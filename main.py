import os
from flask import Flask, render_template, request, redirect, url_for, flash, abort
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Length, Email
from models import db, User
from datetime import datetime
from config import get_config
try:
    from dash_analytics import create_dash_app
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False
# TODO: flask_limit
# TODP: CSRF
# TODO: research HSTS and CSP via Flask-Talisman, X-Frame-Options deny
# TODO: turn off DEBUG
# TODO: research session timeout
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
    column_searchable_list = ['username', 'email', 'password', 'phone', 'role', 'precinct']
    column_filters = ['is_admin', 'is_active', 'created_at', 'role', 'precinct']
    form_excluded_columns = ['password_hash', 'created_at', 'last_login']
    column_details_list = ['id', 'username', 'email', 'password', 'phone', 'role', 'precinct', 'map', 'notes', 'is_admin', 'is_active', 'created_at', 'last_login']
    
    # Define form field order - username first, then password as unique field, followed by contact and role info
    form_columns = ['username', 'email', 'password', 'phone', 'role', 'precinct', 'map', 'notes', 'is_admin', 'is_active']
    
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
    
    # Flask-Login setup
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
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
                flash(f'Welcome back, {user.username}!', 'success')
                
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
    
    @app.route('/static-content')
    @login_required
    def static_content():
        """Display list of available static HTML files. Admin access only."""
        if not current_user.is_admin:
            flash('Access denied. Static content is available to administrators only.', 'error')
            return redirect(url_for('index'))
        static_html_dir = os.path.join(app.root_path, app.config['STATIC_HTML_DIR'])
        
        # Create directory if it doesn't exist
        if not os.path.exists(static_html_dir):
            os.makedirs(static_html_dir)
            # Create a sample file
            sample_content = """<!DOCTYPE html>
<html>
<head>
    <title>Sample Static Content</title>
    <style>
        body { font-family: Arial, sans-serif; padding: 20px; }
        .content { max-width: 800px; margin: 0 auto; }
        h1 { color: #333; }
        .info-box { background: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="content">
        <h1>Sample Static HTML Content</h1>
        <p>This is a sample static HTML file for the Precinct Leaders App. You can add more files to the static_html directory.</p>
        
        <div class="info-box">
            <h2>Features Available:</h2>
            <ul>
                <li>Full HTML support with custom styling</li>
                <li>CSS styling and responsive design</li>
                <li>JavaScript functionality</li>
                <li>Embedded media and images</li>
                <li>Interactive elements and forms</li>
            </ul>
        </div>
        
        <h2>Precinct Information</h2>
        <p>This section could contain specific precinct data, maps, contact information, or any other relevant content for precinct leaders.</p>
        
        <h3>Example Data Table</h3>
        <table border="1" style="border-collapse: collapse; width: 100%;">
            <tr style="background: #e9ecef;">
                <th style="padding: 8px;">Precinct</th>
                <th style="padding: 8px;">Leader</th>
                <th style="padding: 8px;">Contact</th>
            </tr>
            <tr>
                <td style="padding: 8px;">704</td>
                <td style="padding: 8px;">John Doe</td>
                <td style="padding: 8px;">john@example.com</td>
            </tr>
            <tr>
                <td style="padding: 8px;">705</td>
                <td style="padding: 8px;">Jane Smith</td>
                <td style="padding: 8px;">jane@example.com</td>
            </tr>
        </table>
    </div>
</body>
</html>"""
            with open(os.path.join(static_html_dir, 'sample.html'), 'w') as f:
                f.write(sample_content)
        
        # Get list of HTML files
        html_files = []
        try:
            for filename in os.listdir(static_html_dir):
                if filename.endswith('.html'):
                    file_path = os.path.join(static_html_dir, filename)
                    file_stats = os.stat(file_path)
                    html_files.append({
                        'name': filename,
                        'display_name': filename.replace('.html', '').replace('_', ' ').title(),
                        'size': file_stats.st_size,
                        'modified': datetime.fromtimestamp(file_stats.st_mtime)
                    })
        except OSError:
            pass
        
        html_files.sort(key=lambda x: x['name'])
        return render_template('static_content.html', files=html_files)
    
    @app.route('/static-content/<filename>')
    @login_required
    def view_static_content(filename):
        """Display a specific static HTML file with navbar. Available to all authenticated users."""
        static_html_dir = os.path.join(app.root_path, app.config['STATIC_HTML_DIR'])
        file_path = os.path.join(static_html_dir, filename)
        
        # Security check - ensure file exists and is within the static_html directory
        if not os.path.exists(file_path) or not filename.endswith('.html'):
            abort(404)
        
        # For non-admin users, check if they have access to this specific file
        # (either it's their assigned map or it's a public file)
        if not current_user.is_admin:
            # Allow access if it's the user's assigned map
            if current_user.map != filename:
                # For now, allow all authenticated users to view any static content
                # This can be restricted later if needed
                pass
        
        return render_template('static_viewer.html', 
                             filename=filename,
                             display_name=filename.replace('.html', '').replace('_', ' ').title(),
                             is_public_view=not current_user.is_admin)
    
    @app.route('/static-content-raw/<filename>')
    @login_required
    def view_static_content_raw(filename):
        """Serve raw HTML file content for iframe display. Available to all authenticated users."""
        # Allow all authenticated users to view static content
        # For non-admin users, they can only access via direct links (not browse the library)
        
        static_html_dir = os.path.join(app.root_path, app.config['STATIC_HTML_DIR'])
        file_path = os.path.join(static_html_dir, filename)
        
        # Security check - ensure file exists and is within the static_html directory
        if not os.path.exists(file_path) or not filename.endswith('.html'):
            abort(404)
        
        # Read and serve the raw HTML content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            return f'<html><body><h1>Error</h1><p>Error reading file: {str(e)}</p></body></html>', 500
    
    @app.route('/view/<filename>')
    @login_required
    def view_file_new_tab(filename):
        """Open static HTML file directly in new tab with close button. Available to all authenticated users."""
        static_html_dir = os.path.join(app.root_path, app.config['STATIC_HTML_DIR'])
        file_path = os.path.join(static_html_dir, filename)
        
        # Security check - ensure file exists and is within the static_html directory
        if not os.path.exists(file_path) or not filename.endswith('.html'):
            abort(404)
        
        # Read and serve the raw HTML content with close button
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
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
        if (confirm('Close this tab?')) {
            window.close();
            // Fallback for browsers that don't allow window.close()
            setTimeout(function() {
                window.location.href = 'about:blank';
            }, 100);
        }
    }
}
</script>
            '''
            
            # Insert close button after the opening <body> tag
            if '<body>' in content:
                content = content.replace('<body>', '<body>' + close_button)
            else:
                # If no <body> tag found, add it at the beginning
                content = close_button + content
            
            return content
        except Exception as e:
            return f'<html><body><h1>Error</h1><p>Error reading file: {str(e)}</p></body></html>', 500
    
    @app.route('/user-map/<filename>')
    @login_required
    def view_user_map(filename):
        """Display user's map file with navbar. Shows current user's map or any map for admins."""
        static_html_dir = os.path.join(app.root_path, app.config['STATIC_HTML_DIR'])
        file_path = os.path.join(static_html_dir, filename)
        
        # Security check - ensure file exists and is within the static_html directory
        if not os.path.exists(file_path) or not filename.endswith('.html'):
            abort(404)
        
        # Check if current user's map matches requested filename or if user is admin
        if current_user.map != filename and not current_user.is_admin:
            flash('Access denied. You can only view your assigned map.', 'error')
            return redirect(url_for('profile'))
        
        return render_template('static_viewer.html', 
                             filename=filename,
                             display_name=filename.replace('.html', '').replace('_', ' ').title(),
                             is_user_map=True)
    
    @app.route('/user-map-raw/<filename>')
    @login_required
    def view_user_map_raw(filename):
        """Serve raw HTML file content for user's map iframe display."""
        static_html_dir = os.path.join(app.root_path, app.config['STATIC_HTML_DIR'])
        file_path = os.path.join(static_html_dir, filename)
        
        # Security check - ensure file exists and is within the static_html directory
        if not os.path.exists(file_path) or not filename.endswith('.html'):
            abort(404)
        
        # Check if current user's map matches requested filename or if user is admin
        if current_user.map != filename and not current_user.is_admin:
            return '<html><body><h1>Access Denied</h1><p>You can only view your assigned map.</p></body></html>', 403
        
        # Read and serve the raw HTML content
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except Exception as e:
            return f'<html><body><h1>Error</h1><p>Error reading file: {str(e)}</p></body></html>', 500
    
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
