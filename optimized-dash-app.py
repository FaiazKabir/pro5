#!/usr/bin/env python
# coding: utf-8

import os
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import numpy as np

# ---------------------------
# Initialize Dash App
# ---------------------------
app = dash.Dash(__name__, suppress_callback_exceptions=True)
server = app.server  # Important for gunicorn deployment

# ---------------------------
# Create simplified Canadian provinces data without GeoJSON
# ---------------------------

# Define centroids for provinces and territories
province_centroids = {
    "Alberta": {"lat": 53.9333, "lon": -116.5765},
    "British Columbia": {"lat": 53.7267, "lon": -127.6476},
    "Manitoba": {"lat": 53.7609, "lon": -98.8139},
    "New Brunswick": {"lat": 46.5653, "lon": -66.4619},
    "Newfoundland and Labrador": {"lat": 53.1355, "lon": -57.6604},
    "Nova Scotia": {"lat": 45.1679, "lon": -62.6779},
    "Ontario": {"lat": 51.2538, "lon": -85.3232},
    "Prince Edward Island": {"lat": 46.5107, "lon": -63.4168},
    "Quebec": {"lat": 52.9399, "lon": -73.5491},
    "Saskatchewan": {"lat": 52.9399, "lon": -106.4509},
    "Northwest Territories": {"lat": 64.8255, "lon": -124.8457},
    "Nunavut": {"lat": 70.2998, "lon": -83.1076},
    "Yukon": {"lat": 64.2823, "lon": -135.0}
}

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

# Create a DataFrame from our province centroids
provinces_df = pd.DataFrame([
    {"Province": province, "lat": data["lat"], "lon": data["lon"], 
     "Notable Places": ", ".join(province_to_places.get(province, []))}
    for province, data in province_centroids.items()
])

