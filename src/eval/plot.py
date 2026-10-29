"""Per-page CER distribution: one panel per document type, one column of dots per condition."""
import random
from pathlib import Path
from statistics import median

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402


def plot_page_cer(summary: dict, path: Path) -> None:
    """Each dot is one page's CER (mean of its images in that condition); the bar is the median."""
    types, conds = summary["doc_types"], summary["conditions"]
    fig, axes = plt.subplots(1, len(types), figsize=(3.2 * len(types), 3.6), sharey=True, squeeze=False)
    jitter = random.Random(253)
    for ax, t in zip(axes[0], types):
        for x, cond in enumerate(conds):
            vals = sorted(v for key, v in summary["page_cer"].items()
                          if key.split("|")[0] == cond and summary["page_types"][key.split("|")[1]] == t)
            if not vals:
                continue
            ax.scatter([x + jitter.uniform(-0.15, 0.15) for _ in vals], vals, s=14, alpha=0.7)
            ax.hlines(median(vals), x - 0.3, x + 0.3, colors="black", linewidth=1.5)
        flag = " (clean CER > 20%)" if t in summary["flagged_types"] else ""
        ax.set_title(f"{t}{flag}", fontsize=9)
        ax.set_xticks(range(len(conds)), conds, rotation=30, fontsize=8)
        ax.grid(axis="y", alpha=0.3)
    axes[0][0].set_ylabel("page CER")
    fig.suptitle("P0 per-page CER by condition (bar = median)", fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
