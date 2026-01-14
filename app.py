"""
GeoTEO - Geospatial & Meteorological Dashboard
Complete app with smart reports for every city showing weather and air quality information
"""

import dash
from dash import dcc, html, Input, Output, State, callback, ctx, ALL, no_update
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from loguru import logger
import sys
import json
import base64
from pathlib import Path

# Import backend modules
from backend.api_client import OpenAQClient
from backend.data_processor import DataProcessor
from backend.cache_manager import CacheManager
from backend.weather_client import WeatherAPIClient
from backend.ml_predictor import AirQualityPredictor
from backend.report_generator import ReportGenerator
from backend.database import Database
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
ml_predictor = AirQualityPredictor()
report_gen = ReportGenerator()
db = Database()

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
    title="GeoTEO - Geospatial & Meteorological Dashboard",
    suppress_callback_exceptions=True
)

# Add global dark theme CSS
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                background-color: #1e1e1e !important;
                color: #cccccc !important;
            }
            .card {
                background-color: #2d2d30 !important;
                border: 1px solid #3e3e42 !important;
                border-radius: 0 !important;
                color: #cccccc !important;
            }
            .card-header {
                background-color: #252526 !important;
                border-bottom: 1px solid #3e3e42 !important;
                color: #cccccc !important;
            }
            .card-body {
                background-color: #2d2d30 !important;
                color: #cccccc !important;
            }
            .nav-link {
                color: #cccccc !important;
                border-radius: 0 !important;
            }
            .nav-link:hover {
                background-color: #2a2d2e !important;
                color: #ffffff !important;
            }
            .nav-link.active {
                background-color: #094771 !important;
                color: #ffffff !important;
            }
            .form-label {
                color: #cccccc !important;
            }
            .text-muted {
                color: #858585 !important;
            }
            .btn-primary {
                background-color: #007acc !important;
                border-color: #007acc !important;
                border-radius: 0 !important;
            }
            .btn-primary:hover {
                background-color: #005a9e !important;
                border-color: #005a9e !important;
            }
            .btn-dark {
                background-color: #2d2d30 !important;
                border-color: #3e3e42 !important;
                color: #cccccc !important;
                border-radius: 0 !important;
            }
            .btn-dark:hover {
                background-color: #3e3e42 !important;
            }
            .form-control, .form-select {
                background-color: #1e1e1e !important;
                border: 1px solid #3e3e42 !important;
                color: #cccccc !important;
                border-radius: 0 !important;
            }
            .form-control:focus, .form-select:focus {
                background-color: #1e1e1e !important;
                border-color: #007acc !important;
                color: #cccccc !important;
            }
            .badge {
                border-radius: 0 !important;
            }
            .modal-content {
                background-color: #252526 !important;
                border: 1px solid #3e3e42 !important;
                border-radius: 0 !important;
            }
            .modal-header {
                border-bottom: 1px solid #3e3e42 !important;
                color: #cccccc !important;
            }
            .modal-body {
                background-color: #252526 !important;
                color: #cccccc !important;
            }
            .tab-content {
                background-color: #2d2d30 !important;
                color: #cccccc !important;
            }
            .nav-tabs .nav-link {
                border-radius: 0 !important;
                border: 1px solid #3e3e42 !important;
                background-color: #2d2d30 !important;
                color: #cccccc !important;
            }
            .nav-tabs .nav-link.active {
                background-color: #1e1e1e !important;
                border-bottom-color: #1e1e1e !important;
                color: #007acc !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

server = app.server

# App layout with sidebar navigation
app.layout = html.Div([
    # Sidebar Navigation
    html.Div([
        # Logo/Header
        html.Div([
            html.I(className="fas fa-wind", style={"fontSize": "28px", "color": "#007acc"}),
            html.Span("GeoTEO", style={"fontSize": "22px", "fontWeight": "700", "marginLeft": "12px", "color": "#cccccc"})
        ], style={"padding": "20px", "borderBottom": "1px solid #3e3e42", "display": "flex", "alignItems": "center"}),
        
        # Navigation Menu
        html.Div([
            dbc.Nav([
                dbc.NavLink([
                    html.I(className="fas fa-map", style={"marginRight": "12px", "width": "20px"}),
                    "Map View"
                ], id="nav-map", href="#", active=True, className="nav-link-custom"),
                dbc.NavLink([
                    html.I(className="fas fa-chart-bar", style={"marginRight": "12px", "width": "20px"}),
                    "Analytics"
                ], id="nav-analytics", href="#", className="nav-link-custom"),
                dbc.NavLink([
                    html.I(className="fas fa-star", style={"marginRight": "12px", "width": "20px"}),
                    "Favorites"
                ], id="nav-favorites", href="#", className="nav-link-custom"),
                dbc.NavLink([
                    html.I(className="fas fa-history", style={"marginRight": "12px", "width": "20px"}),
                    "History"
                ], id="nav-history", href="#", className="nav-link-custom"),
                dbc.NavLink([
                    html.I(className="fas fa-cog", style={"marginRight": "12px", "width": "20px"}),
                    "Settings"
                ], id="nav-settings", href="#", className="nav-link-custom"),
            ], vertical=True, pills=True, className="flex-column")
        ], style={"padding": "10px", "flex": "1"}),
        
        # Sidebar Footer
        html.Div([
            dbc.Button([
                html.I(className="fas fa-sync-alt", style={"marginRight": "8px"}),
                "Refresh"
            ], id="sidebar-refresh-btn", color="primary", size="sm", className="w-100")
        ], style={"padding": "20px", "borderTop": "1px solid #3e3e42"})
    ], id="sidebar", style={
        "width": "250px",
        "height": "100vh",
        "backgroundColor": "#252526",
        "boxShadow": "2px 0 8px rgba(0,0,0,0.3)",
        "position": "fixed",
        "left": "0",
        "top": "0",
        "display": "flex",
        "flexDirection": "column",
        "zIndex": "1000",
        "overflowY": "auto",
        "color": "#cccccc"
    }),
    
    # Main Content Area
    html.Div([
        # Top Bar
        html.Div([
            dbc.Row([
                dbc.Col([
                    html.Span(id="page-title", children="Map View", style={"fontSize": "20px", "fontWeight": "600", "color": "#cccccc"})
                ], width=6),
                dbc.Col([
                    html.Div([
                        dbc.Button(html.I(className="fas fa-search"), id="search-btn", color="dark", size="sm", className="me-2", style={"width": "40px", "height": "40px", "backgroundColor": "#2d2d30", "border": "1px solid #3e3e42", "color": "#cccccc"}),
                        dbc.Button(html.I(className="fas fa-sync-alt"), id="refresh-btn", color="dark", size="sm", className="me-2", style={"width": "40px", "height": "40px", "backgroundColor": "#2d2d30", "border": "1px solid #3e3e42", "color": "#cccccc"}),
                    ], style={"display": "flex", "justifyContent": "flex-end"})
                ], width=6)
            ])
        ], style={"backgroundColor": "#1e1e1e", "padding": "16px 20px", "boxShadow": "0 2px 8px rgba(0,0,0,0.3)", "marginBottom": "16px", "width": "100%", "borderBottom": "1px solid #3e3e42"}),
        
        # Search Modal
        dbc.Modal([
            dbc.ModalHeader("Search Location"),
            dbc.ModalBody([
                dbc.Input(id="search-input", placeholder="Search city, country...", type="text", className="mb-3", debounce=True),
                html.Div(id="search-results")
            ])
        ], id="search-modal", size="lg", is_open=False),
        
        # Marker Action Modal - Enhanced for GeoTEO (Geospatial + Meteo)
        dbc.Modal([
            dbc.ModalHeader(id="marker-modal-header", children="Location Details"),
            dbc.ModalBody(id="marker-modal-body"),
            dbc.ModalFooter([
                dbc.Button([
                    html.I(className="fas fa-file-pdf me-2"),
                    "Generate Smart Report"
                ], id="marker-generate-report-btn", color="info", className="me-2"),
                dbc.Button("Add to Favorites", id="marker-add-favorite-btn", color="success", className="me-2"),
                dbc.Button("View on Map", id="marker-view-map-btn", color="primary", className="me-2"),
                dbc.Button("Close", id="marker-close-btn", color="secondary", outline=True)
            ])
        ], id="marker-action-modal", is_open=False, size="lg"),
        
        # Main Content Container (switches between views)
        html.Div([
            # Map View (default, always in layout for callbacks)
            html.Div(id="map-view", style={"width": "100%", "maxWidth": "100%", "boxSizing": "border-box"}, children=[
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
                ], className="mb-3", style={"background": "#2d2d30", "color": "#cccccc", "border": "1px solid #3e3e42", "boxShadow": "0 2px 8px rgba(0,0,0,0.3)"}),
                
                # Quick Stats
                dbc.Row([
                    dbc.Col([dbc.Card([dbc.CardBody([html.I(className="fas fa-map-marker-alt", style={"fontSize": "24px", "color": "#007acc"}), html.H3(id="stat-stations", children="0", style={"fontSize": "28px", "fontWeight": "700", "margin": "8px 0", "color": "#cccccc"}), html.P("Stations", style={"fontSize": "12px", "color": "#858585", "marginBottom": "0"})], style={"textAlign": "center", "backgroundColor": "#2d2d30"})], style={"border": "1px solid #3e3e42", "boxShadow": "0 2px 8px rgba(0,0,0,0.3)", "backgroundColor": "#2d2d30"})], width=3, xs=6, className="mb-3"),
                    dbc.Col([dbc.Card([dbc.CardBody([html.I(className="fas fa-globe", style={"fontSize": "24px", "color": "#007acc"}), html.H3(id="stat-countries", children="0", style={"fontSize": "28px", "fontWeight": "700", "margin": "8px 0", "color": "#cccccc"}), html.P("Countries", style={"fontSize": "12px", "color": "#858585", "marginBottom": "0"})], style={"textAlign": "center", "backgroundColor": "#2d2d30"})], style={"border": "1px solid #3e3e42", "boxShadow": "0 2px 8px rgba(0,0,0,0.3)", "backgroundColor": "#2d2d30"})], width=3, xs=6, className="mb-3"),
                    dbc.Col([dbc.Card([dbc.CardBody([html.I(className="fas fa-wind", style={"fontSize": "24px", "color": "#007acc"}), html.H3(id="stat-wind", children="--", style={"fontSize": "28px", "fontWeight": "700", "margin": "8px 0", "color": "#cccccc"}), html.P("Wind km/h", style={"fontSize": "12px", "color": "#858585", "marginBottom": "0"})], style={"textAlign": "center", "backgroundColor": "#2d2d30"})], style={"border": "1px solid #3e3e42", "boxShadow": "0 2px 8px rgba(0,0,0,0.3)", "backgroundColor": "#2d2d30"})], width=3, xs=6, className="mb-3"),
                    dbc.Col([dbc.Card([dbc.CardBody([html.I(className="fas fa-tint", style={"fontSize": "24px", "color": "#007acc"}), html.H3(id="stat-humidity", children="--", style={"fontSize": "28px", "fontWeight": "700", "margin": "8px 0", "color": "#cccccc"}), html.P("Humidity %", style={"fontSize": "12px", "color": "#858585", "marginBottom": "0"})], style={"textAlign": "center", "backgroundColor": "#2d2d30"})], style={"border": "1px solid #3e3e42", "boxShadow": "0 2px 8px rgba(0,0,0,0.3)", "backgroundColor": "#2d2d30"})], width=3, xs=6, className="mb-3")
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
                ], className="mb-3", style={"border": "1px solid #3e3e42", "overflow": "hidden", "boxShadow": "0 2px 8px rgba(0,0,0,0.3)", "backgroundColor": "#2d2d30"})
            ]),
            
            # Other views (dynamically shown)
            html.Div(id="other-views", style={"display": "none", "width": "100%", "maxWidth": "100%"})
        ], style={"padding": "20px", "fontFamily": "'Inter', sans-serif", "backgroundColor": "#1e1e1e", "width": "100%", "maxWidth": "none", "margin": "0", "boxSizing": "border-box", "color": "#cccccc"})
    ], style={"marginLeft": "250px", "minHeight": "100vh", "width": "calc(100vw - 250px)", "maxWidth": "none", "boxSizing": "border-box", "overflowX": "hidden", "backgroundColor": "#1e1e1e"}),
    
    # Hidden stores
    dcc.Store(id="locations-data"),
    dcc.Store(id="weather-data"),
    dcc.Store(id="map-type-store", data="markers"),
    dcc.Store(id="theme-store", data="light"),
    dcc.Store(id="current-view", data="map"),
    dcc.Store(id="selected-location", data=None),  # ISSUE-002: Store for selected location
    dcc.Store(id="clicked-location", data=None),  # Store for clicked marker location
    dcc.Interval(id="interval-component", interval=300000, n_intervals=0),
    dcc.Download(id="download-report")  # Download component for reports
], style={"display": "flex", "minHeight": "100vh", "width": "100vw", "overflow": "hidden", "backgroundColor": "#1e1e1e"})


