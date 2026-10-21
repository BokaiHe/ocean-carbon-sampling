# Ocean-domain mask audit protocol

Written 2026-10-21, before any masked model fit. This is a prespecified
rerun of the existing latitude-cap headline audit
(`scripts/run_latitude_cap_audit.py`) on an explicitly defined ocean domain.
It closes the "ocean-domain check: unresolved" limitation shown on the website.
It is not an independent confirmation and does not add a new sampling rule.

## Why this audit exists

The OSSE never applied an explicit ocean mask. A 1-degree location enters the
candidate pool whenever native IPSL-CM6A-LR grid cells fall in it and `spco2`,
`tos` and `sos` are all finite. The model grid therefore defines "ocean".
That grid contains water bodies that are not connected to the world ocean.

## What was seen before writing this protocol

Disclosed so the design is not presented as blind:

- Domain structure only (no errors): 8-connected components of the union of
  complete-case 1-degree locations across 2005, 2010 and 2014, with periodic
  longitude. Besides the world-ocean component (40,291 locations), three
  isolated components reach below 60°N: the Caspian Sea (54 locations), the
  North American Great Lakes (45) and Lake Victoria (8). The remaining 68
  isolated components lie entirely north of 60°N and are outside the headline
  domain.
- A scan against Natural Earth 1:110m land of class shares, `spco2` and
  salinity summaries, and the share of SOCAT 1990–2004 density weight per
  class (Baltic 6.4%, coast-touching cells 15.6%, Caspian 0%).
- One outcome-based look: in the saved 2005 full-domain supporting per-cell
  errors, excluding the Caspian, named marginal seas or coast-touching cells
  from evaluation only left the historical-density minus random MAE gap at
  +19.4% to +21.0% below 60°N (baseline +20.2%). That check did not refit
  models and cannot show training-side effects. No other masked outcome was
  computed before this protocol.

## Masks

Every mask is a set of 1-degree locations, identical in all months and years.
It is applied to **both** the acquisition pool and the evaluation cells. The
existing 60°N cap (latitude < 60) still applies.

- **M0, reference:** the existing latitude-cap domain. Its saved outputs
  (`results/public/osse_latitude_cap_*.csv`) are the reference and are not
  overwritten.
- **M1, primary: connected ocean.** Remove every location whose component is
  not the largest 8-connected component of the three-year union of
  complete-case locations, labelled on the full globe with periodic longitude
  before the latitude cap. Below 60°N this removes exactly the three lakes
  listed above (107 locations). Marginal seas connected to the ocean remain,
  because they are ocean in the model and dense SOCAT sampling there is part of
  the historical-density behaviour under study.
- **M2, sensitivity: open-ocean interior.** M1, then additionally remove:
  1. marginal seas, each defined by flood fill on the M1 grid from a seed
     location, restricted to a bounding box:
     | Sea | Seed (lat, lon) | Box latitude | Box longitude |
     |---|---|---|---|
     | Mediterranean and Black Sea | 35.5, 18.5 | 30 to 47.5 | -5.5 to 42 |
     | Baltic Sea | 58.5, 20.5 | 53 to 66 | 9.5 to 31 |
     | Hudson Bay | 58.5, -85.5 | 51 to 70 | -96 to -70 |
  2. coastal locations: an M1 location with at least one of its eight
     neighbours (periodic longitude, on the full-globe grid before the latitude
     cap) outside the three-year model-water union. This uses the model's own
     land-sea geometry; no external coastline is downloaded.

The mask builder writes `results/public/osse_ocean_mask_cells.csv` (one row per
location: latitude, longitude, component id, `in_m1`, `in_m2`, exclusion
reason) and a map of excluded locations. Before any fit, the counts per class
and the map are checked for definition errors only, for example a flood fill
leaking into the Atlantic. A definition fix at that stage is recorded in this
file and the mask is then fixed.

### Definition check record (2026-10-21, before any fit)

`scripts/build_ocean_mask.py` was run and its map inspected; no error metric
was computed.

