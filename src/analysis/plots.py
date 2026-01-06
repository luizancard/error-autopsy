from datetime import datetime

import altair as alt
import pandas as pd

primary_color = "#4e4a5aff"


def chart_subjects(subject_data):
    if subject_data is None or not subject_data:
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
        .mark_bar(color=primary_color)
        .encode(
            x=alt.X("Subject:N", title=None),
            y=alt.Y("Errors:Q", title=None),
            opacity=alt.condition(select_subject, alt.value(1), alt.value(0.3)),
        )
        .add_params(select_subject)
        .properties(height=320)
        .configure_view(strokeOpacity=0)
        .configure_axis(labelColor="#0f172a", gridColor="#e2e8f0")
    )
    return chart


def chart_topics(topic_data):
    if topic_data is None:
        return None
    sorted_topics = sorted(topic_data.items(), key=lambda x: x[1], reverse=True)[:10]
    df = pd.DataFrame(sorted_topics, columns=["Topic", "Errors"])

    chart = (
        alt.Chart(df)
        .mark_bar(color=primary_color)
        .encode(
            x=alt.X("Topic:N", title=None, sort="-y"),
            y=alt.Y("Errors:Q", title=None),
            tooltip=["Topic", "Errors"],
        )
        .properties(height=320)
        .configure_view(strokeOpacity=0)
        .configure_axis(labelColor="#0f172a", gridColor="#e2e8f0")
    )
    return chart


def chart_timeline(month_data):
    if not month_data:
        return None

    sorted_months = sorted(
        month_data.items(),
        key=lambda x: datetime.strptime(x[0], "%b %Y"),
    )
    df = pd.DataFrame(sorted_months, columns=["Month", "Errors"])

    chart = (
        alt.Chart(df)
        .mark_bar(color=primary_color)
        .encode(
            x=alt.X("Month:N", title=None, sort=None),
            y=alt.Y("Errors:Q", title=None),
        )
        .properties(height=320)
        .configure_view(strokeOpacity=0)
        .configure_axis(labelColor="#0f172a", gridColor="#e2e8f0")
    )
    return chart


def chart_error_types_pie(type_data):
    if type_data is None or not type_data:
        return None

    df_pie = pd.DataFrame(list(type_data.items()), columns=["Type", "Count"])
    custom_colors = ["#242038", "#725AC1", "#8070C5", "#8D86C9", "#CAC4CE", "#F7ECE1"]

    base = alt.Chart(df_pie).encode(theta=alt.Theta("Count", stack=True))

    pie = base.mark_arc(outerRadius=120, innerRadius=0).encode(
        color=alt.Color(
            "Type",
            scale=alt.Scale(range=custom_colors),
            legend=alt.Legend(title="Error Type"),
        ),
        order=alt.Order("Count", sort="descending"),
        tooltip=["Type", "Count"],
    )

    text = base.mark_text(radius=140).encode(
        text=alt.Text("Count"),
        order=alt.Order("Count", sort="descending"),
        color=alt.value("#0f172a"),
    )

    return (pie + text).properties(height=350)
