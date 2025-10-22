#!/usr/bin/env python3
"""
Flippable Table Validator
========================

This script validates the existing flippable table against the original logic:
- Checks if gov_votes matches Democratic governor votes from same/recent election
- Verifies dem_margin = dem_votes - oppo_votes
- Reports discrepancies

Usage:
    python3 validate_flippable_table.py [--sample-size 20]
"""

import os
import pandas as pd
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

class FlippableTableValidator:
    """Validates existing flippable table against original logic."""
    
    def __init__(self):
        """Initialize with database connection."""
        load_dotenv()
        self.db_url = (
            f'postgresql://{os.getenv("POSTGRES_USER")}:'
            f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
            f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
        )
        self.engine = create_engine(self.db_url)
    
    def get_governor_votes_data(self):
        """Get all governor vote data for validation."""
        query = '''
        SELECT 
            county, precinct, election_date,
            SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as gov_dem_votes
        FROM candidate_vote_results 
        WHERE contest_name ILIKE '%GOVERNOR%'
            AND choice_party = 'DEM'
        GROUP BY county, precinct, election_date
        ORDER BY county, precinct, election_date DESC
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            return pd.DataFrame(result.fetchall(), columns=[
                'county', 'precinct', 'election_date', 'gov_dem_votes'
            ])
    
    def get_flippable_sample(self, sample_size=20):
        """Get sample from existing flippable table."""
        query = '''
        SELECT 
            county, precinct, contest_name, election_date,
            dem_votes, oppo_votes, gov_votes, dem_margin,
            dva_pct_needed
        FROM flippable
        ORDER BY RANDOM()
        LIMIT :sample_size
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'sample_size': sample_size})
            return pd.DataFrame(result.fetchall(), columns=[
                'county', 'precinct', 'contest_name', 'election_date',
                'dem_votes', 'oppo_votes', 'gov_votes', 'dem_margin', 'dva_pct_needed'
            ])
    
    def validate_gov_votes_logic(self, flippable_sample, gov_data):
        """Validate gov_votes against original logic."""
        print(f"\n🏛️  VALIDATING GOV_VOTES LOGIC")
        print("=" * 60)
        
        validation_results = []
        
        for idx, race in flippable_sample.iterrows():
            # Find governor votes for same election
            same_election_gov = gov_data[
                (gov_data['county'] == race['county']) &
                (gov_data['precinct'] == race['precinct']) &
                (gov_data['election_date'] == race['election_date'])
            ]
            
            expected_gov_votes = None
            gov_source = "none"
            
            if len(same_election_gov) > 0:
                expected_gov_votes = int(same_election_gov.iloc[0]['gov_dem_votes'])
                gov_source = "same_election"
            else:
                # Find most recent governor vote for this precinct
                precinct_gov = gov_data[
                    (gov_data['county'] == race['county']) & 
                    (gov_data['precinct'] == race['precinct'])
                ].sort_values('election_date', ascending=False)
                
                if len(precinct_gov) > 0:
                    expected_gov_votes = int(precinct_gov.iloc[0]['gov_dem_votes'])
                    most_recent_date = precinct_gov.iloc[0]['election_date']
                    gov_source = f"most_recent_{most_recent_date}"
                else:
                    expected_gov_votes = 0
                    gov_source = "no_data"
            
            # Check if current gov_votes matches expected
            current_gov_votes = race['gov_votes']
            gov_votes_correct = (current_gov_votes == expected_gov_votes)
            
            # Check dem_margin calculation
            expected_dem_margin = race['dem_votes'] - race['oppo_votes']
            dem_margin_correct = (race['dem_margin'] == expected_dem_margin)
            
            validation_results.append({
                'county': race['county'],
                'precinct': race['precinct'],
                'contest': race['contest_name'],
                'election_date': race['election_date'],
                'current_gov_votes': current_gov_votes,
                'expected_gov_votes': expected_gov_votes,
                'gov_votes_correct': gov_votes_correct,
                'gov_source': gov_source,
                'current_dem_margin': race['dem_margin'],
                'expected_dem_margin': expected_dem_margin,
                'dem_margin_correct': dem_margin_correct
            })
        
        return pd.DataFrame(validation_results)
    
    def report_validation_results(self, validation_df):
        """Report validation results."""
        total_races = len(validation_df)
        gov_votes_correct = validation_df['gov_votes_correct'].sum()
        dem_margin_correct = validation_df['dem_margin_correct'].sum()
        
        print(f"VALIDATION SUMMARY:")
        print(f"  Total races checked: {total_races}")
        print(f"  Gov_votes correct: {gov_votes_correct}/{total_races} ({gov_votes_correct/total_races*100:.1f}%)")
        print(f"  Dem_margin correct: {dem_margin_correct}/{total_races} ({dem_margin_correct/total_races*100:.1f}%)")
        print()
        
        # Show gov_votes discrepancies
        gov_discrepancies = validation_df[~validation_df['gov_votes_correct']]
        if len(gov_discrepancies) > 0:
            print(f"🚨 GOV_VOTES DISCREPANCIES ({len(gov_discrepancies)} races):")
            for idx, race in gov_discrepancies.head(5).iterrows():
                print(f"  📍 {race['county']} Precinct {race['precinct']} - {race['contest']}")
                print(f"     Current: {race['current_gov_votes']}, Expected: {race['expected_gov_votes']}")
                print(f"     Source: {race['gov_source']}")
                print()
        
        # Show dem_margin discrepancies
        margin_discrepancies = validation_df[~validation_df['dem_margin_correct']]
        if len(margin_discrepancies) > 0:
            print(f"🚨 DEM_MARGIN DISCREPANCIES ({len(margin_discrepancies)} races):")
            for idx, race in margin_discrepancies.head(5).iterrows():
                print(f"  📍 {race['county']} Precinct {race['precinct']} - {race['contest']}")
                print(f"     Current: {race['current_dem_margin']}, Expected: {race['expected_dem_margin']}")
                print()
        
        # Show gov_votes sources breakdown
        source_counts = validation_df['gov_source'].value_counts()
        print(f"GOV_VOTES SOURCES:")
        for source, count in source_counts.items():
            print(f"  {source}: {count} races")
    
    def show_sample_details(self, validation_df, limit=5):
        """Show detailed sample for understanding."""
        print(f"\n📊 SAMPLE RACE DETAILS:")
        print("=" * 80)
        
        sample_races = validation_df.head(limit)
        for idx, race in sample_races.iterrows():
            status = "✅" if race['gov_votes_correct'] and race['dem_margin_correct'] else "❌"
            print(f"{status} {race['county']} Precinct {race['precinct']}")
            print(f"   Contest: {race['contest']}")
            print(f"   Election: {race['election_date']}")
            print(f"   Gov votes: {race['current_gov_votes']} (expected: {race['expected_gov_votes']}) - {race['gov_source']}")
            print(f"   Dem margin: {race['current_dem_margin']} (expected: {race['expected_dem_margin']})")
            print()

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Validate flippable table against original logic')
    parser.add_argument('--sample-size', type=int, default=20,
                       help='Number of races to validate (default: 20)')
    parser.add_argument('--show-details', action='store_true',
                       help='Show detailed race information')
    
    args = parser.parse_args()
    
    print("🔍 FLIPPABLE TABLE VALIDATOR")
    print("=" * 50)
    print("Checking existing flippable table against original logic:")
    print("- gov_votes should be Democratic governor votes from same/recent election")
    print("- dem_margin should be dem_votes - oppo_votes")
    print()
    
    # Initialize validator
    validator = FlippableTableValidator()
    
    # Get data
    print(f"📊 Loading data...")
    gov_data = validator.get_governor_votes_data()
    flippable_sample = validator.get_flippable_sample(args.sample_size)
    
    print(f"✅ Governor data: {len(gov_data)} precinct/election combinations")
    print(f"✅ Flippable sample: {len(flippable_sample)} races")
    
    # Validate
    validation_results = validator.validate_gov_votes_logic(flippable_sample, gov_data)
    
    # Report results
    validator.report_validation_results(validation_results)
    
    if args.show_details:
        validator.show_sample_details(validation_results)

if __name__ == "__main__":
    main()