# Callbacks

# Sidebar Navigation Callback
@callback(
    [Output("map-view", "style"), Output("other-views", "children"), Output("other-views", "style"), Output("page-title", "children"), Output("current-view", "data")],
    [Input("nav-map", "n_clicks"), Input("nav-analytics", "n_clicks"), 
     Input("nav-favorites", "n_clicks"), Input("nav-history", "n_clicks"), Input("nav-settings", "n_clicks"),
     Input("marker-add-favorite-btn", "n_clicks"), Input({"type": "search-favorite", "index": ALL}, "n_clicks")],
    State("current-view", "data")
)
def update_main_content(map_clicks, analytics_clicks, fav_clicks, hist_clicks, settings_clicks, marker_fav_clicks, search_fav_clicks, current_view):
    ctx_triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
    
    if "nav-map" in ctx_triggered or (not ctx_triggered and current_view != "map"):
        # Map View - show map, hide other views
        return [
            {"display": "block"},
            html.Div(),
            {"display": "none"},
            "Map View",
            "map"
        ]
    elif "nav-analytics" in ctx_triggered:
        # Analytics View - hide map, show analytics
        return [
            {"display": "none"},
            dbc.Card([
                dbc.CardHeader([
                    dbc.Tabs(id="main-tabs", active_tab="insights", children=[
                        dbc.Tab(label="💡 Insights", tab_id="insights"),
                        dbc.Tab(label="📈 Trends", tab_id="trends"),
                        dbc.Tab(label="⚖️ Compare", tab_id="compare"),
                        dbc.Tab(label="📥 Export", tab_id="export")
                    ])
                ]),
                dbc.CardBody([html.Div(id="tab-content")])
            ], style={"border": "1px solid #3e3e42", "overflow": "hidden", "boxShadow": "0 2px 8px rgba(0,0,0,0.3)", "backgroundColor": "#2d2d30"}),
            {"display": "block"},
            "Analytics",
            "analytics"
        ]
    elif "nav-favorites" in ctx_triggered or "marker-add-favorite-btn" in ctx_triggered or ("search-favorite" in ctx_triggered and current_view == "favorites"):
        # Favorites View - hide map, show favorites (refresh when favorite is added)
        favorites = db.get_favorites()
        fav_list = []
        for fav in favorites:
            fav_list.append(
                dbc.Card([
                    dbc.CardBody([
                        html.H5(fav["name"], className="mb-2"),
                        html.P(f"Country: {fav.get('country', 'N/A')}", className="text-muted mb-2"),
                        dbc.Button("Remove", id={"type": "remove-fav", "index": fav["location_id"]}, color="danger", size="sm")
                    ])
                ], className="mb-2", style={"backgroundColor": "#2d2d30", "border": "1px solid #3e3e42", "color": "#cccccc"})
            )
        return [
            {"display": "none"},
            html.Div([
                html.H4("Favorites", className="mb-4"),
                html.Div(fav_list if fav_list else [html.P("No favorites yet", className="text-muted")])
            ]),
            {"display": "block"},
            "Favorites",
            "favorites"
        ]
    elif "nav-history" in ctx_triggered:
        # History View - hide map, show history
        history = db.get_history(limit=50)
        hist_list = []
        for item in history:
            hist_list.append(
                dbc.Card([
                    dbc.CardBody([
                        html.H5(item["name"], className="mb-2"),
                        html.P(f"Country: {item.get('country', 'N/A')} | Viewed: {item.get('viewed_at', 'N/A')}", className="text-muted mb-0")
                    ])
                ], className="mb-2")
            )
        return [
            {"display": "none"},
            html.Div([
                html.H4("Recent History", className="mb-4"),
                dbc.Button("Clear History", id="clear-history-btn", color="danger", className="mb-3"),
                html.Div(hist_list if hist_list else [html.P("No history", className="text-muted")])
            ]),
            {"display": "block"},
            "History",
            "history"
        ]
    elif "nav-settings" in ctx_triggered:
        # Settings View - reuse the settings tab content
        settings = db.get_all_settings()
        api_keys_info = db.get_all_api_keys()
        
        settings_content = html.Div([
            html.H4("Settings", className="mb-4"),
            
            # API Keys Section
            dbc.Card([
                dbc.CardHeader([html.H5("🔑 API Keys", className="mb-0")]),
                dbc.CardBody([
                    html.Div([
                        html.Label("OpenAQ API Key", className="form-label", style={"fontWeight": "600"}),
                        dbc.Input(id="openaq-key-input", type="password", placeholder="Enter OpenAQ API key", value=db.get_api_key("openaq") or config.OPENAQ_API_KEY or "", className="mb-2"),
                        dbc.Button("Save", id="save-openaq-key-btn", color="primary", size="sm", className="me-2"),
                        dbc.Badge("Configured" if (db.get_api_key("openaq") or config.OPENAQ_API_KEY) else "Not Set", color="success" if (db.get_api_key("openaq") or config.OPENAQ_API_KEY) else "secondary", className="ms-2")
                    ], className="mb-4"),
                    
                    html.Div([
                        html.Label("WeatherAPI Key", className="form-label", style={"fontWeight": "600"}),
                        dbc.Input(id="weather-key-input", type="password", placeholder="Enter WeatherAPI key", value=db.get_api_key("weather") or config.WEATHER_API_KEY or "", className="mb-2"),
                        dbc.Button("Save", id="save-weather-key-btn", color="primary", size="sm", className="me-2"),
                        dbc.Badge("Configured" if (db.get_api_key("weather") or config.WEATHER_API_KEY) else "Not Set", color="success" if (db.get_api_key("weather") or config.WEATHER_API_KEY) else "secondary", className="ms-2")
                    ], className="mb-4"),
                    
                    html.Div([
                        html.Label("OpenAI API Key (Optional)", className="form-label", style={"fontWeight": "600"}),
                        dbc.Input(id="openai-key-input", type="password", placeholder="Enter OpenAI API key", value=db.get_api_key("openai") or "", className="mb-2"),
                        dbc.Button("Save", id="save-openai-key-btn", color="primary", size="sm", className="me-2"),
                        dbc.Badge("Configured" if db.get_api_key("openai") else "Not Set", color="success" if db.get_api_key("openai") else "secondary", className="ms-2"),
                        html.Small("Used for AI-powered insights", className="text-muted d-block mt-1")
                    ], className="mb-4")
                ])
            ], className="mb-4"),
            
            # App Settings
            dbc.Card([
                dbc.CardHeader([html.H5("⚙️ Application Settings", className="mb-0")]),
                dbc.CardBody([
                    html.Div([
                        html.Label("Data Refresh Interval (seconds)", className="form-label", style={"fontWeight": "600"}),
                        dbc.Input(id="refresh-interval-input", type="number", min=60, max=3600, step=60, value=settings.get("refresh_interval", "300"), className="mb-2"),
                        dbc.Button("Save", id="save-refresh-interval-btn", color="primary", size="sm")
                    ], className="mb-4"),
                    
                    html.Div([
                        html.Label("AQI Alert Threshold", className="form-label", style={"fontWeight": "600"}),
                        dbc.Input(id="aqi-threshold-input", type="number", min=0, max=500, value=settings.get("aqi_alert_threshold", "150"), className="mb-2"),
                        html.Small("Get notified when AQI exceeds this value", className="text-muted d-block mb-2"),
                        dbc.Button("Save", id="save-aqi-threshold-btn", color="primary", size="sm")
                    ], className="mb-4"),
                    
                    html.Div([
                        html.Label("Notifications", className="form-label", style={"fontWeight": "600"}),
                        dbc.Switch(id="notifications-switch", label="Enable notifications", value=settings.get("notifications_enabled", "true") == "true")
                    ], className="mb-4")
                ])
            ], className="mb-4"),
            
            # Database Info
            dbc.Card([
                dbc.CardHeader([html.H5("💾 Database Information", className="mb-0")]),
                dbc.CardBody([
                    html.P(f"Database Location: {db.db_path}", className="mb-2"),
                    html.P(f"Favorites: {len(db.get_favorites())}", className="mb-2"),
                    html.P(f"History Entries: {len(db.get_history())}", className="mb-0")
                ])
            ])
        ])
        
        return [
            {"display": "none"},
            settings_content,
            {"display": "block"},
            "Settings",
            "settings"
        ]
    
    # Default to map view
    return [
        {"display": "block"},
        html.Div(),
        {"display": "none"},
        "Map View",
        "map"
    ]


