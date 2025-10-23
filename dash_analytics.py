import dash
from dash import dcc, html, Input, Output, callback
from urllib.parse import urlparse, parse_qs
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

def get_analytics_data(flask_app, user_id=None):
    """Get analytics data from the database and generate sample data."""
    database_error = None
    try:
        # Use Flask app context for database queries
        with flask_app.app_context():
            # Get current user from session or parameter
            current_authenticated_user = None
            
            if user_id:
                # Get user by ID if provided
                current_authenticated_user = User.query.get(user_id)
            else:
                # Try to get current user from Flask-Login
                try:
                    from flask import session
                    if '_user_id' in session:
                        current_authenticated_user = User.query.get(session['_user_id'])
                    elif hasattr(current_user, 'is_authenticated') and current_user.is_authenticated:
                        current_authenticated_user = current_user
                except:
                    current_authenticated_user = None
            
            # Determine scope description based on user permissions
            if current_authenticated_user and hasattr(current_authenticated_user, 'is_admin') and hasattr(current_authenticated_user, 'is_county'):
                if current_authenticated_user.is_admin or current_authenticated_user.is_county:
                    # Admin and county users: show county scope
                    scope_description = f"{current_authenticated_user.county} County Analytics"
                else:
                    # Regular users: show precinct scope
                    scope_description = f"{current_authenticated_user.county} County, Precinct {current_authenticated_user.precinct} Analytics"
            else:
                # No user context - return error instead of fallback data
                raise Exception("No authenticated user context available. Please log in to view analytics.")
                
    except Exception as e:
        # Capture specific error details
        error_message = str(e)
        if "No authenticated user context" in error_message:
            database_error = f"Authentication Error: {error_message}"
            scope_description = "No User Context"
        else:
            database_error = f"Database Error: {error_message}"
            scope_description = "Error - Sample Data"

    # Sample data for charts (in a real app, this would come from actual analytics)
    analytics_data = {
        'scope_description': scope_description,
        'monthly_signups': {
            'Month': ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
            'Signups': [12, 19, 8, 15, 22, 13]
        },
        'login_activity': {
            'Day': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'Logins': [65, 59, 80, 81, 56, 55, 40]
        },
        'password_strength': {
            'Strength': ['Republican', 'Democrat', 'UNAFFILIATED'],
            'Count': [15, 45, 40]
        },
        'recent_activity': {
            'Week': ['Week 1', 'Week 2', 'Week 3', 'Week 4'],
            'Logins': [120, 150, 180, 200],
            'Registrations': [8, 12, 15, 10]
        },
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
    
    # Initially create with empty data - will be populated by callback
    data = {
        'user_stats': {'total': 0, 'admins': 0, 'county': 0, 'regular': 0, 'active': 0, 'inactive': 0},
        'scope_description': 'Loading...',
        'database_error': None,
        'monthly_signups': {'Month': [], 'Signups': []},
        'login_activity': {'Day': [], 'Logins': []},
        'password_strength': {'Strength': [], 'Count': []},
        'recent_activity': {'Week': [], 'Logins': [], 'Registrations': []}
    }
    
    # Create placeholder figures that will be updated by callbacks
    # User Distribution Pie Chart - placeholder
    user_dist_fig = go.Figure()
    user_dist_fig.add_annotation(
        text="Loading user data...",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="#666")
    )
    user_dist_fig.update_layout(title="Website User Types")
    user_dist_fig.update_layout(
        font=dict(family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif"),
        title_font_size=18,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    # Password Strength Pie Chart - placeholder
    password_fig = go.Figure()
    password_fig.add_annotation(
        text="Loading party data...",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="#666")
    )
    password_fig.update_layout(title="Party Voting Distribution")
    
    # Monthly Signups Line Chart - placeholder
    monthly_fig = go.Figure()
    monthly_fig.add_annotation(
        text="Loading registration data...",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="#666")
    )
    monthly_fig.update_layout(title="Monthly Voter Registrations")
    
    # Login Activity Bar Chart - placeholder
    login_fig = go.Figure()
    login_fig.add_annotation(
        text="Loading activity data...",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="#666")
    )
    login_fig.update_layout(title="Weekly Canvasing Activity")
    
    # Recent Activity Multi-line Chart - placeholder
    recent_fig = go.Figure()
    recent_fig.add_annotation(
        text="Loading trend data...",
        xref="paper", yref="paper",
        x=0.5, y=0.5, showarrow=False,
        font=dict(size=16, color="#666")
    )
    recent_fig.update_layout(title="Recent Activity Trends")
    
    # Define the layout
    dash_app.layout = html.Div([
        # URL tracking component
        dcc.Location(id='url', refresh=False),
        
        # Store component to hold user data
        dcc.Store(id='analytics-data-store'),
        
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
        
        # Charts Row 1
        html.Div([
            html.Div([
                html.Div([
                    dcc.Graph(id='password-strength-chart', figure=password_fig, style={'height': '400px'})
                ], className="chart-card p-3", style={
                    'background': 'white',
                    'border-radius': '10px',
                    'box-shadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            ], className="col-md-12"),
        ], className="row mb-4"),
        
        # Charts Row 2
        html.Div([
            html.Div([
                html.Div([
                    dcc.Graph(id='monthly-signups-chart', figure=monthly_fig, style={'height': '400px'})
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
                    dcc.Graph(id='login-activity-chart', figure=login_fig, style={'height': '400px'})
                ], className="chart-card p-3", style={
                    'background': 'white',
                    'border-radius': '10px',
                    'box-shadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            ], className="col-md-6"),
            
            html.Div([
                html.Div([
                    dcc.Graph(id='recent-activity-chart', figure=recent_fig, style={'height': '400px'})
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
    
        # Callback to load analytics data based on URL parameters
    @dash_app.callback(
        Output('analytics-data-store', 'data'),
        Input('url', 'href')
    )
    def load_analytics_data(href):
        if href:
            try:
                parsed_url = urlparse(href)
                query_params = parse_qs(parsed_url.query)
                user_id = query_params.get('user_id', [None])[0]
                
                if user_id:
                    user_id = int(user_id)
                    return get_analytics_data(flask_app, user_id)
                else:
                    return get_analytics_data(flask_app, None)
            except:
                return get_analytics_data(flask_app, None)
        return get_analytics_data(flask_app, None)
    
    # Callback to update scope text from stored data
    @dash_app.callback(
        Output('analytics-scope-text', 'children'),
        Input('analytics-data-store', 'data')
    )
    def update_scope_text(stored_data):
        if stored_data:
            return f"Analytics for: {stored_data['scope_description']}"
        return "Analytics for: Loading..."
    
    # Callback to update password strength chart (political affiliation)
    @dash_app.callback(
        Output('password-strength-chart', 'figure'),
        Input('analytics-data-store', 'data')
    )
    def update_password_strength_chart(stored_data):
        if stored_data and stored_data.get('password_strength'):
            data = stored_data['password_strength']
            try:
                fig = px.bar(
                    x=data['Strength'],
                    y=data['Count'],
                    title='Political Affiliation Distribution',
                    color=data['Strength'],
                    color_discrete_sequence=['#FF6B6B', '#4ECDC4', '#45B7D1']
                )
                fig.update_layout(
                    font=dict(family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif"),
                    title_font_size=18,
                    xaxis_title="Affiliation",
                    yaxis_title="Count",
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                return fig
            except Exception as e:
                error_fig = go.Figure()
                error_fig.add_annotation(
                    text=f"Chart Error: {str(e)}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="red")
                )
                return error_fig
        
        # Return loading figure
        loading_fig = go.Figure()
        loading_fig.add_annotation(
            text="Loading affiliation data...",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#666")
        )
        loading_fig.update_layout(title="Political Affiliation Distribution")
        return loading_fig
    
    # Callback to update monthly signups chart
    @dash_app.callback(
        Output('monthly-signups-chart', 'figure'),
        Input('analytics-data-store', 'data')
    )
    def update_monthly_signups_chart(stored_data):
        if stored_data and stored_data.get('monthly_signups'):
            data = stored_data['monthly_signups']
            try:
                fig = px.line(
                    x=data['Month'],
                    y=data['Signups'],
                    title='Monthly User Signups',
                    markers=True
                )
                fig.update_traces(line_color='#36A2EB', marker_size=8)
                fig.update_layout(
                    font=dict(family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif"),
                    title_font_size=18,
                    xaxis_title="Month",
                    yaxis_title="New Signups",
                    margin=dict(t=50, b=50, l=50, r=50)
                )
                return fig
            except Exception as e:
                error_fig = go.Figure()
                error_fig.add_annotation(
                    text=f"Chart Error: {str(e)}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="red")
                )
                return error_fig
        
        # Return loading figure
        loading_fig = go.Figure()
        loading_fig.add_annotation(
            text="Loading signup data...",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#666")
        )
        loading_fig.update_layout(title="Monthly User Signups")
        return loading_fig
    
    # Callback to update login activity chart
    @dash_app.callback(
        Output('login-activity-chart', 'figure'),
        Input('analytics-data-store', 'data')
    )
    def update_login_activity_chart(stored_data):
        if stored_data and stored_data.get('login_activity'):
            data = stored_data['login_activity']
            try:
                fig = px.bar(
                    x=data['Day'],
                    y=data['Logins'],
                    title='Daily Mobilize Signups',
                    color=data['Logins'],
                    color_continuous_scale='Blues'
                )
                fig.update_layout(
                    font=dict(family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif"),
                    title_font_size=18,
                    xaxis_title="Day of Week",
                    yaxis_title="Mobilize Signup Count",
                    margin=dict(t=50, b=50, l=50, r=50),
                    showlegend=False
                )
                return fig
            except Exception as e:
                error_fig = go.Figure()
                error_fig.add_annotation(
                    text=f"Chart Error: {str(e)}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="red")
                )
                return error_fig
        
        # Return loading figure
        loading_fig = go.Figure()
        loading_fig.add_annotation(
            text="Loading activity data...",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#666")
        )
        loading_fig.update_layout(title="Daily Mobilize Signups")
        return loading_fig
    
    # Callback to update recent activity chart
    @dash_app.callback(
        Output('recent-activity-chart', 'figure'),
        Input('analytics-data-store', 'data')
    )
    def update_recent_activity_chart(stored_data):
        if stored_data and stored_data.get('recent_activity'):
            data = stored_data['recent_activity']
            try:
                # Use plotly graph objects for more reliable chart creation
                fig = go.Figure()
                
                # Add Mobilize trace
                fig.add_trace(go.Scatter(
                    x=data['Week'],
                    y=data['Logins'],
                    mode='lines+markers',
                    name='Mobilize',
                    line=dict(color='#36A2EB', width=3),
                    marker=dict(size=8)
                ))
                
                # Add Registrations trace (scaled for visibility)
                registrations_scaled = [x * 10 for x in data['Registrations']]
                fig.add_trace(go.Scatter(
                    x=data['Week'],
                    y=registrations_scaled,
                    mode='lines+markers',
                    name='Registrations (×10)',
                    line=dict(color='#FF6384', width=3),
                    marker=dict(size=8)
                ))
                
                fig.update_layout(
                    title='Recent Activity Trends',
                    font=dict(family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif"),
                    title_font_size=18,
                    xaxis_title="Week",
                    yaxis_title="Activity Count",
                    margin=dict(t=50, b=50, l=50, r=50),
                    legend=dict(x=0.02, y=0.98, title="Activity Type")
                )
                return fig
            except Exception as e:
                error_fig = go.Figure()
                error_fig.add_annotation(
                    text=f"Chart Error: {str(e)}",
                    xref="paper", yref="paper",
                    x=0.5, y=0.5, showarrow=False,
                    font=dict(size=16, color="red")
                )
                return error_fig
        
        # Return loading figure
        loading_fig = go.Figure()
        loading_fig.add_annotation(
            text="Loading trend data...",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="#666")
        )
        loading_fig.update_layout(title="Recent Activity Trends")
        return loading_fig
    
    return dash_app

# Custom CSS for consistent styling
external_stylesheets = [
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
]