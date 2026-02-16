"""
Exam Telemetry System - Main Application

A Streamlit application for tracking and analyzing exam performance through:
- Study session logging
- Mock exam (simulado) tracking
- Error analysis with AI insights
"""

from datetime import date
from typing import Any, Dict, List, cast

import pandas as pd
import streamlit as st
from streamlit_cookies_controller import CookieController

from assets import styles
from config import (
    DEFAULT_DIFFICULTY,
    DEFAULT_ERROR_TYPE,
    AppConfig,
    TimeFilter,
)
from config.icons import (
    ICON_DASHBOARD,
    ICON_HISTORY,
    ICON_LOG_ERROR,
    ICON_MOCK_ANALYSIS,
)
from src.interface.streamlit import components as ui
from src.interface.streamlit import dashboard_components as dash
from src.interface.streamlit import history_components as hist
from src.interface.streamlit import login_component
from src.interface.streamlit import mock_exam_analysis_components as mock_analysis
from src.interface.streamlit import telemetry_components as telemetry
from src.services import auth_service, excel_service
from src.services import db_service as db
from src.services.db_service import supabase

# App Configuration
st.set_page_config(
    page_title=AppConfig.PAGE_TITLE,
    layout=AppConfig.LAYOUT,
    page_icon=AppConfig.PAGE_ICON,
    initial_sidebar_state="expanded",
)


