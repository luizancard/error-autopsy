"""
Error Autopsy - Main Application

A Streamlit application for tracking and analyzing learning mistakes.
"""

import importlib
from datetime import date
from typing import Any, Dict, List, cast

import streamlit as st

from assets import styles
from config import (
    AVOIDABLE_ERROR_TYPES,
    DEFAULT_ERROR_TYPE,
    ERROR_TYPES,
    AppConfig,
    Colors,
    TimeFilter,
)
from config.icons import ICON_BOOK, ICON_DASHBOARD, ICON_HISTORY, ICON_LOG_ERROR
from src.analysis import metrics as mt
from src.analysis import plots as pt
from src.interface.streamlit import components as ui
from src.interface.streamlit import history_components as hist
from src.interface.streamlit import login_component
from src.services import auth_service
from src.services import db_service as db

importlib.reload(mt)

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

# Check authentication - try to restore session first
if not st.session_state["user"]:
    # Try to get existing session from Supabase
    existing_user = auth_service.get_session()
    if existing_user:
        st.session_state["user"] = existing_user
    else:
        # No session found, show login
        login_component.render_login()
        st.stop()

# User data
current_user = st.session_state["user"]
user_id = current_user.id

# Loading user errors
errors = db.load_data(user_id)

# Helper Functions


