"""Combine candidate components (trade lists from 20_candidates.py) into a portfolio on TRAIN and VALIDATE."""
import sys
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import pandas as pd, numpy as np
from eurusd.portfolio import stats, by_year

R = "/home/user/tapsnap/eurusd/experiments/results/"
names = ["asian_breakout", "london_short", "fomc_day_long", "cot_trend", "weekend_gap_fade", "month_end_fix"]
periods = sys.argv[1:] or ["train", "validate"]
for period in periods:
    pnls = {}
    for n in names:
        t = pd.read_csv(R + f"trades_{n}_{period}.csv", parse_dates=["exit_time"])
        r = t["r"].where(np.isfinite(t["r"]), t["pips"] / 20.0)
        ex = pd.DatetimeIndex(t["exit_time"])
        ex = ex.where(ex.dayofweek < 5, ex + pd.Timedelta(days=1))  # Sunday-start daily bars count as Monday
        s = pd.Series(r.values * 0.01, index=ex.floor("D"))
        pnls[n] = s.groupby(level=0).sum()
    df = pd.DataFrame(pnls).fillna(0.0)
    df = df[df.index.dayofweek < 5]
    print(f"\n=== {period} ===")
    print("correlation of daily P&L:\n", df.corr().round(2).to_string())
    combos = {"all six": names, "breakout only": ["asian_breakout"], "breakout+fomc+london": ["asian_breakout", "fomc_day_long", "london_short"],
              "breakout+fomc+london+cot": ["asian_breakout", "fomc_day_long", "london_short", "cot_trend"]}
    rows = {}
    for k, cols in combos.items():
        p = df[cols].sum(axis=1)
        rows[k] = stats(p)
        rows[k]["years_positive"] = float((by_year(p) > 0).mean())
    for n in names:
        rows[n] = stats(df[n]); rows[n]["years_positive"] = float((by_year(df[n]) > 0).mean())
    print(pd.DataFrame(rows).T.round(3).to_string())
