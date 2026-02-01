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
                }
            )

        if clean_records:
            supabase.table("errors").upsert(clean_records).execute()
        return True
    except Exception as e:
        logger.error(f"Erro ao atualizar: {e}")
        return False
