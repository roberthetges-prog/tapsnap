"""Round 31 (declared before running): do the levels and the wide band replicate on six dollar pairs?

The bots' levels need EUR/USD's evidence frame, so the replication uses the single-gauge form every bot shares: lower
(upper) level = the 20 % (80 %) quantile of the lowest-low (highest-high) move in gauge units over the training window,
times today's gauge (21-session realised vol x sqrt(h)); wide band = both levels stretched by the round-14 factor rule
(smallest factor with 80 % joint holding on past sessions). Walk-forward yearly, 5 / 10 / 21 sessions, GBP, JPY, AUD,
CHF, CAD, NZD vs USD. Bar: each level holds 76-84 % and the band 76-84 % at every horizon for at least 5 of 6 pairs in
2010-26 and in 2018-26. Writes bots_levels_replication.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

GRID = np.round(np.arange(1.0, 2.501, 0.01), 2)
PAIRS = ("eurusd_check", "gbpusd", "usdjpy", "audusd", "usdchf", "usdcad", "nzdusd")
rows = []
for pair in PAIRS:
    if pair == "eurusd_check":
        X = B.build(); D = pd.DataFrame({"close": X["__close"], "high": X["__high"], "low": X["__low"]}, index=X.index)
    else:
        D = pd.read_parquet(ROOT / "data" / "processed" / f"reliable_parts_daily_{pair}.parquet")
    idx = D.index if D.index.tz is not None else D.index.tz_localize("UTC"); D.index = idx
    c, hi, lo = D["close"], D["high"], D["low"]
    g = np.log(c).diff().rolling(21).std()
    for h in (5, 10, 21):
        fmin = lo[::-1].rolling(h, min_periods=h).min()[::-1].shift(-1); fmax = hi[::-1].rolling(h, min_periods=h).max()[::-1].shift(-1)
        s = g * np.sqrt(h); dn = np.log(fmin / c) / s; up = np.log(fmax / c) / s
        ct_end = pd.Series(idx, index=idx).shift(-h)
        ok = (dn.notna() & up.notna()).values
        ql = pd.Series(np.nan, index=idx); qu = ql.copy(); kf = ql.copy()
        for Y in range(2010, 2027):
            ref = ok & (ct_end < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
            ry = idx.year == Y
            if ref.sum() < 500 or not ry.any():
                continue
            a_, b_ = np.quantile(dn[ref], 0.2), np.quantile(up[ref], 0.8)
            ql[ry], qu[ry] = a_, b_
            kf[ry] = next((float(k) for k in GRID if ((dn[ref] >= k * a_) & (up[ref] <= k * b_)).mean() >= 0.80), float(GRID[-1]))
        for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
            m = ok & ql.notna().values & (idx.year >= a) & (idx.year <= b)
            rows.append({"pair": pair, "h": h, "era": era, "n_indep": round(m.sum() / h, 1), "lower_held": float((dn[m] >= ql[m]).mean()), "upper_held": float((up[m] <= qu[m]).mean()),
                         "band_held": float(((dn[m] >= kf[m] * ql[m]) & (up[m] <= kf[m] * qu[m])).mean()), "band_factor": float(kf[m].mean())})
    print(pair, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_levels_replication.csv", index=False)
pd.set_option("display.width", 200)
print(T.assign(**{c: (100 * T[c]).round(1) for c in ("lower_held", "upper_held", "band_held")}).round(2).to_string(index=False))
S = T[T.pair != "eurusd_check"]
for era in ("2010-26", "2018-26"):
    s = S[S.era == era]; okp = s.groupby("pair").apply(lambda x: ((x[["lower_held", "upper_held", "band_held"]] >= 0.76) & (x[["lower_held", "upper_held", "band_held"]] <= 0.84)).all().all())
    print(era, "pairs passing:", int(okp.sum()), "/ 6", list(okp[~okp].index))
