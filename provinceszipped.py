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

geojson_zip = 'data.zip'
unzipped = unzip_geojsons(geojson_zip)

# ---------------------------
# Hardcoded Coordinates
# ---------------------------
hardcoded_poi_coordinates = {
    "Alberta": [
        {"place": "Banff NP", "lat": 51.4968, "lon": -115.9281},
        {"place": "Jasper NP", "lat": 52.8736, "lon": -117.9430},
        {"place": "Calgary Tower", "lat": 51.0452, "lon": -114.0581},
        {"place": "Lake Louise", "lat": 51.4167, "lon": -116.2167},
        {"place": "West Edmonton Mall", "lat": 53.5225, "lon": -113.6242}
    ],
    "British Columbia": [
        {"place": "Stanley Park", "lat": 49.3021, "lon": -123.1460},
        {"place": "Butchart Gardens", "lat": 48.5258, "lon": -123.4628},
        {"place": "Whistler", "lat": 50.1167, "lon": -122.9567},
        {"place": "Capilano Bridge", "lat": 49.3257, "lon": -123.0957},
        {"place": "Pacific Rim NP", "lat": 49.0000, "lon": -125.5000}
    ],
    "Manitoba": [
        {"place": "The Forks", "lat": 49.8947, "lon": -97.1258},
        {"place": "Riding Mountain NP", "lat": 50.6500, "lon": -99.9833},
        {"place": "Assiniboine Zoo", "lat": 49.8844, "lon": -97.2378},
        {"place": "Museum for Human Rights", "lat": 49.8928, "lon": -97.1306},
        {"place": "FortWhyte Alive", "lat": 49.8167, "lon": -97.2667}
    ],
    "New Brunswick": [
        {"place": "Bay of Fundy", "lat": 45.0000, "lon": -66.5000},
        {"place": "Hopewell Rocks", "lat": 45.8406, "lon": -64.6264},
        {"place": "Fundy NP", "lat": 45.5667, "lon": -64.9667},
        {"place": "Reversing Falls", "lat": 45.2600, "lon": -66.0667},
        {"place": "Kings Landing", "lat": 45.8500, "lon": -67.0500}
    ],
    "Newfoundland and Labrador": [
        {"place": "Gros Morne NP", "lat": 49.5000, "lon": -57.5000},
        {"place": "Signal Hill", "lat": 47.5708, "lon": -52.6922},
        {"place": "L'Anse aux Meadows", "lat": 51.5783, "lon": -55.5297},
        {"place": "Cape Spear", "lat": 47.5283, "lon": -52.6231},
        {"place": "Bonavista", "lat": 48.6488, "lon": -53.1124}
    ],
    "Nova Scotia": [
        {"place": "Peggy's Cove", "lat": 44.4983, "lon": -63.9100},
        {"place": "Cabot Trail", "lat": 46.5000, "lon": -60.5000},
        {"place": "Halifax Citadel", "lat": 44.6500, "lon": -63.5753},
        {"place": "Lunenburg", "lat": 44.3833, "lon": -64.3167},
        {"place": "Kejimkujik NP", "lat": 44.4333, "lon": -65.4167}
    ],
    "Ontario": [
        {"place": "CN Tower", "lat": 43.6426, "lon": -79.3871},
        {"place": "Niagara Falls", "lat": 43.0962, "lon": -79.0377},
        {"place": "Algonquin Park", "lat": 45.7750, "lon": -78.3000},
        {"place": "Parliament Hill", "lat": 45.4247, "lon": -75.6950},
        {"place": "Royal Ontario Museum", "lat": 43.6678, "lon": -79.3940}
    ],
    "Prince Edward Island": [
        {"place": "Green Gables", "lat": 46.4947, "lon": -63.3708},
        {"place": "Cavindish Beach", "lat": 46.5167, "lon": -63.4333},
        {"place": "Confederation Trail", "lat": 46.3000, "lon": -63.0000},
        {"place": "PEI NP", "lat": 46.5000, "lon": -63.2500},
        {"place": "Point Prim Lighthouse", "lat": 46.0633, "lon": -62.9650}
    ],
    "Quebec": [
        {"place": "Old Quebec", "lat": 46.8123, "lon": -71.2151},
        {"place": "Mont-Tremblant", "lat": 46.1183, "lon": -74.5956},
        {"place": "Montmorency Falls", "lat": 46.8767, "lon": -71.1800},
        {"place": "Quebec City", "lat": 46.8139, "lon": -71.2080},
        {"place": "Sainte-Anne-de-Beaupré", "lat": 47.0000, "lon": -70.9333}
    ],
    "Saskatchewan": [
        {"place": "Forestry Zoo", "lat": 52.1333, "lon": -106.6333},
        {"place": "Wanuskewin", "lat": 52.2000, "lon": -106.5500},
        {"place": "Prince Albert NP", "lat": 53.9333, "lon": -106.3333},
        {"place": "Wascana Centre", "lat": 50.4333, "lon": -104.6167},
        {"place": "RCMP Heritage Centre", "lat": 50.4000, "lon": -104.6500}
    ],
    "Northwest Territories": [
        {"place": "Nahanni NP", "lat": 63.3333, "lon": -123.5000},
        {"place": "Great Slave Lake", "lat": 61.6667, "lon": -114.0000},
        {"place": "Virginia Falls", "lat": 61.5833, "lon": -125.2167},
        {"place": "Yellowknife", "lat": 62.4500, "lon": -114.3500},
        {"place": "Wood Buffalo NP", "lat": 59.5000, "lon": -112.0000}
    ],
    "Nunavut": [
        {"place": "Auyuittuq NP", "lat": 67.8333, "lon": -65.0000},
        {"place": "Sylvia Grinnell Park", "lat": 63.7333, "lon": -68.5333},
        {"place": "Qaummaarviit Park", "lat": 63.6833, "lon": -68.4833},
        {"place": "Iqaluit", "lat": 63.7500, "lon": -68.5167},
        {"place": "Sirmilik NP", "lat": 73.0000, "lon": -80.0000}
    ],
    "Yukon": [
        {"place": "Kluane NP", "lat": 61.0000, "lon": -138.4167},
        {"place": "Miles Canyon", "lat": 60.7167, "lon": -135.0500},
        {"place": "SS Klondike", "lat": 60.7167, "lon": -135.0500},
        {"place": "Whitehorse", "lat": 60.7167, "lon": -135.0500},
        {"place": "Tombstone Park", "lat": 64.4500, "lon": -138.3333}
    ]
}

# Initialize Dash App
app = dash.Dash(__name__)
server = app.server

app.layout = html.Div([
    html.H1("Canada Provinces with Notable Places"),
    dcc.Dropdown(
        id='province-dropdown',
        options=[],
        multi=True,
        placeholder="Select Provinces to highlight"
    ),
    dcc.Store(id='province-list'), # Store a simple list of provinces
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

        fig = px.choropleth_mapbox(
            pd.DataFrame({'Province': selected_provinces or all_provinces}),
            geojson=geojson_data,
            locations='Province',
            feature