def init_session_state() -> None:
    """Initialize all session state defaults."""
    defaults = {
        "user": None,
        "subject_input": "",
        "topic_input": "",
        "description_input": "",
        "error_type_select": DEFAULT_ERROR_TYPE,
        "difficulty_select": DEFAULT_DIFFICULTY,
        "date_input": date.today(),
        "time_filter": TimeFilter.DEFAULT,
        "reset_form": False,
        "success_message": "",
        "show_success": False,
        "chart_view": 0,
        "current_menu": "Dashboard",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


init_session_state()
styles.local_css()

# Cookie controller for persistent login (24h)
cookie_controller = CookieController()

# Wait for cookies to load from browser before deciding auth state.
# On first render the JS component hasn't communicated yet, so getAll() is empty.
all_cookies = cookie_controller.getAll()
_cookies_ready = all_cookies is not None and len(all_cookies) > 0

# Try to restore session from browser cookies on page reload
if not st.session_state["user"]:
    if _cookies_ready:
        access_token = cookie_controller.get("sb_access_token")
        refresh_token = cookie_controller.get("sb_refresh_token")
        if access_token and refresh_token:
            user = auth_service.restore_session(access_token, refresh_token)
            if user:
                st.session_state["user"] = user
            else:
                # Tokens expired or invalid — clean up
                cookie_controller.remove("sb_access_token")
                cookie_controller.remove("sb_refresh_token")
        else:
            # Cookies loaded but no tokens → truly not logged in
            st.session_state["_no_tokens"] = True
    elif not st.session_state.get("_no_tokens"):
        # Cookies haven't arrived yet — show loading instead of login flash
        st.markdown(
            """
            <div style="display:flex;flex-direction:column;align-items:center;justify-content:center;height:60vh;">
                <p style="color:#94a3b8;font-size:1.1rem;">Loading session...</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.stop()

# Save tokens to cookies right after a fresh login
if st.session_state.get("_save_tokens"):
    cookie_controller.set(
        "sb_access_token",
        st.session_state["access_token"],
        max_age=86400,  # 24 hours
    )
    cookie_controller.set(
        "sb_refresh_token",
        st.session_state["refresh_token"],
        max_age=86400,
    )
    del st.session_state["_save_tokens"]

# Check authentication
if not st.session_state["user"]:
    login_component.render_login()
    st.stop()

# User data
current_user = st.session_state["user"]
user_id = current_user.id

# Load all user data
errors = db.load_data(user_id)
sessions = db.load_study_sessions(user_id)
mock_exams = db.load_mock_exams(user_id)


# Page Renderers


def render_dashboard() -> None:
    """Render the telemetry dashboard with advanced analytics."""
    time_filter = st.session_state.get("time_filter", TimeFilter.DEFAULT)
    dash.render_telemetry_dashboard(errors, sessions, mock_exams, time_filter)


def render_log_session() -> None:
    """Render the session and exam logging interface."""
    telemetry.render_tabbed_logger(user_id)


def render_mock_analysis() -> None:
    """Render the mock exam analysis page."""
    mock_analysis.render_mock_exam_analysis(mock_exams, errors)


def render_history() -> None:
    """Render the history page with import/export functionality."""
    st.title("History")

    # Export/Import buttons
    col1, col2, col3 = st.columns([2, 1, 1])

    with col2:
        if st.button("Import Data", use_container_width=True):
            st.session_state["show_import"] = True

    with col3:
        if st.button("Export Data", use_container_width=True):
            # Generate Excel file
            excel_buffer = excel_service.export_to_excel(errors, sessions, mock_exams)

            st.download_button(
                label="Download Excel",
                data=excel_buffer,
                file_name=f"exam_telemetry_export_{date.today().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )

    # Import modal
    if st.session_state.get("show_import", False):
        with st.expander(" Import Data", expanded=True):
            uploaded_file = st.file_uploader(
                "Upload Excel File",
                type=["xlsx", "xls"],
                help="Upload a file exported from this system or a compatible Excel file",
            )

            if uploaded_file:
                errors_import, sessions_import, exams_import = (
                    excel_service.import_from_excel(uploaded_file, user_id)
                )

                # Validate
                is_valid, issues = excel_service.validate_import_data(
                    errors_import, sessions_import, exams_import
                )

                if not is_valid:
                    st.error("**Validation Issues:**")
                    for issue in issues:
                        st.write(f"- {issue}")
                else:
                    st.success("Ready to import:")
                    st.info(
                        f"- {len(errors_import)} errors\n"
                        f"- {len(sessions_import)} study sessions\n"
                        f"- {len(exams_import)} mock exams"
                    )

                    if st.button("Confirm Import", type="primary"):
                        # Import data
                        success_count = 0

                        # Import sessions (rename date->date_val, strip user_id)
                        for session in sessions_import:
                            s = session.copy()
                            s["date_val"] = s.pop("date", date.today())
                            s.pop("user_id", None)
                            if db.create_study_session(user_id=user_id, **s):
                                success_count += 1

                        # Import exams
                        for exam in exams_import:
                            e = exam.copy()
                            e["date_val"] = e.pop("date", date.today())
                            e.pop("user_id", None)
                            if db.create_mock_exam(user_id=user_id, **e):
                                success_count += 1

                        # Import errors
                        for error in errors_import:
                            er = error.copy()
                            er["date_val"] = er.pop("date", date.today())
                            er.pop("user_id", None)
                            if db.log_error_with_session(user_id=user_id, **er):
                                success_count += 1

                        st.success(f"Imported {success_count} records!")
                        st.session_state["show_import"] = False
                        st.rerun()

            if st.button("Cancel"):
                st.session_state["show_import"] = False
                st.rerun()

    st.divider()

    # Tabbed view for Errors and Study Sessions
    tab1, tab2 = st.tabs(["Errors History", "Study Sessions"])

    with tab1:
        # Existing history functionality
        hist.render_filter_popup(errors)
        hist.render_active_filters()
        filters = st.session_state.history_filters
        filtered_data = hist.apply_filters(errors, filters)

        st.markdown(
            f'<p style="color:#64748b;font-size:0.95rem;">Showing <strong>{len(filtered_data)}</strong> of <strong>{len(errors)}</strong> records</p>',
            unsafe_allow_html=True,
        )

        if filtered_data:
            edited_df = hist.render_editable_table(filtered_data)

            if edited_df is not None:
                col1, col2 = st.columns([3, 1])
                
                # Handle deletes first - convert to pandas Series for operations
                delete_col = edited_df.get("Delete")
                if delete_col is not None and not isinstance(delete_col, pd.Series):
                    delete_mask = pd.Series(delete_col)
                elif delete_col is not None:
                    delete_mask = delete_col
                else:
                    delete_mask = pd.Series([False] * len(edited_df))
                
                if delete_mask.any():
                    with col2:
                        st.warning(f"{int(delete_mask.sum())} error(s) marked for deletion")
                
                # Remove delete column and rows marked for deletion before saving
                edited_df_to_save = edited_df[~delete_mask].drop(columns=["Delete"], errors="ignore")
                
                with col1:
                    if st.button(
                        "Save Changes",
                        use_container_width=True,
                        type="primary",
                        key="save_errors",
                    ):
                        # First delete marked records
                        if delete_mask.any():
                            ids_to_delete = edited_df[delete_mask]["ID"].tolist()
                            if db.delete_errors(user_id, ids_to_delete):
                                st.success(f"Deleted {len(ids_to_delete)} error(s)!")
                        
                        # Then save updated records
                        if len(edited_df_to_save) > 0:
                            updated_records = cast(
                                List[Dict[str, Any]], edited_df_to_save.to_dict("records")
                            )
                            if db.update_errors(user_id, updated_records):
                                st.success("Changes saved successfully!")
                        
                        st.rerun()
        else:
            st.info("No records match your filters.")

    with tab2:
        st.markdown(
            f'<p style="color:#64748b;font-size:0.95rem;">Total <strong>{len(sessions)}</strong> study sessions</p>',
            unsafe_allow_html=True,
        )

        if sessions:
            edited_sessions_df = hist.render_editable_sessions_table(sessions)
            if edited_sessions_df is not None:
                # Handle deletes first - convert to pandas Series for operations
                delete_col = edited_sessions_df.get("Delete")
                if delete_col is not None and not isinstance(delete_col, pd.Series):
                    delete_mask = pd.Series(delete_col)
                elif delete_col is not None:
                    delete_mask = delete_col
                else:
                    delete_mask = pd.Series([False] * len(edited_sessions_df))
                
                if delete_mask.any():
                    st.warning(f"{int(delete_mask.sum())} session(s) marked for deletion")
                
                # Remove delete column and rows marked for deletion before saving
                edited_sessions_df_to_save = edited_sessions_df[~delete_mask].drop(columns=["Delete"], errors="ignore")
                
                if st.button(
                    "Save Changes",
                    use_container_width=True,
                    type="primary",
                    key="save_sessions",
                ):
                    # First delete marked records
                    if delete_mask.any():
                        ids_to_delete = edited_sessions_df[delete_mask]["ID"].tolist()
                        for id_val in ids_to_delete:
                            supabase.table("study_sessions").delete().eq("id", id_val).execute()
                        st.success(f"Deleted {len(ids_to_delete)} session(s)!")
                    
                    # Then save updated records
                    if len(edited_sessions_df_to_save) > 0:
                        updated_sessions = cast(
                            List[Dict[str, Any]], edited_sessions_df_to_save.to_dict("records")
                        )
                        if db.update_sessions(user_id, updated_sessions):
                            st.success("Changes saved successfully!")
                    
                    st.rerun()
        else:
            st.info("No study sessions found. Log some sessions to see them here!")


# Sidebar navigation
with st.sidebar:
    ui.render_sidebar_header()
    # Mostra quem está logado
    st.markdown(
        f"""
        <div style="padding: 10px; background: rgba(0,0,0,0.03); border-radius: 8px; margin-bottom: 20px; border: 1px solid rgba(0,0,0,0.05);">
            <small style="color: #94a3b8; font-weight: 600; text-transform: uppercase; font-size: 0.7rem; letter-spacing: 0.05em;">Logged in as</small>
            <div style="color: #64748b; font-weight: 500; font-size: 0.85rem; overflow: hidden; text-overflow: ellipsis;">{current_user.email}</div>
        </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="sidebar-menu">', unsafe_allow_html=True)
    ui.render_menu_button("Dashboard", "Dashboard", ICON_DASHBOARD)
    ui.render_menu_button("Log Session", "Log Session", ICON_LOG_ERROR)
    ui.render_menu_button("Mock Analysis", "Mock Analysis", ICON_MOCK_ANALYSIS)
    ui.render_menu_button("History", "History", ICON_HISTORY)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown(
        """
        <style>
        div[data-testid="stSidebar"] button[kind="secondary"] {
            background: transparent !important;
            border: 1px solid rgba(0,0,0,0.1) !important;
            color: #64748b !important;
            transition: all 0.2s ease !important;
        }
        div[data-testid="stSidebar"] button[kind="secondary"]:hover {
            background: rgba(0,0,0,0.05) !important;
            border-color: rgba(0,0,0,0.15) !important;
        }
        </style>
    """,
        unsafe_allow_html=True,
    )
    if st.button("Log Out", use_container_width=True, type="secondary"):
        auth_service.sign_out()
        st.session_state["user"] = None
        st.session_state.pop("access_token", None)
        st.session_state.pop("refresh_token", None)
        st.session_state.pop("_no_tokens", None)
        cookie_controller.remove("sb_access_token")
        cookie_controller.remove("sb_refresh_token")
        st.rerun()

raw_menu = st.query_params.get("menu", "Dashboard")
menu = raw_menu[0] if isinstance(raw_menu, list) else raw_menu
st.session_state["current_menu"] = menu

# Route to page
if menu == "Dashboard":
    render_dashboard()
elif menu == "Log Session":
    render_log_session()
elif menu == "Mock Analysis":
    render_mock_analysis()
elif menu == "History":
    render_history()
else:
    # Fallback for legacy menu items
    render_log_session()
