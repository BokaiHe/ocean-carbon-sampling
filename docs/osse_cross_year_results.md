# Three-year OSSE robustness results

## Prespecified design

The temporal robustness phase used 2005, 2010 and 2014, selected before model
fitting as the start, midpoint and endpoint of the locked 2005-2014 analysis
window. Each year used the same Earth system model, variables, one-degree
processing, 20% month-stratified evaluation fraction, observation budgets,
sampling seeds, reconstruction model and SOCAT 1990-2004 historical-density
weights.

For each year, 20 sampling seeds were paired across random,
historical-density and spatial-coverage allocation at budgets of 500, 1,000,
2,500 and 5,000. The experiment produced 720 model fits and 1,440 metric rows
across the primary and threshold-sensitivity evaluation domains.

The sampling seed is the independent repeat within a fixed model year.
Ten-thousand-resample percentile bootstrap intervals describe sampling
randomization within that year. The three selected years are a descriptive
robustness panel, not a sufficient sample for population-level temporal
inference; no across-year confidence interval or p value is reported.

## Historical-density sampling

Historical-density sampling had higher global RMSE than random sampling at
every budget in all three years. At a budget of 5,000, its paired RMSE
disadvantage was 8.96 micro-atmospheres in 2005, 9.95 in 2010 and 10.69 in
2014. All three seed-bootstrap intervals were entirely above zero.

This repeated result shows that allocating new observations in proportion to
past sampling density is inefficient in this controlled model world. It does
not imply that historically sampled regions have no scientific value; it
isolates the cost of using historical density as the allocation rule for a
fixed global reconstruction budget.

## Coverage versus random sampling

The budget-dependent tradeoff observed in 2005 repeated across years. At a
budget of 5,000, the spatial-coverage-minus-random differences were:

| Year | RMSE difference | Seed-bootstrap interval | Median absolute-error difference | p99 absolute-error difference |
|---:|---:|---:|---:|---:|
| 2005 | -1.48 | -2.38 to -0.70 | +0.62 | -5.70 |
| 2010 | -1.09 | -1.70 to -0.51 | +0.78 | -4.21 |
| 2014 | -0.75 | -1.21 to -0.31 | +0.62 | -4.25 |

Negative differences favour spatial coverage. Thus, spatial coverage reduced
RMSE and the severe p99 error tail in all three years, while increasing median
absolute error in all three years. Every within-year seed-bootstrap interval
was entirely below zero for RMSE and p99 error and entirely above zero for
median absolute error at the 5,000-observation budget.

The scientific conclusion is therefore not a universal strategy ranking.
Random sampling better protected typical grid-cell accuracy, whereas spatial
coverage better protected against rare, severe reconstruction failures.

## Extreme-value sensitivity

After excluding evaluation targets above the prespecified 1,000
micro-atmosphere threshold, the 5,000-observation coverage-minus-random RMSE
differences were -0.61, -0.06 and -0.45 micro-atmospheres for 2005, 2010 and
2014. All three seed-bootstrap intervals spanned zero. In contrast, the p99
absolute-error reductions remained directionally consistent and their three
intervals remained entirely below zero.

The global RMSE advantage is therefore sensitive to the small extreme `spco2`
tail, while the reduction in high-but-not-maximum reconstruction errors is more
stable. The extreme values remain in the primary analysis because the
threshold was defined as a sensitivity analysis, not an exclusion rule.

## Interpretation boundary

These results establish temporal repetition within three years from one member
of one Earth system model. They do not establish performance across climate
models, model realizations or the real ocean. The next scientific expansion
should prioritize an independent model or area-weighted remapping audit before
adding more predictors or building causal feature explanations.
