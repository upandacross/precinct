# Map Zoom Controls Enhancement

## Overview
This update adds comprehensive zoom functionality to all map interfaces in the precinct application, providing multiple ways for users to control map zoom levels across different viewing modes.

## Features Added

### 1. In-Map Zoom Controls (All Maps)
- **Location**: Top-right corner of each map (floating overlay)
- **Controls**:
  - ➕ **Zoom In** button (green)
  - ➖ **Zoom Out** button (red)
  - 🎯 **Reset Zoom** button (teal)
- **Styling**: Responsive design that adapts to mobile devices
- **Interaction**: Hover effects and smooth transitions

### 2. Sidebar Map Controls (Static Viewer)
- **Location**: Right sidebar in the static viewer interface
- **Features**:
  - "Map Controls" card with three zoom buttons
  - Keyboard shortcut instructions
  - Cross-frame communication with embedded maps
- **Integration**: Works seamlessly with iframe-embedded maps

### 3. Enhanced New Tab Controls
- **Location**: Bottom-right corner of new tab views
- **Features**:
  - Prominent zoom control panel with blue border
  - Larger, more accessible buttons
  - Enhanced visual feedback
- **Positioning**: Fixed position that doesn't interfere with map content

### 4. Keyboard Shortcuts (All Views)
- **Zoom In**: `Ctrl/Cmd + Plus` or `Ctrl/Cmd + =`
- **Zoom Out**: `Ctrl/Cmd + Minus`
- **Reset Zoom**: `Ctrl/Cmd + 0`
- **Accessibility**: Works across all browsers and platforms

### 5. Cross-Frame Communication
- **Purpose**: Allows parent window controls to communicate with iframe maps
- **Implementation**: Message passing between parent and child frames
- **Fallback**: Direct function calls when message passing fails

## Technical Implementation

### Files Modified
- **All HTML files** in `static_html/` directory (112 files)
- **Template**: `templates/static_viewer.html`
- **Backend**: `main.py` (view_file_new_tab function)

### Scripts Created
- `add_zoom_buttons.py` - Adds basic zoom functionality to all maps
- `add_message_listener.py` - Adds cross-frame communication support
- `add_newtab_zoom_controls.py` - Utility script for new tab enhancements
- `test_zoom_functionality.py` - Verification script

### CSS Classes Added
- `.custom-zoom-controls` - Main zoom control container
- `.zoom-btn` - Base zoom button styling
- `.zoom-in-btn`, `.zoom-out-btn`, `.zoom-reset-btn` - Specific button types
- `.new-tab-zoom-controls` - Enhanced controls for new tab view

### JavaScript Functions Added
- `zoomIn()` - Increases map zoom level by 1
- `zoomOut()` - Decreases map zoom level by 1
- `resetZoom()` - Resets map to fit original bounds
- Event listeners for keyboard shortcuts and cross-frame messages

## User Experience Improvements

### Accessibility
- Large, clearly labeled buttons
- Keyboard navigation support
- High contrast color scheme
- Tooltip text for all controls
- Mobile-responsive design

### Multiple Access Points
1. **Native Leaflet controls** (existing, top-left corner)
2. **Custom overlay controls** (top-right corner)
3. **Sidebar controls** (static viewer right panel)
4. **Enhanced new tab controls** (bottom-right corner)
5. **Keyboard shortcuts** (system-wide)

### Visual Feedback
- Hover effects on all buttons
- Smooth transitions and animations
- Color-coded buttons (green=zoom in, red=zoom out, teal=reset)
- Clear iconography and labels

## Browser Compatibility
- ✅ Chrome/Chromium
- ✅ Firefox
- ✅ Safari
- ✅ Edge
- ✅ Mobile browsers (iOS Safari, Chrome Mobile)

## Testing
Run `python test_zoom_functionality.py` to verify all components are properly installed.

## Future Enhancements
- Zoom level indicator
- Custom zoom level input
- Pan controls
- Map layer toggles
- Fullscreen zoom mode

## Notes
- All changes are backward compatible
- Existing Leaflet zoom controls remain functional
- No impact on map performance or loading times
- Mobile-optimized for touch devices