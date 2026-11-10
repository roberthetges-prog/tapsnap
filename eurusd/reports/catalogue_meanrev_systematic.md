# Catalogue test: mean-reversion (M01-M15) and systematic / vendor-audit entries (Q01-Q03, Q05, Q06)

Data: HistData EUR/USD bid bars (UTC), 1.0 pip spread + 0.2 pip slippage per fill (engine `eurusd.backtest`).
Protocol (`experiments/HOWTO_AGENTS.md`): small grids on TRAIN 2003-2015, best point chosen by train t-stat
(minimum trade count), parameter-neighbourhood check on TRAIN, one VALIDATE 2016-2022 run per family, survival rules
avg R > 0, t >= 2, PF >= 1.15, >= 60 % years positive, >= 30 trades, neighbourhood positive. HOLDOUT 2023+ was never read.
Daily strategies run on UTC calendar days with the Sunday/Saturday stub bars removed. Strategies without a stop are
judged in pips (engine convention `has_r=False`).

Code: `src/eurusd/strategies_meanrev.py` (17 strategies registered in `REGISTRY`), driver
`experiments/13_meanrev_systematic.py`, per-family results `experiments/results/meanrev_systematic.csv`
(grids in `experiments/results/<strategy>_<family>_train.csv`), ML results `experiments/results/meanrev_systematic_ml.csv`,
logs `experiments/results/logs/meanrev_*.log`. A handful of trades of every family were printed and checked by hand
against the raw bars (signal bar, fill, stop, target, exit rule) before the numbers were trusted (see logs).

## 1. Verdict per catalogue id

