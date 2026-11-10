# EUR/USD prediction research: final report

Date: 2026-11-10. Everything below was produced inside this repository; every number can be regenerated
from the scripts in `experiments/` (results in `experiments/results/`, agent reports in `reports/`).

## 1. What was asked and what was done

Goal: collect all available EUR/USD data, crawl the web for formulas, patterns and behaviour, backtest
everything, keep only what works, and build software that emits entries with stop-loss and take-profit.

| Stage | Outcome |
|---|---|
| Price data | HistData 1-minute bid bars 2000-05-30 .. 2026-11-06 (9.04 M bars), rebuilt as M1/M5/M15/M30/H1/H4/D1 parquet. Timestamps proved to be New York local time **with** DST (not EST as HistData claims); verified against ECB fixings and NFP release spikes. Cross-checked with Yahoo (median 1-3 pips) and the ECB reference rate (median 1.8 pips). Known hole: Feb-Jul 2023 (763 missing hours at the source). `data/DATA_QUALITY.md`. |
| Macro / positioning / events | ECB policy rates, euro-area AAA curve, HICP, unemployment; 46 FRED series via GitHub mirrors (2y/10y yields, fed funds, CPI, payrolls, VIX, S&P...); CFTC COT EUR futures 1999-2026 (legacy + TFF); 70 k economic-calendar rows 2010-2026 incl. actual/forecast; verified FOMC (329) and ECB (321) decision timestamps; BLS release schedule. `data/macro/README.md`. |
| Research | 102 practitioner strategies with exact rules and evidence grade (`research/strategy_catalogue.md`, `strategies.json`); 51 academic hypotheses with effect sizes (`research/literature_review.md`, `hypotheses.json`). Both researchers note that WebFetch was blocked for most hosts, so they relied on search summaries. |
| Engine | Chronological bar simulator: market/stop/limit orders, one-cancels-other groups, spread 1.0 pip + slippage 0.2 pip per fill, pessimistic stop-first resolution with optional M1 arbitration, R-multiple and pip statistics, bootstrap and deflated-Sharpe helpers. Two artefacts found by the testing agents were fixed (same-bar take-profit on limit fills; non-chronological OCO pairs). `experiments/test_backtest.py` covers them. |
| Protocol | TRAIN 2003-2015 (explore), VALIDATE 2016-2022 (confirm once per family), HOLDOUT 2023-2026 (touched exactly once, by the final system). Survival = validate avg R > 0, t >= 2, profit factor >= 1.15, >= 60 % of years positive, >= 30 trades, parameter neighbourhood positive on train. |

## 2. Results

### 2.1 Nothing survives as a stand-alone rule

| Family group | Families tested | Survivors | Report |
|---|---|---|---|
| Built-in indicator families (MA cross, Donchian, MACD, Supertrend, RSI, Bollinger, pivots, opening-range / Asian-range breakouts) | 19 | 0 | `experiments/results/logs/*.log`, `02_grid_builtin.py` |
| Session / time-of-day / calendar (S01-S19, B01, C01-C06, Q04) | 36 | 0 | `reports/catalogue_session_calendar.md` |
| Breakout / trend / volatility / price action (T01-T18, V01-V04, P01-P12) | 82 | 0 | `reports/catalogue_trend_vol_pa.md` |
| Mean reversion / systematic / ML (M01-M15, Q01-Q06) | 34 + ML | 0 | `reports/catalogue_meanrev_systematic.md` |
| Academic price-only hypotheses (fix effects, local-hours, weekend gaps, momentum, turn-of-month, vol regimes) | 46 tests | 0 standalone | `reports/hypotheses_price.md` |
| Event hypotheses (FOMC, ECB, NFP, CPI incl. straddles and surprise trades) | 48 tests | 0 | `reports/hypotheses_events.md` |
| Fundamental / positioning (2y and 10y spreads, carry, COT, VIX, S&P regimes) | 23 tests | 0 | `reports/hypotheses_fundamental.md` |

Notable confirmations of published negative results: the plain London breakout (Backtrex: PF 0.87) reproduces
as PF 0.93; MACD+RSI H1 (vendor PF 0.80) reproduces as PF 0.90; Connors RSI(2) is negative on every grid point;
ICT concepts (killzones, FVG, order blocks, silver bullet, Judas swing), harmonic patterns, Fibonacci entries,
pivot bounces, round numbers, candlestick patterns and news straddles are all flat or negative after costs.
An honest ML baseline (logistic / LightGBM on 25 daily features, rolling refits) reaches 52 % directional accuracy
and t = 1.5 after costs - not enough.

Two results that looked like survivors turned out to be engine artefacts and are documented as such: the
Asian-range breakout (validation t 2.6 before the OCO fix, -0.4 after) and the Larry Williams M5 breakout
(t +5.7 before, -1.0 after). The four breakout grids re-run on the corrected engine
(`experiments/results/logs/breakouts_oco_engine.log`): Asian range M15 validation t -0.24 (PF 0.98), fixed-pip
variant t -0.92, London opening range M5 t +0.28 (PF 1.02), New York opening range M5 t -0.98. News straddles
re-run with correct OCO handling stay negative (NFP t -2.2 train / -2.8 validate).

