# Arm C — weak_signals: forecast combination of many weak economic signals

Code: `src/eurusd/arms/weak_signals.py` (`run(cost_pips=1.2)`). Results: `experiments/results/arms/weak_signals_report.csv`
(all variants + leave-one-out + cost sensitivity, `variant` column, `final` flag), `weak_signals_positions.parquet`
(OOS positions of the final variant: `pos`, `fwd_bp`, `net_bp`), `weak_signals_weights.csv` (walk-forward weights),
`weak_signals_leakchecks.csv`, `weak_signals_single_signals.csv` (post-hoc diagnostic). Log: `weak_signals.log`.

## Idea
Round 1 found a dozen EUR/USD effects whose sign is stable but which are individually insignificant. Single-asset FX
edges become usable only by combination: if k weakly correlated signals each carry a little information, the combined
Sharpe grows roughly with sqrt(k). Every effect is expressed as a standardised daily signal (statistics from the
training window only), oriented so that its ECONOMIC PRIOR says "positive -> long EUR/USD over the next NY-close
session" (label `fwd_1d`), and the signals are combined walk-forward (yearly expanding window, `eurusd.wf`).
The London-hours short is not expressible as a daily position and was left out, as instructed.

## Signals (14), priors fixed before any result was looked at
| signal   | prior sign on raw column   | kind   | definition                                                                                                                                                                           |
|:---------|:---------------------------|:-------|:-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| fomc     | +                          | bin    | +1 on the session before a scheduled FOMC statement (h_to_fomc < 30h): FOMC-day long (round-1 H08)                                                                                   |
| cot      | +                          | cont   | cot_z52, CFTC non-commercial net position z-score: follow the positioning trend (H31)                                                                                                |
| spread   | +                          | cont   | d_spread2y_20, 20-day change of the EA-US 2y spread: long EUR if the spread rose (C10)                                                                                               |
| mom63    | +                          | cont   | ret_63d, 3-month time-series momentum (H18)                                                                                                                                          |
| mom21    | +                          | cont   | ret_21d, 1-month time-series momentum (H19)                                                                                                                                          |
| fv       | -                          | cont   | -fv_resid_z, mean reversion of the 2y-spread fair-value residual (F01)                                                                                                               |
| gap      | -                          | bin    | fade a large weekend gap (|gap| > ATR14/5) on the Monday-session row, i.e. over Tuesday (H15, 2-day hold)                                                                            |
| tom      | -                          | bin    | -1 over the turn of the month (bd_to_end <= 1 or bd_from_start <= 3): short EUR/USD T-1 -> T+4 (C04)                                                                                 |
| usdmom   | -                          | cont   | -usd_factor_20, dollar-factor momentum (USD strong vs 5 majors over 20d -> short EUR/USD)                                                                                            |
| vix      | +                          | level  | VIX level (demeaned): round-1 V04 was consistently NEGATIVE for 'long when VIX<20 / short >30', so the kept sign is long EUR/USD when VIX is high (contrary to the risk-on textbook) |
| eqrel    | -                          | cont   | -spx_minus_sx5e_20, US-vs-EA equity relative momentum: US outperformance -> flows to USD (F04 sign)                                                                                  |
| mom252   | -                          | cont   | -ret_252d, 12-month TSMOM expected negative/weak (H17)                                                                                                                               |
| season   | +                          | bin    | +1 when the next session closes in December, -1 in May (C03)                                                                                                                         |
| dow      | +                          | bin    | -1 when the next session closes on Monday, +1 on Friday (Seasonax day-of-week, C01)                                                                                                  |

Standardisation: `cont` signals are divided by the training-window std (no demeaning: the raw sign is the economic
content), clipped to +-2 and halved to [-1, 1]; `level` (VIX) is demeaned with the training mean first; `bin` signals
are already in {-1, 0, +1}. A missing signal counts as 0. Note the prior for `vix` is the direction round 1 observed
(V04 "long when VIX<20 / short >30" was negative in every sub-period), i.e. long EUR/USD when VIX is high, which is the
opposite of the risk-on textbook; `dow` and `season` are the Seasonax / round-1 directions.