# Create a predefined dataset of notable places with coordinates
notable_places_data = [
    {"Province": "Alberta", "Place": "Banff NP", "lat": 51.1784, "lon": -115.5708},
    {"Province": "Alberta", "Place": "Jasper NP", "lat": 52.8738, "lon": -117.9610},
    {"Province": "Alberta", "Place": "Calgary Tower", "lat": 51.0447, "lon": -114.0719},
    {"Province": "Alberta", "Place": "Lake Louise", "lat": 51.4254, "lon": -116.1773},
    {"Province": "Alberta", "Place": "West Edmonton Mall", "lat": 53.5225, "lon": -113.6242},
    {"Province": "British Columbia", "Place": "Stanley Park", "lat": 49.3017, "lon": -123.1417},
    {"Province": "British Columbia", "Place": "Butchart Gardens", "lat": 48.5636, "lon": -123.4683},
    {"Province": "British Columbia", "Place": "Whistler", "lat": 50.1163, "lon": -122.9574},
    {"Province": "British Columbia", "Place": "Capilano Bridge", "lat": 49.3431, "lon": -123.1139},
    {"Province": "British Columbia", "Place": "Pacific Rim NP", "lat": 49.0064, "lon": -125.6581},
    {"Province": "Manitoba", "Place": "The Forks", "lat": 49.8865, "lon": -97.1307},
    {"Province": "Manitoba", "Place": "Riding Mountain NP", "lat": 50.6625, "lon": -100.0333},
    {"Province": "Manitoba", "Place": "Assiniboine Zoo", "lat": 49.8731, "lon": -97.2461},
    {"Province": "Manitoba", "Place": "Museum for Human Rights", "lat": 49.8891, "lon": -97.1309},
    {"Province": "Manitoba", "Place": "FortWhyte Alive", "lat": 49.8274, "lon": -97.2398},
    {"Province": "New Brunswick", "Place": "Bay of Fundy", "lat": 45.2336, "lon": -66.1150},
    {"Province": "New Brunswick", "Place": "Hopewell Rocks", "lat": 45.8261, "lon": -64.5706},
    {"Province": "New Brunswick", "Place": "Fundy NP", "lat": 45.5960, "lon": -65.0018},
    {"Province": "New Brunswick", "Place": "Reversing Falls", "lat": 45.2502, "lon": -66.0864},
    {"Province": "New Brunswick", "Place": "Kings Landing", "lat": 45.9960, "lon": -66.9060},
    {"Province": "Newfoundland and Labrador", "Place": "Gros Morne NP", "lat": 49.6022, "lon": -57.7564},
    {"Province": "Newfoundland and Labrador", "Place": "Signal Hill", "lat": 47.5705, "lon": -52.6819},
    {"Province": "Newfoundland and Labrador", "Place": "L'Anse aux Meadows", "lat": 51.5965, "lon": -55.5308},
    {"Province": "Newfoundland and Labrador", "Place": "Cape Spear", "lat": 47.5227, "lon": -52.6173},
    {"Province": "Newfoundland and Labrador", "Place": "Bonavista", "lat": 48.6583, "lon": -53.1127},
    {"Province": "Nova Scotia", "Place": "Peggy's Cove", "lat": 44.4948, "lon": -63.9189},
    {"Province": "Nova Scotia", "Place": "Cabot Trail", "lat": 46.7371, "lon": -60.3508},
    {"Province": "Nova Scotia", "Place": "Halifax Citadel", "lat": 44.6478, "lon": -63.5816},
    {"Province": "Nova Scotia", "Place": "Lunenburg", "lat": 44.3777, "lon": -64.3092},
    {"Province": "Nova Scotia", "Place": "Kejimkujik NP", "lat": 44.3800, "lon": -65.2175},
    {"Province": "Ontario", "Place": "CN Tower", "lat": 43.6426, "lon": -79.3871},
    {"Province": "Ontario", "Place": "Niagara Falls", "lat": 43.0962, "lon": -79.0716},
    {"Province": "Ontario", "Place": "Algonquin Park", "lat": 45.8333, "lon": -78.5000},
    {"Province": "Ontario", "Place": "Parliament Hill", "lat": 45.4235, "lon": -75.7000},
    {"Province": "Ontario", "Place": "Royal Ontario Museum", "lat": 43.6677, "lon": -79.3948},
    {"Province": "Prince Edward Island", "Place": "Green Gables", "lat": 46.4911, "lon": -63.3838},
    {"Province": "Prince Edward Island", "Place": "Cavindish Beach", "lat": 46.5011, "lon": -63.4187},
    {"Province": "Prince Edward Island", "Place": "Confederation Trail", "lat": 46.3335, "lon": -63.3008},
    {"Province": "Prince Edward Island", "Place": "PEI NP", "lat": 46.4127, "lon": -63.0878},
    {"Province": "Prince Edward Island", "Place": "Point Prim Lighthouse", "lat": 46.0477, "lon": -62.9975},
    {"Province": "Quebec", "Place": "Old Quebec", "lat": 46.8139, "lon": -71.2082},
    {"Province": "Quebec", "Place": "Mont-Tremblant", "lat": 46.1184, "lon": -74.5958},
    {"Province": "Quebec", "Place": "Montmorency Falls", "lat": 46.8855, "lon": -71.1510},
    {"Province": "Quebec", "Place": "Quebec City", "lat": 46.8139, "lon": -71.2080},
    {"Province": "Quebec", "Place": "Sainte-Anne-de-Beaupré", "lat": 47.0226, "lon": -70.9370},
    {"Province": "Saskatchewan", "Place": "Forestry Zoo", "lat": 52.1316, "lon": -106.6702},
    {"Province": "Saskatchewan", "Place": "Wanuskewin", "lat": 52.2163, "lon": -106.5931},
    {"Province": "Saskatchewan", "Place": "Prince Albert NP", "lat": 53.9837, "lon": -106.0173},
    {"Province": "Saskatchewan", "Place": "Wascana Centre", "lat": 50.4364, "lon": -104.6171},
    {"Province": "Saskatchewan", "Place": "RCMP Heritage Centre", "lat": 50.4359, "lon": -104.6615},
    {"Province": "Northwest Territories", "Place": "Nahanni NP", "lat": 61.5833, "lon": -125.5833},
    {"Province": "Northwest Territories", "Place": "Great Slave Lake", "lat": 62.0955, "lon": -114.3858},
    {"Province": "Northwest Territories", "Place": "Virginia Falls", "lat": 61.6031, "lon": -125.7744},
    {"Province": "Northwest Territories", "Place": "Yellowknife", "lat": 62.4540, "lon": -114.3718},
    {"Province": "Northwest Territories", "Place": "Wood Buffalo NP", "lat": 59.4675, "lon": -112.2124},
    {"Province": "Nunavut", "Place": "Auyuittuq NP", "lat": 67.8333, "lon": -65.0000},
    {"Province": "Nunavut", "Place": "Sylvia Grinnell Park", "lat": 63.7430, "lon": -68.5571},
    {"Province": "Nunavut", "Place": "Qaummaarviit Park", "lat": 63.7942, "lon": -68.5532},
    {"Province": "Nunavut", "Place": "Iqaluit", "lat": 63.7467, "lon": -68.5170},
    {"Province": "Nunavut", "Place": "Sirmilik NP", "lat": 72.9962, "lon": -81.2503},
    {"Province": "Yukon", "Place": "Kluane NP", "lat": 60.7500, "lon": -139.5000},
    {"Province": "Yukon", "Place": "Miles Canyon", "lat": 60.6599, "lon": -135.0262},
    {"Province": "Yukon", "Place": "SS Klondike", "lat": 60.7230, "lon": -135.0456},
    {"Province": "Yukon", "Place": "Whitehorse", "lat": 60.7197, "lon": -135.0522},
    {"Province": "Yukon", "Place": "Tombstone Park", "lat": 64.5167, "lon": -138.2167}
]

# Create DataFrame from our predefined data
notable_df = pd.DataFrame(notable_places_data)

# Generate unique marker IDs
notable_df["marker_id"] = notable_df.apply(lambda row: f"{row['Province']}_{row['Place']}_{row.name}", axis=1)

