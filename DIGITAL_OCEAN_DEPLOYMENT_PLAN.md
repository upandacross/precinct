# Digital Ocean Deployment Plan

> **Note**: This is a comprehensive deployment guide for the Precinct Campaign Analytics application on Digital Ocean.

---

## 📋 **Pre-Deployment Checklist**

- [ ] Digital Ocean account with Droplet created (recommended: 2GB RAM minimum)
- [ ] Domain name configured (optional but recommended)
- [ ] GitHub repository access configured
- [ ] Local database backup created
- [ ] Environment variables documented

---

## 🔑 **1. Initial Server Setup**

### Create Digital Ocean Droplet
```bash
# Recommended specifications:
# - OS: Ubuntu 22.04 LTS (latest stable)
# - RAM: 2GB minimum (4GB recommended for production)
# - Storage: 25GB SSD minimum
# - Region: Choose closest to your user base
```

### Secure Server Access
```bash
# On your local machine, create SSH key if not exists
ssh-keygen -t ed25519 -C "your_email@example.com"

# Add public key to Digital Ocean
# Settings → Security → SSH Keys → Add SSH Key
cat ~/.ssh/id_ed25519.pub
```

### Initial Server Configuration
```bash
# SSH into your droplet
ssh root@YOUR_DROPLET_IP

# Update system packages
apt update && apt upgrade -y

# Create non-root user with sudo privileges
adduser precinct
usermod -aG sudo precinct

# Copy SSH keys to new user
rsync --archive --chown=precinct:precinct ~/.ssh /home/precinct

# Test new user access (from local machine)
ssh precinct@YOUR_DROPLET_IP
```

---

## 🗄️ **2. Install PostgreSQL**

```bash
# Install PostgreSQL 15
sudo apt install -y postgresql postgresql-contrib postgresql-15-postgis-3

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE USER precinct WITH PASSWORD 'SECURE_PASSWORD_HERE';
CREATE DATABASE nc OWNER precinct;
\c nc
CREATE EXTENSION postgis;
GRANT ALL PRIVILEGES ON DATABASE nc TO precinct;
EOF

# Configure PostgreSQL for remote connections (if needed)
sudo nano /etc/postgresql/15/main/postgresql.conf
# Set: listen_addresses = 'localhost'  # Keep localhost only for security

# Configure authentication
sudo nano /etc/postgresql/15/main/pg_hba.conf
# Add: local   nc   precinct   scram-sha-256

# Restart PostgreSQL
sudo systemctl restart postgresql
```

---

## 📦 **3. Install Application Source**

### Install System Dependencies
```bash
# Install Python and required packages
sudo apt install -y python3.11 python3.11-venv python3-pip git curl

# Install UV package manager (modern Python dependency tool)
curl -LsSf https://astral.sh/uv/install.sh | sh
source $HOME/.cargo/env

# Install additional system libraries for geospatial support
sudo apt install -y gdal-bin libgdal-dev libgeos-dev libproj-dev
```

### Clone Repository
```bash
# Set up GitHub SSH access
ssh-keygen -t ed25519 -C "precinct@digitalocean"
cat ~/.ssh/id_ed25519.pub
# Add this key to GitHub: Settings → SSH and GPG keys → New SSH key

# Test GitHub connection
ssh -T git@github.com

# Clone repository
cd /home/precinct
git clone git@github.com:upandacross/precinct.git app
cd app
```

---

## ⚙️ **4. Configure Environment**

### Create .env File
```bash
# Create .env with production settings
cat > .env << 'EOF'
# Flask Configuration
FLASK_ENV=production
SECRET_KEY=$(python3 -c 'import os; print(os.urandom(32).hex())')
FLASK_DEBUG=False

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=precinct
POSTGRES_PASSWORD=SECURE_PASSWORD_HERE
POSTGRES_DB=nc
NC_DATABASE_URL=postgresql://precinct:SECURE_PASSWORD_HERE@localhost:5432/nc

# Security Settings
SESSION_COOKIE_SECURE=True
REMEMBER_COOKIE_SECURE=True
WTF_CSRF_ENABLED=True

# Production Settings
MAX_CONTENT_LENGTH=16777216
PERMANENT_SESSION_LIFETIME=14400
SESSION_TIMEOUT_MINUTES=30
EOF

# Secure .env file
chmod 600 .env
```

