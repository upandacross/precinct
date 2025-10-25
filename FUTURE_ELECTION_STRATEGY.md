# Future Election Strategy: Leveraging Historical Flippable Race Analysis

**Strategic Question:** How can analyzing past "flippable" races (2020-2024) inform strategy for upcoming elections?

## 🎯 Core Insight: Historical Patterns Predict Future Opportunities

### What the Historical Data Tells Us

Our analysis of 481 Republican-won races from 2020-2024 reveals:

1. **DVA (Democratic Voter Absenteeism) Patterns**
   - 426,170 Democrats voted for governor but skipped down-ballot races
   - Only 11.2% activation rate needed to flip 322 races via DVA pathway
   - This reveals **behavioral patterns** that likely persist across election cycles

2. **Geographic Clustering of Competitive Races**
   - 22 precincts with 3+ competitive races (flippable clusters)
   - These precincts show **consistent competitiveness** across multiple contests
   - Indicates structural demographic/political characteristics, not random variation

3. **Vote Gap vs DVA Pathways**
   - 66.9% of races are more efficiently won through DVA activation
   - 33.1% require traditional voter acquisition
   - This reveals **two distinct voter mobilization strategies** needed

---

## 🔮 Predictive Value for Future Elections

### 1. **Precinct-Level Propensity Scoring**

**Concept:** Precincts that were "flippable" in past elections likely remain competitive.

**Application to Future Races:**
- **High-Value Targets:** Precincts from our "slam dunk" and "highly flippable" tiers
- **Expected Behavior:** If precinct 74 had 8 flippable races in 2020-2024, it's structurally competitive
- **Resource Allocation:** Focus GOTV and persuasion efforts where historical data shows elasticity

**Why This Works:**
- Demographics change slowly (5-10 year horizon)
- Voter behavior patterns are sticky
- Registration trends are predictable
- Geographic political culture persists

**Data to Track:**
```sql
-- Future election targeting query
SELECT 
    county,
    precinct,
    COUNT(*) as historical_flippable_races,
    AVG(dva_pct_needed) as avg_dva_activation_needed,
    AVG(vote_gap) as avg_vote_gap,
    MIN(margin_pct) as closest_margin
FROM flippable 
GROUP BY county, precinct
HAVING COUNT(*) >= 3  -- At least 3 competitive races
ORDER BY avg_dva_activation_needed ASC
```

---

### 2. **Voter Behavior Pattern Recognition**

**DVA Voters Are Predictable:**
- They vote in high-salience races (Governor, President)
- They skip down-ballot races (judges, commissioners, school board)
- **Future Implication:** These same voters will likely repeat this pattern

**Strategic Response for 2026/2028:**

#### A. **Identify Current DVA-Prone Voters**
```sql
-- Find voters who match historical DVA pattern
SELECT voter_id, precinct
FROM voter_file
WHERE 
    voted_in_2024_presidential = TRUE
    AND voted_in_2024_senate = FALSE
    AND party = 'DEM'
```

#### B. **Targeted Messaging for Down-Ballot Races**
- **Who:** Voters matching historical DVA pattern (voted gov, skipped others)
- **Message:** "You voted for [top ticket]. Don't leave the rest of the ballot blank!"
- **Channel:** Digital ads, text banking, door knocking
- **Timing:** Early voting period + Election Day

#### C. **Sample Ballot Education**
- Historical data shows DVA voters don't complete ballots
- **Solution:** Sample ballot walkthroughs in DVA-heavy precincts
- **Content:** "Down-Ballot Democrats You Don't Want to Miss"

---

### 3. **Contest-Type Vulnerability Analysis**

**Which Race Types Are Most Flippable?**

Based on historical patterns, certain contest types show higher flippability:

