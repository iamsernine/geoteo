"""
AirWatch Enhanced - Complete Mobile-Style App
With WeatherAPI, Advanced Insights, and All Enhancements
"""

import dash
from dash import dcc, html, Input, Output, State, callback, ctx, ALL
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger
import sys
import json

# Import backend modules
from backend.api_client import OpenAQClient
from backend.data_processor import DataProcessor
from backend.cache_manager import CacheManager
from backend.weather_client import WeatherAPIClient
from backend.ml_predictor import MLPredictor
from backend.report_generator import ReportGenerator
import config

# Configure logging
logger.remove()
logger.add(sys.stderr, level=config.LOG_LEVEL)
logger.add(config.LOG_FILE, rotation="10 MB", retention="7 days", level=config.LOG_LEVEL)

# Initialize backend
api_client = OpenAQClient()
data_processor = DataProcessor()
cache_manager = CacheManager()
weather_client = WeatherAPIClient()
ml_predictor = MLPredictor()
report_gen = ReportGenerator()

# Initialize Dash app
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        dbc.icons.FONT_AWESOME,
        "https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap"
    ],
    meta_tags=[
        {"name": "viewport", "content": "width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no"}
    ],
    title="AirWatch - Smart Air Quality Monitor",
    suppress_callback_exceptions=True
)

server = app.server

