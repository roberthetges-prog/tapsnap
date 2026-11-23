"""Round 35 (declared before running): do the 90 % and 95 % bands replicate on six dollar pairs?

Round 16's bands (single-gauge levels stretched by a walk-forward factor for 90 / 95 % joint holding) are published for
5 and 21 sessions on EUR/USD (not 63). Replication with the 21-session realised-vol gauge on GBP, JPY, AUD, CHF, CAD,
NZD vs USD at 5 / 10 / 21 sessions. Bar: joint holding within 3 points of the target for at least 5 of 6 pairs at every
horizon in 2010-26 and 2018-26. Writes bots_band_confidence_replication.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

GRID = np.round(np.arange(1.0, 4.001, 0.01), 2); PAIRS = ("gbpusd", "usdjpy", "audusd", "usdchf", "usdcad", "nzdusd"); rows = []
for pair in PAIRS:
    D = pd.read_parquet(ROOT / "data" / "processed" / f"reliable_parts_daily_{pair}.parquet")
    idx = D.index if D.index.tz is not None else D.index.tz_localize("UTC"); D.index = idx
    c, hi, lo = D["close"], D["high"], D["low"]; g = np.log(c).diff().rolling(21).std()
    for h in (5, 10, 21):
        fmin = lo[::-1].rolling(h, min_periods=h).min()[::-1].shift(-1); fmax = hi[::-1].rolling(h, min_periods=h).max()[::-1].shift(-1)
        s = g * np.sqrt(h); dn = np.log(fmin / c) / s; up = np.log(fmax / c) / s
        ct_end = pd.Series(idx, index=idx).shift(-h); ok = (dn.notna() & up.notna()).values
        for t in (0.90, 0.95):
            ql = pd.Series(np.nan, index=idx); qu = ql.copy(); kf = ql.copy()
            for Y in range(2010, 2027):
                ref = ok & (ct_end < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values; ry = idx.year == Y
                if ref.sum() < 500 or not ry.any():
                    continue
                a_, b_ = np.quantile(dn[ref], 0.2), np.quantile(up[ref], 0.8); ql[ry], qu[ry] = a_, b_
                kf[ry] = next((float(k) for k in GRID if ((dn[ref] >= k * a_) & (up[ref] <= k * b_)).mean() >= t), float(GRID[-1]))
            for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
                m = ok & ql.notna().values & (idx.year >= a) & (idx.year <= b)
                rows.append({"pair": pair, "h": h, "target": t, "era": era, "n_indep": round(m.sum() / h, 1), "both_held": float(((dn[m] >= kf[m] * ql[m]) & (up[m] <= kf[m] * qu[m])).mean()), "factor": float(kf[m].mean())})
    print(pair, "done", flush=True)
T = pd.DataFrame(rows); T["gap"] = T.both_held - T.target; T.to_csv(B.RES / "bots_band_confidence_replication.csv", index=False)
pd.set_option("display.width", 200)
print(T.pivot_table(index=["pair", "h"], columns=["target", "era"], values="both_held").mul(100).round(1).to_string())
for era in ("2010-26", "2018-26"):
    s = T[T.era == era]; okp = s.groupby("pair").gap.apply(lambda x: (x.abs() <= 0.03).all()); print(era, "pairs passing:", int(okp.sum()), "/ 6", list(okp[~okp].index))
