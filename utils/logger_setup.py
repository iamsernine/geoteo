"""
Logger Setup
Configures comprehensive logging for the application
"""

import sys
from pathlib import Path
from loguru import logger
import config


def setup_logging():
    """
    Setup comprehensive logging configuration
    
    Configures loguru logger with:
    - Console output with colored formatting
    - File output with rotation and retention
    - Different log levels for different outputs
    - Structured logging with context
    """
    # Remove default logger
    logger.remove()
    
    # Console logging (colorized)
    logger.add(
        sys.stderr,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=config.LOG_LEVEL,
        colorize=True
    )
    
    # File logging (detailed)
    logger.add(
        config.LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        compression="zip",
        enqueue=True  # Thread-safe
    )
    
    # Error file logging (errors only)
    error_log_file = config.LOGS_DIR / "errors.log"
    logger.add(
        error_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}\n{exception}",
        level="ERROR",
        rotation="5 MB",
        retention="30 days",
        compression="zip",
        backtrace=True,
        diagnose=True
    )
    
    # API calls logging
    api_log_file = config.LOGS_DIR / "api_calls.log"
    logger.add(
        api_log_file,
        format="{time:YYYY-MM-DD HH:mm:ss} | {message}",
        level="INFO",
        rotation="10 MB",
        retention="7 days",
        filter=lambda record: "API" in record["message"] or "request" in record["message"].lower()
    )
    
    logger.info("Logging system initialized")
    logger.info(f"Log level: {config.LOG_LEVEL}")
    logger.info(f"Log file: {config.LOG_FILE}")
    logger.info(f"Error log: {error_log_file}")
    logger.info(f"API log: {api_log_file}")


def log_function_call(func):
    """
    Decorator to log function calls
    
    Usage:
        @log_function_call
        def my_function(arg1, arg2):
            pass
    """
    def wrapper(*args, **kwargs):
        logger.debug(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.debug(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed with error: {e}")
            raise
    return wrapper


def log_api_call(endpoint: str, method: str = "GET", params: dict = None):
    """
    Log API call details
    
    Args:
        endpoint: API endpoint
        method: HTTP method
        params: Request parameters
    """
    logger.info(f"API Call: {method} {endpoint} | Params: {params}")


def log_error(error: Exception, context: dict = None):
    """
    Log error with context
    
    Args:
        error: Exception object
        context: Additional context dictionary
    """
    logger.error(f"Error occurred: {error}")
    if context:
        logger.error(f"Context: {context}")
    logger.exception(error)


def log_performance(operation: str, duration: float, details: dict = None):
    """
    Log performance metrics
    
    Args:
        operation: Operation name
        duration: Duration in seconds
        details: Additional details
    """
    logger.info(f"Performance: {operation} took {duration:.3f}s | Details: {details}")


# Initialize logging when module is imported
setup_logging()
