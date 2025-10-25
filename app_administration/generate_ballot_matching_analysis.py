#!/usr/bin/env python3
"""
Automated Ballot Matching Analysis Generator

Monitors for new candidate data and automatically generates ballot matching
analysis reports for Forsyth County races.

Triggers:
- Municipal races: When 2025, 2027, 2029... data is updated
- State/Federal races: When 2026, 2028, 2030... data is updated
"""

import os
import sys
from pathlib import Path
from datetime import datetime, date
import pandas as pd
from sqlalchemy import create_engine, text

# Add parent directory to path to import config and models
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import Config
from models import User

# Paths
PROJECT_ROOT = Path(__file__).parent.parent
DOC_DIR = PROJECT_ROOT / "doc"
REPORTS_DIR = PROJECT_ROOT / "reports"
REPORTS_DIR.mkdir(exist_ok=True)

def get_county_from_user():
    """Get county from is_county user in database."""
    try:
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        with engine.connect() as conn:
            query = text("""
                SELECT county 
                FROM "user" 
                WHERE is_county = true 
                AND county IS NOT NULL 
                LIMIT 1
            """)
            result = conn.execute(query).fetchone()
            if result and result[0]:
                return result[0]
    except Exception as e:
        print(f"Warning: Could not get county from database: {e}")
    
    # Fallback to FORSYTH if no is_county user found
    return 'FORSYTH'

def is_municipal_year(year):
    """Check if year is a municipal election year (odd years)."""
    return year % 2 == 1

def is_state_federal_year(year):
    """Check if year is a state/federal election year (even years)."""
    return year % 2 == 0

