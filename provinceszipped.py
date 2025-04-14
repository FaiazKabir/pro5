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
# Unzip GeoJSON files
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

# Specify the zip file path and extract
geojson_zip = 'data.zip'  # Update this to your zip file path
unzipped = unzip_geojsons(geojson_zip)

# Initialize global data variables to None
gdf = None
geojson_data = None
points_gdf = None
notable_df = None
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

if unzipped:
    # ---------------------------
    # Load and Prepare Data (Simplified GeoJSON)
    # ---------------------------
    province_geojson_path = 'geoBoundaries-CAN-ADM1_simplified.geojson'
    try:
        with open(province_geojson_path) as f:
            geojson_data = json.load(f)

        gdf = gpd.GeoDataFrame.from_features(geojson_data['features'])
        gdf = gdf.rename(columns={"shapeName": "Province"})
        gdf.set_crs(epsg=4326, inplace=True)

        # Simplify geometries (adjust tolerance as needed)
        gdf['geometry'] = gdf['geometry'].simplify(tolerance=0.01)

        # For hover info, add a comma-separated string of notable places to gdf
        gdf["Notable Places"] = gdf["Province"].map(lambda prov: ", ".join(province_to_places[prov]))

        # Load points-of-interest geoJSON as a GeoDataFrame
        poi_geojson_path = "hotosm_can_points_of_interest_points_geojson.geojson"
        points_gdf = gpd.read_file(poi_geojson_path)
        points_gdf.set_crs(epsg=4326, inplace=True)
        points_gdf = points_gdf.to_crs(gdf.crs)

        # Precompute a DataFrame of only those POIs that match the notable places AND lie within the province boundary.
        filtered_rows = []
        for prov, places in province_to_places.items():
            province_poly = gdf[gdf["Province"] == prov].geometry.unary_union
            for place in places:
                matches = points_gdf[points_gdf["name"].str.contains(place, case=False, na=False)]
                for _, row in matches.iterrows():
                    if row.geometry.within(province_poly):
                        filtered_rows.append({
                            "Province": prov,
                            "Place": place,
                            "lat": row.geometry.y,
                            "lon": row.geometry.x
                        })

        notable_df = pd.DataFrame(filtered_rows)
        notable_df["marker_id"] = notable_df.apply(lambda row: f"{row['Province']}_{row['Place']}_{row.name}", axis=1)

        print("Data loaded and prepared successfully.")

    except FileNotFoundError as e:
        print(f"Error loading GeoJSON file: {e}")
        gdf = pd.DataFrame() # Create empty dataframes to avoid errors later
        geojson_data = {}
        points_gdf = pd.DataFrame()
        notable_df = pd.DataFrame()
    except Exception as e:
        print(f"An error occurred during data loading/preparation: {e}")
        gdf = pd.DataFrame()
        geojson_data = {}
        points_gdf = pd.DataFrame()
        notable_df = pd.DataFrame()

# ---------------------------
# Initialize Dash App
# ---------------------------
app = dash.Dash(__name__)
server = app.server # This MUST be defined for Gunicorn

app.layout = html.Div([
    html.H1("Canada Provinces with Notable Places"),
    dcc.Dropdown(
        id='province-dropdown',
        options=[{'label': prov, 'value': prov} for prov in sorted(gdf['Province'].unique()) if 'Province' in gdf.columns],
        multi=True,
        placeholder="Select Provinces to highlight"
    ),
    dcc.Store(id='clicked-markers', data=[]),
    dcc.Graph(id='choropleth-map')
])

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
    Input('clicked-markers', 'data')
)
def update_map(selected_provinces, clicked_markers):
    if gdf is None or geojson_data is None or notable_df is None:
        return {
            'data': [],
            'layout': {
                'title': 'Error loading data. Please check logs.',
                'margin': {"r": 0, "t": 0, "l": 0, "b": 0}
            }
        }

    if not selected_provinces:
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
        fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
        return fig

    filtered_gdf = gdf[gdf["Province"].isin(selected_provinces)]
    filtered_geojson = {
        "type": "FeatureCollection",
        "features": [feat for feat in geojson_data['features']
                     if feat['properties']['shapeName'] in selected_provinces]
    }
    fig = px.choropleth_mapbox(
        filtered_gdf,
        geojson=filtered_geojson,
        locations='Province',
        featureidkey="properties.shapeName",
        color_discrete_sequence=["blue"],
        hover_data=["Province", "Notable Places"],
        mapbox_style="carto-positron",
        zoom=2,
        center={"lat": 56.130, "lon": -106.347},
        opacity=0.7,
    )

    marker_subset = notable_df[notable_df["Province"].isin(selected_provinces)]
    marker_colors = ["green" if marker_id in clicked_markers else "red"
                     for marker_id in marker_subset["marker_id"]]

    if not marker_subset.empty:
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

if __name__ == '__main__':
    app.run_server(debug=False) # Ensure debug is False for production
