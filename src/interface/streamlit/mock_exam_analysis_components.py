"""
Mock Exam Analysis page components.

Provides a dedicated analysis dashboard for mock exams including:
- KPI cards (total exams, best score, latest score, trend)
- Score trajectory chart
- Section comparison (ENEM/SAT)
- Section progress over time
- Error breakdown per exam
- Exam history
"""

from typing import Any, Dict, List

import streamlit as st
from config import EXAM_SECTION_DEFS, Colors
from src.analysis import metrics as mt
from src.analysis import plots as pt
from src.interface.streamlit import components as ui


def render_mock_exam_analysis(
    mock_exams: List[Dict[str, Any]],
    errors: List[Dict[str, Any]],
) -> None:
    """
    Render the Mock Exam Analysis page.

    Args:
        mock_exams: All mock exam records for the user
        errors: All error records for the user
    """
    st.title("Mock Exam Analysis")

    if not mock_exams:
        st.info(
            "No mock exams logged yet. "
            "Go to Log Session > Mock Exam to record your first simulado."
        )
        return

    # Exam type filter - only show types that have data
    exam_types_with_data = sorted(
        set(e.get("exam_type", "General") for e in mock_exams)
    )

    selected_type = st.selectbox(
        "Exam Type",
        options=["All"] + exam_types_with_data,
        key="mock_analysis_type",
        label_visibility="collapsed",
    )

    # Filter exams
    if selected_type == "All":
        filtered_exams = mock_exams
    else:
        filtered_exams = [e for e in mock_exams if e.get("exam_type") == selected_type]

    if not filtered_exams:
        st.info(f"No exams found for {selected_type}.")
        return

    st.divider()

    # KPI cards
    _render_kpi_cards(filtered_exams)

    st.divider()

    # Score trajectory
    _render_trajectory(filtered_exams)

    # Section analysis (only for ENEM/SAT)
    has_sections = selected_type in EXAM_SECTION_DEFS
    if has_sections:
        st.markdown("---")
        _render_section_analysis(filtered_exams, selected_type)

    # Error breakdown per exam
    st.markdown("---")
    _render_error_breakdown(filtered_exams, errors)

    # Exam history
    st.markdown("---")
    _render_exam_history(filtered_exams)


def _render_kpi_cards(exams: List[Dict[str, Any]]) -> None:
    """Render KPI stat cards for mock exams."""
    stats = mt.calculate_mock_exam_statistics(exams)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        ui.render_metric_card(
            label="Total Exams",
            value=stats["total_exams"],
            icon_char="!",
            icon_bg=Colors.CARD_TOTAL_BG,
            icon_color=Colors.CARD_TOTAL_COLOR,
        )

    with col2:
        ui.render_metric_card(
            label="Best Score",
            value=f"{stats['best_score']:.1f}%",
            icon_char="!",
            icon_bg="#e7f5ef",
            icon_color="#0f766e",
        )

    with col3:
        ui.render_metric_card(
            label="Latest Score",
            value=f"{stats['latest_score']:.1f}%",
            icon_char="!",
            icon_bg=Colors.CARD_ERROR_BG,
            icon_color=Colors.CARD_ERROR_COLOR,
        )

    with col4:
        trend = stats["trend"]
        pill_class = ""
        if trend == "Improving":
            pill_class = "pill-positive"
        elif trend == "Declining":
            pill_class = "pill-negative"

        ui.render_metric_card(
            label="Trend",
            value=trend,
            icon_char="!",
            icon_bg=Colors.CARD_AVOIDABLE_BG,
            icon_color=Colors.CARD_AVOIDABLE_COLOR,
            pill_text=f"Avg: {stats['avg_score']:.0f}%",
            pill_class=pill_class,
        )


def _render_trajectory(exams: List[Dict[str, Any]]) -> None:
    """Render the score trajectory chart."""
    st.markdown(
        "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
        'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Score Trajectory</h3>'
        '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
        "Score evolution over time</p>",
        unsafe_allow_html=True,
    )

    trajectory = mt.get_mock_exam_trajectory(exams)
    chart = pt.chart_mock_exam_trajectory(trajectory)

    if chart:
        st.altair_chart(chart, use_container_width=True)
    else:
        st.info("Not enough data for a trajectory chart yet.")


def _render_section_analysis(exams: List[Dict[str, Any]], exam_type: str) -> None:
    """Render section comparison and trend charts for structured exams."""
    st.markdown(
        "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
        'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Section Analysis</h3>'
        '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
        "Performance breakdown by exam section</p>",
        unsafe_allow_html=True,
    )

    col_comp, col_trend = st.columns(2)

    with col_comp:
        section_data = mt.extract_section_scores(exams, exam_type)
        chart = pt.chart_section_comparison(section_data)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("No section data available.")

    with col_trend:
        trend_data = mt.get_section_trend_data(exams, exam_type)
        chart = pt.chart_section_trends(trend_data)
        if chart:
            st.altair_chart(chart, use_container_width=True)
        else:
            st.info("Need multiple exams to show trends.")


