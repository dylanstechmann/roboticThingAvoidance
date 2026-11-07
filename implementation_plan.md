# Implementation Plan

[Overview]

Enforce the owner's standing decision that this project uses no vendor CAD and only open-source software: write the rule into the durable agent-memory files where it was missing, remove the vendor-CAD research task that violated it, mark the existing v13 vendor-CAD findings as historical-only, and re-point the CAD gap-review task to manufacturer-page and bench evidence.

Scope and context:

- The rule already exists in archived plan-history documents (`docs/plans/implementation-plan-v13-history.md`: "No proprietary vendor CAD" = no proprietary CAD application; use CadQuery/OpenCASCADE; and `docs/plans/implementation-plan-v11-history.md`: open-source CAD/software priorities; manufacturer documentation as evidence), but it never reached the living memory files (`AGENTS.md`, `CLAUDE.md`, `SESSION-STATE-2026-11-07.md`) that agents re-orient from. That gap let the harness expansion (commit `5a069a5`) add a `vendor-cad-research` task that explicitly hunts vendor CAD files.
- Owner decision, recorded 2026-11-07, strictest scope: (1) no vendor CAD files at all going forward; (2) only open-source software for design work; (3) manufacturer pages/datasheets/drawings remain allowed **evidence** (published claims, not received-part measurements); (4) existing v13 vendor-CAD findings stay as committed history, marked historical-only; (5) `cad-motor-gap-review` re-points away from vendor-CAD-derived inputs.
- Archived vendor STEP/PDF files under `sources/` stay in place: they are committed history pinned by `tools/verify-cad-v13.py` (via `derived/cad-v13/manifest.json` `inputHashes`), and the sealed v13 study must remain verifiable. They are never again a geometry authority.
- `docs/mechanical-readiness-v13.md` is NOT among the manifest `inputHashes` (verified), so annotating it is safe. `derived/cad-v13/fit-results.json` IS live-verified (the verifier re-computes fit rows and compares `(id, variant, status)`), so its content is not edited; its historical marking lives in a new `derived/cad-v13/README.md`.
- All work happens on the `ai-orchestration` branch. `main` and the eight world branches are untouched. No new npm/pip dependencies; no live provider calls; no network in tests.

[Types]

1. `TaskSpec` changes (`derived/ai-orchestration/tasks.json`)

   - Remove the `vendor-cad-research` entry entirely (id, kind, title, input_files, prompt_file, preferred_providers, output_name, query, context_policy, owner_review).
   - `cad-motor-gap-review.input_files`: from `["docs/mechanical-readiness-v13.md", "derived/cad-v13/fit-results.json"]` to `["docs/motor-dimensions-published.md", "firmware/ORDER-B-BENCH-KIT.md"]`. `kind` stays `vision`; `preferred_providers` stays `["nvidia-robotics"]`.
   - `vendor-page-read.query`: from `https://www.pololu.com/product/1067` to `https://www.pololu.com/product/4754`. (4754 is the BOM 37D mm gearmotor archived in this repo; 1067 was an unrelated variant picked by an earlier URL grep.)
   - All other entries unchanged.

2. Published-dimension record (new `docs/motor-dimensions-published.md`)

   - Provenance block: source `sources/hardware-2026-10-31/pololu/product-4754-specs.html`, its sha256, archive date 2026-10-31, caveat "published manufacturer values; not received-part measurements; not vendor CAD".
   - Dimension table with exactly what the archived page states (37D mm size class, published 16 mm shaft length, 6 mm shaft diameter, mass if stated). No values from vendor STEP files. Values not stated on the page are listed as "not stated on the archived page".
   - Historical context: the 7.8 mm motor-body gap failure and the 16-vs-22 mm shaft conflict are v13 vendor-CAD-derived findings, historical-only; this file is the non-CAD published baseline for planning caliper checks of the received motor.

