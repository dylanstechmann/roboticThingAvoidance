# V13 CAD artifacts — historical status

**Historical-only as of 2026-11-07.** The artifacts in this directory (`fit-results.json`, `assembly-spec.json`, `assembly-vendor-22mm.json`, `manifest.json`, `parts/`) derive from archived vendor STEP geometry (`sources/hardware-2026-10-31/pololu/step/`). The owner's standing decision is that this project uses **no vendor CAD** and only open-source software.

- These files stay byte-identical because `tools/verify-cad-v13.py` pins them through `manifest.json` `inputHashes` and re-checks fit rows; the sealed v13 study must remain verifiable.
- Treat every finding here as historical reference, never as geometry authority. The 7.8 mm motor-body gap failure and the 16/22 mm shaft-length conflict are vendor-geometry-derived historical results.
- No new task, prompt, design, or geometry may search for, download, import, or build on vendor CAD. New geometry authority is owner measurement of received parts, or open-source models authored in this repository with the CadQuery/OpenCASCADE toolchain.
- Manufacturer pages, datasheets, and drawings remain allowed evidence (see `docs/motor-dimensions-published.md`); archived vendor STEP/PDF under `sources/` is reference-only history.

Agent-run annotation for the owner, 2026-11-07. Not owner-reviewed engineering evidence.
