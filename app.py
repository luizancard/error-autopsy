import importlib
import time
from datetime import date

import streamlit as st

from assets import styles
from src.analysis import metrics as mt
from src.analysis import plots as pt
from src.interface.streamlit import components as ui
from src.services import db_service as db

importlib.reload(mt)

errors = db.load_data()
DEFAULT_ERROR_TYPE = "Content Gap"

st.session_state.setdefault("subject_input", "")
st.session_state.setdefault("topic_input", "")
st.session_state.setdefault("description_input", "")
st.session_state.setdefault("error_type_select", DEFAULT_ERROR_TYPE)
st.session_state.setdefault("error_type_select", DEFAULT_ERROR_TYPE)
st.session_state.setdefault("date_input", date.today())
st.session_state.setdefault("time_filter", "All Time")  # Default filter
st.session_state.setdefault("reset_form", False)
st.session_state.setdefault("success_message", "")
st.session_state.setdefault("show_success", False)

raw_menu = st.query_params.get("menu", "Dashboard")
menu_from_url = raw_menu[0] if isinstance(raw_menu, list) else raw_menu
st.session_state["current_menu"] = menu_from_url

st.set_page_config(page_title="Error Autopsy", layout="wide", page_icon="📝")

styles.local_css()


with st.sidebar:
    ui.render_sidebar_header()
    st.markdown('<div class="sidebar-menu">', unsafe_allow_html=True)

    # Dashboard
    ui.render_menu_button(
        "Dashboard",
        "Dashboard",
        """<svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M3 5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5z"></path>
            <path d="M13 5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V5z"></path>
            <path d="M3 15a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4z"></path>
            <path d="M13 15a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-4z"></path>
            </svg>""",
    )

    # Log error
    ui.render_menu_button(
        "Log Mistake",
        "Log Error",
        """<svg viewBox="0 0 24 24" fill="currentColor">
            <circle cx="12" cy="12" r="10"></circle>
            <path d="M12 7v10M7 12h10" stroke="white" stroke-width="1.5" stroke-linecap="round"></path>
            </svg>""",
    )

    # History
    ui.render_menu_button(
        "History",
        "History",
        """<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
            <circle cx="12" cy="12" r="9"></circle>
            <path d="M12 6v6l4 2"></path>
            </svg>""",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # gets the current menu or defines the standard
    menu = st.session_state.get("current_menu", "Dashboard")

if menu == "Dashboard":
    st.title("Your Progress")

    # Time Filter Widget (Global)
    filter_options = [
        "This Month",
        "Last 2 Months",
        "Last 4 Months",
        "Last 6 Months",
        "All Time",
    ]

    # Place filter at the top, aligned left or with columns
    col_filter_global, _ = st.columns([2, 5])
    with col_filter_global:
        selected_filter = st.selectbox(
            "Time Period",
            options=filter_options,
            index=filter_options.index(st.session_state.get("time_filter", "All Time")),
            key="time_filter_select",
        )
        # Update session state
        st.session_state.time_filter = selected_filter

    # Determine months for filtering
    filter_map = {
        "This Month": 0,
        "Last 2 Months": 2,
        "Last 4 Months": 4,
        "Last 6 Months": 6,
        "All Time": None,
    }
    months_filter = filter_map[selected_filter]

    # Filter the data globally for the dashboard
    dashboard_filtered_errors = mt.filter_data_by_range(errors, months_filter)

    # Calculate metrics on the dashboard_filtered_errors
    total_errors_count = len(dashboard_filtered_errors)

    # Calculate most frequent subject
    subj_counts = {}
    for r in dashboard_filtered_errors:
        s = r.get("subject", "Unknown") or "Unknown"
        subj_counts[s] = subj_counts.get(s, 0) + 1
    top_subj = max(subj_counts.items(), key=lambda x: x[1])[0] if subj_counts else "—"

    # Calculate most frequent type
    type_counts = {}
    for r in dashboard_filtered_errors:
        t = r.get("type", "Other") or "Other"
        type_counts[t] = type_counts.get(t, 0) + 1
    top_tp = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "—"

    # Calculate Avoidable Errors % (Attention Detail + Interpretation)
    avoidable_count = type_counts.get("Attention Detail", 0) + type_counts.get(
        "Interpretation", 0
    )
    if total_errors_count > 0:
        avoidable_pct = (avoidable_count / total_errors_count) * 100
    else:
        avoidable_pct = 0.0

    # Hide delta for now as it makes less sense on variable timeframes
    pill_class = "pill-positive"

    # Render cards side-by-side
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ui.render_metric_card(
            label="Total Errors",
            value=total_errors_count,
            icon_char="!",
            icon_bg="#eef2ff",
            icon_color="#4338ca",
            pill_text=" ",
            pill_class=" ",
        )

    with col2:
        ui.render_metric_card(
            label="Subject with Most Errors",
            value=top_subj,
            icon_char="""<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                    </svg>""",
            icon_bg="#e7f5ef",
            icon_color="#0f766e",
            pill_text=" ",
            pill_class=" ",
        )

    with col3:
        ui.render_metric_card(
            label="Primary Error Reason",
            value=top_tp,
            icon_char="⚡",
            icon_bg="#fff7ed",
            icon_color="#c2410c",
            pill_text=" ",
            pill_class=" ",
        )

    with col4:
        ui.render_metric_card(
            label="Avoidable Errors",
            value=avoidable_count,
            icon_char="⚠️",
            icon_bg="#fefce8",
            icon_color="#cf8215",
            pill_text=f"{avoidable_pct:.1f}%",
            pill_class="pill-negative",
        )

    # Second row: Chart card and AI Insight card
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    chart_errors = dashboard_filtered_errors

    chart_col, insight_col = st.columns([2, 1])

    with chart_col:
        # Initialize chart view state
        if "chart_view" not in st.session_state:
            st.session_state.chart_view = 0

        current_view = st.session_state.chart_view
        subtitles = ["Analysis by discipline", "Analysis by topic", "Timeline overview"]

        # Ensure view index is within bounds
        if current_view >= len(subtitles):
            current_view = 0
            st.session_state.chart_view = 0

        # Header with title and toggle button
        col_title, col_button = st.columns([12, 1])
        with col_title:
            ui.render_chart_header(subtitles[current_view])

        with col_button:
            if st.button("→", key="chart_toggle", help="Toggle view"):
                st.session_state.chart_view = (current_view + 1) % len(subtitles)
                st.rerun()

        # Build data for the selected view
        if current_view == 0:
            subject_data = mt.aggregate_by_subject(chart_errors)

            if subject_data is None:
                st.info(f"No data available for {selected_filter}. Log some errors!")
            else:
                chart = pt.chart_subjects(subject_data)
                if chart:
                    event = st.altair_chart(
                        chart,
                        use_container_width=True,
                        on_select="rerun",
                        key="subject_chart_select",
                    )
                # Handle selection
                if (
                    event
                    and "selection" in event
                    and "selected_subjects" in event["selection"]
                ):
                    selection_list = event["selection"]["selected_subjects"]
                    if selection_list:
                        # Extract the subject name (dictionaries in list)
                        # The click returns a list of dicts, e.g. [{'Subject': 'Math'}]
                        selected_subj_name = selection_list[0].get("Subject")
                        if selected_subj_name:
                            st.session_state.drill_down_subject = selected_subj_name
                            st.session_state.chart_view = 1  # Switch to Topic View
                            st.rerun()

        # Topic Analysis
        elif current_view == 1:
            # Check for drill-down filter
            target_subject = st.session_state.get("drill_down_subject")

            # If drilling down, filter the chart_errors first
            if target_subject:
                c_back, c_text = st.columns([1.5, 8])

                with c_back:
                    if st.button(
                        "← Back", key="clear_drill_down", help="Clear Subject Filter"
                    ):
                        st.session_state.drill_down_subject = None
                        st.session_state.chart_view = 0  # Go back to Subject View
                        st.rerun()

                with c_text:
                    ui.render_drill_down_info(target_subject)

                # Filter data to only this subject
                filtered_topic_errors = [
                    e for e in chart_errors if e.get("subject") == target_subject
                ]
                topic_data = mt.aggregate_by_topic(filtered_topic_errors)
                chart = pt.chart_topics(topic_data)
                if chart:
                    st.altair_chart(chart, use_container_width=True)
            else:
                # Normal behavior
                topic_data = mt.aggregate_by_topic(chart_errors)
                if not topic_data:
                    st.info(
                        f"No data available for {selected_filter}. Log some errors!"
                    )
                else:
                    chart = pt.chart_topics(topic_data)
                    if chart:
                        st.altair_chart(chart, use_container_width=True)

        else:
            month_data = mt.aggregate_by_month_all(chart_errors)
            chart = pt.chart_timeline(month_data)
            if chart:
                st.altair_chart(chart, use_container_width=True)

    with insight_col:
        qp = st.query_params
        if qp.get("refresh_insight") == "true":
            st.session_state.dashboard_insight = ui.generate_web_insight(chart_errors)

        # Check if we already have a cached insight for this session
        if (
            "dashboard_insight" not in st.session_state
            or st.session_state.dashboard_insight is None
            or str(st.session_state.dashboard_insight) == "None"
        ):
            st.session_state.dashboard_insight = ui.generate_web_insight(chart_errors)

        mini_insight = st.session_state.dashboard_insight

        # Fallback for display
        if mini_insight is None or str(mini_insight) == "None":
            mini_insight = "Insight generation failed. Please check log new errors!"

        st.markdown(
            f"""
            <div class="insight-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 class="insight-title" style="color: #eeeeee; margin:0;">Insight</h3>
                </div>
                <div class="insight-content">
                    {mini_insight}
                </div>

                

            </div>
            """,
            unsafe_allow_html=True,
        )

    # Error Breakdown by Type (Pie Chart) with separate filter
    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)

    # Section Header
    st.markdown(
        """
        <h3 style="font-family:'Helvetica Neue', sans-serif;font-size:1.35rem;font-weight:800;color:#0f172a;margin:0 0 0.4rem 0;letter-spacing:0.08em;text-transform:uppercase;">Error Breakdown</h3>
        <p style="font-family:'Helvetica Neue', sans-serif;font-size:0.95rem;color:#94a3b8;font-weight:500;font-style:italic;margin:0 0 1.5rem 0;">Distribution by mistake type</p>
        """,
        unsafe_allow_html=True,
    )

    col_content, col_spacer = st.columns([3, 2])

    # Container for Chart (3/5 layout)
    col_content, col_spacer = st.columns([3, 2])

    with col_content:
        # Use global filtered data
        pie_chart_errors = dashboard_filtered_errors

        # Generate Data
        type_data = mt.count_error_types(pie_chart_errors)

        if type_data is None:
            st.info(f"No data available for {selected_filter}.")
        else:
            df_pie = pt.chart_error_types_pie(type_data)
            if df_pie:
                st.altair_chart(df_pie, use_container_width=True)

elif menu == "Log Error":
    st.title("📝 Log a New Mistake")
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
            "Description (Optional)",
            placeholder="Why do you think this happened?",
            key="description_input",
        )

        submitted = st.button("Log Mistake", use_container_width=True)

        if submitted:
            if subject is None or topic is None:
                st.error("Please fill in both Subject and Topic.")
            else:
                db.log_error(
                    errors,
                    subject,
                    topic,
                    error_type,
                    description,
                    date_input,
                )
                st.session_state.show_success = True
                st.session_state.success_message = (
                    f"Error in {subject} ({topic}) logged!"
                )
                st.session_state.reset_form = True  # Trigger reset on next run
                st.rerun()

    if st.session_state.show_success:
        st.success(st.session_state.success_message)
        time.sleep(2)  # Brief pause so user sees it
        st.session_state.show_success = False
        st.session_state.success_message = ""
        st.rerun()

elif menu == "History":
    st.empty()
