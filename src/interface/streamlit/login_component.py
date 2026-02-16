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
                <p style="color: #64748b; ">Access your account to continue</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        # creating 2 tabs to separete the login x sign up
        tab_login, tab_signup = st.tabs(["Log In", "Sign Up"])
        with tab_login:
            st.markdown("")
            with st.form("login_form"):
                email = st.text_input("Email", placeholder="your@email.com")
                password = st.text_input(
                    "Password", type="password", placeholder="••••••••"
                )
                submit_login = st.form_submit_button(
                    "Log In", width="stretch", type="primary"
                )

            if submit_login:
                if not email or not password:
                    st.warning("Please fill in all fields.")
                else:
                    with st.spinner("Authenticating..."):
                        # Call the authentication service we created
                        user = auth_service.sign_in(email, password)

                        if user:
                            # Success! Save to session and reload
                            st.session_state["user"] = user
                            st.success("Logged in successfully!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Incorrect email or password.")
        with tab_signup:
            st.markdown("")
            with st.form("signup_form"):
                new_email = st.text_input("Email", placeholder="your@email.com")
                new_password = st.text_input(
                    "Password", type="password", placeholder="••••••••"
                )
                submit_signup = st.form_submit_button(
                    "Sign Up", width="stretch"
                )

                if submit_signup:
                    if not new_email or not new_password:
                        st.warning("Please fill in all fields.")
                    elif len(new_password) < 6:
                        st.warning("The password must be at least 6 characters.")
                    else:
                        with st.spinner("Creating account..."):
                            success = auth_service.sign_up(new_email, new_password)
                        if success:
                            st.success(
                                "Account created! You can now log in on the tab above."
                            )
                        else:
                            st.error(
                                "Failed to create account. Please check your email."
                            )
