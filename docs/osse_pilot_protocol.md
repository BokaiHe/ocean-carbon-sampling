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
4. Regrid truth and predictors to a common 1-degree grid with an ocean mask.
5. Construct observation masks at each fixed budget.
6. Compare random, historical-density and spatial-coverage allocation using the
   same reconstruction model and evaluation cells.
7. Score predictions against the complete withheld model truth globally and by
   basin.
8. Report marginal error reduction as budget increases.

## Interpretation boundary

CMIP6 `spco2` is partial pressure, whereas SOCAT reports fugacity (`fCO2`). SOCAT
will define realistic observation locations and sampling density; its carbon
values are not interchangeable with the model truth. A result from one Earth
system model is a controlled proof of concept, not evidence that one strategy is
universally optimal in the real ocean.

## Primary decision

The primary comparison is global-ocean RMSE at a fixed budget. A strategy is
scientifically useful only if any gain persists across seeds, years and major
basins rather than being driven by increased geometric coverage alone.

## Provenance

- CMIP6 dataset citation: <https://doi.org/10.22033/ESGF/CMIP6.5195>
- File-level URLs, sizes and checksums:
  `data/cmip6_osse_pilot_manifest.csv`
