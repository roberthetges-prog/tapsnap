"""Sanity tests for the backtester on hand-built bars."""
import sys, math
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import numpy as np, pandas as pd
from eurusd.backtest import Order, CostModel, run_backtest

idx = pd.date_range("2024-01-01", periods=10, freq="h", tz="UTC")
# bars: open high low close
rows = [
 (1.1000, 1.1010, 1.0990, 1.1005),
 (1.1005, 1.1030, 1.1000, 1.1020),  # bar1: entry bar for market order placed at bar0
 (1.1020, 1.1060, 1.1015, 1.1050),  # bar2: TP at 1.1055 hit
 (1.1050, 1.1055, 1.1020, 1.1030),
 (1.1030, 1.1040, 1.0990, 1.1000),  # bar4
 (1.1000, 1.1010, 1.0950, 1.0960),  # bar5
 (1.0960, 1.0980, 1.0940, 1.0970),
 (1.0970, 1.1000, 1.0960, 1.0990),
 (1.0990, 1.1010, 1.0980, 1.1000),
 (1.1000, 1.1020, 1.0990, 1.1010),
]
df = pd.DataFrame(rows, columns=["open","high","low","close"], index=idx)
cost = CostModel(spread_pips=1.0)

# 1) long market order at bar0, TP 1.1055, SL 1.0980 -> entry bar1 open 1.1005+0.0001, tp hit bar2
r = run_backtest(df, [Order(i=0, side=1, sl=1.0980, tp=1.1055)], cost)
t = r.trades[0]
assert t.entry_i == 1 and abs(t.entry - 1.1006) < 1e-9, t
assert t.reason == "tp" and t.exit_i == 2 and abs(t.pips - 49) < 1e-6, t
assert abs(t.r - (1.1055-1.1006)/(1.1006-1.0980)) < 1e-9

# 2) short market at bar3 (entry bar4 open 1.1030), SL 1.1045, TP 1.0955: bar4 low 1.0990 no; bar5 low 1.0950 -> tp (bid_lo+spread=1.0951<=1.0955)
r = run_backtest(df, [Order(i=3, side=-1, sl=1.1045, tp=1.0955)], cost)
t = r.trades[0]
assert t.entry_i == 4 and t.reason == "tp" and t.exit_i == 5, t
assert abs(t.pips - (1.1030-1.0955)/1e-4) < 1e-6, t.pips

# 3) both SL and TP inside one bar -> SL assumed first. long placed bar1, entry bar2 open 1.1021; sl 1.1016, tp 1.1058: bar2 low 1.1015 <= sl and high 1.1060>=tp
r = run_backtest(df, [Order(i=1, side=1, sl=1.1016, tp=1.1058)], cost)
t = r.trades[0]
assert t.reason == "sl", t

# 3b) same with M1 data resolving TP first
m1 = pd.DataFrame({"open":[1.1021,1.1040,1.1058,1.1030],"high":[1.1040,1.1058,1.1060,1.1030],"low":[1.1020,1.1040,1.1015,1.1015],"close":[1.1040,1.1058,1.1016,1.1016]},
                  index=pd.to_datetime(["2024-01-01 02:00","2024-01-01 02:15","2024-01-01 02:30","2024-01-01 02:45"], utc=True))
r = run_backtest(df, [Order(i=1, side=1, sl=1.1016, tp=1.1058)], cost, ltf=m1)
assert r.trades[0].reason == "tp", r.trades[0]

# 4) buy stop order above market: placed bar4 at 1.1005 expiry 3 bars: bar5 high 1.1010+spread>=1.1005 -> entry at max(1.1005, open 1.1000+0.0001)=1.1005
r = run_backtest(df, [Order(i=4, side=1, entry_type="stop", entry_price=1.1005, expiry_bars=3, sl=1.0940, tp=1.1100, max_hold=2)], cost)
t = r.trades[0]
assert t.entry_i == 5 and abs(t.entry - 1.1005) < 1e-9 and t.reason == "sl" and t.exit_i == 6, t  # bar6 low 1.0940 hits the stop
