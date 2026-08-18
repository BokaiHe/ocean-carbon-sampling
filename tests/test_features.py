import numpy as np
import pandas as pd

from ocean_carbon_sampling.features import FEATURE_COLUMNS, build_features


def test_features_are_cyclic_and_exclude_target() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2000-01-15", "2000-12-15"]),
            "latitude": [-50.0, -50.0],
            "longitude": [-180.0, 180.0],
            "sst": [2.0, 2.0],
            "salinity": [34.0, 34.0],
            "fco2": [350.0, 900.0],
        }
    )
    features = build_features(frame)

    assert list(features) == FEATURE_COLUMNS
    assert "fco2" not in features
    assert np.isclose(features.loc[0, "longitude_sin"], features.loc[1, "longitude_sin"])
    assert np.isclose(features.loc[0, "longitude_cos"], features.loc[1, "longitude_cos"])
