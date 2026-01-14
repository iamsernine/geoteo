"""
Database Module
SQLite database for storing settings, favorites, history, and user data
"""

import sqlite3
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from loguru import logger
import config


class Database:
    """SQLite database manager for AirWatch"""
    
    def __init__(self, db_path: Optional[Path] = None):
        """Initialize database connection"""
        if db_path is None:
            db_path = config.DATA_DIR / "airwatch.db"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        logger.info(f"Database initialized at {self.db_path}")
    
    def _get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """Initialize database schema"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Favorites table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS favorites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id TEXT NOT NULL,
                name TEXT NOT NULL,
                country TEXT,
                latitude REAL,
                longitude REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(location_id)
            )
        """)
        
        # History table (recently viewed locations)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                location_id TEXT NOT NULL,
                name TEXT NOT NULL,
                country TEXT,
                latitude REAL,
                longitude REAL,
                viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS preferences (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # API keys table (encrypted storage)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                service TEXT PRIMARY KEY,
                key_value TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Cache metadata table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS cache_metadata (
                cache_key TEXT PRIMARY KEY,
                data_type TEXT,
                size_bytes INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                expires_at TIMESTAMP
            )
        """)
        
        conn.commit()
        conn.close()
        
        # Initialize default settings
        self._init_default_settings()
    
    def _init_default_settings(self):
        """Initialize default settings"""
        defaults = {
            "theme": "light",
            "refresh_interval": "300",
            "map_type": "markers",
            "default_country": "",
            "notifications_enabled": "true",
            "aqi_alert_threshold": "150",
            "language": "en"
        }
        
        for key, value in defaults.items():
            if not self.get_setting(key):
                self.set_setting(key, value)
    
    # Settings methods
    def get_setting(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a setting value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default
    
    def set_setting(self, key: str, value: str):
        """Set a setting value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO settings (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, value, datetime.now().isoformat()))
        conn.commit()
        conn.close()
    
    def get_all_settings(self) -> Dict[str, str]:
        """Get all settings"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        rows = cursor.fetchall()
        conn.close()
        return {row[0]: row[1] for row in rows}
    
    # API Keys methods
    def save_api_key(self, service: str, key_value: str):
        """Save an API key"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO api_keys (service, key_value, updated_at)
            VALUES (?, ?, ?)
        """, (service, key_value, datetime.now().isoformat()))
        conn.commit()
        conn.close()
        logger.info(f"API key saved for service: {service}")
    
    def get_api_key(self, service: str) -> Optional[str]:
        """Get an API key"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT key_value FROM api_keys WHERE service = ? AND is_active = 1", (service,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else None
    
    def get_all_api_keys(self) -> Dict[str, Dict[str, Any]]:
        """Get all API keys (without values for security)"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT service, is_active, created_at, updated_at FROM api_keys")
        rows = cursor.fetchall()
        conn.close()
        return {
            row[0]: {
                "is_active": bool(row[1]),
                "created_at": row[2],
                "updated_at": row[3]
            }
            for row in rows
        }
    
    def delete_api_key(self, service: str):
        """Delete an API key"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM api_keys WHERE service = ?", (service,))
        conn.commit()
        conn.close()
        logger.info(f"API key deleted for service: {service}")
    
    # Favorites methods
    def add_favorite(self, location_id: str, name: str, country: str = None, 
                    latitude: float = None, longitude: float = None) -> bool:
        """Add a location to favorites"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO favorites (location_id, name, country, latitude, longitude)
                VALUES (?, ?, ?, ?, ?)
            """, (location_id, name, country, latitude, longitude))
            conn.commit()
            conn.close()
            logger.info(f"Added favorite: {name}")
            return True
        except Exception as e:
            logger.error(f"Error adding favorite: {e}")
            return False
    
    def remove_favorite(self, location_id: str) -> bool:
        """Remove a location from favorites"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("DELETE FROM favorites WHERE location_id = ?", (location_id,))
            conn.commit()
            conn.close()
            logger.info(f"Removed favorite: {location_id}")
            return True
        except Exception as e:
            logger.error(f"Error removing favorite: {e}")
            return False
    
    def get_favorites(self) -> List[Dict[str, Any]]:
        """Get all favorites"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT location_id, name, country, latitude, longitude, created_at
            FROM favorites
            ORDER BY created_at DESC
        """)
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "location_id": row[0],
                "name": row[1],
                "country": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "created_at": row[5]
            }
            for row in rows
        ]
    
    def is_favorite(self, location_id: str) -> bool:
        """Check if location is favorite"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM favorites WHERE location_id = ?", (location_id,))
        row = cursor.fetchone()
        conn.close()
        return row is not None
    
    # History methods
    def add_to_history(self, location_id: str, name: str, country: str = None,
                      latitude: float = None, longitude: float = None):
        """Add location to history"""
        try:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO history (location_id, name, country, latitude, longitude)
                VALUES (?, ?, ?, ?, ?)
            """, (location_id, name, country, latitude, longitude))
            conn.commit()
            conn.close()
        except Exception as e:
            logger.error(f"Error adding to history: {e}")
    
    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent history"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT location_id, name, country, latitude, longitude, viewed_at
            FROM history
            ORDER BY viewed_at DESC
            LIMIT ?
        """, (limit,))
        rows = cursor.fetchall()
        conn.close()
        return [
            {
                "location_id": row[0],
                "name": row[1],
                "country": row[2],
                "latitude": row[3],
                "longitude": row[4],
                "viewed_at": row[5]
            }
            for row in rows
        ]
    
    def clear_history(self):
        """Clear all history"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM history")
        conn.commit()
        conn.close()
        logger.info("History cleared")
    
    # Preferences methods
    def get_preference(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get a preference value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT value FROM preferences WHERE key = ?", (key,))
        row = cursor.fetchone()
        conn.close()
        return row[0] if row else default
    
    def set_preference(self, key: str, value: str):
        """Set a preference value"""
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO preferences (key, value, updated_at)
            VALUES (?, ?, ?)
        """, (key, value, datetime.now().isoformat()))
        conn.commit()
        conn.close()


