"""
Permission service for bot.py
Standalone version that works outside Flask context
"""
from datetime import datetime
from access_manager.models.bot_db import TelegramUser, FilePermission, UserGlobalAccess, get_session


class BotPermissionService:
    """Permission service for Telegram bot."""

    def _get_user_by_id_or_username(self, session, identifier):
        """Get user by telegram_id or username.
        
        Args:
            session: Database session
            identifier: Can be telegram_id (numeric string) or username (with or without @)
        
        Returns:
            TelegramUser or None
        """
        if not identifier:
            return None
        
        # Clean up identifier
        identifier = identifier.strip().lstrip('@')
        
        # Check if it looks like a numeric ID
        if identifier.isdigit():
            user = session.query(TelegramUser).filter_by(telegram_id=identifier).first()
            # If not found by ID but user has a username in their telegram profile,
            # try to find by username (handles case where user was registered with username only)
            if not user:
                user = session.query(TelegramUser).filter_by(username=identifier).first()
        else:
            # It's a username - search by username
            user = session.query(TelegramUser).filter_by(username=identifier).first()
        
        return user

    def _get_user_by_telegram_id_with_username_fallback(self, session, telegram_id, username=None):
        """Get user by telegram_id, with fallback to username lookup.
        
        This handles the case where a user was registered with username only,
        but when they interact with the bot, we get their actual telegram_id.
        
        Args:
            session: Database session
            telegram_id: User's Telegram ID
            username: User's Telegram username (optional)
        
        Returns:
            TelegramUser or None
        """
        if not telegram_id:
            return None
        
        # First try to find by telegram_id
        user = session.query(TelegramUser).filter_by(telegram_id=str(telegram_id)).first()
        
        # If not found and we have a username, try to find by username
        # This handles users registered with username only
        if not user and username:
            username_clean = username.strip().lstrip('@')
            user = session.query(TelegramUser).filter_by(username=username_clean).first()
        
        return user

    def has_global_access(self, telegram_id, username=None):
        """Check if a user has global access.
        
        Args:
            telegram_id: User's Telegram ID (string)
            username: User's Telegram username (optional, for fallback lookup)
        """
        session = get_session()
        try:
            user = self._get_user_by_telegram_id_with_username_fallback(session, telegram_id, username)
            if not user or user.status != 'active':
                return False
            global_access = session.query(UserGlobalAccess).filter_by(telegram_user_id=user.id).first()
            return global_access.has_global_access if global_access else False
        finally:
            session.close()

    def has_file_permission(self, telegram_id, file_id, username=None):
        """Check if a user has permission for a specific file.
        
        Args:
            telegram_id: User's Telegram ID (string)
            file_id: File/folder ID to check permission for
            username: User's Telegram username (optional, for fallback lookup)
        """
        session = get_session()
        try:
            user = self._get_user_by_telegram_id_with_username_fallback(session, telegram_id, username)
            
            print(f"[DEBUG] has_file_permission - telegram_id: {telegram_id}, username: {username}")
            print(f"[DEBUG] has_file_permission - file_id: {file_id}")
            print(f"[DEBUG] has_file_permission - user found: {user}")
            
            if not user:
                print(f"[DEBUG] has_file_permission - NO USER FOUND")
                return False
            if user.status != 'active':
                print(f"[DEBUG] has_file_permission - user status: {user.status}")
                return False

            print(f"[DEBUG] has_file_permission - user.id: {user.id}")

            # Check global access first (pass username for fallback)
            if self.has_global_access(telegram_id, username):
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

    def create_user(self, telegram_id=None, username=None, display_name=None):
        """Create a new Telegram user.
        
        Either telegram_id OR username must be provided.
        """
        session = get_session()
        try:
            # Check if user already exists by telegram_id
            if telegram_id:
                existing = session.query(TelegramUser).filter_by(telegram_id=str(telegram_id)).first()
                if existing:
                    return {'success': True, 'data': existing}
            
            # Check if user already exists by username
            if username:
                username_clean = username.strip().lstrip('@')
                existing = session.query(TelegramUser).filter_by(username=username_clean).first()
                if existing:
                    return {'success': True, 'data': existing}

            user = TelegramUser(
                telegram_id=str(telegram_id) if telegram_id else None,
                username=username.strip().lstrip('@') if username else None,
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
