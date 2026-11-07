# Implementation Plan

[Overview]

Finish the four approved computer-only work items on `ai-orchestration`: a sealed blocked-route recovery study and Disrupted-Route (DR) registry, a sealed sim-to-real expected-pass screening analysis, a sealed isolated-human planner-safety benchmark, and an audited per-tool folder breakdown. No hardware action, firmware edit, pinned-source edit, world-branch edit, or new dependency is permitted.

Current state at planning: HEAD is `82a71b5`; the only uncommitted implementation work is the recovery layer, its tests/evaluator, generated recovery/DR artifacts, and this plan. Eight recovery unit tests pass and the current artifacts contain 64 cells × 20 seeds = 1,280 DR entries with internally consistent hashes. They are **not yet accepted** because investigation found two correctness defects: (1) high-side blockers are marked passed at startup because `x < blocker_x` is already true outside the lap, and (2) the association uses ordinal ranks for ties and independently shuffles repeated baseline values, making its Spearman/permutation result invalid. These must be fixed and the study regenerated before any verifier or status document treats it as a result.

The recovery matrix is eight scenarios × four behaviors × two pose modes = **64 cells**, not the 48 in the superseded draft. The four behaviors are `stall_stop`, `lateral_shift`, `replan_lanes`, and `auto`; `backtrack` and `pit_bypass` remain documented as inexpressible in the forward-only v10 oval/pit model. Recovery success means crossing the injected blocker on the lap without contacting it (`recovered` or `recovered_contact`), while mission completion and contacts elsewhere remain separate measurements.

The six RL-v3 inputs also need special handling: only the primary world's seal is in this working tree; the other five seals exist only on their world branches. The sim-to-real tool will read immutable `<source-commit>:derived/rl-v3/<world>/{report,manifest}.json` objects through `git show`, validate every source-seal hash against that commit, and record source branch/commit/report hashes. It will not check out, merge, or modify another branch.

Every study follows the repository's sealed pattern: a stdlib Python evaluator, `derived/<study>-v1/{manifest.json,report.json,summary.md}`, a `tools/verify-*-v1.js` goal test, and a Node wrapper test. The DR registry additionally has a host-only CLI and append-only owner observations. The folder inventory is documentation plus a Node coverage test, not a fifth sealed study. Four new verifiers increase `check-all` from 43 to **47 steps**.

Out of scope remains: the JSON task-object validator (follow-up only), human perception (after G2 sensor selection), DR lookup in firmware (after G2), nonlinear learned-policy work, sensed blocker detection, hardware qualification, and changes to `main` or the eight world branches.

[Types]

### Shared statistics — `software/stockcar/study_stats.py`

Stdlib-only helpers shared by the three studies:

- `wilson(successes, n, z=1.96) -> [float, float] | None`: Wilson 95% interval; `None` for `n == 0`, otherwise clamped to `[0, 1]` (no `-0.0`).
- `midranks(values) -> list[float]`: average ranks for ties; input ordering must not change a tied value's rank.
- `spearman(xs, ys) -> float | None`: Pearson correlation of midranks; `None` when lengths differ/are zero or either vector is constant.
- `quantile(values, q) -> float | None`: deterministic linear-interpolated percentile, used for p2.5/p05/p50/p97.5; `None` for an empty sample.
- `clustered_permutation_p(xs, ys, corr, clusters, strata, shuffles=10000, seed=7) -> float | None`: permute one invariant `ys` value per independent cluster among clusters in the same stratum, rebuild the row-level vector, and compare absolute midrank Spearman statistics. Return `(1 + hits)/(1 + shuffles)`, never an unjustified zero.

### Recovery report and DR entries

`derived/recovery-v1/report.json` contains seeds 100–119 and 64 cell objects: `{scenario, behavior, pose_mode, runs, completed, passed_blocker, recovered, recovered_contact, blocked, stopped, incomplete, passed_wilson95, mean_time_s}`. Outcome counts sum to `runs`; `completed` is independently `state == DONE`. The baseline object reports, per pose mode, `runs`, `completed`, `router_passes`, `mean_planned_contacts`, and Wilson intervals for completion/router pass. **`router_pass` means `planned_contact_vehicles == 0` on the unblocked v10 route, not mission completion.**

