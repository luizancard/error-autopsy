"""
History page UI components for Error Autopsy.

Provides filter popup, editable table, and filter logic for database management.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set

import pandas as pd

import streamlit as st
from config import DIFFICULTY_LEVELS, ERROR_TYPES


def get_unique_values(data: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """
    Extract unique subjects and topics from database.

    Args:
        data: List of error records.

    Returns:
        Dictionary with 'subjects' and 'topics' lists.
    """
    subjects: Set[str] = set()
    topics: Set[str] = set()
    exam_types: Set[str] = set()

    for record in data:
        subject = record.get("subject", "").strip()
        topic = record.get("topic", "").strip()
        etype = record.get("exam_type", "").strip()

        if subject:
            subjects.add(subject)
        if topic:
            topics.add(topic)
        if etype:
            exam_types.add(etype)

    return {
        "subjects": sorted(list(subjects)),
        "topics": sorted(list(topics)),
        "exam_types": sorted(list(exam_types)),
    }


def render_filter_popup(all_data: List[Dict[str, Any]]) -> None:
    # Inicializa o estado se não existir
    if "history_filters" not in st.session_state:
        st.session_state.history_filters = {
            "subjects": [],
            "topics": [],
            "exam_types": [],  # Values from data
            "error_types": [],
            "difficulties": [],
            "date_from": None,
            "date_to": None,
        }

    # Pega valores únicos dos dados passados
    unique_vals = get_unique_values(all_data)

    with st.popover("Filter", width="content"):
        st.markdown("### Filter Options")

        # Exam Type filter
        st.markdown("**Exam Type**")
        selected_exam_types = st.multiselect(
            "Select exam types",
            options=unique_vals["exam_types"],
            default=st.session_state.history_filters.get("exam_types", []),
            key="filter_exam_types_select",
            label_visibility="collapsed",
        )

        # Subject filter
        st.markdown("**Subject**")
        selected_subjects = st.multiselect(
            "Select subjects",
            options=unique_vals["subjects"],
            default=st.session_state.history_filters["subjects"],
            key="filter_subjects_select",
            label_visibility="collapsed",
        )

        # Topic filter
        st.markdown("**Topic**")
        selected_topics = st.multiselect(
            "Select topics",
            options=unique_vals["topics"],
            default=st.session_state.history_filters["topics"],
            key="filter_topics_select",
            label_visibility="collapsed",
        )

        # Error type filter
        st.markdown("**Error Type**")
        selected_types = st.multiselect(
            "Select error types",
            options=ERROR_TYPES,
            default=st.session_state.history_filters["error_types"],
            key="filter_types_select",
            label_visibility="collapsed",
        )

        # Difficulty filter
        st.markdown("**Difficulty**")
        selected_difficulties = st.multiselect(
            "Select difficulties",
            options=DIFFICULTY_LEVELS,
            default=st.session_state.history_filters["difficulties"],
            key="filter_difficulties_select",
            label_visibility="collapsed",
        )

        # Date range filter
        st.markdown("**Date Range**")
        col1, col2 = st.columns(2)
        with col1:
            date_from = st.date_input(
                "From",
                value=st.session_state.history_filters["date_from"],
                key="filter_date_from",
            )
        with col2:
            date_to = st.date_input(
                "To",
                value=st.session_state.history_filters["date_to"],
                key="filter_date_to",
            )

        # Action buttons
        col_apply, col_clear = st.columns(2)
        with col_apply:
            if st.button("Apply Filters", width="stretch", type="primary"):
                st.session_state.history_filters = {
                    "subjects": selected_subjects,
                    "topics": selected_topics,
                    "exam_types": selected_exam_types,
                    "error_types": selected_types,
                    "difficulties": selected_difficulties,
                    "date_from": date_from if date_from else None,
                    "date_to": date_to if date_to else None,
                }
                st.rerun()

        with col_clear:
            if st.button("Clear All", width="stretch"):
                st.session_state.history_filters = {
                    "subjects": [],
                    "topics": [],
                    "exam_types": [],
                    "error_types": [],
                    "difficulties": [],
                    "date_from": None,
                    "date_to": None,
                }
                st.rerun()


def render_active_filters() -> None:
    """
    Display active filter tags/pills below the filter button.
    """
    filters = st.session_state.get("history_filters", {})
    active_filters = []

    # Coleta filtros ativos para exibição
    if filters.get("subjects"):
        for subj in filters["subjects"]:
            active_filters.append(("Subject", subj))

    if filters.get("exam_types"):
        for et in filters["exam_types"]:
            active_filters.append(("Exam Type", et))

    if filters.get("topics"):
        for topic in filters["topics"]:
            active_filters.append(("Topic", topic))

    if filters.get("error_types"):
        for err_type in filters["error_types"]:
            active_filters.append(("Error Type", err_type))

    if filters.get("difficulties"):
        for diff in filters["difficulties"]:
            active_filters.append(("Difficulty", diff))

    if filters.get("date_from") or filters.get("date_to"):
        d_from = filters.get("date_from")
        d_to = filters.get("date_to")
        label = ""
        if d_from and d_to:
            label = f"{d_from.strftime('%d/%m')} - {d_to.strftime('%d/%m')}"
        elif d_from:
            label = f"From {d_from.strftime('%d/%m')}"
        elif d_to:
            label = f"Until {d_to.strftime('%d/%m')}"

        if label:
            active_filters.append(("Date", label))

    # Renderiza as tags visualmente
    if active_filters:
        st.markdown('<div style="margin: 10px 0;">', unsafe_allow_html=True)
        html = '<div style="display: flex; flex-wrap: wrap; gap: 8px;">'
        for cat, val in active_filters:
            html += f'<span style="background: #e0e7ff; color: #3730a3; padding: 4px 8px; border-radius: 4px; font-size: 0.85rem;"><b>{cat}:</b> {val}</span>'
        html += "</div></div>"
        st.markdown(html, unsafe_allow_html=True)


def apply_filters(
    data: List[Dict[str, Any]], filters: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Apply multiple filters to the dataset using AND logic.

    Args:
        data: List of error records.
        filters: Dictionary with filter criteria.

    Returns:
        Filtered list of error records.
    """
    filtered_data = data

    # Filter by subjects
    if filters.get("subjects"):
        filtered_data = [
            record
            for record in filtered_data
            if record.get("subject") in filters["subjects"]
        ]

    # Filter by exam types
    if filters.get("exam_types"):
        filtered_data = [
            record
            for record in filtered_data
            if record.get("exam_type") in filters["exam_types"]
        ]

    # Filter by topics
    if filters.get("topics"):
        filtered_data = [
            record
            for record in filtered_data
            if record.get("topic") in filters["topics"]
        ]

    # Filter by error types
    if filters.get("error_types"):
        filtered_data = [
            record
            for record in filtered_data
            if record.get("type") in filters["error_types"]
        ]

    # Filter by difficulties
    if filters.get("difficulties"):
        filtered_data = [
            record
            for record in filtered_data
            if record.get("difficulty") in filters["difficulties"]
        ]

    # Filter by date range
    date_from = filters.get("date_from")
    date_to = filters.get("date_to")

    if date_from or date_to:

        def parse_date(date_str: str) -> Optional[date]:
            """Parse date string in DD-MM-YYYY format."""
            try:
                return datetime.strptime(date_str, "%d-%m-%Y").date()
            except (ValueError, TypeError):
                return None

        filtered_data_temp = []
        for record in filtered_data:
            record_date = parse_date(record.get("date", ""))
            if record_date:
                if date_from and record_date < date_from:
                    continue
                if date_to and record_date > date_to:
                    continue
                filtered_data_temp.append(record)
        filtered_data = filtered_data_temp

    return filtered_data


