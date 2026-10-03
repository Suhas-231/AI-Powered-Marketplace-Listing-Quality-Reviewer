from datetime import datetime
from app.database import db

class ReviewAction(db.Model):
    __tablename__ = 'review_actions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    suggestion_id = db.Column(db.Integer, db.ForeignKey('suggestions.id', ondelete='CASCADE'), nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False) # 'approve', 'edit', 'reject'
    previous_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    comments = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'suggestion_id': self.suggestion_id,
            'user_id': self.user_id,
            'actor_name': self.actor.name if self.actor else 'Reviewer',
            'action': self.action,
            'previous_value': self.previous_value,
            'new_value': self.new_value,
            'comments': self.comments,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
