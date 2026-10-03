from flask import Blueprint, request, jsonify
from app.database import db
from app.models.policy import Policy
from app.models.user import User
from app.services.audit_service import AuditService

bp = Blueprint('policies', __name__, url_prefix='/api/policies')

@bp.route('', methods=['GET'])
def get_policies():
    """
    Retrieves policies with filtering by category, active status, search query, and sorting.
    """
    category = request.args.get('category')
    active_only = request.args.get('active_only')
    search = request.args.get('search', '').strip()

    query = Policy.query

    if category and category != 'all':
        query = query.filter(Policy.category == category)
    if active_only is not None and active_only != '':
        is_act = active_only.lower() in ['true', '1']
        query = query.filter(Policy.is_active == is_act)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            (Policy.title.ilike(search_filter)) |
            (Policy.policy_code.ilike(search_filter)) |
            (Policy.description.ilike(search_filter)) |
            (Policy.category.ilike(search_filter))
        )

    policies = query.order_by(Policy.category.asc(), Policy.policy_code.asc()).all()

    categories = [c[0] for c in db.session.query(Policy.category).distinct().all()]

    return jsonify({
        'policies': [p.to_dict() for p in policies],
        'total': len(policies),
        'categories': categories,
        'notice': "Demonstration policy knowledge base. Replace these sample rules with official marketplace policy before production use."
    }), 200


@bp.route('', methods=['POST'])
def create_policy():
    """Creates a new policy rule."""
    data = request.get_json() or {}
    user = User.query.first()

    required_fields = ['policy_code', 'section_number', 'title', 'category', 'description']
    missing = [f for f in required_fields if not data.get(f)]
    if missing:
        return jsonify({'success': False, 'message': f"Missing required fields: {', '.join(missing)}"}), 400

    # Check unique policy_code
    code = data['policy_code'].strip().upper()
    if Policy.query.filter_by(policy_code=code).first():
        return jsonify({'success': False, 'message': f"Policy code '{code}' already exists."}), 400

    policy = Policy(
        policy_code=code,
        section_number=data['section_number'].strip(),
        title=data['title'].strip(),
        category=data['category'].strip(),
        description=data['description'].strip(),
        severity_guidance=data.get('severity_guidance', 'Medium'),
        is_active=bool(data.get('is_active', True)),
        is_demo_policy=bool(data.get('is_demo_policy', False))
    )

    db.session.add(policy)
    db.session.commit()

    AuditService.log(
        entity_type='policy',
        entity_id=policy.id,
        action='created',
        details={'policy_code': policy.policy_code, 'title': policy.title},
        user_id=user.id if user else None
    )

    return jsonify({
        'success': True,
        'message': f"Policy '{policy.policy_code}' created successfully.",
        'policy': policy.to_dict()
    }), 201


@bp.route('/<int:policy_id>', methods=['PUT'])
def update_policy(policy_id):
    """Updates an existing policy rule or toggles active status."""
    policy = Policy.query.get_or_404(policy_id)
    data = request.get_json() or {}
    user = User.query.first()

    if 'title' in data:
        policy.title = data['title'].strip()
    if 'section_number' in data:
        policy.section_number = data['section_number'].strip()
    if 'category' in data:
        policy.category = data['category'].strip()
    if 'description' in data:
        policy.description = data['description'].strip()
    if 'severity_guidance' in data:
        policy.severity_guidance = data['severity_guidance']
    if 'is_active' in data:
        policy.is_active = bool(data['is_active'])

    db.session.commit()

    AuditService.log(
        entity_type='policy',
        entity_id=policy.id,
        action='updated',
        details={'policy_code': policy.policy_code, 'is_active': policy.is_active},
        user_id=user.id if user else None
    )

    return jsonify({
        'success': True,
        'message': f"Policy '{policy.policy_code}' updated successfully.",
        'policy': policy.to_dict()
    }), 200


@bp.route('/<int:policy_id>', methods=['DELETE'])
def delete_policy(policy_id):
    """Deletes a policy rule."""
    policy = Policy.query.get_or_404(policy_id)
    policy_code = policy.policy_code
    user = User.query.first()

    db.session.delete(policy)
    db.session.commit()

    AuditService.log(
        entity_type='policy',
        entity_id=policy_id,
        action='deleted',
        details={'policy_code': policy_code},
        user_id=user.id if user else None
    )

    return jsonify({'success': True, 'message': f"Policy '{policy_code}' deleted successfully."}), 200
