"""
End-to-end integration tests for the Precinct application.

Tests cover:
- Complete user workflows
- Cross-component interactions
- End-to-end security validation
- Browser-based testing scenarios
- Full application functionality
"""

import pytest
import time


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


@pytest.mark.integration
class TestCompleteUserWorkflows:
    """Test complete user workflows from start to finish."""
    
    def test_regular_user_complete_workflow(self, client, regular_user, sample_map):
        """Test complete workflow for a regular user."""
        # 1. User visits site (redirected to login)
        response = client.get('/')
        assert response.status_code == 302
        
        # 2. User logs in
        response = login_user(client, regular_user.username, 'user_password')
        assert response.status_code == 200
        assert b'Dashboard' in response.data or b'dashboard' in response.data
        
        # 3. User views their profile
        response = client.get('/profile')
        assert response.status_code == 200
        assert regular_user.username.encode() in response.data
        
        # 4. User accesses their map
        response = client.get('/my-map')
        assert response.status_code == 200
        
        # 5. User views map in iframe mode
        response = client.get('/user-map/012.html')
        assert response.status_code == 200
        
        # 6. User checks session status
        response = client.get('/api/session-status')
        assert response.status_code == 200
        data = response.get_json()
        assert data['status'] == 'active'
        
        # 7. User extends session
        response = client.post('/api/extend-session')
        assert response.status_code == 200
        
        # 8. User visits about page
        response = client.get('/about')
        assert response.status_code == 200
        
        # 9. User logs out
        response = logout_user(client)
        assert response.status_code == 200
        assert b'logged out' in response.data
        
        # 10. Verify session is cleared
        response = client.get('/profile')
        assert response.status_code == 302  # Redirected to login
    
    def test_admin_user_complete_workflow(self, client, admin_user, multiple_maps):
        """Test complete workflow for an admin user."""
        # 1. Admin logs in
        response = login_user(client, admin_user.username, 'admin_password')
        assert response.status_code == 200
        
        # 2. Admin accesses dashboard
        response = client.get('/')
        assert response.status_code == 200
        
        # 3. Admin accesses user administration
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # 4. Admin manages MOTD
        response = client.get('/admin/motd')
        assert response.status_code == 200
        
        # Update MOTD
        response = client.post('/admin/motd', data={
            'motd_content': 'Integration test MOTD'
        }, follow_redirects=True)
        assert response.status_code == 200
        
        # 5. Admin accesses map library
        response = client.get('/static-content')
        assert response.status_code == 200
        
        # 6. Admin views specific maps
        response = client.get('/static-content/012.html')
        assert response.status_code == 200
        
        # 7. Admin opens map in new tab
        response = client.get('/view/012.html')
        assert response.status_code == 200
        assert b'Close Window' in response.data
        assert b'zoomIn()' in response.data
        
        # 8. Admin logs out
        response = logout_user(client)
        assert response.status_code == 200
    
    def test_county_user_complete_workflow(self, client, county_user, multiple_maps):
        """Test complete workflow for a county user."""
        # 1. County user logs in
        response = login_user(client, county_user.username, 'county_password')
        assert response.status_code == 200
        
        # 2. County user accesses dashboard
        response = client.get('/')
        assert response.status_code == 200
        
        # 3. County user accesses map library
        response = client.get('/static-content')
        assert response.status_code == 200
        
        # 4. County user views maps in their county
        response = client.get('/static-content/001.html')
        assert response.status_code == 200
        
        response = client.get('/static-content/012.html')
        assert response.status_code == 200
        
        # 5. County user cannot access admin functions
        response = client.get('/admin/')
        assert response.status_code in [302, 403] or b'Access denied' in response.data
        
        response = client.get('/admin/motd')
        assert response.status_code in [302, 403] or b'Access denied' in response.data
        
        # 6. County user logs out
        response = logout_user(client)
        assert response.status_code == 200


