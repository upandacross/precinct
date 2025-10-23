#!/usr/bin/env python3
"""
Precinct Clustering Analysis
============================

This module provides comprehensive clustering analysis for precinct data including:
1. Spatial clustering (geographic patterns)
2. Political clustering (voting patterns)
3. Performance clustering (flippability analysis)
4. Multi-dimensional clustering combining multiple features

Usage:
    uv run python clustering_analysis.py

Data Sources:
- precincts: Spatial data (area, perimeter, geometry)
- candidate_vote_results: Political voting data 
- flippable: Flippability scores and margins
- voter_record: Voter demographics and registration
"""

import os
import pandas as pd
import numpy as np
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score, calinski_harabasz_score
import matplotlib.pyplot as plt
import seaborn as sns
from flask import Flask
from models import db
from dotenv import load_dotenv
from sqlalchemy import text
from precinct_utils import normalize_precinct_id, normalize_precinct_join
import warnings
warnings.filterwarnings('ignore')

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class PrecinctClusteringAnalysis:
    """Main clustering analysis class for precinct data."""
    
    def __init__(self):
        """Initialize the clustering analysis with database connection."""
        load_dotenv()
        self.app = Flask(__name__)
        self.app.config['SQLALCHEMY_DATABASE_URI'] = (
            f'postgresql://{os.getenv("POSTGRES_USER")}:'
            f'{os.getenv("POSTGRES_PASSWORD")}@'
            f'{os.getenv("POSTGRES_HOST")}:'
            f'{os.getenv("POSTGRES_PORT")}/'
            f'{os.getenv("POSTGRES_DB")}'
        )
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        with self.app.app_context():
            db.init_app(self.app)
            self.load_data()
    
    def load_data(self):
        """Load all relevant data for clustering analysis."""
        print("📊 Loading precinct data for clustering analysis...")
        
        # 1. Spatial data from precincts table
        self.spatial_data = pd.read_sql(text("""
            SELECT 
                precinct,
                county,
                st_areashape as area,
                st_perimetershape as perimeter,
                ST_X(ST_Centroid(geometry)) as longitude,
                ST_Y(ST_Centroid(geometry)) as latitude
            FROM precincts 
            WHERE st_areashape IS NOT NULL 
                AND geometry IS NOT NULL
            ORDER BY county, precinct
        """), db.session.connection())
        
        # 2. Political data from candidate_vote_results
        self.political_data = pd.read_sql(text("""
            SELECT 
                county,
                precinct,
                contest_name,
                candidate_name,
                choice_party,
                total_votes,
                election_date
            FROM candidate_vote_results
            WHERE total_votes IS NOT NULL
            ORDER BY county, precinct, contest_name
        """), db.session.connection())
        
        # 3. Flippability data
        self.flippable_data = pd.read_sql(text("""
            SELECT 
                county,
                precinct,
                contest_name,
                dem_votes,
                oppo_votes,
                dem_margin,
                dva_pct_needed
            FROM flippable
            WHERE dem_votes IS NOT NULL 
                AND oppo_votes IS NOT NULL
            ORDER BY county, precinct
        """), db.session.connection())
        
        print(f"✅ Loaded data:")
        print(f"   - Spatial: {len(self.spatial_data)} precincts")
        print(f"   - Political: {len(self.political_data)} vote records")
        print(f"   - Flippable: {len(self.flippable_data)} flippable contests")
    
    def prepare_spatial_features(self):
        """Prepare spatial features for clustering."""
        print("\n🗺️  Preparing spatial clustering features...")
        
        spatial_features = self.spatial_data.copy()
        
        # Calculate derived spatial metrics
        spatial_features['area_km2'] = spatial_features['area'] / 1_000_000  # Convert to km²
        spatial_features['perimeter_km'] = spatial_features['perimeter'] / 1_000  # Convert to km
        spatial_features['shape_complexity'] = spatial_features['perimeter'] / (2 * np.sqrt(np.pi * spatial_features['area_km2']))
        spatial_features['aspect_ratio'] = spatial_features['perimeter_km'] / spatial_features['area_km2']
        
        # Select features for clustering
        feature_cols = ['area_km2', 'perimeter_km', 'shape_complexity', 'longitude', 'latitude']
        self.spatial_features = spatial_features[['precinct', 'county'] + feature_cols].copy()
        
        print(f"✅ Spatial features prepared: {feature_cols}")
        return self.spatial_features
    
    def prepare_political_features(self):
        """Prepare political features for clustering."""
        print("\n🗳️  Preparing political clustering features...")
        
        # Aggregate political data by precinct
        political_agg = self.political_data.groupby(['county', 'precinct']).agg({
            'total_votes': ['sum', 'mean', 'count'],
            'choice_party': lambda x: x.value_counts().to_dict()
        }).reset_index()
        
        # Flatten column names
        political_agg.columns = ['county', 'precinct', 'total_votes_sum', 'avg_votes_per_contest', 'num_contests', 'party_breakdown']
        
        # Extract party vote percentages
        def extract_party_pcts(party_dict):
            total = sum(party_dict.values()) if party_dict else 1
            return {
                'dem_pct': party_dict.get('DEM', 0) / total * 100,
                'rep_pct': party_dict.get('REP', 0) / total * 100,
                'other_pct': sum(v for k, v in party_dict.items() if k not in ['DEM', 'REP']) / total * 100
            }
        
        party_data = political_agg['party_breakdown'].apply(extract_party_pcts).apply(pd.Series)
        political_features = pd.concat([political_agg[['county', 'precinct', 'total_votes_sum', 'avg_votes_per_contest', 'num_contests']], party_data], axis=1)
        
        self.political_features = political_features.fillna(0)
        
        print(f"✅ Political features prepared for {len(self.political_features)} precincts")
        return self.political_features
    
    def prepare_flippability_features(self):
        """Prepare flippability features for clustering with normalized precinct handling."""
        print("\n🎯 Preparing flippability clustering features...")
        
        # Add normalized precinct columns to flippable data
        flippable_normalized = self.flippable_data.copy()
        precinct_norm = flippable_normalized['precinct'].apply(normalize_precinct_id)
        flippable_normalized[['precinct_padded', 'precinct_unpadded']] = pd.DataFrame(
            precinct_norm.tolist(), index=flippable_normalized.index
        )
        
        # Use unpadded precinct for consistent grouping (matches most voting data)
        flippable_for_agg = flippable_normalized.dropna(subset=['precinct_unpadded']).copy()
        
        # Aggregate flippability data by normalized precinct
        flippable_agg = flippable_for_agg.groupby(['county', 'precinct_unpadded']).agg({
            'dem_votes': 'sum',
            'oppo_votes': 'sum', 
            'dem_margin': 'mean',
            'dva_pct_needed': 'mean'
        }).reset_index()
        
        # Rename back to precinct for consistency
        flippable_agg = flippable_agg.rename(columns={'precinct_unpadded': 'precinct'})
        
        # Calculate additional flippability metrics
        flippable_agg['total_votes'] = flippable_agg['dem_votes'] + flippable_agg['oppo_votes']
        
        # Handle division by zero for dem_vote_pct
        mask = flippable_agg['total_votes'] > 0
        flippable_agg['dem_vote_pct'] = 0.0
        flippable_agg.loc[mask, 'dem_vote_pct'] = (
            flippable_agg.loc[mask, 'dem_votes'] / flippable_agg.loc[mask, 'total_votes']
        ) * 100
        
        flippable_agg['competitiveness'] = 100 - abs(flippable_agg['dem_vote_pct'] - 50)  # How close to 50/50
        flippable_agg['flippability_score'] = (flippable_agg['competitiveness'] * flippable_agg['total_votes']) / 1000  # Weighted by turnout
        
        self.flippability_features = flippable_agg.fillna(0)
        
        print(f"✅ Flippability features prepared for {len(self.flippability_features)} precincts")
        print(f"   - Original flippable records: {len(self.flippable_data)}")
        print(f"   - Precincts with valid data: {len(flippable_for_agg)}")
        print(f"   - Aggregated to: {len(flippable_agg)} unique county/precinct combinations")
        
        return self.flippability_features
    
    def perform_spatial_clustering(self, n_clusters=5):
        """Perform spatial clustering analysis."""
        print(f"\n🗺️  Performing spatial clustering (k={n_clusters})...")
        
        spatial_data = self.prepare_spatial_features()
        feature_cols = ['area_km2', 'perimeter_km', 'shape_complexity', 'longitude', 'latitude']
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(spatial_data[feature_cols])
        
        # K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        spatial_data['spatial_cluster'] = kmeans.fit_predict(X_scaled)
        
        # Calculate clustering metrics
        silhouette = silhouette_score(X_scaled, spatial_data['spatial_cluster'])
        calinski = calinski_harabasz_score(X_scaled, spatial_data['spatial_cluster'])
        
        print(f"✅ Spatial clustering completed:")
        print(f"   - Silhouette Score: {silhouette:.3f}")
        print(f"   - Calinski-Harabasz Score: {calinski:.1f}")
        
        # Analyze clusters
        cluster_summary = spatial_data.groupby('spatial_cluster').agg({
            'area_km2': ['mean', 'std'],
            'perimeter_km': ['mean', 'std'],
            'shape_complexity': ['mean', 'std'],
            'precinct': 'count'
        }).round(2)
        
        print("\n📊 Spatial Cluster Summary:")
        print(cluster_summary)
        
        self.spatial_results = {
            'data': spatial_data,
            'scaler': scaler,
            'model': kmeans,
            'metrics': {'silhouette': silhouette, 'calinski': calinski},
            'summary': cluster_summary
        }
        
        return self.spatial_results
    
    def perform_political_clustering(self, n_clusters=4):
        """Perform political clustering analysis."""
        print(f"\n🗳️  Performing political clustering (k={n_clusters})...")
        
        political_data = self.prepare_political_features()
        feature_cols = ['total_votes_sum', 'avg_votes_per_contest', 'dem_pct', 'rep_pct', 'other_pct']
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(political_data[feature_cols])
        
        # K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        political_data['political_cluster'] = kmeans.fit_predict(X_scaled)
        
        # Calculate clustering metrics
        silhouette = silhouette_score(X_scaled, political_data['political_cluster'])
        calinski = calinski_harabasz_score(X_scaled, political_data['political_cluster'])
        
        print(f"✅ Political clustering completed:")
        print(f"   - Silhouette Score: {silhouette:.3f}")
        print(f"   - Calinski-Harabasz Score: {calinski:.1f}")
        
        # Analyze clusters
        cluster_summary = political_data.groupby('political_cluster').agg({
            'dem_pct': ['mean', 'std'],
            'rep_pct': ['mean', 'std'],
            'total_votes_sum': ['mean', 'std'],
            'precinct': 'count'
        }).round(2)
        
        print("\n📊 Political Cluster Summary:")
        print(cluster_summary)
        
        self.political_results = {
            'data': political_data,
            'scaler': scaler,
            'model': kmeans,
            'metrics': {'silhouette': silhouette, 'calinski': calinski},
            'summary': cluster_summary
        }
        
        return self.political_results
    
    def perform_flippability_clustering(self, n_clusters=3):
        """Perform flippability clustering analysis."""
        print(f"\n🎯 Performing flippability clustering (k={n_clusters})...")
        
        flippable_data = self.prepare_flippability_features()
        feature_cols = ['dem_vote_pct', 'competitiveness', 'flippability_score', 'total_votes', 'dva_pct_needed']
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(flippable_data[feature_cols])
        
        # K-Means clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        flippable_data['flippability_cluster'] = kmeans.fit_predict(X_scaled)
        
        # Calculate clustering metrics
        silhouette = silhouette_score(X_scaled, flippable_data['flippability_cluster'])
        calinski = calinski_harabasz_score(X_scaled, flippable_data['flippability_cluster'])
        
        print(f"✅ Flippability clustering completed:")
        print(f"   - Silhouette Score: {silhouette:.3f}")
        print(f"   - Calinski-Harabasz Score: {calinski:.1f}")
        
        # Analyze clusters
        cluster_summary = flippable_data.groupby('flippability_cluster').agg({
            'dem_vote_pct': ['mean', 'std'],
            'competitiveness': ['mean', 'std'],
            'flippability_score': ['mean', 'std'],
            'dva_pct_needed': ['mean', 'std'],
            'precinct': 'count'
        }).round(2)
        
        print("\n📊 Flippability Cluster Summary:")
        print(cluster_summary)
        
        self.flippability_results = {
            'data': flippable_data,
            'scaler': scaler,
            'model': kmeans,
            'metrics': {'silhouette': silhouette, 'calinski': calinski},
            'summary': cluster_summary
        }
        
        return self.flippability_results
    
    def find_optimal_clusters(self, data_type='spatial', max_k=10):
        """Find optimal number of clusters using elbow method and silhouette analysis."""
        print(f"\n🔍 Finding optimal clusters for {data_type} data...")
        
        # Prepare data based on type
        if data_type == 'spatial':
            data = self.prepare_spatial_features()
            feature_cols = ['area_km2', 'perimeter_km', 'shape_complexity', 'longitude', 'latitude']
        elif data_type == 'political':
            data = self.prepare_political_features()
            feature_cols = ['total_votes_sum', 'avg_votes_per_contest', 'dem_pct', 'rep_pct', 'other_pct']
        elif data_type == 'flippability':
            data = self.prepare_flippability_features()
            feature_cols = ['dem_vote_pct', 'competitiveness', 'flippability_score', 'total_votes', 'dva_pct_needed']
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(data[feature_cols])
        
        # Calculate metrics for different k values
        k_range = range(2, max_k + 1)
        inertias = []
        silhouette_scores = []
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_scaled)
            
            inertias.append(kmeans.inertia_)
            silhouette_scores.append(silhouette_score(X_scaled, cluster_labels))
        
        # Find optimal k using silhouette score
        optimal_k = k_range[np.argmax(silhouette_scores)]
        
        print(f"✅ Optimal number of clusters: {optimal_k}")
        print(f"   - Best silhouette score: {max(silhouette_scores):.3f}")
        
        return {
            'optimal_k': optimal_k,
            'k_range': list(k_range),
            'inertias': inertias,
            'silhouette_scores': silhouette_scores
        }
    
    def create_comprehensive_clusters(self):
        """Create comprehensive clusters combining all features."""
        print("\n🎯 Creating comprehensive multi-dimensional clusters...")
        
        # Merge all feature sets
        spatial = self.prepare_spatial_features()
        political = self.prepare_political_features()
        flippable = self.prepare_flippability_features()
        
        # Use normalize_precinct_join for robust precinct matching
        print("\n🔗 Merging datasets with normalized precinct matching...")
        
        # First merge spatial with political data
        comprehensive = normalize_precinct_join(
            spatial, political, 
            county_col='county', precinct_col='precinct', 
            how='left', suffixes=('', '_political')
        )
        
        # Then merge with flippable data
        comprehensive = normalize_precinct_join(
            comprehensive, flippable,
            county_col='county', precinct_col='precinct',
            how='left', suffixes=('', '_flippable')
        )
        
        # Fill missing values for precincts without political/flippable data
        comprehensive = comprehensive.fillna({
            'total_votes_sum': 0,
            'avg_votes_per_contest': 0,
            'num_contests': 0,
            'dem_pct': 0,
            'rep_pct': 0,
            'other_pct': 0,
            'dem_votes': 0,
            'oppo_votes': 0,
            'dem_margin': 0,
            'dva_pct_needed': 0,
            'total_votes': 0,
            'dem_vote_pct': 0,
            'competitiveness': 0,
            'flippability_score': 0
        })
        
        print(f"📊 Comprehensive dataset: {len(comprehensive)} precincts with all features")
        
        # Count precincts by data availability
        has_political = (comprehensive['total_votes_sum'] > 0).sum()
        has_flippable = (comprehensive['flippability_score'] > 0).sum()
        has_both = ((comprehensive['total_votes_sum'] > 0) & (comprehensive['flippability_score'] > 0)).sum()
        
        print(f"   - With spatial data: {len(comprehensive)} (all precincts)")
        print(f"   - With political data: {has_political}")
        print(f"   - With flippable data: {has_flippable}")
        print(f"   - With complete data: {has_both}")
        
        # Select key features from each category
        feature_cols = [
            # Spatial
            'area_km2', 'shape_complexity', 'longitude', 'latitude',
            # Political  
            'dem_pct', 'rep_pct', 'total_votes_sum',
            # Flippability
            'competitiveness', 'flippability_score', 'dva_pct_needed'
        ]
        
        # Standardize features
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(comprehensive[feature_cols])
        
        # Apply PCA for dimensionality reduction
        pca = PCA(n_components=0.95)  # Keep 95% of variance
        X_pca = pca.fit_transform(X_scaled)
        
        print(f"📉 PCA reduced dimensions: {X_scaled.shape[1]} → {X_pca.shape[1]}")
        print(f"   - Explained variance: {pca.explained_variance_ratio_.sum():.3f}")
        
        # Find optimal clusters
        optimal_analysis = self.find_optimal_clusters_pca(X_pca)
        optimal_k = optimal_analysis['optimal_k']
        
        # Perform final clustering
        kmeans = KMeans(n_clusters=optimal_k, random_state=42, n_init=10)
        comprehensive['comprehensive_cluster'] = kmeans.fit_predict(X_pca)
        
        # Analyze comprehensive clusters
        cluster_summary = comprehensive.groupby('comprehensive_cluster').agg({
            'area_km2': 'mean',
            'dem_pct': 'mean',
            'rep_pct': 'mean',
            'competitiveness': 'mean',
            'flippability_score': 'mean',
            'precinct': 'count'
        }).round(2)
        
        print(f"\n🎯 Comprehensive Clustering Results (k={optimal_k}):")
        print(cluster_summary)
        
        self.comprehensive_results = {
            'data': comprehensive,
            'scaler': scaler,
            'pca': pca,
            'model': kmeans,
            'optimal_analysis': optimal_analysis,
            'summary': cluster_summary
        }
        
        return self.comprehensive_results
    
    def find_optimal_clusters_pca(self, X_pca, max_k=8):
        """Find optimal clusters for PCA-transformed data."""
        k_range = range(2, max_k + 1)
        silhouette_scores = []
        
        for k in k_range:
            kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
            cluster_labels = kmeans.fit_predict(X_pca)
            silhouette_scores.append(silhouette_score(X_pca, cluster_labels))
        
        optimal_k = k_range[np.argmax(silhouette_scores)]
        
        return {
            'optimal_k': optimal_k,
            'k_range': list(k_range),
            'silhouette_scores': silhouette_scores
        }
    
    def generate_insights(self):
        """Generate actionable insights from clustering analysis."""
        print("\n💡 CLUSTERING INSIGHTS & RECOMMENDATIONS")
        print("=" * 60)
        
        insights = []
        
        # Spatial insights
        if hasattr(self, 'spatial_results'):
            spatial_data = self.spatial_results['data']
            largest_cluster = spatial_data['spatial_cluster'].value_counts().index[0]
            cluster_areas = spatial_data.groupby('spatial_cluster')['area_km2'].mean()
            
            insights.append(f"🗺️  SPATIAL: Cluster {largest_cluster} is the largest spatial group with {spatial_data['spatial_cluster'].value_counts().iloc[0]} precincts")
            insights.append(f"   - Average area ranges from {cluster_areas.min():.1f} to {cluster_areas.max():.1f} km²")
        
        # Political insights
        if hasattr(self, 'political_results'):
            political_data = self.political_results['data']
            dem_strongholds = political_data[political_data['dem_pct'] > 60]
            rep_strongholds = political_data[political_data['rep_pct'] > 60]
            
            insights.append(f"🗳️  POLITICAL: Found {len(dem_strongholds)} Democratic strongholds (>60% Dem)")
            insights.append(f"   - Found {len(rep_strongholds)} Republican strongholds (>60% Rep)")
            
            if len(political_data) > 0:
                competitive = political_data[(political_data['dem_pct'] >= 40) & (political_data['dem_pct'] <= 60)]
                insights.append(f"   - {len(competitive)} competitive precincts (40-60% Dem)")
        
        # Flippability insights
        if hasattr(self, 'flippability_results'):
            flippable_data = self.flippability_results['data']
            high_flip = flippable_data[flippable_data['flippability_score'] > flippable_data['flippability_score'].quantile(0.8)]
            
            insights.append(f"🎯 FLIPPABILITY: {len(high_flip)} high-opportunity precincts identified")
            
            if len(high_flip) > 0:
                target_precincts = high_flip.nsmallest(5, 'dva_pct_needed')[['precinct', 'dva_pct_needed', 'competitiveness']]
                insights.append(f"   - Top targets need {target_precincts['dva_pct_needed'].mean():.1f}% vote shift")
        
        # Comprehensive insights
        if hasattr(self, 'comprehensive_results'):
            comp_data = self.comprehensive_results['data']
            cluster_sizes = comp_data['comprehensive_cluster'].value_counts()
            
            insights.append(f"🎯 COMPREHENSIVE: {len(cluster_sizes)} distinct precinct types identified")
            insights.append(f"   - Largest segment: {cluster_sizes.iloc[0]} precincts")
            insights.append(f"   - Most balanced cluster sizes: {cluster_sizes.std():.1f} standard deviation")
        
        for insight in insights:
            print(insight)
        
        return insights
    
    def export_results(self, filename='precinct_clustering_results.csv'):
        """Export clustering results to CSV for further analysis."""
        print(f"\n💾 Exporting results to {filename}...")
        
        if hasattr(self, 'comprehensive_results'):
            data = self.comprehensive_results['data']
            data.to_csv(filename, index=False)
            print(f"✅ Exported {len(data)} precincts with comprehensive clustering")
        else:
            print("❌ No comprehensive results to export. Run create_comprehensive_clusters() first.")
        
        return filename


def main():
    """Main execution function."""
    print("🎯 PRECINCT CLUSTERING ANALYSIS")
    print("=" * 50)
    print("Analyzing North Carolina precinct data for strategic insights")
    print()
    
    # Initialize analysis
    analyzer = PrecinctClusteringAnalysis()
    
    # Perform individual clustering analyses
    analyzer.perform_spatial_clustering(n_clusters=5)
    analyzer.perform_political_clustering(n_clusters=4)
    analyzer.perform_flippability_clustering(n_clusters=3)
    
    # Create comprehensive multi-dimensional clustering
    analyzer.create_comprehensive_clusters()
    
    # Generate insights
    analyzer.generate_insights()
    
    # Export results
    analyzer.export_results()
    
    print("\n✅ Clustering analysis complete!")
    print("\nNext steps:")
    print("- Review precinct_clustering_results.csv for detailed data")
    print("- Use clusters to prioritize organizing efforts")
    print("- Focus on high-flippability precincts")
    print("- Consider spatial clusters for efficient canvassing routes")


if __name__ == "__main__":
    main()