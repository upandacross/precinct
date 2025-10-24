#!/bin/bash
# Deploy updates to Digital Ocean with maintenance mode

set -e  # Exit on error

echo "🚀 Starting deployment with maintenance mode..."

# Enable maintenance mode on server
echo "📋 Step 1: Enabling maintenance mode..."
ssh dg_precinct_root "touch /home/precinct/precinct/instance/MAINTENANCE_MODE"
echo "✓ Maintenance mode enabled"

sleep 2

# Pull latest code
echo "📋 Step 2: Pulling latest code from GitHub..."
ssh dg_precinct_root "cd /home/precinct/precinct && git pull"
echo "✓ Code updated"

# Install/update dependencies
echo "📋 Step 3: Installing dependencies..."
ssh dg_precinct_root "cd /home/precinct/precinct && source venv/bin/activate && pip install -r requirements.txt --quiet"
echo "✓ Dependencies installed"

# Restart the application
echo "📋 Step 4: Restarting application..."
ssh dg_precinct_root "sudo systemctl restart precinct"
echo "✓ Application restarted"

# Wait for app to start
echo "⏳ Waiting 5 seconds for application to start..."
sleep 5

# Disable maintenance mode
echo "📋 Step 5: Disabling maintenance mode..."
ssh dg_precinct_root "rm -f /home/precinct/precinct/instance/MAINTENANCE_MODE"
echo "✓ Maintenance mode disabled"

echo ""
echo "✅ Deployment complete!"
echo "🌐 Application is now live at https://138.197.96.240"
