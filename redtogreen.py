#!/usr/bin/env python
# coding: utf-8

# In[ ]:


#!/usr/bin/env python
import dash
from dash import dcc, html, Input, Output, State
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import zipfile

# Initialize Dash App
app = dash.Dash(__name__)
server = app.server

# ---------------------------
# Hardcoded coordinates (unchanged)
# ---------------------------
hardcoded_poi_coordinates = {
    "Alberta": [
        {"place": "Banff NP", "lat": 51.4968, "lon": -115.9281, "marker_id": "Alberta_Banff NP"},
        {"place": "Jasper NP", "lat": 52.8736, "lon": -117.9430, "marker_id": "Alberta_Jasper NP"},
        # ... (keep all your existing POI coordinates) ...
    ],
    # ... (keep all your other provinces) ...
}

app.layout = html.Div([
    html.H1("Canada Provinces with Notable Places"),
    dcc.Dropdown(
        id='province-dropdown',
        options=[],
        multi=True,
        placeholder="Select Provinces to highlight"
    ),
    dcc.Store(id='province-list'),
    dcc.Store(id='clicked-markers', data=[]),
    dcc.Graph(id='choropleth-map')
])

# ---------------------------
# Load province names
# ---------------------------
@app.callback(
    [Output('province-dropdown', 'options'),
     Output('province-list', 'data')],
    Input('province-dropdown', 'id')
)
def load_province_names(_):
    try:
        with zipfile.ZipFile('data.zip') as z:
            with z.open('geoBoundaries-CAN-ADM1_simplified.geojson') as f:
                geojson = json.load(f)
                provinces = sorted(feat['properties']['shapeName'] for feat in geojson['features'])
                return [{'label': p, 'value': p} for p in provinces], provinces
    except Exception as e:
        print(f"Error loading provinces: {e}")
        return [], []

# ---------------------------
# Optimized map update with all POIs
# ---------------------------
@app.callback(
    Output('choropleth-map', 'figure'),
    [Input('province-dropdown', 'value'),
     Input('clicked-markers', 'data')],
    State('province-list', 'data')
)
def update_map(selected_provinces, clicked_markers, all_provinces):
    try:
        # Initialize figure
        fig = go.Figure()
        
        # Load GeoJSON data
        with zipfile.ZipFile('data.zip') as z:
            with z.open('geoBoundaries-CAN-ADM1_simplified.geojson') as f:
                geojson = json.load(f)
                
                # Show all provinces in light gray if none selected
                if not selected_provinces:
                    fig.add_trace(go.Choroplethmapbox(
                        geojson=geojson,
                        locations=[f['properties']['shapeName'] for f in geojson['features']],
                        z=[1]*len(geojson['features']),
                        colorscale=[[0, 'lightgray'], [1, 'lightgray']],
                        marker_opacity=0.5,
                        featureidkey="properties.shapeName",
                        showscale=False
                    ))
                else:
                    # Show selected provinces in blue
                    filtered_features = [
                        feat for feat in geojson['features']
                        if feat['properties']['shapeName'] in selected_provinces
                    ]
                    fig.add_trace(go.Choroplethmapbox(
                        geojson={"type": "FeatureCollection", "features": filtered_features},
                        locations=[f['properties']['shapeName'] for f in filtered_features],
                        z=[1]*len(filtered_features),
                        colorscale=[[0, 'blue'], [1, 'blue']],
                        marker_opacity=0.7,
                        featureidkey="properties.shapeName",
                        showscale=False
                    ))
        
        # Add ALL POI markers (not just for selected provinces)
        for province, pois in hardcoded_poi_coordinates.items():
            # Only show markers for selected provinces if any are selected
            if not selected_provinces or province in selected_provinces:
                for poi in pois:
                    fig.add_trace(go.Scattermapbox(
                        lat=[poi['lat']],
                        lon=[poi['lon']],
                        mode='markers',
                        marker=dict(
                            size=10,
                            color='green' if poi['marker_id'] in clicked_markers else 'red'
                        ),
                        text=poi['place'],
                        customdata=[poi['marker_id']],
                        hoverinfo='text',
                        showlegend=False
                    ))
        
        # Update map layout
        fig.update_layout(
            mapbox_style="carto-positron",
            mapbox_zoom=2,
            mapbox_center={"lat": 56.130, "lon": -106.347},
            margin={"r":0, "t":0, "l":0, "b":0}
        )
        
        return fig
        
    except Exception as e:
        print(f"Map error: {e}")
        return go.Figure().update_layout(
            title="Error loading map",
            margin={"r":0, "t":0, "l":0, "b":0}
        )

# ---------------------------
# Click handler (unchanged)
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
            marker_id = point['customdata'][0]
            if marker_id not in current_clicked:
                return current_clicked + [marker_id]
    return current_clicked

if __name__ == '__main__':
    app.run_server(debug=True)
