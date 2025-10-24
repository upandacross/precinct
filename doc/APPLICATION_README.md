# Precinct Member's Application with Login & User Management

A complete Flask web application featuring user authentication, encrypted passwords, and administrative user management

## Features

### Authentication & Security

- **User Login/Logout**: Secure authentication system
- **Password Encryption**: Passwords are hashed using secure password hashing
- **Session Management**: Secure session handling with remember me functionality
- **CSRF Protection**: Built-in CRSF protocol protection

### User Management (Admin only)

- **Admin Panel**: Full-featured admin interface
- **User CRUD Operations**: Create, read, update, and delete users
- **Role-based Access**: Admin and regular user roles
- **User Search & Filtering**: Search by username/email, filter by role and status
- **Account Status Management**: Activate/Inactivate user accounts

### Configuration Management

- **Environment-based Config**: Separate configurations for development, production, and testing
- **Secure Defaults**: Production-ready security settings
- **Flexible Settings**: Easy customization of database, security, and application settings

### User Interface

- **Responsive Design**: Responsive UI for small screens
- **Modern Styling**: Clean, professional interface
- **Flash Messages**: User feedback with styled alert messages
- **Navigation**: Context-aware navigation based on user role

### Environment Configuration

- **Development**: Default configuration with debug mode enabled
- **Production**: Secure settings for production deployment
- **Testing**: Configuration optimized for testing

### For Regular Users

1. **Login**: Use your unique username and unique password to access the dashboard
2. **Dashboard**: View your account information and quick actions
3. **Profile**: View detailed profile information
4. **Logout**: Securely end your session

### For Administrators

1. **Admin Panel**: Access the full user management interface
2. **Create Users**: Add new users with username, email, and password
3. **Edit Users**: Modify existing user information and permissions
4. **Search & Filter**: Find users quickly using the search and filter options
5. **Role Management**: Grant or revoke admin privileges

## Key Components

### User Model

- Database model with encrypted seret key storage
- Automatic password hashing on creation/updates

### Authentication

- Login/logout web pages with form validation
- Session management login
- Password verification with secure hashing

### Admin Interface

- Custom secure views requiring admin privileges
- User-friendly forms with password handling
- Search, filter, and pagination capabilities

## Security Features

- **Password Hashing**: Uses password hashing
- **Session Security**: Secure session cookies with internet security protection
- **Access Control**: Role-based access to application functionality
- **Input Validation**: Form validation by application
- **SQL Injection Protection**: Application technology prevents SQL injection