def generate_municipal_analysis(year, county=None):
    """Generate ballot matching analysis for municipal races."""
    
    if county is None:
        county = get_county_from_user()
    
    csv_path = DOC_DIR / f"Candidate_Listing_{year}.csv"
    if not csv_path.exists():
        print(f"✗ No candidate data found for {year}")
        return None
    
    print(f"\n{'='*80}")
    print(f"GENERATING MUNICIPAL BALLOT MATCHING ANALYSIS - {county} COUNTY {year}")
    print(f"{'='*80}\n")
    
    # Read candidate data
    df_csv = pd.read_csv(csv_path, encoding='latin-1')
    county_data = df_csv[df_csv['county_name'] == county]
    
    if len(county_data) == 0:
        print(f"✗ No {county} County data found in {year} file")
        return None
    
    print(f"Found {len(county_data)} candidates across {county_data['contest_name'].nunique()} contests")
    
    # Connect to database
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    # Calculate flippability for each contest
    flippability_results = []
    
    for contest in sorted(county_data['contest_name'].unique()):
        contest_candidates = county_data[county_data['contest_name'] == contest]
        
        # Count party affiliations
        dem_count = len(contest_candidates[contest_candidates['party_candidate'] == 'DEM'])
        rep_count = len(contest_candidates[contest_candidates['party_candidate'] == 'REP'])
        una_count = len(contest_candidates) - dem_count - rep_count
        
        with engine.connect() as conn:
            # Get turnout data
            query = text("""
                SELECT COUNT(DISTINCT precinct) as precincts,
                       SUM(total_votes) as total_votes
                FROM candidate_vote_results
                WHERE county = :county
                AND contest_name = :contest
            """)
            turnout = conn.execute(query, {'county': county, 'contest': contest}).fetchone()
            
            # Get partisan crossover performance
            query = text("""
                SELECT AVG(f.dem_votes::float / NULLIF(f.dem_votes + f.oppo_votes, 0)) * 100 as avg_dem_pct,
                       STDDEV(f.dem_votes::float / NULLIF(f.dem_votes + f.oppo_votes, 0)) * 100 as stddev_dem_pct,
                       COUNT(DISTINCT f.precinct) as partisan_precincts
                FROM flippable f
                WHERE f.county = :county
                AND f.precinct IN (
                    SELECT DISTINCT precinct 
                    FROM candidate_vote_results 
                    WHERE county = :county AND contest_name = :contest
                )
                AND f.dem_votes IS NOT NULL 
                AND f.oppo_votes IS NOT NULL
            """)
            partisan = conn.execute(query, {'county': county, 'contest': contest}).fetchone()
        
        # Calculate flippability
        if partisan and partisan[0] is not None:
            avg_dem_pct = partisan[0]
            dva_needed = max(0, 50.0 - avg_dem_pct)
            
            if avg_dem_pct >= 48:
                rating = "TOSS-UP"
            elif avg_dem_pct >= 45:
                rating = "LEAN REP"
            elif avg_dem_pct >= 40:
                rating = "LIKELY REP"
            else:
                rating = "SAFE REP"
            
            if dem_count == 0:
                rating = "NO DEM CANDIDATE"
        else:
            avg_dem_pct = None
            dva_needed = None
            rating = "INSUFFICIENT DATA"
        
        flippability_results.append({
            'contest': contest,
            'dem_count': dem_count,
            'rep_count': rep_count,
            'una_count': una_count,
            'turnout': turnout[1] if turnout and turnout[1] else 0,
            'precincts': turnout[0] if turnout and turnout[0] else 0,
            'avg_dem_pct': avg_dem_pct,
            'dva_needed': dva_needed,
            'rating': rating
        })
    
    # Generate markdown report
    report_date = datetime.now().strftime('%Y%m%d')
    report_path = REPORTS_DIR / f"{county}_Municipal_Analysis_{report_date}.md"
    
    with open(report_path, 'w') as f:
        f.write(f"# {year} {county} County Municipal Elections - Ballot Matching Analysis\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Source:** Candidate_Listing_{year}.csv\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total Candidates:** {len(county_data)}\n")
        f.write(f"- **Contests:** {county_data['contest_name'].nunique()}\n")
        f.write(f"- **Democratic Candidates:** {len(county_data[county_data['party_candidate'] == 'DEM'])}\n")
        f.write(f"- **Republican Candidates:** {len(county_data[county_data['party_candidate'] == 'REP'])}\n\n")
        
        # Flippability summary
        competitive = [x for x in flippability_results if x['rating'] in ['TOSS-UP', 'LEAN REP']]
        if competitive:
            f.write("### Top Opportunities\n\n")
            for item in sorted(competitive, key=lambda x: x['dva_needed'] if x['dva_needed'] else 999):
                if item['avg_dem_pct']:
                    f.write(f"- **{item['contest']}**: {item['avg_dem_pct']:.1f}% Dem baseline, DVA: {item['dva_needed']:.1f}%\n")
        
        f.write("\n---\n\n")
        f.write("## Flippability Analysis\n\n")
        
        for item in sorted(flippability_results, key=lambda x: x['dva_needed'] if x['dva_needed'] else 999):
            f.write(f"### {item['contest']}\n\n")
            f.write(f"- **Candidates:** {item['dem_count']} DEM, {item['rep_count']} REP, {item['una_count']} Other\n")
            f.write(f"- **Historical Turnout:** {item['turnout']:,} votes across {item['precincts']} precincts\n")
            if item['avg_dem_pct']:
                f.write(f"- **Partisan Baseline:** {item['avg_dem_pct']:.1f}% Dem\n")
                f.write(f"- **DVA Needed:** {item['dva_needed']:.1f}%\n")
            f.write(f"- **Rating:** {item['rating']}\n\n")
        
        f.write("\n---\n\n")
        f.write("*Generated by automated ballot matching analysis system*\n")
    
    print(f"\n✓ Report generated: {report_path}")
    return report_path

