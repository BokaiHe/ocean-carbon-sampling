# One-year OSSE execution-gate results

## Scope

This is a pipeline gate, not the prespecified final OSSE. It compares three
sampling strategies at budgets of 500 and 1,000 using seeds 0–2. Every model is
evaluated on the same 97,488 month-grid cells selected once without using
`spco2`. The repeat unit for strategy variability is the sampling seed (`n = 3`),
not the number of evaluation cells. No p values or confirmatory intervals are
reported at this stage.

## Primary all-value result

At budget 500, mean RMSE was 31.98 micro-atmospheres for random, 32.23 for
spatial coverage and 41.73 for historical density. At budget 1,000, mean RMSE
was 29.46 for random, 29.16 for spatial coverage and 37.88 for historical
density.

Historical-density sampling was therefore worse than both alternatives in all
six seed-budget runs. It also occupied fewer spatial and month-blocks, consistent
with repeated sampling of historically favoured regions. This is descriptive
evidence from the execution gate, not yet a general claim across years or Earth
system models.

Random and spatial-coverage sampling were not stably ordered. Random had lower
mean RMSE at budget 500, whereas spatial coverage had lower mean RMSE at budget
1,000. The absolute differences were small relative to the across-seed
variability, and MAE did not give the same ordering at budget 1,000.

## Frozen extreme-tail sensitivity

The input audit, completed before strategy comparison, identified a small
`spco2` upper tail and froze a 1,000 micro-atmosphere diagnostic threshold. When
evaluation values above that threshold were excluded, random had slightly lower
mean RMSE than spatial coverage at both budgets: 26.04 versus 26.44 at 500, and
23.04 versus 23.19 at 1,000. Historical density remained clearly worse.

The apparent spatial-coverage advantage for all-value RMSE at budget 1,000 is
therefore sensitive to the extreme tail. This sensitivity analysis is not an
open-ocean analysis and does not justify deleting the extreme values.

## Decision

The execution chain passes: all strategies use equal nested budgets, the common
evaluation set is fixed, sampling does not inspect model truth, and metrics are
reproducible. The next analysis should expand to 20 paired seeds and all four
budgets, while retaining both all-value and extreme-tail-sensitivity endpoints.
No figure or headline claim should be frozen from the three-seed gate alone.
