import os
from datetime import datetime
from textwrap import shorten

import matplotlib.pyplot as plt
from dotenv import load_dotenv
from google import genai

RESET = "\033[0m"
RED = "\033[91m"

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None


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


# dashboard com os 4 graficos
def create_graphs(data):
    if not data:
        print("No data to visualize.")
        return

    plt.style.use("seaborn-v0_8-whitegrid")

    # Coletar dados
    type_counts = count_error_types(data)
    subject_counts = count_subjects(data)
    topic_counts = count_topics(data)
    month_counts = count_entries_by_month(data)

    # Criar figura com 4 subplots (2x2)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Error Analysis Graphs", fontsize=16, fontweight="bold")

    # Dados para cada gráfico
    datasets = [
        (type_counts, "Error Types", axes[0, 0], "steelblue"),
        (subject_counts, "Subjects", axes[0, 1], "coral"),
        (topic_counts, "Topics", axes[1, 0], "mediumseagreen"),
        (month_counts, "Timeline (by Month)", axes[1, 1], "mediumpurple"),
    ]

    # Criar cada gráfico
    for data_dict, title, ax, color in datasets:
        if not data_dict:
            ax.text(0.5, 0.5, "No data", ha="center", va="center")
            ax.set_title(title, fontweight="bold")
            continue

        raw_labels = list(data_dict.keys())
        labels = [shorten(str(lbl), width=18, placeholder="...") for lbl in raw_labels]
        values = list(data_dict.values())

        bars = ax.bar(labels, values, color=color, edgecolor="black", alpha=0.8)
        ax.set_title(title, fontweight="bold", fontsize=12)
        ax.set_ylabel("Count", fontsize=10)
        ax.tick_params(axis="x", rotation=30, labelsize=9)
        ax.grid(axis="y", alpha=0.35, linestyle="--")

        # add bar labels and a bit of headroom
        max_val = max(values) if values else 0
        if max_val > 0:
            ax.set_ylim(0, max_val * 1.2)
        ax.bar_label(bars, fmt="%d", padding=3, fontsize=9)

    plt.tight_layout()  # ← Indentado (dentro da função)
    plt.savefig(
        "analytics_dashboard.png", dpi=300, bbox_inches="tight"
    )  # ← 'tight' não 'thigh'
    print("Dashboard saved as 'analytics_dashboard.png'!")
    plt.show()


def quick_summary(data):
    if not data:
        print("\nNo data to summarize. Log errors first.")
        return

    type_counts = count_error_types(data)
    subject_counts = count_subjects(data)
    topic_counts = count_topics(data)
    month_counts = count_entries_by_month(data)

    def print_block(title, counts):
        print(f"\n{title}:")
        if not counts:
            print("  (none)")
            return
        for k, v in sorted(counts.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {k}: {v}")

    print("\n=== Quick Summary ===")
    print_block("By Type", type_counts)
    print_block("By Subject", subject_counts)
    print_block("By Topic", topic_counts)
    print_block("By Month", month_counts)
    print("=====================\n")


def analyze_patterns(data):
    if not client:
        print(f"\n{RED}API Key missing. Cannot use AI analysis.{RESET}")
        return

    if not data:
        print("\nNo data to analyze yet. Log errors first.")
        return

    print("\nAI is analyzing your patterns...\n")

    summary = {
        "total_errors": len(data),
        "distribution_by_type": count_error_types(data),
        "distribution_by_subject": count_subjects(data),
        "distribution_by_topic": count_topics(data),
        "timeline_by_month": count_entries_by_month(data),
    }

    # Create the comprehensive prompt for Gemini
    prompt = f"""You are an elite performance psychologist and exam strategist for a high-achieving high school student. Your goal is NOT to motivate, but to optimize. You deal in efficiency and ROI (Return on Investment) of study time.

STUDENT ERROR DATA:
- Total Errors Logged: {summary["total_errors"]}
- Error Type Distribution: {summary["distribution_by_type"]}
- Subject Distribution: {summary["distribution_by_subject"]}
- Topic Distribution: {summary["distribution_by_topic"]}
- Timeline (by Month): {summary["timeline_by_month"]}

DIAGNOSTIC FRAMEWORK:
Analyze the 'distribution_by_type' to find the root failure point:
- High 'Content Gap': Diagnosis is PASSIVE STUDYING. The student is reading, not retrieving.
- High 'Attention Detail' / 'Interpretation': Diagnosis is COGNITIVE OVERLOAD or RUSHING. The student knows the content but lacks exam execution protocols.
- High 'Time Management': Diagnosis is POOR TRIAGE. The student is getting stuck on hard questions instead of maximizing points per minute.
- High 'Fatigue': Diagnosis is BIOLOGICAL. Sleep, hydration, or decision fatigue management is failing.

ADDITIONAL ANALYSIS REQUIREMENTS:
- Analyze ALL the data: subjects, topics, timeline patterns
- Identify if the student is weak in specific subjects/topics or well-rounded
- Look for temporal patterns (monthly trends, potential exam cycles)
- Consider the interplay between error types and subjects

OUTPUT FORMAT (Markdown):

###THE DIAGNOSIS
(Identify the #1 pattern holding the student back and provide a brief general analysis of the patterns.)

###THE NEUROSCIENCE
(Explain in 1-2 sentences *why* this error happens. Use terms like 'Working Memory', 'Decision Fatigue', 'Encoding Failure', or 'Illusion of Competence'. Also state if the person is worse on a certain subject or topic or if they are well-rounded. Consider ALL the data provided.)

### THE PROTOCOL
(Give 2 strict, actionable, high-level techniques to fix this. NO GENERIC ADVICE like "sleep more" or "read carefully".)
(Examples: "Use the Feynman Technique," "Implement a Checklist for every question," "Do timed drills with 20% less time," "Mask the answers while reading.")

Be brutally honest, data-driven, and specific. Focus on the highest-leverage changes."""

    try:
        # Configure Gemini API with optimal settings
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0.5,  # Lower for more focused, detailed analysis
                "max_output_tokens": 4000,  # Much more space for comprehensive output
                "top_p": 0.9,
                "top_k": 40,
            },
        )

        print("\n" + "-" * 80)
        print(response.text)
        print("-" * 80 + "\n")

    except Exception as e:
        print(f"\n{RED}Error calling Gemini API: {e}{RESET}")


