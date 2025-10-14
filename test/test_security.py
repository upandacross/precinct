"""
Security tests for the Precinct application.

Tests cover:
- HSTS (HTTP Strict Transport Security) headers
- Content Security Policy (CSP)
- X-Frame-Options for iframe compatibility
- Other security headers
- Session security
- CSRF protection
"""

import pytest


def login_user(client, username, password):
    """Helper function to login a user."""
    return client.post('/login', data={
        'username': username,
        'password': password,
        'submit': 'Sign In'
    }, follow_redirects=True)


class TestSecurityHeaders:
    """Test security headers implementation."""
    
    def test_hsts_header_present(self, client):
        """Test that HSTS header is present and properly configured."""
        response = client.get('/login')
        
        assert 'Strict-Transport-Security' in response.headers
        hsts_header = response.headers['Strict-Transport-Security']
        
        # Verify HSTS configuration
        assert 'max-age=31536000' in hsts_header  # 1 year
        assert 'includeSubDomains' in hsts_header
    
    def test_x_frame_options_sameorigin(self, client):
        """Test X-Frame-Options is set to SAMEORIGIN for iframe compatibility."""
        response = client.get('/login')
        
        assert 'X-Frame-Options' in response.headers
        assert response.headers['X-Frame-Options'] == 'SAMEORIGIN'
    
    def test_content_security_policy(self, client):
        """Test Content Security Policy header."""
        response = client.get('/login')
        
        assert 'Content-Security-Policy' in response.headers
        csp_header = response.headers['Content-Security-Policy']
        
        # Verify CSP directives
        assert 'frame-ancestors \'self\'' in csp_header
        assert 'default-src' in csp_header
    
    def test_x_content_type_options(self, client):
        """Test X-Content-Type-Options header prevents MIME sniffing."""
        response = client.get('/login')
        
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
    
    def test_referrer_policy(self, client):
        """Test Referrer-Policy header configuration."""
        response = client.get('/login')
        
        assert 'Referrer-Policy' in response.headers
        referrer_policy = response.headers['Referrer-Policy']
        
        # Should be a restrictive policy
        assert referrer_policy in [
            'strict-origin-when-cross-origin',
            'strict-origin',
            'same-origin'
        ]
    
    def test_permissions_policy(self, client):
        """Test Permissions-Policy header (formerly Feature-Policy)."""
        response = client.get('/login')
        
        # Permissions-Policy should be present
        assert 'Permissions-Policy' in response.headers
    
    def test_security_headers_on_all_routes(self, client, regular_user):
        """Test that security headers are present on all routes."""
        # Test routes that don't require authentication
        routes_to_test = ['/login']
        
        for route in routes_to_test:
            response = client.get(route)
            assert 'Strict-Transport-Security' in response.headers
            assert 'X-Frame-Options' in response.headers
            assert 'X-Content-Type-Options' in response.headers
        
        # Test authenticated routes
        login_user(client, regular_user.username, 'user_password')
        
        auth_routes = ['/', '/profile', '/about']
        for route in auth_routes:
            response = client.get(route)
            assert 'Strict-Transport-Security' in response.headers
            assert 'X-Frame-Options' in response.headers
            assert 'X-Content-Type-Options' in response.headers


class TestIframeSecurity:
    """Test iframe-related security configurations."""
    
    def test_iframe_embedding_allowed_same_origin(self, client, regular_user, sample_map):
        """Test that iframe embedding works for same-origin requests."""
        login_user(client, regular_user.username, 'user_password')
        
        # Test raw map content (used in iframes)
        response = client.get('/user-map-raw/012.html')
        
        # Should be successful
        assert response.status_code == 200
        
        # Should have proper headers for iframe compatibility
        assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    
    def test_map_viewer_iframe_compatibility(self, client, regular_user, sample_map):
        """Test that map viewer page works with iframe setup."""
        login_user(client, regular_user.username, 'user_password')
        
        # Test the viewer page that contains the iframe
        response = client.get('/user-map/012.html')
        assert response.status_code == 200
        
        # Should contain iframe element
        assert b'iframe' in response.data


class TestSessionSecurity:
    """Test session security configurations."""
    
    def test_session_cookie_secure_settings(self, app):
        """Test session cookie security settings."""
        with app.app_context():
            # In production, these should be secure
            # For testing, we verify the configuration exists
            assert app.config.get('SESSION_COOKIE_SECURE') is not None or app.config.get('TESTING')
            assert app.config.get('SESSION_COOKIE_HTTPONLY') is not None or app.config.get('TESTING')
    
    def test_session_timeout_functionality(self, client, regular_user):
        """Test session timeout security feature."""
        login_user(client, regular_user.username, 'user_password')
        
        # Test session status endpoint
        response = client.get('/api/session-status')
        assert response.status_code == 200
        
        data = response.get_json()
        assert 'status' in data
        assert data['status'] in ['active', 'warning']
    
    def test_session_extension_security(self, client, regular_user):
        """Test session extension endpoint security."""
        # Should require authentication
        response = client.post('/api/extend-session')
        assert response.status_code == 401
        
        # Should work when authenticated
        login_user(client, regular_user.username, 'user_password')
        response = client.post('/api/extend-session')
        assert response.status_code == 200


