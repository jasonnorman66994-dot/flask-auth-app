"""
Flask application factory.
Creates and configures the Flask application with all extensions and blueprints.
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_bcrypt import Bcrypt
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from config import config
from app.models import db


def create_app(config_name=None):
    """
    Application factory pattern for Flask app creation.
    
    Args:
        config_name (str): Configuration environment name (development, production, testing)
        
    Returns:
        Flask: Configured Flask application
    """
    # Create Flask app
    app = Flask(__name__)
    
    # Load configuration
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    CORS(app)
    Bcrypt(app)
    
    # Initialize rate limiter
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        storage_uri=app.config['RATELIMIT_STORAGE_URL'],
        default_limits=[app.config['RATELIMIT_DEFAULT']]
    )
    
    # Register blueprints
    from app.routes.auth import auth_bp, limiter as auth_limiter
    from app.routes.users import users_bp
    from app.routes.protected import protected_bp
    
    # Configure limiter for auth blueprint
    auth_limiter.init_app(app)
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(protected_bp)
    
    # Error handlers
    @app.errorhandler(400)
    def bad_request(e):
        return jsonify({'error': 'Bad request', 'status': 400}), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        return jsonify({'error': 'Unauthorized', 'status': 401}), 401
    
    @app.errorhandler(403)
    def forbidden(e):
        return jsonify({'error': 'Forbidden', 'status': 403}), 403
    
    @app.errorhandler(404)
    def not_found(e):
        return jsonify({'error': 'Resource not found', 'status': 404}), 404
    
    @app.errorhandler(409)
    def conflict(e):
        return jsonify({'error': 'Conflict', 'status': 409}), 409
    
    @app.errorhandler(429)
    def ratelimit_handler(e):
        return jsonify({
            'error': 'Too many requests. Please try again later.',
            'status': 429
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return jsonify({'error': 'Internal server error', 'status': 500}), 500
    
    # Health check endpoint
    @app.route('/')
    def index():
        return jsonify({
            'message': 'Flask Auth App API',
            'version': '1.0.0',
            'status': 'running'
        }), 200
    
    @app.route('/health')
    def health():
        return jsonify({'status': 'healthy'}), 200
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
