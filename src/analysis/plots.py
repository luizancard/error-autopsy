from textwrap import shorten

import matplotlib.pyplot as plt

from analysis import metrics as mt


def create_graphs(data):
    if not data:
        print("No data to visualize.")
        return

    plt.style.use("seaborn-v0_8-whitegrid")

    # Coletar dados
    type_counts = mt.count_error_types(data)
    subject_counts = mt.count_subjects(data)
    topic_counts = mt.count_topics(data)
    month_counts = mt.count_entries_by_month(data)

    # Criar figura com 4 subplots (2x2)
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Error Analysis Graphs", fontsize=16, fontweight="bold")

    # Dados para cada gráfico
    datasets = [
        (type_counts, "Error Types", axes[0, 0], "#6366f1"),
        (subject_counts, "Subjects", axes[0, 1], "#6366f1"),
        (topic_counts, "Topics", axes[1, 0], "#6366f1"),
        (month_counts, "Timeline (by Month)", axes[1, 1], "#6366f1"),
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
