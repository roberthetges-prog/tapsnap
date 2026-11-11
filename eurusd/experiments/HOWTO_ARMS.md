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

---
# Round 3 addendum (2026-11-11): new information only

Round 2 verdict: the only predictability that survived is slow macro drift + speculative positioning
(live exposure = EW of `arms/weak_signals.py` tstat/sign and positioning sign(cot_z52) x vol scale;
walk-forward net Sharpe 0.56 / 0.64 / 0.36 for 2010-26 / 2016-26 / 2023-26). Daily ML on the existing
features, intraday ML, regimes, trend and event models all failed (reports/arm_*.md; failed code in research/archive/).
So round 3 arms must bring NEW INFORMATION, not new models on the same columns.

Extra rules for round 3:
* At most 12 variants per arm (count them). Prefer simple, economically motivated signals over model searches.
* Besides the standard table, report INCREMENTAL value: use `eurusd.arms.meta.combine(["weak_signals","regime_trend","<your_arm>"], "EW")`
  vs `combine(["weak_signals","regime_trend"], "EW")` (both via `report_combo`) and the daily-P&L correlation of your
  stream with those two. An arm that is positive but 0.8 correlated with positioning adds nothing.
* Success bar: standalone 2016-2026 net Sharpe > 0.3 at 1.2 pips, 2023-2026 not negative, AND the three-way
  combination beats the two-way combination on 2016-2026. Say plainly if you fail.
* New raw data goes to `data/processed/cross/` or `data/macro/` with a line in the arm report saying source, date
  range and publication lag used. Lag everything honestly (daily closes of other markets: one calendar day, as
  `featstore._align_lagged` does; weekly CFTC: report date + 6 days).
* Yahoo chart API works with a browser User-Agent (see `live_data.py`); CFTC zips for 1999-2026 are already in
  `data/raw/cftc/` (all contracts, legacy `deacot*.zip` and TFF `fut_fin_txt_*.zip`; parsing helpers in `macro_fetch.py`).
* Deliverables as before: `src/eurusd/arms/<arm>.py` with `run(cost_pips=1.2)`, `experiments/results/arms/<arm>_positions.parquet`
  (pos, fwd_bp, net_bp), `<arm>_report.csv`, `reports/arm_<arm>.md`, the three leak checks. Do not commit; do not touch
  `state/`, `config/`, the live modules (`exposure.py`, `scenarios.py`, `brief.py`, `risk.py`) or other arms' files.
