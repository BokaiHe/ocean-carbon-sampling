"""Verify completed predictions, fixed support and paired effects without refitting."""
from pathlib import Path
import json
import sys
import numpy as np
import pandas as pd
from augmentation import metrics

root = Path(__file__).resolve().parent
out = root / (sys.argv[1] if len(sys.argv) > 1 else "results")
started = json.loads((out / "started.json").read_text())
completed = json.loads((out / "completed.json").read_text())
cfg = started["config"]
design = pd.read_parquet(out / "design.parquet")
added = pd.read_csv(out / "additions.csv")
pred = pd.read_parquet(out / "evaluation_predictions.parquet")
scores = pd.read_csv(out / "metrics.csv")
effects = pd.read_csv(out / "paired_effects.csv")
summary = pd.read_csv(out / "effect_summary.csv")
h = set(design.loc[design.baseline, "cell_id"])
e = set(design.loc[design.evaluation, "cell_id"])
assert h.isdisjoint(e) and e == set(pred.cell_id) and pred.cell_id.is_unique
for (seed, arm), group in added.groupby(["seed", "arm"]):
    ids = set(group.cell_id)
    assert len(ids) == len(group) == cfg["added_month_cells"]
    assert ids.isdisjoint(h | e)
    assert group.groupby("month").size().reindex(range(1,13)).tolist() == [84]*4 + [83]*8
    assert arm != "gap_addition" or group.historical_gap.all()
assert len(scores) == 33 and completed["model_fits"] == 11
for row in scores.itertuples():
    field = "baseline" if row.arm == "baseline" else f"{row.arm}_seed_{row.seed}"
    mask = np.ones(len(pred), bool) if row.domain == "global_unobserved" else (
        pred.historical_gap.to_numpy() if row.domain == "historical_gap" else ~pred.historical_gap.to_numpy())
    check = metrics(pred.loc[mask, "truth"], pred.loc[mask, field], pred.loc[mask, "weight"].to_numpy())
    assert all(np.isclose(check[k], getattr(row,k)) for k in check)
    assert row.n_training == len(h) + (0 if row.arm == "baseline" else cfg["added_month_cells"])
for row in effects.itertuples():
    group = scores.loc[scores.domain.eq(row.domain)]
    b = group.loc[group.arm.eq("baseline"), row.metric].iloc[0]
    r = group.loc[group.arm.eq("random_addition") & group.seed.eq(row.seed), row.metric].iloc[0]
    g = group.loc[group.arm.eq("gap_addition") & group.seed.eq(row.seed), row.metric].iloc[0]
    assert np.isclose(row.improvement, {"baseline_minus_random":b-r,"baseline_minus_gap":b-g,"random_minus_gap":r-g}[row.contrast])
for row in summary.itertuples():
    values = effects.loc[effects.domain.eq(row.domain) & effects.metric.eq(row.metric) & effects.contrast.eq(row.contrast), "improvement"]
    assert len(values) == row.n_seeds == 5
    assert np.isclose(values.mean(), row.mean_improvement)
    assert np.isclose(values.min(), row.min_improvement) and np.isclose(values.max(), row.max_improvement)
    assert int((values > 0).sum()) == row.positive_seeds
print(f"PASS ({out.name}): fixed H, common test set, equal additions, all predictions/metrics and paired summaries.")
