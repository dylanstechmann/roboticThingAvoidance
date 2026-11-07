"""Inputs and deterministic screening arithmetic for the sim-to-real v1 study.

The result is an E03-gate transfer index, not a physical full-mission pass probability. Git is used
only to read immutable world-branch seals; this module never checks out or modifies a branch.
"""
import csv
import hashlib
import json
import math
import pathlib
import random
import subprocess

from stockcar.study_stats import quantile, wilson

WORLDS = (
    "world-ccw-line-sq-adv-align", "world-ccw-gate-sq-adv-align",
    "world-ccw-line-rd-adv-align", "world-ccw-gate-rd-adv-align",
    "world-ccw-line-sq-adv-yaw", "world-cw-line-sq-adv-align",
)
POLICIES = ("classical", "learned", "random")
E03_COLUMNS = (
    "trial_id", "surface_id", "support_configuration", "mass_kg", "run_type", "direction", "repeat",
    "duration_s", "drift_mm", "spin_error_deg", "max_speed_in_s", "slip_observed",
    "thermal_or_protection_fault", "notes", "session_id", "configuration_id", "recorded_at",
    "operator_id", "instrument_ids", "calibration_check_id", "setup_record_id", "control_revision",
    "warmup_record_id", "uncertainty_record_id", "raw_observation_ref", "attempt_status",
    "exclusion_reason", "replaces_trial_id",
)
PROVENANCE = (
    "session_id", "configuration_id", "recorded_at", "operator_id", "instrument_ids",
    "calibration_check_id", "setup_record_id", "control_revision", "warmup_record_id",
    "uncertainty_record_id", "raw_observation_ref",
)


def _git(root, *args):
    result = subprocess.run(["git", "-c", f"safe.directory={root}", *args], cwd=root,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False)
    if result.returncode:
        raise RuntimeError(f"git {' '.join(args)} failed: {result.stderr.decode('utf-8', 'replace').strip()}")
    return result.stdout


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def load_world_sources(root):
    """Read and fully validate the six sealed RL-v3 reports at their current branch commits."""
    root = pathlib.Path(root).resolve()
    sources = []
    for world in WORLDS:
        commit = _git(root, "rev-parse", "--verify", f"refs/heads/{world}^{{commit}}").decode().strip()
        prefix = f"derived/rl-v3/{world}"
        report_bytes = _git(root, "show", f"{commit}:{prefix}/report.json")
        manifest_bytes = _git(root, "show", f"{commit}:{prefix}/manifest.json")
        summary_bytes = _git(root, "show", f"{commit}:{prefix}/summary.md")
        report = json.loads(report_bytes)
        manifest = json.loads(manifest_bytes)
        if manifest.get("world") != world or report.get("world") != world:
            raise ValueError(f"world identity mismatch in {world} seal")
        for name, expected in manifest["input_hashes"].items():
            if _sha(_git(root, "show", f"{commit}:{name}")) != expected:
                raise ValueError(f"stale source input {world}:{name}")
        outputs = {"report.json": report_bytes, "summary.md": summary_bytes}
        for name, expected in manifest["output_hashes"].items():
            if name not in outputs or _sha(outputs[name]) != expected:
                raise ValueError(f"stale source output {world}:{name}")
        cells = report.get("results", [])
        if {r["policy"] for r in cells} != set(POLICIES) or len(cells) != 3:
            raise ValueError(f"{world}: classical/learned/random cells required")
        for cell in cells:
            if cell["runs"] != 20 or not 0 <= cell["completed"] <= cell["runs"]:
                raise ValueError(f"{world}: invalid policy run counts")
        sources.append({"world": world, "source_branch": world, "source_commit": commit,
                        "source_report_sha256": _sha(report_bytes),
                        "source_manifest_sha256": _sha(manifest_bytes), "report": report})
    return sources

