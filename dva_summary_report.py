#!/usr/bin/env python3
"""
Quick DVA Summary Report
=======================

Generate a quick text-based summary of the DVA analysis results
for immediate review and strategic planning.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

def generate_dva_summary():
    """Generate a comprehensive text summary of DVA analysis."""
    
    # Database connection
    load_dotenv()
    db_url = (
        f'postgresql://{os.getenv("POSTGRES_USER")}:'
        f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
        f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
    )
    engine = create_engine(db_url)
    
    # Get flippable races data
    query = '''
    WITH race_totals AS (
        SELECT 
            county, precinct, contest_name, election_date,
            SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as dem_votes,
            SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) as rep_votes,
            SUM(total_votes) as total_votes
        FROM candidate_vote_results 
        WHERE choice_party IN ('DEM', 'REP')
        GROUP BY county, precinct, contest_name, election_date
        HAVING SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) > 0 
           AND SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) > 0
    ),
    governor_turnout AS (
        SELECT 
            county, precinct, election_date,
            SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as gov_dem_votes
        FROM candidate_vote_results 
        WHERE choice_party = 'DEM' 
          AND LOWER(contest_name) LIKE '%governor%'
        GROUP BY county, precinct, election_date
    ),
    margins AS (
        SELECT 
            rt.*,
            gt.gov_dem_votes,
            ABS(rt.dem_votes - rt.rep_votes) as vote_diff,
            ROUND((ABS(rt.dem_votes - rt.rep_votes) * 100.0 / rt.total_votes), 2) as margin_pct,
            CASE 
                WHEN gt.gov_dem_votes IS NULL OR gt.gov_dem_votes <= rt.dem_votes THEN 999.9
                ELSE ROUND(((rt.rep_votes + 1 - rt.dem_votes) * 100.0 / (gt.gov_dem_votes - rt.dem_votes)), 1)
            END as dva_pct_needed,
            COALESCE(gt.gov_dem_votes - rt.dem_votes, 0) as dem_absenteeism
        FROM race_totals rt
        LEFT JOIN governor_turnout gt ON rt.county = gt.county 
                                      AND rt.precinct = gt.precinct 
                                      AND rt.election_date = gt.election_date
        WHERE rt.rep_votes > rt.dem_votes  -- Republican wins only
    )
    SELECT *
    FROM margins 
    WHERE margin_pct BETWEEN 0.01 AND 10.0
      AND total_votes >= 25
    ORDER BY dva_pct_needed ASC, margin_pct ASC
    '''
    
    with engine.connect() as conn:
        result = conn.execute(text(query))
        races = pd.DataFrame(result.fetchall(), columns=[
            'county', 'precinct', 'contest_name', 'election_date',
            'dem_votes', 'rep_votes', 'total_votes', 'gov_dem_votes',
            'vote_diff', 'margin_pct', 'dva_pct_needed', 'dem_absenteeism'
        ])
        
        # Convert to numeric
        numeric_cols = ['dem_votes', 'rep_votes', 'total_votes', 'gov_dem_votes',
                      'vote_diff', 'margin_pct', 'dva_pct_needed', 'dem_absenteeism']
        for col in numeric_cols:
            races[col] = pd.to_numeric(races[col], errors='coerce')
    
    # Strategic tier classification
    def get_tier(dva_pct):
        if dva_pct <= 25:
            return 'HIGHLY FLIPPABLE'
        elif dva_pct <= 50:
            return 'FLIPPABLE'
        elif dva_pct <= 75:
            return 'COMPETITIVE'
        elif dva_pct <= 100:
            return 'STRETCH TARGET'
        else:
            return 'DIFFICULT'
    
    races['tier'] = races['dva_pct_needed'].apply(get_tier)
    
    print("🎯 DVA FLIPPABLE RACE SUMMARY REPORT")
    print("=" * 80)
    print(f"Generated: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total Republican-won races analyzed: {len(races)}")
    print()
    
    # Tier summary
    tier_summary = races.groupby('tier').agg({
        'contest_name': 'count',
        'vote_diff': 'sum',
        'dem_absenteeism': 'sum',
        'dva_pct_needed': 'mean'
    }).round(1)
    
    tier_summary.columns = ['races', 'total_gap', 'total_absent', 'avg_dva']
    
    print("📊 STRATEGIC TIER BREAKDOWN:")
    print("-" * 40)
    for tier in ['HIGHLY FLIPPABLE', 'FLIPPABLE', 'COMPETITIVE', 'STRETCH TARGET', 'DIFFICULT']:
        if tier in tier_summary.index:
            data = tier_summary.loc[tier]
            pct = (data['races'] / len(races)) * 100
            print(f"{tier:18s}: {int(data['races']):3d} races ({pct:4.1f}%) | "
                  f"Gap: {int(data['total_gap']):6,} votes | "
                  f"DVA: {data['avg_dva']:5.1f}%")
    print()
    
    # County breakdown
    county_summary = races.groupby('county').agg({
        'contest_name': 'count',
        'vote_diff': 'sum',
        'dva_pct_needed': 'mean'
    }).round(1)
    
    county_summary.columns = ['races', 'total_gap', 'avg_dva']
    county_summary = county_summary.sort_values('races', ascending=False)
    
    print("🏛️  TOP COUNTIES BY FLIPPABLE RACES:")
    print("-" * 50)
    for county, data in county_summary.head(10).iterrows():
        print(f"{county:15s}: {int(data['races']):3d} races | "
              f"Gap: {int(data['total_gap']):5,} votes | "
              f"Avg DVA: {data['avg_dva']:5.1f}%")
    print()
    
    # Top strategic targets
    print("🎯 TOP 15 STRATEGIC TARGETS:")
    print("-" * 60)
    top_targets = races.head(15)
    
    for i, (_, race) in enumerate(top_targets.iterrows(), 1):
        print(f"{i:2d}. {race['county']} P{race['precinct']:3s} | "
              f"{race['contest_name'][:35]:35s} | "
              f"Gap: {int(race['vote_diff']):3d} votes | "
              f"DVA: {race['dva_pct_needed']:5.1f}%")
    print()
    
    # Key insights
    highly_flippable = races[races['tier'] == 'HIGHLY FLIPPABLE']
    if len(highly_flippable) > 0:
        print("💡 KEY STRATEGIC INSIGHTS:")
        print("-" * 30)
        print(f"• {len(highly_flippable)} races need ≤25% DVA activation")
        print(f"• Total vote gap for highly flippable: {highly_flippable['vote_diff'].sum():,} votes")
        print(f"• Available Democratic absenteeism: {highly_flippable['dem_absenteeism'].sum():,} voters")
        print(f"• Success rate potential: {(highly_flippable['dem_absenteeism'].sum() / highly_flippable['vote_diff'].sum()):.1f}x coverage")
        print()
        
        # Efficiency calculation
        efficiency = (highly_flippable['vote_diff'].sum() / highly_flippable['dem_absenteeism'].sum()) * 100
        print(f"• Resource efficiency: Need to activate {efficiency:.1f}% of absent Dems")
        print(f"• If we achieve 25% DVA: Could flip {len(highly_flippable)} races")
        print()
    
    print("📈 RECOMMENDED ACTION PLAN:")
    print("-" * 30)
    print("1. 🎯 PHASE 1: Target all HIGHLY FLIPPABLE races (≤25% DVA)")
    print("2. 💪 PHASE 2: Expand to FLIPPABLE races (25-50% DVA)")  
    print("3. ⚡ PHASE 3: Consider COMPETITIVE races (50-75% DVA)")
    print("4. 🎲 PHASE 4: Evaluate STRETCH TARGETS (75-100% DVA)")
    print()
    print("🔧 TACTICAL RECOMMENDATIONS:")
    print("• Focus voter outreach in precincts with highest absenteeism")
    print("• Prioritize counties with multiple flippable races")
    print("• Target races with <5 vote margins first")
    print("• Monitor turnout patterns in governor vs down-ballot races")
    print()

if __name__ == "__main__":
    generate_dva_summary()