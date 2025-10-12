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
        admin_user = User.query.filter_by(username='admin').first()
        if not admin_user:
            # Create default admin user
            admin_user = User(
                username='admin',
                email='admin@example.com',
                password='admin123',  # This will be hashed automatically
                is_admin=True,
                is_active=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created: admin/admin123")
        else:
            print("Admin user already exists.")

if __name__ == '__main__':
    init_db()