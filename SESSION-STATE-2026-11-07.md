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