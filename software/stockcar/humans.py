"""Static isolated-human geometry and an oracle-planner safety benchmark subclass.

Humans are synthetic 10 in discs, not measured people or detections. The planner knows
truth positions on straightaways; start, pit and arc geometry is not replanned. Human contacts are
kept separate from vehicle contacts and abort the benchmark run immediately. Synthetic only.
"""
import hashlib
import json
import random

from stockcar import mission
from stockcar.geometry import circle_polygon_distance, rectangle, regular_polygon, separation
from stockcar.mission_avoid import AvoidingMissionSim
from stockcar.obstacles import GUIDE_PLUSH, footprint as obstacle_footprint

HUMAN_RADIUS_IN = 5.0
HUMAN_SEPARATION_IN = 1.0
BARRIER_CLEARANCE_IN = 0.5
ZONE_NAMES = ("start", "pit_lane", "lane_change", "turn")


def human_set_id(humans):
    """Provenance hash of the complete nested placement set, independent of the N slice used."""
    payload = [[h["id"], round(h["cx"], 6), round(h["cy"], 6), h.get("radius_in", HUMAN_RADIUS_IN),
                h["zone"], h["side"]] for h in humans]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def human_polygon(human):
    return regular_polygon(human["cx"], human["cy"], human.get("radius_in", HUMAN_RADIUS_IN), 24)


def min_human_clearance(robot_polygon, humans):
    """Minimum signed surface clearance; negative means human contact. None with no humans."""
    if not humans:
        return None
    return min(circle_polygon_distance(h["cx"], h["cy"], h.get("radius_in", HUMAN_RADIUS_IN), robot_polygon)
               for h in humans)


def _zone(field, name, rng):
    x0, y0, x1, y1 = field.walls
    if name == "start":
        box = field.start_box
        return (box[0] - 12, box[1] - 12, box[2] + 12, box[3] + 12)
    if name == "pit_lane":
        return (x0 + 2, y0 + 2, 44.0, y1 - 2)
    if name == "lane_change":
        side = rng.choice(("low", "high"))
        lo, hi = field.corridor(side)
        return (52.0, lo, 72.0, hi)
    if name == "turn":
        return (32.0, y0 + 2, 48.0, y1 - 2) if rng.random() < 0.5 else (76.0, y0 + 2, 92.0, y1 - 2)
    raise ValueError(name)


