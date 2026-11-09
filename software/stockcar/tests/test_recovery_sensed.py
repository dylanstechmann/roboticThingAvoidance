"""Unit tests for the sensed-blocker recovery simulator.

SYNTHETIC: these check the deprivation (no truth in the plan), the confirm/replan triggers, and the
entry/status helpers. The measured recovery rates are recorded by
tools/evaluate-recovery-sensed-v1.py, not asserted here.
"""
import random
import unittest

from stockcar import mission, recovery
from stockcar.recovery_sensed import (SensedRecoveryMissionSim, confirm_status_of,
                                      make_entry_sensed)
from stockcar.recovery_sim import inject_blocker

DRIVE_STEPS = 1500


def _sim_for(seed, scenario, behavior, pose_mode="true_pose"):
    rng = random.Random(seed)
    sim = SensedRecoveryMissionSim(behavior, pose_mode=pose_mode)
    sim.scenario = scenario
    if scenario is not None:
        sim.blocked_side = recovery.SCENARIOS[scenario]["side"]
    layout = mission.random_layout(rng, sim.field, reading="offsets", yaw_mode="aligned", obstacles=True)
    if scenario is not None:
        inject_blocker(layout, sim.field, scenario)
        sim.blocker_poly = layout.polys[-1]
    sim.reset(layout, sensor_seed=seed)
    return sim


def _drive(sim, limit=DRIVE_STEPS):
    for _ in range(limit):
        _, _, done, info = sim.step()
        if done:
            break
    return sim.info()


class SensedRecoveryDecisionTests(unittest.TestCase):
    def test_first_plan_has_no_vehicle_knowledge(self):
        sim = _sim_for(100, "low_mid", "auto")
        self.assertEqual(sim.low_mode, "clear")
        self.assertEqual(sim.high_mode, "clear")
        self.assertEqual(sim.replan_count, 0)
        self.assertEqual(sim.infeasible_vehicles, 0)
        self.assertIsNotNone(sim.routes["LAP"])
        # Any truth-leak plan would mark a profile lane; the discovery plan must not.
        low_pts = [p for p in sim.routes["LAP"].pts if 46 < p[0] < 78 and p[1] < 23]
        self.assertTrue(all(abs(p[1] - mission.LOW_LANE) < 1e-6 for p in low_pts))

    def test_scan_confirms_a_blocker_ahead(self):
        sim = _sim_for(100, "low_mid", "auto")
        _drive(sim)
        self.assertIsNotNone(sim.first_confirm_time_s)
        self.assertTrue(len(sim.vmap.vehicles()) >= 1)

    def test_replan_fires_on_lookahead(self):
        sim = _sim_for(100, "low_mid", "auto")
        _drive(sim)
        self.assertGreaterEqual(sim.replan_count, 1)
        self.assertEqual(sim.low_mode, "profile")   # a spanning blocker is threaded, not cleared

    def test_replans_are_consistent_with_the_sensed_map(self):
        sim = _sim_for(100, "low_mid_band", "lateral_shift")
        replanned = False
        for _ in range(DRIVE_STEPS):
            prev = sim.replan_count
            _, _, done, _ = sim.step()
            if sim.replan_count > prev:
                replanned = True
                low_vehs = [v for v in sim.vmap.vehicles() if v["side"] == "low"]
                expected = recovery.widest_open_band(sim.field, "low", low_vehs) if low_vehs else None
                low_pts = [p for p in sim.routes["LAP"].pts if 62 < p[0] < 68 and p[1] < 23]
                self.assertTrue(low_pts)
                # At every replan the rebuilt lane matches the sensed map at that moment: the
                # sensed band when one clears the vehicles, otherwise the honest naive lane.
                for p in low_pts:
                    if expected is not None:
                        self.assertLess(abs(p[1] - expected), 0.05)
                    else:
                        self.assertLess(abs(p[1] - mission.LOW_LANE), 1e-6)
            if done:
                break
        self.assertTrue(replanned)
        # The robot measured a near face of the blocker, not its truth centre (5.0).
        low_vehs = [v for v in sim.vmap.vehicles() if v["side"] == "low"]
        self.assertTrue(any(abs(v["cy"] - 5.0) > 1.0 and abs(v["cx"] - 60.0) < 3.0 for v in low_vehs))

    def test_stall_stop_never_replans(self):
        sim = _sim_for(100, "low_mid", "stall_stop")
        info = _drive(sim)
        self.assertEqual(sim.replan_count, 0)
        self.assertEqual(sim.low_mode, "clear")
        self.assertEqual(recovery.outcome_of(info), "blocked")   # drove the naive lane into it

    def test_entry_and_confirm_status(self):
        confirmed_first = {"state": "STOPPED", "first_confirm_time_s": 12.0,
                           "first_blocker_contact_s": 14.0, "blocker_passed": False,
                           "blocker_contact_frames": 5, "vehicle_contact_steps": [0, 0, 0],
                           "time_s": 20.0, "replan_count": 1, "sensed_vehicles": 4}
        self.assertEqual(confirm_status_of(confirmed_first), "before_contact")
        after = dict(confirmed_first, first_confirm_time_s=16.0, first_blocker_contact_s=14.0)
        self.assertEqual(confirm_status_of(after), "after_contact")
        never = dict(confirmed_first, first_confirm_time_s=None, first_blocker_contact_s=14.0)
        self.assertEqual(confirm_status_of(never), "never")
        entry = make_entry_sensed("low_mid", "auto", "true_pose", 100, confirmed_first)
        self.assertEqual(entry["detection"], "sensed")
        self.assertEqual(entry["schema"], "recovery-sensed-v1")
        self.assertEqual(entry["entry_id"], "RS-sim-low_mid-auto-true_pose-100")
        self.assertEqual(entry["outcome"], "blocked")
        self.assertEqual(entry["confirm_status"], "before_contact")


if __name__ == "__main__":
    unittest.main()