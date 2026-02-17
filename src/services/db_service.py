import logging
import os
from datetime import date, datetime
from typing import Any, Dict, List, Optional, cast

import streamlit as st
from dotenv import load_dotenv
from supabase import Client, create_client

from config import DATE_FORMAT_DISPLAY, DATE_FORMAT_ISO

logger = logging.getLogger(__name__)
load_dotenv()


@st.cache_resource
def init_supabase() -> Client:
    url = os.getenv("SUPABASE_URL") or st.secrets.get("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY") or st.secrets.get("SUPABASE_KEY")

    if not url or not key:
        st.error("CRITICAL ERROR: Supabase credentials not found.")
        st.stop()

    return create_client(url, key)


supabase = init_supabase()


class ValidationError(Exception):
    pass


def _format_date_iso(date_val: date | datetime | str) -> str:
    if isinstance(date_val, (date, datetime)):
        return date_val.strftime(DATE_FORMAT_ISO)
    try:
        return datetime.strptime(str(date_val), DATE_FORMAT_DISPLAY).strftime(
            DATE_FORMAT_ISO
        )
    except ValueError:
        return str(date_val)


def _validate_input(subject: str, topic: str, error_type: str) -> None:
    if not all([subject.strip(), topic.strip(), error_type.strip()]):
        raise ValidationError("Please fill in all required fields.")


def log_bulk_errors(errors_list: List[Dict[str, Any]]) -> bool:
    """
    Log multiple errors in a single database transaction.

    Args:
        errors_list: List of error dictionaries with fields:
            - user_id (required)
            - subject (required)
            - topic (required)
            - type (required)
            - description (optional)
            - date (required)
            - difficulty (optional, defaults to "Medium")
            - exam_type (optional, defaults to "General")
            - session_id (optional)
            - mock_exam_id (optional)

    Returns:
        True if successful, False otherwise
    """
    if not supabase or not errors_list:
        return False

    try:
        # Format and validate all errors before insertion
        formatted_errors = []
        for error in errors_list:
            # Skip empty entries - check topic is valid
            topic = error.get("topic") or ""
            if not topic or not topic.strip():
                continue

            subject = error.get("subject") or ""
            error_type = error.get("type") or ""

            _validate_input(subject, topic, error_type)

            payload = {
                "user_id": error["user_id"],
                "subject": subject.strip(),
                "topic": topic.strip(),
                "type": error_type,
                "description": (error.get("description") or "").strip(),
                "date": _format_date_iso(error.get("date", date.today())),
                "difficulty": error.get("difficulty", "Medium"),
                "exam_type": error.get("exam_type", "General"),
            }

            # Add optional fields if provided
            if error.get("session_id"):
                payload["session_id"] = error["session_id"]
            if error.get("mock_exam_id"):
                payload["mock_exam_id"] = error["mock_exam_id"]

            formatted_errors.append(payload)

        if formatted_errors:
            supabase.table("errors").insert(formatted_errors).execute()

        return True

    except Exception as e:
        logger.error(f"Error logging bulk errors: {e}")
        st.error(f"Failed to save errors: {e}")
        return False


def load_data(user_id: str) -> List[Dict[str, Any]]:
    """
    Load user errors with optimized column selection and type safety.

    Returns:
        List of error dictionaries with parsed dates
    """
    if not supabase:
        return []

    try:
        # OPTIMIZED: Select only necessary columns
        response = (
            supabase.table("errors")
            .select(
                "id, user_id, subject, topic, type, description, date, difficulty, exam_type, session_id, mock_exam_id"
            )
            .eq("user_id", user_id)
            .order("date", desc=True)
            .execute()
        )

        raw_data = (
            cast(List[Dict[str, Any]], response.data)
            if response.data is not None
            else []
        )

        processed_data: List[Dict[str, Any]] = []

        for item in raw_data:
            clean_item = item.copy()

            # Ensure difficulty field exists (backward compatibility)
            if "difficulty" not in clean_item:
                clean_item["difficulty"] = "Medium"

            # TYPE SAFETY: Strict Date Parsing
            if clean_item.get("date"):
                try:
                    if isinstance(clean_item["date"], str):
                        dt = datetime.strptime(
                            clean_item["date"], DATE_FORMAT_ISO
                        ).date()
                        clean_item["date_obj"] = dt
                        clean_item["date"] = dt.strftime(DATE_FORMAT_DISPLAY)
                    else:
                        clean_item["date_obj"] = clean_item["date"]
                except (ValueError, TypeError):
                    clean_item["date_obj"] = date.today()
                    pass
            else:
                clean_item["date_obj"] = date.today()

            processed_data.append(clean_item)

        return processed_data

    except Exception as e:
        logger.error(f"Error loading data: {e}")
        return []


