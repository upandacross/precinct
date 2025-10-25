from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from precinct_utils import normalize_precinct_id

db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and admin management."""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_county = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    phone = db.Column(db.String(20), nullable=False)
    role = db.Column(db.String(100), nullable=False)
    precinct = db.Column(db.String(100), nullable=True)
    state = db.Column(db.String(50), nullable=True)
    county = db.Column(db.String(100), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def __init__(self, username, email, password, phone, role, is_admin=False, is_county=False, is_active=True, precinct=None, state=None, county=None, notes=None):
        self.username = username
        self.email = email
        self.password = password
        self.set_password(password)
        self.phone = phone
        self.role = role
        self.is_admin = is_admin
        self.is_county = is_county
        self.is_active = is_active
        self.precinct = precinct
        self.state = state
        self.county = county
        self.notes = notes
    
    def set_password(self, password):
        """Hash and set the user's password."""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Check if the provided password matches the user's password."""
        return check_password_hash(self.password_hash, password)
    
    def get_id(self):
        """Return the user ID as a string (required by Flask-Login)."""
        return str(self.id)
    
    def is_authenticated(self):
        """Return True if the user is authenticated."""
        return True
    
    def is_anonymous(self):
        """Return False since this is not an anonymous user."""
        return False
    
    def get_normalized_precinct(self):
        """Get normalized precinct IDs (padded, unpadded) for flexible database queries.
        
        Returns:
            tuple: (padded_precinct, unpadded_precinct) or (None, None) if no precinct set
        """
        if not self.precinct:
            return None, None
        return normalize_precinct_id(self.precinct)
    
    def get_precinct_display_name(self):
        """Get a user-friendly display name for the precinct.
        
        Returns:
            str: Formatted precinct display name or 'Not Set'
        """
        if not self.precinct or not self.county or not self.state:
            return 'Not Set'
        return f"{self.state} {self.county} Precinct {self.precinct}"
    
    def matches_precinct(self, precinct_value):
        """Check if a precinct value matches this user's precinct in any format.
        
        Args:
            precinct_value: Precinct ID to check against (any format)
            
        Returns:
            bool: True if the precinct matches this user's precinct
        """
        if not self.precinct or not precinct_value:
            return False
            
        user_padded, user_unpadded = self.get_normalized_precinct()
        test_padded, test_unpadded = normalize_precinct_id(precinct_value)
        
        if not user_padded or not test_padded:
            return False
            
        return user_padded == test_padded or user_unpadded == test_unpadded
    

    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def __str__(self):
        return self.username


class Map(db.Model):
    """Map model for storing precinct map data in NC PostgreSQL database."""
    
    __tablename__ = 'maps'
    
    id = db.Column(db.Integer, primary_key=True)
    state = db.Column(db.String(100), nullable=False, index=True)
    county = db.Column(db.String(100), nullable=False, index=True)
    precinct = db.Column(db.String(100), nullable=False, index=True)
    map = db.Column(db.Text, nullable=True)  # Store HTML content
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, state, county, precinct, map=None, created_at=None, updated_at=None):
        self.state = state
        self.county = county
        self.precinct = precinct
        self.map = map
        if created_at:
            self.created_at = created_at
        if updated_at:
            self.updated_at = updated_at
    
    @staticmethod
    def get_map_for_user(user):
        """Get the map for a specific user based on their state, county, and precinct.
        
        Uses normalized precinct matching to handle zero-padding inconsistencies.
        """
        if not user.state or not user.county or not user.precinct:
            return None
        
        # Get normalized precinct formats
        padded_precinct, unpadded_precinct = user.get_normalized_precinct()
        if not padded_precinct:
            return None
        
        # Try padded format first
        map_record = Map.query.filter_by(
            state=user.state,
            county=user.county,
            precinct=padded_precinct
        ).first()
        
        # If not found, try unpadded format
        if not map_record:
            map_record = Map.query.filter_by(
                state=user.state,
                county=user.county,
                precinct=unpadded_precinct
            ).first()
        
        return map_record
    
    @staticmethod
    def get_map_by_location(state, county, precinct):
        """Get the map for a specific location.
        
        Uses normalized precinct matching to handle zero-padding inconsistencies.
        """
        # Get normalized precinct formats
        padded_precinct, unpadded_precinct = normalize_precinct_id(precinct)
        if not padded_precinct:
            return None
        
        # Try padded format first
        map_record = Map.query.filter_by(
            state=state,
            county=county,
            precinct=padded_precinct
        ).first()
        
        # If not found, try unpadded format
        if not map_record:
            map_record = Map.query.filter_by(
                state=state,
                county=county,
                precinct=unpadded_precinct
            ).first()
        
        return map_record
    
    @staticmethod
    def get_maps_for_county(county_name):
        """Get all maps for a specific county from NC database."""
        return Map.query.filter_by(county=county_name).order_by(Map.precinct).all()
    
    @staticmethod
    def get_map_filenames_for_county(county_name):
        """Get all map filenames for a specific county."""
        maps = Map.get_maps_for_county(county_name)
        
        map_files = []
        for map_obj in maps:
            filename = f"{map_obj.precinct}.html"
            map_files.append({
                'filename': filename,
                'precinct': map_obj.precinct,
                'state': map_obj.state,
                'county': map_obj.county,
                'display_name': f'{map_obj.state} {map_obj.county} Precinct {map_obj.precinct}',
                'source': 'nc_database',
                'map_content': map_obj.map,
                'size': len(map_obj.map) if map_obj.map else 0,
                'modified': map_obj.created_at,
                'map_id': map_obj.id
            })
        
        return map_files
    
    def __repr__(self):
        return f'<Map {self.state}-{self.county}-{self.precinct}>'
    
    def __str__(self):
        return f'{self.state} {self.county} Precinct {self.precinct}'


class UpcomingElection(db.Model):
    """Model for tracking upcoming elections including municipal, primary, and general elections."""
    
    __tablename__ = 'upcoming_elections'
    
    id = db.Column(db.Integer, primary_key=True)
    election_name = db.Column(db.String(200), nullable=False)
    election_type = db.Column(db.String(50), nullable=False)  # municipal, primary, general, special
    election_date = db.Column(db.Date, nullable=False, index=True)
    early_voting_start = db.Column(db.Date, nullable=True)
    early_voting_end = db.Column(db.Date, nullable=True)
    absentee_request_deadline = db.Column(db.Date, nullable=True)
    absentee_return_deadline = db.Column(db.Date, nullable=True)
    voter_registration_deadline = db.Column(db.Date, nullable=True)
    county = db.Column(db.String(100), nullable=True, index=True)  # NULL = statewide
    municipality = db.Column(db.String(100), nullable=True)  # For municipal elections
    state = db.Column(db.String(50), nullable=False, default='NC')
    description = db.Column(db.Text, nullable=True)
    contests = db.Column(db.Text, nullable=True)  # JSON or comma-separated list of races
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __init__(self, election_name, election_type, election_date, 
                 early_voting_start=None, early_voting_end=None,
                 absentee_request_deadline=None, absentee_return_deadline=None,
                 voter_registration_deadline=None, county=None, municipality=None,
                 state='NC', description=None, contests=None, is_active=True):
        self.election_name = election_name
        self.election_type = election_type
        self.election_date = election_date
        self.early_voting_start = early_voting_start
        self.early_voting_end = early_voting_end
        self.absentee_request_deadline = absentee_request_deadline
        self.absentee_return_deadline = absentee_return_deadline
        self.voter_registration_deadline = voter_registration_deadline
        self.county = county
        self.municipality = municipality
        self.state = state
        self.description = description
        self.contests = contests
        self.is_active = is_active
    
    @staticmethod
    def get_upcoming_elections(county=None, limit=10):
        """Get upcoming elections, optionally filtered by county."""
        from datetime import date
        query = UpcomingElection.query.filter(
            UpcomingElection.election_date >= date.today(),
            UpcomingElection.is_active == True
        )
        
        if county:
            # Get both county-specific and statewide elections
            query = query.filter(
                db.or_(
                    UpcomingElection.county == county,
                    UpcomingElection.county == None
                )
            )
        
        return query.order_by(UpcomingElection.election_date).limit(limit).all()
    
    @staticmethod
    def get_next_election(county=None):
        """Get the next upcoming election."""
        elections = UpcomingElection.get_upcoming_elections(county=county, limit=1)
        return elections[0] if elections else None
    
    def days_until_election(self):
        """Calculate days remaining until this election."""
        from datetime import date
        if self.election_date:
            delta = self.election_date - date.today()
            return delta.days
        return None
    
    def is_early_voting_active(self):
        """Check if early voting is currently active."""
        from datetime import date
        today = date.today()
        if self.early_voting_start and self.early_voting_end:
            return self.early_voting_start <= today <= self.early_voting_end
        return False
    
    def __repr__(self):
        location = self.municipality or self.county or 'Statewide'
        return f'<UpcomingElection {self.election_name} - {location} - {self.election_date}>'
    
    def __str__(self):
        return f'{self.election_name} ({self.election_date})'


