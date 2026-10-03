import pytest
from app import create_app
from app.config import TestingConfig
from app.database import db
from app.models.user import User

@pytest.fixture
def client():
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        # Seed test user
        user = User(
            name="Suhas (Compliance Officer)",
            email="compliance@marketplace.local",
            role="Senior Reviewer",
            password_hash="secret_hashed_password"
        )
        db.session.add(user)
        db.session.commit()

        yield app.test_client()
        db.drop_all()

def test_get_profile(client):
    res = client.get('/api/profile')
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    user = data['user']
    assert user['name'] == "Suhas (Compliance Officer)"
    assert user['email'] == "compliance@marketplace.local"
    assert user['role'] == "Senior Reviewer"
    assert 'password_hash' not in user
    assert 'id' in user
    assert 'created_at' in user

def test_update_profile_success(client):
    res = client.put('/api/profile', json={
        'name': "Suhas K. Sharma",
        'email': "suhas.sharma@marketplace.io"
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['success'] is True
    assert data['user']['name'] == "Suhas K. Sharma"
    assert data['user']['email'] == "suhas.sharma@marketplace.io"

    # Verify persisted in database
    with client.application.app_context():
        db_user = User.query.first()
        assert db_user.name == "Suhas K. Sharma"
        assert db_user.email == "suhas.sharma@marketplace.io"
        assert db_user.role == "Senior Reviewer"

def test_update_profile_validation_empty_name(client):
    res = client.put('/api/profile', json={
        'name': "   ",
        'email': "suhas@marketplace.io"
    })
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert "Full name is required" in data['message']

def test_update_profile_validation_invalid_email(client):
    res = client.put('/api/profile', json={
        'name': "Valid Name",
        'email': "not-an-email"
    })
    assert res.status_code == 400
    data = res.get_json()
    assert data['success'] is False
    assert "valid email" in data['message'].lower()

def test_update_profile_duplicate_email(client):
    # Create a second user in db
    with client.application.app_context():
        user2 = User(
            name="Another User",
            email="existing@marketplace.local",
            role="Auditor"
        )
        db.session.add(user2)
        db.session.commit()

    # Attempt to update first user's email to user2's email
    res = client.put('/api/profile', json={
        'name': "Suhas",
        'email': "existing@marketplace.local"
    })
    assert res.status_code == 409
    data = res.get_json()
    assert data['success'] is False
    assert "already registered" in data['message']

def test_update_profile_role_and_id_tamper_resistant(client):
    # Attempt to tamper with role and id
    res = client.put('/api/profile', json={
        'name': "Suhas Modified",
        'email': "suhas.mod@marketplace.local",
        'role': "SuperAdmin",
        'id': 9999
    })
    assert res.status_code == 200
    data = res.get_json()
    assert data['user']['role'] == "Senior Reviewer" # Role preserved!
    assert data['user']['id'] != 9999 # ID preserved!

    with client.application.app_context():
        db_user = User.query.first()
        assert db_user.role == "Senior Reviewer"
        assert db_user.id != 9999
