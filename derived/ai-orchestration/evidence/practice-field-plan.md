**Practice‑field Build & Measurement Plan**
*(All references are to the current evidence files – `BACKCAST‑2026‑11.md` [1] and `mechanical‑readiness‑v13.md` [2]. No work has been started.)*

---

### 1. Materials & pre‑cut dimensions
| Item | Qty | Nominal size | Verify against | Comment |
|------|-----|--------------|----------------|---------|
| 12 mm MDF board (base) | 1 sheet (4 ft × 8 ft) | 1220 mm × 2440 mm | [1] field‑size note (conservative 10 in × 10 in square) | Cut to 254 mm × 254 mm (10 in) for the “box” footprint. |
| 6 mm acrylic (obstacle panels) | 4 pcs | 150 mm × 150 mm | [2] gate‑travel clearance (21 poses) | Keep ≥ 54 mm stroke clearance (gate travel). |
| 30 mm × 30 mm × 6 mm wood strips | 8 pcs | 300 mm length | [2] motor‑body gap (7.8 mm < 8 mm) | Use as spacers to raise motor mount ≥ 8 mm. |
| 3 mm steel angle (frame reinforcement) | 4 pcs | 200 mm length | [2] wheel‑center track (190 mm) | Align with wheel‑track to avoid interference. |
| 4 mm threaded rod & nuts (adjustable height) | 2 sets | 300 mm | [2] shaft‑hub bore (6 mm) | Provides fine‑tune for tire‑fork clearance. |
| 2 mm double‑sided tape (temporary fixtures) | – | – | – | For prototype placement before final fasteners. |

*All dimensions are in mm; convert to inches only for documentation.*

---

### 2. Build order (sequential, ≤ 1 day per step)
1. **Cut base plate** to 254 mm × 254 mm.
2. **Mark datum grid**: center (0,0), +/‑95 mm edges, wheel‑track lines at ±95 mm.
3. **Attach steel angles** along the long edges of the base (screw into MDF).
4. **Install acrylic panels** as the three “gate” obstacles (front, left, right) using tape; leave 54 mm clearance between panel edge and wheel‑track line.
5. **Mount wood spacers** on the base at the four wheel‑track corners; verify ≥ 8 mm height (motor‑gap requirement).
6. **Drill and insert threaded rods** through spacer holes for later height adjustment.
7. **Place reference markers** (e.g., 25 mm black squares) at the four corners of the 10 in × 10 in box for vision‑system calibration.
8. **Secure all fasteners** with a torque of 1.5 Nm (hand‑tight, no over‑torque).

---

### 3. Measurement checklist (tolerances)
| Check | Target | ± Tolerance | Method | Evidence |
|-------|--------|------------|--------|----------|
| Base plate square | 254 mm × 254 mm | 0.5 mm | Caliper | Log `base_dim.log` |
| Wheel‑track width | 190 mm (default) or 202 mm (vendor) | 0.3 mm | Digital caliper | `track_width.log` |
| Motor‑body gap (spacer height) | ≥ 8 mm | +0 mm / –0.2 mm | Depth gauge | `gap_meas.log` |
| Gate‑stroke clearance | ≥ 54 mm | 0 mm | Ruler | `gate_clear.log` |
| Obstacle panel alignment (parallel to datum) | 0° | ±0.5° | Protractor/angle gauge | `panel_angle.log` |
| Marker corner spacing (box) | 254 mm | 0.5 mm | Tape measure | `marker_spacing.log` |
| Threaded‑rod verticality | 90° | ±0.2° | Angle block | `rod_vert.log` |

All logs must be timestamped (ISO 8601) and stored in `evidence/field_meas/`.

---

### 4. Photo / log requirements for evidence
*For each build step (1‑8) capture:*
- **Wide shot** of the entire field (incl. datum grid).
- **Close‑up** of the measured feature (e.g., gap, clearance).
- **Overlay** of measured value (text) on the image.
- Save as `stepXX_<feature>.jpg` in `evidence/photos/`.

*Log files* (CSV with columns `timestamp,feature,value,unit,pass/fail`) must be committed to the repository alongside the photos.

---

### 5. First field‑test criteria (Gate G1 “Risks measured”)
1. **Physical field built** and all checklist items **pass** (see §3).
2. **Mule robot** (or test rig) placed on the base; wheel‑track measured ≤ 190 mm (or 202 mm) matches CAD variant.
3. **Obstacle‑gate interaction**: drive a low‑speed (0.2 m/s) test cart through each gate; record no contact > 5 mm penetration (use video with a ruler overlay).
4. **Box entry**: cart must fully enter the 10 in × 10 in box without touching the marker edges (≤ 2 mm clearance).
5. **Evidence package**: at least one photo per gate test, a CSV log `gate_test.csv`, and a short video (`gate_test.mp4`).

*Success* = all five items satisfied → gate G1 passes per the back‑cast schedule [1].

---

*Prepared for immediate execution; all steps reference the current digital evidence and respect the “no‑physical‑work‑yet” constraint.*
