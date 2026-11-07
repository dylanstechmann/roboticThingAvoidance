**Pico 2 Bench‑first Firmware Bring‑up Checklist**
*(run with wheels off the ground, current‑limited bench supply, and a qualified operator present)*

| # | Action & Pass Criterion | Tools / Instruments | Expected Log / Measurement | Stop‑condition (owner review) |
|---|--------------------------|---------------------|----------------------------|------------------------------|
| 1 | **Power‑off check** – board un‑powered, all driver enable pins low. | USB‑power off switch, multimeter (continuity). | 0 V on `ENABLE`, `FAULT`, `ESTOP_SENSE`. | Any pin reads >0 V → verify wiring before proceeding. |
| 2 | **Pin‑map validation** – compare `pico2/config.py` pins to driver datasheet (GM1 R04) and bench harness. | Printed pin‑map, bench wiring diagram, continuity tester. | All listed pins short to correct header pins. | Mismatch → abort, re‑wire, and document change. |
| 3 | **Level‑shift verification** – 5 V encoder outputs are safely shifted to 3.3 V. | Oscilloscope or logic probe on encoder lines after level‑shifter. | High ≤ 3.3 V, low ≤ 0.3 V. | Voltage > 3.6 V → replace/adjust level‑shifter. |
| 4 | **E‑stop functional test** – trigger hardware E‑stop; driver power must drop immediately. | E‑stop button, bench power meter on driver supply. | Driver supply current → 0 A within 50 ms of actuation. | Power does not drop → stop, repair E‑stop circuit. |
| 5 | **Flash MicroPython UF2 & copy sources** – board shows `>>>` REPL after reset. | PC, Thonny or `mpremote cp`, UF2 file. | REPL prompt appears; `import pico2` succeeds. | No REPL or import error → re‑flash UF2. |
| 6 | **Run idle‑state sanity script** – `main.boot()` should leave driver disabled, duty = 0. | REPL, `import main; main.boot()` | Log: `driver_enabled=False`, `duty=0`. | Driver enabled or non‑zero duty → abort, check `hal.py`. |
| 7 | **Encoder count sanity** – rotate each wheel **exactly one free revolution** (hand turn, motor un‑powered). | Hand crank, encoder count read via `pico2.encoder.poll()`. | Count ≈ ±1120 (sign matches `LEFT_ENCODER_SIGN`/`RIGHT_ENCODER_SIGN`). | Count outside 900‑1300 or wrong sign → review encoder wiring and sign constants. |
| 8 | **FIFO drain rate test** – run `pico2.bench_e02.open_loop()` at 0 % duty for 5 s. | REPL, bench script, timer. | No FIFO overflow warnings; CPU load < 80 %. | Overflow or watchdog reset → increase poll rate or fix PIO program. |
| 9 | **Current‑limit verification** – set bench supply to 2 A limit, run open‑loop duty = 30 % for 2 s. | Current‑limited bench supply, ammeter. | Current ≤ 2 A, voltage stable. | Current exceeds limit → stop, check driver gain or motor wiring. |
|10| **Safety‑latch test – driver fault** – short motor leads briefly to induce fault. | Jumper wires, safety goggles. | `safety.latch` becomes true, driver disabled, log entry “FAULT”. | Latch does not engage → abort, inspect fault sense circuit. |
|11| **Watchdog timeout test** – pause main loop > 250 ms (e.g., `time.sleep(0.5)` inside loop). | Modify `pico2/runner.py` temporarily, REPL. | Safety latch triggers with reason “watchdog”. | No latch → review watchdog implementation. |
|12| **Auto‑stop timer test** – run open‑loop duty = 100 % for 180 s (or until 178 s auto‑stop). | REPL, timer. | Log shows “auto‑stop after 178 s”, driver disabled. | Motor continues > 180 s → stop, check `safety.auto_stop` logic. |
|13| **Telemetry dump verification** – after any bench run, copy `/e02-*.jsonl` to host and run schema validator. | `mpremote get`, `tools/telemetry_schema.py`. | Validation returns “OK”; records contain `timestamp`, `duty`, `current`, `encoder_counts`. | Schema errors → owner reviews data integrity and firmware logging. |
|14| **Final power‑down & latch reset** – release E‑stop, ensure all latches cleared, driver remains disabled. | E‑stop release, REPL `safety.reset()`. | `safety.latch == False`, `driver_enabled == False`. | Latch persists → owner must manually clear fault and investigate root cause. |

*If any stop‑condition is hit, cease further steps, document the observation, and obtain owner sign‑off before retrying.*
