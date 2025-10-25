# Forsyth County Precinct Analysis Platform

A comprehensive Flask-based web application for Democratic organizing in Forsyth County, NC. Features precinct-level ballot matching analysis, flippable race identification, and automated candidate data tracking.

## Features

- **Ballot Matching Strategy**: Identify winnable races using data-driven flippability analysis
- **Precinct-Level Insights**: Turnout, partisan performance, and strategic targeting
- **Automated Candidate Tracking**: Daily monitoring of NC Board of Elections candidate filings
- **Flippable Race Analysis**: DVA (Democratic Vote Advantage) calculations for resource allocation
- **Role-Based Access**: Admin, county organizer, and public views

## Quick Start

### Installation

```bash
# Clone the repository
cd /home/bren/Home/Projects/HTML_CSS/precinct

# Set up Python environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your database credentials

# Initialize database
python init_db.py
```

### Running the Application

```bash
# Development
./run-app.sh

# Production (with Gunicorn)
./deploy-with-maintenance.sh
```

Access at: `http://localhost:5000`

---

## Automated Candidate Data Tracking

The platform automatically monitors NC Board of Elections for new candidate filings and generates ballot matching analysis reports.

### How It Works

1. **Election Schedule Parsing** (`parse_ncsbe_elections.py`)
   - Scrapes https://www.ncsbe.gov/voting/upcoming-election
   - Extracts election dates and filing periods
   - Saves to `doc/upcoming_elections.json`

2. **Candidate Data Updates** (`update_candidate_data.py`)
   - Downloads candidate CSV files during filing periods
   - Municipal: June-July in odd years (2025, 2027...)
   - State/Federal: December-February in even years (2026, 2028...)
   - Uses MD5 hash comparison to detect new data
   - Source: `https://s3.amazonaws.com/dl.ncsbe.gov/Elections/{year}/Candidate%20Filing/Candidate_Listing_{year}.csv`

3. **Ballot Matching Analysis** (`generate_ballot_matching_analysis.py`)
   - Triggered automatically when new candidate data detected
   - Municipal analysis: Uses partisan crossover data for flippability
   - State/Federal analysis: Matches returning candidates (Tier 1 rematch advantage)
   - Generates dated reports in `reports/` directory

4. **Orchestration** (`daily_election_check.sh`)
   - Runs all three steps in sequence
   - Logs to `/tmp/election_automation_YYYYMM.log`
   - Designed for cron scheduling

### Manual Usage

```bash
# Navigate to app_administration
cd app_administration

# Parse current election schedule
./parse_ncsbe_elections.py

# Check for new candidate data
./update_candidate_data.py

# Force download for specific year
./update_candidate_data.py --force 2025

# Generate analysis for current year
./generate_ballot_matching_analysis.py

# Generate analysis for specific year
./generate_ballot_matching_analysis.py 2026

# Run full automation pipeline
./daily_election_check.sh
```

### Automated Scheduling with Cron

To run the automation daily at 11PM on business days (Monday-Friday):

#### 1. Make Scripts Executable

```bash
cd app_administration
chmod +x daily_election_check.sh
chmod +x update_candidate_data.py
chmod +x parse_ncsbe_elections.py
chmod +x generate_ballot_matching_analysis.py
```

#### 2. Test the Automation

```bash
# Run the full pipeline manually first
./daily_election_check.sh

# Check the log
tail -f /tmp/election_automation_$(date +%Y%m).log
```

#### 3. Set Up Cron Job

```bash
# Edit your crontab
crontab -e

# Add this line (adjust path to your installation):
0 23 * * 1-5 /home/bren/Home/Projects/HTML_CSS/precinct/app_administration/daily_election_check.sh

# Explanation:
# 0        - Minute (0 = top of the hour)
# 23       - Hour (23 = 11 PM in 24-hour format)
# *        - Day of month (every day)
# *        - Month (every month)
# 1-5      - Day of week (1-5 = Monday-Friday)
```

#### 4. Verify Cron Setup

```bash
# List your cron jobs
crontab -l

# Monitor execution (logs are monthly)
tail -f /tmp/election_automation_*.log
```

