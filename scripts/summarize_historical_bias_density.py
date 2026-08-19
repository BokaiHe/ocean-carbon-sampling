"""Relate local historical signed error to SOCAT spatial density."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml
from scipy.stats import spearmanr

from ocean_carbon_sampling.data import read_socat_monthly
from ocean_carbon_sampling.osse_experiment import (
    historical_spatial_weights,
    spherical_cell_area_weights,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/osse_pilot.yaml"))
    parser.add_argument("--year", type=int, default=2005)
    parser.add_argument(
        "--map-input",
        type=Path,
        default=Path("results/public/osse_historical_bias_map_2005.parquet"),
    )
    parser.add_argument(
        "--cell-output",
        type=Path,
        default=Path("results/public/osse_historical_bias_density_cells_2005.parquet"),
    )
    parser.add_argument(
        "--bin-output",
        type=Path,
        default=Path("results/public/osse_historical_bias_density_bins_2005.csv"),
    )
    parser.add_argument(
        "--summary-output",
        type=Path,
        default=Path("results/public/osse_historical_bias_density_summary_2005.csv"),
    )
    parser.add_argument(
        "--decomposition-output",
        type=Path,
        default=Path(
            "results/public/osse_historical_bias_domain_decomposition_2005.csv"
        ),
    )
    parser.add_argument(
        "--coverage-output",
        type=Path,
        default=Path("results/public/osse_historical_spatial_coverage_2005.csv"),
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


def summarize_bins(cells: pd.DataFrame) -> pd.DataFrame:
    positive = cells.loc[cells["historical_spatial_density"] > 0].copy()
    positive["density_bin"] = (
        pd.qcut(
            positive["historical_spatial_density"],
            q=10,
            labels=False,
            duplicates="drop",
        )
        + 1
    )
    zero = cells.loc[cells["historical_spatial_density"] == 0].copy()
    zero["density_bin"] = 0
    grouped = pd.concat([zero, positive], ignore_index=True)
    rows: list[dict[str, float | int]] = []
    columns = (
        "signed_error_historical_density",
        "signed_error_historical_spatial_month_balanced",
    )
    for density_bin, group in grouped.groupby("density_bin", sort=True):
        row: dict[str, float | int] = {
            "density_bin": int(density_bin),
            "n_cells": len(group),
            "density_min": float(group["historical_spatial_density"].min()),
            "density_median": float(group["historical_spatial_density"].median()),
            "density_max": float(group["historical_spatial_density"].max()),
        }
        for column in columns:
            row[f"{column}_mean"] = float(group[column].mean())
            row[f"{column}_median"] = float(group[column].median())
            row[f"{column}_q25"] = float(group[column].quantile(0.25))
            row[f"{column}_q75"] = float(group[column].quantile(0.75))
        rows.append(row)
    return pd.DataFrame(rows)


def decompose_signed_bias(cells: pd.DataFrame) -> pd.DataFrame:
    """Decompose each domain mean into zero- and positive-density contributions."""
    responses = (
        "signed_error_historical_density",
        "signed_error_historical_spatial_month_balanced",
    )
    domains = {
        "global": np.ones(len(cells), dtype=bool),
        "south_of_60n": cells["latitude"].to_numpy(dtype=float) < 60.0,
        "60_to_90n": cells["latitude"].to_numpy(dtype=float) >= 60.0,
    }
    weighting_schemes = {
        "equal_cell": np.ones(len(cells), dtype=float),
        "spherical_cell_area": spherical_cell_area_weights(cells["latitude"]),
    }
    positive = cells["historical_spatial_density"].to_numpy(dtype=float) > 0
    coverage_groups = {
        "all": np.ones(len(cells), dtype=bool),
        "zero_density": ~positive,
        "positive_density": positive,
    }
    rows: list[dict[str, float | int | str]] = []
    for domain, domain_mask in domains.items():
        n_domain = int(domain_mask.sum())
        for weighting, weights in weighting_schemes.items():
            domain_weight = float(weights[domain_mask].sum())
            global_weight = float(weights.sum())
            for response in responses:
                errors = cells[response].to_numpy(dtype=float)
                for coverage_group, coverage_mask in coverage_groups.items():
                    selected = domain_mask & coverage_mask
                    selected_weight = float(weights[selected].sum())
                    weighted_error_sum = float(
                        np.sum(weights[selected] * errors[selected])
                    )
                    rows.append(
                        {
                            "domain": domain,
                            "weighting": weighting,
                            "response": response,
                            "coverage_group": coverage_group,
                            "n_cells": int(selected.sum()),
                            "cell_fraction_of_domain": float(selected.sum() / n_domain),
                            "weight_fraction_of_domain": selected_weight
                            / domain_weight,
                            "weight_fraction_of_global": selected_weight
                            / global_weight,
                            "group_mean_signed_error": weighted_error_sum
                            / selected_weight,
                            "contribution_to_domain_mean": weighted_error_sum
                            / domain_weight,
                            "contribution_to_global_mean": weighted_error_sum
                            / global_weight,
                        }
                    )
    result = pd.DataFrame(rows)
    for keys, group in result.loc[result["coverage_group"] != "all"].groupby(
        ["domain", "weighting", "response"]
    ):
        total = result.loc[
            (result["domain"] == keys[0])
            & (result["weighting"] == keys[1])
            & (result["response"] == keys[2])
            & (result["coverage_group"] == "all"),
            "contribution_to_domain_mean",
        ].item()
        if not np.isclose(group["contribution_to_domain_mean"].sum(), total):
            raise RuntimeError("coverage contributions do not sum to domain mean")
    latitude_rows = result.loc[
        (result["coverage_group"] == "all")
        & result["domain"].isin(["south_of_60n", "60_to_90n"])
    ]
    for keys, group in latitude_rows.groupby(["weighting", "response"]):
        total = result.loc[
            (result["domain"] == "global")
            & (result["weighting"] == keys[0])
            & (result["response"] == keys[1])
            & (result["coverage_group"] == "all"),
            "contribution_to_global_mean",
        ].item()
        if not np.isclose(group["contribution_to_global_mean"].sum(), total):
            raise RuntimeError("latitude-band contributions do not sum to global mean")
    return result


def summarize_spatial_coverage(density: pd.DataFrame) -> pd.DataFrame:
    """Describe structural zero coverage over the complete mapped domain."""
    area = spherical_cell_area_weights(density["latitude"])
    positive = density["historical_spatial_density"].to_numpy(dtype=float) > 0
    total_area = float(area.sum())
    rows: list[dict[str, float | int | str]] = []
    for group, mask in (
        ("all", np.ones(len(density), dtype=bool)),
        ("zero_density", ~positive),
        ("positive_density", positive),
    ):
        rows.append(
            {
                "coverage_group": group,
                "n_spatial_cells": int(mask.sum()),
                "cell_fraction": float(mask.mean()),
                "spherical_area_fraction": float(area[mask].sum() / total_area),
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(args.config.read_text(encoding="utf-8"))
    processed = Path(
        str(config["processing"]["processed_file_template"]).format(year=args.year)
    )
    frame = load_frame(processed)
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
    density = density.groupby(["latitude", "longitude"], as_index=False).first()
    coverage = summarize_spatial_coverage(density)
    maps = pd.read_parquet(args.map_input)
    cells = maps.merge(
        density,
        on=["latitude", "longitude"],
        how="left",
        validate="one_to_one",
    )
    if cells["historical_spatial_density"].isna().any():
        raise RuntimeError("historical spatial density is missing for map cells")
    cells["log10_one_plus_density"] = np.log10(
        1.0 + cells["historical_spatial_density"]
    )

    summary_rows: list[dict[str, float | int | str]] = []
    for scope, subset in (
        ("all_cells", cells),
        ("positive_density_cells", cells.loc[cells["historical_spatial_density"] > 0]),
    ):
        for column in (
            "signed_error_historical_density",
            "signed_error_historical_spatial_month_balanced",
        ):
            rho, pvalue = spearmanr(
                subset["historical_spatial_density"], subset[column]
            )
            summary_rows.append(
                {
                    "scope": scope,
                    "response": column,
                    "n_cells": len(subset),
                    "spearman_rho": float(rho),
                    "nominal_p_value_not_for_inference": float(pvalue),
                    "note": "grid cells are spatially dependent; p is descriptive only",
                }
            )
    bins = summarize_bins(cells)
    decomposition = decompose_signed_bias(cells)
    summary = pd.DataFrame(summary_rows)
    for path in (
        args.cell_output,
        args.bin_output,
        args.summary_output,
        args.decomposition_output,
        args.coverage_output,
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
    float_columns = cells.select_dtypes(include=["number"]).columns
    cells[float_columns] = cells[float_columns].astype("float32")
    cells.to_parquet(args.cell_output, index=False)
    bins.to_csv(args.bin_output, index=False)
    summary.to_csv(args.summary_output, index=False)
    decomposition.to_csv(args.decomposition_output, index=False)
    coverage.to_csv(args.coverage_output, index=False)
    print(summary.to_string(index=False))
    print("\nBinned relationship:\n")
    print(bins.to_string(index=False))
    print("\nSigned-bias decomposition:\n")
    print(decomposition.to_string(index=False))
    print("\nMapped-domain historical spatial coverage:\n")
    print(coverage.to_string(index=False))


if __name__ == "__main__":
    main()
