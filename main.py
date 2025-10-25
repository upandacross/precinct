import os
import re
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify, send_file, send_from_directory, current_app
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_admin import Admin, AdminIndexView, expose, BaseView
from flask_admin.contrib.sqla import ModelView
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email
from sqlalchemy import text
from models import db, User, Map
from datetime import datetime, timedelta
from config import get_config
from security import add_security_headers
from precinct_utils import normalize_precinct_id, normalize_precinct_join, create_precinct_lookup
import markdown
try:
    from dash_analytics import create_dash_app
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False
# Security features implemented:
# ✅ HSTS (HTTP Strict Transport Security) - max-age=31536000; includeSubDomains
# ✅ CSP (Content Security Policy) - comprehensive XSS protection
# ✅ X-Frame-Options: DENY - clickjacking protection
# ✅ X-Content-Type-Options: nosniff - MIME confusion protection
# ✅ Referrer-Policy and Permissions-Policy implemented
# TODO: research Auth0 for MFA

class LoginForm(FlaskForm):
    """Login form for user authentication."""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

class CustomUserForm(FlaskForm):
    """Custom form for User creation with proper validation."""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=80)])
    email = StringField('Email', validators=[DataRequired(), Length(max=120)])
    password = StringField('Password', validators=[DataRequired(), Length(min=6, max=255)])
    phone = StringField('Phone', validators=[DataRequired(), Length(max=20)])
    role = StringField('Role', validators=[DataRequired(), Length(max=100)])
    precinct = StringField('Precinct', validators=[Length(max=100)])
    state = StringField('State', validators=[Length(max=50)])
    county = StringField('County', validators=[Length(max=100)])
    notes = TextAreaField('Notes')
    is_admin = BooleanField('Is Admin')
    is_county = BooleanField('Is County')
    is_active = BooleanField('Is Active', default=True)

class SecureModelView(ModelView):
    """Secure model view that requires admin login."""
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))
class UserModelView(SecureModelView):
    """Custom model view for User management."""
    column_exclude_list = ['password_hash']
    column_searchable_list = ['username', 'email', 'password', 'phone', 'role', 'precinct', 'state', 'county']
    column_filters = ['is_admin', 'is_county', 'is_active', 'created_at', 'role', 'precinct', 'state', 'county']
    form_excluded_columns = ['password_hash', 'created_at', 'last_login']
    column_details_list = ['id', 'username', 'email', 'password', 'phone', 'role', 'precinct', 'state', 'county', 'notes', 'is_admin', 'is_county', 'is_active', 'created_at', 'last_login']
    
    # Use custom form to bypass automatic field generation issues
    form = CustomUserForm
    
    def on_model_change(self, form, model, is_created):
        """Hash password when creating or updating user."""
        if hasattr(form, 'password') and form.password.data:
            model.set_password(form.password.data)

class SecureAdminIndexView(AdminIndexView):
    """Secure admin index view."""
    @expose('/')
    def index(self):
        if not current_user.is_authenticated or not current_user.is_admin:
            return redirect(url_for('login'))
        return self.render('admin/index.html')

class DocumentationView(BaseView):
    """Flask-Admin view for managing documentation files."""
    
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin
    
    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))
    
    @expose('/')
    def index(self):
        """List all documentation files."""
        doc_dir = os.path.join(current_app.root_path, 'doc')
        docs = []
        
        if os.path.exists(doc_dir):
            for filename in os.listdir(doc_dir):
                if filename.endswith('.md') or filename.endswith('.txt'):
                    filepath = os.path.join(doc_dir, filename)
                    if os.path.isfile(filepath):
                        stat_info = os.stat(filepath)
                        last_modified = datetime.fromtimestamp(stat_info.st_mtime)
                        
                        docs.append({
                            'filename': filename,
                            'display_name': filename.replace('_', ' ').replace('.md', '').replace('.txt', '').title(),
                            'last_modified': last_modified,
                            'size': stat_info.st_size,
                            'extension': os.path.splitext(filename)[1]
                        })
        
        docs.sort(key=lambda x: x['filename'])
        return self.render('admin/documentation.html', docs=docs)
    
    @expose('/view/<filename>')
    def view_file(self, filename):
        """View a specific documentation file."""
        doc_dir = os.path.join(current_app.root_path, 'doc')
        filepath = os.path.join(doc_dir, filename)
        
        # Security check
        if not os.path.abspath(filepath).startswith(os.path.abspath(doc_dir)):
            abort(404)
        
        if not os.path.exists(filepath):
            abort(404)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            stat_info = os.stat(filepath)
            last_modified = datetime.fromtimestamp(stat_info.st_mtime)
            is_markdown = filename.endswith('.md')
            
            return self.render('admin/view_documentation.html', 
                             content=content,
                             filename=filename,
                             display_name=filename.replace('_', ' ').replace('.md', '').replace('.txt', '').title(),
                             last_modified=last_modified,
                             is_markdown=is_markdown)
        
        except Exception as e:
            flash(f'Error reading file: {str(e)}', 'danger')
            return redirect(url_for('.index'))
    
    @expose('/edit/<filename>', methods=['GET', 'POST'])
    def edit_file(self, filename):
        """Edit a documentation file."""
        doc_dir = os.path.join(current_app.root_path, 'doc')
        filepath = os.path.join(doc_dir, filename)
        
        # Security check
        if not os.path.abspath(filepath).startswith(os.path.abspath(doc_dir)):
            abort(404)
        
        if not os.path.exists(filepath):
            abort(404)
        
        if request.method == 'POST':
            content = request.form.get('content', '')
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                flash(f'File {filename} updated successfully!', 'success')
                return redirect(url_for('.view_file', filename=filename))
            except Exception as e:
                flash(f'Error saving file: {str(e)}', 'danger')
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            return self.render('admin/edit_documentation.html',
                             content=content,
                             filename=filename,
                             display_name=filename.replace('_', ' ').replace('.md', '').replace('.txt', '').title())
        
        except Exception as e:
            flash(f'Error reading file: {str(e)}', 'danger')
            return redirect(url_for('.index'))
    
    @expose('/rename/<filename>', methods=['GET', 'POST'])
    def rename_file(self, filename):
        """Rename a documentation file."""
        doc_dir = os.path.join(current_app.root_path, 'doc')
        old_filepath = os.path.join(doc_dir, filename)
        
        # Security check
        if not os.path.abspath(old_filepath).startswith(os.path.abspath(doc_dir)):
            abort(404)
        
        if not os.path.exists(old_filepath):
            abort(404)
        
        if request.method == 'POST':
            new_filename = request.form.get('new_filename', '').strip()
            
            if not new_filename:
                flash('New filename cannot be empty', 'danger')
            elif new_filename == filename:
                flash('New filename is the same as current filename', 'warning')
                return redirect(url_for('.index'))
            else:
                # Validate filename - only allow letters, numbers, underscores, hyphens, and dots
                if not re.match(r'^[a-zA-Z0-9_.-]+$', new_filename):
                    flash('Filename contains invalid characters. Only letters, numbers, underscores, hyphens, and dots are allowed.', 'danger')
                else:
                    # Ensure file extension is preserved if not provided
                    old_ext = os.path.splitext(filename)[1]
                    new_ext = os.path.splitext(new_filename)[1]
                    
                    if not new_ext and old_ext:
                        new_filename += old_ext
                    
                    new_filepath = os.path.join(doc_dir, new_filename)
                    
                    # Check if new filename already exists
                    if os.path.exists(new_filepath):
                        flash(f'A file named "{new_filename}" already exists', 'danger')
                    else:
                        try:
                            os.rename(old_filepath, new_filepath)
                            flash(f'File renamed from "{filename}" to "{new_filename}" successfully!', 'success')
                            return redirect(url_for('.view_file', filename=new_filename))
                        except Exception as e:
                            flash(f'Error renaming file: {str(e)}', 'danger')
        
        return self.render('admin/rename_documentation.html',
                         filename=filename,
                         display_name=filename.replace('_', ' ').replace('.md', '').replace('.txt', '').title())
    
    @expose('/delete/<filename>', methods=['POST'])
    def delete_file(self, filename):
        """Delete a documentation file."""
        doc_dir = os.path.join(current_app.root_path, 'doc')
        filepath = os.path.join(doc_dir, filename)
        
        # Security check
        if not os.path.abspath(filepath).startswith(os.path.abspath(doc_dir)):
            abort(404)
        
        if not os.path.exists(filepath):
            abort(404)
        
        try:
            os.remove(filepath)
            flash(f'File "{filename}" deleted successfully!', 'success')
        except Exception as e:
            flash(f'Error deleting file: {str(e)}', 'danger')
        
        return redirect(url_for('.index'))

