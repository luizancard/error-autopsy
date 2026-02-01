import logging
from typing import Any, Optional

import streamlit as st

from src.services.db_service import supabase

logger = logging.getLogger(__name__)


def get_session() -> Optional[Any]:
    """
    Get current session from Supabase.
    """
    if not supabase:
        return None

    try:
        session = supabase.auth.get_session()
        if session and session.user:
            return session.user
        return None
    except Exception as e:
        logger.error(f"Error getting session: {e}")
        return None


def sign_in(email: str, password: str) -> Optional[Any]:
    """
    Authenticate user with Supabase.
    """
    if not supabase:
        logger.error("Error: Supabase client not initialized.")
        st.error("Authentication server connection error.")
        return None

    try:
        # [CORREÇÃO 3] O bloco try agora está completo com except
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        logger.info(f"User {email} logged in successfully.")
        return response.user

    except Exception as e:
        logger.warning(f"Login failed for {email}: {e}")
        return None


def sign_up(email: str, password: str) -> bool:
    if not supabase:
        st.error("Connection Error")
        return False
    try:
        response = supabase.auth.sign_up({"email": email, "password": password})
        if response.user:
            logger.info(f"Account created: {email}")
            return True
        return False
    except Exception as e:
        logger.error(f"Error in creating the account: {e}")
        return False


def sign_out() -> bool:
    if not supabase:
        return False

    try:
        supabase.auth.sign_out()
        return True
    except Exception as e:
        logger.error(f"Logout Error: {e}")
        return False
