#!/bin/bash
#
# Daily Election Data Check and Analysis
#
# This script orchestrates the complete automation pipeline:
# 1. Parse latest election schedule from NCSBE
# 2. Check for new candidate data
# 3. Generate ballot matching analysis if new data detected
#
# Designed for cron execution at 11PM on business days (Mon-Fri)
# Crontab: 0 23 * * 1-5 /path/to/app_administration/daily_election_check.sh
#

set -e  # Exit on error

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
LOG_FILE="/tmp/election_automation_$(date +%Y%m).log"
VENV_DIR="$PROJECT_ROOT/.venv"

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "========================================="
log "Starting Daily Election Check"
log "========================================="

# Activate virtual environment if it exists
if [ -d "$VENV_DIR" ]; then
    log "Activating virtual environment..."
    source "$VENV_DIR/bin/activate"
else
    log "WARNING: No virtual environment found at $VENV_DIR"
fi

cd "$PROJECT_ROOT"

# Step 1: Parse election schedule
log ""
log "Step 1: Parsing NCSBE election schedule..."
if python3 app_administration/parse_ncsbe_elections.py >> "$LOG_FILE" 2>&1; then
    log "✓ Election schedule updated"
else
    log "✗ Failed to parse election schedule (non-critical, continuing...)"
fi

# Step 2: Check for new candidate data
log ""
log "Step 2: Checking for new candidate data..."

# Capture the output to detect if new data was downloaded
UPDATE_OUTPUT=$(python3 app_administration/update_candidate_data.py 2>&1)
echo "$UPDATE_OUTPUT" >> "$LOG_FILE"

# Check if new data was detected
if echo "$UPDATE_OUTPUT" | grep -q "New data detected"; then
    log "✓ NEW CANDIDATE DATA DETECTED!"
    
    # Step 3: Generate ballot matching analysis
    log ""
    log "Step 3: Generating ballot matching analysis..."
    
    # Extract year from the update output or use current year
    YEAR=$(date +%Y)
    
    if python3 app_administration/generate_ballot_matching_analysis.py "$YEAR" >> "$LOG_FILE" 2>&1; then
        log "✓ Ballot matching analysis generated successfully"
        
        # Optional: Send notification (uncomment if you set up email)
        # echo "New candidate data analyzed for $YEAR" | mail -s "Ballot Matching Analysis Ready" your@email.com
        
    else
        log "✗ Failed to generate analysis"
        exit 1
    fi
    
elif echo "$UPDATE_OUTPUT" | grep -q "already current"; then
    log "✓ Candidate data is current (no changes)"
    
elif echo "$UPDATE_OUTPUT" | grep -q "Not currently in an active filing period"; then
    log "ℹ No active filing period"
    
else
    log "✗ Unexpected update script output"
fi

log ""
log "========================================="
log "Daily Election Check Complete"
log "Log: $LOG_FILE"
log "========================================="

# Cleanup old log files (keep last 6 months)
find /tmp -name "election_automation_*.log" -mtime +180 -delete 2>/dev/null || true

exit 0
