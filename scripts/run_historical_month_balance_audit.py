"""Run the factorized historical-spatial, month-balanced OSSE audit."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml
from sklearn.metrics import r2_score

from ocean_carbon_sampling.data import read_socat_monthly
from ocean_carbon_sampling.experiment import make_model, regression_metrics
from ocean_carbon_sampling.features import build_features
from ocean_carbon_sampling.osse_experiment import (
    fixed_budget_orders,
    historical_density_weights,
    historical_spatial_month_balanced_order,
    historical_spatial_weights,
    stratified_evaluation_positions,
)
from ocean_carbon_sampling.splits import add_spatial_folds

METRICS = (
    "rmse",
    "mae",
    "median_absolute_error",
    "p95_absolute_error",
    "p99_absolute_error",
    "bias",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config",
        type=Path,
        default=Path("configs/osse_historical_month_balance_audit.yaml"),
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


def score(observed: np.ndarray, predicted: np.ndarray) -> dict[str, float]:
    result = regression_metrics(observed, predicted)
    absolute_error = np.abs(predicted - observed)
    result.update(
        {
            "median_absolute_error": float(np.median(absolute_error)),
            "p95_absolute_error": float(np.quantile(absolute_error, 0.95)),
            "p99_absolute_error": float(np.quantile(absolute_error, 0.99)),
            "r2": float(r2_score(observed, predicted)),
            "correlation": float(np.corrcoef(observed, predicted)[0, 1]),
        }
    )
    return result


def month_audit(selected: pd.DataFrame) -> dict[str, float | int]:
    counts = selected.groupby("month").size().reindex(range(1, 13), fill_value=0)
    shares = counts / counts.sum()
    return {
        "minimum_month_count": int(counts.min()),
        "maximum_month_count": int(counts.max()),
        "mean_abs_equal_deviation_pp": float(
            np.mean(np.abs(shares - 1.0 / 12.0)) * 100.0
        ),
        "maximum_abs_equal_deviation_pp": float(
            np.max(np.abs(shares - 1.0 / 12.0)) * 100.0
        ),
    }


def map_summary(
    evaluation: pd.DataFrame,
    *,
    seed: int,
    historical_prediction: np.ndarray,
    balanced_prediction: np.ndarray,
) -> pd.DataFrame:
    result = evaluation[["latitude", "longitude"]].copy()
    truth = evaluation["spco2"].to_numpy(dtype=float)
    for label, prediction in (
        ("historical_density", historical_prediction),
        ("historical_spatial_month_balanced", balanced_prediction),
    ):
        residual = prediction - truth
        result[f"signed_error_{label}"] = residual
    result = result.groupby(["latitude", "longitude"], as_index=False).mean()
    result.insert(0, "seed", seed)
    return result


def fit_unit(
    frame: pd.DataFrame,
    evaluation_positions: np.ndarray,
    *,
    full_spatial_weights: np.ndarray,
    full_historical_weights: np.ndarray,
    sample_count: int,
    seeds: tuple[int, ...],
    validation_scheme: str,
    year: int,
    spatial_fold: int | None,
    work: Path,
    make_map: bool,
) -> tuple[pd.DataFrame, pd.DataFrame, list[pd.DataFrame]]:
    unit = f"{validation_scheme}_{year}"
    if spatial_fold is not None:
        unit += f"_fold_{spatial_fold}"
    metric_path = work / f"metrics_{unit}.csv"
    selection_path = work / f"selections_{unit}.csv"
    map_path = work / f"map_{unit}.parquet"
    if metric_path.exists() and selection_path.exists() and (
        not make_map or map_path.exists()
    ):
        maps = [pd.read_parquet(map_path)] if make_map else []
        return pd.read_csv(metric_path), pd.read_csv(selection_path), maps

    evaluation_mask = np.zeros(len(frame), dtype=bool)
    evaluation_mask[evaluation_positions] = True
    candidates = frame.loc[~evaluation_mask].reset_index(drop=True)
    evaluation = frame.loc[evaluation_mask].reset_index(drop=True)
    spatial_weights = full_spatial_weights[~evaluation_mask]
    historical_weights = full_historical_weights[~evaluation_mask]
    x_candidates = build_features(candidates)
    x_evaluation = build_features(evaluation)
    y_candidates = candidates["spco2"].to_numpy(dtype=float)
    y_evaluation = evaluation["spco2"].to_numpy(dtype=float)

    metric_rows: list[dict[str, object]] = []
    selection_rows: list[dict[str, object]] = []
    map_rows: list[pd.DataFrame] = []
    for seed in seeds:
        selected = historical_spatial_month_balanced_order(
            candidates,
            spatial_weights,
            sample_count=sample_count,
            seed=seed + 404,
        )
        model = make_model(seed + 10_000)
        model.fit(x_candidates.iloc[selected], y_candidates[selected])
        prediction = model.predict(x_evaluation)
        metric_rows.append(
            {
                "validation_scheme": validation_scheme,
                "year": year,
                "spatial_fold": spatial_fold,
                "evaluation_domain": "all",
                "strategy": "historical_spatial_month_balanced",
                "budget": sample_count,
                "seed": seed,
                "n_candidates": len(candidates),
                "n_evaluation": len(evaluation),
                **score(y_evaluation, prediction),
            }
        )
        selection_rows.append(
            {
                "validation_scheme": validation_scheme,
                "year": year,
                "spatial_fold": spatial_fold,
                "budget": sample_count,
                "seed": seed,
                "strategy": "historical_spatial_month_balanced",
                "occupied_locations": int(
                    candidates.iloc[selected][["latitude", "longitude"]]
                    .drop_duplicates()
                    .shape[0]
                ),
                **month_audit(candidates.iloc[selected]),
            }
        )
        if make_map:
            original_order = fixed_budget_orders(
                candidates,
                historical_weights,
                maximum_budget=sample_count,
                seed=seed,
            )["historical_density"]
            original_model = make_model(seed + 10_000)
            original_model.fit(
                x_candidates.iloc[original_order], y_candidates[original_order]
            )
            original_prediction = original_model.predict(x_evaluation)
            map_rows.append(
                map_summary(
                    evaluation,
                    seed=seed,
                    historical_prediction=original_prediction,
                    balanced_prediction=prediction,
                )
            )
        print(f"completed {unit}, seed {seed}", flush=True)

    metrics = pd.DataFrame(metric_rows)
    selections = pd.DataFrame(selection_rows)
    metrics.to_csv(metric_path, index=False)
    selections.to_csv(selection_path, index=False)
    if make_map:
        pd.concat(map_rows, ignore_index=True).to_parquet(map_path, index=False)
    return metrics, selections, map_rows


def paired_outputs(
    audit_metrics: pd.DataFrame,
    *,
    hidden_baseline_path: Path,
    block_baseline_path: Path,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    hidden = pd.read_csv(hidden_baseline_path).query(
        "evaluation_domain == 'all' and budget == 5000 and strategy == 'random'"
    )
    hidden.insert(0, "validation_scheme", "month_stratified_hidden_cells")
    hidden["spatial_fold"] = np.nan
    block = pd.read_csv(block_baseline_path).query(
        "evaluation_domain == 'all' and budget == 5000 and strategy == 'random'"
    )
    block.insert(0, "validation_scheme", "whole_spatial_blocks")
    baseline = pd.concat([hidden, block], ignore_index=True)
    keys = ["validation_scheme", "year", "spatial_fold", "budget", "seed"]
    merged = audit_metrics.merge(
        baseline[keys + list(METRICS)],
        on=keys,
        how="left",
        validate="one_to_one",
        suffixes=("_balanced", "_random"),
    )
    if merged[[f"{metric}_random" for metric in METRICS]].isna().any().any():
        raise RuntimeError("random baseline did not align with every audit fit")
    paired_rows: list[dict[str, object]] = []
    for row in merged.itertuples(index=False):
        base = {key: getattr(row, key) for key in keys}
        for metric in METRICS:
            random_value = float(getattr(row, f"{metric}_random"))
            balanced_value = float(getattr(row, f"{metric}_balanced"))
            paired_rows.append(
                {
                    **base,
                    "comparison": "historical_spatial_month_balanced_minus_random",
                    "metric": metric,
                    "random_value": random_value,
                    "comparator_value": balanced_value,
                    "difference": balanced_value - random_value,
                }
            )
    paired = pd.DataFrame(paired_rows)
    unit_keys = [
        "validation_scheme",
        "year",
        "spatial_fold",
        "budget",
        "comparison",
        "metric",
    ]
    unit = (
        paired.groupby(unit_keys, dropna=False, as_index=False)
        .agg(
            n_seeds=("seed", "nunique"),
            random_value=("random_value", "mean"),
            comparator_value=("comparator_value", "mean"),
            mean_difference=("difference", "mean"),
            sd_seed_difference=("difference", "std"),
            seed_fraction_below_zero=("difference", lambda values: (values < 0).mean()),
        )
    )
    distribution = (
        unit.groupby(
            ["validation_scheme", "budget", "comparison", "metric"],
            as_index=False,
        )
        .agg(
            n_units=("mean_difference", "size"),
            mean_random=("random_value", "mean"),
            mean_comparator=("comparator_value", "mean"),
            mean_difference=("mean_difference", "mean"),
            median_difference=("mean_difference", "median"),
            minimum_difference=("mean_difference", "min"),
            maximum_difference=("mean_difference", "max"),
            units_below_zero=("mean_difference", lambda values: (values < 0).sum()),
            units_above_zero=("mean_difference", lambda values: (values > 0).sum()),
        )
    )
    return paired, unit, distribution


def main() -> None:
    args = parse_args()
    audit = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    source = audit["source"]
    osse = yaml.safe_load(Path(source["osse_config"]).read_text(encoding="utf-8"))
    block_config = yaml.safe_load(
        Path(source["spatial_block_config"]).read_text(encoding="utf-8")
    )
    execution = audit["execution"]
    years = tuple(int(year) for year in source["years"])
    seeds = tuple(int(seed) for seed in execution["seeds"])
    sample_count = int(execution["sample_count"])
    work = Path(execution["work_directory"])
    work.mkdir(parents=True, exist_ok=True)

    density = osse["experiment"]["historical_density"]
    socat = read_socat_monthly(density["socat_path"])
    metric_frames: list[pd.DataFrame] = []
    selection_frames: list[pd.DataFrame] = []
    map_frames: list[pd.DataFrame] = []
    for year in years:
        processed = Path(
            str(osse["processing"]["processed_file_template"]).format(year=year)
        )
        frame = load_frame(processed)
        spatial_weights = historical_spatial_weights(
            frame,
            socat,
            year_start=int(density["year_start"]),
            year_end=int(density["year_end"]),
            weight_column=str(density["weight_column"]),
        )
        historical_weights = historical_density_weights(
            frame,
            socat,
            year_start=int(density["year_start"]),
            year_end=int(density["year_end"]),
            weight_column=str(density["weight_column"]),
        )
        evaluation = stratified_evaluation_positions(
            frame,
            fraction=float(osse["experiment"]["evaluation"]["fraction"]),
            seed=int(osse["experiment"]["evaluation"]["seed"]),
        )
        metrics, selections, maps = fit_unit(
            frame,
            evaluation,
            full_spatial_weights=spatial_weights,
            full_historical_weights=historical_weights,
            sample_count=sample_count,
            seeds=seeds,
            validation_scheme="month_stratified_hidden_cells",
            year=year,
            spatial_fold=None,
            work=work,
            make_map=year == 2005,
        )
        metric_frames.append(metrics)
        selection_frames.append(selections)
        map_frames.extend(maps)

        validation = block_config["validation"]
        blocked = add_spatial_folds(
            frame,
            lon_block_degrees=float(validation["longitude_degrees"]),
            lat_block_degrees=float(validation["latitude_degrees"]),
            n_folds=int(validation["n_folds"]),
        )
        for fold in (int(value) for value in validation["folds"]):
            evaluation = np.flatnonzero(
                blocked["spatial_fold"].to_numpy(dtype=int) == fold
            )
            metrics, selections, _ = fit_unit(
                blocked,
                evaluation,
                full_spatial_weights=spatial_weights,
                full_historical_weights=historical_weights,
                sample_count=sample_count,
                seeds=seeds,
                validation_scheme="whole_spatial_blocks",
                year=year,
                spatial_fold=fold,
                work=work,
                make_map=False,
            )
            metric_frames.append(metrics)
            selection_frames.append(selections)

    metrics = pd.concat(metric_frames, ignore_index=True)
    selections = pd.concat(selection_frames, ignore_index=True)
    paired, unit, distribution = paired_outputs(
        metrics,
        hidden_baseline_path=Path("results/public/osse_cross_year_metrics.csv"),
        block_baseline_path=Path(
            "results/public/osse_spatial_block_confirmatory_metrics.csv"
        ),
    )
    outputs = {
        "metrics_file": metrics,
        "selection_audit_file": selections,
        "paired_effects_file": paired,
        "unit_summary_file": unit,
        "distribution_summary_file": distribution,
        "design_file": pd.DataFrame(
            [
                {
                    **audit["identification"],
                    "years": ";".join(str(year) for year in years),
                    "sample_count": sample_count,
                    "n_seeds": len(seeds),
                    "hidden_units": len(years),
                    "whole_block_units": len(years)
                    * len(block_config["validation"]["folds"]),
                }
            ]
        ),
    }
    for key, table in outputs.items():
        path = Path(execution[key])
        path.parent.mkdir(parents=True, exist_ok=True)
        table.to_csv(path, index=False)
        print(f"wrote {len(table):,} rows to {path}")
    map_data = pd.concat(map_frames, ignore_index=True)
    map_data = map_data.groupby(["latitude", "longitude"], as_index=False).agg(
        signed_error_historical_density=(
            "signed_error_historical_density",
            "mean",
        ),
        signed_error_historical_spatial_month_balanced=(
            "signed_error_historical_spatial_month_balanced",
            "mean",
        ),
        historical_negative_seed_fraction=(
            "signed_error_historical_density",
            lambda values: float(np.mean(values < 0)),
        ),
        balanced_negative_seed_fraction=(
            "signed_error_historical_spatial_month_balanced",
            lambda values: float(np.mean(values < 0)),
        ),
    )
    map_data["signed_error_change_balanced_minus_historical"] = (
        map_data["signed_error_historical_spatial_month_balanced"]
        - map_data["signed_error_historical_density"]
    )
    numeric_columns = map_data.select_dtypes(include=["number"]).columns
    map_data[numeric_columns] = map_data[numeric_columns].astype("float32")
    map_data.to_parquet(execution["map_file"], index=False)
    print(distribution.to_string(index=False))


if __name__ == "__main__":
    main()
