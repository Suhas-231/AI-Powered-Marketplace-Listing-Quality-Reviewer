
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


# ---------------------------------------------------------
# BATCH AI REVIEW
# ---------------------------------------------------------

@bp.route('/review', methods=['POST'])
def batch_review():
    """
    Processes multiple listing IDs sequentially.
    Validates each listing, runs AI review, verifies citations,
    and stores findings and suggestions.
    """

    data = request.get_json(silent=True) or {}
    listing_ids = data.get('listing_ids', [])

    if not isinstance(listing_ids, list) or not listing_ids:
        return jsonify({
            'success': False,
            'message': 'listing_ids array is required'
        }), 400

    results = []
    user = User.query.first()

    for listing_id in listing_ids:
        try:
            listing = Listing.query.get(listing_id)

            if not listing:
                results.append({
                    'listing_id': listing_id,
                    'status': 'failed',
                    'error': f'Listing #{listing_id} not found.'
                })
                continue

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

            # Deterministic validation
            val_res = ValidationService.validate_listing_payload(
                listing_dict,
                exclude_id=listing.id
            )

            if not val_res['valid']:
                results.append({
                    'listing_id': listing.id,
                    'listing_title': listing.title,
                    'status': 'failed',
                    'error': (
                        'Deterministic validation failed: '
                        + '; '.join(val_res['errors'].values())
                    )
                })
                continue

            # Retrieve relevant policies
            relevant_policies = (
                PolicyService.retrieve_relevant_policies(listing)
            )

            policy_context_text = (
                PolicyService.format_policies_for_prompt(
                    relevant_policies
                )
            )

            # AI review
            raw_review = GroqService.analyze_listing(
                listing_dict,
                policy_context_text
            )

            verified_findings = (
                PolicyService.verify_policy_citations(
                    raw_review.get('findings', [])
                )
            )

            # Store review
            review = Review(
                listing_id=listing.id,
                status='completed',
                summary=raw_review.get(
                    'summary',
                    'AI review completed.'
                ),
                overall_status=raw_review.get(
                    'overall_status',
                    'needs_review'
                ),
                policy_coverage=raw_review.get(
                    'policy_coverage',
                    'sample_policy'
                ),
                model_name=current_app.config.get(
                    'GROQ_MODEL',
                    'openai/gpt-oss-20b'
                ),
                assumptions=raw_review.get('assumptions', []),
                unverifiable_claims=raw_review.get(
                    'unverifiable_claims',
                    []
                ),
                raw_ai_response=json.dumps(raw_review)
            )

            db.session.add(review)
            db.session.flush()

            # Store findings and suggestions
            for finding in verified_findings:

                finding_record = ReviewFinding(
                    review_id=review.id,
                    field_name=finding['field'],
                    original_value=finding['original_value'],
                    issue_type=finding['issue_type'],
                    severity=finding['severity'],
                    issue_description=finding['issue'],
                    policy_id=finding.get('policy_id'),
                    policy_reference_code=finding.get(
                        'policy_reference_code'
                    ),
                    policy_reference_text=finding.get(
                        'policy_reference_text'
                    ),
                    suggested_revision=finding['suggested_revision'],
                    explanation=finding['explanation'],
                    requires_human_review=finding.get(
                        'requires_human_review',
                        True
                    )
                )

                db.session.add(finding_record)
                db.session.flush()

                suggestion_record = Suggestion(
                    finding_id=finding_record.id,
                    original_value=finding['original_value'],
                    suggested_value=finding['suggested_revision'],
                    action_status='pending'
                )

                db.session.add(suggestion_record)

            listing.status = (
                'revisions_pending'
                if verified_findings
                else 'reviewed'
            )

            db.session.commit()

            results.append({
                'listing_id': listing.id,
                'listing_title': listing.title,
                'status': 'success',
                'review_id': review.id,
                'findings_count': len(verified_findings),
                'overall_status': review.overall_status
            })

            # Small delay between AI requests
            time.sleep(0.5)

        except Exception as e:
            db.session.rollback()

            sanitized_err = GroqService.sanitize_error_message(
                str(e)
            )

            current_model = current_app.config.get(
                'GROQ_MODEL',
                'openai/gpt-oss-20b'
            )

            logger.exception(
                "Error processing listing #%s in batch",
                listing_id
            )

            AuditService.log(
                entity_type='review',
                entity_id=listing_id,
                action='failed',
                details={
                    'listing_id': listing_id,
                    'model': current_model,
                    'error': sanitized_err,
                    'batch': True
                },
                user_id=user.id if user else None
            )

            results.append({
                'listing_id': listing_id,
                'status': 'failed',
                'error': sanitized_err
            })

    AuditService.log(
        entity_type='batch',
        entity_id=0,
        action='batch_review_executed',
        details={
            'requested_count': len(listing_ids),
            'results': results
        },
        user_id=user.id if user else None
    )

    return jsonify({
        'success': True,
        'total_processed': len(listing_ids),
        'successful': sum(
            1 for result in results
            if result['status'] == 'success'
        ),
        'failed': sum(
            1 for result in results
            if result['status'] == 'failed'
        ),
        'results': results
    }), 200


