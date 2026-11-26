"""Round 36 (declared before running): do the levels hold evenly across calendar months?

Thin December markets, summer lulls and quarter-ends could make the levels hold more or less often. Declared question:
holding rate of the lower / upper level and the wide band by calendar month of the window start, 5 and 21 sessions,
2010-26 and 2018-26. A fix is warranted only if a month is off by more than 5 points in the same direction in both eras
(months have about 70 / 17 independent periods each at 5 / 21 sessions). Writes bots_levels_by_month.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

X = B.build(); rows = []
jb = pd.read_csv(B.RES / "bots_joint_band.csv")
for h in (5, 21):
    _, LO, HI = B.walk_forward(X, h, verbose=False)
    idx = LO.index; c = X["__close"].reindex(idx)
    lo = np.log(LO.div(c, axis=0)); hi = np.log(HI.div(c, axis=0)); k20 = 20
    l = np.sort(lo.values, axis=1)[:, k20:100 - k20].mean(1); u = np.sort(hi.values, axis=1)[:, k20:100 - k20].mean(1)
    dn, up = X[f"dn{h}"].reindex(idx).values, X[f"up{h}"].reindex(idx).values
    kf = float(jb[(jb.h == h) & (jb.era == "live")]["avg_factor"].iloc[0])
    mon = pd.DatetimeIndex(X["__ct"].reindex(idx)).month
    ok = np.isfinite(dn) & np.isfinite(l)
    for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
        base = ok & (idx.year >= a) & (idx.year <= b)
        for m_ in range(1, 13):
            m = base & (mon == m_)
            rows.append({"h": h, "era": era, "month": m_, "n_indep": round(m.sum() / h, 1), "lower_held": float((dn[m] >= l[m]).mean()), "upper_held": float((up[m] <= u[m]).mean()),
                         "band_held": float(((dn[m] >= kf * l[m]) & (up[m] <= kf * u[m])).mean())})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_levels_by_month.csv", index=False)
pd.set_option("display.width", 200)
P = T.pivot_table(index=["h", "month"], columns="era", values=["lower_held", "upper_held", "band_held"]).mul(100).round(1); print(P.to_string())
