# OSSE claim audit: absolute baselines and effect distributions

## Truth provenance

The truth field is CMIP6 Earth-system-model output: monthly surface-ocean
`spco2` from IPSL-CM6A-LR historical member `r1i1p1f1`. SST (`tos`) and
salinity (`sos`) from the same model member are predictors. The raw-file
manifest retains filenames, source URLs and SHA-256 hashes. No SOCAT-derived
reconstruction product is used as truth; SOCAT only defines the historical
observing-pattern weights.

## Default reporting estimand

Unless a result is explicitly labelled as supporting, reported portfolio
numbers use **whole-spatial-block validation, spherical one-degree cell-area
weighting, and candidate/evaluation pools jointly restricted to latitude
<60°N**. The descriptive consistency units are 15 prespecified year–folds.
The 20 paired seeds are within-unit sampling replicates; grid cells are used for
descriptive spatial decomposition and are not independent Earth-system
replicates.

## Supporting original-domain absolute baselines at sample count 5,000

This section is explicitly **full model domain with equal-cell weighting**, not
the default estimand. Values are means across three prespecified years for the month-stratified
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

On this common scale, the hidden-cell coverage–random RMSE difference of 1.107
µatm is about 2.5% of the month-cell truth standard deviation, whereas the
whole-block historical–random difference of 8.936 µatm is about 20%. Comparing
the random hidden-cell RMSE of 25.936 µatm with 44.9 µatm gives a rough
variance-explained reference of `1 - (25.936 / 44.9)^2 ≈ 0.67`. This is not an
exact pooled R² because the two quantities use different aggregations. It does
show that reconstruction-model limitations remain material, which makes a
cross-model check the highest-priority extension.

The hidden-cell table resolves one mechanism rather than two validation
regimes. Coverage is worse than random at the median, MAE and p95, but better at
p99. Its lower RMSE is therefore a consequence of squared-error sensitivity to
the small number of very large errors; it is not evidence that most predictions
improve. Whole-block validation preserves the same sub-p95 deterioration, while
the p99 benefit becomes directionally unstable.

The signed-bias percentage is intentionally omitted because the random
denominator is close to zero and a percentage would be unstable and
misleading.

For coverage versus random, the absolute global mean signed errors are below
0.3 µatm, compared with RMSE values near 25–28 µatm. That comparison is thus
primarily about the magnitude distribution rather than a global signed offset.
Near-zero global bias does not exclude cancelling regional biases. Historical
sampling is qualitatively different: its bias is −4.822 µatm in hidden cells
and −4.851 µatm in whole blocks, versus +0.065 and +0.104 µatm for random.
These are equal-cell means over the full complete-model domain; the area and
latitude audit below shows that they are not domain-invariant global offsets.

## Supporting factorized historical month-balance audit

This control uses the original full-domain, equal-cell estimand. It is stricter
than merely matching global month shares.
SOCAT counts from 1990–2004 are first summed over month to form a historical
spatial marginal. That same location weight is then used in every month, with
exact quotas of 416 or 417 observations per month at sample count 5,000. This
factorizes the design into `historical spatial marginal × uniform month`,
removing both global month imbalance and the historical space–month interaction.

| Validation | Metric | Random | Factorized historical | Difference | Direction |
| --- | --- | ---: | ---: | ---: | ---: |
| Hidden cells | Bias | +0.065 | −3.798 | −3.863 | 3/3 below zero |
| Hidden cells | RMSE | 25.936 | 34.299 | +8.363 | 3/3 above zero |
| Hidden cells | p99 absolute error | 66.406 | 112.739 | +46.333 | 3/3 above zero |
| Whole blocks | Bias | +0.104 | −3.736 | −3.839 | 15/15 below zero |
| Whole blocks | RMSE | 27.549 | 35.143 | +7.594 | 15/15 above zero |
| Whole blocks | p99 absolute error | 80.367 | 120.579 | +40.212 | 15/15 above zero |

Whole-block month balancing reduces the original historical-minus-random bias
magnitude from 4.954 to 3.839 µatm, leaving 77.5% of it. It retains 85.0% of
the RMSE penalty and 83.9% of the p99 penalty. Space–month coupling therefore
contributes materially, while the spatial marginal reproduces most of the
penalty under this non-default estimand. This shows that seasonality is not the
sole contributor; it does not establish the original signed offset as a
domain-invariant result.

## Supporting mechanism diagnostic

Random sampling does not develop a comparable signed bias when its sample
count is reduced by an order of magnitude. At counts 500, 1,000, 2,500 and
5,000, the pooled random biases are +0.026, +0.351, +0.170 and +0.065 µatm.
At count 500 the three annual means are −0.18, +0.04 and +0.21 µatm. Thus
nominal sample count or ordinary information loss alone does not reproduce the
historical offset under this diagnostic. This does not estimate the effective
sample size of a clustered design.

The 2005 cell-level diagnostic merges local 20-seed historical signed error
with the SOCAT 1990–2004 spatial marginal. The 20,160 zero-density cells have a
mean signed error of −9.42 µatm. Across the 17,760 positive-density cells, the
ten equal-count density-bin means range only from +1.09 to −0.92 µatm and do
not form a strong monotonic curve. At 60–90°N, 86.6% of mapped cells have zero
historical density; their mean error is −47.56 µatm, compared with −6.13 µatm
for positive-density cells. The prominent northern map feature is therefore
dominated by Arctic zero-coverage cells rather than densely sampled North
Atlantic cells.

