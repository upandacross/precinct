#!/usr/bin/env python3
"""
Script to restore the users table from a backup file.
Can restore from any backup created by backup_users.py script.
"""

import os
import sys
import json
from datetime import datetime

# Add the parent directory to Python path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User
from main import create_app

def list_available_backups():
    """List all available backup files and let user choose."""
    backup_dir = os.path.dirname(os.path.abspath(__file__))
    backup_files = [f for f in os.listdir(backup_dir) if f.startswith('users_backup_') and f.endswith('.json')]
    
    if not backup_files:
        print("❌ No backup files found")
        return None
    
    print(f"📂 Available backup files:")
    backup_files.sort(reverse=True)  # Most recent first
    
    for i, backup_file in enumerate(backup_files, 1):
        # Extract timestamp from filename
        timestamp_str = backup_file.replace('users_backup_', '').replace('.json', '')
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp_str
        
        # Try to read user count from backup file
        file_path = os.path.join(backup_dir, backup_file)
        try:
            with open(file_path, 'r') as f:
                backup_data = json.load(f)
                user_count = backup_data.get('total_users', 'Unknown')
        except:
            user_count = 'Unable to read'
        
        print(f"   {i}. {backup_file}")
        print(f"      Created: {formatted_time}")
        print(f"      Users: {user_count}")
        print()
    
    # Let user choose
    while True:
        try:
            choice = input(f"Select backup file (1-{len(backup_files)}) or 'q' to quit: ").strip()
            if choice.lower() == 'q':
                return None
            
            choice_idx = int(choice) - 1
            if 0 <= choice_idx < len(backup_files):
                return backup_files[choice_idx]
            else:
                print(f"❌ Invalid choice. Please enter 1-{len(backup_files)}")
        except ValueError:
            print("❌ Invalid input. Please enter a number or 'q'")

def load_backup_file(backup_filename):
    """Load and validate backup file."""
    if not backup_filename:
        return None
    
    backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), backup_filename)
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup file not found: {backup_filename}")
        return None
    
    try:
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        # Validate backup structure
        if 'users' not in backup_data:
            print(f"❌ Invalid backup file format: missing 'users' key")
            return None
        
        users_data = backup_data['users']
        print(f"📄 Backup file loaded: {backup_filename}")
        print(f"📅 Created: {backup_data.get('backup_datetime', 'Unknown')}")
        print(f"👥 Users in backup: {len(users_data)}")
        
        return users_data
    
    except Exception as e:
        print(f"❌ Error loading backup file: {e}")
        return None

def restore_users(users_data, clear_existing=True):
    """Restore users from backup data."""
    if not users_data:
        return False
    
    print(f"\n🔄 Starting users restore...")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            if clear_existing:
                # Clear existing users
                existing_count = User.query.count()
                print(f"🗑️  Clearing {existing_count} existing users...")
                User.query.delete()
                db.session.flush()  # Apply deletes but don't commit yet
            
            # Restore users from backup
            restored_count = 0
            skipped_count = 0
            
            for user_data in users_data:
                try:
                    # Check if user already exists (if not clearing existing)
                    if not clear_existing:
                        existing_user = User.query.filter_by(username=user_data['username']).first()
                        if existing_user:
                            print(f"⚠️  Skipping existing user: {user_data['username']}")
                            skipped_count += 1
                            continue
                    
                    # Create new user
                    user = User(
                        username=user_data['username'],
                        email=user_data['email'],
                        password=user_data['password'],
                        password_hash=user_data['password_hash'],
                        is_admin=user_data['is_admin'],
                        is_county=user_data['is_county'],
                        is_active=user_data['is_active'],
                        state=user_data['state'],
                        county=user_data['county'],
                        precinct=user_data['precinct'],
                        phone=user_data['phone'],
                        role=user_data['role'],
                        notes=user_data['notes']
                    )
                    
                    # Set timestamps if available
                    if user_data.get('created_at'):
                        user.created_at = datetime.fromisoformat(user_data['created_at'])
                    
                    if user_data.get('last_login'):
                        user.last_login = datetime.fromisoformat(user_data['last_login'])
                    
                    db.session.add(user)
                    restored_count += 1
                    
                except Exception as e:
                    print(f"⚠️  Error restoring user {user_data.get('username', 'unknown')}: {e}")
                    skipped_count += 1
                    continue
            
            # Commit all changes
            db.session.commit()
            
            print(f"✅ Restore completed successfully!")
            print(f"📊 Users restored: {restored_count}")
            if skipped_count > 0:
                print(f"⚠️  Users skipped: {skipped_count}")
            
            # Show breakdown by user type
            total_users = User.query.count()
            admin_count = User.query.filter_by(is_admin=True).count()
            county_count = User.query.filter_by(is_county=True, is_admin=False).count()
            active_count = User.query.filter_by(is_active=True).count()
            
            print(f"\n📈 Current database status:")
            print(f"   - Total users: {total_users}")
            print(f"   - Admin users: {admin_count}")
            print(f"   - County users: {county_count}")
            print(f"   - Regular users: {total_users - admin_count - county_count}")
            print(f"   - Active users: {active_count}")
            print(f"   - Inactive users: {total_users - active_count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during restore: {e}")
            db.session.rollback()
            return False

def main():
    """Main function for restore script."""
    if len(sys.argv) > 1:
        # Backup filename provided as command line argument
        backup_filename = sys.argv[1]
        print(f"🔄 Restoring from specified backup: {backup_filename}")
    else:
        # Interactive mode - let user choose backup
        print("🔄 NC Database Users Restore Tool")
        print("=" * 50)
        backup_filename = list_available_backups()
        
        if not backup_filename:
            print("👋 No backup selected. Exiting...")
            return
    
    # Load backup file
    users_data = load_backup_file(backup_filename)
    if not users_data:
        return
    
    # Confirm restore operation
    print(f"\n⚠️  WARNING: This will replace ALL existing users in the database!")
    print(f"Users to restore: {len(users_data)}")
    
    confirm = input("\nAre you sure you want to continue? Type 'yes' to confirm: ").strip().lower()
    
    if confirm != 'yes':
        print("❌ Restore cancelled by user")
        return
    
    # Perform restore
    success = restore_users(users_data)
    
    if success:
        print("\n🎉 Users successfully restored from backup!")
        print("💡 You can now use the application with the restored user data.")
    else:
        print("\n❌ Restore failed. Check the error messages above.")

if __name__ == "__main__":
    main()