| Contest Type | Strategic Value | Why Flippable |
|-------------|----------------|---------------|
| **School Board** | High | Low-information, high DVA, non-partisan in many counties |
| **County Commissioner** | High | Local focus, ticket-splitting common, moderate turnout |
| **Clerk of Court** | Medium | Administrative role, low voter knowledge, high DVA |
| **Sheriff** | Medium | Name recognition matters, incumbency advantage can be overcome |
| **District Court Judge** | High | Extremely high DVA (voters skip judicial races consistently) |

**Future Election Application:**
- **Prioritize** judicial and school board races in flippable precincts
- **DVA-focused campaigns** for low-salience administrative races
- **Traditional voter persuasion** for high-profile contests (Sheriff, Commissioner)

---

### 4. **Ballot-to-Flippable Race Matching System**

**Strategic Question:** How do we identify which upcoming races match our historical flippable patterns?

#### The Matching Process

**Step 1: Retrieve Future Ballot Information**
```sql
-- Get all contests on upcoming election ballots in target county
SELECT DISTINCT
    e.election_name,
    e.election_date,
    e.contests,
    e.municipality,
    e.county
FROM upcoming_elections e
WHERE 
    e.county = 'FORSYTH'
    AND e.election_date >= CURRENT_DATE
    AND e.is_active = TRUE
ORDER BY e.election_date;
```

**Step 2: Match Contest Types to Historical Flippables**
```sql
-- Find historical flippable races that match upcoming contest types
WITH upcoming_contests AS (
    -- Parse contests from upcoming_elections
    SELECT 
        election_date,
        election_name,
        UNNEST(STRING_TO_ARRAY(contests, ',')) AS contest_type
    FROM upcoming_elections
    WHERE county = 'FORSYTH' AND election_date >= CURRENT_DATE
),
historical_patterns AS (
    -- Get historical flippable races grouped by contest type
    SELECT 
        CASE 
            WHEN contest_name LIKE '%School Board%' THEN 'School Board'
            WHEN contest_name LIKE '%Commissioner%' THEN 'County Commissioner'
            WHEN contest_name LIKE '%Judge%' OR contest_name LIKE '%Court%' THEN 'Judicial'
            WHEN contest_name LIKE '%Sheriff%' THEN 'Sheriff'
            WHEN contest_name LIKE '%Clerk%' THEN 'Clerk'
            ELSE 'Other'
        END as contest_category,
        COUNT(*) as historical_flippable_count,
        AVG(dva_pct_needed) as avg_dva_needed,
        AVG(vote_gap) as avg_vote_gap,
        STRING_AGG(DISTINCT precinct, ', ') as flippable_precincts
    FROM flippable
    WHERE county = 'FORSYTH'
    GROUP BY contest_category
)
SELECT 
    uc.election_date,
    uc.election_name,
    TRIM(uc.contest_type) as upcoming_contest,
    hp.historical_flippable_count,
    hp.avg_dva_needed,
    hp.avg_vote_gap,
    hp.flippable_precincts,
    -- Strategic scoring
    CASE 
        WHEN hp.avg_dva_needed < 15 THEN 'HIGH PRIORITY - Low DVA Needed'
        WHEN hp.avg_dva_needed < 25 THEN 'MEDIUM PRIORITY - Moderate DVA'
        ELSE 'LONG GAME - High DVA Required'
    END as priority_tier
FROM upcoming_contests uc
LEFT JOIN historical_patterns hp 
    ON TRIM(uc.contest_type) ILIKE '%' || hp.contest_category || '%'
WHERE hp.historical_flippable_count > 0
ORDER BY uc.election_date, hp.avg_dva_needed;
```

#### Candidate Identification Strategy

**Step 3A: Identify Geographic Overlap**
```sql
-- Find precincts where upcoming election overlaps with historical flippable precincts
SELECT 
    f.precinct,
    f.county,
    COUNT(*) as historical_flippable_races,
    AVG(f.dva_pct_needed) as avg_dva_activation,
    STRING_AGG(f.contest_name, ' | ') as past_flippable_contests,
    -- Upcoming election data
    e.election_name,
    e.election_date,
    e.contests as upcoming_contests
FROM flippable f
CROSS JOIN upcoming_elections e
WHERE 
    f.county = e.county
    AND e.election_date >= CURRENT_DATE
    AND e.county = 'FORSYTH'  -- Or any target county
GROUP BY f.precinct, f.county, e.election_name, e.election_date, e.contests
HAVING COUNT(*) >= 2  -- At least 2 historical flippable races
ORDER BY avg_dva_activation ASC;
```