## Combination methods and position mapping
Weights are fitted on the training window of each test year (rows whose `label_end_1d` < Y-01-01) and normalised to
sum to 1 in absolute value:
* `equal`: equal weights with prior signs (uses no label information at all).
* `ridge`: ridge regression of `fwd_1d` on the 14 standardised signals, alpha = n_train (fixed, strong shrinkage).
* `nnls`: sign-restricted least squares, weights >= 0 after the prior orientation (scipy `nnls`); equal weights if all 0.
* `tstat`: weight_i = max(t_i, 0), t_i the training-window univariate t-stat of signal i vs `fwd_1d`.

Score -> position (training-quantile thresholds): `linear`: pos = clip(score / Q80_train(|score|), -1, 1), zero
inside the training 20 % dead zone; `sign`: pos = sign(score) when |score| > training median of |score|, else 0.
Both are then vol-scaled: pos *= min(1, median_train(rv_21d_bp) / rv_21d_bp) (constant risk, no leverage above 1).

**Variants run: 8** (4 methods x 2 mappings). Plus 14 leave-one-out re-runs of the final variant, 1 cost-sensitivity
run and 5 leak-check runs (not candidates). No parameter was tuned on any test year; 2023-2026 was never looked at
separately.

**Selection rule (declared before results):** the final variant is the one with the highest 2010-2015 walk-forward
NET Sharpe at 1.2 pips. Result of the rule: **`tstat_sign`**.

## All variants (net, 1.2 pips, one decision per session, periods_per_year = 252)
| variant      |   SR 2010-2026 |   SR 2016-2026 |   SR 2023-2026 |   SR 2010-2015 |   SR 2016-2022 |   t_2010_2026 |   active_frac |
|:-------------|---------------:|---------------:|---------------:|---------------:|---------------:|--------------:|--------------:|
| equal_linear |           0.5  |           0.19 |           0.3  |           0.94 |           0.13 |          2.09 |          0.79 |
| equal_sign   |           0.42 |           0.18 |           0.22 |           0.76 |           0.15 |          1.75 |          0.49 |
| nnls_linear  |           0.65 |           0.64 |           0.43 |           0.68 |           0.77 |          2.72 |          0.82 |
| nnls_sign    |           0.6  |           0.59 |           0.3  |           0.63 |           0.75 |          2.5  |          0.54 |
| ridge_linear |           0.71 |           0.6  |           0.54 |           0.87 |           0.63 |          2.94 |          0.81 |
| ridge_sign   |           0.56 |           0.41 |           0.43 |           0.78 |           0.41 |          2.35 |          0.5  |
| tstat_linear |           0.69 |           0.6  |           0.5  |           0.84 |           0.66 |          2.89 |          0.81 |
| tstat_sign   |           0.68 |           0.43 |           0.27 |           1.04 |           0.52 |          2.82 |          0.5  |

