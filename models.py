from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

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
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    phone = db.Column(db.String(20), nullable=True)
    role = db.Column(db.String(100), nullable=True)
    precinct = db.Column(db.String(100), nullable=True)
    map = db.Column(db.String(255), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    def __init__(self, username, email, password, is_admin=False, phone=None, role=None, precinct=None, map=None, notes=None):
        self.username = username
        self.email = email
        self.password = password
        self.set_password(password)
        self.is_admin = is_admin
        self.phone = phone
        self.role = role
        self.precinct = precinct
        self.map = map
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
    
    def is_county(self):
        """Return True if the user's role is 'County'."""
        return self.role == 'County'
    
    def __repr__(self):
        return f'<User {self.username}>'
    
    def __str__(self):
        return self.username