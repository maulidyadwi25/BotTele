from flask import Flask
from .models import db
from .config import get_config
import os


def create_app(config=None):
    """Create and configure the Flask application."""
    app = Flask(__name__)

    if config is None:
        config = get_config()

    app.config.from_object(config)

    db.init_app(app)

    from .routes.health import health_bp
    from .routes.projects import projects_bp
    from .routes.dashboard import dashboard_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(projects_bp)
    app.register_blueprint(dashboard_bp)

    with app.app_context():
        db.create_all()

    return app


def init_db(app=None):
    """Initialize database, create all tables."""
    if app is None:
        app = create_app()

    with app.app_context():
        db.create_all()
    return db
