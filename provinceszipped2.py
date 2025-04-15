#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
import pandas as pd
import json
import zipfile
import os
from shapely.geometry import shape

# ---------------------------
# Unzip GeoJSON files (Run once on startup)
# ---------------------------
def unzip_geojsons(zip_path, extract_to='.'):
    """Unzip GeoJSON files from a zip archive"""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        print(f"Extracted files from {zip_path}")
        return True
    except FileNotFoundError:
        print(f"Error: Zip file not found at {zip_path}")
        return False
    except Exception as e:
        print(f"Error unzipping {zip_path}: {e}")
        return False

geojson_zip = 'data.zip'  #  Make sure this file is in the same directory.
unzipped = unzip_geojsons(geojson_zip)

# ---------------------------
# Hardcoded Coordinates
# ---------------------------
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

# Initialize Dash App
app = dash.Dash(__name__)
server = app.server  # This is the important line for Render/Gunicorn

app.layout = html.Div([
    html.H1("Canada Provinces with Notable Places"),
    dcc.Dropdown(
        id='province-dropdown',
        options=[],
        multi=True,
        placeholder="Select Provinces to highlight"
    ),
    dcc.Store(id='province-list'),  # Store a simple list of provinces
    dcc.Store(id='clicked-markers', data=[]),
    dcc.Graph(id='choropleth-map')
])

# ---------------------------
# Callback to Load Province Names and Store Them
# ---------------------------
@app.callback(
    [Output('province-dropdown', 'options'),
     Output('province-list', 'data')],
    Input('province-dropdown', 'id')
)
def load_province_names(dummy_id):
    if not unzipped:
        return [], []

    province_geojson_path = 'geoBoundaries-CAN-ADM1_simplified.geojson'
    try:
        with open(province_geojson_path) as f:
            geojson_data = json.load(f)
        provinces = sorted([feature['properties']['shapeName'] for feature in geojson_data['features']])
        province_options = [{'label': prov, 'value': prov} for prov in provinces]
        return province_options, provinces
    except Exception as e:
        print(f"Error loading province names: {e}")
        return [], []

# ---------------------------
# Callback to Update Map Based on Province Selection
# ---------------------------
@app.callback(
    Output('choropleth-map', 'figure'),
    Input('province-dropdown', 'value'),
    State('province-list', 'data'),
    State('clicked-markers', 'data')
)
def update_province_map(selected_provinces, all_provinces, clicked_markers):
    if not unzipped:
        return {'data': [], 'layout': {'title': 'Data loading failed'}}

    province_geojson_path = 'geoBoundaries-CAN-ADM1_simplified.geojson'
    try:
        with open(province_geojson_path) as f:
            geojson_data = json.load(f)

        if not selected_provinces:
            if all_provinces:
                fig = px.choropleth_mapbox(
                    pd.DataFrame({'Province': all_provinces}),
                    geojson=geojson_data,
                    locations='Province',
                    featureidkey="properties.shapeName",
                    color_discrete_sequence=["lightgray"],
                    hover_data=['Province'],
                    mapbox_style="carto-positron",
                    zoom=2,
                    center={"lat": 56.130, "lon": -106.347},
                    opacity=0.5,
                )
                fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
                return fig
            else:
                return {'data': [], 'layout': {'title': 'No province data available', 'margin': {"r": 0, "t": 0, "l": 0, "b": 0}}}

        filtered_features = [
            feat for feat in geojson_data['features']
            if feat['properties']['shapeName'] in selected_provinces
        ]
        filtered_gdf = gpd.GeoDataFrame.from_features(filtered_features)
        if not filtered_gdf.empty:
            filtered_gdf.rename(columns={"shapeName": "Province"}, inplace=True)
            filtered_gdf.set_crs(epsg=4326, inplace=True)
            filtered_gdf['geometry'] = filtered_gdf['geometry'].simplify(tolerance=0.01)

            # Add markers for selected provinces
            markers = []
            for province in selected_provinces:
                for poi in hardcoded_poi_coordinates.get(province, []):
                    marker = go.Scattermapbox(
                        lat=[poi['lat']],
                        lon=[poi['lon']],
                        mode='markers',
                        marker=go.scattermapbox.Marker(
                            size=10,
                            color='red'
                        ),
                        text=poi['place'],
                        hoverinfo='text',
                        customdata=[poi['marker_id']],  # Store a unique ID for clicked detection
                    )
                    markers.append(marker)

            fig = px.choropleth_mapbox(
                filtered_gdf,
                geojson={"type": "FeatureCollection", "features": filtered_features},
                locations='Province',
                featureidkey="properties.shapeName",
                color_discrete_sequence=["blue"],
                hover_data=["Province"],
                mapbox_style="carto-positron",
                zoom=2,
                center={"lat": 56.130, "lon": -106.347},
                opacity=0.7,
            )
            fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
            # Add the marker traces to the figure
            fig.add_traces(markers)
            return fig
        else:
            return {'data': [], 'layout': {'title': 'No provinces selected', 'margin': {"r": 0, "t": 0, "l": 0, "b": 0}}}
    except Exception as e:
        print(f"Error updating province map: {e}")
        return {'data': [], 'layout': {'title': 'Error displaying map', 'margin': {"r": 0, "t": 0, "l": 0, "b": 0}}}



# ---------------------------
# Callback: Update Clicked Markers List
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
            marker_id = point['customdata'][0]  # Get the marker_id from customdata
            if marker_id not in current_clicked:
                return current_clicked + [marker_id]
    return current_clicked

