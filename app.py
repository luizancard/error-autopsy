import time
from datetime import date

import streamlit as st

import database as db

errors = db.load_data()
DEFAULT_ERROR_TYPE = "Content Gap"

st.session_state.setdefault("subject_input", "")
st.session_state.setdefault("topic_input", "")
st.session_state.setdefault("description_input", "")
st.session_state.setdefault("error_type_select", DEFAULT_ERROR_TYPE)
st.session_state.setdefault("date_input", date.today())
st.session_state.setdefault("reset_form", False)
st.session_state.setdefault("success_message", "")
st.session_state.setdefault("show_success", False)
st.session_state.setdefault("current_menu", "Log Error")

st.set_page_config(page_title="Error Autopsy", layout="wide", page_icon="📝")


def local_css():
    st.markdown(
        """
        <style>
        .st-emotion-cache-1r6slb0 {
            background-color: white;
            padding: 2rem;
            border-radius: 25px;
            box-shadow: 0 7px 10px rgba(0, 0, 0, 0.05);
        }
        
        /* This rounds the corners of text inputs */
        .stTextInput > div > div > input {
            border-radius: 10px;
        }
        
        /* This styles the big headers */
        h1, h2, h3 {
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 700;
            color: #333;
        }
        
        /* Sidebar Header Styling */
        .sidebar-header-container {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.5rem;
            padding: 1rem 0;
        }
        
        .sidebar-logo-wrapper {
            position: relative;
            width: 50px;
            height: 50px;
            flex-shrink: 0;
        }
        
        .sidebar-logo {
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #1a2a4a 0%, #2d4563 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 20px rgba(26, 42, 74, 0.3), inset 0 1px 2px rgba(255, 255, 255, 0.2);
        }
        
        .sidebar-logo svg {
            width: 24px;
            height: 24px;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
        }
        
        .sidebar-title-group h1 {
            margin: 0;
            font-size: 1.4rem;
            color: #1a1a1a;
            font-weight: 800;
            letter-spacing: 0.08em;
        }
        
        /* Menu Buttons Styling */
        .sidebar-menu {
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
            margin-top: 2rem;
        }
        
        .menu-button {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.85rem 1.25rem;
            background: transparent;
            border: none !important;
            cursor: pointer;
            border-radius: 12px;
            transition: all 0.2s ease;
            position: relative;
            font-weight: 700 !important;
            width: 100%;
        }
        
        .menu-button:hover {
            background-color: #e8e8e8;
        }
        
        .menu-button svg {
            width: 20px;
            height: 20px;
            color: #9ca3af;
            transition: color 0.2s ease;
        }
        
        .menu-button span {
            color: #9ca3af;
            font-size: 1.05rem;
            font-weight: 700;
            transition: color 0.2s ease;
        }
        
        .menu-button.active {
            background: #eeeeeeff !important;
        }
        
        .menu-button.active svg {
            color: #6366f1;
        }
        
        .menu-button.active span {
            color: #1a1a1a;
            font-weight: 700;
        }
        
        .menu-button .indicator {
            position: absolute;
            right: 1rem;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #6366f1;
            opacity: 0;
            transition: opacity 0.2s ease;
        }
        
        .menu-button.active .indicator {
            opacity: 1;
        }
        </style>
        
        <script>
        function updateMenuButtons() {
            let currentMenu = '"""
        + st.session_state.current_menu
        + """';
            
            const buttonMap = {
                'Dashboard': 'Dashboard',
                'Log Mistake': 'Log Error',
                'IA Coach': 'Coach AI',
                'History': 'History'
            };
            
            const buttons = document.querySelectorAll('.menu-button');
            buttons.forEach(button => {
                const span = button.querySelector('span');
                const indicator = button.querySelector('.indicator');
                
                if (!span) return;
                
                const text = span.innerText.trim();
                let isActive = false;
                
                for (let btnText in buttonMap) {
                    if (text === btnText && buttonMap[btnText] === currentMenu) {
                        isActive = true;
                        break;
                    }
                }
                
                if (isActive) {
                    button.classList.add('active');
                    button.style.background = '#eeeeeeff';
                    span.style.color = '#1a1a1a';
                    button.querySelector('svg').style.color = '#6366f1';
                    indicator.style.opacity = '1';
                } else {
                    button.classList.remove('active');
                    button.style.background = 'transparent';
                    span.style.color = '#9ca3af';
                    button.querySelector('svg').style.color = '#9ca3af';
                    indicator.style.opacity = '0';
                }
            });
        }
        
        document.addEventListener('DOMContentLoaded', updateMenuButtons);
        window.addEventListener('load', updateMenuButtons);
        </script>
        """,
        unsafe_allow_html=True,
    )


local_css()

