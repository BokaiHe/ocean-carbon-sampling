# Five-fold spatial sensitivity protocol

## Prespecified crossed design

- Spatial folds: all deterministic checkerboard folds 0–4.
- Sampling seeds: integers 0–19 within every fold.
- Budget: 20% of the fold-specific development pool.
- Pairing: random and coverage strategies share the initial sample, model,
  features, development pool, budget, and held-out observations within each
  fold-seed combination.
- Primary effect: RMSE(random) − RMSE(coverage), in µatm.
- No seed, fold, or observed row is removed after inspecting outcomes.

Each fold is an exhaustive alternative test definition, while seeds are Monte
Carlo replicates nested within that definition. Seed-level effects are therefore
summarized separately within each fold. The 100 fold-seed results are not treated
as 100 independent ocean experiments.

## Reporting

For each fold, report n = 20 seeds, the mean and median paired effect, sample
standard deviation, coverage-win fraction, and two-sided 95% percentile
bootstrap interval for the seed-level mean using 10,000 resamples. Across the
five folds, report the equally weighted mean, standard deviation, minimum and
maximum of the five fold means, the number of positive fold means, and the
number of fold-specific intervals entirely above zero.

No p values or multiplicity corrections are used because all five folds are
prespecified and reported rather than selectively tested.

## Interpretation boundary

This analysis measures sensitivity to the deterministic spatial validation
partition and stochastic sampling choices. It still fixes the block size, time
cutoff, covariates, regression model, and observed SOCAT support. It is the final
regional validation gate before an ESM-based global OSSE, not a substitute for
that OSSE.
