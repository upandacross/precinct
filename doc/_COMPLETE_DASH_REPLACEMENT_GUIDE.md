# Complete Guide: Replace Existing Dash Analytics with Dashboard Code

## Current State Analysis

### Files to Remove/Replace
```
REMOVE:
├── dash_analytics.py           # Current Dash analytics (DELETE this file)

REPLACE IN:  
├── main.py                     # Update imports and routes
├── pyproject.toml             # Update dependencies if needed
```

### Current Implementation Details

#### 1. Current Dash Analytics Import (main.py lines 15-18)
```python
try:
    from dash_analytics import create_dash_app
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False
```

#### 2. Current Dash Integration (main.py lines 368-370)
```python
# Dash Analytics Integration
if DASH_AVAILABLE:
    dash_app = create_dash_app(app)
```

#### 3. Current Analytics Route (main.py lines 427-436)
```python
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
```

## Replacement Steps

### Step 1: Remove Old Dash Analytics File
```bash
# Delete the old dash analytics
rm dash_analytics.py
```

### Step 2: Copy and Adapt New Dashboard Code
```bash
# Copy the dashboard app from your copied dashboard directory
cp dashboard/dashboard_app.py ./precinct_dashboard.py
```

### Step 3: Update main.py Imports
**Replace lines 15-18 in main.py:**

FROM:
```python
try:
    from dash_analytics import create_dash_app
    DASH_AVAILABLE = True
except ImportError:
    DASH_AVAILABLE = False
```

TO:
```python
try:
    from precinct_dashboard import create_precinct_dashboard
    DASHBOARD_AVAILABLE = True
except ImportError:
    DASHBOARD_AVAILABLE = False
```

### Step 4: Update Dash Integration in main.py
**Replace lines 368-370 in main.py:**

FROM:
```python
# Dash Analytics Integration
if DASH_AVAILABLE:
    dash_app = create_dash_app(app)
```

TO:
```python
# Precinct Dashboard Integration  
if DASHBOARD_AVAILABLE:
    dashboard_app = create_precinct_dashboard()
    dashboard_app.init_app(app)
```

### Step 5: Update Analytics Route in main.py
**Replace lines 427-436 in main.py:**

FROM:
```python
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
```

TO:
```python
@app.route('/analysis')
@login_required
def analysis():
    """Precinct Dashboard with interactive charts and graphs."""
    if not (current_user.is_admin or current_user.is_county):
        flash('Access denied. Dashboard is available to administrators and county users only.', 'error')
        return redirect(url_for('index'))
    
    if DASHBOARD_AVAILABLE:
        # Redirect to new precinct dashboard
        return redirect('/dashboard/')
    else:
        # Fallback message if dashboard is not available
        flash('Dashboard is not available. Please contact technical support.', 'warning')
        return redirect(url_for('index'))
```

### Step 6: Create Precinct-Specific Dashboard
**Create `precinct_dashboard.py` (adapted from your dashboard code):**

