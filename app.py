import time
from datetime import date, datetime

import streamlit as st

import database as db

errors = db.load_data()
DEFAULT_ERROR_TYPE = "Content Gap"

st.session_state.setdefault("subject_input", "")
st.session_state.setdefault("topic_input", "")
st.session_state.setdefault("description_input", "")
st.session_state.setdefault("error_type_select", DEFAULT_ERROR_TYPE)
st.session_state.setdefault("date_input", date.today())
st.session_state.setdefault("reset_form", False)
st.session_state.setdefault("success_message", "")
st.session_state.setdefault("show_success", False)

raw_menu = st.query_params.get("menu", "Dashboard")
menu_from_url = raw_menu[0] if isinstance(raw_menu, list) else raw_menu
st.session_state["current_menu"] = menu_from_url

st.set_page_config(page_title="Error Autopsy", layout="wide", page_icon="📝")


def local_css():
    st.markdown(
        """
        <style>
        .st-emotion-cache-1r6slb0 {
            background-color: white;
            padding: 2rem;
            border-radius: 25px;
            box-shadow: 0 7px 10px rgba(0, 0, 0, 0.05);
        }
        
        /* This rounds the corners of text inputs */
        .stTextInput > div > div > input {
            border-radius: 10px;
        }
        
        /* This styles the big headers */
        h1, h2, h3 {
            font-family: 'Helvetica Neue', sans-serif;
            font-weight: 700;
            color: #333;
            margin-top: 0.4rem;
            margin-bottom: 1.8rem;
        }
        
        /* Sidebar Header Styling */
        .sidebar-header-container {
            display: flex;
            align-items: center;
            gap: 1rem;
            margin-bottom: 0.5rem;
            padding: 1rem 0;
        }
        
        .sidebar-logo-wrapper {
            position: relative;
            width: 50px;
            height: 50px;
            flex-shrink: 0;
        }
        
        .sidebar-logo {
            width: 100%;
            height: 100%;
            background: linear-gradient(135deg, #1a2a4a 0%, #2d4563 100%);
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 8px 20px rgba(26, 42, 74, 0.3), inset 0 1px 2px rgba(255, 255, 255, 0.2);
        }
        
        .sidebar-logo svg {
            width: 24px;
            height: 24px;
            filter: drop-shadow(0 2px 4px rgba(0, 0, 0, 0.1));
        }
        
        .sidebar-title-group h1 {
            margin: 0;
            font-size: 1.4rem;
            color: #1a1a1a;
            font-weight: 800;
            letter-spacing: 0.08em;
        }
        
        /* Menu Buttons Styling */
        .sidebar-menu {
            display: flex;
            flex-direction: column;
            gap: 0.8rem;
            margin-top: 2rem;
        }

        .sidebar-menu form {
            margin: 0;
        }
        
        .menu-button {
            display: flex;
            align-items: center;
            gap: 1rem;
            padding: 0.85rem 1.25rem;
            background: transparent;
            border: none !important;
            cursor: pointer;
            border-radius: 12px;
            transition: all 0.2s ease;
            position: relative;
            font-weight: 700 !important;
            width: 100%;
            text-decoration: none !important;
            color: inherit;
        }

        .menu-button:visited,
        .menu-button:focus,
        .menu-button:hover,
        .menu-button:active {
            text-decoration: none !important;
            color: inherit;
        }
        
        .menu-button:hover {
            background-color: #e8e8e8;
        }
        
        .menu-button svg {
            width: 20px;
            height: 20px;
            color: #9ca3af;
            transition: color 0.2s ease;
        }
        
        .menu-button span {
            color: #9ca3af;
            font-size: 1.05rem;
            font-weight: 700;
            transition: color 0.2s ease;
        }
        
        .menu-button.active {
            background: #eeeeeeff !important;
        }
        
        .menu-button.active svg {
            color: #6366f1;
        }
        
        .menu-button.active span {
            color: #1a1a1a;
            font-weight: 700;
        }
        
        .menu-button .indicator {
            position: absolute;
            right: 1rem;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #6366f1;
            opacity: 0;
            transition: opacity 0.2s ease;
        }
        
        .menu-button.active .indicator {
            opacity: 1;
        }

        /* Dashboard cards */
        .metrics-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 1.8rem;
            width: 100%;
            margin-top: 2rem;
        }

        .metric-card {
            background: #eeeeeeff; /* uses theme secondaryBackgroundColor */
            border-radius: 24px;
            padding: 18px;
            box-shadow: 0 15px 30px rgba(0,0,0,0.04);
            display: flex;
            flex-direction: column;
            gap: 10px;
            min-height: 140px;
        }

        .metric-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .metric-icon {
            width: 40px;
            height: 40px;
            border-radius: 12px;
            display: grid;
            place-items: center;
            font-size: 18px;
            font-weight: 700;
            color: #1a1a1a;
        }

        .metric-pill {
            background: #e8f9f0;
            color: #169c5b;
            padding: 6px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
            font-weight: 700;
        }

        .metric-label {
            letter-spacing: 0.08em;
            font-size: 0.85rem;
            font-weight: 700;
            color: #8a94a6;
            text-transform: uppercase;
        }

        .metric-value {
            font-size: 2rem;
            font-weight: 800;
            color: #0f172a;
            line-height: 1.1;
        }
        /* Pill state colors */
        .pill-positive { background: #e8f9f0; color: #16a34a; }
        .pill-negative { background: #fee2e2; color: #b91c1c; }

        /* Inner shadow override for cards */
        .metric-card {
            box-shadow:
                inset 0 10px 18px rgba(255,255,255,0.55),
                inset 0 -8px 18px rgba(0,0,0,0.05),
                0 15px 30px rgba(0,0,0,0.04);
            border: 1px solid rgba(0,0,0,0.03);
        }

        /* Chart card - clean white background */
        .chart-card {
            background: #ffffff;
            border-radius: 24px;
            padding: 28px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.06);
            min-height: 480px;
        }

        .chart-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 1.5rem;
        }

        .chart-title {
            font-size: 1.15rem;
            font-weight: 800;
            color: #0f172a;
            margin: 0 0 0.4rem 0;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .chart-subtitle {
            font-size: 0.9rem;
            color: #94a3b8;
            font-weight: 500;
            font-style: italic;
            margin: 0;
        }

        /* Navigation dots */
        .chart-nav-dots {
            display: flex;
            gap: 8px;
            align-items: center;
        }

        .nav-dot {
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #cbd5e1;
            cursor: pointer;
            transition: all 0.3s ease;
            border: none;
            padding: 0;
        }

        .nav-dot.active {
            background: #0f172a;
            width: 10px;
            height: 10px;
        }

        .nav-dot:hover {
            background: #64748b;
        }

        /* AI Insight card - dark background */
        .insight-card {
            background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
            border-radius: 24px;
            padding: 32px 28px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            min-height: 420px;
            display: flex;
            flex-direction: column;
        }

        .insight-icon-wrapper {
            width: 52px;
            height: 52px;
            background: rgba(255,255,255,0.1);
            border-radius: 14px;
            display: flex;
            align-items: center;
            justify-content: center;
            margin-bottom: 1.5rem;
            backdrop-filter: blur(10px);
        }

        .insight-title {
            font-size: 1.45rem;
            font-weight: 700;
            color: #ffffff;
            margin: 0 0 0.2rem 0;
            font-style: italic;
            position: relative;
            display: inline-block;
            padding-bottom: 0.3rem;
        }

        .insight-title::after {
            content: '';
            position: absolute;
            bottom: 0;
            left: 0;
            width: 100%;
            height: 3px;
            background: #6366f1;
            border-radius: 2px;
        }

        .insight-content {
            color: #cbd5e1;
            font-size: 0.95rem;
            line-height: 1.75;
            margin-top: 1.5rem;
            flex-grow: 1;
        }

        .insight-highlight {
            color: #818cf8;
            font-weight: 700;
        }

        .action-button {
            display: inline-flex;
            align-items: center;
            justify-content: center;
            gap: 0.6rem;
            background: white;
            color: #0f172a;
            padding: 0.9rem 1.6rem;
            border-radius: 12px;
            font-weight: 700;
            font-size: 0.9rem;
            text-decoration: none;
            transition: all 0.2s ease;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            border: none;
            margin-top: auto;
        }

        .action-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(0,0,0,0.25);
        }
        </style>
        </style>
        
        <script>
        function updateMenuButtons() {
            let currentMenu = '"""
        + st.session_state.current_menu
        + """';
            
            const buttonMap = {
                'Dashboard': 'Dashboard',
                'Log Mistake': 'Log Error',
                'IA Coach': 'Coach AI',
                'History': 'History'
            };
            
            const buttons = document.querySelectorAll('.menu-button');
            buttons.forEach(button => {
                const span = button.querySelector('span');
                const indicator = button.querySelector('.indicator');
                
                if (!span) return;
                
                const text = span.innerText.trim();
                let isActive = false;
                
                for (let btnText in buttonMap) {
                    if (text === btnText && buttonMap[btnText] === currentMenu) {
                        isActive = true;
                        break;
                    }
                }
                
                if (isActive) {
                    button.classList.add('active');
                    button.style.background = '#eeeeeeff';
                    span.style.color = '#1a1a1a';
                    button.querySelector('svg').style.color = '#6366f1';
                    indicator.style.opacity = '1';
                } else {
                    button.classList.remove('active');
                    button.style.background = 'transparent';
                    span.style.color = '#9ca3af';
                    button.querySelector('svg').style.color = '#9ca3af';
                    indicator.style.opacity = '0';
                }
            });
        }

        document.addEventListener('DOMContentLoaded', updateMenuButtons);
        window.addEventListener('load', updateMenuButtons);

        </script>
        """,
        unsafe_allow_html=True,
    )


