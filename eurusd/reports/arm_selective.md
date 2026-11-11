# Arm N: selective prediction (`selective`) - how often can a call be right, and is it real?

Code `src/eurusd/arms/selective.py` (`run(cost_pips=1.2)`; `python -m eurusd.arms.selective` runs everything in 2 minutes,
`... selective report` rebuilds this file). Results in `experiments/results/arms/`: `selective_positions.parquet` (decision stream
of the final rule: `pos`, `fwd_bp`, `net_bp`, `prob`, `gross_bp`, `hit`, `hold`), `selective_daily_positions.parquet` (the same rule
as a daily weekly-tranche book - use THIS one for stacking), `selective_p60_positions.parquet` / `selective_p60_daily_positions.parquet`
(the pick among the probability calls), `selective_report.csv` (protocol table of all 12 candidates, `variant`, `final`),
`selective_accuracy_coverage.csv` (every target x model x rule x mode x period), `selective_path_calibration.csv`,
`selective_candidates.csv`, `selective_expectancy.csv`, `selective_reliability.csv`, `selective_leakchecks.csv`,
`selective_leak_features.csv`, `selective_incremental.csv`, log `logs/selective.log`.

Scope as re-set by the owner during the run: POSITION trading. Primary horizons 10 / 21 / 42 / 63 sessions (sign of the forward
return and symmetric 2- and 3-ATR barriers), path events over 10 / 21 sessions; 1- and 5-session direction are diagnostics, the
intraday 13:00 item was dropped. The whole protocol, the 12 candidates and the selection rule are in the module docstring and were
written before the first result. Four things were ADDED after the first run and are marked as such: a conservative effective
sample size, the non-overlapping stream for the fixed selectors, a timing placebo, and the second pick (same rule, probability
calls only). None of them changes which rule is selected.

## Verdict
1. **Direction, as the owner asked for it (a calibrated probability, speak only at P >= 60 %): no.** When the averaged model says
   "at least 60 %" it is right 25 % (n=4), 46 % (n=37), 49 % (n=169) and 51 % (n=226) of the time on the 10 / 21 / 42 / 63-session
   sign, and 40-82 % on the eight barrier targets with nothing systematic (weekly decisions, 2010-26). The logistic model on the
   macro + positioning + calendar blocks is anti-informative out of sample at long horizons (its 10 % most confident calls: 22 %
   right at 42 sessions, 15 % at 63): it fits macro LEVELS and a base rate from 2003-09 that did not persist. Only the house score
   alone is roughly calibrated at 42-63 sessions (P >= 60 % calls right 59-63 %, n 219-407 weekly), and the non-overlapping
   stream of those same calls gives 51-63 %. The pick of the declared rule among the ten probability calls,
   `tb63_3atr_avg_p60`, shows 62 % on weekly decisions and **50 % (n=102, +4 bp) on its non-overlapping stream**; it was 100 % long
   in 2010-15 and earns its record in 2021-22. It is not a 60 % call. Its weekly-tranche book does clear the round-3 bar on paper
   (stand-alone net Sharpe 0.39 / 0.78 / 0.51, three-way combination 0.75 against 0.64 on 2016-26, correlation 0.19 / 0.15 with
   the two live streams), but 2010-15 was 0.13, the deflated-Sharpe p is 0.51, the placebo p 0.05, and its seven sibling
   probability calls sit between 25 % and 82 %. I do not recommend it; at most a paper forward test under its own name.
2. **Direction, what is real: the known macro + positioning drift, and its hit rate rises with the HOLDING PERIOD, not with model
   confidence.** The raw sign of the house score is right 53 / 56 / 58 / 60 % of the time at 10 / 21 / 42 / 63 sessions
   (non-overlapping 53 / 55 / 61 / 64 %). That is exactly what a Sharpe of 0.56 implies: accuracy = Phi(Sharpe x sqrt(h/252)) =
   54 / 56 / 59 / 61 %. Requiring positioning, the 2y-spread trend and the house score to agree (44 % of weeks) lifts it to
   **57 / 59 / 65 / 67 %** (non-overlapping 56 / 59 / 61 / 72 %), +29 / +46 / +108 / +153 bp per decision after costs, timing
   placebo p 0.018 / 0.005 / 0.007 at 21 / 42 / 63 sessions. So a >= 60 % directional accuracy does exist out of sample, at 42-63-session
   holds, 23 weekly decisions a year (4-5 non-overlapping positions a year), positive expectancy.
   * 2016-26: holds (55 / 57 / 63 / 67 %; non-overlapping 53 / 57 / 59 / 71 %).
   * 2023-26: **not confirmed** (57 / 55 / 47 / 53 %; non-overlapping 54 / 60 / 45 / 50 % on 63 / 35 / 20 / 14 decisions). The
     intervals are 25-60 points wide: this period can neither confirm 60 % nor reject it.
   * Statistically: the conservative interval of the agreement rule includes the majority base rate at every horizon
     (e.g. 63 sessions: 67 % [49-81]); only the non-overlapping 63-session stream excludes it (72 % [60-82], n=61). The 387 weekly
     decisions of the final rule are 27 directional episodes in 17 years.
   * More selectivity (the calibrated house score at 25 / 10 / 5 % coverage) raises weekly accuracy at 63 sessions to 67 / 70 / 71 %
     (3-ATR barrier: 71 / 70 / 81 %), but the non-overlapping streams do not confirm a rising curve (54 / 63 / 67 % on 50 / 30 / 18
     decisions; barrier 55 / 66 / 60 %), at 10 % coverage only 2 of 12 targets have a non-overlapping lower bound above the base
     rate, none under the conservative weekly interval, and after 2023 the same cells are 38-50 % on the 42- and 63-session sign
     and 52-73 % on the barriers with 19-66 decisions each. Suggestive, not established.
3. **Final by the declared rule: `sign21_agree3`** (21-session call when positioning, spread trend and house score agree).
   2010-26: 387 decisions, 23 a year, **59.4 % right** (interval 52-66 Newey-West, 49-69 conservative; non-overlapping 59 % [51-66],
   n=156), 59.2 % with positive net P&L, average win +185 bp / loss -156 bp, **+46 bp per decision after costs**, hold 21 sessions.
   2016-26: 57.2 % [44-69], +38 bp. 2023-26: 54.5 % [33-74], +27 bp (non-overlapping 60 % [44-74], n=35). Book Sharpe
   0.52 / 0.51 / 0.43 (t 2.17 / 1.72 / 0.85), deflated-Sharpe p 0.31 for 12 candidates. Its own track record before each test year
   is 56-61 % from 2012 on (table in section 6), i.e. it is a "58 % call", not a 60 % one. **It is not new information**: daily
   P&L correlation 0.63 with `regime_trend` and 0.43 with `weak_signals`; adding it moves the combination from 0.64 to 0.64 on
   2016-26 (0.636 -> 0.641; 2010-26 0.56 -> 0.57, 2023-26 0.36 -> 0.40). It clears the round-3 bar by 0.005 Sharpe, which is
   nothing; I do not recommend a new stream.
4. **Path / level events: yes, 60-90 % is real, calibrated and unchanged after 2023 - and it carries no expectancy.** Predicted
   and realised frequencies agree to 1-3 points in every period and to within 5 points inside each volatility regime (table
   below, section 4).
   Example for a position trade: a level 2 ATR away is not touched within 10 sessions 69 % of the time (predicted 68 %), 3 ATR
   86 % (86 %); within 21 sessions 52 % and 71 %. The gain over the naive unconditional rule is modest (Brier skill 5-10 % for
   no-touch, 22-32 % for the next-session range); the value is the calibration. The only spot expression (fade a touch of the
   level, close at the end of the window) earns +0.2 to +3.9 bp per decision at these levels with t at most 1.2, and is negative
   after costs in the 1-session version (t down to -4.9). These numbers size stops and targets; they are not an edge.
5. **What the 60-80 % target means in this data.** With the edge that exists (Sharpe about 0.5), 60 % needs a holding period of
   about a quarter. 70 % at a 63-session hold would need a Sharpe of 1.05 and 80 % a Sharpe of 1.7; at a 21-session hold 60 %
   already needs 0.9. Nothing here supports that. A system that shows 70-80 % on multi-week direction is either quoting a path
   event (stop not hit), an asymmetric stop/target, or a handful of overlapping decisions from one trend.

**Direction: accuracy % [95 % interval] n; W = weekly decisions (conservative interval), N = non-overlapping stream (Wilson)**

*2010-26*

|   hold (sessions) | always on: raw house-score sign (100 %)   | three-way agreement (44 %)              | calibrated house score, 25 %            | 10 %                                  | 5 %                                   |
|------------------:|:------------------------------------------|:----------------------------------------|:----------------------------------------|:--------------------------------------|:--------------------------------------|
|                10 | W 53 [49-58] n=873 / N 53 [49-58] n=437   | W 57 [50-64] n=390 / N 56 [50-62] n=291 | W 56 [47-65] n=212 / N 55 [48-62] n=195 | W 53 [39-66] n=96 / N 47 [37-57] n=96 | W 54 [37-71] n=59 / N 52 [40-64] n=65 |
|                21 | W 56 [49-62] n=870 / N 55 [48-61] n=208   | W 59 [49-69] n=387 / N 59 [51-66] n=156 | W 56 [42-69] n=199 / N 57 [47-66] n=111 | W 57 [37-76] n=89 / N 59 [45-72] n=49 | W 63 [36-84] n=49 / N 44 [28-61] n=32 |
|                42 | W 58 [48-67] n=866 / N 61 [51-69] n=104   | W 65 [50-77] n=383 / N 61 [50-70] n=89  | W 62 [42-79] n=184 / N 50 [39-61] n=72  | W 59 [29-84] n=74 / N 45 [30-62] n=33 | W 69 [29-92] n=42 / N 55 [35-73] n=22 |
|                63 | W 60 [49-71] n=862 / N 64 [52-74] n=69    | W 67 [49-81] n=383 / N 72 [60-82] n=61  | W 67 [42-85] n=195 / N 54 [40-67] n=50  | W 70 [35-91] n=87 / N 63 [46-78] n=30 | W 71 [26-95] n=45 / N 67 [44-84] n=18 |

*2016-26*

|   hold (sessions) | always on: raw house-score sign (100 %)   | three-way agreement (44 %)              | calibrated house score, 25 %            | 10 %                                  | 5 %                                   |
|------------------:|:------------------------------------------|:----------------------------------------|:----------------------------------------|:--------------------------------------|:--------------------------------------|
|                10 | W 52 [46-58] n=562 / N 52 [46-58] n=281   | W 55 [46-63] n=246 / N 53 [46-61] n=178 | W 58 [47-67] n=172 / N 56 [48-64] n=140 | W 56 [42-70] n=87 / N 52 [41-63] n=79 | W 58 [40-74] n=55 / N 53 [40-65] n=57 |
|                21 | W 54 [45-62] n=559 / N 51 [43-59] n=133   | W 57 [44-69] n=243 / N 57 [47-67] n=96  | W 57 [42-71] n=172 / N 61 [51-71] n=83  | W 57 [36-76] n=84 / N 61 [47-74] n=44 | W 63 [36-84] n=49 / N 42 [26-59] n=31 |
|                42 | W 57 [45-68] n=555 / N 61 [49-71] n=66    | W 63 [45-78] n=239 / N 59 [46-71] n=56  | W 63 [41-81] n=157 / N 47 [34-61] n=49  | W 58 [28-83] n=71 / N 44 [28-63] n=27 | W 69 [29-92] n=42 / N 52 [32-72] n=21 |
|                63 | W 62 [47-74] n=551 / N 61 [47-74] n=44    | W 67 [45-84] n=239 / N 71 [55-83] n=38  | W 68 [42-87] n=167 / N 56 [39-71] n=34  | W 69 [33-91] n=84 / N 60 [41-77] n=25 | W 71 [26-95] n=45 / N 65 [41-83] n=17 |

*2023-26*

|   hold (sessions) | always on: raw house-score sign (100 %)   | three-way agreement (44 %)            | calibrated house score, 25 %          | 10 %                                  | 5 %                                   |
|------------------:|:------------------------------------------|:--------------------------------------|:--------------------------------------|:--------------------------------------|:--------------------------------------|
|                10 | W 51 [41-61] n=198 / N 52 [42-61] n=99    | W 57 [42-71] n=80 / N 54 [42-66] n=63 | W 55 [39-70] n=69 / N 52 [39-65] n=52 | W 49 [28-70] n=37 / N 51 [36-67] n=35 | W 60 [31-83] n=20 / N 52 [33-71] n=23 |
|                21 | W 52 [38-66] n=195 / N 57 [43-70] n=47    | W 55 [33-74] n=77 / N 60 [44-74] n=35 | W 58 [35-78] n=69 / N 61 [44-75] n=33 | W 52 [22-80] n=33 / N 63 [41-81] n=19 | W 62 [24-89] n=21 / N 43 [21-67] n=14 |
|                42 | W 46 [28-66] n=191 / N 52 [33-71] n=23    | W 47 [20-75] n=73 / N 45 [26-66] n=20 | W 44 [17-74] n=66 / N 39 [20-61] n=18 | W 38 [10-77] n=37 / N 45 [21-72] n=11 | W 50 [11-89] n=22 / N 40 [17-69] n=10 |
|                63 | W 57 [33-78] n=187 / N 60 [36-80] n=15    | W 53 [21-84] n=73 / N 50 [27-73] n=14 | W 48 [16-82] n=63 / N 62 [36-82] n=13 | W 46 [10-86] n=35 / N 50 [24-76] n=10 | W 50 [8-92] n=20 / N 43 [16-75] n=7   |

**Path / level: probability that a level is NOT touched (one-sided), weekly samples**

|   window (sessions) | level                   |   predicted % | realised % 2010-26   | realised % 2016-26   | realised % 2023-26   |   Brier skill vs naive % | fade net bp / decision (t)   |
|--------------------:|:------------------------|--------------:|:---------------------|:---------------------|:---------------------|-------------------------:|:-----------------------------|
|                  10 | 2 x ATR14               |          68   | 68.6 [65-72]         | 68.9 [65-73]         | 70.5 [64-76]         |                      5.8 | +2.7 (+0.8)                  |
|                  10 | 3 x ATR14               |          85.9 | 86.5 [84-89]         | 86.7 [84-89]         | 87.6 [82-92]         |                      8.1 | +2.0 (+1.1)                  |
|                  21 | 2 x ATR14               |          51.7 | 51.9 [47-57]         | 51.9 [46-58]         | 51.5 [42-61]         |                      6.5 | +2.2 (+0.3)                  |
|                  21 | 3 x ATR14               |          70.2 | 71.2 [67-75]         | 70.8 [65-76]         | 68.5 [58-77]         |                      5.7 | +0.4 (+0.1)                  |
|                  10 | 0.75 x forecast vol (U) |          75.1 | 76.5 [74-79]         | 77.7 [74-81]         | 78.3 [72-83]         |                      5.7 | +3.0 (+1.1)                  |
|                  10 | 1 x forecast vol (U)    |          87.4 | 89.1 [87-91]         | 89.4 [87-92]         | 89.9 [85-93]         |                      9.7 | +1.2 (+0.7)                  |
|                  21 | 0.75 x forecast vol (U) |          76.1 | 77.4 [73-81]         | 77.8 [72-82]         | 75.4 [66-83]         |                      7   | +0.2 (+0.0)                  |
|                  21 | 1 x forecast vol (U)    |          86.7 | 88.4 [85-91]         | 88.7 [84-92]         | 90.0 [82-95]         |                      8.8 | +3.9 (+1.2)                  |

