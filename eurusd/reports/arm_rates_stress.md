# Arm H — rates_stress: market-implied policy expectations and stress measures

Code: `src/eurusd/arms/rates_stress.py` (`run(cost_pips=1.2)`, `fetch_data()`, `leak_checks()`, `incremental()`,
`signal_correlations()`; `python src/eurusd/arms/rates_stress.py` reproduces everything, ~40 s).
Results in `experiments/results/arms/`: `rates_stress_report.csv` (all 12 variants + 0.6-pip run; `variant`, `kind`,
`final`), `rates_stress_positions.parquet` (OOS `pos`, `fwd_bp`, `net_bp` of the final variant),
`rates_stress_weights.csv`, `rates_stress_leakchecks.csv`, `rates_stress_incremental.csv`, `rates_stress_pnl_corr.csv`,
`rates_stress_signal_corr.csv`, `rates_stress_all_variants_net_bp.parquet`. Log: `logs/rates_stress.log`.

## Verdict in one paragraph
The final variant (`tstat_linear`, picked by the pre-declared rule) has net Sharpe **0.49 / 0.32 / 0.31** for
2010-26 / 2016-26 / 2023-26 at 1.2 pips (t 2.04 / 1.06 / 0.61), and the three-way EW meta-combination is 0.664 vs
0.636 for the two-way on 2016-26. So every line of the round-3 bar is met **on paper, by margins that are inside
the noise** (0.32 vs the 0.30 threshold; +0.03 Sharpe on the combination; alpha against the two live streams
+0.42 bp/day with t 0.9; deflated-Sharpe p 0.36 for 12 variants). The part of the arm that works is the part that
is closest to the existing 2y-spread trend (final position 0.62 correlated with `d_spread2y_20`); the genuinely new
raw data (fed funds futures repricing, euro sovereign stress, VVIX) shows no stand-alone predictability. I do not
regard this as confirmed incremental information. Recommendation: do not add it as a third live arm on this evidence.

