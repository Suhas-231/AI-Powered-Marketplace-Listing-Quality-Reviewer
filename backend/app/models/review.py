from datetime import datetime
from app.database import db

class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    listing_id = db.Column(db.Integer, db.ForeignKey('listings.id', ondelete='CASCADE'), nullable=False, index=True)
    status = db.Column(db.String(50), nullable=False, default='completed') # 'pending', 'completed', 'failed'
    summary = db.Column(db.Text, nullable=True)
    overall_status = db.Column(db.String(50), nullable=False, default='needs_review') # 'needs_review', 'flagged', 'compliant'
    policy_coverage = db.Column(db.String(100), default='sample_policy') # 'sample_policy', 'official_policy', 'none'
    model_name = db.Column(db.String(100), nullable=False, default='openai/gpt-oss-20b')
    assumptions = db.Column(db.JSON, nullable=True, default=list)
    unverifiable_claims = db.Column(db.JSON, nullable=True, default=list)
    raw_ai_response = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    findings = db.relationship('ReviewFinding', backref='review', lazy=True, cascade='all, delete-orphan')

    def to_dict(self, include_findings=True):
        data = {
            'id': self.id,
            'listing_id': self.listing_id,
            'listing_title': self.listing.title if self.listing else None,
            'listing_status': self.listing.status if self.listing else None,
            'status': self.status,
            'summary': self.summary,
            'overall_status': self.overall_status,
            'policy_coverage': self.policy_coverage,
            'model_name': self.model_name,
            'assumptions': self.assumptions or [],
            'unverifiable_claims': self.unverifiable_claims or [],
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'total_findings': len(self.findings) if self.findings else 0,
            'severity_counts': {
                'high': sum(1 for f in self.findings if f.severity.lower() == 'high') if self.findings else 0,
                'medium': sum(1 for f in self.findings if f.severity.lower() == 'medium') if self.findings else 0,
                'low': sum(1 for f in self.findings if f.severity.lower() == 'low') if self.findings else 0,
            }
        }
        if include_findings:
            data['findings'] = [f.to_dict() for f in self.findings]
        return data


class ReviewFinding(db.Model):
    __tablename__ = 'review_findings'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    review_id = db.Column(db.Integer, db.ForeignKey('reviews.id', ondelete='CASCADE'), nullable=False, index=True)
    field_name = db.Column(db.String(100), nullable=False) # 'title', 'description', 'price', etc.
    original_value = db.Column(db.Text, nullable=False)
    issue_type = db.Column(db.String(100), nullable=False) # 'misleading_claim', 'prohibited_content', 'unclear_content', etc.
    severity = db.Column(db.String(50), nullable=False, default='Medium') # High, Medium, Low
    issue_description = db.Column(db.Text, nullable=False)
    policy_id = db.Column(db.Integer, db.ForeignKey('policies.id'), nullable=True)
    policy_reference_code = db.Column(db.String(50), nullable=True) # e.g. 'POL-TITLE-001'
    policy_reference_text = db.Column(db.String(255), nullable=True)
    suggested_revision = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text, nullable=False)
    requires_human_review = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    suggestions = db.relationship('Suggestion', backref='finding', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        suggestion = self.suggestions[0] if self.suggestions else None
        return {
            'id': self.id,
            'review_id': self.review_id,
            'field_name': self.field_name,
            'original_value': self.original_value,
            'issue_type': self.issue_type,
            'severity': self.severity,
            'issue_description': self.issue_description,
            'policy_id': self.policy_id,
            'policy_reference_code': self.policy_reference_code or (self.policy.policy_code if self.policy else None),
            'policy_title': self.policy.title if self.policy else self.policy_reference_text,
            'policy_category': self.policy.category if self.policy else None,
            'suggested_revision': self.suggested_revision,
            'explanation': self.explanation,
            'requires_human_review': self.requires_human_review,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'suggestion': suggestion.to_dict() if suggestion else None
        }