def generate_state_federal_analysis(year, county=None):
    """Generate ballot matching analysis for state/federal races."""
    
    if county is None:
        county = get_county_from_user()
    
    csv_path = DOC_DIR / f"Candidate_Listing_{year}.csv"
    if not csv_path.exists():
        print(f"✗ No candidate data found for {year}")
        return None
    
    print(f"\n{'='*80}")
    print(f"GENERATING STATE/FEDERAL BALLOT MATCHING ANALYSIS - {county} COUNTY {year}")
    print(f"{'='*80}\n")
    
    # Read candidate data
    df_csv = pd.read_csv(csv_path, encoding='latin-1')
    county_data = df_csv[df_csv['county_name'] == county]
    
    if len(county_data) == 0:
        print(f"✗ No {county} County data found in {year} file")
        return None
    
    # Filter out municipal races
    state_federal = county_data[~county_data['contest_name'].str.contains('CITY|TOWN|VILLAGE', case=False, na=False)]
    
    print(f"Found {len(state_federal)} candidates across {state_federal['contest_name'].nunique()} contests")
    
    # Connect to database
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    # Match candidates with flippable table (TIER 1: Rematch Advantage)
    returning_candidates = []
    
    with engine.connect() as conn:
        query = text("""
            SELECT DISTINCT contest_name, dem_candidate, rep_candidate
            FROM flippable
            WHERE county = :county
            AND (dem_candidate IS NOT NULL OR rep_candidate IS NOT NULL)
        """)
        historical = conn.execute(query, {'county': county}).fetchall()
        
        historical_names = {}
        for row in historical:
            contest = row[0]
            if contest not in historical_names:
                historical_names[contest] = set()
            if row[1]:
                historical_names[contest].add(row[1])
            if row[2]:
                historical_names[contest].add(row[2])
    
    # Match current candidates
    for _, candidate in state_federal.iterrows():
        name = f"{candidate['first_name']} {candidate['last_name']}".strip()
        contest = candidate['contest_name']
        
        if contest in historical_names and name in historical_names[contest]:
            returning_candidates.append({
                'name': candidate['name_on_ballot'],
                'contest': contest,
                'party': candidate['party_candidate']
            })
    
    # Generate markdown report
    report_date = datetime.now().strftime('%Y%m%d')
    report_path = REPORTS_DIR / f"{county}_StateFederal_Analysis_{report_date}.md"
    
    with open(report_path, 'w') as f:
        f.write(f"# {year} {county} County State/Federal Elections - Ballot Matching Analysis\n\n")
        f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"**Source:** Candidate_Listing_{year}.csv\n\n")
        
        f.write("## Executive Summary\n\n")
        f.write(f"- **Total State/Federal Candidates:** {len(state_federal)}\n")
        f.write(f"- **Contests:** {state_federal['contest_name'].nunique()}\n")
        f.write(f"- **Returning Candidates (Tier 1):** {len(returning_candidates)}\n\n")
        
        if returning_candidates:
            f.write("## TIER 1: Rematch Advantage - Returning Candidates\n\n")
            for cand in sorted(returning_candidates, key=lambda x: x['contest']):
                f.write(f"- **{cand['name']}** ({cand['party']}) - {cand['contest']}\n")
            f.write("\n")
        
        f.write("## All Contests\n\n")
        for contest in sorted(state_federal['contest_name'].unique()):
            contest_cands = state_federal[state_federal['contest_name'] == contest]
            f.write(f"### {contest}\n\n")
            for _, cand in contest_cands.iterrows():
                party = cand['party_candidate'] if pd.notna(cand['party_candidate']) else 'UNA'
                f.write(f"- {cand['name_on_ballot']} ({party})\n")
            f.write("\n")
        
        f.write("\n---\n\n")
        f.write("*Generated by automated ballot matching analysis system*\n")
    
    print(f"\n✓ Report generated: {report_path}")
    return report_path

def main():
    """Main execution."""
    print("="*80)
    print("Automated Ballot Matching Analysis")
    print(f"Run date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    
    # Check for year parameter or use current year
    if len(sys.argv) > 1:
        year = int(sys.argv[1])
    else:
        year = date.today().year
    
    print(f"\nAnalyzing year: {year}")
    
    # Determine race type and generate appropriate analysis
    if is_municipal_year(year):
        print(f"✓ {year} is a municipal election year")
        report = generate_municipal_analysis(year)
    elif is_state_federal_year(year):
        print(f"✓ {year} is a state/federal election year")
        report = generate_state_federal_analysis(year)
    else:
        print(f"✗ Invalid year: {year}")
        return
    
    if report:
        print(f"\n{'='*80}")
        print("SUCCESS - Analysis complete!")
        print(f"Report: {report}")
        print("="*80)
    else:
        print("\n✗ Analysis failed")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
