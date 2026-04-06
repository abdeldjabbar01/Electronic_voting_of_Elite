"""Flask web application initialization."""
from flask import Flask
from .routes import init_routes


def create_app() -> Flask:
    """Application factory for creating Flask app."""
    app = Flask(__name__, 
                template_folder='templates',
                static_folder='static')
    
    # Load configuration
    app.config['SECRET_KEY'] = 'your-secret-key-change-in-production'
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
    
    # Initialize routes
    init_routes(app)
    
    return app
