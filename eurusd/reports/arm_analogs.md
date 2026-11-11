# Arm U - analogs: 'history rhymes' nearest-neighbour forecasting of EUR/USD (round 6)

Code `src/eurusd/arms/analogs.py` (`run(cost_pips=1.2)`, `explain(date=None)`; `PYTHONPATH=src python -m eurusd.arms.analogs` runs everything incl. controls and this report in about four minutes on one core; `... analogs report` rebuilds this file; `... analogs explain [date]` prints the analogs of a date). Outputs in `experiments/results/arms/`: `analogs_positions.parquet` (daily weekly-tranche book of the final rule: `pos`, `fwd_bp`, `net_bp`), `analogs_report.csv` (protocol table, 12 candidates, `variant`, `final`), `analogs_accuracy.csv` (every state x k x horizon x metric x mode x period), `analogs_calibration.csv` (reliability tables and the near-unanimous calls), `analogs_votes.csv` (extra-vote tests and the timing placebo), `analogs_bar.csv`, `analogs_paired_bootstrap.csv`, `analogs_controls.csv` (farthest / random / shuffled / look-ahead), `analogs_episodes.csv`, `analogs_candidates.csv`, `analogs_reference_sign_rules.csv`, `analogs_label_corr.csv`, `analogs_incremental.csv`, `analogs_reconciliation.csv`, `analogs_truncation_test.csv`, `analogs_latest.json` (output of `explain()` for the latest session). The module docstring (states, analog rule, 12 candidates, selection rule) was written before the first result.

## Verdict

**The owner's intuition was tested as a proper analog (nearest-neighbour / kernel) forecast and it does not work for EUR/USD. Analog forecasting
does not reach the 60-80 % band at any horizon or decision frequency, its probabilities are not calibrated, and the Round 5 bar is not met by any
of the 12 candidates.** What it does deliver is a transparent piece of context for the weekly outlook (`explain()`), to be shown WITH its record.

1. **"When the economy / rates / markets looked like today" does not predict the next 1-3 months.** Out-of-sample 2010-26, non-overlapping decisions,
   accuracy at 21 / 42 / 63 sessions with k = 20 (n = about 205 / 103 / 69, i.e. 12 / 6 / 4 decisions a year):
   policy / rates state **A 46 / 48 / 57 %**, macro state (inflation, unemployment) **B 51 / 46 / 49 %**, market state **C 48 / 45 / 44 %**, union of
   everything in 4 principal components **E 43 / 46 / 48 %**. With k = 40: A 42 / 54 / 44, B 55 / 56 / 55, C 47 / 47 / 42, E 46 / 46 / 55. On the
   weekly and monthly clocks the same states sit between 41 and 56 %; over 2006-26 between 42 and 58 %. Every 2010-26 Wilson interval of A, B, C, E
   at 21 sessions contains 50 % except A_k40, which lies BELOW it (35-49; E_k20 at 37-50 touches it). Nothing here is distinguishable from a coin.
2. **The only analog states above chance are the two that contain the information we already trade, and the analogs do it worse than the plain sign.**
   Positioning state **D 55 / 56 / 56 %** (k = 40: 53 / 55 / 54); the plain rule sign(cot_z52) on the same evaluator: 58 / 68 / 68 %.
   The three agreement-rule inputs as a state, **F 58 / 59 / 64 %** with k = 20 (52 / 55 / 57 with k = 40); the sign of the house score alone:
   55 / 61 / 64 %, the agreement rule: 59 / 61 / 72 %. Weekly grid: F 55 / 58 / 60 against 59 / 65 / 67 for the agreement rule. So to the question
   "do analogs add anything to plain sign agreement?" the answer is no: nearest neighbours on (positioning, spread trend, house score) recover part of
   the same drift, with more noise and a strong dependence on k.
3. **The analog probability is not calibrated; "70 % of the analogs rose" came true about half the time.** Weekly forecasts 2006-26, k = 20, states
   A, B, C, E pooled: when 70-80 % of the analogs pointed one way that way was right **45 / 47 / 49 %** of the time at 21 / 42 / 63 sessions
   (448 / 656 / 804 forecasts); at >= 80 %: **34 / 55 / 46 %** (29 / 137 / 204). Brier scores 0.252-0.281 against 0.250 for "always 50 %": worse than
   saying 50 % in all 24 A/B/C/E cells. The slope of outcome on stated probability is negative for A (-0.5 to -0.1) and for C in five of six cells; for B
   and E it is about zero with k = 20 (-0.4 to +0.1) and positive with k = 40 (B +0.2 to +0.6, E 0.0 to +0.7), still with Brier scores of 0.252-0.258.
   D and F have a positive slope throughout (D +0.3 to +0.9, F +0.3 to +0.6; calibrated would be 1) and Brier scores of 0.247-0.258, i.e. equal to the coin.
   The kernel-weighted and the episode-level probabilities are no better (section 4).
4. **Near-unanimous analogs are not better calls, and they are rare.** At least 70 % one way happens on 9-20 % of weeks at 21 sessions (16-40 % at 63
   sessions); non-overlapping 2010-26 that is 1.5-6 decisions a year for A-E, right **A 34 / 41 / 41 %, B 49 / 46 / 56 %, C 45 / 37 / 60 %, D 46 / 52 / 51 %,
   E 42 / 45 / 41 %** (n = 25-107 per cell). F: 54 / 60 / 56 % on 8 / 5 / 4 decisions a year. At least 80 % one way: 0-3 % of weeks at 21 sessions,
   under 1.3 decisions a year for A-E with 0-75 % right on 1-20 decisions (nothing can be said); F 53 / 67 / 60 % on about 3 a year.