```python
import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from models import db, User, Map
from datetime import datetime, timedelta

def create_precinct_dashboard():
    """Create precinct management dashboard"""
    external_stylesheets = [
        'https://codepen.io/chriddyp/pen/bWLwgP.css',
        {
            'href': 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
            'rel': 'stylesheet'
        }
    ]
    
    app = dash.Dash(__name__, url_base_pathname='/dashboard/', external_stylesheets=external_stylesheets)
    
    def get_precinct_data():
        """Get real data from NC database"""
        try:
            # User statistics
            total_users = User.query.count()
            admin_users = User.query.filter_by(is_admin=True).count()
            county_users = User.query.filter_by(is_county=True).count()
            active_users = User.query.filter_by(is_active=True).count()
            
            # Map statistics
            total_maps = Map.query.count()
            maps_with_content = Map.query.filter(db.func.length(Map.map) > 100).count()
            
            # County distribution
            county_stats = db.session.query(
                Map.county, 
                db.func.count(Map.id).label('count')
            ).group_by(Map.county).all()
            
            return {
                'users': {
                    'total': total_users,
                    'admins': admin_users,
                    'county': county_users,
                    'active': active_users,
                    'regular': total_users - admin_users - county_users
                },
                'maps': {
                    'total': total_maps,
                    'with_content': maps_with_content,
                    'without_content': total_maps - maps_with_content
                },
                'counties': dict(county_stats) if county_stats else {}
            }
        except Exception as e:
            print(f"Database error: {e}")
            return {
                'users': {'total': 0, 'admins': 0, 'county': 0, 'active': 0, 'regular': 0},
                'maps': {'total': 0, 'with_content': 0, 'without_content': 0},
                'counties': {}
            }
    
    # Dashboard layout
    app.layout = html.Div([
        html.Div([
            html.H1("NC Precinct Management Dashboard", 
                   style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 20}),
            html.P("Real-time overview of users, maps, and county statistics",
                   style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': 30})
        ], style={'padding': '20px'}),
        
        # Stats cards
        html.Div([
            html.Div([
                html.H3(id='total-users', style={'margin': 0, 'color': '#3498db', 'fontSize': '2.5em'}),
                html.P('Total Users', style={'margin': 0, 'color': '#7f8c8d'})
            ], className='three columns', style={'textAlign': 'center', 'backgroundColor': '#f8f9fa', 'padding': '20px', 'margin': '10px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H3(id='total-maps', style={'margin': 0, 'color': '#e74c3c', 'fontSize': '2.5em'}),
                html.P('Total Maps', style={'margin': 0, 'color': '#7f8c8d'})
            ], className='three columns', style={'textAlign': 'center', 'backgroundColor': '#f8f9fa', 'padding': '20px', 'margin': '10px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H3(id='maps-with-content', style={'margin': 0, 'color': '#27ae60', 'fontSize': '2.5em'}),
                html.P('Maps with Content', style={'margin': 0, 'color': '#7f8c8d'})
            ], className='three columns', style={'textAlign': 'center', 'backgroundColor': '#f8f9fa', 'padding': '20px', 'margin': '10px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
            
            html.Div([
                html.H3(id='active-users', style={'margin': 0, 'color': '#f39c12', 'fontSize': '2.5em'}),
                html.P('Active Users', style={'margin': 0, 'color': '#7f8c8d'})
            ], className='three columns', style={'textAlign': 'center', 'backgroundColor': '#f8f9fa', 'padding': '20px', 'margin': '10px', 'borderRadius': '8px', 'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'}),
        ], className='row', style={'margin': '0 20px'}),
        
        # Charts
        html.Div([
            html.Div([
                dcc.Graph(id='user-distribution')
            ], className='six columns'),
            
            html.Div([
                dcc.Graph(id='map-status')  
            ], className='six columns'),
        ], className='row', style={'margin': '20px'}),
        
        html.Div([
            dcc.Graph(id='county-distribution')
        ], className='row', style={'margin': '20px'}),
        
        # Auto-refresh every 30 seconds
        dcc.Interval(
            id='interval-component',
            interval=30*1000,
            n_intervals=0
        )
    ])
    
    @app.callback(
        [Output('total-users', 'children'),
         Output('total-maps', 'children'),
         Output('maps-with-content', 'children'), 
         Output('active-users', 'children'),
         Output('user-distribution', 'figure'),
         Output('map-status', 'figure'),
         Output('county-distribution', 'figure')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_dashboard(n):
        data = get_precinct_data()
        
        # User distribution pie chart
        user_fig = px.pie(
            values=[data['users']['admins'], data['users']['county'], data['users']['regular']], 
            names=['Administrators', 'County Users', 'Regular Users'],
            title='User Type Distribution',
            color_discrete_sequence=['#e74c3c', '#f39c12', '#3498db']
        )
        
        # Map content status
        map_fig = px.bar(
            x=['With Content', 'Without Content'],
            y=[data['maps']['with_content'], data['maps']['without_content']],
            title='Map Content Status', 
            color=['With Content', 'Without Content'],
            color_discrete_sequence=['#27ae60', '#e74c3c']
        )
        
        # County distribution
        if data['counties']:
            counties = list(data['counties'].keys())
            counts = list(data['counties'].values())
            county_fig = px.bar(
                x=counties,
                y=counts,
                title='Maps per County',
                color_discrete_sequence=['#9b59b6']
            )
        else:
            county_fig = px.bar(title='No County Data Available')
        
        return (
            str(data['users']['total']),
            str(data['maps']['total']),
            str(data['maps']['with_content']), 
            str(data['users']['active']),
            user_fig,
            map_fig,
            county_fig
        )
    
    return app
```

## Summary of Changes

### Files Removed:
- ✅ `dash_analytics.py` - Delete this file

### Files Modified:
- ✅ `main.py` - Update imports, integration, and routes
- ✅ Create `precinct_dashboard.py` - New dashboard with real NC data

### Route Changes:
- **Before**: `/analysis` → redirects to `/dash/analytics/`  
- **After**: `/analysis` → redirects to `/dashboard/` (new precinct dashboard)

### Benefits:
- ✅ **Real Data**: Uses actual NC database (Users, Maps tables)
- ✅ **Precinct-Focused**: Shows relevant precinct management metrics
- ✅ **Modern UI**: Clean, responsive dashboard design  
- ✅ **Live Updates**: Auto-refreshes every 30 seconds
- ✅ **Access Control**: Maintains admin/county user restrictions

## Testing Steps:
1. **Remove old file**: `rm dash_analytics.py`
2. **Create new dashboard**: Copy code above to `precinct_dashboard.py`
3. **Update main.py**: Make the three code changes shown above
4. **Test application**: `python main.py`
5. **Visit dashboard**: Go to `/analysis` (redirects to `/dashboard/`)
6. **Verify data**: Check that real NC database data appears

This replaces your existing Dash analytics with a dashboard that shows real precinct management data from your NC PostgreSQL database!