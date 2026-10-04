import pytest
from app import create_app
from app.config import TestingConfig
from app.database import db
from app.models.listing import Listing
from app.models.user import User

@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        user = User(name="Batch Tester", email="batch@test.local", role="reviewer")
        db.session.add(user)
        
        l1 = Listing(
            title="Valid Listing 1 For Batch Review",
            description="Complete product description with required information and details.",
            category="Electronics & Gadgets",
            price=99.0,
            seller="Vendor 1"
        )
        l2 = Listing(
            title="Miracle Herbal Cure Diabetes Listing 2",
            description="Miraculous tea cure for diabetes and cancer WhatsApp +1-555.",
            category="Health & Personal Care",
            price=29.0,
            seller="Vendor 2"
        )
        db.session.add_all([l1, l2])
        db.session.commit()
        yield app.test_client()
        db.drop_all()

def test_batch_review_processing(client):
    # Submit both listings plus non-existent ID 999
    res = client.post('/api/batch/review', json={'listing_ids': [1, 2, 999]})
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['total_processed'] == 3
    assert data['successful'] == 2
    assert data['failed'] == 1

    results = data['results']
    # Check non-existent listing failed safely without aborting batch
    failed_item = next(r for r in results if r['listing_id'] == 999)
    assert failed_item['status'] == 'failed'

    # Check valid listings succeeded
    success_item = next(r for r in results if r['listing_id'] == 1)
    assert success_item['status'] == 'success'
    assert 'review_id' in success_item

def test_csv_batch_import(client):
    csv_data = """title,description,category,price,currency,listing_type,seller,tags,attributes
"Compact Wireless Ergonomic Mouse","High precision optical sensor ergonomic mouse with silent clicks.","Electronics & Gadgets",29.99,USD,Product,"TechDirect","mouse,wireless","{""DPI"":""1600""}"
"Invalid Row Missing Fields","Short","Electronics & Gadgets",-5.0,USD,Product,""
"""
    res = client.post('/api/batch/import-csv', json={'csv_content': csv_data})
    assert res.status_code == 201
    data = res.get_json()
    assert data['success'] is True
    assert data['imported_count'] == 1
    assert data['errors_count'] == 1

def test_batch_mixed_listings_with_error_isolation_and_retry(client):
    """
    Tests batch review of three listings:
    - Listing 1: normal compliant listing (succeeds)
    - Listing 2: listing with medical claims (succeeds with high severity findings)
    - Listing 3: simulated listing failure (e.g. json_validate_failed)
    Verifies that:
    1. One failure does not halt processing of other listings in batch.
    2. Successful results are persisted.
    3. Retrying only the failed listing succeeds and creates no duplicate reviews.
    """
    from unittest.mock import patch
    from app.services.groq_service import GroqService
    from app.models.review import Review

    # Create listing 3
    with client.application.app_context():
        l3 = Listing(
            title="Listing 3 Candidate For Retry",
            description="High quality cotton canvas backpack with laptop compartment.",
            category="Fashion & Apparel",
            price=49.0,
            seller="Backpack Co"
        )
        db.session.add(l3)
        db.session.commit()
        l3_id = l3.id

    # Mock GroqService: Listing 1 & 2 succeed, Listing 3 fails with json_validate_failed
    original_analyze = GroqService.analyze_listing

    def selective_analyze(listing_dict, policies):
        if listing_dict.get('title') == "Listing 3 Candidate For Retry":
            raise RuntimeError("Groq API model 'openai/gpt-oss-20b' failed JSON validation (json_validate_failed) after 4 attempts.")
        return original_analyze(listing_dict, policies)

    with patch('app.routes.batch.GroqService.analyze_listing', side_effect=selective_analyze):
        batch_res = client.post('/api/batch/review', json={'listing_ids': [1, 2, l3_id]})
        assert batch_res.status_code == 200
        batch_data = batch_res.get_json()
        assert batch_data['total_processed'] == 3
        assert batch_data['successful'] == 2
        assert batch_data['failed'] == 1

        results = batch_data['results']
        failed_item = next(r for r in results if r['listing_id'] == l3_id)
        assert failed_item['status'] == 'failed'
        assert 'json_validate_failed' in failed_item['error']

    # Verify database state after initial batch:
    with client.application.app_context():
        reviews_1 = Review.query.filter_by(listing_id=1).all()
        reviews_2 = Review.query.filter_by(listing_id=2).all()
        reviews_3 = Review.query.filter_by(listing_id=l3_id).all()
        assert len(reviews_1) == 1
        assert len(reviews_2) == 1
        assert len(reviews_3) == 0  # Failed listing rolled back, no corrupted record

    # Now simulate 'Retry Failed Listings': submit ONLY failed listing ID [l3_id]
    retry_res = client.post('/api/batch/review', json={'listing_ids': [l3_id]})
    assert retry_res.status_code == 200
    retry_data = retry_res.get_json()
    assert retry_data['successful'] == 1
    assert retry_data['failed'] == 0

    # Verify database state after retry:
    with client.application.app_context():
        reviews_1_post = Review.query.filter_by(listing_id=1).all()
        reviews_2_post = Review.query.filter_by(listing_id=2).all()
        reviews_3_post = Review.query.filter_by(listing_id=l3_id).all()
        # Listing 3 now has exactly 1 review
        assert len(reviews_3_post) == 1
        assert reviews_3_post[0].status == 'completed'
        # Listings 1 and 2 STILL have exactly 1 review (no duplicates!)
        assert len(reviews_1_post) == 1
        assert len(reviews_2_post) == 1
