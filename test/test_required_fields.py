#!/usr/bin/env python3
"""Test user creation with required phone and role fields."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import create_app
from models import db, User
import traceback

def test_user_creation_with_required_fields():
    """Test user creation with phone and role as required fields."""
    app = create_app()
    
    with app.app_context():
        with app.test_client() as client:
            print("Testing user creation with required phone and role...")
            
            try:
                # Login as admin
                admin_user = User.query.filter_by(is_admin=True).first()
                
                with client.session_transaction() as sess:
                    sess['_user_id'] = str(admin_user.id)
                    sess['_fresh'] = True
                
                # Get form with CSRF token
                response = client.get('/admin/user/new/')
                if response.status_code != 200:
                    print(f"✗ Form load failed: {response.status_code}")
                    return
                
                # Extract CSRF token from response
                html = response.get_data(as_text=True)
                import re
                csrf_match = re.search(r'name="csrf_token".*?value="([^"]+)"', html)
                if not csrf_match:
                    print("✗ No CSRF token found")
                    return
                
                csrf_token = csrf_match.group(1)
                print(f"✓ CSRF token: {csrf_token[:20]}...")
                
                # Count users before
                user_count_before = User.query.count()
                print(f"Users before: {user_count_before}")
                
                # Test form with all required fields
                timestamp = str(int(time.time()))
                form_data = {
                    'csrf_token': csrf_token,
                    'username': 'test_user_' + timestamp[-6:],
                    'email': f'test{timestamp[-6:]}@example.com',
                    'password': 'testpass123',
                    'phone': '555-1234',  # Required field
                    'role': 'volunteer',  # Required field
                    'precinct': 'TEST',
                    'state': 'NC',
                    'county': 'TEST',
                    'notes': 'Test user with required fields',
                    'is_admin': '',  # Unchecked
                    'is_county': '',  # Unchecked  
                    'is_active': 'y'  # Checked
                }
                
                print(f"Submitting form with data: {form_data}")
                
                response = client.post('/admin/user/new/', data=form_data, follow_redirects=False)
                print(f"Response status: {response.status_code}")
                print(f"Location: {response.headers.get('Location', 'None')}")
                
                # Count users after
                user_count_after = User.query.count()
                print(f"Users after: {user_count_after}")
                
                if user_count_after > user_count_before:
                    print("✅ User creation successful!")
                    
                    # Find and verify the new user
                    new_user = User.query.filter_by(username=form_data['username']).first()
                    if new_user:
                        print(f"✓ User created: {new_user.username}")
                        print(f"  Phone: {new_user.phone}")
                        print(f"  Role: {new_user.role}")
                        print(f"  Active: {new_user.is_active}")
                        
                        # Clean up
                        db.session.delete(new_user)
                        db.session.commit()
                        print("✓ Test user cleaned up")
                    else:
                        print("✗ User not found after creation")
                        
                else:
                    print("✗ User creation failed")
                    
                    # Check for validation errors
                    if response.status_code == 200:
                        response_html = response.get_data(as_text=True)
                        if 'error' in response_html.lower() or 'required' in response_html.lower():
                            print("Validation errors detected in response")
                            # Try to extract error messages
                            error_lines = [line.strip() for line in response_html.split('\n') 
                                         if 'error' in line.lower() or 'required' in line.lower()]
                            for error_line in error_lines[:5]:  # Show first 5 error lines
                                if error_line:
                                    print(f"  Error: {error_line[:100]}...")
                
            except Exception as e:
                print(f"✗ Error: {e}")
                traceback.print_exc()

if __name__ == '__main__':
    import time
    test_user_creation_with_required_fields()