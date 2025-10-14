#!/usr/bin/env python3
"""
Load Map HTML Files into NC Database

This script scans the static/html directory for HTML files containing precinct maps
and loads them into the NC database maps table. The precinct number is extracted
from the first three characters of the filename, and all maps are set to 
county='FORSYTH' and state='NC'.

Usage:
    python load_maps.py
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# Add the project root to the Python path to import our modules
project_root = Path(__file__).parent.parent  # Go up one level from app_administration
sys.path.insert(0, str(project_root))

from config import Config
from models import db, Map
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

def setup_database():
    """Initialize database connection using the NC database configuration."""
    # Use the NC database connection string from config
    engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
    
    # Create a session
    Session = sessionmaker(bind=engine)
    session = Session()
    
    return session

def extract_precinct_from_filename(filename):
    """
    Extract precinct number from the first three characters of the filename.
    
    Args:
        filename (str): The HTML filename (e.g., "001_winston_salem_north.html")
    
    Returns:
        str: The precinct number (e.g., "001")
    """
    # Remove file extension and get first 3 characters
    basename = os.path.splitext(filename)[0]
    precinct = basename[:3]
    
    # Validate that it's a 3-digit precinct number
    if len(precinct) == 3 and precinct.isdigit():
        return precinct
    else:
        raise ValueError(f"Invalid precinct format in filename: {filename}")

def load_html_file(filepath):
    """
    Load the content of an HTML file.
    
    Args:
        filepath (str): Path to the HTML file
    
    Returns:
        str: The HTML content
    """
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.read()

def load_maps_into_database():
    """
    Scan the static_html directory and load all HTML files into the maps table.
    """
    # Path to the static_html directory (restored from git)
    html_dir = project_root / 'static_html'
    
    if not html_dir.exists():
        print(f"Error: HTML directory does not exist: {html_dir}")
        return False
    
    # Setup database connection
    try:
        session = setup_database()
    except Exception as e:
        print(f"Error connecting to database: {e}")
        return False
    
    # Find all HTML files in the directory
    html_files = list(html_dir.glob('*.html'))
    
    if not html_files:
        print(f"No HTML files found in {html_dir}")
        return False
    
    print(f"Found {len(html_files)} HTML files to process...")
    
    loaded_count = 0
    updated_count = 0
    error_count = 0
    
    for html_file in html_files:
        try:
            # Extract precinct from filename
            precinct = extract_precinct_from_filename(html_file.name)
            
            # Load HTML content
            html_content = load_html_file(html_file)
            
            # Check if map already exists
            existing_map = session.query(Map).filter_by(
                state='NC',
                county='FORSYTH',
                precinct=precinct
            ).first()
            
            if existing_map:
                # Update existing map
                existing_map.map = html_content
                print(f"Updated map for precinct {precinct} from {html_file.name}")
                updated_count += 1
            else:
                # Create new map entry
                new_map = Map(
                    state='NC',
                    county='FORSYTH',
                    precinct=precinct,
                    map=html_content
                )
                session.add(new_map)
                print(f"Loaded new map for precinct {precinct} from {html_file.name}")
                loaded_count += 1
                
        except Exception as e:
            print(f"Error processing {html_file.name}: {e}")
            error_count += 1
            continue
    
    # Commit all changes
    try:
        session.commit()
        print(f"\nDatabase updated successfully!")
        print(f"Maps loaded: {loaded_count}")
        print(f"Maps updated: {updated_count}")
        if error_count > 0:
            print(f"Errors encountered: {error_count}")
        
        return True
        
    except Exception as e:
        print(f"Error committing to database: {e}")
        session.rollback()
        return False
    
    finally:
        session.close()

def list_current_maps():
    """List all maps currently in the database for verification."""
    try:
        session = setup_database()
        
        maps = session.query(Map).filter_by(state='NC', county='FORSYTH').order_by(Map.precinct).all()
        
        if not maps:
            print("No maps found in database for Forsyth County, NC")
            return
        
        print(f"\nCurrent maps in database:")
        print("Precinct | State | County  | Created")
        print("-" * 40)
        
        for map_entry in maps:
            created = map_entry.created_at.strftime('%Y-%m-%d %H:%M') if map_entry.created_at else 'Unknown'
            print(f"{map_entry.precinct:8} | {map_entry.state:5} | {map_entry.county:7} | {created}")
            
    except Exception as e:
        print(f"Error listing maps: {e}")
    finally:
        session.close()

def main():
    """Main function to load maps and display results."""
    print("Map Loading Script for NC Database")
    print("=" * 40)
    print(f"HTML Directory: {project_root / 'static_html'}")
    print(f"Target: NC Database - Forsyth County")
    print()
    
    # Load maps into database
    success = load_maps_into_database()
    
    if success:
        # List current maps for verification
        list_current_maps()
    else:
        print("Map loading failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()