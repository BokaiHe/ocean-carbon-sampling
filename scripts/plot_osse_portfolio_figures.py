"""Create the three static portfolio figures for the global OSSE study."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.lines as mlines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['Arial', 'DejaVu Sans', 'Liberation Sans']
plt.rcParams['svg.fonttype'] = 'none'
plt.rcParams['pdf.fonttype'] = 42
plt.rcParams.update({'svg.fonttype': 'none', 'pdf.fonttype': 42})
plt.rcParams["font.size"] = 7
plt.rcParams["axes.linewidth"] = 0.8
plt.rcParams["axes.spines.top"] = False
plt.rcParams["axes.spines.right"] = False
plt.rcParams["legend.frameon"] = False
plt.rcParams["savefig.facecolor"] = "white"

ROOT = Path(__file__).resolve().parents[1]
PUBLIC = ROOT / "results" / "public"

COLORS = {
    "random": "#4D4D4D",
    "historical_density": "#D28E2C",
    "spatial_coverage": "#238B8E",
    "blue": "#3775BA",
    "violet": "#8C6BB1",
    "light_blue": "#E8F1F8",
    "light_teal": "#E3F2F0",
    "light_orange": "#F8EBD8",
    "line": "#626262",
    "grid": "#D9D9D9",
    "text": "#272727",
}

STRATEGY_LABELS = {
    "random": "Random",
    "historical_density": "Historical density",
    "spatial_coverage": "Spatial coverage",
}


def _save(fig: plt.Figure, stem: str) -> None:
    PUBLIC.mkdir(parents=True, exist_ok=True)
    fig.savefig(PUBLIC / f"{stem}.svg", facecolor="white")
    fig.savefig(PUBLIC / f"{stem}.pdf", facecolor="white")
    fig.savefig(PUBLIC / f"{stem}.png", dpi=600, facecolor="white")
    fig.savefig(PUBLIC / f"{stem}.tiff", dpi=600, facecolor="white")
    plt.close(fig)


def _panel_label(ax: plt.Axes, label: str) -> None:
    ax.text(
        -0.08,
        1.04,
        label,
        transform=ax.transAxes,
        fontsize=9,
        fontweight="bold",
        ha="left",
        va="bottom",
    )


def _box(
    ax: plt.Axes,
    xy: tuple[float, float],
    width: float,
    height: float,
    text: str,
    *,
    facecolor: str,
    edgecolor: str = "#666666",
    fontsize: float = 7,
    weight: str = "normal",
) -> None:
    patch = FancyBboxPatch(
        xy,
        width,
        height,
        boxstyle="round,pad=0.012,rounding_size=0.018",
        linewidth=0.8,
        edgecolor=edgecolor,
        facecolor=facecolor,
    )
    ax.add_patch(patch)
    ax.text(
        xy[0] + width / 2,
        xy[1] + height / 2,
        text,
        ha="center",
        va="center",
        fontsize=fontsize,
        color=COLORS["text"],
        fontweight=weight,
        linespacing=1.25,
    )


def _arrow(
    ax: plt.Axes,
    start: tuple[float, float],
    end: tuple[float, float],
    *,
    color: str = "#6B6B6B",
) -> None:
    ax.add_patch(
        FancyArrowPatch(
            start,
            end,
            arrowstyle="-|>",
            mutation_scale=9,
            linewidth=0.9,
            color=color,
            connectionstyle="arc3,rad=0",
        )
    )


def figure_design() -> None:
    fig, ax = plt.subplots(figsize=(7.2, 4.15))
    fig.subplots_adjust(left=0.025, right=0.985, bottom=0.045, top=0.965)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")

    ax.text(0.015, 0.955, "a", fontsize=9, fontweight="bold", va="top")
    ax.text(0.015, 0.505, "b", fontsize=9, fontweight="bold", va="top")
    ax.text(0.68, 0.505, "c", fontsize=9, fontweight="bold", va="top")

    _box(
        ax,
        (0.055, 0.71),
        0.19,
        0.18,
        "CMIP6 model ocean\nIPSL-CM6A-LR\n2005 | 2010 | 2014",
        facecolor=COLORS["light_blue"],
        edgecolor=COLORS["blue"],
        weight="bold",
    )
    _box(
        ax,
        (0.315, 0.71),
        0.19,
        0.18,
        "Monthly 1° fields\nspCO2 truth\nSST + salinity",
        facecolor="#F3F5F7",
    )
    _box(
        ax,
        (0.575, 0.71),
        0.19,
        0.18,
        "Locked split per year\n20% common evaluation\n80% acquisition pool",
        facecolor="#F2EDF7",
        edgecolor=COLORS["violet"],
    )
    _box(
        ax,
        (0.835, 0.71),
        0.12,
        0.18,
        "Target blind\nsampling\nfrom pool",
        facecolor=COLORS["light_teal"],
        edgecolor=COLORS["spatial_coverage"],
        weight="bold",
    )
    _arrow(ax, (0.247, 0.80), (0.312, 0.80))
    _arrow(ax, (0.507, 0.80), (0.572, 0.80))
    _arrow(ax, (0.767, 0.80), (0.832, 0.80))

    strategy_specs = [
        (
            0.055,
            "Random\nuniform without replacement",
            COLORS["random"],
            "#EEEEEE",
        ),
        (
            0.26,
            "Historical density\nSOCAT 1990-2004 weights",
            COLORS["historical_density"],
            COLORS["light_orange"],
        ),
        (
            0.465,
            "Spatial coverage\nmonth × 5° × 10° blocks",
            COLORS["spatial_coverage"],
            COLORS["light_teal"],
        ),
    ]
    for x, text, edge, fill in strategy_specs:
        _box(
            ax,
            (x, 0.32),
            0.17,
            0.13,
            text,
            facecolor=fill,
            edgecolor=edge,
            weight="bold",
            fontsize=6.5,
        )

    _box(
        ax,
        (0.70, 0.34),
        0.12,
        0.13,
        "Same locked model\nHistGradientBoosting\nSST, salinity, space, time",
        facecolor="#F3F5F7",
        weight="bold",
        fontsize=6.3,
    )
    _box(
        ax,
        (0.855, 0.34),
        0.11,
        0.13,
        "Common targets\nRMSE | median\np95 | p99",
        facecolor="#F2EDF7",
        edgecolor=COLORS["violet"],
        weight="bold",
        fontsize=6.3,
    )
    strategy_centres = (0.14, 0.345, 0.55)
    for x in strategy_centres:
        ax.plot([x, x], [0.32, 0.245], color="#777777", lw=0.8)
    ax.plot(
        [strategy_centres[0], 0.64],
        [0.245, 0.245],
        color="#777777",
        lw=0.8,
    )
    _arrow(ax, (0.64, 0.245), (0.70, 0.385))
    _arrow(ax, (0.822, 0.405), (0.852, 0.405))

    ax.text(
        0.055,
        0.10,
        "Fixed budgets: 500 | 1,000 | 2,500 | 5,000",
        fontsize=6.7,
        fontweight="bold",
        color=COLORS["text"],
    )
    ax.text(
        0.40,
        0.10,
        "20 paired seeds per year",
        fontsize=6.7,
        fontweight="bold",
        color=COLORS["text"],
    )
    ax.text(
        0.68,
        0.10,
        "Sensitivity: spCO2 ≤ 1,000 | native-area weighting",
        fontsize=6.7,
        fontweight="bold",
        color=COLORS["text"],
    )
    _save(fig, "fig1_osse_design")


def _validate_metrics(frame: pd.DataFrame) -> None:
    required = {
        "year",
        "evaluation_domain",
        "strategy",
        "budget",
        "seed",
        "rmse",
    }
    if required.difference(frame.columns):
        raise ValueError("cross-year metrics table is missing required columns")
    if len(frame) != 1440:
        raise ValueError(f"expected 1,440 metric rows, found {len(frame)}")
    counts = frame.groupby(
        ["year", "evaluation_domain", "strategy", "budget"]
    )["seed"].nunique()
    if not counts.eq(20).all():
        raise ValueError("each annual strategy-budget-domain group must have 20 seeds")


def figure_learning_curves(metrics: pd.DataFrame) -> None:
    _validate_metrics(metrics)
    source = metrics.loc[metrics["evaluation_domain"] == "all"].copy()
    summary = (
        source.groupby(["year", "strategy", "budget"], as_index=False)
        .agg(mean_rmse=("rmse", "mean"), sd_rmse=("rmse", "std"))
        .sort_values(["year", "strategy", "budget"])
    )
    budgets = [500, 1000, 2500, 5000]
    positions = np.arange(len(budgets))
    markers = {"random": "o", "historical_density": "s", "spatial_coverage": "^"}

    fig, axes = plt.subplots(1, 3, figsize=(7.2, 2.75), sharey=True)
    fig.subplots_adjust(left=0.085, right=0.985, bottom=0.22, top=0.80, wspace=0.16)
    for panel, (ax, year) in enumerate(zip(axes, (2005, 2010, 2014), strict=True)):
        for strategy in ("random", "historical_density", "spatial_coverage"):
            selected = summary.loc[
                (summary["year"] == year) & (summary["strategy"] == strategy)
            ].set_index("budget").loc[budgets]
            mean = selected["mean_rmse"].to_numpy()
            spread = selected["sd_rmse"].to_numpy()
            color = COLORS[strategy]
            ax.fill_between(
                positions,
                mean - spread,
                mean + spread,
                color=color,
                alpha=0.10,
                linewidth=0,
            )
            ax.plot(
                positions,
                mean,
                color=color,
                marker=markers[strategy],
                markersize=4,
                linewidth=1.5,
                markeredgecolor="white",
                markeredgewidth=0.5,
                label=STRATEGY_LABELS[strategy],
            )
        random_5000 = summary.loc[
            (summary["year"] == year)
            & (summary["strategy"] == "random")
            & (summary["budget"] == 5000),
            "mean_rmse",
        ].iloc[0]
        coverage_5000 = summary.loc[
            (summary["year"] == year)
            & (summary["strategy"] == "spatial_coverage")
            & (summary["budget"] == 5000),
            "mean_rmse",
        ].iloc[0]
        ax.annotate(
            f"Δ = {coverage_5000 - random_5000:+.2f}",
            xy=(3, coverage_5000),
            xytext=(2.05, coverage_5000 - 2.0),
            fontsize=6.2,
            color=COLORS["spatial_coverage"],
            arrowprops={
                "arrowstyle": "->",
                "lw": 0.7,
                "color": COLORS["spatial_coverage"],
            },
        )
        ax.set_title(str(year), fontsize=8, fontweight="bold", pad=5)
        ax.set_xticks(positions, ["500", "1k", "2.5k", "5k"])
        ax.set_xlabel("Observation budget")
        ax.set_ylim(20, 44)
        ax.set_yticks([20, 25, 30, 35, 40])
        ax.grid(axis="y", color=COLORS["grid"], linewidth=0.5, alpha=0.7)
        ax.tick_params(length=2.5, width=0.7)
        _panel_label(ax, chr(ord("a") + panel))
    axes[0].set_ylabel("Global RMSE (micro-atm)")
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(
        handles,
        labels,
        loc="upper center",
        bbox_to_anchor=(0.53, 0.97),
        ncol=3,
        handlelength=2.2,
        columnspacing=1.7,
    )
    fig.text(
        0.985,
        0.02,
        "Lines: mean; ribbons: ±1 seed SD; n = 20 paired seeds per year",
        ha="right",
        va="bottom",
        fontsize=6,
        color="#5F5F5F",
    )
    _save(fig, "fig2_cross_year_learning_curves")


def _forest_panel(
    ax: plt.Axes,
    source: pd.DataFrame,
    *,
    metric: str,
    title: str,
    xlim: tuple[float, float],
) -> None:
    selected = source.loc[source["metric"] == metric].sort_values("year")
    years = selected["year"].astype(str).tolist()
    estimates = selected["mean_difference"].to_numpy()
    lows = selected["seed_bootstrap_low"].to_numpy()
    highs = selected["seed_bootstrap_high"].to_numpy()
    y = np.arange(len(years))[::-1]
    ax.axvspan(xlim[0], 0, color=COLORS["light_teal"], zorder=0)
    ax.axvspan(0, xlim[1], color="#FAF1E6", zorder=0)
    ax.axvline(0, color="#666666", linestyle="--", linewidth=0.8)
    ax.hlines(y, lows, highs, color=COLORS["spatial_coverage"], linewidth=1.3)
    ax.scatter(
        estimates,
        y,
        s=24,
        color=COLORS["spatial_coverage"],
        edgecolor="white",
        linewidth=0.5,
        zorder=3,
    )
    ax.set_yticks(y, years)
    ax.set_xlim(*xlim)
    ax.set_ylim(-0.7, 2.7)
    ax.set_title(title, fontsize=7.5, fontweight="bold", pad=5)
    ax.set_xlabel("Coverage minus random (micro-atm)")
    ax.grid(axis="x", color=COLORS["grid"], linewidth=0.45, alpha=0.7)
    ax.tick_params(length=2.5, width=0.7)
    ax.text(
        0.02,
        0.04,
        "coverage better",
        transform=ax.transAxes,
        fontsize=5.6,
        color=COLORS["spatial_coverage"],
        ha="left",
    )
    ax.text(
        0.98,
        0.04,
        "random better",
        transform=ax.transAxes,
        fontsize=5.6,
        color="#9A651F",
        ha="right",
    )


def figure_tradeoff(
    paired_summary: pd.DataFrame, weighted_summary: pd.DataFrame
) -> None:
    required = {
        "year",
        "evaluation_domain",
        "budget",
        "comparison",
        "metric",
        "n_seeds",
        "mean_difference",
        "seed_bootstrap_low",
        "seed_bootstrap_high",
    }
    for frame in (paired_summary, weighted_summary):
        if required.difference(frame.columns):
            raise ValueError("paired summary table is missing required columns")
    source = paired_summary.loc[
        (paired_summary["evaluation_domain"] == "all")
        & (paired_summary["budget"] == 5000)
        & (paired_summary["comparison"] == "spatial_coverage_minus_random")
    ]
    if len(source) != 15 or not source["n_seeds"].eq(20).all():
        raise ValueError("expected five metrics for three years with 20 seeds")

    fig = plt.figure(figsize=(7.2, 5.05))
    grid = fig.add_gridspec(
        2,
        3,
        height_ratios=[1.0, 1.15],
        left=0.08,
        right=0.98,
        bottom=0.12,
        top=0.93,
        hspace=0.52,
        wspace=0.34,
    )
    axes = [fig.add_subplot(grid[0, index]) for index in range(3)]
    specs = [
        ("rmse", "RMSE", (-2.8, 0.8)),
        ("median_absolute_error", "Median absolute error", (-0.2, 1.1)),
        ("p99_absolute_error", "99th-percentile error", (-11.0, 1.5)),
    ]
    for panel, (ax, (metric, title, limits)) in enumerate(
        zip(axes, specs, strict=True)
    ):
        _forest_panel(ax, source, metric=metric, title=title, xlim=limits)
        _panel_label(ax, chr(ord("a") + panel))

    ax = fig.add_subplot(grid[1, :])
    keys = ["year", "evaluation_domain", "budget", "comparison", "metric"]
    merged = paired_summary.merge(
        weighted_summary,
        on=keys,
        how="inner",
        validate="one_to_one",
        suffixes=("_equal", "_area"),
    )
    rules = pd.DataFrame(
        [
            ("historical_density_minus_random", "rmse", "Historical - random RMSE"),
            ("spatial_coverage_minus_random", "rmse", "Coverage - random RMSE"),
            (
                "spatial_coverage_minus_random",
                "median_absolute_error",
                "Coverage - random median",
            ),
            (
                "spatial_coverage_minus_random",
                "p99_absolute_error",
                "Coverage - random p99",
            ),
        ],
        columns=["comparison", "metric", "effect_label"],
    )
    audit = merged.loc[
        (merged["evaluation_domain"] == "all") & (merged["budget"] == 5000)
    ].merge(rules, on=["comparison", "metric"], how="inner", validate="many_to_one")
    if len(audit) != 12:
        raise ValueError("expected 12 prespecified area-weighting audit effects")
    effect_colors = {
        "Historical - random RMSE": COLORS["historical_density"],
        "Coverage - random RMSE": COLORS["spatial_coverage"],
        "Coverage - random median": COLORS["violet"],
        "Coverage - random p99": COLORS["blue"],
    }
    year_markers = {2005: "o", 2010: "s", 2014: "^"}
    lower = min(
        audit["mean_difference_equal"].min(),
        audit["mean_difference_area"].min(),
    ) - 0.8
    upper = max(
        audit["mean_difference_equal"].max(),
        audit["mean_difference_area"].max(),
    ) + 0.8
    ax.plot([lower, upper], [lower, upper], color="#8B8B8B", lw=0.9, ls="--")
    for row in audit.itertuples(index=False):
        ax.scatter(
            row.mean_difference_equal,
            row.mean_difference_area,
            s=30,
            marker=year_markers[row.year],
            color=effect_colors[row.effect_label],
            edgecolor="white",
            linewidth=0.5,
            zorder=3,
        )
    ax.set_xlim(lower, upper)
    ax.set_ylim(lower, upper)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("Equal-weight effect (micro-atm)")
    ax.set_ylabel("Area-weighted effect (micro-atm)")
    ax.set_title(
        "Native-area weighting preserves all prespecified effects",
        fontsize=7.5,
        fontweight="bold",
        pad=5,
    )
    ax.grid(color=COLORS["grid"], linewidth=0.45, alpha=0.7)
    ax.text(
        -0.12,
        1.08,
        "d",
        transform=ax.transAxes,
        fontsize=9,
        fontweight="bold",
        ha="left",
        va="bottom",
    )
    effect_handles = [
        mlines.Line2D(
            [],
            [],
            marker="o",
            linestyle="none",
            markerfacecolor=color,
            markeredgecolor="none",
            markersize=5,
            label=label,
        )
        for label, color in effect_colors.items()
    ]
    year_handles = [
        mlines.Line2D(
            [],
            [],
            marker=marker,
            linestyle="none",
            markerfacecolor="#707070",
            markeredgecolor="none",
            markersize=5,
            label=str(year),
        )
        for year, marker in year_markers.items()
    ]
    ax.legend(
        handles=effect_handles + year_handles,
        loc="center left",
        bbox_to_anchor=(1.02, 0.5),
        fontsize=6,
        labelspacing=0.65,
        handletextpad=0.5,
    )
    fig.text(
        0.98,
        0.025,
        "Points: paired-seed mean; intervals: 95% percentile bootstrap; n = 20 seeds per year",
        ha="right",
        fontsize=6,
        color="#5F5F5F",
    )
    _save(fig, "fig3_error_tradeoff_and_robustness")


def main() -> None:
    metrics = pd.read_csv(PUBLIC / "osse_cross_year_metrics.csv")
    paired_summary = pd.read_csv(PUBLIC / "osse_cross_year_paired_summary.csv")
    weighted_summary = pd.read_csv(
        PUBLIC / "osse_regrid_audit_paired_summary.csv"
    )
    figure_design()
    figure_learning_curves(metrics)
    figure_tradeoff(paired_summary, weighted_summary)
    print("Saved three portfolio figures as SVG, PDF and 600-dpi PNG.")


if __name__ == "__main__":
    main()
