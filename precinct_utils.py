#!/usr/bin/env python3
"""
Precinct ID Utilities
=====================

This module provides utilities for handling precinct ID formatting inconsistencies
across different data sources (NC Board of Elections, Census Bureau, etc.).

Usage:
    from precinct_utils import normalize_precinct_join, create_precinct_lookup
    
    # For pandas DataFrames
    df_merged = normalize_precinct_join(spatial_df, voting_df, 'county', 'precinct')
    
    # For SQL queries  
    lookup_table = create_precinct_lookup(engine)
"""

import pandas as pd
import numpy as np
from sqlalchemy import text
from typing import Tuple, Optional, Dict, Any

def normalize_precinct_id(precinct_value: Any) -> Tuple[Optional[str], Optional[str]]:
    """
    Normalize a precinct ID to handle zero-padding inconsistencies.
    
    Args:
        precinct_value: Precinct ID in any format (str, int, float, None)
        
    Returns:
        Tuple of (padded_3digit, unpadded) versions, or (None, None) if invalid
        
    Examples:
        normalize_precinct_id("074") -> ("074", "74")
        normalize_precinct_id("74") -> ("074", "74") 
        normalize_precinct_id(74) -> ("074", "74")
        normalize_precinct_id("4") -> ("004", "4")
        normalize_precinct_id(None) -> (None, None)
    """
    if pd.isna(precinct_value) or precinct_value is None:
        return None, None
    
    # Convert to string and clean
    precinct_str = str(precinct_value).strip()
    
    if not precinct_str or precinct_str.lower() in ['nan', 'none', '']:
        return None, None
    
    # Remove any non-numeric characters and leading zeros
    try:
        # Extract just the numeric part
        numeric_part = ''.join(c for c in precinct_str if c.isdigit())
        if not numeric_part:
            return None, None
            
        # Remove leading zeros but keep at least one digit
        unpadded = numeric_part.lstrip('0') or '0'
        
        # Create 3-digit padded version
        padded = unpadded.zfill(3)
        
        return padded, unpadded
        
    except (ValueError, TypeError):
        return None, None

def create_precinct_lookup(engine) -> pd.DataFrame:
    """
    Create a comprehensive precinct lookup table from the database.
    
    Args:
        engine: SQLAlchemy engine connected to the database
        
    Returns:
        DataFrame with columns: county, precinct_padded, precinct_unpadded, 
        has_spatial, has_voting, has_flippable, precinct_name
    """
    print("🔍 Creating comprehensive precinct lookup...")
    
    # Get all unique precincts from all tables
    lookup_query = text("""
        WITH all_precincts AS (
            -- From spatial data (precincts table)
            SELECT DISTINCT county, precinct, 'spatial' as source, precinct_name
            FROM precincts
            WHERE precinct IS NOT NULL
            
            UNION
            
            -- From voting data (candidate_vote_results) 
            SELECT DISTINCT county, precinct, 'voting' as source, NULL as precinct_name
            FROM candidate_vote_results
            WHERE precinct IS NOT NULL
            
            UNION
            
            -- From flippable data
            SELECT DISTINCT county, precinct, 'flippable' as source, NULL as precinct_name
            FROM flippable  
            WHERE precinct IS NOT NULL
        ),
        precinct_summary AS (
            SELECT 
                county,
                precinct as original_precinct,
                MAX(precinct_name) as precinct_name,
                BOOL_OR(source = 'spatial') as has_spatial,
                BOOL_OR(source = 'voting') as has_voting, 
                BOOL_OR(source = 'flippable') as has_flippable
            FROM all_precincts
            GROUP BY county, precinct
        )
        SELECT * FROM precinct_summary
        ORDER BY county, original_precinct
    """)
    
    lookup_df = pd.read_sql(lookup_query, engine)
    
    # Add normalized precinct IDs
    normalized = lookup_df['original_precinct'].apply(normalize_precinct_id)
    lookup_df[['precinct_padded', 'precinct_unpadded']] = pd.DataFrame(
        normalized.tolist(), index=lookup_df.index
    )
    
    # Remove any rows where normalization failed
    lookup_df = lookup_df.dropna(subset=['precinct_padded', 'precinct_unpadded'])
    
    print(f"✅ Created lookup for {len(lookup_df)} precincts across {lookup_df['county'].nunique()} counties")
    
    # Print summary stats
    total_precincts = len(lookup_df)
    spatial_count = lookup_df['has_spatial'].sum()
    voting_count = lookup_df['has_voting'].sum() 
    flippable_count = lookup_df['has_flippable'].sum()
    
    print(f"📊 Data completeness:")
    print(f"   - Precincts with spatial data: {spatial_count}/{total_precincts} ({spatial_count/total_precincts*100:.1f}%)")
    print(f"   - Precincts with voting data: {voting_count}/{total_precincts} ({voting_count/total_precincts*100:.1f}%)")
    print(f"   - Precincts with flippable data: {flippable_count}/{total_precincts} ({flippable_count/total_precincts*100:.1f}%)")
    
    # Identify problematic precincts (exist in spatial but missing voting data)
    missing_voting = lookup_df[lookup_df['has_spatial'] & ~lookup_df['has_voting']]
    if len(missing_voting) > 0:
        print(f"⚠️  {len(missing_voting)} precincts have spatial data but NO voting data")
        
    return lookup_df

