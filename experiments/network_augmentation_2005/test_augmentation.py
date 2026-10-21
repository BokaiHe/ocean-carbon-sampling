"""Design integrity tests, including observations that must remain untouched."""
import unittest
import numpy as np
import pandas as pd
from augmentation import network_masks, reserve_evaluation, select_additions, metrics


class AugmentationTests(unittest.TestCase):
    def test_baseline_gap_and_unmatched_support(self):
        frame = pd.DataFrame({"month": [1, 2, 1, 1], "latitude": [0.5, .5, 1.5, 2.5], "longitude": [.5] * 4})
        socat = pd.DataFrame({"date": pd.to_datetime(["2005-01-01", "2004-03-01", "2005-01-01", "2006-01-01"]),
                              "latitude": [.5, 1.5, 8.5, 2.5], "longitude": [.5]*4,
                              "fco2_count": [1]*4, "fco2": [400.]*4})
        h, gap, report = network_masks(frame, socat, 2005, 1990, 2005)
        np.testing.assert_array_equal(h, [True, False, False, False])
        np.testing.assert_array_equal(gap, [False, False, False, True])
        self.assertEqual(report["unmatched_socat_month_cells"], 1)
        changed = socat.copy()
        changed.fco2 += 900
        np.testing.assert_array_equal(network_masks(frame, changed, 2005, 1990, 2005)[0], h)

    def test_common_baseline_test_exclusion_and_equal_quotas(self):
        months = np.repeat(np.arange(1, 13), 100)
        h = np.zeros(1200, bool)
        h[np.arange(0, 1200, 100)] = True
        gap = np.tile(np.arange(100) >= 50, 12)
        test, inverse = reserve_evaluation(months, h, gap, .2, 7)
        self.assertFalse((test & h).any())
        self.assertTrue((inverse[test] > 0).all())
        for seed in range(5):
            selections = [select_additions(months, h, test, gap, 125, seed, targeted) for targeted in [False, True]]
            for ids in selections:
                self.assertEqual(len(np.unique(ids)), 125)
                self.assertFalse((h[ids] | test[ids]).any())
                self.assertEqual(len(np.union1d(np.flatnonzero(h), ids)), int(h.sum())+125)
            self.assertTrue(gap[selections[1]].all())
            np.testing.assert_array_equal(np.bincount(months[selections[0]]), np.bincount(months[selections[1]]))
            np.testing.assert_array_equal(selections[0], select_additions(months, h, test, gap, 125, seed, False))
        with self.assertRaises(ValueError):
            select_additions(months, h, test, gap, 10000, 0, True)

    def test_weighted_metrics_known_values(self):
        result = metrics(np.array([0., 0.]), np.array([-2., 4.]), np.array([3., 1.]))
        self.assertAlmostEqual(result["mae"], 2.5)
        self.assertAlmostEqual(result["bias"], -.5)
        self.assertAlmostEqual(result["rmse"], np.sqrt(7))


if __name__ == "__main__":
    unittest.main()
