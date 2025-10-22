#!/usr/bin/env python3
"""
Corrected Flippable Table Updater
=================================

This script correctly implements the original flippable table logic:
- gov_votes: Democratic votes from governor's race in same precinct/election
- If no governor's race, uses most recent governor's race
- dem_margin: dem_votes - oppo_votes

Usage:
    python3 corrected_flippable_updater.py [--dry-run] [--max-margin 15.0]
"""

import os
import pandas as pd
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime

class CorrectedFlippableUpdater:
    """Updates flippable table with correct gov_votes logic."""
    
    def __init__(self, max_margin=15.0, min_votes=50):
        """Initialize with database connection and criteria."""
        load_dotenv()
        self.db_url = (
            f'postgresql://{os.getenv("POSTGRES_USER")}:'
            f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
            f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
        )
        self.engine = create_engine(self.db_url)
        self.max_margin = max_margin
        self.min_votes = min_votes
        
    def get_governor_votes_by_precinct(self):
        """Get Democratic governor votes by precinct and election."""
        print("🏛️  Getting governor vote data by precinct...")
        
        query = '''
        SELECT 
            county, precinct, election_date,
            SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as gov_dem_votes
        FROM candidate_vote_results 
        WHERE contest_name ILIKE '%GOVERNOR%'
            AND choice_party = 'DEM'
        GROUP BY county, precinct, election_date
        ORDER BY county, precinct, election_date
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            gov_data = pd.DataFrame(result.fetchall(), columns=[
                'county', 'precinct', 'election_date', 'gov_dem_votes'
            ])
            
        print(f"✅ Found governor data for {len(gov_data)} precinct/election combinations")
        return gov_data
    
    def get_most_recent_governor_vote(self, county, precinct, gov_data):
        """Get most recent governor vote for a precinct if current election has none."""
        precinct_gov = gov_data[
            (gov_data['county'] == county) & 
            (gov_data['precinct'] == precinct)
        ].sort_values('election_date', ascending=False)
        
        if len(precinct_gov) > 0:
            return int(precinct_gov.iloc[0]['gov_dem_votes'])
        else:
            return 0  # No governor data available
    
    def find_flippable_races_with_correct_gov_votes(self):
        """Find flippable races with correct gov_votes implementation."""
        print(f"🔍 Finding flippable races with correct gov_votes logic...")
        print(f"   - Maximum Republican margin: {self.max_margin}%")
        print(f"   - Minimum total votes: {self.min_votes}")
        
        # First get all governor vote data
        gov_data = self.get_governor_votes_by_precinct()
        
        # Get competitive races
        query = '''
        WITH race_totals AS (
            SELECT 
                county, precinct, contest_name, election_date,
                SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as dem_votes,
                SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) as rep_votes,
                SUM(CASE WHEN choice_party NOT IN ('DEM', 'REP') THEN total_votes ELSE 0 END) as other_votes,
                SUM(total_votes) as total_votes
            FROM candidate_vote_results 
            WHERE choice_party IN ('DEM', 'REP')
            GROUP BY county, precinct, contest_name, election_date
            HAVING SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) > 0 
               AND SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) > 0
        ),
        margins AS (
            SELECT *,
                (rep_votes - dem_votes) as vote_diff,
                ROUND(((rep_votes - dem_votes) * 100.0 / total_votes), 2) as rep_margin_pct,
                ROUND(((rep_votes - dem_votes + 1) * 100.0 / (total_votes + 2)), 2) as dva_pct_needed
            FROM race_totals
            WHERE rep_votes > dem_votes  -- Republicans currently winning
        ),
        close_races AS (
            SELECT *
            FROM margins 
            WHERE rep_margin_pct BETWEEN 0.1 AND :max_margin
              AND total_votes >= :min_votes
        ),
        new_flippable AS (
            SELECT cr.*
            FROM close_races cr
            LEFT JOIN flippable f ON cr.county = f.county 
                                 AND cr.precinct = f.precinct 
                                 AND cr.contest_name = f.contest_name
                                 AND cr.election_date = f.election_date
            WHERE f.id IS NULL  -- Not already in flippable table
        )
        SELECT 
            county, precinct, contest_name, election_date,
            dem_votes, rep_votes, total_votes, 
            vote_diff, rep_margin_pct, dva_pct_needed
        FROM new_flippable 
        ORDER BY rep_margin_pct ASC
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {
                'max_margin': self.max_margin,
                'min_votes': self.min_votes
            })
            
            races = pd.DataFrame(result.fetchall(), columns=[
                'county', 'precinct', 'contest_name', 'election_date',
                'dem_votes', 'rep_votes', 'total_votes', 
                'vote_diff', 'rep_margin_pct', 'dva_pct_needed'
            ])
        
        if len(races) == 0:
            print("✅ No new flippable races found")
            return races
            
        # Add correct gov_votes for each race
        print(f"🏛️  Adding correct gov_votes for {len(races)} races...")
        
        races['gov_votes'] = 0
        for idx, race in races.iterrows():
            # First check if this election has a governor's race for this precinct
            same_election_gov = gov_data[
                (gov_data['county'] == race['county']) &
                (gov_data['precinct'] == race['precinct']) &
                (gov_data['election_date'] == race['election_date'])
            ]
            
            if len(same_election_gov) > 0:
                # Use governor votes from same election
                races.at[idx, 'gov_votes'] = int(same_election_gov.iloc[0]['gov_dem_votes'])
            else:
                # Use most recent governor vote for this precinct
                most_recent = self.get_most_recent_governor_vote(
                    race['county'], race['precinct'], gov_data
                )
                races.at[idx, 'gov_votes'] = most_recent
        
        print(f"✅ Found {len(races)} new flippable races with correct gov_votes")
        return races
    
    def add_races_to_flippable_table(self, new_races, dry_run=True):
        """Add races to flippable table with correct logic."""
        if len(new_races) == 0:
            print("No races to add.")
            return 0
            
        if dry_run:
            print(f"🔍 DRY RUN: Would add {len(new_races)} races to flippable table")
            self.preview_gov_votes_logic(new_races)
            return 0
        
        print(f"💾 Adding {len(new_races)} new races to flippable table...")
        
        # Prepare data with correct calculations
        insert_data = []
        for idx, row in new_races.iterrows():
            insert_data.append({
                'county': row['county'],
                'election_date': row['election_date'],
                'precinct': row['precinct'],
                'contest_name': row['contest_name'],
                'vote_for': 1,
                'source_file': 'corrected_flippable_updater',
                'imported_at': datetime.now(),
                'dem_votes': int(row['dem_votes']),
                'oppo_votes': int(row['rep_votes']),
                'gov_votes': int(row['gov_votes']),  # Correct gov_votes logic
                'dem_margin': int(row['dem_votes'] - row['rep_votes']),  # dem_votes - oppo_votes
                'dva_pct_needed': float(row['dva_pct_needed'])
            })
        
        insert_query = '''
        INSERT INTO flippable (
            county, election_date, precinct, contest_name, vote_for,
            source_file, imported_at, dem_votes, oppo_votes, gov_votes,
            dem_margin, dva_pct_needed
        ) VALUES (
            :county, :election_date, :precinct, :contest_name, :vote_for,
            :source_file, :imported_at, :dem_votes, :oppo_votes, :gov_votes,
            :dem_margin, :dva_pct_needed
        )
        '''
        
        try:
            with self.engine.connect() as conn:
                with conn.begin():
                    for record in insert_data:
                        conn.execute(text(insert_query), record)
                    
            print(f"✅ Successfully added {len(new_races)} races to flippable table")
            return len(new_races)
            
        except Exception as e:
            print(f"❌ Error adding races to flippable table: {e}")
            return 0
    
    def preview_gov_votes_logic(self, races, limit=10):
        """Preview how gov_votes logic works."""
        print(f"\n🏛️  GOV_VOTES LOGIC PREVIEW")
        print("=" * 60)
        
        preview_races = races.head(limit)
        for idx, race in preview_races.iterrows():
            print(f"📍 {race['county']} Precinct {race['precinct']}")
            print(f"   Contest: {race['contest_name']}")
            print(f"   Election: {race['election_date']}")
            print(f"   Race votes: DEM {race['dem_votes']} vs REP {race['rep_votes']}")
            print(f"   Gov votes (DEM): {race['gov_votes']}")
            print(f"   Dem margin: {race['dem_votes'] - race['rep_votes']} (dem_votes - oppo_votes)")
            print(f"   Rep margin: {race['rep_margin_pct']}%")
            print()

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Update flippable table with correct gov_votes logic')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview changes without updating database')
    parser.add_argument('--max-margin', type=float, default=15.0,
                       help='Maximum Republican margin percentage (default: 15.0)')
    parser.add_argument('--min-votes', type=int, default=50,
                       help='Minimum total votes in race (default: 50)')
    
    args = parser.parse_args()
    
    print("🏛️  CORRECTED FLIPPABLE UPDATER")
    print("=" * 50)
    print("Implementing original gov_votes logic:")
    print("- gov_votes = Democratic votes from governor's race in same precinct")
    print("- If no governor's race, use most recent governor's race")
    print("- dem_margin = dem_votes - oppo_votes")
    print()
    
    # Initialize updater
    updater = CorrectedFlippableUpdater(max_margin=args.max_margin, min_votes=args.min_votes)
    
    # Find races with correct logic
    new_races = updater.find_flippable_races_with_correct_gov_votes()
    
    if len(new_races) == 0:
        print("No new flippable races found with current criteria.")
        return
    
    # Add to database (or dry run)
    added = updater.add_races_to_flippable_table(new_races, dry_run=args.dry_run)
    
    if args.dry_run:
        print(f"\n💡 To actually update the database, run without --dry-run:")
        print(f"   python3 corrected_flippable_updater.py --max-margin {args.max_margin} --min-votes {args.min_votes}")
    else:
        print(f"\n✅ Database updated successfully with correct logic!")
        print(f"   Added: {added} new flippable races")

if __name__ == "__main__":
    main()