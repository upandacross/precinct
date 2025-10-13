import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import sqlite3
import os

# Import Flask app components to access database
import sys
sys.path.append('.')
from models import db, User
from flask_login import current_user

def get_analytics_data(flask_app):
    """Get analytics data from the database and generate sample data."""
    database_error = None
    try:
        # Use Flask app context for database queries
        with flask_app.app_context():
            # Get current user within Flask context
            try:
                current_authenticated_user = current_user if current_user.is_authenticated else None
            except:
                current_authenticated_user = None
            
            # Determine filter scope based on user permissions
            if current_authenticated_user and hasattr(current_authenticated_user, 'is_admin') and hasattr(current_authenticated_user, 'is_county'):
                if current_authenticated_user.is_admin or current_authenticated_user.is_county:
                    # Admin and county users: filter by state and county
                    base_query = User.query.filter_by(state=current_authenticated_user.state, county=current_authenticated_user.county)
                    scope_description = f"{current_authenticated_user.county} County"
                else:
                    # Regular users: filter by state, county, and precinct
                    base_query = User.query.filter_by(
                        state=current_authenticated_user.state, 
                        county=current_authenticated_user.county, 
                        precinct=current_authenticated_user.precinct
                    )
                    scope_description = f"{current_authenticated_user.county} County, Precinct {current_authenticated_user.precinct}"
            else:
                # Fallback to all users if no user context
                base_query = User.query
                scope_description = "All Users"
            
            # Get filtered user statistics
            total_users = base_query.count()
            admin_users = base_query.filter_by(is_admin=True).count()
            county_users = base_query.filter_by(is_county=True).count()
            regular_users = total_users - admin_users - county_users
            active_users = base_query.filter_by(is_active=True).count()
            inactive_users = total_users - active_users
    except Exception as e:
        # Capture specific error details
        database_error = f"Database Error: {str(e)}"
        # Fallback to sample data if database is not accessible
        total_users = 25
        admin_users = 3
        regular_users = 22
        active_users = 23
        inactive_users = 2
    
    # Sample data for charts (in a real app, this would come from actual analytics)
    analytics_data = {
        'user_stats': {
            'total': total_users,
            'admins': admin_users,
            'county': county_users if 'county_users' in locals() else 0,
            'regular': regular_users,
            'active': active_users,
            'inactive': inactive_users
        },
        'scope_description': scope_description if 'scope_description' in locals() else 'All Users',
        'monthly_signups': pd.DataFrame({
            'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'Signups': [12, 19, 8, 15, 22, 13]
        }),
        'login_activity': pd.DataFrame({
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'Logins': [65, 59, 80, 81, 56, 55, 40]
        }),
        'password_strength': pd.DataFrame({
            'Strength': ['Republican', 'Democrat', 'UNAFFILIATED'],
            'Count': [15, 45, 40]
        }),
        'recent_activity': pd.DataFrame({
            'Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'Logins': [120, 150, 180, 200],
            'Registrations': [8, 12, 15, 10]
        }),
        'database_error': database_error
    }
    
    return analytics_data

