#!/usr/bin/env python3
"""
Script to restore the maps table from a backup file.
Can restore from any backup created by backup_maps.py script.
"""

import os
import sys
import json
from datetime import datetime

# Add the parent directory to Python path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, Map
from main import create_app

def list_available_backups():
    """List all available backup files and let user choose."""
    backup_dir = os.path.dirname(os.path.abspath(__file__))
    backup_files = [f for f in os.listdir(backup_dir) if f.startswith('maps_backup_') and f.endswith('.json')]
    
    if not backup_files:
        print("❌ No backup files found")
        return None
    
    print(f"📂 Available backup files:")
    backup_files.sort(reverse=True)  # Most recent first
    
    for i, backup_file in enumerate(backup_files, 1):
        # Extract timestamp from filename
        timestamp_str = backup_file.replace('maps_backup_', '').replace('.json', '')
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp_str
        
        # Try to read map count from backup file
        file_path = os.path.join(backup_dir, backup_file)
        try:
            with open(file_path, 'r') as f:
                backup_data = json.load(f)
                map_count = backup_data.get('total_maps', 'Unknown')
                content_size_mb = backup_data.get('total_content_size_bytes', 0) / (1024 * 1024)
        except:
            map_count = 'Unable to read'
            content_size_mb = 0
        
        print(f"   {i}. {backup_file}")
        print(f"      Created: {formatted_time}")
        print(f"      Maps: {map_count}")
        if content_size_mb > 0:
            print(f"      Content: {content_size_mb:.2f} MB")
    
    print()
    choice = input("Enter the number of the backup to restore (or 'q' to quit): ").strip()
    
    if choice.lower() == 'q':
        return None
    
    try:
        index = int(choice) - 1
        if 0 <= index < len(backup_files):
            return backup_files[index]
        else:
            print("❌ Invalid selection")
            return None
    except ValueError:
        print("❌ Invalid input")
        return None

def validate_backup_file(backup_filename):
    """Validate the backup file format and contents."""
    backup_dir = os.path.dirname(os.path.abspath(__file__))
    backup_path = os.path.join(backup_dir, backup_filename)
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup file not found: {backup_filename}")
        return None
    
    try:
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        # Validate required fields
        required_fields = ['backup_timestamp', 'total_maps', 'maps']
        for field in required_fields:
            if field not in backup_data:
                print(f"❌ Invalid backup file: missing field '{field}'")
                return None
        
        maps_data = backup_data['maps']
        if not isinstance(maps_data, list):
            print("❌ Invalid backup file: 'maps' should be a list")
            return None
        
        # Validate each map entry
        for i, map_obj in enumerate(maps_data):
            required_map_fields = ['state', 'county', 'precinct', 'map']
            for field in required_map_fields:
                if field not in map_obj:
                    print(f"❌ Invalid backup file: map {i+1} missing field '{field}'")
                    return None
        
        return backup_data
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return None
    except Exception as e:
        print(f"❌ Error reading backup file: {e}")
        return None

