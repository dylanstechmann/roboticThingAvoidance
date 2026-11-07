# IEEE SoutheastCon 2027 Stock Car Race robot

A personal hobby and learning project for the IEEE SoutheastCon 2027 hardware competition (Daytona Beach; hardware matches on April 17, 2027).

Most planning, simulation and software here were developed with AI assistance across many sessions. Analyses run by an AI agent are labeled as agent-run; physical work is only claimed when the owner records it. **Nothing in this repository is a validated competition robot.**

This project is separate from the FAU team's own work. Roles, gates and dates in these documents are planning suggestions, not team decisions.

The latest one-file showcase is [`share/Showcase-v13.html`](share/Showcase-v13.html) — the v13 source-evidenced 3D CAD assembly and continuous-joint live contact study. Open it in a modern desktop browser; for iPhone, see `share/HOST-V13.txt`.

## Status — November 6, 2026

- **Physical work: none yet.** No parts are ordered, no practice field is built, no organizer Q&A has been posted and no robot has been tested.
- **Rules:** the V3.0 manuals are reviewed. The score model is 390 robot points + 10 publicity. V3.1 (start-flag details) is announced but not posted.
- **Hardware:** a drivetrain test mule (Order A, $177.25 researched) has been checked against Pololu's own CAD. That check found a 7 mm motor-shaft offset that the original mule kit missed. The corrected shaft-down mule deck is drawn in `derived/drivetrain-mule-v10/`, with a drill template, STEP/STL and caliper-driven regeneration; it is not yet printed. No competition chassis exists yet.
- **Software (all simulated):** the v10 work runs on the organizer's CAD field. Whole missions chain the supervisor, mission driver, route files, path tracker, pose estimator and the firmware's control loop on a corrected drivetrain model, and all 91 evaluation missions finished and parked (`derived/full-mission-v10/`).

  **Sensing and estimation (Tracks 1–2):** the AprilTag (pit box) and start flag are now sensed through camera models in an opt-in mission subclass, vehicle contacts are attributed by phase (`derived/avoid-v12/`), and the EKF estimator has a firmware port (`firmware/pico2/estimator.py`) that matches the host filter. The avoid-v12 sweep finds the binding constraint is the 10 in robot envelope against guide-size vehicles — no blend timing made a run contact-free — not the planner.

  **Reinforcement learning (Track 3):** an RL-vs-classical harness (`derived/rl-v1/`) and the first trained policy (`derived/rl-v2/`). A 38-weight linear policy trained by the cross-entropy method on seeds 0–3 completes 20/20 evaluation missions (mean score-like 240.75 vs the classical 267.75, with about half the vehicle-contact steps). It is not matched to a physical robot.

  **Known limits:** the base model tells the robot the vehicle positions; a sensed subclass sees only an assumed-size near face. The lap line is modeled but not yet wired into the route, the board estimator is not wired into `main.py`, and nothing has run on a board. Parameters are placeholders until bench and field measurements replace them.

  The older v9 simulator (`software/mission_v9.py`) stays frozen. Its nominal runs have no obstacles, its obstacle stand-in is about half size, and its 20 seeds are 3 deterministic runs.

## Start here