def create_dash_app(flask_app):
    """Create and configure the Dash app."""
    dash_app = dash.Dash(
        __name__,
        server=flask_app,
        url_base_pathname='/dash/analytics/',
        external_stylesheets=[
            'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
            'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
        ]
    )
    
    # Get analytics data with user context
    data = get_analytics_data(flask_app)
    
    # Create figures with error handling
    try:
        # User Distribution Pie Chart
        user_dist_fig = px.pie(
            values=[data['user_stats']['regular'], data['user_stats']['admins'], data['user_stats']['county'], data['user_stats']['inactive']],
            names=['Regular Users', 'Admin Users', 'County Users', 'Inactive Users'],
            title='User Type Distribution',
            color_discrete_sequence=['#36A2EB', '#FF6384', '#4BC0C0', '#FFCE56']
        )
    except Exception as e:
        # Create error figure
        user_dist_fig = go.Figure()
        user_dist_fig.add_annotation(
            text=f"Chart Error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        user_dist_fig.update_layout(title="User Distribution - Error Loading")
    user_dist_fig.update_layout(
        font=dict(family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif"),
        title_font_size=18,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    # Password Strength Pie Chart
    try:
        password_fig = px.pie(
            data['password_strength'],
            values='Count',
            names='Strength',
            title='Party Voting Distribution',
            color_discrete_sequence=['#FF6B6B', '#FFD93D', '#6BCF7F']
        )
        password_fig.update_layout(
            font=dict(family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif"),
            title_font_size=18,
            margin=dict(t=50, b=50, l=50, r=50)
        )
    except Exception as e:
        password_fig = go.Figure()
        password_fig.add_annotation(
            text=f"Chart Error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        password_fig.update_layout(title="Party Voting Distribution - Error Loading")
    
    # Monthly Signups Line Chart
    try:
        monthly_fig = px.line(
            data['monthly_signups'],
            x='Month',
            y='Signups',
            title='Monthly Voter Registrations',
            markers=True
        )
        monthly_fig.update_traces(
            line_color='#667eea',
            line_width=3,
            marker_size=8
        )
        monthly_fig.update_layout(
            font=dict(family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif"),
            title_font_size=18,
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=50, b=50, l=50, r=50)
        )
    except Exception as e:
        monthly_fig = go.Figure()
        monthly_fig.add_annotation(
            text=f"Chart Error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        monthly_fig.update_layout(title="Monthly Voter Registrations - Error Loading")
    
    # Login Activity Bar Chart
    try:
        login_fig = px.bar(
            data['login_activity'],
            x='Day',
            y='Logins',
            title='Weekly Canvasing Activity',
            color='Logins',
            color_continuous_scale='Blues'
        )
        login_fig.update_layout(
            font=dict(family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif"),
            title_font_size=18,
            showlegend=False,
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=50, b=50, l=50, r=50)
        )
    except Exception as e:
        login_fig = go.Figure()
        login_fig.add_annotation(
            text=f"Chart Error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        login_fig.update_layout(title="Weekly Canvasing Activity - Error Loading")
    
    # Recent Activity Multi-line Chart
    try:
        recent_fig = go.Figure()
        recent_fig.add_trace(go.Scatter(
            x=data['recent_activity']['Week'],
            y=data['recent_activity']['Logins'],
            mode='lines+markers',
            name='Registration Flyers',
            line=dict(color='#4facfe', width=3),
            marker=dict(size=8)
        ))
        recent_fig.add_trace(go.Scatter(
            x=data['recent_activity']['Week'],
            y=data['recent_activity']['Registrations'],
            mode='lines+markers',
            name='Voter Registrations',
            line=dict(color='#43e97b', width=3),
            marker=dict(size=8)
        ))
        recent_fig.update_layout(
            title='Recent Activity Trends',
            font=dict(family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif"),
            title_font_size=18,
            plot_bgcolor='rgba(0,0,0,0)',
            margin=dict(t=50, b=50, l=50, r=50)
        )
    except Exception as e:
        recent_fig = go.Figure()
        recent_fig.add_annotation(
            text=f"Chart Error: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        recent_fig.update_layout(title="Recent Activity Trends - Error Loading")
    
    # Define the layout
    dash_app.layout = html.Div([
        # Header
        html.Div([
            html.Div([
                html.Div([
                    html.H1([
                        html.I(className="fas fa-chart-line", style={'margin-right': '15px'}),
                        "Precinct Analytics Dashboard"
                    ], className="text-white mb-2"),
                    html.P(id="analytics-scope-text", 
                           className="lead text-white mb-0"),
                    # Hidden interval component to trigger updates
                    dcc.Interval(id="scope-interval", interval=1000, n_intervals=0, max_intervals=1)
                ], className="col-md-8"),
                html.Div([
                    html.A([
                        html.I(className="fas fa-home", style={'margin-right': '8px'}),
                        "Dashboard"
                    ], href="/", className="btn btn-outline-light me-2"),
                    html.A([
                        html.I(className="fas fa-arrow-left", style={'margin-right': '8px'}),
                        "Back to App"
                    ], href="/", className="btn btn-light")
                ], className="col-md-4 text-end align-self-center")
            ], className="row align-items-center")
        ], className="analytics-header p-4 mb-4", style={
            'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
            'border-radius': '10px'
        }),
        
        # Database Error Alert (if any)
        html.Div([
            html.Div([
                html.I(className="fas fa-exclamation-triangle", style={'margin-right': '10px'}),
                html.Strong("Database Connection Issue: "),
                html.Span(data['database_error'])
            ], className="alert alert-warning alert-dismissible", role="alert")
        ], className="mb-4") if data['database_error'] else html.Div(),
        
        # Key Statistics
        html.Div([
            html.Div([
                html.Div([
                    html.H2(str(data['user_stats']['total']), className="stats-number text-white"),
                    html.P([html.I(className="fas fa-users"), " Total Users"], className="stats-label text-white")
                ], className="text-center p-3", style={
                    'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    'border-radius': '10px'
                })
            ], className="col-md-2"),
            
            html.Div([
                html.Div([
                    html.H2(str(data['user_stats']['active']), className="stats-number text-white"),
                    html.P([html.I(className="fas fa-user-check"), " Active Users"], className="stats-label text-white")
                ], className="text-center p-3", style={
                    'background': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                    'border-radius': '10px'
                })
            ], className="col-md-2"),
            
            html.Div([
                html.Div([
                    html.H2(str(data['user_stats']['admins']), className="stats-number text-white"),
                    html.P([html.I(className="fas fa-user-shield"), " Admins"], className="stats-label text-white")
                ], className="text-center p-3", style={
                    'background': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                    'border-radius': '10px'
                })
            ], className="col-md-2"),
            
            html.Div([
                html.Div([
                    html.H2(str(data['user_stats']['county']), className="stats-number text-white"),
                    html.P([html.I(className="fas fa-user-tie"), " County"], className="stats-label text-white")
                ], className="text-center p-3", style={
                    'background': 'linear-gradient(135deg, #fd746c 0%, #ff9068 100%)',
                    'border-radius': '10px'
                })
            ], className="col-md-2"),
            
            html.Div([
                html.Div([
                    html.H2(str(data['user_stats']['regular']), className="stats-number text-white"),
                    html.P([html.I(className="fas fa-user"), " Regular"], className="stats-label text-white")
                ], className="text-center p-3", style={
                    'background': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
                    'border-radius': '10px'
                })
            ], className="col-md-2"),
            
            html.Div([
                html.Div([
                    html.H2(str(data['user_stats']['inactive']), className="stats-number text-white"),
                    html.P([html.I(className="fas fa-user-times"), " Inactive"], className="stats-label text-white")
                ], className="text-center p-3", style={
                    'background': 'linear-gradient(135deg, #a8a8a8 0%, #7b7b7b 100%)',
                    'border-radius': '10px'
                })
            ], className="col-md-2"),
        ], className="row mb-4"),
        
        # Charts Row 1
        html.Div([
            html.Div([
                html.Div([
                    dcc.Graph(figure=user_dist_fig, style={'height': '400px'})
                ], className="chart-card p-3", style={
                    'background': 'white',
                    'border-radius': '10px',
                    'box-shadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            ], className="col-md-6"),
            
            html.Div([
                html.Div([
                    dcc.Graph(figure=password_fig, style={'height': '400px'})
                ], className="chart-card p-3", style={
                    'background': 'white',
                    'border-radius': '10px',
                    'box-shadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            ], className="col-md-6"),
        ], className="row mb-4"),
        
        # Charts Row 2
        html.Div([
            html.Div([
                html.Div([
                    dcc.Graph(figure=monthly_fig, style={'height': '400px'})
                ], className="chart-card p-3", style={
                    'background': 'white',
                    'border-radius': '10px',
                    'box-shadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            ], className="col-md-12"),
        ], className="row mb-4"),
        
        # Charts Row 3
        html.Div([
            html.Div([
                html.Div([
                    dcc.Graph(figure=login_fig, style={'height': '400px'})
                ], className="chart-card p-3", style={
                    'background': 'white',
                    'border-radius': '10px',
                    'box-shadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            ], className="col-md-6"),
            
            html.Div([
                html.Div([
                    dcc.Graph(figure=recent_fig, style={'height': '400px'})
                ], className="chart-card p-3", style={
                    'background': 'white',
                    'border-radius': '10px',
                    'box-shadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            ], className="col-md-6"),
        ], className="row mb-4"),
        
        # Insights Section
        html.Div([
            html.Div([
                html.H4([html.I(className="fas fa-lightbulb"), " Key Insights"], className="mb-3"),
                html.Div([
                    html.Div([
                        html.Div([
                            html.H6([html.I(className="fas fa-info-circle"), " Volunteer Growth"], className="alert-heading"),
                            html.P("Volunteers have increased by 10% this month compared to last month.", className="mb-0")
                        ], className="alert alert-info")
                    ], className="col-md-4"),
                    
                    html.Div([
                        html.Div([
                            html.H6([html.I(className="fas fa-check-circle"), " Voting Status"], className="alert-heading"),
                            html.P("35% of democrats have voted in last presidential election, indicating GOTV effort required.", className="mb-0")
                        ], className="alert alert-success")
                    ], className="col-md-4"),
                    
                    html.Div([
                        html.Div([
                            html.H6([html.I(className="fas fa-exclamation-triangle"), " Activity Pattern"], className="alert-heading"),
                            html.P("Peak volunteer activity occurs on Wednesday and Thursday. Consider emphasizing outreach on other days.", className="mb-0")
                        ], className="alert alert-warning")
                    ], className="col-md-4"),
                ], className="row")
            ], className="chart-card p-4", style={
                'background': 'white',
                'border-radius': '10px',
                'box-shadow': '0 2px 10px rgba(0,0,0,0.1)'
            })
        ], className="row")
        
    ], className="container-fluid p-4", style={
        'background': '#f8f9fa',
        'min-height': '100vh'
    })
    
    # Callback to dynamically update the analytics scope text
    @dash_app.callback(
        Output('analytics-scope-text', 'children'),
        Input('scope-interval', 'n_intervals')
    )
    def update_scope_text(n):
        # Get fresh user context data when page loads
        current_data = get_analytics_data(flask_app)
        return f"Analytics for: {current_data['scope_description']}"
    
    return dash_app

# Custom CSS for consistent styling
external_stylesheets = [
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
]