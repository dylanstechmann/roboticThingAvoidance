"""Sensed-blocker recovery simulator: `RecoveryMissionSim` whose planner sees only the forward
range ring's confirmed vehicle map (assumed-size near faces), never the injected positions.

Lap 1 begins on plain lanes for every behavior. Each step the range ring (`sensors_vehicle.scan`)
adds hits to a `VehicleMap`; the first time a cluster reaches the confirmation count the time is
recorded, and once any newly confirmed vehicle on the blocked side sits within
`replan_lookahead_in` ahead in the travel direction, the lap route is rebuilt from
`VehicleMap.vehicles()` using the behavior's planner:

- ``stall_stop`` — the blind no-recovery baseline: never replans, drives the default lane.
- ``lateral_shift`` — hold `recovery.widest_open_band` for the sensed vehicles; fail honestly to
  the naive lane when no band clears them.
- ``replan_lanes`` — `AvoidingMissionSim._spans` vehicle-timed blends around each sensed
  (assumed guide-size, yaw=0) vehicle.
- ``auto`` — `recovery.decide_recovery` semantics from the sensed vehicles (band else thread).

Blocker contact, passing and the outcome are still measured with the parent's ground-truth
instrumentation (`blocker_poly`, the blocker-freeze, `_update_blocker`), so only the *planning
input* is deprived. The recovery-v1 sealed inputs are untouched: this is a subclass in a new file.

Agent-written for the owner's hobby/learning project; synthetic only.
"""
import random

from stockcar import mission
from stockcar import recovery
from stockcar.obstacles import GUIDE_PLUSH, footprint as obstacle_footprint
from stockcar.recovery_sim import RecoveryMissionSim, inject_blocker
from stockcar.sensors_vehicle import VehicleMap, scan


def confirm_status_of(info):
    """`never|before_contact|after_contact` for one sensed run, from the confirm/contact times."""
    first_confirm = info.get("first_confirm_time_s")
    contact = info.get("first_blocker_contact_s")
    if first_confirm is None:
        return "never"
    if contact is None:
        return "before_contact"          # confirmed, and the blocker was never contacted
    return "after_contact" if contact < first_confirm else "before_contact"


def make_entry_sensed(scenario, behavior, pose_mode, seed, info):
    """One computer-only sensed-recovery row (`detection:"sensed"`)."""
    spec = recovery.SCENARIOS[scenario]
    x_entry, x_exit = recovery.STRAIGHT_X[spec["side"]]
    return {
        "schema": "recovery-sensed-v1",
        "entry_id": "RS-sim-%s-%s-%s-%d" % (scenario, behavior, pose_mode, seed),
        "world": "world-ccw-line-sq-adv-align",
        "detection": "sensed",
        "scenario": scenario,
        "behavior": behavior,
        "pose_mode": pose_mode,
        "seed": seed,
        "route_segment": {"phase": "lap", "side": spec["side"], "x_center_in": spec["cx"],
                          "x_range_in": [min(x_entry, x_exit), max(x_entry, x_exit)]},
        "outcome": recovery.outcome_of(info),
        "completion": info.get("state") == "DONE",
        "contact_free": all(c == 0 for c in info.get("vehicle_contact_steps", [1])),
        "blocker_passed": bool(info.get("blocker_passed")),
        "blocker_pass_time_s": info.get("blocker_pass_time_s"),
        "blocker_contact_frames": info.get("blocker_contact_frames", 0),
        "time_s": round(info.get("time_s", 0.0), 2),
        "replan_count": info.get("replan_count", 0),
        "sensed_vehicles": info.get("sensed_vehicles", 0),
        "confirm_status": confirm_status_of(info),
        "source": "sim:evaluate-recovery-sensed-v1",
    }