5. **Why: twenty neighbours are four or five observations, and the neighbourhood carries no stable drift.**
   * Independent episodes behind a k = 20 forecast (analogs within 63 sessions of each other = one episode): macro state B **4.2**, policy state A **4.8**,
     union E 6.1, market C 9.4, positioning D 12.0, F 11.0 (k = 40: 6.3 / 6.1 / 7.6 / 13.0 / 15.9 / 13.5). In 10 % of weeks the macro forecast rests on two
     episodes or fewer. A slow state has visited each neighbourhood only a handful of times since 1999, and the nearest analogs are very often the months just before
     the embargo (today's ten nearest macro analogs: four dates from spring-summer 2026, five from 2007-12..2008-07, one from 2024).
   * Distance does not matter for the new states. Weekly 2006-26, k = 20, 21 / 42 / 63 sessions: A nearest 47 / 49 / 48 %, random dates 50 / 49 / 50,
     FARTHEST dates 51 / 52 / 54; B 51 / 51 / 50 vs 50 / 50 / 52 vs 53 / 50 / 54; C 50 / 47 / 48 vs 50 / 49 / 48 vs 51 / 49 / 47; E 49 / 50 / 55 vs
     50 / 50 / 52 vs 49 / 46 / 43. The method is at best the unconditional coin for these states. It does matter for D (55 / 55 / 57 vs 50 / 50 / 51 random)
     and F (54 / 57 / 60 vs 49 / 48 / 48 random vs 45 / 42 / 39 farthest), which is the known positioning / house-score information.
   * Even hindsight does not help: allowing analogs from the FUTURE (with the 63-session embargo) leaves A, B, C, E at 45-50 % at 21 sessions. The same
     state has been followed by opposite moves in different episodes; there is no stable mapping to find.
6. **Extra vote on the agreement rule: fails for all 12.** Final `F_k20`: gain -2.4 / +6.8 points at 21 / 42 sessions in 2010-26, +0.2 / +9.6 in 2016-26,
   -8.4 / +7.6 in 2023-26 (non-overlapping; weekly paired difference +1.5 [-2.9, +6.1] and -0.1 [-2.3, +2.1]). The candidate closest to the bar is
   `B_k40` (macro state): +4.2 / +8.0 points in 2010-26 and +9.4 / +10.8 in 2016-26, not worse in 2023-26, but on 5.2 / 3.1 decisions a year (under the 6
   required) and with a placebo that keeps +3.3 / +4.4 (2010-26) and +6.7 / +2.6 (2016-26) of the 42-session gain when the call is 63 / 126 sessions stale.
   On the weekly grid its paired difference is +7.2 [+0.6, +14.0] at 21 sessions and -2.9 [-12.2, +4.9] at 42: one of the 24 candidate intervals excludes
   zero upwards and one (`E_k40`, -9.4 [-19.4, -0.1]) downwards, which is what chance produces. Its sibling `B_k20` on the same state loses 2.2 / 0.3 points,
   and B_k40 is long in 71-84 % of its calls. Not a lead. Coverage extension (analog calls when the three old signals disagree): 44-55 % at 21 sessions
   (n = 156-168).
7. **Final by the declared rule: `F_k20`** (highest lower Wilson bound in 2006-15: 61.8 % on 76 decisions, bound 50.6 %; F can only forecast from 2009-11).
   Full record, non-overlapping: 2010-26 **57.8 % [51-64] at 21 sessions (n = 206, 12 a year), 59.2 % [50-68] at 42 (n = 103), 63.8 % [52-74] at 63
   (n = 69)**; 2016-26 53.0 / 53.0 / 65.9 %; 2023-26 50.0 / 47.8 / 73.3 % (n = 46 / 23 / 15). Weekly-tranche book net Sharpe **0.51 / 0.42 / -0.01**
   (2010-26 / 2016-26 / 2023-26), deflated-Sharpe p 0.32, hit rate of active sessions 50.6 %; three-way combination 0.58 / 0.63 / 0.26 against 0.56 / 0.64 / 0.36
   for the two live streams; correlation 0.57 with `regime_trend`. It is the agreement-rule information through a noisier estimator (its sibling with k = 40:
   51.7 % at 21 sessions, Sharpe 0.13), its library scores are in-sample fitted, and it is below the plain rules it was built from. **Round 5 bar: not met
   (0 of 12). Round 3 bar: not met (2023-26 negative, three-way below two-way on 2016-26).** No stream is recommended.
8. Robustness: Mahalanobis distance, the kernel-weighted vote, the library frozen at each year start (strict protocol), the long library with nine extra
   DEM years (A 46 / 47 / 49, B 50 / 52 / 51, C 51 / 51 / 53 % in 2010-26) and the other-era replication on 1997-2005 (A 44 / 56 / 62 on 108 / 55 / 37
   decisions, B 52 / 51 / 51, C 45 / 51 / 41) all give the same picture. Leak checks are clean: shuffled outcomes 48-53 %; removing the embargo lifts every
   state to 56-60 % at 21 sessions and 60-69 % at 63 (as it must); replacing everything after a cut date by noise leaves that year's analogs and
   probabilities unchanged; the agreement rule rebuilt here matches arm N to the decision.

**Answer to the owner.** History does rhyme often enough to be worth LOOKING at, but for EUR/USD the rhyme is not a forecast: with 27 years of euro
history a macro / policy state has four or five independent precedents, the precedents disagree with each other about as often as a coin would, and
"most analogs rose" was right 45-49 % of the time when 70-80 % of them agreed. The honest ceiling stays where the log has it: about 59 % at one month,
61-65 % at two and 67-72 % at a quarter when positioning, the spread trend and the house score agree. Use `explain()` as a "what happened the last times
it looked like this" panel, never as a probability.

## Protocol notes, deviations, additions after the first run

* **Count of trials.** 12 candidates (state x k at 21 sessions) as declared. Strictly counted, 36 state x k x horizon cells of the main method were tabulated,
  plus diagnostics that were never selected from: Mahalanobis (36), kernel (18), long library (18, and 18 on 1997-2005), near-unanimity cells (72). The
  controls (farthest, random, shuffled, look-ahead, frozen, stale) are checks, not variants.
* **Deviation from the yearly protocol, as specified in the brief:** the analog library grows daily (analogs at least 63 sessions before the decision,
  so every 21 / 42 / 63-session outcome is known); only the standardisation, the PCA and the covariance are frozen at 1 January of the decision year.
  The strict version (library frozen at year start minus 63 sessions) is in section 6 and gives the same picture.
* **Proxy.** The euro-area AAA 2y yield starts 2004-09-07; before that state A uses 3m interbank + 0.18 x (German 10y - 3m) from monthly averages with a
  45-day lag, shifted by -0.057 pp (mean gap over the first 250 AAA sessions, RMSE 0.12 pp there). The 63-session change of
  the spread before 2004-09 is therefore coarse. It affects the library of A and E only, not the test dates.
* **Policy gap** = ECB deposit rate minus the Fed target of `policy_state.csv` (midpoint of the range after 2008); the feature store's `policy_diff` uses the
  upper bound, a constant 0.125 pp difference that standardisation removes.
* **State F** uses, for a decision in year Y, house-score weights fitted before Y applied to every session, so the library scores are in-sample fitted
  to next-day returns. This can only flatter F; F still does not beat the plain sign of the house score.
* **Long-library variants** (1990+): Bundesbank / German proxies before the euro (policy phases and key-rate index of arm T, German CPI y/y before HICP
  y/y exists, German unemployment + 1.11 pp before 2000), synthetic DEM euro for the price and the outcomes. Diagnostic only.
* **Added after the first run** (none changes the selection): the table of plain sign rules on the same evaluator (section 3), the by-year record of the
  final, the out-of-sample record inside `explain()`, and the label-correlation table computed on all sessions instead of the weekly grid (on the weekly
  grid one dimension, the 6-month Brent change, showed a +0.10 correlation with the NEXT-session return; on all sessions it is +0.007 and on the other four
  weekly phases -0.06 to +0.02: a sampling accident of that phase before 2010, not a leak).
* **Suspicious / worth knowing.** (a) Non-overlapping cells of 40-70 decisions move by +-10 points with the starting day: e.g. A_k20 at 63 sessions shows 57 %
  non-overlapping and 45 % on the weekly grid in 2010-26. Read the weekly column next to every non-overlapping one. (b) The random control is identical for B
  and E because both have the same eligible sessions and the same seeds. (c) B_k40 looks positive (55-56 %, book Sharpe 0.28 / 0.46 / 0.62) but is long in
  71-84 % of its calls; on the weekly grid 2006-26 it scores 54 / 55 / 54 % against 50 / 50 / 52 for random dates and 54 / 50 / 49 for the farthest
  dates, and its k = 20 sibling is at 46-51 % (2010-26, non-overlapping).
  (d) Macro inputs are latest-vintage (revision risk as in arm T); with a clean negative this cannot matter.
* **Replication (Round 6 lesson).** Other eras: done (1997-2005 with the long library, section 9): chance. Other currency pairs: not done, the repo has no
  policy-state or macro history for other pairs; nothing in the EUR/USD result suggests it would be worth building.

## 1. State vectors and data

Frame: arm O's continuous daily closes (synthetic DEM euro 1975-98, Fed H.10 1999-2002, feature-store sessions 2003-2026-11-06; 13,248 sessions). Main
analog library from 1999-01-04. Every input is what was public the calendar day before the session's closing date.

| state | dimensions | sources and lags | complete from |
|:--|:--|:--|:--|
| A policy / rates (7) | Fed phase, ECB phase (-1 cutting / 0 hold / +1 hiking); ECB deposit - Fed target and its 126-session change; US 2y - Fed target; EA - US 2y spread and its 63-session change | `data/macro/policy_state.csv` (arm T, causal phases; row of closing date - 1); `fred_DGS2`, `ea_aaa_yield_curve.csv` lagged one calendar day; 2y proxy before 2004-09 | 1999-06-29 |
| B macro (8) | US CPI y/y, its 6-month change; euro-area HICP y/y, its 6-month change; US unemployment, 6-month change; euro-area unemployment, 6-month change | `fred_CPIAUCSL`, `fred_UNRATE`, `fred_CP0000EZ19M086NEST`: reference-month end + 21 days (US shutdown months not before 2026-01-31); `ea_unemployment.csv`: + 35 days; older than 150 days = missing | 2000-09-05 |
| C market (7) | EUR/USD 63- and 252-session return; log distance from the 200-session average; percentile of 21-session realised volatility in the trailing 1260 sessions; log VIX; DAX - S&P 500 63-session return; Brent 126-session change | frame closes; `fred_VIXCLS`, `gdaxi_D1`, `spx_D1` + new `analogs_spx_pre2003_D1`, `datahub_brent_daily`: one calendar day | 1999-01-04 |
| D positioning (2) | cot_z52 and its 65-session change | `cot_eurofx_legacy.csv`, report date + 6 days, then one day (identical to the store's `cot_z52`) | 2000-04-04 |
| E union (24 -> 4) | first 4 principal components of A-D, loadings from the training window | as above | 2000-09-05 |
| F agreement inputs (3) | cot_z52, d_spread2y_20, house score | feature store; house weights fitted before the decision year | 2004-10-05 |

New raw data: `data/processed/cross/analogs_spx_pre2003_D1.parquet` - S&P 500 daily closes 1989-01-03 .. 2002-12-31 from the Yahoo chart API (`^GSPC`,
one request with a browser User-Agent, 3,532 rows, same format as `spx_D1.parquet`, whose first close 2003-01-02 it meets exactly); used with a one-calendar-day
lag for the relative equity return of state C before 2003-04.

PCA of state E (loadings fitted before each test year): the first 4 components explain 19, 14, 12, 10 % of the variance of the 24 standardised dimensions in the 2026 window (55 % together).

First session with a forecast (1260 eligible analog sessions): A 2006-01-03, B 2006-01-03, C 2006-01-03, D 2006-01-03, E 2006-01-03, F 2009-11-06 (test years start in 2006; F needs the store's 2y-spread change, which starts 2004-10).

## 2. Reconciliation of the agreement rule with arm N

Rebuilt on this arm's frame and evaluator (2010-26); `n` and accuracy against the published cells of reports/arm_selective.md.

| h   | mode       | n_here   | acc_here   | n_published   | acc_published   |
|:----|:-----------|:---------|:-----------|:--------------|:----------------|
| 21  | weekly     | 387      | 0.5943     | 387           | 0.594           |
| 42  | weekly     | 383      | 0.6475     | 383           | 0.648           |
| 63  | weekly     | 383      | 0.6658     | 383           | 0.666           |
| 21  | nonoverlap | 156      | 0.5897     | 156           | 0.59            |
| 42  | nonoverlap | 89       | 0.6067     | 89            | 0.61            |
| 63  | nonoverlap | 61       | 0.7213     | 61            | 0.72            |

## 3. Standalone accuracy of the analog call sign(P - 0.5)

Accuracy in %, number of decisions in brackets. Main library (1999+), Euclidean distance, plain share of the k analogs. A call is made whenever P is not exactly 0.5 (about 12 non-overlapping 21-session decisions a year, 6 at 42 sessions, 4 at 63).

**Non-overlapping decisions** (greedy stream; 2006-26 from the stream started in 2006, the others from the stream started in 2010)

| rule   | 2006-26 h21   | 2006-26 h42   | 2006-26 h63   | 2010-26 h21   | 2010-26 h42   | 2010-26 h63   | 2016-26 h21   | 2016-26 h42   | 2016-26 h63   | 2023-26 h21   | 2023-26 h42   | 2023-26 h63   |
|:-------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|
| A_k20  | 46.0 (250)    | 50.0 (126)    | 42.4 (85)     | 45.5 (202)    | 48.0 (102)    | 57.4 (68)     | 48.4 (128)    | 46.2 (65)     | 58.1 (43)     | 48.9 (47)     | 36.4 (22)     | 60.0 (15)     |
| A_k40  | 43.5 (255)    | 48.0 (127)    | 47.1 (85)     | 41.7 (206)    | 54.4 (103)    | 43.5 (69)     | 43.2 (132)    | 56.1 (66)     | 45.5 (44)     | 41.3 (46)     | 43.5 (23)     | 46.7 (15)     |
| B_k20  | 51.4 (243)    | 48.4 (126)    | 47.6 (84)     | 51.0 (196)    | 45.5 (101)    | 48.5 (68)     | 50.8 (124)    | 47.7 (65)     | 54.5 (44)     | 56.8 (44)     | 40.9 (22)     | 46.7 (15)     |
| B_k40  | 54.7 (245)    | 58.3 (127)    | 56.0 (84)     | 55.3 (199)    | 55.9 (102)    | 55.2 (67)     | 55.9 (127)    | 63.1 (65)     | 55.8 (43)     | 55.6 (45)     | 63.6 (22)     | 50.0 (14)     |
| C_k20  | 48.8 (254)    | 42.5 (127)    | 49.4 (85)     | 47.8 (205)    | 44.7 (103)    | 43.5 (69)     | 44.3 (131)    | 42.4 (66)     | 45.5 (44)     | 45.7 (46)     | 43.5 (23)     | 53.3 (15)     |
| C_k40  | 47.5 (255)    | 44.5 (128)    | 52.9 (85)     | 46.6 (206)    | 46.6 (103)    | 42.0 (69)     | 43.2 (132)    | 45.5 (66)     | 47.7 (44)     | 39.1 (46)     | 52.2 (23)     | 46.7 (15)     |
| D_k20  | 55.0 (249)    | 53.5 (127)    | 56.5 (85)     | 55.2 (201)    | 55.9 (102)    | 55.9 (68)     | 60.5 (129)    | 55.4 (65)     | 60.5 (43)     | 59.1 (44)     | 43.5 (23)     | 42.9 (14)     |
| D_k40  | 52.6 (253)    | 53.1 (128)    | 57.6 (85)     | 52.5 (204)    | 55.3 (103)    | 53.6 (69)     | 53.1 (130)    | 56.1 (66)     | 61.4 (44)     | 51.1 (45)     | 43.5 (23)     | 66.7 (15)     |
| E_k20  | 45.8 (253)    | 47.2 (127)    | 50.6 (85)     | 43.1 (204)    | 45.6 (103)    | 47.8 (69)     | 43.8 (130)    | 42.4 (66)     | 54.5 (44)     | 39.1 (46)     | 43.5 (23)     | 46.7 (15)     |
| E_k40  | 46.7 (255)    | 45.3 (128)    | 51.8 (85)     | 46.1 (206)    | 45.6 (103)    | 55.1 (69)     | 49.2 (132)    | 49.2 (65)     | 65.9 (44)     | 56.5 (46)     | 40.9 (22)     | 66.7 (15)     |
| F_k20  | 56.2 (208)    | 57.7 (104)    | 55.1 (69)     | 57.8 (206)    | 59.2 (103)    | 63.8 (69)     | 53.0 (132)    | 53.0 (66)     | 65.9 (44)     | 50.0 (46)     | 47.8 (23)     | 73.3 (15)     |
| F_k40  | 49.5 (208)    | 56.7 (104)    | 55.1 (69)     | 51.7 (207)    | 55.3 (103)    | 56.5 (69)     | 51.9 (133)    | 56.9 (65)     | 59.1 (44)     | 46.8 (47)     | 36.4 (22)     | 53.3 (15)     |

**The same with 95 % Wilson intervals, 2010-26, and decisions per year**

| rule   | 2010-26 h21        | 2010-26 h42        | 2010-26 h63       | dec/yr h21   | dec/yr h42   | dec/yr h63   | share long h21   |
|:-------|:-------------------|:-------------------|:------------------|:-------------|:-------------|:-------------|:-----------------|
| A_k20  | 45.5 [39-52] (202) | 48.0 [39-58] (102) | 57.4 [46-68] (68) | 12.1         | 6.1          | 4.1          | 48               |
| A_k40  | 41.7 [35-49] (206) | 54.4 [45-64] (103) | 43.5 [32-55] (69) | 12.3         | 6.2          | 4.2          | 47               |
| B_k20  | 51.0 [44-58] (196) | 45.5 [36-55] (101) | 48.5 [37-60] (68) | 11.7         | 6.1          | 4.1          | 71               |
| B_k40  | 55.3 [48-62] (199) | 55.9 [46-65] (102) | 55.2 [43-67] (67) | 11.9         | 6.1          | 4.0          | 71               |
| C_k20  | 47.8 [41-55] (205) | 44.7 [35-54] (103) | 43.5 [32-55] (69) | 12.2         | 6.2          | 4.2          | 52               |
| C_k40  | 46.6 [40-53] (206) | 46.6 [37-56] (103) | 42.0 [31-54] (69) | 12.3         | 6.2          | 4.2          | 54               |
| D_k20  | 55.2 [48-62] (201) | 55.9 [46-65] (102) | 55.9 [44-67] (68) | 12.0         | 6.1          | 4.1          | 56               |
| D_k40  | 52.5 [46-59] (204) | 55.3 [46-65] (103) | 53.6 [42-65] (69) | 12.2         | 6.2          | 4.2          | 62               |
| E_k20  | 43.1 [37-50] (204) | 45.6 [36-55] (103) | 47.8 [36-59] (69) | 12.2         | 6.2          | 4.2          | 72               |
| E_k40  | 46.1 [39-53] (206) | 45.6 [36-55] (103) | 55.1 [43-66] (69) | 12.3         | 6.2          | 4.2          | 82               |
| F_k20  | 57.8 [51-64] (206) | 59.2 [50-68] (103) | 63.8 [52-74] (69) | 12.3         | 6.2          | 4.2          | 51               |
| F_k40  | 51.7 [45-58] (207) | 55.3 [46-65] (103) | 56.5 [45-68] (69) | 12.4         | 6.2          | 4.2          | 53               |

**Weekly decisions** (every 5th session; overlapping holds, so the effective n is about n x 5 / h)

| rule   | 2006-26 h21   | 2006-26 h42   | 2006-26 h63   | 2010-26 h21   | 2010-26 h42   | 2010-26 h63   | 2016-26 h21   | 2016-26 h42   | 2016-26 h63   | 2023-26 h21   | 2023-26 h42   | 2023-26 h63   |
|:-------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|
| A_k20  | 46.8          | 49.1          | 47.5          | 47.7          | 47.7          | 45.2          | 48.9          | 47.7          | 45.2          | 48.8          | 44.0          | 45.6          |
| A_k40  | 45.3          | 50.3          | 47.6          | 44.2          | 50.4          | 47.3          | 47.8          | 50.4          | 47.6          | 47.3          | 44.6          | 47.0          |
| B_k20  | 51.1          | 51.4          | 50.1          | 52.3          | 50.3          | 49.7          | 53.2          | 48.2          | 50.2          | 53.3          | 47.4          | 45.1          |
| B_k40  | 54.0          | 55.3          | 53.7          | 54.3          | 53.0          | 52.4          | 55.3          | 53.8          | 50.6          | 58.1          | 53.2          | 41.9          |
| C_k20  | 49.9          | 46.9          | 48.4          | 47.7          | 45.1          | 50.2          | 44.0          | 43.9          | 51.0          | 41.4          | 45.3          | 55.8          |
| C_k40  | 49.6          | 49.2          | 49.1          | 48.7          | 46.5          | 48.1          | 47.7          | 48.3          | 52.0          | 48.2          | 52.6          | 56.9          |
| D_k20  | 54.9          | 55.3          | 57.3          | 56.3          | 54.0          | 54.9          | 59.3          | 56.6          | 60.0          | 53.4          | 43.8          | 55.6          |
| D_k40  | 54.5          | 55.8          | 57.6          | 55.1          | 53.7          | 54.5          | 57.4          | 55.5          | 59.0          | 50.3          | 47.5          | 55.4          |
| E_k20  | 48.7          | 49.5          | 54.5          | 45.5          | 45.8          | 50.8          | 46.5          | 46.1          | 54.5          | 43.9          | 47.8          | 59.5          |
| E_k40  | 48.2          | 50.6          | 56.3          | 45.9          | 47.8          | 52.7          | 46.6          | 49.1          | 56.1          | 47.6          | 49.4          | 57.6          |
| F_k20  | 54.0          | 57.1          | 59.6          | 54.6          | 57.6          | 60.2          | 54.0          | 55.8          | 60.4          | 51.2          | 47.4          | 54.1          |
| F_k40  | 51.7          | 55.9          | 57.5          | 52.2          | 56.5          | 58.1          | 53.3          | 56.4          | 60.6          | 45.0          | 47.0          | 52.7          |

**Monthly clock** (last session of each month)

| rule   | 2006-26 h21   | 2006-26 h42   | 2006-26 h63   | 2010-26 h21   | 2010-26 h42   | 2010-26 h63   | 2016-26 h21   | 2016-26 h42   | 2016-26 h63   | 2023-26 h21   | 2023-26 h42   | 2023-26 h63   |
|:-------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|
| A_k20  | 44.4          | 50.2          | 49.3          | 46.4          | 48.2          | 46.5          | 49.0          | 48.2          | 51.5          | 36.1          | 36.8          | 51.3          |
| A_k40  | 44.4          | 49.3          | 47.9          | 45.3          | 48.0          | 46.8          | 48.6          | 51.5          | 48.1          | 48.6          | 48.5          | 45.0          |
| B_k20  | 53.0          | 50.4          | 52.5          | 55.6          | 49.2          | 53.0          | 55.0          | 48.7          | 53.8          | 59.0          | 37.8          | 48.6          |
| B_k40  | 53.8          | 55.2          | 56.2          | 54.7          | 51.1          | 55.2          | 52.7          | 52.1          | 53.2          | 60.5          | 44.2          | 46.2          |
| C_k20  | 44.0          | 50.7          | 48.4          | 40.8          | 48.8          | 48.6          | 34.3          | 45.8          | 50.4          | 25.8          | 43.9          | 50.0          |
| C_k40  | 48.1          | 48.6          | 46.3          | 46.5          | 47.4          | 46.1          | 42.9          | 48.1          | 49.5          | 47.2          | 50.0          | 48.6          |
| D_k20  | 52.7          | 58.9          | 57.5          | 53.4          | 57.0          | 55.8          | 57.7          | 59.6          | 60.9          | 52.9          | 44.4          | 51.4          |
| D_k40  | 55.6          | 56.4          | 57.3          | 56.7          | 54.2          | 54.8          | 57.8          | 54.9          | 58.7          | 53.8          | 46.3          | 58.5          |
| E_k20  | 50.5          | 50.9          | 53.3          | 48.0          | 45.2          | 50.0          | 49.5          | 47.3          | 56.5          | 51.4          | 41.2          | 61.1          |
| E_k40  | 50.2          | 50.9          | 54.9          | 48.3          | 47.0          | 52.0          | 44.8          | 46.4          | 55.5          | 45.7          | 42.1          | 52.5          |
| F_k20  | 55.7          | 56.1          | 58.9          | 56.0          | 56.4          | 59.0          | 54.3          | 55.0          | 59.8          | 53.8          | 47.4          | 53.8          |
| F_k40  | 50.5          | 53.7          | 57.7          | 51.1          | 54.3          | 58.3          | 52.4          | 56.8          | 59.5          | 48.8          | 53.7          | 57.1          |

**Reference: the plain SIGN of the same inputs** (existing signals, same evaluator, non-overlapping; not new trials)

| reference                        | 2006-26 h21   | 2006-26 h42   | 2006-26 h63   | 2010-26 h21   | 2010-26 h42   | 2010-26 h63   | 2016-26 h21   | 2016-26 h42   | 2016-26 h63   | 2023-26 h21   | 2023-26 h42   | 2023-26 h63   |
|:---------------------------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|
| sign(cot_z52)                    | 57.6 (257)    | 59.4 (128)    | 55.3 (85)     | 58.2 (208)    | 68.3 (104)    | 68.1 (69)     | 56.4 (133)    | 66.7 (66)     | 70.5 (44)     | 46.8 (47)     | 56.5 (23)     | 66.7 (15)     |
| sign(d_spread2y_20)              | 47.5 (257)    | 46.9 (128)    | 48.2 (85)     | 50.5 (208)    | 51.0 (104)    | 58.0 (69)     | 51.1 (133)    | 50.0 (66)     | 56.8 (44)     | 55.3 (47)     | 43.5 (23)     | 46.7 (15)     |
| sign(house score)                | 53.3 (257)    | 59.4 (128)    | 56.5 (85)     | 54.8 (208)    | 60.6 (104)    | 63.8 (69)     | 51.1 (133)    | 60.6 (66)     | 61.4 (44)     | 57.4 (47)     | 52.2 (23)     | 60.0 (15)     |
| majority of the three signs      | 51.0 (257)    | 55.5 (128)    | 49.4 (85)     | 55.3 (208)    | 64.4 (104)    | 71.0 (69)     | 51.1 (133)    | 63.6 (66)     | 70.5 (44)     | 57.4 (47)     | 52.2 (23)     | 73.3 (15)     |
| agreement rule (all three agree) | 58.6 (191)    | 56.8 (111)    | 73.7 (76)     | 59.0 (156)    | 60.7 (89)     | 72.1 (61)     | 57.3 (96)     | 58.9 (56)     | 71.1 (38)     | 60.0 (35)     | 45.0 (20)     | 50.0 (14)     |

Weekly grid:

| reference                        | 2006-26 h21   | 2006-26 h42   | 2006-26 h63   | 2010-26 h21   | 2010-26 h42   | 2010-26 h63   | 2016-26 h21   | 2016-26 h42   | 2016-26 h63   | 2023-26 h21   | 2023-26 h42   | 2023-26 h63   |
|:---------------------------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|
| sign(cot_z52)                    | 57.6          | 60.1          | 62.2          | 58.3          | 61.3          | 62.6          | 56.5          | 59.5          | 63.3          | 49.7          | 47.6          | 52.9          |
| sign(d_spread2y_20)              | 49.9          | 49.8          | 51.5          | 49.7          | 50.8          | 51.5          | 49.9          | 51.0          | 50.8          | 53.3          | 49.2          | 44.9          |
| sign(house score)                | 53.6          | 54.6          | 55.7          | 55.5          | 57.9          | 60.4          | 53.7          | 57.3          | 61.5          | 52.3          | 46.1          | 56.7          |
| majority of the three signs      | 54.4          | 55.3          | 58.4          | 55.1          | 56.9          | 60.0          | 53.8          | 56.4          | 61.0          | 51.8          | 45.5          | 51.9          |
| agreement rule (all three agree) | 58.4          | 61.8          | 64.2          | 59.4          | 64.8          | 66.6          | 57.2          | 63.2          | 66.9          | 54.5          | 46.6          | 53.4          |

## 4. Calibration: does '70 % of the analogs rose' come true 70 % of the time?

Weekly grid, 2006-26 (F: 2009-11 onwards). `Brier` of the analog P(up) against 0.250 for 'always 50 %' and against the library base rate (share of rising outcomes among all eligible library sessions); `slope` = regression of the outcome on P (1 = calibrated, 0 = no information, negative = anti-informative); `stated` = mean of max(P, 1-P) on the calls, `realised` = their accuracy.

| rule   | Brier h21   | base-rate Brier h21   | slope h21   | stated / realised h21   | Brier h42   | base-rate Brier h42   | slope h42   | stated / realised h42   | Brier h63   | base-rate Brier h63   | slope h63   | stated / realised h63   |
|:-------|:------------|:----------------------|:------------|:------------------------|:------------|:----------------------|:------------|:------------------------|:------------|:----------------------|:------------|:------------------------|
| A_k20  | 0.268       | 0.251                 | -0.38       | 60 / 47                 | 0.271       | 0.253                 | -0.14       | 62 / 49                 | 0.281       | 0.253                 | -0.29       | 64 / 48                 |
| A_k40  | 0.262       | 0.251                 | -0.51       | 57 / 45                 | 0.260       | 0.253                 | -0.31       | 58 / 50                 | 0.264       | 0.253                 | -0.45       | 59 / 48                 |
| B_k20  | 0.260       | 0.251                 | +0.08       | 61 / 51                 | 0.265       | 0.253                 | +0.09       | 63 / 51                 | 0.270       | 0.253                 | -0.01       | 64 / 50                 |
| B_k40  | 0.252       | 0.251                 | +0.54       | 57 / 54                 | 0.252       | 0.253                 | +0.58       | 59 / 55                 | 0.255       | 0.253                 | +0.24       | 59 / 54                 |
| C_k20  | 0.266       | 0.251                 | -0.10       | 61 / 50                 | 0.269       | 0.253                 | -0.35       | 60 / 47                 | 0.268       | 0.253                 | -0.12       | 62 / 48                 |
| C_k40  | 0.256       | 0.251                 | +0.08       | 57 / 50                 | 0.261       | 0.253                 | -0.52       | 57 / 49                 | 0.259       | 0.253                 | -0.22       | 58 / 49                 |
| D_k20  | 0.258       | 0.251                 | +0.27       | 62 / 55                 | 0.253       | 0.253                 | +0.46       | 62 / 55                 | 0.251       | 0.253                 | +0.54       | 63 / 57                 |
| D_k40  | 0.248       | 0.251                 | +0.73       | 57 / 55                 | 0.249       | 0.253                 | +0.81       | 59 / 56                 | 0.247       | 0.253                 | +0.86       | 60 / 58                 |
| E_k20  | 0.268       | 0.251                 | -0.37       | 61 / 49                 | 0.267       | 0.253                 | +0.13       | 64 / 49                 | 0.270       | 0.253                 | +0.11       | 65 / 54                 |
| E_k40  | 0.258       | 0.251                 | +0.03       | 58 / 48                 | 0.258       | 0.253                 | +0.26       | 60 / 51                 | 0.252       | 0.253                 | +0.69       | 61 / 56                 |
| F_k20  | 0.257       | 0.251                 | +0.33       | 62 / 54                 | 0.253       | 0.254                 | +0.53       | 65 / 57                 | 0.255       | 0.256                 | +0.52       | 66 / 60                 |
| F_k40  | 0.255       | 0.251                 | +0.27       | 59 / 52                 | 0.255       | 0.254                 | +0.49       | 62 / 56                 | 0.255       | 0.256                 | +0.56       | 63 / 58                 |

**Reliability, k = 20, 21 sessions**: realised share of rises in % (number of weekly forecasts) by the stated P(up)

| state          | P <20   | P 20-30   | P 30-40   | P 40-50   | P =50     | P 50-60   | P 60-70   | P 70-80   | P >=80   |
|:---------------|:--------|:----------|:----------|:----------|:----------|:----------|:----------|:----------|:---------|
| A              |         | 50 (2)    | 57 (94)   | 52 (314)  | 51 (257)  | 50 (196)  | 45 (143)  | 42 (57)   | 29 (14)  |
| B              |         | 0 (1)     | 53 (88)   | 46 (198)  | 49 (167)  | 47 (205)  | 53 (341)  | 52 (73)   | 25 (4)   |
| C              | 33 (3)  | 62 (16)   | 50 (119)  | 50 (251)  | 47 (168)  | 54 (182)  | 50 (252)  | 45 (82)   | 25 (4)   |
| D              | 100 (1) | 54 (13)   | 42 (105)  | 45 (260)  | 47 (159)  | 55 (146)  | 57 (256)  | 54 (123)  | 7 (14)   |
| E              |         |           | 79 (19)   | 49 (171)  | 53 (190)  | 50 (216)  | 51 (356)  | 41 (123)  | 0 (2)    |
| F              |         | 53 (19)   | 48 (115)  | 41 (229)  | 42 (110)  | 47 (131)  | 52 (162)  | 55 (89)   | 70 (23)  |
| A+B+C+E pooled | 33 (3)  | 58 (19)   | 55 (320)  | 50 (934)  | 50 (782)  | 50 (799)  | 51 (1092) | 44 (335)  | 25 (24)  |
| all six pooled | 50 (4)  | 55 (51)   | 51 (540)  | 47 (1423) | 49 (1051) | 51 (1076) | 52 (1510) | 48 (547)  | 38 (61)  |

**Reliability, k = 20, 63 sessions**: realised share of rises in % (number of weekly forecasts) by the stated P(up)

| state          | P <20   | P 20-30   | P 30-40   | P 40-50   | P =50    | P 50-60   | P 60-70   | P 70-80   | P >=80   |
|:---------------|:--------|:----------|:----------|:----------|:---------|:----------|:----------|:----------|:---------|
| A              | 50 (2)  | 61 (23)   | 67 (89)   | 50 (207)  | 49 (172) | 50 (129)  | 52 (246)  | 44 (147)  | 48 (54)  |
| B              |         | 47 (32)   | 49 (100)  | 59 (164)  | 41 (110) | 63 (146)  | 45 (321)  | 57 (171)  | 44 (25)  |
| C              | 0 (1)   | 45 (20)   | 50 (109)  | 55 (226)  | 55 (167) | 52 (185)  | 48 (248)  | 49 (103)  | 40 (10)  |
| D              | 100 (1) | 38 (16)   | 33 (60)   | 37 (141)  | 54 (116) | 54 (178)  | 56 (382)  | 55 (157)  | 67 (18)  |
| E              |         | 54 (13)   | 46 (56)   | 43 (131)  | 41 (87)  | 55 (143)  | 58 (361)  | 52 (186)  | 45 (92)  |
| F              | 50 (10) | 41 (54)   | 25 (97)   | 33 (135)  | 43 (68)  | 46 (90)   | 60 (172)  | 53 (173)  | 59 (71)  |
| A+B+C+E pooled | 33 (3)  | 51 (88)   | 54 (354)  | 52 (728)  | 48 (536) | 55 (603)  | 51 (1176) | 51 (607)  | 45 (181) |
| all six pooled | 50 (14) | 46 (158)  | 46 (511)  | 48 (1004) | 49 (720) | 54 (871)  | 53 (1730) | 52 (937)  | 50 (270) |

**Accuracy by stated confidence max(P, 1-P), k = 20, weekly grid 2006-26, pooled over states** (hits / calls)

| states                           | h   | stated 50-60   | stated 60-70   | stated 70-80   | stated >=80   |
|:---------------------------------|:----|:---------------|:---------------|:---------------|:--------------|
| A, B, C, E (the new information) | 21  | 50 (1369)      | 50 (1680)      | 45 (448)       | 34 (29)       |
| A, B, C, E (the new information) | 42  | 47 (1198)      | 51 (1675)      | 47 (656)       | 55 (137)      |
| A, B, C, E (the new information) | 63  | 53 (1033)      | 50 (1699)      | 49 (804)       | 46 (204)      |
| D (positioning)                  | 21  | 53 (281)       | 58 (457)       | 53 (161)       | 21 (19)       |
| D (positioning)                  | 42  | 54 (322)       | 56 (415)       | 60 (161)       | 33 (15)       |
| D (positioning)                  | 63  | 55 (254)       | 59 (480)       | 57 (196)       | 65 (23)       |
| F (agreement inputs)             | 21  | 50 (250)       | 57 (346)       | 51 (143)       | 66 (29)       |
| F (agreement inputs)             | 42  | 55 (176)       | 55 (315)       | 59 (222)       | 67 (75)       |
| F (agreement inputs)             | 63  | 56 (170)       | 64 (281)       | 58 (251)       | 56 (100)      |

**Kernel-weighted probability and the episode-level probability (each episode one vote, k = 20)**, weekly grid 2006-26

| state   | kernel Brier / slope / acc h21   | episode-level Brier / slope / acc h21   | kernel Brier / slope / acc h42   | episode-level Brier / slope / acc h42   | kernel Brier / slope / acc h63   | episode-level Brier / slope / acc h63   |
|:--------|:---------------------------------|:----------------------------------------|:---------------------------------|:----------------------------------------|:---------------------------------|:----------------------------------------|
| A       | 0.254 / -0.99 / 48               | 0.281 / -0.14 / 48                      | 0.254 / -0.15 / 52               | 0.279 / +0.01 / 49                      | 0.255 / -0.22 / 51               | 0.289 / -0.14 / 48                      |
| B       | 0.253 / -1.11 / 49               | 0.264 / +0.21 / 53                      | 0.255 / -0.54 / 49               | 0.264 / +0.24 / 53                      | 0.257 / -0.42 / 50               | 0.274 / -0.00 / 51                      |
| C       | 0.252 / -0.27 / 49               | 0.269 / -0.00 / 52                      | 0.254 / -0.79 / 49               | 0.270 / -0.17 / 51                      | 0.254 / -0.24 / 53               | 0.268 / -0.02 / 52                      |
| D       | 0.248 / +0.71 / 53               | 0.268 / +0.01 / 51                      | 0.248 / +0.78 / 57               | 0.262 / +0.14 / 53                      | 0.248 / +0.76 / 58               | 0.263 / +0.16 / 51                      |
| E       | 0.253 / -1.07 / 50               | 0.282 / -0.27 / 50                      | 0.255 / -0.35 / 52               | 0.277 / +0.09 / 50                      | 0.255 / +0.18 / 52               | 0.289 / -0.11 / 51                      |
| F       | 0.248 / +0.64 / 56               | 0.264 / +0.17 / 51                      | 0.247 / +0.69 / 55               | 0.261 / +0.38 / 53                      | 0.247 / +0.65 / 59               | 0.265 / +0.38 / 56                      |

## 5. Near-unanimous analogs (>= 70 % / >= 80 % one way)

k = 20 (with k = 40 unanimity is rare: see `analogs_calibration.csv`). Accuracy in % (decisions) and decisions per year on the non-overlapping stream; weekly-grid accuracy (calls) next to it; `epi` = mean number of independent episodes behind those calls.

**2010-26**

| state   | call   | h21 non-overlapping   | h21 dec/yr   | h21 weekly   | h42 non-overlapping   | h42 dec/yr   | h42 weekly   | h63 non-overlapping   | h63 dec/yr   | h63 weekly   | epi   |
|:--------|:-------|:----------------------|:-------------|:-------------|:----------------------|:-------------|:-------------|:----------------------|:-------------|:-------------|:------|
| A       | p>=70  | 34.0 [22-48] (47)     | 2.8          | 31.6 (57)    | 40.9 [28-56] (44)     | 2.6          | 40.6 (128)   | 41.0 [27-57] (39)     | 2.3          | 37.4 (190)   | 5.2   |
| A       | p>=80  | 33.3 [10-70] (6)      | 0.4          | 14.3 (7)     | 53.8 [29-77] (13)     | 0.8          | 50.0 (20)    | 46.7 [25-70] (15)     | 0.9          | 56.8 (44)    | 5.0   |
| B       | p>=70  | 48.5 [33-65] (33)     | 2.0          | 47.4 (95)    | 45.5 [30-62] (33)     | 2.0          | 45.0 (160)   | 56.0 [37-73] (25)     | 1.5          | 61.8 (165)   | 3.4   |
| B       | p>=80  | 0.0 [0-79] (1)        | 0.1          | 25.0 (4)     | 75.0 [30-95] (4)      | 0.2          | 66.7 (21)    | 40.0 [12-77] (5)      | 0.3          | 42.1 (19)    | 5.0   |
| C       | p>=70  | 44.9 [36-54] (107)    | 6.4          | 43.5 (115)   | 36.8 [26-50] (57)     | 3.4          | 34.4 (93)    | 59.5 [44-73] (42)     | 2.5          | 48.7 (117)   | 9.3   |
| C       | p>=80  | 35.7 [16-61] (14)     | 0.8          | 50.0 (8)     | 37.5 [14-69] (8)      | 0.5          | 11.1 (9)     | 42.9 [21-67] (14)     | 0.8          | 83.3 (6)     | 9.8   |
| D       | p>=70  | 46.1 [35-57] (76)     | 4.5          | 45.5 (156)   | 51.8 [39-64] (56)     | 3.4          | 55.2 (145)   | 51.1 [37-65] (45)     | 2.7          | 57.1 (189)   | 12.6  |
| D       | p>=80  | 27.3 [10-57] (11)     | 0.7          | 21.1 (19)    | 41.7 [19-68] (12)     | 0.7          | 28.6 (14)    | 61.5 [36-82] (13)     | 0.8          | 63.2 (19)    | 12.0  |
| E       | p>=70  | 41.7 [31-53] (72)     | 4.3          | 38.3 (94)    | 45.2 [33-57] (62)     | 3.7          | 51.3 (191)   | 41.3 [28-56] (46)     | 2.8          | 43.2 (243)   | 6.9   |
| E       | p>=80  | 50.0 [15-85] (4)      | 0.2          | 0.0 (1)      | 58.8 [36-78] (17)     | 1.0          | 52.6 (38)    | 50.0 [30-70] (20)     | 1.2          | 24.5 (49)    | 10.0  |
| F       | p>=70  | 53.7 [45-62] (134)    | 8.0          | 53.8 (171)   | 59.6 [49-69] (89)     | 5.3          | 62.1 (293)   | 55.6 [43-67] (63)     | 3.8          | 58.3 (345)   | 11.5  |
| F       | p>=80  | 52.9 [40-66] (51)     | 3.0          | 65.5 (29)    | 66.7 [54-78] (57)     | 3.4          | 66.7 (75)    | 60.0 [45-73] (45)     | 2.7          | 57.7 (97)    | 12.0  |

**2006-26**

| state   | call   | h21 non-overlapping   | h21 dec/yr   | h21 weekly   | h42 non-overlapping   | h42 dec/yr   | h42 weekly   | h63 non-overlapping   | h63 dec/yr   | h63 weekly   | epi   |
|:--------|:-------|:----------------------|:-------------|:-------------|:----------------------|:-------------|:-------------|:----------------------|:-------------|:-------------|:------|
| A       | p>=70  | 38.2 [28-50] (68)     | 3.3          | 42.6 (101)   | 39.3 [28-52] (56)     | 2.7          | 44.4 (180)   | 41.7 [29-56] (48)     | 2.3          | 40.3 (258)   | 4.7   |
| A       | p>=80  | 58.3 [32-81] (12)     | 0.6          | 33.3 (15)    | 52.4 [32-72] (21)     | 1.0          | 53.5 (43)    | 40.0 [22-61] (20)     | 1.0          | 48.4 (62)    | 4.5   |
| B       | p>=70  | 50.0 [34-66] (36)     | 1.7          | 48.6 (107)   | 48.8 [35-63] (43)     | 2.1          | 49.6 (228)   | 51.4 [36-67] (35)     | 1.7          | 56.0 (266)   | 3.4   |
| B       | p>=80  | 0.0 [0-79] (1)        | 0.0          | 25.0 (4)     | 60.0 [23-88] (5)      | 0.2          | 60.0 (25)    | 42.9 [16-75] (7)      | 0.3          | 38.2 (34)    | 5.0   |
| C       | p>=70  | 48.8 [40-57] (125)    | 6.0          | 46.4 (140)   | 41.2 [30-53] (68)     | 3.3          | 39.1 (115)   | 58.8 [45-71] (51)     | 2.5          | 47.1 (172)   | 8.9   |
| C       | p>=80  | 40.0 [20-64] (15)     | 0.7          | 50.0 (8)     | 41.7 [19-68] (12)     | 0.6          | 11.1 (9)     | 50.0 [29-71] (18)     | 0.9          | 60.0 (15)    | 9.8   |
| D       | p>=70  | 48.4 [38-58] (91)     | 4.4          | 50.0 (180)   | 57.4 [46-68] (68)     | 3.3          | 57.4 (176)   | 55.8 [42-68] (52)     | 2.5          | 57.5 (219)   | 12.2  |
| D       | p>=80  | 27.3 [10-57] (11)     | 0.5          | 21.1 (19)    | 46.2 [23-71] (13)     | 0.6          | 33.3 (15)    | 66.7 [42-85] (15)     | 0.7          | 65.2 (23)    | 12.0  |
| E       | p>=70  | 43.2 [33-54] (88)     | 4.2          | 39.5 (129)   | 49.4 [38-60] (77)     | 3.7          | 54.8 (270)   | 42.9 [31-56] (56)     | 2.7          | 49.0 (312)   | 6.2   |
| E       | p>=80  | 42.9 [16-75] (7)      | 0.3          | 0.0 (2)      | 54.5 [35-73] (22)     | 1.1          | 60.0 (60)    | 51.9 [34-69] (27)     | 1.3          | 44.1 (93)    | 7.5   |
| F       | p>=70  | 53.3 [45-62] (135)    | 8.0          | 53.5 (172)   | 58.9 [49-68] (90)     | 5.3          | 61.3 (297)   | 55.6 [43-67] (63)     | 3.8          | 57.3 (351)   | 11.5  |
| F       | p>=80  | 52.9 [40-66] (51)     | 3.0          | 65.5 (29)    | 65.5 [53-76] (58)     | 3.4          | 66.7 (75)    | 58.7 [44-72] (46)     | 2.7          | 56.0 (100)   | 12.0  |

## 6. Honesty checks specific to analogs

### (i) Independent episodes behind a forecast

Weekly forecasts 2006-26. An episode = chosen analogs chained with gaps of at most 63 sessions.

| rule                 | mean_n_epi   | median_n_epi   | p10_n_epi   | mean_distinct_years   | median_analog_age_years   | mean_dist_1   | mean_dist_k   | h21_share_p>=70   | h21_n_epi_when_p>=70   | h21_share_episode_p>=70   | h63_share_p>=70   | h63_share_episode_p>=70   |
|:---------------------|:-------------|:---------------|:------------|:----------------------|:--------------------------|:--------------|:--------------|:------------------|:-----------------------|:--------------------------|:------------------|:--------------------------|
| A_k20                | 4.84         | 5.0            | 3.0         | 5.35                  | 4.9                       | 0.77          | 1.97          | 0.09              | 4.7                    | 0.19                      | 0.24              | 0.29                      |
| A_k40                | 6.05         | 5.0            | 3.0         | 8.19                  | 5.23                      | 0.77          | 2.55          | 0.02              | 5.67                   | 0.11                      | 0.03              | 0.14                      |
| B_k20                | 4.21         | 4.0            | 2.0         | 4.91                  | 4.55                      | 1.62          | 3.48          | 0.1               | 3.39                   | 0.21                      | 0.25              | 0.24                      |
| B_k40                | 6.34         | 6.0            | 3.0         | 8.0                   | 6.27                      | 1.62          | 4.01          | 0.0               | nan                    | 0.09                      | 0.04              | 0.08                      |
| C_k20                | 9.35         | 9.0            | 6.0         | 8.55                  | 7.21                      | 0.93          | 1.92          | 0.13              | 8.87                   | 0.16                      | 0.16              | 0.13                      |
| C_k40                | 13.04        | 13.0           | 8.0         | 12.42                 | 7.22                      | 0.93          | 2.37          | 0.01              | 13.21                  | 0.06                      | 0.01              | 0.04                      |
| D_k20                | 11.95        | 12.0           | 8.0         | 9.86                  | 7.52                      | 0.09          | 0.57          | 0.17              | 12.16                  | 0.16                      | 0.21              | 0.17                      |
| D_k40                | 15.93        | 16.0           | 9.0         | 13.06                 | 7.69                      | 0.09          | 0.96          | 0.01              | 20.0                   | 0.01                      | 0.05              | 0.05                      |
| E_k20                | 6.07         | 6.0            | 3.0         | 6.28                  | 5.57                      | 1.15          | 3.16          | 0.12              | 6.19                   | 0.21                      | 0.29              | 0.35                      |
| E_k40                | 7.61         | 7.0            | 4.0         | 9.01                  | 5.98                      | 1.15          | 4.03          | 0.03              | 5.64                   | 0.16                      | 0.1               | 0.23                      |
| F_k20                | 10.98        | 11.0           | 6.2         | 9.04                  | 6.61                      | 0.16          | 0.72          | 0.2               | 11.52                  | 0.16                      | 0.4               | 0.29                      |
| F_k40                | 13.45        | 14.0           | 6.0         | 11.88                 | 6.42                      | 0.16          | 1.19          | 0.05              | 14.55                  | 0.09                      | 0.22              | 0.16                      |
| A_k20 (long library) | 6.1          | 6.0            | 4.0         | 6.43                  | 6.49                      | 0.56          | 1.56          | 0.07              | 6.06                   | 0.14                      | 0.21              | 0.19                      |
| A_k40 (long library) | 9.17         | 9.0            | 6.0         | 10.43                 | 7.49                      | 0.56          | 1.95          | 0.02              | 10.0                   | 0.03                      | 0.03              | 0.05                      |
| B_k20 (long library) | 4.71         | 4.0            | 3.0         | 5.31                  | 6.94                      | 1.55          | 3.06          | 0.12              | 4.5                    | 0.21                      | 0.26              | 0.27                      |
| B_k40 (long library) | 7.2          | 7.0            | 3.1         | 8.68                  | 11.05                     | 1.55          | 3.47          | 0.01              | 8.5                    | 0.06                      | 0.04              | 0.08                      |
| C_k20 (long library) | 11.22        | 11.0           | 8.0         | 9.92                  | 11.66                     | 0.85          | 1.69          | 0.11              | 11.26                  | 0.11                      | 0.18              | 0.15                      |
| C_k40 (long library) | 16.68        | 17.0           | 12.0        | 14.97                 | 11.73                     | 0.85          | 2.04          | 0.01              | 17.2                   | 0.04                      | 0.02              | 0.04                      |

`share_p>=70` = share of forecasts where at least 70 % of the analogs agree; `share_episode_p>=70` = the same when each episode has one vote. `mean_dist_1` / `mean_dist_k` = Euclidean distance (in standard deviations) of the nearest and of the k-th analog.

### (ii)-(iv) Distance must matter; shuffled outcomes; look-ahead

**weekly, 21 sessions, 2006-26** (accuracy in %)

| control (k = 20)                               | A    | B    | C    | D    | E    | F    |
|:-----------------------------------------------|:-----|:-----|:-----|:-----|:-----|:-----|
| nearest k (the method)                         | 46.8 | 51.1 | 49.9 | 54.9 | 48.7 | 54.0 |
| ranks 21-40                                    | 47.8 | 53.4 | 52.0 | 55.8 | 51.3 | 50.5 |
| random k (mean of 5 draws)                     | 50.1 | 49.6 | 49.8 | 50.0 | 49.6 | 49.0 |
| farthest k                                     | 51.2 | 52.5 | 50.6 | 49.9 | 48.6 | 44.5 |
| library base rate                              | 45.8 | 45.8 | 45.8 | 45.8 | 45.8 | 46.5 |
| shuffled outcomes (mean of 5)                  | 52.6 | 50.3 | 49.6 | 50.8 | 48.3 | 49.5 |
| look-ahead: future analogs, 63-session embargo | 47.3 | 45.0 | 49.4 | 54.6 | 48.1 | 54.2 |
| look-ahead: no embargo                         | 55.7 | 55.9 | 59.2 | 59.9 | 60.3 | 59.4 |
| library frozen at year start (strict protocol) | 46.1 | 50.1 | 50.8 | 55.3 | 51.6 | 54.2 |
| state 21 sessions stale                        | 46.5 | 48.6 | 46.8 | 48.1 | 48.2 | 52.3 |

**weekly, 42 sessions, 2006-26** (accuracy in %)

| control (k = 20)                               | A    | B    | C    | D    | E    | F    |
|:-----------------------------------------------|:-----|:-----|:-----|:-----|:-----|:-----|
| nearest k (the method)                         | 49.1 | 51.4 | 46.9 | 55.3 | 49.5 | 57.1 |
| ranks 21-40                                    | 46.7 | 56.2 | 49.5 | 53.0 | 49.3 | 49.9 |
| random k (mean of 5 draws)                     | 49.4 | 50.4 | 49.3 | 50.1 | 50.4 | 47.9 |
| farthest k                                     | 52.1 | 49.7 | 49.0 | 52.4 | 45.5 | 42.1 |
| library base rate                              | 46.7 | 46.7 | 46.7 | 46.7 | 46.7 | 44.3 |
| shuffled outcomes (mean of 5)                  | 49.4 | 51.1 | 50.0 | 48.7 | 51.2 | 49.3 |
| look-ahead: future analogs, 63-session embargo | 46.4 | 49.6 | 46.0 | 54.3 | 50.2 | 55.7 |
| look-ahead: no embargo                         | 59.6 | 59.6 | 62.6 | 63.4 | 62.4 | 61.4 |
| library frozen at year start (strict protocol) | 48.3 | 49.6 | 46.9 | 54.9 | 49.2 | 57.9 |
| state 21 sessions stale                        | 47.8 | 50.9 | 42.7 | 49.4 | 50.1 | 54.4 |

**weekly, 63 sessions, 2006-26** (accuracy in %)

| control (k = 20)                               | A    | B    | C    | D    | E    | F    |
|:-----------------------------------------------|:-----|:-----|:-----|:-----|:-----|:-----|
| nearest k (the method)                         | 47.5 | 50.1 | 48.4 | 57.3 | 54.5 | 59.6 |
| ranks 21-40                                    | 49.6 | 52.3 | 47.9 | 55.8 | 53.7 | 55.6 |
| random k (mean of 5 draws)                     | 49.5 | 51.6 | 48.4 | 51.2 | 51.6 | 47.8 |
| farthest k                                     | 54.1 | 53.8 | 47.1 | 52.1 | 42.9 | 38.8 |
| library base rate                              | 47.4 | 47.4 | 47.4 | 47.4 | 47.4 | 43.7 |
| shuffled outcomes (mean of 5)                  | 50.9 | 50.5 | 48.9 | 51.5 | 49.9 | 48.2 |
| look-ahead: future analogs, 63-session embargo | 47.2 | 42.9 | 49.8 | 57.4 | 53.0 | 59.1 |
| look-ahead: no embargo                         | 63.8 | 60.1 | 69.4 | 64.1 | 65.2 | 63.8 |
| library frozen at year start (strict protocol) | 45.4 | 48.5 | 48.7 | 56.3 | 52.8 | 60.5 |
| state 21 sessions stale                        | 46.0 | 49.0 | 49.9 | 53.8 | 51.9 | 54.7 |

**nonoverlap, 21 sessions, 2006-26** (accuracy in %)

| control (k = 20)                               | A    | B    | C    | D    | E    | F    |
|:-----------------------------------------------|:-----|:-----|:-----|:-----|:-----|:-----|
| nearest k (the method)                         | 46.0 | 51.4 | 48.8 | 55.0 | 45.8 | 56.2 |
| ranks 21-40                                    | 44.3 | 51.5 | 50.0 | 56.8 | 52.6 | 49.0 |
| random k (mean of 5 draws)                     | 50.2 | 51.3 | 47.8 | 49.1 | 51.3 | 49.0 |
| farthest k                                     | 50.2 | 55.2 | 54.1 | 45.3 | 48.0 | 44.0 |
| library base rate                              | 44.7 | 44.7 | 44.7 | 44.7 | 44.7 | 47.6 |
| shuffled outcomes (mean of 5)                  | 51.5 | 49.9 | 50.0 | 50.0 | 50.0 | 48.9 |
| look-ahead: future analogs, 63-session embargo | 45.1 | 43.1 | 47.6 | 54.0 | 51.0 | 56.4 |
| look-ahead: no embargo                         | 51.0 | 53.3 | 58.9 | 59.8 | 58.9 | 58.4 |
| library frozen at year start (strict protocol) | 43.3 | 50.2 | 52.8 | 52.4 | 54.2 | 58.3 |
| state 21 sessions stale                        | 46.0 | 47.8 | 45.1 | 49.8 | 52.4 | 52.7 |

**nonoverlap, 42 sessions, 2006-26** (accuracy in %)

| control (k = 20)                               | A    | B    | C    | D    | E    | F    |
|:-----------------------------------------------|:-----|:-----|:-----|:-----|:-----|:-----|
| nearest k (the method)                         | 50.0 | 48.4 | 42.5 | 53.5 | 47.2 | 57.7 |
| ranks 21-40                                    | 48.0 | 51.6 | 52.0 | 48.0 | 45.7 | 56.7 |
| random k (mean of 5 draws)                     | 45.6 | 46.8 | 51.6 | 48.8 | 46.8 | 50.2 |
| farthest k                                     | 52.0 | 50.0 | 48.0 | 52.4 | 43.3 | 48.1 |
| library base rate                              | 46.1 | 46.1 | 46.1 | 46.1 | 46.1 | 43.8 |
| shuffled outcomes (mean of 5)                  | 50.8 | 48.7 | 49.7 | 48.0 | 51.0 | 51.5 |
| look-ahead: future analogs, 63-session embargo | 45.7 | 53.6 | 49.2 | 53.2 | 55.5 | 55.7 |
| look-ahead: no embargo                         | 56.7 | 55.2 | 52.8 | 56.3 | 65.4 | 59.0 |
| library frozen at year start (strict protocol) | 50.0 | 50.4 | 46.9 | 52.0 | 50.0 | 56.3 |
| state 21 sessions stale                        | 47.6 | 55.2 | 43.7 | 52.8 | 48.4 | 52.9 |

**nonoverlap, 63 sessions, 2006-26** (accuracy in %)

| control (k = 20)                               | A    | B    | C    | D    | E    | F    |
|:-----------------------------------------------|:-----|:-----|:-----|:-----|:-----|:-----|
| nearest k (the method)                         | 42.4 | 47.6 | 49.4 | 56.5 | 50.6 | 55.1 |
| ranks 21-40                                    | 55.3 | 48.8 | 45.9 | 57.6 | 52.9 | 43.5 |
| random k (mean of 5 draws)                     | 50.4 | 50.4 | 44.9 | 50.4 | 50.4 | 49.6 |
| farthest k                                     | 59.0 | 56.4 | 48.2 | 56.6 | 40.0 | 36.2 |
| library base rate                              | 43.5 | 43.5 | 43.5 | 43.5 | 43.5 | 41.4 |
| shuffled outcomes (mean of 5)                  | 52.0 | 47.9 | 51.1 | 49.2 | 49.4 | 49.6 |
| look-ahead: future analogs, 63-session embargo | 44.7 | 42.9 | 49.4 | 56.5 | 55.3 | 60.5 |
| look-ahead: no embargo                         | 61.2 | 53.6 | 69.4 | 68.2 | 65.9 | 71.6 |
| library frozen at year start (strict protocol) | 35.7 | 50.0 | 45.9 | 58.8 | 52.9 | 63.8 |
| state 21 sessions stale                        | 46.4 | 50.0 | 45.9 | 60.0 | 54.1 | 60.9 |

Range of the five random draws (weekly, k = 20): A h21 48-52; A h42 48-52; A h63 48-51; B h21 47-51; B h42 49-51; B h63 49-53; C h21 48-52; C h42 48-52; C h63 46-50; D h21 48-52; D h42 48-51; D h63 49-53; E h21 47-51; E h42 49-51; E h63 49-53; F h21 47-52; F h42 46-50; F h63 44-51.

### Engine truncation test

Every state row after the last session of the cut year and every outcome not yet known on that session replaced by noise; the chosen analogs and the probabilities of that year's decisions must be unchanged (F excluded: its inputs come from the feature store).

| cut_year   | state   | decisions   | analogs_identical   | max_abs_diff_p   |
|:-----------|:--------|:------------|:--------------------|:-----------------|
| 2012       | A       | 260         | True                | 0.0              |
| 2012       | B       | 260         | True                | 0.0              |
| 2012       | C       | 260         | True                | 0.0              |
| 2012       | D       | 260         | True                | 0.0              |
| 2012       | E       | 260         | True                | 0.0              |
| 2019       | A       | 260         | True                | 0.0              |
| 2019       | B       | 260         | True                | 0.0              |
| 2019       | C       | 260         | True                | 0.0              |
| 2019       | D       | 260         | True                | 0.0              |
| 2019       | E       | 260         | True                | 0.0              |

### Label in disguise? Correlation of every state dimension with the forward returns (all sessions 1999+)

| state   | dimension       | corr_fwd1   | corr_fwd21   | corr_fwd42   | corr_fwd63   | corr_fwd1_weekly_grid   |
|:--------|:----------------|:------------|:-------------|:-------------|:-------------|:------------------------|
| A       | a_fed_dir       | -0.002      | -0.025       | -0.057       | -0.078       | 0.043                   |
| A       | a_ecb_dir       | -0.011      | -0.067       | -0.089       | -0.089       | 0.012                   |
| A       | a_gap           | 0.002       | 0.019        | 0.027        | 0.027        | -0.034                  |
| A       | a_gap_d126      | -0.011      | -0.029       | -0.029       | -0.047       | -0.033                  |
| A       | a_us_slope      | -0.012      | -0.017       | -0.018       | -0.037       | -0.033                  |
| A       | a_spread2y      | 0.012       | 0.042        | 0.056        | 0.071        | -0.017                  |
| A       | a_spread2y_d63  | 0.006       | 0.043        | 0.067        | 0.08         | 0.048                   |
| B       | b_us_infl       | -0.019      | -0.081       | -0.108       | -0.126       | -0.036                  |
| B       | b_us_infl_d6    | -0.03       | -0.141       | -0.205       | -0.251       | -0.048                  |
| B       | b_ea_infl       | 0.003       | 0.023        | 0.035        | 0.044        | -0.012                  |
| B       | b_ea_infl_d6    | -0.011      | -0.042       | -0.068       | -0.087       | -0.014                  |
| B       | b_us_unemp      | 0.01        | 0.035        | 0.047        | 0.042        | 0.023                   |
| B       | b_us_unemp_d6   | 0.02        | 0.092        | 0.137        | 0.156        | 0.014                   |
| B       | b_ea_unemp      | -0.007      | -0.036       | -0.053       | -0.07        | 0.004                   |
| B       | b_ea_unemp_d6   | 0.012       | 0.059        | 0.079        | 0.093        | 0.003                   |
| C       | c_ret63         | 0.007       | 0.036        | 0.041        | 0.044        | 0.041                   |
| C       | c_ret252        | -0.003      | -0.019       | -0.041       | -0.063       | -0.016                  |
| C       | c_dist200       | 0.003       | 0.02         | 0.016        | 0.019        | 0.021                   |
| C       | c_rvpct         | -0.016      | -0.044       | -0.038       | -0.019       | -0.018                  |
| C       | c_vix           | -0.003      | -0.004       | 0.028        | 0.038        | -0.027                  |
| C       | c_eqrel63       | 0.023       | 0.076        | 0.065        | 0.075        | 0.029                   |
| C       | c_brent_d126    | 0.007       | -0.008       | -0.039       | -0.077       | 0.096                   |
| D       | d_cot_z52       | 0.032       | 0.162        | 0.195        | 0.201        | 0.033                   |
| D       | d_cot_z52_d65   | 0.01        | 0.084        | 0.091        | 0.077        | 0.015                   |
| F       | f_cot_z52       | 0.034       | 0.166        | 0.212        | 0.233        | 0.031                   |
| F       | f_d_spread2y_20 | 0.034       | 0.04         | 0.035        | 0.11         | 0.065                   |
| F       | f_house         | 0.07        | 0.183        | 0.228        | 0.281        | 0.081                   |

## 7. As an EXTRA VOTE on the agreement rule

Form: agreement rule AND the analog call for the same horizon points the same way. Non-overlapping decisions; accuracy of the agreement rule alone, of the vote rule, the gain in points, the vote rule's decisions (per year).

**(a) 2010-26**

| candidate   | h21 agree3   | h21 vote   | h21 gain   | h21 n (per yr)   | h42 agree3   | h42 vote   | h42 gain   | h42 n (per yr)   | h63 agree3   | h63 vote   | h63 gain   | h63 n (per yr)   |
|:------------|:-------------|:-----------|:-----------|:-----------------|:-------------|:-----------|:-----------|:-----------------|:-------------|:-----------|:-----------|:-----------------|
| A_k20       | 59.0         | 48.0       | -11.0      | 100 (6.0)        | 60.7         | 66.1       | +5.4       | 59 (3.5)         | 72.1         | 68.2       | -3.9       | 44 (2.7)         |
| A_k40       | 59.0         | 44.6       | -14.4      | 92 (5.5)         | 60.7         | 60.7       | -0.0       | 61 (3.7)         | 72.1         | 60.0       | -12.1      | 45 (2.7)         |
| B_k20       | 59.0         | 56.8       | -2.2       | 81 (4.8)         | 60.7         | 60.4       | -0.3       | 48 (2.9)         | 72.1         | 65.8       | -6.3       | 38 (2.3)         |
| B_k40       | 59.0         | 63.2       | +4.2       | 87 (5.2)         | 60.7         | 68.6       | +8.0       | 51 (3.1)         | 72.1         | 64.9       | -7.3       | 37 (2.2)         |
| C_k20       | 59.0         | 53.8       | -5.2       | 106 (6.3)        | 60.7         | 56.2       | -4.4       | 64 (3.8)         | 72.1         | 60.8       | -11.3      | 51 (3.1)         |
| C_k40       | 59.0         | 51.4       | -7.6       | 111 (6.6)        | 60.7         | 53.0       | -7.6       | 66 (4.0)         | 72.1         | 59.6       | -12.6      | 47 (2.8)         |
| D_k20       | 59.0         | 55.9       | -3.1       | 127 (7.6)        | 60.7         | 54.1       | -6.6       | 74 (4.4)         | 72.1         | 68.5       | -3.6       | 54 (3.3)         |
| D_k40       | 59.0         | 58.1       | -0.8       | 129 (7.7)        | 60.7         | 54.1       | -6.6       | 74 (4.4)         | 72.1         | 56.9       | -15.3      | 51 (3.1)         |
| E_k20       | 59.0         | 52.8       | -6.2       | 89 (5.3)         | 60.7         | 68.4       | +7.7       | 57 (3.4)         | 72.1         | 60.5       | -11.7      | 43 (2.6)         |
| E_k40       | 59.0         | 47.1       | -11.8      | 87 (5.2)         | 60.7         | 64.8       | +4.1       | 54 (3.2)         | 72.1         | 70.7       | -1.4       | 41 (2.5)         |
| F_k20       | 59.0         | 56.6       | -2.4       | 136 (8.1)        | 60.7         | 67.4       | +6.8       | 86 (5.2)         | 72.1         | 72.1       | +0.0       | 61 (3.7)         |
| F_k40       | 59.0         | 54.6       | -4.4       | 130 (7.8)        | 60.7         | 63.9       | +3.2       | 83 (5.0)         | 72.1         | 68.4       | -3.7       | 57 (3.4)         |

**(a) 2016-26**

| candidate   | h21 agree3   | h21 vote   | h21 gain   | h21 n (per yr)   | h42 agree3   | h42 vote   | h42 gain   | h42 n (per yr)   | h63 agree3   | h63 vote   | h63 gain   | h63 n (per yr)   |
|:------------|:-------------|:-----------|:-----------|:-----------------|:-------------|:-----------|:-----------|:-----------------|:-------------|:-----------|:-----------|:-----------------|
| A_k20       | 57.3         | 48.4       | -8.9       | 64 (5.9)         | 58.9         | 64.3       | +5.4       | 42 (3.9)         | 71.1         | 71.9       | +0.8       | 32 (3.0)         |
| A_k40       | 57.3         | 47.5       | -9.8       | 59 (5.5)         | 58.9         | 58.1       | -0.8       | 43 (4.0)         | 71.1         | 60.6       | -10.4      | 33 (3.1)         |
| B_k20       | 57.3         | 54.7       | -2.6       | 53 (4.9)         | 58.9         | 60.0       | +1.1       | 30 (2.8)         | 71.1         | 69.2       | -1.8       | 26 (2.5)         |
| B_k40       | 57.3         | 66.7       | +9.4       | 54 (5.0)         | 58.9         | 69.7       | +10.8      | 33 (3.1)         | 71.1         | 58.3       | -12.7      | 24 (2.3)         |
| C_k20       | 57.3         | 51.6       | -5.7       | 64 (5.9)         | 58.9         | 53.5       | -5.4       | 43 (4.0)         | 71.1         | 58.1       | -13.0      | 31 (2.9)         |
| C_k40       | 57.3         | 46.4       | -10.9      | 69 (6.4)         | 58.9         | 52.4       | -6.5       | 42 (3.9)         | 71.1         | 58.6       | -12.4      | 29 (2.7)         |
| D_k20       | 57.3         | 58.4       | +1.1       | 77 (7.2)         | 58.9         | 54.2       | -4.8       | 48 (4.5)         | 71.1         | 66.7       | -4.4       | 36 (3.4)         |
| D_k40       | 57.3         | 58.5       | +1.2       | 82 (7.6)         | 58.9         | 51.0       | -7.9       | 51 (4.8)         | 71.1         | 55.6       | -15.5      | 36 (3.4)         |
| E_k20       | 57.3         | 56.6       | -0.7       | 53 (4.9)         | 58.9         | 68.4       | +9.5       | 38 (3.6)         | 71.1         | 60.7       | -10.3      | 28 (2.6)         |
| E_k40       | 57.3         | 45.5       | -11.8      | 55 (5.1)         | 58.9         | 64.1       | +5.2       | 39 (3.7)         | 71.1         | 71.4       | +0.4       | 28 (2.6)         |
| F_k20       | 57.3         | 57.5       | +0.2       | 80 (7.4)         | 58.9         | 68.5       | +9.6       | 54 (5.1)         | 71.1         | 68.4       | -2.6       | 38 (3.6)         |
| F_k40       | 57.3         | 56.8       | -0.5       | 81 (7.5)         | 58.9         | 64.8       | +5.9       | 54 (5.1)         | 71.1         | 68.4       | -2.6       | 38 (3.6)         |

**(a) 2023-26**

| candidate   | h21 agree3   | h21 vote   | h21 gain   | h21 n (per yr)   | h42 agree3   | h42 vote   | h42 gain   | h42 n (per yr)   | h63 agree3   | h63 vote   | h63 gain   | h63 n (per yr)   |
|:------------|:-------------|:-----------|:-----------|:-----------------|:-------------|:-----------|:-----------|:-----------------|:-------------|:-----------|:-----------|:-----------------|
| A_k20       | 60.0         | 32.0       | -28.0      | 25 (6.6)         | 45.0         | 26.7       | -18.3      | 15 (4.1)         | 50.0         | 63.6       | +13.6      | 11 (3.1)         |
| A_k40       | 60.0         | 42.1       | -17.9      | 19 (5.0)         | 45.0         | 46.2       | +1.2       | 13 (3.5)         | 50.0         | 50.0       | +0.0       | 12 (3.3)         |
| B_k20       | 60.0         | 57.9       | -2.1       | 19 (5.0)         | 45.0         | 50.0       | +5.0       | 10 (2.7)         | 50.0         | 41.7       | -8.3       | 12 (3.3)         |
| B_k40       | 60.0         | 77.8       | +17.8      | 18 (4.8)         | 45.0         | 60.0       | +15.0      | 10 (2.7)         | 50.0         | 30.0       | -20.0      | 10 (2.8)         |
| C_k20       | 60.0         | 45.8       | -14.2      | 24 (6.4)         | 45.0         | 37.5       | -7.5       | 16 (4.3)         | 50.0         | 50.0       | +0.0       | 12 (3.3)         |
| C_k40       | 60.0         | 48.0       | -12.0      | 25 (6.6)         | 45.0         | 40.0       | -5.0       | 15 (4.1)         | 50.0         | 30.0       | -20.0      | 10 (2.8)         |
| D_k20       | 60.0         | 54.2       | -5.8       | 24 (6.4)         | 45.0         | 52.9       | +7.9       | 17 (4.6)         | 50.0         | 41.7       | -8.3       | 12 (3.3)         |
| D_k40       | 60.0         | 58.6       | -1.4       | 29 (7.7)         | 45.0         | 47.4       | +2.4       | 19 (5.2)         | 50.0         | 35.7       | -14.3      | 14 (3.9)         |
| E_k20       | 60.0         | 47.1       | -12.9      | 17 (4.5)         | 45.0         | 66.7       | +21.7      | 12 (3.3)         | 50.0         | 33.3       | -16.7      | 9 (2.5)          |
| E_k40       | 60.0         | 45.5       | -14.5      | 22 (5.8)         | 45.0         | 58.3       | +13.3      | 12 (3.3)         | 50.0         | 55.6       | +5.6       | 9 (2.5)          |
| F_k20       | 60.0         | 51.6       | -8.4       | 31 (8.2)         | 45.0         | 52.6       | +7.6       | 19 (5.2)         | 50.0         | 50.0       | +0.0       | 14 (3.9)         |
| F_k40       | 60.0         | 41.4       | -18.6      | 29 (7.7)         | 45.0         | 47.4       | +2.4       | 19 (5.2)         | 50.0         | 50.0       | +0.0       | 14 (3.9)         |

**(b) Coverage extension: accuracy of the analog call when the three old signals do NOT agree** (non-overlapping, decisions in brackets)

| candidate   | 2010-26 h21   | 2010-26 h42   | 2010-26 h63   | 2016-26 h21   | 2016-26 h42   | 2016-26 h63   |
|:------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|
| A_k20       | 50.3 (161)    | 43.5 (92)     | 48.4 (62)     | 50.5 (103)    | 42.4 (59)     | 47.5 (40)     |
| A_k40       | 45.2 (168)    | 48.4 (93)     | 50.0 (64)     | 45.4 (108)    | 48.3 (60)     | 48.8 (41)     |
| B_k20       | 51.3 (156)    | 48.3 (89)     | 47.6 (63)     | 53.6 (97)     | 47.4 (57)     | 46.3 (41)     |
| B_k40       | 54.7 (161)    | 54.3 (92)     | 56.5 (62)     | 57.4 (101)    | 55.9 (59)     | 50.0 (40)     |
| C_k20       | 47.6 (168)    | 45.1 (91)     | 57.8 (64)     | 43.9 (107)    | 46.6 (58)     | 61.0 (41)     |
| C_k40       | 43.5 (168)    | 46.2 (93)     | 42.2 (64)     | 42.2 (109)    | 50.0 (60)     | 39.0 (41)     |
| D_k20       | 54.9 (162)    | 56.0 (91)     | 60.9 (64)     | 55.2 (105)    | 53.4 (58)     | 65.9 (41)     |
| D_k40       | 53.3 (165)    | 52.2 (92)     | 59.4 (64)     | 53.8 (106)    | 52.5 (59)     | 61.0 (41)     |
| E_k20       | 47.6 (164)    | 41.3 (92)     | 44.4 (63)     | 47.1 (104)    | 40.7 (59)     | 42.5 (40)     |
| E_k40       | 53.6 (166)    | 50.0 (92)     | 54.7 (64)     | 57.1 (105)    | 50.8 (59)     | 56.1 (41)     |
| F_k20       | 51.8 (168)    | 47.3 (93)     | 60.9 (64)     | 49.5 (109)    | 48.3 (60)     | 56.1 (41)     |
| F_k40       | 53.6 (168)    | 55.9 (93)     | 64.1 (64)     | 50.9 (108)    | 55.0 (60)     | 63.4 (41)     |

**(c) Paired difference on the weekly grid** (vote rule minus agreement rule, points, 95 % circular block bootstrap)

| candidate   | 2010-26 h21        | 2010-26 h42        | 2010-26 h63        | 2016-26 h21         | 2016-26 h42        | 2016-26 h63        |
|:------------|:-------------------|:-------------------|:-------------------|:--------------------|:-------------------|:-------------------|
| A_k20       | -2.1 [-11.6, +7.1] | -1.0 [-10.3, +7.0] | -6.8 [-17.8, +3.3] | +0.1 [-10.5, +10.7] | +1.7 [-7.0, +9.9]  | -6.5 [-16.6, +2.8] |
| A_k40       | -2.6 [-11.2, +5.7] | +0.5 [-8.2, +8.7]  | -2.9 [-11.8, +4.9] | +3.0 [-7.8, +13.1]  | +4.6 [-3.7, +13.3] | +0.3 [-8.6, +8.8]  |
| B_k20       | +2.5 [-5.5, +10.8] | -3.3 [-14.4, +5.8] | -5.5 [-17.1, +3.9] | +2.6 [-7.1, +12.1]  | -2.5 [-15.8, +8.8] | -1.1 [-13.4, +9.4] |
| B_k40       | +7.2 [+0.6, +14.0] | -2.9 [-12.2, +4.9] | +1.3 [-9.1, +10.5] | +8.1 [-0.7, +16.2]  | -0.4 [-10.3, +8.3] | +4.2 [-7.9, +14.2] |
| C_k20       | -5.1 [-13.6, +2.7] | -3.5 [-12.2, +5.3] | +0.7 [-8.6, +8.6]  | -9.5 [-20.6, +0.6]  | -3.4 [-13.1, +6.6] | +1.5 [-6.9, +9.2]  |
| C_k40       | +3.8 [-4.2, +11.3] | -4.3 [-12.1, +2.5] | -1.4 [-11.6, +6.3] | +2.8 [-7.3, +12.1]  | -0.2 [-8.5, +7.8]  | +3.9 [-6.2, +12.3] |
| D_k20       | +2.0 [-3.1, +7.4]  | -2.6 [-8.9, +2.7]  | -2.9 [-9.7, +2.6]  | +5.5 [-0.7, +12.3]  | +1.9 [-3.5, +7.7]  | +1.7 [-4.1, +7.4]  |
| D_k40       | +1.0 [-3.0, +5.4]  | -4.0 [-10.1, +1.0] | -2.4 [-8.8, +2.9]  | +3.1 [-1.9, +8.5]   | -1.3 [-5.8, +2.7]  | +0.6 [-4.3, +5.3]  |
| E_k20       | -7.2 [-16.4, +1.6] | -4.9 [-15.6, +4.2] | -0.3 [-10.2, +9.1] | -5.8 [-18.2, +6.2]  | +1.3 [-9.9, +11.6] | +7.0 [-3.2, +17.7] |
| E_k40       | -9.4 [-19.4, -0.1] | -5.8 [-16.2, +3.2] | +1.1 [-8.3, +9.6]  | -7.9 [-20.9, +4.9]  | -0.5 [-11.5, +9.2] | +7.0 [-2.0, +15.7] |
| F_k20       | +1.5 [-2.9, +6.1]  | -0.1 [-2.3, +2.1]  | -0.6 [-2.9, +1.5]  | +3.3 [-3.0, +10.2]  | +0.5 [-2.0, +3.1]  | +0.0 [-2.2, +2.1]  |
| F_k40       | -2.4 [-8.2, +3.3]  | +0.1 [-3.9, +3.7]  | -1.6 [-5.4, +1.4]  | +1.1 [-5.3, +7.5]   | +0.2 [-2.6, +2.7]  | -0.6 [-2.4, +1.2]  |

**Timing placebo and the Round 5 bar** (vote gain with the live call / the call 63 sessions stale / 126 sessions stale)

| candidate   | 2010-26 h21: gain / +63 / +126   | 2010-26 h42: gain / +63 / +126   | 2016-26 h21: gain / +63 / +126   | 2016-26 h42: gain / +63 / +126   | gain_3pts   | 6_per_year   | 2023_not_worse   | placebo   | ROUND5_BAR   |
|:------------|:---------------------------------|:---------------------------------|:---------------------------------|:---------------------------------|:------------|:-------------|:-----------------|:----------|:-------------|
| A_k20       | -11.0 / -9.5 / -2.3              | +5.4 / +5.4 / +10.5              | -8.9 / -2.6 / +5.4               | +5.4 / +8.6 / +7.7               | no          | no           | no               | no        | no           |
| A_k40       | -14.4 / -3.5 / -4.3              | -0.0 / +4.2 / +9.7               | -9.8 / -0.6 / -1.6               | -0.8 / +8.6 / +14.0              | no          | no           | no               | no        | no           |
| B_k20       | -2.2 / -2.8 / -3.6               | -0.3 / +7.4 / +1.8               | -2.6 / +3.6 / +5.2               | +1.1 / +10.0 / -4.8              | no          | no           | no               | no        | no           |
| B_k40       | +4.2 / -2.6 / -2.0               | +8.0 / +3.3 / +4.4               | +9.4 / +2.3 / +4.6               | +10.8 / +6.7 / +2.6              | yes         | no           | yes              | no        | no           |
| C_k20       | -5.2 / -7.1 / -6.5               | -4.4 / +6.0 / +5.5               | -5.7 / -1.2 / -5.1               | -5.4 / +14.2 / +13.6             | no          | no           | no               | no        | no           |
| C_k40       | -7.6 / -8.5 / -2.7               | -7.6 / +1.6 / -2.9               | -10.9 / -3.6 / +0.5              | -6.5 / +6.3 / +1.9               | no          | yes          | no               | no        | no           |
| D_k20       | -3.1 / -1.5 / -4.3               | -6.6 / +3.8 / +3.1               | +1.1 / +2.4 / -3.6               | -4.8 / +5.4 / +2.0               | no          | yes          | no               | no        | no           |
| D_k40       | -0.8 / -2.8 / -11.8              | -6.6 / +0.6 / +0.1               | +1.2 / +4.1 / -4.9               | -7.9 / +0.2 / -3.4               | no          | yes          | no               | no        | no           |
| E_k20       | -6.2 / -9.0 / -5.0               | +7.7 / +2.8 / +6.0               | -0.7 / -11.5 / +1.8              | +9.5 / -0.1 / +5.8               | no          | no           | no               | no        | no           |
| E_k40       | -11.8 / -2.4 / -5.1              | +4.1 / +5.4 / +0.4               | -11.8 / -1.0 / +0.7              | +5.2 / +3.6 / -1.0               | no          | no           | no               | no        | no           |
| F_k20       | -2.4 / -4.4 / -3.0               | +6.8 / +5.6 / -6.9               | +0.2 / -3.1 / +0.0               | +9.6 / +4.3 / -7.8               | no          | yes          | no               | no        | no           |
| F_k40       | -4.4 / -4.3 / -6.3               | +3.2 / +6.9 / +3.1               | -0.5 / -3.2 / -1.1               | +5.9 / +6.4 / +3.3               | no          | yes          | no               | no        | no           |

**Agreement rule AND near-unanimous analogs (>= 70 %) the same way** (non-overlapping accuracy, decisions)

| candidate   | 2010-26 h21   | 2010-26 h42   | 2010-26 h63   | 2016-26 h21   | 2016-26 h42   | 2016-26 h63   |
|:------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|
| A_k20       | 60.0 (10)     | 52.6 (19)     | 63.2 (19)     | 71.4 (7)      | 53.8 (13)     | 57.1 (14)     |
| A_k40       | 100.0 (1)     | 0.0 (1)       | 66.7 (3)      | 100.0 (1)     |               | 66.7 (3)      |
| B_k20       | 60.0 (10)     | 56.2 (16)     | 91.7 (12)     | 50.0 (4)      | 66.7 (9)      | 88.9 (9)      |
| B_k40       |               | 80.0 (5)      | 100.0 (1)     |               | 100.0 (4)     | 100.0 (1)     |
| C_k20       | 42.4 (33)     | 47.8 (23)     | 84.2 (19)     | 38.1 (21)     | 41.2 (17)     | 84.6 (13)     |
| C_k40       | 100.0 (4)     | 100.0 (1)     | 100.0 (2)     | 100.0 (2)     | 100.0 (1)     | 100.0 (1)     |
| D_k20       | 50.0 (42)     | 59.5 (37)     | 64.7 (34)     | 58.1 (31)     | 63.0 (27)     | 68.0 (25)     |
| D_k40       | 50.0 (4)      | 40.0 (10)     | 58.3 (12)     | 50.0 (4)      | 25.0 (4)      | 50.0 (8)      |
| E_k20       | 40.0 (20)     | 52.0 (25)     | 64.7 (17)     | 44.4 (9)      | 47.1 (17)     | 77.8 (9)      |
| E_k40       | 66.7 (3)      | 75.0 (4)      | 40.0 (5)      | 100.0 (1)     | 66.7 (3)      | 50.0 (4)      |
| F_k20       | 60.0 (60)     | 62.9 (70)     | 67.9 (53)     | 64.7 (34)     | 63.6 (44)     | 67.6 (34)     |
| F_k40       | 57.1 (14)     | 60.4 (48)     | 57.9 (38)     | 60.0 (10)     | 60.6 (33)     | 57.7 (26)     |

**Standalone timing placebo** (non-overlapping accuracy 2010-26 of the live call and of the call made 63 / 126 sessions stale)

| candidate   | h21: live / +63 / +126   | h42: live / +63 / +126   | h63: live / +63 / +126   |
|:------------|:-------------------------|:-------------------------|:-------------------------|
| A_k20       | 45.5 / 51.0 / 53.0       | 48.0 / 43.1 / 43.1       | 57.4 / 36.8 / 48.5       |
| A_k40       | 41.7 / 46.6 / 46.6       | 54.4 / 47.6 / 43.7       | 43.5 / 39.1 / 40.6       |
| B_k20       | 51.0 / 51.0 / 44.9       | 45.5 / 47.5 / 45.5       | 48.5 / 41.2 / 38.2       |
| B_k40       | 55.3 / 49.7 / 45.7       | 55.9 / 46.6 / 50.0       | 55.2 / 46.3 / 43.3       |
| C_k20       | 47.8 / 52.2 / 45.4       | 44.7 / 46.6 / 53.4       | 43.5 / 50.7 / 55.1       |
| C_k40       | 46.6 / 47.3 / 44.0       | 46.6 / 47.6 / 55.3       | 42.0 / 52.2 / 52.2       |
| D_k20       | 55.2 / 51.2 / 44.3       | 55.9 / 47.1 / 52.9       | 55.9 / 54.4 / 48.5       |
| D_k40       | 52.5 / 49.5 / 47.5       | 55.3 / 55.3 / 50.5       | 53.6 / 52.2 / 44.9       |
| E_k20       | 43.1 / 49.0 / 46.1       | 45.6 / 35.9 / 46.6       | 47.8 / 52.2 / 43.5       |
| E_k40       | 46.1 / 51.0 / 42.2       | 45.6 / 46.6 / 48.5       | 55.1 / 53.6 / 50.7       |
| F_k20       | 57.8 / 54.1 / 51.0       | 59.2 / 54.4 / 42.6       | 63.8 / 48.5 / 49.3       |
| F_k40       | 51.7 / 50.7 / 50.0       | 55.3 / 50.5 / 50.5       | 56.5 / 48.5 / 55.2       |

## 8. Selection by the declared rule and the record of the pick

Non-overlapping 21-session decisions 2006-2015 (F can forecast from 2009-11 only):

| candidate   | n 2006-15   | dec / yr   | accuracy   | Wilson lo   | Wilson hi   | net bp / decision   | share long   | eligible   | final   |
|:------------|:------------|:-----------|:-----------|:------------|:------------|:--------------------|:-------------|:-----------|:--------|
| A_k20       | 122.0       | 12.212     | 0.434      | 0.35        | 0.523       | -27.153             | 0.549        | True       | False   |
| A_k40       | 123.0       | 12.312     | 0.439      | 0.354       | 0.527       | -30.731             | 0.642        | True       | False   |
| B_k20       | 119.0       | 11.911     | 0.521      | 0.432       | 0.609       | -6.117              | 0.672        | True       | False   |
| B_k40       | 118.0       | 11.811     | 0.534      | 0.444       | 0.621       | 8.449               | 0.839        | True       | False   |
| C_k20       | 123.0       | 12.312     | 0.537      | 0.449       | 0.622       | 18.025              | 0.634        | True       | False   |
| C_k40       | 123.0       | 12.312     | 0.52       | 0.433       | 0.607       | -5.418              | 0.65         | True       | False   |
| D_k20       | 120.0       | 12.012     | 0.492      | 0.404       | 0.58        | 3.312               | 0.617        | True       | False   |
| D_k40       | 123.0       | 12.312     | 0.52       | 0.433       | 0.607       | 1.557               | 0.683        | True       | False   |
| E_k20       | 122.0       | 12.212     | 0.475      | 0.389       | 0.563       | 6.406               | 0.869        | True       | False   |
| E_k40       | 123.0       | 12.312     | 0.496      | 0.409       | 0.583       | -10.013             | 0.967        | True       | False   |
| F_k20       | 76.0        | 12.359     | 0.618      | 0.506       | 0.719       | 64.954              | 0.592        | True       | True    |
| F_k40       | 76.0        | 12.359     | 0.461      | 0.353       | 0.572       | -27.801             | 0.829        | True       | False   |

**Final: `F_k20`** (selected by the declared rule).

| mode       | period   | h21                | h21 net bp   | h42                | h42 net bp   | h63                | h63 net bp   |
|:-----------|:---------|:-------------------|:-------------|:-------------------|:-------------|:-------------------|:-------------|
| nonoverlap | 2006-15  | 61.8 [51-72] (76)  | +65          | 65.8 [50-79] (38)  | +133         | 57.7 [39-74] (26)  | +19          |
| nonoverlap | 2010-26  | 57.8 [51-64] (206) | +40          | 59.2 [50-68] (103) | +76          | 63.8 [52-74] (69)  | +120         |
| nonoverlap | 2016-26  | 53.0 [45-61] (132) | +15          | 53.0 [41-65] (66)  | +22          | 65.9 [51-78] (44)  | +80          |
| nonoverlap | 2023-26  | 50.0 [36-64] (46)  | -7           | 47.8 [29-67] (23)  | -49          | 73.3 [48-89] (15)  | +135         |
| weekly     | 2006-15  | 54.1 [42-66] (270) | +34          | 59.4 [43-74] (293) | +75          | 58.3 [38-76] (290) | +119         |
| weekly     | 2010-26  | 54.6 [47-62] (760) | +28          | 57.6 [47-67] (781) | +60          | 60.2 [48-71] (794) | +94          |
| weekly     | 2016-26  | 54.0 [45-63] (498) | +19          | 55.8 [43-68] (495) | +42          | 60.4 [45-74] (512) | +65          |
| weekly     | 2023-26  | 51.2 [36-66] (168) | -0           | 47.4 [28-68] (171) | +3           | 54.1 [30-77] (170) | -12          |
| monthly    | 2006-15  | 58.3 [46-70] (60)  | +49          | 58.0 [42-73] (69)  | +90          | 57.4 [37-75] (68)  | +131         |
| monthly    | 2010-26  | 56.0 [49-63] (175) | +27          | 56.4 [46-66] (179) | +66          | 59.0 [47-70] (188) | +80          |
| monthly    | 2016-26  | 54.3 [45-63] (116) | +12          | 55.0 [42-67] (111) | +43          | 59.8 [45-73] (122) | +47          |
| monthly    | 2023-26  | 53.8 [39-68] (39)  | +11          | 47.4 [27-68] (38)  | +10          | 53.8 [29-77] (39)  | -44          |

By year (non-overlapping stream started in 2010):

| year   | right / n, h21   | right / n, h42   | right / n, h63   |
|:-------|:-----------------|:-----------------|:-----------------|
| 2010   | 9 / 13           | 6 / 7            | 4 / 5            |
| 2011   | 5 / 12           | 3 / 6            | 2 / 4            |
| 2012   | 8 / 12           | 4 / 6            | 2 / 4            |
| 2013   | 10 / 12          | 3 / 6            | 3 / 4            |
| 2014   | 10 / 13          | 5 / 6            | 2 / 4            |
| 2015   | 7 / 12           | 5 / 6            | 2 / 4            |
| 2016   | 7 / 12           | 3 / 7            | 1 / 4            |
| 2017   | 9 / 12           | 4 / 6            | 4 / 4            |
| 2018   | 4 / 13           | 2 / 6            | 3 / 5            |
| 2019   | 5 / 12           | 3 / 6            | 2 / 4            |
| 2020   | 8 / 13           | 4 / 6            | 2 / 4            |
| 2021   | 7 / 12           | 3 / 6            | 4 / 4            |
| 2022   | 7 / 12           | 5 / 6            | 2 / 4            |
| 2023   | 6 / 12           | 2 / 7            | 2 / 4            |
| 2024   | 6 / 13           | 4 / 6            | 3 / 4            |
| 2025   | 6 / 12           | 2 / 6            | 3 / 4            |
| 2026   | 5 / 9            | 3 / 4            | 3 / 3            |

**Protocol table (weekly-tranche books at 1.2 pips, net Sharpe)**

| variant          | 2010-2015   | 2016-2022   | 2010-2026   | 2016-2026   | 2023-2026   | t 2010-26   | deflated-Sharpe p   | final   |
|:-----------------|:------------|:------------|:------------|:------------|:------------|:------------|:--------------------|:--------|
| A_k20            | -0.07       | -0.03       | -0.13       | -0.18       | -0.44       | -0.56       | 0.99                |         |
| A_k40            | -0.62       | -0.35       | -0.45       | -0.33       | -0.27       | -1.88       | 1.0                 |         |
| B_k20            | -0.0        | 0.23        | 0.12        | 0.23        | 0.22        | 0.5         | 0.88                |         |
| B_k40            | 0.09        | 0.37        | 0.28        | 0.46        | 0.62        | 1.18        | 0.69                |         |
| C_k20            | 0.1         | -0.45       | -0.24       | -0.53       | -0.74       | -0.98       | 1.0                 |         |
| C_k40            | -0.18       | -0.37       | -0.24       | -0.28       | -0.07       | -0.98       | 1.0                 |         |
| D_k20            | 0.14        | 0.85        | 0.42        | 0.65        | 0.28        | 1.77        | 0.46                |         |
| D_k40            | 0.11        | 0.83        | 0.36        | 0.59        | 0.1         | 1.52        | 0.56                |         |
| E_k20            | -0.24       | -0.39       | -0.27       | -0.3        | -0.12       | -1.1        | 1.0                 |         |
| E_k40            | -0.4        | -0.43       | -0.33       | -0.29       | -0.02       | -1.39       | 1.0                 |         |
| F_k20            | 0.65        | 0.63        | 0.51        | 0.42        | -0.01       | 2.14        | 0.32                | FINAL   |
| F_k20_cost0.6    | 0.66        | 0.66        | 0.53        | 0.45        | 0.01        | 2.22        | 0.29                |         |
| F_k20_daily_sign | 0.18        | 0.06        | 0.03        | -0.08       | -0.36       | 0.11        | 0.94                |         |
| F_k40            | -0.12       | 0.75        | 0.13        | 0.35        | -0.49       | 0.56        | 0.87                |         |

Hit rate of the delivered daily stream (active sessions):

| period   | active_sessions   | share_net_positive   | share_correct_sign   |
|:---------|:------------------|:---------------------|:---------------------|
| 2006-26  | 3936              | 0.503                | 0.505                |
| 2010-26  | 3898              | 0.504                | 0.506                |
| 2016-26  | 2530              | 0.496                | 0.499                |
| 2023-26  | 890               | 0.488                | 0.491                |

**Daily incremental test** (EW combination, walk-forward weights):

| combo                     | period    | sharpe   | t     |
|:--------------------------|:----------|:---------|:------|
| weak_signals+regime_trend | 2010-2026 | 0.563    | 2.347 |
| weak_signals+regime_trend | 2016-2026 | 0.636    | 2.128 |
| weak_signals+regime_trend | 2023-2026 | 0.356    | 0.708 |
| +analogs                  | 2010-2026 | 0.58     | 2.417 |
| +analogs                  | 2016-2026 | 0.629    | 2.103 |
| +analogs                  | 2023-2026 | 0.26     | 0.517 |

Daily P&L correlation of the final stream with `weak_signals` 0.21, with `regime_trend` 0.57.

## 9. Diagnostics (never selected from)

**Mahalanobis distance and the kernel-weighted vote** (non-overlapping accuracy in %, 2010-26; Euclidean k-NN repeated for comparison)

| state   | k   | h21 Euclid   | h21 Mahalanobis   | h21 kernel   | h42 Euclid   | h42 Mahalanobis   | h42 kernel   | h63 Euclid   | h63 Mahalanobis   | h63 kernel   |
|:--------|:----|:-------------|:------------------|:-------------|:-------------|:------------------|:-------------|:-------------|:------------------|:-------------|
| A       | 20  | 45.5         | 45.8              | 48.6         | 48.0         | 43.1              | 51.0         | 57.4         | 46.4              | 59.4         |
| A       | 40  | 41.7         | 49.5              |              | 54.4         | 50.5              |              | 43.5         | 46.4              |              |
| B       | 20  | 51.0         | 56.9              | 48.6         | 45.5         | 49.0              | 43.3         | 48.5         | 50.7              | 47.8         |
| B       | 40  | 55.3         | 46.4              |              | 55.9         | 45.1              |              | 55.2         | 49.3              |              |
| C       | 20  | 47.8         | 49.8              | 52.4         | 44.7         | 44.7              | 46.2         | 43.5         | 46.4              | 50.7         |
| C       | 40  | 46.6         | 42.2              |              | 46.6         | 46.6              |              | 42.0         | 44.9              |              |
| D       | 20  | 55.2         | 56.4              | 53.4         | 55.9         | 51.0              | 57.7         | 55.9         | 49.3              | 55.1         |
| D       | 40  | 52.5         | 56.9              |              | 55.3         | 51.5              |              | 53.6         | 56.5              |              |
| E       | 20  | 43.1         | 44.1              | 46.6         | 45.6         | 47.6              | 47.1         | 47.8         | 55.1              | 52.2         |
| E       | 40  | 46.1         | 43.4              |              | 45.6         | 49.5              |              | 55.1         | 46.4              |              |
| F       | 20  | 57.8         | 60.2              | 56.7         | 59.2         | 57.3              | 57.7         | 63.8         | 55.1              | 65.2         |
| F       | 40  | 51.7         | 47.8              |              | 55.3         | 52.9              |              | 56.5         | 55.1              |              |

**Long library (analogs from 1990, synthetic DEM euro before 1999, proxies as stated) and the other-era replication 1997-2005**

| state   | k   | 1997-05 h21   | 1997-05 h42   | 1997-05 h63   | 2006-26 h21   | 2006-26 h42   | 2006-26 h63   | 2010-26 h21   | 2010-26 h42   | 2010-26 h63   | main lib 2010-26 h21   | main lib 2010-26 h42   | main lib 2010-26 h63   |
|:--------|:----|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:--------------|:-----------------------|:-----------------------|:-----------------------|
| A       | 20  | 43.5 (108)    | 56.4 (55)     | 62.2 (37)     | 46.0          | 48.8          | 48.2          | 45.5          | 47.1          | 48.5          | 45.5                   | 48.0                   | 57.4                   |
| A       | 40  | 44.5 (110)    | 52.7 (55)     | 54.1 (37)     | 48.6          | 48.8          | 50.6          | 48.3          | 51.0          | 49.3          | 41.7                   | 54.4                   | 43.5                   |
| B       | 20  | 51.5 (101)    | 50.9 (55)     | 51.4 (37)     | 50.0          | 52.8          | 47.6          | 50.3          | 51.5          | 50.7          | 51.0                   | 45.5                   | 48.5                   |
| B       | 40  | 50.5 (107)    | 60.7 (56)     | 56.8 (37)     | 52.6          | 50.0          | 49.4          | 52.8          | 44.1          | 54.4          | 55.3                   | 55.9                   | 55.2                   |
| C       | 20  | 45.0 (109)    | 50.9 (55)     | 40.5 (37)     | 52.8          | 47.2          | 54.1          | 50.7          | 50.5          | 52.9          | 47.8                   | 44.7                   | 43.5                   |
| C       | 40  | 51.8 (110)    | 45.5 (55)     | 45.9 (37)     | 48.6          | 51.6          | 51.8          | 46.6          | 47.6          | 50.7          | 46.6                   | 46.6                   | 42.0                   |

## 10. `explain(date)`: the current reading

`explain()` for the session closing 2026-11-06 (EUR/USD 1.1139); full output in `analogs_latest.json`. For each state: the state today (value, z against the library before this year), the 10 nearest analog dates with the 21 / 42 / 63-session return that followed, P(up) from the 10 / 20 / 40 nearest with the number of independent episodes and a Wilson interval on EPISODES, the kernel probability, the library base rate, the episode list, and the out-of-sample record of that state's call.

| state                             | P(up) h21 (k=20)   | P(up) h42 (k=20)   | P(up) h63 (k=20)   | episodes   | OOS accuracy of this call 2010-26 (21 / 42 / 63)   |
|:----------------------------------|:-------------------|:-------------------|:-------------------|:-----------|:---------------------------------------------------|
| A policy / rates                  | 70 % [41-89]       | 75 % [46-91]       | 65 % [37-86]       | 11         | 46 / 48 / 57                                       |
| B macro (inflation, unemployment) | 60 % [23-88]       | 65 % [26-91]       | 70 % [30-93]       | 5          | 51 / 46 / 48                                       |
| C market                          | 70 % [43-88]       | 60 % [34-81]       | 50 % [26-74]       | 13         | 48 / 45 / 44                                       |
| D positioning                     | 35 % [15-62]       | 50 % [25-75]       | 30 % [12-58]       | 12         | 55 / 56 / 56                                       |
| E union A-D, 4 PCs                | 65 % [34-87]       | 45 % [19-74]       | 60 % [30-84]       | 9          | 43 / 46 / 48                                       |
| F agreement-rule inputs           | 50 % [27-73]       | 45 % [24-69]       | 45 % [24-69]       | 15         | 58 / 59 / 64                                       |

**The 10 most similar moments, state B (macro (inflation, unemployment))** - today: US CPI y/y (%) 3.7173; US CPI y/y, 6-month change 0.4313; euro-area HICP y/y (%) 3.7505; HICP y/y, 6-month change 1.2168; US unemployment (%) 4.2; US unemployment, 6-month change -0.1; euro-area unemployment (%) 6.6; euro-area unemployment, 6-month change 0.1

| rank   | analog date   | distance   | EUR/USD then   | next 21 s. %   | next 42 s. %   | next 63 s. %   |
|:-------|:--------------|:-----------|:---------------|:---------------|:---------------|:---------------|
| 1      | 2026-05-22    | 0.597      | 1.1606         | -1.55          | -1.79          | 0.6            |
| 2      | 2026-07-22    | 0.739      | 1.1408         | 2.32           | 0.65           | -1.73          |
| 3      | 2026-06-22    | 0.895      | 1.1427         | -0.24          | 2.15           | 0.43           |
| 4      | 2008-06-05    | 0.907      | 1.5583         | 0.8            | -0.06          | -7.08          |
| 5      | 2026-04-22    | 1.042      | 1.1708         | -0.77          | -2.07          | -2.58          |
| 6      | 2008-05-06    | 1.056      | 1.5534         | -0.68          | 1.05           | 0.21           |
| 7      | 2008-07-07    | 1.241      | 1.5725         | -1.74          | -8.14          | -13.04         |
| 8      | 2024-06-24    | 1.26       | 1.0733         | 1.11           | 3.79           | 3.91           |
| 9      | 2008-02-05    | 1.288      | 1.4648         | 4.13           | 6.83           | 5.18           |
| 10     | 2007-12-06    | 1.308      | 1.464          | 0.47           | -0.05          | 4.94           |

Episodes behind the 20 nearest: 2007-12-06..2008-08-05 (7); 2024-06-24..2024-06-24 (1); 2025-02-05..2025-06-04 (4); 2025-10-22..2026-01-21 (4); 2026-04-22..2026-07-22 (4).

**The 10 most similar moments, state A (policy / rates)** - today: Fed phase (-1 cutting, 0 hold, +1 hiking) 1.0; ECB phase (-1 cutting, 0 hold, +1 hiking) 1.0; policy gap: ECB deposit - Fed target (pp) -1.375; policy gap, 6-month change (pp) 0.25; US 2y - Fed target (pp) 0.705; EA - US 2y spread (pp) -1.6216; 2y spread, 3-month change (pp) -0.0924

| rank   | analog date   | distance   | EUR/USD then   | next 21 s. %   | next 42 s. %   | next 63 s. %   |
|:-------|:--------------|:-----------|:---------------|:---------------|:---------------|:---------------|
| 1      | 2022-12-09    | 1.307      | 1.0532         | 1.86           | 1.82           | 0.11           |
| 2      | 2026-08-05    | 1.459      | 1.1551         | 0.63           | -2.63          | -3.21          |
| 3      | 2023-03-09    | 1.493      | 1.0579         | 2.61           | 3.54           | 1.12           |
| 4      | 2026-06-22    | 1.542      | 1.1427         | -0.24          | 2.15           | 0.43           |
| 5      | 2023-10-19    | 1.565      | 1.0582         | 3.09           | 3.17           | 2.74           |
| 6      | 2023-07-07    | 1.58       | 1.0967         | 0.32           | -2.26          | -4.29          |
| 7      | 2006-03-24    | 1.64       | 1.2037         | 2.84           | 6.04           | 5.11           |
| 8      | 2023-09-20    | 1.664      | 1.0663         | -0.76          | 2.32           | 2.4            |
| 9      | 2017-02-24    | 1.724      | 1.0561         | 2.82           | 3.41           | 5.99           |
| 10     | 2000-03-20    | 1.733      | 0.971          | -2.43          | -8.47          | -1.87          |

Episodes behind the 20 nearest: 1999-11-11..1999-11-11 (1); 2000-03-20..2000-05-12 (2); 2005-12-13..2005-12-13 (1); 2006-03-24..2006-06-29 (3); 2017-01-24..2017-06-14 (4); 2017-10-02..2017-10-02 (1); 2018-02-12..2018-02-12 (1); 2022-12-09..2022-12-09 (1); 2023-03-09..2023-03-09 (1); 2023-07-07..2023-10-19 (3); 2026-06-22..2026-08-05 (2).

**The 10 most similar moments, state F (agreement-rule inputs)** - today: cot_z52 (store) -2.0469; 20-day change of the 2y spread 0.0953; house macro score 0.0961

| rank   | analog date   | distance   | EUR/USD then   | next 21 s. %   | next 42 s. %   | next 63 s. %   |
|:-------|:--------------|:-----------|:---------------|:---------------|:---------------|:---------------|
| 1      | 2011-10-20    | 0.183      | 1.3777         | -1.85          | -5.83          | -7.86          |
| 2      | 2018-12-05    | 0.226      | 1.1344         | 0.44           | 0.8            | -0.32          |
| 3      | 2025-01-10    | 0.231      | 1.024          | 0.64           | 6.39           | 6.71           |
| 4      | 2026-07-29    | 0.285      | 1.146          | 1.65           | -0.61          | -2.52          |
| 5      | 2024-12-11    | 0.297      | 1.0493         | -2.44          | -1.8           | 3.94           |
| 6      | 2012-01-24    | 0.317      | 1.3035         | 1.62           | 1.24           | 1.4            |
| 7      | 2007-06-27    | 0.396      | 1.3454         | 2.11           | 1.64           | 4.55           |
| 8      | 2007-12-18    | 0.4        | 1.4416         | 1.43           | 1.66           | 8.03           |
| 9      | 2019-04-09    | 0.414      | 1.1264         | -0.63          | 0.11           | -0.36          |
| 10     | 2007-09-17    | 0.491      | 1.3862         | 2.23           | 5.55           | 5.43           |

Episodes behind the 20 nearest: 2005-12-16..2005-12-16 (1); 2007-06-27..2007-09-17 (2); 2007-12-18..2007-12-18 (1); 2008-09-15..2008-09-15 (1); 2011-10-20..2012-01-24 (3); 2014-12-01..2014-12-01 (1); 2015-04-13..2015-04-13 (1); 2018-12-05..2019-01-09 (2); 2019-04-09..2019-04-09 (1); 2021-09-21..2021-09-21 (1); 2021-12-23..2021-12-23 (1); 2022-09-19..2022-09-19 (1); 2024-03-08..2024-03-08 (1); 2024-12-11..2025-01-10 (2); 2026-07-29..2026-07-29 (1).

How to use it in the weekly outlook: call `eurusd.arms.analogs.explain()` (about a second after the imports; it needs the current feature store and
`data/macro/policy_state.csv`, which arm T's `run()` rebuilds) or `PYTHONPATH=src python -m eurusd.arms.analogs latest` to rewrite `analogs_latest.json`.
Show the analog dates and what followed as a narrative panel ("the last times the macro picture looked like this were spring 2008 and mid-2024"), always
with `n_episodes` and the out-of-sample record that the function returns next to each state. Do not print the analog share as a probability of direction:
section 4 shows it is not one.

## What helped, what did not
* Helped: nothing new. Positioning and the house score reappear when they are the state (D, F), weaker than their plain signs.
* Did not help: the policy phase of both central banks, the policy gap and its change, the 2y spread and its change, inflation and unemployment levels and
  changes on both sides, the market state (trend, volatility, VIX, relative equities, oil), their union in principal components; a larger k; Mahalanobis
  distance; kernel weighting; nine more years of library; demanding unanimity; counting episodes instead of analogs.
