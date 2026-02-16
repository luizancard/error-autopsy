"""
Centralized configuration for the Exam Telemetry System.

This module contains all configurable settings including:
- Exam type definitions and subject mappings
- Error type definitions
- Performance benchmarks (pace, accuracy targets)
- Date formats
- Time filter options
- UI theme colors
- File paths
"""

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

# Base paths

BASE_DIR: Path = Path(__file__).resolve().parent.parent
DATA_DIR: Path = BASE_DIR / "data"
ASSETS_DIR: Path = BASE_DIR / "assets"

# Data files
ERROR_LOG_FILE: Path = DATA_DIR / "error_log.json"
CSS_FILE: Path = ASSETS_DIR / "style.css"


# =============================================================================
# EXAM TYPES & CONTEXT
# =============================================================================


class ExamType(Enum):
    """
    Enumeration of supported competitive exams.

    Each exam type has specific subject mappings and performance benchmarks
    tailored to the exam's format and difficulty.
    """

    FUVEST = "FUVEST"  # USP entrance exam
    ENEM = "ENEM"  # National high school exam
    UNICAMP = "UNICAMP"  # UNICAMP entrance exam
    ITA_IME = "ITA/IME"  # Military engineering schools
    SAT = "SAT"  # US college admissions
    GENERAL = "General"  # Generic/practice sessions


# List of exam types for UI dropdowns
EXAM_TYPES: List[str] = [e.value for e in ExamType]

# Default exam type
DEFAULT_EXAM_TYPE: str = ExamType.GENERAL.value


# Context-Aware Subject Mappings
# Maps each exam to its specific subject list

EXAM_SUBJECTS: Dict[str, List[str]] = {
    "FUVEST": [
        "Portuguese",
        "Portuguese Literature",
        "Mathematics",
        "Physics",
        "Chemistry",
        "Biology",
        "History",
        "Geography",
        "English",
        "Redação (Essay)",
    ],
    "ENEM": [
        "Português (Portuguese)",
        "Literatura (Literature)",
        "Inglês (English)",
        "Espanhol (Spanish)",
        "Artes (Arts)",
        "Educação Física (Physical Education)",
        "Matemática (Mathematics)",
        "História (History)",
        "Geografia (Geography)",
        "Filosofia (Philosophy)",
        "Sociologia (Sociology)",
        "Biologia (Biology)",
        "Química (Chemistry)",
        "Física (Physics)",
        "Redação (Essay)",
    ],
    "UNICAMP": [
        "Portuguese",
        "Mathematics",
        "Physics",
        "Chemistry",
        "Biology",
        "History",
        "Geography",
        "English",
        "Redação (Essay)",
        "Interdisciplinary",
    ],
    "ITA/IME": [
        "Mathematics",
        "Physics",
        "Chemistry",
        "Portuguese",
        "English",
        "Redação (Essay)",
    ],
    "SAT": [
        "Reading and Writing",
        "Math",
    ],
    "General": [
        "Mathematics",
        "Physics",
        "Chemistry",
        "Biology",
        "Portuguese",
        "English",
        "History",
        "Geography",
        "Literature",
        "Other",
    ],
}


# Performance Benchmarks
# Target pace (minutes per question) for each exam type

EXAM_PACE_BENCHMARKS: Dict[str, float] = {
    "FUVEST": 3.0,  # ~3 minutes per question (Phase 1)
    "ENEM": 3.0,  # ~180 minutes / 45 questions = 4 min, but 3 is ideal
    "UNICAMP": 3.5,  # Longer, more complex questions
    "ITA/IME": 4.0,  # Extremely difficult, longer solutions
    "SAT": 1.25,  # ~75 seconds per question (varies by section)
    "General": 2.5,  # Conservative general benchmark
}


# Accuracy Targets (percentage thresholds)
class AccuracyZone:
    """Performance zones based on accuracy percentage."""

    MASTERY_THRESHOLD: float = 80.0  # 80%+ = Mastery
    DEVELOPING_THRESHOLD: float = 60.0  # 60-79% = Developing
    # Below 60% = Struggling