The association object contains `units: 320`, `independent_clusters: 40` (20 seeds × two poses), eight scenario rows per cluster, explicit method/definition strings, Spearman and permutation p-values for router pass and planned contacts, and descriptive pooled success rates among router-pass/router-fail rows. Cluster keys are `(pose_mode, seed)`; permutation strata are pose modes. Null statistics are allowed when variance is absent. Summary text must state the repeated-cluster design and must not call the pooled rows independent evidence.

Each sim DR entry retains the existing identity fields and adds audit fields: `{schema, entry_kind: "sim", entry_id, world, route_segment: {phase, side, x_center_in, x_range_in}, blocking: {kind, footprint_in, yaw_deg, spans_corridor}, detection: "truth", pose_mode, recovery_behavior, outcome, blocker_passed, blocker_pass_time_s, blocker_contact_frames, completion, contact_free, time_s, stop_reason, seed, source}`. `outcome` is one of `recovered`, `recovered_contact`, `blocked`, `stopped`, `incomplete`; entry IDs include scenario, behavior, pose, and seed. `spans_corridor` is checked by Python tests against `widest_open_band` for the blocker alone.

A physical observation is an owner-supplied JSON object with `{schema, entry_kind: "physical-observation", entry_id, observed_at, world, route_segment, blocking, detection: "owner-observation", pose_mode: null, recovery_behavior: string|null, outcome: "unknown"|the sim outcomes, completion: bool|null, contact_free: bool|null, observed: non-empty string, seed: null, source: "physical:owner"}`. The CLI may assign a unique `DR-phys-YYYYMMDD-NN` ID. Owner observations are never sealed or rewritten by the recovery evaluator.

### Sim-to-real report

`derived/simreal-v1/report.json` has exactly 18 records (six functional worlds × `classical`/`learned`/`random`). Each record contains `{world, policy, source_branch, source_commit, source_report_sha256, sim_completed, sim_runs, sim_pass_rate, sim_pass_wilson95, n_draws: 10000, draw_seed, drift_source, provisional, e03_sample_counts, drift_mm_1m: {p50,p2_5,p97_5}, spin_error_deg_360: {p50,p2_5,p97_5}, corridor_width_in: 22.5, tolerances: {drift_mm: 25.0, spin_deg: 5.0}, expected_physical_pass: {p50,p2_5,p97_5}, fragile}`.

For each of 10,000 deterministic draws, sample `p_sim ~ Beta(completed + 0.5, runs - completed + 0.5)` (Jeffreys posterior), independently bootstrap one absolute E03 drift and one absolute spin error, and set the draw to `p_sim` only when drift ≤25 mm and spin ≤5 degrees, else zero. The tolerances come from `drivetrain-mule-v4.json`; they define an **E03-gate transfer screening index**, not a full-mission physical-pass probability. `fragile` is exactly `sim_pass_rate >= 0.8 && expected_physical_pass.p2_5 < 0.5`; the 0.8 convention is recorded and is not a physical qualification gate.

`derived/simreal-v1/drift-samples.json` records either measured E03 provenance or the provisional plant sample basis. Measured mode is explicit `--e03 <repo-relative-csv>` and uses all `attempt_status == completed` straight/spin rows with numeric measurements, without cherry-picking. Provisional mode uses 3 masses (2/4/6 kg) × 3 frictions (0.20/0.25/0.30) at 11.1 V: one straight and one left/right spin per combination. Drift is plant body lateral `y` after the 1 m straight; spin error is encoder wheel-differential yaw minus commanded 360 degrees. Both bases are labeled synthetic and not tape measurements. Support configurations are not claimed to be modeled.

### Human benchmark

A human is a static, non-reactive disc with a synthetic 5 in radius (10 in diameter), represented by `regular_polygon`; the 9 in and 6 in radii initially proposed could not fit ten non-overlapping placements for every evaluation seed. This is an assumed planning body, not a measured person or perception output. Human polygons stay separate from vehicle polygons so `vehicle_contact_steps` cannot hide a human contact. The planner receives truth positions (no perception claim), adds straightaway humans to oracle obstacle polygons, and does not claim to replan start, pit, or arc geometry.

