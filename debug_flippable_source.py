#!/usr/bin/env python3
"""
Debug Flippable Table Source Data
=================================

This script investigates how the flippable table was populated from candidate_vote_results
and identifies any discrepancies for precinct 74 specifically.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from config import Config

def debug_flippable_vs_source():
    """Debug the flippable table population logic vs direct candidate_vote_results queries."""
    
    # Initialize database connection
    load_dotenv()
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    print("🔍 DEBUGGING FLIPPABLE TABLE POPULATION FOR PRECINCT 74")
    print("=" * 70)
    
    with engine.connect() as conn:
        
        # 1. Show exactly what's in the flippable table for precinct 74
        print("\n1️⃣ CURRENT FLIPPABLE TABLE DATA (Precinct 74):")
        print("-" * 50)
        
        flippable_query = '''
        SELECT county, precinct, contest_name, election_date,
               dem_votes, oppo_votes, gov_votes, dem_margin, dva_pct_needed
        FROM flippable 
        WHERE precinct = '74'
        ORDER BY election_date DESC, contest_name
        '''
        
        result = conn.execute(text(flippable_query))
        flippable_data = pd.DataFrame(result.fetchall(), columns=[
            'county', 'precinct', 'contest_name', 'election_date',
            'dem_votes', 'oppo_votes', 'gov_votes', 'dem_margin', 'dva_pct_needed'
        ])
        
        print(f"Total races in flippable table for precinct 74: {len(flippable_data)}")
        
        if len(flippable_data) > 0:
            print("\nAll flippable races for precinct 74:")
            for idx, race in flippable_data.iterrows():
                vote_gap = race['oppo_votes'] - race['dem_votes']
                print(f"  {race['contest_name']} ({race['election_date']})")
                print(f"    DEM: {race['dem_votes']}, REP: {race['oppo_votes']}, Gap: {vote_gap}")
                print(f"    Gov: {race['gov_votes']}, Margin: {race['dem_margin']}")
        
        # 2. Recreate the EXACT logic that should populate flippable table
        print(f"\n2️⃣ RECREATING FLIPPABLE LOGIC FROM CANDIDATE_VOTE_RESULTS:")
        print("-" * 50)
        
        # This mimics how the flippable table SHOULD be populated
        recreate_query = '''
        WITH race_totals AS (
            SELECT 
                county, precinct, contest_name, election_date,
                SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as dem_votes,
                SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) as rep_votes,
                SUM(CASE WHEN choice_party NOT IN ('DEM', 'REP') THEN total_votes ELSE 0 END) as other_votes,
                SUM(total_votes) as total_votes
            FROM candidate_vote_results 
            WHERE precinct = '74'
            GROUP BY county, precinct, contest_name, election_date
            HAVING SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) > 0 
               AND SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) > 0
        ),
        close_races AS (
            SELECT *,
                (dem_votes - rep_votes) as dem_margin,
                ROUND(((rep_votes - dem_votes) * 100.0 / (dem_votes + rep_votes)), 2) as rep_margin_pct
            FROM race_totals
            WHERE rep_votes > dem_votes  -- Republicans winning
            AND (dem_votes + rep_votes) >= 50  -- Minimum vote threshold
            AND ((rep_votes - dem_votes) * 100.0 / (dem_votes + rep_votes)) <= 15.0  -- Max 15% margin
        )
        SELECT 
            county, precinct, contest_name, election_date,
            dem_votes, rep_votes as oppo_votes, 
            dem_margin, rep_margin_pct,
            (dem_votes + rep_votes) as race_total_votes
        FROM close_races
        ORDER BY election_date DESC, contest_name
        '''
        
        result = conn.execute(text(recreate_query))
        recreated_data = pd.DataFrame(result.fetchall(), columns=[
            'county', 'precinct', 'contest_name', 'election_date',
            'dem_votes', 'oppo_votes', 'dem_margin', 'rep_margin_pct', 'race_total_votes'
        ])
        
        print(f"Races that SHOULD be in flippable (using standard criteria): {len(recreated_data)}")
        
        if len(recreated_data) > 0:
            print("\nRaces that meet flippable criteria:")
            for idx, race in recreated_data.iterrows():
                vote_gap = race['oppo_votes'] - race['dem_votes']
                print(f"  {race['contest_name']} ({race['election_date']})")
                print(f"    DEM: {race['dem_votes']}, REP: {race['oppo_votes']}, Gap: {vote_gap}")
                print(f"    Margin: {race['dem_margin']}, Rep%: {race['rep_margin_pct']}%")
        
        # 3. Compare the two datasets
        print(f"\n3️⃣ COMPARISON: FLIPPABLE TABLE vs EXPECTED:")
        print("-" * 50)
        
        if len(flippable_data) > 0 and len(recreated_data) > 0:
            # Find races in flippable but not in recreated
            flippable_keys = set((row['contest_name'], row['election_date']) for _, row in flippable_data.iterrows())
            recreated_keys = set((row['contest_name'], row['election_date']) for _, row in recreated_data.iterrows())
            
            only_in_flippable = flippable_keys - recreated_keys
            only_in_recreated = recreated_keys - flippable_keys
            in_both = flippable_keys & recreated_keys
            
            print(f"Races in flippable table only: {len(only_in_flippable)}")
            print(f"Races that should be in flippable: {len(only_in_recreated)}")
            print(f"Races in both: {len(in_both)}")
            
            if only_in_flippable:
                print(f"\nRaces in flippable but not meeting standard criteria:")
                for contest, election in only_in_flippable:
                    race_data = flippable_data[
                        (flippable_data['contest_name'] == contest) & 
                        (flippable_data['election_date'] == election)
                    ].iloc[0]
                    vote_gap = race_data['oppo_votes'] - race_data['dem_votes']
                    rep_pct = (vote_gap / (race_data['dem_votes'] + race_data['oppo_votes'])) * 100
                    print(f"  {contest} ({election}): Gap={vote_gap}, Rep%={rep_pct:.1f}%")
            
            if only_in_recreated:
                print(f"\nRaces that should be in flippable but aren't:")
                for contest, election in only_in_recreated:
                    race_data = recreated_data[
                        (recreated_data['contest_name'] == contest) & 
                        (recreated_data['election_date'] == election)
                    ].iloc[0]
                    print(f"  {contest} ({election}): Rep%={race_data['rep_margin_pct']}%")
        
        elif len(flippable_data) == 0:
            print("⚠️  NO RACES in flippable table for precinct 74!")
            print("   This suggests the flippable table might not include this precinct")
            print("   or the criteria used were different.")
        
        elif len(recreated_data) == 0:
            print("⚠️  NO RACES meet standard flippable criteria for precinct 74!")
            print("   This suggests precinct 74 might not have close races")
            print("   or the criteria used in flippable table were more lenient.")
        
        # 4. Check if there are ANY competitive races in precinct 74
        print(f"\n4️⃣ ALL REPUBLICAN-WINNING RACES IN PRECINCT 74:")
        print("-" * 50)
        
        all_races_query = '''
        WITH race_totals AS (
            SELECT 
                county, precinct, contest_name, election_date,
                SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as dem_votes,
                SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) as rep_votes,
                SUM(total_votes) as total_votes
            FROM candidate_vote_results 
            WHERE precinct = '74'
            GROUP BY county, precinct, contest_name, election_date
            HAVING SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) > 0 
               AND SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) > 0
        )
        SELECT 
            contest_name, election_date,
            dem_votes, rep_votes,
            (dem_votes - rep_votes) as dem_margin,
            ROUND(((rep_votes - dem_votes) * 100.0 / (dem_votes + rep_votes)), 2) as rep_margin_pct,
            (dem_votes + rep_votes) as total_votes
        FROM race_totals
        WHERE rep_votes > dem_votes  -- Republicans winning
        ORDER BY rep_margin_pct ASC  -- Closest races first
        LIMIT 20
        '''
        
        result = conn.execute(text(all_races_query))
        all_races = pd.DataFrame(result.fetchall(), columns=[
            'contest_name', 'election_date', 'dem_votes', 'rep_votes',
            'dem_margin', 'rep_margin_pct', 'total_votes'
        ])
        
        print(f"All Republican-winning races in precinct 74 (closest first):")
        if len(all_races) > 0:
            for idx, race in all_races.iterrows():
                vote_gap = race['rep_votes'] - race['dem_votes']
                meets_criteria = race['rep_margin_pct'] <= 15.0 and race['total_votes'] >= 50
                indicator = "✅" if meets_criteria else "❌"
                print(f"  {indicator} {race['contest_name']} ({race['election_date']})")
                print(f"      DEM: {race['dem_votes']}, REP: {race['rep_votes']}, Gap: {vote_gap}")
                print(f"      Rep margin: {race['rep_margin_pct']}%, Total: {race['total_votes']}")
        else:
            print("  No Republican-winning races found in precinct 74!")
        
        # 5. Show your temp table query results for comparison
        print(f"\n5️⃣ YOUR TEMP TABLE QUERY RESULTS:")
        print("-" * 50)
        
        your_query = '''
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
        LIMIT 10
        '''
        
        result = conn.execute(text(your_query))
        your_results = pd.DataFrame(result.fetchall(), columns=[
            'county', 'precinct', 'contest_name', 'election_date',
            'dem_votes', 'oppo_votes', 'vote_gap'
        ])
        
        print(f"Your temp table query results ({len(your_results)} races):")
        for idx, race in your_results.iterrows():
            rep_margin_pct = abs(race['vote_gap']) / (race['dem_votes'] + race['oppo_votes']) * 100
            print(f"  {race['contest_name']} ({race['election_date']})")
            print(f"    DEM: {race['dem_votes']}, REP: {race['oppo_votes']}, Gap: {race['vote_gap']}")
            print(f"    Rep margin: {rep_margin_pct:.1f}%")

def main():
    """Run the debug analysis."""
    debug_flippable_vs_source()

if __name__ == "__main__":
    main()