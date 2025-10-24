#!/bin/bash
# Disable maintenance mode

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
INSTANCE_DIR="$SCRIPT_DIR/instance"
MAINTENANCE_FILE="$INSTANCE_DIR/MAINTENANCE_MODE"

# Remove maintenance mode flag file
if [ -f "$MAINTENANCE_FILE" ]; then
    rm "$MAINTENANCE_FILE"
    echo "✓ Maintenance mode DISABLED"
    echo "  The application is now accessible to all users."
else
    echo "⚠ Maintenance mode was not enabled"
fi
