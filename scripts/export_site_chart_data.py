"""Export small web-chart inputs from frozen results only; never fit models."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

SCHEMES = (
    ("hidden", "hidden_cells_latitude_cap", 3),
    ("block", "whole_blocks_latitude_cap", 15),
)
MASK_LABELS = {
    "m0": "Original model domain",
    "m1": "Connected ocean (primary)",
    "m2": "Open-ocean interior",
}


def _headline_rows(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.loc[
        (frame["budget"] == 5000)
        & (frame["domain"] == "south_of_60n")
        & (frame["weighting"] == "spherical_cell_area")
    ]


def build_mask_audit(results_dir: Path) -> dict:
    """M0 (pre-mask) and M1/M2 (masked rerun) paired summaries."""
    reference = pd.read_csv(results_dir / "osse_latitude_cap_overall.csv")
    reference.insert(0, "mask", "m0")
    masked = pd.read_csv(results_dir / "osse_ocean_mask_overall.csv")
    overall = _headline_rows(pd.concat([reference, masked], ignore_index=True))
    rows = []
    for mask, label in MASK_LABELS.items():
        for key, source, expected in SCHEMES:
            for comparison in ("historical_density", "spatial_coverage"):
                row = overall.loc[
                    (overall["mask"] == mask)
                    & (overall["validation_scheme"] == source)
                    & (overall["comparison"] == f"{comparison}_minus_random")
                ]
                if len(row) != 1 or int(row["n_units"].iloc[0]) != expected:
                    raise ValueError(f"Unexpected mask audit row: {mask} {key} {comparison}")
                row = row.iloc[0]
                rows.append(
                    {
                        "mask": mask,
                        "label": label,
                        "protocol": key,
                        "comparison": comparison,
                        "n_units": expected,
                        "random_mae": round(float(row.mean_random_mae), 3),
                        "comparator_mae": round(float(row.mean_comparator_mae), 3),
                        "difference_mae": round(float(row.mean_difference_mae), 3),
                        "relative_mae_pct": round(
                            100 * float(row.mean_difference_mae) / float(row.mean_random_mae), 2
                        ),
                        "units_mae_worse": expected
                        - int(row.units_difference_mae_below_zero),
                        "random_rmse": round(float(row.mean_random_rmse), 3),
                        "difference_rmse": round(float(row.mean_difference_rmse), 3),
                        "units_rmse_lower": int(row.units_difference_rmse_below_zero),
                    }
                )
    cells = pd.read_csv(results_dir / "osse_ocean_mask_cells.csv")
    below = cells.loc[cells["latitude"] < 60]
    return {
        "primary_mask": "m1",
        "locations_below_60n": {
            "m0": len(below),
            "m1": int(below["in_m1"].sum()),
            "m2": int(below["in_m2"].sum()),
        },
        "rows": rows,
    }


def build_chart_data(results_dir: Path) -> dict:
    paired = pd.read_csv(results_dir / "osse_ocean_mask_paired.csv")
    paired = paired.loc[paired["mask"] == "m1"]
    selected = paired.loc[
        (paired["budget"] == 5000)
        & (paired["domain"] == "south_of_60n")
        & (paired["weighting"] == "spherical_cell_area")
        & (paired["comparison"] == "historical_density_minus_random")
    ]
    pairs = {}
    for key, source, expected in SCHEMES:
        rows = selected.loc[selected["validation_scheme"] == source].sort_values(
            ["year", "spatial_fold"]
        )
        if len(rows) != expected or rows.duplicated(["year", "spatial_fold"]).any():
            raise ValueError(f"Unexpected {key} evaluation units")
        pairs[key] = [
            {
                "year": int(row.year),
                "fold": int(row.spatial_fold),
                "random": float(row.random_mae),
                "historical": float(row.comparator_mae),
            }
            for row in rows.itertuples()
        ]

    return {
        "provenance": {
            "pairs": "results/public/osse_ocean_mask_paired.csv (mask m1)",
            "mask_audit": "results/public/osse_ocean_mask_overall.csv; M0 from results/public/osse_latitude_cap_overall.csv",
            "pair_scope": "5,000 samples; spherical area; candidates and evaluation <60N in the connected-ocean mask (M1); 20-seed unit means",
            "no_new_fits": True,
        },
        "pairs": pairs,
        "mask_audit": build_mask_audit(results_dir),
    }


if __name__ == "__main__":
    output = Path("site/data/chart-data.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_chart_data(Path("results/public")), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {output}; existing results only")
