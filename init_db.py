#!/usr/bin/env python3
"""
Initialize the database and create default admin user.
"""

from main import create_app
from models import db, User

def init_db():
    """Initialize database and create default admin user."""
    app = create_app()
    
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully.")
        
        # Check if admin user exists  
        admin_user = User.query.filter_by(username=app.config['DEFAULT_ADMIN_USERNAME']).first()
        if not admin_user:
            # Create default admin user using config variables
            admin_user = User(
                username=app.config['DEFAULT_ADMIN_USERNAME'],
                email=app.config['DEFAULT_ADMIN_EMAIL'],
                password=app.config['DEFAULT_ADMIN_PASSWORD'],  # Uses SECRET env var
                is_admin=True,
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"Default admin user created: {app.config['DEFAULT_ADMIN_USERNAME']}/{app.config['DEFAULT_ADMIN_PASSWORD']}")
        else:
            pass

if __name__ == '__main__':
    init_db()