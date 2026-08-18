"""Leakage-aware fixed-budget sampling comparisons on an OSSE truth field."""

from __future__ import annotations

from collections import defaultdict

import numpy as np
import pandas as pd
from sklearn.metrics import r2_score

from ocean_carbon_sampling.experiment import make_model, regression_metrics
from ocean_carbon_sampling.features import build_features


def stratified_evaluation_positions(
    frame: pd.DataFrame,
    *,
    fraction: float,
    seed: int,
    stratum_column: str = "month",
) -> np.ndarray:
    """Select a fixed evaluation subset without inspecting the target."""
    if not 0 < fraction < 1:
        raise ValueError("evaluation fraction must be in (0, 1)")
    rng = np.random.default_rng(seed)
    selected: list[np.ndarray] = []
    strata = frame[stratum_column].to_numpy()
    for stratum in np.unique(strata):
        positions = np.flatnonzero(strata == stratum)
        size = max(1, int(np.floor(len(positions) * fraction)))
        selected.append(rng.choice(positions, size=size, replace=False))
    return np.sort(np.concatenate(selected))


def historical_density_weights(
    candidates: pd.DataFrame,
    socat: pd.DataFrame,
    *,
    year_start: int,
    year_end: int,
    weight_column: str = "fco2_count",
) -> np.ndarray:
    """Map pre-pilot SOCAT observation density to model month-grid cells."""
    historical = socat.loc[
        socat["date"].dt.year.between(year_start, year_end)
    ].copy()
    historical["month"] = historical["date"].dt.month
    density = (
        historical.groupby(["month", "latitude", "longitude"], as_index=False)[
            weight_column
        ]
        .sum()
        .rename(columns={weight_column: "historical_weight"})
    )
    mapped = candidates.loc[:, ["month", "latitude", "longitude"]].merge(
        density,
        on=["month", "latitude", "longitude"],
        how="left",
        sort=False,
    )
    return mapped["historical_weight"].fillna(0.0).to_numpy(dtype=float)


def fixed_budget_orders(
    candidates: pd.DataFrame,
    historical_weights: np.ndarray,
    *,
    maximum_budget: int,
    seed: int,
    longitude_degrees: float = 10.0,
    latitude_degrees: float = 5.0,
) -> dict[str, np.ndarray]:
    """Create nested, target-blind acquisition prefixes for three strategies."""
    n_candidates = len(candidates)
    if maximum_budget <= 0 or maximum_budget > n_candidates:
        raise ValueError("maximum_budget must be within the candidate pool")
    weights = np.asarray(historical_weights, dtype=float)
    if weights.shape != (n_candidates,):
        raise ValueError("historical_weights must align with candidates")
    if np.count_nonzero(weights > 0) < maximum_budget:
        raise ValueError("too few positive historical-density candidates")

    random = np.random.default_rng(seed + 101).choice(
        n_candidates, size=maximum_budget, replace=False
    )
    historical = np.random.default_rng(seed + 202).choice(
        n_candidates,
        size=maximum_budget,
        replace=False,
        p=weights / weights.sum(),
    )
    coverage = _coverage_order(
        candidates,
        maximum_budget,
        seed=seed + 303,
        longitude_degrees=longitude_degrees,
        latitude_degrees=latitude_degrees,
    )
    return {
        "random": random,
        "historical_density": historical,
        "spatial_coverage": coverage,
    }


