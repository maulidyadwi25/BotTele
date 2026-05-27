"""Permission service for managing file access."""
from datetime import datetime
from models import db
from models.user import TelegramUser, FilePermission, UserGlobalAccess


class PermissionService:
    """Service for managing Telegram user permissions."""

    def get_all_users(self):
        """Get all Telegram users."""
        users = TelegramUser.query.all()
        return [user.to_dict() for user in users]

    def get_user(self, user_id):
        """Get a specific user by ID."""
        user = TelegramUser.query.get(user_id)
        return user.to_dict() if user else None

    def create_user(self, telegram_id, username=None, display_name=None):
        """Create a new Telegram user."""
        # Check if user already exists
        existing = TelegramUser.query.filter_by(telegram_id=str(telegram_id)).first()
        if existing:
            return {'success': False, 'error': 'User with this Telegram ID already exists'}

        try:
            user = TelegramUser(
                telegram_id=str(telegram_id),
                username=username,
                display_name=display_name or username
            )
            db.session.add(user)
            db.session.flush()

            # Create global access record
            global_access = UserGlobalAccess(
                telegram_user_id=user.id,
                has_global_access=False,
                access_level='file_specific'
            )
            db.session.add(global_access)
            db.session.commit()

            return {'success': True, 'data': user.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def update_user(self, user_id, data):
        """Update a Telegram user."""
        user = TelegramUser.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}

        try:
            if 'username' in data:
                user.username = data['username']
            if 'display_name' in data:
                user.display_name = data['display_name']
            if 'status' in data:
                user.status = data['status']

            db.session.commit()
            return {'success': True, 'data': user.to_dict()}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def delete_user(self, user_id):
        """Delete a Telegram user."""
        user = TelegramUser.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}

        try:
            # Delete related records
            FilePermission.query.filter_by(telegram_user_id=user_id).delete()
            UserGlobalAccess.query.filter_by(telegram_user_id=user_id).delete()
            db.session.delete(user)
            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def toggle_global_access(self, user_id):
        """Toggle global access for a user."""
        user = TelegramUser.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}

        try:
            global_access = UserGlobalAccess.query.filter_by(telegram_user_id=user_id).first()
            if not global_access:
                global_access = UserGlobalAccess(
                    telegram_user_id=user_id,
                    has_global_access=True,
                    access_level='global'
                )
                db.session.add(global_access)
            else:
                global_access.has_global_access = not global_access.has_global_access
                global_access.access_level = 'global' if global_access.has_global_access else 'file_specific'

            db.session.commit()
            return {'success': True, 'has_global_access': global_access.has_global_access}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def toggle_user_status(self, user_id):
        """Toggle user status between active and suspended."""
        user = TelegramUser.query.get(user_id)
        if not user:
            return {'success': False, 'error': 'User not found'}

        try:
            user.status = 'suspended' if user.status == 'active' else 'active'
            db.session.commit()
            return {'success': True, 'status': user.status}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def has_global_access(self, telegram_id):
        """Check if a user has global access."""
        user = TelegramUser.query.filter_by(telegram_id=str(telegram_id)).first()
        if not user or user.status != 'active':
            return False

        global_access = UserGlobalAccess.query.filter_by(telegram_user_id=user.id).first()
        return global_access.has_global_access if global_access else False

    def has_file_permission(self, telegram_id, file_id):
        """Check if a user has permission for a specific file."""
        user = TelegramUser.query.filter_by(telegram_id=str(telegram_id)).first()
        if not user or user.status != 'active':
            return False

        # Check global access first
        if self.has_global_access(telegram_id):
            return True

        # Check file-specific permission
        permission = FilePermission.query.filter_by(
            telegram_user_id=user.id,
            file_id=file_id
        ).first()

        return permission is not None

    def get_file_permissions(self, file_id):
        """Get all permissions for a file."""
        permissions = FilePermission.query.filter_by(file_id=file_id).all()
        return [p.to_dict() for p in permissions]

    def get_user_permissions(self, user_id):
        """Get all file permissions for a user."""
        permissions = FilePermission.query.filter_by(telegram_user_id=user_id).all()
        return [p.to_dict() for p in permissions]

    def update_file_permissions(self, file_id, file_name, permissions_list, admin_id=None):
        """Update permissions for a file."""
        try:
            # Get existing permissions
            existing = {p.telegram_user_id: p for p in FilePermission.query.filter_by(file_id=file_id).all()}

            for perm_data in permissions_list:
                user_id = perm_data.get('user_id')
                level = perm_data.get('level', 'read')
                granted = perm_data.get('granted', False)

                if user_id in existing:
                    if granted:
                        existing[user_id].permission_level = level
                    else:
                        db.session.delete(existing[user_id])
                    del existing[user_id]
                elif granted:
                    permission = FilePermission(
                        file_id=file_id,
                        file_name=file_name,
                        telegram_user_id=user_id,
                        permission_level=level,
                        granted_by=admin_id
                    )
                    db.session.add(permission)

            # Delete remaining old permissions that weren't updated
            for old_perm in existing.values():
                db.session.delete(old_perm)

            db.session.commit()
            return {'success': True}
        except Exception as e:
            db.session.rollback()
            return {'success': False, 'error': str(e)}

    def bulk_update_permissions(self, updates, admin_id=None):
        """Bulk update permissions for multiple files."""
        try:
            for update in updates:
                file_id = update.get('file_id')
                file_name = update.get('file_name', 'Unknown')
                permissions_list = update.get('permissions', [])
                self.update_file_permissions(file_id, file_name, permissions_list, admin_id)
            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_user_stats(self):
        """Get user statistics."""
        total = TelegramUser.query.count()
        active = TelegramUser.query.filter_by(status='active').count()
        suspended = TelegramUser.query.filter_by(status='suspended').count()

        global_access_count = db.session.query(UserGlobalAccess).filter_by(has_global_access=True).count()

        return {
            'total': total,
            'active': active,
            'suspended': suspended,
            'global_access': global_access_count
        }

    def get_dashboard_stats(self):
        """Get dashboard statistics."""
        stats = self.get_user_stats()
        stats['total_files'] = db.session.query(FilePermission).distinct(FilePermission.file_id).count()
        stats['total_permissions'] = FilePermission.query.count()
        return stats

    def get_recent_activity(self, limit=5):
        """Get recent permission changes."""
        permissions = FilePermission.query.order_by(FilePermission.granted_at.desc()).limit(limit).all()
        return [p.to_dict() for p in permissions]