## Final variant `tstat_sign`: per-year record (net; 1.2 pips headline, 0.6 pips sensitivity)
| period    |    n |   sharpe_1.2pip |   t_1.2pip |   mean_bp_1.2pip |   sum_bp_1.2pip |   active_frac |   sharpe_0.6pip |   t_0.6pip |   mean_bp_0.6pip |   sum_bp_0.6pip |
|:----------|-----:|----------------:|-----------:|-----------------:|----------------:|--------------:|----------------:|-----------:|-----------------:|----------------:|
| 2010      |  260 |           2.522 |      2.562 |            8.133 |        2114.5   |         0.712 |           2.55  |      2.59  |            8.223 |        2137.89  |
| 2011      |  260 |           0.879 |      0.892 |            2.609 |         678.336 |         0.669 |           0.92  |      0.934 |            2.731 |         710.002 |
| 2012      |  260 |           1.935 |      1.966 |            4.161 |        1081.76  |         0.431 |           2.033 |      2.065 |            4.368 |        1135.72  |
| 2013      |  259 |          -0.198 |     -0.201 |           -0.355 |         -92.047 |         0.402 |          -0.08  |     -0.081 |           -0.144 |         -37.267 |
| 2014      |  258 |           0.878 |      0.888 |            1.476 |         380.923 |         0.496 |           0.992 |      1.004 |            1.667 |         430.202 |
| 2015      |  259 |          -0.201 |     -0.203 |           -0.53  |        -137.357 |         0.456 |          -0.146 |     -0.148 |           -0.385 |         -99.775 |
| 2016      |  259 |           0.051 |      0.052 |            0.087 |          22.583 |         0.274 |           0.119 |      0.121 |            0.204 |          52.877 |
| 2017      |  259 |           0.609 |      0.617 |            0.913 |         236.349 |         0.286 |           0.694 |      0.703 |            1.04  |         269.427 |
| 2018      |  260 |          -0.127 |     -0.129 |           -0.302 |         -78.527 |         0.7   |          -0.069 |     -0.07  |           -0.163 |         -42.472 |
| 2019      |  260 |           0.865 |      0.879 |            1.022 |         265.636 |         0.323 |           1.004 |      1.02  |            1.185 |         308.053 |
| 2020      |  260 |           1.011 |      1.027 |            1.837 |         477.687 |         0.435 |           1.086 |      1.103 |            1.974 |         513.303 |
| 2021      |  259 |           0.66  |      0.669 |            1.046 |         270.915 |         0.568 |           0.72  |      0.729 |            1.141 |         295.409 |
| 2022      |  260 |           0.857 |      0.87  |            2.234 |         580.943 |         0.685 |           0.89  |      0.904 |            2.322 |         603.595 |
| 2023      |  258 |           0.047 |      0.047 |            0.113 |          29.178 |         0.609 |           0.106 |      0.107 |            0.255 |          65.8   |
| 2024      |  261 |          -0.252 |     -0.257 |           -0.469 |        -122.287 |         0.586 |          -0.201 |     -0.205 |           -0.374 |         -97.568 |
| 2025      |  260 |           0.74  |      0.752 |            1.42  |         369.217 |         0.438 |           0.797 |      0.81  |            1.531 |         398.087 |
| 2026      |  220 |           0.738 |      0.689 |            1.108 |         243.698 |         0.502 |           0.807 |      0.754 |            1.211 |         266.48  |
| 2010-2026 | 4372 |           0.678 |      2.825 |            1.446 |        6321.51  |         0.504 |           0.741 |      3.088 |            1.58  |        6909.77  |
| 2016-2026 | 2816 |           0.427 |      1.427 |            0.815 |        2295.39  |         0.491 |           0.49  |      1.637 |            0.935 |        2632.99  |
| 2023-2026 |  999 |           0.265 |      0.528 |            0.52  |         519.808 |         0.535 |           0.323 |      0.643 |            0.633 |         632.799 |
| 2010-2015 | 1556 |           1.042 |      2.589 |            2.587 |        4026.11  |         0.528 |           1.107 |      2.75  |            2.749 |        4276.77  |
| 2016-2022 | 1817 |           0.52  |      1.395 |            0.977 |        1775.59  |         0.467 |           0.585 |      1.571 |            1.101 |        2000.19  |

2010-2026 net Sharpe 0.68 (t 2.82, deflated-Sharpe p = 0.064 for 6 arms);
2016-2026 0.43 (t 1.43); 2023-2026 0.27 (t 0.53).
At 0.6 pips: 0.74 / 0.49 / 0.32.
The success bar (2010-2026 > 0.4, 2016-2026 > 0.3, 2023-2026 >= 0 at 1.2 pips) is met, but the 2016-2026 t-stat is
only 1.4 and 2023-2026 is 0.5: the edge is concentrated in 2010-2012 and 2019-2022, 2013/2015/2018/2024 are flat or
slightly negative. Mean net P&L is ~1.4 bp per session with ~50 % of sessions active.

## Leave-one-out ablation of the final variant (drop one signal, re-run walk-forward, 1.2 pips)
| ablation    |   2010-2026 |   2016-2026 |   2023-2026 |   t_2010_2026 |   dSR_2010_2026_vs_full |
|:------------|------------:|------------:|------------:|--------------:|------------------------:|
| drop cot    |        0.45 |        0.39 |        0.66 |          1.89 |                   -0.23 |
| drop dow    |        0.72 |        0.46 |        0.24 |          3    |                    0.04 |
| drop eqrel  |        0.53 |        0.43 |        0.19 |          2.22 |                   -0.15 |
| drop fomc   |        0.75 |        0.47 |        0.43 |          3.13 |                    0.07 |
| drop fv     |        0.67 |        0.43 |        0.21 |          2.78 |                   -0.01 |
| drop gap    |        0.68 |        0.39 |        0.3  |          2.83 |                    0    |
| drop mom21  |        0.59 |        0.45 |        0.28 |          2.44 |                   -0.09 |
| drop mom252 |        0.39 |        0.37 |        0.16 |          1.63 |                   -0.29 |
| drop mom63  |        0.68 |        0.43 |        0.26 |          2.84 |                    0    |
| drop season |        0.49 |        0.37 |        0.3  |          2.06 |                   -0.19 |
| drop spread |        0.54 |        0.52 |        0.42 |          2.26 |                   -0.14 |
| drop tom    |        0.64 |        0.44 |        0.29 |          2.65 |                   -0.04 |
| drop usdmom |        0.71 |        0.4  |        0.19 |          2.94 |                    0.03 |
| drop vix    |        0.68 |        0.43 |        0.27 |          2.82 |                    0    |

