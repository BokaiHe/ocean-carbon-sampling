# Ocean Carbon Sampling

An independent, reproducible study of how fixed-sample-count strategies affect out-of-sample reconstruction of Southern Ocean surface-ocean fCO2, followed by a global observing-system simulation experiment (OSSE) and an interactive web application.

This project is inspired by a collaborative course project in EESC/STAT 4243. The research question, experiment design, validation framework, implementation, and analyses in this repository are being independently redesigned.

## Research question

Under the same annual sample count, which seasonally aware spatial
allocation strategy improves blocked out-of-sample fCO2 reconstruction most
efficiently?

- random sampling;
- densifying historically sampled regions;
- expanding spatial coverage while representing all months;
- uncertainty-and-diversity-guided sampling.

## Temporal design boundary

This is a reconstruction experiment, not a future-forecasting experiment. All
12 months are modelled jointly with cyclic month features. The random hidden
set is stratified by month so that seasonal composition cannot confound the
strategy comparison; the stricter spatial holdout keeps all 12 months from a
location in the same fold.

A selection-only audit of the full three-year confirmatory design shows that
every one of the 1,800 strategy selections covers all 12 months. At budget
5,000, the mean absolute deviation from an equal monthly share is 0.292
percentage points for random sampling and 0.222 for spatial coverage. Their
comparison therefore primarily tests spatial allocation. Historical-density
sampling has a larger deviation of 0.875 percentage points and is interpreted
as a complete historical spatiotemporal observing-pattern baseline. See
[`docs/osse_temporal_design.md`](docs/osse_temporal_design.md).

## Regional validation result

![Five-fold spatial sensitivity](results/public/spatial_fold_sensitivity.png)

Across all five prespecified spatial holdouts and 20 sampling seeds per fold,
coverage sampling improved geographic balance in 100/100 fold-seed combinations.
Predictive gains were heterogeneous: four fold means favored coverage, three
fold-specific seed intervals were entirely above zero, and fold 4 favored random
sampling (mean RMSE gain −0.661 µatm; 95% seed-bootstrap interval −1.149 to
−0.192).

The defensible conclusion is therefore not that geographic coverage is always
superior, but that it reliably changes the sampling geometry and often improves
prediction depending on the held-out region. See
[`docs/spatial_sensitivity_results.md`](docs/spatial_sensitivity_results.md) for
the full result and interpretation boundary.

## Explainability gate

![XGBoost interpretability gate](results/public/diagnostic_interpretability_gate.png)

We tested whether environmental and geographic features could predict the
observation-level benefit of coverage sampling in unseen spatial blocks. The
diagnostic XGBoost models did not pass the prespecified grouped-validation gate:
the primary squared-error target had negative pooled out-of-fold R² for both
feature sets, and rank correlations were weak. SHAP values are therefore
withheld from the public interpretation rather than presented as scientific
drivers. See [`docs/diagnostic_results.md`](docs/diagnostic_results.md) for the
validation metrics and decision rule.

## Global OSSE figure drafts

The OSSE truth is the monthly surface-ocean `spco2` field from the CMIP6
IPSL-CM6A-LR historical simulation, member `r1i1p1f1`—not a SOCAT-derived
reconstruction product. SST and salinity from the same simulation are model
predictors. SOCAT is used only to construct the historical observing-pattern
baseline, so the truth does not inherit SOCAT's sparse sampling mask.

> **Draft visual layer.** These figures preserve the verified analysis and
> panel content, but their layout, typography, and legends are not final
> portfolio graphics. All source tables are retained for a later redesign.

![Locked global OSSE design](results/public/fig1_osse_design.png)

![Cross-year OSSE learning curves](results/public/fig2_cross_year_learning_curves.png)

![Fixed-sample-count error tradeoff and regridding robustness](results/public/fig3_error_tradeoff_and_robustness.png)

