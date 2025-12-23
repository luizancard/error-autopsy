import os
from datetime import datetime

import matplotlib.pyplot as plt
from dotenv import load_dotenv
from google import genai

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
def create_analytics_dashboard(data):
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
