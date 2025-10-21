#!/usr/bin/env python3
"""
Migration script to migrate users from SQLite app.db to PostgreSQL nc database.

This script will:
1. Read all users from the SQLite database (instance/app.db)
2. Map fields between SQLite and PostgreSQL schemas
3. Insert users into PostgreSQL database, avoiding duplicates
4. Handle schema differences between the two databases

Schema differences:
- SQLite has 'map' column, PostgreSQL doesn't
- PostgreSQL has 'is_county' and 'state'/'county' columns, SQLite doesn't
- PostgreSQL requires phone to be NOT NULL

Usage:
    python migrate_sqlite_to_postgres.py [--dry-run]
    
    --dry-run: Preview the migration without making changes
"""

import os
import sys
import sqlite3
import json
from datetime import datetime

# Add the parent directory to Python path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, User
from main import create_app

def get_sqlite_users():
    """Read all users from the SQLite database."""
    sqlite_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'instance', 'app.db')
    
    if not os.path.exists(sqlite_path):
        print(f"❌ SQLite database not found at: {sqlite_path}")
        return []
    
    print(f"📖 Reading users from SQLite database: {sqlite_path}")
    
    conn = sqlite3.connect(sqlite_path)
    cursor = conn.cursor()
    
    # Check if users table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users';")
    if not cursor.fetchone():
        print("❌ No users table found in SQLite database")
        conn.close()
        return []
    
    # Get all users
    cursor.execute("""
        SELECT id, username, email, password, password_hash, is_admin, is_active, 
               created_at, last_login, phone, role, precinct, notes 
        FROM users
    """)
    
    users_data = cursor.fetchall()
    conn.close()
    
    print(f"✅ Found {len(users_data)} users in SQLite database")
    return users_data

def get_existing_postgres_users():
    """Get existing usernames and emails from PostgreSQL to avoid duplicates."""
    app = create_app()
    
    with app.app_context():
        existing_users = User.query.with_entities(User.username, User.email).all()
        usernames = {user.username for user in existing_users}
        emails = {user.email for user in existing_users}
        
        print(f"📊 Found {len(existing_users)} existing users in PostgreSQL database")
        return usernames, emails

def map_sqlite_to_postgres(sqlite_user):
    """Map SQLite user data to PostgreSQL User model format."""
    (id, username, email, password, password_hash, is_admin, is_active, 
     created_at, last_login, phone, role, precinct, notes) = sqlite_user
    
    # Convert SQLite datetime strings to datetime objects if they exist
    created_at_dt = None
    if created_at:
        try:
            created_at_dt = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
        except:
            created_at_dt = datetime.utcnow()
    
    last_login_dt = None
    if last_login:
        try:
            last_login_dt = datetime.fromisoformat(last_login.replace('Z', '+00:00'))
        except:
            pass
    
    # Handle missing phone (PostgreSQL requires it to be NOT NULL)
    if not phone:
        phone = "000-000-0000"  # Default placeholder
    
    # PostgreSQL specific fields not in SQLite
    is_county = False  # Default value
    state = "NC"       # Default to North Carolina
    county = "FORSYTH" # Default county
    
    return {
        'username': username,
        'email': email,
        'password': password,
        'password_hash': password_hash,
        'is_admin': bool(is_admin),
        'is_county': is_county,
        'is_active': bool(is_active),
        'created_at': created_at_dt,
        'last_login': last_login_dt,
        'phone': phone,
        'role': role or 'User',  # Default role if None
        'precinct': precinct,
        'state': state,
        'county': county,
        'notes': notes
    }