def study_plan(data):
    if not client:
        print(f"\n{RED}API Key missing. Cannot use AI analysis.{RESET}")
        return

    if not data:
        print("\nNo data to analyze yet. Log errors first.")
        return

    print("\nThe AI is designing your study plan...\n")

    # Optional exam targeting inputs
    target_exam = (
        input("Do you have an upcoming exam to target? (y/n): ").strip().lower()
    )
    days_until_exam = None
    exam_subjects = []
    exam_topics = []

    if target_exam == "y":
        raw_days = input("How many days until the exam? (number): ").strip()
        try:
            days_until_exam = int(raw_days) if raw_days else None
        except ValueError:
            days_until_exam = None
        exam_subjects = [
            s.strip()
            for s in input("List subjects to be covered (comma-separated): ").split(",")
            if s.strip()
        ]
        exam_topics = [
            t.strip()
            for t in input("List topics to be covered (comma-separated): ").split(",")
            if t.strip()
        ]

        print("\nCaptured exam inputs:")
        print("- Targeting exam: True")
        print(f"- Days until exam: {days_until_exam}")
        subjects_display = (
            ", ".join([s.capitalize() for s in exam_subjects])
            if exam_subjects
            else "(none)"
        )
        topics_display = (
            ", ".join([t.capitalize() for t in exam_topics])
            if exam_topics
            else "(none)"
        )
        print(f"- Exam subjects: {subjects_display}")
        print(f"- Exam topics: {topics_display}")
        print("\n\n Please wait, generating study plan... ")
    else:
        print("\nNo specific exam provided. \nCreating a general improvement plan...")

    subject_counts = count_subjects(data)
    topic_counts = count_topics(data)
    error_type_counts = count_error_types(data)

    # recency weighting: last 30 days get highlighted
    recent_window_days = 30
    now = datetime.now()
    recent_subjects = {}
    recent_topics = {}
    for item in data:
        raw_date = item.get("date")
        try:
            dt = datetime.strptime(raw_date, "%d-%m-%Y")
            if (now - dt).days <= recent_window_days:
                subj = item.get("subject", "Unknown") or "Unknown"
                top = item.get("topic", "Unknown") or "Unknown"
                recent_subjects[subj] = recent_subjects.get(subj, 0) + 1
                recent_topics[top] = recent_topics.get(top, 0) + 1
        except Exception:
            continue

    # Get top 3 weakest subjects and top 5 weakest topics (overall)
    top_weak_subjects = dict(
        sorted(subject_counts.items(), key=lambda item: item[1], reverse=True)[:3]
    )
    top_weak_topics = dict(
        sorted(topic_counts.items(), key=lambda item: item[1], reverse=True)[:5]
    )

    top_error_type = None
    if error_type_counts:
        top_error_type = max(error_type_counts.items(), key=lambda x: x[1])

    summary = {
        "total_errors": len(data),
        "priority_subjects": top_weak_subjects,
        "critical_topics": top_weak_topics,
        "error_types": error_type_counts,
        "top_error_type": top_error_type,
        "timeline": count_entries_by_month(data),
        "recent_subjects": recent_subjects,
        "recent_topics": recent_topics,
        "recent_window_days": recent_window_days,
        "target_exam": target_exam == "y",
        "days_until_exam": days_until_exam,
        "exam_subjects": exam_subjects,
        "exam_topics": exam_topics,
    }

    # Create the comprehensive prompt for Gemini
    prompt = f"""You are an Elite Academic Tutor and Curriculum Designer for a high-achieving high school student. Your methodology is based on Active Recall, Spaced Repetition, and Pareto Efficiency (20% of effort for 80% of results).

STUDENT DATA (Weakest Areas Based on Error Logs):
- Total Errors Logged: {summary["total_errors"]}
- Priority Subjects (most errors, highest weight): {summary["priority_subjects"]}
- Critical Topics (most errors, highest weight): {summary["critical_topics"]}
- Error Type Breakdown: {summary["error_types"]}
- Top Error Type: {summary["top_error_type"]}
- Timeline Pattern: {summary["timeline"]}
- Recent emphasis (last {summary["recent_window_days"]} days): subjects {summary["recent_subjects"]}, topics {summary["recent_topics"]}

EXAM CONTEXT (user-provided, if any):
- Targeting specific upcoming exam: {summary["target_exam"]}
- Days until exam: {summary["days_until_exam"]}
- Exam subjects: {summary["exam_subjects"]}
- Exam topics: {summary["exam_topics"]}

TASK:
Design a customized study plan that prioritizes SUBJECTS and TOPICS above all else, and gives extra weight to the most recent errors. If an upcoming exam is specified, tailor the plan to the remaining days. If no exam is specified, provide a general improvement plan.

RULES:
1. NO PASSIVE STUDYING. Do not suggest "reading notes" or "watching videos" unless followed immediately by a test.
2. ACTIVE RECALL ONLY. Techniques: "Blurting", "Feynman Technique", "Timed Drills", "Reverse Engineering Questions", "Past Paper Analysis".
3. HEAVY WEIGHT ON SUBJECTS/TOPICS. Always anchor tasks to the listed subjects and topics; they have the highest priority.
4. RECENCY PRIORITY. Errors closer to today (last {summary["recent_window_days"]} days) should get extra attention.
5. TIME MANAGEMENT TRIAGE. If Time management is the top error type, include aggressive triage protocols (90-second scan, tag easy/medium/hard, enforced skips/returns, timeboxes).
6. FLEXIBLE DURATION. If days_until_exam is provided, create a day-by-day plan up to that date. Otherwise, propose a repeatable weekly cycle.

OUTPUT FORMAT (Markdown):

###OBJECTIVE
(1-2 sentences on what needs to be fixed, prioritizing subjects/topics and recent errors. If an exam is provided, mention the goal relative to the exam date.)

###PLAN STRUCTURE
- If days_until_exam provided: outline the day-by-day arc until the exam, with heavier focus on listed subjects/topics and recent weak areas.
- If no exam: propose a 5-7 day repeatable loop balancing retrieval, drills, and simulation.

###DAILY / SESSION BLOCKS
- (Concrete blocks anchored to the specific subjects/topics above; include timed drills, interleaving, and self-testing.)
- (If Time management is top error type, embed triage drills and strict timing.)

###SIMULATION & REVIEW
- (Exam-mode simulations if days_until_exam is given; otherwise weekly mock sets.)
- (Error logging + rapid post-mortem instructions.)

###SUCCESS METRICS
- (2-3 measurable checks: e.g., accuracy on targeted topics, time-per-question, retrieval success rate.)

Keep it strict, actionable, and data-specific. Max 500 words."""

    try:
        # Configure Gemini API with optimal settings
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0.6,  # Balanced for structured planning
                "max_output_tokens": 3200,  # Enough for detailed plan
                "top_p": 0.9,
                "top_k": 40,
            },
        )

        print("\n" + "-" * 80)
        print(response.text)
        print("-" * 80 + "\n")

    except Exception as e:
        print(f"\n{RED}Error calling Gemini API: {e}{RESET}")
