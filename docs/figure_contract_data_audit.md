# Figure contract: SOCAT coverage audit

- **Core conclusion:** SOCAT observations are uneven across Southern Ocean space, years, and months; independent temporal and spatial validation are therefore required.
- **Figure archetype:** Quantitative grid with a dominant spatial-coverage panel.
- **Target output:** GitHub README and research report.
- **Backend:** Python/matplotlib only.
- **Final size:** 7.2 × 6.4 inches.
- **Panel a:** Log-scaled observation-row coverage on a 2-degree grid.
- **Panel b:** Annual coverage with the provisional 2020–2024 temporal test period identified.
- **Panel c:** Monthly coverage showing seasonal imbalance.
- **Hero evidence:** Spatial coverage map.
- **Validation evidence:** Annual and monthly coverage counts.
- **Statistics:** Complete-case row counts only; no inferential test.
- **Integrity:** Only documented `-1e34`-style fill values are excluded. Extreme physical values are flagged for review and are not silently removed.
- **Reviewer risk:** A gridded row is not equivalent to an independent cruise or measurement; labels and captions must retain that distinction.

