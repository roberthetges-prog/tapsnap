"""Tests for the live exposure plan logic (no network)."""
import sys, math
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
from eurusd.exposure import Exposure, plan

e = Exposure(asof_session_close="x", target_units=-0.67, c_units=0.0, d_units=-1.34, c_score=0.05, c_threshold=0.1, c_vol_scale=1.0,
             d_cot_z52=-2.05, d_vol_scale=1.34, top_contributions={}, price=1.11682, atr20_pips=61.4, stop_distance_pips=122.8, rebalance_band=0.5)
# 10k equity, 8% annual vol target, 37 bp daily vol -> unit notional = 0.08/sqrt(252)*10000/0.0037 = 13,620 USD = 0.136 lots
p = plan(e, 10_000, 0.08, 0.0037, current_units=0.0)
assert p["action"] == "rebalance" and p["side"] == "short" and abs(p["lots_per_unit"] - 0.136) < 0.002, p
assert abs(p["target_lots"] - 0.09) < 0.011 and p["stop"] > e.price, p
# already short 0.5 units: change 0.17 < band and no sign flip -> hold
assert plan(e, 10_000, 0.08, 0.0037, current_units=-0.5)["action"] == "hold"
# currently long -> sign flip -> rebalance even for a small move
assert plan(e, 10_000, 0.08, 0.0037, current_units=0.1)["action"] == "rebalance"
# flat target -> flat side, no stop
e2 = Exposure(**{**e.__dict__, "target_units": 0.0})
p2 = plan(e2, 10_000, 0.08, 0.0037, current_units=-0.5)
assert p2["side"] == "flat" and p2["stop"] is None and p2["action"] == "rebalance", p2
print("exposure tests pass")
