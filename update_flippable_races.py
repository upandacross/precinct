#!/usr/bin/env python3
"""
Flippable Table Updater
=======================

This script identifies and adds newly discovered flippable races to the flippable table.
It analyzes candidate_vote_results to find close races where a small increase in Democratic
votes could flip the outcome.

Criteria for flippable races:
- Republicans currently winning by 15% or less
- Minimum 50 total votes (to filter out very small races)
- Both Democratic and Republican candidates present
- Not already in the flippable table

Usage:
    python3 update_flippable_races.py [--dry-run] [--max-margin 15.0] [--min-votes 50]
"""

import os
import pandas as pd
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime

class FlippableUpdater:
    """Updates the flippable table with newly discovered close races."""
    
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
        
    def find_new_flippable_races(self):
        """Find close races not already in the flippable table."""
        print(f"🔍 Searching for new flippable races...")
        print(f"   - Maximum Republican margin: {self.max_margin}%")
        print(f"   - Minimum total votes: {self.min_votes}")
        
        query = '''
        WITH race_totals AS (
            SELECT 
                county, precinct, contest_name, election_date,
                SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as dem_votes,
                SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) as rep_votes,
                SUM(CASE WHEN choice_party NOT IN ('DEM', 'REP') THEN total_votes ELSE 0 END) as other_votes,
                SUM(total_votes) as total_votes,
                COUNT(DISTINCT choice_party) as parties
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
            WHERE rep_margin_pct BETWEEN 0.1 AND :max_margin  -- Close races
              AND total_votes >= :min_votes  -- Minimum vote threshold
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
            dem_votes, rep_votes, (dem_votes + rep_votes + other_votes) as gov_votes,
            total_votes, vote_diff, rep_margin_pct, dva_pct_needed
        FROM new_flippable 
        ORDER BY rep_margin_pct ASC
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {
                'max_margin': self.max_margin,
                'min_votes': self.min_votes
            })
            
            new_races = pd.DataFrame(result.fetchall(), columns=[
                'county', 'precinct', 'contest_name', 'election_date',
                'dem_votes', 'rep_votes', 'gov_votes', 'total_votes', 
                'vote_diff', 'rep_margin_pct', 'dva_pct_needed'
            ])
            
            # Convert numeric columns to proper types
            numeric_cols = ['dem_votes', 'rep_votes', 'gov_votes', 'total_votes', 
                          'vote_diff', 'rep_margin_pct', 'dva_pct_needed']
            for col in numeric_cols:
                new_races[col] = pd.to_numeric(new_races[col], errors='coerce')
        
        print(f"✅ Found {len(new_races)} new flippable races")
        return new_races
    
    def preview_new_races(self, new_races, limit=10):
        """Preview the closest new flippable races."""
        if len(new_races) == 0:
            print("No new flippable races found.")
            return
            
        print(f"\n📊 Top {min(limit, len(new_races))} closest new flippable races:")
        print("-" * 80)
        
        preview = new_races.head(limit)[['county', 'precinct', 'contest_name', 
                                       'election_date', 'dem_votes', 'rep_votes', 
                                       'rep_margin_pct', 'dva_pct_needed']]
        
        for idx, row in preview.iterrows():
            print(f"{row['county']} Precinct {row['precinct']}")
            print(f"  Contest: {row['contest_name']}")
            print(f"  Election: {row['election_date']}")
            print(f"  Votes: DEM {row['dem_votes']} vs REP {row['rep_votes']}")
            print(f"  Republican margin: {row['rep_margin_pct']}%")
            print(f"  DVA % needed: {row['dva_pct_needed']}%")
            print()
    
    def add_races_to_flippable_table(self, new_races, dry_run=True):
        """Add new races to the flippable table."""
        if len(new_races) == 0:
            print("No races to add.")
            return 0
            
        if dry_run:
            print(f"🔍 DRY RUN: Would add {len(new_races)} races to flippable table")
            return 0
        
        print(f"💾 Adding {len(new_races)} new races to flippable table...")
        
        # Prepare data for insertion
        insert_data = []
        for idx, row in new_races.iterrows():
            insert_data.append({
                'county': row['county'],
                'election_date': row['election_date'],
                'precinct': row['precinct'],
                'contest_name': row['contest_name'],
                'vote_for': 1,  # Assuming single-vote contests
                'source_file': 'flippable_updater',
                'imported_at': datetime.now(),
                'dem_votes': int(row['dem_votes']),
                'oppo_votes': int(row['rep_votes']),
                'gov_votes': int(row['gov_votes']),
                'dem_margin': int(-row['vote_diff']),  # Negative because Dems are losing
                'dva_pct_needed': float(row['dva_pct_needed'])
            })
        
        # Insert data
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
                with conn.begin():  # Transaction
                    for record in insert_data:
                        conn.execute(text(insert_query), record)
                    
            print(f"✅ Successfully added {len(new_races)} races to flippable table")
            return len(new_races)
            
        except Exception as e:
            print(f"❌ Error adding races to flippable table: {e}")
            return 0
    
    def generate_summary_report(self, new_races):
        """Generate a summary report of the new flippable races."""
        if len(new_races) == 0:
            return
            
        print(f"\n📈 SUMMARY REPORT")
        print("=" * 50)
        
        # Overall statistics
        print(f"Total new flippable races: {len(new_races)}")
        print(f"Average Republican margin: {new_races['rep_margin_pct'].mean():.2f}%")
        print(f"Average DVA % needed: {new_races['dva_pct_needed'].mean():.2f}%")
        print()
        
        # By county
        county_stats = new_races.groupby('county').agg({
            'precinct': 'count',
            'rep_margin_pct': 'mean',
            'dva_pct_needed': 'mean'
        }).round(2)
        county_stats.columns = ['races', 'avg_margin_pct', 'avg_dva_needed']
        
        print("By County:")
        for county, stats in county_stats.iterrows():
            print(f"  {county}: {stats['races']} races (avg margin: {stats['avg_margin_pct']}%)")
        print()
        
        # By election year
        new_races['year'] = pd.to_datetime(new_races['election_date']).dt.year
        year_stats = new_races.groupby('year').size()
        print("By Election Year:")
        for year, count in year_stats.items():
            print(f"  {year}: {count} races")
        print()
        
        # Closest races (top 5)
        print("Top 5 closest races:")
        closest = new_races.nsmallest(5, 'rep_margin_pct')
        for idx, row in closest.iterrows():
            print(f"  {row['county']} Precinct {row['precinct']}: {row['rep_margin_pct']}% margin")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Update flippable table with new close races')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview changes without updating database')
    parser.add_argument('--max-margin', type=float, default=15.0,
                       help='Maximum Republican margin percentage (default: 15.0)')
    parser.add_argument('--min-votes', type=int, default=50,
                       help='Minimum total votes in race (default: 50)')
    parser.add_argument('--preview', type=int, default=10,
                       help='Number of races to preview (default: 10)')
    
    args = parser.parse_args()
    
    print("🎯 FLIPPABLE RACES UPDATER")
    print("=" * 40)
    print("Finding close races where small Democratic vote increases could flip outcomes")
    print()
    
    # Initialize updater
    updater = FlippableUpdater(max_margin=args.max_margin, min_votes=args.min_votes)
    
    # Find new flippable races
    new_races = updater.find_new_flippable_races()
    
    if len(new_races) == 0:
        print("No new flippable races found with current criteria.")
        return
    
    # Preview races
    updater.preview_new_races(new_races, limit=args.preview)
    
    # Generate summary report
    updater.generate_summary_report(new_races)
    
    # Add to database (or dry run)
    added = updater.add_races_to_flippable_table(new_races, dry_run=args.dry_run)
    
    if args.dry_run:
        print(f"\n💡 To actually update the database, run without --dry-run:")
        print(f"   python3 update_flippable_races.py --max-margin {args.max_margin} --min-votes {args.min_votes}")
    else:
        print(f"\n✅ Database updated successfully!")
        print(f"   Added: {added} new flippable races")
        print(f"   Total races in flippable table: [run query to check]")


if __name__ == "__main__":
    main()