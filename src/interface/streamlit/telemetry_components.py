"""
Session and Mock Exam logging UI components.

Provides tabbed interfaces for logging study sessions and mock exams
with real-time performance feedback and intelligent error linking.
"""

from datetime import date

import streamlit as st
from config import (
    DIFFICULTY_LEVELS,
    ERROR_TYPES,
    EXAM_TYPES,
    get_pace_benchmark,
    get_sections_for_exam,
    get_subjects_for_exam,
)
from src.services import db_service as db


def render_session_logger(user_id: str) -> None:
    """
    Render the Study Session logging interface with real-time MPQ calculation.

    Args:
        user_id: Current user's ID
    """
    st.subheader("Log a Study Session")
    st.markdown("Track a batch of questions you completed in a single study block.")

    with st.form("session_form"):
        col1, col2 = st.columns(2)

        with col1:
            # Exam type selector
            exam_type = st.selectbox(
                "Exam Type",
                options=EXAM_TYPES,
                help="Select the exam you're preparing for",
            )

            # Dynamic subject list based on exam
            subjects = get_subjects_for_exam(exam_type)
            subject = st.selectbox(
                "Subject", options=subjects, help="Subject you studied"
            )

        with col2:
            # Date selector
            session_date = st.date_input(
                "Date",
                value=date.today(),
                max_value=date.today(),
                help="When did you complete this session?",
            )

        st.divider()

        # Performance metrics
        col1, col2, col3 = st.columns(3)

        with col1:
            total_questions = st.number_input(
                "Total Questions",
                min_value=1,
                max_value=500,
                value=20,
                help="How many questions did you attempt?",
            )

        with col2:
            correct_count = st.number_input(
                "Correct Answers",
                min_value=0,
                max_value=total_questions,
                value=int(total_questions * 0.7),  # Default 70%
                help="How many did you get right?",
            )

        with col3:
            duration_minutes = st.number_input(
                "Time Spent (minutes)",
                min_value=1.0,
                max_value=600.0,
                value=float(total_questions * 2.5),  # Default 2.5 min/q
                step=5.0,
                help="Total time spent on these questions",
            )

        # Real-time performance feedback
        if total_questions > 0 and duration_minutes > 0:
            accuracy = (correct_count / total_questions) * 100
            pace = duration_minutes / total_questions
            benchmark = get_pace_benchmark(exam_type)

            st.markdown("---")
            st.markdown("### Performance Preview")

            metric_col1, metric_col2, metric_col3 = st.columns(3)

            with metric_col1:
                st.metric(
                    "Accuracy",
                    f"{accuracy:.1f}%",
                    delta="Good" if accuracy >= 70 else "Needs Work",
                    delta_color="normal" if accuracy >= 70 else "inverse",
                )

            with metric_col2:
                st.metric(
                    "Pace (MPQ)",
                    f"{pace:.2f} min/q",
                    delta=f"Target: {benchmark:.2f}",
                    delta_color="off",
                )

            with metric_col3:
                # Classify pace zone
                if pace < benchmark * 0.5:
                    pace_status = "Too Fast"
                    pace_color = "inverse"
                elif pace <= benchmark * 1.2:
                    pace_status = "Optimal"
                    pace_color = "normal"
                else:
                    pace_status = "Too Slow"
                    pace_color = "inverse"

                st.metric("Pace Zone", pace_status, delta_color=pace_color)

            # Warning messages
            if pace > benchmark * 1.3:
                st.warning(
                    f"**Pace Warning:** You're taking {pace:.2f} min/question, "
                    f"but {exam_type} requires ~{benchmark:.2f} min/q. Practice faster!"
                )
            elif pace < benchmark * 0.6 and accuracy < 60:
                st.warning(
                    "**Rushing Alert:** You're going fast but accuracy is low. "
                    "Slow down and focus on precision."
                )

        # Submit button
        submitted = st.form_submit_button(
            "Log Session", use_container_width=True, type="primary"
        )

        if submitted:
            # Create session
            session_id = db.create_study_session(
                user_id=user_id,
                exam_type=exam_type,
                subject=subject,
                total_questions=total_questions,
                correct_count=correct_count,
                duration_minutes=duration_minutes,
                date_val=session_date,
            )

            if session_id:
                # Store session info in session state for potential error logging
                st.session_state["last_session_id"] = session_id
                st.session_state["last_session_subject"] = subject
                st.session_state["last_session_exam_type"] = exam_type
                st.session_state["last_session_errors"] = (
                    total_questions - correct_count
                )
                st.session_state["session_form_submitted"] = True

                # Ask if they want to log errors
                if correct_count < total_questions:
                    st.session_state["show_error_prompt"] = True
            else:
                st.error("Failed to log session. Please try again.")

    # Show success message after form submission
    if st.session_state.get("session_form_submitted", False):
        errors_count = st.session_state.get("last_session_errors", 0)
        st.success(f"✅ Study session logged successfully! You answered {errors_count} questions incorrectly.")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Clear Form", use_container_width=True, key="session_clear"):
                st.session_state["session_form_submitted"] = False
                st.rerun()

    # Show error logging prompt if triggered
    if st.session_state.get("show_error_prompt", False):
        _render_error_prompt_for_session()


