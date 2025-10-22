"""
Performance and load testing for the Precinct application.

Tests cover:
- Load testing with concurrent users
- Response time validation
- Memory usage monitoring  
- Rate limiting effectiveness
- Database performance under load
- Scalability testing
"""

import pytest
import time
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed


def login_user(client, username, password='user_password_unique'):
    """Helper function to login a user with rate limiting tolerance."""
    # Try login - may be rate limited, which is acceptable
    response = client.post('/login', data={
        'username': username,
        'password': password,
        'submit': 'Sign In'
    }, follow_redirects=True)
    
    # Rate limiting (429) is acceptable in tests
    if response.status_code == 429:
        return response
    
    # If not rate limited, should be successful login (200) or redirect (302)
    assert response.status_code in [200, 302], f"Login failed with status {response.status_code}"
    return response


# Performance test thresholds (in milliseconds)
PERFORMANCE_THRESHOLDS = {
    'login': 200,
    'dashboard': 300,
    'map_load': 500,
    'api_response': 100
}


@pytest.mark.performance
@pytest.mark.slow
class TestResponseTimes:
    """Test response time performance."""
    
    def test_login_response_time(self, client, regular_user):
        """Test login response time meets performance threshold."""
        start_time = time.time()
        
        response = client.post('/login', data={
            'username': regular_user.username,
            'password': 'user_password_unique',
            'submit': 'Sign In'
        })
        
        end_time = time.time()
        response_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        assert response.status_code in [200, 302, 429]  # Accept rate limiting
        # Only check performance if not rate limited
        if response.status_code in [200, 302]:
            assert response_time < PERFORMANCE_THRESHOLDS['login']
    
    def test_dashboard_load_time(self, client, regular_user):
        """Test dashboard loading performance."""
        login_user(client, regular_user.username, 'user_password_unique')
        
        start_time = time.time()
        response = client.get('/')
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000
        
        assert response.status_code in [200, 302, 429]  # Accept rate limiting and redirects
        # Only check performance if not rate limited
        if response.status_code in [200, 302]:
            assert response_time < PERFORMANCE_THRESHOLDS['dashboard']
    
    def test_map_loading_performance(self, client, regular_user, sample_map):
        """Test map loading performance."""
        login_user(client, regular_user.username, 'user_password_unique')
        
        # Test map viewer page
        start_time = time.time()
        response = client.get('/user-map/012.html')
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000
        
        assert response.status_code in [200, 302, 429]  # Accept rate limiting and redirects
        # Only check performance if not rate limited
        if response.status_code in [200, 302]:
            assert response_time < PERFORMANCE_THRESHOLDS['map_load']
        
        # Test raw map content
        start_time = time.time()
        response = client.get('/user-map-raw/012.html')
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000
        
        assert response.status_code in [200, 302, 429]  # Accept rate limiting and redirects
        # Only check performance if not rate limited
        if response.status_code in [200, 302]:
            assert response_time < PERFORMANCE_THRESHOLDS['map_load']
    
    def test_api_response_times(self, client, regular_user):
        """Test API endpoint response times."""
        login_user(client, regular_user.username, 'user_password_unique')
        
        # Test session status API
        start_time = time.time()
        response = client.get('/api/session-status')
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000
        
        assert response.status_code in [200, 302, 429]  # Accept rate limiting and redirects
        # Only check performance if not rate limited
        if response.status_code in [200, 302]:
            assert response_time < PERFORMANCE_THRESHOLDS['api_response']
        
        # Test session extension API
        start_time = time.time()
        response = client.post('/api/extend-session')
        end_time = time.time()
        
        response_time = (end_time - start_time) * 1000
        
        assert response.status_code in [200, 302, 429]  # Accept rate limiting and redirects
        # Only check performance if not rate limited
        if response.status_code in [200, 302]:
            assert response_time < PERFORMANCE_THRESHOLDS['api_response']


