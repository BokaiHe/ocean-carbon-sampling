# Global spatial-block holdout OSSE

## What it tests

The earlier global OSSE hides individual month-grid cells at random within each
month. Training and evaluation locations can therefore be geographically close.
That is a valid interpolation test, but it does not establish performance in a
region with no training observations.

The spatial-block holdout asks the stricter question: **if whole ocean regions
are unseen during model fitting, does spatial-coverage sampling still
outperform random sampling under the same observation budget?**

## Locked confirmatory design

- Truth field: IPSL-CM6A-LR surface-ocean fCO2 in the prespecified years 2005,
  2010 and 2014.
- Spatial unit: 20° longitude × 10° latitude block.
- Fold assignment: five exhaustive checkerboard folds; all 12 months from a
  spatial location remain in the same fold.
- Evaluation: one complete fold at a time; the other four folds form the
  candidate pool.
- Strategies: random, historical density, and spatial coverage.
- Budgets: 1,000 and 5,000 observations.
- Replication: 20 paired sampling seeds per year–fold.
- Uncertainty: 10,000-resample bootstrap intervals over paired seed effects
  within each year–fold.
- Model: the same locked reconstruction model and historical weights as the
  main OSSE.
- Buffer: none. This tests transfer into coarse unseen blocks, not buffered
  long-range extrapolation.

The design contains 15 year–fold evaluation units and 1,800 strategy fits. The
five folds cover every occupied block once in each year.

## Main result at budget 5,000

Differences are spatial coverage minus random, so negative values favour
coverage.

| Metric | Mean across 15 year–fold units (µatm) | Units favouring coverage | Intervals entirely below zero | Interpretation |
| --- | ---: | ---: | ---: | --- |
| RMSE | +0.179 | 8/15 | 6/15 | direction depends on year and region |
| p99 absolute error | −3.590 | 9/15 | 6/15 | severe failures are reduced more often |
| Median absolute error | +0.663 | 0/15 | 0/15 | typical error is consistently higher |

RMSE is close to neutral on average but strongly heterogeneous. The mean fold
effect is +0.321 µatm in 2005, +0.462 µatm in 2010 and −0.247 µatm in 2014.
Across all year–fold units, eight effects are negative and seven are positive;
six intervals are entirely below zero and five are entirely above zero.

The p99 effect is negative on average in every year: −3.155 µatm in 2005,
−3.733 µatm in 2010 and −3.883 µatm in 2014. This tail benefit is still not
universal: six of the 15 year–fold mean effects are positive.

Historical-density sampling is consistently worse than random on RMSE at
budget 5,000. Its mean year–fold effect is +8.936 µatm, and all 15 intervals are
entirely above zero.

## Scientific conclusion

The random hidden-cell and whole-block experiments answer different questions.
Coverage sampling improves reconstruction of scattered missing cells inside the
sampled geographic domain. When complete regions are unseen, its RMSE effect is
approximately balanced between gains and losses. The more stable pattern is a
tradeoff: coverage raises typical error everywhere but reduces severe tail
error more often.

The defensible claim is therefore not that coverage is universally superior.
It is that **sampling geometry redistributes reconstruction risk**, and the
choice of objective—typical accuracy, aggregate RMSE, or protection against
extreme failures—changes which strategy is preferable.

## Statistical boundary and remaining limits

The 20 seeds are paired replicates within each year–fold. The 15 year–fold means
are a descriptive consistency check, not 15 fully independent ecological
replicates, and grid cells are never used as the inferential sample size.

The experiment still uses one climate model, three years, coarse blocks, and no
spatial buffer. A later sensitivity study could vary block size and add an
explicit training–evaluation buffer. Those extensions are useful, but no longer
required to establish the present project's central fixed-model conclusion.
