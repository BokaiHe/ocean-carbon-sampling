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
3. **Ask where to add observations next.** A separate 2005 pilot keeps the real
   SOCAT network and adds 1,000 cells at random or in historical gaps; see
   [Adding to the existing network](#adding-to-the-existing-network-2005-pilot).

The website reads frozen JSON only. It does not fit models, optimize ship
routes or estimate deployment benefits in the browser.

## Interactive brief

A bilingual (English / 中文) single page: video opening, then
**introduction → background → method → three findings → robustness →
conclusion → limits → sources**. Text is kept short; method details and every
table live in `docs/` and the notebooks.

- **Background:** a globe of observed SOCAT v2025 surface-water **fCO₂ (µatm)**
  for 2005, 2010 and 2014, by year and month. Dots are observed 1° grid-cell
  centres, not ship positions; all-month values average available months only.
- **Method:** the five-step OSSE, a per-block heatmap and samples-per-block
  histogram for each sampling rule, the design of the augmentation pilot, and a
  globe of the 2005 full-domain sampling and error fields (a pre-mask supporting
  view, labelled as such).
- **Findings:** paired MAE by year and by whole-block unit (connected-ocean
  mask); coverage minus random under the three ocean masks; the augmentation
  pilot (open-ocean mask) with an addition map, RMSE by region and per-seed
  effects.
- **Conclusion** links each claim back to its finding.

NASA Earth Observatory and NOAA Ocean Exploration photographs are credited at
their point of use and are context, not experiment outputs. Coastlines are
public-domain Natural Earth; D3 7.9.0 (ISC) is vendored locally. Fonts are Inter
and Noto Sans SC.

## Two evaluations, two questions

Both headline comparisons use **5,000 samples, spherical cell-area weighting,
and candidates and evaluation jointly restricted to latitude <60°N and to the
connected-ocean mask**. The latitude cutoff is not a sea-ice or
physical-accessibility mask.

| Evaluation | Random MAE | Historical-density MAE | Difference | Relative increase | Descriptive consistency |
|---|---:|---:|---:|---:|---|
| Primary: dispersed hidden cells | 9.226 | 11.746 | +2.520 | +27.32% | 3/3 year means worse |
| Stress test: whole blocks | 11.363 | 13.404 | +2.041 | +17.96% | 15/15 year-fold means worse |

Units: µatm. Differences are calculated before rounding. These magnitudes are
**conditional on one IPSL-CM6A-LR simulation and one locked HistGradientBoosting
learner**, not universal penalties for the real network.
[Source table](results/public/osse_ocean_mask_overall.csv).

**Ocean-domain mask audit, 2026-10-21.** The model grid had placed the Caspian
Sea, the Great Lakes and Lake Victoria (107 of 36,215 locations below 60°N) in
the "ocean" pool. The primary connected-ocean mask (M1) removes them from both
sampling and testing; a sensitivity mask (M2) also removes the Mediterranean
and Black Sea, the Baltic, Hudson Bay and land-adjacent cells. Before the mask
the headline was +25.94% (hidden) and +15.67% (whole blocks); under M2 it is
+27.91% and +20.00%, worse in 3/3 years and 15/15 units throughout.
[Protocol](docs/osse_ocean_mask_protocol.md) ·
[results](docs/osse_ocean_mask_results.md).

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
  [Per-unit effects](results/public/osse_ocean_mask_paired.csv).

**Presentation revision, 2026-09-23:** hidden-cell results now anchor the brief;
whole-block results are a stress test. This is a post-analysis reframing of
existing runs, not a new preregistered experiment. Older notebooks and audit
documents retain their earlier whole-block-default narrative as provenance.
[Current positioning and scope](docs/project_positioning.md).

## What broader coverage does, and does not, show

Under the primary masked evaluation, coverage changes MAE by
**+0.394 µatm** (9.226 to 9.620), while lowering the tail-sensitive RMSE by
**1.008 µatm** (20.075 to 19.067). Under the whole-block stress test, MAE is
nearly unchanged (+0.017 µatm) and RMSE is lower (−1.869 µatm).
Neither combination establishes overall superiority. The RMSE advantage comes
mostly from marginal seas and coastal cells: excluding them (M2) shrinks it to
−0.250 µatm (hidden cells) and −0.178 µatm (whole blocks).
The 12-variant evaluation table, sample-count sweep and error maps remain
pre-mask supporting analyses in `docs/` and `results/public/`; the website's
experiment globe is labelled as pre-mask.

The sample-count sweep is a **separate supporting analysis**: original
full-domain, equal-cell hidden evaluation. At 500 samples, coverage raises
median, p99 and RMSE; at higher counts, extreme-tail reductions coexist with
higher median error. This is conditional on the fixed learner, not an isolated
causal effect of geometry. [Claims audit](docs/osse_claims_audit.md).

## Adding to the existing network (2005 pilot)

A different design from the replacement rules above: keep every 2005 SOCAT
month-cell that matches the model ocean (H), add **1,000** cells either at random
or only at locations SOCAT never observed in 1990–2005 (equal monthly quotas),
and score all arms on one shared hidden set with five paired acquisition seeds.

Reported domain: **open-ocean interior (M2), latitude < 60°N.** Area-weighted
RMSE, µatm, mean of five seeds:

| Evaluation cells | H | H + random | H + gap | Gap − random advantage |
|---|---:|---:|---:|---:|
| All unobserved | 16.067 | 13.160 | 13.031 | 0.128 (5/5 seeds) |
| Historical gaps | 17.538 | 13.920 | 13.415 | 0.505 (5/5) |
| Previously observed | 14.751 | 12.502 | 12.708 | −0.206 (0/5) |

Adding observations helps everywhere; aiming them at gaps adds a small,
consistent extra inside the gaps at a cost where ships already go.

**Order of analysis, stated plainly.** The pilot was first run globally without
an ocean mask (gap advantage 0.462 µatm RMSE). The connected-ocean (M1) and
open-ocean (M2) reruns were chosen **after** seeing that result, to match the
headline study's domain; they are post hoc. Under M1 the advantage is 1.321 µatm,
but about 80% of its squared-error reduction comes from Hudson Bay cells below
60°N; the global figure was likewise driven by the Arctic and inland lakes. All
three runs are kept: [study README](experiments/network_augmentation_2005/README.md).

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
- Ocean-domain mask audit (connected ocean and open-ocean sensitivity):
  [protocol](docs/osse_ocean_mask_protocol.md),
  [results](docs/osse_ocean_mask_results.md).
- Existing-network augmentation pilot, global and domain-matched reruns:
  [study](experiments/network_augmentation_2005/README.md).
- Rerunnable [results walkthrough](notebooks/published/osse_results_walkthrough.ipynb),
  updated with the ocean-mask audit and augmentation pilot, and the earlier
  [visual demo](notebooks/published/osse_visual_story_demo.ipynb), which keeps
  the pre-mask presentation.
- Frozen web brief and [figure-data inventory](docs/osse_figure_data_inventory.md).
  Source tables remain preserved; no new numerical experiment accompanies this revision.

## Run locally

```bash
python -m venv .venv
pip install -e ".[dev,model,osse,app,notebook]"
pytest
```

For the website (Node.js 22.12+; deployment uses Node.js 24):

```bash
npm ci
npm run dev
# Production preview:
npm run build
npm run preview
```

Open the localhost URL printed by Vite, not `site/index.html` via `file://`.
The React hero is pre-rendered for readable no-JavaScript fallback, then hydrated
for video and navigation controls. The existing research visualizations remain
independent; their frozen data and calculations are unchanged. Vite builds `dist/`,
which can be previewed locally. The deployed entrance uses the owner's authorized
`site/licensed/Hero9.tsx`; `site/src/Hero.jsx` provides a public-clone fallback and
shared navigation/media settings. Do not hand-edit the generated header in
`site/index.html`; `npm run render:hero` updates the checked-in HTML.

### Licensed visual components and publishing

The Hero 9 entrance uses the owner-supplied React Bits Pro block with Motion and
Lucide icons: full-height video, character-by-character blur reveal and translucent
research links. Its source stays in ignored `site/licensed/Hero9.tsx`. Public clones
build the fallback hero without that file. `OMIT_LICENSED_HERO=1` tests this path.
The video uses the external URL provided with the block; see
`site/assets/context/hero9-source.md`. No media attribution is overlaid on the hero.
The unrelated mountain poster was removed; a solid dark-blue background appears
while the video loads, or when motion is reduced.
Reduced motion and data-saving settings prevent automatic video playback. Neither
background displays a pause button, as requested by the owner.

The findings cover uses a user-supplied React Bits Pro Mosaic Waves
component. Its source lives in ignored `site/licensed/MosaicWaves.tsx` and is not
distributed in this public repository. Public clones build with a static fallback;
all research data, charts and controls work without the paid component. Motion is
paused or omitted when reduced motion, data saving, offscreen state or hidden
tabs require it.

Run `npm run publish:site` locally to build and publish only the compiled application
to `site-build`. GitHub Pages deploys that branch through Actions. The command checks
the remote and rejects TypeScript, JSX and source maps in the artifact; it never
uploads `site/licensed`. The publisher dispatches the protected main-branch workflow,
which deploys the compiled `site-build` artifact; pushing main alone does not rebuild it.
No model run or raw-data download is required to preview the checked-in site.

Page code: `site/index.html` (structure, English text), `site/i18n.js` (Chinese
text and language switch), `site/ocean.css` (styles and type scale),
`site/story.js` (charts) and `site/globes.js` (both globes).

To regenerate the page data from frozen outputs (no model fitting):

```bash
python scripts/export_site_chart_data.py      # paired MAE units and mask audit
python scripts/export_site_augmentation.py    # open-ocean augmentation run
python scripts/export_site_globe_data.py      # experiment globe
python scripts/export_site_observations.py    # SOCAT globe (needs the local CSV)
```

The repository excludes raw data, trained models, caches, working notebooks
and uncurated outputs. For experiment reproduction, start with
[`data/README.md`](data/README.md), existing `configs/` and their corresponding
`scripts/run_*.py` runners. Data are not downloaded automatically.
