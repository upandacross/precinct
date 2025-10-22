#!/usr/bin/env python3
"""Test Flask-Admin user creation with detailed form debugging."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import create_app
from models import db, User
import traceback

def test_user_creation_detailed():
    """Test Flask-Admin user creation with form debugging."""
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            print("Testing Flask-Admin user creation with debugging...")
            
            try:
                # Login as admin first
                admin_user = User.query.filter_by(is_admin=True).first()
                
                # Simulate login
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(admin_user.id)
                    sess['_fresh'] = True
                
                print("\n1. Getting create form...")
                response = client.get('/admin/user/new/')
                print(f"Create form status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"Form load failed: {response.get_data(as_text=True)[:500]}")
                    return
                
                print("✓ Form loads successfully")
                
                # Count users before creation
                user_count_before = User.query.count()
                print(f"Users before creation: {user_count_before}")
                
                print("\n2. Submitting form with test data...")
                
                # Test form submission with minimal required data first
                timestamp = str(int(time.time()))
                form_data = {
                    'username': 'debug_user_' + timestamp[-6:],  # Make unique
                    'email': f'debug{timestamp[-6:]}@test.com',  # Make unique
                    'password': 'testpass123',
                    'is_admin': 'n',  # Flask-Admin uses 'y'/'n' for boolean fields
                    'is_county': 'n',
                    'is_active': 'y'
                }
                
                print(f"Form data: {form_data}")
                
                response = client.post('/admin/user/new/', data=form_data, follow_redirects=False)
                print(f"Form submission status: {response.status_code}")
                print(f"Location header: {response.headers.get('Location', 'None')}")
                
                # Count users after creation attempt
                user_count_after = User.query.count()
                print(f"Users after creation: {user_count_after}")
                
                if user_count_after > user_count_before:
                    print("✓ User was created successfully!")
                    
                    # Find the new user
                    new_user = User.query.filter_by(username=form_data['username']).first()
                    if new_user:
                        print(f"✓ New user found: {new_user.username} (ID: {new_user.id})")
                        # Clean up
                        db.session.delete(new_user)
                        db.session.commit()
                        print("✓ Test user cleaned up")
                else:
                    print("✗ User was not created")
                    
                    # Check if there were any validation errors by examining response
                    if response.status_code == 302:
                        print("Form submitted successfully but redirected (might be validation errors)")
                    
                    # Try to follow redirects and see the actual page
                    response = client.post('/admin/user/new/', data=form_data, follow_redirects=True)
                    response_text = response.get_data(as_text=True)
                    
                    # Look for error messages in the response
                    if 'error' in response_text.lower() or 'invalid' in response_text.lower():
                        print("Found error indicators in response")
                        # Extract any error messages
                        lines = response_text.split('\n')
                        for i, line in enumerate(lines):
                            if 'error' in line.lower() or 'invalid' in line.lower():
                                print(f"Error line {i}: {line.strip()}")
                                # Print some context
                                for j in range(max(0, i-2), min(len(lines), i+3)):
                                    if j != i:
                                        print(f"Context {j}: {lines[j].strip()}")
                                break
                    
                    # Check for specific Flask-Admin form error patterns
                    if 'field-error' in response_text or 'has-error' in response_text:
                        print("Flask-Admin form validation errors detected")
                
            except Exception as e:
                print(f"✗ Error during test: {e}")
                traceback.print_exc()

if __name__ == '__main__':
    import time
    test_user_creation_detailed()