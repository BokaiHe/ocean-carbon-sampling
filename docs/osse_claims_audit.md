# OSSE claim audit: absolute baselines and effect distributions

## Truth provenance

The truth field is CMIP6 Earth-system-model output: monthly surface-ocean
`spco2` from IPSL-CM6A-LR historical member `r1i1p1f1`. SST (`tos`) and
salinity (`sos`) from the same model member are predictors. The raw-file
manifest retains filenames, source URLs and SHA-256 hashes. No SOCAT-derived
reconstruction product is used as truth; SOCAT only defines the historical
observing-pattern weights.

## Absolute baselines at sample count 5,000

Values are means across three prespecified years for the month-stratified
hidden-cell test, and equally weighted means across 15 year–fold units for the
whole-spatial-block test.

| Validation | Metric | Random | Coverage | Difference | Mean relative change |
| --- | --- | ---: | ---: | ---: | ---: |
| Hidden cells | RMSE | 25.936 | 24.829 | −1.107 | −4.23% |
| Hidden cells | MAE | 10.936 | 11.436 | +0.500 | +4.56% |
| Hidden cells | Median absolute error | 7.083 | 7.754 | +0.670 | +9.47% |
| Hidden cells | p95 absolute error | 30.696 | 31.785 | +1.090 | +3.55% |
| Hidden cells | p99 absolute error | 66.406 | 61.686 | −4.720 | −7.10% |
| Hidden cells | Mean signed error | +0.065 | +0.071 | +0.006 | not defined |
| Whole blocks | RMSE | 27.549 | 27.728 | +0.179 | +1.24% |
| Whole blocks | MAE | 12.828 | 13.460 | +0.632 | +4.94% |
| Whole blocks | Median absolute error | 8.295 | 8.958 | +0.663 | +8.03% |
| Whole blocks | p95 absolute error | 36.588 | 37.846 | +1.257 | +3.44% |
| Whole blocks | p99 absolute error | 80.367 | 76.777 | −3.590 | −3.47% |
| Whole blocks | Mean signed error | +0.104 | +0.256 | +0.152 | not defined |

For context, the pooled monthly truth field across the three prespecified years
has a standard deviation of 44.9 µatm. The spatial standard deviation of the
three annual-mean fields is 31.0 µatm, and the median local seasonal amplitude
is 58.8 µatm. These are direct properties of the locked truth field, not a
conversion to carbon flux.

The hidden-cell table resolves one mechanism rather than two validation
regimes. Coverage is worse than random at the median, MAE and p95, but better at
p99. Its lower RMSE is therefore a consequence of squared-error sensitivity to
the small number of very large errors; it is not evidence that most predictions
improve. Whole-block validation preserves the same sub-p95 deterioration, while
the p99 benefit becomes directionally unstable.

The signed-bias percentage is intentionally omitted because the random
denominator is close to zero and a percentage would be unstable and
misleading.

The absolute global mean signed errors are below 0.3 µatm for random and
coverage, compared with RMSE values near 25–28 µatm. Their contrast is thus
primarily about the magnitude distribution rather than a global signed offset.
Near-zero global bias does not exclude cancelling regional biases.

## Distribution across 15 year–fold units

Coverage-minus-random differences at sample count 5,000:

| Metric | Median | IQR | Range | Units below zero |
| --- | ---: | ---: | ---: | ---: |
| RMSE | −0.321 | −0.940 to +1.368 | −2.496 to +2.922 | 8/15 |
| MAE | +0.550 | +0.383 to +0.815 | +0.160 to +1.379 | 0/15 |
| Median absolute error | +0.626 | +0.509 to +0.775 | +0.409 to +1.069 | 0/15 |
| p95 absolute error | +1.273 | +0.601 to +1.635 | −0.023 to +3.055 | 1/15 |
| p99 absolute error | −1.002 | −11.106 to +2.207 | −16.788 to +6.294 | 9/15 |
| Mean signed error | +0.320 | −0.429 to +0.557 | −0.657 to +1.017 | 6/15 |

The p99 mean of −3.590 µatm is substantially more negative than its median of
−1.002 µatm, and its IQR crosses zero. It is therefore a heterogeneous mean
shift, not a stable directional effect. In contrast, MAE, median and p95 show
nearly uniform deterioration under coverage.

Historical-pattern-minus-random differences are also retained for all 15
year–fold units. Whole-block RMSE is 27.549 µatm for random and 36.486 µatm for
the historical pattern, a +8.936 µatm deterioration; all 15/15 unit differences
are above zero. This is the strongest result under the present pointwise
objective, but the historical baseline combines spatial clustering with its
observed monthly allocation and is not a pure spatial control.

## Sample-count boundary

The month-stratified hidden-cell comparison uses all four locked sample counts.
At 500 observations, coverage has higher RMSE and p99 error than random in all
three years: extreme-tail suppression has not emerged. At 1,000 the direction
is mixed. Only at 2,500 and 5,000 do all three years favour coverage for p99 and
the tail-sensitive RMSE. Median absolute error remains higher under coverage in
every year at every tested count. The redistribution of error is therefore an
emergent high-count result, not a count-invariant advantage.

## Carbon-flux stakes

Surface-ocean pCO2 enters air–sea CO2 flux through the sea–air pCO2 difference,
but µatm cannot be converted to PgC yr−1 by a universal constant. Flux also
depends on gas-transfer velocity, solubility, atmospheric pCO2, ice treatment
and grid-cell area. A defensible integrated-flux evaluation requires applying a
locked flux operator to each reconstructed field. The present claim remains a
pointwise fCO2-reconstruction claim until that analysis is implemented.
