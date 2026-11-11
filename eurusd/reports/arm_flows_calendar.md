# Arm M — flows_calendar: predictable non-informational flows on known dates

Code: `src/eurusd/arms/flows_calendar.py` (`run(cost_pips=1.2)`; `python src/eurusd/arms/flows_calendar.py` rebuilds every file below in ~20 s).
Results in `experiments/results/arms/`: `flows_calendar_positions.parquet` (OOS positions of the final variant: `pos`, `fwd_bp`, `net_bp`),
`flows_calendar_report.csv` (12 candidates + benchmarks/diagnostics + 0.6-pip runs; `variant`, `kind`, `final`), `_hit_rates.csv`,
`_month_end_table.csv`, `_month_stability.csv`, `_month_joint_test.csv`, `_season_legs.csv`, `_season_wf_table.csv`, `_fix_follow_by_day.csv`,
`_fix_decisions.parquet` (one row per month-end decision, all four fix streams), `_descriptives.csv`, `_imm_positioning.csv`, `_incremental.csv`,
`_pnl_corr.csv`, `_replace_test.csv`, `_leakchecks.csv`, `_all_variants_net_bp.parquet`. Log: `logs/flows_calendar.log`.

## Verdict in five lines
* **The arm fails.** The final variant by the pre-declared rule (best 2010-2015 net Sharpe) is `blackout_trend`: net Sharpe
  0.17 / -0.25 / 0.11 for 2010-26 / 2016-26 / 2023-26 (t 0.72 / -0.85 / 0.21), hit rate 50 %; adding it to the live pair LOWERS the
  combination (0.36 / 0.42 / 0.35 vs 0.56 / 0.64 / 0.36). Do not stack it.
* **Equity-conditioned month-end rebalancing is not there**: sign(S&P MTD - Euro Stoxx MTD) has no predictive value for EUR/USD over the last
  1-3 sessions (Sharpe 0.03, -0.12), nor from 15:00 into the 16:00 fix on the last day (-0.28), nor at quarter-ends, nor with a rest-of-world basket.
* **One flow effect is real, but it is the round-1 one and equities do not explain it**: on the last business day the 15:00-15:45 London move
  continues over 15:45-16:00: +3.1 bp gross per month-end (t 3.4, 2010-26, positive in all four eras, hit 57 %), **zero on every other day**
  (-0.17 bp, n 3,661). After a 1.2-pip round trip: Sharpe 0.56 / 0.60 / 0.90 (t 2.3), 11.6 decisions a year, uncorrelated with the live arms
  (0.01 / 0.04), three-way EW 0.78 / 0.82 / 0.63. My equity-agreeing subset (`fix_follow_reb`, 0.48 / 0.47 / 0.84) is no better than the
  unconditional rule and a STALE equity sign conditions it just as well, so the conditioning is noise.
* **"season" is one supported month and one lucky month**: December long has the same sign in four eras (1975-2026 pooled +123 bp, t 2.9,
  31/51 up; +92 bp, 7/10 up after the rule was chosen); May short is entirely 2010-2015 (6/6, +366 bp), wrong-signed 1999-2009 and +6 bp since 2016.
  Jointly the 12 months show no seasonality (ANOVA p 0.40; walk-forward shrinkage factor 0.00 in every test year), 4 of 12 months keep their sign
  across the three eras against 3 expected by chance.
* IMM roll, option expiry, holidays, year-end week, central-bank blackouts: nothing. Treasury settlement dates: skipped (no reachable date list).

## Priors, stated before results (summary of the module docstring, which was written first)
| # | flow | prior | traded as |
|---|---|---|---|
| P1 | month-end hedge rebalancing | US equities outperform euro-area equities MTD -> foreign holders of US assets are under-hedged, must sell USD at month-end -> **long EUR/USD**; larger at quarter/year-ends | `reb_d3`, `reb_d1`, `reb_d3_lin`, `fix_reb`, `fix_follow_reb` |
| P2 | new-month reversal | flow pressure carries no information -> partly reverses in the first sessions of the month | `nm_rev_sig`, `nm_rev_px` |
| P3 | seasonality | Dec long (year-end repatriation / window dressing), May short (European dividend season, sell-in-May), Jan short (reversal); March (Japan FY-end) and April (US tax date) no clear EUR/USD sign. Test agnostic: all 12 months, shrinkage to zero | `season_js` |
| P4 | IMM roll | unrolled speculative positions must be closed before the last trading day -> flow AGAINST net spec position | `imm_fade_cot` |
| P5 | holidays | positions squared before a long weekend -> last week's move partly reverses | `hol_square` |
| P6 | CB blackout | no policy communication -> the 21-day trend persists | `blackout_trend` |
| P7 | Treasury refunding / settlement | foreign buyers must fund in USD | **skipped**: `api.fiscaldata.treasury.gov` and `treasurydirect.gov` are unreachable through the proxy, no clean date list |

## Definitions
Daily variants: feature store (`features_daily.parquet`), label `fwd_1d`, the fixed `wf.py` loop (test years 2010-2026), cost = harness
convention (1.2 pips per unit turnover, i.e. 2.4 pips for an in-and-out trade). `T` = last session of the month (`bd_to_end == 0`).
`rel` = MTD log return of the S&P 500 minus MTD log return of the Euro Stoxx 50 (local currency, bp), each from its own last close of the
previous month, using closes stamped <= session close date - 1 calendar day (`featstore._align_lagged` convention), available from 2007-04.

| # | variant | rule |
|---|---|---|
| 1 | `reb_d3` | sign(`rel`) fixed at the close of T-3, held over the last 3 sessions (T-2, T-1, T) |
| 2 | `reb_d1` | sign(`rel`) at the close of T-1, held over session T |
| 3 | `reb_d3_lin` | as 1, size-weighted: clip(`rel` / Q80_train(\|`rel`\| at T-3 decisions), -1, 1) |
| 4 | `nm_rev_sig` | -sign(`rel` at the close of T) over the first 2 sessions of the new month |
| 5 | `nm_rev_px` | -sign(return of sessions T-2..T) over the first 2 sessions of the new month |
| 6 | `season_js` | for test year Y: month-of-year t-stats of ECB-fixing monthly returns 1999..Y-1, positive-part James-Stein factor B = max(0, 1 - 10 v / sum t^2), position = clip(B t_m / 2, -1, 1) |
| 7 | `imm_fade_cot` | -sign(`cot_z52`) in the 5 sessions ending on the IMM last trading day (Monday before the 3rd Wednesday of Mar/Jun/Sep/Dec) |
| 8 | `hol_square` | -sign(`ret_5d`) over the session before a US federal holiday, Good Friday or a TARGET holiday |
| 9 | `blackout_trend` | sign(`ret_21d`) while 24h < `h_to_fomc` <= 240h or 24h < `h_to_ecb` <= 168h (never held through the announcement session) |
| 10 | `flows_core` | clip(`reb_d3` + `nm_rev_sig` + `season_js`, -1, 1): the proposed replacement of `tom` + `season` |
| 11 | `fix_reb` | M5: last weekday of the month, enter 15:00 London, exit 16:00, direction sign(`rel` through T-1) |
| 12 | `fix_follow_reb` | M5: last weekday, follow the 15:00-15:45 move over 15:45-16:00 only if it agrees with sign(`rel`) |

Intraday: `EURUSD_M5.parquet`, London local time via `tz_convert("Europe/London")` (15:00 London = 14:00 UTC in BST, checked), price at time t =
last M5 close in the preceding 15 minutes (bid), cost **1.2 pips per round trip**, decision-stream format: one row per month-end
(`pos` = 0 when the rule does not trade), `periods_per_year` = 12. Daily window prices cached in `data/processed/flows_calendar_fix_windows.parquet`.
Seven month-ends have no bars in the fix window at the source (2020-11, 2021-05, 2023-02..06: the known HistData 2023 gaps) and are absent.

**Variants: 12 candidates, all listed, none dropped.** Not eligible for selection (benchmarks / diagnostics, 13 streams): the round-1 unconditional
fix-follow and its "disagree" half, the live `season` rule and its two legs, the live `tom` rule, `blackout_trend` outside the windows, `reb_d3`
with a rest-of-world basket and with the DAX, two mid-month placebos, the `eqrel` sign on all days and on the last 3 sessions. Plus 6 re-runs of the
live weak-signal combination (replace test) and the leak-check runs.
**Selection rule (declared before results):** highest 2010-2015 walk-forward net Sharpe at 1.2 pips -> **`blackout_trend`** (0.71).

## All candidates (net, 1.2 pips; daily variants on the session grid, sqrt(252); fix variants on the monthly decision grid, sqrt(12))
| variant        |   SR 2010-2026 |   SR 2016-2026 |   SR 2023-2026 |   SR 2010-2015 |   SR 2016-2022 |   t 2010-26 |   t 2016-26 |   t 2023-26 |   hit net 2010-26 |   trades/yr |   active sessions/yr |   defl. p |
|:---------------|---------------:|---------------:|---------------:|---------------:|---------------:|------------:|------------:|------------:|------------------:|------------:|---------------------:|----------:|
| reb_d3         |           0.03 |           0.08 |          -0.00 |          -0.04 |           0.12 |        0.13 |        0.26 |       -0.00 |              0.52 |       12.05 |                36.14 |      0.94 |
| reb_d1         |          -0.12 |          -0.09 |           0.39 |          -0.16 |          -0.29 |       -0.49 |       -0.29 |        0.77 |              0.51 |       12.05 |                12.05 |      0.98 |
| reb_d3_lin     |           0.02 |           0.05 |           0.24 |          -0.02 |          -0.04 |        0.08 |        0.16 |        0.49 |              0.52 |       12.05 |                36.14 |      0.94 |
| nm_rev_sig     |           0.26 |           0.21 |          -0.10 |           0.34 |           0.42 |        1.10 |        0.71 |       -0.19 |              0.54 |       12.11 |                24.09 |      0.71 |
| nm_rev_px      |           0.24 |           0.16 |           0.54 |           0.35 |          -0.09 |        1.00 |        0.55 |        1.08 |              0.53 |       12.11 |                24.09 |      0.74 |
| season_js      |           0.03 |           0.03 |           0.06 |           0.00 |           0.00 |        0.11 |        0.11 |        0.11 |              0.54 |        0.30 |                13.12 |      0.94 |
| imm_fade_cot   |          -0.46 |          -0.62 |          -0.75 |          -0.22 |          -0.56 |       -1.93 |       -2.07 |       -1.49 |              0.48 |        4.15 |                19.88 |      1.00 |
| hol_square     |          -0.25 |          -0.00 |           0.51 |          -0.68 |          -0.19 |       -1.05 |       -0.00 |        1.02 |              0.43 |       11.87 |                11.87 |      1.00 |
| blackout_trend |           0.17 |          -0.25 |           0.11 |           0.71 |          -0.40 |        0.72 |       -0.85 |        0.21 |              0.50 |       32.46 |               137.27 |      0.83 |
| flows_core     |           0.21 |           0.21 |          -0.06 |           0.21 |           0.35 |        0.86 |        0.69 |       -0.12 |              0.52 |       22.08 |                70.09 |      0.79 |
| fix_reb        |          -0.28 |           0.00 |           0.10 |          -0.81 |          -0.03 |       -1.14 |        0.00 |        0.19 |              0.46 |       11.57 |                11.57 |      1.00 |
| fix_follow_reb |           0.48 |           0.47 |           0.84 |           0.51 |           0.39 |        1.93 |        1.51 |        1.56 |              0.56 |        5.16 |                 5.16 |      0.36 |

