import pytest
from app import create_app
from app.config import TestingConfig
from app.database import db
from app.models.listing import Listing
from app.models.policy import Policy
from app.models.user import User

@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        user = User(name="Review Tester", email="rev@test.local", role="reviewer")
        db.session.add(user)

        # Seed policy
        p = Policy(
            policy_code="POL-HLTH-001",
            section_number="Section 4.1",
            title="Disease Cure Claims",
            category="Medical and health claims",
            description="Non-certified products must never claim to cure diseases.",
            severity_guidance="High",
            is_active=True,
            is_demo_policy=True
        )
        db.session.add(p)

        # Seed listing
        listing = Listing(
            title="Miracle Herbal Cure Diabetes",
            description="Herbal remedy to cure diabetes and cancer naturally.",
            category="Health & Personal Care",
            price=39.99,
            seller="Vitality"
        )
        db.session.add(listing)
        db.session.commit()

        yield app.test_client()
        db.drop_all()

def test_trigger_ai_review_mock(client):
    # Trigger review
    res = client.post('/api/listings/1/review')
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    review = data['review']
    assert review['status'] == 'completed'
    assert len(review['findings']) > 0
    assert review['policy_coverage'] == 'sample_policy'

    # Check listing status changed to revisions_pending
    l_res = client.get('/api/listings/1')
    assert l_res.get_json()['status'] == 'revisions_pending'

def test_review_validation_failure_prevents_ai_review(client):
    # Create invalid listing directly
    invalid_listing = Listing(
        title="Bad",  # Too short
        description="Short",
        category="Health & Personal Care",
        price=10.0,
        seller="Seller"
    )
    with client.application.app_context():
        db.session.add(invalid_listing)
        db.session.commit()
        inv_id = invalid_listing.id

    # Attempt to trigger review on invalid listing
    res = client.post(f'/api/listings/{inv_id}/review')
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert 'validation_errors' in data


def test_delete_ai_review(client):
    # Trigger review first
    res = client.post('/api/listings/1/review')
    assert res.status_code == 201
    rev_id = res.get_json()['review']['id']

    # Confirm listing status is revisions_pending
    l_res = client.get('/api/listings/1')
    assert l_res.get_json()['status'] == 'revisions_pending'

    # Check reviews list
    rev_list = client.get('/api/reviews')
    assert rev_list.status_code == 200
    assert rev_list.get_json()['total'] == 1

    # Delete review
    del_res = client.delete(f'/api/reviews/{rev_id}')
    assert del_res.status_code == 200
    assert del_res.get_json()['success'] is True

    # Review should no longer exist
    get_res = client.get(f'/api/reviews/{rev_id}')
    assert get_res.status_code == 404

    # Listing status should have reverted to draft
    l_res2 = client.get('/api/listings/1')
    assert l_res2.get_json()['status'] == 'draft'
