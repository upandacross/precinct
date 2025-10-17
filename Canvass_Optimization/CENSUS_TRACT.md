# Census Data Import and Processing Guide

## Overview

This directory contains a complete toolkit for importing and processing US Census Bureau data for canvass optimization analysis in Forsyth County, North Carolina. The system provides both comprehensive SQLAlchemy-based database import and lightweight CSV/JSON processing options.

## 🗂️ Project Structure

```
Canvass_Optimization/
├── 📊 Interactive Maps
│   ├── forsyth_precinct_704_map.html           # Precinct 704 buffer analysis
│   └── forsyth_precincts_census_intersection.html  # Spatial intersection analysis
├── 🐍 Census Import Tools
│   ├── census_data_importer.py                 # Full SQLAlchemy + PostGIS importer
│   └── simple_census_processor.py              # Lightweight CSV/JSON processor
├── ⚙️ Configuration
│   ├── census_config.ini                       # Main configuration file
│   ├── requirements.txt                        # Python dependencies
│   ├── setup_census_import.sh                  # Linux/macOS setup script
│   └── setup_census_import.bat                 # Windows setup script
└── 📖 Documentation
    └── CENSUS_README.md                         # This file
```

## 🚀 Quick Start

### 1. Environment Setup

**Linux/macOS:**
```bash
chmod +x setup_census_import.sh
./setup_census_import.sh
```

**Windows:**
```cmd
setup_census_import.bat
```

### 2. Get Census API Key (Free)
1. Visit: https://api.census.gov/data/key_signup.html
2. Sign up for a free API key
3. Edit `census_config.ini` and replace `YOUR_CENSUS_API_KEY_HERE` with your key

### 3. Basic Usage

**Simple Processing (No Database):**
```bash
# Activate virtual environment
source canvass_env/bin/activate

# Generate CSV report for Forsyth County
python simple_census_processor.py --state 37 --county 067 --format csv

# Generate JSON data with API key
python simple_census_processor.py --api-key YOUR_KEY --format json

# Generate human-readable canvass report
python simple_census_processor.py --format report
```

**Full Database Import:**
```bash
# Configure database in census_config.ini first
python census_data_importer.py --config census_config.ini

# Or use command line options
python census_data_importer.py --database postgresql://user:pass@localhost/db --state 37 --county 067
```

## 📊 Interactive Maps

### Precinct 704 Analysis Map
- **File**: `forsyth_precinct_704_map.html`
- **Purpose**: Interactive map showing precinct 704 with 50-meter buffer analysis
- **Features**:
  - Leaflet.js-powered interactive mapping
  - Precinct boundary visualization
  - 50-meter buffer zone for canvassing coordination
  - Adjacent precincts display (604, 703, 702, 705, 607)
  - Responsive design with popup details
  - Area calculations and demographic overlay

### Census Tract Intersection Analysis
- **File**: `forsyth_precincts_census_intersection.html`
- **Purpose**: Spatial analysis of precinct-census tract intersections
- **Features**:
  - PostGIS spatial query visualization
  - Interactive layer toggles (precincts, census tracts, intersections)
  - Intersection area calculations and percentages
  - Real-time spatial relationship analysis
  - SQL query display panel

## 🛠️ Tools Overview

### 1. Census Data Importer (`census_data_importer.py`)

**Comprehensive SQLAlchemy-based import tool with full PostGIS integration**

**Features:**
- Complete Census API integration
- TIGER/Line shapefile download and processing
- PostgreSQL + PostGIS spatial database support
- SQLite and MySQL compatibility
- Alembic database migration support
- Spatial indexing and performance optimization
- Geometry validation and error handling

**Key Command Line Options:**
```bash
python census_data_importer.py [OPTIONS]

Options:
  -c, --config FILE          Configuration file path (default: census_config.ini)
  --state TEXT              State FIPS code (e.g., 37 for NC)
  --county TEXT             County FIPS code (e.g., 067 for Forsyth)
  --database TEXT           Database URL
  --api-key TEXT            Census API key
  --import-existing         Re-import existing records
  --postgis-legacy          Use legacy PostGIS functions
  --create-config          Create sample configuration file
  -v, --verbose            Enable verbose logging
  --help                   Show help message
```

