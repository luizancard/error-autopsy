"""
Error Analysis Dashboard UI Components.

Provides the main dashboard with:
- KPI stat cards (avoidable mistakes, avg accuracy, total errors, top subject)
- Subject distribution chart with topic drill-down
- Monthly error timeline
- Difficulty analysis chart
All charts respect the time filter.
"""

from typing import Any, Dict, List

import streamlit as st
from config import AVOIDABLE_ERROR_TYPES, Colors, TimeFilter
from config.icons import ICON_BOOK
from src.analysis import metrics as mt
from src.analysis import plots as pt
from src.interface.streamlit import components as ui


def render_telemetry_dashboard(
    errors: List[Dict[str, Any]],
    sessions: List[Dict[str, Any]],
    mock_exams: List[Dict[str, Any]],
    time_filter: str,
) -> None:
    """
    Render the main dashboard.

    Args:
        errors: List of error records
        sessions: List of study session records
        mock_exams: List of mock exam records
        time_filter: Selected time filter
    """
    # Apply time filtering
    months = TimeFilter.MONTHS_MAP.get(time_filter)
    filtered_errors = mt.filter_data_by_range(errors, months)
    filtered_sessions = mt.filter_data_by_range(sessions, months)

    # Header with filter
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("Performance Dashboard")

    with col2:
        selected_filter = st.selectbox(
            "Time Period",
            options=TimeFilter.OPTIONS,
            index=TimeFilter.OPTIONS.index(time_filter),
            key="time_filter_select",
            label_visibility="collapsed",
        )

    # Update session state if filter changed
    if selected_filter != time_filter:
        st.session_state["time_filter"] = selected_filter
        st.rerun()

    st.divider()

    # ======================================================================
    # STAT CARDS ROW
    # ======================================================================

    _render_stat_cards(filtered_errors, filtered_sessions)

    st.divider()

    # ======================================================================
    # CHARTS SECTION
    # ======================================================================

    if not filtered_errors:
        st.info(
            f"No errors logged for '{selected_filter}'. "
            "Start logging errors to see your analysis here."
        )
        return

    # --- Subject Distribution (with drill-down to topics) ---
    _render_subject_section(filtered_errors, selected_filter)

    st.markdown("---")

    # --- Monthly Timeline + Difficulty side by side ---
    col_timeline, col_difficulty = st.columns(2)

    with col_timeline:
        st.markdown(
            "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
            'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Errors Over Time</h3>'
            '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
            "Monthly error count</p>",
            unsafe_allow_html=True,
        )
        month_data = mt.aggregate_by_month_all(filtered_errors)
        chart = pt.chart_timeline(month_data)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Not enough data for a timeline yet.")

    with col_difficulty:
        st.markdown(
            "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
            'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Difficulty Analysis</h3>'
            '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
            "Errors by exercise difficulty</p>",
            unsafe_allow_html=True,
        )
        difficulty_data = mt.count_difficulties(filtered_errors)
        chart = pt.chart_difficulties(difficulty_data)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No difficulty data yet.")

    st.markdown("---")

    # --- Error Types Pie Chart + Daily Questions Trend ---
    col_errors, col_questions = st.columns(2)

    with col_errors:
        st.markdown(
            "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
            'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Error Types Distribution</h3>'
            '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
            "Common mistakes by category</p>",
            unsafe_allow_html=True,
        )
        error_type_data = mt.count_error_types(filtered_errors)
        chart = pt.chart_error_types_pie(error_type_data)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No error type data yet.")

    with col_questions:
        st.markdown(
            "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
            'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Daily Study Trend</h3>'
            '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
            "Questions answered per day</p>",
            unsafe_allow_html=True,
        )
        chart = pt.chart_daily_questions(filtered_sessions)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No study session data yet.")


# =========================================================================
# PRIVATE HELPERS
# =========================================================================