def _render_error_breakdown(
    exams: List[Dict[str, Any]], errors: List[Dict[str, Any]]
) -> None:
    """Render errors linked to each mock exam."""
    st.markdown(
        "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
        'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Error Breakdown</h3>'
        '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
        "Errors logged per mock exam</p>",
        unsafe_allow_html=True,
    )

    # Check if any exam has linked errors
    exam_ids = {e.get("id") for e in exams if e.get("id")}
    linked_errors = [e for e in errors if e.get("mock_exam_id") in exam_ids]

    if not linked_errors:
        st.info("No errors have been linked to these mock exams yet.")
        return

    for exam in exams:
        exam_id = exam.get("id")
        if not exam_id:
            continue

        exam_date = exam.get("date")  # DD-MM-YYYY format from load_mock_exams()
        error_summary = mt.get_mock_exam_error_summary(errors, exam_id, exam_date)
        if not error_summary:
            continue

        total_linked = sum(len(v) for v in error_summary.values())
        exam_label = f"{exam.get('exam_name', 'Untitled')} ({exam.get('date', '')}) - {total_linked} error(s)"

        with st.expander(exam_label, expanded=False):
            for subject, subject_errors in error_summary.items():
                st.markdown(f"**{subject}** ({len(subject_errors)} errors)")
                for err in subject_errors:
                    topic = err.get("topic", "")
                    etype = err.get("type", "")
                    desc = err.get("description", "")
                    line = f"- {topic} [{etype}]"
                    if desc:
                        line += f" - {desc}"
                    st.markdown(line)


def _render_exam_history(exams: List[Dict[str, Any]]) -> None:
    """Render expandable exam history list with edit/delete capabilities."""
    st.markdown(
        "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
        'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Exam History</h3>'
        '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
        "All logged mock exams (click to view details, edit, or delete)</p>",
        unsafe_allow_html=True,
    )

    for exam in exams:
        name = exam.get("exam_name", "Untitled")
        date_str = exam.get("date", "")
        pct = exam.get("score_percentage", 0)
        exam_type = exam.get("exam_type", "General")
        exam_id = exam.get("id", "")

        label = f"{name} | {date_str} | {pct:.1f}%"

        with st.expander(label, expanded=False):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric(
                    "Score",
                    f"{exam.get('total_score', 0):.0f}/{exam.get('max_possible_score', 0):.0f}",
                )
            with col2:
                st.metric("Percentage", f"{pct:.1f}%")
            with col3:
                st.metric("Type", exam_type)

            # Show section breakdown if available
            breakdown = exam.get("breakdown_json") or {}
            if isinstance(breakdown, dict):
                section_items = {
                    k: v
                    for k, v in breakdown.items()
                    if isinstance(v, dict) and "label" in v
                }
                if section_items:
                    st.markdown("**Section Breakdown:**")
                    for key, sec in section_items.items():
                        score = sec.get("score", 0)
                        mx = sec.get("max", 0)
                        sec_pct = (score / mx * 100) if mx > 0 else 0
                        st.markdown(
                            f"- {sec.get('label', key)}: {score}/{mx} ({sec_pct:.0f}%)"
                        )

                # Show extra scores
                tri = breakdown.get("tri_score")
                if tri:
                    st.markdown(f"- TRI Score: {tri}")
                scaled = breakdown.get("scaled_score")
                if scaled:
                    st.markdown(f"- Scaled Score: {scaled}")

            notes = exam.get("notes")
            if notes:
                st.markdown(f"**Notes:** {notes}")

            # Edit/Delete buttons
            st.divider()
            col_edit, col_delete = st.columns(2)

            with col_edit:
                if st.button(
                    "Edit Exam", key=f"edit_{exam_id}", use_container_width=True
                ):
                    st.session_state[f"editing_{exam_id}"] = True
                    st.rerun()

            with col_delete:
                if st.button(
                    "Delete Exam",
                    key=f"delete_{exam_id}",
                    use_container_width=True,
                    type="secondary",
                ):
                    st.session_state[f"confirm_delete_{exam_id}"] = True
                    st.rerun()

            # Show edit form if editing
            if st.session_state.get(f"editing_{exam_id}", False):
                _render_edit_form(exam)

            # Show delete confirmation
            if st.session_state.get(f"confirm_delete_{exam_id}", False):
                st.warning(
                    "Are you sure you want to delete this exam? This action cannot be undone."
                )
                col_yes, col_no = st.columns(2)

                with col_yes:
                    if st.button(
                        "Yes, Delete",
                        key=f"confirm_yes_{exam_id}",
                        use_container_width=True,
                        type="primary",
                    ):
                        from src.services import db_service as db

                        user_id = st.session_state.get("user_id", "")
                        if db.delete_mock_exam(exam_id, user_id):
                            st.success("Exam deleted successfully!")
                            st.session_state.pop(f"confirm_delete_{exam_id}", None)
                            st.rerun()
                        else:
                            st.error("Failed to delete exam. Please try again.")

                with col_no:
                    if st.button(
                        "Cancel", key=f"confirm_no_{exam_id}", use_container_width=True
                    ):
                        st.session_state.pop(f"confirm_delete_{exam_id}", None)
                        st.rerun()


def _render_edit_form(exam: Dict[str, Any]) -> None:
    """Render inline edit form for a mock exam."""
    exam_id = exam.get("id", "")

    st.markdown("**Edit Exam Details:**")

    with st.form(f"edit_form_{exam_id}"):
        new_name = st.text_input("Exam Name", value=exam.get("exam_name", ""))
        new_notes = st.text_area("Notes", value=exam.get("notes", ""))

        col_submit, col_cancel = st.columns(2)

        with col_submit:
            if st.form_submit_button(
                "Save Changes", use_container_width=True, type="primary"
            ):
                from src.services import db_service as db

                user_id = st.session_state.get("user_id", "")

                updates = {
                    "exam_name": new_name,
                    "notes": new_notes,
                }

                if db.update_mock_exam(
                    exam_id=exam_id,
                    user_id=user_id,
                    updates=updates,
                ):
                    st.success("Changes saved successfully!")
                    st.session_state.pop(f"editing_{exam_id}", None)
                    st.rerun()
                else:
                    st.error("Failed to save changes. Please try again.")

        with col_cancel:
            if st.form_submit_button("Cancel", use_container_width=True):
                st.session_state.pop(f"editing_{exam_id}", None)
                st.rerun()
