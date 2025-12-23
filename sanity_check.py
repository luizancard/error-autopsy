"""Lightweight sanity check for counts and optional AI calls.

Usage:
    python sanity_check.py          # runs counts only
    RUN_AI_SANITY=1 python sanity_check.py  # runs counts + AI outputs (requires GEMINI_API_KEY)
"""

import os

import analytics as anl
import database as db


def main():
    data = db.load_data()
    print("Loaded entries:", len(data))

    type_counts = anl.count_error_types(data)
    subject_counts = anl.count_subjects(data)
    topic_counts = anl.count_topics(data)
    month_counts = anl.count_entries_by_month(data)

    print("\nCounts by type:", type_counts)
    print("Counts by subject:", subject_counts)
    print("Counts by topic:", topic_counts)
    print("Counts by month:", month_counts)

    if os.getenv("RUN_AI_SANITY") == "1":
        print("\nRunning AI sanity (Gemini)...")
        anl.analyze_patterns(data)
        anl.study_plan(data)
    else:
        print("\nAI sanity skipped. Set RUN_AI_SANITY=1 to include Gemini calls.")


if __name__ == "__main__":
    main()
