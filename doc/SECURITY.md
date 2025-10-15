# Flask Application Security Measures

This document outlines the comprehensive security measures implemented to prevent Flask application hacks.

## 🔒 Security Features Implemented

### 1. **Input Validation & Sanitization**
- **Path Traversal Protection**: Validates all filename inputs to prevent `../` attacks
- **SQL Injection Prevention**: Input validation with suspicious pattern detection  
- **XSS Protection**: Filters malicious scripts and JavaScript injections
- **Command Injection Prevention**: Blocks system(), exec(), eval() patterns
- **File Upload Security**: Validates file extensions and paths

### 2. **Rate Limiting**
- **Login Protection**: 5 attempts per 5 minutes to prevent brute force
- **API Endpoints**: Different limits per route type
- **Static Content**: 100-200 requests per minute based on usage
- **Admin Functions**: Lower limits for sensitive operations

### 3. **Security Headers**
- **X-Frame-Options**: DENY (prevents clickjacking)
- **X-Content-Type-Options**: nosniff (prevents MIME sniffing)
- **X-XSS-Protection**: Enabled with blocking mode
- **Strict-Transport-Security**: HSTS for HTTPS enforcement
- **Content-Security-Policy**: Restricts resource loading
- **Referrer-Policy**: Controls referrer information leakage

### 4. **Authentication & Authorization**
- **Role-based Access Control**: Admin, County, User permissions
- **Secure Password Hashing**: Uses bcrypt for password storage
- **Session Security**: HTTPOnly, Secure, SameSite cookies
- **Session Timeout**: 8-hour automatic logout
- **CSRF Protection**: WTForms CSRF tokens with 1-hour lifetime

### 5. **Logging & Monitoring**
- **Security Event Logging**: Failed logins, suspicious access attempts
- **File Access Auditing**: Logs all file access with user information
- **Rate Limit Violations**: Tracks and logs excessive requests
- **Error Logging**: Comprehensive error tracking for security analysis

### 6. **Production Security**
- **Debug Mode Disabled**: Prevents information disclosure
- **Secure Cookies**: HTTPS-only session cookies in production
- **Database Connection Security**: Connection pooling and pre-ping
- **Environment-based Config**: Separate dev/prod configurations

## 🛡️ Protection Against Common Attacks

### **SQL Injection**
- Input validation with pattern detection
- Parameterized queries (SQLAlchemy ORM)
- Input length limits

### **Cross-Site Scripting (XSS)**
- Content Security Policy headers
- Input validation for script tags
- Template auto-escaping (Jinja2)

### **Cross-Site Request Forgery (CSRF)**
- WTForms CSRF protection
- Token validation on all forms
- SameSite cookie attributes

### **Path Traversal**
- Filename validation
- Path normalization checks
- Directory restriction enforcement

### **Brute Force Attacks**
- Login rate limiting
- Account lockout mechanisms
- Failed attempt logging

### **Session Hijacking**
- Secure cookie configuration
- HTTPOnly flags
- Session timeout
- SameSite attributes

### **Information Disclosure**
- Custom error pages
- Debug mode disabled in production
- Security headers prevent information leaks

### **Clickjacking**

- X-Frame-Options: DENY
- Content Security Policy frame-ancestors

### **File Download Protection**

- **Multi-layer protection** against bulk downloading and unauthorized file access
- **Nginx-level blocking** of sensitive file extensions and directories
- **Flask route protection** with catch-all route blocking
- **User-agent filtering** to block known download tools and scrapers
- **Rate limiting** to prevent rapid bulk requests

#### File Protection Implementation

**1. Nginx Configuration Protection:**

```nginx
# Block sensitive files and directories
location ~ /\.(env|git|svn|hg) {
    deny all;
    return 404;
}

# Block Python source files
location ~ \.(py|pyc|pyo|pyd)$ {
    deny all;
    return 404;
}

# Block config and sensitive files
location ~ \.(ini|cfg|conf|log|sql|backup|bak|old|tmp)$ {
    deny all;
    return 404;
}

# Block sensitive directories
location ~ ^/(config|logs|backup|admin|\.venv|__pycache__|\.git) {
    deny all;
    return 404;
}
```

**2. Flask Application Protection:**

- **Catch-all route** blocks direct access to sensitive files
- **File extension filtering** prevents access to .py, .env, .cfg, etc.
- **Directory pattern blocking** protects `__pycache__`, `.venv`, config folders
- **User-agent blocking** stops wget, curl, scrapy, bots, crawlers

**3. What's Protected:**

- ❌ Source code files (.py, .pyc)
- ❌ Configuration files (.env, .ini, .cfg)
- ❌ Database files (.sql, .backup)
- ❌ Version control (.git, .svn)
- ❌ Virtual environments (`.venv`, `__pycache__`)
- ❌ Log files (.log, .tmp)

**4. What's Still Accessible:**

- ✅ Normal web pages through Flask routes
- ✅ Static assets (CSS, JS, images) from /static/
- ✅ User authentication and forms
- ✅ AJAX requests and API endpoints

## 📋 Security Checklist

✅ **Input Validation**: All user inputs validated and sanitized  
✅ **Authentication**: Secure login with rate limiting  
✅ **Authorization**: Role-based access control implemented  
✅ **Session Management**: Secure cookie configuration  
✅ **CSRF Protection**: Enabled on all forms  
✅ **Security Headers**: Comprehensive header set applied  
✅ **Error Handling**: Custom error pages without information leaks  
✅ **Logging**: Security events logged for monitoring  
✅ **Rate Limiting**: Protection against DoS/brute force  
✅ **File Security**: Path validation and extension checking  

## 🚀 Deployment Security

### **Environment Variables**
```bash
export SECRET_KEY="your-random-32-byte-secret-key"
export DATABASE_URL="your-secure-database-connection"
export FLASK_ENV="production"
export SESSION_COOKIE_SECURE="true"
export REMEMBER_COOKIE_SECURE="true"
```

### **HTTPS Configuration**
Ensure your reverse proxy (nginx/Apache) is configured with:
- TLS 1.2+ only
- Strong cipher suites
- HSTS headers
- Certificate validation

### **Database Security**
- Use strong database credentials
- Enable database connection encryption
- Regular security updates
- Backup encryption

## 📊 Monitoring & Alerts

Monitor the `security.log` file for:
- Failed login attempts
- Rate limit violations
- Suspicious file access patterns
- Invalid input attempts
- Error spikes

Set up alerts for unusual patterns in these security events.

## 🔄 Regular Security Maintenance

1. **Update Dependencies**: Regular package updates
2. **Security Audits**: Periodic code reviews
3. **Log Analysis**: Regular security log review
4. **Penetration Testing**: Annual security assessments
5. **Backup Verification**: Regular backup and recovery tests

## 📞 Security Incident Response

If a security incident is detected:
1. Check `security.log` for attack patterns
2. Review user access logs
3. Verify data integrity
4. Update security measures as needed
5. Document lessons learned

---
*Security measures implemented: October 2025*  
*Regular reviews recommended every 6 months*