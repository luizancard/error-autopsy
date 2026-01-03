import importlib
import sys
import time
from datetime import date, datetime
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from assets import styles

# Add src to path
src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.append(str(src_path))

from analysis import metrics as mt  # noqa: E402
from services import ai_service as ai  # noqa: E402
from services import db_service as db  # noqa: E402

importlib.reload(mt)

errors = db.load_data()
DEFAULT_ERROR_TYPE = "Content Gap"

st.session_state.setdefault("subject_input", "")
st.session_state.setdefault("topic_input", "")
st.session_state.setdefault("description_input", "")
st.session_state.setdefault("error_type_select", DEFAULT_ERROR_TYPE)
st.session_state.setdefault("error_type_select", DEFAULT_ERROR_TYPE)
st.session_state.setdefault("date_input", date.today())
st.session_state.setdefault("time_filter", "All Time")  # Default filter
st.session_state.setdefault("reset_form", False)
st.session_state.setdefault("success_message", "")
st.session_state.setdefault("show_success", False)

raw_menu = st.query_params.get("menu", "Dashboard")
menu_from_url = raw_menu[0] if isinstance(raw_menu, list) else raw_menu
st.session_state["current_menu"] = menu_from_url

st.set_page_config(page_title="Error Autopsy", layout="wide", page_icon="📝")

styles.local_css()


def parse_date_str(d: str):
    try:
        return datetime.strptime(d, "%d-%m-%Y")
    except Exception:
        return None


def current_and_last_month_refs(ref: date):
    first_this = ref.replace(day=1)
    last_month_last_day = first_this - date.resolution
    first_last = last_month_last_day.replace(day=1)
    return (first_this.year, first_this.month), (first_last.year, first_last.month)


def aggregate_monthly_stats(data):
    today = date.today()
    (cy, cm), (ly, lm) = current_and_last_month_refs(today)

    def month_key(dt_obj):
        return (dt_obj.year, dt_obj.month)

    current_errors = []
    last_errors = []

    for row in data:
        dt = parse_date_str(row.get("date", ""))
        if not dt:
            continue
        key = month_key(dt)
        if key == (cy, cm):
            current_errors.append(row)
        elif key == (ly, lm):
            last_errors.append(row)

    # Totals
    current_total = len(current_errors)
    last_total = len(last_errors)

    # Delta percentage
    if last_total == 0:
        delta = 100.0 if current_total > 0 else 0.0
    else:
        delta = ((current_total - last_total) / last_total) * 100

    # Subject with most errors this month
    subject_counts = {}
    for row in current_errors:
        subj = row.get("subject", "Unknown") or "Unknown"
        subject_counts[subj] = subject_counts.get(subj, 0) + 1
    top_subject = (
        max(subject_counts.items(), key=lambda x: x[1])[0] if subject_counts else "—"
    )

    # Primary reason (type) this month
    type_counts = {}
    for row in current_errors:
        t = row.get("type", "Other") or "Other"
        type_counts[t] = type_counts.get(t, 0) + 1
    top_type = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "—"

    return {
        "current_total": current_total,
        "delta": delta,
        "top_subject": top_subject,
        "top_type": top_type,
    }


def aggregate_by_topic(data):
    """Count errors by topic across all data."""
    topic_counts = {}
    for row in data:
        topic = row.get("topic", "Unknown") or "Unknown"
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    return topic_counts


def aggregate_by_subject(data):
    """Count errors by subject across all data."""
    subject_counts = {}
    for row in data:
        subj = row.get("subject", "Unknown") or "Unknown"
        subject_counts[subj] = subject_counts.get(subj, 0) + 1
    return subject_counts


def aggregate_by_month_all(data):
    """Count errors by month across all data."""
    month_counts = {}
    for row in data:
        dt = parse_date_str(row.get("date", ""))
        if dt:
            month_str = dt.strftime("%b %Y")  # e.g., "Dec 2025"
            month_counts[month_str] = month_counts.get(month_str, 0) + 1
    return month_counts


def generate_mini_insight(data):
    # enerate AI-powered insight based on last 2 months of error data.
    return ai.generate_web_insight(data)


