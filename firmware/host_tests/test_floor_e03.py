# Floor-trial runner and log tool, tested against the simulated motor and the plant model.
# SYNTHETIC: these check behavior; plant friction, mass and inertia are placeholders, so passing
# does not predict the physical mule. Ground truth comes from the plant's own state.
import json
import math
import pathlib
import sys
import unittest

import config
import floor_e03
from host_tests.fakes import FakeHal
from host_tests.plant_hal import PlantHal
from runner import Runner

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools" / "bench"))
import log_to_e03  # noqa: E402

E03_TEMPLATE = ROOT / "derived" / "drivetrain-mule-v10" / "templates" / "E03-trials.csv"
IN_TO_M = 0.0254
NOMINAL = (11.1, 0.25, 4.0)  # source V, friction, mass: the 4 kg qualifying case


class TripHal(FakeHal):
    """A fake that latches the e-stop partway through a trial (counts encoder polls)."""

    def __init__(self, trip_after):
        super().__init__()
        self.polls = 0
        self.trip_after = trip_after

    def poll_encoders(self):
        self.polls += 1
        if self.polls >= self.trip_after:
            self.estop = True
        return super().poll_encoders()


def dump_records(runner):
    lines = []
    runner.log.dump(lines.append, json.dumps)
    return [json.loads(line) for line in lines], "\n".join(lines) + "\n"


def body_speed_in_s(record):
    rpm = record["rpm"]
    return (rpm[0] + rpm[1]) / 2.0 / 60.0 * 2.0 * math.pi * config.WHEEL_RADIUS_M / IN_TO_M


class StraightTests(unittest.TestCase):
    def test_straight_trial_lands_on_target_distance(self):
        hal = PlantHal(*NOMINAL)
        runner = Runner(hal, mode="DRIVE")
        summary = floor_e03.straight(runner, speed_in_s=8.0, length_m=1.0)
        self.assertEqual(summary["result"], "completed")
        self.assertAlmostEqual(summary["distance_m"], 1.0, delta=0.05)
        self.assertGreater(summary["duration_s"], 1.0)
        moved = math.sqrt(hal.state["x"] ** 2 + hal.state["y"] ** 2)
        self.assertAlmostEqual(moved, 1.0, delta=0.10)  # ground truth from the plant
        records, _ = dump_records(runner)
        self.assertTrue(records)
        self.assertTrue(all(r["mode"] == "DRIVE" for r in records))
        first = records[0]["t_ms"]
        cruise = [r for r in records if 2000 <= r["t_ms"] - first <= 3500]
        self.assertTrue(cruise)
        # Mean, not max: the PI briefly overshoots the cruise target by ~10% while settling.
        self.assertAlmostEqual(sum(body_speed_in_s(r) for r in cruise) / len(cruise), 8.0, delta=0.5)
        self.assertLess(max(body_speed_in_s(r) for r in cruise), 10.0)


class SpinTests(unittest.TestCase):
    def test_spin_trial_lands_on_target_yaw(self):
        hal = PlantHal(*NOMINAL)
        runner = Runner(hal, mode="DRIVE")
        summary = floor_e03.spin(runner, "left", yaw_rate_rad_s=2.0, revolutions=1.0)
        self.assertEqual(summary["result"], "completed")
        self.assertTrue(345.0 <= summary["yaw_deg"] <= 375.0, summary["yaw_deg"])
        # The plant couples yaw to forward velocity, so an in-place spin turns the wheels without
        # turning the body; the body's real spin error is the physical quantity E03 measures. The
        # plant-true check is the wheel differential: one revolution means each wheel rolls the
        # half-track arc in opposite directions.
        left, right = hal.state["wheel_angle"]
        target = 2.0 * 2.0 * math.pi * config.HALF_TRACK_M / config.WHEEL_RADIUS_M
        self.assertAlmostEqual(right - left, target, delta=2.0)

    def test_spin_direction_sets_the_yaw_sign(self):
        hal = PlantHal(*NOMINAL)
        runner = Runner(hal, mode="DRIVE")
        summary = floor_e03.spin(runner, "right", yaw_rate_rad_s=2.0, revolutions=0.25)
        self.assertEqual(summary["result"], "completed")
        self.assertTrue(-105.0 <= summary["yaw_deg"] <= -75.0, summary["yaw_deg"])
        left, right = hal.state["wheel_angle"]
        target = -2.0 * 0.5 * math.pi * config.HALF_TRACK_M / config.WHEEL_RADIUS_M
        self.assertAlmostEqual(right - left, target, delta=1.0)