## New raw data (source, range, lag)
| file | source | range | lag used |
|---|---|---|---|
| `data/processed/cross/zq_fut_D1.parquet` | Yahoo chart API `ZQ=F` (CBOT 30-day fed funds futures, front continuous) | 2000-09-01..2026-11-10, 6,560 daily bars | one calendar day (`featstore._align_lagged`): a session closing on date D uses the bar stamped <= D-1 |
| `data/processed/cross/move_D1.parquet` | Yahoo `^MOVE` (ICE BofA Treasury implied vol) | 2002-11-12..2026-11-10, 5,934 | one calendar day |
| `data/processed/cross/vvix_D1.parquet` | Yahoo `^VVIX` (vol of VIX) | 2007-01-03..2026-11-10, 4,987 | one calendar day |
| `data/macro/ea_all_yield_curve.csv` | ECB Data Portal `YC.B.U2.EUR.4F.G_N_C.SV_C_YM.SR_3M/1Y/2Y/5Y/10Y` (all euro-area central-government issuers, Svensson spot) | 2004-09-06..2026-11-10, 5,671 | one calendar day (the ECB publishes day D's curve at noon CET on D+1, before the NY close of D+1) |

Already in the repo and used: `ea_aaa_yield_curve.csv`, `ea_overnight_rates.csv` (EONIA to 2021, EUR-STR from 2019-10),
`fred_DFEDTAR/DFEDTARL/DFEDTARU`, `fred_FEDFUNDS` (monthly), `fred_EFFR` (daily, 2022+). `^VIX` and `ZT=F` were already
in the store (`vix`, `zt_ret_*`) and were not re-fetched. **Not usable:** US real yield `DFII10` and breakeven `T10YIE`
exist only from 2022-01 in the mirrors (FRED itself is blocked), which is too short for a 2010-2026 walk-forward.
The in-progress Yahoo bar (session date = fetch date) is dropped at fetch time; it showed a 30 bp bad tick in `ZQ=F`.

Derived series and their caveats:
* `ZQ=F` rolls on the first business day of the month (verified on the March-2022 and December-2015 hikes), so the
  front contract is the current month and `100 - price` is the implied **average** effective rate of that month.
  It only sees a Fed move that falls inside the current month; nothing further out is available on Yahoo
  (back contracts have no history). Changes of the gap across a month roll partly reveal what the second contract
  already priced: stale, not look-ahead.
* Effective funds rate, calendar-daily: `fred_EFFR` from 2022-01-03; before that the target (mid of the range from
  2008-12-16) plus the previous month's gap between `FEDFUNDS` and that month's average target, clipped into the
  target range. Monthly-average error against `FEDFUNDS` 2003-2021: 2 bp mean absolute (worst month January 2009).
* Euro stress = all-issuer minus AAA spot yield, mean of the 2y and 10y points: 3 bp in 2005-07, 1.2-1.4 pp in
  2011-12, 0.3-0.6 pp since 2015. The AAA basket changes over time (downgrades), so the level has composition breaks.

## Signals (10) with economic sign priors, fixed before any P&L was computed
All are oriented so that positive = long EUR/USD over the next session (`fwd_1d`).
| signal | prior on the raw quantity | definition |
|---|---|---|
| `ffgap` | - | priced-in Fed move: (100 - ZQ) minus the status-quo month average of the effective rate (realised days so far + today's rate for the remaining days). Hike priced -> USD support |
| `ffgap_d5` | - | 5-session change of `ffgap` (hawkish repricing) |
| `ffgap_d20` | - | 20-session change of `ffgap` |
| `relpath_d20` | + | relative policy-path repricing: 20-session change of [(EA AAA 2y - EUR overnight) - (US 2y - fed effective)]; EUR overnight = EUR-STR, or EONIA - 8.5 bp before 2019-10, 10-day rolling median |
| `stress_lvl` | - | euro sovereign stress level (demeaned and scaled on the training window) |
| `stress_d20` | - | 20-session change of the stress spread |
| `spr_lowmove` | + | the store's `d_spread2y_20`, active only when `^MOVE` <= its training-window median |
| `spr_lowvvix` | + | `d_spread2y_20`, active only when `^VVIX` <= its training-window median |
| `curve_d20` | - | Ang-Chen term-spread change: 20-session change of (EA 10y-2y) - (US 10y-2y); relatively steepening EA curve -> short EUR |
| `carry_vol` | + | `policy_diff / rv_21d_bp` (carry to vol) |

Standardisation as in `arms/weak_signals.py`, training window only: divide by the training std (no demeaning except
`stress_lvl`), clip +-2, halve; gates use the training median of the gate column; missing = 0.
Positions are vol-scaled: `pos *= min(1, median_train(rv_21d_bp) / rv_21d_bp)`.

## Variants and selection rule
**12 variants, all reported below:** 10 single-signal variants (sign mapping: +-1 when |z| > training median of |z|)
and 2 combinations with the house method (weights = training-window univariate t-stat vs `fwd_1d`, clipped at 0):
`tstat_sign` (sign above the training median of |score|) and `tstat_linear` (clip(score / Q80_train), 20 % dead zone).
Additionally one 0.6-pip run of the final variant and five leak-check runs (not candidates). No ablation or re-tuning
was run after the results were seen; the only change after the first data inspection (before any P&L) was clipping
the pre-2022 effective-rate proxy into the target range.

**Selection rule (in the module docstring before the first run):** final = the combination variant with the higher
2010-2015 net Sharpe at 1.2 pips. Result: **`tstat_linear`** (0.74 vs 0.68).

## Single-signal table (net, 1.2 pips, 252 periods/year)
| variant     |   SR 2010-26 |     t |   SR 2016-26 |    t  |   SR 2023-26 |   t   |   SR 2010-15 |   SR 2016-22 |   active |
|:------------|-------------:|------:|-------------:|------:|-------------:|------:|-------------:|-------------:|---------:|
| ffgap       |         0.3  |  1.23 |         0.15 |  0.52 |        -0.51 | -1.02 |         0.52 |         0.4  |     0.31 |
| ffgap_d5    |        -0.18 | -0.73 |        -0.12 | -0.4  |        -0.43 | -0.86 |        -0.26 |         0.05 |     0.34 |
| ffgap_d20   |        -0.03 | -0.14 |        -0.01 | -0.02 |         0.02 |  0.05 |        -0.08 |        -0.02 |     0.35 |
| relpath_d20 |         0.31 |  1.31 |         0.2  |  0.67 |         0.26 |  0.51 |         0.51 |         0.17 |     0.52 |
| stress_lvl  |         0.02 |  0.08 |        -0.07 | -0.25 |        -0.14 | -0.29 |         0.08 |        -0.02 |     0.34 |
| stress_d20  |         0.11 |  0.46 |         0.16 |  0.53 |        -0.1  | -0.2  |         0.06 |         0.27 |     0.7  |
| spr_lowmove |         0.33 |  1.38 |         0.33 |  1.09 |        -0.27 | -0.53 |         0.35 |         0.49 |     0.68 |
| spr_lowvvix |        -0.27 | -1.12 |        -0.4  | -1.35 |        -0.67 | -1.33 |        -0.09 |        -0.23 |     0.3  |
| curve_d20   |         0.34 |  1.43 |         0.18 |  0.61 |         0.49 |  0.97 |         0.57 |         0.01 |     0.5  |
| carry_vol   |         0.2  |  0.82 |        -0.05 | -0.18 |        -0.13 | -0.26 |         0.9  |        -0.01 |     0.75 |

No single signal reaches |t| = 1.5 over 2010-26. Reading by idea:
1. **Priced-in Fed move.** The level has the prior's sign in 2010-22 (0.52 / 0.40) and the wrong sign in 2023-26
   (-0.51); the 5- and 20-session changes carry nothing. The front contract is too short-sighted to be a policy-path
   measure.
2. **Relative policy-path repricing** is positive in every sub-period (0.31, t 1.3) but is a close relative of the
   existing spread trend (correlation 0.53 with `d_spread2y_20`).
3. **Euro sovereign stress**: nothing. The level is flat (0.02); the 20-session change is weakly positive (0.11,
   t 0.5), i.e. "stress up -> EUR down" is not rejected but is not usable. It also overlaps with the live equity
   relative-momentum signal (0.34).
4. **Vol conditioning of the spread trend.** Low-MOVE gate: 0.33 over 2010-26 and 2016-26, negative in 2023-26; that
   is about what the ungated spread signal does (0.31 / 0.13 / 0.21 in `arm_weak_signals.md`), so the gate is not
   shown to add anything. Low-VVIX gate: wrong-signed throughout (-0.27, t -1.1) - the spread trend lost money
   in low-VVIX periods, the opposite of the prior.
5. **Curve (Ang-Chen change)**: 0.34 (t 1.4), positive in 2010-15 and 2023-26, zero in 2016-22; correlation 0.54
   with the spread trend because the 2y leg dominates.
6. **Carry-to-vol**: 0.90 in 2010-15, zero afterwards; its training t-stat was negative in every year so the
   combination never used it.

## Combinations
| variant      |   SR 2010-26 |    t |   SR 2016-26 |   t  |   SR 2023-26 |   t   |   SR 2010-15 |   SR 2016-22 |   active |
|:-------------|-------------:|-----:|-------------:|-----:|-------------:|------:|-------------:|-------------:|---------:|
| tstat_sign   |         0.37 | 1.56 |         0.16 | 0.54 |         0.11 |  0.22 |         0.68 |         0.19 |     0.5  |
| tstat_linear |         0.49 | 2.04 |         0.32 | 1.06 |         0.31 |  0.61 |         0.74 |         0.32 |     0.85 |

The two mappings of the same score differ by 0.16 Sharpe on 2016-26, which is itself a measure of how loosely the
result is pinned down.

### Final variant `tstat_linear`, per year (net; 1.2 pips headline, 0.6 pips sensitivity)
| period    |    n |   sharpe |      t |   mean_bp |   sum_bp |   active_frac |   sharpe_0.6pip |   t_0.6pip |   mean_bp_0.6pip |
|:----------|-----:|---------:|-------:|----------:|---------:|--------------:|----------------:|-----------:|-----------------:|
| 2010      |  260 |    2.489 |  2.528 |     5.898 | 1533.46  |         0.915 |           2.52  |      2.559 |            5.971 |
| 2011      |  260 |    0.245 |  0.249 |     0.657 |  170.851 |         0.935 |           0.271 |      0.275 |            0.725 |
| 2012      |  260 |    1.427 |  1.449 |     2.988 |  776.859 |         0.915 |           1.462 |      1.485 |            3.061 |
| 2013      |  259 |   -0.216 | -0.219 |    -0.356 |  -92.098 |         0.815 |          -0.174 |     -0.176 |           -0.287 |
| 2014      |  258 |    0.783 |  0.792 |     0.609 |  157.013 |         0.775 |           0.858 |      0.868 |            0.667 |
| 2015      |  259 |   -0.265 | -0.269 |    -0.593 | -153.473 |         0.861 |          -0.237 |     -0.24  |           -0.53  |
| 2016      |  259 |   -0.06  | -0.061 |    -0.093 |  -24.004 |         0.807 |          -0.012 |     -0.012 |           -0.019 |
| 2017      |  259 |    0.028 |  0.029 |     0.048 |   12.322 |         0.865 |           0.068 |      0.069 |            0.114 |
| 2018      |  260 |    0.604 |  0.614 |     1.004 |  261.071 |         0.85  |           0.649 |      0.66  |            1.079 |
| 2019      |  260 |    0.641 |  0.651 |     0.84  |  218.367 |         0.869 |           0.712 |      0.723 |            0.932 |
| 2020      |  260 |    0.55  |  0.558 |     0.917 |  238.53  |         0.754 |           0.591 |      0.6   |            0.987 |
| 2021      |  259 |    0.269 |  0.273 |     0.347 |   89.824 |         0.788 |           0.316 |      0.32  |            0.406 |
| 2022      |  260 |    0.306 |  0.311 |     0.74  |  192.443 |         0.912 |           0.355 |      0.36  |            0.857 |
| 2023      |  258 |   -0.625 | -0.632 |    -1.233 | -318.143 |         0.829 |          -0.544 |     -0.55  |           -1.072 |
| 2024      |  261 |   -0.501 | -0.51  |    -0.793 | -206.851 |         0.866 |          -0.43  |     -0.437 |           -0.679 |
| 2025      |  260 |    2.094 |  2.126 |     3.103 |  806.853 |         0.823 |           2.16  |      2.194 |            3.202 |
| 2026      |  220 |    0.79  |  0.739 |     0.947 |  208.277 |         0.787 |           0.885 |      0.827 |            1.059 |
| 2010-2026 | 4372 |    0.489 |  2.036 |     0.885 | 3871.3   |         0.846 |           0.536 |      2.231 |            0.97  |
| 2016-2026 | 2816 |    0.317 |  1.061 |     0.525 | 1478.69  |         0.832 |           0.374 |      1.251 |            0.619 |
| 2023-2026 |  999 |    0.307 |  0.612 |     0.491 |  490.137 |         0.828 |           0.384 |      0.764 |            0.612 |
| 2010-2015 | 1556 |    0.745 |  1.85  |     1.538 | 2392.61  |         0.87  |           0.777 |      1.932 |            1.605 |
| 2016-2022 | 1817 |    0.323 |  0.867 |     0.544 |  988.553 |         0.835 |           0.37  |      0.993 |            0.623 |

Deflated-Sharpe p (2010-26, 12 variants) = 0.36. 2010 alone is 40 % of the 2010-26 P&L. 2023 and 2024 are both
negative; 2023-26 is positive only because of 2025 (Sharpe 2.1). Mean |position| 0.45, turnover about 41 units a year.

### Walk-forward weights (t-stat weights, normalised)
|   test_year |   ffgap |   ffgap_d5 |   ffgap_d20 |   relpath_d20 |   stress_lvl |   stress_d20 |   spr_lowmove |   spr_lowvvix |   curve_d20 |   carry_vol |
|------------:|--------:|-----------:|------------:|--------------:|-------------:|-------------:|--------------:|--------------:|------------:|------------:|
|        2010 |    0.21 |       0.06 |        0    |          0.4  |         0    |         0    |          0    |          0    |        0.33 |           0 |
|        2013 |    0.17 |       0    |        0    |          0.24 |         0.04 |         0.17 |          0    |          0.15 |        0.23 |           0 |
|        2016 |    0.16 |       0    |        0    |          0.24 |         0.02 |         0.17 |          0    |          0.15 |        0.25 |           0 |
|        2019 |    0.17 |       0    |        0.04 |          0.21 |         0.01 |         0.17 |          0.15 |          0.06 |        0.2  |           0 |
|        2022 |    0.14 |       0.05 |        0.02 |          0.2  |         0.02 |         0.17 |          0.11 |          0.12 |        0.17 |           0 |
|        2026 |    0.16 |       0.07 |        0    |          0.21 |         0.01 |         0.17 |          0.1  |          0.07 |        0.21 |           0 |

(every year in `rates_stress_weights.csv`). About 60 % of the weight sits on the spread-trend relatives
(`relpath_d20`, `curve_d20`, the two gated spreads), 15-20 % on `ffgap`, about 17 % on `stress_d20`.

## Incremental value over the live combination
`eurusd.arms.meta.combine(..., "EW")` + `report_combo`, as prescribed:
| combo   | period    |    n |   sharpe |     t |   mean_bp |
|:--------|:----------|-----:|---------:|------:|----------:|
| EW_2way (weak_signals, regime_trend) | 2010-2026 | 4373 |    0.563 | 2.347 |     0.583 |
| EW_2way | 2013-2026 | 3593 |    0.622 | 2.347 |     0.709 |
| EW_2way | 2016-2026 | 2817 |    0.636 | 2.128 |     0.738 |
| EW_2way | 2023-2026 | 1000 |    0.356 | 0.708 |     0.42  |
| EW_3way (+ rates_stress) | 2010-2026 | 4373 |    0.556 | 2.315 |     0.478 |
| EW_3way | 2013-2026 | 3593 |    0.613 | 2.315 |     0.582 |
| EW_3way | 2016-2026 | 2817 |    0.664 | 2.221 |     0.639 |
| EW_3way | 2023-2026 | 1000 |    0.438 | 0.873 |     0.42  |

Daily-P&L correlation of this arm with the two live streams:
| period    |   corr_weak_signals |   corr_regime_trend |   corr_weak_vs_regime |
|:----------|--------------------:|--------------------:|----------------------:|
| 2010-2026 |                0.4  |                0.07 |                  0.27 |
| 2016-2026 |                0.33 |               -0.04 |                  0.33 |
| 2023-2026 |                0.28 |               -0.05 |                  0.33 |

Regression of this arm's daily net bp on the two live streams (post-hoc diagnostic, not a variant):
| period | alpha bp/day | t(alpha) | beta weak_signals | beta regime_trend | R2 |
|---|---:|---:|---:|---:|---:|
| 2010-2026 | 0.43 | 1.09 | 0.35 | -0.03 | 0.16 |
| 2016-2026 | 0.42 | 0.91 | 0.33 | -0.10 | 0.13 |
| 2023-2026 | 0.43 | 0.56 | 0.27 | -0.10 | 0.10 |

The three-way combination beats the two-way one on 2016-26 by 0.03 Sharpe (0.664 vs 0.636) and on 2023-26 by 0.08,
and is 0.01 worse on 2010-26 and 2013-26. The stream is not a copy of either live arm (correlation 0.33 with
weak_signals, about zero with positioning), which is why it diversifies a little, but its own alpha against them has
t 0.9. Formally the criterion "three-way beats two-way on 2016-2026" is met; statistically the two are
indistinguishable.

Correlation of the standardised new signals with the live combination's macro signals (full sample from 2004-10):
|             |   spread trend (d_spread2y_20) |   -fv_resid_z |   eq. rel. mom. |   cot_z52 |   -ret_252d |
|:------------|-------------:|---------:|------------:|----------:|-------------:|
| ffgap       |         0.21 |     0.04 |        0.06 |     -0.05 |        -0.13 |
| ffgap_d5    |         0    |     0.02 |        0.03 |      0    |         0.02 |
| ffgap_d20   |         0.08 |     0.02 |        0.04 |     -0.03 |         0.02 |
| relpath_d20 |         0.53 |     0.04 |        0.03 |      0.06 |         0.11 |
| stress_lvl  |         0.05 |     0.01 |        0.06 |     -0.04 |        -0.26 |
| stress_d20  |         0.06 |    -0.16 |        0.34 |      0.14 |        -0.04 |
| spr_lowmove |         0.49 |    -0.03 |       -0.05 |      0.12 |        -0.03 |
| spr_lowvvix |         0.65 |     0.02 |        0.01 |      0.09 |        -0.11 |
| curve_d20   |         0.54 |     0.02 |        0.05 |      0.11 |        -0.13 |
| carry_vol   |        -0.14 |    -0.05 |       -0.03 |     -0.02 |         0.15 |

The final variant's position series is 0.62 correlated with `d_spread2y_20` (same on 2016-26) and 0.40 with the
weak_signals position. The signals that are nearly orthogonal to the live set (`ffgap_d5`, `ffgap_d20`,
`stress_lvl`) are exactly the ones with no predictability.

## Leak checks (final variant, 1.2 pips)
| check                                   |   2010-2026 |   2016-2026 |   2023-2026 |   t 2010-26 |
|:----------------------------------------|------------:|------------:|------------:|------------:|
| shuffled_labels                         |        0.08 |        0.14 |        0.34 |        0.34 |
| features_shift_plus1                    |        0.59 |        0.52 |        0.56 |        2.47 |
| features_shift_plus5                    |        0.23 |        0.13 |       -0.02 |        0.95 |
| features_shift_plus21                   |       -0.51 |       -0.42 |       -1.03 |       -2.14 |
| features_shift_minus1_lookahead_control |        0.5  |        0.42 |        0.14 |        2.09 |

1. **Shuffled labels** (one global permutation of `fwd_1d`, used for fitting and evaluation): 0.08, t 0.3 -> ~0.
2. **Signals lagged one extra session**: 0.59, no collapse - expected for 20-session changes and levels, the same
   behaviour as in `arm_weak_signals.md`. At +5 sessions it halves (0.23) and at +21 it turns to -0.51 (t -2.1):
   the 20-session changes of the month before point the other way. That confirms the result depends on the signal's
   timing rather than on a constant bias, but a "wrong-lag" Sharpe of -0.5 is as large in size as the headline +0.49,
   which says the headline is not far outside what this pipeline produces by chance.
   Look-ahead control (signals of the NEXT session): 0.50, no jump. The inputs contain no EUR/USD price, and because
   every series is lagged a full calendar day, "one session ahead" is data stamped on the closing date itself.
3. **Label in disguise**: full-sample correlation of each standardised signal with `fwd_1d` is between -0.012 and
   +0.027 (table in `rates_stress_leakchecks.csv`); the largest weights go to `relpath_d20` (0.025), `curve_d20`
   (0.027), `ffgap` (0.020), `stress_d20` (0.022). Alignment was spot-checked on the March-2022 hike: the session
   closing 2022-03-17 22:00 UTC carries the `ZQ=F` gap and `^MOVE` value stamped 2022-03-16.

## What helped, what did not, what is suspicious
* Helped (weakly): expressing the rate-differential trend as a path measure (`relpath_d20`) and as a relative curve
  change (`curve_d20`). Both are re-expressions of information already in the store.
* Did not help: fed funds futures repricing (changes), euro sovereign stress (level and change), VVIX conditioning
  (wrong sign), carry-to-vol after 2015. MOVE conditioning is not distinguishable from the ungated spread trend.
* Suspicious / caveats: (a) every pass is by a hair and t-stats on 2016-26 are about 1; (b) 2010 carries 40 % of
  the P&L, 2025 carries 2023-26; (c) the sign-mapped twin of the final variant gives 0.16 on 2016-26; (d) the lag
  profile is non-monotonic with a significant negative at 21 sessions; (e) the fed-funds signal sees only the
  current month - a proper test of "priced-in policy path" needs the 2nd-6th ZQ contracts or OIS, which are not
  reachable from here; (f) pre-2022 the effective funds rate is a proxy; (g) the AAA/all-issuer spread has
  composition breaks.
* Not run (would exceed the declared 12 variants): leave-one-out ablation, adding the new signals to the
  weak_signals signal set, other lookbacks.
