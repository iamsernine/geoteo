"""
AirWatch V2 - Mobile-Style App with Enhanced Features
Modern UI with WeatherAPI integration and advanced insights
"""

import dash
from dash import dcc, html, Input, Output, State, callback, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta
from loguru import logger
import sys

# Import backend modules
from backend.api_client import OpenAQClient
from backend.data_processor import DataProcessor
from backend.cache_manager import CacheManager
from backend.weather_client import WeatherAPIClient
import config

# Configure logging
logger.remove()
logger.add(sys.stderr, level=config.LOG_LEVEL)
logger.add(config.LOG_FILE, rotation="10 MB", retention="7 days", level=config.LOG_LEVEL)

# Initialize backend components
api_client = OpenAQClient()
data_processor = DataProcessor()
cache_manager = CacheManager()
weather_client = WeatherAPIClient()

# Initialize Dash app with modern theme
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
    title="AirWatch - Smart Air Quality Monitor"
)

server = app.server

# Mobile-style App Layout
app.layout = dbc.Container([
    # Top App Bar (Mobile-style)
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-wind", style={"fontSize": "24px", "color": "#1976d2"}),
                    html.Span("AirWatch", style={
                        "fontSize": "20px",
                        "fontWeight": "600",
                        "marginLeft": "12px",
                        "color": "#1976d2"
                    })
                ], style={"display": "flex", "alignItems": "center"})
            ], width=6),
            dbc.Col([
                html.Div([
                    dbc.Button(
                        html.I(className="fas fa-search"),
                        id="search-btn",
                        color="light",
                        size="sm",
                        className="me-2",
                        style={"borderRadius": "50%", "width": "40px", "height": "40px"}
                    ),
                    dbc.Button(
                        html.I(className="fas fa-bell"),
                        id="notifications-btn",
                        color="light",
                        size="sm",
                        className="me-2",
                        style={"borderRadius": "50%", "width": "40px", "height": "40px"}
                    ),
                    dbc.Button(
                        html.I(className="fas fa-moon", id="theme-icon"),
                        id="theme-toggle",
                        color="light",
                        size="sm",
                        style={"borderRadius": "50%", "width": "40px", "height": "40px"}
                    )
                ], style={"display": "flex", "justifyContent": "flex-end"})
            ], width=6)
        ], className="align-items-center")
    ], style={
        "backgroundColor": "white",
        "padding": "16px 20px",
        "boxShadow": "0 2px 8px rgba(0,0,0,0.1)",
        "position": "sticky",
        "top": "0",
        "zIndex": "1000",
        "marginBottom": "16px"
    }),
    
    # Search Modal
    dbc.Modal([
        dbc.ModalHeader("Search Location"),
        dbc.ModalBody([
            dbc.Input(
                id="search-input",
                placeholder="Search city, country...",
                type="text",
                className="mb-3"
            ),
            html.Div(id="search-results")
        ])
    ], id="search-modal", size="lg"),
    
    # Current Location Card (Hero Section)
    dbc.Card([
        dbc.CardBody([
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H2(id="current-location", children="Global", style={
                            "fontSize": "28px",
                            "fontWeight": "600",
                            "marginBottom": "4px"
                        }),
                        html.P(id="current-time", children=datetime.now().strftime("%A, %B %d"), style={
                            "color": "#666",
                            "marginBottom": "20px"
                        })
                    ])
                ], width=12),
            ]),
            dbc.Row([
                dbc.Col([
                    html.Div([
                        html.H1(id="main-aqi", children="--", style={
                            "fontSize": "72px",
                            "fontWeight": "700",
                            "marginBottom": "0",
                            "lineHeight": "1"
                        }),
                        html.P("Air Quality Index", style={
                            "fontSize": "14px",
                            "color": "#666",
                            "marginTop": "8px"
                        })
                    ])
                ], width=6),
                dbc.Col([
                    html.Div(id="aqi-gauge", style={"height": "120px"})
                ], width=6)
            ]),
            html.Div(id="aqi-status-badge", style={"marginTop": "16px"}),
            
            # Weather Info
            html.Div(id="weather-info", style={"marginTop": "20px"})
        ])
    ], className="mb-3", style={
        "background": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
        "color": "white",
        "borderRadius": "16px",
        "boxShadow": "0 4px 20px rgba(102, 126, 234, 0.4)"
    }),
    
    # Quick Stats Grid
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-map-marker-alt", style={"fontSize": "24px", "color": "#1976d2"}),
                        html.H3(id="stat-stations", children="0", style={"fontSize": "28px", "fontWeight": "700", "margin": "8px 0"}),
                        html.P("Stations", style={"fontSize": "12px", "color": "#666", "marginBottom": "0"})
                    ], style={"textAlign": "center"})
                ])
            ], style={"borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})
        ], width=3, xs=6, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-globe", style={"fontSize": "24px", "color": "#4caf50"}),
                        html.H3(id="stat-countries", children="0", style={"fontSize": "28px", "fontWeight": "700", "margin": "8px 0"}),
                        html.P("Countries", style={"fontSize": "12px", "color": "#666", "marginBottom": "0"})
                    ], style={"textAlign": "center"})
                ])
            ], style={"borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})
        ], width=3, xs=6, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-wind", style={"fontSize": "24px", "color": "#ff9800"}),
                        html.H3(id="stat-wind", children="--", style={"fontSize": "28px", "fontWeight": "700", "margin": "8px 0"}),
                        html.P("Wind km/h", style={"fontSize": "12px", "color": "#666", "marginBottom": "0"})
                    ], style={"textAlign": "center"})
                ])
            ], style={"borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})
        ], width=3, xs=6, className="mb-3"),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div([
                        html.I(className="fas fa-tint", style={"fontSize": "24px", "color": "#2196f3"}),
                        html.H3(id="stat-humidity", children="--", style={"fontSize": "28px", "fontWeight": "700", "margin": "8px 0"}),
                        html.P("Humidity %", style={"fontSize": "12px", "color": "#666", "marginBottom": "0"})
                    ], style={"textAlign": "center"})
                ])
            ], style={"borderRadius": "12px", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"})
        ], width=3, xs=6, className="mb-3")
    ]),
    
    # Map Visualization Card
    dbc.Card([
        dbc.CardHeader([
            dbc.Row([
                dbc.Col([
                    html.H5("Air Quality Map", style={"marginBottom": "0", "fontWeight": "600"})
                ], width=6),
                dbc.Col([
                    dbc.ButtonGroup([
                        dbc.Button("Heatmap", id="btn-heatmap", size="sm", outline=True, color="primary"),
                        dbc.Button("Markers", id="btn-markers", size="sm", color="primary"),
                        dbc.Button("Density", id="btn-density", size="sm", outline=True, color="primary")
                    ], size="sm")
                ], width=6, style={"textAlign": "right"})
            ])
        ], style={"backgroundColor": "#f8f9fa", "borderBottom": "1px solid #dee2e6"}),
        dbc.CardBody([
            dcc.Loading(
                id="loading-map",
                type="circle",
                children=[
                    dcc.Graph(
                        id="main-map",
                        style={"height": "400px"},
                        config={"displayModeBar": False, "scrollZoom": True}
                    )
                ]
            )
        ], style={"padding": "0"})
    ], className="mb-3", style={"borderRadius": "12px", "overflow": "hidden", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
    
    # Insights & Analytics Tabs
    dbc.Card([
        dbc.CardHeader([
            dbc.Tabs(
                id="main-tabs",
                active_tab="insights",
                children=[
                    dbc.Tab(
                        label=html.Div([html.I(className="fas fa-lightbulb me-2"), "Insights"], style={"display": "inline-flex", "alignItems": "center"}),
                        tab_id="insights",
                        tab_style={"borderRadius": "8px 8px 0 0"}
                    ),
                    dbc.Tab(
                        label=html.Div([html.I(className="fas fa-chart-line me-2"), "Trends"], style={"display": "inline-flex", "alignItems": "center"}),
                        tab_id="trends"
                    ),
                    dbc.Tab(
                        label=html.Div([html.I(className="fas fa-balance-scale me-2"), "Compare"], style={"display": "inline-flex", "alignItems": "center"}),
                        tab_id="compare"
                    ),
                    dbc.Tab(
                        label=html.Div([html.I(className="fas fa-download me-2"), "Export"], style={"display": "inline-flex", "alignItems": "center"}),
                        tab_id="export"
                    )
                ],
                style={"borderBottom": "none"}
            )
        ], style={"backgroundColor": "#f8f9fa", "borderBottom": "1px solid #dee2e6"}),
        dbc.CardBody([
            html.Div(id="tab-content")
        ])
    ], className="mb-3", style={"borderRadius": "12px", "overflow": "hidden", "boxShadow": "0 2px 8px rgba(0,0,0,0.1)"}),
    
    # Bottom Navigation (Mobile-style)
    html.Div([
        dbc.Row([
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-home", style={"fontSize": "24px"}),
                    html.P("Home", style={"fontSize": "10px", "marginTop": "4px", "marginBottom": "0"})
                ], style={"textAlign": "center", "color": "#1976d2", "cursor": "pointer"})
            ], width=3),
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-map", style={"fontSize": "24px"}),
                    html.P("Map", style={"fontSize": "10px", "marginTop": "4px", "marginBottom": "0"})
                ], style={"textAlign": "center", "color": "#666", "cursor": "pointer"})
            ], width=3),
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-chart-bar", style={"fontSize": "24px"}),
                    html.P("Stats", style={"fontSize": "10px", "marginTop": "4px", "marginBottom": "0"})
                ], style={"textAlign": "center", "color": "#666", "cursor": "pointer"})
            ], width=3),
            dbc.Col([
                html.Div([
                    html.I(className="fas fa-cog", style={"fontSize": "24px"}),
                    html.P("Settings", style={"fontSize": "10px", "marginTop": "4px", "marginBottom": "0"})
                ], style={"textAlign": "center", "color": "#666", "cursor": "pointer"})
            ], width=3)
        ])
    ], style={
        "backgroundColor": "white",
        "padding": "12px 0",
        "boxShadow": "0 -2px 8px rgba(0,0,0,0.1)",
        "position": "fixed",
        "bottom": "0",
        "left": "0",
        "right": "0",
        "zIndex": "1000"
    }),
    
    # Hidden components
    dcc.Store(id="locations-data"),
    dcc.Store(id="weather-data"),
    dcc.Store(id="map-type-store", data="markers"),
    dcc.Store(id="theme-store", data="light"),
    dcc.Store(id="selected-location", data=None),
    dcc.Interval(id="interval-component", interval=300000, n_intervals=0)  # 5 min
    
], fluid=True, style={
    "paddingBottom": "80px",  # Space for bottom nav
    "fontFamily": "'Inter', sans-serif",
    "backgroundColor": "#f5f5f5"
}, className="px-3 py-0")


# Callbacks will be added here...

if __name__ == "__main__":
    app.run_server(debug=config.FLASK_DEBUG, host=config.HOST, port=config.PORT)
