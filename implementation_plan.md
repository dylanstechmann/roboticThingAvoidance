# Implementation Plan

[Overview]

Extend the existing `ai-orchestration` harness so it can route advisory work across every provider family available in the owner’s private key store, while keeping costs and context size under control.

Scope and context:

- The harness currently supports only OpenAI-compatible chat/review providers and manual provider selection. It works, but it does not yet use the research/search/scholarship keys, it has no cost-aware routing, and it has no owner-review workflow.
- This plan adds three capabilities:
  1. **Provider-family expansion** — every key family currently present in `~/.config/ai-keys.env` gets a registry entry. Families with vendored endpoint knowledge become live; families that still need endpoint confirmation are listed as `planned` so they are visible but not automatically selected.
  2. **Cost-aware task routing** — providers gain a `cost_rank` and family tags. Automatic provider selection prefers the cheapest suitable provider for the task’s `kind`, so expensive models are not used when a cheaper one will do.
  3. **Automatic context compaction** — when the assembled prompt exceeds a configurable token budget, the harness first summarizes the inputs into a digest using a cheap summarize provider, then runs the real task against the digest instead of the full raw files. This keeps long evidence chains from blowing up context windows or cost.
- This plan also adds a lightweight **owner-review workflow**: each generated evidence file can be marked `accepted` or `rejected` with notes, recorded in a sidecar JSON file and mirrored into the run record.
- No new runtime dependencies are introduced. The implementation uses Node’s built-in `fetch`, `fs`, `path`, and `crypto` only. The existing Python MCP tools in `.agent-tools/mcp/` are not modified; their endpoint conventions are ported into the Node CLI.

Constraints carried over from the repository:

- All outputs remain **advisory** and are not owner-reviewed engineering evidence until explicitly marked.
- No API keys or credential-like strings are committed. The harness reads keys only from the environment or `~/.config/ai-keys.env`.
- No changes are made to `main` or to the eight published world branches.
- The pinned simulator and CAD files remain untouched.

[Types]

All data structures remain JSON-only so they can be audited and diffed.

1. `ProviderSpec` — extended

   Every provider registry entry gains three new fields: `family`, `cost_rank`, and `max_context_tokens`. Existing fields are unchanged.

   ```json
   {
     "id": "moonshot-kimi",
     "family": "chat",
     "role": ["summarize", "review"],
     "endpoint": "https://api.moonshot.ai/v1/chat/completions",
     "auth_env": "MOONSHOT_API_KEY",
     "transport": "openai-chat",
     "model_hint": "moonshot-v1-128k",
     "cost_rank": 2,
     "max_context_tokens": 120000,
     "notes": "Long-context summarization and review."
   }
   ```

   Field rules:

   - `id`: lowercase, hyphenated, unique.
   - `family`: one of `chat`, `web-search`, `web-read`, `scholar`, `runtime`, `planned`.
   - `role`: array; values include `chat`, `summarize`, `review`, `research`, `search`, `literature`, `vision`, `code`, `planning`, `runtime`.
   - `endpoint`: `http(s)` URL, or `null` when `transport` is `planned`.
   - `auth_env`: environment-variable name only, never a value.
   - `transport`: one of `openai-chat`, `http-json`, `web-search`, `web-read`, `scholar-search`, `runtime`, `planned`.
   - `model_hint`: string or `null` for search/scholar providers.
   - `cost_rank`: integer `1`–`5`; ordinal only, not a price. `1` means cheapest known, `5` means most expensive.
   - `max_context_tokens`: advisory integer used by compaction and routing.
   - `notes`: short human-readable guidance.


   Provider families to add:

   - **Chat / review** — already present: `nvidia-robotics`, `openrouter-general`, `together-general`, `fireworks-general`, `deepinfra-general`, `novita-general`, `baseten-text`, `moonshot-kimi`, `siliconflow-general`, `atlas-general`, `parasail-general`, `llmtr-general`.
   - **Additional chat** — add `inception-lab` using `INCEPTION_API_KEY`; confirm endpoint/model before marking it live.
   - **Web search** — add `exa-search` (`EXA_API_KEY`), `brave-search` (`BRAVE_SEARCH_API_KEY`), `brave-answers` (`BRAVE_ANSWERS_API_KEY`), `jina-search` (`JINA_API_KEY`), `firecrawl-search` (`FIRECRAWL_API_KEY`).
   - **Web read** — add `jina-read` (`JINA_API_KEY`), `firecrawl-scrape` (`FIRECRAWL_API_KEY`).
   - **Scholar** — add `openalex-search` (`OPENALEX_API_KEY`), `semantic-scholar-search` (`SEMANTIC_SCHOLAR_API_KEY`), `core-search` (`CORE_API_KEY`), `pubmed-search` (`NCBI_API_KEY`), `orcid-record` (`ORCID_CLIENT_ID`/`ORCID_CLIENT_SECRET`).
   - **Runtime** — register `modal-runtime` using `MODAL_TOKEN_ID`/`MODAL_TOKEN_SECRET` as `transport: planned` until the execution API is confirmed. It is visible in the registry but not automatically selected.
   - Any other key families found in the private store are added with `transport: planned` rather than invented endpoints.

