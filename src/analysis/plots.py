"""
Chart generation functions for error analysis visualization.

Uses Altair for creating interactive charts with consistent theming.
"""

from datetime import datetime
from typing import Dict, Optional, Union

import altair as alt
import pandas as pd

from config import ChartConfig, Colors


def _configure_chart_style(chart: alt.Chart) -> alt.Chart:
    """
    Apply consistent styling to an Altair chart.

    Args:
        chart: The Altair chart to style.

    Returns:
        Styled chart with configured axes and view.
    """
    return chart.configure_view(strokeOpacity=0).configure_axis(
        labelColor=Colors.AXIS_LABEL, gridColor=Colors.AXIS_GRID
    )


def chart_subjects(subject_data: Optional[Dict[str, int]]) -> Optional[alt.Chart]:
    """
    Create a bar chart showing error distribution by subject.

    Args:
        subject_data: Dictionary mapping subject names to error counts.

    Returns:
        Altair chart object or None if no data.
    """
    if not subject_data:
        return None

    df = pd.DataFrame(
        list(subject_data.items()),
        columns=["Subject", "Errors"],
    ).sort_values("Errors", ascending=False)

    select_subject = alt.selection_point(
        name="selected_subjects", fields=["Subject"], on="click"
    )

    chart = (
        alt.Chart(df)
        .mark_bar(color=Colors.PRIMARY)
        .encode(
            x=alt.X("Subject:N", title=None),
            y=alt.Y("Errors:Q", title=None),
            opacity=alt.condition(select_subject, alt.value(1), alt.value(0.3)),
        )
        .add_params(select_subject)
        .properties(height=ChartConfig.HEIGHT_DEFAULT)
    )
    return _configure_chart_style(chart)


def chart_topics(topic_data: Optional[Dict[str, int]]) -> Optional[alt.Chart]:
    """
    Create a bar chart showing error distribution by topic.

    Args:
        topic_data: Dictionary mapping topic names to error counts.

    Returns:
        Altair chart object or None if no data.
    """
    if not topic_data:
        return None

    sorted_topics = sorted(topic_data.items(), key=lambda x: x[1], reverse=True)[
        : ChartConfig.TOP_TOPICS_LIMIT
    ]
    df = pd.DataFrame(sorted_topics, columns=["Topic", "Errors"])

    chart = (
        alt.Chart(df)
        .mark_bar(color=Colors.PRIMARY)
        .encode(
            x=alt.X("Topic:N", title=None, sort="-y"),
            y=alt.Y("Errors:Q", title=None),
            tooltip=["Topic", "Errors"],
        )
        .properties(height=ChartConfig.HEIGHT_DEFAULT)
    )
    return _configure_chart_style(chart)


def chart_timeline(month_data: Optional[Dict[str, int]]) -> Optional[alt.Chart]:
    """
    Create a bar chart showing error trends over time.

    Args:
        month_data: Dictionary mapping month labels to error counts.

    Returns:
        Altair chart object or None if no data.
    """
    if not month_data:
        return None

    sorted_months = sorted(
        month_data.items(),
        key=lambda x: datetime.strptime(x[0], "%b %Y"),
    )
    df = pd.DataFrame(sorted_months, columns=["Month", "Errors"])

    chart = (
        alt.Chart(df)
        .mark_bar(color=Colors.PRIMARY)
        .encode(
            x=alt.X("Month:N", title=None, sort=None),
            y=alt.Y("Errors:Q", title=None),
        )
        .properties(height=ChartConfig.HEIGHT_DEFAULT)
    )
    return _configure_chart_style(chart)


def chart_error_types_pie(
    type_data: Optional[Dict[str, int]],
) -> Optional[Union[alt.Chart, alt.LayerChart]]:
    """
    Create a pie chart showing error distribution by type.

    Args:
        type_data: Dictionary mapping error types to counts.

    Returns:
        Altair chart or LayerChart object, or None if no data.
    """
    if not type_data:
        return None

    df_pie = pd.DataFrame(list(type_data.items()), columns=["Type", "Count"])

    base = alt.Chart(df_pie).encode(theta=alt.Theta("Count", stack=True))

    pie = base.mark_arc(outerRadius=120, innerRadius=0).encode(
        color=alt.Color(
            "Type",
            scale=alt.Scale(range=Colors.CHART_PALETTE),
            legend=alt.Legend(title="Error Type"),
        ),
        order=alt.Order("Count", sort="descending"),
        tooltip=["Type", "Count"],
    )

    text = base.mark_text(radius=140).encode(
        text=alt.Text("Count"),
        order=alt.Order("Count", sort="descending"),
        color=alt.value(Colors.AXIS_LABEL),
    )

    return (pie + text).properties(height=ChartConfig.HEIGHT_LARGE)


def chart_difficulties(
    difficulty_data: Optional[Dict[str, int]],
) -> Optional[alt.Chart]:
    """
    Create a horizontal bar chart showing error distribution by difficulty level.

    Args:
        difficulty_data: Dictionary mapping difficulty levels to counts.

    Returns:
        Altair chart object or None if no data.
    """
    if not difficulty_data:
        return None

    # Define order for difficulties (Easy -> Medium -> Hard)
    difficulty_order = ["Easy", "Medium", "Hard"]

    # Create DataFrame with ordered difficulties
    df = pd.DataFrame(
        list(difficulty_data.items()),
        columns=["Difficulty", "Count"],
    )

    # Color mapping for difficulty levels
    color_scale = alt.Scale(
        domain=["Easy", "Medium", "Hard"],
        range=["#10b981", "#f59e0b", "#ef4444"],  # Green, Amber, Red
    )

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            y=alt.Y(
                "Difficulty:N",
                title=None,
                sort=difficulty_order,
            ),
            x=alt.X("Count:Q", title=None),
            color=alt.Color(
                "Difficulty:N",
                scale=color_scale,
                legend=None,
            ),
            tooltip=["Difficulty", "Count"],
        )
        .properties(height=180)
    )
    return _configure_chart_style(chart)