`trades/yr` = runs of consecutive active sessions with an unchanged sign; `defl. p` = deflated-Sharpe probability for 12 trials.
`season_js` is flat by construction: the shrinkage factor is 0 in every test year but 2026 (0.005), so its numbers describe a 0.1 % position.

At 0.6 pips:
| variant                |   SR 2010-2026 |   SR 2016-2026 |   SR 2023-2026 |   SR 2010-2015 |
|:-----------------------|---------------:|---------------:|---------------:|---------------:|
| reb_d3_cost0.6         |           0.07 |           0.13 |           0.05 |          -0.00 |
| reb_d1_cost0.6         |          -0.05 |          -0.00 |           0.49 |          -0.11 |
| reb_d3_lin_cost0.6     |           0.05 |           0.09 |           0.29 |           0.01 |
| nm_rev_sig_cost0.6     |           0.31 |           0.27 |          -0.05 |           0.38 |
| nm_rev_px_cost0.6      |           0.29 |           0.22 |           0.59 |           0.39 |
| season_js_cost0.6      |           0.03 |           0.04 |           0.06 |           0.00 |
| imm_fade_cot_cost0.6   |          -0.44 |          -0.60 |          -0.73 |          -0.20 |
| hol_square_cost0.6     |          -0.17 |           0.08 |           0.62 |          -0.62 |
| blackout_trend_cost0.6 |           0.23 |          -0.19 |           0.16 |           0.75 |
| flows_core_cost0.6     |           0.26 |           0.27 |           0.01 |           0.25 |
| fix_reb_cost0.6        |          -0.20 |           0.08 |           0.21 |          -0.74 |
| fix_follow_reb_cost0.6 |           0.56 |           0.56 |           0.98 |           0.59 |

Benchmarks and diagnostics (same harness, not candidates):
| variant                      |   SR 2010-2026 |   SR 2016-2026 |   SR 2023-2026 |   SR 2010-2015 |   SR 2016-2022 |   t 2010-26 |   t 2016-26 |   t 2023-26 |   hit net 2010-26 |   trades/yr |   active sessions/yr |
|:-----------------------------|---------------:|---------------:|---------------:|---------------:|---------------:|------------:|------------:|------------:|------------------:|------------:|---------------------:|
| bench_fix_follow             |           0.56 |           0.60 |           0.90 |           0.49 |           0.54 |        2.28 |        1.94 |        1.66 |              0.54 |       11.57 |                11.57 |
| bench_fix_follow_disagree    |           0.31 |           0.37 |           0.42 |           0.21 |           0.37 |        1.26 |        1.19 |        0.77 |              0.53 |        6.41 |                 6.41 |
| bench_live_season_dec_may    |           0.58 |           0.31 |           0.25 |           0.93 |           0.35 |        2.44 |        1.05 |        0.49 |              0.54 |        1.96 |                42.85 |
| bench_live_tom               |           0.11 |          -0.15 |           0.05 |           0.45 |          -0.25 |        0.45 |       -0.49 |        0.09 |              0.51 |       12.05 |                60.24 |
| bench_blackout_trend_outside |          -0.24 |          -0.27 |           0.16 |          -0.20 |          -0.54 |       -0.99 |       -0.90 |        0.32 |              0.49 |       30.50 |               122.08 |
| diag_reb_d3_row              |          -0.07 |          -0.13 |           0.18 |           0.02 |          -0.27 |       -0.29 |       -0.44 |        0.35 |              0.49 |       12.05 |                36.14 |
| diag_reb_d3_dax              |          -0.10 |          -0.42 |          -0.12 |           0.36 |          -0.56 |       -0.40 |       -1.41 |       -0.25 |              0.50 |       12.05 |                36.14 |
| placebo_reb_midmonth_8_6     |          -0.11 |          -0.05 |          -0.83 |          -0.19 |           0.35 |       -0.46 |       -0.17 |       -1.65 |              0.49 |       11.99 |                35.96 |
| placebo_reb_midmonth_13_11   |          -0.25 |          -0.41 |           0.12 |          -0.02 |          -0.68 |       -1.04 |       -1.36 |        0.25 |              0.48 |       11.99 |                35.96 |
| bench_live_season_dec_only   |           0.29 |           0.46 |           0.07 |           0.11 |           0.64 |        1.22 |        1.53 |        0.14 |              0.54 |        0.95 |                20.59 |
| bench_live_season_may_only   |           0.52 |           0.02 |           0.26 |           1.09 |          -0.09 |        2.15 |        0.06 |        0.53 |              0.54 |        1.01 |                22.26 |
| diag_eqrel20_sign_all_days   |           0.38 |           0.30 |           0.34 |           0.50 |           0.28 |        1.60 |        1.01 |        0.68 |              0.51 |       35.19 |               259.53 |
| diag_eqrel20_sign_last3      |          -0.33 |          -0.26 |          -0.19 |          -0.43 |          -0.30 |       -1.37 |       -0.88 |       -0.37 |              0.46 |       15.49 |                36.14 |

## Final variant `blackout_trend`: per-year record (net)
| period    |    n |   sharpe |      t |   mean_bp |    sum_bp |   active_frac |   sharpe_0.6pip |   t_0.6pip |
|:----------|-----:|---------:|-------:|----------:|----------:|--------------:|----------------:|-----------:|
| 2010      |  260 |    2.476 |  2.515 |     8.495 |  2208.795 |         0.573 |           2.511 |      2.550 |
| 2011      |  260 |    1.988 |  2.019 |     6.917 |  1798.477 |         0.569 |           2.022 |      2.054 |
| 2012      |  260 |   -0.791 | -0.804 |    -1.981 |  -515.113 |         0.608 |          -0.735 |     -0.747 |
| 2013      |  259 |    0.421 |  0.427 |     0.836 |   216.455 |         0.641 |           0.491 |      0.498 |
| 2014      |  258 |    0.456 |  0.461 |     0.829 |   213.917 |         0.674 |           0.536 |      0.543 |
| 2015      |  259 |   -0.696 | -0.706 |    -2.643 |  -684.452 |         0.676 |          -0.649 |     -0.658 |
| 2016      |  259 |    0.371 |  0.376 |     1.038 |   268.812 |         0.618 |           0.422 |      0.428 |
| 2017      |  259 |   -1.208 | -1.224 |    -2.737 |  -708.856 |         0.602 |          -1.134 |     -1.149 |
| 2018      |  260 |   -0.709 | -0.720 |    -1.437 |  -373.588 |         0.569 |          -0.644 |     -0.654 |
| 2019      |  260 |    0.143 |  0.146 |     0.211 |    54.774 |         0.600 |           0.236 |      0.239 |
| 2020      |  260 |   -0.572 | -0.581 |    -1.273 |  -330.990 |         0.585 |          -0.504 |     -0.512 |
| 2021      |  259 |   -0.099 | -0.100 |    -0.139 |   -36.098 |         0.402 |          -0.035 |     -0.035 |
| 2022      |  260 |   -0.648 | -0.659 |    -1.840 |  -478.364 |         0.477 |          -0.601 |     -0.610 |
| 2023      |  258 |   -1.443 | -1.460 |    -2.669 |  -688.558 |         0.415 |          -1.384 |     -1.400 |
| 2024      |  261 |    0.454 |  0.462 |     0.591 |   154.363 |         0.307 |           0.503 |      0.512 |
| 2025      |  260 |    1.540 |  1.564 |     2.659 |   691.317 |         0.296 |           1.583 |      1.608 |
| 2026      |  220 |    0.037 |  0.034 |     0.053 |    11.679 |         0.357 |           0.099 |      0.092 |
| 2010-2026 | 4372 |    0.173 |  0.719 |     0.412 |  1802.569 |         0.529 |           0.225 |      0.939 |
| 2016-2026 | 2816 |   -0.253 | -0.846 |    -0.510 | -1435.510 |         0.477 |          -0.194 |     -0.650 |
| 2023-2026 |  999 |    0.105 |  0.210 |     0.169 |   168.800 |         0.343 |           0.159 |      0.316 |
| 2010-2015 | 1556 |    0.706 |  1.755 |     2.081 |  3238.078 |         0.623 |           0.754 |      1.874 |
| 2016-2022 | 1817 |   -0.400 | -1.073 |    -0.883 | -1604.310 |         0.550 |          -0.338 |     -0.907 |

Deflated-Sharpe p 0.83 (12 variants). Success bar: 2016-2026 > 0.3 **failed** (-0.25); 2023-2026 not negative: passed (0.11, t 0.2);
three-way beats two-way on 2016-2026: **failed** (0.42 vs 0.64). The 2010-2015 number that selected it is two years (2010, 2011), and the trend rule
outside the blackout windows is negative in the same harness (-0.24), so the "blackout" conditioning looked informative in 2010-2015 and
reversed afterwards: a selection artefact.

Hit rates of the final variant (out of sample):
| period    |   decisions |   decisions_per_year |   hit_net |   hit_sign_gross |   episodes |   episodes_per_year |   episode_hit_net |   episode_hit_gross |   mean_net_bp_per_decision |   mean_gross_bp_per_decision |
|:----------|------------:|---------------------:|----------:|-----------------:|-----------:|--------------------:|------------------:|--------------------:|---------------------------:|-----------------------------:|
| 2010-2026 |        2313 |              137.270 |     0.498 |            0.501 |        547 |              32.463 |             0.479 |               0.486 |                      0.935 |                        1.257 |
| 2016-2026 |        1343 |              123.779 |     0.491 |            0.494 |        312 |              28.756 |             0.455 |               0.462 |                     -0.907 |                       -0.573 |
| 2023-2026 |         343 |               89.091 |     0.472 |            0.481 |         78 |              20.260 |             0.564 |               0.577 |                      0.666 |                        0.988 |

