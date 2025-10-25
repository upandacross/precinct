#!/bin/bash
# Cron-friendly wrapper for candidate data updates
# Add to crontab: 0 8 * * * /path/to/app_administration/daily_candidate_check.sh

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_ROOT"

# Activate virtual environment if needed
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run the update script from app_administration
python3 app_administration/update_candidate_data.py --analyze

# Log result
echo "Update check completed: $(date)" >> /tmp/candidate_updates.log