The locked global OSSE separates sampling geometry from sample count: each
strategy receives the same number of observations, uses the same reconstruction
model, and is evaluated against complete model truth. At sufficiently high
sample counts, coverage lowers p99 error but raises median, MAE and p95 error in
the month-stratified hidden-cell test. Its lower RMSE is therefore a
tail-sensitive consequence of a few very large errors, not independent evidence
of broad improvement. A stricter spatial-block holdout repeats five exhaustive
folds in 2005, 2010 and 2014 with 20 paired seeds. The same sub-p95 deterioration
persists, while the p99 benefit becomes directionally unstable: its mean
difference is −3.590 µatm, but only 9/15 year–fold units favour coverage. The
clean conclusion is that coverage lowers the extreme tail while raising error
in the more common range; that tail benefit is not stable when complete
regions are unseen. Historical-pattern sampling has a larger but estimand-
sensitive penalty. Under the original equal-cell full domain, whole-block RMSE
increases from 27.549 to 36.486 µatm (+8.936), all 15/15 units are worse, and
signed bias is approximately −4.85 µatm. Spherical evaluation weighting reduces
historical-minus-random bias to −2.049 µatm in hidden cells and −1.884 µatm in
whole blocks. When candidates and evaluation are both restricted below 60°N,
the area-weighted bias differences fall to −0.835 and −0.473 µatm, while MAE
remains worse by +2.466 µatm in 3/3 hidden years and +1.855 µatm in all 15/15
whole-block units. The robust conclusion is therefore an error-magnitude
penalty; the large signed offset is a high-northern, equal-cell-domain result.

The mechanism is topological rather than a simple effective-sample-size loss.
Across the complete 2005 mapped domain, 53.1% of spatial cells have zero
historical spatial-marginal weight (49.2% of spherical area). In the 2005
hidden-cell decomposition, zero-density cells contribute −5.010 µatm to the
equal-cell mean while positive-density cells contribute only −0.104 µatm.
Random sampling remains near zero across sample counts without a monotonic
trend. The current inputs do not include sea-ice concentration, so the <60°N
variant is a transparent feasibility proxy rather than a sea-ice mask. Full, source-grounded
draft captions and interpretation limits are provided in
[`docs/osse_portfolio_figure_legends.md`](docs/osse_portfolio_figure_legends.md).
The rerunnable narrative is available in
[`notebooks/published/osse_results_walkthrough.ipynb`](notebooks/published/osse_results_walkthrough.ipynb),
with a map-first visual demo in
[`notebooks/published/osse_visual_story_demo.ipynb`](notebooks/published/osse_visual_story_demo.ipynb),
and the exact redraw inputs are listed in
[`docs/osse_figure_data_inventory.md`](docs/osse_figure_data_inventory.md).

The hidden-cell redistribution is sample-count dependent. At count 500,
coverage is worse than random for RMSE and p99 in all three years; extreme-tail
suppression appears consistently only at 2,500 and 5,000. Median error is higher
at every tested count. Absolute baselines, relative changes, truth-field scale
references and full year–fold
distributions are reported in
[`docs/osse_claims_audit.md`](docs/osse_claims_audit.md).

## Project stages

1. **Regional minimum experiment** — SOCAT v2025, Southern Ocean, random versus coverage sampling.
2. **Regional benchmark** — all strategies, repeated seeds, temporal and spatial holdouts, probabilistic evaluation.
3. **Global OSSE** — subsample an Earth system model field using SOCAT-like masks and compare reconstructions with model truth.
4. **Interactive application** — explore observations, sampling choices, learning curves, and calibration.

## Repository policy

The repository intentionally excludes raw data, working notebooks, trained models, caches, logs, and uncurated experiment outputs. Only reusable source code, configuration, tests, a small demo dataset, published notebooks, and curated public results belong in Git.

## Quick start

```bash
python -m venv .venv
pip install -e ".[dev,model,osse,app,notebook]"
pytest
```

Data are not downloaded automatically. See [`data/README.md`](data/README.md) and the SOCAT data-use statement before running experiments.

