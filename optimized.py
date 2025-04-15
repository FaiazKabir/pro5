import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import json
import zipfile
import os
from flask_caching import Cache
import pandas as pd

# ---------------------------
# Initialize Dash App with Caching
# ---------------------------
app = dash.Dash(__name__)
server = app.server  # For Render/Gunicorn deployment

# Setup caching - simple RAM cache that will help with repeated operations
cache = Cache(app.server, config={
    'CACHE_TYPE': 'SimpleCache',
    'CACHE_DEFAULT_TIMEOUT': 300  # 5 minutes cache timeout
})

# ---------------------------
# Data Loading Functions (Run once on startup)
# ---------------------------
@cache.memoize()
def unzip_and_load_geojson(zip_path='data.zip', geojson_name='geoBoundaries-CAN-ADM1_simplified.geojson'):
    """Unzip GeoJSON files and load data - cached for efficiency"""
    try:
        # Extract if needed
        if not os.path.exists(geojson_name):
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall('.')
            print(f"Extracted files from {zip_path}")
        
        # Load the GeoJSON file
        with open(geojson_name) as f:
            geojson_data = json.load(f)
            
        # Pre-process: Simplify features to reduce payload size
        for feature in geojson_data['features']:
            if 'geometry' in feature and feature['geometry'] and 'coordinates' in feature['geometry']:
                # Simplify multipolygon coordinates (reduce detail for performance)
                if feature['geometry']['type'] == 'MultiPolygon':
                    feature['geometry']['coordinates'] = [[[coord for i, coord in enumerate(polygon[0]) if i % 3 == 0]] 
                                                         for polygon in feature['geometry']['coordinates']]
                elif feature['geometry']['type'] == 'Polygon':
                    feature['geometry']['coordinates'] = [[coord for i, coord in enumerate(ring) if i % 3 == 0] 
                                                         for ring in feature['geometry']['coordinates']]
        
        # Extract provinces list
        provinces = sorted([feature['properties']['shapeName'] for feature in geojson_data['features']])
        
        return geojson_data, provinces, True
    except FileNotFoundError:
        print(f"Error: File not found at {zip_path} or {geojson_name}")
        return None, [], False
    except Exception as e:
        print(f"Error loading data: {e}")
        return None, [], False

