# Implementation Plan

[Overview]

Add the missing E03 floor-trial path to the Pico 2 mule firmware and its host tooling — a closed-loop, sensor-free trial runner (`straight` and `spin`), a REPL entry in `main.py`, a host log-to-CSV tool matching the sealed E03 measurement contract, plant-backed host tests, and documentation — so the owner can run the BACKCAST G1 deliverable "E03 floor trials" (due Dec 6) as soon as the bench kit is wired and E02A/E02 are done.

Scope and context:

- The E03 analysis contract already exists and is sealed: `node tools/mule-measurements-v10.js --kind E03` (wrapping the pinned v4 analyzer) consumes copies of `derived/drivetrain-mule-v10/templates/E03-trials.csv` — 450 planned rows: 9 cells (3 support configurations `dual-front-rear|front-only|rear-only` × mass cases 2/4/6 kg), 50 trials per cell (10 straight + 20 left + 20 right). Gates in `drivetrain-mule-v10.json`: qualifying mass 4 kg, cruise speed 8 in/s, 1 m straight length, at most 25 mm drift with at least 9/10 passes, median spin error at most 5°.
- The E02 chain to mirror end-to-end: firmware `bench_e02.py` (open-loop duty steps, RAM telemetry, writes `/e02-<run>.jsonl` after the motors stop) → host `tools/bench/log_to_e02.py` (one CSV row: log-derivable fields filled, human-measured fields left blank, nothing invented) → the owner appends the row to their copy of the template.
- What is missing is the middle of the E03 chain: no firmware trial runner exists (`grep -i e03 firmware/` finds only a comment) and there is no `log_to_e03.py`.
- Deliberately out of scope: the estimator/mission path. `mission_driver.py` documents that `main.py` cannot start missions until the sensors are chosen (G2 concept review, Dec 13); the on-board EKF stays unwired, and `hal.py`'s sensor reads (`read_gyro` etc.) stay `NotImplementedError`. E03 needs no gyro, reflectance, or ToF — drift and spin error are physical (tape) measurements; the firmware uses encoder odometry only.
- `derived/drivetrain-mule-v10/**` is tool-generated and hash-verified (`tools/verify-drivetrain-mule-v10.js`) and is not edited. `tools/mule-measurements-v4.js` (pinned by the sealed v4 manifest) and `-v10.js` (its wrapper) are not edited. `schemas/telemetry-v1.json` is unchanged — floor runs log under the existing `DRIVE` mode.
- Verified facts this design rests on: encoder signs are applied in the PIO layer on device (`PioEncoder(..., LEFT/RIGHT_ENCODER_SIGN)`), so count deltas are forward-positive on both sides and integrate directly; the DriveShaper ramps body speed at `MAX_ACCEL_M_S2`/`MAX_BRAKE_M_S2` and yaw at `MAX_YAW_ACCEL_RAD_S2` (4.5), and its pure-spin ceiling is `MAX_WHEEL_RPM`-derived ≈ 4.15 rad/s; a 2 rad/s spin needs only ~0.202 m/s wheel speed (~48 rpm), well inside the envelope.
- All work on the `ai-orchestration` branch. `main` and the eight world branches are untouched. No new dependencies. MicroPython lint and the full `check-all` gate must pass.

[Types]

1. Trial parameters and results (`firmware/pico2/floor_e03.py`)

   - Speeds in in/s and yaw rates in rad/s (matching `mission_driver.py` and the E03 vocabulary); lengths in m; durations in s; conversions to SI inside the module (1 in/s = 0.0254 m/s).
   - `straight(runner, speed_in_s=8.0, length_m=1.0)` returns `{"result", "length_m", "distance_m", "duration_s", "yaw_deg", "stop_reason"}`.
   - `spin(runner, direction, yaw_rate_rad_s=2.0, revolutions=1.0)` returns the same shape; `direction` is `"left"` (positive/CCW yaw — the shaper speeds the right wheel for +yaw) or `"right"`.
   - Telemetry records use mode `"DRIVE"` (schema `schemas/telemetry-v1.json` unchanged; 50 Hz records, 3000-record buffer ≈ 60 s — no wrap for ~10 s trials).

2. E03 CSV row (`tools/bench/log_to_e03.py`)

   - Columns exactly the `E03-trials.csv` header order: `trial_id, surface_id, support_configuration, mass_kg, run_type, direction, repeat, duration_s, drift_mm, spin_error_deg, max_speed_in_s, slip_observed, thermal_or_protection_fault, notes, session_id, configuration_id, recorded_at, operator_id, instrument_ids, calibration_check_id, setup_record_id, control_revision, warmup_record_id, uncertainty_record_id, raw_observation_ref, attempt_status, exclusion_reason, replaces_trial_id`.
   - trial_id per template: straight `E03-<support>-<mass>-straight-<repeat>` (direction column `forward`); spin `E03-<support>-<mass>-spin-<left|right>-<repeat>`.
   - Prefilled (firmware-derivable): trial_id, support_configuration, mass_kg, run_type, direction, repeat, duration_s, max_speed_in_s (straight only), thermal_or_protection_fault, notes, raw_observation_ref (`<log name> sha256:<hex>`).
   - Left blank for the owner (the validator rejects placeholders by design): surface_id, drift_mm, spin_error_deg, slip_observed, session_id, configuration_id, recorded_at, operator_id, instrument_ids, calibration_check_id, setup_record_id, control_revision, warmup_record_id, uncertainty_record_id, attempt_status, exclusion_reason, replaces_trial_id.

