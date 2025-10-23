#!/usr/bin/env python3
"""
Database Helpers with Precinct Normalization
=============================================

This module provides database helper functions that automatically handle
precinct ID normalization for common query patterns.

Usage:
    from db_helpers import get_flippable_races_for_user, get_precinct_voting_data
    
    # Get user's flippable races (handles precinct format automatically)
    races = get_flippable_races_for_user(db_engine, user)
    
    # Get voting data for precinct (tries both padded/unpadded formats)
    voting_data = get_precinct_voting_data(db_engine, county, precinct)
"""

import pandas as pd
from sqlalchemy import text
from precinct_utils import normalize_precinct_id
from typing import Optional, List, Dict, Any

def get_flippable_races_for_user(engine, user, limit: int = 100) -> pd.DataFrame:
    """
    Get flippable races for a user, handling precinct format inconsistencies.
    
    Args:
        engine: SQLAlchemy database engine
        user: User object with county, precinct attributes
        limit: Maximum number of races to return
        
    Returns:
        DataFrame with flippable race data
    """
    if not user or not user.county or not user.precinct:
        return pd.DataFrame()
    
    # Get normalized precinct formats
    padded_precinct, unpadded_precinct = normalize_precinct_id(user.precinct)
    if not padded_precinct:
        return pd.DataFrame()
    
    query = text('''
        SELECT county, precinct, contest_name, election_date,
               dem_votes, oppo_votes, gov_votes, dem_margin, dva_pct_needed
        FROM flippable 
        WHERE UPPER(county) = UPPER(:county) 
        AND (precinct = :precinct_padded OR precinct = :precinct_unpadded)
        ORDER BY dem_margin DESC
        LIMIT :limit
    ''')
    
    return pd.read_sql(query, engine, params={
        'county': user.county,
        'precinct_padded': padded_precinct,
        'precinct_unpadded': unpadded_precinct,
        'limit': limit
    })

def get_precinct_voting_data(engine, county: str, precinct: str, election_year: Optional[str] = None) -> pd.DataFrame:
    """
    Get voting data for a specific precinct, handling format inconsistencies.
    
    Args:
        engine: SQLAlchemy database engine
        county: County name
        precinct: Precinct ID (any format)
        election_year: Optional year filter
        
    Returns:
        DataFrame with candidate vote results
    """
    padded_precinct, unpadded_precinct = normalize_precinct_id(precinct)
    if not padded_precinct:
        return pd.DataFrame()
    
    # Build query with optional year filter
    year_filter = ""
    params = {
        'county': county,
        'precinct_padded': padded_precinct,
        'precinct_unpadded': unpadded_precinct
    }
    
    if election_year:
        year_filter = "AND EXTRACT(YEAR FROM election_date) = :election_year"
        params['election_year'] = election_year
    
    query = text(f'''
        SELECT county, precinct, contest_name, election_date,
               candidate_name, choice_party, total_votes
        FROM candidate_vote_results 
        WHERE UPPER(county) = UPPER(:county) 
        AND (precinct = :precinct_padded OR precinct = :precinct_unpadded)
        {year_filter}
        ORDER BY election_date DESC, contest_name, total_votes DESC
    ''')
    
    return pd.read_sql(query, engine, params=params)

