# Project agent instructions

Canonical agent instructions live in [AGENTS.md](AGENTS.md) — read that first.

Owner-set constraints (no vendor CAD; open-source software only) are listed in
[AGENTS.md](AGENTS.md) under "Owner-set constraints" — treat them as hard rules.

Portable agent tooling (MCP servers, skills, harness wiring) is described in
[AGENT_TOOLS.md](AGENT_TOOLS.md). Provider keys load from `~/.config/ai-keys.env`
and must never be committed. Run the `secrets-guard` skill before committing.