@callback(
    [Output("locations-data", "data"), Output("stat-stations", "children"), Output("stat-countries", "children")],
    [Input("interval-component", "n_intervals"), Input("refresh-btn", "n_clicks"), Input("sidebar-refresh-btn", "n_clicks")],
    prevent_initial_call=False
)
def update_data(n, clicks, sidebar_clicks):
    try:
        logger.info("Fetching data...")
        cache_key = "locations:all"
        cached = cache_manager.get(cache_key)
        
        # Check if refresh was clicked
        ctx_triggered = ctx.triggered[0]["prop_id"] if ctx.triggered else ""
        force_refresh = "refresh-btn" in ctx_triggered or "sidebar-refresh-btn" in ctx_triggered
        
        if cached and not force_refresh:
            locations = cached
        else:
            try:
                locations = api_client.get_locations(limit=500)
                if locations:
                    cache_manager.set(cache_key, locations, timeout=300)
            except Exception as e:
                logger.error(f"Error fetching locations: {e}")
                locations = cached if cached else []
    except Exception as e:
        logger.error(f"Error in update_data callback: {e}")
        return [], "0", "0"
    
    if not locations:
        return [], "0", "0"
    
    try:
        processed = [data_processor.process_location_data(loc) for loc in locations if loc]
        countries = len(set(loc.get("country_code") for loc in processed if loc.get("country_code")))
        return processed, str(len(processed)), str(countries)
    except Exception as e:
        logger.error(f"Error processing location data: {e}")
        return [], "0", "0"


@callback(
    Output("main-map", "figure"),
    [Input("locations-data", "data"), Input("map-type-store", "data")],
    prevent_initial_call=False
)
def update_map(data, map_type):
    if not data:
        return go.Figure()
    
    try:
        df = pd.DataFrame(data)
        if df.empty:
            return go.Figure()
        
        df["lat"] = df["coordinates"].apply(lambda x: x.get("latitude") if isinstance(x, dict) and x else None)
        df["lon"] = df["coordinates"].apply(lambda x: x.get("longitude") if isinstance(x, dict) and x else None)
        df = df.dropna(subset=["lat", "lon"])
        
        if df.empty:
            return go.Figure()
        
        aqi_colors = [[0, "rgb(0,228,0)"], [0.17, "rgb(255,255,0)"], [0.33, "rgb(255,126,0)"], [0.5, "rgb(255,0,0)"], [0.67, "rgb(143,63,151)"], [1, "rgb(126,0,35)"]]
        
        if map_type == "heatmap":
            fig = go.Figure(go.Densitymapbox(lon=df["lon"], lat=df["lat"], z=df["max_aqi"], radius=25, colorscale=aqi_colors, zmin=0, zmax=300, colorbar=dict(title="AQI")))
            fig.update_layout(mapbox=dict(style="open-street-map", center=dict(lat=20, lon=0), zoom=1.5), height=400, margin=dict(l=0,r=0,t=0,b=0))
        elif map_type == "density":
            fig = px.density_mapbox(df, lat="lat", lon="lon", z="max_aqi", radius=20, center=dict(lat=20, lon=0), zoom=1.5, mapbox_style="open-street-map", color_continuous_scale=aqi_colors, range_color=[0,300], height=400)
            fig.update_layout(margin=dict(l=0,r=0,t=0,b=0))
        else:
            # ISSUE-002: Add click events to markers
            # Ensure location_id exists (fallback to id if needed)
            if "location_id" not in df.columns:
                if "id" in df.columns:
                    df["location_id"] = df["id"].astype(str)
                else:
                    df["location_id"] = df.index.astype(str)
            
            # Prepare customdata for click events - use list of lists for Plotly
            customdata = df[["location_id", "name", "country", "max_aqi"]].values.tolist()
            
            fig = go.Figure(go.Scattermapbox(
                lon=df["lon"], 
                lat=df["lat"], 
                mode="markers", 
                marker=dict(size=10, color=df["max_aqi"], colorscale=aqi_colors, cmin=0, cmax=300, colorbar=dict(title="AQI"), opacity=0.8), 
                text=df.apply(lambda r: f"<b>{r['name']}</b><br>AQI: {r['max_aqi']}", axis=1), 
                hovertemplate="%{text}<extra></extra>",
                customdata=customdata
            ))
            fig.update_layout(
                mapbox=dict(style="open-street-map", center=dict(lat=20, lon=0), zoom=1.5), 
                height=400, 
                margin=dict(l=0,r=0,t=0,b=0),
                clickmode='event+select'  # Enable click events
            )
        
        return fig
    except Exception as e:
        logger.error(f"Error updating map: {e}")
        return go.Figure()