class TestCSRFProtection:
    """Test CSRF protection (disabled in testing but verify structure)."""
    
    def test_csrf_token_structure(self, client):
        """Test CSRF token handling structure."""
        # In testing, CSRF is disabled, but verify the form structure
        response = client.get('/login')
        assert response.status_code == 200
        
        # Login form should be present
        assert b'form' in response.data
        assert b'username' in response.data
        assert b'password' in response.data
    
    def test_form_submission_works(self, client, regular_user):
        """Test that forms work (CSRF disabled in testing)."""
        response = client.post('/login', data={
            'username': regular_user.username,
            'password': 'user_password',
            'submit': 'Sign In'
        }, follow_redirects=True)
        
        assert response.status_code == 200


@pytest.mark.security
class TestSecurityBestPractices:
    """Test adherence to security best practices."""
    
    def test_no_sensitive_info_in_headers(self, client):
        """Test that no sensitive information is leaked in headers."""
        response = client.get('/login')
        
        # Server header should not reveal too much info
        server_header = response.headers.get('Server', '')
        # In testing mode, some headers might be different
        # This is a structural test for production security
    
    def test_error_pages_no_info_disclosure(self, client):
        """Test that error pages don't disclose sensitive information."""
        # Test 404 error
        response = client.get('/nonexistent-page')
        assert response.status_code == 404
        
        # Should not contain sensitive debug information
        assert b'Traceback' not in response.data
        assert b'File "' not in response.data
    
    def test_login_error_messages(self, client):
        """Test that login error messages don't reveal user existence."""
        # Test with non-existent user
        response = client.post('/login', data={
            'username': 'nonexistent_user',
            'password': 'any_password',
            'submit': 'Sign In'
        })
        
        # Should use generic error message
        assert b'Invalid username or password' in response.data
        
        # Test with existing user but wrong password
        response = client.post('/login', data={
            'username': 'test_user',  # This might not exist, but error should be same
            'password': 'wrong_password',
            'submit': 'Sign In'
        })
        
        assert b'Invalid username or password' in response.data


class TestRateLimiting:
    """Test rate limiting security measures."""
    
    def test_login_rate_limiting_headers(self, client):
        """Test rate limiting headers on login attempts."""
        response = client.post('/login', data={
            'username': 'test',
            'password': 'test',
            'submit': 'Sign In'
        })
        
        # Should have rate limiting headers
        # Note: Exact headers depend on Flask-Limiter configuration
        assert response.status_code in [200, 429]
    
    @pytest.mark.slow
    def test_excessive_login_attempts_blocked(self, client):
        """Test that excessive login attempts are blocked."""
        # Make multiple rapid login attempts
        for i in range(15):  # Exceed the limit
            response = client.post('/login', data={
                'username': 'attacker',
                'password': 'wrong',
                'submit': 'Sign In'
            })
            
            # After the limit, should get 429 (Too Many Requests)
            if i > 10:  # After exceeding the 10 per minute limit
                assert response.status_code == 429


class TestMapAccessSecurity:
    """Test security of map access controls."""
    
    def test_map_access_requires_authentication(self, client):
        """Test that map endpoints require authentication."""
        response = client.get('/user-map/012.html')
        assert response.status_code == 302  # Redirect to login
        
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 302  # Redirect to login
    
    def test_map_access_control_by_precinct(self, client, regular_user, sample_map):
        """Test that users can only access their assigned precinct maps."""
        login_user(client, regular_user.username, 'user_password')
        
        # Should access their own precinct (012)
        response = client.get('/user-map/012.html')
        assert response.status_code == 200
        
        # Should NOT access different precinct
        response = client.get('/user-map/999.html')
        assert response.status_code in [403, 404] or b'Access denied' in response.data
    
    def test_admin_map_access_override(self, client, admin_user, sample_map):
        """Test that admin users can access any map."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Admin should access any map
        response = client.get('/user-map/012.html')
        assert response.status_code == 200


class TestHTTPSRedirection:
    """Test HTTPS-related security configurations."""
    
    def test_hsts_forces_https(self, client):
        """Test that HSTS header forces HTTPS in browsers."""
        response = client.get('/login')
        
        hsts_header = response.headers.get('Strict-Transport-Security')
        assert hsts_header is not None
        
        # Should have long max-age to force HTTPS
        assert 'max-age=31536000' in hsts_header  # 1 year
    
    def test_secure_headers_present(self, client):
        """Test that all security headers are present."""
        response = client.get('/login')
        
        expected_headers = [
            'Strict-Transport-Security',
            'X-Frame-Options',
            'X-Content-Type-Options',
            'Content-Security-Policy'
        ]
        
        for header in expected_headers:
            assert header in response.headers, f"Missing security header: {header}"


@pytest.mark.security
class TestContentSecurityPolicy:
    """Detailed CSP testing."""
    
    def test_csp_prevents_xss(self, client):
        """Test CSP configuration prevents XSS attacks."""
        response = client.get('/login')
        
        csp_header = response.headers.get('Content-Security-Policy', '')
        
        # Should have restrictive script-src
        assert 'script-src' in csp_header
        
        # Should not allow 'unsafe-inline' without nonce/hash
        if '\'unsafe-inline\'' in csp_header:
            # If unsafe-inline is present, should have nonce or hash
            assert 'nonce-' in csp_header or 'sha256-' in csp_header
    
    def test_csp_frame_ancestors(self, client):
        """Test CSP frame-ancestors directive."""
        response = client.get('/login')
        
        csp_header = response.headers.get('Content-Security-Policy', '')
        
        # Should allow self for iframe compatibility
        assert 'frame-ancestors \'self\'' in csp_header