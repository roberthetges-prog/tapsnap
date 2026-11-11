# Arm O — swing: EUR/USD position trading designed for the multi-week horizon

Code `src/eurusd/arms/swing.py` (`run(cost_pips=1.2)`; `PYTHONPATH=src python -m eurusd.arms.swing full` writes
everything in about seven minutes on one core, `fetch` re-downloads the FRED series this arm added, `leak` re-runs the
leak checks; `experiments/61_swing_report.py` rebuilds this file from the CSVs). Results in `experiments/results/arms/`:
`swing_positions.parquet` (daily stream of the flagged rule: `pos`, `fwd_bp`, `net_bp` after costs and carry, plus
`gross_bp`, `carry_bp`), `swing_trades.csv` (one row per trade), `swing_report.csv` (harness table, all 12 candidates,
`variant` and `final` columns), `swing_trade_stats.csv` (candidates and sensitivities by era), `swing_accuracy.csv`,
`swing_calibration.csv`, `swing_predictors.csv`, `swing_probabilities.parquet` (walk-forward P(up) of the nine
forecasters), `swing_weights.csv`, `swing_ablation.csv`, `swing_live_benchmark.csv`, `swing_pre1999_*.csv`,
`swing_incremental.csv`, `swing_leakchecks.csv`, `swing_label_corr.csv`, `swing_hitrates.csv`,
`swing_trades_all_candidates.csv`. Logs `experiments/results/arms/logs/swing*.log`. This report is generated from those
files.

## Verdict
**The arm fails, cleanly.** The declared selection rule finds no eligible rule: none of the 12 candidates has both
>= 8 (or the fallback >= 4) trades a year and a positive net expectancy in 2006-2015. `S_M_p55` is flagged `final`
only so that a stream exists for the lead's incremental test; it is not a recommendation.

1. **A calibrated 60 % call on the next month's direction practically does not exist.** With probabilities calibrated
   honestly in the training window, the transparent scorecard reaches P >= 0.60 on 23 of 249 month-ends in
   2006-2026 (1.1 a year); those calls were right 56.5 % of the time (Wilson 36.8-74.4).
   P >= 0.65 happened 2 times, P >= 0.70 never. The t-stat combination and the logistic model, whose probabilities are
   calibrated on inner out-of-sample scores, reach 0.55 on 12 and 35 month-ends and 0.60 on 1 and 16; their hit rates
   there (42 % for T at 0.55, 60 % and 50 % for L at 0.55 and 0.60) are all inside the noise.
2. **The probability does not sort the outcomes.** Scorecard, month-ends 2006-2026: stated 51 / 54 / 56 / 59 / 62 %,
   realised 57 / 51 / 60 / 42 / 52 %. Brier score 0.250 against 0.250 for "always 50 %".
3. **Best honest multi-week direction accuracy of the purpose-built system: 54.1 %** (scorecard, every month-end,
   246 non-overlapping decisions 2006-2026, Wilson 47.8-60.2, naive 50.2); 55.6 % in 2010-26, 57.1 % in
   2016-26, 50.0 % in 2023-26. The interval contains 50 %. Traded every month with a 3-ATR stop, after 1.2 pips and
   carry: +23 pips a trade, monthly-P&L Sharpe 0.28 (2006-26), 0.48 (2016-26), -0.14 (2023-26).
4. **Designing for the horizon did not beat the existing exposure held for a month.** The sign of the live daily
   combination read at month-ends and run through the same trade simulator (benchmark, not a candidate, and selected on
   this very period by rounds 1-2): 59.1 % right in 2010-26 (176 trades, Wilson 51.7-66.1), +58 pips a trade,
   Sharpe 0.64; 2016-26 58.7 % / 0.58; 2023-26 48.7 % / -0.28. The scorecard on the same window: 55.6 %.
5. **What carries the little there is**: speculative positioning (alone 59.8 % at month-ends 2006-26) and US-vs-euro-area
   equity momentum, i.e. the two house signals already live, plus 6-month oil since 2016. Rate levels, real rates, PPP,
   the 5-year average, curve slope, carry and (after 1998) trend are at 50 % or wrongly signed. Nothing new was found.
6. Incremental test: three-way 0.66 vs two-way 0.64 on 2016-26 (noise), 0.13 vs 0.36 on 2023-26 (worse).
   Standalone harness Sharpe of the flagged stream 0.28 / 0.40 / -0.37: the round-3 bar is missed (2023-26 negative).

## 1. Data and spans
Price (continuous daily frame, 13,248 sessions):

| src       | first      | last       | sessions   | what                                                                                                                  |
|:----------|:-----------|:-----------|:-----------|:----------------------------------------------------------------------------------------------------------------------|
| synth_dem | 1975-01-02 | 1998-12-31 | 6025       | synthetic euro = 1.95583 / DEM-per-USD; DEM daily = DKK daily (H.10) x monthly DEM/DKK; close only; ROBUSTNESS SAMPLE |
| h10       | 1999-01-04 | 2002-12-31 | 1037       | Fed H.10 noon-NY USD per EUR (ECB reference rate on the 32 weekdays without an H.10 quote); close only                |
| histdata  | 2003-01-02 | 2026-11-06 | 6186       | feature-store NY-close sessions (HistData H1), true session open/high/low                                             |

* Weekly ATR = mean true range of the last 13 weekly bars. Before 2003 only closes exist, so the close-only weekly
  range is scaled by 1.359 (ratio of true to close-only weekly range in 2003-2005, i.e. before the first test year).
  All test-period trades (2006+) use true session highs and lows for stops.
* Pre-1999 sample: FRED no longer serves the daily DEM series (`DEXGEUS` returns 404) and the repo's H.10 file has no
  DEM column, so the daily path is DKK/USD (H.10 daily) times the monthly-average DEM/DKK cross (FRED `EXGEUS` /
  `EXDNUS`), interpolated. Its monthly averages match `EXGEUS` to 0.1 % (sd of the log error 0.0011); applied to
  1999-2001, where the euro itself is known, the 21-session returns of the same construction are 0.995 correlated with
  the real ones and the daily returns 0.91. Good for a 21-session robustness test, not for anything daily.
* Repo series used with their lags: US 2y / 10y (`fred_DGS2`, `fred_DGS10`), `fred_T10Y3M`, Fed target (`fred_DFEDTAR`,
  `DFEDTARL/U`), ECB MRO, EONIA / euro short-term rate, AAA curve, VIX (`fred_VIXCLS`), DAX and S&P closes, Brent
  (`datahub_brent_daily`, an EIA spot price, treated as a market price): one calendar day. US CPI, HICP: 60 days from
  the month stamp. US 3-month interbank (`fred_IR3TIB01USM156N`): 45 days. CFTC legacy report: report date + 6 days,
  then one day.
* Main-sample walk-forward: training from 1999, test years 2006-2026 (7 training years for the first test year). The
  pre-1999 path is never used to fit anything in the main sample; it only gives the 5-year average and the PPP mean a
  history, so those two exist from 1999 instead of 2004.

New raw data (all `data/macro/`, fetched with curl from `fred.stlouisfed.org/graph/fredgraph.csv`):

| file | content | range | lag used |
|---|---|---|---|
| `fred_DEXDNUS.csv` | DKK per USD, daily H.10 | 1971-01-04 .. 2026-11-06 | price of the day (pre-1999 path only) |
| `fred_EXGEUS.csv`, `fred_EXDNUS.csv` | DEM and DKK per USD, monthly averages | 1971-01 .. 2001-12 / 2026-10 | used as a level bridge, pre-1999 only |
| `fred_IRLTLT01DEM156N.csv` | German 10-year yield, monthly average | 1956-05 .. 2026-09 | 45 days from the month stamp; euro-area 10y before 2004-09 |
| `fred_IR3TIB01DEM156N.csv` | German 3-month interbank, monthly | 1960-01 .. 2026-09 | 45 days; short rate before 1999 and 3m rate before 2004-09 |
| `fred_DEUCPIALLMINMEI.csv` | German CPI | 1955-01 .. 2025-03 | 60 days; spliced to the HICP index before 1996 |

Not obtained: S&P 500 before 2003 and the VIX term structure (VIX3M). Both need Yahoo; Yahoo answered HTTP 429 to a
plain request and the retry with a browser User-Agent was blocked by this session's permission layer, which I did not
work around. Consequence: `eqrel63` starts in
2003-04 (repo `spx_D1`, `gdaxi_D1`) and "VIX term" is replaced by the VIX level against its own 1-year median.

Which predictor exists over which span is the `first value` column of the next table (first weekly decision with a
value). In short: price-based, 10-year, short-rate, slope (10y-3m), carry, seasonality from 1975; valuation from 1980;
oil from 1987; VIX from 1991; positioning from 2000 (z52) / 2002 (z156); equities from 2003; everything that needs a
euro-area 2-year yield from 2004-09. The fitted models may use a predictor only once it has 156 weekly training rows.

## 2. Predictors, priors (fixed before any result) and single-predictor accuracy
Every predictor is oriented so that a positive value means "long EUR/USD" under the stated prior. The accuracy columns
are the share of weekly decisions on which the sign of the oriented predictor equals the sign of the next 21- / 42-session
return. No fitting is involved, so these are honest for the textbook priors; for the priors marked HOUSE the sign was
observed by rounds 1-2 on 2003-2026 and the 1999-2026 columns are in-sample for the sign. Weekly windows overlap: the
number of independent 21-session bets is about 345 for 1999-2026, 258 for 2006-2026, 133 for 2016-2026 and 236 for
1980-1998, so one standard error is about 2.7 / 3.1 / 4.3 / 3.3 points (half of that again for 42 sessions).

