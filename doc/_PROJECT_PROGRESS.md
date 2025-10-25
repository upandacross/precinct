# Project Progress Log

Track major features, updates, and milestones for the Precinct Campaign Platform.

---

## October 25, 2025

### ✅ Municipal Race Integration into Flippable Table

**Feature:** Extended flippable table to include municipal races with proxy DVA calculations using partisan baseline.

**What Was Built:**
1. **Script: `add_municipal_to_flippable.py`**
   - Queries `candidate_vote_results` for municipal contests (city, town, county board races)
   - Calculates partisan baseline from same precinct's state/federal races
   - Uses average governor votes from partisan races as proxy for municipal DVA
   - Adds `race_type` column to distinguish 'partisan' vs 'municipal' races
   - Filters to actual flippable races (DVA > 0)

2. **Database Integration:**
   - Modified `calculate_dva_pct_needed()` trigger to work with both race types
   - Municipal races use partisan `gov_votes` average from same precinct
   - Maintains consistent DVA formula across all race types
   - Added 142 municipal races for Forsyth County

3. **Automation Integration:**
   - Updated `daily_election_check.sh` to call municipal script
   - Runs after new candidate data is detected
   - Clears and refreshes municipal races on each run
   - Continues automation pipeline even if municipal update fails (non-critical)

4. **Test Coverage:**
   - Added `TestMunicipalFlippable` class with 6 tests
   - Tests partisan baseline calculation, contest filtering, DVA proxy logic
   - Validates dry-run mode and integration with flippable table
   - Total test suite: 29 passing tests

**Key Technical Details:**
- **Partisan Baseline:** Averages Democratic % from partisan races in same precinct
- **Governor Votes Proxy:** Uses average `gov_votes` from partisan races for DVA calculation
- **Municipal Contest Filter:** CITY OF%, TOWN OF%, %BOARD OF COMMISSIONERS%, excludes NC/US/state races
- **DVA Interpretation:** Positive = flippable (Dems losing), Negative = already won, Zero = tie

**Files Created:**
- `app_administration/add_municipal_to_flippable.py` - Municipal race integration script

**Files Modified:**
- `app_administration/daily_election_check.sh` - Added municipal update step
- `test/test_candidate_automation.py` - Added 6 municipal flippable tests
- Database trigger `calculate_dva_pct_needed()` - Works for all race types

**Database Impact:**
- Forsyth County: 355 partisan races + 142 municipal races = 497 total flippable opportunities
- Unified query interface for all race types
- Pre-calculated DVA eliminates recalculation overhead

**Next Steps:**
- Update `generate_ballot_matching_analysis.py` to query flippable table directly
- Extend to all NC counties (currently Forsyth only)
- Add municipal race filtering in UI

---

## October 24, 2025

### ✅ Ballot Matching Strategy Documentation System

**Feature:** Created role-based ballot matching strategy documentation accessible from flippable races page.

**What Was Built:**
1. **Two Document Versions:**
   - `BALLOT_MATCHING_STRATEGY.md` - Full version with detailed examples (admin/county only)
   - `BALLOT_MATCHING_STRATEGY_PUBLIC.md` - Simplified version without examples (all users)

2. **Smart Route:**
   - `/ballot-matching-strategy` - Automatically serves correct version based on user role
   - Admin/county users see full strategic examples
   - Regular users see core concepts without detailed scenarios

3. **UI Integration:**
   - Red "Flippability and Future Races" button on flippable races page
   - Upper right placement for visibility
   - Accessible to all authenticated users

**Strategic Content Includes:**
- Core concept of ballot-to-flippable race matching
- Candidate recruitment strategies (including rematch advantage)
- Republican candidate movement tracking
- Voter mobilization targeting
- Decision framework for resource allocation
- Key principles for multi-cycle success

**Files Modified/Created:**
- `doc/BALLOT_MATCHING_STRATEGY.md` - Full version with examples
- `doc/BALLOT_MATCHING_STRATEGY_PUBLIC.md` - Simplified public version
- `main.py` - Added `/ballot-matching-strategy` route with role-based logic
- `templates/flippable.html` - Added red button in upper right