3. Historical-status annotations

   - `docs/mechanical-readiness-v13.md` gains `## Historical status (2026-11-07)` directly under the title: the vendor-CAD variants and fit gates in this study derive from archived vendor STEP; vendor CAD is no longer used; treat all findings here as historical reference, not geometry authority; new geometry comes from owner measurements and open-source models.
   - `derived/cad-v13/README.md` (new): same marking for `fit-results.json`, `assembly-vendor-22mm.json`, both assembly identities, and the pinned archived STEP sources; states the verifier pins stay intact.

[Files]

New files:

- `docs/motor-dimensions-published.md` — manufacturer-page dimension distillation for the BOM drive motor; allowed evidence; new input for `cad-motor-gap-review`.
- `derived/cad-v13/README.md` — historical-only status for the v13 vendor-CAD-derived artifacts.

Deleted files:

- `prompts/vendor-cad-research.md` — the vendor-CAD hunting prompt.
- `derived/ai-orchestration/evidence/vendor-cad-research.md`
- `derived/ai-orchestration/evidence/vendor-cad-research.run.json` — dry-run artifacts of the removed task.

Modified files:

- `derived/ai-orchestration/tasks.json` — as in [Types] 1.
- `prompts/cad-fit-review.md` — reframe: goal becomes "plan caliper measurements of the received motor against the published dimensions to confirm or refute the historical 7.8 mm gap failure"; constraints add "vendor CAD is not used; the 7.8 mm figure is a historical vendor-CAD-derived finding, not current authority".
- `docs/mechanical-readiness-v13.md` — Historical status section per [Types] 3.
- `AGENTS.md` — new section `## Owner-set constraints (do not violate)` at the end, exact text:

  1. **No vendor CAD.** Do not search for, download, import, or build on vendor/manufacturer CAD files (STEP, SolidWorks, Fusion, etc.) for any new work. Archived vendor STEP/PDF files under `sources/` are committed history, kept only so the sealed v13 study stays verifiable; treat them as historical reference, never as geometry authority.
  2. **Open-source software only.** Robot geometry and design work uses this repository's open-source toolchain (CadQuery/OpenCASCADE and the existing conversion/rendering tools). No proprietary CAD applications.
  3. **Geometry authority is owner measurement.** Dimensions come from the owner's physical measurements of received parts, or from open-source models authored here. Manufacturer product pages, datasheets, and drawings may be read as evidence, but they are published claims, not received-part measurements.
  4. **AI harness tasks must not aim any provider at vendor CAD acquisition.** Reading manufacturer pages for published specs (as `vendor-page-read` does) is allowed; hunting CAD models is not.

- `CLAUDE.md` — add one pointer line: owner-set constraints (no vendor CAD; open-source software only) are listed in `AGENTS.md`.
- `SESSION-STATE-2026-11-07.md` — new section `## Owner constraint — no vendor CAD (2026-11-07)` recording the decision and this correction; update the harness-expansion section: the four-task list becomes three (`rules-update-scan`, `literature-search`, `vendor-page-read`), and note the `vendor-cad-research` removal, the `cad-motor-gap-review` re-point, and the 1067-to-4754 query fix.
- `docs/ai-orchestration.md` — `What this is not` gains "A way to research or adopt vendor CAD."; add a short task-authoring note: manufacturer pages/datasheets are allowed evidence; vendor CAD files are not; tasks must not aim any provider at vendor CAD acquisition.
- `PROJECT-STATUS.md` — add a `**November 7 review (agent-run):**` paragraph: owner constraint recorded; vendor-CAD findings marked historical-only; vendor-CAD research task removed; gap-review task re-pointed to manufacturer-page and bench evidence.
- `tests/ai-orchestration-provider.test.js` — as in [Functions].
- `implementation_plan.md` — replaced by this document.

Files not modified:

- `derived/ai-orchestration/registry.json` (no vendor references; providers unchanged).
- `tools/ai-orchestrate.js` (data-only change; no code change).
- Sealed harness evidence for the five chat tasks; `cad-motor-gap-review` is NOT re-run into the evidence directory — its committed live record stays sealed history, and the next owner-initiated live run produces a fresh record with the new inputs.
- `derived/cad-v13/fit-results.json`, `assembly-*.json`, `manifest.json`, archived `sources/**` (verifier pins; history).
- `BACKCAST-2026-11.md` (owner planning document); all pinned simulator files; `share/` showcases; `main` and the eight world branches.