**Step 3B: Match Specific Race Characteristics**
```sql
-- Detailed matching: Find candidates/races with similar competitive profiles
WITH race_profiles AS (
    SELECT 
        contest_name,
        county,
        precinct,
        margin_pct,
        dva_pct_needed,
        vote_gap,
        rep_votes,
        dem_votes,
        -- Categorize competitiveness
        CASE 
            WHEN margin_pct <= 3 THEN 'Ultra Competitive'
            WHEN margin_pct <= 5 THEN 'Highly Competitive'
            WHEN margin_pct <= 8 THEN 'Competitive'
        END as competitiveness_tier,
        -- Categorize DVA pathway
        CASE 
            WHEN dva_pct_needed <= 12 THEN 'DVA Slam Dunk'
            WHEN dva_pct_needed <= 20 THEN 'DVA Achievable'
            WHEN dva_pct_needed <= 30 THEN 'DVA Possible'
        END as dva_tier
    FROM flippable
    WHERE county = 'FORSYTH'
)
SELECT 
    contest_name,
    precinct,
    competitiveness_tier,
    dva_tier,
    margin_pct,
    dva_pct_needed,
    vote_gap,
    -- Strategic recommendation
    CASE 
        WHEN dva_tier = 'DVA Slam Dunk' THEN 'RECRUIT IMMEDIATELY - Easy win via DVA'
        WHEN dva_tier = 'DVA Achievable' AND competitiveness_tier = 'Ultra Competitive' 
            THEN 'HIGH PRIORITY - Winnable with focused effort'
        WHEN competitiveness_tier = 'Highly Competitive' 
            THEN 'STRONG CANDIDATE - Invest in quality recruitment'
        ELSE 'LONG-TERM BUILD - Develop bench'
    END as recruitment_strategy
FROM race_profiles
ORDER BY 
    CASE dva_tier
        WHEN 'DVA Slam Dunk' THEN 1
        WHEN 'DVA Achievable' THEN 2
        ELSE 3
    END,
    margin_pct ASC;
```

#### Practical Application Workflow

**For November 2025 Municipal Elections (Example):**

1. **Query Upcoming Ballot** → Winston-Salem has Mayor + City Council races
2. **Check Historical Data** → Were there flippable municipal races in 2020-2024?
3. **Match Precincts** → Which Winston-Salem precincts had 3+ flippable races?
4. **Identify Patterns** → What was the avg DVA needed? (e.g., 10-15%)
5. **Target Recruitment** → Recruit candidates for those specific seats/wards
6. **Voter Universe** → Build targeted lists of DVA voters in those precincts
7. **Messaging Focus** → "You voted for governor—don't skip city council!"

**For 2026 Primary Elections:**

1. **List all ballot contests** → U.S. House, NC Senate, NC House, County Commissioner, Sheriff, etc.
2. **Match each to historical** → Which contest types were most flippable?
3. **Geographic targeting** → Which precincts had flippable Commissioner races?
4. **DVA scoring** → Rank by easiest DVA activation percentage
5. **Candidate recruitment** → Focus recruitment in high-opportunity districts
6. **Resource allocation** → Invest heavily in historically flippable race types

#### Candidate-Specific Matching Example

**Scenario:** 2026 County Commissioner Race in Forsyth County

```sql
-- Find which precincts had flippable commissioner races historically
SELECT 
    precinct,
    contest_name,
    year,
    margin_pct,
    dva_pct_needed,
    vote_gap,
    dem_votes,
    rep_votes,
    gov_dem_votes - dem_votes as dva_voter_pool
FROM flippable
WHERE 
    county = 'FORSYTH'
    AND contest_name LIKE '%Commissioner%'
ORDER BY dva_pct_needed ASC
LIMIT 20;
```

