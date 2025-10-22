#!/usr/bin/env python3
"""
DVA-Focused Flippable Analysis
=============================

This script applies the ORIGINAL DVA criteria we discussed:
- Vote gap ≤ 100 votes (traditional pathway)
- DVA percentage ≤ 50% (DVA pathway) 
- Focus on races where one of these pathways is achievable

Specifically analyzes candidate_vote_results data for precinct 74.
"""

import os
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from config import Config

def analyze_dva_criteria_precinct_74():
    """Apply the original DVA criteria we discussed to precinct 74 races."""
    
    # Initialize database connection
    load_dotenv()
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    print("🎯 DVA-FOCUSED ANALYSIS FOR PRECINCT 74")
    print("Original Criteria:")
    print("- Vote gap ≤ 100 votes (traditional pathway)")
    print("- DVA percentage ≤ 50% (DVA pathway)")
    print("- Focus on Republican-winning races")
    print("=" * 60)
    
    with engine.connect() as conn:
        
        # 1. Get all Republican-winning races in precinct 74 from candidate_vote_results
        print("\n1️⃣ ALL REPUBLICAN-WINNING RACES (Precinct 74):")
        print("-" * 50)
        
        base_query = '''
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
            contest_name, election_date, county,
            dem_votes, rep_votes,
            (rep_votes - dem_votes) as vote_gap,
            ROUND(((rep_votes - dem_votes) * 100.0 / (dem_votes + rep_votes)), 2) as rep_margin_pct,
            (dem_votes + rep_votes) as race_total_votes
        FROM race_totals
        WHERE rep_votes > dem_votes  -- Republicans winning
        ORDER BY (rep_votes - dem_votes) ASC  -- Closest races first
        '''
        
        result = conn.execute(text(base_query))
        all_races = pd.DataFrame(result.fetchall(), columns=[
            'contest_name', 'election_date', 'county', 'dem_votes', 'rep_votes',
            'vote_gap', 'rep_margin_pct', 'race_total_votes'
        ])
        
        print(f"Total Republican-winning races in precinct 74: {len(all_races)}")
        
        # 2. Get Democratic governor votes for DVA calculation
        print("\n2️⃣ GOVERNOR VOTE LOOKUP FOR DVA CALCULATION:")
        print("-" * 50)
        
        gov_query = '''
        SELECT 
            county, precinct, election_date,
            SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as gov_dem_votes
        FROM candidate_vote_results 
        WHERE contest_name = 'NC GOVERNOR'
          AND choice_party = 'DEM'
          AND precinct = '74'
        GROUP BY county, precinct, election_date
        ORDER BY election_date DESC
        '''
        
        result = conn.execute(text(gov_query))
        gov_data = pd.DataFrame(result.fetchall(), columns=[
            'county', 'precinct', 'election_date', 'gov_dem_votes'
        ])
        
        print(f"Governor races found for precinct 74: {len(gov_data)}")
        for idx, gov in gov_data.iterrows():
            print(f"  {gov['election_date']}: {gov['gov_dem_votes']} DEM governor votes")
        
        # Create governor lookup
        gov_lookup = {}
        most_recent_gov = None
        for idx, gov in gov_data.iterrows():
            key = (gov['county'], gov['precinct'], gov['election_date'])
            gov_lookup[key] = gov['gov_dem_votes']
            if most_recent_gov is None or gov['election_date'] > most_recent_gov[0]:
                most_recent_gov = (gov['election_date'], gov['gov_dem_votes'])
        
        # 3. Apply DVA criteria to each race
        print(f"\n3️⃣ DVA CRITERIA ANALYSIS:")
        print("-" * 50)
        
        dva_results = []
        
        for idx, race in all_races.iterrows():
            # Get governor votes for this race
            key = (race['county'], '74', race['election_date'])
            if key in gov_lookup:
                gov_votes = gov_lookup[key]
                gov_source = "Same election"
            elif most_recent_gov:
                gov_votes = most_recent_gov[1]
                gov_source = f"Most recent ({most_recent_gov[0]})"
            else:
                gov_votes = race['race_total_votes']  # Fallback
                gov_source = "Race total (fallback)"
            
            # Calculate DVA metrics
            vote_gap = race['vote_gap']
            dem_absenteeism = gov_votes - race['dem_votes'] if gov_votes > race['dem_votes'] else 0
            
            if dem_absenteeism > 0:
                dva_pct = (vote_gap / dem_absenteeism) * 100
            else:
                dva_pct = 999.9  # Can't calculate DVA
            
            # Apply criteria
            traditional_viable = vote_gap <= 100
            dva_viable = dva_pct <= 50.0 and dem_absenteeism > 0
            
            # Determine assessment based on our original criteria
            if vote_gap <= 25:
                assessment = "🎯 SLAM DUNK (Traditional)"
            elif vote_gap <= 100:
                assessment = "✅ HIGHLY FLIPPABLE (Traditional)"
            elif dva_viable and dva_pct <= 15:
                assessment = "🎯 SLAM DUNK (DVA)"
            elif dva_viable and dva_pct <= 35:
                assessment = "✅ HIGHLY FLIPPABLE (DVA)"
            elif dva_viable:
                assessment = "🟡 COMPETITIVE (DVA)"
            elif vote_gap <= 300:
                assessment = "🟡 COMPETITIVE (Traditional)"
            else:
                assessment = "🔴 STRETCH GOAL"
            
            # Best pathway
            if traditional_viable and dva_viable:
                best_pathway = "Traditional" if vote_gap <= dva_pct else "DVA"
            elif traditional_viable:
                best_pathway = "Traditional"
            elif dva_viable:
                best_pathway = "DVA"
            else:
                best_pathway = "Difficult"
            
            dva_results.append({
                'contest_name': race['contest_name'],
                'election_date': race['election_date'],
                'dem_votes': race['dem_votes'],
                'rep_votes': race['rep_votes'],
                'vote_gap': vote_gap,
                'gov_votes': gov_votes,
                'gov_source': gov_source,
                'dem_absenteeism': dem_absenteeism,
                'dva_pct': round(dva_pct, 1),
                'traditional_viable': traditional_viable,
                'dva_viable': dva_viable,
                'assessment': assessment,
                'best_pathway': best_pathway,
                'rep_margin_pct': race['rep_margin_pct']
            })
        
        # Convert to DataFrame for analysis
        dva_df = pd.DataFrame(dva_results)
        
        # 4. Show results by our criteria
        print(f"\n4️⃣ RACES MEETING DVA CRITERIA:")
        print("-" * 50)
        
        viable_races = dva_df[dva_df['traditional_viable'] | dva_df['dva_viable']]
        
        print(f"Races meeting criteria (≤100 vote gap OR ≤50% DVA): {len(viable_races)}")
        
        if len(viable_races) > 0:
            print("\nDetailed breakdown:")
            for idx, race in viable_races.iterrows():
                print(f"\n  📋 {race['contest_name']} ({race['election_date']})")
                print(f"      DEM: {race['dem_votes']}, REP: {race['rep_votes']}, Gap: {race['vote_gap']}")
                print(f"      Gov votes: {race['gov_votes']} ({race['gov_source']})")
                print(f"      Dem absenteeism: {race['dem_absenteeism']}")
                print(f"      DVA percentage: {race['dva_pct']}%")
                print(f"      Traditional viable: {'✅' if race['traditional_viable'] else '❌'}")
                print(f"      DVA viable: {'✅' if race['dva_viable'] else '❌'}")
                print(f"      Assessment: {race['assessment']}")
                print(f"      Best pathway: {race['best_pathway']}")
        
        # 5. Summary by assessment category
        print(f"\n5️⃣ SUMMARY BY ASSESSMENT CATEGORY:")
        print("-" * 50)
        
        assessment_counts = dva_df['assessment'].value_counts()
        for assessment, count in assessment_counts.items():
            print(f"  {assessment}: {count} races")
        
        # 6. Compare with current flippable table
        print(f"\n6️⃣ COMPARISON WITH CURRENT FLIPPABLE TABLE:")
        print("-" * 50)
        
        flippable_query = '''
        SELECT COUNT(*) as count
        FROM flippable 
        WHERE precinct = '74'
        '''
        
        result = conn.execute(text(flippable_query))
        flippable_count = result.fetchone()[0]
        
        print(f"Current flippable table races for precinct 74: {flippable_count}")
        print(f"Races meeting DVA criteria: {len(viable_races)}")
        print(f"Races meeting strict criteria (≤100 gap OR ≤35% DVA): {len(dva_df[(dva_df['vote_gap'] <= 100) | ((dva_df['dva_viable']) & (dva_df['dva_pct'] <= 35))])}")

def main():
    """Run the DVA-focused analysis."""
    analyze_dva_criteria_precinct_74()

if __name__ == "__main__":
    main()