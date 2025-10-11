#!/usr/bin/env python3
"""
Script to remove the custom zoom controls overlay from all static HTML map files.
This removes the zoom buttons that appear in the upper right corner of each map.
"""

import os
import glob
import re

def remove_custom_zoom_controls(file_path):
    """Remove custom zoom controls from a static HTML file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if custom zoom controls exist
    if 'custom-zoom-controls' not in content:
        print(f"No custom zoom controls found in {file_path}")
        return False
    
    # Remove the CSS for custom zoom controls
    css_pattern = r'<style>\s*\.custom-zoom-controls\s*{.*?}\s*</style>'
    content = re.sub(css_pattern, '', content, flags=re.DOTALL)
    
    # Remove the HTML for custom zoom controls
    html_pattern = r'<!-- Custom Zoom Controls -->\s*<div class="custom-zoom-controls">.*?</div>'
    content = re.sub(html_pattern, '', content, flags=re.DOTALL)
    
    # Write the modified content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Removed custom zoom controls from {file_path}")
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
            if remove_custom_zoom_controls(file_path):
                success_count += 1
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
    
    print(f"\nCompleted! Successfully removed custom zoom controls from {success_count} out of {len(html_files)} files.")
    print("\nNote: The following zoom controls remain active:")
    print("- Native Leaflet zoom controls (top-left corner)")
    print("- Sidebar map controls (in static viewer)")
    print("- Enhanced new tab controls (bottom-right of new tabs)")
    print("- Keyboard shortcuts (Ctrl/Cmd + Plus/Minus/0)")

if __name__ == "__main__":
    main()