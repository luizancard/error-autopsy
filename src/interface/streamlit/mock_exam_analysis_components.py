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
from config import AVOIDABLE_ERROR_TYPES, EXAM_SECTION_DEFS, Colors
from src.analysis import metrics as mt
from src.analysis import plots as pt
from src.interface.streamlit import components as ui


def _get_linked_errors(exams: list[dict], all_errors: list[dict]) -> list[dict]:
    """Get errors linked to the given mock exams."""
    exam_ids = {e.get("id") for e in exams if e.get("id")}
    return [e for e in all_errors if e.get("mock_exam_id") in exam_ids]


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

    # Score trajectory + TRI/Scaled score side by side (ENEM/SAT)
    if selected_type in ("ENEM", "SAT"):
        scaled_data = mt.get_scaled_score_trajectory(filtered_exams, selected_type)
        if scaled_data:
            col_traj, col_scaled = st.columns(2)
            with col_traj:
                _render_trajectory(filtered_exams)
            with col_scaled:
                if selected_type == "ENEM":
                    chart = pt.chart_scaled_score_trajectory(
                        scaled_data,
                        score_label="TRI Score",
                        target_score=700,
                        max_score=1000,
                    )
                else:
                    chart = pt.chart_scaled_score_trajectory(
                        scaled_data,
                        score_label="Scaled Score",
                        target_score=1200,
                        max_score=1600,
                    )
                if chart:
                    st.altair_chart(chart, width="stretch")
        else:
            _render_trajectory(filtered_exams)
    else:
        _render_trajectory(filtered_exams)

    # Section analysis vs Error analysis
    sections = EXAM_SECTION_DEFS.get(selected_type, {})
    if len(sections) > 1:
        # Multi-section exams (ENEM, SAT) — show section comparison
        st.markdown("---")
        _render_section_analysis(filtered_exams, selected_type)

    # Error analysis (subject/topic/difficulty/type charts)
    linked_errors = _get_linked_errors(filtered_exams, errors)
    if linked_errors:
        st.markdown("---")
        _render_error_analysis(linked_errors, selected_type)

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
        st.altair_chart(chart, width="stretch")
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
            st.altair_chart(chart, width="stretch")
        else:
            st.info("No section data available.")

    with col_trend:
        trend_data = mt.get_section_trend_data(exams, exam_type)
        chart = pt.chart_section_trends(trend_data)
        if chart:
            st.altair_chart(chart, width="stretch")
        else:
            st.info("Need multiple exams to show trends.")


