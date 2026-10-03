import pytest
from app import create_app
from app.config import TestingConfig
from app.database import db
from app.models.policy import Policy
from app.models.listing import Listing
from app.services.policy_service import PolicyService

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        # Seed test policies
        p1 = Policy(
            policy_code="POL-TITLE-001",
            section_number="Section 1.1",
            title="Title Formatting Limits",
            category="Product title guidelines",
            description="Titles must not exceed 150 characters and avoid emojis.",
            severity_guidance="Medium",
            is_active=True,
            is_demo_policy=True
        )
        p2 = Policy(
            policy_code="POL-HLTH-001",
            section_number="Section 4.1",
            title="Disease Cure Claims",
            category="Medical and health claims",
            description="Non-certified products must never claim to cure diseases.",
            severity_guidance="High",
            is_active=True,
            is_demo_policy=True
        )
        db.session.add_all([p1, p2])
        db.session.commit()
        yield app
        db.drop_all()

def test_policy_retrieval(app):
    with app.app_context():
        listing = Listing(
            title="Miracle Herbal Cure for Diabetes",
            description="Will cure diabetes and illnesses in two days.",
            category="Health & Personal Care",
            price=30.0,
            seller="Herbals"
        )
        policies = PolicyService.retrieve_relevant_policies(listing)
        assert len(policies) > 0
        codes = [p.policy_code for p in policies]
        assert "POL-HLTH-001" in codes

def test_verify_policy_citations(app):
    with app.app_context():
        findings = [
            {
                "field": "title",
                "original_value": "Miracle cure",
                "issue_type": "misleading_claim",
                "severity": "High",
                "issue": "Cannot promise cure",
                "policy_section": "POL-HLTH-001",
                "suggested_revision": "Herbal supplement",
                "explanation": "Complies with rules"
            },
            {
                "field": "description",
                "original_value": "Invented claim",
                "issue_type": "unknown",
                "severity": "Low",
                "issue": "Fabricated reference test",
                "policy_section": "POL-FAKE-999",
                "suggested_revision": "Clean desc",
                "explanation": "Testing hallucination"
            }
        ]

        verified = PolicyService.verify_policy_citations(findings)
        assert len(verified) == 2
        # Real policy
        assert verified[0]["citation_verified"] is True
        assert verified[0]["policy_reference_code"] == "POL-HLTH-001"
        assert verified[0]["policy_id"] is not None
        # Hallucinated policy
        assert verified[1]["citation_verified"] is False
        assert verified[1]["policy_id"] is None
