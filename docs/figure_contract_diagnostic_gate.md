# Figure contract: XGBoost/SHAP interpretability gate

- **Core conclusion:** Neither environmental nor location-augmented XGBoost predicts observation-level strategy benefit across unseen spatial blocks well enough to support SHAP interpretation.
- **Figure archetype:** Two-panel quantitative validation gate.
- **Target output:** GitHub portfolio and diagnostic report.
- **Backend:** Python/matplotlib only.
- **Final size:** 7.2 × 3.3 inches.
- **Panel a:** Spatial GroupKFold R² for the mean squared-error difference target.
- **Panel b:** The same validation for the mean absolute-error difference target.
- **Points:** Five geographic group folds; black marker is the pooled out-of-fold result. Overall Spearman correlation is printed below each marker.
- **Gate:** SHAP interpretation requires pooled out-of-fold R² > 0 and Spearman ≥ 0.20 for the prespecified primary target.
- **Testing:** This is a predictive validity check, not an inferential hypothesis test; no p values are used.
- **Source data:** `diagnostic_group_cv.csv` and `diagnostic_interpretability_gate.csv`.
- **Reviewer risk:** Thresholds are pragmatic interpretability safeguards, not universal statistical standards; failure means attribution is withheld, not that features have no relationship with sampling performance.
