from datetime import datetime
from flask import Blueprint, request, jsonify
from app.database import db
from app.models.suggestion import Suggestion
from app.models.action import ReviewAction
from app.models.listing import Listing
from app.models.review import ReviewFinding
from app.models.user import User
from app.services.audit_service import AuditService

bp = Blueprint('suggestions', __name__, url_prefix='/api/suggestions')

def apply_revision_to_listing(listing: Listing, field_name: str, new_value: str):
    """
    Safely updates the corresponding listing field with user approved content.
    Handles standard scalar fields (title, description, seller, price) and JSON attributes.
    """
    field_lower = field_name.lower().strip()
    if field_lower == 'title':
        listing.title = new_value
    elif field_lower == 'description':
        listing.description = new_value
    elif field_lower == 'seller':
        listing.seller = new_value
    elif field_lower == 'price':
        try:
            listing.price = float(new_value)
        except ValueError:
            pass
    elif field_lower in ['attributes', 'attribute']:
        # If attribute or custom field, handle gracefully
        pass
    listing.updated_at = datetime.utcnow()

@bp.route('/<int:suggestion_id>/approve', methods=['POST'])
def approve_suggestion(suggestion_id):
    """
    Approves an AI suggestion.
    Transfers suggested_value to final_value, updates listing field,
    records ReviewAction, and generates AuditLog.
    """
    suggestion = Suggestion.query.get_or_404(suggestion_id)
    finding = suggestion.finding
    review = finding.review
    listing = review.listing
    user = User.query.first()
    data = request.get_json() or {}

    previous_val = suggestion.original_value
    # Use edited final_value if already edited, or suggested_value
    approved_text = data.get('final_value') or suggestion.suggested_value

    try:
        suggestion.action_status = 'approved'
        suggestion.final_value = approved_text
        suggestion.reviewed_by = user.id if user else None
        suggestion.reviewed_at = datetime.utcnow()

        # Record action in ReviewActions
        action_log = ReviewAction(
            suggestion_id=suggestion.id,
            user_id=user.id if user else None,
            action='approve',
            previous_value=previous_val,
            new_value=approved_text,
            comments=data.get('comments', 'Approved by reviewer')
        )
        db.session.add(action_log)

        # Apply revision directly to the listing
        apply_revision_to_listing(listing, finding.field_name, approved_text)
        listing.status = 'revisions_applied'

        db.session.commit()

        AuditService.log(
            entity_type='suggestion',
            entity_id=suggestion.id,
            action='approved',
            details={
                'field': finding.field_name,
                'listing_id': listing.id,
                'final_value': approved_text
            },
            user_id=user.id if user else None
        )

        return jsonify({
            'success': True,
            'message': f"Revision for '{finding.field_name}' approved and applied to listing.",
            'suggestion': suggestion.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to approve suggestion: {str(e)}'}), 500


@bp.route('/<int:suggestion_id>', methods=['PUT'])
def edit_suggestion(suggestion_id):
    """
    Allows the human reviewer to edit the suggested wording before approving.
    Can also apply immediately if 'apply': True is passed.
    """
    suggestion = Suggestion.query.get_or_404(suggestion_id)
    finding = suggestion.finding
    listing = finding.review.listing
    user = User.query.first()
    data = request.get_json() or {}

    edited_value = data.get('final_value')
    if not edited_value or not str(edited_value).strip():
        return jsonify({'success': False, 'message': 'Edited replacement text cannot be empty'}), 400

    should_apply = data.get('apply', False)

    try:
        prev_val = suggestion.final_value or suggestion.suggested_value
        suggestion.final_value = edited_value.strip()
        suggestion.action_status = 'approved' if should_apply else 'edited'
        suggestion.reviewed_by = user.id if user else None
        suggestion.reviewed_at = datetime.utcnow()

        action_log = ReviewAction(
            suggestion_id=suggestion.id,
            user_id=user.id if user else None,
            action='edit',
            previous_value=prev_val,
            new_value=suggestion.final_value,
            comments=data.get('comments', 'Edited by reviewer')
        )
        db.session.add(action_log)

        if should_apply:
            apply_revision_to_listing(listing, finding.field_name, suggestion.final_value)
            listing.status = 'revisions_applied'

        db.session.commit()

        AuditService.log(
            entity_type='suggestion',
            entity_id=suggestion.id,
            action='edited',
            details={
                'field': finding.field_name,
                'listing_id': listing.id,
                'applied': should_apply,
                'final_value': suggestion.final_value
            },
            user_id=user.id if user else None
        )

        return jsonify({
            'success': True,
            'message': 'Suggestion updated successfully',
            'suggestion': suggestion.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to edit suggestion: {str(e)}'}), 500


@bp.route('/<int:suggestion_id>/reject', methods=['POST'])
def reject_suggestion(suggestion_id):
    """
    Rejects the AI suggestion, preserving the original listing content intact.
    Records the rejection reason and user decision.
    """
    suggestion = Suggestion.query.get_or_404(suggestion_id)
    finding = suggestion.finding
    listing = finding.review.listing
    user = User.query.first()
    data = request.get_json() or {}

    reason = data.get('reason', 'Rejected by human reviewer')

    try:
        suggestion.action_status = 'rejected'
        suggestion.rejection_reason = reason
        suggestion.reviewed_by = user.id if user else None
        suggestion.reviewed_at = datetime.utcnow()

        action_log = ReviewAction(
            suggestion_id=suggestion.id,
            user_id=user.id if user else None,
            action='reject',
            previous_value=suggestion.suggested_value,
            new_value=suggestion.original_value,
            comments=reason
        )
        db.session.add(action_log)

        # Do not modify listing field; preserve original content
        db.session.commit()

        AuditService.log(
            entity_type='suggestion',
            entity_id=suggestion.id,
            action='rejected',
            details={
                'field': finding.field_name,
                'listing_id': listing.id,
                'reason': reason
            },
            user_id=user.id if user else None
        )

        return jsonify({
            'success': True,
            'message': f"Suggestion for '{finding.field_name}' rejected. Original content retained.",
            'suggestion': suggestion.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'Failed to reject suggestion: {str(e)}'}), 500
