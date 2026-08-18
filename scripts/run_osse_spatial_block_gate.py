"""Run a minimal global OSSE gate with exhaustive spatial-block holdouts."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from ocean_carbon_sampling.data import read_socat_monthly
from ocean_carbon_sampling.osse_experiment import (
    historical_density_weights,
    run_osse_gate,
    summarize_paired_effects,
    summarize_spatial_fold_consistency,
)
from ocean_carbon_sampling.splits import add_spatial_folds

METRICS = (
    "rmse",
    "mae",
    "median_absolute_error",
    "p95_absolute_error",
    "p99_absolute_error",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/osse_spatial_block_gate.yaml"),
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


def build_paired_effects(metrics: pd.DataFrame) -> pd.DataFrame:
    """Pair strategy-minus-random effects within fold, budget and seed."""
    index = [
        "year",
        "spatial_fold",
        "evaluation_domain",
        "budget",
        "seed",
    ]
    rows: list[dict[str, object]] = []
    for keys, group in metrics.groupby(index, sort=True):
        key_values = dict(zip(index, keys, strict=True))
        strategies = group.set_index("strategy")
        if not {
            "random",
            "historical_density",
            "spatial_coverage",
        }.issubset(strategies.index):
            raise ValueError("each paired group requires all three strategies")
        for strategy in ("historical_density", "spatial_coverage"):
            for metric in METRICS:
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


def block_map(frame: pd.DataFrame, *, lon_width: float, lat_width: float) -> pd.DataFrame:
    """Return a public table describing every occupied evaluation block."""
    result = frame.loc[
        :, ["latitude", "longitude", "spatial_block", "spatial_fold"]
    ].copy()
    result["lon_block"] = np.floor(
        (result["longitude"] + 180.0) / lon_width
    ).astype(int)
    result["lat_block"] = np.floor(
        (result["latitude"] + 90.0) / lat_width
    ).astype(int)
    blocks = (
        result.groupby(
            ["spatial_block", "spatial_fold", "lon_block", "lat_block"],
            as_index=False,
        )
        .size()
        .rename(columns={"size": "month_grid_rows"})
    )
    blocks["longitude_center"] = -180.0 + (blocks["lon_block"] + 0.5) * lon_width
    blocks["latitude_center"] = -90.0 + (blocks["lat_block"] + 0.5) * lat_width
    blocks["longitude_width"] = lon_width
    blocks["latitude_width"] = lat_width
    return blocks.sort_values(["spatial_fold", "lat_block", "lon_block"])


def main() -> None:
    args = parse_args()
    gate = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    source_config_path = Path(gate["source"]["osse_config"])
    osse = yaml.safe_load(source_config_path.read_text(encoding="utf-8"))
    year = int(gate["source"]["year"])
    processing = osse["processing"]
    processed_path = Path(
        str(processing["processed_file_template"]).format(year=year)
    )
    frame = load_frame(processed_path)

    validation = gate["validation"]
    lon_width = float(validation["longitude_degrees"])
    lat_width = float(validation["latitude_degrees"])
    n_folds = int(validation["n_folds"])
    frame = add_spatial_folds(
        frame,
        lon_block_degrees=lon_width,
        lat_block_degrees=lat_width,
        n_folds=n_folds,
    )
    if frame.groupby(["latitude", "longitude"])["spatial_fold"].nunique().max() != 1:
        raise RuntimeError("a spatial location was assigned to multiple folds")

    density = osse["experiment"]["historical_density"]
    socat = read_socat_monthly(density["socat_path"])
    weights = historical_density_weights(
        frame,
        socat,
        year_start=int(density["year_start"]),
        year_end=int(density["year_end"]),
        weight_column=str(density["weight_column"]),
    )
    acquisition_blocks = osse["experiment"]["coverage_blocks"]
    evaluation_config = osse["experiment"]["evaluation"]
    execution = gate["execution"]
    work = Path(execution["work_directory"])
    work.mkdir(parents=True, exist_ok=True)

    metric_frames: list[pd.DataFrame] = []
    selection_frames: list[pd.DataFrame] = []
    design_rows: list[dict[str, object]] = []
    for fold in (int(value) for value in validation["folds"]):
        evaluation = np.flatnonzero(frame["spatial_fold"].to_numpy() == fold)
        metric_path = work / f"metrics_fold_{fold}.csv"
        selection_path = work / f"selections_fold_{fold}.csv"
        if not (metric_path.exists() and selection_path.exists()):
            metrics, selections = run_osse_gate(
                frame,
                weights,
                evaluation,
                budgets=tuple(int(value) for value in execution["budgets"]),
                seeds=tuple(int(value) for value in execution["seeds"]),
                longitude_degrees=float(acquisition_blocks["longitude_degrees"]),
                latitude_degrees=float(acquisition_blocks["latitude_degrees"]),
                extreme_value_threshold=float(
                    evaluation_config["extreme_value_sensitivity_threshold"]
                ),
            )
            metrics.insert(0, "spatial_fold", fold)
            metrics.insert(0, "year", year)
            selections.insert(0, "spatial_fold", fold)
            selections.insert(0, "year", year)
            metrics.to_csv(metric_path, index=False)
            selections.to_csv(selection_path, index=False)
        metric_frames.append(pd.read_csv(metric_path))
        selection_frames.append(pd.read_csv(selection_path))
        evaluation_blocks = frame.iloc[evaluation]["spatial_block"].nunique()
        design_rows.append(
            {
                "year": year,
                "spatial_fold": fold,
                "n_evaluation_month_cells": len(evaluation),
                "n_candidate_month_cells": len(frame) - len(evaluation),
                "evaluation_fraction": len(evaluation) / len(frame),
                "n_evaluation_blocks": int(evaluation_blocks),
                "longitude_degrees": lon_width,
                "latitude_degrees": lat_width,
                "buffer_degrees": float(validation["buffer_degrees"]),
                "n_seeds": len(execution["seeds"]),
                "budgets": ";".join(str(value) for value in execution["budgets"]),
            }
        )
        print(f"completed spatial fold {fold}", flush=True)

    metrics = pd.concat(metric_frames, ignore_index=True).sort_values(
        ["year", "spatial_fold", "evaluation_domain", "budget", "seed", "strategy"]
    )
    selections = pd.concat(selection_frames, ignore_index=True).sort_values(
        ["year", "spatial_fold", "budget", "seed", "strategy"]
    )
    paired = build_paired_effects(metrics)
    paired_summary = summarize_paired_effects(
        paired,
        n_resamples=int(execution["bootstrap_resamples"]),
        seed=int(execution["bootstrap_seed"]),
    )
    consistency = summarize_spatial_fold_consistency(paired_summary)

    outputs = {
        "metrics_file": metrics,
        "selections_file": selections,
        "paired_effects_file": paired,
        "paired_summary_file": paired_summary,
        "fold_consistency_file": consistency,
        "design_file": pd.DataFrame(design_rows),
        "block_map_file": block_map(
            frame,
            lon_width=lon_width,
            lat_width=lat_width,
        ),
    }
    for config_key, table in outputs.items():
        output_path = Path(execution[config_key])
        output_path.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(output_path, index=False)
        print(f"wrote {len(table):,} rows to {output_path}")


if __name__ == "__main__":
    main()
