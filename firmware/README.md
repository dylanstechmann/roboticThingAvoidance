# Pico 2 firmware skeleton for the drivetrain mule

2026-11-03 · agent-written MicroPython for the owner's hobby/learning project.

**Not flashed, not run on hardware.** Everything here has run only in CPython host tests against a simulated motor (`host_tests/fakes.py`), whose parameters are placeholders.

## Safety first

- **E-stop:** the hardware e-stop must cut motor power by itself (GM1 R04). The firmware's e-stop input only mirrors it.
- **Boot:** the board boots to **IDLE**, with the driver disabled and zero duty.
- **Bench sessions:** run the bench script only from the REPL, inside an approved, supervised, current-limited setup (`derived/drivetrain-mule-v4/bench-readiness.md`, gates R2–R4), with the wheels off the ground.
- **Floor trials:** run the E03 floor script only from the REPL, inside an approved floor setup: wheels on the ground, a cleared area, one documented surface, the e-stop in reach, after E02A/E02. The trials need no gyro, reflectance or ToF — drift and spin error are physical (tape) measurements.
- **Latched stops:** every stop latches and never resumes by itself. Causes: e-stop, driver fault, a 250 ms command watchdog, repeated loop overruns, or the 178 s auto-stop. Re-arming needs a released e-stop and zero commands.
- **Pin map:** `pico2/config.py` holds a **provisional** pin map. The bench/electrical lead must check it against the chosen driver and the wiring before anything is energized (see `ORDER-B-BENCH-KIT.md`).
- **Encoder logic levels:** the 37D encoders output 5 V logic, so level-shift it to 3.3 V.

## Layout

| File | Role |
|---|---|
| `pico2/config.py` | Provisional pins, rates and limits |
| `pico2/hal.py` | The only file that touches `machine` (PWM, direction, enable, fault, e-stop sense, start switch, ADC) |
| `pico2/encoder.py` | PIO edge counter, see below. Also a pure-Python x4 decoder for simulation and hand checks. |
| `pico2/motor.py` | Wheel-speed PI with feed-forward, anti-windup and slew limit |
| `pico2/drive.py` | Turns speed and yaw-rate requests into wheel targets. Speed and yaw changes share one grip budget, and the robot slows down rather than change the turn radius when the faster wheel runs out of speed. |
| `pico2/safety.py` | Latching safety supervisor; every motor command passes through it |
| `pico2/telemetry.py` | RAM ring buffer of fixed-width records (about 165 KB for 3000); JSON Lines on dump, schema `../schemas/telemetry-v1.json` |
| `pico2/runner.py` | 200 Hz fixed-rate loop using wrapping `ticks_us` arithmetic |
| `pico2/bench_e02.py` | E02 open-loop duty steps |
| `pico2/floor_e03.py` | E03 closed-loop floor trials (straight/spin) that brake onto the target |
| `pico2/main.py` | Boot to IDLE; `main.bench()` and `main.floor()` from the REPL |
| `mission_driver.py` | Turns the supervisor's phases into routes and spins; needs no hardware, and `main.py` deliberately cannot start it yet |
| `route_store.py` | Reads the packed route files, one at a time |
| `geom.py` | MicroPython-safe planar geometry and 4×4 matrix helpers for the on-board EKF |
| `estimator.py` | On-board EKF port (`EstimatorBoard`) of `software/stockcar/estimator.py`; not wired into `main.py` |
| `field_tables.py` | Generated static map (barrier polygons, marking band) and estimator constants (`tools/build_field_tables.py`) |
| `host_tests/` | 79 CPython tests: safety latch, auto-stop, watchdog, controller, drive shaping, all 16 encoder transitions, ring buffer, a full simulated bench run, MicroPython lint, bench tools, the E03 floor trials, and the real control loop against the corrected drivetrain model (`plant_hal.py`), including whole laps and pit legs (`route_follow.py`) and whole missions (`full_mission.py`) |