Grid cells are spatially dependent, so this curve and its nominal correlations
are descriptive rather than inferential. It strengthens the geographic-gap
interpretation but does not identify a causal local density response. The
supported wording is that the penalty is concentrated in structural-zero
regions rather than changing monotonically across positive-density groups.

## Structural-zero contribution decomposition

Across all 40,624 complete spatial cells in the 2005 mapped model domain,
21,580 (53.1%) receive zero SOCAT 1990–2004 spatial-marginal weight. Those
structural zeros represent 49.2% of spherical one-degree cell area. The
historical strategy cannot select them at any nominal sample count unless its
support is changed.

For the 2005 hidden-cell signed-error map, the equal-cell historical mean is
−5.114 µatm. Zero-density cells contribute −5.010 µatm to that mean; covered
cells contribute only −0.104 µatm and have group mean −0.222 µatm. Under exact
spherical latitude-band weights, the total becomes −1.833 µatm: zero-density
cells contribute −1.893 µatm and covered cells +0.060 µatm. Thus the bias is
localized to structural zeros, but its nominal global magnitude is strongly
latitude-weight sensitive.

Cells at 60–90°N contribute −4.540 µatm of the equal-cell total, but −1.395
µatm after spherical weighting because they comprise 10.8% of cells and only
3.8% of spherical cell area in this evaluation sample. South of 60°N, the
corresponding contributions are −0.574 and −0.438 µatm.

## Evaluation-area and latitude-domain audit

All locked models were refit for 20 paired seeds at sample count 5,000 in the
three prespecified years and five whole-block folds. One-degree evaluation
errors were summarized both equally and with exact spherical latitude-band
areas; cells were also reported above and below 60°N. The independent
descriptive units remain three years for hidden cells and 15 year–fold units
for whole blocks.

The four-line whole-block sensitivity table is retained in the main narrative:

| Estimand | Historical − random bias |
| --- | ---: |
| Full model domain, equal-cell weighting | −4.954 |
| Full model domain, spherical area weighting | −1.884 |
| <60°N evaluation only, spherical area weighting | −0.631 |
| **Default:** candidates and evaluation <60°N, spherical area weighting | **−0.473** |

Changing only the evaluation weights leaves training unchanged. A stricter
feasibility proxy therefore rebuilds random, historical and coverage strategies
after restricting both candidate and evaluation pools to latitude <60°N.

| Validation | Comparison | Area-weighted bias difference | Direction | MAE difference | RMSE difference | RMSE worse units |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| Hidden cells, <60°N | Historical − random | −0.835 | 3/3 negative | +2.466 | +4.224 | 3/3 |
| Whole blocks, <60°N | Historical − random | −0.473 | 12/15 negative | +1.855 | +1.310 | 12/15 |
| Hidden cells, <60°N | Coverage − random | −0.002 | 2/3 negative | +0.186 | −1.745 | 0/3 |
| Whole blocks, <60°N | Coverage − random | +0.094 | 11/15 negative | −0.007 | −2.201 | 1/15 |

The default result is the historical error-magnitude penalty,
especially MAE, not a universal −4.85 µatm signed offset. The latter is a
high-northern, equal-cell-domain result. The latitude-cap experiment is not a
sea-ice mask: the current CMIP download and processed truth contain `spco2`,
`tos` and `sos`, but no `siconc`. Complete high-latitude model cells—including
potentially ice-covered cells—enter the original candidate and evaluation
pools. A physically feasible observing-domain result requires an explicit
sea-ice field and a prespecified accessibility rule.

## Supporting original-domain distribution across 15 year–fold units

The following values use full-domain equal-cell weighting.
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
are above zero. The historical-minus-random signed-bias difference is negative
in 3/3 hidden-cell years and 15/15 whole-block units. In hidden cells,
historical p99 absolute error rises
from 66.406 to 127.954 µatm, nearly doubling. This is the largest effect under
the supporting equal-cell full-domain objective. The area/domain audit narrows
the default claim to an error-magnitude penalty and shows that the signed
offset is high-northern and estimand-sensitive.

## Supporting original-domain sample-count boundary

This hidden-cell comparison uses full-domain equal-cell weighting and all four locked sample counts.
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
and grid-cell area. Unlike absolute-error magnitudes, a signed global offset is
not removed by positive–negative cancellation within the evaluated mean and can
propagate directionally into a downstream flux estimate. A defensible numerical
flux effect still requires applying a locked flux operator to each reconstructed
field. The present quantitative claim remains a pointwise pCO2-reconstruction
claim until that analysis is implemented.

Cross-model robustness and a sea-ice-aware accessibility mask are decisive
unresolved tests, not generic optional extensions. Signed bias can depend on a
learner's shrinkage and inductive bias, while the present audit already shows
strong sensitivity to latitude and evaluation weights. A contrasting
OI/kriging-style method may also change the magnitude penalty.
