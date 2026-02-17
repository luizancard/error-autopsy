"""
Error Analysis Dashboard UI Components.

Provides the main dashboard with:
- KPI stat cards (avoidable mistakes, avg accuracy, total errors, top subject)
- Subject distribution chart with topic drill-down
- Monthly error timeline
- Difficulty analysis chart
All charts respect the time filter.
"""

from datetime import date
from typing import Any, Dict, List

import streamlit as st
from config import AVOIDABLE_ERROR_TYPES, EXAM_TYPES, Colors, TimeFilter
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
    Render the main dashboard with AI insights and tabbed interface.

    REFACTORED: Added AI insights and organized with tabs for better UX.

    Args:
        errors: List of error records
        sessions: List of study session records
        mock_exams: List of mock exam records
        time_filter: Selected time filter
    """

    # Header with filters
    col1, col2, col3 = st.columns([3, 1, 1])

    with col1:
        st.title("Performance Dashboard")

    with col2:
        exam_type_filter = st.multiselect(
            "Exam Type",
            options=EXAM_TYPES,
            default=[],
            key="dash_exam_filter",
            label_visibility="collapsed",
            placeholder="Select exams",
        )

    with col3:
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

    # Apply time filtering
    months = TimeFilter.MONTHS_MAP.get(selected_filter)
    filtered_errors = mt.filter_data_by_range(errors, months)
    filtered_sessions = mt.filter_data_by_range(sessions, months)

    # Apply exam type filtering
    if exam_type_filter:
        filtered_errors = [
            e for e in filtered_errors if e.get("exam_type") in exam_type_filter
        ]
        filtered_sessions = [
            s for s in filtered_sessions if s.get("exam_type") in exam_type_filter
        ]

    # ======================================================================
    # AI INSIGHTS - TOP OF DASHBOARD
    # ======================================================================

    _render_ai_insights(filtered_errors)

    st.divider()

    # ======================================================================
    # STAT CARDS ROW
    # ======================================================================

    _render_stat_cards(filtered_errors, filtered_sessions)

    # ======================================================================
    # TABBED INTERFACE
    # ======================================================================

    if not filtered_errors:
        st.info(
            f"No errors logged for '{selected_filter}'. "
            "Start logging errors to see your analysis here."
        )
        return

    tab1, tab2, tab3 = st.tabs(["Overview", "Analytics", "Timeline"])

    # --- TAB 1: OVERVIEW ---
    with tab1:
        st.markdown("### Quick Overview")

        # Activity Heatmap
        st.markdown("#### Activity Heatmap")
        st.caption("Daily error logging activity (contribution-style)")
        heatmap_data = mt.get_activity_heatmap_data(
            filtered_sessions, filtered_errors, mock_exams, days=90
        )
        heatmap_chart = pt.chart_activity_heatmap(heatmap_data)
        if heatmap_chart:
            st.altair_chart(heatmap_chart, use_container_width=True)
        else:
            st.info("Not enough data for heatmap yet.")

        st.divider()

        # Weakest Subjects
        st.markdown("#### Weakest Subjects")
        st.caption("Subjects with the most errors")
        subject_data = mt.aggregate_by_subject(filtered_errors)
        if subject_data:
            # Sort by count descending and take top 5
            sorted_subjects = sorted(
                subject_data.items(), key=lambda x: x[1], reverse=True
            )[:5]

            # Get max count for scaling the bars
            max_count = sorted_subjects[0][1] if sorted_subjects else 1

            for subject, count in sorted_subjects:
                col1, col2, col3 = st.columns([3, 2, 1])
                with col1:
                    st.markdown(f"**{subject}**")
                with col2:
                    # Visual progress bar with purple colors
                    percentage = (count / max_count) * 100
                    st.markdown(
                        f'<div style="background-color: #F7ECE1; border-radius: 10px; height: 20px; overflow: hidden;">'
                        f'<div style="background: linear-gradient(90deg, #725AC1, #8D86C9); width: {percentage}%; height: 100%; border-radius: 10px;"></div>'
                        f"</div>",
                        unsafe_allow_html=True,
                    )
                with col3:
                    st.markdown(
                        f'<span style="color: #725AC1; font-weight: bold;">{count}</span>',
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No subject data yet.")

    # --- TAB 2: ANALYTICS ---
    with tab2:
        st.markdown("### Detailed Analytics")

        # Subject Distribution (with drill-down)
        _render_subject_section(filtered_errors, selected_filter)

        st.divider()

        # Error Types Pie + Difficulty Bar (side by side)
        col_types, col_diff = st.columns(2)

        with col_types:
            st.markdown("#### Error Types Distribution")
            st.caption("Common mistakes by category")
            error_type_data = mt.count_error_types(filtered_errors)
            chart = pt.chart_error_types_pie(error_type_data)
            if chart:
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No error type data yet.")

        with col_diff:
            st.markdown("#### Difficulty Analysis")
            st.caption("Errors by exercise difficulty")
            difficulty_data = mt.count_difficulties(filtered_errors)
            chart = pt.chart_difficulties(difficulty_data)
            if chart:
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No difficulty data yet.")

        st.divider()

        # Speed vs Accuracy Scatter
        st.markdown("#### Speed vs Accuracy")
        st.caption("Session performance correlation")
        if filtered_sessions:
            # Create scatter plot data
            scatter_data = []
            for session in filtered_sessions:
                if session.get("pace_per_question") and session.get(
                    "accuracy_percentage"
                ):
                    scatter_data.append(
                        {
                            "Pace (min/q)": session["pace_per_question"],
                            "Accuracy (%)": session["accuracy_percentage"],
                            "Subject": session.get("subject", "Unknown"),
                        }
                    )

            if scatter_data:
                import altair as alt

                scatter_chart = (
                    alt.Chart(alt.Data(values=scatter_data))
                    .mark_circle(size=100, opacity=0.7)
                    .encode(
                        x=alt.X("Pace (min/q):Q", scale=alt.Scale(zero=False)),
                        y=alt.Y("Accuracy (%):Q", scale=alt.Scale(domain=[0, 100])),
                        color=alt.Color(
                            "Subject:N", legend=alt.Legend(title="Subject")
                        ),
                        tooltip=["Subject:N", "Pace (min/q):Q", "Accuracy (%):Q"],
                    )
                    .properties(height=300)
                )
                st.altair_chart(scatter_chart, use_container_width=True)
            else:
                st.info("Not enough session data for speed vs accuracy analysis.")
        else:
            st.info("No study session data yet.")

        st.divider()

        # Exam Type + Pace by Subject (side by side)
        col_exam, col_pace = st.columns(2)

        with col_exam:
            st.markdown("#### Errors by Exam Type")
            st.caption("Distribution across exam types")
            exam_type_data = mt.count_by_field(filtered_errors, "exam_type")
            chart = pt.chart_exam_type_distribution(exam_type_data)
            if chart:
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No exam type data yet.")

        with col_pace:
            st.markdown("#### Pace per Question")
            st.caption("Average minutes per question by subject")
            pace_data = mt.get_pace_by_subject(filtered_sessions)
            chart = pt.chart_pace_by_subject(pace_data)
            if chart:
                st.altair_chart(chart, use_container_width=True)
            else:
                st.info("No study session data yet.")

    # --- TAB 3: TIMELINE ---
    with tab3:
        st.markdown("### Timeline Analysis")

        # Monthly Error Timeline
        st.markdown("#### Errors Over Time")
        st.caption("Monthly error count")
        month_data = mt.aggregate_by_month_all(filtered_errors)
        chart = pt.chart_timeline(month_data)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Not enough data for a timeline yet.")

        st.divider()

        # Mock Exam Score Trajectory
        st.markdown("#### Mock Exam Performance Trajectory")
        st.caption("Score evolution over time")
        if mock_exams:
            # Sort by date
            sorted_exams = sorted(
                mock_exams, key=lambda x: x.get("date_obj", date.today())
            )

            trajectory_data = []
            for exam in sorted_exams:
                trajectory_data.append(
                    {
                        "Date": exam.get("date", ""),
                        "Score %": exam.get("score_percentage", 0),
                        "Exam": exam.get("exam_name", "Unknown"),
                    }
                )

            if trajectory_data:
                import altair as alt

                trajectory_chart = (
                    alt.Chart(alt.Data(values=trajectory_data))
                    .mark_line(point=True, strokeWidth=3)
                    .encode(
                        x=alt.X("Date:N", axis=alt.Axis(labelAngle=-45)),
                        y=alt.Y("Score %:Q", scale=alt.Scale(domain=[0, 100])),
                        tooltip=["Exam:N", "Date:N", "Score %:Q"],
                    )
                    .properties(height=350)
                )
                st.altair_chart(trajectory_chart, use_container_width=True)
            else:
                st.info("No mock exam data yet.")
        else:
            st.info("No mock exams logged yet.")

        st.divider()

        # Daily Study Trend
        st.markdown("#### Daily Study Activity")
        st.caption("Questions answered per day")
        chart = pt.chart_daily_questions(filtered_sessions)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No study session data yet.")


# =========================================================================
# PRIVATE HELPERS
# =========================================================================


def _render_ai_insights(filtered_errors: List[Dict[str, Any]]) -> None:
    """
    Render AI-powered insights at the top of the dashboard.

    Shows actionable alerts based on error patterns:
    - Fatigue warning if >25% of recent errors are fatigue-related
    - Focus alert if a specific topic appears >3 times recently
    """
    if not filtered_errors:
        return

    # Get recent errors (last 30 days or last 20 errors, whichever is smaller)
    recent_errors = filtered_errors[: min(20, len(filtered_errors))]

    insights = []

    # Check for fatigue pattern
    fatigue_count = sum(1 for e in recent_errors if e.get("type") == "Fatigue")
    fatigue_percentage = (
        (fatigue_count / len(recent_errors) * 100) if recent_errors else 0
    )

    if fatigue_percentage > 25:
        insights.append(
            {
                "type": "warning",
                "icon": "",
                "title": "Fatigue Alert",
                "message": f"{fatigue_percentage:.0f}% of recent errors are fatigue-related. Consider taking breaks or shorter study sessions.",
            }
        )

    # Check for recurring topic
    topic_counts = {}
    for error in recent_errors:
        topic = error.get("topic", "")
        if topic:
            topic_counts[topic] = topic_counts.get(topic, 0) + 1

    if topic_counts:
        most_common_topic = max(topic_counts.items(), key=lambda x: x[1])
        if most_common_topic[1] > 3:
            insights.append(
                {
                    "type": "info",
                    "icon": "",
                    "title": "Focus Area Detected",
                    "message": f"Topic '{most_common_topic[0]}' appears {most_common_topic[1]} times in recent errors. Consider focused review.",
                }
            )

    # Render insights if any
    if insights:
        st.markdown("### AI Insights")
        st.caption("Actionable recommendations based on your error patterns")

        for insight in insights:
            if insight["type"] == "warning":
                st.warning(f"**{insight['title']}**: {insight['message']}")
            elif insight["type"] == "info":
                st.info(f"**{insight['title']}**: {insight['message']}")


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
            st.altair_chart(chart, width="stretch")

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
                width="stretch",
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
