"""Evaluate blocked-route recovery across scenarios, behaviors and pose modes.

Agent-run synthetic study on the reserved evaluation seeds 100-119. Four blocked scenarios (two
straightaway sides x two blocker positions, each in a spanning and a band form), four behaviors
(`stall_stop`, `lateral_shift`, `replan_lanes`, `auto`) and two pose modes (control on the true pose
or the EKF estimate) = 64 cells x 20 runs. Every seed also runs an unblocked baseline so the recovery
success rate can be tied to the
same seed's router pass. Writes the sealed `derived/recovery-v1/` package and the computer-only DR
registry (`derived/dr-registry-v1/`).

Usage: uv run --no-project --python 3.12 python -B -I tools/evaluate-recovery-v1.py
"""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "software"))
from stockcar import mission  # noqa: E402
from stockcar import recovery  # noqa: E402
from stockcar.recovery_sim import run_recovery  # noqa: E402
from stockcar.study_stats import clustered_permutation_p, spearman, wilson  # noqa: E402

OUT = ROOT / "derived" / "recovery-v1"
DR = ROOT / "derived" / "dr-registry-v1"
WORLD = "world-ccw-line-sq-adv-align"  # SECRETS-GUARD-IGNORE: public ruleset identifier, not a credential
DATE = "2026-11-07"
SEEDS = list(mission.MissionEnv.EVAL)
SCENARIOS = tuple(recovery.SCENARIOS)
BEHAVIORS = recovery.BEHAVIORS + (recovery.AUTO,)  # SECRETS-GUARD-IGNORE: behavior expression, not a credential
POSE_MODES = {"true_pose": False, "ekf_pose": True}
INPUTS = ["tools/evaluate-recovery-v1.py", "software/stockcar/recovery.py",
          "software/stockcar/study_stats.py", "software/stockcar/recovery_sim.py", "software/stockcar/mission_avoid.py",
          "software/stockcar/mission_sensed.py", "software/stockcar/mission.py",
          "software/stockcar/supervisor.py", "software/stockcar/lapmodel.py",
          "software/stockcar/passage.py", "software/stockcar/field.py",
          "software/stockcar/obstacles.py", "software/stockcar/geometry.py",
          "software/stockcar/sensors_camera.py", "software/stockcar/sensors.py",
          "software/stockcar/estimator.py", "software/stockcar/avoidance.py",
          "software/stockcar/lane_profile.py", "software/stockcar/sensors_vehicle.py",
          "derived/organizer-cad-v10/field-v10.json"]


def cell_of(rows, scenario, behavior, pose):
    runs = [r for r in rows if r["scenario"] == scenario and r["behavior"] == behavior
            and r["pose_mode"] == pose]
    recovered = sum(1 for r in runs if r["outcome"] == "recovered")
    recovered_contact = sum(1 for r in runs if r["outcome"] == "recovered_contact")
    blocked = sum(1 for r in runs if r["outcome"] == "blocked")
    stopped = sum(1 for r in runs if r["outcome"] == "stopped")
    incomplete = sum(1 for r in runs if r["outcome"] == "incomplete")
    passed = recovered + recovered_contact
    return {"scenario": scenario, "behavior": behavior, "pose_mode": pose, "runs": len(runs),
            "completed": sum(1 for r in runs if r["state"] == "DONE"), "passed_blocker": passed,
            "recovered": recovered, "recovered_contact": recovered_contact, "blocked": blocked,
            "stopped": stopped, "incomplete": incomplete, "passed_wilson95": wilson(passed, len(runs)),
            "mean_time_s": round(sum(r["time_s"] for r in runs) / len(runs), 2)}


