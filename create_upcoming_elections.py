#!/usr/bin/env python3
"""
Create and populate upcoming_elections table with North Carolina election dates.
Focuses on Forsyth County and statewide elections through November 2026.
"""

from datetime import date
from models import db, UpcomingElection
from main import create_app

def create_upcoming_elections_table():
    """Create the upcoming_elections table and populate with election data."""
    
    app = create_app()
    """Create the upcoming_elections table and populate with election data."""
    
    with app.app_context():
        # Create the table
        print("Creating upcoming_elections table...")
        db.create_all()
        
        # Clear existing data (optional - comment out to preserve existing records)
        print("Clearing existing election records...")
        UpcomingElection.query.delete()
        
        # Define upcoming elections based on NC State Board of Elections calendar
        elections = [
            # November 2025 Municipal Elections (Statewide)
            UpcomingElection(
                election_name="November 2025 Municipal Elections",
                election_type="municipal",
                election_date=date(2025, 11, 4),
                early_voting_start=date(2025, 10, 16),
                early_voting_end=date(2025, 11, 1),
                absentee_request_deadline=date(2025, 10, 28),
                absentee_return_deadline=date(2025, 11, 4),
                voter_registration_deadline=date(2025, 10, 10),
                state='NC',
                description="Municipal elections held in participating NC municipalities",
                contests="Mayor, City Council, Board of Aldermen (varies by municipality)"
            ),
            
            # Forsyth County - Winston-Salem Municipal Election
            UpcomingElection(
                election_name="Winston-Salem Municipal Election",
                election_type="municipal",
                election_date=date(2025, 11, 4),
                early_voting_start=date(2025, 10, 16),
                early_voting_end=date(2025, 11, 1),
                absentee_request_deadline=date(2025, 10, 28),
                absentee_return_deadline=date(2025, 11, 4),
                voter_registration_deadline=date(2025, 10, 10),
                county='FORSYTH',
                municipality='Winston-Salem',
                state='NC',
                description="Winston-Salem city elections for Mayor and City Council",
                contests="Mayor, City Council At-Large, Ward Representatives"
            ),
            
            # Forsyth County - Kernersville Municipal Election
            UpcomingElection(
                election_name="Kernersville Municipal Election",
                election_type="municipal",
                election_date=date(2025, 11, 4),
                early_voting_start=date(2025, 10, 16),
                early_voting_end=date(2025, 11, 1),
                absentee_request_deadline=date(2025, 10, 28),
                absentee_return_deadline=date(2025, 11, 4),
                voter_registration_deadline=date(2025, 10, 10),
                county='FORSYTH',
                municipality='Kernersville',
                state='NC',
                description="Kernersville town elections",
                contests="Mayor, Board of Aldermen"
            ),
            
            # Forsyth County - Clemmons Municipal Election (if applicable)
            UpcomingElection(
                election_name="Clemmons Municipal Election",
                election_type="municipal",
                election_date=date(2025, 11, 4),
                early_voting_start=date(2025, 10, 16),
                early_voting_end=date(2025, 11, 1),
                absentee_request_deadline=date(2025, 10, 28),
                absentee_return_deadline=date(2025, 11, 4),
                voter_registration_deadline=date(2025, 10, 10),
                county='FORSYTH',
                municipality='Clemmons',
                state='NC',
                description="Clemmons village elections",
                contests="Mayor, Village Council"
            ),
            
            # 2026 Primary Election (Statewide)
            UpcomingElection(
                election_name="North Carolina Primary Election",
                election_type="primary",
                election_date=date(2026, 3, 3),
                early_voting_start=date(2026, 2, 13),
                early_voting_end=date(2026, 2, 28),
                absentee_request_deadline=date(2026, 2, 24),
                absentee_return_deadline=date(2026, 3, 3),
                voter_registration_deadline=date(2026, 2, 6),
                state='NC',
                description="Statewide primary elections for federal, state, and local offices",
                contests="U.S. Senate, U.S. House, NC Senate, NC House, County Offices"
            ),
            
            # 2026 Primary Election - Forsyth County
            UpcomingElection(
                election_name="Forsyth County Primary Election",
                election_type="primary",
                election_date=date(2026, 3, 3),
                early_voting_start=date(2026, 2, 13),
                early_voting_end=date(2026, 2, 28),
                absentee_request_deadline=date(2026, 2, 24),
                absentee_return_deadline=date(2026, 3, 3),
                voter_registration_deadline=date(2026, 2, 6),
                county='FORSYTH',
                state='NC',
                description="Primary elections in Forsyth County",
                contests="U.S. House District 6, NC Senate District 31/32, NC House District 71/72/74/75, County Commissioner, Sheriff, Clerk of Court"
            ),
            
            # 2026 General Election (Statewide)
            UpcomingElection(
                election_name="North Carolina General Election",
                election_type="general",
                election_date=date(2026, 11, 3),
                early_voting_start=date(2026, 10, 15),
                early_voting_end=date(2026, 10, 31),
                absentee_request_deadline=date(2026, 10, 27),
                absentee_return_deadline=date(2026, 11, 3),
                voter_registration_deadline=date(2026, 10, 9),
                state='NC',
                description="Statewide general elections for federal, state, and local offices",
                contests="U.S. Senate, U.S. House, NC Senate, NC House, County Offices, Judicial Races"
            ),
            
            # 2026 General Election - Forsyth County
            UpcomingElection(
                election_name="Forsyth County General Election",
                election_type="general",
                election_date=date(2026, 11, 3),
                early_voting_start=date(2026, 10, 15),
                early_voting_end=date(2026, 10, 31),
                absentee_request_deadline=date(2026, 10, 27),
                absentee_return_deadline=date(2026, 11, 3),
                voter_registration_deadline=date(2026, 10, 9),
                county='FORSYTH',
                state='NC',
                description="General elections in Forsyth County",
                contests="U.S. House District 6, NC Senate District 31/32, NC House District 71/72/74/75, County Commissioner, Sheriff, Clerk of Court, School Board, Soil & Water Conservation"
            ),
        ]
        
        # Add all elections to database
        print(f"\nAdding {len(elections)} elections to database...")
        for election in elections:
            db.session.add(election)
            print(f"  ✓ {election.election_name} - {election.election_date}")
        
        # Commit changes
        db.session.commit()
        print(f"\n✅ Successfully created upcoming_elections table and added {len(elections)} elections!")
        
        # Display upcoming elections
        print("\n" + "="*80)
        print("UPCOMING ELECTIONS IN FORSYTH COUNTY")
        print("="*80)
        
        forsyth_elections = UpcomingElection.get_upcoming_elections(county='FORSYTH')
        for election in forsyth_elections:
            days_left = election.days_until_election()
            early_voting_status = "✓ ACTIVE NOW" if election.is_early_voting_active() else ""
            
            print(f"\n📅 {election.election_name}")
            print(f"   Type: {election.election_type.upper()}")
            print(f"   Election Day: {election.election_date} ({days_left} days)")
            print(f"   Early Voting: {election.early_voting_start} to {election.early_voting_end} {early_voting_status}")
            if election.municipality:
                print(f"   Municipality: {election.municipality}")
            if election.contests:
                print(f"   Contests: {election.contests}")
        
        print("\n" + "="*80)
        print("ALL UPCOMING NC ELECTIONS (STATEWIDE)")
        print("="*80)
        
        all_elections = UpcomingElection.get_upcoming_elections(limit=20)
        for election in all_elections:
            days_left = election.days_until_election()
            location = election.municipality or election.county or "Statewide"
            print(f"  • {election.election_date} | {election.election_name} ({location}) - {days_left} days")
        
        print("\n")

if __name__ == "__main__":
    create_upcoming_elections_table()
