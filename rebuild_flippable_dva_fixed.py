#!/usr/bin/env python3
"""
Rebuild Flippable Table with DVA Criteria
========================================

This script rebuilds the flippable table using the correct DVA criteria:
- Vote gap ≤ 100 votes (traditional pathway) OR DVA ≤ 50% (DVA pathway)
- Proper governor vote lookup with three-tier fallback
- Clean temporary table management with automatic cleanup

Usage:
    python3 rebuild_flippable_dva.py [--dry-run] [--backup-existing]
"""

import os
import pandas as pd
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
from config import Config

class FlippableDVARebuilder:
    """Rebuilds the flippable table with proper DVA criteria."""
    
    def __init__(self):
        """Initialize with database connection."""
        load_dotenv()
        self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
    def cleanup_existing_temp_tables(self):
        """Clean up any existing temporary tables."""
        print("🧹 Cleaning up existing temporary tables...")
        
        temp_tables = ['temp_dem', 'temp_oppo', 'temp_dva_races', 'temp_governor_lookup']
        
        with self.engine.connect() as conn:
            for table in temp_tables:
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table}"))
                    conn.commit()
                    print(f"   ✅ Dropped {table} (if it existed)")
                except Exception as e:
                    print(f"   ⚠️  Could not drop {table}: {e}")
    
    def backup_existing_flippable(self):
        """Create a backup of the existing flippable table."""
        print("💾 Creating backup of existing flippable table...")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_table = f"flippable_backup_{timestamp}"
        
        with self.engine.connect() as conn:
            try:
                # Create backup
                conn.execute(text(f"""
                    CREATE TABLE {backup_table} AS 
                    SELECT * FROM flippable
                """))
                conn.commit()
                
                # Get count
                result = conn.execute(text(f"SELECT COUNT(*) FROM {backup_table}"))
                count = result.fetchone()[0]
                
                print(f"   ✅ Created backup table: {backup_table}")
                print(f"   📊 Backed up {count} records")
                return backup_table
                
            except Exception as e:
                print(f"   ❌ Backup failed: {e}")
                return None
    
    def process_all_operations(self, dry_run=False, backup_existing=False):
        """Process all operations in a single connection to maintain temp tables."""
        print("🔄 Processing DVA flippable rebuild...")
        
        with self.engine.connect() as conn:
            # Build governor lookup
            print("🏛️  Building governor votes lookup for all precincts...")
            
            conn.execute(text("""
                CREATE TEMP TABLE temp_governor_lookup AS
                SELECT 
                    county, precinct, election_date,
                    SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as gov_dem_votes
                FROM candidate_vote_results 
                WHERE contest_name = 'NC GOVERNOR'
                  AND choice_party = 'DEM'
                GROUP BY county, precinct, election_date
            """))
            
            # Get statistics
            result = conn.execute(text("SELECT COUNT(*) FROM temp_governor_lookup"))
            count = result.fetchone()[0]
            
            result = conn.execute(text("""
                SELECT COUNT(DISTINCT county || '-' || precinct) FROM temp_governor_lookup
            """))
            precincts = result.fetchone()[0]
            
            print(f"   ✅ Governor lookup created: {count} precinct/election combinations")
            print(f"   📍 Covers {precincts} unique precincts")
            
            # Find DVA viable races
            print("🎯 Finding races that meet DVA criteria...")
            print("   Criteria: Vote gap ≤ 100 OR DVA percentage ≤ 50%")
            
            conn.execute(text("""
                CREATE TEMP TABLE temp_dva_races AS
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
                republican_winning AS (
                    SELECT *,
                        (rep_votes - dem_votes) as vote_gap,
                        (dem_votes + rep_votes) as race_total_votes,
                        ROUND(((rep_votes - dem_votes) * 100.0 / (dem_votes + rep_votes)), 2) as rep_margin_pct
                    FROM race_totals
                    WHERE rep_votes > dem_votes  -- Republicans currently winning
                      AND (dem_votes + rep_votes) >= 50  -- Minimum vote threshold
                ),
                with_governor_votes AS (
                    SELECT 
                        r.*,
                        COALESCE(
                            g1.gov_dem_votes,  -- Same election governor vote
                            g2.gov_dem_votes,  -- Most recent governor vote for precinct
                            g3.avg_gov_votes,  -- County average as fallback
                            r.race_total_votes -- Final fallback
                        ) as gov_votes
                    FROM republican_winning r
                    -- Tier 1: Governor race in same election
                    LEFT JOIN temp_governor_lookup g1 ON 
                        r.county = g1.county AND 
                        r.precinct = g1.precinct AND 
                        r.election_date = g1.election_date
                    -- Tier 2: Most recent governor race for this precinct
                    LEFT JOIN (
                        SELECT DISTINCT ON (county, precinct) 
                            county, precinct, gov_dem_votes
                        FROM temp_governor_lookup
                        ORDER BY county, precinct, election_date DESC
                    ) g2 ON r.county = g2.county AND r.precinct = g2.precinct
                    -- Tier 3: County average as fallback
                    LEFT JOIN (
                        SELECT county, 
                               AVG(gov_dem_votes) as avg_gov_votes
                        FROM temp_governor_lookup
                        GROUP BY county
                    ) g3 ON r.county = g3.county
                ),
                with_dva_calculations AS (
                    SELECT *,
                        GREATEST(0, gov_votes - dem_votes) as dem_absenteeism,
                        CASE 
                            WHEN gov_votes > dem_votes THEN
                                ROUND(((vote_gap + 1) * 100.0 / (gov_votes - dem_votes)), 2)
                            ELSE 999.9
                        END as dva_pct_needed
                    FROM with_governor_votes
                ),
                dva_viable AS (
                    SELECT *,
                        CASE
                            WHEN vote_gap <= 25 THEN '🎯 SLAM DUNK'
                            WHEN vote_gap <= 100 THEN '✅ HIGHLY FLIPPABLE'
                            WHEN dva_pct_needed <= 15 THEN '🎯 SLAM DUNK'
                            WHEN dva_pct_needed <= 35 THEN '✅ HIGHLY FLIPPABLE'
                            WHEN vote_gap <= 300 OR dva_pct_needed <= 50 THEN '🟡 COMPETITIVE'
                            ELSE '🔴 STRETCH GOAL'
                        END as assessment,
                        CASE
                            WHEN vote_gap <= 100 AND dva_pct_needed <= 50 THEN
                                CASE WHEN vote_gap <= dva_pct_needed THEN 'traditional' ELSE 'dva' END
                            WHEN vote_gap <= 100 THEN 'traditional'
                            WHEN dva_pct_needed <= 50 THEN 'dva'
                            ELSE 'difficult'
                        END as best_pathway
                    FROM with_dva_calculations
                )
                SELECT * FROM dva_viable
                WHERE vote_gap <= 100 OR dva_pct_needed <= 50.0  -- DVA criteria
            """))
            
            # Get statistics
            result = conn.execute(text("SELECT COUNT(*) FROM temp_dva_races"))
            total_races = result.fetchone()[0]
            
            result = conn.execute(text("""
                SELECT assessment, COUNT(*) as count
                FROM temp_dva_races
                GROUP BY assessment
                ORDER BY 
                    CASE assessment
                        WHEN '🎯 SLAM DUNK' THEN 1
                        WHEN '✅ HIGHLY FLIPPABLE' THEN 2
                        WHEN '🟡 COMPETITIVE' THEN 3
                        WHEN '🔴 STRETCH GOAL' THEN 4
                        ELSE 5
                    END
            """))
            
            assessment_breakdown = result.fetchall()
            
            print(f"   ✅ Found {total_races} races meeting DVA criteria")
            print(f"   📊 Assessment breakdown:")
            for assessment, count in assessment_breakdown:
                print(f"      {assessment}: {count} races")
            
            # Show pathway breakdown
            result = conn.execute(text("""
                SELECT best_pathway, COUNT(*) as count
                FROM temp_dva_races
                GROUP BY best_pathway
            """))
            
            pathway_breakdown = result.fetchall()
            print(f"   🎯 Best pathway analysis:")
            for pathway, count in pathway_breakdown:
                print(f"      {pathway.title()}: {count} races")
            
            # Rebuild flippable table
            print(f"🔄 {'PREVIEW:' if dry_run else ''} Rebuilding flippable table...")
            
            if not dry_run:
                # Clear existing flippable table
                conn.execute(text("DELETE FROM flippable"))
                print(f"   🗑️  Cleared existing flippable table")
            
            # Insert new data
            insert_query = """
                INSERT INTO flippable (
                    county, precinct, contest_name, election_date,
                    dem_votes, oppo_votes, gov_votes, dem_margin, dva_pct_needed
                )
                SELECT 
                    county, precinct, contest_name, election_date,
                    dem_votes, rep_votes as oppo_votes, gov_votes, 
                    (dem_votes - rep_votes) as dem_margin, dva_pct_needed
                FROM temp_dva_races
            """
            
            if dry_run:
                # Just show what would be inserted
                result = conn.execute(text("""
                    SELECT 
                        county, precinct, contest_name, election_date,
                        dem_votes, rep_votes as oppo_votes, vote_gap, dva_pct_needed, assessment
                    FROM temp_dva_races
                    ORDER BY 
                        CASE assessment
                            WHEN '🎯 SLAM DUNK' THEN 1
                            WHEN '✅ HIGHLY FLIPPABLE' THEN 2
                            WHEN '🟡 COMPETITIVE' THEN 3
                            ELSE 4
                        END,
                        vote_gap ASC
                    LIMIT 10
                """))
                
                preview = result.fetchall()
                print(f"   👀 PREVIEW: Top 10 races that would be inserted:")
                for race in preview:
                    print(f"      {race[0]} P{race[1]} - {race[2]} ({race[3]})")
                    print(f"         Gap: {race[6]}, DVA: {race[7]}%, Assessment: {race[8]}")
                
            else:
                # Actually insert the data
                result = conn.execute(text(insert_query))
                conn.commit()
                
                # Get final count
                result = conn.execute(text("SELECT COUNT(*) FROM flippable"))
                final_count = result.fetchone()[0]
                
                print(f"   ✅ Inserted {final_count} races into flippable table")
                
                # Show summary
                result = conn.execute(text("""
                    SELECT 
                        CASE
                            WHEN (oppo_votes - dem_votes) <= 25 THEN '🎯 SLAM DUNK'
                            WHEN (oppo_votes - dem_votes) <= 100 THEN '✅ HIGHLY FLIPPABLE'
                            WHEN dva_pct_needed <= 15 THEN '🎯 SLAM DUNK (DVA)'
                            WHEN dva_pct_needed <= 35 THEN '✅ HIGHLY FLIPPABLE (DVA)'
                            ELSE '🟡 COMPETITIVE'
                        END as category,
                        COUNT(*) as count
                    FROM flippable
                    GROUP BY 1
                    ORDER BY count DESC
                """))
                
                categories = result.fetchall()
                print(f"   📊 Final flippable table breakdown:")
                for category, count in categories:
                    print(f"      {category}: {count} races")
                
                # Show precinct 74 results
                self.show_precinct_74_results(conn)
            
            return total_races
    
    def show_precinct_74_results(self, conn):
        """Show the results for precinct 74 specifically."""
        print(f"\n🎯 PRECINCT 74 RESULTS:")
        print("-" * 50)
        
        result = conn.execute(text("""
            SELECT contest_name, election_date, dem_votes, oppo_votes, 
                   (oppo_votes - dem_votes) as vote_gap, dva_pct_needed,
                   CASE
                       WHEN (oppo_votes - dem_votes) <= 25 THEN '🎯 SLAM DUNK'
                       WHEN (oppo_votes - dem_votes) <= 100 THEN '✅ HIGHLY FLIPPABLE'
                       WHEN dva_pct_needed <= 15 THEN '🎯 SLAM DUNK (DVA)'
                       WHEN dva_pct_needed <= 35 THEN '✅ HIGHLY FLIPPABLE (DVA)'
                       ELSE '🟡 COMPETITIVE'
                   END as assessment
            FROM flippable 
            WHERE precinct = '74'
            ORDER BY (oppo_votes - dem_votes) ASC
        """))
        
        p74_races = result.fetchall()
        
        if p74_races:
            print(f"Found {len(p74_races)} flippable races for precinct 74:")
            for race in p74_races:
                print(f"  📋 {race[0]} ({race[1]})")
                print(f"     DEM: {race[2]}, REP: {race[3]}, Gap: {race[4]}")
                print(f"     DVA: {race[5]}%, Assessment: {race[6]}")
        else:
            print("No flippable races found for precinct 74")

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Rebuild flippable table with DVA criteria')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview changes without modifying database')
    parser.add_argument('--backup-existing', action='store_true',
                       help='Create backup of existing flippable table')
    parser.add_argument('--skip-cleanup', action='store_true',
                       help='Skip cleanup of existing temporary tables')
    
    args = parser.parse_args()
    
    print("🎯 FLIPPABLE TABLE DVA REBUILDER")
    print("=" * 50)
    print("Implementing DVA criteria:")
    print("- Vote gap ≤ 100 votes (traditional pathway) OR")
    print("- DVA percentage ≤ 50% (DVA pathway)")
    print("- Proper governor vote lookup with three-tier fallback")
    print("- Automatic temporary table cleanup")
    print()
    
    rebuilder = FlippableDVARebuilder()
    
    try:
        # Step 1: Clean up any existing temporary tables
        if not args.skip_cleanup:
            rebuilder.cleanup_existing_temp_tables()
        
        # Step 2: Backup existing table if requested
        if args.backup_existing and not args.dry_run:
            rebuilder.backup_existing_flippable()
        
        # Step 3: Process all operations
        race_count = rebuilder.process_all_operations(
            dry_run=args.dry_run, 
            backup_existing=args.backup_existing
        )
        
        print(f"\n✅ {'Preview completed' if args.dry_run else 'Rebuild completed successfully'}!")
        
        if args.dry_run:
            print(f"💡 Run without --dry-run to actually rebuild the table")
        
    except Exception as e:
        print(f"❌ Error during rebuild: {e}")
        raise

if __name__ == "__main__":
    main()