@pytest.mark.integration
class TestCrossComponentInteractions:
    """Test interactions between different components."""
    
    def test_authentication_and_map_access(self, client, regular_user, sample_map):
        """Test integration between authentication and map access."""
        # Without authentication, map access should fail
        response = client.get('/user-map/012.html')
        assert response.status_code == 302
        
        response = client.get('/my-map')
        assert response.status_code == 302
        
        # After authentication, map access should work
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/user-map/012.html')
        assert response.status_code == 200
        
        response = client.get('/my-map')
        assert response.status_code == 200
    
    def test_session_management_and_api_access(self, client, regular_user):
        """Test integration between session management and API access."""
        # API access without session should fail
        response = client.get('/api/session-status')
        assert response.status_code == 401
        
        response = client.post('/api/extend-session')
        assert response.status_code == 401
        
        # After login, API should work
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/api/session-status')
        assert response.status_code == 200
        
        response = client.post('/api/extend-session')
        assert response.status_code == 200
        
        # After logout, API should fail again
        logout_user(client)
        
        response = client.get('/api/session-status')
        assert response.status_code == 401
    
    def test_admin_privileges_and_map_access(self, client, admin_user, regular_user, sample_map):
        """Test integration between admin privileges and map access."""
        # Regular user can only access their map
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/static-content')
        assert response.status_code in [302, 403] or b'Access denied' in response.data
        
        logout_user(client)
        
        # Admin can access all maps
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/static-content')
        assert response.status_code == 200
        
        response = client.get('/user-map/012.html')
        assert response.status_code == 200
    
    def test_database_and_map_rendering(self, client, regular_user, sample_map):
        """Test integration between database content and map rendering."""
        login_user(client, regular_user.username, 'user_password')
        
        # Raw map should come from database
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 200
        
        # Should contain database content
        assert b'Test Map - Precinct 012' in response.data
        
        # Should also contain injected zoom controls
        assert b'window.addEventListener' in response.data
        assert b'zoomIn' in response.data


@pytest.mark.integration
class TestSecurityIntegration:
    """Test end-to-end security functionality."""
    
    def test_complete_security_headers_flow(self, client, regular_user):
        """Test security headers throughout complete user flow."""
        # Check headers on login page
        response = client.get('/login')
        assert 'Strict-Transport-Security' in response.headers
        assert 'X-Frame-Options' in response.headers
        
        # Check headers after login
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/')
        assert 'Strict-Transport-Security' in response.headers
        assert 'X-Frame-Options' in response.headers
        
        # Check headers on API endpoints
        response = client.get('/api/session-status')
        assert 'Strict-Transport-Security' in response.headers
        
        # Check headers on map content
        response = client.get('/user-map-raw/012.html')
        assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
    
    def test_iframe_security_integration(self, client, regular_user, sample_map):
        """Test iframe security integration."""
        login_user(client, regular_user.username, 'user_password')
        
        # Map viewer should allow iframe embedding
        response = client.get('/user-map/012.html')
        assert response.status_code == 200
        
        # Raw map content should have proper headers for iframe
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 200
        assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
        
        # Should include zoom control message listener
        assert b'window.addEventListener(\'message\'' in response.data
    
    def test_session_timeout_integration(self, client, regular_user):
        """Test session timeout integration across components."""
        login_user(client, regular_user.username, 'user_password')
        
        # Fresh session should be active
        response = client.get('/api/session-status')
        data = response.get_json()
        assert data['status'] == 'active'
        
        # Navigation should maintain session
        client.get('/profile')
        client.get('/about')
        
        response = client.get('/api/session-status')
        data = response.get_json()
        assert data['status'] == 'active'
        
        # Session extension should work
        response = client.post('/api/extend-session')
        assert response.status_code == 200


@pytest.mark.integration
class TestDataFlowIntegration:
    """Test data flow between components."""
    
    def test_user_data_to_map_access(self, client, regular_user, sample_map):
        """Test flow from user data to map access."""
        login_user(client, regular_user.username, 'user_password')
        
        # User's profile data should determine map access
        response = client.get('/my-map')
        assert response.status_code == 200
        
        # Map should be based on user's state/county/precinct
        response = client.get('/my-map-raw')
        assert response.status_code == 200
        assert b'Wake County, Precinct 012' in response.data
    
    def test_admin_privileges_to_functionality(self, client, admin_user):
        """Test flow from admin privileges to available functionality."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Admin status should enable admin functions
        response = client.get('/admin/')
        assert response.status_code == 200
        
        response = client.get('/admin/motd')
        assert response.status_code == 200
        
        # Admin should access all maps
        response = client.get('/static-content')
        assert response.status_code == 200
    
    def test_database_to_ui_integration(self, client, admin_user, sample_map):
        """Test integration from database content to UI display."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Database map content should appear in UI
        response = client.get('/static-content/012.html')
        assert response.status_code == 200
        
        # Raw content should match database
        response = client.get('/static-content-raw/012.html')
        assert response.status_code == 200
        assert b'Test Map - Precinct 012' in response.data


