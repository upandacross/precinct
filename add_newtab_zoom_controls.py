#!/usr/bin/env python3
"""
Script to add enhanced new tab zoom controls to all static HTML map files.
This adds additional zoom controls specifically for the new tab view mode.
"""

import os
import glob
import re

def add_new_tab_zoom_controls(file_path):
    """Add enhanced zoom controls for new tab view to a static HTML file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if enhanced zoom controls are already added
    if 'new-tab-zoom-controls' in content:
        print(f"Enhanced zoom controls already exist in {file_path}")
        return False
    
    # Enhanced zoom controls for new tab view
    enhanced_zoom_controls = '''
    <!-- Enhanced Zoom Controls for New Tab -->
    <div class="new-tab-zoom-controls" style="position: fixed; bottom: 20px; right: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 8px;">
        <div style="background: rgba(255,255,255,0.95); padding: 12px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); border: 2px solid #007bff;">
            <div style="text-align: center; margin-bottom: 8px; font-weight: bold; color: #007bff; font-size: 12px;">ZOOM CONTROLS</div>
            <div style="display: flex; flex-direction: column; gap: 4px;">
                <button onclick="zoomIn()" style="width: 60px; height: 35px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold; transition: background 0.2s;" onmouseover="this.style.backgroundColor='#218838'" onmouseout="this.style.backgroundColor='#28a745'" title="Zoom In (Ctrl/Cmd + Plus)">+</button>
                <button onclick="zoomOut()" style="width: 60px; height: 35px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold; transition: background 0.2s;" onmouseover="this.style.backgroundColor='#c82333'" onmouseout="this.style.backgroundColor='#dc3545'" title="Zoom Out (Ctrl/Cmd + Minus)">−</button>
                <button onclick="resetZoom()" style="width: 60px; height: 30px; background: #17a2b8; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 10px; font-weight: bold; transition: background 0.2s;" onmouseover="this.style.backgroundColor='#138496'" onmouseout="this.style.backgroundColor='#17a2b8'" title="Reset Zoom (Ctrl/Cmd + 0)">Reset</button>
            </div>
        </div>
    </div>'''
    
    # Find the close window button and add zoom controls after it
    close_button_pattern = r'(<div style="position: fixed; top: 10px; right: 10px;[^>]*>.*?</script>)'
    
    if re.search(close_button_pattern, content, re.DOTALL):
        # Insert enhanced zoom controls after the close button
        content = re.sub(close_button_pattern, r'\1' + enhanced_zoom_controls, content, flags=re.DOTALL)
        print(f"Added enhanced zoom controls to {file_path}")
        
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    else:
        print(f"Could not find close button in {file_path} - it may not have been processed for new tab view yet")
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
            if add_new_tab_zoom_controls(file_path):
                success_count += 1
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
    
    print(f"\nCompleted! Successfully modified {success_count} out of {len(html_files)} files.")
    print("Note: Files without close buttons haven't been processed for new tab view yet.")
    print("The enhanced zoom controls will be added when users open files in new tabs.")

if __name__ == "__main__":
    main()