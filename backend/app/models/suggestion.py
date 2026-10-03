from datetime import datetime
from app.database import db

class Suggestion(db.Model):
    __tablename__ = 'suggestions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    finding_id = db.Column(db.Integer, db.ForeignKey('review_findings.id', ondelete='CASCADE'), nullable=False, index=True)
    original_value = db.Column(db.Text, nullable=False)
    suggested_value = db.Column(db.Text, nullable=False)
    final_value = db.Column(db.Text, nullable=True)
    action_status = db.Column(db.String(50), nullable=False, default='pending', index=True) # 'pending', 'approved', 'rejected', 'edited'
    rejection_reason = db.Column(db.Text, nullable=True)
    reviewed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    reviewed_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    actions = db.relationship('ReviewAction', backref='suggestion', lazy=True, cascade='all, delete-orphan', order_by='desc(ReviewAction.created_at)')
    reviewer = db.relationship('User', foreign_keys=[reviewed_by], lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'finding_id': self.finding_id,
            'original_value': self.original_value,
            'suggested_value': self.suggested_value,
            'final_value': self.final_value,
            'action_status': self.action_status,
            'rejection_reason': self.rejection_reason,
            'reviewed_by': self.reviewed_by,
            'reviewer_name': self.reviewer.name if self.reviewer else None,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'action_history': [a.to_dict() for a in self.actions]
        }
