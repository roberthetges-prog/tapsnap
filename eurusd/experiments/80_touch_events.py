"""Round 21 (one trial, declared before running): do the touch odds need an event-week adjustment?

Round 20's touch table pools all sessions. Round 11 found one-week LEVELS hold 2-8 points less in weeks with a scheduled
FOMC / ECB / payrolls / CPI. Declared question, 5 and 10 sessions: realised touch frequency in event windows vs other
windows at each grid distance against the pooled stated odds. Candidate (one): separate tables for the two groups.
Adopt only if (a) the pooled table is off by more than 3 points in either group at any distance of 0.5-2.0 units in
2010-26 AND (b) the split tables are within 3 points in both groups in 2010-26 and 2018-26. Writes bots_touch_events.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B
from eurusd.arms import sharper_levels as SL

GRID = np.round(np.arange(0.25, 3.01, 0.25), 2)
X = B.build()
g = pd.DataFrame({sp["bot"]: X[f"g_{sp['gauge']}"] for sp in B.SPECS}).median(axis=1)
ev = SL.event_times()
a = pd.DatetimeIndex(X["__ct"]).as_unit("ns").asi8
rows = []
for h in (5, 10):
    b = pd.DatetimeIndex(X["__ct"] + pd.offsets.BDay(h)).as_unit("ns").asi8
    evw = np.zeros(len(X), bool)
    for k in ("fomc", "ecb", "nfp", "cpi"):
        evw |= SL._count_in(ev[k], a, b) > 0
    s = g * np.sqrt(h)
    dn, up, yend = -X[f"dn{h}"] / s, X[f"up{h}"] / s, X[f"yend{h}"]
    ok = (dn.notna() & up.notna()).values
    tf = lambda m, d: float(0.5 * ((dn[m] >= d).mean() + (up[m] >= d).mean()))  # noqa: E731
    pooled = {d: pd.Series(np.nan, index=X.index) for d in GRID}; split = {d: pd.Series(np.nan, index=X.index) for d in GRID}
    for Y in range(2010, 2027):
        ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
        ry = X.index.year == Y
        if ref.sum() < 500:
            continue
        for d in GRID:
            pooled[d][ry] = tf(ref, d)
            split[d][ry & evw] = tf(ref & evw, d); split[d][ry & ~evw] = tf(ref & ~evw, d)
    for era, aa, bb in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
        base = ok & pooled[GRID[0]].notna().values & (X.index.year >= aa) & (X.index.year <= bb)
        for grp, m in (("event window", base & evw), ("no event", base & ~evw)):
            for d in GRID:
                rows.append({"h": h, "era": era, "group": grp, "distance": d, "n_indep": round(m.sum() / h, 1), "realised": tf(m, d),
                             "stated_pooled": float(pooled[d][m].mean()), "stated_split": float(split[d][m].mean())})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T["gap_pooled"] = T.realised - T.stated_pooled; T["gap_split"] = T.realised - T.stated_split
T.to_csv(B.RES / "bots_touch_events.csv", index=False)
pd.set_option("display.width", 220)
S = T[T.distance.between(0.5, 2.0)]
print(S.assign(**{c: (100 * S[c]).round(1) for c in ("realised", "stated_pooled", "stated_split", "gap_pooled", "gap_split")}).to_string(index=False))
print("\nmax |gap| pooled / split by h, era, group:\n", (100 * S.groupby(["h", "era", "group"])[["gap_pooled", "gap_split"]].apply(lambda x: x.abs().max())).round(1).to_string())

# live tables (declared outcome: adopted at 5 sessions only, where both groups are within 1.2 points)
live = []
h = 5
b5 = pd.DatetimeIndex(X["__ct"] + pd.offsets.BDay(5)).as_unit("ns").asi8
evw5 = np.zeros(len(X), bool)
for k in ("fomc", "ecb", "nfp", "cpi"):
    evw5 |= SL._count_in(ev[k], a, b5) > 0
s5 = g * np.sqrt(5)
dn5, up5 = -X["dn5"] / s5, X["up5"] / s5
ok5 = (dn5.notna() & up5.notna()).values
for grp, m in (("event window", ok5 & evw5), ("no event", ok5 & ~evw5)):
    for d in GRID:
        live.append({"h": 5, "group": grp, "distance": d, "p_touch": float(0.5 * ((dn5[m] >= d).mean() + (up5[m] >= d).mean()))})
pd.DataFrame(live).to_csv(B.RES / "bots_touch_odds_events.csv", index=False)
print("live event tables written")
