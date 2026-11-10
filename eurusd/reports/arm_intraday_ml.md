# Arm B: intraday_ml - context-conditioned intraday prediction at fixed decision times

## Idea
Round 1 found one robust intraday regularity (short EUR/USD 07:00-13:00 London) and that hour-of-day patterns drift.
This arm asks whether a model conditioned on the day's context predicts the London session, the London/NY overlap and
the overnight session better than the unconditional rule. Decision bars (hourly feature store, index = bar start):
L07 = bar closing 07:00 London (`hour_london == 6`), L13 = bar closing 13:00 London (`hour_london == 12`),
NY17 = bar closing 17:00 New York (`hour_ny == 16`); weekend bars dropped. Targets `fwd_4h`, `fwd_8h` (bp, from the
decision bar close). One decision per weekday per variant, so `periods_per_year = 260`.

## Features (55 at the final decision bar)
All hourly-store columns except labels, `close` and the columns constant at a decision bar (`hour_london`, `hour_ny`,
`is_london`, `is_ny`), and columns more than 50 % NaN at that decision bar (`ret_since_london_open_bp` is undefined at
L07). Groups: multi-horizon returns, intraday vol state, position in the 24h range, distances to previous-day
high/low/open/pivot, session-so-far return, hour_utc (= DST flag) and dow, event clocks (hours to/since FOMC, ECB,
NFP, CPI, any high-impact), and `d_*` = the previous NY session's daily features (returns, rv, trend state, adx, 2y
spread and its changes, fair-value residual, VIX, COT, dollar factor, DXY/SPX, last NFP/CPI surprises, month-end).

## Models and decision rule
* LightGBM regression (300 trees, lr 0.03, 15 leaves, min 100 rows per leaf, 70 % features / 80 % rows per tree,
  L2 5, `num_threads=1`), target clipped at +-3 sd of the training window.
* Ridge (median impute, standardize, alpha chosen by 4-fold time-ordered CV inside the training window, target clipped).
* Logistic on sign(target) (C = 0.05); forecast in bp = (2 P(up) - 1) x mean |target| of the training window.
* Decision rule: pos = sign(forecast) iff |forecast| > max( q-quantile of |forecast| on the last 20 % (time-ordered) of
  the training window, round-trip cost in bp = 2 x cost_pips / price ), q in {0.5, 0.8}.
* Costs: each decision is a discrete round trip, so net = pos x fwd - 2|pos| x cost. (The harness's diff-based turnover
  would charge an always-short rule once in 17 years; the round-trip accounting is the honest one for intraday trades.)
  Positions are fixed by the 1.2-pip rule; the 0.6-pip record re-prices the same positions.
* Walk-forward: `eurusd.wf.walk_forward` with `label_end_{h}h`, test years 2010-2026, expanding window from 2003.

## Selection rule (declared before results)
Among the 36 ML-grid variants (3 decision bars x 2 horizons x 3 models x 2 quantiles) pick the highest 2010-2015 net
Sharpe at 1.2 pips among variants active on >= 10% of their decision bars in 2010-2015; report its full
2010-2026 record. Baselines, regime gates and event exclusion are reported in the same harness but are not eligible.
Number of variants run in this arm: **51** (36 grid + 2 unconditional + 10 regime + 3 event-exclusion); the
deflated-Sharpe p of the final variant uses n_trials = 51.

## Final variant: `ml_NY17_4h_lgbm_q0.8`
Decision bar NY17, horizon 4h, model lgbm, quantile 0.8. Deflated-Sharpe p (n_trials=51) = 0.04.

