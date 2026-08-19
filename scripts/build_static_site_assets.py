"""Build the frozen JSON contract and PNG maps for the static portfolio site."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import xarray as xr
import yaml
from matplotlib.collections import PatchCollection
from matplotlib.colors import Normalize
from matplotlib.patches import Rectangle

from ocean_carbon_sampling.data import read_socat_monthly
from ocean_carbon_sampling.osse_experiment import historical_spatial_weights

WEIGHT_LABELS = {
    "equal": "Equal-cell weighting",
    "area": "Spherical cell-area weighting",
}
DOMAIN_LABELS = {
    "global": "Full model domain",
    "eval60": "Evaluation restricted to <60°N",
    "both60": "Candidates and evaluation restricted to <60°N",
}
SCHEME_LABELS = {
    "hidden": "Month-stratified hidden cells",
    "block": "Whole-spatial-block holdout",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/osse_pilot.yaml"))
    parser.add_argument("--results-dir", type=Path, default=Path("results/public"))
    parser.add_argument("--site-dir", type=Path, default=Path("site"))
    parser.add_argument("--year", type=int, default=2005)
    return parser.parse_args()


def _metric_payload(
    *,
    random_value: float,
    comparator_value: float,
    difference: float,
    n_units: int,
    units_below_zero: int,
    metric: str,
) -> dict[str, float | int | str | None]:
    if metric == "bias":
        direction = f"{units_below_zero}/{n_units} negative"
        relative = None
    else:
        units_worse = n_units - units_below_zero
        direction = f"{units_worse}/{n_units} worse"
        relative = 100.0 * difference / random_value
    return {
        "random": round(float(random_value), 3),
        "comparator": round(float(comparator_value), 3),
        "difference": round(float(difference), 3),
        "relative_pct": None if relative is None else round(float(relative), 2),
        "direction": direction,
        "n_units": int(n_units),
    }


def _pack_area_row(row: pd.Series) -> dict[str, object]:
    n_units = int(row["n_units"])
    metrics = {}
    for metric in ("bias", "mae", "rmse"):
        metrics[metric] = _metric_payload(
            random_value=row[f"mean_mean_{metric}_random"],
            comparator_value=row[f"mean_mean_{metric}_historical_density"],
            difference=row[f"mean_mean_{metric}_difference"],
            n_units=n_units,
            units_below_zero=int(row[f"units_mean_{metric}_difference_below_zero"]),
            metric=metric,
        )
    return {"n_units": n_units, "metrics": metrics}


def _pack_cap_row(row: pd.Series) -> dict[str, object]:
    n_units = int(row["n_units"])
    metrics = {}
    for metric in ("bias", "mae", "rmse"):
        metrics[metric] = _metric_payload(
            random_value=row[f"mean_random_{metric}"],
            comparator_value=row[f"mean_comparator_{metric}"],
            difference=row[f"mean_difference_{metric}"],
            n_units=n_units,
            units_below_zero=int(row[f"units_difference_{metric}_below_zero"]),
            metric=metric,
        )
    return {"n_units": n_units, "metrics": metrics}


def build_estimands(results_dir: Path) -> dict[str, object]:
    area = pd.read_csv(results_dir / "osse_historical_area_domain_paired_overall.csv")
    cap = pd.read_csv(results_dir / "osse_latitude_cap_overall.csv")
    estimands: dict[str, object] = {}
    scheme_sources = {
        "hidden": "hidden_cells",
        "block": "whole_blocks",
    }
    for scheme, source_scheme in scheme_sources.items():
        for weight, source_weight in {
            "equal": "equal_cell",
            "area": "spherical_cell_area",
        }.items():
            for domain, source_domain in {
                "global": "global",
                "eval60": "south_of_60n",
            }.items():
                matches = area.loc[
                    (area["validation_scheme"] == source_scheme)
                    & (area["weighting"] == source_weight)
                    & (area["domain"] == source_domain)
                    & (area["budget"] == 5000)
                ]
                if len(matches) != 1:
                    raise RuntimeError(f"Expected one area/domain row, found {len(matches)}")
                key = f"{weight}|{domain}|{scheme}"
                estimands[key] = {
                    **_pack_area_row(matches.iloc[0]),
                    "weight": weight,
                    "domain": domain,
                    "scheme": scheme,
                    "label": (
                        f"{WEIGHT_LABELS[weight]} · {DOMAIN_LABELS[domain]} · "
                        f"{SCHEME_LABELS[scheme]}"
                    ),
                    "status": "supporting",
                }

            cap_scheme = f"{source_scheme}_latitude_cap"
            matches = cap.loc[
                (cap["validation_scheme"] == cap_scheme)
                & (cap["weighting"] == source_weight)
                & (cap["domain"] == "south_of_60n")
                & (cap["comparison"] == "historical_density_minus_random")
                & (cap["budget"] == 5000)
            ]
            if len(matches) != 1:
                raise RuntimeError(f"Expected one aligned-domain row, found {len(matches)}")
            key = f"{weight}|both60|{scheme}"
            estimands[key] = {
                **_pack_cap_row(matches.iloc[0]),
                "weight": weight,
                "domain": "both60",
                "scheme": scheme,
                "label": (
                    f"{WEIGHT_LABELS[weight]} · {DOMAIN_LABELS['both60']} · "
                    f"{SCHEME_LABELS[scheme]}"
                ),
                "status": "default" if key == "area|both60|block" else "supporting",
            }
    if len(estimands) != 12:
        raise RuntimeError(f"Expected 12 estimand states, found {len(estimands)}")
    return estimands


def build_sample_sweep(results_dir: Path) -> dict[str, object]:
    claims = pd.read_csv(results_dir / "osse_claim_distribution_summary.csv")
    selected = claims.query(
        "validation_scheme == 'month_stratified_hidden_cells' and "
        "comparison == 'spatial_coverage_minus_random' and "
        "metric in ['median_absolute_error', 'p99_absolute_error', 'rmse']"
    )
    sweep: dict[str, object] = {}
    for budget, group in selected.groupby("budget", sort=True):
        metrics = {}
        for _, row in group.iterrows():
            metric = str(row["metric"])
            metrics[metric] = {
                "random": round(float(row["mean_random_baseline"]), 3),
                "coverage": round(float(row["mean_comparator_value"]), 3),
                "difference": round(float(row["mean_difference"]), 3),
                "relative_pct": round(
                    float(row["mean_relative_error_change_percent"]), 2
                ),
                "direction": (
                    f"{int(row['units_below_zero'])}/{int(row['n_units'])} years below zero"
                ),
            }
        sweep[str(int(budget))] = {"budget": int(budget), "metrics": metrics}
    expected = {"500", "1000", "2500", "5000"}
    if set(sweep) != expected:
        raise RuntimeError(f"Unexpected sample-count states: {sorted(sweep)}")
    return sweep


def build_audits(results_dir: Path) -> dict[str, object]:
    month = pd.read_csv(results_dir / "osse_month_balance_strategy_summary.csv")
    month = month.query("budget == 5000").set_index("strategy")
    regrid = pd.read_csv(results_dir / "osse_regrid_audit_stability_gate.csv")
    return {
        "month_balance": {
            strategy: {
                "selections": int(row["n_year_fold_seed_selections"]),
                "minimum_months_covered": int(row["minimum_months_covered"]),
                "mean_abs_equal_deviation_pp": round(
                    float(row["mean_abs_equal_deviation_pp"]), 3
                ),
            }
            for strategy, row in month.iterrows()
        },
        "regridding": {
            "direction_checks": len(regrid),
            "direction_checks_passed": int(regrid["direction_pass"].sum()),
            "note": "Correlated metrics are not independent tests.",
        },
        "replication": {
            "years": [2005, 2010, 2014],
            "spatial_folds": 5,
            "year_fold_units": 15,
            "paired_seeds_per_unit": 20,
            "interpretation": "Descriptive consistency units; no formal whole-block significance test.",
        },
    }


def load_complete_density(config: dict, year: int) -> pd.DataFrame:
    processing = config["processing"]
    path = Path(str(processing["processed_file_template"]).format(year=year))
    with xr.open_dataset(path, engine="h5netcdf", decode_times=True) as dataset:
        frame = (
            dataset[["spco2", "tos", "sos"]]
            .to_dataframe()
            .dropna()
            .reset_index()
            .rename(columns={"time": "date", "tos": "sst", "sos": "salinity"})
        )
    density_config = config["experiment"]["historical_density"]
    socat = read_socat_monthly(density_config["socat_path"])
    weights = historical_spatial_weights(
        frame,
        socat,
        year_start=int(density_config["year_start"]),
        year_end=int(density_config["year_end"]),
        weight_column=str(density_config["weight_column"]),
    )
    density = frame[["latitude", "longitude"]].copy()
    density["historical_spatial_density"] = weights
    return density.groupby(["latitude", "longitude"], as_index=False).first()


def _raster(frame: pd.DataFrame, column: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    pivot = frame.pivot(index="latitude", columns="longitude", values=column)
    return (
        pivot.to_numpy(),
        pivot.columns.to_numpy(dtype=float),
        pivot.index.to_numpy(dtype=float),
    )


def render_sampling_maps(
    *,
    sampling: pd.DataFrame,
    density: pd.DataFrame,
    output_dir: Path,
) -> dict[str, dict[str, str]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    valid = density.assign(valid=1.0)
    ocean, longitudes, latitudes = _raster(valid, "valid")
    zero, _, _ = _raster(
        density.assign(
            zero=(density["historical_spatial_density"].to_numpy(dtype=float) <= 0).astype(float)
        ),
        "zero",
    )
    extent = [
        float(longitudes.min() - 0.5),
        float(longitudes.max() + 0.5),
        float(latitudes.min() - 0.5),
        float(latitudes.max() + 0.5),
    ]
    vmax = float(sampling["observations"].quantile(0.98))
    norm = Normalize(vmin=0.0, vmax=max(vmax, 1.0))
    maps: dict[str, dict[str, str]] = {}
    for strategy in ("random", "historical_density", "spatial_coverage"):
        subset = sampling.loc[sampling["strategy"] == strategy].copy()
        short = {
            "historical_density": "historical",
            "spatial_coverage": "coverage",
        }.get(strategy, strategy)
        maps[short] = {}
        for show_zero in (False, True):
            fig, ax = plt.subplots(figsize=(12.8, 6.4), dpi=150)
            fig.patch.set_facecolor("#f7f9f7")
            ax.set_facecolor("#eef1ee")
            ocean_rgba = np.zeros((*ocean.shape, 4), dtype=float)
            ocean_rgba[np.isfinite(ocean)] = (0.83, 0.89, 0.87, 1.0)
            ax.imshow(ocean_rgba, origin="lower", extent=extent, interpolation="none")
            if show_zero:
                zero_rgba = np.zeros((*zero.shape, 4), dtype=float)
                zero_rgba[zero == 1] = (0.36, 0.39, 0.40, 0.78)
                ax.imshow(zero_rgba, origin="lower", extent=extent, interpolation="none")

            patches = [
                Rectangle((row.longitude - 5.0, row.latitude - 2.5), 10.0, 5.0)
                for row in subset.itertuples(index=False)
            ]
            collection = PatchCollection(
                patches,
                cmap="YlOrRd",
                norm=norm,
                edgecolor=(1, 1, 1, 0.28),
                linewidth=0.25,
            )
            collection.set_array(subset["observations"].to_numpy(dtype=float))
            ax.add_collection(collection)
            ax.set_xlim(-180, 180)
            ax.set_ylim(-82, 90)
            ax.set_xticks([-180, -120, -60, 0, 60, 120, 180])
            ax.set_yticks([-60, -30, 0, 30, 60, 90])
            ax.tick_params(colors="#50605c", labelsize=9)
            ax.grid(color="white", linewidth=0.55, alpha=0.55)
            for spine in ax.spines.values():
                spine.set_visible(False)
            colorbar = fig.colorbar(collection, ax=ax, orientation="horizontal", pad=0.075, fraction=0.04)
            colorbar.set_label("Selected observations per 5° × 10° block", color="#35423f", fontsize=9)
            colorbar.ax.tick_params(labelsize=8, colors="#50605c")
            suffix = "zero" if show_zero else "base"
            filename = f"sampling_{short}_{suffix}.png"
            fig.savefig(output_dir / filename, bbox_inches="tight", facecolor=fig.get_facecolor())
            plt.close(fig)
            maps[short][suffix] = f"assets/maps/{filename}"
    return maps


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    site_data_dir = args.site_dir / "data"
    map_dir = args.site_dir / "assets" / "maps"
    site_data_dir.mkdir(parents=True, exist_ok=True)
    sampling = pd.read_parquet(args.results_dir / "osse_visual_demo_sampling.parquet")
    density = load_complete_density(config, args.year)
    maps = render_sampling_maps(sampling=sampling, density=density, output_dir=map_dir)
    coverage = pd.read_csv(args.results_dir / "osse_historical_spatial_coverage_2005.csv")
    zero = coverage.set_index("coverage_group").loc["zero_density"]

    payload = {
        "metadata": {
            "title": "Ocean Carbon Sampling",
            "generated_from": "Frozen results/public tables",
            "map_year": args.year,
            "sample_count": 5000,
            "default_estimand": "area|both60|block",
            "default_comparison": "historical density minus random",
        },
        "maps": {
            "images": maps,
            "zero_coverage_cell_pct": round(100.0 * float(zero["cell_fraction"]), 1),
            "zero_coverage_area_pct": round(
                100.0 * float(zero["spherical_area_fraction"]), 1
            ),
            "zero_coverage_cells": int(zero["n_spatial_cells"]),
            "definition": (
                "SOCAT 1990–2004 historical spatial-marginal weight equals zero "
                "on the complete 2005 mapped model domain."
            ),
        },
        "estimands": build_estimands(args.results_dir),
        "estimand_journey": [
            "equal|global|block",
            "area|global|block",
            "area|eval60|block",
            "area|both60|block",
        ],
        "sample_sweep": build_sample_sweep(args.results_dir),
        "audits": build_audits(args.results_dir),
    }
    output = site_data_dir / "site-data.json"
    output.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {output}")
    print(f"wrote {sum(len(value) for value in maps.values())} map PNGs to {map_dir}")


if __name__ == "__main__":
    main()
