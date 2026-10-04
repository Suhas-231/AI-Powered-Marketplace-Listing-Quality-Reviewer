import csv
import io
import json
import logging
import time
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.listing import Listing
from app.models.review import Review, ReviewFinding
from app.models.suggestion import Suggestion
from app.models.user import User
from app.services.validation_service import ValidationService
from app.services.policy_service import PolicyService
from app.services.groq_service import GroqService
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

bp = Blueprint('batch', __name__, url_prefix='/api/batch')

@bp.route('/review', methods=['POST'])
def batch_review():
    """
    Processes a batch of listing IDs sequentially.
    Validates each listing, runs AI review, verifies citations, and isolates errors.
    """
    data = request.get_json() or {}
    listing_ids = data.get('listing_ids', [])
    if not isinstance(listing_ids, list) or not listing_ids:
        return jsonify({'success': False, 'message': 'listing_ids array is required'}), 400

    results = []
    user = User.query.first()

    for l_id in listing_ids:
        try:
            listing = Listing.query.get(l_id)
            if not listing:
                results.append({
                    'listing_id': l_id,
                    'status': 'failed',
                    'error': f'Listing #{l_id} not found.'
                })
                continue

            # Deterministic pre-validation
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
            val_res = ValidationService.validate_listing_payload(listing_dict, exclude_id=listing.id)
            if not val_res['valid']:
                results.append({
                    'listing_id': listing.id,
                    'listing_title': listing.title,
                    'status': 'failed',
                    'error': f"Deterministic validation failed: {'; '.join(val_res['errors'].values())}"
                })
                continue

            # Policy retrieval
            relevant_policies = PolicyService.retrieve_relevant_policies(listing)
            policy_context_text = PolicyService.format_policies_for_prompt(relevant_policies)

            # Groq review
            raw_review = GroqService.analyze_listing(listing_dict, policy_context_text)
            verified_findings = PolicyService.verify_policy_citations(raw_review.get('findings', []))

            # Store Review & Findings
            review = Review(
                listing_id=listing.id,
                status='completed',
                summary=raw_review.get('summary', 'AI review completed.'),
                overall_status=raw_review.get('overall_status', 'needs_review'),
                policy_coverage=raw_review.get('policy_coverage', 'sample_policy'),
                model_name=current_app.config.get('GROQ_MODEL', 'openai/gpt-oss-20b'),
                assumptions=raw_review.get('assumptions', []),
                unverifiable_claims=raw_review.get('unverifiable_claims', []),
                raw_ai_response=json.dumps(raw_review)
            )
            db.session.add(review)
            db.session.flush()

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
                    policy_reference_text=f.get('policy_reference_text'),
                    suggested_revision=f['suggested_revision'],
                    explanation=f['explanation'],
                    requires_human_review=f.get('requires_human_review', True)
                )
                db.session.add(finding_record)
                db.session.flush()

                suggestion_record = Suggestion(
                    finding_id=finding_record.id,
                    original_value=f['original_value'],
                    suggested_value=f['suggested_revision'],
                    action_status='pending'
                )
                db.session.add(suggestion_record)

            listing.status = 'revisions_pending' if len(verified_findings) > 0 else 'reviewed'
            db.session.commit()

            results.append({
                'listing_id': listing.id,
                'listing_title': listing.title,
                'status': 'success',
                'review_id': review.id,
                'findings_count': len(verified_findings),
                'overall_status': review.overall_status
            })

            # Small gentle rate limit delay between API requests
            time.sleep(0.5)

        except Exception as e:
            db.session.rollback()
            sanitized_err = GroqService.sanitize_error_message(str(e))
            current_model = current_app.config.get('GROQ_MODEL', 'openai/gpt-oss-20b')
            logger.error(f"Error processing listing #{l_id} in batch [model='{current_model}']: {sanitized_err}")
            
            # Log failure in audit trail without exposing API keys or sensitive data
            AuditService.log(
                entity_type='review',
                entity_id=l_id,
                action='failed',
                details={
                    'listing_id': l_id,
                    'model': current_model,
                    'error': sanitized_err,
                    'batch': True
                },
                user_id=user.id if user else None
            )

            results.append({
                'listing_id': l_id,
                'status': 'failed',
                'error': sanitized_err
            })

    AuditService.log(
        entity_type='batch',
        entity_id=0,
        action='batch_review_executed',
        details={'requested_count': len(listing_ids), 'results': results},
        user_id=user.id if user else None
    )

    return jsonify({
        'success': True,
        'total_processed': len(listing_ids),
        'successful': sum(1 for r in results if r['status'] == 'success'),
        'failed': sum(1 for r in results if r['status'] == 'failed'),
        'results': results
    }), 200


@bp.route('/import-csv', methods=['POST'])
def import_csv():
    """
    Parses uploaded CSV or CSV text content, validates each row, and imports valid listings into database.
    """
    user = User.query.first()
    csv_text = None

    if 'file' in request.files:
        file = request.files['file']
        csv_text = file.read().decode('utf-8', errors='ignore')
    elif request.is_json:
        csv_text = request.json.get('csv_content')
    else:
        csv_text = request.form.get('csv_content')

    if not csv_text or not csv_text.strip():
        return jsonify({'success': False, 'message': 'No CSV content provided'}), 400

    imported_listings = []
    errors = []

    try:
        reader = csv.DictReader(io.StringIO(csv_text))
        for row_idx, row in enumerate(reader, start=1):
            # Parse attributes if JSON string or empty
            raw_attrs = (row.get('attributes') or '').strip()
            parsed_attrs = {}
            if raw_attrs and raw_attrs.startswith('{'):
                try:
                    parsed_attrs = json.loads(raw_attrs)
                except Exception:
                    parsed_attrs = {}

            # Parse tags
            raw_tags = row.get('tags') or ''
            tags_list = [t.strip() for t in raw_tags.split(',') if t.strip()] if raw_tags else []

            payload = {
                'title': row.get('title', '').strip(),
                'description': row.get('description', '').strip(),
                'category': row.get('category', '').strip(),
                'price': row.get('price', '').strip(),
                'currency': row.get('currency', 'USD').strip() or 'USD',
                'listing_type': row.get('listing_type', 'Product').strip() or 'Product',
                'seller': row.get('seller', '').strip(),
                'attributes': parsed_attrs,
                'tags': tags_list
            }

            val_res = ValidationService.validate_listing_payload(payload, check_duplicates=False)
            if not val_res['valid']:
                errors.append({
                    'row': row_idx,
                    'title': payload.get('title', 'Unknown'),
                    'errors': val_res['errors']
                })
                continue

            clean = val_res['sanitized_data']
            listing = Listing(
                user_id=user.id if user else None,
                title=clean['title'],
                description=clean['description'],
                category=clean['category'],
                price=clean['price'],
                currency=clean['currency'],
                listing_type=clean['listing_type'],
                seller=clean['seller'],
                attributes=clean['attributes'],
                tags=clean['tags'],
                status='draft'
            )
            db.session.add(listing)
            imported_listings.append(listing)

        db.session.commit()

        AuditService.log(
            entity_type='batch',
            entity_id=0,
            action='csv_imported',
            details={'imported_count': len(imported_listings), 'error_count': len(errors)},
            user_id=user.id if user else None
        )

        return jsonify({
            'success': True,
            'imported_count': len(imported_listings),
            'imported_ids': [l.id for l in imported_listings],
            'errors_count': len(errors),
            'errors': errors
        }), 201

    except Exception as e:
        db.session.rollback()
        logger.error(f"CSV import failed: {e}")
        return jsonify({'success': False, 'message': f'CSV parsing error: {str(e)}'}), 400
