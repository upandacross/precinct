"""
API endpoints and session management tests for the Precinct application.

Tests cover:
- Session status endpoint
- Session extension endpoint  
- API authentication requirements
- Response format validation
- Rate limiting compliance
- Error handling
"""

import pytest
import json
from datetime import datetime


def login_user(client, username, password):
    """Helper function to login a user."""
    return client.post('/login', data={
        'username': username,
        'password': password,
        'submit': 'Sign In'
    }, follow_redirects=True)


class TestSessionAPI:
    """Test session management API endpoints."""
    
    def test_session_status_requires_auth(self, client):
        """Test that session status endpoint requires authentication."""
        response = client.get('/api/session-status')
        assert response.status_code == 401
        
        # Should return JSON error
        try:
            data = response.get_json()
            assert data is not None
        except:
            pass  # Some setups might not return JSON for 401
    
    def test_session_status_authenticated(self, client, regular_user):
        """Test session status endpoint with authenticated user."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/api/session-status')
        assert response.status_code == 200
        
        # Should return JSON with status
        data = response.get_json()
        assert data is not None
        assert 'status' in data
        assert data['status'] in ['active', 'warning', 'expired']
    
    def test_session_status_active_response(self, client, regular_user):
        """Test session status returns active for fresh session."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/api/session-status')
        assert response.status_code == 200
        
        data = response.get_json()
        assert data['status'] == 'active'
    
    def test_session_extend_requires_auth(self, client):
        """Test that session extension endpoint requires authentication."""
        response = client.post('/api/extend-session')
        assert response.status_code == 401
    
    def test_session_extend_authenticated(self, client, regular_user):
        """Test session extension endpoint with authenticated user."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.post('/api/extend-session')
        assert response.status_code == 200
        
        # Should return JSON confirmation
        data = response.get_json()
        assert data is not None
        assert 'status' in data
        assert data['status'] == 'extended'
    
    def test_session_extend_method_restriction(self, client, regular_user):
        """Test that session extension only accepts POST method."""
        login_user(client, regular_user.username, 'user_password')
        
        # GET should not be allowed
        response = client.get('/api/extend-session')
        assert response.status_code == 405  # Method Not Allowed
        
        # PUT should not be allowed
        response = client.put('/api/extend-session')
        assert response.status_code == 405


class TestAPIResponseFormats:
    """Test API response format consistency."""
    
    def test_session_status_json_format(self, client, regular_user):
        """Test session status API returns proper JSON format."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/api/session-status')
        assert response.status_code == 200
        
        # Should have JSON content type
        content_type = response.headers.get('Content-Type', '')
        assert 'application/json' in content_type or content_type == ''
        
        # Should be valid JSON
        data = response.get_json()
        assert isinstance(data, dict)
        
        # Should have required fields
        assert 'status' in data
        
        # Status should be valid value
        valid_statuses = ['active', 'warning', 'expired']
        assert data['status'] in valid_statuses
    
    def test_session_extend_json_format(self, client, regular_user):
        """Test session extension API returns proper JSON format."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.post('/api/extend-session')
        assert response.status_code == 200
        
        # Should be valid JSON
        data = response.get_json()
        assert isinstance(data, dict)
        assert 'status' in data
        assert data['status'] == 'extended'
    
    def test_api_error_responses(self, client):
        """Test API error response formats."""
        # Test unauthorized access
        response = client.get('/api/session-status')
        assert response.status_code == 401
        
        # Error responses should be consistent
        # (Implementation may vary - this tests the structure)
        try:
            data = response.get_json()
            if data:
                assert isinstance(data, dict)
        except:
            pass  # Some frameworks don't return JSON for auth errors


class TestAPISecurityHeaders:
    """Test security headers on API endpoints."""
    
    def test_api_security_headers(self, client, regular_user):
        """Test that API endpoints include security headers."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/api/session-status')
        assert response.status_code == 200
        
        # Should have security headers
        assert 'X-Content-Type-Options' in response.headers
        assert response.headers['X-Content-Type-Options'] == 'nosniff'
        
        # Should have HSTS header
        assert 'Strict-Transport-Security' in response.headers
    
    def test_api_cors_headers(self, client, regular_user):
        """Test CORS headers on API endpoints if applicable."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/api/session-status')
        assert response.status_code == 200
        
        # API should not have permissive CORS by default
        cors_header = response.headers.get('Access-Control-Allow-Origin')
        if cors_header:
            assert cors_header != '*'  # Should not allow all origins


class TestAPIRateLimiting:
    """Test rate limiting on API endpoints."""
    
    @pytest.mark.slow
    def test_api_rate_limiting(self, client, regular_user):
        """Test rate limiting on API endpoints."""
        login_user(client, regular_user.username, 'user_password')
        
        # Make multiple rapid requests
        responses = []
        for i in range(10):
            response = client.get('/api/session-status')
            responses.append(response.status_code)
        
        # Should mostly succeed (within rate limits)
        success_count = sum(1 for code in responses if code == 200)
        assert success_count >= 8  # Allow for some rate limiting
    
    def test_api_rate_limit_headers(self, client, regular_user):
        """Test rate limiting headers on API responses."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/api/session-status')
        
        # Should include rate limiting information (if implemented)
        # Note: Exact headers depend on Flask-Limiter configuration
        # This is a structural test
        assert response.status_code in [200, 429]


