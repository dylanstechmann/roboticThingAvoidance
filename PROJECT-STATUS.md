# IEEE project status and lineage

Updated November 7, 2026. Personal hobby/learning project with AI-assisted research and software. No purchases, fabrication, physical robot trials or organizer contact are recorded.

**November 7 computer-only study pack (agent-run):** `derived/recovery-v1/` seals 64 cells and `derived/dr-registry-v1/` contains 1,280 sim entries. All 640 spanning-blocker runs blocked; `auto` passed 17/20 mid-band and 20/20 corner-band runs in both pose modes, while ordinary vehicle contacts remained separate. No unblocked route had zero planned contacts, so the router-pass association is null; the planned-contact Spearman is only 0.0474 (clustered permutation p=0.007999), not evidence of a useful practical link. `derived/simreal-v1/` validates 18 records against six immutable world seals, but its provisional symmetric plant gives near-zero drift and zero fragile flags, not evidence of hardware robustness. `derived/humans-v1/` uses 10 in static discs: 8/20 N=1 runs completed, every seed had a human contact by N=2, and N=2..10 completions are 0/20. `docs/folder-breakdown.md` covers 149 tools and leaves 25 explicit test gaps. Full `check-all` passed 47/47 steps; none of these synthetic results is physical qualification.

**November 7 review (agent-run):** the owner's standing constraint is now recorded in `AGENTS.md` ("Owner-set constraints"): this project uses no vendor CAD and only open-source software; the rule had survived only in archived plan-history files. The v13 vendor-geometry findings are marked historical-only, the AI harness's vendor-CAD research task was removed, and the `cad-motor-gap-review` advisory task was re-pointed to the page-published motor dimensions (`docs/motor-dimensions-published.md`) and the bench kit notes ahead of physical measurement. The firmware also gained the E03 floor-trial path for the G1 bring-up gate: a closed-loop straight/spin runner (`firmware/pico2/floor_e03.py`) that ends its commands one braking allowance short of the target so the shaper's ramp-down lands on it, a `main.floor()` REPL entry that keeps boot at IDLE, and `tools/bench/log_to_e03.py` turning each trial log into one template-matching CSV row with the human-measured fields left blank. All host-tested (79 firmware tests; MicroPython lint clean); nothing run on hardware, and the sealed E03 analyzer, templates and mule-v10 package are untouched.