**Output Interpretation:**
- Precinct 74: Had 2 flippable commissioner races, avg DVA needed = 11%
- Precinct 45: Had 1 flippable commissioner race, DVA needed = 15%
- **Action:** Recruit strong Democratic candidate for Commissioner
- **Target:** Focus DVA activation in Precincts 74, 45, and similar high-opportunity areas
- **Goal:** Activate 12-15% of identified DVA voters = flip the seat

#### Technology Integration

**Automated Matching System:**

```python
# Pseudocode for ballot matching system
def match_upcoming_to_flippable(county, election_date):
    """
    Match upcoming election contests to historical flippable patterns.
    """
    # Get upcoming ballot contests
    upcoming = query_upcoming_elections(county, election_date)
    
    # Get historical flippable races
    historical = query_flippable_races(county)
    
    # Match by contest type
    matches = []
    for contest in upcoming.contests:
        contest_type = categorize_contest(contest)
        
        # Find historical races of same type
        similar_races = historical.filter(type=contest_type)
        
        if similar_races.count() > 0:
            match = {
                'upcoming_contest': contest,
                'historical_count': similar_races.count(),
                'avg_dva_needed': similar_races.avg('dva_pct_needed'),
                'best_precincts': similar_races.order_by('dva_pct_needed')[:5],
                'priority_score': calculate_priority(similar_races),
                'recommended_strategy': generate_strategy(similar_races)
            }
            matches.append(match)
    
    return prioritize_matches(matches)
```

**Dashboard Integration:**

Create a "2026 Election Opportunities" dashboard showing:
- Upcoming ballot contests
- Historical flippable race matches
- Target precincts for each race
- DVA activation targets
- Candidate recruitment priorities
- Voter universe sizes

---

### 5. **Multi-Cycle Investment Strategy**

**The Long Game: Building Infrastructure in Flippable Precincts**

**Year 1 (2025 - Off-Year):**
- Voter registration drives in high-DVA precincts
- Community organizing in precincts with 3+ flippable races
- Build precinct captain network in tier 1 & 2 precincts

**Year 2 (2026 - Midterm):**
- Test DVA activation messaging in priority precincts
- Measure activation rate improvements vs. 2022 baseline
- Refine voter contact strategies based on results

**Year 3 (2027 - Off-Year):**
- Deepen relationships with activated DVA voters
- Recruit candidates for identified flippable races
- Pre-campaign in highest-opportunity contests

**Year 4 (2028 - Presidential):**
- Full deployment of refined DVA activation strategy
- Maximum resource allocation to proven flippable precincts
- Coordinate down-ballot messaging with top-ticket campaign

---

## 📊 Data-Driven Decision Framework

### Before Every Election, Ask:

1. **Which precincts were historically flippable?**
   - Use flippable race count and DVA patterns from 2020-2024
   
2. **What contests are on the ballot?**
   - Match contest types to historical flippability patterns
   
3. **What's our voter file showing?**
   - Identify current voters matching historical DVA patterns
   
4. **Where should we invest resources?**
   - Prioritize precincts with proven elasticity and efficient pathways

### Resource Allocation Model

```
Priority Score = (Historical Flippable Races × 3) 
                + (Low DVA% Needed × 2) 
                + (High Dem Registration × 1)
                - (Large Vote Gaps × 2)
```

**Tier 1 (Highest ROI):** Score 15+
- Maximum canvassing, texting, digital ads
- Candidate recruitment and support
- Sample ballot campaigns

**Tier 2 (Medium ROI):** Score 10-14
- Moderate field investment
- Targeted digital ads
- Mail campaigns

**Tier 3 (Long-term Build):** Score 5-9
- Voter registration focus
- Community organizing
- Infrastructure development

---

## 🎲 Scenario Planning: 2026 Example

**Hypothetical:** You're planning for 2026 midterms in Wake County.

