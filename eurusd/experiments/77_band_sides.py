"""Round 18 (one trial, declared before running): is the wide band breached evenly on both sides?

The round-14 band stretches both of the bots' levels by one factor. If breaches come mostly from one side, the band is
mis-placed. Declared question: share of breaches below vs above, 2010-26 and 2018-26, at 5 / 21 / 63 sessions.
Candidate (one): a separate walk-forward factor per side, each chosen so that its side is breached at most 10 % of the
time in the training window (joint target still about 80 %). Bar: in 2010-26 and 2018-26 the two sides' breach rates
are within 2 points of each other at every horizon, the joint holding rate stays within 4 points of 80 %, and the
average width is not more than 2 % wider than the single-factor band. Writes bots_band_sides.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

GRID = np.round(np.arange(1.0, 3.001, 0.01), 2)
X = B.build()
rows = []
for h in B.HORIZONS:
    _, LO, HI = B.walk_forward(X, h, verbose=False)
    idx = LO.index
    c = X["__close"].reindex(idx)
    lo, hi = np.log(LO.median(axis=1) / c), np.log(HI.median(axis=1) / c)
    dn, up, yend = X[f"dn{h}"].reindex(idx), X[f"up{h}"].reindex(idx), X[f"yend{h}"].reindex(idx)
    ok = (lo.notna() & dn.notna()).values
    def k_joint(m):
        for k in GRID:
            if ((dn[m] >= k * lo[m]) & (up[m] <= k * hi[m])).mean() >= 0.80:
                return float(k)
        return float(GRID[-1])
    def k_side(m, side):
        for k in GRID:
            r = (dn[m] < k * lo[m]).mean() if side == "lo" else (up[m] > k * hi[m]).mean()
            if r <= 0.10:
                return float(k)
        return float(GRID[-1])
    k1 = pd.Series(np.nan, index=idx); kl = k1.copy(); ku = k1.copy()
    for Y in range(2010, 2027):
        ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
        rows_y = idx.year == Y
        if ref.sum() >= 500:
            k1[rows_y] = k_joint(ref); kl[rows_y] = k_side(ref, "lo"); ku[rows_y] = k_side(ref, "hi")
    for name, a_l, a_u in (("single factor", k1, k1), ("factor per side", kl, ku)):
        bl, bu = dn < a_l * lo, up > a_u * hi
        for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026), ("2023-26", 2023, 2026)):
            m = ok & a_l.notna().values & (idx.year >= a) & (idx.year <= b)
            rows.append({"h": h, "band": name, "era": era, "n_indep": round(m.sum() / h, 1), "both_held": float((~bl[m] & ~bu[m]).mean()),
                         "breached_below": float(bl[m].mean()), "breached_above": float(bu[m].mean()),
                         "avg_width_pct": 100 * float((a_u[m] * hi[m] - a_l[m] * lo[m]).mean())})
    rows.append({"h": h, "band": "live factors", "era": "live", "n_indep": np.nan, "both_held": np.nan, "breached_below": k_side(ok, "lo"), "breached_above": k_side(ok, "hi"), "avg_width_pct": k_joint(ok)})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_band_sides.csv", index=False)
pd.set_option("display.width", 200); print(T.round(3).to_string(index=False))