## Protocol notes, additions and what looked suspicious
* Walk-forward as in `wf.py`: for test year Y everything (house weights, logistic fit, Platt map, coverage thresholds, range
  and volatility models, the excursion distributions) uses rows whose label is known before Y-01-01. Label-known time is the
  close of session t+h exactly; the store's `label_end_1d` (close + 1 day) lets a Friday row into the training set one session
  early at a year boundary, so I did not use it.
* Costs: 1.2 pips per unit turnover. Per-decision P&L is charged a full round trip (2.4 pips, no netting); the books use
  `pnl_from_positions` (time exit, turnover netted) or 2.4 pips per tranche (stop/target exit). At 21-63-session holds costs are
  about 1 % of the average absolute move; 0.6 pips changes the final's Sharpe by 0.01-0.02.
* ADDED after the first run (not in the docstring): (a) conservative effective n = min(Newey-West n, decisions x 5 / holding
  period). The declared Newey-West n credits 192 independent decisions to 862 weekly 63-session calls where only 69
  non-overlapping periods exist, so it is too generous; every interval printed in this file is the conservative one unless
  labelled. (b) Non-overlapping stream for the fixed selectors. (c) Timing placebo. (d) The pick of the declared rule
  restricted to the ten probability calls, because the declared final turned out to be a fixed rule and the owner asked for a
  probability call. Selection is identical under the Newey-West and the conservative bound; under the bootstrap bound the
  probability pick would be `tb42_3atr_avg_p60` (56 % weekly, 2023-26 46 %), no better.
* Weekly and non-overlapping numbers differ by up to 16 points for the same rule (e.g. calibrated house score, 25 % coverage,
  3-ATR / 63 sessions: 71 % weekly, 55 % non-overlapping). Weekly sampling counts a long trend many times; with about 69
  independent 63-session periods in the whole out-of-sample span any single accuracy has roughly +-12 points of error. Quote
  the non-overlapping number when in doubt.
* Platt calibration with an intercept imports the training base rate: sign of the calibrated house probability is right 54 %
  at 63 sessions where the raw sign is right 60 %. For a drift-free asset the prior P(up) = 0.5 is better than the fitted one.
* The event selector is unreliable: the store's FOMC / ECB / NFP patterns also catch minutes, speeches and ADP (38-52 % of
  sessions are "event" sessions in 2010-23, 29-30 % in 2024-25 where the calendar is thinner). Quiet / volatile / event filters
  show no consistent effect on multi-week direction (section 3).
* Leak checks (section 7). Labels shuffled: 47.6-51.3 % on all weekly 21-session decisions for the three models, 43-54 % for the
  agreement rule, and not a single P >= 60 % call is issued. Look-ahead control (features from h sessions ahead): 86-88 % at
  21 sessions, 75 % on the 63-session barrier, so the harness would expose a leak. Features made 1 / 21 / 63 sessions older:
  the final rule gives 59.3 / 57.5 / 58.9 % against 59.4 %. A leak would vanish at lag 1; this does not, because the
  information is slow (52-week positioning z-score, 20-day spread trend, 27 directional episodes in 17 years). It does mean
  the calls are regime calls and the independent sample is small. Largest full-sample correlation of any input with the label:
  0.15 (cot_z52, 21-session sign), 0.22 (63-session barrier); none is a label in disguise.
* What helped: the holding period, and agreement of the three slow signals. What did not: the logistic model on the macro +
  positioning + calendar blocks, probability calibration, model confidence beyond the agreement rule, the trend-state filter
  (never better than agreement alone), the quiet / volatile / event filters.
* Variant count for deflation: 12 candidate rules. Diagnostics computed but not selected from: 14 targets x 3 models x 8 rules x
  2 evaluation modes, 4 x 7 selector cells x 2 modes, the path tables.

## 1. Targets
`up_share` = share of sessions 2003-2026 on which a long would have closed in profit; `resolved_share` = barrier hit before the time-out.
| target    | kind   |   h |   k_atr |    n |   up_share |   resolved_share |   avg_hold |   mean_abs_bp |
|:----------|:-------|----:|--------:|-----:|-----------:|-----------------:|-----------:|--------------:|
| sign1     | sign   |   1 |       0 | 6185 |      0.505 |          nan     |      1     |        41.376 |
| sign5     | sign   |   5 |       0 | 6181 |      0.504 |          nan     |      5     |        93.28  |
| sign10    | sign   |  10 |       0 | 6176 |      0.506 |          nan     |     10     |       132.107 |
| sign21    | sign   |  21 |       0 | 6165 |      0.5   |          nan     |     21     |       192.56  |
| sign42    | sign   |  42 |       0 | 6144 |      0.512 |          nan     |     42     |       276.364 |
| sign63    | sign   |  63 |       0 | 6123 |      0.518 |          nan     |     63     |       334.904 |
| tb10_2atr | tb     |  10 |       2 | 6176 |      0.506 |            0.615 |      7.291 |       123.472 |
| tb10_3atr | tb     |  10 |       3 | 6176 |      0.506 |            0.276 |      9.077 |       131.013 |
| tb21_2atr | tb     |  21 |       2 | 6165 |      0.513 |            0.888 |      9.866 |       152.859 |
| tb21_3atr | tb     |  21 |       3 | 6165 |      0.506 |            0.579 |     15.365 |       179.698 |
| tb42_2atr | tb     |  42 |       2 | 6144 |      0.521 |            0.993 |     10.751 |       165.501 |
| tb42_3atr | tb     |  42 |       3 | 6144 |      0.523 |            0.848 |     21.069 |       223.52  |
| tb63_2atr | tb     |  63 |       2 | 6123 |      0.522 |            0.999 |     10.827 |       166.543 |
| tb63_3atr | tb     |  63 |       3 | 6123 |      0.53  |            0.93  |     23.32  |       236.429 |

## 2. (A) Accuracy-coverage curves, direction
Cells: accuracy % [95 % interval] n decisions. Weekly tables: decisions every 5th session, overlapping holds; the interval is Wilson with the SMALLER of the Newey-West effective n and n x 5 / holding period (the conservative one; the Newey-West-only interval, the block bootstrap and every other column are in `selective_accuracy_coverage.csv`). Non-overlapping tables: plain Wilson.

**house model, weekly decisions, 2010-26**

| target    | cov100           | cov50            | cov25            | cov10           | cov5            |
|:----------|:-----------------|:-----------------|:-----------------|:----------------|:----------------|
| sign10    | 52 [47-57] n=873 | 53 [47-60] n=442 | 56 [47-65] n=212 | 53 [39-66] n=96 | 54 [37-71] n=59 |
| sign21    | 52 [46-59] n=870 | 53 [44-63] n=414 | 56 [42-69] n=199 | 57 [37-76] n=89 | 63 [36-84] n=49 |
| sign42    | 53 [44-63] n=866 | 60 [46-73] n=409 | 62 [42-79] n=184 | 59 [29-84] n=74 | 69 [29-92] n=42 |
| sign63    | 54 [42-65] n=862 | 62 [45-77] n=402 | 67 [42-85] n=195 | 70 [35-91] n=87 | 71 [26-95] n=45 |
| tb10_2atr | 51 [47-55] n=873 | 53 [47-58] n=430 | 55 [46-63] n=211 | 47 [35-60] n=93 | 45 [29-62] n=51 |
| tb10_3atr | 52 [47-56] n=873 | 53 [47-59] n=437 | 56 [47-65] n=211 | 52 [38-65] n=95 | 54 [37-71] n=57 |
| tb21_2atr | 51 [47-56] n=870 | 57 [50-63] n=385 | 60 [50-70] n=184 | 56 [39-71] n=75 | 62 [39-81] n=40 |
| tb21_3atr | 51 [45-57] n=870 | 56 [47-64] n=399 | 63 [50-74] n=187 | 57 [38-75] n=82 | 65 [36-86] n=40 |
| tb42_2atr | 52 [47-57] n=866 | 59 [51-66] n=388 | 63 [52-73] n=182 | 62 [44-77] n=76 | 66 [41-84] n=41 |
| tb42_3atr | 53 [46-60] n=866 | 63 [53-72] n=389 | 69 [54-82] n=173 | 69 [45-86] n=75 | 81 [46-96] n=37 |
| tb63_2atr | 53 [48-58] n=862 | 59 [51-66] n=380 | 63 [52-72] n=182 | 65 [47-80] n=74 | 69 [44-87] n=39 |
| tb63_3atr | 54 [47-61] n=862 | 65 [55-75] n=390 | 71 [56-83] n=184 | 70 [45-87] n=77 | 81 [46-96] n=37 |

**house model, weekly decisions, 2016-26**

| target    | cov100           | cov50            | cov25            | cov10           | cov5            |
|:----------|:-----------------|:-----------------|:-----------------|:----------------|:----------------|
| sign10    | 54 [48-60] n=562 | 57 [49-64] n=318 | 58 [47-67] n=172 | 56 [42-70] n=87 | 58 [40-74] n=55 |
| sign21    | 53 [45-62] n=559 | 54 [43-65] n=307 | 57 [42-71] n=172 | 57 [36-76] n=84 | 63 [36-84] n=49 |
| sign42    | 56 [44-67] n=555 | 60 [44-75] n=295 | 63 [41-81] n=157 | 58 [28-83] n=71 | 69 [29-92] n=42 |
| sign63    | 58 [43-71] n=551 | 63 [43-80] n=290 | 68 [42-87] n=167 | 69 [33-91] n=84 | 71 [26-95] n=45 |
| tb10_2atr | 52 [47-57] n=562 | 55 [48-62] n=312 | 56 [47-65] n=172 | 50 [37-63] n=84 | 49 [32-66] n=47 |
| tb10_3atr | 54 [48-59] n=562 | 56 [48-63] n=316 | 57 [47-67] n=171 | 55 [40-68] n=86 | 58 [40-75] n=53 |
| tb21_2atr | 52 [46-58] n=559 | 55 [47-63] n=290 | 58 [47-69] n=161 | 57 [40-72] n=72 | 62 [39-81] n=40 |
| tb21_3atr | 51 [44-59] n=559 | 55 [45-65] n=300 | 60 [47-73] n=164 | 56 [36-74] n=79 | 65 [36-86] n=40 |
| tb42_2atr | 53 [47-59] n=555 | 57 [49-66] n=289 | 62 [49-72] n=156 | 63 [45-78] n=73 | 66 [41-84] n=41 |
| tb42_3atr | 55 [47-64] n=555 | 62 [50-73] n=279 | 68 [51-81] n=148 | 68 [44-85] n=72 | 81 [46-96] n=37 |
| tb63_2atr | 53 [47-59] n=551 | 57 [48-65] n=287 | 62 [50-72] n=157 | 65 [46-80] n=71 | 69 [44-87] n=39 |
| tb63_3atr | 57 [48-66] n=551 | 66 [53-76] n=288 | 70 [54-83] n=159 | 69 [44-86] n=74 | 81 [46-96] n=37 |

**house model, weekly decisions, 2023-26**

| target    | cov100           | cov50            | cov25           | cov10           | cov5            |
|:----------|:-----------------|:-----------------|:----------------|:----------------|:----------------|
| sign10    | 57 [47-66] n=198 | 56 [43-68] n=114 | 55 [39-70] n=69 | 49 [28-70] n=37 | 60 [31-83] n=20 |
| sign21    | 52 [38-65] n=195 | 53 [35-70] n=116 | 58 [35-78] n=69 | 52 [22-80] n=33 | 62 [24-89] n=21 |
| sign42    | 47 [29-67] n=191 | 50 [26-73] n=111 | 44 [17-74] n=66 | 38 [10-77] n=37 | 50 [11-89] n=22 |
| sign63    | 52 [29-75] n=187 | 52 [24-79] n=107 | 48 [16-82] n=63 | 46 [10-86] n=35 | 50 [8-92] n=20  |
| tb10_2atr | 56 [48-64] n=198 | 57 [46-67] n=116 | 57 [42-70] n=69 | 50 [32-68] n=36 | 60 [35-81] n=20 |
| tb10_3atr | 57 [47-66] n=198 | 56 [44-68] n=114 | 55 [39-70] n=69 | 49 [29-69] n=37 | 58 [30-82] n=19 |
| tb21_2atr | 53 [44-63] n=195 | 57 [43-69] n=106 | 59 [43-74] n=64 | 65 [41-83] n=34 | 71 [41-90] n=21 |
| tb21_3atr | 51 [39-63] n=195 | 54 [38-69] n=111 | 56 [36-75] n=66 | 54 [28-78] n=37 | 67 [28-91] n=18 |
| tb42_2atr | 52 [42-62] n=191 | 58 [45-71] n=106 | 56 [39-72] n=64 | 59 [37-79] n=37 | 71 [41-90] n=24 |
| tb42_3atr | 50 [37-64] n=191 | 55 [37-72] n=105 | 52 [30-74] n=63 | 54 [26-79] n=39 | 68 [29-92] n=19 |
| tb63_2atr | 52 [42-62] n=187 | 57 [43-69] n=104 | 56 [39-71] n=63 | 63 [40-81] n=35 | 73 [41-91] n=22 |
| tb63_3atr | 51 [37-66] n=187 | 57 [38-74] n=105 | 52 [30-74] n=65 | 54 [26-80] n=39 | 68 [29-92] n=19 |

**house model, NON-OVERLAPPING decisions, 2010-26**

| target    | cov100           | cov50            | cov25            | cov10            | cov5            |
|:----------|:-----------------|:-----------------|:-----------------|:-----------------|:----------------|
| sign10    | 50 [46-55] n=437 | 49 [44-55] n=356 | 55 [48-62] n=195 | 47 [37-57] n=96  | 52 [40-64] n=65 |
| sign21    | 50 [43-57] n=208 | 50 [43-57] n=178 | 57 [47-66] n=111 | 59 [45-72] n=49  | 44 [28-61] n=32 |
| sign42    | 49 [40-59] n=104 | 53 [43-63] n=96  | 50 [39-61] n=72  | 45 [30-62] n=33  | 55 [35-73] n=22 |
| sign63    | 51 [39-62] n=69  | 58 [46-70] n=65  | 54 [40-67] n=50  | 63 [46-78] n=30  | 67 [44-84] n=18 |
| tb10_2atr | 50 [46-54] n=603 | 49 [45-54] n=452 | 53 [46-59] n=251 | 47 [38-56] n=117 | 51 [39-62] n=69 |
| tb10_3atr | 51 [47-56] n=482 | 51 [46-56] n=381 | 54 [48-61] n=213 | 49 [40-59] n=99  | 52 [40-63] n=66 |
| tb21_2atr | 51 [46-55] n=451 | 55 [49-60] n=335 | 53 [46-60] n=195 | 53 [43-64] n=86  | 57 [42-70] n=44 |
| tb21_3atr | 49 [43-55] n=288 | 54 [47-60] n=235 | 55 [47-63] n=138 | 58 [46-70] n=62  | 47 [32-63] n=38 |
| tb42_2atr | 49 [45-54] n=401 | 53 [47-58] n=305 | 52 [45-60] n=185 | 61 [49-71] n=76  | 60 [46-74] n=43 |
| tb42_3atr | 48 [41-55] n=190 | 56 [48-63] n=167 | 54 [45-63] n=113 | 62 [49-74] n=56  | 60 [42-75] n=30 |
| tb63_2atr | 49 [44-54] n=397 | 55 [49-61] n=291 | 53 [46-60] n=173 | 63 [51-73] n=75  | 61 [46-74] n=46 |
| tb63_3atr | 53 [45-60] n=179 | 58 [50-65] n=151 | 55 [45-64] n=102 | 66 [52-78] n=50  | 60 [42-75] n=30 |

