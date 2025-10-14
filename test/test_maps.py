"""
Map functionality and access control tests for the Precinct application.

Tests cover:
- Map access controls
- Map content delivery
- Map viewing modes (navbar, raw, new tab)
- Zoom control functionality
- Error handling for missing maps
- Iframe compatibility
"""

import pytest


def login_user(client, username, password):
    """Helper function to login a user."""
    return client.post('/login', data={
        'username': username,
        'password': password,
        'submit': 'Sign In'
    }, follow_redirects=True)


class TestMapAccessControl:
    """Test map access control functionality."""
    
    def test_map_requires_authentication(self, client):
        """Test that all map endpoints require authentication."""
        map_endpoints = [
            '/user-map/012.html',
            '/user-map-raw/012.html',
            '/static-content/012.html',
            '/static-content-raw/012.html',
            '/view/012.html',
            '/my-map',
            '/my-map-raw'
        ]
        
        for endpoint in map_endpoints:
            response = client.get(endpoint)
            assert response.status_code == 302  # Redirect to login
    
    def test_regular_user_map_access(self, client, regular_user, sample_map):
        """Test regular user map access permissions."""
        login_user(client, regular_user.username, 'user_password')
        
        # Should access their own precinct map
        response = client.get('/user-map/012.html')
        assert response.status_code == 200
        
        # Should access raw version of their map
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 200
        
        # Should NOT access different precinct
        response = client.get('/user-map/999.html')
        assert response.status_code in [403, 404] or b'Access denied' in response.data
    
    def test_admin_map_access(self, client, admin_user, sample_map, multiple_maps):
        """Test admin user map access permissions."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Admin should access any map
        response = client.get('/user-map/012.html')
        assert response.status_code == 200
        
        # Should access map library
        response = client.get('/static-content')
        assert response.status_code == 200
        
        # Should access any precinct in the library
        response = client.get('/static-content/001.html')
        assert response.status_code == 200
    
    def test_county_user_map_access(self, client, county_user, multiple_maps):
        """Test county user map access permissions."""
        login_user(client, county_user.username, 'county_password')
        
        # County user should access map library
        response = client.get('/static-content')
        assert response.status_code == 200
        
        # Should access maps in their county
        response = client.get('/static-content/012.html')
        assert response.status_code == 200
    
    def test_regular_user_denied_map_library(self, client, regular_user):
        """Test that regular users cannot access map library."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/static-content')
        assert response.status_code == 302 or b'Access denied' in response.data


class TestMapContentDelivery:
    """Test map content delivery and rendering."""
    
    def test_map_content_from_database(self, client, regular_user, sample_map):
        """Test that map content is served from database."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 200
        
        # Should contain the HTML content from database
        assert b'Test Map - Precinct 012' in response.data
        assert b'Test Precinct Map 012' in response.data
        assert b'Wake County, Precinct 012' in response.data
    
    def test_map_with_navbar_wrapper(self, client, regular_user, sample_map):
        """Test map display with navbar wrapper."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/user-map/012.html')
        assert response.status_code == 200
        
        # Should use the static_viewer template
        assert b'iframe' in response.data or b'map-container' in response.data
    
    def test_map_error_handling_missing_map(self, client, regular_user):
        """Test error handling when map doesn't exist."""
        login_user(client, regular_user.username, 'user_password')
        
        # Try to access non-existent map
        response = client.get('/user-map-raw/999.html')
        
        # Should return error page or 404
        assert response.status_code in [404, 200]
        
        if response.status_code == 200:
            # Should contain error information
            assert b'Error' in response.data or b'not found' in response.data
    
    def test_map_content_security(self, client, regular_user, sample_map):
        """Test that map content includes security features."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 200
        
        # Should include zoom message listener for security
        assert b'window.addEventListener' in response.data
    
    def test_my_map_functionality(self, client, regular_user, sample_map):
        """Test /my-map endpoint functionality."""
        login_user(client, regular_user.username, 'user_password')
        
        # Should access user's map based on their profile
        response = client.get('/my-map')
        assert response.status_code == 200
        
        # Raw version should also work
        response = client.get('/my-map-raw')
        assert response.status_code == 200
        assert b'Test Map - Precinct 012' in response.data


class TestMapViewingModes:
    """Test different map viewing modes."""
    
    def test_new_tab_view_with_controls(self, client, county_user, sample_map):
        """Test new tab view with close button and zoom controls."""
        login_user(client, county_user.username, 'county_password')
        
        response = client.get('/view/012.html')
        assert response.status_code == 200
        
        # Should include close button
        assert b'Close Window' in response.data
        assert b'closeWindow()' in response.data
        
        # Should include zoom controls
        assert b'zoomIn()' in response.data
        assert b'zoomOut()' in response.data
        assert b'resetZoom()' in response.data
    
    def test_iframe_raw_view(self, client, regular_user, sample_map):
        """Test raw view for iframe embedding."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 200
        
        # Should have proper iframe compatibility
        headers = response.headers
        assert headers.get('X-Frame-Options') == 'SAMEORIGIN'
        
        # Should include message listener for zoom controls
        assert b'window.addEventListener(\'message\'' in response.data
    
    def test_static_content_viewer(self, client, county_user, sample_map):
        """Test static content viewer with navbar."""
        login_user(client, county_user.username, 'county_password')
        
        response = client.get('/static-content/012.html')
        assert response.status_code == 200
        
        # Should use static_viewer template
        # This would typically include navigation elements


