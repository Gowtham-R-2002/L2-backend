from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, User, Role
from functools import wraps

users_bp = Blueprint('users', __name__)

def admin_required(f):
    """Decorator to require admin role"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        current_user_id = int(get_jwt_identity())
        user = User.query.get(current_user_id)
        
        if not user or not user.role or user.role.name != 'Admin':
            return jsonify({'success': False, 'error': 'Admin access required'}), 403
        
        return f(*args, **kwargs)
    return decorated_function

@users_bp.route('', methods=['GET'])
@jwt_required()
@admin_required
def get_users():
    """Get all users (admin only)"""
    try:
        search = request.args.get('search', '')
        role_id = request.args.get('role_id', type=int)
        is_active = request.args.get('is_active', type=bool)
        
        query = User.query
        
        if search:
            query = query.filter(
                db.or_(
                    User.username.contains(search),
                    User.email.contains(search),
                    User.first_name.contains(search),
                    User.last_name.contains(search)
                )
            )
        
        if role_id:
            query = query.filter_by(role_id=role_id)
        
        if is_active is not None:
            query = query.filter_by(is_active=is_active)
        
        users = query.all()
        
        return jsonify({
            'success': True,
            'data': [user.to_dict() for user in users],
            'count': len(users)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@users_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
@admin_required
def get_user(user_id):
    """Get user by ID (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        return jsonify({
            'success': True,
            'data': user.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@users_bp.route('', methods=['POST'])
@jwt_required()
@admin_required
def create_user():
    """Create new user (admin only)"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['username', 'email', 'password', 'first_name', 'last_name', 'role_id']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'success': False, 'error': f'{field} is required'}), 400
        
        # Check if username or email already exists
        if User.query.filter_by(username=data['username']).first():
            return jsonify({'success': False, 'error': 'Username already exists'}), 409
        
        if User.query.filter_by(email=data['email']).first():
            return jsonify({'success': False, 'error': 'Email already exists'}), 409
        
        # Verify role exists
        role = Role.query.get(data['role_id'])
        if not role:
            return jsonify({'success': False, 'error': 'Role not found'}), 404
        
        # Create new user
        user = User(
            username=data['username'],
            email=data['email'],
            first_name=data['first_name'],
            last_name=data['last_name'],
            role_id=data['role_id'],
            is_active=data.get('is_active', True)
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': user.to_dict(),
            'message': 'User created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@users_bp.route('/<int:user_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_user(user_id):
    """Update user (admin only)"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Update allowed fields
        updatable_fields = ['username', 'email', 'first_name', 'last_name', 'role_id', 'is_active']
        
        for field in updatable_fields:
            if field in data:
                if field == 'username' and data[field] != user.username:
                    if User.query.filter_by(username=data[field]).first():
                        return jsonify({'success': False, 'error': 'Username already exists'}), 409
                
                if field == 'email' and data[field] != user.email:
                    if User.query.filter_by(email=data[field]).first():
                        return jsonify({'success': False, 'error': 'Email already exists'}), 409
                
                if field == 'role_id':
                    role = Role.query.get(data[field])
                    if not role:
                        return jsonify({'success': False, 'error': 'Role not found'}), 404
                
                setattr(user, field, data[field])
        
        # Update password if provided
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': user.to_dict(),
            'message': 'User updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@users_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
@admin_required
def delete_user(user_id):
    """Delete user (admin only)"""
    try:
        current_user_id = int(get_jwt_identity())
        
        # Prevent admin from deleting themselves
        if user_id == current_user_id:
            return jsonify({'success': False, 'error': 'Cannot delete your own account'}), 409
        
        user = User.query.get_or_404(user_id)
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'User deleted successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@users_bp.route('/roles', methods=['GET'])
@jwt_required()
def get_roles():
    """Get all roles"""
    try:
        roles = Role.query.all()
        return jsonify({
            'success': True,
            'data': [role.to_dict() for role in roles],
            'count': len(roles)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@users_bp.route('/roles', methods=['POST'])
@jwt_required()
@admin_required
def create_role():
    """Create new role (admin only)"""
    try:
        data = request.get_json()
        
        if not data or not data.get('name'):
            return jsonify({'success': False, 'error': 'Role name is required'}), 400
        
        # Check if role already exists
        if Role.query.filter_by(name=data['name']).first():
            return jsonify({'success': False, 'error': 'Role already exists'}), 409
        
        role = Role(
            name=data['name'],
            description=data.get('description'),
            permissions=data.get('permissions', {})
        )
        
        db.session.add(role)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': role.to_dict(),
            'message': 'Role created successfully'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@users_bp.route('/roles/<int:role_id>', methods=['PUT'])
@jwt_required()
@admin_required
def update_role(role_id):
    """Update role (admin only)"""
    try:
        role = Role.query.get_or_404(role_id)
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Update fields
        updatable_fields = ['name', 'description', 'permissions']
        
        for field in updatable_fields:
            if field in data:
                if field == 'name' and data[field] != role.name:
                    if Role.query.filter_by(name=data[field]).first():
                        return jsonify({'success': False, 'error': 'Role name already exists'}), 409
                
                setattr(role, field, data[field])
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': role.to_dict(),
            'message': 'Role updated successfully'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500 