Run the reproducible data audit, minimum experiment, and repeated-seed benchmark
after placing the SOCAT CSV at the configured raw-data path:

```bash
python scripts/make_data_audit.py data/raw/socat/SOCATv2025_tracks_gridded_monthly.csv
python scripts/run_minimal_experiment.py
python scripts/run_seed_benchmark.py
python scripts/plot_seed_benchmark.py
python scripts/run_spatial_sensitivity.py
python scripts/plot_spatial_sensitivity.py
python scripts/build_observation_effects.py
python scripts/run_xgb_shap_diagnostic.py
python scripts/plot_diagnostic_gate.py
python scripts/download_osse_pilot.py --dry-run
python scripts/audit_osse_inputs.py
python scripts/prepare_osse_pilot.py
python scripts/run_osse_gate.py
python scripts/run_osse_gate.py --phase benchmark
python scripts/prepare_osse_pilot.py --years 2010 2014
python scripts/run_osse_gate.py --phase cross_year
python scripts/prepare_osse_pilot.py --years 2005 2010 2014 --regrid area_weighted
python scripts/run_osse_gate.py --phase regrid_audit
python scripts/summarize_regrid_audit.py
python scripts/run_osse_spatial_block_gate.py
python scripts/run_osse_spatial_block_gate.py --config configs/osse_spatial_block_confirmatory.yaml
python scripts/audit_osse_month_balance.py
python scripts/run_historical_month_balance_audit.py
python scripts/summarize_historical_bias_density.py
python scripts/run_historical_area_domain_audit.py
python scripts/run_latitude_cap_audit.py
python scripts/summarize_osse_truth_scale.py
python scripts/plot_osse_portfolio_figures.py
jupyter lab notebooks/published/osse_results_walkthrough.ipynb
jupyter lab notebooks/published/osse_visual_story_demo.ipynb
```

## Current status

The SOCAT coverage audit, leakage-aware minimum experiment, 20-seed benchmark,
five-fold spatial sensitivity analysis, and spatially grouped XGBoost/SHAP
interpretability gate are implemented. The first global OSSE pilot is specified
for IPSL-CM6A-LR historical output (2005–2014), with input download and audit
tools ready. A three-seed, two-budget execution gate now compares random,
historical-density and spatial-coverage sampling on a common 2005 evaluation
set. The completed 20-seed, four-budget single-year benchmark identifies a
tradeoff between typical error and severe tail error. A prespecified robustness
phase repeats the full design in 2005, 2010 and 2014. At the largest sample
count, spatial coverage raises median, MAE and p95 error while reducing p99 and the
tail-sensitive RMSE in the random hidden-cell test. Historical-density
allocation is less accurate; its original equal-cell signed offset is strongly
attenuated by spherical evaluation weights and by an aligned <60°N feasibility
domain. The error-magnitude penalty is more robust: in the aligned area-weighted
audit, historical MAE remains higher in 3/3 hidden years and 15/15 whole-block
units. This remains a single-model, not a sea-ice-aware, real-ocean or
cross-model conclusion. In the confirmatory
three-year whole-block holdout, coverage still worsens median and MAE in all 15
units and p95 in 14/15; its p99 mean favours coverage but only 9/15 unit
directions agree. Historical-pattern RMSE is worse than random in 15/15. A
native-cell-area weighting audit at sample count 5,000 preserves the directions
of the three displayed, correlated coverage metrics; it is one robustness
audit rather than multiple independent tests. See
[`docs/osse_regrid_audit_results.md`](docs/osse_regrid_audit_results.md). Results are generated into
`results/public/`; raw observations, resumable work files, withheld exploratory
interpretations, and heavy local outputs remain excluded from Git.

Cross-model replication and a prespecified sea-ice/accessibility mask are the
decisive unresolved tests. The magnitude penalty may change under a different
spatial inductive bias, while the signed offset is already shown to depend
strongly on area weighting and the high-northern evaluation domain.