### Step 1: Query Historical Data
```sql
SELECT 
    precinct,
    COUNT(*) as flippable_count,
    AVG(dva_pct_needed) as avg_dva_needed,
    STRING_AGG(contest_name, ', ') as past_contests
FROM flippable
WHERE county = 'WAKE'
GROUP BY precinct
ORDER BY flippable_count DESC;
```

### Step 2: Identify 2026 Ballot Contests
- County Commissioner (3 seats)
- School Board (5 seats)
- Clerk of Superior Court
- Register of Deeds

### Step 3: Match Historical Patterns
- **School Board races** historically flippable in precincts 12, 34, 74
- These precincts had avg DVA activation need of 8-12%
- **Strategic Focus:** DVA activation messaging for School Board

### Step 4: Build Targeted Voter Universe
```sql
-- 2026 School Board targets in Wake County
SELECT v.voter_id, v.precinct, v.name
FROM voters v
JOIN flippable f ON v.precinct = f.precinct
WHERE 
    v.county = 'WAKE'
    AND v.party = 'DEM'
    AND v.voted_2024_general = TRUE
    AND v.voted_2024_local_races = FALSE  -- DVA pattern
    AND f.contest_name LIKE '%School Board%'
```

### Step 5: Campaign Execution
- **Message:** "You voted for Harris. Don't forget the School Board!"
- **Channels:** SMS (72 hrs before election), digital ads (2 weeks out), door knocks (weekend before)
- **Goal:** Activate 12% of DVA voters = flip 3 School Board seats

---

## 🔬 Continuous Learning: Post-Election Analysis

**After Every Election, Measure:**

1. **DVA Activation Success Rate**
   - Compare actual vs. predicted DVA behavior
   - Adjust future models accordingly

2. **Precinct Performance vs. History**
   - Did historically flippable precincts perform as expected?
   - Update propensity scores

3. **Contest-Type Patterns**
   - Which race types showed expected flippability?
   - Refine contest-type targeting

4. **Message Testing Results**
   - Which DVA activation messages worked best?
   - A/B test results inform future campaigns

**Data Pipeline:**
```
Historical Analysis (2020-2024) 
    ↓
Predictive Model (for upcoming election)
    ↓
Campaign Execution (targeted outreach)
    ↓
Post-Election Validation (measure results)
    ↓
Model Refinement (update for next cycle)
    ↓
[Repeat]
```

---

## 💡 Key Strategic Insights

### 1. **DVA is the Biggest Opportunity**
- 426K Democratic voters skipped down-ballot races
- Only need to activate ~12% to flip hundreds of races
- **This is easier than converting Republicans or registering new voters**

### 2. **Geography Matters More Than We Think**
- Precincts with multiple flippable races = structural competitiveness
- Focus on place, not just demographics
- **Local organizing beats broad messaging**

### 3. **Not All Races Are Created Equal**
- Low-salience races (judges, clerks) have highest DVA
- High-profile races (Sheriff, Commissioner) need traditional persuasion
- **Tailor strategy to contest type**

### 4. **Historical Data is Predictive**
- Past flippability predicts future opportunity
- Voter behavior patterns persist across cycles
- **Data-driven targeting beats intuition**

### 5. **Small Margins = Big Opportunities**
- Many races lost by <100 votes
- Minimal activation/persuasion needed
- **Low-hanging fruit exists everywhere**

---

## 🚀 Immediate Next Steps

### For Campaign Staff:

1. **Build Precinct Priority List**
   - Use historical flippable data
   - Rank by DVA efficiency and race count
   
2. **Create DVA Voter File**
   - Flag voters with historical skip pattern
   - Segment by precinct and contest history

3. **Develop Messaging Framework**
   - Contest-specific down-ballot messages
   - Test "complete your ballot" framing

4. **Recruit Precinct Captains**
   - Focus on tier 1 & 2 flippable precincts
   - Train on DVA activation tactics

### For Data/Analytics Team:

