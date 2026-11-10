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
  Positions are fixed by the 1.2-pip rule; the 0.6 / 2.0 / 3.0-pip records re-price the same positions.
* Walk-forward: `eurusd.wf.walk_forward` with `label_end_{h}h`, test years 2010-2026, expanding window from 2003.

## Selection rule (declared before results)
Among the 36 ML-grid variants (3 decision bars x 2 horizons x 3 models x 2 quantiles) pick the highest 2010-2015 net
Sharpe at 1.2 pips among variants active on >= 10% of their decision bars in 2010-2015; report its full
2010-2026 record. Baselines, regime gates, event exclusion and the post-selection diagnostics are reported in the same
harness but were not eligible. Number of variants run in this arm: **56** (36 grid + 2 unconditional + 10 regime
+ 3 event-exclusion + 5 diagnostics; cost re-pricings and leak checks not counted); the deflated-Sharpe p of the
final variant uses n_trials = 56.

## Final variant: `ml_NY17_4h_lgbm_q0.8`
Decision bar NY17, horizon 4h, model lgbm, quantile 0.8. Deflated-Sharpe p (n_trials=56) = 0.047.
638 trades in 2010-2026 (42% long), gross +5.23 bp per trade,
79% of the trades are in the direction opposite to the decision bar's own 1h return.

| year | net Sharpe (1.2p) | t | mean bp | active | n | net Sharpe (0.6p) | t (0.6p) |
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

| period | net Sharpe | t | gross Sharpe | mean bp/decision | sum bp | active | n |
|---|---|---|---|---|---|---|---|
| 2010-2026 | +0.95 | +3.86 | +1.55 | +0.47 | +2013 | 0.15 | 4273 |
| 2016-2026 | +0.76 | +2.45 | +1.51 | +0.31 | +848 | 0.15 | 2722 |
| 2023-2026 | +0.47 | +0.89 | +1.01 | +0.21 | +191 | 0.11 | 922 |
| 2010-2015 | +1.23 | +3.00 | +1.68 | +0.75 | +1165 | 0.15 | 1551 |
| 2016-2022 | +0.92 | +2.41 | +1.78 | +0.37 | +657 | 0.17 | 1800 |

Aggregates at 0.6 pips (same positions):

| period | net Sharpe | t | gross Sharpe | mean bp/decision | sum bp | active | n |
|---|---|---|---|---|---|---|---|
| 2010-2026 | +1.26 | +5.10 | +1.55 | +0.63 | +2674 | 0.15 | 4273 |
| 2016-2026 | +1.14 | +3.68 | +1.51 | +0.47 | +1284 | 0.15 | 2722 |
| 2023-2026 | +0.74 | +1.40 | +1.01 | +0.33 | +301 | 0.11 | 922 |
| 2010-2015 | +1.45 | +3.55 | +1.68 | +0.90 | +1390 | 0.15 | 1551 |
| 2016-2022 | +1.36 | +3.57 | +1.78 | +0.55 | +983 | 0.17 | 1800 |

Cost sensitivity (same positions; net Sharpe / t):

| cost pips per side | SR 2010-2026 | t | SR 2016-2026 | SR 2023-2026 |
|---|---|---|---|---|
| 0.6 | +1.26 | +5.10 | +1.14 | +0.74 |
| 1.2 | +0.95 | +3.86 | +0.76 | +0.47 |
| 2.0 | +0.54 | +2.18 | +0.24 | +0.11 |
| 3.0 | +0.01 | +0.05 | -0.41 | -0.35 |

Break-even cost for the final variant is about 2.9 pips per side.

Success bar (2010-2026 SR > 0.4, 2016-2026 SR > 0.3, 2023-2026 >= 0 at 1.2 pips): **PASSED** on paper -
see the assessment below before taking it at face value.

