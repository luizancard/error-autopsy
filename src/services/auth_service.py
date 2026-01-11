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


def sign_out() -> bool:
    if not supabase:
        return False

    try:
        supabase.auth.sign_out()
        return True
    except Exception as e:
        logger.error(f"Erro no logout: {e}")
        return False
