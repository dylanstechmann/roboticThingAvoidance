# Session State — 2026-11-07 · roboticThingAvoidance (worlds)

## Goal
Close out and publish the eight-world ruleset branch strategy: six functional worlds with their existing sealed RL-v3 artifacts, plus two structural placeholder branches for rules whose simulator semantics remain unresolved. Keep simulator behavior and `main` unchanged.

## Confirmed scope
- The owner approved structural Option B: all eight named world branches exist; QA04 `enforced` and QA03 `small` implementation is deferred.
- `world-ccw-line-sq-enf-align` and `world-ccw-line-sq-adv-small` set `DEFAULT_WORLD` but intentionally retain `WorldMissionSim.__init__`'s `NotImplementedError`, have no `derived/rl-v3/<world>/` seal, and are not promotion-eligible.
- The six functional seals are complete and were not retrained or regenerated during the close-out. Training budgets remain intentionally non-uniform.
- Final branch-tip hashes are deliberately omitted here: committing a tip table makes the handoff stale immediately. Query Git for current tips; immutable seal commits are recorded below.

## Existing scaffold and measured seals
Steps 1–6 remain on primary: `ruleset.py`/`worlds.json`, `world_routes.py`, `mission_worlds.py`, `docs/worlds.md`, `tools/train-world.py`, `tools/evaluate-world.py`, `tools/verify-world.js`, and world tests. Primary passed full `check-all` 43/43 at seal commit `f691e18`; the close-out's final-tip gates are mandatory before publication.

| world / functional branch | immutable seal commit | CEM generations | best fitness | learned eval | classical eval |
|---|---|---:|---:|---|---|
| `world-ccw-line-sq-adv-align` | `f691e18` | 10 | 74.715 | 17/20, score-like 219.5 | 20/20, score-like 267.75 |
| `world-ccw-gate-sq-adv-align` | `3e2d969` | 10 | 74.715 | 17/20, score-like 219.5 | 20/20, score-like 267.75 |
| `world-ccw-line-rd-adv-align` | `19fa738` | 3 | 28.980 | 0/20, score-like 30 | 20/20, score-like 283.5 |
| `world-ccw-gate-rd-adv-align` | `58c3a70` | 3 | 28.980 | 0/20, score-like 30 | 20/20, score-like 283.5 |
| `world-ccw-line-sq-adv-yaw` | `44ad8bd` | 10 | 99.833 | 20/20, score-like 244.75 | 20/20, score-like 282.25 |
| `world-cw-line-sq-adv-align` | `2d4e0d4` | 10 | 54.918 | 0/20, score-like 60.25 | 20/20, score-like 249.75 |

Random was 0/20, score-like 10 on every world. The round-body CEM curves are flat at the zero-weight baseline 28.980; that is recorded as measured, not as learned improvement. Every seal contains exactly five own-world files and all manifest hashes validate.

## Branch model
- Six functional branches: `world-ccw-line-sq-adv-align`, `world-ccw-gate-sq-adv-align`, `world-ccw-line-rd-adv-align`, `world-ccw-gate-rd-adv-align`, `world-ccw-line-sq-adv-yaw`, `world-cw-line-sq-adv-align`.
- Two structural placeholders: `world-ccw-line-sq-enf-align`, `world-ccw-line-sq-adv-small`.
- Each branch has only its own `DEFAULT_WORLD`; no branch carries another world's seal.

## KEY CONSTRAINT (do not violate)
Pinned — hashed by existing sealed verifiers; MUST stay byte-identical: `software/stockcar/{mission.py, routes.py, field.py, obstacles.py, supervisor.py, lapmodel.py, passage.py, geometry.py, sensors.py, sensors_camera.py, estimator.py}` + `derived/organizer-cad-v10/field-v10.json`. ALL new world behavior must land in UNPINNED files (`mission_worlds.py`, `world_routes.py`, and the planned `world_geometry.py` / `world_layouts.py`). `tests/test_worlds.py` pins `mission.py` SHA-256 `346fb5c977fddaaad7d790afcb466beacb3f2beeebe01803befb9da004032678`.