## Does conditioning beat the unconditional London short?
Same harness, same round-trip costs. The unconditional short at L07:
4h horizon SR 2010-2026 -1.07 (t -4.40, gross SR +0.26), 2016-2026 -1.42, 2023-2026 -1.77;
8h horizon SR 2010-2026 -0.20 (t -0.83, gross SR +0.66), 2016-2026 -0.53, 2023-2026 -0.99.
The unconditional mean move from 07:00 London (about -0.4 bp over 4h, -1.3 bp over 8h) is smaller than one round trip
at 1.2 pips (about 2.2 bp), so the rule is gross-positive but net-negative when traded every day; round 1's positive
record for it relied on a 6h hold, a disaster stop and a lower cost assumption.

* Conditioning at the same decision bar (L07): the best of the 12 L07 ML variants over 2010-2026 is `ml_L07_8h_logit_q0.8`
  with net SR +0.31 (t +1.25). The models cut the losing days (net SR goes from
  -1.07 / -0.20 to about zero) but find no reliably profitable subset: nothing at L07 clears the cost gate
  often enough, and 2016-2026 is at best flat. **Conditioning does not turn the London effect into a tradable signal.**
* Regime gates on the unconditional short: the mid-rv tercile and high-ADX halves look best in 2010-2015 (SR about +0.8 at
  8h) but both are negative in 2016-2026 and 2023-2026. Low-rv regimes are the worst. No gate is stable.
* Event exclusion (bars within 2h of a high-impact event removed): changes nothing for the London short (slightly worse);
  for the final configuration it raises the Sharpe a little (see table).
* L13 (London/NY overlap): every one of the 12 variants is negative over 2010-2026 (best `ml_L13_4h_lgbm_q0.8` SR -0.17).
  Nothing predictable at the overlap after costs.
* NY17 (overnight): all 12 variants are positive and it is where the selection rule lands. See the assessment.

### Baselines and regime gates (London short at L07; gate thresholds from the training window)
| variant | SR 2010-2015 | SR 2010-2026 | SR 2016-2026 | SR 2023-2026 | t 2010-26 | gross SR 2010-26 | active |
|---|---|---|---|---|---|---|---|
| london_short_uncond_4h | -0.62 | -1.07 | -1.42 | -1.77 | -4.40 | +0.26 | 1.00 |
| london_short_rv_low_4h | -0.17 | -0.94 | -1.30 | -1.25 | -3.85 | +0.38 | 0.55 |
| london_short_rv_mid_4h | +0.03 | -0.27 | -0.47 | -0.91 | -1.11 | +0.30 | 0.21 |
| london_short_rv_high_4h | -0.72 | -0.62 | -0.58 | -0.94 | -2.55 | -0.15 | 0.24 |
| london_short_adx_low_4h | -0.80 | -0.98 | -1.12 | -1.45 | -4.04 | +0.02 | 0.50 |
| london_short_adx_high_4h | -0.13 | -0.56 | -0.89 | -1.06 | -2.28 | +0.34 | 0.50 |
| london_short_uncond_8h | +0.25 | -0.20 | -0.53 | -0.99 | -0.83 | +0.66 | 1.00 |
| london_short_rv_low_8h | -0.23 | -0.52 | -0.64 | -0.37 | -2.12 | +0.30 | 0.55 |
| london_short_rv_mid_8h | +0.81 | +0.24 | -0.17 | -0.93 | +0.98 | +0.60 | 0.21 |
| london_short_rv_high_8h | -0.08 | -0.04 | +0.01 | -0.41 | -0.15 | +0.28 | 0.24 |
| london_short_adx_low_8h | -0.55 | -0.55 | -0.55 | -1.33 | -2.24 | +0.08 | 0.50 |
| london_short_adx_high_8h | +0.83 | +0.24 | -0.20 | -0.05 | +0.97 | +0.82 | 0.50 |

