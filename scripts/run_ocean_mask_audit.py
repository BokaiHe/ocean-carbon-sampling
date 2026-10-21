"""Rerun the latitude-cap headline audit on the M1 and M2 ocean-domain masks."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import yaml
from run_historical_area_domain_audit import evaluate_unit, load_frame, unit_summary
from run_latitude_cap_audit import paired_overall, paired_units

from ocean_carbon_sampling.data import read_socat_monthly
from ocean_carbon_sampling.osse_experiment import (
    historical_density_weights,
    stratified_evaluation_positions,
)
from ocean_carbon_sampling.splits import add_spatial_folds

STRATEGIES = ("random", "historical_density", "spatial_coverage")
MASKS = ("m1", "m2")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/osse_ocean_mask.yaml"))
    parser.add_argument(
        "--check-m0",
        action="store_true",
        help="only rerun M0 2005 hidden cells and compare with the saved audit",
    )
    return parser.parse_args()


def mask_locations(cells_file: Path) -> dict[str, set[tuple[float, float]]]:
    cells = pd.read_csv(cells_file)
    return {
        name: set(
            zip(
                cells.loc[cells[f"in_{name}"], "latitude"],
                cells.loc[cells[f"in_{name}"], "longitude"],
                strict=True,
            )
        )
        for name in MASKS
    }


def run_units(
    frame: pd.DataFrame,
    weights: np.ndarray,
    hidden: np.ndarray,
    *,
    year: int,
    mask: str,
    work: Path,
    settings: dict,
    only_hidden: bool = False,
) -> list[pd.DataFrame]:
    """Evaluate the hidden-cell unit and the five whole-block folds for one frame."""
    block = settings["block"]
    block_frame = add_spatial_folds(
        frame,
        lon_block_degrees=float(block["longitude_degrees"]),
        lat_block_degrees=float(block["latitude_degrees"]),
        n_folds=int(block["n_folds"]),
    )
    units = [("hidden_cells_latitude_cap", -1, frame, np.flatnonzero(hidden))]
    if not only_hidden:
        folds = block_frame["spatial_fold"].to_numpy(dtype=int)
        for fold in (int(value) for value in block["folds"]):
            units.append(
                ("whole_blocks_latitude_cap", fold, block_frame, np.flatnonzero(folds == fold))
            )

    results = []
    for scheme, fold, unit_frame, positions in units:
        cache = work / f"metrics_{mask}_{year}_{scheme}_{fold}.csv"
        if cache.exists():
            metrics = pd.read_csv(cache)
        else:
            metrics = evaluate_unit(
                unit_frame,
                weights,
                positions,
                year=year,
                validation_scheme=scheme,
                spatial_fold=fold,
                budget=settings["budget"],
                seeds=settings["seeds"],
                longitude_degrees=settings["coverage_longitude"],
                latitude_degrees=settings["coverage_latitude"],
                latitude_cutoff=settings["latitude_max"],
                strategies=STRATEGIES,
            )
            metrics.insert(0, "mask", mask)
            metrics.to_csv(cache, index=False)
        results.append(metrics)
        print(f"complete: {mask} {year} {scheme} fold={fold}", flush=True)
    return results


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    osse = yaml.safe_load(Path(config["source"]["osse_config"]).read_text(encoding="utf-8"))
    block = yaml.safe_load(Path(config["source"]["block_config"]).read_text(encoding="utf-8"))
    experiment = osse["experiment"]
    density = experiment["historical_density"]
    execution = config["execution"]
    settings = {
        "block": block["validation"],
        "budget": int(execution["budget"]),
        "seeds": tuple(int(seed) for seed in block["execution"]["seeds"]),
        "coverage_longitude": float(experiment["coverage_blocks"]["longitude_degrees"]),
        "coverage_latitude": float(experiment["coverage_blocks"]["latitude_degrees"]),
        "latitude_max": float(config["mask"]["latitude_max"]),
    }
    work = Path(execution["work_directory"])
    work.mkdir(parents=True, exist_ok=True)
    socat = read_socat_monthly(density["socat_path"])
    masks = mask_locations(Path(config["mask"]["cells_file"]))
    template = str(osse["processing"]["processed_file_template"])
    years = [2005] if args.check_m0 else [int(year) for year in config["source"]["years"]]

    metric_frames: list[pd.DataFrame] = []
    for year in years:
        frame = load_frame(Path(template.format(year=year)))
        frame = frame.loc[frame["latitude"] < settings["latitude_max"]].reset_index(drop=True)
        weights = historical_density_weights(
            frame,
            socat,
            year_start=int(density["year_start"]),
            year_end=int(density["year_end"]),
            weight_column=str(density["weight_column"]),
        )
        hidden = np.zeros(len(frame), dtype=bool)
        hidden[
            stratified_evaluation_positions(
                frame,
                fraction=float(experiment["evaluation"]["fraction"]),
                seed=int(experiment["evaluation"]["seed"]),
            )
        ] = True

        if args.check_m0:
            (new,) = run_units(
                frame, weights, hidden, year=year, mask="m0", work=work,
                settings=settings, only_hidden=True,
            )
            saved = pd.read_csv(
                "results/osse_latitude_cap_work/metrics_2005_hidden_cells_latitude_cap_-1.csv"
            )
            keys = ["seed", "strategy", "domain", "weighting"]
            merged = saved.merge(new, on=keys, suffixes=("_saved", "_new"))
            worst = max(
                float((merged[f"{m}_saved"] - merged[f"{m}_new"]).abs().max())
                for m in ("bias", "mae", "rmse")
            )
            print(f"M0 2005 hidden: {len(merged)} rows compared, max |difference| {worst:.3g}")
            return

        locations = list(zip(frame["latitude"], frame["longitude"], strict=True))
        for mask in MASKS:
            keep = np.fromiter((loc in masks[mask] for loc in locations), bool, len(frame))
            metric_frames += run_units(
                frame.loc[keep].reset_index(drop=True),
                weights[keep],
                hidden[keep],
                year=year,
                mask=mask,
                work=work,
                settings=settings,
            )

    metrics = pd.concat(metric_frames, ignore_index=True)
    units, paired, overall = [], [], []
    for mask, group in metrics.groupby("mask", sort=True):
        mask_units = unit_summary(group)
        mask_paired = paired_units(mask_units)
        for table, values in (
            (units, mask_units),
            (paired, mask_paired),
            (overall, paired_overall(mask_paired)),
        ):
            values.insert(0, "mask", mask)
            table.append(values)
    outputs = {
        "metrics_file": metrics,
        "unit_summary_file": pd.concat(units, ignore_index=True),
        "paired_file": pd.concat(paired, ignore_index=True),
        "overall_file": pd.concat(overall, ignore_index=True),
    }
    for key, table in outputs.items():
        table.to_csv(execution[key], index=False)
    print(outputs["overall_file"].to_string(index=False))


if __name__ == "__main__":
    main()
