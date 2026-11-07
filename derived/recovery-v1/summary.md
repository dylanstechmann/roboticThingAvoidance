# Blocked-route recovery v1: behaviors and the router-pass link

2026-11-07. Agent-run synthetic study (seeds 100-119, world world-ccw-line-sq-adv-align). Eight scenarios inject one guide-plush blocker — four corridor-spanning, four against a wall that leave a passable band; each seed also runs the unblocked baseline so the recovery success and the router pass are paired on every seed.

| scenario | behavior | pose | completed | passed blocker | recovered | w/ contact | blocked | stopped | incomplete | passed Wilson95 | mean s |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|---|---:|
| low_mid | lateral_shift | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 31.8 |
| low_mid | lateral_shift | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 31.8 |
| low_mid | replan_lanes | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 31.77 |
| low_mid | replan_lanes | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 31.79 |
| low_mid | stall_stop | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 31.76 |
| low_mid | stall_stop | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 31.75 |
| low_mid | auto | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 31.77 |
| low_mid | auto | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 31.79 |
| low_corner | lateral_shift | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 30.68 |
| low_corner | lateral_shift | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 30.69 |
| low_corner | replan_lanes | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 30.68 |
| low_corner | replan_lanes | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 30.69 |
| low_corner | stall_stop | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 30.68 |
| low_corner | stall_stop | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 30.69 |
| low_corner | auto | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 30.68 |
| low_corner | auto | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 30.69 |
| high_mid | lateral_shift | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 39.8 |
| high_mid | lateral_shift | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 39.83 |
| high_mid | replan_lanes | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 40.12 |
| high_mid | replan_lanes | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 40.16 |
| high_mid | stall_stop | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 40.07 |
| high_mid | stall_stop | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 40.09 |
| high_mid | auto | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 40.13 |
| high_mid | auto | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 40.16 |
| high_corner | lateral_shift | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 38.69 |
| high_corner | lateral_shift | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 38.71 |
| high_corner | replan_lanes | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 38.92 |
| high_corner | replan_lanes | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 38.95 |
| high_corner | stall_stop | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 38.98 |
| high_corner | stall_stop | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 39.01 |
| high_corner | auto | true_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 38.93 |
| high_corner | auto | ekf_pose | 0/20 | 0 | 0 | 0 | 20 | 0 | 0 | 0.0..0.1611 | 38.96 |
| low_mid_band | lateral_shift | true_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 82.09 |
| low_mid_band | lateral_shift | ekf_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 82.09 |
| low_mid_band | replan_lanes | true_pose | 17/20 | 17 | 0 | 17 | 3 | 0 | 0 | 0.6396..0.9476 | 76.05 |
| low_mid_band | replan_lanes | ekf_pose | 17/20 | 17 | 0 | 17 | 3 | 0 | 0 | 0.6396..0.9476 | 76.06 |
| low_mid_band | stall_stop | true_pose | 17/20 | 17 | 0 | 17 | 3 | 0 | 0 | 0.6396..0.9476 | 75.75 |
| low_mid_band | stall_stop | ekf_pose | 17/20 | 17 | 0 | 17 | 3 | 0 | 0 | 0.6396..0.9476 | 75.77 |
| low_mid_band | auto | true_pose | 17/20 | 17 | 0 | 17 | 3 | 0 | 0 | 0.6396..0.9476 | 76.11 |
| low_mid_band | auto | ekf_pose | 17/20 | 17 | 0 | 17 | 3 | 0 | 0 | 0.6396..0.9476 | 76.08 |
| low_corner_band | lateral_shift | true_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 82.09 |
| low_corner_band | lateral_shift | ekf_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 82.08 |
| low_corner_band | replan_lanes | true_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 85.4 |
| low_corner_band | replan_lanes | ekf_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 85.36 |
| low_corner_band | stall_stop | true_pose | 18/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 78.84 |
| low_corner_band | stall_stop | ekf_pose | 18/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 81.91 |
| low_corner_band | auto | true_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 85.38 |
| low_corner_band | auto | ekf_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 85.38 |
| high_mid_band | lateral_shift | true_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 81.9 |
| high_mid_band | lateral_shift | ekf_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 81.94 |
| high_mid_band | replan_lanes | true_pose | 17/20 | 17 | 0 | 17 | 3 | 0 | 0 | 0.6396..0.9476 | 76.55 |
| high_mid_band | replan_lanes | ekf_pose | 17/20 | 17 | 0 | 17 | 3 | 0 | 0 | 0.6396..0.9476 | 76.55 |
| high_mid_band | stall_stop | true_pose | 17/20 | 17 | 0 | 17 | 3 | 0 | 0 | 0.6396..0.9476 | 77.07 |
| high_mid_band | stall_stop | ekf_pose | 17/20 | 17 | 0 | 17 | 3 | 0 | 0 | 0.6396..0.9476 | 77.06 |
| high_mid_band | auto | true_pose | 17/20 | 17 | 0 | 17 | 3 | 0 | 0 | 0.6396..0.9476 | 76.6 |
| high_mid_band | auto | ekf_pose | 17/20 | 17 | 0 | 17 | 3 | 0 | 0 | 0.6396..0.9476 | 76.64 |
| high_corner_band | lateral_shift | true_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 81.9 |
| high_corner_band | lateral_shift | ekf_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 81.89 |
| high_corner_band | replan_lanes | true_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 85.0 |
| high_corner_band | replan_lanes | ekf_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 84.99 |
| high_corner_band | stall_stop | true_pose | 18/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 79.6 |
| high_corner_band | stall_stop | ekf_pose | 18/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 79.65 |
| high_corner_band | auto | true_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 84.99 |
| high_corner_band | auto | ekf_pose | 20/20 | 20 | 0 | 20 | 0 | 0 | 0 | 0.8389..1.0 | 85.01 |

## Router-pass association

Units: 320 (scenario x pose x seed). Recovery success is 'passed the injected blocker'. Spearman(recovery success, router pass) = None (permutation p = None); Spearman(recovery success, router planned contacts) = 0.0474 (p = 0.007999). Recovery success among router-pass rows None; among router-fail rows 0.4625. Method: midrank Spearman; two-sided permutation of whole pose/seed baseline clusters within pose. 40 independent pose/seed baseline clusters repeat across eight scenarios; pooled row rates are descriptive, not 320 independent observations. Null statistics indicate no rank variance and are reported rather than treated as evidence.

## Implementation notes (honest deviations from the plan)

- Only three expressible behaviors plus `auto` were studied: `backtrack` and `pit_bypass` are not expressible in the v10 oval route model (a kinematic forward follower; the field's single pit connection opens at the west end, so a mid-straight blocker cannot be detoured around). `stall_stop` is realized as the status-quo plan plus a blocker-local freeze that the supervisor stall watchdog then stops; a blanket collision-stop would also freeze ordinary quadrant-vehicle contacts that the sealed avoid/rl baselines tolerate. Recovery detection uses truth lane positions (`oracle`); a sensed-detection variant is a follow-on. Passage requires a directional crossing on the LAP route within the blocked corridor, so start/pit positions on the high side cannot be mistaken for a successful recovery.
