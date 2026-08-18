# OSSE figure-data inventory

## Status

The current composite figures are visual drafts. Their source data remain the
authoritative inputs for later redrawing; no values need to be recovered from
PNG, PDF, or SVG files.

## Retained redraw inputs

| File | Role | Granularity |
| --- | --- | --- |
| `results/public/osse_cross_year_metrics.csv` | Learning curves and absolute performance | year × domain × strategy × budget × seed |
| `results/public/osse_cross_year_paired_summary.csv` | Fixed-budget paired effects and bootstrap intervals | year × domain × budget × comparison × metric |
| `results/public/osse_regrid_audit_paired_summary.csv` | Equal-bin versus native-cell-area robustness | regrid method × year × domain × budget × comparison × metric |
| `results/public/osse_cross_year_design.csv` | Locked cross-year design metadata | design record |
| `results/public/osse_cross_year_versions.csv` | Runtime and package provenance | software component |
| `results/public/osse_regrid_audit_design.csv` | Regridding-audit design metadata | design record |
| `results/public/osse_regrid_audit_versions.csv` | Regridding-audit runtime provenance | software component |

Regional context used by the walkthrough is retained in
`spatial_sensitivity_overall_summary.csv` and
`diagnostic_interpretability_gate.csv`.

## Draft panel mapping

- Figure 1 is a protocol schematic derived from the locked design tables and
  documented workflow; it does not encode quantitative observations.
- Figure 2 uses all rows from `osse_cross_year_metrics.csv` where
  `evaluation_domain == "all"`.
- Figure 3a–c uses the 5,000-observation,
  `spatial_coverage_minus_random` rows from
  `osse_cross_year_paired_summary.csv`.
- Figure 3d uses the 12 prespecified stability checks from
  `osse_regrid_audit_paired_summary.csv`.

## Statistical boundary

Seed-level uncertainty is based on 20 paired sampling seeds. Bootstrap
intervals resample those paired seed effects; model grid cells are not treated
as independent replicates. The current figures may be redesigned, but future
plots must preserve that unit of replication and the locked comparison signs.
