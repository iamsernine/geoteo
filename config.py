"""
AirWatch Configuration Module
Handles all application configuration and environment variables
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
EXPORTS_DIR = BASE_DIR / "exports"
CACHE_DIR = DATA_DIR / "cache"

# Create directories if they don't exist
for dir_path in [DATA_DIR, LOGS_DIR, EXPORTS_DIR, CACHE_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# API Configuration
OPENAQ_API_KEY = os.getenv("OPENAQ_API_KEY", "")
OPENAQ_BASE_URL = "https://api.openaq.org/v3"

# WeatherAPI Configuration (Get free key from weatherapi.com)
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
WEATHER_BASE_URL = "http://api.weatherapi.com/v1"

# OpenAI Configuration (For Smart Analytics)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")  # Use gpt-4o-mini for cost efficiency

# Flask Configuration
FLASK_ENV = os.getenv("FLASK_ENV", "development")
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "True") == "True"
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8050"))

# Cache Configuration
CACHE_TYPE = os.getenv("CACHE_TYPE", "disk")
CACHE_TIMEOUT = int(os.getenv("CACHE_TIMEOUT", "300"))  # 5 minutes

# Logging Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = LOGS_DIR / "airwatch.log"

# Data Refresh Configuration
DATA_REFRESH_INTERVAL = int(os.getenv("DATA_REFRESH_INTERVAL", "300"))  # 5 minutes

# Mapbox Configuration (Optional)
MAPBOX_TOKEN = os.getenv("MAPBOX_TOKEN", "")

# Air Quality Index (AQI) Thresholds
AQI_THRESHOLDS = {
    "pm25": [
        (0, 12, "Good", "#00e400"),
        (12.1, 35.4, "Moderate", "#ffff00"),
        (35.5, 55.4, "Unhealthy for Sensitive Groups", "#ff7e00"),
        (55.5, 150.4, "Unhealthy", "#ff0000"),
        (150.5, 250.4, "Very Unhealthy", "#8f3f97"),
        (250.5, float('inf'), "Hazardous", "#7e0023"),
    ],
    "pm10": [
        (0, 54, "Good", "#00e400"),
        (55, 154, "Moderate", "#ffff00"),
        (155, 254, "Unhealthy for Sensitive Groups", "#ff7e00"),
        (255, 354, "Unhealthy", "#ff0000"),
        (355, 424, "Very Unhealthy", "#8f3f97"),
        (425, float('inf'), "Hazardous", "#7e0023"),
    ],
    "no2": [
        (0, 53, "Good", "#00e400"),
        (54, 100, "Moderate", "#ffff00"),
        (101, 360, "Unhealthy for Sensitive Groups", "#ff7e00"),
        (361, 649, "Unhealthy", "#ff0000"),
        (650, 1249, "Very Unhealthy", "#8f3f97"),
        (1250, float('inf'), "Hazardous", "#7e0023"),
    ],
    "o3": [
        (0, 54, "Good", "#00e400"),
        (55, 70, "Moderate", "#ffff00"),
        (71, 85, "Unhealthy for Sensitive Groups", "#ff7e00"),
        (86, 105, "Unhealthy", "#ff0000"),
        (106, 200, "Very Unhealthy", "#8f3f97"),
        (201, float('inf'), "Hazardous", "#7e0023"),
    ],
}

# Health Recommendations
HEALTH_RECOMMENDATIONS = {
    "Good": {
        "general": "Air quality is satisfactory, and air pollution poses little or no risk.",
        "sensitive": "Enjoy your outdoor activities!",
        "icon": "✅"
    },
    "Moderate": {
        "general": "Air quality is acceptable. However, there may be a risk for some people.",
        "sensitive": "Unusually sensitive people should consider limiting prolonged outdoor exertion.",
        "icon": "⚠️"
    },
    "Unhealthy for Sensitive Groups": {
        "general": "Members of sensitive groups may experience health effects.",
        "sensitive": "People with respiratory or heart disease, children, and older adults should limit prolonged outdoor exertion.",
        "icon": "🔶"
    },
    "Unhealthy": {
        "general": "Some members of the general public may experience health effects.",
        "sensitive": "People with respiratory or heart disease, children, and older adults should avoid prolonged outdoor exertion. Everyone else should limit prolonged outdoor exertion.",
        "icon": "🔴"
    },
    "Very Unhealthy": {
        "general": "Health alert: The risk of health effects is increased for everyone.",
        "sensitive": "People with respiratory or heart disease, children, and older adults should avoid all outdoor exertion. Everyone else should limit outdoor exertion.",
        "icon": "🟣"
    },
    "Hazardous": {
        "general": "Health warning of emergency conditions: everyone is more likely to be affected.",
        "sensitive": "Everyone should avoid all outdoor exertion.",
        "icon": "⚫"
    }
}

# Major Cities for Quick Access
MAJOR_CITIES = [
    {"name": "Paris", "country": "FR", "lat": 48.8566, "lon": 2.3522},
    {"name": "London", "country": "GB", "lat": 51.5074, "lon": -0.1278},
    {"name": "New York", "country": "US", "lat": 40.7128, "lon": -74.0060},
    {"name": "Tokyo", "country": "JP", "lat": 35.6762, "lon": 139.6503},
    {"name": "Beijing", "country": "CN", "lat": 39.9042, "lon": 116.4074},
    {"name": "Delhi", "country": "IN", "lat": 28.7041, "lon": 77.1025},
    {"name": "Mumbai", "country": "IN", "lat": 19.0760, "lon": 72.8777},
    {"name": "São Paulo", "country": "BR", "lat": -23.5505, "lon": -46.6333},
    {"name": "Mexico City", "country": "MX", "lat": 19.4326, "lon": -99.1332},
    {"name": "Cairo", "country": "EG", "lat": 30.0444, "lon": 31.2357},
    {"name": "Los Angeles", "country": "US", "lat": 34.0522, "lon": -118.2437},
    {"name": "Sydney", "country": "AU", "lat": -33.8688, "lon": 151.2093},
]

# Pollutant Display Names
POLLUTANT_NAMES = {
    "pm25": "PM2.5",
    "pm10": "PM10",
    "no2": "NO₂",
    "o3": "O₃",
    "so2": "SO₂",
    "co": "CO",
}

# Pollutant Units
POLLUTANT_UNITS = {
    "pm25": "µg/m³",
    "pm10": "µg/m³",
    "no2": "ppb",
    "o3": "ppb",
    "so2": "ppb",
    "co": "ppm",
}
