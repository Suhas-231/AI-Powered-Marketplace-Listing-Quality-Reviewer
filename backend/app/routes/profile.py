import re
import logging
from flask import Blueprint, request, jsonify
from app.database import db
from app.models.user import User
from app.services.audit_service import AuditService

logger = logging.getLogger(__name__)

bp = Blueprint('profile', __name__, url_prefix='/api')

EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$')

@bp.route('/profile', methods=['GET'])
def get_profile():
    """Retrieves the current user's profile information from MySQL."""
    user = User.query.first()
    if not user:
        user = User(
            name="Suhas (Compliance Officer)",
            email="compliance@marketplace.local",
            role="Senior Reviewer"
        )
        db.session.add(user)
        db.session.commit()

    return jsonify({
        'success': True,
        'user': user.to_dict()
    }), 200

@bp.route('/profile', methods=['PUT'])
def update_profile():
    """Updates the current user's full name and email address in MySQL."""
    user = User.query.first()
    if not user:
        return jsonify({'success': False, 'message': 'User profile not found.'}), 404

    data = request.get_json() or {}

    name = data.get('name')
    email = data.get('email')

    # Validate full name
    if name is None or not isinstance(name, str) or not name.strip():
        return jsonify({
            'success': False,
            'message': 'Full name is required and cannot be empty.'
        }), 400

    name = name.strip()
    if len(name) < 2:
        return jsonify({
            'success': False,
            'message': 'Full name must be at least 2 characters long.'
        }), 400

    if len(name) > 100:
        return jsonify({
            'success': False,
            'message': 'Full name cannot exceed 100 characters.'
        }), 400

    # Validate email
    if email is None or not isinstance(email, str) or not email.strip():
        return jsonify({
            'success': False,
            'message': 'Email address is required and cannot be empty.'
        }), 400

    email = email.strip().lower()
    if not EMAIL_REGEX.match(email):
        return jsonify({
            'success': False,
            'message': 'Please provide a valid email address (e.g. name@example.com).'
        }), 400

    if len(email) > 120:
        return jsonify({
            'success': False,
            'message': 'Email address cannot exceed 120 characters.'
        }), 400

    # Check uniqueness against other users in database
    existing_user = User.query.filter(User.email == email, User.id != user.id).first()
    if existing_user:
        return jsonify({
            'success': False,
            'message': f'The email address "{email}" is already registered by another account.'
        }), 409

    # Role & Account ID cannot be modified through this form (strictly preserved)
    previous_name = user.name
    previous_email = user.email

    try:
        user.name = name
        user.email = email
        db.session.commit()

        AuditService.log(
            entity_type='user',
            entity_id=user.id,
            action='updated',
            details={
                'previous_name': previous_name,
                'new_name': user.name,
                'previous_email': previous_email,
                'new_email': user.email
            },
            user_id=user.id
        )

        return jsonify({
            'success': True,
            'message': 'Profile updated successfully.',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to update profile for user #{user.id}: {e}")
        return jsonify({
            'success': False,
            'message': f'Database error updating profile: {str(e)}'
        }), 500
