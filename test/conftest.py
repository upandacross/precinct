"""
Pytest configuration and shared fixtures for the Precinct application test suite.

This module provides:
- Test application configuration
- Database setup/teardown
- User fixtures for testing
- Test client configuration
"""

import os
import tempfile
import pytest
from datetime import datetime
import sys

# Add the parent directory to Python path so we can import our modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import create_app
from models import db, User, Map


@pytest.fixture(scope='session')
def app():
    """Create application for the tests."""
    # Set environment variable for testing configuration
    os.environ['FLASK_ENV'] = 'testing'
    
    # Create a temporary file for the test database
    db_fd, db_path = tempfile.mkstemp(suffix='.db')
    
    # Test configuration
    test_config = {
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': f'sqlite:///{db_path}',
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,  # Disable CSRF for easier testing
        'SECRET_KEY': 'test-secret-key-not-for-production',
        'SESSION_TIMEOUT_MINUTES': 30,
        'SESSION_WARNING_MINUTES': 5,
        'DEFAULT_ADMIN_USERNAME': 'test_admin',
        'DEFAULT_ADMIN_EMAIL': 'admin@test.com',
        'DEFAULT_ADMIN_PASSWORD': 'test_admin_password_unique',
        'RATELIMIT_STORAGE_URL': 'memory://',
        'RATELIMIT_ENABLED': False,  # Disable rate limiting for tests
        'LOGIN_DISABLED': False,  # We want to test login functionality
    }
    
    # Create the app with test configuration
    app = create_app()
    
    # Override configuration with test settings
    for key, value in test_config.items():
        app.config[key] = value
    
    # Create application context
    with app.app_context():
        # Create all database tables
        db.create_all()
        
        yield app
        
        # Cleanup
        db.drop_all()
        os.close(db_fd)
        os.unlink(db_path)


@pytest.fixture
def client(app):
    """A test client for the app."""
    return app.test_client()


@pytest.fixture
def runner(app):
    """A test runner for the app's Click commands."""
    return app.test_cli_runner()


@pytest.fixture
def db_session(app):
    """Database session for tests."""
    with app.app_context():
        # Clear existing data before each test
        db.session.query(User).delete()
        db.session.query(Map).delete()
        db.session.commit()
        yield db.session
        # Clean up after test
        db.session.query(User).delete() 
        db.session.query(Map).delete()
        db.session.commit()


@pytest.fixture
def admin_user(app, db_session):
    """Create an admin user for testing."""
    with app.app_context():
        user = User(
            username='test_admin',
            email='admin@test.com',
            password='admin_password_unique',
            phone='555-0001',
            role='admin',
            precinct='001',
            state='NC',
            county='Wake',
            is_admin=True,
            is_county=False,
            is_active=True,
            notes='Test admin user'
        )
        db.session.add(user)
        db.session.commit()
        
        # Refresh to get the ID
        db.session.refresh(user)
        return user


@pytest.fixture
def regular_user(app, db_session):
    """Create a regular user for testing."""
    with app.app_context():
        user = User(
            username='test_user',
            email='user@test.com',
            password='user_password_unique',
            phone='555-0002',
            role='voter',
            precinct='012',
            state='NC',
            county='Wake',
            is_admin=False,
            is_county=False,
            is_active=True,
            notes='Test regular user'
        )
        db.session.add(user)
        db.session.commit()
        
        db.session.refresh(user)
        return user


@pytest.fixture
def county_user(app, db_session):
    """Create a county-level user for testing."""
    with app.app_context():
        user = User(
            username='test_county',
            email='county@test.com',
            password='county_password_unique',
            phone='555-0003',
            role='county_admin',
            precinct='000',
            state='NC',
            county='Wake',
            is_admin=False,
            is_county=True,
            is_active=True,
            notes='Test county user'
        )
        db.session.add(user)
        db.session.commit()
        
        db.session.refresh(user)
        return user


