# Implementation Plan

[Overview]

Add a two-stage, credential-safe AI-assisted finishing workflow to the existing robotics project: first build a local orchestration harness that routes narrowly scoped engineering tasks to the most suitable external AI providers, then use that harness to accelerate the project’s real next milestones—organizer Q&A preparation, mechanical fit review, firmware bring-up planning, and practice-field validation.

Scope and context:

- The repository is already a fully simulated, evidence-heavy robotics planning project with 43/43 gates on the eight-world branch model.
- No physical parts have been ordered, no practice field exists, and no organizer Q&A has been posted. The project’s current critical path is therefore physical bring-up, not more simulation.
- The best next phase is not “call every model on every task.” It is a role-specific routing harness that assigns each task to a small number of well-suited models, records provenance, and keeps the owner in control.
- The API credentials shown in this chat must be treated as compromised. Before implementation:
  1. Rotate every pasted key.
  2. Store new credentials only in private provider consoles or a local secrets file outside the repository.
  3. Do not copy keys into this plan, source files, logs, screenshots, or terminal transcripts.
- This plan proposes no embedded secrets, no new mandatory dependencies, and no changes to the eight already-published world branches or `main`.

[Types]

Use JSON-only data structures so the harness can be audited and diffed.

1. `ProviderSpec`

   ```json
   {
     "id": "nvidia-robotics",
     "role": ["robotics", "vision", "policy"],
     "endpoint": "https://integrate.api.nvidia.com/v1",
     "model_hint": "nvidia/gr00t-n1.5",
     "auth_env": "NVIDIA_API_KEY",
     "transport": "openai-compat",
     "max_tokens_hint": 4096,
     "notes": "Use for robot foundation-model reasoning and CAD/field visual review."
   }
   ```

   Required fields: `id`, `role`, `endpoint`, `auth_env`, `transport`, `model_hint`.
   `role` values: `code`, `review`, `vision`, `robotics`, `research`, `literature`, `planning`, `summarize`.

2. `TaskRequest`

   ```json
   {
     "id": "cad-motor-gap-review",
     "kind": "vision",
     "title": "Review the 7.8 mm motor-body gap failure",
     "input_files": [
       "docs/mechanical-readiness-v13.md",
       "derived/cad-v13/fit-results.json"
     ],
     "prompt_file": "prompts/cad-motor-gap.md",
     "preferred_providers": ["nvidia-robotics", "openrouter-general"],
     "output_name": "cad-motor-gap-review.md",
     "owner_review": false
   }
   ```

   Required fields: `id`, `kind`, `title`, `input_files`, `prompt_file`, `preferred_providers`, `output_name`.
   `kind` values: `code`, `review`, `vision`, `robotics`, `research`, `literature`, `planning`, `summarize`.

3. `RunRecord`

   ```json
   {
     "task_id": "cad-motor-gap-review",
     "provider_id": "nvidia-robotics",
     "model": "nvidia/gr00t-n1.5",
     "started_at": "2026-11-07T12:00:00.000Z",
     "finished_at": "2026-11-07T12:03:12.000Z",
     "status": "success",
     "prompt_sha256": "…",
     "response_sha256": "…",
     "input_files": [
       {
         "path": "docs/mechanical-readiness-v13.md",
         "sha256": "…"
       }
     ],
     "output_path": "derived/ai-orchestration/evidence/cad-motor-gap-review.md",
     "notes": "Agent-run; not owner-reviewed."
   }
   ```

   Required fields: `task_id`, `provider_id`, `model`, `started_at`, `finished_at`, `status`, `prompt_sha256`, `response_sha256`, `output_path`.
   The record must never contain API keys, request headers, or raw credential material.


[Files]

New files:

- `/workspace/roboticThingAvoidance/tools/ai-orchestrate.js`
  - Node 24 CLI using only built-in `fs`, `path`, `crypto`, and global `fetch`.
  - Loads a provider registry, task manifest, and prompt files.
  - Selects a provider, runs one task, and writes an auditable evidence record.
  - Supports `--dry-run`, `--task`, `--provider`, `--manifest`, `--registry`, and `--help`.

