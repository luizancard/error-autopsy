from datetime import datetime

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