### 2.2 Effects that keep their sign (weak, not individually significant on validation)

| Component | Rule | Train 2003-15 | Validate 2016-22 | Holdout 2023-26 |
|---|---|---|---|---|
| `london_short` | short 07:00-13:00 London local, 1 x ADR disaster stop | t 2.1, 77 % yrs | t 1.4 (1.7 in pips), PF 1.09, 86 % yrs | t -0.2, PF 0.99 |
| `fomc_day_long` | long from the NY close before a scheduled FOMC statement to the statement-day close, 1.5 x ATR stop | t 1.7, PF 1.53 | t 1.6, PF 1.65, 86 % yrs | t 0.3, PF 1.14 |
| `cot_trend` | weekly position in the sign of the 52-week z-score of non-commercial EUR futures net positioning, 2 x ATR stop | t 1.9, PF 1.20 | t 1.3, PF 1.18 | t 0.9, PF 1.20 |

Daily P&L correlations between the three are below 0.05 in every period. The combination (1 % risk per trade):

| Period | Sharpe | t-stat | Max drawdown | Years positive |
|---|---|---|---|---|
| Train 2003-2015 | 0.86 | 3.1 | -12 % | 92 % |
| Validate 2016-2022 | 0.79 | 2.1 | -11 % | 86 % |
| **Holdout 2023-2026 (run once)** | **0.26** | **0.53** | -11 % | 4/4 (+3.8 %, +1.9 %, +1.3 %, +0.9 %) |

The holdout is the verdict: the combined system earned about 1.8 % a year at 1 % risk per trade on 2023-2026, which is not distinguishable from zero (t 0.5).
This agrees with the literature (technical rules dead since the 1990s; the London-fix and local-hours effects
documented on 1997-2012 data; post-2015 decay reported by the FCA and by Krohn-Mueller-Whelan).

### 2.3 Behaviour facts that are robust (useful for execution, not for direction)

* Average daily range: 121 pips (2003-2015), 80 pips (2016-2022), 71 pips (2023-2026); 2008: 185, 2019: 55.
* Hourly range peaks at 13:00-16:00 UTC (London/NY overlap, 24-38 pips per hour) and troughs at 21:00-05:00 UTC (7-13 pips).
* The 08:00-11:00 ET block sets the daily high or low 7-9 % per hour versus 4.2 % for a random hour.
* The previous day's high or low is taken out on ~49 % of days each, both on ~11 %, neither on ~14 %.
* Daily and hourly returns have no exploitable autocorrelation (|rho| < 0.02 at all lags).
* NFP moves EUR/USD 10-18 bp in the first five minutes; price returns to the pre-release level within an hour on
  59-69 % of releases, but neither fading nor following the jump is profitable after costs.
* Realised volatility is forecastable: a HAR model beats the naive forecast by 25-30 % RMSE out of sample
  (`src/eurusd/volatility.py`); use it for sizing, not for direction.

## 3. The software

* `PYTHONPATH=src python -m eurusd.cli signals` prints the actionable orders of the live components for the latest
  closed bar: side, entry type and price, stop-loss, take-profit (time exit where the component has none), validity,
  hard exit time and position size for the given account and risk per trade. `--asof` replays any past moment.
* `config/live_strategies.json` holds the components with their full validation record; add or remove components there.
* `python -m eurusd.cli update` downloads the newest HistData month(s) and rebuilds the bars; `python -m eurusd.macro_fetch`
  refreshes the macro inputs (the CFTC file and FOMC calendar must be current for two of the components).
* `python -m eurusd.cli backtest NAME TF PARAMS --period validate` backtests any registered strategy (built-in plus the
  ~65 strategies the testing agents wrote in `strategies_session.py`, `strategies_trend_pa.py`, `strategies_meanrev.py`).

## 3b. Risk engine (added after the research phase)

`src/eurusd/risk.py` sits between every signal and the order: sizing by the minimum of a hard cap, a quarter-Kelly
cap from the component's own trade record, a HAR volatility target and the open-risk budget; event gating around
FOMC/ECB/NFP/CPI; kill switches on daily, monthly and peak-to-trough losses, consecutive losses, stale data and
spreads; parametric, historical (stop-aware, 6,800 days) and Monte Carlo value-at-risk; minute-level stress replays
of nine historical shock episodes and synthetic gaps; and a health check comparing each component's live trades to
its validation distribution. `python -m eurusd.cli risk` produces the report; `reports/risk_latest.md` is the latest.
It limits damage and sizes correctly. It does not create edge, and the holdout verdict above is unchanged.

## 4. Recommendation

Do not trade the signals as a stand-alone source of edge: the untouched holdout says the edge is not there in
2023-2026. The system is a sound research platform (clean data, correct engine, pre-registered protocol) and the
three components are the only effects that did not fail. Reasonable next steps if the project continues:
rolling re-validation each year with the same protocol, execution-cost reduction (the London component's gross
2.3 bp/day survives only with sub-pip spreads), and adding genuinely new information (order flow, options
positioning) rather than more indicator combinations.
