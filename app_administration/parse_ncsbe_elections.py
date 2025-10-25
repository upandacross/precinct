#!/usr/bin/env python3
"""
Parse NC BOE Upcoming Elections page to extract election dates and filing periods.

This supplements the hardcoded filing periods in update_candidate_data.py with
real-time data from the NCSBE website.
"""

import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
from pathlib import Path

# Get the project root (parent of app_administration)
PROJECT_ROOT = Path(__file__).parent.parent

def parse_upcoming_elections():
    """
    Fetch and parse the NC BOE upcoming elections page.
    
    Returns:
        dict: Election information including dates and filing periods
    """
    url = "https://www.ncsbe.gov/voting/upcoming-election"
    
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract all text content
        text = soup.get_text()
        
        elections = {
            'municipal_2025': {},
            'state_federal_2026': {},
            'parsed_date': datetime.now().isoformat()
        }
        
        # Parse 2025 Municipal Elections
        # Look for election dates
        municipal_dates = re.findall(r'(Tuesday|Monday|Wednesday|Thursday|Friday), (Sept?\.|Oct\.|Nov\.) (\d+)', text)
        
        if municipal_dates:
            elections['municipal_2025']['election_dates'] = []
            for day_name, month, day_num in municipal_dates:
                elections['municipal_2025']['election_dates'].append({
                    'date': f"{month} {day_num}, 2025",
                    'day': day_name,
                    'description': 'Municipal Election'
                })
        
        # Parse voter deadlines (gives us hints about election timeline)
        # Registration deadline is 25 days before election
        reg_deadline = re.search(r'([A-Z][a-z]+) (\d+).*?Voter registration deadline', text)
        if reg_deadline:
            elections['municipal_2025']['registration_deadline'] = f"{reg_deadline.group(1)} {reg_deadline.group(2)}, 2025"
        
        # Early voting period
        early_voting = re.search(r'([A-Z][a-z]+) (\d+).*?([A-Z][a-z]+) (\d+).*?In-person early voting', text)
        if early_voting:
            elections['municipal_2025']['early_voting'] = {
                'start': f"{early_voting.group(1)} {early_voting.group(2)}, 2025",
                'end': f"{early_voting.group(3)} {early_voting.group(4)}, 2025"
            }
        
        # Extract specific municipalities mentioned
        forsyth_mention = re.search(r'Forsyth County:\s*([^\n]+)', text)
        if forsyth_mention:
            municipalities = forsyth_mention.group(1).split(',')
            elections['municipal_2025']['forsyth_municipalities'] = [m.strip() for m in municipalities]
        
        return elections
        
    except Exception as e:
        print(f"Error parsing upcoming elections: {e}")
        return None

def estimate_filing_period(election_date_str):
    """
    Estimate filing period based on election date.
    
    NC typically has filing periods:
    - Municipal: ~4-5 months before election (June-July for November)
    - State/Federal: ~9-11 months before (Dec-Feb for November)
    """
    try:
        # Parse election date
        election_date = datetime.strptime(election_date_str.replace('Sept.', 'Sep').replace('Oct.', 'Oct').replace('Nov.', 'Nov'), '%b %d, %Y')
        
        # Municipal elections: filing typically June-July for November election
        filing_start = election_date - timedelta(days=135)  # ~4.5 months before
        filing_end = election_date - timedelta(days=120)    # ~4 months before
        
        return {
            'estimated_filing_start': filing_start.strftime('%B %d, %Y'),
            'estimated_filing_end': filing_end.strftime('%B %d, %Y'),
            'election_date': election_date.strftime('%B %d, %Y')
        }
    except:
        return None

def main():
    """Main execution."""
    print("="*80)
    print("NC Board of Elections - Upcoming Elections Parser")
    print("="*80 + "\n")
    
    elections = parse_upcoming_elections()
    
    if not elections:
        print("✗ Failed to parse elections data")
        return
    
    print("✓ Successfully parsed upcoming elections\n")
    
    # Display Municipal 2025 info
    if elections.get('municipal_2025'):
        print("2025 MUNICIPAL ELECTIONS")
        print("-" * 80)
        
        muni = elections['municipal_2025']
        
        if muni.get('election_dates'):
            print("\nElection Dates:")
            for date_info in muni['election_dates']:
                print(f"  • {date_info['date']} ({date_info['day']})")
                
                # Estimate filing period
                filing = estimate_filing_period(date_info['date'])
                if filing:
                    print(f"    Estimated filing: {filing['estimated_filing_start']} - {filing['estimated_filing_end']}")
        
        if muni.get('registration_deadline'):
            print(f"\nRegistration Deadline: {muni['registration_deadline']}")
        
        if muni.get('early_voting'):
            print(f"\nEarly Voting: {muni['early_voting']['start']} - {muni['early_voting']['end']}")
        
        if muni.get('forsyth_municipalities'):
            print(f"\nForsyth County Municipalities:")
            for city in muni['forsyth_municipalities']:
                print(f"  • {city}")
    
    # Save to JSON for reference
    output_file = PROJECT_ROOT / 'doc' / 'upcoming_elections.json'
    output_file.parent.mkdir(exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(elections, f, indent=2)
    
    print(f"\n✓ Data saved to {output_file}")
    print("\n" + "="*80)
    print("NEXT STEPS:")
    print("  1. Verify filing periods on NCSBE website")
    print("  2. Update update_candidate_data.py if needed")
    print("  3. Set up cron job for daily updates during filing period")
    print("="*80)

if __name__ == "__main__":
    main()
