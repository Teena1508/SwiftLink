import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-url-shortener-2026')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///url_shortener.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    PORT = int(os.environ.get('PORT', 5001))
    BASE_URL = os.environ.get('BASE_URL', f'http://127.0.0.1:{PORT}')
    RATE_LIMIT_PER_MINUTE = int(os.environ.get('RATE_LIMIT_PER_MINUTE', 10))
    DEFAULT_SHORT_CODE_LENGTH = 6
    MAX_CUSTOM_ALIAS_LENGTH = 30
    MIN_CUSTOM_ALIAS_LENGTH = 3

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    RATE_LIMIT_PER_MINUTE = 5
