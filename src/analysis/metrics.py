"""
Metrics and aggregation functions for exam telemetry analysis.

Provides functions for counting, filtering, and aggregating error data,
study sessions, and mock exams to power dashboard visualizations and insights.
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from config import (
    DATE_FORMAT_DISPLAY,
    DAYS_PER_MONTH,
    AccuracyZone,
    PaceZone,
    get_pace_benchmark,
)

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


def count_difficulties(data: List[Dict[str, Any]]) -> Dict[str, int]:
    """
    Count errors grouped by difficulty level.

    Args:
        data: List of error records.

    Returns:
        Dictionary mapping difficulty level to count.
    """
    if not data:
        return {}

    difficulty_counts: Dict[str, int] = {}
    for error in data:
        difficulty = error.get("difficulty", "Medium") or "Medium"
        difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1

    return difficulty_counts


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


# =============================================================================
# STUDY SESSION METRICS
# =============================================================================


def analyze_session_performance(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Analyze session performance with classification zones.

    Args:
        sessions: List of study session records

    Returns:
        List of sessions enriched with performance classifications
    """
    analyzed = []

    for session in sessions:
        # Copy session data
        s = session.copy()

        # Extract metrics
        pace = s.get("pace_per_question", 0)
        accuracy = s.get("accuracy_percentage", 0)
        exam_type = s.get("exam_type", "General")

        # Get benchmark for this exam type
        benchmark = get_pace_benchmark(exam_type)

        # Classify pace
        s["pace_zone"] = PaceZone.classify(pace, benchmark)
        s["pace_benchmark"] = benchmark

        # Classify accuracy
        if accuracy >= AccuracyZone.MASTERY_THRESHOLD:
            s["accuracy_zone"] = "Mastery"
        elif accuracy >= AccuracyZone.DEVELOPING_THRESHOLD:
            s["accuracy_zone"] = "Developing"
        else:
            s["accuracy_zone"] = "Struggling"

        # Combined performance zone (for scatter plot quadrants)
        if s["pace_zone"] == "Rushing" and accuracy < AccuracyZone.DEVELOPING_THRESHOLD:
            s["performance_zone"] = "Rushing & Struggling"
        elif s["pace_zone"] == "Rushing" and accuracy >= AccuracyZone.MASTERY_THRESHOLD:
            s["performance_zone"] = "Rushing & Accurate (Risky)"
        elif s["pace_zone"] == "Optimal" and accuracy >= AccuracyZone.MASTERY_THRESHOLD:
            s["performance_zone"] = "Mastery Zone"
        elif (
            s["pace_zone"] == "Too Slow" and accuracy >= AccuracyZone.MASTERY_THRESHOLD
        ):
            s["performance_zone"] = "Slow but Accurate"
        else:
            s["performance_zone"] = "Needs Improvement"

        analyzed.append(s)

    return analyzed