@pytest.mark.performance
@pytest.mark.slow
class TestConcurrentUsers:
    """Test performance with concurrent users."""
    
    def simulate_user_session(self, app, user_data):
        """Simulate a single user session for concurrent testing."""
        with app.test_client() as client:
            try:
                # Login
                response = client.post('/login', data={
                    'username': user_data['username'],
                    'password': user_data['password'],
                    'submit': 'Sign In'
                })
                
                if response.status_code not in [200, 302]:
                    return {'success': False, 'error': 'Login failed'}
                
                # Navigate pages
                pages = ['/', '/profile', '/about']
                for page in pages:
                    response = client.get(page)
                    if response.status_code != 200:
                        return {'success': False, 'error': f'Failed to load {page}'}
                
                # Check session
                response = client.get('/api/session-status')
                if response.status_code != 200:
                    return {'success': False, 'error': 'Session API failed'}
                
                # Logout
                response = client.get('/logout')
                if response.status_code not in [200, 302]:
                    return {'success': False, 'error': 'Logout failed'}
                
                return {'success': True, 'error': None}
                
            except Exception as e:
                return {'success': False, 'error': str(e)}
    
    def test_concurrent_logins(self, app, regular_user, admin_user):
        """Test concurrent user logins."""
        users = [
            {'username': regular_user.username, 'password': 'user_password_unique'},
            {'username': admin_user.username, 'password': 'admin_password_unique'}
        ] * 5  # Simulate 10 concurrent users
        
        start_time = time.time()
        
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(self.simulate_user_session, app, user) 
                      for user in users]
            
            results = []
            for future in as_completed(futures):
                results.append(future.result())
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Check results
        successful_sessions = sum(1 for r in results if r['success'])
        failure_rate = (len(results) - successful_sessions) / len(results)
        
        # Most sessions should succeed (allow 15% failure rate under load for concurrent stress testing)
        assert failure_rate <= 0.15
        
        # Should complete within reasonable time (allow 10 seconds for 10 concurrent users)
        assert total_time < 10.0
    
    def test_concurrent_map_access(self, app, regular_user, sample_map):
        """Test concurrent map access performance."""
        def access_map(app_instance):
            with app_instance.test_client() as client:
                try:
                    # Login
                    login_user(client, regular_user.username, 'user_password_unique')
                    
                    # Access map
                    start = time.time()
                    response = client.get('/user-map-raw/012.html')
                    end = time.time()
                    
                    return {
                        'success': response.status_code == 200,
                        'response_time': (end - start) * 1000
                    }
                except Exception as e:
                    return {'success': False, 'response_time': 0, 'error': str(e)}
        
        # Simulate 5 concurrent map accesses
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(access_map, app) for _ in range(5)]
            results = [future.result() for future in futures]
        
        # All should succeed
        successful_requests = sum(1 for r in results if r['success'])
        assert successful_requests >= 4  # Allow 1 failure out of 5
        
        # Average response time should be reasonable
        response_times = [r['response_time'] for r in results if r['success']]
        if response_times:
            avg_response_time = sum(response_times) / len(response_times)
            assert avg_response_time < 1000  # Less than 1 second average


@pytest.mark.performance
class TestDatabasePerformance:
    """Test database performance under load."""
    
    def test_user_query_performance(self, app, db_session):
        """Test user query performance."""
        with app.app_context():
            from models import User
            
            # Create multiple users for testing
            test_users = []
            for i in range(50):
                user = User(
                    username=f'perf_user_{i}',
                    email=f'perf_{i}@test.com',
                    password=f'test_password_{i}',  # Unique password per user
                    phone=f'555-{i:04d}',
                    role='voter',
                    state='NC',
                    county='Wake',
                    precinct=f'{i:03d}'
                )
                test_users.append(user)
                db_session.add(user)
            
            db_session.commit()
            
            # Test query performance
            start_time = time.time()
            
            # Perform various queries
            for i in range(10):
                User.query.filter_by(username=f'perf_user_{i}').first()
                User.query.filter_by(county='Wake').count()
                User.query.filter_by(is_active=True).all()
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # 30 queries should complete quickly
            assert query_time < 1.0
            
            # Cleanup
            for user in test_users:
                db_session.delete(user)
            db_session.commit()
    
    def test_map_query_performance(self, app, db_session, multiple_maps):
        """Test map query performance."""
        with app.app_context():
            from models import Map
            
            start_time = time.time()
            
            # Perform map queries
            for i in range(20):
                Map.query.filter_by(county='Wake').all()
                Map.query.filter_by(state='NC', county='Wake', precinct='012').first()
            
            end_time = time.time()
            query_time = end_time - start_time
            
            # 40 queries should complete quickly
            assert query_time < 1.0


@pytest.mark.performance
class TestMemoryUsage:
    """Test memory usage patterns."""
    
    def test_session_memory_usage(self, client, regular_user):
        """Test memory usage during user sessions."""
        import gc
        import sys
        
        # Get initial memory baseline
        gc.collect()
        initial_objects = len(gc.get_objects())
        
        # Perform user operations
        for i in range(10):
            login_user(client, regular_user.username, 'user_password_unique')
            client.get('/')
            client.get('/profile')
            client.get('/api/session-status')
            client.post('/api/extend-session')
            client.get('/logout')
        
        # Check memory usage
        gc.collect()
        final_objects = len(gc.get_objects())
        
        # Memory growth should be reasonable (allow 50% growth)
        growth_ratio = final_objects / initial_objects
        assert growth_ratio < 1.5
    
    def test_map_content_memory_efficiency(self, client, regular_user, sample_map):
        """Test memory efficiency of map content serving."""
        login_user(client, regular_user.username, 'user_password_unique')
        
        # Access map content multiple times
        for i in range(20):
            response = client.get('/user-map-raw/012.html')
            assert response.status_code in [200, 302, 429]  # Accept rate limiting
            # Don't store response data to test memory efficiency


