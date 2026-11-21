"""Round 27 (declared before running): do the levels hold when the price sits at a recent extreme?

The levels are centred on the close with no direction. If the close is at a 63-session high, the upper level may be
breached more often (momentum) or less often (reversion). Declared question, 5 / 10 / 21 sessions: holding rate of
the lower and upper levels when the close is in the top decile of its 63-session range, in the bottom decile, and in
the middle, 2010-26 and 2018-26. A fix is warranted only if one side is off by more than 4 points in the same direction
in BOTH eras; a declared candidate is then tested in a later round. Writes bots_levels_extremes.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

X = B.build(); rows = []
c_all = X["__close"]; pos = (c_all - c_all.rolling(63).min()) / (c_all.rolling(63).max() - c_all.rolling(63).min())
for h in (5, 10, 21):
    _, LO, HI = B.walk_forward(X, h, verbose=False)
    idx = LO.index; c = c_all.reindex(idx)
    lo = np.log(LO.div(c, axis=0)); hi = np.log(HI.div(c, axis=0))
    k = 20; l = np.sort(lo.values, axis=1)[:, k:100 - k].mean(1); u = np.sort(hi.values, axis=1)[:, k:100 - k].mean(1)
    dn, up = X[f"dn{h}"].reindex(idx).values, X[f"up{h}"].reindex(idx).values
    p = pos.reindex(idx).values
    ok = np.isfinite(dn) & np.isfinite(l) & np.isfinite(p)
    for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
        base = ok & (idx.year >= a) & (idx.year <= b)
        for grp, m in (("at 63-session high (top decile)", base & (p >= 0.9)), ("middle", base & (p > 0.1) & (p < 0.9)), ("at 63-session low (bottom decile)", base & (p <= 0.1))):
            rows.append({"h": h, "era": era, "position": grp, "n_indep": round(m.sum() / h, 1), "lower_held": float((dn[m] >= l[m]).mean()), "upper_held": float((up[m] <= u[m]).mean())})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_levels_extremes.csv", index=False)
pd.set_option("display.width", 200); print(T.assign(lower_held=(100 * T.lower_held).round(1), upper_held=(100 * T.upper_held).round(1)).to_string(index=False))
