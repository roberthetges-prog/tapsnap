"""Round 19 (one trial, declared before running): the bots' levels at two more horizons, 10 and 42 sessions.

The product gives levels for 5, 21 and 63 sessions. Users may want two weeks and two months. Same bots, same method,
nothing re-tuned. Bar: each level (lower, upper) holds within 4 points of 80 % at both horizons in 2010-26, 2016-26 and
2023-26; the wide band (round-14 factor rule) within 4 points of 80 %. Writes bots_levels_10_42.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

GRID = np.round(np.arange(1.0, 2.501, 0.01), 2)
X = B.build()
lc = np.log(X["__close"]); ct = X["__ct"]; hist = X["__src"] == "histdata"
hi, lo = X["__high"].where(hist), X["__low"].where(hist)
for h in (10, 42):
    X[f"y{h}"] = np.sign(lc.shift(-h) - lc); X[f"yend{h}"] = ct.shift(-h)
    X[f"dn{h}"] = np.log(lo[::-1].rolling(h, min_periods=h).min()[::-1].shift(-1) / X["__close"])
    X[f"up{h}"] = np.log(hi[::-1].rolling(h, min_periods=h).max()[::-1].shift(-1) / X["__close"])
rows = []
for h in (10, 42):
    _, LO, HI = B.walk_forward(X, h, verbose=False)
    idx = LO.index; c = X["__close"].reindex(idx)
    lo_, hi_ = np.log(LO.median(axis=1) / c), np.log(HI.median(axis=1) / c)
    dn, up, yend = X[f"dn{h}"].reindex(idx), X[f"up{h}"].reindex(idx), X[f"yend{h}"].reindex(idx)
    ok = (lo_.notna() & dn.notna()).values
    def k_for(m):
        for k in GRID:
            if ((dn[m] >= k * lo_[m]) & (up[m] <= k * hi_[m])).mean() >= 0.80:
                return float(k)
        return float(GRID[-1])
    ks = pd.Series(np.nan, index=idx)
    for Y in range(2010, 2027):
        ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
        if ref.sum() >= 500:
            ks[idx.year == Y] = k_for(ref)
    for era, a, b in B.ERAS:
        m = ok & ks.notna().values & (idx.year >= a) & (idx.year <= b)
        rows.append({"h": h, "era": era, "n_indep": round(m.sum() / h, 1), "lower_held": float((dn[m] >= lo_[m]).mean()), "upper_held": float((up[m] <= hi_[m]).mean()),
                     "both_held": float(((dn[m] >= lo_[m]) & (up[m] <= hi_[m])).mean()), "band_held": float(((dn[m] >= ks[m] * lo_[m]) & (up[m] <= ks[m] * hi_[m])).mean()),
                     "avg_width_pct": 100 * float((hi_[m] - lo_[m]).mean()), "band_factor": float(ks[m].mean())})
    rows.append({"h": h, "era": "live", "band_factor": k_for(ok)})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_levels_10_42.csv", index=False)
pd.set_option("display.width", 200); print(T.round(3).to_string(index=False))