[Functions]

No production functions change. Test functions only:

1. Modified: `real registry routes each task family to a live provider of that family` (`tests/ai-orchestration-provider.test.js`)
   - Delete the `assert.equal(pick('vendor-cad-research').id, 'exa-search');` line.
   - Keep: `cad-motor-gap-review` to `nvidia-robotics`, `rules-update-scan` to `exa-search`, `literature-search` to `openalex-search`, `vendor-page-read` to `jina-read`.

2. New: `no task targets vendor CAD research` (`tests/ai-orchestration-provider.test.js`)
   - Load `DEFAULT_MANIFEST`; assert no task `id`, `prompt_file`, or `output_name` contains `vendor-cad`.
   - Assert no task `input_files` entry lives under `derived/cad-v13/`.
   - Assert `prompts/` contains no file whose name or content mentions `vendor-cad`.
   - Assert `vendor-page-read.query` points at the BOM motor page (`product/4754`).

3. Automatically covering the new state: `default task manifest loads and references real files` (`tests/ai-orchestrate.test.js`) — `loadTaskManifest` validates that the re-pointed inputs exist on disk.

[Classes]

None. No class changes anywhere.

[Dependencies]

None.

- No new npm or pip packages; Node built-ins only.
- No live provider calls; no network in tests.
- No new external service required by `node tools/check-all.js`.

[Testing]

1. Existing tests stay green

   - `tests/ai-orchestrate.test.js` (11 tests) — file unchanged, must pass against the updated manifest.
   - `tests/ai-orchestration-provider.test.js` — 19 tests with one assertion removed, plus the new policy test (20 tests).

2. Validation gates

   - `node --check tools/ai-orchestrate.js` (unchanged file; sanity).
   - `node --test tests/ai-orchestrate.test.js tests/ai-orchestration-provider.test.js`.
   - `node tools/check-all.js` — all 43 steps must pass, including `verify-cad-v13` (annotating `docs/mechanical-readiness-v13.md` is safe because it is not in `manifest.json` `inputHashes`; `fit-results.json` is untouched).
   - Secrets scan on all changed files via `.claude/skills/secrets-guard/scripts/scan_secrets.py`.
   - Confirm `main` and the eight world branches are untouched (`git ls-remote --heads origin`).

3. Not re-run

   - `cad-motor-gap-review` is not re-run into `derived/ai-orchestration/evidence/`; test-suite dry-runs into temp directories already cover the wiring of the re-pointed inputs.

[Implementation Order]

1. Create `docs/motor-dimensions-published.md` from the archived `product-4754-specs.html` (page-published values only; provenance block with source sha256).
2. Update `derived/ai-orchestration/tasks.json`: remove `vendor-cad-research`; re-point `cad-motor-gap-review.input_files`; fix `vendor-page-read.query` to `product/4754`.
3. Delete `prompts/vendor-cad-research.md` and the two `vendor-cad-research` evidence files.
4. Rewrite `prompts/cad-fit-review.md` to the measurement-first framing.
5. Annotate `docs/mechanical-readiness-v13.md` with the Historical status section; create `derived/cad-v13/README.md`.
6. Write the rule into the durable memory files: `AGENTS.md` (new constraints section), `CLAUDE.md` (pointer line), `SESSION-STATE-2026-11-07.md` (decision record plus harness-expansion corrections), `docs/ai-orchestration.md`, `PROJECT-STATUS.md` (dated review paragraph).
7. Update `tests/ai-orchestration-provider.test.js` (remove the routing assertion; add the policy test).
8. Validate: `node --test` on both test files, full `node tools/check-all.js`, secrets scan on changed files, confirm branch state.
9. Commit and push on `ai-orchestration`.

**Do not begin implementation until the owner explicitly approves this plan.**
