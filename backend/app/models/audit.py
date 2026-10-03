from datetime import datetime
from app.database import db

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    entity_type = db.Column(db.String(50), nullable=False, index=True) # 'listing', 'review', 'suggestion', 'policy'
    entity_id = db.Column(db.Integer, nullable=False, index=True)
    action = db.Column(db.String(100), nullable=False) # 'created', 'updated', 'approved', 'rejected', 'deleted', 'reviewed'
    details = db.Column(db.JSON, nullable=True, default=dict)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'user_name': self.actor.name if self.actor else 'System',
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'action': self.action,
            'details': self.details or {},
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
