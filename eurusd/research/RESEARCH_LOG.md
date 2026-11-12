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

| 4 | vol-conditioned intraday tactics (12), FX relative value (12, strict count 24), flows & calendar (12), intraday path from M1 (22), selective probabilities (12), OFI replication (1: FAILS), swing / position trading from 1999 (12 + 14 sensitivities: FAILS) | 109 | none. Agreement rule adopted as the PRODUCT FORM of the existing information (not a new edge) | vol tactics: none; range forecast kept for stop/target placement (78 % above/below-median accuracy; oracle ceiling for intraday tactics ~0.8-1.1 Sharpe) |

| 5 | liquidity & stress (12): FAILS; real economy (12): FAILS; regime dependence (4): no rule adopted, one lead (policy-gap direction); policy cycle / reaction functions (10, strict 15): FAILS | 43 | none so far |

| 6 | policy-divergence replication across G10 (7): FAILS; analog / nearest-neighbour 'history rhymes' forecasting (12, strict 36): FAILS; data scoping (36 sources, no backtest) | 43 | none |

| 7 | official and portfolio flows (12): FAILS ... (options, text/news pending) | 12+ | none so far |

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
  order-flow proxy orthogonalised to the day's return (+0.53 / +0.41 / +0.68, 13 of 17 years). Tested as a single
  pre-registered replication on six other pairs (arm P): FAILS (basket 0.06 / 0.16 / 0.21, pooled t 0.5). Dropped. The 'fade the last hour' effect is a closing-bid artefact.
* **Selective probabilities (reports/arm_selective.md).** Calibrated P>=60 % directional calls do not work (no better than
  chance; logistic model anti-informative at long horizons). Accuracy rises with HOLDING PERIOD: hit = Phi(Sharpe x sqrt(h/252)).
  Agreement rule (positioning, 2y-spread trend, house score all agree; 44 % of the time): 57 / 59 / 65 / 67 % right at
  10 / 21 / 42 / 63 sessions (non-overlapping 56 / 59 / 61 / 72), +46 bp net at 21 sessions; holds 2016-26, unconfirmed
  2023-26 (tiny n). Same information as the live streams (corr 0.63), in position-trade form. 70 % at a quarter would need
  Sharpe ~1.05, 80 % ~1.7.
* Path / level probabilities are real and calibrated to 1-3 points in every era: level 2 ATR away untouched in 10 sessions
  69 %, 3 ATR 87 %; in 21 sessions 52 % / 71 %. No expectancy alone; use for stops and targets.
* **Position trading designed for the horizon (reports/arm_swing.md): fails.** Scorecard / t-stat / logistic models on slow
  predictors (rates, real rates, PPP, trend, positioning, equities, oil, seasonality, carry) with 1999+ history, carry cost
  and weekly-ATR stops: 54 % at month-ends (2006-26), 50 % in 2023-26; probabilities do not sort outcomes (Brier = coin).
  Only positioning (57-60 %), relative equity momentum (57-60 %, fading) and 6-month oil (55-58 %) carry anything; rate
  levels, real rates, PPP, curve, carry, contrarian extremes are at or below 50 %. Stops make no measurable difference;
  carry is worth ~13 pips per month-long trade. The existing exposure read monthly gives 59 % / +58 pips (2010-26),
  49 % in 2023-26.
* HONEST CEILING SO FAR (direction, EUR/USD): ~59 % at one month, 61-65 % at two, 67-72 % at a quarter when the three
  slow signals agree (2010-26); unconfirmed since 2023. Path / level events: 69-87 %, calibrated, stable.
* Liquidity and stress as a 1-3 month vote (relative ECB/Fed balance sheets, M3-M2, excess liquidity, CISS euro-US, HY
  spreads, NFCI): 44-57 %, nothing; as an extra vote it lowers the agreement rule (59 -> 55 % at 21 sessions); the stale
  placebo beats the live signal. 'USD safe haven when stress is high and rising' was right only 41 % of the time.
* Real economy as a 1-3 month vote: Brent 6-month change 55 / 57 / 68 % but its 63-session-stale version does as well
  (regime bet); TTF/Henry Hub gas ratio a weekly-grid lead since 2018 only (one shock, not confirmed non-overlapping);
  OECD CLI, sentiment, trade balance, US real-yield and breakeven changes: 44-53 %. No extra vote passes.
  Blocked sources: OECD SDMX, Eurostat, DBnomics, EIA; FRED's OECD CLI frozen at 2024-01.
