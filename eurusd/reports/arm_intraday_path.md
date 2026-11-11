# Arm K - intraday_path: what the 1-minute path inside the day says about the next day / week (round 4)

Code: `src/eurusd/arms/intraday_path.py` (`build_features()`, `run(cost_pips=1.2)`; `python src/eurusd/arms/intraday_path.py 1.2`
also writes the controls, leak checks, incremental test and the two post-hoc checks; 2 minutes, one process). Outputs in
`experiments/results/arms/`: `intraday_path_positions.parquet` (final variant, OOS: `pos`, `fwd_bp`, `net_bp`),
`intraday_path_report.csv` (19 backtests at 1.2 pips + the same positions at 0.6 and 0 pips; columns `variant`, `kind`, `cost_pips`,
`final`, hit rates), `intraday_path_all_positions.parquet`, `intraday_path_fitlog.json` (weights, orientations, thresholds per year),
`intraday_path_controls.csv`, `intraday_path_control_resid_stream.parquet` (control (a), NOT an arm file),
`intraday_path_control_followup.csv`, `intraday_path_leakchecks.csv`, `intraday_path_incremental.csv`, `intraday_path_correlations.csv`,
`intraday_path_feature_corr.csv`, `intraday_path_signal_corr.csv`, `intraday_path_residual_signal_corr.csv`,
`intraday_path_late_artefact.csv`, `intraday_path_late_lagged_execution.csv`, `intraday_path_tranche_hit.csv`, log `logs/intraday_path.log`.
New derived data: `data/processed/intraday_path_features.parquet`.

## Verdict in one paragraph
**The arm fails.** The final variant picked by the pre-declared rule (best 2010-2015 net Sharpe among 11 candidates) is the 5-day
tick-rule order-flow proxy with the literature sign (`w5_ofi`, long after net up-tick flow): net Sharpe at 1.2 pips
**-0.02 (t -0.07) for 2010-2026, -0.48 (t -1.61) for 2016-2026, -0.72 (t -1.43) for 2023-2026**; hit rate 48.4% / 47.4% / 47.3%.
It looked good in 2010-2015 (+0.64) and reversed afterwards. Adding it to the live pair lowers the EW combination on 2016-2026 from
0.636 to 0.302. No path feature predicts next-day or next-week direction robustly: of the 16 single-signal backtests the only
one above the bar is the 1-day **fade of the last hour before the close** (`d1_late`, a diagnostic, 0.45 / 0.42 / 0.67, hit 53.0%),
and a post-hoc check shows it is largely a bid-price / rollover effect: executed one hour after the close it drops to
0.14 / 0.17 / 0.47 (t 0.56). The literature-signed asymmetry measures (signed jump variation, realised skewness: fade) are positive
only after 2016 (`w5_rsj` 0.21 / 0.63 / 0.98, but -0.31 in 2010-2015; t 0.88 overall). One thing deserves a follow-up and nothing
more: the pre-declared "is it ret_1d in disguise" control (a), the same order-flow signal with the existing price features regressed
out, is **positive** (0.53 (t 2.23) / 0.41 / 0.68, survives a one-session lag, circular-shift p 0.005, would lift the three-way
combination to 0.725 on 2016-2026). It was not a candidate, it is one of 22 backtests (deflated-Sharpe p 0.39), so it is a
hypothesis for a pre-registered test, not a result.

## Idea
The feature store describes a session with OHLC-type numbers. The 1-minute path inside the session carries more: asymmetry of
up- and down-variation, jumps, which session made the move, how clean the move was, what happened in the last hour, when the
extremes were made, and the tick-by-tick direction of trading. The high-frequency literature reports that some of these predict
returns over the next day or week. One decision per NY-close session; horizons: next session and next five sessions.

