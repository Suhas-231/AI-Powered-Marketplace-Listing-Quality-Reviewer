from flask import Blueprint, jsonify
from sqlalchemy import func
from app.database import db
from app.models.listing import Listing
from app.models.review import Review, ReviewFinding
from app.models.suggestion import Suggestion
from app.models.action import ReviewAction

bp = Blueprint('dashboard', __name__, url_prefix='/api/dashboard')

@bp.route('/stats', methods=['GET'])
def get_dashboard_stats():
    """
    Returns actual database statistics and distributions for dashboard summary cards.
    """
    total_listings = Listing.query.count()
    pending_reviews = Listing.query.filter(Listing.status.in_(['pending_review', 'revisions_pending'])).count()
    
    approved_revisions = Suggestion.query.filter_by(action_status='approved').count()
    rejected_revisions = Suggestion.query.filter_by(action_status='rejected').count()
    
    # Listings requiring attention: flagged or having high severity findings
    requiring_attention = Listing.query.join(Review).filter(
        (Review.overall_status == 'flagged') |
        (Listing.status == 'revisions_pending')
    ).distinct().count()

    # Severity distribution across all findings
    severity_query = db.session.query(
        ReviewFinding.severity,
        func.count(ReviewFinding.id)
    ).group_by(ReviewFinding.severity).all()
    
    severity_dist = {'High': 0, 'Medium': 0, 'Low': 0}
    for sev, count in severity_query:
        if sev and sev.capitalize() in severity_dist:
            severity_dist[sev.capitalize()] = count

    # Review status distribution
    status_query = db.session.query(
        Listing.status,
        func.count(Listing.id)
    ).group_by(Listing.status).all()
    status_dist = {status: count for status, count in status_query}

    # Recent items
    recent_listings = Listing.query.order_by(Listing.created_at.desc()).limit(5).all()
    recent_reviews = Review.query.order_by(Review.created_at.desc()).limit(5).all()
    recent_actions = ReviewAction.query.order_by(ReviewAction.created_at.desc()).limit(6).all()

    return jsonify({
        'summary': {
            'total_listings': total_listings,
            'pending_reviews': pending_reviews,
            'approved_revisions': approved_revisions,
            'rejected_revisions': rejected_revisions,
            'listings_requiring_attention': requiring_attention
        },
        'severity_distribution': severity_dist,
        'status_distribution': status_dist,
        'recent_listings': [l.to_dict() for l in recent_listings],
        'recent_reviews': [r.to_dict(include_findings=False) for r in recent_reviews],
        'recent_actions': [a.to_dict() for a in recent_actions]
    }), 200