# ---------------------------
# App Layout
# ---------------------------
app.layout = html.Div([
    html.H1("Interactive Canada Provinces Explorer", style={'textAlign': 'center', 'marginBottom': '20px'}),
    html.Div([
        html.Label("Select provinces to explore:"),
        dcc.Dropdown(
            id='province-dropdown',
            options=[{'label': prov, 'value': prov} for prov in sorted(provinces_df['Province'].unique())],
            multi=True,
            placeholder="Select provinces to highlight on map",
            style={'width': '100%'}
        ),
    ], style={'margin': '0 auto', 'width': '80%', 'marginBottom': '20px'}),
    html.Div(id='selection-info', 
             children="Select provinces above to see their notable places.", 
             style={'textAlign': 'center', 'marginBottom': '10px'}),
    html.Div([
        dcc.Graph(id='map', style={'height': '700px'})
    ], style={'margin': '0 auto', 'width': '90%'}),
    html.Div([
        html.H3("Points of Interest", style={'textAlign': 'center'}),
        html.Div(id='clicked-info', 
                 children="Click on markers to see more information.", 
                 style={'textAlign': 'center', 'marginBottom': '10px'}),
    ], style={'margin': '0 auto', 'width': '80%', 'marginTop': '20px'}),
    dcc.Store(id='clicked-markers', data=[])
])

# ---------------------------
# Callbacks
# ---------------------------
@app.callback(
    Output('selection-info', 'children'),
    Input('province-dropdown', 'value')
)
def update_selection_info(selected_provinces):
    """Update text showing what's currently selected"""
    if not selected_provinces or len(selected_provinces) == 0:
        return "Select provinces above to see their notable places."
    return f"Selected provinces: {', '.join(selected_provinces)}"

@app.callback(
    Output('clicked-markers', 'data'),
    Output('clicked-info', 'children'),
    Input('map', 'clickData'),
    State('clicked-markers', 'data')
)
def update_clicked_markers(clickData, current_clicked):
    if not current_clicked:
        current_clicked = []
        
    info_text = "Click on markers to see more information."
    
    if clickData and 'points' in clickData:
        point = clickData['points'][0]
        if 'customdata' in point:
            marker_id = point['customdata']
            place_name = point.get('text', '')
            
            if marker_id not in current_clicked:
                current_clicked.append(marker_id)
                info_text = f"Selected place: {place_name}"
            else:
                # Toggle off if clicked again
                current_clicked = [m for m in current_clicked if m != marker_id]
                info_text = f"Deselected place: {place_name}"
                
        elif 'text' in point:
            # Province was clicked
            province_name = point.get('text', '')
            info_text = f"Province: {province_name}"
            
    if current_clicked:
        # Get all place names for clicked markers
        clicked_places = []
        for marker_id in current_clicked:
            parts = marker_id.split('_')
            if len(parts) >= 2:
                place = parts[1]
                clicked_places.append(place)
        
        if clicked_places:
            info_text = f"Selected places: {', '.join(clicked_places)}"
    
    return current_clicked, info_text

@app.callback(
    Output('map', 'figure'),
    Input('province-dropdown', 'value'),
    Input('clicked-markers', 'data')
)
def update_map(selected_provinces, clicked_markers):
    # Handle None or empty selections
    if not selected_provinces:
        selected_provinces = []
    
    if not clicked_markers:
        clicked_markers = []
    
    # Create base map figure
    fig = go.Figure()
    
    # Add text labels for all provinces
    fig.add_trace(go.Scattermapbox(
        lat=provinces_df["lat"],
        lon=provinces_df["lon"],
        mode='text+markers',
        marker=dict(
            size=15, 
            color=['#3366cc' if p in selected_provinces else '#cccccc' for p in provinces_df['Province']],
            opacity=[0.8 if p in selected_provinces else 0.5 for p in provinces_df['Province']]
        ),
        text=provinces_df["Province"],
        textfont=dict(size=10, color='black'),
        hovertext=provinces_df["Notable Places"],
        hoverinfo='text',
        name='Provinces'
    ))
    
    # Add markers for notable places in selected provinces
    if selected_provinces:
        marker_subset = notable_df[notable_df["Province"].isin(selected_provinces)]
        if not marker_subset.empty:
            marker_colors = ["#33cc33" if marker_id in clicked_markers else "#ff3333"
                         for marker_id in marker_subset["marker_id"]]
            
            fig.add_trace(go.Scattermapbox(
                lat=marker_subset["lat"],
                lon=marker_subset["lon"],
                mode='markers',
                marker=dict(size=10, color=marker_colors),
                text=marker_subset["Place"],
                customdata=marker_subset["marker_id"],
                hoverinfo='text',
                name='Points of Interest'
            ))
    
    # Update map layout
    fig.update_layout(
        mapbox=dict(
            style="carto-positron",
            zoom=2,
            center={"lat": 56.130, "lon": -106.347},
        ),
        margin={"r": 0, "t": 0, "l": 0, "b": 0},
        showlegend=False,
        uirevision='constant'  # Preserves zoom/pan state on updates
    )
    
    return fig

# ---------------------------
# Run the server
# ---------------------------
if __name__ == '__main__':
    # Get port from environment variable or use 8080 as default
    port = int(os.environ.get('PORT', 8080))
    app.run_server(debug=False, host='0.0.0.0', port=port)