def _render_error_analysis(
    linked_errors: List[Dict[str, Any]], exam_type: str = "All"
) -> None:
    """Render interactive error analysis charts (subject, topic, difficulty, types)."""
    st.markdown(
        "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
        'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Error Analysis</h3>'
        '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
        "Subject and error pattern breakdown across your mock exams</p>",
        unsafe_allow_html=True,
    )

    # --- Row 1: Subject ↔ Topic drill-down ---
    target_subject = st.session_state.get("mock_drill_down_subject")

    if target_subject:
        # TOPIC DRILL-DOWN MODE
        c_back, c_text = st.columns([1.5, 8])
        with c_back:
            if st.button(
                "< Back", key="mock_clear_drill_down", help="Back to subjects"
            ):
                st.session_state.mock_drill_down_subject = None
                st.rerun()
        with c_text:
            ui.render_drill_down_info(target_subject)

        topic_errors = [e for e in linked_errors if e.get("subject") == target_subject]
        topic_data = mt.aggregate_by_topic(topic_errors)

        if topic_data:
            chart = pt.chart_topics(topic_data)
            if chart:
                st.altair_chart(chart, width="stretch")
        else:
            st.info(f"No topic data for {target_subject}.")
    else:
        # SUBJECT OVERVIEW MODE
        subject_data = mt.aggregate_by_subject(linked_errors)

        if subject_data:
            chart = pt.chart_subjects(subject_data)
            if chart:
                event = st.altair_chart(
                    chart,
                    width="stretch",
                    on_select="rerun",
                    key="mock_subject_chart_select",
                )

                if (
                    event
                    and "selection" in event
                    and "selected_subjects" in event["selection"]
                ):
                    selection_list = event["selection"]["selected_subjects"]
                    if selection_list:
                        selected_subj = selection_list[0].get("Subject")
                        if selected_subj:
                            st.session_state.mock_drill_down_subject = selected_subj
                            st.rerun()
        else:
            st.info("No subject data available.")

    # --- Row 2: Per-section topic breakdown ---
    from config import get_subjects_for_section

    sections = EXAM_SECTION_DEFS.get(exam_type, {})

    # Build section_label → list of subjects to filter by
    section_topic_groups: dict[str, list[str]] = {}
    for sec_key, sec in sections.items():
        if sec.get("is_essay"):
            continue
        label = sec.get("label", sec_key)
        subjects_for_sec = get_subjects_for_section(exam_type, sec_key)
        section_topic_groups[label] = subjects_for_sec

    if len(section_topic_groups) > 1:
        section_cols = st.columns(len(section_topic_groups))
        for idx, (group_label, subjects_list) in enumerate(
            section_topic_groups.items()
        ):
            with section_cols[idx]:
                st.markdown(
                    f"<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
                    f'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">{group_label} Topics</h3>'
                    f'<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
                    f"Most common error topics in {group_label}</p>",
                    unsafe_allow_html=True,
                )
                subj_errors = [
                    e for e in linked_errors if e.get("subject") in subjects_list
                ]
                topic_data = mt.aggregate_by_topic(subj_errors)
                if topic_data:
                    chart = pt.chart_topics(topic_data)
                    if chart:
                        st.altair_chart(chart, width="stretch")
                else:
                    st.info(f"No topic data for {group_label} yet.")

    # --- Row 3: Difficulty + Error Types side by side ---
    col_diff, col_types = st.columns(2)

    with col_diff:
        st.markdown(
            "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
            'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Difficulty Analysis</h3>'
            '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
            "Errors by exercise difficulty</p>",
            unsafe_allow_html=True,
        )
        difficulty_data = mt.count_difficulties(linked_errors)
        chart = pt.chart_difficulties(difficulty_data)
        if chart:
            st.altair_chart(chart, width="stretch")
        else:
            st.info("No difficulty data yet.")

    with col_types:
        st.markdown(
            "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
            'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Error Types</h3>'
            '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
            "Common mistakes by category</p>",
            unsafe_allow_html=True,
        )
        error_type_data = mt.count_error_types(linked_errors)
        chart = pt.chart_error_types_pie(error_type_data)
        if chart:
            st.altair_chart(chart, width="stretch")
        else:
            st.info("No error type data yet.")

    # --- Row 4: Weakest Subjects + Avoidable Errors ---
    _render_weakest_subjects(linked_errors)
    _render_avoidable_errors(linked_errors)


def _render_weakest_subjects(errors: List[Dict[str, Any]]) -> None:
    """Show top 3 weakest subjects with their most common error type."""
    subject_data = mt.aggregate_by_subject(errors)
    if not subject_data:
        return

    # Sort by error count descending
    sorted_subjects = sorted(subject_data.items(), key=lambda x: x[1], reverse=True)[:3]

    st.markdown(
        "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
        'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Weakest Subjects</h3>'
        '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
        "Top subjects to focus your study on</p>",
        unsafe_allow_html=True,
    )

    cols = st.columns(len(sorted_subjects))
    for i, (subject, count) in enumerate(sorted_subjects):
        # Find most common error type for this subject
        subj_errors = [e for e in errors if e.get("subject") == subject]
        type_counts: Dict[str, int] = {}
        for err in subj_errors:
            t = err.get("type", "Other") or "Other"
            type_counts[t] = type_counts.get(t, 0) + 1
        top_type = max(type_counts, key=type_counts.get) if type_counts else "--"

        with cols[i]:
            ui.render_metric_card(
                label=subject,
                value=f"{count} errors",
                icon_char="!",
                icon_bg=Colors.CARD_ERROR_BG,
                icon_color=Colors.CARD_ERROR_COLOR,
                pill_text=f"Top: {top_type}",
                pill_class="pill-negative",
            )


