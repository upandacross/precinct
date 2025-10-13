"""
Security enhancements for Flask application to prevent common attacks.
"""

from flask import request, abort, g
from functools import wraps
import time
from collections import defaultdict, deque
import re
import logging

# Rate limiting storage (in production, use Redis or database)
rate_limit_storage = defaultdict(lambda: deque())

# Security headers
SECURITY_HEADERS = {
    'X-Frame-Options': 'SAMEORIGIN',
    'X-Content-Type-Options': 'nosniff',
    'X-XSS-Protection': '1; mode=block',
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'Content-Security-Policy': (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' 'unsafe-eval' "
        "https://cdn.jsdelivr.net https://code.jquery.com https://cdnjs.cloudflare.com; "
        "style-src 'self' 'unsafe-inline' "
        "https://cdn.jsdelivr.net https://netdna.bootstrapcdn.com; "
        "img-src 'self' data: https:; "
        "font-src 'self' https://cdn.jsdelivr.net; "
        "connect-src 'self'; "
        "frame-ancestors 'self';"
    ),
    'Referrer-Policy': 'strict-origin-when-cross-origin',
    'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
}

# Suspicious patterns for path traversal and injection detection
SUSPICIOUS_PATTERNS = [
    r'\.\./',           # Path traversal
    r'\.\.\\',          # Windows path traversal
    r'<script',         # XSS
    r'javascript:',     # XSS
    r'vbscript:',       # XSS
    r'onload=',         # XSS
    r'onclick=',        # XSS
    r'onerror=',        # XSS
    r'union.*select',   # SQL injection
    r'drop.*table',     # SQL injection
    r'insert.*into',    # SQL injection
    r'delete.*from',    # SQL injection
    r'exec\(',          # Code injection
    r'eval\(',          # Code injection
    r'system\(',        # Command injection
    r'passthru\(',      # Command injection
]

def rate_limit(max_requests=60, window=60, per='ip'):
    """
    Rate limiting decorator to prevent brute force attacks.
    
    Args:
        max_requests: Maximum requests allowed
        window: Time window in seconds
        per: Rate limit per 'ip' or 'user'
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if per == 'ip':
                key = request.remote_addr
            elif per == 'user' and hasattr(g, 'current_user') and g.current_user.is_authenticated:
                key = f"user:{g.current_user.id}"
            else:
                key = request.remote_addr
            
            now = time.time()
            
            # Clean old entries
            cutoff = now - window
            while rate_limit_storage[key] and rate_limit_storage[key][0] < cutoff:
                rate_limit_storage[key].popleft()
            
            # Check rate limit
            if len(rate_limit_storage[key]) >= max_requests:
                logging.warning(f"Rate limit exceeded for {key}")
                abort(429)  # Too Many Requests
            
            # Add current request
            rate_limit_storage[key].append(now)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def validate_input(data, max_length=1000):
    """
    Validate input for suspicious patterns and length.
    """
    if not data:
        return True
    
    # Check length
    if len(str(data)) > max_length:
        return False
    
    # Check for suspicious patterns
    data_str = str(data).lower()
    for pattern in SUSPICIOUS_PATTERNS:
        if re.search(pattern, data_str, re.IGNORECASE):
            logging.warning(f"Suspicious pattern detected: {pattern} in {data}")
            return False
    
    return True

def secure_filename_validation(filename):
    """
    Validate filename for security issues.
    """
    if not filename:
        return False
    
    # Check for path traversal
    if '..' in filename or '/' in filename or '\\' in filename:
        return False
    
    # Check file extension
    allowed_extensions = {'.html', '.htm', '.txt', '.json', '.csv'}
    if not any(filename.lower().endswith(ext) for ext in allowed_extensions):
        return False
    
    # Check for suspicious patterns
    if not validate_input(filename, max_length=255):
        return False
    
    return True

def add_security_headers(response):
    """
    Add security headers to response.
    """
    for header, value in SECURITY_HEADERS.items():
        response.headers[header] = value
    return response

def validate_request_data():
    """
    Validate request data for security issues (less aggressive).
    """
    try:
        # Only validate suspicious form data
        if request.form:
            for key, value in request.form.items():
                if key not in ['csrf_token', 'remember_me'] and not validate_input(value):
                    logging.warning(f"Invalid form data detected: {key}={value[:50]}...")
                    abort(400)
        
        # Only validate suspicious query parameters
        if request.args:
            for key, value in request.args.items():
                # Skip common safe parameters
                if key not in ['next', 'page', 'per_page'] and not validate_input(value):
                    logging.warning(f"Invalid query parameter detected: {key}={value[:50]}...")
                    abort(400)
        
        # Validate JSON data
        if request.is_json:
            try:
                json_data = request.get_json()
                if isinstance(json_data, dict):
                    for key, value in json_data.items():
                        if not validate_input(value):
                            logging.warning(f"Invalid JSON data detected: {key}={str(value)[:50]}...")
                            abort(400)
            except Exception:
                # Invalid JSON, but let Flask handle it
                pass
                
    except Exception as e:
        # Don't break requests due to validation errors
        logging.error(f"Request validation error: {str(e)}")
        pass

def admin_required(f):
    """
    Decorator to require admin privileges.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        if not current_user.is_authenticated:
            abort(401)
        if not current_user.is_admin:
            logging.warning(f"Non-admin user {current_user.username} attempted to access admin function")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def county_or_admin_required(f):
    """
    Decorator to require county or admin privileges.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        if not current_user.is_authenticated:
            abort(401)
        if not (current_user.is_admin or current_user.is_county):
            logging.warning(f"User {current_user.username} attempted to access county function without privileges")
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def secure_path_validation(filename, allowed_directory):
    """
    Validate that filename is within allowed directory and secure.
    """
    import os
    
    if not secure_filename_validation(filename):
        return False
    
    # Construct full path
    full_path = os.path.join(allowed_directory, filename)
    
    # Resolve to absolute path to prevent traversal
    try:
        abs_allowed = os.path.abspath(allowed_directory)
        abs_requested = os.path.abspath(full_path)
        
        # Ensure the requested path is within the allowed directory
        if not abs_requested.startswith(abs_allowed + os.sep):
            return False
    except Exception:
        return False
    
    return True