def get_speed_accuracy_data(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepare data for speed vs accuracy scatter plot.

    Args:
        sessions: List of study session records

    Returns:
        List of data points with pace, accuracy, and metadata
    """
    scatter_data = []

    for session in sessions:
        pace = session.get("pace_per_question", 0)
        accuracy = session.get("accuracy_percentage", 0)
        subject = session.get("subject", "Unknown")
        exam_type = session.get("exam_type", "General")
        date_str = session.get("date", "")

        if pace > 0:  # Only include valid sessions
            scatter_data.append(
                {
                    "pace": round(pace, 2),
                    "accuracy": round(accuracy, 1),
                    "subject": subject,
                    "exam_type": exam_type,
                    "date": date_str,
                    "total_questions": session.get("total_questions", 0),
                }
            )

    return scatter_data


def calculate_session_statistics(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate aggregate statistics across all sessions.

    Args:
        sessions: List of study session records

    Returns:
        Dictionary with overall statistics
    """
    if not sessions:
        return {
            "total_sessions": 0,
            "total_questions": 0,
            "avg_accuracy": 0.0,
            "avg_pace": 0.0,
            "total_study_time": 0.0,
            "best_subject": "—",
            "improvement_needed": "—",
        }

    total_questions = sum(s.get("total_questions", 0) for s in sessions)
    total_correct = sum(s.get("correct_count", 0) for s in sessions)
    total_time = sum(s.get("duration_minutes", 0) for s in sessions)

    # Average accuracy (weighted by question count)
    avg_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0

    # Average pace
    avg_pace = (total_time / total_questions) if total_questions > 0 else 0

    # Best subject (highest accuracy)
    subject_stats: Dict[str, Dict[str, float]] = {}
    for s in sessions:
        subj = s.get("subject", "Unknown")
        if subj not in subject_stats:
            subject_stats[subj] = {"correct": 0, "total": 0}

        subject_stats[subj]["correct"] += s.get("correct_count", 0)
        subject_stats[subj]["total"] += s.get("total_questions", 0)

    best_subject = "—"
    best_acc = 0
    worst_subject = "—"
    worst_acc = 100

    for subj, stats in subject_stats.items():
        if stats["total"] > 0:
            acc = (stats["correct"] / stats["total"]) * 100
            if acc > best_acc:
                best_acc = acc
                best_subject = subj
            if acc < worst_acc:
                worst_acc = acc
                worst_subject = subj

    return {
        "total_sessions": len(sessions),
        "total_questions": total_questions,
        "avg_accuracy": round(avg_accuracy, 1),
        "avg_pace": round(avg_pace, 2),
        "total_study_time": round(total_time / 60, 1),  # Convert to hours
        "best_subject": best_subject,
        "improvement_needed": worst_subject if worst_acc < 60 else "—",
    }


# =============================================================================
# MOCK EXAM METRICS
# =============================================================================


def get_mock_exam_trajectory(mock_exams: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Prepare data for mock exam score trajectory chart.

    Args:
        mock_exams: List of mock exam records

    Returns:
        List sorted by date with attempt numbers
    """
    if not mock_exams:
        return []

    # Sort by date (oldest first for trajectory)
    sorted_exams = sorted(
        mock_exams, key=lambda x: parse_date_str(x.get("date", "")) or datetime.min
    )

    trajectory = []
    exam_type_counters: Dict[str, int] = {}

    for exam in sorted_exams:
        exam_type = exam.get("exam_type", "General")
        exam_name = exam.get("exam_name", "Untitled")
        score = exam.get("total_score", 0)
        max_score = exam.get("max_possible_score", 100)
        percentage = exam.get("score_percentage", 0)
        date_str = exam.get("date", "")

        # Track attempt number per exam type
        if exam_type not in exam_type_counters:
            exam_type_counters[exam_type] = 0
        exam_type_counters[exam_type] += 1

        trajectory.append(
            {
                "exam_type": exam_type,
                "exam_name": exam_name,
                "date": date_str,
                "score": round(score, 1),
                "max_score": round(max_score, 1),
                "percentage": round(percentage, 1),
                "attempt_number": exam_type_counters[exam_type],
            }
        )

    # Calculate improvement trends
    for i in range(1, len(trajectory)):
        if trajectory[i]["exam_type"] == trajectory[i - 1]["exam_type"]:
            prev_pct = trajectory[i - 1]["percentage"]
            curr_pct = trajectory[i]["percentage"]
            trajectory[i]["improvement"] = round(curr_pct - prev_pct, 1)
        else:
            trajectory[i]["improvement"] = None

    return trajectory


def calculate_mock_exam_statistics(mock_exams: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Calculate statistics for mock exams.

    Args:
        mock_exams: List of mock exam records

    Returns:
        Dictionary with mock exam statistics
    """
    if not mock_exams:
        return {
            "total_exams": 0,
            "avg_score": 0.0,
            "best_score": 0.0,
            "latest_score": 0.0,
            "trend": "—",
        }

    total_exams = len(mock_exams)
    avg_score = sum(e.get("score_percentage", 0) for e in mock_exams) / total_exams

    sorted_by_score = sorted(
        mock_exams, key=lambda x: x.get("score_percentage", 0), reverse=True
    )
    best_score = sorted_by_score[0].get("score_percentage", 0)

    # Latest exam
    sorted_by_date = sorted(
        mock_exams,
        key=lambda x: parse_date_str(x.get("date", "")) or datetime.min,
        reverse=True,
    )
    latest_score = sorted_by_date[0].get("score_percentage", 0)

    # Trend (compare latest vs average of previous)
    if total_exams >= 2:
        prev_avg = sum(e.get("score_percentage", 0) for e in sorted_by_date[1:]) / (
            total_exams - 1
        )

        if latest_score > prev_avg + 5:
            trend = "Improving"
        elif latest_score < prev_avg - 5:
            trend = "Declining"
        else:
            trend = "Stable"
    else:
        trend = "—"

    return {
        "total_exams": total_exams,
        "avg_score": round(avg_score, 1),
        "best_score": round(best_score, 1),
        "latest_score": round(latest_score, 1),
        "trend": trend,
    }


# =============================================================================
# VOLUME HEATMAP DATA
# =============================================================================


def get_activity_heatmap_data(
    sessions: List[Dict[str, Any]],
    errors: List[Dict[str, Any]],
    mock_exams: List[Dict[str, Any]],
    days: int = 180,
) -> List[Dict[str, Any]]:
    """
    Generate contribution-style heatmap data for study activity.

    Args:
        sessions: Study session records
        errors: Error records
        mock_exams: Mock exam records
        days: Number of days to include (default 180 = ~6 months)

    Returns:
        List of daily activity records
    """
    # Create date range
    end_date = date.today()
    start_date = end_date - timedelta(days=days)

    # Initialize daily counters
    activity_map: Dict[str, Dict[str, Any]] = {}
    current = start_date

    while current <= end_date:
        date_key = current.strftime("%Y-%m-%d")
        activity_map[date_key] = {
            "date": current.strftime(DATE_FORMAT_DISPLAY),
            "questions_answered": 0,
            "errors_logged": 0,
            "exams_taken": 0,
            "study_time": 0,
        }
        current += timedelta(days=1)

    # Aggregate sessions
    for session in sessions:
        dt = parse_date_str(session.get("date", ""))
        if dt and start_date <= dt.date() <= end_date:
            date_key = dt.strftime("%Y-%m-%d")
            activity_map[date_key]["questions_answered"] += session.get(
                "total_questions", 0
            )
            activity_map[date_key]["study_time"] += session.get("duration_minutes", 0)

    # Aggregate errors
    for error in errors:
        dt = parse_date_str(error.get("date", ""))
        if dt and start_date <= dt.date() <= end_date:
            date_key = dt.strftime("%Y-%m-%d")
            activity_map[date_key]["errors_logged"] += 1

    # Aggregate mock exams
    for exam in mock_exams:
        dt = parse_date_str(exam.get("date", ""))
        if dt and start_date <= dt.date() <= end_date:
            date_key = dt.strftime("%Y-%m-%d")
            activity_map[date_key]["exams_taken"] += 1

    # Convert to list and add intensity score
    heatmap_data = []
    for date_key in sorted(activity_map.keys()):
        day_data = activity_map[date_key]

        # Calculate intensity (0-4 scale like GitHub)
        questions = day_data["questions_answered"]
        if questions == 0:
            intensity = 0
        elif questions < 10:
            intensity = 1
        elif questions < 30:
            intensity = 2
        elif questions < 50:
            intensity = 3
        else:
            intensity = 4

        day_data["intensity"] = intensity
        day_data["date_key"] = date_key
        heatmap_data.append(day_data)

    return heatmap_data


# =============================================================================
# MOCK EXAM SECTION ANALYSIS
# =============================================================================


def extract_section_scores(
    mock_exams: List[Dict[str, Any]], exam_type: str
) -> List[Dict[str, Any]]:
    """
    Extract section-level scores from breakdown_json for charting.

    Args:
        mock_exams: List of mock exam records
        exam_type: Filter to this exam type

    Returns:
        List of dicts with section, score, max, percentage, exam_name, date
    """
    results = []
    filtered = [e for e in mock_exams if e.get("exam_type") == exam_type]

    for exam in filtered:
        breakdown = exam.get("breakdown_json") or {}
        if not isinstance(breakdown, dict):
            continue

        exam_name = exam.get("exam_name", "Untitled")
        date_str = exam.get("date", "")

        for key, sec_data in breakdown.items():
            # Skip non-section entries like tri_score, scaled_score
            if not isinstance(sec_data, dict) or "label" not in sec_data:
                continue

            score = sec_data.get("score", 0)
            max_val = sec_data.get("max", 1)
            pct = (score / max_val * 100) if max_val > 0 else 0

            results.append({
                "section": sec_data.get("label", key),
                "score": score,
                "max": max_val,
                "percentage": round(pct, 1),
                "exam_name": exam_name,
                "date": date_str,
            })

    return results


def get_section_trend_data(
    mock_exams: List[Dict[str, Any]], exam_type: str
) -> List[Dict[str, Any]]:
    """
    Get section scores over time for trend analysis.

    Args:
        mock_exams: List of mock exam records
        exam_type: Filter to this exam type

    Returns:
        List of dicts with section, percentage, date (sorted by date)
    """
    section_data = extract_section_scores(mock_exams, exam_type)
    if not section_data:
        return []

    # Sort by date
    sorted_data = sorted(
        section_data,
        key=lambda x: parse_date_str(x.get("date", "")) or datetime.min,
    )

    return sorted_data


def get_mock_exam_error_summary(
    errors: List[Dict[str, Any]],
    mock_exam_id: str,
    exam_date: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Group errors by subject for a specific mock exam.

    Includes both explicitly linked errors and errors from the same date.

    Args:
        errors: List of all error records
        mock_exam_id: The mock exam ID to filter by
        exam_date: Optional exam date (DD-MM-YYYY) for fallback matching

    Returns:
        Dictionary mapping subject -> list of error dicts
    """
    grouped: Dict[str, List[Dict[str, Any]]] = {}

    for error in errors:
        # Primary match: explicit mock_exam_id linkage
        if error.get("mock_exam_id") == mock_exam_id:
            subject = error.get("subject", "Unknown")
            if subject not in grouped:
                grouped[subject] = []
            grouped[subject].append(error)
        # Fallback match: same date if no mock_exam_id specified
        elif (
            not error.get("mock_exam_id")
            and exam_date
            and error.get("date") == exam_date
        ):
            subject = error.get("subject", "Unknown")
            if subject not in grouped:
                grouped[subject] = []
            grouped[subject].append(error)

    return grouped