**house model, NON-OVERLAPPING decisions, 2016-26**

| target    | cov100           | cov50            | cov25            | cov10           | cov5            |
|:----------|:-----------------|:-----------------|:-----------------|:----------------|:----------------|
| sign10    | 52 [46-57] n=281 | 52 [46-59] n=237 | 56 [48-64] n=140 | 52 [41-63] n=79 | 53 [40-65] n=57 |
| sign21    | 53 [44-61] n=133 | 51 [42-60] n=118 | 61 [51-71] n=83  | 61 [47-74] n=44 | 42 [26-59] n=31 |
| sign42    | 53 [41-65] n=66  | 55 [43-67] n=62  | 47 [34-61] n=49  | 44 [28-63] n=27 | 52 [32-72] n=21 |
| sign63    | 57 [42-70] n=44  | 62 [47-75] n=42  | 56 [39-71] n=34  | 60 [41-77] n=25 | 65 [41-83] n=17 |
| tb10_2atr | 52 [47-57] n=389 | 53 [47-58] n=299 | 56 [49-63] n=184 | 51 [41-60] n=99 | 53 [41-65] n=60 |
| tb10_3atr | 54 [49-60] n=313 | 56 [50-62] n=257 | 58 [50-66] n=156 | 54 [44-65] n=81 | 53 [40-65] n=57 |
| tb21_2atr | 51 [46-57] n=290 | 54 [48-61] n=214 | 52 [44-60] n=143 | 52 [41-63] n=79 | 56 [41-70] n=43 |
| tb21_3atr | 49 [42-56] n=187 | 53 [45-61] n=154 | 54 [44-63] n=99  | 55 [42-67] n=55 | 46 [31-62] n=37 |
| tb42_2atr | 50 [44-56] n=254 | 52 [46-59] n=200 | 50 [42-59] n=131 | 57 [46-68] n=68 | 60 [44-73] n=42 |
| tb42_3atr | 52 [43-61] n=119 | 59 [50-68] n=108 | 52 [41-63] n=77  | 60 [46-73] n=48 | 59 [41-74] n=29 |
| tb63_2atr | 49 [43-55] n=250 | 54 [47-61] n=192 | 52 [43-60] n=127 | 59 [47-70] n=68 | 60 [45-73] n=45 |
| tb63_3atr | 57 [48-66] n=112 | 61 [51-71] n=96  | 54 [42-65] n=71  | 64 [49-76] n=44 | 59 [41-74] n=29 |

**house model, NON-OVERLAPPING decisions, 2023-26**

| target    | cov100           | cov50            | cov25           | cov10           | cov5            |
|:----------|:-----------------|:-----------------|:----------------|:----------------|:----------------|
| sign10    | 53 [43-62] n=99  | 48 [38-59] n=85  | 52 [39-65] n=52 | 51 [36-67] n=35 | 52 [33-71] n=23 |
| sign21    | 55 [41-69] n=47  | 48 [33-62] n=42  | 61 [44-75] n=33 | 63 [41-81] n=19 | 43 [21-67] n=14 |
| sign42    | 48 [29-67] n=23  | 59 [39-77] n=22  | 39 [20-61] n=18 | 45 [21-72] n=11 | 40 [17-69] n=10 |
| sign63    | 47 [25-70] n=15  | 60 [36-80] n=15  | 62 [36-82] n=13 | 50 [24-76] n=10 | 43 [16-75] n=7  |
| tb10_2atr | 49 [41-58] n=136 | 53 [43-62] n=112 | 57 [45-68] n=67 | 55 [40-69] n=42 | 64 [46-79] n=28 |
| tb10_3atr | 53 [43-62] n=108 | 51 [41-61] n=90  | 53 [40-65] n=59 | 57 [41-71] n=37 | 52 [33-71] n=23 |
| tb21_2atr | 55 [45-64] n=99  | 59 [48-70] n=79  | 55 [41-68] n=51 | 59 [42-74] n=34 | 60 [41-77] n=25 |
| tb21_3atr | 51 [39-63] n=65  | 52 [39-64] n=56  | 60 [45-74] n=40 | 65 [46-81] n=26 | 59 [36-78] n=17 |
| tb42_2atr | 51 [40-61] n=87  | 57 [45-67] n=74  | 45 [31-59] n=47 | 53 [36-69] n=32 | 60 [41-77] n=25 |
| tb42_3atr | 48 [33-62] n=42  | 63 [48-76] n=41  | 45 [30-62] n=33 | 62 [41-79] n=21 | 56 [33-77] n=16 |
| tb63_2atr | 49 [39-60] n=85  | 55 [43-66] n=69  | 44 [31-59] n=45 | 55 [38-71] n=31 | 62 [43-78] n=26 |
| tb63_3atr | 53 [37-68] n=38  | 58 [42-73] n=36  | 47 [30-64] n=30 | 63 [41-81] n=19 | 56 [33-77] n=16 |

**logit model, weekly decisions, 2010-26**

| target    | cov100           | cov50            | cov25            | cov10           | cov5            |
|:----------|:-----------------|:-----------------|:-----------------|:----------------|:----------------|
| sign10    | 48 [44-53] n=873 | 48 [41-56] n=315 | 51 [40-63] n=134 | 58 [34-79] n=31 | 60 [23-88] n=10 |
| sign21    | 49 [42-55] n=870 | 45 [34-57] n=291 | 44 [25-64] n=85  | 50 [13-87] n=14 | 67 [9-97] n=3   |
| sign42    | 47 [37-56] n=866 | 40 [27-55] n=369 | 30 [13-55] n=128 | 22 [5-61] n=50  | 12 [1-60] n=34  |
| sign63    | 48 [36-59] n=862 | 44 [26-62] n=319 | 41 [14-75] n=78  | 15 [1-79] n=20  | 0 [0-79] n=6    |
| tb10_2atr | 49 [45-53] n=873 | 53 [47-59] n=355 | 52 [43-62] n=161 | 56 [38-73] n=39 | 53 [29-75] n=19 |
| tb10_3atr | 49 [45-54] n=873 | 50 [42-57] n=325 | 53 [41-64] n=129 | 61 [37-80] n=28 | 64 [29-88] n=11 |
| tb21_2atr | 49 [44-53] n=870 | 47 [41-54] n=429 | 51 [41-62] n=167 | 50 [31-69] n=52 | 59 [30-83] n=22 |
| tb21_3atr | 47 [42-53] n=870 | 43 [35-53] n=357 | 49 [34-65] n=114 | 42 [18-70] n=31 | 50 [17-83] n=14 |
| tb42_2atr | 48 [43-53] n=866 | 46 [38-55] n=405 | 43 [32-56] n=178 | 47 [30-64] n=64 | 50 [24-76] n=28 |
| tb42_3atr | 47 [41-54] n=866 | 50 [40-60] n=366 | 51 [34-68] n=131 | 58 [24-86] n=24 | 62 [14-94] n=8  |
| tb63_2atr | 47 [41-52] n=862 | 46 [39-53] n=455 | 42 [31-54] n=213 | 48 [34-63] n=93 | 49 [30-68] n=51 |
| tb63_3atr | 48 [41-56] n=862 | 53 [42-63] n=387 | 51 [35-66] n=176 | 46 [23-70] n=70 | 32 [9-70] n=25  |

**avg model, weekly decisions, 2010-26**

| target    | cov100           | cov50            | cov25            | cov10           | cov5            |
|:----------|:-----------------|:-----------------|:-----------------|:----------------|:----------------|
| sign10    | 52 [48-57] n=873 | 50 [43-57] n=383 | 53 [44-63] n=201 | 57 [43-70] n=91 | 55 [36-72] n=53 |
| sign21    | 50 [43-57] n=870 | 49 [40-59] n=388 | 52 [37-67] n=172 | 64 [39-84] n=59 | 62 [30-87] n=32 |
| sign42    | 52 [43-62] n=866 | 58 [43-71] n=365 | 61 [36-81] n=120 | 63 [28-88] n=54 | 66 [23-92] n=32 |
| sign63    | 53 [42-65] n=862 | 60 [42-76] n=337 | 69 [40-88] n=140 | 68 [28-92] n=62 | 75 [21-97] n=28 |
| tb10_2atr | 51 [47-55] n=873 | 54 [48-59] n=429 | 53 [45-61] n=218 | 51 [39-63] n=92 | 50 [34-66] n=52 |
| tb10_3atr | 52 [47-56] n=873 | 52 [45-59] n=389 | 52 [43-61] n=209 | 57 [44-70] n=94 | 56 [39-72] n=55 |
| tb21_2atr | 50 [45-55] n=870 | 54 [48-61] n=431 | 57 [47-67] n=180 | 62 [44-77] n=63 | 64 [39-83] n=36 |
| tb21_3atr | 51 [45-56] n=870 | 53 [44-61] n=414 | 56 [43-68] n=182 | 64 [40-83] n=53 | 68 [35-89] n=31 |
| tb42_2atr | 52 [47-57] n=866 | 56 [49-62] n=421 | 59 [48-70] n=174 | 63 [45-78] n=68 | 68 [40-87] n=31 |
| tb42_3atr | 54 [47-61] n=866 | 61 [52-71] n=405 | 66 [48-80] n=138 | 67 [41-85] n=63 | 73 [36-93] n=33 |
| tb63_2atr | 52 [47-57] n=862 | 55 [48-62] n=393 | 57 [45-67] n=161 | 63 [45-78] n=70 | 69 [41-88] n=29 |
| tb63_3atr | 55 [47-62] n=862 | 64 [54-73] n=402 | 68 [51-81] n=156 | 70 [44-87] n=66 | 72 [37-92] n=36 |

**avg model, NON-OVERLAPPING decisions, 2010-26**

| target    | cov100           | cov50            | cov25            | cov10            | cov5            |
|:----------|:-----------------|:-----------------|:-----------------|:-----------------|:----------------|
| sign10    | 51 [47-56] n=437 | 51 [45-56] n=299 | 48 [40-55] n=165 | 54 [43-64] n=84  | 50 [37-63] n=54 |
| sign21    | 51 [44-58] n=208 | 53 [45-60] n=163 | 51 [41-61] n=90  | 62 [45-76] n=34  | 43 [24-63] n=21 |
| sign42    | 50 [41-59] n=104 | 50 [40-60] n=90  | 51 [38-64] n=53  | 54 [35-71] n=26  | 56 [33-77] n=16 |
| sign63    | 52 [41-64] n=69  | 54 [42-66] n=59  | 50 [36-64] n=42  | 74 [54-87] n=23  | 75 [47-91] n=12 |
| tb10_2atr | 50 [46-54] n=603 | 50 [45-54] n=432 | 50 [44-57] n=235 | 52 [43-60] n=122 | 49 [38-61] n=71 |
| tb10_3atr | 51 [47-55] n=482 | 49 [44-54] n=326 | 49 [42-56] n=180 | 52 [42-62] n=88  | 53 [40-65] n=57 |
| tb21_2atr | 51 [46-55] n=451 | 49 [44-54] n=356 | 51 [43-58] n=186 | 56 [45-66] n=79  | 61 [46-74] n=41 |
| tb21_3atr | 48 [42-53] n=288 | 51 [45-58] n=234 | 48 [40-57] n=135 | 50 [36-64] n=48  | 43 [27-61] n=28 |
| tb42_2atr | 51 [46-55] n=401 | 51 [45-56] n=327 | 54 [47-61] n=184 | 62 [50-73] n=66  | 58 [42-73] n=36 |
| tb42_3atr | 49 [42-56] n=190 | 54 [47-62] n=166 | 52 [42-61] n=102 | 59 [45-72] n=49  | 65 [45-81] n=23 |
| tb63_2atr | 51 [46-56] n=397 | 51 [45-56] n=308 | 54 [46-61] n=177 | 62 [50-72] n=71  | 58 [42-73] n=36 |
| tb63_3atr | 51 [44-58] n=179 | 55 [47-63] n=148 | 55 [45-64] n=99  | 60 [45-74] n=40  | 69 [50-83] n=26 |

**Net P&L per decision (bp, after a 2 x 1.2 pip round trip), house model, weekly: 2010-26 / 2016-26 / 2023-26**

| target    | cov100          | cov50           | cov25             | cov10             | cov5              |
|:----------|:----------------|:----------------|:------------------|:------------------|:------------------|
| sign10    | +2 / +6 / +12   | +7 / +17 / +13  | +5 / +14 / +13    | -6 / +13 / -3     | +5 / +22 / +24    |
| sign21    | +9 / +18 / +15  | +4 / +19 / +13  | +25 / +33 / +24   | +30 / +36 / -12   | +65 / +65 / +43   |
| sign42    | +19 / +44 / +18 | +68 / +69 / +20 | +77 / +86 / -2    | +85 / +73 / -17   | +125 / +125 / +35 |
| sign63    | +3 / +46 / +12  | +85 / +97 / +42 | +114 / +117 / +23 | +112 / +103 / -17 | +123 / +123 / +2  |
| tb10_2atr | -2 / +1 / +11   | +2 / +10 / +13  | +3 / +11 / +13    | -18 / -1 / +2     | -27 / -8 / +27    |
| tb10_3atr | -2 / +4 / +10   | +1 / +11 / +11  | +3 / +11 / +10    | -10 / +8 / -7     | -3 / +14 / +7     |
| tb21_2atr | +1 / +6 / +7    | +21 / +19 / +15 | +38 / +31 / +21   | +21 / +27 / +38   | +40 / +40 / +53   |
| tb21_3atr | +0 / +4 / +4    | +24 / +24 / +11 | +52 / +42 / +13   | +30 / +29 / +5    | +77 / +77 / +41   |
| tb42_2atr | +3 / +7 / +4    | +28 / +23 / +22 | +45 / +38 / +16   | +38 / +42 / +26   | +54 / +54 / +59   |
| tb42_3atr | +13 / +24 / +4  | +60 / +54 / +17 | +93 / +83 / +5    | +97 / +88 / +17   | +155 / +155 / +62 |
| tb63_2atr | +8 / +9 / +5    | +30 / +24 / +18 | +44 / +40 / +14   | +47 / +47 / +35   | +64 / +64 / +63   |
| tb63_3atr | +17 / +30 / +2  | +72 / +73 / +25 | +102 / +98 / +3   | +103 / +98 / +12  | +162 / +162 / +62 |