Placements are generated once per seed in deterministic zone order (`start`, `pit_lane`, `lane_change`, `turn`), then nested so the first N placements are used for every N=1..10 cell. Rejection sampling requires humans to be inside their explicit zone, clear of barriers/vehicles/other humans and the initial robot footprint. Zone rectangles derive from `Field.start_box`, pit-route bounds, straight lane-change x=52..72, and west/east arc bounds; constants and rejection limits live in `humans.py`. Placement randomness is separate from vehicle-layout randomness so layouts stay paired across N.

Each of ten cells has 20 runs and `{n_humans, runs, completed, completion_rate, completion_wilson95, human_contact_count, human_contact_rate, min_clearance_in: {p50,p05}, aborted, aborted_rate, aborted_wilson95, runs_detail}`. Run detail records `{seed, state, completed, aborted, stop_reason, human_contact_count, human_contact_frames, min_clearance_in, time_s}`. Contact is negative `circle_polygon_distance`; abort is immediate on first human contact with `stop_reason: "human_contact"`. `human_contact_count` counts distinct humans contacted, `min_clearance_in` is minimum surface clearance over the run, and rates have Wilson intervals. No minimum rate or hoped-for trend is asserted.

### Folder-breakdown rows

`docs/folder-breakdown.md` has one row per source file under `tools/` and `tools/bench/` (excluding `__pycache__`): `{folder, tool, purpose, goal_test, gap_note}`. `goal_test` must name a real direct verifier/test, or the row must say `GAP` and explain missing coverage. Generic inclusion in `check-all` is not presented as a tool-specific goal test.

[Files]

New shared/library files:

- `software/stockcar/study_stats.py` — the five statistics helpers above.
- `software/stockcar/simreal.py` — Git-object source loading/validation, E03 CSV parsing, deterministic draw generation, and record summarization; no firmware import.
- `software/stockcar/humans.py` — human shape/zone constants, seeded nested placement, clearance/contact helpers, `HumanMissionSim`, and `run_human`.
- `software/stockcar/tests/test_study_stats.py`, `test_simreal.py`, and `test_humans.py` — focused unit/integration tests.

New tools and tests:

- `tools/dr-registry.js` — host-only `query`, `add-physical`, and `stats` CLI with JSON output and schema validation.
- `tools/evaluate-simreal-v1.py` — provisional plant sample generation or explicit measured-E03 loading; seals `derived/simreal-v1/` including `drift-samples.json`.
- `tools/evaluate-humans-v1.py` — ten-cell × 20-seed study; seals `derived/humans-v1/`.
- `tools/verify-{recovery,dr-registry,simreal,humans}-v1.js` — four auto-discovered goal tests.
- `tests/{recovery,dr-registry,simreal,humans}-v1.test.js` — verifier wrapper tests following `tests/avoid-v12.test.js`.
- `tests/folder-breakdown.test.js` — verifies complete, unique tool inventory coverage and real goal-test paths/GAP markers.
- `docs/folder-breakdown.md` — audited per-tool table.
- Generated `derived/recovery-v1/**`, `derived/dr-registry-v1/**`, `derived/simreal-v1/**`, and `derived/humans-v1/**`.

Modified existing files:

- `software/stockcar/recovery.py` — richer DR audit fields and geometry assertions; scenario dictionary API remains unchanged.
- `software/stockcar/recovery_sim.py` — directional lap-only blocker crossing and pass timestamp.
- `software/stockcar/tests/test_recovery.py` — high-side startup regression, crossing direction/corridor tests, scenario-span checks, and outcome/entry fields.
- `tools/evaluate-recovery-v1.py` — shared tie-aware clustered statistics, corrected baseline/association definitions, incomplete counts, non-destructive physical-observation handling, and updated summary limitations.
- `PROJECT-STATUS.md` and `SESSION-STATE-2026-11-07.md` — final measured results, corrections, limitations, and agent/owner handoff.
- `implementation_plan.md` — this executable revision of the approved plan.

