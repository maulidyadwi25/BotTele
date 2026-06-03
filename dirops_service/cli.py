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


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Database management CLI')
    parser.add_argument('command', choices=['init', 'drop', 'reset'],
                        help='Command to run')

    args = parser.parse_args()

    if args.command == 'init':
        init_db()
    elif args.command == 'drop':
        drop_db()
    elif args.command == 'reset':
        reset_db()