def calculate_dashboard_metrics(
    data: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calculate all dashboard metrics from filtered data.

    Args:
        data: Filtered list of error records.

    Returns:
        Dictionary with total, top_subject, top_type, avoidable_count, avoidable_pct.
    """
    total = len(data)

    # Subject counts
    subj_counts: Dict[str, int] = {}
    for r in data:
        s = r.get("subject", "Unknown") or "Unknown"
        subj_counts[s] = subj_counts.get(s, 0) + 1
    top_subject = (
        max(subj_counts.items(), key=lambda x: x[1])[0] if subj_counts else "—"
    )

    # Type counts
    type_counts: Dict[str, int] = {}
    for r in data:
        t = r.get("type", "Other") or "Other"
        type_counts[t] = type_counts.get(t, 0) + 1
    top_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "—"

    # Avoidable errors
    avoidable_count = sum(
        type_counts.get(error_type, 0) for error_type in AVOIDABLE_ERROR_TYPES
    )
    avoidable_pct = (avoidable_count / total * 100) if total > 0 else 0.0

    return {
        "total": total,
        "top_subject": top_subject,
        "top_type": top_type,
        "avoidable_count": avoidable_count,
        "avoidable_pct": avoidable_pct,
    }


def render_dashboard_metrics(metrics: Dict[str, Any]) -> None:
    """
    Render the metric cards row.

    Args:
        metrics: Dictionary from calculate_dashboard_metrics.
    """
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ui.render_metric_card(
            label="Total Errors",
            value=metrics["total"],
            icon_char="!",
            icon_bg=Colors.CARD_TOTAL_BG,
            icon_color=Colors.CARD_TOTAL_COLOR,
        )

    with col2:
        ui.render_metric_card(
            label="Subject with Most Errors",
            value=metrics["top_subject"],
            icon_char=ICON_BOOK,
            icon_bg=Colors.CARD_SUBJECT_BG,
            icon_color=Colors.CARD_SUBJECT_COLOR,
        )

    with col3:
        ui.render_metric_card(
            label="Primary Error Reason",
            value=metrics["top_type"],
            icon_char="⚡",
            icon_bg=Colors.CARD_ERROR_BG,
            icon_color=Colors.CARD_ERROR_COLOR,
        )

    with col4:
        ui.render_metric_card(
            label="Avoidable Errors",
            value=metrics["avoidable_count"],
            icon_char="⚠️",
            icon_bg=Colors.CARD_AVOIDABLE_BG,
            icon_color=Colors.CARD_AVOIDABLE_COLOR,
            pill_text=f"{metrics['avoidable_pct']:.1f}%",
            pill_class="pill-negative",
        )


def render_chart_section(
    chart_errors: List[Dict[str, Any]], selected_filter: str
) -> None:
    """
    Render the chart section with toggle between views.

    Args:
        chart_errors: Filtered error data for charts.
        selected_filter: Current time filter label for messages.
    """
    current_view = st.session_state.chart_view
    subtitles = ["Analysis by discipline", "Analysis by topic", "Timeline overview"]

    if current_view >= len(subtitles):
        current_view = 0
        st.session_state.chart_view = 0

    col_title, col_button = st.columns([12, 1])
    with col_title:
        ui.render_chart_header(subtitles[current_view])

    with col_button:
        if st.button("→", key="chart_toggle", help="Toggle view"):
            st.session_state.chart_view = (current_view + 1) % len(subtitles)
            st.rerun()

    if current_view == 0:
        _render_subject_chart(chart_errors, selected_filter)
    elif current_view == 1:
        _render_topic_chart(chart_errors, selected_filter)
    else:
        _render_timeline_chart(chart_errors)


def _render_subject_chart(
    chart_errors: List[Dict[str, Any]], selected_filter: str
) -> None:
    """Render subject analysis chart with drill-down support."""
    subject_data = mt.aggregate_by_subject(chart_errors)

    if not subject_data:
        st.info(f"No data available for {selected_filter}. Log some errors!")
        return

    chart = pt.chart_subjects(subject_data)
    if chart:
        event = st.altair_chart(
            chart,
            use_container_width=True,
            on_select="rerun",
            key="subject_chart_select",
        )

        if event and "selection" in event and "selected_subjects" in event["selection"]:
            selection_list = event["selection"]["selected_subjects"]
            if selection_list:
                selected_subj_name = selection_list[0].get("Subject")
                if selected_subj_name:
                    st.session_state.drill_down_subject = selected_subj_name
                    st.session_state.chart_view = 1
                    st.rerun()


def _render_topic_chart(
    chart_errors: List[Dict[str, Any]], selected_filter: str
) -> None:
    """Render topic analysis chart with optional drill-down filter."""
    target_subject = st.session_state.get("drill_down_subject")

    if target_subject:
        c_back, c_text = st.columns([1.5, 8])
        with c_back:
            if st.button("← Back", key="clear_drill_down", help="Clear Subject Filter"):
                st.session_state.drill_down_subject = None
                st.session_state.chart_view = 0
                st.rerun()
        with c_text:
            ui.render_drill_down_info(target_subject)

        filtered_errors = [
            e for e in chart_errors if e.get("subject") == target_subject
        ]
        topic_data = mt.aggregate_by_topic(filtered_errors)
    else:
        topic_data = mt.aggregate_by_topic(chart_errors)

    if not topic_data:
        st.info(f"No data available for {selected_filter}. Log some errors!")
        return

    chart = pt.chart_topics(topic_data)
    if chart:
        st.altair_chart(chart, use_container_width=True)


def _render_timeline_chart(chart_errors: List[Dict[str, Any]]) -> None:
    """Render timeline chart."""
    month_data = mt.aggregate_by_month_all(chart_errors)
    chart = pt.chart_timeline(month_data)
    if chart:
        st.altair_chart(chart, use_container_width=True)


def render_insight_panel(chart_errors: List[Dict[str, Any]]) -> None:
    """
    Render the insight panel with cached insights.

    Args:
        chart_errors: Error data to generate insights from.
    """
    qp = st.query_params
    if qp.get("refresh_insight") == "true":
        st.session_state.dashboard_insight = ui.generate_web_insight(chart_errors)

    if (
        "dashboard_insight" not in st.session_state
        or st.session_state.dashboard_insight is None
        or str(st.session_state.dashboard_insight) == "None"
    ):
        st.session_state.dashboard_insight = ui.generate_web_insight(chart_errors)

    mini_insight = st.session_state.dashboard_insight
    if mini_insight is None or str(mini_insight) == "None":
        mini_insight = "Insight generation failed. Please log new errors!"

    st.markdown(
        f"""
        <div class="insight-card">
            <div style="display:flex; justify-content:space-between; align-items:center;">
                <h3 class="insight-title" style="color: #eeeeee; margin:0;">Insight</h3>
            </div>
            <div class="insight-content">{mini_insight}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_pie_chart_section(data: List[Dict[str, Any]], selected_filter: str) -> None:
    """
    Render the error breakdown pie chart section.

    Args:
        data: Filtered error data.
        selected_filter: Current time filter label.
    """
    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)
    st.markdown(
        """
        <h3 style="font-family:'Helvetica Neue', sans-serif;font-size:1.35rem;font-weight:800;color:#0f172a;margin:0 0 0.4rem 0;letter-spacing:0.08em;text-transform:uppercase;">Error Breakdown</h3>
        <p style="font-family:'Helvetica Neue', sans-serif;font-size:0.95rem;color:#94a3b8;font-weight:500;font-style:italic;margin:0 0 1.5rem 0;">Distribution by mistake type</p>
        """,
        unsafe_allow_html=True,
    )

    col_content, _ = st.columns([3, 2])
    with col_content:
        type_data = mt.count_error_types(data)
        if not type_data:
            st.info(f"No data available for {selected_filter}.")
        else:
            chart = pt.chart_error_types_pie(type_data)
            if chart:
                st.altair_chart(chart, use_container_width=True)