def log_error(
    user_id: str,
    subject: str,
    topic: str,
    error_type: str,
    description: Optional[str],
    date_val: date,
    difficulty: str = "Medium",
    exam_type: str = "General",
) -> bool:
    if not supabase:
        return False

    try:
        _validate_input(subject, topic, error_type)

        payload = {
            "user_id": user_id,
            "subject": subject.strip(),
            "topic": topic.strip(),
            "type": error_type,
            "description": description.strip() if description else "",
            "date": _format_date_iso(date_val),
            "difficulty": difficulty,
            "exam_type": exam_type,
        }

        supabase.table("errors").insert(payload).execute()
        return True
    except Exception as e:
        logger.error(f"Erro ao salvar: {e}")
        st.error(f"Failed to save: {e}")
        return False


def update_errors(user_id: str, updated_records: List[Dict[str, Any]]) -> bool:
    if not supabase:
        return False

    try:
        clean_records = []
        for rec in updated_records:
            # Handle both original column names and display names
            rec_id = rec.get("ID") or rec.get("id")
            if not rec_id:
                continue

            clean_records.append(
                {
                    "id": rec_id,
                    "user_id": user_id,
                    "subject": rec.get("Subject") or rec.get("subject", ""),
                    "topic": rec.get("Topic") or rec.get("topic", ""),
                    "type": rec.get("Error Type") or rec.get("type", ""),
                    "description": rec.get("Description") or rec.get("description", ""),
                    "date": _format_date_iso(
                        rec.get("Date") or rec.get("date", date.today())
                    ),
                    "difficulty": rec.get("Difficulty")
                    or rec.get("difficulty", "Medium"),
                }
            )

        if clean_records:
            supabase.table("errors").upsert(clean_records).execute()
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar: {e}")
        return False


def delete_errors(user_id: str, error_ids: List[str]) -> bool:
    """
    Delete multiple error records.

    Args:
        user_id: User UUID
        error_ids: List of error IDs to delete

    Returns:
        True if successful, False otherwise
    """
    if not supabase:
        return False

    try:
        for error_id in error_ids:
            supabase.table("errors").delete().eq("id", error_id).eq(
                "user_id", user_id
            ).execute()
        return True
    except Exception as e:
        logger.error(f"Error deleting errors: {e}")
        return False


# =============================================================================
# STUDY SESSION OPERATIONS
# =============================================================================


def update_sessions(user_id: str, updated_records: List[Dict[str, Any]]) -> bool:
    """
    Update multiple study session records.

    Args:
        user_id: User UUID
        updated_records: List of session dictionaries with updated values

    Returns:
        True if successful, False otherwise
    """
    if not supabase:
        return False

    try:
        clean_records = []
        for rec in updated_records:
            if not rec.get("ID"):
                continue

            # Mapping display names back to database columns
            clean_rec = {
                "id": rec["ID"],
                "user_id": user_id,
                "exam_type": rec.get("Exam Type", "General"),
                "subject": rec.get("Subject", ""),
                "topics_covered": rec.get("Topics Covered", ""),
                "questions_total": int(rec.get("Total Questions", 0)),
                "questions_correct": int(rec.get("Correct", 0)),
                "questions_wrong": int(rec.get("Wrong", 0)),
                "time_spent_min": int(rec.get("Time (min)", 0)),
                "date": _format_date_iso(rec.get("Date", date.today())),
            }
            clean_records.append(clean_rec)

        if clean_records:
            supabase.table("study_sessions").upsert(clean_records).execute()
        return True
    except Exception as e:
        logger.error(f"Error updating sessions: {e}")
        return False


