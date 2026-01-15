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
    
    def __init__(self, api_key: Optional[str] = None, db: Optional[Any] = None):
        """
        Initialize OpenAQ API client
        
        Args:
            api_key: OpenAQ API key (optional, uses config or database if not provided)
            db: Database instance to check for stored API keys
        """
        # Try to get API key from: provided > config > database
        self.api_key = api_key
        if not self.api_key:
            self.api_key = config.OPENAQ_API_KEY
        if not self.api_key and db:
            try:
                self.api_key = db.get_api_key("openaq")
            except Exception as e:
                logger.debug(f"Could not get API key from database: {e}")
        
        # Clean up API key - remove whitespace and quotes
        if self.api_key:
            self.api_key = self.api_key.strip().strip('"').strip("'")
        
        # Warn if API key looks like OpenAI key (starts with sk-)
        if self.api_key and self.api_key.startswith("sk-"):
            logger.warning("API key format looks like OpenAI key (starts with 'sk-'). OpenAQ API keys have a different format.")
            logger.warning("Please verify you're using the correct API key from https://platform.openaq.org/")
        
        self.base_url = config.OPENAQ_BASE_URL
        self.headers = {}
        
        if self.api_key:
            # OpenAQ API v3 uses X-API-Key header
            self.headers["X-API-Key"] = self.api_key
            # Log first and last 4 chars for debugging (without exposing full key)
            key_preview = f"{self.api_key[:4]}...{self.api_key[-4:]}" if len(self.api_key) > 8 else "***"
            logger.info(f"OpenAQ API client initialized with API key: {key_preview}")
        else:
            logger.warning("OpenAQ API client initialized without API key - some endpoints may require authentication")
    
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
            # Log headers (without exposing full API key)
            debug_headers = {k: (v[:4] + "..." + v[-4:] if len(v) > 8 else "***") if "key" in k.lower() else v 
                           for k, v in self.headers.items()}
            logger.debug(f"Request headers: {debug_headers}")
            response = requests.get(url, headers=self.headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            logger.debug(f"Received {len(data.get('results', []))} results")
            return data
            
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if hasattr(e, 'response') else None
            if status_code == 401:
                logger.error(f"OpenAQ API authentication failed (401). Please check your API key in Settings or .env file.")
                logger.error(f"Get your API key from: https://platform.openaq.org/")
                # Try to get response body for more details
                try:
                    if hasattr(e, 'response') and e.response.text:
                        error_detail = e.response.json() if e.response.headers.get('content-type', '').startswith('application/json') else e.response.text[:200]
                        logger.error(f"API error details: {error_detail}")
                except:
                    pass
            elif status_code == 403:
                logger.error(f"OpenAQ API access forbidden (403). Your API key may not have permission for this endpoint.")
            else:
                logger.error(f"API request failed with status {status_code}: {e}")
            return {"results": [], "meta": {}, "error": str(e), "status_code": status_code}
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
