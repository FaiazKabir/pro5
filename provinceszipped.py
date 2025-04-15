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
# This callback will NOT load the large POI GeoJSON initially
# ---------------------------
@app.callback(
    Output('choropleth-map', 'figure'),
    Input('province-dropdown', 'value'),
    State('province-list', 'data')
)
def update_province_map(selected_provinces, all_provinces):
    if not unzipped:
        return {'data': [], 'layout': {'title': 'Data loading failed'}}

    province_geojson_path = 'geoBoundaries-CAN-ADM1_simplified.geojson'
    try:
        with open(province_geojson_path) as f:
            geojson_data = json.load(f)

        if not selected_provinces:
            fig = px.choropleth_mapbox(
                pd.DataFrame({'Province': all_provinces}), # Dummy DataFrame
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

        filtered_features = [
            feat for feat in geojson_data['features']
            if feat['properties']['shapeName'] in selected_provinces
        ]
        filtered_gdf = gpd.GeoDataFrame.from_features(filtered_features)
        if not filtered_gdf.empty:
            filtered_gdf.rename(columns={"shapeName": "Province"}, inplace=True)
            filtered_gdf.set_crs(epsg=4326, inplace=True)
            filtered_gdf['geometry'] = filtered_gdf['geometry'].simplify(tolerance=0.01)
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
            filtered_gdf["Notable Places"] = filtered_gdf["Province"].map(lambda prov: ", ".join(province_to_places.get(prov, [])))

            fig = px.choropleth_mapbox(
                filtered_gdf,
                geojson={
                    "type": "FeatureCollection",
                    "features": filtered_features
                },
                locations='Province',
                featureidkey="properties.shapeName",
                color_discrete_sequence=["blue"],
                hover_data=["Province", "Notable Places"],
                mapbox_style="carto-positron",
                zoom=2,
                center={"lat": 56.130, "lon": -106.347},
                opacity=0.7,
            )
            fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

            # **Crucially, we are NOT loading and processing the large POI file here.**
            # We would need a different strategy to display POIs within memory limits.

            return fig
        else:
            return {'data': [], 'layout': {'title': 'No provinces selected'}}

    except Exception as e:
        print(f"Error updating province map: {e}")
        return {'data': [], 'layout': {'title': 'Error displaying map'}}

# ---------------------------
# Placeholder for Potential POI Interaction (Needs a Memory-Efficient Strategy)
# ---------------------------
# You would need a different way to handle the large POI file.
# Some possibilities (each with its own complexity):
# 1. Pre-process POIs: Filter and save smaller, province-specific POI files. Load these on demand.
# 2. Use a geospatial database: Query POIs within the selected province boundaries.
# 3. Implement client-side filtering (if the browser has enough memory, which is unlikely for 280MB).

if __name__ == '__main__':
    app.run_server(debug=False)