def read_e03(path, root):
    """Read completed measurements from an existing E03 CSV; never invent missing measurements."""
    root = pathlib.Path(root).resolve()
    resolved = pathlib.Path(path).resolve()
    try:
        relative = resolved.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("E03 CSV must live inside the repository") from exc
    raw = resolved.read_bytes()
    with resolved.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        if tuple(reader.fieldnames or ()) != E03_COLUMNS:
            raise ValueError("E03 CSV must use the existing 27-column template")
        rows = list(reader)
    completed = [r for r in rows if r["attempt_status"] == "completed"]
    if not completed:
        raise ValueError("E03 CSV has no completed trials")
    for row in completed:
        if not row["surface_id"] or row["surface_id"] == "DOCUMENT_SURFACE":
            raise ValueError("E03 completed trials need an actual surface_id")
        for key in PROVENANCE:
            if not row[key].strip():
                raise ValueError(f"{row['trial_id']}: provenance {key} required")
    drift, spins = [], []
    for row in completed:
        try:
            if row["run_type"] == "straight":
                drift.append(float(row["drift_mm"]))
            elif row["run_type"] == "spin":
                spins.append(float(row["spin_error_deg"]))
            else:
                raise ValueError(f"{row['trial_id']}: unknown run_type")
        except (TypeError, ValueError) as exc:
            raise ValueError(f"{row['trial_id']}: numeric drift/spin measurement required") from exc
    if not drift or not spins:
        raise ValueError("E03 analysis needs completed straight and spin measurements")
    if not all(math.isfinite(v) for v in drift + spins):
        raise ValueError("E03 drift/spin measurements must be finite")
    provenance = {"path": relative, "sha256": _sha(raw), "completed_rows": len(completed),
                  "straight_count": len(drift), "spin_count": len(spins),
                  "surface_ids": sorted({r["surface_id"] for r in completed}),
                  "configuration_ids": sorted({r["configuration_id"] for r in completed})}
    return {"drift_mm": drift, "spin_error_deg": spins, "provenance": provenance}


def expected_draws(completed, runs, drift, spins, tolerances, n_draws=10000, seed=7):
    """Jeffreys sim posterior times an empirical E03 geometry-survival indicator."""
    if runs < 1 or not 0 <= completed <= runs:
        raise ValueError("require runs > 0 and 0 <= completed <= runs")
    if not drift or not spins or n_draws < 1:
        raise ValueError("non-empty drift/spin samples and positive draw count required")
    rng = random.Random(seed)
    drift_limit, spin_limit = tolerances["drift_mm"], tolerances["spin_deg"]
    draws = []
    for _ in range(n_draws):
        p_sim = rng.betavariate(completed + 0.5, runs - completed + 0.5)
        survives = abs(rng.choice(drift)) <= drift_limit and abs(rng.choice(spins)) <= spin_limit
        draws.append(p_sim if survives else 0.0)
    return draws


def summarize(values):
    return {key: round(quantile(values, q), 6)
            for key, q in (("p50", 0.5), ("p2_5", 0.025), ("p97_5", 0.975))}


def draw_seed(world, policy):
    digest = hashlib.sha256(f"20261107:{world}:{policy}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def make_records(sources, samples, corridor_width_in, tolerances, n_draws=10000):
    """Create the 18 report records from validated source cells and one common sample set."""
    records = []
    for source in sources:
        for cell in source["report"]["results"]:
            world, policy = source["world"], cell["policy"]
            completed, runs = cell["completed"], cell["runs"]
            seed = draw_seed(world, policy)
            expected = summarize(expected_draws(completed, runs, samples["drift_mm"],
                                                samples["spin_error_deg"], tolerances, n_draws, seed))
            sim_rate = round(completed / runs, 4)
            records.append({
                "world": world, "policy": policy, "source_branch": source["source_branch"],
                "source_commit": source["source_commit"],
                "source_report_sha256": source["source_report_sha256"],
                "sim_completed": completed, "sim_runs": runs, "sim_pass_rate": sim_rate,
                "sim_pass_wilson95": wilson(completed, runs), "n_draws": n_draws, "draw_seed": seed,
                "drift_source": samples["source"], "provisional": samples["provisional"],
                "e03_sample_counts": {"straight": len(samples["drift_mm"]),
                                      "spin": len(samples["spin_error_deg"])},
                "drift_mm_1m": summarize(samples["drift_mm"]),
                "spin_error_deg_360": summarize(samples["spin_error_deg"]),
                "corridor_width_in": corridor_width_in, "tolerances": dict(tolerances),
                "expected_physical_pass": expected,
                "fragile": sim_rate >= 0.8 and expected["p2_5"] < 0.5,
            })
    return records