**Is the 10 % cell evidence? accuracy at 10 % coverage against the majority base rate (max of up-share, 1 - up-share), 2010-26**

| model   | target    |   majority base % | weekly          | weekly lower bound > base (NW / conservative)   | non-overlapping   | non-overlapping lower bound > base   |
|:--------|:----------|------------------:|:----------------|:------------------------------------------------|:------------------|:-------------------------------------|
| house   | sign10    |              51.8 | 53 [39-66] n=96 | no / no                                         | 47 [37-57] n=96   | no                                   |
| house   | sign21    |              52   | 57 [37-76] n=89 | no / no                                         | 59 [45-72] n=49   | no                                   |
| house   | sign42    |              53.1 | 59 [29-84] n=74 | no / no                                         | 45 [30-62] n=33   | no                                   |
| house   | sign63    |              53.2 | 70 [35-91] n=87 | yes / no                                        | 63 [46-78] n=30   | no                                   |
| house   | tb10_2atr |              51.2 | 47 [35-60] n=93 | no / no                                         | 47 [38-56] n=117  | no                                   |
| house   | tb10_3atr |              51.5 | 52 [38-65] n=95 | no / no                                         | 49 [40-59] n=99   | no                                   |
| house   | tb21_2atr |              50.8 | 56 [39-71] n=75 | no / no                                         | 53 [43-64] n=86   | no                                   |
| house   | tb21_3atr |              51.5 | 57 [38-75] n=82 | no / no                                         | 58 [46-70] n=62   | no                                   |
| house   | tb42_2atr |              50.2 | 62 [44-77] n=76 | no / no                                         | 61 [49-71] n=76   | no                                   |
| house   | tb42_3atr |              51.5 | 69 [45-86] n=75 | yes / no                                        | 62 [49-74] n=56   | no                                   |
| house   | tb63_2atr |              50.1 | 65 [47-80] n=74 | yes / no                                        | 63 [51-73] n=75   | yes                                  |
| house   | tb63_3atr |              50.7 | 70 [45-87] n=77 | yes / no                                        | 66 [52-78] n=50   | yes                                  |
| avg     | sign10    |              51.8 | 57 [43-70] n=91 | no / no                                         | 54 [43-64] n=84   | no                                   |
| avg     | sign21    |              52   | 64 [39-84] n=59 | no / no                                         | 62 [45-76] n=34   | no                                   |
| avg     | sign42    |              53.1 | 63 [28-88] n=54 | no / no                                         | 54 [35-71] n=26   | no                                   |
| avg     | sign63    |              53.2 | 68 [28-92] n=62 | no / no                                         | 74 [54-87] n=23   | yes                                  |
| avg     | tb10_2atr |              51.2 | 51 [39-63] n=92 | no / no                                         | 52 [43-60] n=122  | no                                   |
| avg     | tb10_3atr |              51.5 | 57 [44-70] n=94 | no / no                                         | 52 [42-62] n=88   | no                                   |
| avg     | tb21_2atr |              50.8 | 62 [44-77] n=63 | no / no                                         | 56 [45-66] n=79   | no                                   |
| avg     | tb21_3atr |              51.5 | 64 [40-83] n=53 | no / no                                         | 50 [36-64] n=48   | no                                   |
| avg     | tb42_2atr |              50.2 | 63 [45-78] n=68 | no / no                                         | 62 [50-73] n=66   | no                                   |
| avg     | tb42_3atr |              51.5 | 67 [41-85] n=63 | no / no                                         | 59 [45-72] n=49   | no                                   |
| avg     | tb63_2atr |              50.1 | 63 [45-78] n=70 | no / no                                         | 62 [50-72] n=71   | yes                                  |
| avg     | tb63_3atr |              50.7 | 70 [44-87] n=66 | yes / no                                        | 60 [45-74] n=40   | no                                   |

### Probability rules: speak only when the calibrated probability is at least 55 / 60 / 65 %

**house model, weekly, 2010-26**

| target    | p55              | p60              | p65              |
|:----------|:-----------------|:-----------------|:-----------------|
| sign10    | 52 [44-61] n=246 | 52 [28-75] n=27  | -                |
| sign21    | 51 [41-61] n=386 | 45 [27-64] n=105 | 61 [27-87] n=28  |
| sign42    | 55 [43-66] n=607 | 59 [45-73] n=364 | 56 [36-74] n=188 |
| sign63    | 57 [43-70] n=619 | 60 [43-75] n=407 | 60 [39-79] n=243 |
| tb10_2atr | 51 [44-59] n=250 | 48 [24-72] n=21  | -                |
| tb10_3atr | 52 [44-60] n=249 | 50 [26-74] n=24  | -                |
| tb21_2atr | 54 [47-61] n=391 | 57 [42-70] n=93  | 44 [17-76] n=18  |
| tb21_3atr | 53 [44-62] n=381 | 60 [42-75] n=105 | 63 [30-87] n=27  |
| tb42_2atr | 56 [49-62] n=501 | 61 [52-70] n=225 | 65 [43-82] n=57  |
| tb42_3atr | 57 [48-65] n=569 | 62 [51-72] n=325 | 69 [52-83] n=137 |
| tb63_2atr | 57 [50-63] n=485 | 62 [52-71] n=219 | 66 [47-81] n=68  |
| tb63_3atr | 59 [50-67] n=587 | 63 [52-73] n=372 | 72 [58-83] n=210 |

**logit model, weekly, 2010-26**

| target    | p55              | p60              | p65              |
|:----------|:-----------------|:-----------------|:-----------------|
| sign10    | 48 [35-61] n=100 | 52 [27-76] n=25  | 0 [0-79] n=3     |
| sign21    | 38 [24-54] n=150 | 46 [23-71] n=54  | 90 [31-99] n=10  |
| sign42    | 46 [32-62] n=324 | 45 [23-69] n=122 | 46 [19-76] n=69  |
| sign63    | 39 [24-56] n=391 | 42 [20-67] n=166 | 43 [19-72] n=120 |
| tb10_2atr | 47 [35-60] n=89  | 58 [33-80] n=24  | 50 [16-84] n=6   |
| tb10_3atr | 49 [36-63] n=93  | 45 [25-67] n=33  | 50 [14-86] n=6   |
| tb21_2atr | 47 [33-62] n=109 | 55 [33-75] n=44  | 33 [7-78] n=6    |
| tb21_3atr | 40 [26-57] n=104 | 48 [25-72] n=42  | 90 [38-99] n=10  |
| tb42_2atr | 46 [35-58] n=211 | 53 [35-71] n=86  | 38 [9-79] n=8    |
| tb42_3atr | 49 [39-60] n=361 | 44 [25-64] n=101 | 55 [19-86] n=20  |
| tb63_2atr | 45 [33-58] n=205 | 55 [34-74] n=64  | -                |
| tb63_3atr | 52 [41-62] n=405 | 51 [34-67] n=141 | 46 [21-73] n=59  |

**avg model, weekly, 2010-26**

| target    | p55              | p60              | p65              |
|:----------|:-----------------|:-----------------|:-----------------|
| sign10    | 49 [37-61] n=129 | 25 [3-80] n=4    | -                |
| sign21    | 44 [32-57] n=258 | 46 [20-75] n=37  | -                |
| sign42    | 52 [40-64] n=500 | 49 [29-69] n=169 | 46 [20-74] n=76  |
| sign63    | 55 [40-70] n=498 | 51 [30-72] n=226 | 48 [21-76] n=112 |
| tb10_2atr | 49 [38-60] n=115 | 57 [21-87] n=7   | -                |
| tb10_3atr | 49 [38-61] n=128 | 40 [8-83] n=5    | -                |
| tb21_2atr | 51 [41-61] n=203 | 82 [39-97] n=11  | -                |
| tb21_3atr | 47 [35-59] n=216 | 57 [29-81] n=30  | -                |
| tb42_2atr | 53 [44-62] n=339 | 71 [54-83] n=68  | -                |
| tb42_3atr | 56 [46-65] n=461 | 56 [39-71] n=144 | 65 [32-87] n=31  |
| tb63_2atr | 54 [45-62] n=322 | 78 [59-90] n=59  | -                |
| tb63_3atr | 58 [49-67] n=505 | 62 [48-75] n=206 | 65 [43-82] n=85  |

**P >= 60 % calls by period (weekly; accuracy [interval] n, net bp per decision)**

| target    | house 2010-26          | house 2016-26          | house 2023-26          | logit 2010-26          | logit 2016-26           | logit 2023-26         | avg 2010-26            | avg 2016-26            | avg 2023-26             |
|:----------|:-----------------------|:-----------------------|:-----------------------|:-----------------------|:------------------------|:----------------------|:-----------------------|:-----------------------|:------------------------|
| sign10    | 52 [28-75] n=27 +12bp  | 52 [27-76] n=25 +20bp  | 67 [30-90] n=12 +61bp  | 52 [27-76] n=25 -4bp   | -                       | -                     | 25 [3-80] n=4 -168bp   | -                      | -                       |
| sign21    | 45 [27-64] n=105 -49bp | 51 [31-71] n=88 -14bp  | 50 [22-78] n=34 -14bp  | 46 [23-71] n=54 -30bp  | 50 [5-95] n=2 -28bp     | -                     | 46 [20-75] n=37 -11bp  | 43 [6-89] n=7 +34bp    | 50 [5-95] n=4 +35bp     |
| sign42    | 59 [45-73] n=364 +43bp | 62 [43-78] n=222 +68bp | 51 [24-77] n=85 +21bp  | 45 [23-69] n=122 -36bp | 28 [3-81] n=18 -0bp     | 28 [3-81] n=18 -0bp   | 49 [29-69] n=169 -26bp | 51 [20-81] n=53 +54bp  | 39 [10-78] n=36 -7bp    |
| sign63    | 60 [43-75] n=407 +51bp | 65 [44-82] n=260 +95bp | 55 [25-82] n=100 +48bp | 42 [20-67] n=166 -68bp | 37 [10-75] n=62 -75bp   | 41 [11-79] n=56 -40bp | 51 [30-72] n=226 -19bp | 58 [29-83] n=117 +56bp | 46 [16-79] n=70 -4bp    |
| tb10_2atr | 48 [24-72] n=21 -20bp  | 47 [23-73] n=19 -13bp  | 86 [42-98] n=7 +75bp   | 58 [33-80] n=24 +34bp  | -                       | -                     | 57 [21-87] n=7 +26bp   | -                      | -                       |
| tb10_3atr | 50 [26-74] n=24 -3bp   | 50 [25-75] n=22 +5bp   | 67 [31-90] n=12 +53bp  | 45 [25-67] n=33 -16bp  | -                       | -                     | 40 [8-83] n=5 -31bp    | -                      | -                       |
| tb21_2atr | 57 [42-70] n=93 +26bp  | 57 [42-71] n=88 +27bp  | 60 [36-80] n=30 +28bp  | 55 [33-75] n=44 +16bp  | -                       | -                     | 82 [39-97] n=11 +137bp | 67 [15-96] n=3 +57bp   | 100 [21-100] n=2 +176bp |
| tb21_3atr | 60 [42-75] n=105 +41bp | 59 [42-75] n=103 +37bp | 52 [28-76] n=40 +4bp   | 48 [25-72] n=42 -12bp  | -                       | -                     | 57 [29-81] n=30 +63bp  | 67 [16-95] n=6 +107bp  | 60 [12-94] n=5 +75bp    |
| tb42_2atr | 61 [52-70] n=225 +42bp | 59 [47-70] n=166 +30bp | 56 [38-72] n=54 +16bp  | 53 [35-71] n=86 +15bp  | -                       | -                     | 71 [54-83] n=68 +85bp  | 80 [41-96] n=15 +117bp | 86 [39-98] n=7 +111bp   |
| tb42_3atr | 62 [51-72] n=325 +56bp | 65 [51-77] n=210 +68bp | 55 [33-74] n=75 +15bp  | 44 [25-64] n=101 -26bp | 38 [12-73] n=24 -43bp   | 38 [12-73] n=24 -43bp | 56 [39-71] n=144 +38bp | 58 [32-81] n=53 +58bp  | 46 [20-74] n=39 -7bp    |
| tb63_2atr | 62 [52-71] n=219 +44bp | 59 [47-70] n=164 +34bp | 55 [37-72] n=56 +15bp  | 55 [34-74] n=64 +26bp  | 100 [21-100] n=1 +218bp | -                     | 78 [59-90] n=59 +110bp | 83 [46-97] n=18 +117bp | 90 [43-99] n=10 +114bp  |
| tb63_3atr | 63 [52-73] n=372 +59bp | 66 [52-77] n=244 +75bp | 57 [36-75] n=83 +22bp  | 51 [34-67] n=141 -5bp  | 58 [33-80] n=53 +30bp   | 51 [25-77] n=43 +11bp | 62 [48-75] n=206 +60bp | 69 [49-84] n=107 +95bp | 56 [31-78] n=54 +31bp   |

**Reliability, 2010-26, weekly: realised accuracy % (mean predicted confidence %) n, by confidence bucket**


*house*

| target    | 0.50-0.55     | 0.55-0.60     | 0.60-0.65     | 0.65-0.70     | 0.70-1.00     |
|:----------|:--------------|:--------------|:--------------|:--------------|:--------------|
| sign10    | 52 (52) n=627 | 53 (57) n=219 | 52 (61) n=27  | -             | -             |
| sign21    | 54 (53) n=484 | 53 (57) n=281 | 39 (62) n=77  | 59 (67) n=27  | 100 (74) n=1  |
| sign42    | 51 (53) n=259 | 48 (58) n=243 | 62 (62) n=176 | 56 (67) n=122 | 58 (73) n=66  |
| sign63    | 47 (52) n=243 | 50 (57) n=212 | 60 (62) n=164 | 59 (67) n=95  | 61 (75) n=148 |
| tb10_2atr | 51 (52) n=623 | 52 (57) n=229 | 48 (61) n=21  | -             | -             |
| tb10_3atr | 51 (52) n=624 | 52 (57) n=225 | 50 (61) n=24  | -             | -             |
| tb21_2atr | 49 (52) n=479 | 54 (57) n=298 | 60 (62) n=75  | 47 (66) n=17  | 0 (76) n=1    |
| tb21_3atr | 49 (52) n=489 | 50 (57) n=276 | 59 (62) n=78  | 62 (67) n=26  | 100 (75) n=1  |
| tb42_2atr | 47 (52) n=365 | 51 (57) n=276 | 60 (62) n=168 | 60 (67) n=45  | 83 (73) n=12  |
| tb42_3atr | 45 (53) n=297 | 50 (57) n=244 | 57 (62) n=188 | 66 (67) n=103 | 79 (74) n=34  |
| tb63_2atr | 48 (52) n=377 | 53 (57) n=266 | 60 (62) n=151 | 62 (66) n=52  | 81 (73) n=16  |
| tb63_3atr | 44 (52) n=275 | 53 (57) n=215 | 51 (62) n=162 | 72 (67) n=106 | 73 (74) n=104 |