**Use Cases:**
- Educate volunteers on strategic candidate recruitment
- Guide precinct captains on using historical data
- Explain to candidates why they should run (data-driven pitch)
- Opposition research using Republican candidate tracking
- Resource allocation decisions based on proven patterns

---

### ✅ Candidate Name Tracking in Flippable Races

**Feature:** Enhanced flippable race infrastructure to track Democratic and Republican candidate names.

**What Was Built:**
1. **Database Schema Enhancement**
   - Added `dem_candidate` column to flippable table
   - Added `rep_candidate` column to flippable table
   - Backfilled 384 existing flippable races with candidate names

2. **Updated Infrastructure:**
   - `update_flippable_races.py` - Now captures candidate names from `candidate_vote_results`
   - `add_candidate_names_to_flippable.py` - Migration script with automatic backfill

3. **Strategic Capability:**
   - Track which candidates ran in flippable races
   - Identify "almost winners" (candidates who lost narrowly)
   - Enable candidate-specific matching across different races
   - Support "rematch" recruitment strategy

**Use Cases:**
- Find candidates who lost by <3% and recruit them to run again
- Identify candidates who ran multiple times with improving margins
- Match candidates to different race types based on their proven strength
- Geographic targeting: Find where specific candidates performed best
- "Sarah ran for School Board and almost won - let's recruit her for Commissioner"

**Files Modified/Created:**
- `update_flippable_races.py` - Enhanced to capture `dem_candidate` and `rep_candidate`
- `add_candidate_names_to_flippable.py` - New migration script
- `doc/BALLOT_MATCHING_STRATEGY.md` - Added section on recruiting candidates who've run before

**Next Steps:**
- [ ] Create candidate tracking dashboard
- [ ] Build "Almost Winners" report (candidates with <3% losses)
- [ ] Cross-reference candidates across multiple races
- [ ] Create candidate improvement trajectory analysis
- [ ] Automated recruitment lists based on candidate history

---

### ✅ Upcoming Elections Database System

**Feature:** Created comprehensive election tracking system for Forsyth County and North Carolina.

**What Was Built:**
1. **New Database Model** - `UpcomingElection` class in `models.py`
   - Tracks election dates, types (municipal, primary, general)
   - Early voting start/end dates
   - Absentee ballot request and return deadlines
   - Voter registration deadlines
   - County and municipality filtering
   - Contest information for each election

2. **Helper Methods:**
   - `get_upcoming_elections(county=None, limit=10)` - Query upcoming elections
   - `get_next_election(county=None)` - Get next election date
   - `days_until_election()` - Calculate days remaining
   - `is_early_voting_active()` - Check if early voting is currently open

3. **Initial Data Populated:**
   - November 4, 2025 - Municipal Elections (Winston-Salem, Kernersville, Clemmons)
   - March 3, 2026 - Primary Elections
   - November 3, 2026 - General Elections
   - Both Forsyth County-specific and statewide elections

**Current Status:**
- 🗳️ **Early voting is ACTIVE NOW** for municipal elections (Oct 16 - Nov 1)
- Election Day: November 4, 2025 (11 days away)

**Files Modified/Created:**
- `models.py` - Added `UpcomingElection` model
- `create_upcoming_elections.py` - Migration script to create and populate table

**Next Steps:**
- [ ] Integrate election data into main dashboard
- [ ] Add election countdown widget to user interface
- [ ] Create voter information pages for each election
- [ ] Add early voting location finder
- [ ] Email/SMS reminders for important election deadlines

**Use Cases:**
- Display upcoming election dates to precinct captains
- Alert users when early voting begins
- Show registration deadlines
- Track municipal vs. county vs. statewide elections
- Filter elections by county for targeted campaigns

---

### ✅ Future Election Strategy Document

**Feature:** Comprehensive strategic framework for using historical flippable race data.

**What Was Built:**
- Created `FUTURE_ELECTION_STRATEGY.md` - 400+ line strategic playbook
- Data-driven decision framework for resource allocation
- Multi-cycle investment strategy (2025-2028)
- Contest-type vulnerability analysis
- DVA activation strategies
- Technical SQL queries for targeting

