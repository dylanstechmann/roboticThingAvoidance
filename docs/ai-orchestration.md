# AI orchestration

This folder contains a local orchestration harness for routing narrowly scoped engineering tasks to external AI providers and recording advisory evidence.

Everything generated here is agent-run and advisory. It is not owner-reviewed engineering evidence unless explicitly marked otherwise.

## What this is

- A small Node 24 CLI.
- A provider registry with environment-variable names only.
- A task manifest.
- Prompt templates.
- A dry-run mode and an optional live mode.
- An evidence directory with hashes and run records.

## What this is not

- A replacement for owner review.
- A substitute for physical testing.
- A way to store API credentials.
- A claim that any AI output is validated engineering work.

## Files

- `registry.json` — provider metadata, never secrets.
- `tasks.json` — the current advisory tasks.
- `evidence/` — generated outputs and run records.
- `../../prompts/` — reusable prompt templates.
- `../../tools/ai-orchestrate.js` — the CLI.

## Usage

Dry-run a task:

```sh
node tools/ai-orchestrate.js \
  --task cad-motor-gap-review \
  --provider nvidia-robotics \
  --dry-run
```

Live mode automatically loads keys from `~/.config/ai-keys.env` if that file exists. You do not have to export keys manually.

Example:

```sh
node tools/ai-orchestrate.js \
  --task cad-motor-gap-review \
  --provider nvidia-robotics \
  --live
```

The loader only reads keys from that private file or the environment; it never writes credentials back to disk. Use `--secrets-file FILE` to choose a different private file, or `--no-secrets-file` to disable automatic loading.

## Provider routing

- Robotics, CAD, and vision tasks prefer NVIDIA-style robotics/VLM providers. The current registry uses `nvidia/nemotron-3-nano-omni-30b-a3b-reasoning` for those tasks.
- Rules interpretation and code review prefer general reasoning providers such as OpenRouter, Together, Fireworks, or DeepInfra.
- Web research can use Exa, Brave, Jina, or Firecrawl, but those are not part of this default harness.
- Literature tasks can use OpenAlex, Semantic Scholar, Core, or ORCID when a cited source is needed.

## Credential policy

1. Rotate any key that has been pasted into a chat.
2. Store new credentials in `~/.config/ai-keys.env` with mode `600`, or in the provider console.
3. Keep the secrets file outside this repository.
4. Never paste keys into this repository, prompts, or generated artifacts.
5. Run the secrets guard before every commit.

## Evidence policy

Every run writes:

- the generated advisory output;
- a JSON run record;
- input-file hashes;
- prompt and response hashes;
- the provider and model used.

The run record never contains request headers or API keys.

## Owner review

Before using any output as engineering evidence:

1. read the generated file;
2. compare it against the cited inputs;
3. mark it reviewed in the project notes;
4. record what was accepted and what was rejected.
