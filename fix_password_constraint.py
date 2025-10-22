#!/usr/bin/env python3
"""
Remove unique constraint from password field in users table.

This fixes the Flask-Admin user creation issue where the unique constraint
on the password field was causing form field generation to fail with
"'tuple' object has no attribute 'items'" error.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import create_app
from models import db
import traceback

def remove_password_unique_constraint():
    """Remove the unique constraint from the password column."""
    app = create_app()
    
    with app.app_context():
        print("Removing unique constraint from password field...")
        
        try:
            # Check if the constraint exists first
            inspector = db.inspect(db.engine)
            constraints = inspector.get_unique_constraints('users')
            password_constraint = None
            
            for constraint in constraints:
                if 'password' in constraint['column_names']:
                    password_constraint = constraint
                    break
            
            if password_constraint:
                print(f"Found password unique constraint: {password_constraint['name']}")
                
                # Drop the unique constraint
                with db.engine.connect() as conn:
                    # PostgreSQL syntax to drop unique constraint
                    sql = f"ALTER TABLE users DROP CONSTRAINT IF EXISTS {password_constraint['name']}"
                    print(f"Executing: {sql}")
                    conn.execute(db.text(sql))
                    conn.commit()
                    print("✓ Unique constraint removed successfully")
            else:
                print("No unique constraint found on password field")
                
                # Check if there might be a unique index instead
                indexes = inspector.get_indexes('users')
                password_index = None
                
                for index in indexes:
                    if 'password' in index['column_names'] and index.get('unique', False):
                        password_index = index
                        break
                
                if password_index:
                    print(f"Found password unique index: {password_index['name']}")
                    
                    with db.engine.connect() as conn:
                        sql = f"DROP INDEX IF EXISTS {password_index['name']}"
                        print(f"Executing: {sql}")
                        conn.execute(db.text(sql))
                        conn.commit()
                        print("✓ Unique index removed successfully")
                else:
                    print("No unique index found on password field either")
            
            # Verify the fix by checking current constraints
            print("\nVerifying current constraints...")
            constraints = inspector.get_unique_constraints('users')
            indexes = inspector.get_indexes('users')
            
            print("Current unique constraints:")
            for constraint in constraints:
                print(f"  {constraint['name']}: {constraint['column_names']}")
            
            print("Current unique indexes:")
            for index in indexes:
                if index.get('unique', False):
                    print(f"  {index['name']}: {index['column_names']}")
            
            print("\n✓ Password field unique constraint removal complete")
            
        except Exception as e:
            print(f"✗ Error removing password unique constraint: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    remove_password_unique_constraint()