# E03 floor trials (closed-loop, wheels on the ground), run only from the REPL inside an approved
# floor setup: a cleared area, one documented surface, the e-stop in reach, after E02A/E02. The
# trials need no gyro, reflectance or ToF: drift and spin error are physical (tape) measurements.
# Each trial commands body motion through the shaper and integrates encoder odometry for its
# stopping decision, ending the commands one braking allowance short of the target so the ramp-down
# lands on it (the shaper's yaw decel alone would overshoot a 360-degree spin by about 25 degrees
# at 2 rad/s). Logs to RAM; the caller writes /e03-<run>.jsonl after the motors stop.
# Speeds in/s, yaw rates rad/s, lengths m.

import math

import config

IN_TO_M = 0.0254
SETTLE_RPM = 2.0
SETTLE_TIMEOUT_S = 2.0


def check(speed_in_s, yaw_rate_rad_s):
    """Convert to SI and refuse parameters beyond the config.py motion envelope."""
    speed_m_s = speed_in_s * IN_TO_M
    wheel_m_s = config.MAX_WHEEL_RPM * config.WHEEL_RADIUS_M * 2.0 * math.pi / 60.0
    demand = abs(speed_m_s) + config.HALF_TRACK_M * abs(yaw_rate_rad_s)
    if demand > wheel_m_s:
        raise ValueError("command needs %.3f m/s at the fastest wheel; the envelope allows %.3f m/s"
                         % (demand, wheel_m_s))
    return speed_m_s, yaw_rate_rad_s


def _integrate(runner, last_counts, per_count_m):
    """One odometry sample: returns (counts, forward distance, differential yaw)."""
    counts = runner.hal.poll_encoders()
    dl = (counts[0] - last_counts[0]) * per_count_m
    dr = (counts[1] - last_counts[1]) * per_count_m
    return counts, (dl + dr) / 2.0, (dr - dl) / (2.0 * config.HALF_TRACK_M)


def _drive_until(runner, speed_m_s, yaw_rate_rad_s, reached):
    """Run the motion loop until reached(distance, yaw) or a safety stop latches."""
    per_count_m = 2.0 * math.pi * config.WHEEL_RADIUS_M / config.COUNTS_PER_OUTPUT_REV
    counts = runner.hal.poll_encoders()
    distance = 0.0
    yaw = 0.0
    deadline = runner.hal.ticks_us() + runner.period_us
    while not runner.safety.stopped and not reached(distance, yaw):
        runner.drive(speed_m_s, yaw_rate_rad_s)
        counts, ds, dyaw = _integrate(runner, counts, per_count_m)
        distance += ds
        yaw += dyaw
        deadline = runner.wait_next(deadline)
    return distance, yaw, counts


def _settle(runner, counts, distance, yaw):
    """Command zero motion while the shaper ramps down, until the wheels stop or the timeout."""
    per_count_m = 2.0 * math.pi * config.WHEEL_RADIUS_M / config.COUNTS_PER_OUTPUT_REV
    end_ms = runner.hal.ticks_ms() + int(SETTLE_TIMEOUT_S * 1000)
    deadline = runner.hal.ticks_us() + runner.period_us
    while not runner.safety.stopped:
        runner.drive(0.0, 0.0)
        counts, ds, dyaw = _integrate(runner, counts, per_count_m)
        distance += ds
        yaw += dyaw
        if abs(runner.rpm[0]) < SETTLE_RPM and abs(runner.rpm[1]) < SETTLE_RPM:
            break
        if runner.hal.ticks_diff(runner.hal.ticks_ms(), end_ms) >= 0:
            break
        deadline = runner.wait_next(deadline)
    return distance, yaw, counts


def straight(runner, speed_in_s=8.0, length_m=1.0):
    """One straight E03 trial: travel length_m at cruise speed, braking onto the target."""
    speed_m_s, _ = check(speed_in_s, 0.0)
    if length_m <= 0.0:
        raise ValueError("length must be positive")
    brake_m = speed_m_s * speed_m_s / (2.0 * config.MAX_BRAKE_M_S2)
    stop_at = length_m - brake_m
    if stop_at < 0.0:
        stop_at = 0.0
    if not runner.arm():
        return {"result": "not armed: release the e-stop and zero the commands", "length_m": length_m,
                "distance_m": 0.0, "duration_s": 0.0, "yaw_deg": 0.0, "stop_reason": "not_armed"}
    start_ms = runner.hal.ticks_ms()
    distance, yaw, counts = _drive_until(runner, speed_m_s, 0.0, lambda d, y: d >= stop_at)
    distance, yaw, counts = _settle(runner, counts, distance, yaw)
    runner.hal.set_duty(0.0, 0.0)
    runner.hal.set_enabled(False)
    duration_s = runner.hal.ticks_diff(runner.hal.ticks_ms(), start_ms) / 1000.0
    return {"result": runner.safety.stop_reason or "completed", "length_m": length_m,
            "distance_m": round(distance, 4), "duration_s": round(duration_s, 3),
            "yaw_deg": round(yaw * 180.0 / math.pi, 2), "stop_reason": runner.safety.stop_reason}


def spin(runner, direction, yaw_rate_rad_s=2.0, revolutions=1.0):
    """One spin E03 trial: turn in place for the given revolutions, braking onto the target."""
    if direction not in ("left", "right"):
        raise ValueError("direction must be left or right")
    _, yaw_rate = check(0.0, yaw_rate_rad_s)
    if revolutions <= 0.0:
        raise ValueError("revolutions must be positive")
    sign = 1.0 if direction == "left" else -1.0
    target_yaw = sign * 2.0 * math.pi * revolutions
    brake_yaw = yaw_rate * yaw_rate / (2.0 * config.MAX_YAW_ACCEL_RAD_S2)
    if abs(target_yaw) <= brake_yaw:
        raise ValueError("revolutions too small to stop on target at this yaw rate")
    stop_at_yaw = target_yaw - sign * brake_yaw
    if not runner.arm():
        return {"result": "not armed: release the e-stop and zero the commands", "direction": direction,
                "revolutions": revolutions, "distance_m": 0.0, "duration_s": 0.0, "yaw_deg": 0.0,
                "stop_reason": "not_armed"}
    start_ms = runner.hal.ticks_ms()
    distance, yaw, counts = _drive_until(runner, 0.0, sign * yaw_rate,
                                         lambda d, y: abs(y) >= abs(stop_at_yaw))
    distance, yaw, counts = _settle(runner, counts, distance, yaw)
    runner.hal.set_duty(0.0, 0.0)
    runner.hal.set_enabled(False)
    duration_s = runner.hal.ticks_diff(runner.hal.ticks_ms(), start_ms) / 1000.0
    return {"result": runner.safety.stop_reason or "completed", "direction": direction,
            "revolutions": revolutions, "yaw_deg": round(yaw * 180.0 / math.pi, 2),
            "distance_m": round(distance, 4), "duration_s": round(duration_s, 3),
            "stop_reason": runner.safety.stop_reason}


def save(runner, path, dumps):
    with open(path, "w") as f:
        return runner.log.dump(lambda line: f.write(line + "\n"), dumps)