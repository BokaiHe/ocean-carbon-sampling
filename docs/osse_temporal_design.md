# Temporal design and monthly balance

## Estimand

The project estimates how a fixed annual observation budget should be allocated
to reconstruct a global monthly fCO2 field. It does not estimate future-month
forecast skill.

Each candidate observation is a month–latitude–longitude record. All 12 months
are fitted jointly in one model, using cyclic `month_sin` and `month_cos`
features so that December and January remain adjacent in feature space.

## Why the random hidden set is stratified by month

The seasonal carbon cycle can be large. An unstratified hidden set could contain
different month proportions by chance, making an apparent strategy difference
partly a difference in seasonal test composition. The month-stratified hidden
set holds out the same fraction within every month and therefore keeps the
evaluation question focused on sampling allocation.

The stricter spatial-block experiment uses a different protection: every month
at one geographic location belongs to the same fold. The model cannot train on
one month at a location and be evaluated on another month at that location.

## Why a chronological split is not the primary test

Training on earlier months or years and testing later ones would evaluate
forecasting under temporal distribution shift. That is scientifically valid,
but it combines sampling allocation with seasonal extrapolation and long-term
change. It answers a different question from reconstruction under a fixed
annual observing programme and is outside the current scope.

## Month-balance audit

The audit reconstructs the exact acquisition orders used by the three-year,
five-fold, 20-seed confirmatory experiment without fitting additional models.
It contains 1,800 selections: three strategies × two budgets × 20 seeds × five
folds × three years.

All 1,800 selections cover all 12 months. At budget 5,000:

| Strategy | Mean absolute deviation from equal monthly share | Mean maximum deviation | Maximum observed deviation |
| --- | ---: | ---: | ---: |
| Random | 0.292 percentage points | 0.754 percentage points | 1.033 percentage points |
| Spatial coverage | 0.222 percentage points | 0.532 percentage points | 0.947 percentage points |
| Historical density | 0.875 percentage points | 2.506 percentage points | 3.667 percentage points |

Random and spatial-coverage sampling are therefore closely seasonally balanced;
their performance difference primarily reflects where observations are placed.
Historical-density sampling intentionally reproduces both the spatial and
seasonal structure of the historical observing pattern. It is a realistic
spatiotemporal baseline, not a pure spatial control.

## Defensible terminology

- `spatial_coverage` remains the implementation name.
- In prose, it is described as **seasonally balanced spatial coverage**.
- The historical-density comparator is described as a **historical
  spatiotemporal observing-pattern baseline**.
- Results are claims about reconstruction, not chronological forecasting.
