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

# 5) limit order: buy limit at 1.1000 placed bar3 (bar4 open 1.1030, low 1.0990 -> fills; bar4 high 1.1040 >= tp 1.1035 but
#    without M1 data the same-bar TP is NOT allowed). Then bar5 low 1.0950 <= sl 1.0960 -> sl.
r = run_backtest(df, [Order(i=3, side=1, entry_type="limit", entry_price=1.1000, expiry_bars=2, sl=1.0960, tp=1.1035)], cost)
t = r.trades[0]
assert t.entry_i == 4 and abs(t.entry - 1.1000) < 1e-9 and t.reason == "sl" and t.exit_i == 5, t
# 5b) with M1 data showing the dip to 1.0999 first and then the rally to 1.1040: TP allowed on the entry bar
m1b = pd.DataFrame({"open":[1.1030,1.1000,1.1010,1.1035],"high":[1.1030,1.1005,1.1041,1.1036],"low":[1.0999,1.0990,1.1008,1.1030],"close":[1.1000,1.1005,1.1040,1.1030]},
                   index=pd.to_datetime(["2024-01-01 04:00","2024-01-01 04:15","2024-01-01 04:30","2024-01-01 04:45"], utc=True))
r = run_backtest(df, [Order(i=3, side=1, entry_type="limit", entry_price=1.1000, expiry_bars=2, sl=1.0960, tp=1.1035)], cost, ltf=m1b)
assert r.trades[0].reason == "tp" and r.trades[0].exit_i == 4, r.trades[0]
# 6) market order can take profit on its entry bar when the stop is not touched: long at bar1 open (1.1006), tp 1.1025 (bar1 high 1.1030)
r = run_backtest(df, [Order(i=0, side=1, sl=1.0980, tp=1.1025)], cost)
assert r.trades[0].reason == "tp" and r.trades[0].exit_i == 1, r.trades[0]
print("all backtest tests pass")

# 7) OCO pair: buy stop 1.1035 / sell stop 1.1015 placed at bar1 (bar2 open 1.1020, high 1.1060, low 1.1015).
#    Without M1 data: the sell stop (5 pips from open) is assumed touched before the buy stop (15 pips) -> short fills,
#    its stop (1.1035) is hit on the same bar -> -1R; the buy stop is cancelled (OCO), so no long trade follows.
pair = [Order(i=1, side=1, entry_type="stop", entry_price=1.1035, sl=1.1015, tp=1.1095, expiry_bars=3, tag="x"),
        Order(i=1, side=-1, entry_type="stop", entry_price=1.1015, sl=1.1035, tp=1.0955, expiry_bars=3, tag="x")]
r = run_backtest(df, pair, cost)
assert len(r.trades) == 1 and r.trades[0].side == -1 and r.trades[0].reason == "sl" and r.trades[0].exit_i == 2, r.trades
# 7b) with M1 data showing the rally first: the long fills first, the short is cancelled, long exits by time
m1c = pd.DataFrame({"open":[1.1020,1.1040,1.1055,1.1030],"high":[1.1045,1.1060,1.1056,1.1050],"low":[1.1019,1.1038,1.1015,1.1028],"close":[1.1040,1.1055,1.1030,1.1050]},
                   index=pd.to_datetime(["2024-01-01 02:00","2024-01-01 02:15","2024-01-01 02:30","2024-01-01 02:45"], utc=True))
r = run_backtest(df, pair, cost, ltf=m1c)
assert len(r.trades) == 1 and r.trades[0].side == 1 and r.trades[0].entry_i == 2, r.trades
# 8) a pending order cannot fill while a trade is open; it fills afterwards if still valid
ords = [Order(i=0, side=1, sl=1.0980, tp=1.1055),  # fills bar1, tp bar2
        Order(i=0, side=-1, entry_type="limit", entry_price=1.1050, sl=1.1080, tp=1.1000, expiry_bars=4, tag="y")]
r = run_backtest(df, ords, cost)
# bar2 touches 1.1050 but the long is still open (exits on bar2) -> no fill on the exit bar; bar3 high 1.1055 -> fills at 1.1050; tp on bar4
assert len(r.trades) == 2 and r.trades[1].entry_i == 3 and r.trades[1].side == -1 and r.trades[1].reason == "tp" and r.trades[1].exit_i == 4, r.trades
print("oco / pending tests pass")