Hit rates of every candidate (`season_js` omitted: flat):
| variant        | period    |   decisions |   decisions_per_year |   hit_net |   hit_sign_gross |   episodes_per_year |   episode_hit_net |   mean_net_bp_per_decision |
|:---------------|:----------|------------:|---------------------:|----------:|-----------------:|--------------------:|------------------:|---------------------------:|
| reb_d3         | 2010-2026 |         609 |               36.142 |     0.519 |            0.522 |              12.047 |             0.493 |                      0.590 |
| reb_d3         | 2016-2026 |         393 |               36.221 |     0.529 |            0.534 |              12.074 |             0.504 |                      0.933 |
| reb_d3         | 2023-2026 |         141 |               36.623 |     0.518 |            0.532 |              12.208 |             0.511 |                      0.338 |
| reb_d1         | 2010-2026 |         203 |               12.047 |     0.512 |            0.512 |              12.047 |             0.512 |                     -0.694 |
| reb_d1         | 2016-2026 |         131 |               12.074 |     0.534 |            0.534 |              12.074 |             0.534 |                     -0.066 |
| reb_d1         | 2023-2026 |          47 |               12.208 |     0.596 |            0.596 |              12.208 |             0.596 |                      5.234 |
| reb_d3_lin     | 2010-2026 |         609 |               36.142 |     0.519 |            0.522 |              12.047 |             0.493 |                      0.271 |
| reb_d3_lin     | 2016-2026 |         393 |               36.221 |     0.529 |            0.534 |              12.074 |             0.504 |                      0.392 |
| reb_d3_lin     | 2023-2026 |         141 |               36.623 |     0.518 |            0.532 |              12.208 |             0.511 |                      1.129 |
| nm_rev_sig     | 2010-2026 |         406 |               24.095 |     0.537 |            0.539 |              12.107 |             0.525 |                      3.368 |
| nm_rev_sig     | 2016-2026 |         262 |               24.147 |     0.523 |            0.527 |              12.166 |             0.553 |                      2.564 |
| nm_rev_sig     | 2023-2026 |          94 |               24.416 |     0.511 |            0.521 |              12.468 |             0.542 |                     -0.484 |
| nm_rev_px      | 2010-2026 |         406 |               24.095 |     0.532 |            0.534 |              12.107 |             0.529 |                      3.113 |
| nm_rev_px      | 2016-2026 |         262 |               24.147 |     0.534 |            0.538 |              12.166 |             0.523 |                      2.107 |
| nm_rev_px      | 2023-2026 |          94 |               24.416 |     0.521 |            0.532 |              12.468 |             0.500 |                      6.340 |
| imm_fade_cot   | 2010-2026 |         335 |               19.881 |     0.481 |            0.487 |               4.154 |             0.357 |                     -5.245 |
| imm_fade_cot   | 2016-2026 |         215 |               19.816 |     0.465 |            0.474 |               4.147 |             0.289 |                     -6.705 |
| imm_fade_cot   | 2023-2026 |          75 |               19.481 |     0.453 |            0.453 |               3.896 |             0.267 |                     -7.546 |
| hol_square     | 2010-2026 |         200 |               11.869 |     0.435 |            0.445 |              11.869 |             0.435 |                     -2.324 |
| hol_square     | 2016-2026 |         130 |               11.982 |     0.477 |            0.485 |              11.982 |             0.477 |                      1.061 |
| hol_square     | 2023-2026 |          47 |               12.208 |     0.574 |            0.596 |              12.208 |             0.574 |                      5.971 |
| blackout_trend | 2010-2026 |        2313 |              137.270 |     0.498 |            0.501 |              32.463 |             0.479 |                      0.935 |
| blackout_trend | 2016-2026 |        1343 |              123.779 |     0.491 |            0.494 |              28.756 |             0.455 |                     -0.907 |
| blackout_trend | 2023-2026 |         343 |               89.091 |     0.472 |            0.481 |              20.260 |             0.564 |                      0.666 |
| flows_core     | 2010-2026 |        1181 |               70.089 |     0.524 |            0.532 |              22.077 |             0.513 |                      1.336 |
| flows_core     | 2016-2026 |         821 |               75.668 |     0.525 |            0.535 |              22.396 |             0.531 |                      1.130 |
| flows_core     | 2023-2026 |         401 |              104.156 |     0.516 |            0.536 |              22.597 |             0.529 |                     -0.105 |
| fix_reb        | 2010-2026 |         195 |               11.573 |     0.456 |            0.487 |              11.573 |             0.456 |                     -1.836 |
| fix_reb        | 2016-2026 |         123 |               11.336 |     0.504 |            0.520 |              11.336 |             0.504 |                      0.009 |
| fix_reb        | 2023-2026 |          41 |               10.649 |     0.561 |            0.585 |              10.649 |             0.561 |                      0.499 |
| fix_follow_reb | 2010-2026 |          87 |                5.163 |     0.563 |            0.575 |               5.163 |             0.563 |                      2.852 |
| fix_follow_reb | 2016-2026 |          60 |                5.530 |     0.567 |            0.567 |               5.530 |             0.567 |                      2.844 |
| fix_follow_reb | 2023-2026 |          20 |                5.195 |     0.650 |            0.650 |               5.195 |             0.650 |                      3.077 |

## (1) Month-end: conditioned vs unconditioned (gross bp per month-end event, no costs)
All month-ends:
| test (gross bp per month-end, no cost)                                | 2003-2009                      | 2010-2015                      | 2016-2022                      | 2023-2026                      | 2010-2026                      |
|:----------------------------------------------------------------------|:-------------------------------|:-------------------------------|:-------------------------------|:-------------------------------|:-------------------------------|
| daily T-2..T: unconditional long EUR                                  | +5.4 (t +0.5, hit 0.57, n 84)  | -4.6 (t -0.4, hit 0.44, n 72)  | +10.3 (t +1.2, hit 0.54, n 84) | -13.7 (t -1.5, hit 0.40, n 47) | -0.5 (t -0.1, hit 0.47, n 203) |
| daily T-2..T: sign(rel@T-3)  [reb_d3]                                 | -11.1 (t -0.5, hit 0.45, n 33) | +0.8 (t +0.1, hit 0.50, n 72)  | +4.9 (t +0.6, hit 0.50, n 84)  | +2.1 (t +0.2, hit 0.51, n 47)  | +2.8 (t +0.5, hit 0.50, n 203) |
| daily T-2..T: sign(rel_dax@T-3) (SPX-DAX, diag.)                      | -4.3 (t -0.4, hit 0.42, n 83)  | +12.3 (t +1.0, hit 0.54, n 72) | -11.2 (t -1.3, hit 0.40, n 84) | -0.3 (t -0.0, hit 0.51, n 47)  | -0.3 (t -0.1, hit 0.48, n 203) |
| daily T-2..T: sign(rel_row@T-3) (US vs SX5E/FTSE/N225, diag.)         | -19.0 (t -0.9, hit 0.45, n 33) | +2.3 (t +0.2, hit 0.50, n 72)  | -4.3 (t -0.5, hit 0.44, n 84)  | +5.6 (t +0.6, hit 0.51, n 47)  | +0.3 (t +0.1, hit 0.48, n 203) |
| daily T: unconditional long EUR                                       | +7.3 (t +1.0, hit 0.54, n 84)  | -3.5 (t -0.5, hit 0.50, n 72)  | +0.2 (t +0.0, hit 0.50, n 84)  | -11.3 (t -2.2, hit 0.43, n 47) | -3.8 (t -1.1, hit 0.48, n 203) |
| daily T: sign(rel@T-1)  [reb_d1]                                      | -13.6 (t -1.0, hit 0.45, n 33) | -0.9 (t -0.1, hit 0.47, n 72)  | -2.0 (t -0.4, hit 0.50, n 84)  | +6.3 (t +1.2, hit 0.60, n 47)  | +0.3 (t +0.1, hit 0.51, n 203) |
| daily T+1..T+2: unconditional long EUR                                | +1.3 (t +0.1, hit 0.52, n 84)  | -2.8 (t -0.3, hit 0.46, n 72)  | -2.2 (t -0.3, hit 0.49, n 84)  | -4.4 (t -0.5, hit 0.43, n 46)  | -2.9 (t -0.6, hit 0.47, n 202) |
| daily T+1..T+2: -sign(rel@T)  [nm_rev_sig]                            | +8.1 (t +0.5, hit 0.61, n 33)  | +12.1 (t +1.2, hit 0.50, n 72) | +7.3 (t +1.1, hit 0.55, n 84)  | +2.5 (t +0.3, hit 0.59, n 46)  | +7.9 (t +1.6, hit 0.54, n 202) |
| daily T+1..T+2: -sign(ret T-2..T)  [nm_rev_px]                        | -10.1 (t -1.0, hit 0.48, n 84) | +10.2 (t +1.0, hit 0.57, n 72) | +2.8 (t +0.4, hit 0.55, n 84)  | +11.5 (t +1.2, hit 0.50, n 46) | +7.4 (t +1.5, hit 0.54, n 202) |
| fix 15:00-16:00: unconditional long EUR                               | -1.2 (t -0.4, hit 0.49, n 83)  | -4.5 (t -1.8, hit 0.39, n 72)  | +3.5 (t +1.2, hit 0.59, n 82)  | +4.1 (t +1.6, hit 0.56, n 41)  | +0.6 (t +0.4, hit 0.51, n 195) |
| fix 15:00-16:00: sign(rel)  [fix_reb]                                 | +6.1 (t +1.1, hit 0.58, n 33)  | -4.1 (t -1.6, hit 0.43, n 72)  | +0.8 (t +0.3, hit 0.49, n 82)  | +1.6 (t +0.6, hit 0.59, n 41)  | -0.8 (t -0.5, hit 0.49, n 195) |
| fix 15:45-16:00: follow 15:00-15:45 (round-1 H05, unconditional)      | +2.4 (t +1.8, hit 0.53, n 83)  | +2.5 (t +1.9, hit 0.60, n 72)  | +3.4 (t +2.0, hit 0.55, n 82)  | +3.4 (t +2.5, hit 0.59, n 41)  | +3.1 (t +3.4, hit 0.57, n 195) |
| fix 15:45-16:00: follow, move agrees with sign(rel)  [fix_follow_reb] | +6.9 (t +1.6, hit 0.67, n 18)  | +3.8 (t +1.7, hit 0.59, n 27)  | +3.8 (t +1.4, hit 0.53, n 40)  | +4.2 (t +2.2, hit 0.65, n 20)  | +3.9 (t +2.6, hit 0.57, n 87)  |
| fix 15:45-16:00: follow, move disagrees with sign(rel)                | +1.9 (t +0.7, hit 0.50, n 14)  | +1.8 (t +1.1, hit 0.60, n 45)  | +3.1 (t +1.5, hit 0.57, n 42)  | +2.6 (t +1.3, hit 0.52, n 21)  | +2.5 (t +2.1, hit 0.57, n 108) |

