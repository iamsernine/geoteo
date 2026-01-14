"""
OpenAQ API Client
Handles all interactions with the OpenAQ API
"""

import requests
from typing import Dict, List, Optional, Any
from loguru import logger
import config


class OpenAQClient:
    """Client for interacting with OpenAQ API v3"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAQ API client
        
        Args:
            api_key: OpenAQ API key (optional, uses config if not provided)
        """
        self.api_key = api_key or config.OPENAQ_API_KEY
        self.base_url = config.OPENAQ_BASE_URL
        self.headers = {}
        
        if self.api_key:
            self.headers["X-API-Key"] = self.api_key
        
        logger.info("OpenAQ API client initialized")
    
    def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Make a request to the OpenAQ API
        
        Args:
            endpoint: API endpoint (e.g., '/locations')
            params: Query parameters
            
        Returns:
            JSON response as dictionary
        """
        url = f"{self.base_url}{endpoint}"
        
        try:
            logger.debug(f"Making request to {url} with params: {params}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Received {len(data.get('results', []))} results")
            return data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return {"results": [], "meta": {}, "error": str(e)}
    
    def get_locations(self, 
                     limit: int = 100, 
                     country: Optional[str] = None,
                     coordinates: Optional[tuple] = None,
                     radius: Optional[int] = None) -> List[Dict]:
        """
        Get air quality monitoring locations
        
        Args:
            limit: Maximum number of locations to return
            country: Country code (e.g., 'US', 'FR')
            coordinates: (latitude, longitude) tuple for geospatial search
            radius: Search radius in meters (requires coordinates)
            
        Returns:
            List of location dictionaries
        """
        params = {"limit": limit}
        
        if country:
            params["country"] = country
        
        if coordinates and len(coordinates) == 2:
            params["coordinates"] = f"{coordinates[0]},{coordinates[1]}"
            if radius:
                params["radius"] = radius
        
        data = self._make_request("/locations", params)
        return data.get("results", [])
    
    def get_location_by_id(self, location_id: int) -> Optional[Dict]:
        """
        Get details for a specific location
        
        Args:
            location_id: OpenAQ location ID
            
        Returns:
            Location dictionary or None if not found
        """
        data = self._make_request(f"/locations/{location_id}")
        results = data.get("results", [])
        return results[0] if results else None
    
    def get_latest_measurements(self, location_id: int) -> Dict:
        """
        Get latest measurements for a location
        
        Args:
            location_id: OpenAQ location ID
            
        Returns:
            Dictionary with latest measurements
        """
        data = self._make_request(f"/locations/{location_id}/latest")
        return data
    
    def get_measurements(self, 
                        sensor_id: int,
                        date_from: Optional[str] = None,
                        date_to: Optional[str] = None,
                        limit: int = 1000) -> List[Dict]:
        """
        Get historical measurements for a sensor
        
        Args:
            sensor_id: Sensor ID
            date_from: Start date (ISO format)
            date_to: End date (ISO format)
            limit: Maximum number of measurements
            
        Returns:
            List of measurement dictionaries
        """
        params = {"limit": limit}
        
        if date_from:
            params["date_from"] = date_from
        if date_to:
            params["date_to"] = date_to
        
        data = self._make_request(f"/sensors/{sensor_id}/measurements", params)
        return data.get("results", [])
    
    def get_countries(self) -> List[Dict]:
        """
        Get list of countries with air quality data
        
        Returns:
            List of country dictionaries
        """
        data = self._make_request("/countries", {"limit": 300})
        return data.get("results", [])
    
    def search_locations_by_name(self, name: str, limit: int = 10) -> List[Dict]:
        """
        Search locations by name
        
        Args:
            name: Location name to search for
            limit: Maximum number of results
            
        Returns:
            List of matching locations
        """
        params = {"name": name, "limit": limit}
        data = self._make_request("/locations", params)
        return data.get("results", [])
    
    def get_locations_by_bbox(self, 
                              min_lat: float, 
                              min_lon: float,
                              max_lat: float, 
                              max_lon: float,
                              limit: int = 100) -> List[Dict]:
        """
        Get locations within a bounding box
        
        Args:
            min_lat: Minimum latitude
            min_lon: Minimum longitude
            max_lat: Maximum latitude
            max_lon: Maximum longitude
            limit: Maximum number of locations
            
        Returns:
            List of locations within bounding box
        """
        params = {
            "bbox": f"{min_lon},{min_lat},{max_lon},{max_lat}",
            "limit": limit
        }
        data = self._make_request("/locations", params)
        return data.get("results", [])
    
    def get_parameters(self) -> List[Dict]:
        """
        Get list of available air quality parameters
        
        Returns:
            List of parameter dictionaries
        """
        data = self._make_request("/parameters")
        return data.get("results", [])