*avg*

| target    | 0.50-0.55     | 0.55-0.60     | 0.60-0.65     | 0.65-0.70    | 0.70-1.00    |
|:----------|:--------------|:--------------|:--------------|:-------------|:-------------|
| sign10    | 53 (52) n=744 | 50 (57) n=125 | 25 (61) n=4   | -            | -            |
| sign21    | 52 (52) n=612 | 44 (57) n=221 | 46 (61) n=37  | -            | -            |
| sign42    | 53 (53) n=366 | 54 (57) n=331 | 51 (62) n=93  | 46 (67) n=63 | 46 (71) n=13 |
| sign63    | 51 (53) n=364 | 59 (57) n=272 | 54 (62) n=114 | 46 (67) n=46 | 50 (74) n=66 |
| tb10_2atr | 51 (52) n=758 | 48 (57) n=108 | 57 (61) n=7   | -            | -            |
| tb10_3atr | 52 (52) n=745 | 50 (57) n=123 | 40 (61) n=5   | -            | -            |
| tb21_2atr | 50 (52) n=667 | 49 (57) n=192 | 82 (61) n=11  | -            | -            |
| tb21_3atr | 52 (52) n=654 | 45 (57) n=186 | 57 (61) n=30  | -            | -            |
| tb42_2atr | 51 (52) n=527 | 49 (57) n=271 | 71 (62) n=68  | -            | -            |
| tb42_3atr | 52 (53) n=405 | 56 (57) n=317 | 53 (62) n=113 | 68 (67) n=28 | 33 (72) n=3  |
| tb63_2atr | 50 (52) n=540 | 49 (57) n=263 | 78 (62) n=59  | -            | -            |
| tb63_3atr | 49 (52) n=357 | 56 (57) n=299 | 60 (62) n=121 | 66 (67) n=70 | 60 (71) n=15 |

### Optional diagnostics: 1- and 5-session direction (non-overlapping, 2010-26)

| tm          | cov100            | cov50             | cov25             | cov10            | cov5             | p55              | p60             |
|:------------|:------------------|:------------------|:------------------|:-----------------|:-----------------|:-----------------|:----------------|
| sign1 avg   | 51 [50-53] n=4372 | 51 [49-53] n=2237 | 51 [48-54] n=942  | 55 [50-60] n=341 | 56 [48-63] n=165 | 64 [35-85] n=11  | -               |
| sign1 house | 51 [50-53] n=4372 | 51 [49-53] n=2178 | 51 [48-54] n=1009 | 52 [47-57] n=407 | 51 [44-57] n=226 | 65 [52-75] n=62  | -               |
| sign1 logit | 51 [49-52] n=4372 | 51 [49-53] n=2309 | 51 [48-54] n=942  | 53 [47-59] n=264 | 53 [44-63] n=105 | 54 [29-77] n=13  | -               |
| sign5 avg   | 50 [47-54] n=874  | 51 [47-55] n=591  | 52 [46-58] n=273  | 52 [43-61] n=119 | 53 [42-64] n=73  | 46 [38-54] n=145 | -               |
| sign5 house | 52 [49-55] n=874  | 53 [49-57] n=632  | 52 [47-58] n=326  | 53 [44-61] n=135 | 53 [43-63] n=88  | 54 [49-60] n=323 | 49 [35-63] n=45 |
| sign5 logit | 52 [48-55] n=874  | 50 [45-55] n=389  | 47 [39-55] n=148  | 41 [26-58] n=32  | 50 [25-75] n=12  | 47 [36-57] n=86  | 33 [14-61] n=12 |

## 3. (B) Agreement and regime selectors (fixed rules, sign targets)
Direction = sign of the walk-forward house score. Cells: accuracy % [interval] n, net bp per decision.

**weekly, 2010-26**

| model            | sign10                 | sign21                 | sign42                  | sign63                  |
|:-----------------|:-----------------------|:-----------------------|:------------------------|:------------------------|
| B:house_sign_all | 53 [49-58] n=873 +15bp | 56 [49-62] n=870 +30bp | 58 [48-67] n=866 +65bp  | 60 [49-71] n=862 +90bp  |
| B:agree3         | 57 [50-64] n=390 +29bp | 59 [49-69] n=387 +46bp | 65 [50-77] n=383 +108bp | 67 [49-81] n=383 +153bp |
| B:agree3_trend   | 59 [51-67] n=271 +31bp | 59 [47-71] n=268 +41bp | 61 [43-76] n=265 +89bp  | 63 [42-80] n=265 +135bp |
| B:house_quiet    | 52 [45-60] n=321 +14bp | 57 [45-67] n=318 +34bp | 60 [44-74] n=314 +70bp  | 64 [44-80] n=310 +99bp  |
| B:house_volatile | 55 [43-67] n=124 +11bp | 59 [41-75] n=124 +55bp | 63 [38-82] n=124 +121bp | 63 [33-85] n=124 +115bp |
| B:house_nonevent | 53 [47-59] n=491 +19bp | 57 [48-65] n=488 +34bp | 58 [45-70] n=486 +75bp  | 64 [48-77] n=483 +99bp  |
| B:house_event    | 54 [47-61] n=382 +11bp | 54 [44-64] n=382 +24bp | 57 [43-71] n=380 +53bp  | 56 [39-72] n=379 +78bp  |

**weekly, 2016-26**

| model            | sign10                 | sign21                 | sign42                 | sign63                  |
|:-----------------|:-----------------------|:-----------------------|:-----------------------|:------------------------|
| B:house_sign_all | 52 [46-58] n=562 +9bp  | 54 [45-62] n=559 +25bp | 57 [45-68] n=555 +63bp | 62 [47-74] n=551 +84bp  |
| B:agree3         | 55 [46-63] n=246 +19bp | 57 [44-69] n=243 +38bp | 63 [45-78] n=239 +91bp | 67 [45-84] n=239 +127bp |
| B:agree3_trend   | 57 [46-67] n=166 +25bp | 58 [42-72] n=163 +46bp | 60 [38-78] n=160 +82bp | 64 [38-84] n=160 +107bp |
| B:house_quiet    | 50 [41-59] n=231 +3bp  | 53 [40-66] n=228 +16bp | 54 [36-71] n=224 +32bp | 61 [39-80] n=220 +50bp  |
| B:house_volatile | 55 [41-68] n=91 +4bp   | 58 [38-76] n=91 +52bp  | 65 [36-86] n=91 +146bp | 64 [30-88] n=91 +146bp  |
| B:house_nonevent | 51 [44-59] n=344 +9bp  | 55 [45-66] n=341 +30bp | 58 [43-72] n=339 +78bp | 65 [47-81] n=336 +104bp |
| B:house_event    | 54 [44-63] n=218 +10bp | 51 [38-64] n=218 +19bp | 56 [37-73] n=216 +41bp | 55 [33-76] n=215 +52bp  |

**weekly, 2023-26**

| model            | sign10                | sign21                 | sign42                 | sign63                 |
|:-----------------|:----------------------|:-----------------------|:-----------------------|:-----------------------|
| B:house_sign_all | 51 [41-61] n=198 +6bp | 52 [38-66] n=195 +14bp | 46 [28-66] n=191 +33bp | 57 [33-78] n=187 +58bp |
| B:agree3         | 57 [42-71] n=80 +20bp | 55 [33-74] n=77 +27bp  | 47 [20-75] n=73 +26bp  | 53 [21-84] n=73 +32bp  |
| B:agree3_trend   | 54 [37-70] n=61 +14bp | 48 [25-72] n=58 +3bp   | 38 [13-72] n=55 +5bp   | 45 [13-82] n=55 +0bp   |
| B:house_quiet    | 49 [36-62] n=112 +2bp | 52 [34-70] n=109 +11bp | 44 [21-69] n=105 +11bp | 57 [27-83] n=101 +31bp |
| B:house_volatile | 42 [18-71] n=19 -53bp | 37 [10-76] n=19 -33bp  | 26 [3-79] n=19 -34bp   | 26 [2-84] n=19 -69bp   |
| B:house_nonevent | 47 [36-59] n=135 +1bp | 52 [36-69] n=132 +13bp | 46 [25-69] n=130 +44bp | 57 [29-81] n=127 +56bp |
| B:house_event    | 59 [42-74] n=63 +17bp | 52 [29-74] n=63 +15bp  | 46 [18-77] n=61 +10bp  | 55 [19-86] n=60 +61bp  |

**NON-OVERLAPPING, 2010-26**

| model            | sign10                 | sign21                 | sign42                  | sign63                 |
|:-----------------|:-----------------------|:-----------------------|:------------------------|:-----------------------|
| B:house_sign_all | 53 [49-58] n=437 +17bp | 55 [48-61] n=208 +35bp | 61 [51-69] n=104 +80bp  | 64 [52-74] n=69 +134bp |
| B:agree3         | 56 [50-62] n=291 +29bp | 59 [51-66] n=156 +55bp | 61 [50-70] n=89 +99bp   | 72 [60-82] n=61 +184bp |
| B:agree3_trend   | 54 [47-61] n=213 +16bp | 51 [42-60] n=123 +25bp | 51 [40-62] n=76 +52bp   | 70 [56-80] n=53 +110bp |
| B:house_quiet    | 54 [48-60] n=250 +18bp | 55 [46-64] n=121 +13bp | 60 [48-71] n=67 +29bp   | 59 [45-72] n=49 +81bp  |
| B:house_volatile | 60 [50-70] n=91 +19bp  | 60 [46-73] n=48 +47bp  | 59 [41-75] n=27 +87bp   | 62 [41-79] n=21 +106bp |
| B:house_nonevent | 55 [50-60] n=405 +17bp | 54 [47-60] n=200 +30bp | 60 [51-69] n=101 +101bp | 64 [52-75] n=67 +111bp |
| B:house_event    | 53 [48-58] n=359 +11bp | 49 [42-56] n=199 +18bp | 61 [52-70] n=101 +81bp  | 66 [54-76] n=67 +151bp |

**NON-OVERLAPPING, 2016-26**

| model            | sign10                 | sign21                 | sign42                 | sign63                 |
|:-----------------|:-----------------------|:-----------------------|:-----------------------|:-----------------------|
| B:house_sign_all | 52 [46-58] n=281 +14bp | 51 [43-59] n=133 +22bp | 61 [49-71] n=66 +59bp  | 61 [47-74] n=44 +67bp  |
| B:agree3         | 53 [46-61] n=178 +28bp | 57 [47-67] n=96 +48bp  | 59 [46-71] n=56 +89bp  | 71 [55-83] n=38 +164bp |
| B:agree3_trend   | 52 [43-60] n=130 +16bp | 52 [41-63] n=75 +15bp  | 47 [33-61] n=47 +22bp  | 72 [55-84] n=32 +119bp |
| B:house_quiet    | 52 [45-60] n=168 +8bp  | 53 [42-64] n=81 +9bp   | 59 [44-72] n=46 +14bp  | 58 [41-73] n=33 -2bp   |
| B:house_volatile | 63 [50-74] n=62 +31bp  | 66 [48-80] n=32 +61bp  | 61 [39-80] n=18 +108bp | 64 [39-84] n=14 +208bp |
| B:house_nonevent | 55 [49-61] n=262 +7bp  | 50 [42-59] n=129 +11bp | 57 [45-68] n=65 +60bp  | 70 [55-81] n=43 +110bp |
| B:house_event    | 52 [46-59] n=222 +8bp  | 53 [44-61] n=127 +28bp | 65 [52-75] n=65 +78bp  | 67 [53-80] n=43 +127bp |

**NON-OVERLAPPING, 2023-26**

| model            | sign10                | sign21                | sign42                 | sign63                 |
|:-----------------|:----------------------|:----------------------|:-----------------------|:-----------------------|
| B:house_sign_all | 52 [42-61] n=99 +10bp | 57 [43-70] n=47 +48bp | 52 [33-71] n=23 +69bp  | 60 [36-80] n=15 +120bp |
| B:agree3         | 54 [42-66] n=63 +14bp | 60 [44-74] n=35 +19bp | 45 [26-66] n=20 -7bp   | 50 [27-73] n=14 -35bp  |
| B:agree3_trend   | 52 [39-65] n=50 +11bp | 41 [26-59] n=29 -23bp | 33 [16-56] n=18 -66bp  | 42 [19-68] n=12 -54bp  |
| B:house_quiet    | 58 [46-69] n=71 +12bp | 58 [41-73] n=33 +29bp | 63 [41-81] n=19 +64bp  | 62 [36-82] n=13 -17bp  |
| B:house_volatile | 54 [29-77] n=13 -8bp  | 43 [16-75] n=7 -41bp  | 50 [15-85] n=4 -59bp   | 67 [21-94] n=3 +202bp  |
| B:house_nonevent | 54 [44-64] n=94 +10bp | 49 [35-63] n=45 -9bp  | 30 [16-51] n=23 -54bp  | 73 [48-89] n=15 +91bp  |
| B:house_event    | 53 [42-64] n=73 +5bp  | 48 [34-62] n=44 +14bp | 74 [54-87] n=23 +109bp | 67 [42-85] n=15 +136bp |

## 4. (C) Path / level events: calibration and Brier score
`predicted` = model probability (training-window frequency of the scaled excursion), `realised` = out-of-sample frequency. Skill = 1 - Brier(model) / Brier(naive); naive = unconditional training distribution in pips (whole window / trailing 250 sessions). Multi-session windows are sampled weekly; interval = Wilson with min(Newey-West effective n, non-overlapping count).

**(i) next-session range stays below k x forecast range** (param = k)

|   param |   predicted % |   realised % 2010-26 | 95 % interval   |    n |   realised % 2016-26 |   realised % 2023-26 |   Brier model |   Brier naive (all) |   Brier naive (1y) |   skill vs naive 1y % |   skill 2023-26 % |
|--------:|--------------:|---------------------:|:----------------|-----:|---------------------:|---------------------:|--------------:|--------------------:|-------------------:|----------------------:|------------------:|
|    1    |          51.2 |                 54.6 | 53-56           | 4372 |                 53.9 |                 53.8 |        0.2491 |              0.3205 |             0.3208 |                  22.4 |              20.1 |
|    1.25 |          72.4 |                 75.6 | 74-77           | 4372 |                 74.9 |                 74   |        0.1854 |              0.2849 |             0.2508 |                  26.1 |              22.6 |
|    1.5  |          86   |                 88.1 | 87-89           | 4372 |                 87.5 |                 85.9 |        0.1054 |              0.205  |             0.1544 |                  31.7 |              26   |

**(ii) price does NOT touch a level u x U away within 1 session(s)** (param = u; U = forecast mean daily range x sqrt(1); upper and lower level pooled)

