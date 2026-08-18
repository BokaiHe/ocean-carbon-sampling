# Native-cell-area weighting sensitivity audit

## Prespecified comparison

The cross-year OSSE originally assigned each native ocean-cell centre to a
one-degree target bin and gave all contributing native cells equal weight. This
audit repeated the complete 2005, 2010 and 2014 experiment after weighting each
contributing value by the exact native cell area stored in the CMIP6 files.

The target-bin assignment, variables, evaluation positions, SOCAT
historical-density window, four budgets, 20 paired sampling seeds and
reconstruction model were unchanged. The audit therefore isolates weighting
within each occupied target bin. It is not a polygon-overlap conservative
remapping audit because each native cell is still assigned by its centre.

The qualitative gate was frozen before the weighted model results were
inspected. At a budget of 5,000, all three years had to preserve four effect
directions: historical-density-minus-random RMSE above zero;
spatial-coverage-minus-random RMSE below zero; spatial-coverage-minus-random
p99 absolute error below zero; and spatial-coverage-minus-random median
absolute error above zero.

## Processed-field differences

All weighted cubes retained exactly 40,624 occupied ocean bins per month. For
`spco2`, the mean absolute difference between weighting methods was 0.0190,
0.0191 and 0.0191 micro-atmospheres in 2005, 2010 and 2014. The corresponding
95th-percentile absolute differences were 0.093, 0.094 and 0.095
micro-atmospheres, and field correlations exceeded 0.99999.

Most target values were unchanged because many occupied one-degree bins contain
one valid native ocean cell. A small number of complex cells changed much more:
the maximum absolute `spco2` differences were 42.7, 53.7 and 45.8
micro-atmospheres. Reporting only the global average would therefore hide a
localized regridding sensitivity.

## Strategy-effect stability

At the 5,000-observation budget, the equal-weight and area-weighted paired
effects were:

| Year | Effect and metric | Equal weight | Area weighted | Weighted minus equal |
|---:|---|---:|---:|---:|
| 2005 | Historical density minus random, RMSE | +8.96 | +8.94 | -0.02 |
| 2010 | Historical density minus random, RMSE | +9.95 | +9.84 | -0.11 |
| 2014 | Historical density minus random, RMSE | +10.69 | +10.63 | -0.06 |
| 2005 | Spatial coverage minus random, RMSE | -1.48 | -1.46 | +0.02 |
| 2010 | Spatial coverage minus random, RMSE | -1.09 | -1.15 | -0.06 |
| 2014 | Spatial coverage minus random, RMSE | -0.75 | -0.69 | +0.06 |
| 2005 | Spatial coverage minus random, p99 error | -5.70 | -5.69 | +0.01 |
| 2010 | Spatial coverage minus random, p99 error | -4.21 | -5.02 | -0.82 |
| 2014 | Spatial coverage minus random, p99 error | -4.25 | -4.26 | -0.01 |
| 2005 | Spatial coverage minus random, median error | +0.62 | +0.64 | +0.02 |
| 2010 | Spatial coverage minus random, median error | +0.78 | +0.75 | -0.03 |
| 2014 | Spatial coverage minus random, median error | +0.62 | +0.59 | -0.02 |

All 12 prespecified direction checks passed. In addition, all 12 corresponding
within-year seed-bootstrap intervals remained entirely on the expected side of
zero. Thus, native-cell-area weighting changed some local field values and
slightly changed effect sizes, but it did not change the cross-year qualitative
conclusion.

## Extreme-value sensitivity

After applying the prespecified threshold of `spco2 <= 1,000`, the weighted
coverage-minus-random RMSE differences at budget 5,000 were -0.59, -0.15 and
-0.41 micro-atmospheres in 2005, 2010 and 2014. Their seed-bootstrap intervals
all spanned zero, matching the earlier conclusion that the all-value RMSE gain
is partly dependent on the extreme tail.

## Defensible conclusion

The central result is robust to replacing equal native-cell weights with exact
native-cell-area weights inside the one-degree bins: spatial coverage trades a
small deterioration in typical grid-cell error for fewer severe reconstruction
failures, while historical-density allocation remains inefficient for global
reconstruction in this model experiment.

This audit removes one important preprocessing concern but does not establish
robustness to polygon-overlap conservative remapping, another Earth system
model, another ensemble member or the real ocean.