class SafetyTests(unittest.TestCase):
    def test_estop_mid_trial_latches_and_refuses_rearm(self):
        hal = TripHal(trip_after=400)  # roughly one second in, while moving
        runner = Runner(hal, mode="DRIVE")
        summary = floor_e03.straight(runner, speed_in_s=8.0, length_m=1.0)
        self.assertEqual(summary["result"], "estop")
        self.assertEqual(summary["stop_reason"], "estop")
        self.assertFalse(hal.enabled)
        self.assertLess(summary["distance_m"], 1.0)
        again = floor_e03.straight(runner, speed_in_s=8.0, length_m=1.0)
        self.assertTrue(again["result"].startswith("not armed"))

    def test_beyond_envelope_parameters_are_refused(self):
        with self.assertRaises(ValueError):
            floor_e03.check(40.0, 0.0)
        with self.assertRaises(ValueError):
            floor_e03.check(0.0, 6.0)
        hal = FakeHal()
        runner = Runner(hal, mode="DRIVE")
        with self.assertRaises(ValueError):
            floor_e03.straight(runner, speed_in_s=40.0)
        with self.assertRaises(ValueError):
            floor_e03.spin(runner, "left", yaw_rate_rad_s=6.0)
        with self.assertRaises(ValueError):
            floor_e03.spin(runner, "sideways")
        with self.assertRaises(ValueError):
            floor_e03.straight(runner, speed_in_s=8.0, length_m=0.0)
        with self.assertRaises(ValueError):
            floor_e03.spin(runner, "left", revolutions=0.0)
        self.assertEqual(hal.enable_history, [])  # refused before arming


class LogToolTests(unittest.TestCase):
    def test_straight_row_matches_the_template(self):
        hal = FakeHal()
        runner = Runner(hal, mode="DRIVE")
        summary = floor_e03.straight(runner, speed_in_s=8.0, length_m=1.0)
        self.assertEqual(summary["result"], "completed")
        _, text = dump_records(runner)
        row = log_to_e03.row_from_log(text, "e03-1.jsonl", "dual-front-rear", 2, "straight", "forward", 1)
        header = E03_TEMPLATE.read_text(encoding="utf-8").splitlines()[0].split(",")
        self.assertEqual(list(row.keys()), header)
        self.assertEqual(row["trial_id"], "E03-dual-front-rear-2-straight-1")
        self.assertEqual(row["support_configuration"], "dual-front-rear")
        self.assertEqual(row["mass_kg"], "2")
        self.assertEqual(row["run_type"], "straight")
        self.assertEqual(row["direction"], "forward")
        self.assertEqual(row["repeat"], "1")
        self.assertAlmostEqual(float(row["duration_s"]), summary["duration_s"], delta=0.1)
        speed = float(row["max_speed_in_s"])
        self.assertGreater(speed, 6.0)
        self.assertLess(speed, 9.0)
        self.assertEqual(row["thermal_or_protection_fault"], "")
        for blank in ("surface_id", "drift_mm", "spin_error_deg", "slip_observed", "session_id",
                      "configuration_id", "recorded_at", "operator_id", "instrument_ids",
                      "calibration_check_id", "setup_record_id", "control_revision",
                      "warmup_record_id", "uncertainty_record_id", "attempt_status",
                      "exclusion_reason", "replaces_trial_id"):
            self.assertEqual(row[blank], "", blank)
        self.assertTrue(row["raw_observation_ref"].startswith("e03-1.jsonl sha256:"))

    def test_spin_row_uses_the_direction_in_the_trial_id(self):
        hal = FakeHal()
        runner = Runner(hal, mode="DRIVE")
        summary = floor_e03.spin(runner, "left", yaw_rate_rad_s=2.0, revolutions=1.0)
        self.assertEqual(summary["result"], "completed")
        _, text = dump_records(runner)
        row = log_to_e03.row_from_log(text, "e03-2.jsonl", "front-only", 4, "spin", "left", 1)
        self.assertEqual(row["trial_id"], "E03-front-only-4-spin-left-1")
        self.assertEqual(row["max_speed_in_s"], "")  # spins carry no straight-line speed
        self.assertAlmostEqual(float(row["duration_s"]), summary["duration_s"], delta=0.1)


if __name__ == "__main__":
    unittest.main()