**November 7 continuation (agent-run):** the rotated provider credentials are stored only in the private key store outside the repository; the five local-only `next-phase-v10` commits are published to GitHub (fast-forward, `main` unchanged); and three live advisory runs with the new keys are recorded in `derived/ai-orchestration/evidence/` (all `review: pending`): `rules-update-scan` (Exa; official 2027 pages and Arena Build Guide found, still no V3.1 posting), `literature-search` (OpenAlex) and `organizer-qa-draft` (OpenRouter via the harness's role-aware fallback). The JSON task-object validator follow-up is implemented: `validateTaskManifest()` cross-checks the task manifest against the provider registry before any run, with 11 new offline tests (42/42 in the focused harness suites). The secrets-guard scanner now skips embedded base64 data URIs, clearing a false-positive Brave-key match inside `share/Showcase-v10.html`'s image data (that file is untouched; it remains a sealed v13 build input). The owner then dropped the japanfold provider entirely — key removed from the private store and the planned registry entry, with tests and docs updated to match. No hardware action, purchasing or organizer contact occurred in this continuation.

**November 6 review (agent-run):** Tracks 1a–1d landed — the AprilTag and start flag are sensed through camera models in an opt-in mission subclass, vehicle contacts are attributed by phase, and the `avoid-v12` sweep pins the contact-free zero on the 10 in robot envelope against guide-size vehicles (not blend timing). Track 2 ported the EKF estimator to firmware (`firmware/pico2/estimator.py`, matching the host filter) but it is not yet wired into `main.py`. An RL-vs-classical evaluation scaffold (`derived/rl-v1/`) and a first trained linear policy (`derived/rl-v2/`) are in place; the trained policy completes 20/20 evaluation missions (score-like 240.75 vs the classical 267.75) and has not been matched to a physical robot.

**November 3 review (agent-run):** the plan, gates and dates to April are in `BACKCAST-2026-11.md`; the Q&A questions to post are in `derived/qa-pack-v10/`; corrections to pinned documents are in `ERRATA-2026-11.md`; and the club summary is `derived/club-update-v10/CLUB-UPDATE.md`. The findings, each fixed in the next packages:
- **Obstacles missing from the nominal case.** Every legal match has three obstacles, passed on every lap, but the "nominal" v9 runs have none.
- **Obstacle stand-in too small.** The v9 stand-in is a 4.6 in circle (a 2 in square in the planner); the organizer guide's vehicle is about 8.55 x 8.2 in.
- **20/20 overstated.** The 20 evaluation seeds are 3 deterministic runs, one per pit box.
- **Simulator defects.**
  - The RL interface cannot be driven by a policy.
  - The simulator ignores the motor model.
  - `match_logic.py` is not used by the simulator.
  - Nominal laps take 29.60–29.65 s, not 32.35 s.

**Club package:** `derived/club-package-v9/CLUB-PRESENTATION.md`, with the rule/Q&A ledger and conditional parts list. The updated synthetic mission completes three clean obstacle-free laps and parks in all 20 evaluation seeds, which are 3 distinct deterministic configurations (one per pit box); all finish before 165 s. Nine obstacle probes yield three entry safe stops, three collision-free detour attempts that time out at 178 s, and three off-route completions. No avoidance mission is qualified. No RL policy has been trained. See `derived/mission-v9/README.md`.

## Start here

Open **`share/Showcase-v10.html`** for the one-page overview (arena, parts, physics, simulations) built for sharing. The consolidated offline studio is **`share/Robot-Studio-v8.html`**; its guide is `derived/robot-studio-v8/README.md`.

v8 combines rather than replaces the earlier work:

| Earlier contribution | Status in v8 |
|---|---|
| Multi-model GM1/GM2 V3 document interpretation and field geometry | Retained as source-backed findings with unresolved Q&A and measurement gates |
| Navigation and scoring models | Retained as conditional studies; not legal routes or measured performance |
| Mule dynamics, stopping and electrical screening | Original data retained; old 176 mm track is explicitly incompatible with vendor-CAD 202 mm track |
| Tire-mechanism comparison | All 162 cases / 2,970 frames retained; no mechanism selected |
| Claude v7 vendor CAD and AprilTag analysis | Retained; useful CAD correction and library/geometry findings |
| v7 realistic renderer | Reused for the assembly/field workspace |

## What is actually established

- Archived GM1/GM2 V3 manuals support the nominal **390 robot points + 10 publicity** scoring model. Official Discord Q&A has not been reviewed.
- Multi-model image transcription and mesh analysis support the documented field/tire baseline. This is not a measured physical field or print-tolerance certification.
- Pololu CAD supports a **7 mm motor-shaft offset**, **202 mm stock wheel track**, and a **7.09 mm support mismatch** in the original mule kit. These are CAD measurements, not received-part measurements.
- AprilTag 3 decodes the organizer sheet as **tagStandard41h12 IDs 1–3**. OpenCV ArUco has no 41h12 dictionary. Pose uses the inner **5/9** edge; the physical print scale is unmeasured.
- The Node suite and artifact verifiers check software and reproducibility, not physical robot success.
- All artifact verifiers pass as of November 4 (`node tools/check-all.js`).
- `verify-planner-diagnostics-v3.js` passes again through a recorded input supersession. `tools/avoidance-v3.js` changed after that package was sealed; `--reproduce` regenerates the report, summary and 48 SVGs byte-identically. No sealed bytes changed. See `derived/audits/2026-11-03-planner-diagnostics-v3-input-supersession/`.

## What is not established

- No final competition chassis, tire mechanism, driver, battery, actuator or wiring release.
- No calibrated dynamics, legal complete mission, robust obstacle avoidance or physical reliability estimate.
- No measured received parts, real camera performance, installed field geometry or official answers to the eight team Q&A items.

## Version history and preservation

This folder had **no Git repository before November 1, 2026**. Earlier session documents explicitly confirm that. The local Git history begins with a snapshot of the files present at consolidation; it is not a reconstruction of earlier edits or proof of which agent made them.

A full pre-consolidation backup is stored one level above this project at `../ieee-pre-consolidation-2026-11-01.tar.gz`, SHA-256 `3f918631e432b49ec6a9f1e414a842aefac02ffea725e4b4f67ecc594c82b551`.

The `website/` directory retains its own independent local Git history. Its deployment files are also tracked in the parent project without importing or deleting its nested metadata.

A private GitHub remote now exists (`github.com/dylanstechmann/ieee`). `main` was pushed on November 3 and updated on November 4 at the owner's go-ahead; newer next-phase work stays on the `next-phase-v10` branch until the owner approves another update. (Earlier notes saying no remote existed predate it.)

## Next work in priority order

**Superseded on November 3 by `BACKCAST-2026-11.md`.** The order there is:
- **Physical (owner and club):** post the Q&A; decide Order A, the obstacle set and field materials; build and measure the practice field; caliper-check parts and build the mule; run the tire-mechanism DOE.
- **Agent:** done so far: a one-command check (`node tools/check-all.js`); the Q&A pack and corrections; the organizer CAD extraction (`derived/organizer-cad-v10/`); the practice-field packet (`derived/practice-field-v10/`); the shaft-down mule deck (`derived/drivetrain-mule-v10/`); the Pico 2 firmware skeleton with bench tools (`firmware/`, not flashed); the v10 supervisor and planner in `software/stockcar/`; the passability atlas (`derived/passability-atlas-v10/`: with the guide-size vehicle, contact-free passes exist for only 0–47% of placements, and a round base helps lane changes by only 0.5–1 in); the tire-fixture test kit (`derived/tire-fixture-v10/`); the competition mockup and sizing box (`derived/competition-mockup-v10/`); and the lap study (`derived/lap-study-v10/`). The lap study finds contact-free laps in only 0–2.5% of random layouts with guide-size vehicles, missions of about 81 s at 12 in/s (all under 165 s), and about 296 expected points with the exchange against 250 without. The v10 mission simulator (`derived/mission-v10/`) completes 20/20 evaluation missions on the empty field (median 55 s at 12 in/s) and with guide-size vehicles, where no run is contact-free. Its RL interface can now be driven by a policy. Sensor models and an EKF estimator (`derived/estimation-v10/`) let the simulated robot steer from estimated pose. In this optimistic model, low range sensing to walls carries the estimate. Reflectance alone can also finish once the gyro is calibrated (20/20 on the empty field), so it is a fallback; odometry alone drifts by inches. Gyro bias and gyro scale both matter, and wheel scale barely does. The robot still gets true vehicle positions for its lane plan. A Python port of the dynamics model matches the JavaScript on all six scenarios and exposed faults in it (`ERRATA-2026-11.md`). The corrected model (`derived/envelope-v10/`) gives a top speed of about 21–24 in/s, shows that grip limits acceleration and braking, and shows that in a 7.5 in U-turn the outer wheel limits the robot to about 11–13 in/s, so 12 in/s works and 16 in/s does not. The firmware gained command shaping (`firmware/pico2/drive.py`), and its real control loop now runs in tests against this model. A log replay tool (`tools/replay-log.py`) reruns mission logs through the estimator and supervisor. The maneuver study (`derived/maneuver-v10/`) runs the firmware's real control loop along routes on the corrected model: it finishes laps on all 27 conditions within about 0.4 in, at about 9 s per lap and 60–63 s per clean mission. The simulator's sharp pit routes could not be driven at speed, so the study rounds them and caps pit speed at 8 in/s. With guide-size vehicles no line avoids contact, so plain lanes score best; dodging starts to pay near half that size. It also exports a route library for the robot. Its plain-lanes laps drive from the EKF with no vehicle knowledge at all; the estimation and mission studies still read true vehicle positions for their lane plans.
  The full-mission study (`derived/full-mission-v10/`) chains the supervisor, a new mission driver, packed route files, the tracker, the EKF and the firmware loop: 91 of 91 simulated missions finished and parked with no wall contact, at about 58 s. The robot passes straight through vehicles in that model, so its score with vehicles is an upper bound. The tightest moment is the square's spin in the pit box.
  - **Not built:** camera and start-flag sensor models, so the simulated robot is told its pit box and start. They depend on QA02 and V3.1. The estimator is not yet on the board side, and `main.py` deliberately cannot start a mission.
  - **Waiting on measurements:** finding vehicles with the robot's own sensors, because at guide size the best line ignores them and it pays only if the official set is much smaller; refreshing the simulations with the measured field, vehicles and motors.

The list below is the earlier plan, kept for reference.

1. **Timeout diagnosed; broader maneuver study remains unqualified.** The detoured lap takes 44.40 s versus about 29.6 s nominal (earlier notes said 32.35 s; an in-memory re-run on November 3 gives 29.60–29.65 s for every box), adding 38 inches and four spins. The final lap starts at 141.80 s and auto-stops at 178 s with two laps complete. Reverse-entry/rejoin candidates intersect the divider; a bounded reverse-first lower-lane study was geometrically clear but still timed out during parking, even with reduced settling or a direct parking approach. See `derived/mission-v9/README.md`. The production baseline and three detour timeouts are unchanged; do not tune the same hypothetical bypass repeatedly.
2. Resolve official Q&A and measure a built field, actual obstacles and printed tags. Use those measurements for a broader route/maneuver study rather than assuming this hypothetical blocker.
3. Physically verify the proposed mule geometry through the documented bench gates; dynamics-v9 is corrected-track but uncalibrated.
4. Build a legal-envelope competition mockup and real tire fixture; compare acquisition, retention, release and bail-out behavior.
5. Replace perfect simulated knowledge with real sensing, then train/evaluate RL only against a coherent classical baseline. Keep dated portfolio evidence.

The detailed handoffs remain in `SESSION-STATE-2026-10-29.md`, `SESSION-STATE-2026-10-30.md`, `SESSION-STATE-2026-10-31.md` and `SESSION-STATE-2026-11-01.md`. Older plans and V2 references are historical, not current status.
