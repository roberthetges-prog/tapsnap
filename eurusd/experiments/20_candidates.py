"""Candidate components on TRAIN and VALIDATE (holdout untouched). Writes results/candidates.csv"""
import sys, json
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import pandas as pd, numpy as np
from eurusd.backtest import CostModel
from eurusd.evaluate import run_one
from eurusd import features as F
import eurusd.strategies_candidates  # noqa

COST = CostModel(spread_pips=1.0, slippage_pips=0.2)
D = "/home/user/tapsnap/eurusd/data/processed/"
m15 = pd.read_parquet(D + "EURUSD_M15.parquet")
h1 = pd.read_parquet(D + "EURUSD_H1.parquet")
d1 = F.daily_ohlc(h1, 22); d1 = d1[d1["n"] >= 10].drop(columns="n")
d1 = d1[d1.index.dayofweek != 5]
CANDS = {
    "london_short": (h1, dict(entry_min=7 * 60, exit_min=13 * 60, stop_adr=1.0)),
    "asian_breakout": (m15, dict(start=1, end=8, entry_until=14, tp_rr=3.0, exit_hour=20)),
    "month_end_fix": (m15, dict(stop_pips=15, min_move_pips=3)),
    "weekend_gap_fade": (d1, dict(gap_atr=0.2, hold=1, stop_atr=1.0)),
    "fomc_day_long": (d1, dict(stop_atr=1.5)),
    "cot_trend": (d1, dict(hold_days=5, stop_atr=2.0)),
}
rows = []
periods = sys.argv[1:] or ["train", "validate"]
for name, (df, params) in CANDS.items():
    for period in periods:
        s, res = run_one(df, name, params, period, COST)
        s["name"] = name
        rows.append(s)
        print(f"{name:18s} {period:9s} n={s['trades']:5d} win={s.get('win_rate',0):.2f} avgR={s.get('avg_r',0):+.3f} avg_pips={s.get('avg_pips',0):+.2f} PF={s.get('profit_factor',0):.2f} t={s.get('t_stat',0):+.2f} tpips={s.get('t_stat_pips',0):+.2f} yrs+={s.get('years_positive',0):.0%} sl%={s.get('sl_rate',0):.2f}")
        res.tdf.to_csv(f"/home/user/tapsnap/eurusd/experiments/results/trades_{name}_{period}.csv", index=False)
pd.DataFrame(rows).to_csv("/home/user/tapsnap/eurusd/experiments/results/candidates.csv", index=False)
