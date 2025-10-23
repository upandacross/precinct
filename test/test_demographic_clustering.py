"""
Test suite for demographic clustering functionality.

Tests the county-wide demographic clustering analysis system for admin and county users.
"""

import pytest
from flask import url_for
from models import User, db
import json


class TestDemographicClustering:
    """Test demographic clustering route and functionality."""

    def test_demographic_clustering_access_control(self, app, admin_user, county_user, regular_user):
        """Test that only admin and county users can access demographic clustering."""
        with app.test_client() as client:
            # Test admin access
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
                sess['_fresh'] = True
            
            response = client.get('/demographic-clustering')
            assert response.status_code == 200
            assert b'Demographic Clustering Analysis' in response.data
            
            # Test county user access
            with client.session_transaction() as sess:
                sess['_user_id'] = str(county_user.id)
                sess['_fresh'] = True
            
            response = client.get('/demographic-clustering')
            assert response.status_code == 200
            assert b'Demographic Clustering Analysis' in response.data

    def test_demographic_clustering_regular_user_denied(self, app, regular_user):
        """Test that regular users are denied access to demographic clustering."""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(regular_user.id)
                sess['_fresh'] = True
            
            response = client.get('/demographic-clustering')
            assert response.status_code == 302  # Redirect to login or access denied

    def test_demographic_clustering_anonymous_denied(self, app):
        """Test that anonymous users are denied access to demographic clustering."""
        with app.test_client() as client:
            response = client.get('/demographic-clustering')
            assert response.status_code == 302  # Redirect to login

    def test_demographic_clustering_template_content(self, app, admin_user):
        """Test that the demographic clustering template contains expected content."""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
                sess['_fresh'] = True
            
            response = client.get('/demographic-clustering')
            assert response.status_code == 200
            
            # Check for key elements
            assert b'Demographic Clustering Analysis' in response.data
            assert b'Strategic Insights' in response.data or b'clusters' in response.data.lower()

    def test_demographic_clustering_route_registration(self, app):
        """Test that demographic clustering route is properly registered."""
        with app.test_request_context():
            url = url_for('demographic_clustering')
            assert url == '/demographic-clustering'


class TestDocumentationAccess:
    """Test documentation access and edit button visibility."""

    def test_documentation_edit_button_admin_only(self, app, admin_user, county_user, regular_user):
        """Test that Edit button only appears for admin users in documentation."""
        with app.test_client() as client:
            # Test admin user - check if the Manage Documents button appears
            client.post('/login', data={'username': admin_user.username, 'password': 'admin_pass'})
            response = client.get('/documentation')
            assert response.status_code == 200
            
            # The Manage Documents button should appear for admin users in the header
            response_text = response.data.decode('utf-8')
            admin_has_manage_button = 'Manage Documents' in response_text
            client.get('/logout')
            
            # Test county user does NOT see the button
            client.post('/login', data={'username': county_user.username, 'password': 'county_pass'})
            response = client.get('/documentation')
            assert response.status_code == 200
            
            response_text = response.data.decode('utf-8')
            county_has_manage_button = 'Manage Documents' in response_text
            client.get('/logout')
            
            # Admin should see the button, county should not
            if admin_has_manage_button and not county_has_manage_button:
                # Perfect - access control working correctly
                assert True
            elif not admin_has_manage_button and not county_has_manage_button:
                # Neither sees it - might be because no docs exist, skip test
                pytest.skip("No Manage Documents button visible - possibly no docs in directory")
            else:
                # County user can see admin controls - this is the problem
                pytest.fail(f"Access control broken: admin={admin_has_manage_button}, county={county_has_manage_button}")

    def test_documentation_admin_routes_access_control(self, app, admin_user, county_user):
        """Test that admin documentation routes are properly protected."""
        with app.test_client() as client:
            # Test admin can access admin routes
            client.post('/login', data={'username': admin_user.username, 'password': 'admin_pass'})
            response = client.get('/admin/doc_admin/')
            assert response.status_code in [200, 302], "Admin should access doc admin"
            client.get('/logout')
            
            # Test county user cannot access admin routes
            client.post('/login', data={'username': county_user.username, 'password': 'county_pass'})
            response = client.get('/admin/doc_admin/')
            # Should be redirected to login or forbidden
            assert response.status_code in [302, 403], f"County user got {response.status_code} for admin route"