- **Fix: coastal rule.** The first build flagged open-ocean locations around
  50–60°N and in the Arctic as coastal. Cell-centre binning of the curvilinear
  native grid leaves empty 1-degree holes in open water, and their neighbours
  counted as "next to land". The rule now treats a non-water location as
  land-like only if it overlaps Natural Earth 1:110m land (10 × 10 sub-points,
  local Cartopy cache) or its 8-connected non-water component has more than 10
  locations. The second clause keeps Antarctic ice-shelf fronts as coast.
  Below 60°N this changed coastal locations from 2,852 to 2,536.
- **Label: disconnected water.** North of 60°N, isolated components are polar
  binning fragments, not lakes, so the exclusion reason is
  `disconnected_water`. They lie outside the headline domain.
- **Checked without change:** the Mediterranean and Black Sea fill stops at
  Gibraltar (westmost 36.5°N, 5.5°W) and excludes the Bay of Biscay; the
  Baltic fill reaches 9.5°E, including part of the Kattegat and Skagerrak;
  the Hudson Bay fill spans 51.5–69.5°N, 94.5–70.5°W. The Red Sea and
  Persian Gulf were not in the prespecified list and remain in M2.

Frozen counts below 60°N: 36,215 M0 locations; M1 removes 107 (Caspian 54,
Great Lakes 45, Lake Victoria 8), leaving 36,108; M2 additionally removes 483
marginal-sea and 2,536 coastal locations, leaving 33,089.

## Design held fixed

Identical to the latitude-cap headline audit unless stated:

- truth and predictors: IPSL-CM6A-LR historical `r1i1p1f1`, 2005, 2010, 2014,
  native-cell-centre 1-degree bin means;
- learner, features and hyperparameters: unchanged;
- strategies: random, historical-density (SOCAT 1990–2004 `fco2_count`),
  spatial coverage (10° × 5° × month blocks);
- 5,000 samples, seeds 0–19, paired across strategies;
- weighting: equal-cell and spherical cell area; bias, MAE and RMSE.

Evaluation units:

- **Hidden cells (primary).** The M0 hidden set (seed 2026, 20% within each
  month on the <60°N frame) restricted to locations kept by the mask. The set
  is not redrawn, so differences from M0 reflect the mask rather than a new
  test sample.
- **Whole blocks (stress test).** The five existing 20° × 10° checkerboard
  folds, recomputed geometrically on the masked frame.

That gives 3 hidden-cell units and 15 year-fold units per mask, with 20 seeds
each.

## Code check

Before the masked runs, rerun M0 for 2005 hidden cells through the new script
and confirm it reproduces the saved latitude-cap metrics.

## Primary estimand and reporting

Primary: historical-density minus random MAE, spherical area weighting, hidden
cells, M1, averaged over the three years. Report for M0, M1 and M2, both
comparisons (historical-density and coverage, each minus random), all three
metrics and both weightings:

- year-unit means and the mean across units;
- the number of units with the comparator worse than random (3 hidden, 15
  whole-block);
- per-class counts of removed locations and month-cells.

All rows are published. No masks, years, seeds or metrics are dropped after
seeing results. Unit counts are descriptive; the three years share one ESM
run, so no significance test is claimed.

## Decision rules for the website and README

Fixed now, applied after the run whatever the result:

1. The headline numbers become the M1 values. M0 stays available as the
   pre-audit reference.
2. The "ocean-domain check: unresolved" warnings are replaced by a statement
   of the mask used and a link to these results.
3. If historical-density minus random MAE under M2 has the same sign as under
   M1 in all three hidden-cell years, the brief may say the direction is robust
   to excluding marginal seas and coastal cells. Otherwise the headline must say
   the result is sensitive to that domain choice.
4. Coverage statements follow the same rule separately for MAE and RMSE.
5. Any further mask tried after seeing these results is labelled post hoc.

## Outputs

- `results/public/osse_ocean_mask_cells.csv` and the excluded-location map;
- `results/public/osse_ocean_mask_{metrics,unit_summary,paired,overall}.csv`;
- `results/osse_ocean_mask_work/` caches (ignored);
- `docs/osse_ocean_mask_results.md`.

## Boundaries

This audit fixes the domain definition only. It does not test other ESMs,
learners, observation noise, sea-ice access or the Arctic north of 60°N.
