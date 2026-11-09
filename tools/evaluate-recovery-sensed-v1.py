"""Evaluate sensed-blocker recovery across scenarios, behaviors and pose modes.

Agent-run synthetic study on the reserved evaluation seeds 100-119. Eight scenarios (two
straightaway sides x two blocker positions, each spanning and band), four behaviors (stall_stop,
lateral_shift, replan_lanes, auto) and two pose modes (control on the true pose or the EKF
estimate), all deprived of vehicle truth: planning uses only the range ring's `VehicleMap`. Also
runs an unblocked sensed baseline per pose/seed, and writes an oracle-vs-sensed comparison read
from the sealed `derived/recovery-v1/report.json`. Writes the sealed
`derived/recovery-sensed-v1/` package: manifest.json, report.json, summary.md, rows.json.

Usage: uv run --no-project --python 3.12 python -B -I tools/evaluate-recovery-sensed-v1.py [--smoke]
"""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "software"))
from stockcar import mission  # noqa: E402
from stockcar import recovery  # noqa: E402
from stockcar.recovery_sensed import confirm_status_of, make_entry_sensed, run_recovery_sensed  # noqa: E402
from stockcar.study_stats import wilson  # noqa: E402

OUT = ROOT / "derived" / "recovery-sensed-v1"
WORLD = "world-ccw-line-sq-adv-align"  # SECRETS-GUARD-IGNORE: public ruleset identifier, not a credential
DATE = "2026-11-07"
SMOKE = "--smoke" in sys.argv
SEEDS = list(mission.MissionEnv.EVAL)
RUN_SEEDS = SEEDS[:2] if SMOKE else SEEDS
SCENARIOS = tuple(recovery.SCENARIOS)
BEHAVIORS = recovery.BEHAVIORS + (recovery.AUTO,)  # SECRETS-GUARD-IGNORE: behavior expression, not a credential
POSE_MODES = ("true_pose", "ekf_pose")
INPUTS = [
    "tools/evaluate-recovery-sensed-v1.py", "software/stockcar/recovery_sensed.py",
    "software/stockcar/recovery.py", "software/stockcar/study_stats.py",
    "software/stockcar/recovery_sim.py", "software/stockcar/mission_avoid.py",
    "software/stockcar/mission_sensed.py", "software/stockcar/mission.py",
    "software/stockcar/supervisor.py", "software/stockcar/lapmodel.py", "software/stockcar/passage.py",
    "software/stockcar/field.py", "software/stockcar/obstacles.py", "software/stockcar/geometry.py",
    "software/stockcar/sensors_camera.py", "software/stockcar/sensors.py", "software/stockcar/estimator.py",
    "software/stockcar/avoidance.py", "software/stockcar/lane_profile.py",
    "software/stockcar/sensors_vehicle.py", "derived/organizer-cad-v10/field-v10.json",
]


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def cell_of(rows, scenario, behavior, pose):
    runs = [r for r in rows if r["scenario"] == scenario and r["behavior"] == behavior
            and r["pose_mode"] == pose]
    recovered = sum(1 for r in runs if r["outcome"] == "recovered")
    recovered_contact = sum(1 for r in runs if r["outcome"] == "recovered_contact")
    blocked = sum(1 for r in runs if r["outcome"] == "blocked")
    stopped = sum(1 for r in runs if r["outcome"] == "stopped")
    incomplete = sum(1 for r in runs if r["outcome"] == "incomplete")
    passed = recovered + recovered_contact
    confirmed = sum(1 for r in runs if r["confirm_status"] != "never")
    after = sum(1 for r in runs if r["confirm_status"] == "after_contact")
    return {"scenario": scenario, "behavior": behavior, "pose_mode": pose, "runs": len(runs),
            "completed": sum(1 for r in runs if r["state"] == "DONE"), "passed_blocker": passed,
            "recovered": recovered, "recovered_contact": recovered_contact, "blocked": blocked,
            "stopped": stopped, "incomplete": incomplete, "passed_wilson95": wilson(passed, len(runs)),
            "mean_time_s": round(sum(r["time_s"] for r in runs) / len(runs), 2),
            "confirmed_rate": round(confirmed / len(runs), 4),
            "mean_replans": round(sum(r["replan_count"] for r in runs) / len(runs), 2),
            "contact_before_confirm": after}
