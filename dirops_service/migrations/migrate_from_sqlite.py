"""
Migration script to transfer data from old SQLite databases to dirops.

This script migrates:
- access_manager.db (SQLite) → dirops database

Usage:
    python -m dirops_service.migrations.migrate_from_sqlite

Before running:
1. Backup both databases
2. Ensure dirops database is created and accessible
3. Set environment variables for target database
"""
import os
import sys
import json
import argparse

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Load environment
load_dotenv()


def get_source_engine(db_path):
    """Create engine for source SQLite database."""
    if not os.path.exists(db_path):
        print(f"[ERROR] Source database not found: {db_path}")
        return None
    return create_engine(f'sqlite:///{os.path.abspath(db_path)}')


def get_target_engine():
    """Create engine for target dirops database using dirops config."""
    from dirops_service.config import get_config
    config = get_config()
    return create_engine(config.SQLALCHEMY_DATABASE_URI)


def migrate_admin_users(source_session, target_session):
    """Migrate admin_users table."""
    print("\n[1/5] Migrating admin_users...")
    from access_manager.models.bot_db import AdminUser as SourceAdminUser
    
    source_users = source_session.query(SourceAdminUser).all()
    from dirops_service.models import AdminUser
    
    migrated = 0
    for user in source_users:
        existing = target_session.query(AdminUser).filter_by(username=user.username).first()
        if not existing:
            new_user = AdminUser(
                username=user.username,
                password_hash=user.password_hash,
                created_at=user.created_at
            )
            target_session.add(new_user)
            migrated += 1
    
    target_session.commit()
    print(f"   → Migrated {migrated} admin users")
    return migrated


def migrate_telegram_users(source_session, target_session):
    """Migrate telegram_users table."""
    print("\n[2/5] Migrating telegram_users...")
    from access_manager.models.bot_db import TelegramUser as SourceTelegramUser
    
    source_users = source_session.query(SourceTelegramUser).all()
    from dirops_service.models import TelegramUser
    
    migrated = 0
    for user in source_users:
        # Check by telegram_id or username
        existing = target_session.query(TelegramUser).filter(
            (TelegramUser.telegram_id == user.telegram_id) |
            (TelegramUser.username == user.username)
        ).first()
        
        if not existing:
            new_user = TelegramUser(
                telegram_id=user.telegram_id,
                username=user.username,
                display_name=user.display_name,
                status=user.status,
                created_at=user.created_at
            )
            target_session.add(new_user)
            migrated += 1
    
    target_session.commit()
    print(f"   → Migrated {migrated} telegram users")
    return migrated


def migrate_file_permissions(source_session, target_session):
    """Migrate file_permissions table."""
    print("\n[3/5] Migrating file_permissions...")
    from access_manager.models.bot_db import FilePermission as SourceFilePermission
    
    source_perms = source_session.query(SourceFilePermission).all()
    from dirops_service.models import FilePermission, TelegramUser
    
    migrated = 0
    for perm in source_perms:
        # Find the telegram user by username or telegram_id
        telegram_user = target_session.query(TelegramUser).filter(
            (TelegramUser.telegram_id == perm.telegram_user.telegram_id) |
            (TelegramUser.username == perm.telegram_user.username)
        ).first()
        
        if telegram_user:
            # Check if permission already exists
            existing = target_session.query(FilePermission).filter_by(
                file_id=perm.file_id,
                telegram_user_id=telegram_user.id
            ).first()
            
            if not existing:
                new_perm = FilePermission(
                    file_id=perm.file_id,
                    file_name=perm.file_name,
                    telegram_user_id=telegram_user.id,
                    permission_level=perm.permission_level,
                    granted_at=perm.granted_at,
                    granted_by=perm.granted_by
                )
                target_session.add(new_perm)
                migrated += 1
    
    target_session.commit()
    print(f"   → Migrated {migrated} file permissions")
    return migrated


