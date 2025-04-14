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
        options=[],  # Options will be populated dynamically
        multi=True,
        placeholder="Select Provinces to highlight"
    ),
    dcc.Store(id='province-data'), # Store to hold province-specific data
    dcc.Store(id='poi-data'),      # Store to hold POI data
    dcc.Store(id='clicked-markers', data=[]),
    dcc.Graph(id='choropleth-map')
])

# ---------------------------
# Callback to Load Initial Data and Populate Dropdown
# ---------------------------
@app.callback(
    [Output('province-dropdown', 'options'),
     Output('province-data', 'data'),
     Output('poi-data', 'data')],
    Input('province-dropdown', 'id') # Dummy input to trigger on app load
)
def load_initial_data(dummy_id):
    if not unzipped:
        return [], {}, {}

    province_geojson_path = 'geoBoundaries-CAN-ADM1_simplified.geojson'
    poi_geojson_path = "hotosm_can_points_of_interest_points_geojson.geojson"
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

    try:
        with open(province_geojson_path) as f:
            geojson_data = json.load(f)
        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        gdf = gdf.rename(columns={"shapeName": "Province"})
        gdf.set_crs(epsg=4326, inplace=True)
        gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01)
        province_options = [{'label': prov, 'value': prov} for prov in sorted(gdf['Province'].unique())]
        province_data = gdf.to_json()

        points_gdf_full = gpd.read_file(poi_geojson_path)
        points_gdf_full.set_crs(epsg=4326, inplace=True)
        poi_data = points_gdf_full.to_json()

        return province_options, province_data, poi_data

    except Exception as e:
        print(f"Error loading initial data: {e}")
        return [], {}, {}

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
            marker_id = point['customdata']
            if marker_id not in current_clicked:
                return current_clicked + [marker_id]
    return current_clicked

# ---------------------------
# Callback: Update Map Based on Province Selection and Clicked Markers
# ---------------------------
@app.callback(
    Output('choropleth-map', 'figure'),
    Input('province-dropdown', 'value'),
    State('province-data', 'data'),
    State('poi-data', 'data'),
    State('clicked-markers', 'data')
)
def update_map(selected_provinces, province_data_json, poi_data_json, clicked_markers):
    if not province_data_json or not poi_data_json:
        return {
            'data': [],
            'layout': {
                'title': 'Data not loaded.',
                'margin': {"r": 0, "t": 0, "l": 0, "b": 0}
            }
        }

    gdf = gpd.read_file(json.dumps(province_data_json))
    points_gdf = gpd.read_file(json.dumps(poi_data_json))
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
    gdf["Notable Places"] = gdf["Province"].map(lambda prov: ", ".join(province_to_places[prov]))

    fig = px.choropleth_mapbox(
        gdf[gdf["Province"].isin(selected_provinces)] if selected_provinces else gdf,
        geojson={
            "type": "FeatureCollection",
            "features": [feat for feat in json.loads(province_data_json)['features']
                         if not selected_provinces or feat['properties']['shapeName'] in selected_provinces]
        },
        locations='Province',
        featureidkey="properties.shapeName",
        color_discrete_sequence=["blue"] if selected_provinces else ["lightgray"],
        hover_data=["Province", "Notable Places"],
        mapbox_style="carto-positron",
        zoom=2,
        center={"lat": 56.130, "lon": -106.347},
        opacity=0.7 if selected_provinces else 0.5,
    )
    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})

    if selected_provinces:
        filtered_rows = []
        for prov in selected_provinces:
            province_poly = gdf[gdf["Province"] == prov].geometry.unary_union
            for place in province_to_places[prov]:
                matches = points_gdf[points_gdf["name"].str.contains(place, case=False, na=False)]
                for _, row in matches.iterrows():
                    if row.geometry.within(province_poly):
                        filtered_rows.append({
                            "Province": prov,
                            "Place": place,
                            "lat": row.geometry.y,
                            "lon": row.geometry.x
                        })
        marker_subset = pd.DataFrame(filtered_rows)
        if not marker_subset.empty:
            marker_subset["marker_id"] = marker_subset.apply(lambda row: f"{row['Province']}_{row['Place']}_{row.name}", axis=1)
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

    return fig

if __name__ == '__main__':
    app.run_server(debug=False)