## Features (`build_features()`, cache `data/processed/intraday_path_features.parquet`)
Source: `data/processed/EURUSD_M1.parquet` (HistData 1-minute BID bars, true UTC, rows from 2002-12-31), no publication lag: every
number of row T uses bars stamped inside [T, T + 24h) only, T = session start 22:00 UTC, i.e. it is known at `close_time`.
6,186 rows, index identical to `features_daily.parquet` (checked: the last 1-minute close of every session equals the feature-store
`close` exactly, and open-to-close plus `gap_bp` reproduces `ret_1d` to 1e-13 bp). 38 columns: the measures below, their 5-day
means (`*_5d`, at least 3 of 5 sessions), bar counts, quality flag `ok`.

* 5-minute sampling: last 1-minute close of each 5-minute bin; returns between consecutive observed bins of the same session; the
  first return is measured from the session's first 1-minute open (the weekend / rollover gap is in no realised measure).
* A 5-minute return spanning more than 15 minutes without a tick is excluded from the realised measures (it would look like a jump).
* **Quality rule (fixed before any result):** all path features of a session are NaN when it has fewer than 200 valid 5-minute returns
  or more than 120 minutes of such holes. 141 sessions fail, 113 of them between 2023-02-20 and 2023-07-28 (the hours missing in the
  2023 source file); the signals are 0 there (the final is active on 48% of the 2023 sessions instead of ~80%).

| feature | definition | literature | prior stated before any result |
|---|---|---|---|
| `rsj` | signed jump variation (RS+ - RS-) / RV from 5-minute returns | Barndorff-Nielsen, Kinnebrock & Shephard 2010; Patton & Sheppard 2015; Bollerslev, Li & Zhao 2020 | **negative** (fade) |
| `rskew` | realised skewness sqrt(n) sum r^3 / RV^1.5 | Amaya, Christoffersen, Jacobs & Vasquez 2015 | **negative** (fade) |
| `rkurt` | realised kurtosis n sum r^4 / RV^2 | Amaya et al. 2015 | unsigned: cached, not traded as a direction |
| `jump` | signed jump day: Huang-Tauchen ratio statistic (bipower variation, tripower quarticity) above 2.326 (1% level), sign of the largest 5-minute return; 0 otherwise. 18% of sessions since 2010 are flagged (the test over-rejects without a time-of-day volatility correction; kept as declared) | Barndorff-Nielsen & Shephard 2006; Huang & Tauchen 2005; Jiang & Zhu 2017 (continuation in stocks) vs Andersen et al. 2003 (FX news absorbed in minutes) | none usable: sign from the training window |
| `ny_share` | r_NY / (\|r_Asia\| + \|r_Europe\| + \|r_NY\|); Asia = start -> 07:00 London, Europe = 07:00 London -> 08:00 New York, NY = 08:00 New York -> close (DST-aware) | Lou, Polk & Skouras 2019; Breedon & Ranaldo 2013 (unconditional patterns only) | none: training window |
| `eff` | signed efficiency ratio (log close - log open) / sum of \|5-minute moves\| | Kaufman | none: training window |
| `late` | log close - log price at 16:00 New York, divided by the session's realised vol | Gao, Han, Li & Zhou 2018 (same-day effect) | none for the next day: training window |
| `hl_time` | time of the session high minus time of the session low, in fractions of the session (1-minute closes, so ghost-tick wicks cannot matter) | practitioner | none: training window |
| `ofi` | tick-rule order-flow proxy: sum w_i d_i / sum w_i over 1-minute bars, d_i = tick-rule sign of the close change (zero change -> previous sign), w_i = min(high - low, 30 pips). Weighting by \|close change\| would be algebraically the 1-minute efficiency ratio, hence the range weight. HistData volume is always 0, so this is direction of quoting activity, not traded volume | Evans & Lyons 2002, 2005; Rime, Sarno & Sojli 2010 | **positive** (follow) |

"Sign from the training window": every test year the orientation is the sign of the training-window correlation of the standardised
signal with the label of the variant's horizon. Fitted orientations were stable: all five were negative (fade) in every year at the
1-day horizon; at the 5-day horizon `ny_share` and `eff` were positive (follow) in nearly every year, `late` negative.

## Model (house method of `arms/weak_signals.py`)
* Standardise: divide by the training-window sd (no demeaning), clip at +-2, halve. `jump` at the 1-day horizon stays in {-1, 0, +1}.
  At least 250 available training rows.
