"""Run the fixed-budget OSSE gate, benchmark or cross-year robustness phase."""

from __future__ import annotations

import argparse
import hashlib
import sys
from importlib.metadata import version
from pathlib import Path

import pandas as pd
import xarray as xr
import yaml

from ocean_carbon_sampling.data import read_socat_monthly
from ocean_carbon_sampling.osse_experiment import (
    historical_density_weights,
    run_osse_gate,
    stratified_evaluation_positions,
    summarize_paired_effects,
    summarize_year_consistency,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/osse_pilot.yaml")
    parser.add_argument(
        "--phase",
        choices=("gate", "benchmark", "cross_year", "regrid_audit"),
        default="gate",
    )
    return parser.parse_args()


def _processed_path(
    processing: dict[str, object], *, year: int, phase: str
) -> Path:
    if phase == "regrid_audit":
        return Path(
            str(processing["area_weighted_processed_file_template"]).format(year=year)
        )
    if phase == "cross_year":
        return Path(str(processing["processed_file_template"]).format(year=year))
    return Path(str(processing["processed_file"]))


def _load_frame(path: Path) -> pd.DataFrame:
    with xr.open_dataset(path, engine="h5netcdf", decode_times=True) as dataset:
        frame = (
            dataset[["spco2", "tos", "sos"]]
            .to_dataframe()
            .dropna()
            .reset_index()
            .rename(columns={"time": "date", "tos": "sst", "sos": "salinity"})
        )
    frame["month"] = frame["date"].dt.month
    frame["observation_id"] = range(len(frame))
    return frame


def _run_year(
    *,
    year: int,
    phase: str,
    processed_path: Path,
    experiment: dict[str, object],
    run_config: dict[str, object],
    socat: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, object]]:
    frame = _load_frame(processed_path)
    density_config = experiment["historical_density"]
    weights = historical_density_weights(
        frame,
        socat,
        year_start=int(density_config["year_start"]),
        year_end=int(density_config["year_end"]),
        weight_column=str(density_config["weight_column"]),
    )
    evaluation_config = experiment["evaluation"]
    evaluation = stratified_evaluation_positions(
        frame,
        fraction=float(evaluation_config["fraction"]),
        seed=int(evaluation_config["seed"]),
    )
    coverage = experiment["coverage_blocks"]
    metrics, selections = run_osse_gate(
        frame,
        weights,
        evaluation,
        budgets=tuple(int(value) for value in run_config["budgets"]),
        seeds=tuple(int(value) for value in run_config["seeds"]),
        longitude_degrees=float(coverage["longitude_degrees"]),
        latitude_degrees=float(coverage["latitude_degrees"]),
        extreme_value_threshold=float(
            evaluation_config["extreme_value_sensitivity_threshold"]
        ),
    )
    if phase in {"cross_year", "regrid_audit"}:
        metrics.insert(0, "year", year)
        selections.insert(0, "year", year)
    design: dict[str, object] = {
        "phase": phase,
        "pilot_year": year,
    }
    if phase in {"cross_year", "regrid_audit"}:
        design["processed_file"] = processed_path.as_posix()
        design["regrid_method"] = (
            "native_cell_area_weighted_bin_mean"
            if phase == "regrid_audit"
            else "native_cell_center_bin_mean"
        )
    design.update(
        {
            "n_complete_month_cells": len(frame),
            "n_evaluation": len(evaluation),
            "evaluation_fraction_realized": len(evaluation) / len(frame),
            "evaluation_seed": int(evaluation_config["seed"]),
            "extreme_value_sensitivity_threshold": float(
                evaluation_config["extreme_value_sensitivity_threshold"]
            ),
            "evaluation_positions_sha256": hashlib.sha256(
                evaluation.tobytes()
            ).hexdigest(),
            "historical_year_start": int(density_config["year_start"]),
            "historical_year_end": int(density_config["year_end"]),
            "positive_historical_month_cells": int((weights > 0).sum()),
            "budgets": ";".join(str(value) for value in run_config["budgets"]),
            "seeds": ";".join(str(value) for value in run_config["seeds"]),
        }
    )
    return metrics, selections, design