Signals whose removal hurts most over 2010-2026: `mom252` (-0.29), `cot` (-0.23), `season` (-0.19), `eqrel` (-0.15),
`spread` (-0.14), `mom21` (-0.09). Removing `fomc`, `dow` or `usdmom` HELPS (+0.07, +0.04, +0.03): those carry no
information in the combination (dow is in fact wrongly signed out of sample, see the single-signal table; the t-stat
weighting learns this and drives its weight to 0 by 2025). Over 2016-2026 the ranking is similar (`mom252`, `season`,
`cot`, `gap`, `usdmom` hurt most when dropped, -0.03 to -0.06) but dropping `spread` would have HELPED (+0.09): the
spread signal's contribution is a 2010-2015 phenomenon. Over 2023-2026 the picture is noisier (dropping `cot`,
`fomc` or `spread` would have helped by +0.15 to +0.40; dropping `mom252`, `eqrel`, `usdmom` hurts most, -0.08 to -0.11). So the combination is carried by
the slow macro / flow signals: 12-month momentum (negative), CFTC positioning trend, December/May seasonality,
US-vs-EA equity relative momentum and the 20-day 2y-spread change, and not by the calendar/event signals.

## Single-signal records (post-hoc diagnostic, NOT used for selection; sign mapping, one signal alone, 1.2 pips)
| signal alone (prior sign)   |   2010-2026 |   2016-2026 |   2023-2026 |   t_2010_2026 |   active_frac |
|:----------------------------|------------:|------------:|------------:|--------------:|--------------:|
| cot                         |        0.44 |        0.47 |        0.07 |          1.84 |          0.57 |
| dow                         |       -0.71 |       -1.05 |       -1.39 |         -2.95 |          0.4  |
| eqrel                       |        0.4  |        0.37 |        0.7  |          1.66 |          0.76 |
| fomc                        |        0.09 |        0.27 |        0.14 |          0.37 |          0.06 |
| fv                          |       -0    |        0.14 |        0.21 |         -0.02 |          0.59 |
| gap                         |       -0.13 |       -0.12 |       -0.66 |         -0.54 |          0.03 |
| mom21                       |       -0.1  |       -0.11 |        0.08 |         -0.4  |          0.41 |
| mom252                      |        0.33 |        0.3  |        0.78 |          1.35 |          0.4  |
| mom63                       |        0.14 |        0.18 |       -0.07 |          0.6  |          0.42 |
| season                      |        0.62 |        0.31 |        0.24 |          2.59 |          0.17 |
| spread                      |        0.31 |        0.13 |        0.21 |          1.29 |          0.51 |
| tom                         |        0.09 |       -0.19 |        0.04 |          0.39 |          0.23 |
| usdmom                      |       -0.05 |       -0.24 |       -0.34 |         -0.22 |          0.43 |
| vix                         |       -0.13 |        0    |        0.33 |         -0.55 |          0.44 |

Individually almost nothing is significant (|t| < 2 except `season` +2.6 and `dow` -3.0, the latter with the WRONG
sign relative to the Seasonax prior), which is exactly the premise of the arm; the combination's t of 2.8 is what the
sum of weak signals buys. The signals are weakly correlated except the momentum block (`mom63`, `mom21`, `usdmom`,
`cot`, `-fv`: pairwise 0.3-0.8), which is why the data-weighted methods beat equal weights after 2015.