local_css()


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
    """Generate a brief AI-style insight about the student's performance."""
    if not data:
        return (
            "No data available yet. Start logging errors to get personalized insights."
        )

    total = len(data)
    stats = aggregate_monthly_stats(data)
    subject_counts = aggregate_by_subject(data)

    # Find top subject
    top_subject = (
        max(subject_counts.items(), key=lambda x: x[1])[0]
        if subject_counts
        else "Unknown"
    )
    top_subject_count = subject_counts.get(top_subject, 0)

    # Calculate percentage
    if total > 0:
        pct = int((top_subject_count / total) * 100)
    else:
        pct = 0

    # Craft a mini insight
    if stats["current_total"] > 5:
        intensity = "frequently making mistakes"
    elif stats["current_total"] > 2:
        intensity = "making some errors"
    else:
        intensity = "showing good progress"

    insight = f'You are {intensity} in <span class="insight-highlight">{top_subject}</span> after {stats["current_total"]} logged errors this month. This suggests possible content gaps or rushed execution.'

    return insight


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
    stats = aggregate_monthly_stats(errors)
    delta_val = stats["delta"]
    pill_class = "pill-positive" if delta_val >= 0 else "pill-negative"
    st.title("Your Progress")

    # Render cards side-by-side with minimal changes
    col1, col2, col3 = st.columns(3)

    col1.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-icon" style="background:#eef2ff; color:#4338ca;">!</div>
                <div class="metric-pill {pill_class}">{delta_val:+.1f}%</div>
            </div>
            <div class="metric-label">Total Errors (Month)</div>
            <div class="metric-value">{stats["current_total"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col2.markdown(
        f"""
        <div class="metric-card">
            <div class="metric-header">
                <div class="metric-icon" style="background:#e7f5ef; color:#0f766e;">◎</div>
                <div class="metric-pill pill-positive">Highlight</div>
            </div>
            <div class="metric-label">Subject with Most Errors</div>
            <div class="metric-value">{stats["top_subject"]}</div>
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
            <div class="metric-value">{stats["top_type"]}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Second row: Chart card and AI Insight card
    st.markdown("<div style='margin-top: 2rem;'></div>", unsafe_allow_html=True)

    chart_col, insight_col = st.columns([1.3, 1])

    with chart_col:
        # Initialize chart view state
        if "chart_view" not in st.session_state:
            st.session_state.chart_view = 0

        # Ensure current_view is an integer
        current_view = st.session_state.chart_view
        if isinstance(current_view, str):
            current_view = 0 if current_view == "Subject" else 1
            st.session_state.chart_view = current_view

        subtitles = ["Analysis by discipline", "Timeline overview"]

        # Create buttons for navigation using st.form to avoid extra spacing
        col_btn1, col_btn2, col_spacer = st.columns([0.5, 0.5, 9])
        with col_btn1:
            if st.button("⬤" if current_view == 0 else "○", key="dot0", help="Subject"):
                st.session_state.chart_view = 0
                st.rerun()
        with col_btn2:
            if st.button("⬤" if current_view == 1 else "○", key="dot1", help="Month"):
                st.session_state.chart_view = 1
                st.rerun()

        # Single container for entire card
        st.markdown(
            f"""
            <div class="chart-card">
                <div class="chart-header">
                    <div>
                        <h3 class="chart-title">Error Concentration</h3>
                        <p class="chart-subtitle">{subtitles[current_view]}</p>
                    </div>
                </div>
            """,
            unsafe_allow_html=True,
        )

        # Chart content
        if current_view == 0:
            subject_data = aggregate_by_subject(errors)
            if subject_data:
                import pandas as pd

                df = pd.DataFrame(
                    list(subject_data.items()), columns=["Subject", "Errors"]
                )
                df = df.sort_values("Errors", ascending=False)
                st.bar_chart(df.set_index("Subject"), color="#6366f1", height=320)
            else:
                st.info("No data available yet. Start logging errors!")
        else:
            month_data = aggregate_by_month_all(errors)
            if month_data:
                import pandas as pd

                sorted_months = sorted(
                    month_data.items(), key=lambda x: datetime.strptime(x[0], "%b %Y")
                )
                df = pd.DataFrame(sorted_months, columns=["Month", "Errors"])
                st.bar_chart(df.set_index("Month"), color="#6366f1", height=320)
            else:
                st.info("No data available yet. Start logging errors!")

        st.markdown("</div>", unsafe_allow_html=True)

    with insight_col:
        mini_insight = generate_mini_insight(errors)

        st.markdown(
            f"""
            <div class="insight-card">
                <div class="insight-icon-wrapper">
                    <svg viewBox="0 0 24 24" fill="white" width="26" height="26">
                        <circle cx="12" cy="12" r="3" fill="white"/>
                        <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 18c-4.41 0-8-3.59-8-8s3.59-8 8-8 8 3.59 8 8-3.59 8-8 8z" fill="white" opacity="0.6"/>
                        <path d="M12 6v6l4 2" stroke="white" stroke-width="1.5" stroke-linecap="round" opacity="0.8" fill="none"/>
                    </svg>
                </div>
                <h3 class="insight-title">AI Insight</h3>
                <div class="insight-content">
                    {mini_insight}
                </div>
                <form method="get">
                    <input type="hidden" name="menu" value="Coach AI" />
                    <button type="submit" class="action-button">
                        View Action Plan
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" width="16" height="16">
                            <path d="M5 12h14M12 5l7 7-7 7"/>
                        </svg>
                    </button>
                </form>
            </div>
            """,
            unsafe_allow_html=True,
        )

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
            "Description", placeholder="What exactly happened?", key="description_input"
        )

        # Adding some space before the button
        st.write("")

        if st.button("Save Error", type="primary"):
            new_id = len(errors) + 1
            formatted_date = date_input.strftime("%d-%m-%Y")

            new_error = {
                "id": new_id,
                "date": formatted_date,
                "subject": subject,
                "topic": topic,
                "description": description,
                "type": error_type,
            }
            errors.append(new_error)
            db.save_data(errors)

            # Save the success message to session state
            st.session_state.success_message = f"Error {new_id} Saved Successfully!"
            st.session_state.show_success = True
            st.session_state.reset_form = True
            if st.session_state.show_success:
                st.success(st.session_state.success_message)
                time.sleep(1)
                st.session_state.show_sucess = False

            st.rerun()
elif menu == "Coach AI":
    st.empty()
elif menu == "History":
    st.empty()
