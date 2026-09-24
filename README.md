# Ocean Carbon Sampling

A reproducible fixed-sample-count observing-system simulation experiment (OSSE)
and interactive research brief by **Bokai He**, Columbia University, Earth and
Environmental Engineering. Contact: **bh2954@columbia.edu**.

**[Open the interactive research brief](https://bokaihe.github.io/ocean-carbon-sampling/)**

## Research question and storyline

At the same annual number of selected month-cells, how do **random**,
**historical-density** and **seasonally aware coverage** sampling change monthly
surface-ocean pCO2 reconstruction error under a specified learner and domain?

1. **Quantify the cost of historical-density allocation.** This is a controlled
   estimate, not a new discovery that real-world ocean sampling is uneven.
2. **Test the limits of broader coverage.** Coverage does not improve every
   error measure; its effects depend on sample count and evaluation.
3. **Ask where to add observations next.** That is a future experiment on an
   existing network, not a question answered by these replacement rules.

The website reads frozen JSON and pre-rendered maps. It does not fit models,
optimize ship routes or estimate deployment benefits in the browser.

The presentation combines an ocean-image opening and field photography with
interactive evidence charts. NASA Earth Observatory / Michala Garrison and
NOAA Ocean Exploration photographs are credited at their point of use and
identified as context, not experiment outputs. The chapter navigation and large
globe layout draw visual inspiration from [Seasats](https://www.seasats.com/),
without copying its assets, fonts, code or vessel tracks.

The interactive globe reads the existing 2005 full-domain sampling and error
fields: drag or use arrow keys to rotate, use +/− to zoom, switch strategies and
select sampling counts, local MAE, or MAE differences from random. It shows
supporting results, **not the aligned-domain headline evaluation**. Sampling
points are block centres, not ship positions; no real or simulated routes are
displayed. Coastlines use public-domain Natural Earth data and locally vendored
D3 7.9.0 (ISC). Data load only near the globe; original flat maps are retained.

Rebuild its data from saved results (no model fitting):

```powershell
python scripts/export_site_globe_data.py
```

The exporter retains all locations and missing errors, rounding display values
to four decimal places. The original Parquet/CSV outputs retain full precision.
Frozen headline scores and experiment protocols remain unchanged.

## Two evaluations, two questions

Both headline comparisons use **5,000 samples, spherical cell-area weighting,
and candidates and evaluation jointly restricted to latitude <60°N**.
The latitude cutoff is not a sea-ice or physical-accessibility mask.

| Evaluation | Random MAE | Historical-density MAE | Difference | Relative increase | Descriptive consistency |
|---|---:|---:|---:|---:|---|
| Primary: dispersed hidden cells | 9.508 | 11.975 | +2.466 | +25.94% | 3/3 year means worse |
| Stress test: whole blocks | 11.836 | 13.691 | +1.855 | +15.67% | 15/15 year-fold means worse |

Units: µatm. Differences are calculated before rounding. These magnitudes are
**conditional on one IPSL-CM6A-LR simulation and one locked HistGradientBoosting
learner**, not universal penalties for the real network.
[Source table](results/public/osse_latitude_cap_overall.csv).

- **Primary:** reserve approximately 20% of month-cells within each month
  before sampling. One fixed test set per year is shared by all strategies
  and 20 paired seeds. This tests dispersed missing-cell reconstruction, not
  full-field performance after sampling from the unrestricted domain.
- **Stress test:** exclude all months in held-out 20° × 10° blocks before
  sampling. Five checkerboard folds have no buffer. Each of the 15 year-fold
  means averages 20 paired seeds.
- The three years share one ESM run. Direction counts are descriptive,
  not independent-replicate significance tests. No formal whole-block
  significance test is claimed.
  [Per-unit effects](results/public/osse_latitude_cap_paired.csv).

**Presentation revision, 2026-09-23:** hidden-cell results now anchor the brief;
whole-block results are a stress test. This is a post-analysis reframing of
existing runs, not a new preregistered experiment. Older notebooks and audit
documents retain their earlier whole-block-default narrative as provenance.
[Current positioning and scope](docs/project_positioning.md).

## What broader coverage does, and does not, show

Under the primary aligned-domain evaluation, coverage changes MAE by
**+0.186 µatm** (9.508 to 9.695), while lowering the tail-sensitive RMSE by
**1.745 µatm** (20.766 to 19.021). Under the whole-block stress test, MAE is
nearly unchanged (−0.007 µatm) and RMSE is lower (−2.201 µatm).
Neither combination establishes overall superiority.

The sample-count line chart uses a **separate supporting analysis**: original
full-domain, equal-cell hidden evaluation. At 500 samples, coverage raises
median, p99 and RMSE; at higher counts, extreme-tail reductions coexist with
higher median error. This is conditional on the fixed learner, not an isolated
causal effect of geometry. [Claims audit](docs/osse_claims_audit.md).

## A methodological self-correction

Historical-density minus random signed bias in the **whole-block stress test**
changes with the quantity being estimated:

| Weighting and domain | Bias difference, µatm |
|---|---:|
| Full domain, equal-cell | −4.954 |
| Full domain, spherical area | −1.884 |
| Evaluation only <60°N, spherical area | −0.631 |
| Candidates and evaluation <60°N, spherical area | −0.473 |

These are not four independent confirmations. The last value is not the primary
hidden-cell estimate (−0.835 µatm). The original large offset was reclassified
as an estimand-sensitivity example, not evidence of a universal signed bias.

The 2005 full-domain structural-zero maps and density diagnostics are supporting
analyses, not a decomposition of the primary result or a causal map of the
best places to add observations.

## Data, methods and boundaries

- **Truth:** monthly CMIP6 IPSL-CM6A-LR historical `spco2`, member `r1i1p1f1`,
  for 2005, 2010 and 2014. Not a SOCAT-derived reconstruction product.
- **Sampling:** random gives candidates equal probability; historical-density
  samples without replacement using SOCAT 1990–2004 month-location count
  weights; coverage prioritizes underrepresented month-space blocks.
  Historical-density does not replay cruises, repeat lines or trajectories.
- **Idealized observations:** monthly model-grid truth has no added measurement
  or representation error. SST and salinity are from the same simulation.
  Real-world errors and strategy rankings remain unverified.
- **Locked learner and limited features:** fixed HistGradientBoosting settings
  across counts and strategies; inputs are SST, salinity, latitude, cyclic
  longitude, year and cyclic month. No MLD, chlorophyll or atmospheric CO2.
  No ablation establishes which features dominate. Sample-count responses
  depend on the learner as well as sampling.
- **Separate yearly fits:** all 12 months are fitted jointly within each year;
  the year feature is constant within a fit. Continuous interannual variability,
  trends and decadal carbon-sink skill are not evaluated.
- **Fair within-protocol comparison:** target-blind sampling, common test sets,
  paired seeds and nested sample-count prefixes. Month-balance controls and
  native-cell-area regridding remain supporting audits.

Cross-learner and cross-ESM generality, noisy observations, full-field recovery
after unrestricted sampling, integrated flux, sea-ice-aware access and feasible
observation-addition plans remain **not yet supported**.

## Related work and attribution

The model-truth approach builds on the Large Ensemble Testbed literature,
including [Gloege et al. (2021)](https://doi.org/10.1029/2020GB006788).
[Heimdal et al. (2024)](https://doi.org/10.5194/bg-21-2159-2024) evaluates
autonomous additions to SOCAT using pCO2-Residual and multiple ESMs. Our
fixed-count rules, single learner and held-out evaluations answer a smaller,
different question, not a replication or superiority claim.
[Full references and verified method distinctions](docs/project_positioning.md).

This is an independent extension of a **Spring 2025 EESC/STAT 4243 course
project in Galen A. McKinley's class**. This credit refers to the course
foundation, not supervision or endorsement of every subsequent extension.

The [original collaborative project](https://github.com/spariser/ReconstructOceanCarbonP3G1)
was by **Azam Khan, Bokai He, Sarah Pariser and Zhi Wang**. Its public
contribution statement credits Bokai He with statistical significance analysis
and NGBoost/XGBoost comparison. The team's work is not represented as
sole-authored. This repository separately develops fixed-count experiments,
evaluation audits and the interactive brief. Course-level statistical tests
are not evidence of formal significance in the present OSSE.

## Completed work and retained evidence

- Regional SOCAT minimum experiment and repeated-seed spatial benchmark:
  [regional sensitivity](docs/spatial_sensitivity_results.md).
- Spatially grouped XGBoost interpretability gate: it failed to generalize
  sufficiently, so SHAP was withheld as a driver explanation:
  [gate decision](docs/diagnostic_results.md).
- Global OSSE, cross-year/sample-count comparisons, month-balance controls,
  regridding and area/domain audits:
  [temporal design](docs/osse_temporal_design.md),
  [regridding audit](docs/osse_regrid_audit_results.md).
- Rerunnable [walkthrough](notebooks/published/osse_results_walkthrough.ipynb)
  and [visual demo](notebooks/published/osse_visual_story_demo.ipynb).
  These preserve the earlier presentation; use this README for current scope.
- Frozen web brief and [figure-data inventory](docs/osse_figure_data_inventory.md).
  Source tables remain preserved; no new numerical experiment accompanies this revision.

## Run locally

```bash
python -m venv .venv
pip install -e ".[dev,model,osse,app,notebook]"
pytest
python -m http.server 8000 --directory site
```

Open `http://localhost:8000/`, not `site/index.html` via `file://`.
No model run or raw-data download is required to preview the checked-in site.
The paired MAE chart foregrounds `area|both60|hidden`, alongside the whole-block
stress test. The separate signed-bias dot chart uses whole-block results only.
All four sample counts and all 12 evaluation variants are visible simultaneously;
hover, tap or focus marks for values, or expand the accessible source tables.

To regenerate site assets from curated outputs and required local inputs:

```bash
python scripts/build_static_site_assets.py
python scripts/export_site_chart_data.py
python scripts/build_site_error_map.py
```

The second command reads only frozen paired-unit and sampling-summary outputs;
it does not train models. It exports `site/data/chart-data.json` for the 3 + 15
paired rows and illustrative occupied-block bars. The other charts read the
unchanged `site-data.json`. Scope notes remain directly below each chart.

The supporting 2005 full-domain error map is now displayed, built by subtracting
the saved per-cell mean absolute errors without fitting or new predictions.
Its CSV retains missing values and values beyond the ±30 µatm colour scale;
see [map contract and QA](docs/site_error_map_notes.md). Aligned-domain caches contain aggregate
scores, not per-cell predictions. Clipping the old fields would not reproduce
the aligned training pool, so no primary-scope penalty map is claimed.

The repository excludes raw data, trained models, caches, working notebooks
and uncurated outputs. For experiment reproduction, start with
[`data/README.md`](data/README.md), existing `configs/` and their corresponding
`scripts/run_*.py` runners. Data are not downloaded automatically.
