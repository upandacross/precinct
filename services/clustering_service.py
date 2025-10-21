import pandas as pd
import json
from models import db
from sqlalchemy import text

class ClusteringService:
    """Service class for handling clustering data and insights."""
    
    def __init__(self):
        self.precinct_data = None
        self.census_data = None
        
    def load_precinct_clustering_data(self, county_filter=None):
        """Load precinct clustering results from CSV, optionally filtered by county."""
        try:
            self.precinct_data = pd.read_csv('precinct_clustering_results.csv')
            
            # Apply county filter if specified
            if county_filter:
                self.precinct_data = self.precinct_data[self.precinct_data['county'] == county_filter]
                
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
        
        # Handle data type conversion - precinct might be string in user but int in data
        try:
            user_precinct_int = int(user.precinct)
        except (ValueError, TypeError):
            user_precinct_int = user.precinct
        
        # Try matching with both string and int versions
        user_precinct = self.precinct_data[
            ((self.precinct_data['precinct'] == user.precinct) | 
             (self.precinct_data['precinct'] == user_precinct_int)) & 
            (self.precinct_data['county'].str.upper() == str(user.county).upper())
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
            'dem_vote_pct': float(precinct_info['dem_pct']),  # Vote share, not race wins
            'dem_race_win_pct': self._calculate_race_win_percentage(user),  # Actual race wins
            'rep_pct': float(precinct_info['rep_pct']),
            'area_km2': float(precinct_info['area_km2']),
            'strategic_priority': self._determine_strategic_priority(precinct_info),
            'election_date_range': self._get_election_date_range()
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
    
    def get_cluster_summary(self, user_cluster=None):
        """Get clustering summary statistics, optionally focused on user's cluster."""
        if self.precinct_data is None or self.precinct_data.empty:
            return None
        
        if user_cluster is not None:
            # User-specific cluster analysis
            return self.get_user_cluster_summary(user_cluster)
        else:
            # Overall summary (admin view or fallback)
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
    
    def get_user_cluster_summary(self, user_cluster):
        """Get detailed analysis of the user's specific cluster."""
        if self.precinct_data is None or self.precinct_data.empty:
            return None
            
        # Get data for user's cluster
        cluster_data = self.precinct_data[
            self.precinct_data['comprehensive_cluster'] == user_cluster
        ]
        
        if cluster_data.empty:
            return None
        
        # Calculate cluster-specific statistics
        cluster_stats = {
            'user_cluster': user_cluster,
            'cluster_size': len(cluster_data),
            'total_precincts_in_dataset': len(self.precinct_data),
            'cluster_percentage': round((len(cluster_data) / len(self.precinct_data)) * 100, 1),
            
            # Data availability in this cluster
            'precincts_with_political_data': int((cluster_data['total_votes_sum'] > 0).sum()),
            'precincts_with_flippable_data': int((cluster_data['flippability_score'] > 0).sum()),
            'complete_data_precincts': int(((cluster_data['total_votes_sum'] > 0) & 
                                          (cluster_data['flippability_score'] > 0)).sum()),
            
            # Cluster characteristics
            'avg_area': round(cluster_data['area_km2'].mean(), 2),
            'avg_flippability_score': round(cluster_data['flippability_score'].mean(), 2),
            'flippability_range': {
                'min': round(cluster_data['flippability_score'].min(), 2),
                'max': round(cluster_data['flippability_score'].max(), 2)
            },
            
            # Priority assessment
            'is_high_priority': user_cluster in [3, 5, 6],
            'strategic_focus': self._get_cluster_strategic_focus(user_cluster, cluster_data),
            
            # Peer precincts (others in same cluster)
            'peer_precincts': len(cluster_data) - 1  # Exclude the user's own precinct
        }
        
        return cluster_stats
    
    def _get_cluster_strategic_focus(self, cluster_id, cluster_data):
        """Determine the strategic focus for a specific cluster."""
        complete_data_ratio = ((cluster_data['total_votes_sum'] > 0) & 
                              (cluster_data['flippability_score'] > 0)).sum() / len(cluster_data)
        avg_flippability = cluster_data['flippability_score'].mean()
        
        if cluster_id in [3, 5, 6] and complete_data_ratio > 0.5:
            return "High-impact organizing target"
        elif cluster_id == 1:
            return "Large-scale voter outreach opportunity"
        elif avg_flippability > 100:
            return "Competitive races - focus on GOTV"
        elif complete_data_ratio < 0.3:
            return "Data collection and research needed"
        else:
            return "Medium-priority organizing target"
    
    def _get_election_date_range(self):
        """Get the range of election dates from the database."""
        try:
            result = db.session.execute(text("""
                SELECT MIN(election_date) as earliest, MAX(election_date) as latest
                FROM candidate_vote_results
            """)).fetchone()
            
            if result and result[0] and result[1]:
                earliest = result[0].strftime('%Y')
                latest = result[1].strftime('%Y')
                if earliest == latest:
                    return f"Elections from {earliest}"
                else:
                    return f"Elections from {earliest}-{latest}"
            else:
                return "All elections"
        except Exception:
            return "All elections"
    
    def _calculate_race_win_percentage(self, user):
        """Calculate the percentage of races won by Democrats in this precinct."""
        try:
            result = db.session.execute(text("""
                WITH race_totals AS (
                    SELECT 
                        contest_name, election_date,
                        SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) as dem_votes,
                        SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) as rep_votes
                    FROM candidate_vote_results 
                    WHERE precinct = :precinct AND county = :county 
                      AND choice_party IN ('DEM', 'REP')
                    GROUP BY contest_name, election_date
                    HAVING SUM(CASE WHEN choice_party = 'DEM' THEN total_votes ELSE 0 END) > 0 
                       AND SUM(CASE WHEN choice_party = 'REP' THEN total_votes ELSE 0 END) > 0
                )
                SELECT 
                    COUNT(*) as total_races,
                    SUM(CASE WHEN dem_votes > rep_votes THEN 1 ELSE 0 END) as dem_wins
                FROM race_totals
            """), {'precinct': str(user.precinct), 'county': str(user.county).upper()}).fetchone()
            
            if result and result[0] and result[0] > 0:
                total_races = result[0]
                dem_wins = result[1]
                return (dem_wins / total_races) * 100
            else:
                return 0.0
        except Exception:
            return 0.0
    
    def get_county_insights(self, county_name):
        """Get clustering insights for specific county."""
        if self.precinct_data is None or self.precinct_data.empty:
            return None
        
        # Case-insensitive county matching
        county_data = self.precinct_data[
            self.precinct_data['county'].str.upper() == str(county_name).upper()
        ]
        
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