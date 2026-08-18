# Data directory

Raw and derived data are deliberately excluded from Git. Keep the following local layout:

```text
data/
├── raw/
│   ├── socat/
│   └── cmip6/
├── interim/
├── processed/
└── demo/
```

## Download now: regional minimum experiment

Download **SOCAT version 2025, monthly 1-degree gridded CSV** from the official SOCAT release page:

- Release and download links: https://socat.info/index.php/version-2025/
- Dataset DOI: https://doi.org/10.25921/648f-fv35

Prefer the compressed CSV mirror (approximately 14 MB) rather than the multi-gigabyte NetCDF file. Read and follow the SOCAT data-use statement.

Place the extracted monthly CSV under:

```text
data/raw/socat/
```

Do not rename the downloaded file until its exact filename and columns have been recorded in a data manifest.

The minimum experiment uses the Southern Ocean subset (`latitude < -35`) and initially requires only:

- time/year/month;
- latitude and longitude;
- weighted mean fCO2;
- weighted mean SST;
- weighted mean salinity;
- observation or cruise counts when available.

## Download next: global OSSE pilot

The regional experiment is now frozen and the first global OSSE pilot uses one
verified CMIP6 historical realization:

- model: `IPSL-CM6A-LR`;
- member: `r1i1p1f1`;
- table/grid: `Omon/gn`;
- source files: 1850–2014 monthly output;
- pilot analysis window: 2005–2014.

Download the first three files listed in `data/cmip6_osse_pilot_manifest.csv`
into:

```text
data/raw/cmip6/IPSL-CM6A-LR/historical/r1i1p1f1/Omon/gn/
```

Preview the exact URLs, sizes and destination paths with:

```bash
python scripts/download_osse_pilot.py --dry-run
```

The three required variables are:

- `spco2` — surface ocean partial pressure of CO2;
- `tos` — sea surface temperature;
- `sos` — sea surface salinity;

The full source files total approximately 1.10 GB. The code will subset the last
10 years after download; the raw files are retained unchanged for provenance.

Do not download the optional second-stage variables yet:

- `mlotst` — mixed-layer depth;
- `chl` — chlorophyll concentration.

Do not bulk-download other models or ensemble members before the pilot closes.

## Commit policy

Only a small, documented, redistribution-compatible sample may be placed in `data/demo/` and committed. Raw SOCAT and CMIP6 files must remain local or in external archival storage.
