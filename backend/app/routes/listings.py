from datetime import datetime
from flask import Blueprint, request, jsonify, current_app
from app.database import db
from app.models.listing import Listing
from app.models.user import User
from app.services.validation_service import ValidationService
from app.services.audit_service import AuditService

bp = Blueprint('listings', __name__, url_prefix='/api/listings')

@bp.route('', methods=['GET'])
def get_listings():
    """
    Retrieves listings with search, category filtering, status filtering, sorting, and pagination.
    """
    category = request.args.get('category')
    status = request.args.get('status')
    search = request.args.get('search', '').strip()
    sort_by = request.args.get('sort_by', 'created_at')
    sort_order = request.args.get('sort_order', 'desc')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    query = Listing.query

    if category and category != 'all':
        query = query.filter(Listing.category == category)
    if status and status != 'all':
        query = query.filter(Listing.status == status)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Listing.title.ilike(search_filter)) |
            (Listing.description.ilike(search_filter)) |
            (Listing.seller.ilike(search_filter))
        )

    # Sorting
    sort_col = getattr(Listing, sort_by, Listing.created_at)
    if sort_order.lower() == 'asc':
        query = query.order_by(sort_col.asc())
    else:
        query = query.order_by(sort_col.desc())

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'listings': [l.to_dict() for l in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages,
        'per_page': pagination.per_page
    }), 200


@bp.route('/<int:listing_id>', methods=['GET'])
def get_listing(listing_id):
    """Retrieves a single listing with its reviews and findings."""
    listing = Listing.query.get_or_404(listing_id)
    return jsonify(listing.to_dict(include_reviews=True)), 200


@bp.route('', methods=['POST'])
def create_listing():
    """
    Creates a new listing after running deterministic validation.
    """
    data = request.get_json() or {}
    validation_result = ValidationService.validate_listing_payload(data)

    if not validation_result['valid']:
        return jsonify({
            'success': False,
            'message': 'Listing validation failed',
            'errors': validation_result['errors'],
            'warnings': validation_result['warnings']
        }), 400

    clean = validation_result['sanitized_data']
    user = User.query.first()

    listing = Listing(
        user_id=user.id if user else None,
        title=clean['title'],
        description=clean['description'],
        category=clean['category'],
        price=clean['price'],
        currency=clean.get('currency', 'USD'),
        listing_type=clean.get('listing_type', 'Product'),
        seller=clean['seller'],
        attributes=clean.get('attributes', {}),
        tags=clean.get('tags', []),
        status=data.get('status', 'draft')
    )

    db.session.add(listing)
    db.session.commit()

    AuditService.log(
        entity_type='listing',
        entity_id=listing.id,
        action='created',
        details={'title': listing.title, 'category': listing.category, 'price': listing.price},
        user_id=user.id if user else None
    )

    return jsonify({
        'success': True,
        'message': 'Listing created successfully',
        'listing': listing.to_dict(),
        'warnings': validation_result['warnings']
    }), 201


@bp.route('/<int:listing_id>', methods=['PUT'])
def update_listing(listing_id):
    """Updates an existing listing after validation."""
    listing = Listing.query.get_or_404(listing_id)
    data = request.get_json() or {}

    validation_result = ValidationService.validate_listing_payload(data, exclude_id=listing_id)
    if not validation_result['valid']:
        return jsonify({
            'success': False,
            'message': 'Validation failed on update',
            'errors': validation_result['errors'],
            'warnings': validation_result['warnings']
        }), 400

    clean = validation_result['sanitized_data']
    user = User.query.first()

    listing.title = clean['title']
    listing.description = clean['description']
    listing.category = clean['category']
    listing.price = clean['price']
    listing.currency = clean.get('currency', listing.currency)
    listing.listing_type = clean.get('listing_type', listing.listing_type)
    listing.seller = clean['seller']
    listing.attributes = clean.get('attributes', listing.attributes)
    listing.tags = clean.get('tags', listing.tags)
    listing.updated_at = datetime.utcnow()

    db.session.commit()

    AuditService.log(
        entity_type='listing',
        entity_id=listing.id,
        action='updated',
        details={'title': listing.title, 'updated_fields': list(clean.keys())},
        user_id=user.id if user else None
    )

    return jsonify({
        'success': True,
        'message': 'Listing updated successfully',
        'listing': listing.to_dict(),
        'warnings': validation_result['warnings']
    }), 200


@bp.route('/<int:listing_id>', methods=['DELETE'])
def delete_listing(listing_id):
    """Deletes a listing and records audit entry."""
    listing = Listing.query.get_or_404(listing_id)
    listing_id_saved = listing.id
    listing_title = listing.title
    user = User.query.first()

    db.session.delete(listing)
    db.session.commit()

    AuditService.log(
        entity_type='listing',
        entity_id=listing_id_saved,
        action='deleted',
        details={'title': listing_title},
        user_id=user.id if user else None
    )

    return jsonify({'success': True, 'message': f'Listing #{listing_id_saved} deleted'}), 200


@bp.route('/<int:listing_id>/validate', methods=['POST'])
def validate_listing(listing_id):
    """
    Runs standalone deterministic validation for a listing without submitting for AI review.
    """
    listing = Listing.query.get_or_404(listing_id)
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
    result = ValidationService.validate_listing_payload(listing_dict, exclude_id=listing.id)
    return jsonify(result), 200