# Load POI data - structured as a pandas DataFrame for better processing
@cache.memoize()
def load_poi_data():
    """Load Points of Interest data"""
    hardcoded_poi_coordinates = {
        "Alberta": [
            {"place": "Banff NP", "lat": 51.4968, "lon": -115.9281, "marker_id": "Alberta_Banff NP"},
            {"place": "Jasper NP", "lat": 52.8736, "lon": -117.9430, "marker_id": "Alberta_Jasper NP"},
            {"place": "Calgary Tower", "lat": 51.0452, "lon": -114.0581, "marker_id": "Alberta_Calgary Tower"},
            {"place": "Lake Louise", "lat": 51.4167, "lon": -116.2167, "marker_id": "Alberta_Lake Louise"},
            {"place": "West Edmonton Mall", "lat": 53.5225, "lon": -113.6242, "marker_id": "Alberta_West Edmonton Mall"}
        ],
        "British Columbia": [
            {"place": "Stanley Park", "lat": 49.3021, "lon": -123.1460, "marker_id": "British Columbia_Stanley Park"},
            {"place": "Butchart Gardens", "lat": 48.5258, "lon": -123.4628, "marker_id": "British Columbia_Butchart Gardens"},
            {"place": "Whistler", "lat": 50.1167, "lon": -122.9567, "marker_id": "British Columbia_Whistler"},
            {"place": "Capilano Bridge", "lat": 49.3257, "lon": -123.0957, "marker_id": "British Columbia_Capilano Bridge"},
            {"place": "Pacific Rim NP", "lat": 49.0000, "lon": -125.5000, "marker_id": "British Columbia_Pacific Rim NP"}
        ],
        "Manitoba": [
            {"place": "The Forks", "lat": 49.8947, "lon": -97.1258, "marker_id": "Manitoba_The Forks"},
            {"place": "Riding Mountain NP", "lat": 50.6500, "lon": -99.9833, "marker_id": "Manitoba_Riding Mountain NP"},
            {"place": "Assiniboine Zoo", "lat": 49.8844, "lon": -97.2378, "marker_id": "Manitoba_Assiniboine Zoo"},
            {"place": "Museum for Human Rights", "lat": 49.8928, "lon": -97.1306, "marker_id": "Manitoba_Museum for Human Rights"},
            {"place": "FortWhyte Alive", "lat": 49.8167, "lon": -97.2667, "marker_id": "Manitoba_FortWhyte Alive"}
        ],
        "New Brunswick": [
            {"place": "Bay of Fundy", "lat": 45.0000, "lon": -66.5000, "marker_id": "New Brunswick_Bay of Fundy"},
            {"place": "Hopewell Rocks", "lat": 45.8406, "lon": -64.6264, "marker_id": "New Brunswick_Hopewell Rocks"},
            {"place": "Fundy NP", "lat": 45.5667, "lon": -64.9667, "marker_id": "New Brunswick_Fundy NP"},
            {"place": "Reversing Falls", "lat": 45.2600, "lon": -66.0667, "marker_id": "New Brunswick_Reversing Falls"},
            {"place": "Kings Landing", "lat": 45.8500, "lon": -67.0500, "marker_id": "New Brunswick_Kings Landing"}
        ],
        "Newfoundland and Labrador": [
            {"place": "Gros Morne NP", "lat": 49.5000, "lon": -57.5000, "marker_id": "Newfoundland and Labrador_Gros Morne NP"},
            {"place": "Signal Hill", "lat": 47.5708, "lon": -52.6922, "marker_id": "Newfoundland and Labrador_Signal Hill"},
            {"place": "L'Anse aux Meadows", "lat": 51.5783, "lon": -55.5297, "marker_id": "Newfoundland and Labrador_L'Anse aux Meadows"},
            {"place": "Cape Spear", "lat": 47.5283, "lon": -52.6231, "marker_id": "Newfoundland and Labrador_Cape Spear"},
            {"place": "Bonavista", "lat": 48.6488, "lon": -53.1124, "marker_id": "Newfoundland and Labrador_Bonavista"}
        ],
        "Nova Scotia": [
            {"place": "Peggy's Cove", "lat": 44.4983, "lon": -63.9100, "marker_id": "Nova Scotia_Peggy's Cove"},
            {"place": "Cabot Trail", "lat": 46.5000, "lon": -60.5000, "marker_id": "Nova Scotia_Cabot Trail"},
            {"place": "Halifax Citadel", "lat": 44.6500, "lon": -63.5753, "marker_id": "Nova Scotia_Halifax Citadel"},
            {"place": "Lunenburg", "lat": 44.3833, "lon": -64.3167, "marker_id": "Nova Scotia_Lunenburg"},
            {"place": "Kejimkujik NP", "lat": 44.4333, "lon": -65.4167, "marker_id": "Nova Scotia_Kejimkujik NP"}
        ],
        "Ontario": [
            {"place": "CN Tower", "lat": 43.6426, "lon": -79.3871, "marker_id": "Ontario_CN Tower"},
            {"place": "Niagara Falls", "lat": 43.0962, "lon": -79.0377, "marker_id": "Ontario_Niagara Falls"},
            {"place": "Algonquin Park", "lat": 45.7750, "lon": -78.3000, "marker_id": "Ontario_Algonquin Park"},
            {"place": "Parliament Hill", "lat": 45.4247, "lon": -75.6950, "marker_id": "Ontario_Parliament Hill"},
            {"place": "Royal Ontario Museum", "lat": 43.6678, "lon": -79.3940, "marker_id": "Ontario_Royal Ontario Museum"}
        ],
        "Prince Edward Island": [
            {"place": "Green Gables", "lat": 46.4947, "lon": -63.3708, "marker_id": "Prince Edward Island_Green Gables"},
            {"place": "Cavindish Beach", "lat": 46.5167, "lon": -63.4333, "marker_id": "Prince Edward Island_Cavindish Beach"},
            {"place": "Confederation Trail", "lat": 46.3000, "lon": -63.0000, "marker_id": "Prince Edward Island_Confederation Trail"},
            {"place": "PEI NP", "lat": 46.5000, "lon": -63.2500, "marker_id": "Prince Edward Island_PEI NP"},
            {"place": "Point Prim Lighthouse", "lat": 46.0633, "lon": -62.9650, "marker_id": "Prince Edward Island_Point Prim Lighthouse"}
        ],
        "Quebec": [
            {"place": "Old Quebec", "lat": 46.8123, "lon": -71.2151, "marker_id": "Quebec_Old Quebec"},
            {"place": "Mont-Tremblant", "lat": 46.1183, "lon": -74.5956, "marker_id": "Quebec_Mont-Tremblant"},
            {"place": "Montmorency Falls", "lat": 46.8767, "lon": -71.1800, "marker_id": "Quebec_Montmorency Falls"},
            {"place": "Quebec City", "lat": 46.8139, "lon": -71.2080, "marker_id": "Quebec_Quebec City"},
            {"place": "Sainte-Anne-de-Beaupré", "lat": 47.0000, "lon": -70.9333, "marker_id": "Quebec_Sainte-Anne-de-Beaupré"}
        ],
        "Saskatchewan": [
            {"place": "Forestry Zoo", "lat": 52.1333, "lon": -106.6333, "marker_id": "Saskatchewan_Forestry Zoo"},
            {"place": "Wanuskewin", "lat": 52.2000, "lon": -106.5500, "marker_id": "Saskatchewan_Wanuskewin"},
            {"place": "Prince Albert NP", "lat": 53.9333, "lon": -106.3333, "marker_id": "Saskatchewan_Prince Albert NP"},
            {"place": "Wascana Centre", "lat": 50.4333, "lon": -104.6167, "marker_id": "Saskatchewan_Wascana Centre"},
            {"place": "RCMP Heritage Centre", "lat": 50.4000, "lon": -104.6500, "marker_id": "Saskatchewan_RCMP Heritage Centre"}
        ],
        "Northwest Territories": [
            {"place": "Nahanni NP", "lat": 63.3333, "lon": -123.5000, "marker_id": "Northwest Territories_Nahanni NP"},
            {"place": "Great Slave Lake", "lat": 61.6667, "lon": -114.0000, "marker_id": "Northwest Territories_Great Slave Lake"},
            {"place": "Virginia Falls", "lat": 61.5833, "lon": -125.2167, "marker_id": "Northwest Territories_Virginia Falls"},
            {"place": "Yellowknife", "lat": 62.4500, "lon": -114.3500, "marker_id": "Northwest Territories_Yellowknife"},
            {"place": "Wood Buffalo NP", "lat": 59.5000, "lon": -112.0000, "marker_id": "Northwest Territories_Wood Buffalo NP"}
        ],
        "Nunavut": [
            {"place": "Auyuittuq NP", "lat": 67.8333, "lon": -65.0000, "marker_id": "Nunavut_Auyuittuq NP"},
            {"place": "Sylvia Grinnell Park", "lat": 63.7333, "lon": -68.5333, "marker_id": "Nunavut_Sylvia Grinnell Park"},
            {"place": "Qaummaarviit Park", "lat": 63.6833, "lon": -68.4833, "marker_id": "Nunavut_Qaummaarviit Park"},
            {"place": "Iqaluit", "lat": 63.7500, "lon": -68.5167, "marker_id": "Nunavut_Iqaluit"},
            {"place": "Sirmilik NP", "lat": 73.0000, "lon": -80.0000, "marker_id": "Nunavut_Sirmilik NP"}
        ],
        "Yukon": [
            {"place": "Kluane NP", "lat": 61.0000, "lon": -138.4167, "marker_id": "Yukon_Kluane NP"},
            {"place": "Miles Canyon", "lat": 60.7167, "lon": -135.0500, "marker_id": "Yukon_Miles Canyon"},
            {"place": "SS Klondike", "lat": 60.7167, "lon": -135.0500, "marker_id": "Yukon_SS Klondike"},
            {"place": "Whitehorse", "lat": 60.7167, "lon": -135.0500, "marker_id": "Yukon_Whitehorse"},
            {"place": "Tombstone Park", "lat": 64.4500, "lon": -138.3333, "marker_id": "Yukon_Tombstone Park"}
        ]
    }
    
    # Convert nested dictionary to flattened DataFrame for better performance
    poi_rows = []
    for province, pois in hardcoded_poi_coordinates.items():
        for poi in pois:
            poi_rows.append({
                'province': province,
                'place': poi['place'],
                'lat': poi['lat'],
                'lon': poi['lon'],
                'marker_id': poi['marker_id']
            })
    
    return pd.DataFrame(poi_rows)

