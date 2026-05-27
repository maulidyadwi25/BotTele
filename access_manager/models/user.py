from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class AdminUser(db.Model):
    """Admin users for the web panel."""
    __tablename__ = 'admin_users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<AdminUser {self.username}>'


class TelegramUser(db.Model):
    """Telegram users who can access files."""
    __tablename__ = 'telegram_users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    telegram_id = db.Column(db.String(50), unique=True, nullable=False)
    username = db.Column(db.String(100), nullable=True)
    display_name = db.Column(db.String(100), nullable=True)
    status = db.Column(db.String(20), default='active')  # active, suspended
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationship
    permissions = db.relationship('FilePermission', backref='telegram_user', lazy='dynamic')
    global_access = db.relationship('UserGlobalAccess', backref='telegram_user', uselist=False)

    def __repr__(self):
        return f'<TelegramUser {self.username or self.telegram_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'display_name': self.display_name,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'has_global_access': self.global_access.has_global_access if self.global_access else False,
            'access_level': self.global_access.access_level if self.global_access else 'restricted'
        }


class FilePermission(db.Model):
    """File-specific permissions for Telegram users."""
    __tablename__ = 'file_permissions'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    file_id = db.Column(db.String(100), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    telegram_user_id = db.Column(db.Integer, db.ForeignKey('telegram_users.id'), nullable=False)
    permission_level = db.Column(db.String(20), default='read')  # read, write, admin
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    granted_by = db.Column(db.Integer, db.ForeignKey('admin_users.id'), nullable=True)

    def __repr__(self):
        return f'<FilePermission {self.file_id} - {self.telegram_user_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'file_id': self.file_id,
            'file_name': self.file_name,
            'telegram_user_id': self.telegram_user_id,
            'permission_level': self.permission_level,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'granted_by': self.granted_by
        }


class UserGlobalAccess(db.Model):
    """Global access settings per Telegram user."""
    __tablename__ = 'user_global_access'

    telegram_user_id = db.Column(db.Integer, db.ForeignKey('telegram_users.id'), primary_key=True)
    has_global_access = db.Column(db.Boolean, default=False)
    access_level = db.Column(db.String(20), default='restricted')  # global, file_specific, restricted

    def __repr__(self):
        return f'<UserGlobalAccess {self.telegram_user_id} - {self.access_level}>'
