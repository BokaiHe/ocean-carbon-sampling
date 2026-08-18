"""Spatially validated XGBoost diagnostics for strategy error differences."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import GroupKFold

from ocean_carbon_sampling.features import FEATURE_COLUMNS, build_features

ENVIRONMENT_FEATURES = ["sst", "salinity", "year", "month_sin", "month_cos"]
FULL_FEATURES = FEATURE_COLUMNS


def interpretability_gate(
    metrics: pd.DataFrame,
    *,
    target: str,
    minimum_r2: float,
    minimum_spearman: float,
) -> pd.DataFrame:
    """Choose the best validated variant and decide whether SHAP is admissible."""
    candidates = metrics.loc[
        (metrics["target"] == target) & (metrics["cv_fold"].astype(str) == "overall")
    ].sort_values("r2", ascending=False)
    if candidates.empty:
        raise ValueError(f"no overall grouped-CV result for target {target}")
    best = candidates.iloc[0]
    passed = bool(
        best["r2"] > minimum_r2 and best["spearman"] >= minimum_spearman
    )
    reason = (
        "passed spatial generalization thresholds"
        if passed
        else "withheld: insufficient spatially grouped predictive skill"
    )
    return pd.DataFrame(
        {
            "target": [target],
            "selected_model_variant": [best["model_variant"]],
            "overall_oof_r2": [best["r2"]],
            "overall_oof_spearman": [best["spearman"]],
            "minimum_oof_r2": [minimum_r2],
            "minimum_oof_spearman": [minimum_spearman],
            "shap_interpretation_allowed": [passed],
            "decision": [reason],
        }
    )


def diagnostic_features(frame: pd.DataFrame, variant: str) -> pd.DataFrame:
    """Build prospective features; observed fCO2 is intentionally excluded."""
    features = build_features(frame)
    if variant == "environment":
        return features.loc[:, ENVIRONMENT_FEATURES]
    if variant == "full":
        return features.loc[:, FULL_FEATURES]
    raise ValueError(f"unknown diagnostic variant: {variant}")


def make_xgb_diagnostic(seed: int):
    """Return the locked, untuned XGBoost diagnostic regressor."""
    from xgboost import XGBRegressor

    return XGBRegressor(
        objective="reg:squarederror",
        n_estimators=300,
        max_depth=4,
        learning_rate=0.05,
        min_child_weight=5,
        subsample=0.8,
        colsample_bytree=0.8,
        reg_lambda=1.0,
        tree_method="hist",
        random_state=seed,
        n_jobs=4,
    )


def grouped_cross_validation(
    frame: pd.DataFrame,
    *,
    variant: str,
    target_column: str,
    group_column: str,
    n_splits: int,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Evaluate the diagnostic on geographic blocks never used for fitting."""
    x = diagnostic_features(frame, variant)
    y = frame[target_column].to_numpy()
    groups = frame[group_column].to_numpy()
    splitter = GroupKFold(n_splits=n_splits)
    oof_prediction = np.full(len(frame), np.nan)
    metric_rows = []

    for cv_fold, (train_index, test_index) in enumerate(splitter.split(x, y, groups)):
        model = make_xgb_diagnostic(seed + cv_fold)
        model.fit(x.iloc[train_index], y[train_index])
        prediction = model.predict(x.iloc[test_index])
        oof_prediction[test_index] = prediction
        correlation = spearmanr(y[test_index], prediction).statistic
        metric_rows.append(
            {
                "model_variant": variant,
                "cv_fold": cv_fold,
                "n_train": len(train_index),
                "n_test": len(test_index),
                "r2": float(r2_score(y[test_index], prediction)),
                "mae": float(mean_absolute_error(y[test_index], prediction)),
                "spearman": float(correlation),
            }
        )

    if np.isnan(oof_prediction).any():
        raise RuntimeError("grouped cross-validation did not predict every observation")
    overall_correlation = spearmanr(y, oof_prediction).statistic
    metric_rows.append(
        {
            "model_variant": variant,
            "cv_fold": "overall",
            "n_train": len(frame),
            "n_test": len(frame),
            "r2": float(r2_score(y, oof_prediction)),
            "mae": float(mean_absolute_error(y, oof_prediction)),
            "spearman": float(overall_correlation),
        }
    )
    predictions = frame[["observation_id", "spatial_test_fold"]].copy()
    predictions["model_variant"] = variant
    predictions["observed_effect"] = y
    predictions["oof_predicted_effect"] = oof_prediction
    return pd.DataFrame(metric_rows), predictions


def tree_shap_summaries(
    frame: pd.DataFrame,
    *,
    variant: str,
    target_column: str,
    seed: int,
) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray, list[str]]:
    """Fit the descriptive final model and summarize Tree SHAP attributions."""
    import shap

    x = diagnostic_features(frame, variant)
    y = frame[target_column].to_numpy()
    model = make_xgb_diagnostic(seed)
    model.fit(x, y)
    explainer = shap.TreeExplainer(
        model,
        feature_perturbation="tree_path_dependent",
    )
    explanation = explainer(x, check_additivity=True)
    shap_values = np.asarray(explanation.values)

    importance = pd.DataFrame(
        {
            "model_variant": variant,
            "feature": list(x.columns),
            "mean_abs_shap": np.mean(np.abs(shap_values), axis=0),
            "mean_shap": np.mean(shap_values, axis=0),
        }
    ).sort_values("mean_abs_shap", ascending=False)
    importance["rank"] = range(1, len(importance) + 1)

    fold_rows = []
    for fold in sorted(frame["spatial_test_fold"].unique()):
        mask = frame["spatial_test_fold"].to_numpy() == fold
        for feature_index, feature in enumerate(x.columns):
            fold_rows.append(
                {
                    "model_variant": variant,
                    "spatial_test_fold": int(fold),
                    "feature": feature,
                    "mean_shap": float(shap_values[mask, feature_index].mean()),
                    "mean_abs_shap": float(
                        np.abs(shap_values[mask, feature_index]).mean()
                    ),
                    "n_observations": int(mask.sum()),
                }
            )
    return importance, pd.DataFrame(fold_rows), shap_values, list(x.columns)
