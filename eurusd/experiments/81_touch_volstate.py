"""Round 22 (one trial, declared before running): are the touch odds even across volatility states?

The touch table scales distance by today's volatility gauge, which should make it state-free; the levels (round 11)
were not. Declared question, 5 / 10 / 21 sessions: realised touch frequency by tercile of the 21-session realised
volatility (terciles from the training window) against the pooled stated odds at distances 0.5-2.0. Candidate (one):
a table per tercile. Adopt only if the pooled table is off by more than 3 points in some tercile at some distance in
BOTH 2010-26 and 2018-26, and the per-tercile tables are within 3 in every tercile in both eras. Writes
bots_touch_volstate.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

GRID = np.round(np.arange(0.5, 2.01, 0.25), 2)
X = B.build()
g = pd.DataFrame({sp["bot"]: X[f"g_{sp['gauge']}"] for sp in B.SPECS}).median(axis=1)
v = X["g_rv21"]
rows = []
for h in (5, 10, 21):
    s = g * np.sqrt(h)
    dn, up, yend = -X[f"dn{h}"] / s, X[f"up{h}"] / s, X[f"yend{h}"]
    ok = (dn.notna() & up.notna() & v.notna()).values
    tf = lambda m, d: float(0.5 * ((dn[m] >= d).mean() + (up[m] >= d).mean()))  # noqa: E731
    pooled = {d: pd.Series(np.nan, index=X.index) for d in GRID}; split = {d: pd.Series(np.nan, index=X.index) for d in GRID}
    terc = pd.Series(np.nan, index=X.index)
    for Y in range(2010, 2027):
        ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
        ry = X.index.year == Y
        if ref.sum() < 500:
            continue
        q1, q2 = np.quantile(v[ref], [1 / 3, 2 / 3])
        t_all = np.where(v < q1, 0, np.where(v < q2, 1, 2))
        terc[ry] = t_all[ry]
        for d in GRID:
            pooled[d][ry] = tf(ref, d)
            for t in range(3):
                split[d][ry & (t_all == t)] = tf(ref & (t_all == t), d)
    for era, aa, bb in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
        base = ok & pooled[GRID[0]].notna().values & (X.index.year >= aa) & (X.index.year <= bb)
        for t, nm in enumerate(("calm", "normal", "volatile")):
            m = base & (terc == t).values
            for d in GRID:
                rows.append({"h": h, "era": era, "tercile": nm, "distance": d, "n_indep": round(m.sum() / h, 1), "realised": tf(m, d),
                             "stated_pooled": float(pooled[d][m].mean()), "stated_split": float(split[d][m].mean())})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T["gap_pooled"] = T.realised - T.stated_pooled; T["gap_split"] = T.realised - T.stated_split
T.to_csv(B.RES / "bots_touch_volstate.csv", index=False)
pd.set_option("display.width", 220)
print((100 * T.groupby(["h", "era", "tercile"])[["gap_pooled", "gap_split"]].apply(lambda x: x.abs().max())).round(1).to_string())
print(T[(T.distance == 1.0)].assign(**{c: (100 * T[c]).round(1) for c in ("realised", "stated_pooled", "stated_split")})[["h", "era", "tercile", "n_indep", "realised", "stated_pooled", "stated_split"]].to_string(index=False))
