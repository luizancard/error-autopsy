import time
from datetime import date, datetime

import altair as alt
import pandas as pd
import streamlit as st

import analytics as an
import database as db

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
            background: #EEEEEE;
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

        .insight-title {
            font-size: 1.6rem;
            font-weight: 700;
            color: #eeeeee;
            margin: 0 0 0.2rem 0;
            font-style: bold;
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
    return an.generate_web_insight(data)


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
    st.markdown(
        """
        <style>
        /* Force transparent buttons for both "Back" and the Chart Toggle */
        /* We target the specific data-testid for stButton to ensure we hit them */
        
        div[data-testid="stButton"] > button {
            background-color: transparent !important;
            border: 1px solid transparent !important; /* Ensure border is transparent */
            box-shadow: none !important;
            color: #64748b !important;
            font-weight: 600 !important;
            padding: 0px 8px !important;
            transition: all 0.2s ease;
        }

        /* Hover state */
        div[data-testid="stButton"] > button:hover {
            color: #6366f1 !important;
            background-color: rgba(99, 102, 241, 0.1) !important; /* Very subtle hover bg */
            border-color: transparent !important;
        }

        /* Active/Focus state */
        div[data-testid="stButton"] > button:active, 
        div[data-testid="stButton"] > button:focus {
            color: #4338ca !important;
            background-color: transparent !important;
            border-color: transparent !important;
            box-shadow: none !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )
    
    st.title("Your Progress")

    # Time Filter Widget (Global)
    filter_options = ["This Month", "Last 2 Months", "Last 4 Months", "Last 6 Months", "All Time"]
    
    # Place filter at the top, aligned left or with columns
    col_filter_global, _ = st.columns([2, 5])
    with col_filter_global:
        selected_filter = st.selectbox(
            "Time Period", 
            options=filter_options, 
            index=filter_options.index(st.session_state.get("time_filter", "All Time")),
            key="time_filter_select"
        )
        # Update session state
        st.session_state.time_filter = selected_filter

    # Determine months for filtering
    filter_map = {
        "This Month": 0,
        "Last 2 Months": 2,
        "Last 4 Months": 4,
        "Last 6 Months": 6,
        "All Time": None
    }
    months_filter = filter_map[selected_filter]
    
    # Filter the data globally for the dashboard
    dashboard_filtered_errors = an.filter_data_by_range(errors, months_filter)

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
    avoidable_count = type_counts.get("Attention Detail", 0) + type_counts.get("Interpretation", 0)
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
                select_subject = alt.selection_point(name="select_subject", fields=["Subject"], on="click")

                chart = (
                    alt.Chart(df)
                    .mark_bar(color="#6366f1")
                    .encode(
                        x=alt.X("Subject:N", title=None),
                        y=alt.Y("Errors:Q", title=None),
                        opacity=alt.condition(select_subject, alt.value(1), alt.value(0.3))
                    )
                    .add_params(select_subject)
                    .properties(height=320)
                    .configure_view(strokeOpacity=0)
                    .configure_axis(labelColor="#0f172a", gridColor="#e2e8f0")
                )
                
                # Render chart with selection event
                event = st.altair_chart(chart, use_container_width=True, on_select="rerun", key="subject_chart_select")
                
                # Handle selection
                if event and "selection" in event and "select_subject" in event["selection"]:
                    selection_list = event["selection"]["select_subject"]
                    if selection_list:
                        # Extract the subject name (dictionaries in list)
                        # The click returns a list of dicts, e.g. [{'Subject': 'Math'}]
                        selected_subj_name = selection_list[0].get("Subject")
                        if selected_subj_name:
                            st.session_state.drill_down_subject = selected_subj_name
                            st.session_state.chart_view = 1 # Switch to Topic View
                            st.rerun()

        elif current_view == 1: # Topic Analysis
            # Check for drill-down filter
            target_subject = st.session_state.get("drill_down_subject")
            
            # If drilling down, filter the chart_errors first
            if target_subject:
                # Show active filter UI with cleaner styling
                # Using a narrow column for the button to keep it compact
                c_back, c_text = st.columns([1.5, 8])
                
                with c_back:
                    if st.button("← Back", key="clear_drill_down", help="Clear Subject Filter"):
                        st.session_state.drill_down_subject = None
                        st.session_state.chart_view = 0 # Go back to Subject View
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
                        unsafe_allow_html=True
                    )
                
                # Filter data to only this subject
                filtered_topic_errors = [e for e in chart_errors if e.get("subject") == target_subject]
                topic_data = aggregate_by_topic(filtered_topic_errors)
            else:
                # Normal behavior
                topic_data = aggregate_by_topic(chart_errors)
            
            if not topic_data:
                 st.info(f"No data available for {selected_filter}. Log some errors!")
            else:
                 # Limit to top 10 topics to avoid clutter
                 sorted_topics = sorted(topic_data.items(), key=lambda x: x[1], reverse=True)[:10]
                 df = pd.DataFrame(sorted_topics, columns=["Topic", "Errors"])
                 
                 chart = (
                    alt.Chart(df)
                    .mark_bar(color="#6366f1") 
                    .encode(
                        x=alt.X("Topic:N", title=None, sort="-y"),
                        y=alt.Y("Errors:Q", title=None),
                        tooltip=["Topic", "Errors"]
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
             st.session_state.dashboard_insight = an.generate_mini_insight(chart_errors)
        
        # Check if we already have a cached insight for this session
        if "dashboard_insight" not in st.session_state:
             st.session_state.dashboard_insight = an.generate_mini_insight(chart_errors)
        
        mini_insight = st.session_state.dashboard_insight
        
        # We need a way to refresh it. Let's add a small refresh icon/button near the title using columns inside the markdown? 
        # Or simpler: Just rely on the cache. If they want new, they can clear cache or we add a button.
        # Let's add a button below the text.
        
        st.markdown(
            f"""
            <div class="insight-card">
                <div style="display:flex; justify-content:space-between; align-items:center;">
                    <h3 class="insight-title" style="color: #eeeeee; margin:0;">AI Insight</h3>
                </div>
                <div class="insight-content">
                    {mini_insight}
                </div>
                <form action="/" method="get">
                     <button name="refresh_insight" value="true" type="submit" style="
                        background: rgba(255,255,255,0.1); 
                        border: none; 
                        color: white; 
                        padding: 4px 8px; 
                        border-radius: 4px; 
                        cursor: pointer; 
                        font-size: 0.75rem;
                        margin-top: 10px;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                     ">
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                             <path d="M23 4v6h-6"></path>
                             <path d="M1 20v-6h6"></path>
                             <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path>
                        </svg>
                        Refresh Insight
                     </button>
                    <!-- Keep menu context -->
                     <input type="hidden" name="menu" value="Dashboard" />
                </form>
                

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
        unsafe_allow_html=True
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
        type_data = an.count_error_types(pie_chart_errors)
        
        if not type_data:
             st.info(f"No data available for {selected_filter}.")
        else:
            df_pie = pd.DataFrame(list(type_data.items()), columns=["Type", "Count"])
            
            # Custom Palette from user image
            # Midnight Violet, Slate Blue, Lavender Purple, Soft Periwinkle, Pale Slate, Linen
            custom_colors = ["#242038", "#725AC1", "#8070C5", "#8D86C9", "#CAC4CE", "#F7ECE1"]
            
            base = alt.Chart(df_pie).encode(
                theta=alt.Theta("Count", stack=True)
            )
            
            pie = base.mark_arc(outerRadius=120, innerRadius=0).encode(
                color=alt.Color(
                    "Type", 
                    scale=alt.Scale(range=custom_colors),
                    legend=alt.Legend(title="Error Type")
                ),
                order=alt.Order("Count", sort="descending"),
                tooltip=["Type", "Count"]
            )
            
            text = base.mark_text(radius=140).encode(
                text=alt.Text("Count"),
                order=alt.Order("Count", sort="descending"),
                color=alt.value("#0f172a") 
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
                an.log_error(
                    errors,
                    subject,
                    topic,
                    error_type,
                    description,
                    str(date_input),
                )
                st.session_state.show_success = True
                st.session_state.success_message = f"Error in {subject} ({topic}) logged!"
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
    st.markdown("""
        <style>
            /* Global Font Override */
            @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
            
            html, body, [class*="css"] {
                font-family: 'Inter', 'Helvetica Neue', sans-serif;
            }
            
            /* Custom Pill Nav */
            .nav-pill {
                display: inline-block;
                padding: 8px 16px;
                border-radius: 99px;
                font-size: 0.8rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.05em;
                cursor: pointer;
                transition: all 0.2s ease;
                border: 1px solid transparent;
                margin-right: 8px;
            }
            .nav-pill.active {
                background-color: #0f172a;
                color: white;
                box-shadow: 0 4px 12px rgba(15, 23, 42, 0.15);
            }
            .nav-pill.inactive {
                background-color: white;
                color: #64748b;
                border: 1px solid #e2e8f0;
            }
            .nav-pill.inactive:hover {
                background-color: #f8fafc;
                border-color: #cbd5e1;
                color: #334155;
            }
            
            /* "Ghost" Button Style (as seen in screenshots) */
            .ghost-btn {
                background: white;
                border: 1px solid #e2e8f0;
                color: #0f172a;
                font-weight: 600;
                border-radius: 8px;
                padding: 0.5rem 1rem;
                font-size: 0.9rem;
                transition: all 0.2s;
            }
            .ghost-btn:hover {
                background: #f8fafc;
                border-color: #cbd5e1;
            }
            
            /* Dashed Empty State */
            .dashed-container {
                border: 2px dashed #e2e8f0;
                border-radius: 24px;
                background-color: #ffffff;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                text-align: center;
                padding: 6rem 2rem;
                min-height: 400px;
                margin-top: 1.5rem;
            }
            
            /* Configuration Modal Style */
            .config-card {
                background: white;
                border: 1px solid #e2e8f0;
                border-radius: 24px;
                padding: 2rem;
                box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04);
                max-width: 600px;
                margin: 2rem auto;
            }
            
            /* Hide Default Streamlit Elements */
            [data-testid="stHeader"] { visibility: hidden; }
        </style>
    """, unsafe_allow_html=True)

    # ---------------------------------------------------------
    # 2. CUSTOM NAVIGATION (State-Based)
    # ---------------------------------------------------------
    # Init state for sub-view
    if "coach_view" not in st.session_state:
        st.session_state.coach_view = "diagnostic"

    # Custom Top Bar
    c_nav, c_actions = st.columns([1, 1])
    
    with c_nav:
        # We use columns to simulate the pill buttons side-by-side
        # To make them strictly clickable, we use st.button but heavily styled
        # Or better: Standard st.pills if available? It's new in very recent streamlit. 
        # Let's stick to buttons for stability, or better yet, a segmented control.
        # Streamlit has `st.segmented_control` in 1.40.0+. I'll assume we are on standard.
        # Simplest approach: Two columns with buttons and conditionally render style.
        
        n1, n2, n_spacer = st.columns([1, 1, 3])
        if n1.button("AI DIAGNOSTIC ENGINE", key="nav_diag", 
                     type="primary" if st.session_state.coach_view == "diagnostic" else "secondary",
                     use_container_width=True):
            st.session_state.coach_view = "diagnostic"
            st.rerun()
            
        if n2.button("STUDY PLAN", key="nav_plan", 
                     type="primary" if st.session_state.coach_view == "plan" else "secondary",
                     use_container_width=True):
            st.session_state.coach_view = "plan"
            st.rerun()

    # ---------------------------------------------------------
    # 3. DIAGNOSTIC ENGINE VIEW
    # ---------------------------------------------------------
    if st.session_state.coach_view == "diagnostic":
        st.markdown("""
            <h1 style="font-family:'Helvetica Neue'; font-weight:900; font-style:italic; font-size:3rem; letter-spacing:-0.04em; margin-bottom:0; line-height:1.1;">
                AI DIAGNOSTIC ENGINE
            </h1>
            <p style="color:#64748b; font-size:1.1rem; font-weight:500; margin-top:0.5rem; margin-bottom:2rem;">
                Scanning behavioral data to identify neuro-cognitive bottlenecks.
            </p>
        """, unsafe_allow_html=True)
        
        # Controls Row
        c_filter, c_btn = st.columns([1, 4])
        with c_filter:
            time_scope = st.selectbox("Scope", ["Last 30 Days", "Last 60 Days"], label_visibility="collapsed")
        with c_btn:
            # Right align the button
            st.markdown(
                """
                <div style="text-align: right;">
                    <!-- Use Streamlit form to capture this action properly -->
                </div>
                """, unsafe_allow_html=True
            )
            # Just standard button for now, styled via primary type
            run_diag = st.button("RUN DEEP DIAGNOSIS", type="primary", use_container_width=False)

        # Logic
        if run_diag:
             # Just like before
             days = 30 if "30" in time_scope else 60
             filtered_data = an.filter_data_by_range(errors, months=None) 
             cutoff = date.today() - pd.Timedelta(days=days)
             filtered_diag_data = [e for e in errors if datetime.strptime(e['date'], "%d-%m-%Y").date() >= cutoff]
             
             with st.spinner("Analyzing neural patterns..."):
                 diagnosis = an.generate_pattern_diagnosis(filtered_diag_data)
                 st.session_state.latest_diagnosis = diagnosis
                 st.session_state.diagnosis_date = time_scope

        # DISPLAY AREA
        if "latest_diagnosis" in st.session_state and st.session_state.get('diagnosis_date') == time_scope:
             # RENDER ACTIVE CARD (We'll reuse the style from before but refined)
             date_scope = st.session_state.get('diagnosis_date', 'Unknown')
             diagnosis_text = st.session_state.latest_diagnosis
             st.markdown(f"""
                 <div style="background-color: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 3rem; box-shadow: 0 10px 30px -10px rgba(0,0,0,0.08); margin-top: 1rem;">
                    <!-- Header -->
                    <div style="display:flex; justify-content:space-between; margin-bottom:2rem;">
                        <span style="background:#fef3c7; color:#d97706; font-weight:800; font-size:0.75rem; padding:6px 14px; border-radius:99px; text-transform:uppercase; letter-spacing:0.05em;">Neural Insight</span>
                        <span style="color:#94a3b8; font-weight:600; font-size:0.9rem;">{date_scope}</span>
                    </div>
                    <!-- Content -->
                    <div style="font-size:1.4rem; line-height:1.6; font-weight:500; color:#1e293b; font-family:'Helvetica Neue';">
                        {diagnosis_text}
                    </div>
                    <!-- Footer -->
                    <div style="margin-top:2.5rem; padding-top:2rem; border-top:1px solid #f1f5f9;">
                         <div style="font-size:0.8rem; text-transform:uppercase; color:#64748b; font-weight:700; letter-spacing:0.05em;">Diagnosis Confidence: <span style="color:#10b981;">98.2%</span></div>
                    </div>
                 </div>
             """, unsafe_allow_html=True)
        else:
            # IDLE STATE
            st.markdown("""
                <div class="dashed-container">
                    <div style="width:72px; height:72px; background:#f8fafc; border-radius:50%; display:flex; align-items:center; justify-content:center; margin-bottom:1.5rem;">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83"/></svg>
                    </div>
                    <h3 style="color:#0f172a; font-weight:700; font-size:1.5rem; margin:0 0 0.5rem 0;">Neural Link Idle</h3>
                    <p style="color:#64748b; max-width:400px; line-height:1.6;">Request a diagnosis to allow the AI to scan your recent error descriptions and performance trends.</p>
                </div>
            """, unsafe_allow_html=True)


    # ---------------------------------------------------------
    # 4. STUDY PLAN VIEW
    # ---------------------------------------------------------
    elif st.session_state.coach_view == "plan":
         st.markdown("""
            <div style="display:flex; justify-content:space-between; align-items:end; margin-bottom:2rem;">
                <div>
                    <h1 style="font-family:'Helvetica Neue'; font-weight:900; font-style:italic; font-size:3rem; letter-spacing:-0.04em; margin-bottom:0; line-height:1.1;">
                        STUDY PLAN
                    </h1>
                    <p style="color:#64748b; font-size:1.1rem; font-weight:500; margin-top:0.5rem;">
                        High-retention schedules mapping your path to mastery.
                    </p>
                </div>
            </div>
        """, unsafe_allow_html=True)
         
         # "Generate New Plan" Button (Top Right)
         c_main, c_new = st.columns([4, 1])
         with c_new:
             if st.button("+ GENERATE NEW PLAN", use_container_width=True):
                 st.session_state.show_config_modal = True
         
         # Logic for Modal
         if st.session_state.get("show_config_modal", False):
             # RENDER CONFIG FORM
             with st.container():
                 st.markdown("""
                    <div class="config-card">
                        <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:2rem;">
                             <h3 style="margin:0; font-weight:800; font-size:1.5rem;">CONFIGURATIONS</h3>
                        </div>
                 """, unsafe_allow_html=True)
                 
                 # 1. Exam Toggle
                 st.markdown("<label style='font-size:0.8rem; font-weight:700; color:#64748b; text-transform:uppercase;'>Do you have an upcoming exam?</label>", unsafe_allow_html=True)
                 has_exam = st.radio("Has Exam", ["YES", "NO, GENERAL GROWTH"], horizontal=True, label_visibility="collapsed")
                 
                 st.write("")
                 st.write("")
                 
                 # 2. Study Days (Standard Multi-Select or Styled Buttons)
                 st.markdown("<label style='font-size:0.8rem; font-weight:700; color:#64748b; text-transform:uppercase;'>Select Study Days</label>", unsafe_allow_html=True)
                 selected_days = st.pills("Days", ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"], selection_mode="multi", default=["MON", "WED", "FRI"])
                 
                 # 3. Exam Details (Conditional)
                 exam_config = {}
                 if has_exam == "YES":
                     st.write("")
                     c1, c2 = st.columns(2)
                     with c1:
                         sub = st.text_input("Subject", placeholder="e.g. Quantum Physics")
                     with c2:
                         dt = st.date_input("Exam Date")
                     
                     topics = st.text_area("Target Topics", placeholder="What specific topics will be covered?")
                     
                     exam_config = {
                         "has_exam": True, 
                         "subject": sub, 
                         "date": str(dt), 
                         "topics": topics,
                         "study_days": selected_days
                     }
                 else:
                     exam_config = {
                         "has_exam": False,
                         "study_days": selected_days
                     }
                     
                 st.write("")
                 st.write("")
                 
                 if st.button("GENERATE INTELLIGENCE PLAN", type="primary", use_container_width=True):
                      with st.spinner("Constructing tactical matrix..."):
                           plan = an.generate_tactical_plan(errors, exam_config)
                           st.session_state.tactical_plan = plan
                           st.session_state.show_config_modal = False # Close modal
                           st.rerun()
                           
                 st.markdown("</div>", unsafe_allow_html=True) # End card
         
         # ACTIVE PLAN DISPLAY
         if "tactical_plan" in st.session_state and not st.session_state.get("show_config_modal", False):
              plan_content = st.session_state.tactical_plan
              st.markdown(f"""
                 <div style="background-color: white; border: 1px solid #e2e8f0; border-radius: 16px; padding: 3rem; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); margin-top:2rem;">
                      <div style="font-family: 'Helvetica Neue', sans-serif; line-height: 1.8; color: #334155;">
                        {plan_content}
                      </div>
                 </div>
              """, unsafe_allow_html=True)
         elif not st.session_state.get("show_config_modal", False):
              # IDLE STATE
              st.markdown("""
                <div class="dashed-container">
                    <div style="width:72px; height:72px; background:#f8fafc; border-radius:50%; display:flex; align-items:center; justify-content:center; margin-bottom:1.5rem;">
                        <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#94a3b8" stroke-width="2"><rect x="3" y="4" width="18" height="18" rx="2" ry="2"></rect><line x1="16" y1="2" x2="16" y2="6"></line><line x1="8" y1="2" x2="8" y2="6"></line><line x1="3" y1="10" x2="21" y2="10"></line></svg>
                    </div>
                    <h3 style="color:#0f172a; font-weight:700; font-size:1.5rem; margin:0 0 0.5rem 0;">Awaiting Parameters</h3>
                    <p style="color:#64748b; max-width:400px; line-height:1.6;">Configure your exam details or weekly goals to generate a personalized trajectory.</p>
                </div>
            """, unsafe_allow_html=True)
elif menu == "History":
    st.empty()

