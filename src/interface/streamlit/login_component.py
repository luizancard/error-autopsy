import time

import streamlit as st
from src.services import auth_service


def render_login():
    col1, col2, col3 = st.columns([1, 2, 1])

    with col2:
        st.markdown(
            """
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1>Autopsy Login</h1>
                <p style="color: #64748b; ">Acess your account to continue</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # creating 2 tabs to separete the login x sign up
        tab_login, tab_signup = st.tabs([""])
        with st.form("login_form"):
            email = st.text_input("E-mail", placeholder="seu@email.com")
            password = st.text_input("Senha", type="password", placeholder="••••••••")

            submit = st.form_submit_button(
                "Entrar", use_container_width=True, type="primary"
            )

            if submit:
                if not email or not password:
                    st.warning("Preencha todos os campos.")
                else:
                    with st.spinner("Autenticando..."):
                        # Chama o serviço de autenticação que criamos
                        user = auth_service.sign_in(email, password)

                        if user:
                            # Sucesso! Salva na sessão e recarrega
                            st.session_state["user"] = user
                            st.success("Login realizado com sucesso!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("E-mail ou senha incorretos.")

        st.markdown(
            """
            <div style="text-align: center; margin-top: 1rem; font-size: 0.8rem; color: #94a3b8;">
                Ainda não tem conta? Peça ao administrador para criar uma no Supabase.
            </div>
            """,
            unsafe_allow_html=True,
        )
