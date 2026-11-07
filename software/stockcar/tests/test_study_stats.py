import unittest

from stockcar import study_stats


class StudyStatsTests(unittest.TestCase):
    def test_wilson_is_bounded_and_handles_zero_runs(self):
        self.assertIsNone(study_stats.wilson(0, 0))
        self.assertEqual(study_stats.wilson(0, 20)[0], 0.0)
        self.assertEqual(study_stats.wilson(20, 20)[1], 1.0)
        with self.assertRaises(ValueError):
            study_stats.wilson(2, 1)

    def test_midranks_assign_average_ranks_to_ties(self):
        self.assertEqual(study_stats.midranks([10, 20, 10, 30]), [0.5, 2.0, 0.5, 3.0])

    def test_spearman_uses_ties_and_is_row_order_invariant(self):
        xs = [0, 0, 1, 1, 2, 2]
        ys = [0, 0, 1, 1, 2, 2]
        self.assertAlmostEqual(study_stats.spearman(xs, ys), 1.0)
        self.assertAlmostEqual(study_stats.spearman(xs, list(reversed(ys))), -1.0)
        tied = study_stats.spearman([0, 0, 1, 1], [0, 1, 0, 1])
        self.assertAlmostEqual(study_stats.spearman([1, 0, 0, 1], [0, 1, 0, 1]), tied)
        self.assertIsNone(study_stats.spearman([1, 1], [1, 2]))
        self.assertIsNone(study_stats.spearman([1], [1]))

    def test_quantile_interpolates(self):
        self.assertEqual(study_stats.quantile([0, 10, 20, 30], 0.5), 15)
        self.assertEqual(study_stats.quantile([0, 10, 20, 30], 0.25), 7.5)
        self.assertIsNone(study_stats.quantile([], 0.5))

    def test_clustered_permutation_is_deterministic_and_bounded(self):
        # Two scenarios per pose/seed cluster; the baseline y is deliberately repeated within a cluster.
        clusters = [(pose, seed) for pose in ("true", "ekf") for seed in range(4) for _ in range(2)]
        strata = [pose for pose, _seed in clusters]
        xs = [i % 2 for i in range(len(clusters))]
        ys = [float(seed < 2) for pose, seed in clusters]
        corr = study_stats.spearman(xs, ys)
        args = (xs, ys, corr, clusters, strata)
        a = study_stats.clustered_permutation_p(*args, shuffles=40, seed=7)
        b = study_stats.clustered_permutation_p(*args, shuffles=40, seed=7)
        self.assertEqual(a, b)
        self.assertGreaterEqual(a, 1 / 41)
        self.assertLessEqual(a, 1.0)
        self.assertIsNone(study_stats.clustered_permutation_p(xs, ys, None, clusters, strata))

    def test_clustered_permutation_rejects_invalid_clusters(self):
        with self.assertRaises(ValueError):
            study_stats.clustered_permutation_p([0, 1], [0, 1], 1.0, ["a", "a"], ["s", "s"])
        with self.assertRaises(ValueError):
            study_stats.clustered_permutation_p([0, 1], [0, 1], 1.0, ["a", "b"], ["s", "s"], shuffles=0)
        with self.assertRaises(ValueError):
            study_stats.clustered_permutation_p([0, 1], [0, 1], 1.0, ["a", "a"], ["s", "t"])


if __name__ == "__main__":
    unittest.main()
