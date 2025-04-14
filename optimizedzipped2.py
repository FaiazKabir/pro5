#!/usr/bin/env python
# coding: utf-8

import os
import sys
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
import pandas as pd
import json
import zipfile
import tempfile
from shapely.geometry import shape

# ---------------------------
# Set up logging for debugging
# ---------------------------
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

# ---------------------------
# Initialize Dash App
# ---------------------------
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # Important for gunicorn deployment

# ---------------------------
# Load and Prepare Data (with debugging)
# ---------------------------

def extract_file_from_zip(zip_path, file_name):
    """Extract a single file from a zip archive and return its content"""
    try:
        logger.info(f"Attempting to extract {file_name} from {zip_path}")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            # List all files in the zip to verify content
            logger.info(f"Files in zip: {zip_ref.namelist()}")
            if file_name in zip_ref.namelist():
                with zip_ref.open(file_name) as file:
                    logger.info(f"Successfully extracted {file_name}")
                    return file.read()
            else:
                logger.error(f"File {file_name} not found in {zip_path}")
                # If exact name not found, try to find a similar file
                for name in zip_ref.namelist():
                    if file_name.lower() in name.lower():
                        logger.info(f"Found similar file: {name}")
                        with zip_ref.open(name) as file:
                            return file.read()
                return None
    except Exception as e:
        logger.error(f"Error extracting {file_name} from {zip_path}: {e}")
        return None

def load_and_simplify_geojson(geojson_data, tolerance=0.05):
    """Load GeoJSON and apply simplification to reduce memory footprint"""
    try:
        # Parse GeoJSON from bytes if needed
        if isinstance(geojson_data, bytes):
            geojson_data = json.loads(geojson_data.decode('utf-8'))
        elif isinstance(geojson_data, str):
            geojson_data = json.loads(geojson_data)
        
        logger.info(f"GeoJSON parsed successfully. Features: {len(geojson_data['features'])}")
        
        # Create GeoDataFrame
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        
        # Check for shapeName column and rename if found
        if 'shapeName' in gdf.columns:
            gdf = gdf.rename(columns={"shapeName": "Province"})
        
        # Ensure CRS is set
        gdf.set_crs(epsg=4326, inplace=True)
        
        # Simplify geometries with higher tolerance to reduce memory
        gdf['geometry'] = gdf['geometry'].simplify(tolerance=tolerance)
        
        # Verify we have the Province column
        if 'Province' not in gdf.columns:
            logger.error("Province column not found in GeoJSON")
            # Try to find an alternative column
            for col in gdf.columns:
                if 'name' in col.lower() or 'province' in col.lower():
                    logger.info(f"Using column {col} as Province")
                    gdf = gdf.rename(columns={col: "Province"})
                    break
        
        # Only keep necessary columns
        if 'Province' in gdf.columns:
            gdf = gdf[['Province', 'geometry']]
            logger.info(f"Provinces found: {gdf['Province'].tolist()}")
        else:
            logger.error("Could not find Province column")
        
        return gdf, geojson_data
    except Exception as e:
        logger.error(f"Error loading GeoJSON: {e}")
        # Provide fallback minimal data
        return gpd.GeoDataFrame(columns=["Province", "geometry"]), {"type": "FeatureCollection", "features": []}

# Define notable places per province
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
logger.info("Starting data loading process")
geojson_zip = 'data.zip'
province_geojson_filename = 'geoBoundaries-CAN-ADM1_simplified.geojson'

# Create a fallback minimal GeoDataFrame in case loading fails
fallback_provinces = list(province_to_places.keys())
fallback_gdf = gpd.GeoDataFrame({
    "Province": fallback_provinces,
    "geometry": [None] * len(fallback_provinces)
})

# Try to extract and load the province boundaries
province_geojson_data = extract_file_from_zip(geojson_zip, province_geojson_filename)
if province_geojson_data:
    logger.info("Successfully extracted province GeoJSON data")
    gdf, geojson_data = load_and_simplify_geojson(province_geojson_data)
    
    # Verify we have valid data
    if gdf.empty:
        logger.warning("GeoDataFrame is empty, using fallback")
        gdf = fallback_gdf
        # Create minimal geojson as well
        geojson_data = {"type": "FeatureCollection", "features": []}
    else:
        logger.info(f"Loaded GeoDataFrame with {len(gdf)} rows")
