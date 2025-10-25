# Project Progress Log

Track major features, updates, and milestones for the Precinct Campaign Platform.

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

*Last Updated: October 24, 2025*