**Key Strategic Insights:**
1. DVA (Democratic Voter Absenteeism) is the biggest opportunity
2. Historical flippability predicts future opportunities
3. Geography matters - precinct clustering shows structural competitiveness
4. Contest types require different strategies (judicial vs. executive)
5. Small margins = big opportunities (many races lost by <100 votes)

**Files Created:**
- `FUTURE_ELECTION_STRATEGY.md` - Complete strategic playbook

---

## Earlier Development

### Deployment & Operations
- ✅ **Maintenance Mode System** - Zero-downtime deployment capability
  - Flag file-based maintenance mode (`instance/MAINTENANCE_MODE`)
  - Professional maintenance page with animated design
  - SSH alias configured: `dg_precinct_root`
  - Automated deployment script: `./deploy-with-maintenance.sh`
  - Manual control scripts: `enable-maintenance.sh`, `disable-maintenance.sh`
  - Server: Digital Ocean (138.197.96.240)
  - App directory: `/home/precinct/precinct`
  - Systemd service: `precinct`
  - Total downtime during deployment: ~5-10 seconds
  - **Usage:** Run `./deploy-with-maintenance.sh` after pushing to GitHub
  - **Manual SSH:** `ssh dg_precinct_root` for server access

### Database & Infrastructure
- ✅ PostgreSQL migration from SQLite
- ✅ NC-specific database implementation
- ✅ Dual-database architecture (NC + national)
- ✅ Map storage in database (HTML content)
- ✅ User authentication and authorization
- ✅ Session management and timeouts
- ✅ Rate limiting implementation

### Analytics & Visualization
- ✅ DVA (Democratic Voter Absenteeism) analysis
- ✅ Flippable race analysis (2020-2024)
- ✅ Precinct clustering (K-means)
- ✅ Census tract clustering
- ✅ Interactive dashboards (Dash → Flask migration)
- ✅ Geographic visualizations

### Campaign Tools
- ✅ Campaign Message Toolkit
- ✅ A/B testing framework for messaging
- ✅ Precinct leader management
- ✅ County filtering and access control
- ✅ DVA vs Vote Gap comparison tools

### Documentation
- ✅ Application README
- ✅ Security documentation
- ✅ Database migration guides
- ✅ UV/deployment guides
- ✅ Git workflow tutorials

---

## Upcoming Priorities

### High Priority
- [ ] Election dashboard integration
- [ ] Early voting location API integration
- [ ] Automated election deadline reminders
- [ ] Mobile-responsive election countdown

### Medium Priority
- [ ] Historical election results database
- [ ] Voter turnout tracking by precinct
- [ ] Sample ballot integration
- [ ] Candidate information pages

### Low Priority / Long-term
- [ ] Multi-state expansion
- [ ] Predictive modeling for turnout
- [ ] Social media integration
- [ ] Automated reporting tools

---

## Technical Debt & Maintenance

### Known Issues
- [ ] Flask-Admin pkg_resources deprecation warning
- [ ] Session cleanup for inactive users
- [ ] Map HTML storage optimization (consider compression)

### Performance Improvements
- [ ] Database query optimization for large datasets
- [ ] Caching strategy for frequently accessed data
- [ ] Background job processing for analytics

---

## October 25, 2025

### ✅ Candidate Automation System with Comprehensive Testing

**Feature:** Fully automated system for monitoring NC Board of Elections candidate filings and generating ballot matching analysis reports.

**What Was Built:**

#### 1. **Automated Candidate Data Tracking**
- **Script:** `app_administration/update_candidate_data.py`
- Smart detection of filing periods:
  - Municipal: June-July in odd years (2025, 2027...)
  - State/Federal: December-February in even years (2026, 2028...)
- MD5 hash comparison to detect new candidate data
- Data quality verification with column validation
- Auto-generates Forsyth County analysis summaries
- Force mode for manual downloads: `--force YEAR`
- Source: `https://s3.amazonaws.com/dl.ncsbe.gov/Elections/{year}/Candidate%20Filing/`

#### 2. **Election Schedule Parser**
- **Script:** `app_administration/parse_ncsbe_elections.py`
- Web scraper for `https://www.ncsbe.gov/voting/upcoming-election`
- Extracts election dates using regex pattern matching
- Estimates filing periods based on election dates
- Identifies Forsyth County municipalities
- Saves structured data to `doc/upcoming_elections.json`

