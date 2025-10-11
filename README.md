# Precinct Member's Application with Login & User Management
    - by Claude Sonnet 4
A complete Flask web application featuring user authentication, encrypted passwords, and administrative user management using Flask-Login and Flask-Admin.

## Features

### Authentication & Security
- **User Login/Logout**: Secure authentication system with Flask-Login
- **Password Encryption**: Passwords are hashed using Werkzeug's secure password hashing
- **Session Management**: Secure session handling with remember me functionality
- **CSRF Protection**: Built-in CSRF protection with Flask-WTF

### User Management
- **Admin Panel**: Full-featured admin interface powered by Flask-Admin
- **User CRUD Operations**: Create, read, update, and delete users
- **Role-based Access**: Admin and regular user roles
- **User Search & Filtering**: Search by username/email, filter by role and status
- **Account Status Management**: Enable/disable user accounts

### Configuration Management
- **Environment-based Config**: Separate configurations for development, production, and testing
- **Secure Defaults**: Production-ready security settings
- **Environment Variables**: Support for environment variable configuration
- **Flexible Settings**: Easy customization of database, security, and application settings

### User Interface
- **Responsive Design**: Bootstrap-based responsive UI
- **Modern Styling**: Clean, professional interface with Font Awesome icons
- **Flash Messages**: User feedback with styled alert messages
- **Navigation**: Context-aware navigation based on user role

## Installation

1. **Install Dependencies**:
   ```bash
   uv sync
   ```

2. **Run the Application**:
   ```bash
   python main.py
   ```

3. **Access the Application**:
   - Main App: http://127.0.0.1:5000
   - Admin Panel: http://127.0.0.1:5000/admin

## Configuration

The application uses a `config.py` file for configuration management with support for different environments:

### Environment Configuration
- **Development**: Default configuration with debug mode enabled
- **Production**: Secure settings for production deployment
- **Testing**: Configuration optimized for testing

### Environment Variables
Create a `.env` file (see `.env.example`) to customize settings:

```bash
# Copy the example environment file
cp .env.example .env

# Edit the configuration
nano .env
```

### Key Configuration Options
- `FLASK_ENV`: Set environment (development, production, testing)
- `SECRET_KEY`: Application secret key (change in production)
- `DATABASE_URL`: Database connection string
- `SESSION_COOKIE_SECURE`: Enable secure cookies in production
- `DEFAULT_ADMIN_*`: Default admin user settings

## Default Credentials

The application creates a default admin user on first run:
- **Username**: `admin`
- **Password**: `admin123`

## Usage

### For Regular Users
1. **Login**: Use your credentials to access the dashboard
2. **Dashboard**: View your account information and quick actions
3. **Profile**: View detailed profile information
4. **Logout**: Securely end your session

### For Administrators
1. **Admin Panel**: Access the full user management interface at `/admin`
2. **Create Users**: Add new users with username, email, and password
3. **Edit Users**: Modify existing user information and permissions
4. **Search & Filter**: Find users quickly using the search and filter options
5. **Role Management**: Grant or revoke admin privileges

## Application Structure

```
├── main.py              # Main Flask application
├── models.py            # Database models (User model)
├── templates/           # HTML templates
│   ├── base.html       # Base template with navigation
│   ├── login.html      # Login form
│   ├── dashboard.html  # User dashboard
│   └── profile.html    # User profile page
├── pyproject.toml      # Project dependencies
└── app.db              # SQLite database (created on first run)
```

## Key Components

### User Model (`models.py`)
- SQLAlchemy model with encrypted password storage
- Flask-Login integration with required methods
- Automatic password hashing on creation/updates

### Authentication (`main.py`)
- Login/logout routes with form validation
- Session management with Flask-Login
- Password verification with secure hashing

### Admin Interface
- Custom secure ModelView requiring admin privileges
- User-friendly forms with password handling
- Search, filter, and pagination capabilities

## Security Features

- **Password Hashing**: Uses Werkzeug's generate_password_hash
- **Session Security**: Secure session cookies with CSRF protection
- **Access Control**: Role-based access to admin functionality
- **Input Validation**: Form validation with WTForms
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection

## Configuration

The application uses environment variables for configuration:
- `SECRET_KEY`: Flask secret key (defaults to development key)
- `DATABASE_URL`: Database connection string (defaults to SQLite)

## Production Deployment

For production deployment:
1. Set `SECRET_KEY` environment variable to a secure random key
2. Configure a production database (PostgreSQL, MySQL, etc.)
3. Use a production WSGI server (Gunicorn, uWSGI)
4. Enable HTTPS and secure headers
5. Change default admin credentials immediately

## Technologies Used

- **Flask**: Web framework
- **Flask-Login**: User session management
- **Flask-Admin**: Administrative interface
- **Flask-SQLAlchemy**: Database ORM
- **Flask-WTF**: Form handling and CSRF protection
- **Werkzeug**: Password hashing
- **Bootstrap 5**: Frontend styling
- **Font Awesome**: Icons
