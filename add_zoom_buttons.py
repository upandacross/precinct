#!/usr/bin/env python3
"""
Script to add custom zoom buttons to all static HTML map files.
This adds additional zoom controls that are more prominent and accessible.
"""

import os
import glob
import re

def add_zoom_buttons_to_html(file_path):
    """Add custom zoom buttons to a static HTML file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if zoom buttons are already added
    if 'custom-zoom-controls' in content:
        print(f"Zoom buttons already exist in {file_path}")
        return False
    
    # Find the map ID using regex
    map_id_match = re.search(r'var (map_[a-f0-9]+) = L\.map\(', content)
    if not map_id_match:
        print(f"Could not find map ID in {file_path}")
        return False
    
    map_id = map_id_match.group(1)
    
    # CSS for zoom buttons
    zoom_css = """
    <style>
        .custom-zoom-controls {
            position: absolute;
            top: 20px;
            right: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 5px;
        }
        
        .zoom-btn {
            width: 40px;
            height: 40px;
            background: white;
            border: 2px solid #ccc;
            border-radius: 6px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 20px;
            font-weight: bold;
            box-shadow: 0 2px 5px rgba(0,0,0,0.2);
            user-select: none;
            transition: all 0.2s ease;
        }
        
        .zoom-btn:hover {
            background: #f0f0f0;
            border-color: #999;
            transform: translateY(-1px);
            box-shadow: 0 3px 8px rgba(0,0,0,0.3);
        }
        
        .zoom-btn:active {
            transform: translateY(0px);
            box-shadow: 0 1px 3px rgba(0,0,0,0.2);
        }
        
        .zoom-in-btn {
            color: #2c7fb8;
        }
        
        .zoom-out-btn {
            color: #d94801;
        }
        
        .zoom-reset-btn {
            width: 40px;
            height: 30px;
            font-size: 12px;
            color: #41ab5d;
        }
        
        @media (max-width: 768px) {
            .custom-zoom-controls {
                top: 10px;
                right: 10px;
            }
            
            .zoom-btn {
                width: 35px;
                height: 35px;
                font-size: 18px;
            }
            
            .zoom-reset-btn {
                width: 35px;
                height: 25px;
                font-size: 10px;
            }
        }
    </style>"""
    
    # HTML for zoom buttons
    zoom_html = f"""
    <!-- Custom Zoom Controls -->
    <div class="custom-zoom-controls">
        <div class="zoom-btn zoom-in-btn" onclick="zoomIn()" title="Zoom In">+</div>
        <div class="zoom-btn zoom-out-btn" onclick="zoomOut()" title="Zoom Out">−</div>
        <div class="zoom-btn zoom-reset-btn" onclick="resetZoom()" title="Reset Zoom">Reset</div>
    </div>"""
    
    # JavaScript for zoom functionality
    zoom_js = f"""
    <script>
        // Custom zoom functions
        function zoomIn() {{
            if (typeof {map_id} !== 'undefined') {{
                {map_id}.zoomIn(1);
            }}
        }}
        
        function zoomOut() {{
            if (typeof {map_id} !== 'undefined') {{
                {map_id}.zoomOut(1);
            }}
        }}
        
        function resetZoom() {{
            if (typeof {map_id} !== 'undefined') {{
                // Get the original bounds from the fitBounds call
                const bounds = {map_id}.getBounds();
                {map_id}.fitBounds(bounds);
            }}
        }}
        
        // Keyboard shortcuts for zoom
        document.addEventListener('keydown', function(e) {{
            if (e.ctrlKey || e.metaKey) {{
                if (e.key === '=' || e.key === '+') {{
                    e.preventDefault();
                    zoomIn();
                }} else if (e.key === '-') {{
                    e.preventDefault();
                    zoomOut();
                }} else if (e.key === '0') {{
                    e.preventDefault();
                    resetZoom();
                }}
            }}
        }});
    </script>"""
    
    # Insert CSS before the closing </head> tag
    content = content.replace('</head>', zoom_css + '\n</head>')
    
    # Insert HTML before the map div
    map_div_pattern = r'(<div class="folium-map"[^>]*>)'
    content = re.sub(map_div_pattern, zoom_html + r'\n    \1', content)
    
    # Insert JavaScript before the closing </html> tag
    content = content.replace('</html>', zoom_js + '\n</html>')
    
    # Write the modified content back to the file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"Added zoom buttons to {file_path}")
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
            if add_zoom_buttons_to_html(file_path):
                success_count += 1
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
    
    print(f"\nCompleted! Successfully modified {success_count} out of {len(html_files)} files.")

if __name__ == "__main__":
    main()