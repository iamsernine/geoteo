"""
WeatherAPI Client
Handles weather data retrieval for correlation with air quality
"""

import requests
from typing import Dict, Optional, Tuple
from loguru import logger
import config


class WeatherAPIClient:
    """Client for WeatherAPI.com to fetch meteorological data"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize WeatherAPI client
        
        Args:
            api_key: WeatherAPI key (optional, uses config if not provided)
        """
        self.api_key = api_key or getattr(config, 'WEATHER_API_KEY', '')
        self.base_url = "http://api.weatherapi.com/v1"
        logger.info("WeatherAPI client initialized")
    
    def _make_request(self, endpoint: str, params: Dict) -> Dict:
        """
        Make request to WeatherAPI
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}/{endpoint}"
        params["key"] = self.api_key
        
        try:
            logger.debug(f"WeatherAPI request: {endpoint} with params: {params}")
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"WeatherAPI response received")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"WeatherAPI request failed: {e}")
            return {}
    
    def get_current_weather(self, lat: float, lon: float) -> Dict:
        """
        Get current weather for coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with weather data
        """
        params = {
            "q": f"{lat},{lon}",
            "aqi": "yes"  # Include air quality data if available
        }
        
        data = self._make_request("current.json", params)
        
        if not data:
            return {}
        
        current = data.get("current", {})
        
        weather_data = {
            "temperature_c": current.get("temp_c"),
            "temperature_f": current.get("temp_f"),
            "feels_like_c": current.get("feelslike_c"),
            "feels_like_f": current.get("feelslike_f"),
            "humidity": current.get("humidity"),
            "wind_speed_kph": current.get("wind_kph"),
            "wind_speed_mph": current.get("wind_mph"),
            "wind_degree": current.get("wind_degree"),
            "wind_direction": current.get("wind_dir"),
            "pressure_mb": current.get("pressure_mb"),
            "pressure_in": current.get("pressure_in"),
            "precipitation_mm": current.get("precip_mm"),
            "precipitation_in": current.get("precip_in"),
            "cloud_cover": current.get("cloud"),
            "uv_index": current.get("uv"),
            "visibility_km": current.get("vis_km"),
            "visibility_miles": current.get("vis_miles"),
            "condition": current.get("condition", {}).get("text"),
            "condition_icon": current.get("condition", {}).get("icon"),
            "last_updated": current.get("last_updated")
        }
        
        return weather_data
    
    def get_forecast(self, lat: float, lon: float, days: int = 3) -> Dict:
        """
        Get weather forecast for coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            days: Number of forecast days (1-10)
            
        Returns:
            Dictionary with forecast data
        """
        params = {
            "q": f"{lat},{lon}",
            "days": min(days, 10),
            "aqi": "yes"
        }
        
        data = self._make_request("forecast.json", params)
        
        if not data:
            return {}
        
        forecast_days = data.get("forecast", {}).get("forecastday", [])
        
        forecast_data = []
        for day in forecast_days:
            day_data = {
                "date": day.get("date"),
                "max_temp_c": day.get("day", {}).get("maxtemp_c"),
                "min_temp_c": day.get("day", {}).get("mintemp_c"),
                "avg_temp_c": day.get("day", {}).get("avgtemp_c"),
                "max_wind_kph": day.get("day", {}).get("maxwind_kph"),
                "total_precip_mm": day.get("day", {}).get("totalprecip_mm"),
                "avg_humidity": day.get("day", {}).get("avghumidity"),
                "condition": day.get("day", {}).get("condition", {}).get("text"),
                "uv_index": day.get("day", {}).get("uv")
            }
            forecast_data.append(day_data)
        
        return {"forecast": forecast_data}
    
    def analyze_weather_air_quality_correlation(self, weather_data: Dict, aqi: float) -> Dict:
        """
        Analyze correlation between weather and air quality
        
        Args:
            weather_data: Weather data dictionary
            aqi: Air Quality Index
            
        Returns:
            Dictionary with correlation analysis
        """
        analysis = {
            "wind_impact": "unknown",
            "humidity_impact": "unknown",
            "temperature_impact": "unknown",
            "overall_conditions": "unknown",
            "recommendations": []
        }
        
        if not weather_data:
            return analysis
        
        wind_speed = weather_data.get("wind_speed_kph", 0)
        humidity = weather_data.get("humidity", 0)
        temperature = weather_data.get("temperature_c", 0)
        
        # Wind impact analysis
        if wind_speed > 20:
            analysis["wind_impact"] = "positive"
            analysis["recommendations"].append("Strong winds help disperse pollutants")
        elif wind_speed < 5:
            analysis["wind_impact"] = "negative"
            analysis["recommendations"].append("Low wind speed may trap pollutants")
        else:
            analysis["wind_impact"] = "neutral"
        
        # Humidity impact analysis
        if humidity > 70:
            analysis["humidity_impact"] = "negative"
            analysis["recommendations"].append("High humidity can worsen air quality perception")
        elif humidity < 30:
            analysis["humidity_impact"] = "negative"
            analysis["recommendations"].append("Low humidity may increase particle suspension")
        else:
            analysis["humidity_impact"] = "neutral"
        
        # Temperature impact analysis
        if temperature > 30:
            analysis["temperature_impact"] = "negative"
            analysis["recommendations"].append("High temperatures can increase ozone formation")
        elif temperature < 0:
            analysis["temperature_impact"] = "negative"
            analysis["recommendations"].append("Cold air can trap pollutants near ground")
        else:
            analysis["temperature_impact"] = "neutral"
        
        # Overall conditions
        negative_factors = sum([
            1 for impact in [analysis["wind_impact"], analysis["humidity_impact"], analysis["temperature_impact"]]
            if impact == "negative"
        ])
        
        if negative_factors >= 2:
            analysis["overall_conditions"] = "unfavorable"
        elif negative_factors == 0:
            analysis["overall_conditions"] = "favorable"
        else:
            analysis["overall_conditions"] = "moderate"
        
        return analysis
    
    def get_wind_rose_data(self, lat: float, lon: float) -> Dict:
        """
        Get wind direction and speed for wind rose visualization
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Dictionary with wind data
        """
        weather = self.get_current_weather(lat, lon)
        
        if not weather:
            return {}
        
        return {
            "wind_speed": weather.get("wind_speed_kph", 0),
            "wind_direction": weather.get("wind_direction", "N"),
            "wind_degree": weather.get("wind_degree", 0)
        }
