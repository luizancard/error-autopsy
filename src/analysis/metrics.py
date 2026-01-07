"""
Metrics and aggregation functions for error analysis.

Provides functions for counting, filtering, and aggregating error data
to power dashboard visualizations and insights.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from config import DATE_FORMAT_DISPLAY, DAYS_PER_MONTH

logger = logging.getLogger(__name__)


def count_error_types(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count errors grouped by error type.

    Args:
        data: List of error records.

    Returns:
        Dictionary mapping error type to count.
    """
    if not data:
        return {}

    counts: Dict[str, int] = {}
    for error in data:
        error_type = error.get("type", "Unknown")
        counts[error_type] = counts.get(error_type, 0) + 1

    return counts


def count_subjects(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count errors grouped by subject.

    Args:
        data: List of error records.

    Returns:
        Dictionary mapping subject to count.
    """
    if not data:
        return {}

    subject_counts: Dict[str, int] = {}
    for subj in data:
        raw_subject = subj.get("subject", "Unknown")
        subject = raw_subject.strip() if isinstance(raw_subject, str) else "Unknown"
        if not subject:
            subject = "Unknown"
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
    return subject_counts


def count_topics(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count errors grouped by topic.

    Args:
        data: List of error records.

    Returns:
        Dictionary mapping topic to count.
    """
    if not data:
        return {}

    topic_counts: Dict[str, int] = {}
    for top in data:
        raw_topic = top.get("topic", "Unknown")
        topic = raw_topic.strip() if isinstance(raw_topic, str) else "Unknown"
        if not topic:
            topic = "Unknown"
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    return topic_counts


def filter_data_by_range(
    data: List[Dict[str, Any]], months: Optional[int]
) -> List[Dict[str, Any]]:
    """
    Filter data to include only entries from the last N months.

    Args:
        data: List of error records.
        months: Number of months to look back. None means all time.
                0 means current month only.

    Returns:
        Filtered list of error records.
    """
    if not data:
        return []

    if months is None:
        return data

    now = datetime.now()

    if months == 0:
        cutoff = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    else:
        days_back = months * DAYS_PER_MONTH
        cutoff = now - timedelta(days=days_back)

    filtered_data = []
    for item in data:
        raw_date = item.get("date")
        if not raw_date:
            continue
        try:
            dt = datetime.strptime(raw_date, DATE_FORMAT_DISPLAY)
            if dt >= cutoff:
                filtered_data.append(item)
        except (TypeError, ValueError):
            continue
    return filtered_data


def count_entries_by_month(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count errors grouped by month.

    Args:
        data: List of error records.

    Returns:
        Dictionary mapping month (YYYY-MM) to count.
    """
    if not data:
        return {}

    counts: Dict[str, int] = {}
    for item in data:
        raw_date = item.get("date")
        if not raw_date:
            continue
        try:
            dt = datetime.strptime(raw_date, DATE_FORMAT_DISPLAY)
            month_key = dt.strftime("%Y-%m")
        except (TypeError, ValueError):
            logger.debug(f"Invalid date format: {raw_date}")
            continue

        counts[month_key] = counts.get(month_key, 0) + 1

    return counts


def parse_date_str(d: str) -> Optional[datetime]:
    """
    Parse date string in display format.

    Args:
        d: Date string in DD-MM-YYYY format.

    Returns:
        Datetime object or None if parsing fails.
    """
    try:
        return datetime.strptime(d, DATE_FORMAT_DISPLAY)
    except Exception:
        return None


def current_and_last_month_refs(
    ref: date,
) -> tuple[tuple[int, int], tuple[int, int]]:
    """
    Get year/month tuples for current and previous month.

    Args:
        ref: Reference date to calculate from.

    Returns:
        Tuple of (current_year, current_month), (last_year, last_month).
    """
    first_this = ref.replace(day=1)
    last_month_last_day = first_this - date.resolution
    first_last = last_month_last_day.replace(day=1)
    return (first_this.year, first_this.month), (first_last.year, first_last.month)


def aggregate_monthly_stats(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate monthly statistics comparing current vs previous month.

    Args:
        data: List of error records.

    Returns:
        Dictionary with current_total, delta percentage, top_subject, and top_type.
    """
    today = date.today()
    (cy, cm), (ly, lm) = current_and_last_month_refs(today)

    def month_key(dt_obj: datetime) -> tuple[int, int]:
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


def aggregate_by_topic(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count errors grouped by topic.

    Args:
        data: List of error records.

    Returns:
        Dictionary mapping topic names to error counts.
    """
    topic_counts: Dict[str, int] = {}
    for row in data:
        topic = row.get("topic", "Unknown") or "Unknown"
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    return topic_counts


def aggregate_by_subject(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count errors grouped by subject.

    Args:
        data: List of error records.

    Returns:
        Dictionary mapping subject names to error counts.
    """
    subject_counts: Dict[str, int] = {}
    for row in data:
        subj = row.get("subject", "Unknown") or "Unknown"
        subject_counts[subj] = subject_counts.get(subj, 0) + 1
    return subject_counts


def aggregate_by_month_all(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count errors grouped by month label.

    Args:
        data: List of error records.

    Returns:
        Dictionary mapping month labels (e.g., "Dec 2025") to counts.
    """
    month_counts: Dict[str, int] = {}
    for row in data:
        dt = parse_date_str(row.get("date", ""))
        if dt:
            month_str = dt.strftime("%b %Y")
            month_counts[month_str] = month_counts.get(month_str, 0) + 1
    return month_counts