# App layout with mobile-style design
app.layout = dbc.Container([
    # Top App Bar
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-wind", style={"fontSize": "24px", "color": "#1976d2"}),
                    html.Span("AirWatch", style={"fontSize": "20px", "fontWeight": "600", "marginLeft": "12px", "color": "#1976d2"})
                ], style={"display": "flex", "alignItems": "center"})
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Button(html.I(className="fas fa-search"), id="search-btn", color="light", size="sm", className="me-2", style={"borderRadius": "50%", "width": "40px", "height": "40px"}),
                    dbc.Button(html.I(className="fas fa-sync-alt"), id="refresh-btn", color="light", size="sm", className="me-2", style={"borderRadius": "50%", "width": "40px", "height": "40px"}),
                    dbc.Button(html.I(className="fas fa-moon", id="theme-icon"), id="theme-toggle", color="light", size="sm", style={"borderRadius": "50%", "width": "40px", "height": "40px"})
                ], style={"display": "flex", "justifyContent": "flex-end"})
            ], width=6)
        ])
    ], id="top-bar", style={"backgroundColor": "white", "padding": "16px 20px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)", "position": "sticky", "top": "0", "zIndex": "1000", "marginBottom": "16px"}),
    
    # Search Modal
    dbc.Modal([
        dbc.ModalHeader("Search Location"),
        dbc.ModalBody([
            dbc.Input(id="search-input", placeholder="Search city, country...", type="text", className="mb-3"),
            html.Div(id="search-results")
        ])
    ], id="search-modal", size="lg"),
    
    # Hero Card
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.H2(id="current-location", children="Global", style={"fontSize": "28px", "fontWeight": "600", "marginBottom": "4px"}),
                    html.P(id="current-time", children=datetime.now().strftime("%A, %B %d"), style={"color": "rgba(255,255,255,0.8)", "marginBottom": "20px"})
                ], width=12),
            ]),
            dbc.Row([
                dbc.Col([
                    html.H1(id="main-aqi", children="--", style={"fontSize": "72px", "fontWeight": "700", "marginBottom": "0", "lineHeight": "1"}),
                    html.P("Air Quality Index", style={"fontSize": "14px", "color": "rgba(255,255,255,0.8)", "marginTop": "8px"}),
                    html.Div(id="aqi-status-badge", style={"marginTop": "16px"})
                ], width=6),
                dbc.Col([
                    html.Div(id="weather-info")
                ], width=6)
            ])
        ])
    ], className="mb-3", style={"background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", "color": "white", "borderRadius": "16px", "boxShadow": "0 4px 20px rgba(102, 126, 234, 0.4)"}),
    
    # Quick Stats
    dbc.Row([
        dbc.Col([dbc.Card([dbc.CardBody([html.I(className="fas fa-map-marker-alt", style={"fontSize": "24px", "color": "#1976d2"}), html.H3(id="stat-stations", children="0", style={"fontSize": "28px", "fontWeight": "700", "margin": "8px 0"}), html.P("Stations", style={"fontSize": "12px", "color": "#666", "marginBottom": "0"})], style={"textAlign": "center"})], style={"borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})], width=3, xs=6, className="mb-3"),
        dbc.Col([dbc.Card([dbc.CardBody([html.I(className="fas fa-globe", style={"fontSize": "24px", "color": "#4caf50"}), html.H3(id="stat-countries", children="0", style={"fontSize": "28px", "fontWeight": "700", "margin": "8px 0"}), html.P("Countries", style={"fontSize": "12px", "color": "#666", "marginBottom": "0"})], style={"textAlign": "center"})], style={"borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})], width=3, xs=6, className="mb-3"),
        dbc.Col([dbc.Card([dbc.CardBody([html.I(className="fas fa-wind", style={"fontSize": "24px", "color": "#ff9800"}), html.H3(id="stat-wind", children="--", style={"fontSize": "28px", "fontWeight": "700", "margin": "8px 0"}), html.P("Wind km/h", style={"fontSize": "12px", "color": "#666", "marginBottom": "0"})], style={"textAlign": "center"})], style={"borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})], width=3, xs=6, className="mb-3"),
        dbc.Col([dbc.Card([dbc.CardBody([html.I(className="fas fa-tint", style={"fontSize": "24px", "color": "#2196f3"}), html.H3(id="stat-humidity", children="--", style={"fontSize": "28px", "fontWeight": "700", "margin": "8px 0"}), html.P("Humidity %", style={"fontSize": "12px", "color": "#666", "marginBottom": "0"})], style={"textAlign": "center"})], style={"borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})], width=3, xs=6, className="mb-3")
    ]),
    
    # Map Card
    dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([html.H5("Air Quality Map", style={"marginBottom": "0", "fontWeight": "600"})], width=6),
                dbc.Col([dbc.ButtonGroup([dbc.Button("Heatmap", id="btn-heatmap", size="sm", outline=True, color="primary"), dbc.Button("Markers", id="btn-markers", size="sm", color="primary"), dbc.Button("Density", id="btn-density", size="sm", outline=True, color="primary")])], width=6, style={"textAlign": "right"})
            ])
        ]),
        dbc.CardBody([dcc.Loading(id="loading-map", type="circle", children=[dcc.Graph(id="main-map", style={"height": "400px"}, config={"displayModeBar": False, "scrollZoom": True})])], style={"padding": "0"})
    ], className="mb-3", style={"borderRadius": "12px", "overflow": "hidden", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
    
    # Tabs
    dbc.Card([
        dbc.CardHeader([
            dbc.Tabs(id="main-tabs", active_tab="insights", children=[
                dbc.Tab(label=html.Div([html.I(className="fas fa-lightbulb me-2"), "Insights"]), tab_id="insights"),
                dbc.Tab(label=html.Div([html.I(className="fas fa-chart-line me-2"), "Trends"]), tab_id="trends"),
                dbc.Tab(label=html.Div([html.I(className="fas fa-balance-scale me-2"), "Compare"]), tab_id="compare"),
                dbc.Tab(label=html.Div([html.I(className="fas fa-download me-2"), "Export"]), tab_id="export")
            ])
        ]),
        dbc.CardBody([html.Div(id="tab-content")])
    ], className="mb-5", style={"borderRadius": "12px", "overflow": "hidden", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
    
    # Hidden stores
    dcc.Store(id="locations-data"),
    dcc.Store(id="weather-data"),
    dcc.Store(id="map-type-store", data="markers"),
    dcc.Store(id="theme-store", data="light"),
    dcc.Interval(id="interval-component", interval=300000, n_intervals=0)
    
], fluid=True, style={"paddingBottom": "30px", "fontFamily": "'Inter', sans-serif", "backgroundColor": "#f5f5f5"}, className="px-3 py-0")


# Callbacks
@callback(
    [Output("locations-data", "data"), Output("stat-stations", "children"), Output("stat-countries", "children")],
    [Input("interval-component", "n_intervals"), Input("refresh-btn", "n_clicks")]
)
def update_data(n, clicks):
    logger.info("Fetching data...")
    cache_key = "locations:all"
    cached = cache_manager.get(cache_key)
    if cached and clicks is None:
        locations = cached
    else:
        locations = api_client.get_locations(limit=500)
        cache_manager.set(cache_key, locations, timeout=300)
    
    processed = [data_processor.process_location_data(loc) for loc in locations]
    countries = len(set(loc.get("country_code") for loc in processed if loc.get("country_code")))
    return processed, str(len(processed)), str(countries)


@callback(
    Output("main-map", "figure"),
    [Input("locations-data", "data"), Input("map-type-store", "data")]
)
def update_map(data, map_type):
    if not data:
        return go.Figure()
    
    df = pd.DataFrame(data)
    df["lat"] = df["coordinates"].apply(lambda x: x.get("latitude") if x else None)
    df["lon"] = df["coordinates"].apply(lambda x: x.get("longitude") if x else None)
    df = df.dropna(subset=["lat", "lon"])
    
    aqi_colors = [[0, "rgb(0,228,0)"], [0.17, "rgb(255,255,0)"], [0.33, "rgb(255,126,0)"], [0.5, "rgb(255,0,0)"], [0.67, "rgb(143,63,151)"], [1, "rgb(126,0,35)"]]
    
    if map_type == "heatmap":
        fig = go.Figure(go.Densitymapbox(lon=df["lon"], lat=df["lat"], z=df["max_aqi"], radius=25, colorscale=aqi_colors, zmin=0, zmax=300, colorbar=dict(title="AQI")))
        fig.update_layout(mapbox=dict(style="open-street-map", center=dict(lat=20, lon=0), zoom=1.5), height=400, margin=dict(l=0,r=0,t=0,b=0))
    elif map_type == "density":
        fig = px.density_mapbox(df, lat="lat", lon="lon", z="max_aqi", radius=20, center=dict(lat=20, lon=0), zoom=1.5, mapbox_style="open-street-map", color_continuous_scale=aqi_colors, range_color=[0,300], height=400)
        fig.update_layout(margin=dict(l=0,r=0,t=0,b=0))
    else:
        fig = go.Figure(go.Scattermapbox(lon=df["lon"], lat=df["lat"], mode="markers", marker=dict(size=10, color=df["max_aqi"], colorscale=aqi_colors, cmin=0, cmax=300, colorbar=dict(title="AQI"), opacity=0.8), text=df.apply(lambda r: f"<b>{r['name']}</b><br>AQI: {r['max_aqi']}", axis=1), hovertemplate="%{text}<extra></extra>"))
        fig.update_layout(mapbox=dict(style="open-street-map", center=dict(lat=20, lon=0), zoom=1.5), height=400, margin=dict(l=0,r=0,t=0,b=0))
    
    return fig


@callback(
    [Output("main-aqi", "children"), Output("aqi-status-badge", "children")],
    Input("locations-data", "data")
)
def update_aqi(data):
    if not data:
        return "--", ""
    df = pd.DataFrame(data)
    avg_aqi = int(df["max_aqi"].mean())
    category = data_processor.get_aqi_category(avg_aqi)
    color = data_processor.get_aqi_color(avg_aqi)
    badge = dbc.Badge(category, color="light", style={"backgroundColor": color, "padding": "8px 16px", "fontSize": "14px"})
    return str(avg_aqi), badge


@callback(
    [Output("weather-info", "children"), Output("stat-wind", "children"), Output("stat-humidity", "children")],
    Input("locations-data", "data")
)
def update_weather(data):
    if not data or not config.WEATHER_API_KEY:
        return "", "--", "--"
    
    # Get weather for first location as example
    loc = data[0]
    coords = loc.get("coordinates", {})
    lat, lon = coords.get("latitude"), coords.get("longitude")
    
    if not lat or not lon:
        return "", "--", "--"
    
    weather = weather_client.get_current_weather(lat, lon)
    if not weather:
        return "", "--", "--"
    
    weather_div = html.Div([
        html.Div([
            html.I(className="fas fa-temperature-high me-2"),
            html.Span(f"{weather.get('temperature_c', '--')}°C")
        ], style={"marginBottom": "8px"}),
        html.Div([
            html.I(className="fas fa-wind me-2"),
            html.Span(f"{weather.get('wind_speed_kph', '--')} km/h {weather.get('wind_direction', '')}")
        ], style={"marginBottom": "8px"}),
        html.Div([
            html.I(className="fas fa-tint me-2"),
            html.Span(f"{weather.get('humidity', '--')}%")
        ])
    ], style={"fontSize": "14px"})
    
    return weather_div, str(weather.get('wind_speed_kph', '--')), f"{weather.get('humidity', '--')}%"


@callback(
    Output("map-type-store", "data"),
    [Input("btn-heatmap", "n_clicks"), Input("btn-markers", "n_clicks"), Input("btn-density", "n_clicks")],
    prevent_initial_call=True
)
def change_map_type(h, m, d):
    triggered = ctx.triggered_id
    if triggered == "btn-heatmap":
        return "heatmap"
    elif triggered == "btn-density":
        return "density"
    return "markers"


@callback(
    Output("tab-content", "children"),
    [Input("main-tabs", "active_tab"), Input("locations-data", "data")]
)
def render_tab(tab, data):
    if not data:
        return html.Div("Loading...", className="text-center py-5")
    
    df = pd.DataFrame(data)
    
    if tab == "insights":
        top10 = df.nlargest(10, "max_aqi")
        fig = px.bar(top10, x="name", y="max_aqi", color="max_aqi", color_continuous_scale="RdYlGn_r", title="Top 10 Most Polluted Locations")
        
        insights = [
            {"icon": "fas fa-exclamation-triangle", "title": "High Pollution Alert", "text": f"{len(df[df['max_aqi'] > 150])} locations with unhealthy air quality", "color": "#ff5252"},
            {"icon": "fas fa-check-circle", "title": "Good Air Quality", "text": f"{len(df[df['max_aqi'] <= 50])} locations with good air quality", "color": "#4caf50"},
            {"icon": "fas fa-chart-line", "title": "Average AQI", "text": f"Global average: {int(df['max_aqi'].mean())}", "color": "#2196f3"}
        ]
        
        insight_cards = [
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className=i["icon"], style={"fontSize": "32px", "color": i["color"]}),
                        html.H5(i["title"], className="mt-3"),
                        html.P(i["text"], style={"color": "#666"})
                    ], style={"textAlign": "center"})
                ])
            ], className="mb-3")
            for i in insights
        ]
        
        return html.Div([dcc.Graph(figure=fig)] + insight_cards)
    
    elif tab == "trends":
        return html.Div([
            html.H5("Air Quality Trends", className="mb-3"),
            html.P("Historical data and ML predictions coming soon...")
        ])
    
    elif tab == "compare":
        return html.Div([
            html.H5("City Comparison", className="mb-3"),
            html.P("Select multiple cities to compare their air quality metrics.")
        ])
    
    elif tab == "export":
        return html.Div([
            html.H5("Export Data", className="mb-3"),
            dbc.Button([html.I(className="fas fa-file-pdf me-2"), "Download PDF Report"], color="primary", className="mb-2 w-100"),
            dbc.Button([html.I(className="fas fa-file-excel me-2"), "Export to Excel"], color="success", className="mb-2 w-100"),
            dbc.Button([html.I(className="fas fa-file-csv me-2"), "Export to CSV"], color="info", className="w-100")
        ])
    
    return html.Div("Select a tab")


@callback(
    Output("search-modal", "is_open"),
    Input("search-btn", "n_clicks"),
    State("search-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_search(n, is_open):
    return not is_open


if __name__ == "__main__":
    app.run_server(debug=config.FLASK_DEBUG, host=config.HOST, port=config.PORT)
