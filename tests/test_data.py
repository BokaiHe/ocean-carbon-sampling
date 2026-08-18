from pathlib import Path

import pandas as pd

from ocean_carbon_sampling.data import read_socat_monthly, select_southern_ocean


def test_read_socat_monthly_handles_metadata_and_fill_values(tmp_path: Path) -> None:
    sample = tmp_path / "socat.csv"
    sample.write_text(
        "metadata line\n"
        "DATE, LAT, LON, COUNT_NCRUISE_YEAR, FCO2_COUNT_NOBS_YEAR, "
        "FCO2_AVE_WEIGHTED_YEAR, SST_AVE_WEIGHTED_YEAR, "
        "SALINITY_AVE_WEIGHTED_YEAR\n"
        '"2020-01-16",-40.5,10.5,1,4,380.0,5.0,-1e34\n'
        '"2019-01-16",-50.5,20.5,1,4,370.0,4.0,34.0\n',
        encoding="utf-8",
    )

    frame = read_socat_monthly(sample)

    assert pd.isna(frame.loc[0, "salinity"])
    assert frame.loc[1, "fco2"] == 370.0

    selected = select_southern_ocean(frame, year_start=2019, year_end=2019)
    assert selected["latitude"].tolist() == [-50.5]

