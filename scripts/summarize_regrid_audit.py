"""Compare equal-weight and native-cell-area-weighted OSSE results."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
import xarray as xr
import yaml

from ocean_carbon_sampling.osse_experiment import summarize_paired_effects


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/osse_pilot.yaml")
    return parser.parse_args()


def _field_comparison(
    *, processing: dict[str, object], years: list[int]
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for year in years:
        baseline_path = Path(
            str(processing["processed_file_template"]).format(year=year)
        )
        weighted_path = Path(
            str(processing["area_weighted_processed_file_template"]).format(
                year=year
            )
        )
        with (
            xr.open_dataset(baseline_path, engine="h5netcdf") as baseline,
            xr.open_dataset(weighted_path, engine="h5netcdf") as weighted,
        ):
            for variable in ("spco2", "tos", "sos"):
                first = baseline[variable].values.astype(float)
                second = weighted[variable].values.astype(float)
                valid = np.isfinite(first) & np.isfinite(second)
                difference = second[valid] - first[valid]
                absolute = np.abs(difference)
                rows.append(
                    {
                        "year": year,
                        "variable": variable,
                        "n_common_values": int(valid.sum()),
                        "mean_difference": float(difference.mean()),
                        "mean_absolute_difference": float(absolute.mean()),
                        "median_absolute_difference": float(np.median(absolute)),
                        "p95_absolute_difference": float(
                            np.quantile(absolute, 0.95)
                        ),
                        "maximum_absolute_difference": float(absolute.max()),
                        "correlation": float(np.corrcoef(first[valid], second[valid])[0, 1]),
                    }
                )
    return pd.DataFrame(rows)


def _method_effects(
    baseline: pd.DataFrame, weighted: pd.DataFrame
) -> pd.DataFrame:
    keys = [
        "year",
        "evaluation_domain",
        "budget",
        "seed",
        "comparison",
        "metric",
    ]
    merged = baseline.merge(
        weighted,
        on=keys,
        how="inner",
        validate="one_to_one",
        suffixes=("_equal_weight", "_area_weighted"),
    )
    if len(merged) != len(baseline) or len(merged) != len(weighted):
        raise ValueError("regridding result tables do not have identical design rows")
    merged["difference"] = (
        merged["difference_area_weighted"] - merged["difference_equal_weight"]
    )
    return merged


def _stability_gate(weighted_summary: pd.DataFrame) -> pd.DataFrame:
    rules = [
        ("historical_density_minus_random", "rmse", "positive"),
        ("spatial_coverage_minus_random", "rmse", "negative"),
        ("spatial_coverage_minus_random", "p99_absolute_error", "negative"),
        ("spatial_coverage_minus_random", "median_absolute_error", "positive"),
    ]
    rows: list[dict[str, object]] = []
    source = weighted_summary.loc[
        (weighted_summary["evaluation_domain"] == "all")
        & (weighted_summary["budget"] == 5000)
    ]
    for comparison, metric, expected in rules:
        selected = source.loc[
            (source["comparison"] == comparison) & (source["metric"] == metric)
        ].sort_values("year")
        for row in selected.itertuples(index=False):
            positive = expected == "positive"
            direction_pass = row.mean_difference > 0 if positive else row.mean_difference < 0
            interval_pass = (
                row.seed_bootstrap_low > 0
                if positive
                else row.seed_bootstrap_high < 0
            )
            rows.append(
                {
                    "year": row.year,
                    "comparison": comparison,
                    "metric": metric,
                    "expected_direction": expected,
                    "mean_difference": row.mean_difference,
                    "seed_bootstrap_low": row.seed_bootstrap_low,
                    "seed_bootstrap_high": row.seed_bootstrap_high,
                    "direction_pass": direction_pass,
                    "interval_direction_consistent": interval_pass,
                }
            )
    return pd.DataFrame(rows)


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    processing = config["processing"]
    baseline_config = config["experiment"]["cross_year"]
    audit_config = config["experiment"]["regrid_audit"]
    years = [int(value) for value in audit_config["years"]]
    baseline = pd.read_csv(baseline_config["paired_effects_file"])
    weighted = pd.read_csv(audit_config["paired_effects_file"])
    weighted_summary = pd.read_csv(audit_config["paired_summary_file"])

    field_comparison = _field_comparison(processing=processing, years=years)
    method_effects = _method_effects(baseline, weighted)
    method_summary = summarize_paired_effects(
        method_effects,
        n_resamples=int(audit_config["bootstrap_resamples"]),
        seed=int(audit_config["bootstrap_seed"]),
    ).rename(
        columns={
            "mean_difference": "mean_area_weighting_change",
            "sd_difference": "sd_area_weighting_change",
            "fraction_difference_below_zero": "fraction_change_below_zero",
        }
    )
    gate = _stability_gate(weighted_summary)
    outputs = {
        audit_config["field_comparison_file"]: field_comparison,
        audit_config["method_effects_file"]: method_effects,
        audit_config["method_summary_file"]: method_summary,
        audit_config["stability_gate_file"]: gate,
    }
    for output, frame in outputs.items():
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        frame.to_csv(path, index=False)
    print(field_comparison.to_string(index=False))
    print(f"\nQualitative stability gate: {bool(gate['direction_pass'].all())}")
    print(gate.to_string(index=False))


if __name__ == "__main__":
    main()
