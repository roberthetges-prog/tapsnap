"""Round 24 (one trial, declared before running): which volatility gauge makes the touch odds state-free?

Rounds 22-23: scaling by the median bot gauge over-reacts to today's volatility. Candidate: a single gauge per horizon
chosen from {rv10, rv21, rv63, ewma, blend, atr14} on 2010-2017 by the smallest maximum per-tercile calibration gap
(distances 0.5-2.0). Bar: in 2018-2026 the chosen gauge's gap is within 3 points in every tercile at that horizon.
Writes bots_touch_gauge.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

GRID = np.round(np.arange(0.5, 2.01, 0.25), 2)
X = B.build()
v = X["g_rv21"]
rows = []
for h in (5, 10, 21):
    dn0, up0, yend = -X[f"dn{h}"], X[f"up{h}"], X[f"yend{h}"]
    for gname in B.GAUGES:
        g = X[f"g_{gname}"]
        ok = (dn0.notna() & up0.notna() & v.notna() & g.notna()).values
        s = g * np.sqrt(h); dn, up = dn0 / s, up0 / s
        terc = pd.Series(np.nan, index=X.index); stated = {d: pd.Series(np.nan, index=X.index) for d in GRID}
        for Y in range(2010, 2027):
            ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
            ry = X.index.year == Y
            if ref.sum() < 500:
                continue
            q1, q2 = np.quantile(v[ref], [1 / 3, 2 / 3])
            t_all = np.where(v < q1, 0, np.where(v < q2, 1, 2)); terc[ry] = t_all[ry]
            for d in GRID:
                stated[d][ry] = float(0.5 * ((dn[ref] >= d).mean() + (up[ref] >= d).mean()))
        for era, aa, bb in (("2010-17", 2010, 2017), ("2018-26", 2018, 2026)):
            base = ok & stated[GRID[0]].notna().values & (X.index.year >= aa) & (X.index.year <= bb)
            for t, nm in enumerate(("calm", "normal", "volatile")):
                m = base & (terc == t).values
                for d in GRID:
                    rows.append({"h": h, "gauge": gname, "era": era, "tercile": nm, "distance": d, "n_indep": round(m.sum() / h, 1),
                                 "realised": float(0.5 * ((dn[m] >= d).mean() + (up[m] >= d).mean())), "stated": float(stated[d][m].mean())})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T["gap"] = T.realised - T.stated
T.to_csv(B.RES / "bots_touch_gauge.csv", index=False)
M = (100 * T.groupby(["h", "gauge", "era"]).gap.apply(lambda x: x.abs().max())).round(1).unstack()
print(M.to_string())
for h in (5, 10, 21):
    pick = M.loc[h]["2010-17"].idxmin(); print(f"h={h}: pick {pick} (2010-17 {M.loc[(h, pick), '2010-17']}) -> 2018-26 max gap {M.loc[(h, pick), '2018-26']}")
