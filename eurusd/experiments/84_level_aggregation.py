"""Round 25 (declared before running): how should the 100 bots' levels be combined?

The published level is the MEDIAN of the 100 bots' levels. Candidates (3): the mean; the 20 %-trimmed mean; a
track-record weighted median (each bot weighted by how close its own levels came to an 80 % holding rate on past
sessions, walk-forward). Scoring: the pinball (quantile) loss at the 20 % / 80 % quantiles of the period's lowest low and
highest high, as in round 11, plus holding rates. Bar: a candidate replaces the median only if its loss is lower at
all four horizons in 2018-2026 with a paired block-bootstrap interval excluding zero at two of them. Writes
bots_level_aggregation.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

rng = np.random.default_rng(3)
def pin(x, tau):
    return np.where(x >= 0, tau * x, (tau - 1) * x)
def loss(l, u, dn, up):
    return pin(dn - l, 0.20) + pin(up - u, 0.80)
def boot_diff(a, b, block):
    d = (a - b); n = len(d); nb = int(np.ceil(n / block)); out = []
    for _ in range(2000):
        st = rng.integers(0, n, nb); idx = (st[:, None] + np.arange(block)[None, :]).ravel()[:n] % n
        out.append(d[idx].mean())
    return float(np.percentile(out, 2.5)), float(np.percentile(out, 97.5))
X = B.build()
rows = []
for h in B.HORIZONS:
    _, LO, HI = B.walk_forward(X, h, verbose=False)
    idx = LO.index; c = X["__close"].reindex(idx)
    lo, hi = np.log(LO.div(c, axis=0)), np.log(HI.div(c, axis=0))
    dn, up, yend = X[f"dn{h}"].reindex(idx), X[f"up{h}"].reindex(idx), X[f"yend{h}"].reindex(idx)
    ok = (lo.notna().all(axis=1) & dn.notna()).values
    cands = {"median": (lo.median(axis=1), hi.median(axis=1)), "mean": (lo.mean(axis=1), hi.mean(axis=1))}
    tl, th = lo.apply(lambda r: r.sort_values().iloc[20:80].mean(), axis=1), hi.apply(lambda r: r.sort_values().iloc[20:80].mean(), axis=1)
    cands["trimmed mean"] = (tl, th)
    # track-record weighted median: weight = 1 / (|hold rate - 0.8| + 0.02) on known past sessions, per bot, walk-forward
    wl, wh = pd.Series(np.nan, index=idx), pd.Series(np.nan, index=idx)
    for Y in range(2010, 2027):
        ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
        ry = idx.year == Y
        if ref.sum() < 500 or not ry.any():
            continue
        hold_l = (dn[ref].values[:, None] >= lo[ref].values).mean(0); hold_h = (up[ref].values[:, None] <= hi[ref].values).mean(0)
        w_l = 1 / (np.abs(hold_l - 0.8) + 0.02); w_h = 1 / (np.abs(hold_h - 0.8) + 0.02)
        def wmed(M, w):
            out = np.empty(M.shape[0])
            for i in range(M.shape[0]):
                o = np.argsort(M[i]); cw = np.cumsum(w[o]); out[i] = M[i][o][np.searchsorted(cw, 0.5 * cw[-1])]
            return out
        wl[ry] = wmed(lo[ry].values, w_l); wh[ry] = wmed(hi[ry].values, w_h)
    cands["record-weighted median"] = (wl, wh)
    base_l = loss(cands["median"][0].values, cands["median"][1].values, dn.values, up.values)
    for name, (l, u) in cands.items():
        L = loss(l.values, u.values, dn.values, up.values)
        for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
            m = ok & l.notna().values & (idx.year >= a) & (idx.year <= b)
            lo_ci, hi_ci = boot_diff(L[m], base_l[m], block=2 * h) if name != "median" else (0.0, 0.0)
            rows.append({"h": h, "candidate": name, "era": era, "n_indep": round(m.sum() / h, 1), "loss_bp": 1e4 * float(L[m].mean()),
                         "vs_median_pct": 100 * float(L[m].mean() / base_l[m].mean() - 1), "ci_lo_bp": 1e4 * lo_ci, "ci_hi_bp": 1e4 * hi_ci,
                         "lower_held": float((dn[m] >= l[m]).mean()), "upper_held": float((up[m] <= u[m]).mean()), "width_pct": 100 * float((u[m] - l[m]).mean())})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_level_aggregation.csv", index=False)
pd.set_option("display.width", 220); print(T.round(3).to_string(index=False))
