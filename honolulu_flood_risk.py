"""
High Tide Ahead - Mapping Flood Risk and Population Exposure in Honolulu
A comprehensive geospatial analysis of flood vulnerability in Honolulu County, Hawaii
"""

import geopandas as gpd
import rasterio
from rasterio.mask import mask
from rasterio.warp import calculate_default_transform, reproject, Resampling
import numpy as np
import pandas as pd
from shapely.geometry import mapping
import folium
from folium import plugins
import matplotlib.pyplot as plt
import seaborn as sns
from rasterstats import zonal_stats
import requests
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

class HonoluluFloodAnalysis:
    """Main class for flood risk analysis in Honolulu County"""
    
    def __init__(self, data_dir='data', output_dir='outputs'):
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.output_dir.mkdir(exist_ok=True)
        
        # Target CRS for Honolulu (Hawaii State Plane Zone 3)
        self.target_crs = 'EPSG:3759'
        
        # Data storage
        self.dem = None
        self.dem_transform = None
        self.dem_crs = None
        self.county_boundary = None
        self.hydrology = None
        self.census_data = None
        self.flood_risk_raster = None
        self.population_exposure = None
        
    def load_county_boundary(self, filepath=None):
        """Load Honolulu County boundary from file or create placeholder"""
        print("Loading county boundary...")
        if filepath and Path(filepath).exists():
            self.county_boundary = gpd.read_file(filepath)
        else:
            # Create approximate boundary for Honolulu County (Oahu)
            # These coordinates roughly encompass Oahu island
            from shapely.geometry import box
            bbox = box(-158.3, 21.2, -157.6, 21.75)
            self.county_boundary = gpd.GeoDataFrame(
                {'geometry': [bbox]}, 
                crs='EPSG:4326'
            )
        
        self.county_boundary = self.county_boundary.to_crs(self.target_crs)
        print(f"County boundary loaded: {self.county_boundary.crs}")
        return self.county_boundary
    
    def load_dem(self, filepath):
        """Load and preprocess Digital Elevation Model"""
        print(f"Loading DEM from {filepath}...")
        
        with rasterio.open(filepath) as src:
            # Reproject to target CRS if needed
            if src.crs != self.target_crs:
                transform, width, height = calculate_default_transform(
                    src.crs, self.target_crs, src.width, src.height, *src.bounds
                )
                kwargs = src.meta.copy()
                kwargs.update({
                    'crs': self.target_crs,
                    'transform': transform,
                    'width': width,
                    'height': height
                })
                
                dem_reprojected = np.empty((height, width), dtype=src.dtypes[0])
                reproject(
                    source=rasterio.band(src, 1),
                    destination=dem_reprojected,
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=self.target_crs,
                    resampling=Resampling.bilinear
                )
                
                self.dem = dem_reprojected
                self.dem_transform = transform
                self.dem_crs = self.target_crs
            else:
                # Clip to county boundary
                county_geom = [mapping(self.county_boundary.geometry.iloc[0])]
                out_image, out_transform = mask(src, county_geom, crop=True)
                self.dem = out_image[0]
                self.dem_transform = out_transform
                self.dem_crs = src.crs
        
        print(f"DEM loaded: shape={self.dem.shape}, CRS={self.dem_crs}")
        return self.dem
    
    def load_hydrology(self, filepath=None):
        """Load hydrological features (rivers, coastlines)"""
        print("Loading hydrology data...")
        if filepath and Path(filepath).exists():
            self.hydrology = gpd.read_file(filepath)
            self.hydrology = self.hydrology.to_crs(self.target_crs)
        else:
            # Create synthetic coastline from county boundary
            self.hydrology = self.county_boundary.copy()
            self.hydrology['type'] = 'coastline'
        
        print(f"Hydrology loaded: {len(self.hydrology)} features")
        return self.hydrology
    
    def load_census_data(self, filepath=None):
        """Load census block group data with population"""
        print("Loading census data...")
        if filepath and Path(filepath).exists():
            self.census_data = gpd.read_file(filepath)
        else:
            # Create synthetic census blocks for demonstration
            self.census_data = self._create_synthetic_census_blocks()
        
        self.census_data = self.census_data.to_crs(self.target_crs)
        
        # Ensure population column exists
        if 'population' not in self.census_data.columns:
            if 'POP' in self.census_data.columns:
                self.census_data['population'] = self.census_data['POP']
            else:
                self.census_data['population'] = 1000  # Default value
        
        print(f"Census data loaded: {len(self.census_data)} block groups")
        return self.census_data
    
    def _create_synthetic_census_blocks(self):
        """Create synthetic census blocks for demonstration"""
        from shapely.geometry import box
        import numpy as np
        
        # Get county bounds
        minx, miny, maxx, maxy = self.county_boundary.total_bounds
        
        # Create grid
        n_blocks = 50
        x_coords = np.linspace(minx, maxx, int(np.sqrt(n_blocks)))
        y_coords = np.linspace(miny, maxy, int(np.sqrt(n_blocks)))
        
        blocks = []
        for i in range(len(x_coords)-1):
            for j in range(len(y_coords)-1):
                geom = box(x_coords[i], y_coords[j], x_coords[i+1], y_coords[j+1])
                blocks.append({
                    'geometry': geom,
                    'GEOID': f'15003{i:02d}{j:02d}',
                    'population': np.random.randint(500, 5000)
                })
        
        return gpd.GeoDataFrame(blocks, crs=self.target_crs)
    
    def classify_elevation_risk(self):
        """Classify elevation into flood risk categories"""
        print("Classifying elevation-based flood risk...")
        
        risk_raster = np.zeros_like(self.dem, dtype=np.int8)
        
        # High risk: < 2m elevation
        risk_raster[self.dem < 2] = 3
        # Moderate risk: 2-5m elevation
        risk_raster[(self.dem >= 2) & (self.dem < 5)] = 2
        # Low risk: > 5m elevation
        risk_raster[self.dem >= 5] = 1
        # No data areas
        risk_raster[self.dem < 0] = 0
        
        self.elevation_risk = risk_raster
        print("Elevation risk classification complete")
        return risk_raster
    
    def calculate_proximity_risk(self, buffer_distances=[100, 500, 1000]):
        """Calculate risk based on proximity to water bodies"""
        print("Calculating proximity-based risk...")
        
        from rasterio.features import rasterize
        
        # Create buffers around hydrology features
        buffers = []
        for dist in sorted(buffer_distances, reverse=True):
            buffered = self.hydrology.buffer(dist)
            risk_value = 4 - (buffer_distances.index(dist) + 1)  # 3 for closest, 1 for farthest
            for geom in buffered:
                buffers.append((geom, risk_value))
        
        # Rasterize buffers
        proximity_risk = rasterize(
            buffers,
            out_shape=self.dem.shape,
            transform=self.dem_transform,
            fill=0,
            dtype=np.int8,
            all_touched=True
        )
        
        self.proximity_risk = proximity_risk
        print("Proximity risk calculation complete")
        return proximity_risk
    
    def calculate_composite_risk(self):
        """Combine elevation and proximity into composite flood risk index"""
        print("Calculating composite flood risk...")
        
        # Weighted combination: 60% elevation, 40% proximity
        composite = (0.6 * self.elevation_risk + 0.4 * self.proximity_risk).astype(np.float32)
        
        # Normalize to 0-100 scale
        composite_normalized = ((composite - composite.min()) / 
                               (composite.max() - composite.min()) * 100)
        
        self.flood_risk_raster = composite_normalized
        print("Composite flood risk calculated")
        return composite_normalized
    
    def analyze_population_exposure(self):
        """Calculate population exposure to flood risk zones"""
        print("Analyzing population exposure...")
        
        # Save raster temporarily for zonal stats
        temp_raster = self.output_dir / 'temp_flood_risk.tif'
        with rasterio.open(
            temp_raster, 'w',
            driver='GTiff',
            height=self.flood_risk_raster.shape[0],
            width=self.flood_risk_raster.shape[1],
            count=1,
            dtype=self.flood_risk_raster.dtype,
            crs=self.dem_crs,
            transform=self.dem_transform
        ) as dst:
            dst.write(self.flood_risk_raster, 1)
        
        # Calculate zonal statistics
        stats = zonal_stats(
            self.census_data,
            str(temp_raster),
            stats=['mean', 'max', 'min', 'median'],
            geojson_out=False
        )
        
        # Add statistics to census data
        self.census_data['flood_risk_mean'] = [s['mean'] if s['mean'] else 0 for s in stats]
        self.census_data['flood_risk_max'] = [s['max'] if s['max'] else 0 for s in stats]
        
        # Classify exposure
        self.census_data['risk_category'] = pd.cut(
            self.census_data['flood_risk_mean'],
            bins=[0, 33, 66, 100],
            labels=['Low', 'Moderate', 'High']
        )
        
        # Calculate exposed population
        self.census_data['exposed_population'] = self.census_data.apply(
            lambda row: row['population'] * (row['flood_risk_mean'] / 100), 
            axis=1
        )
        
        # Clean up
        temp_raster.unlink()
        
        self.population_exposure = self.census_data
        print(f"Population exposure analysis complete")
        return self.census_data
    
    def create_interactive_map(self):
        """Create interactive Folium map"""
        print("Creating interactive map...")
        
        # Convert to WGS84 for Folium
        county_wgs84 = self.county_boundary.to_crs('EPSG:4326')
        census_wgs84 = self.census_data.to_crs('EPSG:4326')
        
        # Get center coordinates
        center = [county_wgs84.geometry.centroid.y.iloc[0], 
                 county_wgs84.geometry.centroid.x.iloc[0]]
        
        # Create map
        m = folium.Map(
            location=center,
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # Add choropleth layer for flood risk
        folium.Choropleth(
            geo_data=census_wgs84,
            data=census_wgs84,
            columns=['GEOID', 'flood_risk_mean'],
            key_on='feature.properties.GEOID',
            fill_color='YlOrRd',
            fill_opacity=0.7,
            line_opacity=0.2,
            legend_name='Flood Risk Index (0-100)',
            name='Flood Risk'
        ).add_to(m)
        
        # Add popup information
        style_function = lambda x: {'fillColor': '#ffffff', 
                                   'color':'#000000', 
                                   'fillOpacity': 0.1, 
                                   'weight': 0.1}
        
        highlight_function = lambda x: {'fillColor': '#000000', 
                                       'color':'#000000', 
                                       'fillOpacity': 0.50, 
                                       'weight': 0.1}
        
        popup = folium.GeoJsonPopup(
            fields=['GEOID', 'population', 'flood_risk_mean', 'risk_category'],
            aliases=['Block Group ID', 'Population', 'Flood Risk Score', 'Risk Category'],
            localize=True,
            labels=True
        )
        
        folium.GeoJson(
            census_wgs84,
            style_function=style_function,
            highlight_function=highlight_function,
            popup=popup,
            name='Census Blocks'
        ).add_to(m)
        
        # Add layer control
        folium.LayerControl().add_to(m)
        
        # Save map
        map_path = self.output_dir / 'flood_risk_map.html'
        m.save(str(map_path))
        print(f"Interactive map saved to {map_path}")
        
        return m
    
    def create_static_visualizations(self):
        """Create static charts and visualizations"""
        print("Creating static visualizations...")
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # 1. Flood risk distribution
        axes[0, 0].hist(self.flood_risk_raster.flatten(), bins=50, 
                       color='steelblue', edgecolor='black')
        axes[0, 0].set_xlabel('Flood Risk Score')
        axes[0, 0].set_ylabel('Frequency')
        axes[0, 0].set_title('Distribution of Flood Risk Scores')
        axes[0, 0].grid(True, alpha=0.3)
        
        # 2. Population exposure by risk category
        exposure_summary = self.census_data.groupby('risk_category')['population'].sum()
        axes[0, 1].bar(exposure_summary.index, exposure_summary.values, 
                      color=['green', 'orange', 'red'])
        axes[0, 1].set_xlabel('Risk Category')
        axes[0, 1].set_ylabel('Population')
        axes[0, 1].set_title('Population by Flood Risk Category')
        axes[0, 1].grid(True, alpha=0.3, axis='y')
        
        # 3. Elevation distribution
        axes[1, 0].hist(self.dem[self.dem > 0].flatten(), bins=50,
                       color='brown', edgecolor='black', alpha=0.7)
        axes[1, 0].set_xlabel('Elevation (meters)')
        axes[1, 0].set_ylabel('Frequency')
        axes[1, 0].set_title('Elevation Distribution in Honolulu County')
        axes[1, 0].axvline(x=2, color='red', linestyle='--', label='High Risk Threshold')
        axes[1, 0].axvline(x=5, color='orange', linestyle='--', label='Moderate Risk Threshold')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # 4. Top 10 most vulnerable census blocks
        top_vulnerable = self.census_data.nlargest(10, 'exposed_population')[
            ['GEOID', 'exposed_population']
        ]
        axes[1, 1].barh(range(len(top_vulnerable)), top_vulnerable['exposed_population'].values)
        axes[1, 1].set_yticks(range(len(top_vulnerable)))
        axes[1, 1].set_yticklabels(top_vulnerable['GEOID'].values, fontsize=8)
        axes[1, 1].set_xlabel('Exposed Population')
        axes[1, 1].set_title('Top 10 Most Vulnerable Census Blocks')
        axes[1, 1].grid(True, alpha=0.3, axis='x')
        
        plt.tight_layout()
        viz_path = self.output_dir / 'flood_analysis_visualizations.png'
        plt.savefig(viz_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Static visualizations saved to {viz_path}")
        
    def generate_summary_report(self):
        """Generate summary statistics and findings"""
        print("\n" + "="*60)
        print("HONOLULU FLOOD RISK ANALYSIS - SUMMARY REPORT")
        print("="*60)
        
        total_pop = self.census_data['population'].sum()
        high_risk_pop = self.census_data[
            self.census_data['risk_category'] == 'High'
        ]['population'].sum()
        
        print(f"\nTotal Population Analyzed: {total_pop:,.0f}")
        print(f"Population in High Risk Areas: {high_risk_pop:,.0f} ({high_risk_pop/total_pop*100:.1f}%)")
        
        print("\nPopulation by Risk Category:")
        for category in ['Low', 'Moderate', 'High']:
            pop = self.census_data[
                self.census_data['risk_category'] == category
            ]['population'].sum()
            print(f"  {category}: {pop:,.0f} ({pop/total_pop*100:.1f}%)")
        
        print(f"\nMean Flood Risk Score: {self.census_data['flood_risk_mean'].mean():.2f}")
        print(f"Max Flood Risk Score: {self.census_data['flood_risk_max'].max():.2f}")
        
        print("\nTop 5 Most Vulnerable Census Blocks:")
        top5 = self.census_data.nlargest(5, 'flood_risk_mean')[
            ['GEOID', 'population', 'flood_risk_mean', 'risk_category']
        ]
        print(top5.to_string(index=False))
        
        print("\n" + "="*60)
        
        # Save report to file
        report_path = self.output_dir / 'summary_report.txt'
        with open(report_path, 'w') as f:
            f.write("HONOLULU FLOOD RISK ANALYSIS - SUMMARY REPORT\n")
            f.write("="*60 + "\n\n")
            f.write(f"Total Population Analyzed: {total_pop:,.0f}\n")
            f.write(f"Population in High Risk Areas: {high_risk_pop:,.0f} ({high_risk_pop/total_pop*100:.1f}%)\n\n")
            f.write(top5.to_string(index=False))
        
        print(f"\nFull report saved to {report_path}")
    
    def export_results(self):
        """Export results to files"""
        print("\nExporting results...")
        
        # Export census data with flood risk
        census_export = self.output_dir / 'census_flood_risk.geojson'
        self.census_data.to_file(census_export, driver='GeoJSON')
        print(f"Census data exported to {census_export}")
        
        # Export flood risk raster
        raster_export = self.output_dir / 'flood_risk_raster.tif'
        with rasterio.open(
            raster_export, 'w',
            driver='GTiff',
            height=self.flood_risk_raster.shape[0],
            width=self.flood_risk_raster.shape[1],
            count=1,
            dtype=self.flood_risk_raster.dtype,
            crs=self.dem_crs,
            transform=self.dem_transform,
            compress='lzw'
        ) as dst:
            dst.write(self.flood_risk_raster, 1)
        print(f"Flood risk raster exported to {raster_export}")
        
        # Export summary CSV
        csv_export = self.output_dir / 'census_summary.csv'
        self.census_data.drop(columns='geometry').to_csv(csv_export, index=False)
        print(f"Summary CSV exported to {csv_export}")
    
    def run_complete_analysis(self, dem_path, hydro_path=None, census_path=None):
        """Run the complete flood risk analysis pipeline"""
        print("Starting Honolulu Flood Risk Analysis Pipeline...")
        print("="*60 + "\n")
        
        # 1. Load data
        self.load_county_boundary()
        self.load_dem(dem_path)
        self.load_hydrology(hydro_path)
        self.load_census_data(census_path)
        
        # 2. Calculate flood risk
        self.classify_elevation_risk()
        self.calculate_proximity_risk()
        self.calculate_composite_risk()
        
        # 3. Analyze population exposure
        self.analyze_population_exposure()
        
        # 4. Create visualizations
        self.create_interactive_map()
        self.create_static_visualizations()
        
        # 5. Generate reports
        self.generate_summary_report()
        
        # 6. Export results
        self.export_results()
        
        print("\n" + "="*60)
        print("Analysis complete! Check the 'outputs' folder for results.")
        print("="*60)


# Example usage
if __name__ == "__main__":
    # Initialize analysis
    analysis = HonoluluFloodAnalysis(data_dir='data', output_dir='outputs')
    
    # Option 1: Run with actual data files
    # analysis.run_complete_analysis(
    #     dem_path='data/honolulu_dem.tif',
    #     hydro_path='data/honolulu_hydrology.shp',
    #     census_path='data/honolulu_census.shp'
    # )
    
    # Option 2: Run with synthetic data for demonstration
    print("This script requires actual geospatial data files.")
    print("\nTo run the analysis:")
    print("1. Download DEM data from USGS 3DEP (https://apps.nationalmap.gov/downloader/)")
    print("2. Download hydrology from USGS NHD (https://www.usgs.gov/national-hydrography)")
    print("3. Download census data from TIGER/Line (https://www.census.gov/geographies/mapping-files/time-series/geo/tiger-line-file.html)")
    print("4. Place files in 'data/' folder")
    print("5. Run: analysis.run_complete_analysis(dem_path='...', hydro_path='...', census_path='...')")
    print("\nFor a demo with synthetic data, uncomment the demonstration code below.")
    
    # Demonstration with synthetic data (uncomment to run)
    # print("\n--- RUNNING DEMONSTRATION WITH SYNTHETIC DATA ---\n")
    # Create minimal synthetic DEM for demo
    # import numpy as np
    # demo_dem = np.random.uniform(0, 20, (1000, 1000))
    # analysis.load_county_boundary()
    # analysis.dem = demo_dem
    # analysis.dem_transform = rasterio.transform.from_bounds(
    #     -158.3, 21.2, -157.6, 21.75, 1000, 1000
    # )
    # analysis.dem_crs = analysis.target_crs
    # analysis.load_hydrology()
    # analysis.load_census_data()
    # analysis.classify_elevation_risk()
    # analysis.calculate_proximity_risk()
    # analysis.calculate_composite_risk()
    # analysis.analyze_population_exposure()
    # analysis.create_interactive_map()
    # analysis.create_static_visualizations()
    # analysis.generate_summary_report()
    # analysis.export_results()
