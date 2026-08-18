import pandas as pd

from ocean_carbon_sampling.splits import add_spatial_folds, add_validation_regimes


def test_validation_regimes_do_not_mix_future_and_spatial_tests() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2019-01-01", "2020-01-01"]),
            "latitude": [-45.0, -45.0],
            "longitude": [10.0, 10.0],
        }
    )
    assigned = add_validation_regimes(add_spatial_folds(frame))

    assert assigned.loc[1, "temporal_split"] == "test"
    assert assigned.loc[1, "spatial_split"] == "not_used"


def test_five_spatial_holdouts_partition_each_pretest_row_once() -> None:
    frame = pd.DataFrame(
        {
            "date": pd.to_datetime(["2019-01-01"] * 5),
            "latitude": [-45.0, -55.0, -65.0, -45.0, -55.0],
            "longitude": [-170.0, -90.0, 0.0, 80.0, 170.0],
        }
    )
    blocked = add_spatial_folds(frame)
    test_counts = pd.Series(0, index=blocked.index)
    for fold in range(5):
        assigned = add_validation_regimes(blocked, spatial_test_fold=fold)
        test_counts += (assigned["spatial_split"] == "test").astype(int)

    assert (test_counts == 1).all()
