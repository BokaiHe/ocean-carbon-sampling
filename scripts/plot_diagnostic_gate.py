"""Plot grouped-CV evidence used to accept or reject SHAP interpretation."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

COLORS = {"environment": "#8E989F", "full": "#3478A6"}
LABELS = {"environment": "Environment", "full": "Environment + location"}
TARGET_LABELS = {
    "mean_squared_error_gain": "a  Squared-error strategy effect",
    "mean_absolute_error_gain": "b  Absolute-error strategy effect",
}


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


def plot_target(axis: plt.Axes, metrics: pd.DataFrame, target: str) -> None:
    subset = metrics.loc[metrics["target"] == target].copy()
    for position, variant in enumerate(["environment", "full"]):
        values = subset.loc[
            (subset["model_variant"] == variant)
            & (subset["cv_fold"].astype(str) != "overall")
        ]
        offsets = np.linspace(-0.08, 0.08, len(values))
        axis.scatter(
            position + offsets,
            values["r2"],
            color=COLORS[variant],
            s=30,
            alpha=0.75,
            edgecolor="white",
            linewidth=0.4,
        )
        overall = subset.loc[
            (subset["model_variant"] == variant)
            & (subset["cv_fold"].astype(str) == "overall")
        ].iloc[0]
        axis.scatter(
            position,
            overall["r2"],
            color="#20262A",
            marker="D",
            s=48,
            zorder=3,
        )
        axis.text(
            position,
            overall["r2"] - 0.055,
            f"ρ = {overall['spearman']:.2f}",
            ha="center",
            va="top",
            fontsize=7,
        )
    axis.axhline(0, color="#60686E", linestyle="--", linewidth=0.9)
    axis.set_xticks([0, 1], [LABELS["environment"], LABELS["full"]])
    axis.set_ylabel("Spatial GroupKFold R²")
    axis.set_title(TARGET_LABELS[target], loc="left", weight="bold")
    axis.grid(axis="y", color="#D9DDE0", linewidth=0.6)


def make_figure(metrics: pd.DataFrame, output: Path) -> None:
    configure_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.3), constrained_layout=True)
    for axis, target in zip(axes, TARGET_LABELS, strict=True):
        plot_target(axis, metrics, target)
    fig.suptitle(
        "XGBoost does not generalize strategy benefit across spatial blocks",
        fontsize=11,
        weight="bold",
    )
    fig.supxlabel(
        "Colored points: five held-out group folds; black diamonds: pooled out-of-fold result",
        fontsize=7,
    )
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "diagnostic_interpretability_gate.png", dpi=300, bbox_inches="tight")
    fig.savefig(output / "diagnostic_interpretability_gate.tiff", dpi=600, bbox_inches="tight")
    fig.savefig(output / "diagnostic_interpretability_gate.svg", bbox_inches="tight")
    fig.savefig(output / "diagnostic_interpretability_gate.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    metrics = pd.read_csv(args.input / "diagnostic_group_cv.csv")
    make_figure(metrics, args.output)


if __name__ == "__main__":
    main()
