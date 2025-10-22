#!/usr/bin/env python3
"""
Flippable Data Discrepancy Investigation
========================================

This script investigates the discrepancy between:
1. Direct queries using temp_dem/temp_oppo tables
2. Data shown on the flippable races page (from flippable table)

Focus: Precinct '74' data comparison
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from config import Config

def investigate_precinct_74_discrepancy():
    """Compare flippable table vs direct candidate_vote_results for precinct 74."""
    
    # Initialize database connection
    load_dotenv()
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    print("🔍 INVESTIGATING PRECINCT 74 DATA DISCREPANCY")
    print("=" * 60)
    
    with engine.connect() as conn:
        
        # 1. Get data from flippable table for precinct 74
        print("\n1️⃣ FLIPPABLE TABLE DATA (what the web page shows):")
        print("-" * 50)
        
        flippable_query = '''
        SELECT county, precinct, contest_name, election_date,
               dem_votes, oppo_votes, gov_votes, dem_margin, dva_pct_needed,
               (oppo_votes - dem_votes) as vote_gap
        FROM flippable 
        WHERE precinct = '74'
        AND dem_margin < 0  -- Republicans winning
        ORDER BY dem_margin DESC
        '''
        
        result = conn.execute(text(flippable_query))
        flippable_data = pd.DataFrame(result.fetchall(), columns=[
            'county', 'precinct', 'contest_name', 'election_date',
            'dem_votes', 'oppo_votes', 'gov_votes', 'dem_margin', 
            'dva_pct_needed', 'vote_gap'
        ])
        
        print(f"Found {len(flippable_data)} races in flippable table for precinct 74")
        if len(flippable_data) > 0:
            print("\nTop 5 races from flippable table:")
            for idx, race in flippable_data.head().iterrows():
                print(f"  {race['contest_name']} ({race['election_date']})")
                print(f"    DEM: {race['dem_votes']}, REP: {race['oppo_votes']}, Gap: {race['vote_gap']}")
        
        # 2. Get data directly from candidate_vote_results for precinct 74
        print(f"\n2️⃣ DIRECT CANDIDATE_VOTE_RESULTS DATA (your temp table approach):")
        print("-" * 50)
        
        # Create the same temp tables approach you used
        direct_query = '''
        WITH temp_dem AS (
            SELECT county, precinct, contest_name, election_date,
                   SUM(total_votes) as dem_votes
            FROM candidate_vote_results 
            WHERE choice_party = 'DEM'
            AND precinct = '74'
            GROUP BY county, precinct, contest_name, election_date
        ),
        temp_oppo AS (
            SELECT county, precinct, contest_name, election_date,
                   SUM(total_votes) as oppo_votes
            FROM candidate_vote_results 
            WHERE choice_party = 'REP'
            AND precinct = '74'
            GROUP BY county, precinct, contest_name, election_date
        )
        SELECT o.county, o.precinct, o.contest_name, o.election_date,
               d.dem_votes, o.oppo_votes, 
               (d.dem_votes - o.oppo_votes) as vote_gap
        FROM temp_dem d
        LEFT JOIN temp_oppo o ON 
            d.precinct = o.precinct AND
            d.election_date = o.election_date AND
            d.contest_name = o.contest_name
        WHERE d.precinct = '74' 
        AND (d.dem_votes - o.oppo_votes) < 0  -- Republicans winning
        ORDER BY (d.dem_votes - o.oppo_votes) DESC
        '''
        
        result = conn.execute(text(direct_query))
        direct_data = pd.DataFrame(result.fetchall(), columns=[
            'county', 'precinct', 'contest_name', 'election_date',
            'dem_votes', 'oppo_votes', 'vote_gap'
        ])
        
        print(f"Found {len(direct_data)} races from direct query for precinct 74")
        if len(direct_data) > 0:
            print("\nTop 5 races from direct query:")
            for idx, race in direct_data.head().iterrows():
                print(f"  {race['contest_name']} ({race['election_date']})")
                print(f"    DEM: {race['dem_votes']}, REP: {race['oppo_votes']}, Gap: {race['vote_gap']}")
        
        # 3. Compare the two datasets
        print(f"\n3️⃣ COMPARISON ANALYSIS:")
        print("-" * 50)
        
        if len(flippable_data) > 0 and len(direct_data) > 0:
            # Merge for comparison
            flippable_compare = flippable_data[['contest_name', 'election_date', 'dem_votes', 'oppo_votes', 'vote_gap']].copy()
            flippable_compare['source'] = 'flippable_table'
            
            direct_compare = direct_data[['contest_name', 'election_date', 'dem_votes', 'oppo_votes', 'vote_gap']].copy()
            direct_compare['source'] = 'direct_query'
            
            # Find races that exist in both
            merged = pd.merge(
                flippable_compare, direct_compare,
                on=['contest_name', 'election_date'],
                suffixes=('_flippable', '_direct'),
                how='outer'
            )
            
            print(f"Races in flippable table only: {len(merged[merged['source_direct'].isna()])}")
            print(f"Races in direct query only: {len(merged[merged['source_flippable'].isna()])}")
            print(f"Races in both: {len(merged[merged['source_direct'].notna() & merged['source_flippable'].notna()])}")
            
            # Check for differences in vote counts
            both_sources = merged[merged['source_direct'].notna() & merged['source_flippable'].notna()]
            if len(both_sources) > 0:
                vote_diffs = both_sources[
                    (both_sources['dem_votes_flippable'] != both_sources['dem_votes_direct']) |
                    (both_sources['oppo_votes_flippable'] != both_sources['oppo_votes_direct'])
                ]
                
                if len(vote_diffs) > 0:
                    print(f"\n⚠️  VOTE COUNT DISCREPANCIES FOUND: {len(vote_diffs)} races")
                    for idx, race in vote_diffs.head().iterrows():
                        print(f"  {race['contest_name']} ({race['election_date']})")
                        print(f"    Flippable: DEM {race['dem_votes_flippable']}, REP {race['oppo_votes_flippable']}")
                        print(f"    Direct:    DEM {race['dem_votes_direct']}, REP {race['oppo_votes_direct']}")
                else:
                    print(f"✅ No vote count discrepancies found in overlapping races")
        
        # 4. Check if flippable table has filtering criteria
        print(f"\n4️⃣ FLIPPABLE TABLE CRITERIA CHECK:")
        print("-" * 50)
        
        criteria_query = '''
        SELECT 
            MIN(dem_margin) as min_dem_margin,
            MAX(dem_margin) as max_dem_margin,
            MIN(dem_votes + oppo_votes) as min_total_votes,
            MAX(dem_votes + oppo_votes) as max_total_votes,
            COUNT(*) as total_races
        FROM flippable
        WHERE precinct = '74'
        '''
        
        result = conn.execute(text(criteria_query))
        criteria = result.fetchone()
        
        print(f"Flippable table criteria for precinct 74:")
        print(f"  Dem margin range: {criteria[0]} to {criteria[1]}")
        print(f"  Total votes range: {criteria[2]} to {criteria[3]}")
        print(f"  Total races: {criteria[4]}")
        
        # 5. Get all candidate_vote_results for precinct 74 to see full picture
        print(f"\n5️⃣ RAW CANDIDATE_VOTE_RESULTS SUMMARY:")
        print("-" * 50)
        
        raw_summary_query = '''
        SELECT 
            contest_name,
            election_date,
            COUNT(DISTINCT choice_party) as parties,
            SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as dem_total,
            SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) as rep_total,
            SUM(total_votes) as all_votes
        FROM candidate_vote_results
        WHERE precinct = '74'
        GROUP BY contest_name, election_date
        HAVING SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) > 0
           AND SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) > 0
           AND SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) > 
               SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END)
        ORDER BY (SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) - 
                  SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END)) DESC
        LIMIT 10
        '''
        
        result = conn.execute(text(raw_summary_query))
        raw_summary = pd.DataFrame(result.fetchall(), columns=[
            'contest_name', 'election_date', 'parties', 'dem_total', 'rep_total', 'all_votes'
        ])
        
        print(f"Top 10 Republican-winning races in precinct 74 (raw data):")
        for idx, race in raw_summary.iterrows():
            gap = race['dem_total'] - race['rep_total']
            print(f"  {race['contest_name']} ({race['election_date']})")
            print(f"    DEM: {race['dem_total']}, REP: {race['rep_total']}, Gap: {gap}")

def main():
    """Run the investigation."""
    investigate_precinct_74_discrepancy()

if __name__ == "__main__":
    main()