# Custom sidebar with professional design
with st.sidebar:
    # Header with logo and title
    st.markdown(
        """
        <div class="sidebar-header-container">
            <div class="sidebar-logo-wrapper">
                <div class="sidebar-logo">
                    <svg viewBox="0 0 24 24" fill="white">
                        <path d="M12 2c.2 0 .4.1.5.3l2.3 4.7 5.2.8c.2 0 .4.2.4.4s-.1.4-.3.5l-3.8 3.7.9 5.2c0 .2-.1.4-.3.5-.2.1-.4.1-.6 0L12 15.2l-4.7 2.5c-.2.1-.4.1-.6 0-.2-.1-.3-.3-.3-.5l.9-5.2-3.8-3.7c-.2-.1-.3-.3-.3-.5s.2-.4.4-.4l5.2-.8 2.3-4.7c.1-.2.3-.3.5-.3z"/>
                    </svg>
                </div>
            </div>
            <div class="sidebar-title-group">
                <h1>AUTOPSY</h1>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Menu items with icons
    st.markdown('<div class="sidebar-menu">', unsafe_allow_html=True)

    # Dashboard button
    st.markdown(
        """
        <form method="get">
            <input type="hidden" name="menu" value="Dashboard" />
            <button type="submit" class="menu-button" data-menu="Dashboard">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M3 5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5z"></path>
                    <path d="M13 5a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2V5z"></path>
                    <path d="M3 15a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4z"></path>
                    <path d="M13 15a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v4a2 2 0 0 1-2 2h-4a2 2 0 0 1-2-2v-4z"></path>
                </svg>
                <span>Dashboard</span>
                <div class="indicator"></div>
            </button>
        </form>
        """,
        unsafe_allow_html=True,
    )

    # Log Error button
    st.markdown(
        """
        <form method="get">
            <input type="hidden" name="menu" value="Log Error" />
            <button type="submit" class="menu-button" data-menu="Log Error">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <circle cx="12" cy="12" r="10"></circle>
                    <path d="M12 7v10M7 12h10" stroke="white" stroke-width="1.5" stroke-linecap="round"></path>
                </svg>
                <span>Log Mistake</span>
                <div class="indicator"></div>
            </button>
        </form>
        """,
        unsafe_allow_html=True,
    )

    # Coach AI button
    st.markdown(
        """
        <form method="get">
            <input type="hidden" name="menu" value="Coach AI" />
            <button type="submit" class="menu-button" data-menu="Coach AI">
                <svg viewBox="0 0 24 24" fill="currentColor">
                    <path d="M2 9 L12 4 L22 9 L12 14 Z"/>
                    <path d="M6 11.5 V15 C6 16.5 18 16.5 18 15 V11.5 L12 14.5 Z"/>
                    <path d="M18.5 9.5 V14 C18.5 14.8 17.5 15.2 17 15.2
                            C16.5 15.2 15.5 14.8 15.5 14
                            V12.8 C15.5 12.4 15.8 12.1 16.2 12.1
                            C16.6 12.1 16.9 12.4 16.9 12.8
                            V13.6 C16.9 13.8 17.2 14 17.5 14
                            C17.8 14 18.1 13.8 18.1 13.6
                            V9.5 Z"/>
                </svg>
                <span>IA Coach</span>
                <div class="indicator"></div>
            </button>
        </form>
        """,
        unsafe_allow_html=True,
    )

    # History button
    st.markdown(
        """
        <form method="get">
            <input type="hidden" name="menu" value="History" />
            <button type="submit" class="menu-button" data-menu="History">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <circle cx="12" cy="12" r="9"></circle>
                    <path d="M12 6v6l4 2"></path>
                </svg>
                <span>History</span>
                <div class="indicator"></div>
            </button>
        </form>
        """,
        unsafe_allow_html=True,
    )

    st.markdown("</div>", unsafe_allow_html=True)

    menu = st.session_state.current_menu

# Blank dashboard placeholder; other pages can be added later
if menu == "Dashboard":
    # Custom CSS to make dashboard buttons (Arrow, Back) look clean/transparent
    # Styles moved to assets/style.css

    st.title("Your Progress")

    # Time Filter Widget (Global)
    filter_options = [
        "This Month",
        "Last 2 Months",
        "Last 4 Months",
        "Last 6 Months",
        "All Time",
    ]

    # Place filter at the top, aligned left or with columns
    col_filter_global, _ = st.columns([2, 5])
    with col_filter_global:
        selected_filter = st.selectbox(
            "Time Period",
            options=filter_options,
            index=filter_options.index(st.session_state.get("time_filter", "All Time")),
            key="time_filter_select",
        )
        # Update session state
        st.session_state.time_filter = selected_filter

    # Determine months for filtering
    filter_map = {
        "This Month": 0,
        "Last 2 Months": 2,
        "Last 4 Months": 4,
        "Last 6 Months": 6,
        "All Time": None,
    }
    months_filter = filter_map[selected_filter]

    # Filter the data globally for the dashboard
    dashboard_filtered_errors = mt.filter_data_by_range(errors, months_filter)

    # Calculate metrics on the dashboard_filtered_errors
    total_errors_count = len(dashboard_filtered_errors)

    # Calculate most frequent subject
    subj_counts = {}
    for r in dashboard_filtered_errors:
        s = r.get("subject", "Unknown") or "Unknown"
        subj_counts[s] = subj_counts.get(s, 0) + 1
    top_subj = max(subj_counts.items(), key=lambda x: x[1])[0] if subj_counts else "—"

    # Calculate most frequent type
    type_counts = {}
    for r in dashboard_filtered_errors:
        t = r.get("type", "Other") or "Other"
        type_counts[t] = type_counts.get(t, 0) + 1
    top_tp = max(type_counts.items(), key=lambda x: x[1])[0] if type_counts else "—"

    # Calculate Avoidable Errors % (Attention Detail + Interpretation)
    avoidable_count = type_counts.get("Attention Detail", 0) + type_counts.get(
        "Interpretation", 0
    )
    if total_errors_count > 0:
        avoidable_pct = (avoidable_count / total_errors_count) * 100
    else:
        avoidable_pct = 0.0

    # Hide delta for now as it makes less sense on variable timeframes
    pill_class = "pill-positive"

    # Render cards side-by-side (Now 4 columns)
    col1, col2, col3, col4 = st.columns(4)

    col1.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-icon" style="background:#eef2ff; color:#4338ca;">!</div>
            </div>
            <div class="metric-label">Total Errors</div>
            <div class="metric-value">{total_errors_count}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col2.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-icon" style="background:#e7f5ef; color:#0f766e;">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" width="20" height="20">
                        <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                        <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                    </svg>
                </div>
                <div class="metric-pill pill-positive">Highlight</div>
            </div>
            <div class="metric-label">Subject with Most Errors</div>
            <div class="metric-value">{top_subj}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col3.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-icon" style="background:#fff7ed; color:#c2410c;">⚡</div>
                <div class="metric-pill pill-positive">Primary</div>
            </div>
            <div class="metric-label">Primary Error Reason</div>
            <div class="metric-value">{top_tp}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col4.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-icon" style="background:#fefce8; color:#a16207;">⚠️</div>
                <div class="metric-pill pill-negative">{avoidable_pct:.1f}%</div>
            </div>
            <div class="metric-label">Avoidable Errors</div>
            <div class="metric-value">{avoidable_count}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Second row: Filter, Chart card and AI Insight card
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # Second row: Chart card and AI Insight card
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    # (Removed local filter widget)

    chart_errors = dashboard_filtered_errors

    chart_col, insight_col = st.columns([2, 1])

    with chart_col:
        # Initialize chart view state
        if "chart_view" not in st.session_state:
            st.session_state.chart_view = 0

        current_view = st.session_state.chart_view
        subtitles = ["Analysis by discipline", "Analysis by topic", "Timeline overview"]

        # Ensure view index is within bounds (if we added a new view)
        if current_view >= len(subtitles):
            current_view = 0
            st.session_state.chart_view = 0

        # Header with title and toggle button
        col_title, col_button = st.columns([12, 1])
        with col_title:
            st.markdown(
                f"""
                <h3 style="font-family:'Helvetica Neue', sans-serif;font-size:1.35rem;font-weight:800;color:#0f172a;margin:0 0 0.4rem 0;letter-spacing:0.08em;text-transform:uppercase;">Error Concentration</h3>
                <p style="font-family:'Helvetica Neue', sans-serif;font-size:0.95rem;color:#94a3b8;font-weight:500;font-style:italic;margin:0 0 1.5rem 0;">{subtitles[current_view]}</p>
            """,
                unsafe_allow_html=True,
            )

        with col_button:
            if st.button("→", key="chart_toggle", help="Toggle view"):
                st.session_state.chart_view = (current_view + 1) % len(subtitles)
                st.rerun()

        # Build data for the selected view
        if current_view == 0:
            subject_data = aggregate_by_subject(chart_errors)
            if not subject_data:
                st.info(f"No data available for {selected_filter}. Log some errors!")
            else:
                df = pd.DataFrame(
                    list(subject_data.items()), columns=["Subject", "Errors"]
                ).sort_values("Errors", ascending=False)

                # Create selection interval
                select_subject = alt.selection_point(
                    name="select_subject", fields=["Subject"], on="click"
                )

                chart = (
                    alt.Chart(df)
                    .mark_bar(color="#6366f1")
                    .encode(
                        x=alt.X("Subject:N", title=None),
                        y=alt.Y("Errors:Q", title=None),
                        opacity=alt.condition(
                            select_subject, alt.value(1), alt.value(0.3)
                        ),
                    )
                    .add_params(select_subject)
                    .properties(height=320)
                    .configure_view(strokeOpacity=0)
                    .configure_axis(labelColor="#0f172a", gridColor="#e2e8f0")
                )

                # Render chart with selection event
                event = st.altair_chart(
                    chart,
                    use_container_width=True,
                    on_select="rerun",
                    key="subject_chart_select",
                )

                # Handle selection
                if (
                    event
                    and "selection" in event
                    and "select_subject" in event["selection"]
                ):
                    selection_list = event["selection"]["select_subject"]
                    if selection_list:
                        # Extract the subject name (dictionaries in list)
                        # The click returns a list of dicts, e.g. [{'Subject': 'Math'}]
                        selected_subj_name = selection_list[0].get("Subject")
                        if selected_subj_name:
                            st.session_state.drill_down_subject = selected_subj_name
                            st.session_state.chart_view = 1  # Switch to Topic View
                            st.rerun()

        elif current_view == 1:  # Topic Analysis
            # Check for drill-down filter
            target_subject = st.session_state.get("drill_down_subject")

            # If drilling down, filter the chart_errors first
            if target_subject:
                # Show active filter UI with cleaner styling
                # Using a narrow column for the button to keep it compact
                c_back, c_text = st.columns([1.5, 8])

                with c_back:
                    if st.button(
                        "← Back", key="clear_drill_down", help="Clear Subject Filter"
                    ):
                        st.session_state.drill_down_subject = None
                        st.session_state.chart_view = 0  # Go back to Subject View
                        st.rerun()

                with c_text:
                    # Styled text matching dashboard aesthetics
                    st.markdown(
                        f"""
                        <div style="font-family:'Helvetica Neue', sans-serif; padding-top: 5px;">
                            <span style="color:#64748b; font-weight:500; font-size:0.9rem;">Showing topics for:</span>
                            <span style="color:#6366f1; font-weight:700; font-size:1rem; margin-left:4px;">{target_subject}</span>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                # Filter data to only this subject
                filtered_topic_errors = [
                    e for e in chart_errors if e.get("subject") == target_subject
                ]
                topic_data = aggregate_by_topic(filtered_topic_errors)
            else:
                # Normal behavior
                topic_data = aggregate_by_topic(chart_errors)

            if not topic_data:
                st.info(f"No data available for {selected_filter}. Log some errors!")
            else:
                # Limit to top 10 topics to avoid clutter
                sorted_topics = sorted(
                    topic_data.items(), key=lambda x: x[1], reverse=True
                )[:10]
                df = pd.DataFrame(sorted_topics, columns=["Topic", "Errors"])

                chart = (
                    alt.Chart(df)
                    .mark_bar(color="#6366f1")
                    .encode(
                        x=alt.X("Topic:N", title=None, sort="-y"),
                        y=alt.Y("Errors:Q", title=None),
                        tooltip=["Topic", "Errors"],
                    )
                    .properties(height=320)
                    .configure_view(strokeOpacity=0)
                    .configure_axis(labelColor="#0f172a", gridColor="#e2e8f0")
                )
                st.altair_chart(chart, use_container_width=True)

        else:
            month_data = aggregate_by_month_all(chart_errors)
            if not month_data:
                st.info(f"No data available for {selected_filter}. Log some errors!")
            else:
                sorted_months = sorted(
                    month_data.items(),
                    key=lambda x: datetime.strptime(x[0], "%b %Y"),
                )
                df = pd.DataFrame(sorted_months, columns=["Month", "Errors"])

                chart = (
                    alt.Chart(df)
                    .mark_bar(color="#6366f1")
                    .encode(
                        x=alt.X("Month:N", title=None, sort=None),
                        y=alt.Y("Errors:Q", title=None),
                    )
                    .properties(height=320)
                    .configure_view(strokeOpacity=0)
                    .configure_axis(labelColor="#0f172a", gridColor="#e2e8f0")
                )
                st.altair_chart(chart, use_container_width=True)

    with insight_col:
        # Check for refresh request via query params (from the custom HTML form)
        # We need to handle this BEFORE displaying logic to ensure it updates instantly
        qp = st.query_params
        if qp.get("refresh_insight") == "true":
            st.session_state.dashboard_insight = ai.generate_mini_insight(chart_errors)

        # Check if we already have a cached insight for this session
        if (
            "dashboard_insight" not in st.session_state
            or st.session_state.dashboard_insight is None
            or str(st.session_state.dashboard_insight) == "None"
        ):
            st.session_state.dashboard_insight = ai.generate_web_insight(chart_errors)

        mini_insight = st.session_state.dashboard_insight

        # Fallback for display
        if mini_insight is None or str(mini_insight) == "None":
            mini_insight = "Insight generation failed. Please check API Key or Logs."

        st.markdown(
            f"""
            <div class="insight-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 class="insight-title" style="color: #eeeeee; margin:0;">Insight</h3>
                </div>
                <div class="insight-content">
                    {mini_insight}
                </div>

                

            </div>
            """,
            unsafe_allow_html=True,
        )

    # -------------------------------------------------------------------------
    # NEW SECTION: Error Breakdown by Type (Pie Chart) with separate filter
    st.markdown("<div style='margin-top: 3rem;'></div>", unsafe_allow_html=True)

    # Section Header
    st.markdown(
        """
        <h3 style="font-family:'Helvetica Neue', sans-serif;font-size:1.35rem;font-weight:800;color:#0f172a;margin:0 0 0.4rem 0;letter-spacing:0.08em;text-transform:uppercase;">Error Breakdown</h3>
        <p style="font-family:'Helvetica Neue', sans-serif;font-size:0.95rem;color:#94a3b8;font-weight:500;font-style:italic;margin:0 0 1.5rem 0;">Distribution by mistake type</p>
        """,
        unsafe_allow_html=True,
    )

    # Container for Filter + Chart
    # Use a card-like style or just clean layout
    # Container for Filter + Chart
    # Use a 3/5 column layout as requested
    col_content, col_spacer = st.columns([3, 2])

    # Container for Chart (3/5 layout)
    col_content, col_spacer = st.columns([3, 2])

    with col_content:
        # (Removed local filter widget)

        # Use global filtered data
        pie_chart_errors = dashboard_filtered_errors

        # Generate Data
        type_data = mt.count_error_types(pie_chart_errors)

        if not type_data:
            st.info(f"No data available for {selected_filter}.")
        else:
            df_pie = pd.DataFrame(list(type_data.items()), columns=["Type", "Count"])

            # Custom Palette from user image
            # Midnight Violet, Slate Blue, Lavender Purple, Soft Periwinkle, Pale Slate, Linen
            custom_colors = [
                "#242038",
                "#725AC1",
                "#8070C5",
                "#8D86C9",
                "#CAC4CE",
                "#F7ECE1",
            ]

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

            # Combine
            pie_chart = (pie + text).properties(height=350)

            st.altair_chart(pie_chart, use_container_width=True)

elif menu == "Log Error":
    st.title("📝 Log a New Mistake")
    with st.container(border=True):
        if st.session_state.reset_form:
            st.session_state.subject_input = ""
            st.session_state.topic_input = ""
            st.session_state.description_input = ""
            st.session_state.error_type_select = DEFAULT_ERROR_TYPE
            st.session_state.date_input = date.today()
            st.session_state.reset_form = False

        col1, col2 = st.columns(2)
        with col1:
            subject = st.text_input(
                "Subject", placeholder="e.g., Math", key="subject_input"
            )
            topic = st.text_input(
                "Topic", placeholder="e.g., Geometry", key="topic_input"
            )
        with col2:
            date_input = st.date_input("Date", key="date_input")
            error_type = st.selectbox(
                "Error Type",
                [
                    "Content Gap",
                    "Attention Detail",
                    "Time Management",
                    "Fatigue",
                    "Interpretation",
                ],
                key="error_type_select",
            )

        description = st.text_area(
            "Description (Optional)",
            placeholder="Why do you think this happened?",
            key="description_input",
        )

        submitted = st.button("Log Mistake", use_container_width=True)

        if submitted:
            if not subject or not topic:
                st.error("Please fill in both Subject and Topic.")
            else:
                db.log_error(
                    errors,
                    subject,
                    topic,
                    error_type,
                    description,
                    date_input,
                )
                st.session_state.show_success = True
                st.session_state.success_message = (
                    f"Error in {subject} ({topic}) logged!"
                )
                st.session_state.reset_form = True  # Trigger reset on next run
                st.rerun()

    if st.session_state.show_success:
        st.success(st.session_state.success_message)
        time.sleep(2)  # Brief pause so user sees it
        st.session_state.show_success = False
        st.session_state.success_message = ""
        st.rerun()

elif menu == "Coach AI":
    # ---------------------------------------------------------
    # 1. HIGH-FIDELITY CSS INJECTION
    # ---------------------------------------------------------
    # Styles moved to assets/style.css

    # ---------------------------------------------------------
    # 2. DIAGNOSTIC ENGINE VIEW (Default)
    # ---------------------------------------------------------

    st.markdown(
        """
        <h1 class="diagnostic-header">
            AI DIAGNOSTIC ENGINE
        </h1>
        <p class="diagnostic-subtext">
            Scanning behavioral data to identify neuro-cognitive bottlenecks.
        </p>
    """,
        unsafe_allow_html=True,
    )

    # Controls Row
    c_filter, c_btn = st.columns([1, 4])
    with c_filter:
        time_scope = st.selectbox(
            "Scope", ["Last 30 Days", "Last 60 Days"], label_visibility="collapsed"
        )
    with c_btn:
        # Fake label to align with the "Scope" label in the other column
        st.markdown(
            "<div style='margin-bottom: 0.2rem; font-size: 0.8rem; visibility: hidden;'>Spacer</div>",
            unsafe_allow_html=True,
        )
        # Just standard button for now, styled via primary type
        run_diag = st.button(
            "RUN DEEP DIAGNOSIS", type="primary", use_container_width=False
        )

    # Logic
    if run_diag:
        # Just like before
        days = 30 if "30" in time_scope else 60
        filtered_data = mt.filter_data_by_range(errors, months=None)
        cutoff = date.today() - pd.Timedelta(days=days)
        filtered_diag_data = [
            e
            for e in errors
            if datetime.strptime(e["date"], "%d-%m-%Y").date() >= cutoff
        ]

        with st.spinner("Analyzing neural patterns..."):
            diagnosis = ai.generate_pattern_diagnosis(filtered_diag_data)
            st.session_state.latest_diagnosis = diagnosis
            st.session_state.diagnosis_date = time_scope

    # DISPLAY AREA
    if (
        "latest_diagnosis" in st.session_state
        and st.session_state.get("diagnosis_date") == time_scope
    ):
        # RENDER ACTIVE CARD (We'll reuse the style from before but refined)
        date_scope = st.session_state.get("diagnosis_date", "Unknown")
        diagnosis_text = st.session_state.latest_diagnosis
        st.markdown(
            f"""
                <div class="neural-card">
                    <!-- Header -->
                    <div class="neural-header">
                        <span class="neural-badge">Neural Insight</span>
                        <span class="neural-date">{date_scope}</span>
                    </div>
                    <!-- Content -->
                    <div class="neural-content">
                        {diagnosis_text}
                    </div>
                    <!-- Footer -->
                    <div class="neural-footer">
                        <div class="neural-confidence">Diagnosis Confidence: <span class="neural-confidence-value">98.2%</span></div>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        # IDLE STATE
        st.markdown(
            """
                <div class="dashed-container idle-container">
                    <div class="idle-icon-circle">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
                    </div>
                    <h3 class="idle-title">Neural Link Idle</h3>
                    <p class="idle-text">Request a diagnosis to allow the AI to scan your recent error descriptions and performance trends.</p>
                </div>
            """,
            unsafe_allow_html=True,
        )


elif menu == "History":
    st.empty()
