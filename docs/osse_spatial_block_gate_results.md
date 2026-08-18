# Global spatial-block holdout OSSE

## What it tests

The earlier global OSSE hides individual month-grid cells at random within each
month. Training and evaluation locations can therefore be geographically close.
That is a valid interpolation test, but it does not establish performance in a
region with no training observations.

The spatial-block holdout gate asks the stricter question: **if whole ocean
regions are unseen during model fitting, does spatial-coverage sampling still
outperform random sampling under the same observation budget?**

## Locked minimal design

- Truth field: IPSL-CM6A-LR surface-ocean fCO2 for 2005.
- Spatial unit: 20° longitude × 10° latitude block.
- Fold assignment: five exhaustive checkerboard folds; all 12 months from a
  spatial location remain in the same fold.
- Evaluation: one complete fold at a time; the other four folds form the
  candidate pool.
- Strategies: random, historical density, and spatial coverage.
- Budgets: 1,000 and 5,000 observations.
- Replication: five paired sampling seeds per fold.
- Uncertainty: 10,000-resample bootstrap intervals over paired seed effects.
- Model: the same locked reconstruction model and historical weights as the
  main OSSE.
- Buffer: none. This is a coarse unseen-block interpolation/extrapolation gate,
  not a buffered long-range extrapolation test.

The five folds contain 94,032–103,476 evaluation month-grid rows each, covering
all 282 occupied spatial blocks exactly once.

## Main result at budget 5,000

Positive differences mean spatial coverage has larger error than random.

| Held-out fold | RMSE difference (µatm) | 95% seed-bootstrap interval | Reading |
| ---: | ---: | ---: | --- |
| 0 | +4.488 | +2.470 to +6.027 | random better |
| 1 | +2.841 | +1.230 to +4.602 | random better |
| 2 | −0.981 | −2.122 to +0.460 | uncertain |
| 3 | −1.853 | −2.682 to −1.024 | coverage better |
| 4 | +3.551 | +0.998 to +6.661 | random better |

Across the five folds, the mean fold effect is **+1.609 µatm**. Coverage has a
lower mean RMSE in two of five folds, but only fold 3 has an interval entirely
below zero. Three folds have intervals entirely above zero. For p99 absolute
error, the mean fold effect is +2.977 µatm and no fold has an interval entirely
below zero. Median absolute error increases under coverage in all five folds.

Historical-density sampling is consistently worse than random at budget 5,000:
its mean fold RMSE difference is +9.140 µatm and all five fold intervals are
entirely above zero.

## Scientific conclusion

The random hidden-cell result and the spatial-block result answer different
questions. Coverage sampling can reduce RMSE and severe tail error when
predicting scattered missing cells within the sampled geographic domain. That
advantage is **not stable when the target is an entire unseen region**.

This is a useful negative constraint, not a failed experiment. It prevents the
portfolio from making an unsupported universal claim and reveals the next
scientific question: which regional properties determine whether coverage or
random allocation transfers better across space?

## Remaining limits

This is a deliberately minimal gate: one climate model, one year, five seeds,
coarse blocks, and no spatial buffer. A confirmatory experiment should repeat
the locked folds across multiple years and more seeds, then test sensitivity to
block size and an explicit training–evaluation buffer. Until then, the result
supports a boundary on the claim, not a global law about observing strategy.