**Database Models:**
- `CensusTracts`: TIGER/Line census tract geometries
- `CensusDemographics`: ACS demographic variables
- `VotingPrecincts`: Precinct boundaries and voter data

### 2. Simple Census Processor (`simple_census_processor.py`)

**Lightweight alternative with no database dependencies**

**Features:**
- Direct Census API integration
- CSV, JSON, and human-readable report output
- No database installation required
- Standalone operation
- Built-in demographic analysis for canvass optimization

**Key Command Line Options:**
```bash
python simple_census_processor.py [OPTIONS]

Options:
  --state TEXT              State FIPS code (default: 37 for NC)
  --county TEXT             County FIPS code (default: 067 for Forsyth)
  --year TEXT               Census data year (default: 2022)
  --api-key TEXT            Census API key
  --format [csv|json|report] Output format (default: csv)
  --output TEXT             Output file path
  -v, --verbose             Enable verbose logging
  --help                    Show help message
```

**Output Formats:**
- **CSV**: Structured data suitable for Excel/analysis tools
- **JSON**: Machine-readable format for web applications
- **Report**: Human-readable canvass optimization summary

## ⚙️ Configuration

### Main Configuration File (`census_config.ini`)

```ini
[census]
api_key = YOUR_CENSUS_API_KEY_HERE
state_fips = 37         # North Carolina
county_fips = 067       # Forsyth County
year = 2022
dataset = acs/acs5

[database]
database_url = postgresql://postgres:password@localhost:5432/canvass_optimization
postgis_legacy = false
schema_name = census

[import]
import_existing = false
validate_geometry = true
create_indexes = true
download_shapefiles = true

[canvass_optimization]
target_precincts = 704,703,702,705,604,607
demographic_variables = B01003_001E,B25001_001E,B19013_001E,B25077_001E
high_density_threshold = 1000
renter_heavy_threshold = 0.6
```

### Database Configuration Options

**PostgreSQL (Recommended for full functionality):**
```ini
database_url = postgresql://username:password@localhost:5432/canvass_optimization
```

**SQLite (For development/testing):**
```ini
database_url = sqlite:///census_data.db
```

**MySQL:**
```ini
database_url = mysql://username:password@localhost:3306/canvass_optimization
```

## 📈 Census Variables for Canvass Optimization

The system focuses on demographic variables most relevant to voter canvassing:

### Population and Housing
- `B01003_001E`: Total Population
- `B25001_001E`: Total Housing Units
- `B25003_002E`: Owner-Occupied Housing Units
- `B25003_003E`: Renter-Occupied Housing Units

### Economic Indicators
- `B19013_001E`: Median Household Income
- `B25077_001E`: Median Home Value

### Demographics for Voter Analysis
- `B08303_001E`: Total Commuters (work patterns)
- `B15003_022E`: Bachelor's Degree (education levels)

### Age Groups (Voter Turnout Analysis)
- `B01001_007E` through `B01001_033E`: Age groups by sex (18-29 focus)

## 🗺️ PostGIS Spatial Analysis

The system performs sophisticated spatial analysis using PostGIS:

### Key Spatial Operations
1. **ST_Intersects()**: Find precincts that overlap with census tracts
2. **ST_Intersection()**: Calculate exact overlap areas
3. **ST_Area()**: Measure intersection areas
4. **ST_Buffer()**: Create canvassing buffer zones
5. **ST_Within()**: Identify containment relationships

### Example Spatial Query
```sql
-- Find precinct-census tract intersections with area calculations
SELECT 
    p.precinct_id,
    c.geoid as tract_geoid,
    ST_Area(ST_Intersection(p.geom, c.geom)) as intersection_area,
    ROUND((ST_Area(ST_Intersection(p.geom, c.geom)) / ST_Area(p.geom)) * 100, 2) as precinct_pct
FROM voting_precincts p
JOIN census_tracts c ON ST_Intersects(p.geom, c.geom)
WHERE p.precinct_id = '704'
ORDER BY intersection_area DESC;
```

