#!/usr/bin/env python3
"""Test user creation with detailed validation checking."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import create_app, CustomUserForm
from models import db, User
import traceback

def test_custom_form_validation():
    """Test the custom form validation and user creation."""
    app = create_app()
    
    with app.app_context():
        print("Testing custom form validation...")
        
        try:
            # Test direct form validation
            print("\n1. Testing form validation...")
            
            form_data = {
                'username': 'test_form_user',
                'email': 'testform@test.com',
                'password': 'testpass123',
                'phone': '555-8888',
                'role': 'volunteer',
                'precinct': 'TEST',
                'state': 'NC',
                'county': 'TEST',
                'notes': 'Test user via custom form',
                'is_admin': False,
                'is_county': False,
                'is_active': True
            }
            
            # Create form instance
            form = CustomUserForm(data=form_data)
            
            print(f"Form validation result: {form.validate()}")
            
            if form.errors:
                print("Form validation errors:")
                for field, errors in form.errors.items():
                    print(f"  {field}: {errors}")
            else:
                print("✓ Form validates successfully")
                
                # Test user creation with form data
                print("\n2. Testing user creation with form data...")
                
                user = User(
                    username=form.username.data,
                    email=form.email.data,
                    password=form.password.data,
                    phone=form.phone.data,
                    role=form.role.data,
                    precinct=form.precinct.data,
                    state=form.state.data,
                    county=form.county.data,
                    notes=form.notes.data,
                    is_admin=form.is_admin.data,
                    is_county=form.is_county.data,
                    is_active=form.is_active.data
                )
                
                # Check for existing user with same username
                existing_user = User.query.filter_by(username=form.username.data).first()
                if existing_user:
                    print(f"Deleting existing test user: {existing_user.username}")
                    db.session.delete(existing_user)
                    db.session.commit()
                
                db.session.add(user)
                db.session.commit()
                
                print(f"✓ User created successfully: {user.username}")
                
                # Verify the user exists
                created_user = User.query.filter_by(username=form.username.data).first()
                if created_user:
                    print(f"✓ User verified in database: {created_user.username}")
                    print(f"  Email: {created_user.email}")
                    print(f"  Password hash exists: {bool(created_user.password_hash)}")
                    print(f"  Is active: {created_user.is_active}")
                    
                    # Clean up
                    db.session.delete(created_user)
                    db.session.commit()
                    print("✓ Test user cleaned up")
                else:
                    print("✗ User not found in database after creation")
            
        except Exception as e:
            print(f"✗ Error in form validation test: {e}")
            traceback.print_exc()
            db.session.rollback()

if __name__ == '__main__':
    test_custom_form_validation()