* Target s_t = orientation x sign(z_t) when \|z_t\| exceeds the training median of \|z\|, else 0, times min(1, median_train(rv_21d_bp) / rv_21d_bp).
* `d1`: daily feature, label `fwd_1d`, position = s_t. `w5`: 5-day mean of the feature, label `fwd_5d` (training rows with
  `label_end_5d` before the test year), position = (s_t + ... + s_t-4) / 5, i.e. 1/5 tranches held five sessions; P&L booked daily on
  `fwd_1d`, costs on the change of the summed position.
* Combination: weights proportional to max(t_i, 0) of the training-window correlation of the oriented signal with the label
  (for training-signed signals this is \|t_i\|, which favours them; stated in the module before the run); same sign/median mapping.

## Variants and selection rule (written in the module docstring before the first run)
* **11 candidates** for the final: the eight single signals at the 5-day horizon, `combo_d1`, `combo_w5`, `combo_both` (mean of the two).
* **8 diagnostics**, same table, not eligible: the eight single signals at the 1-day horizon.
* **2 controls** declared in advance on the final: (a) signals replaced by their residual from a training-window OLS on
  [ret_1d / rv_1d_bp, body_rel, close_in_range - 0.5] (5-day means for w5); (b) the final's pipeline on those three existing features alone.
