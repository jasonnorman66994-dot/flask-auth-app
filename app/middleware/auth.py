"""
Authentication middleware and decorators for JWT token validation and role-based access control.
"""
from functools import wraps
from flask import request, jsonify, current_app
import jwt
from datetime import datetime

from app.models import User, TokenBlacklist


def token_required(f):
    """
    Decorator to require valid JWT token for route access.
    Extracts and validates JWT from Authorization header.
    Attaches user object to kwargs as 'current_user'.
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Extract token from Authorization header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(' ')[1]  # Format: "Bearer <token>"
            except IndexError:
                return jsonify({'error': 'Invalid token format', 'status': 401}), 401
        
        if not token:
            return jsonify({'error': 'Missing authentication token', 'status': 401}), 401
        
        # Check if token is blacklisted
        if TokenBlacklist.is_blacklisted(token):
            return jsonify({'error': 'Token has been revoked', 'status': 401}), 401
        
        try:
            # Decode and validate token
            data = jwt.decode(
                token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            
            # Get user from database
            current_user = User.query.get(data['user_id'])
            
            if not current_user:
                return jsonify({'error': 'User not found', 'status': 401}), 401
            
            if not current_user.is_active:
                return jsonify({'error': 'User account is inactive', 'status': 401}), 401
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token has expired', 'status': 401}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token', 'status': 401}), 401
        except Exception as e:
            return jsonify({'error': 'Token validation failed', 'status': 401}), 401
        
        # Pass current_user to the route
        return f(current_user=current_user, *args, **kwargs)
    
    return decorated


def require_role(*allowed_roles):
    """
    Decorator to require specific role(s) for route access.
    Implements role hierarchy: guest < user < admin
    
    Args:
        allowed_roles: Variable number of role strings (e.g., 'admin', 'user')
    """
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            # Define role hierarchy
            role_hierarchy = {
                'guest': 0,
                'user': 1,
                'admin': 2
            }
            
            # Get user's role level
            user_role_level = role_hierarchy.get(current_user.role, -1)
            
            # Get minimum required role level
            required_level = min([role_hierarchy.get(role, 999) for role in allowed_roles])
            
            # Check if user has sufficient permissions
            if user_role_level < required_level:
                return jsonify({
                    'error': 'Insufficient permissions',
                    'status': 403,
                    'required_role': allowed_roles[0] if len(allowed_roles) == 1 else list(allowed_roles)
                }), 403
            
            return f(current_user=current_user, *args, **kwargs)
        
        return decorated
    
    return decorator


def require_permission(permission):
    """
    Decorator to check specific permissions (for future extensibility).
    Currently implements basic permission checking.
    
    Args:
        permission (str): Permission name to check
    """
    def decorator(f):
        @wraps(f)
        def decorated(current_user, *args, **kwargs):
            # Permission mapping (can be extended)
            permissions_map = {
                'read': ['guest', 'user', 'admin'],
                'write': ['user', 'admin'],
                'delete': ['admin'],
                'manage_users': ['admin']
            }
            
            allowed_roles = permissions_map.get(permission, [])
            
            if current_user.role not in allowed_roles:
                return jsonify({
                    'error': f'Permission denied: {permission}',
                    'status': 403
                }), 403
            
            return f(current_user=current_user, *args, **kwargs)
        
        return decorated
    
    return decorator
