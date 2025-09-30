# Dash Analytics Integration

## Overview
The Precinct Analytics page has been converted from JavaScript (Chart.js) to Python Dash library for more powerful data visualization and interactivity.

## Features
- **Interactive Charts**: Built with Plotly for smooth interactions and zooming
- **Real-time Data**: Pulls actual user statistics from the database
- **Python-based**: All chart logic is now in Python instead of JavaScript
- **Responsive Design**: Maintains Bootstrap styling for consistency
- **Multiple Chart Types**: Pie charts, line charts, bar charts, and multi-line charts

## Installation

### Option 1: Automatic Installation
```bash
./install_dash.sh
```

### Option 2: Manual Installation
```bash
source .venv/bin/activate
pip install -r dash_requirements.txt
```

### Option 3: Individual Packages
```bash
pip install dash plotly pandas
```

## Usage
1. Install the required packages using one of the methods above
2. Restart your Flask application
3. Navigate to the "Precinct Analytics" page from the main navigation
4. The app will automatically redirect to the Dash analytics dashboard at `/dash/analytics/`

## Fallback Behavior
If Dash packages are not installed:
- The analytics link will redirect to the main dashboard
- A warning message will be displayed indicating missing packages
- The main Flask app continues to work normally

## Files Added
- `dash_analytics.py` - Main Dash application with all charts
- `dash_requirements.txt` - Required packages for Dash functionality
- `install_dash.sh` - Automatic installation script

## Technical Details
- **Route**: `/analysis` redirects to `/dash/analytics/`
- **Integration**: Dash app is embedded within the Flask application
- **Data Source**: Real user statistics + sample trend data
- **Styling**: Uses Bootstrap 5 and Font Awesome for consistent appearance

## Charts Included
1. **User Distribution** (Pie Chart) - Regular vs Admin vs Inactive users
2. **Password Strength** (Pie Chart) - Weak vs Medium vs Strong passwords
3. **Monthly Registrations** (Line Chart) - User signup trends over time
4. **Weekly Login Activity** (Bar Chart) - Login patterns by day of week
5. **Recent Activity Trends** (Multi-line Chart) - Logins vs Registrations comparison

## Customization
To add more charts or modify existing ones, edit the `dash_analytics.py` file and add new figures to the layout.