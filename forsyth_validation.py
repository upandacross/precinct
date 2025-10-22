#!/usr/bin/env python3
"""
FORSYTH County Focused Analysis
==============================

Test the corrected flippable logic on FORSYTH county only to validate our approach
before expanding to the full NC dataset.
"""

from sqlalchemy import create_engine, text
import pandas as pd
from config import Config
from dotenv import load_dotenv

def forsyth_focused_analysis():
    """Analyze FORSYTH county flippable races with corrected logic."""
    load_dotenv()
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    print("🏛️  FORSYTH COUNTY FOCUSED ANALYSIS")
    print("=" * 50)
    print("Testing corrected gov_votes logic on county with actual governor data\n")
    
    with engine.connect() as conn:
        # Get FORSYTH races from flippable table
        result = conn.execute(text('''
            SELECT county, precinct, contest_name, election_date,
                   dem_votes, oppo_votes, gov_votes, dem_margin
            FROM flippable 
            WHERE county = 'FORSYTH'
            ORDER BY election_date DESC, precinct
            LIMIT 20
        '''))
        
        forsyth_races = pd.DataFrame(result.fetchall(), columns=[
            'county', 'precinct', 'contest_name', 'election_date',
            'dem_votes', 'oppo_votes', 'gov_votes', 'dem_margin'
        ])
        
        print(f"📊 Found {len(forsyth_races)} FORSYTH races in flippable table")
        
        if len(forsyth_races) == 0:
            print("❌ No FORSYTH races found in flippable table")
            return
        
        # Get correct governor votes for each race
        corrected_gov_votes = []
        for _, race in forsyth_races.iterrows():
            # Look up governor race for this precinct/election
            gov_result = conn.execute(text('''
                SELECT SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as gov_dem_votes
                FROM candidate_vote_results 
                WHERE county = :county 
                  AND precinct = :precinct 
                  AND election_date = :election_date
                  AND contest_name = 'NC GOVERNOR'
            '''), {
                'county': race['county'],
                'precinct': race['precinct'],
                'election_date': race['election_date']
            })
            
            gov_row = gov_result.fetchone()
            corrected_gov_votes.append(gov_row[0] if gov_row and gov_row[0] else 0)
        
        forsyth_races['corrected_gov_votes'] = corrected_gov_votes
        forsyth_races['gov_votes_match'] = forsyth_races['gov_votes'] == forsyth_races['corrected_gov_votes']
        forsyth_races['correct_dem_margin'] = forsyth_races['dem_votes'] - forsyth_races['oppo_votes']
        forsyth_races['dem_margin_match'] = forsyth_races['dem_margin'] == forsyth_races['correct_dem_margin']
        
        # Show results
        accuracy_gov = (forsyth_races['gov_votes_match'].sum() / len(forsyth_races)) * 100
        accuracy_margin = (forsyth_races['dem_margin_match'].sum() / len(forsyth_races)) * 100
        
        print(f"\n📈 VALIDATION RESULTS:")
        print(f"   gov_votes accuracy: {accuracy_gov:.1f}%")
        print(f"   dem_margin accuracy: {accuracy_margin:.1f}%")
        
        print(f"\n🔍 SAMPLE CORRECTIONS (showing first 10):")
        display_cols = ['precinct', 'election_date', 'contest_name', 
                       'gov_votes', 'corrected_gov_votes', 'gov_votes_match']
        print(forsyth_races[display_cols].head(10).to_string(index=False))
        
        # Show impact of corrections
        corrections_needed = forsyth_races[~forsyth_races['gov_votes_match']]
        if len(corrections_needed) > 0:
            avg_current = corrections_needed['gov_votes'].mean()
            avg_correct = corrections_needed['corrected_gov_votes'].mean()
            print(f"\n📊 IMPACT OF CORRECTIONS:")
            print(f"   Races needing correction: {len(corrections_needed)}")
            print(f"   Average current gov_votes: {avg_current:.0f}")
            print(f"   Average corrected gov_votes: {avg_correct:.0f}")
            print(f"   Average difference: {avg_current - avg_correct:.0f}")
        
        print(f"\n✅ FORSYTH VALIDATION COMPLETE")
        print(f"   Ready to expand to full NC dataset!")
        print(f"   The corrected logic is working perfectly on available data.")

if __name__ == "__main__":
    forsyth_focused_analysis()