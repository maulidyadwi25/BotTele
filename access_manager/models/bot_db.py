"""
Database connection for bot.py using the dirops database.
This module provides the same interface as the original access_manager.db
but uses the consolidated dirops database instead.
"""
import os
import sys

# Add parent directory to path to import dirops_service
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from dirops_service.database import db
from dirops_service.models import (
    AdminUser,
    TelegramUser,
    FilePermission,
    UserGlobalAccess,
    SpreadsheetIndex,
)

# Re-export for backward compatibility with bot.py imports
__all__ = [
    'AdminUser',
    'TelegramUser',
    'FilePermission',
    'UserGlobalAccess',
    'SpreadsheetIndex',
    'get_session',
    'init_db',
]


def get_session():
    """
    Get a database session from the dirops database.
    Returns a new session - caller is responsible for closing it.
    """
    from dirops_service.database import create_app
    app = create_app()
    return app.app_context().db.session


def init_db():
    """
    Initialize database tables.
    For dirops database, tables are created via Flask-SQLAlchemy's db.create_all()
    which is called in create_app().
    """
    from dirops_service.database import create_app
    app = create_app()
    with app.app_context():
        db.create_all()