def _render_error_prompt_for_session() -> None:
    """
    Prompt user to log errors from the last session.
    """
    st.markdown("---")
    st.markdown("### Did you make mistakes in this session?")

    errors_count = st.session_state.get("last_session_errors", 0)
    st.info(
        f"You got {errors_count} question(s) wrong. "
        "Would you like to log the specific errors?"
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Yes, Log Errors", use_container_width=True, type="primary"):
            st.session_state["show_error_form"] = True
            st.session_state["show_error_prompt"] = False
            st.rerun()

    with col2:
        if st.button("No, Skip", use_container_width=True):
            st.session_state["show_error_prompt"] = False
            st.session_state.pop("last_session_id", None)
            st.session_state.pop("last_session_subject", None)
            st.session_state.pop("last_session_exam_type", None)
            st.rerun()


def render_error_logger_for_session(user_id: str, session_id: str) -> None:
    """
    Render error logging form linked to a specific session.

    Args:
        user_id: Current user's ID
        session_id: Session ID to link errors to
    """
    st.markdown("### Log Errors from Session")
    st.info("Add specific errors you made during this session (one at a time).")

    with st.form("session_error_form"):
        col1, col2 = st.columns(2)

        with col1:
            topic = st.text_input(
                "Topic *",
                help="Specific topic of the error (e.g., 'Quadratic Functions')",
            )
            error_type = st.selectbox("Error Type *", options=ERROR_TYPES, index=0)

        with col2:
            difficulty = st.selectbox(
                "Difficulty",
                options=DIFFICULTY_LEVELS,
                index=1,  # Default to Medium
            )

        description = st.text_area(
            "Description (optional)", help="What went wrong? What did you learn?"
        )

        submitted = st.form_submit_button("Add Error", use_container_width=True)

        if submitted:
            if not topic.strip():
                st.error("Please enter a topic.")
            else:
                session_subject = st.session_state.get(
                    "last_session_subject", "Unknown"
                )
                session_exam_type = st.session_state.get(
                    "last_session_exam_type", "General"
                )
                success = db.log_error_with_session(
                    user_id=user_id,
                    subject=session_subject,
                    topic=topic.strip(),
                    error_type=error_type,
                    description=description,
                    date_val=date.today(),
                    difficulty=difficulty,
                    exam_type=session_exam_type,
                    session_id=session_id,
                )

                if success:
                    st.success("Error logged!")
                    st.rerun()

    if st.button("Done Logging Errors"):
        st.session_state["show_error_form"] = False
        st.session_state.pop("last_session_id", None)
        st.session_state.pop("last_session_subject", None)
        st.session_state.pop("last_session_exam_type", None)
        st.rerun()


def render_simulado_logger(user_id: str) -> None:
    """
    Render the Mock Exam (Simulado) logging interface.
    Shows exam-specific section inputs for ENEM and SAT.

    Args:
        user_id: Current user's ID
    """
    st.subheader("Log a Mock Exam (Simulado)")
    st.markdown("Record the results of a full practice exam.")

    with st.form("simulado_form"):
        # Exam identification
        col1, col2 = st.columns(2)

        with col1:
            exam_type = st.selectbox(
                "Exam Type", options=EXAM_TYPES, help="Which exam did you simulate?"
            )

        with col2:
            exam_date = st.date_input(
                "Date Taken", value=date.today(), max_value=date.today()
            )

        exam_name = st.text_input(
            "Exam Name *",
            placeholder="e.g., FUVEST 2024 Phase 1, ENEM Simulado 3",
            help="Give this exam a descriptive name",
        )

        st.divider()

        # Check if this exam has structured sections
        sections = get_sections_for_exam(exam_type)

        breakdown_json = {}
        total_score = 0.0
        max_possible_score = 100.0

        if sections:
            # Exam-specific section inputs
            st.markdown("### Section Scores")

            section_values = {}
            for key, sec in sections.items():
                if sec["is_essay"]:
                    val = st.number_input(
                        f"{sec['label']} ({sec['min']}-{sec['max']})",
                        min_value=sec["min"],
                        max_value=sec["max"],
                        value=sec["min"],
                        step=10,
                        key=f"sec_{key}",
                    )
                else:
                    val = st.number_input(
                        f"{sec['label']} (0-{sec['max']} correct)",
                        min_value=sec["min"],
                        max_value=sec["max"],
                        value=0,
                        step=1,
                        key=f"sec_{key}",
                    )
                section_values[key] = val

            # Optional extra score fields
            if exam_type == "ENEM":
                st.divider()
                tri_score = st.number_input(
                    "TRI Score (optional)",
                    min_value=0.0,
                    max_value=1000.0,
                    value=0.0,
                    step=1.0,
                    help="Final TRI calculated score, if available",
                )
                # Build breakdown
                for key, sec in sections.items():
                    breakdown_json[key] = {
                        "label": sec["label"],
                        "score": section_values[key],
                        "max": sec["max"],
                        "subject": sec["subject"],
                    }
                if tri_score > 0:
                    breakdown_json["tri_score"] = tri_score
                # total = sum of objective correct + redacao
                total_score = float(sum(section_values.values()))
                max_possible_score = float(
                    sum(sec["max"] for sec in sections.values())
                )

            elif exam_type == "SAT":
                st.divider()
                scaled_score = st.number_input(
                    "Scaled Score (optional, 400-1600)",
                    min_value=0,
                    max_value=1600,
                    value=0,
                    step=10,
                    help="Official scaled score, if available",
                )
                for key, sec in sections.items():
                    breakdown_json[key] = {
                        "label": sec["label"],
                        "score": section_values[key],
                        "max": sec["max"],
                        "subject": sec["subject"],
                    }
                if scaled_score > 0:
                    breakdown_json["scaled_score"] = scaled_score
                total_score = float(sum(section_values.values()))
                max_possible_score = float(
                    sum(sec["max"] for sec in sections.values())
                )

        else:
            # Generic scoring for other exam types
            st.markdown("### Scoring")
            col1, col2 = st.columns(2)

            with col1:
                total_score = st.number_input(
                    "Your Score",
                    min_value=0.0,
                    max_value=10000.0,
                    value=0.0,
                    step=1.0,
                    help="Points you scored",
                )

            with col2:
                max_possible_score = st.number_input(
                    "Maximum Possible Score",
                    min_value=1.0,
                    max_value=10000.0,
                    value=100.0,
                    step=1.0,
                    help="Total points available",
                )

        # Score preview
        if max_possible_score > 0:
            percentage = (total_score / max_possible_score) * 100
            st.metric(
                "Score Percentage",
                f"{percentage:.1f}%",
                delta="Pass" if percentage >= 70 else "Needs Improvement",
                delta_color="normal" if percentage >= 70 else "inverse",
            )

            if percentage >= 80:
                st.success("Excellent performance! Keep it up!")
            elif percentage >= 60:
                st.info("Good progress. Focus on weak areas to improve further.")
            else:
                st.warning(
                    "There's room for improvement. Review fundamentals and practice more."
                )

        # Optional notes
        notes = st.text_area(
            "Notes (optional)",
            placeholder="How did it feel? What sections were hardest?",
            help="Add any observations about this exam",
        )

        # Submit
        submitted = st.form_submit_button(
            "Log Mock Exam", use_container_width=True, type="primary"
        )

        if submitted:
            if not exam_name.strip():
                st.error("Please enter an exam name.")
            elif total_score > max_possible_score:
                st.error("Score cannot exceed maximum possible score.")
            else:
                exam_id = db.create_mock_exam(
                    user_id=user_id,
                    exam_name=exam_name.strip(),
                    exam_type=exam_type,
                    total_score=total_score,
                    max_possible_score=max_possible_score,
                    date_val=exam_date,
                    breakdown_json=breakdown_json if breakdown_json else None,
                    notes=notes.strip() if notes else None,
                )

                if exam_id:
                    st.session_state["simulado_form_submitted"] = True
                    st.session_state["simulado_exam_id"] = exam_id
                    
                    # Check if any section had errors for error logging prompt
                    has_errors = False
                    if sections:
                        for key, sec in sections.items():
                            score = breakdown_json.get(key, {})
                            if isinstance(score, dict):
                                val = score.get("score", 0)
                                mx = score.get("max", 0)
                                if not sec["is_essay"] and val < mx:
                                    has_errors = True
                                    break

                    if has_errors:
                        st.session_state["mock_exam_id"] = exam_id
                        st.session_state["mock_exam_type"] = exam_type
                        st.session_state["mock_exam_breakdown"] = breakdown_json
                        st.session_state["mock_exam_date"] = exam_date
                        st.session_state["show_mock_error_prompt"] = True
                else:
                    st.error("Failed to log exam. Please try again.")

    # Show success message after form submission
    if st.session_state.get("simulado_form_submitted", False):
        st.success(f"✅ Mock exam logged successfully! You can now log errors from this exam.")
        
        col1, col2 = st.columns([3, 1])
        with col2:
            if st.button("Clear Form", use_container_width=True):
                st.session_state["simulado_form_submitted"] = False
                st.session_state["simulado_exam_id"] = None
                st.rerun()

    # Show error logging prompt after mock exam
    if st.session_state.get("show_mock_error_prompt", False):
        _render_mock_exam_error_prompt()


def _render_mock_exam_error_prompt() -> None:
    """Prompt user to log errors from their mock exam sections."""
    st.markdown("---")
    st.markdown("### Log Errors from Mock Exam")

    breakdown = st.session_state.get("mock_exam_breakdown", {})
    exam_type = st.session_state.get("mock_exam_type", "General")
    sections = get_sections_for_exam(exam_type)

    if not sections or not breakdown:
        st.session_state["show_mock_error_prompt"] = False
        return

    # Show sections that had wrong answers
    sections_with_errors = []
    for key, sec in sections.items():
        sec_data = breakdown.get(key, {})
        if isinstance(sec_data, dict) and not sec["is_essay"]:
            val = sec_data.get("score", 0)
            mx = sec_data.get("max", 0)
            wrong = mx - val
            if wrong > 0:
                sections_with_errors.append(
                    {"key": key, "label": sec["label"], "subject": sec["subject"], "wrong": wrong}
                )

    if not sections_with_errors:
        st.info("No wrong answers detected in objective sections.")
        st.session_state["show_mock_error_prompt"] = False
        return

    st.info(
        "You had wrong answers in some sections. "
        "Log specific errors to track your weak points."
    )

    col1, col2 = st.columns([1, 1])

    with col1:
        if st.button("Yes, Log Errors", use_container_width=True, type="primary", key="mock_yes"):
            st.session_state["show_mock_error_form"] = True
            st.session_state["show_mock_error_prompt"] = False
            st.rerun()

    with col2:
        if st.button("No, Skip", use_container_width=True, key="mock_skip"):
            _clear_mock_exam_state()
            st.rerun()


def _render_mock_exam_error_logger(user_id: str) -> None:
    """Render per-section error logging for a mock exam."""
    st.markdown("### Log Errors from Mock Exam")

    mock_exam_id = st.session_state.get("mock_exam_id")
    exam_type = st.session_state.get("mock_exam_type", "General")
    breakdown = st.session_state.get("mock_exam_breakdown", {})
    exam_date = st.session_state.get("mock_exam_date", date.today())
    sections = get_sections_for_exam(exam_type)

    if not sections or not mock_exam_id:
        _clear_mock_exam_state()
        return

    # Show sections with errors
    for key, sec in sections.items():
        sec_data = breakdown.get(key, {})
        if not isinstance(sec_data, dict) or sec["is_essay"]:
            continue
        val = sec_data.get("score", 0)
        mx = sec_data.get("max", 0)
        wrong = mx - val
        if wrong <= 0:
            continue

        with st.expander(f"{sec['label']} - {wrong} error(s)", expanded=False):
            with st.form(f"mock_error_{key}", clear_on_submit=True):
                topic = st.text_input(
                    "Topic *",
                    help="Specific topic of the error",
                    key=f"mock_topic_{key}",
                )
                col1, col2 = st.columns(2)
                with col1:
                    error_type = st.selectbox(
                        "Error Type *",
                        options=ERROR_TYPES,
                        key=f"mock_etype_{key}",
                    )
                with col2:
                    difficulty = st.selectbox(
                        "Difficulty",
                        options=DIFFICULTY_LEVELS,
                        index=1,
                        key=f"mock_diff_{key}",
                    )
                description = st.text_area(
                    "Description (optional)",
                    key=f"mock_desc_{key}",
                )

                if st.form_submit_button("Add Error", use_container_width=True):
                    if not topic.strip():
                        st.error("Please enter a topic.")
                    else:
                        success = db.log_error_with_session(
                            user_id=user_id,
                            subject=sec["subject"],
                            topic=topic.strip(),
                            error_type=error_type,
                            description=description,
                            date_val=exam_date,
                            difficulty=difficulty,
                            exam_type=exam_type,
                            mock_exam_id=mock_exam_id,
                        )
                        if success:
                            st.success(f"Error logged for {sec['label']}!")
                            st.rerun()

    if st.button("Done Logging Errors", key="mock_done"):
        _clear_mock_exam_state()
        st.rerun()


def _clear_mock_exam_state() -> None:
    """Remove all mock-exam error logging state."""
    for k in [
        "mock_exam_id",
        "mock_exam_type",
        "mock_exam_breakdown",
        "mock_exam_date",
        "show_mock_error_prompt",
        "show_mock_error_form",
    ]:
        st.session_state.pop(k, None)


def render_tabbed_logger(user_id: str) -> None:
    """
    Render the complete tabbed logging interface.

    Provides tabs for:
    1. Study Sessions (batch question logging)
    2. Mock Exams (simulados)
    3. Individual Errors (legacy single-error logging)

    Args:
        user_id: Current user's ID
    """
    # Check if we need to show session-linked error form
    if st.session_state.get("show_error_form", False):
        session_id = st.session_state.get("last_session_id")
        if session_id:
            render_error_logger_for_session(user_id, session_id)
            return

    # Check if we need to show mock-exam-linked error form
    if st.session_state.get("show_mock_error_form", False):
        _render_mock_exam_error_logger(user_id)
        return

    # Main tabbed interface
    tab1, tab2, tab3 = st.tabs(
        ["Study Session", "Mock Exam", "Individual Error"]
    )

    with tab1:
        render_session_logger(user_id)

    with tab2:
        render_simulado_logger(user_id)

    with tab3:
        # Keep the original single-error logging as fallback
        render_legacy_error_logger(user_id)


def render_legacy_error_logger(user_id: str) -> None:
    """Legacy single-error logging form."""
    st.info("**Tip:** Use the Study Session tab to log multiple errors at once!")

    with st.form("legacy_error_form", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            subject = st.text_input("Subject *")
            topic = st.text_input("Topic *")
            difficulty = st.selectbox("Difficulty", options=DIFFICULTY_LEVELS, index=1)

        with col2:
            error_date = st.date_input(
                "Date", value=date.today(), max_value=date.today()
            )
            error_type = st.selectbox("Error Type *", options=ERROR_TYPES, index=0)

        description = st.text_area("Description (optional)", help="What went wrong?")

        submitted = st.form_submit_button("Log Error", use_container_width=True)

        if submitted:
            if not subject.strip() or not topic.strip():
                st.error("Subject and Topic are required.")
            else:
                success = db.log_error(
                    user_id=user_id,
                    subject=subject.strip(),
                    topic=topic.strip(),
                    error_type=error_type,
                    description=description,
                    date_val=error_date,
                    difficulty=difficulty,
                )

                if success:
                    st.success("Error logged!")
                    st.rerun()