## 🎯 Canvass Optimization Analysis

### High-Priority Areas for Canvassing

1. **High-Density Areas**: Census tracts with >1000 housing units
2. **Renter-Heavy Areas**: Tracts with >60% rental occupancy
3. **Young Adult Concentrations**: High 18-29 population areas
4. **Buffer Zones**: 50-meter walking buffers around precinct boundaries

### Analysis Workflow

1. **Import Census Data**: Demographics and tract boundaries
2. **Import Precinct Data**: Voting precinct boundaries
3. **Spatial Analysis**: Calculate intersections and buffer zones
4. **Demographic Overlay**: Map population characteristics to areas
5. **Priority Ranking**: Score areas based on canvass factors

## 🔧 Troubleshooting

### Common Issues

**Census API Rate Limits:**
- The Census API has rate limits but they're quite generous
- The system includes automatic retry and error handling
- Use your API key to avoid most limitations

**PostGIS Installation Issues:**
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib postgis

# macOS with Homebrew
brew install postgresql postgis

# Verify installation
psql -c "SELECT PostGIS_version();"
```

**Python Dependencies:**
```bash
# If installation fails, try updating pip first
pip install --upgrade pip

# Install with specific versions if needed
pip install 'sqlalchemy>=2.0.0' 'geoalchemy2>=0.14.0'

# For geometric operations issues
pip install --upgrade shapely
```

**Database Connection Issues:**
1. Verify PostgreSQL is running: `sudo service postgresql start`
2. Check database exists: `psql -l`
3. Test connection: `psql -U postgres -d canvass_optimization`
4. Verify PostGIS extension: `SELECT * FROM pg_extension WHERE extname = 'postgis';`

### Performance Optimization

**For Large Datasets:**
1. Increase batch size in configuration
2. Create spatial indexes: `CREATE INDEX idx_geom ON table USING GIST (geom);`
3. Use connection pooling for multiple imports
4. Consider partitioning large tables by geographic area

**Memory Issues:**
1. Process data in smaller geographic chunks
2. Use streaming processing for large shapefiles
3. Increase PostgreSQL shared_buffers setting
4. Consider using PostGIS raster for very large datasets

## 📝 Data Sources

### US Census Bureau APIs
- **ACS 5-Year Estimates**: Most recent comprehensive demographic data
- **TIGER/Line Shapefiles**: Official census tract boundaries
- **Decennial Census**: Population counts (every 10 years)

### North Carolina Specific
- **State FIPS**: 37
- **Forsyth County FIPS**: 067
- **Major Cities**: Winston-Salem, Kernersville, Clemmons

### Voting Precinct Data
- Source: Forsyth County Board of Elections
- Format: Shapefile or GeoJSON
- Updates: After redistricting or precinct changes

## 🤝 Contributing

### Code Standards
- Follow PEP 8 for Python code formatting
- Use type hints where possible
- Include docstrings for all functions
- Add logging for important operations

### Testing
```bash
# Run tests
pytest tests/

# With coverage
pytest --cov=. tests/

# Specific test
pytest tests/test_census_importer.py
```

### Adding New Census Variables
1. Add variable definitions to `CANVASS_VARIABLES` in `simple_census_processor.py`
2. Update the configuration file with new variable codes
3. Add processing logic in both importers
4. Update documentation

## 📞 Support

### Resources
- **Census API Documentation**: https://www.census.gov/data/developers/data-sets.html
- **PostGIS Documentation**: https://postgis.net/documentation/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Leaflet.js Documentation**: https://leafletjs.com/

### Getting Help
1. Check the logs in `census_import.log`
2. Enable verbose mode with `-v` flag
3. Verify configuration settings
4. Test with simple processor first
5. Check database connectivity separately

---

## 📄 License

This project is designed for civic engagement and canvass optimization. Please ensure compliance with your local election laws and data usage regulations when using this system for political activities.

**Last Updated**: December 2024
**Version**: 1.0.0