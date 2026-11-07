"""Evaluate static isolated-human planner safety for N=1..10 on reserved seeds 100-119.

Synthetic 10 in discs have truth positions known to the straightaway oracle planner. Start, pit and
turn geometry is deliberately not replanned; first human contact aborts immediately. Nested N adds
placements in zone order, so N trends are descriptive and confounded with zone composition.

Usage: uv run --no-project --python 3.12 python -B -I tools/evaluate-humans-v1.py
"""
import hashlib
import json
import pathlib
import random
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "software"))
from stockcar import mission  # noqa: E402
from stockcar.field import Field  # noqa: E402
from stockcar.humans import HUMAN_RADIUS_IN, place_humans, run_human  # noqa: E402
from stockcar.study_stats import quantile, wilson  # noqa: E402

OUT = ROOT / "derived" / "humans-v1"
DATE = "2026-11-07"
SEEDS = list(mission.MissionEnv.EVAL)
INPUTS = ["tools/evaluate-humans-v1.py", "software/stockcar/humans.py",
          "software/stockcar/study_stats.py", "software/stockcar/mission_avoid.py",
          "software/stockcar/mission_sensed.py", "software/stockcar/mission.py",
          "software/stockcar/supervisor.py", "software/stockcar/lapmodel.py",
          "software/stockcar/passage.py", "software/stockcar/field.py",
          "software/stockcar/obstacles.py", "software/stockcar/geometry.py",
          "software/stockcar/sensors_camera.py", "software/stockcar/sensors.py",
          "software/stockcar/estimator.py", "software/stockcar/lane_profile.py",
          "software/stockcar/sensors_vehicle.py", "derived/organizer-cad-v10/field-v10.json"]
RUN_KEYS = ("seed", "state", "completed", "aborted", "stop_reason", "human_contact_count",
            "human_contact_frames", "min_clearance_in", "time_s", "human_set_id")


def detail(info, seed):
    row = {key: info.get(key) for key in RUN_KEYS}
    row["seed"] = seed
    row["min_clearance_in"] = round(row["min_clearance_in"], 6)
    return row


def cell(n, rows):
    completed = sum(r["completed"] for r in rows)
    contact_runs = sum(r["human_contact_count"] > 0 for r in rows)
    aborted = sum(r["aborted"] for r in rows)
    clearances = [r["min_clearance_in"] for r in rows]
    return {"n_humans": n, "runs": len(rows), "completed": completed,
            "completion_rate": round(completed / len(rows), 4),
            "completion_wilson95": wilson(completed, len(rows)),
            "human_contact_count": sum(r["human_contact_count"] for r in rows),
            "human_contact_runs": contact_runs, "human_contact_rate": round(contact_runs / len(rows), 4),
            "human_contact_wilson95": wilson(contact_runs, len(rows)),
            "min_clearance_in": {"p50": round(quantile(clearances, 0.5), 4),
                                 "p05": round(quantile(clearances, 0.05), 4)},
            "aborted": aborted, "aborted_rate": round(aborted / len(rows), 4),
            "aborted_wilson95": wilson(aborted, len(rows)), "runs_detail": rows}

def main():
    rows_by_n = {n: [] for n in range(1, 11)}
    for seed in SEEDS:
        # Seed-outer/N-inner: one placement set per seed, nested for every N in that seed only.
        field = Field()
        layout = mission.random_layout(random.Random(seed), field, reading="offsets",
                                       yaw_mode="aligned", obstacles=True)
        humans = place_humans(seed, layout, field)
        for n in range(1, 11):
            info = run_human(seed, n, humans=humans)
            rows_by_n[n].append(detail(info, seed))
    cells = [cell(n, rows_by_n[n]) for n in range(1, 11)]
    report = {"version": "0.1.0", "date": DATE,
              "status": "agent-run synthetic static-human benchmark; truth positions, not perception or physical safety",
              "world": "world-ccw-line-sq-adv-align", "seeds": SEEDS,
              "model": {"human_radius_in": HUMAN_RADIUS_IN, "humans": "static, non-reactive discs",
                        "planner": "oracle truth on lane-change straightaways; start/pit/turn not replanned",
                        "abort": "first human contact", "nested_zone_order": ["start", "pit_lane", "lane_change", "turn"],
                        "corridor_geometry": "10 in human + 10 in robot + margins leaves only narrow wall-adjacent bands; centered humans are infeasible",
                        "trend_caveat": "N is confounded with zone composition; no causal trend is inferred"},
              "cells": cells}
    summary = ["# Isolated-human planner safety v1", "",
               f"{DATE}. Agent-run synthetic study, N=1..10 x 20 seeds = 200 runs. Humans are static "
               f"{2 * HUMAN_RADIUS_IN:g} in discs with truth positions. First contact aborts immediately; "
               "only lane-change straightaways are considered by the oracle planner. A 10 in human + 10 in robot "
               "+ margins leaves only narrow wall-adjacent bands; centered humans are infeasible.", "",
               "| N | completed | completion rate | contact runs | total contacts | aborted | min-clearance p50 | p05 |",
               "|---:|---:|---:|---:|---:|---:|---:|---:|"]
    for c in cells:
        summary.append(f"| {c['n_humans']} | {c['completed']}/20 | {c['completion_rate']} "
                       f"| {c['human_contact_runs']}/20 | {c['human_contact_count']} | {c['aborted']}/20 "
                       f"| {c['min_clearance_in']['p50']} | {c['min_clearance_in']['p05']} |")
    summary += ["", "Placements are nested in start/pit-lane/lane-change/turn order. N therefore "
                "changes both crowding and zone composition; no causal or monotonic trend is claimed. "
                "Human contacts are separate from vehicle contacts. Static truth geometry is not human "
                "perception, and completion without a human contact is not a physical safety qualification."]
    files = {"report.json": json.dumps(report, indent=1) + "\n", "summary.md": "\n".join(summary) + "\n"}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (OUT / name).write_text(text, encoding="utf-8")
    manifest = {"date": DATE, "status": report["status"],
                "input_hashes": {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in INPUTS},
                "output_hashes": {n: hashlib.sha256(t.encode()).hexdigest() for n, t in files.items()}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(cells)} cells x 20 runs")


if __name__ == "__main__":
    main()