def create_study_session(
    user_id: str,
    exam_type: str,
    subject: str,
    total_questions: int,
    correct_count: int,
    duration_minutes: float,
    date_val: date,
) -> Optional[str]:
    """
    Create a new study session record.

    Args:
        user_id: User UUID
        exam_type: Type of exam (FUVEST, ENEM, etc.)
        subject: Subject studied
        total_questions: Total number of questions attempted
        correct_count: Number of questions answered correctly
        duration_minutes: Time spent in minutes
        date_val: Date of the session

    Returns:
        Session ID if successful, None otherwise
    """
    if not supabase:
        return None

    try:
        if total_questions <= 0:
            raise ValidationError("Total questions must be greater than 0")
        if correct_count < 0 or correct_count > total_questions:
            raise ValidationError("Invalid correct count")
        if duration_minutes <= 0:
            raise ValidationError("Duration must be greater than 0")

        payload = {
            "user_id": user_id,
            "exam_type": exam_type,
            "subject": subject.strip(),
            "total_questions": total_questions,
            "correct_count": correct_count,
            "duration_minutes": round(duration_minutes, 2),
            "date": _format_date_iso(date_val),
        }

        response = supabase.table("study_sessions").insert(payload).execute()

        data = response.data
        if data and len(data) > 0:
            row = cast(Dict[str, Any], data[0])
            return str(row["id"])
        return None

    except Exception as e:
        logger.error(f"Error creating study session: {e}")
        st.error(f"Failed to create session: {e}")
        return None


def load_study_sessions(user_id: str) -> List[Dict[str, Any]]:
    """
    Load study sessions with optimized column selection and type safety.

    Returns:
        List of session dictionaries with computed metrics and parsed dates
    """
    if not supabase:
        return []

    try:
        # OPTIMIZED: Select only necessary columns
        response = (
            supabase.table("study_sessions")
            .select(
                "id, user_id, exam_type, subject, total_questions, correct_count, duration_minutes, date"
            )
            .eq("user_id", user_id)
            .order("date", desc=True)
            .execute()
        )

        raw_data = (
            cast(List[Dict[str, Any]], response.data)
            if response.data is not None
            else []
        )

        processed_data: List[Dict[str, Any]] = []

        for item in raw_data:
            clean_item = item.copy()

            # Ensure required fields exist with defaults
            total_q = float(clean_item.get("total_questions", 0))
            correct = float(clean_item.get("correct_count", 0))
            duration = float(clean_item.get("duration_minutes", 0))

            clean_item["total_questions"] = total_q
            clean_item["correct_count"] = correct
            clean_item["duration_minutes"] = duration

            # TYPE SAFETY: Strict Date Parsing
            if clean_item.get("date"):
                try:
                    if isinstance(clean_item["date"], str):
                        dt = datetime.strptime(
                            clean_item["date"], DATE_FORMAT_ISO
                        ).date()
                        clean_item["date_obj"] = dt
                        clean_item["date"] = dt.strftime(DATE_FORMAT_DISPLAY)
                    else:
                        clean_item["date_obj"] = clean_item["date"]
                except (ValueError, TypeError):
                    clean_item["date_obj"] = date.today()
                    pass
            else:
                clean_item["date_obj"] = date.today()

            # Computed Metrics
            if total_q > 0:
                clean_item["accuracy_percentage"] = (correct / total_q) * 100
                clean_item["pace_per_question"] = duration / total_q
            else:
                clean_item["accuracy_percentage"] = 0.0
                clean_item["pace_per_question"] = 0.0

            processed_data.append(clean_item)

        return processed_data

    except Exception as e:
        logger.error(f"Error loading study sessions: {e}")
        return []