| period | Sharpe (1.2p) | t | mean bp | active | n | Sharpe (0.6p) | t (0.6p) |
|---|---|---|---|---|---|---|---|
| 2010 | +0.88 | +0.88 | +0.57 | 0.17 | 258 | +1.11 | +1.11 |
| 2011 | +1.96 | +1.96 | +1.47 | 0.19 | 260 | +2.16 | +2.16 |
| 2012 | +1.31 | +1.31 | +0.80 | 0.18 | 260 | +1.58 | +1.58 |
| 2013 | +1.27 | +1.26 | +0.64 | 0.05 | 257 | +1.35 | +1.34 |
| 2014 | +1.58 | +1.57 | +0.34 | 0.04 | 258 | +1.70 | +1.69 |
| 2015 | +0.88 | +0.88 | +0.68 | 0.27 | 258 | +1.26 | +1.26 |
| 2016 | +2.27 | +2.26 | +1.37 | 0.14 | 259 | +2.49 | +2.49 |
| 2017 | +0.43 | +0.43 | +0.08 | 0.10 | 259 | +0.97 | +0.97 |
| 2018 | +1.11 | +1.10 | +0.29 | 0.11 | 259 | +1.51 | +1.51 |
| 2019 | +1.56 | +1.54 | +0.44 | 0.18 | 255 | +2.20 | +2.18 |
| 2020 | +0.20 | +0.20 | +0.11 | 0.26 | 255 | +0.72 | +0.72 |
| 2021 | -1.48 | -1.47 | -0.26 | 0.11 | 256 | -0.85 | -0.84 |
| 2022 | +1.04 | +1.04 | +0.53 | 0.27 | 257 | +1.65 | +1.64 |
| 2023 | +1.47 | +1.28 | +0.48 | 0.14 | 197 | +1.91 | +1.67 |
| 2024 | -0.62 | -0.62 | -0.19 | 0.05 | 255 | -0.43 | -0.42 |
| 2025 | +0.79 | +0.79 | +0.54 | 0.18 | 255 | +1.08 | +1.07 |
| 2026 | +0.13 | +0.12 | +0.03 | 0.06 | 215 | +0.38 | +0.35 |

Aggregates at 1.2 pips:

| period | Sharpe | t | mean bp/decision | sum bp | active | n |
|---|---|---|---|---|---|---|
| 2010-2026 | +0.95 | +3.86 | +0.47 | +2013 | 0.15 | 4273 |
| 2016-2026 | +0.76 | +2.45 | +0.31 | +848 | 0.15 | 2722 |
| 2023-2026 | +0.47 | +0.89 | +0.21 | +191 | 0.11 | 922 |
| 2010-2015 | +1.23 | +3.00 | +0.75 | +1165 | 0.15 | 1551 |
| 2016-2022 | +0.92 | +2.41 | +0.37 | +657 | 0.17 | 1800 |

Aggregates at 0.6 pips (same positions):

| period | Sharpe | t | mean bp/decision | sum bp | active | n |
|---|---|---|---|---|---|---|
| 2010-2026 | +1.26 | +5.10 | +0.63 | +2674 | 0.15 | 4273 |
| 2016-2026 | +1.14 | +3.68 | +0.47 | +1284 | 0.15 | 2722 |
| 2023-2026 | +0.74 | +1.40 | +0.33 | +301 | 0.11 | 922 |
| 2010-2015 | +1.45 | +3.55 | +0.90 | +1390 | 0.15 | 1551 |
| 2016-2022 | +1.36 | +3.57 | +0.55 | +983 | 0.17 | 1800 |

Success bar (2010-2026 SR > 0.4, 2016-2026 SR > 0.3, 2023-2026 >= 0 at 1.2 pips): **PASSED**.

## Comparison with the unconditional London short (same harness, same costs)
Unconditional short at L07, horizon 4h: SR 2010-2026 -1.07 (t -4.40),
2016-2026 -1.42, 2023-2026 -1.77; horizon 4h:
SR 2010-2026 -1.07 (t -4.40), 2016-2026 -1.42,
2023-2026 -1.77. Note that the per-trade cost of a 4h/8h round trip (about 2.2 bp at 1.2 pips)
is larger than the unconditional mean move (about -0.4 bp at 4h, -1.3 bp at 8h from 07:00 London), so the unconditional
rule cannot be net profitable at retail cost in this accounting.

### Baselines and regime gates (London short at L07; gate thresholds from the training window)
| variant | SR 2010-2015 | SR 2010-2026 | SR 2016-2026 | SR 2023-2026 | t 2010-26 | active |
|---|---|---|---|---|---|---|
| london_short_uncond_4h | -0.62 | -1.07 | -1.42 | -1.77 | -4.40 | 1.00 |
| london_short_rv_low_4h | -0.17 | -0.94 | -1.30 | -1.25 | -3.85 | 0.55 |
| london_short_rv_mid_4h | +0.03 | -0.27 | -0.47 | -0.91 | -1.11 | 0.21 |
| london_short_rv_high_4h | -0.72 | -0.62 | -0.58 | -0.94 | -2.55 | 0.24 |
| london_short_adx_low_4h | -0.80 | -0.98 | -1.12 | -1.45 | -4.04 | 0.50 |
| london_short_adx_high_4h | -0.13 | -0.56 | -0.89 | -1.06 | -2.28 | 0.50 |
| london_short_uncond_8h | +0.25 | -0.20 | -0.53 | -0.99 | -0.83 | 1.00 |
| london_short_rv_low_8h | -0.23 | -0.52 | -0.64 | -0.37 | -2.12 | 0.55 |
| london_short_rv_mid_8h | +0.81 | +0.24 | -0.17 | -0.93 | +0.98 | 0.21 |
| london_short_rv_high_8h | -0.08 | -0.04 | +0.01 | -0.41 | -0.15 | 0.24 |
| london_short_adx_low_8h | -0.55 | -0.55 | -0.55 | -1.33 | -2.24 | 0.50 |
| london_short_adx_high_8h | +0.83 | +0.24 | -0.20 | -0.05 | +0.97 | 0.50 |