def normalize_precinct_join(
    left_df: pd.DataFrame, 
    right_df: pd.DataFrame, 
    county_col: str = 'county',
    precinct_col: str = 'precinct',
    how: str = 'left',
    suffixes: Tuple[str, str] = ('', '_right')
) -> pd.DataFrame:
    """
    Join two DataFrames on county and precinct, handling zero-padding inconsistencies.
    
    Args:
        left_df: Left DataFrame 
        right_df: Right DataFrame
        county_col: Name of county column (assumed same in both)
        precinct_col: Name of precinct column (assumed same in both) 
        how: Join type ('left', 'right', 'inner', 'outer')
        suffixes: Suffixes for overlapping column names
        
    Returns:
        Merged DataFrame with normalized precinct matching
    """
    print(f"🔗 Performing normalized precinct join ({len(left_df)} x {len(right_df)} rows)")
    
    # Create working copies
    left_work = left_df.copy()
    right_work = right_df.copy()
    
    # Add normalized precinct IDs to both DataFrames
    left_normalized = left_work[precinct_col].apply(normalize_precinct_id)
    right_normalized = right_work[precinct_col].apply(normalize_precinct_id)
    
    left_work[['_precinct_padded', '_precinct_unpadded']] = pd.DataFrame(
        left_normalized.tolist(), index=left_work.index
    )
    right_work[['_precinct_padded', '_precinct_unpadded']] = pd.DataFrame(
        right_normalized.tolist(), index=right_work.index
    )
    
    # Try join with padded format first
    merged = left_work.merge(
        right_work, 
        left_on=[county_col, '_precinct_padded'],
        right_on=[county_col, '_precinct_padded'], 
        how=how,
        suffixes=suffixes
    )
    
    # For any unmatched rows, try unpadded format
    if how in ['left', 'outer']:
        unmatched_left = left_work[~left_work.index.isin(merged.index)]
        if len(unmatched_left) > 0:
            additional_matches = unmatched_left.merge(
                right_work,
                left_on=[county_col, '_precinct_unpadded'],
                right_on=[county_col, '_precinct_unpadded'],
                how='inner', 
                suffixes=suffixes
            )
            if len(additional_matches) > 0:
                merged = pd.concat([merged, additional_matches], ignore_index=True)
    
    # Clean up temporary columns
    cols_to_drop = [col for col in merged.columns if col.startswith('_precinct_')]
    merged = merged.drop(columns=cols_to_drop)
    
    match_rate = len(merged[merged[f'{precinct_col}{suffixes[1]}'].notna()]) / len(left_df) * 100
    print(f"✅ Join complete: {match_rate:.1f}% match rate")
    
    return merged

def create_universal_precinct_view(engine, view_name: str = 'precinct_universal') -> str:
    """
    Create a database view that provides universal precinct mapping.
    
    Args:
        engine: SQLAlchemy engine
        view_name: Name for the view to create
        
    Returns:
        SQL for the created view
    """
    view_sql = f"""
    CREATE OR REPLACE VIEW {view_name} AS
    WITH precinct_normalization AS (
        SELECT DISTINCT
            county,
            precinct as original_precinct,
            LPAD(LTRIM(precinct, '0'), 3, '0') as precinct_padded,
            LTRIM(precinct, '0') as precinct_unpadded
        FROM (
            SELECT county, precinct FROM precincts WHERE precinct IS NOT NULL
            UNION
            SELECT county, precinct FROM candidate_vote_results WHERE precinct IS NOT NULL  
            UNION
            SELECT county, precinct FROM flippable WHERE precinct IS NOT NULL
        ) all_precincts
    )
    SELECT 
        county,
        precinct_padded,
        precinct_unpadded,
        ARRAY_AGG(DISTINCT original_precinct) as original_formats
    FROM precinct_normalization
    GROUP BY county, precinct_padded, precinct_unpadded
    ORDER BY county, precinct_padded;
    """
    
    with engine.connect() as conn:
        conn.execute(text(view_sql))
        conn.commit()
    
    print(f"✅ Created database view: {view_name}")
    return view_sql

# Example usage functions for common patterns
def get_precinct_74_all_formats(engine) -> Dict[str, Any]:
    """Get precinct 74 data in all available formats for debugging."""
    result = {}
    
    # Check all possible formats
    formats_to_try = ['74', '074', '4']
    
    for fmt in formats_to_try:
        query = text(f"""
            SELECT 
                'precincts' as table_name,
                COUNT(*) as count,
                '{fmt}' as format_tried
            FROM precincts WHERE precinct = :precinct
            
            UNION ALL
            
            SELECT 
                'candidate_vote_results' as table_name,
                COUNT(*) as count,
                '{fmt}' as format_tried
            FROM candidate_vote_results WHERE precinct = :precinct
            
            UNION ALL
            
            SELECT 
                'flippable' as table_name, 
                COUNT(*) as count,
                '{fmt}' as format_tried
            FROM flippable WHERE precinct = :precinct
        """)
        
        df = pd.read_sql(query, engine, params={'precinct': fmt})
        result[fmt] = df
    
    return result

if __name__ == "__main__":
    # Demo/test the utilities
    print("🧪 Testing precinct normalization utilities...")
    
    test_cases = [
        "074", "74", "4", 74, 4.0, "004", "  74  ", None, "", "abc", "12a"
    ]
    
    for test_case in test_cases:
        padded, unpadded = normalize_precinct_id(test_case)
        print(f"   {test_case} -> ({padded}, {unpadded})")