Quarter-ends (Mar/Jun/Sep/Dec):
| test (gross bp per month-end, no cost)                                | 2010-2015                      | 2016-2022                      | 2023-2026                      | 2010-2026                      |
|:----------------------------------------------------------------------|:-------------------------------|:-------------------------------|:-------------------------------|:-------------------------------|
| daily T-2..T: unconditional long EUR                                  | -4.0 (t -0.2, hit 0.38, n 24)  | +17.6 (t +1.1, hit 0.57, n 28) | +4.8 (t +0.4, hit 0.40, n 15)  | +7.0 (t +0.7, hit 0.46, n 67)  |
| daily T-2..T: sign(rel@T-3)  [reb_d3]                                 | -12.3 (t -0.7, hit 0.50, n 24) | +3.9 (t +0.2, hit 0.50, n 28)  | +6.0 (t +0.5, hit 0.53, n 15)  | -1.4 (t -0.1, hit 0.51, n 67)  |
| daily T-2..T: sign(rel_dax@T-3) (SPX-DAX, diag.)                      | +14.7 (t +0.8, hit 0.58, n 24) | -10.1 (t -0.6, hit 0.39, n 28) | +6.0 (t +0.5, hit 0.53, n 15)  | +2.4 (t +0.2, hit 0.49, n 67)  |
| daily T-2..T: sign(rel_row@T-3) (US vs SX5E/FTSE/N225, diag.)         | -0.9 (t -0.0, hit 0.50, n 24)  | -0.7 (t -0.0, hit 0.43, n 28)  | -5.4 (t -0.4, hit 0.40, n 15)  | -1.8 (t -0.2, hit 0.45, n 67)  |
| daily T: unconditional long EUR                                       | -6.3 (t -0.5, hit 0.50, n 24)  | +1.9 (t +0.3, hit 0.46, n 28)  | +1.3 (t +0.1, hit 0.47, n 15)  | -1.2 (t -0.2, hit 0.48, n 67)  |
| daily T: sign(rel@T-1)  [reb_d1]                                      | -4.7 (t -0.4, hit 0.46, n 24)  | -3.3 (t -0.5, hit 0.43, n 28)  | +8.5 (t +0.9, hit 0.60, n 15)  | -1.2 (t -0.2, hit 0.48, n 67)  |
| daily T+1..T+2: unconditional long EUR                                | -2.7 (t -0.2, hit 0.46, n 24)  | -23.2 (t -1.7, hit 0.39, n 28) | -21.5 (t -1.5, hit 0.33, n 15) | -15.5 (t -1.7, hit 0.40, n 67) |
| daily T+1..T+2: -sign(rel@T)  [nm_rev_sig]                            | +28.1 (t +1.7, hit 0.54, n 24) | +3.1 (t +0.2, hit 0.50, n 28)  | -10.7 (t -0.7, hit 0.47, n 15) | +9.0 (t +1.0, hit 0.51, n 67)  |
| daily T+1..T+2: -sign(ret T-2..T)  [nm_rev_px]                        | +15.9 (t +0.9, hit 0.58, n 24) | +10.5 (t +0.8, hit 0.61, n 28) | -11.3 (t -0.8, hit 0.33, n 15) | +7.6 (t +0.8, hit 0.54, n 67)  |
| fix 15:00-16:00: unconditional long EUR                               | -4.2 (t -1.1, hit 0.50, n 24)  | +8.9 (t +3.0, hit 0.64, n 28)  | +2.6 (t +0.6, hit 0.54, n 13)  | +2.8 (t +1.3, hit 0.57, n 65)  |
| fix 15:00-16:00: sign(rel)  [fix_reb]                                 | -5.8 (t -1.6, hit 0.42, n 24)  | -4.2 (t -1.3, hit 0.43, n 28)  | +0.9 (t +0.2, hit 0.62, n 13)  | -3.8 (t -1.7, hit 0.46, n 65)  |
| fix 15:45-16:00: follow 15:00-15:45 (round-1 H05, unconditional)      | +1.0 (t +0.3, hit 0.58, n 24)  | +3.2 (t +1.4, hit 0.61, n 28)  | +2.5 (t +0.9, hit 0.54, n 13)  | +2.2 (t +1.4, hit 0.58, n 65)  |
| fix 15:45-16:00: follow, move agrees with sign(rel)  [fix_follow_reb] | -0.5 (t -0.1, hit 0.57, n 7)   | +3.8 (t +1.0, hit 0.64, n 11)  | -0.5 (t -0.1, hit 0.43, n 7)   | +1.4 (t +0.6, hit 0.56, n 25)  |
| fix 15:45-16:00: follow, move disagrees with sign(rel)                | +1.6 (t +0.5, hit 0.59, n 17)  | +2.8 (t +0.9, hit 0.59, n 17)  | +6.0 (t +1.9, hit 0.67, n 6)   | +2.8 (t +1.4, hit 0.60, n 40)  |

Year-end (December only) and non-quarter month-ends, 2010-2026:
| test (gross bp per month-end, no cost)                                | 2010-2026                      |
|:----------------------------------------------------------------------|:-------------------------------|
| daily T-2..T: unconditional long EUR                                  | +23.1 (t +1.1, hit 0.50, n 16) |
| daily T-2..T: sign(rel@T-3)  [reb_d3]                                 | -21.9 (t -1.1, hit 0.38, n 16) |
| daily T-2..T: sign(rel_dax@T-3) (SPX-DAX, diag.)                      | +8.5 (t +0.4, hit 0.50, n 16)  |
| daily T-2..T: sign(rel_row@T-3) (US vs SX5E/FTSE/N225, diag.)         | -21.3 (t -1.0, hit 0.31, n 16) |
| daily T: unconditional long EUR                                       | -4.0 (t -0.4, hit 0.44, n 16)  |
| daily T: sign(rel@T-1)  [reb_d1]                                      | -18.8 (t -2.0, hit 0.31, n 16) |
| daily T+1..T+2: unconditional long EUR                                | -61.4 (t -3.7, hit 0.19, n 16) |
| daily T+1..T+2: -sign(rel@T)  [nm_rev_sig]                            | -10.3 (t -0.4, hit 0.38, n 16) |
| daily T+1..T+2: -sign(ret T-2..T)  [nm_rev_px]                        | +13.8 (t +0.6, hit 0.56, n 16) |
| fix 15:00-16:00: unconditional long EUR                               | -4.8 (t -1.2, hit 0.44, n 16)  |
| fix 15:00-16:00: sign(rel)  [fix_reb]                                 | -1.1 (t -0.3, hit 0.62, n 16)  |
| fix 15:45-16:00: follow 15:00-15:45 (round-1 H05, unconditional)      | -1.1 (t -0.3, hit 0.50, n 16)  |
| fix 15:45-16:00: follow, move agrees with sign(rel)  [fix_follow_reb] | -0.3 (t -0.1, hit 0.50, n 8)   |
| fix 15:45-16:00: follow, move disagrees with sign(rel)                | -1.8 (t -0.3, hit 0.50, n 8)   |

| test (gross bp per month-end, no cost)                                | 2010-2026                      |
|:----------------------------------------------------------------------|:-------------------------------|
| daily T-2..T: unconditional long EUR                                  | -4.3 (t -0.6, hit 0.48, n 136) |
| daily T-2..T: sign(rel@T-3)  [reb_d3]                                 | +4.9 (t +0.7, hit 0.50, n 136) |
| daily T-2..T: sign(rel_dax@T-3) (SPX-DAX, diag.)                      | -1.7 (t -0.2, hit 0.47, n 136) |
| daily T-2..T: sign(rel_row@T-3) (US vs SX5E/FTSE/N225, diag.)         | +1.4 (t +0.2, hit 0.49, n 136) |
| daily T: unconditional long EUR                                       | -5.0 (t -1.2, hit 0.49, n 136) |
| daily T: sign(rel@T-1)  [reb_d1]                                      | +1.1 (t +0.2, hit 0.53, n 136) |
| daily T+1..T+2: unconditional long EUR                                | +3.3 (t +0.5, hit 0.50, n 135) |
| daily T+1..T+2: -sign(rel@T)  [nm_rev_sig]                            | +7.4 (t +1.2, hit 0.56, n 135) |
| daily T+1..T+2: -sign(ret T-2..T)  [nm_rev_px]                        | +7.4 (t +1.2, hit 0.55, n 135) |
| fix 15:00-16:00: unconditional long EUR                               | -0.4 (t -0.2, hit 0.48, n 130) |
| fix 15:00-16:00: sign(rel)  [fix_reb]                                 | +0.7 (t +0.3, hit 0.50, n 130) |
| fix 15:45-16:00: follow 15:00-15:45 (round-1 H05, unconditional)      | +3.5 (t +3.1, hit 0.57, n 130) |
| fix 15:45-16:00: follow, move agrees with sign(rel)  [fix_follow_reb] | +4.9 (t +2.7, hit 0.58, n 62)  |
| fix 15:45-16:00: follow, move disagrees with sign(rel)                | +2.3 (t +1.6, hit 0.56, n 68)  |

Reading:
* The equity sign adds nothing to any daily window: `reb_d3` +2.8 bp over three sessions (t 0.5, hit 50 %), `reb_d1` +0.3 bp (t 0.1). The
  DAX-based history 2003-2009 (-4 bp) and the rest-of-world basket (+0.3 bp) agree. Quarter-ends are not stronger (-1.4 bp, t -0.1); year-end has
  16 observations and is negative.
* Into the fix, the rebalancing direction itself is wrong-signed in 2010-2015 and zero since (`fix_reb` -0.8 bp, t -0.5).
* The unconditional round-1 rule is the only row with |t| > 3: +3.1 bp (t 3.4), positive in 2003-09, 2010-15, 2016-22, 2023-26. Splitting it by
  agreement with the equity sign gives +3.9 bp (n 87) vs +2.5 bp (n 108): a 1.4 bp difference with a standard error of about 1.9 bp.
* The mid-month placebos of `reb_d3` (sessions 8-6 and 13-11 before month-end) give Sharpe -0.11 and -0.25: no month-end pattern to speak of.
* Not a candidate, noted only: the first two sessions of January are down in 13 of 16 years 2010-2026 (-61 bp, t -3.7). It is one cell of a 280-cell
  table and overlaps the live `tom` short; treat it as a hypothesis, not a finding.

Is the fix continuation a month-end effect? Same rule on other days (gross bp, `flows_calendar_fix_follow_by_day.csv`):
| day                   | 2001-2009                        | 2010-2015                        | 2016-2022                        | 2023-2026                       | 2010-2026                        |
|:----------------------|:---------------------------------|:---------------------------------|:---------------------------------|:--------------------------------|:---------------------------------|
| last business day (T) | +1.67 (t +1.4, hit 0.52, n 101)  | +2.55 (t +1.9, hit 0.60, n 72)   | +3.45 (t +2.0, hit 0.55, n 82)   | +3.35 (t +2.5, hit 0.59, n 41)  | +3.10 (t +3.4, hit 0.57, n 195)  |
| T-1                   | -0.46 (t -0.6, hit 0.40, n 108)  | +0.50 (t +0.6, hit 0.50, n 72)   | -1.52 (t -1.7, hit 0.46, n 84)   | -0.37 (t -0.5, hit 0.39, n 46)  | -0.54 (t -1.0, hit 0.46, n 202)  |
| T-2                   | +1.03 (t +1.1, hit 0.48, n 108)  | +1.63 (t +1.3, hit 0.60, n 72)   | -1.18 (t -1.0, hit 0.50, n 84)   | -0.66 (t -0.5, hit 0.50, n 44)  | -0.05 (t -0.1, hit 0.54, n 200)  |
| all other days        | +0.18 (t +0.9, hit 0.43, n 1903) | +0.49 (t +2.1, hit 0.49, n 1340) | -0.54 (t -2.7, hit 0.45, n 1562) | -0.60 (t -2.7, hit 0.42, n 759) | -0.17 (t -1.4, hit 0.46, n 3661) |