Relevant facts: `random_layout` (pinned) hardcodes `GUIDE_PLUSH` and has no shape arg → "small" needs a world-specific layout generator. `lane_plan`/`classical_action` are advisory (whole corridor) → "enforced" needs new logic. White-line marking lives in `field-v10.json` `clearances_in` (`side_lane_wall_face_to_marking_outer_edge` 10.53 / `inner_lane_marking_inner_edge_to_divider_face` 11.071), readable via `Field.data` WITHOUT editing `field.py`; band ≈0.9 in wide.

## Relevant implementation facts
- Pinned `mission.random_layout` hardcodes `GUIDE_PLUSH` and has no shape argument, so `small` needs a future world-specific layout generator in an unpinned module.
- `lane_plan`/`classical_action` are advisory over the whole corridor, so `enforced` needs new behavior rather than a default. White-line data is in `field-v10.json` `clearances_in` (`side_lane_wall_face_to_marking_outer_edge` 10.53 / `inner_lane_marking_inner_edge_to_divider_face` 11.071), readable through `Field.data` without editing `field.py`; the band is about 0.9 in wide.

## Tooling usage (per world W)
- `uv run --no-project --python 3.12 python -B -I tools/train-world.py --world W` → `derived/rl-v3/W/{trained-weights,training}.json`
- `... tools/evaluate-world.py --world W` → `derived/rl-v3/W/{report,summary,manifest}.json` (seal; classical/random/learned on eval seeds 100–119)
- `node tools/verify-world.js` (reads `DEFAULT_WORLD`); `node tools/check-all.js` runs the full gate.

## Deferred semantics
- **QA04 `enforced`:** decide which white-line boundary governs and whether enforcement is a hard route constraint or a measured crossing penalty. A hard constraint is closer to “stay in lane,” but a 10 in robot in an approximately 11 in lane cannot pass an 8.2 in obstacle. The earlier crossing-penalty default measured the wrong behavior.
- **QA03 `small`:** the open question is toy interpretation, not only physical size. Real toy dimensions are 6.5 × 3.25 in; the current placeholder is 8 × 4 in. Do not silently promote either number as a measured organizer fact.
- Future work belongs in `world_geometry.py`, `world_layouts.py`, `ruleset.py`, and `mission_worlds.py` after owner approval; it requires new tests and a newly sealed world.

## Validation and publication
- One shared close-out documentation commit propagates this file, `implementation_plan.md`, and `docs/worlds.md` to all eight branches before final-tip validation.
- Full `check-all` must pass on the six functional final tips; actual counts and durations belong in the execution handoff and `/tmp/robotic-world-closeout/`, not in stale tip tables here.
- Placeholder branches are expected to fail `verify-world.js` because no seal exists. That is deferred behavior, never reported as a green gate.
- Publish primary by fast-forward, siblings with explicit hash-valued `--force-with-lease`, and new placeholder refs with ordinary non-force pushes. Do not update `main` (`f56fb53`) without separate owner approval.

## Re-orient after compaction

## AI orchestration next phase (2026-11-07)

- The eight-world branch strategy is complete. The next phase is AI-assisted physical bring-up, not more simulation.
- A local orchestration harness is planned to route narrowly scoped tasks—organizer Q&A drafting, CAD fit review, firmware bring-up, practice-field planning, and rules cross-checks—to suitable external AI providers.
- All outputs are advisory and must be explicitly owner-reviewed before being treated as engineering evidence.
- The API keys pasted into this session are compromised and must be rotated before any live provider call.
- New credentials must be stored only in private provider consoles or `~/.config/ai-keys.env`; they must never be committed to this repository.
- The harness now loads `~/.config/ai-keys.env` automatically, so keys do not have to be exported or typed manually.
- Live advisory runs were exercised with OpenRouter, NVIDIA Nemotron omni reasoning, Fireworks GPT-OSS, and DeepInfra; all outputs remain advisory and owner-review-gated.
- No changes are planned to `main` or to the eight published world branches.

Run `git log --oneline --decorate`, `git branch -avv`, `git ls-remote --heads origin 'refs/heads/world-*'`, and read `implementation_plan.md`, `docs/worlds.md`, and this file. The pinned-file constraint is the first trap: never edit `mission.py`, `routes.py`, `field.py`, `obstacles.py`, or the other pinned inputs. Confirm placeholders remain semantic stubs before changing simulator code.

