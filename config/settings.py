"""
Centralized configuration for the Error Autopsy application.

This module contains all configurable settings including:
- Error type definitions
- Date formats
- Time filter options
- UI theme colors
- File paths
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Literal

# Base paths

BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
ASSETS_DIR: Path = BASE_DIR / "assets"

# Data files
ERROR_LOG_FILE: Path = DATA_DIR / "error_log.json"
CSS_FILE: Path = ASSETS_DIR / "style.css"


# Error Types


class ErrorType(Enum):
    """
    Enumeration of error categories for mistake classification.

    Each type represents a distinct reason why a mistake occurred,
    helping users identify patterns in their learning process.
    """

    CONTENT_GAP = "Content Gap"
    ATTENTION_DETAIL = "Attention Detail"
    TIME_MANAGEMENT = "Time Management"
    FATIGUE = "Fatigue"
    INTERPRETATION = "Interpretation"


# List of error type values for UI dropdowns
ERROR_TYPES: List[str] = [e.value for e in ErrorType]

# Default error type for forms
DEFAULT_ERROR_TYPE: str = ErrorType.CONTENT_GAP.value

# Error types considered "avoidable" for metrics
AVOIDABLE_ERROR_TYPES: List[str] = [
    ErrorType.ATTENTION_DETAIL.value,
    ErrorType.INTERPRETATION.value,
]

# Date Formats

# Primary format used for storage and display (DD-MM-YYYY)
DATE_FORMAT_DISPLAY: str = "%d-%m-%Y"

# ISO format for parsing date inputs (YYYY-MM-DD)
DATE_FORMAT_ISO: str = "%Y-%m-%d"

# Days per month approximation for date filtering
DAYS_PER_MONTH: int = 30

# Time filters


class TimeFilter:
    """Configuration for time-based data filtering."""

    # Filter options displayed in UI
    OPTIONS: List[str] = [
        "This Month",
        "Last 2 Months",
        "Last 4 Months",
        "Last 6 Months",
        "All Time",
    ]

    # Mapping of filter labels to months (None = no filter)
    MONTHS_MAP: Dict[str, int | None] = {
        "This Month": 0,
        "Last 2 Months": 2,
        "Last 4 Months": 4,
        "Last 6 Months": 6,
        "All Time": None,
    }

    DEFAULT: str = "All Time"


# UI Theme colors


class Colors:
    """
    Color palette for the application UI.

    Colors are organized by semantic purpose to maintain
    consistency across all components.
    """

    # Primary brand colors
    PRIMARY: str = "#4e4a5aff"
    PRIMARY_LIGHT: str = "#6366f1"

    # Text colors
    TEXT_DARK: str = "#0f172a"
    TEXT_MUTED: str = "#94a3b8"
    TEXT_SECONDARY: str = "#64748b"
    TEXT_LIGHT: str = "#9ca3af"
    TEXT_WHITE: str = "#eeeeee"

    # Background colors
    BG_LIGHT: str = "#eeeeeeff"
    BG_DARK: str = "#1a1a1a"

    # Chart axis colors
    AXIS_LABEL: str = "#0f172a"
    AXIS_GRID: str = "#e2e8f0"

    # Metric card icon backgrounds and colors
    CARD_TOTAL_BG: str = "#eef2ff"
    CARD_TOTAL_COLOR: str = "#4338ca"

    CARD_SUBJECT_BG: str = "#e7f5ef"
    CARD_SUBJECT_COLOR: str = "#0f766e"

    CARD_ERROR_BG: str = "#fff7ed"
    CARD_ERROR_COLOR: str = "#c2410c"

    CARD_AVOIDABLE_BG: str = "#fefce8"
    CARD_AVOIDABLE_COLOR: str = "#cf8215"

    # Chart color palette (for pie charts, etc.)
    CHART_PALETTE: List[str] = [
        "#242038",
        "#725AC1",
        "#8070C5",
        "#8D86C9",
        "#CAC4CE",
        "#F7ECE1",
    ]


# Chart Configuration


class ChartConfig:
    """Configuration for chart dimensions and display."""

    # Default chart heights
    HEIGHT_DEFAULT: int = 320
    HEIGHT_LARGE: int = 350

    # Maximum items to display
    TOP_TOPICS_LIMIT: int = 10


# App Configuration


class AppConfig:
    """General application settings."""

    PAGE_TITLE: str = "Error Autopsy"
    PAGE_ICON: str = "📝"
    LAYOUT: Literal["centered", "wide"] = "wide"

    # Success message display duration (seconds)
    SUCCESS_MESSAGE_DURATION: float = 2.0
