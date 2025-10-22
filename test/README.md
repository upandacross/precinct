# Precinct Application Test Suite

## Overview

This comprehensive test suite covers all major components of the Precinct Flask application including authentication, security, database operations, map functionality, and API endpoints.

## Test Structure

```
test/
├── README.md                           # This documentation
├── LAST_RUN_RESULTS.md                 # Latest test execution results with timestamps
├── conftest.py                         # Pytest configuration and shared fixtures
├── test_auth.py                        # Authentication and authorization tests
├── test_security.py                    # Security headers and HSTS tests
├── test_database.py                    # Database model and operations tests
├── test_maps.py                        # Map functionality and access control tests
├── test_api.py                         # API endpoints and session management tests
├── test_admin.py                       # Admin interface and Flask-Admin tests
├── test_integration.py                 # End-to-end integration tests
├── test_performance.py                 # Load testing and performance validation
├── test_clustering_integration.py      # Clustering analysis integration tests
├── test_custom_form_*.py               # Flask-Admin custom form tests
├── test_flask_admin_user.py            # Flask-Admin user creation tests
└── run_all_tests.py                    # Test runner script
```

## Prerequisites

### Dependencies Management

**IMPORTANT**: This project uses `uv` for dependency management. 

#### Installing Test Dependencies

```bash
# Install all dependencies (including test dependencies)
uv sync

# Add a new test dependency
uv add --group test package_name

# Add a new regular dependency
uv add package_name
```

**DO NOT use `pip install`** - always use `uv add` to ensure proper dependency tracking and virtual environment management.

#### Current Test Dependencies
- `pytest`: Core testing framework
- `pytest-flask`: Flask-specific testing utilities
- `pytest-cov`: Coverage reporting
- `beautifulsoup4`: HTML parsing for form analysis
- `requests-mock`: HTTP request mocking
- `selenium`: Browser automation (if needed)

## Running Tests

### Full Test Suite (Recommended)

```bash
# Run all tests with verbose output
python -m pytest test/ -v

# Run all tests with coverage
python -m pytest test/ --cov=. --cov-report=html
```

### Individual Test Categories

```bash
# Authentication tests
python -m pytest test/test_auth.py -v

# Security tests (includes HSTS and security headers)
python -m pytest test/test_security.py -v

# Database tests (includes User model with required phone/role)
python -m pytest test/test_database.py -v

# Map functionality tests
python -m pytest test/test_maps.py -v

# API tests
python -m pytest test/test_api.py -v

# Admin interface tests
python -m pytest test/test_admin.py -v

# Integration tests
python -m pytest test/test_integration.py -v

# Performance tests
python -m pytest test/test_performance.py -v

# Clustering integration tests
python test/test_clustering_integration.py
```

### All Tests

```bash
# Run all tests
python test/run_all_tests.py

# Or using pytest directly
python -m pytest test/ -v

# With coverage report
python -m pytest test/ --cov=. --cov-report=html --cov-report=term
```

## Test Categories

### 1. Authentication Tests (`test_auth.py`)
- **Login/Logout functionality**
  - Valid credential authentication
  - Invalid credential rejection
  - Session management
  - Remember me functionality
- **User registration and management**
- **Password hashing verification**
- **Rate limiting on login attempts**
- **Access control for different user roles**

### 2. Security Tests (`test_security.py`)
- **HSTS header validation**
  - Proper max-age setting
  - includeSubDomains directive
- **Content Security Policy (CSP)**
  - XSS protection validation
  - Frame ancestors policy
- **X-Frame-Options header**
  - SAMEORIGIN setting for iframe compatibility
- **Security headers presence**
  - X-Content-Type-Options
  - Referrer-Policy
  - Permissions-Policy
- **Session security**
  - Session timeout functionality
  - Secure session management

### 3. Database Tests (`test_database.py`)
- **User model operations**
  - CRUD operations
  - Password hashing/verification
  - User role management
- **Map model operations**
  - Map content storage/retrieval
  - Geographic filtering (state/county/precinct)
- **Database connection handling**
- **Transaction integrity**
- **NC database integration**

