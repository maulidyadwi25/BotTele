"""
Permission service for bot.py
Standalone version that works outside Flask context
"""
from datetime import datetime
from access_manager.models.bot_db import TelegramUser, FilePermission, UserGlobalAccess, get_session


class BotPermissionService:
    """Permission service for Telegram bot."""

    def has_global_access(self, telegram_id):
        """Check if a user has global access."""
        session = get_session()
        try:
            user = session.query(TelegramUser).filter_by(telegram_id=str(telegram_id)).first()
            if not user or user.status != 'active':
                return False
            global_access = session.query(UserGlobalAccess).filter_by(telegram_user_id=user.id).first()
            return global_access.has_global_access if global_access else False
        finally:
            session.close()

    def has_file_permission(self, telegram_id, file_id):
        """Check if a user has permission for a specific file."""
        session = get_session()
        try:
            user = session.query(TelegramUser).filter_by(telegram_id=str(telegram_id)).first()
            
            print(f"[DEBUG] has_file_permission - telegram_id: {telegram_id}")
            print(f"[DEBUG] has_file_permission - file_id: {file_id}")
            print(f"[DEBUG] has_file_permission - user found: {user}")
            
            if not user:
                print(f"[DEBUG] has_file_permission - NO USER FOUND")
                return False
            if user.status != 'active':
                print(f"[DEBUG] has_file_permission - user status: {user.status}")
                return False

            print(f"[DEBUG] has_file_permission - user.id: {user.id}")

            # Check global access first
            if self.has_global_access(telegram_id):
                print(f"[DEBUG] has_file_permission - user has GLOBAL access")
                return True

            # Check file-specific permission
            print(f"[DEBUG] has_file_permission - checking FilePermission table for user.id={user.id}, file_id={file_id}")
            permission = session.query(FilePermission).filter_by(
                telegram_user_id=user.id,
                file_id=file_id
            ).first()

            print(f"[DEBUG] has_file_permission - permission found: {permission}")
            return permission is not None
        finally:
            session.close()

    def create_user(self, telegram_id, username=None, display_name=None):
        """Create a new Telegram user."""
        session = get_session()
        try:
            # Check if user already exists
            existing = session.query(TelegramUser).filter_by(telegram_id=str(telegram_id)).first()
            if existing:
                return {'success': True, 'data': existing}

            user = TelegramUser(
                telegram_id=str(telegram_id),
                username=username,
                display_name=display_name or username
            )
            session.add(user)
            session.flush()

            # Create global access record
            global_access = UserGlobalAccess(
                telegram_user_id=user.id,
                has_global_access=False,
                access_level='file_specific'
            )
            session.add(global_access)
            session.commit()

            return {'success': True, 'data': user}
        except Exception as e:
            session.rollback()
            return {'success': False, 'error': str(e)}
        finally:
            session.close()