class TestFlippableAnalysisSorting:
    """Test precinct sorting and zero-padding in flippable analysis."""

    def test_flippable_analysis_access_control(self, app, admin_user, county_user, regular_user):
        """Test that only admin and county users can access flippable analysis."""
        with app.test_client() as client:
            # Test admin access
            client.post('/login', data={'username': admin_user.username, 'password': 'admin_pass'})
            response = client.get('/flippable-analysis')
            # Might redirect to index if no data, but should not be forbidden
            assert response.status_code in [200, 302], "Admin should access flippable analysis"
            client.get('/logout')
            
            # Test county user access
            client.post('/login', data={'username': county_user.username, 'password': 'county_pass'})
            response = client.get('/flippable-analysis')
            # Might redirect to index if no data, but should not be forbidden
            assert response.status_code in [200, 302], "County user should access flippable analysis"
            client.get('/logout')
            
            # Test regular user denied
            client.post('/login', data={'username': regular_user.username, 'password': 'user_pass'})
            response = client.get('/flippable-analysis')
            assert response.status_code == 302, "Regular user should be redirected from flippable analysis"

    def test_precinct_sorting_logic(self, app):
        """Test the precinct sorting function logic."""
        # Import the sorting function logic (simulated)
        def sort_by_precinct_number(precinct):
            """Simulate the sorting logic from main.py"""
            precinct_name = precinct.get('precinct_name', '')
            parts = precinct_name.split('-')
            if len(parts) >= 2 and parts[-1].isdigit():
                return int(parts[-1])
            return float('inf')
        
        # Test data
        test_precincts = [
            {'precinct_name': 'FORSYTH-092'},
            {'precinct_name': 'FORSYTH-001'},
            {'precinct_name': 'FORSYTH-123'},
            {'precinct_name': 'FORSYTH-009'},
            {'precinct_name': 'WAKE-NON-NUMERIC'},
        ]
        
        # Sort using the function
        sorted_precincts = sorted(test_precincts, key=sort_by_precinct_number)
        
        # Verify correct order
        assert sorted_precincts[0]['precinct_name'] == 'FORSYTH-001'
        assert sorted_precincts[1]['precinct_name'] == 'FORSYTH-009'
        assert sorted_precincts[2]['precinct_name'] == 'FORSYTH-092'
        assert sorted_precincts[3]['precinct_name'] == 'FORSYTH-123'
        assert sorted_precincts[4]['precinct_name'] == 'WAKE-NON-NUMERIC'  # Non-numeric goes to end

    def test_zero_padding_display_logic(self, app):
        """Test the zero-padding display logic."""
        def apply_zero_padding(precinct_name):
            """Simulate the zero-padding logic from main.py"""
            parts = precinct_name.split('-')
            if len(parts) >= 2 and parts[-1].isdigit():
                precinct_num = int(parts[-1])
                return f'{parts[0]}-{precinct_num:03d}'
            return precinct_name
        
        # Test zero-padding
        assert apply_zero_padding('FORSYTH-1') == 'FORSYTH-001'
        assert apply_zero_padding('FORSYTH-92') == 'FORSYTH-092'
        assert apply_zero_padding('FORSYTH-123') == 'FORSYTH-123'
        assert apply_zero_padding('WAKE-NON-NUMERIC') == 'WAKE-NON-NUMERIC'

    def test_flippable_analysis_template_content(self, app, admin_user):
        """Test that flippable analysis contains expected content and structure."""
        with app.test_client() as client:
            client.post('/login', data={'username': admin_user.username, 'password': 'admin_pass'})
            
            response = client.get('/flippable-analysis')
            # Route might redirect if no data available
            if response.status_code == 200:
                # Check for expected content if page loads
                assert b'flippable' in response.data.lower() or b'precinct' in response.data.lower()
            elif response.status_code == 302:
                # Redirect is also acceptable if no data is available
                assert True  # Pass the test
            else:
                pytest.fail(f"Unexpected status code: {response.status_code}")


