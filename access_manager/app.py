"""
Access Manager - Flask Application Entry Point
File Access Management System for Telegram users
"""
import os
from dotenv import load_dotenv

# Load .env from parent directory (bot-tele root)
# __file__ is access_manager/app.py, go up 2 levels to reach bot-tele
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(env_path)

from flask import Flask, session, redirect, url_for
from models import db
from models.user import AdminUser
from werkzeug.security import generate_password_hash


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///access_manager.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Register blueprints
    from routes.auth import auth_bp
    from routes.users import users_bp
    from routes.files import files_bp
    from routes.dashboard import dashboard_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(files_bp)
    app.register_blueprint(dashboard_bp)
    
    # Root route redirects to dashboard
    @app.route('/')
    def root():
        if 'user_id' in session:
            return redirect(url_for('dashboard.index'))
        return redirect(url_for('auth.login'))
    
    # Create tables and default admin
    with app.app_context():
        db.create_all()
        create_default_admin(app)
    
    return app


def create_default_admin(app):
    """Create a default admin user if none exists."""
    with app.app_context():
        if not AdminUser.query.first():
            admin = AdminUser(username='admin')
            admin.password_hash = generate_password_hash('admin123')
            db.session.add(admin)
            db.session.commit()
            print("=" * 50)
            print("Default admin user created!")
            print("Username: admin")
            print("Password: admin123")
            print("=" * 50)


if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
