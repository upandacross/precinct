#!/usr/bin/env python3
"""
Simple test script to see if there are import/runtime errors.
"""

print("Starting basic Flask test...")

try:
    print("Importing Flask components...")
    from flask import Flask
    print("✓ Flask imported successfully")
    
    from models import db, User, Map
    print("✓ Models imported successfully") 
    
    from config import get_config
    print("✓ Config imported successfully")
    
    from security import add_security_headers
    print("✓ Security module imported successfully")
    
    print("Testing Dash import...")
    try:
        from dash_analytics import create_dash_app
        print("✓ Dash analytics imported successfully")
        DASH_AVAILABLE = True
    except ImportError as e:
        print(f"⚠ Dash analytics import failed: {e}")
        DASH_AVAILABLE = False
    
    print("Creating Flask app...")
    from main import create_app
    app = create_app()
    print("✓ Flask app created successfully")
    
    print("Testing app context...")
    with app.app_context():
        print("✓ App context works")
        
        # Test database connection
        try:
            user_count = User.query.count()
            print(f"✓ Database connection works - found {user_count} users")
        except Exception as e:
            print(f"❌ Database error: {e}")
    
    print("\n🎉 All basic tests passed! Flask app should work.")
    
except Exception as e:
    print(f"❌ Error occurred: {e}")
    import traceback
    traceback.print_exc()