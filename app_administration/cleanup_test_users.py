#!/usr/bin/env python3
"""
Script to clean up (delete) all test users from the database.
Use with caution!
"""

import os
import sys

# Add the parent directory to Python path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User
from main import create_app

def main():
    """Delete all test users."""
    print("🗑️  TEST USER CLEANUP SCRIPT")
    print("=" * 40)
    
    app = create_app()
    
    with app.app_context():
        try:
            # Get all test users
            test_users = User.query.filter(User.username.like('test%')).all()
            
            if not test_users:
                print("No test users found to delete.")
                return
            
            print(f"Found {len(test_users)} test users to delete.")
            
            # Ask for confirmation
            response = input("Are you sure you want to delete all test users? (yes/no): ")
            
            if response.lower() != 'yes':
                print("Cleanup cancelled.")
                return
            
            # Delete all test users
            for user in test_users:
                db.session.delete(user)
            
            db.session.commit()
            print(f"✅ Successfully deleted {len(test_users)} test users.")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error during cleanup: {e}")

if __name__ == "__main__":
    main()