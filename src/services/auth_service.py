import logging
from typing import Any, Optional

import streamlit as st

from src.services.db_service import supabase

logger = logging.getLogger(__name__)


def sign_in(email: str, password: str) -> Optional[Any]:
    """
    Authenticate user with Supabase.
    On success, stores session tokens in st.session_state for cookie persistence.
    """
    if not supabase:
        logger.error("Error: Supabase client not initialized.")
        st.error("Authentication server connection error.")
        return None

    try:
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        if response and response.session:
            # Store tokens so app.py can save them to cookies
            st.session_state["access_token"] = response.session.access_token
            st.session_state["refresh_token"] = response.session.refresh_token
            st.session_state["_save_tokens"] = True

        logger.info(f"User {email} logged in successfully.")
        return response.user

    except Exception as e:
        logger.warning(f"Login failed for {email}: {e}")
        return None


def restore_session(access_token: str, refresh_token: str) -> Optional[Any]:
    """
    Restore a Supabase session from stored tokens (read from cookies).
    Returns the user object if the session is still valid, otherwise None.
    """
    if not supabase:
        return None

    try:
        response = supabase.auth.set_session(access_token, refresh_token)
        if response and response.user and response.session:
            # Tokens may have been refreshed — update session_state
            st.session_state["access_token"] = response.session.access_token
            st.session_state["refresh_token"] = response.session.refresh_token
            return response.user
        return None
    except Exception as e:
        logger.warning(f"Session restoration failed: {e}")
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
