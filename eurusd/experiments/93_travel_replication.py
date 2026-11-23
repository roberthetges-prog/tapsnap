"""Round 34 (declared before running): does the travel band replicate on six dollar pairs, and does it hold at 63 sessions?

Round 33's band (10 / 90 % walk-forward quantiles of range / (gauge x sqrt h)) covers 76-80 % on EUR/USD at 5 / 10 / 21.
Replication with the 21-session realised-vol gauge on GBP, JPY, AUD, CHF, CAD, NZD vs USD, plus EUR/USD itself with
that gauge, at 5 / 10 / 21 / 63 sessions. Bar: coverage 76-84 % for at least 5 of 6 pairs at 5 / 10 / 21 in 2010-26 and
2018-26; 63 sessions reported (adopted on EUR/USD only if 76-84 in both eras). Writes bots_travel_replication.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

PAIRS = ("eurusd_rv21", "gbpusd", "usdjpy", "audusd", "usdchf", "usdcad", "nzdusd"); rows = []
for pair in PAIRS:
    if pair == "eurusd_rv21":
        X = B.build(); hist = X["__src"] == "histdata"
        D = pd.DataFrame({"close": X["__close"], "high": X["__high"].where(hist), "low": X["__low"].where(hist)}, index=X.index)
    else:
        D = pd.read_parquet(ROOT / "data" / "processed" / f"reliable_parts_daily_{pair}.parquet")
    idx = D.index if D.index.tz is not None else D.index.tz_localize("UTC"); D.index = idx
    c, hi, lo = D["close"], D["high"], D["low"]; g = np.log(c).diff().rolling(21).std()
    for h in (5, 10, 21, 63):
        fmax = hi[::-1].rolling(h, min_periods=h).max()[::-1].shift(-1); fmin = lo[::-1].rolling(h, min_periods=h).min()[::-1].shift(-1)
        rng_ = np.log(fmax / fmin); s = g * np.sqrt(h); ratio = rng_ / s
        ct_end = pd.Series(idx, index=idx).shift(-h); ok = ratio.notna().values
        q10 = pd.Series(np.nan, index=idx); q90 = q10.copy()
        for Y in range(2010, 2027):
            ref = ok & (ct_end < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
            ry = idx.year == Y
            if ref.sum() >= 500 and ry.any():
                q10[ry], q90[ry] = np.quantile(ratio[ref], [0.1, 0.9])
        for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
            m = ok & q10.notna().values & (idx.year >= a) & (idx.year <= b)
            rows.append({"pair": pair, "h": h, "era": era, "n_indep": round(m.sum() / h, 1), "coverage": float(((ratio[m] >= q10[m]) & (ratio[m] <= q90[m])).mean()),
                         "below": float((ratio[m] < q10[m]).mean()), "above": float((ratio[m] > q90[m]).mean())})
    print(pair, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_travel_replication.csv", index=False)
pd.set_option("display.width", 200)
P = T.pivot_table(index=["pair", "h"], columns="era", values="coverage").mul(100).round(1); print(P.to_string())
S = T[T.pair != "eurusd_rv21"]
for era in ("2010-26", "2018-26"):
    s = S[(S.era == era) & (S.h < 63)]; okp = s.groupby("pair").coverage.apply(lambda x: ((x >= 0.76) & (x <= 0.84)).all())
    print(era, "pairs passing at 5/10/21:", int(okp.sum()), "/ 6", list(okp[~okp].index))
