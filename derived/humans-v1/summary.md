# Isolated-human planner safety v1

2026-11-07. Agent-run synthetic study, N=1..10 x 20 seeds = 200 runs. Humans are static 10 in discs with truth positions. First contact aborts immediately; only lane-change straightaways are considered by the oracle planner. A 10 in human + 10 in robot + margins leaves only narrow wall-adjacent bands; centered humans are infeasible.

| N | completed | completion rate | contact runs | total contacts | aborted | min-clearance p50 | p05 |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 8/20 | 0.4 | 12/20 | 12 | 12/20 | -0.1744 | -0.4244 |
| 2 | 0/20 | 0.0 | 20/20 | 20 | 20/20 | -0.2544 | -0.4204 |
| 3 | 0/20 | 0.0 | 20/20 | 20 | 20/20 | -0.1482 | -0.4204 |
| 4 | 0/20 | 0.0 | 20/20 | 20 | 20/20 | -0.2079 | -0.7795 |
| 5 | 0/20 | 0.0 | 20/20 | 20 | 20/20 | -0.2438 | -0.6617 |
| 6 | 0/20 | 0.0 | 20/20 | 20 | 20/20 | -0.2438 | -0.6299 |
| 7 | 0/20 | 0.0 | 20/20 | 20 | 20/20 | -0.2438 | -0.6299 |
| 8 | 0/20 | 0.0 | 20/20 | 20 | 20/20 | -0.2438 | -0.6299 |
| 9 | 0/20 | 0.0 | 20/20 | 20 | 20/20 | -0.2667 | -0.6299 |
| 10 | 0/20 | 0.0 | 20/20 | 20 | 20/20 | -0.28 | -0.6299 |

Placements are nested in start/pit-lane/lane-change/turn order. N therefore changes both crowding and zone composition; no causal or monotonic trend is claimed. Human contacts are separate from vehicle contacts. Static truth geometry is not human perception, and completion without a human contact is not a physical safety qualification.