def get_precincts_missing_data(engine, data_type: str = 'voting') -> pd.DataFrame:
    """
    Find precincts that exist spatially but are missing specific data types.
    
    Args:
        engine: SQLAlchemy database engine
        data_type: Type of data to check ('voting', 'flippable', 'both')
        
    Returns:
        DataFrame with precincts missing the specified data
    """
    if data_type == 'voting':
        query = text('''
            WITH spatial_precincts AS (
                SELECT DISTINCT county, precinct, precinct_name
                FROM precincts
                WHERE precinct IS NOT NULL
            ),
            voting_precincts AS (
                SELECT DISTINCT county, precinct
                FROM candidate_vote_results
                WHERE precinct IS NOT NULL
            )
            SELECT sp.county, sp.precinct, sp.precinct_name,
                   'missing_voting_data' as issue_type
            FROM spatial_precincts sp
            LEFT JOIN voting_precincts vp 
                ON sp.county = vp.county 
                AND (sp.precinct = vp.precinct OR 
                     LPAD(LTRIM(sp.precinct, '0'), 3, '0') = LPAD(LTRIM(vp.precinct, '0'), 3, '0'))
            WHERE vp.precinct IS NULL
            ORDER BY sp.county, sp.precinct
        ''')
    elif data_type == 'flippable':
        query = text('''
            WITH spatial_precincts AS (
                SELECT DISTINCT county, precinct, precinct_name
                FROM precincts
                WHERE precinct IS NOT NULL
            ),
            flippable_precincts AS (
                SELECT DISTINCT county, precinct
                FROM flippable
                WHERE precinct IS NOT NULL
            )
            SELECT sp.county, sp.precinct, sp.precinct_name,
                   'missing_flippable_data' as issue_type
            FROM spatial_precincts sp
            LEFT JOIN flippable_precincts fp 
                ON sp.county = fp.county 
                AND (sp.precinct = fp.precinct OR 
                     LPAD(LTRIM(sp.precinct, '0'), 3, '0') = LPAD(LTRIM(fp.precinct, '0'), 3, '0'))
            WHERE fp.precinct IS NULL
            ORDER BY sp.county, sp.precinct
        ''')
    else:  # both
        query = text('''
            WITH spatial_precincts AS (
                SELECT DISTINCT county, precinct, precinct_name
                FROM precincts
                WHERE precinct IS NOT NULL
            ),
            voting_precincts AS (
                SELECT DISTINCT county, precinct
                FROM candidate_vote_results
                WHERE precinct IS NOT NULL
            ),
            flippable_precincts AS (
                SELECT DISTINCT county, precinct
                FROM flippable
                WHERE precinct IS NOT NULL
            )
            SELECT sp.county, sp.precinct, sp.precinct_name,
                   CASE 
                       WHEN vp.precinct IS NULL AND fp.precinct IS NULL 
                       THEN 'missing_both'
                       WHEN vp.precinct IS NULL 
                       THEN 'missing_voting_data'
                       WHEN fp.precinct IS NULL 
                       THEN 'missing_flippable_data'
                   END as issue_type
            FROM spatial_precincts sp
            LEFT JOIN voting_precincts vp 
                ON sp.county = vp.county 
                AND (sp.precinct = vp.precinct OR 
                     LPAD(LTRIM(sp.precinct, '0'), 3, '0') = LPAD(LTRIM(vp.precinct, '0'), 3, '0'))
            LEFT JOIN flippable_precincts fp 
                ON sp.county = fp.county 
                AND (sp.precinct = fp.precinct OR 
                     LPAD(LTRIM(sp.precinct, '0'), 3, '0') = LPAD(LTRIM(fp.precinct, '0'), 3, '0'))
            WHERE vp.precinct IS NULL OR fp.precinct IS NULL
            ORDER BY sp.county, sp.precinct
        ''')
    
    return pd.read_sql(query, engine)

def create_precinct_lookup_table(engine) -> pd.DataFrame:
    """
    Create a comprehensive precinct lookup table for the application.
    
    Args:
        engine: SQLAlchemy database engine
        
    Returns:
        DataFrame with normalized precinct mappings
    """
    query = text('''
        WITH all_precincts AS (
            -- Spatial precincts
            SELECT 'spatial' as source, county, precinct, precinct_name
            FROM precincts
            WHERE precinct IS NOT NULL
            
            UNION ALL
            
            -- Voting precincts  
            SELECT 'voting' as source, county, precinct, NULL as precinct_name
            FROM (SELECT DISTINCT county, precinct FROM candidate_vote_results) v
            WHERE precinct IS NOT NULL
            
            UNION ALL
            
            -- Flippable precincts
            SELECT 'flippable' as source, county, precinct, NULL as precinct_name
            FROM (SELECT DISTINCT county, precinct FROM flippable) f
            WHERE precinct IS NOT NULL
        ),
        precinct_summary AS (
            SELECT 
                county,
                precinct as original_precinct,
                MAX(precinct_name) as precinct_name,
                LPAD(LTRIM(precinct, '0'), 3, '0') as precinct_padded,
                LTRIM(precinct, '0') as precinct_unpadded,
                STRING_AGG(DISTINCT source, ', ' ORDER BY source) as data_sources,
                COUNT(DISTINCT source) as source_count
            FROM all_precincts
            GROUP BY county, precinct
        )
        SELECT 
            county,
            original_precinct,
            precinct_name,
            precinct_padded,
            precinct_unpadded,
            data_sources,
            source_count,
            CASE 
                WHEN source_count = 3 THEN 'complete'
                WHEN data_sources LIKE '%spatial%' AND data_sources LIKE '%voting%' THEN 'good'
                WHEN data_sources LIKE '%spatial%' THEN 'spatial_only'
                ELSE 'incomplete'
            END as completeness_status
        FROM precinct_summary
        ORDER BY county, precinct_padded
    ''')
    
    return pd.read_sql(query, engine)

