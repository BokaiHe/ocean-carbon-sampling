# XGBoost and SHAP diagnostic protocol

## Scientific question

Which prospective environmental and geographic features are associated with
the observation-level change in held-out prediction error when coverage
sampling replaces random sampling?

The diagnostic target is the mean across 20 sampling seeds of
`squared error(random) − squared error(coverage)` for each observation when its
spatial fold is completely held out. Positive values favor coverage sampling.

## Leakage controls

- Every target value is built only from predictions made while that observation's
  entire 20° × 10° spatial block is excluded from reconstruction-model fitting.
- Seed-level effects are averaged before diagnostic modeling, so one observation
  appears once rather than being treated as 20 independent samples.
- Observed fCO2 and reconstruction predictions are excluded from diagnostic
  features.
- Diagnostic validation uses GroupKFold by 20° × 10° spatial block.

## Models

Two locked, untuned XGBoost regressors are compared:

1. **Environment:** SST, salinity, year, and cyclic month.
2. **Full:** environment features plus latitude and cyclic longitude.

The model uses 300 trees, maximum depth 4, learning rate 0.05, minimum child
weight 5, row and feature subsampling of 0.8, L2 regularization 1, and histogram
tree construction. Performance is reported using spatially grouped out-of-fold
R², MAE, and Spearman correlation. SHAP interpretation is permitted only if the
diagnostic model shows useful spatially grouped predictive performance.

## SHAP boundary

Tree SHAP explains the fitted XGBoost diagnostic output. Mean absolute SHAP
values rank contribution magnitude; fold-specific signed means show which
features push predicted strategy benefit upward or downward. These are
model-dependent associations, not causal effects, physical mechanisms, or proof
that changing a feature would change sampling performance. Correlated features
can share or redistribute attribution.