|   param |   predicted % |   realised % 2010-26 | 95 % interval   |    n |   realised % 2016-26 |   realised % 2023-26 |   Brier model |   Brier naive (all) |   Brier naive (1y) |   skill vs naive 1y % |   skill 2023-26 % | fade: net bp / decision (t)   |
|--------:|--------------:|---------------------:|:----------------|-----:|---------------------:|---------------------:|--------------:|--------------------:|-------------------:|----------------------:|------------------:|:------------------------------|
|    0.25 |          29.8 |                 31.3 | 30-33           | 4372 |                 31.1 |                 31.5 |        0.2155 |              0.2239 |             0.2271 |                   5.1 |               3.1 | -2.9 (-4.9)                   |
|    0.5  |          56.4 |                 57.7 | 56-59           | 4372 |                 57.5 |                 57.7 |        0.2443 |              0.2661 |             0.2667 |                   8.4 |               6.4 | -2.1 (-3.8)                   |
|    0.75 |          74.1 |                 75.4 | 74-77           | 4372 |                 75.1 |                 74.6 |        0.1854 |              0.2108 |             0.2035 |                   8.9 |               6.9 | -1.2 (-3.0)                   |
|    1    |          85.6 |                 86.8 | 86-88           | 4372 |                 86.6 |                 86.4 |        0.1147 |              0.1388 |             0.1268 |                   9.6 |               8.5 | -0.3 (-1.0)                   |
|    1.25 |          92.4 |                 93.3 | 92-94           | 4372 |                 92.9 |                 92.1 |        0.063  |              0.0821 |             0.0708 |                  11   |               8.6 | -0.1 (-0.3)                   |
|    1.5  |          96.1 |                 96.6 | 96-97           | 4372 |                 96.5 |                 95.9 |        0.0327 |              0.0465 |             0.0371 |                  11.7 |               9.1 | +0.2 (+1.3)                   |
|    2    |          99   |                 99.1 | 99-99           | 4372 |                 99.1 |                 98.7 |        0.0092 |              0.0147 |             0.0103 |                  10.7 |               7   | +0.1 (+0.9)                   |

**(ii) price does NOT touch a level u x U away within 5 session(s)** (param = u; U = forecast mean daily range x sqrt(5); upper and lower level pooled)

|   param |   predicted % |   realised % 2010-26 | 95 % interval   |   n |   realised % 2016-26 |   realised % 2023-26 |   Brier model |   Brier naive (all) |   Brier naive (1y) |   skill vs naive 1y % |   skill 2023-26 % | fade: net bp / decision (t)   |
|--------:|--------------:|---------------------:|:----------------|----:|---------------------:|---------------------:|--------------:|--------------------:|-------------------:|----------------------:|------------------:|:------------------------------|
|    0.25 |          30.3 |                 30.1 | 28-32           | 874 |                 30.2 |                 31.4 |        0.2106 |              0.2185 |             0.2201 |                   4.3 |               3.4 | -0.9 (-0.3)                   |
|    0.5  |          56.2 |                 57.4 | 55-60           | 874 |                 57.3 |                 56.3 |        0.2448 |              0.2615 |             0.2608 |                   6.1 |               4.9 | -0.0 (-0.0)                   |
|    0.75 |          75.5 |                 76.9 | 75-79           | 874 |                 77.5 |                 76.6 |        0.1779 |              0.2061 |             0.1934 |                   8   |               7.8 | -0.1 (-0.1)                   |
|    1    |          87.1 |                 88.3 | 87-90           | 874 |                 88.5 |                 87.9 |        0.1033 |              0.1274 |             0.1134 |                   8.9 |               6.6 | -0.1 (-0.1)                   |
|    1.25 |          93.7 |                 94.2 | 93-95           | 874 |                 94.4 |                 94.7 |        0.0545 |              0.0724 |             0.0605 |                   9.9 |               4.4 | +1.4 (+1.4)                   |
|    1.5  |          97.2 |                 97.3 | 96-98           | 874 |                 97.2 |                 97   |        0.0267 |              0.0386 |             0.0297 |                  10   |               3.2 | +1.0 (+1.4)                   |
|    2    |          99.4 |                 99.5 | 99-100          | 874 |                 99.5 |                 99.2 |        0.0051 |              0.009  |             0.006  |                  14.4 |               5.7 | +0.1 (+0.7)                   |

**(ii) price does NOT touch a level u x U away within 10 session(s)** (param = u; U = forecast mean daily range x sqrt(10); upper and lower level pooled)

|   param |   predicted % |   realised % 2010-26 | 95 % interval   |   n |   realised % 2016-26 |   realised % 2023-26 |   Brier model |   Brier naive (all) |   Brier naive (1y) |   skill vs naive 1y % |   skill 2023-26 % | fade: net bp / decision (t)   |
|--------:|--------------:|---------------------:|:----------------|----:|---------------------:|---------------------:|--------------:|--------------------:|-------------------:|----------------------:|------------------:|:------------------------------|
|    0.25 |          30.6 |                 30.1 | 27-33           | 873 |                 30.2 |                 30.3 |        0.2104 |              0.2175 |             0.2209 |                   4.8 |               3.6 | +4.3 (+1.0)                   |
|    0.5  |          56.5 |                 58.4 | 55-62           | 873 |                 58.6 |                 59.3 |        0.2434 |              0.2619 |             0.2608 |                   6.7 |               6   | +1.6 (+0.4)                   |
|    0.75 |          75.1 |                 76.5 | 74-79           | 873 |                 77.7 |                 78.3 |        0.1801 |              0.202  |             0.191  |                   5.7 |               4.7 | +3.0 (+1.1)                   |
|    1    |          87.4 |                 89.1 | 87-91           | 873 |                 89.4 |                 89.9 |        0.0978 |              0.1235 |             0.1083 |                   9.7 |               6.3 | +1.2 (+0.7)                   |
|    1.25 |          94.1 |                 94.8 | 93-96           | 873 |                 94.9 |                 94.4 |        0.0495 |              0.0679 |             0.0562 |                  12   |               4.3 | +0.1 (+0.1)                   |
|    1.5  |          97.1 |                 97.9 | 97-99           | 873 |                 98.1 |                 98.2 |        0.0203 |              0.0317 |             0.0239 |                  15.1 |              12.7 | -0.3 (-0.4)                   |
|    2    |          99.4 |                 99.5 | 99-100          | 873 |                 99.5 |                 99.2 |        0.0051 |              0.0084 |             0.0059 |                  13.7 |               3.4 | -0.1 (-0.6)                   |

**(ii) price does NOT touch a level u x U away within 21 session(s)** (param = u; U = forecast mean daily range x sqrt(21); upper and lower level pooled)

|   param |   predicted % |   realised % 2010-26 | 95 % interval   |   n |   realised % 2016-26 |   realised % 2023-26 |   Brier model |   Brier naive (all) |   Brier naive (1y) |   skill vs naive 1y % |   skill 2023-26 % | fade: net bp / decision (t)   |
|--------:|--------------:|---------------------:|:----------------|----:|---------------------:|---------------------:|--------------:|--------------------:|-------------------:|----------------------:|------------------:|:------------------------------|
|    0.25 |          30.9 |                 31.6 | 27-36           | 870 |                 32.2 |                 32.8 |        0.2162 |              0.2236 |             0.225  |                   3.9 |               4.6 | +4.8 (+0.6)                   |
|    0.5  |          56.9 |                 58.4 | 54-63           | 870 |                 58.8 |                 56.7 |        0.2432 |              0.2599 |             0.2597 |                   6.4 |               4.2 | +5.3 (+0.8)                   |
|    0.75 |          76.1 |                 77.4 | 73-81           | 870 |                 77.8 |                 75.4 |        0.1751 |              0.1968 |             0.1884 |                   7   |               6.1 | +0.2 (+0.0)                   |
|    1    |          86.7 |                 88.4 | 85-91           | 870 |                 88.7 |                 90   |        0.103  |              0.1215 |             0.1129 |                   8.8 |               8.3 | +3.9 (+1.2)                   |
|    1.25 |          92.9 |                 94.5 | 92-96           | 870 |                 95.4 |                 95.1 |        0.0524 |              0.0662 |             0.0578 |                   9.3 |               7.3 | +0.7 (+0.4)                   |
|    1.5  |          96.7 |                 97   | 95-98           | 870 |                 97.1 |                 96.4 |        0.029  |              0.0361 |             0.0313 |                   7.1 |              -0.9 | +2.1 (+1.6)                   |
|    2    |          99.3 |                 99.3 | 98-100          | 870 |                 99.5 |                 99.2 |        0.0069 |              0.0096 |             0.0075 |                   8.3 |               1.8 | +1.7 (+1.9)                   |

**(ii) price does NOT touch a level k x ATR14 away within 10 sessions** (param = k)

|   param |   predicted % |   realised % 2010-26 | 95 % interval   |   n |   realised % 2016-26 |   realised % 2023-26 |   Brier model |   Brier naive (all) |   Brier naive (1y) |   skill vs naive 1y % |   skill 2023-26 % | fade: net bp / decision (t)   |
|--------:|--------------:|---------------------:|:----------------|----:|---------------------:|---------------------:|--------------:|--------------------:|-------------------:|----------------------:|------------------:|:------------------------------|
|       1 |          38.4 |                 38   | 35-41           | 873 |                 38.1 |                 36.4 |        0.2357 |              0.2446 |             0.247  |                   4.6 |               3.1 | +4.9 (+1.1)                   |
|       2 |          68   |                 68.6 | 65-72           | 873 |                 68.9 |                 70.5 |        0.2154 |              0.2354 |             0.2286 |                   5.8 |               7.3 | +2.7 (+0.8)                   |
|       3 |          85.9 |                 86.5 | 84-89           | 873 |                 86.7 |                 87.6 |        0.117  |              0.141  |             0.1273 |                   8.1 |               6.8 | +2.0 (+1.1)                   |

**(ii) price does NOT touch a level k x ATR14 away within 21 sessions** (param = k)

|   param |   predicted % |   realised % 2010-26 | 95 % interval   |   n |   realised % 2016-26 |   realised % 2023-26 |   Brier model |   Brier naive (all) |   Brier naive (1y) |   skill vs naive 1y % |   skill 2023-26 % | fade: net bp / decision (t)   |
|--------:|--------------:|---------------------:|:----------------|----:|---------------------:|---------------------:|--------------:|--------------------:|-------------------:|----------------------:|------------------:|:------------------------------|
|       1 |          27.7 |                 26.5 | 22-31           | 870 |                 26.5 |                 26.2 |        0.195  |              0.1995 |             0.2016 |                   3.3 |               3   | +7.3 (+1.1)                   |
|       2 |          51.7 |                 51.9 | 47-57           | 870 |                 51.9 |                 51.5 |        0.2497 |              0.2642 |             0.2672 |                   6.5 |               4.7 | +2.2 (+0.3)                   |
|       3 |          70.2 |                 71.2 | 67-75           | 870 |                 70.8 |                 68.5 |        0.2053 |              0.2248 |             0.2177 |                   5.7 |               4.7 | +0.4 (+0.1)                   |

**Calibration inside volatility regimes (terciles of the forecast, 2010-26): realised % (predicted %)**

| ev                          | F_low          | F_mid          | F_high        |
|:----------------------------|:---------------|:---------------|:--------------|
| notouch_kATR h=10 param=2.0 | 67 (68) n=558  | 72 (68) n=188  | 72 (68) n=127 |
| notouch_kATR h=10 param=3.0 | 85 (86) n=558  | 90 (86) n=188  | 89 (86) n=127 |
| notouch_kATR h=21 param=2.0 | 51 (52) n=552  | 52 (52) n=189  | 56 (52) n=129 |
| notouch_kATR h=21 param=3.0 | 69 (70) n=552  | 74 (70) n=189  | 77 (70) n=129 |
| notouch_uF h=1 param=0.75   | 75 (74) n=2634 | 76 (74) n=1022 | 77 (74) n=716 |
| notouch_uF h=1 param=1.0    | 86 (86) n=2634 | 87 (86) n=1022 | 88 (86) n=716 |
| notouch_uF h=10 param=0.75  | 75 (75) n=558  | 80 (75) n=188  | 78 (75) n=127 |
| notouch_uF h=10 param=1.0   | 88 (87) n=558  | 91 (87) n=188  | 90 (87) n=127 |
| notouch_uF h=21 param=0.75  | 76 (76) n=552  | 79 (76) n=189  | 81 (76) n=129 |
| notouch_uF h=21 param=1.0   | 87 (87) n=552  | 90 (87) n=189  | 90 (86) n=129 |
| notouch_uF h=5 param=0.75   | 77 (76) n=557  | 78 (75) n=190  | 76 (76) n=127 |
| notouch_uF h=5 param=1.0    | 87 (87) n=557  | 90 (87) n=190  | 89 (87) n=127 |

