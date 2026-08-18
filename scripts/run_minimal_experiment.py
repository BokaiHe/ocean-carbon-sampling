"""Run and visualize the preregistered Southern Ocean minimum experiment."""

from __future__ import annotations

import argparse
from pathlib import Path

import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import yaml

from ocean_carbon_sampling.data import read_socat_monthly, select_southern_ocean
from ocean_carbon_sampling.experiment import ExperimentSettings, run_regime
from ocean_carbon_sampling.splits import add_spatial_folds, add_validation_regimes

COLORS = {"random": "#8A949C", "coverage": "#2D6F9F"}
LABELS = {"random": "Random", "coverage": "Coverage"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=Path("configs/minimal.yaml"))
    parser.add_argument("--output", type=Path, default=Path("results/public"))
    return parser.parse_args()


def load_settings(path: Path) -> tuple[dict, ExperimentSettings]:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    sampling = config["sampling"]
    coverage = sampling["coverage_cells"]
    settings = ExperimentSettings(
        seed=int(config["experiment"]["seed"]),
        initial_fraction=float(sampling["initial_fraction"]),
        budgets=tuple(float(value) for value in sampling["budgets"]),
        coverage_lon_degrees=float(coverage["longitude_degrees"]),
        coverage_lat_degrees=float(coverage["latitude_degrees"]),
    )
    return config, settings


def configure_style() -> None:
    mpl.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
            "font.size": 8,
            "axes.spines.right": False,
            "axes.spines.top": False,
            "axes.linewidth": 0.8,
            "legend.frameon": False,
            "svg.fonttype": "none",
            "pdf.fonttype": 42,
        }
    )


def make_figure(metrics: pd.DataFrame, output: Path) -> None:
    """Plot locked-test RMSE; one seed means no inferential error bars."""
    configure_style()
    fig, axes = plt.subplots(1, 2, figsize=(7.2, 3.2), constrained_layout=True)
    panel_titles = {
        "temporal": "a  Temporal transfer: test years 2020–2024",
        "spatial": "b  Spatial transfer: held-out geographic blocks",
    }
    for axis, regime in zip(axes, ["temporal", "spatial"], strict=True):
        subset = metrics.loc[metrics["regime"] == regime]
        for strategy in ["random", "coverage"]:
            values = subset.loc[subset["strategy"] == strategy].sort_values(
                "budget_fraction"
            )
            axis.plot(
                values["budget_fraction"] * 100,
                values["rmse"],
                marker="o",
                markersize=5,
                linewidth=1.7,
                color=COLORS[strategy],
                label=LABELS[strategy],
            )
        axis.set_title(panel_titles[regime], loc="left", weight="bold")
        axis.set_xlabel("Training budget (% of development pool)")
        axis.set_ylabel("Test RMSE (µatm)")
        axis.set_xticks(sorted(metrics["budget_fraction"].unique() * 100))
        axis.grid(axis="y", color="#D9DDE0", linewidth=0.6)
    axes[0].legend(title="Sampling strategy")
    fig.suptitle(
        "Coverage sampling lowers locked-test RMSE in this single-seed run",
        fontsize=11,
        weight="bold",
    )
    output.mkdir(parents=True, exist_ok=True)
    fig.savefig(output / "minimum_experiment_rmse.png", dpi=300, bbox_inches="tight")
    fig.savefig(output / "minimum_experiment_rmse.tiff", dpi=600, bbox_inches="tight")
    fig.savefig(output / "minimum_experiment_rmse.svg", bbox_inches="tight")
    fig.savefig(output / "minimum_experiment_rmse.pdf", bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    args = parse_args()
    config, settings = load_settings(args.config)
    full = read_socat_monthly(config["data"]["raw_path"])
    study = select_southern_ocean(
        full,
        latitude_max=float(config["data"]["latitude_max"]),
        year_start=int(config["data"]["year_start"]),
        year_end=int(config["data"]["year_end"]),
    )
    complete = study.dropna(subset=["fco2", "sst", "salinity"]).copy()
    n_before = len(study)
    n_after = len(complete)
    complete = add_spatial_folds(
        complete,
        lon_block_degrees=float(
            config["validation"]["spatial_block_lon_degrees"]
        ),
        lat_block_degrees=float(
            config["validation"]["spatial_block_lat_degrees"]
        ),
    )
    complete = add_validation_regimes(
        complete,
        temporal_test_start=int(config["validation"]["temporal_test_start"]),
        spatial_test_fold=int(config["validation"]["spatial_test_fold"]),
    )

    outputs = []
    selections = []
    for regime, split_column in [
        ("temporal", "temporal_split"),
        ("spatial", "spatial_split"),
    ]:
        metrics, selection = run_regime(
            complete,
            regime=regime,
            split_column=split_column,
            settings=settings,
        )
        outputs.append(metrics)
        selections.append(selection)

    metrics = pd.concat(outputs, ignore_index=True)
    selection_summary = pd.concat(selections, ignore_index=True)
    args.output.mkdir(parents=True, exist_ok=True)
    metrics.to_csv(args.output / "minimum_experiment_metrics.csv", index=False)
    selection_summary.to_csv(
        args.output / "minimum_experiment_selection.csv", index=False
    )
    pd.DataFrame(
        {
            "stage": ["selected_domain", "complete_predictors_and_target"],
            "rows": [n_before, n_after],
            "rows_removed_at_step": [0, n_before - n_after],
        }
    ).to_csv(args.output / "minimum_experiment_attrition.csv", index=False)
    make_figure(metrics, args.output)


if __name__ == "__main__":
    main()