- `/workspace/roboticThingAvoidance/docs/ai-orchestration.md`
  - Owner-facing usage guide.
  - Explains provider routing, role assignments, evidence logging, credential handling, and the fact that every output is advisory until owner-reviewed.

- `/workspace/roboticThingAvoidance/prompts/`
  - Reusable prompt templates:
    - `organizer-qa-draft.md`
    - `cad-fit-review.md`
    - `firmware-bringup-checklist.md`
    - `practice-field-plan.md`
    - `rules-interpretation.md`

- `/workspace/roboticThingAvoidance/derived/ai-orchestration/registry.json`
  - Provider registry. Contains environment-variable names only, never secrets.

- `/workspace/roboticThingAvoidance/derived/ai-orchestration/tasks.json`
  - Initial task manifest for the next physical phase.

- `/workspace/roboticThingAvoidance/derived/ai-orchestration/evidence/README.md`
  - States that evidence files are AI-generated advisory artifacts and require owner review before being treated as engineering results.

- `/workspace/roboticThingAvoidance/tests/ai-orchestrate.test.js`
  - Unit tests for registry parsing, task routing, dry-run output, evidence hashing, and secret-free behavior.

Modified files:

- `/workspace/roboticThingAvoidance/package.json`
  - Add `"ai:orchestrate": "node tools/ai-orchestrate.js"` to `scripts`.
  - Do not add runtime dependencies.

- `/workspace/roboticThingAvoidance/README.md`
  - Add a short “AI orchestration” section linking to `docs/ai-orchestration.md`.
  - State that AI-generated advisories are labeled and are not owner-validated work.

- `/workspace/roboticThingAvoidance/SESSION-STATE-2026-11-07.md`
  - Add the next-phase scope: credential rotation, orchestration harness, then AI-assisted physical bring-up.
  - Record that the pasted keys are compromised and must be rotated.

Files not to modify:

- `software/stockcar/mission.py`
- `software/stockcar/routes.py`
- `software/stockcar/field.py`
- `software/stockcar/obstacles.py`
- `software/stockcar/supervisor.py`
- `software/stockcar/lapmodel.py`
- `software/stockcar/passage.py`
- `software/stockcar/geometry.py`
- `software/stockcar/sensors.py`
- `software/stockcar/sensors_camera.py`
- `software/stockcar/estimator.py`
- `derived/organizer-cad-v10/field-v10.json`
- Existing eight-world branch seal artifacts.
- `main`

[Functions]

New functions in `tools/ai-orchestrate.js`:

1. `parseArgs(argv)`
   - Signature: `parseArgs(argv) -> object`
   - Parses `--task`, `--provider`, `--registry`, `--manifest`, `--dry-run`, and `--help`.
   - Fails fast with a readable usage message.

2. `loadProviderRegistry(path)`
   - Signature: `loadProviderRegistry(path) -> ProviderSpec[]`
   - Reads `registry.json`.
   - Validates required fields and unique provider IDs.
   - Rejects any file containing literal credential prefixes such as `sk-or-v1-`, `tgp_v1_`, `nvapi-`, or `jina_`.

3. `loadTaskManifest(path)`
   - Signature: `loadTaskManifest(path) -> TaskRequest[]`
   - Reads `tasks.json`.
   - Validates that every referenced input and prompt file exists.
   - Rejects duplicate task IDs.

4. `selectProvider(task, providers)`
   - Signature: `selectProvider(task, providers) -> ProviderSpec`
   - Prefers an intersection of `task.preferred_providers` and provider `role`.
   - Falls back to the first provider matching `task.kind`.
   - Returns a deterministic selection for reproducible dry-runs.

5. `buildPrompt(task, provider)`
   - Signature: `buildPrompt(task, provider) -> string`
   - Loads `task.prompt_file`.
   - Appends labeled input file paths and hashes.
   - Includes an explicit instruction: “Do not claim owner review or physical validation.”

6. `hashText(text)`
   - Signature: `hashText(text) -> string`
   - SHA-256 helper for prompts and responses.

