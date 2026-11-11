# Arm S: regime dependence (`regime_dependence`) - is the post-2023 fade noise, decay or regime?

Code `src/eurusd/arms/regime_dependence.py` (`run(cost_pips=1.2)`; `python -m eurusd.arms.regime_dependence` runs everything in about
3 minutes and rewrites this file). Results in `experiments/results/arms/`: `regime_dependence_positions.parquet` (daily stream `pos`,
`fwd_bp`, `net_bp`, `conditional`, `rule`: it is the UNCONDITIONAL agreement rule, flagged `conditional = False`, because no conditional
rule was adopted), `regime_dependence_report.csv` (protocol table of every stream, `variant`, `kind`, `final`),
`regime_dependence_tables.csv` (all tables, column `table`: power, power_joint, rolling3y, rolling5y, eras, step, regime, regime_sub,
screen, screen_placebo, mix, candidates, bar, mute_log, leak, pipeline_placebo, daily_gate, reconcile, regime_timeline),
`regime_dependence_incremental.csv`, `regime_dependence_strict_posthoc_positions.parquet` (the post hoc candidate, not for stacking).
The protocol, the components, the eight regime definitions, the screen, the candidate rule and the final-selection rule are in the
module docstring and were written before any result; what was added after the first run is listed there and marked below.
Reconciliation with arm N first: agreement rule at 21 sessions 59.4 % on 387 weekly decisions, 59.0 % on 156 non-overlapping ones,
weekly-tranche book Sharpe 0.52 / 0.51 / 0.43 - identical to `reports/arm_selective.md`.

## Verdict
**The fade is mostly noise, partly a return of positioning to its long-run level, and only weakly a regime. No conditional rule is adopted.**

1. **(a) Noise - yes for the P&L, for every signal.** With the 2010-22 record unchanged, a 2023-26 Sharpe as low as the observed one
   arrives 18 % of the time for positioning (0.77 -> 0.32), 40 % for the spread trend, 26 % for the house score, 27 % for December,
   48 % for equity momentum, 19 % for the agreement rule as a daily stream and 40 % for its weekly-tranche book (0.55 -> 0.43);
   jointly for the five component streams p = 0.19. None is distinguishable from noise. The sample could not have told us more:
   a signal with NO edge left would fall below the 5 % critical value only 17-50 % of the time. Rolling windows say the same: the
   agreement rule's 3-year Sharpe was -0.46, -0.14 and +0.08 in the windows ending 2015-2017 and then 0.9-1.0; the present trough is
   +0.25 to +0.49. The record has already contained a deeper fade and recovered from it.
2. **The hit rate is a different matter, and it is one signal, not all of them.** Weekly accuracy 2010-22 -> 2023-26: positioning
   61 -> 50 % at 21 sessions (p 0.02) and 65 -> 48 % at 42 (p 0.004); house score 61 -> 46 % at 42 (p 0.011); agreement rule
   61 -> 55 % at 21 (p 0.24, not a fade: the non-overlapping stream reads 59 -> 60 %) and 69 -> 47 % at 42 (p 0.010). The spread
   trend (49 -> 53 %, 51 -> 49 %) and equity momentum (53 -> 55 %, 54 -> 53 %) did not fade at all. Priced as a family on common
   pseudo-samples: pooled p 0.049, largest drop (positioning at 42 sessions) family-wise p 0.03; with positioning-free signals only
   (spread, equity momentum) p 0.47. Against a true 0.5-Sharpe process instead of the 2010-22 level the same numbers are p 0.13 / 0.04
   for positioning and 0.43 / 0.08 for the agreement rule. So: "every surviving signal fades" is wrong. Positioning's directional hit
   rate after 2023 is distinguishably below its 2010-22 level; the rest is inside the noise. Positioning still made money in 2023-26
   (Sharpe 0.32) because its wins were larger than its losses.
