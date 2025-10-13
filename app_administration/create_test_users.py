#!/usr/bin/env python3
"""
Script to create test users for every precinct in FORSYTH county.
Creates between 10-25 active users and 3-5 inactive users per precinct.
All users are regular users (no admin or county privileges).
Usernames: test001, test002, etc.
Passwords: test001!123, test002!123, etc.
"""

import os
import sys
import random
from datetime import datetime, timedelta

# Add the parent directory to Python path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User, Map
from main import create_app

def get_forsyth_precincts():
    """Get all unique precincts in FORSYTH county from the maps table."""
    precincts = db.session.query(Map.precinct).filter_by(
        state='NC', 
        county='FORSYTH'
    ).distinct().all()
    
    return [precinct[0] for precinct in precincts]

def get_next_test_user_number():
    """Get the next sequential number for test users."""
    # Find the highest existing test user number
    existing_users = User.query.filter(User.username.like('test%')).all()
    
    max_num = 0
    for user in existing_users:
        try:
            # Extract number from username like 'test001'
            if user.username.startswith('test'):
                num_str = user.username[4:]  # Remove 'test' prefix
                if num_str.isdigit():
                    max_num = max(max_num, int(num_str))
        except:
            continue
    
    return max_num + 1

def create_test_users_for_precinct(precinct, start_number):
    """Create test users for a specific precinct."""
    print(f"Creating test users for precinct {precinct}...")
    
    # Random number of active and inactive users
    num_active = random.randint(10, 25)
    num_inactive = random.randint(3, 5)
    total_users = num_active + num_inactive
    
    users_created = []
    current_number = start_number
    
    for i in range(total_users):
        # Create username and password
        username = f"test{current_number:03d}"
        password = f"{username}!123"
        email = f"{username}@example.com"
        
        # Determine if user should be active or inactive
        is_active = i < num_active  # First users are active, rest inactive
        
        # All test users are regular users (no admin or county privileges)
        is_admin = False
        is_county = False
        
        # Create user
        try:
            user = User(
                username=username,
                email=email,
                password=password,
                is_admin=is_admin,
                is_county=is_county,
                state='NC',
                county='FORSYTH',
                precinct=precinct,
                phone=f"336-555-{random.randint(1000, 9999)}",
                role=f"Volunteer {precinct}",
                notes=f"Test user for precinct {precinct}"
            )
            user.is_active = is_active
            
            # Set random last_login for active users
            if is_active:
                days_ago = random.randint(1, 30)
                user.last_login = datetime.utcnow() - timedelta(days=days_ago)
            
            db.session.add(user)
            users_created.append({
                'username': username,
                'password': password,
                'email': email,
                'active': is_active,
                'admin': is_admin,
                'county': is_county
            })
            
            current_number += 1
            
        except Exception as e:
            print(f"Error creating user {username}: {e}")
            current_number += 1
            continue
    
    # Commit users for this precinct
    try:
        db.session.commit()
        print(f"✅ Created {len(users_created)} users for precinct {precinct}")
        print(f"   - Active: {sum(1 for u in users_created if u['active'])}")
        print(f"   - Inactive: {sum(1 for u in users_created if not u['active'])}")
        print(f"   - All users: Regular users (no admin/county privileges)")
        
        return users_created, current_number
        
    except Exception as e:
        db.session.rollback()
        print(f"❌ Error committing users for precinct {precinct}: {e}")
        return [], current_number

def main():
    """Main function to create test users for all FORSYTH precincts."""
    print("🚀 Starting test user creation for FORSYTH county precincts...")
    print("=" * 60)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Get all FORSYTH precincts
            precincts = get_forsyth_precincts()
            print(f"Found {len(precincts)} precincts in FORSYTH county:")
            for precinct in sorted(precincts):
                print(f"  - {precinct}")
            print()
            
            if not precincts:
                print("❌ No precincts found in FORSYTH county. Make sure the maps table is populated.")
                return
            
            # Get starting user number
            start_number = get_next_test_user_number()
            print(f"Starting with test user number: {start_number:03d}")
            print()
            
            # Create users for each precinct
            all_users = []
            current_number = start_number
            
            for precinct in sorted(precincts):
                users, current_number = create_test_users_for_precinct(precinct, current_number)
                all_users.extend(users)
                print()
            
            # Summary
            print("=" * 60)
            print("📊 SUMMARY:")
            print(f"✅ Total users created: {len(all_users)}")
            print(f"✅ Total active users: {sum(1 for u in all_users if u['active'])}")
            print(f"✅ Total inactive users: {sum(1 for u in all_users if not u['active'])}")
            print(f"✅ All users: Regular users (no admin/county privileges)")
            print(f"✅ Precincts populated: {len(precincts)}")
            print()
            
            print("📝 TEST USER CREDENTIALS SAMPLE:")
            print("Username | Password   | Active | Role")
            print("-" * 35)
            for user in all_users[:10]:  # Show first 10 users
                role = "User"  # All test users are regular users
                active = "Yes" if user['active'] else "No"
                print(f"{user['username']} | {user['password']} | {active:6s} | {role}")
            
            if len(all_users) > 10:
                print(f"... and {len(all_users) - 10} more users")
            
            print()
            print("🎉 Test user creation completed successfully!")
            print("💡 All test users are regular users - you can test analytics with precinct-level access.")
            
        except Exception as e:
            print(f"❌ Error during test user creation: {e}")
            db.session.rollback()

if __name__ == "__main__":
    main()