@callback(
    [Output("main-aqi", "children"), Output("aqi-status-badge", "children")],
    Input("locations-data", "data")
)
def update_aqi(data):
    if not data:
        return "--", ""
    try:
        df = pd.DataFrame(data)
        if df.empty or "max_aqi" not in df.columns:
            return "--", ""
        avg_aqi = int(df["max_aqi"].mean())
        category = data_processor.get_aqi_category(avg_aqi)
        color = data_processor.get_aqi_color(avg_aqi)
        badge = dbc.Badge(category, color="light", style={"backgroundColor": color, "padding": "8px 16px", "fontSize": "14px"})
        return str(avg_aqi), badge
    except Exception as e:
        logger.error(f"Error updating AQI: {e}")
        return "--", ""


# ISSUE-002: Map click handler - opens action modal
@callback(
    [Output("clicked-location", "data"), Output("marker-action-modal", "is_open")],
    Input("main-map", "clickData"),
    State("locations-data", "data"),
    prevent_initial_call=True
)
def handle_map_click(click_data, locations_data):
    """Handle map marker clicks to open action modal"""
    if not click_data or not click_data.get("points"):
        return None, False
    
    try:
        point = click_data["points"][0]
        customdata = point.get("customdata")
        if customdata and isinstance(customdata, list) and len(customdata) >= 4:
            # customdata is [location_id, name, country, max_aqi]
            location_id = str(customdata[0])
            # Find full location data
            if locations_data:
                for loc in locations_data:
                    if isinstance(loc, dict):
                        loc_id = str(loc.get("location_id") or loc.get("id", ""))
                        if loc_id == location_id:
                            # Add to history
                            db.add_to_history(
                                location_id=location_id,
                                name=loc.get("name", "Unknown"),
                                country=loc.get("country", ""),
                                latitude=loc.get("coordinates", {}).get("latitude") if isinstance(loc.get("coordinates"), dict) else None,
                                longitude=loc.get("coordinates", {}).get("longitude") if isinstance(loc.get("coordinates"), dict) else None
                            )
                            return loc, True  # Open modal
    except Exception as e:
        logger.error(f"Error handling map click: {e}")
    return None, False


# ISSUE-003: Fix weather to use selected location
@callback(
    [Output("weather-info", "children"), Output("stat-wind", "children"), Output("stat-humidity", "children"), Output("current-location", "children")],
    [Input("locations-data", "data"), Input("selected-location", "data")]
)
def update_weather(data, selected_loc):
    """Update weather for selected location or first location"""
    if not data or not config.WEATHER_API_KEY:
        return "", "--", "--", "Global"
    
    # ISSUE-003: Use selected location if available, otherwise first location
    try:
        if selected_loc and isinstance(selected_loc, dict):
            loc = selected_loc
            location_name = loc.get("name", "Selected Location")
        else:
            loc = data[0] if isinstance(data, list) and len(data) > 0 else None
            location_name = "Global"
        
        if not loc:
            return "", "--", "--", location_name
        
        coords = loc.get("coordinates", {}) if isinstance(loc, dict) else {}
        lat, lon = coords.get("latitude"), coords.get("longitude")
        
        if not lat or not lon:
            return "", "--", "--", location_name
    except (IndexError, TypeError, AttributeError):
        return "", "--", "--", "Global"
    
    weather = weather_client.get_current_weather(lat, lon)
    if not weather:
        return "", "--", "--", location_name
    
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
    ], style={"fontSize": "14px", "color": "#cccccc"})
    
    return weather_div, str(weather.get('wind_speed_kph', '--')), f"{weather.get('humidity', '--')}%", location_name


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
    
    try:
        df = pd.DataFrame(data)
        if df.empty:
            return html.Div("No data available", className="text-center py-5")
        
        if tab == "insights":
            if "max_aqi" not in df.columns or "name" not in df.columns:
                return html.Div("Data format error", className="text-center py-5")
            
            top10 = df.nlargest(10, "max_aqi") if len(df) > 0 else df
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
                dbc.Button([html.I(className="fas fa-file-pdf me-2"), "Download PDF Report"], id="export-pdf-btn", color="primary", className="mb-2 w-100"),
                dbc.Button([html.I(className="fas fa-file-excel me-2"), "Export to Excel"], id="export-excel-btn", color="success", className="mb-2 w-100"),
                dbc.Button([html.I(className="fas fa-file-csv me-2"), "Export to CSV"], id="export-csv-btn", color="info", className="w-100")
            ])
        
        elif tab == "settings":
            # Get current settings
            settings = db.get_all_settings()
            api_keys_info = db.get_all_api_keys()
            
            return html.Div([
                html.H4("Settings", className="mb-4"),
                
                # API Keys Section
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("🔑 API Keys", className="mb-0")
                    ]),
                    dbc.CardBody([
                        # OpenAQ API Key
                        html.Div([
                            html.Label("OpenAQ API Key", className="form-label", style={"fontWeight": "600"}),
                            dbc.Input(
                                id="openaq-key-input",
                                type="password",
                                placeholder="Enter OpenAQ API key",
                                value=db.get_api_key("openaq") or config.OPENAQ_API_KEY or "",
                                className="mb-2"
                            ),
                            dbc.Button("Save", id="save-openaq-key-btn", color="primary", size="sm", className="me-2"),
                            dbc.Badge("Configured" if (db.get_api_key("openaq") or config.OPENAQ_API_KEY) else "Not Set", 
                                    color="success" if (db.get_api_key("openaq") or config.OPENAQ_API_KEY) else "secondary", className="ms-2")
                        ], className="mb-4"),
                        
                        # WeatherAPI Key
                        html.Div([
                            html.Label("WeatherAPI Key", className="form-label", style={"fontWeight": "600"}),
                            dbc.Input(
                                id="weather-key-input",
                                type="password",
                                placeholder="Enter WeatherAPI key",
                                value=db.get_api_key("weather") or config.WEATHER_API_KEY or "",
                                className="mb-2"
                            ),
                            dbc.Button("Save", id="save-weather-key-btn", color="primary", size="sm", className="me-2"),
                            dbc.Badge("Configured" if (db.get_api_key("weather") or config.WEATHER_API_KEY) else "Not Set",
                                    color="success" if (db.get_api_key("weather") or config.WEATHER_API_KEY) else "secondary", className="ms-2")
                        ], className="mb-4"),
                        
                        # OpenAI Key
                        html.Div([
                            html.Label("OpenAI API Key (Optional)", className="form-label", style={"fontWeight": "600"}),
                            dbc.Input(
                                id="openai-key-input",
                                type="password",
                                placeholder="Enter OpenAI API key",
                                value=db.get_api_key("openai") or "",
                                className="mb-2"
                            ),
                            dbc.Button("Save", id="save-openai-key-btn", color="primary", size="sm", className="me-2"),
                            dbc.Badge("Configured" if db.get_api_key("openai") else "Not Set",
                                    color="success" if db.get_api_key("openai") else "secondary", className="ms-2"),
                            html.Small("Used for AI-powered insights and recommendations", className="text-muted d-block mt-1")
                        ], className="mb-4")
                    ])
                ], className="mb-4"),
                
                # App Settings Section
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("⚙️ Application Settings", className="mb-0")
                    ]),
                    dbc.CardBody([
                        # Refresh Interval
                        html.Div([
                            html.Label("Data Refresh Interval (seconds)", className="form-label", style={"fontWeight": "600"}),
                            dbc.Input(
                                id="refresh-interval-input",
                                type="number",
                                min=60,
                                max=3600,
                                step=60,
                                value=settings.get("refresh_interval", "300"),
                                className="mb-2"
                            ),
                            dbc.Button("Save", id="save-refresh-interval-btn", color="primary", size="sm")
                        ], className="mb-4"),
                        
                        # AQI Alert Threshold
                        html.Div([
                            html.Label("AQI Alert Threshold", className="form-label", style={"fontWeight": "600"}),
                            dbc.Input(
                                id="aqi-threshold-input",
                                type="number",
                                min=0,
                                max=500,
                                value=settings.get("aqi_alert_threshold", "150"),
                                className="mb-2"
                            ),
                            html.Small("Get notified when AQI exceeds this value", className="text-muted d-block mb-2"),
                            dbc.Button("Save", id="save-aqi-threshold-btn", color="primary", size="sm")
                        ], className="mb-4"),
                        
                        # Notifications
                        html.Div([
                            html.Label("Notifications", className="form-label", style={"fontWeight": "600"}),
                            dbc.Switch(
                                id="notifications-switch",
                                label="Enable notifications",
                                value=settings.get("notifications_enabled", "true") == "true"
                            )
                        ], className="mb-4")
                    ])
                ], className="mb-4"),
                
                # Database Info
                dbc.Card([
                    dbc.CardHeader([
                        html.H5("💾 Database Information", className="mb-0")
                    ]),
                    dbc.CardBody([
                        html.P(f"Database Location: {db.db_path}", className="mb-2"),
                        html.P(f"Favorites: {len(db.get_favorites())}", className="mb-2"),
                        html.P(f"History Entries: {len(db.get_history())}", className="mb-0")
                    ])
                ])
            ])
        
        return html.Div("Select a tab")
    except Exception as e:
        logger.error(f"Error rendering tab: {e}")
        return html.Div(f"Error: {str(e)}", className="text-center py-5")


