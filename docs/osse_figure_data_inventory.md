# OSSE figure-data inventory

## Status

The current composite figures are visual drafts. Their source data remain the
authoritative inputs for later redrawing; no values need to be recovered from
PNG, PDF, or SVG files.

## Retained redraw inputs

| File | Role | Granularity |
| --- | --- | --- |
| `results/public/osse_cross_year_metrics.csv` | Learning curves and absolute performance | year × domain × strategy × budget × seed |
| `results/public/osse_cross_year_paired_summary.csv` | Fixed-sample-count paired effects and bootstrap intervals | year × domain × budget × comparison × metric |
| `results/public/osse_regrid_audit_paired_summary.csv` | Equal-bin versus native-cell-area robustness | regrid method × year × domain × budget × comparison × metric |
| `results/public/osse_cross_year_design.csv` | Locked cross-year design metadata | design record |
| `results/public/osse_cross_year_versions.csv` | Runtime and package provenance | software component |
| `results/public/osse_regrid_audit_design.csv` | Regridding-audit design metadata | design record |
| `results/public/osse_regrid_audit_versions.csv` | Regridding-audit runtime provenance | software component |
| `results/public/osse_visual_demo_fields.parquet` | Representative hidden-evaluation error maps | 2005 spatial grid cell |
| `results/public/osse_visual_demo_sampling.parquet` | Fixed-sample-count sampling-density maps | strategy × 5° × 10° block |
| `results/public/osse_visual_demo_metadata.csv` | Demo year, seed, budget and row-count boundary | one representative-map record |
| `results/public/osse_spatial_block_confirmatory_blocks.csv` | Spatial-block fold assignment for the strict holdout map | year × occupied 20° × 10° block |
| `results/public/osse_spatial_block_confirmatory_paired_summary.csv` | Year- and fold-specific paired effects and seed-bootstrap intervals | year × fold × domain × budget × comparison × metric |
| `results/public/osse_spatial_block_confirmatory_consistency.csv` | Within-year cross-fold consistency | year × domain × budget × comparison × metric |
| `results/public/osse_spatial_block_confirmatory_overall.csv` | Descriptive cross-year–fold consistency | domain × budget × comparison × metric |
| `results/public/osse_spatial_block_confirmatory_design.csv` | Locked confirmatory design metadata | year × spatial fold |
| `results/public/osse_month_balance_counts.csv` | Exact selected count and share for each month | year × fold × strategy × budget × seed × month |
| `results/public/osse_month_balance_selection_summary.csv` | Per-selection month-balance diagnostics | year × fold × strategy × budget × seed |
| `results/public/osse_month_balance_strategy_summary.csv` | Portfolio-level month-balance audit | strategy × budget |
| `results/public/osse_claim_unit_effects.csv` | Absolute random/comparator values, differences and relative changes | validation scheme × year × optional fold × budget × comparison × metric |
| `results/public/osse_claim_distribution_summary.csv` | Mean, median, IQR, range and direction counts across validation units | validation scheme × budget × comparison × metric |
| `results/public/osse_truth_scale.csv` | Intrinsic pCO2 variability and seasonal-amplitude references from the locked truth fields | year plus pooled prespecified years |
| `results/public/osse_historical_month_balance_metrics.csv` | Factorized historical-spatial × uniform-month reconstruction metrics | validation scheme × year × optional fold × seed |
| `results/public/osse_historical_month_balance_selections.csv` | Exact month-quota and occupied-location audit for the factorized control | validation scheme × year × optional fold × seed |
| `results/public/osse_historical_month_balance_paired_effects.csv` | Seed-paired factorized-historical minus random effects | validation scheme × year × optional fold × seed × metric |
| `results/public/osse_historical_month_balance_unit_summary.csv` | Seed summaries for every validation unit | validation scheme × year × optional fold × metric |
| `results/public/osse_historical_month_balance_distribution_summary.csv` | Cross-unit absolute values, differences and direction counts | validation scheme × metric |
| `results/public/osse_historical_month_balance_design.csv` | Locked factorization definition, years, seeds and unit counts | one design record |
| `results/public/osse_historical_bias_map_2005.parquet` | Original and factorized historical signed-error maps with seed-direction consistency | 2005 hidden-evaluation spatial cell |
| `results/public/osse_historical_bias_density_cells_2005.parquet` | Signed-error map cells merged with the SOCAT historical spatial marginal | 2005 hidden-evaluation spatial cell |
| `results/public/osse_historical_bias_density_bins_2005.csv` | Zero-density group plus positive-density decile summaries | density group |
| `results/public/osse_historical_bias_density_summary_2005.csv` | Descriptive Spearman correlations with spatial-dependence warning | scope × response |
| `results/public/osse_historical_bias_domain_decomposition_2005.csv` | Equal-cell and spherical-area zero-coverage/latitude contribution decomposition | domain × weighting × response × coverage group |
| `results/public/osse_historical_spatial_coverage_2005.csv` | Complete mapped-domain structural-zero cell and area shares | coverage group |
| `results/public/osse_historical_area_domain_metrics.csv` | Refit random/historical metrics under equal-cell and spherical evaluation weights | validation × year × fold × seed × strategy × domain × weighting |
| `results/public/osse_historical_area_domain_unit_summary.csv` | Seed-averaged area/domain results for each validation unit | validation × year × fold × strategy × domain × weighting |
| `results/public/osse_historical_area_domain_overall.csv` | Absolute historical/random area-domain summaries | validation × strategy × domain × weighting |
| `results/public/osse_historical_area_domain_paired.csv` | Unit-level historical-minus-random area/domain effects | validation × year × fold × domain × weighting |
| `results/public/osse_historical_area_domain_paired_overall.csv` | Cross-unit historical-minus-random area/domain audit | validation × domain × weighting |
| `results/public/osse_latitude_cap_metrics.csv` | Three-strategy refits with candidates and evaluation restricted below 60°N | validation × year × fold × seed × strategy × weighting |
| `results/public/osse_latitude_cap_unit_summary.csv` | Seed-averaged latitude-cap results | validation × year × fold × strategy × weighting |
| `results/public/osse_latitude_cap_paired.csv` | Unit-level latitude-cap comparator-minus-random effects | validation × year × fold × comparison × weighting |
| `results/public/osse_latitude_cap_overall.csv` | Cross-unit aligned-domain sensitivity summary | validation × comparison × weighting |