## Walk-forward weights of the final variant over time (t-stat weights, normalised to sum 1)
|   test_year |   fomc |   cot |   spread |   mom63 |   mom21 |    fv |   gap |   tom |   usdmom |   vix |   eqrel |   mom252 |   season |   dow |
|------------:|-------:|------:|---------:|--------:|--------:|------:|------:|------:|---------:|------:|--------:|---------:|---------:|------:|
|        2010 |  0.201 | 0.121 |    0.196 |   0     |   0.059 | 0     | 0.096 | 0.059 |    0.007 | 0     |   0.025 |    0.15  |    0.022 | 0.063 |
|        2011 |  0.13  | 0.105 |    0.164 |   0.004 |   0.098 | 0.003 | 0.096 | 0.014 |    0.049 | 0     |   0.085 |    0.117 |    0.069 | 0.064 |
|        2012 |  0.118 | 0.111 |    0.149 |   0.002 |   0.07  | 0.043 | 0.073 | 0.046 |    0.033 | 0     |   0.092 |    0.126 |    0.055 | 0.082 |
|        2013 |  0.116 | 0.107 |    0.143 |   0     |   0.065 | 0.047 | 0.065 | 0.058 |    0.028 | 0     |   0.097 |    0.108 |    0.082 | 0.083 |
|        2014 |  0.105 | 0.094 |    0.144 |   0     |   0.056 | 0.048 | 0.058 | 0.073 |    0.021 | 0     |   0.111 |    0.115 |    0.093 | 0.083 |
|        2015 |  0.09  | 0.115 |    0.151 |   0.001 |   0.064 | 0.024 | 0.056 | 0.079 |    0.038 | 0     |   0.126 |    0.106 |    0.087 | 0.064 |
|        2016 |  0.096 | 0.124 |    0.174 |   0.018 |   0.06  | 0.013 | 0.05  | 0.066 |    0.028 | 0     |   0.119 |    0.082 |    0.116 | 0.054 |
|        2017 |  0.111 | 0.126 |    0.167 |   0.013 |   0.046 | 0.022 | 0.065 | 0.025 |    0.013 | 0     |   0.155 |    0.091 |    0.127 | 0.039 |
|        2018 |  0.126 | 0.149 |    0.159 |   0.018 |   0.042 | 0.005 | 0.057 | 0.025 |    0.003 | 0     |   0.155 |    0.09  |    0.116 | 0.055 |
|        2019 |  0.116 | 0.142 |    0.171 |   0.02  |   0.044 | 0.001 | 0.056 | 0.024 |    0.013 | 0     |   0.142 |    0.098 |    0.132 | 0.042 |
|        2020 |  0.129 | 0.143 |    0.171 |   0.017 |   0.042 | 0.004 | 0.057 | 0.022 |    0.009 | 0     |   0.137 |    0.095 |    0.139 | 0.036 |
|        2021 |  0.123 | 0.146 |    0.162 |   0.02  |   0.035 | 0     | 0.079 | 0.017 |    0.006 | 0     |   0.166 |    0.09  |    0.136 | 0.021 |
|        2022 |  0.128 | 0.152 |    0.17  |   0.014 |   0.031 | 0.011 | 0.07  | 0.024 |    0.004 | 0     |   0.156 |    0.095 |    0.131 | 0.013 |
|        2023 |  0.119 | 0.166 |    0.15  |   0.02  |   0.026 | 0.018 | 0.077 | 0.036 |    0.009 | 0     |   0.166 |    0.076 |    0.121 | 0.016 |
|        2024 |  0.126 | 0.154 |    0.138 |   0.013 |   0.024 | 0.026 | 0.08  | 0.056 |    0.007 | 0     |   0.165 |    0.079 |    0.129 | 0.003 |
|        2025 |  0.133 | 0.156 |    0.141 |   0.013 |   0.022 | 0.038 | 0.072 | 0.05  |    0.011 | 0     |   0.169 |    0.08  |    0.115 | 0     |
|        2026 |  0.12  | 0.159 |    0.156 |   0.023 |   0.019 | 0.038 | 0.067 | 0.034 |    0.009 | 0.007 |   0.17  |    0.079 |    0.117 | 0     |

The weights are stable: `spread`, `eqrel`, `cot`, `fomc`, `season` and `mom252` take ~75 % of the weight throughout;
`vix` is 0 in every year but the last (its training t-stat is negative under the declared prior, i.e. the textbook
risk-on sign would have been right in-sample), `fv`, `mom63` and `usdmom` are near zero (they are crowded out by their
correlated siblings `cot`/`mom21`), and `dow` decays from 0.06 to 0.

