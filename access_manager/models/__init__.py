from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import AdminUser, TelegramUser, FilePermission, UserGlobalAccess

__all__ = ['db', 'AdminUser', 'TelegramUser', 'FilePermission', 'UserGlobalAccess']
