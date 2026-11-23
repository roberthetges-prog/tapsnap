"""Round 32 (declared before running): do the one-week levels depend on which weekday the window starts?

A 5-session window starting on a Friday close meets the weekend gap first; one starting on a Monday close meets it at
the end. Declared question: holding rate of the lower / upper level and the wide band by weekday of the session close,
5 sessions, 2010-26 and 2018-26. A fix is warranted only if a weekday is off by more than 4 points in both eras.
Writes bots_levels_weekday.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

X = B.build(); rows = []
h = 5
_, LO, HI = B.walk_forward(X, h, verbose=False)
idx = LO.index; c = X["__close"].reindex(idx)
lo = np.log(LO.div(c, axis=0)); hi = np.log(HI.div(c, axis=0)); k20 = 20
l = np.sort(lo.values, axis=1)[:, k20:100 - k20].mean(1); u = np.sort(hi.values, axis=1)[:, k20:100 - k20].mean(1)
dn, up = X["dn5"].reindex(idx).values, X["up5"].reindex(idx).values
jb = pd.read_csv(B.RES / "bots_joint_band.csv"); kf = float(jb[(jb.h == 5) & (jb.era == "live")]["avg_factor"].iloc[0])
wd = pd.DatetimeIndex(X["__ct"].reindex(idx)).dayofweek
ok = np.isfinite(dn) & np.isfinite(l)
for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
    base = ok & (idx.year >= a) & (idx.year <= b)
    for d, nm in enumerate(("Mon", "Tue", "Wed", "Thu", "Fri")):
        m = base & (wd == d)
        rows.append({"era": era, "close_weekday": nm, "n_indep": round(m.sum() / h, 1), "lower_held": float((dn[m] >= l[m]).mean()), "upper_held": float((up[m] <= u[m]).mean()),
                     "band_held": float(((dn[m] >= kf * l[m]) & (up[m] <= kf * u[m])).mean())})
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_levels_weekday.csv", index=False)
print(T.assign(**{c_: (100 * T[c_]).round(1) for c_ in ("lower_held", "upper_held", "band_held")}).to_string(index=False))