### Event exclusion (decision bars within 2h of a high-impact event removed from train and test)
| variant | SR 2010-2015 | SR 2010-2026 | SR 2016-2026 | SR 2023-2026 | t 2010-26 | gross SR 2010-26 | active |
|---|---|---|---|---|---|---|---|
| ml_NY17_4h_lgbm_q0.8_noevent2h | +1.57 | +1.21 | +0.98 | +0.96 | +4.86 | +1.85 | 0.15 |
| london_short_uncond_4h_noevent2h | -0.78 | -1.24 | -1.58 | -2.05 | -4.92 | +0.12 | 1.00 |
| london_short_uncond_8h_noevent2h | +0.22 | -0.22 | -0.53 | -1.11 | -0.89 | +0.64 | 1.00 |

### Full ML grid
| variant | SR 2010-2015 | SR 2010-2026 | SR 2016-2026 | SR 2023-2026 | t 2010-26 | gross SR 2010-26 | active |
|---|---|---|---|---|---|---|---|
| ml_L07_4h_lgbm_q0.5 | +0.46 | -0.09 | -0.50 | +0.21 | -0.35 | +0.74 | 0.43 |
| ml_L07_4h_lgbm_q0.8 | +0.27 | -0.21 | -0.58 | +0.13 | -0.86 | +0.23 | 0.15 |
| ml_L07_4h_ridge_q0.5 | +0.13 | -0.20 | -0.57 | +0.00 | -0.83 | +0.18 | 0.13 |
| ml_L07_4h_ridge_q0.8 | +0.13 | -0.15 | -0.46 | +0.00 | -0.60 | +0.18 | 0.10 |
| ml_L07_4h_logit_q0.5 | -0.07 | -0.49 | -0.81 | -1.07 | -2.00 | +0.29 | 0.40 |
| ml_L07_4h_logit_q0.8 | +0.13 | -0.12 | -0.33 | +0.21 | -0.49 | +0.31 | 0.15 |
| ml_L07_8h_lgbm_q0.5 | +0.17 | +0.05 | -0.05 | -0.32 | +0.19 | +0.57 | 0.43 |
| ml_L07_8h_lgbm_q0.8 | +0.03 | +0.01 | -0.00 | -0.27 | +0.05 | +0.29 | 0.15 |
| ml_L07_8h_ridge_q0.5 | +0.20 | +0.03 | -0.10 | -0.41 | +0.13 | +0.48 | 0.35 |
| ml_L07_8h_ridge_q0.8 | +0.14 | +0.03 | -0.07 | -0.31 | +0.13 | +0.38 | 0.25 |
| ml_L07_8h_logit_q0.5 | +0.16 | +0.07 | +0.01 | -0.30 | +0.29 | +0.59 | 0.42 |
| ml_L07_8h_logit_q0.8 | +0.61 | +0.31 | +0.08 | -0.60 | +1.25 | +0.61 | 0.15 |
| ml_L13_4h_lgbm_q0.5 | -0.68 | -0.47 | -0.32 | -0.79 | -1.92 | +0.18 | 0.44 |
| ml_L13_4h_lgbm_q0.8 | -0.54 | -0.17 | +0.07 | -0.70 | -0.70 | +0.21 | 0.15 |
| ml_L13_4h_ridge_q0.5 | -0.53 | -0.58 | -0.63 | +0.15 | -2.35 | -0.27 | 0.13 |
| ml_L13_4h_ridge_q0.8 | -0.34 | -0.51 | -0.63 | +0.15 | -2.06 | -0.21 | 0.11 |
| ml_L13_4h_logit_q0.5 | -0.62 | -0.68 | -0.77 | -0.65 | -2.78 | -0.02 | 0.44 |
| ml_L13_4h_logit_q0.8 | -0.21 | -0.31 | -0.53 | -0.63 | -1.28 | +0.10 | 0.20 |
| ml_L13_8h_lgbm_q0.5 | -0.30 | -0.31 | -0.33 | -0.56 | -1.27 | +0.24 | 0.44 |
| ml_L13_8h_lgbm_q0.8 | -0.42 | -0.22 | -0.07 | -0.00 | -0.89 | +0.07 | 0.15 |
| ml_L13_8h_ridge_q0.5 | -0.08 | -0.53 | -0.96 | -0.57 | -2.16 | -0.04 | 0.36 |
| ml_L13_8h_ridge_q0.8 | -0.17 | -0.18 | -0.20 | +0.53 | -0.72 | +0.07 | 0.13 |
| ml_L13_8h_logit_q0.5 | -0.51 | -0.72 | -0.89 | -1.18 | -2.92 | -0.19 | 0.43 |
| ml_L13_8h_logit_q0.8 | -0.44 | -0.52 | -0.62 | -1.29 | -2.11 | -0.21 | 0.18 |
| ml_NY17_4h_lgbm_q0.5 | +0.79 | +0.45 | +0.21 | +0.47 | +1.84 | +1.73 | 0.45 |
| ml_NY17_4h_lgbm_q0.8 | +1.23 | +0.95 | +0.76 | +0.47 | +3.86 | +1.55 | 0.15 |
| ml_NY17_4h_ridge_q0.5 | +0.40 | +0.50 | +0.58 | +0.81 | +2.02 | +1.35 | 0.23 |
| ml_NY17_4h_ridge_q0.8 | +0.94 | +0.78 | +0.68 | +0.81 | +3.15 | +1.36 | 0.12 |
| ml_NY17_4h_logit_q0.5 | +0.83 | +0.88 | +0.94 | +1.25 | +3.55 | +2.00 | 0.34 |
| ml_NY17_4h_logit_q0.8 | +1.19 | +1.19 | +1.23 | +1.42 | +4.82 | +1.76 | 0.15 |
| ml_NY17_8h_lgbm_q0.5 | +0.09 | +0.31 | +0.47 | -0.22 | +1.27 | +1.29 | 0.46 |
| ml_NY17_8h_lgbm_q0.8 | +0.16 | +0.40 | +0.58 | +0.22 | +1.64 | +0.98 | 0.18 |
| ml_NY17_8h_ridge_q0.5 | +0.34 | +0.59 | +0.71 | +0.57 | +2.41 | +1.48 | 0.30 |
| ml_NY17_8h_ridge_q0.8 | +0.39 | +0.84 | +1.03 | +0.70 | +3.41 | +1.62 | 0.20 |
| ml_NY17_8h_logit_q0.5 | +0.37 | +0.47 | +0.52 | +0.22 | +1.90 | +1.36 | 0.41 |
| ml_NY17_8h_logit_q0.8 | +0.37 | +0.61 | +0.76 | +0.63 | +2.49 | +1.13 | 0.15 |

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
(shifted one day in `featstore.build_hourly`), `ret_*`/`rv_*`/range/level distances use bars up to and including the
decision bar, event clocks are measured at the decision-bar close, and `fwd_*`/`label_end_*`/`close` are excluded.
`ret_1h` (the decision bar's own return) is the top feature; what that means is discussed below.

## Post-selection diagnostics of the final configuration (not eligible for selection)
| variant | SR 2010-2015 | SR 2010-2026 | SR 2016-2026 | SR 2023-2026 | t 2010-26 | gross SR 2010-26 | active |
|---|---|---|---|---|---|---|---|
| diag_fade_ret1h_q0.5_NY17_4h | +0.77 | +0.71 | +0.69 | +0.69 | +2.89 | +1.94 | 0.42 |
| diag_fade_ret1h_q0.8_NY17_4h | +0.84 | +0.93 | +1.03 | +0.80 | +3.79 | +1.46 | 0.14 |
| ml_NY17_4h_lgbm_q0.8_no_last_bar_feats | +0.41 | +0.27 | +0.17 | +1.04 | +1.10 | +0.95 | 0.14 |
| ml_NY17_4h_lgbm_q0.8_decision-1h | +0.52 | +0.09 | -0.43 | -0.71 | +0.35 | +0.77 | 0.15 |
| ml_NY17_4h_lgbm_q0.8_decision+1h | +0.51 | +0.56 | +0.61 | +0.93 | +2.06 | +1.29 | 0.16 |

`diag_fade_ret1h_q*`: no model at all, just short when the decision bar's own 1h return is above its training quantile
and long when below (q = 0.5 / 0.8). `_no_last_bar_feats`: the final model without ret_1h, ret_2h, range_1h_pips, range_rel_24h.
`_decision-1h` / `_decision+1h`: the final configuration one hour earlier / later on the same local clock.

## Assessment: what the NY17 result is, and why it should not be taken at face value
The final variant's record is driven by mean reversion of the 16:00-17:00 New York bar, i.e. the daily rollover hour:
* corr(ret_1h, fwd_1h) in 2010-2026 is about -0.09 at `hour_ny` 16, -0.16 at 17 and -0.10 at 18, versus |corr| < 0.06 at
  every other hour; corr(ret_1h, fwd_4h) is -0.12 at hour 16 and within +-0.04 elsewhere.
* 79% of the final variant's trades are simply against the decision bar's own return. The model-free fade rule
  (`diag_fade_ret1h_q0.8`) earns net SR +0.93 (2016-2026 +1.03), as much as the LightGBM model.
* Removing the four decision-bar features drops the final configuration to net SR +0.27 (2016-2026 +0.17).
  The day's context (d_* macro, positioning, event clocks, previous-day levels) on its own does not carry the result.
* The effect lives in the thinnest hour of the day (mean |1h move| at 17:00 NY is about a third of the London morning),
  in bid-only HistData prices, with exactly the shape of quote bounce in illiquid trading. Retail spreads at the 17:00 NY
  rollover are routinely 3-10 pips, not 1.2, and the break-even cost of the final variant is about 2.9 pips per side.
  At 2.0 pips the net Sharpe is +0.54, at 3.0 pips +0.01.
So the arm's honest conclusion is: the context-conditioned intraday models find **no new information** at the London
decision bars (L07, L13), and the one thing they do find (NY17) is a microstructure artefact of the rollover hour that
is unlikely to survive real overnight spreads. The positions file is nevertheless the declared final variant, so the lead
can decide whether to stack it; it should be given the cost of the rollover hour, not 1.2 pips.

## Leak checks (final configuration re-run through the same pipeline)
| check | net SR 2010-2026 | t | gross SR 2010-2026 | net SR 2016-2026 | expectation |
|---|---|---|---|---|---|
| labels shuffled, 5 seeds (mean [min, max]) | -0.82 [-1.05, -0.50] | -3.33 | +0.01 [-0.20, +0.25] | -0.82 | gross ~0, net = cost drag |
| features shifted +1 decision bar (stale) | -0.25 | -1.02 | +0.49 | -0.48 | collapses |
| features shifted -1 decision bar (future) | +3.75 | +15.22 | +4.14 | +3.73 | jumps (the pipeline would detect a leak) |

With shuffled labels the model has no skill but still pays the round-trip cost on ~15 % of bars, so the net Sharpe is
negative by construction and the gross Sharpe is the number to read (~0). Stale features collapse to the cost drag; features
from the next decision bar (which overlap the label window) jump to a very large Sharpe, confirming the harness is
sensitive to a leak and that the real run contains none of that kind.

## Run
`PYTHONPATH=src python -m eurusd.arms.intraday_ml` (9.4 min, one CPU per fit; log in `experiments/results/logs/intraday_ml.log`).
Files: `src/eurusd/arms/intraday_ml.py` (`run(cost_pips=1.2)`), `experiments/results/arms/intraday_ml_positions.parquet`
(OOS positions of the final variant: index = decision bar, `pos`, `fwd_bp`, `net_bp`, `horizon_h`, `forecast_bp`),
`experiments/results/arms/intraday_ml_report.csv` (all variants, `variant`, `group`, `final`, `cost_pips`, `gross_sharpe`).