@callback(
    Output("search-modal", "is_open"),
    Input("search-btn", "n_clicks"),
    State("search-modal", "is_open"),
    prevent_initial_call=True
)
def toggle_search(n, is_open):
    """Toggle search modal - only responds to button click"""
    if n:
        return not is_open
    return is_open


# ISSUE-001: Search Functionality - Fixed modal closing issue
@callback(
    Output("search-results", "children"),
    Input("search-input", "value"),
    State("locations-data", "data"),
    prevent_initial_call=True
)
def search_locations(query, data):
    if not query or not data:
        return html.Div("Enter a search term to find locations", className="text-muted text-center py-3")
    
    try:
        query_lower = query.lower().strip()
        if len(query_lower) < 2:
            return html.Div("Please enter at least 2 characters", className="text-muted text-center py-3")
        
        # Search in location names and countries
        results = []
        for loc in data:
            if not isinstance(loc, dict):
                continue
            
            name = loc.get("name", "").lower()
            country = loc.get("country", "").lower()
            country_code = loc.get("country_code", "").lower()
            
            if (query_lower in name or 
                query_lower in country or 
                query_lower in country_code):
                results.append(loc)
        
        if not results:
            return html.Div([
                html.I(className="fas fa-search me-2"),
                f"No locations found for '{query}'"
            ], className="text-muted text-center py-3")
        
        # Limit to top 20 results
        results = results[:20]
        
        # Create result cards
        result_cards = []
        for loc in results:
            coords = loc.get("coordinates", {})
            lat = coords.get("latitude") if isinstance(coords, dict) else None
            lon = coords.get("longitude") if isinstance(coords, dict) else None
            aqi = loc.get("max_aqi", "N/A")
            aqi_color = data_processor.get_aqi_color(aqi) if isinstance(aqi, (int, float)) else "#666"
            
            result_cards.append(
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H6(loc.get("name", "Unknown"), className="mb-1", style={"color": "#cccccc"}),
                            html.Small(f"{loc.get('country', 'N/A')} | AQI: {aqi}", className="text-muted")
                        ]),
                        html.Div([
                            dbc.Button(
                                "View on Map",
                                id={"type": "search-select", "index": loc.get("location_id", "")},
                                color="primary",
                                size="sm",
                                className="me-2 mt-2"
                            ),
                            dbc.Button(
                                "Add to Favorites",
                                id={"type": "search-favorite", "index": loc.get("location_id", "")},
                                color="success",
                                size="sm",
                                className="mt-2"
                            )
                        ])
                    ])
                ], className="mb-2", style={"backgroundColor": "#2d2d30", "border": "1px solid #3e3e42"})
            )
        
        return html.Div([
            html.P(f"Found {len(results)} location(s)", className="text-muted mb-3"),
            html.Div(result_cards)
        ])
        
    except Exception as e:
        logger.error(f"Error searching locations: {e}")
        return html.Div("Error searching locations", className="text-danger text-center py-3")


# ISSUE-001: Search action callbacks
@callback(
    [Output("selected-location", "data", allow_duplicate=True), Output("search-modal", "is_open", allow_duplicate=True)],
    Input({"type": "search-select", "index": ALL}, "n_clicks"),
    State("locations-data", "data"),
    prevent_initial_call=True
)
def select_location_from_search(n_clicks_list, data):
    """Select location from search results"""
    if ctx.triggered and data:
        try:
            triggered_id = ctx.triggered[0]["prop_id"]
            if "search-select" in triggered_id:
                location_id = json.loads(triggered_id.split(".")[0])["index"]
                for loc in data:
                    if isinstance(loc, dict):
                        loc_id = str(loc.get("location_id") or loc.get("id", ""))
                        if loc_id == str(location_id):
                            # Add to history
                            db.add_to_history(
                                location_id=loc_id,
                                name=loc.get("name", "Unknown"),
                                country=loc.get("country", ""),
                                latitude=loc.get("coordinates", {}).get("latitude") if isinstance(loc.get("coordinates"), dict) else None,
                                longitude=loc.get("coordinates", {}).get("longitude") if isinstance(loc.get("coordinates"), dict) else None
                            )
                            return loc, False  # Close modal
        except Exception as e:
            logger.error(f"Error selecting location from search: {e}")
    return no_update, no_update


@callback(
    [Output("search-results", "children", allow_duplicate=True), Output("other-views", "children", allow_duplicate=True)],
    Input({"type": "search-favorite", "index": ALL}, "n_clicks"),
    [State("locations-data", "data"), State("current-view", "data")],
    prevent_initial_call=True
)
def add_favorite_from_search(n_clicks_list, data, current_view):
    """Add location to favorites from search"""
    if ctx.triggered and data:
        try:
            triggered_id = ctx.triggered[0]["prop_id"]
            if "search-favorite" in triggered_id:
                location_id = json.loads(triggered_id.split(".")[0])["index"]
                for loc in data:
                    if isinstance(loc, dict):
                        loc_id = str(loc.get("location_id") or loc.get("id", ""))
                        if loc_id == str(location_id):
                            # Check if already in favorites to avoid duplicates
                            if not db.is_favorite(loc_id):
                                db.add_favorite(
                                    location_id=loc_id,
                                    name=loc.get("name", "Unknown"),
                                    country=loc.get("country", ""),
                                    latitude=loc.get("coordinates", {}).get("latitude") if isinstance(loc.get("coordinates"), dict) else None,
                                    longitude=loc.get("coordinates", {}).get("longitude") if isinstance(loc.get("coordinates"), dict) else None
                                )
        except Exception as e:
            logger.error(f"Error adding favorite from search: {e}")
    return no_update, no_update


@callback(
    Output("clear-history-btn", "children"),
    Input("clear-history-btn", "n_clicks"),
    prevent_initial_call=True
)
def clear_history(n):
    if n:
        db.clear_history()
        return "History Cleared!"
    return "Clear History"