def update_study_session(
    session_id: str,
    user_id: str,
    updates: Dict[str, Any],
) -> bool:
    """
    Update an existing study session.

    Args:
        session_id: Session UUID
        user_id: User UUID (for security)
        updates: Dictionary of fields to update

    Returns:
        True if successful
    """
    if not supabase:
        return False

    try:
        # Ensure user owns this session
        updates["user_id"] = user_id

        # Format date if present
        if "date" in updates:
            updates["date"] = _format_date_iso(updates["date"])

        supabase.table("study_sessions").update(updates).eq("id", session_id).eq(
            "user_id", user_id
        ).execute()

        return True

    except Exception as e:
        logger.error(f"Error updating study session: {e}")
        return False


def delete_study_session(session_id: str, user_id: str) -> bool:
    """
    Delete a study session and unlink related errors.

    Args:
        session_id: Session UUID
        user_id: User UUID (for security)

    Returns:
        True if successful
    """
    if not supabase:
        return False

    try:
        # First unlink errors from this session
        supabase.table("errors").update({"session_id": None}).eq(
            "session_id", session_id
        ).eq("user_id", user_id).execute()

        # Then delete the session
        supabase.table("study_sessions").delete().eq("id", session_id).eq(
            "user_id", user_id
        ).execute()

        return True

    except Exception as e:
        logger.error(f"Error deleting study session: {e}")
        return False


# =============================================================================
# MOCK EXAM OPERATIONS
# =============================================================================


def create_mock_exam(
    user_id: str,
    exam_name: str,
    exam_type: str,
    total_score: float,
    max_possible_score: float,
    date_val: date,
    breakdown_json: Optional[Dict[str, Any]] = None,
    notes: Optional[str] = None,
) -> Optional[str]:
    """
    Create a new mock exam record.

    Args:
        user_id: User UUID
        exam_name: Name of the exam (e.g., "FUVEST 2024 Phase 1")
        exam_type: Type of exam
        total_score: Points scored
        max_possible_score: Maximum possible points
        date_val: Date of the exam
        breakdown_json: Optional section breakdown
        notes: Optional notes

    Returns:
        Mock exam ID if successful, None otherwise
    """
    if not supabase:
        return None

    try:
        if total_score < 0:
            raise ValidationError("Score cannot be negative")
        if max_possible_score <= 0:
            raise ValidationError("Max score must be greater than 0")
        if total_score > max_possible_score:
            raise ValidationError("Score cannot exceed max possible score")

        payload = {
            "user_id": user_id,
            "exam_name": exam_name.strip(),
            "exam_type": exam_type,
            "total_score": round(total_score, 2),
            "max_possible_score": round(max_possible_score, 2),
            "date": _format_date_iso(date_val),
            "breakdown_json": breakdown_json or {},
            "notes": notes.strip() if notes else "",
        }

        response = supabase.table("mock_exams").insert(payload).execute()

        data = response.data
        if data and len(data) > 0:
            row = cast(Dict[str, Any], data[0])
            return str(row["id"])
        return None

    except Exception as e:
        logger.error(f"Error creating mock exam: {e}")
        st.error(f"Failed to create mock exam: {e}")
        return None