@pytest.fixture
def inactive_user(app, db_session):
    """Create an inactive user for testing."""
    with app.app_context():
        user = User(
            username='inactive_user',
            email='inactive@test.com',
            password='inactive_password_unique',
            phone='555-0004',
            role='voter',
            precinct='999',
            state='NC',
            county='Wake',
            is_admin=False,
            is_county=False,
            is_active=False,
            notes='Test inactive user'
        )
        db.session.add(user)
        db.session.commit()
        
        db.session.refresh(user)
        return user


@pytest.fixture
def sample_map(app, db_session, regular_user):
    """Create a sample map for testing."""
    with app.app_context():
        map_content = '''<!DOCTYPE html>
<html>
<head>
    <title>Test Map - Precinct 012</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .map-container { background: #f0f0f0; padding: 20px; border-radius: 5px; }
    </style>
</head>
<body>
    <div class="map-container">
        <h1>Test Precinct Map 012</h1>
        <p>This is a test map for Wake County, Precinct 012.</p>
        <div id="map-placeholder">Interactive map would go here</div>
    </div>
    <script>
        // Mock map initialization
        console.log('Test map loaded for precinct 012');
    </script>
</body>
</html>'''
        
        map_record = Map(
            state='NC',
            county='Wake',
            precinct='012',
            map=map_content,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        db.session.add(map_record)
        db.session.commit()
        
        db.session.refresh(map_record)
        return map_record


@pytest.fixture
def multiple_maps(app, db_session):
    """Create multiple maps for testing county-level access."""
    with app.app_context():
        maps = []
        for precinct_num in ['001', '002', '003', '012']:
            map_content = f'''<!DOCTYPE html>
<html>
<head>
    <title>Test Map - Precinct {precinct_num}</title>
</head>
<body>
    <h1>Test Precinct Map {precinct_num}</h1>
    <p>Wake County, Precinct {precinct_num}</p>
</body>
</html>'''
            
            map_record = Map(
                state='NC',
                county='Wake',
                precinct=precinct_num,
                map=map_content,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.session.add(map_record)
            maps.append(map_record)
        
        db.session.commit()
        
        for map_record in maps:
            db.session.refresh(map_record)
        
        return maps


@pytest.fixture
def authenticated_client(client, regular_user):
    """Provide a client with an authenticated regular user."""
    # Login the user
    response = client.post('/login', data={
        'username': regular_user.username,
        'password': 'user_password_unique',
        'submit': 'Sign In'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    return client


@pytest.fixture
def admin_client(client, admin_user):
    """Provide a client with an authenticated admin user."""
    # Login the admin user
    response = client.post('/login', data={
        'username': admin_user.username,
        'password': 'admin_password_unique',
        'submit': 'Sign In'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    return client


@pytest.fixture
def county_client(client, county_user):
    """Provide a client with an authenticated county user."""
    # Login the county user
    response = client.post('/login', data={
        'username': county_user.username,
        'password': 'county_password_unique',
        'submit': 'Sign In'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    return client


# Helper functions for tests

def login_user(client, username, password):
    """Helper function to login a user."""
    return client.post('/login', data={
        'username': username,
        'password': password,
        'submit': 'Sign In'
    }, follow_redirects=True)


def logout_user(client):
    """Helper function to logout a user."""
    return client.get('/logout', follow_redirects=True)


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "security: marks tests as security-focused"
    )
    config.addinivalue_line(
        "markers", "performance: marks tests as performance tests"
    )


# Test data constants
TEST_USERS = {
    'admin': {
        'username': 'test_admin',
        'password': 'admin_password_unique',
        'email': 'admin@test.com'
    },
    'user': {
        'username': 'test_user',
        'password': 'user_password_unique',
        'email': 'user@test.com'
    },
    'county': {
        'username': 'test_county',
        'password': 'county_password_unique',
        'email': 'county@test.com'
    }
}

# Security test constants
SECURITY_HEADERS = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Frame-Options': 'SAMEORIGIN',
    'X-Content-Type-Options': 'nosniff',
    'Referrer-Policy': 'strict-origin-when-cross-origin'
}

# Performance test thresholds (in milliseconds)
PERFORMANCE_THRESHOLDS = {
    'login': 200,
    'dashboard': 300,
    'map_load': 500,
    'api_response': 100
}