@pytest.mark.integration 
@pytest.mark.slow
class TestPerformanceIntegration:
    """Test performance across integrated components."""
    
    def test_complete_workflow_performance(self, client, regular_user, sample_map):
        """Test performance of complete user workflow."""
        start_time = time.time()
        
        # Complete workflow with timing
        login_user(client, regular_user.username, 'user_password')
        client.get('/')
        client.get('/profile')
        client.get('/my-map')
        client.get('/api/session-status')
        client.post('/api/extend-session')
        logout_user(client)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Complete workflow should be reasonably fast (allow 5 seconds for testing)
        assert total_time < 5.0
    
    def test_map_loading_performance(self, client, regular_user, sample_map):
        """Test map loading performance."""
        login_user(client, regular_user.username, 'user_password')
        
        # Test map loading times
        start_time = time.time()
        response = client.get('/user-map/012.html')
        end_time = time.time()
        
        assert response.status_code == 200
        load_time = end_time - start_time
        assert load_time < 1.0  # Should load within 1 second
        
        # Test raw map content loading
        start_time = time.time()
        response = client.get('/user-map-raw/012.html')
        end_time = time.time()
        
        assert response.status_code == 200
        load_time = end_time - start_time
        assert load_time < 0.5  # Raw content should be faster


@pytest.mark.integration
class TestErrorHandlingIntegration:
    """Test error handling across integrated components."""
    
    def test_database_error_to_ui_handling(self, client, regular_user):
        """Test graceful handling of database errors in UI."""
        login_user(client, regular_user.username, 'user_password')
        
        # Try to access non-existent map
        response = client.get('/user-map/999.html')
        
        # Should handle gracefully with proper error page
        assert response.status_code in [404, 200]
        
        if response.status_code == 200:
            # Should show user-friendly error
            assert b'Error' in response.data or b'not found' in response.data
    
    def test_authentication_error_flow(self, client):
        """Test authentication error flow across components."""
        # Try to access protected resources without authentication
        protected_urls = [
            '/',
            '/profile',
            '/my-map',
            '/api/session-status',
            '/admin/'
        ]
        
        for url in protected_urls:
            response = client.get(url)
            # Should redirect to login or return 401
            assert response.status_code in [302, 401]
    
    def test_permission_error_integration(self, client, regular_user):
        """Test permission error handling across components."""
        login_user(client, regular_user.username, 'user_password')
        
        # Try to access admin-only resources
        admin_urls = [
            '/admin/',
            '/admin/motd',
            '/static-content'
        ]
        
        for url in admin_urls:
            response = client.get(url)
            # Should deny access appropriately
            assert response.status_code in [302, 403] or b'Access denied' in response.data


@pytest.mark.integration
class TestBrowserCompatibility:
    """Test browser compatibility scenarios (simulated)."""
    
    def test_iframe_compatibility_flow(self, client, regular_user, sample_map):
        """Test iframe compatibility throughout the application."""
        login_user(client, regular_user.username, 'user_password')
        
        # Viewer page should set up iframe correctly
        response = client.get('/user-map/012.html')
        assert response.status_code == 200
        
        # Raw content should be iframe-compatible
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 200
        assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
        
        # Should include cross-frame communication
        assert b'window.addEventListener(\'message\'' in response.data
    
    def test_javascript_functionality_integration(self, client, admin_user, sample_map):
        """Test JavaScript functionality integration."""
        login_user(client, admin_user.username, 'admin_password')
        
        # New tab view should include JavaScript controls
        response = client.get('/view/012.html')
        assert response.status_code == 200
        
        # Should include zoom control JavaScript
        assert b'zoomIn()' in response.data
        assert b'zoomOut()' in response.data
        assert b'closeWindow()' in response.data
        
        # Should include proper event handlers
        assert b'onclick=' in response.data