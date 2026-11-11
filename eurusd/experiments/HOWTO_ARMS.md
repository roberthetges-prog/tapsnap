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

---
# Round 4 addendum (2026-11-11)

Read the Round 3 addendum first; all of it still applies (max 12 variants, incremental test against
`combine(["weak_signals","regime_trend"], "EW")`, honest lags, no touching live files or other arms).
Rounds 1-3 summary and what is already known NOT to work: `research/RESEARCH_LOG.md` and `reports/arm_*.md`. Do not
re-test those; bring new information or new structure.
Additional reporting for round 4: besides Sharpe/t, report the out-of-sample HIT RATE of the final variant
(share of active decisions with positive net P&L, and share with the correct sign before costs) for
2010-26 / 2016-26 / 2023-26, with the number of decisions. If your target is not direction (e.g. range, volatility,
probability of touching a level), report classification accuracy or Brier score against a naive baseline as well.
CPU: four arms share 4 cores; one process per arm, set OMP_NUM_THREADS=1; when working with M1/M5 data load only the
columns and years you need (M1 parquet is 106 MB, 9 M rows) and cache intermediate daily aggregates to
`data/processed/` under a name starting with your arm.

---
# Round 5 addendum (2026-11-11): the product is multi-week direction

Read the Round 3 and Round 4 addenda first; they still apply (max 12 candidates, honest lags, leak checks, no touching
live files or other arms). Read `research/RESEARCH_LOG.md` in full: ~440 trials so far; what failed must not be re-tested.

Product (owner): DIRECTIONAL POSITION TRADING in EUR/USD, holds of weeks to a quarter, a call only when the odds are good.
State of the art to beat (reports/arm_selective.md): the AGREEMENT RULE - call only when positioning sign (cot_z52), the
20-day 2y-spread trend sign (d_spread2y_20) and the house macro-score sign agree (about 44 % of sessions): right
56 / 59 / 61 / 72 % at 10 / 21 / 42 / 63 sessions non-overlapping (2010-26), 57 % at 21 sessions since 2016, unconfirmed
since 2023. Rebuild it with `eurusd.arms.selective` helpers (read that module) so your numbers reconcile with it first.

How a round-5 arm is judged (native to the horizon):
1. Standalone: for each new signal, directional accuracy at 21 / 42 / 63 sessions on weekly decisions AND on
   non-overlapping decisions, with Wilson intervals on the non-overlapping count; 2010-26, 2016-26, 2023-26.
2. As an EXTRA VOTE: (a) accuracy and decisions/year of "agreement rule AND new signal agrees" vs the agreement rule alone;
   (b) accuracy of calls the new signal makes when the three old signals do NOT agree (does it extend coverage?);
   (c) the paired difference with a bootstrap interval. An extra vote that raises accuracy by cutting the sample to a
   handful of trades proves nothing: report decisions per year next to every accuracy.
3. Daily-stream incremental test from the Round 3 addendum, as before.
4. Timing placebo: shift the new signal by +63 and +126 sessions; a slow level that scores the same when stale is a
   regime bet, not information (this killed the macro surprise index).
Success bar: the extra-vote rule beats the agreement rule by >= 3 accuracy points at 21 and 42 sessions on non-overlapping
decisions in BOTH 2010-26 and 2016-26 with at least 6 decisions a year, is not worse in 2023-26, and the timing placebo
loses at least half of the gain. Say plainly if you fail.
Data notes: FRED is reachable only with `curl --http1.1` from some shells and not at all from others; GitHub mirrors
(see `macro_fetch.py` MIRRORS) and the ECB API (https://data-api.ecb.europa.eu/service/data/<FLOW>/<KEY>?format=csvdata)
work; Yahoo chart API needs a browser User-Agent and rate-limits (retry with backoff, cache everything you fetch).
State the publication lag you assume for every monthly or weekly series and lag conservatively.

---
# Round 6 addendum (2026-11-11)

Read the Round 3, 4 and 5 addenda first; all still apply (Round 5 defines the multi-week judging: accuracy at 21 / 42 / 63
sessions on weekly and non-overlapping decisions with intervals and decisions per year, the extra-vote tests against the
agreement rule, the +63 / +126 session timing placebo, the daily incremental test). `research/RESEARCH_LOG.md` now lists
~480 trials; do not re-test what failed. Two standing lessons to respect:
* REPLICATION beats backtest: two EUR/USD-only findings (positioning trend, residual order flow) failed on other
  currencies. Where an idea can be tested on other pairs or other eras with the identical rule, do that and report it.
* A slow signal that scores the same when 3-6 months stale is a regime bet, not information. Always run the placebo.

---
# Round 7 addendum (2026-11-11): information the project has never had

Read the Round 3-6 addenda first; all apply (Round 5: multi-week judging, extra-vote tests against the agreement rule,
+63 / +126 session placebo, daily incremental test; Round 6: replication and the stale-signal lesson).
`research/RESEARCH_LOG.md` lists ~520 trials. `research/DATA_SCOPING.md` and `research/data_sources.json` describe 36
data sources with verified download URLs, date ranges, lags and pitfalls: your sources are named in your brief; read their
entries there before fetching. Third-party copies of vendor data are research-only: record the URL and the date you
fetched it, cross-check a sample against any independent source you can reach, and report gaps. Cache everything under
`data/macro/` or `data/processed/cross/` with your arm's prefix.
Because these sources are new, also report for each signal: its correlation with the three agreement-rule inputs
(cot_z52, d_spread2y_20, house score) and with EUR/USD's own trailing 1- and 3-month return (a signal that merely
restates the recent price move is not new information: show accuracy after regressing that out, as arm K's control did).
FRED: use `curl --http1.1` with NO browser user-agent.
