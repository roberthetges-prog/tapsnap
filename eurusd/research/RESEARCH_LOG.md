# Research log (continuous loop)

Mandate (owner, 2026-11-11): run autonomously, keep opening new avenues, stop only when told. Target: the highest
honest out-of-sample predictability for EUR/USD. Rules that never bend: the fixed walk-forward protocol
(`experiments/HOWTO_ARMS.md`), leak checks on every arm, every trial counted (below) and deflated, nothing goes live
without passing; survivors enter the paper forward test as NEW named scenarios starting from zero.

## Trial count (for deflation)
| Round | What | Variants tried | Survivors |
|---|---|---|---|
| 1 | 102 practitioner strategies, 51 academic hypotheses, 19 indicator families (train/validate/holdout) | ~290 | 0 stand-alone; 3 weak components |
| 2 | daily ML, intraday ML, weak-signal combination, regimes/trend, events (walk-forward 2010-2026) | 137 | weak-signal combination + positioning trend -> live exposure (Sharpe 0.56 / 0.64 / 0.36) |
| 3 | rate expectations & stress (12), deep positioning (12), macro surprises (12), G10 positioning (pending) | 36+ | none so far |

## What is established
* Predictable: slow macro drift and speculative positioning (direction, weakly); volatility and range (strongly).
* Not predictable after costs: technical patterns, intraday direction, event reactions, regimes, non-linear ML on
  the same features, rate-futures and stress measures, macro surprise indices, finer positioning structure.
* Positioning: the level is the signal; no trader group is specially informed; robust to z-window and to delays.
* A six-month record cannot separate skill from luck (see reports/scenario_replay.md).

## Avenue queue
Round 4 (launched 2026-11-11): volatility-conditioned intraday tactics; intraday-path signals from 1-minute data
(signed jumps, semivariance, skew); FX relative value (EUR/USD vs a basket of dollar pairs); equity-conditioned
month-end / fix / calendar flows. Lead: prediction scoreboard (direction, range, cone calibration).
Later: weekly-horizon ensembles of survivors; implied volatility and options positioning (needs a data host);
news / central-bank text tone (needs a data host); cross-currency portfolio if G10 positioning validates.
