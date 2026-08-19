"""Audit historical signed bias under area weighting and a 60°N domain split."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from ocean_carbon_sampling.data import read_socat_monthly
from ocean_carbon_sampling.experiment import make_model
from ocean_carbon_sampling.features import build_features
from ocean_carbon_sampling.osse_experiment import (
    fixed_budget_orders,
    historical_density_weights,
    spherical_cell_area_weights,
    stratified_evaluation_positions,
    weighted_regression_metrics,
)
from ocean_carbon_sampling.splits import add_spatial_folds


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--osse-config", type=Path, default=Path("configs/osse_pilot.yaml")
    )
    parser.add_argument(
        "--block-config",
        type=Path,
        default=Path("configs/osse_spatial_block_confirmatory.yaml"),
    )
    parser.add_argument("--budget", type=int, default=5000)
    parser.add_argument("--latitude-cutoff", type=float, default=60.0)
    parser.add_argument(
        "--work-directory",
        type=Path,
        default=Path("results/osse_historical_area_domain_work"),
    )
    parser.add_argument(
        "--metrics-output",
        type=Path,
        default=Path("results/public/osse_historical_area_domain_metrics.csv"),
    )
    parser.add_argument(
        "--unit-output",
        type=Path,
        default=Path("results/public/osse_historical_area_domain_unit_summary.csv"),
    )
    parser.add_argument(
        "--overall-output",
        type=Path,
        default=Path("results/public/osse_historical_area_domain_overall.csv"),
    )
    parser.add_argument(
        "--paired-output",
        type=Path,
        default=Path("results/public/osse_historical_area_domain_paired.csv"),
    )
    parser.add_argument(
        "--paired-overall-output",
        type=Path,
        default=Path("results/public/osse_historical_area_domain_paired_overall.csv"),
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


def evaluate_unit(
    frame: pd.DataFrame,
    historical_weights: np.ndarray,
    evaluation_positions: np.ndarray,
    *,
    year: int,
    validation_scheme: str,
    spatial_fold: int,
    budget: int,
    seeds: tuple[int, ...],
    longitude_degrees: float,
    latitude_degrees: float,
    latitude_cutoff: float,
    strategies: tuple[str, ...],
) -> pd.DataFrame:
    evaluation_mask = np.zeros(len(frame), dtype=bool)
    evaluation_mask[np.asarray(evaluation_positions, dtype=int)] = True
    candidates = frame.loc[~evaluation_mask].reset_index(drop=True)
    evaluation = frame.loc[evaluation_mask].reset_index(drop=True)
    candidate_weights = np.asarray(historical_weights, dtype=float)[~evaluation_mask]
    x_candidates = build_features(candidates)
    x_evaluation = build_features(evaluation)
    y_candidates = candidates["spco2"].to_numpy(dtype=float)
    y_evaluation = evaluation["spco2"].to_numpy(dtype=float)
    evaluation_latitude = evaluation["latitude"].to_numpy(dtype=float)
    area_weights = spherical_cell_area_weights(evaluation_latitude)
    domains = {
        "global": np.ones(len(evaluation), dtype=bool),
        "south_of_60n": evaluation_latitude < latitude_cutoff,
        "60_to_90n": evaluation_latitude >= latitude_cutoff,
    }
    rows: list[dict[str, float | int | str]] = []
    domains = {name: mask for name, mask in domains.items() if mask.any()}
    for seed in seeds:
        orders = fixed_budget_orders(
            candidates,
            candidate_weights,
            maximum_budget=budget,
            seed=seed,
            longitude_degrees=longitude_degrees,
            latitude_degrees=latitude_degrees,
        )
        for strategy in strategies:
            selected = orders[strategy]
            model = make_model(seed + 10_000)
            model.fit(x_candidates.iloc[selected], y_candidates[selected])
            prediction = model.predict(x_evaluation)
            for domain, domain_mask in domains.items():
                for weighting, weights in (
                    ("equal_cell", np.ones(int(domain_mask.sum()), dtype=float)),
                    ("spherical_cell_area", area_weights[domain_mask]),
                ):
                    scores = weighted_regression_metrics(
                        y_evaluation[domain_mask],
                        prediction[domain_mask],
                        weights,
                    )
                    rows.append(
                        {
                            "year": year,
                            "validation_scheme": validation_scheme,
                            "spatial_fold": spatial_fold,
                            "budget": budget,
                            "seed": seed,
                            "strategy": strategy,
                            "domain": domain,
                            "weighting": weighting,
                            "latitude_cutoff_degrees_north": latitude_cutoff,
                            "n_evaluation": int(domain_mask.sum()),
                            **scores,
                        }
                    )
    return pd.DataFrame(rows)


def validate_cache(
    frame: pd.DataFrame,
    *,
    year: int,
    validation_scheme: str,
    spatial_fold: int,
    budget: int,
    seeds: tuple[int, ...],
    strategies: tuple[str, ...],
    latitude_cutoff: float,
) -> None:
    checks = {
        "year": set(frame["year"].astype(int)) == {year},
        "validation": set(frame["validation_scheme"]) == {validation_scheme},
        "fold": set(frame["spatial_fold"].astype(int)) == {spatial_fold},
        "budget": set(frame["budget"].astype(int)) == {budget},
        "seeds": set(frame["seed"].astype(int)) == set(seeds),
        "strategies": set(frame["strategy"]) == set(strategies),
        "domains": "global" in set(frame["domain"]),
        "weighting": set(frame["weighting"])
        == {
            "equal_cell",
            "spherical_cell_area",
        },
        "latitude cutoff": set(frame["latitude_cutoff_degrees_north"])
        == {latitude_cutoff},
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        raise RuntimeError(f"cached audit unit mismatch: {', '.join(failed)}")


def unit_summary(metrics: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "validation_scheme",
        "year",
        "spatial_fold",
        "budget",
        "domain",
        "weighting",
        "strategy",
    ]
    return metrics.groupby(columns, as_index=False).agg(
        n_seeds=("seed", "nunique"),
        mean_bias=("bias", "mean"),
        sd_bias=("bias", "std"),
        mean_mae=("mae", "mean"),
        mean_rmse=("rmse", "mean"),
    )


def overall_summary(units: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "validation_scheme",
        "budget",
        "domain",
        "weighting",
        "strategy",
    ]
    return units.groupby(columns, as_index=False).agg(
        n_units=("mean_bias", "size"),
        mean_of_unit_bias=("mean_bias", "mean"),
        median_unit_bias=("mean_bias", "median"),
        minimum_unit_bias=("mean_bias", "min"),
        maximum_unit_bias=("mean_bias", "max"),
        units_below_zero=("mean_bias", lambda values: int((values < 0).sum())),
        mean_of_unit_mae=("mean_mae", "mean"),
        mean_of_unit_rmse=("mean_rmse", "mean"),
    )


def paired_unit_summary(units: pd.DataFrame) -> pd.DataFrame:
    index = [
        "validation_scheme",
        "year",
        "spatial_fold",
        "budget",
        "domain",
        "weighting",
    ]
    values = ["mean_bias", "mean_mae", "mean_rmse"]
    wide = units.pivot(index=index, columns="strategy", values=values)
    wide.columns = [f"{metric}_{strategy}" for metric, strategy in wide.columns]
    wide = wide.reset_index()
    for metric in values:
        wide[f"{metric}_difference"] = (
            wide[f"{metric}_historical_density"] - wide[f"{metric}_random"]
        )
    return wide


def paired_overall_summary(paired: pd.DataFrame) -> pd.DataFrame:
    columns = ["validation_scheme", "budget", "domain", "weighting"]
    rows: list[dict[str, float | int | str]] = []
    for keys, group in paired.groupby(columns, sort=True):
        row: dict[str, float | int | str] = dict(zip(columns, keys, strict=True))
        row["n_units"] = len(group)
        for metric in ("mean_bias", "mean_mae", "mean_rmse"):
            differences = group[f"{metric}_difference"]
            row[f"mean_{metric}_random"] = float(group[f"{metric}_random"].mean())
            row[f"mean_{metric}_historical_density"] = float(
                group[f"{metric}_historical_density"].mean()
            )
            row[f"mean_{metric}_difference"] = float(differences.mean())
            row[f"median_{metric}_difference"] = float(differences.median())
            row[f"units_{metric}_difference_below_zero"] = int((differences < 0).sum())
        rows.append(row)
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    if not np.isclose(args.latitude_cutoff, 60.0):
        raise ValueError("the published audit locks latitude-cutoff at 60°N")
    osse = yaml.safe_load(args.osse_config.read_text(encoding="utf-8"))
    block = yaml.safe_load(args.block_config.read_text(encoding="utf-8"))
    years = tuple(int(value) for value in block["source"]["years"])
    seeds = tuple(int(value) for value in block["execution"]["seeds"])
    processing = osse["processing"]
    experiment = osse["experiment"]
    density = experiment["historical_density"]
    socat = read_socat_monthly(density["socat_path"])
    coverage = experiment["coverage_blocks"]
    block_validation = block["validation"]
    args.work_directory.mkdir(parents=True, exist_ok=True)
    metric_frames: list[pd.DataFrame] = []

    for year in years:
        path = Path(str(processing["processed_file_template"]).format(year=year))
        base_frame = load_frame(path)
        base_weights = historical_density_weights(
            base_frame,
            socat,
            year_start=int(density["year_start"]),
            year_end=int(density["year_end"]),
            weight_column=str(density["weight_column"]),
        )
        hidden_positions = stratified_evaluation_positions(
            base_frame,
            fraction=float(experiment["evaluation"]["fraction"]),
            seed=int(experiment["evaluation"]["seed"]),
        )
        units = [("hidden_cells", -1, hidden_positions)]

        block_frame = add_spatial_folds(
            base_frame,
            lon_block_degrees=float(block_validation["longitude_degrees"]),
            lat_block_degrees=float(block_validation["latitude_degrees"]),
            n_folds=int(block_validation["n_folds"]),
        )
        for fold in (int(value) for value in block_validation["folds"]):
            positions = np.flatnonzero(
                block_frame["spatial_fold"].to_numpy(dtype=int) == fold
            )
            units.append(("whole_blocks", fold, positions))

        for validation_scheme, fold, positions in units:
            cache = (
                args.work_directory / f"metrics_{year}_{validation_scheme}_{fold}.csv"
            )
            if cache.exists():
                metrics = pd.read_csv(cache)
                if "latitude_cutoff_degrees_north" not in metrics:
                    metrics["latitude_cutoff_degrees_north"] = args.latitude_cutoff
                    metrics.to_csv(cache, index=False)
                validate_cache(
                    metrics,
                    year=year,
                    validation_scheme=validation_scheme,
                    spatial_fold=fold,
                    budget=args.budget,
                    seeds=seeds,
                    strategies=("random", "historical_density"),
                    latitude_cutoff=args.latitude_cutoff,
                )
            else:
                frame = (
                    block_frame if validation_scheme == "whole_blocks" else base_frame
                )
                metrics = evaluate_unit(
                    frame,
                    base_weights,
                    positions,
                    year=year,
                    validation_scheme=validation_scheme,
                    spatial_fold=fold,
                    budget=args.budget,
                    seeds=seeds,
                    longitude_degrees=float(coverage["longitude_degrees"]),
                    latitude_degrees=float(coverage["latitude_degrees"]),
                    latitude_cutoff=args.latitude_cutoff,
                    strategies=("random", "historical_density"),
                )
                metrics.to_csv(cache, index=False)
            metric_frames.append(metrics)
            print(f"complete: {year} {validation_scheme} fold={fold}", flush=True)

    metrics = pd.concat(metric_frames, ignore_index=True)
    units = unit_summary(metrics)
    overall = overall_summary(units)
    paired = paired_unit_summary(units)
    paired_overall = paired_overall_summary(paired)
    for path in (
        args.metrics_output,
        args.unit_output,
        args.overall_output,
        args.paired_output,
        args.paired_overall_output,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.metrics_output, index=False)
    units.to_csv(args.unit_output, index=False)
    overall.to_csv(args.overall_output, index=False)
    paired.to_csv(args.paired_output, index=False)
    paired_overall.to_csv(args.paired_overall_output, index=False)
    print("\nOverall audit:\n")
    print(overall.to_string(index=False))
    print("\nPaired audit:\n")
    print(paired_overall.to_string(index=False))


if __name__ == "__main__":
    main()
