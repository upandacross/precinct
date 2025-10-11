#!/usr/bin/env python3
"""
Script to disable default Leaflet zoom controls and move enhanced zoom controls 
from lower right to upper left in all static HTML map files.
"""

import os
import glob
import re

def modify_zoom_controls(file_path):
    """Disable Leaflet zoom controls and move enhanced controls to upper left."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if this file has the map configuration
    if 'zoomControl": true' not in content:
        print(f"No zoom controls found in {file_path}")
        return False
    
    # Step 1: Disable the default Leaflet zoom controls
    content = content.replace('"zoomControl": true', '"zoomControl": false')
    
    # Step 2: Check if enhanced zoom controls exist in new tab view and move them
    if 'new-tab-zoom-controls' in content:
        # Update the positioning from bottom-right to top-left
        old_style = 'style="position: fixed; bottom: 20px; right: 20px;'
        new_style = 'style="position: fixed; top: 20px; left: 20px;'
        content = content.replace(old_style, new_style)
        
        print(f"Modified zoom controls in {file_path}")
        
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    else:
        # For files without enhanced controls, just disable Leaflet controls for now
        print(f"Disabled Leaflet zoom controls in {file_path}")
        
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True

def main():
    """Main function to process all HTML files in the static_html directory."""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_html_dir = os.path.join(script_dir, 'static_html')
    
    if not os.path.exists(static_html_dir):
        print(f"Error: {static_html_dir} directory not found!")
        return
    
    # Find all HTML files
    html_files = glob.glob(os.path.join(static_html_dir, '*.html'))
    
    if not html_files:
        print("No HTML files found in static_html directory!")
        return
    
    print(f"Found {len(html_files)} HTML files to process...")
    
    success_count = 0
    for file_path in sorted(html_files):
        filename = os.path.basename(file_path)
        try:
            if modify_zoom_controls(file_path):
                success_count += 1
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
    
    print(f"\nCompleted! Successfully modified {success_count} out of {len(html_files)} files.")
    print("\nChanges made:")
    print("- Disabled default Leaflet zoom controls (upper left)")
    print("- Moved enhanced new-tab zoom controls from lower right to upper left")

if __name__ == "__main__":
    main()