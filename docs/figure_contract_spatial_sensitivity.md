# Figure contract: five-fold spatial sensitivity

- **Core conclusion:** Coverage reliably improves geographic balance, but its predictive effect varies across held-out spatial regions and reverses for fold 4.
- **Figure archetype:** Asymmetric quantitative robustness figure with validation geometry.
- **Target output:** GitHub portfolio and regional benchmark report.
- **Backend:** Python/matplotlib only.
- **Final size:** 7.2 × 3.6 inches.
- **Panel a:** All 20 seed-level RMSE gains for each of five folds, with fold mean and 95% seed-bootstrap interval.
- **Panel b:** Occupied pre-2020 20° × 10° blocks colored by deterministic test fold.
- **Independent unit:** One sampling seed within a fixed fold for fold-specific intervals; fold means are the units of cross-fold sensitivity.
- **Testing:** No p values, significance stars, seed exclusions, or selected folds.
- **Source data:** `spatial_sensitivity_paired_effects.csv`, `spatial_sensitivity_fold_summary.csv`, and `spatial_fold_blocks.csv`.
- **Reviewer risk:** The five folds exhaust this checkerboard assignment but do not cover alternative block sizes, temporal definitions, models, or unobserved ocean locations.