def restore_maps(backup_filename, mode='replace'):
    """
    Restore maps from backup file.
    
    Args:
        backup_filename: Name of the backup file
        mode: 'replace' (clear existing maps) or 'merge' (add/update maps)
    """
    print("🔄 Starting maps table restore...")
    print("=" * 50)
    
    # Validate backup file
    backup_data = validate_backup_file(backup_filename)
    if not backup_data:
        return False
    
    maps_data = backup_data['maps']
    print(f"📁 Backup file: {backup_filename}")
    print(f"📅 Created: {backup_data.get('backup_datetime', 'Unknown')}")
    print(f"📊 Maps to restore: {len(maps_data)}")
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Get current map count for comparison
            current_count = Map.query.count()
            print(f"📈 Current maps in database: {current_count}")
            
            if mode == 'replace' and current_count > 0:
                confirm = input(f"\n⚠️  This will DELETE all {current_count} existing maps. Continue? (yes/no): ")
                if confirm.lower() not in ['yes', 'y']:
                    print("❌ Restore cancelled")
                    return False
                
                print("🗑️  Clearing existing maps...")
                Map.query.delete()
                db.session.commit()
                print("✅ Existing maps cleared")
            
            # Restore maps from backup
            print(f"📥 Restoring {len(maps_data)} maps...")
            
            restored_count = 0
            updated_count = 0
            error_count = 0
            
            for i, map_data in enumerate(maps_data, 1):
                try:
                    # Check if map already exists (for merge mode)
                    existing_map = None
                    if mode == 'merge':
                        existing_map = Map.query.filter_by(
                            state=map_data['state'],
                            county=map_data['county'],
                            precinct=map_data['precinct']
                        ).first()
                    
                    if existing_map:
                        # Update existing map
                        existing_map.map = map_data['map']
                        updated_count += 1
                        if i % 10 == 0:
                            print(f"   Updated map {i}/{len(maps_data)}: {map_data['state']} {map_data['county']} Precinct {map_data['precinct']}")
                    else:
                        # Create new map
                        new_map = Map(
                            state=map_data['state'],
                            county=map_data['county'],
                            precinct=map_data['precinct'],
                            map=map_data['map']
                        )
                        db.session.add(new_map)
                        restored_count += 1
                        if i % 10 == 0:
                            print(f"   Restored map {i}/{len(maps_data)}: {map_data['state']} {map_data['county']} Precinct {map_data['precinct']}")
                
                except Exception as e:
                    print(f"❌ Error restoring map {i}: {e}")
                    error_count += 1
                    continue
            
            # Commit all changes
            db.session.commit()
            
            # Show results
            final_count = Map.query.count()
            print("\n✅ Restore completed!")
            print(f"📊 Results:")
            print(f"   - Maps restored: {restored_count}")
            if mode == 'merge':
                print(f"   - Maps updated: {updated_count}")
            if error_count > 0:
                print(f"   - Errors: {error_count}")
            print(f"   - Total maps now: {final_count}")
            
            # Show breakdown by location
            states = db.session.query(Map.state.distinct()).all()
            counties = db.session.query(Map.county.distinct()).all()
            
            print(f"\n📍 Database now contains:")
            print(f"   - States: {len(states)}")
            print(f"   - Counties: {len(counties)}")
            
            # Count by state/county
            from sqlalchemy import func
            location_counts = db.session.query(
                Map.state, Map.county, func.count(Map.id)
            ).group_by(Map.state, Map.county).all()
            
            for state, county, count in location_counts:
                print(f"   - {state} {county}: {count} maps")
            
            return True
            
        except Exception as e:
            print(f"❌ Error during restore: {e}")
            db.session.rollback()
            return False

def main():
    """Main function to handle command line arguments or interactive mode."""
    print("🗺️  NC Database Maps Restore Tool")
    print("=" * 50)
    
    # Check if backup filename was provided as argument
    if len(sys.argv) > 1:
        backup_filename = sys.argv[1]
        
        # Check if mode was specified
        mode = 'replace'  # default
        if len(sys.argv) > 2:
            mode = sys.argv[2].lower()
            if mode not in ['replace', 'merge']:
                print(f"❌ Invalid mode: {mode}. Use 'replace' or 'merge'")
                sys.exit(1)
        
        print(f"📁 Backup file: {backup_filename}")
        print(f"🔄 Mode: {mode}")
        
        success = restore_maps(backup_filename, mode)
        if success:
            print(f"\n💡 Maps successfully restored from {backup_filename}")
        else:
            print(f"\n❌ Restore failed")
            sys.exit(1)
    
    else:
        # Interactive mode
        while True:
            print("\nOptions:")
            print("1. Restore maps (replace all existing)")
            print("2. Merge maps (add new, update existing)")
            print("3. List available backups")
            print("4. Exit")
            
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                backup_filename = list_available_backups()
                if backup_filename:
                    restore_maps(backup_filename, 'replace')
            
            elif choice == '2':
                backup_filename = list_available_backups()
                if backup_filename:
                    restore_maps(backup_filename, 'merge')
            
            elif choice == '3':
                list_available_backups()
            
            elif choice == '4':
                print("👋 Goodbye!")
                break
            
            else:
                print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()