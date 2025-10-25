#!/usr/bin/env python3
"""
Add Municipal Races to Flippable Table
======================================

Extends the flippable table to include municipal races with proxy DVA calculations
based on partisan crossover performance in the same precincts.

This script:
1. Queries candidate_vote_results for municipal contests
2. Calculates baseline Democratic performance using partisan races in same precincts
3. Computes proxy DVA needed for municipal races
4. Adds municipal races to flippable table with race_type flag

Usage:
    python3 add_municipal_to_flippable.py [--county COUNTY] [--dry-run] [--clear-municipal]
"""

import argparse
import os
import sys
from sqlalchemy import create_engine, text
from datetime import datetime

# Add parent directory to path to import config
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from config import Config
    DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI
except ImportError:
    # Fallback to environment variable
    DATABASE_URL = os.environ.get('DATABASE_URL')
    if not DATABASE_URL:
        print("Error: Cannot import config.py and DATABASE_URL environment variable not set")
        print("Run from project root or set DATABASE_URL environment variable")
        sys.exit(1)


class MunicipalFlippableAdder:
    """Adds municipal races to flippable table with proxy DVA."""
    
    def __init__(self):
        """Initialize with database connection."""
        self.engine = create_engine(DATABASE_URL)
    
    def ensure_race_type_column(self):
        """Add race_type column if it doesn't exist."""
        print("🔧 Ensuring race_type column exists...")
        
        with self.engine.connect() as conn:
            # Check if column exists
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'flippable' 
                AND column_name = 'race_type'
            """))
            
            if result.fetchone() is None:
                # Add the column
                conn.execute(text("""
                    ALTER TABLE flippable 
                    ADD COLUMN race_type VARCHAR(20) DEFAULT 'partisan'
                """))
                
                # Update existing rows
                conn.execute(text("""
                    UPDATE flippable 
                    SET race_type = 'partisan' 
                    WHERE race_type IS NULL
                """))
                
                conn.commit()
                print("   ✅ Added race_type column and set existing rows to 'partisan'")
            else:
                print("   ✅ race_type column already exists")
    
    def clear_existing_municipal(self, county=None):
        """Clear existing municipal races from flippable table."""
        print("🗑️  Clearing existing municipal races...")
        
        with self.engine.connect() as conn:
            if county:
                result = conn.execute(text("""
                    DELETE FROM flippable 
                    WHERE race_type = 'municipal' 
                    AND county = :county
                """), {'county': county})
            else:
                result = conn.execute(text("""
                    DELETE FROM flippable 
                    WHERE race_type = 'municipal'
                """))
            
            conn.commit()
            print(f"   ✅ Deleted {result.rowcount} existing municipal race records")
    
    def get_partisan_baseline(self, county, precinct, conn):
        """
        Calculate baseline Democratic performance in a precinct using partisan races.
        
        Returns:
            tuple: (avg_dem_pct, avg_gov_votes, avg_oppo_votes) or (None, None, None)
        """
        result = conn.execute(text("""
            SELECT 
                AVG(dem_votes::float / NULLIF(dem_votes + oppo_votes, 0)) * 100 as avg_dem_pct,
                AVG(gov_votes) as avg_gov_votes,
                AVG(oppo_votes) as avg_oppo_votes
            FROM flippable
            WHERE county = :county
            AND precinct = :precinct
            AND race_type = 'partisan'
            AND dem_votes IS NOT NULL
            AND oppo_votes IS NOT NULL
            AND gov_votes IS NOT NULL
            AND dem_votes + oppo_votes > 0
        """), {'county': county, 'precinct': precinct})
        
        row = result.fetchone()
        if row and row[0] is not None:
            return (row[0], int(row[1]) if row[1] else None, int(row[2]) if row[2] else None)
        return (None, None, None)
    
    def get_municipal_contests(self, county=None):
        """
        Get municipal contests from candidate_vote_results.
        
        Returns list of dicts with contest info.
        """
        print("📊 Querying municipal contests...")
        
        with self.engine.connect() as conn:
            # Build query
            where_clause = "WHERE county = :county" if county else ""
            
            query = text(f"""
                SELECT DISTINCT
                    county,
                    precinct,
                    contest_name,
                    election_date
                FROM candidate_vote_results
                {where_clause}
                AND (
                    contest_name LIKE 'CITY OF%'
                    OR contest_name LIKE 'TOWN OF%'
                    OR contest_name LIKE 'VILLAGE OF%'
                    OR contest_name LIKE '%MAYOR%'
                    OR contest_name LIKE '%COUNCIL%'
                    OR contest_name LIKE '%ALDERMAN%'
                    OR contest_name LIKE '%BOARD OF COMMISSIONERS%'
                )
                AND contest_name NOT LIKE 'NC %'
                AND contest_name NOT LIKE 'US %'
                AND contest_name NOT LIKE '%GOVERNOR%'
                AND contest_name NOT LIKE '%LIEUTENANT GOVERNOR%'
                AND contest_name NOT LIKE '%ATTORNEY GENERAL%'
                ORDER BY county, election_date DESC, contest_name, precinct
            """)
            
            params = {'county': county} if county else {}
            result = conn.execute(query, params)
            
            contests = []
            for row in result:
                contests.append({
                    'county': row[0],
                    'precinct': row[1],
                    'contest_name': row[2],
                    'election_date': row[3]
                })
            
            print(f"   ✅ Found {len(contests)} municipal contest/precinct combinations")
            return contests
    
    def get_dem_rep_votes(self, county, precinct, contest_name, election_date, conn):
        """
        Get Democratic and Republican vote totals for a municipal contest.
        
        Returns:
            tuple: (dem_votes, rep_votes) or None if data not available
        """
        # Get all candidates for this contest
        result = conn.execute(text("""
            SELECT choice_party, SUM(total_votes) as votes
            FROM candidate_vote_results
            WHERE county = :county
            AND precinct = :precinct
            AND contest_name = :contest_name
            AND election_date = :election_date
            AND choice_party IN ('DEM', 'REP')
            GROUP BY choice_party
        """), {
            'county': county,
            'precinct': precinct,
            'contest_name': contest_name,
            'election_date': election_date
        })
        
        votes = {'DEM': 0, 'REP': 0}
        for row in result:
            votes[row[0]] = row[1]
        
        # Only return if we have both parties (actual contest)
        if votes['DEM'] > 0 and votes['REP'] > 0:
            return (votes['DEM'], votes['REP'])
        
        return None
    
    def add_municipal_races(self, county=None, dry_run=False, clear_existing=False):
        """
        Add municipal races to flippable table with proxy DVA calculations.
        """
        print(f"\n{'='*70}")
        print(f"ADDING MUNICIPAL RACES TO FLIPPABLE TABLE")
        if county:
            print(f"County: {county}")
        if dry_run:
            print("MODE: DRY RUN (preview only)")
        if clear_existing:
            print("MODE: CLEAR EXISTING MUNICIPAL RACES")
        print(f"{'='*70}\n")
        
        # Clear existing municipal races if requested
        # Note: This clears both race_type='municipal' AND municipal contest names
        if clear_existing and not dry_run:
            with self.engine.begin() as conn:  # Use begin() for auto-commit
                where_clause = f"AND county = '{county}'" if county else ""
                # Delete records that are either:
                # 1. Tagged as municipal (race_type='municipal')
                # 2. Have municipal contest names (CITY OF, COUNTY BOARD, etc.)
                result = conn.execute(text(f"""
                    DELETE FROM flippable
                    WHERE (
                        race_type = 'municipal'
                        OR contest_name LIKE 'CITY OF%'
                        OR contest_name LIKE '%BOARD OF COMMISSIONERS%'
                        OR contest_name LIKE '%TOWN OF%'
                        OR contest_name LIKE '%VILLAGE OF%'
                    )
                    {where_clause}
                """))
                print(f"🗑️  Cleared {result.rowcount} existing municipal races\n")
        
        contests = self.get_municipal_contests(county)
        
        if not contests:
            print("❌ No municipal contests found")
            return
        
        added = 0
        skipped_no_partisan = 0
        skipped_no_votes = 0
        skipped_uncontested = 0
        
        # Use begin() for auto-commit transaction
        with self.engine.begin() as conn:
            for contest in contests:
                # Get Democratic and Republican votes
                votes = self.get_dem_rep_votes(
                    contest['county'],
                    contest['precinct'],
                    contest['contest_name'],
                    contest['election_date'],
                    conn
                )
                
                if votes is None:
                    skipped_uncontested += 1
                    continue
                
                dem_votes, rep_votes = votes
                
                # Get partisan baseline for this precinct (includes gov_votes)
                baseline_data = self.get_partisan_baseline(
                    contest['county'],
                    contest['precinct'],
                    conn
                )
                
                if baseline_data[0] is None:
                    skipped_no_partisan += 1
                    continue
                
                baseline_dem_pct, avg_gov_votes, avg_oppo_votes = baseline_data
                
                # Calculate margin
                dem_margin = dem_votes - rep_votes
                
                if dry_run:
                    print(f"   PREVIEW: {contest['county']} P{contest['precinct']} - {contest['contest_name']}")
                    print(f"            Dem: {dem_votes}, Rep: {rep_votes}, Margin: {dem_margin:+d}")
                    print(f"            Baseline: {baseline_dem_pct:.1f}%, Gov votes: {avg_gov_votes}")
                    added += 1
                else:
                    # Insert into flippable table with gov_votes from partisan baseline
                    # The trigger will calculate dva_pct_needed automatically
                    conn.execute(text("""
                        INSERT INTO flippable (
                            county, precinct, contest_name, election_date,
                            dem_votes, oppo_votes, gov_votes, dem_margin,
                            race_type
                        ) VALUES (
                            :county, :precinct, :contest_name, :election_date,
                            :dem_votes, :oppo_votes, :gov_votes, :dem_margin,
                            'municipal'
                        )
                    """), {
                        'county': contest['county'],
                        'precinct': contest['precinct'],
                        'contest_name': contest['contest_name'],
                        'election_date': contest['election_date'],
                        'dem_votes': dem_votes,
                        'oppo_votes': rep_votes,
                        'gov_votes': avg_gov_votes,
                        'dem_margin': dem_margin
                    })
                
                    added += 1
        
        # Print summary
        print(f"\n{'='*70}")
        print("SUMMARY")
        print(f"{'='*70}")
        print(f"✅ Added to flippable: {added}")
        print(f"⚠️  Skipped (no partisan baseline): {skipped_no_partisan}")
        print(f"⚠️  Skipped (no contested votes): {skipped_uncontested}")
        print(f"{'='*70}\n")
        
        if not dry_run and added > 0:
            self.show_sample_results(county)
    
    def show_sample_results(self, county=None):
        """Show sample of added municipal races."""
        print("📊 Sample of FLIPPABLE municipal races (top 10 by DVA, DVA > 0):\n")
        
        with self.engine.connect() as conn:
            where_clause = "AND county = :county" if county else ""
            params = {'county': county} if county else {}
            
            result = conn.execute(text(f"""
                SELECT 
                    county, precinct, contest_name, election_date,
                    dem_votes, oppo_votes, dem_margin, dva_pct_needed,
                    CASE
                        WHEN dva_pct_needed <= 2 THEN '🎯 SLAM DUNK'
                        WHEN dva_pct_needed <= 5 THEN '✅ HIGHLY FLIPPABLE'
                        WHEN dva_pct_needed <= 10 THEN '🟡 COMPETITIVE'
                        ELSE '🔵 LONG SHOT'
                    END as rating
                FROM flippable
                WHERE race_type = 'municipal'
                AND dva_pct_needed > 0
                {where_clause}
                ORDER BY dva_pct_needed ASC
                LIMIT 10
            """), params)
            
            for row in result:
                print(f"{row[8]} {row[0]} P{row[1]} - {row[2]}")
                margin = row[6] if row[6] is not None else 0
                dva = row[7] if row[7] is not None else 0
                print(f"   Date: {row[3]}, Margin: {margin:+d}, DVA: {dva:.1f}%")


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description='Add municipal races to flippable table with proxy DVA calculations'
    )
    parser.add_argument(
        '--county',
        help='Filter to specific county (e.g., FORSYTH)',
        type=str
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Preview changes without modifying database'
    )
    parser.add_argument(
        '--clear-municipal',
        action='store_true',
        help='Clear existing municipal races before adding'
    )
    
    args = parser.parse_args()
    
    adder = MunicipalFlippableAdder()
    
    # Ensure race_type column exists
    if not args.dry_run:
        adder.ensure_race_type_column()
    
    # Add municipal races (clear_existing handled within method)
    adder.add_municipal_races(
        county=args.county,
        dry_run=args.dry_run,
        clear_existing=args.clear_municipal
    )


if __name__ == '__main__':
    main()
