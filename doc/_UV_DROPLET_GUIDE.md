# Using UV on DigitalOcean Droplet

This guide covers how to install and use `uv` (the fast Python package manager) on your DigitalOcean droplet for deploying Flask applications.

## **What is UV?**

`uv` is an extremely fast Python package installer and resolver, written in Rust. It's designed to be a drop-in replacement for pip and pip-tools, with significantly better performance.

### **Benefits of UV:**
- **10-100x faster** than pip for package installation
- **Better dependency resolution** and conflict detection
- **Consistent behavior** across platforms
- **Drop-in replacement** for pip commands
- **Built-in virtual environment management**

## **Installing UV on Ubuntu Droplet**

### **Method 1: Official Installer (Recommended)**

```bash
# Install uv using the official installer
curl -LsSf https://astral.sh/uv/install.sh | sh

# Reload your shell configuration
source ~/.bashrc

# Verify installation
uv --version
```

### **Method 2: Using pip (if you prefer)**

```bash
# Install uv via pip
pip install uv

# Verify installation
uv --version
```

### **Method 3: Pre-built Binary**

```bash
# Download and install pre-built binary
curl -LsSf https://github.com/astral-sh/uv/releases/latest/download/uv-installer.sh | sh
```

## **Basic UV Usage**

### **Virtual Environment Management**

```bash
# Create a new virtual environment
uv venv .venv

# Create with specific Python version
uv venv --python 3.11 .venv

# Activate virtual environment
source .venv/bin/activate

# Deactivate
deactivate
```

### **Package Installation**

```bash
# Install packages from requirements.txt
uv pip install -r requirements.txt

# Install individual packages
uv pip install flask flask-sqlalchemy

# Install with specific versions
uv pip install flask==3.1.2

# Install development dependencies
uv pip install pytest pytest-flask --dev
```

### **Package Management**

```bash
# List installed packages
uv pip list

# Show package information
uv pip show flask

# Freeze current environment
uv pip freeze

# Generate requirements.txt
uv pip freeze > requirements.txt

# Uninstall packages
uv pip uninstall package-name

# Upgrade packages
uv pip install --upgrade package-name
```

## **Flask Application Deployment with UV**

### **Complete Deployment Workflow**

```bash
# 1. Navigate to your project directory
cd /var/www/precinct

# 2. Create virtual environment with uv
uv venv .venv

# 3. Activate virtual environment
source .venv/bin/activate

# 4. Install dependencies
uv pip install -r requirements.txt

# 5. Verify installation
uv pip list

# 6. Test your application
python wsgi.py
```

### **Environment-Specific Installation**

```bash
# Production environment
uv pip install -r requirements.txt --no-dev

# Development environment with testing tools
uv pip install -r requirements.txt
uv pip install pytest pytest-flask pytest-cov --dev

# Minimal production install (no cache)
uv pip install -r requirements.txt --no-cache-dir
```

## **Advanced UV Features**

### **Dependency Resolution**

```bash
# Show dependency tree
uv pip tree

# Resolve dependencies without installing
uv pip compile requirements.in

# Check for dependency conflicts
uv pip check

# Show outdated packages
uv pip list --outdated
```

### **Cache Management**

```bash
# Show cache information
uv cache info

# Clear cache
uv cache clean

# Show cache directory
uv cache dir
```

### **Performance Optimizations**

```bash
# Use system site-packages (faster for system packages)
uv pip install --system -r requirements.txt

# Parallel installation (default, but can be controlled)
uv pip install --concurrent-downloads 10 -r requirements.txt

# Skip dependency checks for faster installation
uv pip install --no-deps package-name
```

## **Droplet-Specific Configurations**

### **System-Level Installation**

If you need to install packages system-wide on your droplet:

```bash
# Install packages globally (be cautious)
sudo uv pip install --system package-name

# Install in user directory
uv pip install --user package-name
```

### **Memory-Constrained Environments**

For smaller droplets with limited RAM:

```bash
# Reduce parallel downloads to save memory
export UV_CONCURRENT_DOWNLOADS=2

# Or set in your shell profile
echo "export UV_CONCURRENT_DOWNLOADS=2" >> ~/.bashrc
```

### **Disk Space Management**

```bash
# Install without keeping cache
uv pip install -r requirements.txt --no-cache-dir

# Clean cache after installation
uv pip install -r requirements.txt && uv cache clean
```

## **Integration with Systemd Services**

### **Service File Configuration**

When creating systemd services, ensure uv-installed packages are accessible:

```ini
# /etc/systemd/system/precinct.service
[Unit]
Description=Precinct Flask App
After=network.target

[Service]
User=precinct
Group=precinct
WorkingDirectory=/var/www/precinct
Environment=PATH=/var/www/precinct/.venv/bin:/usr/bin:/bin
ExecStart=/var/www/precinct/.venv/bin/python wsgi.py
Restart=always

[Install]
WantedBy=multi-user.target
```

### **Environment Variables**

```bash
# Set UV-specific environment variables
export UV_CACHE_DIR=/var/cache/uv
export UV_CONCURRENT_DOWNLOADS=4
export UV_NO_PROGRESS=1  # Disable progress bars in scripts

# Add to your deployment script
echo "export UV_NO_PROGRESS=1" >> /var/www/precinct/.env
```

## **Troubleshooting UV on Droplet**

### **Common Issues and Solutions**

#### **Issue: UV not found after installation**
```bash
# Solution: Reload shell or add to PATH
source ~/.bashrc
# or
export PATH="$HOME/.local/bin:$PATH"
```

