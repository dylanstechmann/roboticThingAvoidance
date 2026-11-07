# AI orchestration

This folder contains a local orchestration harness for routing narrowly scoped engineering tasks to external AI providers and recording advisory evidence.

Everything generated here is agent-run and advisory. It is not owner-reviewed engineering evidence unless explicitly marked otherwise.

## What this is

- A small Node 24 CLI: `tools/ai-orchestrate.js`.
- A provider registry with environment-variable names only, covering every key family in the owner's private key store.
- A task manifest and reusable prompt templates.
- A dry-run mode (default, offline) and an optional live mode.
- Cost-aware routing, automatic context compaction, and an owner-review workflow.
- An evidence directory with hashes and run records.

## What this is not

- A replacement for owner review.
- A substitute for physical testing.
- A way to store API credentials.
- A claim that any AI output is validated engineering work.
- A way to research or adopt vendor CAD.

## Provider families

| Family | Providers | Transport | Live? |
|---|---|---|---|
| chat | nvidia-robotics, openrouter-general, together-general, fireworks-general, deepinfra-general, novita-general, baseten-text, moonshot-kimi, siliconflow-general, atlas-general, parasail-general, llmtr-general | openai-compat | yes (confirm models marked placeholder before live use) |
| chat (planned) | inception-lab, omtx-general, japanfold-general | planned | no — endpoints unconfirmed |
| web-search | exa-search, brave-search, brave-answers, jina-search, firecrawl-search | web-search | yes |
| web-read | jina-read, firecrawl-scrape | web-read | yes |
| scholar | openalex-search, semantic-scholar-search, core-search, pubmed-search, orcid-record | scholar-search | yes |
| runtime | modal-runtime | planned | no — execution API unconfirmed |

Every provider entry carries:

- `family` — one of the families above;
- `cost_rank` — an ordinal from 1 (cheapest known) to 5 (most expensive). It is a routing preference, not a price;
- `max_context_tokens` — advisory window used by compaction and routing;
- `auth_env` — the environment-variable name that holds the key, never the value.

Automatic selection picks the cheapest live provider whose family matches the task kind. `planned` transports are registered so the key families stay visible, but they are never auto-selected and fail with a clear message if requested live.

## Task-authoring rules

- Manufacturer product pages, datasheets, and drawings are allowed evidence.
- Vendor CAD files are not: no task may search for, download, import, or build on vendor CAD.
- Geometry authority is the owner's physical measurement of received parts, or open-source models authored in this repository.

## Usage

Dry-run a task (offline, deterministic):

```sh
node tools/ai-orchestrate.js \
  --task cad-motor-gap-review \
  --provider nvidia-robotics \
  --dry-run
```

Live mode automatically loads keys from `~/.config/ai-keys.env` if that file exists. You do not have to export keys manually.

```sh
node tools/ai-orchestrate.js \
  --task cad-motor-gap-review \
  --provider nvidia-robotics \
  --live
```

Search, page-read, and scholar tasks work the same way; the harness sends the task's recorded `query` to the provider and stores the formatted results as evidence. For example:

```sh
node tools/ai-orchestrate.js --task literature-search --provider openalex-search --live
node tools/ai-orchestrate.js --task vendor-page-read --provider jina-read --live
```

The loader only reads keys from that private file or the environment; it never writes credentials back to disk. Use `--secrets-file FILE` to choose a different private file, or `--no-secrets-file` to disable automatic loading.

## Context compaction

- The default context budget is **12,000 estimated tokens**, far below the 200k-token context windows the owner wants to stay under. Override per run with `--context-budget N`, or disable compaction for one run with `--no-compact`.
- A task can pin its own policy: `context_policy: { mode: "auto", budget_tokens: 12000 }` or `{ mode: "off" }`.
- When the assembled prompt exceeds the budget, the harness first summarizes the inputs into a digest — live mode uses the cheapest credentialed summarize provider; dry-run uses a deterministic local digest — writes it to `derived/ai-orchestration/context/<task-id>.digest.md`, and runs the task against the digest.
- The run record records `compaction.applied`, the digest file, its hash, and the reason.

## Owner review

Before using any output as engineering evidence, the owner marks it:

```sh
node tools/ai-orchestrate.js --review --task cad-motor-gap-review --status accepted --notes "planning only"
node tools/ai-orchestrate.js --review --task practice-field-plan --status rejected --notes "waiting on bench data"
```

This writes `evidence/<task-id>.review.json` and mirrors the decision into the run record. Reviewing is an owner action; the agent does not review its own outputs.

## Credential policy

1. Rotate any key that has been pasted into a chat.
2. Store new credentials in `~/.config/ai-keys.env` with mode `600`, or in the provider console.
3. Keep the secrets file outside this repository.
4. Never paste keys into this repository, prompts, or generated artifacts.
5. Run the secrets guard before every commit.

## Evidence policy

Every run writes the generated advisory output, a JSON run record, input-file hashes with size and token estimates, prompt and response hashes, the provider family and cost rank, compaction metadata, and the review state. The run record never contains request headers or API keys.

## Files

- `registry.json` — provider metadata, never secrets.
- `tasks.json` — the current advisory tasks.
- `evidence/` — generated outputs, run records, and owner-review sidecars.
- `context/` — compaction digests.
- `../../prompts/` — reusable prompt templates.
- `../../tools/ai-orchestrate.js` — the CLI.
