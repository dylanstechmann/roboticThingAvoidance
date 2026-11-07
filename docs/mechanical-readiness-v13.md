# V13 mechanical readiness — source-evidenced digital study

## Historical status (2026-11-07)

This study's vendor-CAD variants and fit gates derive from archived vendor geometry. Under the owner's standing constraint (recorded in `AGENTS.md`: no vendor CAD; open-source software only), everything in this document is **historical reference only, not geometry authority**. New geometry comes from owner measurement of received parts and open-source models; see `docs/motor-dimensions-published.md` for the page-published motor baseline and `derived/cad-v13/README.md` for the artifact directory status.

**Status: not mechanically ready for fabrication or competition.** This is an agent-run CAD and simulation study for a personal hobby/learning project. No parts have been purchased or measured, no mechanism or electronics actuator has been selected, and no physical robot test or owner-reviewed approval is claimed.

Open the self-contained `share/Showcase-v13.html` directly in a browser. It works offline. Build and validation evidence is under `derived/showcase-v13/`; generated CAD is under `derived/cad-v13/`.

## Selected hardware and geometry

The procurement snapshot covers Pololu **#4754** motor, **#1995** bracket, **#1083** hub, **#1430** wheel, **#953** caster and **#1962** wheel screw. Archived product pages, drawings and manufacturer STEP files remain read-only evidence in `sources/`; hashes and paths are recorded in `derived/cad-v13/manifest.json`.

- **17 native-scale GLB assets, 11 selected part types and 34 placed instances.**
- Conversion and metrology use **CadQuery/OpenCASCADE, cascadio and trimesh**, not a proprietary CAD application.
- Purchased geometry is never rescaled to force a fit. Motor internals, fastener heads and threads are simplified or omitted as recorded per part.
- The default retains the detailed vendor motor body and replaces only its isolated shaft region with the published **16 mm** D-shaft derivative. It is not represented as unmodified vendor CAD.
- The separate comparison retains the archived **22 mm** shaft. Neither variant resolves the physical source conflict.

| Variant | Wheel-center track | Overall CAD width | Assembly identity |
|---|---:|---:|---|
| Published 16 mm — default | 190 mm | 203.5 mm | `order-a-bom-nominal-16mm-v13` |
| Archived vendor CAD 22 mm | 202 mm | 215.5 mm | `order-a-vendor-cad-22mm-v13` |

Source dimensions and assembly datums are **millimetres**. Runtime positions are converted explicitly to **metres**; placed instance scale remains `(1,1,1)`. Rendering, exported assembly nodes, reduced-order colliders and run JSON carry the same assembly ID and hash.

## Fit gates — failures retained

`derived/cad-v13/fit-results.json` reports **8 passes, 2 failures and 2 source conflicts** across the two variants.

| Check | Result | Interpretation |
|---|---|---|
| 6 mm shaft / hub bore | Pass, nominal | Not received-part tolerance qualification. |
| 9.2 mm hub engagement span | Pass, nominal | Named geometric check only. |
| 80 mm wheel diameter | Pass, nominal | Archived vendor geometry. |
| Motor-body gap | **FAIL: 7.8 mm < 8 mm** | Fails in both variants; not hidden or relaxed. |
| Motor shaft source length | **CONFLICT** | Product page states 16 mm; archived STEP measures 22 mm. |
| Gate travel clearance | Pass at 21 sampled poses | Exact-solid gate/lift overlap check; not a continuous collision certificate. |

The proposed mechanism has no selected actuator, bearings, fasteners, electronics or manufacturing process. Its strength, compliance, safety and thermal performance are unqualified.

## Live contact study

The fixed-step **Rapier 0.12.0** model uses a level-plane chassis, force-limited differential traction, a dynamic compound tire and named cuboid lift/gate colliders. The gate remains collidable through its continuous **54 mm horizontal** stroke. There is no tire attachment, pickup weld, tire pose writing or retry logic.

Load-bearing fork/tray contact is evaluated separately from incidental open-gate contact. Release requires independent destination-fixture support, low tire height and persistence. Mass, inertia, friction and actuator values remain editable assumptions; ideal position-actuated joints do not size real actuators.

Saved headless outcomes in `derived/showcase-v13/live-validation.json`:

| Run | Outcome | Time | Evidence |
|---|---|---:|---|
| Nominal demo | **PASS** | 352.892 s | 3 laps; 228.867 s carried; 0.508 s pickup support; 0.500 s independent release |
| 0.12 kg tire demo | **PASS** | 352.892 s | Same completed mission; heavier assumed tire |
| Missing tire | **FAIL** | 115.458 s | Acquisition failed; zero carried time |
| Weak lift | **FAIL** | 107.467 s | Assumed payload exceeds actuator force |
| Misaligned tire | **FAIL** | 122.817 s | Acquisition failed; zero carried time |
| Organizer field | **FAIL** | 60.042 s | Acquisition failed: no elevated tire supported by fork contacts |

The source and destination rails are **proposed fixtures**, not official tire hardware. The organizer-field result is not a competition score, robot qualification or validation of organizer tire geometry.


## Browser and reproducibility evidence

`derived/showcase-v13/browser-validation.json` records **16 offline Chromium checks and 16 screenshots**, with **zero page/console errors, zero external requests and no 390 px horizontal overflow**. Checks include every selectable part with in-canvas projected bounds, desktop and narrow whole-robot framing, both shaft variants, current-datum part framing, post-mission zero-joint restoration, actual run-JSON download, pause, named gate contacts and independent release. The same run verifies operation with Safari 15.0-era APIs (`structuredClone`, `Array.prototype.at`, `replaceChildren`) removed, an explicit WebGL2 diagnostic when WebGL2 is unavailable, and a no-JavaScript warning for iOS Files/Mail previews. Those compatibility cases are Chromium simulations, not physical iPhone validation.

Key files:

- `derived/showcase-v13/assembly.glb` and `assembly-manifest.json` — 34-node assembly export.
- `derived/showcase-v13/collision-study.json` — seven named reduced-order colliders.
- `derived/showcase-v13/build-manifest.json` — HTML inputs, dependency hashes and output hash.
- `derived/showcase-v13/validation-summary.json` — deterministic projection of saved reports.
- `derived/showcase-v13/screenshots/` — part, assembly, live, organizer and narrow-layout captures.

## Reproduce

```sh
node --test tests/assembly-spec-v13.test.js tests/showcase-v13.test.js tests/live-physics-v13.test.js
uv run --offline --no-project --python 3.12 --with cadquery==2.8.0 \
  --with cascadio==0.1.1 --with trimesh==5.2.0 \
  python -B -m unittest discover -s cad-v13/tests -v
node tools/verify-cad-v13.js
node tools/check-live-v13.js
node tools/build-showcase-v13.js
node tools/check-showcase-v13-browser.js
node tools/check-all.js --json /tmp/ieee-v13-full.json
node tools/summarize-v13-validation.js /tmp/ieee-v13-full.json
```

The engineering blockers remain the **7.8 mm motor gap**, **16/22 mm source conflict**, **organizer-field acquisition failure**, and absence of selected mechanism/electronics hardware and physical measurements.