def get_precinct_data_summary(engine) -> Dict[str, Any]:
    """
    Get a summary of precinct data completeness across all tables.
    
    Args:
        engine: SQLAlchemy database engine
        
    Returns:
        Dictionary with summary statistics
    """
    lookup = create_precinct_lookup_table(engine)
    
    summary = {
        'total_precincts': len(lookup),
        'by_completeness': lookup['completeness_status'].value_counts().to_dict(),
        'by_county': lookup['county'].value_counts().to_dict(),
        'source_distribution': lookup['data_sources'].value_counts().to_dict(),
        'avg_sources_per_precinct': lookup['source_count'].mean(),
        'precincts_with_all_data': len(lookup[lookup['source_count'] == 3]),
        'precincts_missing_voting': len(lookup[~lookup['data_sources'].str.contains('voting')]),
        'precincts_missing_flippable': len(lookup[~lookup['data_sources'].str.contains('flippable')])
    }
    
    return summary

def test_precinct_74_data(engine) -> Dict[str, Any]:
    """
    Specific test function for precinct 74/074 data availability.
    
    Args:
        engine: SQLAlchemy database engine
        
    Returns:
        Dictionary with precinct 74 data status
    """
    # Check all formats of precinct 74
    formats = ['74', '074', '4']
    results = {}
    
    for fmt in formats:
        padded, unpadded = normalize_precinct_id(fmt)
        
        # Check each table
        for table in ['precincts', 'candidate_vote_results', 'flippable']:
            query = text(f'SELECT COUNT(*) as count FROM {table} WHERE precinct = :precinct')
            count = pd.read_sql(query, engine, params={'precinct': fmt}).iloc[0]['count']
            
            if fmt not in results:
                results[fmt] = {}
            results[fmt][table] = count
    
    # Get normalized summary
    voting_data = get_precinct_voting_data(engine, 'FORSYTH', '74')
    flippable_data = get_flippable_races_for_user(engine, type('User', (), {
        'county': 'FORSYTH', 'precinct': '74'
    })())
    
    return {
        'format_breakdown': results,
        'normalized_results': {
            'voting_records': len(voting_data),
            'flippable_records': len(flippable_data),
            'precinct_exists_spatially': any(
                results[fmt]['precincts'] > 0 for fmt in formats
            )
        },
        'padded_unpadded': normalize_precinct_id('74')
    }

if __name__ == "__main__":
    # Test the helper functions
    from dotenv import load_dotenv
    from sqlalchemy import create_engine
    import os
    
    load_dotenv()
    
    db_url = (
        f'postgresql://{os.getenv("POSTGRES_USER")}:'
        f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
        f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
    )
    engine = create_engine(db_url)
    
    print("🧪 Testing database helpers...")
    
    # Test precinct 74 specifically
    p74_results = test_precinct_74_data(engine)
    print(f"\n📊 Precinct 74 Test Results:")
    print(f"Format breakdown: {p74_results['format_breakdown']}")
    print(f"Normalized results: {p74_results['normalized_results']}")
    
    # Get data completeness summary
    summary = get_precinct_data_summary(engine)
    print(f"\n📈 Data Completeness Summary:")
    print(f"Total precincts: {summary['total_precincts']}")
    print(f"Completeness distribution: {summary['by_completeness']}")
    print(f"Precincts missing voting data: {summary['precincts_missing_voting']}")
    print(f"Precincts missing flippable data: {summary['precincts_missing_flippable']}")