| id | entry | what was tested | best family on VALIDATE | verdict |
|---|---|---|---|---|
| M01 | Connors RSI(2) D1 | thr 5/10, SMA200 filter, exit close>SMA5 (+/- SMA200 cross exit), no stop / 2xATR, both / long only (16 pts) | all 16 train points <= 0 in R or pips; val 27 trades, t 0.25 | FAIL - no edge on train, too few trades; vendor's negative result confirmed (sec. 3) |
| M02 | RSI(14) 30/70 cross-back | D1 and H4, stop 1.5/3 ATR, exit RSI 50/60 or BB mid, max hold (32 pts) | H4: val t 0.93, PF 1.13, 57 % yrs; train negative | FAIL - negative on train, insignificant on validate |
| M03 | Bollinger (20,2) fade to mid | D1, H1, M1 (NautilusTrader BB+RSI variant); exit on close crossing the mid band, ATR or band-width stop (36 pts) | D1: val 91 trades, +0.144 R, PF 1.38, t 1.42, 71 % yrs - but train negative (t -0.34, 38 % yrs) and 2019 alone is 9.6 of the 13.1 R | FAIL (near-miss on D1 only); H1 flat, M1 destroyed by costs (PF 0.46) |
| M04 | z-score vs SMA20 +/-2 sigma re-entry | H1, D1, M5; exit z=0; stop z=+/-3 or ATR (34 pts) | all negative; M5 avg -1.2 pips/trade (t -25 in pips) | FAIL |
| M05 | Classic pivots | fade S1/R1 (limit or rejection bar) -> PP, stop half/full way to S2/R2, day 00/22 UTC, open-inside-S1/R1 filter; break of R1 -> R2 (H1 40 pts, M15 4 pts) | fade H1: train +0.03 R (t 1.4) but val -0.02 R, 29 % yrs; break: val t -5.1 | FAIL - fades flat, breaks lose (touch-frequency logic confirmed, sec. 3, but not tradable) |
| M06 | Fibonacci pivots | same fade/break rules with 0.382/0.618/1.0 levels (16 pts) | fade val t -3.0, break val t -7.3 | FAIL |
| M07 | Camarilla H3/L3 fade, H4/L4 break | fade H3/L3 -> C or opposite, stop beyond H4/L4; break at H4/L4 -> +0.5/1.0 x range (H1 32 pts, M15 8 pts) | fade H1: train +0.02 R (t 1.2, 2207 trades), val -0.01 R, t -0.5; break val t -2.1 | FAIL (train edge of the limit fade is an entry-bar-fill artefact, sec. 4) |
| M08 | Woodie pivots | (H+L+2C)/4 and (H+L+2*open)/4, fade and break (16 pts) | fade val t -1.2, break val t -4.3 | FAIL |
| M09 | Round numbers 00/50 | M15 fade of first touch (stop 15, target 25/50) and break (>12 pips through, target 50/100), 00 vs 00+50 vs placebo 25/75 (24 pts) | fade val t -3.4; break val t -1.0 | FAIL - first touches *continue* on average (+1.25 pips/30 min, t 3.5), too small to trade |
| M10 | Turtle soup / PDH-PDL fade | sweep 3..15/30 pips beyond PDH/PDL then close back inside; target PD mid / opposite; H1, M15 (16 pts); D1 20-day turtle soup (12 pts) | M15: val 162 trades, +0.19 R, PF 1.29, t 1.11, 86 % yrs - but every train grid point is negative (best t -0.26) | FAIL (near-miss on M15: validate-only, no train support); H1 flat, D1 turtle soup val t -0.5 |
| M11 | Weekly-open mean reversion | Tue/Wed close >= 0.75/1/1.5 ADR from weekly open -> fade, target weekly open, stop 0.5/1 ADR, Fri 15:00 London exit (12 pts) | val t -0.68, PF 0.92 | FAIL - base rate of return to the weekly open falls to 26 % at 1-1.5 ADR (sec. 3) |
| M12 | Daily-open mean reversion | NY session fade when >= 0.5/0.75 ADR from the 00/22 UTC open, target open (16 pts) | train t -4.8, val t -2.6 | FAIL - price returns to the open only 10 % of the time after a 0.5-0.75 ADR excursion |
| M13 | Fade 3-day > 1 % streaks (tastyfx) | streak 3, cum 0.5/1/1.5 %, hold 1-3, no / 1 ATR stop, fade vs momentum (36 pts) | fade 1.5 %, hold 1, 1 ATR stop: train 229 trades, +0.09 R, PF 1.52, t 2.4, neighbourhood +0.22; val 59 trades, +0.03 R, PF 1.11, t 0.34, 71 % yrs | FAIL - sign survives, size does not (t 0.34); tastyfx's 59 % win rate becomes 56 % here |
| M14 | Caporale-Plastun abnormal days | D1 contrarian / momentum next day (k 1.5/2/2.5 sd of 20 days, hold 1-2, 24 pts); H1 intraday momentum once the day is flagged abnormal (18 pts) | D1: val t -1.56 (contrarian); H1 momentum leg: train +2.6 pips/trade (t 1.2), val -4.2 pips, t -2.1 | FAIL both legs after costs |
| M15 | Quantified Strategies daily MR (rules not public) | reconstruction: lowest/highest close of n=3..10 days, hold 1-2, long / both (16 pts) | best train t 1.15 (pips); val -0.7 pips/trade, t -0.37 | FAIL (reconstruction; vendor's 0.06 %/trade is below one spread) |
| Q01 | Backtrex vendor suite | replicated Connors RSI(2) D1 and MACD+RSI H1 SL45/TP90 (2 RSI filters) on 2016-10-02..2022-12-31 (vendor window minus HOLDOUT), plus a 12-point grid | MACD+RSI: 563 trades, 32 % win, PF 0.90, -3.3 pips/trade (vendor: 1,977 trades, PF 0.80 over 10 y); RSI(2): 28 trades, PF 2.2 here vs vendor PF 0.78 over 75 trades (sample too small, long-only 8 trades PF 0.99) | AUDIT: vendor's losing MACD+RSI reproduced; RSI(2) inconclusive at 28 trades, no edge on 2003-2015 |
| Q02 | Dukascopy contest sample | MA7/MA14 cross TP10/SL20 on H1 (8 pts) and M1 (1 pt) | H1 val 1,756 trades, PF 0.83, t -3.8; M1 17,268 trades, PF 0.83, t -11 | FAIL - as expected for a contest demo rule |
| Q03 | MQL5 market EA audit | not implementable: no entry rules, grid/martingale logic undisclosed | - | NOT IMPLEMENTED (meta-entry) |
| Q05 | EPAT walk-forward TSMOM | position = sign(close - close[20/60/120/250]), reverse on flip, no / 3 ATR stop (8 pts); daily-return Sharpe table | lookback 120: train Sharpe 0.38, val Sharpe 0.28 (ann. +2.0 %), 86 % yrs; trade-level val 41 trades, PF 1.8, t 1.07 | FAIL on our rules (t < 2, 41 trades) but consistent with EPAT's 'low positive' Sharpe ~0.5 claim at lookback 120 |
| Q06 | ML direction baseline | logistic + LightGBM on 25 daily features (lagged returns, realised vol, momentum, RSI, z, range, dow, month), fit on TRAIN, expanding-window yearly refits inside VALIDATE | logit: val accuracy 52.4 % (1,824 days, binomial p 0.023 one-sided, 2 models tried), P&L +1.8 pips/day after 1.4 pips/RT, PF 1.10, t 1.5, Sharpe 0.56, 57 % yrs; LightGBM 51.1 %, PF 1.02 | FAIL - accuracy barely above 50 %, after-cost edge insignificant; train in-sample 70 % vs CV 51 % for LightGBM shows how easy it is to overfit |

**Nothing survives validation.** Near-misses worth a second look only with a hypothesis that explains the train/validate split:
M03 on D1 (validate +0.14 R but concentrated in 2019), M10 on M15 (validate PF 1.29, 86 % years, but no train support at all),
M13 (positive both periods, too small to be significant), Q05 TSMOM-120 (positive both periods, 41 validate trades).

## 2. Per-family results (train best params; stats = trades / win % / avg R or pips / PF / t / years positive)

| id | family | tf | best params (train) | TRAIN | VALIDATE | neighbourhood median | verdict |
|---|---|---|---|---|---|---|---|
| M01 | M01_crsi2_d1 | D1 | {thr: 10, exit_on_trend_cross: false, sl_atr: 2.0, sides: long} | 84 / 56% / 0.000 R / PF 1.00 / t 0.00 / 58% | 27 / 70% / 0.024 R / PF 1.13 / t 0.25 / 40% | -2.124 (neg) | FAIL: too few validation trades; t-stat 0.25 < 2; PF 1.13 < 1.15; only 40% years positive; parameter neighbourhood not positive on train |
| M02 | M02_rsi14_d1 | D1 | {exit_rsi: 50, sl_atr: 1.5, tp_mode: rsi, max_hold: 10} | 84 / 38% / -0.077 R / PF 0.85 / t -0.66 / 38% | 40 / 35% / -0.087 R / PF 0.84 / t -0.49 / 43% | -0.134 (neg) | FAIL: negative on validation; t-stat -0.49 < 2; PF 0.84 < 1.15; only 43% years positive; parameter neighbourhood not positive on train |
| M02 | M02_rsi14_h4 | H4 | {exit_rsi: 60, sl_atr: 1.5, tp_mode: rsi, max_hold: 60} | 609 / 30% / -0.039 R / PF 0.94 / t -0.64 / 38% | 303 / 35% / 0.084 R / PF 1.13 / t 0.93 / 57% | -0.040 (neg) | FAIL: t-stat 0.93 < 2; PF 1.13 < 1.15; only 57% years positive; parameter neighbourhood not positive on train |
| M03 | M03_bb_d1 | D1 | {rsi_filter: false, sl_mode: atr, sl_val: 2.0, max_hold: 20} | 152 / 55% / -0.025 R / PF 0.94 / t -0.34 / 38% | 91 / 59% / 0.144 R / PF 1.38 / t 1.42 / 71% | -0.046 (neg) | FAIL: t-stat 1.42 < 2; parameter neighbourhood not positive on train |
| M03 | M03_bb_h1 | H1 | {rsi_filter: false, sl_mode: band, sl_val: 1.0, max_hold: 24} | 4059 / 58% / -0.002 R / PF 0.99 / t -0.20 / 54% | 2222 / 59% / -0.009 R / PF 0.97 / t -0.56 / 43% | -0.003 (neg) | FAIL: negative on validation; t-stat -0.56 < 2; PF 0.97 < 1.15; only 43% years positive; parameter neighbourhood not positive on train |
| M03 | M03_bb_m1 | M1 | {rsi_filter: true, k: 2.5, sl_mode: atr, sl_val: 2.0, max_hold: 240} | 52667 / 42% / -0.211 R / PF 0.64 / t -47.30 / 0% | 26440 / 38% / -0.338 R / PF 0.46 / t -58.52 / 0% | -0.207 (neg) | FAIL: negative on validation; t-stat -58.52 < 2; PF 0.46 < 1.15; only 0% years positive; parameter neighbourhood not positive on train |
| M04 | M04_z_h1 | H1 | {entry_z: 2.0, stop_mode: atr, stop_val: 3.0, max_hold: 48} | 4057 / 63% / -0.010 R / PF 0.96 / t -1.02 / 38% | 2180 / 63% / -0.013 R / PF 0.95 / t -1.00 / 57% | -0.020 (neg) | FAIL: negative on validation; t-stat -1.00 < 2; PF 0.95 < 1.15; only 57% years positive; parameter neighbourhood not positive on train |
| M04 | M04_z_d1 | D1 | {entry_z: 2.5, stop_mode: atr, stop_val: 2.0, max_hold: 20} | 54 / 57% / -0.002 R / PF 1.00 / t -0.01 / 46% | 38 / 50% / -0.081 R / PF 0.83 / t -0.53 / 29% | -0.026 (neg) | FAIL: negative on validation; t-stat -0.53 < 2; PF 0.83 < 1.15; only 29% years positive; parameter neighbourhood not positive on train |
| M04 | M04_z_m5 | M5 | {entry_z: 2.0, stop_mode: z, stop_val: 3.0, max_hold: 48} | 55665 / 47% / -2.246 R / PF 0.14 / t -1.07 / 0% | 30364 / 44% / -0.235 R / PF 0.56 / t -45.08 / 0% | -1.246 (neg) | FAIL: negative on validation; t-stat -45.08 < 2; PF 0.56 < 1.15; only 0% years positive; parameter neighbourhood not positive on train |
| M05 | M05_classic_fade | H1 | {ptype: classic, mode: fade, entry_style: limit, day_start: 0, require_open_inside: false, sl_frac: 1.0} | 2036 / 52% / 0.028 R / PF 1.07 / t 1.40 / 77% | 1108 / 50% / -0.021 R / PF 0.95 / t -0.75 / 29% | -0.017 (neg) | FAIL: negative on validation; t-stat -0.75 < 2; PF 0.95 < 1.15; only 29% years positive; parameter neighbourhood not positive on train |
| M05 | M05_classic_break | H1 | {ptype: classic, mode: break, entry_style: close, day_start: 0, require_open_inside: true, sl_frac: 1.0} | 1615 / 56% / -0.044 R / PF 0.85 / t -2.72 / 15% | 914 / 53% / -0.115 R / PF 0.67 / t -5.14 / 0% | -0.084 (neg) | FAIL: negative on validation; t-stat -5.14 < 2; PF 0.67 < 1.15; only 0% years positive; parameter neighbourhood not positive on train |
| M05 | M05_classic_fade_m15 | M15 | {ptype: classic, mode: fade, entry_style: reject, day_start: 22, require_open_inside: true, sl_frac: 0.5} | 1364 / 43% / -0.094 R / PF 0.82 / t -3.28 / 23% | 758 / 40% / -0.130 R / PF 0.76 / t -3.32 / 29% | -0.095 (neg) | FAIL: negative on validation; t-stat -3.32 < 2; PF 0.76 < 1.15; only 29% years positive; parameter neighbourhood not positive on train |
| M06 | M06_fib_fade | H1 | {ptype: fib, mode: fade, entry_style: limit, day_start: 0, require_open_inside: false, sl_frac: 1.0} | 2098 / 38% / -0.074 R / PF 0.88 / t -2.82 / 23% | 1148 / 36% / -0.107 R / PF 0.83 / t -3.02 / 0% | -0.107 (neg) | FAIL: negative on validation; t-stat -3.02 < 2; PF 0.83 < 1.15; only 0% years positive; parameter neighbourhood not positive on train |
| M06 | M06_fib_break | H1 | {ptype: fib, mode: break, entry_style: close, day_start: 0, require_open_inside: false, sl_frac: 1.0} | 1610 / 62% / -0.111 R / PF 0.62 / t -7.69 / 0% | 932 / 61% / -0.143 R / PF 0.55 / t -7.31 / 0% | -0.151 (neg) | FAIL: negative on validation; t-stat -7.31 < 2; PF 0.55 < 1.15; only 0% years positive; parameter neighbourhood not positive on train |
| M07 | M07_cam_fade | H1 | {ptype: camarilla, mode: fade, entry_style: limit, cam_tp: c, day_start: 22, require_open_inside: true} | 2207 / 54% / 0.023 R / PF 1.05 / t 1.16 / 54% | 1234 / 53% / -0.013 R / PF 0.97 / t -0.50 / 57% | 0.011 (ok) | FAIL: negative on validation; t-stat -0.50 < 2; PF 0.97 < 1.15; only 57% years positive |
| M07 | M07_cam_fade_m15 | M15 | {ptype: camarilla, mode: fade, entry_style: limit, cam_tp: c, day_start: 0, require_open_inside: false} | 2405 / 51% / -0.048 R / PF 0.90 / t -2.55 / 23% | 1346 / 51% / -0.060 R / PF 0.87 / t -2.45 / 0% | -0.050 (neg) | FAIL: negative on validation; t-stat -2.45 < 2; PF 0.87 < 1.15; only 0% years positive; parameter neighbourhood not positive on train |
| M07 | M07_cam_break | H1 | {ptype: camarilla, mode: break, entry_style: close, tp_rng: 1.0, day_start: 0, require_open_inside: true} | 1642 / 46% / 0.011 R / PF 1.02 / t 0.40 / 54% | 887 / 43% / -0.076 R / PF 0.85 / t -2.11 / 14% | -0.042 (neg) | FAIL: negative on validation; t-stat -2.11 < 2; PF 0.85 < 1.15; only 14% years positive; parameter neighbourhood not positive on train |
| M08 | M08_woodie_fade | H1 | {ptype: woodie, mode: fade, entry_style: limit, day_start: 0, require_open_inside: true, sl_frac: 1.0} | 2025 / 51% / 0.010 R / PF 1.02 / t 0.47 / 54% | 1087 / 49% / -0.035 R / PF 0.92 / t -1.22 / 29% | -0.012 (neg) | FAIL: negative on validation; t-stat -1.22 < 2; PF 0.92 < 1.15; only 29% years positive; parameter neighbourhood not positive on train |
| M08 | M08_woodie_break | H1 | {ptype: woodie, mode: break, entry_style: close, day_start: 0, require_open_inside: true, sl_frac: 1.0} | 1602 / 56% / -0.036 R / PF 0.88 / t -2.04 / 23% | 873 / 52% / -0.107 R / PF 0.70 / t -4.29 / 0% | -0.051 (neg) | FAIL: negative on validation; t-stat -4.29 < 2; PF 0.70 < 1.15; only 0% years positive; parameter neighbourhood not positive on train |
| M09 | M09_rn_fade | M15 | {mode: fade, levels: placebo, sl_pips: 15, tp_pips: 50, lookback: 96} | 2773 / 28% / -0.126 R / PF 0.83 / t -3.91 / 15% | 1115 / 30% / -0.155 R / PF 0.77 / t -3.41 / 0% | -0.140 (neg) | FAIL: negative on validation; t-stat -3.41 < 2; PF 0.77 < 1.15; only 0% years positive; parameter neighbourhood not positive on train |
| M09 | M09_rn_break | M15 | {mode: break, levels: placebo, confirm_pips: 12, tp_pips: 100, lookback: 24} | 8458 / 30% / -0.002 R / PF 1.00 / t -0.09 / 54% | 2860 / 35% / -0.029 R / PF 0.95 / t -1.03 / 29% | -0.036 (neg) | FAIL: negative on validation; t-stat -1.03 < 2; PF 0.95 < 1.15; only 29% years positive; parameter neighbourhood not positive on train |
| M10 | M10_pdhl_h1 | H1 | {sweep_min: 3, sweep_max: 15, tp: opp, day_start: 22} | 478 / 31% / -0.101 R / PF 0.84 / t -1.38 / 23% | 264 / 34% / -0.002 R / PF 1.00 / t -0.02 / 57% | -0.113 (neg) | FAIL: negative on validation; t-stat -0.02 < 2; PF 1.00 < 1.15; only 57% years positive; parameter neighbourhood not positive on train |
| M10 | M10_pdhl_m15 | M15 | {sweep_min: 3, sweep_max: 30, tp: opp, day_start: 22} | 444 / 26% / -0.025 R / PF 0.97 / t -0.26 / 54% | 162 / 33% / 0.193 R / PF 1.29 / t 1.11 / 86% | -0.050 (neg) | FAIL: t-stat 1.11 < 2; parameter neighbourhood not positive on train |
| M10 | M10_tsoup_d1 | D1 | {n: 20, min_age: 4, hold: 4, tp_atr: 0, sl_pips: 2.0} | 74 / 28% / 0.338 R / PF 1.50 / t 0.92 / 62% | 56 / 25% / -0.126 R / PF 0.82 / t -0.48 / 43% | 0.057 (ok) | FAIL: negative on validation; t-stat -0.48 < 2; PF 0.82 < 1.15; only 43% years positive |
| M11 | M11_wopen_h1 | H1 | {dist_adr: 0.75, sl_adr: 0.5, days: 12} | 513 / 37% / -0.010 R / PF 0.98 / t -0.18 / 54% | 288 / 36% / -0.051 R / PF 0.92 / t -0.68 / 43% | -0.044 (neg) | FAIL: negative on validation; t-stat -0.68 < 2; PF 0.92 < 1.15; only 43% years positive; parameter neighbourhood not positive on train |
| M12 | M12_dopen_h1 | H1 | {day_start: 0, dist_adr: 0.75, sl_adr: 0.25, ny_end: 19} | 1019 / 44% / -0.123 R / PF 0.68 / t -4.81 / 15% | 528 / 43% / -0.093 R / PF 0.75 / t -2.62 / 29% | -0.111 (neg) | FAIL: negative on validation; t-stat -2.62 < 2; PF 0.75 < 1.15; only 29% years positive; parameter neighbourhood not positive on train |
| M13 | M13_streak_d1 | D1 | {streak: 3, min_cum_pct: 1.5, hold: 1, sl_atr: 1.0, direction: fade} | 229 / 58% / 0.090 R / PF 1.52 / t 2.41 / 62% | 59 / 56% / 0.028 R / PF 1.11 / t 0.34 / 71% | 0.220 (ok) | FAIL: t-stat 0.34 < 2; PF 1.11 < 1.15 |
| M14 | M14_abn_d1 | D1 | {window: 20, k: 1.5, hold: 2, sl_atr: 1.0, direction: contrarian} | 418 / 48% / 0.023 R / PF 1.07 / t 0.55 / 62% | 217 / 42% / -0.084 R / PF 0.78 / t -1.56 / 57% | 0.020 (ok) | FAIL: negative on validation; t-stat -1.56 < 2; PF 0.78 < 1.15; only 57% years positive |
| M14 | M14_abn_h1 | H1 | {window: 20, k: 1.5, last_entry_hour: 18, sl_atr: 0} | 676 / 50% / 2.421 pips / PF 1.14 / t 1.16 / 46% | 388 / 45% / -4.194 pips / PF 0.71 / t -2.07 / 29% | 0.666 (ok) | FAIL: negative on validation; t-stat -2.07 < 2; PF 0.71 < 1.15; only 29% years positive |
| M15 | M15_qs_d1 | D1 | {n: 5, hold: 1, sides: both} | 1163 / 53% / 2.730 pips / PF 1.09 / t 1.15 / 69% | 638 / 51% / -0.699 pips / PF 0.96 / t -0.37 / 43% | 1.074 (ok) | FAIL: negative on validation; t-stat -0.37 < 2; PF 0.96 < 1.15; only 43% years positive |
| Q01 | Q01_macdrsi_h1 | H1 | {rsi_mode: above50, sl_pips: 30, tp_pips: 90} | 2092 / 27% / 0.041 R / PF 1.06 / t 1.08 / 54% | 832 / 23% / -0.096 R / PF 0.88 / t -1.66 / 14% | 0.001 (ok) | FAIL: negative on validation; t-stat -1.66 < 2; PF 0.88 < 1.15; only 14% years positive |
| Q02 | Q02_macross_h1 | H1 | {kind: ema, tp_pips: 20, sl_pips: 20} | 3838 / 45% / -0.138 R / PF 0.75 / t -8.82 / 0% | 1756 / 48% / -0.088 R / PF 0.83 / t -3.81 / 14% | -0.258 (neg) | FAIL: negative on validation; t-stat -3.81 < 2; PF 0.83 < 1.15; only 14% years positive; parameter neighbourhood not positive on train |
| Q02 | Q02_macross_m1 | M1 | {kind: sma, tp_pips: 10, sl_pips: 20} | 61455 / 65% / -0.063 R / PF 0.82 / t -22.27 / 0% | 17268 / 65% / -0.059 R / PF 0.83 / t -11.09 / 0% | -0.063 (neg) | FAIL: negative on validation; t-stat -11.09 < 2; PF 0.83 < 1.15; only 0% years positive; parameter neighbourhood not positive on train |
| Q05 | Q05_tsmom_d1 | D1 | {lookback: 120, sl_atr: 0} | 96 / 38% / 69.606 pips / PF 1.90 / t 1.55 / 58% | 41 / 34% / 49.985 pips / PF 1.80 / t 1.07 / 71% | 0.028 (ok) | FAIL: t-stat 1.07 < 2 |
## 3. Descriptive statistics behind the catalogue claims (TRAIN only unless stated)

**M05 pivot touch frequencies** (classic pivots from the previous UTC day, weekdays; MQL5 study 2003-2010 in brackets):

| period | days | high>=PP | high>=R1 | high>=R2 | high>=R3 | low<=PP | low<=S1 | low<=S2 | low<=S3 | low<=S1 open<PP | low<=S1 open>=PP |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2003-2010 | 2072 | 87.8 (87.4) | 45.8 (43.1) | 19.4 (20.4) | 7.9 (6.3) | 86.7 (85.9) | 42.8 (45.3) | 16.4 (21.5) | 5.9 (6.6) | 51.2 (50.4) | 34.9 (36.2) |
| 2003-2015 | 3373 | 87.9 | 44.8 | 18.3 | 7.0 | 87.9 | 43.1 | 17.0 | 6.1 | 51.4 | 35.2 |

The MQL5 numbers replicate almost exactly, so "R1/S1 is reached on fewer than half the days" is true - but a resting
order at S1 is filled exactly on those 43-46 % of days, and conditional on being filled the move to PP is not more
likely than the move to S2 (fade families above are flat to negative).

**M09 round numbers** (M15, first touch of the next level with no touch in the previous 24 bars, 07-20 UTC, forward
30-min move in the direction of the approach): 00 levels 2,921 touches, +1.25 pips (t 3.5), reversal 49 %;
00+50 levels 5,549 touches, +1.08 pips (t 4.4), reversal 50 %; placebo 25/75 levels 5,494 touches, +0.46 pips (t 1.9),
reversal 52 %. Round numbers behave marginally differently from placebo levels - as mild continuation, not reversal -
and the effect (about 1 pip) is below the cost of a trade.

**M11/M12 base rates** (H1): P(price trades back through the weekly open before Friday 15:00 London | distance at
Tuesday 23:00 UTC) = 82 % for < 0.5 ADR, 51 % for 0.5-1 ADR, 26 % for 1-1.5 ADR, 10 % beyond 1.5 ADR (n = 293/233/98/48 weeks).
P(back through the daily open by 21:00 UTC | distance at 13:00 UTC) = 72 % for < 0.25 ADR, 31 % for 0.25-0.5, 10 % for
0.5-0.75, 6 % for 0.75-1, 1 % beyond 1 ADR (n = 1403/946/557/255/184 days). Large excursions from the open do not revert
within the week/day, which is why M11 and M12 lose.

**Q01/Q02 vendor rules, fixed parameters, 2016-10-02..2022-12-31** (the vendor window minus HOLDOUT; a replication,
not a parameter choice):

| rule | trades | win % | PF (pips) | avg pips | total pips | t |
|---|---|---|---|---|---|---|
| Backtrex Connors RSI(2) D1 (RSI<5, close>SMA200, exit SMA5 or SMA200 cross, no stop) | 28 | 75 | 2.20 | +27.9 | +782 | 1.68 |
| same, long only | 8 | 63 | 0.99 | -0.2 | -2 | -0.01 |
| Backtrex MACD+RSI H1 SL45/TP90, RSI>50 filter | 563 | 32 | 0.90 | -3.3 | -1854 | -1.23 |
| Backtrex MACD+RSI H1 SL45/TP90, RSI not extreme | 750 | 32 | 0.91 | -2.7 | -2030 | -1.17 |
| Dukascopy MA7/MA14 H1 TP10/SL20 | 2356 | 59 | 0.64 | -3.1 | -7187 | -9.95 |

Vendor: MACD+RSI 1,977 trades PF 0.80 (-53 %); RSI(2) 75 trades, 54.7 %, PF 0.78 (-4.5 %). The MACD+RSI loss is
reproduced in direction and size per trade. RSI(2) gives 28 trades here (the vendor's 75 over ten years includes 2023+
and probably a different day boundary); on 2003-2015 none of the 16 RSI(2) variants had positive expectancy.

**Q05 TSMOM daily Sharpe** (close-to-close, 1.4 pips per flip): lookback 20: train 0.27 / validate -0.53; 60: -0.04 / 0.01;
120: 0.38 / 0.28 (annualised +3.9 % / +2.0 %, 69 % / 86 % years positive); 250: -0.09 / -0.15. Only the 120-day
lookback is positive in both periods, at about half the Sharpe EPAT reports (0.54).

**Q06 ML baseline** (`experiments/results/meanrev_systematic_ml.csv`): logistic regression (C=0.05, standardised) and
LightGBM (300 trees, 7 leaves, lr 0.02, min 100 samples/leaf) on 25 features; TRAIN in-sample accuracy 54.3 % / 69.8 %,
TRAIN 5-fold time-series CV 51.3 % / 50.7 %; VALIDATE (refit every January on all data to date) 52.4 % / 51.1 % over 1,824
days (up-day base rate 50.4 %). Trading the sign every day after 1.4 pips per round trip: logit +1.8 pips/day, PF 1.10,
t 1.5, Sharpe 0.56, 4/7 years positive; LightGBM +0.3 pips/day, PF 1.02. With the catalogue's 0.55 probability threshold:
logit 420 days in market, +2.8 pips/day, PF 1.15, t 1.06, 5/7 years; LightGBM 687 days, PF 1.14, t 1.27, 3/7 years.
Top LightGBM features: rv20, SMA200 distance, r3, r9, RSI2. Conclusion: 51-52 % directional accuracy, consistent with the
honest write-ups cited in the catalogue; it does not clear the survival bar.

## 4. Caveats found while checking trades

* **Limit-entry fades are flattered by the engine.** For limit orders the engine allows a take-profit exit on the entry
  bar (no path information). With the best train parameters 20 % (classic S1/R1), 28 % (camarilla H3/L3), 22 % (Woodie)
  and 16 % (Fibonacci) of trades exit at TP on the fill bar; excluding them the train avg R is -0.20 to -0.39 instead of
  about 0. The small positive train t-stats of the limit-fade families (M05 1.4, M07 1.2) are therefore artefacts;
  the rejection-bar (market entry) variants, which the engine treats conservatively, are negative on both periods.
* **M04 on M5**: with sd(20) of a few pips, the z = 3 stop is 2-6 pips from entry, so R-multiples explode (train avg R
  -2.2 with t only -1.1); the pip statistics (-1.2 pips/trade, t -25) are the meaningful ones.
* The Backtrex comparison window excludes 2023+ (HOLDOUT), so trade counts are lower than the vendor's.
* M15 is a reconstruction (vendor sells the rules); M14's intraday leg uses UTC days and close-to-close returns, the
  paper's exact day boundary is unknown.
