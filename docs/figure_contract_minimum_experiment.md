# Figure contract: minimum sampling experiment

- **Core conclusion:** At the 20% budget, coverage sampling lowers locked-test RMSE relative to random sampling in both transfer regimes for the single preregistered seed; robustness remains untested.
- **Figure archetype:** Two-panel quantitative comparison grid.
- **Target output:** GitHub portfolio, project report, and later web-app summary.
- **Backend:** Python/matplotlib only.
- **Final size:** 7.2 × 3.2 inches.
- **Panel a:** Temporal-holdout RMSE versus training budget.
- **Panel b:** Spatial-block-holdout RMSE versus training budget.
- **Primary metric:** RMSE in µatm; MAE and signed mean bias remain in source data.
- **Comparability:** Strategies share the initial sample, candidate pool, budget, features, model, and locked test set within each regime.
- **Uncertainty boundary:** This first run uses one preregistered seed, so the figure contains no inferential error bars and cannot establish robustness.
- **Integrity:** Complete-case exclusion is recorded before fitting. Test outcomes are unavailable to acquisition.
- **Reviewer risk:** SOCAT is an observational archive with uneven support; performance on observed held-out rows is not equivalent to performance over the entire Southern Ocean.
