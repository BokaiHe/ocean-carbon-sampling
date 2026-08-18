"""Plot five-fold spatial sensitivity and the held-out block geometry."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import Patch, Rectangle

FOLD_COLORS = ["#4C78A8", "#77A6C5", "#D18A49", "#9476A5", "#6E9C76"]


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


def plot_effects(
    axis: plt.Axes, paired: pd.DataFrame, fold_summary: pd.DataFrame
) -> None:
    rmse_summary = fold_summary.loc[fold_summary["metric"] == "rmse_gain"]
    for fold in range(5):
        values = paired.loc[paired["spatial_test_fold"] == fold].sort_values("seed")
        offsets = np.linspace(-0.15, 0.15, len(values))
        axis.scatter(
            fold + offsets,
            values["rmse_gain"],
            s=22,
            color=FOLD_COLORS[fold],
            alpha=0.72,
            edgecolor="white",
            linewidth=0.4,
            zorder=2,
        )
        estimate = rmse_summary.loc[
            rmse_summary["spatial_test_fold"] == fold
        ].iloc[0]
        axis.errorbar(
            fold,
            estimate["mean"],
            yerr=[
                [estimate["mean"] - estimate["ci_lower"]],
                [estimate["ci_upper"] - estimate["mean"]],
            ],
            fmt="D",
            markersize=5.5,
            color="#23282C",
            capsize=3,
            linewidth=1.3,
            zorder=3,
        )
    axis.axhline(0, color="#60686E", linestyle="--", linewidth=0.9)
    axis.set_xticks(range(5), [f"Fold {fold}" for fold in range(5)])
    axis.set_ylabel("RMSE gain, random − coverage (µatm)")
    axis.set_title("a  Coverage effect for every held-out fold", loc="left", weight="bold")
    axis.grid(axis="y", color="#D9DDE0", linewidth=0.6)
    axis.text(
        0.02,
        0.98,
        "n = 20 seeds per fold\nBlack marker: mean; bars: 95% seed-bootstrap interval",
        transform=axis.transAxes,
        va="top",
        fontsize=7,
    )


def plot_fold_map(axis: plt.Axes, blocks: pd.DataFrame) -> None:
    for row in blocks.itertuples(index=False):
        fold = int(row.spatial_fold)
        axis.add_patch(
            Rectangle(
                (
                    row.longitude_center - row.longitude_width / 2.0,
                    row.latitude_center - row.latitude_width / 2.0,
                ),
                row.longitude_width,
                row.latitude_width,
                facecolor=FOLD_COLORS[fold],
                edgecolor="white",
                linewidth=0.5,
            )
        )
    axis.set_xlim(-180, 180)
    axis.set_ylim(-80, -35)
    axis.set_xlabel("Longitude")
    axis.set_ylabel("Latitude")
    axis.set_title("b  Occupied pre-2020 validation blocks", loc="left", weight="bold")
    axis.legend(
        handles=[
            Patch(facecolor=FOLD_COLORS[fold], label=f"Fold {fold}")
            for fold in range(5)
        ],
        ncol=2,
        fontsize=7,
        loc="lower left",
    )


def make_figure(
    paired: pd.DataFrame,
    fold_summary: pd.DataFrame,
    blocks: pd.DataFrame,
    output: Path,
) -> None:
    configure_style()
    fig, axes = plt.subplots(
        1,
        2,
        figsize=(7.2, 3.6),
        constrained_layout=True,
        gridspec_kw={"width_ratios": [1.18, 1.0]},
    )
    plot_effects(axes[0], paired, fold_summary)
    plot_fold_map(axes[1], blocks)
    fig.suptitle(
        "Prediction gains depend on the held-out spatial region",
        fontsize=11,
        weight="bold",
    )
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "spatial_fold_sensitivity.png", dpi=300, bbox_inches="tight")
    fig.savefig(output / "spatial_fold_sensitivity.tiff", dpi=600, bbox_inches="tight")
    fig.savefig(output / "spatial_fold_sensitivity.svg", bbox_inches="tight")
    fig.savefig(output / "spatial_fold_sensitivity.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    paired = pd.read_csv(args.input / "spatial_sensitivity_paired_effects.csv")
    fold_summary = pd.read_csv(
        args.input / "spatial_sensitivity_fold_summary.csv"
    )
    blocks = pd.read_csv(args.input / "spatial_fold_blocks.csv")
    make_figure(paired, fold_summary, blocks, args.output)


if __name__ == "__main__":
    main()
