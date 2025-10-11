#!/usr/bin/env python3
"""
Script to add message listener support to all static HTML map files.
This allows zoom controls from the parent window to work with the maps.
"""

import os
import glob
import re

def add_message_listener_to_html(file_path):
    """Add message listener for zoom controls to a static HTML file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if message listener is already added
    if 'addEventListener(\'message\'' in content:
        print(f"Message listener already exists in {file_path}")
        return False
    
    # Message listener JavaScript
    message_listener_js = """
        
        // Listen for zoom commands from parent window
        window.addEventListener('message', function(event) {
            if (event.data && event.data.action) {
                switch(event.data.action) {
                    case 'zoomIn':
                        zoomIn();
                        break;
                    case 'zoomOut':
                        zoomOut();
                        break;
                    case 'resetZoom':
                        resetZoom();
                        break;
                }
            }
        });"""
    
    # Find the keydown event listener pattern 
    zoom_js_pattern = r'(document\.addEventListener\(\'keydown\',.*?}\s*}\);)'
    
    if re.search(zoom_js_pattern, content, re.DOTALL):
        # Insert after the existing keydown listener
        content = re.sub(zoom_js_pattern, r'\1' + message_listener_js, content, flags=re.DOTALL)
        print(f"Added message listener to {file_path}")
        
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    else:
        print(f"Could not find keydown listener in {file_path}")
        return False

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
            if add_message_listener_to_html(file_path):
                success_count += 1
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
    
    print(f"\nCompleted! Successfully modified {success_count} out of {len(html_files)} files.")

if __name__ == "__main__":
    main()