* **1 post-hoc backtest** added after seeing the results (`d1_late` executed 60 minutes after the close).
* **Count for deflation: 19 pre-declared backtests (the report's deflated-Sharpe p uses 19), 22 in total.** The brief's limit of 12
  refers to the candidates (11).
* Rule: final = candidate with the highest 2010-2015 walk-forward net Sharpe at 1.2 pips. 2016+ was never used for a choice.

## Results at 1.2 pips, walk-forward 2010-2026 (hit sign = share of active sessions with the right sign before costs; hit net = share with positive net P&L)
### Candidates
| variant | SR 2010-15 | SR 2010-26 (t) | SR 2016-26 (t) | SR 2023-26 (t) | hit sign / net 2010-26 (n) | hit sign / net 2016-26 (n) | hit sign / net 2023-26 (n) | gross SR 2010-26 | SR at 0.6 pips | turnover / yr |
|---|---|---|---|---|---|---|---|---|---|---|
| w5_rsj | -0.31 | +0.21 (+0.88) | +0.63 (+2.11) | +0.98 (+1.95) | 52.4% / 51.0% (3604) | 52.9% / 51.5% (2252) | 53.5% / 51.6% (762) | +0.30 | +0.26 | 35 |
| w5_rskew | -0.58 | -0.00 (-0.00) | +0.39 (+1.29) | +0.69 (+1.36) | 51.8% / 50.5% (3536) | 52.8% / 51.4% (2261) | 52.3% / 50.3% (748) | +0.09 | +0.04 | 35 |
| w5_jump | -0.96 | -0.44 (-1.85) | -0.03 (-0.10) | +0.13 (+0.26) | 47.9% / 47.2% (1065) | 48.7% / 48.3% (555) | 49.4% / 49.4% (162) | -0.39 | -0.42 | 9 |
| w5_ny_share | +0.42 | -0.17 (-0.73) | -0.64 (-2.15) | -1.20 (-2.39) | 48.0% / 47.0% (3677) | 47.6% / 46.6% (2308) | 47.5% / 46.2% (757) | -0.08 | -0.13 | 35 |
| w5_eff | +0.32 | -0.18 (-0.77) | -0.60 (-2.02) | -0.49 (-0.99) | 49.1% / 48.0% (3643) | 48.8% / 47.7% (2283) | 49.5% / 48.4% (759) | -0.10 | -0.14 | 35 |
| w5_late | -0.43 | +0.04 (+0.18) | +0.37 (+1.25) | +0.51 (+1.02) | 49.7% / 48.7% (3505) | 50.1% / 49.0% (2196) | 50.3% / 48.4% (707) | +0.12 | +0.08 | 32 |
| w5_hl_time | +0.00 | -0.13 (-0.52) | -0.23 (-0.76) | +0.13 (+0.26) | 50.1% / 49.0% (3692) | 49.6% / 48.6% (2335) | 50.7% / 49.5% (767) | -0.04 | -0.08 | 36 |
| **w5_ofi** (final) | +0.64 | -0.02 (-0.07) | -0.48 (-1.61) | -0.72 (-1.43) | 48.4% / 47.7% (3418) | 47.4% / 46.7% (2212) | 47.3% / 46.4% (745) | +0.07 | +0.03 | 32 |
| combo_d1 | +0.33 | +0.04 (+0.18) | -0.16 (-0.52) | +0.43 (+0.86) | 52.7% / 51.5% (1968) | 52.2% / 50.7% (1248) | 54.1% / 52.5% (413) | +0.39 | +0.21 | 167 |
| combo_w5 | +0.17 | -0.25 (-1.04) | -0.58 (-1.95) | -1.01 (-2.01) | 47.4% / 46.2% (3637) | 46.6% / 45.6% (2270) | 46.8% / 45.8% (736) | -0.16 | -0.20 | 36 |
| combo_both | +0.40 | -0.09 (-0.37) | -0.46 (-1.52) | -0.21 (-0.43) | 50.1% / 47.9% (3829) | 50.1% / 47.8% (2411) | 50.1% / 47.4% (789) | +0.21 | +0.06 | 90 |

### Diagnostics: single signals at the 1-day horizon
| variant | SR 2010-15 | SR 2010-26 (t) | SR 2016-26 (t) | SR 2023-26 (t) | hit sign / net 2010-26 (n) | hit sign / net 2016-26 (n) | hit sign / net 2023-26 (n) | gross SR 2010-26 | SR at 0.6 pips | turnover / yr |
|---|---|---|---|---|---|---|---|---|---|---|
| d1_rsj | -0.10 | -0.38 (-1.57) | -0.59 (-1.96) | -0.12 (-0.24) | 50.4% / 49.2% (2073) | 49.1% / 47.7% (1276) | 49.5% / 48.1% (426) | -0.03 | -0.20 | 174 |
| d1_rskew | -0.22 | -0.38 (-1.58) | -0.50 (-1.67) | +0.09 (+0.18) | 50.9% / 49.7% (2063) | 50.6% / 49.1% (1256) | 52.2% / 50.1% (419) | -0.05 | -0.21 | 172 |
| d1_jump | +0.10 | -0.34 (-1.42) | -0.71 (-2.37) | +0.31 (+0.62) | 49.9% / 48.8% (766) | 49.5% / 48.4% (426) | 53.5% / 52.1% (142) | -0.09 | -0.22 | 76 |
| d1_ny_share | +0.16 | -0.09 (-0.37) | -0.26 (-0.87) | -0.33 (-0.65) | 52.3% / 51.3% (2087) | 51.6% / 50.3% (1339) | 51.1% / 50.1% (445) | +0.26 | +0.09 | 176 |
| d1_eff | -0.11 | -0.17 (-0.71) | -0.21 (-0.71) | -0.13 (-0.26) | 51.1% / 50.0% (2069) | 50.1% / 48.7% (1290) | 50.2% / 48.4% (428) | +0.19 | +0.01 | 178 |
| d1_late | +0.50 | +0.45 (+1.86) | +0.42 (+1.39) | +0.67 (+1.32) | 53.0% / 52.1% (1970) | 53.3% / 52.5% (1296) | 56.1% / 54.8% (416) | +0.77 | +0.61 | 161 |
| d1_hl_time | -0.13 | -0.26 (-1.08) | -0.35 (-1.18) | -0.66 (-1.30) | 51.3% / 50.0% (2045) | 50.6% / 49.1% (1329) | 47.7% / 46.0% (461) | +0.07 | -0.09 | 172 |
| d1_ofi | -0.39 | -0.38 (-1.58) | -0.38 (-1.26) | -0.17 (-0.33) | 48.5% / 47.3% (1879) | 49.3% / 47.9% (1201) | 49.9% / 48.0% (400) | -0.04 | -0.21 | 164 |

Reading: at the 5-day horizon nothing is significant over 2010-2026 and six of eight signals change sign between 2010-2015 and
2016-2026. The two literature fades (`w5_rsj`, `w5_rskew`) earn 0.63 / 0.39 after 2016 and lose in 2010-2015. The training-signed
`w5_ny_share` had a training t of +5.5 in 2003-2009 (overlapping labels) and lost in every later block. At the 1-day horizon
turnover is 160-180 position units a year, about 0.35 Sharpe of costs, and only `d1_late` has a gross edge worth naming.

### Final variant `w5_ofi`, per year (and control (a) for comparison)
| period | n | net Sharpe | t | sum bp | active | Sharpe at 0.6 pips | control (a) residual-OFI Sharpe |
|---|---|---|---|---|---|---|---|
| 2010 | 260 | +1.72 | +1.75 | +907 | 0.82 | +1.74 | +1.39 |
| 2011 | 260 | -0.32 | -0.32 | -147 | 0.75 | -0.30 | +0.81 |
| 2012 | 260 | +1.04 | +1.06 | +481 | 0.84 | +1.08 | +0.99 |
| 2013 | 259 | +0.59 | +0.59 | +208 | 0.72 | +0.62 | +0.78 |
| 2014 | 258 | -0.25 | -0.26 | -73 | 0.77 | -0.20 | -0.13 |
| 2015 | 259 | +0.62 | +0.63 | +329 | 0.76 | +0.65 | +0.31 |
| 2016 | 259 | -0.85 | -0.87 | -367 | 0.77 | -0.81 | -0.26 |
| 2017 | 259 | +0.63 | +0.64 | +242 | 0.80 | +0.67 | +0.79 |
| 2018 | 260 | -1.33 | -1.35 | -530 | 0.80 | -1.28 | -0.47 |
| 2019 | 260 | -1.75 | -1.78 | -410 | 0.77 | -1.66 | +1.03 |
| 2020 | 260 | +0.29 | +0.29 | +130 | 0.82 | +0.33 | +0.24 |
| 2021 | 259 | -0.18 | -0.18 | -52 | 0.87 | -0.12 | -0.45 |
| 2022 | 260 | -0.07 | -0.07 | -26 | 0.82 | -0.02 | +1.26 |
| 2023 | 258 | -0.15 | -0.16 | -37 | 0.48 | -0.11 | +1.18 |
| 2024 | 261 | -0.82 | -0.84 | -235 | 0.83 | -0.75 | +0.09 |
| 2025 | 260 | -0.65 | -0.66 | -207 | 0.88 | -0.59 | +1.23 |
| 2026 | 220 | -1.20 | -1.12 | -322 | 0.80 | -1.14 | +0.03 |
| 2010-2026 | 4372 | -0.02 | -0.07 | -110 | 0.78 | +0.03 | +0.53 |
| 2016-2026 | 2816 | -0.48 | -1.61 | -1814 | 0.79 | -0.43 | +0.41 |
| 2023-2026 | 999 | -0.72 | -1.43 | -802 | 0.74 | -0.66 | +0.68 |
| 2010-2015 | 1556 | +0.64 | +1.59 | +1705 | 0.78 | +0.67 | +0.73 |
| 2016-2022 | 1817 | -0.39 | -1.04 | -1013 | 0.81 | -0.34 | +0.30 |

Deflated-Sharpe p of the final (19 backtests): 0.97. Hit rate of the 1/5 tranches against their own 5-day label: 50.9% / 47.2% / 48.7%
(1,809 / 1,183 / 376 overlapping targets). Turnover 32 position units a year.

### Combination weights
`combo_d1` put 28-54% on `late` every year (the rest on `jump`, `ny_share`, `hl_time`), 0 on `ofi`; `combo_w5` put 48-62% on
`ny_share`, 0 on `rsj` and `rskew` (their training correlation had the wrong sign for the prior until 2025). Full history in
`intraday_path_fitlog.json`.

## Is it new information? Correlation with the existing price features (same session)
| signal | ret_1d | ret_1d / rv | range_pips | range_rel_adr | close_in_range | body_rel | Spearman ret_1d | R2 on [ret_1d/rv, body_rel, close_in_range] |
|---|---|---|---|---|---|---|---|---|
| rsj | +0.78 | +0.79 | +0.01 | +0.02 | +0.69 | +0.80 | +0.83 | 0.64 |
| rskew | +0.53 | +0.50 | +0.02 | +0.03 | +0.43 | +0.52 | +0.68 | 0.27 |
| jump | +0.23 | +0.23 | -0.00 | -0.00 | +0.20 | +0.25 | +0.25 | 0.06 |
| ny_share | +0.63 | +0.67 | +0.01 | +0.01 | +0.83 | +0.70 | +0.69 | 0.69 |
| eff | +0.91 | +0.96 | +0.01 | +0.02 | +0.84 | +0.96 | +0.97 | 0.94 |
| late | +0.14 | +0.13 | +0.04 | +0.04 | +0.23 | +0.14 | +0.09 | 0.07 |
| hl_time | +0.76 | +0.85 | +0.01 | +0.01 | +0.71 | +0.87 | +0.83 | 0.76 |
| ofi | +0.77 | +0.82 | +0.01 | +0.01 | +0.72 | +0.82 | +0.82 | 0.68 |
| rkurt | +0.04 | +0.03 | +0.13 | +0.33 | +0.03 | +0.03 | +0.04 | 0.00 |

Six of the eight signals are largely the day's direction in another unit: `eff` is ret_1d (R2 0.94), `hl_time`, `ny_share`, `ofi`,
`rsj` have R2 0.64-0.76 on three existing columns. Only `late` (R2 0.07), `jump` (0.06) and `rkurt` (0.00, but it correlates 0.33
with `range_rel_adr`) are mostly new. Among themselves: `rsj`-`rskew` 0.88, `eff`-`ofi` 0.85, `eff`-`rsj` 0.85, `late` below 0.16 with
everything. After removing the three existing features, `rsj`-`rskew` stay at 0.91 and `ofi` is nearly unrelated to the rest (0.32 with `eff`, below 0.1 otherwise).

Controls on the final (declared in advance):
* (b) the same pipeline on [ret_1d/rv, body_rel, close_in_range] alone: -0.37 / -0.68 / -0.73. The 5-day direction of price was
  followed in training and reversed out of sample; that component is what sank `w5_ofi`, `w5_eff`, `w5_ny_share` and `combo_w5`.
* (a) `w5_ofi` with those features regressed out: **0.53 (t 2.23) / 0.41 (t 1.38) / 0.68 (t 1.35)**, 2010-2015 0.73, 0.58 / 0.46 / 0.74 at 0.6 pips,
  hit sign 51.1% / 50.8% / 50.4% (3,344 / 2,168 / 743 active sessions), 30 units of turnover a year, positive in 13 of 17 years.
  Post-hoc robustness of this one stream (`intraday_path_control_followup.csv`, no new variant): features lagged one session
  0.61 / 0.58 / 0.85, five sessions 0.37 / 0.50 / 0.05, 21 sessions 0.02 / 0.07 / 0.44; circular-shift null (200 draws) p = 0.005 /
  0.045 / 0.085; daily P&L correlation 0.12 with weak_signals and -0.03 with positioning; three-way EW with it 0.645 / 0.725 / 0.640
  against 0.563 / 0.636 / 0.356 for the live pair. Because it survives a one-session lag it cannot be the closing-bid effect described
  below. **Caveats: it was not a candidate, it is the best of 22 backtests (deflated-Sharpe p 0.39 with 22 trials, 0.36 with 19), the
  hit rate is 51%, and there is no second 1-minute series in the repository to replicate it on.** I do not count it as a result.

## The one positive single signal is mostly a bid-price effect (post-hoc, `late_artefact_check()`)
`d1_late` fades the move from 16:00 New York to the close: full-sample correlation with `fwd_1d` -0.061 (n 6,045), net 0.45 / 0.42 /
0.67, gross 0.77. The 1-minute file holds bid prices and the feature-store session closes inside the 17:00 New York rollover, when
spreads widen and the bid is marked down. A low closing bid makes `late` negative and the next close-to-close return positive, and
nobody can buy at that bid.
* Average `late` return 2016-2026: -0.68 bp; average return of the first 60 minutes of the next session: +0.92 bp (a mark-down and its recovery).
* Correlation of `late` with the first 15 minutes of the next session -0.095 (winter closes -0.139), with the first 4 hours -0.123,
  with the remaining 20 hours -0.023. More than half of the covariance with `fwd_1d` is realised within four hours of the close.
* Same positions entered and exited 60 minutes after each close: gross Sharpe 0.46, net **0.14 (t 0.56) / 0.17 / 0.47**, hit 51.6%.
What remains is a reversal of the last hour in the thin hours after the rollover, gross about 0.5 Sharpe at 160 units of turnover a
year, measured on bids only. Not tradable at 1.2 pips, and real spreads at that hour are wider.

## Incremental test (addendum rule)
| EW combination | 2010-2026 | 2016-2026 | 2023-2026 |
|---|---|---|---|
| weak_signals + regime_trend | 0.563 (t 2.35) | 0.636 (t 2.13) | 0.356 (t 0.71) |
| + intraday_path (final `w5_ofi`) | 0.340 (t 1.42) | 0.302 (t 1.01) | 0.003 (t 0.01) |

The arm enters the combination in 14 of 17 years (its trailing t was positive because of 2010-2015) and costs 0.33 Sharpe on 2016-2026.
Daily P&L correlation of the final with weak_signals 0.20 / 0.16 / 0.00 and with positioning 0.09 / 0.05 / 0.00 (monthly 0.32 and 0.18 for 2010-2026).
**Fails all three parts of the bar: standalone 2016-2026 -0.48 (needs > 0.3), 2023-2026 negative, three-way below two-way.**

## Leak checks (final variant; `intraday_path_leakchecks.csv`)
1. Shuffled labels, 40 permutations of `fwd_1d` (`fwd_5d` rebuilt from the shuffled series): 2010-2026 net Sharpe mean -0.09 (the cost
   drag), sd 0.25; gross mean -0.01.
2. Features shifted forward by 1 / 5 / 21 sessions: -0.10 / -0.01 / +0.08 (the actual is -0.02: there is nothing to collapse).
   Look-ahead controls: features shifted back by 1 session +1.24 (t 5.2), by 5 sessions +6.02 (t 25): the harness exposes a look-ahead
   at once, because the path features of a session contain its own return. Circular-shift null: actual at the 41st / 88th / 91st
   percentile from the top (p 0.41 / 0.88 / 0.91).
3. Label in disguise: full-sample correlation of every standardised signal with its label is between -0.03 and +0.04, except `d1_late`
   -0.061 (explained above). The correlation with the SAME session's return is 0.14-0.91, as it must be for path features, which is why
   check 2 matters. Truncation test: the features of 12 random sessions rebuilt from 1-minute bars stamped before that session's close
   are identical (max difference 0.0, no NaN mismatch).
4. Alignment: session close from M1 equals the feature-store close on all 6,186 rows; the feature index equals the feature-store index.

## What helped, what did not, what is suspicious
* Did not help: every literal reading of the eight ideas as a direction signal, at either horizon, and all three combinations.
  Most path features are the day's direction in disguise, and the direction of the last day or week has no stable sign.
* Signed-jump / skewness fade: right sign after 2016 only; not distinguishable from noise over the full sample.
* Suspicious and explained: the last-hour fade (bid mark-down at the rollover). Anything built on the closing bid has this problem;
  the feature-store label itself is bid close to bid close.
* Open hypothesis, not a result: order-flow proxy net of the price move (control (a)). A fair test needs a pre-registered arm with
  that single variant, preferably on 1-minute data of other pairs, and a paper forward record from zero.
* Data limits: no traded volume and no ask side; 113 sessions of 2023 are unusable; jump test without periodicity correction.
