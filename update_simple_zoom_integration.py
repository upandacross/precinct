#!/usr/bin/env python3
"""
Simple script to update all files to use integrated zoom functions.
"""

import os
import glob

def update_file_zoom_integration(file_path):
    """Update a single file's zoom integration."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Skip files that don't have custom zoom functions
    if 'customZoomIn()' not in content:
        return False
    
    # Replace the zoomIn map calls with calls to existing functions
    content = content.replace('map_', 'MAP_ID_PLACEHOLDER_')  # Temporary placeholder
    content = content.replace('.zoomIn(1);', '.zoomIn(1); // Direct map call')
    content = content.replace('.zoomOut(1);', '.zoomOut(1); // Direct map call')
    
    # Add integration check before direct map calls
    old_pattern = '''            if (typeof MAP_ID_PLACEHOLDER_'''
    new_pattern = '''            // Call existing zoomIn function if available, otherwise use map directly
            if (typeof zoomIn !== 'undefined') {
                zoomIn();
            } else if (typeof MAP_ID_PLACEHOLDER_'''
    
    content = content.replace(old_pattern, new_pattern)
    
    # Similar for zoomOut
    old_pattern_out = '''        function customZoomOut() {
            if (typeof MAP_ID_PLACEHOLDER_'''
    new_pattern_out = '''        function customZoomOut() {
            // Call existing zoomOut function if available, otherwise use map directly  
            if (typeof zoomOut !== 'undefined') {
                zoomOut();
            } else if (typeof MAP_ID_PLACEHOLDER_'''
    
    content = content.replace(old_pattern_out, new_pattern_out)
    
    # Restore map ID
    content = content.replace('MAP_ID_PLACEHOLDER_', 'map_')
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    return True

def main():
    """Update all HTML files."""
    
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_html_dir = os.path.join(script_dir, 'static_html')
    html_files = glob.glob(os.path.join(static_html_dir, '*.html'))
    
    print(f"Updating zoom integration in {len(html_files)} files...")
    
    for file_path in html_files:
        try:
            update_file_zoom_integration(file_path)
        except Exception as e:
            print(f"Error updating {os.path.basename(file_path)}: {e}")
    
    print("Integration update completed!")

if __name__ == "__main__":
    main()