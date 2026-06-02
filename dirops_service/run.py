"""Run the dirops_service Flask application."""
import os
from dirops_service.database import create_app
from dirops_service.config import get_config

if __name__ == '__main__':
    config = get_config()
    app = create_app(config)
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 5001)), debug=config.DEBUG)
