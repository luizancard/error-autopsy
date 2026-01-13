"""
History page UI components for Error Autopsy.

Provides filter popup, editable table, and filter logic for database management.
"""

from datetime import date, datetime
from typing import Any, Dict, List, Optional, Set

import pandas as pd

import streamlit as st
from config import ERROR_TYPES


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

    for record in data:
        subject = record.get("subject", "").strip()
        topic = record.get("topic", "").strip()
        if subject:
            subjects.add(subject)
        if topic:
            topics.add(topic)

    return {"subjects": sorted(list(subjects)), "topics": sorted(list(topics))}


def render_filter_popup(all_data: List[Dict[str, Any]]) -> None:
    # Initialize filter state if not exists
    if "history_filters" not in st.session_state:
        st.session_state.history_filters = {
            "subjects": [],
            "topics": [],
            "error_types": [],
            "date_from": None,
            "date_to": None,
        }

    # Get unique values from current data
    unique_vals = get_unique_values(all_data)

    with st.popover("Filter", use_container_width=False):
        st.markdown("### Filter Options")
        st.markdown("Select multiple criteria to filter your data.")

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
            if st.button("Apply Filters", use_container_width=True, type="primary"):
                st.session_state.history_filters = {
                    "subjects": selected_subjects,
                    "topics": selected_topics,
                    "error_types": selected_types,
                    "date_from": date_from if date_from else None,
                    "date_to": date_to if date_to else None,
                }
                st.rerun()

        with col_clear:
            if st.button("Clear All", use_container_width=True):
                st.session_state.history_filters = {
                    "subjects": [],
                    "topics": [],
                    "error_types": [],
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

    # Collect active filters
    if filters.get("subjects"):
        for subj in filters["subjects"]:
            active_filters.append(("Subject", subj))

    if filters.get("topics"):
        for topic in filters["topics"]:
            active_filters.append(("Topic", topic))

    if filters.get("error_types"):
        for err_type in filters["error_types"]:
            active_filters.append(("Error Type", err_type))

    if filters.get("date_from") or filters.get("date_to"):
        date_from = filters.get("date_from")
        date_to = filters.get("date_to")
        date_str = ""
        if date_from and date_to:
            date_str = (
                f"{date_from.strftime('%d/%m/%Y')} - {date_to.strftime('%d/%m/%Y')}"
            )
        elif date_from:
            date_str = f"From {date_from.strftime('%d/%m/%Y')}"
        elif date_to:
            date_str = f"Until {date_to.strftime('%d/%m/%Y')}"
        if date_str:
            active_filters.append(("Date", date_str))

    # Render filter tags
    if active_filters:
        st.markdown(
            '<div style="margin-top: 1rem; margin-bottom: 1rem;">',
            unsafe_allow_html=True,
        )

        filter_html = '<div style="display: flex; flex-wrap: wrap; gap: 0.5rem;">'
        for label, value in active_filters:
            filter_html += f'<span class="filter-tag"><span class="filter-tag-label">{label}:</span> {value}</span>'
        filter_html += "</div>"

        st.markdown(filter_html, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)


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
        st.info("📭 No records found. Try adjusting your filters or log some errors!")
        return None

    # Convert to DataFrame for editing
    df = pd.DataFrame(data)

    # Reorder columns for better UX
    column_order = ["id", "subject", "topic", "type", "description", "date"]
    df = df[column_order]

    # Rename columns for display
    df.columns = ["ID", "Subject", "Topic", "Error Type", "Description", "Date"]

    # Configure column settings
    column_config = {
        "ID": st.column_config.TextColumn(
            "ID",
            width="small",
            disabled=True,  # ID should not be editable
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
        "Description": st.column_config.TextColumn(
            "Description",
            width="large",
        ),
        "Date": st.column_config.TextColumn(
            "Date",
            width="medium",
            help="Format: DD-MM-YYYY",
        ),
    }

    # Render editable data table
    st.markdown('<div class="data-table-container">', unsafe_allow_html=True)

    edited_df = st.data_editor(
        df,
        column_config=column_config,
        use_container_width=True,
        num_rows="fixed",  # Canvas rendering prevents background styling
        hide_index=True,
        key="history_data_editor",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    return edited_df
