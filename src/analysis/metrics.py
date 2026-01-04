from datetime import date, datetime

RESET = "\033[0m"
RED = "\033[91m"


def count_error_types(data):
    if not data:
        print("No data to analyze yet.")
        return {}

    counts = {}
    for error in data:
        error_type = error.get("type", "Unknown")
        counts[error_type] = counts.get(error_type, 0) + 1

    return counts


def count_subjects(data):
    if not data:
        print("No data to analyze yet.")
        return {}

    subject_counts = {}
    for subj in data:
        raw_subject = subj.get("subject", "Unknown")
        subject = raw_subject.strip() if isinstance(raw_subject, str) else "Unknown"
        if not subject:
            subject = "Unknown"
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
    return subject_counts


def count_topics(data):
    if not data:
        print("No data to analyze yet.")
        return {}

    topic_counts = {}
    for top in data:
        raw_topic = top.get("topic", "Unknown")
        topic = raw_topic.strip() if isinstance(raw_topic, str) else "Unknown"
        if not topic:
            topic = "Unknown"
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    return topic_counts


def filter_data_by_range(data, months):
    """Filter data to only include entries from the last N months."""
    if not data:
        return []

    if months is None:  # "All time"
        return data

    now = datetime.now()

    filtered_data = []

    cutoff = None

    if months == 0:
        # Start of current month
        cutoff = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        days_back = months * 30
        from datetime import timedelta

        cutoff = now - timedelta(days=days_back)

    for item in data:
        raw_date = item.get("date")
        try:
            dt = datetime.strptime(raw_date, "%d-%m-%Y")
            if dt >= cutoff:
                filtered_data.append(item)
        except (TypeError, ValueError):
            continue
    return filtered_data


def count_entries_by_month(data):
    if not data:
        print("No data to analyze yet.")
        return {}

    counts = {}
    parse_error_logged = False
    for item in data:
        raw_date = item.get("date")  # sempre deve existir no seu fluxo
        try:
            dt = datetime.strptime(raw_date, "%d-%m-%Y")
            month_key = dt.strftime("%Y-%m")
        except (TypeError, ValueError):
            parse_error_logged = True
            continue

        counts[month_key] = counts.get(month_key, 0) + 1

    if parse_error_logged:
        print("Warning: Some entries had invalid dates and were skipped.")

    return counts


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
