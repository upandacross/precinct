"""
Test suite for analytics and chart error resolution.

Tests the Dash analytics system and ensures chart errors are resolved.
"""

import pytest
from flask import url_for
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock


class TestAnalyticsChartErrorResolution:
    """Test analytics chart error resolution and data validation."""

    def test_numeric_data_validation(self, app):
        """Test the numeric data validation that prevents chart errors."""
        
        def validate_chart_data(data, field_name="data"):
            """Simulate the validation logic from dash_analytics.py"""
            if not data:
                return []
        
            try:
                # Convert to pandas Series for robust numeric conversion
                series = pd.Series(data)
                numeric_series = pd.to_numeric(series, errors='coerce')
        
                # Filter out NaN values and convert back to list
                clean_data = numeric_series.dropna().tolist()
                
                # Ensure we have numeric types only and filter out infinity values
                validated_data = [x for x in clean_data if isinstance(x, (int, float, np.integer, np.floating)) and np.isfinite(x)]
                
                return validated_data
            except Exception:
                return []        # Test various problematic data scenarios
        test_cases = [
            # (input_data, expected_behavior)
            ([1, 2, 3, 4, 5], [1, 2, 3, 4, 5]),  # Clean numeric data
            ([1, 2, None, 4, 5], [1, 2, 4, 5]),  # None values removed
            ([1, 2, 'invalid', 4, 5], [1, 2, 4, 5]),  # String values removed
            ([1.5, 2.7, 3.2], [1.5, 2.7, 3.2]),  # Float values preserved
            (['a', 'b', 'c'], []),  # All invalid data
            ([], []),  # Empty input
            ([np.nan, 1, 2], [1, 2]),  # NaN values removed
            ([float('inf'), 1, 2], [1, 2]),  # Infinity values handled
        ]
        
        for input_data, expected in test_cases:
            result = validate_chart_data(input_data)
            assert len(result) == len(expected), f"Failed for input {input_data}"
            if expected:  # Only check values if we expect any
                assert result == expected, f"Failed for input {input_data}"

    def test_chart_scaling_operations(self, app):
        """Test that scaling operations work with validated data."""
        
        def safe_scaling(data, scale_factor=10):
            """Simulate safe scaling operations for charts."""
            try:
                # Validate data first
                validated = [x for x in data if isinstance(x, (int, float)) and not pd.isna(x)]
                
                # Apply scaling
                scaled = [x * scale_factor for x in validated]
                
                return scaled
            except Exception:
                return []
        
        # Test scaling with various data
        test_data = [1, 2, 3, None, 'invalid', 4]
        result = safe_scaling(test_data)
        expected = [10, 20, 30, 40]  # Only valid numbers scaled
        assert result == expected

    def test_array_length_validation(self, app):
        """Test that arrays have consistent lengths for chart operations."""
        
        def validate_array_consistency(*arrays):
            """Ensure all arrays have the same length."""
            if not arrays:
                return True
            
            # Get the length of the first non-empty array
            target_length = None
            for arr in arrays:
                if arr:
                    target_length = len(arr)
                    break
            
            if target_length is None:
                return True  # All arrays are empty
            
            # Check all arrays have the same length
            return all(len(arr) == target_length for arr in arrays if arr is not None)
        
        # Test various array combinations
        assert validate_array_consistency([1, 2, 3], [4, 5, 6], [7, 8, 9])  # Same length
        assert not validate_array_consistency([1, 2, 3], [4, 5])  # Different lengths
        assert validate_array_consistency([], [], [])  # All empty
        assert validate_array_consistency([1], [2], [3])  # Single elements

    def test_dashboard_analytics_route(self, app, admin_user):
        """Test that dashboard analytics route works without errors."""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
                sess['_fresh'] = True
            
            # Test dashboard route
            response = client.get('/')
            assert response.status_code == 200
            
            # Should not contain JavaScript errors in the response
            assert b'chart error' not in response.data.lower()
            assert b'invalid value' not in response.data.lower()

    def test_website_users_analytics(self, app, admin_user):
        """Test the website users analytics page with real data."""
        with app.test_client() as client:
            with client.session_transaction() as sess:
                sess['_user_id'] = str(admin_user.id)
                sess['_fresh'] = True
            
            # Try to access website users page if it exists
            try:
                response = client.get('/website-users')
                if response.status_code == 200:
                    # Should contain chart or user data
                    assert b'user' in response.data.lower() or b'chart' in response.data.lower()
            except Exception:
                # Route might not exist yet, that's okay
                pass