Regional context used by the walkthrough is retained in
`spatial_sensitivity_overall_summary.csv` and
`diagnostic_interpretability_gate.csv`.

The three `osse_visual_demo_*` files are regenerated by
`scripts/export_osse_visual_demo_data.py`. They use every complete 2005
month-grid cell for the truth field and every row of the locked hidden
evaluation set for the error fields. Error maps average all 20 paired seeds;
`sign_consistent_80pct` marks spatial cells whose seed-level ΔMAE has the same
sign in at least 16/20 seeds. The 5° × 10° sampling map is an explicitly
declared spatial aggregation for representative seed 0, not a subsample.

## Draft panel mapping

- Figure 1 is a protocol schematic derived from the locked design tables and
  documented workflow; it does not encode quantitative observations.
- Figure 2 uses all rows from `osse_cross_year_metrics.csv` where
  `evaluation_domain == "all"`.
- The budget-sweep figure uses every sample count for the RMSE, p99 and median
  `spatial_coverage_minus_random` rows in
  `osse_cross_year_paired_summary.csv`.
- The spatial-weighting comparison remains a supporting audit sourced from
  `osse_regrid_audit_paired_summary.csv`; its correlated metric directions are
  not counted as independent tests.
- Evaluation-area weighting and the aligned <60°N feasibility proxy are separate
  estimands sourced from `osse_historical_area_domain_*` and
  `osse_latitude_cap_*`; neither is described as a sea-ice mask.
- The notebook spatial-block gate map uses every occupied block in
  `osse_spatial_block_confirmatory_blocks.csv`; its forest panels use all 45
  RMSE, p99 and median-error rows at sample count 5,000 from
  `osse_spatial_block_confirmatory_paired_summary.csv`.

## Statistical boundary

Seed-level uncertainty is based on 20 paired sampling seeds. Bootstrap
intervals resample those paired seed effects; model grid cells are not treated
as independent replicates. The current figures may be redesigned, but future
plots must preserve that unit of replication and the locked comparison signs.
The confirmatory spatial-block experiment uses 20 paired seeds within each of
five exhaustive spatial folds in three prespecified years. Seeds are the
within-year–fold replication unit. The 15 year–fold means are reported as a
descriptive consistency check and must not be replaced by a cell-level
significance test or treated as 15 fully independent ecological replicates.
The month-balance tables are a deterministic audit of the same acquisition
orders; they do not add model fits or a new inferential sample.