Yes: it exists only on the last business day; on the other 3,661 days the continuation is -0.17 bp and after 2016 significantly negative.
The 15:45-16:00 absolute move is 9.7 bp on the last day against 5.7 bp otherwise, which is the flow.

Per-year record of the two fix streams (net of 1.2 pips per round trip, bp per month-end):
| period    |   bench_fix_follow n |   fix_follow_reb n |   bench_fix_follow sharpe |   fix_follow_reb sharpe |   bench_fix_follow mean_bp |   fix_follow_reb mean_bp |   bench_fix_follow sum_bp |   fix_follow_reb sum_bp |
|:----------|---------------------:|-------------------:|--------------------------:|------------------------:|---------------------------:|-------------------------:|--------------------------:|------------------------:|
| 2010      |                12.00 |              12.00 |                      0.86 |                    1.25 |                       2.22 |                     2.47 |                     26.63 |                   29.66 |
| 2010-2015 |                72.00 |              72.00 |                      0.49 |                    0.51 |                       1.62 |                     1.08 |                    116.38 |                   77.49 |
| 2010-2026 |               195.00 |             195.00 |                      0.56 |                    0.48 |                       2.08 |                     1.27 |                    405.01 |                  248.10 |
| 2011      |                12.00 |              12.00 |                     -0.10 |                    0.83 |                      -0.27 |                     0.41 |                     -3.22 |                    4.97 |
| 2012      |                12.00 |              12.00 |                     -0.50 |                   -1.04 |                      -1.58 |                    -0.74 |                    -18.96 |                   -8.87 |
| 2013      |                12.00 |              12.00 |                      1.93 |                   -0.19 |                       3.45 |                    -0.18 |                     41.41 |                   -2.18 |
| 2014      |                12.00 |              12.00 |                      0.73 |                    0.65 |                       2.03 |                     1.24 |                     24.40 |                   14.90 |
| 2015      |                12.00 |              12.00 |                      0.65 |                    0.76 |                       3.84 |                     3.25 |                     46.12 |                   39.02 |
| 2016      |                12.00 |              12.00 |                      0.76 |                    1.28 |                       3.34 |                     3.58 |                     40.09 |                   42.96 |
| 2016-2022 |                82.00 |              82.00 |                      0.54 |                    0.39 |                       2.38 |                     1.33 |                    195.38 |                  109.08 |
| 2016-2026 |               123.00 |             123.00 |                      0.60 |                    0.47 |                       2.35 |                     1.39 |                    288.62 |                  170.61 |
| 2017      |                12.00 |              12.00 |                      1.01 |                    1.30 |                       4.11 |                     4.75 |                     49.28 |                   57.02 |
| 2018      |                12.00 |              12.00 |                     -0.22 |                   -1.01 |                      -0.60 |                    -2.19 |                     -7.15 |                  -26.30 |
| 2019      |                12.00 |              12.00 |                     -0.75 |                   -0.41 |                      -2.49 |                    -1.37 |                    -29.93 |                  -16.41 |
| 2020      |                11.00 |              11.00 |                      0.48 |                    0.67 |                       2.67 |                     3.37 |                     29.39 |                   37.03 |
| 2021      |                11.00 |              11.00 |                      0.32 |                   -1.50 |                       2.12 |                    -4.59 |                     23.29 |                  -50.48 |
| 2022      |                12.00 |              12.00 |                      1.86 |                    1.92 |                       7.53 |                     5.44 |                     90.41 |                   65.26 |
| 2023      |                 7.00 |               7.00 |                      0.00 |                    0.00 |                       1.29 |                    -0.31 |                      9.04 |                   -2.20 |
| 2023-2026 |                41.00 |              41.00 |                      0.90 |                    0.84 |                       2.27 |                     1.50 |                     93.24 |                   61.53 |
| 2024      |                12.00 |              12.00 |                      0.93 |                    1.10 |                       2.00 |                     2.26 |                     24.04 |                   27.06 |
| 2025      |                12.00 |              12.00 |                      0.43 |                    0.13 |                       1.35 |                     0.27 |                     16.16 |                    3.26 |
| 2026      |                10.00 |              10.00 |                      1.92 |                    1.92 |                       4.40 |                     3.34 |                     44.01 |                   33.41 |

Hit rates, `fix_follow_reb` (candidate, not selected) and `bench_fix_follow` (round-1 rule, not a candidate):
| period    |   decisions |   decisions_per_year |   hit_net |   hit_sign_gross |   episodes |   episodes_per_year |   episode_hit_net |   episode_hit_gross |   mean_net_bp_per_decision |   mean_gross_bp_per_decision |
|:----------|------------:|---------------------:|----------:|-----------------:|-----------:|--------------------:|------------------:|--------------------:|---------------------------:|-----------------------------:|
| 2010-2026 |          87 |                5.163 |     0.563 |            0.575 |         87 |               5.163 |             0.563 |               0.575 |                      2.852 |                        3.879 |
| 2016-2026 |          60 |                5.530 |     0.567 |            0.567 |         60 |               5.530 |             0.567 |               0.567 |                      2.844 |                        3.912 |
| 2023-2026 |          20 |                5.195 |     0.650 |            0.650 |         20 |               5.195 |             0.650 |               0.650 |                      3.077 |                        4.154 |

| period    |   decisions |   decisions_per_year |   hit_net |   hit_sign_gross |   episodes |   episodes_per_year |   episode_hit_net |   episode_hit_gross |   mean_net_bp_per_decision |   mean_gross_bp_per_decision |
|:----------|------------:|---------------------:|----------:|-----------------:|-----------:|--------------------:|------------------:|--------------------:|---------------------------:|-----------------------------:|
| 2010-2026 |         195 |               11.573 |     0.544 |            0.574 |        195 |              11.573 |             0.544 |               0.574 |                      2.077 |                        3.096 |
| 2016-2026 |         123 |               11.336 |     0.553 |            0.561 |        123 |              11.336 |             0.553 |               0.561 |                      2.347 |                        3.416 |
| 2023-2026 |          41 |               10.649 |     0.585 |            0.585 |         41 |              10.649 |             0.585 |               0.585 |                      2.274 |                        3.353 |

Cost sensitivity of the unconditional rule (2010-26 / 2016-26 / 2023-26 Sharpe): 0.6 pips 0.70 / 0.74 / 1.11; 1.2 pips 0.55 / 0.60 / 0.90;
2.0 pips 0.36 / 0.42 / 0.62; 3.0 pips 0.11 / 0.19 / 0.27. Break-even is about 3.4 pips per round trip, and spreads at the month-end fix are
wider than on a normal afternoon, so the 1.2-pip headline is optimistic for this particular quarter of an hour.
The brief for this arm described the rule as "about zero after costs"; round 1's own table has t after cost of 1.6 / 1.4 / 1.8 in the three periods, which is the
same result as here. It was one of roughly 290 round-1 trials and every era shown here was already seen in round 1, so this is a replication
with a month-end-specificity check added, not new out-of-sample evidence.

## (2) New-month reversal
`nm_rev_sig` 0.26 / 0.21 / -0.10 (t 1.1) and `nm_rev_px` 0.24 / 0.16 / 0.54 (t 1.0); gross +7.9 and +7.4 bp per month over two sessions,
hit 54 %. Right sign, far from significant, and the two variants disagree about 2023-2026. Not usable alone.

## (3) Seasonality: month-of-year stability (ECB fixing, month-end to month-end, bp; pre-1999 = -dlog(CHF per USD) from the Fed H.10 file)
The datahub H.10 file has no DEM column (AUD, CAD, EUR from 1999, JPY, CHF, GBP), so the pre-1999 proxy is USD/CHF, which shadowed the D-mark.
It is a proxy for the dollar leg, not EUR/USD, and is shown as supporting evidence only.

|   month | 1975-1998 (CHF proxy)   | 1999-2009              | 2010-2017             | 2018-2026             | 1999-2026               | same sign 1999-09 / 2010-17 / 2018-26   | ... and in the pre-1999 proxy   |
|--------:|:------------------------|:-----------------------|:----------------------|:----------------------|:------------------------|:----------------------------------------|:--------------------------------|
|       1 | -181 (t -2.6, up 9/24)  | -142 (t -1.3, up 3/10) | -38 (t -0.3, up 5/8)  | +11 (t +0.2, up 5/9)  | -60 (t -1.1, up 13/27)  | no                                      | no                              |
|       2 | +15 (t +0.2, up 13/24)  | -20 (t -0.4, up 5/11)  | -40 (t -0.5, up 3/8)  | -66 (t -2.3, up 2/9)  | -40 (t -1.4, up 10/28)  | YES                                     | no                              |
|       3 | -43 (t -0.5, up 12/24)  | +11 (t +0.1, up 6/11)  | -5 (t -0.0, up 3/8)   | -19 (t -0.2, up 3/9)  | -3 (t -0.1, up 12/28)   | no                                      | no                              |
|       4 | +3 (t +0.0, up 9/24)    | +7 (t +0.1, up 5/11)   | +140 (t +1.8, up 6/8) | +20 (t +0.2, up 4/9)  | +49 (t +1.0, up 15/28)  | YES                                     | YES                             |
|       5 | -18 (t -0.4, up 12/24)  | +100 (t +0.9, up 6/11) | -269 (t -2.3, up 1/8) | -13 (t -0.2, up 4/9)  | -41 (t -0.6, up 11/28)  | no                                      | no                              |
|       6 | +21 (t +0.3, up 13/24)  | +26 (t +0.3, up 5/11)  | +73 (t +2.3, up 6/8)  | -22 (t -0.3, up 4/9)  | +24 (t +0.6, up 15/28)  | no                                      | no                              |
|       7 | +63 (t +0.7, up 11/24)  | +4 (t +0.1, up 6/11)   | +30 (t +0.3, up 4/8)  | +39 (t +0.5, up 6/9)  | +23 (t +0.5, up 16/28)  | YES                                     | YES                             |
|       8 | +69 (t +1.3, up 15/24)  | -55 (t -0.6, up 6/11)  | +34 (t +0.5, up 5/8)  | +3 (t +0.1, up 4/9)   | -11 (t -0.3, up 15/28)  | no                                      | no                              |
|       9 | +180 (t +2.6, up 17/24) | +76 (t +0.9, up 6/11)  | +5 (t +0.0, up 4/8)   | -129 (t -2.9, up 2/9) | -11 (t -0.2, up 12/28)  | no                                      | no                              |
|      10 | +64 (t +0.7, up 15/24)  | -118 (t -1.0, up 5/11) | +14 (t +0.2, up 4/8)  | -39 (t -0.6, up 4/9)  | -55 (t -1.0, up 13/28)  | no                                      | no                              |
|      11 | -35 (t -0.4, up 11/24)  | +103 (t +1.3, up 7/11) | -205 (t -2.1, up 1/8) | +41 (t +0.4, up 5/8)  | -7 (t -0.1, up 13/27)   | no                                      | no                              |
|      12 | +118 (t +1.8, up 14/24) | +209 (t +1.7, up 6/11) | +31 (t +0.4, up 5/8)  | +111 (t +2.1, up 6/8) | +127 (t +2.2, up 17/27) | YES                                     | YES                             |