# Settings Callbacks
@callback(
    Output("save-openaq-key-btn", "children"),
    Input("save-openaq-key-btn", "n_clicks"),
    State("openaq-key-input", "value"),
    prevent_initial_call=True
)
def save_openaq_key(n, key_value):
    if n and key_value:
        db.save_api_key("openaq", key_value)
        return "Saved!"
    return "Save"


@callback(
    Output("save-weather-key-btn", "children"),
    Input("save-weather-key-btn", "n_clicks"),
    State("weather-key-input", "value"),
    prevent_initial_call=True
)
def save_weather_key(n, key_value):
    if n and key_value:
        db.save_api_key("weather", key_value)
        return "Saved!"
    return "Save"


@callback(
    Output("save-openai-key-btn", "children"),
    Input("save-openai-key-btn", "n_clicks"),
    State("openai-key-input", "value"),
    prevent_initial_call=True
)
def save_openai_key(n, key_value):
    if n and key_value:
        db.save_api_key("openai", key_value)
        return "Saved!"
    return "Save"


@callback(
    Output("save-refresh-interval-btn", "children"),
    Input("save-refresh-interval-btn", "n_clicks"),
    State("refresh-interval-input", "value"),
    prevent_initial_call=True
)
def save_refresh_interval(n, value):
    if n and value:
        db.set_setting("refresh_interval", str(value))
        return "Saved!"
    return "Save"


@callback(
    Output("save-aqi-threshold-btn", "children"),
    Input("save-aqi-threshold-btn", "n_clicks"),
    State("aqi-threshold-input", "value"),
    prevent_initial_call=True
)
def save_aqi_threshold(n, value):
    if n and value:
        db.set_setting("aqi_alert_threshold", str(value))
        return "Saved!"
    return "Save"


@callback(
    Output("notifications-switch", "value"),
    Input("notifications-switch", "value"),
    prevent_initial_call=True
)
def save_notifications(value):
    db.set_setting("notifications_enabled", "true" if value else "false")
    return value






# Export Callbacks
@callback(
    Output("export-pdf-btn", "children"),
    Input("export-pdf-btn", "n_clicks"),
    State("locations-data", "data"),
    prevent_initial_call=True
)
def export_pdf(n, data):
    if n and data:
        try:
            df = pd.DataFrame(data)
            # Generate comparison report for all locations
            locations_list = df.to_dict('records')
            if locations_list:
                report_path = report_gen.generate_comparison_report(locations_list)
                return f"PDF Saved: {report_path.name}!"
        except Exception as e:
            logger.error(f"Error exporting PDF: {e}")
            return "Error!"
    return "Download PDF Report"


@callback(
    Output("export-excel-btn", "children"),
    Input("export-excel-btn", "n_clicks"),
    State("locations-data", "data"),
    prevent_initial_call=True
)
def export_excel(n, data):
    if n and data:
        try:
            df = pd.DataFrame(data)
            excel_path = config.EXPORTS_DIR / f"airwatch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
            df.to_excel(excel_path, index=False)
            return "Excel Exported!"
        except Exception as e:
            logger.error(f"Error exporting Excel: {e}")
            return "Error!"
    return "Export to Excel"


@callback(
    Output("export-csv-btn", "children"),
    Input("export-csv-btn", "n_clicks"),
    State("locations-data", "data"),
    prevent_initial_call=True
)
def export_csv(n, data):
    if n and data:
        try:
            df = pd.DataFrame(data)
            csv_path = config.EXPORTS_DIR / f"airwatch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            df.to_csv(csv_path, index=False)
            return "CSV Exported!"
        except Exception as e:
            logger.error(f"Error exporting CSV: {e}")
            return "Error!"
    return "Export to CSV"


# Remove favorite callback - updates the favorites view when a favorite is removed
@callback(
    Output("other-views", "children", allow_duplicate=True),
    Input({"type": "remove-fav", "index": ALL}, "n_clicks"),
    State("current-view", "data"),
    prevent_initial_call=True
)
def remove_favorite(n_clicks_list, current_view):
    try:
        # Only process if a remove button was actually clicked (not just view regeneration)
        if ctx.triggered and current_view == "favorites":
            triggered_id = ctx.triggered[0]["prop_id"]
            if "remove-fav" in triggered_id and ctx.triggered[0]["value"]:
                # Check if this button was actually clicked (value > 0)
                location_id = json.loads(triggered_id.split(".")[0])["index"]
                db.remove_favorite(location_id)
        
        # Refresh favorites view only if we're on favorites tab
        if current_view == "favorites":
            favorites = db.get_favorites()
            fav_list = []
            for fav in favorites:
                fav_list.append(
                    dbc.Card([
                        dbc.CardBody([
                            html.H5(fav["name"], className="mb-2"),
                            html.P(f"Country: {fav.get('country', 'N/A')}", className="text-muted mb-2"),
                            dbc.Button("Remove", id={"type": "remove-fav", "index": fav["location_id"]}, color="danger", size="sm")
                        ])
                    ], className="mb-2", style={"backgroundColor": "#2d2d30", "border": "1px solid #3e3e42", "color": "#cccccc"})
                )
            return html.Div([
                html.H4("Favorites", className="mb-4"),
                html.Div(fav_list if fav_list else [html.P("No favorites yet", className="text-muted")])
            ])
    except Exception as e:
        logger.error(f"Error removing favorite: {e}")
    return no_update


