"""Export the open-ocean (M2) network-augmentation run for the website; no fits."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

STUDY = Path("experiments/network_augmentation_2005")
RUN = STUDY / "results_m2_lt60"
OUTPUT = Path("site/data/augmentation.json")


def build() -> dict:
    started = json.loads((RUN / "started.json").read_text(encoding="utf-8"))
    metrics = pd.read_csv(RUN / "metrics.csv")
    effects = pd.read_csv(RUN / "paired_effects.csv")
    design = pd.read_parquet(RUN / "design.parquet")
    additions = pd.read_csv(RUN / "additions.csv")

    scores = [
        {
            "arm": row.arm,
            "seed": int(row.seed),
            "domain": row.domain,
            "rmse": round(float(row.rmse), 3),
            "mae": round(float(row.mae), 3),
        }
        for row in metrics.itertuples()
    ]
    paired = [
        {
            "domain": row.domain,
            "seed": int(row.seed),
            "metric": row.metric,
            "contrast": row.contrast,
            "improvement": round(float(row.improvement), 3),
        }
        for row in effects.itertuples()
    ]
    baseline = (
        design.loc[design.baseline]
        .groupby(["longitude", "latitude"])
        .size()
        .reset_index(name="months")
    )
    gaps = design.loc[design.historical_gap, ["longitude", "latitude"]].drop_duplicates()
    picks = {
        arm: {
            str(seed): group[["longitude", "latitude", "month"]].values.tolist()
            for seed, group in additions.loc[additions.arm == arm].groupby("seed")
        }
        for arm in ("random_addition", "gap_addition")
    }
    inventory = started["inventory"]
    return {
        "metadata": {
            "year": started["config"]["year"],
            "domain": "Open-ocean interior (M2), latitude < 60°N",
            "added_month_cells": started["config"]["added_month_cells"],
            "seeds": started["config"]["acquisition_seeds"],
            "baseline_month_cells": inventory["matched_baseline_month_cells"],
            "evaluation_month_cells": inventory["evaluation_month_cells"],
            "historical_gap_evaluation_cells": inventory["historical_gap_evaluation_cells"],
            "source": str(RUN.as_posix()),
            "no_new_fits": True,
        },
        "scores": scores,
        "paired": paired,
        "map": {
            "baseline": [[float(x), float(y), int(n)] for x, y, n in baseline.values],
            "gap_locations": gaps.values.tolist(),
            "additions": picks,
        },
    }


if __name__ == "__main__":
    OUTPUT.write_text(json.dumps(build(), separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size / 1000:.0f} kB); existing results only")