## AI orchestration harness expansion (2026-11-07)

- The harness registers all 28 key families from the private key store: 12 live chat/review providers, three planned chat families (inception, omtx, japanfold), five web-search providers, two page-read providers, five scholarly-search providers, and the Modal runtime as planned.
- Providers carry `family`, `cost_rank` (1 cheapest to 5), and `max_context_tokens`. Automatic selection prefers the cheapest live provider whose family matches the task kind and never auto-selects `planned` transports.
- Prompts over the context budget are compacted into a digest first (default 12,000 tokens, well below 200k-token windows): live mode uses the cheapest credentialed summarize provider, dry-run uses a deterministic local digest. Digests land in `derived/ai-orchestration/context/`.
- New live routes mirror the vendored `.agent-tools/mcp/*` endpoint conventions: web search (Exa, Brave, Brave Answers, Jina, Firecrawl), page read (Jina Reader, Firecrawl scrape), and scholarly search (OpenAlex, Semantic Scholar, CORE, PubMed, ORCID).
- New advisory tasks exercise each family: `rules-update-scan`, `literature-search`, and `vendor-page-read` (reads the BOM 37D mm gearmotor product page, Pololu #4754). The `vendor-cad-research` task added in that commit was removed the same day for violating the no-vendor-CAD constraint; `cad-motor-gap-review` was re-pointed to manufacturer-page and bench evidence.
- Owner review workflow: `node tools/ai-orchestrate.js --review --task <id> --status accepted|rejected [--notes ...]` writes `<task-id>.review.json` and mirrors the decision into the run record. Reviewing is an owner action; the agent does not review its own outputs.
- Fixes along the way: baseten provider `auth_env` typo (`BASTEN_API_KEY` → `BASETEN_API_KEY`), `--help` now reachable, and the jina/omtx credential patterns tightened so environment-variable names do not trip the guard.
- Tests: `tests/ai-orchestration-provider.test.js` (19 offline tests with stubbed fetch) alongside the original 11.

## Owner constraint — no vendor CAD (2026-11-07)

- The owner confirmed a standing decision: this project uses **no vendor CAD** and **only open-source software**. The rule had been documented only in archived plan-history files (`docs/plans/implementation-plan-v13-history.md`, `docs/plans/implementation-plan-v11-history.md`) and was missed during the harness expansion.
- The rule is now written into `AGENTS.md` ("Owner-set constraints"), `CLAUDE.md`, this file, `docs/ai-orchestration.md`, and `PROJECT-STATUS.md`, and a policy test (`no task targets vendor CAD research`) fails the suite if vendor-CAD research is reintroduced.
- The `vendor-cad-research` task, prompt, and dry-run evidence are deleted; `vendor-page-read` now targets the correct BOM motor page (Pololu #4754, not #1067).
- The sealed v13 vendor-geometry findings are marked historical-only: `docs/mechanical-readiness-v13.md` carries a Historical status section and `derived/cad-v13/README.md` marks the artifact directory. Verifier-pinned artifacts stay byte-identical so the v13 study remains verifiable.
- `cad-motor-gap-review` is re-pointed to `docs/motor-dimensions-published.md` (page-published dimensions of Pololu #4754) and `firmware/ORDER-B-BENCH-KIT.md`; its sealed live run record stays as history.

## E03 floor-trial firmware (2026-11-07)

- Added the missing middle of the E03 chain for BACKCAST G1 ("E03 floor trials", due Dec 6): `firmware/pico2/floor_e03.py` (closed-loop straight/spin trials, encoder-odometry stopping with braking lookahead — the shaper's yaw decel alone would overshoot a 360-degree spin by ~25 degrees, five times the sealed 5-degree median-spin gate), a `main.floor()` REPL entry (boot stays IDLE), and `tools/bench/log_to_e03.py` (one CSV row per `/e03-<id>.jsonl`, template columns and trial-id formats exact; human-measured fields stay blank).
- Sealed contract untouched: `tools/mule-measurements-v4.js`/`-v10.js`, the `derived/drivetrain-mule-v10/**` package (tool-generated, hash-verified), the templates, and the telemetry schema (trials log in the existing `DRIVE` mode).
- The estimator/mission path stays deliberately unwired (`mission_driver.py`: no pose source until the sensors are chosen, G2 Dec 13). E03 needs no gyro, reflectance or ToF — drift and spin error are physical (tape) measurements.
- Host tests: `firmware/host_tests/test_floor_e03.py` (7 tests, plant-backed; note the plant couples yaw to forward velocity, so in-place spin ground truth is the wheel differential, not body yaw). Firmware suite 79 tests PASS; MicroPython lint clean. Nothing run on hardware; flashing and floor trials remain owner actions under the approved setups, after E02A/E02.

## Computer-only study pack (2026-11-07)

### Recovery and DR registry

- New unpinned modules `recovery.py`, `recovery_sim.py`, `study_stats.py`, evaluator `tools/evaluate-recovery-v1.py`, and seals `derived/recovery-v1/` + `derived/dr-registry-v1/`. The matrix is eight scenarios × four behaviors (`stall_stop`, `lateral_shift`, `replan_lanes`, `auto`) × two poses × 20 seeds = 64 cells and 1,280 DR entries.
- The former high-side false pass was fixed: passage now requires a directional crossing on the LAP route inside the blocked corridor with no blocker contact. All 640 runs in the four spanning scenarios are `blocked`; high-side start/pit positions no longer count as passage.
- `auto` results are identical in true/EKF pose: mid-band low/high pass 17/20 (three blocker contacts each), corner-band low/high pass 20/20. No run is fully contact-free because ordinary quadrant-vehicle contacts are reported separately from blocker recovery.
- Router pass is correctly defined as zero planned contact vehicles on the unblocked v10 route, not baseline completion. All 40 baselines complete, but none has a router pass, so recovery-success/router-pass Spearman and p-value are null. Against planned contact count, midrank Spearman is 0.0474 with a 10,000-shuffle whole-cluster permutation p=0.007999. There are 40 independent pose/seed clusters repeated over eight scenarios, not 320 independent baseline observations; the small coefficient is not a practical router/recovery link.
- `backtrack` and `pit_bypass` remain inexpressible in the forward-only oval/pit route model and were not fabricated. Sensed blocker detection is a follow-up.
- `tools/dr-registry.js` provides host-only `query`, `add-physical`, and `stats`. Sim entries stay hash-sealed; physical observations are owner-appended and are preserved on study regeneration. Example: `node tools/dr-registry.js query --side low --x 60 --kind guide-plush`. The robot has no registry read/write path.

### Sim-to-real expected-pass screening

- `derived/simreal-v1/` has 18 records (six worlds × classical/learned/random), 10,000 deterministic draws per record, and `drift-samples.json` provenance. Only the primary world seal is in this working tree, so the other five are read and fully hash-validated through immutable Git objects at their world-branch commits; no checkout/merge/branch edit occurs.
- Current input is `provisional-plant`: nine straight and 18 spin samples from the 2/4/6 kg × friction 0.20/0.25/0.30 host grid. Lateral drift is essentially zero and maximum absolute encoder spin error is 2.29 degrees. All 18 `fragile` flags are false under this input, which is **not** evidence of physical robustness.
- The expected-pass value is an E03-gate transfer index (Jeffreys sim posterior × empirical 25 mm drift/5 degree spin survival), not a full-mission physical-pass probability. After owner E03 trials, rerun with `uv run --no-project --python 3.12 python -B -I tools/evaluate-simreal-v1.py --e03 measurements/.../E03-trials.csv`; completed measured rows must carry real provenance.

### Isolated-human planner safety

- `derived/humans-v1/` has ten cells × 20 seeds = 200 runs with independent static 10 in discs and immediate first-contact abort. The 18 in/12 in stand-ins could not fit ten non-overlapping placements for every seed, so the 10 in stand-in is an explicit deviation, not an adult-body measurement.
- N=1 completes 8/20 with 12 contacts/aborts. Every seed has a contact by N=2, so N=2..10 all complete 0/20. Run-level clearance percentiles and Wilson intervals are in the report. Placement-set SHA-256 IDs prove 20 distinct seed sets and nested reuse only across each seed's N slices.
- N also adds zones in start/pit-lane/lane-change/turn order, so trends are confounded and no causal/monotonic claim is made. Straight lane-change humans use oracle truth; start, pit and turns are not replanned. This is not human perception or a physical safety qualification.

### Folder audit, validation and handoff

- `docs/folder-breakdown.md` accounts for all 149 files under `tools/` and `tools/bench/`; 25 have explicit GAP rows rather than invented coverage. `tests/folder-breakdown.test.js` checks exact inventory coverage and real goal-test paths.
- Full `node tools/check-all.js`: **47/47 PASS** — 69 Node files/332 passes, 43 verifiers, 245 software tests, 79 firmware host tests, and the working-tree immutability check. Focused recovery regression is 11 tests; shared statistics, simreal and humans add 16 more.
- Remaining computer-only follow-ups: the 25 documented test gaps, JSON task-object validator, sensed blocker detection, human perception after G2, firmware DR lookup after G2, and nonlinear policy work. Owner physical work remains E02A/E02/E03, field/vehicle measurement and the G2 decisions; this pack did not perform or simulate-owner-approve any of them.

## Key rotation, GitHub publication and live advisory runs (2026-11-07, later session)

- The owner supplied rotated provider credentials in chat. They are stored only in the private key store `~/.config/ai-keys.env` (mode 600, outside this repository; 29 entries including `GITHUB_PERSONAL_ACCESS_TOKEN`) and load automatically into the harness and `.agent-tools/mcp/*`. No key value is committed anywhere; the secrets-guard scans and `readJsonFile`'s credential-content guard remain the repo-side defenses. The values passed through a chat transcript, so the morning session's rotate-before-live-use rule applies to this set as well.
- The `gh` CLI now authenticates with the owner's new GitHub token (`gh auth login --with-token`; `gh auth setup-git` wired the git credential helper), so pushes need no token in any URL, config file or command line.
- Published `next-phase-v10` to GitHub as a fast-forward (`1f77339..ecdbc7f`): the v13 one-file showcase, the shared release habit, the `*.tar.gz` gitignore rule, the v11–v13 showcase consolidation and the main merge. All other branches were already in sync; `main` stays at `f56fb53`. A pre-push secrets scan of the pushed diff was clean.
- Live advisory runs with the rotated keys (all `review: pending`, agent-run): `rules-update-scan` via `exa-search` (the official SoutheastCon 2027 student-competitions page, the Arena Build Guide PDF and the 2026 ruleset PDF surfaced; still no V3.1 posting in the results), `literature-search` via `openalex-search` (path-planning, obstacle-avoidance and odometry references), and `organizer-qa-draft` via `openrouter-general` — the harness rejected `deepinfra-general` for a `planning` task (role mismatch) and auto-selected OpenRouter, exercising the cost-routing fallback end to end. The evidence files and run records were regenerated; prior versions remain in Git history.
- Implemented the JSON task-object validator follow-up: `validateTaskManifest()` in `tools/ai-orchestrate.js` runs before any task or review and enforces that every `preferred_providers` id exists in the registry with at least one live route for the task kind, `output_name` is a safe `.md` file name, `query` is present for search/read/scholar kinds, `owner_review` is boolean, and `prompt_file`/`input_files` are relative in-repo paths. `tests/ai-orchestration-tasks.test.js` adds 11 offline tests (focused harness suites: 42/42 pass). The `check-all` step count is unchanged at 47 because the new tests join the single Node stage.
- Fixed a secrets-guard false positive: the full-worktree scan flagged `share/Showcase-v10.html` as carrying a Brave key, but both matches (`BSAGBb...`, `BSAY9d...`) are random substrings inside the file's embedded base64 PNG data URIs, not credentials. `scan_secrets.py` now strips `data:...;base64,` blobs before pattern matching (SKILL.md updated), so the standing pre-commit gate is usable again; keys outside a blob on the same line are still caught. `Showcase-v10.html` itself is untouched — it is a hashed input of the sealed v13 showcase build (`tools/build-showcase-v13.js`).
- The owner directed that the japanfold provider not be used ("no japanese"): its key is removed from the private key store (28 entries now), the planned `japanfold-general` entry is removed from `derived/ai-orchestration/registry.json`, and `docs/ai-orchestration.md` plus the provider test's key-family list are updated to match. The `jf_live_` credential-detection patterns in the harness and secrets-guard remain — they are leak guards, not provider usage. Earlier dated records keep their original text.
