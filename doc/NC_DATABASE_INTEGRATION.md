# NC Database Integration for Maps List

## Overview

This document describes the modifications made to integrate NC (North Carolina) PostgreSQL database functionality for testing map filenames while keeping the view and new tab operations using the local SQLAlchemy maps table.

## Changes Made

### 1. Models (models.py)

#### Added PostgreSQL Support
```python
# Optional PostgreSQL support for NC database
try:
    import psycopg2
    HAS_POSTGRESQL = True
except ImportError:
    HAS_POSTGRESQL = False
```

#### New NCDatabase Class
- **Purpose**: Handle connections to the NC PostgreSQL database
- **Key Methods**:
  - `connect()`: Establish connection to NC database
  - `disconnect()`: Close NC database connection
  - `get_map_filenames()`: Fetch map filenames from NC database maps table
  - `init_app(app)`: Initialize with Flask app configuration

#### NC Database Table Structure
The NC database `maps` table has the same structure as the local maps table:
- `id` (integer, primary key)
- `state` (string)
- `county` (string) 
- `precinct` (string)
- `map` (text, HTML content or filename)
- `created_at` (datetime)

### 2. Configuration (config.py)

#### Added NC Database Configuration
```python
# NC Database Configuration (for testing map filenames)
NC_DATABASE_URL = os.environ.get('NC_DATABASE_URL', 'postgresql://postgres:password@localhost:5432/nc')
```

### 3. Main Application (main.py)

#### Updated Imports
- Added `nc_db` import from models

#### Modified static_content() Route
The route now:
1. **Gets map filenames from NC database** for the list display
2. **Filters by user permissions** (county-level users see only their state/county)
3. **Checks for corresponding local map data** for view/new tab functionality
4. **Falls back to local database maps** if NC database is unavailable
5. **Still includes static file fallback**

#### Key Logic Changes
- **Filename Source**: NC database provides the filenames and display names
- **View/New Tab Source**: Local SQLAlchemy maps table provides actual content
- **Permission Filtering**: Uses NC database state/county info for access control
- **Graceful Degradation**: Falls back to local-only operation if NC database fails

### 4. Templates (templates/static_content.html)

#### Added Source Column
- Shows the source of each map entry (NC Database, Local DB, Static File)
- Color-coded badges for easy identification

#### Enhanced Actions Column
- **NC Database + Local Map**: Full functionality (View + New Tab)
- **NC Database Only**: Disabled actions with explanatory message
- **Local/Static**: Standard functionality

#### Updated About Section
- Explains the three data sources
- Notes about testing mode behavior
- Badge legend for user understanding

## How It Works

### Data Flow for Maps List

1. **Primary Source**: NC database provides map filenames and metadata
   - Query: `SELECT state, county, precinct FROM maps ORDER BY state, county, precinct`
   - Creates filenames as `{precinct}.html`
   - Display names as `NC {state} {county} Precinct {precinct}`

2. **Permission Filtering**: County-level users see only their jurisdiction
   - Uses NC database state/county data for filtering
   - Admin users see all maps

3. **Local Map Lookup**: For each NC database entry, check local maps table
   - Query: `Map.query.filter_by(state=nc_state, county=nc_county, precinct=nc_precinct)`
   - Determines if view/new tab functionality is available

4. **Fallback Behavior**: If NC database unavailable
   - Falls back to local maps table only
   - User sees warning message
   - Standard functionality continues

### View and New Tab Operations

- **Still use local SQLAlchemy maps table** for actual content
- **Filename matching**: Uses filename from NC database to lookup local content
- **get_map_content_by_filename()** function unchanged
- **Existing routes** (view_static_content, view_file_new_tab) work normally

## Testing

### Test Script (test_nc_db.py)
- Verifies PostgreSQL connectivity
- Tests NC database table structure
- Validates map filename retrieval
- Shows configuration settings

### Test Results
- ✓ 112 maps found in NC database
- ✓ All maps are for "NC FORSYTH" county
- ✓ Proper state, county, precinct data available
- ✓ Graceful handling of connection failures

## Usage

### For Development
1. Set NC database URL: `export NC_DATABASE_URL="postgresql://user:pass@host:port/nc"`
2. Ensure psycopg2 is installed: `pip install psycopg2-binary`
3. Run application: Map filenames come from NC database, content from local

### For Production
- If NC database is unavailable, application functions normally with local data
- No breaking changes to existing functionality
- Graceful degradation built-in

## Benefits

1. **Testing Flexibility**: Can test with NC database filenames while using local content
2. **No Breaking Changes**: Existing functionality preserved
3. **Progressive Enhancement**: NC database adds features but isn't required
4. **Clear User Feedback**: UI shows data sources and availability
5. **Proper Access Control**: County-level filtering works with NC data

## Future Enhancements

- Could extend to use NC database for content as well
- Could add caching for NC database queries
- Could add admin interface for NC database management
- Could support multiple external database sources