def _render_avoidable_errors(errors: List[Dict[str, Any]]) -> None:
    """Show avoidable error stats — errors that could be eliminated with better habits."""
    total = len(errors)
    if total == 0:
        return

    # Count avoidable errors
    type_counts: Dict[str, int] = {}
    for err in errors:
        t = err.get("type", "Other") or "Other"
        type_counts[t] = type_counts.get(t, 0) + 1

    avoidable_count = sum(type_counts.get(et, 0) for et in AVOIDABLE_ERROR_TYPES)
    if avoidable_count == 0:
        return

    avoidable_pct = avoidable_count / total * 100

    # Most common avoidable type
    avoidable_breakdown = {
        t: c for t, c in type_counts.items() if t in AVOIDABLE_ERROR_TYPES
    }
    top_avoidable = (
        max(avoidable_breakdown, key=avoidable_breakdown.get)
        if avoidable_breakdown
        else "--"
    )

    # Subject most affected by avoidable errors
    avoidable_errors = [e for e in errors if e.get("type") in AVOIDABLE_ERROR_TYPES]
    subj_counts: Dict[str, int] = {}
    for err in avoidable_errors:
        s = err.get("subject", "Unknown") or "Unknown"
        subj_counts[s] = subj_counts.get(s, 0) + 1
    top_subj = max(subj_counts, key=subj_counts.get) if subj_counts else "--"

    st.markdown(
        "<h3 style=\"font-family:'Helvetica Neue',sans-serif;font-size:1.2rem;"
        'font-weight:700;color:#0f172a;margin:0 0 0.4rem 0;">Avoidable Errors</h3>'
        '<p style="font-size:0.9rem;color:#94a3b8;margin:0 0 1rem 0;">'
        "Mistakes that could be eliminated with better test-taking habits</p>",
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns(3)

    with col1:
        ui.render_metric_card(
            label="Avoidable Errors",
            value=avoidable_count,
            icon_char="!",
            icon_bg=Colors.CARD_AVOIDABLE_BG,
            icon_color=Colors.CARD_AVOIDABLE_COLOR,
            pill_text=f"{avoidable_pct:.0f}% of total",
            pill_class="pill-negative",
        )

    with col2:
        ui.render_metric_card(
            label="Most Common Type",
            value=top_avoidable,
            icon_char="!",
            icon_bg=Colors.CARD_TOTAL_BG,
            icon_color=Colors.CARD_TOTAL_COLOR,
        )

    with col3:
        ui.render_metric_card(
            label="Most Affected Subject",
            value=top_subj,
            icon_char="!",
            icon_bg=Colors.CARD_SUBJECT_BG,
            icon_color=Colors.CARD_SUBJECT_COLOR,
        )


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

    linked_errors = _get_linked_errors(exams, errors)

    if not linked_errors:
        st.info("No errors have been linked to these mock exams yet.")
        return

    for exam in exams:
        exam_id = exam.get("id")
        if not exam_id:
            continue

        exam_date = exam.get("date")
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
                if st.button("Edit Exam", key=f"edit_{exam_id}", width="stretch"):
                    st.session_state[f"editing_{exam_id}"] = True
                    st.rerun()

            with col_delete:
                if st.button(
                    "Delete Exam",
                    key=f"delete_{exam_id}",
                    width="stretch",
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
                        width="stretch",
                        type="primary",
                    ):
                        from src.services import db_service as db

                        user_id = st.session_state["user"].id
                        if db.delete_mock_exam(exam_id, user_id):
                            st.success("Exam deleted successfully!")
                            st.session_state.pop(f"confirm_delete_{exam_id}", None)
                            st.rerun()
                        else:
                            st.error("Failed to delete exam. Please try again.")

                with col_no:
                    if st.button(
                        "Cancel", key=f"confirm_no_{exam_id}", width="stretch"
                    ):
                        st.session_state.pop(f"confirm_delete_{exam_id}", None)
                        st.rerun()


def _render_edit_form(exam: Dict[str, Any]) -> None:
    """Render comprehensive inline edit form for a mock exam."""
    exam_id = exam.get("id", "")
    exam_type = exam.get("exam_type", "General")
    breakdown = exam.get("breakdown_json") or {}

    st.markdown("**Edit Exam Details:**")

    with st.form(f"edit_form_{exam_id}"):
        new_name = st.text_input("Exam Name", value=exam.get("exam_name", ""))
        new_notes = st.text_area("Notes", value=exam.get("notes", ""))

        # Get section definitions if exam has structured sections
        from config import get_sections_for_exam

        sections = get_sections_for_exam(exam_type)

        new_breakdown = {}
        new_total_score = exam.get("total_score", 0)
        new_max_score = exam.get("max_possible_score", 0)

        if sections and isinstance(breakdown, dict):
            st.markdown("**Section Scores:**")

            # Allow editing each section score
            for key, sec in sections.items():
                if key in breakdown and isinstance(breakdown[key], dict):
                    current_score = breakdown[key].get("score", 0)
                    max_score = breakdown[key].get("max", sec["max"])

                    if sec["is_essay"]:
                        new_score = st.number_input(
                            f"{sec['label']} ({sec['min']}-{max_score})",
                            min_value=sec["min"],
                            max_value=max_score,
                            value=int(current_score),
                            step=10,
                            key=f"edit_sec_{key}_{exam_id}",
                        )
                    else:
                        new_score = st.number_input(
                            f"{sec['label']} (0-{max_score} correct)",
                            min_value=0,
                            max_value=max_score,
                            value=int(current_score),
                            step=1,
                            key=f"edit_sec_{key}_{exam_id}",
                        )

                    new_breakdown[key] = {
                        "label": sec["label"],
                        "score": new_score,
                        "max": max_score,
                        "subject": sec["subject"],
                    }

            # Recalculate totals
            new_total_score = sum(s["score"] for s in new_breakdown.values())
            new_max_score = sum(s["max"] for s in new_breakdown.values())

            # Show updated percentage
            if new_max_score > 0:
                new_pct = (new_total_score / new_max_score) * 100
                st.metric("Updated Percentage", f"{new_pct:.1f}%")
        else:
            # For exams without sections, allow editing total score directly
            col1, col2 = st.columns(2)
            with col1:
                new_total_score = st.number_input(
                    "Total Score",
                    min_value=0.0,
                    value=float(exam.get("total_score", 0)),
                    step=1.0,
                    key=f"edit_total_{exam_id}",
                )
            with col2:
                new_max_score = st.number_input(
                    "Max Score",
                    min_value=1.0,
                    value=float(exam.get("max_possible_score", 100)),
                    step=1.0,
                    key=f"edit_max_{exam_id}",
                )

        col_submit, col_cancel = st.columns(2)

        with col_submit:
            if st.form_submit_button("Save Changes", width="stretch", type="primary"):
                from src.services import db_service as db

                user_id = st.session_state["user"].id

                updates = {
                    "exam_name": new_name,
                    "notes": new_notes,
                    "total_score": new_total_score,
                    "max_possible_score": new_max_score,
                }

                # Update breakdown if sections were edited
                if new_breakdown:
                    # Keep extra fields like tri_score, scaled_score
                    for k, v in breakdown.items():
                        if k not in new_breakdown and not isinstance(v, dict):
                            new_breakdown[k] = v
                    updates["breakdown_json"] = new_breakdown

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
            if st.form_submit_button("Cancel", width="stretch"):
                st.session_state.pop(f"editing_{exam_id}", None)
                st.rerun()
