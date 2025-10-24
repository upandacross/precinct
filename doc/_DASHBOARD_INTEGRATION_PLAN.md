# Integration Plan: Dashboard Code into Precinct Application

## Overview
Integrate the copied dashboard code from `/dashboard` directory into the main precinct application, creating a dual dashboard system:
- **Existing**: `/analysis` → `/dash/analytics/` (political analytics) 
- **New**: `/dashboard` → `/dashboard/` (general dashboard from copied code)

## Current Dashboard Analysis

### Copied Dashboard Structure
```
dashboard/
├── app.py                 # Flask app with Dash integration
├── dashboard_app.py       # Dash app creation and configuration  
├── templates/index.html   # Landing page template
├── requirements.txt       # Dependencies
└── pyproject.toml        # Project configuration
```

### Key Components Found
1. **Flask App** (`app.py`): Simple Flask wrapper
2. **Dash App** (`dashboard_app.py`): Full dashboard with:
   - Sample data generation
   - Multiple chart types (sales, categories, etc.)
   - Interactive callbacks
   - Professional styling
3. **Template** (`index.html`): Landing page with dashboard link
4. **Dependencies**: Standard Dash/Flask stack

## Integration Strategy

### Phase 1: Copy Dashboard Components

#### 1.1 Copy Dashboard App Module
```bash
# Copy the main dashboard code
cp dashboard/dashboard_app.py ./dashboard_service.py
```

#### 1.2 Adapt Dashboard for Precinct Context
Modify `dashboard_service.py` to:
- Change sample data to precinct-relevant data
- Use NC database for real data
- Adapt styling to match precinct theme
- Add authentication integration

#### 1.3 Copy Static Assets
```bash
# If there are any static files in dashboard
cp -r dashboard/static/* static/ 2>/dev/null || true
```

### Phase 2: Integrate into Main Flask App

#### 2.1 Update main.py Dependencies
Add to top of `main.py`:
```python
# Add dashboard import (after adapting dashboard_app.py)
from dashboard_service import create_precinct_dashboard
```

#### 2.2 Add Dashboard Route
Add to `main.py` after existing routes:
```python
@app.route('/dashboard')
@login_required
def dashboard_redirect():
    """Redirect to integrated dashboard"""
    if not (current_user.is_admin or current_user.is_county):
        flash('Access denied. Dashboard available to administrators and county users only.', 'error')
        return redirect(url_for('index'))
    
    return redirect('/precinct-dashboard/')
```

#### 2.3 Integrate Dash App
Add to create_app() function in main.py:
```python
def create_app():
    app = Flask(__name__)
    # ... existing setup ...
    
    # Integrate existing analytics (keep)
    if DASH_AVAILABLE:
        create_dash_app(app)  # Existing: /dash/analytics/
    
    # Integrate new dashboard
    precinct_dashboard = create_precinct_dashboard()
    precinct_dashboard.init_app(app)  # New: /precinct-dashboard/
    
    return app
```

### Phase 3: Adapt Dashboard Content

