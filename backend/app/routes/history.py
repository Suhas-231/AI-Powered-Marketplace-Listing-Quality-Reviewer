from flask import Blueprint, request, jsonify
from app.models.audit import AuditLog
from app.models.action import ReviewAction
from app.models.listing import Listing
from app.models.review import Review

bp = Blueprint('history', __name__, url_prefix='/api')

@bp.route('/history', methods=['GET'])
def get_global_history():
    """
    Returns global audit logs and review actions with pagination and filtering.
    """
    entity_type = request.args.get('entity_type')
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    query = AuditLog.query
    if entity_type and entity_type != 'all':
        query = query.filter_by(entity_type=entity_type)

    pagination = query.order_by(AuditLog.created_at.desc()).paginate(page=page, per_page=per_page, error_out=False)

    return jsonify({
        'logs': [l.to_dict() for l in pagination.items],
        'total': pagination.total,
        'page': pagination.page,
        'pages': pagination.pages
    }), 200


@bp.route('/listings/<int:listing_id>/history', methods=['GET'])
def get_listing_history(listing_id):
    """
    Returns comprehensive history for a single listing:
    Audit logs, AI reviews generated, and human revision decisions.
    """
    listing = Listing.query.get_or_404(listing_id)

    # 1. Direct listing audit logs
    logs = AuditLog.query.filter_by(entity_type='listing', entity_id=listing.id).order_by(AuditLog.created_at.desc()).all()

    # 2. Reviews with findings
    reviews = Review.query.filter_by(listing_id=listing.id).order_by(Review.created_at.desc()).all()

    # 3. Actions taken on suggestions related to this listing
    suggestion_ids = []
    for r in reviews:
        for f in r.findings:
            for s in f.suggestions:
                suggestion_ids.append(s.id)

    actions = []
    if suggestion_ids:
        actions = ReviewAction.query.filter(ReviewAction.suggestion_id.in_(suggestion_ids)).order_by(ReviewAction.created_at.desc()).all()

    return jsonify({
        'listing': listing.to_dict(),
        'audit_logs': [l.to_dict() for l in logs],
        'reviews': [r.to_dict(include_findings=True) for r in reviews],
        'actions': [a.to_dict() for a in actions]
    }), 200
