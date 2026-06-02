import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent


class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', None)
    SQLALCHEMY_ENGINE_OPTIONS = os.getenv('SQLALCHEMY_ENGINE_OPTIONS', None)

    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
    DB_NAME = os.getenv('DB_NAME', 'dirops.db')

    if not SQLALCHEMY_DATABASE_URI:
        if DB_TYPE == 'sqlite':
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{BASE_DIR / DB_NAME}'
        elif DB_TYPE == 'postgresql':
            DB_HOST = os.getenv('DB_HOST', 'localhost')
            DB_PORT = os.getenv('DB_PORT', '5432')
            DB_NAME = os.getenv('DB_NAME', 'dirops')
            DB_USER = os.getenv('DB_USER', 'postgres')
            DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')
            SQLALCHEMY_DATABASE_URI = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'
        elif DB_TYPE == 'mysql':
            DB_HOST = os.getenv('DB_HOST', 'localhost')
            DB_PORT = os.getenv('DB_PORT', '3306')
            DB_NAME = os.getenv('DB_NAME', 'dirops')
            DB_USER = os.getenv('DB_USER', 'root')
            DB_PASSWORD = os.getenv('DB_PASSWORD', 'root')
            SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'

    if SQLALCHEMY_ENGINE_OPTIONS:
        import json
        SQLALCHEMY_ENGINE_OPTIONS = json.loads(SQLALCHEMY_ENGINE_OPTIONS)


class DevelopmentConfig(Config):
    DEBUG = True
    DB_TYPE = os.getenv('DB_TYPE', 'sqlite')
    DB_NAME = os.getenv('DB_NAME', 'dirops_dev.db')
    if not Config.SQLALCHEMY_DATABASE_URI:
        if DB_TYPE == 'sqlite':
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{BASE_DIR / DB_NAME}'


class ProductionConfig(Config):
    DEBUG = False
    DB_TYPE = os.getenv('DB_TYPE', 'postgresql')


class TestConfig(Config):
    TESTING = True
    DB_TYPE = 'sqlite'
    DB_NAME = 'dirops_test.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{BASE_DIR / DB_NAME}'


config_by_name = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'test': TestConfig,
    'default': DevelopmentConfig
}


def get_config():
    env = os.getenv('FLASK_ENV', 'development')
    return config_by_name.get(env, DevelopmentConfig)
