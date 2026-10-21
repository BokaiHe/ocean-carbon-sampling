# Existing-network augmentation: 2005 pilot

Open [Network_Augmentation_2005.ipynb](Network_Augmentation_2005.ipynb), the executed English research notebook. It preserves the existing observing support, adds observations, and evaluates their incremental benefit. It does not replace the existing network with a new sampling distribution.

## Design

- Fixed baseline: **11,676** SOCAT-supported 2005 month-cells matched to the model grid; **285** observed month-cells are unmatched and excluded explicitly.
- Arms: H; H + 1,000 random additions; H + 1,000 additions at historically unobserved spatial locations.
- Historical gap: no valid SOCAT record at the 1-degree location during **1990–2005**, including all months.
- Equal added month quotas; five paired acquisition seeds; baseline fitted once; **11 fits** total.
- Common evaluation: **95,156** hidden non-H month-cells, including **49,344** in historical gaps. No evaluation cell is acquired.
- Global complete-case model domain, **without the older 60°N cutoff**. These results are not directly comparable to the old restricted-domain replacement experiment.
- Idealized pCO2 and predictors from one IPSL-CM6A-LR simulation; real SOCAT values define valid observing support only. No artificial observation noise or ship-accessibility mask.

## Observed pilot results

Area-weighted RMSE in µatm; augmented results are means across five acquisition seeds.

| Evaluation domain | Existing network H | H + random | H + gap |
|---|---:|---:|---:|
| Global unobserved | 38.791 | 36.127 | 35.665 |
| Historical-gap locations | 53.060 | 49.857 | 49.073 |
| Previously observed locations | 17.155 | 14.658 | 14.919 |

Gap additions improve global RMSE over H by **3.126 µatm**. Their additional improvement over equal-count random additions is **0.462 µatm**, with an observed seed range of **0.241–0.732 µatm** (5/5 seeds positive). In historical gaps that targeting advantage is **0.783 µatm**. At previously observed locations random additions are better by **0.260 µatm**, although both augmented arms improve over H there.

MAE follows the same targeting tradeoff. All results are retained; no strategy or domain was selected based on the outcome. Five seed outcomes describe acquisition randomness, not independent ocean realizations or statistical significance.

## Domain-matched reruns (2026-10-21)

The pilot above is global and has no ocean mask. The headline replacement study
was later restricted to latitude < 60°N and to a connected-ocean mask (M1), with
an open-ocean-interior sensitivity mask (M2; also excludes the Mediterranean and
Black Sea, Baltic, Hudson Bay and land-adjacent cells). See
`docs/osse_ocean_mask_protocol.md`. Both masks were rerun here with the same
seeds and settings; each took under a minute.

**These reruns are post hoc.** They were decided after the global result above
was known, to match the headline study's domain; no protocol was frozen for
them beforehand. All three runs are kept and reported. The website and the main
README use M2, chosen as the open-ocean view after seeing that the M1 advantage
was dominated by Hudson Bay.

| Run | Config | Baseline H | Evaluation cells |
|---|---|---:|---:|
| Global pilot (above) | `config.json` → `results/` | 11,676 | 95,156 |
| M1, < 60°N | `config_m1_lt60.json` → `results_m1_lt60/` | 11,000 | 84,453 |
| M2, < 60°N | `config_m2_lt60.json` → `results_m2_lt60/` | 9,671 | 77,474 |

H + random minus H + gap (positive favours gap targeting), area-weighted, µatm,
mean of five seeds [min, max] and seeds positive:

| Domain | Metric | Global pilot | M1, < 60°N | M2, < 60°N |
|---|---|---|---|---|
| All unobserved | RMSE | +0.462 [0.24, 0.73] 5/5 | +1.321 [0.66, 3.03] 5/5 | +0.128 [0.00, 0.23] 5/5 |
| All unobserved | MAE | +0.274 [0.02, 0.53] 5/5 | +0.079 [−0.42, 0.59] 3/5 | +0.090 [0.04, 0.14] 5/5 |
| Historical gaps | MAE | +0.780 5/5 | +0.487 4/5 | +0.410 5/5 |
| Previously observed | MAE | −0.193 0/5 | −0.280 1/5 | −0.173 0/5 |

Both augmented arms improve on H by roughly 2–3 µatm in every run. The M1 RMSE
targeting advantage is dominated by Hudson Bay: about 80% of the area-weighted
squared-error reduction comes from Hudson Bay cells below 60°N, which are under
1% of evaluation area. In the open-ocean interior (M2) gap targeting still beats
random in all five seeds, but by about 0.1 µatm globally; it helps in historical
gaps (+0.4 µatm MAE) and costs at previously observed locations (−0.2 µatm).

`audit_results.py <results-dir>` re-derives every metric and paired effect from
the saved predictions for any run.

## Contents and safe execution

- `PROTOCOL.md` and `config.json`: evaluation and settings written before the global fit.
- `config_m1_lt60.json`, `config_m2_lt60.json`: the post hoc domain-matched reruns (latitude cap and ocean mask from `results/public/osse_ocean_mask_cells.csv`).
- `augmentation.py`: the experiment runner (`--config`, `--results`), using the original project's loader, features and model factory; it refuses to overwrite any started run.
- `test_augmentation.py`: design integrity and numerical metric tests.
- `results/`, `results_m1_lt60/`, `results_m2_lt60/`: design masks, acquisitions, all evaluation predictions, metrics and paired effects for each run.
- `build_notebook.py`: rebuilds the notebook and three figure pairs **without model fitting** (global run only).
- `audit_results.py [results-dir]`: re-derives every metric and paired effect from the saved predictions.

From this study directory, using the project's Python environment:

```text
python -m unittest -v test_augmentation.py
python audit_results.py results
python audit_results.py results_m2_lt60
python build_notebook.py
```

For a new run, use a separate study directory and freeze its protocol before fitting. The explicit runner is `python augmentation.py --project-root <original-project-root>`; do not delete the existing receipts to force a rerun.

## Interpretation

This pilot supports the value of filling observational gaps under one fixed simulation and learner, with a regional tradeoff. It does not establish global deployment optimality, equal operational cost, independent real-observation accuracy, or generality across years and ESMs. Adding points in a simulated gap is not proof that a ship or float can operate there. More years and added counts belong in a separately frozen extension.

The study code, saved outputs and tests are now included in the public project
repository. This is a research pilot, not a peer-reviewed publication.