## Leak checks
| check                                   |   2010-2026 |   2016-2026 |   2023-2026 |   t_2010_2026 |
|:----------------------------------------|------------:|------------:|------------:|--------------:|
| features_shift_minus1_lookahead_control |        2.42 |        2.26 |        2.53 |         10.1  |
| features_shift_plus1                    |        0.87 |        0.73 |        0.58 |          3.63 |
| features_shift_plus21                   |        0.81 |        0.7  |        0.46 |          3.38 |
| features_shift_plus5                    |        0.34 |        0.23 |        0.38 |          1.43 |
| shuffled_labels                         |        0.14 |       -0    |       -0.25 |          0.6  |

Full-sample correlation of each standardised signal with `fwd_1d`:
| signal   |   corr_with_fwd_1d |
|:---------|-------------------:|
| fomc     |             0.0261 |
| cot      |             0.0343 |
| spread   |             0.0342 |
| mom63    |             0.0044 |
| mom21    |             0.0042 |
| fv       |             0.0087 |
| gap      |             0.0109 |
| tom      |             0.0091 |
| usdmom   |             0.0011 |
| vix      |             0.0029 |
| eqrel    |             0.0386 |
| mom252   |             0.0176 |
| season   |             0.0259 |
| dow      |            -0.0029 |

1. **Shuffled labels** (one global permutation of `fwd_1d`, used for fitting AND evaluation): 2010-2026 Sharpe 0.14,
   t 0.6; 2016-2026 0.00 -> ~0 as required.
2. **Features lagged by one extra session**: the result does NOT collapse (SR 0.87 at lag 1, 0.34 at lag 5, 0.81 at
   lag 21). This is expected for a set of 20-250 day signals (their value barely changes from one day to the next),
   so the 1-day shift is a weak test here; it does show that the edge is not an event-day / precise-timing effect, and
   the lag-1 improvement is consistent with a 1-day reversal component of EUR/USD that is not in the signal set.
   The fast signals (fomc, gap, tom, dow, season) are mis-timed at lag 1 and they are also the ones the ablation says
   carry nothing (except season). The non-monotonic lag profile (0.87 / 0.34 / 0.81) says the edge is noisy and slow;
   it should be read as a caution about how robust the ~0.7 Sharpe is, not as evidence of a leak.
   Look-ahead control: shifting the signals the other way (using the next session's signals) gives SR 2.4, t 10, so
   the harness would have exposed a genuine look-ahead loudly; the final 0.68 is far from that.
3. **Top features vs label-in-disguise**: the largest weights are `spread`, `eqrel`, `cot`, `fomc`, `season`,
   `mom252`; their full-sample correlations with `fwd_1d` are 0.03-0.04 (max 0.039 for `eqrel`), nothing near a label.
   All inputs are feature-store columns lagged as in `featstore.build_daily` (macro lagged one calendar day, COT +6
   days, calendar/event clocks deterministic); the only columns built here from `shift(-1)` are the NEXT session's
   weekday/month (calendar, known in advance). `gap` uses the previous session's ATR for its threshold.

## What helped, what did not, and what is suspicious
* Helped: combining. No single signal passes |t| > 2 with the right sign, the combination gives t 2.8 (2010-2026).
  Data-driven weights (ridge / nnls / tstat) beat equal prior weights after 2015 (2016-2026 SR 0.4-0.6 vs 0.2) because
  they down-weight the wrongly-signed `dow` and the redundant momentum block.
* Carried by: `mom252` (negative 12-month momentum), `cot` (follow positioning), `season` (Dec long / May short),
  `eqrel` (US-vs-EA equity momentum -> USD), `spread` (20d 2y-spread change). Not by: `fomc`, `dow`, `usdmom`, `vix`.
* Did not help: `dow` (wrong sign OOS), `vix` (zero weight), `gap` (3 % active, negative alone), `fv`, `mom63`.
* Suspicious / caveats: (a) 2010-2012 contribute 60 % of the 2010-2026 P&L; (b) the lag test does not collapse, so the
  edge is a slow drift exposure (negative 12m momentum + positioning + seasonality) rather than something with precise
  timing; (c) the deflated-Sharpe p is 0.064 with only 6 arms declared, and 8 variants were run inside the arm;
  (d) 2023-2026 Sharpe 0.27 with t 0.5 is indistinguishable from 0; (e) `season` is a 2-month-a-year signal with 16 %
  activity and `t` 2.6 alone, the kind of thing that can be a fluke despite its round-1 pedigree.
