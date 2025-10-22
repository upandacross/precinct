#!/usr/bin/env python3
"""
Analytics Dashboard Diagnostic
=============================

This script checks the analytics dashboard data generation to identify
any invalid values or issues with the graphs.
"""

import os
import sys
sys.path.append('.')

from sqlalchemy import create_engine, text
from dotenv import load_dotenv
from config import Config
from models import User, db
from flask import Flask

def diagnose_analytics_data():
    """Diagnose potential issues with analytics data generation."""
    
    # Create minimal Flask app for database context
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    db.init_app(app)
    
    print("🔍 ANALYTICS DASHBOARD DIAGNOSTIC")
    print("=" * 50)
    
    with app.app_context():
        try:
            # Import analytics function
            from dash_analytics import get_analytics_data
            
            # Get analytics data for a test user (user ID 1)
            analytics_data = get_analytics_data(app, user_id=1)
            
            print("📊 ANALYTICS DATA STRUCTURE:")
            for key, value in analytics_data.items():
                if key == 'database_error' and value:
                    print(f"   ❌ {key}: {value}")
                elif isinstance(value, dict):
                    print(f"   📁 {key}:")
                    for subkey, subvalue in value.items():
                        if subvalue is None:
                            print(f"      ⚠️  {subkey}: None")
                        elif isinstance(subvalue, (int, float)):
                            if str(subvalue) in ['inf', '-inf', 'nan']:
                                print(f"      ❌ {subkey}: {subvalue} (INVALID)")
                            else:
                                print(f"      ✅ {subkey}: {subvalue}")
                        else:
                            print(f"      📄 {subkey}: {type(subvalue).__name__}")
                elif isinstance(value, list):
                    print(f"   📋 {key}: {len(value)} items")
                    if value and any(x is None or str(x) in ['inf', '-inf', 'nan'] for x in value):
                        print(f"      ⚠️  Contains invalid values!")
                else:
                    print(f"   📄 {key}: {value}")
            
            # Check specific charts that might have issues
            print(f"\n🎨 CHART DATA VALIDATION:")
            
            # User distribution chart
            if 'user_stats' in analytics_data:
                stats = analytics_data['user_stats']
                total = sum([stats.get('regular', 0), stats.get('admins', 0), 
                           stats.get('county', 0), stats.get('inactive', 0)])
                print(f"   👥 User Distribution: {total} total users")
                if total == 0:
                    print(f"      ⚠️  Zero total users might cause chart issues")
            
            # Password strength chart
            if 'password_strength' in analytics_data:
                pwd_data = analytics_data['password_strength']
                if isinstance(pwd_data, dict) and 'Count' in pwd_data:
                    counts = pwd_data['Count']
                    if any(x is None or str(x) in ['inf', '-inf', 'nan'] for x in counts):
                        print(f"   🔐 Password Strength: Contains invalid values!")
                    else:
                        print(f"   🔐 Password Strength: {sum(counts)} total entries")
            
            # Monthly signups chart
            if 'monthly_signups' in analytics_data:
                monthly_data = analytics_data['monthly_signups']
                if isinstance(monthly_data, dict) and 'Signups' in monthly_data:
                    signups = monthly_data['Signups']
                    if any(x is None or str(x) in ['inf', '-inf', 'nan'] for x in signups):
                        print(f"   📅 Monthly Signups: Contains invalid values!")
                    else:
                        print(f"   📅 Monthly Signups: {sum(signups)} total signups")
            
            # Check for database errors
            if analytics_data.get('database_error'):
                print(f"\n❌ DATABASE ERROR DETECTED:")
                print(f"   {analytics_data['database_error']}")
                print(f"   This might cause charts to show placeholder or error data.")
            
        except Exception as e:
            print(f"❌ ERROR RUNNING DIAGNOSTIC: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    diagnose_analytics_data()