# Marker Action Modal Callbacks - Enhanced for GeoTEO
@callback(
    [Output("marker-modal-header", "children"), Output("marker-modal-body", "children")],
    Input("clicked-location", "data")
)
def update_marker_modal(location_data):
    """Update marker modal with comprehensive geospatial and meteorological information"""
    if not location_data or not isinstance(location_data, dict):
        return "Location Details", html.Div("No location selected")
    
    name = location_data.get("name", "Unknown")
    country = location_data.get("country", "N/A")
    aqi = location_data.get("max_aqi", 0)
    aqi_category = data_processor.get_aqi_category(aqi) if isinstance(aqi, (int, float)) else "Unknown"
    aqi_color = data_processor.get_aqi_color(aqi) if isinstance(aqi, (int, float)) else "#666"
    
    coords = location_data.get("coordinates", {})
    lat = coords.get("latitude") if isinstance(coords, dict) else None
    lon = coords.get("longitude") if isinstance(coords, dict) else None
    
    is_favorite = db.is_favorite(str(location_data.get("location_id") or location_data.get("id", "")))
    
    # Fetch weather data if coordinates are available
    weather_data = None
    forecast_data = None
    weather_analysis = None
    
    if lat and lon and config.WEATHER_API_KEY:
        try:
            weather_data = weather_client.get_current_weather(lat, lon)
            forecast_data = weather_client.get_forecast(lat, lon, days=3)
            if weather_data and aqi:
                weather_analysis = weather_client.analyze_weather_air_quality_correlation(weather_data, aqi)
        except Exception as e:
            logger.error(f"Error fetching weather data: {e}")
    
    # Build modal content with tabs for different information
    tabs_content = []
    
    # Tab 1: Overview (Air Quality + Current Weather)
    overview_content = html.Div([
        # Air Quality Section
        html.Div([
            html.H5("🌍 Air Quality", className="mb-3", style={"color": "#cccccc", "fontWeight": "600"}),
            html.Div([
                html.Div([
                    html.P("Air Quality Index", className="mb-1", style={"fontSize": "14px", "color": "#858585"}),
                    html.H3(str(aqi), style={"fontSize": "48px", "fontWeight": "700", "color": aqi_color, "margin": "0"}),
                    dbc.Badge(aqi_category, style={"backgroundColor": aqi_color, "color": "#fff", "marginTop": "8px", "fontSize": "12px"})
                ], style={"textAlign": "center", "padding": "20px", "backgroundColor": "#1e1e1e", "borderRadius": "4px", "marginBottom": "20px"})
            ]),
            # Pollutants info
            html.Div([
                html.P("Monitored Pollutants:", className="mb-2", style={"fontSize": "14px", "color": "#cccccc", "fontWeight": "600"}),
                html.Div([
                    html.Span(f"• {poll.get('display_name', 'Unknown')}: {poll.get('value', 'N/A')} {poll.get('units', '')}", 
                             style={"display": "block", "fontSize": "12px", "color": "#858585", "marginBottom": "4px"})
                    for poll in location_data.get("sensors", [])[:5]
                ]) if location_data.get("sensors") else html.P("No sensor data available", style={"fontSize": "12px", "color": "#666"})
            ])
        ], className="mb-4"),
        
        # Current Weather Section
        html.Div([
            html.H5("🌤️ Current Weather", className="mb-3", style={"color": "#cccccc", "fontWeight": "600"}),
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-temperature-high", style={"fontSize": "24px", "color": "#ff6b6b", "marginRight": "10px"}),
                            html.Div([
                                html.H4(f"{weather_data.get('temperature_c', '--')}°C" if weather_data else "--", 
                                       style={"margin": "0", "fontSize": "28px", "fontWeight": "700", "color": "#cccccc"}),
                                html.Small(f"Feels like {weather_data.get('feels_like_c', '--')}°C" if weather_data else "", 
                                          style={"color": "#858585", "fontSize": "12px"})
                            ])
                        ], style={"display": "flex", "alignItems": "center", "padding": "15px", "backgroundColor": "#1e1e1e", "borderRadius": "4px"})
                    ], width=6, className="mb-2"),
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-cloud", style={"fontSize": "20px", "color": "#74b9ff", "marginRight": "10px"}),
                            html.Div([
                                html.P(weather_data.get('condition', 'N/A') if weather_data else "N/A", 
                                      style={"margin": "0", "fontSize": "14px", "fontWeight": "600", "color": "#cccccc"}),
                                html.Small(f"Cloud: {weather_data.get('cloud_cover', '--')}%" if weather_data else "", 
                                          style={"color": "#858585", "fontSize": "11px"})
                            ])
                        ], style={"display": "flex", "alignItems": "center", "padding": "15px", "backgroundColor": "#1e1e1e", "borderRadius": "4px"})
                    ], width=6, className="mb-2")
                ]),
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-wind", style={"fontSize": "18px", "color": "#a29bfe", "marginRight": "8px"}),
                            html.Div([
                                html.P(f"{weather_data.get('wind_speed_kph', '--')} km/h" if weather_data else "--", 
                                      style={"margin": "0", "fontSize": "14px", "fontWeight": "600", "color": "#cccccc"}),
                                html.Small(weather_data.get('wind_direction', '') if weather_data else "", 
                                          style={"color": "#858585", "fontSize": "11px"})
                            ])
                        ], style={"display": "flex", "alignItems": "center", "padding": "12px", "backgroundColor": "#1e1e1e", "borderRadius": "4px"})
                    ], width=4, className="mb-2"),
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-tint", style={"fontSize": "18px", "color": "#0984e3", "marginRight": "8px"}),
                            html.Div([
                                html.P(f"{weather_data.get('humidity', '--')}%" if weather_data else "--", 
                                      style={"margin": "0", "fontSize": "14px", "fontWeight": "600", "color": "#cccccc"}),
                                html.Small("Humidity", style={"color": "#858585", "fontSize": "11px"})
                            ])
                        ], style={"display": "flex", "alignItems": "center", "padding": "12px", "backgroundColor": "#1e1e1e", "borderRadius": "4px"})
                    ], width=4, className="mb-2"),
                    dbc.Col([
                        html.Div([
                            html.I(className="fas fa-compress-arrows-alt", style={"fontSize": "18px", "color": "#00b894", "marginRight": "8px"}),
                            html.Div([
                                html.P(f"{weather_data.get('pressure_mb', '--')} mb" if weather_data else "--", 
                                      style={"margin": "0", "fontSize": "14px", "fontWeight": "600", "color": "#cccccc"}),
                                html.Small("Pressure", style={"color": "#858585", "fontSize": "11px"})
                            ])
                        ], style={"display": "flex", "alignItems": "center", "padding": "12px", "backgroundColor": "#1e1e1e", "borderRadius": "4px"})
                    ], width=4, className="mb-2")
                ], className="mt-2"),
                html.Div([
                    html.P([
                        html.I(className="fas fa-sun", style={"marginRight": "8px", "color": "#fdcb6e"}),
                        html.Span(f"UV Index: {weather_data.get('uv_index', '--')}" if weather_data else "UV Index: --", 
                                 style={"fontSize": "13px", "color": "#cccccc"}),
                        html.Span(" | ", style={"margin": "0 8px", "color": "#666"}),
                        html.I(className="fas fa-eye", style={"marginRight": "8px", "color": "#6c5ce7"}),
                        html.Span(f"Visibility: {weather_data.get('visibility_km', '--')} km" if weather_data else "Visibility: --", 
                                 style={"fontSize": "13px", "color": "#cccccc"})
                    ], style={"marginTop": "15px", "padding": "10px", "backgroundColor": "#1e1e1e", "borderRadius": "4px"})
                ]) if weather_data else html.Div()
            ]) if weather_data else html.Div([
                html.P("Weather data unavailable. Please configure WEATHER_API_KEY in your .env file.", 
                      style={"color": "#858585", "fontSize": "13px", "fontStyle": "italic"})
            ])
        ])
    ])
    
    tabs_content.append(dbc.Tab(overview_content, label="Overview", tab_id="tab-overview"))
    
    # Tab 2: Weather Forecast (if available)
    if forecast_data and forecast_data.get("forecast"):
        forecast_content = html.Div([
            html.H5("📅 3-Day Weather Forecast", className="mb-3", style={"color": "#cccccc", "fontWeight": "600"}),
            html.Div([
                dbc.Card([
                    dbc.CardBody([
                        html.Div([
                            html.H6(day.get("date", "N/A"), className="mb-2", style={"color": "#cccccc", "fontWeight": "600"}),
                            html.P(day.get("condition", "N/A"), className="mb-2", style={"fontSize": "13px", "color": "#858585"}),
                            html.Div([
                                html.Span(f"↑ {day.get('max_temp_c', '--')}°C", style={"color": "#ff6b6b", "fontWeight": "600", "marginRight": "15px"}),
                                html.Span(f"↓ {day.get('min_temp_c', '--')}°C", style={"color": "#74b9ff", "fontWeight": "600"})
                            ], className="mb-2"),
                            html.Div([
                                html.Small([
                                    html.I(className="fas fa-wind", style={"marginRight": "4px"}),
                                    f"{day.get('max_wind_kph', '--')} km/h"
                                ], style={"color": "#858585", "fontSize": "11px", "marginRight": "15px"}),
                                html.Small([
                                    html.I(className="fas fa-tint", style={"marginRight": "4px"}),
                                    f"{day.get('avg_humidity', '--')}%"
                                ], style={"color": "#858585", "fontSize": "11px"}),
                                html.Small([
                                    html.I(className="fas fa-sun", style={"marginRight": "4px"}),
                                    f"UV: {day.get('uv_index', '--')}"
                                ], style={"color": "#858585", "fontSize": "11px"})
                            ])
                        ])
                    ])
                ], style={"backgroundColor": "#1e1e1e", "border": "1px solid #3e3e42", "marginBottom": "10px"})
                for day in forecast_data["forecast"]
            ])
        ])
        tabs_content.append(dbc.Tab(forecast_content, label="Forecast", tab_id="tab-forecast"))
    
    # Tab 3: Analysis (Weather-Air Quality Correlation)
    if weather_analysis:
        analysis_content = html.Div([
            html.H5("🔬 Weather-Air Quality Analysis", className="mb-3", style={"color": "#cccccc", "fontWeight": "600"}),
            html.Div([
                dbc.Row([
                    dbc.Col([
                        html.Div([
                            html.P("Wind Impact", className="mb-1", style={"fontSize": "12px", "color": "#858585"}),
                            html.H6(weather_analysis.get("wind_impact", "unknown").title(), 
                                   style={"color": "#cccccc", "fontWeight": "600"})
                        ], style={"padding": "15px", "backgroundColor": "#1e1e1e", "borderRadius": "4px", "textAlign": "center"})
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.P("Humidity Impact", className="mb-1", style={"fontSize": "12px", "color": "#858585"}),
                            html.H6(weather_analysis.get("humidity_impact", "unknown").title(), 
                                   style={"color": "#cccccc", "fontWeight": "600"})
                        ], style={"padding": "15px", "backgroundColor": "#1e1e1e", "borderRadius": "4px", "textAlign": "center"})
                    ], width=4),
                    dbc.Col([
                        html.Div([
                            html.P("Temperature Impact", className="mb-1", style={"fontSize": "12px", "color": "#858585"}),
                            html.H6(weather_analysis.get("temperature_impact", "unknown").title(), 
                                   style={"color": "#cccccc", "fontWeight": "600"})
                        ], style={"padding": "15px", "backgroundColor": "#1e1e1e", "borderRadius": "4px", "textAlign": "center"})
                    ], width=4)
                ], className="mb-3"),
                html.Div([
                    html.P("Overall Conditions", className="mb-2", style={"fontSize": "14px", "color": "#cccccc", "fontWeight": "600"}),
                    dbc.Badge(weather_analysis.get("overall_conditions", "unknown").title(), 
                             color="success" if weather_analysis.get("overall_conditions") == "favorable" else 
                                   "warning" if weather_analysis.get("overall_conditions") == "moderate" else "danger",
                             style={"fontSize": "13px", "padding": "8px 15px"})
                ], className="mb-3"),
                html.Div([
                    html.P("Recommendations", className="mb-2", style={"fontSize": "14px", "color": "#cccccc", "fontWeight": "600"}),
                    html.Ul([
                        html.Li(rec, style={"fontSize": "12px", "color": "#858585", "marginBottom": "5px"})
                        for rec in weather_analysis.get("recommendations", [])
                    ])
                ]) if weather_analysis.get("recommendations") else html.Div()
            ])
        ])
        tabs_content.append(dbc.Tab(analysis_content, label="Analysis", tab_id="tab-analysis"))
    
    # Tab 4: Location Details
    details_content = html.Div([
        html.H5("📍 Location Information", className="mb-3", style={"color": "#cccccc", "fontWeight": "600"}),
        html.Div([
            html.P([
                html.Strong("Name: ", style={"color": "#cccccc"}),
                html.Span(name, style={"color": "#858585"})
            ], className="mb-2"),
            html.P([
                html.Strong("Country: ", style={"color": "#cccccc"}),
                html.Span(country, style={"color": "#858585"})
            ], className="mb-2"),
            html.P([
                html.Strong("Coordinates: ", style={"color": "#cccccc"}),
                html.Span(f"{lat}, {lon}" if lat and lon else "N/A", style={"color": "#858585"})
            ], className="mb-2"),
            html.P([
                html.Strong("Location ID: ", style={"color": "#cccccc"}),
                html.Span(str(location_data.get("location_id") or location_data.get("id", "N/A")), 
                         style={"color": "#858585", "fontFamily": "monospace", "fontSize": "12px"})
            ], className="mb-2"),
            html.P([
                html.Strong("Status: ", style={"color": "#cccccc"}),
                html.Span("⭐ In Favorites" if is_favorite else "Not in Favorites", 
                         style={"color": "#858585"})
            ], className="mb-0")
        ], style={"padding": "15px", "backgroundColor": "#1e1e1e", "borderRadius": "4px"})
    ])
    tabs_content.append(dbc.Tab(details_content, label="Details", tab_id="tab-details"))
    
    # Create tabs component
    tabs = dbc.Tabs(tabs_content, active_tab="tab-overview", className="mb-3")
    
    modal_body = html.Div([
        html.Div([
            html.H4(name, className="mb-1", style={"color": "#cccccc", "fontWeight": "700"}),
            html.P([
                html.I(className="fas fa-map-marker-alt me-2", style={"color": "#007acc"}),
                f"{country}"
            ], className="text-muted mb-3", style={"fontSize": "14px"})
        ], className="mb-3"),
        tabs
    ])
    
    return f"🌍 {name} - GeoTEO Report", modal_body


