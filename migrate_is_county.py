#!/usr/bin/env python3
"""
Direct database migration script to add is_county column.
This bypasses Flask app initialization to avoid the missing column error.
"""

import sqlite3
import os

def add_is_county_column():
    """Add is_county column to users table directly."""
    
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
                # Check if column already exists
                cursor.execute("PRAGMA table_info(users)")
                columns = [column[1] for column in cursor.fetchall()]
                
                if 'is_county' in columns:
                    print(f"  is_county column already exists in {db_path}!")
                    continue
                
                # Add the new column
                cursor.execute("ALTER TABLE users ADD COLUMN is_county BOOLEAN DEFAULT 0 NOT NULL")
                conn.commit()
                print(f"  Successfully added is_county column to {db_path}!")
                
            except Exception as e:
                print(f"  Error adding column to {db_path}: {e}")
                conn.rollback()
            
            finally:
                conn.close()
        else:
            print(f"Database not found: {db_path}")
    
    print("Migration completed!")

if __name__ == "__main__":
    add_is_county_column()