"""
Chart generation functions for exam telemetry visualization.

Uses Altair for creating interactive charts with consistent theming.
Includes advanced visualizations for speed/accuracy analysis and performance tracking.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

import altair as alt
import pandas as pd

from config import ChartConfig, Colors, get_pace_benchmark


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


def _get_color_for_category(index: int) -> str:
    """
    Get a color from the palette for a category.

    Args:
        index: Category index

    Returns:
        Color hex string from the palette
    """
    return Colors.CHART_PALETTE[index % len(Colors.CHART_PALETTE)]


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
        .mark_bar()
        .encode(
            x=alt.X("Subject:N", title=None),
            y=alt.Y("Errors:Q", title=None),
            color=alt.Color(
                "Subject:N", scale=alt.Scale(scheme="purples"), legend=None
            ),
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
        .mark_bar()
        .encode(
            x=alt.X("Month:N", title=None, sort=None),
            y=alt.Y("Errors:Q", title=None),
            color=alt.Color("Month:N", scale=alt.Scale(scheme="purples"), legend=None),
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

    # Use chart palette colors for consistency
    color_scale = alt.Scale(
        domain=["Easy", "Medium", "Hard"],
        range=Colors.CHART_PALETTE[:3],  # Use first 3 colors from palette
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


# =============================================================================
# EXAM TELEMETRY VISUALIZATIONS
# =============================================================================


def chart_speed_vs_accuracy(scatter_data: List[Dict[str, Any]]) -> Optional[alt.Chart]:
    """
    Create a scatter plot showing the relationship between pace and accuracy.

    This chart helps identify performance zones:
    - Mastery Zone: Optimal pace with high accuracy
    - Rushing Zone: Fast but low accuracy
    - Slow Zone: Accurate but too slow

    Args:
        scatter_data: List of dicts with pace, accuracy, subject, exam_type

    Returns:
        Interactive Altair scatter chart or None if no data
    """
    if not scatter_data:
        return None

    df = pd.DataFrame(scatter_data)

    # Compute exam-specific benchmark for each row
    df["benchmark"] = df["exam_type"].apply(get_pace_benchmark)

    # Create performance zone classification using dynamic benchmarks
    def classify_zone(row: pd.Series) -> str:
        bm = row["benchmark"]
        if row["accuracy"] >= 80 and row["pace"] <= bm * 1.2:
            return "Mastery Zone"
        if row["pace"] < bm * 0.5:
            return "Rushing"
        if row["pace"] > bm * 1.2:
            return "Slow"
        return "Developing"

    df["zone"] = df.apply(classify_zone, axis=1)

    # Use the median benchmark for the reference line
    median_benchmark = float(df["benchmark"].median())

    # Color coding for zones
    zone_colors = alt.Scale(
        domain=["Mastery Zone", "Developing", "Rushing", "Slow"],
        range=["#10b981", "#3b82f6", "#f59e0b", "#6b7280"],
    )

    # Selection for interaction
    brush = alt.selection_point(encodings=["color"], on="click")

    chart = (
        alt.Chart(df)
        .mark_circle(size=100, opacity=0.7)
        .encode(
            x=alt.X(
                "pace:Q",
                title="Minutes Per Question (MPQ)",
                scale=alt.Scale(zero=False),
            ),
            y=alt.Y("accuracy:Q", title="Accuracy %", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color(
                "zone:N", scale=zone_colors, legend=alt.Legend(title="Performance Zone")
            ),
            opacity=alt.condition(brush, alt.value(1), alt.value(0.3)),
            tooltip=[
                alt.Tooltip("subject:N", title="Subject"),
                alt.Tooltip("exam_type:N", title="Exam"),
                alt.Tooltip("pace:Q", title="Pace (min/q)", format=".2f"),
                alt.Tooltip("accuracy:Q", title="Accuracy", format=".1f"),
                alt.Tooltip("total_questions:Q", title="Questions"),
                alt.Tooltip("date:N", title="Date"),
            ],
        )
        .add_params(brush)
        .properties(height=400, title="Speed vs Accuracy Analysis")
    )

    # Add reference lines for ideal zones
    benchmark_line = (
        alt.Chart(pd.DataFrame({"pace": [median_benchmark]}))
        .mark_rule(color="#ef4444", strokeDash=[5, 5], opacity=0.5)
        .encode(x="pace:Q")
    )

    accuracy_line = (
        alt.Chart(pd.DataFrame({"accuracy": [80.0]}))
        .mark_rule(color="#10b981", strokeDash=[5, 5], opacity=0.5)
        .encode(y="accuracy:Q")
    )

    final_chart = chart + benchmark_line + accuracy_line
    return _configure_chart_style(final_chart)


def chart_mock_exam_trajectory(
    trajectory_data: List[Dict[str, Any]],
) -> Optional[alt.Chart]:
    """
    Create a line chart showing mock exam score evolution over time.

    Args:
        trajectory_data: List of dicts with exam_type, date, percentage, attempt_number

    Returns:
        Line chart with trend indicators or None if no data
    """
    if not trajectory_data:
        return None

    df = pd.DataFrame(trajectory_data)

    # Sort by date for proper line plotting
    df["date_parsed"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df = df.sort_values("date_parsed")

    # Color by exam type — use theme palette
    unique_types = list(df["exam_type"].unique())
    exam_colors = alt.Scale(
        domain=unique_types,
        range=Colors.CHART_PALETTE[: len(unique_types)],
    )

    # Line chart
    line = (
        alt.Chart(df)
        .mark_line(point=alt.OverlayMarkDef(size=100, filled=True), strokeWidth=3)
        .encode(
            x=alt.X("date_parsed:T", title="Date"),
            y=alt.Y("percentage:Q", title="Score %", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color(
                "exam_type:N", scale=exam_colors, legend=alt.Legend(title="Exam Type")
            ),
            tooltip=[
                alt.Tooltip("exam_name:N", title="Exam"),
                alt.Tooltip("exam_type:N", title="Type"),
                alt.Tooltip("date:N", title="Date"),
                alt.Tooltip("percentage:Q", title="Score %", format=".1f"),
                alt.Tooltip("score:Q", title="Raw Score", format=".1f"),
                alt.Tooltip("attempt_number:Q", title="Attempt #"),
            ],
        )
        .properties(height=350, title="Mock Exam Score Trajectory")
    )

    # Add target line at 80%
    target_line = (
        alt.Chart(pd.DataFrame({"target": [80.0]}))
        .mark_rule(color="#10b981", strokeDash=[8, 4], opacity=0.6, size=2)
        .encode(y="target:Q")
    )

    final_chart = line + target_line
    return _configure_chart_style(final_chart)


def chart_scaled_score_trajectory(
    trajectory_data: List[Dict[str, Any]],
    score_label: str = "Score",
    target_score: Optional[float] = None,
    max_score: float = 1000,
) -> Optional[alt.Chart]:
    """
    Create a line chart for TRI (ENEM) or scaled (SAT) score trajectory.

    Args:
        trajectory_data: List of dicts with date, score, exam_name, attempt_number
        score_label: Label for the Y axis (e.g., "TRI Score", "Scaled Score")
        target_score: Optional target line value
        max_score: Maximum possible score for Y-axis domain

    Returns:
        Line chart or None if no data
    """
    if not trajectory_data:
        return None

    df = pd.DataFrame(trajectory_data)
    df["date_parsed"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df = df.sort_values("date_parsed")

    line = (
        alt.Chart(df)
        .mark_line(
            point=alt.OverlayMarkDef(size=100, filled=True),
            strokeWidth=3,
            color=Colors.CHART_PALETTE[0],
        )
        .encode(
            x=alt.X("date_parsed:T", title="Date"),
            y=alt.Y(
                "score:Q",
                title=score_label,
                scale=alt.Scale(domain=[0, max_score]),
            ),
            tooltip=[
                alt.Tooltip("exam_name:N", title="Exam"),
                alt.Tooltip("date:N", title="Date"),
                alt.Tooltip("score:Q", title=score_label, format=".0f"),
                alt.Tooltip("attempt_number:Q", title="Attempt #"),
            ],
        )
        .properties(height=300, title=f"{score_label} Trajectory")
    )

    if target_score:
        target_line = (
            alt.Chart(pd.DataFrame({"target": [target_score]}))
            .mark_rule(color="#10b981", strokeDash=[8, 4], opacity=0.6, size=2)
            .encode(y="target:Q")
        )
        final_chart = line + target_line
    else:
        final_chart = line

    return _configure_chart_style(final_chart)


def chart_activity_heatmap(heatmap_data: List[Dict[str, Any]]) -> Optional[alt.Chart]:
    """
    Create a GitHub-style contribution heatmap showing study volume over time.

    Args:
        heatmap_data: List of dicts with date_key, intensity, questions_answered

    Returns:
        Heatmap visualization or None if no data
    """
    if not heatmap_data:
        return None

    df = pd.DataFrame(heatmap_data)

    # Parse dates for week/day extraction
    df["date_parsed"] = pd.to_datetime(df["date_key"], format="%Y-%m-%d")
    # Use continuous week offset from earliest date to handle year boundaries
    min_date = df["date_parsed"].min()
    df["week"] = (df["date_parsed"] - min_date).dt.days // 7
    df["day_of_week"] = df["date_parsed"].dt.dayofweek  # 0=Monday, 6=Sunday
    df["month_label"] = df["date_parsed"].dt.strftime("%b %Y")

    # Intensity color scale (purple tones matching dashboard theme)
    intensity_colors = alt.Scale(
        domain=[0, 1, 2, 3, 4],
        range=["#F7ECE1", "#CAC4CE", "#8D86C9", "#8070C5", "#725AC1"],
    )

    chart = (
        alt.Chart(df)
        .mark_rect(stroke="white", strokeWidth=2)
        .encode(
            x=alt.X("week:O", title="", axis=alt.Axis(labels=False, ticks=False)),
            y=alt.Y(
                "day_of_week:O",
                title="Day",
                axis=alt.Axis(
                    labelExpr="['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'][datum.value]"
                ),
            ),
            color=alt.Color(
                "intensity:O",
                scale=intensity_colors,
                legend=alt.Legend(
                    title="Activity Level",
                    labelExpr="['None', 'Low', 'Medium', 'High', 'Very High'][datum.value]",
                ),
            ),
            tooltip=[
                alt.Tooltip("date:N", title="Date"),
                alt.Tooltip("questions_answered:Q", title="Questions Answered"),
                alt.Tooltip("errors_logged:Q", title="Errors Logged"),
                alt.Tooltip("study_time:Q", title="Study Time (min)", format=".0f"),
            ],
        )
        .properties(height=200, title="Study Activity Heatmap (Last 6 Months)")
    )

    return _configure_chart_style(chart)


def chart_session_summary(sessions: List[Dict[str, Any]]) -> Optional[alt.Chart]:
    """
    Create a multi-bar chart showing session counts by subject with accuracy overlay.

    Args:
        sessions: List of session records

    Returns:
        Grouped bar chart or None if no data
    """
    if not sessions:
        return None

    # Aggregate by subject
    subject_stats: Dict[str, Dict[str, float]] = {}

    for s in sessions:
        subj = s.get("subject", "Unknown")
        if subj not in subject_stats:
            subject_stats[subj] = {"total_questions": 0, "correct": 0, "sessions": 0}

        subject_stats[subj]["total_questions"] += s.get("total_questions", 0)
        subject_stats[subj]["correct"] += s.get("correct_count", 0)
        subject_stats[subj]["sessions"] += 1

    # Calculate accuracy
    data = []
    for subj, stats in subject_stats.items():
        accuracy = (
            (stats["correct"] / stats["total_questions"] * 100)
            if stats["total_questions"] > 0
            else 0
        )
        data.append(
            {
                "subject": subj,
                "sessions": stats["sessions"],
                "accuracy": round(accuracy, 1),
                "questions": stats["total_questions"],
            }
        )

    df = pd.DataFrame(data).sort_values("sessions", ascending=False)

    # Bar chart for session count
    bars = (
        alt.Chart(df)
        .mark_bar(color=Colors.PRIMARY, opacity=0.7)
        .encode(
            x=alt.X("subject:N", title="Subject", sort="-y"),
            y=alt.Y("sessions:Q", title="Number of Sessions"),
            tooltip=[
                alt.Tooltip("subject:N", title="Subject"),
                alt.Tooltip("sessions:Q", title="Sessions"),
                alt.Tooltip("questions:Q", title="Total Questions"),
                alt.Tooltip("accuracy:Q", title="Accuracy %", format=".1f"),
            ],
        )
    )

    # Line overlay for accuracy
    line = (
        alt.Chart(df)
        .mark_line(
            point=alt.OverlayMarkDef(filled=True, size=80),
            color="#ef4444",
            strokeWidth=2,
        )
        .encode(
            x=alt.X("subject:N", sort="-y"),
            y=alt.Y("accuracy:Q", title="Accuracy %", scale=alt.Scale(domain=[0, 100])),
        )
    )

    chart = (
        alt.layer(bars, line)
        .resolve_scale(y="independent")
        .properties(height=300, title="Session Volume & Accuracy by Subject")
    )

    return _configure_chart_style(chart)


# =============================================================================
# MOCK EXAM SECTION CHARTS
# =============================================================================


def chart_section_comparison(
    section_data: List[Dict[str, Any]],
) -> Optional[alt.Chart]:
    """
    Create a grouped bar chart comparing section scores for the latest exam(s).

    Args:
        section_data: List of dicts with section, percentage, exam_name

    Returns:
        Grouped bar chart or None if no data
    """
    if not section_data:
        return None

    df = pd.DataFrame(section_data)

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("section:N", title="Section"),
            y=alt.Y("percentage:Q", title="Score %", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color(
                "exam_name:N",
                scale=alt.Scale(range=Colors.CHART_PALETTE),
                legend=alt.Legend(title="Exam"),
            ),
            xOffset="exam_name:N",
            tooltip=[
                alt.Tooltip("exam_name:N", title="Exam"),
                alt.Tooltip("section:N", title="Section"),
                alt.Tooltip("score:Q", title="Score"),
                alt.Tooltip("max:Q", title="Max"),
                alt.Tooltip("percentage:Q", title="%", format=".1f"),
            ],
        )
        .properties(height=320, title="Section Score Comparison")
    )

    return _configure_chart_style(chart)


def chart_section_trends(
    trend_data: List[Dict[str, Any]],
) -> Optional[alt.Chart]:
    """
    Create a multi-line chart showing section scores over time.

    Args:
        trend_data: List of dicts with section, percentage, date

    Returns:
        Multi-line trend chart or None if no data
    """
    if not trend_data:
        return None

    df = pd.DataFrame(trend_data)

    # Parse dates
    df["date_parsed"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df = df.dropna(subset=["date_parsed"])

    if df.empty:
        return None

    df = df.sort_values("date_parsed")

    chart = (
        alt.Chart(df)
        .mark_line(point=alt.OverlayMarkDef(size=80, filled=True), strokeWidth=2)
        .encode(
            x=alt.X("date_parsed:T", title="Date"),
            y=alt.Y("percentage:Q", title="Score %", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color(
                "section:N",
                scale=alt.Scale(range=Colors.CHART_PALETTE),
                legend=alt.Legend(title="Section"),
            ),
            tooltip=[
                alt.Tooltip("section:N", title="Section"),
                alt.Tooltip("date:N", title="Date"),
                alt.Tooltip("percentage:Q", title="Score %", format=".1f"),
                alt.Tooltip("exam_name:N", title="Exam"),
            ],
        )
        .properties(height=320, title="Section Progress Over Time")
    )

    return _configure_chart_style(chart)


def chart_daily_questions(sessions: List[Dict[str, Any]]) -> Optional[alt.Chart]:
    """
    Create a bar chart showing total questions answered per day.

    Args:
        sessions: List of study session records

    Returns:
        Altair chart or None if no data
    """
    if not sessions:
        return None

    # Aggregate questions by date
    daily_stats: Dict[str, int] = {}
    for session in sessions:
        date_str = session.get("date", "")
        if date_str:
            questions = session.get("total_questions", 0)
            daily_stats[date_str] = daily_stats.get(date_str, 0) + questions

    if not daily_stats:
        return None

    df = pd.DataFrame(
        sorted(daily_stats.items(), key=lambda x: datetime.strptime(x[0], "%d-%m-%Y")),
        columns=["Date", "Questions"],
    )

    # Convert to datetime for proper sorting
    df["date_parsed"] = pd.to_datetime(df["Date"], format="%d-%m-%Y")
    df = df.sort_values("date_parsed")

    chart = (
        alt.Chart(df)
        .mark_bar(color=Colors.PRIMARY_LIGHT)
        .encode(
            x=alt.X("date_parsed:T", title=None),
            y=alt.Y("Questions:Q", title="Questions Answered"),
            tooltip=["Date:N", "Questions:Q"],
        )
        .properties(height=200)
    )

    return _configure_chart_style(chart)


def chart_exam_type_distribution(type_data: Dict[str, int]) -> Optional[alt.Chart]:
    """
    Create a bar chart showing error distribution by exam type.

    Args:
        type_data: Dictionary mapping exam type to error count

    Returns:
        Altair chart or None if no data
    """
    if not type_data:
        return None

    # Convert dict to DataFrame
    df = pd.DataFrame(list(type_data.items()), columns=["Exam Type", "Count"])

    # Sort by count descending
    df = df.sort_values("Count", ascending=False)

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("Exam Type:N", title=None, sort="-y"),
            y=alt.Y("Count:Q", title="Errors"),
            color=alt.Color(
                "Exam Type:N", scale=alt.Scale(range=Colors.CHART_PALETTE), legend=None
            ),
            tooltip=["Exam Type:N", "Count:Q"],
        )
        .properties(height=250, title="Errors by Exam Type")
    )

    return _configure_chart_style(chart)


def chart_pace_by_subject(pace_data: List[Dict[str, Any]]) -> Optional[alt.Chart]:
    """
    Create a bar chart showing average pace (minutes/question) by subject.

    Args:
        pace_data: List of dicts with subject and pace

    Returns:
        Altair chart or None if no data
    """
    if not pace_data:
        return None

    df = pd.DataFrame(pace_data)

    chart = (
        alt.Chart(df)
        .mark_bar()
        .encode(
            x=alt.X("subject:N", title=None, sort="-y"),
            y=alt.Y("pace:Q", title="Minutes per Question"),
            color=alt.Color(
                "subject:N", scale=alt.Scale(range=Colors.CHART_PALETTE), legend=None
            ),
            tooltip=[
                alt.Tooltip("subject:N", title="Subject"),
                alt.Tooltip("pace:Q", title="Min/Question", format=".2f"),
            ],
        )
        .properties(height=250, title="Avg Time per Question")
    )

    return _configure_chart_style(chart)
