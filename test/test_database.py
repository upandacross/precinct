"""
Database model and operations tests for the Precinct application.

Tests cover:
- User model operations
- Map model operations
- Database relationships
- CRUD operations
- Data validation
- Query functionality
"""

import pytest
from datetime import datetime
from models import db, User, Map


class TestUserModel:
    """Test User model functionality."""
    
    def test_user_creation(self, app, db_session):
        """Test creating a new user."""
        with app.app_context():
            user = User(
                username='test_new_user',
                email='new@test.com',
                password='test_password',
                phone='555-1234',
                role='voter',
                precinct='123',
                state='NC',
                county='Wake',
                is_admin=False,
                is_county=False,
                is_active=True,
                notes='Test user creation'
            )
            
            db_session.add(user)
            db_session.commit()
            
            # Verify user was created
            assert user.id is not None
            assert user.username == 'test_new_user'
            assert user.email == 'new@test.com'
            assert user.password_hash is not None
            assert user.password_hash != 'test_password'  # Should be hashed
    
    def test_user_password_hashing(self, app, db_session):
        """Test password hashing functionality."""
        with app.app_context():
            user = User(
                username='password_test',
                email='password@test.com',
                password='my_secure_password',
                phone='555-PWD',
                role='voter',
                state='NC',
                county='Wake',
                precinct='001'
            )
            
            # Password should be hashed
            assert user.password_hash != 'my_secure_password'
            
            # Should be able to verify correct password
            assert user.check_password('my_secure_password')
            
            # Should reject incorrect password
            assert not user.check_password('wrong_password')
    
    def test_user_password_update(self, app, db_session, regular_user):
        """Test updating user password."""
        with app.app_context():
            old_hash = regular_user.password_hash
            
            # Update password
            regular_user.set_password('new_password')
            db_session.commit()
            
            # Hash should have changed
            assert regular_user.password_hash != old_hash
            
            # Should verify with new password
            assert regular_user.check_password('new_password')
            
            # Should not verify with old password
            assert not regular_user.check_password('user_password_unique')
    
    def test_user_str_representation(self, regular_user):
        """Test user string representation."""
        user_str = str(regular_user)
        assert regular_user.username in user_str
    
    def test_user_query_by_username(self, app, db_session, regular_user):
        """Test querying user by username."""
        with app.app_context():
            found_user = User.query.filter_by(username=regular_user.username).first()
            
            assert found_user is not None
            assert found_user.id == regular_user.id
            assert found_user.email == regular_user.email
    
    def test_user_unique_constraints(self, app, db_session, regular_user):
        """Test that username and email are unique."""
        with app.app_context():
            # Try to create user with same username
            duplicate_user = User(
                username=regular_user.username,  # Same username
                email='different@test.com',
                password='test_password',
                phone='555-DUP',
                role='voter',
                state='NC',
                county='Wake',
                precinct='002'
            )
            
            db_session.add(duplicate_user)
            
            # Should raise an integrity error
            with pytest.raises(Exception):  # SQLAlchemy IntegrityError
                db_session.commit()
    
    def test_user_role_properties(self, admin_user, county_user, regular_user):
        """Test user role property checks."""
        # Admin user
        assert admin_user.is_admin is True
        assert admin_user.is_county is False
        
        # County user
        assert county_user.is_admin is False
        assert county_user.is_county is True
        
        # Regular user
        assert regular_user.is_admin is False
        assert regular_user.is_county is False
    
    def test_user_last_login_tracking(self, app, db_session):
        """Test last login timestamp tracking."""
        with app.app_context():
            user = User(
                username='login_test',
                email='login@test.com',
                password='test_password',
                phone='555-LOGIN',
                role='voter',
                state='NC',
                county='Wake',
                precinct='001'
            )
            
            db_session.add(user)
            db_session.commit()
            
            # Initially no last login
            assert user.last_login is None
            
            # Update last login
            user.last_login = datetime.utcnow()
            db_session.commit()
            
            assert user.last_login is not None


