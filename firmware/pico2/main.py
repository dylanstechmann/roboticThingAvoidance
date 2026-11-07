# Boot entry for the mule. Default is IDLE: motors disabled, nothing moves.
# Run the E02 bench script only from the REPL, inside an approved bench setup:
#   >>> import main; main.bench("both")
# Run the E03 floor trials only from the REPL, inside an approved floor setup (wheels on the
# ground, a cleared area, the e-stop in reach, after E02A/E02):
#   >>> import main; main.floor("straight", run_id=1)
#   >>> import main; main.floor("spin", direction="left", run_id=2)
import json

import bench_e02
import floor_e03
from hal import PicoHal
from runner import Runner


def idle():
    hal = PicoHal()
    hal.set_duty(0.0, 0.0)
    hal.set_enabled(False)
    return hal


def bench(motor="both", run_id=1):
    runner = Runner(PicoHal(), mode="BENCH")
    outcome = bench_e02.run(runner, motor)
    lines = bench_e02.save(runner, "/e02-%d.jsonl" % run_id, json.dumps)
    print("E02 run", run_id, outcome, lines, "records; dropped", runner.log.dropped)
    return outcome


def floor(trial="straight", direction="left", speed_in_s=8.0, length_m=1.0,
          yaw_rate_rad_s=2.0, revolutions=1.0, run_id=1):
    runner = Runner(PicoHal(), mode="DRIVE")
    if trial == "straight":
        summary = floor_e03.straight(runner, speed_in_s, length_m)
    elif trial == "spin":
        summary = floor_e03.spin(runner, direction, yaw_rate_rad_s, revolutions)
    else:
        print("trial must be straight or spin")
        return None
    lines = floor_e03.save(runner, "/e03-%d.jsonl" % run_id, json.dumps)
    print("E03 run", run_id, summary, lines, "records; dropped", runner.log.dropped)
    return summary


if __name__ == "__main__":
    idle()