[Files]

New files:

- `firmware/pico2/floor_e03.py` — closed-loop floor trials with braking-lookahead stopping (details in [Functions]); arm/stop and telemetry save mirror `bench_e02.py`; parameters validated against the `config.py` envelope; no `machine` imports (lint-clean); hardware-independent so host tests run it against `PlantHal`/`FakeHal`.
- `firmware/host_tests/test_floor_e03.py` — plant-backed trials with ground-truth comparison, safety latches, parameter validation, and the log-tool row shape.
- `tools/bench/log_to_e03.py` — one E03 CSV row per log, mirroring `log_to_e02.py` (argparse CLI, row printed to stdout via `csv.DictWriter`).

Modified files:

- `firmware/pico2/main.py` — add a `floor(...)` REPL entry mirroring `bench()`: builds `Runner(PicoHal(), mode="DRIVE")`, runs straight or spin, writes `/e03-<run_id>.jsonl`, prints the summary. The boot default stays IDLE (motors disabled).
- `firmware/README.md` — layout-table rows for `floor_e03.py` and the new entry; an "E03 floor data flow" section (board REPL → `/e03-<id>.jsonl` → `log_to_e03.py` → the owner's `E03-trials.csv` copy → `mule-measurements-v10 --kind E03`); a safety bullet: floor trials run wheels-on-ground in a cleared area with the e-stop accessible, only after E02A/E02 under an approved setup; note the sensor-free design (no gyro needed; drift and spin error are physical measurements).
- `PROJECT-STATUS.md` — extend the November 7 review paragraph with one sentence on the E03 firmware/tooling addition.
- `SESSION-STATE-2026-11-07.md` — short note recording the E03 addition and that the mission/estimator path stays blocked on sensor selection.
- `implementation_plan.md` — replaced by this document.

Files not modified:

- `derived/drivetrain-mule-v10/**` (tool-generated, hash-verified), `tools/mule-measurements-v4.js` and `tools/mule-measurements-v10.js` (sealed analyzer contract), the CSV templates, `schemas/telemetry-v1.json` (reuse `DRIVE`), `firmware/pico2/{estimator,mission_driver,hal,runner,drive,motor,safety,telemetry,encoder,config}.py` and `bench_e02.py` (reused unchanged; no seams needed — `Runner.drive()` already exposes closed-loop body control), pinned simulator files, `main` and the eight world branches.

[Functions]

New functions:

1. `firmware/pico2/floor_e03.py`

   - `check(speed_in_s, yaw_rate_rad_s)` — convert to SI and refuse parameters whose wheel demand exceeds the `config.py` envelope: linear speed above the `MAX_WHEEL_RPM`-derived wheel-speed limit, or pure-spin yaw above `max_wheel_speed_m_s / HALF_TRACK_M` (≈ 4.15 rad/s); returns the SI pair `(speed_m_s, yaw_rate_rad_s)`.
   - `straight(runner, speed_in_s=8.0, length_m=1.0)` — arm; 200 Hz loop calling `runner.drive(speed_m_s, 0.0)`; integrate per-count travel `2*pi*WHEEL_RADIUS_M/COUNTS_PER_OUTPUT_REV` from encoder deltas into distance (forward-positive, no extra sign handling); **stop commanding motion at `length_m - v^2/(2*MAX_BRAKE_M_S2)`** (≈ 0.021 m at 8 in/s) so the ramp-down lands on target instead of overshooting; then command 0.0 and wait for settle (both `|rpm|` below ~2 rpm, bounded by a ~2 s settle timeout); break early on any safety stop; zero duty and disable; return the summary dict.
   - `spin(runner, direction, yaw_rate_rad_s=2.0, revolutions=1.0)` — same loop with `runner.drive(0.0, ±yaw_rate)`; integrate differential yaw `(ds_right - ds_left)/(2*HALF_TRACK_M)` (positive = CCW = left); **stop commanding at `target_yaw - omega^2/(2*MAX_YAW_ACCEL_RAD_S2)`** (≈ 0.444 rad = 25.5° at 2 rad/s — without this lookahead the systematic overshoot alone would exceed the sealed 5° median-spin gate); then command 0.0 and settle as above; return the summary dict with `yaw_deg`.
   - `save(runner, path, dumps)` — identical pattern to `bench_e02.save` (RAM ring buffer → JSON Lines after the motors stop).
   - Style for MicroPython lint compliance: `math.sqrt` (never `math.hypot`), `%` formatting, no `match` statements, imports only `math` plus local modules.

2. `tools/bench/log_to_e03.py`

   - `row_from_log(text, log_name, support, mass, kind, direction, repeat)` — validate telemetry lines with `telemetry_schema.validate_lines`; `duration_s` = `DRIVE`-mode `t_ms` span plus one 20 ms telemetry period; `max_speed_in_s` = maximum body speed implied by the `rpm` pairs (mean wheel rpm → m/s → in/s); `thermal_or_protection_fault` true iff stop reasons beyond `none/not_armed/auto_stop` appear; `notes` states exactly what was computed and from what; `raw_observation_ref` = `<log name> sha256:<hex>`.
   - `main(argv=None)` — argparse: `--support` (dual-front-rear|front-only|rear-only), `--mass` (2|4|6), `--kind` (straight|spin), `--direction` (forward|left|right), `--repeat` (positive int), positional log path; prints one CSV row to stdout, mirroring `log_to_e02.py` exactly.

3. `firmware/host_tests/test_floor_e03.py` (unittest, auto-discovered; mirrors `test_plant_in_the_loop.py` patterns — `IN = 0.0254`, `runner.arm()`, tick + `runner.wait_next(deadline)` + `hal._advance()` loop)

   - `test_straight_trial_lands_on_target_distance` — `PlantHal(11.1, 0.25, 4.0)` (nominal, qualifying mass); result `completed`; integrated encoder distance within ~5 cm of 1.0 m; `DRIVE`-mode records present; compare against plant ground truth `hal.state` (mean tail speed ≈ 8 in/s).
   - `test_spin_trial_lands_on_target_yaw` — `PlantHal` nominal; |integrated yaw| within ~15° of 360° and at least ~345° (catches sign or stopping-logic bugs); `yaw_deg` sign matches direction.
   - `test_estop_mid_trial_latches` — `FakeHal` with `hal.estop = True` injected mid-run (attribute, per the fake's API); `stop_reason` `estop`; motors disabled; no resume.
   - `test_beyond_envelope_parameters_are_refused` — oversized speed (e.g., 40 in/s) and oversized yaw (e.g., 6 rad/s) raise a clear error before arming.
   - `test_log_to_e03_row_matches_template` — synthetic straight log via `floor_e03.straight` against `FakeHal`; row columns equal the template header; trial_id format matches; `duration_s`/`max_speed_in_s` computed; every human-measured field blank.

Modified functions: none in existing modules. `main.py` gains only the `floor()` entry.

Removed functions: none.

[Classes]

None. No new or modified classes; `floor_e03.py` is plain functions like `bench_e02.py`, reusing `Runner`, `DriveShaper`, `WheelSpeedController`, `SafetyMonitor`, and `Telemetry` unchanged.

[Dependencies]

None.

- Python stdlib only for the new tool and tests (`argparse`, `csv`, `hashlib`, `io`, `json`, `pathlib`, `sys`, `unittest`).
- No new npm or pip packages; no network; no hardware.
- MicroPython compatibility enforced by the existing `tools/micropython_lint.py` gate, which lints `firmware/pico2/floor_e03.py` automatically.

[Testing]

1. New host tests auto-discovered by the existing firmware stage:

   - `uv run --no-project --python 3.12 python -B -I -m unittest discover -s firmware/host_tests -t firmware` (also run by `node tools/check-all.js`). Suite grows from 72 to ~77 tests; the five plant-backed trials add a few seconds to the ~38 s stage.
   - Plant-backed assertions are behavior checks with placeholder friction/mass; passing them does not predict the physical mule (existing README wording preserved). Where possible, assertions compare the firmware's integrated odometry against the plant's ground-truth `state` (`v`, `yaw_rate`, `slip`).

2. Existing gates that must stay green

   - MicroPython lint over `firmware/pico2` (covers the new file; `math.hypot` and friends banned).
   - The AI orchestration node tests (unchanged by this plan).
   - `node tools/check-all.js` full gate: all steps, including the sealed verifiers (mule-v10 package untouched) and the firmware suite.
   - Secrets scan on changed files; `git ls-remote`/`git log origin/main` confirming `main` and the world branches untouched.

3. Not run in this change

   - Anything on hardware. Flashing, bench, and floor trials are owner actions under the approved setups; E02A/E02 gates still precede E03. No physical measurement is claimed or simulated as real.

[Implementation Order]

1. Write `firmware/pico2/floor_e03.py` (check, straight, spin, save) with braking-lookahead stopping, mirroring `bench_e02.py` structure and safety behavior.
2. Add the `floor(...)` REPL entry to `firmware/pico2/main.py`; boot default stays IDLE.
3. Write `tools/bench/log_to_e03.py` mirroring `log_to_e02.py`, with the template's exact columns and trial_id formats.
4. Write `firmware/host_tests/test_floor_e03.py` (plant-backed trials with ground-truth comparison, safety latch, envelope validation, row shape).
5. Update `firmware/README.md` (layout, E03 data flow, floor safety), `PROJECT-STATUS.md` (November 7 review sentence), `SESSION-STATE-2026-11-07.md` (note).
6. Validate: MicroPython lint, firmware host tests, the AI test suites, full `node tools/check-all.js`, secrets scan, branch-state check.
7. Commit and push on `ai-orchestration`.

**Do not begin implementation until the owner explicitly approves this plan.**