### Event exclusion (decision bars within 2h of a high-impact event removed from train and test)
| variant | SR 2010-2015 | SR 2010-2026 | SR 2016-2026 | SR 2023-2026 | t 2010-26 | active |
|---|---|---|---|---|---|---|
| ml_NY17_4h_lgbm_q0.8_noevent2h | +1.57 | +1.21 | +0.98 | +0.96 | +4.86 | 0.15 |
| london_short_uncond_4h_noevent2h | -0.78 | -1.24 | -1.58 | -2.05 | -4.92 | 1.00 |
| london_short_uncond_8h_noevent2h | +0.22 | -0.22 | -0.53 | -1.11 | -0.89 | 1.00 |

### Full ML grid
| variant | SR 2010-2015 | SR 2010-2026 | SR 2016-2026 | SR 2023-2026 | t 2010-26 | active |
|---|---|---|---|---|---|---|
| ml_L07_4h_lgbm_q0.5 | +0.46 | -0.09 | -0.50 | +0.21 | -0.35 | 0.43 |
| ml_L07_4h_lgbm_q0.8 | +0.27 | -0.21 | -0.58 | +0.13 | -0.86 | 0.15 |
| ml_L07_4h_ridge_q0.5 | +0.13 | -0.20 | -0.57 | +0.00 | -0.83 | 0.13 |
| ml_L07_4h_ridge_q0.8 | +0.13 | -0.15 | -0.46 | +0.00 | -0.60 | 0.10 |
| ml_L07_4h_logit_q0.5 | -0.07 | -0.49 | -0.81 | -1.07 | -2.00 | 0.40 |
| ml_L07_4h_logit_q0.8 | +0.13 | -0.12 | -0.33 | +0.21 | -0.49 | 0.15 |
| ml_L07_8h_lgbm_q0.5 | +0.17 | +0.05 | -0.05 | -0.32 | +0.19 | 0.43 |
| ml_L07_8h_lgbm_q0.8 | +0.03 | +0.01 | -0.00 | -0.27 | +0.05 | 0.15 |
| ml_L07_8h_ridge_q0.5 | +0.20 | +0.03 | -0.10 | -0.41 | +0.13 | 0.35 |
| ml_L07_8h_ridge_q0.8 | +0.14 | +0.03 | -0.07 | -0.31 | +0.13 | 0.25 |
| ml_L07_8h_logit_q0.5 | +0.16 | +0.07 | +0.01 | -0.30 | +0.29 | 0.42 |
| ml_L07_8h_logit_q0.8 | +0.61 | +0.31 | +0.08 | -0.60 | +1.25 | 0.15 |
| ml_L13_4h_lgbm_q0.5 | -0.68 | -0.47 | -0.32 | -0.79 | -1.92 | 0.44 |
| ml_L13_4h_lgbm_q0.8 | -0.54 | -0.17 | +0.07 | -0.70 | -0.70 | 0.15 |
| ml_L13_4h_ridge_q0.5 | -0.53 | -0.58 | -0.63 | +0.15 | -2.35 | 0.13 |
| ml_L13_4h_ridge_q0.8 | -0.34 | -0.51 | -0.63 | +0.15 | -2.06 | 0.11 |
| ml_L13_4h_logit_q0.5 | -0.62 | -0.68 | -0.77 | -0.65 | -2.78 | 0.44 |
| ml_L13_4h_logit_q0.8 | -0.21 | -0.31 | -0.53 | -0.63 | -1.28 | 0.20 |
| ml_L13_8h_lgbm_q0.5 | -0.30 | -0.31 | -0.33 | -0.56 | -1.27 | 0.44 |
| ml_L13_8h_lgbm_q0.8 | -0.42 | -0.22 | -0.07 | -0.00 | -0.89 | 0.15 |
| ml_L13_8h_ridge_q0.5 | -0.08 | -0.53 | -0.96 | -0.57 | -2.16 | 0.36 |
| ml_L13_8h_ridge_q0.8 | -0.17 | -0.18 | -0.20 | +0.53 | -0.72 | 0.13 |
| ml_L13_8h_logit_q0.5 | -0.51 | -0.72 | -0.89 | -1.18 | -2.92 | 0.43 |
| ml_L13_8h_logit_q0.8 | -0.44 | -0.52 | -0.62 | -1.29 | -2.11 | 0.18 |
| ml_NY17_4h_lgbm_q0.5 | +0.79 | +0.45 | +0.21 | +0.47 | +1.84 | 0.45 |
| ml_NY17_4h_lgbm_q0.8 | +1.23 | +0.95 | +0.76 | +0.47 | +3.86 | 0.15 |
| ml_NY17_4h_ridge_q0.5 | +0.40 | +0.50 | +0.58 | +0.81 | +2.02 | 0.23 |
| ml_NY17_4h_ridge_q0.8 | +0.94 | +0.78 | +0.68 | +0.81 | +3.15 | 0.12 |
| ml_NY17_4h_logit_q0.5 | +0.83 | +0.88 | +0.94 | +1.25 | +3.55 | 0.34 |
| ml_NY17_4h_logit_q0.8 | +1.19 | +1.19 | +1.23 | +1.42 | +4.82 | 0.15 |
| ml_NY17_8h_lgbm_q0.5 | +0.09 | +0.31 | +0.47 | -0.22 | +1.27 | 0.46 |
| ml_NY17_8h_lgbm_q0.8 | +0.16 | +0.40 | +0.58 | +0.22 | +1.64 | 0.18 |
| ml_NY17_8h_ridge_q0.5 | +0.34 | +0.59 | +0.71 | +0.57 | +2.41 | 0.30 |
| ml_NY17_8h_ridge_q0.8 | +0.39 | +0.84 | +1.03 | +0.70 | +3.41 | 0.20 |
| ml_NY17_8h_logit_q0.5 | +0.37 | +0.47 | +0.52 | +0.22 | +1.90 | 0.41 |
| ml_NY17_8h_logit_q0.8 | +0.37 | +0.61 | +0.76 | +0.63 | +2.49 | 0.15 |

