import os

from dotenv import load_dotenv
from google import genai

from analysis import metrics as mt

RESET = "\033[0m"
RED = "\033[91m"


load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if api_key:
    client = genai.Client(api_key=api_key)
else:
    client = None


def analyze_patterns(data):
    if not client:
        print(f"\n{RED}API Key missing. Cannot use AI analysis.{RESET}")
        return

    if not data:
        print("\nNo data to analyze yet. Log errors first.")
        return

    summary = {
        "total_errors": len(data),
        "distribution_by_type": mt.count_error_types(data),
        "distribution_by_subject": mt.count_subjects(data),
        "distribution_by_topic": mt.count_topics(data),
        "timeline_by_month": mt.count_entries_by_month(data),
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
        print("\nPlease wait, generating the analisis...\n")
        # Configure Gemini API with optimal settings
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0.5,  # Lower for more focused, detailed analysis
                "max_output_tokens": 3000,  # Much more space for comprehensive output
                "top_p": 0.9,
                "top_k": 40,
            },
        )

        print("\n" + "-" * 80)
        print(response.text)
        print("-" * 80 + "\n")

    except Exception as e:
        print(f"\n{RED}Error calling Gemini API: {e}{RESET}")


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


def generate_pattern_diagnosis(data):
    """Generates a deep psychological diagnosis of error patterns."""
    if not client or not data:
        return "System Idle: Log errors to enable pattern recognition."

    intro_prompt = (
        """
    You are an elite Cognitive Performance Coach. 
    Analyze the provided error log to identify the **Root Psychological Cause** of the user's mistakes.
    
    DATA:
    """
        + str(data)
        + """
    
    GOAL:
    Write a COMPREHENSIVE psychological analysis (approx 150-200 words).
    - Do NOT stop at 1-2 sentences. Expound on the behavior.
    - Identify the #1 behavioral pattern and explain the cognitive mechanism (e.g. "Associative Interference", "Decision Fatigue").
    - Connect the specific subjects/topics to the error types.
    - **CRITICAL: Ensure the response is complete and does not cut off mid-sentence.**
    
    FORMATTING RULES:
    1. Output **HTML** only. Use <b>text</b> for emphasis.
    2. DO NOT use Markdown.
    3. Return a single, well-structured paragraph.
    
    Tone: Surgical, professional, high-performance.
    """
    )

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=intro_prompt,
            config={"temperature": 0.7, "max_output_tokens": 3000},
        )
        return response.text
    except Exception as e:
        return f"Diagnosis unavailable: {str(e)}"


def generate_tactical_plan(data, exam_config=None):
    """Generates a structured study plan based on exam config or general growth."""
    if not client:
        return "AI Module Offline."

    # context construction
    if exam_config and exam_config.get("has_exam"):
        mode = "TARGETED BLITZ"
        focus = f"Exam on {exam_config.get('date')} for Subject: {exam_config.get('subject')} covering {exam_config.get('topics')}."
    else:
        mode = "GENERAL GROWTH"
        focus = "Long-term mastery and error reduction."

    study_days = "Mon, Tue, Wed, Thu, Fri, Sat, Sun"
    if exam_config and exam_config.get("study_days"):
        study_days = ", ".join(exam_config.get("study_days"))

    prompt = f"""
    You are a Tactical Study Strategist. Create a 'High-Leverage Focus Plan'.
    
    MODE: {mode}
    FOCUS: {focus}
    AVAILABLE STUDY DAYS: {study_days}
    RECENT ERROR DATA COUNT: {len(data) if data else 0}
    
    TASK:
    Create a daily routine matrix (Morning, Midday, Evening) ONLY for the selected Available Study Days ({study_days}).
    If ({study_days}) does not include all 7 days, generate a plan ONLY for those days.

    1. **Morning (Retrieval)**: Active recall tasks specific to the user's weak topics.
    2. **Midday (Execution)**: Timed practice or simulation.
    3. **Evening (Synthesis)**: Review and error autopsy.
    
    Output Format:
    Return in Markdown. Use headers for blocks (### Morning 01).
    Keep it concise. If specific error topics exists in the data, PRIORTIZE them in the plan.
    """

    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={"temperature": 0.8, "max_output_tokens": 500},
        )
        return response.text
    except Exception as e:
        return f"Plan generation failed: {str(e)}"


'''
def study_plan(data):
    return generate_tactical_plan(data)

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

    subject_counts = mt.count_subjects(data)
    topic_counts = mt.count_topics(data)
    error_type_counts = mt.count_error_types(data)

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
        "timeline": mt.count_entries_by_month(data),
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
'''
