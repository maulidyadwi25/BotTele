"""
Flask application factory for access_manager web dashboard.
Now uses the consolidated dirops database instead of its own SQLite.
"""
import os
import sys

# Add parent directory to path to import dirops_service
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flask import Flask
from dirops_service.database import db
from dirops_service.config import get_config


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # Get configuration from dirops config
    config = get_config()
    app.config.from_object(config)

    # Override secret key if needed
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize database (uses dirops database)
    db.init_app(app)

    # Register blueprints
    from access_manager.routes.auth import auth_bp
    from access_manager.routes.users import users_bp
    from access_manager.routes.files import files_bp
    from access_manager.routes.dashboard import dashboard_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(dashboard_bp)

    # Create tables and default admin
    with app.app_context():
        db.create_all()
        create_default_admin(app)

    return app


def create_default_admin(app):
    """Create a default admin user if none exists."""
    from dirops_service.models import AdminUser

    with app.app_context():
        if not AdminUser.query.first():
            admin = AdminUser(username='admin')
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
            print("Default admin user created: admin / admin123")
