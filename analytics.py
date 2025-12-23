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

    print("\n AI is analyzing your patterns...\n")

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

Diagnosis:
(Identify the #1 pattern holding the student back BUT, also do a general anylisis of the patterns analyzed. Be direct.)

The Neuroscience: 
(Explain in 1-2 sentences *why* this error happens. Use terms like 'Working Memory', 'Decision Fatigue', 'Encoding Failure', or 'Illusion of Competence'. Also state if the person is worse on a certain subject or topic or if they are well-rounded. Consider ALL the data provided.)

The protocol:
(Give 2 strict, actionable, high-level techniques to fix this. NO GENERIC ADVICE like "sleep more" or "read carefully".)
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