No file is deleted or moved. `package.json` is unchanged. Pinned sources, all previously sealed packages, `firmware/**`, E03 templates/contracts, `schemas/`, `main`, and all world branches remain byte-identical; provisional sim-to-real code imports host-plant sources without editing them.

[Functions]

Statistics:

- Add `wilson`, `midranks`, `spearman`, `quantile`, and `clustered_permutation_p` to `study_stats.py` with the exact contracts in [Types]. Replace the local Wilson/Spearman/permutation implementations in `evaluate-recovery-v1.py`; reuse Wilson/quantile in simreal and humans.

Recovery:

- Modify `RecoveryMissionSim.step` in `recovery_sim.py`: retain the previous pose; check blocker contact before crossing; set `blocker_passed` only on `route_name == "LAP"`, with current y inside the blocked corridor, zero prior blocker contacts, and a directional center crossing (`previous_x <= cx < x` low, `previous_x >= cx > x` high). Record `blocker_pass_time_s`; never infer passage from one-sided x position.
- Modify `RecoveryMissionSim.reset` to clear previous-pose/pass/contact/timestamp state. Keep `_blocker_contact`, `classical_action`, `build_routes`, `run_recovery`, and scenario dictionaries otherwise intact.
- Modify `make_entry` in `recovery.py` to emit pass/contact audit fields. Add a test-only geometry consistency check for every `SCENARIOS[name]["spans"]`; do not infer span labels from outcomes.
- Modify `cell_of`, baseline aggregation, and association construction in `evaluate-recovery-v1.py` per [Types]. Preserve `physical-observations.json` with create-if-missing semantics; never replace it with `[]` on regeneration.

DR CLI (`tools/dr-registry.js`):

- `validateEntry(entry, {physical}) -> entry`: enforce required/allowed fields, finite dimensions/ranges, unique IDs at file load, valid enums, and physical-vs-sim-only fields; reject credential-like content using the existing harness patterns without reading any key store.
- `query(filters) -> object`: match side, kind, x within route range, optional behavior, and optional footprint within 0.5 in per dimension; aggregate matching sim precedents by behavior with `passed_blocker`-equivalent success (`recovered`/`recovered_contact`), Wilson intervals, and IDs; include matching physical observations.
- `addPhysical(input, physicalPath) -> entry`: validate owner JSON, assign a unique ID if absent, append atomically to the physical file, and never open the sim registry for writing.
- `stats() -> object`: counts by entry kind/behavior/outcome and sim success rates with Wilson intervals. CLI usage is `node tools/dr-registry.js query|add-physical|stats [flags]`; tests use temporary paths, never repository observations.

Sim-to-real:

- `load_world_sources(root) -> list` in `simreal.py`: resolve six explicit world branches to full commits; read report/manifest through `git show`; validate every source input/output hash against those commits; return all three policy cells and immutable provenance. Fail on missing/malformed/stale sources rather than reducing coverage.
- `read_e03(path) -> {drift_mm, spin_error_deg, provenance}`: parse the existing 27-column CSV; require completed straight and spin rows, numeric measurements, non-placeholder surface/provenance, and a repo-relative path. Include SHA-256 and row counts.
- `expected_draws(completed, runs, drift, spins, tolerances, n_draws, seed) -> list[float]`: implement [Types]' Jeffreys/bootstrap formula with `random.betavariate` and stable world/policy integer seeds. `summarize_draws` produces ordered percentiles and the exact fragile flag.
- `provisional_samples()` in `evaluate-simreal-v1.py`: add `firmware/` and `firmware/pico2/` to the isolated import path, instantiate `PlantHal` + `Runner`, and run only host `floor_e03` methods. Record parameter grid and measurement bases. Hash direct/transitive repository inputs (`config`, `floor_e03`, `runner`, `drive`, `motor`, `safety`, `telemetry`, `fakes`, `plant_hal`, `dynamics`, `envelope`, `lapmodel`, dynamics golden fixture) plus evaluator/library/field/gate files.
- Seal `report.json`, `drift-samples.json`, and `summary.md`; the manifest contains normal file input hashes plus six source commit/report records. Summary explains the screening formula, branch provenance, small-sample bootstrap limitation, and provisional/measured mode.

