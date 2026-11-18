"""Round 15 (one trial, declared here before running): does the WIDE BAND hold evenly, and can one tested tweak make it so?

Round 14's band (bots' levels stretched by one walk-forward factor) holds 80 % overall. Declared question: its joint
holding rate by volatility tercile (21-session realised vol, terciles of the training window) and in weeks with a
scheduled FOMC / ECB / payrolls / CPI inside a 5-session window. Candidate (one): the factor chosen PER TERCILE of
today's volatility, same walk-forward rule. Bar: the per-tercile band's joint holding rate is within 4 points of 80 %
in every tercile at 5 and 21 sessions in 2010-26 and 2018-26, with the spread across terciles smaller than the
single-factor band's. Writes experiments/results/arms/bots_even_band.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B
from eurusd.arms import sharper_levels as SL

GRID = np.round(np.arange(1.0, 2.501, 0.01), 2)
X = B.build()
ev = SL.event_times()
rows = []
for h in B.HORIZONS:
    _, LO, HI = B.walk_forward(X, h, verbose=False)
    idx = LO.index
    c = X["__close"].reindex(idx)
    lo, hi = np.log(LO.median(axis=1) / c), np.log(HI.median(axis=1) / c)
    dn, up, yend = X[f"dn{h}"].reindex(idx), X[f"up{h}"].reindex(idx), X[f"yend{h}"].reindex(idx)
    g = X["g_rv21"].reindex(idx)
    ct = pd.DatetimeIndex(X["__ct"].reindex(idx)).as_unit("ns").asi8
    end5 = pd.DatetimeIndex(X["__ct"].reindex(idx) + pd.offsets.BDay(5)).as_unit("ns").asi8
    evw = np.zeros(len(idx), bool)
    for k in ("fomc", "ecb", "nfp", "cpi"):
        evw |= SL._count_in(ev[k], ct, end5) > 0
    ok = (lo.notna() & dn.notna() & g.notna()).values
    held = lambda k, m: ((dn[m] >= k * lo[m]) & (up[m] <= k * hi[m])).mean()  # noqa: E731
    def k_for(m):
        for k in GRID:
            if held(k, m) >= 0.80:
                return float(k)
        return float(GRID[-1])
    k1 = pd.Series(np.nan, index=idx); k3 = pd.Series(np.nan, index=idx); terc = pd.Series(np.nan, index=idx)
    for Y in range(2010, 2027):
        ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
        rows_y = (idx.year == Y)
        if ref.sum() < 500 or not rows_y.any():
            continue
        q1, q2 = np.quantile(g[ref], [1 / 3, 2 / 3])
        t_all = np.where(g < q1, 0, np.where(g < q2, 1, 2))
        terc[rows_y] = t_all[rows_y]
        k1[rows_y] = k_for(ref)
        for t in range(3):
            k3[rows_y & (t_all == t)] = k_for(ref & (t_all == t))
    for name, k in (("single factor", k1), ("factor per tercile", k3)):
        both = (dn >= k * lo) & (up <= k * hi)
        for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026), ("2023-26", 2023, 2026)):
            m = ok & k.notna().values & (idx.year >= a) & (idx.year <= b)
            r = {"h": h, "band": name, "era": era, "n_indep": round(m.sum() / h, 1), "all": float(both[m].mean())}
            for t, nm in enumerate(("calm", "normal", "volatile")):
                mm = m & (terc == t).values
                r[nm] = float(both[mm].mean())
            r["spread"] = max(r["calm"], r["normal"], r["volatile"]) - min(r["calm"], r["normal"], r["volatile"])
            r["event_week"] = float(both[m & evw].mean()); r["other_weeks"] = float(both[m & ~evw].mean())
            r["avg_width_pct"] = 100 * float((k[m] * (hi[m] - lo[m])).mean())
            rows.append(r)
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_even_band.csv", index=False)
pd.set_option("display.width", 200); print(T.round(3).to_string(index=False))
