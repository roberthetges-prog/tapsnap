# Research round 2: finding NEW predictability (read fully before writing code)

Goal: raise genuine out-of-sample predictability of EUR/USD with new information and new structure,
not parameter tweaks. Everything is judged by one fixed walk-forward protocol so arms are comparable.

## Inputs (do not rebuild them; extend only by adding columns in your own module)
* `data/processed/features_daily.parquet`  6,186 NY-close sessions 2003-2026, 141 columns. Index = session start
  (UTC 21/22:00 of the previous calendar day); `close_time` = session close. Features use data <= close_time
  (macro lagged one calendar day). Labels: `fwd_1d`, `fwd_2d`, `fwd_5d`, `fwd_10d` (bp), `tb_5d_1atr` (+1/-1/0).
  `label_end_1d/5d/10d` = when the label is known. Feature groups: price/technical (ret_*, rv_*, dist_sma*, rsi*,
  donch*, streak, adx14, sess_*_bp), calendar (dow, dom, month, bd_from_start, bd_to_end, is_month_end),
  events (h_to_fomc/ecb/nfp/cpi, h_since_*, h_to_any_high, n_high_next_24h, last_surprise_* z-scores),
  macro (us2y, ea2y, spread2y, spread10y, curves, policy_diff, d_spread*_k, fv_resid_z, vix, dxy/spx/gold/oil/sx5e/zt
  returns, usd_* cross-pair returns, usd_factor_*, eur_vs_usd_factor_20), positioning (cot_net_pct, cot_z52, cot_d4, cot_lev_z52).
* `data/processed/features_hourly.parquet` 147,490 hourly bars 2003-2026, 68 columns. Index = bar start (UTC).
  Labels `fwd_1h/4h/8h/24h` (bp) and `label_end_*h`. Includes local hours (hour_london, hour_ny), session-so-far
  returns, distances to previous-day levels, event clocks, and `d_*` = previous session's daily features.
* Builder: `src/eurusd/featstore.py` (read it to see exactly how each column is lagged).
* Cross-asset raw series: `data/processed/cross/*_D1.parquet` (2003+) and `*_H1.parquet` (last ~2 years only).
* Everything else from round 1: `src/eurusd/{data,features,backtest,evaluate,strategies*}.py`, reports in `reports/`.

## Protocol (`src/eurusd/wf.py`, fixed - do not alter)
```python
from eurusd.wf import walk_forward, pnl_from_positions, report, to_positions, YEARS
pred = walk_forward(df, fit, predict, label_end=df["label_end_1d"])   # yearly expanding window, test years 2010..2026
pos  = to_positions(pred, "sign", threshold=...)                       # or your own mapping to [-1, 1]
pnl  = pnl_from_positions(pos, df["fwd_1d"], df["close"], cost_pips=1.2)   # also run cost_pips=0.6 as sensitivity
tbl  = report(pnl, periods_per_year=252, name="my_arm", n_arms=6)       # per year + aggregates + deflated-Sharpe p
```
* The model for test year Y is fitted on rows whose label is known before Y-01-01 ONLY. All hyper-parameters,
  thresholds, feature selection and ensembling weights must be chosen inside the training window (time-ordered CV
  or a fixed rule). Never choose anything by looking at a test year. Never touch 2023-2026 separately.
* Thresholds must be expressed in training-window terms (e.g. a quantile of training predictions), not fixed by eye.
* Costs: 1.2 pips per unit turnover (retail) is the headline; report 0.6 pips as sensitivity. For hourly arms the cost
  matters enormously: trade rarely and only when the forecast exceeds the cost.
* Report the SAME table for every variant you try (keep a count: the number of variants you ran goes into the
  report so the lead can deflate). Pick your arm's single final variant by a rule stated BEFORE you see results
  (e.g. "the variant with the best 2010-2015 walk-forward Sharpe", then report its full 2010-2026 record).
* periods_per_year: 252 for one decision per session; for hourly arms use the number of decision bars per year.
* Success bar for an arm to be considered: 2010-2026 net Sharpe > 0.4 with 2016-2026 net Sharpe > 0.3 and
  2023-2026 not negative, at 1.2 pips. Be honest when you fail; a clean negative is valuable.

## Deliverables (per arm)
* Code in `src/eurusd/arms/<arm>.py` with a `run(cost_pips=1.2) -> (positions Series, report DataFrame)` entry point,
  reproducible from the feature store.
* Out-of-sample positions saved to `experiments/results/arms/<arm>_positions.parquet` (index, pos, fwd return, net_bp)
  and the report tables to `experiments/results/arms/<arm>_report.csv` (all variants, with a `variant` column and a
  `final` flag). The lead stacks the finals walk-forward, so the positions must be the OOS ones.
* A short markdown `reports/arm_<arm>.md`: idea, features, model, selection rule, number of variants tried, the
  final record (per year), what new information helped, what did not, and anything suspicious (leak checks you did).
* Leak checks you MUST do and report: (1) shuffle the labels and show the pipeline gives ~0 Sharpe; (2) shift the
  features forward by one period and show the result collapses; (3) list the top features and sanity-check that
  none is a label in disguise.
* 4 CPUs are shared by 5 arms: keep any single fit under a minute; LightGBM with <= 400 trees and
  `num_threads=1`, or linear models, are fine. Use `nohup ... &` with logs for long loops and poll the log.
