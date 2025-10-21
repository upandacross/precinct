import pandas as pd
import json
from models import db
from sqlalchemy import text

class ClusteringService:
    """Service class for handling clustering data and insights."""
    
    def __init__(self):
        self.precinct_data = None
        self.census_data = None
        
    def load_precinct_clustering_data(self):
        """Load precinct clustering results from CSV."""
        try:
            self.precinct_data = pd.read_csv('precinct_clustering_results.csv')
            return True
        except FileNotFoundError:
            return False
    
    def load_census_clustering_data(self):
        """Load census tract clustering results from CSV."""
        try:
            self.census_data = pd.read_csv('census_tract_clustering_results.csv')
            return True
        except FileNotFoundError:
            return False
    
    def get_user_precinct_insights(self, user):
        """Get clustering insights for user's specific precinct."""
        if not self.precinct_data is None and hasattr(self.precinct_data, 'empty'):
            if self.precinct_data.empty or not user.precinct:
                return None
        elif self.precinct_data is None or not user.precinct:
            return None
            
        user_precinct = self.precinct_data[
            (self.precinct_data['precinct'] == user.precinct) & 
            (self.precinct_data['county'] == user.county)
        ]
        
        if user_precinct.empty:
            return None
            
        precinct_info = user_precinct.iloc[0]
        
        return {
            'precinct': user.precinct,
            'county': user.county,
            'comprehensive_cluster': int(precinct_info['comprehensive_cluster']),
            'has_political_data': precinct_info['total_votes_sum'] > 0,
            'has_flippable_data': precinct_info['flippability_score'] > 0,
            'flippability_score': float(precinct_info['flippability_score']),
            'area_km2': float(precinct_info['area_km2']),
            'strategic_priority': self._determine_strategic_priority(precinct_info)
        }
    
    def _determine_strategic_priority(self, precinct_info):
        """Determine strategic priority based on cluster and data availability."""
        cluster = int(precinct_info['comprehensive_cluster'])
        has_complete_data = (precinct_info['total_votes_sum'] > 0 and 
                           precinct_info['flippability_score'] > 0)
        
        if has_complete_data and cluster in [3, 5, 6]:
            return "Tier 1 - High Priority"
        elif cluster == 1:
            return "Tier 2 - Large Segment"
        else:
            return "Tier 3 - Data Collection Target"
    
    def get_cluster_summary(self):
        """Get overall clustering summary statistics."""
        if self.precinct_data is None or self.precinct_data.empty:
            return None
            
        summary = {
            'total_precincts': len(self.precinct_data),
            'precincts_with_political_data': (self.precinct_data['total_votes_sum'] > 0).sum(),
            'precincts_with_flippable_data': (self.precinct_data['flippability_score'] > 0).sum(),
            'high_priority_precincts': len(self.precinct_data[
                self.precinct_data['comprehensive_cluster'].isin([3, 5, 6])
            ]),
            'cluster_distribution': self.precinct_data['comprehensive_cluster'].value_counts().to_dict()
        }
        
        return summary
    
    def get_county_insights(self, county_name):
        """Get clustering insights for specific county."""
        if self.precinct_data is None or self.precinct_data.empty:
            return None
            
        county_data = self.precinct_data[self.precinct_data['county'] == county_name]
        
        if county_data.empty:
            return None
            
        return {
            'total_precincts': len(county_data),
            'avg_flippability_score': county_data['flippability_score'].mean(),
            'cluster_distribution': county_data['comprehensive_cluster'].value_counts().to_dict(),
            'priority_precincts': len(county_data[
                county_data['comprehensive_cluster'].isin([3, 5, 6])
            ])
        }
    
    def get_chart_data(self):
        """Get data formatted for charts and visualizations."""
        if self.precinct_data is None or self.precinct_data.empty:
            return None
            
        data = {
            'cluster_distribution': self.precinct_data['comprehensive_cluster'].value_counts().sort_index().to_dict(),
            'flippability_by_cluster': self.precinct_data.groupby('comprehensive_cluster')['flippability_score'].mean().round(2).to_dict(),
            'data_availability': {
                'total': len(self.precinct_data),
                'with_political': int((self.precinct_data['total_votes_sum'] > 0).sum()),
                'with_flippable': int((self.precinct_data['flippability_score'] > 0).sum()),
                'complete_data': int(((self.precinct_data['total_votes_sum'] > 0) & 
                                    (self.precinct_data['flippability_score'] > 0)).sum())
            }
        }
        
        return data