| predictor    | fam   | prior (sign on the raw quantity, reason)                                                 | definition                                                  | first value   | 21s 99-26   | 21s 06-26   | 21s 16-26   | 21s 80-98 DEM   | 42s 99-26   | 42s 06-26   | 42s 16-26   | 42s 80-98 DEM   |
|:-------------|:------|:-----------------------------------------------------------------------------------------|:------------------------------------------------------------|:--------------|:------------|:------------|:------------|:----------------|:------------|:------------|:------------|:----------------|
| rd2_lvl      | RL    | + high relative 2y yield attracts capital (carry / forward-premium puzzle)               | EA AAA 2y - US 2y                                           | 2004-09-10    | 49.4        | 49.0        | 50.7        |                 | 51.3        | 50.7        | 53.7        |                 |
| rd10_lvl     | RL    | + same at the long end                                                                   | EA 10y (German monthly to 2004-09, AAA after) - US 10y      | 1975-01-03    | 51.3        | 49.9        | 50.7        | 51.7            | 51.5        | 50.9        | 53.7        | 50.3            |
| pol_lvl      | RL    | + same for policy rates                                                                  | ECB MRO - Fed target (pre-1999: 3m interbank DE - US)       | 1975-01-03    | 52.4        | 48.5        | 50.7        | 52.6            | 55.5        | 51.2        | 53.7        | 53.4            |
| rrd2_lvl     | RL    | + real-rate differential (Dornbusch-Frankel)                                             | 2y differential - 12m inflation differential                | 2004-09-10    | 44.5        | 42.5        | 47.0        |                 | 45.2        | 43.3        | 47.4        |                 |
| rrd10_lvl    | RL    | + real-rate differential                                                                 | 10y differential - 12m inflation differential               | 1975-01-03    | 45.7        | 44.0        | 48.0        | 49.9            | 44.6        | 44.0        | 48.5        | 48.5            |
| rd2_d63      | RC    | + rising relative yields, slow adjustment of the currency                                | 3-month change of rd2                                       | 2004-12-03    | 53.4        | 52.5        | 52.1        |                 | 54.5        | 53.6        | 51.7        |                 |
| rd2_d126     | RC    | + same                                                                                   | 6-month change of rd2                                       | 2005-02-25    | 54.8        | 54.1        | 51.6        |                 | 53.5        | 52.9        | 50.1        |                 |
| rd10_d63     | RC    | + same                                                                                   | 3-month change of rd10                                      | 1975-04-04    | 51.6        | 51.5        | 52.0        | 54.8            | 51.2        | 51.1        | 49.0        | 53.1            |
| rd10_d126    | RC    | + same                                                                                   | 6-month change of rd10                                      | 1975-07-03    | 52.2        | 53.5        | 52.1        | 55.8            | 51.3        | 53.9        | 53.0        | 54.2            |
| pol_d63      | RC    | + relative policy tightening                                                             | 3-month change of the policy differential                   | 1975-04-04    | 50.3        | 50.2        | 49.4        | 52.4            | 50.1        | 51.0        | 53.4        | 54.8            |
| pol_d126     | RC    | + same                                                                                   | 6-month change of the policy differential                   | 1975-07-03    | 49.3        | 49.8        | 49.0        | 52.9            | 48.9        | 48.9        | 49.3        | 57.0            |
| rrd2_d126    | RC    | + rising real differential                                                               | 6-month change of rrd2                                      | 2005-02-25    | 49.9        | 48.8        | 50.0        |                 | 48.8        | 47.6        | 48.1        |                 |
| rrd10_d126   | RC    | + rising real differential                                                               | 6-month change of rrd10                                     | 1975-07-03    | 47.1        | 47.2        | 50.7        | 58.1            | 46.2        | 46.4        | 48.1        | 56.6            |
| ppp_dev      | VAL   | - CPI real exchange rate reverts to its mean (half-life 3-5y => ~1.5 %/month of the gap) | -(log real rate - expanding mean since 1975)                | 1980-01-11    | 49.6        | 49.4        | 49.3        | 50.4            | 46.8        | 45.4        | 46.3        | 52.1            |
| ma5y_dev     | VAL   | - reversion to the 5-year average                                                        | -(log spot - log 1260-session mean)                         | 1980-01-11    | 49.9        | 51.8        | 53.0        | 45.7            | 48.8        | 51.1        | 51.5        | 46.5            |
| mom63        | TR    | + time-series momentum (Moskowitz-Ooi-Pedersen)                                          | 63-session log return                                       | 1975-04-04    | 52.0        | 52.2        | 49.5        | 55.8            | 52.5        | 53.1        | 46.7        | 54.7            |
| mom126       | TR    | + same                                                                                   | 126-session log return                                      | 1975-07-03    | 52.6        | 53.1        | 50.2        | 52.5            | 52.5        | 53.1        | 51.5        | 53.7            |
| mom252       | TR    | + same (textbook; rounds 1-2 saw the opposite sign at the daily horizon)                 | 252-session log return                                      | 1976-01-09    | 50.6        | 49.2        | 49.1        | 56.5            | 49.5        | 47.4        | 48.6        | 57.2            |
| sma50_200    | TR    | + trend state                                                                            | sign(SMA50 - SMA200)                                        | 1975-10-17    | 52.1        | 52.6        | 49.8        | 54.4            | 51.5        | 51.6        | 48.3        | 54.4            |
| wma10_40     | TR    | + trend state                                                                            | sign(10-week - 40-week average of weekly closes)            | 1975-10-10    | 52.1        | 52.9        | 50.7        | 54.7            | 51.9        | 52.1        | 48.8        | 55.3            |
| brk126       | TR    | + breakout of the 6-month range                                                          | +1 after a 126-session closing high, -1 after a low (state) | 1975-07-03    | 51.3        | 52.0        | 49.5        | 54.9            | 50.6        | 50.4        | 48.8        | 55.5            |
| cot_z52      | POS   | + follow speculators (HOUSE finding; EUR-specific, fragile)                              | non-commercial net/OI, 52-week z                            | 2000-01-07    | 56.9        | 57.1        | 56.1        |                 | 57.8        | 60.2        | 59.1        |                 |
| cot_z156     | POS   | + same on a 3-year window (HOUSE)                                                        | 156-week z                                                  | 2001-12-28    | 56.4        | 55.3        | 55.0        |                 | 54.9        | 53.9        | 54.2        |                 |
| cot_ext      | POSX  | - crowded positioning reverses (textbook contrarian)                                     | -sign(z156) when abs(z156) > 1.5                            | 2001-12-28    | 45.8        | 46.0        | 47.7        |                 | 38.9        | 39.3        | 40.7        |                 |
| eqrel63      | EQ    | + euro-area equity outperformance draws flows (HOUSE sign F04)                           | 63-session return DAX - S&P 500 (local)                     | 2003-04-04    | 56.2        | 57.3        | 53.4        |                 | 58.1        | 59.8        | 56.0        |                 |
| vix_lvl      | EQ    | - high VIX = risk-off, dollar bid (textbook; expected weak)                              | -(VIX - its 252-session median)                             | 1991-01-04    | 50.5        | 49.8        | 49.1        | 53.6            | 49.1        | 48.6        | 48.8        | 58.4            |
| slope2_diff  | CURVE | - the steeper relative curve underperforms (Ang-Chen 2010)                               | -((EA10-EA2) - (US10-US2))                                  | 2004-09-10    | 48.9        | 48.3        | 50.5        |                 | 49.6        | 48.7        | 51.5        |                 |
| slope3m_diff | CURVE | - same with the 3-month rate                                                             | -((EA10-EA3m) - (US10-US3m))                                | 1975-01-03    | 51.4        | 47.8        | 50.4        | 49.5            | 52.3        | 47.9        | 51.0        | 52.0            |
| seas         | SEAS  | + December long / May short (HOUSE C03, no economic story)                               | share of the horizon in December - share in May             | 1975-01-03    | 55.5        | 53.4        | 55.2        | 50.6            | 52.9        | 50.8        | 53.0        | 45.8            |
| seas_month   | SEAS  | none: sign learned on the expanding training history (abs(t) >= 1)                       | month-of-year mean of the target, prior years only          | 1980-01-04    | 49.5        | 46.2        | 42.2        | 49.7            | 39.9        | 39.4        | 32.0        | 53.3            |
| oil_d63      | OIL   | - dearer oil worsens euro-area terms of trade                                            | -(63-session log change of Brent)                           | 1987-08-21    | 52.1        | 51.6        | 55.6        | 48.6            | 51.6        | 52.1        | 59.5        | 48.6            |
| oil_d126     | OIL   | - same                                                                                   | -(126-session log change of Brent)                          | 1987-11-20    | 53.6        | 54.9        | 57.7        | 47.0            | 53.3        | 55.3        | 58.9        | 50.4            |
| carry        | CARRY | + short-rate carry (expected weak)                                                       | EUR overnight - Fed target (pre-1999: 3m interbank)         | 1975-01-03    | 51.3        | 47.2        | 50.7        | 52.6            | 53.8        | 49.1        | 53.7        | 53.4            |

Reading it:
* Above 55 % at 21 sessions in 2006-2026: `cot_z52`, `cot_z156` and `eqrel63` (all HOUSE signs, positioning and
  equity momentum are already in the live exposure), nothing else. `oil_d126` and `rd2_d126` are at 54-55 %, `seas`
  at 53 %.
* **Trend at position-trading speed**: 52-53 % over 2006-2026 and 49-51 % over 2016-2026, against 53-57 % in the
  DEM era. Monthly holding does not rescue it; the round-2 finding stands. 12-month momentum is at 49 %.
* **Rate differential levels and carry**: 47-50 % in 2006-2026. **Real-rate differential levels are wrongly signed**
  (42-44 %): the currency with the higher real yield fell.
* **Valuation**: PPP gap 49 % at 21 sessions and 45 % at 42; 5-year average 52 %. As the prior said, a 3-5 year
  half-life is invisible at one or two months.
* **Curve slope (Ang-Chen)**: 48 %. **Positioning extremes, contrarian**: 46 % at 21 and 39 % at 42 sessions on only
  ~50 independent bets, i.e. fading extreme positioning was wrong; following it was right.
* **Month-of-year effect learned from the past** (`seas_month`): 46 % and 39 %, worse than a coin. The December/May
  rule (`seas`) is the only calendar effect with a positive record and it has no economic story.

## 3. Models, decision clocks, probabilities
Targets on a decision close: sign of the next 21-session return (`h21`), of the next 42-session return (`h42`), and a
symmetric triple barrier at 2 x weekly ATR within 42 sessions (`tb`; no touch = sign of the 42-session return).
Models, fitted on weekly decision rows whose label is known before the test year (`eurusd.wf.walk_forward`, expanding,
test years 2006-2026):
* **S** scorecard: sign votes, mean within family, mean across the 11 families. No fitted number in the score.
* **T** house combination: weights proportional to the positive part of each predictor's training t-stat.
* **L** ridge logistic regression, penalty chosen by inner time-ordered CV.
* Probability P(up) = sigmoid(b x score), no intercept, b >= 0 fitted in the training window: on the training scores
  for S (the score has no fitted part), on inner walk-forward out-of-sample scores for T and L.

Calibration slope b by test year (0 means "the training window gives no out-of-sample evidence that the score predicts",
and the model then says 50 % all year):

|   test_year |    S |    T |    L |
|------------:|-----:|-----:|-----:|
|        2006 | 1.45 | 1.03 | 0.59 |
|        2007 | 1.23 | 0.00 | 0.00 |
|        2008 | 1.12 | 0.00 | 0.00 |
|        2009 | 1.06 | 0.00 | 0.00 |
|        2010 | 1.03 | 0.00 | 0.00 |
|        2011 | 0.92 | 0.00 | 0.00 |
|        2012 | 0.82 | 0.00 | 0.00 |
|        2013 | 0.78 | 0.00 | 0.00 |
|        2014 | 0.83 | 0.00 | 0.00 |
|        2015 | 0.89 | 0.15 | 0.07 |
|        2016 | 0.91 | 0.19 | 0.09 |
|        2017 | 0.89 | 0.13 | 0.05 |
|        2018 | 0.88 | 0.20 | 0.81 |
|        2019 | 0.89 | 0.27 | 0.81 |
|        2020 | 0.91 | 0.37 | 0.86 |
|        2021 | 0.98 | 0.45 | 0.88 |
|        2022 | 0.97 | 0.40 | 1.13 |
|        2023 | 1.05 | 0.59 | 1.62 |
|        2024 | 1.04 | 0.54 | 1.47 |
|        2025 | 0.94 | 0.46 | 0.38 |
|        2026 | 0.84 | 0.42 | 1.16 |