#### 3. **Ballot Matching Analysis Generator**
- **Script:** `app_administration/generate_ballot_matching_analysis.py`
- Auto-generates comprehensive analysis reports when new data detected
- **Municipal races:** 
  - Uses partisan crossover data for flippability scoring
  - Calculates DVA (Democratic Vote Advantage) needed
  - Rates races: TOSS-UP, LEAN REP, LIKELY REP, SAFE REP
- **State/Federal races:**
  - Identifies returning candidates (Tier 1 rematch advantage)
  - Matches candidate names with historical flippable table
- Dynamic county detection from database (`is_county` user)
- Simplified report format: `{COUNTY}_Municipal_Analysis_{YYYYMMDD}.md`
- Reports saved to `reports/` directory

#### 4. **Orchestration & Scheduling**
- **daily_candidate_check.sh:** Simple wrapper for cron (candidate data only)
- **daily_election_check.sh:** Full pipeline automation
  1. Parses NCSBE election schedule
  2. Checks for new candidate data during filing periods
  3. Generates ballot matching analysis if changes detected
  4. Logs all operations to `/tmp/election_automation_YYYYMM.log`
  5. Monthly log rotation with 6-month retention
- Ready for cron: `0 23 * * 1-5` (11PM on business days)

#### 5. **Comprehensive Test Suite**
- **File:** `test/test_candidate_automation.py`
- **Coverage:** 23 tests, 100% passing
- **Test Categories:**
  - Update candidate data (6 tests): Filing periods, hash calculation, data quality
  - Parse NCSBE elections (4 tests): Date extraction, filing estimation, error handling
  - Generate ballot matching analysis (5 tests): Year detection, county retrieval, flippability
  - Integration tests (5 tests): Project structure, executability, database connectivity
  - Edge cases (3 tests): Missing data, invalid input, empty datasets
- **Integration:** Added to `test/run_all_tests.py` as `candidate_automation` category
- Run with: `python3 test/run_all_tests.py --category candidate_automation`

**Files Modified/Created:**
- `app_administration/update_candidate_data.py` - Candidate data downloader
- `app_administration/parse_ncsbe_elections.py` - Election schedule parser
- `app_administration/generate_ballot_matching_analysis.py` - Analysis generator
- `app_administration/daily_election_check.sh` - Full orchestration pipeline
- `app_administration/daily_candidate_check.sh` - Simple cron wrapper
- `app_administration/CANDIDATE_DATA_UPDATES.md` - Usage documentation
- `app_administration/2025_Forsyth_Municipal_Analysis_20251025.md` - Sample analysis
- `doc/Candidate_Listing_2020.csv` through `2025.csv` - Historical data
- `doc/upcoming_elections.json` - Parsed election schedule
- `doc/_BALLOT_MATCHING_STRATEGY.pdf` - PDF version of strategy guide
- `test/test_candidate_automation.py` - Complete test suite
- `test/run_all_tests.py` - Updated with new test category
- `README.md` - Complete automation guide with cron instructions

**Technical Improvements:**
1. **Dynamic County Support:** Reads county from database `is_county` user instead of hardcoding
2. **Simplified Filenames:** Removed year prefix from reports (date suffix makes it obvious)
3. **Path Independence:** Scripts work from `app_administration/` with proper path resolution
4. **Comprehensive Error Handling:** Graceful fallbacks for missing data, network errors
5. **Modular Design:** Each script can run independently or as part of pipeline

**Database Integration:**
- Queries `flippable` table for partisan crossover data
- Queries `candidate_vote_results` for historical turnout
- Reads county from `user` table (`is_county = true`)
- Uses `Config.SQLALCHEMY_DATABASE_URI` for connections

**Example Analysis Output:**
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

**Status:** Production-ready, pending user access decisions

**Next Steps (Future Considerations):**
- [ ] User interface for viewing generated analyses in web app
- [ ] Email notifications when new candidate data detected
- [ ] Integration with campaign messaging toolkit
- [ ] Volunteer targeting based on flippability scores
- [ ] Historical trend analysis across election cycles
- [ ] State/federal analysis automation for 2026 elections
- [ ] API endpoints for programmatic access to analysis data

---

*Last Updated: October 25, 2025*
