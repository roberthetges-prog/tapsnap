"""ONE-TIME holdout evaluation (2023-01-01 .. today) of the pre-registered final system:
components london_short + fomc_day_long + cot_trend with the parameters fixed on TRAIN and
confirmed on VALIDATE in 20_candidates.py / 21_portfolio_validate.py. Run once; do not tune on this.
"""
import sys, json
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import pandas as pd, numpy as np
from eurusd.backtest import CostModel
from eurusd.evaluate import run_one
from eurusd import features as F
from eurusd.portfolio import stats, by_year
import eurusd.strategies_candidates  # noqa

COST = CostModel(spread_pips=1.0, slippage_pips=0.2)
D = "/home/user/tapsnap/eurusd/data/processed/"
h1 = pd.read_parquet(D + "EURUSD_H1.parquet")
d1 = F.daily_ohlc(h1, 22); d1 = d1[d1["n"] >= 10].drop(columns="n"); d1 = d1[d1.index.dayofweek != 5]
FINAL = {
    "london_short": (h1, dict(entry_min=7 * 60, exit_min=13 * 60, stop_adr=1.0)),
    "fomc_day_long": (d1, dict(stop_atr=1.5)),
    "cot_trend": (d1, dict(hold_days=5, stop_atr=2.0)),
}
R = "/home/user/tapsnap/eurusd/experiments/results/"
rows = []; pnls = {}
for name, (df, params) in FINAL.items():
    s, res = run_one(df, name, params, "holdout", COST)
    s["name"] = name; rows.append(s)
    print(f"{name:14s} holdout n={s['trades']:5d} win={s.get('win_rate',0):.2f} avgR={s.get('avg_r',0):+.3f} avg_pips={s.get('avg_pips',0):+.2f} PF={s.get('profit_factor',0):.2f} t={s.get('t_stat',0):+.2f} yrs+={s.get('years_positive',0):.0%}")
    print(res.by_year().round(3).to_string())
    res.tdf.to_csv(R + f"trades_{name}_holdout.csv", index=False)
    t = res.tdf
    ex = pd.DatetimeIndex(t["exit_time"]); ex = ex.where(ex.dayofweek < 5, ex + pd.Timedelta(days=1))
    pnls[name] = pd.Series(t["r"].values * 0.01, index=ex.floor("D")).groupby(level=0).sum()
df = pd.DataFrame(pnls).fillna(0.0); df = df[df.index.dayofweek < 5]
p = df.sum(axis=1)
st = stats(p); st["years_positive"] = float((by_year(p) > 0).mean())
print("\nPORTFOLIO holdout (1% risk per trade):", json.dumps({k: round(v, 3) for k, v in st.items()}))
print("by year:", by_year(p).round(3).to_dict())
pd.DataFrame(rows).to_csv(R + "holdout_components.csv", index=False)
json.dump({"portfolio": st, "by_year": {str(k): float(v) for k, v in by_year(p).items()}}, open(R + "holdout_portfolio.json", "w"), indent=1)
