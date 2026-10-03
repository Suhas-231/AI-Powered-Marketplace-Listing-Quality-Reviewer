from datetime import datetime
from app.database import db

class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=True)
    role = db.Column(db.String(50), nullable=False, default='reviewer')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    listings = db.relationship('Listing', backref='author', lazy=True)
    actions = db.relationship('ReviewAction', backref='actor', lazy=True)
    audit_logs = db.relationship('AuditLog', backref='actor', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'role': self.role,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
