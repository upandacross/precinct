#!/usr/bin/env python3
"""Debug script to test user creation and identify tuple/dict issues."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import create_app
from models import db, User
import traceback

def test_user_creation():
    """Test user creation to identify the tuple error."""
    app = create_app()
    
    with app.app_context():
        print("Testing user creation...")
        
        try:
            # Test direct model creation
            print("\n1. Testing direct User model creation...")
            test_user = User(
                username='debug_test_user',
                email='debug@test.com',
                password='testpass123',
                is_admin=False,
                phone='555-1234',
                role='volunteer',
                precinct='TEST',
                state='NC',
                county='TEST',
                notes='Debug test user'
            )
            
            # Try to add to session
            db.session.add(test_user)
            print("✓ User object created successfully")
            
            # Try to commit
            db.session.commit()
            print("✓ User saved to database successfully")
            
            # Clean up
            db.session.delete(test_user)
            db.session.commit()
            print("✓ Test user cleaned up")
            
        except Exception as e:
            print(f"✗ Error in direct user creation: {e}")
            print(f"Exception type: {type(e)}")
            traceback.print_exc()
            db.session.rollback()
        
        # Test Flask-Admin form simulation
        print("\n2. Testing Flask-Admin form field access...")
        try:
            from main import UserModelView
            from flask_admin.form import BaseForm
            
            # Create a mock form-like object to test form handling
            class MockForm:
                def __init__(self):
                    self.password = MockField('testpass123')
                    
                def items(self):
                    return [('password', self.password)]
            
            class MockField:
                def __init__(self, data):
                    self.data = data
            
            form = MockForm()
            user_view = UserModelView(User, db.session)
            
            # Test the on_model_change method
            test_user2 = User(
                username='debug_test_user2',
                email='debug2@test.com',
                password='testpass123'
            )
            
            user_view.on_model_change(form, test_user2, True)
            print("✓ Flask-Admin on_model_change method works")
            
        except Exception as e:
            print(f"✗ Error in Flask-Admin simulation: {e}")
            print(f"Exception type: {type(e)}")
            traceback.print_exc()
        
        # Test form field configuration
        print("\n3. Testing Flask-Admin field configuration...")
        try:
            from main import UserModelView
            user_view = UserModelView(User, db.session)
            
            # Check if any configuration returns tuples instead of dicts
            print(f"form_columns type: {type(user_view.form_columns)}")
            print(f"form_columns value: {user_view.form_columns}")
            
            print(f"column_filters type: {type(user_view.column_filters)}")
            print(f"column_filters value: {user_view.column_filters}")
            
            print(f"form_excluded_columns type: {type(user_view.form_excluded_columns)}")
            print(f"form_excluded_columns value: {user_view.form_excluded_columns}")
            
            # Check if any of these are causing the tuple issue
            for attr_name in ['column_exclude_list', 'column_searchable_list', 'column_filters']:
                attr_value = getattr(user_view, attr_name, None)
                if attr_value:
                    print(f"{attr_name}: {type(attr_value)} = {attr_value}")
                    
        except Exception as e:
            print(f"✗ Error in configuration check: {e}")
            print(f"Exception type: {type(e)}")
            traceback.print_exc()

if __name__ == '__main__':
    test_user_creation()