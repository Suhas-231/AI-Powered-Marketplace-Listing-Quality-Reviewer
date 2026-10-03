from datetime import datetime
from app.database import db

class Policy(db.Model):
    __tablename__ = 'policies'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    policy_code = db.Column(db.String(50), unique=True, nullable=False, index=True) # e.g. POL-TITLE-001
    section_number = db.Column(db.String(50), nullable=False) # e.g. Section 1.1
    title = db.Column(db.String(255), nullable=False)
    category = db.Column(db.String(100), nullable=False, index=True)
    description = db.Column(db.Text, nullable=False)
    severity_guidance = db.Column(db.String(50), nullable=False, default='Medium') # High, Medium, Low
    is_active = db.Column(db.Boolean, default=True, nullable=False, index=True)
    is_demo_policy = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    findings = db.relationship('ReviewFinding', backref='policy', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'policy_code': self.policy_code,
            'section_number': self.section_number,
            'title': self.title,
            'category': self.category,
            'description': self.description,
            'severity_guidance': self.severity_guidance,
            'is_active': self.is_active,
            'is_demo_policy': self.is_demo_policy,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
