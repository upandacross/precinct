"""
Flask application configuration settings.
"""

import os
from datetime import timedelta


class Config:
    """Base configuration class."""
    
    # Basic Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY') or os.urandom(32).hex()  # Fallback to random key

    # Database Configuration - Only PostgreSQL NC database on hosting platform
    # Build PostgreSQL URI from environment variables
    POSTGRES_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
    POSTGRES_PORT = os.environ.get('POSTGRES_PORT', '4747')  # Updated to match .env default
    POSTGRES_USER = os.environ.get('POSTGRES_USER', 'precinct')
    POSTGRES_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'bren123')
    POSTGRES_DB = os.environ.get('POSTGRES_DB', 'nc')
    
    # Construct database URI from components or use full URI if provided
    SQLALCHEMY_DATABASE_URI = os.environ.get('NC_DATABASE_URL') or \
        f'postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}'
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Security Configuration
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens
    
    # Session Configuration
    PERMANENT_SESSION_LIFETIME = timedelta(hours=4)  # 4 hour sessions
    SESSION_TIMEOUT_MINUTES = 30  # Session timeout after 30 minutes of inactivity
    SESSION_WARNING_MINUTES = 5   # Warn user 5 minutes before timeout
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Flask-Login Configuration
    REMEMBER_COOKIE_DURATION = timedelta(days=7)  # Remember me for 7 days
    REMEMBER_COOKIE_SECURE = os.environ.get('REMEMBER_COOKIE_SECURE', 'False').lower() == 'true'
    REMEMBER_COOKIE_HTTPONLY = True
    
    # Flask-Admin Configuration
    FLASK_ADMIN_SWATCH = 'cerulean'  # Bootstrap theme for admin
    
    # Application Specific Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file upload
    
    # Default Admin User Configuration
    DEFAULT_ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    DEFAULT_ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'brenvoice@gmail.com')
    DEFAULT_ADMIN_PASSWORD = os.environ.get('SECRET', '!1OkslCZtBBPCHRG!')  # Use SECRET env var
    
    # Rate Limiting Configuration
    RATELIMIT_STORAGE_URL = "memory://"  # Use in-memory storage for rate limiting
    RATELIMIT_DEFAULT = "200 per day, 50 per hour"  # Default rate limits
    
    # PostgreSQL is the only database on hosting platform
    RATELIMIT_HEADERS_ENABLED = True  # Include rate limit headers in responses
    
class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    TESTING = False
    
    # Development uses NC PostgreSQL database (inherits from base Config class)
    # SQLALCHEMY_DATABASE_URI is inherited from Config class
    
    # Less secure cookies for development
    SESSION_COOKIE_SECURE = False
    REMEMBER_COOKIE_SECURE = False
    FLASK_PORT = int(os.environ.get('FLASK_PORT', 5000))

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    TESTING = False
    
    # Production uses NC PostgreSQL database (inherits from base Config class)
    # Override only if DATABASE_URL is explicitly set (for hosting platforms like Heroku)
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    # Otherwise inherits from base Config class with .env variables

    # Secure cookies for production
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    FLASK_PORT = 8080
    
    # Production security settings
    WTF_CSRF_SSL_STRICT = True
    
    # Stricter session timeouts for production
    SESSION_TIMEOUT_MINUTES = 15  # 15 minutes for production
    SESSION_WARNING_MINUTES = 2   # 2 minutes warning
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)  # Shorter max session
    
    # Stricter rate limits for production
    RATELIMIT_DEFAULT = "100 per day, 20 per hour"  # Stricter than development


class TestingConfig(Config):
    """Testing configuration."""
    DEBUG = True
    TESTING = True
    
    # In-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    
    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False
    
    # Disable rate limiting for testing
    RATELIMIT_ENABLED = False
    RATELIMIT_DEFAULT = "100000 per minute"  # Effectively unlimited for tests
    
    # Shorter session times for testing
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=5)


# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
CONFIG_KEY = os.environ.get('FLASK_ENV', 'default').lower()

def get_config():
    """Get configuration class based on environment."""
    env = os.environ.get('FLASK_ENV', 'production').lower()
    return config.get(env, config['default'])
