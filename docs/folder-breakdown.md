# Per-tool folder breakdown

2026-11-07. Agent-audited inventory of the live `tools/` tree for the owner's hobby/learning project. Each row names the tool's purpose and its direct goal test. `GAP` means no direct test or same-study verifier was found; generic inclusion in `check-all` is not claimed as tool-specific coverage.

| folder | tool | purpose | goal test | gap note |
|---|---|---|---|---|
| `tools/` | `ai-orchestrate.js` | AI orchestration harness: routes narrowly scoped engineering tasks to the best-suited provider and records auditable, advisory evidence. Never stores credentials. | `tests/ai-orchestrate.test.js`<br>`tests/ai-orchestration-provider.test.js` | — |
| `tools/` | `analyze_e04_v10.py` | Analyze a filled E04 tire-handling DOE sheet (derived/tire-fixture-v10/doe-round1.csv format). | `software/stockcar/tests/test_e04_analysis.py` | — |
| `tools/` | `apriltag-41h12-v7.py` | AprilTag tagStandard41h12 readability check for the 2027 Stock Car Race field. | `tests/apriltag-41h12-v7.test.js`<br>`tests/team-brief-v7.test.js` | — |
| `tools/` | `atlas-v10.py` | Passability atlas v10: can a 10 in robot pass the Appendix E obstacles without contact? | `tests/passability-atlas-v10.test.js` | — |
| `tools/` | `avoidance-v3.js` | Policy is fixed for this planner instance. Never share these caches between phases or uncertainty policies with different admissibility rules. | `tests/avoidance-v3.test.js`<br>`tests/connected-navigation-v3.test.js`<br>`tests/contract-navigation-v3.test.js`<br>`tests/input-supersession.test.js`<br>`tests/planner-diagnostics-v3.test.js` | — |
| `tools/bench/` | `fit_motor.py` | Fit a simple DC-motor model to E02 bench logs (telemetry v1 JSON Lines from firmware bench_e02). | `firmware/host_tests/test_bench_tools.py` | — |
| `tools/bench/` | `log_to_e02.py` | Turn one bench_e02 log (telemetry v1 JSON Lines) into one E02-characterization CSV row. | `firmware/host_tests/test_bench_tools.py` | — |
| `tools/bench/` | `log_to_e03.py` | Turn one floor_e03 log (telemetry v1 JSON Lines) into one E03-floor-trial CSV row. | `firmware/host_tests/test_floor_e03.py` | — |
| `tools/` | `build-cad-v11.py` | Build additive editable exterior/structure studies. Never edits old artifacts. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `build-cad-v13.py` | Build source-evidenced v13 parts and datum-driven assembly studies. | `tools/verify-cad-v13.js` | — |
| `tools/` | `build-integration-studio-v6.js` | Project utility: build integration studio v6. | `tools/verify-integration-studio-v6.js`<br>`tests/integration-studio-v6.test.js` | — |
| `tools/` | `build-mule-dynamics-studio-v5.js` | Project utility: build mule dynamics studio v5. | `tests/mule-dynamics-v5.test.js` | — |
| `tools/` | `build-mule-studio-v4.js` | Project utility: build mule studio v4. | `tools/verify-mule-studio-v4.js`<br>`tests/mule-dynamics-v5.test.js`<br>`tests/mule-studio-v4.test.js`<br>`tests/stopping-dynamics-v6.test.js` | — |
| `tools/` | `build-robot-lab-v3.js` | Project utility: build robot lab v3. | `tools/verify-robot-lab-v3.js`<br>`tests/robot-lab-v3.test.js` | — |
| `tools/` | `build-robot-lab-v4.js` | Project utility: build robot lab v4. | `tools/verify-robot-lab-v4.js`<br>`tests/robot-lab-v4.test.js` | — |
| `tools/` | `build-robot-studio-v7.js` | Builds share/Robot-Studio-v7.html: one offline file with three.js (MIT, bundled by esbuild), the Pololu vendor meshes from tools/robot-studio-v7-parts.py, the measured assembly, the field | `tools/verify-robot-studio-v7.js` | — |
| `tools/` | `build-robot-studio-v8.js` | Project utility: build robot studio v8. | `tools/verify-robot-studio-v8.js` | — |
| `tools/` | `build-showcase-v11.js` | Project utility: build showcase v11. | `tests/showcase-v11.test.js` | — |
| `tools/` | `build-showcase-v13.js` | Project utility: build showcase v13. | `tests/showcase-v13.test.js` | — |
| `tools/` | `build-stopping-dynamics-v6.js` | Project utility: build stopping dynamics v6. | `tools/verify-stopping-dynamics-v6.js`<br>`tests/stopping-dynamics-v6-source-audit.test.js`<br>`tests/stopping-dynamics-v6.test.js` | — |
| `tools/` | `build-team-brief-page-v7.py` | Build the shareable HTML page for derived/team-brief-v7/TEAM-BRIEF.md. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `build_field_tables.py` | Generate firmware/pico2/field_tables.py — the board's static map (barrier polygons and the marking | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `build_pico_bundle.py` | Builds the folder to copy onto the Pico 2: firmware, the shared logic files and packed route tables. | `firmware/host_tests/test_estimator_in_mission.py`<br>`firmware/host_tests/test_mission_driver.py` | — |
| `tools/` | `check-all.js` | One-command project check: the Node test suite, every tools/verify-*.js artifact verifier, the Python suites, and a working-tree cleanliness check. | `tests/history-v10.test.js` | — |
| `tools/` | `check-fit-v13.py` | Evaluate nominal interfaces and sampled exact-solid v13 gate travel. | `tools/verify-cad-v13.py` | — |
| `tools/` | `check-live-v11.js` | Project utility: check live v11. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `check-live-v13.js` | Project utility: check live v13. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `check-robot-studio-v8-browser.js` | Project utility: check robot studio v8 browser. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `check-showcase-v11-browser.js` | Project utility: check showcase v11 browser. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `check-showcase-v13-browser.js` | Project utility: check showcase v13 browser. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `competition-mockup-v10.js` | Builds derived/competition-mockup-v10: true-scale square and round 10 in base plates that reuse the mule's motors, brackets and wheels, a side-view envelope inside the 12 in starting cube, a sizing-box | `tests/competition-mockup-v10.test.js` | — |
| `tools/` | `confirmation-packet-v3.js` | Render actual stored waypoints; arrows describe SPATIAL travel, not body heading. No invented finish-line geometry or obstacle placement is drawn. | `tests/confirmation-packet-v3.test.js` | — |
| `tools/` | `connected-candidate-summary-v3.js` | Project utility: connected candidate summary v3. | `tests/connected-navigation-v3.test.js` | — |
| `tools/` | `connected-navigation-v3.js` | Midpoints of strictly positive axis-aligned gaps, including robot half-extent and nominal margin. They only supplement search; interval checks decide safety. | `tests/confirmation-packet-v3.test.js`<br>`tests/connected-navigation-v3.test.js` | — |
| `tools/` | `constrained-field-v3.js` | Project utility: constrained field v3. | `tests/avoidance-v3.test.js`<br>`tests/confirmation-packet-v3.test.js`<br>`tests/connected-navigation-v3.test.js`<br>`tests/constrained-field-v3.test.js`<br>`tests/contract-navigation-v3.test.js`<br>`tests/differential-drive-v3.test.js`<br>`tests/navigation-stress-v3.test.js`<br>`tests/navigation-v3.test.js` | — |
| `tools/` | `contract-navigation-v3.js` | Center translation is affine, so endpoint containment in this convex rectangle covers every interpolated center, including spins. Not footprint containment. | `tests/contract-navigation-v3.test.js`<br>`tests/planner-diagnostics-v3.test.js` | — |
| `tools/` | `demo-mission-v10.py` | Runs one simulated whole mission and writes a self-contained, offline replay page. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `differential-drive-v3.js` | Reject lateral translation and simultaneous translate/rotate. This restricted primitive set is realizable by ideal differential drive but is not a planner. | `tests/avoidance-v3.test.js`<br>`tests/connected-navigation-v3.test.js`<br>`tests/contract-navigation-v3.test.js`<br>`tests/differential-drive-v3.test.js`<br>`tests/navigation-stress-v3.test.js` | — |
| `tools/` | `dr-registry.js` | Computer-only DR registry: sim precedents are sealed; owner observations are append-only. | `tests/dr-registry-v1.test.js` | — |
| `tools/` | `drivetrain-mule-v10.js` | Shaft-down mule deck revision (v10): resolves the deck, hole pattern and caster risers from the vendor-CAD measurements (or from caliper measurements with --from-measurements), writes a fit | `tests/drivetrain-mule-v10.test.js`<br>`tests/studio-dimensions-v11.test.js`<br>`firmware/host_tests/test_bench_tools.py`<br>`firmware/host_tests/test_floor_e03.py` | — |
| `tools/` | `drivetrain-mule-v4.js` | Project utility: drivetrain mule v4. | `tests/drivetrain-mule-v4.test.js`<br>`tests/mule-readiness-v4.test.js` | — |
| `tools/` | `dynamics-golden-v10.js` | Writes software/stockcar/tests/fixtures/dynamics-golden-v10.json: the exact inputs and JavaScript results of the dynamics-v9 model (tools/mule-dynamics-v5.js with the v9 config) for its six | `tests/dynamics-golden-v10.test.js`<br>`software/stockcar/tests/test_dynamics.py`<br>`software/stockcar/tests/test_envelope.py` | — |
| `tools/` | `dynamics-v9.js` | Project utility: dynamics v9. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `electrical-selection-v6.js` | Project utility: electrical selection v6. | `tests/electrical-selection-v6.test.js` | — |
| `tools/` | `envelope-v10.py` | Envelope v10: speed, acceleration, stopping and spin limits from the corrected dynamics model. | `tests/envelope-v10.test.js`<br>`firmware/host_tests/test_estimator_in_mission.py`<br>`firmware/host_tests/test_mission_driver.py`<br>`firmware/host_tests/test_plant_in_the_loop.py`<br>`firmware/host_tests/test_route_tracking.py` | — |
| `tools/` | `evaluate-avoid-v11.py` | Sweep the assumed robot footprint size through the sensed+avoidance mission to locate why contact-free | `tools/verify-avoid-v11.js` | — |
| `tools/` | `evaluate-avoid-v12.py` | Evaluate the avoiding-mission simulator across lane sources, footprints, yaw and pose modes. | `tools/verify-avoid-v12.js` | — |
| `tools/` | `evaluate-estimation-v10.py` | Estimation v10: closed-loop missions controlled from estimated pose, with sensor ablations. | `tools/verify-estimation-v10.js` | — |
| `tools/` | `evaluate-full-mission-v10.py` | Full mission v10: whole missions on the simulated robot, from the packed routes the board would use. | `tools/verify-full-mission-v10.js` | — |
| `tools/` | `evaluate-full-mission-v11.py` | Evaluate the sensed v11 mission simulator against the v10 ground-truth baseline. | `tools/verify-full-mission-v11.js` | — |
| `tools/` | `evaluate-humans-v1.py` | Evaluate static isolated-human planner safety for N=1..10 on reserved seeds 100-119. | `tools/verify-humans-v1.js` | — |
| `tools/` | `evaluate-maneuver-v10.py` | Maneuver v10: speed profiles, the firmware following them on the corrected plant, and a route library. | `tools/verify-maneuver-v10.js` | — |
| `tools/` | `evaluate-mission-v10.py` | Evaluate the v10 mission simulator on the reserved evaluation seeds (100-119). | `tools/verify-mission-v10.js` | — |
| `tools/` | `evaluate-mission-v9.py` | Write reproducible synthetic baseline evidence; never train or claim a policy. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `evaluate-recovery-v1.py` | Evaluate blocked-route recovery across scenarios, behaviors and pose modes. | `tools/verify-recovery-v1.js`<br>`software/stockcar/tests/test_recovery.py` | — |
| `tools/` | `evaluate-rl-v1.py` | Evaluate the RL-vs-classical harness: the classical baseline against a random policy. | `tools/verify-rl-v1.js` | — |
| `tools/` | `evaluate-rl-v2.py` | Compare the trained policy against the classical baseline and the random policy on the evaluation | `tools/verify-rl-v2.js` | — |
| `tools/` | `evaluate-sensing-v11.py` | Characterize the sensed game-element models (AprilTag pit box, start flag, checkered lap line). | `tools/verify-sensing-v11.js` | — |
| `tools/` | `evaluate-simreal-v1.py` | Seal the six-world sim-to-real E03-gate transfer screening study. | `tools/verify-simreal-v1.js` | — |
| `tools/` | `evaluate-world.py` | Compare the trained policy against the classical baseline and the random policy on the evaluation | `tools/verify-world.js` | — |
| `tools/` | `export-assembly-v11.js` | GLTFExporter uses the standard FileReader interface; Node supplies Blob. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `export-assembly-v13.js` | Project utility: export assembly v13. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `extract-sources.js` | Reproducible, loss-aware extraction from the two archived Word files. Requires Node.js and the unzip executable; no third-party packages. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `f3d-reader.js` | Read-only access to Autodesk Fusion .f3d archives and their ASM ("ACIS binary") B-rep blobs. The archives are untrusted input: members are decompressed in memory with size limits, names are | `tests/organizer-cad-v10.test.js` | — |
| `tools/` | `hardware-development-v3.js` | Project utility: hardware development v3. | `tests/hardware-development-v3.test.js`<br>`tests/order-a-procurement-v4.test.js` | — |
| `tools/` | `input-supersession.js` | Input-hash checking with dated supersession records. A sealed report lists the SHA-256 of each input at sealing time. A supersession record may accept one documented later edit of a specific input, but | `tests/input-supersession.test.js` | — |
| `tools/` | `inspect-tire-stl.js` | Intersect binary STL triangles with planes normal to Y; coordinates remain in STL units. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `lap-study-v10.py` | Lap study v10: contact-free laps, lap and mission times, and expected score over random layouts. | `tests/lap-study-v10.test.js` | — |
| `tools/` | `mechanism-envelope-v6.js` | Project utility: mechanism envelope v6. | `tests/mechanism-envelope-v6.test.js`<br>`tests/robot-studio-v8.test.js` | — |
| `tools/` | `mechanism-prototyping-v3.js` | Project utility: mechanism prototyping v3. | `tests/mechanism-prototyping-v3.test.js` | — |
| `tools/` | `micropython_lint.py` | Static checks that firmware/pico2 stays within what MicroPython on the RP2350 supports. | `firmware/host_tests/test_micropython_lint.py`<br>`firmware/host_tests/test_mission_driver.py` | — |
| `tools/` | `mission-timeline-v3.js` | Mission timeline feasibility model for the GM2 V3 stock-car mission (rules snapshot 2026-10-29). Converts the dimension-constrained field | `tests/mission-timeline-v3.test.js`<br>`tests/team-brief-v7.test.js` | — |
| `tools/` | `mule-deck-v10-cad.py` | Build STEP and STL files for the v10 mule deck and one caster riser from geometry.json. | `tools/verify-drivetrain-mule-v10.js` | — |
| `tools/` | `mule-dynamics-v5.js` | Project utility: mule dynamics v5. | `tests/mule-dynamics-v5.test.js` | — |
| `tools/` | `mule-measurements-v10.js` | Analyzer for mule E02/E03 bench logs against a chosen config (default drivetrain-mule-v10.json). It reuses the analysis functions of tools/mule-measurements-v4.js unchanged: that file is pinned by | `tests/drivetrain-mule-v10.test.js` | — |
| `tools/` | `mule-measurements-v4.js` | Project utility: mule measurements v4. | `tests/drivetrain-mule-v4.test.js`<br>`tests/mule-readiness-v4.test.js` | — |
| `tools/` | `mule-readiness-v4.js` | Project utility: mule readiness v4. | `tools/verify-drivetrain-mule-v4.js` | — |
| `tools/` | `multimodel-vision.py` | Multi-model vision consensus tool (OpenRouter). | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `navigation-stress-v3.js` | Every body point moves by at most d + R*/angle/ over an interval. At any interpolated pose the nearer endpoint is at most half that bound away. | `tests/avoidance-v3.test.js`<br>`tests/contract-navigation-v3.test.js`<br>`tests/navigation-stress-v3.test.js`<br>`tests/planner-diagnostics-v3.test.js` | — |
| `tools/` | `navigation-v3.js` | All vertices must be on the left of every edge (CCW convex input). | `tests/avoidance-v3.test.js`<br>`tests/confirmation-packet-v3.test.js`<br>`tests/connected-navigation-v3.test.js`<br>`tests/contract-navigation-v3.test.js`<br>`tests/differential-drive-v3.test.js`<br>`tests/navigation-stress-v3.test.js`<br>`tests/navigation-v3.test.js`<br>`tests/planner-diagnostics-v3.test.js` | — |
| `tools/` | `order-a-procurement-v4.js` | Project utility: order a procurement v4. | `tests/drivetrain-mule-v4.test.js`<br>`tests/electrical-selection-v6.test.js`<br>`tests/order-a-procurement-v4.test.js`<br>`tests/stopping-dynamics-v6-source-audit.test.js` | — |
| `tools/` | `organizer-cad-v10.js` | Reads the organizer's Fusion arena file (ZIP members compressed with Zstandard, B-rep in ASM binary form) and derives field geometry in the project frame. Agent-run extraction for the owner's | `tests/organizer-cad-v10.test.js`<br>`tests/studio-consistency-v12.test.js` | — |
| `tools/` | `plan-mission-v9-avoidance.js` | Project utility: plan mission v9 avoidance. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `planner-diagnostics-v3.js` | Geometry variants without pose error do not alter center-region/gate checks. | `tests/input-supersession.test.js`<br>`tests/planner-diagnostics-v3.test.js` | — |
| `tools/` | `practice-field-v10.js` | Builds derived/practice-field-v10: a practice-field build packet (materials, layout coordinates, plan drawing, as-built measurement template, +/-1 in variation drills) from the organizer CAD | `tests/practice-field-v10.test.js` | — |
| `tools/` | `qa-pack-v10.js` | Builds derived/qa-pack-v10 from qa-pack-v10.json: the deduplicated official Q&A questions, Discord-ready text, an answer-ledger template and a manifest. Agent-prepared drafts for the | `tests/qa-pack-v10.test.js` | — |
| `tools/` | `refine-stopping-dynamics-v6.js` | Project utility: refine stopping dynamics v6. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `refresh-confirmation-sources-v3.js` | Project utility: refresh confirmation sources v3. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `render-arena-guide.py` | Render the archived guide; run with uv --with pypdfium2 --with pillow. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `render-drawing-layout.js` | --out DIR writes elsewhere (tests use a temporary directory); the default is the sealed package location. | `tests/drawing-layout-v3.test.js` | — |
| `tools/` | `replay-log.py` | Reruns a mission log (schemas/mission-log-v1.json) through the estimator and supervisor. | `software/stockcar/tests/test_replay.py` | — |
| `tools/` | `robot-studio-v7-parts.py` | Convert the Order A vendor CAD to render meshes and check the mule assembly. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `route-progress-v3.js` | Strict partition-crossing engineering audit: crossing a gate's infinite partition outside its finite span is a bypass, not earned progress. | `tests/connected-navigation-v3.test.js`<br>`tests/planner-diagnostics-v3.test.js` | — |
| `tools/` | `score-v3.js` | Provisional arithmetic over referee-style achievement decisions, not a rules engine. | `tests/score-v3.test.js`<br>`tests/tournament-v7.test.js` | — |
| `tools/` | `seal-integration-studio-v6.js` | Project utility: seal integration studio v6. | `tools/verify-integration-studio-v6.js` | — |
| `tools/` | `sensor-plane-figure-v7.py` | Cross-section of one straightaway showing why a top-mounted 2D LiDAR misses the | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `stopping-dynamics-v6.js` | Solve Vbus = Vsource - Rsource * Pterminal/Vbus. Signed current permits returned power into an explicitly unresolved ideal source boundary. | `tests/stopping-dynamics-v6-source-audit.test.js`<br>`tests/stopping-dynamics-v6.test.js` | — |
| `tools/` | `strategy-v3.js` | Expected-score model for the GM2 V3 mission (rules snapshot 2026-10-29). Inputs are human-estimated, unconditional success probabilities for each | `tests/strategy-v3.test.js` | — |
| `tools/` | `summarize-v13-validation.js` | Project utility: summarize v13 validation. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `telemetry_schema.py` | Standard-library validator for telemetry records (schemas/telemetry-v1.json). | `firmware/host_tests/test_runner_bench.py` | — |
| `tools/` | `tire-fixture-v10.js` | Builds derived/tire-fixture-v10: a repeatable E04 tire-handling test kit. It contains a 1:1 pit-box corner with tire targets, a pose jig, round-1 DOE run sheets (L9 x 5 repeats + 5 nominal = 50 per | `tests/tire-fixture-v10.test.js`<br>`software/stockcar/tests/test_e04_analysis.py` | — |
| `tools/` | `tournament-v7.js` | Tournament-aware score model for the GM2 V3 Stock Car Race (rules snapshot 2026-10-04 manuals, archived 2026-10-29). GM1 V3 §4.7.1 ranks Qualification | `tests/team-brief-v7.test.js`<br>`tests/tournament-v7.test.js` | — |
| `tools/` | `train-rl-policy.py` | Train the project's first RL policy with the cross-entropy method, dependency-free. | GAP | No direct test or same-study verifier found in the audited test suites. |
| `tools/` | `train-world.py` | Train a linear ``LearnedPolicy`` for one ruleset world with the cross-entropy method, dependency-free. | `tools/verify-world.js` | — |
| `tools/` | `verify-apriltag-41h12-v7.js` | Verifies the sealed AprilTag 41h12 v7 package without re-running the Python experiment (that needs uv and network access). `--seal` rewrites manifest.json. | `tools/verify-apriltag-41h12-v7.js` | — |
| `tools/` | `verify-avoid-v11.js` | Verifies derived/avoid-v11: input/output hashes and the footprint-sensitivity decomposition. Regenerate with: uv run --no-project --python 3.12 python -B -I tools/evaluate-avoid-v11.py | `tools/verify-avoid-v11.js` | — |
| `tools/` | `verify-avoid-v12.js` | Verifies derived/avoid-v12: input/output hashes and the study's structure. It checks the recorded numbers, not a hoped-for direction — completion, contact-free, infeasible and attribution counts | `tools/verify-avoid-v12.js` | — |
| `tools/` | `verify-cad-v13.js` | Project utility: verify cad v13. | `tools/verify-cad-v13.js` | — |
| `tools/` | `verify-cad-v13.py` | Read-only v13 source, asset and fit verification; never rebuilds artifacts. | `tools/verify-cad-v13.py` | — |
| `tools/` | `verify-competition-mockup-v10.js` | Rebuilds derived/competition-mockup-v10 in memory, compares every file, and checks the fit facts. | `tools/verify-competition-mockup-v10.js` | — |
| `tools/` | `verify-confirmation-packet-v3.js` | Project utility: verify confirmation packet v3. | `tools/verify-confirmation-packet-v3.js` | — |
| `tools/` | `verify-connected-navigation-v3.js` | Some sealed v3 records contain an accidentally duplicated absolute repository root, and the repo was renamed ieee -> roboticThingAvoidance, so historical /workspace/ieee prefixes are remapped to | `tools/verify-connected-navigation-v3.js` | — |
| `tools/` | `verify-dr-registry-v1.js` | Project utility: verify dr registry v1. | `tools/verify-dr-registry-v1.js` | — |
| `tools/` | `verify-drivetrain-mule-v10.js` | Verifies derived/drivetrain-mule-v10 without CadQuery: text outputs are rebuilt and compared, the manifest is recomputed, and the STL files are parsed and checked for closure, size and volume. | `tools/verify-drivetrain-mule-v10.js` | — |
| `tools/` | `verify-drivetrain-mule-v4.js` | Project utility: verify drivetrain mule v4. | `tools/verify-drivetrain-mule-v4.js` | — |
| `tools/` | `verify-electrical-selection-v6.js` | Project utility: verify electrical selection v6. | `tools/verify-electrical-selection-v6.js` | — |
| `tools/` | `verify-envelope-v10.js` | Verifies derived/envelope-v10: hashes, then recomputes the physics and lap-model claims here with hand formulas, independently of the Python that produced them. | `tools/verify-envelope-v10.js` | — |
| `tools/` | `verify-estimation-v10.js` | Verifies derived/estimation-v10: hashes, the evaluation matrix, the ablation and run-level consistency. Regenerate with: uv run --no-project --python 3.12 python -B -I tools/evaluate-estimation-v10.py | `tools/verify-estimation-v10.js` | — |
| `tools/` | `verify-full-mission-v10.js` | Verifies derived/full-mission-v10: hashes, the mission matrix, summaries and every score, recomputed here from each mission's raw fields. Regenerate with: | `tools/verify-full-mission-v10.js` | — |
| `tools/` | `verify-full-mission-v11.js` | Verifies derived/full-mission-v11: input/output hashes and the sensed-vs-truth mission comparison. Regenerate with: uv run --no-project --python 3.12 python -B -I tools/evaluate-full-mission-v11.py | `tools/verify-full-mission-v11.js` | — |
| `tools/` | `verify-hardware-development-v3.js` | Project utility: verify hardware development v3. | `tools/verify-hardware-development-v3.js` | — |
| `tools/` | `verify-humans-v1.js` | Project utility: verify humans v1. | `tools/verify-humans-v1.js` | — |
| `tools/` | `verify-integration-studio-v6.js` | Project utility: verify integration studio v6. | `tools/verify-integration-studio-v6.js` | — |
| `tools/` | `verify-lap-study-v10.js` | Verifies derived/lap-study-v10: input and output hashes, layout counts, internal consistency of contact-free flags and aggregates. Regenerate with: uv run --no-project --python 3.12 python -B -I tools/lap-study-v10.py | `tools/verify-lap-study-v10.js` | — |
| `tools/` | `verify-maneuver-v10.js` | Verifies derived/maneuver-v10: hashes, row counts, and the route library, whose clearances, limits and times are recomputed here without the Python geometry. Regenerate with: | `tools/verify-maneuver-v10.js` | — |
| `tools/` | `verify-mechanism-envelope-v6.js` | Project utility: verify mechanism envelope v6. | `tools/verify-mechanism-envelope-v6.js` | — |
| `tools/` | `verify-mechanism-prototyping-v3.js` | Project utility: verify mechanism prototyping v3. | `tools/verify-mechanism-prototyping-v3.js` | — |
| `tools/` | `verify-mission-v10.js` | Verifies derived/mission-v10: input and output hashes, the evaluation matrix, and run-level consistency. Regenerate with: uv run --no-project --python 3.12 python -B -I tools/evaluate-mission-v10.py | `tools/verify-mission-v10.js` | — |
| `tools/` | `verify-mule-dynamics-v5.js` | Project utility: verify mule dynamics v5. | `tools/verify-mule-dynamics-v5.js` | — |
| `tools/` | `verify-mule-studio-v4.js` | Project utility: verify mule studio v4. | `tools/verify-mule-studio-v4.js` | — |
| `tools/` | `verify-order-a-procurement-v4.js` | Project utility: verify order a procurement v4. | `tools/verify-order-a-procurement-v4.js` | — |
| `tools/` | `verify-organizer-cad-v10.js` | Re-derives derived/organizer-cad-v10 from the organizer .f3d bytes and checks every output byte for byte, plus the key field facts. CAD geometry from a June 2026 design file; not a measured field. | `tools/verify-organizer-cad-v10.js` | — |
| `tools/` | `verify-passability-atlas-v10.js` | Verifies derived/passability-atlas-v10: input and output hashes, matrix completeness and internal consistency. --reproduce re-plans a few Part B cases in Python (uv) and compares the results. | `tools/verify-passability-atlas-v10.js` | — |
| `tools/` | `verify-planner-diagnostics-v3.js` | Some sealed v3 records contain an accidentally duplicated absolute repository root, and the repo was renamed ieee -> roboticThingAvoidance, so historical /workspace/ieee prefixes are remapped to | `tools/verify-planner-diagnostics-v3.js` | — |
| `tools/` | `verify-practice-field-v10.js` | Rebuilds derived/practice-field-v10 in memory, compares every file, and checks the packet's internal consistency. An agent-prepared build packet; nothing has been built or measured. | `tools/verify-practice-field-v10.js` | — |
| `tools/` | `verify-qa-pack-v10.js` | Verifies derived/qa-pack-v10: every manual quote appears at its cited paragraph line, every earlier question maps to a new one, paste text fits Discord, outputs match a fresh build, and the live answer | `tools/verify-qa-pack-v10.js` | — |
| `tools/` | `verify-recovery-v1.js` | Verifies recovery-v1 structure and hashes; results are checked as measured, not for a desired direction. Regenerate: uv run --no-project --python 3.12 python -B -I tools/evaluate-recovery-v1.py | `tools/verify-recovery-v1.js` | — |
| `tools/` | `verify-rl-v1.js` | Verifies derived/rl-v1: input/output hashes and the scaffold's structure. It checks reproducibility and that every measured field is present and in range; it does not assert a | `tools/verify-rl-v1.js` | — |
| `tools/` | `verify-rl-v2.js` | Verifies derived/rl-v2: input/output hashes and the trained-policy study's structure. It checks reproducibility and that every field is present and in range; it does not assert a hoped-for | `tools/verify-rl-v2.js` | — |
| `tools/` | `verify-robot-lab-v3.js` | Project utility: verify robot lab v3. | `tools/verify-robot-lab-v3.js` | — |
| `tools/` | `verify-robot-lab-v4.js` | Project utility: verify robot lab v4. | `tools/verify-robot-lab-v4.js` | — |
| `tools/` | `verify-robot-studio-v7.js` | Verifies Robot Studio v7 without rebuilding it (the build needs the npm toolchain in ~/.cache/ieee-studio-v7-build): input/output hashes, measured assembly invariants, | `tools/verify-robot-studio-v7.js` | — |
| `tools/` | `verify-robot-studio-v8.js` | Project utility: verify robot studio v8. | `tools/verify-robot-studio-v8.js` | — |
| `tools/` | `verify-sensing-v11.js` | Verifies derived/sensing-v11: input/output hashes and the characterisation of the camera models. Regenerate with: uv run --no-project --python 3.12 python -B -I tools/evaluate-sensing-v11.py | `tools/verify-sensing-v11.js` | — |
| `tools/` | `verify-simreal-v1.js` | Project utility: verify simreal v1. | `tools/verify-simreal-v1.js` | — |
| `tools/` | `verify-stopping-dynamics-v6.js` | Project utility: verify stopping dynamics v6. | `tools/verify-stopping-dynamics-v6.js` | — |
| `tools/` | `verify-tire-fixture-v10.js` | Rebuilds derived/tire-fixture-v10 in memory, compares every file, and checks the DOE structure. | `tools/verify-tire-fixture-v10.js` | — |
| `tools/` | `verify-world.js` | Verifies derived/rl-v3/<world> — the world named by software/stockcar/DEFAULT_WORLD, or an explicit first argument. It checks input/output hashes and the trained-policy study's structure, i.e. | `tools/verify-world.js` | — |
| `tools/` | `vision-transcribe.py` | Send an image (optionally downscaled) to an OpenRouter vision model and print its transcription. | GAP | No direct test or same-study verifier found in the audited test suites. |

## Explicit coverage gaps

25 of 149 tools currently have an explicit GAP. These are follow-up test gaps, not claims that the tools failed.

- `tools/build-cad-v11.py`
- `tools/build-team-brief-page-v7.py`
- `tools/build_field_tables.py`
- `tools/check-live-v11.js`
- `tools/check-live-v13.js`
- `tools/check-robot-studio-v8-browser.js`
- `tools/check-showcase-v11-browser.js`
- `tools/check-showcase-v13-browser.js`
- `tools/demo-mission-v10.py`
- `tools/dynamics-v9.js`
- `tools/evaluate-mission-v9.py`
- `tools/export-assembly-v11.js`
- `tools/export-assembly-v13.js`
- `tools/extract-sources.js`
- `tools/inspect-tire-stl.js`
- `tools/multimodel-vision.py`
- `tools/plan-mission-v9-avoidance.js`
- `tools/refine-stopping-dynamics-v6.js`
- `tools/refresh-confirmation-sources-v3.js`
- `tools/render-arena-guide.py`
- `tools/robot-studio-v7-parts.py`
- `tools/sensor-plane-figure-v7.py`
- `tools/summarize-v13-validation.js`
- `tools/train-rl-policy.py`
- `tools/vision-transcribe.py`
