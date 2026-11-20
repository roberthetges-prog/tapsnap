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

| 7 | official and portfolio flows (12): FAILS; options information (12): FAILS; text, news, uncertainty, policy surprises (12): FAILS | 36 | none so far |

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
* Options market (25-delta risk reversals 2003-2026, implied vol / VRP / term structure, CFTC options-only positioning):
  skew REACTS to spot (corr +0.45 with the trailing month; look-ahead copy scores 68 %); followed 53-55 %, 'fade extreme
  skew' 37 % (wrong way); VRP, slope, option positioning independent but empty (47-55 %); extra vote fails (no gain at
  21 sessions, stale copy gains more at 42); no replication on USD/JPY or EUR/JPY. Unadjusted lead only: agreement calls
  the skew contradicts are right ~50 % vs 62 % confirmed (weekly grid, 21 sessions, 66 correlated tests).
* Text and news (Fed / ECB tone from 4,900 statements, minutes and speeches; SF Fed news sentiment; policy and
  geopolitical uncertainty; Jarocinski-Karadi policy and information shocks): new information (0-13 % explained by the old
  inputs) but uninformative: tone 49-57 %, sentiment 48-52 %, uncertainty 41-57 %, pure policy surprises 46-54 %; extra
  vote fails; stale copies do as well. One lead (6-month information shocks: 60-66 % since 2016, 45 % in 2010-15) for a
  forward test only; its data end 2025-10.
* Positioning: the level is the signal; no trader group is specially informed; robust to z-window and to delays.
* A six-month record cannot separate skill from luck (see reports/scenario_replay.md).
* **Positioning does not replicate (reports/arm_g10_positioning.md).** The identical rule on GBP, JPY, CHF, AUD, CAD, NZD,
  MXN gives a basket Sharpe of -0.38 / -0.58 / -0.62; EUR ranks 1 of 8. The live positioning stream therefore rests on
  the pair it was mined on. Planning Sharpe for it: 0.25-0.45, not 0.6-0.7. Weight kept, not raised.
* Direction accuracy today: 52 % next session, 55 % next week, 58 % next month (2010-26), fading after 2023.
  Range / volatility accuracy: 75 % above/below median, 93 % on volatile-day calls (reports/prediction_scoreboard.md).

## VERDICT AFTER SEVEN ROUNDS (2026-11-12)
About 560 pre-declared trials across every class of public information reachable from here: price at all frequencies,
calendar and flows, events and surprises, rates and curves, positioning in every cut, liquidity, stress, the real economy,
policy cycles and reaction functions, analogs, options, official flows, text and news. Since round 2, some 270 trials have
produced ZERO new survivors, and all four leads that looked promising (order flow, policy-gap gating, positioning on other
currencies, analog unanimity) failed replication or placebo tests.
HIGHEST HONEST PREDICTION NUMBERS:
* Direction, EUR/USD, when positioning, the 2y-spread trend and the macro score agree (about 44 % of the time):
  59 % right at one month, 61-65 % at two months, 67-72 % at a quarter (walk-forward 2010-26, net of costs);
  57-67 % since 2016; unconfirmed since 2023 (too few trades to tell; power analysis says two decades would be needed).
* Path and level events: 69-87 %, calibrated to 1-3 points in every era (stops and targets at known odds).
* Next-session range: 75-78 % above/below normal; 93 % on volatile-day calls.
Planning Sharpe for the directional engine: 0.3-0.5. Higher numbers require a Sharpe near 1 (70 % at a quarter) or 1.7
(80 %), which no public information tested here supports.
What could still move the ceiling: time (the paper forward test, currently paused by the owner), data that is paid or
blocked (live options skew, OIS curves, CLS flow, real-time vintages), and the two forward-only leads (information
shocks; skew-contradicted calls). More mining of the same public data would now mostly manufacture false positives.

