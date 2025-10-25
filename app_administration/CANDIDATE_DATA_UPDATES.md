# NC Board of Elections Candidate Data Updates

## Overview

The NC State Board of Elections (NCSBE) provides candidate listing files during filing periods. These files are updated **daily during the filing period** and need to be downloaded regularly to maintain current data.

**Current Data Files:**
- `doc/Candidate_Listing_2020.csv` (3.8M) - Historical
- `doc/Candidate_Listing_2021.csv` (608K) - Historical
- `doc/Candidate_Listing_2022.csv` (2.6M) - Historical
- `doc/Candidate_Listing_2023.csv` (772K) - Historical
- `doc/Candidate_Listing_2024.csv` (3.9M) - Historical
- `doc/Candidate_Listing_2025.csv` (755K) - **ACTIVE - Needs daily updates during filing**

---

## Filing Periods to Watch

### Municipal Elections (Odd Years)
- **Filing Period:** Typically mid-June to early July
- **Election Date:** First Tuesday after first Monday in November (odd years)
- **2025 Filing:** June-July 2025
- **2025 Election:** November 4, 2025

### State/Federal Elections (Even Years)
- **Filing Period:** Typically December-February
- **Primary:** March (Presidential) or May (Congressional)
- **General Election:** First Tuesday after first Monday in November (even years)
- **2026 Filing:** December 2025 - February 2026
- **2026 Primary:** May 2026
- **2026 General:** November 3, 2026

---

## Automated Update Script ⭐ **RECOMMENDED**

### Quick Start

The `update_candidate_data.py` script automatically:
- ✅ Knows when filing periods are active
- ✅ Downloads from the correct URL for each year
- ✅ Detects if data has changed (MD5 hash comparison)
- ✅ Verifies data quality
- ✅ Provides summary analysis

**Usage:**

```bash
# During filing period - automatically checks and updates
./update_candidate_data.py

# Force download for specific year (outside filing period)
./update_candidate_data.py --force 2025
./update_candidate_data.py --force 2026

# With analysis output
./update_candidate_data.py --analyze
```

**Example Output:**
```
✓ Active filing period detected: Municipal Election Filing
  Target year: 2025
  Period type: municipal

ℹ️  Existing file found: Candidate_Listing_2025.csv
✓ Download complete
✓ File updated: doc/Candidate_Listing_2025.csv

DATA SUMMARY
Total candidates: 1,234
FORSYTH COUNTY:
  Candidates: 51
  Contests: 12
```

### Setup Daily Cron Job (During Filing Periods)

```bash
# Edit crontab
crontab -e

# Add daily check at 8 AM
0 8 * * * /home/bren/Home/Projects/HTML_CSS/precinct/daily_candidate_check.sh
```

The script is smart enough to only download when in filing periods:
- **Municipal:** June-July (odd years)
- **State/Federal:** December-February (even years)

---

## Download Process

### Option 1: Manual Download (if automated script fails)

1. **Visit NCSBE Candidate Portal:**
   - URL: https://s3.amazonaws.com/dl.ncsbe.gov/Elections/
   - Look for current year folder (e.g., `2025/`, `2026/`)

2. **Download Latest CSV:**
   - Navigate to appropriate year folder
   - Download `Candidate_Listing_YYYY.csv` or similar file
   - Check timestamp at bottom of PDF version to verify freshness

3. **Save to Project:**
   ```bash
   # Save to doc/ directory with year in filename
   cp ~/Downloads/Candidate_Listing_2026.csv doc/Candidate_Listing_2026.csv
   ```

4. **Verify Data:**
   ```bash
   # Check file size and encoding
   wc -l doc/Candidate_Listing_2026.csv
   file doc/Candidate_Listing_2026.csv
   
   # Preview data
   head -20 doc/Candidate_Listing_2026.csv
   ```

### Option 2: Automated Script (For regular updates)

Create a script to download and check for updates:

```bash
#!/bin/bash
# update_candidate_data.sh

YEAR=$(date +%Y)
URL="https://s3.amazonaws.com/dl.ncsbe.gov/Elections/${YEAR}/data/Candidate_Listing_${YEAR}.csv"
DEST="doc/Candidate_Listing_${YEAR}.csv"

# Download latest file
echo "Downloading candidate data for ${YEAR}..."
wget -q -O "${DEST}.tmp" "$URL"

# Check if download succeeded
if [ $? -eq 0 ]; then
    # Compare with existing file
    if [ -f "$DEST" ]; then
        if ! cmp -s "$DEST" "${DEST}.tmp"; then
            echo "✓ New data available - updating file"
            mv "${DEST}.tmp" "$DEST"
            echo "File updated: $(date)"
            
            # Optional: Run analysis
            # python3 analyze_new_candidates.py
        else
            echo "No changes - file is current"
            rm "${DEST}.tmp"
        fi
    else
        echo "✓ Initial download complete"
        mv "${DEST}.tmp" "$DEST"
    fi
else
    echo "✗ Download failed"
    rm -f "${DEST}.tmp"
    exit 1
fi
```

Make executable:
```bash
chmod +x update_candidate_data.sh
```

### Option 3: Daily Cron Job (During filing periods)

Add to crontab during active filing periods:

