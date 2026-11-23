"""Round 33 (declared before running): an 80 % band for the coming period's RANGE (high minus low), as a product line.

The levels say where the price will stay; a user also asks how much it will travel. Candidate: the ratio of the next
h sessions' range (highest high minus lowest low, in log terms) to the median bot gauge x sqrt(h) has a walk-forward
10 % / 90 % quantile over the training window; multiply by today's gauge for the band. Bar: coverage 76-84 % at 5 / 10 /
21 sessions in 2010-26 and 2018-26; also report the accuracy of 'range above / below its 1-year median' from the
band's midpoint against the published HAR figure (75-78 %). Writes bots_range_band.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

X = B.build(); rows = []; live = []
g = pd.DataFrame({sp["bot"]: X[f"g_{sp['gauge']}"] for sp in B.SPECS}).median(axis=1)
hist = X["__src"] == "histdata"; hi, lo = X["__high"].where(hist), X["__low"].where(hist)
for h in (5, 10, 21, 63):
    fmax = hi[::-1].rolling(h, min_periods=h).max()[::-1].shift(-1); fmin = lo[::-1].rolling(h, min_periods=h).min()[::-1].shift(-1)
    rng_ = np.log(fmax / fmin); s = g * np.sqrt(h); ratio = rng_ / s
    yend = X["__ct"].shift(-h)
    ok = (ratio.notna()).values
    q10 = pd.Series(np.nan, index=X.index); q90 = q10.copy(); q50 = q10.copy(); med1y = q10.copy()
    for Y in range(2010, 2027):
        ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
        ry = X.index.year == Y
        if ref.sum() < 500 or not ry.any():
            continue
        q10[ry], q50[ry], q90[ry] = np.quantile(ratio[ref], [0.1, 0.5, 0.9])
        last = ref & (X["__ct"] >= pd.Timestamp(f"{Y}-01-01", tz="UTC") - pd.DateOffset(years=1)).values
        med1y[ry] = float(np.median(rng_[last]))
    lo_b, hi_b, mid = q10 * s, q90 * s, q50 * s
    for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
        m = ok & q10.notna().values & (X.index.year >= a) & (X.index.year <= b)
        cover = float(((rng_[m] >= lo_b[m]) & (rng_[m] <= hi_b[m])).mean())
        acc = float(((mid[m] > med1y[m]) == (rng_[m] > med1y[m])).mean())
        naive = float(((rng_.shift(h)[m] > med1y[m]) == (rng_[m] > med1y[m])).mean())
        rows.append({"h": h, "era": era, "n_indep": round(m.sum() / h, 1), "coverage_80": cover, "below_low": float((rng_[m] < lo_b[m]).mean()), "above_high": float((rng_[m] > hi_b[m]).mean()),
                     "above_below_median_acc": acc, "naive_same_as_last": naive, "avg_band_pct": 100 * float((hi_b[m] - lo_b[m]).mean()), "avg_mid_pct": 100 * float(mid[m].mean())})
    live.append({"h": h, "q10": float(np.quantile(ratio[ok], 0.1)), "q50": float(np.quantile(ratio[ok], 0.5)), "q90": float(np.quantile(ratio[ok], 0.9))})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_range_band.csv", index=False); pd.DataFrame(live).to_csv(B.RES / "bots_range_band_live.csv", index=False)
pd.set_option("display.width", 200)
print(T.assign(**{c: (100 * T[c]).round(1) for c in ("coverage_80", "below_low", "above_high", "above_below_median_acc", "naive_same_as_last")}).round(2).to_string(index=False))