7. `runTask(task, provider, options)`
   - Signature: `async runTask(task, provider, options) -> RunRecord`
   - In `--dry-run`, writes a deterministic stub response without network access.
   - In live mode, calls the provider endpoint using `fetch`.
   - Writes the response to `derived/ai-orchestration/evidence/<task.output_name>`.
   - Writes `RunRecord` metadata beside it.

8. `writeRunRecord(record)`
   - Signature: `writeRunRecord(record) -> void`
   - Serializes the run record as JSON.
   - Never writes API keys, headers, or request bodies containing credentials.

9. `printSummary(records)`
   - Signature: `printSummary(records) -> void`
   - Prints task, provider, status, output path, and advisory status.

Removed functions: none.
Modified functions: none in existing files.


[Classes]

No new classes are required. The harness should remain procedural, matching the existing `tools/*.js` style.

If a future refactor needs an abstraction, introduce:

- `class AIOrchestrator`
  - Constructor: `constructor({registry, manifest, options})`
  - Methods:
    - `async run(taskId)`
    - `selectProvider(task)`
    - `writeEvidence(record)`
    - `summary()`

- `class ProviderAdapter`
  - Methods:
    - `async send(prompt, providerSpec)`
    - `name`
  - Subclasses:
    - `OpenAICompatAdapter`
    - `DryRunAdapter`

This class layer is optional and should only be added if `tools/ai-orchestrate.js` grows beyond one file.

[Dependencies]

No new runtime dependencies.

Use only:

- Node 24 built-ins
- Global `fetch`
- Existing repository test harness (`node --test`)
- Existing Python/uv tools if a helper script is needed later

External integration requirements:

1. Provider credentials
   - Read only from environment variables named in `registry.json`, such as:
     - `OPENROUTER_API_KEY`
     - `NVIDIA_API_KEY`
     - `TOGETHER_API_KEY`
     - `FIREWORKS_API_KEY`
     - `DEEPINFRA_API_KEY`
     - `NOVITA_API_KEY`
     - `BASTEN_API_KEY`
     - `MOONSHOT_API_KEY`
     - `SILICONFLOW_API_KEY`
     - `ATLAS_CLOUD_API_KEY`
     - `PARASAIL_API_KEY`
     - `LLMTR_API_KEY`
     - `INCEPTION_API_KEY`
   - Never write the values to disk in this repository.

2. Recommended provider roles

   - Robotics / vision / control
     - NVIDIA NIM-style endpoints for robotics and VLM models, including candidate families such as:
       - GR00T N1.5 / Isaac-style robot foundation models
       - VILA-style vision-language models
       - Cosmos-style world-model or simulation reasoning, if exposed
     - Use for CAD fit review, field-image reasoning, mechanism sanity checks, and robot-policy discussion.

   - General reasoning and code review
     - OpenRouter, Together, Fireworks, Novita, DeepInfra, Baseten, Moonshot, SiliconFlow, Atlas Cloud, Parasail, LLMtr, Inception
     - Use for:
       - rules interpretation
       - test-plan drafting
       - firmware bring-up checklists
       - documentation summaries
       - code review of non-pinned files

   - Web research
     - Exa, Brave, Jina, Firecrawl
     - Use for:
       - organizer manual updates
       - part availability
       - competition deadline checks
       - rules-history research

   - Literature and evidence
     - OpenAlex, Semantic Scholar, Core, ORCID
     - Use only if a specific engineering question needs a cited source.

3. Credential policy
   - Rotate every key pasted in this conversation before any live call.
   - Store new credentials in provider consoles or `~/.config/ai-keys.env` with mode `600`.
   - Never paste them into the repository, prompts, or generated artifacts.
   - `secrets-guard` must scan:
     - `registry.json`
     - `tasks.json`
     - prompt files
     - evidence outputs
     - tests


[Testing]

1. Unit tests (`tests/ai-orchestrate.test.js`)

   - `parseArgs` accepts documented flags and rejects unknown flags.
   - `loadProviderRegistry` validates required fields and rejects duplicate IDs.
   - `loadTaskManifest` rejects missing prompt/input files.
   - `selectProvider` prefers an explicit provider, then role match, then deterministic fallback.
   - `buildPrompt` includes the advisory label and input hashes.
   - `runTask --dry-run` creates evidence and a run record without network access.
   - `writeRunRecord` never includes credential-like strings.
   - Generated evidence files are deterministic in dry-run mode.

