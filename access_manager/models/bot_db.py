"""
Standalone database connection for bot.py
Uses SQLAlchemy directly without Flask-SQLAlchemy
"""
import os
import json
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

# Get database path - use instance folder like Flask does
# Flask's sqlite:///access_manager.db creates db in instance/ folder when running from access_manager/
# bot_db.py is in access_manager/models/, so we go up one level then to instance
db_path = os.path.join(os.path.dirname(__file__), '..', 'instance', 'access_manager.db')
db_path = os.path.abspath(db_path)
print(f"[DEBUG] bot_db.py using database path: {db_path}")
engine = create_engine(f'sqlite:///{db_path}', connect_args={"check_same_thread": False})
Session = sessionmaker(bind=engine)
Base = declarative_base()


class AdminUser(Base):
    __tablename__ = 'admin_users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class TelegramUser(Base):
    __tablename__ = 'telegram_users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(String(50), nullable=True)  # Can be null if username is provided
    username = Column(String(100), unique=True, nullable=True)  # Unique to identify by username
    display_name = Column(String(100), nullable=True)
    status = Column(String(20), default='active')
    created_at = Column(DateTime, default=datetime.utcnow)
    permissions = relationship('FilePermission', backref='telegram_user', lazy='dynamic')
    global_access = relationship('UserGlobalAccess', backref='telegram_user', uselist=False)


class FilePermission(Base):
    __tablename__ = 'file_permissions'
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String(100), nullable=False)
    file_name = Column(String(255), nullable=False)
    telegram_user_id = Column(Integer, ForeignKey('telegram_users.id'), nullable=False)
    permission_level = Column(String(20), default='read')
    granted_at = Column(DateTime, default=datetime.utcnow)
    granted_by = Column(Integer, ForeignKey('admin_users.id'), nullable=True)


class UserGlobalAccess(Base):
    __tablename__ = 'user_global_access'
    telegram_user_id = Column(Integer, ForeignKey('telegram_users.id'), primary_key=True)
    has_global_access = Column(Boolean, default=False)
    access_level = Column(String(20), default='restricted')


class SpreadsheetIndex(Base):
    """Stores spreadsheet file/sheet metadata to avoid repeated API calls"""
    __tablename__ = 'spreadsheet_index'
    id = Column(Integer, primary_key=True, autoincrement=True)
    file_id = Column(String(100), unique=True, nullable=False, index=True)
    file_name = Column(String(255), nullable=False)
    folder_id = Column(String(100), nullable=True, index=True)
    folder_path = Column(String(500), nullable=True)
    sheet_names = Column(Text, nullable=True)  # JSON array of sheet names
    last_modified = Column(String(50), nullable=True)  # Drive modifiedTime
    last_indexed = Column(DateTime, default=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    def get_sheet_list(self):
        """Return sheet names as a Python list"""
        if self.sheet_names:
            return json.loads(self.sheet_names)
        return []
    
    def set_sheet_list(self, sheet_list):
        """Store sheet names as JSON"""
        self.sheet_names = json.dumps(sheet_list)


def get_session():
    """Get a new database session."""
    return Session()


def init_db():
    """Initialize database tables."""
    Base.metadata.create_all(engine)


# Initialize tables on import
init_db()