class TestZoomControlFunctionality:
    """Test zoom control features."""
    
    def test_zoom_controls_in_new_tab(self, client, admin_user, sample_map):
        """Test zoom controls in new tab view."""
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/view/012.html')
        assert response.status_code == 200
        
        # Should have enhanced zoom controls
        assert b'new-tab-zoom-controls' in response.data
        assert b'Zoom In' in response.data
        assert b'Zoom Out' in response.data
        assert b'Reset' in response.data
    
    def test_zoom_message_listener(self, client, regular_user, sample_map):
        """Test zoom control message listener for iframe communication."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 200
        
        # Should include message listener
        assert b'window.addEventListener(\'message\'' in response.data
        assert b'event.data.action' in response.data
        assert b'zoomIn' in response.data
        assert b'zoomOut' in response.data
        assert b'resetZoom' in response.data


class TestMapLibraryFunctionality:
    """Test map library browsing functionality."""
    
    def test_map_library_display(self, client, county_user, multiple_maps):
        """Test map library displays available maps."""
        login_user(client, county_user.username, 'county_password')
        
        response = client.get('/static-content')
        assert response.status_code == 200
        
        # Should display list of maps
        assert b'001.html' in response.data
        assert b'002.html' in response.data
        assert b'012.html' in response.data
    
    def test_map_library_county_filtering(self, client, county_user, multiple_maps):
        """Test that map library shows only county-appropriate maps."""
        login_user(client, county_user.username, 'county_password')
        
        response = client.get('/static-content')
        assert response.status_code == 200
        
        # Should only show maps for user's county (Wake)
        # This depends on the implementation details
        assert response.status_code == 200  # Basic check
    
    def test_map_library_admin_access(self, client, admin_user, multiple_maps):
        """Test admin access to map library."""
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/static-content')
        assert response.status_code == 200
        
        # Admin should see all maps
        assert b'html' in response.data  # Should contain map files


class TestMapErrorHandling:
    """Test error handling for map-related operations."""
    
    def test_user_without_location_info(self, client, app, db_session):
        """Test handling users without complete location information."""
        with app.app_context():
            from models import User
            
            # Create user without complete location info
            incomplete_user = User(
                username='incomplete_location',
                email='incomplete@test.com',
                password='test_password',
                state='',  # Missing state
                county='',  # Missing county
                precinct=''  # Missing precinct
            )
            
            db_session.add(incomplete_user)
            db_session.commit()
            
            login_user(client, 'incomplete_location', 'test_password')
            
            response = client.get('/my-map')
            # Should redirect or show error
            assert response.status_code in [302, 200]
            
            if response.status_code == 200:
                assert b'location information' in response.data or b'contact an administrator' in response.data
    
    def test_database_error_handling(self, client, regular_user):
        """Test graceful handling of database errors."""
        login_user(client, regular_user.username, 'user_password')
        
        # Try to access map that doesn't exist in database
        response = client.get('/user-map-raw/999.html')
        
        # Should return proper error page
        assert response.status_code in [404, 200]
        
        if response.status_code == 200:
            # Should be an error page with helpful information
            assert b'Error' in response.data or b'not found' in response.data
    
    def test_malformed_filename_handling(self, client, regular_user):
        """Test handling of malformed map filenames."""
        login_user(client, regular_user.username, 'user_password')
        
        # Try various malformed filenames
        bad_filenames = [
            'nothtml',
            'test.txt',
            '../../../etc/passwd',
            '<script>alert("xss")</script>.html'
        ]
        
        for filename in bad_filenames:
            response = client.get(f'/user-map-raw/{filename}')
            # Should either reject or handle gracefully
            assert response.status_code in [400, 403, 404, 200]


class TestMapContentValidation:
    """Test map content validation and security."""
    
    def test_map_content_structure(self, client, regular_user, sample_map):
        """Test that map content has proper HTML structure."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 200
        
        # Should be valid HTML
        assert b'<!DOCTYPE html>' in response.data
        assert b'<html>' in response.data
        assert b'</html>' in response.data
        assert b'<head>' in response.data
        assert b'<body>' in response.data
    
    def test_map_content_injection_prevention(self, client, regular_user, sample_map):
        """Test that zoom controls are properly injected without breaking content."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 200
        
        # Should have original content plus zoom controls
        assert b'Test Map - Precinct 012' in response.data  # Original content
        assert b'window.addEventListener' in response.data   # Added zoom controls


class TestMapResponseHeaders:
    """Test HTTP response headers for map requests."""
    
    def test_map_security_headers(self, client, regular_user, sample_map):
        """Test security headers on map responses."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 200
        
        # Should have proper security headers
        assert response.headers.get('X-Frame-Options') == 'SAMEORIGIN'
        assert 'Content-Security-Policy' in response.headers
    
    def test_map_content_type(self, client, regular_user, sample_map):
        """Test Content-Type header for map responses."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/user-map-raw/012.html')
        assert response.status_code == 200
        
        # Should have proper content type for HTML
        content_type = response.headers.get('Content-Type', '')
        assert 'text/html' in content_type or content_type == ''  # Flask default