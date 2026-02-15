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
    get_subjects_for_exam,
)
from src.services import db_service as db


def render_session_logger(user_id: str) -> None:
    """
    Render the Study Session logging interface with real-time MPQ calculation.

    Args:
        user_id: Current user's ID
    """
    st.subheader("📚 Log a Study Session")
    st.markdown("Track a batch of questions you completed in a single study block.")

    with st.form("session_form", clear_on_submit=True):
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
                    pace_status = "⚠️ Too Fast"
                    pace_color = "inverse"
                elif pace <= benchmark * 1.2:
                    pace_status = "✅ Optimal"
                    pace_color = "normal"
                else:
                    pace_status = "🐌 Too Slow"
                    pace_color = "inverse"

                st.metric("Pace Zone", pace_status, delta_color=pace_color)

            # Warning messages
            if pace > benchmark * 1.3:
                st.warning(
                    f"⏱️ **Pace Warning:** You're taking {pace:.2f} min/question, "
                    f"but {exam_type} requires ~{benchmark:.2f} min/q. Practice faster!"
                )
            elif pace < benchmark * 0.6 and accuracy < 60:
                st.warning(
                    "🏃 **Rushing Alert:** You're going fast but accuracy is low. "
                    "Slow down and focus on precision."
                )

        # Submit button
        submitted = st.form_submit_button(
            "📊 Log Session", use_container_width=True, type="primary"
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
                st.success("✅ Session logged successfully!")

                # Store session info in session state for potential error logging
                st.session_state["last_session_id"] = session_id
                st.session_state["last_session_subject"] = subject
                st.session_state["last_session_exam_type"] = exam_type
                st.session_state["last_session_errors"] = (
                    total_questions - correct_count
                )

                # Ask if they want to log errors
                if correct_count < total_questions:
                    st.session_state["show_error_prompt"] = True

                st.rerun()
            else:
                st.error("Failed to log session. Please try again.")

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

    Args:
        user_id: Current user's ID
    """
    st.subheader("🎯 Log a Mock Exam (Simulado)")
    st.markdown("Record the results of a full practice exam.")

    with st.form("simulado_form", clear_on_submit=True):
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

        # Scoring
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

        # Calculate percentage
        if max_possible_score > 0:
            percentage = (total_score / max_possible_score) * 100
            st.metric(
                "Score Percentage",
                f"{percentage:.1f}%",
                delta="Pass" if percentage >= 70 else "Needs Improvement",
                delta_color="normal" if percentage >= 70 else "inverse",
            )

            # Performance feedback
            if percentage >= 80:
                st.success("🎉 Excellent performance! Keep it up!")
            elif percentage >= 60:
                st.info("📈 Good progress. Focus on weak areas to improve further.")
            else:
                st.warning(
                    "💪 There's room for improvement. Review fundamentals and practice more."
                )

        # Optional notes
        notes = st.text_area(
            "Notes (optional)",
            placeholder="How did it feel? What sections were hardest?",
            help="Add any observations about this exam",
        )

        # Submit
        submitted = st.form_submit_button(
            "🏆 Log Mock Exam", use_container_width=True, type="primary"
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
                    notes=notes.strip() if notes else None,
                )

                if exam_id:
                    st.success("✅ Mock exam logged successfully!")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("Failed to log exam. Please try again.")


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

    # Main tabbed interface
    tab1, tab2, tab3 = st.tabs(
        ["📚 Study Session", "🎯 Mock Exam", "❌ Individual Error"]
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
    st.info("💡 **Tip:** Use the Study Session tab to log multiple errors at once!")

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
                    st.success("✅ Error logged!")
                    st.rerun()