def render_editable_table(data: List[Dict[str, Any]]) -> Optional[pd.DataFrame]:
    """
    Render a beautiful, Notion-like editable data table.

    Args:
        data: List of error records to display.

    Returns:
        Edited DataFrame if changes were made, None otherwise.
    """
    if not data:
        st.info("No records found. Try adjusting your filters or log some errors!")
        return None

    # Convert to DataFrame for editing
    df = pd.DataFrame(data)

    # Ensure difficulty column exists (backward compatibility)
    if "difficulty" not in df.columns:
        df["difficulty"] = "Medium"

    if "exam_type" not in df.columns:
        df["exam_type"] = "General"

    # Reorder columns for better UX
    column_order = [
        "id",
        "exam_type",
        "subject",
        "topic",
        "type",
        "difficulty",
        "description",
        "date",
    ]
    # Only use columns that exist in the DataFrame
    column_order = [col for col in column_order if col in df.columns]
    df = df[column_order]

    # Rename columns for display
    rename_map = {
        "id": "ID",
        "exam_type": "Exam Type",
        "subject": "Subject",
        "topic": "Topic",
        "type": "Error Type",
        "difficulty": "Difficulty",
        "description": "Description",
        "date": "Date",
    }
    # Only rename columns that exist
    df = df.rename(columns=rename_map)

    # Add delete checkbox column
    df["Delete"] = False

    # Configure column settings
    column_config = {
        "ID": st.column_config.TextColumn(
            "ID",
            width="small",
            disabled=True,
        ),
        "Subject": st.column_config.TextColumn(
            "Subject",
            width="medium",
            required=True,
        ),
        "Topic": st.column_config.TextColumn(
            "Topic",
            width="medium",
            required=True,
        ),
        "Error Type": st.column_config.SelectboxColumn(
            "Error Type",
            width="medium",
            options=ERROR_TYPES,
            required=True,
        ),
        "Difficulty": st.column_config.SelectboxColumn(
            "Difficulty",
            width="small",
            options=DIFFICULTY_LEVELS,
            required=True,
        ),
        "Description": st.column_config.TextColumn(
            "Description",
            width="large",
        ),
        "Date": st.column_config.TextColumn(
            "Date",
            width="medium",
            help="Format: DD-MM-YYYY",
        ),
        "Delete": st.column_config.CheckboxColumn(
            "Delete",
            width="small",
            default=False,
        ),
    }

    # Render editable data table
    st.markdown('<div class="data-table-container">', unsafe_allow_html=True)

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        column_order=[
            "Subject",
            "Topic",
            "Error Type",
            "Difficulty",
            "Description",
            "Date",
            "Delete",
        ],
        width="stretch",
        num_rows="fixed",
        hide_index=True,
        key="history_data_editor",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    return edited_df