@callback(
    Output("marker-action-modal", "is_open", allow_duplicate=True),
    Input("marker-add-favorite-btn", "n_clicks"),
    State("clicked-location", "data"),
    prevent_initial_call=True
)
def add_favorite_from_marker(n_clicks, location_data):
    """Add location to favorites from marker modal"""
    if n_clicks and location_data:
        try:
            loc_id = str(location_data.get("location_id") or location_data.get("id", ""))
            # Check if already in favorites to avoid duplicates
            if not db.is_favorite(loc_id):
                db.add_favorite(
                    location_id=loc_id,
                    name=location_data.get("name", "Unknown"),
                    country=location_data.get("country", ""),
                    latitude=location_data.get("coordinates", {}).get("latitude") if isinstance(location_data.get("coordinates"), dict) else None,
                    longitude=location_data.get("coordinates", {}).get("longitude") if isinstance(location_data.get("coordinates"), dict) else None
                )
            return False  # Close modal
        except Exception as e:
            logger.error(f"Error adding favorite from marker: {e}")
    return no_update


@callback(
    [Output("marker-action-modal", "is_open", allow_duplicate=True), Output("selected-location", "data", allow_duplicate=True)],
    Input("marker-view-map-btn", "n_clicks"),
    State("clicked-location", "data"),
    prevent_initial_call=True
)
def view_location_on_map(n_clicks, location_data):
    """Select location and close modal to view on map"""
    if n_clicks and location_data:
        return False, location_data  # Close modal and select location
    return no_update, no_update


@callback(
    Output("marker-action-modal", "is_open", allow_duplicate=True),
    Input("marker-close-btn", "n_clicks"),
    prevent_initial_call=True
)
def close_marker_modal(n_clicks):
    """Close marker action modal"""
    if n_clicks:
        return False
    return no_update


@callback(
    [Output("marker-action-modal", "is_open", allow_duplicate=True), 
     Output("marker-generate-report-btn", "children", allow_duplicate=True),
     Output("download-report", "data")],
    Input("marker-generate-report-btn", "n_clicks"),
    State("clicked-location", "data"),
    prevent_initial_call=True
)
def generate_smart_report(n_clicks, location_data):
    """Generate comprehensive smart report with geospatial and meteorological data and trigger download"""
    if not n_clicks or not location_data:
        return no_update, no_update, no_update
    
    try:
        # Get coordinates
        coords = location_data.get("coordinates", {})
        lat = coords.get("latitude") if isinstance(coords, dict) else None
        lon = coords.get("longitude") if isinstance(coords, dict) else None
        
        # Fetch weather data if available
        weather_data = None
        forecast_data = None
        weather_analysis = None
        
        if lat and lon and config.WEATHER_API_KEY:
            try:
                weather_data = weather_client.get_current_weather(lat, lon)
                forecast_data = weather_client.get_forecast(lat, lon, days=3)
                if weather_data:
                    aqi = location_data.get("max_aqi", 0)
                    weather_analysis = weather_client.analyze_weather_air_quality_correlation(weather_data, aqi)
            except Exception as e:
                logger.error(f"Error fetching weather for report: {e}")
        
        # Generate insights
        insights = []
        if weather_analysis:
            insights.extend(weather_analysis.get("recommendations", []))
        
        # Generate the enhanced report
        report_path = report_gen.generate_location_report(
            location_data=location_data,
            weather_data=weather_data,
            forecast_data=forecast_data,
            weather_analysis=weather_analysis,
            insights=insights if insights else None
        )
        
        logger.info(f"Smart report generated: {report_path}")
        
        # Read the file and prepare for download
        report_file = Path(report_path)
        if report_file.exists():
            # Read file as binary
            with open(report_file, 'rb') as f:
                file_content = f.read()
            
            # Encode to base64 for download
            file_base64 = base64.b64encode(file_content).decode()
            
            # Get filename for download
            filename = report_file.name
            
            # Return: close modal, update button, trigger download
            return False, [  # Close modal
                html.I(className="fas fa-check me-2"),
                "Report Downloaded!"
            ], dict(
                content=file_base64,
                filename=filename,
                base64=True,
                type="application/pdf"
            )
        else:
            logger.error(f"Report file not found: {report_path}")
            return no_update, [
                html.I(className="fas fa-exclamation-triangle me-2"),
                "Error: File not found"
            ], no_update
        
    except Exception as e:
        logger.error(f"Error generating smart report: {e}")
        return no_update, [
            html.I(className="fas fa-exclamation-triangle me-2"),
            "Error generating report"
        ], no_update


if __name__ == "__main__":
    app.run_server(debug=config.FLASK_DEBUG, host=config.HOST, port=config.PORT)
