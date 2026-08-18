# Minimum experiment: first-run results

## Result

With the shared 10% initial sample, both strategies necessarily produce the
same model and metrics. At the 20% development-pool budget, coverage sampling
has lower locked-test error than random sampling in both validation regimes:

| Validation regime | Random RMSE | Coverage RMSE | Relative RMSE reduction |
|---|---:|---:|---:|
| Temporal holdout, 2020–2024 | 27.94 µatm | 27.84 µatm | 0.39% |
| Spatial block holdout | 30.53 µatm | 28.89 µatm | 5.37% |

Coverage sampling reaches every occupied 10° × 5° development-pool cell at
the 20% budget (273/273 for temporal development and 217/217 for spatial
development), whereas random sampling reaches 270/273 and 214/217. The public
selection table also reports the coefficient of variation of observations per
coverage cell; a lower value indicates more even geographic representation.

## Interpretation

This run supports continuing the project: the spatial-transfer result is large
enough to motivate repeated-seed analysis, while the temporal-transfer gain is
small and should not be presented as robust evidence yet. The experiment shows
association under an archived-observation design, not a globally optimal route
or a causal estimate of the value of future observations.

## Locked limitations

- One preregistered seed; no confidence interval or hypothesis test.
- Evaluation covers observed SOCAT rows, not the full Southern Ocean surface.
- SST and salinity are treated as covariates available at prediction time.
- Only one model and two budgets are used to isolate the sampling comparison.
- Repeated seeds and block-bootstrap intervals belong to the regional benchmark,
  not this minimum feasibility experiment.
