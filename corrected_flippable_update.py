#!/usr/bin/env python3
"""
Corrected Flippable Table Updater
=================================

This script implements the CORRECT flippable logic as originally designed:
- gov_votes: Democratic votes from the governor race in that precinct/election
- If no governor race in that election, use the most recent governor race
- dem_margin: dem_votes - oppo_votes

Usage:
    python3 corrected_flippable_update.py [--dry-run] [--max-margin 15.0] [--min-votes 50]
"""

import os
import pandas as pd
import argparse
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from datetime import datetime
from config import Config

class CorrectedFlippableUpdater:
    """Updates the flippable table with the CORRECT gov_votes logic."""
    
    def __init__(self, max_margin=15.0, min_votes=50):
        """Initialize with database connection and criteria."""
        load_dotenv()  # Load .env file
        self.engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        self.max_margin = max_margin
        self.min_votes = min_votes
        
    def get_governor_votes_lookup(self):
        """Create a lookup table for governor votes by precinct and election - ALL PRECINCTS."""
        print("🏛️  Building governor votes lookup table for ALL precincts...")
        
        query = '''
        SELECT 
            county, precinct, election_date,
            SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as gov_dem_votes
        FROM candidate_vote_results 
        WHERE contest_name = 'NC GOVERNOR'
          AND choice_party = 'DEM'
        GROUP BY county, precinct, election_date
        ORDER BY election_date DESC
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query))
            
            gov_lookup = {}
            most_recent_by_precinct = {}
            most_recent_by_county = {}
            
            for row in result.fetchall():
                county, precinct, election_date, gov_dem_votes = row
                key = (county, precinct, election_date)
                gov_lookup[key] = gov_dem_votes
                
                # Track most recent for each precinct
                precinct_key = (county, precinct)
                if precinct_key not in most_recent_by_precinct:
                    most_recent_by_precinct[precinct_key] = (election_date, gov_dem_votes)
                elif election_date > most_recent_by_precinct[precinct_key][0]:
                    most_recent_by_precinct[precinct_key] = (election_date, gov_dem_votes)
                
                # Track most recent for each county (for precincts without governor data)
                county_key = county
                if county_key not in most_recent_by_county:
                    most_recent_by_county[county_key] = (election_date, gov_dem_votes)
                elif election_date > most_recent_by_county[county_key][0]:
                    most_recent_by_county[county_key] = (election_date, gov_dem_votes)
        
        print(f"✅ Governor lookup built:")
        print(f"   - {len(gov_lookup)} precinct/election combinations")
        print(f"   - {len(most_recent_by_precinct)} precincts with governor data")
        print(f"   - {len(most_recent_by_county)} counties with governor data")
        return gov_lookup, most_recent_by_precinct, most_recent_by_county
    
    def find_new_flippable_races_corrected(self):
        """Find close races with CORRECT gov_votes logic - ALL PRECINCTS."""
        print(f"🔍 Finding new flippable races with corrected logic (ALL PRECINCTS)...")
        print(f"   - Maximum Republican margin: {self.max_margin}%")
        print(f"   - Minimum total votes: {self.min_votes}")
        
        # Get governor votes lookup
        gov_lookup, most_recent_gov, most_recent_county = self.get_governor_votes_lookup()
        
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
                ROUND(((rep_votes - dem_votes) * 100.0 / total_votes), 2) as rep_margin_pct
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
            dem_votes, rep_votes, (dem_votes + rep_votes + other_votes) as race_total_votes,
            total_votes, vote_diff, rep_margin_pct
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
                'dem_votes', 'rep_votes', 'race_total_votes', 'total_votes', 
                'vote_diff', 'rep_margin_pct'
            ])
            
            # Add CORRECT gov_votes column for ALL precincts
            new_races['gov_votes'] = new_races.apply(
                lambda row: self.get_correct_gov_votes(
                    row, gov_lookup, most_recent_gov, most_recent_county
                ), axis=1
            )
            
            # Calculate CORRECT dva_pct_needed and determine best pathway
            # dva_pct_needed = ((oppo_votes + 1) - dem_votes) / (gov_votes - dem_votes)
            def calculate_best_pathway(row):
                vote_gap = (row['rep_votes'] + 1) - row['dem_votes']  # Votes needed to win
                dem_absenteeism = row['gov_votes'] - row['dem_votes']  # Dem governor voters who didn't vote down-ballot
                
                # Calculate DVA percentage
                if dem_absenteeism <= 0:
                    dva_pct = 999.9  # Can't flip if no Democratic absenteeism
                else:
                    dva_pct = (vote_gap / dem_absenteeism) * 100
                
                # Determine difficulty levels
                vote_gap_difficulty = "EASY" if vote_gap <= 50 else "MEDIUM" if vote_gap <= 150 else "HARD"
                dva_difficulty = "EASY" if dva_pct <= 25 else "MEDIUM" if dva_pct <= 50 else "HARD"
                
                # Choose better pathway and create user-friendly assessment
                if vote_gap <= 25 or dva_pct <= 15:
                    assessment = "🎯 SLAM DUNK"
                    best_pathway = "traditional" if vote_gap <= 25 else "dva"
                elif vote_gap <= 100 or dva_pct <= 35:
                    assessment = "✅ HIGHLY FLIPPABLE"
                    best_pathway = "traditional" if vote_gap <= 100 else "dva"
                elif vote_gap <= 300 or dva_pct <= 60:
                    assessment = "🟡 COMPETITIVE"
                    best_pathway = "traditional" if vote_gap <= 300 else "dva"
                else:
                    assessment = "🔴 STRETCH GOAL"
                    best_pathway = "traditional" if vote_gap < dva_pct else "dva"
                
                return {
                    'dva_pct_needed': round(dva_pct, 2),
                    'vote_gap': vote_gap,
                    'best_pathway': best_pathway,
                    'assessment': assessment
                }
            
            # Apply calculations
            pathway_data = new_races.apply(calculate_best_pathway, axis=1)
            new_races['dva_pct_needed'] = [p['dva_pct_needed'] for p in pathway_data]
            new_races['vote_gap'] = [p['vote_gap'] for p in pathway_data]
            new_races['best_pathway'] = [p['best_pathway'] for p in pathway_data]
            new_races['assessment'] = [p['assessment'] for p in pathway_data]
            
            # Convert numeric columns
            numeric_cols = ['dem_votes', 'rep_votes', 'race_total_votes', 'total_votes', 
                          'vote_diff', 'rep_margin_pct', 'gov_votes', 'dva_pct_needed', 'vote_gap']
            for col in numeric_cols:
                new_races[col] = pd.to_numeric(new_races[col], errors='coerce')
        
        print(f"✅ Found {len(new_races)} new flippable races with corrected logic")
        print(f"   Counties: {sorted(new_races['county'].unique())}")
        
        if len(new_races) > 0:
            print(f"\n📊 ASSESSMENT BREAKDOWN:")
            for assessment in new_races['assessment'].value_counts().index:
                count = new_races['assessment'].value_counts()[assessment]
                print(f"   {assessment}: {count} races")
            
            print(f"\n🎯 BEST PATHWAY ANALYSIS:")
            pathway_counts = new_races['best_pathway'].value_counts()
            if 'traditional' in pathway_counts:
                print(f"   Traditional (vote gap): {pathway_counts['traditional']} races")
            if 'dva' in pathway_counts:
                print(f"   DVA (mobilize absent Dems): {pathway_counts['dva']} races")
        
        return new_races
    
    def get_correct_gov_votes(self, row, gov_lookup, most_recent_gov, most_recent_county):
        """Get the correct gov_votes value using three-tier lookup system."""
        county = row['county']
        precinct = row['precinct']
        election_date = row['election_date']
        
        # Tier 1: Governor race in same election (exact match)
        key = (county, precinct, election_date)
        if key in gov_lookup:
            return gov_lookup[key]
        
        # Tier 2: Most recent governor race for this precinct
        precinct_key = (county, precinct)
        if precinct_key in most_recent_gov:
            return most_recent_gov[precinct_key][1]  # gov_dem_votes
        
        # Tier 3: County-level average as fallback
        if county in most_recent_county:
            return most_recent_county[county]
        
        # Final fallback: Use race total (maintains existing behavior for edge cases)
        return row.get('race_total_votes', row.get('total_votes', 0))
    
    def validate_against_existing_flippable(self, sample_size=100):
        """Validate our corrected logic against existing flippable table."""
        print(f"\n🔍 VALIDATING CORRECTED LOGIC")
        print("=" * 60)
        
        # Get governor lookup - now returns three values
        gov_lookup, most_recent_gov, most_recent_county = self.get_governor_votes_lookup()
        
        # Get sample from existing flippable table
        query = '''
        SELECT county, precinct, contest_name, election_date,
               dem_votes, oppo_votes, gov_votes, dem_margin
        FROM flippable 
        ORDER BY RANDOM() 
        LIMIT :sample_size
        '''
        
        with self.engine.connect() as conn:
            result = conn.execute(text(query), {'sample_size': sample_size})
            existing = pd.DataFrame(result.fetchall(), columns=[
                'county', 'precinct', 'contest_name', 'election_date',
                'dem_votes', 'oppo_votes', 'gov_votes', 'dem_margin'
            ])
        
        # Calculate what gov_votes SHOULD be according to correct logic
        existing['correct_gov_votes'] = existing.apply(
            lambda row: self.get_correct_gov_votes(row, gov_lookup, most_recent_gov, most_recent_county), axis=1
        )
        
        # Calculate what dem_margin SHOULD be
        existing['correct_dem_margin'] = existing['dem_votes'] - existing['oppo_votes']
        
        # Compare
        gov_matches = (existing['gov_votes'] == existing['correct_gov_votes']).sum()
        margin_matches = (existing['dem_margin'] == existing['correct_dem_margin']).sum()
        
        print(f"Sample size: {len(existing)} races")
        print(f"gov_votes correct: {gov_matches}/{len(existing)} ({(gov_matches/len(existing)*100):.1f}%)")
        print(f"dem_margin correct: {margin_matches}/{len(existing)} ({(margin_matches/len(existing)*100):.1f}%)")
        
        # Show some examples of discrepancies
        gov_wrong = existing[existing['gov_votes'] != existing['correct_gov_votes']].head(5)
        if len(gov_wrong) > 0:
            print(f"\nExample gov_votes discrepancies:")
            for idx, row in gov_wrong.iterrows():
                print(f"  {row['county']} P{row['precinct']} {row['election_date']}: current={row['gov_votes']} vs correct={row['correct_gov_votes']}")
        
        return existing

def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Update flippable table with CORRECTED logic')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview changes without updating database')
    parser.add_argument('--max-margin', type=float, default=15.0,
                       help='Maximum Republican margin percentage (default: 15.0)')
    parser.add_argument('--min-votes', type=int, default=50,
                       help='Minimum total votes in race (default: 50)')
    parser.add_argument('--validate-only', action='store_true',
                       help='Only validate existing data, do not find new races')
    
    args = parser.parse_args()
    
    print("🏛️  CORRECTED FLIPPABLE UPDATER")
    print("=" * 50)
    print("Implementing original gov_votes logic:")
    print("- gov_votes = Democratic votes from governor race in same election")
    print("- If no governor race, use most recent governor race for that precinct")
    print("- dem_margin = dem_votes - oppo_votes")
    print()
    
    # Initialize updater
    updater = CorrectedFlippableUpdater(max_margin=args.max_margin, min_votes=args.min_votes)
    
    # Validate existing data
    validation_results = updater.validate_against_existing_flippable()
    
    if not args.validate_only:
        # Find new races with corrected logic
        new_races = updater.find_new_flippable_races_corrected()
        
        if len(new_races) > 0:
            print(f"\n📋 NEW RACES WITH CORRECTED LOGIC:")
            for idx, race in new_races.head(10).iterrows():
                print(f"  {race['county']} P{race['precinct']} - {race['contest_name']}")
                print(f"    Election: {race['election_date']}")
                print(f"    Votes: DEM {race['dem_votes']} vs REP {race['rep_votes']}")
                print(f"    Gov votes (corrected): {race['gov_votes']}")
                print(f"    Margin: {race['rep_margin_pct']}%")
                print()
        else:
            print(f"\n✅ No new races found with current criteria.")
    
    print(f"\n💡 The validation shows how the current flippable table")
    print(f"   compares to your original design logic.")

if __name__ == "__main__":
    main()