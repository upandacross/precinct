#!/usr/bin/env python3
"""
Flask-Migrate setup and migration script for adding is_county column.
"""

from flask import Flask
from flask_migrate import Migrate, init, migrate, upgrade
from main import create_app, db
import os

def setup_migrations():
    """Set up Flask-Migrate and create migration for is_county column."""
    
    app = create_app()
    migrate_obj = Migrate(app, db)
    
    with app.app_context():
        migrations_dir = os.path.join(app.root_path, 'migrations')
        
        # Initialize migrations if not already done
        if not os.path.exists(migrations_dir):
            print("Initializing Flask-Migrate...")
            init()
            print("Migrations initialized!")
        
        # Create migration for is_county column
        print("Creating migration for is_county column...")
        migrate(message="Add is_county column to users table")
        print("Migration created!")
        
        # Apply the migration
        print("Applying migration...")
        upgrade()
        print("Migration applied successfully!")

if __name__ == "__main__":
    setup_migrations()