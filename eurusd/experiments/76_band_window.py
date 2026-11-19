"""Round 17 (one trial, declared before running): a 10-year window for the band factor, to fix the 63-session bands.

Round 16: the 90 / 95 % bands over-hold at 63 sessions (91.7 / 97.3 % in 2010-26, 93.9 / 99.0 % in 2018-26) because the
expanding training window keeps 2008-12. Candidate: the factor chosen on the last 10 years of known outcomes instead of
all of them (everything else as rounds 14 and 16). Bar: at 63 sessions every target (80 / 90 / 95) within 3 points in
2010-26 and 2018-26, and 5 / 21 sessions still within 3. Writes bots_band_window.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

GRID = np.round(np.arange(1.0, 4.001, 0.01), 2)
TARGETS = (0.80, 0.90, 0.95)
X = B.build()
rows = []
for h in B.HORIZONS:
    _, LO, HI = B.walk_forward(X, h, verbose=False)
    idx = LO.index
    c = X["__close"].reindex(idx)
    lo, hi = np.log(LO.median(axis=1) / c), np.log(HI.median(axis=1) / c)
    dn, up, yend = X[f"dn{h}"].reindex(idx), X[f"up{h}"].reindex(idx), X[f"yend{h}"].reindex(idx)
    ct = X["__ct"].reindex(idx)
    ok = (lo.notna() & dn.notna()).values
    def k_for(m, t):
        for k in GRID:
            if ((dn[m] >= k * lo[m]) & (up[m] <= k * hi[m])).mean() >= t:
                return float(k)
        return float(GRID[-1])
    for t in TARGETS:
        ks = pd.Series(np.nan, index=idx)
        for Y in range(2010, 2027):
            start = pd.Timestamp(f"{Y}-01-01", tz="UTC")
            ref = ok & (yend < start).values & (ct >= start - pd.DateOffset(years=10)).values
            if ref.sum() >= 500:
                ks[idx.year == Y] = k_for(ref, t)
        both = (dn >= ks * lo) & (up <= ks * hi)
        for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026), ("2023-26", 2023, 2026)):
            m = ok & ks.notna().values & (idx.year >= a) & (idx.year <= b)
            rows.append({"h": h, "target": t, "era": era, "n_indep": round(m.sum() / h, 1), "both_held": float(both[m].mean()),
                         "worst_year": float(both[m].groupby(idx[m].year).mean().min()), "avg_factor": float(ks[m].mean()),
                         "avg_width_pct": 100 * float((ks[m] * (hi[m] - lo[m])).mean())})
        last = ok & (ct >= ct.iloc[-1] - pd.DateOffset(years=10)).values
        rows.append({"h": h, "target": t, "era": "live", "n_indep": np.nan, "both_held": np.nan, "worst_year": np.nan, "avg_factor": k_for(last, t), "avg_width_pct": np.nan})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_band_window.csv", index=False)
pd.set_option("display.width", 200); print(T[T.era != "live"].round(3).to_string(index=False)); print(T[T.era == "live"][["h", "target", "avg_factor"]].to_string(index=False))
