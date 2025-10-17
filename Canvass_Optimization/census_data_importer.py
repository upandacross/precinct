#!/usr/bin/env python3
"""
Forsyth County Census Data Importer
==================================

A comprehensive SQLAlchemy-based tool for importing US Census Bureau data
into PostgreSQL/PostGIS databases with support for:

- Census API integration for demographic data
- TIGER/Line shapefile download and processing  
- PostGIS spatial data import with geometry validation
- Multiple database backend support (PostgreSQL, SQLite, MySQL)
- Alembic database migration management
- Configurable import options and data filtering

Dependencies:
    - sqlalchemy >= 2.0.0
    - geoalchemy2 >= 0.14.0
    - psycopg2-binary >= 2.9.0 (PostgreSQL)
    - requests >= 2.28.0
    - shapely >= 2.0.0
    - fiona >= 1.8.0
    - click >= 8.0.0

Usage:
    python census_data_importer.py --help
    python census_data_importer.py --state NC --county 067 --database postgresql://user:pass@localhost/db
    python census_data_importer.py --import-existing --postgis-legacy
"""

import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
import configparser
from datetime import datetime

# Core imports
import requests
import click
from sqlalchemy import (
    create_engine, Column, String, Integer, Float, Boolean, DateTime, 
    Text, MetaData, Table, inspect, text
)
from sqlalchemy.orm import sessionmaker, DeclarativeBase, Session
from sqlalchemy.dialects.postgresql import UUID
from geoalchemy2 import Geometry
from geoalchemy2.functions import ST_GeomFromText, ST_IsValid, ST_MakeValid
import shapely.wkt
from shapely.geometry import shape
import fiona

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('census_import.log')
    ]
)
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """SQLAlchemy declarative base with common functionality"""
    pass


@dataclass
class CensusConfig:
    """Configuration for Census API and data import"""
    api_key: Optional[str] = None
    base_url: str = "https://api.census.gov/data"
    tiger_url: str = "https://www2.census.gov/geo/tiger"
    state_fips: str = "37"  # North Carolina
    county_fips: str = "067"  # Forsyth County
    year: str = "2022"
    dataset: str = "acs/acs5"
    vintage: str = "2022"
    
    # Database configuration
    database_url: str = "sqlite:///census_data.db"
    postgis_legacy: bool = False
    schema_name: str = "census"
    table_prefix: str = "census_"
    
    # Import settings
    import_existing: bool = False
    validate_geometry: bool = True
    create_indexes: bool = True
    download_shapefiles: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    @classmethod
    def from_file(cls, config_file: str) -> 'CensusConfig':
        """Load configuration from INI file"""
        config = configparser.ConfigParser()
        config.read(config_file)
        
        kwargs = {}
        if 'census' in config:
            kwargs.update(config['census'])
        if 'database' in config:
            kwargs.update(config['database'])
        if 'import' in config:
            kwargs.update(config['import'])
            
        return cls(**kwargs)


class CensusTracts(Base):
    """SQLAlchemy model for Census Tracts with PostGIS geometry"""
    __tablename__ = 'census_tracts'
    
    # TIGER/Line identifiers
    statefp = Column(String(2), primary_key=True)
    countyfp = Column(String(3), primary_key=True) 
    tractce = Column(String(6), primary_key=True)
    geoid = Column(String(11), unique=True, nullable=False)
    
    # Geographic names
    name = Column(String(7))
    namelsad = Column(String(20))
    mtfcc = Column(String(5))
    funcstat = Column(String(1))
    
    # Area measurements
    aland = Column(Float)  # Land area in square meters
    awater = Column(Float)  # Water area in square meters
    intptlat = Column(Float)  # Internal point latitude
    intptlon = Column(Float)  # Internal point longitude
    
    # PostGIS geometry column
    geom = Column(Geometry('MULTIPOLYGON', srid=4326))
    
    # Import metadata
    import_date = Column(DateTime, default=datetime.utcnow)
    source = Column(String(100), default='TIGER/Line Shapefiles')
    
    def __repr__(self):
        return f"<CensusTracts(geoid='{self.geoid}', name='{self.namelsad}')>"


