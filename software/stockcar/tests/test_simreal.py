import csv
import json
import pathlib
import tempfile
import unittest

from stockcar import simreal

ROOT = pathlib.Path(__file__).resolve().parents[3]


class SimrealSourceTests(unittest.TestCase):
    def test_all_six_immutable_world_seals_validate(self):
        sources = simreal.load_world_sources(ROOT)
        self.assertEqual([s["world"] for s in sources], list(simreal.WORLDS))
        self.assertEqual(sum(len(s["report"]["results"]) for s in sources), 18)
        for source in sources:
            self.assertRegex(source["source_commit"], r"^[0-9a-f]{40}$")
            self.assertEqual(len(source["source_report_sha256"]), 64)


class SimrealDrawTests(unittest.TestCase):
    def test_draws_are_deterministic_and_ordered(self):
        args = (17, 20, [5.0, 20.0], [1.0, 4.0], {"drift_mm": 25.0, "spin_deg": 5.0})
        a = simreal.expected_draws(*args, n_draws=200, seed=9)
        self.assertEqual(a, simreal.expected_draws(*args, n_draws=200, seed=9))
        self.assertEqual(len(a), 200)
        summary = simreal.summarize(a)
        self.assertLessEqual(summary["p2_5"], summary["p50"])
        self.assertLessEqual(summary["p50"], summary["p97_5"])

    def test_failed_geometry_produces_zero_transfer_and_fragility(self):
        draws = simreal.expected_draws(20, 20, [30.0], [0.0],
                                       {"drift_mm": 25.0, "spin_deg": 5.0}, n_draws=50)
        self.assertEqual(draws, [0.0] * 50)
        source = {"world": "synthetic-world", "source_branch": "synthetic-world",
                  "source_commit": "0" * 40, "source_report_sha256": "0" * 64,
                  "report": {"results": [{"policy": "classical", "completed": 20, "runs": 20}]}}
        samples = {"source": "provisional-plant", "provisional": True,
                   "drift_mm": [30.0], "spin_error_deg": [0.0]}
        record = simreal.make_records([source], samples, 22.5,
                                      {"drift_mm": 25.0, "spin_deg": 5.0}, n_draws=50)[0]
        self.assertEqual(record["expected_physical_pass"]["p97_5"], 0.0)
        self.assertTrue(record["fragile"])
        self.assertEqual(record["sim_pass_rate"], 1.0)


class E03InputTests(unittest.TestCase):
    def _row(self, kind, trial_id):
        row = {key: "" for key in simreal.E03_COLUMNS}
        row.update({"trial_id": trial_id, "surface_id": "SYNTHETIC_SURFACE", "run_type": kind,
                    "direction": "forward" if kind == "straight" else "left",
                    "attempt_status": "completed"})
        for key in simreal.PROVENANCE:
            row[key] = f"SYNTHETIC_{key}"
        return row

    def _write(self, directory, rows):
        path = pathlib.Path(directory) / "e03.csv"
        with path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=simreal.E03_COLUMNS)
            writer.writeheader()
            writer.writerows(rows)
        return path

    def test_completed_measurements_and_provenance_are_read(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "software" / "stockcar" / "tests") as tmp:
            straight = self._row("straight", "E03-synthetic-straight")
            straight["drift_mm"] = "-12.5"
            spin = self._row("spin", "E03-synthetic-spin")
            spin["spin_error_deg"] = "4"
            planned = self._row("straight", "E03-planned")
            planned["attempt_status"] = "planned"
            path = self._write(tmp, [straight, spin, planned])
            result = simreal.read_e03(path, ROOT)
            self.assertEqual(result["drift_mm"], [-12.5])
            self.assertEqual(result["spin_error_deg"], [4.0])
            self.assertEqual(result["provenance"]["completed_rows"], 2)
            self.assertEqual(len(result["provenance"]["sha256"]), 64)

    def test_placeholder_surface_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "software" / "stockcar" / "tests") as tmp:
            straight = self._row("straight", "E03-synthetic-straight")
            straight["drift_mm"] = "1"
            spin = self._row("spin", "E03-synthetic-spin")
            spin["spin_error_deg"] = "1"
            for row in (straight, spin):
                row["surface_id"] = "DOCUMENT_SURFACE"
            path = self._write(tmp, [straight, spin])
            with self.assertRaisesRegex(ValueError, "surface_id"):
                simreal.read_e03(path, ROOT)


if __name__ == "__main__":
    unittest.main()
