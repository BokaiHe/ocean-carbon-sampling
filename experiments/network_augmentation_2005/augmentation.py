"""Target-blind additions to an unchanged observed network; independent study module."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
import time

os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")
sys.dont_write_bytecode = True

import numpy as np
import pandas as pd


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def dump(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def network_masks(frame, socat, year, historical_start, historical_end):
    """Map exact observation support without inspecting numerical truth values."""
    valid = socat.loc[(socat.fco2_count > 0) & np.isfinite(socat.fco2)].copy()
    valid["month"] = valid.date.dt.month
    keys = ["month", "latitude", "longitude"]
    base = valid.loc[valid.date.dt.year.eq(year), keys].drop_duplicates()
    history = valid.loc[valid.date.dt.year.between(historical_start, historical_end),
                        ["latitude", "longitude"]].drop_duplicates()
    index = pd.MultiIndex.from_frame(frame[keys])
    base_index = pd.MultiIndex.from_frame(base)
    spatial = pd.MultiIndex.from_frame(frame[["latitude", "longitude"]])
    h = np.asarray(index.isin(base_index))
    gap = ~np.asarray(spatial.isin(pd.MultiIndex.from_frame(history)))
    if frame.duplicated(keys).any():
        raise ValueError("Duplicate model month-cells")
    if not h.any() or not gap.any() or np.any(h & gap):
        raise ValueError("Invalid baseline/gap masks")
    return h, gap, {"socat_2005_valid_month_cells": len(base),
                    "matched_baseline_month_cells": int(h.sum()),
                    "unmatched_socat_month_cells": int((~base_index.isin(index)).sum()),
                    "history_unique_locations": len(history)}


def reserve_evaluation(month, baseline, gap, fraction, seed):
    rng = np.random.default_rng(seed)
    evaluation = np.zeros(len(month), dtype=bool)
    inverse_probability = np.zeros(len(month), dtype=float)
    for m in sorted(np.unique(month)):
        for g in [False, True]:
            candidates = np.flatnonzero((month == m) & ~baseline & (gap == g))
            if len(candidates) < 2:
                raise ValueError("Insufficient evaluation-stratum population")
            n = max(1, int(np.floor(fraction * len(candidates))))
            chosen = rng.choice(candidates, n, replace=False)
            evaluation[chosen] = True
            inverse_probability[chosen] = len(candidates) / n
    return evaluation, inverse_probability


def select_additions(month, baseline, evaluation, gap, count, seed, target_gap):
    """Use equal month quotas; no responses/features/predictions are accepted."""
    rng = np.random.default_rng(seed)
    months = sorted(np.unique(month))
    if len(months) != 12:
        raise ValueError("All twelve months are required")
    per_month, extra = divmod(count, 12)
    eligible = ~baseline & ~evaluation
    if target_gap:
        eligible &= gap
    selected = []
    for i, m in enumerate(months):
        pool = np.flatnonzero(eligible & (month == m))
        n = per_month + int(i < extra)
        if len(pool) < n:
            raise ValueError(f"Insufficient eligible cells for month {m}")
        selected.extend(rng.choice(pool, n, replace=False))
    return np.sort(np.asarray(selected, dtype=int))


def metrics(y, prediction, weights):
    residual = np.asarray(prediction) - np.asarray(y)
    if not (np.isfinite(residual).all() and np.isfinite(weights).all() and (weights > 0).all()):
        raise ValueError("Invalid metric inputs")
    return {"rmse": float(np.sqrt(np.average(residual**2, weights=weights))),
            "mae": float(np.average(abs(residual), weights=weights)),
            "bias": float(np.average(residual, weights=weights))}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--config", default="config.json", help="study config, relative to this directory")
    parser.add_argument("--results", default="results", help="output directory, relative to this directory")
    args = parser.parse_args()
    study = Path(__file__).resolve().parent
    project = args.project_root.resolve()
    out = study / args.results
    if (out / "started.json").exists():
        raise RuntimeError("Existing run detected; preserve it and create a separate study for any new run")
    cfg = json.loads((study / args.config).read_text())
    sys.path.insert(0, str(project / "src"))
    import xarray as xr
    from threadpoolctl import threadpool_limits
    from ocean_carbon_sampling.data import read_socat_monthly
    from ocean_carbon_sampling.features import build_features
    from ocean_carbon_sampling.experiment import make_model
    from ocean_carbon_sampling.osse_experiment import spherical_cell_area_weights

    inputs = {cfg["truth_file"]: sha(project / cfg["truth_file"]),
              cfg["socat_file"]: sha(project / cfg["socat_file"])}
    for name in ["data.py", "features.py", "experiment.py", "sampling.py", "osse_experiment.py"]:
        relative = "src/ocean_carbon_sampling/" + name
        inputs[relative] = sha(project / relative)
    with xr.open_dataset(project / cfg["truth_file"], engine="h5netcdf") as ds:
        frame = ds[["spco2", "tos", "sos"]].to_dataframe().dropna().reset_index().rename(
            columns={"time": "date", "tos": "sst", "sos": "salinity"})
    frame = frame.loc[np.isfinite(frame[["spco2", "sst", "salinity"]]).all(axis=1)].reset_index(drop=True)
    if cfg.get("latitude_max") is not None:
        frame = frame.loc[frame.latitude < cfg["latitude_max"]].reset_index(drop=True)
    if cfg.get("domain_mask_file"):
        mask = pd.read_csv(project / cfg["domain_mask_file"])
        mask = mask.loc[mask[cfg["domain_mask_column"]], ["latitude", "longitude"]]
        frame = frame.merge(mask, on=["latitude", "longitude"], how="inner", sort=False)
        frame = frame.sort_values(["date", "latitude", "longitude"]).reset_index(drop=True)
    frame["month"] = frame.date.dt.month
    if set(frame.date.dt.year) != {cfg["year"]}:
        raise ValueError("Unexpected year")
    frame["cell_id"] = np.arange(len(frame))
    socat = read_socat_monthly(project / cfg["socat_file"])
    h, gap, inventory = network_masks(frame, socat, cfg["year"], cfg["historical_start_year"], cfg["historical_end_year"])
    month = frame.month.to_numpy()
    evaluation, inverse = reserve_evaluation(month, h, gap, cfg["evaluation_fraction"], cfg["evaluation_seed"])
    hids = np.flatnonzero(h)
    eids = np.flatnonzero(evaluation)
    acquisition = []
    choices = {}
    for seed in cfg["acquisition_seeds"]:
        for arm, targeted in [("random_addition", False), ("gap_addition", True)]:
            added = select_additions(month, h, evaluation, gap, cfg["added_month_cells"], seed + 7000, targeted)
            training = np.concatenate([hids, added])
            assert len(np.unique(training)) == len(hids) + cfg["added_month_cells"]
            assert not evaluation[training].any() and np.isin(hids, training).all()
            assert not targeted or gap[added].all()
            choices[(seed, arm)] = added
            part = frame.iloc[added][["cell_id", "month", "latitude", "longitude"]].copy()
            part["seed"], part["arm"], part["historical_gap"] = seed, arm, gap[added]
            acquisition.append(part)
        a, b = [choices[(seed, arm)] for arm in ["random_addition", "gap_addition"]]
        assert np.array_equal(np.bincount(month[a], minlength=13), np.bincount(month[b], minlength=13))
    out.mkdir(parents=True, exist_ok=True)
    geometry = frame[["cell_id", "month", "latitude", "longitude"]].copy()
    geometry["baseline"], geometry["historical_gap"], geometry["evaluation"] = h, gap, evaluation
    geometry.to_parquet(out / "design.parquet", index=False)
    pd.concat(acquisition).to_csv(out / "additions.csv", index=False)
    inventory.update({"complete_model_month_cells": len(frame), "evaluation_month_cells": len(eids),
                      "historical_gap_evaluation_cells": int(gap[eids].sum()),
                      "candidate_addition_month_cells": int((~h & ~evaluation).sum()),
                      "baseline_count_by_month": {str(m): int(((month == m) & h).sum()) for m in range(1, 13)},
                      "latitude_min": float(frame.latitude.min()), "latitude_max": float(frame.latitude.max())})
    import platform, sklearn
    started = {"started_utc": pd.Timestamp.now(tz="UTC").isoformat(), "config": cfg,
               "source_inputs_sha256": inputs, "inventory": inventory,
               "study_inputs_sha256": {p: sha(study / p) for p in [args.config, "PROTOCOL.md", "augmentation.py", "test_augmentation.py"]},
               "design_sha256": sha(out / "design.parquet"), "additions_sha256": sha(out / "additions.csv"),
               "versions": {"python": platform.python_version(), "numpy": np.__version__, "pandas": pd.__version__, "sklearn": sklearn.__version__}}
    dump(out / "started.json", started)
    print("Design locked before model fitting:", json.dumps(inventory), flush=True)
    x = build_features(frame)
    y = frame.spco2.to_numpy()
    ev = frame.iloc[eids][["cell_id", "month", "latitude", "longitude", "spco2"]].copy().rename(columns={"spco2": "truth"})
    ev["historical_gap"] = gap[eids]
    ev["weight"] = spherical_cell_area_weights(ev.latitude) * inverse[eids]
    domains = {"global_unobserved": np.ones(len(ev), bool), "historical_gap": gap[eids],
               "previously_observed_locations": ~gap[eids]}
    rows = []

    def fit_and_record(arm, seed, train):
        begin = time.monotonic()
        model = make_model(cfg["model_seed"]).set_params(**cfg["model_settings"])
        with threadpool_limits(limits=cfg["threads"]):
            model.fit(x.iloc[train], y[train])
            prediction = model.predict(x.iloc[eids])
        key = "baseline" if arm == "baseline" else f"{arm}_seed_{seed}"
        ev[key] = prediction
        for domain, mask in domains.items():
            rows.append({"arm": arm, "seed": seed, "domain": domain, "n_training": len(train),
                         "n_evaluation": int(mask.sum()), **metrics(y[eids][mask], prediction[mask], ev.weight.to_numpy()[mask])})
        pd.DataFrame(rows).to_csv(out / "metrics.csv", index=False)
        ev.to_parquet(out / "evaluation_predictions.parquet", index=False)
        print(f"Completed {key}: train={len(train)}, seconds={time.monotonic()-begin:.1f}", flush=True)

    fit_and_record("baseline", -1, hids)
    for seed in cfg["acquisition_seeds"]:
        for arm in ["random_addition", "gap_addition"]:
            fit_and_record(arm, seed, np.concatenate([hids, choices[(seed, arm)]]))
    scores = pd.DataFrame(rows)
    effects = []
    for domain in domains:
        base = scores.loc[(scores.arm == "baseline") & (scores.domain == domain)].iloc[0]
        for seed in cfg["acquisition_seeds"]:
            sub = scores.loc[(scores.seed == seed) & (scores.domain == domain)].set_index("arm")
            for metric in ["rmse", "mae"]:
                for contrast, delta in [
                    ("baseline_minus_random", base[metric] - sub.loc["random_addition", metric]),
                    ("baseline_minus_gap", base[metric] - sub.loc["gap_addition", metric]),
                    ("random_minus_gap", sub.loc["random_addition", metric] - sub.loc["gap_addition", metric])]:
                    effects.append({"domain": domain, "seed": seed, "metric": metric, "contrast": contrast, "improvement": float(delta)})
    effects = pd.DataFrame(effects)
    effects.to_csv(out / "paired_effects.csv", index=False)
    effects.groupby(["domain", "metric", "contrast"], as_index=False).agg(
        mean_improvement=("improvement", "mean"), min_improvement=("improvement", "min"),
        max_improvement=("improvement", "max"), n_seeds=("seed", "nunique"),
        positive_seeds=("improvement", lambda v: int((v > 0).sum()))).to_csv(out / "effect_summary.csv", index=False)
    assert all(sha(project / p) == digest for p, digest in inputs.items())
    assert sha(out / "design.parquet") == started["design_sha256"]
    assert sha(out / "additions.csv") == started["additions_sha256"]
    dump(out / "completed.json", {"completed_utc": pd.Timestamp.now(tz="UTC").isoformat(),
         "model_fits": 11, "all_baseline_points_preserved": True, "evaluation_never_acquired": True,
         "equal_added_month_quotas": True, "source_inputs_unchanged": True,
         "started_sha256": sha(out / "started.json"),
         "outputs_sha256": {p.name: sha(p) for p in sorted(out.iterdir()) if p.is_file()}})
    print(effects.groupby(["domain", "metric", "contrast"]).improvement.mean().to_string(), flush=True)


if __name__ == "__main__":
    main()
