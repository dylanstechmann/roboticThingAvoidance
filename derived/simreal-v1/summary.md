# Sim-to-real v1: E03-gate transfer screening

2026-11-07. Agent-run screening over six sealed worlds and three policies. Source: `provisional-plant` (PROVISIONAL SYNTHETIC PLANT). This is not a full-mission physical-pass probability and is not hardware qualification.

| world | policy | sim pass | expected p50 | p2.5 | p97.5 | fragile |
|---|---|---:|---:|---:|---:|---|
| world-ccw-line-sq-adv-align | classical | 20/20 | 0.988747 | 0.879203 | 0.999978 | false |
| world-ccw-line-sq-adv-align | random | 0/20 | 0.010789 | 2.9e-05 | 0.113185 | false |
| world-ccw-line-sq-adv-align | learned | 17/20 | 0.844027 | 0.650042 | 0.955345 | false |
| world-ccw-gate-sq-adv-align | classical | 20/20 | 0.988571 | 0.881184 | 0.999975 | false |
| world-ccw-gate-sq-adv-align | random | 0/20 | 0.011151 | 2e-05 | 0.11947 | false |
| world-ccw-gate-sq-adv-align | learned | 17/20 | 0.844878 | 0.653587 | 0.957303 | false |
| world-ccw-line-rd-adv-align | classical | 20/20 | 0.989277 | 0.885525 | 0.999973 | false |
| world-ccw-line-rd-adv-align | random | 0/20 | 0.011134 | 2.4e-05 | 0.116744 | false |
| world-ccw-line-rd-adv-align | learned | 0/20 | 0.01129 | 2.3e-05 | 0.116011 | false |
| world-ccw-gate-rd-adv-align | classical | 20/20 | 0.988899 | 0.883157 | 0.99998 | false |
| world-ccw-gate-rd-adv-align | random | 0/20 | 0.01136 | 2.2e-05 | 0.116476 | false |
| world-ccw-gate-rd-adv-align | learned | 0/20 | 0.010536 | 2.2e-05 | 0.116189 | false |
| world-ccw-line-sq-adv-yaw | classical | 20/20 | 0.98907 | 0.887389 | 0.999976 | false |
| world-ccw-line-sq-adv-yaw | random | 0/20 | 0.011146 | 2.3e-05 | 0.117091 | false |
| world-ccw-line-sq-adv-yaw | learned | 20/20 | 0.988782 | 0.88653 | 0.999976 | false |
| world-cw-line-sq-adv-align | classical | 20/20 | 0.988623 | 0.882204 | 0.999978 | false |
| world-cw-line-sq-adv-align | random | 0/20 | 0.011401 | 2.5e-05 | 0.116938 | false |
| world-cw-line-sq-adv-align | learned | 0/20 | 0.011137 | 2.8e-05 | 0.113665 | false |

Each draw combines a Jeffreys-posterior sim rate with independent bootstrapped E03 drift/spin samples. The empirical samples are few and are not a validated error distribution; percentiles do not include sensing, placement, model or full-route exposure uncertainty. Source commits and all source-seal hashes are in the manifest.

Provisional grid maxima: |drift| 2.17185e-15 mm; |spin error| 2.29 deg. The symmetric plant's near-zero lateral drift is a model limitation. No fragile flags under this input is not evidence that the physical robot is robust.
