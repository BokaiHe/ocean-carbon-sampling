"""Export observed SOCAT monthly fCO2, separate from simulated truth and errors."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

import numpy as np

from ocean_carbon_sampling.data import read_socat_monthly

YEARS = (2005, 2010, 2014)


def export(source: Path, destination: Path) -> dict:
    frame = read_socat_monthly(source)
    frame = frame.loc[frame.date.dt.year.isin(YEARS)].copy()
    valid = np.isfinite(frame.fco2) & (frame.fco2_count > 0)
    excluded = int((~valid).sum())
    frame = frame.loc[valid].sort_values(["date", "latitude", "longitude"])
    if frame.duplicated(["date", "latitude", "longitude"]).any():
        raise ValueError("Duplicate monthly grid cells")
    records = {}
    for year in YEARS:
        part = frame.loc[frame.date.dt.year == year]
        rows = [
            [
                int(row.date.month),
                float(row.longitude),
                float(row.latitude),
                float(row.fco2),
                int(row.fco2_count),
                int(row.cruise_count),
            ]
            for row in part.itertuples(index=False)
        ]
        records[str(year)] = rows
    data = {
        "metadata": {
            "source": source.name,
            "source_sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "doi": "https://doi.org/10.25921/648f-fv35",
            "release": "SOCAT v2025",
            "source_page": "https://socat.info/index.php/version-2025/",
            "data_use": "https://socat.info/wp-content/uploads/2025/06/SOCATv2025_DataUseStatement.pdf",
            "methods": [
                "https://doi.org/10.5194/essd-8-383-2016",
                "https://doi.org/10.5194/essd-5-145-2013",
            ],
            "quantity": "Surface-water CO2 fugacity (fCO2)",
            "units": "µatm",
            "field": "FCO2_AVE_WEIGHTED_YEAR",
            "resolution": "1 degree latitude x 1 degree longitude, monthly",
            "columns": [
                "month",
                "longitude",
                "latitude",
                "fco2",
                "observation_count",
                "cruise_count",
            ],
            "years": list(YEARS),
            "default_year": 2014,
            "monthly_mean": "SOCAT per-cruise-weighted monthly grid mean, retained at source precision.",
            "all_months": "Arithmetic mean of available monthly grid means within each location and selected year. Months weighted equally; not a complete annual mean or observation-weighted mean.",
            "colour_domain": [200, 600],
            "colour_clipping": "Only colours saturate outside 200–600 µatm. No finite measured values are clipped or discarded.",
            "excluded_missing_or_unobserved_rows": excluded,
            "purpose": "Observation context only. Not individual ship positions, not model truth or errors, not a flux or concentration map. No new model fitting.",
            "acknowledgement": "We thank the SOCAT data providers, researchers, funding agencies, data managers and quality controllers. SOCAT is an international effort endorsed by IOCCP and SOLAS.",
        },
        "years": records,
    }
    destination.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return data


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--source",
        type=Path,
        default=root / "data/raw/socat/SOCATv2025_tracks_gridded_monthly.csv",
    )
    parser.add_argument(
        "--output", type=Path, default=root / "site/data/observed-co2.json"
    )
    args = parser.parse_args()
    result = export(args.source, args.output)
    print({year: len(rows) for year, rows in result["years"].items()})