# Page Renderers


def render_dashboard() -> None:
    """Render the main dashboard page."""
    st.title("Your Progress")

    # Time filter
    col_filter, _ = st.columns([2, 5])
    with col_filter:
        selected_filter = st.selectbox(
            "Time Period",
            options=TimeFilter.OPTIONS,
            index=TimeFilter.OPTIONS.index(
                st.session_state.get("time_filter", TimeFilter.DEFAULT)
            ),
            key="time_filter_select",
        )
        st.session_state.time_filter = selected_filter

    months_filter = TimeFilter.MONTHS_MAP[selected_filter]
    filtered_errors = mt.filter_data_by_range(errors, months_filter)

    # Metrics row
    metrics = calculate_dashboard_metrics(filtered_errors)
    render_dashboard_metrics(metrics)

    # Charts and insights
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)
    chart_col, insight_col = st.columns([2, 1])

    with chart_col:
        render_chart_section(filtered_errors, selected_filter)

    with insight_col:
        render_insight_panel(filtered_errors)

    # Pie chart section
    render_pie_chart_section(filtered_errors, selected_filter)


def render_log_error() -> None:
    """Render the log error form page."""
    st.title("Log a New Mistake")

    with st.container(border=True):
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
                "Error Type", ERROR_TYPES, key="error_type_select"
            )

        description = st.text_area(
            "Description (Optional)",
            placeholder="Why do you think this happened?",
            key="description_input",
        )

        if st.button("Log a Mistake", use_container_width=True):
            if db.log_error(
                user_id, subject, topic, error_type, description, date_input
            ):
                st.toast(f"Logged error for {subject}.")
                st.session_state.reset_form = True
                st.rerun()


def render_history() -> None:
    st.title("History")

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
        if edited_df is not None and st.button(
            "Save Changes", use_container_width=True, type="primary"
        ):
            updated_records = cast(List[Dict[str, Any]], edited_df.to_dict("records"))
            if db.update_errors(user_id, updated_records):
                st.success("Changes saved successfully!")
                st.rerun()
    else:
        st.info("No records match your filters.")


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
    ui.render_menu_button("Log a Mistake", "Log Error", ICON_LOG_ERROR)
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
        st.rerun()

raw_menu = st.query_params.get("menu", "Dashboard")
menu = raw_menu[0] if isinstance(raw_menu, list) else raw_menu
st.session_state["current_menu"] = menu

# Route to page
if menu == "Dashboard":
    render_dashboard()
elif menu == "Log Error":
    render_log_error()
elif menu == "History":
    render_history()
