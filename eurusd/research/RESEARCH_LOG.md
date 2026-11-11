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
| 3 | rate expectations & stress (12), deep positioning (12), macro surprises (12), G10 positioning (10) | 46 | none added. Rates/stress: spread trend re-expressed, +0.03 Sharpe = noise. Deep positioning: crude rule not improved (placebo matched). Macro surprises: not timing-dependent, cannot run live. G10: effect does NOT replicate outside EUR |

| 4 | vol-conditioned intraday tactics (12), FX relative value (12, strict count 24), flows & calendar (12), intraday path from M1 (22), selective + swing + OFI replication pending | 70+ | vol tactics: none; range forecast kept for stop/target placement (78 % above/below-median accuracy; oracle ceiling for intraday tactics ~0.8-1.1 Sharpe) |

## What is established
* Predictable: slow macro drift and speculative positioning (direction, weakly); volatility and range (strongly).
* Not predictable after costs: technical patterns, intraday direction, event reactions, regimes, non-linear ML on
  the same features, rate-futures and stress measures, macro surprise indices, finer positioning structure.
* FX relative value (EUR/USD vs 8 dollar pairs: residual reversion, dollar trend, lead-lag, dispersion, PCA): nothing; hit rates 48-51 %.
* Yahoo daily FX bars changed stamp convention in 2010 Q3 (end-of-day -> start-of-day); never join them same-day. Fed H.10 = 12:00 NY, verified to 1 pip.
* Flows & calendar: equity-conditioned month-end rebalancing, IMM rolls, holidays, blackout windows: nothing.
  Month-end fix continuation (follow 15:00-15:45 London into the 16:00 fix, last business day) is real: +3.1 bp gross,
  t 3.4, all eras positive, hit 54-59 %, ~12 a year, break-even ~3.4 pips. A 15-minute side tactic, not the product.
* Seasonality: December long is supported in every era; May short was 2010-15 luck. The live `season` input's honest
  record is ~0.3 Sharpe since 2016. Candidate scenario for later: December-only season.
* Intraday path features from 1-minute data (signed jumps, realised skew, session shares, efficiency, late-day move,
  order-flow proxy): none robust; most are ret_1d in disguise and flip sign across eras. One post-hoc lead: the 5-day
  order-flow proxy orthogonalised to the day's return (+0.53 / +0.41 / +0.68, 13 of 17 years). Being tested as a single
  pre-registered replication on six other pairs (arm P). The 'fade the last hour' effect is a closing-bid artefact.
* Positioning: the level is the signal; no trader group is specially informed; robust to z-window and to delays.
* A six-month record cannot separate skill from luck (see reports/scenario_replay.md).
* **Positioning does not replicate (reports/arm_g10_positioning.md).** The identical rule on GBP, JPY, CHF, AUD, CAD, NZD,
  MXN gives a basket Sharpe of -0.38 / -0.58 / -0.62; EUR ranks 1 of 8. The live positioning stream therefore rests on
  the pair it was mined on. Planning Sharpe for it: 0.25-0.45, not 0.6-0.7. Weight kept, not raised.
* Direction accuracy today: 52 % next session, 55 % next week, 58 % next month (2010-26), fading after 2023.
  Range / volatility accuracy: 75 % above/below median, 93 % on volatile-day calls (reports/prediction_scoreboard.md).

## Product definition (owner, 2026-11-11)
Directional POSITION trading: hold for weeks up to a month or more, a few decisions a month, each with a calibrated
probability; act when P >= 60 % (target band 60-80 %). Not day trading. Backtesting on history is the research engine;
the paper forward test runs in the background as a free cross-check. Intraday findings matter only for stop and
target placement.

## Avenue queue
Round 4 (launched 2026-11-11; plus arm N selective calibrated probabilities and arm O multi-week position trading with 1999+ history, carry cost and weekly-ATR stops): volatility-conditioned intraday tactics; intraday-path signals from 1-minute data
(signed jumps, semivariance, skew); FX relative value (EUR/USD vs a basket of dollar pairs); equity-conditioned
month-end / fix / calendar flows. Lead: prediction scoreboard (direction, range, cone calibration).
Later: weekly-horizon ensembles of survivors; implied volatility and options positioning (needs a data host);
news / central-bank text tone (needs a data host); cross-currency portfolio if G10 positioning validates.