The plant-backed tests catch control bugs, but their friction, mass and inertia values are placeholders, so passing them does not show that the gains suit a real robot. The motion limits in `config.py` come from the conservative envelope in `../derived/envelope-v10/`. Replace them after the E03 floor trials.

## Encoder decoding

Each encoder uses one PIO state machine. It counts rising edges of channel A, takes the direction from channel B, and pushes the running count to the RX FIFO.
- That is x1 decoding: **1120 counts per output revolution**, 0.22 mm of travel per count with 80 mm wheels.
- The common x4 jump-table program (archived as `sources/electrical-2026-10-31/pico-quadrature.pio`) must be loaded at instruction address 0. MicroPython does not guarantee that, so this skeleton avoids computed jumps.
- `poll()` must drain the FIFO faster than it can fill: at no-load speed that is about 2,800 edges per second per motor, so drain at 1 kHz or more.

**First bench check:** turn each wheel exactly one revolution by hand with the motors unpowered. Expect about ±1120 counts, with the sign set by `LEFT_ENCODER_SIGN` / `RIGHT_ENCODER_SIGN`.

## Flashing (owner, on the Windows host)

1. Install the MicroPython UF2 for the Raspberry Pi Pico 2 (RP2350) from micropython.org. Record the version.
2. Copy `pico2/*.py` to the board with Thonny or `mpremote cp`.

The bench work needs only those files. `python -I tools/build_pico_bundle.py OUT_DIR` builds the larger folder for later mission work: the firmware, `supervisor.py`, `tracker.py` and the packed routes. It has not been tried on a board. An on-board EKF port (`pico2/estimator.py`) plus its static map (`pico2/field_tables.py`) is present and host-parity-tested, but it is not wired into `main.py` — no sensor driver exists yet, so `main.py` still boots to IDLE only.

This container runs under WSL2 and normally cannot see the Pico's USB serial port without usbipd-win. Logs therefore move as files.

## Bench data flow

```text
board:   >>> import main; main.bench("both", run_id=1)      -> /e02-1.jsonl on the board
host:    copy the file off with Thonny or mpremote, into measurements/mule/<date>/
repo:    python -I tools/telemetry_schema.py measurements/mule/<date>/e02-1.jsonl
         python -I tools/bench/log_to_e02.py --motor left --bus-case nominal --run 1 <log>   # one CSV row; fill bus_v, current, temperature, operator, instruments yourself
         node tools/mule-measurements-v10.js --kind E02 --input <your E02 copy> --output <new file> --progress
         python -I tools/bench/fit_motor.py --side left --output calibration/motor-<date>-left.json <logs>
```

The fitted gain, deadband and time constant replace the placeholder feed-forward in `motor.py` and the simulated motor. Record every change as a dated, reviewed edit.

## E03 floor data flow

```text
board:   >>> import main; main.floor("straight", speed_in_s=8, run_id=1)    -> /e03-1.jsonl
         >>> import main; main.floor("spin", direction="left", run_id=2)   -> /e03-2.jsonl
host:    copy the file off with Thonny or mpremote, into measurements/mule/<date>/
repo:    python -I tools/bench/log_to_e03.py --support dual-front-rear --mass 2 --kind straight --direction forward --repeat 1 <log>   # one CSV row
         fill in drift_mm / spin_error_deg (tape), the slip flag, the surface and the provenance columns yourself, and set attempt_status once the row is complete
         node tools/mule-measurements-v10.js --kind E03 --input <your E03 copy> --output <new file> --progress
```

Each trial ends its commands one braking allowance short of the target so the shaper's ramp-down lands on it: without that, the yaw decel limit alone would overshoot a 360-degree spin by about 25 degrees, five times the 5-degree median-spin gate. The trial cells (support configuration, mass, 10 straight + 20 left + 20 right per cell) come from the E03 template, not the firmware.

## Run the host tests

```sh
uv run --no-project --python 3.12 python -B -I -m unittest discover -s firmware/host_tests -t firmware
```

`node tools/check-all.js` runs them too.
