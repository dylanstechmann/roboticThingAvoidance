"""Seal the six-world sim-to-real E03-gate transfer screening study.

Without --e03, drift/spin samples come from the provisional host plant and are loudly synthetic.
With --e03 PATH, all completed measurements in that repo-relative E03 CSV are used. Neither mode is a
physical full-mission qualification. World reports are read from immutable world-branch Git objects.

Usage: uv run --no-project --python 3.12 python -B -I tools/evaluate-simreal-v1.py [--e03 PATH]
"""
import argparse
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "software"))
from stockcar import simreal  # noqa: E402
from stockcar.field import Field  # noqa: E402

OUT = ROOT / "derived" / "simreal-v1"
DATE = "2026-11-07"
BASE_INPUTS = [
    "tools/evaluate-simreal-v1.py", "software/stockcar/simreal.py",
    "software/stockcar/study_stats.py", "software/stockcar/field.py",
    "derived/organizer-cad-v10/field-v10.json", "drivetrain-mule-v4.json",
]
PLANT_INPUTS = [
    "firmware/pico2/config.py", "firmware/pico2/floor_e03.py", "firmware/pico2/runner.py",
    "firmware/pico2/drive.py", "firmware/pico2/motor.py", "firmware/pico2/safety.py",
    "firmware/pico2/telemetry.py", "firmware/host_tests/fakes.py",
    "firmware/host_tests/plant_hal.py", "software/stockcar/dynamics.py",
    "software/stockcar/envelope.py", "software/stockcar/lapmodel.py",
    "software/stockcar/tests/fixtures/dynamics-golden-v10.json",
]


def provisional_samples():
    """Run the E03 host methods against a fixed synthetic plant grid; no hardware is touched."""
    for directory in (ROOT / "firmware", ROOT / "firmware" / "pico2"):
        sys.path.insert(0, str(directory))
    import floor_e03  # noqa: E402
    from host_tests.plant_hal import PlantHal  # noqa: E402
    from runner import Runner  # noqa: E402

    drift, spins, straight_rows, spin_rows = [], [], [], []
    for mass in (2.0, 4.0, 6.0):
        for friction in (0.20, 0.25, 0.30):
            hal = PlantHal(11.1, friction, mass)
            result = floor_e03.straight(Runner(hal, mode="DRIVE"), speed_in_s=8.0, length_m=1.0)
            if result["result"] != "completed":
                raise RuntimeError(f"provisional straight did not complete: {result}")
            value = hal.state["y"] * 1000.0
            drift.append(value)
            straight_rows.append({"mass_kg": mass, "friction": friction, "source_v": 11.1,
                                  "drift_mm": round(value, 6)})
            for direction, target in (("left", 360.0), ("right", -360.0)):
                hal = PlantHal(11.1, friction, mass)
                result = floor_e03.spin(Runner(hal, mode="DRIVE"), direction,
                                        yaw_rate_rad_s=2.0, revolutions=1.0)
                if result["result"] != "completed":
                    raise RuntimeError(f"provisional spin did not complete: {result}")
                error = result["yaw_deg"] - target
                spins.append(error)
                spin_rows.append({"mass_kg": mass, "friction": friction, "source_v": 11.1,
                                  "direction": direction, "spin_error_deg": round(error, 6)})
    return {"source": "provisional-plant", "provisional": True,
            "basis": {"drift": "plant body lateral y after the 1 m straight; synthetic, not tape",
                      "spin": "encoder wheel-differential yaw minus commanded 360 deg; synthetic, not tape"},
            "parameters": {"masses_kg": [2, 4, 6], "frictions": [0.20, 0.25, 0.30], "source_v": 11.1,
                           "support_configurations_modeled": False},
            "drift_mm": drift, "spin_error_deg": spins,
            "straight_samples": straight_rows, "spin_samples": spin_rows}

