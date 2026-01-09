# Data base linked to superbase (PostgreSQL)

import json
import logging
import os
import uuid
from datetime import date, datetime
from typing import Any, Dict, List, Optional

import streamlit as st
from dotenv import load_dotenv

from config import DATE_FORMAT_DISPLAY, DATE_FORMAT_ISO, ERROR_LOG_FILE

logger = logging.getLogger(__name__)
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL" or st.secrets.get("SUPABASE_URL"))
SUPABASE_KEY = os.getenv("SUPABASE_KEY" or st.secrets.get("SUPABASE_KEY"))
"""
if not SUPABASE_URL or SUPABASE_KEY:
    supabase = None
else: 
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        logger.error(f"Erro crítico conectando ao Supabase: {e}")
"""


class ValidationError(Exception):
    """Raised when input validation fails."""

    pass


def load_data() -> List[Dict[str, Any]]:
    """
    Load error records from the JSON database file.

    Returns:
        List of error record dictionaries. Empty list if file doesn't exist.
    """
    if not ERROR_LOG_FILE.exists():
        return []

    try:
        with open(ERROR_LOG_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse error log: {e}")
        return []
    except IOError as e:
        logger.error(f"Failed to read error log file: {e}")
        return []


def save_data(data: List[Dict[str, Any]]) -> bool:
    """
    Save error records to the JSON database file.

    Args:
        data: List of error record dictionaries to save.

    Returns:
        True if save succeeded, False otherwise.
    """
    try:
        with open(ERROR_LOG_FILE, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        logger.info("Data saved successfully")
        return True
    except IOError as e:
        logger.error(f"Failed to save data: {e}")
        return False


def delete_database(data: List[Dict[str, Any]]) -> bool:
    """
    Clear all records from the database.

    Warning: This operation is irreversible.

    Args:
        data: In-memory data list to clear.

    Returns:
        True if deletion succeeded, False otherwise.
    """
    try:
        with open(ERROR_LOG_FILE, "w", encoding="utf-8") as file:
            json.dump([], file)
        data.clear()
        logger.info("Database cleared successfully")
        return True
    except IOError as e:
        logger.error(f"Failed to clear database: {e}")
        return False


def _generate_id() -> str:
    """Generate a unique ID for a new record."""
    return str(uuid.uuid4())[:8]


def _format_date(date_val: date | datetime | str) -> str:
    """
    Convert date value to standardized display format.

    Args:
        date_val: Date as datetime object or string.

    Returns:
        Date string in DD-MM-YYYY format.
    """
    if isinstance(date_val, (date, datetime)):
        return date_val.strftime(DATE_FORMAT_DISPLAY)

    try:
        parsed = datetime.strptime(str(date_val), DATE_FORMAT_ISO)
        return parsed.strftime(DATE_FORMAT_DISPLAY)
    except ValueError:
        return str(date_val)


def _validate_input(subject: str, topic: str, error_type: str) -> None:
    """
    Validate required fields before saving.

    Args:
        subject: Subject name to validate.
        topic: Topic name to validate.
        error_type: Error type to validate.

    Raises:
        ValidationError: If any required field is empty.
    """
    errors = []
    if not subject or not subject.strip():
        errors.append("Subject")
    if not topic or not topic.strip():
        errors.append("Topic")
    if not error_type or not error_type.strip():
        errors.append("Error Type")

    if errors:
        raise ValidationError(f"Missing required fields: {', '.join(errors)}")


def log_error(
    data: List[Dict[str, Any]],
    subject: str,
    topic: str,
    error_type: str,
    description: Optional[str],
    date_val: date | datetime | str,
) -> bool:
    """
    Log a new error record to the database.

    Args:
        data: In-memory list of error records.
        subject: Academic subject (e.g., "Math").
        topic: Specific topic within subject (e.g., "Geometry").
        error_type: Category of error from ErrorType enum.
        description: Optional user reflection on the error.
        date_val: When the error occurred.

    Returns:
        True if logging succeeded, False otherwise.

    Raises:
        ValidationError: If required fields are missing.
    """
    _validate_input(subject, topic, error_type)

    new_entry = {
        "id": _generate_id(),
        "subject": subject.strip(),
        "topic": topic.strip(),
        "type": error_type,
        "description": description.strip() if description else "",
        "date": _format_date(date_val),
    }

    data.append(new_entry)
    return save_data(data)


def update_errors(updated_data: List[Dict[str, Any]]) -> bool:
    """
    Update multiple error records in the database.

    Used by the History page to save bulk edits from the data table.

    Args:
        updated_data: Complete list of error records with modifications.

    Returns:
        True if update succeeded, False otherwise.

    Raises:
        ValidationError: If any record has missing required fields.
    """
    # Validate all records before saving
    for record in updated_data:
        subject = record.get("subject", "").strip()
        topic = record.get("topic", "").strip()
        error_type = record.get("type", "").strip()

        _validate_input(subject, topic, error_type)

    # All records are valid, save to file
    return save_data(updated_data)
