# Global OSSE pilot protocol

## Scientific question

Under the same observation budget, does changing the spatial allocation of
surface-ocean carbon observations reduce reconstruction error against a complete
global truth field?

The regional SOCAT experiment cannot answer this conclusively because SOCAT has
no complete unobserved truth. The OSSE closes that gap by treating an Earth
system model field as known truth, hiding most grid cells, and measuring how well
each sampling strategy reconstructs them.

## Locked pilot scope

- CMIP6 source: IPSL-CM6A-LR historical;
- member: `r1i1p1f1`;
- table and native grid: `Omon`, `gn`;
- immutable source version: `v20180803`;
- truth: monthly `spco2`;
- initial predictors: monthly `tos` and `sos`;
- analysis window: January 2005 through December 2014;
- first execution gate: one complete year before the ten-year run;
- target analysis grid: global monthly 1 degree;
- initial budgets: 500, 1,000, 2,500 and 5,000 observations;
- repeated sampling: 20 seeds.

IPSL-CM6A-LR was selected because the official ESGF index exposes the three
required monthly ocean variables for the same experiment, member, grid and file
version. Mixed-layer depth and chlorophyll are available but intentionally
deferred until the three-variable pipeline closes.

## Experimental chain

1. Preserve the downloaded NetCDF files unchanged and verify byte size and
   SHA-256 against the ESGF manifest.
2. Select the locked analysis period before regridding.
3. Convert coordinates, calendars and units explicitly; never infer them from
   filename conventions alone.
4. For the one-year execution gate, assign native ocean-cell centres to regular
   1-degree bins and average values within each occupied bin. This creates no
   values over unoccupied land bins and uses one identical transformation for
   truth and predictors.
5. Construct observation masks at each fixed budget.
6. Compare random, historical-density and spatial-coverage allocation using the
   same reconstruction model and evaluation cells.
7. Score predictions against the complete withheld model truth globally and by
   basin.
8. Report marginal error reduction as budget increases.

## One-year execution gate

The first model comparison uses a fixed 20% evaluation sample stratified by
month. Evaluation positions are selected once with seed 2026 and are unavailable
to every sampling strategy. The remaining cells form the common acquisition
pool. This gives all strategies exactly the same evaluation targets.

Three target-blind acquisition rules are compared:

- `random`: uniform sampling without replacement;
- `historical_density`: weighted sampling using SOCAT observation counts from
  1990–2004 for the same month and 1-degree cell;
- `spatial_coverage`: one observation per 10-degree longitude by 5-degree
  latitude by month block before any block receives a second observation.

All strategies use identical budgets, seeds, predictors, model settings and
evaluation cells. The execution gate runs budgets of 500 and 1,000 with three
seeds before the prespecified 20-seed, four-budget experiment.

Primary metrics use every evaluation value. A separately labelled sensitivity
row recomputes metrics after excluding evaluation targets above 1,000
micro-atmospheres, the threshold frozen during input audit before strategy
results were inspected. This diagnostic tests whether a small extreme tail
dominates RMSE; it is not relabelled as an open-ocean analysis.

The single-year benchmark expands this design to 20 paired sampling seeds and
budgets of 500, 1,000, 2,500 and 5,000. Strategy-minus-random differences are
summarized across seeds with 10,000-resample percentile bootstrap intervals.
These intervals describe sampling-randomization variability conditional on the
fixed 2005 truth field, model and evaluation set; they do not represent
uncertainty across years, Earth system models or the real ocean. Budget-wise
intervals are treated as an effect-size learning curve, not as four independent
hypothesis tests.

## Prespecified three-year robustness phase

The first temporal robustness check uses 2005, 2010 and 2014, fixed before the
additional model runs as the start, midpoint and endpoint of the 2005-2014
analysis window. It repeats the complete 20-seed, four-budget design separately
within each year. All sampling strategies retain the SOCAT 1990-2004 density
window, so the historical allocation rule is defined only from observations
before every simulated target year.

Seed-level paired differences and bootstrap intervals are calculated within
each year. The three annual mean effects are then summarized by their range and
directional consistency. Because three selected model years are not an adequate
sample for population-level temporal inference, no across-year p value or
confidence interval is calculated. Agreement across these years is reported as
robustness within this model experiment, not as evidence of real-ocean
generality.

## Interpretation boundary

CMIP6 `spco2` is partial pressure, whereas SOCAT reports fugacity (`fCO2`). SOCAT
will define realistic observation locations and sampling density; its carbon
values are not interchangeable with the model truth. A result from one Earth
system model is a controlled proof of concept, not evidence that one strategy is
universally optimal in the real ocean.

The centre-bin mean is a pipeline-validation transformation rather than the
final regridding claim. Before the ten-year scientific comparison, it must be
checked against an area-weighted mapping using native cell area. Because all
sampling strategies in the pilot use the same processed truth field, this
provisional transformation does not advantage one strategy over another.

No finite model values are removed post hoc. The 2005 audit identifies a small
upper tail in `spco2` (81 processed values above 1,000 micro-atmospheres), with
the maximum in the Hudson Bay region. These values are retained for the pipeline
gate and must later be accompanied by a prespecified open-ocean/coastal
sensitivity analysis rather than silently clipped.

## Primary decision

The primary comparison is global-ocean RMSE at a fixed budget. A strategy is
scientifically useful only if any gain persists across seeds, years and major
basins rather than being driven by increased geometric coverage alone.

## Provenance

- CMIP6 dataset citation: <https://doi.org/10.22033/ESGF/CMIP6.5195>
- File-level URLs, sizes and checksums:
  `data/cmip6_osse_pilot_manifest.csv`