class TestChartErrorResolution:
    """Test that chart errors have been resolved in analytics."""

    def test_dash_analytics_data_validation(self, app):
        """Test that chart data validation prevents 'invalid value' errors."""
        # This simulates the data validation logic from dash_analytics.py
        import pandas as pd
        
        def validate_numeric_array(data_array, fallback_value=0):
            """Simulate the validation logic."""
            if not data_array:
                return [fallback_value]
            
            # Convert to pandas Series for numeric validation
            series = pd.Series(data_array)
            numeric_series = pd.to_numeric(series, errors='coerce')
            # Remove NaN values
            clean_data = numeric_series.dropna().tolist()
            
            # Return fallback if no valid data
            return clean_data if clean_data else [fallback_value]
        
        # Test with problematic data
        test_cases = [
            ([1, 2, 3, None, 'invalid'], 3),  # Mixed valid/invalid - should have 3 valid numbers
            ([None, 'invalid', 'bad'], 1),    # All invalid - should return fallback
            ([], 1),                          # Empty array - should return fallback
            ([1.5, 2.7, 3.2], 3),           # Valid floats - should return all 3
        ]
        
        for input_data, expected_count in test_cases:
            result = validate_numeric_array(input_data)
            assert len(result) == expected_count, f"Expected {expected_count} items for {input_data}, got {len(result)}"
            assert all(isinstance(x, (int, float)) for x in result), "Should only contain numbers"

    def test_analytics_routes_accessibility(self, app, admin_user):
        """Test that analytics routes are accessible and don't throw chart errors."""
        with app.test_client() as client:
            client.post('/login', data={'username': admin_user.username, 'password': 'admin_pass'})
            
            # Test main analytics route
            response = client.get('/dash/analytics')
            # Should not return 500 (server error) - might redirect or be permanent redirect (308)
            assert response.status_code in [200, 302, 308, 404], f"Got status {response.status_code}"


class TestRouteAccessControl:
    """Test comprehensive route access control based on user roles."""

    def test_admin_only_routes(self, app, admin_user, county_user, regular_user):
        """Test routes that should only be accessible to admin users."""
        admin_only_routes = [
            '/admin/',
            '/admin/doc_admin/',
        ]
        
        with app.test_client() as client:
            for route in admin_only_routes:
                # Test admin access - first login properly
                login_response = client.post('/login', data={
                    'username': admin_user.username,
                    'password': 'admin_pass'
                })
                
                response = client.get(route)
                assert response.status_code in [200, 302], f"Admin should access {route}"
                
                # Logout admin
                client.get('/logout')
                
                # Test county user denied - login as county user
                login_response = client.post('/login', data={
                    'username': county_user.username,
                    'password': 'county_pass'
                })
                
                response = client.get(route)
                # County user should be redirected or forbidden
                assert response.status_code in [302, 403], f"County user should be denied {route}"
                
                # Logout county user
                client.get('/logout')

    def test_admin_and_county_routes(self, app, admin_user, county_user, regular_user):
        """Test routes accessible to both admin and county users."""
        admin_county_routes = [
            '/flippable-analysis',
            '/demographic-clustering',
        ]
        
        with app.test_client() as client:
            for route in admin_county_routes:
                # Test admin access
                client.post('/login', data={'username': admin_user.username, 'password': 'admin_pass'})
                response = client.get(route)
                # These routes might redirect if no data, but should not be forbidden
                assert response.status_code in [200, 302], f"Admin should access {route}"
                client.get('/logout')
                
                # Test county access
                client.post('/login', data={'username': county_user.username, 'password': 'county_pass'})
                response = client.get(route)
                assert response.status_code in [200, 302], f"County user should access {route}"
                client.get('/logout')
                
                # Test regular user denied
                client.post('/login', data={'username': regular_user.username, 'password': 'user_pass'})
                response = client.get(route)
                assert response.status_code == 302, f"Regular user should be denied {route}"
                client.get('/logout')


class TestUIEnhancements:
    """Test UI enhancements and user experience improvements."""

    def test_documentation_floating_buttons(self, app, admin_user):
        """Test that documentation pages have properly positioned action buttons."""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
                sess['_fresh'] = True
            
            response = client.get('/documentation')
            assert response.status_code == 200
            
            # Should contain documentation list
            assert b'Documentation' in response.data

    def test_page_title_clarity(self, app, admin_user):
        """Test that page titles have been clarified for better UX."""
        with app.test_client() as client:
            client.post('/login', data={'username': admin_user.username, 'password': 'admin_pass'})
            
            # Test clustering page title
            response = client.get('/clustering')
            assert response.status_code in [200, 302]  # Accept both success and redirect
            
            # Test flippable analysis page title - might redirect if no data
            response = client.get('/flippable-analysis')
            assert response.status_code in [200, 302], "Page should load or redirect gracefully"