def render_editable_sessions_table(
    data: List[Dict[str, Any]],
) -> Optional[pd.DataFrame]:
    """
    Render an editable data table for study sessions with calculated metrics.

    Args:
        data: List of study session records to display.

    Returns:
        Edited DataFrame if changes were made, None otherwise.
    """
    if not data:
        st.info("No study sessions found. Log some sessions to see them here!")
        return None

    # Convert to DataFrame for editing
    df = pd.DataFrame(data)

    # Handle different column name variations from DB
    # Map database column names to standard names
    column_mapping = {
        "total_questions": "questions_total",
        "correct_count": "questions_correct",
        "accuracy_percentage": "success_rate",
        "pace_per_question": "avg_time_per_question",
        "duration_minutes": "time_spent_min",
    }

    for db_col, standard_col in column_mapping.items():
        if db_col in df.columns and standard_col not in df.columns:
            df[standard_col] = df[db_col]

    # Ensure columns exist
    if "questions_total" not in df.columns and "total_questions" in df.columns:
        df["questions_total"] = df["total_questions"]
    if "questions_correct" not in df.columns and "correct_count" in df.columns:
        df["questions_correct"] = df["correct_count"]
    if "success_rate" not in df.columns and "accuracy_percentage" in df.columns:
        df["success_rate"] = df["accuracy_percentage"]
    if "avg_time_per_question" not in df.columns and "pace_per_question" in df.columns:
        df["avg_time_per_question"] = df["pace_per_question"]
    if "time_spent_min" not in df.columns and "duration_minutes" in df.columns:
        df["time_spent_min"] = df["duration_minutes"]

    # Calculate metrics if not already present
    if "success_rate" not in df.columns:
        df["success_rate"] = (
            (df["questions_correct"] / df["questions_total"] * 100).fillna(0).round(1)
        )
    if "avg_time_per_question" not in df.columns:
        df["avg_time_per_question"] = (
            (df["time_spent_min"] / df["questions_total"]).fillna(0).round(2)
        )

    # Reorder columns for better UX (ID hidden by default)
    column_order = [
        "id",
        "exam_type",
        "subject",
        "topics_covered",
        "questions_total",
        "questions_correct",
        "success_rate",
        "time_spent_min",
        "avg_time_per_question",
        "date",
    ]
    # Only use columns that exist in the DataFrame
    column_order = [col for col in column_order if col in df.columns]
    df = df[column_order]

    # Rename columns for display
    display_names = {
        "id": "ID",
        "exam_type": "Exam Type",
        "subject": "Subject",
        "topics_covered": "Topics Covered",
        "questions_total": "Total Questions",
        "questions_correct": "Correct",
        "success_rate": "Success Rate (%)",
        "time_spent_min": "Time (min)",
        "avg_time_per_question": "Avg Time/Q (min)",
        "date": "Date",
    }
    df.columns = [display_names.get(col, col) for col in df.columns]

    # Configure column settings
    column_config = {
        "ID": st.column_config.TextColumn(
            "ID",
            width="small",
            disabled=True,
        ),
        "Exam Type": st.column_config.TextColumn(
            "Exam Type",
            width="medium",
            required=True,
        ),
        "Subject": st.column_config.TextColumn(
            "Subject",
            width="medium",
            required=True,
        ),
        "Topics Covered": st.column_config.TextColumn(
            "Topics Covered",
            width="large",
        ),
        "Total Questions": st.column_config.NumberColumn(
            "Total Questions",
            width="small",
            min_value=0,
            required=True,
        ),
        "Correct": st.column_config.NumberColumn(
            "Correct",
            width="small",
            min_value=0,
        ),
        "Success Rate (%)": st.column_config.NumberColumn(
            "Success Rate (%)",
            width="small",
            format="%.1f%%",
            disabled=True,
        ),
        "Time (min)": st.column_config.NumberColumn(
            "Time (min)",
            width="small",
            min_value=0,
        ),
        "Avg Time/Q (min)": st.column_config.NumberColumn(
            "Avg Time/Q (min)",
            width="small",
            format="%.2f",
            disabled=True,
        ),
        "Date": st.column_config.TextColumn(
            "Date",
            width="medium",
            help="Format: DD-MM-YYYY",
        ),
    }

    # Add delete checkbox column
    df["Delete"] = False

    # Render editable data table
    st.markdown('<div class="data-table-container">', unsafe_allow_html=True)

    column_config["Delete"] = st.column_config.CheckboxColumn(
        "Delete",
        width="small",
        default=False,
    )

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        column_order=[
            "Exam Type",
            "Subject",
            "Topics Covered",
            "Total Questions",
            "Correct",
            "Success Rate (%)",
            "Time (min)",
            "Avg Time/Q (min)",
            "Date",
            "Delete",
        ],
        width="stretch",
        num_rows="fixed",
        hide_index=True,
        key="sessions_data_editor",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    return edited_df
