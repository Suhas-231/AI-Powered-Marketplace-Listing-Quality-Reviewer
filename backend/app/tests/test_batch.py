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
