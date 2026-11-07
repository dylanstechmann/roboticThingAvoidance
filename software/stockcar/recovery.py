"""Blocked-route recovery decisions for the computer-only recovery study.

A straightaway is "blocked" when `avoidance.plan_straight` reports `contact`: no straight line clears
every vehicle for the robot's footprint. This module is the pure decision layer over
`stockcar.avoidance`, `stockcar.passage` and `stockcar.obstacles` — no I/O and no simulator state —
so the study's route builders can be unit-tested without running a mission. Nothing here is an
organizer ruling or a prediction about the physical mule.

Agent-written for the owner's hobby/learning project; synthetic only.
"""
from stockcar.avoidance import plan_straight
from stockcar.obstacles import GUIDE_PLUSH, footprint
from stockcar.passage import free_center_intervals

BEHAVIORS = ("lateral_shift", "replan_lanes", "stall_stop")
AUTO = "auto"
ROBOT_WIDTH_IN = 10.0
MARGIN_IN = 0.25
STRAIGHT_X = {"low": (44.0, 80.0), "high": (80.0, 44.0)}   # (x_entry, x_exit) in travel order

# Eight blocker scenarios: four corridor-spanning (the blocker centred on the corridor closes the side
# to a 10 in robot) and four "band" cousins (the same blocker pushed against a wall, which leaves a
# legal centre line on the far side). The guide-plush obstacle is 8.55 x 8.2 in; the straightaway
# corridor is 22.5 in wide (field walls y 1..47, 1 in divider at y 23.5..24.5).
SCENARIOS = {
    "low_mid":         {"side": "low",  "cx": 60.0, "cy": 12.25, "spans": True,  "label": "low, mid, spanning"},
    "low_corner":      {"side": "low",  "cx": 50.0, "cy": 12.25, "spans": True,  "label": "low, west-arc corner, spanning"},
    "high_mid":        {"side": "high", "cx": 64.0, "cy": 35.75, "spans": True,  "label": "high, mid, spanning"},
    "high_corner":     {"side": "high", "cx": 74.0, "cy": 35.75, "spans": True,  "label": "high, east-arc corner, spanning"},
    "low_mid_band":    {"side": "low",  "cx": 60.0, "cy": 5.0,   "spans": False, "label": "low, mid, wall-side blocker leaves a band"},
    "low_corner_band": {"side": "low",  "cx": 50.0, "cy": 5.0,   "spans": False, "label": "low, corner, band"},
    "high_mid_band":   {"side": "high", "cx": 64.0, "cy": 42.0,  "spans": False, "label": "high, mid, wall-side blocker leaves a band"},
    "high_corner_band": {"side": "high", "cx": 74.0, "cy": 42.0, "spans": False, "label": "high, corner, band"},
}


def classify(plan_result):
    """`(mode, blocked_count)` from an `avoidance.plan_straight` result."""
    _lanes, mode, blocked = plan_result
    return mode, blocked


def side_plan(field, vehicles, side, default_y, robot_width=ROBOT_WIDTH_IN, margin=MARGIN_IN):
    """`(mode, blocked_count)` for one straightaway, from the given vehicle dicts."""
    return classify(plan_straight(field, vehicles, side, default_y,
                                  robot_width=robot_width, margin=margin))


def widest_open_band(field, side, vehicles, robot_width=ROBOT_WIDTH_IN, margin=MARGIN_IN):
    """Centre y of the widest band a straight-driving robot can hold past EVERY vehicle, or None.

    Intersects each vehicle's `free_center_intervals` (a straight line must clear the polygon, not
    just thread past its nearest face), so a vehicle that leaves a legal band on one side still
    yields that band. `None` means the side is contact-blocked: no straight line clears it.
    """
    band = field.corridor(side)
    merged = None
    for v in vehicles:
        poly = footprint(v.get("shape", GUIDE_PLUSH), v["cx"], v["cy"], v["yaw"])
        intervals = free_center_intervals(band, poly, robot_width=robot_width, margin=margin)
        if not intervals:
            return None
        if merged is None:
            merged = intervals
        else:
            merged = [(max(a, c), min(b, d)) for a, b in merged for c, d in intervals if max(a, c) <= min(b, d)]
        if not merged:
            return None
    widest = max(merged, key=lambda interval: interval[1] - interval[0])
    return (widest[0] + widest[1]) / 2.0


def decide_recovery(field, side, vehicles, robot_width=ROBOT_WIDTH_IN, margin=MARGIN_IN):
    """The `auto` choice for a blocked side: shift to a clear band when one exists, else thread.

    `replan_lanes` (vehicle-timed S-curves) is the fallback because it can succeed where a single
    fixed lane cannot; on a truly spanning blocker it degrades to the naive lane whose contact the
    supervisor's stall watchdog turns into a stop (`stall_stop`, the explicit no-recovery baseline).
    """
    if widest_open_band(field, side, vehicles, robot_width, margin) is not None:
        return "lateral_shift"
    return "replan_lanes"


def outcome_of(info):
    """Recovery outcome keyed to the injected blocker, not to ordinary obstacle threading.

    The square-10 robot nearly always contacts a quadrant vehicle somewhere (the avoid-v12 finding),
    so "recovered" is only meaningful against the blocker: `recovered` (passed the blocker and the
    whole run contact-free), `recovered_contact` (passed the blocker, other contacts recorded),
    `blocked` (the blocker stopped it), `stopped` (stopped without ever contacting the blocker),
    `incomplete` (step cap without a terminal state).
    """
    if info.get("blocker_passed"):
        if all(c == 0 for c in info.get("vehicle_contact_steps", [1])):
            return "recovered"
        return "recovered_contact"
    if info.get("blocker_contact_frames", 0) > 0:
        return "blocked"
    if info.get("state") == "STOPPED":
        return "stopped"
    return "incomplete"


def make_entry(world, scenario, behavior, pose_mode, seed, info):
    """One computer-only Disrupted-Route (DR) registry entry from a simulated run."""
    spec = SCENARIOS[scenario]
    x_entry, x_exit = STRAIGHT_X[spec["side"]]
    x_range = [min(x_entry, x_exit), max(x_entry, x_exit)]
    return {
        "schema": "dr-registry-v1",
        "entry_kind": "sim",
        "entry_id": "DR-sim-%s-%s-%s-%d" % (scenario, behavior, pose_mode, seed),
        "world": world,
        "route_segment": {"phase": "lap", "side": spec["side"], "x_center_in": spec["cx"],
                          "x_range_in": x_range},
        "blocking": {"kind": "guide-plush",
                     "footprint_in": [GUIDE_PLUSH["length_in"], GUIDE_PLUSH["width_in"]],
                     "yaw_deg": 0.0, "spans_corridor": spec["spans"]},
        "detection": "truth",
        "pose_mode": pose_mode,
        "recovery_behavior": behavior,
        "outcome": outcome_of(info),
        "blocker_passed": bool(info.get("blocker_passed")),
        "blocker_pass_time_s": info.get("blocker_pass_time_s"),
        "blocker_contact_frames": info.get("blocker_contact_frames", 0),
        "completion": info.get("state") == "DONE",
        "contact_free": all(c == 0 for c in info.get("vehicle_contact_steps", [1])),
        "time_s": round(info.get("time_s", 0.0), 2),
        "stop_reason": info.get("stop_reason"),
        "seed": seed,
        "source": "sim:evaluate-recovery-v1",
    }