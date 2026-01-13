"""
User management routes: profile, user CRUD operations.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_bcrypt import Bcrypt

from app.models import db, User
from app.middleware.auth import token_required, require_role
from app.utils.validators import (
    validate_username,
    validate_email_format,
    validate_password_strength,
    validate_role,
    sanitize_input
)

users_bp = Blueprint('users', __name__, url_prefix='/api')


@users_bp.route('/profile', methods=['GET'])
@token_required
def get_profile(current_user):
    """
    Get current user's profile.
    
    Returns:
        200: User profile data
        401: Unauthorized
    """
    return jsonify({
        'message': 'Profile retrieved successfully',
        'data': current_user.to_dict(include_posts=True)
    }), 200


@users_bp.route('/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    """
    Update current user's profile.
    
    Expected JSON:
        {
            "username": "string" (optional),
            "email": "string" (optional),
            "password": "string" (optional)
        }
    
    Returns:
        200: Profile updated successfully
        400: Validation error
        409: Username or email already exists
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided', 'status': 400}), 400
        
        updated = False
        
        # Update username if provided
        if 'username' in data:
            username = sanitize_input(data['username'])
            is_valid, error = validate_username(username)
            if not is_valid:
                return jsonify({'error': error, 'status': 400}), 400
            
            # Check if username is taken by another user
            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({'error': 'Username already exists', 'status': 409}), 409
            
            current_user.username = username
            updated = True
        
        # Update email if provided
        if 'email' in data:
            email = sanitize_input(data['email'])
            is_valid, error = validate_email_format(email)
            if not is_valid:
                return jsonify({'error': error, 'status': 400}), 400
            
            # Check if email is taken by another user
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != current_user.id:
                return jsonify({'error': 'Email already exists', 'status': 409}), 409
            
            current_user.email = email
            updated = True
        
        # Update password if provided
        if 'password' in data:
            password = data['password']
            is_valid, error = validate_password_strength(password)
            if not is_valid:
                return jsonify({'error': error, 'status': 400}), 400
            
            bcrypt = Bcrypt(current_app)
            current_user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
            updated = True
        
        if updated:
            db.session.commit()
            return jsonify({
                'message': 'Profile updated successfully',
                'data': current_user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'No valid fields to update', 'status': 400}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Profile update failed', 'status': 500}), 500


@users_bp.route('/users', methods=['GET'])
@token_required
@require_role('admin')
def get_users(current_user):
    """
    Get list of all users (admin only).
    
    Returns:
        200: List of users
        403: Forbidden (not admin)
    """
    try:
        users = User.query.all()
        return jsonify({
            'message': 'Users retrieved successfully',
            'data': [user.to_dict() for user in users],
            'count': len(users)
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve users', 'status': 500}), 500


@users_bp.route('/users/<int:user_id>', methods=['GET'])
@token_required
@require_role('admin')
def get_user(current_user, user_id):
    """
    Get specific user by ID (admin only).
    
    Returns:
        200: User data
        404: User not found
        403: Forbidden (not admin)
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found', 'status': 404}), 404
        
        return jsonify({
            'message': 'User retrieved successfully',
            'data': user.to_dict(include_posts=True)
        }), 200
    except Exception as e:
        return jsonify({'error': 'Failed to retrieve user', 'status': 500}), 500


@users_bp.route('/users/<int:user_id>', methods=['PUT'])
@token_required
@require_role('admin')
def update_user(current_user, user_id):
    """
    Update user by ID (admin only).
    
    Expected JSON:
        {
            "username": "string" (optional),
            "email": "string" (optional),
            "is_active": boolean (optional)
        }
    
    Returns:
        200: User updated successfully
        400: Validation error
        404: User not found
        409: Username or email already exists
    """
    try:
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found', 'status': 404}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided', 'status': 400}), 400
        
        updated = False
        
        # Update username if provided
        if 'username' in data:
            username = sanitize_input(data['username'])
            is_valid, error = validate_username(username)
            if not is_valid:
                return jsonify({'error': error, 'status': 400}), 400
            
            existing_user = User.query.filter_by(username=username).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': 'Username already exists', 'status': 409}), 409
            
            user.username = username
            updated = True
        
        # Update email if provided
        if 'email' in data:
            email = sanitize_input(data['email'])
            is_valid, error = validate_email_format(email)
            if not is_valid:
                return jsonify({'error': error, 'status': 400}), 400
            
            existing_user = User.query.filter_by(email=email).first()
            if existing_user and existing_user.id != user.id:
                return jsonify({'error': 'Email already exists', 'status': 409}), 409
            
            user.email = email
            updated = True
        
        # Update is_active if provided
        if 'is_active' in data:
            if not isinstance(data['is_active'], bool):
                return jsonify({'error': 'is_active must be a boolean', 'status': 400}), 400
            user.is_active = data['is_active']
            updated = True
        
        if updated:
            db.session.commit()
            return jsonify({
                'message': 'User updated successfully',
                'data': user.to_dict()
            }), 200
        else:
            return jsonify({'error': 'No valid fields to update', 'status': 400}), 400
            
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'User update failed', 'status': 500}), 500


@users_bp.route('/users/<int:user_id>', methods=['DELETE'])
@token_required
@require_role('admin')
def delete_user(current_user, user_id):
    """
    Delete user by ID (admin only).
    
    Returns:
        200: User deleted successfully
        400: Cannot delete yourself
        404: User not found
    """
    try:
        if current_user.id == user_id:
            return jsonify({'error': 'Cannot delete your own account', 'status': 400}), 400
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found', 'status': 404}), 404
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User deleted successfully'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'User deletion failed', 'status': 500}), 500


@users_bp.route('/users/<int:user_id>/role', methods=['PUT'])
@token_required
@require_role('admin')
def update_user_role(current_user, user_id):
    """
    Update user role (admin only).
    
    Expected JSON:
        {
            "role": "guest|user|admin"
        }
    
    Returns:
        200: Role updated successfully
        400: Validation error or cannot change own role
        404: User not found
    """
    try:
        if current_user.id == user_id:
            return jsonify({'error': 'Cannot change your own role', 'status': 400}), 400
        
        user = User.query.get(user_id)
        
        if not user:
            return jsonify({'error': 'User not found', 'status': 404}), 404
        
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided', 'status': 400}), 400
        
        role = data.get('role', '')
        
        is_valid, error = validate_role(role)
        if not is_valid:
            return jsonify({'error': error, 'status': 400}), 400
        
        user.role = role
        db.session.commit()
        
        return jsonify({
            'message': 'User role updated successfully',
            'data': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Role update failed', 'status': 500}), 500