## Round 8 (2026-11-17): the committee of 100 analysts (owner's idea) - 1 trial
Owner asked for 100 independent agents that each give a direction and a probability, with the vote as the recommendation.
Built as 50 views of the evidence in 10 schools x 2 temperaments (prior-following on all history; prior-free on the last
ten years), yearly walk-forward, design / majority classes / keep bar written into `src/eurusd/committee.py` before the
first run. Test `experiments/70_committee.py`, report `reports/committee.md`.
* A clear majority (>= 65 % of the analysts with a view, at least 20 voting) was right 59.6 % at one month, 63.8 % at two,
  64.7 % at three (2010-26; 112 / 47 / 31 independent calls); 56 / 60 / 65 % since 2016; 46 / 44 / 43 % since 2023.
* Same as the three-signal agreement rule on the same folds (58.3 / 63.3 / 66.7 %): gain +1.3 and +0.6 points 2010-26,
  -1.7 and -2.1 since 2016. **Bar missed (FAIL)**: the committee is the agreement rule in another costume, because the
  only analysts with a real record are the positioning and macro-score ones already in the rule.
* The size of the majority does NOT sort the outcomes: 80 %+ majorities were right 57 % at one month, 65-80 % majorities
  61 %. '85 of 100' is not more reliable than '70 of 100'; the analysts are correlated, so the share is not a probability.
* A 63-session-stale vote still scores 57-59 %, a 126-session-stale one 51 %: it is a slow regime read.
* Null machine (labels shifted by years): 43-58 %. The noise band is about +-8 points on these call counts.
* Look-ahead control clean (0 of 48 columns differ on a truncated frame); future-label test in `experiments/test_committee.py`.
Decision: kept as a READ-OUT only (`cli committee`, one line in the weekly outlook), labelled with the hit rate each
majority class actually had; it decides nothing and the position call still follows the agreement rule.
Also fixed: the live price splice fetched only 5 days, leaving holes after a pause longer than that; it now covers the gap.

### Round 8, trial 2 (2026-11-17): Fed desk added to the committee (owner's request)
Five Fed-meeting views x 2 temperaments = 10 analysts (latest decision, direction of the last move, 2-year yield reaction
on decision day, EUR/USD reaction on decision day, what the 2-year prices against the policy rate), each state held from
the statement until the next meeting; declared in the module before running, nothing else changed.
* The committee with the Fed desk: 59.0 / 63.1 / 63.6 % at 1 / 2 / 3 months (2010-26), without it 59.6 / 63.8 / 64.7 %.
  No gain; bar still missed.
* The Fed desk alone (majority of its analysts with a view): right 42.5 % at one month, 43.8 % at two, 49.4 % at three
  (59 / 72 / 56 independent calls). The textbook reading ('a hike lifts the dollar') was wrong more often than right
  after the decision, consistent with round 5: the move is priced before the meeting. Not significant as a contrarian
  rule either (95 % range at one month about 31-55 %).
