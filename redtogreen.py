#!/usr/bin/env python
# coding: utf-8

# In[ ]:


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

# ---------------------------
# Memory Optimizations:
# 1. Load only necessary provinces
# 2. Use simpler data structures
# 3. Avoid geopandas (use raw GeoJSON)
# 4. Simplify geometries upfront
# ---------------------------

# Hardcoded coordinates (unchanged)
hardcoded_poi_coordinates = {
    # ... (keep your existing coordinate dictionary) ...
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
    dcc.Store(id='province-list'),
    dcc.Store(id='clicked-markers', data=[]),
    dcc.Graph(id='choropleth-map')
])

# ---------------------------
# Load province names (memory efficient)
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
# Optimized map update
# ---------------------------
@app.callback(
    Output('choropleth-map', 'figure'),
    [Input('province-dropdown', 'value'),
     Input('clicked-markers', 'data')],
    State('province-list', 'data')
)
def update_map(selected_provinces, clicked_markers, all_provinces):
    try:
        # Base map with all provinces (light gray)
        if not selected_provinces:
            return px.choropleth_mapbox(
                pd.DataFrame({'Province': all_provinces}),
                geojson=get_geojson(),
                locations='Province',
                featureidkey="properties.shapeName",
                color_discrete_sequence=["lightgray"],
                mapbox_style="carto-positron",
                zoom=2,
                center={"lat": 56.130, "lon": -106.347},
                opacity=0.5
            ).update_layout(margin={"r":0, "t":0, "l":0, "b":0})

        # Load only selected provinces
        with zipfile.ZipFile('data.zip') as z:
            with z.open('geoBoundaries-CAN-ADM1_simplified.geojson') as f:
                geojson = json.load(f)
                filtered_features = [
                    feat for feat in geojson['features']
                    if feat['properties']['shapeName'] in selected_provinces
                ]

        fig = px.choropleth_mapbox(
            pd.DataFrame({'Province': selected_provinces}),
            geojson={"type": "FeatureCollection", "features": filtered_features},
            locations='Province',
            featureidkey="properties.shapeName",
            color_discrete_sequence=["blue"],
            mapbox_style="carto-positron",
            zoom=2,
            center={"lat": 56.130, "lon": -106.347},
            opacity=0.7
        )

        # Add markers efficiently
        for province in selected_provinces:
            for poi in hardcoded_poi_coordinates.get(province, []):
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
                    hoverinfo='text'
                ))

        return fig.update_layout(margin={"r":0, "t":0, "l":0, "b":0})

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
