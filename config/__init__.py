"""
Configuration package for Error Autopsy.

Provides centralized access to all application settings.
"""

from config.settings import (
    ASSETS_DIR,
    AVOIDABLE_ERROR_TYPES,
    BASE_DIR,
    CSS_FILE,
    DATA_DIR,
    DATE_FORMAT_DISPLAY,
    DATE_FORMAT_ISO,
    DAYS_PER_MONTH,
    DEFAULT_ERROR_TYPE,
    ERROR_LOG_FILE,
    ERROR_TYPES,
    AppConfig,
    ChartConfig,
    Colors,
    ErrorType,
    TimeFilter,
)

__all__ = [
    "AppConfig",
    "ChartConfig",
    "Colors",
    "ErrorType",
    "TimeFilter",
    "ASSETS_DIR",
    "AVOIDABLE_ERROR_TYPES",
    "BASE_DIR",
    "CSS_FILE",
    "DATA_DIR",
    "DATE_FORMAT_DISPLAY",
    "DATE_FORMAT_ISO",
    "DAYS_PER_MONTH",
    "DEFAULT_ERROR_TYPE",
    "ERROR_LOG_FILE",
    "ERROR_TYPES",
]
