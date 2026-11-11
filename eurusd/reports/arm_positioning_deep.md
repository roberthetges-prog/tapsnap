# Arm G: the structure of CFTC positioning (`positioning_deep`)

Code `src/eurusd/arms/positioning_deep.py` (`run(cost_pips=1.2)`; `python src/eurusd/arms/positioning_deep.py` runs `run()` and
`analysis()`, about 40 s). Positions of the final variant `experiments/results/arms/positioning_deep_positions.parquet`
(pos, fwd_bp, net_bp), all variants `positioning_deep_report.csv` (`variant`, `kind`, `cost_pips`, `final`, `live_from`), all streams
`positioning_deep_all_positions.parquet`, and the analysis tables `positioning_deep_{extremes,flow_price,lags,shutdown,shuffle,vs_baseline,combos,corr,label_corr}.csv`.

**Verdict: clean negative on the incremental question.** No richer positioning signal improves on the crude rule
sign(z52 of non-commercial net / OI). The variant picked by the declared rule (`ext_flat`) earns net Sharpe
0.67 / 0.54 / 0.41 (2010-26 / 2016-26 / 2023-26) against 0.70 / 0.60 / 0.31 for the crude rule, is 0.91 correlated with
the existing positioning stream, and the three-way combination gains exactly what adding a second copy of the crude
rule gains. The useful output is descriptive: what the structure of the data says about why the crude rule works.

## Idea and data
Only the crudest form of positioning had been used. The CFTC reports also split speculators into groups (TFF), give
gross long and short legs, open interest, trader counts and concentration ratios. Twelve economically motivated
signals were declared in the module docstring before any result was computed, each a daily position in [-1, 1]
= weekly signal x the live vol scale clip(median_train(rv_21d_bp) / rv_21d_bp, 0, 1.5), yearly expanding walk-forward
(`eurusd.wf`). The vol target is the only fitted quantity; all directions, windows and thresholds are fixed a priori.

* Weekly data: `data/macro/cot_eurofx_deep.csv` (1,453 rows 1999-01-05..2026-11-03, 43 columns), built by `build_deep()` from
  the raw zips in `data/raw/cftc/`. Legacy part identical to `cot_eurofx_legacy.csv` plus trader counts and concentration.