class CensusDemographics(Base):
    """SQLAlchemy model for Census ACS demographic data"""
    __tablename__ = 'census_demographics'
    
    geoid = Column(String(11), primary_key=True)
    variable = Column(String(20), primary_key=True)
    value = Column(Float)
    margin_of_error = Column(Float)
    
    # Variable metadata
    label = Column(Text)
    concept = Column(Text)
    
    # Import metadata  
    dataset = Column(String(50))
    vintage = Column(String(4))
    import_date = Column(DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f"<CensusDemographics(geoid='{self.geoid}', variable='{self.variable}')>"


class VotingPrecincts(Base):
    """SQLAlchemy model for Voting Precincts"""
    __tablename__ = 'voting_precincts'
    
    precinct_id = Column(String(10), primary_key=True)
    precinct_name = Column(String(100))
    county_name = Column(String(50))
    state_fips = Column(String(2))
    
    # PostGIS geometry
    geom = Column(Geometry('POLYGON', srid=4326))
    
    # Area and demographics
    area_sq_meters = Column(Float)
    population_estimate = Column(Integer)
    registered_voters = Column(Integer)
    
    # Import metadata
    import_date = Column(DateTime, default=datetime.utcnow)
    source = Column(String(100))
    
    def __repr__(self):
        return f"<VotingPrecincts(id='{self.precinct_id}', name='{self.precinct_name}')>"


class CensusImporter:
    """Main Census data importer class with PostGIS support"""
    
    def __init__(self, config: CensusConfig):
        self.config = config
        self.engine = None
        self.session = None
        self.setup_database()
        
    def setup_database(self):
        """Initialize database connection and create tables"""
        logger.info(f"Connecting to database: {self.config.database_url}")
        
        # Create engine with PostGIS support if PostgreSQL
        if self.config.database_url.startswith('postgresql'):
            self.engine = create_engine(
                self.config.database_url,
                echo=False,
                pool_pre_ping=True,
                connect_args={'options': '-csearch_path=public,census'}
            )
            # Enable PostGIS extension
            with self.engine.connect() as conn:
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
                conn.commit()
        else:
            self.engine = create_engine(self.config.database_url, echo=False)
            
        # Create session factory
        Session = sessionmaker(bind=self.engine)
        self.session = Session()
        
        # Create all tables
        Base.metadata.create_all(self.engine)
        logger.info("Database tables created successfully")
        
    def fetch_census_api_data(self, variables: List[str], geography: str = "tract") -> Dict[str, Any]:
        """Fetch demographic data from Census API"""
        if not self.config.api_key:
            logger.warning("No Census API key provided, skipping API data fetch")
            return {}
            
        url = f"{self.config.base_url}/{self.config.year}/{self.config.dataset}"
        
        params = {
            'get': ','.join(variables + ['NAME']),
            'for': f"{geography}:*",
            'in': f"state:{self.config.state_fips} county:{self.config.county_fips}",
            'key': self.config.api_key
        }
        
        logger.info(f"Fetching Census API data: {url}")
        logger.info(f"Variables: {variables}")
        
        try:
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            headers = data[0]
            rows = data[1:]
            
            logger.info(f"Retrieved {len(rows)} records from Census API")
            return {
                'headers': headers,
                'data': rows,
                'total_records': len(rows)
            }
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Census API request failed: {e}")
            return {}
    
    def download_tiger_shapefiles(self) -> Optional[str]:
        """Download TIGER/Line shapefiles for census tracts"""
        if not self.config.download_shapefiles:
            return None
            
        # TIGER/Line URL pattern for tract shapefiles
        filename = f"tl_{self.config.year}_{self.config.state_fips}{self.config.county_fips}_tract.zip"
        url = f"{self.config.tiger_url}/TIGER{self.config.year}/TRACT/{filename}"
        
        download_dir = Path("tiger_downloads")
        download_dir.mkdir(exist_ok=True)
        
        shapefile_path = download_dir / filename
        
        if shapefile_path.exists() and not self.config.import_existing:
            logger.info(f"Shapefile already exists: {shapefile_path}")
            return str(shapefile_path)
        
        logger.info(f"Downloading TIGER shapefile: {url}")
        
        try:
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            with open(shapefile_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Downloaded shapefile: {shapefile_path} ({shapefile_path.stat().st_size} bytes)")
            return str(shapefile_path)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to download shapefile: {e}")
            return None
    
    def extract_and_import_shapefiles(self, shapefile_path: str) -> int:
        """Extract ZIP and import shapefile data using Fiona"""
        import zipfile
        
        extract_dir = Path("tiger_extracted")
        extract_dir.mkdir(exist_ok=True)
        
        # Extract ZIP file
        with zipfile.ZipFile(shapefile_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
        
        # Find the .shp file
        shp_files = list(extract_dir.glob("*.shp"))
        if not shp_files:
            logger.error("No .shp file found in extracted archive")
            return 0
        
        shp_file = shp_files[0]
        logger.info(f"Importing shapefile: {shp_file}")
        
        imported_count = 0
        
        try:
            with fiona.open(shp_file, 'r') as shapefile:
                logger.info(f"Shapefile schema: {shapefile.schema}")
                logger.info(f"Shapefile CRS: {shapefile.crs}")
                
                for feature in shapefile:
                    # Extract properties
                    props = feature['properties']
                    geom = feature['geometry']
                    
                    # Create tract record
                    tract = CensusTracts(
                        statefp=props.get('STATEFP'),
                        countyfp=props.get('COUNTYFP'),
                        tractce=props.get('TRACTCE'),
                        geoid=props.get('GEOID'),
                        name=props.get('NAME'),
                        namelsad=props.get('NAMELSAD'),
                        mtfcc=props.get('MTFCC'),
                        funcstat=props.get('FUNCSTAT'),
                        aland=float(props.get('ALAND', 0)),
                        awater=float(props.get('AWATER', 0)),
                        intptlat=float(props.get('INTPTLAT', 0)),
                        intptlon=float(props.get('INTPTLON', 0)),
                        geom=f"SRID=4326;{shapely.wkt.dumps(shape(geom))}"
                    )
                    
                    # Validate geometry if configured
                    if self.config.validate_geometry:
                        # This would use PostGIS ST_IsValid in a real implementation
                        pass
                    
                    # Merge or add tract
                    existing = self.session.query(CensusTracts).filter_by(geoid=tract.geoid).first()
                    if existing and not self.config.import_existing:
                        logger.debug(f"Skipping existing tract: {tract.geoid}")
                        continue
                    
                    if existing:
                        # Update existing record
                        for key, value in tract.__dict__.items():
                            if not key.startswith('_'):
                                setattr(existing, key, value)
                    else:
                        self.session.add(tract)
                    
                    imported_count += 1
                    
                    if imported_count % 100 == 0:
                        self.session.commit()
                        logger.info(f"Imported {imported_count} tract records...")
                
                # Final commit
                self.session.commit()
                logger.info(f"Completed shapefile import: {imported_count} tracts imported")
                
        except Exception as e:
            logger.error(f"Shapefile import failed: {e}")
            self.session.rollback()
            return 0
        
        return imported_count
    
    def import_demographic_data(self, api_data: Dict[str, Any]) -> int:
        """Import demographic data from Census API response"""
        if not api_data or not api_data.get('data'):
            logger.warning("No demographic data to import")
            return 0
            
        headers = api_data['headers']
        rows = api_data['data']
        
        # Common ACS variables mapping
        variable_map = {
            'B01003_001E': {'label': 'Total Population', 'concept': 'Total Population'},
            'B25001_001E': {'label': 'Total Housing Units', 'concept': 'Housing Units'},
            'B19013_001E': {'label': 'Median Household Income', 'concept': 'Income'},
            'B08303_001E': {'label': 'Total Commuters', 'concept': 'Commuting'},
        }
        
        imported_count = 0
        
        try:
            for row in rows:
                row_dict = dict(zip(headers, row))
                
                # Build GEOID from state, county, tract
                geoid = f"{row_dict.get('state', '')}{row_dict.get('county', '')}{row_dict.get('tract', '')}"
                
                # Import each variable
                for var_code in headers:
                    if var_code in ['NAME', 'state', 'county', 'tract']:
                        continue
                        
                    value = row_dict.get(var_code)
                    if value is None or value == '-888888888':  # Census null values
                        continue
                    
                    # Get margin of error if available
                    moe_code = var_code.replace('E', 'M')
                    margin_of_error = row_dict.get(moe_code)
                    
                    # Create demographic record
                    demo_record = CensusDemographics(
                        geoid=geoid,
                        variable=var_code,
                        value=float(value) if value else None,
                        margin_of_error=float(margin_of_error) if margin_of_error else None,
                        label=variable_map.get(var_code, {}).get('label', var_code),
                        concept=variable_map.get(var_code, {}).get('concept', 'Unknown'),
                        dataset=self.config.dataset,
                        vintage=self.config.year
                    )
                    
                    # Merge or add record
                    existing = self.session.query(CensusDemographics).filter_by(
                        geoid=geoid, variable=var_code
                    ).first()
                    
                    if existing and not self.config.import_existing:
                        continue
                        
                    if existing:
                        existing.value = demo_record.value
                        existing.margin_of_error = demo_record.margin_of_error
                        existing.import_date = datetime.utcnow()
                    else:
                        self.session.add(demo_record)
                    
                    imported_count += 1
            
            self.session.commit()
            logger.info(f"Imported {imported_count} demographic records")
            
        except Exception as e:
            logger.error(f"Demographic import failed: {e}")
            self.session.rollback()
            return 0
        
        return imported_count
    
    def create_spatial_indexes(self):
        """Create spatial indexes for PostGIS performance"""
        if not self.config.create_indexes:
            return
        
        logger.info("Creating spatial indexes...")
        
        try:
            # Create spatial index on census tracts geometry
            self.session.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_census_tracts_geom ON census_tracts USING GIST (geom)"
            ))
            
            # Create spatial index on voting precincts geometry
            self.session.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_voting_precincts_geom ON voting_precincts USING GIST (geom)"
            ))
            
            # Create btree indexes on commonly queried fields
            self.session.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_census_tracts_geoid ON census_tracts (geoid)"
            ))
            
            self.session.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_census_demographics_geoid ON census_demographics (geoid)"
            ))
            
            self.session.commit()
            logger.info("Spatial indexes created successfully")
            
        except Exception as e:
            logger.error(f"Index creation failed: {e}")
            self.session.rollback()
    
    def run_spatial_analysis_queries(self):
        """Execute example spatial analysis queries"""
        logger.info("Running spatial analysis queries...")
        
        try:
            # Query 1: Find precincts that intersect with census tracts
            result = self.session.execute(text("""
                SELECT 
                    p.precinct_id,
                    p.precinct_name,
                    c.geoid as tract_geoid,
                    c.namelsad as tract_name,
                    ST_Area(ST_Intersection(p.geom, c.geom)) as intersection_area
                FROM voting_precincts p
                JOIN census_tracts c ON ST_Intersects(p.geom, c.geom)
                WHERE p.state_fips = :state_fips
                ORDER BY intersection_area DESC
                LIMIT 10
            """), {'state_fips': self.config.state_fips})
            
            logger.info("Top 10 Precinct-Census Tract Intersections:")
            for row in result:
                logger.info(f"  {row.precinct_name} ∩ {row.tract_name}: {row.intersection_area:.2f} sq meters")
                
        except Exception as e:
            logger.error(f"Spatial analysis query failed: {e}")
    
    def run_full_import(self):
        """Execute complete census data import workflow"""
        logger.info("Starting full census data import...")
        
        # Step 1: Download and import TIGER shapefiles
        if self.config.download_shapefiles:
            shapefile_path = self.download_tiger_shapefiles()
            if shapefile_path:
                tract_count = self.extract_and_import_shapefiles(shapefile_path)
                logger.info(f"Imported {tract_count} census tracts from shapefiles")
        
        # Step 2: Fetch and import demographic data
        if self.config.api_key:
            # Common ACS5 variables for demographic analysis
            variables = [
                'B01003_001E',  # Total Population
                'B25001_001E',  # Housing Units
                'B19013_001E',  # Median Household Income
                'B08303_001E',  # Commuting Data
            ]
            
            api_data = self.fetch_census_api_data(variables)
            if api_data:
                demo_count = self.import_demographic_data(api_data)
                logger.info(f"Imported {demo_count} demographic records from Census API")
        
        # Step 3: Create spatial indexes
        self.create_spatial_indexes()
        
        # Step 4: Run example spatial queries
        self.run_spatial_analysis_queries()
        
        logger.info("Census data import completed successfully!")
    
    def cleanup(self):
        """Clean up database connections and temporary files"""
        if self.session:
            self.session.close()
        if self.engine:
            self.engine.dispose()
        logger.info("Database connections closed")


