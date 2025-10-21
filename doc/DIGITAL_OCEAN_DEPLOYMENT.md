# DigitalOcean Flask Deployment Guide

## **Deployment Options on DigitalOcean:**

### 1. **DigitalOcean App Platform** (Easiest - PaaS)
- **Best for**: Simple deployments, automatic scaling
- **Process**: Connect GitHub repo → automatic builds/deployments
- **Pros**: Zero server management, auto-scaling, SSL certificates
- **Cons**: Less control, higher cost for complex apps

### 2. **Droplets** (Most flexible - VPS)
- **Best for**: Full control, custom configurations
- **Setup**: Ubuntu server + Nginx + Gunicorn/uWSGI
- **Pros**: Full control, cost-effective, customizable
- **Cons**: Requires server management

### 3. **Docker on Droplets**
- **Best for**: Containerized deployments
- **Setup**: Docker + Docker Compose + reverse proxy
- **Pros**: Consistent environments, easy scaling
- **Cons**: Docker knowledge required

## **Recommended Setup for Your Flask App:**

Given your current setup with Waitress WSGI server, here's what I'd recommend:

### **Option 1: App Platform (Simplest)**
```yaml
# app.yaml
name: precinct-app
services:
- name: web
  source_dir: /
  github:
    repo: upandacross/precinct
    branch: main
  run_command: python wsgi.py
  environment_slug: python
  instance_count: 1
  instance_size_slug: basic-xxs
  envs:
  - key: FLASK_ENV
    value: production
  - key: DATABASE_URL
    value: ${db.DATABASE_URL}
databases:
- engine: PG
  name: db
  num_nodes: 1
  size: db-s-dev-database
```

### **Option 2: Droplet Setup (More Control)**

**1. Create Droplet:**
```bash
# Choose Ubuntu 22.04, $6/month droplet is fine for start
```

**2. Server Setup:**
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python, pip, nginx
sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib -y

# Create app user
sudo adduser precinct
sudo usermod -aG sudo precinct
```

**3. Deploy Your App:**
```bash
# Clone repo
git clone https://github.com/upandacross/precinct.git /var/www/precinct
cd /var/www/precinct

# Setup virtual environment
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # You'll need to create this
```

**4. Nginx Configuration:**
```nginx
# /etc/nginx/sites-available/precinct
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

**5. Systemd Service:**
```ini
# /etc/systemd/system/precinct.service
[Unit]
Description=Precinct Flask App
After=network.target

[Service]
User=precinct
Group=precinct
WorkingDirectory=/var/www/precinct
ExecStart=/var/www/precinct/.venv/bin/python wsgi.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## **Database Considerations:**

### **Managed Database (Recommended):**
- Use DigitalOcean's Managed PostgreSQL
- Automatic backups, updates, scaling
- Connection via DATABASE_URL environment variable

### **Self-hosted Database:**
- Install PostgreSQL on same droplet
- Configure backup scripts
- More cost-effective but requires maintenance

## **Environment Variables & Security:**

```bash
# Create .env file
FLASK_ENV=production
SECRET_KEY=your-super-secret-key
DATABASE_URL=postgresql://user:pass@host:port/dbname
```

## **SSL/HTTPS Setup:**
```bash
# Install Certbot for free SSL
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## **For Your Specific App:**

Looking at your current setup, you're already using:
- ✅ Waitress WSGI server
- ✅ PostgreSQL database  
- ✅ Proper Flask configuration

**Quick deployment steps would be:**

1. **Create requirements.txt:**
```bash
pip freeze > requirements.txt
```

2. **Set environment variables for production**
3. **Choose deployment method** (App Platform for simplicity)
4. **Set up SSH keys for GitHub access**
5. **Configure database connection**
6. **Set up domain and SSL**

## **Complete Droplet Deployment Steps:**

### Step 1: Create and Configure Droplet
1. Log into DigitalOcean
2. Create new droplet (Ubuntu 22.04, $6/month basic)
3. Add your SSH key
4. Connect via SSH: `ssh root@your-droplet-ip`

### Step 2: Setup SSH Keys for GitHub Access

**On the DigitalOcean Droplet:**

```bash
# Generate SSH key on the droplet
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Display the public key
cat ~/.ssh/id_rsa.pub

# Add GitHub to known hosts
ssh-keyscan -H github.com >> ~/.ssh/known_hosts
```

**Add Droplet's Public Key to GitHub:**

1. Copy the droplet's public key output from above
2. Go to GitHub → Settings → SSH and GPG keys → New SSH key
3. Paste the key and name it "DigitalOcean Droplet - Precinct App"

**Test SSH Connection:**

```bash
# Test GitHub SSH connection
ssh -T git@github.com

# Should see: "Hi upandacross! You've successfully authenticated..."
```

