# Single-year OSSE benchmark results

## Design and reporting boundary

The benchmark used the fixed 2005 IPSL-CM6A-LR truth field, one common set of
97,488 evaluation month-cells, four nested observation budgets and 20 sampling
seeds. Each seed produced random, historical-density and spatial-coverage
samples; the same model seed and evaluation cells were used within each paired
comparison.

The independent repeat for sampling variability is the seed (`n = 20`). The
97,488 evaluation cells are repeated measurements within a fixed simulation,
not independent replicates. Percentile bootstrap intervals use 10,000 paired
seed resamples and quantify sampling-randomization variability only. They do not
cover uncertainty across years, Earth system models or the real ocean. No p
values or multiple-testing claims are made across the four-budget learning
curve.

## Reconstruction performance

All three strategies improved as budget increased. Historical-density sampling
had the highest mean RMSE at every budget: 40.36, 37.99, 36.30 and 35.45
micro-atmospheres at budgets 500, 1,000, 2,500 and 5,000, respectively. Its
paired RMSE disadvantage relative to random ranged from 7.58 to 8.96
micro-atmospheres, and every seed-bootstrap interval remained above zero.

Random and spatial coverage showed a budget-dependent tradeoff. At budgets 500
and 1,000 their paired RMSE intervals spanned zero. At 2,500, spatial coverage
had a mean RMSE difference of -1.37 micro-atmospheres relative to random, but
the seed-bootstrap interval still included zero (-2.91 to 0.03). At 5,000, the
mean difference was -1.48 (-2.38 to -0.70), with lower RMSE in 17 of 20 seeds.

## Typical error versus tail error

The 5,000-observation result does not mean spatial coverage is uniformly more
accurate. Relative to random, spatial coverage had:

- RMSE difference: -1.48 micro-atmospheres (-2.38 to -0.70);
- MAE difference: +0.43 (+0.16 to +0.69);
- median absolute-error difference: +0.62 (+0.52 to +0.71);
- 95th-percentile absolute-error difference: +1.07 (+0.36 to +1.72);
- 99th-percentile absolute-error difference: -5.70 (-9.84 to -1.95).

Negative differences favour spatial coverage. Thus, at the largest budget,
spatial coverage reduced the most severe error tail but slightly worsened the
typical grid-cell error. This is a risk-distribution tradeoff, not a universal
ranking.

## Extreme-value sensitivity

After excluding evaluation targets above the 1,000-micro-atmosphere threshold
frozen during input audit, the 5,000-observation coverage-minus-random RMSE
difference was -0.61 micro-atmospheres, with a seed-bootstrap interval from
-2.21 to +0.81. The all-value RMSE advantage is therefore partly dependent on
the small extreme `spco2` tail. The values remain in the primary analysis; this
sensitivity check is not used as a post-hoc exclusion rule.

## Sampling geometry

At budget 5,000, historical density occupied an average of 611 coarse spatial
blocks and 2,128 month-blocks. Random occupied 959 spatial blocks and 4,015
month-blocks, while spatial coverage occupied 1,026 spatial blocks and exactly
5,000 month-blocks. The poorer historical-density reconstruction is consistent
with repeatedly allocating observations to previously favoured regions rather
than increasing environmental and geographic support.

## Defensible conclusion

For this fixed 2005 model world, repeating historical sampling density was
consistently inefficient for global reconstruction. Random allocation performed
well at small budgets and minimized typical absolute error. At the largest
budget, spatial coverage reduced rare large errors and consequently improved
RMSE, while slightly worsening median and mean absolute error. The preferred
strategy therefore depends on whether the observing objective prioritizes
average local accuracy or protection against severe reconstruction failures.

Cross-year and cross-model replication is required before transferring this
conclusion to the real ocean.