Humans:

- `human_polygon(human)` and `min_human_clearance(robot_polygon, humans)`: polygon generation and minimum signed surface distance using pinned geometry helpers.
- `place_humans(seed, layout, field, count=10) -> list`: nested deterministic rejection placement with zone/side labels; raise clearly if the bounded sampler cannot place ten rather than relaxing separation rules.
- `HumanMissionSim.build_routes`: mirror the small oracle builder in `AvoidingMissionSim`, combining vehicle and straightaway-human polygons by side while leaving pit/enter/park geometry unchanged. Keep separate infeasible-obstacle accounting.
- `HumanMissionSim.step`: update minimum clearance after motion; on first contact record human ID(s), set `aborted`/`stop_reason`, and return `done=True` immediately. Ordinary vehicle/wall behavior is not mislabeled human contact.
- `run_human(seed, n_humans, sensing=False, max_steps=4000) -> info`: build one normal seeded layout, inject the first N nested humans, run to terminal state/abort/cap, and return run-detail fields. The evaluator aggregates cells and writes hashes/summary with static-truth and uncovered-route-zone limitations.

Folder inventory:

- Enumerate actual files recursively under `tools/`, map each to its direct verifier or imported Node/Python test where one exists, and write explicit GAP rows elsewhere. `tests/folder-breakdown.test.js` compares the live file set with parsed Markdown paths, rejects duplicates/missing rows, verifies every non-GAP goal-test path exists, and requires a reason for each GAP.

[Classes]

- `RecoveryMissionSim` (`recovery_sim.py`, existing): add previous-pose/pass-timestamp state and corrected step/reset behavior. No constructor or scenario API change.
- `HumanMissionSim` (`humans.py`, new): extend `AvoidingMissionSim` with `lane_source="oracle"`, separate human geometry/contact state, human-aware straight routes, minimum-clearance tracking, and immediate human-contact termination. Do not modify the supervisor to fabricate a mission state.
- `PlantHal` and `Runner` (existing): reused unchanged for provisional samples; no subclass or firmware edit.
- No `BlockingScenario` class is introduced: scenarios remain dictionaries in `recovery.SCENARIOS`. No classes are removed.

[Dependencies]

No package or lockfile changes. Use CPython 3.12 stdlib through `uv run --no-project --python 3.12 python -B -I`; Node built-ins (`node:test`, `assert`, `fs`, `path`, `crypto`, `child_process`); and the installed Git CLI for immutable world-source objects. No network, provider credential, npm/Python package, hardware tool, or Docker-in-Docker step is needed.

[Testing]

Focused tests during implementation:

1. Run all software tests with `cd software && uv run --no-project --python 3.12 python -B -I -m unittest discover -s stockcar/tests -t . -p 'test_*.py'`. Statistics tests cover Wilson bounds, quantiles, midrank ties/order invariance, constant vectors, deterministic clustered permutation, and cluster/stratum validation. Recovery tests prove a high-side blocker is not passed in ENTER/at reset and that seed 100 `high_mid` + `stall_stop` contacts/blocks instead of producing the old false pass.
2. `test_simreal.py` uses explicitly synthetic drift/spin arrays to test deterministic draws, zero geometry survival, interval ordering, fragile recomputation, E03 filtering, and all six immutable source seals. It does not assert a desired physical-pass ranking.
3. `test_humans.py` checks nested/non-overlapping placements and zones, closer-human clearance monotonicity, separate human/vehicle accounting, immediate abort, human-aware routes, and one seeded N=1 primary-world completion without human contact. Fix any exposed placement/route defect rather than weaken the assertion.
4. Run each verifier directly and through its Node wrapper. Recovery verification checks 64 cells, 20 runs/cell, outcome sums, Wilson bounds, baseline/cluster definitions, hash freshness, and honest method strings, never a success direction. DR verification checks 1,280 unique sim entries and complete coverage, then exercises query/add/stats against temporary files including duplicate/malformed-input rejection and preservation of observations.
5. Simreal verification checks 18 records, six source commit seals/hashes, sim-rate agreement, 10,000 draws, interval ordering/ranges, exact fragile recomputation, and provenance. Human verification checks ten cells/200 runs, rates/count consistency, p05 ≤ p50, abort ⇒ contact, and completion ⇒ not aborted.
6. `tests/folder-breakdown.test.js` must account for every current tool, including all tools introduced here, with real test paths or explicit gaps.

