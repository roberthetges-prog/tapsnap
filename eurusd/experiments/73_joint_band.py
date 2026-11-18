"""Round 14 (one trial, declared here before running): a WIDE BAND that both sides hold together 8 times in 10.

The published lower / upper levels each hold about 80 %, but both together only about 60 %. A user who wants one range
that contains the whole period's price action 8 times in 10 needs wider levels. Method (fixed): stretch both of the
bots' median levels away from the price by one factor k. For test year Y, k is the smallest factor (grid 1.00 .. 2.50,
step 0.01) for which both levels held together at least 80 % of the time on the walk-forward levels of earlier years
whose outcome was known before Y-01-01. Test: joint holding rate 2010-26, 2016-26, 2023-26 within 4 points of 80 % at
5, 21 and 63 sessions. Writes experiments/results/arms/bots_joint_band.csv (record and the factor to use live).
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

GRID = np.round(np.arange(1.0, 2.501, 0.01), 2)
X = B.build()
rows = []
for h in B.HORIZONS:
    _, LO, HI = B.walk_forward(X, h, verbose=False)
    c = X["__close"].reindex(LO.index)
    lo, hi = np.log(LO.median(axis=1) / c), np.log(HI.median(axis=1) / c)
    dn, up, yend = X[f"dn{h}"].reindex(LO.index), X[f"up{h}"].reindex(LO.index), X[f"yend{h}"].reindex(LO.index)
    ok = lo.notna() & dn.notna()
    def k_for(mask):
        for k in GRID:
            if ((dn[mask] >= k * lo[mask]) & (up[mask] <= k * hi[mask])).mean() >= 0.80:
                return float(k)
        return float(GRID[-1])
    kser = pd.Series(np.nan, index=LO.index)
    for Y in range(2010, 2027):
        ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC"))
        if ref.sum() >= 500:
            kser[LO.index.year == Y] = k_for(ref)
    both = (dn >= kser * lo) & (up <= kser * hi)
    for era, a, b in B.ERAS:
        m = ok & kser.notna() & (LO.index.year >= a) & (LO.index.year <= b)
        rows.append({"h": h, "era": era, "n_indep": round(m.sum() / h, 1), "both_held": float(both[m].mean()), "avg_factor": float(kser[m].mean()),
                     "avg_width_pct": 100 * float((kser[m] * (hi[m] - lo[m])).mean()), "plain_both_held": float(((dn[m] >= lo[m]) & (up[m] <= hi[m])).mean())})
    rows.append({"h": h, "era": "live", "n_indep": np.nan, "both_held": np.nan, "avg_factor": k_for(ok), "avg_width_pct": np.nan, "plain_both_held": np.nan})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_joint_band.csv", index=False)
print(T.round(3).to_string(index=False))
