"""
Database connection for bot.py using the access_manager database.
This module provides the same interface as the original access_manager.db
but uses the access_manager database (the same one as the web admin).
"""
import os
import sys

# Add parent directory to path to import access_manager
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from flask import Flask
from access_manager.models import db
from access_manager.models.user import (
    AdminUser,
    TelegramUser,
    FilePermission,
    UserGlobalAccess,
)

# Re-export for backward compatibility with bot.py imports
__all__ = [
    'AdminUser',
    'TelegramUser',
    'FilePermission',
    'UserGlobalAccess',
    'get_session',
    'init_db',
]


def get_bot_db_path():
    """Get the path to the access_manager database."""
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    return os.path.join(base_dir, 'access_manager', 'instance', 'access_manager.db')


def create_bot_app():
    """Create a minimal Flask app for the bot to use access_manager database."""
    app = Flask(__name__)
    
    # Load .env from parent directory
    env_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), '.env')
    from dotenv import load_dotenv
    load_dotenv(env_path)
    
    # Use the same database as access_manager (with correct path)
    db_path = get_bot_db_path()
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    return app


def get_session():
    """
    Get a database session from the access_manager database.
    Returns a tuple of (app_context, session).
    Caller is responsible for closing the session and popping the context.
    """
    app = create_bot_app()
    ctx = app.app_context()
    ctx.push()
    return ctx, db.session


def init_db():
    """
    Initialize database tables.
    """
    app = create_bot_app()
    with app.app_context():
        db.create_all()
