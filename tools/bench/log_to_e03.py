"""Turn one floor_e03 log (telemetry v1 JSON Lines) into one E03-floor-trial CSV row.

The row records what the log measured (the trial duration from the DRIVE records, the maximum
straight-line speed, any fault stop) and links the raw log by SHA-256. Everything the log cannot
know stays blank for the operator: the surface, the tape-measured drift or spin error, the slip
observation, and the provenance columns. Nothing is invented. Append the printed row to your copy
of the E03 template under measurements/, set attempt_status once the row is complete, then check
it with node tools/mule-measurements-v10.js --kind E03 --input <copy> --output <new> --progress.

Usage: python -I tools/bench/log_to_e03.py --support dual-front-rear|front-only|rear-only --mass 2|4|6
       --kind straight|spin --direction forward|left|right --repeat N LOG.jsonl
"""
import argparse
import csv
import hashlib
import io
import json
import math
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
sys.path.insert(0, str(ROOT / "firmware" / "pico2"))
import config  # noqa: E402  firmware constants; the wheel radius must match the firmware that made the log
import telemetry_schema  # noqa: E402

COLUMNS = ["trial_id", "surface_id", "support_configuration", "mass_kg", "run_type", "direction", "repeat",
           "duration_s", "drift_mm", "spin_error_deg", "max_speed_in_s", "slip_observed", "thermal_or_protection_fault",
           "notes", "session_id", "configuration_id", "recorded_at", "operator_id", "instrument_ids",
           "calibration_check_id", "setup_record_id", "control_revision", "warmup_record_id", "uncertainty_record_id",
           "raw_observation_ref", "attempt_status", "exclusion_reason", "replaces_trial_id"]

IN_TO_M = 0.0254


def body_speed_in_s(record):
    if record["rpm"][0] is None or record["rpm"][1] is None:
        return None
    mean_rpm = (record["rpm"][0] + record["rpm"][1]) / 2.0
    return mean_rpm / 60.0 * 2.0 * math.pi * config.WHEEL_RADIUS_M / IN_TO_M


def row_from_log(text, log_name, support, mass, kind, direction, repeat):
    lines = text.splitlines()
    problems = telemetry_schema.validate_lines(lines)
    if problems:
        raise SystemExit(f"{log_name}: {problems[0]}")
    records = [json.loads(line) for line in lines if line.strip()]
    drive = [r for r in records if r["mode"] == "DRIVE"]
    if len(drive) < 2:
        raise SystemExit(f"{log_name}: need at least two DRIVE records to time a trial")
    span_ms = drive[-1]["t_ms"] - drive[0]["t_ms"]
    period_ms = span_ms / (len(drive) - 1)
    duration_s = (span_ms + period_ms) / 1000.0
    stops = sorted({r["stop_reason"] for r in records if r["stop_reason"] not in (None, "not_armed")})
    row = {c: "" for c in COLUMNS}
    if kind == "straight":
        trial_id = f"E03-{support}-{mass}-straight-{repeat}"
        speeds = [s for s in (body_speed_in_s(r) for r in drive) if s is not None]
        measured = f"max_speed_in_s {max(speeds):.2f} from the wheel-rpm records; " if speeds else ""
        row["max_speed_in_s"] = f"{max(speeds):.2f}" if speeds else ""
    else:
        trial_id = f"E03-{support}-{mass}-spin-{direction}-{repeat}"
        measured = ""
    row.update({
        "trial_id": trial_id,
        "support_configuration": support, "mass_kg": str(mass),
        "run_type": kind, "direction": direction, "repeat": str(repeat),
        "duration_s": f"{duration_s:.2f}",
        "thermal_or_protection_fault": "true" if stops and stops != ["auto_stop"] else "",
        "notes": "duration_s from the DRIVE-record t_ms span plus one telemetry period; " + measured
                 + (f"stop reasons: {', '.join(stops)}" if stops else "no stop reason logged"),
        "raw_observation_ref": f"{log_name} sha256:{hashlib.sha256(text.encode('utf-8')).hexdigest()}",
    })
    return row


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--support", choices=["dual-front-rear", "front-only", "rear-only"], required=True)
    parser.add_argument("--mass", type=int, choices=[2, 4, 6], required=True)
    parser.add_argument("--kind", choices=["straight", "spin"], required=True)
    parser.add_argument("--direction", choices=["forward", "left", "right"], required=True)
    parser.add_argument("--repeat", type=int, required=True)
    parser.add_argument("log")
    args = parser.parse_args(argv)
    if args.kind == "straight" and args.direction != "forward":
        raise SystemExit("straight trials take --direction forward")
    if args.kind == "spin" and args.direction not in ("left", "right"):
        raise SystemExit("spin trials take --direction left or right")
    limit = 10 if args.kind == "straight" else 20
    if not 1 <= args.repeat <= limit:
        raise SystemExit(f"--repeat must be 1..{limit} for {args.kind} trials")
    text = pathlib.Path(args.log).read_text(encoding="utf-8")
    row = row_from_log(text, pathlib.Path(args.log).name, args.support, args.mass, args.kind, args.direction, args.repeat)
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=COLUMNS, lineterminator="\n")
    writer.writerow(row)
    sys.stdout.write(buffer.getvalue())
    return row


if __name__ == "__main__":
    main()