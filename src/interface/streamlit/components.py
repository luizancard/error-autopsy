import streamlit as st

# renders the sidebar logo and title


def render_sidebar_header():
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


# render a generic button
def render_menu_button(label, value, icon_svg):
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
    label,
    value,
    icon_char,
    icon_bg="#eef2ff",
    icon_color="#4338ca",
    pill_text=None,
    pill_class="",
):
    pill_html = (
        f'<div class="metric-pill {pill_class}">{pill_text}</div>' if pill_text else ""
    )
    st.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-header">
            <div class="metric-icon" style="background:{icon_bg}; color:{icon_color};">
                {icon_char}
        </div>
        {pill_html}
    </div>
    <div class="metric-label">{label}</div>
    <div class="metric-value">{value}</div>
</div>
""",
        unsafe_allow_html=True,
    )


def render_diagnostic_header():
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


def render_neural_result(diagnosis_text, date_scope):
    st.markdown(
        """
        <div class="neural-card">
            <div class="neural-header">
                    <span class="neural-badge">Insight</span>
                    <span class="neural-data">{data_scope}</span>
            </div>
            <div class="neural_content">{diagnosis_text}</div>
            <div clas="neural_footer">
                <div class = "neural-confidence">Diagnosis Confidence: <span class="neural-confidence-value">98.8%</span></div>
            </div>
        </div>      
                """,
        unsafe_allow_html=True,
    )


def render_idle_state():
    st.markdown(""""
        <div class="dashed-container idle-container">
            <div class="idle-icon-circle">
                """)


def render_chart_header(subtitle):
    st.markdown(
        """
        <h3 style="font-family:'Helvetica Neue', sans-serif; font-size:1.35rem;font-weight:800;color:#0f172a;margin:0 0 0.4rem 0;letter-spacing:0.08em;text-transform:uppercase;">Error Concentration</h3>
        <p style="font-family:'Helvetica Neue', sans-serif; font-size:0.95rem;font-weight:500;color:#94a3b8;font-style:italic;margin:0 0 1.5rem 0;>{subtitle}</p>
    """,
        unsafe_allow_html=True,
    )


def render_drill_down_info(subject_name):
    st.markdown(
        f"""
        <div style="font-family:'Helvetica Neue', sans-serif; padding-top: 5px;">
            <span style="color:#64748b; font-weight:500; font-size:0.9rem;">Showing topics for:</span>
            <span style="color:#6366f1; font-weight:700; font-size:1rem; margin-left:4px;">{subject_name}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def generate_web_insight(data):
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