* Most Fed analysts stay silent most of the time because their own history gives them no edge (the design silences them).
Decision: Fed desk kept in the read-out because the owner asked for it (it shows the last decision, the market reaction,
what is priced and the next meeting date); it does not improve the probability. The headline now reads
'direction, probability', the probability being the pooled walk-forward hit rate of clear-or-strong majorities.
Also added: `committee.refresh_fed_target()` (the mirror's Fed target series was two months stale; FRED answers directly).

### Round 8, trials 3-10 (2026-11-17): weighting the analysts (owner's idea: weight each input by importance, e.g. the
### Fed in a Fed-meeting week, and by whether a known pattern is repeating)
Eight schemes against the equal vote, call rule and selection rule declared in `experiments/71_committee_weights.py`
before running; pick on 2010-17, confirmation on 2018-26. Report `reports/committee_weights.md`.
Accuracy at 1 / 2 months, 2010-26 (equal vote 59.0 / 63.1):
* track record (mute analysts with a bad past) 58.8 / 58.8; track x conviction 59.6 / 58.7
* own conviction (weight = distance of the analyst's probability from 50 %) 60.9 / 63.9
* equal weight per school 59.2 / 59.6
* event week (x3 for Fed desk, central banks and rates in a Fed or ECB week; x3 economy before payrolls / CPI) 59.0 / 61.7;
  on Fed-week sessions alone 57.9 vs 58.0 for the equal vote: the Fed week does not make the Fed analysts more right
* pattern (weight = who was right in the 250 most similar past vote patterns) 58.6 / 59.2
* learned ridge weights 58.8 / 54.9; pattern replay (what followed the 250 most similar patterns) 61.5 / 51.6 on 2.9 and
  2.2 calls a year (too few; 45.6 % at two months in 2010-17)
Pick by the rule: own conviction (2010-17 score 65.2 vs 64.7). Confirmation 2018-26: +1.9 points at one month, +1.1 at two.
Bar (+2 at both) missed, so THE EQUAL VOTE STAYS. Conviction weighting is the only scheme not worse in any cell and makes
slightly more calls; it is shown as a second line in the read-out, labelled not proven better.
Why nothing beats equal weights: with roughly 110 independent one-month outcomes since 2010, any weight estimated from
the record is mostly noise (the classic forecast-combination result). Round 8 total: 10 trials, no new survivor.

## Round 9 (opened 2026-11-17; owner switched the research loop back on)
No new predictors of 2010-2026 (see the verdict above). Three arms whose answer is useful either way, protocol in the
Round 9 addendum of `experiments/HOWTO_ARMS.md`:
* AA `pre_euro`: the positioning rule and the agreement rule on the Deutsche Mark, 1986-1998 (CFTC history before 1999,
  never used here). Out-of-time replication: it either supports the planning Sharpe or lowers it.
* AB `trade_design`: take-profit / stop / time-limit designs for agreement-rule calls with a stated win probability,
  against a random-entry baseline that shows how much of the win rate is barrier geometry.
* AC `leg_decomposition`: euro leg or dollar leg? The slow signals on EUR vs a basket and USD vs a basket; does hedging
  the unpredicted leg raise accuracy?
Status: COMPLETE (2026-11-17). 24 candidates (AA 6, AB 12, AC 6), no survivor; one finding that lowers the planning figures.

**AA `pre_euro` (6 candidates, 12 declared evaluations, 3 post-hoc checks): CLEAN FAIL (reports/arm_pre_euro.md).**
The identical positioning rule on Deutsche Mark futures (CFTC history from 1986, never used before), scored on the
synthetic euro, 1987-02 to 1998-12:
* right 47.6 / 47.5 / 45.0 % at 21 / 42 / 63 sessions (141 / 70 / 46 independent decisions; random timing 49.7 %);
  daily-stream Sharpe +0.03 (t 0.1). The agreement-style rule rebuilt for that era: 48.3 / 45.2 / 42.0 %.
* JPY, GBP, CHF, CAD futures in the same years: 47-52 %; nothing.
* Not an artefact: one more week of delay, an optimistic lag, an independent month-end price, and an independent
  re-computation all give 46-51 %; a copy that knows each report 30 days early scores 74 %, so the pipeline would have
  found information had there been any; the stand-in inputs keep the full record when applied to EUR/USD 2010-26.
* Pooled Sharpe of the positioning stream OUTSIDE the 2003-22 window it was selected on (mark 1987-98, EUR/USD 2000-02
  and 2023-26; 18.7 years): +0.10 (t 0.4; 95 % range -0.35 to +0.55). Inside the window: +0.64.
**CONSEQUENCE (supersedes the planning figures above).** The positioning effect now rests on EUR/USD 2003-2022 alone:
it failed on seven other currencies (round 3) and on the euro's own predecessor (this arm), and it is unconfirmed since
2023. Planning Sharpe for positioning-driven calls: 0.1-0.3 (centre 0.2), i.e. about 52 / 53 / 54 % at 1 / 2 / 3 months,
not 58-63 %. The agreement rule's 59 / 63 / 67 % and the committee's 59 / 63 / 64 % are IN-SAMPLE descriptions of
2010-26 with no out-of-time support and must be quoted that way. The paper forward test is now the only way left to
find out whether anything is there.

**AB `trade_design` (12 candidates): FAILS the bar (reports/arm_trade_design.md).** Agreement-rule calls with take-profit /
stop / time-limit barriers resolved on hourly bars, against the same barriers on random dates and directions.
* The pick by the declared rule (take-profit 3 ATR, stop 4 ATR, 42 sessions) won 63.2 % on 76 unseen trades in 2018-26,
  +50 pips a trade; random entry with the same barriers wins 54.2 %, inside the interval (51.9-73.1); the plain 42-session
  hold earned +87 pips a trade. 0 of 10 barrier designs pass.
* A 70-78 % win rate IS available and its stated probability holds (take-profit 1 ATR, stop 3 ATR, 21 sessions: stated
  76.9 %, realised 77.4 % in 2018-26), but random entries win 71.8 % with the same barriers: about 5 points are edge, the
  rest is geometry, and the average loss is 2.3 times the average win.
* The rule's edge is +6 to +10 win-rate points over the random-entry baseline whatever the barriers (2010-26); +2.5 to +9
  in 2018-26; -2 to +7 in 2023-26. Barriers move the baseline (40-72 %), not the edge.
* No barrier design earns more pips a year than the plain hold (2018-26: holds +497 / +451, barrier designs +250 to +434).
  A stop only caps the single worst trade (-1,227 pips on the 42-session hold).
* A 63-session-stale signal through the chosen design still wins 61 % but earns +25 instead of +65 pips a trade.
Decision: nothing changes in the product. A trade ticket may quote a win probability only together with its random-entry
baseline (e.g. 'wins about 64 %; 54 of that is what these barriers give anyone; the call adds about 9 points').

**AC `leg_decomposition` (6 candidates): FAILS (reports/arm_leg_decomposition.md).** EUR/USD split into the euro against a
basket (JPY, GBP, CHF, CAD, AUD) and the dollar against the same basket, on Fed H.10 fixings.
* The agreement calls expressed on the euro leg are 5.5-8 points LESS accurate than on plain EUR/USD (21 sessions: 53.2 vs
  59.2 % in 2010-26, interval -11.2 .. -1.0); Sharpe 0.22 / -0.20 after the six spreads of the hedge against 0.66 / 0.47.
* Neither a euro nor a dollar signal: 2010-15 the euro leg earned two thirds of the P&L, 2016-26 the dollar leg nearly all
  of it; positioning alone calls both legs about 55 %. The legs are almost uncorrelated, so the pair collects whichever is
  working and a hedge removes edge with the noise. ECB weights, Fed weights and a seven-currency basket say the same.
Decision: keep expressing calls on plain EUR/USD.

## Round 10 (opened 2026-11-17): do the RELIABLE parts hold elsewhere?
After round 9 the directional edge has no out-of-time support, while two things have been stable in every era on EUR/USD:
the next-session range forecast (75-78 % above/below median; 80 % band) and the level / no-touch odds (2 ATR and 3 ATR
away untouched within 10 sessions 69 % / 87 %; within 21 sessions 52 % / 71 %). Neither was ever tested off EUR/USD.
* BA `reliable_parts`: the same range model and the same level odds, frozen, on six other dollar pairs (GBP, JPY, CHF,
  CAD, AUD, NZD). If they hold, the stop / target / sizing layer of the product is structural; if not, it too is
  EUR/USD-specific and must be labelled so.
Status: COMPLETE (2026-11-17). 11 candidates.
**BA `reliable_parts`: both declared bars missed, for different reasons (reports/arm_reliable_parts.md).**
* LEVEL ODDS replicate almost exactly: on GBP, JPY, AUD, CHF, CAD, NZD a level 2 ATR / 3 ATR away is untouched within
  10 sessions 68.3-68.9 % / 84.8-87.6 % and within 21 sessions 50.9-52.2 % / 69.5-71.5 % (EUR/USD 69 / 87 / 52 / 71);
  24 of 24 cells within 2.2 points. The stability clause failed in 3 of 24 cells, but a stationary driftless surrogate
  fails it as often, so that clause carried no information (reported as declared, not redrawn).
* They are ARITHMETIC, not prediction: the driftless-Brownian formula 2*Phi(k*1.596/sqrt(h)) - 1 gives 68.7 / 87.0 /
  51.4 / 70.4 with no data. The only empirical content is that ATR14 measures the next 10-21 sessions' volatility.
* RANGE FORECAST: the model form transfers (edge over 'same as yesterday' +4.4 to +7.9 points on every pair, 80 % band
  covers 77-82 % everywhere, frozen EUR coefficients within a point of each pair's own fit) but the headline '75-78 %'
  is EUR/USD-specific: 66-74 % elsewhere (1 of 6 pairs within 4 points), 'volatile-day' call 84-93 % elsewhere. Reason
  (post hoc): EUR/USD's volatility wandered further from its year-ago median, which makes the class easier. Against a
  stronger baseline (21-session mean range above the median) the regression adds only 1-2 points, on EUR/USD too.
Decision: quote level odds as the arithmetic of a driftless market at today's volatility (valid on any liquid dollar
pair), never as an edge; label the 75-78 % and 93 % range figures as EUR/USD-only. What the product can rely on is the
volatility estimate, nothing more.

## Round 11 (opened 2026-11-17): sharper levels
* CA `sharper_levels`: at the same 80 % holding rate, how narrow can the lower / upper levels be made, and can they be
  made to hold evenly in calm and volatile markets, around events and in trending years? Candidates are volatility
  estimates and calibration methods only; chosen on 2010-17, confirmed on 2018-26 and on six other pairs untouched.
Status: COMPLETE (2026-11-17). 12 candidates. **FAILS the bar (reports/arm_sharper_levels.md).**
* No method is narrower at the same 80 % reliability in 2018-26. The pick (HAR regression on daily-return volatility) scores
  -0.2 % / -1.3 % / +0.2 % against the bots at 5 / 21 / 63 sessions, no interval excludes zero, and it is 2-10 % wider.
  0 of 11 candidates pass. Levels without volatility scaling are 11-19 % worse, so the bots' scaling is doing the work.
* Evenness is real: regression levels halve the spread of the holding rate across volatility terciles (9.1 -> 4.7 points;
  6 of 6 other pairs), by being wider in calm markets and narrower in volatile ones (elasticity to today's volatility
  0.84 / 0.73 / 0.60 rather than the bots' 1.0). Small pooled score gain on six pairs (2-4 %), post hoc.
* The bots' levels hold about 75 % in quiet markets and 85 % in volatile ones, and one-week levels hold 2-8 points less
  often in weeks with FOMC, ECB, payrolls or CPI. Adaptive widening after misses makes every score worse.
Decision: the bots' median level stays. The two caveats are printed with the vote.

## Round 12 (opened 2026-11-17; owner: 'can we expand the bots' experience')
* DA `bots_experience`: the same 100 seeded bots on evidence that exists for every dollar pair and back to the 1980s,
  trained (a) on EUR/USD 1999+ only, (b) plus the Deutsche Mark era, (c) plus six other dollar pairs, (d) both; all
  scored on EUR/USD 2010-26. Adopted only if the vote is at least 2 points better at 21 and 63 sessions in 2018-26.
Status: COMPLETE (2026-11-17). 3 candidates. **NOT ADOPTED (reports/arm_bots_experience.md).**
* More years (mark era 1987-98): +0.1 / +0.2 points at 21 / 63 sessions in 2018-26 (intervals include zero). 72 of the 100
  bots have a 5- or 10-year memory and are unchanged by construction; the 28 all-history bots are slightly worse.
* More markets (six other dollar pairs pooled): -8.3 / -9.2 points (45.0 / 46.5 % on 2010-26 against 52.9 / 53.9 %). The
  bots drop positioning (26 % -> 5 % of kept columns) for global columns shared by all pairs (18 % -> 37 %), become more
  alike (correlation of being right 0.22 -> 0.28) and the pooled vote scores 48-52 % on every other pair.
* The generic evidence set alone costs nothing (52.9 / 53.9 % against the product's 52.0 / 53.2 %). Noise floor about 4 points.
Decision: `bots.py` unchanged.

RESEARCH LOOP STOPPED by the owner on 2026-11-17 (weekly usage). Heartbeat disabled; the paper forward test and alerts
continue. About 650 trials in twelve rounds; no survivor since round 2, and that one has no out-of-time support.

## Round 13 (2026-11-17; owner: one more study only, then stop)
* EA `levels_confirm`: the two round-11 leads on the levels (evener width; event-week adjustment), frozen exactly as
  round 11 left them, on markets never scored in this project. Adopted into `bots.py` only if both the declared score
  and the evenness improve there.
Status: COMPLETE (2026-11-18). 2 candidates. (Owner, same evening: continue the research loop; heartbeat re-enabled.)
**K1 (har_d) NOT confirmed; K2 (hourly-volatility HAR with event adjustment) CONFIRMED by the declared bar, thinly
(reports/arm_levels_confirm.md).** Six never-scored markets from HistData 1-minute bars (EUR/GBP, EUR/JPY, EUR/CHF,
USD/SEK, USD/NOK, EUR/AUD as declared reserve; gold dropped by the declared data-quality rule), pooled 2010-26:
* K2 score vs the bots -2.1 % / -2.4 % / -3.8 % at 5 / 21 / 63 sessions, all three intervals excluding zero (the 21- and
  63-session ones barely: upper bounds -0.07 % and -0.11 %, not robust to block length, seeds or leaving out one market);
  tercile spread of the holding rate smaller on 6 of 6 markets (about halved); levels hold 78-82 %; the one-week
  event-week shortfall falls from 2.5 to 0.4 points. The 5-session gain, the evenness and the event repair are solid.
* It did not pass on EUR/USD itself in round 11.
Decision: K2 is printed with the vote as a second opinion for 5 and 21 sessions (the event calendar in the repo ends in
December 2026, too short for 63); the bots' levels remain the product. OWNER'S DECISION 2026-11-18: make the switch
anyway: K2's levels are the published ones at 5 and 21 sessions, the bots' levels are printed beside them and stay the
published ones at 63 sessions until the event calendar is extended. First survivor since round 2, and it concerns
levels, not direction.

## Round 14 (2026-11-18): the wide band - 1 trial, PASSES
`experiments/73_joint_band.py` (declared in its docstring). The two levels each hold ~80 % but both together ~60 %.
Stretching both of the bots' median levels by one walk-forward factor (about 1.33 / 1.37 / 1.34 at 5 / 21 / 63 sessions)
gives a band that contained the whole period's price action 80.0 / 81.1 / 79.5 % of the time in 2010-26, 80-82 % in
2016-26 and 81-82 % in 2023-26 (target 80, bar +-4). Printed with the vote as the 'wide band'.

## Heartbeat 2026-11-18 12:06: no arm running; no new round opened this cycle
The published levels (K2) count scheduled ECB and US releases inside the window, and the repo's calendars end in
December 2026; the official 2027 calendars are on www.ecb.europa.eu and www.bls.gov, which the network policy blocks
(a request to add the hosts was put to the owner at 06:06 and not answered). Fix made: the vote now falls back to the
bots' levels for any horizon whose window runs past the calendars, and says so. Once the 2027 calendars are in
`data/macro/ecb_decisions.csv` and `us_bls_releases.csv`, all three horizons use K2 automatically.

## Round 15 (2026-11-18 18:06 heartbeat): an even wide band - 1 trial, misses the bar by 0.1 point
`experiments/74_even_band.py` (declared in its docstring). The round-14 band holds 80 % overall but 77 % in calm markets
and 84-92 % in volatile ones (spread 7 points at 5 and 21 sessions, 17 at 63), and 77-80 % in event weeks vs 82-84 %
otherwise. Candidate: the stretch factor chosen per volatility tercile (same walk-forward rule). Result 2010-26 /
2018-26: spread falls to 1.5 / 1.8 points (5 sessions), 3.4 / 2.5 (21), 7.3 / 3.3 (63); every tercile cell at 5 and 21
sessions is 80.7-84.1 %, one cell (normal tercile, 21 sessions, 2010-26: 84.1 %) is 0.1 point outside the declared +-4
band, so FAIL by the letter; the band is 1-2 % wider and holds 82 % overall. Not adopted on my own; the owner may switch.

## Round 16 (2026-11-19 00:06 heartbeat): the wide band at 90 and 95 % - 1 trial, PASSES at 5 and 21 sessions, FAILS at 63
`experiments/75_band_confidence.py` (declared). Joint holding 2010-26 / 2018-26: 90 % target -> 89.5 / 89.7 (5 sessions),
90.7 / 90.4 (21), 91.7 / 93.9 (63); 95 % target -> 94.4 / 94.4, 95.2 / 95.2, 97.3 / 99.0. Within the declared 3 points
at 5 and 21 sessions; too wide at 63 (the 2008-12 years in the training window stretch the factor). Worst single year
at 21 sessions: 63 % (80 % band), 76 % (90), 86 % (95). Adopted: the 90 and 95 % bands are printed with the vote for
one week and one month ('rarely breached'); not for three months.

## Round 17 (2026-11-19 06:06 heartbeat): 10-year window for the band factor - 1 trial, FAILS
`experiments/76_band_window.py` (declared). At 63 sessions the 90 / 95 % bands still over-hold: 91.6 / 96.7 % in
2010-26 and 93.3 / 97.9 % in 2018-26 (bar: within 3 points). The excess is not the 2008-12 window: with only 68 / 35
independent three-month periods a 5 % tail cannot be calibrated at all. 5 / 21 sessions unchanged. Nothing adopted;
the 90 / 95 % bands stay published for one week and one month only.

## Round 18 (2026-11-19 12:06 heartbeat): is the band breached evenly on both sides? - 1 trial, FAILS
`experiments/77_band_sides.py` (declared). The single-factor band is already near-even: breaches below / above 10.7 /
9.4 % (5 sessions), 11.2 / 7.9 (21), 11.8 / 9.1 (63) in 2010-26, and 10.1 / 9.6, 10.1 / 9.2, 8.2 / 11.1 in 2018-26: the
side that is breached more flips between eras. A factor per side (each side breached 10 % in training) over-corrects:
in 2018-26 breaches 8.3 / 10.7 (21 sessions) and 5.1 / 15.0 (63), outside the declared 2-point evenness, because the
asymmetry learned from 2008-17 (euro falling) reversed afterwards. Nothing adopted; the band stays symmetric. The lesson
is the same as for direction: whichever side history favoured does not persist.

## Round 19 (2026-11-19 18:06 heartbeat): levels at 10 and 42 sessions - 1 trial, FAILS by the letter
`experiments/78_levels_10_42.py` (declared). Same bots, nothing re-tuned. 10 sessions: lower / upper held 79.3 / 81.4
(2010-26), 81.4 / 80.1 (2016-26), 84.2 / 79.8 (2023-26: 0.2 point outside the +-4 band on 99 periods). 42 sessions:
77.4 / 82.1, 80.7 / 78.5, 85.0 / 74.3 (2023-26, 23 periods: outside). The wide band holds 79.6-82.2 % at both horizons
in every era. So two-week levels are as good as the published ones within noise; two-month levels drift in the small
recent sample, as the 63-session ones do. Not added to the product (the bar was missed); the owner can ask for the
two-week horizon.

## 2026-11-19: two-week horizon added to the vote (owner's decision after round 19)
`HORIZONS = (5, 10, 21, 63)` in `bots.py` and `sharper_levels.py`; records, levels, wide band and 90 / 95 % bands rebuilt
for all four horizons (72, 73, 75). The two-week direction vote is as uninformative as the others; its levels hold about
80 % and its band about 80 %.

## Round 20 (2026-11-20 00:06 heartbeat): touch odds for any level - 1 trial, PASSES
`experiments/79_touch_odds.py` (declared). Walk-forward touch frequency by distance (0.25-3.0 median-gauge units) at
5 / 10 / 21 sessions: stated vs realised within 0.7 / 1.0 / 1.0 points at every distance in 2010-26 and 2018-26, within
1.7 since 2023 (bar 4). The empirical table has fatter tails than the driftless-Brownian formula (6.6 % vs 4.6 % at 2
units, 21 sessions), so the table is used, not the formula. Adopted as `cli touch <level>`: the odds that a user's
stop or target is touched within one week, two weeks or one month. Arithmetic of volatility, not direction.

## The vote: 100 self-researching bots, direction and levels (owner's design, 2026-11-17) - 2 trials
Owner: no entries; just direction by a vote of 100 differently trained agents that do their own research, plus a lower
and an upper level. Built as `src/eurusd/bots.py` (design in its docstring before the first run; a bot is its seed: a
desk of 12 of 74 evidence columns, its own research rule, learner, memory and volatility gauge; every bot must vote).
Test `experiments/72_bots.py`, report `reports/bots.md`, command `cli vote`.
* DIRECTION: the majority was right 50.3 / 52.0 / 53.2 % at 5 / 21 / 63 sessions (2010-26; 856 / 202 / 67 independent
  votes), 48.6 / 50.3 / 56.1 % since 2016, 48.5 / 47.0 / 56.1 % since 2023. A bigger majority is no more reliable
  (21 sessions: thin 51.5, fair 49.7, wide 53.6, very wide 55.9 %). The count is not a probability: when 60-69 bots
  voted UP the pair rose 37 % of the time at 21 sessions. Median single bot 50-52 %; bots' votes correlate 0.13-0.17.
* Why below the hand-built committee's 59 %: the committee's analysts were chosen with hindsight (house signs); bots
  that must find their evidence themselves have none. 52 % is the honest size and matches the out-of-time planning
  figure from round 9.
* Track-record weights: +3.7 / +1.8 points in 2010-17 but -1.3 / -1.9 in 2018-26. Equal vote stays.
* LEVELS (each bot scales the lowest low / highest high of its memory by its own volatility gauge; median of 100):
  the lower level held 79.1 / 78.0 / 78.0 % and the upper 80.7 / 82.1 / 82.3 % at 5 / 21 / 63 sessions (target 80 %),
  within 4 points in every era except 63 sessions since 2023 (89 / 74 % on 15 independent periods). Both held about
  60 %. Levels that ignore current volatility are 12-18 % wider and hold 92 % in calm markets but 80 % in volatile
  ones. In the worst single year a level held only 58-70 % (21 sessions) and 33-39 % (63 sessions): a trending year.
Decision: `cli vote` is the product read-out the owner asked for; it prints the count next to its measured worth and
the levels next to theirs. The weekly outlook carries the vote line instead of the committee line.

## Product definition (owner, 2026-11-17, supersedes the next section where they differ)
No entries, no take-profit, no stop. Output = direction (the vote count of 100 bots) and a lower and an upper level,
for one week, one month and three months.

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
