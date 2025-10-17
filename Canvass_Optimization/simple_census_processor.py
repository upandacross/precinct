#!/usr/bin/env python3
"""
Simple Census Data Processor
============================

A lightweight alternative to the full SQLAlchemy importer for basic
census data processing without external database dependencies.

Features:
- CSV/JSON output formats
- Direct Census API integration
- Precinct-demographic mapping
- No database installation required
- Standalone operation

Usage:
    python simple_census_processor.py --help
    python simple_census_processor.py --state NC --county 067 --output csv
    python simple_census_processor.py --api-key YOUR_KEY --format json --output-file forsyth_demographics.json
"""

import os
import sys
import json
import csv
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CensusVariable:
    """Census variable definition with metadata"""
    code: str
    label: str
    concept: str
    data_type: str = "estimate"
    
    def __post_init__(self):
        # Determine if this is estimate or margin of error
        if self.code.endswith('M'):
            self.data_type = "margin_of_error"
        elif self.code.endswith('E'):
            self.data_type = "estimate"


@dataclass 
class GeographicUnit:
    """Geographic unit (census tract, precinct, etc.)"""
    geoid: str
    name: str
    geography_type: str
    state_fips: str
    county_fips: str
    tract_fips: Optional[str] = None
    
    def full_name(self) -> str:
        return f"{self.name} ({self.geography_type} {self.geoid})"


