#!/usr/bin/env python3
"""
Database migration script for Precinct application.

This script adds the missing 'updated_at' column to the maps table.
Run this script to update existing databases to match the current model schema.

Usage:
    python migrate_database.py

Make sure to backup your database before running this migration!
"""

import os
import sys
from datetime import datetime
from main import create_app
from models import db

def run_migration():
    """Run database migration to add updated_at column to maps table."""
    
    app = create_app()
    
    with app.app_context():
        try:
            # Check if we're using SQLite (test) or PostgreSQL (production)
            engine = db.engine
            dialect_name = engine.dialect.name
            
            print(f"🔍 Detected database dialect: {dialect_name}")
            
            # Check if maps table exists first
            inspector = db.inspect(engine)
            tables = inspector.get_table_names()
            
            if 'maps' not in tables:
                print("ℹ️  Maps table doesn't exist. Running db.create_all() to create all tables...")
                db.create_all()
                print("✅ All tables created with current schema. No migration needed.")
                return True
            
            # Check if updated_at column already exists
            columns = [col['name'] for col in inspector.get_columns('maps')]
            
            if 'updated_at' in columns:
                print("✅ Column 'updated_at' already exists in maps table. No migration needed.")
                return True
            
            print("📝 Adding 'updated_at' column to maps table...")
            
            # SQL to add the updated_at column
            if dialect_name == 'postgresql':
                # PostgreSQL syntax
                sql = """
                ALTER TABLE maps 
                ADD COLUMN updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
                
                UPDATE maps 
                SET updated_at = created_at 
                WHERE updated_at IS NULL;
                """
            else:
                # SQLite syntax (for testing)
                sql = """
                ALTER TABLE maps 
                ADD COLUMN updated_at DATETIME DEFAULT CURRENT_TIMESTAMP;
                
                UPDATE maps 
                SET updated_at = created_at 
                WHERE updated_at IS NULL;
                """
            
            # Execute the migration
            db.session.execute(db.text(sql))
            db.session.commit()
            
            print("✅ Migration completed successfully!")
            print("   - Added 'updated_at' column to maps table")
            print("   - Set initial values to match created_at timestamps")
            
            # Verify the migration
            columns_after = [col['name'] for col in inspector.get_columns('maps')]
            if 'updated_at' in columns_after:
                print("✅ Verification: updated_at column successfully added")
            else:
                print("❌ Verification failed: updated_at column not found")
                return False
                
            return True
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            db.session.rollback()
            return False

def backup_reminder():
    """Display backup reminder to user."""
    print("=" * 60)
    print("🚨 IMPORTANT: DATABASE MIGRATION")
    print("=" * 60)
    print()
    print("This script will modify your database schema by adding:")
    print("  - 'updated_at' column to the 'maps' table")
    print()
    print("🔒 BACKUP RECOMMENDATION:")
    print("  Please ensure you have a current backup of your database")
    print("  before proceeding with this migration.")
    print()
    print("📋 Migration Details:")
    print("  - Adds updated_at DATETIME column to maps table")
    print("  - Sets initial values to match existing created_at values")
    print("  - Uses database-appropriate SQL syntax")
    print()

if __name__ == '__main__':
    backup_reminder()
    
    # Ask for confirmation
    response = input("Do you want to proceed with the migration? (yes/no): ").lower().strip()
    
    if response in ['yes', 'y']:
        print("\n🚀 Starting database migration...")
        success = run_migration()
        
        if success:
            print("\n🎉 Migration completed successfully!")
            print("\nNext steps:")
            print("1. Restart your application")
            print("2. Verify that map timestamps are working correctly")
            print("3. Test map creation/updates to ensure updated_at is functioning")
        else:
            print("\n❌ Migration failed. Please check the error messages above.")
            print("   Your database has been left unchanged.")
            sys.exit(1)
    else:
        print("\n⏹️  Migration cancelled by user.")
        print("   Run this script again when you're ready to migrate.")