2. Secret-safety tests

   Add a test that scans all new AI-orchestration files for common credential prefixes:

   - `sk-or-v1-`
   - `tgp_v1_`
   - `nvapi-`
   - `jina_`
   - `fw_`
   - `psk-`
   - `nck_live_`
   - `fc-`
   - `omtx_`
   - `jf_live_`

   The test must fail if any literal credential appears.

3. Integration tests

   - No live provider calls in the default test suite.
   - Optional integration tests are gated behind an explicit environment variable, for example:
     - `AI_ORCHESTRATION_LIVE=1`
   - Even in live mode, tests must use one low-cost provider and one prompt.
   - Integration tests must be disabled unless the owner explicitly enables them.

4. Repository gate

   - Add `tests/ai-orchestrate.test.js` to the existing Node test discovery pattern.
   - Do not add external network calls to `node tools/check-all.js` by default.
   - Optional full mode may later include:
     - `node --test tests/ai-orchestrate.test.js`
   - `secrets-guard --worktree` must pass before any commit or push.

[Implementation Order]

1. Credential hygiene first
   - Rotate every key pasted in this conversation.
   - Store new credentials outside the repository.
   - Confirm `.gitignore` covers local secret files.
   - Do not proceed with live provider calls until this is done.

2. Design the provider registry
   - Create `derived/ai-orchestration/registry.json`.
   - Include only environment-variable names, not values.
   - Populate with the recommended role mapping above.

3. Create task manifest and prompts
   - Create `derived/ai-orchestration/tasks.json`.
   - Add the first five high-value tasks:
     1. Organizer Q&A draft from `derived/qa-pack-v10/QUESTIONS.md`.
     2. Mechanical fit review of the 7.8 mm motor-body gap failure.
     3. Firmware bring-up checklist for the Pico 2 stack.
     4. Practice-field build and measurement plan.
     5. Rules-interpretation cross-check of V3.0/V3.1 open questions.
   - Add one prompt file per task under `prompts/`.

4. Implement `tools/ai-orchestrate.js`
   - Start with dry-run mode only.
   - Add registry loading, task loading, provider selection, prompt building, evidence writing, and summary printing.
   - Keep the CLI small and auditable.

5. Add provider adapters
   - Implement `OpenAICompatAdapter` for providers that expose OpenAI-compatible endpoints.
   - Add a `DryRunAdapter` for tests.
   - Add provider-specific adapters only when necessary.
   - Never log request headers or credentials.

6. Add tests
   - Create `tests/ai-orchestrate.test.js`.
   - Cover parsing, routing, dry-run execution, hashing, and secret scanning.
   - Ensure `node --test` passes.

7. Update documentation
   - Add `docs/ai-orchestration.md`.
   - Update `README.md` with a short AI-assisted finishing workflow section.
   - Update `SESSION-STATE-2026-11-07.md` with the new phase and credential-rotation requirement.

8. Validate
   - Run:
     - `node --test tests/ai-orchestrate.test.js`
     - `node tools/check-all.js`
     - `secrets-guard --worktree`
   - Confirm no existing branch tip changes.

9. Use the harness for the next physical milestone
   - Run the first five tasks in dry-run mode.
   - Review outputs manually.
   - Use the best outputs to prepare:
     - organizer Q&A submission drafts
     - mechanical fit-risk register
     - firmware bring-up checklist
     - practice-field build plan
   - Do not treat any AI-generated output as owner-reviewed engineering evidence until the owner explicitly marks it reviewed.

10. Proceed to hardware bring-up
    - Once the harness and first advisory outputs are accepted, the project’s next real milestone is physical:
      - post organizer Q&A
      - order parts
      - build the practice field
      - assemble the mule
      - run bench characterization
      - begin firmware bring-up
    - The AI orchestration harness should support those steps, not replace owner review or physical testing.

**Do not begin implementation until the owner explicitly approves this plan.**
