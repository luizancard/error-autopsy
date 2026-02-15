"""
Exam Telemetry Dashboard UI Components.

Provides comprehensive performance analytics including:
- Speed vs Accuracy analysis
- Mock exam trajectory
- Session performance metrics
- Activity heatmaps
"""

from typing import Any, Dict, List

import streamlit as st
from config import Colors, TimeFilter
from src.analysis import metrics as mt
from src.analysis import plots as pt


def render_telemetry_dashboard(
    errors: List[Dict[str, Any]],
    sessions: List[Dict[str, Any]],
    mock_exams: List[Dict[str, Any]],
    time_filter: str,
) -> None:
    """
    Render the complete exam telemetry dashboard.

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
    filtered_exams = mt.filter_data_by_range(mock_exams, months)

    # Header with filter
    col1, col2 = st.columns([3, 1])

    with col1:
        st.title("📊 Performance Dashboard")

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

    # ==========================================================================
    # KPI METRICS ROW
    # ==========================================================================

    _render_kpi_metrics(filtered_sessions, filtered_exams, filtered_errors)

    st.divider()

    # ==========================================================================
    # SESSION PERFORMANCE ANALYSIS
    # ==========================================================================

    if sessions:
        st.markdown("## 🎯 Session Performance")

        # Speed vs Accuracy Scatter Plot
        scatter_data = mt.get_speed_accuracy_data(filtered_sessions)
        if scatter_data:
            chart = pt.chart_speed_vs_accuracy(scatter_data)
            if chart:
                st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Log study sessions to see speed vs accuracy analysis.")

        st.markdown("---")

        # Session summary by subject
        if filtered_sessions:
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("### Volume & Accuracy by Subject")
                summary_chart = pt.chart_session_summary(filtered_sessions)
                if summary_chart:
                    st.altair_chart(summary_chart, use_container_width=True)

            with col2:
                st.markdown("### Session Statistics")
                stats = mt.calculate_session_statistics(filtered_sessions)
                _render_session_stats_card(stats)

    else:
        st.info(
            "👆 **Get Started:** Log your first study session using the '📚 Log Session' page!"
        )

    st.divider()

    # ==========================================================================
    # MOCK EXAM TRAJECTORY
    # ==========================================================================

    if mock_exams:
        st.markdown("## 📈 Mock Exam Progress")

        trajectory = mt.get_mock_exam_trajectory(filtered_exams)
        if trajectory:
            chart = pt.chart_mock_exam_trajectory(trajectory)
            if chart:
                st.altair_chart(chart, use_container_width=True)

            # Exam statistics
            exam_stats = mt.calculate_mock_exam_statistics(filtered_exams)
            _render_exam_stats(exam_stats)
        else:
            st.info("No mock exams in selected time period.")

        st.markdown("---")

    # ==========================================================================
    # ERROR ANALYSIS (Legacy)
    # ==========================================================================

    if filtered_errors:
        st.markdown("## ⚠️ Error Analysis")

        col1, col2 = st.columns(2)

        with col1:
            st.markdown("### By Error Type")
            type_counts = mt.count_error_types(filtered_errors)
            chart = pt.chart_error_types_pie(type_counts)
            if chart:
                st.altair_chart(chart, use_container_width=True)

        with col2:
            st.markdown("### By Difficulty")
            diff_counts = mt.count_difficulties(filtered_errors)
            chart = pt.chart_difficulties(diff_counts)
            if chart:
                st.altair_chart(chart, use_container_width=True)

        st.markdown("---")

    # ==========================================================================
    # ACTIVITY HEATMAP
    # ==========================================================================

    st.markdown("## 📅 Study Activity")
    heatmap_data = mt.get_activity_heatmap_data(
        sessions=sessions, errors=errors, mock_exams=mock_exams, days=180
    )

    if heatmap_data and any(d["intensity"] > 0 for d in heatmap_data):
        chart = pt.chart_activity_heatmap(heatmap_data)
        if chart:
            st.altair_chart(chart, use_container_width=True)

        # Activity summary
        total_questions = sum(d["questions_answered"] for d in heatmap_data)
        total_time = sum(d["study_time"] for d in heatmap_data)
        active_days = sum(1 for d in heatmap_data if d["intensity"] > 0)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Questions (6mo)", f"{total_questions:,}")
        with col2:
            st.metric("Study Time (hours)", f"{total_time / 60:.1f}")
        with col3:
            st.metric("Active Days", active_days)
    else:
        st.info("Start logging sessions to see your activity heatmap!")


def _render_kpi_metrics(
    sessions: List[Dict[str, Any]],
    exams: List[Dict[str, Any]],
    errors: List[Dict[str, Any]],
) -> None:
    """Render the top-level KPI metrics."""
    col1, col2, col3, col4 = st.columns(4)

    # Calculate metrics
    session_stats = mt.calculate_session_statistics(sessions) if sessions else None
    exam_stats = mt.calculate_mock_exam_statistics(exams) if exams else None

    with col1:
        total_sessions = len(sessions)
        st.metric(
            "Study Sessions",
            total_sessions,
            delta=f"{session_stats['total_questions']} questions"
            if session_stats
            else None,
        )

    with col2:
        if session_stats and session_stats["avg_accuracy"] > 0:
            st.metric(
                "Avg Accuracy",
                f"{session_stats['avg_accuracy']:.1f}%",
                delta="Good" if session_stats["avg_accuracy"] >= 70 else "Improve",
                delta_color="normal"
                if session_stats["avg_accuracy"] >= 70
                else "inverse",
            )
        else:
            st.metric("Avg Accuracy", "—")

    with col3:
        if exam_stats and exam_stats["total_exams"] > 0:
            st.metric(
                "Latest Mock Exam",
                f"{exam_stats['latest_score']:.1f}%",
                delta=exam_stats["trend"],
            )
        else:
            st.metric("Mock Exams", "0")

    with col4:
        total_errors = len(errors)
        st.metric(
            "Errors Logged",
            total_errors,
            delta=f"{session_stats['best_subject']}"
            if session_stats and session_stats["best_subject"] != "—"
            else None,
        )


def _render_session_stats_card(stats: Dict[str, Any]) -> None:
    """Render session statistics in a formatted card."""
    st.markdown(
        f"""
    <div style="
        background: {Colors.BG_LIGHT};
        padding: 1.5rem;
        border-radius: 8px;
        border-left: 4px solid {Colors.PRIMARY};
    ">
        <div style="margin-bottom: 1rem;">
            <div style="color: {Colors.TEXT_MUTED}; font-size: 0.9rem;">Total Sessions</div>
            <div style="font-size: 2rem; font-weight: bold; color: {Colors.PRIMARY};">
                {stats["total_sessions"]}
            </div>
        </div>

        <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
            <div>
                <div style="color: {Colors.TEXT_MUTED}; font-size: 0.85rem;">Questions Answered</div>
                <div style="font-size: 1.5rem; font-weight: 600;">
                    {stats["total_questions"]:,}
                </div>
            </div>
            <div>
                <div style="color: {Colors.TEXT_MUTED}; font-size: 0.85rem;">Study Time</div>
                <div style="font-size: 1.5rem; font-weight: 600;">
                    {stats["total_study_time"]:.1f}h
                </div>
            </div>
            <div>
                <div style="color: {Colors.TEXT_MUTED}; font-size: 0.85rem;">Avg Pace</div>
                <div style="font-size: 1.5rem; font-weight: 600;">
                    {stats["avg_pace"]:.2f} min/q
                </div>
            </div>
            <div>
                <div style="color: {Colors.TEXT_MUTED}; font-size: 0.85rem;">Best Subject</div>
                <div style="font-size: 1.5rem; font-weight: 600;">
                    {stats["best_subject"]}
                </div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )


def _render_exam_stats(stats: Dict[str, Any]) -> None:
    """Render mock exam statistics."""
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric("Total Exams", stats["total_exams"])

    with col2:
        st.metric("Average Score", f"{stats['avg_score']:.1f}%")

    with col3:
        st.metric("Best Score", f"{stats['best_score']:.1f}%")

    with col4:
        trend = stats["trend"]
        trend_icon = (
            "↗" if "Improving" in trend else "↘" if "Declining" in trend else "→"
        )
        st.metric("Trend", trend_icon, delta=trend.replace(trend_icon, "").strip())
