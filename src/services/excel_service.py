"""
Excel import/export service for exam telemetry data.

Provides functions to export study sessions, errors, and mock exams to Excel,
and intelligently import data from Excel files with automatic mapping.
"""

import logging
from datetime import datetime
from io import BytesIO
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st

from config import DATE_FORMAT_DISPLAY, DATE_FORMAT_ISO

logger = logging.getLogger(__name__)


# =============================================================================
# EXPORT FUNCTIONS
# =============================================================================


def export_to_excel(
    errors: List[Dict[str, Any]],
    sessions: List[Dict[str, Any]],
    mock_exams: List[Dict[str, Any]],
) -> BytesIO:
    """
    Export all data to a multi-sheet Excel file.

    Args:
        errors: List of error records
        sessions: List of study session records
        mock_exams: List of mock exam records

    Returns:
        BytesIO buffer containing the Excel file
    """
    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Sheet 1: Errors
        if errors:
            df_errors = pd.DataFrame(errors)
            # Drop internal columns
            drop_cols = [
                c
                for c in df_errors.columns
                if c in ["user_id", "created_at", "updated_at"]
            ]
            df_errors = df_errors.drop(columns=drop_cols, errors="ignore")
            df_errors.to_excel(writer, sheet_name="Errors", index=False)

        # Sheet 2: Study Sessions
        if sessions:
            df_sessions = pd.DataFrame(sessions)
            drop_cols = [
                c
                for c in df_sessions.columns
                if c in ["user_id", "created_at", "updated_at"]
            ]
            df_sessions = df_sessions.drop(columns=drop_cols, errors="ignore")
            df_sessions.to_excel(writer, sheet_name="Study Sessions", index=False)

        # Sheet 3: Mock Exams
        if mock_exams:
            df_exams = pd.DataFrame(mock_exams)
            drop_cols = [
                c
                for c in df_exams.columns
                if c in ["user_id", "created_at", "updated_at"]
            ]
            df_exams = df_exams.drop(columns=drop_cols, errors="ignore")
            df_exams.to_excel(writer, sheet_name="Mock Exams", index=False)

        # Sheet 4: Metadata
        metadata = pd.DataFrame(
            [
                {
                    "Export Date": datetime.now().strftime(DATE_FORMAT_DISPLAY),
                    "Total Errors": len(errors),
                    "Total Sessions": len(sessions),
                    "Total Mock Exams": len(mock_exams),
                    "Format Version": "2.0",
                }
            ]
        )
        metadata.to_excel(writer, sheet_name="Metadata", index=False)

    output.seek(0)
    return output


# =============================================================================
# IMPORT FUNCTIONS
# =============================================================================


