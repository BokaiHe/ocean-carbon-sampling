"""Run the minimal fixed-budget sampling comparison on the 2005 OSSE cube."""

from __future__ import annotations

import argparse
import hashlib
from pathlib import Path

import pandas as pd
import xarray as xr
import yaml

from ocean_carbon_sampling.data import read_socat_monthly
from ocean_carbon_sampling.osse_experiment import (
    historical_density_weights,
    run_osse_gate,
    stratified_evaluation_positions,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="configs/osse_pilot.yaml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    processing = config["processing"]
    experiment = config["experiment"]
    gate = experiment["execution_gate"]

    with xr.open_dataset(
        processing["processed_file"], engine="h5netcdf", decode_times=True
    ) as dataset:
        frame = (
            dataset[["spco2", "tos", "sos"]]
            .to_dataframe()
            .dropna()
            .reset_index()
            .rename(columns={"time": "date", "tos": "sst", "sos": "salinity"})
        )
    frame["month"] = frame["date"].dt.month
    frame["observation_id"] = range(len(frame))

    density_config = experiment["historical_density"]
    socat = read_socat_monthly(density_config["socat_path"])
    weights = historical_density_weights(
        frame,
        socat,
        year_start=int(density_config["year_start"]),
        year_end=int(density_config["year_end"]),
        weight_column=density_config["weight_column"],
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
        budgets=tuple(int(value) for value in gate["budgets"]),
        seeds=tuple(int(value) for value in gate["seeds"]),
        longitude_degrees=float(coverage["longitude_degrees"]),
        latitude_degrees=float(coverage["latitude_degrees"]),
        extreme_value_threshold=float(
            evaluation_config["extreme_value_sensitivity_threshold"]
        ),
    )

    metrics_path = Path(gate["metrics_file"])
    selections_path = Path(gate["selections_file"])
    design_path = Path(gate["design_file"])
    summary_path = Path(gate["summary_file"])
    paired_path = Path(gate["paired_effects_file"])
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(metrics_path, index=False)
    selections.to_csv(selections_path, index=False)
    evaluation_digest = hashlib.sha256(evaluation.tobytes()).hexdigest()
    design = pd.DataFrame(
        [
            {
                "pilot_year": int(processing["pilot_year"]),
                "n_complete_month_cells": len(frame),
                "n_evaluation": len(evaluation),
                "evaluation_fraction_realized": len(evaluation) / len(frame),
                "evaluation_seed": int(evaluation_config["seed"]),
                "extreme_value_sensitivity_threshold": float(
                    evaluation_config["extreme_value_sensitivity_threshold"]
                ),
                "evaluation_positions_sha256": evaluation_digest,
                "historical_year_start": int(density_config["year_start"]),
                "historical_year_end": int(density_config["year_end"]),
                "positive_historical_month_cells": int((weights > 0).sum()),
                "budgets": ";".join(str(value) for value in gate["budgets"]),
                "seeds": ";".join(str(value) for value in gate["seeds"]),
            }
        ]
    )
    design.to_csv(design_path, index=False)

    summary = (
        metrics.groupby(
            ["evaluation_domain", "strategy", "budget"], as_index=False
        )
        .agg(
            mean_rmse=("rmse", "mean"),
            sd_rmse=("rmse", "std"),
            mean_mae=("mae", "mean"),
            mean_r2=("r2", "mean"),
            mean_correlation=("correlation", "mean"),
            n_seeds=("seed", "nunique"),
        )
        .sort_values(["evaluation_domain", "budget", "mean_rmse"])
    )
    summary.to_csv(summary_path, index=False)
    paired_rows: list[dict[str, object]] = []
    for domain in metrics["evaluation_domain"].unique():
        domain_metrics = metrics.loc[metrics["evaluation_domain"] == domain]
        for budget in sorted(domain_metrics["budget"].unique()):
            budget_metrics = domain_metrics.loc[domain_metrics["budget"] == budget]
            for seed in sorted(budget_metrics["seed"].unique()):
                seed_metrics = budget_metrics.loc[budget_metrics["seed"] == seed].set_index(
                    "strategy"
                )
                for strategy in ("spatial_coverage", "historical_density"):
                    for metric in ("rmse", "mae"):
                        paired_rows.append(
                            {
                                "evaluation_domain": domain,
                                "budget": budget,
                                "seed": seed,
                                "comparison": f"{strategy}_minus_random",
                                "metric": metric,
                                "difference": float(
                                    seed_metrics.loc[strategy, metric]
                                    - seed_metrics.loc["random", metric]
                                ),
                            }
                        )
    pd.DataFrame(paired_rows).to_csv(paired_path, index=False)
    print(summary.to_string(index=False))
    print(f"\nCommon evaluation cells: {len(evaluation):,}")


if __name__ == "__main__":
    main()
