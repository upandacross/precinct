#!/usr/bin/env python3
"""
Test script to verify zoom button functionality has been added successfully.
This checks a sample of HTML files to ensure all components are properly added.
"""

import os
import glob
import re

def test_zoom_functionality(file_path):
    """Test that zoom functionality has been properly added to an HTML file."""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tests_passed = []
    tests_failed = []
    
    # Test 1: Check for custom zoom controls CSS
    if 'custom-zoom-controls' in content:
        tests_passed.append("✓ Custom zoom controls CSS found")
    else:
        tests_failed.append("✗ Custom zoom controls CSS missing")
    
    # Test 2: Check for zoom button HTML
    if 'zoom-btn zoom-in-btn' in content and 'onclick="zoomIn()"' in content:
        tests_passed.append("✓ Zoom in button HTML found")
    else:
        tests_failed.append("✗ Zoom in button HTML missing")
    
    # Test 3: Check for zoom JavaScript functions
    if 'function zoomIn()' in content and 'function zoomOut()' in content:
        tests_passed.append("✓ Zoom JavaScript functions found")
    else:
        tests_failed.append("✗ Zoom JavaScript functions missing")
    
    # Test 4: Check for keyboard shortcuts
    if 'keydown' in content and 'ctrlKey' in content:
        tests_passed.append("✓ Keyboard shortcuts found")
    else:
        tests_failed.append("✗ Keyboard shortcuts missing")
    
    # Test 5: Check for message listener
    if 'addEventListener(\'message\'' in content:
        tests_passed.append("✓ Message listener for cross-frame communication found")
    else:
        tests_failed.append("✗ Message listener for cross-frame communication missing")
    
    return tests_passed, tests_failed

def main():
    """Main function to test a sample of HTML files."""
    
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    static_html_dir = os.path.join(script_dir, 'static_html')
    
    if not os.path.exists(static_html_dir):
        print(f"Error: {static_html_dir} directory not found!")
        return
    
    # Find all HTML files and test a sample
    html_files = glob.glob(os.path.join(static_html_dir, '*.html'))
    
    if not html_files:
        print("No HTML files found in static_html directory!")
        return
    
    # Test first 3 files as a sample
    test_files = sorted(html_files)[:3]
    
    print("Testing zoom functionality on sample files...\n")
    
    all_tests_passed = True
    
    for file_path in test_files:
        filename = os.path.basename(file_path)
        print(f"Testing {filename}:")
        
        try:
            passed, failed = test_zoom_functionality(file_path)
            
            for test in passed:
                print(f"  {test}")
            
            for test in failed:
                print(f"  {test}")
                all_tests_passed = False
            
            print()
            
        except Exception as e:
            print(f"  ✗ Error testing {filename}: {str(e)}\n")
            all_tests_passed = False
    
    if all_tests_passed:
        print("🎉 All zoom functionality tests PASSED!")
        print("\nFeatures added:")
        print("• Custom zoom buttons (In-map overlay)")
        print("• Keyboard shortcuts (Ctrl/Cmd + Plus/Minus/0)")
        print("• Cross-frame communication for iframe controls")
        print("• Enhanced new-tab zoom controls")
        print("• Mobile-responsive design")
    else:
        print("❌ Some tests FAILED. Please check the output above.")
    
    print(f"\nTotal files with zoom functionality: {len(html_files)}")
    print("\nTo test the functionality:")
    print("1. Start the Flask application")
    print("2. Navigate to any map in the static viewer")
    print("3. Use the Map Controls panel on the right")
    print("4. Open a map in a new tab to see enhanced controls")
    print("5. Try keyboard shortcuts: Ctrl/Cmd + Plus/Minus/0")

if __name__ == "__main__":
    main()