1. **Automate Flippable Analysis**
   - Create pipeline for post-election updates
   - Build predictive model for future races

2. **Integrate with Voter File**
   - Match historical patterns to current voters
   - Score voters by DVA propensity

3. **Build Monitoring Dashboard**
   - Track early vote DVA rates in real-time
   - Alert if activation falls below target

---

## 📚 Appendix: Technical Queries

### Query 1: Find High-Value Target Precincts for Next Election
```sql
WITH precinct_scores AS (
    SELECT 
        county,
        precinct,
        COUNT(*) as flippable_count,
        AVG(dva_pct_needed) as avg_dva_needed,
        AVG(vote_gap) as avg_gap,
        MIN(margin_pct) as closest_margin
    FROM flippable
    GROUP BY county, precinct
)
SELECT 
    county,
    precinct,
    flippable_count,
    ROUND(avg_dva_needed, 1) as dva_activation_target,
    ROUND(avg_gap, 0) as avg_votes_needed,
    ROUND(closest_margin, 2) as closest_race_margin,
    -- Priority scoring
    (flippable_count * 3) + 
    (CASE WHEN avg_dva_needed < 15 THEN 4 ELSE 0 END) +
    (CASE WHEN avg_gap < 200 THEN 3 ELSE 0 END) as priority_score
FROM precinct_scores
WHERE flippable_count >= 2
ORDER BY priority_score DESC
LIMIT 50;
```

### Query 2: Identify DVA-Pattern Voters for Targeting
```sql
-- Adapt this template to your voter file schema
SELECT 
    voter_id,
    county,
    precinct,
    registration_date,
    -- Flag DVA behavior pattern
    CASE 
        WHEN voted_governor_2020 = TRUE AND num_downballot_2020 < 3 THEN TRUE
        ELSE FALSE 
    END as dva_2020,
    CASE 
        WHEN voted_president_2024 = TRUE AND num_downballot_2024 < 3 THEN TRUE
        ELSE FALSE 
    END as dva_2024
FROM voters
WHERE 
    party = 'DEM'
    AND precinct IN (SELECT precinct FROM flippable GROUP BY precinct HAVING COUNT(*) >= 3)
HAVING dva_2020 = TRUE OR dva_2024 = TRUE;
```

### Query 3: Contest-Type Flippability Analysis
```sql
SELECT 
    CASE 
        WHEN contest_name LIKE '%School Board%' THEN 'School Board'
        WHEN contest_name LIKE '%Commissioner%' THEN 'County Commissioner'
        WHEN contest_name LIKE '%Judge%' OR contest_name LIKE '%Court%' THEN 'Judicial'
        WHEN contest_name LIKE '%Sheriff%' THEN 'Sheriff'
        WHEN contest_name LIKE '%Clerk%' THEN 'Clerk'
        ELSE 'Other'
    END as contest_type,
    COUNT(*) as flippable_races,
    AVG(dva_pct_needed) as avg_dva_needed,
    AVG(vote_gap) as avg_vote_gap,
    COUNT(*) FILTER (WHERE dva_pct_needed < 15) as slam_dunk_count
FROM flippable
GROUP BY contest_type
ORDER BY flippable_races DESC;
```

---

## 🎯 Final Thought: From Analysis to Action

This historical analysis isn't just backward-looking—it's a **roadmap for winning future elections**.

Every flippable race from 2020-2024 teaches us:
- **Where** to focus (precincts with multiple competitive races)
- **Who** to target (DVA-prone Democratic voters)
- **What** to say ("Complete your ballot, don't skip local races")
- **When** to invest (early in precincts with proven elasticity)

**The data doesn't lie:** We have hundreds of winnable races if we activate our own voters.

**The challenge:** Converting historical insight into boots-on-the-ground organizing.

**The opportunity:** Flip local races, build the bench, and create a sustainable Democratic infrastructure from the ground up.

---

*Document Version: 1.0*  
*Last Updated: October 24, 2025*  
*Data Source: NC Flippable Races Analysis 2020-2024*