def load_mock_exams(user_id: str) -> List[Dict[str, Any]]:
    """
    Load mock exams with optimized column selection and type safety.

    CRITICAL: Includes breakdown_json column to prevent analysis page crashes.

    Returns:
        List of mock exam dictionaries with computed percentages and parsed dates
    """
    if not supabase:
        return []

    try:
        # OPTIMIZED: Select only necessary columns
        # CRITICAL: breakdown_json is REQUIRED for analysis page
        response = (
            supabase.table("mock_exams")
            .select(
                "id, user_id, exam_name, exam_type, total_score, max_possible_score, date, breakdown_json, notes"
            )
            .eq("user_id", user_id)
            .order("date", desc=True)
            .execute()
        )

        raw_data = (
            cast(List[Dict[str, Any]], response.data)
            if response.data is not None
            else []
        )

        processed_data: List[Dict[str, Any]] = []

        for item in raw_data:
            clean_item = item.copy()

            # TYPE SAFETY: Strict Date Parsing
            if clean_item.get("date"):
                try:
                    if isinstance(clean_item["date"], str):
                        dt = datetime.strptime(
                            clean_item["date"], DATE_FORMAT_ISO
                        ).date()
                        clean_item["date_obj"] = dt
                        clean_item["date"] = dt.strftime(DATE_FORMAT_DISPLAY)
                    else:
                        clean_item["date_obj"] = clean_item["date"]
                except (ValueError, TypeError):
                    clean_item["date_obj"] = date.today()
                    pass
            else:
                clean_item["date_obj"] = date.today()

            # Ensure score_percentage exists
            total_score = clean_item.get("total_score", 0) or 0
            max_score = clean_item.get("max_possible_score", 1) or 1

            clean_item["score_percentage"] = (
                (float(total_score) / float(max_score) * 100) if max_score > 0 else 0
            )

            # Convert Decimal to float for consistency
            for key in ("total_score", "max_possible_score", "score_percentage"):
                if key in clean_item and clean_item[key] is not None:
                    clean_item[key] = float(clean_item[key])

            processed_data.append(clean_item)

        return processed_data

    except Exception as e:
        logger.error(f"Error loading mock exams: {e}")
        return []


def update_mock_exam(
    exam_id: str,
    user_id: str,
    updates: Dict[str, Any],
) -> bool:
    """
    Update an existing mock exam.

    Args:
        exam_id: Mock exam UUID
        user_id: User UUID (for security)
        updates: Dictionary of fields to update

    Returns:
        True if successful
    """
    if not supabase:
        return False

    try:
        # Ensure user owns this exam
        updates["user_id"] = user_id

        # Format date if present
        if "date" in updates:
            updates["date"] = _format_date_iso(updates["date"])

        supabase.table("mock_exams").update(updates).eq("id", exam_id).eq(
            "user_id", user_id
        ).execute()

        return True

    except Exception as e:
        logger.error(f"Error updating mock exam: {e}")
        return False


def delete_mock_exam(exam_id: str, user_id: str) -> bool:
    """
    Delete a mock exam.

    Args:
        exam_id: Mock exam UUID
        user_id: User UUID (for security)

    Returns:
        True if successful
    """
    if not supabase:
        return False

    try:
        supabase.table("mock_exams").delete().eq("id", exam_id).eq(
            "user_id", user_id
        ).execute()

        return True

    except Exception as e:
        logger.error(f"Error deleting mock exam: {e}")
        return False


# =============================================================================
# ENHANCED ERROR LOGGING (with session linking)
# =============================================================================


def log_error_with_session(
    user_id: str,
    subject: str,
    topic: str,
    error_type: str,
    description: Optional[str],
    date_val: date,
    difficulty: str = "Medium",
    exam_type: str = "General",
    session_id: Optional[str] = None,
    mock_exam_id: Optional[str] = None,
) -> bool:
    """
    Log an error with optional session/mock exam linking and exam type.

    Args:
        user_id: User UUID
        subject: Subject of the error
        topic: Specific topic
        error_type: Type of error
        description: Optional description
        date_val: Date of the error
        difficulty: Difficulty level
        exam_type: Type of exam context
        session_id: Optional session ID to link this error to
        mock_exam_id: Optional mock exam ID to link this error to

    Returns:
        True if successful
    """
    if not supabase:
        return False

    try:
        _validate_input(subject, topic, error_type)

        payload = {
            "user_id": user_id,
            "subject": subject.strip(),
            "topic": topic.strip(),
            "type": error_type,
            "description": description.strip() if description else "",
            "date": _format_date_iso(date_val),
            "difficulty": difficulty,
            "exam_type": exam_type,
        }

        # Add session link if provided
        if session_id:
            payload["session_id"] = session_id

        # Add mock exam link if provided
        if mock_exam_id:
            payload["mock_exam_id"] = mock_exam_id

        supabase.table("errors").insert(payload).execute()
        return True

    except Exception as e:
        logger.error(f"Error logging error: {e}")
        st.error(f"Failed to save: {e}")
        return False
