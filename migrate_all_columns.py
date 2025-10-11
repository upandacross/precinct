#!/usr/bin/env python3
"""
Comprehensive database migration script to add all missing columns.
"""

import sqlite3
import os

def migrate_all_columns():
    """Add all missing columns to users table."""
    
    # Define all expected columns that might be missing
    expected_columns = {
        'state': 'VARCHAR(50)',
        'county': 'VARCHAR(100)', 
        'is_county': 'BOOLEAN DEFAULT 0 NOT NULL'
    }
    
    # Database paths to check
    db_paths = [
        'instance/app.db',
        'instance/app_dev.db'
    ]
    
    for db_path in db_paths:
        if os.path.exists(db_path):
            print(f"Processing database: {db_path}")
            
            # Connect to database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            try:
                # Check existing columns
                cursor.execute("PRAGMA table_info(users)")
                existing_columns = [column[1] for column in cursor.fetchall()]
                print(f"  Existing columns: {existing_columns}")
                
                # Add missing columns
                for col_name, col_definition in expected_columns.items():
                    if col_name not in existing_columns:
                        sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_definition}"
                        print(f"  Adding column: {col_name}")
                        cursor.execute(sql)
                        conn.commit()
                        print(f"    Successfully added {col_name} column!")
                    else:
                        print(f"    Column {col_name} already exists")
                
            except Exception as e:
                print(f"  Error migrating {db_path}: {e}")
                conn.rollback()
            
            finally:
                conn.close()
        else:
            print(f"Database not found: {db_path}")
    
    print("Migration completed!")

if __name__ == "__main__":
    migrate_all_columns()