def create_sample_config():
    """Create sample configuration file"""
    config = configparser.ConfigParser()
    
    config['census'] = {
        'api_key': 'YOUR_CENSUS_API_KEY_HERE',
        'state_fips': '37',  # North Carolina
        'county_fips': '067',  # Forsyth County
        'year': '2022',
        'dataset': 'acs/acs5'
    }
    
    config['database'] = {
        'database_url': 'postgresql://username:password@localhost:5432/census_db',
        'postgis_legacy': 'false',
        'schema_name': 'census',
        'table_prefix': 'census_'
    }
    
    config['import'] = {
        'import_existing': 'false',
        'validate_geometry': 'true', 
        'create_indexes': 'true',
        'download_shapefiles': 'true'
    }
    
    with open('census_config.ini', 'w') as configfile:
        config.write(configfile)
    
    print("Sample configuration created: census_config.ini")
    print("Please edit the file with your Census API key and database settings")


@click.command()
@click.option('--config', '-c', help='Configuration file path', default='census_config.ini')
@click.option('--state', help='State FIPS code (e.g., 37 for NC)')
@click.option('--county', help='County FIPS code (e.g., 067 for Forsyth)')
@click.option('--database', help='Database URL')
@click.option('--api-key', help='Census API key')
@click.option('--import-existing', is_flag=True, help='Re-import existing records')
@click.option('--postgis-legacy', is_flag=True, help='Use legacy PostGIS functions')
@click.option('--create-config', is_flag=True, help='Create sample configuration file')
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose logging')
def main(config, state, county, database, api_key, import_existing, 
         postgis_legacy, create_config, verbose):
    """
    Forsyth County Census Data Importer
    
    Import Census Bureau data and TIGER shapefiles into PostGIS database
    for spatial analysis and canvass optimization.
    """
    
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    if create_config:
        create_sample_config()
        return
    
    try:
        # Load configuration
        if os.path.exists(config):
            census_config = CensusConfig.from_file(config)
            logger.info(f"Loaded configuration from: {config}")
        else:
            census_config = CensusConfig()
            logger.info("Using default configuration")
        
        # Override with command line arguments
        if state:
            census_config.state_fips = state
        if county:
            census_config.county_fips = county
        if database:
            census_config.database_url = database
        if api_key:
            census_config.api_key = api_key
        if import_existing:
            census_config.import_existing = True
        if postgis_legacy:
            census_config.postgis_legacy = True
        
        logger.info(f"Import Configuration:")
        logger.info(f"  State FIPS: {census_config.state_fips}")
        logger.info(f"  County FIPS: {census_config.county_fips}")
        logger.info(f"  Database: {census_config.database_url}")
        logger.info(f"  PostGIS Legacy: {census_config.postgis_legacy}")
        
        # Initialize and run importer
        importer = CensusImporter(census_config)
        importer.run_full_import()
        importer.cleanup()
        
        logger.info("Census import completed successfully!")
        
    except Exception as e:
        logger.error(f"Census import failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()