def _summarize_metrics(metrics: pd.DataFrame) -> pd.DataFrame:
    group_columns = ["evaluation_domain", "strategy", "budget"]
    sort_columns = ["evaluation_domain", "budget", "mean_rmse"]
    if "year" in metrics.columns:
        group_columns.insert(0, "year")
        sort_columns.insert(0, "year")
    return (
        metrics.groupby(group_columns, as_index=False)
        .agg(
            mean_rmse=("rmse", "mean"),
            sd_rmse=("rmse", "std"),
            mean_mae=("mae", "mean"),
            mean_median_absolute_error=("median_absolute_error", "mean"),
            mean_p95_absolute_error=("p95_absolute_error", "mean"),
            mean_p99_absolute_error=("p99_absolute_error", "mean"),
            mean_r2=("r2", "mean"),
            mean_correlation=("correlation", "mean"),
            n_seeds=("seed", "nunique"),
        )
        .sort_values(sort_columns)
    )


def _paired_effects(metrics: pd.DataFrame) -> pd.DataFrame:
    group_columns = ["evaluation_domain", "budget", "seed"]
    if "year" in metrics.columns:
        group_columns.insert(0, "year")
    rows: list[dict[str, object]] = []
    for keys, group in metrics.groupby(group_columns, sort=True):
        key_values = dict(zip(group_columns, keys, strict=True))
        strategies = group.set_index("strategy")
        for strategy in ("spatial_coverage", "historical_density"):
            for metric in (
                "rmse",
                "mae",
                "median_absolute_error",
                "p95_absolute_error",
                "p99_absolute_error",
            ):
                rows.append(
                    {
                        **key_values,
                        "comparison": f"{strategy}_minus_random",
                        "metric": metric,
                        "difference": float(
                            strategies.loc[strategy, metric]
                            - strategies.loc["random", metric]
                        ),
                    }
                )
    return pd.DataFrame(rows)


def _software_versions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"package": "python", "version": sys.version.split()[0]},
            *(
                {"package": package, "version": version(package)}
                for package in (
                    "numpy",
                    "pandas",
                    "scikit-learn",
                    "xarray",
                    "h5netcdf",
                )
            ),
        ]
    )


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    processing = config["processing"]
    experiment = config["experiment"]
    config_key = "execution_gate" if args.phase == "gate" else args.phase
    run_config = experiment[config_key]
    annual_phase = args.phase in {"cross_year", "regrid_audit"}
    years = (
        [int(value) for value in run_config["years"]]
        if annual_phase
        else [int(processing["pilot_year"])]
    )
    density_config = experiment["historical_density"]
    socat = read_socat_monthly(density_config["socat_path"])

    metric_frames: list[pd.DataFrame] = []
    selection_frames: list[pd.DataFrame] = []
    design_rows: list[dict[str, object]] = []
    for year in years:
        path = _processed_path(processing, year=year, phase=args.phase)
        metrics, selections, design = _run_year(
            year=year,
            phase=args.phase,
            processed_path=path,
            experiment=experiment,
            run_config=run_config,
            socat=socat,
        )
        metric_frames.append(metrics)
        selection_frames.append(selections)
        design_rows.append(design)

    metrics = pd.concat(metric_frames, ignore_index=True)
    selections = pd.concat(selection_frames, ignore_index=True)
    summary = _summarize_metrics(metrics)
    paired = _paired_effects(metrics)
    output_paths = [
        Path(run_config[key])
        for key in (
            "metrics_file",
            "selections_file",
            "design_file",
            "summary_file",
            "paired_effects_file",
        )
    ]
    for path in output_paths:
        path.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(run_config["metrics_file"], index=False)
    selections.to_csv(run_config["selections_file"], index=False)
    pd.DataFrame(design_rows).to_csv(run_config["design_file"], index=False)
    summary.to_csv(run_config["summary_file"], index=False)
    paired.to_csv(run_config["paired_effects_file"], index=False)

    if args.phase in {"benchmark", "cross_year", "regrid_audit"}:
        paired_summary = summarize_paired_effects(
            paired,
            n_resamples=int(run_config["bootstrap_resamples"]),
            seed=int(run_config["bootstrap_seed"]),
        )
        paired_summary.to_csv(run_config["paired_summary_file"], index=False)
        _software_versions().to_csv(run_config["versions_file"], index=False)
        if annual_phase:
            summarize_year_consistency(paired_summary).to_csv(
                run_config["year_consistency_file"], index=False
            )
    print(summary.to_string(index=False))
    print(f"\nCompleted years: {', '.join(str(year) for year in years)}")


if __name__ == "__main__":
    main()