# ---------------------------------------------------------
# CSV HEADER NORMALIZATION
# ---------------------------------------------------------

def normalize_csv_header(header):
    """
    Normalizes CSV column names.

    Examples:
        Product Title -> title
        SELLER NAME   -> seller
        listing type  -> listing_type
    """

    if header is None:
        return ''

    normalized = str(header)

    # Remove UTF-8 BOM
    normalized = normalized.replace('\ufeff', '')

    # Normalize case and whitespace
    normalized = normalized.strip().lower()

    # Replace spaces and hyphens with underscores
    normalized = normalized.replace(' ', '_')
    normalized = normalized.replace('-', '_')

    # Handle common alternative column names
    aliases = {
        'product_title': 'title',
        'listing_title': 'title',
        'product_name': 'title',
        'name': 'title',

        'product_description': 'description',
        'listing_description': 'description',

        'product_category': 'category',

        'product_price': 'price',

        'seller_name': 'seller',
        'vendor': 'seller',
        'vendor_name': 'seller',

        'type': 'listing_type',
        'product_type': 'listing_type'
    }

    return aliases.get(normalized, normalized)


# ---------------------------------------------------------
# CSV IMPORT
# ---------------------------------------------------------

@bp.route('/import-csv', methods=['POST'])
def import_csv():
    """
    Imports listings from CSV file or CSV text.

    Supports:
    - UTF-8 BOM
    - Header case differences
    - Extra spaces in headers
    - Alternative column names
    - Comma, semicolon and tab delimiters
    - Optional attributes and tags
    - Row-level validation errors
    """

    user = User.query.first()
    csv_text = None

    # Receive uploaded file
    if 'file' in request.files:
        uploaded_file = request.files['file']

        if not uploaded_file.filename:
            return jsonify({
                'success': False,
                'message': 'No file selected.'
            }), 400

        csv_bytes = uploaded_file.read()

        try:
            csv_text = csv_bytes.decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                csv_text = csv_bytes.decode('latin-1')
            except Exception:
                return jsonify({
                    'success': False,
                    'message': 'Unable to decode the uploaded CSV file.'
                }), 400

    # Receive JSON content
    elif request.is_json:
        data = request.get_json(silent=True) or {}
        csv_text = data.get('csv_content')

    # Receive form content
    else:
        csv_text = request.form.get('csv_content')

    if not isinstance(csv_text, str) or not csv_text.strip():
        return jsonify({
            'success': False,
            'message': 'No CSV content provided.'
        }), 400

    # Remove BOM and leading blank characters
    csv_text = csv_text.lstrip('\ufeff').strip()

    imported_listings = []
    errors = []

    try:
        # Detect delimiter
        sample = csv_text[:8192]

        try:
            dialect = csv.Sniffer().sniff(
                sample,
                delimiters=',;\t|'
            )
            delimiter = dialect.delimiter
        except csv.Error:
            delimiter = ','

        logger.info(
            "CSV import started. Detected delimiter: %r",
            delimiter
        )

        # Parse CSV
        reader = csv.DictReader(
            io.StringIO(csv_text, newline=''),
            delimiter=delimiter,
            skipinitialspace=True
        )

        if not reader.fieldnames:
            return jsonify({
                'success': False,
                'message': 'CSV header row is missing.'
            }), 400

        # Normalize column headers
        original_headers = reader.fieldnames

        normalized_headers = [
            normalize_csv_header(header)
            for header in original_headers
        ]

        # Reject duplicate normalized headers
        if len(normalized_headers) != len(set(normalized_headers)):
            return jsonify({
                'success': False,
                'message': (
                    'CSV contains duplicate columns after header '
                    'normalization. Please check the header row.'
                ),
                'headers': normalized_headers
            }), 400

        reader.fieldnames = normalized_headers

        logger.info(
            "Normalized CSV headers: %s",
            normalized_headers
        )

        # Required columns
        required_headers = [
            'title',
            'description',
            'category',
            'price',
            'seller'
        ]

        missing_headers = [
            header for header in required_headers
            if header not in normalized_headers
        ]

        if missing_headers:
            return jsonify({
                'success': False,
                'message': 'Required CSV columns are missing.',
                'missing_headers': missing_headers,
                'received_headers': normalized_headers
            }), 400

        # Process each CSV row
        for row_idx, row in enumerate(reader, start=1):

            # Skip completely empty rows
            if not row or all(
                value is None or not str(value).strip()
                for value in row.values()
            ):
                continue

            # Handle rows containing more values than headers
            if None in row:
                errors.append({
                    'row': row_idx,
                    'title': 'Unknown',
                    'errors': {
                        'csv': (
                            'This row contains extra values. '
                            'Check commas and quotation marks.'
                        )
                    }
                })
                continue

            # Normalize values safely
            normalized_row = {}

            for key, value in row.items():
                normalized_key = normalize_csv_header(key)

                normalized_row[normalized_key] = (
                    str(value).strip()
                    if value is not None
                    else ''
                )

            # Parse attributes
            raw_attrs = normalized_row.get('attributes', '')
            parsed_attrs = {}

            if raw_attrs:
                try:
                    parsed_attrs = json.loads(raw_attrs)

                    if not isinstance(parsed_attrs, dict):
                        raise ValueError(
                            'Attributes must be a JSON object.'
                        )

                except (json.JSONDecodeError, ValueError):
                    errors.append({
                        'row': row_idx,
                        'title': normalized_row.get(
                            'title',
                            'Unknown'
                        ),
                        'errors': {
                            'attributes': (
                                'Invalid JSON in attributes column. '
                                'Use a valid JSON object.'
                            )
                        }
                    })
                    continue

            # Parse tags
            raw_tags = normalized_row.get('tags', '')

            tags_list = [
                tag.strip()
                for tag in raw_tags.split(',')
                if tag.strip()
            ]

            # Prepare listing payload
            payload = {
                'title': normalized_row.get('title', ''),
                'description': normalized_row.get(
                    'description',
                    ''
                ),
                'category': normalized_row.get('category', ''),
                'price': normalized_row.get('price', ''),
                'currency': (
                    normalized_row.get('currency') or 'USD'
                ),
                'listing_type': (
                    normalized_row.get('listing_type') or 'Product'
                ),
                'seller': normalized_row.get('seller', ''),
                'attributes': parsed_attrs,
                'tags': tags_list
            }

            # Validate listing
            val_res = ValidationService.validate_listing_payload(
                payload,
                check_duplicates=False
            )

            if not val_res['valid']:
                errors.append({
                    'row': row_idx,
                    'title': payload.get('title') or 'Unknown',
                    'errors': val_res['errors']
                })
                continue

            # Insert valid listing
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

        # Save all valid listings
        db.session.commit()

        # Audit log
        AuditService.log(
            entity_type='batch',
            entity_id=0,
            action='csv_imported',
            details={
                'imported_count': len(imported_listings),
                'error_count': len(errors)
            },
            user_id=user.id if user else None
        )

        logger.info(
            "CSV import completed. Imported: %s, Errors: %s",
            len(imported_listings),
            len(errors)
        )

        return jsonify({
            'success': True,
            'imported_count': len(imported_listings),
            'imported_ids': [
                listing.id for listing in imported_listings
            ],
            'errors_count': len(errors),
            'errors': errors
        }), 201

    except Exception as e:
        db.session.rollback()

        logger.exception('CSV import failed')

        return jsonify({
            'success': False,
            'message': 'CSV parsing or import failed.',
            'error': str(e)
        }), 400
