#!/usr/bin/env python3
"""
Quick analysis of governor data coverage
"""

import os
import sys
from sqlalchemy import create_engine, text
import pandas as pd
from dotenv import load_dotenv
from config import Config

def analyze_governor_coverage():
    """Analyze what governor data we have available."""
    
    # Load environment variables and use Config class
    load_dotenv()
    DATABASE_URL = Config.SQLALCHEMY_DATABASE_URI
    print(f"📊 Using database: {DATABASE_URL}")
    
    try:
        engine = create_engine(DATABASE_URL)
        
        print("\n🔍 ANALYZING GOVERNOR DATA COVERAGE")
        print("=" * 50)
        
        with engine.connect() as conn:
            # Check what governor contests we have
            result = conn.execute(text('''
                SELECT DISTINCT contest_name
                FROM candidate_vote_results 
                WHERE UPPER(contest_name) LIKE '%GOVERNOR%'
                ORDER BY contest_name
            '''))
            
            governor_contests = [row[0] for row in result.fetchall()]
            print(f"\n🏛️ Governor Contest Names ({len(governor_contests)} found):")
            for contest in governor_contests:
                print(f"   '{contest}'")
            
            if governor_contests:
                # Get details for each governor contest
                print(f"\n📈 Governor Contest Details:")
                for contest in governor_contests:
                    result = conn.execute(text('''
                        SELECT election_date, 
                               COUNT(DISTINCT precinct) as precincts,
                               COUNT(DISTINCT county) as counties,
                               SUM(total_votes) as total_votes
                        FROM candidate_vote_results 
                        WHERE contest_name = :contest_name
                        GROUP BY election_date
                        ORDER BY election_date DESC
                    '''), {'contest_name': contest})
                    
                    for row in result.fetchall():
                        print(f"   {row[0]}: '{contest}' - {row[1]} precincts, {row[2]} counties, {row[3]} votes")
            
            # Check flippable table summary
            result = conn.execute(text('''
                SELECT COUNT(*) as total_races,
                       COUNT(DISTINCT county) as counties,
                       COUNT(DISTINCT precinct) as precincts,
                       MIN(election_date) as earliest,
                       MAX(election_date) as latest
                FROM flippable
            '''))
            
            row = result.fetchone()
            print(f"\n📊 Current Flippable Table:")
            print(f"   Total races: {row[0]}")
            print(f"   Counties: {row[1]}")
            print(f"   Precincts: {row[2]}")
            print(f"   Date range: {row[3]} to {row[4]}")
            
            # Test our lookup logic with sample data
            print(f"\n🔍 Testing Lookup Logic:")
            result = conn.execute(text('''
                SELECT county, precinct, election_date, contest_name
                FROM flippable 
                LIMIT 5
            '''))
            
            sample_races = result.fetchall()
            for race in sample_races:
                county, precinct, election_date, contest_name = race
                
                # Try to find governor data for this precinct/election
                result = conn.execute(text('''
                    SELECT contest_name, 
                           SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as dem_votes,
                           SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) as rep_votes
                    FROM candidate_vote_results 
                    WHERE county = :county 
                      AND precinct = :precinct 
                      AND election_date = :election_date
                      AND UPPER(contest_name) LIKE '%GOVERNOR%'
                    GROUP BY contest_name
                '''), {
                    'county': county,
                    'precinct': precinct,
                    'election_date': election_date
                })
                
                gov_data = result.fetchall()
                print(f"   {county} P{precinct} {election_date}: {len(gov_data)} governor races")
                for gov_race in gov_data:
                    print(f"     → {gov_race[0]}: D={gov_race[1]}, R={gov_race[2]}")
                
    except Exception as e:
        print(f"❌ Database error: {e}")
        print("This might indicate the database is not running or configured properly.")

if __name__ == "__main__":
    analyze_governor_coverage()