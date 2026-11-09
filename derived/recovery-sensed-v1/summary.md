# recovery-sensed-v1 — sensed blocker detection

Agent-run synthetic study (2026-11-07). Every run plans only from the forward range ring's confirmed `VehicleMap`; the first plan is a plain-lane discovery lap and recovery replans fire when a newly confirmed vehicle is within 30 in ahead on the blocked side. Blocker contact/pass are still measured with ground truth, so only the planning input is deprived.

## Measured outcomes (not tuned)
- runs: 1280 (8 scenarios x 4 behaviors x 2 pose modes x 20 seeds)
- recovered or recovered_contact: 598/1280
- blocked: 682; stopped: 0; incomplete: 0
- band scenarios recovered: 598/640; spanning scenarios: 0/640
- confirm never reached: 0/1280; contacted before confirm: 0/1280
- unblocked sensed baseline: 40/40 completed

## Semantics and limitations
- `stall_stop` here is the blind default-lane baseline (no sensing use), unlike recovery-v1's truth plan_straight lane; the two studies are not drop-in comparable on the band scenarios.
- The sensed planner sees an assumed guide-size near face (yaw=0, labeled depth); ray layout, noise, dropout and gates are placeholders pending Order B bench data (QA03/QA08).
- EKF pose mode feeds the estimator pose to the controller; the range ring uses the truth pose, mirroring the avoiding-simulator convention.
- Outcomes are measured, not claims of hardware robustness.

## Oracle vs sensed (from the sealed recovery-v1 report, rates are fractions)
```
low_mid lateral_shift true_pose oracle=0.000 sensed=0.000
low_mid lateral_shift ekf_pose oracle=0.000 sensed=0.000
low_mid replan_lanes true_pose oracle=0.000 sensed=0.000
low_mid replan_lanes ekf_pose oracle=0.000 sensed=0.000
low_mid stall_stop true_pose oracle=0.000 sensed=0.000
low_mid stall_stop ekf_pose oracle=0.000 sensed=0.000
low_mid auto true_pose oracle=0.000 sensed=0.000
low_mid auto ekf_pose oracle=0.000 sensed=0.000
low_corner lateral_shift true_pose oracle=0.000 sensed=0.000
low_corner lateral_shift ekf_pose oracle=0.000 sensed=0.000
low_corner replan_lanes true_pose oracle=0.000 sensed=0.000
low_corner replan_lanes ekf_pose oracle=0.000 sensed=0.000
low_corner stall_stop true_pose oracle=0.000 sensed=0.000
low_corner stall_stop ekf_pose oracle=0.000 sensed=0.000
low_corner auto true_pose oracle=0.000 sensed=0.000
low_corner auto ekf_pose oracle=0.000 sensed=0.000
high_mid lateral_shift true_pose oracle=0.000 sensed=0.000
high_mid lateral_shift ekf_pose oracle=0.000 sensed=0.000
high_mid replan_lanes true_pose oracle=0.000 sensed=0.000
high_mid replan_lanes ekf_pose oracle=0.000 sensed=0.000
high_mid stall_stop true_pose oracle=0.000 sensed=0.000
high_mid stall_stop ekf_pose oracle=0.000 sensed=0.000
high_mid auto true_pose oracle=0.000 sensed=0.000
high_mid auto ekf_pose oracle=0.000 sensed=0.000
high_corner lateral_shift true_pose oracle=0.000 sensed=0.000
high_corner lateral_shift ekf_pose oracle=0.000 sensed=0.000
high_corner replan_lanes true_pose oracle=0.000 sensed=0.000
high_corner replan_lanes ekf_pose oracle=0.000 sensed=0.000
high_corner stall_stop true_pose oracle=0.000 sensed=0.000
high_corner stall_stop ekf_pose oracle=0.000 sensed=0.000
high_corner auto true_pose oracle=0.000 sensed=0.000
high_corner auto ekf_pose oracle=0.000 sensed=0.000
low_mid_band lateral_shift true_pose oracle=1.000 sensed=1.000
low_mid_band lateral_shift ekf_pose oracle=1.000 sensed=1.000
low_mid_band replan_lanes true_pose oracle=0.850 sensed=0.700
low_mid_band replan_lanes ekf_pose oracle=0.850 sensed=0.700
low_mid_band stall_stop true_pose oracle=0.850 sensed=1.000
low_mid_band stall_stop ekf_pose oracle=0.850 sensed=1.000
low_mid_band auto true_pose oracle=0.850 sensed=0.700
low_mid_band auto ekf_pose oracle=0.850 sensed=0.700
low_corner_band lateral_shift true_pose oracle=1.000 sensed=1.000
low_corner_band lateral_shift ekf_pose oracle=1.000 sensed=1.000
low_corner_band replan_lanes true_pose oracle=1.000 sensed=0.950
low_corner_band replan_lanes ekf_pose oracle=1.000 sensed=1.000
low_corner_band stall_stop true_pose oracle=1.000 sensed=1.000
low_corner_band stall_stop ekf_pose oracle=1.000 sensed=1.000
low_corner_band auto true_pose oracle=1.000 sensed=0.950
low_corner_band auto ekf_pose oracle=1.000 sensed=1.000
high_mid_band lateral_shift true_pose oracle=1.000 sensed=1.000
high_mid_band lateral_shift ekf_pose oracle=1.000 sensed=1.000
high_mid_band replan_lanes true_pose oracle=0.850 sensed=0.800
high_mid_band replan_lanes ekf_pose oracle=0.850 sensed=0.800
high_mid_band stall_stop true_pose oracle=0.850 sensed=1.000
high_mid_band stall_stop ekf_pose oracle=0.850 sensed=1.000
high_mid_band auto true_pose oracle=0.850 sensed=0.800
high_mid_band auto ekf_pose oracle=0.850 sensed=0.800
high_corner_band lateral_shift true_pose oracle=1.000 sensed=1.000
high_corner_band lateral_shift ekf_pose oracle=1.000 sensed=1.000
high_corner_band replan_lanes true_pose oracle=1.000 sensed=1.000
high_corner_band replan_lanes ekf_pose oracle=1.000 sensed=1.000
high_corner_band stall_stop true_pose oracle=1.000 sensed=1.000
high_corner_band stall_stop ekf_pose oracle=1.000 sensed=1.000
high_corner_band auto true_pose oracle=1.000 sensed=1.000
high_corner_band auto ekf_pose oracle=1.000 sensed=1.000
```

