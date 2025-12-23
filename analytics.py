import os
from datetime import datetime

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
        subject = subj.get("subject", "Unknown")
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
    return subject_counts


def count_topics(data):
    if not data:
        print("No data to analyze yet.")
        return {}

    topic_counts = {}
    for top in data:
        topic = top.get("topic", "Unknown")
        topic_counts[topic] = topic_counts.get(topic, 0) + 1
    return topic_counts


def count_entries_by_month(data):
    if not data:
        print("No data to analyze yet.")
        return {}

    counts = {}
    for item in data:
        raw_date = item.get("date")  # sempre deve existir no seu fluxo
        try:
            dt = datetime.strptime(raw_date, "%d-%m-%Y")
            month_key = dt.strftime("%Y-%m")
        except (TypeError, ValueError):
            continue

        counts[month_key] = counts.get(month_key, 0) + 1

    return counts


# dashboard com os 4 graficos
def create_graphs(data):
    if not data:
        print("No data to visualize.")
        return

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

        labels = list(data_dict.keys())
        values = list(data_dict.values())

        ax.bar(labels, values, color=color, edgecolor="black", alpha=0.7)
        ax.set_title(title, fontweight="bold", fontsize=12)
        ax.set_ylabel("Count", fontsize=10)
        ax.tick_params(axis="x", rotation=45, labelsize=9)
        ax.grid(axis="y", alpha=0.3, linestyle="--")

    plt.tight_layout()  # ← Indentado (dentro da função)
    plt.savefig(
        "analytics_dashboard.png", dpi=300, bbox_inches="tight"
    )  # ← 'tight' não 'thigh'
    print("Dashboard saved as 'analytics_dashboard.png'!")
    plt.show()


def analyze_patterns(data):
    if not client:
        print(f"\n{RED}API Key missing. Cannot use AI analysis.{RESET}")
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

#Diagnosis:

(Identify the #1 pattern holding the student back BUT, also 
do a general anylisis of the patterns analyzed. Be direct.)

#The Neuroscience: 

(Explain in 1-2 sentences *why* this error happens. 
Use terms like 'Working Memory', 'Decision Fatigue', 'Encoding Failure', or 'Illusion of Competence'. Also state if the person is worse on a certain subject or topic or if they are well-rounded. Consider ALL the data provided.)

#The protocol:

(Give 2 strict (separate them with a blank), actionable, high-level techniques to fix this. NO GENERIC ADVICE like "sleep more" or "read carefully".)
(Examples of good advice: "Use the Feynman Technique," "Implement a Checklist for every question," "Do timed drills with 20% less time," "Mask the answers while reading.")

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

    print("\nThe AI is designing your 3-Day Sprint...\n")

    subject_counts = count_subjects(data)
    topic_counts = count_topics(data)
    error_type_counts = count_error_types(data)

    # Get top 3 weakest subjects and top 5 weakest topics
    top_weak_subjects = dict(
        sorted(subject_counts.items(), key=lambda item: item[1], reverse=True)[:3]
    )
    top_weak_topics = dict(
        sorted(topic_counts.items(), key=lambda item: item[1], reverse=True)[:5]
    )

    summary = {
        "total_errors": len(data),
        "priority_subjects": top_weak_subjects,
        "critical_topics": top_weak_topics,
        "error_types": error_type_counts,
        "timeline": count_entries_by_month(data),
    }

    # Create the comprehensive prompt for Gemini
    prompt = f"""You are an Elite Academic Tutor and Curriculum Designer for a high-achieving high school student. Your methodology is based on Active Recall, Spaced Repetition, and Pareto Efficiency (20% of effort for 80% of results).

STUDENT DATA (Weakest Areas Based on Error Logs):
- Total Errors Logged: {summary["total_errors"]}
- Priority Subjects (most errors): {summary["priority_subjects"]}
- Critical Topics (most errors): {summary["critical_topics"]}
- Error Type Breakdown: {summary["error_types"]}
- Timeline Pattern: {summary["timeline"]}

TASK:
Design a high-intensity "72-Hour Recovery Sprint" to fix these specific gaps based on the actual data provided.

RULES:
1. NO PASSIVE STUDYING. Do not suggest "reading notes" or "watching videos" unless followed immediately by a test.
2. ACTIVE RECALL ONLY. Suggest techniques like: "Blurting", "Feynman Technique", "Timed Drills", "Reverse Engineering Questions", "Past Paper Analysis".
3. BE SPECIFIC. Reference the exact subjects and topics from the input data.
4. DATA-DRIVEN. If error types show "Content Gap", focus on retrieval practice. If "Attention/Interpretation", focus on exam protocols. If "Time Management", focus on triage drills.

OUTPUT FORMAT (Markdown):

#Objective:
(1-2 sentences on what needs to be fixed based on the specific data patterns).

#The 72-hour protocol

**DAY 1: DIAGNOSIS & PATCHING (The "Feynman" Day)**
- (Specific actionable task for the #1 weakest subject with exact topic names)
- (Active recall technique for the #2 weakest area)
- (Self-testing protocol)

**DAY 2: GRIND & APPLICATION (The "Drill" Day)**
- (Specific timed practice instruction with subjects/topics from data)
- (Interleaving task mixing the weak subjects)
- (Error analysis checkpoint)

**DAY 3: SIMULATION (The "Exam" Day)**
- (Full simulation instructions mimicking real exam conditions)
- (Triage protocol if time management is an issue)
- (Post-exam error logging and pattern review)

#Success metrics: 
- (2-3 concrete ways to measure if the sprint worked)

Keep it strict, actionable, and data-specific. Max 500 words."""

    try:
        # Configure Gemini API with optimal settings
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config={
                "temperature": 0.6,  # Balanced for structured planning
                "max_output_tokens": 3000,  # Enough for detailed 3-day plan
                "top_p": 0.9,
                "top_k": 40,
            },
        )

        print("\n" + "=" * 80)
        print(response.text)
        print("=" * 80 + "\n")

    except Exception as e:
        print(f"\n{RED}Error calling Gemini API: {e}{RESET}")
