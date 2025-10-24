#!/bin/bash
# Enable maintenance mode

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTANCE_DIR="$SCRIPT_DIR/instance"

# Create instance directory if it doesn't exist
mkdir -p "$INSTANCE_DIR"

# Create maintenance mode flag file
touch "$INSTANCE_DIR/MAINTENANCE_MODE"

echo "✓ Maintenance mode ENABLED"
echo "  The application will now show the maintenance page to all users."
echo "  To disable maintenance mode, run: ./disable-maintenance.sh"