Months with the same sign in 1999-2009, 2010-2017 and 2018-2026: **4 of 12** (February -, April +, July +, December +); 3 expected
by chance (each month has probability 1/4). Adding the pre-1999 proxy: 3 (April, July, December); 1.5 expected.

Joint test of "any month-of-year effect" (`sum_t2` = sum of the 12 squared month t-stats; `JS_factor` = the shrinkage weight the data earn):
| era                   |   sum_t2 |   expected_under_null |   chi2_p_naive |   anova_F |   anova_p |   JS_factor |
|:----------------------|---------:|----------------------:|---------------:|----------:|----------:|------------:|
| 1975-1998 (CHF proxy) |   19.931 |                13.143 |          0.110 |     1.456 |     0.148 |       0.450 |
| 1999-2009             |    9.825 |                15.032 |          0.797 |     1.145 |     0.333 |       0.000 |
| 2010-2017             |   19.156 |                16.800 |          0.321 |     1.393 |     0.191 |       0.269 |
| 2018-2026             |   18.931 |                16.114 |          0.295 |     0.742 |     0.696 |       0.291 |
| 1999-2026             |   11.166 |                12.970 |          0.587 |     1.057 |     0.396 |       0.032 |

The 12 month t-stats of 1999-2026 are NARROWER than noise (sum of squares 11.2 against 13.0 expected). Only December exceeds |t| = 2 (t 2.2),
which is what the largest of 12 noise t-stats looks like. Walk-forward shrinkage factor by test year: 2010: 0.000, 2011: 0.000, 2012: 0.000, 2013: 0.000, 2014: 0.000, 2015: 0.000, 2016: 0.000, 2017: 0.000, 2018: 0.000, 2019: 0.000, 2020: 0.000, 2021: 0.000, 2022: 0.000, 2023: 0.000, 2024: 0.000, 2025: 0.000, 2026: 0.005.
Training-window month t-stats for four test years:
|   month |   2010 |   2016 |   2023 |   2026 |
|--------:|-------:|-------:|-------:|-------:|
|    1.00 |  -1.33 |  -1.41 |  -1.16 |  -1.16 |
|    2.00 |  -0.39 |  -0.46 |  -1.05 |  -1.26 |
|    3.00 |   0.13 |  -0.39 |  -0.33 |   0.13 |
|    4.00 |   0.09 |   0.91 |   0.55 |   0.89 |
|    5.00 |   0.88 |  -0.65 |  -0.52 |  -0.62 |
|    6.00 |   0.34 |   0.87 |   0.52 |   0.83 |
|    7.00 |   0.07 |   0.00 |   0.44 |   0.44 |
|    8.00 |  -0.65 |  -0.41 |  -0.63 |  -0.35 |
|    9.00 |   0.91 |   0.58 |   0.00 |  -0.05 |
|   10.00 |  -1.02 |  -0.62 |  -0.66 |  -0.94 |
|   11.00 |   1.31 |  -0.31 |  -0.12 |  -0.12 |
|   12.00 |   1.73 |   1.67 |   2.17 |   2.20 |

The two legs of the live `season` rule, and the January prior (one observation per year, gross bp, sign-adjusted so that + = the rule earns):
| leg                                         | 1975-1998 (CHF proxy)            | 1999-2009                        | 2010-2015 (round-1 TRAIN, in-sample for the rule)   | 2016-2026 (after the rule was chosen)   | 1999-2026                        | 1975-2026 pooled (proxy + ECB)   |
|:--------------------------------------------|:---------------------------------|:---------------------------------|:----------------------------------------------------|:----------------------------------------|:---------------------------------|:---------------------------------|
| December long                               | +117.64 (t +1.8, hit 0.58, n 24) | +209.10 (t +1.7, hit 0.55, n 11) | +35.36 (t +0.3, hit 0.67, n 6)                      | +92.27 (t +2.0, hit 0.70, n 10)         | +127.22 (t +2.2, hit 0.63, n 27) | +122.71 (t +2.9, hit 0.61, n 51) |
| May short                                   | +18.30 (t +0.4, hit 0.50, n 24)  | -100.28 (t -0.9, hit 0.45, n 11) | +365.67 (t +3.1, hit 1.00, n 6)                     | +6.46 (t +0.1, hit 0.55, n 11)          | +41.50 (t +0.6, hit 0.61, n 28)  | +30.79 (t +0.7, hit 0.56, n 52)  |
| January short (prior: reversal of December) | +180.75 (t +2.6, hit 0.62, n 24) | +141.96 (t +1.3, hit 0.70, n 10) | +88.89 (t +0.6, hit 0.50, n 6)                      | -29.65 (t -0.5, hit 0.36, n 11)         | +60.25 (t +1.1, hit 0.52, n 27)  | +116.96 (t +2.6, hit 0.57, n 51) |

Answer to "real effect or two lucky months": **one of each.**
* December long: positive in 1975-98 (proxy), 1999-2009, 2010-2015 and 2016-2026; pooled t 2.9 over 51 years, hit 61 %; +92 bp (7/10) in the
  ten Decembers after round 1 fixed the rule. As a daily stream 2010-26 / 2016-26 / 2023-26 Sharpe 0.29 / 0.46 / 0.07. Weak but consistent.
* May short: +366 bp in 2010-2015 with 6 of 6 (Greek crisis Mays), which is inside round 1's TRAIN window where the rule was found; -100 bp in
  1999-2009, +18 bp in the proxy era, +6 bp (6/11) in 2016-2026. Daily stream 0.52 / 0.02 / 0.26, i.e. all of it from 2010-2015. Lucky.
* A walk-forward investor in 2010 would not have shorted May (training t +0.9) and would have held December at t 1.7 with zero shrunk weight.
  The 2010-2015 Sharpe of 0.93 of the live rule is in-sample; its honest record is 2016-2026: 0.31 (t about 1.0).
* January short had the strongest pre-1999 record (t 2.6) and has faded (4/11 since 2016).

## (4) IMM roll weeks and option-expiry Fridays
`imm_fade_cot` -0.46 / -0.62 / -0.75 (t -1.9): the prior is rejected. It is the positioning arm with the sign flipped (P&L correlation with
`regime_trend` on active days -0.89). Following positioning inside vs outside the roll window (gross bp per session):
| window             | 2003-2009                        | 2010-2015                        | 2016-2026                        | 2010-2026                        |
|:-------------------|:---------------------------------|:---------------------------------|:---------------------------------|:---------------------------------|
| IMM roll window    | -10.14 (t -1.8, hit 0.50, n 140) | +2.43 (t +0.5, hit 0.48, n 120)  | +6.47 (t +2.0, hit 0.53, n 215)  | +5.02 (t +1.8, hit 0.51, n 335)  |
| all other sessions | +2.21 (t +1.4, hit 0.51, n 1673) | +2.91 (t +1.8, hit 0.53, n 1436) | +1.51 (t +1.7, hit 0.51, n 2601) | +2.01 (t +2.5, hit 0.52, n 4037) |

Positioning-following is, if anything, stronger in the roll window after 2010 (+5.0 vs +2.0 bp, difference t about 1); nothing to trade separately.
Opex Fridays: -0.3 bp (t -0.1, n 285) against -1.8 bp on other Fridays: nothing (table below).

## (5) Holidays and (6) central-bank blackouts: descriptive (unconditional long EUR/USD, bp per session; `|r|` = mean absolute return)
| window (unconditional long EUR, bp per session)   | 2003-2009                     | 2010-2017                     | 2018-2026                     | 2003-2026                     |
|:--------------------------------------------------|:------------------------------|:------------------------------|:------------------------------|:------------------------------|
| IMM roll window (5 sessions to LTD)               | +3.7 (t +0.6, n 140, |r| 51)  | +4.5 (t +1.0, n 160, |r| 43)  | -0.2 (t -0.0, n 175, |r| 37)  | +2.5 (t +1.0, n 475, |r| 43)  |
| IMM week (Mon-Fri around 3rd Wed)                 | +6.9 (t +1.0, n 140, |r| 57)  | +2.0 (t +0.4, n 160, |r| 46)  | -4.3 (t -1.1, n 175, |r| 37)  | +1.1 (t +0.4, n 475, |r| 46)  |
| opex Friday (3rd Friday)                          | +4.9 (t +0.6, n 83, |r| 52)   | -1.7 (t -0.3, n 96, |r| 44)   | -3.1 (t -0.9, n 106, |r| 29)  | -0.3 (t -0.1, n 285, |r| 41)  |
| other Fridays                                     | -1.5 (t -0.4, n 278, |r| 53)  | -1.9 (t -0.5, n 319, |r| 48)  | -2.0 (t -0.8, n 354, |r| 34)  | -1.8 (t -1.0, n 951, |r| 44)  |
| pre-holiday session (US or TARGET)                | +1.2 (t +0.2, n 80, |r| 52)   | -2.4 (t -0.5, n 93, |r| 37)   | -5.3 (t -1.3, n 108, |r| 32)  | -2.5 (t -0.8, n 281, |r| 39)  |
| pre-US-holiday session                            | -1.1 (t -0.1, n 75, |r| 52)   | -4.7 (t -1.0, n 88, |r| 37)   | -5.8 (t -1.3, n 101, |r| 31)  | -4.1 (t -1.3, n 264, |r| 39)  |
| pre-TARGET-holiday session                        | -4.4 (t -0.4, n 23, |r| 45)   | +9.4 (t +1.1, n 25, |r| 35)   | -6.4 (t -0.9, n 29, |r| 30)   | -0.7 (t -0.1, n 77, |r| 36)   |
| post-holiday session                              | +4.3 (t +0.5, n 82, |r| 58)   | -8.1 (t -1.4, n 93, |r| 45)   | -7.7 (t -1.8, n 108, |r| 35)  | -4.4 (t -1.3, n 283, |r| 45)  |
| year-end week (Dec 24 - Jan 2)                    | +12.4 (t +1.7, n 38, |r| 37)  | +1.3 (t +0.2, n 45, |r| 32)   | -2.1 (t -0.4, n 51, |r| 27)   | +3.2 (t +0.9, n 134, |r| 32)  |
| December 1-23                                     | +6.9 (t +1.0, n 116, |r| 52)  | -0.3 (t -0.1, n 132, |r| 42)  | +4.7 (t +1.4, n 131, |r| 30)  | +3.6 (t +1.2, n 379, |r| 41)  |
| May                                               | +5.8 (t +1.1, n 154, |r| 52)  | -12.5 (t -2.5, n 177, |r| 49) | -0.5 (t -0.2, n 198, |r| 32)  | -2.7 (t -1.1, n 529, |r| 43)  |
| Fed blackout (10d before FOMC)                    | +1.1 (t +0.3, n 339, |r| 50)  | +0.5 (t +0.2, n 814, |r| 43)  | -1.6 (t -1.0, n 743, |r| 33)  | -0.2 (t -0.2, n 1896, |r| 40) |
| ECB quiet week                                    | -1.6 (t -0.5, n 338, |r| 48)  | -1.5 (t -0.7, n 792, |r| 43)  | +1.5 (t +0.7, n 468, |r| 33)  | -0.6 (t -0.5, n 1598, |r| 41) |
| any blackout                                      | +0.4 (t +0.2, n 622, |r| 49)  | -0.7 (t -0.4, n 1286, |r| 43) | -0.9 (t -0.6, n 1027, |r| 34) | -0.5 (t -0.5, n 2935, |r| 41) |
| no blackout                                       | +2.6 (t +1.4, n 1191, |r| 48) | -1.1 (t -0.5, n 788, |r| 45)  | +0.1 (t +0.1, n 1271, |r| 33) | +0.7 (t +0.7, n 3250, |r| 42) |
| all sessions                                      | +1.8 (t +1.2, n 1813, |r| 49) | -0.9 (t -0.7, n 2074, |r| 44) | -0.3 (t -0.4, n 2298, |r| 33) | +0.1 (t +0.2, n 6185, |r| 41) |

