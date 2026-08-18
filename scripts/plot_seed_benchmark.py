"""Plot seed-level paired effects from the regional sampling benchmark."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COLORS = {"temporal": "#4C82A8", "spatial": "#D18A49"}
LABELS = {"temporal": "Temporal holdout", "spatial": "Spatial holdout"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path("results/public"))
    parser.add_argument("--output", type=Path, default=Path("results/public"))
    return parser.parse_args()


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.8,
            "legend.frameon": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )


def plot_metric(
    axis: plt.Axes,
    paired: pd.DataFrame,
    summary: pd.DataFrame,
    *,
    metric: str,
    ylabel: str,
    title: str,
) -> None:
    for position, regime in enumerate(["temporal", "spatial"]):
        values = paired.loc[paired["regime"] == regime].sort_values("seed")
        offsets = np.linspace(-0.16, 0.16, len(values))
        axis.scatter(
            position + offsets,
            values[metric],
            s=24,
            color=COLORS[regime],
            alpha=0.72,
            edgecolor="white",
            linewidth=0.4,
            zorder=2,
        )
        estimate = summary.loc[
            (summary["regime"] == regime) & (summary["metric"] == metric)
        ].iloc[0]
        axis.errorbar(
            position,
            estimate["mean"],
            yerr=[
                [estimate["mean"] - estimate["ci_lower"]],
                [estimate["ci_upper"] - estimate["mean"]],
            ],
            fmt="D",
            markersize=6,
            color="#23282C",
            capsize=4,
            linewidth=1.4,
            zorder=3,
        )
    axis.axhline(0, color="#60686E", linestyle="--", linewidth=0.9)
    axis.set_xticks([0, 1], [LABELS["temporal"], LABELS["spatial"]])
    axis.set_ylabel(ylabel)
    axis.set_title(title, loc="left", weight="bold")
    axis.grid(axis="y", color="#D9DDE0", linewidth=0.6)


def make_figure(paired: pd.DataFrame, summary: pd.DataFrame, output: Path) -> None:
    configure_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.4), constrained_layout=True)
    plot_metric(
        axes[0],
        paired,
        summary,
        metric="rmse_gain",
        ylabel="RMSE gain, random − coverage (µatm)",
        title="a  Predictive effect across seeds",
    )
    plot_metric(
        axes[1],
        paired,
        summary,
        metric="cell_cv_reduction",
        ylabel="Reduction in coverage-cell count CV",
        title="b  Geographic-balance effect across seeds",
    )
    fig.suptitle(
        "Coverage improves mean RMSE and geographic balance across seeds",
        fontsize=11,
        weight="bold",
    )
    fig.supxlabel(
        "Dots: prespecified seeds; diamonds: means; bars: 95% seed-bootstrap intervals",
        fontsize=7,
    )
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "seed_benchmark_effects.png", dpi=300, bbox_inches="tight")
    fig.savefig(output / "seed_benchmark_effects.tiff", dpi=600, bbox_inches="tight")
    fig.savefig(output / "seed_benchmark_effects.svg", bbox_inches="tight")
    fig.savefig(output / "seed_benchmark_effects.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    paired = pd.read_csv(args.input / "benchmark_paired_effects.csv")
    summary = pd.read_csv(args.input / "benchmark_summary.csv")
    make_figure(paired, summary, args.output)


if __name__ == "__main__":
    main()
