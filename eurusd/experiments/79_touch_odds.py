"""Round 20 (one trial, declared before running): a touch-odds table for ANY level, as a product feature.

The vote gives levels at fixed odds. A user also wants the reverse: the odds that a level of their choosing (a stop, a
target) is touched within h sessions. Method (fixed): distance of the level from the close in units of the median bot
gauge (the median across the 100 bots of each bot's gauge g, times sqrt(h)); the touch probability at each distance is
the walk-forward empirical frequency on sessions whose outcome was known before the test year, read off a grid of
distances 0.25 .. 3.0 (step 0.25), either side pooled. Bar: at 5, 10 and 21 sessions the realised touch frequency at
each grid distance is within 4 points of the stated one in 2010-26 and 2018-26 (Brier against the driftless-Brownian
formula reported as context). Writes bots_touch_odds.csv (the live table) and bots_touch_calibration.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import norm
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

GRID = np.round(np.arange(0.25, 3.01, 0.25), 2)
X = B.build()
g = pd.DataFrame({sp["bot"]: X[f"g_{sp['gauge']}"] for sp in B.SPECS}).median(axis=1)
cal, live = [], []
for h in (5, 10, 21):
    s = g * np.sqrt(h)
    dn, up, yend = -X[f"dn{h}"] / s, X[f"up{h}"] / s, X[f"yend{h}"]      # largest adverse move each side, in gauge units
    ok = (dn.notna() & up.notna()).values
    def touch_freq(m, d):
        return float(0.5 * ((dn[m] >= d).mean() + (up[m] >= d).mean()))
    stated = pd.DataFrame(np.nan, index=X.index, columns=GRID)
    for Y in range(2010, 2027):
        ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
        if ref.sum() >= 500:
            stated.loc[X.index.year == Y] = [touch_freq(ref, d) for d in GRID]
    for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026), ("2023-26", 2023, 2026)):
        m = ok & stated[GRID[0]].notna().values & (X.index.year >= a) & (X.index.year <= b)
        for d in GRID:
            real = touch_freq(m, d)
            st = float(stated.loc[m, d].mean())
            brown = float(2 * (1 - norm.cdf(d)))                          # driftless Brownian motion, same units
            cal.append({"h": h, "era": era, "distance": d, "stated": st, "realised": real, "gap": real - st, "brownian": brown, "n_indep": round(m.sum() / h, 1)})
    for d in GRID:
        live.append({"h": h, "distance": d, "p_touch": touch_freq(ok, d)})
    print(h, "done", flush=True)
C = pd.DataFrame(cal); L = pd.DataFrame(live)
C.to_csv(B.RES / "bots_touch_calibration.csv", index=False); L.to_csv(B.RES / "bots_touch_odds.csv", index=False)
pd.set_option("display.width", 200)
print(C[C.era != "2023-26"].assign(**{c: (100 * C[c]).round(1) for c in ("stated", "realised", "gap", "brownian")}).to_string(index=False))
print("max |gap| by h and era:\n", C.groupby(["h", "era"]).gap.apply(lambda x: 100 * x.abs().max()).round(1).to_string())
