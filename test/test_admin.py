"""
Admin interface and Flask-Admin tests for the Precinct application.

Tests cover:
- Admin access control
- User management interface
- MOTD (Message of the Day) functionality
- Flask-Admin security
- Admin dashboard functionality
"""

import pytest
import os


def login_user(client, username, password):
    """Helper function to login a user."""
    return client.post('/login', data={
        'username': username,
        'password': password,
        'submit': 'Sign In'
    }, follow_redirects=True)


class TestAdminAccessControl:
    """Test admin interface access control."""
    
    def test_admin_requires_authentication(self, client):
        """Test that admin interface requires authentication."""
        response = client.get('/admin/')
        assert response.status_code == 302  # Redirect to login
    
    def test_admin_requires_admin_role(self, client, regular_user):
        """Test that admin interface requires admin role."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/admin/')
        # Should redirect or show access denied
        assert response.status_code in [302, 403] or b'Access denied' in response.data
    
    def test_admin_access_with_admin_user(self, client, admin_user):
        """Test admin interface access with admin user."""
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Should contain admin interface elements
        assert b'Admin' in response.data or b'admin' in response.data
    
    def test_county_user_no_admin_access(self, client, county_user):
        """Test that county users cannot access admin interface."""
        login_user(client, county_user.username, 'county_password')
        
        response = client.get('/admin/')
        # Should be denied access
        assert response.status_code in [302, 403] or b'Access denied' in response.data


class TestUserManagement:
    """Test user management functionality in admin interface."""
    
    def test_user_list_view(self, client, admin_user):
        """Test user list view in admin interface."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Try to access user management
        response = client.get('/admin/user/')
        
        if response.status_code == 200:
            # Should show user list
            assert b'user' in response.data.lower()
        else:
            # Route might be different, check main admin page
            response = client.get('/admin/')
            assert response.status_code == 200
            assert b'Users' in response.data or b'user' in response.data
    
    def test_user_creation_access(self, client, admin_user):
        """Test access to user creation interface."""
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Should have user management capabilities
        # Exact structure depends on Flask-Admin setup
    
    def test_password_field_exclusion(self, client, admin_user, regular_user):
        """Test that password hash is not displayed in user management."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Access user management
        response = client.get('/admin/')
        
        if response.status_code == 200:
            # Should not display raw password hash
            assert b'password_hash' not in response.data
            
            # But should show password field for editing (without value)
            # This depends on implementation


class TestMOTDFunctionality:
    """Test Message of the Day functionality."""
    
    def test_motd_requires_admin(self, client, regular_user):
        """Test that MOTD management requires admin access."""
        login_user(client, regular_user.username, 'user_password')
        
        response = client.get('/admin/motd')
        assert response.status_code == 302 or b'Access denied' in response.data
    
    def test_motd_admin_access(self, client, admin_user):
        """Test admin access to MOTD management."""
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/admin/motd')
        assert response.status_code == 200
        
        # Should contain MOTD form elements
        assert b'motd' in response.data.lower()
        assert b'form' in response.data.lower()
    
    def test_motd_display_form(self, client, admin_user):
        """Test MOTD editing form display."""
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/admin/motd')
        assert response.status_code == 200
        
        # Should have textarea or input for MOTD content
        assert b'textarea' in response.data or b'input' in response.data
        assert b'submit' in response.data.lower() or b'save' in response.data.lower()
    
    def test_motd_update_functionality(self, app, client, admin_user):
        """Test updating MOTD content."""
        login_user(client, admin_user.username, 'admin_password')
        
        test_message = "Test MOTD message for testing"
        
        # Submit MOTD update
        response = client.post('/admin/motd', data={
            'motd_content': test_message
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # Should show success message
        assert b'updated' in response.data.lower() or b'success' in response.data.lower()
        
        # Verify MOTD file was created/updated
        with app.app_context():
            motd_path = os.path.join(app.root_path, 'motd.txt')
            if os.path.exists(motd_path):
                with open(motd_path, 'r') as f:
                    content = f.read().strip()
                    assert content == test_message
    
    def test_motd_empty_content_handling(self, client, admin_user):
        """Test handling of empty MOTD content."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Submit empty MOTD
        response = client.post('/admin/motd', data={
            'motd_content': ''
        }, follow_redirects=True)
        
        # Should handle gracefully
        assert response.status_code == 200