T is silent from 2007 to 2014 and barely speaks afterwards; that is the honest calibration at work, not a bug: its
in-sample t-stats do not survive the inner walk-forward. The t-stat weights themselves (largest ten, selected years)
settle on positioning, equity momentum and the 2-year spread change, the same things the daily arm found (blank =
the predictor does not yet have 156 weekly training rows):

| test_year   | cot_z156   | cot_z52   | seas   | eqrel63   | rd2_d63   | slope3m_diff   | rd2_d126   | pol_lvl   | carry   | ppp_dev   |
|:------------|:-----------|:----------|:-------|:----------|:----------|:---------------|:-----------|:----------|:--------|:----------|
| 2006        | 0.11       | 0.05      | 0.07   |           |           | 0.14           |            | 0.14      | 0.14    | 0.03      |
| 2008        | 0.07       | 0.03      | 0.06   | 0.0       | 0.07      | 0.11           |            | 0.1       | 0.1     | 0.0       |
| 2010        | 0.14       | 0.08      | 0.07   | 0.01      | 0.05      | 0.08           | 0.05       | 0.08      | 0.07    | 0.03      |
| 2013        | 0.14       | 0.11      | 0.09   | 0.07      | 0.08      | 0.08           | 0.06       | 0.04      | 0.05    | 0.07      |
| 2016        | 0.13       | 0.11      | 0.06   | 0.1       | 0.07      | 0.04           | 0.06       | 0.04      | 0.04    | 0.05      |
| 2019        | 0.14       | 0.12      | 0.07   | 0.09      | 0.06      | 0.05           | 0.06       | 0.04      | 0.04    | 0.06      |
| 2022        | 0.14       | 0.14      | 0.06   | 0.09      | 0.06      | 0.05           | 0.07       | 0.04      | 0.04    | 0.07      |
| 2026        | 0.14       | 0.14      | 0.06   | 0.12      | 0.09      | 0.02           | 0.08       | 0.02      | 0.02    | 0.07      |

### Model comparison: direction accuracy, % (number of decisions acted on)
Month-end clock, non-overlapping (h21 scored on the return to the next month-end; h42 and tb on every other month-end).
Interval = Wilson 95 %.

| model   | target   | P >=   | 2006-2026   | 95 % interval 06-26   | independent bets 06-26   | 2010-2026   | 2016-2026   | 2023-2026   |
|:--------|:---------|:-------|:------------|:----------------------|:-------------------------|:------------|:------------|:------------|
| S       | h21      | 0.5    | 54.1 (246)  | 47.8-60.2             | 246                      | 55.6 (198)  | 57.1 (126)  | 50.0 (44)   |
| S       | h21      | 0.55   | 53.9 (89)   | 43.6-63.9             | 89                       | 58.0 (69)   | 56.0 (50)   | 35.7 (14)   |
| S       | h21      | 0.6    | 56.5 (23)   | 36.8-74.4             | 23                       | 52.9 (17)   | 56.2 (16)   | 50.0 (6)    |
| S       | h42      | 0.5    | 54.0 (124)  | 45.3-62.6             | 124                      | 54.0 (100)  | 57.8 (64)   | 40.9 (22)   |
| S       | h42      | 0.55   | 65.5 (29)   | 47.3-80.1             | 29                       | 77.8 (18)   | 75.0 (16)   | 25.0 (4)    |
| S       | h42      | 0.6    | 100.0 (4)   |                       | 4                        | 100.0 (3)   | 100.0 (3)   | 100.0 (1)   |
| S       | tb       | 0.5    | 51.6 (124)  | 42.9-60.2             | 124                      | 51.0 (100)  | 56.2 (64)   | 45.5 (22)   |
| S       | tb       | 0.55   | 56.2 (32)   | 39.3-71.8             | 32                       | 66.7 (21)   | 68.4 (19)   | 25.0 (4)    |
| S       | tb       | 0.6    | 100.0 (4)   |                       | 4                        | 100.0 (3)   | 100.0 (3)   | 100.0 (1)   |
| T       | h21      | 0.5    | 56.2 (153)  | 48.3-63.8             | 153                      | 56.7 (141)  | 56.6 (129)  | 53.3 (45)   |
| T       | h21      | 0.55   | 41.7 (12)   | 19.3-68.0             | 12                       | 60.0 (5)    | 60.0 (5)    | 60.0 (5)    |
| T       | h21      | 0.6    | 0.0 (1)     |                       | 1                        | - (0)       | - (0)       | - (0)       |
| T       | h42      | 0.5    | 61.5 (52)   | 48.0-73.5             | 52                       | 65.0 (40)   | 65.0 (40)   | 54.5 (22)   |
| T       | h42      | 0.55   | 66.7 (6)    | 30.0-90.3             | 6                        | - (0)       | - (0)       | - (0)       |
| T       | h42      | 0.6    | 60.0 (5)    | 23.1-88.2             | 5                        | - (0)       | - (0)       | - (0)       |
| T       | tb       | 0.5    | 50.0 (46)   | 36.1-63.9             | 46                       | 50.0 (34)   | 50.0 (34)   | 45.5 (22)   |
| T       | tb       | 0.55   | 50.0 (6)    | 18.8-81.2             | 6                        | - (0)       | - (0)       | - (0)       |
| T       | tb       | 0.6    | 40.0 (5)    | 11.8-76.9             | 5                        | - (0)       | - (0)       | - (0)       |
| L       | h21      | 0.5    | 54.2 (153)  | 46.3-61.9             | 153                      | 54.6 (141)  | 53.5 (129)  | 42.2 (45)   |
| L       | h21      | 0.55   | 60.0 (35)   | 43.6-74.4             | 35                       | 65.2 (23)   | 65.2 (23)   | 53.3 (15)   |
| L       | h21      | 0.6    | 50.0 (16)   | 28.0-72.0             | 16                       | 50.0 (6)    | 50.0 (6)    | 40.0 (5)    |
| L       | h42      | 0.5    | 46.9 (64)   | 35.2-58.9             | 64                       | 50.0 (52)   | 47.8 (46)   | 50.0 (22)   |
| L       | h42      | 0.55   | 60.0 (15)   | 35.7-80.2             | 15                       | 55.6 (9)    | 55.6 (9)    | 50.0 (8)    |
| L       | h42      | 0.6    | 66.7 (6)    | 30.0-90.3             | 6                        | - (0)       | - (0)       | - (0)       |
| L       | tb       | 0.5    | 51.3 (76)   | 40.3-62.2             | 76                       | 54.7 (64)   | 51.7 (58)   | 50.0 (22)   |
| L       | tb       | 0.55   | 54.2 (24)   | 35.1-72.1             | 24                       | 55.6 (18)   | 55.6 (18)   | 50.0 (16)   |
| L       | tb       | 0.6    | 62.5 (8)    | 30.6-86.3             | 8                        | 100.0 (2)   | 100.0 (2)   | 100.0 (2)   |

Weekly clock, overlapping horizons. Interval = circular block bootstrap (blocks of 9 weeks for 21 sessions, 17 weeks for
42); "independent bets" = number of acted decisions whose horizon windows do not overlap.

| model   | target   | P >=   | 2006-2026   | 95 % interval 06-26   | independent bets 06-26   | 2010-2026   | 2016-2026   | 2023-2026   |
|:--------|:---------|:-------|:------------|:----------------------|:-------------------------|:------------|:------------|:------------|
| S       | h21      | 0.5    | 53.7 (1073) | 49.2-58.3             | 217                      | 55.1 (865)  | 55.5 (553)  | 47.9 (192)  |
| S       | h21      | 0.55   | 49.2 (372)  | 41.5-57.4             | 113                      | 51.7 (286)  | 53.5 (213)  | 39.1 (69)   |
| S       | h21      | 0.6    | 60.7 (89)   | 44.7-75.5             | 31                       | 68.5 (54)   | 78.3 (46)   | 75.0 (16)   |
| S       | h42      | 0.5    | 50.3 (1068) | 43.9-56.6             | 120                      | 52.9 (862)  | 52.7 (552)  | 39.4 (188)  |
| S       | h42      | 0.55   | 52.8 (235)  | 39.8-64.1             | 45                       | 57.9 (164)  | 60.7 (150)  | 33.9 (62)   |
| S       | h42      | 0.6    | 62.8 (43)   | 38.5-88.0             | 10                       | 79.2 (24)   | 79.2 (24)   | 54.5 (11)   |
| S       | tb       | 0.5    | 51.2 (1068) | 44.9-57.4             | 120                      | 53.8 (862)  | 54.0 (552)  | 43.1 (188)  |
| S       | tb       | 0.55   | 53.2 (267)  | 40.8-63.7             | 50                       | 57.9 (190)  | 59.9 (172)  | 30.9 (68)   |
| S       | tb       | 0.6    | 57.1 (49)   | 34.5-78.8             | 12                       | 67.9 (28)   | 67.9 (28)   | 42.9 (14)   |
| T       | h21      | 0.5    | 52.3 (665)  | 46.7-58.1             | 134                      | 52.9 (613)  | 53.2 (560)  | 47.7 (195)  |
| T       | h21      | 0.55   | 42.6 (54)   | 20.0-64.0             | 16                       | 53.8 (26)   | 53.8 (26)   | 52.0 (25)   |
| T       | h21      | 0.6    | 28.6 (7)    | 0.0-100.0             | 2                        | - (0)       | - (0)       | - (0)       |
| T       | h42      | 0.5    | 50.6 (453)  | 41.5-59.4             | 51                       | 55.9 (349)  | 55.9 (349)  | 44.8 (192)  |
| T       | h42      | 0.55   | 37.7 (53)   | 24.5-57.1             | 7                        | 0.0 (1)     | 0.0 (1)     | 0.0 (1)     |
| T       | h42      | 0.6    | 34.8 (46)   | 5.0-60.0              | 6                        | - (0)       | - (0)       | - (0)       |
| T       | tb       | 0.5    | 47.2 (400)  | 36.9-57.9             | 45                       | 51.0 (296)  | 51.0 (296)  | 44.8 (192)  |
| T       | tb       | 0.55   | 38.5 (52)   | 26.5-60.0             | 6                        | - (0)       | - (0)       | - (0)       |
| T       | tb       | 0.6    | 34.8 (46)   | 5.0-60.0              | 6                        | - (0)       | - (0)       | - (0)       |
| L       | h21      | 0.5    | 53.1 (665)  | 47.6-58.5             | 134                      | 53.7 (613)  | 53.4 (560)  | 45.1 (195)  |
| L       | h21      | 0.55   | 54.1 (157)  | 41.8-66.1             | 39                       | 58.1 (105)  | 58.1 (105)  | 49.3 (73)   |
| L       | h21      | 0.6    | 47.8 (69)   | 28.6-65.5             | 16                       | 52.4 (21)   | 52.4 (21)   | 50.0 (20)   |
| L       | h42      | 0.5    | 46.0 (557)  | 37.2-55.1             | 63                       | 50.3 (453)  | 50.5 (400)  | 49.5 (192)  |
| L       | h42      | 0.55   | 44.3 (122)  | 32.5-59.2             | 17                       | 48.6 (70)   | 48.6 (70)   | 46.2 (65)   |
| L       | h42      | 0.6    | 35.6 (59)   | 20.0-51.4             | 8                        | 14.3 (7)    | 14.3 (7)    | 14.3 (7)    |
| L       | tb       | 0.5    | 48.2 (662)  | 40.9-55.4             | 75                       | 51.4 (558)  | 51.7 (505)  | 46.4 (192)  |
| L       | tb       | 0.55   | 47.6 (185)  | 37.1-58.3             | 25                       | 51.1 (133)  | 51.1 (133)  | 46.2 (119)  |
| L       | tb       | 0.6    | 38.0 (79)   | 25.0-52.5             | 11                       | 37.0 (27)   | 37.0 (27)   | 38.5 (26)   |

