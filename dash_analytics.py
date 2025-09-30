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

def get_analytics_data():
    """Get analytics data from the database and generate sample data."""
    try:
        # Get real user statistics
        total_users = User.query.count()
        admin_users = User.query.filter_by(is_admin=True).count()
        regular_users = total_users - admin_users
        active_users = User.query.filter_by(is_active=True).count()
        inactive_users = total_users - active_users
    except:
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
            'regular': regular_users,
            'active': active_users,
            'inactive': inactive_users
        },
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
        })
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
    
    # Get analytics data
    data = get_analytics_data()
    
    # Create figures
    # User Distribution Pie Chart
    user_dist_fig = px.pie(
        values=[data['user_stats']['regular'], data['user_stats']['admins'], data['user_stats']['inactive']],
        names=['Regular Voters', 'Infrequent Voters', 'Inactive Voters'],
        title='Voter Distribution',
        color_discrete_sequence=['#36A2EB', '#FF6384', '#FFCE56']
    )
    user_dist_fig.update_layout(
        font=dict(family="Segoe UI, Tahoma, Geneva, Verdana, sans-serif"),
        title_font_size=18,
        margin=dict(t=50, b=50, l=50, r=50)
    )
    
    # Password Strength Pie Chart
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
    
    # Monthly Signups Line Chart
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
    
    # Login Activity Bar Chart
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
    
    # Recent Activity Multi-line Chart
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
                    html.P("Comprehensive insights into precinct 704 activity and performance (example)", 
                           className="lead text-white mb-0")
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
        
        # Key Statistics
        html.Div([
            html.Div([
                html.Div([
                    html.H2(str(data['user_stats']['total']), className="stats-number text-white"),
                    html.P([html.I(className="fas fa-users"), " Total Volunteers"], className="stats-label text-white")
                ], className="text-center p-3", style={
                    'background': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                    'border-radius': '10px'
                })
            ], className="col-md-3"),
            
            html.Div([
                html.Div([
                    html.H2(str(data['user_stats']['active']), className="stats-number text-white"),
                    html.P([html.I(className="fas fa-user-check"), " Active Volunteers"], className="stats-label text-white")
                ], className="text-center p-3", style={
                    'background': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
                    'border-radius': '10px'
                })
            ], className="col-md-3"),
            
            html.Div([
                html.Div([
                    html.H2(str(data['user_stats']['admins']), className="stats-number text-white"),
                    html.P([html.I(className="fas fa-user-shield"), " Precinct Officials"], className="stats-label text-white")
                ], className="text-center p-3", style={
                    'background': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
                    'border-radius': '10px'
                })
            ], className="col-md-3"),
            
            html.Div([
                html.Div([
                    html.H2(str(data['user_stats']['regular']), className="stats-number text-white"),
                    html.P([html.I(className="fas fa-user"), " Regular Precinct Meeting Size"], className="stats-label text-white")
                ], className="text-center p-3", style={
                    'background': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
                    'border-radius': '10px'
                })
            ], className="col-md-3"),
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
    
    return dash_app

# Custom CSS for consistent styling
external_stylesheets = [
    'https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css'
]