### Step 3: Initial Server Setup
```bash
# Update packages
apt update && apt upgrade -y

# Create non-root user
adduser precinct
usermod -aG sudo precinct
ufw allow OpenSSH
ufw enable

# Switch to new user
su - precinct
```

### Step 4: Install Dependencies
```bash
# Install required packages
sudo apt install python3-pip python3-venv nginx postgresql postgresql-contrib git curl -y

# Install uv (fast Python package manager)
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# Install Node.js (if needed)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt-get install -y nodejs
```

### Step 5: Clone and Setup Application
```bash
# Clone your repository using SSH
cd /var/www
sudo git clone git@github.com:upandacross/precinct.git
sudo chown -R precinct:precinct /var/www/precinct
cd /var/www/precinct

# Setup virtual environment with uv
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt
```

### Step 6: Configure PostgreSQL
```bash
# Switch to postgres user
sudo -u postgres psql

# Create database and user
CREATE DATABASE nc;
CREATE USER precinct WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE nc TO precinct;
\q

# Initialize your database
source .venv/bin/activate
python init_db.py  # Or whatever your db initialization script is
```

### Step 7: Configure Environment Variables
```bash
# Create environment file
sudo nano /var/www/precinct/.env

# Add these variables:
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-here
DATABASE_URL=postgresql://precinct@localhost/nc
```

### Step 8: Create Systemd Service
```bash
# Create service file
sudo nano /etc/systemd/system/precinct.service
```

Add the systemd configuration from above, then:

```bash
# Enable and start the service
sudo systemctl daemon-reload
sudo systemctl enable precinct
sudo systemctl start precinct
sudo systemctl status precinct
```

### Step 9: Configure Nginx
```bash
# Create nginx configuration
sudo nano /etc/nginx/sites-available/precinct
```

Add the nginx configuration from above, then:

```bash
# Enable the site
sudo ln -s /etc/nginx/sites-available/precinct /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 10: Configure Firewall
```bash
# Allow HTTP and HTTPS
sudo ufw allow 'Nginx Full'
sudo ufw allow ssh
sudo ufw enable
```

### Step 11: Setup SSL Certificate
```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate (replace with your domain)
sudo certbot --nginx -d your-domain.com

# Test auto-renewal
sudo certbot renew --dry-run
```

## **Monitoring and Maintenance:**

### Log Files to Monitor:
```bash
# Application logs
sudo journalctl -u precinct -f

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -f
```

### Regular Maintenance Tasks:
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Restart services if needed
sudo systemctl restart precinct
sudo systemctl restart nginx

# Monitor disk space
df -h

# Monitor memory usage
free -h
```

## **Scaling Considerations:**

### Horizontal Scaling:
- Use DigitalOcean Load Balancer
- Deploy multiple droplets
- Use managed database for shared state

### Vertical Scaling:
- Resize droplet as needed
- Monitor CPU and memory usage
- Consider using DigitalOcean monitoring

### Database Scaling:
- Start with managed PostgreSQL
- Consider read replicas for heavy read workloads
- Use connection pooling (pgbouncer)

## **Cost Optimization:**

### Development Environment:
- $6/month basic droplet
- Shared CPU instance
- 1GB RAM, 25GB SSD

### Production Environment:
- $18/month droplet (2GB RAM)
- Regular CPU instance
- Managed database ($15/month minimum)
- Load balancer if needed ($12/month)

### Estimated Monthly Costs:
- **Development**: $6-12/month
- **Small Production**: $30-50/month
- **Medium Production**: $75-150/month

## **Backup Strategy:**

### Automated Backups:
```bash
# Database backup script
#!/bin/bash
pg_dump -h localhost -U precinct nc > backup_$(date +%Y%m%d_%H%M%S).sql
```

### DigitalOcean Features:
- Automated droplet snapshots
- Managed database backups
- Volume snapshots for additional storage

## **Security Best Practices:**

1. **Keep system updated**
2. **Use SSH keys only (disable password auth)**
3. **Configure firewall properly**
4. **Use HTTPS everywhere**
5. **Regular security audits**
6. **Monitor logs for suspicious activity**
7. **Use strong passwords and secrets**
8. **Regular backup testing**

## **Troubleshooting Common Issues:**

### Application Won't Start:
```bash
# Check service status
sudo systemctl status precinct

# View logs
sudo journalctl -u precinct -n 50

# Check if port is in use
sudo netstat -tulpn | grep :8080
```

### Database Connection Issues:
```bash
# Test database connection
psql -h localhost -U precinct -d nc

# Check PostgreSQL status
sudo systemctl status postgresql
```

### Nginx Issues:
```bash
# Test nginx configuration
sudo nginx -t

# Check nginx logs
sudo tail -f /var/log/nginx/error.log
```

This guide should get your Flask application successfully deployed to DigitalOcean!