* At "always act" every model is at 52-56 % on the 21-session target, with intervals that contain 50 %.
* Raising the threshold does not raise accuracy in any stable way. The one eye-catching cell, S weekly at P >= 0.60
  (60.7 % on 89 weekly decisions, 78.3 % in 2016-26), is 31 independent bets, block-bootstrap interval 44.7-75.5,
  and the same threshold was 41.9 % in 2006-2015; the two bands just below it (0.55-0.60) realised 44-47 %.
* The 42-session and barrier targets are not reliably easier than the 21-session one (the 61.5 % of T on h42 is 52
  month-ends, interval 48-74, and its weekly twin is at 51 %).
* Brier score 2006-2026 (0.2500 = always 50 %):

| forecaster   | target   |      M |      W |
|:-------------|:---------|-------:|-------:|
| S            | h21      | 0.2503 | 0.2505 |
| S            | h42      | 0.2450 | 0.2507 |
| S            | tb       | 0.2486 | 0.2504 |
| T            | h21      | 0.2501 | 0.2503 |
| T            | h42      | 0.2493 | 0.2537 |
| T            | tb       | 0.2525 | 0.2539 |
| L            | h21      | 0.2519 | 0.2529 |
| L            | h42      | 0.2503 | 0.2574 |
| L            | tb       | 0.2539 | 0.2612 |

### Probability calibration (scorecard, 21 sessions)
| clock   | era       | bin            | n   | n_independent   | predicted %   | realised %   | lo   | hi (Wilson, treats rows as independent)   |
|:--------|:----------|:---------------|:----|:----------------|:--------------|:-------------|:-----|:------------------------------------------|
| M       | 2006-2026 | [0.500, 0.525) | 86  | 86              | 51.3          | 57.0         | 46.4 | 66.9                                      |
| M       | 2006-2026 | [0.525, 0.550) | 74  | 74              | 53.7          | 51.3         | 40.2 | 62.4                                      |
| M       | 2006-2026 | [0.550, 0.575) | 40  | 40              | 56.1          | 60.0         | 44.6 | 73.7                                      |
| M       | 2006-2026 | [0.575, 0.600) | 26  | 26              | 58.7          | 42.3         | 25.5 | 61.1                                      |
| M       | 2006-2026 | [0.600, 0.650) | 21  | 21              | 61.6          | 52.4         | 32.4 | 71.7                                      |
| M       | 2006-2026 | [0.650, 0.700) | 2   | 2               | 67.1          | 100.0        | 34.2 | 100.0                                     |
| M       | 2016-2026 | [0.500, 0.525) | 45  | 45              | 51.4          | 55.6         | 41.2 | 69.1                                      |
| M       | 2016-2026 | [0.525, 0.550) | 34  | 34              | 53.8          | 61.8         | 45.0 | 76.1                                      |
| M       | 2016-2026 | [0.550, 0.575) | 19  | 19              | 56.3          | 63.2         | 41.0 | 80.8                                      |
| M       | 2016-2026 | [0.575, 0.600) | 15  | 15              | 58.6          | 46.7         | 24.8 | 69.9                                      |
| M       | 2016-2026 | [0.600, 0.650) | 16  | 16              | 61.3          | 56.2         | 33.2 | 76.9                                      |
| W       | 2006-2026 | [0.500, 0.525) | 385 | 92              | 51.3          | 55.8         | 50.8 | 60.7                                      |
| W       | 2006-2026 | [0.525, 0.550) | 325 | 77              | 53.7          | 56.9         | 51.5 | 62.2                                      |
| W       | 2006-2026 | [0.550, 0.575) | 170 | 40              | 56.1          | 46.5         | 39.1 | 54.0                                      |
| W       | 2006-2026 | [0.575, 0.600) | 113 | 27              | 58.7          | 44.2         | 35.4 | 53.4                                      |
| W       | 2006-2026 | [0.600, 0.650) | 77  | 18              | 61.7          | 58.4         | 47.3 | 68.8                                      |
| W       | 2006-2026 | [0.650, 0.700) | 12  | 3               | 66.5          | 75.0         | 46.8 | 91.1                                      |
| W       | 2016-2026 | [0.500, 0.525) | 200 | 48              | 51.3          | 57.0         | 50.1 | 63.7                                      |
| W       | 2016-2026 | [0.525, 0.550) | 147 | 35              | 53.7          | 57.1         | 49.1 | 64.9                                      |
| W       | 2016-2026 | [0.550, 0.575) | 84  | 20              | 56.2          | 51.2         | 40.7 | 61.6                                      |
| W       | 2016-2026 | [0.575, 0.600) | 83  | 20              | 58.7          | 42.2         | 32.1 | 52.9                                      |
| W       | 2016-2026 | [0.600, 0.650) | 46  | 11              | 61.6          | 78.3         | 64.4 | 87.7                                      |

A calibrated forecaster would show realised rising with predicted. It does not: the 57.5-60 % band realised 42-44 %
and the 50-52.5 % band 56-57 %. The stated probabilities are not usable for sizing or for a "P >= 60 %" trigger.

## 4. The trade as a position trader would run it
Entry at the decision close when flat and max(P, 1-P) >= threshold; initial stop 3 x weekly ATR, checked on session
highs and lows, gap filled at the open; time exit at the next month-end close (M) or four weekly closes later (W); a
trade that ends on time may be renewed on the same close. Costs: 1.2 pips per round trip, plus overnight carry on every
night held = (EUR overnight rate (EONIA, then the euro short-term rate) - Fed funds target midpoint) x days / 360 x
side. R = net pips / (3 x weekly ATR at entry). The daily stream charges the harness cost (1.2 pips per unit of
turnover, i.e. 2.4 a round trip) plus the same carry, and reconciles with the trade list to the basis point.

### The 12 candidates on the selection window 2006-2015
| candidate   | trades   | per yr   | direction right at horizon %   | Wilson 95 %   | expectancy pips   | Sharpe monthly P&L   | eligible (>= 8/yr and exp > 0)   | fallback (>= 4/yr and exp > 0)   |
|:------------|:---------|:---------|:-------------------------------|:--------------|:------------------|:---------------------|:---------------------------------|:---------------------------------|
| S_M_p55     | 39       | 3.9      | 51.3                           | 36.2-66.1     | -71.0             | -0.25                | no                               | no                               |
| S_M_p60     | 7        | 0.7      | 57.1                           | 25.0-84.2     | 176.4             | 0.3                  | no                               | no                               |
| S_W_p55     | 62       | 6.2      | 46.8                           | 34.9-59.0     | -27.1             | -0.15                | no                               | no                               |
| S_W_p60     | 17       | 1.7      | 41.2                           | 21.6-64.0     | -40.2             | -0.13                | no                               | no                               |
| T_M_p55     | 7        | 0.7      | 28.6                           | 8.2-64.1      | -143.1            | -0.44                | no                               | no                               |
| T_M_p60     | 1        | 0.1      | 0.0                            | 0.0-79.3      | -174.4            | -0.43                | no                               | no                               |
| T_W_p55     | 9        | 0.9      | 33.3                           | 12.1-64.6     | -63.4             | -0.3                 | no                               | no                               |
| T_W_p60     | 3        | 0.3      | 66.7                           | 20.8-93.9     | 1.8               | 0.01                 | no                               | no                               |
| L_M_p55     | 12       | 1.2      | 50.0                           | 25.4-74.6     | -51.7             | -0.23                | no                               | no                               |
| L_M_p60     | 10       | 1.0      | 50.0                           | 23.7-76.3     | -37.5             | -0.17                | no                               | no                               |
| L_W_p55     | 13       | 1.3      | 38.5                           | 17.7-64.5     | -46.4             | -0.22                | no                               | no                               |
| L_W_p60     | 14       | 1.4      | 50.0                           | 26.8-73.2     | -42.1             | -0.22                | no                               | no                               |

**Selection: no candidate is eligible, under the rule or under the fallback.** By the pre-declared last resort the best
lower Wilson bound, `S_M_p55`, is flagged `final`. It lost money on the selection window.

All candidates, all eras: direction right % / expectancy pips / monthly-P&L Sharpe (trades):

| candidate   | 2006-2026                | 2006-2015               | 2010-2026                | 2016-2026                | 2023-2026               |
|:------------|:-------------------------|:------------------------|:-------------------------|:-------------------------|:------------------------|
| S_M_p55     | 53.9 / -7 / +0.01 (89)   | 51.3 / -71 / -0.25 (39) | 58.0 / +34 / +0.28 (69)  | 56.0 / +43 / +0.44 (50)  | 35.7 / -39 / -0.37 (14) |
| S_M_p60     | 56.5 / +127 / +0.44 (23) | 57.1 / +176 / +0.30 (7) | 52.9 / +94 / +0.49 (17)  | 56.2 / +105 / +0.65 (16) | 50.0 / +28 / +0.23 (6)  |
| S_W_p55     | 51.1 / +5 / +0.07 (131)  | 46.8 / -27 / -0.15 (62) | 55.0 / +40 / +0.38 (100) | 55.1 / +35 / +0.45 (69)  | 45.8 / -15 / -0.21 (24) |
| S_W_p60     | 52.8 / +17 / +0.10 (36)  | 41.2 / -40 / -0.13 (17) | 52.2 / +30 / +0.19 (23)  | 63.2 / +69 / +0.42 (19)  | 50.0 / -28 / -0.31 (8)  |
| T_M_p55     | 41.7 / -55 / -0.14 (12)  | 28.6 / -143 / -0.44 (7) | 60.0 / +67 / +0.16 (5)   | 60.0 / +67 / +0.19 (5)   | 60.0 / +67 / +0.32 (5)  |
| T_M_p60     | 0.0 / -174 / -0.29 (1)   | 0.0 / -174 / -0.43 (1)  | - (0)                    | - (0)                    | - (0)                   |
| T_W_p55     | 42.1 / -26 / -0.09 (19)  | 33.3 / -63 / -0.30 (9)  | 50.0 / +8 / +0.03 (10)   | 50.0 / +8 / +0.04 (10)   | 44.4 / -24 / -0.15 (9)  |
| T_W_p60     | 66.7 / +2 / +0.01 (3)    | 66.7 / +2 / +0.01 (3)   | - (0)                    | - (0)                    | - (0)                   |
| L_M_p55     | 60.0 / +29 / +0.17 (35)  | 50.0 / -52 / -0.23 (12) | 65.2 / +71 / +0.34 (23)  | 65.2 / +71 / +0.43 (23)  | 53.3 / +21 / +0.26 (15) |
| L_M_p60     | 50.0 / -41 / -0.15 (16)  | 50.0 / -38 / -0.17 (10) | 50.0 / -48 / -0.11 (6)   | 50.0 / -48 / -0.14 (6)   | 40.0 / -84 / -0.20 (5)  |
| L_W_p55     | 50.0 / +19 / +0.14 (46)  | 38.5 / -46 / -0.22 (13) | 54.5 / +44 / +0.28 (33)  | 54.5 / +44 / +0.35 (33)  | 45.5 / -10 / -0.01 (22) |
| L_W_p60     | 50.0 / -36 / -0.15 (20)  | 50.0 / -42 / -0.22 (14) | 50.0 / -20 / -0.05 (6)   | 50.0 / -20 / -0.07 (6)   | 40.0 / -52 / -0.07 (5)  |

