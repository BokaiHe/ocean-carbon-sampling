# SOCAT v2025 data audit

Source file: `SOCATv2025_tracks_gridded_monthly.csv`

Audit date: 2026-08-17

## File structure

- Compressed download: 14,363,411 bytes.
- Extracted text file: 47,998,947 bytes.
- The file begins with 242 lines of CDL-style metadata.
- The comma-separated header begins on line 243.
- The global table contains 384,729 rows and 19 columns.
- Dates span February 1970 through December 2024.

Although variable names end in `_YEAR`, the rows are monthly observations and
the `DATE` field advances by month. Internal code maps the source names to short,
stable names rather than spreading source-specific names across the project.

## Initial study subset

Filters:

- latitude south of 35 degrees S;
- years 1990–2024;
- complete weighted-mean fCO2, SST, and salinity.

Results:

- 59,835 rows before replacing fill values;
- 1,375 rows contain the salinity fill value `-1e34`;
- 58,460 complete rows remain;
- 9,658 unique 1-degree grid cells;
- 49,372 rows in 1990–2019;
- 9,088 rows in the provisional 2020–2024 temporal test period;
- zero duplicate `(date, latitude, longitude)` rows.

## Open quality-control decisions

Some technically valid rows contain unusually low salinity or extreme fCO2.
These values must not be silently removed. The next step is to map them, inspect
their observation counts and locations, and predefine any physical-domain filter
before model comparison begins.

