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
        with st.form("login_form"):
            email = st.text_input("E-mail", placeholder="your@email.com")
            password = st.text_input("Password", type="password")

            submit = st.form_submit_button(
                "Enter", use_container_width=True, type="primary"
            )

            if submit:
                if not email or not password:
                    st.warning("Fill in all the fields")
                else:
                    with st.spinner("Authenticating...."):
                        user = auth_service.sign_in(email, password)
                    if user:
                        st.session_state["suer"] = user
                        st.success("Login completed with success!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("E-mail or Password incorrect.")
        st.markdown(
            """
            <div style="text-align: center; margin-top: 1rem; font-size: 0.8rem; color: #94a3b8;>
                No account? Create One
            """,
            unsafe_allow_html=True,
        )