def _render_stat_cards(
    filtered_errors: List[Dict[str, Any]],
    filtered_sessions: List[Dict[str, Any]],
) -> None:
    """Render the 4 KPI stat cards at the top of the dashboard."""
    total = len(filtered_errors)

    # Avoidable count
    type_counts: Dict[str, int] = {}
    for r in filtered_errors:
        t = r.get("type", "Other") or "Other"
        type_counts[t] = type_counts.get(t, 0) + 1
    avoidable_count = sum(type_counts.get(et, 0) for et in AVOIDABLE_ERROR_TYPES)
    avoidable_pct = (avoidable_count / total * 100) if total > 0 else 0.0

    # Average accuracy from study sessions
    accuracies = [
        s.get("accuracy_percentage", 0)
        for s in filtered_sessions
        if s.get("accuracy_percentage") is not None
    ]
    avg_accuracy = sum(accuracies) / len(accuracies) if accuracies else 0.0

    # Top subject by error count
    subj_counts: Dict[str, int] = {}
    for r in filtered_errors:
        s = r.get("subject", "Unknown") or "Unknown"
        subj_counts[s] = subj_counts.get(s, 0) + 1
    top_subject = (
        max(subj_counts.items(), key=lambda x: x[1])[0] if subj_counts else "--"
    )

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ui.render_metric_card(
            label="Total Errors",
            value=total,
            icon_char="!",
            icon_bg=Colors.CARD_TOTAL_BG,
            icon_color=Colors.CARD_TOTAL_COLOR,
        )

    with col2:
        ui.render_metric_card(
            label="Avoidable Mistakes",
            value=avoidable_count,
            icon_char="!",
            icon_bg=Colors.CARD_AVOIDABLE_BG,
            icon_color=Colors.CARD_AVOIDABLE_COLOR,
            pill_text=f"{avoidable_pct:.1f}%",
            pill_class="pill-negative",
        )

    with col3:
        ui.render_metric_card(
            label="Avg Accuracy",
            value=f"{avg_accuracy:.1f}%" if accuracies else "--",
            icon_char="!",
            icon_bg=Colors.CARD_ERROR_BG,
            icon_color=Colors.CARD_ERROR_COLOR,
        )

    with col4:
        ui.render_metric_card(
            label="Top Error Subject",
            value=top_subject,
            icon_char=ICON_BOOK,
            icon_bg=Colors.CARD_SUBJECT_BG,
            icon_color=Colors.CARD_SUBJECT_COLOR,
        )


def _render_subject_section(
    filtered_errors: List[Dict[str, Any]], selected_filter: str
) -> None:
    """Render the subject chart, or topic drill-down if a subject is selected."""
    target_subject = st.session_state.get("drill_down_subject")

    if target_subject:
        # TOPIC DRILL-DOWN MODE
        c_back, c_text = st.columns([1.5, 8])
        with c_back:
            if st.button("< Back", key="clear_drill_down", help="Clear Subject Filter"):
                st.session_state.drill_down_subject = None
                st.rerun()
        with c_text:
            ui.render_drill_down_info(target_subject)

        topic_errors = [
            e for e in filtered_errors if e.get("subject") == target_subject
        ]
        topic_data = mt.aggregate_by_topic(topic_errors)

        if not topic_data:
            st.info(f"No topic data for {target_subject} in {selected_filter}.")
            return

        chart = pt.chart_topics(topic_data)
        if chart:
            st.altair_chart(chart, use_container_width=True)

    else:
        # SUBJECT OVERVIEW MODE
        ui.render_chart_header("Analysis by discipline")
        subject_data = mt.aggregate_by_subject(filtered_errors)

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

            if (
                event
                and "selection" in event
                and "selected_subjects" in event["selection"]
            ):
                selection_list = event["selection"]["selected_subjects"]
                if selection_list:
                    selected_subj_name = selection_list[0].get("Subject")
                    if selected_subj_name:
                        st.session_state.drill_down_subject = selected_subj_name
                        st.rerun()