---

## 💾 **5. Database Import**

### Transfer Database Backup
```bash
# On your LOCAL machine, create database dump
cd /home/bren/Home/Projects/HTML_CSS/precinct
./app_administration/dump_nc_database.sh  # Or use pg_dump directly

# Compress the dump
gzip -c nc_database_dump.sql > nc_database_dump.sql.gz

# Transfer to Digital Ocean
scp nc_database_dump.sql.gz precinct@YOUR_DROPLET_IP:/home/precinct/app/
```

### Import Database
```bash
# On Digital Ocean server
cd /home/precinct/app

# Extract and import
gunzip nc_database_dump.sql.gz
psql -U precinct -d nc -f nc_database_dump.sql

# Verify import
psql -U precinct -d nc -c "\dt"  # List tables
psql -U precinct -d nc -c "SELECT COUNT(*) FROM maps;"  # Test query

# Clean up dump file
rm nc_database_dump.sql
```

---

## 🐍 **6. Install Python Dependencies**

```bash
cd /home/precinct/app

# Run UV setup (creates virtual environment and installs dependencies)
./setup-uv.sh

# Verify installation
source .venv/bin/activate
python -c "import flask; import sqlalchemy; import geoalchemy2; print('✅ Core dependencies installed')"
```

---

## 🧪 **7. Run Tests**

```bash
cd /home/precinct/app

# Run all tests using the test script
./run-tests.sh

# Or run tests manually with UV
uv run pytest test/ -v

# Expected output: 236/236 tests passing
# If tests fail, review error messages before proceeding
```

---

## 🚀 **8. Production Server Setup**

### Install Gunicorn (Production WSGI Server)
```bash
# Add gunicorn to project
uv add gunicorn

# Test gunicorn locally
uv run gunicorn -w 4 -b 127.0.0.1:8000 wsgi:app --timeout 120
# Press Ctrl+C to stop
```

### Create Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/precinct.service
```

Add this content:
```ini
[Unit]
Description=Precinct Campaign Analytics Application
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=precinct
Group=precinct
WorkingDirectory=/home/precinct/app
Environment="PATH=/home/precinct/app/.venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=/home/precinct/app/.venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /home/precinct/app/logs/access.log \
    --error-logfile /home/precinct/app/logs/error.log \
    --log-level info \
    wsgi:app

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Create logs directory
mkdir -p /home/precinct/app/logs

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable precinct
sudo systemctl start precinct

# Check status
sudo systemctl status precinct
```

---

## 🌐 **9. Install and Configure Nginx**

### Install Nginx
```bash
sudo apt install -y nginx

