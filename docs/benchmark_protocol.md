# Repeated-seed regional benchmark protocol

## Prespecified design

- Sampling seeds: integers 0–19, fixed before running the benchmark.
- Independent Monte Carlo unit: one complete sampling run for one seed.
- Budget: 20% of the regime-specific development pool.
- Pairing: random and coverage strategies share the initial sample, development
  pool, model, features, budget, and locked test observations within each seed.
- Validation regimes: 2020–2024 temporal holdout and pre-2020 held-out spatial
  blocks, reported separately.
- Primary paired effect: RMSE(random) − RMSE(coverage), in µatm.
- Mechanism diagnostic: coverage-cell count CV(random) − CV(coverage).

Positive effects favor coverage sampling. Every seed-level effect is retained;
there is no outlier exclusion or post-hoc seed selection.

## Uncertainty summary

For each regime, the benchmark reports the mean, median, sample standard
deviation, fraction of positive paired effects, and a two-sided 95% percentile
bootstrap interval for the mean using 10,000 resamples of the 20 seed-level
paired effects. The bootstrap seed is fixed at 2026.

No p values are used. The two validation regimes are prespecified and interpreted
separately, so this descriptive benchmark does not apply a multiple-testing
correction.

## Interpretation boundary

The seed-level interval measures sensitivity to stochastic sampling choices
under this algorithm and fixed observed dataset. It does not represent
uncertainty from alternative test blocks, SOCAT measurement error, model choice,
or unobserved Southern Ocean locations. Those require block resampling, model
sensitivity analysis, and ultimately the global OSSE.