* **New raw data**: `fin_fut_txt_2006_2016.zip` from `https://www.cftc.gov/files/dea/history/` (CFTC TFF history file,
  2006-06-13..2016-12-27; used for 2006-06-13..2010-07-13, 214 extra weeks; on the 337 overlapping weeks it equals the
  project's `cot_eurofx_tff.csv` exactly). Stored git-ignored in `data/raw/cftc/`; `build_deep()` re-downloads it if missing.
* Publication lag: report date (Tuesday) + 6 days, then the feature store's one-calendar-day lag, exactly as
  `featstore.py` does for `cot_z52`; positions change at the NY close one week after the report date. Rolling statistics
  and differences are computed on the weekly rows before alignment.
* TFF starts 2006-06-13, so a TFF-based signal is live from the first test year with 5 calendar years of history: **2012**.
  Legacy-based signals are live from 2010. TFF variants should be judged on 2016-2026 only.

## Baseline reproduction
`base_nc_z52` rebuilt from the raw zips: daily z-score equals the feature store's `cot_z52` (max abs difference 0.0), and
the positions equal regime_trend's `cot_uncond` stream exactly (max abs difference 0.0): net Sharpe **0.70 / 0.60 / 0.31**,
t 2.91 / 2.01 / 0.62. The quoted 0.74 for 2010-26 is regime_trend's final `cot_regimeK3`, i.e. the same rule with an
HMM gate that was partly closed in 2010-2013 only; from 2014 the two are identical, hence the same 0.60 / 0.31.

## Selection rule and count
Final = the candidate with the highest 2010-2015 walk-forward net Sharpe at 1.2 pips of its stream as delivered (zeros
where not live). 12 candidates declared, **11 distinct**: `flow_build13` and `flow_cover13` turned out to be algebraically
the same series, (sign d13 long - sign d13 short) / 2 - a definition error found after the first run, left as declared.
Baseline, 30 diagnostics and 12 window-robustness streams were never eligible. Deflated-Sharpe p uses 12 trials.

## Candidates (net Sharpe at 1.2 pips; turnover is 6-23 units a year, so 0.6 pips changes nothing)

| variant | live | SR 10-15 | SR 10-26 | t | SR 16-26 | t | SR 23-26 | t | SR 10-26 @0.6 | P&L corr with baseline 16-26 | paired diff vs baseline, t 16-26 | residual alpha t 16-26 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| base_nc_z52 (baseline) | 2010 | 0.85 | 0.70 | 2.91 | 0.60 | 2.01 | 0.31 | 0.62 | 0.70 | 1.00 | | |
| am_z52 | 2012 | -0.25 | 0.30 | 1.25 | 0.59 | 1.97 | 0.06 | 0.13 | 0.31 | 0.65 | -0.05 | 0.87 |
| lev_z52 | 2012 | 0.36 | 0.53 | 2.22 | 0.63 | 2.09 | 0.66 | 1.32 | 0.54 | 0.66 | 0.10 | 1.01 |
| am_lev_agree | 2012 | 0.08 | 0.53 | 2.22 | 0.74 | 2.47 | 0.40 | 0.79 | 0.54 | 0.80 | 0.04 | 1.44 |
| flow_combo | 2010 | 0.27 | 0.18 | 0.74 | 0.12 | 0.39 | 0.57 | 1.14 | 0.20 | 0.54 | -1.96 | -0.83 |
| flow_build13 (= flow_cover13) | 2010 | 0.80 | 0.53 | 2.22 | 0.34 | 1.13 | 0.40 | 0.80 | 0.54 | 0.62 | -1.34 | -0.14 |
| **ext_flat (final)** | 2010 | **0.87** | **0.67** | **2.80** | **0.54** | **1.81** | **0.41** | **0.82** | 0.68 | 0.91 | -0.88 | -0.07 |
| ext_fade | 2010 | 0.79 | 0.55 | 2.29 | 0.39 | 1.29 | 0.42 | 0.85 | 0.56 | 0.67 | -0.88 | -0.07 |
| oi_conviction | 2010 | 0.04 | 0.40 | 1.65 | 0.64 | 2.13 | 0.54 | 1.08 | 0.41 | 0.78 | -0.55 | 0.90 |
| breadth_z52 | 2010 | 0.64 | 0.52 | 2.17 | 0.44 | 1.48 | 0.39 | 0.78 | 0.53 | 0.69 | -0.67 | 0.14 |
| div_follow_pos | 2010 | 0.22 | 0.43 | 1.79 | 0.56 | 1.88 | 1.10 | 2.19 | 0.45 | 0.17 | -1.05 | 1.56 |
| deep_combo | 2010 | 0.83 | 0.71 | 2.96 | 0.63 | 2.12 | 0.47 | 0.93 | 0.72 | 0.92 | -0.53 | 0.68 |

"Paired diff" is the t-statistic of (candidate - baseline) daily net bp on 2016-2026; the largest is +0.10. Four
candidates have a higher 2016-2026 Sharpe than the baseline (am_lev_agree 0.74, oi_conviction 0.64, lev_z52 0.63,
deep_combo 0.63); with a standard error of about 0.2 on each difference and a best-of-11 pick, none is an improvement.

## Final variant `ext_flat` (crude rule, flat while |z52| > 2), per year

| period | n | SR @1.2 | t | mean bp/day | active | SR @0.6 | baseline SR |
|---|---|---|---|---|---|---|---|
| 2010 | 260 | 1.35 | 1.37 | 4.69 | 0.81 | 1.36 | 1.30 |
| 2011 | 260 | 1.49 | 1.51 | 5.33 | 0.89 | 1.50 | 1.34 |
| 2012 | 260 | 0.83 | 0.84 | 2.57 | 0.93 | 0.83 | 0.95 |
| 2013 | 259 | -0.63 | -0.64 | -1.62 | 0.81 | -0.62 | -0.68 |
| 2014 | 258 | 1.83 | 1.85 | 4.16 | 0.79 | 1.84 | 2.23 |
| 2015 | 259 | 0.36 | 0.36 | 1.31 | 0.92 | 0.36 | 0.16 |
| 2016 | 259 | 1.12 | 1.13 | 3.32 | 0.90 | 1.13 | 0.68 |
| 2017 | 259 | 1.26 | 1.28 | 3.11 | 0.75 | 1.27 | 1.92 |
| 2018 | 260 | -0.18 | -0.18 | -0.45 | 0.77 | -0.17 | 0.05 |
| 2019 | 260 | -0.05 | -0.05 | -0.10 | 1.00 | -0.04 | -0.05 |
| 2020 | 260 | 1.09 | 1.11 | 2.50 | 0.79 | 1.10 | 0.83 |
| 2021 | 259 | 0.19 | 0.19 | 0.41 | 0.88 | 0.19 | 0.40 |
| 2022 | 260 | 0.64 | 0.65 | 1.81 | 0.83 | 0.66 | 1.17 |
| 2023 | 258 | 0.42 | 0.43 | 1.11 | 0.88 | 0.43 | 0.11 |
| 2024 | 261 | 0.44 | 0.45 | 0.80 | 0.73 | 0.46 | 0.87 |
| 2025 | 260 | 0.07 | 0.07 | 0.20 | 0.97 | 0.08 | 0.01 |
| 2026 (to Nov 5) | 220 | 0.95 | 0.89 | 1.88 | 0.71 | 0.96 | 0.40 |
| **2010-2026** | 4372 | **0.67** | **2.80** | 1.82 | 0.85 | 0.68 | 0.70 |
| **2016-2026** | 2816 | **0.54** | **1.81** | 1.32 | 0.84 | 0.55 | 0.60 |
| **2023-2026** | 999 | **0.41** | **0.82** | 0.96 | 0.83 | 0.42 | 0.31 |
| 2010-2015 | 1556 | 0.87 | 2.16 | 2.74 | 0.86 | 0.88 | 0.85 |
| 2016-2022 | 1817 | 0.61 | 1.64 | 1.51 | 0.85 | 0.62 | 0.76 |

Deflated-Sharpe p (12 trials) = 0.13. It beat the baseline in 8 of 17 years. It won the selection by 0.02 Sharpe
(0.87 vs 0.85 for the baseline, 0.83 for deep_combo); the shuffled-label control below shows that a pure-noise winner
of this selection averages +0.43 in the selection window, so the pick carries no information.

## What the structure says

**1. Who is informed: nobody in particular.** Sign of the 52-week z-score by group, 2016-2026 net Sharpe:
asset managers 0.59, leveraged funds 0.63, dealers faded 0.74, legacy commercials faded 0.67, non-reportables 0.62,
legacy non-commercials 0.60, other reportables 0.31. Every speculative group, and the mirror image of the dealers,
gives the same signal with the same strength (P&L correlations with the baseline 0.56-0.96; other reportables 0.11). When asset managers and
leveraged funds disagree, following either against the other earns nothing (`diag_am_minus_lev` -0.06, 2023-26 -0.78).
Going flat on disagreement (`am_lev_agree`) has the best 2016-2026 Sharpe of the arm (0.74) only because it cuts risk
in the disagreement weeks; its mean P&L equals the baseline's (paired t 0.04). Weekly flow / return correlations
(descriptive, 2006-2026, `positioning_deep_flow_price.csv`):

| group | flow vs previous week's return | vs same week's return | vs next week's return | vs week after next (tradable) |
|---|---|---|---|---|
| non-commercial | 0.20 | 0.38 | 0.01 | 0.02 |
| asset managers | 0.23 | 0.18 | -0.05 | -0.04 |
| leveraged funds | 0.18 | 0.30 | 0.01 | 0.02 |
| dealers | -0.26 | -0.39 | 0.01 | 0.00 |
| other reportables | -0.03 | 0.08 | 0.01 | -0.02 |

All speculative groups chase the current and the previous week's move, dealers absorb it, and no group's flow leads
the next weeks. Asset managers do not lead leveraged funds (2016-2026: -0.12 / -0.07 on the next two weeks).

**2. Flows vs levels: the level is the signal.** 1-week and 4-week changes of net positions are worthless or negative
(2016-2026 Sharpe -0.32 and 0.01 for non-commercials; -0.41 / -0.05 asset managers; -0.38 / -0.41 leveraged funds).
The 13-week change earns 0.57 but is 0.69 correlated with the level rule and has no residual alpha (t 0.72).
`flow_combo` 0.12. Gross legs: the short leg carries more than the long leg (fade the z52 of gross shorts 0.71 against
follow the z52 of gross longs 0.45; 13-week short-leg flow 0.44 against long-leg flow 0.10), but the short-leg rule is
0.86 correlated with the baseline and its residual alpha t is 1.26. Post-hoc split of the 13-week net flow by dominant
leg: building 0.28, covering / liquidation 0.50; not different from each other within noise.

**3. Extremes: the trend-following rule does not fail at |z| > 2, it only weakens.** Baseline P&L by |z52| bucket
(gross, bucket days only, `positioning_deep_extremes.csv`):

| abs z52 | 2010-26 days | mean bp/day | SR on bucket days | 2016-26 days | mean bp/day | SR on bucket days |
|---|---|---|---|---|---|---|
| 0 - 0.5 | 838 | 0.30 | 0.11 | 498 | -0.03 | -0.01 |
| 0.5 - 1 | 815 | 3.79 | 1.16 | 486 | 2.51 | 0.89 |
| 1 - 1.5 | 1180 | 2.38 | 0.82 | 812 | 1.30 | 0.48 |
| 1.5 - 2 | 864 | 2.32 | 0.81 | 568 | 2.77 | 1.11 |
| > 2 | 675 (36 episodes) | 1.31 | 0.47 (t 0.77) | 452 (25 episodes) | 1.67 | 0.62 (t 0.83) |
| > 2.5 | 208 (15 episodes) | 0.55 | 0.20 | 140 (10 episodes) | -0.22 | -0.09 |

Following the sign is still positive beyond 2 sd (15 % of days), so flattening gives up a small positive return
(`ext_flat` 0.54 vs 0.60 on 2016-2026) and fading costs more (`ext_fade` 0.39). Beyond 2.5 sd the mean is about zero
with opposite signs on the two sides (long extremes +3.9 bp, short extremes -3.8 bp in 2010-2026) on 15 episodes: no
basis for a contrarian rule. The only visible non-monotonicity is at the other end: the rule earns nothing when
|z| < 0.5 (19 % of days). That is an observation made after the fact, not a tested variant.

**4. Open interest: unstable.** The baseline held only while OI is above its level 13 reports earlier earns 0.64 on
2016-2026 and the falling-OI part 0.13, but in 2010-2015 it was the reverse (0.04 vs 1.22). No usable conditioning.

**5. Trader counts and concentration: the same signal again.** Head-count breadth of non-commercials (z52 of
(nL - nS) / (nL + nS)) earns 0.52 / 0.44 / 0.39, 0.69 correlated with the baseline, residual alpha t 0.14. The top-4
net concentration (long minus short) is consistently negative as a follow signal (-0.46 / -0.39 / -0.38) because the
four largest net traders are the dealer / commercial side; it is -0.70 correlated with the baseline.

**6. z-score window (robustness table, not a search).**

| series | window (weeks) | SR 10-15 | SR 10-26 | SR 16-26 | t 16-26 | SR 23-26 |
|---|---|---|---|---|---|---|
| non-commercial | 26 | 0.53 | 0.40 | 0.31 | 1.05 | 0.09 |
| non-commercial | **52** | 0.85 | 0.70 | 0.60 | 2.01 | 0.31 |
| non-commercial | 104 | 0.28 | 0.48 | 0.62 | 2.08 | 0.32 |
| non-commercial | 156 | 0.31 | 0.43 | 0.51 | 1.69 | 0.17 |
| asset managers | 26 / 52 / 104 / 156 | 0.09 / -0.25 / 0.26 / 0.22 | 0.28 / 0.30 / 0.30 / 0.11 | 0.38 / 0.59 / 0.32 / 0.05 | 1.27 / 1.97 / 1.07 / 0.18 | 0.02 / 0.06 / 0.03 / -0.42 |
| leveraged funds | 26 / 52 / 104 / 156 | 0.50 / 0.36 / 0.35 / 0.39 | 0.34 / 0.53 / 0.35 / 0.16 | 0.25 / 0.63 / 0.34 / 0.04 | 0.84 / 2.09 / 1.15 / 0.13 | 0.20 / 0.66 / 0.37 / 0.01 |
| breadth | 26 / 52 / 104 / 156 | 0.55 / 0.64 / 0.42 / 0.23 | 0.46 / 0.52 / 0.42 / 0.20 | 0.41 / 0.44 / 0.42 / 0.19 | 1.37 / 1.48 / 1.41 / 0.63 | 0.07 / 0.39 / 0.10 / -0.04 |

For the legacy non-commercial series the sign is positive at every window and 52-156 weeks give 0.5-0.6 on 2016-2026,
so the crude rule is not a knife-edge there; the 2010-2015 advantage of 52 weeks (0.85 vs 0.3-0.5) is the round-1
selection. For the TFF groups 52 weeks is clearly the best window on 2016-2026 and 156 weeks is zero, which says the
0.59-0.63 of the group rules partly rides on the window that was already chosen on the legacy series.

**7. Positioning x price divergence: the edge is not a trend proxy, and may sit where positioning disagrees with price.**
Splitting the baseline by agreement with the sign of the 26-week price change: against the price trend 0.67 / 0.58 /
0.73, with it 0.40 / 0.33 / -0.09. The candidate `div_follow_pos` (13-week positioning flow when it opposes the 13-week
price change) earns 0.43 / 0.56 / 1.10 with only 0.17 correlation to the baseline and 0.14 to weak_signals, and is the
only stream here that would add to the stack (three-way 0.77 vs 0.64 on 2016-2026). It is NOT a result: it was 0.22 in
2010-2015 and so not selected, it is the best of 11 by hindsight (alpha t against the two live streams 1.50), and it is
timing-fragile (2016-2026 Sharpe 0.46 / 0.56 / 0.41 / 0.14 / 0.18 / 1.04 at lead 2, as run, lag 1 / 5 / 10 / 20
sessions, where the baseline stays within 0.50-0.69). Worth a forward watch, nothing more.

## Incremental test (EW, `eurusd.arms.meta`; `positioning_deep_combos.csv`, `positioning_deep_corr.csv`)

| combination | SR 2010-26 | SR 2016-26 | t 2016-26 | SR 2023-26 |
|---|---|---|---|---|
| two-way: weak_signals + regime_trend | 0.563 | 0.636 | 2.13 | 0.356 |
| three-way: + positioning_deep (ext_flat) | 0.569 | 0.644 | 2.16 | 0.406 |
| placebo three-way: + a copy of the crude rule | 0.567 | 0.646 | 2.16 | 0.354 |
| replacement: weak_signals + positioning_deep | 0.523 | 0.620 | 2.07 | 0.436 |

Daily P&L correlation of the final stream: **0.88 with regime_trend (0.91 on 2016-2026)**, 0.21 with weak_signals;
alpha against both t 0.34 (2010-26) and 0.14 (2016-26). The three-way combination is nominally 0.008 above the two-way
on 2016-2026, but a second copy of the crude rule does the same (0.646), so the gain is the heavier weight on
positioning, not new information. Replacing regime_trend's stream with this one is worse on 2010-2026 (0.52 vs 0.56)
and 2016-2026 (0.62 vs 0.64) and slightly better on 2023-2026 (0.44 vs 0.36, t < 1): do not replace.
Formal success bar: standalone 2016-2026 0.54 > 0.3 yes, 2023-2026 0.41 not negative yes, three-way > two-way by
0.008 yes in the letter - **but the arm fails its own question: it adds nothing to the crude positioning rule.**

## Leak checks
1. **Shuffled labels** (fwd_1d permuted over all rows, 20 seeds, baseline + 12 candidates + the selection rule re-run):
   selected final 2016-2026 Sharpe mean -0.09 (sd 0.31, range -0.73..+0.29), 2010-2026 mean +0.07 (sd 0.23);
   baseline 2010-2026 mean -0.03 (sd 0.26). The selection window itself averages +0.43 for the noise winner, which is the
   selection bias of a best-of-12 pick on six years and is why 2010-2015 is not evidence.
2. **Shifted features** (`positioning_deep_lags.csv`, 2010-26 / 2016-26 Sharpe): the signal is weekly and slow, so a
   one-session delay cannot collapse it; baseline 0.64 / 0.50 at lag 1, 0.73 / 0.69 at lag 5, 0.67 / 0.53 at lag 10,
   0.85 / 0.53 at lag 20; final 0.53 / 0.36, 0.57 / 0.53, 0.49 / 0.38, 0.71 / 0.30. That +-0.15 timing noise is as large
   as every difference between variants in this arm. Leading instead: trading at the Friday close after publication
   (lead 2, legitimate) 0.72 / 0.54; at the report Tuesday itself (lead 5, not yet published) 0.42 / 0.28, no gain; with
   next week's report (lead 10, true look-ahead) the baseline rises to 0.96 and the 1-week-flow probe jumps from -0.19
   to **1.70**, because flows are 0.38 correlated with the same week's return. The pipeline is alignment-sensitive
   exactly where it should be, and the as-run alignment sits one full week outside the measurement window.
3. **Inputs**: weekly long / short / spreading positions by group, open interest, trader counts, concentration ratios,
   the EUR/USD close on report dates (divergence signals only) and rv_21d_bp for the vol scale. None is a label in
   disguise: correlation of the daily signals with fwd_1d is 0.015-0.046.
4. **Late reports**: reports dated inside US government shutdowns (2013-10, 2018-12..2019-02, 2025-10..12) were
   published weeks late, which the +6-day rule ignores (as does the live baseline). Delaying them to approximate
   catch-up dates changes nothing: baseline 0.699 / 0.602 / 0.313, final 0.672 / 0.541 / 0.409 (`positioning_deep_shutdown.csv`).

## Caveats
* The crude rule was selected in round 1 on 2003-2015, so 2010-2015 flatters it and every variant correlated with it;
  only 2016-2026 is evidence, and there the baseline's own t is 2.0. With 11 years, a variant would need roughly
  +0.3 to +0.4 Sharpe over a 0.9-correlated baseline to be distinguishable. This arm cannot rule out small improvements; it
  shows there is no large one.
* TFF variants have 15 live years (2012-2026) and their selection window is four years; the catch-up dates in the
  shutdown check are approximate; the CFTC files are current history, not as-published vintages.
* One declared candidate was a duplicate (flow_build13 = flow_cover13), so the theme "short covering vs new longs" was
  tested by the leg diagnostics and a post-hoc split rather than by a clean pre-declared pair.