# Create Nginx configuration
sudo nano /etc/nginx/sites-available/precinct
```

Add this configuration:
```nginx
server {
    listen 80;
    server_name YOUR_DOMAIN_OR_IP;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Client body size limit (16MB to match app config)
    client_max_body_size 16M;

    # Static files
    location /static {
        alias /home/precinct/app/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts for long-running analytics
        proxy_connect_timeout 120s;
        proxy_send_timeout 120s;
        proxy_read_timeout 120s;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/precinct /etc/nginx/sites-enabled/

# Remove default site
sudo rm /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx
```

---

## 🔒 **10. SSL/TLS Setup (Optional but Recommended)**

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

---

## 🔧 **11. Firewall Configuration**

```bash
# Configure UFW firewall
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Check status
sudo ufw status
```

---

## 📊 **12. Monitoring and Maintenance**

### View Application Logs
```bash
# Systemd service logs
sudo journalctl -u precinct -f

# Application logs
tail -f /home/precinct/app/logs/error.log
tail -f /home/precinct/app/logs/access.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log
```

### Common Management Commands
```bash
# Restart application
sudo systemctl restart precinct

# Pull latest code and restart
cd /home/precinct/app
git pull origin main
uv sync  # Update dependencies
sudo systemctl restart precinct

# Database backup
pg_dump -U precinct nc | gzip > ~/backups/nc_$(date +%Y%m%d_%H%M%S).sql.gz
```

---

## ✅ **13. Post-Deployment Verification**

- [ ] Visit http://YOUR_DROPLET_IP and verify homepage loads
- [ ] Test user registration and login
- [ ] Test "View My Map" functionality
- [ ] Run analytics dashboard (if DASH_AVAILABLE)
- [ ] Check all 236 tests pass
- [ ] Verify database queries work correctly
- [ ] Test campaign messaging tools (if deployed)
- [ ] Monitor logs for errors during first 24 hours

---

## 🚨 **Troubleshooting**

### Application Won't Start
```bash
# Check service status
sudo systemctl status precinct

# View recent logs
sudo journalctl -u precinct -n 50

# Check database connection
psql -U precinct -d nc -c "SELECT 1;"

# Verify .env file exists and is readable
cat /home/precinct/app/.env
```

### Database Connection Issues
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Verify credentials in .env match database
# Check pg_hba.conf authentication method
```

### Nginx 502 Bad Gateway
```bash
# Ensure Gunicorn is running
sudo systemctl status precinct

# Check Gunicorn is listening on correct port
sudo netstat -tlnp | grep 8000
```

---

## 🚀 **Future Enhancements & Security Roadmap**

### Multi-Factor Authentication (MFA)
- [ ] **Research Auth0 Integration** - Implement enterprise-grade MFA
  - Provides 2FA via SMS, authenticator apps, and email
  - Handles user management and authentication flows
  - Consider Auth0 free tier (up to 7,000 active users)
  - Alternative: Implement TOTP-based MFA with `pyotp` library

### Additional Security Improvements
- [ ] **Rate Limiting** - Already implemented with Flask-Limiter, consider Redis backend for distributed limiting
- [ ] **Session Security** - Already implemented secure cookies, consider Redis for session storage
- [ ] **Database Security** - Implement database connection pooling with pgBouncer
- [ ] **Audit Logging** - Track all admin actions and sensitive operations
- [ ] **IP Whitelisting** - For admin panel access (optional)

### Performance Enhancements
- [ ] **CDN Integration** - Use Digital Ocean Spaces + CDN for static assets
- [ ] **Database Optimization** - Add indexes, query optimization, connection pooling
- [ ] **Caching Layer** - Implement Redis for session storage and caching
- [ ] **Load Balancing** - Scale to multiple Droplets with Load Balancer

### Monitoring & Analytics
- [ ] **Application Performance Monitoring** - Integrate New Relic or Datadog
- [ ] **Error Tracking** - Sentry integration for production error monitoring
- [ ] **Uptime Monitoring** - UptimeRobot or Pingdom for availability alerts
- [ ] **Log Aggregation** - Centralized logging with ELK stack or Digital Ocean's native tools

### Backup & Disaster Recovery
- [ ] **Automated Backups** - Digital Ocean automated snapshots (weekly recommended)
- [ ] **Database Backups** - Automated PostgreSQL backups to Digital Ocean Spaces
- [ ] **Disaster Recovery Plan** - Documented recovery procedures
- [ ] **Geographic Redundancy** - Multi-region deployment for high availability

---

## 📝 **Deployment Notes**

1. **Typo Correction**: Changed "DG" to "Digital Ocean" throughout (DG is unclear)
2. **PostgreSQL Restart**: PostgreSQL doesn't need restart to "pick up .env" - the app reads .env, not PostgreSQL
3. **Security**: Added security hardening (firewall, SSL, secure headers)
4. **Production Server**: Added Gunicorn + Nginx setup (Flask dev server is not production-safe)
5. **Service Management**: Added systemd service for auto-restart and process management
6. **Monitoring**: Added logging and troubleshooting sections
7. **Testing**: Expanded test verification before deployment
8. **Database Import**: Added proper compression and verification steps
