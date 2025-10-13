#!/usr/bin/env python3
"""
Script to backup the users table from the NC database.
Creates a timestamped backup file that can be used to restore users later.
"""

import os
import sys
import json
from datetime import datetime

# Add the parent directory to Python path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User
from main import create_app

def backup_users():
    """Backup all users from the database to a JSON file."""
    print("🔄 Starting users table backup...")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Get all users from the database
            users = User.query.all()
            print(f"Found {len(users)} users in the database")
            
            if not users:
                print("⚠️  No users found in the database")
                return None
            
            # Convert users to dictionary format for JSON serialization
            users_data = []
            for user in users:
                user_dict = {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'password': user.password,  # This is the original password, not hashed
                    'password_hash': user.password_hash,
                    'is_admin': user.is_admin,
                    'is_county': user.is_county,
                    'is_active': user.is_active,
                    'created_at': user.created_at.isoformat() if user.created_at else None,
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'state': user.state,
                    'county': user.county,
                    'precinct': user.precinct,
                    'phone': user.phone,
                    'role': user.role,
                    'notes': user.notes
                }
                users_data.append(user_dict)
            
            # Create timestamped backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"users_backup_{timestamp}.json"
            backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), backup_filename)
            
            # Write backup to JSON file
            with open(backup_path, 'w') as f:
                json.dump({
                    'backup_timestamp': timestamp,
                    'backup_datetime': datetime.now().isoformat(),
                    'total_users': len(users_data),
                    'users': users_data
                }, f, indent=2)
            
            print(f"✅ Backup completed successfully!")
            print(f"📁 Backup saved to: {backup_filename}")
            print(f"📊 Users backed up: {len(users_data)}")
            
            # Show breakdown by user type
            admin_count = sum(1 for u in users_data if u['is_admin'])
            county_count = sum(1 for u in users_data if u['is_county'] and not u['is_admin'])
            regular_count = sum(1 for u in users_data if not u['is_admin'] and not u['is_county'])
            active_count = sum(1 for u in users_data if u['is_active'])
            
            print(f"   - Admin users: {admin_count}")
            print(f"   - County users: {county_count}")
            print(f"   - Regular users: {regular_count}")
            print(f"   - Active users: {active_count}")
            print(f"   - Inactive users: {len(users_data) - active_count}")
            
            return backup_filename
            
        except Exception as e:
            print(f"❌ Error during backup: {e}")
            return None

def list_backups():
    """List all available backup files."""
    backup_dir = os.path.dirname(os.path.abspath(__file__))
    backup_files = [f for f in os.listdir(backup_dir) if f.startswith('users_backup_') and f.endswith('.json')]
    
    if not backup_files:
        print("📂 No backup files found")
        return []
    
    print(f"📂 Found {len(backup_files)} backup file(s):")
    backup_files.sort(reverse=True)  # Most recent first
    
    for i, backup_file in enumerate(backup_files, 1):
        # Extract timestamp from filename
        timestamp_str = backup_file.replace('users_backup_', '').replace('.json', '')
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp_str
        
        # Get file size
        file_path = os.path.join(backup_dir, backup_file)
        file_size = os.path.getsize(file_path)
        size_mb = file_size / (1024 * 1024)
        
        print(f"   {i}. {backup_file}")
        print(f"      Created: {formatted_time}")
        print(f"      Size: {size_mb:.2f} MB")
        
        # Try to read user count from backup file
        try:
            with open(file_path, 'r') as f:
                backup_data = json.load(f)
                user_count = backup_data.get('total_users', 'Unknown')
                print(f"      Users: {user_count}")
        except:
            print(f"      Users: Unable to read")
        
        print()
    
    return backup_files

def main():
    """Main function with menu options."""
    print("🗃️  NC Database Users Backup Tool")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Create new backup")
        print("2. List existing backups")
        print("3. Exit")
        
        choice = input("\nEnter your choice (1-3): ").strip()
        
        if choice == '1':
            backup_filename = backup_users()
            if backup_filename:
                print(f"\n💡 To restore this backup later, use:")
                print(f"   python3 restore_users.py {backup_filename}")
        
        elif choice == '2':
            list_backups()
        
        elif choice == '3':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1, 2, or 3.")

if __name__ == "__main__":
    main()