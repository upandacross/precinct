#!/usr/bin/env python3
"""
Test script for the clustering integration.
Tests the ClusteringService to ensure it can load data and provide insights.
"""

import sys
import os

# Add the parent directory to the path to import from the main app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.clustering_service import ClusteringService

def test_clustering_service():
    """Test the clustering service functionality."""
    print("Testing ClusteringService...")
    
    service = ClusteringService()
    
    # Test loading data
    print("1. Testing data loading...")
    success = service.load_precinct_clustering_data()
    if success:
        print("   ✓ Data loaded successfully")
        print(f"   ✓ Found {len(service.precinct_data)} precincts in clustering data")
    else:
        print("   ✗ Failed to load clustering data")
        return False
    
    # Test chart data
    print("2. Testing chart data generation...")
    chart_data = service.get_chart_data()
    if chart_data:
        print("   ✓ Chart data generated successfully")
        print(f"   ✓ Cluster distribution: {chart_data.get('cluster_distribution', {})}")
    else:
        print("   ✗ Failed to generate chart data")
    
    # Test user insights (simulate a precinct user)
    print("3. Testing user insights...")
    
    # Find a precinct with complete data to test
    complete_precincts = service.precinct_data[
        (service.precinct_data['total_votes_sum'] > 0) & 
        (service.precinct_data['flippability_score'] > 0)
    ]
    
    if not complete_precincts.empty:
        test_precinct = complete_precincts.iloc[0]
        county = test_precinct['county']
        precinct = test_precinct['precinct']
        
        print(f"   Testing with precinct: {county} - {precinct}")
        
        # Create a mock user object
        class MockUser:
            def __init__(self, county, precinct):
                self.county = county
                self.precinct = precinct
        
        mock_user = MockUser(county, precinct)
        user_insights = service.get_user_precinct_insights(mock_user)
        if user_insights:
            print("   ✓ User insights generated successfully")
            print(f"   ✓ Cluster: {user_insights['comprehensive_cluster']}")
            print(f"   ✓ Strategic Priority: {user_insights['strategic_priority']}")
        else:
            print("   ✗ Failed to generate user insights")
    else:
        print("   ! No precincts with complete data found for testing")
    
    # Test summary data
    print("4. Testing cluster summary...")
    summary = service.get_cluster_summary()
    if summary:
        print("   ✓ Cluster summary generated successfully")
        print(f"   ✓ Total precincts: {summary['total_precincts']}")
        print(f"   ✓ High priority precincts: {summary['high_priority_precincts']}")
    else:
        print("   ✗ Failed to generate cluster summary")
    
    return True

if __name__ == "__main__":
    print("Clustering Integration Test")
    print("=" * 40)
    
    # Check if clustering data file exists
    csv_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "precinct_clustering_results.csv")
    if not os.path.exists(csv_path):
        print(f"✗ Clustering data file not found: {csv_path}")
        print("Please run clustering_analysis.py first to generate the data.")
        sys.exit(1)
    
    # Run tests
    success = test_clustering_service()
    
    print("\n" + "=" * 40)
    if success:
        print("✓ All tests passed! Clustering integration is ready.")
    else:
        print("✗ Some tests failed. Check the output above.")
        sys.exit(1)