# Load data at startup
geojson_data, provinces, load_success = unzip_and_load_geojson()
poi_df = load_poi_data()

# ---------------------------
# App Layout
# ---------------------------
app.layout = html.Div([
    html.H1("Canada Provinces with Notable Places"),
    dcc.Dropdown(
        id='province-dropdown',
        options=[{'label': prov, 'value': prov} for prov in provinces] if load_success else [],
        multi=True,
        placeholder="Select Provinces to highlight"
    ),
    dcc.Store(id='clicked-markers', data=[]),
    dcc.Graph(id='choropleth-map')
])

# ---------------------------
# Callback to Update Map Based on Province Selection
# ---------------------------
@app.callback(
    Output('choropleth-map', 'figure'),
    [Input('province-dropdown', 'value'),
     Input('clicked-markers', 'data')]
)
def update_province_map(selected_provinces, clicked_markers):
    if not load_success:
        return {'data': [], 'layout': {'title': 'Data loading failed'}}
    
    # Default map settings
    center = {"lat": 56.130, "lon": -106.347}
    zoom = 2
    
    # If no provinces selected, show all provinces in light gray
    if not selected_provinces or len(selected_provinces) == 0:
        df = pd.DataFrame({'Province': provinces})
        fig = px.choropleth_mapbox(
            df,
            geojson=geojson_data,
            locations='Province',
            featureidkey="properties.shapeName",
            color_discrete_sequence=["lightgray"],
            mapbox_style="carto-positron",
            zoom=zoom,
            center=center,
            opacity=0.5,
        )
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig
    
    # Filter to selected provinces
    selected_provinces_df = pd.DataFrame({'Province': selected_provinces})
    
    # Create base map with selected provinces
    fig = px.choropleth_mapbox(
        selected_provinces_df,
        geojson=geojson_data,
        locations='Province',
        featureidkey="properties.shapeName",
        color_discrete_sequence=["blue"],
        hover_data=['Province'],
        mapbox_style="carto-positron",
        zoom=zoom,
        center=center,
        opacity=0.7,
    )
    
    # Efficiently filter POI data for selected provinces
    filtered_poi = poi_df[poi_df['province'].isin(selected_provinces)]
    
    # Add markers for selected provinces (if any POIs exist)
    if not filtered_poi.empty:
        # Set marker colors based on clicked status
        filtered_poi['color'] = filtered_poi['marker_id'].apply(
            lambda x: 'green' if x in clicked_markers else 'red'
        )
        
        # Add all markers in a single trace for better performance
        fig.add_trace(go.Scattermapbox(
            lat=filtered_poi['lat'].tolist(),
            lon=filtered_poi['lon'].tolist(),
            mode='markers',
            marker=dict(
                size=10,
                color=filtered_poi['color'].tolist(),
            ),
            text=filtered_poi['place'].tolist(),
            hoverinfo='text',
            customdata=filtered_poi['marker_id'].tolist(),
        ))
    
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig

# ---------------------------
# Callback: Update Clicked Markers List
# ---------------------------
@app.callback(
    Output('clicked-markers', 'data'),
    Input('choropleth-map', 'clickData'),
    State('clicked-markers', 'data')
)
def update_clicked_markers(clickData, current_clicked):
    if not clickData or 'points' not in clickData:
        return current_clicked
    
    point = clickData['points'][0]
    
    # Check if a marker was clicked (has customdata)
    if 'customdata' not in point:
        return current_clicked
    
    marker_id = point['customdata']
    
    # Toggle marker status
    if marker_id in current_clicked:
        return [mid for mid in current_clicked if mid != marker_id]
    else:
        return current_clicked + [marker_id]

if __name__ == '__main__':
    app.run_server(debug=False)