## 5. (D) Expectancy: accuracy is not edge
Every candidate, then the weekly cells with accuracy >= 60 % on 2010-26 and at least 150 decisions (all 73 cells with >= 30 decisions are in `selective_expectancy.csv`). win / loss = average net bp of winning / losing decisions; Sharpe = net, daily, weekly-tranche book (time exit at the horizon | symmetric stop/target with time-out). `placebo p` = share of 2,000 random rotations of the rule's own call series (>= 26 weeks) that reach the same accuracy / mean bp.
| rule                           |   n |   dec/yr |   acc % |   win |   loss | net bp 10-26 / 16-26 / 23-26   |   hold | Sharpe time exit 10-26 / 16-26 / 23-26   | Sharpe stop/target 10-26 / 16-26 / 23-26   | placebo p acc / bp   |
|:-------------------------------|----:|---------:|--------:|------:|-------:|:-------------------------------|-------:|:-----------------------------------------|:-------------------------------------------|:---------------------|
| sign10_avg_p60                 |   4 |      0.2 |      25 |    40 |   -238 | -168 / - / -                   |     10 | -0.31 / +0.00 / +0.00                    | -0.26 / +0.00 / +0.00                      | -                    |
| sign21_avg_p60                 |  37 |      2.2 |      46 |   340 |   -310 | -11 / +34 / +35                |     21 | -0.03 / +0.10 / +0.13                    | +0.12 / +0.07 / +0.63                      | 0.62 / 0.54          |
| sign42_avg_p60                 | 169 |     10.1 |      49 |   318 |   -351 | -26 / +54 / -7                 |     42 | -0.07 / +0.22 / +0.01                    | +0.01 / +0.40 / +0.11                      | 0.47 / 0.58          |
| sign63_avg_p60                 | 226 |     13.6 |      51 |   340 |   -391 | -19 / +56 / -4                 |     63 | -0.05 / +0.21 / -0.01                    | +0.13 / +0.54 / +0.13                      | 0.38 / 0.53          |
| tb10_2atr_avg_p60              |   7 |      0.4 |      57 |   173 |   -170 | +26 / - / -                    |      7 | +0.08 / +0.00 / +0.00                    | +0.08 / +0.00 / +0.00                      | -                    |
| tb21_2atr_avg_p60              |  11 |      0.7 |      82 |   200 |   -149 | +137 / +57 / +176              |     11 | +0.29 / +0.07 / -0.03                    | +0.46 / +0.21 / +0.99                      | 0.07 / 0.01          |
| tb42_3atr_avg_p60              | 144 |      8.6 |      56 |   278 |   -254 | +38 / +58 / -7                 |     21 | +0.03 / +0.19 / +0.08                    | +0.20 / +0.33 / +0.20                      | 0.21 / 0.13          |
| tb63_3atr_avg_p60              | 206 |     12.4 |      62 |   255 |   -261 | +60 / +95 / +31                |     23 | +0.13 / +0.49 / +0.19                    | +0.39 / +0.78 / +0.51                      | 0.05 / 0.03          |
| sign21_house_p60               | 105 |      6.3 |      45 |   129 |   -194 | -49 / -14 / -14                |     21 | -0.32 / -0.11 / -0.13                    | -0.23 / -0.03 / +0.15                      | 0.82 / 0.92          |
| sign21_logit_p60               |  54 |      3.2 |      46 |   344 |   -354 | -30 / -28 / -                  |     21 | -0.08 / -0.06 / +0.00                    | +0.07 / +0.45 / +0.00                      | 0.66 / 0.70          |
| sign21_agree3                  | 387 |     23.1 |      59 |   185 |   -156 | +46 / +38 / +27                |     21 | +0.52 / +0.51 / +0.43                    | +0.77 / +0.64 / +0.65                      | 0.02 / 0.01          |
| sign21_agree3_trend            | 268 |     16   |      59 |   181 |   -161 | +41 / +46 / +3                 |     21 | +0.39 / +0.51 / +0.13                    | +0.70 / +0.57 / +0.40                      | 0.07 / 0.08          |
| sign42 house cov50             | 409 |     24.6 |      60 |   256 |   -214 | +68 / +69 / +20                |     42 | +0.45 / +0.57 / +0.20                    | +0.68 / +0.74 / +0.34                      | 0.03 / 0.04          |
| sign42 house cov25             | 184 |     11   |      62 |   249 |   -197 | +77 / +86 / -2                 |     42 | +0.39 / +0.52 / +0.03                    | +0.69 / +0.74 / +0.21                      | 0.06 / 0.08          |
| sign63 house cov50             | 402 |     24.2 |      62 |   316 |   -284 | +85 / +97 / +42                |     63 | +0.39 / +0.55 / +0.29                    | +0.73 / +0.86 / +0.26                      | 0.02 / 0.06          |
| sign63 house cov25             | 195 |     11.8 |      67 |   293 |   -245 | +114 / +117 / +23              |     63 | +0.44 / +0.53 / +0.13                    | +0.77 / +0.85 / +0.34                      | 0.02 / 0.07          |
| sign63 house p60               | 407 |     24.5 |      60 |   318 |   -349 | +51 / +95 / +48                |     63 | +0.20 / +0.52 / +0.30                    | +0.46 / +0.86 / +0.45                      | 0.02 / 0.14          |
| sign63 house p65               | 243 |     14.7 |      60 |   321 |   -328 | +64 / +97 / +27                |     63 | +0.18 / +0.42 / +0.13                    | +0.48 / +0.78 / +0.41                      | 0.10 / 0.18          |
| sign63 avg cov50               | 337 |     20.3 |      60 |   294 |   -299 | +54 / +73 / +32                |     63 | +0.25 / +0.39 / +0.19                    | +0.68 / +0.75 / +0.60                      | 0.06 / 0.17          |
| tb21_2atr house cov25          | 184 |     11   |      60 |   150 |   -131 | +38 / +31 / +21                |     10 | +0.48 / +0.50 / +0.36                    | +0.56 / +0.55 / +0.47                      | 0.03 / 0.01          |
| tb21_3atr house cov25          | 187 |     11.2 |      63 |   166 |   -144 | +52 / +42 / +13                |     16 | +0.43 / +0.44 / +0.32                    | +0.54 / +0.52 / +0.30                      | 0.01 / 0.01          |
| tb42_2atr house cov25          | 182 |     10.9 |      63 |   157 |   -146 | +45 / +38 / +16                |     11 | +0.51 / +0.62 / +0.16                    | +0.61 / +0.60 / +0.39                      | 0.01 / 0.01          |
| tb42_2atr house p60            | 225 |     13.5 |      61 |   168 |   -158 | +42 / +30 / +16                |     11 | +0.53 / +0.56 / +0.08                    | +0.58 / +0.51 / +0.37                      | 0.01 / 0.01          |
| tb42_3atr house cov50          | 389 |     23.3 |      63 |   219 |   -207 | +60 / +54 / +17                |     21 | +0.50 / +0.62 / +0.33                    | +0.70 / +0.74 / +0.42                      | 0.00 / 0.01          |
| tb42_3atr house cov25          | 173 |     10.4 |      69 |   224 |   -189 | +93 / +83 / +5                 |     22 | +0.45 / +0.58 / +0.06                    | +0.73 / +0.77 / +0.27                      | 0.00 / 0.00          |
| tb42_3atr house p60            | 325 |     19.5 |      62 |   231 |   -223 | +56 / +68 / +15                |     22 | +0.33 / +0.60 / +0.15                    | +0.54 / +0.76 / +0.37                      | 0.01 / 0.00          |
| tb42_3atr avg cov50            | 405 |     24.3 |      61 |   213 |   -203 | +51 / +54 / +32                |     21 | +0.50 / +0.70 / +0.61                    | +0.63 / +0.77 / +0.66                      | 0.01 / 0.01          |
| tb63_2atr house cov25          | 182 |     11   |      63 |   158 |   -146 | +44 / +40 / +14                |     11 | +0.55 / +0.65 / +0.24                    | +0.60 / +0.64 / +0.35                      | 0.02 / 0.01          |
| tb63_2atr house p60            | 219 |     13.2 |      62 |   168 |   -154 | +44 / +34 / +15                |     11 | +0.52 / +0.59 / +0.15                    | +0.62 / +0.55 / +0.36                      | 0.02 / 0.01          |
| tb63_3atr house cov50          | 390 |     23.5 |      65 |   227 |   -222 | +72 / +73 / +25                |     23 | +0.48 / +0.63 / +0.31                    | +0.81 / +0.94 / +0.53                      | 0.00 / 0.00          |
| tb63_3atr house cov25          | 184 |     11.1 |      71 |   230 |   -213 | +102 / +98 / +3                |     24 | +0.50 / +0.61 / +0.15                    | +0.79 / +0.89 / +0.24                      | 0.00 / 0.00          |
| tb63_3atr house p60            | 372 |     22.4 |      63 |   235 |   -239 | +59 / +75 / +22                |     23 | +0.30 / +0.60 / +0.23                    | +0.58 / +0.87 / +0.45                      | 0.00 / 0.00          |
| tb63_3atr house p65            | 210 |     12.7 |      72 |   252 |   -230 | +119 / +105 / +10              |     24 | +0.45 / +0.56 / +0.19                    | +0.87 / +0.90 / +0.32                      | 0.00 / 0.00          |
| tb63_3atr avg cov50            | 402 |     24.2 |      64 |   221 |   -214 | +64 / +67 / +36                |     23 | +0.40 / +0.65 / +0.39                    | +0.77 / +0.92 / +0.71                      | 0.00 / 0.00          |
| tb63_3atr avg cov25            | 156 |      9.4 |      68 |   220 |   -190 | +89 / +92 / +27                |     24 | +0.40 / +0.53 / +0.24                    | +0.67 / +0.83 / +0.49                      | 0.01 / 0.00          |
| sign42 B:agree3 filter         | 383 |     23   |      65 |   283 |   -206 | +108 / +91 / +26               |     42 | +0.67 / +0.66 / +0.22                    | +0.71 / +0.72 / +0.41                      | 0.00 / 0.00          |
| sign42 B:agree3_trend filter   | 265 |     15.9 |      61 |   289 |   -211 | +89 / +82 / +5                 |     42 | +0.47 / +0.51 / +0.05                    | +0.52 / +0.58 / +0.07                      | 0.07 / 0.04          |
| sign63 B:house_sign_all filter | 862 |     52   |      60 |   331 |   -270 | +90 / +84 / +58                |     63 | +0.67 / +0.71 / +0.48                    | +0.76 / +0.87 / +0.36                      | 0.00 / 0.00          |
| sign63 B:agree3 filter         | 383 |     23.1 |      67 |   345 |   -229 | +153 / +127 / +32              |     63 | +0.66 / +0.66 / +0.19                    | +0.77 / +0.81 / +0.50                      | 0.01 / 0.00          |
| sign63 B:agree3_trend filter   | 265 |     16   |      63 |   345 |   -230 | +135 / +107 / +0               |     63 | +0.50 / +0.48 / +0.02                    | +0.59 / +0.65 / +0.12                      | 0.05 / 0.04          |
| sign63 B:house_quiet filter    | 310 |     18.7 |      64 |   268 |   -192 | +99 / +50 / +31                |     63 | +0.55 / +0.32 / +0.20                    | +0.47 / +0.27 / +0.10                      | 0.04 / 0.07          |
| sign63 B:house_nonevent filter | 483 |     29.1 |      64 |   305 |   -248 | +99 / +104 / +56               |     63 | +0.70 / +0.81 / +0.43                    | +0.90 / +0.87 / +0.30                      | 0.00 / 0.00          |

## 6. Final selection (declared rule) and the record of the picks
| candidate           |   n 10-15 |   dec/yr 10-15 |   acc % 10-15 |   lower bound % (NW) |   lower % (conservative) |   lower % (bootstrap) |   net bp 10-15 | >= 15/yr   | expectancy > 0   | eligible   | final   | P>=60 pick   |
|:--------------------|----------:|---------------:|--------------:|---------------------:|-------------------------:|----------------------:|---------------:|:-----------|:-----------------|:-----------|:--------|:-------------|
| sign10_avg_p60      |         4 |            0.7 |          25   |                  3.7 |                      2.7 |                 nan   |         -168.4 | False      | False            | False      | False   | False        |
| sign21_avg_p60      |        30 |            5   |          46.7 |                 22.3 |                     18.3 |                  12.8 |          -22   | False      | False            | False      | False   | False        |
| sign42_avg_p60      |       116 |           19.4 |          47.4 |                 29.4 |                     24.7 |                  26.1 |          -62.8 | True       | False            | False      | False   | False        |
| sign63_avg_p60      |       109 |           18.2 |          43.1 |                 22.1 |                     17.7 |                  12.2 |          -99.6 | True       | False            | False      | False   | False        |
| tb10_2atr_avg_p60   |         7 |            1.2 |          57.1 |                 21.8 |                     21   |                  22.2 |           26.2 | False      | True             | False      | False   | False        |
| tb21_2atr_avg_p60   |         8 |            1.3 |          87.5 |                 52.9 |                     36.4 |                  50   |          166.6 | False      | True             | False      | False   | False        |
| tb42_3atr_avg_p60   |        91 |           15.2 |          53.8 |                 31.7 |                     31.7 |                  25   |           26.1 | True       | True             | True       | False   | False        |
| tb63_3atr_avg_p60   |        99 |           16.6 |          54.5 |                 32.4 |                     32.4 |                  23.7 |           20.9 | True       | True             | True       | False   | True         |
| sign21_house_p60    |        17 |            2.8 |          11.8 |                  2.7 |                      1.2 |                   0   |         -233.3 | False      | False            | False      | False   | False        |
| sign21_logit_p60    |        52 |            8.7 |          46.2 |                 27   |                     22.8 |                  22.5 |          -30.5 | False      | False            | False      | False   | False        |
| sign21_agree3       |       144 |           24.1 |          63.2 |                 51.6 |                     46.5 |                  51.4 |           59   | True       | True             | True       | True    | False        |
| sign21_agree3_trend |       105 |           17.6 |          61.9 |                 46.8 |                     42.5 |                  45.2 |           33.3 | True       | True             | True       | False   | False        |

Selection under the three interval variants (all 12 / P >= 60 % only): {'lo': ('sign21_agree3', 'tb63_3atr_avg_p60'), 'lo_cons': ('sign21_agree3', 'tb63_3atr_avg_p60'), 'boot_lo': ('sign21_agree3', 'tb42_3atr_avg_p60')}


### `sign21_agree3` - FINAL by the declared rule
| period   |   decisions |   per year |   correct sign before costs % | interval NW   | interval conservative   | interval bootstrap   | eff. n NW / cons   |   up base % |   no-skill acc % |   positive net P&L % |   avg win bp |   avg loss bp |   net bp / decision |   avg hold (sessions) |   long share % |
|:---------|------------:|-----------:|------------------------------:|:--------------|:------------------------|:---------------------|:-------------------|------------:|-----------------:|---------------------:|-------------:|--------------:|--------------------:|----------------------:|---------------:|
| 2010-15  |         144 |       24.1 |                          63.2 | 52-73         | 46-77                   | 51-74                | 71 / 34            |        46   |             51.1 |                 62.5 |          222 |          -213 |                59   |                    21 |             36 |
| 2010-26  |         387 |       23.1 |                          59.4 | 52-66         | 49-69                   | 52-66                | 190 / 92           |        48   |             50.2 |                 59.2 |          185 |          -156 |                45.9 |                    21 |             44 |
| 2016-26  |         243 |       22.6 |                          57.2 | 48-66         | 44-69                   | 48-66                | 121 / 58           |        49.2 |             50   |                 57.2 |          161 |          -126 |                38.2 |                    21 |             49 |
| 2023-26  |          77 |       20.6 |                          54.5 | 38-70         | 33-74                   | 38-70                | 34 / 18            |        52.3 |             50   |                 54.5 |          159 |          -132 |                26.5 |                    21 |             49 |

Non-overlapping stream of the same rule: 2010-26 59 [51-66] n=156 +55bp; 2016-26 57 [47-67] n=96 +48bp; 2023-26 60 [44-74] n=35 +19bp

Weekly-tranche book, daily net P&L (protocol table): 2010-2026 Sharpe +0.52 (t +2.17, +3554 bp); 2016-2026 Sharpe +0.51 (t +1.72, +1846 bp); 2023-2026 Sharpe +0.43 (t +0.85, +509 bp); 2010-2015 Sharpe +0.56 (t +1.38, +1708 bp); deflated-Sharpe p (12 candidates) 0.31; at 0.6 pips: +0.53 / +0.53 / +0.44.

Per year (decisions by decision date):

