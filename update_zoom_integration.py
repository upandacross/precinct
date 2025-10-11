#!/usr/bin/env python3
"""
Script to update custom zoom controls to integrate properly with existing zoom functions.
"""

import os
import glob
import re

def update_custom_zoom_integration(file_path):
    """Update custom zoom functions to integrate with existing zoom functions."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if custom zoom functions exist
    if 'customZoomIn()' not in content:
        print(f"No custom zoom functions found in {file_path}")
        return False
    
    # Find the map ID using regex
    map_id_match = re.search(r'var (map_[a-f0-9]+) = L\.map\(', content)
    if not map_id_match:
        print(f"Could not find map ID in {file_path}")
        return False
    
    map_id = map_id_match.group(1)
    
    # Replace the custom zoom functions to integrate with existing functions
    old_custom_zoom = rf'// Custom zoom functions to replace Leaflet controls\s*function customZoomIn\(\) {{\s*if \(typeof {map_id} !== \'undefined\'\) {{\s*{map_id}\.zoomIn\(1\);\s*updateZoomButtonStates\(\);\s*}}\s*}}\s*function customZoomOut\(\) {{\s*if \(typeof {map_id} !== \'undefined\'\) {{\s*{map_id}\.zoomOut\(1\);\s*updateZoomButtonStates\(\);\s*}}\s*}}'
    
    new_custom_zoom = f'''// Custom zoom functions to replace Leaflet controls
        function customZoomIn() {{
            // Call existing zoomIn function if it exists, otherwise use map directly
            if (typeof zoomIn !== 'undefined') {{
                zoomIn();
            }} else if (typeof {map_id} !== 'undefined') {{
                {map_id}.zoomIn(1);
            }}
            updateZoomButtonStates();
        }}
        
        function customZoomOut() {{
            // Call existing zoomOut function if it exists, otherwise use map directly
            if (typeof zoomOut !== 'undefined') {{
                zoomOut();
            }} else if (typeof {map_id} !== 'undefined') {{
                {map_id}.zoomOut(1);
            }}
            updateZoomButtonStates();
        }}'''
    
    # Use re.sub with DOTALL flag to handle multiline patterns
    content = re.sub(old_custom_zoom, new_custom_zoom, content, flags=re.DOTALL)
    
    # Write the modified content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Updated custom zoom integration in {file_path}")
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
            if update_custom_zoom_integration(file_path):
                success_count += 1
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
    
    print(f"\nCompleted! Successfully updated {success_count} out of {len(html_files)} files.")

if __name__ == "__main__":
    main()