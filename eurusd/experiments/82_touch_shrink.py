"""Round 23 (one trial, declared before running): shrink today's volatility towards its long-run level before scaling.

Round 22: touch odds scaled by today's gauge are too low in calm and too high in volatile markets. Candidate: scale by
g_eff = g^(1-w) * g_long^w, where g_long is the median gauge over the training window and w is ONE parameter chosen on
2010-2017 (grid 0.0 .. 0.6 step 0.1) to minimise the maximum absolute calibration gap across volatility terciles at
distances 0.5-2.0 and 5 / 10 / 21 sessions. Bar: with that w, in 2018-2026 the per-tercile gap of the pooled table is
within 3 points in every tercile at every horizon (the w = 0 table misses by up to 8). Writes bots_touch_shrink.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

GRID = np.round(np.arange(0.5, 2.01, 0.25), 2)
WS = np.round(np.arange(0.0, 0.61, 0.1), 1)
X = B.build()
g = pd.DataFrame({sp["bot"]: X[f"g_{sp['gauge']}"] for sp in B.SPECS}).median(axis=1)
v = X["g_rv21"]
rows = []
for h in (5, 10, 21):
    dn0, up0, yend = -X[f"dn{h}"], X[f"up{h}"], X[f"yend{h}"]
    ok = (dn0.notna() & up0.notna() & v.notna() & g.notna()).values
    for w in WS:
        geff = pd.Series(np.nan, index=X.index); terc = pd.Series(np.nan, index=X.index)
        stated = {d: pd.Series(np.nan, index=X.index) for d in GRID}
        for Y in range(2010, 2027):
            ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
            ry = X.index.year == Y
            if ref.sum() < 500:
                continue
            glong = float(np.median(g[ref]))
            ge = g ** (1 - w) * glong ** w
            s = ge * np.sqrt(h)
            dn, up = dn0 / s, up0 / s
            geff[ry] = ge[ry]
            q1, q2 = np.quantile(v[ref], [1 / 3, 2 / 3])
            t_all = np.where(v < q1, 0, np.where(v < q2, 1, 2)); terc[ry] = t_all[ry]
            for d in GRID:
                stated[d][ry] = float(0.5 * ((dn[ref] >= d).mean() + (up[ref] >= d).mean()))
        s = geff * np.sqrt(h); dn, up = dn0 / s, up0 / s
        for era, aa, bb in (("2010-17", 2010, 2017), ("2018-26", 2018, 2026)):
            base = ok & geff.notna().values & (X.index.year >= aa) & (X.index.year <= bb)
            for t, nm in enumerate(("calm", "normal", "volatile")):
                m = base & (terc == t).values
                for d in GRID:
                    rows.append({"h": h, "w": w, "era": era, "tercile": nm, "distance": d, "n_indep": round(m.sum() / h, 1),
                                 "realised": float(0.5 * ((dn[m] >= d).mean() + (up[m] >= d).mean())), "stated": float(stated[d][m].mean())})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T["gap"] = T.realised - T.stated
T.to_csv(B.RES / "bots_touch_shrink.csv", index=False)
M = (100 * T.groupby(["w", "era"]).gap.apply(lambda x: x.abs().max())).round(1).unstack()
print("max |gap| over terciles, distances, horizons:\n", M.to_string())
w_pick = float(M["2010-17"].idxmin()); print("\nPICK on 2010-17: w =", w_pick, "| 2018-26 max gap:", M.loc[w_pick, "2018-26"])
P = T[(T.w == w_pick) & (T.era == "2018-26")]
print((100 * P.groupby(["h", "tercile"]).gap.apply(lambda x: x.abs().max())).round(1).unstack().to_string())