Final validation and publication:

- Regenerate recovery once after corrections and inspect the new report before sealing the narrative: high spanning scenarios must no longer show startup passes; all four spanning scenario geometries and band outcomes are reviewed as measured. The current run took about 14 minutes, so use a captured log and verify exit status rather than assuming completion.
- Run `node tools/check-all.js` from the repository root; expect **47 passing steps** (one Node stage, 43 verifiers, two Python stages, one tree-cleanliness step) and no files changed by the run. Run focused suites first so failures are cheap to diagnose.
- Review `git diff --check`, the complete diff, and generated manifests. Run `python3 .claude/skills/secrets-guard/scripts/scan_secrets.py --worktree` before staging and `--staged` after staging; any hit blocks commit/push.
- Record `main`, `ai-orchestration`, and all eight world-branch tip hashes before and after work. Confirm only `ai-orchestration` advances and the final push is `git push origin ai-orchestration`; do not push `main` or world branches.
- Commit the corrected recovery work, four studies, inventory, and docs together only after every gate passes. The final summary must distinguish agent-run synthetic results from owner-performed/reviewed physical work and list any remaining GAP rows explicitly.

[Implementation Order]

1. Obtain owner approval of this revised plan. Preserve the previous draft at `/tmp/roboticThingAvoidance-implementation-plan.pre-update.md` during this session; git history retains earlier plans.
2. Add `study_stats.py` and its unit tests. Fix recovery crossing/timestamps, DR audit fields, baseline definitions, clustered midrank association, outcome counts, and create-if-missing physical observations. Run focused recovery/statistics tests before any long regeneration.
3. Regenerate `derived/recovery-v1/` and `derived/dr-registry-v1/registry.json`; inspect all scenario/behavior outcomes and association diagnostics. Do not tune scenarios to obtain a preferred correlation.
4. Add `verify-recovery-v1.js` and its Node wrapper; then implement `dr-registry.js`, its verifier/wrapper, and temporary-file CLI tests. Validate both against the regenerated artifacts.
5. Implement `simreal.py` + tests and `evaluate-simreal-v1.py`; validate all six Git-object source seals, generate provisional host-plant samples, seal the 18-record package, and add its verifier/wrapper. Measured mode is ready for an owner-supplied E03 CSV but is not fabricated or run without one.
6. Implement `humans.py` + tests, run the N=1..10 × 20-seed evaluator, inspect contact/abort/clearance results, and add its verifier/wrapper. Document uncovered route zones and static truth-position assumptions.
7. Produce `docs/folder-breakdown.md` from the final tool inventory and add `tests/folder-breakdown.test.js`; retain explicit coverage gaps rather than inventing tests.
8. Update `PROJECT-STATUS.md` and `SESSION-STATE-2026-11-07.md` with actual regenerated numbers, corrected recovery interpretation, simreal screening limitations, human benchmark findings, and the owner handoff. Update `ERRATA-2026-11.md` only if a separate existing unpinned document is found to be wrong.
9. Run focused suites, full `node tools/check-all.js` (47 steps), diff review, secrets scans, and branch-tip comparison. Confirm no pinned/sealed/firmware/world-branch changes.
10. Commit and push `ai-orchestration`, then report artifact paths, validation results, remaining GAPs, and follow-ups. Follow-ups not implemented here remain the JSON task-object validator, human perception after G2, firmware DR lookups after G2, sensed blocker detection, and nonlinear policy work.

**The owner approved implementation after this plan. Execution results and the 47-step validation are recorded in `SESSION-STATE-2026-11-07.md`.**
