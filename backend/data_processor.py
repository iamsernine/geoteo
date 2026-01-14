"""
Data Processor
Processes air quality data, calculates AQI, and generates insights
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from loguru import logger
import config


class DataProcessor:
    """Processes and analyzes air quality data"""
    
    def __init__(self):
        """Initialize data processor"""
        self.aqi_thresholds = config.AQI_THRESHOLDS
        self.health_recommendations = config.HEALTH_RECOMMENDATIONS
        logger.info("Data processor initialized")
    
    def calculate_aqi(self, pollutant: str, value: float) -> Tuple[int, str, str]:
        """
        Calculate Air Quality Index for a pollutant
        
        Args:
            pollutant: Pollutant name (pm25, pm10, no2, o3, etc.)
            value: Pollutant concentration value
            
        Returns:
            Tuple of (AQI value, category, color)
        """
        pollutant = pollutant.lower()
        
        if pollutant not in self.aqi_thresholds:
            logger.warning(f"Unknown pollutant: {pollutant}")
            return (0, "Unknown", "#cccccc")
        
        thresholds = self.aqi_thresholds[pollutant]
        
        for min_val, max_val, category, color in thresholds:
            if min_val <= value <= max_val:
                # Calculate AQI using linear interpolation
                # Simplified AQI calculation
                if category == "Good":
                    aqi = int((value / max_val) * 50)
                elif category == "Moderate":
                    aqi = int(50 + ((value - min_val) / (max_val - min_val)) * 50)
                elif category == "Unhealthy for Sensitive Groups":
                    aqi = int(100 + ((value - min_val) / (max_val - min_val)) * 50)
                elif category == "Unhealthy":
                    aqi = int(150 + ((value - min_val) / (max_val - min_val)) * 50)
                elif category == "Very Unhealthy":
                    aqi = int(200 + ((value - min_val) / (max_val - min_val)) * 100)
                else:  # Hazardous
                    aqi = int(300 + min((value - min_val) / 100, 200))
                
                return (aqi, category, color)
        
        # If value exceeds all thresholds
        return (500, "Hazardous", "#7e0023")
    
    def get_health_recommendation(self, category: str) -> Dict[str, str]:
        """
        Get health recommendation for AQI category
        
        Args:
            category: AQI category name
            
        Returns:
            Dictionary with general and sensitive group recommendations
        """
        return self.health_recommendations.get(category, {
            "general": "No data available",
            "sensitive": "No data available",
            "icon": "❓"
        })
    
    def get_aqi_category(self, aqi: int) -> str:
        """
        Get AQI category based on AQI value
        
        Args:
            aqi: Air Quality Index value (0-500)
            
        Returns:
            Category name string
        """
        if aqi <= 50:
            return "Good"
        elif aqi <= 100:
            return "Moderate"
        elif aqi <= 150:
            return "Unhealthy for Sensitive Groups"
        elif aqi <= 200:
            return "Unhealthy"
        elif aqi <= 300:
            return "Very Unhealthy"
        else:
            return "Hazardous"
    
    def get_aqi_color(self, aqi: int) -> str:
        """
        Get color code for AQI value
        
        Args:
            aqi: Air Quality Index value (0-500)
            
        Returns:
            Hex color code string
        """
        if aqi <= 50:
            return "#00e400"  # Green
        elif aqi <= 100:
            return "#ffff00"  # Yellow
        elif aqi <= 150:
            return "#ff7e00"  # Orange
        elif aqi <= 200:
            return "#ff0000"  # Red
        elif aqi <= 300:
            return "#8f3f97"  # Purple
        else:
            return "#7e0023"  # Maroon
    
    def process_location_data(self, location: Dict) -> Dict:
        """
        Process location data and calculate AQI
        
        Args:
            location: Location dictionary from API
            
        Returns:
            Processed location data with AQI
        """
        location_id = str(location.get("id", ""))
        processed = {
            "id": location.get("id"),
            "location_id": location_id,  # Add location_id for consistency
            "name": location.get("name", "Unknown"),
            "locality": location.get("locality", ""),
            "country": location.get("country", {}).get("name", "Unknown"),
            "country_code": location.get("country", {}).get("code", ""),
            "coordinates": location.get("coordinates", {}),
            "sensors": [],
            "max_aqi": 0,
            "max_aqi_category": "Good",
            "max_aqi_color": "#00e400",
            "pollutants": {}
        }
        
        # Process sensors
        for sensor in location.get("sensors", []):
            param = sensor.get("parameter", {})
            param_name = param.get("name", "").lower()
            
            processed["sensors"].append({
                "id": sensor.get("id"),
                "parameter": param_name,
                "display_name": config.POLLUTANT_NAMES.get(param_name, param_name.upper()),
                "units": param.get("units", "")
            })
        
        return processed
    
    def process_measurements(self, measurements: List[Dict], parameter: str) -> pd.DataFrame:
        """
        Process measurements into a pandas DataFrame
        
        Args:
            measurements: List of measurement dictionaries
            parameter: Parameter name
            
        Returns:
            DataFrame with processed measurements
        """
        if not measurements:
            return pd.DataFrame()
        
        df = pd.DataFrame(measurements)
        
        # Convert datetime
        if "datetime" in df.columns:
            df["datetime"] = pd.to_datetime(df["datetime"])
        
        # Calculate AQI for each measurement
        if "value" in df.columns:
            df[["aqi", "category", "color"]] = df["value"].apply(
                lambda x: pd.Series(self.calculate_aqi(parameter, x))
            )
        
        return df
    
    def aggregate_measurements(self, df: pd.DataFrame, freq: str = "H") -> pd.DataFrame:
        """
        Aggregate measurements by time frequency
        
        Args:
            df: DataFrame with measurements
            freq: Pandas frequency string (H=hourly, D=daily, W=weekly)
            
        Returns:
            Aggregated DataFrame
        """
        if df.empty or "datetime" not in df.columns:
            return df
        
        df = df.set_index("datetime")
        
        agg_dict = {
            "value": ["mean", "min", "max", "std"],
            "aqi": "mean"
        }
        
        aggregated = df.resample(freq).agg(agg_dict)
        aggregated.columns = ["_".join(col).strip() for col in aggregated.columns.values]
        
        return aggregated.reset_index()
    
    def calculate_statistics(self, df: pd.DataFrame) -> Dict:
        """
        Calculate statistics from measurements
        
        Args:
            df: DataFrame with measurements
            
        Returns:
            Dictionary with statistics
        """
        if df.empty or "value" not in df.columns:
            return {}
        
        stats = {
            "mean": float(df["value"].mean()),
            "median": float(df["value"].median()),
            "min": float(df["value"].min()),
            "max": float(df["value"].max()),
            "std": float(df["value"].std()),
            "count": int(len(df))
        }
        
        if "aqi" in df.columns:
            stats["avg_aqi"] = float(df["aqi"].mean())
            stats["max_aqi"] = float(df["aqi"].max())
        
        return stats
    
    def detect_trends(self, df: pd.DataFrame, window: int = 24) -> Dict:
        """
        Detect trends in air quality data
        
        Args:
            df: DataFrame with measurements
            window: Rolling window size
            
        Returns:
            Dictionary with trend information
        """
        if df.empty or "value" not in df.columns or len(df) < window:
            return {"trend": "insufficient_data"}
        
        # Calculate rolling mean
        df["rolling_mean"] = df["value"].rolling(window=window).mean()
        
        # Calculate trend (positive = increasing, negative = decreasing)
        recent_mean = df["rolling_mean"].iloc[-window:].mean()
        previous_mean = df["rolling_mean"].iloc[-2*window:-window].mean()
        
        if pd.isna(recent_mean) or pd.isna(previous_mean):
            return {"trend": "insufficient_data"}
        
        change_percent = ((recent_mean - previous_mean) / previous_mean) * 100
        
        if change_percent > 10:
            trend = "increasing"
        elif change_percent < -10:
            trend = "decreasing"
        else:
            trend = "stable"
        
        return {
            "trend": trend,
            "change_percent": float(change_percent),
            "recent_mean": float(recent_mean),
            "previous_mean": float(previous_mean)
        }
    
    def compare_locations(self, locations_data: List[Dict]) -> pd.DataFrame:
        """
        Compare multiple locations
        
        Args:
            locations_data: List of location dictionaries with measurements
            
        Returns:
            DataFrame with comparison data
        """
        comparison_data = []
        
        for loc in locations_data:
            comparison_data.append({
                "name": loc.get("name", "Unknown"),
                "country": loc.get("country", "Unknown"),
                "aqi": loc.get("max_aqi", 0),
                "category": loc.get("max_aqi_category", "Unknown"),
                "color": loc.get("max_aqi_color", "#cccccc")
            })
        
        df = pd.DataFrame(comparison_data)
        df = df.sort_values("aqi", ascending=False)
        
        return df
    
    def generate_insights(self, location_data: Dict, measurements_df: pd.DataFrame) -> List[str]:
        """
        Generate insights from location data and measurements
        
        Args:
            location_data: Processed location data
            measurements_df: DataFrame with measurements
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # AQI insight
        aqi = location_data.get("max_aqi", 0)
        category = location_data.get("max_aqi_category", "Unknown")
        insights.append(f"Current air quality is {category} with an AQI of {aqi}")
        
        # Statistics insights
        if not measurements_df.empty:
            stats = self.calculate_statistics(measurements_df)
            
            if stats.get("max") and stats.get("mean"):
                if stats["max"] > stats["mean"] * 1.5:
                    insights.append(f"Peak pollution levels are {stats['max']:.1f}, significantly higher than average")
            
            # Trend insights
            trends = self.detect_trends(measurements_df)
            if trends.get("trend") == "increasing":
                insights.append(f"Air quality is worsening (↑{abs(trends['change_percent']):.1f}%)")
            elif trends.get("trend") == "decreasing":
                insights.append(f"Air quality is improving (↓{abs(trends['change_percent']):.1f}%)")
            elif trends.get("trend") == "stable":
                insights.append("Air quality has been stable recently")
        
        return insights
