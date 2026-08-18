"""Audit month allocation without fitting additional reconstruction models."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from ocean_carbon_sampling.data import read_socat_monthly
from ocean_carbon_sampling.osse_experiment import (
    fixed_budget_orders,
    historical_density_weights,
)
from ocean_carbon_sampling.splits import add_spatial_folds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/osse_spatial_block_confirmatory.yaml"),
    )
    return parser.parse_args()


def load_frame(path: Path) -> pd.DataFrame:
    with xr.open_dataset(path, engine="h5netcdf", decode_times=True) as dataset:
        frame = (
            dataset[["spco2", "tos", "sos"]]
            .to_dataframe()
            .dropna()
            .reset_index()
            .rename(columns={"time": "date", "tos": "sst", "sos": "salinity"})
        )
    frame["month"] = frame["date"].dt.month
    return frame


def selection_month_rows(
    candidates: pd.DataFrame,
    weights: np.ndarray,
    *,
    year: int,
    fold: int,
    budgets: tuple[int, ...],
    seeds: tuple[int, ...],
    longitude_degrees: float,
    latitude_degrees: float,
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Return month counts and per-selection imbalance diagnostics."""
    candidate_counts = np.bincount(
        candidates["month"].to_numpy(dtype=int), minlength=13
    )[1:]
    candidate_share = candidate_counts / candidate_counts.sum()
    equal_share = np.full(12, 1.0 / 12.0)
    count_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for seed in seeds:
        orders = fixed_budget_orders(
            candidates,
            weights,
            maximum_budget=max(budgets),
            seed=seed,
            longitude_degrees=longitude_degrees,
            latitude_degrees=latitude_degrees,
        )
        for strategy, order in orders.items():
            for budget in budgets:
                selected_months = candidates.iloc[order[:budget]]["month"].to_numpy(
                    dtype=int
                )
                counts = np.bincount(selected_months, minlength=13)[1:]
                shares = counts / budget
                for month_index, count in enumerate(counts, start=1):
                    count_rows.append(
                        {
                            "year": year,
                            "spatial_fold": fold,
                            "strategy": strategy,
                            "budget": budget,
                            "seed": seed,
                            "month": month_index,
                            "selected_count": int(count),
                            "selected_fraction": float(shares[month_index - 1]),
                            "candidate_fraction": float(
                                candidate_share[month_index - 1]
                            ),
                            "equal_month_fraction": float(
                                equal_share[month_index - 1]
                            ),
                        }
                    )
                summary_rows.append(
                    {
                        "year": year,
                        "spatial_fold": fold,
                        "strategy": strategy,
                        "budget": budget,
                        "seed": seed,
                        "months_covered": int(np.count_nonzero(counts)),
                        "month_count_cv": float(counts.std() / counts.mean()),
                        "mean_abs_equal_deviation_pp": float(
                            np.abs(shares - equal_share).mean() * 100.0
                        ),
                        "max_abs_equal_deviation_pp": float(
                            np.abs(shares - equal_share).max() * 100.0
                        ),
                        "max_abs_candidate_deviation_pp": float(
                            np.abs(shares - candidate_share).max() * 100.0
                        ),
                    }
                )
    return count_rows, summary_rows


def summarize_strategies(selection_summary: pd.DataFrame) -> pd.DataFrame:
    """Aggregate imbalance diagnostics without treating months as replicates."""
    return (
        selection_summary.groupby(["strategy", "budget"], as_index=False)
        .agg(
            n_year_fold_seed_selections=("seed", "size"),
            minimum_months_covered=("months_covered", "min"),
            mean_month_count_cv=("month_count_cv", "mean"),
            mean_abs_equal_deviation_pp=("mean_abs_equal_deviation_pp", "mean"),
            mean_max_abs_equal_deviation_pp=(
                "max_abs_equal_deviation_pp",
                "mean",
            ),
            maximum_abs_equal_deviation_pp=(
                "max_abs_equal_deviation_pp",
                "max",
            ),
            mean_max_abs_candidate_deviation_pp=(
                "max_abs_candidate_deviation_pp",
                "mean",
            ),
        )
        .sort_values(["budget", "strategy"])
    )


def main() -> None:
    args = parse_args()
    gate = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    osse_path = Path(gate["source"]["osse_config"])
    osse = yaml.safe_load(osse_path.read_text(encoding="utf-8"))
    years = tuple(int(value) for value in gate["source"]["years"])
    folds = tuple(int(value) for value in gate["validation"]["folds"])
    budgets = tuple(int(value) for value in gate["execution"]["budgets"])
    seeds = tuple(int(value) for value in gate["execution"]["seeds"])
    validation = gate["validation"]
    density = osse["experiment"]["historical_density"]
    acquisition = osse["experiment"]["coverage_blocks"]
    processed_template = str(osse["processing"]["processed_file_template"])
    socat = read_socat_monthly(density["socat_path"])

    count_rows: list[dict[str, object]] = []
    summary_rows: list[dict[str, object]] = []
    for year in years:
        frame = load_frame(Path(processed_template.format(year=year)))
        frame = add_spatial_folds(
            frame,
            lon_block_degrees=float(validation["longitude_degrees"]),
            lat_block_degrees=float(validation["latitude_degrees"]),
            n_folds=int(validation["n_folds"]),
        )
        full_weights = historical_density_weights(
            frame,
            socat,
            year_start=int(density["year_start"]),
            year_end=int(density["year_end"]),
            weight_column=str(density["weight_column"]),
        )
        for fold in folds:
            candidate_mask = frame["spatial_fold"].to_numpy(dtype=int) != fold
            candidates = frame.loc[candidate_mask].reset_index(drop=True)
            weights = full_weights[candidate_mask]
            counts, summaries = selection_month_rows(
                candidates,
                weights,
                year=year,
                fold=fold,
                budgets=budgets,
                seeds=seeds,
                longitude_degrees=float(acquisition["longitude_degrees"]),
                latitude_degrees=float(acquisition["latitude_degrees"]),
            )
            count_rows.extend(counts)
            summary_rows.extend(summaries)
            print(f"audited year {year}, spatial fold {fold}", flush=True)

    counts = pd.DataFrame(count_rows)
    selection_summary = pd.DataFrame(summary_rows)
    strategy_summary = summarize_strategies(selection_summary)
    audit = gate["month_balance_audit"]
    for key, table in (
        ("counts_file", counts),
        ("selection_summary_file", selection_summary),
        ("strategy_summary_file", strategy_summary),
    ):
        output = Path(audit[key])
        output.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(output, index=False)
        print(f"wrote {len(table):,} rows to {output}")


if __name__ == "__main__":
    main()