No window has a directional mean distinguishable from zero in the full sample. Post-holiday sessions are negative after 2010 (-8.1, -7.7 bp;
t -1.4, -1.8) but positive before; pre-holiday squaring (`hol_square`) is -0.25 / 0.00 / 0.51 with a 43 % hit rate: rejected. The year-end week
is quieter (|r| 32 vs 41 bp) without drift. Blackout windows have the same mean and the same absolute return as other days (41.1 vs 41.6 bp).

## (7) Treasury refunding / auction settlement
Skipped. Both official sources of auction and settlement dates time out through the proxy; a rule-based calendar (15th and month-end) would not
be the "clean date list" asked for and month-end is already covered above.

## Incremental value against the live combination
`eurusd.arms.meta.combine(..., "EW")` / `report_combo`, net Sharpe:
| combo                                               |   2010-2026 |   2016-2026 |   2023-2026 |   2013-2026 |
|:----------------------------------------------------|------------:|------------:|------------:|------------:|
| weak_signals+regime_trend                           |       0.563 |       0.636 |       0.356 |       0.622 |
| weak_signals+regime_trend+reb_d3                    |       0.554 |       0.624 |       0.302 |       0.611 |
| weak_signals+regime_trend+reb_d1                    |       0.556 |       0.636 |       0.356 |       0.613 |
| weak_signals+regime_trend+reb_d3_lin                |       0.515 |       0.569 |       0.309 |       0.568 |
| weak_signals+regime_trend+nm_rev_sig                |       0.568 |       0.639 |       0.232 |       0.627 |
| weak_signals+regime_trend+nm_rev_px                 |       0.551 |       0.650 |       0.617 |       0.607 |
| weak_signals+regime_trend+season_js                 |       0.563 |       0.636 |       0.356 |       0.622 |
| weak_signals+regime_trend+imm_fade_cot              |       0.563 |       0.636 |       0.356 |       0.622 |
| weak_signals+regime_trend+hol_square                |       0.563 |       0.636 |       0.356 |       0.622 |
| weak_signals+regime_trend+blackout_trend            |       0.364 |       0.418 |       0.351 |       0.401 |
| weak_signals+regime_trend+flows_core                |       0.578 |       0.665 |       0.274 |       0.638 |
| weak_signals+regime_trend+fix_reb                   |       0.563 |       0.636 |       0.356 |       0.622 |
| weak_signals+regime_trend+fix_follow_reb            |       0.696 |       0.776 |       0.626 |       0.768 |
| weak_signals+regime_trend+bench_fix_follow          |       0.777 |       0.824 |       0.632 |       0.858 |
| weak_signals+regime_trend+bench_live_season_dec_may |       0.634 |       0.684 |       0.410 |       0.700 |
| weak_signals+regime_trend+bench_live_tom            |       0.446 |       0.468 |       0.328 |       0.492 |

The first row is the live pair. The official test is the `blackout_trend` row (the final): 0.36 / 0.42 / 0.35, **worse** than 0.56 / 0.64 / 0.36;
verified from the saved positions file. Rows identical to the pair mean the stream never had a positive trailing t-stat and got zero weight.
For information: `fix_follow_reb` (candidate, not selected) 0.70 / 0.78 / 0.63 and the round-1 unconditional rule 0.78 / 0.82 / 0.63. Note that
`meta.combine` scales every stream to the same daily volatility, which hands a 12-decisions-a-year stream a very large position on its active
days; the size of that improvement is an artefact of the scaling, the sign of it (positive, uncorrelated) is what carries over.

Daily-P&L correlations with the two live arms (2010-2026, all days / active days only / 2016-2026):
| variant                   |   corr_weak_signals |   corr_regime_trend |   corr_ws_active_days |   corr_rt_active_days |   corr_2016_2026_ws |   corr_2016_2026_rt |
|:--------------------------|--------------------:|--------------------:|----------------------:|----------------------:|--------------------:|--------------------:|
| reb_d3                    |              -0.146 |              -0.060 |                -0.344 |                -0.144 |              -0.148 |               0.011 |
| reb_d1                    |              -0.086 |               0.000 |                -0.270 |                 0.002 |              -0.078 |              -0.017 |
| reb_d3_lin                |              -0.153 |              -0.044 |                -0.359 |                -0.106 |              -0.181 |               0.003 |
| nm_rev_sig                |               0.131 |               0.004 |                 0.328 |                 0.013 |               0.146 |              -0.002 |
| nm_rev_px                 |              -0.031 |              -0.035 |                -0.079 |                -0.087 |              -0.091 |              -0.026 |
| season_js                 |               0.027 |              -0.077 |                 0.172 |                -0.416 |               0.038 |              -0.098 |
| imm_fade_cot              |              -0.072 |              -0.271 |                -0.260 |                -0.892 |              -0.081 |              -0.304 |
| hol_square                |              -0.031 |              -0.033 |                -0.136 |                -0.135 |              -0.029 |              -0.025 |
| blackout_trend            |               0.272 |               0.220 |                 0.337 |                 0.269 |               0.237 |               0.175 |
| flows_core                |              -0.024 |              -0.042 |                -0.044 |                -0.076 |              -0.017 |               0.007 |
| fix_reb                   |               0.005 |               0.010 |                 0.024 |                 0.043 |              -0.002 |               0.028 |
| fix_follow_reb            |               0.015 |               0.022 |                 0.113 |                 0.148 |               0.017 |               0.034 |
| bench_fix_follow          |               0.006 |               0.037 |                 0.016 |                 0.173 |               0.019 |               0.056 |
| bench_live_season_dec_may |               0.164 |              -0.053 |                 0.399 |                -0.132 |               0.192 |              -0.065 |
| bench_live_tom            |               0.075 |               0.042 |                 0.133 |                 0.074 |               0.051 |              -0.083 |

### Should the flow signals REPLACE `season` and `tom` in the weak-signal stream?
The live stream already contains `season` (Dec +1 / May -1) and `tom` (short T-1..T+3). Re-run of its final variant (`tstat_sign`) in-process
with the inputs swapped (`fc_season` = `season_js`, `fc_monthend` = `reb_d3` + `nm_rev_sig`; the weak_signals module and files are untouched):
| weak_signals_inputs           |   n_signals |   SR_2010_2026 |   t_2010_2026 |   SR_2016_2026 |   SR_2023_2026 |   EW_with_regime_trend_2010_2026 |   EW_with_regime_trend_2016_2026 |   EW_with_regime_trend_2023_2026 |
|:------------------------------|------------:|---------------:|--------------:|---------------:|---------------:|---------------------------------:|---------------------------------:|---------------------------------:|
| original_14                   |          14 |          0.678 |         2.825 |          0.427 |          0.265 |                            0.563 |                            0.636 |                            0.356 |
| drop_season_tom               |          12 |          0.525 |         2.188 |          0.356 |          0.207 |                            0.519 |                            0.588 |                            0.316 |
| replace_season_tom_with_flows |          14 |          0.616 |         2.566 |          0.502 |          0.507 |                            0.586 |                            0.680 |                            0.496 |
| replace_season_only           |          14 |          0.495 |         2.061 |          0.368 |          0.295 |                            0.477 |                            0.600 |                            0.368 |
| replace_tom_only              |          14 |          0.701 |         2.922 |          0.541 |          0.464 |                            0.604 |                            0.710 |                            0.482 |
| add_flows_keep_originals      |          16 |          0.688 |         2.864 |          0.435 |          0.459 |                            0.570 |                            0.646 |                            0.480 |

* `season` -> shrinkage version: **no**, in back-test terms. `season_js` is zero, so this equals dropping `season` (0.50 / 0.37 / 0.30 against
  0.68 / 0.43 / 0.27). But the 0.19 lost over 2010-2026 is almost all May 2010-2015; over 2016-2026 the loss is 0.06. The defensible change is
  to keep December and drop May, which is a post-hoc choice and belongs in the forward paper test, not in the back-test.
* `tom` -> month-end flow version: marginally better on every window (0.70 / 0.54 / 0.46; with `regime_trend` 0.60 / 0.71 / 0.48 against
  0.56 / 0.64 / 0.36). It is one of five configurations tried, its components are individually insignificant (`reb_d3` t 0.1, `nm_rev_sig`
  t 1.1) and a Sharpe difference of 0.1 over eleven years is well inside the noise. **Not a case for replacing**; `tom` itself is dead since 2016
  (-0.15) and could simply be dropped at no cost (the weak-signals ablation already showed that).
* Correlation of my candidates with the live stream is low throughout (|rho| < 0.3; the live `season` rule itself is 0.16 with weak_signals).

