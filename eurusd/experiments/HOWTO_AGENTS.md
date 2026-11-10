# How to test a strategy with this engine (read fully before writing code)

Run everything from /home/user/tapsnap/eurusd with `sys.path.insert(0, "/home/user/tapsnap/eurusd/src")`.

## Data
`from eurusd.data import load_ohlc`; `df = load_ohlc("M5")` (M1, M5, M15, M30, H1, H4, D1). UTC index, bid prices,
columns open/high/low/close/volume (volume is always 0). Bars are labelled by their START time.
Timestamps are true UTC (converted from New York local time with DST). So:
* London session is 08:00-16:30 **London local**; use `df.index.tz_convert("Europe/London")` for local-time rules.
* NY session open 08:00 New York local = 13:00 UTC winter / 12:00 UTC summer. Use `America/New_York`.
* The FX day starts 17:00 New York. `eurusd.features.daily_ohlc(df, day_start_utc_hour=22)` builds NY-close days
  (22 UTC winter; use 21 in summer or accept the 1h slip).
* Feb-Jul 2023 is missing ~760 hours (source hole) - intraday results in 2023 are unreliable. 2000-2002 is thin.
* A few bad ticks remain in 2000-2002 (irrelevant to TRAIN/VALIDATE which start 2003).

## Orders and backtest
```python
from eurusd.backtest import Order, CostModel, run_backtest
# Order(i, side, entry_type='market'|'stop'|'limit', entry_price, sl, tp, expiry_bars, max_hold, exit_i, tag)
#   i       = bar index at which the decision is made (uses info up to and incl. bar i close)
#   market  = filled at bar i+1 open (+spread for longs)
#   stop/limit = pending at entry_price for expiry_bars bars after i
#   sl/tp   = absolute prices (NaN = none); exit_i = hard exit at the close of that bar index; max_hold = bars
res = run_backtest(df, orders, CostModel(spread_pips=1.0, slippage_pips=0.2))
res.summary()   # trades, win_rate, avg_r, avg_pips, profit_factor, t_stat, years_positive (via run_one), ...
res.by_year(); res.tdf  # trade list with entry_time/exit_time/reason
```
Costs: 1.0 pip spread + 0.2 pip slippage per fill, always. R = profit / initial stop distance. If a strategy has no stop,
metrics fall back to pips (`has_r=False`, `t_stat_pips`, `profit_factor_pips`).
Intra-bar SL/TP ambiguity is resolved pessimistically (SL first) unless you pass `ltf=load_ohlc("M1")` slice.

## Protocol (do not bend it)
`from eurusd.evaluate import SPLITS, run_one, run_grid, neighbourhood_ok, verdict`
* TRAIN 2003-2015 for exploring/choosing parameters; VALIDATE 2016-2022 once per family with the chosen parameters;
  HOLDOUT 2023+ is forbidden - never run anything on it.
* `run_one(df, strategy_name, params, "train", cost)` returns (summary_dict, result). Strategies must be registered:
  put your functions in your OWN module (e.g. `src/eurusd/strategies_session.py`) and register with
  `from eurusd.strategies import REGISTRY; REGISTRY["my_name"] = my_func` at import time, then import your module
  before calling run_one. Do NOT edit strategies.py, backtest.py, evaluate.py, features.py (other agents use them).
* Survival rules on VALIDATE: avg R > 0, t >= 2, PF >= 1.15, >= 60 % of years positive, parameter neighbourhood
  positive on TRAIN (`neighbourhood_ok`), >= 30 trades. `verdict(train_best_row, val_summary, neigh_ok)` applies them.
* Keep grids small (<= 60 points per family; the engine is pure Python, ~1-4 s per run on M15, more on M5).
  Run heavy grids with `nohup ... &` and poll the log; 4 CPUs are shared with other agents - use at most 2 processes.
* For every catalogue entry record: catalogue id, what exactly you implemented (your reconstruction where rules were vague),
  train best params, train stats, validate stats, verdict + reason. Also record it when you could NOT implement an entry
  (discretionary / needs data we lack) and why.

## Helpers (eurusd.features)
sma, ema, rsi, atr, bollinger, donchian, macd, adx, stochastic, keltner, supertrend, daily_ohlc, prev_day_levels
(pivots incl. camarilla), session_range(df, start_hour, end_hour) [UTC hours, same-day window], time_features, zscore.