def migrate_user_global_access(source_session, target_session):
    """Migrate user_global_access table."""
    print("\n[4/5] Migrating user_global_access...")
    from access_manager.models.bot_db import UserGlobalAccess as SourceGlobalAccess
    
    source_access = source_session.query(SourceGlobalAccess).all()
    from dirops_service.models import UserGlobalAccess, TelegramUser
    
    migrated = 0
    for access in source_access:
        # Find the telegram user
        telegram_user = target_session.query(TelegramUser).filter(
            (TelegramUser.telegram_id == access.telegram_user.telegram_id) |
            (TelegramUser.username == access.telegram_user.username)
        ).first()
        
        if telegram_user:
            # Check if already exists
            existing = target_session.query(UserGlobalAccess).filter_by(
                telegram_user_id=telegram_user.id
            ).first()
            
            if not existing:
                new_access = UserGlobalAccess(
                    telegram_user_id=telegram_user.id,
                    has_global_access=access.has_global_access,
                    access_level=access.access_level
                )
                target_session.add(new_access)
                migrated += 1
    
    target_session.commit()
    print(f"   → Migrated {migrated} global access records")
    return migrated


def migrate_spreadsheet_index(source_session, target_session):
    """Migrate spreadsheet_index table."""
    print("\n[5/5] Migrating spreadsheet_index...")
    from access_manager.models.bot_db import SpreadsheetIndex as SourceIndex
    
    source_indexes = source_session.query(SourceIndex).all()
    from dirops_service.models import SpreadsheetIndex
    
    migrated = 0
    for idx in source_indexes:
        existing = target_session.query(SpreadsheetIndex).filter_by(
            file_id=idx.file_id
        ).first()
        
        if not existing:
            new_idx = SpreadsheetIndex(
                file_id=idx.file_id,
                file_name=idx.file_name,
                folder_id=idx.folder_id,
                folder_path=idx.folder_path,
                sheet_names=idx.sheet_names,
                last_modified=idx.last_modified,
                last_indexed=idx.last_indexed,
                is_active=idx.is_active
            )
            target_session.add(new_idx)
            migrated += 1
    
    target_session.commit()
    print(f"   → Migrated {migrated} spreadsheet indexes")
    return migrated


def run_migration(access_manager_db_path):
    """Run the complete migration."""
    print("=" * 60)
    print("MIGRATION: access_manager.db → dirops database")
    print("=" * 60)
    
    # Source engine (old SQLite)
    source_engine = get_source_engine(access_manager_db_path)
    if not source_engine:
        print("\n[ERROR] Cannot proceed without source database")
        return False
    
    # Target engine (dirops)
    target_engine = get_target_engine()
    
    SourceSession = sessionmaker(bind=source_engine)
    TargetSession = sessionmaker(bind=target_engine)
    
    source_session = SourceSession()
    target_session = TargetSession()
    
    try:
        # Check if source tables exist
        inspector = inspect(source_engine)
        tables = inspector.get_table_names()
        print(f"\nSource database tables: {tables}")
        
        # Run migrations
        total = 0
        total += migrate_admin_users(source_session, target_session)
        total += migrate_telegram_users(source_session, target_session)
        total += migrate_file_permissions(source_session, target_session)
        total += migrate_user_global_access(source_session, target_session)
        total += migrate_spreadsheet_index(source_session, target_session)
        
        print("\n" + "=" * 60)
        print(f"MIGRATION COMPLETE: {total} total records migrated")
        print("=" * 60)
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Migration failed: {e}")
        target_session.rollback()
        return False
    finally:
        source_session.close()
        target_session.close()


def main():
    parser = argparse.ArgumentParser(description='Migrate data from access_manager.db to dirops')
    parser.add_argument('--db-path', '-d', 
                        default='access_manager/instance/access_manager.db',
                        help='Path to access_manager.db (default: access_manager/instance/access_manager.db)')
    parser.add_argument('--dry-run', '-n', action='store_true',
                        help='Show what would be migrated without making changes')
    
    args = parser.parse_args()
    
    if args.dry_run:
        print("[DRY RUN MODE - No changes will be made]")
    
    success = run_migration(args.db_path)
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
