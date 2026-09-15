"""Generate the JCTC Table of Contents graphic in vector and raster formats."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Ellipse, FancyArrowPatch, FancyBboxPatch


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "paper"


def main() -> None:
    rng = np.random.default_rng(20260915)
    plt.rcParams.update({
        "font.family": "DejaVu Sans",
        "font.size": 7.5,
        "axes.linewidth": 0.7,
    })
    fig = plt.figure(figsize=(3.25, 1.75), facecolor="#fbfaf6")

    ax_left = fig.add_axes([0.04, 0.18, 0.40, 0.68])
    ax_left.set_xlim(0, 1)
    ax_left.set_ylim(0, 1)
    ax_left.axis("off")
    box = FancyBboxPatch(
        (0.01, 0.02), 0.96, 0.93,
        boxstyle="round,pad=0.02,rounding_size=0.035",
        facecolor="#eef5f4", edgecolor="#466b69", linewidth=0.8,
    )
    ax_left.add_patch(box)
    centers = np.array([[0.28, 0.66], [0.66, 0.63], [0.52, 0.30]])
    colors = ["#3b82a0", "#57a773", "#e58b3a"]
    for (cx, cy), color in zip(centers, colors):
        ax_left.add_patch(Ellipse((cx, cy), 0.30, 0.22, facecolor=color,
                                  edgecolor="white", linewidth=0.8, alpha=0.88))
        points = rng.normal((cx, cy), (0.065, 0.045), size=(32, 2))
        ax_left.scatter(points[:, 0], points[:, 1], s=2.5, color="#173b3f",
                        alpha=0.55, linewidths=0)
    ax_left.text(0.49, 0.91, "same landscape", ha="center", va="center",
                 color="#173b3f", weight="bold", fontsize=7.6)
    ax_left.text(0.49, 0.075, "more saved frames", ha="center", va="center",
                 color="#173b3f", fontsize=7.2)

    arrow = FancyArrowPatch(
        (0.455, 0.52), (0.545, 0.52), transform=fig.transFigure,
        arrowstyle="-|>", mutation_scale=12, linewidth=1.2, color="#e06b32",
    )
    fig.add_artist(arrow)

    ax = fig.add_axes([0.58, 0.22, 0.38, 0.61], facecolor="none")
    x = np.arange(5)
    selected = np.array([3.1, 4.2, 6.0, 8.6, 11.8])
    reference = np.repeat(3.0, len(x))
    ax.plot(x, selected, "o-", color="#d95f24", lw=1.8, ms=3.8,
            label="BIC-selected k")
    ax.plot(x, reference, "--", color="#2b7a78", lw=1.3,
            label="reference k")
    ax.fill_between(x, reference, selected, color="#f4b183", alpha=0.24)
    ax.set_xlim(-0.15, 4.15)
    ax.set_ylim(2, 13)
    ax.set_xticks([0, 4], ["low", "high"])
    ax.set_yticks([3, 8, 12])
    ax.set_xlabel("sampling budget", labelpad=1)
    ax.set_ylabel("state count", labelpad=1)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", color="#d8d5ce", linewidth=0.45, alpha=0.8)
    ax.legend(loc="upper left", frameon=False, fontsize=6.2,
              handlelength=1.5, borderaxespad=0.1)

    fig.text(0.5, 0.965, "More frames, more apparent states",
             ha="center", va="top", fontsize=8.2, weight="bold",
             color="#173b3f")

    fig.savefig(OUT / "toc_graphic.pdf", bbox_inches=None)
    fig.savefig(OUT / "toc_graphic.png", dpi=600, bbox_inches=None)
    plt.close(fig)


if __name__ == "__main__":
    main()
