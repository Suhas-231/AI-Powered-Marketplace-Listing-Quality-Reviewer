import pytest
from app import create_app
from app.config import TestingConfig
from app.database import db
from app.models.listing import Listing

@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.drop_all()

def test_create_and_get_listing(client):
    payload = {
        'title': 'Ergonomic Office Chair with Lumbar Support',
        'description': 'High back breathable mesh executive desk chair with adjustable 3D armrests and tilt lock.',
        'category': 'Home & Kitchen',
        'price': 189.99,
        'currency': 'USD',
        'listing_type': 'Product',
        'seller': 'OfficeComfort Direct',
        'attributes': {'Color': 'Black', 'Weight Capacity': '300 lbs'},
        'tags': ['chair', 'ergonomic', 'office']
    }

    create_res = client.post('/api/listings', json=payload)
    assert create_res.status_code == 201
    created = create_res.get_json()
    assert created['success'] is True
    listing_id = created['listing']['id']

    get_res = client.get(f'/api/listings/{listing_id}')
    assert get_res.status_code == 200
    listing = get_res.get_json()
    assert listing['title'] == payload['title']
    assert listing['price'] == 189.99
    assert listing['category'] == 'Home & Kitchen'

def test_dashboard_stats(client):
    # Test dashboard statistics on empty and populated DB
    stats_empty = client.get('/api/dashboard/stats')
    assert stats_empty.status_code == 200
    assert stats_empty.get_json()['summary']['total_listings'] == 0

    # Create a listing
    client.post('/api/listings', json={
        'title': 'Stainless Steel Kitchen Chef Knife 8 Inch',
        'description': 'High carbon stainless steel precision forged chef knife for professional cooking.',
        'category': 'Home & Kitchen',
        'price': 49.95,
        'seller': 'CulinaryMaster'
    })

    stats_res = client.get('/api/dashboard/stats')
    assert stats_res.status_code == 200
    data = stats_res.get_json()
    assert data['summary']['total_listings'] == 1


def test_revisions_applied_cannot_be_edited(client):
    # Create listing directly
    with client.application.app_context():
        listing = Listing(
            title="Original Valid Title Here",
            description="Original valid description that is long enough.",
            category="Home & Kitchen",
            price=29.99,
            seller="KitchenCo",
            status="revisions_applied"
        )
        db.session.add(listing)
        db.session.commit()
        l_id = listing.id

    # Attempt to edit/update listing
    update_res = client.put(f'/api/listings/{l_id}', json={
        'title': 'New Updated Title Here',
        'description': 'Original valid description that is long enough.',
        'category': 'Home & Kitchen',
        'price': 29.99,
        'seller': 'KitchenCo'
    })
    assert update_res.status_code == 400
    data = update_res.get_json()
    assert data['success'] is False
    assert 'cannot be edited once revisions have been applied' in data['message']