* **Why the fade after 2023 (reports/arm_regime_dependence.md): mostly noise.** No component's Sharpe drop is
  distinguishable from a 0.5-Sharpe process (p 0.18-0.48); the 2023-26 sample has 17-50 % power; an 80 %-power test of
  59 % vs 50 % needs ~190 non-overlapping calls (two decades). Positioning's 2010-22 stretch was its best ever (Sharpe
  0.15-0.38 before 2010, 0.73-0.83 in 2010-22, 0.32-0.36 since): plan positioning-driven calls at Sharpe 0.3-0.5.
  Equity momentum shows the mining signature (step down after 2015). One pre-declared regime passes in both halves:
  the agreement rule is right 64 % / 70 % (21 / 42 sessions, 2006-26, n=74/47) when the ECB-Fed policy gap is WIDER
  than six months earlier and 51 % / 49 % otherwise; family-wise p 0.11, so a lead, not a result. 2023-26 was 58 %
  NARROWER sessions. Registered as paper scenario `agreement_wider`.
  **Replication (reports/arm_divergence_g10.md): FAILS.** Rate-differential trend gated by WIDER on eight other currencies:
  pooled t 1.98, placebo p 0.056, all of it from 2000-09 (2010-26: +0.10 vs complement -0.04, p 0.33); the gate sorts trades
  into earn-carry / pay-carry, and spot-only shows nothing. On EUR/USD the contrast also vanishes with interbank instead of
  policy rates. Third EUR-specific artefact; engine stays unconditional; scenario demoted to a control.
* **Central-bank reaction functions (reports/arm_policy_cycle.md): no edge.** Predicting cut / hold / hike from inflation
  and unemployment does not beat persistence (Fed 71 vs 77 %, ECB 80 vs 76 % next meeting; 3-6 months worse) and calls
  almost no turning point. EUR/USD after cycle turns: textbook sign right ~half the time (n 10-17 per cell, 1975-2026);
  the move comes BEFORE the event (EUR/USD fell in 14 of 17 three-month windows before a first Fed hike). 'Economy-implied
  path minus priced path' scores 50 % and is better when stale (regime artefact). Policy state is context only.
* **'History rhymes' analog forecasting (reports/arm_analogs.md): fails.** Nearest-neighbour forecasts from policy, macro,
  market and combined state vectors: 41-56 % at 21-63 sessions; analog probabilities are anti-calibrated ('70-80 % of
  analogs one way' came true 45-49 %); the FARTHEST dates forecast as well as the nearest (no stable state-to-outcome
  mapping); 20 neighbours rest on 4-12 independent episodes. Only positioning and agreement-input states beat chance, and
  less than the plain signs. `explain()` kept as a 'what followed last time' context panel, never as a probability.
* Official and portfolio flows (Fed custody holdings, swap lines, foreign repo pool, ECB BoP portfolio flows, TIC, SPF
  consensus): 40-57 % at 1-3 months; they FOLLOW the exchange rate (custody rises after EUR/USD strength, TIC follows
  dollar weakness, EA flows are coincident); independent of the agreement inputs but uninformative; no extra vote passes.
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
Round 5 (2026-11-11): slow fundamentals not yet used (liquidity and balance sheets, financial stress and credit, energy
terms of trade, growth leading indicators, real yields), judged natively at the 1-3 month horizon as an extra vote;
policy-regime dependence of the surviving signals and the post-2023 fade; central-bank reaction functions (owner's idea):
predict Fed / ECB moves from inflation and unemployment, event-study EUR/USD around every cycle turn, trade the gap
between the economy-implied relative policy path and what 2y yields price (arm T).
Round 6 (2026-11-11): 'history rhymes' analog / nearest-neighbour forecasting on the macro state (owner's intuition);
replication of the policy-divergence lead across G10 pairs (does rate-differential trend following work when the policy
gap is widening?); scoping of data we cannot reach yet (options positioning, OIS, flow, news text).
Round 7 (2026-11-11): NEW INFORMATION found reachable by the scoping pass (research/DATA_SCOPING.md, 36 sources):
options (25-delta risk reversals 2003-2026, implied vol, CFTC options-only positioning); official flows (Fed custody
holdings, foreign repo pool, swap lines; ECB portfolio flows); text and uncertainty (news sentiment, policy uncertainty,
geopolitical risk, central-bank speeches and statements, policy / information shocks).
Later: weekly-horizon ensembles of survivors; implied volatility and options positioning (needs a data host);
news / central-bank text tone (needs a data host); cross-currency portfolio if G10 positioning validates.