# Pace Zones (for speed analysis)
class PaceZone:
    """Performance zones based on pace relative to benchmark."""

    RUSHING_MULTIPLIER: float = 0.5  # < 50% of benchmark = Rushing
    OPTIMAL_MAX_MULTIPLIER: float = 1.2  # 50%-120% = Optimal
    # > 120% = Too Slow

    @staticmethod
    def classify(pace: float, benchmark: float) -> str:
        """Classify pace relative to exam benchmark."""
        if pace < benchmark * PaceZone.RUSHING_MULTIPLIER:
            return "Rushing"
        elif pace <= benchmark * PaceZone.OPTIMAL_MAX_MULTIPLIER:
            return "Optimal"
        else:
            return "Too Slow"


def get_subjects_for_exam(exam_type: str) -> List[str]:
    """
    Get the appropriate subject list for a given exam type.

    Args:
        exam_type: The exam type identifier

    Returns:
        List of subjects for that exam
    """
    return EXAM_SUBJECTS.get(exam_type, EXAM_SUBJECTS["General"])


def get_pace_benchmark(exam_type: str) -> float:
    """
    Get the target pace (minutes per question) for an exam type.

    Args:
        exam_type: The exam type identifier

    Returns:
        Target minutes per question
    """
    return EXAM_PACE_BENCHMARKS.get(exam_type, EXAM_PACE_BENCHMARKS["General"])


# =============================================================================
# EXAM SECTION DEFINITIONS (for structured mock exams)
# =============================================================================

# Each section: key -> {label, min, max, subject (maps to error log subject)}

ENEM_SECTIONS: Dict[str, Dict[str, Any]] = {
    "linguagens": {
        "label": "Linguagens",
        "min": 0,
        "max": 45,
        "subject": "Linguagens (Languages & Codes)",
        "is_essay": False,
    },
    "ciencias_humanas": {
        "label": "Ciencias Humanas",
        "min": 0,
        "max": 45,
        "subject": "Ciencias Humanas (Social Sciences)",
        "is_essay": False,
    },
    "ciencias_natureza": {
        "label": "Ciencias da Natureza",
        "min": 0,
        "max": 45,
        "subject": "Ciencias da Natureza (Natural Sciences)",
        "is_essay": False,
    },
    "matematica": {
        "label": "Matematica",
        "min": 0,
        "max": 45,
        "subject": "Matematica (Mathematics)",
        "is_essay": False,
    },
    "redacao": {
        "label": "Redacao",
        "min": 400,
        "max": 1000,
        "subject": "Redacao (Essay)",
        "is_essay": True,
    },
}

SAT_SECTIONS: Dict[str, Dict[str, Any]] = {
    "rw_module1": {
        "label": "R&W Module 1",
        "min": 0,
        "max": 27,
        "subject": "Reading and Writing",
        "is_essay": False,
    },
    "rw_module2": {
        "label": "R&W Module 2",
        "min": 0,
        "max": 27,
        "subject": "Reading and Writing",
        "is_essay": False,
    },
    "math_module1": {
        "label": "Math Module 1",
        "min": 0,
        "max": 22,
        "subject": "Math",
        "is_essay": False,
    },
    "math_module2": {
        "label": "Math Module 2",
        "min": 0,
        "max": 22,
        "subject": "Math",
        "is_essay": False,
    },
}

EXAM_SECTION_DEFS: Dict[str, Dict[str, Dict[str, Any]]] = {
    "ENEM": ENEM_SECTIONS,
    "SAT": SAT_SECTIONS,
}


def get_sections_for_exam(exam_type: str) -> Optional[Dict[str, Dict[str, Any]]]:
    """
    Get section definitions for an exam type, if it has structured sections.

    Args:
        exam_type: The exam type identifier

    Returns:
        Section definitions dict or None if exam uses generic scoring
    """
    return EXAM_SECTION_DEFS.get(exam_type)


# =============================================================================
# ERROR TYPES
# =============================================================================


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

# Difficulty Levels


class DifficultyLevel(Enum):
    """Enumeration of difficulty levels for exercises."""

    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


# List of difficulty levels for UI dropdowns
DIFFICULTY_LEVELS: List[str] = [d.value for d in DifficultyLevel]

# Default difficulty level for forms
DEFAULT_DIFFICULTY: str = DifficultyLevel.MEDIUM.value

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
    PAGE_ICON: str = "A"
    LAYOUT: Literal["centered", "wide"] = "wide"

    # Success message display duration (seconds)
    SUCCESS_MESSAGE_DURATION: float = 2.0