2. `TaskSpec` — extended

   ```json
   {
     "id": "rules-update-scan",
     "kind": "search",
     "title": "Scan public sources for rule or field updates",
     "input_files": [
       "RULES-AND-SOURCES.md"
     ],
     "prompt_file": "prompts/rules-update-scan.md",
     "preferred_providers": [
       "exa-search",
       "brave-search",
       "jina-search"
     ],
     "output_name": "rules-update-scan.md",
     "context_policy": {
       "mode": "auto",
       "budget_tokens": 12000
     },
     "review": false
   }
   ```

   Field rules:

   - `id`: lowercase, hyphenated, unique.
   - `kind`: one of `chat`, `summarize`, `review`, `research`, `search`, `literature`, `vision`, `code`, `planning`, `runtime`.
   - `input_files`: non-empty array of repository-relative paths.
   - `prompt_file`: repository-relative path to a template under `prompts/`.
   - `preferred_providers`: ordered array of provider ids used as a preference filter before cost ranking.
   - `output_name`: filename written under `derived/ai-orchestration/evidence/`.
   - `context_policy`: optional object with:
     - `mode`: `auto` (default) or `off`.
     - `budget_tokens`: integer; if omitted, the CLI `--context-budget` value is used.
   - `review`: optional boolean; `true` marks the task as requiring explicit owner review before its output is used elsewhere.


3. `RunRecord` — extended

   ```json
   {
     "task_id": "cad-motor-gap-review",
     "provider_id": "nvidia-robotics",
     "provider_family": "chat",
     "cost_rank": 3,
     "model": "nvidia/nemotron-3-nano-omni-30b-a3b-reasoning",
     "started_at": "2026-11-07T12:00:00.000Z",
     "finished_at": "2026-11-07T12:01:12.000Z",
     "status": "success",
     "prompt_sha256": "…",
     "response_sha256": "…",
     "input_files": [
       {
         "path": "docs/mechanical-readiness-v13.md",
         "sha256": "…",
         "chars": 1234,
         "tokens_estimated": 309,
         "compacted": true
       }
     ],
     "compaction": {
       "applied": true,
       "digest_file": "derived/ai-orchestration/context/cad-motor-gap-review.digest.md",
       "digest_sha256": "…",
       "compaction_provider_id": "moonshot-kimi",
       "reason": "prompt exceeded context budget"
     },
     "output_path": "derived/ai-orchestration/evidence/cad-motor-gap-review.md",
     "review": {
       "status": "pending",
       "reviewed_at": null,
       "reviewer": null,
       "notes": null
     },
     "notes": "Agent-run; not owner-reviewed."
   }
   ```

4. `ReviewRecord` — new sidecar

   Stored as `<task-id>.review.json` beside the evidence output:

   ```json
   {
     "task_id": "cad-motor-gap-review",
     "output_path": "derived/ai-orchestration/evidence/cad-motor-gap-review.md",
     "status": "accepted",
     "reviewer": "owner",
     "reviewed_at": "2026-11-07T12:05:00.000Z",
     "notes": "Accepted for planning only; fabrication decision still requires bench measurement.",
     "run_sha256": "…",
     "output_sha256": "…"
   }
   ```

   `status` is one of `accepted`, `rejected`, `pending`.

5. `ContextPolicy`

   ```json
   {
     "mode": "auto",
     "budget_tokens": 12000
   }
   ```

   - `auto` means compaction runs whenever the estimated prompt size exceeds `budget_tokens`.
   - `off` disables compaction for that task.

[Files]

New files:

