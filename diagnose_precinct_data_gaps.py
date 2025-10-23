#!/usr/bin/env python3
"""
Precinct Data Completeness Diagnostic
=====================================

This script identifies precincts that exist geographically but lack voting data,
which causes zeros in the clustering analysis for political metrics.

Usage:
    python diagnose_precinct_data_gaps.py
"""

import os
import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

def main():
    """Main diagnostic function."""
    load_dotenv()
    
    # Create database connection
    db_url = (
        f'postgresql://{os.getenv("POSTGRES_USER")}:'
        f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
        f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
    )
    engine = create_engine(db_url)
    
    print("🔍 PRECINCT DATA COMPLETENESS DIAGNOSTIC")
    print("=" * 50)
    
    # Get all precincts
    all_precincts = pd.read_sql(text("""
        SELECT precinct, county, precinct_name
        FROM precincts
        ORDER BY county, precinct
    """), engine)
    
    # Get precincts with candidate vote data
    precincts_with_votes = pd.read_sql(text("""
        SELECT DISTINCT precinct, county
        FROM candidate_vote_results
        ORDER BY county, precinct
    """), engine)
    
    # Get precincts with flippable data
    precincts_with_flippable = pd.read_sql(text("""
        SELECT DISTINCT precinct, county
        FROM flippable
        ORDER BY county, precinct
    """), engine)
    
    print(f"📊 **Summary:**")
    print(f"   - Total precincts: {len(all_precincts)}")
    print(f"   - Precincts with vote data: {len(precincts_with_votes)}")
    print(f"   - Precincts with flippable data: {len(precincts_with_flippable)}")
    
    # Find precincts missing vote data
    missing_votes = all_precincts[
        ~all_precincts['precinct'].isin(precincts_with_votes['precinct'])
    ].copy()
    
    # Find precincts missing flippable data
    missing_flippable = all_precincts[
        ~all_precincts['precinct'].isin(precincts_with_flippable['precinct'])
    ].copy()
    
    print(f"\n❌ **Data Gaps:**")
    print(f"   - Precincts missing vote data: {len(missing_votes)}")
    print(f"   - Precincts missing flippable data: {len(missing_flippable)}")
    
    if len(missing_votes) > 0:
        print(f"\n🚨 **Precincts with NO candidate vote data:**")
        for _, row in missing_votes.iterrows():
            print(f"   - {row['county']} P{row['precinct']}: {row['precinct_name']}")
    
    if len(missing_flippable) > 0:
        print(f"\n⚠️  **Precincts with NO flippable data:**")
        # Show only first 20 to avoid overwhelming output
        show_count = min(20, len(missing_flippable))
        for _, row in missing_flippable.head(show_count).iterrows():
            print(f"   - {row['county']} P{row['precinct']}: {row['precinct_name']}")
        
        if len(missing_flippable) > 20:
            print(f"   ... and {len(missing_flippable) - 20} more")
    
    # Check specific precinct 074
    p074_info = all_precincts[all_precincts['precinct'] == '074']
    if len(p074_info) > 0:
        p074 = p074_info.iloc[0]
        has_votes = '074' in precincts_with_votes['precinct'].values
        has_flippable = '074' in precincts_with_flippable['precinct'].values
        
        print(f"\n🎯 **Precinct 074 Specific Analysis:**")
        print(f"   - Name: {p074['precinct_name']}")
        print(f"   - County: {p074['county']}")
        print(f"   - Has vote data: {'✅ Yes' if has_votes else '❌ No'}")
        print(f"   - Has flippable data: {'✅ Yes' if has_flippable else '❌ No'}")
        print(f"   - **Root cause**: Missing {', '.join([s for s in ['vote data', 'flippable data'] if not (has_votes if s == 'vote data' else has_flippable)])}")
    
    print(f"\n💡 **Recommendations:**")
    if len(missing_votes) > 0:
        print(f"   1. Investigate why {len(missing_votes)} precincts have no candidate vote results")
        print(f"   2. Check if these precincts had no contests, or if data import failed")
    
    if len(missing_flippable) > 0:
        print(f"   3. {len(missing_flippable)} precincts lack flippable race data")
        print(f"   4. This could be normal if they had no competitive races")
    
    print(f"   5. Consider excluding precincts with no voting data from clustering analysis")
    print(f"   6. Or implement fallback values for political metrics when voting data is missing")
    
    print(f"\n✅ Diagnostic complete!")

if __name__ == "__main__":
    main()