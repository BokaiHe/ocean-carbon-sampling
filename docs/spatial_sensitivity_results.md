# Five-fold spatial sensitivity results

## Main result

The predictive effect of coverage sampling is heterogeneous across the five
prespecified spatial holdouts, despite consistently improved training-sample
balance.

| Held-out fold | Mean RMSE gain | 95% seed-bootstrap interval | Coverage wins |
|---|---:|---:|---:|
| Fold 0 | 0.594 µatm | 0.371 to 0.811 | 18/20 seeds |
| Fold 1 | 0.794 µatm | 0.274 to 1.388 | 14/20 seeds |
| Fold 2 | 0.130 µatm | −0.048 to 0.313 | 12/20 seeds |
| Fold 3 | 0.619 µatm | 0.409 to 0.834 | 18/20 seeds |
| Fold 4 | −0.661 µatm | −1.149 to −0.192 | 6/20 seeds |

Positive RMSE gain means RMSE(random) − RMSE(coverage), so positive values favor
coverage. Four of five fold means are positive, but only three fold-specific
seed-bootstrap intervals are entirely above zero. The equally weighted mean of
the five fold means is 0.295 µatm, with an across-fold standard deviation of
0.588 and a range from −0.661 to 0.794 µatm.

The coefficient of variation of observations per coverage cell improves in all
100 fold-seed combinations. Its five fold means range from 0.948 to 0.999. Thus,
the acquisition rule performs its intended geometric operation consistently,
but geometric balance does not guarantee lower prediction error in every held-
out region.

## Figure legend

Panel a shows all paired seed-level RMSE effects for each held-out spatial fold
(n = 20 prespecified sampling seeds per fold). Black markers are fold means and
error bars are two-sided 95% percentile bootstrap intervals from 10,000
resamples of the 20 seed effects within that fold. The dashed line denotes no
difference. Panel b shows all occupied pre-2020 20° × 10° validation blocks,
colored by their deterministic fold assignment. No seed or fold was excluded;
no p values or significance thresholds are used.

## Interpretation

The earlier single-fold result was real for fold 0 but was not spatially
universal. The defensible regional conclusion is that coverage sampling improves
the spatial balance of selected observations and often, but not always, improves
blocked prediction. Fold 4 is a planned negative result and should remain
prominent in the portfolio because it motivates the next scientific question:
which environmental or geographic distribution shifts make uniform geographic
coverage insufficient?

## Remaining boundary

The five folds exhaust the current checkerboard assignment but still fix the
20° × 10° block size, model, predictors, time cutoff, and observed SOCAT support.
The next analysis should diagnose fold-specific covariate shift and error before
designing the global OSSE sampling strategies.