def main():
    rows = []
    entries = []
    units = []
    baseline = {}
    for pose, sensing in POSE_MODES.items():
        for seed in SEEDS:
            info = run_recovery(seed, scenario=None, behavior="stall_stop", sensing=sensing)
            baseline[f"{pose}:{seed}"] = {"pose_mode": pose, "seed": seed,
                                          "completed": info["state"] == "DONE",
                                          "planned_contact_vehicles": info["planned_contact_vehicles"],
                                          "lane_modes": info["lane_modes"]}
    for scenario in SCENARIOS:
        for pose, sensing in POSE_MODES.items():
            for seed in SEEDS:
                auto_outcome = None
                for behavior in BEHAVIORS:
                    info = run_recovery(seed, scenario=scenario, behavior=behavior, sensing=sensing)
                    outcome = recovery.outcome_of(info)
                    if behavior == recovery.AUTO:
                        auto_outcome = outcome
                    entries.append(recovery.make_entry(WORLD, scenario, behavior, pose, seed, info))
                    rows.append({"scenario": scenario, "behavior": behavior, "pose_mode": pose,
                                 "seed": seed, "state": info["state"], "outcome": outcome,
                                 "time_s": info["time_s"]})
                base = baseline[f"{pose}:{seed}"]
                units.append({"scenario": scenario, "pose_mode": pose, "seed": seed,
                              "baseline_completed": 1 if base["completed"] else 0,
                              "router_pass": 1 if base["planned_contact_vehicles"] == 0 else 0,
                              "router_planned_contacts": base["planned_contact_vehicles"],
                              "recovery_success": 1 if auto_outcome in ("recovered", "recovered_contact") else 0})

    cells = [cell_of(rows, s, b, p) for s in SCENARIOS for b in BEHAVIORS for p in POSE_MODES]
    xs_succ = [u["recovery_success"] for u in units]
    xs_pass = [u["router_pass"] for u in units]
    xs_contacts = [u["router_planned_contacts"] for u in units]
    rho_pass = spearman(xs_succ, xs_pass)
    rho_contacts = spearman(xs_succ, xs_contacts)
    passed = [u for u in units if u["router_pass"] == 1]
    failed = [u for u in units if u["router_pass"] == 0]
    clusters = [(u["pose_mode"], u["seed"]) for u in units]
    strata = [u["pose_mode"] for u in units]
    p_pass = clustered_permutation_p(xs_succ, xs_pass, rho_pass, clusters, strata)
    p_contacts = clustered_permutation_p(xs_succ, xs_contacts, rho_contacts, clusters, strata)
    association = {
        "units": len(units),
        "independent_clusters": len(set(clusters)),
        "scenario_rows_per_cluster": len(SCENARIOS),
        "permutation_shuffles": 10000,
        "permutation_seed": 7,
        "method": "midrank Spearman; two-sided permutation of whole pose/seed baseline clusters within pose",
        "router_pass_definition": "unblocked v10 route has planned_contact_vehicles == 0 (not baseline completion)",
        "recovery_success_vs_router_pass_spearman": None if rho_pass is None else round(rho_pass, 4),
        "recovery_success_vs_router_pass_p": None if p_pass is None else round(p_pass, 6),
        "recovery_success_vs_planned_contacts_spearman":
            None if rho_contacts is None else round(rho_contacts, 4),
        "recovery_success_vs_planned_contacts_p": None if p_contacts is None else round(p_contacts, 6),
        "recovery_success_among_router_pass_rows":
            None if not passed else round(sum(u["recovery_success"] for u in passed) / len(passed), 4),
        "recovery_success_among_router_fail_rows":
            None if not failed else round(sum(u["recovery_success"] for u in failed) / len(failed), 4),
        "note": "40 independent pose/seed baseline clusters repeat across eight scenarios; pooled row "
                "rates are descriptive, not 320 independent observations. Null statistics indicate no "
                "rank variance and are reported rather than treated as evidence.",
    }

    report = {"version": "0.1.0", "date": DATE,
              "status": "agent-run synthetic study; blocker positions, yaw and vehicle size are assumptions",
              "world": WORLD, "seeds": SEEDS, "cells": cells, "association": association,
              "baseline": {"pose_modes": {
                  p: {"runs": len(SEEDS),
                      "completed": sum(1 for s in SEEDS if baseline[f"{p}:{s}"]["completed"]),
                      "completion_wilson95": wilson(
                          sum(1 for s in SEEDS if baseline[f"{p}:{s}"]["completed"]), len(SEEDS)),
                      "router_passes": sum(
                          1 for s in SEEDS if baseline[f"{p}:{s}"]["planned_contact_vehicles"] == 0),
                      "router_pass_wilson95": wilson(
                          sum(1 for s in SEEDS if baseline[f"{p}:{s}"]["planned_contact_vehicles"] == 0),
                          len(SEEDS)),
                      "mean_planned_contacts": round(
                          sum(baseline[f"{p}:{s}"]["planned_contact_vehicles"] for s in SEEDS) / len(SEEDS), 2)}
                  for p in POSE_MODES}}}

    summary = [
        "# Blocked-route recovery v1: behaviors and the router-pass link",
        "",
        f"{DATE}. Agent-run synthetic study (seeds 100-119, world {WORLD}). Eight scenarios inject one "
        "guide-plush blocker — four corridor-spanning, four against a wall that leave a passable band; "
        "each seed also runs the unblocked baseline so the recovery success and the router pass are "
        "paired on every seed.",
        "",
        "| scenario | behavior | pose | completed | passed blocker | recovered | w/ contact | blocked | stopped | incomplete | passed Wilson95 | mean s |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|",
    ]
    for c in cells:
        lo, hi = c["passed_wilson95"]
        summary.append(f"| {c['scenario']} | {c['behavior']} | {c['pose_mode']} | {c['completed']}/{c['runs']} "
                       f"| {c['passed_blocker']} | {c['recovered']} | {c['recovered_contact']} | {c['blocked']} "
                       f"| {c['stopped']} | {c['incomplete']} | {lo}..{hi} | {c['mean_time_s']} |")
    a = report["association"]
    summary += [
        "",
        "## Router-pass association",
        "",
        f"Units: {a['units']} (scenario x pose x seed). Recovery success is 'passed the injected "
        "blocker'. "
        f"Spearman(recovery success, router pass) = "
        f"{a['recovery_success_vs_router_pass_spearman']} (permutation p = "
        f"{a['recovery_success_vs_router_pass_p']}); Spearman(recovery success, router planned contacts) = "
        f"{a['recovery_success_vs_planned_contacts_spearman']} (p = "
        f"{a['recovery_success_vs_planned_contacts_p']}). Recovery success among router-pass rows "
        f"{a['recovery_success_among_router_pass_rows']}; among router-fail rows "
        f"{a['recovery_success_among_router_fail_rows']}. Method: {a['method']}. {a['note']}",
        "",
        "## Implementation notes (honest deviations from the plan)",
        "",
        "- Only three expressible behaviors plus `auto` were studied: `backtrack` and `pit_bypass` are "
        "not expressible in the v10 oval route model (a kinematic forward follower; the field's single "
        "pit connection opens at the west end, so a mid-straight blocker cannot be detoured around). "
        "`stall_stop` is realized as the status-quo plan plus a blocker-local freeze that the "
        "supervisor stall watchdog then stops; a blanket collision-stop would also freeze ordinary "
        "quadrant-vehicle contacts that the sealed avoid/rl baselines tolerate. Recovery detection uses "
        "truth lane positions (`oracle`); a sensed-detection variant is a follow-on. Passage requires a "
        "directional crossing on the LAP route within the blocked corridor, so start/pit positions on "
        "the high side cannot be mistaken for a successful recovery.",
    ]

    files = {"report.json": json.dumps(report, indent=1) + "\n", "summary.md": "\n".join(summary) + "\n"}
    OUT.mkdir(parents=True, exist_ok=True)
    DR.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (OUT / name).write_text(text, encoding="utf-8")
    manifest = {"date": DATE, "status": report["status"],
                "input_hashes": {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in INPUTS},
                "output_hashes": {n: hashlib.sha256(t.encode("utf-8")).hexdigest() for n, t in files.items()}}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    registry_text = json.dumps(entries, indent=1) + "\n"
    (DR / "registry.json").write_text(registry_text, encoding="utf-8")
    physical_path = DR / "physical-observations.json"
    if not physical_path.exists():
        physical_path.write_text("[]\n", encoding="utf-8")
    dr_manifest = {"date": DATE, "access": "computer-only",
                   "note": "Sim entries are written only by tools/evaluate-recovery-v1.py; physical "
                           "observations are appended by the owner through tools/dr-registry.js "
                           "add-physical. The robot has no read or write path to this registry.",
                   "registry_sha256": hashlib.sha256(registry_text.encode("utf-8")).hexdigest(),
                   "sim_entry_count": len(entries)}
    (DR / "manifest.json").write_text(json.dumps(dr_manifest, indent=2) + "\n", encoding="utf-8")

    print(f"wrote {OUT.relative_to(ROOT)}: {len(cells)} cells x 20 runs, {len(entries)} DR entries")


if __name__ == "__main__":
    main()