# Custom sidebar with professional design
with st.sidebar:
    # Header with logo and title
    st.markdown(
        """
        <div class="sidebar-header-container">
            <div class="sidebar-logo-wrapper">
                <div class="sidebar-logo">
                    <svg viewBox="0 0 24 24" fill="white">
                        <path d="M12 2c.2 0 .4.1.5.3l2.3 4.7 5.2.8c.2 0 .4.2.4.4s-.1.4-.3.5l-3.8 3.7.9 5.2c0 .2-.1.4-.3.5-.2.1-.4.1-.6 0L12 15.2l-4.7 2.5c-.2.1-.4.1-.6 0-.2-.1-.3-.3-.3-.5l.9-5.2-3.8-3.7c-.2-.1-.3-.3-.3-.5s.2-.4.4-.4l5.2-.8 2.3-4.7c.1-.2.3-.3.5-.3z"/>
                    </svg>
                </div>
            </div>
            <div class="sidebar-title-group">
                <h1>AUTOPSY</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Menu items with icons
    st.markdown('<div class="sidebar-menu">', unsafe_allow_html=True)

    # Dashboard button
    st.markdown(
        """
        <button class="menu-button" onclick="window.location.reload()">
            <svg viewBox="0 0 24 24" fill="currentColor">
                <path d="M3 5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5z"></path>
                <path d="M13 5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V5z"></path>
                <path d="M3 15a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4z"></path>
                <path d="M13 15a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-4z"></path>
            </svg>
            <span>Dashboard</span>
            <div class="indicator"></div>
        </button>
        """,
        unsafe_allow_html=True,
    )
    if st.session_state.current_menu == "Dashboard":
        st.session_state.current_menu = "Dashboard"

    # Log Error button
    st.markdown(
        """
        <button class="menu-button" onclick="window.location.reload()">
            <svg viewBox="0 0 24 24" fill="currentColor">
                <circle cx="12" cy="12" r="10"></circle>
                <path d="M12 7v10M7 12h10" stroke="white" stroke-width="1.5" stroke-linecap="round"></path>
            </svg>
            <span>Log Mistake</span>
            <div class="indicator"></div>
        </button>
        """,
        unsafe_allow_html=True,
    )

    # Coach AI button
    st.markdown(
        """
    <button class="menu-button" onclick="window.location.reload()">
        <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M2 9 L12 4 L22 9 L12 14 Z"/>
            <path d="M6 11.5 V15 C6 16.5 18 16.5 18 15 V11.5 L12 14.5 Z"/>
            <path d="M18.5 9.5 V14 C18.5 14.8 17.5 15.2 17 15.2
                    C16.5 15.2 15.5 14.8 15.5 14
                    V12.8 C15.5 12.4 15.8 12.1 16.2 12.1
                    C16.6 12.1 16.9 12.4 16.9 12.8
                    V13.6 C16.9 13.8 17.2 14 17.5 14
                    C17.8 14 18.1 13.8 18.1 13.6
                    V9.5 Z"/>
        </svg>
        <span>IA Coach</span>
        <div class="indicator"></div>
    </button>
    """,
        unsafe_allow_html=True,
    )

    # History button
    st.markdown(
        """
        <button class="menu-button" onclick="window.location.reload()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                <circle cx="12" cy="12" r="9"></circle>
                <path d="M12 6v6l4 2"></path>
            </svg>
            <span>History</span>
            <div class="indicator"></div>
        </button>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    menu = st.session_state.current_menu

if menu == "Log Error":
    st.title("📝 Log a New Mistake")
    with st.container(border=True):
        # st.subheader("📝 Log a New Mistake")

        if st.session_state.reset_form:
            st.session_state.subject_input = ""
            st.session_state.topic_input = ""
            st.session_state.description_input = ""
            st.session_state.error_type_select = DEFAULT_ERROR_TYPE
            st.session_state.date_input = date.today()
            st.session_state.reset_form = False

        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input(
                "Subject", placeholder="e.g., Math", key="subject_input"
            )
            topic = st.text_input(
                "Topic", placeholder="e.g., Geometry", key="topic_input"
            )
        with col2:
            date_input = st.date_input("Date", key="date_input")
            error_type = st.selectbox(
                "Error Type",
                [
                    "Content Gap",
                    "Attention Detail",
                    "Time Management",
                    "Fatigue",
                    "Interpretation",
                ],
                key="error_type_select",
            )

        description = st.text_area(
            "Description", placeholder="What exactly happened?", key="description_input"
        )

        # Adding some space before the button
        st.write("")

        if st.button("Save Error", type="primary"):
            new_id = len(errors) + 1
            formatted_date = date_input.strftime("%d-%m-%Y")

            new_error = {
                "id": new_id,
                "date": formatted_date,
                "subject": subject,
                "topic": topic,
                "description": description,
                "type": error_type,
            }
            errors.append(new_error)
            db.save_data(errors)

            # Save the success message to session state
            st.session_state.success_message = f"Error {new_id} Saved Successfully!"
            st.session_state.show_success = True
            st.session_state.reset_form = True
            if st.session_state.show_success:
                st.success(st.session_state.success_message)
                time.sleep(1)
                st.session_state.show_sucess = False

            st.rerun()
