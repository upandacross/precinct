#!/usr/bin/env python3
"""
Census Tract Clustering Analysis
================================

This module provides comprehensive clustering analysis for census tract demographic data including:
1. Population & Housing clustering (density, occupancy patterns)
2. Economic clustering (income, home values, employment)
3. Education clustering (degree levels, education rates)
4. Geographic clustering (spatial distribution)
5. Multi-dimensional clustering combining all demographic features

Usage:
    python3 census_tract_clustering.py

Data Source:
- census_tract: Comprehensive demographic and economic data from US Census
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
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import warnings
warnings.filterwarnings('ignore')

# Set up plotting style
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

class CensusTractClusteringAnalysis:
    """Main clustering analysis class for census tract demographic data."""
    
    def __init__(self):
        """Initialize the clustering analysis with database connection."""
        load_dotenv()
        self.db_url = (
            f'postgresql://{os.getenv("POSTGRES_USER")}:'
            f'{os.getenv("POSTGRES_PASSWORD")}@{os.getenv("POSTGRES_HOST")}:'
            f'{os.getenv("POSTGRES_PORT")}/{os.getenv("POSTGRES_DB")}'
        )
        self.engine = create_engine(self.db_url)
        
        # Data containers
        self.census_data = None
        self.population_clusters = None
        self.economic_clusters = None
        self.education_clusters = None
        self.geographic_clusters = None
        self.comprehensive_clusters = None
        
        # Scalers for different feature types
        self.scalers = {}
        
    def load_census_data(self):
        """Load census tract data from PostgreSQL database."""
        print("📊 Loading census tract data...")
        
        query = """
        SELECT 
            geoid,
            tract_id,
            full_fips,
            state,
            county,
            total_population,
            total_housing_units,
            owner_occupied,
            renter_occupied,
            median_income,
            bachelor_degree,
            master_degree,
            professional_degree,
            doctorate_degree,
            public_transport,
            work_from_home,
            median_home_value,
            median_age,
            college_educated,
            education_rate,
            occupancy_rate,
            homeowner_rate,
            remote_work_rate,
            income_category,
            area_sq_m,
            aland,
            awater,
            intptlat::float as latitude,
            intptlon::float as longitude
        FROM census_tract
        WHERE total_population > 0 
        AND total_housing_units > 0
        AND median_income > 0
        ORDER BY geoid
        """
        
        with self.engine.connect() as conn:
            self.census_data = pd.read_sql(query, conn)
        
        # Calculate additional demographic metrics
        self.census_data['population_density'] = (
            self.census_data['total_population'] / self.census_data['area_sq_m'] * 1000000  # per sq km
        )
        self.census_data['housing_density'] = (
            self.census_data['total_housing_units'] / self.census_data['area_sq_m'] * 1000000
        )
        self.census_data['advanced_degree_rate'] = (
            (self.census_data['master_degree'] + self.census_data['professional_degree'] + 
             self.census_data['doctorate_degree']) / self.census_data['total_population']
        )
        self.census_data['water_ratio'] = (
            self.census_data['awater'] / (self.census_data['aland'] + self.census_data['awater'])
        )
        
        print(f"✅ Loaded {len(self.census_data)} census tracts")
        print(f"   - States: {self.census_data['state'].nunique()}")
        print(f"   - Counties: {self.census_data['county'].nunique()}")
        print(f"   - Population range: {self.census_data['total_population'].min():,} - {self.census_data['total_population'].max():,}")
        print(f"   - Income range: ${self.census_data['median_income'].min():,} - ${self.census_data['median_income'].max():,}")
        
    def perform_population_housing_clustering(self, n_clusters=4):
        """Perform clustering based on population and housing characteristics."""
        print(f"\n🏘️  Performing population & housing clustering (k={n_clusters})...")
        
        # Select population and housing features
        features = [
            'total_population', 'total_housing_units', 'population_density', 
            'housing_density', 'occupancy_rate', 'homeowner_rate', 'water_ratio'
        ]
        
        # Prepare data
        data = self.census_data[features].copy()
        data = data.fillna(data.median())
        
        # Scale features
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data)
        self.scalers['population'] = scaler
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(scaled_data)
        
        # Calculate metrics
        silhouette = silhouette_score(scaled_data, clusters)
        calinski = calinski_harabasz_score(scaled_data, clusters)
        
        # Store results
        self.census_data['population_cluster'] = clusters
        self.population_clusters = {
            'model': kmeans,
            'features': features,
            'silhouette': silhouette,
            'calinski': calinski
        }
        
        print(f"✅ Population & housing clustering completed:")
        print(f"   - Silhouette Score: {silhouette:.3f}")
        print(f"   - Calinski-Harabasz Score: {calinski:.1f}")
        
        # Summary statistics
        summary = self.census_data.groupby('population_cluster')[features + ['geoid']].agg({
            'total_population': ['mean', 'std'],
            'population_density': ['mean', 'std'],
            'homeowner_rate': ['mean', 'std'],
            'geoid': 'count'
        }).round(2)
        summary.columns = ['_'.join(col).strip() for col in summary.columns]
        summary = summary.rename(columns={'geoid_count': 'tract_count'})
        
        print(f"\n📊 Population & Housing Cluster Summary:")
        print(summary)
        
    def perform_economic_clustering(self, n_clusters=5):
        """Perform clustering based on economic characteristics."""
        print(f"\n💰 Performing economic clustering (k={n_clusters})...")
        
        # Select economic features
        features = [
            'median_income', 'median_home_value', 'public_transport', 
            'work_from_home', 'remote_work_rate'
        ]
        
        # Prepare data
        data = self.census_data[features].copy()
        data = data.fillna(data.median())
        
        # Scale features
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data)
        self.scalers['economic'] = scaler
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(scaled_data)
        
        # Calculate metrics
        silhouette = silhouette_score(scaled_data, clusters)
        calinski = calinski_harabasz_score(scaled_data, clusters)
        
        # Store results
        self.census_data['economic_cluster'] = clusters
        self.economic_clusters = {
            'model': kmeans,
            'features': features,
            'silhouette': silhouette,
            'calinski': calinski
        }
        
        print(f"✅ Economic clustering completed:")
        print(f"   - Silhouette Score: {silhouette:.3f}")
        print(f"   - Calinski-Harabasz Score: {calinski:.1f}")
        
        # Summary statistics
        summary = self.census_data.groupby('economic_cluster')[features + ['geoid']].agg({
            'median_income': ['mean', 'std'],
            'median_home_value': ['mean', 'std'],
            'remote_work_rate': ['mean', 'std'],
            'geoid': 'count'
        }).round(2)
        summary.columns = ['_'.join(col).strip() for col in summary.columns]
        summary = summary.rename(columns={'geoid_count': 'tract_count'})
        
        print(f"\n📊 Economic Cluster Summary:")
        print(summary)
        
    def perform_education_clustering(self, n_clusters=4):
        """Perform clustering based on education characteristics."""
        print(f"\n🎓 Performing education clustering (k={n_clusters})...")
        
        # Select education features
        features = [
            'bachelor_degree', 'master_degree', 'professional_degree', 
            'doctorate_degree', 'college_educated', 'education_rate', 'advanced_degree_rate'
        ]
        
        # Prepare data
        data = self.census_data[features].copy()
        data = data.fillna(data.median())
        
        # Scale features
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data)
        self.scalers['education'] = scaler
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(scaled_data)
        
        # Calculate metrics
        silhouette = silhouette_score(scaled_data, clusters)
        calinski = calinski_harabasz_score(scaled_data, clusters)
        
        # Store results
        self.census_data['education_cluster'] = clusters
        self.education_clusters = {
            'model': kmeans,
            'features': features,
            'silhouette': silhouette,
            'calinski': calinski
        }
        
        print(f"✅ Education clustering completed:")
        print(f"   - Silhouette Score: {silhouette:.3f}")
        print(f"   - Calinski-Harabasz Score: {calinski:.1f}")
        
        # Summary statistics
        summary = self.census_data.groupby('education_cluster')[features + ['geoid']].agg({
            'education_rate': ['mean', 'std'],
            'advanced_degree_rate': ['mean', 'std'],
            'college_educated': ['mean', 'std'],
            'geoid': 'count'
        }).round(3)
        summary.columns = ['_'.join(col).strip() for col in summary.columns]
        summary = summary.rename(columns={'geoid_count': 'tract_count'})
        
        print(f"\n📊 Education Cluster Summary:")
        print(summary)
        
    def perform_geographic_clustering(self, n_clusters=6):
        """Perform clustering based on geographic characteristics."""
        print(f"\n🗺️  Performing geographic clustering (k={n_clusters})...")
        
        # Select geographic features
        features = ['latitude', 'longitude', 'area_sq_m']
        
        # Prepare data
        data = self.census_data[features].copy()
        data = data.fillna(data.median())
        
        # Scale features (use MinMaxScaler for coordinates)
        scaler = MinMaxScaler()
        scaled_data = scaler.fit_transform(data)
        self.scalers['geographic'] = scaler
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(scaled_data)
        
        # Calculate metrics
        silhouette = silhouette_score(scaled_data, clusters)
        calinski = calinski_harabasz_score(scaled_data, clusters)
        
        # Store results
        self.census_data['geographic_cluster'] = clusters
        self.geographic_clusters = {
            'model': kmeans,
            'features': features,
            'silhouette': silhouette,
            'calinski': calinski
        }
        
        print(f"✅ Geographic clustering completed:")
        print(f"   - Silhouette Score: {silhouette:.3f}")
        print(f"   - Calinski-Harabasz Score: {calinski:.1f}")
        
        # Summary statistics
        summary = self.census_data.groupby('geographic_cluster')[features + ['geoid']].agg({
            'latitude': ['mean', 'std'],
            'longitude': ['mean', 'std'],
            'area_sq_m': ['mean', 'std'],
            'geoid': 'count'
        }).round(3)
        summary.columns = ['_'.join(col).strip() for col in summary.columns]
        summary = summary.rename(columns={'geoid_count': 'tract_count'})
        
        print(f"\n📊 Geographic Cluster Summary:")
        print(summary)
        
    def create_comprehensive_clusters(self, n_clusters=5):
        """Create comprehensive multi-dimensional clustering using all features."""
        print(f"\n🎯 Creating comprehensive multi-dimensional clusters (k={n_clusters})...")
        
        # Combine all features from individual analyses
        all_features = []
        if self.population_clusters:
            all_features.extend(self.population_clusters['features'])
        if self.economic_clusters:
            all_features.extend(self.economic_clusters['features'])
        if self.education_clusters:
            all_features.extend(self.education_clusters['features'])
        if self.geographic_clusters:
            all_features.extend(self.geographic_clusters['features'])
        
        # Remove duplicates while preserving order
        features = list(dict.fromkeys(all_features))
        
        print(f"📊 Using {len(features)} features for comprehensive analysis")
        
        # Prepare data
        data = self.census_data[features].copy()
        data = data.fillna(data.median())
        
        # Scale features
        scaler = StandardScaler()
        scaled_data = scaler.fit_transform(data)
        
        # Apply PCA for dimensionality reduction
        pca = PCA(n_components=min(10, len(features)), random_state=42)
        pca_data = pca.fit_transform(scaled_data)
        
        explained_variance = pca.explained_variance_ratio_.sum()
        print(f"📉 PCA reduced dimensions: {len(features)} → {pca_data.shape[1]}")
        print(f"   - Explained variance: {explained_variance:.3f}")
        
        # Perform clustering
        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        clusters = kmeans.fit_predict(pca_data)
        
        # Calculate metrics
        silhouette = silhouette_score(pca_data, clusters)
        calinski = calinski_harabasz_score(pca_data, clusters)
        
        # Store results
        self.census_data['comprehensive_cluster'] = clusters
        self.comprehensive_clusters = {
            'model': kmeans,
            'pca': pca,
            'scaler': scaler,
            'features': features,
            'silhouette': silhouette,
            'calinski': calinski,
            'explained_variance': explained_variance
        }
        
        print(f"✅ Comprehensive clustering completed:")
        print(f"   - Silhouette Score: {silhouette:.3f}")
        print(f"   - Calinski-Harabasz Score: {calinski:.1f}")
        
        # Summary statistics with key demographic indicators
        key_features = ['total_population', 'median_income', 'education_rate', 'homeowner_rate', 'remote_work_rate']
        summary = self.census_data.groupby('comprehensive_cluster')[key_features + ['geoid']].agg({
            'total_population': 'mean',
            'median_income': 'mean',
            'education_rate': 'mean',
            'homeowner_rate': 'mean',
            'remote_work_rate': 'mean',
            'geoid': 'count'
        }).round(3)
        summary = summary.rename(columns={'geoid': 'tract_count'})
        
        print(f"\n🎯 Comprehensive Cluster Summary:")
        print(summary)
        
    def generate_insights(self):
        """Generate strategic insights from clustering results."""
        print(f"\n💡 CENSUS TRACT CLUSTERING INSIGHTS & RECOMMENDATIONS")
        print("=" * 70)
        
        if self.population_clusters:
            pop_counts = self.census_data['population_cluster'].value_counts()
            largest_pop_cluster = pop_counts.index[0]
            print(f"🏘️  POPULATION: Cluster {largest_pop_cluster} is the largest with {pop_counts.iloc[0]} tracts")
            
            # High-density areas
            high_density = self.census_data[
                self.census_data['population_density'] > self.census_data['population_density'].quantile(0.8)
            ]
            print(f"   - {len(high_density)} high-density tracts (top 20%)")
            
        if self.economic_clusters:
            # High-income areas
            high_income = self.census_data[
                self.census_data['median_income'] > self.census_data['median_income'].quantile(0.8)
            ]
            print(f"💰 ECONOMIC: {len(high_income)} high-income tracts identified")
            print(f"   - Income threshold: ${self.census_data['median_income'].quantile(0.8):,.0f}+")
            
            # Remote work hotspots
            remote_work = self.census_data[
                self.census_data['remote_work_rate'] > self.census_data['remote_work_rate'].quantile(0.8)
            ]
            print(f"   - {len(remote_work)} remote work hotspots (top 20%)")
            
        if self.education_clusters:
            # Highly educated areas
            high_education = self.census_data[
                self.census_data['education_rate'] > self.census_data['education_rate'].quantile(0.8)
            ]
            print(f"🎓 EDUCATION: {len(high_education)} highly educated tracts")
            print(f"   - Education rate threshold: {self.census_data['education_rate'].quantile(0.8):.1%}+")
            
        if self.comprehensive_clusters:
            comp_counts = self.census_data['comprehensive_cluster'].value_counts()
            cluster_balance = comp_counts.std()
            print(f"🎯 COMPREHENSIVE: {len(comp_counts)} distinct demographic profiles")
            print(f"   - Most common profile: {comp_counts.iloc[0]} tracts")
            print(f"   - Cluster balance: {cluster_balance:.1f} standard deviation")
            
    def export_results(self, filename="census_tract_clustering_results.csv"):
        """Export clustering results to CSV file."""
        print(f"\n💾 Exporting results to {filename}...")
        
        if self.census_data is None:
            print("❌ No data to export. Run load_census_data() first.")
            return
            
        # Select relevant columns for export
        export_columns = [
            'geoid', 'tract_id', 'full_fips', 'state', 'county',
            'total_population', 'median_income', 'median_home_value',
            'education_rate', 'homeowner_rate', 'remote_work_rate',
            'population_density', 'latitude', 'longitude'
        ]
        
        # Add cluster columns if they exist
        cluster_columns = [col for col in self.census_data.columns if col.endswith('_cluster')]
        export_columns.extend(cluster_columns)
        
        # Export data
        export_data = self.census_data[export_columns].copy()
        export_data.to_csv(filename, index=False)
        
        print(f"✅ Exported {len(export_data)} census tracts with {len(cluster_columns)} clustering results")


def main():
    """Main execution function."""
    print("🎯 CENSUS TRACT CLUSTERING ANALYSIS")
    print("=" * 60)
    print("Analyzing demographic patterns in census tract data")
    print()
    
    # Initialize analysis
    analyzer = CensusTractClusteringAnalysis()
    
    # Load data
    analyzer.load_census_data()
    
    # Perform individual clustering analyses
    analyzer.perform_population_housing_clustering(n_clusters=4)
    analyzer.perform_economic_clustering(n_clusters=5)
    analyzer.perform_education_clustering(n_clusters=4)
    analyzer.perform_geographic_clustering(n_clusters=6)
    
    # Create comprehensive multi-dimensional clustering
    analyzer.create_comprehensive_clusters(n_clusters=5)
    
    # Generate insights
    analyzer.generate_insights()
    
    # Export results
    analyzer.export_results()
    
    print("\n✅ Census tract clustering analysis complete!")
    print("\nNext steps:")
    print("- Review census_tract_clustering_results.csv for detailed data")
    print("- Use clusters to understand demographic patterns")
    print("- Target specific demographic profiles for campaigns")
    print("- Analyze geographic clustering for regional strategies")


if __name__ == "__main__":
    main()