def measured_samples(path):
    measured = simreal.read_e03(path, ROOT)
    return {"source": f"e03:{measured['provenance']['path']}", "provisional": False,
            "basis": {"drift": "owner-recorded completed E03 straight drift_mm",
                      "spin": "owner-recorded completed E03 spin_error_deg"}, **measured}


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--e03", help="repo-relative completed E03 CSV; default is provisional host plant")
    args = parser.parse_args()
    samples = measured_samples(args.e03) if args.e03 else provisional_samples()
    sources = simreal.load_world_sources(ROOT)
    gates = json.loads((ROOT / "drivetrain-mule-v4.json").read_text())["gates"]
    tolerances = {"drift_mm": float(gates["maximum_straight_drift_mm"]),
                  "spin_deg": float(gates["median_spin_error_deg"])}
    low, high = Field().corridor("low"), Field().corridor("high")
    if low[1] - low[0] != high[1] - high[0]:
        raise ValueError("simreal scalar corridor width requires symmetric straightaways")
    records = simreal.make_records(sources, samples, low[1] - low[0], tolerances)
    report = {"version": "0.1.0", "date": DATE,
              "status": "agent-run E03-gate transfer screening; not physical full-mission qualification",
              "model": {"draws": 10000, "sim_posterior": "Jeffreys Beta(completed+0.5, failures+0.5)",
                        "geometry": "independent empirical bootstrap of completed drift and spin samples",
                        "fragile_rule": "sim_pass_rate >= 0.8 and expected_physical_pass.p2_5 < 0.5",
                        "limitation": "not a full-mission physical-pass probability"},
              "records": records}
    summary = ["# Sim-to-real v1: E03-gate transfer screening", "",
               f"{DATE}. Agent-run screening over six sealed worlds and three policies. Source: "
               f"`{samples['source']}` ({'PROVISIONAL SYNTHETIC PLANT' if samples['provisional'] else 'completed E03 measurements'}). "
               "This is not a full-mission physical-pass probability and is not hardware qualification.", "",
               "| world | policy | sim pass | expected p50 | p2.5 | p97.5 | fragile |",
               "|---|---|---:|---:|---:|---:|---|"]
    for r in records:
        e = r["expected_physical_pass"]
        summary.append(f"| {r['world']} | {r['policy']} | {r['sim_completed']}/{r['sim_runs']} "
                       f"| {e['p50']} | {e['p2_5']} | {e['p97_5']} | {str(r['fragile']).lower()} |")
    summary += ["", "Each draw combines a Jeffreys-posterior sim rate with independent bootstrapped "
                "E03 drift/spin samples. The empirical samples are few and are not a validated error "
                "distribution; percentiles do not include sensing, placement, model or full-route "
                "exposure uncertainty. Source commits and all source-seal hashes are in the manifest."]
    if samples["provisional"]:
        summary += ["", f"Provisional grid maxima: |drift| {max(abs(v) for v in samples['drift_mm']):.6g} mm; "
                    f"|spin error| {max(abs(v) for v in samples['spin_error_deg']):.6g} deg. The symmetric "
                    "plant's near-zero lateral drift is a model limitation. No fragile flags under this "
                    "input is not evidence that the physical robot is robust."]
    files = {"report.json": json.dumps(report, indent=1) + "\n",
             "summary.md": "\n".join(summary) + "\n",
             "drift-samples.json": json.dumps(samples, indent=1) + "\n"}
    OUT.mkdir(parents=True, exist_ok=True)
    for name, text in files.items():
        (OUT / name).write_text(text, encoding="utf-8")
    inputs = BASE_INPUTS + ([] if args.e03 else PLANT_INPUTS)
    if args.e03:
        inputs.append(samples["provenance"]["path"])
    source_commits = [{k: v for k, v in s.items() if k != "report"} for s in sources]
    manifest = {"date": DATE, "status": report["status"],
                "input_hashes": {f: hashlib.sha256((ROOT / f).read_bytes()).hexdigest() for f in inputs},
                "output_hashes": {n: hashlib.sha256(t.encode()).hexdigest() for n, t in files.items()},
                "source_commits": source_commits}
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(ROOT)}: {len(records)} records, source {samples['source']}")


if __name__ == "__main__":
    main()