| To... | Open |
|---|---|
| See the latest source-evidenced parts and live contact study | `share/Showcase-v13.html` (offline, self-contained; guide: `robot-studio-v13/README.md`) |
| Open the v13 showcase on an iPhone | Host it once at a public static URL and share that link; iOS Files/Mail previews do not run the 3D studio (`share/HOST-V13.txt`) |
| Review the v13 mechanical blockers and actual validation outcomes | `docs/mechanical-readiness-v13.md` |
| See everything on the earlier shareable page | `share/Showcase-v10.html` (arena, parts, physics, simulation — offline, self-contained) |
| See the plan, gates and dates to April | `BACKCAST-2026-11.md` |
| Build the practice field | `derived/practice-field-v10/` (materials, layout coordinates, as-built template), from the organizer CAD in `derived/organizer-cad-v10/` |
| Build the drivetrain mule | `derived/drivetrain-mule-v10/` (shaft-down deck, risers, fit report, inspection templates) |
| Prepare the first bench session | `firmware/README.md` (Pico 2 MicroPython skeleton, not yet flashed) and `firmware/ORDER-B-BENCH-KIT.md` |
| See which sensors keep the robot localized (simulation) | `derived/estimation-v10/README.md` (agent-run, synthetic) |
| Rerun a mission log through the estimator | `tools/replay-log.py`, with the format in `schemas/mission-log-v1.json` |
| See what the drivetrain can do, and what limits it (simulation) | `derived/envelope-v10/README.md` (agent-run, synthetic) |
| See how the firmware follows routes, and which line to take past vehicles (simulation) | `derived/maneuver-v10/README.md` (agent-run, synthetic), with route tables in `route-library.json` |
| See whole simulated missions, from the route files the board would use | `derived/full-mission-v10/README.md` (agent-run, synthetic) |
| Watch one simulated mission | `share/Mission-Replay-v10.html` (offline; `tools/demo-mission-v10.py` runs another in seconds) |
| Know whether obstacles can be passed | `derived/passability-atlas-v10/README.md` (agent-run geometry; vehicle size decides it) |
| See lap times, contact rates and expected score over random layouts | `derived/lap-study-v10/README.md` (agent-run, synthetic) |
| Build a full-size mockup and sizing box | `derived/competition-mockup-v10/README.md` |
| Test tire pickup concepts | `derived/tire-fixture-v10/` (1:1 target, DOE sheets, `tools/analyze_e04_v10.py`) |
| Post the official Q&A questions | `derived/qa-pack-v10/QUESTIONS.md` and `PASTE.md`; record answers in `qa/answers-ledger.json` |
| Prepare the Dec 13 concept review | `derived/club-update-v10/CDR-PREP.md` |
| Read the short club summary | `derived/club-update-v10/CLUB-UPDATE.md` (corrections and next two weeks) and `derived/club-package-v9/CLUB-PRESENTATION.md` |
| See the FAU concept table updated to V3 | `derived/club-update-v10/SECTION-4.1-UPDATE.md` (PDF beside it) |
| Understand status and lineage | `PROJECT-STATUS.md` |
| Check rules and numbers | `CURRENT-RULES-2026-10-29.md`, `VERIFIED-FACTS.md` + `VERIFIED-FACTS-ADDENDUM.md`, `ERRATA-2026-11.md` |
| View the robot and field in 3D, offline | `share/Robot-Studio-v8.html` (guide: `derived/robot-studio-v8/README.md`) |
| Read older announcements and the October plan | `HISTORY.md` |

## AI orchestration

The repository includes a small local orchestration harness for routing narrowly scoped engineering tasks to external AI providers and recording advisory evidence.

- Guide: `docs/ai-orchestration.md`
- Tool: `tools/ai-orchestrate.js`
- Tasks: `derived/ai-orchestration/tasks.json`
- Evidence: `derived/ai-orchestration/evidence/`

Everything produced by this harness is labeled agent-run and advisory. It is not owner-reviewed engineering evidence until the owner explicitly marks it reviewed.

The harness never stores API credentials. Provider keys are loaded automatically from `~/.config/ai-keys.env` or from environment variables named in `derived/ai-orchestration/registry.json`.


## Sharable showcase release habit

When a new one-file showcase is ready, follow this recurring habit so the GitHub front page always shows the latest showable HTML at the top, before the status detail:

1. Produce or refresh the one-file HTML (for v13: `node tools/build-showcase-v13.js`).
2. Run the focused v13 tests plus `node tools/check-all.js`.
3. Put the new HTML in `share/` (e.g. `share/Showcase-v13.html`) and keep earlier pinned showcase HTML files unchanged.
4. Point this README's “latest one-file showcase” line and the first “Start here” row at the new file.
5. Run `secrets-guard --staged`, commit, and push to `main`.
6. Desktop reviewers open the HTML in a browser. iPhone reviewers need a hosted public URL; see `share/HOST-V13.txt`.

## Run the checks

```sh
node tools/check-all.js          # about 5 minutes
node tools/check-all.js --full   # adds a 3-minute reproduction check
```

`check-all` runs:
- the Node test suite;
- every `tools/verify-*.js` artifact verifier;
- the Python suites (CPython 3.12 through uv);
- a check that the run left the working tree unchanged.

It was tested with Node v24.18.1, uv 0.13 and CPython 3.12.16. It checks software and reproducibility, not robot performance. `npm test` runs only the Node tests.

## Repository map

| Path | Contents |
|---|---|
| `derived/<name>-vN/` | Versioned packages. Most are sealed by a `manifest.json` of input and output hashes and checked by `tools/verify-<name>-vN.js`. To change one, add a new version. |
| `tools/` | Generators, verifiers, `check-all.js` |
| `tests/` | Node tests |
| `software/` | Python simulators, estimator, route tools and match logic, with tests |
| `firmware/` | Pico 2 MicroPython skeleton (bench, safety and mission driver) with CPython host tests; not flashed |
| `schemas/` | Shared data formats (telemetry v1, mission log v1) |
| `share/` | Showcase page (v10), offline HTML studios (v4–v8) and mission replays (v10) |
| `sources/` | Archived organizer and vendor files with hashes |
| `derived/audits/` | Dated audits, including the November 3 baseline |
| `*-vN.json` (root) | Inputs to the matching packages |
| `SESSION-STATE-*.md` | Dated handoffs |
| `website/` | Older "Road to Daytona" site (separate git history). It still shows V2 scoring and is historical. |

## House rules for people and agents

- **Never edit pinned files**; record corrections in `VERIFIED-FACTS-ADDENDUM.md`, `ERRATA-2026-11.md` or a new package version. Pinned files:
  - `VERIFIED-FACTS.md`, `RULES-AND-SOURCES.md`, `GEOMETRY-AND-CONCEPTS.md`, `STRATEGY-AND-ARCHITECTURE.md`, `RESOURCES-AND-BUDGET.md`, `CURRENT-RULES-2026-10-29.md`;
  - any output listed in a package manifest.

  Sealed manifests pin these, and an edit silently breaks verifiers.
- Run `node tools/check-all.js` after any change, including documentation.
- Keep negative results. Never relax a rule, size or time limit to make a route pass.
- Agents do not buy parts or contact the organizers. Label agent-run work, and claim physical results only from recorded measurements.

## Credits

- **Rules, field and game elements:** the IEEE SoutheastCon 2027 hardware competition organizers. Game Manuals 1 and 2 (V3.0), the arena build guide, the arena Fusion 360 file and the spare-tire CAD/STL are archived with hashes in `sources/`.
- **Drivetrain CAD and data:** Pololu product pages, datasheets and STEP models (`sources/hardware-2026-10-31/`, `sources/hardware-2026-11-01/`, `sources/electrical-2026-10-31/`).
- **Software used:**
  - AprilTag 3, through `pupil-apriltags`;
  - three.js and esbuild for the studios;
  - cascadio and trimesh for STEP conversion;
  - Blender for the field model;
  - Playwright with headless Chromium for browser checks;
  - Node.js, Python and uv.
- **AI assistance:**
  - AI coding assistants, including Claude (Anthropic), produced most of the analysis, software and documentation across many sessions.
  - The project history names other assistants for some earlier work.
  - The October 29 drawing transcription used a panel of vision models (Gemini, Qwen, Nemotron, Claude and GPT), listed in `tools/multimodel-vision.py`.

  The owner reviews and decides; agent output is labeled as such.