#### **Issue: Permission denied errors**
```bash
# Solution: Use proper ownership
sudo chown -R precinct:precinct /var/www/precinct
sudo -u precinct uv pip install -r requirements.txt
```

#### **Issue: Memory errors during installation**
```bash
# Solution: Reduce concurrent downloads
UV_CONCURRENT_DOWNLOADS=1 uv pip install -r requirements.txt
```

#### **Issue: Network timeouts**
```bash
# Solution: Increase timeout and retry
uv pip install -r requirements.txt --timeout 300 --retries 5
```

### **Debugging Commands**

```bash
# Check UV configuration
uv config

# Verbose installation for debugging
uv pip install -r requirements.txt --verbose

# Show what would be installed without installing
uv pip install -r requirements.txt --dry-run

# Check environment
uv pip check --verbose
```

## **Comparison: UV vs PIP Performance**

### **Speed Benchmarks (Typical Flask App)**

| Operation | pip | uv | Speedup |
|-----------|-----|-----|---------|
| Fresh install (62 packages) | ~45s | ~4s | 11x faster |
| Reinstall (cached) | ~25s | ~1s | 25x faster |
| Dependency resolution | ~8s | ~0.3s | 27x faster |
| requirements.txt generation | ~2s | ~0.1s | 20x faster |

### **Memory Usage**

- **pip**: 50-100MB RAM during installation
- **uv**: 20-40MB RAM during installation
- **Benefit**: Better for smaller droplets

## **Best Practices for Production**

### **1. Pin Your Dependencies**

Always use exact versions in production:

```txt
# requirements.txt
flask==3.1.2
flask-sqlalchemy==3.1.1
psycopg2-binary==2.9.11
```

### **2. Use Lock Files**

For even more reproducible builds:

```bash
# Generate lock file
uv pip compile requirements.in --output-file requirements.txt

# Install from lock file
uv pip sync requirements.txt
```

### **3. Separate Dev/Prod Dependencies**

```bash
# requirements.in
flask
flask-sqlalchemy
psycopg2-binary

# requirements-dev.in
-r requirements.in
pytest
pytest-flask
black
flake8

# Generate separate files
uv pip compile requirements.in
uv pip compile requirements-dev.in
```

### **4. Health Check Script**

```bash
#!/bin/bash
# health_check.sh
cd /var/www/precinct
source .venv/bin/activate
uv pip check || exit 1
python -c "import main; print('App imports successfully')" || exit 1
echo "Health check passed"
```

## **Automation Scripts**

### **Deployment Script**

```bash
#!/bin/bash
# deploy.sh
set -e

echo "🚀 Starting deployment with UV..."

# Navigate to project directory
cd /var/www/precinct

# Pull latest code
git pull origin main

# Activate virtual environment
source .venv/bin/activate

# Update dependencies with UV
echo "📦 Installing dependencies..."
uv pip install -r requirements.txt

# Run health checks
echo "🔍 Running health checks..."
uv pip check
python -c "from main import create_app; app = create_app(); print('✅ App created successfully')"

# Restart services
echo "🔄 Restarting services..."
sudo systemctl restart precinct
sudo systemctl restart nginx

echo "✅ Deployment completed successfully!"
```

### **Update Script**

```bash
#!/bin/bash
# update_deps.sh
set -e

cd /var/www/precinct
source .venv/bin/activate

echo "📋 Current packages:"
uv pip list --outdated

echo "⬆️ Updating packages..."
uv pip install --upgrade -r requirements.txt

echo "💾 Saving new requirements..."
uv pip freeze > requirements.txt

echo "✅ Dependencies updated!"
```

## **Monitoring UV Performance**

### **Installation Metrics**

```bash
# Time installation
time uv pip install -r requirements.txt

# Monitor with system resources
htop &
uv pip install -r requirements.txt

# Check cache usage
uv cache info
```

### **Log Analysis**

```bash
# Enable verbose logging
UV_LOG_LEVEL=debug uv pip install -r requirements.txt

# Monitor installation progress
uv pip install -r requirements.txt --progress
```

## **Migration from PIP to UV**

### **Step-by-Step Migration**

```bash
# 1. Backup current environment
pip freeze > pip_requirements.txt

# 2. Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.bashrc

# 3. Create new environment with UV
uv venv .venv-new
source .venv-new/bin/activate

# 4. Install with UV
uv pip install -r pip_requirements.txt

# 5. Verify everything works
python -c "import main; print('Migration successful')"

# 6. Replace old environment
rm -rf .venv
mv .venv-new .venv
```

### **Validation Checklist**

- [ ] All packages installed correctly
- [ ] Application starts without errors
- [ ] All tests pass
- [ ] Performance is improved
- [ ] Service files updated with correct paths

## **UV Configuration Files**

### **pyproject.toml Integration**

```toml
# pyproject.toml
[project]
name = "precinct"
version = "1.0.0"
dependencies = [
    "flask>=3.1.0",
    "flask-sqlalchemy>=3.1.0",
    "psycopg2-binary>=2.9.0",
    "waitress>=3.0.0"
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-flask>=1.3.0",
    "black>=23.0.0"
]

[tool.uv]
dev-dependencies = [
    "pytest>=8.0.0",
    "pytest-flask>=1.3.0"
]
```

### **UV Configuration**

```toml
# uv.toml
[tool.uv]
cache-dir = "/var/cache/uv"
concurrent-downloads = 4
no-progress = true
```

This comprehensive guide should help you leverage UV's speed and reliability for your Flask application deployment on DigitalOcean droplets!