- `prompts/context-compaction.md` — instructions used when summarizing large inputs into a digest.
- `prompts/rules-update-scan.md` — web-search prompt for rule or field updates.
- `prompts/vendor-cad-research.md` — web-search/read prompt for vendor CAD and part references.
- `prompts/literature-search.md` — scholar-search prompt for academic or standards references.
- `prompts/web-page-read.md` — page-read prompt used with `jina-read` / `firecrawl-scrape`.
- `derived/ai-orchestration/context/` — directory holding generated digests. Each digest is named `<task-id>.digest.md`.
- `tests/ai-orchestration-provider.test.js` — tests for the expanded registry, cost ranking, compaction, and review workflow.
- `derived/ai-orchestration/evidence/<task-id>.review.json` — per-task review sidecars (generated at review time).


Modified files:

- `tools/ai-orchestrate.js`
  - Add token estimation and automatic compaction.
  - Add cost-aware provider selection.
  - Add provider-family dispatch beyond OpenAI-compatible chat.
  - Add the review subcommand and sidecar writing.
  - Extend `parseArgs` with the new flags.
- `derived/ai-orchestration/registry.json`
  - Add `family`, `cost_rank`, and `max_context_tokens` to every provider.
  - Add the new provider families listed above.
- `derived/ai-orchestration/tasks.json`
  - Add `context_policy` where useful.
  - Add new tasks that exercise search, scholar, and compaction routes.
- `prompts/organizer-qa-draft.md`, `prompts/cad-fit-review.md`, `prompts/firmware-bringup-checklist.md`, `prompts/practice-field-plan.md`, `prompts/rules-interpretation.md`
  - No structural change required; they remain advisory.
- `docs/ai-orchestration.md`
  - Document provider families, cost ranking, automatic compaction, and the review workflow.
- `README.md`
  - Update the one-paragraph AI-assisted workflow summary.
- `SESSION-STATE-2026-11-07.md`
  - Add a short note recording the expanded harness scope.
- `implementation_plan.md`
  - Replaced by this document.

Files not modified:

- `.agent-tools/mcp/web_mcp.py`
- `.agent-tools/mcp/scholar_mcp.py`
- `.agent-tools/mcp/agentkeys.py`
- Any pinned simulator or CAD file.
- Any of the eight published world branches.
- `main`.

[Functions]

New functions in `tools/ai-orchestrate.js`:

1. `estimateTokens(text) -> number`
   - Approximate token count from character length (`Math.ceil(text.length / 4)`).
   - Used only as a budget heuristic; no tokenizer dependency is added.

2. `needsCompaction(prompt, budgetTokens) -> boolean`
   - Returns `true` when `estimateTokens(prompt) > budgetTokens`.

3. `compactInputs(task, provider, options) -> { digest, digestPath, digestSha256, applied }`
   - Reads the task’s input files.
   - Builds a compaction prompt using `prompts/context-compaction.md`.
   - Calls the cheapest available `summarize` provider (or a deterministic local digest in dry-run).
   - Writes the digest to `derived/ai-orchestration/context/<task-id>.digest.md`.
   - Returns the digest path and hash so the run record can reference it.

4. `callWebSearch(provider, query, options) -> string`
   - Implements the `web-search` transport using the provider’s endpoint and auth header.
   - Returns markdown-formatted results.
   - The endpoint conventions mirror those already used by `.agent-tools/mcp/web_mcp.py`.

5. `callWebRead(provider, url, options) -> string`
   - Implements the `web-read` transport for `jina-read` and `firecrawl-scrape`.
   - Returns markdown text clipped to the configured limit.

6. `callScholarSearch(provider, query, options) -> string`
   - Implements the `scholar-search` transport for OpenAlex, Semantic Scholar, CORE, PubMed, and ORCID.
   - Returns a structured markdown list with identifiers and links.
   - The endpoint conventions mirror `.agent-tools/mcp/scholar_mcp.py`.


7. `callRuntime(provider, task, options) -> string`
   - Placeholder for the `runtime` transport.
   - Initially returns a clear “not implemented” message.
   - Exists so future Modal/container work can be added without changing the dispatcher.

8. `dispatchProvider(provider, task, options) -> string`
   - Chooses the correct adapter based on `provider.transport`.
   - Supported transports: `openai-chat`, `web-search`, `web-read`, `scholar-search`.
   - `planned` and `runtime` raise a clear error instead of silently calling a wrong endpoint.

9. `writeReviewRecord(task, runRecord, review) -> void`
   - Writes `derived/ai-orchestration/evidence/<task-id>.review.json`.
   - Updates the matching run record’s `review` field.

