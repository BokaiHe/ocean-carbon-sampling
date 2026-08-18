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

## Do not download yet: global OSSE

Global model data will be selected only after the regional benchmark passes its validation gates. The provisional CMIP6 monthly surface variables are:

- `spco2` — surface ocean partial pressure of CO2;
- `tos` — sea surface temperature;
- `sos` — sea surface salinity;
- `mlotst` — mixed-layer depth;
- `chl` — chlorophyll concentration.

The first OSSE will use one ESM, one member, a limited time window, and a common 1-degree monthly grid. Do not bulk-download multiple ESMs or ensemble members in advance.

## Commit policy

Only a small, documented, redistribution-compatible sample may be placed in `data/demo/` and committed. Raw SOCAT and CMIP6 files must remain local or in external archival storage.