def place_humans(seed, layout, field, count=10):
    """Deterministic nested placements, with one of each zone before flexible fallback zones."""
    if not 1 <= count <= 10:
        raise ValueError("count must be in 1..10")
    rng = random.Random(1000003 * seed + 17)
    start = ((field.start_box[0] + field.start_box[2]) / 2,
             (field.start_box[1] + field.start_box[3]) / 2)
    initial_robot = rectangle(start[0], start[1], 0.0, 10.0, 10.0)
    barriers = field.barriers()
    humans = []
    for index in range(count):
        preferred = ZONE_NAMES[index % len(ZONE_NAMES)]
        placed = None
        for attempt in range(12000):
            # Rotate rather than relax geometry when a preferred zone is full.
            zone = preferred if attempt < 2000 else ZONE_NAMES[(index + attempt // 2000) % len(ZONE_NAMES)]
            x0, y0, x1, y1 = _zone(field, zone, rng)
            candidate = {"id": f"H{index + 1:02d}", "cx": rng.uniform(x0, x1), "cy": rng.uniform(y0, y1),
                         "radius_in": HUMAN_RADIUS_IN, "zone": zone}
            poly = human_polygon(candidate)
            if any(separation(poly, b) < BARRIER_CLEARANCE_IN for b in barriers):
                continue
            if separation(poly, initial_robot) < HUMAN_SEPARATION_IN:
                continue
            if any(separation(poly, p) < HUMAN_SEPARATION_IN for p in layout.polys):
                continue
            if any(separation(poly, human_polygon(h)) < HUMAN_SEPARATION_IN for h in humans):
                continue
            candidate["side"] = "low" if candidate["cy"] < 23.5 else "high" if candidate["cy"] > 24.5 else "pit"
            placed = candidate
            break
        if placed is None:
            raise RuntimeError(f"could not place {count} humans for seed {seed}; stopped at {index}")
        humans.append(placed)
    return humans

class HumanMissionSim(AvoidingMissionSim):
    def __init__(self, humans=(), sensing=False):
        super().__init__(lane_source="oracle", sensing=sensing)
        self.humans = list(humans)
        self.aborted = False
        self.human_stop_reason = None
        self.human_contact_ids = set()
        self.human_contact_frames = 0
        self.min_clearance_in = None
        self.infeasible_humans = 0
        self.human_set_id = None

    def build_routes(self, layout):
        low = [obstacle_footprint(v.get("shape", GUIDE_PLUSH), v["cx"], v["cy"], v["yaw"])
               for v in layout.vehicles if v["side"] == "low"]
        high = [obstacle_footprint(v.get("shape", GUIDE_PLUSH), v["cx"], v["cy"], v["yaw"])
                for v in layout.vehicles if v["side"] == "high"]
        straight_humans = [h for h in self.humans if h["zone"] == "lane_change"]
        low += [human_polygon(h) for h in straight_humans if h["side"] == "low"]
        high += [human_polygon(h) for h in straight_humans if h["side"] == "high"]
        self.infeasible_vehicles = 0
        self.infeasible_humans = sum(1 for h in straight_humans if not mission.free_center_intervals(
            self.field.corridor(h["side"]), human_polygon(h), robot_width=10.0, margin=0.25))
        self._build_pit_routes(layout)
        self._set_lap_route(self._spans("low", low), self._spans("high", high))

    def reset(self, layout, sensor_seed=0):
        out = super().reset(layout, sensor_seed)
        self.aborted = False
        self.human_stop_reason = None
        self.human_contact_ids = set()
        self.human_contact_frames = 0
        self.min_clearance_in = min_human_clearance(
            self._footprint(self.state["x"], self.state["y"], self.state["th"]), self.humans)
        return out

    def step(self, action=None):
        obs, reward, done, _info = super().step(action)
        robot = self._footprint(self.state["x"], self.state["y"], self.state["th"])
        clearance = min_human_clearance(robot, self.humans)
        if clearance is not None:
            self.min_clearance_in = clearance if self.min_clearance_in is None else min(self.min_clearance_in, clearance)
        contacted = [h for h in self.humans
                     if circle_polygon_distance(h["cx"], h["cy"], h.get("radius_in", HUMAN_RADIUS_IN), robot) < 0]
        if contacted:
            self.human_contact_frames += 1
            self.human_contact_ids.update(h["id"] for h in contacted)
            self.aborted = True
            self.human_stop_reason = "human_contact"
            done = True
        return obs, reward, done, self.info()

    def info(self):
        info = super().info()
        info.update({"n_humans": len(self.humans), "completed": self.out["state"] == "DONE" and not self.aborted,
                     "aborted": self.aborted, "stop_reason": self.human_stop_reason or self.out.get("stop_reason"),
                     "human_contact_count": len(self.human_contact_ids),
                     "human_contact_ids": sorted(self.human_contact_ids),
                     "human_contact_frames": self.human_contact_frames,
                     "min_clearance_in": self.min_clearance_in,
                     "infeasible_humans": self.infeasible_humans, "human_set_id": self.human_set_id})
        return info


def run_human(seed, n_humans, sensing=False, max_steps=4000, humans=None):
    rng = random.Random(seed)
    sim = HumanMissionSim(sensing=sensing)
    layout = mission.random_layout(rng, sim.field, reading="offsets", yaw_mode="aligned", obstacles=True)
    source_humans = place_humans(seed, layout, sim.field) if humans is None else humans
    sim.human_set_id = human_set_id(source_humans)
    sim.humans = list(source_humans[:n_humans])
    sim.reset(layout, sensor_seed=seed)
    for _ in range(max_steps):
        _, _, done, info = sim.step()
        if done:
            return info
    return sim.info()
