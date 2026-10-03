import json
import logging
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.listing import Listing
from app.models.review import Review, ReviewFinding
from app.models.suggestion import Suggestion
from app.models.user import User
from app.services.validation_service import ValidationService
from app.services.policy_service import PolicyService
from app.services.gemini_service import GeminiService
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

bp = Blueprint('reviews', __name__, url_prefix='/api')

@bp.route('/listings/<int:listing_id>/review', methods=['POST'])
def trigger_ai_review(listing_id):
    """
    Submits a listing for AI policy review.
    Runs deterministic validation first, retrieves policies, calls Gemini, verifies citations,
    and creates review + findings + suggestion records.
    """
    listing = Listing.query.get_or_404(listing_id)
    user = User.query.first()

    # Step 1: Deterministic validation check
    listing_dict = {
        'title': listing.title,
        'description': listing.description,
        'category': listing.category,
        'price': listing.price,
        'currency': listing.currency,
        'listing_type': listing.listing_type,
        'seller': listing.seller,
        'attributes': listing.attributes,
        'tags': listing.tags
    }
    validation_res = ValidationService.validate_listing_payload(listing_dict, exclude_id=listing.id)
    if not validation_res['valid']:
        return jsonify({
            'success': False,
            'message': 'Listing failed deterministic validation and cannot be submitted for AI review.',
            'validation_errors': validation_res['errors']
        }), 400

    # Step 2: Retrieve relevant policies
    relevant_policies = PolicyService.retrieve_relevant_policies(listing)
    policy_context_text = PolicyService.format_policies_for_prompt(relevant_policies)

    # Step 3 & 4: Call Gemini via official google-genai SDK
    try:
        raw_review = GeminiService.analyze_listing(listing_dict, policy_context_text)
    except Exception as e:
        logger.error(f"AI review execution failed for listing #{listing_id}: {e}")
        # Record failed review attempt
        failed_review = Review(
            listing_id=listing.id,
            status='failed',
            summary=f"AI review failed: {str(e)}",
            overall_status='flagged',
            model_name=current_app.config.get('GEMINI_MODEL', 'gemini-2.5-flash')
        )
        db.session.add(failed_review)
        db.session.commit()
        return jsonify({
            'success': False,
            'message': f"AI review failed: {str(e)}",
            'review_id': failed_review.id
        }), 502

    # Step 5 & 6: Verify citations against actual database policies
    findings = raw_review.get('findings', [])
    verified_findings = PolicyService.verify_policy_citations(findings)

    # Step 7: Store review, findings, and suggestions in database
    review = Review(
        listing_id=listing.id,
        status='completed',
        summary=raw_review.get('summary', 'AI review completed successfully.'),
        overall_status=raw_review.get('overall_status', 'needs_review'),
        policy_coverage=raw_review.get('policy_coverage', 'sample_policy'),
        model_name=current_app.config.get('GEMINI_MODEL', 'gemini-2.5-flash'),
        assumptions=raw_review.get('assumptions', []),
        unverifiable_claims=raw_review.get('unverifiable_claims', []),
        raw_ai_response=json.dumps(raw_review)
    )
    db.session.add(review)
    db.session.flush() # generates review.id

    created_findings = []
    for f in verified_findings:
        finding_record = ReviewFinding(
            review_id=review.id,
            field_name=f['field'],
            original_value=f['original_value'],
            issue_type=f['issue_type'],
            severity=f['severity'],
            issue_description=f['issue'],
            policy_id=f.get('policy_id'),
            policy_reference_code=f.get('policy_reference_code'),
            policy_reference_text=f.get('policy_reference_text') or f.get('policy_reference'),
            suggested_revision=f['suggested_revision'],
            explanation=f['explanation'],
            requires_human_review=f.get('requires_human_review', True)
        )
        db.session.add(finding_record)
        db.session.flush()

        # Create corresponding pending Suggestion for human approval workflow
        suggestion_record = Suggestion(
            finding_id=finding_record.id,
            original_value=f['original_value'],
            suggested_value=f['suggested_revision'],
            action_status='pending'
        )
        db.session.add(suggestion_record)
        created_findings.append(finding_record)

    # Update listing status
    listing.status = 'revisions_pending' if len(created_findings) > 0 else 'reviewed'
    db.session.commit()

    # Record audit entry
    AuditService.log(
        entity_type='review',
        entity_id=review.id,
        action='completed',
        details={
            'listing_id': listing.id,
            'findings_count': len(created_findings),
            'overall_status': review.overall_status,
            'model': review.model_name
        },
        user_id=user.id if user else None
    )

    return jsonify({
        'success': True,
        'message': 'AI review generated successfully',
        'review': review.to_dict(include_findings=True)
    }), 201


@bp.route('/reviews/<int:review_id>', methods=['GET'])
def get_review(review_id):
    """Retrieves full details of a specific AI review."""
    review = Review.query.get_or_404(review_id)
    return jsonify(review.to_dict(include_findings=True)), 200


@bp.route('/listings/<int:listing_id>/reviews', methods=['GET'])
def get_listing_reviews(listing_id):
    """Retrieves review history for a specific listing."""
    listing = Listing.query.get_or_404(listing_id)
    reviews = Review.query.filter_by(listing_id=listing.id).order_by(Review.created_at.desc()).all()
    return jsonify([r.to_dict(include_findings=True) for r in reviews]), 200


@bp.route('/reviews', methods=['GET'])
def list_reviews():
    """Retrieves all AI reviews, ordered by creation date descending."""
    listing_id = request.args.get('listing_id', type=int)
    query = Review.query
    if listing_id:
        query = query.filter_by(listing_id=listing_id)
    reviews = query.order_by(Review.created_at.desc()).all()
    return jsonify({
        'success': True,
        'reviews': [r.to_dict(include_findings=False) for r in reviews],
        'total': len(reviews)
    }), 200


@bp.route('/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """
    Permanently deletes an AI review and its associated findings and suggestions.
    Updates the listing status back to 'draft' if no other reviews remain.
    """
    review = Review.query.get_or_404(review_id)
    listing = Listing.query.get(review.listing_id)
    user = User.query.first()

    deleted_id = review.id
    listing_id = review.listing_id

    try:
        db.session.delete(review)

        # Revert listing status if no other reviews exist for this listing
        if listing:
            other_reviews = Review.query.filter(
                Review.listing_id == listing_id,
                Review.id != deleted_id
            ).all()
            if not other_reviews and listing.status in ['revisions_pending', 'reviewed', 'in_review']:
                listing.status = 'draft'

        db.session.commit()

        AuditService.log(
            entity_type='review',
            entity_id=deleted_id,
            action='deleted',
            details={'listing_id': listing_id},
            user_id=user.id if user else None
        )

        return jsonify({
            'success': True,
            'message': f'Review #{deleted_id} has been permanently deleted.'
        }), 200
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to delete review #{review_id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Failed to delete review: {str(e)}'
        }), 500