Modified functions:

1. `validateProvider(provider)`
   - Require `family`, `cost_rank`, and `max_context_tokens`.
   - Validate `cost_rank` is an integer between `1` and `5`.
   - Validate `transport` is one of the supported values.
   - Allow `endpoint: null` only when `transport` is `planned`.

2. `validateTask(task)`
   - Accept optional `context_policy` and `review` fields.
   - Validate `context_policy.mode` is `auto` or `off`.
   - Validate `context_policy.budget_tokens` is a positive integer when present.

3. `selectProvider(task, providers)`
   - Keep the existing preferred-provider filter.
   - Sort matching providers by `cost_rank` ascending.
   - If two providers share a `cost_rank`, preserve the original registry order.
   - Prefer a provider whose `family` matches the task `kind` when both exist.

4. `buildPrompt(task, provider, options)`
   - Accept an optional `compaction` object.
   - When compaction is applied, include the digest and the original file hashes, but not the full file contents.
   - When compaction is not applied, keep the current full-content behavior.

5. `runTask(task, provider, options)`
   - Estimate the prompt size before calling the provider.
   - When the budget is exceeded and `context_policy.mode` is `auto`, run compaction first.
   - Record compaction metadata in the run record.
   - Record `provider_family` and `cost_rank` in the run record.
   - Initialize `review.status` to `pending`.
   - On live search/scholar providers, use the new dispatch functions instead of the chat adapter.

6. `parseArgs(argv)`
   - Add `--context-budget <n>` (default `12000`).
   - Add `--no-compact` to disable compaction for a single run.
   - Add `--review` with `--task <id>`, `--status accepted|rejected`, and `--notes "…"`.
   - Allow `--review` without `--dry-run` or `--live`.

7. `printSummary(records)`
   - Show `provider_family`, `cost_rank`, and compaction status in the one-line summary.
   - Show `review: accepted|rejected|pending`.

8. `main()`
   - Handle the `--review` subcommand before provider execution.
   - Otherwise keep the existing dry-run/live behavior.

9. `loadProviderRegistry(file)` / `loadTaskManifest(file)`
   - Validate the new fields described above.

Removed functions:

- None. No existing function is deleted.

[Classes]

No new public classes are required. The harness stays function-based, matching the existing style.

Internal adapter classes (implementation detail only):

1. `ProviderAdapter` — new, `tools/ai-orchestrate.js`
   - Methods: `constructor(provider)`, `supports(task)`, `run(task, options)`.
   - Base class for the transport dispatchers.

2. `OpenAIChatAdapter extends ProviderAdapter`
   - Wraps the existing OpenAI-compatible chat path.

3. `WebSearchAdapter extends ProviderAdapter`
   - Wraps `callWebSearch`.

4. `WebReadAdapter extends ProviderAdapter`
   - Wraps `callWebRead`.

5. `ScholarSearchAdapter extends ProviderAdapter`
   - Wraps `callScholarSearch`.

6. `RuntimeAdapter extends ProviderAdapter`
   - Placeholder for future container/runtime providers.
   - Initially returns a clear “planned, not live” message.

7. `CompactionAdapter`
   - Wraps `compactInputs`.
   - Selects the cheapest available `summarize` provider.

8. `ReviewStore`
   - Wraps `writeReviewRecord`.
   - Reads and writes the sidecar JSON.
   - Mirrors review state into the run record.

These classes are private to `tools/ai-orchestrate.js` and are not exported unless a later refactor splits the file.


[Dependencies]

No new npm or pip dependencies are introduced.

- Node built-ins used: `fs`, `path`, `crypto`, `os`, `fetch`.
- The vendored Python MCP tools remain unchanged.
- No tokenizer package is added; token counting is approximate.
- No new external service is required by `node tools/check-all.js`.

If a provider family later requires a real SDK, it is added as an explicit follow-up task, not silently in this change.

[Testing]

1. Existing tests stay green

   - `tests/ai-orchestrate.test.js` continues to pass.
   - No existing test is deleted.

