#!/usr/bin/env python3
"""
Script to backup the maps table from the NC database.
Creates a timestamped backup file that can be used to restore maps later.
"""

import os
import sys
import json
from datetime import datetime

# Add the parent directory to Python path to import models
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import db, Map
from main import create_app

def backup_maps():
    """Backup all maps from the database to a JSON file."""
    print("🔄 Starting maps table backup...")
    print("=" * 50)
    
    # Create Flask app context
    app = create_app()
    
    with app.app_context():
        try:
            # Get all maps from the database
            maps = Map.query.all()
            print(f"Found {len(maps)} maps in the database")
            
            if not maps:
                print("⚠️  No maps found in the database")
                return None
            
            # Convert maps to dictionary format for JSON serialization
            maps_data = []
            total_content_size = 0
            
            for map_obj in maps:
                map_content_size = len(map_obj.map) if map_obj.map else 0
                total_content_size += map_content_size
                
                map_dict = {
                    'id': map_obj.id,
                    'state': map_obj.state,
                    'county': map_obj.county,
                    'precinct': map_obj.precinct,
                    'map': map_obj.map,  # Full HTML content
                    'created_at': map_obj.created_at.isoformat() if map_obj.created_at else None,
                    'content_size': map_content_size
                }
                maps_data.append(map_dict)
            
            # Create timestamped backup filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_filename = f"maps_backup_{timestamp}.json"
            backup_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), backup_filename)
            
            # Write backup to JSON file
            backup_data = {
                'backup_timestamp': timestamp,
                'backup_datetime': datetime.now().isoformat(),
                'total_maps': len(maps_data),
                'total_content_size_bytes': total_content_size,
                'maps': maps_data
            }
            
            with open(backup_path, 'w') as f:
                json.dump(backup_data, f, indent=2)
            
            print(f"✅ Backup completed successfully!")
            print(f"📁 Backup saved to: {backup_filename}")
            print(f"📊 Maps backed up: {len(maps_data)}")
            
            # Show breakdown by state/county
            states = set(m['state'] for m in maps_data if m['state'])
            counties = set(m['county'] for m in maps_data if m['county'])
            
            print(f"   - States: {len(states)} ({', '.join(sorted(states))})")
            print(f"   - Counties: {len(counties)} ({', '.join(sorted(counties))})")
            print(f"   - Total content size: {total_content_size / (1024 * 1024):.2f} MB")
            
            # Show breakdown by county
            county_counts = {}
            for map_obj in maps_data:
                county_key = f"{map_obj['state']} {map_obj['county']}"
                county_counts[county_key] = county_counts.get(county_key, 0) + 1
            
            if county_counts:
                print(f"\n📍 Maps by location:")
                for location, count in sorted(county_counts.items()):
                    print(f"   - {location}: {count} maps")
            
            # Get file size
            backup_size = os.path.getsize(backup_path)
            print(f"\n💾 Backup file size: {backup_size / (1024 * 1024):.2f} MB")
            
            return backup_filename
            
        except Exception as e:
            print(f"❌ Error during backup: {e}")
            return None

def list_backups():
    """List all available backup files."""
    backup_dir = os.path.dirname(os.path.abspath(__file__))
    backup_files = [f for f in os.listdir(backup_dir) if f.startswith('maps_backup_') and f.endswith('.json')]
    
    if not backup_files:
        print("📂 No backup files found")
        return []
    
    print(f"📂 Found {len(backup_files)} backup file(s):")
    backup_files.sort(reverse=True)  # Most recent first
    
    for i, backup_file in enumerate(backup_files, 1):
        # Extract timestamp from filename
        timestamp_str = backup_file.replace('maps_backup_', '').replace('.json', '')
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
            formatted_time = timestamp.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp_str
        
        # Get file size
        file_path = os.path.join(backup_dir, backup_file)
        file_size = os.path.getsize(file_path)
        size_mb = file_size / (1024 * 1024)
        
        print(f"   {i}. {backup_file}")
        print(f"      Created: {formatted_time}")
        print(f"      Size: {size_mb:.2f} MB")
        
        # Try to read map count from backup file
        try:
            with open(file_path, 'r') as f:
                backup_data = json.load(f)
                map_count = backup_data.get('total_maps', 'Unknown')
                content_size_mb = backup_data.get('total_content_size_bytes', 0) / (1024 * 1024)
                print(f"      Maps: {map_count}")
                print(f"      Content: {content_size_mb:.2f} MB")
        except:
            print(f"      Maps: Unable to read")
        
        print()
    
    return backup_files

def verify_backup(backup_filename):
    """Verify the integrity of a backup file."""
    backup_dir = os.path.dirname(os.path.abspath(__file__))
    backup_path = os.path.join(backup_dir, backup_filename)
    
    if not os.path.exists(backup_path):
        print(f"❌ Backup file not found: {backup_filename}")
        return False
    
    try:
        print(f"🔍 Verifying backup: {backup_filename}")
        
        with open(backup_path, 'r') as f:
            backup_data = json.load(f)
        
        required_fields = ['backup_timestamp', 'backup_datetime', 'total_maps', 'maps']
        for field in required_fields:
            if field not in backup_data:
                print(f"❌ Missing required field: {field}")
                return False
        
        maps_data = backup_data['maps']
        expected_count = backup_data['total_maps']
        actual_count = len(maps_data)
        
        if actual_count != expected_count:
            print(f"❌ Map count mismatch: expected {expected_count}, found {actual_count}")
            return False
        
        # Verify each map has required fields
        required_map_fields = ['id', 'state', 'county', 'precinct', 'map']
        for i, map_obj in enumerate(maps_data):
            for field in required_map_fields:
                if field not in map_obj:
                    print(f"❌ Map {i+1} missing required field: {field}")
                    return False
        
        print(f"✅ Backup verification passed!")
        print(f"   - Maps: {actual_count}")
        print(f"   - Created: {backup_data['backup_datetime']}")
        
        return True
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON format: {e}")
        return False
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

def main():
    """Main function with menu options."""
    print("🗺️  NC Database Maps Backup Tool")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Create new backup")
        print("2. List existing backups")
        print("3. Verify backup integrity")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == '1':
            backup_filename = backup_maps()
            if backup_filename:
                print(f"\n💡 To restore this backup later, use:")
                print(f"   python3 restore_maps.py {backup_filename}")
        
        elif choice == '2':
            list_backups()
        
        elif choice == '3':
            backups = list_backups()
            if backups:
                print(f"\nEnter backup filename to verify (or press Enter to cancel):")
                filename = input("Filename: ").strip()
                if filename:
                    verify_backup(filename)
        
        elif choice == '4':
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please enter 1, 2, 3, or 4.")

if __name__ == "__main__":
    main()