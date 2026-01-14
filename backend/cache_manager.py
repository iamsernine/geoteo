"""
Cache Manager
Handles caching of API responses and processed data
"""

import json
import hashlib
from typing import Any, Optional
from pathlib import Path
from diskcache import Cache
from loguru import logger
import config


class CacheManager:
    """Manages caching of API responses and processed data"""
    
    def __init__(self, cache_dir: Optional[Path] = None, timeout: int = 300):
        """
        Initialize cache manager
        
        Args:
            cache_dir: Directory for cache storage
            timeout: Default cache timeout in seconds
        """
        self.cache_dir = cache_dir or config.CACHE_DIR
        self.timeout = timeout
        self.cache = Cache(str(self.cache_dir))
        logger.info(f"Cache manager initialized at {self.cache_dir}")
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate a cache key from arguments
        
        Args:
            prefix: Key prefix
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Cache key string
        """
        # Create a unique key from all arguments
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        key_hash = hashlib.md5(key_data.encode()).hexdigest()
        return f"{prefix}:{key_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        try:
            value = self.cache.get(key)
            if value is not None:
                logger.debug(f"Cache hit for key: {key}")
            else:
                logger.debug(f"Cache miss for key: {key}")
            return value
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """
        Set value in cache
        
        Args:
            key: Cache key
            value: Value to cache
            timeout: Cache timeout in seconds (uses default if None)
            
        Returns:
            True if successful, False otherwise
        """
        try:
            expire_time = timeout if timeout is not None else self.timeout
            self.cache.set(key, value, expire=expire_time)
            logger.debug(f"Cached value for key: {key} (timeout: {expire_time}s)")
            return True
        except Exception as e:
            logger.error(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """
        Delete value from cache
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        try:
            result = self.cache.delete(key)
            logger.debug(f"Deleted cache key: {key}")
            return result
        except Exception as e:
            logger.error(f"Cache delete error: {e}")
            return False
    
    def clear(self) -> bool:
        """
        Clear all cache
        
        Returns:
            True if successful, False otherwise
        """
        try:
            self.cache.clear()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Cache clear error: {e}")
            return False
    
    def get_or_set(self, key: str, func, *args, timeout: Optional[int] = None, **kwargs) -> Any:
        """
        Get value from cache or compute and cache it
        
        Args:
            key: Cache key
            func: Function to call if cache miss
            *args: Arguments for func
            timeout: Cache timeout
            **kwargs: Keyword arguments for func
            
        Returns:
            Cached or computed value
        """
        # Try to get from cache
        value = self.get(key)
        
        if value is not None:
            return value
        
        # Compute value
        try:
            value = func(*args, **kwargs)
            self.set(key, value, timeout)
            return value
        except Exception as e:
            logger.error(f"Error computing value for cache: {e}")
            return None
    
    def cached_api_call(self, api_func, *args, timeout: Optional[int] = None, **kwargs) -> Any:
        """
        Decorator-style cached API call
        
        Args:
            api_func: API function to call
            *args: Arguments for api_func
            timeout: Cache timeout
            **kwargs: Keyword arguments for api_func
            
        Returns:
            Cached or fresh API response
        """
        # Generate cache key from function name and arguments
        func_name = api_func.__name__
        key = self._generate_key(func_name, *args, **kwargs)
        
        return self.get_or_set(key, api_func, *args, timeout=timeout, **kwargs)
    
    def get_stats(self) -> dict:
        """
        Get cache statistics
        
        Returns:
            Dictionary with cache stats
        """
        try:
            return {
                "size": len(self.cache),
                "volume": self.cache.volume(),
                "directory": str(self.cache_dir)
            }
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}