|   year |   decisions |   long_share |   accuracy |   net_win_rate |   gross_bp |   net_bp |   avg_hold |   book Sharpe |
|-------:|------------:|-------------:|-----------:|---------------:|-----------:|---------:|-----------:|--------------:|
|   2010 |          31 |         0.39 |       0.61 |           0.58 |      86.03 |    84.24 |         21 |          0.77 |
|   2011 |          33 |         0.45 |       0.64 |           0.64 |     100.4  |    98.67 |         21 |          0.95 |
|   2012 |          28 |         0.32 |       0.61 |           0.61 |      15.56 |    13.69 |         21 |          0.2  |
|   2013 |           7 |         1    |       0.43 |           0.43 |    -117.34 |  -119.12 |         21 |         -0.97 |
|   2014 |          24 |         0.12 |       0.75 |           0.75 |      84.55 |    82.74 |         21 |          1.3  |
|   2015 |          21 |         0.29 |       0.62 |           0.62 |      54.12 |    51.99 |         21 |          0.41 |
|   2016 |          24 |         0.5  |       0.58 |           0.58 |      12.06 |     9.89 |         21 |          0.18 |
|   2017 |          19 |         1    |       0.68 |           0.68 |     115.22 |   113.05 |         21 |          1.25 |
|   2018 |          21 |         0    |       0.62 |           0.62 |      52.93 |    50.85 |         21 |          0.62 |
|   2019 |          12 |         0.83 |       0.5  |           0.5  |     -21.35 |   -23.51 |         21 |         -0.07 |
|   2020 |          25 |         1    |       0.52 |           0.52 |      35.4  |    33.28 |         21 |          0.55 |
|   2021 |          34 |         0.15 |       0.44 |           0.44 |      -2.51 |    -4.55 |         21 |         -0.19 |
|   2022 |          31 |         0.32 |       0.74 |           0.74 |     111.43 |   109.17 |         21 |          1.23 |
|   2023 |          17 |         0.71 |       0.35 |           0.35 |     -43.5  |   -45.74 |         21 |         -0.12 |
|   2024 |          23 |         0.13 |       0.52 |           0.52 |      44.62 |    42.4  |         21 |          0.57 |
|   2025 |          19 |         1    |       0.63 |           0.63 |      63.18 |    61.11 |         21 |          0.81 |
|   2026 |          18 |         0.22 |       0.67 |           0.67 |      40.06 |    37.99 |         21 |          0.65 |

Incremental test, EW(weak_signals, regime_trend) -> EW(+ this stream), net Sharpe: 2010-2026 0.56 -> 0.57; 2016-2026 0.64 -> 0.64; 2023-2026 0.36 -> 0.40. Daily P&L correlation with weak_signals 0.43, with regime_trend 0.63.

### `tb63_3atr_avg_p60` - pick of the same rule among the ten P >= 60 % probability calls
| period   |   decisions |   per year |   correct sign before costs % | interval NW   | interval conservative   | interval bootstrap   | eff. n NW / cons   |   up base % |   no-skill acc % |   positive net P&L % |   avg win bp |   avg loss bp |   net bp / decision |   avg hold (sessions) |   long share % |
|:---------|------------:|-----------:|------------------------------:|:--------------|:------------------------|:---------------------|:-------------------|------------:|-----------------:|---------------------:|-------------:|--------------:|--------------------:|----------------------:|---------------:|
| 2010-15  |          99 |       16.6 |                          54.5 | 32-75         | 32-75                   | 24-74                | 17 / 17            |        48.6 |             48.6 |                 54.5 |          301 |          -315 |                20.9 |                  22.7 |            100 |
| 2010-26  |         206 |       12.4 |                          62.1 | 48-74         | 48-75                   | 48-75                | 49 / 45            |        49.3 |             49.8 |                 62.1 |          255 |          -261 |                59.6 |                  23   |             65 |
| 2016-26  |         107 |       10.1 |                          69.2 | 54-81         | 49-84                   | 53-84                | 41 / 23            |        49.7 |             50.1 |                 69.2 |          221 |          -186 |                95.5 |                  23.2 |             33 |
| 2023-26  |          54 |       15.1 |                          55.6 | 36-74         | 31-78                   | 36-78                | 22 / 13            |        55.1 |             48.5 |                 55.6 |          198 |          -178 |                30.7 |                  20.1 |             35 |

Non-overlapping stream of the same rule: 2010-26 50 [40-60] n=102 +4bp; 2016-26 51 [38-64] n=55 +18bp; 2023-26 50 [33-67] n=28 +2bp

Weekly-tranche book, daily net P&L (protocol table): 2010-2026 Sharpe +0.39 (t +1.62, +945 bp); 2016-2026 Sharpe +0.78 (t +2.61, +786 bp); 2023-2026 Sharpe +0.51 (t +1.03, +227 bp); 2010-2015 Sharpe +0.13 (t +0.32, +159 bp); deflated-Sharpe p (12 candidates) 0.51; at 0.6 pips: +0.39 / +0.79 / +0.53.

Per year (decisions by decision date):

|   year |   decisions |   long_share |   accuracy |   net_win_rate |   gross_bp |   net_bp |   avg_hold |   book Sharpe |
|-------:|------------:|-------------:|-----------:|---------------:|-----------:|---------:|-----------:|--------------:|
|   2010 |          52 |         1    |       0.5  |           0.5  |      21.1  |    19.28 |      20.38 |         -0.09 |
|   2011 |          30 |         1    |       0.53 |           0.53 |      -4.24 |    -5.96 |      23.73 |          0.28 |
|   2012 |          12 |         1    |       0.92 |           0.92 |     169.46 |   167.59 |      29.5  |          1.11 |
|   2014 |           5 |         1    |       0.2  |           0.2  |    -151.15 |  -153.01 |      25.2  |         -1.39 |
|   2016 |           1 |         0    |       1    |           1    |     272.96 |   270.7  |      15    |          1.01 |
|   2018 |           8 |         0    |       0.75 |           0.75 |     128.05 |   125.98 |      29.5  |          0.82 |
|   2019 |           1 |         1    |       0    |           0    |    -221.1  |  -223.19 |      43    |         -0.98 |
|   2020 |           2 |         1    |       1    |           1    |     278.04 |   275.88 |      34.5  |          1.55 |
|   2021 |          21 |         0    |       0.81 |           0.81 |      92.91 |    90.88 |      25.29 |          1.16 |
|   2022 |          20 |         0.65 |       0.9  |           0.9  |     254.39 |   252.09 |      25.05 |          2.18 |
|   2023 |          16 |         0.69 |       0.38 |           0.38 |     -39.12 |   -41.36 |      18.56 |          0.34 |
|   2024 |          24 |         0    |       0.54 |           0.54 |      32.03 |    29.79 |      23.29 |          0.37 |
|   2025 |           6 |         1    |       1    |           1    |     226.38 |   224.23 |      19    |          1.35 |
|   2026 |           8 |         0.25 |       0.62 |           0.62 |      34.59 |    32.54 |      14.12 |          0.66 |

Incremental test, EW(weak_signals, regime_trend) -> EW(+ this stream), net Sharpe: 2010-2026 0.56 -> 0.64; 2016-2026 0.64 -> 0.75; 2023-2026 0.36 -> 0.44. Daily P&L correlation with weak_signals 0.19, with regime_trend 0.15.

**The fixed rule's own probability** (hit rate of `sign21_agree3` weekly decisions whose label was known before the test year; history starts 2006; this is the `prob` column of the positions file, converted to P(up)):

|   test_year |   history_decisions |   history_hit_rate |   prob_correct_used |
|------------:|--------------------:|-------------------:|--------------------:|
|        2010 |                  33 |              0.455 |               0.457 |
|        2011 |                  67 |              0.537 |               0.536 |
|        2012 |                  96 |              0.562 |               0.561 |
|        2013 |                 127 |              0.575 |               0.574 |
|        2014 |                 135 |              0.57  |               0.569 |
|        2015 |                 159 |              0.597 |               0.596 |
|        2016 |                 179 |              0.598 |               0.597 |
|        2017 |                 203 |              0.596 |               0.595 |
|        2018 |                 223 |              0.605 |               0.604 |
|        2019 |                 244 |              0.607 |               0.606 |
|        2020 |                 253 |              0.601 |               0.6   |
|        2021 |                 278 |              0.601 |               0.6   |
|        2022 |                 312 |              0.58  |               0.58  |
|        2023 |                 342 |              0.588 |               0.587 |
|        2024 |                 362 |              0.583 |               0.582 |
|        2025 |                 385 |              0.577 |               0.576 |
|        2026 |                 401 |              0.581 |               0.581 |

## 7. Leak checks
Weekly decisions, 2010-26, accuracy / n. `shuffled_labels`: every label permuted (target and the 1-session return the house weights are fitted on). `features_stale_plusK`: all features K sessions older. `lookahead_control`: features taken h sessions in the future - NOT a result, it shows the harness would expose a look-ahead.

*sign21*

| check                     | agree3     | agree3_trend    | avg cov10   | avg cov100   | avg p60    | house cov100   | house cov25   | house p60   | house_sign_all    | logit cov100   | logit p60   |
|:--------------------------|:-----------|:----------------|:------------|:-------------|:-----------|:---------------|:--------------|:------------|:------------------|:---------------|:------------|
| baseline                  | 59.4 / 387 | 59.3 / 268      | 64.4 / 59   | 49.8 / 870   | 45.9 / 37  | 52.4 / 870     | 56.3 / 199    | 44.8 / 105  | 55.5 / 870        | 48.6 / 870     | 46.3 / 54   |
| features_stale_plus1      | 59.2 / 400 | 57.6 / 283      | 60.0 / 45   | 50.2 / 870   | 50.0 / 30  | 51.6 / 870     | 54.0 / 215    | 58.1 / 93   | 55.6 / 870        | 48.6 / 870     | 46.7 / 45   |
| features_stale_plus21     | 57.5 / 355 | 50.6 / 247      | 44.2 / 52   | 53.0 / 870   | 28.2 / 39  | 54.1 / 870     | 56.7 / 180    | 50.5 / 186  | 55.2 / 870        | 48.7 / 870     | 0.0 / 3     |
| features_stale_plus63     | 58.9 / 380 | 56.5 / 262      | 58.1 / 93   | 51.3 / 870   | 48.9 / 47  | 54.7 / 870     | 55.1 / 216    | 54.2 / 212  | 53.9 / 870        | 47.8 / 870     | 45.5 / 11   |
| lookahead_control_minus21 | 86.3 / 401 | 92.3 / 323      | 100.0 / 60  | 87.9 / 870   | 91.6 / 787 | 85.6 / 870     | 100.0 / 190   | 89.1 / 786  | 86.0 / 870        | 87.9 / 870     | 90.1 / 815  |
| shuffled_labels_0         | 50.2 / 265 | 51.3 / 193      | 42.2 / 64   | 47.6 / 872   | -          | 50.6 / 872     | 48.4 / 285    | -           | 49.8 / 872        | 49.2 / 872     | -           |
| shuffled_labels_1         | 53.6 / 250 | 54.4 / 160      | 46.3 / 82   | 51.3 / 872   | -          | 50.3 / 872     | 50.6 / 233    | -           | 49.2 / 872        | 51.1 / 872     | -           |
| shuffled_labels_2         | 43.3 / 180 | 43.7 / 103      | 49.4 / 89   | 49.3 / 873   | -          | 50.5 / 873     | 45.7 / 269    | -           | 48.0 / 873        | 48.2 / 873     | -           |

*tb63_3atr*

| check                     | avg cov10   | avg cov100   | avg p60    | house cov100   | house cov25   | house p60   | logit cov100   | logit p60   |
|:--------------------------|:------------|:-------------|:-----------|:---------------|:--------------|:------------|:---------------|:------------|
| baseline                  | 69.7 / 66   | 54.5 / 862   | 62.1 / 206 | 54.4 / 862     | 71.2 / 184    | 62.9 / 372  | 48.4 / 862     | 51.1 / 141  |
| features_stale_plus1      | 66.7 / 60   | 55.6 / 862   | 59.7 / 233 | 56.0 / 862     | 69.6 / 184    | 60.4 / 409  | 49.5 / 862     | 50.7 / 146  |
| features_stale_plus21     | 57.7 / 71   | 56.3 / 862   | 58.8 / 245 | 54.5 / 862     | 65.0 / 163    | 58.7 / 358  | 52.4 / 862     | 53.3 / 169  |
| features_stale_plus63     | 63.0 / 54   | 56.0 / 862   | 57.5 / 167 | 57.3 / 862     | 63.1 / 168    | 62.8 / 293  | 51.7 / 862     | 45.9 / 98   |
| lookahead_control_minus63 | 94.7 / 95   | 74.5 / 862   | 80.5 / 614 | 75.9 / 862     | 90.6 / 191    | 81.4 / 683  | 66.5 / 862     | 72.5 / 581  |
| shuffled_labels_0         | 40.5 / 74   | 50.6 / 868   | -          | 50.6 / 868     | 51.3 / 189    | -           | 50.6 / 868     | -           |
| shuffled_labels_1         | 45.3 / 53   | 53.5 / 866   | -          | 53.5 / 866     | 51.7 / 240    | -           | 53.5 / 866     | -           |
| shuffled_labels_2         | 57.7 / 26   | 50.9 / 865   | -          | 51.3 / 865     | 52.7 / 169    | -           | 51.1 / 865     | -           |

**Top weights of the last fit (2026) and full-sample correlation of each input with the label**

| target   |   fit_year | model   | feature                                                  |   weight |   corr_with_label_full_sample |
|:---------|-----------:|:--------|:---------------------------------------------------------|---------:|------------------------------:|
| sign21   |       2026 | logit   | cot_z52                                                  |    0.126 |                         0.151 |
| sign21   |       2026 | logit   | spx_minus_sx5e_20                                        |   -0.082 |                        -0.086 |
| sign21   |       2026 | logit   | month_11                                                 |    0.075 |                         0.078 |
| sign21   |       2026 | logit   | month_10                                                 |   -0.07  |                        -0.062 |
| sign21   |       2026 | logit   | cot_lev_z52                                              |    0.068 |                         0.108 |
| sign21   |       2026 | logit   | d_spread10y_20                                           |   -0.064 |                        -0.037 |
| sign21   |       2026 | logit   | usd_jpy_ret_20                                           |   -0.061 |                        -0.048 |
| sign21   |       2026 | logit   | cot_net_pct                                              |    0.055 |                         0.116 |
| sign21   |       2026 | logit   | us10y                                                    |    0.049 |                         0.077 |
| sign21   |       2026 | logit   | usd_aud_ret_20                                           |   -0.048 |                        -0.057 |
| sign21   |       2026 | house   | fomc                                                     |    0.117 |                        -0.006 |
| sign21   |       2026 | house   | cot                                                      |    0.159 |                         0.154 |
| sign21   |       2026 | house   | spread                                                   |    0.156 |                         0.039 |
| sign21   |       2026 | house   | mom63                                                    |    0.024 |                         0.02  |
| sign21   |       2026 | house   | mom21                                                    |    0.019 |                         0.037 |
| sign21   |       2026 | house   | fv                                                       |    0.038 |                        -0.016 |
| sign21   |       2026 | house   | gap                                                      |    0.068 |                         0.02  |
| sign21   |       2026 | house   | tom                                                      |    0.033 |                        -0.019 |
| sign21   |       2026 | house   | usdmom                                                   |    0.009 |                         0.043 |
| sign21   |       2026 | house   | vix                                                      |    0.008 |                         0.019 |
| sign21   |       2026 | house   | eqrel                                                    |    0.171 |                         0.095 |
| sign21   |       2026 | house   | mom252                                                   |    0.081 |                         0.039 |
| sign21   |       2026 | house   | season                                                   |    0.117 |                         0.014 |
| sign21   |       2026 | house   | dow                                                      |    0     |                         0.002 |
| sign21   |       2026 | logit   | MAX |corr| of any of the 82 logit columns with the label |  nan     |                         0.151 |

(The same table for the other target is in `selective_leak_features.csv`; its largest |corr| is 0.22.)