def import_from_excel(
    file: Any, user_id: str
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Import data from an Excel file with intelligent mapping.

    Handles both:
    1. Files exported from this system (multi-sheet format)
    2. Generic Excel files with error data (auto-mapping)

    Args:
        file: Uploaded file object
        user_id: User ID to assign to imported records

    Returns:
        Tuple of (errors list, sessions list, mock_exams list)
    """
    try:
        # Read all sheets
        xl_file = pd.ExcelFile(file)
        sheet_names = xl_file.sheet_names

        errors = []
        sessions = []
        mock_exams = []

        # Case 1: Multi-sheet export from this system
        if "Errors" in sheet_names or "Study Sessions" in sheet_names:
            errors = _import_errors_sheet(xl_file, user_id)
            sessions = _import_sessions_sheet(xl_file, user_id)
            mock_exams = _import_exams_sheet(xl_file, user_id)

        # Case 2: Generic single-sheet file (assume it's errors)
        elif len(sheet_names) > 0:
            df = pd.read_excel(file, sheet_name=sheet_names[0])
            errors = _map_generic_to_errors(df, user_id)

        return errors, sessions, mock_exams

    except Exception as e:
        logger.error(f"Error importing Excel file: {e}")
        st.error(f"Failed to import file: {e}")
        return [], [], []


def _import_errors_sheet(xl_file: pd.ExcelFile, user_id: str) -> List[Dict[str, Any]]:
    """Import errors from the Errors sheet."""
    if "Errors" not in xl_file.sheet_names:
        return []

    df = pd.read_excel(xl_file, sheet_name="Errors")

    errors = []
    for _, row in df.iterrows():
        try:
            error = {
                "user_id": user_id,
                "subject": str(row.get("subject", "Unknown")),
                "topic": str(row.get("topic", "Unknown")),
                "type": str(row.get("type", "Content Gap")),
                "description": str(row.get("description", "")),
                "date": _parse_date(row.get("date")),
                "difficulty": str(row.get("difficulty", "Medium")),
                "exam_type": str(row.get("exam_type", "General")),
            }

            # Add session_id if present
            if "session_id" in row and pd.notna(row["session_id"]):
                error["session_id"] = str(row["session_id"])

            errors.append(error)
        except Exception as e:
            logger.warning(f"Skipping invalid error row: {e}")
            continue

    return errors


def _import_sessions_sheet(xl_file: pd.ExcelFile, user_id: str) -> List[Dict[str, Any]]:
    """Import study sessions from the Study Sessions sheet."""
    if "Study Sessions" not in xl_file.sheet_names:
        return []

    df = pd.read_excel(xl_file, sheet_name="Study Sessions")

    sessions = []
    for _, row in df.iterrows():
        try:
            session = {
                "user_id": user_id,
                "exam_type": str(row.get("exam_type", "General")),
                "subject": str(row.get("subject", "Unknown")),
                "total_questions": int(row.get("total_questions", 0)),
                "correct_count": int(row.get("correct_count", 0)),
                "duration_minutes": float(row.get("duration_minutes", 0)),
                "date": _parse_date(row.get("date")),
            }

            sessions.append(session)
        except Exception as e:
            logger.warning(f"Skipping invalid session row: {e}")
            continue

    return sessions


def _import_exams_sheet(xl_file: pd.ExcelFile, user_id: str) -> List[Dict[str, Any]]:
    """Import mock exams from the Mock Exams sheet."""
    if "Mock Exams" not in xl_file.sheet_names:
        return []

    df = pd.read_excel(xl_file, sheet_name="Mock Exams")

    exams = []
    for _, row in df.iterrows():
        try:
            exam = {
                "user_id": user_id,
                "exam_name": str(row.get("exam_name", "Untitled")),
                "exam_type": str(row.get("exam_type", "General")),
                "total_score": float(row.get("total_score", 0)),
                "max_possible_score": float(row.get("max_possible_score", 100)),
                "date": _parse_date(row.get("date")),
                "notes": str(row.get("notes", "")),
            }

            exams.append(exam)
        except Exception as e:
            logger.warning(f"Skipping invalid exam row: {e}")
            continue

    return exams


def _map_generic_to_errors(df: pd.DataFrame, user_id: str) -> List[Dict[str, Any]]:
    """
    Intelligently map a generic DataFrame to error records.

    Attempts to identify columns based on common patterns:
    - Subject/Materia/Disciplina → subject
    - Topic/Assunto/Topico → topic
    - Type/Tipo/Error Type → type
    - Date/Data → date
    - Description/Descrição → description
    """
    errors = []

    # Column mapping heuristics
    col_map = _detect_columns(df.columns)

    for _, row in df.iterrows():
        try:
            error = {
                "user_id": user_id,
                "subject": str(row.get(col_map.get("subject", "Subject"), "Unknown")),
                "topic": str(row.get(col_map.get("topic", "Topic"), "Unknown")),
                "type": str(row.get(col_map.get("type", "Type"), "Content Gap")),
                "description": str(
                    row.get(col_map.get("description", "Description"), "")
                ),
                "date": _parse_date(row.get(col_map.get("date", "Date"))),
                "difficulty": str(
                    row.get(col_map.get("difficulty", "Difficulty"), "Medium")
                ),
                "exam_type": "General",  # Default for generic imports
            }

            errors.append(error)
        except Exception as e:
            logger.warning(f"Skipping invalid row: {e}")
            continue

    return errors


def _detect_columns(columns: List[str]) -> Dict[str, str]:
    """
    Detect column mappings from generic Excel file.

    Args:
        columns: List of column names

    Returns:
        Dictionary mapping canonical name to detected column name
    """
    mapping = {}

    # Normalize column names
    normalized = {col.lower().strip(): col for col in columns}

    # Subject detection
    subject_patterns = ["subject", "materia", "matéria", "disciplina", "assunto"]
    for pattern in subject_patterns:
        if pattern in normalized:
            mapping["subject"] = normalized[pattern]
            break

    # Topic detection
    topic_patterns = ["topic", "topico", "tópico", "tema", "assunto"]
    for pattern in topic_patterns:
        if pattern in normalized:
            mapping["topic"] = normalized[pattern]
            break

    # Type detection
    type_patterns = [
        "type",
        "tipo",
        "error type",
        "tipo de erro",
        "category",
        "categoria",
    ]
    for pattern in type_patterns:
        if pattern in normalized:
            mapping["type"] = normalized[pattern]
            break

    # Date detection
    date_patterns = ["date", "data", "fecha", "when"]
    for pattern in date_patterns:
        if pattern in normalized:
            mapping["date"] = normalized[pattern]
            break

    # Description detection
    desc_patterns = ["description", "descrição", "descricao", "notes", "notas", "obs"]
    for pattern in desc_patterns:
        if pattern in normalized:
            mapping["description"] = normalized[pattern]
            break

    # Difficulty detection
    diff_patterns = ["difficulty", "dificuldade", "nivel", "nível", "level"]
    for pattern in diff_patterns:
        if pattern in normalized:
            mapping["difficulty"] = normalized[pattern]
            break

    return mapping


def _parse_date(date_val: Any) -> str:
    """
    Parse a date value from Excel into ISO format.

    Args:
        date_val: Can be string, datetime, or Timestamp

    Returns:
        Date string in ISO format (YYYY-MM-DD)
    """
    if pd.isna(date_val):
        return datetime.now().strftime(DATE_FORMAT_ISO)

    # If already a datetime/Timestamp
    if isinstance(date_val, (datetime, pd.Timestamp)):
        return date_val.strftime(DATE_FORMAT_ISO)

    # Try parsing as string
    if isinstance(date_val, str):
        # Try DD-MM-YYYY format first
        try:
            dt = datetime.strptime(date_val, DATE_FORMAT_DISPLAY)
            return dt.strftime(DATE_FORMAT_ISO)
        except ValueError:
            pass

        # Try ISO format
        try:
            dt = datetime.strptime(date_val, DATE_FORMAT_ISO)
            return dt.strftime(DATE_FORMAT_ISO)
        except ValueError:
            pass

        # Try other common formats
        for fmt in ["%d/%m/%Y", "%m/%d/%Y", "%Y/%m/%d"]:
            try:
                dt = datetime.strptime(date_val, fmt)
                return dt.strftime(DATE_FORMAT_ISO)
            except ValueError:
                continue

    # Fallback to today
    return datetime.now().strftime(DATE_FORMAT_ISO)


# =============================================================================
# VALIDATION FUNCTIONS
# =============================================================================


def validate_import_data(
    errors: List[Dict[str, Any]],
    sessions: List[Dict[str, Any]],
    mock_exams: List[Dict[str, Any]],
) -> Tuple[bool, List[str]]:
    """
    Validate imported data before inserting into database.

    Args:
        errors: List of error records
        sessions: List of session records
        mock_exams: List of mock exam records

    Returns:
        Tuple of (is_valid, list of error messages)
    """
    issues = []

    # Check if any data was imported
    if not any([errors, sessions, mock_exams]):
        issues.append("No data found in the file.")
        return False, issues

    # Validate errors
    for i, error in enumerate(errors):
        if not error.get("subject") or not error.get("topic"):
            issues.append(f"Error row {i + 1}: Missing required fields (subject/topic)")

    # Validate sessions
    for i, session in enumerate(sessions):
        total = session.get("total_questions", 0)
        correct = session.get("correct_count", 0)

        if total <= 0:
            issues.append(f"Session row {i + 1}: Total questions must be > 0")
        if correct > total:
            issues.append(f"Session row {i + 1}: Correct count exceeds total")

    # Validate mock exams
    for i, exam in enumerate(mock_exams):
        score = exam.get("total_score", 0)
        max_score = exam.get("max_possible_score", 0)

        if max_score <= 0:
            issues.append(f"Exam row {i + 1}: Max score must be > 0")
        if score > max_score:
            issues.append(f"Exam row {i + 1}: Score exceeds max possible")

    # If there are critical issues, fail validation
    if len(issues) > 5:
        return False, issues[:5] + [f"...and {len(issues) - 5} more issues"]

    return len(issues) == 0, issues
