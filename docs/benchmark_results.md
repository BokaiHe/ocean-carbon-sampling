# Repeated-seed benchmark results

## Main result

At a fixed 20% development-pool budget, coverage sampling produced a positive
mean paired RMSE gain in both prespecified transfer regimes:

| Validation regime | Mean RMSE gain | 95% seed-bootstrap interval | Coverage wins |
|---|---:|---:|---:|
| Temporal holdout, 2020–2024 | 0.329 µatm | 0.092 to 0.561 | 16/20 seeds |
| Spatial block holdout | 0.594 µatm | 0.374 to 0.812 | 18/20 seeds |

RMSE gain is defined as RMSE(random) − RMSE(coverage), so positive values favor
coverage sampling. No seed was excluded. Coverage also reduced the coefficient
of variation of observations per geographic coverage cell in 20/20 seeds for
both validation regimes. The mean reductions were 0.973 (temporal development)
and 0.999 (spatial development).

## Figure legend

Each colored point is one complete paired sampling run for a prespecified seed
(n = 20 seeds per validation regime). Black diamonds show the seed-level mean;
error bars show two-sided 95% percentile bootstrap intervals for that mean from
10,000 seed resamples. The dashed horizontal line marks no difference. Panel a
shows locked-test RMSE(random) − RMSE(coverage). Panel b shows the corresponding
reduction in the coefficient of variation of training observations per 10° × 5°
coverage cell. No p values or significance thresholds are used. Source data are
provided in `benchmark_paired_effects.csv` and `benchmark_summary.csv`.

## Interpretation boundary

The result is evidence that the coverage strategy is more reliable than the
single-seed feasibility run suggested, especially for spatial transfer. It is
not yet a claim of global observing-system optimality. The interval quantifies
variation caused by stochastic sampling choices on one fixed observed dataset
and fixed test definitions; it does not cover alternative spatial folds,
measurement error, model choice, or unobserved ocean locations.

## Next scientific gate

Before the global OSSE, the spatial conclusion should be checked across all five
held-out spatial folds. This separates a general coverage benefit from a result
that happens to depend on the currently selected checkerboard fold.