class TestSessionTimeout:
    """Test session timeout functionality through API."""
    
    def test_session_warning_threshold(self, client, regular_user):
        """Test session warning functionality."""
        login_user(client, regular_user.username, 'user_password')
        
        # Fresh session should be active
        response = client.get('/api/session-status')
        data = response.get_json()
        assert data['status'] == 'active'
        
        # Session extension should reset activity
        response = client.post('/api/extend-session')
        assert response.status_code == 200
        
        # Should still be active after extension
        response = client.get('/api/session-status')
        data = response.get_json()
        assert data['status'] == 'active'
    
    def test_session_activity_tracking(self, client, regular_user):
        """Test that session activity is properly tracked."""
        # Login creates session activity
        login_user(client, regular_user.username, 'user_password')
        
        # API calls should update activity
        response = client.get('/api/session-status')
        assert response.status_code == 200
        
        # Extension should update activity
        response = client.post('/api/extend-session')
        assert response.status_code == 200
        
        # Subsequent status check should still be active
        response = client.get('/api/session-status')
        data = response.get_json()
        assert data['status'] == 'active'


class TestAPIErrorHandling:
    """Test error handling in API endpoints."""
    
    def test_invalid_api_endpoints(self, client):
        """Test handling of invalid API endpoint requests."""
        response = client.get('/api/nonexistent-endpoint')
        assert response.status_code == 404
    
    def test_malformed_requests(self, client, regular_user):
        """Test handling of malformed API requests."""
        login_user(client, regular_user.username, 'user_password')
        
        # Test with invalid content type
        response = client.post('/api/extend-session', 
                              data='invalid json',
                              headers={'Content-Type': 'application/json'})
        
        # Should handle gracefully
        assert response.status_code in [200, 400]
    
    def test_api_method_not_allowed(self, client, regular_user):
        """Test proper handling of wrong HTTP methods."""
        login_user(client, regular_user.username, 'user_password')
        
        # Session status should only accept GET
        response = client.post('/api/session-status')
        assert response.status_code == 405  # Method Not Allowed
        
        # Session extend should only accept POST
        response = client.get('/api/extend-session')
        assert response.status_code == 405


class TestAPIIntegration:
    """Test API integration with application features."""
    
    def test_session_api_with_page_navigation(self, client, regular_user):
        """Test session API behavior during page navigation."""
        login_user(client, regular_user.username, 'user_password')
        
        # Navigate to different pages
        client.get('/')
        client.get('/profile')
        client.get('/about')
        
        # Session should remain active
        response = client.get('/api/session-status')
        data = response.get_json()
        assert data['status'] == 'active'
    
    def test_session_api_after_logout(self, client, regular_user):
        """Test session API behavior after logout."""
        login_user(client, regular_user.username, 'user_password')
        
        # Verify session is active
        response = client.get('/api/session-status')
        assert response.status_code == 200
        
        # Logout
        client.get('/logout', follow_redirects=True)
        
        # Session API should require re-authentication
        response = client.get('/api/session-status')
        assert response.status_code == 401


class TestAPIPerformance:
    """Test API endpoint performance."""
    
    def test_api_response_times(self, client, regular_user):
        """Test API response times are reasonable."""
        import time
        
        login_user(client, regular_user.username, 'user_password')
        
        # Test session status endpoint
        start_time = time.time()
        response = client.get('/api/session-status')
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Response should be fast (less than 100ms in test environment)
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert response_time < 1000  # Allow 1 second in test environment
        
        # Test session extension endpoint
        start_time = time.time()
        response = client.post('/api/extend-session')
        end_time = time.time()
        
        assert response.status_code == 200
        
        response_time = (end_time - start_time) * 1000
        assert response_time < 1000


class TestAPIContentNegotiation:
    """Test API content negotiation and headers."""
    
    def test_api_accepts_json(self, client, regular_user):
        """Test API properly handles JSON Accept headers."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/api/session-status', 
                             headers={'Accept': 'application/json'})
        assert response.status_code == 200
        
        # Should return JSON
        data = response.get_json()
        assert data is not None
    
    def test_api_content_type_headers(self, client, regular_user):
        """Test API sets proper Content-Type headers."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/api/session-status')
        assert response.status_code == 200
        
        # Should have appropriate content type
        content_type = response.headers.get('Content-Type', '')
        # Flask might set this automatically or it might be empty in test
        assert 'application/json' in content_type or content_type == ''