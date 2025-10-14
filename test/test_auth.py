"""
Authentication and authorization tests for the Precinct application.

Tests cover:
- User login/logout functionality
- Password validation
- Session management
- Access control
- Rate limiting
- User role permissions
"""

import pytest
from flask import session, url_for
from models import User


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


class TestAuthentication:
    """Test user authentication functionality."""
    
    def test_login_page_accessible(self, client):
        """Test that login page loads correctly."""
        response = client.get('/login')
        assert response.status_code == 200
        assert b'Username' in response.data
        assert b'Password' in response.data
        assert b'Sign In' in response.data
    
    def test_valid_login(self, client, regular_user):
        """Test login with valid credentials."""
        response = login_user(client, regular_user.username, 'user_password')
        assert response.status_code == 200
        # Should redirect to dashboard after successful login
        assert b'Dashboard' in response.data or b'dashboard' in response.data
    
    def test_invalid_username(self, client):
        """Test login with invalid username."""
        response = login_user(client, 'nonexistent_user', 'any_password')
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_invalid_password(self, client, regular_user):
        """Test login with invalid password."""
        response = login_user(client, regular_user.username, 'wrong_password')
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_inactive_user_login(self, client, inactive_user):
        """Test that inactive users cannot login."""
        response = login_user(client, inactive_user.username, 'inactive_password')
        assert response.status_code == 200
        assert b'Invalid username or password' in response.data
    
    def test_logout_functionality(self, client, regular_user):
        """Test user logout."""
        # Login first
        login_user(client, regular_user.username, 'user_password')
        
        # Then logout
        response = logout_user(client)
        assert response.status_code == 200
        assert b'You have been logged out' in response.data
    
    def test_remember_me_functionality(self, client, regular_user):
        """Test remember me checkbox functionality."""
        response = client.post('/login', data={
            'username': regular_user.username,
            'password': 'user_password',
            'remember_me': True,
            'submit': 'Sign In'
        }, follow_redirects=True)
        
        assert response.status_code == 200
    
    def test_redirect_after_login(self, client, regular_user):
        """Test redirect to intended page after login."""
        # Try to access protected page
        response = client.get('/profile')
        assert response.status_code == 302  # Redirect to login
        
        # Login with next parameter
        response = client.post('/login?next=%2Fprofile', data={
            'username': regular_user.username,
            'password': 'user_password',
            'submit': 'Sign In'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        # Should be on profile page now
        assert b'Profile' in response.data or b'profile' in response.data


class TestAuthorization:
    """Test user authorization and access control."""
    
    def test_dashboard_requires_login(self, client):
        """Test that dashboard requires authentication."""
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login
    
    def test_profile_requires_login(self, client):
        """Test that profile page requires authentication."""
        response = client.get('/profile')
        assert response.status_code == 302  # Redirect to login
    
    def test_admin_access_control(self, client, regular_user, admin_user):
        """Test admin-only functionality access control."""
        # Regular user should not access admin functions
        login_user(client, regular_user.username, 'user_password')
        response = client.get('/admin/motd')
        assert response.status_code == 302 or b'Access denied' in response.data
        
        logout_user(client)
        
        # Admin user should access admin functions
        login_user(client, admin_user.username, 'admin_password')
        response = client.get('/admin/motd')
        assert response.status_code == 200
    
    def test_county_user_access(self, client, county_user):
        """Test county user access permissions."""
        login_user(client, county_user.username, 'county_password')
        
        # County users should access static content
        response = client.get('/static-content')
        assert response.status_code == 200
    
    def test_regular_user_map_access(self, client, regular_user):
        """Test regular user map access restrictions."""
        login_user(client, regular_user.username, 'user_password')
        
        # Should not access map library
        response = client.get('/static-content')
        assert response.status_code == 302 or b'Access denied' in response.data


class TestSessionManagement:
    """Test session handling and timeout functionality."""
    
    def test_session_creation_on_login(self, client, regular_user):
        """Test that session is properly created on login."""
        with client.session_transaction() as sess:
            assert 'last_activity' not in sess
        
        login_user(client, regular_user.username, 'user_password')
        
        with client.session_transaction() as sess:
            assert 'last_activity' in sess
    
    def test_session_status_endpoint(self, authenticated_client):
        """Test session status API endpoint."""
        response = authenticated_client.get('/api/session-status')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['active', 'warning', 'expired']
    
    def test_session_extension_endpoint(self, authenticated_client):
        """Test session extension API endpoint."""
        response = authenticated_client.post('/api/extend-session')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'extended'
    
    def test_session_status_requires_auth(self, client):
        """Test that session endpoints require authentication."""
        response = client.get('/api/session-status')
        assert response.status_code == 401
        
        response = client.post('/api/extend-session')
        assert response.status_code == 401


class TestPasswordSecurity:
    """Test password handling and security."""
    
    def test_password_hashing(self, app, db_session):
        """Test that passwords are properly hashed."""
        with app.app_context():
            user = User(
                username='hash_test',
                email='hash@test.com',
                password='test_password',
                state='NC',
                county='Wake',
                precinct='001'
            )
            db_session.add(user)
            db_session.commit()
            
            # Password should be hashed, not stored in plain text
            assert user.password_hash != 'test_password'
            assert user.check_password('test_password')
            assert not user.check_password('wrong_password')
    
    def test_password_validation(self, client):
        """Test password validation requirements."""
        # Test with empty password
        response = client.post('/login', data={
            'username': 'test_user',
            'password': '',
            'submit': 'Sign In'
        })
        # Should have validation error (form won't submit)
        assert response.status_code == 200


@pytest.mark.slow
class TestRateLimiting:
    """Test rate limiting on authentication endpoints."""
    
    def test_login_rate_limiting(self, client):
        """Test rate limiting on login attempts."""
        # Attempt multiple rapid logins
        for i in range(12):  # Exceeds the 10 per minute limit
            response = client.post('/login', data={
                'username': 'test_user',
                'password': 'wrong_password',
                'submit': 'Sign In'
            })
            
            if i < 10:
                assert response.status_code == 200
            else:
                # Should be rate limited after 10 attempts
                assert response.status_code == 429


class TestUserLastLogin:
    """Test last login timestamp functionality."""
    
    def test_last_login_updated(self, client, regular_user, db_session):
        """Test that last_login timestamp is updated on successful login."""
        with client.application.app_context():
            # Get initial last_login value
            initial_last_login = regular_user.last_login
            
            # Login
            login_user(client, regular_user.username, 'user_password')
            
            # Refresh user from database
            db_session.refresh(regular_user)
            
            # Last login should be updated
            assert regular_user.last_login != initial_last_login
            assert regular_user.last_login is not None


class TestLoginFlow:
    """Test complete login/logout flow scenarios."""
    
    def test_complete_user_session(self, client, regular_user):
        """Test complete user session from login to logout."""
        # Start with no session
        response = client.get('/')
        assert response.status_code == 302  # Redirect to login
        
        # Login
        response = login_user(client, regular_user.username, 'user_password')
        assert response.status_code == 200
        
        # Access protected resource
        response = client.get('/profile')
        assert response.status_code == 200
        
        # Logout
        response = logout_user(client)
        assert response.status_code == 200
        
        # Verify session is cleared
        response = client.get('/profile')
        assert response.status_code == 302  # Should redirect to login again
    
    def test_already_logged_in_redirect(self, client, regular_user):
        """Test redirect when already logged in user visits login page."""
        # Login first
        login_user(client, regular_user.username, 'user_password')
        
        # Try to visit login page again
        response = client.get('/login')
        assert response.status_code == 302  # Should redirect to dashboard


class TestUserRoles:
    """Test different user role behaviors."""
    
    def test_admin_user_capabilities(self, client, admin_user):
        """Test admin user specific capabilities."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Admin should access user management
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Admin should access MOTD management
        response = client.get('/admin/motd')
        assert response.status_code == 200
    
    def test_county_user_capabilities(self, client, county_user):
        """Test county user specific capabilities."""
        login_user(client, county_user.username, 'county_password')
        
        # County user should access static content
        response = client.get('/static-content')
        assert response.status_code == 200
    
    def test_regular_user_limitations(self, client, regular_user):
        """Test regular user access limitations."""
        login_user(client, regular_user.username, 'user_password')
        
        # Regular user should NOT access admin functions
        response = client.get('/admin/')
        assert response.status_code in [302, 403] or b'Access denied' in response.data
        
        # Regular user should NOT access full map library
        response = client.get('/static-content')
        assert response.status_code in [302, 403] or b'Access denied' in response.data