class SimpleCensusAPI:
    """Simplified Census API client with no external dependencies"""
    
    BASE_URL = "https://api.census.gov/data"
    TIGER_URL = "https://www2.census.gov/geo/tiger"
    
    # Common ACS5 variables for canvass optimization analysis
    CANVASS_VARIABLES = {
        # Population and Housing
        'B01003_001E': CensusVariable('B01003_001E', 'Total Population', 'Total Population'),
        'B25001_001E': CensusVariable('B25001_001E', 'Total Housing Units', 'Housing Units'),
        'B25003_002E': CensusVariable('B25003_002E', 'Owner-Occupied Housing Units', 'Housing Tenure'),
        'B25003_003E': CensusVariable('B25003_003E', 'Renter-Occupied Housing Units', 'Housing Tenure'),
        
        # Demographics
        'B19013_001E': CensusVariable('B19013_001E', 'Median Household Income', 'Household Income'),
        'B25077_001E': CensusVariable('B25077_001E', 'Median Home Value', 'Home Value'),
        'B08303_001E': CensusVariable('B08303_001E', 'Total Commuters', 'Commuting to Work'),
        'B15003_022E': CensusVariable('B15003_022E', "Bachelor's Degree", 'Educational Attainment'),
        
        # Age Groups (useful for voter turnout modeling)
        'B01001_007E': CensusVariable('B01001_007E', 'Male 18-19 years', 'Sex by Age'),
        'B01001_008E': CensusVariable('B01001_008E', 'Male 20-24 years', 'Sex by Age'),
        'B01001_009E': CensusVariable('B01001_009E', 'Male 25-29 years', 'Sex by Age'),
        'B01001_031E': CensusVariable('B01001_031E', 'Female 18-19 years', 'Sex by Age'),
        'B01001_032E': CensusVariable('B01001_032E', 'Female 20-24 years', 'Sex by Age'),
        'B01001_033E': CensusVariable('B01001_033E', 'Female 25-29 years', 'Sex by Age'),
    }
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.session_info = {
            'requests_made': 0,
            'last_request_time': None,
            'errors': []
        }
    
    def build_url(self, year: str, dataset: str, variables: List[str], 
                  geography: str, state: str, county: str = None) -> str:
        """Build Census API URL with proper encoding"""
        base = f"{self.BASE_URL}/{year}/{dataset}"
        
        params = {
            'get': ','.join(variables + ['NAME']),
            'for': geography,
        }
        
        # Add geographic filters
        if county:
            params['in'] = f"state:{state} county:{county}"
        else:
            params['in'] = f"state:{state}"
            
        if self.api_key:
            params['key'] = self.api_key
        
        # Manually encode URL to handle special characters
        query_string = urllib.parse.urlencode(params)
        return f"{base}?{query_string}"
    
    def make_request(self, url: str, timeout: int = 30) -> Optional[Dict[str, Any]]:
        """Make HTTP request with error handling"""
        self.session_info['requests_made'] += 1
        self.session_info['last_request_time'] = datetime.now()
        
        logger.info(f"Census API Request #{self.session_info['requests_made']}: {url}")
        
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                if response.status == 200:
                    content = response.read().decode('utf-8')
                    return json.loads(content)
                else:
                    logger.error(f"API request failed with status: {response.status}")
                    return None
                    
        except urllib.error.HTTPError as e:
            error_msg = f"HTTP Error {e.code}: {e.reason}"
            logger.error(error_msg)
            self.session_info['errors'].append(error_msg)
            return None
            
        except urllib.error.URLError as e:
            error_msg = f"URL Error: {e.reason}"
            logger.error(error_msg)
            self.session_info['errors'].append(error_msg)
            return None
            
        except json.JSONDecodeError as e:
            error_msg = f"JSON Decode Error: {e.msg}"
            logger.error(error_msg)
            self.session_info['errors'].append(error_msg)
            return None
            
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(error_msg)
            self.session_info['errors'].append(error_msg)
            return None
    
    def get_tract_data(self, year: str, state_fips: str, county_fips: str, 
                       variables: List[str] = None) -> Dict[str, Any]:
        """Fetch census tract data for a specific county"""
        if variables is None:
            variables = list(self.CANVASS_VARIABLES.keys())
        
        url = self.build_url(
            year=year,
            dataset="acs/acs5",
            variables=variables,
            geography="tract:*",
            state=state_fips,
            county=county_fips
        )
        
        data = self.make_request(url)
        
        if not data:
            return {'success': False, 'error': 'API request failed'}
        
        # Process response
        headers = data[0]
        rows = data[1:]
        
        processed_data = []
        for row in rows:
            row_dict = dict(zip(headers, row))
            
            # Build standardized tract record
            tract_record = {
                'geoid': f"{row_dict.get('state', '')}{row_dict.get('county', '')}{row_dict.get('tract', '')}",
                'name': row_dict.get('NAME', ''),
                'state_fips': row_dict.get('state', ''),
                'county_fips': row_dict.get('county', ''),
                'tract_fips': row_dict.get('tract', ''),
                'variables': {},
                'metadata': {
                    'source': 'US Census Bureau ACS5',
                    'year': year,
                    'dataset': 'acs/acs5',
                    'retrieved_at': datetime.now().isoformat()
                }
            }
            
            # Add variable data
            for var_code in variables:
                if var_code in row_dict:
                    value = row_dict[var_code]
                    
                    # Handle Census null values
                    if value in ['-888888888', '-666666666', '-555555555', None, '']:
                        value = None
                    else:
                        try:
                            value = float(value) if '.' in str(value) else int(value)
                        except (ValueError, TypeError):
                            value = None
                    
                    variable_info = self.CANVASS_VARIABLES.get(var_code, 
                        CensusVariable(var_code, var_code, 'Unknown'))
                    
                    tract_record['variables'][var_code] = {
                        'value': value,
                        'label': variable_info.label,
                        'concept': variable_info.concept,
                        'data_type': variable_info.data_type
                    }
            
            processed_data.append(tract_record)
        
        return {
            'success': True,
            'data': processed_data,
            'summary': {
                'total_tracts': len(processed_data),
                'variables_requested': len(variables),
                'state_fips': state_fips,
                'county_fips': county_fips,
                'api_requests_made': self.session_info['requests_made']
            }
        }
    
    def get_variable_metadata(self, year: str, dataset: str = "acs/acs5") -> Dict[str, Any]:
        """Fetch variable definitions and metadata"""
        url = f"{self.BASE_URL}/{year}/{dataset}/variables.json"
        
        logger.info(f"Fetching variable metadata: {url}")
        data = self.make_request(url)
        
        if not data:
            return {'success': False, 'error': 'Failed to fetch variable metadata'}
        
        variables = data.get('variables', {})
        
        # Filter to variables we care about
        canvass_vars = {}
        for var_code in self.CANVASS_VARIABLES.keys():
            if var_code in variables:
                canvass_vars[var_code] = variables[var_code]
        
        return {
            'success': True,
            'variables': canvass_vars,
            'total_variables_available': len(variables),
            'canvass_variables_found': len(canvass_vars)
        }