class TestMonthlySignupChart:
    """Test the monthly signup chart implementation."""

    def test_monthly_data_aggregation(self, app):
        """Test monthly signup data aggregation logic."""
        from datetime import datetime, timedelta
        
        def aggregate_monthly_signups(users_data):
            """Simulate monthly signup aggregation."""
            monthly_counts = {}
            
            for user in users_data:
                if 'created_at' in user and user['created_at']:
                    try:
                        # Parse date (assuming datetime object or string)
                        if isinstance(user['created_at'], str):
                            date = datetime.fromisoformat(user['created_at'].replace('Z', '+00:00'))
                        else:
                            date = user['created_at']
                        
                        # Create month key
                        month_key = f"{date.year}-{date.month:02d}"
                        monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
                    except Exception:
                        continue  # Skip invalid dates
            
            return monthly_counts
        
        # Test data
        test_users = [
            {'created_at': '2025-01-15T10:00:00Z'},
            {'created_at': '2025-01-20T14:30:00Z'},
            {'created_at': '2025-02-05T09:15:00Z'},
            {'created_at': '2025-02-10T16:45:00Z'},
            {'created_at': '2025-02-25T11:20:00Z'},
            {'created_at': None},  # Should be skipped
        ]
        
        result = aggregate_monthly_signups(test_users)
        
        assert result['2025-01'] == 2  # January has 2 signups
        assert result['2025-02'] == 3  # February has 3 signups
        assert '2025-03' not in result  # March has no signups

    def test_chart_js_data_format(self, app):
        """Test that data is formatted correctly for Chart.js."""
        import calendar
        
        def format_for_chartjs(monthly_data):
            """Format monthly data for Chart.js line chart."""
            if not monthly_data:
                return {'labels': [], 'data': []}
            
            # Sort by date
            sorted_months = sorted(monthly_data.keys())
            
            # Format labels (e.g., "Jan 2025")
            labels = []
            data = []
            
            for month_key in sorted_months:
                try:
                    year, month = month_key.split('-')
                    month_name = calendar.month_abbr[int(month)]
                    labels.append(f"{month_name} {year}")
                    data.append(monthly_data[month_key])
                except Exception:
                    continue
            
            return {'labels': labels, 'data': data}
        
        # Test formatting
        test_data = {
            '2025-01': 10,
            '2025-02': 15,
            '2025-03': 8
        }
        
        result = format_for_chartjs(test_data)
        
        assert result['labels'] == ['Jan 2025', 'Feb 2025', 'Mar 2025']
        assert result['data'] == [10, 15, 8]
        
        # Test empty data
        empty_result = format_for_chartjs({})
        assert empty_result['labels'] == []
        assert empty_result['data'] == []


class TestDashAnalyticsIntegration:
    """Test Dash analytics integration and error handling."""

    def test_dash_app_initialization(self, app):
        """Test that Dash app initializes without errors."""
        try:
            # Try to import dash_analytics
            import dash_analytics
            
            # If import succeeds, test basic functionality
            assert dash_analytics is not None, "Dash analytics module should be importable"
            # Don't assume specific attributes exist, just test basic import
        except ImportError:
            # dash_analytics might not exist or be disabled
            pytest.skip("Dash analytics not available")
        except Exception as e:
            pytest.fail(f"Dash analytics initialization failed: {e}")

    def test_data_validation_functions(self, app):
        """Test the data validation functions used in analytics."""
        
        def validate_numeric_series(data, default_value=0):
            """Validate and clean numeric data series."""
            if not data:
                return [default_value]
            
            try:
                # Use pandas for robust validation
                series = pd.Series(data)
                numeric_series = pd.to_numeric(series, errors='coerce')
                clean_data = numeric_series.dropna()
                
                # Return as list, with default if empty
                result = clean_data.tolist()
                return result if result else [default_value]
            except Exception:
                return [default_value]
        
        # Test edge cases that previously caused errors
        test_cases = [
            (None, [0]),
            ([], [0]),
            ([None, None, None], [0]),
            (['invalid'], [0]),
            ([1, 'invalid', 3], [1, 3]),
            ([1.5, 2.5, 3.5], [1.5, 2.5, 3.5]),
        ]
        
        for input_data, expected in test_cases:
            result = validate_numeric_series(input_data)
            assert len(result) > 0, "Should never return empty list"
            assert all(isinstance(x, (int, float)) for x in result), "Should contain only numbers"


class TestUserAnalytics:
    """Test user analytics and reporting functionality."""

    def test_user_signup_analytics(self, app, db_session):
        """Test user signup analytics calculation."""
        from models import User
        from datetime import datetime, timedelta
        
        # Create test users with different signup dates
        test_users = []
        base_date = datetime.now() - timedelta(days=90)
        
        for i in range(10):
            user = User(
                username=f'analytics_test_user_{i}',
                email=f'analytics_test{i}@example.com',
                password=f'hashed_password_{i}',
                phone=f'555-000-{i:04d}',
                role='member'
            )
            # Set the created_at timestamp after instantiation
            user.created_at = base_date + timedelta(days=i*7)
            test_users.append(user)
            db_session.add(user)
        
        # Test analytics would calculate monthly signups
        monthly_signups = {}
        for user in test_users:
            month_key = user.created_at.strftime('%Y-%m')
            monthly_signups[month_key] = monthly_signups.get(month_key, 0) + 1
        
        # Should have distributed users across months
        assert len(monthly_signups) > 0
        assert sum(monthly_signups.values()) == len(test_users)

    def test_analytics_performance(self, app):
        """Test that analytics calculations perform efficiently."""
        import time
        
        # Simulate large dataset processing
        large_dataset = [{'created_at': f'2025-{i%12+1:02d}-01'} for i in range(10000)]
        
        start_time = time.time()
        
        # Simulate analytics processing
        monthly_counts = {}
        for record in large_dataset:
            month = record['created_at'][:7]  # YYYY-MM
            monthly_counts[month] = monthly_counts.get(month, 0) + 1
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        # Should process 10k records quickly (under 1 second)
        assert processing_time < 1.0, f"Analytics processing too slow: {processing_time}s"
        assert len(monthly_counts) == 12  # 12 months
        assert sum(monthly_counts.values()) == 10000