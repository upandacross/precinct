#!/usr/bin/env python3
"""Investigate Flask-Admin form field creation to find tuple issue."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import create_app, UserModelView
from models import db, User
import traceback

def investigate_form_creation():
    """Investigate Flask-Admin form creation process."""
    app = create_app()
    
    with app.app_context():
        print("Investigating Flask-Admin form creation...")
        
        try:
            # Create UserModelView instance
            user_view = UserModelView(User, db.session)
            
            print("\n1. Checking model columns...")
            for column_name in User.__table__.columns.keys():
                column = User.__table__.columns[column_name]
                print(f"Column: {column_name}")
                print(f"  Type: {column.type}")
                print(f"  Nullable: {column.nullable}")
                print(f"  Unique: {column.unique}")
                print(f"  Default: {column.default}")
                
                # Check for any tuple-like arguments
                if hasattr(column, 'kwargs'):
                    print(f"  kwargs: {column.kwargs}")
                print()
            
            print("\n2. Checking Flask-Admin form configuration...")
            print(f"form_columns: {user_view.form_columns}")
            print(f"form_excluded_columns: {user_view.form_excluded_columns}")
            
            # Try to manually create form class
            print("\n3. Attempting form class creation...")
            try:
                form_class = user_view._get_form_class()
                print(f"✓ Form class created: {form_class}")
                
                # Try to instantiate the form
                print("\n4. Attempting form instantiation...")
                form = form_class()
                print(f"✓ Form instantiated: {form}")
                
            except Exception as form_error:
                print(f"✗ Form creation error: {form_error}")
                print(f"Exception type: {type(form_error)}")
                traceback.print_exc()
                
                # Let's dig deeper into the form field creation
                print("\n5. Investigating individual field creation...")
                
                # Get the form fields from the model
                try:
                    from flask_admin.contrib.sqla.fields import get_form
                    from flask_admin.form import get_form_opts
                    
                    # Check if there are any problematic field configurations
                    form_opts = get_form_opts(User, user_view.form_columns, user_view.form_excluded_columns)
                    print(f"Form opts: {form_opts}")
                    
                except Exception as field_error:
                    print(f"✗ Field investigation error: {field_error}")
                    traceback.print_exc()
        
        except Exception as e:
            print(f"✗ Overall error: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    investigate_form_creation()