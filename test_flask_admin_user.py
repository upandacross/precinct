#!/usr/bin/env python3
"""Test Flask-Admin user creation by simulating web request."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import create_app
from models import db, User
import traceback
from flask import request

def test_flask_admin_user_creation():
    """Test Flask-Admin user creation workflow."""
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            print("Testing Flask-Admin user creation...")
            
            try:
                # Login as admin first (assuming we have an admin user)
                print("\n1. Creating admin user for testing...")
                admin_user = User.query.filter_by(is_admin=True).first()
                if not admin_user:
                    admin_user = User(
                        username='test_admin',
                        email='admin@test.com',
                        password='adminpass123',
                        is_admin=True
                    )
                    db.session.add(admin_user)
                    db.session.commit()
                    print("✓ Admin user created")
                else:
                    print("✓ Admin user already exists")
                
                # Simulate login
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(admin_user.id)
                    sess['_fresh'] = True
                
                print("\n2. Testing Flask-Admin create user form...")
                
                # Get the create user form
                response = client.get('/admin/user/new/')
                print(f"Create form response status: {response.status_code}")
                
                if response.status_code == 200:
                    print("✓ Admin create form loads successfully")
                    
                    # Test form submission
                    form_data = {
                        'username': 'test_new_user',
                        'email': 'newuser@test.com',
                        'password': 'newpass123',
                        'phone': '555-9999',
                        'role': 'volunteer',
                        'precinct': 'TEST',
                        'state': 'NC',
                        'county': 'TEST',
                        'notes': 'Test user via Flask-Admin',
                        'is_admin': False,
                        'is_county': False,
                        'is_active': True
                    }
                    
                    response = client.post('/admin/user/new/', data=form_data, follow_redirects=True)
                    print(f"Form submission response status: {response.status_code}")
                    
                    if response.status_code == 200:
                        # Check if user was created
                        new_user = User.query.filter_by(username='test_new_user').first()
                        if new_user:
                            print("✓ User created successfully via Flask-Admin")
                            # Clean up
                            db.session.delete(new_user)
                            db.session.commit()
                            print("✓ Test user cleaned up")
                        else:
                            print("✗ User was not created - checking response content")
                            print(f"Response content: {response.get_data(as_text=True)[:500]}...")
                    else:
                        print(f"✗ Form submission failed with status {response.status_code}")
                        print(f"Response content: {response.get_data(as_text=True)[:500]}...")
                
                else:
                    print(f"✗ Admin create form failed to load: {response.status_code}")
                    print(f"Response content: {response.get_data(as_text=True)[:200]}...")
                
            except Exception as e:
                print(f"✗ Error during Flask-Admin test: {e}")
                print(f"Exception type: {type(e)}")
                traceback.print_exc()
                db.session.rollback()

if __name__ == '__main__':
    test_flask_admin_user_creation()