```bash
# Edit crontab
crontab -e

# Add daily update at 8 AM during filing period
0 8 * * * /home/bren/Home/Projects/HTML_CSS/precinct/update_candidate_data.sh >> /tmp/candidate_update.log 2>&1
```

---

## Post-Download Analysis

After downloading new data, run analysis to identify changes:

```bash
# Check what's new in Forsyth County
python3 << 'EOF'
import pandas as pd

# Load new data
df_new = pd.read_csv('doc/Candidate_Listing_2026.csv', encoding='latin-1')
forsyth_new = df_new[df_new['county_name'] == 'FORSYTH']

print(f"Total Forsyth County candidates: {len(forsyth_new)}")
print(f"Unique contests: {forsyth_new['contest_name'].nunique()}")

print("\nContest breakdown:")
for contest in sorted(forsyth_new['contest_name'].unique()):
    count = len(forsyth_new[forsyth_new['contest_name'] == contest])
    print(f"  {contest}: {count} candidates")

# Party breakdown
print("\nParty affiliation:")
print(forsyth_new['party_candidate'].value_counts())
EOF
```

---

## Integration with Ballot Matching Strategy

When new candidate data is downloaded:

1. **Run Ballot Matching Analysis:**
   ```bash
   # For municipal races (like 2025 analysis)
   python3 analyze_municipal_candidates.py --year 2026
   
   # For state/federal races
   python3 analyze_partisan_candidates.py --year 2026
   ```

2. **Update Flippability Analysis:**
   - Match candidate names with `flippable` table (for returning candidates)
   - Calculate DVA scores using partisan crossover data
   - Identify high-priority races

3. **Generate Reports:**
   - Create markdown analysis (like `2025_Forsyth_Municipal_Analysis.md`)
   - Update strategic recommendations
   - Share with organizing team

---

## Data Quality Checks

Always verify downloaded data:

```python
import pandas as pd

df = pd.read_csv('doc/Candidate_Listing_2026.csv', encoding='latin-1')

# Check for required columns
required_cols = ['county_name', 'contest_name', 'name_on_ballot', 
                 'first_name', 'last_name', 'party_candidate']
missing = [col for col in required_cols if col not in df.columns]
if missing:
    print(f"⚠️  Missing columns: {missing}")

# Check for Forsyth County data
forsyth = df[df['county_name'] == 'FORSYTH']
if len(forsyth) == 0:
    print("⚠️  No Forsyth County data found")
else:
    print(f"✓ {len(forsyth)} Forsyth County candidates")

# Check for encoding issues
for col in ['name_on_ballot', 'contest_name']:
    if df[col].str.contains('�').any():
        print(f"⚠️  Encoding issues in {col}")
```

---

## Filing Period Monitoring Schedule

### 2025 Municipal Filing (June-July 2025)
- [x] Initial download: June 2025
- [ ] Daily updates during filing: June-July 2025
- [ ] Final update after filing closes: Early July 2025
- [x] Analysis complete: October 25, 2025

### 2026 State/Federal Filing (Dec 2025 - Feb 2026)
- [ ] Monitor for filing period announcement
- [ ] Initial download when filing opens
- [ ] Daily updates during filing period
- [ ] Final update after filing closes
- [ ] Run comprehensive ballot matching analysis

---

## Contact & Resources

**NC State Board of Elections:**
- Website: https://www.ncsbe.gov/
- Data Downloads: https://s3.amazonaws.com/dl.ncsbe.gov/index.html
- Candidate Portal: https://s3.amazonaws.com/dl.ncsbe.gov/Elections/

**Useful Links:**
- Election Calendar: https://www.ncsbe.gov/Elections
- Filing Requirements: https://www.ncsbe.gov/running-office
- County Boards: https://vt.ncsbe.gov/BOEInfo/

---

## Automation Ideas

Future enhancements:

1. **Slack/Email Notifications:**
   - Alert when new candidates file
   - Daily summary during filing period
   - Highlight competitive races

2. **Automatic Analysis:**
   - Run ballot matching on new data
   - Compare with previous snapshots
   - Flag returning candidates

3. **Dashboard Integration:**
   - Real-time candidate tracking
   - Filing deadline countdown
   - Race competitiveness scores

4. **Git Version Control:**
   ```bash
   # Track changes in candidate data
   git add doc/Candidate_Listing_2026.csv
   git commit -m "Update: 2026 candidates as of $(date +%Y-%m-%d)"
   ```

---

## Quick Reference Commands

```bash
# Download latest data
wget https://s3.amazonaws.com/dl.ncsbe.gov/Elections/2026/data/Candidate_Listing_2026.csv -O doc/Candidate_Listing_2026.csv

# Check for Forsyth County candidates
grep "FORSYTH" doc/Candidate_Listing_2026.csv | wc -l

# View unique contests
python3 -c "import pandas as pd; df=pd.read_csv('doc/Candidate_Listing_2026.csv', encoding='latin-1'); print(df[df['county_name']=='FORSYTH']['contest_name'].unique())"

# Run ballot matching analysis
python3 analyze_candidates.py --county FORSYTH --year 2026
```

---

**Last Updated:** October 25, 2025  
**Next Review:** December 2025 (when 2026 filing period begins)
