# Figure contract: repeated-seed benchmark

- **Core conclusion:** Across 20 prespecified seeds, coverage sampling improves mean locked-test RMSE and geographic balance in both validation regimes, while several negative seed-level effects remain visible.
- **Figure archetype:** Two-panel quantitative robustness grid.
- **Target output:** GitHub portfolio and research report.
- **Backend:** Python/matplotlib only.
- **Final size:** 7.2 × 3.4 inches.
- **Panel a:** All seed-level paired RMSE gains plus mean and 95% seed-bootstrap interval.
- **Panel b:** All seed-level reductions in coverage-cell count CV plus mean and 95% seed-bootstrap interval.
- **Independent unit:** One complete paired sampling run per prespecified seed; n = 20 seeds per validation regime.
- **Interval:** Two-sided percentile bootstrap interval for the seed-level mean, 10,000 resamples.
- **Testing:** No p values and no significance stars.
- **Source data:** `benchmark_paired_effects.csv` and `benchmark_summary.csv`.
- **Reviewer risk:** Seed-bootstrap intervals capture sampling-algorithm variability only, not uncertainty across spatial test definitions, observations, or models.
