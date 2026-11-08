import pathlib
import sys
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "tools"))
import build_field_tables  # noqa: E402


class BuildFieldTablesTests(unittest.TestCase):
    def test_rendered_tables_match_the_committed_firmware_map(self):
        tables = build_field_tables.render_tables()
        committed = (ROOT / "firmware" / "pico2" / "field_tables.py").read_text(encoding="utf-8")
        self.assertEqual(tables + "\n", committed)

    def test_tables_carry_the_expected_structure(self):
        namespace = {}
        exec(build_field_tables.render_tables(), namespace)
        self.assertEqual(len(namespace["BARRIERS"]), 6)
        self.assertEqual(len(namespace["BAND_OUTER"]), 8)
        self.assertEqual(len(namespace["BAND_INNER"]), 8)
        self.assertEqual(namespace["COUNTS_PER_REV"], 1120)
        self.assertGreater(namespace["SHALLOWEST_CROSSING"], 0)


if __name__ == "__main__":
    unittest.main()