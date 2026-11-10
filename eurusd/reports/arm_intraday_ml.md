# Arm B: intraday_ml - context-conditioned intraday prediction at fixed decision times

## Idea
Round 1 found one robust intraday regularity (short EUR/USD 07:00-13:00 London) and that hour-of-day patterns drift.
This arm asks whether a model conditioned on the day's context predicts the London session, the London/NY overlap and
the overnight session better than the unconditional rule. Decision bars (hourly feature store, index = bar start):
L07 = bar closing 07:00 London (`hour_london == 6`), L13 = bar closing 13:00 London (`hour_london == 12`),
NY17 = bar closing 17:00 New York (`hour_ny == 16`); weekend bars dropped. Targets `fwd_4h`, `fwd_8h` (bp, from the
decision bar close). One decision per weekday per variant, so `periods_per_year = 260`.

## Features (54 at the final decision bar)
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
Number of variants run in this arm: **19** (36 grid + 2 unconditional + 10 regime + 3 event-exclusion); the
deflated-Sharpe p of the final variant uses n_trials = 19.

## Final variant: `ml_L07_4h_ridge_q0.5`
Decision bar L07, horizon 4h, model ridge, quantile 0.5. Deflated-Sharpe p (n_trials=19) = 1.00.

| period | Sharpe (1.2p) | t | mean bp | active | n | Sharpe (0.6p) | t (0.6p) |
|---|---|---|---|---|---|---|---|
| 2010 | +0.33 | +0.33 | +0.35 | 0.26 | 260 | +0.55 | +0.55 |
| 2011 | +0.36 | +0.36 | +0.60 | 0.58 | 259 | +0.66 | +0.65 |
| 2012 | +0.00 | +0.00 | +0.00 | 0.00 | 258 | +0.00 | +0.00 |
| 2013 | -1.29 | -1.28 | -0.76 | 0.23 | 258 | -0.94 | -0.94 |
| 2014 | +1.06 | +1.05 | +0.31 | 0.07 | 258 | +1.27 | +1.27 |
| 2015 | +0.27 | +0.27 | +0.20 | 0.07 | 259 | +0.37 | +0.37 |
| 2016 | -1.72 | -1.72 | -1.67 | 0.31 | 260 | -1.38 | -1.38 |
| 2017 | +1.39 | +1.39 | +0.66 | 0.09 | 258 | +1.59 | +1.58 |
| 2018 | -0.96 | -0.96 | -0.61 | 0.22 | 260 | -0.60 | -0.60 |
| 2019 | -2.17 | -2.16 | -0.82 | 0.26 | 259 | -1.46 | -1.46 |
| 2020 | -0.58 | -0.58 | -0.50 | 0.12 | 260 | -0.44 | -0.44 |
| 2021 | +0.00 | +0.00 | +0.00 | 0.00 | 259 | +0.00 | +0.00 |
| 2022 | +0.00 | +0.00 | +0.00 | 0.00 | 260 | +0.00 | +0.00 |
| 2023 | +0.00 | +0.00 | +0.00 | 0.00 | 259 | +0.00 | +0.00 |
| 2024 | +0.00 | +0.00 | +0.00 | 0.00 | 261 | +0.00 | +0.00 |
| 2025 | +0.00 | +0.00 | +0.00 | 0.00 | 260 | +0.00 | +0.00 |
| 2026 | +0.00 | +0.00 | +0.00 | 0.00 | 221 | +0.00 | +0.00 |

Aggregates at 1.2 pips:

| period | Sharpe | t | mean bp/decision | sum bp | active | n |
|---|---|---|---|---|---|---|
| 2010-2026 | -0.20 | -0.83 | -0.13 | -583 | 0.13 | 4369 |
| 2016-2026 | -0.57 | -1.87 | -0.27 | -765 | 0.09 | 2817 |
| 2023-2026 | +0.00 | +0.00 | +0.00 | +0 | 0.00 | 1001 |
| 2010-2015 | +0.13 | +0.32 | +0.12 | +182 | 0.20 | 1552 |
| 2016-2022 | -0.71 | -1.87 | -0.42 | -765 | 0.14 | 1816 |

Aggregates at 0.6 pips (same positions):

| period | Sharpe | t | mean bp/decision | sum bp | active | n |
|---|---|---|---|---|---|---|
| 2010-2026 | -0.01 | -0.04 | -0.01 | -27 | 0.13 | 4369 |
| 2016-2026 | -0.36 | -1.20 | -0.17 | -488 | 0.09 | 2817 |
| 2023-2026 | +0.00 | +0.00 | +0.00 | +0 | 0.00 | 1001 |
| 2010-2015 | +0.33 | +0.80 | +0.30 | +461 | 0.20 | 1552 |
| 2016-2022 | -0.45 | -1.20 | -0.27 | -488 | 0.14 | 1816 |

