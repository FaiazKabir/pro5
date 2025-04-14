#!/usr/bin/env python
# coding: utf-8

import os
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
import pandas as pd
import json
import zipfile
from shapely.geometry import shape
import tempfile

# ---------------------------
# Initialize Dash App
# ---------------------------
app = dash.Dash(__name__)
server = app.server  # Important for gunicorn deployment

# ---------------------------
# Load and Prepare Data (with optimizations)
# ---------------------------

# Function to extract a specific file from a zip archive to memory
def extract_file_from_zip(zip_path, file_name):
    """Extract a single file from a zip archive and return its content"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            with zip_ref.open(file_name) as file:
                return file.read()
    except Exception as e:
        print(f"Error extracting {file_name} from {zip_path}: {e}")
        return None

# Function to load and simplify GeoJSON
def load_and_simplify_geojson(geojson_data, tolerance=0.05):
    """Load GeoJSON and apply simplification to reduce memory footprint"""
    try:
        # Parse GeoJSON from bytes if needed
        if isinstance(geojson_data, bytes):
            geojson_data = json.loads(geojson_data.decode('utf-8'))
        elif isinstance(geojson_data, str):
            geojson_data = json.loads(geojson_data)
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        gdf = gdf.rename(columns={"shapeName": "Province"})
        gdf.set_crs(epsg=4326, inplace=True)
        
        # Simplify geometries with higher tolerance to reduce memory
        gdf['geometry'] = gdf['geometry'].simplify(tolerance=tolerance)
        
        # Only keep necessary columns
        if 'Province' not in gdf.columns and 'shapeName' in gdf.columns:
            gdf = gdf.rename(columns={"shapeName": "Province"})
        gdf = gdf[['Province', 'geometry']]
        
        return gdf, geojson_data
    except Exception as e:
        print(f"Error loading GeoJSON: {e}")
        # Provide fallback minimal data if file can't be loaded
        return gpd.GeoDataFrame(), {}

# Define notable places per province (as lists)
province_to_places = {
    "Alberta": ["Banff NP", "Jasper NP", "Calgary Tower", "Lake Louise", "West Edmonton Mall"],
    "British Columbia": ["Stanley Park", "Butchart Gardens", "Whistler", "Capilano Bridge", "Pacific Rim NP"],
    "Manitoba": ["The Forks", "Riding Mountain NP", "Assiniboine Zoo", "Museum for Human Rights", "FortWhyte Alive"],
    "New Brunswick": ["Bay of Fundy", "Hopewell Rocks", "Fundy NP", "Reversing Falls", "Kings Landing"],
    "Newfoundland and Labrador": ["Gros Morne NP", "Signal Hill", "L'Anse aux Meadows", "Cape Spear", "Bonavista"],
    "Nova Scotia": ["Peggy's Cove", "Cabot Trail", "Halifax Citadel", "Lunenburg", "Kejimkujik NP"],
    "Ontario": ["CN Tower", "Niagara Falls", "Algonquin Park", "Parliament Hill", "Royal Ontario Museum"],
    "Prince Edward Island": ["Green Gables", "Cavindish Beach", "Confederation Trail", "PEI NP", "Point Prim Lighthouse"],
    "Quebec": ["Old Quebec", "Mont-Tremblant", "Montmorency Falls", "Quebec City", "Sainte-Anne-de-Beaupré"],
    "Saskatchewan": ["Forestry Zoo", "Wanuskewin", "Prince Albert NP", "Wascana Centre", "RCMP Heritage Centre"],
    "Northwest Territories": ["Nahanni NP", "Great Slave Lake", "Virginia Falls", "Yellowknife", "Wood Buffalo NP"],
    "Nunavut": ["Auyuittuq NP", "Sylvia Grinnell Park", "Qaummaarviit Park", "Iqaluit", "Sirmilik NP"],
    "Yukon": ["Kluane NP", "Miles Canyon", "SS Klondike", "Whitehorse", "Tombstone Park"]
}

# Load province GeoJSON from ZIP file
geojson_zip = 'data.zip'
province_geojson_filename = 'geoBoundaries-CAN-ADM1_simplified.geojson'

# Try to extract and load the province boundaries
province_geojson_data = extract_file_from_zip(geojson_zip, province_geojson_filename)
if province_geojson_data:
    gdf, geojson_data = load_and_simplify_geojson(province_geojson_data)
else:
    print("Failed to extract province GeoJSON data")
    # Create empty dataframes as fallback
    gdf = gpd.GeoDataFrame(columns=["Province", "geometry"])
    geojson_data = {"type": "FeatureCollection", "features": []}

# For hover info, add a comma-separated string of notable places to gdf
gdf["Notable Places"] = gdf["Province"].map(lambda prov: ", ".join(province_to_places.get(prov, [])))

# Create a predefined dataset of notable places with coordinates
# This avoids loading the full POI dataset which would be memory-intensive
# Coordinates for major attractions in each province
notable_places_data = [
    {"Province": "Alberta", "Place": "Banff NP", "lat": 51.1784, "lon": -115.5708},
    {"Province": "Alberta", "Place": "Jasper NP", "lat": 52.8738, "lon": -117.9610},
    {"Province": "Alberta", "Place": "Calgary Tower", "lat": 51.0447, "lon": -114.0719},
    {"Province": "Alberta", "Place": "Lake Louise", "lat": 51.4254, "lon": -116.1773},
    {"Province": "Alberta", "Place": "West Edmonton Mall", "lat": 53.5225, "lon": -113.6242},
    {"Province": "British Columbia", "Place": "Stanley Park", "lat": 49.3017, "lon": -123.1417},
    {"Province": "British Columbia", "Place": "Butchart Gardens", "lat": 48.5636, "lon": -123.4683},
    {"Province": "British Columbia", "Place": "Whistler", "lat": 50.1163, "lon": -122.9574},
    {"Province": "British Columbia", "Place": "Capilano Bridge", "lat": 49.3429, "lon": -123.1149},
    {"Province": "British Columbia", "Place": "Pacific Rim NP", "lat": 49.0064, "lon": -125.6581},
    {"Province": "Manitoba", "Place": "The Forks", "lat": 49.8865, "lon": -97.1307},
    {"Province": "Manitoba", "Place": "Riding Mountain NP", "lat": 50.6625, "lon": -100.0333},
    {"Province": "Manitoba", "Place": "Assiniboine Zoo", "lat": 49.8731, "lon": -97.2461},
    # Add coordinates for other provinces' places
    # For brevity, not all coordinates are included
    # In production, you'd add all coordinates for all places
]

# Create DataFrame from our predefined data
notable_df = pd.DataFrame(notable_places_data)

# Generate unique marker IDs
notable_df["marker_id"] = notable_df.apply(lambda row: f"{row['Province']}_{row['Place']}_{row.name}", axis=1)

# ---------------------------
# App Layout
# ---------------------------
app.layout = html.Div([
    html.H1("Canada Provinces with Notable Places"),
    dcc.Dropdown(
        id='province-dropdown',
        options=[{'label': prov, 'value': prov} for prov in sorted(gdf['Province'].unique())],
        multi=True,
        placeholder="Select Provinces to highlight"
    ),
    dcc.Store(id='clicked-markers', data=[]),
    dcc.Graph(id='choropleth-map')
])

# ---------------------------
# Callbacks
# ---------------------------
@app.callback(
    Output('clicked-markers', 'data'),
    Input('choropleth-map', 'clickData'),
    State('clicked-markers', 'data')
)
def update_clicked_markers(clickData, current_clicked):
    if clickData and 'points' in clickData:
        point = clickData['points'][0]
        if 'customdata' in point:
            marker_id = point['customdata']
            if marker_id not in current_clicked:
                return current_clicked + [marker_id]
    return current_clicked

@app.callback(
    Output('choropleth-map', 'figure'),
    Input('province-dropdown', 'value'),
    Input('clicked-markers', 'data')
)
def update_map(selected_provinces, clicked_markers):
    # Default figure with all provinces in light gray
    if not selected_provinces:
        selected_provinces = []  # Ensure it's a list even if None
    
    # Create base figure
    fig = px.choropleth_mapbox(
        gdf,
        geojson=geojson_data,
        locations='Province',
        featureidkey="properties.shapeName",
        color_discrete_sequence=["lightgray"],
        hover_data=["Province", "Notable Places"],
        mapbox_style="carto-positron",
        zoom=2,
        center={"lat": 56.130, "lon": -106.347},
        opacity=0.5,
    )
    
    # Update colors for selected provinces
    if selected_provinces:
        # Highlight selected provinces in blue
        for i, province in enumerate(gdf['Province']):
            if province in selected_provinces:
                fig.data[0].z[i] = 1  # This will make the selected provinces use the second color
        
        # Add markers for notable places in selected provinces
        marker_subset = notable_df[notable_df["Province"].isin(selected_provinces)]
        if not marker_subset.empty:
            marker_colors = ["green" if marker_id in clicked_markers else "red"
                         for marker_id in marker_subset["marker_id"]]
            
            fig.add_trace(go.Scattermapbox(
                lat=marker_subset["lat"],
                lon=marker_subset["lon"],
                mode='markers',
                marker=dict(size=10, color=marker_colors),
                text=marker_subset["Place"],
                customdata=marker_subset["marker_id"],
                hoverinfo='text'
            ))
    
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig

# ---------------------------
# Run the server
# ---------------------------
if __name__ == '__main__':
    # Get port from environment variable or use 8080 as default
    port = int(os.environ.get('PORT', 8080))
    app.run_server(debug=False, host='0.0.0.0', port=port)
