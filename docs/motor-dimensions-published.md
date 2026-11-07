# Published motor dimensions — BOM drive motor (Pololu #4754)

Manufacturer-page evidence for the BOM drive motor. These are **published manufacturer values**, not received-part measurements, and not vendor CAD. Geometry authority for design work is the owner's physical measurement of received parts.

Owner constraint (2026-11-07): this project uses no vendor CAD and only open-source software. This page-evidence file is the non-CAD baseline for planning caliper checks; see `AGENTS.md` "Owner-set constraints".

## Provenance

| Field | Value |
|---|---|
| Source | `sources/hardware-2026-10-31/pololu/product-4754-specs.html` (archived manufacturer page) |
| sha256 | `75e2d2b69b0277c45daabbb4f2ae617d3fbb14a9c89cf9fa43effba5f42afc71` |
| Archived | 2026-10-31 |
| Product | Pololu #4754 — 70:1 Metal Gearmotor 37Dx70L mm 12V with 64 CPR Encoder (Helical Pinion) |

## Published dimensions and specs (as stated on the archived page)

| Item | Published value |
|---|---|
| Size (gearbox) | 37D × 70L mm |
| Weight | 205 g |
| Output shaft | 6 mm diameter D-shaft, 16 mm long |
| Gear ratio | 70:1 |
| Motor voltage | 12 V |
| No-load | 150 RPM, 200 mA |
| Stall extrapolation | 27 kg·cm (380 oz·in), 5.5 A |
| Encoder resolution | 64 CPR on the motor shaft; 4480 CPR on the gearbox output shaft |

Anything not stated on the archived page is not listed here. Do not fill gaps from vendor CAD.

## Historical context (vendor CAD-derived; historical only)

- The sealed v13 fit study (`docs/mechanical-readiness-v13.md`, historical) reported a **7.8 mm motor-body gap** against an 8 mm requirement, derived from archived vendor geometry. Retained as history; not geometry authority.
- The same study recorded a **16 mm vs 22 mm shaft-length conflict**: this page states 16 mm; the archived vendor STEP measures 22 mm. The published 16 mm value is the planning baseline here; measure the received part.
- The v13 BOM record's 70.1 mm body length and 7 mm shaft offset came from vendor-STEP-derived metrology (`cad-v13/bom-evidence.json`, historical), not from this page.

## Use

Input for the `cad-motor-gap-review` advisory task: plan caliper measurements of the received motors against these published values before any layout revision.

## Advisory boundary

Agent-curated from the archived manufacturer page. Not owner-reviewed engineering evidence. Do not claim owner review, physical testing, or competition qualification.
