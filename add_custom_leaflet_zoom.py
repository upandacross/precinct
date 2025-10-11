#!/usr/bin/env python3
"""
Script to add custom zoom controls to the upper left corner of all static HTML map files.
This replaces the disabled Leaflet zoom controls with our custom controls.
"""

import os
import glob
import re

def add_custom_zoom_controls(file_path):
    """Add custom zoom controls to upper left corner of a static HTML file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check if custom zoom controls are already added
    if 'leaflet-replacement-zoom-controls' in content:
        print(f"Custom zoom controls already exist in {file_path}")
        return False
    
    # Find the map ID using regex
    map_id_match = re.search(r'var (map_[a-f0-9]+) = L\.map\(', content)
    if not map_id_match:
        print(f"Could not find map ID in {file_path}")
        return False
    
    map_id = map_id_match.group(1)
    
    # CSS for custom zoom controls in upper left
    zoom_css = """
    <style>
        .leaflet-replacement-zoom-controls {
            position: absolute;
            top: 20px;
            left: 20px;
            z-index: 1000;
            display: flex;
            flex-direction: column;
            gap: 2px;
        }
        
        .leaflet-zoom-btn {
            width: 34px;
            height: 34px;
            background: white;
            border: 2px solid rgba(0,0,0,0.2);
            border-radius: 4px;
            display: flex;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            font-size: 18px;
            font-weight: bold;
            box-shadow: 0 1px 5px rgba(0,0,0,0.2);
            user-select: none;
            transition: all 0.1s ease;
            text-decoration: none;
            color: #333;
        }
        
        .leaflet-zoom-btn:hover {
            background: #f4f4f4;
            border-color: rgba(0,0,0,0.4);
        }
        
        .leaflet-zoom-btn:active {
            background: #e6e6e6;
        }
        
        .leaflet-zoom-btn.leaflet-disabled {
            background: #f9f9f9;
            color: #bbb;
            cursor: default;
        }
        
        .leaflet-zoom-btn.leaflet-disabled:hover {
            background: #f9f9f9;
            border-color: rgba(0,0,0,0.2);
        }
        
        @media (max-width: 768px) {
            .leaflet-replacement-zoom-controls {
                top: 10px;
                left: 10px;
            }
            
            .leaflet-zoom-btn {
                width: 30px;
                height: 30px;
                font-size: 16px;
            }
        }
    </style>"""
    
    # HTML for custom zoom controls
    zoom_html = f"""
    <!-- Custom Leaflet Replacement Zoom Controls -->
    <div class="leaflet-replacement-zoom-controls">
        <div class="leaflet-zoom-btn" onclick="customZoomIn()" title="Zoom in">+</div>
        <div class="leaflet-zoom-btn" onclick="customZoomOut()" title="Zoom out">−</div>
    </div>"""
    
    # JavaScript for zoom functionality
    zoom_js = f"""
    <script>
        // Custom zoom functions to replace Leaflet controls
        function customZoomIn() {{
            if (typeof {map_id} !== 'undefined') {{
                {map_id}.zoomIn(1);
                updateZoomButtonStates();
            }}
        }}
        
        function customZoomOut() {{
            if (typeof {map_id} !== 'undefined') {{
                {map_id}.zoomOut(1);
                updateZoomButtonStates();
            }}
        }}
        
        function updateZoomButtonStates() {{
            if (typeof {map_id} !== 'undefined') {{
                const currentZoom = {map_id}.getZoom();
                const minZoom = {map_id}.getMinZoom();
                const maxZoom = {map_id}.getMaxZoom();
                
                const zoomInBtn = document.querySelector('.leaflet-replacement-zoom-controls .leaflet-zoom-btn:first-child');
                const zoomOutBtn = document.querySelector('.leaflet-replacement-zoom-controls .leaflet-zoom-btn:last-child');
                
                // Disable/enable zoom in button
                if (currentZoom >= maxZoom) {{
                    zoomInBtn.classList.add('leaflet-disabled');
                }} else {{
                    zoomInBtn.classList.remove('leaflet-disabled');
                }}
                
                // Disable/enable zoom out button
                if (currentZoom <= minZoom) {{
                    zoomOutBtn.classList.add('leaflet-disabled');
                }} else {{
                    zoomOutBtn.classList.remove('leaflet-disabled');
                }}
            }}
        }}
        
        // Initialize button states when map is ready
        if (typeof {map_id} !== 'undefined') {{
            {map_id}.on('zoomend', updateZoomButtonStates);
            {map_id}.whenReady(function() {{
                updateZoomButtonStates();
            }});
        }}
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
    
    print(f"Added custom zoom controls to {file_path}")
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
            if add_custom_zoom_controls(file_path):
                success_count += 1
        except Exception as e:
            print(f"Error processing {filename}: {str(e)}")
    
    print(f"\nCompleted! Successfully added custom zoom controls to {success_count} out of {len(html_files)} files.")
    print("\nFeatures added:")
    print("- Custom zoom controls in upper left corner (replacing Leaflet controls)")
    print("- Leaflet-style appearance and behavior")
    print("- Automatic disable/enable based on zoom limits")
    print("- Mobile-responsive design")
    print("- Integration with existing zoom functions and keyboard shortcuts")

if __name__ == "__main__":
    main()