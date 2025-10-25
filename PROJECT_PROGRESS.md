# Project Progress Log

## October 25, 2025 - Candidate Automation System

### Overview
Implemented complete automation system for monitoring NC Board of Elections candidate filings and generating ballot matching analysis reports.

### Features Implemented

#### 1. **Automated Candidate Data Tracking**
- **Script**: `app_administration/update_candidate_data.py`
- Smart detection of filing periods (municipal: June-July odd years, state/federal: Dec-Feb even years)
- MD5 hash comparison to detect new candidate data
- Data quality verification
- Auto-generates Forsyth County analysis summaries
- Force mode for manual downloads: `--force YEAR`

#### 2. **Election Schedule Parser**
- **Script**: `app_administration/parse_ncsbe_elections.py`
- Scrapes https://www.ncsbe.gov/voting/upcoming-election
- Extracts election dates and estimates filing periods
- Saves to `doc/upcoming_elections.json`
- Identifies Forsyth County municipalities

#### 3. **Ballot Matching Analysis Generator**
- **Script**: `app_administration/generate_ballot_matching_analysis.py`
- Auto-generates analysis reports when new candidate data detected
- **Municipal races**: Uses partisan crossover data for flippability scoring
- **State/Federal races**: Identifies returning candidates (Tier 1 rematch advantage)
- Dynamic county detection from database (`is_county` user)
- Report format: `{COUNTY}_Municipal_Analysis_{YYYYMMDD}.md`
- Reports saved to `reports/` directory

#### 4. **Orchestration Scripts**
- **daily_candidate_check.sh**: Simple wrapper for cron (candidate data only)
- **daily_election_check.sh**: Full pipeline (schedule + data + analysis)
  - Parses election schedule
  - Checks for new candidate data
  - Generates analysis if changes detected
  - Logs to `/tmp/election_automation_YYYYMM.log`

#### 5. **Comprehensive Test Suite**
- **File**: `test/test_candidate_automation.py`
- **Coverage**: 23 tests, 100% passing
- **Categories**:
  - Update candidate data (6 tests)
  - Parse NCSBE elections (4 tests)
  - Generate ballot matching analysis (5 tests)
  - Integration tests (5 tests)
  - Edge cases (3 tests)
- **Integration**: Added to `test/run_all_tests.py` as `candidate_automation` category

### Technical Details

#### File Organization
```
app_administration/
├── update_candidate_data.py          # Download NC BOE candidate files
├── parse_ncsbe_elections.py          # Parse election schedule
├── generate_ballot_matching_analysis.py  # Generate ballot matching reports
├── daily_candidate_check.sh          # Simple cron wrapper
├── daily_election_check.sh           # Full orchestration
├── CANDIDATE_DATA_UPDATES.md         # Documentation
└── 2025_Forsyth_Municipal_Analysis_20251025.md  # Sample analysis

doc/
├── Candidate_Listing_2025.csv        # NC BOE data
└── upcoming_elections.json           # Parsed election schedule

reports/
└── FORSYTH_Municipal_Analysis_YYYYMMDD.md  # Generated analyses

test/
└── test_candidate_automation.py      # Test suite
```

#### Key Improvements
1. **Dynamic County Support**: Reads county from database `is_county` user instead of hardcoding
2. **Simplified Filenames**: Removed year prefix from reports (date suffix makes it obvious)
3. **Path Independence**: Scripts work from `app_administration/` with proper path resolution
4. **Comprehensive Testing**: Full test coverage with integration into test runner
5. **Error Handling**: Graceful fallbacks for missing data, network errors, etc.

#### Cron Setup
```bash
# Edit crontab
crontab -e

# Add this line for 11PM Mon-Fri execution:
0 23 * * 1-5 /home/bren/Home/Projects/HTML_CSS/precinct/app_administration/daily_election_check.sh
```

### Database Integration
- Queries `flippable` table for partisan crossover data
- Queries `candidate_vote_results` for historical turnout
- Reads county from `user` table (`is_county = true`)
- Connects via `Config.SQLALCHEMY_DATABASE_URI`

### Data Sources
- **NC BOE Candidate Files**: `https://s3.amazonaws.com/dl.ncsbe.gov/Elections/{year}/Candidate%20Filing/Candidate_Listing_{year}.csv`
- **NCSBE Election Schedule**: `https://www.ncsbe.gov/voting/upcoming-election`

### Example Analysis Output
```markdown
# 2025 FORSYTH County Municipal Elections - Ballot Matching Analysis

## Executive Summary
- Total Candidates: 51
- Contests: 12
- Democratic Candidates: 15
- Republican Candidates: 18

### Top Opportunities
- Lewisville Mayor: 47.2% Dem baseline, DVA: 2.8%
- Kernersville Council: 45.8% Dem baseline, DVA: 4.2%

## Flippability Analysis
### Lewisville Mayor
- Candidates: 2 DEM, 2 REP, 0 Other
- Historical Turnout: 3,245 votes across 8 precincts
- Partisan Baseline: 47.2% Dem
- DVA Needed: 2.8%
- Rating: LEAN REP
```

### Next Steps (Future Considerations)
- [ ] User interface for viewing generated analyses
- [ ] Email notifications when new data detected
- [ ] Integration with campaign messaging toolkit
- [ ] Volunteer targeting based on flippability scores
- [ ] Historical trend analysis
- [ ] State/federal analysis for 2026 elections

### Testing Status
✅ All tests passing (23/23)
✅ Integrated into main test suite
✅ Scripts executable and properly located
✅ Database connectivity verified
✅ Path resolution working correctly

### Documentation
- README.md updated with automation instructions
- CANDIDATE_DATA_UPDATES.md with detailed usage guide
- Test suite serves as API documentation
- Cron setup instructions included

---

**Status**: Ready for production use (pending user access decision)
**Last Updated**: October 25, 2025
**Developer**: Assistant with @upandacross
