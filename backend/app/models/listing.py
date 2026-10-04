from datetime import datetime
from app.database import db

class Listing(db.Model):
    __tablename__ = 'listings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    title = db.Column(db.String(255), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    price = db.Column(db.Float, nullable=False)
    currency = db.Column(db.String(10), nullable=False, default='INR')
    listing_type = db.Column(db.String(50), nullable=False, default='Product')
    attributes = db.Column(db.JSON, nullable=True, default=dict)
    seller = db.Column(db.String(120), nullable=False)
    tags = db.Column(db.JSON, nullable=True, default=list)
    status = db.Column(db.String(50), nullable=False, default='draft', index=True) 
    # status: 'draft', 'pending_review', 'in_review', 'revisions_pending', 'revisions_applied', 'approved', 'rejected'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    reviews = db.relationship('Review', backref='listing', lazy=True, cascade='all, delete-orphan', order_by='desc(Review.created_at), desc(Review.id)')

    @property
    def latest_completed_review(self):
        """Returns the most recent successfully completed review."""
        if not self.reviews:
            return None
        for r in self.reviews:
            if r.status == 'completed':
                return r
        return None

    def to_dict(self, include_reviews=False):
        latest = self.latest_completed_review
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'price': float(self.price) if self.price is not None else 0.0,
            'currency': self.currency,
            'listing_type': self.listing_type,
            'attributes': self.attributes or {},
            'seller': self.seller,
            'tags': self.tags or [],
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'review_count': len(self.reviews) if self.reviews else 0,
            'latest_review_status': latest.overall_status if latest else None,
            'latest_review_id': latest.id if latest else None
        }
        if include_reviews and self.reviews:
            data['reviews'] = [r.to_dict(include_findings=True) for r in self.reviews]
        return data