def migrate_users(dry_run=False):
    """Migrate users from SQLite to PostgreSQL."""
    print("🚀 Starting user migration from SQLite to PostgreSQL")
    print("=" * 60)
    
    # Get SQLite users
    sqlite_users = get_sqlite_users()
    if not sqlite_users:
        print("❌ No users found in SQLite database. Migration cancelled.")
        return False
    
    # Get existing PostgreSQL users
    existing_usernames, existing_emails = get_existing_postgres_users()
    
    # Filter out duplicates
    users_to_migrate = []
    skipped_users = []
    
    for sqlite_user in sqlite_users:
        username = sqlite_user[1]  # username is at index 1
        email = sqlite_user[2]     # email is at index 2
        
        if username in existing_usernames:
            skipped_users.append(f"Username '{username}' already exists")
            continue
        
        if email in existing_emails:
            skipped_users.append(f"Email '{email}' already exists")
            continue
        
        users_to_migrate.append(sqlite_user)
    
    print(f"📊 Migration Summary:")
    print(f"   - Total users in SQLite: {len(sqlite_users)}")
    print(f"   - Users to migrate: {len(users_to_migrate)}")
    print(f"   - Users to skip (duplicates): {len(skipped_users)}")
    
    if skipped_users:
        print(f"\n⚠️  Skipped users:")
        for skip_reason in skipped_users[:5]:  # Show first 5
            print(f"   - {skip_reason}")
        if len(skipped_users) > 5:
            print(f"   - ... and {len(skipped_users) - 5} more")
    
    if not users_to_migrate:
        print("\n✅ No new users to migrate. All users already exist in PostgreSQL.")
        return True
    
    if dry_run:
        print(f"\n🔍 DRY RUN MODE - Would migrate {len(users_to_migrate)} users:")
        for sqlite_user in users_to_migrate[:3]:  # Show first 3
            mapped_user = map_sqlite_to_postgres(sqlite_user)
            print(f"   - {mapped_user['username']} ({mapped_user['email']})")
        if len(users_to_migrate) > 3:
            print(f"   - ... and {len(users_to_migrate) - 3} more users")
        print("\n🏃 Run without --dry-run to perform the actual migration")
        return True
    
    # Perform the actual migration
    app = create_app()
    migrated_count = 0
    error_count = 0
    
    with app.app_context():
        for sqlite_user in users_to_migrate:
            try:
                mapped_user = map_sqlite_to_postgres(sqlite_user)
                
                # Create new User object
                new_user = User(
                    username=mapped_user['username'],
                    email=mapped_user['email'],
                    password=mapped_user['password'],
                    is_admin=mapped_user['is_admin'],
                    is_county=mapped_user['is_county'],
                    is_active=mapped_user['is_active'],
                    phone=mapped_user['phone'],
                    role=mapped_user['role'],
                    precinct=mapped_user['precinct'],
                    state=mapped_user['state'],
                    county=mapped_user['county'],
                    notes=mapped_user['notes']
                )
                
                # Set the password hash directly (bypassing the set_password method)
                new_user.password_hash = mapped_user['password_hash']
                
                # Set timestamps
                if mapped_user['created_at']:
                    new_user.created_at = mapped_user['created_at']
                if mapped_user['last_login']:
                    new_user.last_login = mapped_user['last_login']
                
                db.session.add(new_user)
                migrated_count += 1
                
                print(f"✅ Prepared user: {mapped_user['username']} ({mapped_user['email']})")
                
            except Exception as e:
                error_count += 1
                username = sqlite_user[1] if len(sqlite_user) > 1 else "unknown"
                print(f"❌ Error preparing user {username}: {e}")
        
        # Commit all changes
        if migrated_count > 0:
            try:
                db.session.commit()
                print(f"\n🎉 Migration completed successfully!")
                print(f"   - Migrated users: {migrated_count}")
                print(f"   - Errors: {error_count}")
            except Exception as e:
                db.session.rollback()
                print(f"\n❌ Failed to commit migration: {e}")
                return False
        else:
            print(f"\n⚠️  No users were migrated due to errors")
    
    return True

def main():
    """Main function to handle command line arguments and run migration."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrate users from SQLite to PostgreSQL')
    parser.add_argument('--dry-run', action='store_true', 
                       help='Preview the migration without making changes')
    
    args = parser.parse_args()
    
    print("🗄️  User Migration Tool: SQLite → PostgreSQL")
    print("=" * 50)
    
    if args.dry_run:
        print("🔍 Running in DRY RUN mode - no changes will be made")
    else:
        print("⚠️  LIVE MODE - changes will be made to the database")
        response = input("\nContinue with migration? (y/N): ")
        if response.lower() != 'y':
            print("❌ Migration cancelled by user")
            return
    
    print()
    
    try:
        success = migrate_users(dry_run=args.dry_run)
        if success:
            print("\n✅ Migration process completed")
        else:
            print("\n❌ Migration process failed")
            sys.exit(1)
    except Exception as e:
        print(f"\n💥 Migration failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()