Harness Sharpe of the 12 daily streams (net, 1.2 pips per unit turnover plus carry, 252 periods):

| variant   |   2006-2026 |   2006-2015 |   2010-2026 |   2016-2026 |   2023-2026 |
|:----------|------------:|------------:|------------:|------------:|------------:|
| S_M_p55   |        0.02 |       -0.28 |        0.28 |        0.40 |       -0.37 |
| S_M_p60   |        0.44 |        0.32 |        0.40 |        0.57 |        0.19 |
| S_W_p55   |        0.07 |       -0.16 |        0.36 |        0.39 |       -0.21 |
| S_W_p60   |        0.09 |       -0.11 |        0.16 |        0.39 |       -0.28 |
| T_M_p55   |       -0.12 |       -0.40 |        0.14 |        0.18 |        0.30 |
| T_M_p60   |       -0.12 |       -0.18 |        0.00 |        0.00 |        0.00 |
| T_W_p55   |       -0.08 |       -0.21 |        0.03 |        0.04 |       -0.16 |
| T_W_p60   |        0.00 |        0.00 |        0.00 |        0.00 |        0.00 |
| L_M_p55   |        0.17 |       -0.21 |        0.36 |        0.45 |        0.27 |
| L_M_p60   |       -0.14 |       -0.14 |       -0.12 |       -0.15 |       -0.21 |
| L_W_p55   |        0.14 |       -0.19 |        0.28 |        0.35 |       -0.01 |
| L_W_p60   |       -0.14 |       -0.19 |       -0.05 |       -0.06 |       -0.07 |

The only candidate that is positive in each of the five reporting windows is `S_M_p60`, the owner's threshold on the scorecard: 23 trades in
21 years (2 long), harness Sharpe 0.44 / 0.40 / 0.57 / 0.19 for 2006-26 / 2010-26 / 2016-26 / 2023-26, deflated-Sharpe p
0.49 with 12 candidates. It traded 0.7 times a year on the selection window, so it is not eligible, its direction
accuracy is 56.5 % (Wilson 36.8-74.4), and it is the same short-EUR-with-carry exposure as the rule below.

### The flagged rule `S_M_p55` (scorecard, month-end, P >= 0.55, stop 3 x ATR)
| era       | trades   | per yr   | long %   | closed in profit %   | direction right at horizon %   | Wilson 95 %   | avg win pips   | avg loss pips   | expectancy pips   | of which carry   | expectancy R   | hold sessions   | stopped %   | max DD (R)   | Sharpe monthly P&L   |
|:----------|:---------|:---------|:---------|:---------------------|:-------------------------------|:--------------|:---------------|:----------------|:------------------|:-----------------|:---------------|:----------------|:------------|:-------------|:---------------------|
| 2006-2026 | 89       | 4.3      | 24.7     | 59.6                 | 53.9                           | 43.6-63.9     | 211.0          | -328.0          | -7.0              | 13.3             | 0.015          | 21.2            | 6.7         | 5.8          | 0.01                 |
| 2006-2015 | 39       | 3.9      | 51.3     | 51.3                 | 51.3                           | 36.2-66.1     | 281.0          | -442.0          | -71.0             | 10.4             | -0.057         | 21.6            | 5.1         | 5.8          | -0.25                |
| 2010-2026 | 69       | 4.1      | 18.8     | 65.2                 | 58.0                           | 46.2-68.9     | 201.0          | -278.0          | 34.2              | 12.3             | 0.073          | 21.2            | 5.8         | 3.0          | 0.28                 |
| 2016-2026 | 50       | 4.6      | 4.0      | 66.0                 | 56.0                           | 42.3-68.8     | 169.0          | -201.0          | 42.9              | 15.6             | 0.072          | 21.0            | 8.0         | 3.0          | 0.44                 |
| 2023-2026 | 14       | 3.6      | 14.3     | 50.0                 | 35.7                           | 16.3-61.2     | 134.0          | -212.0          | -39.0             | 9.2              | -0.088         | 20.6            | 14.3        | 3.0          | -0.37                |

Per year, harness table (deflated-Sharpe p for 2010-2026 with 12 candidates = 0.69):

| period    |    n |   sharpe |      t |   mean_bp |    sum_bp |   active_frac |   sharpe_0.6pip |
|:----------|-----:|---------:|-------:|----------:|----------:|--------------:|----------------:|
| 2006      |  258 |   -0.519 | -0.526 |    -1.319 |  -340.379 |         0.674 |          -0.516 |
| 2007      |  259 |   -0.257 | -0.260 |    -0.185 |   -47.863 |         0.170 |          -0.252 |
| 2008      |  260 |   -0.660 | -0.671 |    -3.128 |  -813.235 |         0.546 |          -0.658 |
| 2009      |  259 |   -1.270 | -1.287 |    -3.499 |  -906.363 |         0.255 |          -1.267 |
| 2010      |  260 |   -1.146 | -1.164 |    -2.695 |  -700.577 |         0.258 |          -1.143 |
| 2011      |  260 |   -0.909 | -0.924 |    -2.724 |  -708.276 |         0.500 |          -0.905 |
| 2012      |  260 |    0.921 |  0.936 |     1.466 |   381.038 |         0.265 |           0.928 |
| 2013      |  259 |    0.907 |  0.920 |     0.469 |   121.343 |         0.081 |           0.915 |
| 2014      |  258 |    0.668 |  0.676 |     1.024 |   264.185 |         0.248 |           0.674 |
| 2015      |  259 |    1.643 |  1.666 |     3.710 |   960.988 |         0.247 |           1.647 |
| 2016      |  259 |    1.483 |  1.503 |     1.411 |   365.567 |         0.085 |           1.488 |
| 2017      |  259 |   -0.986 | -1.000 |    -0.178 |   -45.976 |         0.004 |          -0.986 |
| 2018      |  260 |    1.017 |  1.033 |     2.890 |   751.310 |         0.985 |           1.018 |
| 2019      |  260 |    0.533 |  0.542 |     0.859 |   223.318 |         0.669 |           0.538 |
| 2020      |  260 |   -1.123 | -1.140 |    -0.944 |  -245.336 |         0.104 |          -1.116 |
| 2021      |  259 |    0.341 |  0.346 |     0.484 |   125.402 |         0.336 |           0.345 |
| 2022      |  260 |    1.545 |  1.569 |     5.087 |  1322.714 |         0.738 |           1.547 |
| 2023      |  258 |   -0.017 | -0.017 |    -0.032 |    -8.208 |         0.326 |          -0.012 |
| 2024      |  261 |   -0.862 | -0.877 |    -0.614 |  -160.231 |         0.180 |          -0.846 |
| 2025      |  260 |   -1.544 | -1.568 |    -2.281 |  -593.102 |         0.185 |          -1.543 |
| 2026      |  221 |    0.775 |  0.725 |     1.065 |   235.455 |         0.498 |           0.781 |
| 2010-2026 | 4373 |    0.283 |  1.178 |     0.524 |  2289.615 |         0.335 |           0.287 |
| 2016-2026 | 2817 |    0.401 |  1.341 |     0.700 |  1970.914 |         0.372 |           0.405 |
| 2023-2026 | 1000 |   -0.371 | -0.738 |    -0.526 |  -526.086 |         0.289 |          -0.365 |
| 2010-2015 | 1556 |    0.101 |  0.250 |     0.205 |   318.701 |         0.267 |           0.105 |
| 2016-2022 | 1817 |    0.724 |  1.944 |     1.374 |  2497.000 |         0.418 |           0.727 |
| 2006-2026 | 5409 |    0.016 |  0.073 |     0.034 |   181.776 |         0.349 |           0.019 |
| 2006-2015 | 2592 |   -0.278 | -0.890 |    -0.690 | -1789.138 |         0.324 |          -0.274 |

Round-4 hit rates of the flagged rule:

| era       | decisions (trades)   | net P&L > 0 %   | correct sign before costs %   | active sessions   | sessions net > 0 %   | sessions sign correct %   |
|:----------|:---------------------|:----------------|:------------------------------|:------------------|:---------------------|:--------------------------|
| 2010-2026 | 69                   | 65.2            | 58.0                          | 1463              | 52.3                 | 51.5                      |
| 2016-2026 | 50                   | 66.0            | 56.0                          | 1048              | 51.0                 | 50.2                      |
| 2023-2026 | 14                   | 50.0            | 35.7                          | 289               | 51.2                 | 49.8                      |

What this record is: 4 % of the 2016-2026 trades are long, i.e. the scorecard at P >= 0.55 is a short-EUR position
that collects the dollar's rate advantage (16 of the 43 pips a trade are carry) and happened to be on the right
side of 2018-2022. It lost every year from 2006 to 2011 and again in 2024-2025. That is one macro regime, not timing skill.

