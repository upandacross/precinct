#!/usr/bin/env python3
"""
Fix Flask-Admin tuple issue by customizing form field creation.

The issue is that Flask-Admin is passing field flags as tuples instead of dictionaries
when creating form fields for unique constrained columns.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import create_app
from models import db, User
import traceback
from wtforms import StringField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, Optional

def test_custom_form_approach():
    """Test custom form field approach to fix the tuple issue."""
    app = create_app()
    
    with app.app_context():
        print("Testing custom form field approach...")
        
        try:
            # Let's create a custom form class for the UserModelView
            print("\n1. Creating custom form fields...")
            
            # Test if we can override form_args to fix the tuple issue
            from flask_admin.contrib.sqla import ModelView
            from flask_admin.form import Select2Field
            
            class FixedUserModelView(ModelView):
                """Fixed UserModelView with proper form field configuration."""
                
                # Exclude problematic fields from automatic generation
                form_excluded_columns = ['password_hash', 'created_at', 'last_login', 'id']
                
                # Specify form field order
                form_columns = ['username', 'email', 'password', 'phone', 'role', 'precinct', 'state', 'county', 'notes', 'is_admin', 'is_county', 'is_active']
                
                # Override form_args to prevent tuple issues
                form_args = {
                    'username': {
                        'validators': [DataRequired(), Length(min=4, max=80)],
                        'render_kw': {'placeholder': 'Enter username'}
                    },
                    'email': {
                        'validators': [DataRequired(), Email(), Length(max=120)],
                        'render_kw': {'placeholder': 'Enter email address'}
                    },
                    'password': {
                        'validators': [DataRequired(), Length(min=6, max=255)],
                        'render_kw': {'placeholder': 'Enter password'}
                    },
                    'phone': {
                        'validators': [Optional(), Length(max=20)],
                        'render_kw': {'placeholder': 'Phone number (optional)'}
                    },
                    'role': {
                        'validators': [Optional(), Length(max=100)],
                        'render_kw': {'placeholder': 'Role (optional)'}
                    },
                    'precinct': {
                        'validators': [Optional(), Length(max=100)],
                        'render_kw': {'placeholder': 'Precinct (optional)'}
                    },
                    'state': {
                        'validators': [Optional(), Length(max=50)],
                        'render_kw': {'placeholder': 'State (optional)'}
                    },
                    'county': {
                        'validators': [Optional(), Length(max=100)],
                        'render_kw': {'placeholder': 'County (optional)'}
                    },
                    'notes': {
                        'validators': [Optional()],
                        'render_kw': {'placeholder': 'Additional notes (optional)', 'rows': 3}
                    }
                }
                
                def on_model_change(self, form, model, is_created):
                    """Hash password when creating or updating user."""
                    if hasattr(form, 'password') and form.password.data:
                        model.set_password(form.password.data)
                
                def is_accessible(self):
                    """Require admin access."""
                    from flask_login import current_user
                    return current_user.is_authenticated and current_user.is_admin
                
                def inaccessible_callback(self, name, **kwargs):
                    """Redirect to login if not accessible."""
                    from flask import redirect, url_for
                    return redirect(url_for('login'))
            
            # Test creating the view
            user_view = FixedUserModelView(User, db.session, name='Users')
            print("✓ Custom UserModelView created successfully")
            
            # Test form creation
            print("\n2. Testing form creation with custom view...")
            try:
                # This should work without the tuple error
                form_class = user_view.get_create_form()
                print(f"✓ Form class created: {form_class}")
                
                # Test form instantiation
                form = form_class()
                print(f"✓ Form instantiated: {form}")
                
                print("\n3. Available form fields:")
                for field_name, field in form._fields.items():
                    print(f"  {field_name}: {type(field).__name__}")
                
                print("\n✓ Custom form approach works! This should fix the tuple issue.")
                
            except Exception as form_error:
                print(f"✗ Form creation still fails: {form_error}")
                print(f"Exception type: {type(form_error)}")
                traceback.print_exc()
            
        except Exception as e:
            print(f"✗ Error in custom form approach: {e}")
            traceback.print_exc()

if __name__ == '__main__':
    test_custom_form_approach()