import logging
from typing import Any, Optional

import streamlit as st

from src.services.db_service import supabase

logger = logging.getLogger(__name__)


def sign_in(email: str, password: str) -> Optional[Any]:
    """
    Autentica o usuário no Supabase.
    """
    if not supabase:
        logger.error("Erro: Cliente Supabase não inicializado.")
        st.error("Erro de conexão com o servidor de autenticação.")
        return None

    try:
        # [CORREÇÃO 3] O bloco try agora está completo com except
        response = supabase.auth.sign_in_with_password(
            {"email": email, "password": password}
        )

        logger.info(f"Usuário {email} logado com sucesso.")
        return response.user

    except Exception as e:
        logger.warning(f"Login falhou para {email}: {e}")
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
