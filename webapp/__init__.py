from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import os

# Initialize extensions
db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config=None):
    """Create and configure the Flask application"""
    app = Flask(__name__, 
                static_folder='static',
                template_folder='templates')
    
    # Configure the app
    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev_key_replace_in_production'),
        SQLALCHEMY_DATABASE_URI=os.environ.get('DATABASE_URL', 'sqlite:///rfp_finder.db'),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    
    # Override config if provided
    if config:
        app.config.update(config)
    
    # Initialize extensions with the app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    
    # Import models to ensure they're registered with SQLAlchemy
    from webapp.models import User, RFP
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Register blueprints
    from .views.main import main_bp
    from .views.auth import auth_bp
    from .views.rfps import rfps_bp
    from .views.admin import admin_bp
    from .views.notifications import notifications_bp
    from .views.scraper import scraper_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(rfps_bp, url_prefix='/rfps')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(notifications_bp, url_prefix='/notifications')
    app.register_blueprint(scraper_bp, url_prefix='/api/scraper')
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    return app
