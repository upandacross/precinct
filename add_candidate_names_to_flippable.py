#!/usr/bin/env python3
"""
Add candidate name columns to flippable table.

This migration adds dem_candidate and rep_candidate columns to the flippable table
to track which specific candidates were involved in flippable races. This enables
candidate-specific matching for ballot strategy.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def add_candidate_columns():
    """Add dem_candidate and rep_candidate columns to flippable table."""
    
    load_dotenv()
    db_url = (
        f'postgresql://{os.getenv("POSTGRES_USER")}:'
        f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
        f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
    )
    engine = create_engine(db_url)
    
    print("🔧 Adding candidate name columns to flippable table...")
    
    # Check if columns already exist
    check_query = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name = 'flippable' 
        AND column_name IN ('dem_candidate', 'rep_candidate')
    """
    
    with engine.connect() as conn:
        result = conn.execute(text(check_query))
        existing_cols = [row[0] for row in result]
        
        if 'dem_candidate' in existing_cols and 'rep_candidate' in existing_cols:
            print("✅ Columns already exist. No migration needed.")
            return
    
    # Add columns in separate transaction
    with engine.connect() as conn:
        with conn.begin():
            if 'dem_candidate' not in existing_cols:
                print("  Adding dem_candidate column...")
                conn.execute(text("""
                    ALTER TABLE flippable 
                    ADD COLUMN dem_candidate VARCHAR(255)
                """))
            
            if 'rep_candidate' not in existing_cols:
                print("  Adding rep_candidate column...")
                conn.execute(text("""
                    ALTER TABLE flippable 
                    ADD COLUMN rep_candidate VARCHAR(255)
                """))
        
        print("✅ Successfully added candidate name columns to flippable table")
        
    # Backfill in separate transaction
    with engine.connect() as conn:
        # Optionally backfill existing records
        print("\n🔄 Backfilling candidate names for existing flippable races...")
        backfill_query = """
            UPDATE flippable f
            SET 
                dem_candidate = (
                    SELECT candidate_name 
                    FROM candidate_vote_results cvr 
                    WHERE cvr.county = f.county 
                    AND cvr.precinct = f.precinct 
                    AND cvr.contest_name = f.contest_name 
                    AND cvr.election_date = f.election_date 
                    AND cvr.choice_party = 'DEM'
                    LIMIT 1
                ),
                rep_candidate = (
                    SELECT candidate_name 
                    FROM candidate_vote_results cvr 
                    WHERE cvr.county = f.county 
                    AND cvr.precinct = f.precinct 
                    AND cvr.contest_name = f.contest_name 
                    AND cvr.election_date = f.election_date 
                    AND cvr.choice_party = 'REP'
                    LIMIT 1
                )
            WHERE f.dem_candidate IS NULL OR f.rep_candidate IS NULL
        """
        
        with conn.begin():
            result = conn.execute(text(backfill_query))
            updated_count = result.rowcount
        
        print(f"✅ Backfilled {updated_count} existing flippable race records with candidate names")
        
        # Show sample results
        print("\n📊 Sample flippable races with candidate names:")
        sample_query = """
            SELECT county, precinct, contest_name, 
                   dem_candidate, rep_candidate, dva_pct_needed
            FROM flippable 
            WHERE dem_candidate IS NOT NULL 
            AND rep_candidate IS NOT NULL
            ORDER BY dva_pct_needed ASC
            LIMIT 5
        """
        
        result = conn.execute(text(sample_query))
        for row in result:
            print(f"  {row[0]} P{row[1]}: {row[2]}")
            print(f"    DEM: {row[3]} vs REP: {row[4]} (DVA needed: {row[5]:.1f}%)")

if __name__ == "__main__":
    add_candidate_columns()
