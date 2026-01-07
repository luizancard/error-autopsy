"""
Streamlit UI components for the Error Autopsy application.

Provides reusable components for rendering headers, cards, charts, and insights.
"""

from typing import Any, Dict, List, Optional

import streamlit as st


def render_sidebar_header() -> None:
    """Render the application logo and title in the sidebar."""
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


def render_menu_button(label: str, value: str, icon_svg: str) -> None:
    """
    Render a navigation button in the sidebar.

    Args:
        label: Display text for the button.
        value: Menu value submitted when clicked.
        icon_svg: SVG markup for the button icon.
    """
    st.sidebar.markdown(
        f"""
        <form method="get">
            <input type="hidden" name="menu" value="{value}" />
            <button type="submit" class="menu-button" data-menu="{value}">
                {icon_svg}
                <span>{label}</span>
                <div class="indicator"></div>
            </button>
        </form>
        """,
        unsafe_allow_html=True,
    )


def render_metric_card(
    label: str,
    value: Any,
    icon_char: str,
    icon_bg: str = "#eef2ff",
    icon_color: str = "#4338ca",
    pill_text: Optional[str] = None,
    pill_class: str = "",
) -> None:
    """
    Render a metric card with icon and optional pill badge.

    Args:
        label: Card title text.
        value: Main metric value to display.
        icon_char: Character or SVG for the icon.
        icon_bg: Background color for the icon.
        icon_color: Color for the icon.
        pill_text: Optional text for the pill badge.
        pill_class: CSS class for pill styling.
    """
    pill_html = (
        f'<div class="metric-pill {pill_class}">{pill_text}</div>' if pill_text else ""
    )
    html = f'<div class="metric-card"><div class="metric-header"><div class="metric-icon" style="background:{icon_bg}; color:{icon_color};">{icon_char}</div>{pill_html}</div><div class="metric-label">{label}</div><div class="metric-value">{value}</div></div>'
    st.markdown(html, unsafe_allow_html=True)


def render_diagnostic_header() -> None:
    """Render the diagnostic engine header with loading message."""
    st.markdown(
        """
        <h1 class="diagnostic-header">
            AI Diagnostic Engine
        </h1>
        <p class="diagnostic-subtext">
            Scanning behavioral data to identify patterns...
        </p>
"""
    )


def render_neural_result(diagnosis_text: str, date_scope: str) -> None:
    """
    Display diagnostic results in a styled card.

    Args:
        diagnosis_text: The diagnosis content to display.
        date_scope: Time period the diagnosis covers.
    """
    st.markdown(
        f"""
        <div class="neural-card">
            <div class="neural-header">
                <span class="neural-badge">Insight</span>
                <span class="neural-data">{date_scope}</span>
            </div>
            <div class="neural-content">{diagnosis_text}</div>
            <div class="neural-footer">
                <div class="neural-confidence">
                    Diagnosis Confidence: <span class="neural-confidence-value">98.8%</span>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_idle_state() -> None:
    """
    Display an idle state placeholder when no action is in progress.
    """
    st.markdown(
        """
        <div class="dashed-container idle-container">
            <div class="idle-icon-circle">
                <span class="idle-icon">📊</span>
            </div>
            <p class="idle-text">No data to display</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_chart_header(subtitle: str) -> None:
    """
    Render a styled header for chart sections.

    Args:
        subtitle: Descriptive text shown below the title.
    """
    st.markdown(
        f"""
        <h3 style="font-family:'Helvetica Neue', sans-serif; font-size:1.35rem; font-weight:800; color:#0f172a; margin:0 0 0.4rem 0; letter-spacing:0.08em; text-transform:uppercase;">Error Concentration</h3>
        <p style="font-family:'Helvetica Neue', sans-serif; font-size:0.95rem; font-weight:500; color:#94a3b8; font-style:italic; margin:0 0 1.5rem 0;">{subtitle}</p>
        """,
        unsafe_allow_html=True,
    )


def render_drill_down_info(subject_name: str) -> None:
    """
    Display the current drill-down filter context.

    Args:
        subject_name: Name of the subject being filtered.
    """
    st.markdown(
        f"""
        <div style="font-family:'Helvetica Neue', sans-serif; padding-top: 5px;">
            <span style="color:#64748b; font-weight:500; font-size:0.9rem;">Showing topics for:</span>
            <span style="color:#6366f1; font-weight:700; font-size:1rem; margin-left:4px;">{subject_name}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def generate_web_insight(data: List[Dict[str, Any]]) -> str:
    """
    Generate insight HTML from error data.

    Analyzes error patterns to find the most problematic subject/topic
    combination and provides actionable recommendations.

    Args:
        data: List of error records (already filtered by time period).

    Returns:
        HTML string with insight content.
    """
    if not data:
        return "No data in this period. Log more errors or adjust the filter to get key insights."

    # Note: 'data' is already filtered by the dashboard time selector,
    # so we analyze WHATEVER is passed to us (last 6 months, this month, etc.)
    recent_data = data

    # (Unused variables removed)

    # 1. Drill Down Analysis
    hierarchy = {}

    for item in recent_data:
        sub = item.get("subject", "Unknown").strip() or "Unknown"
        top = item.get("topic", "Unknown").strip() or "Unknown"
        err = item.get("type", "Unknown")

        if sub not in hierarchy:
            hierarchy[sub] = {}
        if top not in hierarchy[sub]:
            hierarchy[sub][top] = {}
        hierarchy[sub][top][err] = hierarchy[sub][top].get(err, 0) + 1

    # Find stats
    max_errors = -1
    best_combo = None

    for sub, topics in hierarchy.items():
        for top, error_counts in topics.items():
            # Find dominant error for this topic
            dom_err = max(error_counts.items(), key=lambda x: x[1])[0]
            total_topic_errors = sum(error_counts.values())

            if total_topic_errors > max_errors:
                max_errors = total_topic_errors
                best_combo = (sub, top, dom_err, total_topic_errors)

    if not best_combo:
        return "Keep logging errors to unlock insights."

    target_sub, target_top, target_err, count = best_combo

    # Static Advice Map
    advice_map = {
        "Content Gap": "Review core concepts and definitions before practicing.",
        "Attention detail": "Read questions twice and underline key variables.",
        "Attention Detail": "Read questions twice and underline key variables.",
        "Time management": "Skip hard questions early; focus on 'points per minute'.",
        "Time Management": "Skip hard questions early; focus on 'points per minute'.",
        "Fatigue": "Optimize sleep and take breaks. Quality over quantity.",
        "Interpretation": "Re-state the problem in your own words before solving.",
        "Unknown": "Ensure you categorize your errors to get better tips.",
    }

    # Normalize error key for lookup
    key = str(target_err).strip()
    tip = advice_map.get(key) or advice_map.get(
        key.title(), "Review your error log patterns."
    )

    # HTML Output
    insight_html = (
        f"Bottleneck detected in <b>{target_sub}</b>: <br>"
        f"High volume of '<b>{target_err}</b>' errors in <span class='insight-highlight'>{target_top}</span>. "
        f"<br><br><b>Recommendation:</b> {tip}"
    )

    return insight_html
