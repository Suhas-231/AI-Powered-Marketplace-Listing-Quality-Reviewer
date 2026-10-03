import pytest
from app import create_app
from app.config import TestingConfig
from app.database import db
from app.services.validation_service import ValidationService
from app.models.listing import Listing

@pytest.fixture
def app():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

def test_required_fields_validation(app):
    with app.app_context():
        # Empty payload
        res = ValidationService.validate_listing_payload({})
        assert not res['valid']
        assert 'title' in res['errors']
        assert 'description' in res['errors']
        assert 'category' in res['errors']
        assert 'price' in res['errors']
        assert 'seller' in res['errors']

def test_price_validation(app):
    with app.app_context():
        # Non-numeric price
        res_text = ValidationService.validate_listing_payload({
            'title': 'Valid Title Product',
            'description': 'This is a sufficiently long valid description for testing purposes.',
            'category': 'Electronics & Gadgets',
            'price': 'invalid-price',
            'seller': 'Test Store'
        })
        assert not res_text['valid']
        assert 'price' in res_text['errors']

        # Negative price
        res_neg = ValidationService.validate_listing_payload({
            'title': 'Valid Title Product',
            'description': 'This is a sufficiently long valid description for testing purposes.',
            'category': 'Electronics & Gadgets',
            'price': -10.0,
            'seller': 'Test Store'
        })
        assert not res_neg['valid']
        assert 'price' in res_neg['errors']

        # Zero price
        res_zero = ValidationService.validate_listing_payload({
            'title': 'Valid Title Product',
            'description': 'This is a sufficiently long valid description for testing purposes.',
            'category': 'Electronics & Gadgets',
            'price': 0,
            'seller': 'Test Store'
        })
        assert not res_zero['valid']
        assert 'price' in res_zero['errors']

def test_category_validation(app):
    with app.app_context():
        # Unsupported category
        res = ValidationService.validate_listing_payload({
            'title': 'Valid Title Product',
            'description': 'This is a sufficiently long valid description for testing purposes.',
            'category': 'Unauthorized Category XYZ',
            'price': 29.99,
            'seller': 'Test Store'
        })
        assert not res['valid']
        assert 'category' in res['errors']

def test_title_and_description_lengths(app):
    with app.app_context():
        # Too short title
        res_short = ValidationService.validate_listing_payload({
            'title': 'Abc',
            'description': 'This is a sufficiently long valid description for testing purposes.',
            'category': 'Electronics & Gadgets',
            'price': 15.0,
            'seller': 'Store'
        })
        assert not res_short['valid']
        assert 'title' in res_short['errors']

        # Too short description
        res_short_desc = ValidationService.validate_listing_payload({
            'title': 'Valid Title Product',
            'description': 'Short text',
            'category': 'Electronics & Gadgets',
            'price': 15.0,
            'seller': 'Store'
        })
        assert not res_short_desc['valid']
        assert 'description' in res_short_desc['errors']

def test_duplicate_detection(app):
    with app.app_context():
        # Insert initial listing
        l1 = Listing(
            title="Premium Organic Himalayan Green Tea 250g",
            description="High mountain loose leaf organic green tea freshly harvested and packed.",
            category="Health & Personal Care",
            price=24.99,
            seller="TeaGarden"
        )
        db.session.add(l1)
        db.session.commit()

        # Check exact normalized duplicate
        dup_check = ValidationService.check_duplicate(
            "premium organic himalayan green tea 250g!",
            "Health & Personal Care"
        )
        assert dup_check['is_duplicate'] is True
        assert dup_check['duplicate_id'] == l1.id

        # Exclude self when editing
        dup_self = ValidationService.check_duplicate(
            "premium organic himalayan green tea 250g",
            "Health & Personal Care",
            exclude_id=l1.id
        )
        assert dup_self['is_duplicate'] is False
