import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email
from models import db, User, Map
from datetime import datetime
from config import get_config
try:
    from dash_analytics import create_dash_app
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False
# TODP: CSRF
# TODO: research HSTS and CSP via Flask-Talisman, X-Frame-Options deny
# TODO: turn off DEBUG
# TODO: research Auth0 for MFA

class LoginForm(FlaskForm):
    """Login form for user authentication."""
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')

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
    column_details_list = ['id', 'username', 'email', 'password', 'phone', 'role', 'precinct', 'state', 'county', 'map', 'notes', 'is_admin', 'is_county', 'is_active', 'created_at', 'last_login']
    
    # Define form field order - username first, then password as unique field, followed by contact and role info
    form_columns = ['username', 'email', 'password', 'phone', 'role', 'precinct', 'state', 'county', 'map', 'notes', 'is_admin', 'is_county', 'is_active']
    
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

def create_app():
    """Application factory."""
    app = Flask(__name__)
    
    # Load configuration from config.py
    config_class = get_config()
    app.config.from_object(config_class)
    
    # Initialize extensions
    db.init_app(app)
    
    # Flask-Limiter setup
    limiter = Limiter(
        key_func=get_remote_address,
        default_limits=["200 per day", "50 per hour"],
        storage_uri=app.config.get('RATELIMIT_STORAGE_URL', 'memory://')
    )
    limiter.init_app(app)
    
    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # NC database is initialized through the same db instance with SQLALCHEMY_BINDS
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Message of the Day helper function
    def get_motd():
        """Read and return the message of the day from motd.txt file."""
        try:
            motd_path = os.path.join(app.root_path, 'motd.txt')
            if os.path.exists(motd_path):
                with open(motd_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    return content if content else None
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
            
            # If map field contains just a filename, try to load from static_html directory
            if map_record.map.endswith('.html') and len(map_record.map) < 50:
                static_content = get_static_html_content(map_record.map)
                if static_content is None:
                    # Static file referenced by database but not found
                    app.logger.error(f'Database references static file {map_record.map} for user {user.username} but file not found')
                    return create_error_page("Database Error", 
                        f"Map file '{map_record.map}' referenced in database but not found in static directory.")
                return static_content
            
            # Otherwise, assume it's HTML content stored directly in the database
            return map_record.map
            
        except Exception as e:
            app.logger.error(f'Database error retrieving map for user {user.username}: {str(e)}')
            return create_error_page("Database Error", 
                "Failed to retrieve map from database. Please try again or contact support.")
    
    def get_map_content_by_filename(filename):
        """Get map content by filename, checking database first, then static files."""
        try:
            # Extract precinct number from filename (e.g., "999.html" -> "999")
            if filename.endswith('.html'):
                precinct = filename[:-5]  # Remove .html extension
                
                # Try to find in database by precinct number
                # We don't know the state/county, so we'll search for any map with this precinct
                map_record = Map.query.filter_by(precinct=precinct).first()
                
                if map_record and map_record.map:
                    # If it's stored HTML content, return it
                    if not map_record.map.endswith('.html') or len(map_record.map) > 50:
                        app.logger.info(f'Serving map {filename} from database (full content) for {map_record.state} {map_record.county} Precinct {map_record.precinct}')
                        return map_record.map
                    
                    # If it's a filename reference, load the static file
                    static_content = get_static_html_content(map_record.map)
                    if static_content is None:
                        app.logger.error(f'Database references static file {map_record.map} for {filename} but file not found')
                        return create_error_page("Database Error", 
                            f"Map file '{map_record.map}' referenced in database but not found in static directory.")
                    app.logger.info(f'Serving map {filename} from database reference to static file {map_record.map}')
                    return static_content
            
            # Also try searching in the map field for filename references (legacy support)
            map_record = Map.query.filter(Map.map.like(f'%{filename}%')).first()
            if map_record and map_record.map:
                if map_record.map == filename:  # Exact filename match
                    static_content = get_static_html_content(filename)
                    if static_content is None:
                        app.logger.error(f'Database references static file {filename} but file not found')
                        return create_error_page("Database Error", 
                            f"Map file '{filename}' referenced in database but not found in static directory.")
                    app.logger.info(f'Serving map {filename} from database reference to static file')
                    return static_content
            
        except Exception as e:
            app.logger.error(f'Database error retrieving map by filename {filename}: {str(e)}')
            return create_error_page("Database Error", 
                "Failed to retrieve map from database. Please try again or contact support.")
        
        # Fall back to static file
        static_content = get_static_html_content(filename)
        if static_content:
            app.logger.info(f'Serving map {filename} from static file fallback (no database match found)')
            return static_content
        
        # Neither database nor static file found
        return None
    
    def get_static_html_content(filename):
        """Get HTML content from static_html directory."""
        try:
            static_html_dir = os.path.join(app.root_path, app.config['STATIC_HTML_DIR'])
            file_path = os.path.join(static_html_dir, filename)
            
            if not os.path.exists(file_path) or not filename.endswith('.html'):
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            app.logger.error(f'Error reading static HTML file {filename}: {str(e)}')
            return None
    
    def user_can_access_map(user, filename_or_precinct):
        """Check if user can access a specific map."""
        if user.is_admin:
            return True
        
        # For county users, allow access to any map in their county
        if user.is_county and user.state and user.county:
            return True
        
        # For regular users, only allow access to their assigned map
        if user.map == filename_or_precinct:
            return True
        
        # Also check if the filename matches their precinct
        if user.precinct == filename_or_precinct:
            return True
        
        # Check if filename corresponds to user's location
        if filename_or_precinct and filename_or_precinct.replace('.html', '') == user.precinct:
            return True
        
        return False

    # Make MOTD function available to all templates
    @app.context_processor
    def inject_motd():
        return dict(get_motd=get_motd)
    
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
    
    # Flask-Admin setup
    admin = Admin(
        app, 
        name='User Admin', 
        template_mode='bootstrap4',
        base_template='admin/my_master.html' if hasattr(app.config, 'FLASK_ADMIN_SWATCH') else None,
        index_view=SecureAdminIndexView()
    )
    admin.add_view(UserModelView(User, db.session, name='Users'))
    
    # Dash Analytics Integration
    if DASH_AVAILABLE:
        dash_app = create_dash_app(app)
    
    @app.route('/')
    @login_required
    def index():
        """Dashboard page - requires login."""
        return render_template('dashboard.html', user=current_user)
    
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
    
    @app.route('/analysis')
    @login_required
    def analysis():
        """Precinct Analytics page with Dash charts and graphs."""
        if DASH_AVAILABLE:
            # Redirect to Dash analytics app
            return redirect('/dash/analytics/')
        else:
            # Fallback to simple message if Dash is not available
            flash('Dash analytics is not available. Please install dash, plotly, and pandas packages.', 'warning')
            return redirect(url_for('index'))
    
    @app.route('/profile')
    @login_required
    def profile():
        """User profile page."""
        return render_template('profile.html', user=current_user)
    
    @app.route('/admin/motd', methods=['GET', 'POST'])
    @login_required
    def admin_motd():
        """Admin page to edit message of the day."""
        if not current_user.is_admin:
            flash('Access denied. Administrator access required.', 'error')
            return redirect(url_for('index'))
        
        motd_path = os.path.join(app.root_path, 'motd.txt')
        
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
        current_motd = get_motd() or ''
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
        flash('Rate limit exceeded. Please try again later.', 'warning')
        return render_template('dashboard.html', user=current_user), 429
    
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
            return redirect(url_for('dashboard'))
        elif 'Database Error' in map_content and '<div class="error-container">' in map_content:
            # Database error occurred, show error message
            flash('There was an error retrieving your map from the database. Please try again or contact support.', 'error')
            return redirect(url_for('dashboard'))
        
        # Create a filename for display purposes
        filename = f"{current_user.precinct}.html"
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

    # Initialize database
    with app.app_context():
        init_db()
    
    return app

def main():
    """Run the Flask application."""
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)

if __name__ == "__main__":
    main()