## Leak checks
| check                                                                                 | variant        |   SR_2010_2026 |   t_2010_2026 |   SR_2016_2026 |   SR_2023_2026 |   sd_across_shuffles |
|:--------------------------------------------------------------------------------------|:---------------|---------------:|--------------:|---------------:|---------------:|---------------------:|
| actual                                                                                | reb_d3         |          0.031 |         0.127 |          0.078 |         -0.002 |              nan     |
| actual                                                                                | reb_d1         |         -0.117 |        -0.486 |         -0.088 |          0.388 |              nan     |
| actual                                                                                | reb_d3_lin     |          0.019 |         0.079 |          0.049 |          0.244 |              nan     |
| actual                                                                                | nm_rev_sig     |          0.264 |         1.102 |          0.211 |         -0.096 |              nan     |
| actual                                                                                | nm_rev_px      |          0.241 |         1.004 |          0.164 |          0.544 |              nan     |
| actual                                                                                | season_js      |          0.027 |         0.114 |          0.034 |          0.057 |              nan     |
| actual                                                                                | imm_fade_cot   |         -0.463 |        -1.927 |         -0.621 |         -0.748 |              nan     |
| actual                                                                                | hol_square     |         -0.252 |        -1.049 |         -0.001 |          0.513 |              nan     |
| actual                                                                                | blackout_trend |          0.173 |         0.719 |         -0.253 |          0.105 |              nan     |
| actual                                                                                | flows_core     |          0.207 |         0.864 |          0.208 |         -0.061 |              nan     |
| actual                                                                                | fix_reb        |         -0.284 |        -1.144 |          0.001 |          0.101 |              nan     |
| actual                                                                                | fix_follow_reb |          0.479 |         1.930 |          0.471 |          0.845 |              nan     |
| shuffled_labels_mean_of_20                                                            | reb_d3         |          0.046 |       nan     |        nan     |        nan     |                0.198 |
| shuffled_labels_mean_of_20                                                            | reb_d1         |         -0.061 |       nan     |        nan     |        nan     |                0.192 |
| shuffled_labels_mean_of_20                                                            | reb_d3_lin     |          0.017 |       nan     |        nan     |        nan     |                0.167 |
| shuffled_labels_mean_of_20                                                            | nm_rev_sig     |         -0.103 |       nan     |        nan     |        nan     |                0.209 |
| shuffled_labels_mean_of_20                                                            | nm_rev_px      |         -0.032 |       nan     |        nan     |        nan     |                0.210 |
| shuffled_labels_mean_of_20                                                            | season_js      |          0.015 |       nan     |        nan     |        nan     |                0.184 |
| shuffled_labels_mean_of_20                                                            | imm_fade_cot   |         -0.024 |       nan     |        nan     |        nan     |                0.254 |
| shuffled_labels_mean_of_20                                                            | hol_square     |         -0.081 |       nan     |        nan     |        nan     |                0.196 |
| shuffled_labels_mean_of_20                                                            | blackout_trend |         -0.141 |       nan     |        nan     |        nan     |                0.248 |
| shuffled_labels_mean_of_20                                                            | flows_core     |          0.004 |       nan     |        nan     |        nan     |                0.215 |
| shuffled_labels_mean_of_20                                                            | fix_reb        |         -0.073 |       nan     |        nan     |        nan     |                0.266 |
| shuffled_labels_mean_of_20                                                            | fix_follow_reb |         -0.220 |       nan     |        nan     |        nan     |                0.248 |
| signal_shifted_one_period (prev month's equity signal / prev month's season estimate) | reb_d3         |          0.180 |         0.748 |          0.165 |         -0.567 |              nan     |
| signal_shifted_one_period (prev month's equity signal / prev month's season estimate) | reb_d1         |          0.258 |         1.073 |          0.521 |          0.085 |              nan     |
| signal_shifted_one_period (prev month's equity signal / prev month's season estimate) | reb_d3_lin     |          0.210 |         0.875 |          0.282 |         -0.427 |              nan     |
| signal_shifted_one_period (prev month's equity signal / prev month's season estimate) | nm_rev_sig     |          0.206 |         0.859 |          0.321 |          0.741 |              nan     |
| signal_shifted_one_period (prev month's equity signal / prev month's season estimate) | season_js      |          0.314 |         1.306 |          0.391 |          0.656 |              nan     |
| signal_shifted_one_period (prev month's equity signal / prev month's season estimate) | flows_core     |          0.282 |         1.173 |          0.346 |          0.174 |              nan     |
| positions_one_session_late                                                            | reb_d3         |         -0.304 |        -1.267 |         -0.011 |         -0.009 |              nan     |
| positions_one_session_late                                                            | reb_d1         |         -0.218 |        -0.908 |         -0.247 |          0.167 |              nan     |
| positions_one_session_late                                                            | reb_d3_lin     |         -0.431 |        -1.796 |         -0.155 |          0.192 |              nan     |
| positions_one_session_late                                                            | nm_rev_sig     |          0.083 |         0.348 |          0.337 |          0.742 |              nan     |
| positions_one_session_late                                                            | nm_rev_px      |          0.039 |         0.165 |          0.120 |         -0.201 |              nan     |
| positions_one_session_late                                                            | season_js      |          0.040 |         0.167 |          0.050 |          0.084 |              nan     |
| positions_one_session_late                                                            | imm_fade_cot   |         -0.364 |        -1.518 |         -0.635 |         -1.076 |              nan     |
| positions_one_session_late                                                            | hol_square     |         -0.054 |        -0.225 |         -0.284 |         -0.152 |              nan     |
| positions_one_session_late                                                            | blackout_trend |         -0.054 |        -0.225 |         -0.271 |          0.020 |              nan     |
| positions_one_session_late                                                            | flows_core     |         -0.159 |        -0.662 |          0.222 |          0.502 |              nan     |
| LOOKAHEAD_CONTROL positions from the next session's signal                            | blackout_trend |          2.006 |         8.355 |          1.877 |          1.241 |              nan     |
| LOOKAHEAD_CONTROL positions from the next session's signal                            | hol_square     |         -1.133 |        -4.718 |         -0.805 |         -0.696 |              nan     |
| LOOKAHEAD_CONTROL positions from the next session's signal                            | nm_rev_px      |         -0.943 |        -3.927 |         -0.811 |         -0.261 |              nan     |
| signal_shifted_one_period (prev month's equity signal / prev month's season estimate) | fix_reb        |          0.064 |         0.256 |          0.364 |          0.315 |              nan     |
| signal_shifted_one_period (prev month's equity signal / prev month's season estimate) | fix_follow_reb |          0.548 |         2.208 |          0.758 |          0.460 |              nan     |
| LOOKAHEAD_CONTROL rel measured through T, unlagged                                    | reb_d3         |          0.222 |         0.925 |          0.285 |          0.255 |              nan     |
| LOOKAHEAD_CONTROL perfect foresight on the 3 month-end sessions                       | reb_d3         |          4.719 |        19.654 |          4.798 |          4.866 |              nan     |

1. **Shuffled labels** (20 permutations each; `fwd_1d` permuted for the daily variants, the ECB training months permuted for `season_js`, the
   fix-window label returns permuted independently of the signal window): means between -0.22 and +0.05 with a standard error of about 0.05.
   The negative ones are the cost drag of rules that trade without information (`fix_follow_reb` -0.22, `blackout_trend` -0.14); none is positive.
   First attempt permuted the three fix-window returns together, which preserved the 15:00-15:45 -> 15:45-16:00 dependence and gave +0.26 for
   `fix_follow_reb`; that was the check being wrong, and it is also direct evidence that the edge is the intraday continuation, not the equity sign.
2. **Signals shifted forward by one period.** Final variant one session late: 0.17 -> -0.05 (there was little to lose). Month-end variants with
   the PREVIOUS month's equity sign: `reb_d3` 0.18, `reb_d1` 0.26, `fix_reb` 0.06, i.e. a stale signal does as well as or better than the real
   one, and `fix_follow_reb` keeps 0.55 (t 2.2) with a stale equity sign. That is the cleanest evidence in this report that the equity conditioning
   carries no information. Look-ahead controls: next-session signal gives `blackout_trend` 2.0 (t 8.4), and perfect foresight on the three
   month-end sessions gives 4.7 (t 20), so the harness exposes a look-ahead loudly. Even the unlagged equity signal measured through T gives
   only 0.22: relative equity performance is simply unrelated to EUR/USD in these windows.
3. **Signals vs labels** (none is a label in disguise; all |corr| <= 0.04):
| signal vs label                      |   corr |        n |
|:-------------------------------------|-------:|---------:|
| rel@T-3 vs sum fwd (T-2..T)          |  0.013 |  236.000 |
| rel (all rows) vs fwd_1d             | -0.041 | 5085.000 |
| -cot_z52 (IMM rows) vs fwd_1d        | -0.032 |  475.000 |
| -ret_5d (pre-holiday rows) vs fwd_1d |  0.030 |  281.000 |
| ret_21d (blackout rows) vs fwd_1d    |  0.016 | 2924.000 |
| season_js position vs fwd_1d         |  0.001 | 4372.000 |
| rel@fix vs r_1500_1600               |  0.008 |  228.000 |
   All inputs are feature-store columns (lagged as in `featstore.build_daily`) or deterministic calendars; the only `shift(-1)` columns are the
   NEXT session's close date and month (calendar). `bd_to_end` uses the number of sessions in the month, which is known in advance except for the
   seven source-data gaps noted above.

## New data
* `data/processed/cross/gdaxi_D1.parquet`, `n225_D1.parquet`, `ftse_D1.parquet`: Yahoo chart API (`^GDAXI`, `^N225`, `^FTSE`, browser User-Agent),
  1990-01-02 .. 2026-11-10, daily OHLC, index = session open in UTC (same layout as `sx5e_D1.parquet`). Used for diagnostics only (DAX
  pre-2007 history, rest-of-world basket). Publication lag used: one calendar day (close stamped <= session close date - 1).
  `^GDAXI` is a total-return index, which biases MTD comparisons by about +0.25 % a month; it is not used in any candidate.
* `data/processed/flows_calendar_fix_windows.parquet`: cache of 14:45-16:00 London M5 prices per weekday, 2000-05 .. 2026-11.
* `ecb_EURUSD_D1.csv` (1999+) for month-of-year estimates; `datahub_fx_fed_h10_daily.csv` CHF column for the pre-1999 proxy.

## What helped, what did not, what is suspicious
* Helped: nothing new. The one robust object in this arm is round 1's month-end fix continuation, now shown to be specific to the last
  business day and independent of relative equity performance.
* Did not help: MTD relative equity performance in any window or form; quarter-end splits; IMM, opex, holiday and blackout calendars;
  data-driven month-of-year estimates.
* Suspicious / caveats: (a) the selection rule picked the candidate whose 2010-2015 number was two good years, and the candidate that passes the
  bar numerically (`fix_follow_reb`: 2016-2026 0.47, 2023-2026 0.84, three-way 0.78 > 0.64) was ranked second; I have not swapped them.
  Its deflated-Sharpe p is 0.36 for 12 trials and its t is 1.9. (b) The fix result rests on bid prices and a flat 1.2-pip cost at the most
  crowded quarter of an hour of the month. (c) Month-end counts are small: 195 events, 41 in 2023-2026. (d) The tables above contain several
  hundred cells; any single cell with |t| near 2 (January's first sessions, post-holiday sessions, February) is expected by chance.
* If the lead wants to carry anything forward: the unconditional month-end fix-follow as a separately named tactical paper scenario with its
  real spread recorded, and a December-only `season` as a forward-test variant. Neither is a result of this arm's protocol.