def summary_text(cells, baseline, comparison, rows):
    def n(outcome):
        return sum(1 for r in rows if r["outcome"] == outcome)
    total = len(rows)
    recovered = n("recovered") + n("recovered_contact")
    band = [c for c in cells if c["scenario"].endswith("_band")]
    spanning = [c for c in cells if not c["scenario"].endswith("_band")]

    def rate(cs):
        rec = sum(c["recovered"] + c["recovered_contact"] for c in cs)
        return rec, sum(c["runs"] for c in cs)
    b_rec, b_runs = rate(band)
    s_rec, s_runs = rate(spanning)
    never = sum(1 for r in rows if r["confirm_status"] == "never")
    after = sum(1 for r in rows if r["confirm_status"] == "after_contact")
    return [
        "# recovery-sensed-v1 — sensed blocker detection",
        "",
        "Agent-run synthetic study (%s). Every run plans only from the forward range ring's "
        "confirmed `VehicleMap`; the first plan is a plain-lane discovery lap and recovery replans "
        "fire when a newly confirmed vehicle is within 30 in ahead on the blocked side. Blocker "
        "contact/pass are still measured with ground truth, so only the planning input is deprived."
        % DATE,
        "",
        "## Measured outcomes (not tuned)",
        "- runs: %d (8 scenarios x 4 behaviors x 2 pose modes x %d seeds)" % (total, len(RUN_SEEDS)),
        "- recovered or recovered_contact: %d/%d" % (recovered, total),
        "- blocked: %d; stopped: %d; incomplete: %d" % (n("blocked"), n("stopped"), n("incomplete")),
        "- band scenarios recovered: %d/%d; spanning scenarios: %d/%d" % (b_rec, b_runs, s_rec, s_runs),
        "- confirm never reached: %d/%d; contacted before confirm: %d/%d" % (never, total, after, total),
        "- unblocked sensed baseline: %d/%d completed" % (sum(1 for b in baseline if b["completed"]),
                                                          len(baseline)),
        "",
        "## Semantics and limitations",
        "- `stall_stop` here is the blind default-lane baseline (no sensing use), unlike recovery-v1's "
        "truth plan_straight lane; the two studies are not drop-in comparable on the band scenarios.",
        "- The sensed planner sees an assumed guide-size near face (yaw=0, labeled depth); ray layout, "
        "noise, dropout and gates are placeholders pending Order B bench data (QA03/QA08).",
        "- EKF pose mode feeds the estimator pose to the controller; the range ring uses the truth "
        "pose, mirroring the avoiding-simulator convention.",
        "- Outcomes are measured, not claims of hardware robustness.",
        "",
        "## Oracle vs sensed (from the sealed recovery-v1 report, rates are fractions)",
        "```",
    ] + ["%s %s %s oracle=%.3f sensed=%.3f" % (c["scenario"], c["behavior"], c["pose_mode"],
                                                c["oracle_recovered_rate"], c["sensed_recovered_rate"])
         for c in comparison] + ["```", ""]
def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows, entries, baseline, comparison = [], [], [], []
    print("baselines (%d)..." % (len(POSE_MODES) * len(RUN_SEEDS)), flush=True)
    for pose in POSE_MODES:
        for seed in RUN_SEEDS:
            info = run_recovery_sensed(seed, scenario=None, behavior="stall_stop", pose_mode=pose)
            baseline.append({"pose_mode": pose, "seed": seed, "completed": info["state"] == "DONE",
                             "planned_contact_vehicles": info["planned_contact_vehicles"],
                             "lane_modes": info["lane_modes"]})
    total_runs = len(SCENARIOS) * len(BEHAVIORS) * len(POSE_MODES) * len(RUN_SEEDS)
    print("cells (%d runs)..." % total_runs, flush=True)
    done = 0
    for scenario in SCENARIOS:
        for pose in POSE_MODES:
            for seed in RUN_SEEDS:
                for behavior in BEHAVIORS:
                    info = run_recovery_sensed(seed, scenario=scenario, behavior=behavior, pose_mode=pose)
                    outcome = recovery.outcome_of(info)
                    entries.append(make_entry_sensed(scenario, behavior, pose, seed, info))
                    rows.append({"scenario": scenario, "behavior": behavior, "pose_mode": pose,
                                 "seed": seed, "state": info["state"], "outcome": outcome,
                                 "time_s": info["time_s"], "replan_count": info["replan_count"],
                                 "confirm_status": confirm_status_of(info)})
                    done += 1
                    if done % 64 == 0:
                        print("  %d/%d" % (done, total_runs), flush=True)
    cells = [cell_of(rows, s, b, p) for s in SCENARIOS for b in BEHAVIORS for p in POSE_MODES]
    oracle = json.loads((ROOT / "derived" / "recovery-v1" / "report.json").read_text(encoding="utf-8"))
    oracle_cells = {(c["scenario"], c["behavior"], c["pose_mode"]): c for c in oracle["cells"]}
    for c in cells:
        o = oracle_cells.get((c["scenario"], c["behavior"], c["pose_mode"]))
        if o is not None:
            comparison.append({"scenario": c["scenario"], "behavior": c["behavior"],
                               "pose_mode": c["pose_mode"],
                               "oracle_recovered_rate": round((o["recovered"] + o["recovered_contact"]) / o["runs"], 4),
                               "sensed_recovered_rate": round((c["recovered"] + c["recovered_contact"]) / c["runs"], 4)})
    report = {"date": DATE, "status": "agent-run synthetic study; sensed near-face priors and "
              "placeholder ray/noise/gates are assumptions; smoke=%s" % SMOKE, "world": WORLD,
              "seeds": RUN_SEEDS, "cells": cells, "baseline": baseline, "comparison": comparison}
    summary = "\n".join(summary_text(cells, baseline, comparison, rows))
    (OUT / "rows.json").write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    (OUT / "summary.md").write_text(summary + "\n", encoding="utf-8")
    manifest = {"date": DATE, "status": report["status"], "smoke": SMOKE,
                "input_hashes": {f: sha256(ROOT / f) for f in INPUTS},
                "output_hashes": {"report.json": sha256(OUT / "report.json"),
                                  "summary.md": sha256(OUT / "summary.md"),
                                  "rows.json": sha256(OUT / "rows.json")}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print("wrote %s (%d cells, %d rows, %d baselines)" % (OUT.relative_to(ROOT), len(cells),
                                                          len(rows), len(baseline)))


if __name__ == "__main__":
    main()