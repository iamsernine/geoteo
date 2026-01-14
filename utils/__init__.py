"""
AirWatch Utilities Module
Common utility functions and helpers
"""

from .logger_setup import setup_logging, log_function_call, log_api_call, log_error, log_performance

__all__ = ["setup_logging", "log_function_call", "log_api_call", "log_error", "log_performance"]
