"""Round 30 (declared before running): does the touch-odds table replicate on six other dollar pairs?

Round 20's table (touch frequency by distance in gauge units, walk-forward) is calibrated within 1 point on EUR/USD.
Replication, nothing re-tuned: on GBP, JPY, AUD, CHF, CAD, NZD against the dollar, gauge = 21-session realised
volatility of daily log returns (the EUR/USD table uses the median bot gauge; rv21 is one of them), each pair's own
walk-forward table, distances 0.5-2.5 units, 5 / 10 / 21 sessions. Bar: realised within 3 points of stated at every
distance for at least 5 of 6 pairs in 2010-26 and in 2018-26. Also: the EUR/USD table applied FROZEN to each pair.
Writes bots_touch_replication.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

GRID = np.round(np.arange(0.5, 2.51, 0.25), 2)
PAIRS = ("gbpusd", "usdjpy", "audusd", "usdchf", "usdcad", "nzdusd")
rows = []
def table(dn, up, ok, idx, ct_end, h):
    stated = {d: pd.Series(np.nan, index=idx) for d in GRID}
    for Y in range(2010, 2027):
        ref = ok & (ct_end < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
        ry = idx.year == Y
        if ref.sum() >= 500:
            for d in GRID:
                stated[d][ry] = float(0.5 * ((dn[ref] >= d).mean() + (up[ref] >= d).mean()))
    return stated
eur = pd.read_csv(B.RES / "bots_touch_odds.csv")
for pair in PAIRS:
    D = pd.read_parquet(ROOT / "data" / "processed" / f"reliable_parts_daily_{pair}.parquet")
    idx = D.index if D.index.tz is not None else D.index.tz_localize("UTC")
    D.index = idx
    c, hi, lo = D["close"], D["high"], D["low"]
    r = np.log(c).diff(); g = r.rolling(21).std()
    for h in (5, 10, 21):
        fmin = lo[::-1].rolling(h, min_periods=h).min()[::-1].shift(-1); fmax = hi[::-1].rolling(h, min_periods=h).max()[::-1].shift(-1)
        s = g * np.sqrt(h)
        dn = -np.log(fmin / c) / s; up = np.log(fmax / c) / s
        ct_end = pd.Series(idx, index=idx).shift(-h)
        ok = (dn.notna() & up.notna()).values
        st = table(dn, up, ok, idx, ct_end, h)
        te = eur[eur.h == h].sort_values("distance")
        for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
            m = ok & st[GRID[0]].notna().values & (idx.year >= a) & (idx.year <= b)
            for d in GRID:
                real = float(0.5 * ((dn[m] >= d).mean() + (up[m] >= d).mean()))
                rows.append({"pair": pair, "h": h, "era": era, "distance": d, "n_indep": round(m.sum() / h, 1), "realised": real, "stated_own": float(st[d][m].mean()),
                             "stated_eur_frozen": float(np.interp(d, te.distance, te.p_touch))})
    print(pair, "done", flush=True)
T = pd.DataFrame(rows); T["gap_own"] = T.realised - T.stated_own; T["gap_eur"] = T.realised - T.stated_eur_frozen
T.to_csv(B.RES / "bots_touch_replication.csv", index=False)
M = (100 * T.groupby(["pair", "era"])[["gap_own", "gap_eur"]].apply(lambda x: x.abs().max())).round(1)
pd.set_option("display.width", 200); print(M.to_string())
for era in ("2010-26", "2018-26"):
    print(era, "pairs within 3 (own table):", int((M.xs(era, level="era").gap_own <= 3).sum()), "/ 6 ; (frozen EUR table):", int((M.xs(era, level="era").gap_eur <= 3).sum()), "/ 6")
