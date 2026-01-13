"""
Application entry point.
Runs the Flask development server.
"""
import os
from app import create_app

# Create Flask application
app = create_app()

if __name__ == '__main__':
    # Get configuration from environment
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print(f"Starting Flask Auth App on {host}:{port}")
    print(f"Debug mode: {debug}")
    
    app.run(host=host, port=port, debug=debug)
