#!/usr/bin/env python3
"""
Script to check existing test users and provide statistics.
"""

import os
import sys

# Add the parent directory to Python path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User
from main import create_app

def main():
    """Check existing test users."""
    print("📊 EXISTING TEST USERS REPORT")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get all test users
            test_users = User.query.filter(User.username.like('test%')).all()
            
            if not test_users:
                print("No test users found.")
                return
            
            print(f"Total test users: {len(test_users)}")
            print()
            
            # Group by precinct
            by_precinct = {}
            for user in test_users:
                precinct = user.precinct or 'Unknown'
                if precinct not in by_precinct:
                    by_precinct[precinct] = []
                by_precinct[precinct].append(user)
            
            # Show statistics by precinct
            for precinct in sorted(by_precinct.keys()):
                users = by_precinct[precinct]
                active = sum(1 for u in users if u.is_active)
                inactive = len(users) - active
                admins = sum(1 for u in users if u.is_admin)
                county = sum(1 for u in users if u.is_county)
                
                print(f"Precinct {precinct}:")
                print(f"  Total: {len(users)} | Active: {active} | Inactive: {inactive}")
                print(f"  Admin: {admins} | County: {county}")
                print()
            
            # Overall statistics
            total_active = sum(1 for u in test_users if u.is_active)
            total_inactive = len(test_users) - total_active
            total_admins = sum(1 for u in test_users if u.is_admin)
            total_county = sum(1 for u in test_users if u.is_county)
            
            print("OVERALL STATISTICS:")
            print(f"Active users: {total_active}")
            print(f"Inactive users: {total_inactive}")
            print(f"Admin users: {total_admins}")
            print(f"County users: {total_county}")
            print(f"Precincts with users: {len(by_precinct)}")
            
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()