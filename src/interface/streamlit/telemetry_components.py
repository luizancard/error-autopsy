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
        st.success(
            f"✅ Study session logged successfully! You answered {errors_count} questions incorrectly."
        )

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

    with col2:
        if st.button("No, Skip", use_container_width=True):
            st.session_state["show_error_prompt"] = False
            st.session_state.pop("last_session_id", None)
            st.session_state.pop("last_session_subject", None)
            st.session_state.pop("last_session_exam_type", None)


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

    # Initialize session state for mock exam form
    if "mock_exam_form" not in st.session_state:
        st.session_state.mock_exam_form = {
            "exam_type": "General",
            "exam_date": date.today(),
            "exam_name": "",
            "section_values": {},
            "tri_score": 0.0,
            "scaled_score": 0,
            "total_score": 0.0,
            "max_possible_score": 100.0,
            "notes": "",
        }

    form_state = st.session_state.mock_exam_form

    # Exam identification (not in form, so it doesn't trigger submission)
    col1, col2 = st.columns(2)

    with col1:
        form_state["exam_type"] = st.selectbox(
            "Exam Type",
            options=EXAM_TYPES,
            index=EXAM_TYPES.index(form_state["exam_type"]),
            help="Which exam did you simulate?",
        )

    with col2:
        form_state["exam_date"] = st.date_input(
            "Date Taken", value=form_state["exam_date"], max_value=date.today()
        )

    form_state["exam_name"] = st.text_input(
        "Exam Name *",
        value=form_state["exam_name"],
        placeholder="e.g., FUVEST 2024 Phase 1, ENEM Simulado 3",
        help="Give this exam a descriptive name",
    )

    st.divider()

    # Check if this exam has structured sections
    sections = get_sections_for_exam(form_state["exam_type"])

    if sections:
        # Exam-specific section inputs
        st.markdown("### Section Scores")

        for key, sec in sections.items():
            if key not in form_state["section_values"]:
                form_state["section_values"][key] = sec["min"]

            if sec["is_essay"]:
                form_state["section_values"][key] = st.number_input(
                    f"{sec['label']} ({sec['min']}-{sec['max']})",
                    min_value=sec["min"],
                    max_value=sec["max"],
                    value=form_state["section_values"][key],
                    step=10,
                    key=f"sec_{key}",
                )
            else:
                form_state["section_values"][key] = st.number_input(
                    f"{sec['label']} (0-{sec['max']} correct)",
                    min_value=sec["min"],
                    max_value=sec["max"],
                    value=form_state["section_values"][key],
                    step=1,
                    key=f"sec_{key}",
                )

        # Optional extra score fields
        if form_state["exam_type"] == "ENEM":
            st.divider()
            form_state["tri_score"] = st.number_input(
                "TRI Score (optional)",
                min_value=0.0,
                max_value=1000.0,
                value=form_state["tri_score"],
                step=1.0,
                help="Final TRI calculated score, if available",
            )

        elif form_state["exam_type"] == "SAT":
            st.divider()
            form_state["scaled_score"] = st.number_input(
                "Scaled Score (optional, 400-1600)",
                min_value=0,
                max_value=1600,
                value=form_state["scaled_score"],
                step=10,
                help="Official scaled score, if available",
            )

        # Calculate totals from section values
        form_state["total_score"] = float(sum(form_state["section_values"].values()))
        form_state["max_possible_score"] = float(
            sum(sec["max"] for sec in sections.values())
        )

    else:
        # Generic scoring for other exam types
        st.markdown("### Scoring")
        col1, col2 = st.columns(2)

        with col1:
            form_state["total_score"] = st.number_input(
                "Your Score",
                min_value=0.0,
                max_value=10000.0,
                value=form_state["total_score"],
                step=1.0,
                help="Points you scored",
            )

        with col2:
            form_state["max_possible_score"] = st.number_input(
                "Maximum Possible Score",
                min_value=1.0,
                max_value=10000.0,
                value=form_state["max_possible_score"],
                step=1.0,
                help="Total points available",
            )

    # Score preview (updates in real-time)
    if form_state["max_possible_score"] > 0:
        percentage = (
            form_state["total_score"] / form_state["max_possible_score"]
        ) * 100
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
    form_state["notes"] = st.text_area(
        "Notes (optional)",
        value=form_state["notes"],
        placeholder="How did it feel? What sections were hardest?",
        help="Add any observations about this exam",
    )

    # Submit button (outside form)
    col_button1, col_button2 = st.columns([3, 1])

    with col_button1:
        if st.button("Log Mock Exam", use_container_width=True, type="primary"):
            # Validation and submission
            if not form_state["exam_name"].strip():
                st.error("Please enter an exam name.")
            elif form_state["total_score"] > form_state["max_possible_score"]:
                st.error("Score cannot exceed maximum possible score.")
            else:
                # Build breakdown_json
                breakdown_json = {}
                if sections:
                    for key, sec in sections.items():
                        breakdown_json[key] = {
                            "label": sec["label"],
                            "score": form_state["section_values"][key],
                            "max": sec["max"],
                            "subject": sec["subject"],
                        }
                    if (
                        form_state["exam_type"] == "ENEM"
                        and form_state["tri_score"] > 0
                    ):
                        breakdown_json["tri_score"] = form_state["tri_score"]
                    elif (
                        form_state["exam_type"] == "SAT"
                        and form_state["scaled_score"] > 0
                    ):
                        breakdown_json["scaled_score"] = form_state["scaled_score"]

                exam_id = db.create_mock_exam(
                    user_id=user_id,
                    exam_name=form_state["exam_name"].strip(),
                    exam_type=form_state["exam_type"],
                    total_score=form_state["total_score"],
                    max_possible_score=form_state["max_possible_score"],
                    date_val=form_state["exam_date"],
                    breakdown_json=breakdown_json if breakdown_json else None,
                    notes=form_state["notes"].strip() if form_state["notes"] else None,
                )

                if exam_id:
                    st.session_state["simulado_form_submitted"] = True
                    st.session_state["simulado_exam_id"] = exam_id

                    # Store form state before clearing for error logging
                    stored_form_state = form_state.copy()
                    stored_section_values = form_state["section_values"].copy()

                    # Clear form after successful submission
                    st.session_state.mock_exam_form = {
                        "exam_type": "General",
                        "exam_date": date.today(),
                        "exam_name": "",
                        "section_values": {},
                        "tri_score": 0.0,
                        "scaled_score": 0,
                        "total_score": 0.0,
                        "max_possible_score": 100.0,
                        "notes": "",
                    }

                    # Check if any section had errors for error logging prompt
                    has_errors = False
                    if sections:
                        for key, sec in sections.items():
                            val = stored_section_values.get(key, 0)
                            mx = sec["max"]
                            if not sec["is_essay"] and val < mx:
                                has_errors = True
                                break

                    if has_errors:
                        st.session_state["mock_exam_id"] = exam_id
                        st.session_state["mock_exam_type"] = stored_form_state[
                            "exam_type"
                        ]
                        st.session_state["mock_exam_breakdown"] = breakdown_json
                        st.session_state["mock_exam_date"] = stored_form_state[
                            "exam_date"
                        ]
                        st.session_state["show_mock_error_prompt"] = True

                    # Rerun to clear form visually
                    st.rerun()
                else:
                    st.error("Failed to log exam. Please try again.")

    with col_button2:
        if st.button("Clear", use_container_width=True):
            st.session_state.mock_exam_form = {
                "exam_type": "General",
                "exam_date": date.today(),
                "exam_name": "",
                "section_values": {},
                "tri_score": 0.0,
                "scaled_score": 0,
                "total_score": 0.0,
                "max_possible_score": 100.0,
                "notes": "",
            }
            st.rerun()

    # Show success message after form submission
    if st.session_state.get("simulado_form_submitted", False):
        st.success(
            "✅ Mock exam logged successfully! You can now log errors from this exam."
        )

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
                    {
                        "key": key,
                        "label": sec["label"],
                        "subject": sec["subject"],
                        "wrong": wrong,
                    }
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
        if st.button(
            "Yes, Log Errors", use_container_width=True, type="primary", key="mock_yes"
        ):
            st.session_state["show_mock_error_form"] = True
            st.session_state["show_mock_error_prompt"] = False

    with col2:
        if st.button("No, Skip", use_container_width=True, key="mock_skip"):
            _clear_mock_exam_state()


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

    # Show success message if error was just logged
    if st.session_state.get("mock_error_just_logged"):
        section_label = st.session_state.get("mock_error_logged_section", "")
        st.success(f"Error logged for {section_label}!")
        st.session_state.pop("mock_error_just_logged", None)
        st.session_state.pop("mock_error_logged_section", None)

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

        # Initialize error counter for this section if not exists
        counter_key = f"logged_errors_{key}"
        if counter_key not in st.session_state:
            st.session_state[counter_key] = 0

        # Check if all errors for this section are logged
        if st.session_state[counter_key] >= wrong:
            with st.expander(
                f"{sec['label']} - {wrong} error(s) ✓ All logged", expanded=False
            ):
                st.info("All errors for this section have been logged.")
            continue

        # Show progress in expander title and inside
        with st.expander(
            f"{sec['label']} - {st.session_state[counter_key]}/{wrong} errors logged",
            expanded=True,
        ):

            with st.form(f"mock_error_{key}"):
                # For ENEM, show subject dropdown; for SAT, use section subject directly
                if exam_type == "ENEM":
                    subject = st.selectbox(
                        "Subject *",
                        options=get_subjects_for_exam(exam_type),
                        help="Select the specific subject for this error",
                        key=f"mock_subject_{key}",
                    )
                else:
                    subject = sec["subject"]
                    st.caption(f"Subject: {subject}")

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
                            subject=subject,
                            topic=topic.strip(),
                            error_type=error_type,
                            description=description,
                            date_val=exam_date,
                            difficulty=difficulty,
                            exam_type=exam_type,
                            mock_exam_id=mock_exam_id,
                        )
                        if success:
                            st.session_state[counter_key] += 1
                            st.session_state["mock_error_just_logged"] = True
                            st.session_state["mock_error_logged_section"] = sec["label"]
                            st.rerun()

    # Check if all errors have been logged
    total_errors = 0
    for key, sec in sections.items():
        if sec["is_essay"]:
            continue
        sec_data = breakdown.get(key, {})
        if isinstance(sec_data, dict):
            val = sec_data.get("score", 0)
            mx = sec_data.get("max", 0)
            total_errors += max(mx - val, 0)
    
    total_logged = sum(
        st.session_state.get(f"logged_errors_{key}", 0) for key in sections.keys()
    )

    if total_logged >= total_errors and total_errors > 0:
        st.success("All errors have been logged! Click 'Done' below to finish.")

    if st.button("Done Logging Errors", key="mock_done"):
        _clear_mock_exam_state()


def _clear_mock_exam_state() -> None:
    """Remove all mock-exam error logging state."""
    # Clear error counters
    keys_to_remove = [
        k for k in st.session_state.keys() if k.startswith("logged_errors_")
    ]
    for k in keys_to_remove:
        st.session_state.pop(k, None)

    # Clear mock exam state
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
    tab1, tab2, tab3 = st.tabs(["Study Session", "Mock Exam", "Individual Error"])

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