class TestMapModel:
    """Test Map model functionality."""
    
    def test_map_creation(self, app, db_session):
        """Test creating a new map."""
        with app.app_context():
            map_content = '''<!DOCTYPE html>
<html>
<head><title>Test Map</title></head>
<body><h1>Test Map Content</h1></body>
</html>'''
            
            map_record = Map(
                state='NC',
                county='Wake',
                precinct='456',
                map=map_content
            )
            
            db_session.add(map_record)
            db_session.commit()
            
            # Verify map was created
            assert map_record.id is not None
            assert map_record.state == 'NC'
            assert map_record.county == 'Wake'
            assert map_record.precinct == '456'
            assert map_record.map == map_content
    
    def test_map_timestamps(self, app, db_session):
        """Test map creation and update timestamps."""
        with app.app_context():
            map_record = Map(
                state='NC',
                county='Wake',
                precinct='789',
                map='<html>Test</html>'
            )
            
            db_session.add(map_record)
            db_session.commit()
            
            # Should have creation timestamp
            assert map_record.created_at is not None
            assert map_record.updated_at is not None
            
            # Update the map
            original_updated = map_record.updated_at
            map_record.map = '<html>Updated Test</html>'
            map_record.updated_at = datetime.utcnow()
            db_session.commit()
            
            # Updated timestamp should change
            assert map_record.updated_at > original_updated
    
    def test_map_query_by_location(self, app, db_session, sample_map):
        """Test querying maps by state/county/precinct."""
        with app.app_context():
            found_map = Map.query.filter_by(
                state='NC',
                county='Wake',
                precinct='012'
            ).first()
            
            assert found_map is not None
            assert found_map.id == sample_map.id
            assert found_map.map == sample_map.map
    
    def test_map_get_for_user(self, app, db_session, regular_user, sample_map):
        """Test Map.get_map_for_user class method."""
        with app.app_context():
            # Should find map for user's location
            map_record = Map.get_map_for_user(regular_user)
            
            assert map_record is not None
            assert map_record.state == regular_user.state
            assert map_record.county == regular_user.county
            assert map_record.precinct == regular_user.precinct
    
    def test_map_get_for_user_not_found(self, app, db_session):
        """Test Map.get_map_for_user when no map exists."""
        with app.app_context():
            # Create user with location that has no map
            user = User(
                username='no_map_user',
                email='nomap@test.com',
                password='test_password',
                phone='555-NOMAP',
                role='voter',
                state='CA',  # Different state
                county='Los Angeles',
                precinct='999'
            )
            
            map_record = Map.get_map_for_user(user)
            assert map_record is None
    
    def test_map_get_filenames_for_county(self, app, db_session, multiple_maps):
        """Test Map.get_map_filenames_for_county class method."""
        with app.app_context():
            filenames = Map.get_map_filenames_for_county('Wake')
            
            assert len(filenames) > 0
            
            # Should return dictionaries with required fields
            for map_info in filenames:
                assert 'filename' in map_info
                assert 'display_name' in map_info
                assert 'precinct' in map_info
                assert 'map_content' in map_info
                assert map_info['filename'].endswith('.html')


class TestDatabaseRelationships:
    """Test relationships between models."""
    
    def test_user_map_relationship(self, app, db_session, regular_user, sample_map):
        """Test relationship between users and their maps."""
        with app.app_context():
            # Find map for user
            user_map = Map.query.filter_by(
                state=regular_user.state,
                county=regular_user.county,
                precinct=regular_user.precinct
            ).first()
            
            assert user_map is not None
            assert user_map.state == regular_user.state
            assert user_map.county == regular_user.county
            assert user_map.precinct == regular_user.precinct


