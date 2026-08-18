# XGBoost and SHAP diagnostic results

## Interpretability decision

SHAP interpretation was withheld because the XGBoost diagnostic models did not
generalize strategy benefit to unseen 20° × 10° spatial blocks.

| Target | Model | Pooled OOF R² | Spearman correlation |
|---|---|---:|---:|
| Mean squared-error gain | Environment | −0.068 | 0.056 |
| Mean squared-error gain | Environment + location | −0.062 | 0.075 |
| Mean absolute-error gain | Environment | −0.020 | 0.066 |
| Mean absolute-error gain | Environment + location | 0.009 | 0.117 |

The prespecified SHAP gate requires pooled spatially grouped OOF R² > 0 and
Spearman correlation ≥ 0.20 for the primary squared-error target. The best
primary-target model fails both practical requirements. Replacing squared error
with the more robust absolute-error difference does not provide useful spatial
generalization either.

## What this means

XGBoost can fit the full diagnostic data and Tree SHAP can numerically decompose
that fitted output, but the resulting feature ranking is not a reliable account
of what will happen in a new spatial block. Latitude, longitude, SST, and salinity
appear prominent in the in-sample decomposition, yet publishing that ranking as
an explanation would confuse fit with validated explanation. Those provisional
artifacts are retained only in the ignored diagnostic work directory.

This result does not show that environmental variables are irrelevant. It shows
that the current observation-level target is noisy, spatially nonstationary, or
missing variables needed to generalize strategy benefit. SHAP explains a model;
it cannot repair a model that lacks out-of-block predictive skill.

## Next diagnostic

The next step should be descriptive and spatial rather than another black-box
model: compare fold-specific covariate distributions, nearest-neighbor distance
from each held-out observation to the selected training set, and mapped paired
error differences. These diagnostics can test whether Fold 4 reflects poor
environmental representativeness, seasonal mismatch, or a few high-loss regions.