Success bar (2010-2026 SR > 0.4, 2016-2026 SR > 0.3, 2023-2026 >= 0 at 1.2 pips): **FAILED**.

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
| ml_L07_4h_ridge_q0.5_noevent2h | +0.05 | -0.11 | -0.35 | +0.52 | -0.44 | 0.10 |
| london_short_uncond_4h_noevent2h | -0.78 | -1.24 | -1.58 | -2.05 | -4.92 | 1.00 |
| london_short_uncond_8h_noevent2h | +0.22 | -0.22 | -0.53 | -1.11 | -0.89 | 1.00 |

### Full ML grid
| variant | SR 2010-2015 | SR 2010-2026 | SR 2016-2026 | SR 2023-2026 | t 2010-26 | active |
|---|---|---|---|---|---|---|
| ml_L07_4h_ridge_q0.5 | +0.13 | -0.20 | -0.57 | +0.00 | -0.83 | 0.13 |
| ml_L07_4h_ridge_q0.8 | +0.13 | -0.15 | -0.46 | +0.00 | -0.60 | 0.10 |
| ml_L07_4h_logit_q0.5 | -0.07 | -0.49 | -0.81 | -1.07 | -2.00 | 0.40 |
| ml_L07_4h_logit_q0.8 | +0.13 | -0.12 | -0.33 | +0.21 | -0.49 | 0.15 |

## Top features
Mean LightGBM gain share over the 17 walk-forward fits at L07/4h (the final model is linear; this is its LightGBM counterpart):

| feature | gain share |
|---|---|
| rv_120h_bp | 0.039 |
| rv_24h_bp | 0.038 |
| ret_2h | 0.036 |
| ret_4h | 0.036 |
| d_rv_21d_bp | 0.035 |
| d_ret_21d | 0.034 |
| atr24_pips | 0.029 |
| d_spread2y | 0.027 |
| d_vix | 0.027 |
| ret_24h | 0.026 |
| d_usd_factor_20 | 0.026 |
| ret_1h | 0.025 |
| d_usd_factor_5 | 0.025 |
| dist_pd_high_atr | 0.025 |
| d_ret_1d | 0.025 |


Largest standardized coefficients of the final linear model fitted on 2003-2022 (sign, for intuition):

| feature | coef |
|---|---|
| ret_2h | -0.186 |
| ret_1h | -0.161 |
| d_bd_to_end | -0.141 |
| dist_pd_high_atr | -0.100 |
| ret_since_day_open_bp | -0.099 |
| dow | -0.084 |
| ret_4h | -0.065 |
| d_usd_factor_20 | -0.065 |
| h_since_ecb | +0.065 |
| ret_8h | -0.063 |
| d_is_month_end | +0.061 |
| h_since_nfp | +0.053 |

Sanity check: none of these is a label in disguise. All `d_*` columns are the previous NY session's daily features
(shifted one day in `featstore.build_hourly`), `ret_*`/`rv_*`/range/level distances use bars up to the decision bar,
event clocks are measured at the decision-bar close, and `fwd_*`/`label_end_*`/`close` are excluded.

## Leak checks (final configuration re-run through the same pipeline)
| check | SR 2010-2026 | t | SR 2016-2026 | expectation |
|---|---|---|---|---|
| labels shuffled (seed 7) | -0.21 | -0.86 | -0.69 | ~0 |
| features shifted +1 decision bar (stale) | -0.01 | -0.06 | +0.30 | collapses |
| features shifted -1 decision bar (future) | +6.49 | +26.59 | +6.39 | jumps (shows the pipeline would detect a leak) |

## What helped, what did not
See the summary tables above; the written assessment is in the lead's notes and in the run log
(`experiments/results/logs/intraday_ml.log`). Run time 1.0 min on one CPU per fit.

Files: `src/eurusd/arms/intraday_ml.py` (`run(cost_pips=1.2)`), `experiments/results/arms/intraday_ml_positions.parquet`
(OOS positions of the final variant: index = decision bar, `pos`, `fwd_bp`, `net_bp`, `horizon_h`, `forecast_bp`),
`experiments/results/arms/intraday_ml_report.csv` (all variants, `variant`, `group`, `final`, `cost_pips`).
