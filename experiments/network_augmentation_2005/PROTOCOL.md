# Existing-network augmentation: 2005 pilot

This prospective execution protocol is written before the new fits, after earlier replacement-strategy results were already known. It is a new exploratory experiment, not an independent confirmation or a retrospective relabeling of the earlier study.

## Question and three arms

Can adding observations to historically unobserved locations improve reconstruction beyond a fixed existing observing network? At the same additional sample count, does gap-focused acquisition outperform random acquisition?

- **H:** every valid 2005 SOCAT month-location that exactly matches a complete 2005 model month-cell. Keep H unchanged in every arm and seed.
- **H + random:** H plus 1,000 unique remaining month-cells, drawn randomly within fixed equal month quotas.
- **H + gap:** H plus 1,000 unique remaining month-cells at locations with no valid SOCAT observation in any month during 1990–2005, drawn randomly within the same month quotas.

Historical gaps are spatial 1-degree locations, not only missing seasons. Valid SOCAT entries have positive observation count and finite fCO2. Actual fCO2 values are used only to identify valid observed entries; the response and SST/salinity in every fitted model come from the ESM. SOCAT fCO2 is never treated as interchangeable with model pCO2. Month-cell count is not cruise count, observation count or cost.

Use all twelve months of 2005 and the entire complete-case model-grid domain, with no 60°N restriction. Record unmatched SOCAT month-cells; do not interpolate or silently replace them. These grid cells cover the processed model domain, not every geographic ocean location. No ship accessibility, sea-ice or platform-feasibility mask is assumed. This is an idealized retrospective reconstruction, not future forecasting or a deployment recommendation.

## Evaluation and leakage prevention

Before acquisition, reserve 20% of **non-H** month-cells independently within each month × historical-gap stratum using one fixed seed. H is never discarded to form the evaluation set. All arms and seeds share the same evaluation cells; those cells are excluded from all acquisition pools. A location may have other months in training: this is missing-month-cell reconstruction, not wholly unseen-block transfer.

Primary evaluation is RMSE across the global unobserved domain. Also report MAE and signed bias, and each metric in historical-gap locations and previously observed locations. Use spherical 1-degree cell areas with inverse inclusion-probability correction for the stratified evaluation sample; normalize within each reported domain. Do not remove extreme target values or change the domain after seeing results.

Selection uses only coordinates, month and observed-coverage metadata, never pCO2 values, baseline prediction errors or model uncertainty. Equal month quotas isolate the change in spatial eligibility from a change in added seasonal allocation. Sampling is without replacement; all existing H records remain. Require enough eligible cells in every month, otherwise stop without silently changing the protocol.

## Model, contrasts and reporting

Reuse the existing feature construction and HistGradientBoosting hyperparameters. Disable early stopping in all arms so every fit uses its supplied training records for the same 150 boosting iterations. Fix model randomness across all fits; vary only the new observation choices using five prespecified paired acquisition seeds. Fit H once and reuse its prediction, rather than treating repeated copies of the same baseline as independent fits.

Retain all five seed outcomes. Report the mean, minimum and maximum of paired differences; with five seeds, do not add significance tests or bootstrap confidence claims. These describe acquisition variability conditional on one year, ESM member, fixed baseline, learner and test sample.

1. Baseline error minus H+random error: benefit of random additions.
2. Baseline error minus H+gap error: benefit of gap-focused additions.
3. H+random error minus H+gap error: benefit of gap targeting at equal added count.

Positive differences favor augmentation/gap targeting for magnitude errors. Signed bias is reported separately; smaller signed bias is not automatically better. Improvement of either augmented arm over H does not establish a targeting advantage. Gap targeting may benefit the gap domain while harming other regions; report both.

## Execution and provenance

Write input/code/config hashes and acquisition/evaluation indices before fitting. Preserve all per-seed metrics and evaluation predictions. Refuse to overwrite a started experiment. Run integrity tests before fitting. Notebook Run All reads completed outputs, verifies hashes and redraws figures only; it does not silently refit. Existing study code, results, website and Git history remain unchanged.

Sources: SOCAT v2025 (https://doi.org/10.25921/648f-fv35) provides observation support; IPSL-CM6A-LR historical r1i1p1f1 (https://doi.org/10.22033/ESGF/CMIP6.5195) provides simulated truth and predictors. This experiment evaluates the value of hypothetical observations of model truth, not reconstruction accuracy against independent real measurements.

## Addendum (2026-10-21, after results)

Not part of the prespecified protocol. After the global results were known, the
same design was rerun with latitude < 60°N and the connected-ocean (M1) and
open-ocean (M2) masks from `docs/osse_ocean_mask_protocol.md`, so this pilot
matches the headline study's domain. These reruns are post hoc; see README.
