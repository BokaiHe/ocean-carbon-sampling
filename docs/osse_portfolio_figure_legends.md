# Draft portfolio figure legends

> Status: **draft visual layer**. The underlying result tables, statistical
> definitions, and panel-to-data mapping are retained and verified. Layout,
> typography, and legend design will be replaced before portfolio publication.

## Fig. 1 | Locked global observing-system simulation experiment

**a,** Monthly surface-ocean `spco2` truth and SST and salinity predictors from
IPSL-CM6A-LR are processed to a common one-degree grid for 2005, 2010 and 2014.
Within each year, a fixed month-stratified 20% evaluation set is hidden from all
sampling strategies. **b,** Random, historical-density and spatial-coverage
rules acquire observations from the shared remaining pool at budgets of 500,
1,000, 2,500 and 5,000. Historical-density weights use SOCAT observations from
1990-2004; spatial coverage cycles across month by 5-degree latitude by
10-degree longitude blocks. **c,** Each selected sample trains the same locked
histogram gradient-boosting model using SST, salinity, latitude, cyclic
longitude and cyclic month features. Predictions are scored on common targets.
The full comparison uses 20 paired sampling seeds per year and includes
prespecified extreme-value and native-cell-area-weighting sensitivity analyses.

## Fig. 2 | Sampling-strategy learning curves across three model years

**a-c,** Global-ocean RMSE for random, historical-density and spatial-coverage
sampling in 2005 (**a**), 2010 (**b**) and 2014 (**c**). Lines show the mean and
shaded ribbons show plus or minus one standard deviation across 20 paired
sampling seeds at each budget. Delta annotations give the mean
spatial-coverage-minus-random RMSE difference at 5,000 observations. All
strategies use identical evaluation targets, predictors and reconstruction
settings within each year. Historical-density sampling remains least accurate,
whereas spatial coverage attains lower RMSE than random sampling at the largest
budget in all three years. Source data:
`results/public/osse_cross_year_metrics.csv`.

## Fig. 3 | Spatial coverage trades typical accuracy for protection against severe errors

**a-c,** Spatial-coverage-minus-random paired differences at a budget of 5,000
for global RMSE (**a**), median absolute error (**b**) and 99th-percentile
absolute error (**c**). Points show paired-seed mean differences and horizontal
lines show 95% percentile bootstrap intervals from 10,000 resamples of the 20
paired sampling seeds within each year. Negative values favour spatial
coverage. **d,** Prespecified strategy effects calculated from equal-weight
target bins and exact native-cell-area-weighted target bins. Colours identify
the effect and marker shapes identify the model year; the dashed line denotes
identity. All 12 effects retain their prespecified direction after native-area
weighting. Intervals quantify sampling-randomization variability within a fixed
model year, not uncertainty across years, models or the real ocean. Source data:
`results/public/osse_cross_year_paired_summary.csv` and
`results/public/osse_regrid_audit_paired_summary.csv`.