else:
    logger.error("Failed to extract province GeoJSON data, using fallback")
    gdf = fallback_gdf
    geojson_data = {"type": "FeatureCollection", "features": []}

# Add notable places to GeoDataFrame
gdf["Notable Places"] = gdf["Province"].map(lambda prov: ", ".join(province_to_places.get(prov, [])))

# Create a predefined dataset of notable places with coordinates
# This avoids loading the full POI dataset
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
    # Add more coordinates for other provinces
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
    html.Div([
        html.Label("Select provinces to highlight:"),
        dcc.Dropdown(
            id='province-dropdown',
            options=[{'label': prov, 'value': prov} for prov in sorted(gdf['Province'].unique())],
            multi=True,
            placeholder="Select Provinces to highlight",
            style={'width': '100%'}
        ),
    ], style={'margin-bottom': '20px'}),
    html.Div(id='selection-info', children="No provinces selected"),
    dcc.Store(id='clicked-markers', data=[]),
    dcc.Graph(id='choropleth-map', style={'height': '700px'})
])

# ---------------------------
# Callbacks
# ---------------------------
@app.callback(
    Output('selection-info', 'children'),
    Input('province-dropdown', 'value')
)
def update_selection_info(selected_provinces):
    """Update text showing what's currently selected (debugging aid)"""
    if not selected_provinces or len(selected_provinces) == 0:
        return "No provinces selected"
    return f"Selected provinces: {', '.join(selected_provinces)}"

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
                logger.info(f"Marker clicked: {marker_id}")
                return current_clicked + [marker_id]
            else:
                # Toggle off if clicked again
                logger.info(f"Marker unclicked: {marker_id}")
                return [m for m in current_clicked if m != marker_id]
    return current_clicked or []

@app.callback(
    Output('choropleth-map', 'figure'),
    Input('province-dropdown', 'value'),
    Input('clicked-markers', 'data')
)
def update_map(selected_provinces, clicked_markers):
    logger.info(f"Updating map with selected provinces: {selected_provinces}")
    logger.info(f"Clicked markers: {clicked_markers}")
    
    # Handle None or empty selections
    if not selected_provinces:
        selected_provinces = []
    
    # Create two separate dataframes - one for selected provinces and one for unselected
    selected_gdf = gdf[gdf["Province"].isin(selected_provinces)] if selected_provinces else gpd.GeoDataFrame()
    unselected_gdf = gdf[~gdf["Province"].isin(selected_provinces)] if selected_provinces else gdf
    
    # Base figure with unselected provinces
    fig = px.choropleth_mapbox(
        unselected_gdf,
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
    
    # Add selected provinces with different color
    if not selected_gdf.empty:
        selected_fig = px.choropleth_mapbox(
            selected_gdf,
            geojson=geojson_data,
            locations='Province',
            featureidkey="properties.shapeName",
            color_discrete_sequence=["blue"],
            hover_data=["Province", "Notable Places"],
            opacity=0.7,
        )
        fig.add_trace(selected_fig.data[0])
    
    # Add markers for notable places in selected provinces
    if selected_provinces:
        marker_subset = notable_df[notable_df["Province"].isin(selected_provinces)]
        if not marker_subset.empty:
            logger.info(f"Adding {len(marker_subset)} markers for selected provinces")
            
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
    
    fig.update_layout(
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        mapbox_style="carto-positron",
        mapbox=dict(
            zoom=2,
            center={"lat": 56.130, "lon": -106.347},
        )
    )
    
    return fig

# ---------------------------
# Run the server
# ---------------------------
if __name__ == '__main__':
    # Get port from environment variable or use 8080 as default
    port = int(os.environ.get('PORT', 8080))
    logger.info(f"Starting server on port {port}")
    app.run_server(debug=False, host='0.0.0.0', port=port)
