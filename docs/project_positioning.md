# Project positioning, attribution and evaluation scope

Presentation revision: 2026-09-23. This revision uses existing result tables.
No observations, sampling rules, model fits or numerical results were changed.

## One research question and one storyline

At a fixed number of selected month-cells, how do random, historical-density
and seasonally aware coverage rules affect monthly pCO2 reconstruction error
under a specified model and evaluation domain?

1. Quantify the error cost of historical-density allocation, not a surprising
   discovery that real-world sampling is uneven.
2. Test whether broader coverage solves that problem. It does not improve all
   error measures; the response depends on sample count and evaluation.
3. Motivate a future experiment on where to add observations to an existing
   network. The current replacement-design comparison does not answer it.

## Primary comparison and stress test

Both headline comparisons use 5,000 samples, spherical cell-area weighting,
and candidate and evaluation domains restricted to latitude <60°N.
This latitude cutoff is a domain restriction, not proof of physical access
and not a sea-ice mask.

| Evaluation | Random MAE | Historical-density MAE | Difference | Relative change | Consistency |
|---|---:|---:|---:|---:|---|
| Primary: scattered hidden cells | 9.508 | 11.975 | +2.466 | +25.94% | 3/3 year means worse |
| Stress test: whole blocks | 11.836 | 13.691 | +1.855 | +15.67% | 15/15 year-fold means worse |

MAE is in µatm. Differences and percentages are computed before rounding,
so subtraction of displayed values can differ by 0.001 µatm. Source:
[`osse_latitude_cap_overall.csv`](../results/public/osse_latitude_cap_overall.csv).
Year-level and year-fold effects are in
[`osse_latitude_cap_paired.csv`](../results/public/osse_latitude_cap_paired.csv).

The primary protocol reserves approximately 20% of the month-cells in each
month before sampling. One fixed evaluation set per year is shared by all
strategies and 20 paired seeds. This is reconstruction at dispersed missing
month-cells, not full-field evaluation after unrestricted sampling. A location
can have another month in training; this is allowed by this reconstruction
question, not a test of transfer to wholly unseen locations.

The stress test excludes every month in each held-out 20° longitude × 10°
latitude block before sampling. Five deterministic checkerboard folds cover
the domain, without a buffer. It measures reconstruction in wholly unobserved
blocks, not buffered long-range extrapolation. Each year-fold mean averages
20 paired seeds. The three years share one ESM run; neither 3/3 nor 15/15 is
an independent-replicate significance test.

The four-step signed-bias history remains a **whole-block** sensitivity audit:
−4.954 (full-domain/equal-cell), −1.884 (full-domain/area), −0.631
(evaluation <60°N/area), −0.473 µatm (both domains <60°N/area).
The last value is not the primary hidden-cell bias difference (−0.835 µatm).
This presentation choice is a post-analysis reframing, not a newly
preregistered protocol. Older notebooks, experimental configs and audit
documents retain their original scopes and whole-block default terminology;
the current README and website explicitly distinguish the two evaluations.

## Design boundaries

- **Idealized data.** Monthly model-grid targets have no added measurement or
  representation error; SST and salinity come from the same simulation.
  Absolute errors and rankings are not validated for noisy real observations.
- **Fixed learner.** HistGradientBoosting uses the same locked hyperparameters
  across counts and strategies. Sample-count effects are conditional on this
  learner, not isolated causal effects of sampling geometry.
- **Limited features and truth.** One IPSL-CM6A-LR member supplies truth.
  Predictors are SST, salinity, latitude, cyclic longitude, year and cyclic
  month. MLD, chlorophyll and atmospheric CO2 are absent. No ablation establishes
  which predictors dominate. Cross-learner and cross-ESM generality is untested.
- **Separate yearly fits.** All 12 months of each of 2005, 2010 and 2014 are
  fitted jointly, but each year has its own model. The year feature is constant
  within a fit. Continuous interannual variability and trends are not evaluated.
- **Density, not trajectories.** Historical-density uses SOCAT 1990–2004
  month-location count weights for sampling without replacement. It does not
  replay cruises, repeat lines or platform accessibility. It is not a lower
  bound on the error of the real SOCAT network.

## Related work and the difference here

Gloege et al. established the Large Ensemble Testbed approach to evaluate
reconstructions against model truth, with multiple ESMs and seasonal-to-decadal
skill. This project adopts the controlled-truth idea, not their temporal
scope or ensemble breadth.

Heimdal et al. evaluated additional Southern Ocean autonomous observations
on top of SOCAT, with pCO2-Residual, multiple ESMs and full-field evaluation.
Here, fixed-count density/coverage rules replace one another, with direct-pCO2
prediction and two held-out evaluations. This is not a replication, a superior
method claim, or an estimate of their platform or flux benefits.

References verified against Crossref DOI metadata and article text on
2026-09-23. Two verified; no mismatches. The academic-search MCP was unavailable,
so DOI records were queried directly. Article sources establish the method
comparisons; metadata alone does not establish those claims.

- Gloege, L., et al. (2021). *Quantifying Errors in Observationally Based
  Estimates of Ocean Carbon Sink Variability*. Global Biogeochemical Cycles,
  35, e2020GB006788. https://doi.org/10.1029/2020GB006788
  ([article text](https://www.vliz.be/imisdocs/publications/381488.pdf), Fig. 1 and §2).
- Heimdal, T. H., McKinley, G. A., Sutton, A. J., Fay, A. R., & Gloege, L.
  (2024). *Assessing improvements in global ocean pCO2 machine learning
  reconstructions with Southern Ocean autonomous sampling*. Biogeosciences,
  21, 2159–2176. https://doi.org/10.5194/bg-21-2159-2024
  ([article text](https://bg.copernicus.org/articles/21/2159/2024/), §§2.1–2.4).

## Course foundation and contribution boundaries

This is an independent extension of the Spring 2025 EESC/STAT 4243 course
project in Galen A. McKinley's class. The author confirmed the course
relationship on 2026-09-23. It is not a claim that she supervised or endorsed
all subsequent independent work.

The original team was Azam Khan, Bokai He, Sarah Pariser and Zhi Wang.
Its [public contribution statement](https://github.com/spariser/ReconstructOceanCarbonP3G1)
credits Bokai He with statistical significance analysis and NGBoost/XGBoost
comparison. Other contributors developed the training/visualization pipeline,
sampling masks and narrative, and seasonality analysis. The original
collaborative work is not attributed solely to Bokai He. Those course-level
statistical tests are not evidence of formal significance in the present OSSE.

The current repository separately develops the fixed-count comparison,
evaluation audits and interactive brief. Credit for the course foundation,
published methodology and new implementation is kept distinct.

## Stop rule

No new experiment is required for this presentation revision. The only
optional next experiment discussed here is a protocol-frozen reconstruction
sampled from the complete candidate domain, with explicit full-field and
unobserved-cell scoring. It would require new sampling and fitting. Real SOCAT
masks, new predictors, tuning and multiple ESMs are separate extensions, not
silent changes to this comparison.
