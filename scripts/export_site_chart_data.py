"""Export small web-chart inputs from frozen results only; never fit models."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def build_chart_data(results_dir: Path) -> dict:
    paired = pd.read_csv(results_dir / "osse_latitude_cap_paired.csv")
    selected = paired.loc[
        (paired["budget"] == 5000)
        & (paired["domain"] == "south_of_60n")
        & (paired["weighting"] == "spherical_cell_area")
        & (paired["comparison"] == "historical_density_minus_random")
    ]
    pairs = {}
    for key, source, expected in (
        ("hidden", "hidden_cells_latitude_cap", 3),
        ("block", "whole_blocks_latitude_cap", 15),
    ):
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

    sampling = pd.read_parquet(results_dir / "osse_visual_demo_sampling.parquet")
    metadata = pd.read_csv(results_dir / "osse_visual_demo_metadata.csv").iloc[0]
    blocks = []
    for key, source in (
        ("random", "random"),
        ("historical", "historical_density"),
        ("coverage", "spatial_coverage"),
    ):
        rows = sampling.loc[sampling["strategy"] == source]
        if rows.duplicated(["latitude", "longitude"]).any():
            raise ValueError("Sampling summary has duplicate spatial blocks")
        count = int(rows["observations"].sum())
        if count != int(metadata["budget"]):
            raise ValueError("Sampling map and metadata counts disagree")
        blocks.append(
            {
                "strategy": key,
                "blocks": int((rows["observations"] > 0).sum()),
                "sample_count": count,
            }
        )

    return {
        "provenance": {
            "pairs": "results/public/osse_latitude_cap_paired.csv",
            "sampling": "results/public/osse_visual_demo_sampling.parquet",
            "sampling_metadata": "results/public/osse_visual_demo_metadata.csv",
            "pair_scope": "5,000 samples; spherical area; candidates and evaluation <60N; 20-seed unit means",
            "no_new_fits": True,
        },
        "pairs": pairs,
        "sampling": {
            "year": int(metadata["year"]),
            "seed": int(metadata["seed"]),
            "longitude_degrees": float(metadata["sampling_longitude_degrees"]),
            "latitude_degrees": float(metadata["sampling_latitude_degrees"]),
            "scope": "Original full-domain hidden-cell illustrative selection; not the primary aligned-domain runs",
            "blocks": blocks,
        },
        "error_map_availability": {
            "source": "results/public/osse_visual_demo_fields.parquet",
            "available": "2005 full-domain per-cell mean absolute errors for random and historical-density, averaged across 20 seeds and available hidden months",
            "primary_domain_map_available": False,
            "boundary": "Clipping the saved full-domain map cannot reproduce candidate-domain alignment. Current latitude-cap caches contain aggregate scores, not per-cell predictions.",
        },
    }


if __name__ == "__main__":
    output = Path("site/data/chart-data.json")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(build_chart_data(Path("results/public")), indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {output}; existing results only")