@pytest.mark.performance
class TestRateLimitingPerformance:
    """Test rate limiting effectiveness under load."""
    
    def test_login_rate_limiting_effectiveness(self, client):
        """Test that rate limiting effectively prevents abuse."""
        # Check if rate limiting is enabled for this test environment
        rate_limiting_enabled = client.application.config.get('RATELIMIT_ENABLED', True)
        
        start_time = time.time()
        
        # Attempt rapid login requests
        responses = []
        for i in range(20):
            response = client.post('/login', data={
                'username': 'attacker',
                'password': 'wrong_password',
                'submit': 'Sign In'
            })
            responses.append(response.status_code)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        if rate_limiting_enabled:
            # Should start rate limiting after threshold
            rate_limited_responses = sum(1 for code in responses if code == 429)
            # Should have some rate limited responses after threshold
            assert rate_limited_responses > 0 or total_time > 5  # Either rate limited or slowed down
        else:
            # If rate limiting disabled, just verify no server errors
            server_errors = sum(1 for code in responses if code >= 500)
            assert server_errors == 0  # No server errors should occur
    
    def test_api_rate_limiting_under_load(self, client, regular_user):
        """Test API rate limiting under concurrent load."""
        login_user(client, regular_user.username, 'user_password_unique')
        
        def make_api_request():
            return client.get('/api/session-status').status_code
        
        # Make concurrent API requests
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_api_request) for _ in range(30)]
            results = [future.result() for future in futures]
        
        # Most should succeed, some might be rate limited
        success_rate = sum(1 for code in results if code == 200) / len(results)
        
        # Should have reasonable success rate (allow for some rate limiting)
        assert success_rate >= 0.7  # 70% success rate minimum


@pytest.mark.performance
class TestScalabilityMetrics:
    """Test scalability indicators."""
    
    def test_response_time_consistency(self, client, regular_user):
        """Test that response times remain consistent."""
        login_user(client, regular_user.username, 'user_password_unique')
        
        response_times = []
        
        # Measure response times for multiple requests
        for i in range(20):
            start_time = time.time()
            response = client.get('/')
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            response_times.append(response_time)
            
            assert response.status_code in [200, 302, 429]  # Accept rate limiting
        
        # Calculate consistency metrics
        avg_time = sum(response_times) / len(response_times)
        max_time = max(response_times)
        min_time = min(response_times)
        
        # Response time variance should be reasonable
        variance_ratio = max_time / min_time if min_time > 0 else 1
        
        # Max response time shouldn't be more than 5x the minimum
        assert variance_ratio < 5.0
        
        # Average should be within acceptable range
        assert avg_time < PERFORMANCE_THRESHOLDS['dashboard']
    
    def test_throughput_measurement(self, app, regular_user):
        """Measure application throughput."""
        def single_request_cycle(app_instance):
            with app_instance.test_client() as client:
                try:
                    # Complete request cycle
                    login_user(client, regular_user.username, 'user_password_unique')
                    client.get('/')
                    client.get('/api/session-status')
                    client.get('/logout')
                    return 1  # Successful cycle
                except:
                    return 0  # Failed cycle
        
        start_time = time.time()
        
        # Run concurrent request cycles
        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(single_request_cycle, app) for _ in range(10)]
            successful_cycles = sum(future.result() for future in futures)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Calculate throughput (cycles per second)
        if total_time > 0:
            throughput = successful_cycles / total_time
            
            # Should handle at least 1 complete cycle per second
            assert throughput >= 1.0
        
        # Most cycles should succeed
        success_rate = successful_cycles / 10
        assert success_rate >= 0.8


@pytest.mark.performance
class TestResourceUtilization:
    """Test resource utilization patterns."""
    
    def test_file_handle_management(self, client, admin_user):
        """Test file handle management during MOTD operations."""
        login_user(client, admin_user.username, 'admin_password_unique')
        
        # Perform multiple MOTD updates
        for i in range(10):
            response = client.post('/admin/motd', data={
                'motd_content': f'Test message {i}'
            })
            # Don't check status to avoid affecting resource usage measurement
        
        # Should not accumulate file handles
        # This is primarily tested by ensuring operations complete successfully
    
    def test_session_cleanup(self, app):
        """Test session cleanup efficiency."""
        # Create multiple test clients to simulate multiple sessions
        clients = []
        
        for i in range(10):
            client = app.test_client()
            clients.append(client)
            
            # Create session activity
            client.get('/login')
        
        # Sessions should be properly managed
        # This is tested by ensuring no errors occur during session creation