#### 5. Email Notifications (Optional)

To receive email alerts when new data is detected, uncomment this line in `daily_election_check.sh`:

```bash
# echo "New candidate data analyzed for $YEAR" | mail -s "Ballot Matching Analysis Ready" your@email.com
```

Requires `mailutils` package:
```bash
sudo apt-get install mailutils
```

### Log Management

- **Location**: `/tmp/election_automation_YYYYMM.log`
- **Retention**: Automatically deletes logs older than 6 months
- **Monthly Rotation**: New log file each month
- **Manual Cleanup**: `find /tmp -name "election_automation_*.log" -delete`

### Filing Period Schedule

| Year | Type | Filing Period | Election Date |
|------|------|---------------|---------------|
| 2025 | Municipal | June 22 - July 7 | Sept 9, Oct 7, Nov 4 |
| 2026 | State/Federal | Dec 2025 - Feb 2026 | November 2026 |
| 2027 | Municipal | June-July 2027 | Fall 2027 |
| 2028 | State/Federal | Dec 2027 - Feb 2028 | November 2028 |

### Troubleshooting

**No new data detected during filing period:**
```bash
# Force a download
./update_candidate_data.py --force 2025

# Check election schedule
cat doc/upcoming_elections.json
```

**Analysis not generating:**
```bash
# Run manually with verbose output
python3 generate_ballot_matching_analysis.py 2025
```

**Cron job not running:**
```bash
# Check system cron service
sudo systemctl status cron

# Verify crontab entry
crontab -l

# Check system log
grep CRON /var/log/syslog
```

**Database connection errors:**
```bash
# Verify .env configuration
cat .env | grep DATABASE

# Test database connection
python3 -c "from config import Config; print(Config.SQLALCHEMY_DATABASE_URI)"
```

---

## Project Structure

```
precinct/
├── main.py                              # Flask application
├── models.py                            # Database models
├── config.py                            # Configuration
├── requirements.txt                     # Python dependencies
│
├── templates/                           # Jinja2 templates
│   ├── base.html
│   ├── flippable.html
│   └── flippable_analysis.html
│
├── static/                              # CSS, JavaScript, images
│
├── doc/                                 # Documentation and data
│   ├── Candidate_Listing_YYYY.csv      # NC BOE candidate data
│   ├── upcoming_elections.json          # Parsed election schedule
│   └── _BALLOT_MATCHING_STRATEGY.md    # Strategy document
│
├── reports/                             # Generated analysis reports
│   ├── FORSYTH_Municipal_Analysis_YYYYMMDD.md
│   └── FORSYTH_StateFederal_Analysis_YYYYMMDD.md
│
├── app_administration/                  # Admin tools and automation
│   ├── update_candidate_data.py         # Download NC BOE candidate files
│   ├── parse_ncsbe_elections.py         # Parse election schedule
│   ├── generate_ballot_matching_analysis.py # Generate ballot matching reports
│   ├── daily_election_check.sh          # Orchestration script
│   └── CANDIDATE_DATA_UPDATES.md        # Documentation
│
├── Automation Scripts (deprecated - moved to app_administration/)
└── (see app_administration/ for current scripts)
```

## Database Schema

### `flippable` table
- State and federal partisan races with candidate names
- Fields: `county`, `precinct`, `contest_name`, `dem_candidate`, `rep_candidate`, `dem_votes`, `oppo_votes`
- Used for DVA calculations and Tier 1 candidate matching

### `candidate_vote_results` table
- All election results including municipal races
- Fields: `county`, `precinct`, `contest_name`, `total_votes`, `winner_party`
- Municipal races have vote totals but no candidate names

## Contributing

See `CAMPAIGN_MESSAGE_TOOLKIT.md` and `FUTURE_ELECTION_STRATEGY.md` for organizing guidance.

## License

Proprietary - Forsyth County Democratic Party

---

## Support

For issues or questions:
- Check logs: `/tmp/election_automation_*.log`
- Review documentation: `CANDIDATE_DATA_UPDATES.md`
- Validate data: `./validate_flippable_table.py`
