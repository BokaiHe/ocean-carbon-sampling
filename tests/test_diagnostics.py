import pandas as pd

from ocean_carbon_sampling.diagnostics import diagnostic_features, interpretability_gate


def test_diagnostic_features_exclude_observed_target() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2010-01-15", "2011-06-15"]),
            "latitude": [-50.0, -60.0],
            "longitude": [10.0, 20.0],
            "sst": [2.0, 3.0],
            "salinity": [34.0, 35.0],
            "fco2": [350.0, 700.0],
            "mean_squared_error_gain": [10.0, -5.0],
        }
    )

    environment = diagnostic_features(frame, "environment")
    full = diagnostic_features(frame, "full")

    assert "fco2" not in environment
    assert "fco2" not in full
    assert "mean_squared_error_gain" not in environment
    assert "latitude" not in environment
    assert "latitude" in full


def test_shap_gate_requires_spatial_predictive_skill() -> None:
    metrics = pd.DataFrame(
        {
            "target": ["gain", "gain"],
            "model_variant": ["environment", "full"],
            "cv_fold": ["overall", "overall"],
            "r2": [-0.1, 0.05],
            "spearman": [0.3, 0.1],
        }
    )
    gate = interpretability_gate(
        metrics, target="gain", minimum_r2=0.0, minimum_spearman=0.2
    ).iloc[0]

    assert gate["selected_model_variant"] == "full"
    assert not gate["shap_interpretation_allowed"]
