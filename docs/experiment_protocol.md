# Minimum experiment protocol

## Question

Under a fixed observation budget, does spatial-coverage sampling improve out-of-sample Southern Ocean fCO2 prediction relative to random sampling?

## Scope

- Dataset: SOCAT v2025 monthly 1-degree gridded product.
- Region: latitude south of 35 degrees S.
- Period: 1990–2024, subject to a post-download coverage audit.
- Target: weighted mean fCO2.
- Strategies: random and spatial coverage.
- Model: one lightweight tree-based regression baseline.

## Locked validation

Two test regimes will be reported separately:

1. Temporal holdout: recent years are never used for model fitting or sample acquisition.
2. Spatial holdout: geographic blocks are never used for model fitting or sample acquisition.

The candidate pool and the locked test sets must be created before sampling begins. Test labels must not influence feature engineering, hyperparameter tuning, acquisition, or stopping decisions.

## Primary and secondary outcomes

- Primary minimum-experiment metric: test RMSE.
- Secondary metrics: MAE and mean bias.
- The full regional benchmark will add CRPS, prediction-interval coverage, interval width, repeated seeds, and block-bootstrap confidence intervals.

## Completion gate

The minimum experiment passes when:

- it runs from a clean environment;
- the same seed produces the same selections and metrics;
- random and coverage strategies use identical initial sets, candidate pools, tests, and budgets;
- temporal and spatial test results are saved separately;
- one run finishes on a normal laptop within a few minutes;
- no test-set information is used during acquisition.

## Interpretation boundary

This is an offline observation-value experiment using archived SOCAT observations. It does not by itself identify globally optimal future ship or autonomous-platform routes. Global unsampled locations will be studied later with an ESM-based OSSE, where a complete model truth is available.

