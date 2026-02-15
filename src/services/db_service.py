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


def load_data(user_id: str) -> List[Dict[str, Any]]:
    """Carrega erros do usuário logado com segurança de tipos."""
    if not supabase:
        return []

    try:
        response = (
            supabase.table("errors")
            .select("*")
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
            # Agora o linter sabe que 'item' é um Dict, então .copy() é válido
            clean_item = item.copy()

            if clean_item.get("date"):
                try:
                    dt = datetime.strptime(str(clean_item["date"]), DATE_FORMAT_ISO)
                    clean_item["date"] = dt.strftime(DATE_FORMAT_DISPLAY)
                except (ValueError, TypeError):
                    pass

            processed_data.append(clean_item)

        return processed_data

    except Exception as e:
        logger.error(f"Erro ao carregar dados: {e}")
        return []


def log_error(
    user_id: str,
    subject: str,
    topic: str,
    error_type: str,
    description: Optional[str],
    date_val: date,
    difficulty: str = "Medium",
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
            if not rec.get("id"):
                continue

            clean_records.append(
                {
                    "id": rec["id"],
                    "user_id": user_id,
                    "subject": rec["subject"],
                    "topic": rec["topic"],
                    "type": rec["type"],
                    "description": rec.get("description", ""),
                    "date": _format_date_iso(rec["date"]),
                    "difficulty": rec.get("difficulty", "Medium"),
                }
            )

        if clean_records:
            supabase.table("errors").upsert(clean_records).execute()
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar: {e}")
        return False


# =============================================================================
# STUDY SESSION OPERATIONS
# =============================================================================


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
    Load all study sessions for a user.

    Returns:
        List of session dictionaries with computed metrics
    """
    if not supabase:
        return []

    try:
        response = (
            supabase.table("study_sessions")
            .select("*")
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

            # Format date for display
            if clean_item.get("date"):
                try:
                    dt = datetime.strptime(str(clean_item["date"]), DATE_FORMAT_ISO)
                    clean_item["date"] = dt.strftime(DATE_FORMAT_DISPLAY)
                except (ValueError, TypeError):
                    pass

            # Ensure computed fields exist (fallback if DB migration missing)
            total_q = clean_item.get("total_questions", 0) or 0
            correct = clean_item.get("correct_count", 0) or 0
            duration = clean_item.get("duration_minutes", 0) or 0

            if "accuracy_percentage" not in clean_item or clean_item["accuracy_percentage"] is None:
                clean_item["accuracy_percentage"] = (
                    (correct / total_q * 100) if total_q > 0 else 0
                )

            if "pace_per_question" not in clean_item or clean_item["pace_per_question"] is None:
                clean_item["pace_per_question"] = (
                    (duration / total_q) if total_q > 0 else 0
                )

            # Convert Decimal to float for JSON serialization
            for key in ("accuracy_percentage", "pace_per_question", "duration_minutes"):
                if key in clean_item and clean_item[key] is not None:
                    clean_item[key] = float(clean_item[key])

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
    Load all mock exams for a user.

    Returns:
        List of mock exam dictionaries with computed percentages
    """
    if not supabase:
        return []

    try:
        response = (
            supabase.table("mock_exams")
            .select("*")
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

            # Format date for display
            if clean_item.get("date"):
                try:
                    dt = datetime.strptime(str(clean_item["date"]), DATE_FORMAT_ISO)
                    clean_item["date"] = dt.strftime(DATE_FORMAT_DISPLAY)
                except (ValueError, TypeError):
                    pass

            # Ensure score_percentage exists (fallback if DB migration missing)
            total_score = clean_item.get("total_score", 0) or 0
            max_score = clean_item.get("max_possible_score", 1) or 1

            if "score_percentage" not in clean_item or clean_item["score_percentage"] is None:
                clean_item["score_percentage"] = (
                    (float(total_score) / float(max_score) * 100) if max_score > 0 else 0
                )

            # Convert Decimal to float
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
) -> bool:
    """
    Log an error with optional session linking and exam type.

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

        supabase.table("errors").insert(payload).execute()
        return True

    except Exception as e:
        logger.error(f"Error logging error: {e}")
        st.error(f"Failed to save: {e}")
        return False