#### 3.1 Create Precinct-Specific Dashboard Service
Modify copied `dashboard_service.py`:
```python
import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from models import db, User, Map
from datetime import datetime, timedelta

def create_precinct_dashboard():
    """Create precinct-focused dashboard"""
    app = dash.Dash(__name__, 
                   url_base_pathname='/precinct-dashboard/', 
                   external_stylesheets=[
                       'https://codepen.io/chriddyp/pen/bWLwgP.css',
                       {
                           'href': 'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap',
                           'rel': 'stylesheet'
                       }
                   ])
    
    def get_precinct_data():
        """Get real data from NC database"""
        try:
            # User statistics
            total_users = User.query.count()
            admin_users = User.query.filter_by(is_admin=True).count()
            county_users = User.query.filter_by(is_county=True).count()
            
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
                    'regular': total_users - admin_users - county_users
                },
                'maps': {
                    'total': total_maps,
                    'with_content': maps_with_content,
                    'without_content': total_maps - maps_with_content
                },
                'counties': dict(county_stats)
            }
        except Exception as e:
            print(f"Database error: {e}")
            return None
    
    # Dashboard layout
    app.layout = html.Div([
        html.Div([
            html.H1("Precinct Management Dashboard", 
                   style={'textAlign': 'center', 'color': '#2c3e50', 'marginBottom': 30}),
            html.P("Overview of precinct users, maps, and county statistics",
                   style={'textAlign': 'center', 'color': '#7f8c8d', 'marginBottom': 40})
        ], className='header'),
        
        # Stats cards row
        html.Div([
            html.Div([
                html.Div([
                    html.H3(id='total-users', children='0', style={'margin': 0, 'color': '#3498db'}),
                    html.P('Total Users', style={'margin': 0, 'color': '#7f8c8d'})
                ], className='stat-card')
            ], className='three columns'),
            
            html.Div([
                html.Div([
                    html.H3(id='total-maps', children='0', style={'margin': 0, 'color': '#e74c3c'}),
                    html.P('Total Maps', style={'margin': 0, 'color': '#7f8c8d'})
                ], className='stat-card')
            ], className='three columns'),
            
            html.Div([
                html.Div([
                    html.H3(id='maps-with-content', children='0', style={'margin': 0, 'color': '#27ae60'}),
                    html.P('Maps with Content', style={'margin': 0, 'color': '#7f8c8d'})
                ], className='stat-card')
            ], className='three columns'),
            
            html.Div([
                html.Div([
                    html.H3(id='admin-users', children='0', style={'margin': 0, 'color': '#f39c12'}),
                    html.P('Admin Users', style={'margin': 0, 'color': '#7f8c8d'})
                ], className='stat-card')
            ], className='three columns'),
        ], className='row', style={'marginBottom': 40}),
        
        # Charts row
        html.Div([
            html.Div([
                dcc.Graph(id='user-distribution')
            ], className='six columns'),
            
            html.Div([
                dcc.Graph(id='map-content-status')
            ], className='six columns'),
        ], className='row'),
        
        html.Div([
            html.Div([
                dcc.Graph(id='county-distribution')
            ], className='twelve columns'),
        ], className='row'),
        
        # Auto-refresh interval
        dcc.Interval(
            id='interval-component',
            interval=30*1000,  # Update every 30 seconds
            n_intervals=0
        )
    ])
    
    @app.callback(
        [Output('total-users', 'children'),
         Output('total-maps', 'children'), 
         Output('maps-with-content', 'children'),
         Output('admin-users', 'children'),
         Output('user-distribution', 'figure'),
         Output('map-content-status', 'figure'),
         Output('county-distribution', 'figure')],
        [Input('interval-component', 'n_intervals')]
    )
    def update_dashboard(n):
        data = get_precinct_data()
        
        if not data:
            # Return empty values on error
            empty_fig = {'data': [], 'layout': {'title': 'Data not available'}}
            return '0', '0', '0', '0', empty_fig, empty_fig, empty_fig
        
        # Update stat values
        total_users = str(data['users']['total'])
        total_maps = str(data['maps']['total']) 
        maps_with_content = str(data['maps']['with_content'])
        admin_users = str(data['users']['admins'])
        
        # User distribution pie chart
        user_fig = px.pie(
            values=[data['users']['admins'], data['users']['county'], data['users']['regular']], 
            names=['Admins', 'County Users', 'Regular Users'],
            title='User Distribution',
            color_discrete_sequence=['#e74c3c', '#f39c12', '#3498db']
        )
        
        # Map content status bar chart
        map_fig = px.bar(
            x=['With Content', 'Without Content'],
            y=[data['maps']['with_content'], data['maps']['without_content']],
            title='Map Content Status',
            color=['With Content', 'Without Content'],
            color_discrete_sequence=['#27ae60', '#e74c3c']
        )
        
        # County distribution bar chart
        counties = list(data['counties'].keys())
        counts = list(data['counties'].values())
        county_fig = px.bar(
            x=counties,
            y=counts, 
            title='Maps per County',
            color_discrete_sequence=['#9b59b6']
        )
        
        return (total_users, total_maps, maps_with_content, admin_users,
                user_fig, map_fig, county_fig)
    
    return app
```

### Phase 4: Update Navigation

#### 4.1 Add Dashboard Links
Update navigation in templates to include both:
- **Analytics** (existing Dash): `/analysis` 
- **Dashboard** (new): `/dashboard`

In `templates/base.html`:
```html
<!-- Add to navigation -->
{% if current_user.is_admin or current_user.is_county %}
<li class="nav-item dropdown">
    <a class="nav-link dropdown-toggle" href="#" id="dashboardDropdown" role="button" data-bs-toggle="dropdown">
        <i class="fas fa-chart-line"></i> Analytics & Dashboards
    </a>
    <ul class="dropdown-menu">
        <li><a class="dropdown-item" href="{{ url_for('analysis') }}">
            <i class="fas fa-analytics"></i> Precinct Analytics
        </a></li>
        <li><a class="dropdown-item" href="{{ url_for('dashboard_redirect') }}">
            <i class="fas fa-tachometer-alt"></i> Management Dashboard  
        </a></li>
    </ul>
</li>
{% endif %}
```

## Implementation Steps

1. **Copy dashboard_app.py** → `dashboard_service.py`
2. **Adapt dashboard code** for precinct data and NC database
3. **Update main.py** to integrate new dashboard alongside existing analytics
4. **Update navigation** to show both dashboard options
5. **Test both systems** work independently
6. **Style dashboard** to match precinct application theme

## Benefits

- **Dual Dashboard System**: Analytics + Management views
- **Keep Existing Investment**: Preserve current Dash analytics
- **Proven Code Base**: Use working dashboard code  
- **Precinct-Focused Data**: Real data from NC database
- **Enhanced Functionality**: Multiple dashboard perspectives

## Testing Plan

- [ ] Existing analytics still work at `/analysis`
- [ ] New dashboard loads at `/dashboard` → `/precinct-dashboard/`
- [ ] Both dashboards respect authentication  
- [ ] Real NC database data populates new dashboard
- [ ] Navigation works for both dashboard types
- [ ] Styling consistent with precinct theme