2. New unit tests in `tests/ai-orchestration-provider.test.js`

   - Registry validation
     - Every provider has `family`, `cost_rank`, and `max_context_tokens`.
     - `cost_rank` is an integer between `1` and `5`.
     - `transport` is recognized.
     - `planned` providers may have `endpoint: null`.
     - Provider ids remain unique.

   - Cost-aware routing
     - Given two providers with the same role, the lower `cost_rank` is selected.
     - Preferred-provider order still wins over raw registry order when both match the task kind.
     - A provider with a mismatched family is not selected for a task that requires a specific family.

   - Context compaction
     - A short prompt does not trigger compaction.
     - A prompt over the configured budget triggers compaction.
     - The digest file is written under `derived/ai-orchestration/context/`.
     - The run record records `compaction.applied`, `digest_file`, and `digest_sha256`.
     - `--no-compact` disables compaction even when the budget is exceeded.
     - Dry-run mode produces a deterministic digest without network access.

   - Review workflow
     - `--review --task <id> --status accepted --notes "…"` writes `<task-id>.review.json`.
     - The run record’s `review.status` becomes `accepted`.
     - `--status rejected` writes `rejected`.
     - Missing `--status` fails with a clear error.
     - Reviewing an unknown task fails with a clear error.

   - Provider dispatch
     - `web-search` tasks route to `callWebSearch`.
     - `scholar-search` tasks route to `callScholarSearch`.
     - `planned` transports fail with a clear “not implemented” message.
     - No live network call is made by default; tests stub `fetch`.

3. Integration strategy

   - Default `npm test` and `node tools/check-all.js` make **no** external network calls.
   - Live provider smoke tests remain opt-in:
     - one chat provider,
     - one search provider,
     - one scholar provider.
   - Live tests are not part of `check-all`.

4. Validation gates

   - `node --check tools/ai-orchestrate.js`
   - `node --test tests/ai-orchestrate.test.js tests/ai-orchestration-provider.test.js`
   - `node tools/check-all.js`
   - `python .claude/skills/secrets-guard/scripts/scan_secrets.py <changed-files>`


[Implementation Order]

1. Extend the provider registry schema
   - Add `family`, `cost_rank`, and `max_context_tokens` to every existing provider.
   - Add the new chat, web-search, web-read, scholar, and planned runtime providers.
   - Keep endpoint values only where the API is already known; mark the rest `planned`.

2. Extend the task manifest and prompts
   - Add `context_policy` to tasks that can grow large.
   - Add the new search/scholar/compaction prompt templates.
   - Add at least one task per new provider family so each route is exercised.

3. Implement token estimation and automatic compaction
   - Add `estimateTokens`, `needsCompaction`, and `compactInputs`.
   - Wire compaction into `buildPrompt` and `runTask`.
   - Write digests under `derived/ai-orchestration/context/`.
   - Record compaction metadata in the run record.

4. Implement cost-aware provider selection
   - Sort matching providers by `cost_rank`.
   - Keep preferred-provider ordering as a first-stage filter.
   - Prefer family-specific providers for search and scholar tasks.

5. Implement the provider dispatch layer
   - Add `callWebSearch`, `callWebRead`, and `callScholarSearch`.
   - Add the `dispatchProvider` function.
   - Add the `RuntimeAdapter` placeholder.
   - Keep `planned` transports out of automatic selection.

6. Implement the review workflow
   - Add `writeReviewRecord` and the `ReviewStore` helper.
   - Add the `--review` CLI mode.
   - Write sidecar JSON files beside each evidence output.
   - Mirror review status into the run record.

7. Update the CLI surface
   - Add `--context-budget`, `--no-compact`, and `--review`.
   - Keep `--dry-run` and `--live` behavior unchanged for existing tasks.
   - Update `--help` text.

8. Update documentation
   - `docs/ai-orchestration.md`: provider families, cost ranking, compaction, review workflow.
   - `README.md`: one short updated paragraph.
   - `SESSION-STATE-2026-11-07.md`: note the expanded scope.

9. Extend the tests
   - Add `tests/ai-orchestration-provider.test.js`.
   - Cover registry validation, cost ranking, compaction, review, and dispatch.
   - Keep all tests offline by stubbing `fetch`.

10. Validate
   - `node --check tools/ai-orchestrate.js`
   - `node --test tests/ai-orchestrate.test.js tests/ai-orchestration-provider.test.js`
   - `node tools/check-all.js`
   - Secrets scan on every changed file.
   - Confirm the eight world branches and `main` are untouched.

11. Optional follow-up (not part of this change)
   - Enable live search and scholar smoke tests.
   - Add a Modal runtime adapter if container execution becomes useful.
   - Split `tools/ai-orchestrate.js` into `tools/ai-orchestration/` modules once the file exceeds a comfortable size.

**Do not begin implementation until the owner explicitly approves this plan.**
