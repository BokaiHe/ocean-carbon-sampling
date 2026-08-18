"""Create curated SOCAT coverage summaries and the first project figure."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from ocean_carbon_sampling.data import read_socat_monthly, select_southern_ocean
from ocean_carbon_sampling.splits import add_spatial_folds, add_validation_regimes

PALETTE = {
    "navy": "#315A7D",
    "blue": "#76A5C4",
    "orange": "#D98C4A",
    "gray": "#A8ADB3",
    "dark": "#2D3439",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("path", type=Path)
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


def build_summaries(frame: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    annual = (
        frame.assign(year=frame["date"].dt.year)
        .groupby("year", as_index=False)
        .size()
        .rename(columns={"size": "rows"})
    )
    monthly = (
        frame.assign(month=frame["date"].dt.month)
        .groupby("month", as_index=False)
        .size()
        .rename(columns={"size": "rows"})
    )
    return annual, monthly


def build_split_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for regime, column in [
        ("temporal", "temporal_split"),
        ("spatial", "spatial_split"),
    ]:
        counts = frame[column].value_counts()
        for split, count in counts.items():
            rows.append({"regime": regime, "split": split, "rows": int(count)})
    return pd.DataFrame(rows)


def build_quality_flags(frame: pd.DataFrame) -> pd.DataFrame:
    rules = {
        "fco2_below_100": frame["fco2"] < 100,
        "fco2_above_700": frame["fco2"] > 700,
        "sst_outside_minus3_to_35": ~frame["sst"].between(-3, 35),
        "salinity_below_20": frame["salinity"] < 20,
        "salinity_above_40": frame["salinity"] > 40,
    }
    return pd.DataFrame(
        {
            "flag": list(rules),
            "rows": [int(mask.fillna(False).sum()) for mask in rules.values()],
            "action": "review_only_not_excluded",
        }
    )


def build_cleaning_summary(
    selected: pd.DataFrame, complete: pd.DataFrame
) -> pd.DataFrame:
    """Record the only row-exclusion step used by the minimal experiment."""
    n_before = len(selected)
    n_after = len(complete)
    return pd.DataFrame(
        {
            "stage": ["selected_domain", "complete_predictors_and_target"],
            "rows": [n_before, n_after],
            "rows_removed_at_step": [0, n_before - n_after],
        }
    )


def make_figure(
    frame: pd.DataFrame,
    annual: pd.DataFrame,
    monthly: pd.DataFrame,
    output: Path,
) -> None:
    configure_style()
    fig = plt.figure(figsize=(7.2, 6.4), constrained_layout=True)
    grid = fig.add_gridspec(2, 2, height_ratios=[1.25, 1.0])
    ax_map = fig.add_subplot(grid[0, :])
    ax_year = fig.add_subplot(grid[1, 0])
    ax_month = fig.add_subplot(grid[1, 1])

    lon_edges = np.arange(-180, 181, 2)
    lat_edges = np.arange(-80, -33, 2)
    counts, _, _ = np.histogram2d(
        frame["latitude"], frame["longitude"], bins=[lat_edges, lon_edges]
    )
    pseudocount = 1.0
    positive_counts = np.where(counts > 0, counts + pseudocount, np.nan)
    masked = np.ma.masked_invalid(np.log10(positive_counts))
    mesh = ax_map.pcolormesh(
        lon_edges,
        lat_edges,
        masked,
        cmap="Blues",
        shading="auto",
        rasterized=True,
    )
    ax_map.set_xlim(-180, 180)
    ax_map.set_ylim(-80, -35)
    ax_map.set_xlabel("Longitude")
    ax_map.set_ylabel("Latitude")
    ax_map.set_title("a  Southern Ocean SOCAT coverage, 1990–2024", loc="left", weight="bold")
    colorbar = fig.colorbar(mesh, ax=ax_map, pad=0.02, fraction=0.035)
    colorbar.set_label("log10(rows + 1) per 2° cell")

    year_colors = np.where(
        annual["year"] >= 2020, PALETTE["orange"], PALETTE["blue"]
    )
    ax_year.bar(annual["year"], annual["rows"], color=year_colors, width=0.9)
    ax_year.axvline(2019.5, color=PALETTE["dark"], linestyle="--", linewidth=0.9)
    ax_year.text(2020.1, annual["rows"].max() * 0.93, "temporal test", fontsize=7)
    ax_year.set_xlabel("Year")
    ax_year.set_ylabel("Monthly grid rows")
    ax_year.set_title("b  Coverage changes through time", loc="left", weight="bold")
    ax_year.tick_params(axis="x", rotation=45)

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ax_month.bar(monthly["month"], monthly["rows"], color=PALETTE["navy"])
    ax_month.set_xticks(range(1, 13), month_names, rotation=45)
    ax_month.set_xlabel("Month")
    ax_month.set_ylabel("Monthly grid rows")
    ax_month.set_title("c  Strong seasonal sampling imbalance", loc="left", weight="bold")

    fig.suptitle(
        "SOCAT observations are uneven across Southern Ocean space and time",
        fontsize=11,
        weight="bold",
    )
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "socat_coverage_audit.png", dpi=300, bbox_inches="tight")
    fig.savefig(output / "socat_coverage_audit.tiff", dpi=600, bbox_inches="tight")
    fig.savefig(output / "socat_coverage_audit.svg", bbox_inches="tight")
    fig.savefig(output / "socat_coverage_audit.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    full = read_socat_monthly(args.path)
    study = select_southern_ocean(full)
    complete = study.dropna(subset=["fco2", "sst", "salinity"]).copy()
    complete = add_spatial_folds(complete)
    complete = add_validation_regimes(complete)

    annual, monthly = build_summaries(complete)
    args.output.mkdir(parents=True, exist_ok=True)
    annual.to_csv(args.output / "annual_coverage.csv", index=False)
    monthly.to_csv(args.output / "monthly_coverage.csv", index=False)
    build_split_summary(complete).to_csv(
        args.output / "data_split_summary.csv", index=False
    )
    build_quality_flags(complete).to_csv(
        args.output / "quality_review_flags.csv", index=False
    )
    build_cleaning_summary(study, complete).to_csv(
        args.output / "cleaning_summary.csv", index=False
    )
    make_figure(complete, annual, monthly, args.output)


if __name__ == "__main__":
    main()
