"""
Authentication routes: register, login, refresh, logout.
"""
from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import jwt
from datetime import datetime, timedelta

from app.models import db, User, TokenBlacklist
from app.utils.validators import (
    validate_username,
    validate_email_format,
    validate_password_strength,
    sanitize_input
)

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

# Initialize limiter (will be configured in app factory)
limiter = Limiter(key_func=get_remote_address)


def generate_access_token(user_id):
    """Generate JWT access token."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + current_app.config['JWT_ACCESS_TOKEN_EXPIRES'],
        'iat': datetime.utcnow(),
        'type': 'access'
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm=current_app.config['JWT_ALGORITHM'])


def generate_refresh_token(user_id):
    """Generate JWT refresh token."""
    payload = {
        'user_id': user_id,
        'exp': datetime.utcnow() + current_app.config['JWT_REFRESH_TOKEN_EXPIRES'],
        'iat': datetime.utcnow(),
        'type': 'refresh'
    }
    return jwt.encode(payload, current_app.config['JWT_SECRET_KEY'], algorithm=current_app.config['JWT_ALGORITHM'])


@auth_bp.route('/register', methods=['POST'])
@limiter.limit("5 per 15 minutes")
def register():
    """
    Register a new user.
    
    Expected JSON:
        {
            "username": "string",
            "email": "string",
            "password": "string"
        }
    
    Returns:
        201: User created successfully
        400: Validation error
        409: Username or email already exists
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided', 'status': 400}), 400
        
        # Extract and sanitize inputs
        username = sanitize_input(data.get('username', ''))
        email = sanitize_input(data.get('email', ''))
        password = data.get('password', '')
        
        # Validate username
        is_valid, error = validate_username(username)
        if not is_valid:
            return jsonify({'error': error, 'status': 400}), 400
        
        # Validate email
        is_valid, error = validate_email_format(email)
        if not is_valid:
            return jsonify({'error': error, 'status': 400}), 400
        
        # Validate password strength
        is_valid, error = validate_password_strength(password)
        if not is_valid:
            return jsonify({'error': error, 'status': 400}), 400
        
        # Check if username already exists
        if User.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists', 'status': 409}), 409
        
        # Check if email already exists
        if User.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists', 'status': 409}), 409
        
        # Hash password
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt(current_app)
        password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        
        # Create new user
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role='user'  # Default role
        )
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': 'User registered successfully',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Registration failed', 'status': 500}), 500


@auth_bp.route('/login', methods=['POST'])
@limiter.limit("5 per 15 minutes")
def login():
    """
    Authenticate user and return JWT tokens.
    
    Expected JSON:
        {
            "username": "string",  # or "email"
            "password": "string"
        }
    
    Returns:
        200: Login successful with tokens
        400: Missing credentials
        401: Invalid credentials
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided', 'status': 400}), 400
        
        username = sanitize_input(data.get('username', ''))
        email = sanitize_input(data.get('email', ''))
        password = data.get('password', '')
        
        if not password:
            return jsonify({'error': 'Password is required', 'status': 400}), 400
        
        # Find user by username or email
        user = None
        if username:
            user = User.query.filter_by(username=username).first()
        elif email:
            user = User.query.filter_by(email=email).first()
        else:
            return jsonify({'error': 'Username or email is required', 'status': 400}), 400
        
        if not user:
            return jsonify({'error': 'Invalid credentials', 'status': 401}), 401
        
        # Check if user is active
        if not user.is_active:
            return jsonify({'error': 'User account is inactive', 'status': 401}), 401
        
        # Verify password
        from flask_bcrypt import Bcrypt
        bcrypt = Bcrypt(current_app)
        if not bcrypt.check_password_hash(user.password_hash, password):
            return jsonify({'error': 'Invalid credentials', 'status': 401}), 401
        
        # Generate tokens
        access_token = generate_access_token(user.id)
        refresh_token = generate_refresh_token(user.id)
        
        return jsonify({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token,
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': 'Login failed', 'status': 500}), 500


@auth_bp.route('/refresh', methods=['POST'])
def refresh():
    """
    Refresh access token using refresh token.
    
    Expected JSON:
        {
            "refresh_token": "string"
        }
    
    Returns:
        200: New access token
        400: Missing refresh token
        401: Invalid or expired refresh token
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided', 'status': 400}), 400
        
        refresh_token = data.get('refresh_token', '')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required', 'status': 400}), 400
        
        # Check if token is blacklisted
        if TokenBlacklist.is_blacklisted(refresh_token):
            return jsonify({'error': 'Token has been revoked', 'status': 401}), 401
        
        # Decode and validate refresh token
        try:
            payload = jwt.decode(
                refresh_token,
                current_app.config['JWT_SECRET_KEY'],
                algorithms=[current_app.config['JWT_ALGORITHM']]
            )
            
            if payload.get('type') != 'refresh':
                return jsonify({'error': 'Invalid token type', 'status': 401}), 401
            
            user_id = payload['user_id']
            
            # Verify user still exists and is active
            user = User.query.get(user_id)
            if not user or not user.is_active:
                return jsonify({'error': 'User not found or inactive', 'status': 401}), 401
            
            # Generate new access token
            new_access_token = generate_access_token(user_id)
            
            return jsonify({
                'message': 'Token refreshed successfully',
                'access_token': new_access_token
            }), 200
            
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Refresh token has expired', 'status': 401}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid refresh token', 'status': 401}), 401
            
    except Exception as e:
        return jsonify({'error': 'Token refresh failed', 'status': 500}), 500


@auth_bp.route('/logout', methods=['POST'])
def logout():
    """
    Logout user by blacklisting the refresh token.
    
    Expected JSON:
        {
            "refresh_token": "string"
        }
    
    Returns:
        200: Logout successful
        400: Missing refresh token
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided', 'status': 400}), 400
        
        refresh_token = data.get('refresh_token', '')
        
        if not refresh_token:
            return jsonify({'error': 'Refresh token is required', 'status': 400}), 400
        
        # Check if already blacklisted
        if not TokenBlacklist.is_blacklisted(refresh_token):
            # Add to blacklist
            blacklisted_token = TokenBlacklist(token=refresh_token)
            db.session.add(blacklisted_token)
            db.session.commit()
        
        return jsonify({
            'message': 'Logout successful'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': 'Logout failed', 'status': 500}), 500
