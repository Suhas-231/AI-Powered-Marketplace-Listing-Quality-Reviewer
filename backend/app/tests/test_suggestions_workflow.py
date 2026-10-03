import pytest
from app import create_app
from app.config import TestingConfig
from app.database import db
from app.models.listing import Listing
from app.models.review import Review, ReviewFinding
from app.models.suggestion import Suggestion
from app.models.action import ReviewAction
from app.models.audit import AuditLog
from app.models.user import User

@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        # Create user
        user = User(name="Inspector", email="inspector@test.com", role="reviewer")
        db.session.add(user)
        # Create listing
        listing = Listing(
            user_id=1,
            title="BAD TITLE WITH MIRACLE CLAIMS",
            description="Original description text that has no issues.",
            category="Health & Personal Care",
            price=45.0,
            seller="Vendor X",
            status="pending_review"
        )
        db.session.add(listing)
        db.session.flush()

        # Create review & finding & suggestion
        review = Review(
            listing_id=listing.id,
            status="completed",
            summary="Review with 1 finding",
            overall_status="needs_review",
            model_name="mock-model"
        )
        db.session.add(review)
        db.session.flush()

        finding = ReviewFinding(
            review_id=review.id,
            field_name="title",
            original_value="BAD TITLE WITH MIRACLE CLAIMS",
            issue_type="misleading_claim",
            severity="High",
            issue_description="Miracle claim in title",
            suggested_revision="Clean Compliant Title For Tea",
            explanation="Complies with rules"
        )
        db.session.add(finding)
        db.session.flush()

        suggestion = Suggestion(
            finding_id=finding.id,
            original_value=finding.original_value,
            suggested_value=finding.suggested_revision,
            action_status="pending"
        )
        db.session.add(suggestion)
        db.session.commit()

        yield app.test_client()
        db.drop_all()

def test_approve_suggestion_updates_listing_and_creates_action(client):
    # Approve suggestion #1
    res = client.post('/api/suggestions/1/approve', json={'comments': 'Approved clean title'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['suggestion']['action_status'] == 'approved'

    # Verify listing title was updated in database
    listing_res = client.get('/api/listings/1')
    assert listing_res.status_code == 200
    listing_data = listing_res.get_json()
    assert listing_data['title'] == "Clean Compliant Title For Tea"
    assert listing_data['status'] == "revisions_applied"

    # Verify ReviewAction and AuditLog were recorded
    history_res = client.get('/api/listings/1/history')
    assert history_res.status_code == 200
    hist = history_res.get_json()
    assert len(hist['actions']) == 1
    assert hist['actions'][0]['action'] == 'approve'
    assert hist['actions'][0]['new_value'] == "Clean Compliant Title For Tea"

def test_reject_suggestion_preserves_original_listing_field(client):
    # Reject suggestion #1
    res = client.post('/api/suggestions/1/reject', json={'reason': 'Seller provided clinical documentation'})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['suggestion']['action_status'] == 'rejected'

    # Listing title must remain untouched
    listing_res = client.get('/api/listings/1')
    listing_data = listing_res.get_json()
    assert listing_data['title'] == "BAD TITLE WITH MIRACLE CLAIMS"

    # Verify Action logged
    history_res = client.get('/api/listings/1/history')
    hist = history_res.get_json()
    assert len(hist['actions']) == 1
    assert hist['actions'][0]['action'] == 'reject'

def test_edit_suggestion_and_apply(client):
    # Edit suggestion and apply
    res = client.put('/api/suggestions/1', json={
        'final_value': 'Custom Edited Botanical Herbal Tea 250g',
        'apply': True,
        'comments': 'Customized by reviewer'
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['suggestion']['action_status'] == 'approved'
    assert data['suggestion']['final_value'] == 'Custom Edited Botanical Herbal Tea 250g'

    # Verify listing was updated with edited value
    listing_res = client.get('/api/listings/1')
    listing_data = listing_res.get_json()
    assert listing_data['title'] == 'Custom Edited Botanical Herbal Tea 250g'
