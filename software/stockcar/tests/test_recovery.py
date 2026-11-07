"""Unit and smoke tests for the blocked-route recovery decision layer and simulator.

SYNTHETIC: these check the decision logic and that the sim terminates and reports; the measured
recovery rates are recorded by tools/evaluate-recovery-v1.py, not asserted here.
"""
import random
import unittest

from stockcar import mission, recovery
from stockcar.field import Field
from stockcar.obstacles import GUIDE_PLUSH
from stockcar.recovery_sim import RecoveryMissionSim, inject_blocker, run_recovery


def _taller(field, side, cx, cy):
    return {"side": side, "cx": cx, "cy": cy, "yaw": 0.0, "shape": GUIDE_PLUSH}


class RecoveryDecisionTests(unittest.TestCase):
    def setUp(self):
        self.field = Field()

    def test_spanning_blocker_leaves_no_open_band(self):
        lo, hi = self.field.corridor("low")
        v = _taller(self.field, "low", 60.0, (lo + hi) / 2.0)
        self.assertIsNone(recovery.widest_open_band(self.field, "low", [v]))
        self.assertEqual(recovery.side_plan(self.field, [v], "low", mission.LOW_LANE), ("contact", 1))

    def test_every_scenario_span_label_matches_blocker_geometry(self):
        for name, spec in recovery.SCENARIOS.items():
            with self.subTest(scenario=name):
                blocker = _taller(self.field, spec["side"], spec["cx"], spec["cy"])
                band = recovery.widest_open_band(self.field, spec["side"], [blocker])
                self.assertEqual(band is None, spec["spans"])

    def test_off_centre_blocker_leaves_a_band_away_from_it(self):
        lo, _ = self.field.corridor("low")
        y = lo + 7.5  # against the wall leaves a divider-side band
        v = _taller(self.field, "low", 60.0, y)
        band = recovery.widest_open_band(self.field, "low", [v])
        self.assertIsNotNone(band)
        self.assertGreater(band, y)

    def test_decide_recovery_prefers_shift_when_a_band_exists(self):
        f = self.field
        lo, _ = f.corridor("low")
        off = _taller(f, "low", 60.0, lo + 7.5)
        self.assertEqual(recovery.decide_recovery(f, "low", [off]), "lateral_shift")
        span = _taller(f, "low", 60.0, (f.corridor("low")[0] + f.corridor("low")[1]) / 2.0)
        self.assertEqual(recovery.decide_recovery(f, "low", [span]), "replan_lanes")

    def test_classify_outcome_and_entry_shapes(self):
        self.assertEqual(recovery.classify(([(44.0, 80.0, 9.0)], "contact", 1)), ("contact", 1))
        clean = {"state": "DONE", "blocker_passed": True, "vehicle_contact_steps": [0, 0, 0],
                 "time_s": 100.0, "stop_reason": None}
        self.assertEqual(recovery.outcome_of(clean), "recovered")
        passed = {"state": "DONE", "blocker_passed": True, "vehicle_contact_steps": [3, 0, 0],
                  "time_s": 100.0, "stop_reason": None}
        self.assertEqual(recovery.outcome_of(passed), "recovered_contact")
        blocked = {"state": "STOPPED", "blocker_contact_frames": 5, "time_s": 20.0, "stop_reason": "stalled"}
        self.assertEqual(recovery.outcome_of(blocked), "blocked")
        stopped = {"state": "STOPPED", "time_s": 178.0, "stop_reason": "auto_stop"}
        self.assertEqual(recovery.outcome_of(stopped), "stopped")
        entry = recovery.make_entry("world-ccw-line-sq-adv-align", "low_mid", "lateral_shift",
                                    "true_pose", 100, clean)
        self.assertEqual(entry["entry_kind"], "sim")
        self.assertEqual(entry["entry_id"], "DR-sim-low_mid-lateral_shift-true_pose-100")
        self.assertTrue(entry["blocking"]["spans_corridor"])
        self.assertEqual(entry["outcome"], "recovered")
        self.assertTrue(entry["blocker_passed"])
        self.assertIsNone(entry["blocker_pass_time_s"])
        self.assertEqual(entry["blocker_contact_frames"], 0)


class RecoverySimTests(unittest.TestCase):
    def test_injection_puts_one_blocker_on_the_side(self):
        field = Field()
        layout = mission.random_layout(random.Random(105), field, reading="offsets",
                                       yaw_mode="aligned", obstacles=True)
        before = len(layout.vehicles)
        inject_blocker(layout, field, "low_mid")
        self.assertEqual(len(layout.vehicles), before + 1)
        self.assertEqual(layout.vehicles[-1]["quadrant"], "blocked")
        self.assertEqual(layout.vehicles[-1]["side"], "low")
        self.assertEqual(len(layout.polys), before + 1)

    def test_every_behavior_runs_and_reports(self):
        for behavior in recovery.BEHAVIORS + (recovery.AUTO,):
            info = run_recovery(105, scenario="low_mid", behavior=behavior, max_steps=300)
            self.assertEqual(info["behavior"], behavior)
            self.assertEqual(info["scenario"], "low_mid")
            self.assertIn(info["state"], ("DONE", "STOPPED", "ENTER", "LAP", "TO_PIT", "EXIT_PIT", "PARK"))

    def test_high_blocker_is_not_passed_from_the_start_or_pit_side(self):
        info = run_recovery(100, scenario="high_mid", behavior="stall_stop", max_steps=4000)
        self.assertFalse(info["blocker_passed"])
        self.assertGreater(info["blocker_contact_frames"], 0)
        self.assertEqual(recovery.outcome_of(info), "blocked")

    def test_crossing_requires_lap_direction_and_blocked_corridor(self):
        cases = (("ENTER", True, 45.0, False), ("LAP", True, 45.0, True),
                 ("LAP", False, 45.0, False), ("LAP", True, 20.0, False))
        for route_name, forward, y, expected in cases:
            with self.subTest(route=route_name, forward=forward, y=y):
                sim = RecoveryMissionSim()
                sim.scenario = "high_mid"
                layout = mission.random_layout(random.Random(7), sim.field, obstacles=False)
                inject_blocker(layout, sim.field, "high_mid")
                sim.blocker_poly = layout.polys[-1]
                sim.reset(layout)
                sim.route_name = route_name
                sim.state.update(x=63.0 if forward else 65.0, y=y)
                sim._update_blocker(65.0 if forward else 63.0)
                self.assertEqual(sim.blocker_passed, expected)

    def test_unblocked_baseline_completes(self):
        info = run_recovery(110, scenario=None, behavior="stall_stop", max_steps=6000)
        self.assertEqual(info["state"], "DONE")

    def test_unknown_arguments_are_rejected(self):
        with self.assertRaises(ValueError):
            RecoveryMissionSim(behavior="nonsense")
        with self.assertRaises(KeyError):
            recovery.SCENARIOS["nope"]


if __name__ == "__main__":
    unittest.main()