### 4. Map Tests (`test_maps.py`)
- **Map access controls**
  - User-specific map access
  - Admin/county user permissions
  - Precinct-based filtering
- **Map content delivery**
  - Database content retrieval
  - Error handling for missing maps
  - iframe compatibility
- **Zoom control functionality**
- **Map viewing modes** (navbar, raw, new tab)

### 5. API Tests (`test_api.py`)
- **Session management endpoints**
  - `/api/session-status`
  - `/api/extend-session`
- **Response format validation**
- **Authentication requirements**
- **Rate limiting compliance**
- **Error handling**

### 6. Admin Interface Tests (`test_admin.py`)
- **Admin access control**
- **User management interface**
- **MOTD (Message of the Day) functionality**
- **Flask-Admin security**
- **Admin dashboard functionality**

### 7. Integration Tests (`test_integration.py`)
- **Complete user workflows**
  - Login → Dashboard → Map viewing
  - Admin workflows
  - County user workflows
- **Cross-component interactions**
- **End-to-end security validation**
- **Browser-based testing (Selenium)**

### 8. Performance Tests (`test_performance.py`)
- **Load testing**
  - Concurrent user simulation
  - Database performance under load
- **Response time validation**
- **Memory usage monitoring**
- **Rate limiting effectiveness**

### 9. Clustering Integration Tests (`test_clustering_integration.py`)
- **ClusteringService functionality**
  - CSV data loading validation
  - Precinct clustering data processing
- **User-specific insights generation**
  - Mock user precinct assignments
  - Strategic priority classifications
- **Chart data preparation**
  - Cluster distribution calculations
  - API endpoint data formatting
- **Summary statistics validation**
  - Total precinct counts
  - High-priority precinct identification

**Note:** This test requires `precinct_clustering_results.csv` to be generated by running `clustering_analysis.py` first.

## Test Configuration

### Environment Setup

Tests use a separate SQLite database (`test.db`) to avoid affecting production data:

```python
# Test configuration automatically set in conftest.py
TESTING = True
SQLALCHEMY_DATABASE_URI = 'sqlite:///test.db'
WTF_CSRF_ENABLED = False  # Disabled for testing convenience
SECRET_KEY = 'test-secret-key'
```

### Fixtures Available

- `app`: Flask application instance
- `client`: Test client for making requests
- `db`: Database instance
- `admin_user`: Pre-created admin user
- `regular_user`: Pre-created regular user
- `county_user`: Pre-created county-level user

## Test Data

Tests use controlled test data including:
- **Test users** with various permission levels
- **Sample map data** for different states/counties/precincts
- **Mock external dependencies**

## Continuous Integration

Tests are designed to run in CI environments:

```bash
# CI-friendly test run
python -m pytest test/ --tb=short --maxfail=5 --disable-warnings
```

## Coverage Goals

Target test coverage:
- **Authentication**: 100%
- **Security**: 95%
- **Database operations**: 90%
- **Map functionality**: 90%
- **API endpoints**: 95%
- **Overall application**: 85%+

## Troubleshooting

### Common Issues

1. **Database conflicts**: Ensure test database is properly isolated
2. **Port conflicts**: Tests use different ports to avoid conflicts
3. **Missing dependencies**: Install all test requirements
4. **Permission issues**: Ensure proper file system permissions

### Debug Mode

Run tests with verbose output and debug information:

```bash
python -m pytest test/ -v -s --tb=long
```

### Test Database Reset

If tests fail due to database state issues:

```bash
rm -f test.db  # Remove test database
python -m pytest test/ -v  # Recreate during test run
```

## Contributing

When adding new features:
1. Write tests FIRST (TDD approach)
2. Ensure all existing tests pass
3. Maintain coverage standards
4. Update this documentation

## Security Testing Notes

- Tests validate security headers in development mode
- Production security testing should be done separately
- Never commit real credentials or production data
- Use mock services for external dependencies

## Performance Benchmarks

Expected performance baselines:
- Login response: < 200ms
- Map loading: < 500ms
- API endpoints: < 100ms
- Database queries: < 50ms

Run performance tests to validate these benchmarks remain within acceptable ranges.