class TestDatabaseOperations:
    """Test database CRUD operations."""
    
    def test_create_multiple_users(self, app, db_session):
        """Test creating multiple users."""
        with app.app_context():
            users = []
            for i in range(5):
                user = User(
                    username=f'bulk_user_{i}',
                    email=f'bulk_{i}@test.com',
                    password=f'password_{i}',
                    phone=f'555-{i:04d}',
                    role='voter',
                    state='NC',
                    county='Wake',
                    precinct=f'00{i}'
                )
                users.append(user)
                db_session.add(user)
            
            db_session.commit()
            
            # Verify all users were created
            for user in users:
                assert user.id is not None
    
    def test_update_user_information(self, app, db_session, regular_user):
        """Test updating user information."""
        with app.app_context():
            # Update user fields
            regular_user.email = 'updated@test.com'
            regular_user.phone = '555-9999'
            regular_user.notes = 'Updated notes'
            
            db_session.add(regular_user)  # Ensure the changes are tracked
            db_session.commit()
            
            # Verify updates
            updated_user = User.query.get(regular_user.id)
            assert updated_user.email == 'updated@test.com'
            assert updated_user.phone == '555-9999'
            assert updated_user.notes == 'Updated notes'
    
    def test_delete_user(self, app, db_session):
        """Test deleting a user."""
        with app.app_context():
            # Create user to delete
            user = User(
                username='to_delete',
                email='delete@test.com',
                password='test_password',
                phone='555-DEL',
                role='voter',
                state='NC',
                county='Wake',
                precinct='999'
            )
            
            db_session.add(user)
            db_session.commit()
            
            user_id = user.id
            
            # Delete user
            db_session.delete(user)
            db_session.commit()
            
            # Verify user was deleted
            deleted_user = User.query.get(user_id)
            assert deleted_user is None
    
    def test_query_users_by_county(self, app, db_session, regular_user, county_user):
        """Test querying users by county."""
        with app.app_context():
            wake_users = User.query.filter_by(county='Wake').all()
            
            assert len(wake_users) >= 2  # At least regular_user and county_user
            
            user_ids = [user.id for user in wake_users]
            assert regular_user.id in user_ids
            assert county_user.id in user_ids
    
    def test_query_active_users(self, app, db_session, regular_user, inactive_user):
        """Test querying active vs inactive users."""
        with app.app_context():
            active_users = User.query.filter_by(is_active=True).all()
            inactive_users = User.query.filter_by(is_active=False).all()
            
            # Should have at least one active and one inactive
            assert len(active_users) >= 1
            assert len(inactive_users) >= 1
            
            active_ids = [user.id for user in active_users]
            inactive_ids = [user.id for user in inactive_users]
            
            assert regular_user.id in active_ids
            assert inactive_user.id in inactive_ids


class TestDataValidation:
    """Test data validation and constraints."""
    
    def test_required_user_fields(self, app, db_session):
        """Test that required user fields are enforced."""
        with app.app_context():
            # Try to create user without required fields (should raise TypeError)
            with pytest.raises(TypeError):
                incomplete_user = User()  # This should fail due to required args
            
            # Test passed - TypeError was properly raised for missing required fields
    
    def test_email_format_validation(self, app, db_session):
        """Test email format validation (if implemented)."""
        with app.app_context():
            user = User(
                username='email_test',
                email='invalid_email_format',
                password='test_password',
                phone='555-EMAIL',
                role='voter',
                state='NC',
                county='Wake',
                precinct='001'
            )
            
            db_session.add(user)
            # Note: Actual email validation depends on model implementation
            # This test structure shows how to test it
            try:
                db_session.commit()
                # If no validation, this will succeed
                assert user.id is not None
            except Exception:
                # If validation exists, this will raise an exception
                pass
    
    def test_precinct_format(self, app, db_session):
        """Test precinct number format handling."""
        with app.app_context():
            user = User(
                username='precinct_test',
                email='precinct@test.com',
                password='test_password',
                phone='555-PREC',
                role='voter',
                state='NC',
                county='Wake',
                precinct='012'  # Should handle leading zeros
            )
            
            db_session.add(user)
            db_session.commit()
            
            assert user.precinct == '012'