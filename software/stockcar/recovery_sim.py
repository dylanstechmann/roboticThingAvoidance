"""Blocked-route recovery simulator: one seeded mission with an injected blocker and a behavior.

`RecoveryMissionSim` extends `AvoidingMissionSim`. A corridor-spanning guide-plush blocker is added to
the layout (truth lane planning), and a blocker-local safety freeze — contact at the injected blocker
halts the robot and lets the supervisor's stall watchdog stop the run — replaces the blanket
collision-stops layer so the unblocked baseline and ordinary obstacle threading keep the v10 "continue
gently" behaviour of the sealed studies. The `behavior` chooses how the robot plans past the block:

- ``stall_stop`` — the status-quo v10 plan (fixed 12 in blends): drives into the blocker and is
  stopped by the stall watchdog (the no-recovery baseline).
- ``lateral_shift`` — hold the widest band that clears every vehicle (`recovery.widest_open_band`);
  a spanning blocker leaves no band, so the robot fails honestly to the naive lane and a stop.
- ``replan_lanes`` — vehicle-timed `lane_profile` blends threading each vehicle by its padded edges.
- ``auto`` — `recovery.decide_recovery`: shift when a clear band exists, otherwise thread.

Pinned v10 source files are untouched; the blocker and behaviours join through a subclass the same way
`AvoidingMissionSim` layers on `SensedMissionSim`. Agent-written; synthetic only.
"""
import random

from stockcar import mission
from stockcar import recovery
from stockcar.mission import HIGH_LANE, LOW_LANE
from stockcar.geometry import separation
from stockcar.mission_avoid import AvoidingMissionSim
from stockcar.obstacles import GUIDE_PLUSH, footprint as obstacle_footprint


def inject_blocker(layout, field, scenario):
    """Append the scenario's corridor-spanning blocker vehicle and its polygon to a layout."""
    spec = recovery.SCENARIOS[scenario]
    cy = spec["cy"]
    layout.vehicles.append({"quadrant": "blocked", "side": spec["side"], "cx": spec["cx"],
                            "cy": cy, "yaw": 0.0, "shape": GUIDE_PLUSH})
    layout.polys.append(obstacle_footprint(GUIDE_PLUSH, spec["cx"], cy, 0.0))


class RecoveryMissionSim(AvoidingMissionSim):
    def __init__(self, behavior="stall_stop", sensing=False):
        if behavior not in recovery.BEHAVIORS and behavior != recovery.AUTO:
            raise ValueError("unknown behavior %r" % (behavior,))
        # stall_stop keeps the status-quo plan (fixed blends); the rest plan from truth lane positions
        # and thread the vehicles by their padded edges (or a fixed clear band, per the behavior).
        lane_source = "v10_blend" if behavior == "stall_stop" else "oracle"
        super().__init__(lane_source=lane_source, sensing=sensing)
        self.behavior = behavior
        self.scenario = None
        self.blocked_side = None
        self.blocker_poly = None
        self.previous_x = None
        self.blocker_passed = False
        self.blocker_pass_time_s = None
        self.blocker_contact_frames = 0

    def _blocker_contact(self):
        if self.blocker_poly is None or self.blocker_passed:
            return False
        return separation(self._footprint(self.state["x"], self.state["y"], self.state["th"]),
                          self.blocker_poly) < 0

    def classical_action(self):
        # Freeze only on a real contact with the injected blocker; elsewhere the v10 gentle policy
        # holds, so ordinary obstacle threading stays comparable to the sealed avoid/rl studies.
        if self._blocker_contact():
            return (0.0, 0.0)
        return mission.MissionSim.classical_action(self)

    def _update_blocker(self, previous_x):
        if self.scenario is None or self.blocker_passed:
            return
        if self._blocker_contact():
            self.blocker_contact_frames += 1
            return
        spec = recovery.SCENARIOS[self.scenario]
        x, y = self.state["x"], self.state["y"]
        lo, hi = self.field.corridor(spec["side"])
        crossed = ((spec["side"] == "low" and previous_x <= spec["cx"] < x)
                   or (spec["side"] == "high" and previous_x >= spec["cx"] > x))
        if (self.blocker_contact_frames == 0 and self.route_name == "LAP"
                and lo <= y <= hi and crossed):
            self.blocker_passed = True
            self.blocker_pass_time_s = round(self.t, 2)

    def step(self, action=None):
        previous_x = self.state["x"] if self.previous_x is None else self.previous_x
        out = super().step(action)
        self._update_blocker(previous_x)
        self.previous_x = self.state["x"]
        return out

    def _vehicle_polys(self, side):
        return [obstacle_footprint(GUIDE_PLUSH, v["cx"], v["cy"], v["yaw"])
                for v in self.layout.vehicles if v["side"] == side]

    def build_routes(self, layout):
        if self.behavior in ("replan_lanes", "stall_stop"):
            super().build_routes(layout)   # oracle thread / v10_blend naive, respectively
            return
        # lateral_shift and auto rebuild each straightaway from a clear band when one exists.
        self.infeasible_vehicles = 0
        spans = {}
        for side in ("low", "high"):
            vehicles = [v for v in layout.vehicles if v["side"] == side]
            default = LOW_LANE if side == "low" else HIGH_LANE
            x0, x1 = recovery.STRAIGHT_X[side]
            y = recovery.widest_open_band(self.field, side, vehicles)
            if y is not None:
                spans[side] = [(x0, x1, y)]
            elif self.behavior == recovery.AUTO:
                spans[side] = self._spans(side, self._vehicle_polys(side))
            else:
                spans[side] = [(x0, x1, default)]   # no band: naive lane, an honest failure
        self._build_pit_routes(layout)
        self._set_lap_route(spans["low"], spans["high"])

    def reset(self, layout, sensor_seed=0):
        out = super().reset(layout, sensor_seed)
        self.blocked = [v for v in layout.vehicles if v.get("quadrant") == "blocked"]
        self.previous_x = self.state["x"]
        self.blocker_passed = False
        self.blocker_pass_time_s = None
        self.blocker_contact_frames = 0
        return out

    def info(self):
        info = super().info()
        info["behavior"] = self.behavior
        info["scenario"] = self.scenario
        info["blocked_side"] = self.blocked_side
        info["blocker_passed"] = self.blocker_passed
        info["blocker_pass_time_s"] = self.blocker_pass_time_s
        info["blocker_contact_frames"] = self.blocker_contact_frames
        return info


def run_recovery(seed, scenario=None, behavior="stall_stop", sensing=False, max_steps=4000):
    """One seeded mission (scenario=None is the unblocked baseline). Returns the info dict."""
    rng = random.Random(seed)
    sim = RecoveryMissionSim(behavior, sensing=sensing)
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