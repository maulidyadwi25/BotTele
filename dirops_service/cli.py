import os
import sys
import argparse

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dirops_service.database import create_app
from dirops_service.models import db
from dirops_service.config import get_config


def init_db():
    """Initialize database, create all tables."""
    app = create_app()
    with app.app_context():
        db.create_all()
        print("Database tables created successfully.")


def drop_db():
    """Drop all database tables."""
    app = create_app()
    with app.app_context():
        db.drop_all()
        print("Database tables dropped successfully.")


def reset_db():
    """Reset database - drop and recreate all tables."""
    app = create_app()
    with app.app_context():
        db.drop_all()
        db.create_all()
        print("Database reset successfully.")


def run_migrations():
    """Run Alembic migrations."""
    import subprocess
    result = subprocess.run(['alembic', 'upgrade', 'head'], cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.exit(result.returncode)


def create_migration(message):
    """Create a new Alembic migration."""
    import subprocess
    result = subprocess.run(['alembic', 'revision', '--message', message], cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    sys.exit(result.returncode)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Database management CLI')
    parser.add_argument('command', choices=['init', 'drop', 'reset', 'migrate', 'migration'],
                        help='Command to run')
    parser.add_argument('-m', '--message', help='Migration message (for create migration)')

    args = parser.parse_args()

    if args.command == 'init':
        init_db()
    elif args.command == 'drop':
        drop_db()
    elif args.command == 'reset':
        reset_db()
    elif args.command == 'migrate':
        run_migrations()
    elif args.command == 'migration':
        if not args.message:
            print("Error: -m/--message is required for creating a migration")
            sys.exit(1)
        create_migration(args.message)