## Top features
Mean LightGBM gain share over the 17 walk-forward fits at NY17/4h:

| feature | gain share |
|---|---|
| ret_1h | 0.062 |
| atr24_pips | 0.044 |
| d_rv_21d_bp | 0.041 |
| range_1h_pips | 0.038 |
| d_vix | 0.035 |
| rv_120h_bp | 0.035 |
| d_spread2y | 0.032 |
| ret_2h | 0.032 |
| d_spx_ret_5 | 0.027 |
| d_usd_factor_20 | 0.026 |
| range_rel_24h | 0.026 |
| d_d_spread2y_5 | 0.025 |
| d_fv_resid_z | 0.024 |
| d_dist_sma50_atr | 0.023 |
| d_d_spread2y_20 | 0.023 |


Sanity check: none of these is a label in disguise. All `d_*` columns are the previous NY session's daily features
(shifted one day in `featstore.build_hourly`), `ret_*`/`rv_*`/range/level distances use bars up to the decision bar,
event clocks are measured at the decision-bar close, and `fwd_*`/`label_end_*`/`close` are excluded.

## Leak checks (final configuration re-run through the same pipeline)
| check | SR 2010-2026 | t | SR 2016-2026 | expectation |
|---|---|---|---|---|
| labels shuffled (seed 7) | -0.50 | -2.04 | -0.36 | ~0 |
| features shifted +1 decision bar (stale) | -0.25 | -1.02 | -0.48 | collapses |
| features shifted -1 decision bar (future) | +3.75 | +15.22 | +3.73 | jumps (shows the pipeline would detect a leak) |

## What helped, what did not
See the summary tables above; the written assessment is in the lead's notes and in the run log
(`experiments/results/logs/intraday_ml.log`). Run time 8.3 min on one CPU per fit.

Files: `src/eurusd/arms/intraday_ml.py` (`run(cost_pips=1.2)`), `experiments/results/arms/intraday_ml_positions.parquet`
(OOS positions of the final variant: index = decision bar, `pos`, `fwd_bp`, `net_bp`, `horizon_h`, `forecast_bp`),
`experiments/results/arms/intraday_ml_report.csv` (all variants, `variant`, `group`, `final`, `cost_pips`).