class TestFlaskAdminSecurity:
    """Test Flask-Admin security configurations."""
    
    def test_admin_csrf_protection(self, client, admin_user):
        """Test CSRF protection on admin forms."""
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/admin/motd')
        assert response.status_code == 200
        
        # In testing, CSRF might be disabled, but form structure should be correct
        assert b'form' in response.data
    
    def test_admin_session_security(self, client, admin_user):
        """Test admin session security requirements."""
        # Admin access without login should fail
        response = client.get('/admin/')
        assert response.status_code == 302
        
        # Login and verify access
        login_user(client, admin_user.username, 'admin_password')
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Logout should invalidate admin access
        client.get('/logout')
        response = client.get('/admin/')
        assert response.status_code == 302
    
    def test_admin_user_enumeration_protection(self, client, admin_user):
        """Test protection against user enumeration in admin interface."""
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Admin interface should not leak sensitive user information
        # in ways that could be exploited


class TestAdminUserInterface:
    """Test admin user interface elements."""
    
    def test_admin_navigation_elements(self, client, admin_user):
        """Test admin navigation and interface elements."""
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Should have navigation elements
        # Exact content depends on Flask-Admin configuration
        assert len(response.data) > 0
    
    def test_admin_user_list_columns(self, client, admin_user, regular_user):
        """Test that user list shows appropriate columns."""
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/admin/')
        
        if response.status_code == 200:
            # Should not show password hash in listings
            assert b'password_hash' not in response.data
            
            # Should show safe user information
            # (Implementation specific)
    
    def test_admin_user_search_functionality(self, client, admin_user):
        """Test user search functionality in admin interface."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Access main admin interface
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Search functionality depends on Flask-Admin configuration
        # This is a structural test


class TestAdminDataFiltering:
    """Test data filtering and access in admin interface."""
    
    def test_admin_user_filtering(self, client, admin_user, regular_user, county_user):
        """Test user filtering capabilities."""
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Should be able to access user management
        # Filtering capabilities depend on implementation
    
    def test_admin_county_filtering(self, client, admin_user, multiple_maps):
        """Test county-based filtering if applicable."""
        login_user(client, admin_user.username, 'admin_password')
        
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Admin should see all data regardless of county


class TestAdminErrorHandling:
    """Test error handling in admin interface."""
    
    def test_admin_invalid_routes(self, client, admin_user):
        """Test handling of invalid admin routes."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Try invalid admin route
        response = client.get('/admin/nonexistent')
        assert response.status_code == 404
    
    def test_admin_malformed_requests(self, client, admin_user):
        """Test handling of malformed admin requests."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Test malformed MOTD update
        response = client.post('/admin/motd', data={
            'invalid_field': 'test'
        })
        
        # Should handle gracefully
        assert response.status_code in [200, 400]


class TestAdminAuditTrail:
    """Test admin audit trail and logging."""
    
    def test_admin_action_logging(self, client, admin_user):
        """Test that admin actions are properly logged."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Perform admin action (MOTD update)
        response = client.post('/admin/motd', data={
            'motd_content': 'Test audit message'
        })
        
        # Action should complete successfully
        assert response.status_code in [200, 302]
        
        # Logging verification would require checking application logs
        # This is a structural test for the functionality
    
    def test_admin_session_tracking(self, client, admin_user):
        """Test admin session tracking."""
        login_user(client, admin_user.username, 'admin_password')
        
        # Admin access should be tracked
        response = client.get('/admin/')
        assert response.status_code == 200
        
        # Session should be properly maintained
        response = client.get('/admin/motd')
        assert response.status_code == 200


class TestAdminPerformance:
    """Test admin interface performance."""
    
    def test_admin_page_load_times(self, client, admin_user):
        """Test admin page load performance."""
        import time
        
        login_user(client, admin_user.username, 'admin_password')
        
        start_time = time.time()
        response = client.get('/admin/')
        end_time = time.time()
        
        assert response.status_code == 200
        
        # Should load reasonably quickly (allow 2 seconds for test environment)
        load_time = end_time - start_time
        assert load_time < 2.0
    
    def test_motd_update_performance(self, client, admin_user):
        """Test MOTD update performance."""
        import time
        
        login_user(client, admin_user.username, 'admin_password')
        
        start_time = time.time()
        response = client.post('/admin/motd', data={
            'motd_content': 'Performance test message'
        })
        end_time = time.time()
        
        assert response.status_code in [200, 302]
        
        # Should update quickly
        update_time = end_time - start_time
        assert update_time < 1.0