"""Create absolute-baseline and unit-distribution tables for OSSE claims."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

METRICS = (
    "rmse",
    "mae",
    "median_absolute_error",
    "p95_absolute_error",
    "p99_absolute_error",
    "bias",
)
COMPARATORS = ("historical_density", "spatial_coverage")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--cross-year-metrics",
        type=Path,
        default=Path("results/public/osse_cross_year_metrics.csv"),
    )
    parser.add_argument(
        "--spatial-block-metrics",
        type=Path,
        default=Path("results/public/osse_spatial_block_confirmatory_metrics.csv"),
    )
    parser.add_argument(
        "--unit-output",
        type=Path,
        default=Path("results/public/osse_claim_unit_effects.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("results/public/osse_claim_distribution_summary.csv"),
    )
    return parser.parse_args()


def build_unit_effects(
    metrics: pd.DataFrame,
    *,
    validation_scheme: str,
    unit_columns: list[str],
) -> pd.DataFrame:
    """Pair seed-mean absolute metrics within each validation unit."""
    filtered = metrics.loc[metrics["evaluation_domain"] == "all"].copy()
    group_columns = [*unit_columns, "budget", "strategy"]
    means = filtered.groupby(group_columns, as_index=False, dropna=False)[
        list(METRICS)
    ].mean()
    rows: list[dict[str, object]] = []
    pair_columns = [*unit_columns, "budget"]
    for keys, group in means.groupby(pair_columns, sort=True, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        unit = dict(zip(pair_columns, keys, strict=True))
        strategies = group.set_index("strategy")
        if "random" not in strategies.index:
            raise ValueError(f"random baseline missing for {unit}")
        for comparator in COMPARATORS:
            if comparator not in strategies.index:
                raise ValueError(f"{comparator} missing for {unit}")
            for metric in METRICS:
                random_mean = float(strategies.loc["random", metric])
                comparator_mean = float(strategies.loc[comparator, metric])
                difference = comparator_mean - random_mean
                relative = (
                    difference / random_mean * 100.0
                    if metric != "bias" and random_mean != 0.0
                    else np.nan
                )
                unit_mask = np.ones(len(filtered), dtype=bool)
                for column, value in unit.items():
                    unit_mask &= (
                        filtered[column].isna().to_numpy()
                        if pd.isna(value)
                        else filtered[column].to_numpy() == value
                    )
                rows.append(
                    {
                        "validation_scheme": validation_scheme,
                        **unit,
                        "comparison": f"{comparator}_minus_random",
                        "metric": metric,
                        "n_seeds": int(filtered.loc[unit_mask, "seed"].nunique()),
                        "random_mean": random_mean,
                        "comparator_mean": comparator_mean,
                        "difference": difference,
                        "relative_error_change_percent": relative,
                    }
                )
    return pd.DataFrame(rows)


def summarize_distributions(unit_effects: pd.DataFrame) -> pd.DataFrame:
    """Describe effect distributions across years or year-fold units."""
    rows: list[dict[str, object]] = []
    group_columns = ["validation_scheme", "budget", "comparison", "metric"]
    for keys, group in unit_effects.groupby(group_columns, sort=True):
        differences = group["difference"].to_numpy(dtype=float)
        rows.append(
            {
                **dict(zip(group_columns, keys, strict=True)),
                "n_units": len(group),
                "n_years": int(group["year"].nunique()),
                "unit_definition": (
                    "year-fold"
                    if group["spatial_fold"].notna().any()
                    else "year"
                ),
                "mean_random_baseline": float(group["random_mean"].mean()),
                "mean_comparator_value": float(group["comparator_mean"].mean()),
                "mean_difference": float(differences.mean()),
                "median_difference": float(np.median(differences)),
                "q25_difference": float(np.quantile(differences, 0.25)),
                "q75_difference": float(np.quantile(differences, 0.75)),
                "minimum_difference": float(differences.min()),
                "maximum_difference": float(differences.max()),
                "units_below_zero": int(np.sum(differences < 0)),
                "units_above_zero": int(np.sum(differences > 0)),
                "mean_relative_error_change_percent": (
                    float(group["relative_error_change_percent"].mean())
                    if group["relative_error_change_percent"].notna().any()
                    else np.nan
                ),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    cross_year = pd.read_csv(args.cross_year_metrics)
    cross_year["spatial_fold"] = np.nan
    spatial_block = pd.read_csv(args.spatial_block_metrics)
    unit_effects = pd.concat(
        [
            build_unit_effects(
                cross_year,
                validation_scheme="month_stratified_hidden_cells",
                unit_columns=["year", "spatial_fold"],
            ),
            build_unit_effects(
                spatial_block,
                validation_scheme="whole_spatial_blocks",
                unit_columns=["year", "spatial_fold"],
            ),
        ],
        ignore_index=True,
    )
    summary = summarize_distributions(unit_effects)
    for path, table in (
        (args.unit_output, unit_effects),
        (args.summary_output, summary),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(path, index=False)
        print(f"wrote {len(table):,} rows to {path}")


if __name__ == "__main__":
    main()