def create_app():
    """Application factory."""
    app = Flask(__name__)
    
    # Load configuration from config.py
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    
    # Flask-Limiter setup
    # For tests, conditionally disable rate limiting completely
    if app.config.get('RATELIMIT_ENABLED', True):
        default_limits = ["200 per day", "50 per hour"]
        limiter = Limiter(
            key_func=get_remote_address,
            default_limits=default_limits,
            storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
        )
        limiter.init_app(app)
    else:
        # For testing: create a dummy limiter that doesn't actually limit
        class DummyLimiter:
            def __init__(self):
                pass
            def limit(self, *args, **kwargs):
                def decorator(f):
                    return f  # Return function unchanged
                return decorator
            def init_app(self, app):
                pass
            def __getattr__(self, name):
                # Return a dummy method for any other limiter attributes/methods
                def dummy(*args, **kwargs):
                    def decorator(f):
                        return f
                    return decorator
                return dummy
        limiter = DummyLimiter()
    
    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Security headers setup
    @app.after_request
    def apply_security_headers(response):
        """Apply HSTS and other security headers to all responses."""
        return add_security_headers(response)
    
    # NC database is initialized through the same db instance with SQLALCHEMY_BINDS
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Message of the Day helper function
    def get_motd():
        """Read and return the message of the day from motd.md file, rendered as HTML."""
        try:
            motd_path = os.path.join(app.root_path, 'motd.md')
            if os.path.exists(motd_path):
                with open(motd_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        # Convert Markdown to HTML
                        html_content = markdown.markdown(
                            content,
                            extensions=['extra', 'nl2br', 'sane_lists']
                        )
                        return html_content
            return None
        except Exception as e:
            app.logger.warning(f'Error reading MOTD file: {str(e)}')
            return None
    
    # Map helper functions
    def create_error_page(error_title, error_message):
        """Create a standardized error page for map loading issues."""
        return f'''<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{error_title} - Precinct Maps</title>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 40px;
            background-color: #f8f9fa;
            color: #333;
        }}
        .error-container {{
            max-width: 600px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .error-icon {{
            font-size: 64px;
            color: #dc3545;
            margin-bottom: 20px;
        }}
        .error-title {{
            font-size: 24px;
            font-weight: bold;
            color: #dc3545;
            margin-bottom: 15px;
        }}
        .error-message {{
            font-size: 16px;
            line-height: 1.5;
            margin-bottom: 25px;
            color: #666;
        }}
        .error-actions {{
            margin-top: 30px;
        }}
        .btn {{
            display: inline-block;
            padding: 10px 20px;
            margin: 5px;
            text-decoration: none;
            border-radius: 4px;
            font-weight: bold;
        }}
        .btn-primary {{
            background-color: #007bff;
            color: white;
        }}
        .btn-secondary {{
            background-color: #6c757d;
            color: white;
        }}
        .btn:hover {{
            opacity: 0.9;
        }}
        .technical-info {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #dc3545;
            text-align: left;
            font-size: 14px;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="error-container">
        <div class="error-icon">⚠️</div>
        <div class="error-title">{error_title}</div>
        <div class="error-message">{error_message}</div>
        
        <div class="error-actions">
            <a href="javascript:history.back()" class="btn btn-secondary">← Go Back</a>
            <a href="/dashboard" class="btn btn-primary">Dashboard</a>
        </div>
        
        <div class="technical-info">
            <strong>What happened?</strong><br>
            There was an issue retrieving the map content from the database. This could be due to:
            <ul style="margin: 10px 0; text-align: left;">
                <li>Temporary database connectivity issues</li>
                <li>Missing or corrupted map data</li>
                <li>File system issues with static map files</li>
            </ul>
            If this problem persists, please contact technical support.
        </div>
    </div>
</body>
</html>'''

    def get_map_content_for_user(user):
        """Get map content for a user from the database."""
        if not user or not user.state or not user.county or not user.precinct:
            return None
        
        try:
            map_record = Map.get_map_for_user(user)
            if not map_record or not map_record.map:
                return None
            
            # Check if map field contains a filename reference (which is an error - should be full HTML content)
            if map_record.map.endswith('.html') and len(map_record.map) < 50:
                app.logger.error(f'Database contains filename reference {map_record.map} for user {user.username} - should contain full HTML content')
                return create_error_page("Database Error", 
                    f"Map content missing from database for user {user.username}. Only filename reference found.")
            
            # Map field should contain full HTML content stored directly in the database
            return map_record.map
            
        except Exception as e:
            app.logger.error(f'Database error retrieving map for user {user.username}: {str(e)}')
            return create_error_page("Database Error", 
                "Failed to retrieve map from database. Please try again or contact support.")
    
    def get_map_content_by_filename(filename):
        """Get map content by filename using current user's state/county context."""
        try:
            # Extract precinct number from filename (e.g., "999.html" -> "999")
            if filename.endswith('.html'):
                precinct = filename[:-5]  # Remove .html extension
                
                # Use current user's state and county to find the correct map
                if not current_user or not current_user.state or not current_user.county:
                    app.logger.error(f'Cannot lookup map {filename} - user has no state/county context')
                    return create_error_page("Access Error", 
                        "Your state/county information is not set. Please contact an administrator.")
                
                # Normalize precinct number for flexible database lookup
                padded_precinct, unpadded_precinct = normalize_precinct_id(precinct)
                if not padded_precinct:
                    app.logger.error(f'Invalid precinct format in filename: {filename}')
                    return create_error_page("Invalid Request", 
                        f"Invalid precinct format in filename: {filename}")
                
                # Try finding map with both padded and unpadded precinct formats
                map_record = Map.query.filter_by(
                    state=current_user.state,
                    county=current_user.county,
                    precinct=padded_precinct
                ).first()
                
                # If not found with padded format, try unpadded
                if not map_record:
                    map_record = Map.query.filter_by(
                        state=current_user.state,
                        county=current_user.county,
                        precinct=unpadded_precinct
                    ).first()
                
                if map_record and map_record.map:
                    # If it's stored HTML content, return it
                    if not map_record.map.endswith('.html') or len(map_record.map) > 50:
                        app.logger.info(f'Serving map {filename} from database (full content) for {map_record.state} {map_record.county} Precinct {map_record.precinct}')
                        return map_record.map
                    
                    # If it's a filename reference, this is an error - should contain full HTML content
                    app.logger.error(f'Database contains filename reference {map_record.map} for {filename} in {current_user.state} {current_user.county} - should contain full HTML content')
                    return create_error_page("Database Error", 
                        f"Map content missing from database for {filename}. Only filename reference found.")
                
                # Map not found for this state/county/precinct combination
                app.logger.error(f'Map {filename} not found in database for {current_user.state} {current_user.county}')
                return create_error_page("Map Not Found", 
                    f"Map {filename} not found for {current_user.state} {current_user.county}.")
            
        except Exception as e:
            app.logger.error(f'Database error retrieving map by filename {filename}: {str(e)}')
            return create_error_page("Database Error", 
                "Failed to retrieve map from database. Please try again or contact support.")
        
        # No fallback to static files - all content must come from database
        app.logger.error(f'Invalid filename format: {filename}')
        return None
    
    def user_can_access_map(user, filename_or_precinct):
        """Check if user can access a specific map."""
        if user.is_admin:
            return True
        
        # For county users, allow access to any map in their county
        if user.is_county and user.state and user.county:
            return True
        
        # Zero-pad the user's precinct for comparison
        user_precinct_padded = user.precinct.zfill(3) if user.precinct else None
        
        # For regular users, only allow access to their assigned precinct map
        if user.precinct == filename_or_precinct or user_precinct_padded == filename_or_precinct:
            return True
        
        # Check if filename corresponds to user's precinct (handle both padded and unpadded)
        if filename_or_precinct:
            # Remove .html extension if present
            precinct_from_filename = filename_or_precinct.replace('.html', '')
            
            # Check both padded and unpadded versions
            if (precinct_from_filename == user.precinct or 
                precinct_from_filename == user_precinct_padded or
                precinct_from_filename.zfill(3) == user_precinct_padded):
                return True
        
        return False

    # Make MOTD function available to all templates
    @app.context_processor
    def inject_motd():
        return dict(get_motd=get_motd)
    
    # Maintenance mode check
    @app.before_request
    def check_maintenance_mode():
        """Check if maintenance mode is enabled."""
        # Skip maintenance check for static files
        if request.path.startswith('/static/'):
            return None
        
        # Check for maintenance mode flag file
        maintenance_file = os.path.join(app.instance_path, 'MAINTENANCE_MODE')
        if os.path.exists(maintenance_file):
            # Allow access to the maintenance page itself
            if request.endpoint == 'maintenance':
                return None
            # Show maintenance page for all other requests
            return render_template('maintenance.html'), 503
        
        # If trying to access maintenance page when not in maintenance mode, redirect to index
        if request.endpoint == 'maintenance':
            return redirect(url_for('index'))
    
    # Block suspicious user agents and rapid requests
    @app.before_request
    def block_suspicious_requests():
        """Block requests from download tools and scrapers."""
        user_agent = request.headers.get('User-Agent', '').lower()
        
        # Block known download tools
        blocked_agents = [
            'wget', 'curl', 'scrapy', 'bot', 'spider', 'crawler',
            'downloader', 'harvester', 'extractor', 'httrack'
        ]
        
        for blocked in blocked_agents:
            if blocked in user_agent:
                abort(403)  # Forbidden
    
    # Session timeout handling
    @app.before_request
    def check_session_timeout():
        """Check for session timeout and update last activity."""
        if current_user.is_authenticated:
            now = datetime.utcnow()
            last_activity = session.get('last_activity')
            
            if last_activity:
                last_activity = datetime.fromisoformat(last_activity)
                timeout_minutes = app.config.get('SESSION_TIMEOUT_MINUTES', 30)
                
                # Check if session has timed out
                if (now - last_activity).total_seconds() > (timeout_minutes * 60):
                    logout_user()
                    session.clear()
                    flash('Your session has expired due to inactivity. Please log in again.', 'warning')
                    return redirect(url_for('login'))
            
            # Update last activity timestamp
            session['last_activity'] = now.isoformat()
            session.permanent = True
    
    @app.route('/api/session-status')
    @login_required
    def session_status():
        """API endpoint to check session status for client-side warnings."""
        if not current_user.is_authenticated:
            return jsonify({'status': 'expired'}), 401
            
        now = datetime.utcnow()
        last_activity = session.get('last_activity')
        
        if last_activity:
            last_activity = datetime.fromisoformat(last_activity)
            timeout_minutes = app.config.get('SESSION_TIMEOUT_MINUTES', 30)
            warning_minutes = app.config.get('SESSION_WARNING_MINUTES', 5)
            
            time_since_activity = (now - last_activity).total_seconds()
            timeout_seconds = timeout_minutes * 60
            warning_seconds = (timeout_minutes - warning_minutes) * 60
            
            if time_since_activity > warning_seconds:
                remaining_seconds = timeout_seconds - time_since_activity
                return jsonify({
                    'status': 'warning',
                    'remaining_seconds': max(0, int(remaining_seconds))
                })
        
        return jsonify({'status': 'active'})
    
    @app.route('/api/extend-session', methods=['POST'])
    @login_required
    def extend_session():
        """API endpoint to extend user session."""
        session['last_activity'] = datetime.utcnow().isoformat()
        return jsonify({'status': 'extended'})
    
    @app.route('/documentation')
    def documentation():
        """Display available documentation from doc directory."""
        doc_dir = os.path.join(app.root_path, 'doc')
        docs = []
        
        if os.path.exists(doc_dir):
            for filename in os.listdir(doc_dir):
                if filename.endswith('.md') or filename.endswith('.txt'):
                    # Only show files that start with an uppercase letter (public visibility)
                    if filename[0].isupper():
                        filepath = os.path.join(doc_dir, filename)
                        if os.path.isfile(filepath):
                            # Get file stats for last modified date
                            stat_info = os.stat(filepath)
                            last_modified = datetime.fromtimestamp(stat_info.st_mtime)
                            
                            docs.append({
                                'filename': filename,
                                'display_name': filename.replace('_', ' ').replace('.md', '').replace('.txt', '').title(),
                                'last_modified': last_modified,
                                'size': stat_info.st_size
                            })
        
        # Sort by filename
        docs.sort(key=lambda x: x['filename'])
        
        return render_template('documentation.html', docs=docs)
    
    @app.route('/documentation/<filename>')
    def show_documentation(filename):
        """Display specific documentation file."""
        doc_dir = os.path.join(app.root_path, 'doc')
        filepath = os.path.join(doc_dir, filename)
        
        # Security check - ensure file is in doc directory
        if not os.path.abspath(filepath).startswith(os.path.abspath(doc_dir)):
            abort(404)
        
        # Public visibility check - only show files that start with uppercase letter
        if not filename[0].isupper():
            abort(404)
        
        if not os.path.exists(filepath):
            abort(404)
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get file info
            stat_info = os.stat(filepath)
            last_modified = datetime.fromtimestamp(stat_info.st_mtime)
            
            # Determine content type
            is_markdown = filename.endswith('.md')
            
            return render_template('show_documentation.html', 
                                 content=content, 
                                 filename=filename,
                                 display_name=filename.replace('_', ' ').replace('.md', '').replace('.txt', '').title(),
                                 last_modified=last_modified,
                                 is_markdown=is_markdown)
        
        except Exception as e:
            app.logger.error(f'Error reading documentation file {filename}: {str(e)}')
            abort(500)
    
    @app.route('/ballot-matching-strategy')
    @login_required
    def ballot_matching_strategy():
        """Display ballot matching strategy document - version based on user role."""
        try:
            # Determine which version to show based on user role
            if current_user.is_admin or current_user.is_county:
                # Full version with examples for admin and county users
                filename = '_BALLOT_MATCHING_STRATEGY.md'
            else:
                # Simplified version without examples for regular users
                filename = '_BALLOT_MATCHING_STRATEGY_PUBLIC.md'
            
            filepath = os.path.join('doc', filename)
            
            if not os.path.exists(filepath):
                abort(404)
            
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Get file info
            stat_info = os.stat(filepath)
            last_modified = datetime.fromtimestamp(stat_info.st_mtime)
            
            return render_template('show_documentation.html', 
                                 content=content, 
                                 filename='Ballot Matching Strategy',
                                 display_name='Ballot Matching Strategy: Flippability and Future Races',
                                 last_modified=last_modified,
                                 is_markdown=True)
        
        except Exception as e:
            app.logger.error(f'Error reading ballot matching strategy: {str(e)}')
            flash('Error loading ballot matching strategy document.', 'error')
            return redirect(url_for('index'))
    
    # Flask-Admin setup
    admin = Admin(
        app, 
        name='User Admin', 
        template_mode='bootstrap4',
        base_template='admin/my_master.html' if hasattr(app.config, 'FLASK_ADMIN_SWATCH') else None,
        index_view=SecureAdminIndexView()
    )
    admin.add_view(UserModelView(User, db.session, name='Users'))
    admin.add_view(DocumentationView(name='Documentation', endpoint='doc_admin'))
    
    # Dash Analytics Integration
    if DASH_AVAILABLE:
        dash_app = create_dash_app(app)
    
    @app.route('/')
    @login_required
    def index():
        """Dashboard page - requires login."""
        # Check if we should show MOTD (only after login)
        show_motd = session.pop('show_motd', False)
        return render_template('dashboard.html', user=current_user, show_motd=show_motd)
    
    @app.route('/login', methods=['GET', 'POST'])
    @limiter.limit("10 per minute")  # Protect against brute force attacks
    def login():
        """Login page."""
        if current_user.is_authenticated:
            return redirect(url_for('index'))
        
        form = LoginForm()
        if form.validate_on_submit():
            user = User.query.filter_by(username=form.username.data).first()
            
            if user and user.check_password(form.password.data) and user.is_active:
                # Update last login time
                user.last_login = datetime.utcnow()
                db.session.commit()
                
                login_user(user, remember=form.remember_me.data)
                
                # Initialize session timeout tracking
                session['last_activity'] = datetime.utcnow().isoformat()
                session.permanent = True
                
                # Set flag to show MOTD after login
                session['show_motd'] = True
                
                # Redirect to next page or dashboard
                next_page = request.args.get('next')
                if next_page and next_page != url_for('about'):
                    return redirect(next_page)
                # Always redirect to dashboard for successful login
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password', 'error')
        
        return render_template('login.html', form=form)
    
    @app.route('/logout')
    @login_required
    def logout():
        """Logout route."""
        username = current_user.username
        logout_user()
        session.clear()  # Clear session data on logout
        flash(f'You have been logged out, {username}.', 'info')
        return redirect(url_for('login'))
    
    @app.route('/about')
    @login_required
    def about():
        """About page."""
        return render_template('about.html')
    
    @app.route('/maintenance')
    def maintenance():
        """Maintenance mode page - handled by before_request check."""
        return render_template('maintenance.html'), 503
    
    @app.route('/analysis')
    @login_required
    def analysis():
        """Precinct Analytics page with Dash charts and graphs."""
        if DASH_AVAILABLE:
            # Pass user ID as query parameter to Dash app for authentication
            return redirect(f'/dash/analytics/?user_id={current_user.id}')
        else:
            # Fallback to simple message if Dash is not available
            flash('Dash analytics is not available. Please install dash, plotly, and pandas packages.', 'warning')
            return redirect(url_for('index'))
    
    @app.route('/flippable', methods=['GET', 'POST'])
    @login_required
    def flippable_races():
        """Historical Race Analysis - Shows past races (2020-2024) by precinct with DVA assessment."""
        try:
            # Handle analysis navigation for admin/county users
            analysis_county = None
            analysis_precinct = None
            from_analysis = False
            
            if request.method == 'POST' and (current_user.is_admin or current_user.is_county):
                analysis_county = request.form.get('analysis_county')
                analysis_precinct = request.form.get('analysis_precinct')
                from_analysis = True
            
            # Determine which county and precinct to show
            if from_analysis:
                target_county = analysis_county
                target_precinct = analysis_precinct
            else:
                # Check if user has precinct information
                if not current_user.county or not current_user.precinct:
                    flash('Your county and precinct information is not set. Please contact an administrator to update your profile.', 'warning')
                    return redirect(url_for('index'))
                target_county = current_user.county
                target_precinct = current_user.precinct
            
            # Get flippable races from database filtered by target county and precinct
            # Normalize precinct format to handle inconsistencies between tables
            padded_precinct, unpadded_precinct = normalize_precinct_id(target_precinct)
            
            query = text('''
            SELECT county, precinct, contest_name, election_date,
                   dem_votes, oppo_votes, gov_votes, dem_margin, dva_pct_needed
            FROM flippable 
            WHERE UPPER(county) = UPPER(:county) 
            AND (precinct = :precinct_padded OR precinct = :precinct_unpadded)
            ORDER BY dem_margin DESC
            LIMIT 100
            ''')
            
            result = db.session.execute(query, {
                'county': target_county,
                'precinct_padded': padded_precinct,
                'precinct_unpadded': unpadded_precinct
            })
            races = result.fetchall()
            
            # Process races with assessment categories
            processed_races = []
            assessment_counts = {"🎯 SLAM DUNK": 0, "✅ HIGHLY FLIPPABLE": 0, "🟡 COMPETITIVE": 0, "🔴 STRETCH GOAL": 0}
            
            for race in races:
                # Safely extract values
                county = race[0] if race[0] else "Unknown"
                precinct = race[1] if race[1] else "Unknown"
                contest_name = race[2] if race[2] else "Unknown"
                election_date = race[3] if race[3] else "Unknown"
                dem_votes = race[4] if race[4] is not None else 0
                oppo_votes = race[5] if race[5] is not None else 0
                gov_votes = race[6] if race[6] is not None else 0
                dem_margin = race[7] if race[7] is not None else 0
                dva_pct_needed = race[8] if race[8] is not None else 999.9
                
                # Calculate vote gap and DVA metrics
                vote_gap = (oppo_votes + 1) - dem_votes
                dem_absenteeism = gov_votes - dem_votes if gov_votes > dem_votes else 0
                
                # Determine assessment category
                if vote_gap <= 25 or (dem_absenteeism > 0 and dva_pct_needed <= 15):
                    assessment = "🎯 SLAM DUNK"
                    effort_level = "Weekend volunteer effort"
                elif vote_gap <= 100 or (dem_absenteeism > 0 and dva_pct_needed <= 35):
                    assessment = "✅ HIGHLY FLIPPABLE"
                    effort_level = "Month-long focused campaign"
                elif vote_gap <= 300 or (dem_absenteeism > 0 and dva_pct_needed <= 60):
                    assessment = "🟡 COMPETITIVE"
                    effort_level = "Season-long strategic effort"
                else:
                    assessment = "🔴 STRETCH GOAL"
                    effort_level = "Multi-cycle investment"
                
                # Determine best pathway
                if vote_gap <= 100 and dem_absenteeism > 0 and dva_pct_needed <= 50:
                    best_pathway = "DVA" if dva_pct_needed < (vote_gap / max(oppo_votes, 1) * 100) else "Traditional"
                else:
                    best_pathway = "Traditional"
                
                assessment_counts[assessment] += 1
                
                processed_races.append({
                    'county': county,
                    'precinct': precinct,
                    'contest_name': contest_name,
                    'election_date': str(election_date),
                    'dem_votes': dem_votes,
                    'oppo_votes': oppo_votes,
                    'vote_gap': vote_gap,
                    'dva_pct_needed': dva_pct_needed,
                    'assessment': assessment,
                    'effort_level': effort_level,
                    'best_pathway': best_pathway
                })
            
            return render_template('flippable.html', 
                                 races=processed_races,
                                 assessment_counts=assessment_counts,
                                 show_back_to_analysis=from_analysis,
                                 target_county=target_county,
                                 target_precinct=target_precinct,
                                 user=current_user)
            
        except Exception as e:
            flash(f'Error loading flippable races: {str(e)}', 'error')
            return redirect(url_for('index'))

    @app.route('/flippable-analysis')
    @login_required
    def flippable_analysis():
        """Administrative Historical Race Analysis - County-wide overview of past races (2020-2024) for admin and county users."""
        # Restrict access to admin and county users only
        if not (current_user.is_admin or current_user.is_county):
            flash('Access denied. This page is available to administrators and county coordinators only.', 'error')
            return redirect(url_for('index'))
        
        try:
            # Determine scope based on user role
            if current_user.is_admin:
                # Admin sees all counties
                county_filter = None
                scope_description = "Statewide Analysis - All Counties"
            else:
                # County users see only their county
                county_filter = current_user.county
                scope_description = f"{current_user.county} County Analysis"
            
            # Build the base query
            base_query = '''
            SELECT county, precinct, contest_name, election_date,
                   dem_votes, oppo_votes, gov_votes, dem_margin, dva_pct_needed,
                   COUNT(*) as race_count
            FROM flippable 
            '''
            
            if county_filter:
                base_query += 'WHERE UPPER(county) = UPPER(:county) '
            
            # Get summary statistics by county and precinct
            summary_query = base_query + '''
            GROUP BY county, precinct, contest_name, election_date, dem_votes, oppo_votes, gov_votes, dem_margin, dva_pct_needed
            ORDER BY county, precinct, dem_margin DESC
            '''
            
            # Execute query
            if county_filter:
                result = db.session.execute(text(summary_query), {'county': county_filter})
            else:
                result = db.session.execute(text(summary_query))
            
            races = result.fetchall()
            
            # Process races and create summaries
            county_summaries = {}
            precinct_summaries = {}  # New: Group by county-precinct combination
            total_assessment_counts = {"🎯 SLAM DUNK": 0, "✅ HIGHLY FLIPPABLE": 0, "🟡 COMPETITIVE": 0, "🔴 STRETCH GOAL": 0}
            
            for race in races:
                county = race[0] if race[0] else "Unknown"
                precinct = race[1] if race[1] else "Unknown"
                contest_name = race[2] if race[2] else "Unknown"
                election_date = race[3] if race[3] else "Unknown"
                dem_votes = race[4] if race[4] is not None else 0
                oppo_votes = race[5] if race[5] is not None else 0
                gov_votes = race[6] if race[6] is not None else 0
                dem_margin = race[7] if race[7] is not None else 0
                dva_pct_needed = race[8] if race[8] is not None else 999.9
                
                # Calculate metrics
                vote_gap = (oppo_votes + 1) - dem_votes
                dem_absenteeism = gov_votes - dem_votes if gov_votes > dem_votes else 0
                
                # Determine assessment category
                if vote_gap <= 25 or (dem_absenteeism > 0 and dva_pct_needed <= 15):
                    assessment = "🎯 SLAM DUNK"
                elif vote_gap <= 100 or (dem_absenteeism > 0 and dva_pct_needed <= 35):
                    assessment = "✅ HIGHLY FLIPPABLE"
                elif vote_gap <= 300 or (dem_absenteeism > 0 and dva_pct_needed <= 60):
                    assessment = "🟡 COMPETITIVE"
                else:
                    assessment = "🔴 STRETCH GOAL"
                
                total_assessment_counts[assessment] += 1
                
                # Initialize county summary if needed
                if county not in county_summaries:
                    county_summaries[county] = {
                        "🎯 SLAM DUNK": 0, "✅ HIGHLY FLIPPABLE": 0, "🟡 COMPETITIVE": 0, "🔴 STRETCH GOAL": 0,
                        'total_races': 0, 'total_vote_gap': 0, 'avg_dva': 0, 'dva_count': 0
                    }
                
                county_summaries[county][assessment] += 1
                county_summaries[county]['total_races'] += 1
                county_summaries[county]['total_vote_gap'] += vote_gap
                if dva_pct_needed < 999:
                    county_summaries[county]['avg_dva'] += dva_pct_needed
                    county_summaries[county]['dva_count'] += 1
                
                # Group by precinct - key is county-precinct combination
                precinct_key = f"{county}-{precinct}"
                if precinct_key not in precinct_summaries:
                    precinct_summaries[precinct_key] = {
                        'county': county,
                        'precinct': precinct,
                        "🎯 SLAM DUNK": 0, "✅ HIGHLY FLIPPABLE": 0, "🟡 COMPETITIVE": 0, "🔴 STRETCH GOAL": 0,
                        'total_races': 0, 'total_vote_gap': 0, 'avg_dva': 0, 'dva_count': 0,
                        'races': []  # Store individual races for detail view
                    }
                
                precinct_summaries[precinct_key][assessment] += 1
                precinct_summaries[precinct_key]['total_races'] += 1
                precinct_summaries[precinct_key]['total_vote_gap'] += vote_gap
                if dva_pct_needed < 999:
                    precinct_summaries[precinct_key]['avg_dva'] += dva_pct_needed
                    precinct_summaries[precinct_key]['dva_count'] += 1
                
                # Add individual race details
                precinct_summaries[precinct_key]['races'].append({
                    'contest_name': contest_name,
                    'election_date': str(election_date),
                    'dem_votes': dem_votes,
                    'oppo_votes': oppo_votes,
                    'vote_gap': vote_gap,
                    'dva_pct_needed': round(dva_pct_needed, 1) if dva_pct_needed < 999 else 'N/A',
                    'assessment': assessment,
                    'dem_margin': dem_margin
                })
            
            # Calculate averages for county summaries
            for county in county_summaries:
                if county_summaries[county]['dva_count'] > 0:
                    county_summaries[county]['avg_dva'] = round(
                        county_summaries[county]['avg_dva'] / county_summaries[county]['dva_count'], 1
                    )
                else:
                    county_summaries[county]['avg_dva'] = 'N/A'
            
            # Calculate averages for precinct summaries
            for precinct_key in precinct_summaries:
                if precinct_summaries[precinct_key]['dva_count'] > 0:
                    precinct_summaries[precinct_key]['avg_dva'] = round(
                        precinct_summaries[precinct_key]['avg_dva'] / precinct_summaries[precinct_key]['dva_count'], 1
                    )
                else:
                    precinct_summaries[precinct_key]['avg_dva'] = 'N/A'
            
            # Sort precincts by county then precinct number (numeric sorting with zero-padded display)
            def sort_key(item):
                county = item[1]['county']
                precinct = item[1]['precinct']
                # Convert precinct to integer for numeric sorting, fallback to 999999 for non-numeric
                try:
                    precinct_num = int(precinct)
                except (ValueError, TypeError):
                    precinct_num = 999999  # Put non-numeric precincts at the end
                return (county, precinct_num)
            
            sorted_precincts = sorted(precinct_summaries.items(), key=sort_key)
            
            # Zero-pad precinct numbers for display
            for precinct_key, precinct_data in sorted_precincts:
                try:
                    # Zero-pad numeric precincts to 3 digits
                    precinct_num = int(precinct_data['precinct'])
                    precinct_data['precinct'] = f"{precinct_num:03d}"
                except (ValueError, TypeError):
                    # Leave non-numeric precincts as-is
                    pass
            
            return render_template('flippable_analysis.html', 
                                 county_summaries=county_summaries,
                                 precinct_summaries=sorted_precincts,
                                 total_assessment_counts=total_assessment_counts,
                                 scope_description=scope_description,
                                 user=current_user)
                                 
        except Exception as e:
            flash(f'Error loading flippable races analysis: {str(e)}', 'error')
            return redirect(url_for('index'))
    
    @app.route('/clustering')
    @login_required
    def clustering_analysis():
        """Clustering Analysis dashboard page."""
        from services.clustering_service import ClusteringService
        
        clustering_service = ClusteringService()
        
        # Determine county filter for non-admin users
        county_filter = None
        if not current_user.is_admin and current_user.county:
            county_filter = current_user.county
        
        # Load clustering data (filtered by county for non-admin users)
        precinct_loaded = clustering_service.load_precinct_clustering_data(county_filter=county_filter)
        census_loaded = clustering_service.load_census_clustering_data()
        
        if not precinct_loaded:
            flash('Precinct clustering data not available. Please run clustering analysis first.', 'warning')
            return redirect(url_for('index'))
        
        # Get user-specific insights
        user_insights = clustering_service.get_user_precinct_insights(current_user)
        
        # Get cluster summary (personalized if user has precinct data)
        user_cluster = None
        if user_insights and 'comprehensive_cluster' in user_insights:
            user_cluster = user_insights['comprehensive_cluster']
        
        cluster_summary = clustering_service.get_cluster_summary(user_cluster=user_cluster)
        
        # Get county insights if user has county
        county_insights = None
        if current_user.county:
            county_insights = clustering_service.get_county_insights(current_user.county)
        
        return render_template('clustering.html', 
                             user=current_user,
                             user_insights=user_insights,
                             cluster_summary=cluster_summary,
                             county_insights=county_insights,
                             census_available=census_loaded)

    @app.route('/demographic-clustering', endpoint='demographic_clustering')
    @login_required
    def demographic_clustering():
        """County-wide Demographic Clustering Analysis - Admin and county users only."""
        # Restrict access to admin and county users only
        if not (current_user.is_admin or current_user.is_county):
            flash('Access denied. This page is available to administrators and county coordinators only.', 'error')
            return redirect(url_for('index'))
        
        try:
            # Load precinct clustering data for precinct distribution analysis
            from services.clustering_service import ClusteringService
            clustering_service = ClusteringService()
            county_filter = None if current_user.is_admin else current_user.county
            precinct_loaded = clustering_service.load_precinct_clustering_data(county_filter=county_filter)
            
            # Get scope description - demographics clustering is always county-specific
            scope_description = f"{current_user.county} County"
            
            # Organize precincts by clustering results if data is available
            precinct_distribution = {}
            if precinct_loaded and clustering_service.precinct_data is not None:
                import pandas as pd
                df = clustering_service.precinct_data
                
                # Group precincts by comprehensive cluster
                cluster_groups = df.groupby('comprehensive_cluster')
                for cluster_id, group in cluster_groups:
                    precinct_list = group['precinct'].tolist()
                    avg_flippability = group['flippability_score'].mean()
                    avg_dem_pct = group['dem_pct'].mean()
                    
                    precinct_distribution[cluster_id] = {
                        'precincts': precinct_list,
                        'count': len(precinct_list),
                        'avg_flippability': round(avg_flippability, 2),
                        'avg_dem_pct': round(avg_dem_pct, 1),
                        'description': f"Cluster {cluster_id}"
                    }
            
            # Census tract clustering data (based on the analysis document)
            clustering_data = {
                'overview': {
                    'total_tracts': 94,
                    'county': 'Forsyth',
                    'state': 'North Carolina',
                    'population_range': {'min': 1217, 'max': 8393},
                    'income_range': {'min': 17076, 'max': 168125},
                    'analysis_date': 'October 21, 2025'
                },
                'population_housing': {
                    'clusters': 4,
                    'silhouette_score': 0.285,
                    'distribution': [
                        {'id': 0, 'tracts': 4, 'avg_pop': 4778, 'description': 'High population areas'},
                        {'id': 1, 'tracts': 50, 'avg_pop': 3592, 'description': 'Largest cluster'},
                        {'id': 2, 'tracts': 18, 'avg_pop': 6416, 'description': 'Highest population density'},
                        {'id': 3, 'tracts': 22, 'avg_pop': 3016, 'description': 'Lower population areas'}
                    ]
                },
                'economic': {
                    'clusters': 5,
                    'silhouette_score': 0.328,
                    'distribution': [
                        {'id': 0, 'tracts': 16, 'avg_income': 95336, 'description': 'High-income areas'},
                        {'id': 1, 'tracts': 34, 'avg_income': 50344, 'description': 'Largest middle-income group'},
                        {'id': 2, 'tracts': 13, 'avg_income': 36852, 'description': 'Lower-middle income'},
                        {'id': 3, 'tracts': 30, 'avg_income': 79481, 'description': 'Upper-middle income'},
                        {'id': 4, 'tracts': 1, 'avg_income': 36574, 'description': 'Single low-income outlier'}
                    ]
                },
                'education': {
                    'clusters': 4,
                    'silhouette_score': 0.469,
                    'distribution': [
                        {'id': 0, 'tracts': 10, 'education_rate': 52.6, 'description': 'Highly educated'},
                        {'id': 1, 'tracts': 55, 'education_rate': 14.6, 'description': 'Largest, lower education'},
                        {'id': 2, 'tracts': 25, 'education_rate': 30.4, 'description': 'Moderate education'},
                        {'id': 3, 'tracts': 4, 'education_rate': 38.8, 'description': 'Above-average education'}
                    ]
                },
                'geographic': {
                    'clusters': 6,
                    'silhouette_score': 0.332,
                    'distribution': [
                        {'id': 0, 'tracts': 21, 'latitude': 36.153, 'description': 'Northern area'},
                        {'id': 1, 'tracts': 17, 'latitude': 36.098, 'description': 'South-central area'},
                        {'id': 2, 'tracts': 3, 'latitude': 36.150, 'description': 'Small northern cluster'},
                        {'id': 3, 'tracts': 6, 'latitude': 36.210, 'description': 'Northernmost area'},
                        {'id': 4, 'tracts': 14, 'latitude': 36.037, 'description': 'Southern area'},
                        {'id': 5, 'tracts': 33, 'latitude': 36.090, 'description': 'Largest geographic cluster'}
                    ]
                },
                'strategic_insights': {
                    'high_opportunity': {
                        'high_income_tracts': 19,
                        'remote_work_hotspots': 19,
                        'highly_educated_areas': 19,
                        'high_density_tracts': 19
                    },
                    'targeting_strategies': [
                        {
                            'category': 'High-Education Areas',
                            'tracts': 10,
                            'rate': 52.6,
                            'strategy': 'Policy-focused messaging, detailed position papers',
                            'demographics': 'Likely engaged voters, responsive to complex issues'
                        },
                        {
                            'category': 'High-Income Areas',
                            'tracts': 16,
                            'income': 95000,
                            'strategy': 'Economic stability messaging, tax policy focus',
                            'demographics': 'Homeowners, established community members'
                        },
                        {
                            'category': 'Remote Work Hotspots',
                            'tracts': 19,
                            'strategy': 'Technology policy, work-life balance issues',
                            'demographics': 'Professional class, flexible schedules'
                        }
                    ]
                }
            }
            
            return render_template('demographic_clustering.html', 
                                 clustering_data=clustering_data,
                                 precinct_distribution=precinct_distribution,
                                 scope_description=scope_description,
                                 user=current_user)
                                 
        except Exception as e:
            flash(f'Error loading demographic clustering analysis: {str(e)}', 'error')
            return redirect(url_for('index'))

    @app.route('/website-users')
    @login_required
    def website_user_report():
        """Website User Report - Admin and County users only."""
        # Restrict access to admin and county users only
        if not (current_user.is_admin or current_user.is_county):
            flash('Access denied. This feature is only available to administrators and county coordinators.', 'error')
            return redirect(url_for('index'))
        
        try:
            # Determine filter scope based on user permissions
            if current_user.is_admin:
                # Admin users: can see all users in their state
                base_query = User.query.filter_by(state=current_user.state)
                scope_description = f"All {current_user.state} Users"
            else:  # is_county
                # County users: filter by state and county
                base_query = User.query.filter_by(state=current_user.state, county=current_user.county)
                scope_description = f"{current_user.county} County Users"
            
            # Get user statistics
            total_users = base_query.count()
            admin_users = base_query.filter_by(is_admin=True).count()
            county_users = base_query.filter_by(is_county=True, is_admin=False).count()
            regular_users = total_users - admin_users - county_users
            active_users = base_query.filter_by(is_active=True).count()
            inactive_users = total_users - active_users
            
            # Get recent users (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_users = base_query.filter(User.created_at >= thirty_days_ago).count()
            
            # Get monthly signup data for chart (last 12 months)
            monthly_signups = []
            monthly_labels = []
            for i in range(11, -1, -1):  # Last 12 months, newest first
                month_start = datetime.utcnow().replace(day=1) - timedelta(days=32*i)
                month_start = month_start.replace(day=1)
                if i == 0:
                    month_end = datetime.utcnow()
                else:
                    month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)
                
                month_users = base_query.filter(
                    User.created_at >= month_start,
                    User.created_at <= month_end
                ).count()
                
                monthly_signups.append(month_users)
                monthly_labels.append(month_start.strftime('%b %Y'))
            
            # Get all precincts in county and user distribution
            precinct_distribution = {}
            if current_user.county:
                # First, get all precincts that exist in the county from the precincts table
                all_precincts_query = text('''
                    SELECT DISTINCT precinct 
                    FROM precincts 
                    WHERE UPPER(county) = UPPER(:county) 
                    ORDER BY precinct
                ''')
                all_precincts = db.session.execute(all_precincts_query, {'county': current_user.county}).fetchall()
                
                # Initialize all precincts with 0 users
                for precinct_row in all_precincts:
                    precinct = precinct_row[0]
                    precinct_distribution[precinct] = 0
                
                # If no precincts found in precincts table, fall back to candidate_vote_results
                if not precinct_distribution:
                    fallback_query = text('''
                        SELECT DISTINCT precinct 
                        FROM candidate_vote_results 
                        WHERE UPPER(county) = UPPER(:county) 
                        ORDER BY precinct
                    ''')
                    fallback_precincts = db.session.execute(fallback_query, {'county': current_user.county}).fetchall()
                    for precinct_row in fallback_precincts:
                        precinct = precinct_row[0]
                        precinct_distribution[precinct] = 0
                
                # Now count actual users by precinct
                precinct_query = base_query.filter(User.precinct.isnot(None))
                for user in precinct_query.all():
                    if user.precinct:
                        # Handle both padded and unpadded precinct formats
                        user_precinct = str(user.precinct).strip()
                        padded_precinct = user_precinct.zfill(3)
                        
                        # Check if user's precinct (padded or unpadded) matches any known precinct
                        if user_precinct in precinct_distribution:
                            precinct_distribution[user_precinct] += 1
                        elif padded_precinct in precinct_distribution:
                            precinct_distribution[padded_precinct] += 1
                        else:
                            # If precinct format doesn't match, add it anyway
                            precinct_distribution[user_precinct] = precinct_distribution.get(user_precinct, 0) + 1
            
            user_stats = {
                'total': total_users,
                'admin': admin_users,
                'county': county_users,
                'regular': regular_users,
                'active': active_users,
                'inactive': inactive_users,
                'recent': recent_users,
                'scope_description': scope_description,
                'precinct_distribution': dict(sorted(precinct_distribution.items())),
                'monthly_signups': {
                    'labels': monthly_labels,
                    'data': monthly_signups
                }
            }
            
            return render_template('website_user_report.html', 
                                 user_stats=user_stats,
                                 user=current_user)
            
        except Exception as e:
            flash(f'Error loading user report: {str(e)}', 'error')
            return redirect(url_for('index'))

    @app.route('/api/clustering/data')
    @login_required
    def clustering_data_api():
        """API endpoint for clustering data (for charts)."""
        from services.clustering_service import ClusteringService
        
        clustering_service = ClusteringService()
        
        # Determine county filter for non-admin users
        county_filter = None
        if not current_user.is_admin and current_user.county:
            county_filter = current_user.county
        
        if not clustering_service.load_precinct_clustering_data(county_filter=county_filter):
            return jsonify({'error': 'Clustering data not available'}), 404
        
        # Return data for charts (already filtered by county during load)
        data = clustering_service.get_chart_data()
        if data is None:
            return jsonify({'error': 'No clustering data available for your county'}), 404
            
        return jsonify(data)

    @app.route('/precinct_clustering_results.csv')
    @login_required
    def download_clustering_csv():
        """Download clustering results CSV file filtered by user's county."""
        from services.clustering_service import ClusteringService
        import tempfile
        from flask import after_this_request
        
        clustering_service = ClusteringService()
        
        # Determine county filter for non-admin users
        county_filter = None
        if not current_user.is_admin and current_user.county:
            county_filter = current_user.county
        
        if not clustering_service.load_precinct_clustering_data(county_filter=county_filter):
            abort(404, description="Clustering data not available")
        
        if clustering_service.precinct_data is None or clustering_service.precinct_data.empty:
            abort(404, description="No clustering data available for your county")
        
        # Create temporary CSV file with filtered data
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.csv') as temp_file:
            clustering_service.precinct_data.to_csv(temp_file.name, index=False)
            temp_file_path = temp_file.name
        
        # Determine download filename
        download_name = f"precinct_clustering_results_{county_filter}.csv" if county_filter else "precinct_clustering_results.csv"
        
        # Clean up temporary file after sending
        @after_this_request
        def remove_file(response):
            try:
                os.remove(temp_file_path)
            except Exception:
                pass
            return response
        
        return send_file(temp_file_path, 
                        as_attachment=True, 
                        download_name=download_name,
                        mimetype='text/csv')
    
    @app.route('/doc/<filename>')
    @login_required
    def serve_documentation(filename):
        """Serve documentation files from the doc directory."""
        # Security: only allow .md files
        if not filename.endswith('.md'):
            abort(404)
        
        # Security: prevent directory traversal
        if '..' in filename or '/' in filename:
            abort(404)
        
        # Visibility check - only allow files starting with uppercase letter (unless admin)
        if not current_user.is_admin and not filename[0].isupper():
            abort(404)
        
        doc_path = os.path.join(app.root_path, 'doc', filename)
        if not os.path.exists(doc_path):
            abort(404, description=f"Documentation file '{filename}' not found")
        
        return send_file(doc_path, 
                        mimetype='text/markdown',
                        as_attachment=False)
    
    @app.route('/profile')
    @login_required
    def profile():
        """User profile page."""
        return render_template('profile.html', user=current_user)
    
    @app.route('/admin/motd', methods=['GET', 'POST'])
    @login_required
    def admin_motd():
        """Admin page to edit message of the day (Markdown format)."""
        if not current_user.is_admin:
            flash('Access denied. Administrator access required.', 'error')
            return redirect(url_for('index'))
        
        motd_path = os.path.join(app.root_path, 'motd.md')
        
        if request.method == 'POST':
            motd_content = request.form.get('motd_content', '').strip()
            try:
                with open(motd_path, 'w', encoding='utf-8') as f:
                    f.write(motd_content)
                flash('Message of the Day updated successfully!', 'success')
            except Exception as e:
                flash(f'Error updating MOTD: {str(e)}', 'error')
            return redirect(url_for('admin_motd'))
        
        # GET request - display the form
        # Read raw markdown content for editing
        try:
            if os.path.exists(motd_path):
                with open(motd_path, 'r', encoding='utf-8') as f:
                    current_motd = f.read().strip()
            else:
                current_motd = ''
        except:
            current_motd = ''
        
        return render_template('admin_motd.html', current_motd=current_motd)
    
    @app.route('/static-content')
    @login_required
    def static_content():
        """Display list of available maps with filenames from NC database but view/new tab using local maps table. Admin and county access."""
        if not (current_user.is_admin or current_user.is_county):
            flash('Access denied. Maps are available to administrators and county users only.', 'error')
            return redirect(url_for('index'))
        
        html_files = []
        
        # Get maps from NC PostgreSQL database only - no fallbacks
        try:
            if not current_user.county:
                app.logger.error(f'User {current_user.username} has no county assigned')
                flash('Your county information is not set. Please contact an administrator.', 'error')
                return redirect(url_for('profile'))
            
            # Get maps for the current user's county from NC database
            nc_maps = Map.get_map_filenames_for_county(current_user.county)
            app.logger.info(f'Found {len(nc_maps)} maps from NC database for county: {current_user.county}')
            
            if not nc_maps:
                app.logger.error(f'No maps found in NC database for county: {current_user.county}')
                flash(f'No maps found for county: {current_user.county}. This is a database error.', 'error')
                return redirect(url_for('index'))
            
            for nc_map in nc_maps:
                if not nc_map.get('map_content'):
                    app.logger.error(f'Map content missing for precinct {nc_map["precinct"]} in county {current_user.county}')
                    # Still show the map but mark it as having an error
                    has_content = False
                else:
                    has_content = True
                
                html_files.append({
                    'name': nc_map['filename'],
                    'display_name': nc_map['display_name'],
                    'size': nc_map.get('size', 0),
                    'modified': nc_map.get('modified', datetime.utcnow()),
                    'source': 'nc_database',
                    'precinct': nc_map['precinct'],
                    'has_content': has_content,
                    'map_id': nc_map.get('map_id')
                })
                
        except Exception as e:
            app.logger.error(f'Critical error accessing NC database: {str(e)}')
            flash('Database error: Unable to access map data. Please contact technical support.', 'error')
            return redirect(url_for('index'))
        
        html_files.sort(key=lambda x: (x.get('source', 'static'), x['name']))
        return render_template('static_content.html', files=html_files)
    
    @app.route('/static-content/<filename>')
    @login_required
    @limiter.limit("100 per hour")  # Limit file access to prevent excessive downloads
    def view_static_content(filename):
        """Display a specific map file with navbar. Available to all authenticated users."""
        # Check access permissions using the new helper function
        if not (current_user.is_admin or current_user.is_county):
            if not user_can_access_map(current_user, filename):
                flash('Access denied. You can only view your assigned map.', 'error')
                return redirect(url_for('index'))
        
        # Try to get map content from database first, then fall back to static files
        map_content = get_map_content_by_filename(filename)
        if not map_content:
            abort(404)
        
        return render_template('static_viewer.html', 
                             filename=filename,
                             display_name=filename.replace('.html', '').replace('_', ' ').title(),
                             is_public_view=not (current_user.is_admin or current_user.is_county))
    
    @app.route('/static-content-raw/<filename>')
    @login_required
    @limiter.limit("100 per hour")  # Limit raw file access
    def view_static_content_raw(filename):
        """Serve raw HTML file content for iframe display. Available to all authenticated users."""
        # Allow all authenticated users to view static content
        # For non-admin users, they can only access via direct links (not browse the library)
        
        # Try to get map content from database first, then fall back to static files
        content = get_map_content_by_filename(filename)
        if content is None:
            # Neither database nor static file found
            error_content = create_error_page("Map Not Found", 
                f"The requested map '{filename}' could not be found in the database or static files.")
            return error_content, 404
        
        # Content found (either valid content or error page from database issues)
        return content
    
    @app.route('/view/<filename>')
    @login_required
    @limiter.limit("100 per hour")  # Limit new tab file access
    def view_file_new_tab(filename):
        """Open map file directly in new tab with close button. Available to all authenticated users."""
        # Try to get map content from database first, then fall back to static files
        content = get_map_content_by_filename(filename)
        if content is None:
            # Neither database nor static file found
            error_content = create_error_page("Map Not Found", 
                f"The requested map '{filename}' could not be found in the database or static files.")
            return error_content, 404
        
        # Add close button and zoom controls to the content
        try:
            
            # Add a close window button to the map content
            close_button = '''
<div style="position: fixed; top: 10px; right: 10px; z-index: 9999;">
    <button onclick="closeWindow()" 
       style="background: #dc3545; color: white; padding: 8px 16px; border: none; 
              border-radius: 4px; font-family: Arial, sans-serif; font-size: 14px;
              box-shadow: 0 2px 4px rgba(0,0,0,0.2); cursor: pointer; display: inline-block;
              transition: background-color 0.2s;"
       onmouseover="this.style.backgroundColor='#c82333'"
       onmouseout="this.style.backgroundColor='#dc3545'">
        ✕ Close Window
    </button>
</div>
<script>
function closeWindow() {
    // Try to close the window
    if (window.opener) {
        window.close();
    } else {
        // If not opened by another window, try alternative methods
        window.close();
        // Fallback for browsers that don't allow window.close()
        setTimeout(function() {
            window.location.href = 'about:blank';
        }, 100);
    }
}
</script>
            '''
            
            # Enhanced zoom controls for new tab view
            enhanced_zoom_controls = '''
<!-- Enhanced Zoom Controls for New Tab -->
<div class="new-tab-zoom-controls" style="position: fixed; top: 20px; left: 20px; z-index: 9999; display: flex; flex-direction: column; gap: 8px;">
    <div style="background: rgba(255,255,255,0.95); padding: 8px; border-radius: 8px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); border: 2px solid #007bff;">
        <div style="display: flex; flex-direction: column; gap: 4px;">
            <button onclick="zoomIn()" style="width: 60px; height: 35px; background: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold; transition: background 0.2s;" onmouseover="this.style.backgroundColor='#218838'" onmouseout="this.style.backgroundColor='#28a745'" title="Zoom In (Ctrl/Cmd + Plus)">+</button>
            <button onclick="zoomOut()" style="width: 60px; height: 35px; background: #dc3545; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 16px; font-weight: bold; transition: background 0.2s;" onmouseover="this.style.backgroundColor='#c82333'" onmouseout="this.style.backgroundColor='#dc3545'" title="Zoom Out (Ctrl/Cmd + Minus)">−</button>
            <button onclick="resetZoom()" style="width: 60px; height: 30px; background: #17a2b8; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 10px; font-weight: bold; transition: background 0.2s;" onmouseover="this.style.backgroundColor='#138496'" onmouseout="this.style.backgroundColor='#17a2b8'" title="Reset Zoom (Ctrl/Cmd + 0)">Reset</button>
        </div>
    </div>
</div>
            '''
            
            # Insert close button and zoom controls after the opening <body> tag
            if '<body>' in content:
                content = content.replace('<body>', '<body>' + close_button + enhanced_zoom_controls)
            else:
                # If no <body> tag found, add it at the beginning
                content = close_button + enhanced_zoom_controls + content
            
            return content
        except Exception as e:
            return f'<html><body><h1>Error</h1><p>Error reading file: {str(e)}</p></body></html>', 500
    
    @app.route('/user-map/<filename>')
    @login_required
    @limiter.limit("100 per hour")  # Limit user map access
    def view_user_map(filename):
        """Display user's map file with navbar. Shows current user's map or any map for admins."""
        # Check access permissions using new helper function
        if not user_can_access_map(current_user, filename):
            flash('Access denied. You can only view your assigned map.', 'error')
            return redirect(url_for('profile'))
        
        # Try to get map content from database first, then fall back to static files
        map_content = get_map_content_by_filename(filename)
        if not map_content:
            abort(404)
        
        return render_template('static_viewer.html', 
                             filename=filename,
                             display_name=filename.replace('.html', '').replace('_', ' ').title(),
                             is_user_map=True)
    
    @app.route('/user-map-raw/<filename>')
    @login_required
    @limiter.limit("100 per hour")  # Limit raw user map access
    def view_user_map_raw(filename):
        """Serve raw HTML file content for user's map iframe display with zoom control support."""
        # Check access permissions using new helper function
        if not user_can_access_map(current_user, filename):
            return '<html><body><h1>Access Denied</h1><p>You can only view your assigned map.</p></body></html>', 403
        
        # Try to get map content from database first, then fall back to static files
        content = get_map_content_by_filename(filename)
        if not content:
            abort(404)
        
        # Add zoom control support to the content
        try:
            
            # Add message listener for zoom controls to work with sidebar
            zoom_message_listener = '''
<script>
// Message listener for sidebar zoom controls
window.addEventListener('message', function(event) {
    if (event.data && event.data.action) {
        switch(event.data.action) {
            case 'zoomIn':
                if (window.map && window.map.zoomIn) {
                    window.map.zoomIn();
                }
                break;
            case 'zoomOut':
                if (window.map && window.map.zoomOut) {
                    window.map.zoomOut();
                }
                break;
            case 'resetZoom':
                if (window.map && window.map.setView) {
                    // Reset to initial map view - you may need to adjust these coordinates
                    window.map.setView([39.8283, -98.5795], 4); // Default US center view
                }
                break;
        }
    }
});

// Make map globally accessible for zoom controls
document.addEventListener('DOMContentLoaded', function() {
    // Wait for Leaflet map to be initialized
    setTimeout(function() {
        // Try to find the map instance
        if (typeof map !== 'undefined') {
            window.map = map;
        } else {
            // If map variable not found, try to find it in the window object
            for (let key in window) {
                if (window[key] && typeof window[key] === 'object' && 
                    window[key].hasOwnProperty('_container') && 
                    window[key]._container && window[key]._container.classList.contains('leaflet-container')) {
                    window.map = window[key];
                    break;
                }
            }
        }
    }, 1000);
});
</script>
            '''
            
            # Insert message listener before closing </body> tag
            if '</body>' in content:
                content = content.replace('</body>', zoom_message_listener + '</body>')
            else:
                # If no </body> tag found, add it at the end
                content = content + zoom_message_listener
            
            return content
        except Exception as e:
            return f'<html><body><h1>Error</h1><p>Error reading file: {str(e)}</p></body></html>', 500
    
    # Rate limiting error handler
    @app.errorhandler(429)
    def ratelimit_handler(e):
        """Handle rate limit exceeded errors."""
        if current_user.is_authenticated and hasattr(current_user, 'created_at'):
            flash('Rate limit exceeded. Please try again later.', 'warning')
            return render_template('dashboard.html', user=current_user), 429
        else:
            # For unauthenticated users or users without full attributes, redirect to login
            return render_template('login.html', form=LoginForm()), 429
    
    def init_db():
        """Initialize database with tables and create admin user if none exists."""
        db.create_all()
        
        # Create admin user if no users exist
        if User.query.count() == 0:
            from flask import current_app
            admin_user = User(
                username=current_app.config['DEFAULT_ADMIN_USERNAME'],
                email=current_app.config['DEFAULT_ADMIN_EMAIL'],
                password=current_app.config['DEFAULT_ADMIN_PASSWORD'],
                phone='555-ADMIN',  # Required field
                role='Administrator',  # Required field
                is_admin=True
            )
            db.session.add(admin_user)
            db.session.commit()
            print(f"Created default admin user: {current_app.config['DEFAULT_ADMIN_USERNAME']}/{current_app.config['DEFAULT_ADMIN_PASSWORD']}")
    
    @app.route('/my-map')
    @login_required
    @limiter.limit("100 per hour")  # Limit user map access
    def view_my_map():
        """Display the current user's map based on their state, county, and precinct."""
        if not current_user.state or not current_user.county or not current_user.precinct:
            flash('Your location information is not complete. Please contact an administrator to update your profile.', 'warning')
            return redirect(url_for('profile'))
        
        # Get the user's map from database
        map_content = get_map_content_for_user(current_user)
        if map_content is None:
            flash(f'No map found for {current_user.state} {current_user.county} Precinct {current_user.precinct}.', 'info')
            return redirect(url_for('index'))
        elif 'Database Error' in map_content and '<div class="error-container">' in map_content:
            # Database error occurred, show error message
            flash('There was an error retrieving your map from the database. Please try again or contact support.', 'error')
            return redirect(url_for('index'))
        
        # Create a zero-padded filename for display purposes
        padded_precinct = current_user.precinct.zfill(3)
        filename = f"{padded_precinct}.html"
        return render_template('static_viewer.html', 
                             filename=filename,
                             display_name=f"{current_user.state} {current_user.county} Precinct {current_user.precinct}",
                             is_user_map=True)
    
    @app.route('/my-map-raw')
    @login_required
    @limiter.limit("100 per hour")  # Limit raw user map access
    def view_my_map_raw():
        """Serve raw HTML content for the current user's map."""
        if not current_user.state or not current_user.county or not current_user.precinct:
            return '<html><body><h1>Error</h1><p>Location information not available.</p></body></html>', 400
        
        # Get the user's map from database
        content = get_map_content_for_user(current_user)
        if content is None:
            error_content = create_error_page("Map Not Found", 
                f"No map available for {current_user.state} {current_user.county} Precinct {current_user.precinct}.")
            return error_content, 404
        
        # Add zoom control support
        zoom_message_listener = '''
<script>
// Message listener for sidebar zoom controls
window.addEventListener('message', function(event) {
    if (event.data && event.data.action) {
        switch(event.data.action) {
            case 'zoomIn':
                if (window.map && window.map.zoomIn) {
                    window.map.zoomIn();
                }
                break;
            case 'zoomOut':
                if (window.map && window.map.zoomOut) {
                    window.map.zoomOut();
                }
                break;
            case 'resetZoom':
                if (window.map && window.map.setView) {
                    window.map.setView([39.8283, -98.5795], 4);
                }
                break;
        }
    }
});
</script>
        '''
        
        # Insert zoom controls before closing </body> tag
        if '</body>' in content:
            content = content.replace('</body>', zoom_message_listener + '</body>')
        else:
            content = content + zoom_message_listener
        
        return content

    # File protection - block direct access to sensitive files
    @app.route('/<path:filename>')
    def catch_all_files(filename):
        """Catch all route to prevent direct file access."""
        # Block sensitive file extensions
        blocked_extensions = [
            '.py', '.pyc', '.pyo', '.pyd',  # Python files
            '.env', '.ini', '.cfg', '.conf',  # Config files  
            '.log', '.sql', '.backup', '.bak', '.old', '.tmp',  # Data files
            '.git', '.svn', '.hg',  # Version control
            '.json', '.yml', '.yaml', '.xml'  # Data files
        ]
        
        # Block sensitive directories/files
        blocked_patterns = [
            '__pycache__', '.venv', 'venv', 'node_modules',
            'config', 'logs', 'backup', 'migrations',
            'requirements.txt', 'wsgi.py', 'main.py', 'models.py'
        ]
        
        # Check file extension
        for ext in blocked_extensions:
            if filename.lower().endswith(ext):
                abort(404)
        
        # Check blocked patterns
        for pattern in blocked_patterns:
            if pattern in filename.lower():
                abort(404)
        
        # If it's not a blocked file, let Flask handle it normally
        # This will result in a 404 for non-existent routes
        abort(404)

    # Initialize database
    with app.app_context():
        init_db()
    
    return app

def main():
    """Run the Flask application."""
    app = create_app()
    # Get debug setting from config, not hardcoded
    debug_mode = app.config.get('DEBUG', False)
    port = app.config.get('FLASK_PORT', 5000)
    app.run(debug=debug_mode, host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()