class SensedRecoveryMissionSim(RecoveryMissionSim):
    """`RecoveryMissionSim` deprived of vehicle truth: plans from the range ring's `VehicleMap` only."""

    def __init__(self, behavior="stall_stop", pose_mode="true_pose", replan_lookahead_in=30.0,
                 sense_every=1):
        if pose_mode not in ("true_pose", "ekf_pose"):
            raise ValueError("unknown pose_mode %r" % (pose_mode,))
        if behavior not in recovery.BEHAVIORS and behavior != recovery.AUTO:
            raise ValueError("unknown behavior %r" % (behavior,))
        super().__init__(behavior, sensing=(pose_mode == "ekf_pose"))
        self.pose_mode = pose_mode
        self.replan_lookahead_in = replan_lookahead_in
        self.sense_every = sense_every
        self.vmap = VehicleMap()
        self.scan_rng = random.Random(0)
        self.replanned_vehicle_count = 0
        self.replan_count = 0
        self.first_confirm_time_s = None
        self.steps = 0
        self.first_contact_time = None

    # -- routes: the discovery plan has no vehicle knowledge ------------------
    def build_routes(self, layout):
        # Plain lanes for every behavior: no truth (oracle/v10_blend) path is entered.
        self.infeasible_vehicles = 0
        self._build_pit_routes(layout)
        self._set_lap_route([], [])

    # -- sensing and replanning ------------------------------------------------
    def _sense(self):
        pose = (self.state["x"], self.state["y"], self.state["th"])
        self.vmap.add(scan(pose, self.barriers, self.layout.polys, self.scan_rng), pose)
        if self.first_confirm_time_s is None and self.vmap.vehicles():
            self.first_confirm_time_s = round(self.t, 2)

    def _blocker_contact(self):
        hit = super()._blocker_contact()
        if hit and self.first_contact_time is None:
            self.first_contact_time = round(self.t, 2)
        return hit

    def _ahead(self, vehicle, side, x):
        dx = vehicle["cx"] - x if side == "low" else x - vehicle["cx"]
        return 0.0 < dx <= self.replan_lookahead_in

    def _maybe_replan(self):
        if self.behavior == "stall_stop":
            return
        vehs = self.vmap.vehicles()
        if len(vehs) <= self.replanned_vehicle_count:
            return
        if self.route_name != "LAP" or self.blocked_side is None:
            return
        ahead = any(self._ahead(v, self.blocked_side, self.state["x"])
                    for v in vehs if v["side"] == self.blocked_side)
        if not ahead:
            return
        self.replanned_vehicle_count = len(vehs)
        self._replan_from_sensed()

    def _replan_from_sensed(self):
        vehs = self.vmap.vehicles()
        spans = {}
        for side in ("low", "high"):
            vehicles = [v for v in vehs if v["side"] == side]
            if self.behavior in (recovery.BEHAVIORS[0], recovery.AUTO):  # lateral_shift / auto
                y = recovery.widest_open_band(self.field, side, vehicles) if vehicles else None
                if y is not None:
                    x0, x1 = recovery.STRAIGHT_X[side]
                    spans[side] = [(x0, x1, y)]
                elif self.behavior == recovery.AUTO:
                    spans[side] = self._spans(side, [obstacle_footprint(GUIDE_PLUSH, v["cx"], v["cy"], v["yaw"])
                                                      for v in vehicles])
                else:
                    spans[side] = []          # no clear band: the honest naive lane
            else:  # replan_lanes: thread each sensed (assumed-size) vehicle
                spans[side] = self._spans(side, [obstacle_footprint(GUIDE_PLUSH, v["cx"], v["cy"], v["yaw"])
                                                 for v in vehicles])
        snap_s = 0.0
        if self.route_name == "LAP":
            old = self.routes["LAP"]
            snap_s = old.s[min(self.route_index, len(old.s) - 1)]
        self._build_pit_routes(self.layout)
        self._set_lap_route(spans["low"], spans["high"])
        # Re-snap by cumulative path length, not spatial nearest: the LAP is a closed loop whose
        # start and end share the gate point, so a spatial nearest can jump the tracker to the
        # route end and trip `route_done`. The rebuilt route shares the prefix up to the trigger.
        s = self.routes["LAP"].s
        self.route_index = min(range(len(s)), key=lambda i: abs(s[i] - snap_s))
        self.route_done = False
        self.replan_count += 1

    def step(self, action=None):
        if self.out["state"] in ("DONE", "STOPPED"):
            return super().step(action)
        if self.sense_every > 0 and self.steps % self.sense_every == 0:
            self._sense()
        out = super().step(action)
        self.steps += 1
        if self.out["state"] not in ("DONE", "STOPPED"):
            self._maybe_replan()
        return out

    def reset(self, layout, sensor_seed=0):
        out = super().reset(layout, sensor_seed)
        self.vmap = VehicleMap()
        self.scan_rng = random.Random(sensor_seed)
        self.replanned_vehicle_count = 0
        self.replan_count = 0
        self.first_confirm_time_s = None
        self.steps = 0
        self.first_contact_time = None
        return out

    def info(self):
        info = super().info()
        info["pose_mode"] = self.pose_mode
        info["replan_count"] = self.replan_count
        info["sensed_vehicles"] = len(self.vmap.vehicles())
        info["first_confirm_time_s"] = self.first_confirm_time_s
        info["first_blocker_contact_s"] = self.first_contact_time
        return info


def run_recovery_sensed(seed, scenario=None, behavior="stall_stop", pose_mode="true_pose",
                        max_steps=4000, replan_lookahead_in=30.0, sense_every=1):
    """One seeded sensed-recovery mission (`scenario=None` is the unblocked baseline)."""
    rng = random.Random(seed)
    sim = SensedRecoveryMissionSim(behavior, pose_mode=pose_mode,
                                   replan_lookahead_in=replan_lookahead_in, sense_every=sense_every)
    sim.scenario = scenario
    if scenario is not None:
        sim.blocked_side = recovery.SCENARIOS[scenario]["side"]
    layout = mission.random_layout(rng, sim.field, reading="offsets", yaw_mode="aligned", obstacles=True)
    if scenario is not None:
        inject_blocker(layout, sim.field, scenario)
        sim.blocker_poly = layout.polys[-1]
    sim.reset(layout, sensor_seed=seed)
    for _ in range(max_steps):
        _, _, done, info = sim.step()
        if done:
            return info
    return sim.info()