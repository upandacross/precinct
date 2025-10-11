#!/usr/bin/env python3
"""
Migration script to add is_county column to existing database.
This preserves existing user data while adding the new column.
"""

import sqlite3
import os
from main import create_app

def add_is_county_column():
    """Add is_county column to users table if it doesn't exist."""
    
    # Get the app instance to access config
    app = create_app()
    
    with app.app_context():
        # Get database path from config
        db_path = os.path.join(app.instance_path, 'app.db')
        
        if not os.path.exists(db_path):
            print("Database doesn't exist. Run the app to create it first.")
            return
        
        # Connect to database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if column already exists
            cursor.execute("PRAGMA table_info(users)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'is_county' in columns:
                print("is_county column already exists!")
                return
            
            # Add the new column
            cursor.execute("ALTER TABLE users ADD COLUMN is_county BOOLEAN DEFAULT 0 NOT NULL")
            conn.commit()
            print("Successfully added is_county column to users table!")
            
        except Exception as e:
            print(f"Error adding column: {e}")
            conn.rollback()
        
        finally:
            conn.close()

if __name__ == "__main__":
    add_is_county_column()