3. **(b) Decay of a mined effect - not the pattern for positioning or the agreement rule, yes for equity momentum.** A mined rule
   steps down at the edge of its selection window. Positioning: Sharpe 0.73 (2010-15, selection) -> 0.83 (2016-22), weekly accuracy
   61 -> 60 %; agreement rule 0.63 -> 0.68; house score 0.57 -> 0.88. No step (z between -0.5 and +0.2). Equity momentum does step:
   0.50 -> 0.28 (2016-22), weekly accuracy 59 -> 50 % over 2016-26 (p < 0.01). What the long history shows instead is that
   2010-22 was the exceptional stretch for positioning: Sharpe +0.15 in 2000-02 (before any selection window, H.10 prices), +0.29 to
   +0.38 in 2003-09, +0.73 to +0.83 in 2010-22, +0.32 to +0.36 in 2023-26. The agreement rule in 2006-09 (house weights walk-forward,
   outside round 2's window): Sharpe +0.19, weekly accuracy 47 % / 31 %. The post-2023 numbers look like the long-run level
   (arm G's planning Sharpe of 0.25-0.45 for positioning), not like a new decay. The spread trend never had directional accuracy at
   21-42 sessions in any era (46-53 % weekly); its Sharpe of 0.3 is payoff asymmetry. December: 6 of 7, 4 of 6, 6 of 7, 2 of 3.
4. **(c) Regime - one of eight pre-declared regimes shows in both halves; it is suggestive, not established, and it does not make a
   better call.** For the agreement rule only `div_change` passes the screen: when the gap between the ECB deposit rate and the fed
   funds target is WIDER than six months earlier the rule is right 68 % / 70 % at 21 / 42 sessions in 2006-15 and 60 % / 70 % in
   2016-26, against 54 / 44 % and 48 / 56 % outside (2006-26: 64 % [52-74], n=74 and 70 % [56-81], n=47 inside; 51 % and 49 % outside);
   its daily Sharpe is 1.52 / 1.02 inside and 0.02 / 0.02 outside. NARROWER is the mirror (54 / 42 % and 50 / 39 %, Sharpe -0.2).
   The P&L concentration is the same for positioning alone (Sharpe 1.34, t 3.9, on WIDER sessions; 0.12 elsewhere) and for the spread
   trend (0.95 against 0.10). Chance: 21 classes were looked at; rotating the regime labels against the calls, this class shows such
   a gap in 0.8 % of draws, but SOME class passes in 30 % of draws, two or more in 12 %, and the family-wise p of the largest gap is
   0.11 (accuracy) and 0.17 (Sharpe). The other seven: policy regime (lower bound / hiking / cutting) flips sign between the halves
   (hiking: -25 / -16 points, then +10 / +14); policy-gap level, rate volatility, dollar trend, US inflation and with- / counter-trend
   show nothing consistent; crowding: calls with |z| < 1 are worse at 21 sessions in both halves (-13, -17 points) but not in Sharpe,
   and the agreement rule does not weaken above |z| = 2 (63 % at both horizons). For the single components, positioning "works at
   the lower bound / small policy gap" passes the screen but is the fade restated: inside 2016-22 the large-gap sessions were as good
   (Sharpe 0.86 against 0.74) and 2023-26 is 100 % large-gap; the house score's inflation and trend classes and equity momentum's
   trend class all reverse in 2023-26.
   Does it explain the fade? In part, in money terms only. 2023-26 was a NARROWER period (58 % of sessions against 12 % in 2010-22;
   WIDER 27 % against 45 %). Holding each class at its 2010-22 record, the mix alone explains 35 % of positioning's drop in net bp per
   session and 44 % of the agreement rule's. Inside WIDER the P&L held up after 2023 (positioning Sharpe 1.06, agreement rule 1.38;
   outside -0.02 and -0.37), but the hit rate did not (agreement rule 50 % / 36 % on 22 weekly calls): the mix explains none of the
   accuracy drop (implied 60 % / 66 % for positioning, actual 50 % / 48 %).
5. **Tradeable test: fails the Round 5 bar; nothing adopted.** The declared walk-forward rule (`cond_div_change`: mute a class once
   its training-window accuracy is 5 points below the rest; it mutes NARROWER from 2013 on) against the unconditional rule,
   non-overlapping decisions:

   | | 21 sessions | 42 sessions |
   |---|---|---|
   | 2010-26 | 62 % (n=128, 7.4 a year) vs 59 % (n=156): **+2.7** [-1, +8] | 65 % (n=75) vs 61 % (n=89): **+4.7** [-3, +10] |
   | 2016-26 | 62 % (n=68, 6.1 a year) vs 57 % (n=96): **+4.5** [-2, +14] | 67 % (n=42) vs 59 % (n=56): **+7.7** [-4, +17] |
   | 2023-26 | 63 % (n=19) vs 60 % (n=35): +3.2 [-6, +29] | 50 % (n=12) vs 45 % (n=20): +5.0 [-10, +33] |

   It misses the 3-point bar at 21 sessions in 2010-26, every paired-bootstrap interval includes zero (p 0.08-0.19), the calls it
   refuses were still right 54 % / 57 % of the time, the weekly figures move by 1-2 points only, and its tranche-book Sharpe is
   unchanged (0.52 / 0.53 / 0.43 against 0.52 / 0.51 / 0.43). The full-pipeline placebo (rotate the labels, apply the same screen,
   run the same rule on whatever passes) gives +0.7 / +3.1 points on average and matches or beats the real gain in 19-27 % of
   passing draws: a quarter of the 21-session gain and two thirds of the 42-session gain is what choosing the regime variable on
   the whole sample buys.
   Two post hoc variants (written after seeing where the P&L sits, counted as trials, not eligible): the literal "speak only in
   the favourable class" rule is no better (59 % on 83 decisions, 4.8 a year; +0.1 / +4.0 points; book Sharpe 0.46 / 0.41 / 0.31);
   the same gate applied daily (hold the agreement position only on favourable sessions) has Sharpe 0.80 / 0.69 / 0.71 against
   0.56 / 0.52 / 0.20 and beats the pipeline placebo (2-4 % of passing draws do as well) - but the walk-forward chose the wrong class
   (SAME) in 2012-14, the whole 2010-26 gain is the year 2015 (0.75 against 0.72 without it) and most of the 2016-26 gain is 2023
   (0.65 against 0.61 without it). That is a lead for a paper forward test under its own name, not a rule.
6. **Leak checks.** Regime labels shuffled: gain -1.0 / +2.2 points (i.i.d.) and -0.1 / +1.6 (block rotation) against the real
   +2.7 / +4.7; the shuffles reach the real gain in 2-15 % and 7-13 % of draws, i.e. the gain does not cleanly vanish at 42 sessions
   because muting any persistent subset of a small sample moves a 75-decision accuracy by a few points. Labels lagged 21 sessions:
   +3.5 / +11.3 (no loss); lagged 63: -0.6 / +0.8; lagged 126: +1.0 / +2.0 - the class changes several times a year, so the
   information is gone within a quarter (it is a state of the policy cycle, not a slow level, and it is known at the close: both
   policy rates are public the day they change). Look-ahead controls: an oracle regime built from the future outcome gives 93 % /
   80 %, features taken 21 sessions ahead give 86 % - the harness exposes a leak; choosing the muted class with hindsight gives
   the same +2.8 / +4.6 as the walk-forward choice. Outcomes rotated against the calls: 49.7 %. Inputs of the regime labels are
   policy rates, the US 2y yield, the broad dollar index, US CPI, CFTC positioning and the 200-day average, all lagged; none
   contains a forward return.
7. **Round 3 incremental test.** The delivered stream is the unconditional agreement rule, so it repeats arm N: EW(weak_signals,
   regime_trend) 0.56 / 0.64 / 0.36 -> 0.57 / 0.64 / 0.40 with it; correlation 0.43 and 0.63. Nothing new for the stack.

**What to do with this.** (i) Keep the engine speaking unconditionally; do not gate it on any regime. (ii) Plan positioning-driven
calls at the long-run level (Sharpe 0.3-0.5, about 55 % at one month), not at the 2010-22 level (61-65 %). (iii) Show the
policy-gap direction (WIDER / SAME / NARROWER, known the day a policy rate changes) next to each call as context, and start a paper
forward test of "agreement rule on WIDER sessions only" as a new named scenario from zero. As of the last session (2026-11-05) the
class is NARROWER. (iv) The 2023-26 window cannot decide between "edge intact" and "edge gone" (power 17-50 %). An 80 %-power test
of 59 % against 50 % needs about 190 non-overlapping calls, two decades at nine a year; only more markets or more history shorten that.

**Counts for deflation.** Tradeable rules run: 1 declared (`cond_div_change`) + 3 post hoc (`strict_div_change`, and the daily-gated
form of both) = 4. Diagnostics, never selected from: 6 components x 21 regime classes x 3 periods, the screen, the power tables.
No threshold or window of any regime definition was changed after the first run.

**Caveats.** The regime variable was chosen on the whole sample (the walk-forward protects only the class choice); the pipeline
placebo is the correction. `div_change` uses a 182-day comparison fixed in advance; no other window was tried. The fed target file
ends 2026-09-20 and is held constant after it. CPI and CFTC data are current vintages. The broad dollar index starts in 2006, so the
dollar regime is defined from October 2006. The house score before 2010 is fitted on 3-6 years of data. Non-overlapping accuracy
of a 4-year window moves by up to 9 points with the phase of the stream (positioning 2023-26: 47 % or 55 %), which is why the weekly
statistic with a block bootstrap carries the power test. 2026 runs to 5 November.

## 1. Power: is 2023-26 distinguishable from the earlier record?
Null = the 2010-2022 record unchanged; circular block bootstrap of the 2010-22 sessions (block 126), pseudo-samples as long as 2023-26, same decision rule; 5,000 draws. `p unchanged` = share of draws at or below the observed 2023-26 value. `p true-0.5` = the same distribution re-centred on what a true 0.5-Sharpe process gives (55.7 % at 21 sessions, 58.1 % at 42, Sharpe 0.5): the answer to "is this within what a 0.5-Sharpe process produces" (added after the first run). `power` = probability that a process with NO edge would fall below the 5 % critical value of the unchanged null, i.e. how often this sample could even see a dead signal.

**Weekly decisions (overlap handled by the bootstrap; primary accuracy test)**

| component                | 21 sessions: 2010-22 -> 2023-26 (n)   |   p unchanged @21 |   p true-0.5 @21 | 42 sessions: 2010-22 -> 2023-26 (n)   |   p unchanged @42 |   p true-0.5 @42 |
|:-------------------------|:--------------------------------------|------------------:|-----------------:|:--------------------------------------|------------------:|-----------------:|
| positioning sign         | 61 -> 50 (195)                        |             0.02  |            0.134 | 65 -> 48 (191)                        |             0.004 |            0.042 |
| 2y-spread 20d trend      | 49 -> 53 (195)                        |             0.815 |            0.326 | 51 -> 49 (191)                        |             0.364 |            0.067 |
| house macro score        | 56 -> 52 (195)                        |             0.314 |            0.242 | 61 -> 46 (191)                        |             0.011 |            0.022 |
| relative equity momentum | 53 -> 55 (195)                        |             0.54  |            0.502 | 54 -> 53 (191)                        |             0.209 |            0.176 |
| AGREEMENT RULE           | 61 -> 55 (77)                         |             0.24  |            0.427 | 69 -> 47 (73)                         |             0.01  |            0.081 |

**Non-overlapping decisions** (stream started 2010 as in arm N; the 2023-26 figure of a single stream moves by up to 9 points with the phase of the stream: positioning reads 47 % here and 55 % on the stream started in 2003)

| component                | 21: 2010-22 -> 2023-26 (n)   |   p unchanged @21 |   p true-0.5 @21 |   power @21 | 42: 2010-22 -> 2023-26 (n)   |   p unchanged @42 |   p true-0.5 @42 |   power @42 |
|:-------------------------|:-----------------------------|------------------:|-----------------:|------------:|:-----------------------------|------------------:|-----------------:|------------:|
| positioning sign         | 61 -> 47 (47)                |             0.04  |            0.119 |        0.5  | 72 -> 57 (23)                |             0.281 |            0.46  |        0.5  |
| 2y-spread 20d trend      | 49 -> 55 (47)                |             0.856 |            0.443 |        0.07 | 53 -> 43 (23)                |             0.316 |            0.089 |        0.11 |
| house macro score        | 54 -> 57 (47)                |             0.681 |            0.581 |        0.19 | 63 -> 52 (23)                |             0.292 |            0.292 |        0.34 |
| relative equity momentum | 53 -> 66 (47)                |             0.94  |            0.899 |        0.19 | 56 -> 70 (23)                |             0.921 |            0.834 |        0.2  |
| AGREEMENT RULE           | 59 -> 60 (35)                |             0.637 |            0.676 |        0.16 | 65 -> 45 (20)                |             0.041 |            0.107 |        0.41 |
| December long            | 77 -> 67 (3)                 |             0.365 |            0.595 |        0.5  | 62 -> 33 (3)                 |             0.2   |            0.2   |        0.12 |

**Net Sharpe**

| stream (daily, net 1.2 pips)               |   Sharpe 2010-22 |   Sharpe 2023-26 |   p unchanged |   p true-0.5 |   5 % critical value |   power vs no edge |
|:-------------------------------------------|-----------------:|-----------------:|--------------:|-------------:|---------------------:|-------------------:|
| positioning sign                           |             0.77 |             0.32 |         0.18  |        0.365 |                -0.04 |               0.48 |
| 2y-spread 20d trend                        |             0.34 |             0.24 |         0.398 |        0.288 |                -0.49 |               0.17 |
| house macro score                          |             0.7  |             0.35 |         0.264 |        0.392 |                -0.17 |               0.4  |
| December long                              |             0.34 |             0.07 |         0.271 |        0.188 |                -0.49 |               0.17 |
| relative equity momentum                   |             0.4  |             0.34 |         0.476 |        0.384 |                -0.42 |               0.21 |
| AGREEMENT RULE                             |             0.65 |             0.2  |         0.191 |        0.266 |                -0.28 |               0.3  |
| agreement rule, weekly-tranche book        |             0.55 |             0.43 |         0.402 |        0.428 |                -0.17 |               0.36 |
| equal-weight of the five component streams |             0.92 |             0.49 |         0.219 |        0.481 |                -0.01 |               0.5  |

**Joint test on common pseudo-samples (added after the first run; picking the worst component afterwards is a selection, this prices it)**

| stat            | set                                          |   block |   observed 2023-26 (mean) |   null mean |   p pooled mean | largest drop   |   its z |   family-wise p of the largest drop |
|:----------------|:---------------------------------------------|--------:|--------------------------:|------------:|----------------:|:---------------|--------:|------------------------------------:|
| weekly accuracy | all four components x 21/42                  |     126 |                     0.509 |       0.565 |           0.049 | cot@42         |   2.637 |                               0.028 |
| weekly accuracy | positioning excluded (spread, house, eqrel)  |     126 |                     0.516 |       0.545 |           0.213 | house@42       |   2.264 |                               0.053 |
| weekly accuracy | spread and eqrel only (no positioning input) |     126 |                     0.528 |       0.531 |           0.467 | eqrel@42       |   0.835 |                               0.51  |
| daily Sharpe    | five component streams                       |     126 |                     0.264 |       0.512 |           0.187 | cot            |   0.908 |                               0.596 |
| weekly accuracy | all four components x 21/42                  |     252 |                     0.509 |       0.565 |           0.042 | cot@42         |   2.865 |                               0.013 |
| weekly accuracy | positioning excluded (spread, house, eqrel)  |     252 |                     0.516 |       0.545 |           0.206 | house@42       |   2.307 |                               0.052 |
| weekly accuracy | spread and eqrel only (no positioning input) |     252 |                     0.528 |       0.531 |           0.475 | eqrel@42       |   0.836 |                               0.499 |
| daily Sharpe    | five component streams                       |     252 |                     0.264 |       0.507 |           0.226 | cot            |   0.91  |                               0.559 |

**Other base windows** (2016-22 is not a selection window; 2010-15 -> 2016-26 is the selection-step test)

| component                | 2016-22 -> 2023-26 W21   | 2016-22 -> 2023-26 W42   | 2016-22 -> 2023-26 Sharpe   | 2010-15 -> 2016-26 W21   | 2010-15 -> 2016-26 W42   | 2010-15 -> 2016-26 Sharpe   |
|:-------------------------|:-------------------------|:-------------------------|:----------------------------|:-------------------------|:-------------------------|:----------------------------|
| positioning sign         | 60->50 p 0.04            | 66->48 p 0.01            | 0.83->0.32 p 0.17           | 61->57 p 0.03            | 65->59 p 0.08            | 0.73->0.66 p 0.39           |
| 2y-spread 20d trend      | 48->53 p 0.78            | 52->49 p 0.27            | 0.36->0.24 p 0.38           | 49->50 p 0.78            | 50->51 p 0.75            | 0.32->0.32 p 0.48           |
| house macro score        | 54->52 p 0.35            | 63->46 p 0.01            | 0.88->0.35 p 0.07           | 59->54 p 0.21            | 59->57 p 0.20            | 0.57->0.70 p 0.65           |
| relative equity momentum | 47->55 p 0.91            | 51->53 p 0.49            | 0.28->0.34 p 0.57           | 59->50 p 0.00            | 58->52 p 0.00            | 0.50->0.30 p 0.22           |
| AGREEMENT RULE           | 58->55 p 0.19            | 70->47 p 0.01            | 0.68->0.20 p 0.12           | 63->57 p 0.33            | 67->63 p 0.37            | 0.63->0.52 p 0.36           |

Block-length sensitivity (63 / 126 / 252 sessions): the largest change of any weekly-accuracy or Sharpe p-value is 0.049; all in `regime_dependence_tables.csv` (`table == power`).

## 2. Decay: eras and rolling windows around the selection windows
Round 1 chose its rules on 2003-2015 (validation 2016-22, holdout 2023-26); round 2 chose walk-forward variants on 2010-2015. `2000-02` precedes every selection window (Fed H.10 noon prices; positioning and December only). Components start when their data do: spread 2004-10, house score and agreement rule 2006, equity momentum 2007-04. Cells: net Sharpe (t) / weekly accuracy at 21 / at 42 sessions; December: Sharpe (t) / hits of the one yearly call.

| component                    | 2000-02               | 2003-09                | 2010-15               | 2016-22               | 2023-26               | 2003-15                | 2016-26               |
|:-----------------------------|:----------------------|:-----------------------|:----------------------|:----------------------|:----------------------|:-----------------------|:----------------------|
| positioning sign (H.10 noon) | +0.15 (0.3) / 49 / 53 | +0.38 (1.0) / 53 / 53  | +0.82 (2.0) / 61 / 64 | +0.83 (2.2) / 61 / 65 | +0.36 (0.7) / 48 / 49 | +0.57 (2.1) / 57 / 58  | +0.67 (2.2) / 57 / 59 |
| positioning sign             | -                     | +0.29 (0.8) / 56 / 52  | +0.73 (1.8) / 61 / 65 | +0.83 (2.2) / 60 / 66 | +0.32 (0.6) / 50 / 48 | +0.49 (1.8) / 58 / 58  | +0.66 (2.2) / 57 / 59 |
| 2y-spread 20d trend          | -                     | +0.67 (1.6) / 49 / 46  | +0.32 (0.8) / 49 / 50 | +0.36 (1.0) / 48 / 52 | +0.24 (0.5) / 53 / 49 | +0.49 (1.7) / 49 / 49  | +0.32 (1.1) / 50 / 51 |
| house macro score            | -                     | -0.02 (-0.1) / 45 / 41 | +0.57 (1.4) / 59 / 59 | +0.88 (2.4) / 54 / 63 | +0.35 (0.7) / 52 / 46 | +0.32 (1.0) / 53 / 52  | +0.70 (2.3) / 54 / 57 |
| relative equity momentum     | -                     | -                      | +0.50 (1.2) / 59 / 58 | +0.28 (0.8) / 47 / 51 | +0.34 (0.7) / 55 / 53 | +0.33 (1.0) / 57 / 56  | +0.30 (1.0) / 50 / 52 |
| AGREEMENT RULE               | -                     | +0.19 (0.4) / 47 / 31  | +0.63 (1.6) / 63 / 67 | +0.68 (1.8) / 58 / 70 | +0.20 (0.4) / 55 / 47 | +0.48 (1.5) / 60 / 60  | +0.52 (1.7) / 57 / 63 |
| December long (H.10 noon)    | +1.38 (2.4) / 3 of 3  | +0.44 (1.2) / 6 of 7   | +0.04 (0.1) / 4 of 6  | +0.71 (1.9) / 6 of 7  | +0.10 (0.2) / 2 of 3  | +0.28 (1.0) / 10 of 13 | +0.51 (1.7) / 8 of 10 |
| December long                | -                     | +0.50 (1.3) / 6 of 7   | +0.11 (0.3) / 4 of 6  | +0.64 (1.7) / 6 of 7  | +0.07 (0.1) / 2 of 3  | +0.34 (1.2) / 10 of 13 | +0.46 (1.5) / 8 of 10 |

**Steps** (z > 0 = lower afterwards; |z| < 1 everywhere, a 6-11 year Sharpe has a standard error of 0.3-0.4)

| component                | from    | to      | Sharpe         |   step z (Sharpe) | weekly acc 21   |
|:-------------------------|:--------|:--------|:---------------|------------------:|:----------------|
| positioning sign         | 2010-15 | 2016-22 | +0.73 -> +0.83 |             -0.15 | 61 -> 60        |
| positioning sign         | 2010-15 | 2016-26 | +0.73 -> +0.66 |              0.14 | 61 -> 57        |
| positioning sign         | 2016-22 | 2023-26 | +0.83 -> +0.32 |              0.76 | 60 -> 50        |
| positioning sign         | 2003-09 | 2010-15 | +0.29 -> +0.73 |             -0.74 | 56 -> 61        |
| 2y-spread 20d trend      | 2010-15 | 2016-22 | +0.32 -> +0.36 |             -0.07 | 49 -> 48        |
| 2y-spread 20d trend      | 2010-15 | 2016-26 | +0.32 -> +0.32 |              0    | 49 -> 50        |
| 2y-spread 20d trend      | 2016-22 | 2023-26 | +0.36 -> +0.24 |              0.19 | 48 -> 53        |
| 2y-spread 20d trend      | 2003-09 | 2010-15 | +0.67 -> +0.32 |              0.56 | 49 -> 49        |
| house macro score        | 2010-15 | 2016-22 | +0.57 -> +0.88 |             -0.5  | 59 -> 54        |
| house macro score        | 2010-15 | 2016-26 | +0.57 -> +0.70 |             -0.23 | 59 -> 54        |
| house macro score        | 2016-22 | 2023-26 | +0.88 -> +0.35 |              0.78 | 54 -> 52        |
| house macro score        | 2003-09 | 2010-15 | -0.02 -> +0.57 |             -0.9  | 45 -> 59        |
| relative equity momentum | 2010-15 | 2016-22 | +0.50 -> +0.28 |              0.38 | 59 -> 47        |
| relative equity momentum | 2010-15 | 2016-26 | +0.50 -> +0.30 |              0.38 | 59 -> 50        |
| relative equity momentum | 2016-22 | 2023-26 | +0.28 -> +0.34 |             -0.09 | 47 -> 55        |
| AGREEMENT RULE           | 2010-15 | 2016-22 | +0.63 -> +0.68 |             -0.08 | 63 -> 58        |
| AGREEMENT RULE           | 2010-15 | 2016-26 | +0.63 -> +0.52 |              0.2  | 63 -> 57        |
| AGREEMENT RULE           | 2016-22 | 2023-26 | +0.68 -> +0.20 |              0.74 | 58 -> 55        |
| AGREEMENT RULE           | 2003-09 | 2010-15 | +0.19 -> +0.63 |             -0.66 | 47 -> 63        |
| positioning sign (H.10)  | 2010-15 | 2016-22 | +0.82 -> +0.83 |             -0.02 | 61 -> 61        |
| positioning sign (H.10)  | 2010-15 | 2016-26 | +0.82 -> +0.67 |              0.25 | 61 -> 57        |
| positioning sign (H.10)  | 2016-22 | 2023-26 | +0.83 -> +0.36 |              0.68 | 61 -> 48        |
| positioning sign (H.10)  | 2003-09 | 2010-15 | +0.38 -> +0.82 |             -0.73 | 53 -> 61        |
| positioning sign (H.10)  | 2000-02 | 2003-15 | +0.15 -> +0.57 |             -0.64 | 49 -> 57        |

**Rolling 3-year net Sharpe (window ending in the year shown)**

|   window end |   2y-spread 20d trend |   AGREEMENT RULE |   December long |   December long H.10 |   house macro score |   positioning sign |   positioning sign H.10 |   relative equity momentum |
|-------------:|----------------------:|-----------------:|----------------:|---------------------:|--------------------:|-------------------:|------------------------:|---------------------------:|
|         2002 |                       |                  |                 |                 1.38 |                     |                    |                    0.15 |                            |
|         2003 |                       |                  |                 |                 1.42 |                     |                    |                    0.57 |                            |
|         2004 |                       |                  |                 |                 1.7  |                     |                    |                    0.42 |                            |
|         2005 |                       |                  |            1.01 |                 0.95 |                     |               0.07 |                    0.25 |                            |
|         2006 |                 -0    |                  |            0.3  |                 0.27 |                     |               0.39 |                    0.46 |                            |
|         2007 |                  0.63 |                  |           -0.03 |                -0.1  |                     |               0.29 |                    0.22 |                            |
|         2008 |                  1.34 |             0.25 |            0.71 |                 0.61 |               -0.28 |               0.15 |                    0.17 |                            |
|         2009 |                  1.05 |             0.12 |            0.35 |                 0.29 |               -0.04 |               0.38 |                    0.38 |                       0.02 |
|         2010 |                  1.16 |             0.73 |            0.59 |                 0.46 |                0.83 |               0.85 |                    0.87 |                       0.38 |
|         2011 |                  0.68 |             1.15 |           -0.65 |                -0.79 |                1.39 |               1.18 |                    1.21 |                       0.91 |
|         2012 |                  0.83 |             1.36 |            0.1  |                -0.08 |                1.57 |               1.09 |                    1.19 |                       1.09 |
|         2013 |                  0.17 |             0.71 |           -0.16 |                -0.18 |                0.69 |               0.63 |                    0.72 |                       0.67 |
|         2014 |                 -0.06 |             0.43 |           -0.02 |                -0.03 |                0.12 |               0.75 |                    0.85 |                       0.67 |
|         2015 |                 -0.3  |            -0.46 |            0.12 |                 0.14 |               -0.65 |               0.3  |                    0.39 |                      -0.21 |
|         2016 |                 -0.09 |            -0.14 |           -0.09 |                -0.03 |               -0.25 |               0.71 |                    0.72 |                       0.2  |
|         2017 |                 -0.04 |             0.08 |            0.33 |                 0.35 |                0.17 |               0.69 |                    0.72 |                      -0.23 |
|         2018 |                  0.52 |             0.88 |            0.24 |                 0.27 |                1.01 |               0.9  |                    0.89 |                       0.21 |
|         2019 |                  0.81 |             0.97 |            0.87 |                 1.01 |                1    |               0.72 |                    0.75 |                      -0.35 |
|         2020 |                  0.5  |             0.33 |            1.07 |                 1.31 |                0.74 |               0.29 |                    0.34 |                       0.03 |
|         2021 |                  0.31 |             0.3  |            0.86 |                 1.06 |                0.51 |               0.42 |                    0.5  |                      -0.41 |
|         2022 |                  0.21 |             0.67 |            0.95 |                 1.2  |                0.93 |               0.95 |                    0.98 |                       0.49 |
|         2023 |                  0.02 |             0.47 |            0.76 |                 0.85 |                0.72 |               0.76 |                    0.75 |                       0.37 |
|         2024 |                 -0.06 |             0.49 |            0.32 |                 0.47 |                0.79 |               0.87 |                    0.88 |                       0.74 |
|         2025 |                  0.23 |             0.25 |            0.08 |                 0.11 |                0.4  |               0.3  |                    0.38 |                       0    |
|         2026 |                  0.54 |             0.39 |           -0.23 |                -0.2  |                0.33 |               0.39 |                    0.41 |                       0.45 |

**Rolling 5-year net Sharpe**

|   window end |   2y-spread 20d trend |   AGREEMENT RULE |   December long |   December long H.10 |   house macro score |   positioning sign |   positioning sign H.10 |   relative equity momentum |
|-------------:|----------------------:|-----------------:|----------------:|---------------------:|--------------------:|-------------------:|------------------------:|---------------------------:|
|         2004 |                       |                  |                 |                 1.37 |                     |                    |                    0.13 |                            |
|         2005 |                       |                  |                 |                 0.97 |                     |                    |                    0.46 |                            |
|         2006 |                       |                  |                 |                 1.05 |                     |                    |                    0.53 |                            |
|         2007 |                       |                  |            0.56 |                 0.53 |                     |               0.02 |                    0.16 |                            |
|         2008 |                  0.91 |                  |            0.63 |                 0.55 |                     |               0.19 |                    0.23 |                            |
|         2009 |                  0.87 |                  |            0.26 |                 0.21 |                     |               0.52 |                    0.48 |                            |
|         2010 |                  0.98 |             0.62 |            0.38 |                 0.28 |                0.44 |               0.59 |                    0.61 |                            |
|         2011 |                  1.07 |             0.85 |            0.2  |                 0.11 |                0.72 |               0.7  |                    0.73 |                       0.5  |
|         2012 |                  0.96 |             0.9  |            0.31 |                 0.21 |                0.98 |               0.93 |                    0.97 |                       0.58 |
|         2013 |                  0.34 |             0.82 |           -0.23 |                -0.33 |                0.98 |               0.86 |                    0.91 |                       0.76 |
|         2014 |                  0.52 |             1.05 |           -0.08 |                -0.18 |                0.97 |               0.94 |                    1.05 |                       0.89 |
|         2015 |                  0.1  |             0.33 |           -0.09 |                -0.08 |                0.19 |               0.65 |                    0.73 |                       0.3  |
|         2016 |                 -0.21 |            -0.08 |            0.15 |                 0.16 |               -0.13 |               0.51 |                    0.57 |                       0.29 |
|         2017 |                 -0.08 |             0.13 |            0.09 |                 0.14 |               -0.01 |               0.67 |                    0.73 |                       0.01 |
|         2018 |                  0.27 |             0.36 |            0.1  |                 0.13 |                0.29 |               0.8  |                    0.82 |                      -0    |
|         2019 |                  0.2  |             0.13 |            0.48 |                 0.49 |                0.27 |               0.48 |                    0.48 |                      -0.22 |
|         2020 |                  0.4  |             0.63 |            0.56 |                 0.59 |                0.88 |               0.73 |                    0.77 |                       0.18 |
|         2021 |                  0.6  |             0.73 |            0.79 |                 0.96 |                0.87 |               0.67 |                    0.73 |                      -0.39 |
|         2022 |                  0.39 |             0.54 |            0.97 |                 1.19 |                0.79 |               0.63 |                    0.63 |                       0.24 |
|         2023 |                  0.08 |             0.37 |            0.91 |                 1.03 |                0.69 |               0.64 |                    0.68 |                       0.29 |
|         2024 |                  0.06 |             0.48 |            0.45 |                 0.59 |                0.74 |               0.77 |                    0.81 |                       0.32 |
|         2025 |                  0.25 |             0.49 |            0.39 |                 0.48 |                0.6  |               0.62 |                    0.64 |                       0.22 |
|         2026 |                  0.21 |             0.42 |            0.39 |                 0.48 |                0.6  |               0.63 |                    0.63 |                       0.72 |

**Rolling 5-year weekly accuracy at 21 sessions (%)**

|   window end |   2y-spread 20d trend |   AGREEMENT RULE |   house macro score |   positioning sign |   positioning sign H.10 |   relative equity momentum |
|-------------:|----------------------:|-----------------:|--------------------:|-------------------:|------------------------:|---------------------------:|
|         2004 |                       |                  |                     |                    |                      52 |                            |
|         2005 |                       |                  |                     |                    |                      52 |                            |
|         2006 |                       |                  |                     |                    |                      55 |                            |
|         2007 |                       |                  |                     |                 53 |                      51 |                            |
|         2008 |                    51 |                  |                     |                 53 |                      51 |                            |
|         2009 |                    51 |                  |                     |                 54 |                      52 |                            |
|         2010 |                    51 |               54 |                  49 |                 56 |                      54 |                            |
|         2011 |                    52 |               58 |                  52 |                 59 |                      58 |                         51 |
|         2012 |                    50 |               61 |                  59 |                 62 |                      61 |                         54 |
|         2013 |                    44 |               60 |                  59 |                 63 |                      62 |                         58 |
|         2014 |                    48 |               63 |                  59 |                 63 |                      63 |                         59 |
|         2015 |                    49 |               64 |                  58 |                 61 |                      62 |                         59 |
|         2016 |                    49 |               62 |                  55 |                 61 |                      59 |                         59 |
|         2017 |                    49 |               64 |                  53 |                 63 |                      61 |                         53 |
|         2018 |                    56 |               65 |                  56 |                 61 |                      61 |                         48 |
|         2019 |                    51 |               61 |                  53 |                 58 |                      58 |                         43 |
|         2020 |                    48 |               58 |                  52 |                 60 |                      62 |                         43 |
|         2021 |                    45 |               54 |                  53 |                 57 |                      61 |                         44 |
|         2022 |                    48 |               57 |                  56 |                 58 |                      61 |                         49 |
|         2023 |                    45 |               53 |                  55 |                 56 |                      57 |                         54 |
|         2024 |                    47 |               53 |                  56 |                 54 |                      56 |                         57 |
|         2025 |                    50 |               55 |                  56 |                 53 |                      51 |                         55 |
|         2026 |                    54 |               60 |                  56 |                 55 |                      52 |                         57 |

**Rolling 5-year weekly accuracy at 42 sessions (%)**

|   window end |   2y-spread 20d trend |   AGREEMENT RULE |   house macro score |   positioning sign |   positioning sign H.10 |   relative equity momentum |
|-------------:|----------------------:|-----------------:|--------------------:|-------------------:|------------------------:|---------------------------:|
|         2004 |                       |                  |                     |                    |                      49 |                            |
|         2005 |                       |                  |                     |                    |                      50 |                            |
|         2006 |                       |                  |                     |                    |                      54 |                            |
|         2007 |                       |                  |                     |                 50 |                      52 |                            |
|         2008 |                    50 |                  |                     |                 54 |                      56 |                            |
|         2009 |                    47 |                  |                     |                 55 |                      57 |                            |
|         2010 |                    46 |               45 |                  45 |                 57 |                      59 |                            |
|         2011 |                    48 |               54 |                  48 |                 60 |                      60 |                         53 |
|         2012 |                    46 |               60 |                  60 |                 63 |                      62 |                         58 |
|         2013 |                    45 |               61 |                  59 |                 64 |                      63 |                         58 |
|         2014 |                    52 |               69 |                  59 |                 67 |                      66 |                         58 |
|         2015 |                    51 |               69 |                  58 |                 64 |                      64 |                         59 |
|         2016 |                    53 |               66 |                  58 |                 61 |                      61 |                         56 |
|         2017 |                    51 |               67 |                  54 |                 63 |                      64 |                         51 |
|         2018 |                    56 |               71 |                  61 |                 63 |                      64 |                         50 |
|         2019 |                    51 |               66 |                  57 |                 60 |                      60 |                         49 |
|         2020 |                    50 |               68 |                  57 |                 64 |                      63 |                         48 |
|         2021 |                    47 |               68 |                  61 |                 67 |                      65 |                         51 |
|         2022 |                    52 |               72 |                  65 |                 66 |                      64 |                         53 |
|         2023 |                    47 |               63 |                  61 |                 62 |                      60 |                         56 |
|         2024 |                    51 |               63 |                  62 |                 59 |                      58 |                         56 |
|         2025 |                    51 |               61 |                  59 |                 57 |                      57 |                         56 |
|         2026 |                    53 |               59 |                  53 |                 53 |                      55 |                         55 |

## 3. Pre-declared economic regimes
Definitions are in the module docstring (written before the results). Regime labels use only data stamped at least one calendar day before the session close (broad dollar 7 days, CPI 60 days after the month stamp). Share of sessions by year for every regime: `table == regime_timeline` in the tables file.

**Screen for the agreement rule** (gap = non-overlapping accuracy inside the class minus outside it; a class passes only if all four gaps are >= 5 points with one sign and the Sharpe gaps agree; rotation p = share of 1,000 joint rotations of the regime labels in which THIS class shows a consistent gap at least as large; it is not adjusted for the 21 classes looked at)

| regime     | class    | gap 21 / 42, 2006-15 (pts)   | gap 21 / 42, 2016-26 (pts)   | Sharpe in - out, 2006-15 / 2016-26   | >= 10 decisions each side   | screen       | rotation p (accuracy gap)   | rotation p (Sharpe gap)   |
|:-----------|:---------|:-----------------------------|:-----------------------------|:-------------------------------------|:----------------------------|:-------------|:----------------------------|:--------------------------|
| policy     | CUT      | -9 / +13                     | +1 / -8                      | +0.00 / -0.74                        | NO                          | -            | -                           | -                         |
| policy     | OTHER    | +8 / +13                     | -25 / -37                    | -0.19 / -0.86                        | NO                          | -            | -                           | -                         |
| policy     | HIKE     | -25 / -16                    | +10 / +14                    | +0.36 / +0.54                        | yes                         | -            | 0.906                       | 0.211                     |
| policy     | LB       | +14 / +6                     | -8 / +1                      | -0.17 / +0.07                        | yes                         | -            | 0.636                       | 0.507                     |
| div_level  | BELOW    | +20 / +27                    | -16 / +10                    | +0.24 / +0.17                        | yes                         | -            | 0.942                       | 0.288                     |
| div_level  | ABOVE    | -20 / -27                    | +16 / -10                    | -0.24 / -0.17                        | yes                         | -            | 0.942                       | 0.288                     |
| div_change | SAME     | -6 / -12                     | -1 / +13                     | -0.55 / -0.26                        | yes                         | -            | 0.848                       | 0.309                     |
| div_change | NARROWER | -10 / -18                    | -12 / -28                    | -0.92 / -1.02                        | yes                         | UNFAVOURABLE | 0.015                       | 0.027                     |
| div_change | WIDER    | +14 / +26                    | +12 / +14                    | +1.50 / +1.00                        | yes                         | FAVOURABLE   | 0.008                       | 0.010                     |
| ratevol    | MID      | +9 / +7                      | +4 / +15                     | -0.32 / -0.32                        | yes                         | -            | 0.075                       | 0.265                     |
| ratevol    | HIGH     | +7 / +8                      | +3 / -14                     | -0.24 / +0.13                        | yes                         | -            | 0.333                       | 0.330                     |
| ratevol    | LOW      | -7 / -6                      | -10 / +8                     | +0.32 / +0.10                        | yes                         | -            | 0.693                       | 0.396                     |
| dollar     | BELOW    | +0 / -2                      | +3 / +3                      | -0.08 / +0.55                        | yes                         | -            | 0.307                       | 0.662                     |
| dollar     | ABOVE    | -0 / +2                      | -3 / -3                      | +0.08 / -0.55                        | yes                         | -            | 0.307                       | 0.662                     |
| inflation  | LOW      | +6 / -2                      | -8 / +1                      | +0.07 / -0.08                        | yes                         | -            | 0.390                       | 0.462                     |
| inflation  | HIGH     | -6 / +2                      | +8 / -1                      | -0.07 / +0.08                        | yes                         | -            | 0.390                       | 0.462                     |
| crowding   | 1-2      | +4 / +13                     | +15 / +9                     | -0.16 / +0.75                        | yes                         | -            | 0.053                       | 0.682                     |
| crowding   | <1       | -13 / -8                     | -17 / -5                     | +0.18 / -0.77                        | yes                         | -            | 0.032                       | 0.708                     |
| crowding   | >2       | +23 / +5                     | -6 / +0                      | -0.04 / -0.11                        | yes                         | -            | 0.566                       | 0.485                     |
| trend_rel  | WITH     | -2 / +5                      | +12 / -17                    | -0.44 / +0.53                        | yes                         | -            | 0.913                       | 0.827                     |
| trend_rel  | COUNTER  | +2 / -5                      | -12 / +17                    | +0.44 / -0.53                        | yes                         | -            | 0.913                       | 0.827                     |

**Chance control: all regime labels rotated jointly against the calls by at least a year** (binary variables count as two mirrored classes, in the data and in the placebo alike)

| component                |   classes passing |   placebo: mean passing |   placebo: share of draws with any pass |   p(as many pass) |   largest consistent accuracy gap |   placebo 95th pct |   family-wise p (accuracy) |   largest consistent Sharpe gap |   placebo 95th pct (Sharpe) |   family-wise p (Sharpe) |
|:-------------------------|------------------:|------------------------:|----------------------------------------:|------------------:|----------------------------------:|-------------------:|---------------------------:|--------------------------------:|----------------------------:|-------------------------:|
| AGREEMENT RULE           |                 2 |                   0.458 |                                   0.296 |             0.117 |                             0.122 |              0.143 |                      0.108 |                           0.996 |                       1.211 |                    0.167 |
| positioning sign         |                 4 |                   0.64  |                                   0.365 |             0.012 |                             0.095 |              0.116 |                      0.138 |                           0.723 |                       1.066 |                    0.315 |
| 2y-spread 20d trend      |                 0 |                   0.51  |                                   0.315 |             1     |                             0.021 |              0.109 |                      0.768 |                           0.787 |                       1.18  |                    0.35  |
| house macro score        |                 4 |                   0.53  |                                   0.292 |             0.015 |                             0.088 |              0.11  |                      0.145 |                           0.307 |                       1.233 |                    0.955 |
| relative equity momentum |                 2 |                   0.507 |                                   0.312 |             0.15  |                             0.08  |              0.126 |                      0.23  |                           0.969 |                       1.181 |                    0.142 |

**Classes that pass the same screen for the single components** (information only; nothing is traded on them)

| component                | regime     | class    | screen       | gap 21 / 42, 2006-15   | gap 21 / 42, 2016-26   | Sharpe gap 2006-15 / 2016-26   |
|:-------------------------|:-----------|:---------|:-------------|:-----------------------|:-----------------------|:-------------------------------|
| positioning sign         | policy     | LB       | FAVOURABLE   | +9 / +14               | +7 / +6                | +0.32 / +0.12                  |
| positioning sign         | div_level  | BELOW    | FAVOURABLE   | +15 / +20              | +10 / +20              | +0.28 / +0.10                  |
| positioning sign         | div_level  | ABOVE    | UNFAVOURABLE | -15 / -20              | -10 / -20              | -0.28 / -0.10                  |
| positioning sign         | div_change | NARROWER | UNFAVOURABLE | -11 / -9               | -9 / -5                | -0.85 / -0.55                  |
| house macro score        | inflation  | LOW      | UNFAVOURABLE | -16 / -9               | -13 / -11              | -0.13 / -0.49                  |
| house macro score        | inflation  | HIGH     | FAVOURABLE   | +16 / +9               | +13 / +11              | +0.13 / +0.49                  |
| house macro score        | trend_rel  | WITH     | FAVOURABLE   | +15 / +14              | +5 / +6                | +1.04 / +0.31                  |
| house macro score        | trend_rel  | COUNTER  | UNFAVOURABLE | -15 / -14              | -5 / -6                | -1.04 / -0.31                  |
| relative equity momentum | trend_rel  | WITH     | FAVOURABLE   | +12 / +8               | +9 / +8                | +1.07 / +0.45                  |
| relative equity momentum | trend_rel  | COUNTER  | UNFAVOURABLE | -12 / -8               | -9 / -8                | -1.07 / -0.45                  |

**Is a regime effect the fade restated? Second half split at 2023** (added after the first run)

| component                | regime     | class    | period   |   sessions | Sharpe in / out   | weekly acc 21 in / out (n in)   | weekly acc 42 in / out   |
|:-------------------------|:-----------|:---------|:---------|-----------:|:------------------|:--------------------------------|:-------------------------|
| AGREEMENT RULE           | div_change | SAME     | 2016-22  |        485 | +0.60 / +0.71     | 55 / 60 (53)                    | 62 / 74                  |
| AGREEMENT RULE           | div_change | SAME     | 2023-26  |        150 | -0.47 / +0.34     | 56 / 54 (16)                    | 62 / 42                  |
| AGREEMENT RULE           | div_change | NARROWER | 2016-22  |        291 | -0.05 / +0.83     | 50 / 60 (30)                    | 70 / 71                  |
| AGREEMENT RULE           | div_change | NARROWER | 2023-26  |        579 | -0.33 / +0.74     | 56 / 53 (39)                    | 46 / 47                  |
| AGREEMENT RULE           | div_change | WIDER    | 2016-22  |       1041 | +0.92 / +0.33     | 64 / 53 (83)                    | 76 / 65                  |
| AGREEMENT RULE           | div_change | WIDER    | 2023-26  |        271 | +1.38 / -0.37     | 50 / 56 (22)                    | 36 / 51                  |
| positioning sign         | div_change | SAME     | 2016-22  |        485 | +0.77 / +0.85     | 57 / 61 (97)                    | 63 / 67                  |
| positioning sign         | div_change | SAME     | 2023-26  |        150 | -0.97 / +0.55     | 53 / 49 (32)                    | 41 / 49                  |
| positioning sign         | div_change | NARROWER | 2016-22  |        291 | +0.25 / +0.93     | 59 / 60 (58)                    | 64 / 66                  |
| positioning sign         | div_change | NARROWER | 2023-26  |        579 | +0.26 / +0.39     | 50 / 49 (111)                   | 47 / 49                  |
| positioning sign         | div_change | WIDER    | 2016-22  |       1041 | +1.00 / +0.56     | 62 / 57 (209)                   | 67 / 63                  |
| positioning sign         | div_change | WIDER    | 2023-26  |        271 | +1.06 / -0.02     | 46 / 51 (52)                    | 54 / 45                  |
| positioning sign         | div_level  | BELOW    | 2016-22  |        520 | +0.74 / +0.86     | 56 / 62 (104)                   | 68 / 65                  |
| positioning sign         | div_level  | BELOW    | 2023-26  |          0 | - / +0.32         | - / 50 (0)                      | - / 48                   |
| positioning sign         | div_level  | ABOVE    | 2016-22  |       1297 | +0.86 / +0.74     | 62 / 56 (260)                   | 65 / 68                  |
| positioning sign         | div_level  | ABOVE    | 2023-26  |       1000 | +0.32 / -         | 50 / - (195)                    | 48 / -                   |
| positioning sign         | policy     | CUT      | 2016-22  |        161 | -1.43 / +1.00     | 53 / 61 (32)                    | 53 / 67                  |
| positioning sign         | policy     | CUT      | 2023-26  |        491 | +0.26 / +0.39     | 54 / 45 (98)                    | 56 / 39                  |
| positioning sign         | policy     | OTHER    | 2016-22  |         66 | +1.74 / +0.79     | 69 / 60 (13)                    | 85 / 65                  |
| positioning sign         | policy     | OTHER    | 2023-26  |         98 | -0.60 / +0.38     | 37 / 51 (19)                    | 33 / 49                  |
| positioning sign         | policy     | HIKE     | 2016-22  |        787 | +1.19 / +0.53     | 63 / 58 (158)                   | 70 / 63                  |
| positioning sign         | policy     | HIKE     | 2023-26  |        411 | +0.54 / +0.17     | 47 / 51 (78)                    | 40 / 53                  |
| positioning sign         | policy     | LB       | 2016-22  |        803 | +0.74 / +0.89     | 58 / 62 (161)                   | 63 / 68                  |
| positioning sign         | policy     | LB       | 2023-26  |          0 | - / +0.32         | - / 50 (0)                      | - / 48                   |
| house macro score        | inflation  | LOW      | 2016-22  |       1403 | +0.68 / +1.45     | 49 / 71 (281)                   | 57 / 84                  |
| house macro score        | inflation  | LOW      | 2023-26  |        390 | +0.02 / +0.62     | 54 / 51 (78)                    | 49 / 44                  |
| house macro score        | inflation  | HIGH     | 2016-22  |        414 | +1.45 / +0.68     | 71 / 49 (83)                    | 84 / 57                  |
| house macro score        | inflation  | HIGH     | 2023-26  |        610 | +0.62 / +0.02     | 51 / 54 (117)                   | 44 / 49                  |
| house macro score        | trend_rel  | WITH     | 2016-22  |        980 | +1.24 / +0.48     | 58 / 49 (200)                   | 66 / 60                  |
| house macro score        | trend_rel  | WITH     | 2023-26  |        561 | +0.09 / +0.65     | 50 / 55 (111)                   | 40 / 54                  |
| house macro score        | trend_rel  | COUNTER  | 2016-22  |        837 | +0.48 / +1.24     | 49 / 58 (164)                   | 60 / 66                  |
| house macro score        | trend_rel  | COUNTER  | 2023-26  |        439 | +0.65 / +0.09     | 55 / 50 (84)                    | 54 / 40                  |
| relative equity momentum | trend_rel  | WITH     | 2016-22  |        899 | +0.75 / -0.13     | 52 / 42 (181)                   | 55 / 46                  |
| relative equity momentum | trend_rel  | WITH     | 2023-26  |        412 | +0.11 / +0.51     | 54 / 56 (81)                    | 45 / 59                  |
| relative equity momentum | trend_rel  | COUNTER  | 2016-22  |        918 | -0.13 / +0.75     | 42 / 52 (183)                   | 46 / 55                  |
| relative equity momentum | trend_rel  | COUNTER  | 2023-26  |        588 | +0.51 / +0.11     | 56 / 54 (114)                   | 59 / 45                  |

**Policy-gap direction (`div_change`): 2023-26 next to 2010-22** (added after the first run)

| component                | class    | share of sessions 2010-22 / 2023-26 (%)   | net bp per session 2010-22 / 2023-26   | Sharpe 2010-22 / 2023-26   | weekly acc 21, 2010-22 / 2023-26 (n)   | weekly acc 42, 2010-22 / 2023-26   |
|:-------------------------|:---------|:------------------------------------------|:---------------------------------------|:---------------------------|:---------------------------------------|:-----------------------------------|
| positioning sign         | SAME     | 42 / 15                                   | +1.50 / -2.70                          | +0.43 / -0.97              | 57 / 53 (32)                           | 60 / 41                            |
| positioning sign         | NARROWER | 12 / 58                                   | +1.19 / +0.65                          | +0.41 / +0.26              | 58 / 50 (111)                          | 65 / 47                            |
| positioning sign         | WIDER    | 45 / 27                                   | +4.06 / +3.29                          | +1.18 / +1.06              | 65 / 46 (52)                           | 70 / 54                            |
| 2y-spread 20d trend      | SAME     | 42 / 15                                   | +0.90 / +0.86                          | +0.26 / +0.31              | 47 / 41 (32)                           | 48 / 59                            |
| 2y-spread 20d trend      | NARROWER | 12 / 58                                   | +0.35 / -1.05                          | +0.12 / -0.42              | 42 / 53 (111)                          | 54 / 50                            |
| 2y-spread 20d trend      | WIDER    | 45 / 27                                   | +1.59 / +4.17                          | +0.46 / +1.35              | 52 / 62 (52)                           | 54 / 42                            |
| house macro score        | SAME     | 42 / 15                                   | +1.50 / +3.77                          | +0.43 / +1.36              | 56 / 66 (32)                           | 58 / 53                            |
| house macro score        | NARROWER | 12 / 58                                   | +3.22 / +0.63                          | +1.11 / +0.26              | 56 / 57 (111)                          | 68 / 53                            |
| house macro score        | WIDER    | 45 / 27                                   | +3.01 / +0.01                          | +0.88 / +0.00              | 57 / 35 (52)                           | 62 / 27                            |
| relative equity momentum | SAME     | 42 / 15                                   | -0.10 / +4.89                          | -0.03 / +1.77              | 55 / 72 (32)                           | 53 / 66                            |
| relative equity momentum | NARROWER | 12 / 58                                   | +2.66 / +1.37                          | +0.91 / +0.56              | 51 / 60 (111)                          | 65 / 55                            |
| relative equity momentum | WIDER    | 45 / 27                                   | +2.34 / -2.25                          | +0.68 / -0.72              | 51 / 35 (52)                           | 52 / 42                            |
| AGREEMENT RULE           | SAME     | 42 / 15                                   | +0.86 / -0.92                          | +0.36 / -0.47              | 57 / 56 (16)                           | 61 / 62                            |
| AGREEMENT RULE           | NARROWER | 12 / 58                                   | +0.37 / -0.49                          | +0.16 / -0.33              | 51 / 56 (39)                           | 69 / 46                            |
| AGREEMENT RULE           | WIDER    | 45 / 27                                   | +2.40 / +2.80                          | +1.07 / +1.38              | 68 / 50 (22)                           | 77 / 36                            |

**How much of the fade does the 2023-26 regime mix explain?** (each class keeps its 2010-22 record, only the mix changes)

| component                |   net bp/session 2010-22 |   implied for 2023-26 by its regime mix |   actual 2023-26 |   share of the P&L drop explained by the mix (%) | weekly acc 21: 2010-22 / implied / actual   | weekly acc 42: 2010-22 / implied / actual   |
|:-------------------------|-------------------------:|----------------------------------------:|-----------------:|-------------------------------------------------:|:--------------------------------------------|:--------------------------------------------|
| positioning sign         |                     2.62 |                                    2.01 |             0.86 |                                               35 | 61 / 60 / 50                                | 65 / 66 / 48                                |
| 2y-spread 20d trend      |                     1.15 |                                    0.77 |             0.65 |                                               76 | 49 / 45 / 53                                | 51 / 53 / 49                                |
| house macro score        |                     2.4  |                                    2.91 |             0.94 |                                              -35 | 56 / 56 / 52                                | 61 / 65 / 46                                |
| relative equity momentum |                     1.35 |                                    2.16 |             0.92 |                                             -188 | 53 / 52 / 55                                | 54 / 60 / 53                                |
| AGREEMENT RULE           |                     1.5  |                                    0.99 |             0.34 |                                               44 | 61 / 57 / 55                                | 69 / 70 / 47                                |

### Full regime tables
Cells: non-overlapping accuracy at 21 sessions [Wilson 95 %] n · the same at 42 sessions · net Sharpe of the daily stream on the class's sessions (for the agreement rule and December zero-position days are included). Stream of "component speaks AND class holds", started 2006. Weekly accuracy, the outside-class figures and net bp per decision are in the tables file (`table == regime`).

**positioning sign**

| regime     | class    |   share of sessions 2006-26 (%) | 2006-26                                        | 2006-15                                       | 2016-26                                       |
|:-----------|:---------|--------------------------------:|:-----------------------------------------------|:----------------------------------------------|:----------------------------------------------|
| policy     | CUT      |                              14 | 44 [29-59] n=39 · 60 [39-78] n=20 · SR +0.07   | 43 [16-75] n=7 · 75 [30-95] n=4 · SR +0.43    | 44 [28-61] n=32 · 56 [33-77] n=16 · SR -0.09  |
| policy     | OTHER    |                               8 | 50 [31-69] n=24 · 50 [25-75] n=12 · SR +0.72   | 57 [33-79] n=14 · 57 [25-84] n=7 · SR +0.77   | 40 [17-69] n=10 · 40 [12-77] n=5 · SR +0.67   |
| policy     | HIKE     |                              32 | 57 [46-67] n=84 · 52 [38-67] n=42 · SR +0.73   | 52 [34-69] n=27 · 43 [21-67] n=14 · SR +0.23  | 60 [47-71] n=57 · 57 [39-73] n=28 · SR +0.98  |
| policy     | LB       |                              46 | 61 [52-70] n=119 · 64 [51-75] n=61 · SR +0.73  | 60 [50-70] n=81 · 66 [51-78] n=41 · SR +0.73  | 63 [47-77] n=38 · 60 [39-78] n=20 · SR +0.74  |
| div_level  | BELOW    |                              48 | 60 [51-68] n=126 · 62 [50-73] n=64 · SR +0.66  | 59 [50-68] n=101 · 59 [45-71] n=51 · SR +0.66 | 60 [41-77] n=25 · 77 [50-92] n=13 · SR +0.74  |
| div_level  | ABOVE    |                              52 | 49 [41-58] n=134 · 54 [42-65] n=67 · SR +0.59  | 44 [27-63] n=25 · 38 [18-64] n=13 · SR +0.38  | 50 [41-60] n=109 · 57 [44-70] n=54 · SR +0.64 |
| div_change | SAME     |                              31 | 59 [48-68] n=92 · 63 [49-75] n=51 · SR +0.13   | 57 [44-70] n=54 · 63 [46-78] n=30 · SR +0.06  | 61 [45-74] n=38 · 62 [41-79] n=21 · SR +0.33  |
| div_change | NARROWER |                              30 | 54 [43-64] n=80 · 61 [46-74] n=41 · SR +0.11   | 58 [42-72] n=38 · 60 [39-78] n=20 · SR -0.01  | 50 [36-64] n=42 · 62 [41-79] n=21 · SR +0.26  |
| div_change | WIDER    |                              39 | 58 [49-67] n=110 · 54 [42-67] n=57 · SR +1.34  | 71 [56-83] n=42 · 61 [41-78] n=23 · SR +1.78  | 50 [38-62] n=68 · 50 [34-66] n=34 · SR +1.01  |
| ratevol    | MID      |                              18 | 56 [44-68] n=62 · 63 [47-77] n=38 · SR +0.35   | 60 [39-78] n=20 · 58 [32-81] n=12 · SR +0.54  | 55 [40-69] n=42 · 65 [46-81] n=26 · SR +0.24  |
| ratevol    | HIGH     |                              25 | 57 [45-68] n=69 · 61 [45-75] n=36 · SR +0.68   | 65 [43-82] n=20 · 64 [35-85] n=11 · SR +0.28  | 53 [39-66] n=49 · 60 [41-77] n=25 · SR +0.99  |
| ratevol    | LOW      |                              57 | 62 [54-69] n=157 · 68 [57-77] n=81 · SR +0.68  | 61 [51-70] n=97 · 70 [56-81] n=50 · SR +0.73  | 63 [51-74] n=60 · 65 [47-79] n=31 · SR +0.58  |
| dollar     | BELOW    |                              46 | 59 [50-66] n=135 · 65 [54-75] n=72 · SR +0.55  | 59 [46-70] n=63 · 64 [47-78] n=33 · SR +0.44  | 58 [47-69] n=72 · 67 [51-79] n=39 · SR +0.72  |
| dollar     | ABOVE    |                              54 | 58 [50-66] n=153 · 63 [53-73] n=82 · SR +0.67  | 60 [48-71] n=68 · 68 [51-80] n=37 · SR +0.75  | 56 [46-67] n=85 · 60 [45-73] n=45 · SR +0.61  |
| inflation  | LOW      |                              68 | 57 [50-64] n=178 · 61 [51-71] n=90 · SR +0.60  | 58 [48-68] n=91 · 59 [44-72] n=46 · SR +0.73  | 56 [46-66] n=87 · 64 [49-76] n=44 · SR +0.43  |
| inflation  | HIGH     |                              32 | 59 [49-69] n=86 · 58 [43-71] n=45 · SR +0.67   | 58 [42-73] n=36 · 58 [36-77] n=19 · SR +0.38  | 60 [46-72] n=50 · 58 [39-74] n=26 · SR +1.05  |
| crowding   | 1-2      |                              46 | 60 [53-68] n=164 · 60 [50-69] n=95 · SR +0.78  | 60 [49-70] n=78 · 60 [45-72] n=47 · SR +0.85  | 60 [50-70] n=86 · 60 [46-73] n=48 · SR +0.74  |
| crowding   | <1       |                              39 | 53 [45-62] n=129 · 56 [45-66] n=77 · SR +0.46  | 53 [41-64] n=68 · 71 [56-82] n=41 · SR +0.44  | 54 [42-66] n=61 · 39 [25-55] n=36 · SR +0.51  |
| crowding   | >2       |                              15 | 65 [52-76] n=60 · 62 [47-75] n=42 · SR +0.58   | 67 [48-81] n=27 · 65 [43-82] n=20 · SR +0.43  | 64 [47-78] n=33 · 59 [39-77] n=22 · SR +0.72  |
| trend_rel  | WITH     |                              75 | 60 [53-66] n=218 · 59 [50-68] n=115 · SR +0.66 | 61 [51-69] n=104 · 64 [51-76] n=56 · SR +0.73 | 59 [50-67] n=114 · 54 [42-66] n=59 · SR +0.58 |
| trend_rel  | COUNTER  |                              25 | 54 [44-63] n=95 · 62 [49-73] n=58 · SR +0.53   | 58 [43-71] n=45 · 63 [44-78] n=27 · SR +0.25  | 50 [37-63] n=50 · 61 [44-76] n=31 · SR +0.85  |

**2y-spread 20d trend**

| regime     | class    |   share of sessions 2006-26 (%) | 2006-26                                        | 2006-15                                       | 2016-26                                       |
|:-----------|:---------|--------------------------------:|:-----------------------------------------------|:----------------------------------------------|:----------------------------------------------|
| policy     | CUT      |                              14 | 56 [41-71] n=39 · 60 [39-78] n=20 · SR +1.44   | 71 [36-92] n=7 · 50 [15-85] n=4 · SR +3.49    | 53 [36-69] n=32 · 62 [39-82] n=16 · SR +0.69  |
| policy     | OTHER    |                               8 | 67 [47-82] n=24 · 25 [9-53] n=12 · SR +0.66    | 79 [52-92] n=14 · 29 [8-64] n=7 · SR +1.05    | 50 [24-76] n=10 · 20 [4-62] n=5 · SR -0.36    |
| policy     | HIKE     |                              32 | 51 [41-62] n=84 · 40 [27-56] n=42 · SR +0.48   | 52 [34-69] n=27 · 43 [21-67] n=14 · SR +1.00  | 51 [38-63] n=57 · 39 [24-58] n=28 · SR +0.22  |
| policy     | LB       |                              46 | 51 [42-60] n=119 · 49 [37-61] n=61 · SR +0.09  | 52 [41-62] n=81 · 49 [34-64] n=41 · SR +0.01  | 50 [35-65] n=38 · 50 [30-70] n=20 · SR +0.30  |
| div_level  | BELOW    |                              48 | 45 [37-54] n=126 · 50 [38-62] n=64 · SR +0.47  | 47 [37-56] n=101 · 51 [38-64] n=51 · SR +0.47 | 40 [23-59] n=25 · 46 [23-71] n=13 · SR +0.50  |
| div_level  | ABOVE    |                              52 | 53 [45-61] n=134 · 48 [36-60] n=67 · SR +0.44  | 52 [33-70] n=25 · 31 [13-58] n=13 · SR +1.07  | 53 [44-62] n=109 · 52 [39-65] n=54 · SR +0.28 |
| div_change | SAME     |                              31 | 48 [38-58] n=92 · 45 [32-59] n=51 · SR +0.37   | 44 [32-58] n=54 · 37 [22-54] n=30 · SR +0.27  | 53 [37-68] n=38 · 57 [37-76] n=21 · SR +0.66  |
| div_change | NARROWER |                              30 | 59 [48-69] n=80 · 44 [30-59] n=41 · SR -0.21   | 55 [40-70] n=38 · 50 [30-70] n=20 · SR -0.18  | 62 [47-75] n=42 · 38 [21-59] n=21 · SR -0.25  |
| div_change | WIDER    |                              39 | 55 [46-64] n=110 · 40 [29-53] n=57 · SR +0.95  | 57 [42-71] n=42 · 30 [16-51] n=23 · SR +1.53  | 54 [43-66] n=68 · 47 [31-63] n=34 · SR +0.49  |
| ratevol    | MID      |                              18 | 58 [46-70] n=62 · 50 [35-65] n=38 · SR +0.11   | 50 [30-70] n=20 · 42 [19-68] n=12 · SR -0.45  | 62 [47-75] n=42 · 54 [35-71] n=26 · SR +0.49  |
| ratevol    | HIGH     |                              25 | 52 [41-64] n=69 · 58 [42-73] n=36 · SR +0.90   | 70 [48-85] n=20 · 55 [28-79] n=11 · SR +2.24  | 45 [32-59] n=49 · 60 [41-77] n=25 · SR +0.05  |
| ratevol    | LOW      |                              57 | 45 [38-53] n=157 · 48 [38-59] n=81 · SR +0.33  | 45 [36-55] n=97 · 42 [29-56] n=50 · SR +0.27  | 45 [33-58] n=60 · 58 [41-74] n=31 · SR +0.48  |
| dollar     | BELOW    |                              46 | 47 [39-56] n=135 · 40 [30-52] n=72 · SR +0.38  | 52 [40-64] n=63 · 48 [33-65] n=33 · SR +0.28  | 43 [32-55] n=72 · 33 [21-49] n=39 · SR +0.54  |
| dollar     | ABOVE    |                              54 | 49 [41-57] n=153 · 50 [39-61] n=82 · SR +0.51  | 43 [32-54] n=68 · 51 [36-67] n=37 · SR +0.81  | 54 [44-64] n=85 · 49 [35-63] n=45 · SR +0.18  |
| inflation  | LOW      |                              68 | 47 [40-55] n=178 · 47 [37-57] n=90 · SR +0.36  | 43 [33-53] n=91 · 41 [28-56] n=46 · SR +0.25  | 52 [41-62] n=87 · 52 [38-66] n=44 · SR +0.52  |
| inflation  | HIGH     |                              32 | 58 [48-68] n=86 · 51 [37-65] n=45 · SR +0.64   | 61 [45-75] n=36 · 53 [32-73] n=19 · SR +1.26  | 56 [42-69] n=50 · 50 [32-68] n=26 · SR -0.03  |
| crowding   | 1-2      |                              46 | 54 [47-62] n=164 · 59 [49-68] n=95 · SR +0.50  | 59 [48-69] n=78 · 62 [47-74] n=47 · SR +0.31  | 50 [40-60] n=86 · 56 [42-69] n=48 · SR +0.75  |
| crowding   | <1       |                              39 | 42 [34-50] n=129 · 48 [37-59] n=77 · SR +0.50  | 41 [30-53] n=68 · 46 [32-61] n=41 · SR +0.90  | 43 [31-55] n=61 · 50 [34-66] n=36 · SR -0.13  |
| crowding   | >2       |                              15 | 63 [51-74] n=60 · 57 [42-71] n=42 · SR +0.18   | 67 [48-81] n=27 · 60 [39-78] n=20 · SR +0.31  | 61 [44-75] n=33 · 55 [35-73] n=22 · SR +0.07  |
| trend_rel  | WITH     |                              58 | 55 [48-61] n=214 · 44 [36-53] n=115 · SR +0.71 | 52 [43-61] n=110 · 47 [35-60] n=57 · SR +0.88 | 58 [48-67] n=104 · 41 [30-54] n=58 · SR +0.47 |
| trend_rel  | COUNTER  |                              42 | 47 [40-54] n=186 · 53 [43-62] n=108 · SR +0.11 | 44 [34-55] n=84 · 49 [36-62] n=51 · SR +0.09  | 49 [40-59] n=102 · 56 [43-68] n=57 · SR +0.14 |

**house macro score**

| regime     | class    |   share of sessions 2006-26 (%) | 2006-26                                        | 2006-15                                       | 2016-26                                       |
|:-----------|:---------|--------------------------------:|:-----------------------------------------------|:----------------------------------------------|:----------------------------------------------|
| policy     | CUT      |                              14 | 51 [36-66] n=39 · 55 [34-74] n=20 · SR +0.11   | 43 [16-75] n=7 · 25 [5-70] n=4 · SR +0.02     | 53 [36-69] n=32 · 62 [39-82] n=16 · SR +0.18  |
| policy     | OTHER    |                               8 | 54 [35-72] n=24 · 58 [32-81] n=12 · SR +0.07   | 57 [33-79] n=14 · 57 [25-84] n=7 · SR -0.71   | 50 [24-76] n=10 · 60 [23-88] n=5 · SR +2.30   |
| policy     | HIKE     |                              32 | 49 [38-59] n=84 · 52 [38-67] n=42 · SR +0.83   | 59 [41-75] n=27 · 64 [39-84] n=14 · SR +0.56  | 44 [32-57] n=57 · 46 [30-64] n=28 · SR +0.96  |
| policy     | LB       |                              46 | 60 [51-68] n=119 · 64 [51-75] n=61 · SR +0.46  | 64 [53-74] n=81 · 68 [53-80] n=41 · SR +0.48  | 50 [35-65] n=38 · 55 [34-74] n=20 · SR +0.44  |
| div_level  | BELOW    |                              48 | 52 [44-61] n=126 · 59 [47-71] n=64 · SR +0.49  | 53 [44-63] n=101 · 59 [45-71] n=51 · SR +0.50 | 48 [30-67] n=25 · 62 [36-82] n=13 · SR +0.48  |
| div_level  | ABOVE    |                              52 | 54 [45-62] n=134 · 52 [40-64] n=67 · SR +0.46  | 60 [41-77] n=25 · 62 [36-82] n=13 · SR -0.59  | 52 [43-61] n=109 · 50 [37-63] n=54 · SR +0.74 |
| div_change | SAME     |                              31 | 59 [48-68] n=92 · 49 [36-62] n=51 · SR +0.55   | 56 [42-68] n=54 · 43 [27-61] n=30 · SR +0.53  | 63 [47-77] n=38 · 57 [37-76] n=21 · SR +0.64  |
| div_change | NARROWER |                              30 | 49 [38-60] n=80 · 59 [43-72] n=41 · SR +0.30   | 42 [28-58] n=38 · 60 [39-78] n=20 · SR +0.13  | 55 [40-69] n=42 · 57 [37-76] n=21 · SR +0.51  |
| div_change | WIDER    |                              39 | 55 [45-64] n=110 · 58 [45-70] n=57 · SR +0.54  | 60 [44-73] n=42 · 70 [49-84] n=23 · SR +0.23  | 51 [40-63] n=68 · 50 [34-66] n=34 · SR +0.83  |
| ratevol    | MID      |                              18 | 60 [47-71] n=62 · 58 [42-72] n=38 · SR +0.88   | 65 [43-82] n=20 · 67 [39-86] n=12 · SR +1.40  | 57 [42-71] n=42 · 54 [35-71] n=26 · SR +0.58  |
| ratevol    | HIGH     |                              25 | 54 [42-65] n=69 · 56 [40-70] n=36 · SR +0.14   | 55 [34-74] n=20 · 36 [15-65] n=11 · SR -0.56  | 53 [39-66] n=49 · 64 [45-80] n=25 · SR +0.63  |
| ratevol    | LOW      |                              57 | 55 [47-62] n=157 · 58 [47-68] n=81 · SR +0.53  | 59 [49-68] n=97 · 60 [46-72] n=50 · SR +0.40  | 48 [36-61] n=60 · 55 [38-71] n=31 · SR +0.83  |
| dollar     | BELOW    |                              46 | 53 [45-62] n=135 · 58 [47-69] n=72 · SR +0.25  | 59 [46-70] n=63 · 55 [38-70] n=33 · SR +0.18  | 49 [37-60] n=72 · 62 [46-75] n=39 · SR +0.34  |
| dollar     | ABOVE    |                              54 | 51 [43-59] n=153 · 54 [43-64] n=82 · SR +0.62  | 53 [41-64] n=68 · 54 [38-69] n=37 · SR +0.36  | 49 [39-60] n=85 · 53 [39-67] n=45 · SR +0.93  |
| inflation  | LOW      |                              68 | 51 [44-58] n=178 · 54 [44-64] n=90 · SR +0.38  | 45 [35-55] n=91 · 54 [40-68] n=46 · SR +0.28  | 57 [47-67] n=87 · 55 [40-68] n=44 · SR +0.52  |
| inflation  | HIGH     |                              32 | 66 [56-75] n=86 · 64 [50-77] n=45 · SR +0.67   | 61 [45-75] n=36 · 63 [41-81] n=19 · SR +0.41  | 70 [56-81] n=50 · 65 [46-81] n=26 · SR +1.01  |
| crowding   | 1-2      |                              46 | 55 [48-63] n=164 · 61 [51-70] n=95 · SR +0.50  | 54 [43-64] n=78 · 64 [50-76] n=47 · SR +0.32  | 57 [46-67] n=86 · 58 [44-71] n=48 · SR +0.75  |
| crowding   | <1       |                              39 | 50 [41-58] n=129 · 49 [38-60] n=77 · SR +0.37  | 53 [41-64] n=68 · 54 [39-68] n=41 · SR +0.27  | 46 [34-58] n=61 · 44 [30-60] n=36 · SR +0.55  |
| crowding   | >2       |                              15 | 62 [49-73] n=60 · 64 [49-77] n=42 · SR +0.69   | 63 [44-78] n=27 · 65 [43-82] n=20 · SR +0.51  | 61 [44-75] n=33 · 64 [43-80] n=22 · SR +0.85  |
| trend_rel  | WITH     |                              52 | 59 [52-65] n=217 · 56 [47-64] n=115 · SR +0.85 | 60 [50-69] n=105 · 54 [42-67] n=57 · SR +0.88 | 58 [49-67] n=112 · 57 [44-69] n=58 · SR +0.84 |
| trend_rel  | COUNTER  |                              48 | 49 [42-56] n=211 · 46 [37-55] n=112 · SR +0.12 | 45 [36-54] n=107 · 40 [29-53] n=57 · SR -0.16 | 53 [43-62] n=104 · 51 [38-64] n=55 · SR +0.53 |

**December long**

| regime     | class    |   share of sessions 2006-26 (%) | 2006-26                                        | 2006-15                                        | 2016-26                                        |
|:-----------|:---------|--------------------------------:|:-----------------------------------------------|:-----------------------------------------------|:-----------------------------------------------|
| policy     | CUT      |                              14 | 75 [30-95] n=4 · 50 [15-85] n=4 · SR +0.86     | 100 [21-100] n=1 · 100 [21-100] n=1 · SR +2.17 | 67 [21-94] n=3 · 33 [6-79] n=3 · SR +0.20      |
| policy     | OTHER    |                               8 | 100 [21-100] n=1 · 100 [21-100] n=1 · SR +0.19 | 100 [21-100] n=1 · 100 [21-100] n=1 · SR -0.12 | - · - · SR +1.11                               |
| policy     | HIKE     |                              32 | 100 [57-100] n=5 · 60 [23-88] n=5 · SR +0.56   | 100 [21-100] n=1 · 0 [0-79] n=1 · SR -0.13     | 100 [51-100] n=4 · 75 [30-95] n=4 · SR +0.79   |
| policy     | LB       |                              46 | 60 [31-83] n=10 · 50 [24-76] n=10 · SR -0.09   | 57 [25-84] n=7 · 43 [16-75] n=7 · SR -0.16     | 67 [21-94] n=3 · 67 [21-94] n=3 · SR +0.11     |
| div_level  | BELOW    |                              48 | 73 [43-90] n=11 · 55 [28-79] n=11 · SR +0.30   | 67 [35-88] n=9 · 56 [27-81] n=9 · SR +0.26     | 100 [34-100] n=2 · 50 [9-91] n=2 · SR +0.69    |
| div_level  | ABOVE    |                              52 | 78 [45-94] n=9 · 56 [27-81] n=9 · SR +0.28     | 100 [21-100] n=1 · 0 [0-79] n=1 · SR -0.34     | 75 [41-93] n=8 · 62 [31-86] n=8 · SR +0.41     |
| div_change | SAME     |                              31 | 56 [27-81] n=9 · 44 [19-73] n=9 · SR +0.36     | 60 [23-88] n=5 · 40 [12-77] n=5 · SR +0.49     | 50 [15-85] n=4 · 50 [15-85] n=4 · SR +0.04     |
| div_change | NARROWER |                              30 | 100 [57-100] n=5 · 40 [12-77] n=5 · SR +0.12   | 100 [34-100] n=2 · 50 [9-91] n=2 · SR -0.18    | 100 [44-100] n=3 · 33 [6-79] n=3 · SR +0.45    |
| div_change | WIDER    |                              39 | 83 [44-97] n=6 · 83 [44-97] n=6 · SR +0.30     | 67 [21-94] n=3 · 67 [21-94] n=3 · SR -0.02     | 100 [44-100] n=3 · 100 [44-100] n=3 · SR +0.83 |
| ratevol    | MID      |                              18 | 100 [44-100] n=3 · 33 [6-79] n=3 · SR +0.39    | - · - · SR -0.66                               | 100 [44-100] n=3 · 33 [6-79] n=3 · SR +0.83    |
| ratevol    | HIGH     |                              25 | 80 [38-96] n=5 · 60 [23-88] n=5 · SR +0.63     | 100 [34-100] n=2 · 100 [34-100] n=2 · SR +1.08 | 67 [21-94] n=3 · 33 [6-79] n=3 · SR +0.29      |
| ratevol    | LOW      |                              57 | 67 [39-86] n=12 · 58 [32-81] n=12 · SR +0.05   | 62 [31-86] n=8 · 38 [14-69] n=8 · SR -0.11     | 75 [30-95] n=4 · 100 [51-100] n=4 · SR +0.42   |
| dollar     | BELOW    |                              46 | 88 [53-98] n=8 · 75 [41-93] n=8 · SR +0.17     | 80 [38-96] n=5 · 60 [23-88] n=5 · SR -0.07     | 100 [44-100] n=3 · 100 [44-100] n=3 · SR +0.65 |
| dollar     | ABOVE    |                              54 | 67 [39-86] n=12 · 42 [19-68] n=12 · SR +0.36   | 60 [23-88] n=5 · 40 [12-77] n=5 · SR +0.37     | 71 [36-92] n=7 · 43 [16-75] n=7 · SR +0.38     |
| inflation  | LOW      |                              68 | 71 [45-88] n=14 · 57 [33-79] n=14 · SR +0.12   | 75 [41-93] n=8 · 50 [22-78] n=8 · SR +0.04     | 67 [30-90] n=6 · 67 [30-90] n=6 · SR +0.25     |
| inflation  | HIGH     |                              32 | 83 [44-97] n=6 · 50 [19-81] n=6 · SR +0.52     | 50 [9-91] n=2 · 50 [9-91] n=2 · SR +0.43       | 100 [51-100] n=4 · 50 [15-85] n=4 · SR +0.81   |
| crowding   | 1-2      |                              46 | 50 [19-81] n=6 · 33 [10-70] n=6 · SR -0.21     | 0 [0-66] n=2 · 0 [0-66] n=2 · SR -0.43         | 75 [30-95] n=4 · 50 [15-85] n=4 · SR +0.09     |
| crowding   | <1       |                              39 | 85 [58-96] n=13 · 62 [36-82] n=13 · SR +0.53   | 88 [53-98] n=8 · 62 [31-86] n=8 · SR +0.44     | 80 [38-96] n=5 · 60 [23-88] n=5 · SR +0.81     |
| crowding   | >2       |                              15 | 100 [21-100] n=1 · 100 [21-100] n=1 · SR +0.50 | - · - · SR +1.07                               | 100 [21-100] n=1 · 100 [21-100] n=1 · SR +0.33 |
| trend_rel  | WITH     |                              53 | 90 [60-98] n=10 · 60 [31-83] n=10 · SR +1.14   | 80 [38-96] n=5 · 40 [12-77] n=5 · SR -0.20     | 100 [57-100] n=5 · 80 [38-96] n=5 · SR +3.36   |
| trend_rel  | COUNTER  |                              47 | 60 [31-83] n=10 · 50 [24-76] n=10 · SR +0.93   | 60 [23-88] n=5 · 60 [23-88] n=5 · SR +1.39     | 60 [23-88] n=5 · 40 [12-77] n=5 · SR +0.32     |

**relative equity momentum**

| regime     | class    |   share of sessions 2006-26 (%) | 2006-26                                        | 2006-15                                       | 2016-26                                       |
|:-----------|:---------|--------------------------------:|:-----------------------------------------------|:----------------------------------------------|:----------------------------------------------|
| policy     | CUT      |                              14 | 56 [41-71] n=39 · 55 [34-74] n=20 · SR +0.07   | 14 [3-51] n=7 · 50 [15-85] n=4 · SR -0.38     | 66 [48-80] n=32 · 56 [33-77] n=16 · SR +0.29  |
| policy     | OTHER    |                               8 | 38 [21-57] n=24 · 42 [19-68] n=12 · SR +0.11   | 50 [27-73] n=14 · 43 [16-75] n=7 · SR -0.68   | 20 [6-51] n=10 · 40 [12-77] n=5 · SR +2.35    |
| policy     | HIKE     |                              32 | 49 [38-61] n=67 · 62 [45-76] n=34 · SR +0.67   | 70 [40-89] n=10 · 100 [61-100] n=6 · SR +2.26 | 46 [33-58] n=57 · 54 [36-70] n=28 · SR +0.34  |
| policy     | LB       |                              46 | 53 [44-62] n=119 · 61 [48-72] n=61 · SR +0.26  | 57 [46-67] n=81 · 66 [51-78] n=41 · SR +0.38  | 45 [30-60] n=38 · 50 [30-70] n=20 · SR -0.08  |
| div_level  | BELOW    |                              48 | 52 [43-60] n=126 · 53 [41-65] n=64 · SR +0.14  | 54 [45-64] n=101 · 53 [40-66] n=51 · SR +0.27 | 40 [23-59] n=25 · 54 [29-77] n=13 · SR -0.67  |
| div_level  | ABOVE    |                              52 | 61 [52-69] n=117 · 49 [37-62] n=59 · SR +0.55  | 75 [41-93] n=8 · 60 [23-88] n=5 · SR +1.04    | 60 [50-68] n=109 · 48 [35-61] n=54 · SR +0.51 |
| div_change | SAME     |                              31 | 57 [46-66] n=90 · 61 [47-74] n=49 · SR +0.08   | 56 [42-68] n=52 · 61 [42-76] n=28 · SR +0.12  | 58 [42-72] n=38 · 62 [41-79] n=21 · SR -0.02  |
| div_change | NARROWER |                              30 | 53 [42-64] n=73 · 53 [37-68] n=38 · SR +0.44   | 55 [38-71] n=31 · 59 [36-78] n=17 · SR +0.45  | 52 [38-67] n=42 · 48 [28-68] n=21 · SR +0.45  |
| div_change | WIDER    |                              39 | 59 [50-68] n=101 · 58 [44-70] n=52 · SR +0.42  | 73 [56-85] n=33 · 67 [44-84] n=18 · SR +0.53  | 53 [41-64] n=68 · 53 [37-69] n=34 · SR +0.35  |
| ratevol    | MID      |                              18 | 52 [39-64] n=58 · 44 [30-60] n=36 · SR +0.12   | 38 [18-61] n=16 · 40 [17-69] n=10 · SR -0.82  | 57 [42-71] n=42 · 46 [29-65] n=26 · SR +0.67  |
| ratevol    | HIGH     |                              25 | 61 [49-72] n=69 · 58 [42-73] n=36 · SR +0.04   | 55 [34-74] n=20 · 36 [15-65] n=11 · SR -0.54  | 63 [49-75] n=49 · 68 [48-83] n=25 · SR +0.44  |
| ratevol    | LOW      |                              57 | 58 [50-66] n=141 · 52 [41-63] n=73 · SR +0.52  | 65 [55-75] n=81 · 67 [52-79] n=42 · SR +0.81  | 48 [36-61] n=60 · 32 [19-50] n=31 · SR -0.03  |
| dollar     | BELOW    |                              46 | 53 [45-62] n=128 · 59 [47-70] n=68 · SR -0.02  | 54 [41-66] n=56 · 52 [34-69] n=29 · SR +0.53  | 53 [41-64] n=72 · 64 [48-77] n=39 · SR -0.71  |
| dollar     | ABOVE    |                              54 | 55 [47-62] n=150 · 51 [40-62] n=80 · SR +0.54  | 57 [45-68] n=65 · 54 [38-70] n=35 · SR +0.19  | 53 [42-63] n=85 · 49 [35-63] n=45 · SR +0.97  |
| inflation  | LOW      |                              68 | 59 [51-66] n=172 · 62 [52-72] n=87 · SR +0.25  | 66 [55-75] n=85 · 70 [55-81] n=43 · SR +0.36  | 52 [41-62] n=87 · 55 [40-68] n=44 · SR +0.10  |
| inflation  | HIGH     |                              32 | 55 [43-65] n=75 · 54 [39-68] n=39 · SR +0.45   | 56 [37-73] n=25 · 62 [36-82] n=13 · SR +0.26  | 54 [40-67] n=50 · 50 [32-68] n=26 · SR +0.66  |
| crowding   | 1-2      |                              46 | 55 [47-63] n=151 · 52 [42-62] n=88 · SR -0.07  | 55 [43-67] n=65 · 57 [42-71] n=40 · SR -0.05  | 55 [44-65] n=86 · 48 [34-62] n=48 · SR -0.11  |
| crowding   | <1       |                              39 | 51 [42-60] n=120 · 55 [43-66] n=71 · SR +0.31  | 53 [40-65] n=59 · 54 [38-70] n=35 · SR +0.22  | 49 [37-61] n=61 · 56 [40-70] n=36 · SR +0.47  |
| crowding   | >2       |                              15 | 63 [50-74] n=57 · 68 [52-80] n=40 · SR +1.58   | 62 [43-79] n=24 · 72 [49-88] n=18 · SR +2.20  | 64 [47-78] n=33 · 64 [43-80] n=22 · SR +1.11  |
| trend_rel  | WITH     |                              47 | 58 [51-65] n=187 · 58 [49-67] n=105 · SR +0.74 | 58 [48-68] n=86 · 59 [45-72] n=49 · SR +0.92  | 57 [48-67] n=101 · 57 [44-69] n=56 · SR +0.55 |
| trend_rel  | COUNTER  |                              53 | 48 [41-54] n=204 · 50 [41-59] n=110 · SR -0.03 | 46 [36-56] n=91 · 51 [37-64] n=49 · SR -0.15  | 49 [40-58] n=113 · 49 [37-61] n=61 · SR +0.10 |

**AGREEMENT RULE**

| regime     | class    |   share of sessions 2006-26 (%) | 2006-26                                       | 2006-15                                      | 2016-26                                      |
|:-----------|:---------|--------------------------------:|:----------------------------------------------|:---------------------------------------------|:---------------------------------------------|
| policy     | CUT      |                              14 | 57 [39-73] n=30 · 53 [31-74] n=17 · SR +0.09  | 50 [15-85] n=4 · 67 [21-94] n=3 · SR +0.48   | 58 [39-74] n=26 · 50 [27-73] n=14 · SR -0.07 |
| policy     | OTHER    |                               8 | 53 [30-75] n=15 · 50 [24-76] n=10 · SR +0.14  | 67 [35-88] n=9 · 67 [30-90] n=6 · SR +0.30   | 33 [10-70] n=6 · 25 [5-70] n=4 · SR -0.30    |
| policy     | HIKE     |                              32 | 55 [42-67] n=55 · 59 [42-74] n=32 · SR +0.81  | 40 [22-61] n=20 · 42 [19-68] n=12 · SR +0.77 | 63 [46-77] n=35 · 70 [48-85] n=20 · SR +0.83 |
| policy     | LB       |                              46 | 59 [49-69] n=96 · 58 [45-70] n=55 · SR +0.46  | 64 [52-75] n=64 · 56 [40-70] n=36 · SR +0.42 | 50 [34-66] n=32 · 63 [41-81] n=19 · SR +0.57 |
| div_level  | BELOW    |                              48 | 60 [50-69] n=99 · 61 [48-73] n=57 · SR +0.53  | 64 [53-74] n=78 · 60 [45-73] n=45 · SR +0.51 | 43 [24-63] n=21 · 67 [39-86] n=12 · SR +0.66 |
| div_level  | ABOVE    |                              52 | 56 [46-66] n=93 · 52 [39-64] n=56 · SR +0.46  | 44 [25-66] n=18 · 33 [14-61] n=12 · SR +0.27 | 59 [47-69] n=75 · 57 [42-70] n=44 · SR +0.49 |
| div_change | SAME     |                              31 | 55 [43-66] n=73 · 56 [41-69] n=45 · SR +0.20  | 55 [40-69] n=42 · 44 [27-63] n=25 · SR +0.16 | 55 [38-71] n=31 · 70 [48-85] n=20 · SR +0.32 |
| div_change | NARROWER |                              30 | 52 [39-64] n=60 · 41 [26-57] n=37 · SR -0.20  | 54 [36-70] n=28 · 42 [23-64] n=19 · SR -0.20 | 50 [34-66] n=32 · 39 [20-61] n=18 · SR -0.21 |
| div_change | WIDER    |                              39 | 64 [52-74] n=74 · 70 [56-81] n=47 · SR +1.23  | 68 [50-81] n=31 · 70 [48-85] n=20 · SR +1.52 | 60 [46-74] n=43 · 70 [52-84] n=27 · SR +1.02 |
| ratevol    | MID      |                              18 | 61 [47-74] n=44 · 73 [56-86] n=30 · SR +0.24  | 69 [42-87] n=13 · 70 [40-89] n=10 · SR +0.19 | 58 [41-74] n=31 · 75 [53-89] n=20 · SR +0.27 |
| ratevol    | HIGH     |                              25 | 62 [48-74] n=50 · 55 [38-72] n=29 · SR +0.50  | 67 [39-86] n=12 · 62 [31-86] n=8 · SR +0.27  | 61 [45-74] n=38 · 52 [32-72] n=21 · SR +0.60 |
| ratevol    | LOW      |                              57 | 55 [46-64] n=116 · 65 [52-75] n=65 · SR +0.56 | 59 [48-70] n=76 · 63 [48-76] n=43 · SR +0.55 | 48 [33-63] n=40 · 68 [47-84] n=22 · SR +0.59 |
| dollar     | BELOW    |                              46 | 56 [46-65] n=97 · 61 [48-72] n=59 · SR +0.56  | 51 [37-64] n=49 · 57 [39-73] n=30 · SR +0.40 | 60 [46-73] n=48 · 66 [47-80] n=29 · SR +0.89 |
| dollar     | ABOVE    |                              54 | 54 [45-63] n=116 · 61 [49-71] n=66 · SR +0.41 | 51 [38-64] n=51 · 59 [41-74] n=29 · SR +0.48 | 57 [45-68] n=65 · 62 [46-76] n=37 · SR +0.34 |
| inflation  | LOW      |                              68 | 56 [48-64] n=130 · 54 [43-65] n=76 · SR +0.49 | 60 [48-71] n=70 · 51 [36-66] n=41 · SR +0.50 | 52 [39-64] n=60 · 57 [41-72] n=35 · SR +0.49 |
| inflation  | HIGH     |                              32 | 57 [45-69] n=63 · 55 [40-70] n=38 · SR +0.50  | 54 [35-71] n=26 · 53 [30-75] n=15 · SR +0.42 | 59 [43-74] n=37 · 57 [37-74] n=23 · SR +0.57 |
| crowding   | 1-2      |                              46 | 63 [54-71] n=117 · 68 [56-77] n=77 · SR +0.63 | 60 [47-72] n=58 · 67 [51-79] n=39 · SR +0.39 | 66 [53-77] n=59 · 68 [53-81] n=38 · SR +0.92 |
| crowding   | <1       |                              39 | 45 [35-55] n=85 · 57 [44-69] n=58 · SR +0.35  | 47 [33-61] n=47 · 56 [39-71] n=34 · SR +0.58 | 42 [28-58] n=38 · 58 [39-76] n=24 · SR -0.01 |
| crowding   | >2       |                              15 | 63 [49-75] n=49 · 63 [46-77] n=35 · SR +0.44  | 77 [57-90] n=22 · 62 [39-82] n=16 · SR +0.44 | 52 [34-69] n=27 · 63 [41-81] n=19 · SR +0.44 |
| trend_rel  | WITH     |                              78 | 56 [48-64] n=155 · 57 [47-66] n=97 · SR +0.82 | 55 [44-66] n=78 · 59 [45-72] n=49 · SR +0.71 | 57 [46-68] n=77 · 54 [40-67] n=48 · SR +0.98 |
| trend_rel  | COUNTER  |                              22 | 50 [38-62] n=68 · 63 [49-75] n=46 · SR +0.82  | 57 [39-73] n=30 · 55 [35-73] n=22 · SR +1.15 | 45 [30-60] n=38 · 71 [51-85] n=24 · SR +0.45 |

## 4. Tradeable test
`cond_div_change`, walk-forward choice of the muted class(es) by test year: from 2010: none; from 2013: NARROWER.

`strict_div_change`, walk-forward choice of the favourable class(es) by test year: from 2010: none; from 2012: SAME; from 2015: WIDER.

**Non-overlapping decisions, conditional rule against the unconditional agreement rule** (`cond_` = the rule declared before the first run; `strict_` = post hoc)

| rule              |   hold | period   | unconditional             | conditional               |   difference (pts) | paired bootstrap 95 %   |   p(diff <= 0) | weekly: uncond -> cond (n)   | refused calls right % (n)   | net bp/decision: uncond -> cond   |
|:------------------|-------:|:---------|:--------------------------|:--------------------------|-------------------:|:------------------------|---------------:|:-----------------------------|:----------------------------|:----------------------------------|
| cond_div_change   |     21 | 2010-26  | 59 [51-66] n=156 (9.0/yr) | 62 [53-70] n=128 (7.4/yr) |                2.7 | [-1, +8]                |           0.08 | 59 -> 61 (318)               | 54 (69)                     | +55 -> +66                        |
| cond_div_change   |     21 | 2016-26  | 57 [47-67] n=96 (8.7/yr)  | 62 [50-72] n=68 (6.1/yr)  |                4.5 | [-2, +14]               |           0.1  | 57 -> 59 (174)               | 54 (69)                     | +48 -> +66                        |
| cond_div_change   |     21 | 2023-26  | 60 [44-74] n=35 (9.0/yr)  | 63 [41-81] n=19 (4.9/yr)  |                3.2 | [-6, +29]               |           0.17 | 55 -> 53 (38)                | 56 (39)                     | +19 -> +37                        |
| cond_div_change   |     42 | 2010-26  | 61 [50-70] n=89 (5.2/yr)  | 65 [54-75] n=75 (4.4/yr)  |                4.7 | [-3, +10]               |           0.17 | 65 -> 66 (318)               | 57 (65)                     | +99 -> +111                       |
| cond_div_change   |     42 | 2016-26  | 59 [46-71] n=56 (5.1/yr)  | 67 [52-79] n=42 (3.8/yr)  |                7.7 | [-4, +17]               |           0.15 | 63 -> 66 (174)               | 57 (65)                     | +89 -> +107                       |
| cond_div_change   |     42 | 2023-26  | 45 [26-66] n=20 (5.3/yr)  | 50 [25-75] n=12 (3.2/yr)  |                5   | [-10, +33]              |           0.19 | 47 -> 47 (38)                | 46 (35)                     | -7 -> -10                         |
| strict_div_change |     21 | 2010-26  | 59 [51-66] n=156 (9.0/yr) | 59 [48-69] n=83 (4.8/yr)  |                0.1 | [-8, +11]               |           0.39 | 59 -> 60 (191)               | 59 (196)                    | +55 -> +76                        |
| strict_div_change |     21 | 2016-26  | 57 [47-67] n=96 (8.7/yr)  | 60 [46-74] n=43 (3.9/yr)  |                3.2 | [-9, +19]               |           0.22 | 57 -> 61 (105)               | 54 (138)                    | +48 -> +61                        |
| strict_div_change |     21 | 2023-26  | 60 [44-74] n=35 (9.0/yr)  | 58 [32-81] n=12 (3.1/yr)  |               -1.7 | [-21, +34]              |           0.36 | 55 -> 50 (22)                | 56 (55)                     | +19 -> +59                        |
| strict_div_change |     42 | 2010-26  | 61 [50-70] n=89 (5.2/yr)  | 65 [51-76] n=51 (3.0/yr)  |                4   | [-10, +10]              |           0.5  | 65 -> 65 (191)               | 64 (192)                    | +99 -> +116                       |
| strict_div_change |     42 | 2016-26  | 59 [46-71] n=56 (5.1/yr)  | 70 [52-84] n=27 (2.5/yr)  |               11.4 | [-10, +19]              |           0.26 | 63 -> 68 (105)               | 60 (134)                    | +89 -> +143                       |
| strict_div_change |     42 | 2023-26  | 45 [26-66] n=20 (5.3/yr)  | 56 [27-81] n=9 (2.4/yr)   |               10.6 | [-7, +45]               |           0.1  | 47 -> 36 (22)                | 51 (51)                     | -7 -> +75                         |

**Round 5 bar**

| rule              | post_hoc   | gain_ge_3pts_21_and_42_in_2010-26_and_2016-26   | ge_6_decisions_a_year_21   | not_worse_2023-26   | ge_6_decisions_a_year_2010-15   |   wilson_lo_2010-15 |
|:------------------|:-----------|:------------------------------------------------|:---------------------------|:--------------------|:--------------------------------|--------------------:|
| cond_div_change   | False      | False                                           | True                       | True                | True                            |            0.490176 |
| strict_div_change | True       | False                                           | False                      | False               | True                            |            0.421951 |

**Protocol table, net Sharpe at 1.2 pips** (weekly-tranche books `agree3_unconditional`, `cond_*`, `strict_*`; `daily_*` = position held only on sessions on which the rule speaks, added after the first run; 0.6-pip rows in the report csv change nothing beyond 0.02)

| variant                    |   2010-2015 |   2010-2026 |   2016-2026 |   2023-2026 |   t 2010-2026 |   t 2016-2026 |
|:---------------------------|------------:|------------:|------------:|------------:|--------------:|--------------:|
| agree3_unconditional       |        0.56 |        0.52 |        0.51 |        0.43 |          2.17 |          1.72 |
| cond_div_change            |        0.56 |        0.52 |        0.53 |        0.43 |          2.17 |          1.77 |
| daily_agree3_unconditional |        0.63 |        0.56 |        0.52 |        0.2  |          2.34 |          1.75 |
| daily_cond_div_change      |        0.63 |        0.63 |        0.67 |        0.48 |          2.64 |          2.24 |
| daily_strict_div_change    |        0.97 |        0.8  |        0.69 |        0.71 |          3.34 |          2.31 |
| strict_div_change          |        0.55 |        0.46 |        0.41 |        0.31 |          1.9  |          1.38 |

**Full-pipeline placebo** (300 joint rotations of the regime labels; the screen of section 3 is applied to each, and the walk-forward rules are run on whatever passes: 94 draws, 31 %, pass something). This prices the fact that the regime VARIABLE was chosen on the whole sample. Unconditional references: non-overlapping gain 0 by definition, tranche-book Sharpe 0.52 / 0.51 / 0.43, daily-stream Sharpe 0.56 / 0.52 / 0.20.

| statistic                   |   real |   placebo mean | placebo 5 % / 95 %   |   share of passing placebo draws >= real |
|:----------------------------|-------:|---------------:|:---------------------|-----------------------------------------:|
| gain21_2010-26              |  0.027 |          0.007 | -0.032 / 0.055       |                                    0.191 |
| gain21_2016-26              |  0.045 |          0.014 | -0.050 / 0.110       |                                    0.213 |
| gain42_2010-26              |  0.047 |          0.031 | -0.015 / 0.090       |                                    0.266 |
| gain42_2016-26              |  0.077 |          0.044 | -0.035 / 0.155       |                                    0.234 |
| book_sharpe_2010-26         |  0.521 |          0.488 | 0.388 / 0.629        |                                    0.266 |
| daily_sharpe_2010-26        |  0.633 |          0.576 | 0.462 / 0.744        |                                    0.255 |
| book_sharpe_2016-26         |  0.529 |          0.466 | 0.257 / 0.681        |                                    0.309 |
| daily_sharpe_2016-26        |  0.671 |          0.51  | 0.305 / 0.725        |                                    0.138 |
| book_sharpe_2023-26         |  0.426 |          0.379 | -0.025 / 0.770       |                                    0.5   |
| daily_sharpe_2023-26        |  0.478 |          0.234 | -0.179 / 0.712       |                                    0.17  |
| strict_gain21_2010-26       |  0.001 |          0.013 | -0.036 / 0.085       |                                    0.596 |
| strict_gain21_2016-26       |  0.032 |          0.031 | -0.065 / 0.247       |                                    0.362 |
| strict_gain42_2010-26       |  0.04  |          0.05  | -0.012 / 0.161       |                                    0.489 |
| strict_gain42_2016-26       |  0.114 |          0.053 | -0.056 / 0.167       |                                    0.181 |
| strict_book_sharpe_2010-26  |  0.457 |          0.447 | 0.329 / 0.544        |                                    0.479 |
| strict_daily_sharpe_2010-26 |  0.801 |          0.572 | 0.396 / 0.748        |                                    0.021 |
| strict_book_sharpe_2016-26  |  0.412 |          0.408 | 0.139 / 0.614        |                                    0.543 |
| strict_daily_sharpe_2016-26 |  0.692 |          0.443 | 0.115 / 0.678        |                                    0.043 |
| strict_book_sharpe_2023-26  |  0.315 |          0.371 | -0.075 / 0.727       |                                    0.489 |
| strict_daily_sharpe_2023-26 |  0.71  |          0.262 | -0.139 / 0.603       |                                    0.032 |

**Daily streams per year (net Sharpe)**

|   period |   daily_agree3_unconditional |   daily_cond_div_change |   daily_strict_div_change |
|---------:|-----------------------------:|------------------------:|--------------------------:|
|     2010 |                         1.71 |                    1.71 |                      1.71 |
|     2011 |                         1.51 |                    1.51 |                      1.51 |
|     2012 |                         0.65 |                    0.65 |                     -1.07 |
|     2013 |                        -0.87 |                   -0.87 |                     -1.27 |
|     2014 |                         1.61 |                    1.61 |                      1.31 |
|     2015 |                        -1.28 |                   -1.28 |                      2.78 |
|     2016 |                         0.22 |                    0.22 |                     -0.15 |
|     2017 |                         2.13 |                    2.13 |                      2.13 |
|     2018 |                         0.57 |                    0.57 |                      0.57 |
|     2019 |                        -0.38 |                    1.06 |                      0.81 |
|     2020 |                         0.42 |                    0.47 |                      0    |
|     2021 |                         0.52 |                    0.52 |                      0    |
|     2022 |                         1    |                    1    |                      1.15 |
|     2023 |                        -0.21 |                    0.57 |                      1.21 |
|     2024 |                         0.59 |                    0.71 |                      0.41 |
|     2025 |                         0.5  |                    0.38 |                      0.83 |
|     2026 |                        -0.05 |                   -1.14 |                      0    |

**Robustness of the post hoc daily-gated stream** (added after the first run)

| check                                                                           |   sharpe 2010-26 |   sharpe 2016-26 |   sharpe 2023-26 | share placebo >= real 2010-26   | share placebo >= real 2016-26   | share placebo >= real 2023-26   | regime     |
|:--------------------------------------------------------------------------------|-----------------:|-----------------:|-----------------:|:--------------------------------|:--------------------------------|:--------------------------------|:-----------|
| unconditional daily stream                                                      |             0.56 |             0.52 |             0.2  | -                               | -                               | -                               | div_change |
| strict gate, walk-forward class choice (post hoc candidate)                     |             0.8  |             0.69 |             0.71 | -                               | -                               | -                               | div_change |
| strict gate, class chosen with hindsight                                        |             0.71 |             0.69 |             0.71 | -                               | -                               | -                               | div_change |
| strict gate, regime labels lagged +5 sessions                                   |             0.76 |             0.65 |             0.62 | -                               | -                               | -                               | div_change |
| strict gate, regime labels lagged +21 sessions                                  |             0.79 |             0.56 |             0.29 | -                               | -                               | -                               | div_change |
| strict gate, regime labels lagged +63 sessions                                  |             0.63 |             0.7  |             0.78 | -                               | -                               | -                               | div_change |
| strict gate, regime labels lagged +126 sessions                                 |             0.58 |             0.29 |             0.2  | -                               | -                               | -                               | div_change |
| year 2015 removed: unconditional                                                |             0.72 |             0.52 |             0.2  | -                               | -                               | -                               | div_change |
| year 2015 removed: strict gate                                                  |             0.75 |             0.69 |             0.71 | -                               | -                               | -                               | div_change |
| year 2023 removed: unconditional                                                |             0.61 |             0.61 |             0.39 | -                               | -                               | -                               | div_change |
| year 2023 removed: strict gate                                                  |             0.79 |             0.65 |             0.54 | -                               | -                               | -                               | div_change |
| year 2019 removed: unconditional                                                |             0.59 |             0.57 |             0.2  | -                               | -                               | -                               | div_change |
| year 2019 removed: strict gate                                                  |             0.82 |             0.71 |             0.71 | -                               | -                               | -                               | div_change |
| this variable's labels rotated by >= 1 year (300 draws, no screen): mean Sharpe |             0.56 |             0.4  |             0.24 | 0.000                           | 0.027                           | 0.043                           | div_change |

## 5. Leak checks
Gain = non-overlapping accuracy of the conditional rule minus the unconditional rule.

| rule              | check                                                                                 | gain21 2010-26   | gain42 2010-26   | gain21 2016-26   | gain42 2016-26   |   acc21 2010-26 | acc42 2010-26   | n21 2010-26   | share placebo >= real 21 2010-26   | share placebo >= real 42 2010-26   | share placebo >= real 21 2016-26   | share placebo >= real 42 2016-26   |
|:------------------|:--------------------------------------------------------------------------------------|:-----------------|:-----------------|:-----------------|:-----------------|----------------:|:----------------|:--------------|:-----------------------------------|:-----------------------------------|:-----------------------------------|:-----------------------------------|
| cond              | baseline (walk-forward class choice)                                                  | 0.027            | 0.047            | 0.045            | 0.077            |           0.617 | 0.653           | 128.000       | -                                  | -                                  | -                                  | -                                  |
| cond              | regime labels lagged +21 sessions                                                     | 0.035            | 0.113            | 0.041            | 0.161            |           0.625 | 0.719           | 96.000        | -                                  | -                                  | -                                  | -                                  |
| cond              | regime labels lagged +63 sessions                                                     | -0.006           | 0.008            | -0.003           | 0.031            |           0.583 | 0.614           | 144.000       | -                                  | -                                  | -                                  | -                                  |
| cond              | regime labels lagged +126 sessions                                                    | 0.010            | 0.020            | 0.022            | 0.006            |           0.6   | 0.627           | 120.000       | -                                  | -                                  | -                                  | -                                  |
| cond              | look-ahead control: regime labels from 126 sessions ahead                             | 0.006            | 0.043            | 0.006            | 0.070            |           0.596 | 0.650           | 136.000       | -                                  | -                                  | -                                  | -                                  |
| cond              | look-ahead control: muted classes chosen with hindsight (2010-26)                     | 0.028            | 0.046            | 0.045            | 0.077            |           0.618 | 0.653           | 123.000       | -                                  | -                                  | -                                  | -                                  |
| cond              | look-ahead control: oracle regime = future 21-session outcome                         | 0.340            | 0.191            | 0.427            | 0.215            |           0.93  | 0.797           | 128.000       | -                                  | -                                  | -                                  | -                                  |
| cond              | regime labels shuffled (iid shuffle, 300 draws): mean                                 | -0.010           | 0.022            | -0.005           | 0.037            |           0.58  | 0.629           | 151.297       | 0.020                              | 0.150                              | 0.023                              | 0.147                              |
| cond              | regime labels shuffled (block rotation, 300 draws): mean                              | -0.001           | 0.016            | -0.005           | 0.014            |           0.588 | 0.622           | 128.823       | 0.077                              | 0.127                              | 0.070                              | 0.107                              |
| cond              | outcomes rotated against the calls (200 draws): mean accuracy of the conditional rule | -                | -                | -                | -                |           0.497 | 0.497           | -             | -                                  | -                                  | -                                  | -                                  |
| strict (post hoc) | baseline (walk-forward class choice)                                                  | 0.001            | 0.040            | 0.032            | 0.114            |           0.59  | 0.647           | 83.000        | -                                  | -                                  | -                                  | -                                  |
| strict (post hoc) | regime labels lagged +21 sessions                                                     | 0.017            | 0.091            | 0.041            | 0.161            |           0.607 | 0.698           | 89.000        | -                                  | -                                  | -                                  | -                                  |
| strict (post hoc) | regime labels lagged +63 sessions                                                     | 0.009            | 0.075            | 0.027            | 0.111            |           0.598 | 0.682           | 117.000       | -                                  | -                                  | -                                  | -                                  |
| strict (post hoc) | regime labels lagged +126 sessions                                                    | 0.017            | 0.033            | 0.031            | -0.014           |           0.607 | 0.640           | 89.000        | -                                  | -                                  | -                                  | -                                  |
| strict (post hoc) | look-ahead control: regime labels from 126 sessions ahead                             | -0.007           | 0.018            | -0.045           | 0.019            |           0.582 | 0.625           | 79.000        | -                                  | -                                  | -                                  | -                                  |
| strict (post hoc) | look-ahead control: muted classes chosen with hindsight (2010-26)                     | 0.029            | 0.086            | 0.032            | 0.114            |           0.619 | 0.692           | 63.000        | -                                  | -                                  | -                                  | -                                  |
| strict (post hoc) | look-ahead control: oracle regime = future 21-session outcome                         | 0.340            | 0.191            | 0.427            | 0.215            |           0.93  | 0.797           | 128.000       | -                                  | -                                  | -                                  | -                                  |
| strict (post hoc) | regime labels shuffled (iid shuffle, 300 draws): mean                                 | -0.013           | 0.028            | -0.005           | 0.035            |           0.577 | 0.635           | 143.777       | 0.233                              | 0.337                              | 0.107                              | 0.040                              |
| strict (post hoc) | regime labels shuffled (block rotation, 300 draws): mean                              | 0.003            | 0.033            | 0.003            | 0.031            |           0.593 | 0.640           | 103.127       | 0.513                              | 0.360                              | 0.230                              | 0.120                              |
| strict (post hoc) | outcomes rotated against the calls (200 draws): mean accuracy of the conditional rule | -                | -                | -                | -                |           0.501 | 0.504           | -             | -                                  | -                                  | -                                  | -                                  |
|                   | look-ahead control: agreement rule with features from 21 sessions ahead (weekly)      | -                | -                | -                | -                |           0.863 | -               | -             | -                                  | -                                  | -                                  | -                                  |

## 6. Round 3 incremental test of the delivered stream

| combo                     | period    |   sharpe |    t |
|:--------------------------|:----------|---------:|-----:|
| weak_signals+regime_trend | 2010-2026 |     0.56 | 2.35 |
| weak_signals+regime_trend | 2016-2026 |     0.64 | 2.13 |
| weak_signals+regime_trend | 2023-2026 |     0.36 | 0.71 |
| +regime_dependence        | 2010-2026 |     0.57 | 2.38 |
| +regime_dependence        | 2016-2026 |     0.64 | 2.14 |
| +regime_dependence        | 2023-2026 |     0.4  | 0.81 |

Daily-P&L correlation of the delivered stream with weak_signals 0.43, with regime_trend 0.63.