### Sensitivities of the flagged rule (reported, never selectable)
| sensitivity                                                             | era       | trades   | per yr   | closed in profit %   | direction right at horizon %   | Wilson 95 %   | avg win pips   | avg loss pips   | expectancy pips   | expectancy R   | hold sessions   | stopped %   | max DD (R)   | Sharpe monthly P&L   |
|:------------------------------------------------------------------------|:----------|:---------|:---------|:---------------------|:-------------------------------|:--------------|:---------------|:----------------|:------------------|:---------------|:----------------|:------------|:-------------|:---------------------|
| P > 0.50 (always act, 12 a year)                                        | 2006-2026 | 246      | 11.8     | 56.5                 | 54.1                           | 47.8-60.2     | 236.0          | -254.0          | 22.6              | 0.046          | 21.4            | 3.7         | 4.4          | 0.28                 |
| P > 0.50 (always act, 12 a year)                                        | 2016-2026 | 126      | 11.6     | 61.9                 | 57.1                           | 48.4-65.4     | 178.0          | -205.0          | 32.2              | 0.068          | 21.2            | 4.8         | 4.4          | 0.48                 |
| P > 0.50 (always act, 12 a year)                                        | 2023-2026 | 44       | 11.4     | 56.8                 | 50.0                           | 35.8-64.2     | 158.0          | -243.0          | -15.0             | -0.005         | 20.8            | 9.1         | 4.4          | -0.14                |
| P >= 0.55 (= the flagged rule)                                          | 2006-2026 | 89       | 4.3      | 59.6                 | 53.9                           | 43.6-63.9     | 211.0          | -328.0          | -7.0              | 0.015          | 21.2            | 6.7         | 5.8          | 0.01                 |
| P >= 0.55 (= the flagged rule)                                          | 2016-2026 | 50       | 4.6      | 66.0                 | 56.0                           | 42.3-68.8     | 169.0          | -201.0          | 42.9              | 0.072          | 21.0            | 8.0         | 3.0          | 0.44                 |
| P >= 0.55 (= the flagged rule)                                          | 2023-2026 | 14       | 3.6      | 50.0                 | 35.7                           | 16.3-61.2     | 134.0          | -212.0          | -39.0             | -0.088         | 20.6            | 14.3        | 3.0          | -0.37                |
| P >= 0.60 (the owner's threshold)                                       | 2006-2026 | 23       | 1.1      | 69.6                 | 56.5                           | 36.8-74.4     | 242.0          | -136.0          | 127.1             | 0.157          | 22.0            | 0.0         | 0.7          | 0.44                 |
| P >= 0.60 (the owner's threshold)                                       | 2016-2026 | 16       | 1.5      | 75.0                 | 56.2                           | 33.2-76.9     | 185.0          | -134.0          | 105.5             | 0.187          | 22.1            | 0.0         | 0.7          | 0.65                 |
| P >= 0.60 (the owner's threshold)                                       | 2023-2026 | 6        | 1.6      | 50.0                 | 50.0                           | 18.8-81.2     | 174.0          | -119.0          | 27.7              | 0.049          | 22.3            | 0.0         | 0.7          | 0.23                 |
| P >= 0.65                                                               | 2006-2026 | 2        | 0.1      | 100.0                | 100.0                          | 34.2-100.0    | 50.0           | 0.0             | 49.9              | 0.068          | 21.5            | 0.0         | 0.0          | 0.11                 |
| P >= 0.65                                                               | 2016-2026 | 0        | 0.0      |                      |                                |               |                |                 |                   |                |                 |             |              | 0.0                  |
| P >= 0.65                                                               | 2023-2026 | 0        | 0.0      |                      |                                |               |                |                 |                   |                |                 |             |              | 0.0                  |
| P >= 0.70                                                               | 2006-2026 | 0        | 0.0      |                      |                                |               |                |                 |                   |                |                 |             |              | 0.0                  |
| P >= 0.70                                                               | 2016-2026 | 0        | 0.0      |                      |                                |               |                |                 |                   |                |                 |             |              | 0.0                  |
| P >= 0.70                                                               | 2023-2026 | 0        | 0.0      |                      |                                |               |                |                 |                   |                |                 |             |              | 0.0                  |
| stop 2 x weekly ATR                                                     | 2006-2026 | 89       | 4.3      | 59.6                 | 53.9                           | 43.6-63.9     | 211.0          | -291.0          | 8.1               | 0.059          | 20.1            | 15.7        | 7.1          | 0.11                 |
| stop 2 x weekly ATR                                                     | 2016-2026 | 50       | 4.6      | 66.0                 | 56.0                           | 42.3-68.8     | 169.0          | -170.0          | 53.6              | 0.141          | 20.4            | 12.0        | 3.5          | 0.59                 |
| stop 2 x weekly ATR                                                     | 2023-2026 | 14       | 3.6      | 50.0                 | 35.7                           | 16.3-61.2     | 134.0          | -167.0          | -16.5             | -0.063         | 19.6            | 14.3        | 3.5          | -0.21                |
| trailing stop 3 x ATR                                                   | 2006-2026 | 89       | 4.3      | 59.6                 | 53.9                           | 43.6-63.9     | 211.0          | -323.0          | -4.9              | 0.018          | 21.1            | 9.0         | 5.7          | 0.03                 |
| trailing stop 3 x ATR                                                   | 2016-2026 | 50       | 4.6      | 66.0                 | 56.0                           | 42.3-68.8     | 169.0          | -197.0          | 44.2              | 0.075          | 21.0            | 8.0         | 3.0          | 0.45                 |
| trailing stop 3 x ATR                                                   | 2023-2026 | 14       | 3.6      | 50.0                 | 35.7                           | 16.3-61.2     | 134.0          | -211.0          | -39.0             | -0.088         | 20.6            | 14.3        | 3.0          | -0.37                |
| no stop                                                                 | 2006-2026 | 89       | 4.3      | 60.7                 | 53.9                           | 43.6-63.9     | 207.0          | -322.0          | -1.0              | 0.002          | 21.7            | 0.0         | 0.4          | 0.06                 |
| no stop                                                                 | 2016-2026 | 50       | 4.6      | 68.0                 | 56.0                           | 42.3-68.8     | 164.0          | -170.0          | 57.1              | 0.006          | 21.7            | 0.0         | 0.1          | 0.62                 |
| no stop                                                                 | 2023-2026 | 14       | 3.6      | 50.0                 | 35.7                           | 16.3-61.2     | 134.0          | -178.0          | -22.2             | -0.003         | 21.8            | 0.0         | 0.1          | -0.26                |
| symmetric 2-ATR barrier (target and stop), 2-month limit, tb forecaster | 2006-2026 | 42       | 2.0      | 54.8                 | 54.8                           | 39.9-68.8     | 287.0          | -376.0          | -13.0             | 0.023          | 32.2            | 28.6        | 5.0          | -0.0                 |
| symmetric 2-ATR barrier (target and stop), 2-month limit, tb forecaster | 2016-2026 | 27       | 2.5      | 63.0                 | 66.7                           | 47.8-81.4     | 249.0          | -241.0          | 67.2              | 0.18           | 31.4            | 25.9        | 4.2          | 0.37                 |
| symmetric 2-ATR barrier (target and stop), 2-month limit, tb forecaster | 2023-2026 | 9        | 2.3      | 33.3                 | 22.2                           | 6.3-54.7      | 163.0          | -230.0          | -99.0             | -0.309         | 30.7            | 44.4        | 4.2          | -0.6                 |
| 42-session forecaster, exit after 2 months                              | 2006-2026 | 39       | 1.9      | 61.5                 | 61.5                           | 45.9-75.1     | 298.0          | -456.0          | 8.0               | 0.037          | 39.5            | 17.9        | 3.0          | 0.06                 |
| 42-session forecaster, exit after 2 months                              | 2016-2026 | 26       | 2.4      | 65.4                 | 65.4                           | 46.2-80.6     | 251.0          | -273.0          | 69.6              | 0.129          | 40.3            | 11.5        | 3.0          | 0.35                 |
| 42-session forecaster, exit after 2 months                              | 2023-2026 | 9        | 2.3      | 33.3                 | 22.2                           | 6.3-54.7      | 188.0          | -237.0          | -95.3             | -0.21          | 38.7            | 22.2        | 3.0          | -0.52                |
| 0.6 pips per round trip                                                 | 2006-2026 | 89       | 4.3      | 59.6                 | 53.9                           | 43.6-63.9     | 212.0          | -328.0          | -6.4              | 0.016          | 21.2            | 6.7         | 5.7          | 0.02                 |
| 0.6 pips per round trip                                                 | 2016-2026 | 50       | 4.6      | 66.0                 | 56.0                           | 42.3-68.8     | 169.0          | -201.0          | 43.5              | 0.073          | 21.0            | 8.0         | 3.0          | 0.44                 |
| 0.6 pips per round trip                                                 | 2023-2026 | 14       | 3.6      | 50.0                 | 35.7                           | 16.3-61.2     | 134.0          | -211.0          | -38.4             | -0.087         | 20.6            | 14.3        | 3.0          | -0.37                |
| retail swap mark-up 0.75 % p.a. against the holder                      | 2006-2026 | 89       | 4.3      | 57.3                 | 53.9                           | 43.6-63.9     | 212.0          | -318.0          | -14.5             | 0.003          | 21.2            | 6.7         | 6.0          | -0.03                |
| retail swap mark-up 0.75 % p.a. against the holder                      | 2016-2026 | 50       | 4.6      | 62.0                 | 56.0                           | 42.3-68.8     | 172.0          | -186.0          | 36.1              | 0.058          | 21.0            | 8.0         | 3.1          | 0.37                 |
| retail swap mark-up 0.75 % p.a. against the holder                      | 2023-2026 | 14       | 3.6      | 35.7                 | 35.7                           | 16.3-61.2     | 178.0          | -170.0          | -45.7             | -0.102         | 20.6            | 14.3        | 3.1          | -0.43                |
| carry ignored (as all earlier arms did)                                 | 2006-2026 | 89       | 4.3      | 53.9                 | 53.9                           | 43.6-63.9     | 220.0          | -302.0          | -20.3             | -0.008         | 21.2            | 6.7         | 6.2          | -0.07                |
| carry ignored (as all earlier arms did)                                 | 2016-2026 | 50       | 4.6      | 56.0                 | 56.0                           | 42.3-68.8     | 181.0          | -169.0          | 27.4              | 0.04           | 21.0            | 8.0         | 3.2          | 0.29                 |
| carry ignored (as all earlier arms did)                                 | 2023-2026 | 14       | 3.6      | 35.7                 | 35.7                           | 16.3-61.2     | 184.0          | -177.0          | -48.2             | -0.109         | 20.6            | 14.3        | 3.2          | -0.44                |
| entry one session late                                                  | 2006-2026 | 89       | 4.3      | 56.2                 | 55.1                           | 44.7-65.0     | 206.0          | -291.0          | -12.2             | 0.014          | 20.5            | 4.5         | 6.2          | -0.03                |
| entry one session late                                                  | 2016-2026 | 50       | 4.6      | 58.0                 | 56.0                           | 42.3-68.8     | 174.0          | -129.0          | 46.8              | 0.086          | 20.6            | 2.0         | 2.7          | 0.5                  |
| entry one session late                                                  | 2023-2026 | 14       | 3.6      | 35.7                 | 35.7                           | 16.3-61.2     | 129.0          | -155.0          | -53.2             | -0.122         | 20.6            | 7.1         | 2.7          | -0.61                |

* **Carry matters at this horizon**: ignoring it changes the 2006-2026 expectancy from -7 to -20 pips a trade
  (about 13 pips per month-long trade, in favour of dollar longs for most of the sample); a retail swap mark-up of
  0.75 % p.a. takes about 8 pips a trade back. The 1.2-pip spread is irrelevant (+0.6 pips at 0.6).
* Stops: a 3-ATR stop is hit on 7 % of trades and changes nothing; 2 ATR is hit on 16 % and is slightly better
  here, no stop slightly better again in 2016-26: no evidence that the stop adds or costs anything. Trailing: no effect.
* The barrier version and the 42-session version trade about twice a year and look like the base rule; both lose
  2023-26.
* P >= 0.60: 23 trades in 21 years, +127 pips each, Sharpe 0.44; t of the trade mean about 1.9, from 23 trades of which
  16 fall in 2016-26 and all of those are short. I would not read anything into it.

## 5. Benchmark: the live exposure held as a position (not a candidate)
Sign of 0.5 x weak_signals + 0.5 x regime_trend (both walk-forward from 2010) read at the decision close and run through
the same simulator (3-ATR stop, 1.2 pips, carry):

| benchmark            | era       | trades   | per yr   | closed in profit %   | direction right at horizon %   | Wilson 95 %   | expectancy pips   | of which carry   | max DD (R)   | Sharpe monthly P&L   |
|:---------------------|:----------|:---------|:---------|:---------------------|:-------------------------------|:--------------|:------------------|:-----------------|:-------------|:---------------------|
| live_exposure_sign_M | 2010-2026 | 176      | 10.5     | 61.9                 | 59.1                           | 51.7-66.1     | 58.1              | 0.5              | 3.9          | 0.64                 |
| live_exposure_sign_M | 2016-2026 | 109      | 10.1     | 63.3                 | 58.7                           | 49.3-67.5     | 39.3              | 0.7              | 3.9          | 0.58                 |
| live_exposure_sign_M | 2023-2026 | 39       | 10.1     | 53.8                 | 48.7                           | 33.9-63.8     | -25.0             | 0.5              | 3.9          | -0.28                |
| live_exposure_sign_W | 2010-2026 | 202      | 12.0     | 57.9                 | 58.4                           | 51.5-65.0     | 47.5              | 0.1              | 3.3          | 0.6                  |
| live_exposure_sign_W | 2016-2026 | 127      | 11.7     | 59.1                 | 59.8                           | 51.1-68.0     | 48.1              | 0.2              | 2.3          | 0.83                 |
| live_exposure_sign_W | 2023-2026 | 46       | 12.0     | 52.2                 | 50.0                           | 36.1-63.9     | 7.6               | -0.4             | 2.3          | 0.21                 |

This is the best multi-week record in the repository and it is not mine. Two cautions: it was selected by rounds 1-2
out of ~430 variants on exactly this period, so it is flattered in a way the prior-signed scorecard is not; and it is
at 49-50 % with a negative or flat expectancy in 2023-26, like everything else here.

## 6. Which predictors carry it (leave one family out / one family alone; diagnostic)
Direction right % / expectancy pips / monthly Sharpe (trades). "drop X" = the flagged rule without family X; "only X" =
a one-family scorecard that acts whenever its training-window slope is positive.

| run                                                 | 2006-2026                | 2010-2026                | 2016-2026                | 2023-2026               |
|:----------------------------------------------------|:-------------------------|:-------------------------|:-------------------------|:------------------------|
| none (final)                                        | 53.9 / -7 / +0.01 (89)   | 58.0 / +34 / +0.28 (69)  | 56.0 / +43 / +0.44 (50)  | 35.7 / -39 / -0.37 (14) |
| drop RL                                             | 55.7 / +15 / +0.15 (106) | 59.8 / +54 / +0.48 (87)  | 58.5 / +48 / +0.50 (65)  | 45.0 / -35 / -0.29 (20) |
| drop RC                                             | 51.1 / -12 / -0.03 (94)  | 55.9 / +30 / +0.25 (68)  | 53.8 / +30 / +0.32 (52)  | 26.7 / -83 / -0.82 (15) |
| drop VAL                                            | 55.0 / +14 / +0.13 (120) | 56.7 / +34 / +0.31 (90)  | 55.2 / +31 / +0.35 (58)  | 31.2 / -64 / -0.66 (16) |
| drop TR                                             | 49.4 / +8 / +0.09 (79)   | 57.1 / +82 / +0.54 (56)  | 54.5 / +43 / +0.41 (44)  | 30.8 / -66 / -0.64 (13) |
| drop POS                                            | 47.2 / +1 / +0.05 (53)   | 53.1 / +79 / +0.45 (32)  | 53.8 / +72 / +0.50 (26)  | 44.4 / -9 / -0.10 (9)   |
| drop POSX                                           | 54.8 / +5 / +0.09 (104)  | 58.3 / +41 / +0.38 (84)  | 58.1 / +48 / +0.54 (62)  | 45.8 / +0 / +0.00 (24)  |
| drop EQ                                             | 50.0 / -18 / -0.06 (72)  | 52.7 / +12 / +0.11 (55)  | 56.4 / +41 / +0.35 (39)  | 30.8 / -56 / -0.50 (13) |
| drop CURVE                                          | 55.8 / +15 / +0.15 (104) | 59.5 / +58 / +0.50 (84)  | 53.8 / +20 / +0.23 (65)  | 40.9 / -48 / -0.44 (22) |
| drop SEAS                                           | 50.6 / -22 / -0.07 (85)  | 55.4 / +27 / +0.22 (65)  | 55.1 / +40 / +0.38 (49)  | 37.5 / -42 / -0.41 (16) |
| drop OIL                                            | 53.0 / -0 / +0.03 (100)  | 56.5 / +29 / +0.23 (69)  | 54.5 / +33 / +0.31 (44)  | 25.0 / -92 / -0.78 (12) |
| drop CARRY                                          | 57.3 / +16 / +0.16 (103) | 61.7 / +68 / +0.59 (81)  | 58.5 / +49 / +0.51 (65)  | 45.0 / -35 / -0.29 (20) |
| only RL (acts whenever its training slope b > 0)    | 40.5 / -79 / -0.36 (84)  | 33.3 / -140 / -0.53 (36) | - (0)                    | - (0)                   |
| only RC (acts whenever its training slope b > 0)    | 46.7 / -15 / -0.13 (210) | 46.1 / -9 / -0.05 (165)  | 45.9 / -7 / -0.08 (111)  | 50.0 / -1 / +0.07 (40)  |
| only VAL (acts whenever its training slope b > 0)   | - (0)                    | - (0)                    | - (0)                    | - (0)                   |
| only TR (acts whenever its training slope b > 0)    | 54.6 / +3 / +0.03 (240)  | 53.9 / +2 / -0.01 (193)  | 52.8 / -5 / -0.08 (125)  | 45.2 / -54 / -0.73 (42) |
| only POS (acts whenever its training slope b > 0)   | 59.8 / +49 / +0.47 (194) | 59.9 / +52 / +0.61 (157) | 59.2 / +43 / +0.59 (103) | 52.5 / -5 / +0.00 (40)  |
| only POSX (acts whenever its training slope b > 0)  | 25.0 / -84 / -0.07 (8)   | - (0)                    | - (0)                    | - (0)                   |
| only EQ (acts whenever its training slope b > 0)    | 55.8 / +4 / +0.05 (113)  | 56.1 / +20 / +0.19 (98)  | 50.0 / +2 / +0.01 (60)   | 35.7 / -96 / -0.67 (14) |
| only CURVE (acts whenever its training slope b > 0) | 45.4 / -21 / -0.21 (218) | 45.4 / -13 / -0.16 (174) | 49.1 / +8 / +0.12 (108)  | 40.6 / +4 / -0.02 (32)  |
| only SEAS (acts whenever its training slope b > 0)  | 53.8 / +27 / +0.15 (93)  | 56.3 / +36 / +0.26 (71)  | 53.3 / -12 / -0.16 (45)  | 43.8 / -51 / -0.51 (16) |
| only OIL (acts whenever its training slope b > 0)   | 53.1 / +14 / +0.16 (177) | 54.7 / +26 / +0.32 (137) | 58.5 / +40 / +0.49 (94)  | 55.2 / -8 / -0.05 (29)  |
| only CARRY (acts whenever its training slope b > 0) | 49.0 / -7 / -0.05 (249)  | 50.7 / +4 / +0.05 (201)  | 50.4 / +3 / +0.06 (129)  | 44.4 / -2 / -0.08 (45)  |

Positioning alone is the strongest family by a distance (59-60 % and +43 to +52 pips a trade in every window, flat in
2023-26) and removing it costs the scorecard most accuracy; oil alone is positive but weaker; trend alone is at
+3 pips a trade. The scorecard is better without the rate-level and carry families. Valuation never acts (its training
slope is never positive). Since the family signs were not all textbook (POS, EQ and SEAS are house signs), the families that work are
exactly the ones this project had already mined.

## 7. Pre-1999 robustness sample (synthetic DEM euro, 1975-1998, close only; test years 1982-1998)
Same pipeline, same candidates, predictors that exist before 1999 only (no positioning, no equities, no 2-year yields).
Carry = German minus US 3-month interbank. Never used for any choice.

Forecast accuracy (h21):

| forecaster   | clock   | thr   | n_decisions   | n_acted   | acc   | ci_lo   | ci_hi   | naive_majority   | n_independent   |
|:-------------|:--------|:------|:--------------|:----------|:------|:--------|:--------|:-----------------|:----------------|
| S            | M       | 0.5   | 203           | 142       | 48.6  | 40.5    | 56.7    | 54.2             | 142             |
| S            | M       | 0.55  | 203           | 0         |       |         |         | 54.2             | 0               |
| S            | M       | 0.6   | 203           | 0         |       |         |         | 54.2             | 0               |
| S            | W       | 0.5   | 887           | 621       | 51.0  | 45.0    | 57.0    | 50.2             | 126             |
| S            | W       | 0.55  | 887           | 0         |       |         |         | 50.2             | 0               |
| S            | W       | 0.6   | 887           | 0         |       |         |         | 50.2             | 0               |
| T            | M       | 0.5   | 203           | 203       | 55.7  | 48.8    | 62.3    | 54.2             | 203             |
| T            | M       | 0.55  | 203           | 111       | 54.1  | 44.8    | 63.0    | 54.2             | 111             |
| T            | M       | 0.6   | 203           | 15        | 46.7  | 24.8    | 69.9    | 54.2             | 15              |
| T            | W       | 0.5   | 887           | 887       | 57.8  | 52.5    | 62.9    | 50.2             | 178             |
| T            | W       | 0.55  | 887           | 474       | 55.1  | 47.8    | 62.3    | 50.2             | 106             |
| T            | W       | 0.6   | 887           | 67        | 49.3  | 32.0    | 66.7    | 50.2             | 18              |
| L            | M       | 0.5   | 203           | 167       | 46.1  | 38.7    | 53.7    | 54.2             | 167             |
| L            | M       | 0.55  | 203           | 13        | 30.8  | 12.7    | 57.6    | 54.2             | 13              |
| L            | M       | 0.6   | 203           | 0         |       |         |         | 54.2             | 0               |
| L            | W       | 0.5   | 887           | 731       | 49.5  | 43.6    | 55.3    | 50.2             | 147             |
| L            | W       | 0.55  | 887           | 58        | 39.7  | 21.4    | 56.7    | 50.2             | 15              |
| L            | W       | 0.6   | 887           | 0         |       |         |         | 50.2             | 0               |

Trades (candidates with at least one trade):

| candidate   | era       | trades   | per yr   | direction right at horizon %   | Wilson 95 %   | expectancy pips   | Sharpe monthly P&L   |
|:------------|:----------|:---------|:---------|:-------------------------------|:--------------|:------------------|:---------------------|
| T_M_p55     | 1982-1998 | 111      | 6.5      | 54.1                           | 44.8-63.0     | 23.4              | 0.18                 |
| T_M_p60     | 1982-1998 | 15       | 0.9      | 46.7                           | 24.8-69.9     | -117.5            | -0.14                |
| T_W_p55     | 1982-1998 | 131      | 7.7      | 60.3                           | 51.7-68.3     | 39.4              | 0.33                 |
| T_W_p60     | 1982-1998 | 23       | 1.4      | 56.5                           | 36.8-74.4     | -37.7             | -0.09                |
| L_M_p55     | 1982-1998 | 13       | 0.8      | 30.8                           | 12.7-57.6     | -239.3            | -0.34                |
| L_W_p55     | 1982-1998 | 17       | 1.0      | 47.1                           | 26.2-69.0     | -111.9            | -0.24                |

* The prior-signed scorecard is at chance here too (48.6 % at month-ends) and never reaches P >= 0.55.
* The t-stat combination does better in the DEM era (57.8 % weekly, interval 52.5-62.9), consistent with the
  single-predictor table, where trend and the 6-month change of the 10-year (real) differential are at 55-58 % in that
  era; almost all of it is 1982-1989 (`T_W_p55` Sharpe 0.59, then 0.11 in 1990-98).
  It is the well-known trend era of the dollar, and the same model in the euro era is at 52.3 %.
* Month-ends: T is at 55.7 % against a naive majority of 54.2 %, and its P >= 0.60 calls (15 month-ends) were right 46.7 % of
  the time: here too a higher stated probability did not mean a higher hit rate.
* So the older sample does not support any of the textbook predictors as a stable multi-week signal either.

## 8. Incremental test (round-3 addendum)
`meta.combine([...], "EW")` + `report_combo`, daily net P&L, 2010 onward (combination starts 2013):

| | 2010-2026 | 2013-2026 | 2016-2026 | 2023-2026 |
|---|---|---|---|---|
| EW(weak_signals, regime_trend) Sharpe (t) | 0.56 (2.35) | 0.62 (2.35) | 0.64 (2.13) | 0.36 (0.71) |
| EW(weak_signals, regime_trend, swing) | 0.58 (2.42) | 0.64 (2.42) | 0.66 (2.22) | 0.13 (0.26) |

Daily P&L correlation of the swing stream with weak_signals 0.09, with regime_trend 0.28, with their
combination 0.26. Alpha of the swing stream on the two survivors: +0.13 bp a day (t 0.29) 2010-26,
+0.30 (t 0.62) 2016-26, -0.79 (t -1.32) 2023-26. The combiner admits the stream in 11 of the 14 years.
**Round-3 bar: failed.** Standalone 2016-2026 is 0.40 (> 0.3) and the three-way edges the two-way by +0.03 on
2016-26, but 2023-2026 is -0.37, the alpha t-stats are below 1, and the rule was not selectable in the first place.

## 9. Leak checks
| check                                                          | era       | decisions / trades   | direction right %   | expectancy pips   | Sharpe monthly   | sd across seeds (acc / Sharpe)   |
|:---------------------------------------------------------------|:----------|:---------------------|:--------------------|:------------------|:-----------------|:---------------------------------|
| final (reference)                                              | 2006-2026 | 89.0                 | 53.9                | -7.0              | 0.01             |                                  |
| final (reference)                                              | 2016-2026 | 50.0                 | 56.0                | 42.9              | 0.44             |                                  |
| features_lag_plus1week                                         | 2006-2026 | 78.0                 | 52.6                | -9.1              | -0.0             |                                  |
| features_lag_plus1week                                         | 2016-2026 | 50.0                 | 58.0                | 45.2              | 0.4              |                                  |
| features_lag_plus4weeks                                        | 2006-2026 | 22.0                 | 40.9                | -144.6            | -0.39            |                                  |
| features_lag_plus4weeks                                        | 2016-2026 | 10.0                 | 40.0                | -88.8             | -0.28            |                                  |
| features_lag_plus13weeks                                       | 2006-2026 | 27.0                 | 44.4                | -28.5             | -0.07            |                                  |
| features_lag_plus13weeks                                       | 2016-2026 | 4.0                  | 75.0                | 45.0              | 0.06             |                                  |
| features_from_1week_AHEAD_lookahead_control                    | 2006-2026 | 75.0                 | 50.7                | -8.2              | -0.0             |                                  |
| features_from_1week_AHEAD_lookahead_control                    | 2016-2026 | 42.0                 | 54.8                | 49.8              | 0.51             |                                  |
| features_from_21sessions_AHEAD_lookahead_control               | 2006-2026 | 78.0                 | 57.7                | 2.9               | 0.1              |                                  |
| features_from_21sessions_AHEAD_lookahead_control               | 2016-2026 | 49.0                 | 67.3                | 97.6              | 1.08             |                                  |
| control_trend_family_only_honest                               | 2006-2026 | 240.0                | 54.6                | 3.0               | 0.03             |                                  |
| control_trend_family_only_honest                               | 2016-2026 | 125.0                | 52.8                | -5.3              | -0.08            |                                  |
| control_trend_family_only_21sessions_AHEAD                     | 2006-2026 | 241.0                | 63.1                | 73.0              | 0.8              |                                  |
| control_trend_family_only_21sessions_AHEAD                     | 2016-2026 | 125.0                | 60.8                | 49.8              | 0.83             |                                  |
| shuffled_labels_weekly_accuracy_thr0.5 (pooled over seeds)     | 2006-2026 | 537.5                | 50.6                |                   |                  | 0.019 / -                        |
| shuffled_labels_weekly_accuracy_thr0.55 (pooled over seeds)    | 2006-2026 | 6.6                  | 47.0                |                   |                  | 0.216 / -                        |
| shuffled_labels_weekly_accuracy_thr0.6 (pooled over seeds)     | 2006-2026 | 0.0                  | 0.0                 |                   |                  |                                  |
| permuted_price_path_always_in_market (pooled over seeds)       | 2006-2026 | 137.8                | 49.4                | 2.4               | -0.01            | 0.046 / 0.19                     |
| permuted_price_path_full_pipeline (accuracy pooled over seeds) | 2006-2026 | 9.0                  | 40.8                | -43.0             | -0.07            | 0.267 / 0.16                     |

1. **Shuffled labels** (targets permuted among decision rows, used for fitting and scoring, 20 seeds): 50.6 % at
   "always act"; the calibrator then issues a P >= 0.55 call on 7 weekly decisions per run instead of ~370 and none
   at 0.60. **Permuted price path** (daily bars from 1999 re-ordered at random, the whole pipeline including the trade
   simulation, 20 seeds): 49.4 % and Sharpe -0.01 (sd 0.19) when always in the market; at P >= 0.55 only ~9 trades a
   run, Sharpe -0.07 (sd 0.16). The 41 % pooled accuracy of those few trades is 1.5 standard errors below 50 across
   seeds and has a mechanical cause: a permutation keeps the total 1999-2026 return, so whatever drift the training
   window had is taken back in the test window. Note that the null Sharpe has a standard deviation of about 0.2 over
   21 years: the flagged rule's 0.02 (2006-26) and 0.28 (2010-26) sit inside it.
2. **Features lagged** by 1 / 4 / 13 extra weeks: 52.6 / 40.9 / 44.4 % and the number of P >= 0.55 calls falls from 89
   to 78 / 22 / 27, because the in-sample calibration slope shrinks. With a reference this close to zero "collapse" is
   not a meaningful word; what the test shows is that nothing improves with stale inputs. **Look-ahead control**: the
   full scorecard fed with predictors from 21 sessions ahead rises to 57.7 % only, because the trend family's leak is
   offset by the valuation family, which votes against a price that has risen. The trend family alone makes the harness's
   sensitivity plain (and in 2016-26 the full scorecard does jump, to 67.3 % and Sharpe 1.08): 54.6 % honest, 63.1 % and Sharpe 0.80 with features from 21 sessions ahead.
3. **Label in disguise**: largest correlations of an oriented predictor with the forward 21-session return on weekly rows:

| predictor   |   corr_fwd_h21 |   corr_fwd_h42 |
|:------------|---------------:|---------------:|
| cot_z156    |          0.170 |          0.200 |
| cot_z52     |          0.159 |          0.192 |
| rrd2_lvl    |         -0.148 |         -0.202 |
| eqrel63     |          0.148 |          0.159 |
| rrd10_d126  |         -0.134 |         -0.193 |
| rrd10_lvl   |         -0.132 |         -0.172 |
| rd2_d126    |          0.112 |          0.135 |
| rd2_d63     |          0.111 |          0.166 |
| cot_ext     |         -0.097 |         -0.140 |
| slope2_diff |         -0.084 |         -0.140 |

   Nothing above 0.2; the negative entries are the wrongly-signed real-rate and slope priors. `seas_month` is the only
   predictor built from labels and it uses prior calendar years only. `seas` looks forward on the calendar, not on
   prices.
4. The trade list and the daily stream reconcile (sum of side x log(exit / entry) = sum of the stream's gross P&L, to
   0.02 bp; carry to 0.3 %). A stop trade and a time-exit trade were checked by hand against the session bars.
5. Entry one session late: -12 pips a trade against -7; no dependence on the exact entry close.

## 10. Variant count, caveats
* **Candidates: 12** (3 models x 2 clocks x 2 thresholds), the cap. Forecasters behind them: 9 (3 models x 3 targets), of
  which the candidates use 3. Reported but not selectable: 14 sensitivity runs of the flagged rule, 2 live-exposure
  benchmarks, 22 ablation runs, 12 candidate replays on the pre-1999 sample, 33 single-predictor rows, and 47 leak-check
  runs (5 feature shifts, 2 trend-only controls, 20 label shuffles, 20 permuted paths). The candidate set, the models
  and the selection rule were not touched after the first result. Added after results were seen, all outside the
  candidate set: the live-exposure benchmark, the trend-only look-ahead control, the always-in-the-market version of
  the permuted-path null and the pooling of null accuracies over seeds; two reporting bugs were fixed (a read-only
  array in the label shuffle, time-zone stamps in the trade file).
* Departures from the brief, all forced: (a) daily DEM is not in the H.10 file and not on FRED any more, hence the
  DKK bridge; (b) no Yahoo, hence no S&P before 2003 and no VIX term structure; (c) the 42-session and barrier trades
  cannot reach 8 trades a year with one position at a time, so they were run as sensitivities, not candidates.
* The early test years lean on thin training data (1999-2005; 2-year yields and equities enter the fitted models in
  2007-2008). The scorecard's calibration slope for 2006 came from 7 years and produced confident, wrong short calls
  through 2006 (probabilities up to 0.68). That is what a short history does and it is part of the honest record.
* The monthly sample is small by nature: 246 non-overlapping decisions in 21 years. A true 55 % accuracy has a standard
  error of 3.2 points on that sample, so 54 % cannot be told from 50 % or from 58 %. More history was the point of the
  pre-1999 sample, and there the prior-signed scorecard is at 49 %.
* Suspicious-looking and explained: T and L make no calls in 2007-2014 (b = 0, see section 3); "only VAL" never trades
  (same reason); 75 % of the flagged rule's trades are short because the rate-level, real-rate and carry families have voted
  dollar for most of 2006-2026.

## What this means for the product
* Do not attach "P >= 60 %" to a monthly EUR/USD direction call from this information set. The honest number is about
  54-59 % when always acting, with a 95 % interval of roughly +-6-7 points, and about 50 % since 2023.
* The horizon effect in the scoreboard (52 / 55 / 58 %) is the same slow positioning-and-equity signal read over a
  longer window, not additional predictability that a purpose-built monthly model can harvest.
* If the position-trading product is run anyway, the least bad expression in this repository is the existing live
  exposure read at month-ends (section 5), with the carry accounted for (about 13 pips a month for or against the
  position at the 2006-2026 average rate gap; it has been ignored so far), and with the planning Sharpe the research
  log already gives for it (0.25-0.45), not the 0.6 of its in-sample-selected record.
