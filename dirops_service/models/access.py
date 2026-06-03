"""
Access management models for bot/telegram user permissions.
These models were migrated from access_manager.db to consolidate
all databases into dirops.
"""
import json
import hashlib
from datetime import datetime
from . import db


class AdminUser(db.Model):
    """Admin user for web dashboard authentication."""
    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship to permissions granted
    granted_permissions = db.relationship('FilePermission', backref='granter', lazy='dynamic')

    def set_password(self, password: str):
        """Hash and set the password."""
        self.password_hash = hashlib.sha256(password.encode()).hexdigest()

    def check_password(self, password: str) -> bool:
        """Verify password against stored hash."""
        return self.password_hash == hashlib.sha256(password.encode()).hexdigest()


class TelegramUser(db.Model):
    """Telegram user with file access permissions."""
    __tablename__ = 'telegram_users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    telegram_id = db.Column(db.String(50), nullable=True)  # Can be null if only username
    username = db.Column(db.String(100), unique=True, nullable=True)  # Unique identifier
    display_name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    permissions = db.relationship('FilePermission', backref='telegram_user', lazy='dynamic')
    global_access = db.relationship('UserGlobalAccess', backref='telegram_user', uselist=False)


class FilePermission(db.Model):
    """File-specific permissions for telegram users."""
    __tablename__ = 'file_permissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_id = db.Column(db.String(100), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    telegram_user_id = db.Column(db.Integer, db.ForeignKey('telegram_users.id'), nullable=False)
    permission_level = db.Column(db.String(20), default='read')  # read, write, admin
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)


class UserGlobalAccess(db.Model):
    """Global access level for telegram users (bypass file-specific permissions)."""
    __tablename__ = 'user_global_access'

    telegram_user_id = db.Column(db.Integer, db.ForeignKey('telegram_users.id'), primary_key=True)
    has_global_access = db.Column(db.Boolean, default=False)
    access_level = db.Column(db.String(20), default='restricted')  # restricted, read, write, admin


class SpreadsheetIndex(db.Model):
    """
    Stores spreadsheet file/sheet metadata to avoid repeated Google API calls.
    Index is updated when Drive's modifiedTime changes.
    """
    __tablename__ = 'spreadsheet_index'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    file_name = db.Column(db.String(255), nullable=False)
    folder_id = db.Column(db.String(100), nullable=True, index=True)
    folder_path = db.Column(db.String(500), nullable=True)
    sheet_names = db.Column(db.Text, nullable=True)  # JSON array of sheet names
    last_modified = db.Column(db.String(50), nullable=True)  # Drive modifiedTime
    last_indexed = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)

    def get_sheet_list(self):
        """Return sheet names as a Python list."""
        if self.sheet_names:
            return json.loads(self.sheet_names)
        return []

    def set_sheet_list(self, sheet_list):
        """Store sheet names as JSON."""
        self.sheet_names = json.dumps(sheet_list)


# Aliases for backward compatibility with bot_db.py imports
TelegramUserAlias = TelegramUser
FilePermissionAlias = FilePermission
UserGlobalAccessAlias = UserGlobalAccess
SpreadsheetIndexAlias = SpreadsheetIndex


__all__ = [
    'AdminUser',
    'TelegramUser',
    'FilePermission',
    'UserGlobalAccess',
    'SpreadsheetIndex',
]