class CensusDataProcessor:
    """Process and export census data in various formats"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api = SimpleCensusAPI(api_key)
        self.data_cache = {}
    
    def fetch_county_demographics(self, state_fips: str, county_fips: str, 
                                  year: str = "2022") -> Dict[str, Any]:
        """Fetch complete demographic data for a county"""
        cache_key = f"{state_fips}_{county_fips}_{year}"
        
        if cache_key in self.data_cache:
            logger.info(f"Using cached data for {cache_key}")
            return self.data_cache[cache_key]
        
        logger.info(f"Fetching demographics for State {state_fips}, County {county_fips}")
        
        result = self.api.get_tract_data(year, state_fips, county_fips)
        
        if result['success']:
            self.data_cache[cache_key] = result
            logger.info(f"Successfully fetched {result['summary']['total_tracts']} tract records")
        else:
            logger.error(f"Failed to fetch demographics: {result.get('error', 'Unknown error')}")
        
        return result
    
    def calculate_summary_statistics(self, tract_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate county-level summary statistics"""
        summary = {
            'total_tracts': len(tract_data),
            'population': {'total': 0, 'tracts_with_data': 0},
            'housing': {'total_units': 0, 'owner_occupied': 0, 'renter_occupied': 0},
            'income': {'values': [], 'median': None},
            'education': {'bachelors_degree': 0},
            'young_adults': {'count': 0}  # 18-29 age group
        }
        
        for tract in tract_data:
            variables = tract.get('variables', {})
            
            # Population
            pop_var = variables.get('B01003_001E', {})
            if pop_var.get('value') is not None:
                summary['population']['total'] += pop_var['value']
                summary['population']['tracts_with_data'] += 1
            
            # Housing
            total_units = variables.get('B25001_001E', {}).get('value', 0) or 0
            owner_occupied = variables.get('B25003_002E', {}).get('value', 0) or 0
            renter_occupied = variables.get('B25003_003E', {}).get('value', 0) or 0
            
            summary['housing']['total_units'] += total_units
            summary['housing']['owner_occupied'] += owner_occupied
            summary['housing']['renter_occupied'] += renter_occupied
            
            # Income
            income_var = variables.get('B19013_001E', {})
            if income_var.get('value') is not None:
                summary['income']['values'].append(income_var['value'])
            
            # Education
            bachelors_var = variables.get('B15003_022E', {})
            if bachelors_var.get('value') is not None:
                summary['education']['bachelors_degree'] += bachelors_var['value']
            
            # Young Adults (18-29) - sum multiple age group variables
            young_adult_vars = ['B01001_007E', 'B01001_008E', 'B01001_009E', 
                                'B01001_031E', 'B01001_032E', 'B01001_033E']
            for var_code in young_adult_vars:
                var_data = variables.get(var_code, {})
                if var_data.get('value') is not None:
                    summary['young_adults']['count'] += var_data['value']
        
        # Calculate derived statistics
        if summary['income']['values']:
            sorted_incomes = sorted(summary['income']['values'])
            n = len(sorted_incomes)
            if n % 2 == 0:
                summary['income']['median'] = (sorted_incomes[n//2-1] + sorted_incomes[n//2]) / 2
            else:
                summary['income']['median'] = sorted_incomes[n//2]
        
        # Calculate percentages
        total_occupied = summary['housing']['owner_occupied'] + summary['housing']['renter_occupied']
        if total_occupied > 0:
            summary['housing']['owner_occupied_pct'] = (summary['housing']['owner_occupied'] / total_occupied) * 100
            summary['housing']['renter_occupied_pct'] = (summary['housing']['renter_occupied'] / total_occupied) * 100
        
        return summary
    
    def export_to_csv(self, tract_data: List[Dict[str, Any]], output_file: str):
        """Export tract data to CSV format"""
        logger.info(f"Exporting {len(tract_data)} tracts to CSV: {output_file}")
        
        if not tract_data:
            logger.warning("No data to export")
            return
        
        # Determine all unique variable codes
        all_variables = set()
        for tract in tract_data:
            all_variables.update(tract.get('variables', {}).keys())
        
        fieldnames = [
            'geoid', 'name', 'state_fips', 'county_fips', 'tract_fips'
        ]
        
        # Add variable columns
        for var_code in sorted(all_variables):
            variable_info = SimpleCensusAPI.CANVASS_VARIABLES.get(var_code,
                CensusVariable(var_code, var_code, 'Unknown'))
            fieldnames.extend([
                f"{var_code}_value",
                f"{var_code}_label"
            ])
        
        with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for tract in tract_data:
                row = {
                    'geoid': tract.get('geoid', ''),
                    'name': tract.get('name', ''),
                    'state_fips': tract.get('state_fips', ''),
                    'county_fips': tract.get('county_fips', ''),
                    'tract_fips': tract.get('tract_fips', '')
                }
                
                # Add variable data
                for var_code in sorted(all_variables):
                    var_data = tract.get('variables', {}).get(var_code, {})
                    row[f"{var_code}_value"] = var_data.get('value', '')
                    row[f"{var_code}_label"] = var_data.get('label', '')
                
                writer.writerow(row)
        
        logger.info(f"CSV export completed: {output_file}")
    
    def export_to_json(self, result_data: Dict[str, Any], output_file: str):
        """Export full result data to JSON format"""
        logger.info(f"Exporting data to JSON: {output_file}")
        
        # Add processing metadata
        export_data = {
            'export_metadata': {
                'exported_at': datetime.now().isoformat(),
                'processor_version': '1.0.0',
                'format': 'simple_census_json_v1'
            },
            'census_data': result_data
        }
        
        with open(output_file, 'w', encoding='utf-8') as jsonfile:
            json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
        
        logger.info(f"JSON export completed: {output_file}")
    
    def create_canvass_summary_report(self, tract_data: List[Dict[str, Any]], 
                                      output_file: str):
        """Create a human-readable canvass optimization report"""
        summary = self.calculate_summary_statistics(tract_data)
        
        report_content = f"""
FORSYTH COUNTY CANVASS OPTIMIZATION REPORT
==========================================
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Data Source: US Census Bureau ACS 5-Year Estimates

SUMMARY STATISTICS
------------------
Total Census Tracts: {summary['total_tracts']}
Total Population: {summary['population']['total']:,}
Tracts with Population Data: {summary['population']['tracts_with_data']}

HOUSING ANALYSIS
----------------
Total Housing Units: {summary['housing']['total_units']:,}
Owner-Occupied Units: {summary['housing']['owner_occupied']:,} ({summary['housing'].get('owner_occupied_pct', 0):.1f}%)
Renter-Occupied Units: {summary['housing']['renter_occupied']:,} ({summary['housing'].get('renter_occupied_pct', 0):.1f}%)

DEMOGRAPHIC INSIGHTS
--------------------
Median Household Income: ${summary['income']['median']:,} (estimated)
Adults with Bachelor's Degree: {summary['education']['bachelors_degree']:,}
Young Adults (18-29): {summary['young_adults']['count']:,}

CANVASS RECOMMENDATIONS
-----------------------
1. High-Density Areas: Focus on census tracts with >1000 housing units
2. Renter-Heavy Areas: Prioritize tracts with >60% rental occupancy 
3. Young Adult Concentrations: Target areas with high 18-29 population
4. Income Diversity: Balance outreach across income levels

TRACT-LEVEL DATA
----------------
"""
        
        # Add top 10 tracts by population
        tract_pop = [(t.get('geoid', ''), t.get('name', ''), 
                      t.get('variables', {}).get('B01003_001E', {}).get('value', 0) or 0)
                     for t in tract_data]
        tract_pop.sort(key=lambda x: x[2], reverse=True)
        
        report_content += "\nTop 10 Tracts by Population:\n"
        for i, (geoid, name, pop) in enumerate(tract_pop[:10], 1):
            report_content += f"{i:2d}. {name:<50} Pop: {pop:>6,}\n"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Canvass report created: {output_file}")


def main():
    """Main CLI interface"""
    parser = argparse.ArgumentParser(
        description="Simple Census Data Processor for Canvass Optimization",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python simple_census_processor.py --state 37 --county 067 --format csv
  python simple_census_processor.py --api-key YOUR_KEY --format json --output forsyth_data.json
  python simple_census_processor.py --state 37 --county 067 --format report
        """
    )
    
    parser.add_argument('--state', default='37', 
                       help='State FIPS code (default: 37 for North Carolina)')
    parser.add_argument('--county', default='067',
                       help='County FIPS code (default: 067 for Forsyth County)')
    parser.add_argument('--year', default='2022',
                       help='Census data year (default: 2022)')
    parser.add_argument('--api-key', 
                       help='Census API key (optional but recommended)')
    parser.add_argument('--format', choices=['csv', 'json', 'report'], default='csv',
                       help='Output format (default: csv)')
    parser.add_argument('--output', '--output-file',
                       help='Output file path (auto-generated if not specified)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize processor
    processor = CensusDataProcessor(args.api_key)
    
    # Fetch data
    logger.info(f"Processing census data for State {args.state}, County {args.county}")
    result = processor.fetch_county_demographics(args.state, args.county, args.year)
    
    if not result['success']:
        logger.error("Failed to fetch census data")
        sys.exit(1)
    
    # Generate output filename if not provided
    if not args.output:
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        county_name = f"state{args.state}_county{args.county}"
        
        if args.format == 'csv':
            args.output = f"census_data_{county_name}_{timestamp}.csv"
        elif args.format == 'json':
            args.output = f"census_data_{county_name}_{timestamp}.json"
        elif args.format == 'report':
            args.output = f"canvass_report_{county_name}_{timestamp}.txt"
    
    # Export data
    if args.format == 'csv':
        processor.export_to_csv(result['data'], args.output)
    elif args.format == 'json':
        processor.export_to_json(result, args.output)
    elif args.format == 'report':
        processor.create_canvass_summary_report(result['data'], args.output)
    
    # Print summary
    print(f"\n✅ Processing Complete!")
    print(f"📊 Processed {result['summary']['total_tracts']} census tracts")
    print(f"📁 Output saved to: {args.output}")
    print(f"🌐 API requests made: {processor.api.session_info['requests_made']}")
    
    if processor.api.session_info['errors']:
        print(f"⚠️  Errors encountered: {len(processor.api.session_info['errors'])}")


if __name__ == "__main__":
    main()