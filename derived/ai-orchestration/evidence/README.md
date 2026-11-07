# Evidence

Files in this directory are AI-generated advisory artifacts.

They are **not** owner-reviewed engineering evidence unless explicitly marked as reviewed in the project notes.

Each task normally produces:

- `<task-id>.md` — advisory output.
- `<task-id>.run.json` — run record with provider, model, timestamps, and hashes.

The run record never contains API keys or request headers.

When a prompt exceeds the context budget, the harness first writes a digest under `../context/<task-id>.digest.md` and records the digest hash in the run record.

`<task-id>.review.json` sidecars are written only by the owner through the `--review` mode; the agent does not review its own outputs.

Before treating any file here as engineering evidence, the owner must:

1. read it;
2. compare it against the cited inputs;
3. accept or reject the recommendation;
4. record the decision.