def run_osse_gate(
    frame: pd.DataFrame,
    historical_weights: np.ndarray,
    evaluation_positions: np.ndarray,
    *,
    budgets: tuple[int, ...],
    seeds: tuple[int, ...],
    longitude_degrees: float = 10.0,
    latitude_degrees: float = 5.0,
    extreme_value_threshold: float | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit one locked model and use one common evaluation set for all strategies."""
    if not budgets or min(budgets) <= 0:
        raise ValueError("budgets must contain positive integers")
    evaluation_mask = np.zeros(len(frame), dtype=bool)
    evaluation_mask[np.asarray(evaluation_positions, dtype=int)] = True
    candidates = frame.loc[~evaluation_mask].reset_index(drop=True)
    evaluation = frame.loc[evaluation_mask].reset_index(drop=True)
    candidate_weights = np.asarray(historical_weights)[~evaluation_mask]
    if candidates.empty or evaluation.empty:
        raise ValueError("candidate and evaluation pools must both be non-empty")

    x_candidates = build_features(candidates)
    x_evaluation = build_features(evaluation)
    y_candidates = candidates["spco2"].to_numpy()
    y_evaluation = evaluation["spco2"].to_numpy()
    metric_rows: list[dict[str, object]] = []
    selection_rows: list[dict[str, object]] = []

    for seed in seeds:
        orders = fixed_budget_orders(
            candidates,
            candidate_weights,
            maximum_budget=max(budgets),
            seed=seed,
            longitude_degrees=longitude_degrees,
            latitude_degrees=latitude_degrees,
        )
        for strategy, order in orders.items():
            for budget in sorted(budgets):
                selected = order[:budget]
                model = make_model(seed + 10_000)
                model.fit(x_candidates.iloc[selected], y_candidates[selected])
                prediction = model.predict(x_evaluation)
                domains = {"all": np.ones(len(evaluation), dtype=bool)}
                if extreme_value_threshold is not None:
                    domains["spco2_le_threshold"] = (
                        y_evaluation <= extreme_value_threshold
                    )
                for domain, domain_mask in domains.items():
                    observed = y_evaluation[domain_mask]
                    predicted = prediction[domain_mask]
                    scores = regression_metrics(observed, predicted)
                    correlation = float(np.corrcoef(observed, predicted)[0, 1])
                    metric_rows.append(
                        {
                            "evaluation_domain": domain,
                            "strategy": strategy,
                            "budget": budget,
                            "seed": seed,
                            "n_candidates": len(candidates),
                            "n_evaluation": len(evaluation),
                            "n_evaluation_domain": len(observed),
                            **scores,
                            "r2": float(r2_score(observed, predicted)),
                            "correlation": correlation,
                        }
                    )
                selection_rows.append(
                    _selection_summary(
                        candidates.iloc[selected],
                        candidate_weights[selected],
                        strategy=strategy,
                        budget=budget,
                        seed=seed,
                        longitude_degrees=longitude_degrees,
                        latitude_degrees=latitude_degrees,
                    )
                )
    return pd.DataFrame(metric_rows), pd.DataFrame(selection_rows)


def _coverage_order(
    candidates: pd.DataFrame,
    size: int,
    *,
    seed: int,
    longitude_degrees: float,
    latitude_degrees: float,
) -> np.ndarray:
    month = candidates["month"].to_numpy(dtype=int)
    lon_block = np.floor(
        (candidates["longitude"].to_numpy() + 180.0) / longitude_degrees
    ).astype(int)
    lat_block = np.floor(
        (candidates["latitude"].to_numpy() + 90.0) / latitude_degrees
    ).astype(int)
    groups: dict[tuple[int, int, int], list[int]] = defaultdict(list)
    for position, key in enumerate(zip(month, lat_block, lon_block, strict=True)):
        groups[key].append(position)

    rng = np.random.default_rng(seed)
    group_keys = list(groups)
    rng.shuffle(group_keys)
    for key in group_keys:
        rng.shuffle(groups[key])

    order: list[int] = []
    offset = 0
    active = group_keys
    while active and len(order) < size:
        rng.shuffle(active)
        next_active: list[tuple[int, int, int]] = []
        for key in active:
            positions = groups[key]
            if offset < len(positions):
                order.append(positions[offset])
                if len(order) == size:
                    break
            if offset + 1 < len(positions):
                next_active.append(key)
        active = next_active
        offset += 1
    if len(order) != size:
        raise RuntimeError("coverage order did not reach the requested budget")
    return np.asarray(order, dtype=int)


def _selection_summary(
    selected: pd.DataFrame,
    historical_weights: np.ndarray,
    *,
    strategy: str,
    budget: int,
    seed: int,
    longitude_degrees: float,
    latitude_degrees: float,
) -> dict[str, object]:
    lon_block = np.floor(
        (selected["longitude"].to_numpy() + 180.0) / longitude_degrees
    ).astype(int)
    lat_block = np.floor(
        (selected["latitude"].to_numpy() + 90.0) / latitude_degrees
    ).astype(int)
    month = selected["month"].to_numpy(dtype=int)
    spatial = np.column_stack([lat_block, lon_block])
    spatiotemporal = np.column_stack([month, lat_block, lon_block])
    return {
        "strategy": strategy,
        "budget": budget,
        "seed": seed,
        "occupied_spatial_blocks": int(np.unique(spatial, axis=0).shape[0]),
        "occupied_month_blocks": int(np.unique(spatiotemporal, axis=0).shape[0]),
        "months_covered": int(np.unique(month).size),
        "fraction_with_historical_weight": float(np.mean(historical_weights > 0)),
        "mean_historical_weight": float(np.mean(historical_weights)),
    }
