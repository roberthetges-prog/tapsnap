"""Round 28 (declared in round 27, before running): widen the LOWER level when the close sits at a 63-session low.

When the close is in the bottom decile of its 63-session range the lower level is breached far more often (round 27).
Candidate (one): on such sessions the lower level's log distance is multiplied by a walk-forward factor k (grid 1.00 ..
2.00, step 0.01), the smallest for which the lower level held at least 80 % on past bottom-decile sessions whose outcome
was known before the test year. Nothing else changes (upper level, middle sessions). Bar: bottom-decile lower holding
rate within 4 points of 80 % at 5 and 10 sessions in 2018-26 (21 reported), middle unchanged by construction.
Also reported: the mirror candidate (upper level at 63-session highs) for description only. Writes bots_lower_at_lows.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

GRID = np.round(np.arange(1.0, 2.001, 0.01), 2)
X = B.build(); rows = []
c_all = X["__close"]; pos_all = (c_all - c_all.rolling(63).min()) / (c_all.rolling(63).max() - c_all.rolling(63).min())
for h in (5, 10, 21):
    _, LO, HI = B.walk_forward(X, h, verbose=False)
    idx = LO.index; c = c_all.reindex(idx)
    lo = np.log(LO.div(c, axis=0)); hi = np.log(HI.div(c, axis=0)); k20 = 20
    l = pd.Series(np.sort(lo.values, axis=1)[:, k20:100 - k20].mean(1), index=idx); u = pd.Series(np.sort(hi.values, axis=1)[:, k20:100 - k20].mean(1), index=idx)
    dn, up, yend = X[f"dn{h}"].reindex(idx), X[f"up{h}"].reindex(idx), X[f"yend{h}"].reindex(idx)
    p = pos_all.reindex(idx)
    ok = (dn.notna() & l.notna() & p.notna()).values
    low_ = (p <= 0.1).values; high_ = (p >= 0.9).values
    kl = pd.Series(np.nan, index=idx); ku = pd.Series(np.nan, index=idx)
    for Y in range(2010, 2027):
        ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
        ry = idx.year == Y
        if (ref & low_).sum() < 200 or not ry.any():
            continue
        m = ref & low_
        kl[ry] = next((float(k) for k in GRID if (dn[m] >= k * l[m]).mean() >= 0.80), float(GRID[-1]))
        m = ref & high_
        ku[ry] = next((float(k) for k in GRID if (up[m] <= k * u[m]).mean() >= 0.80), float(GRID[-1]))
    l_new = l.where(~low_, l * kl); u_new = u.where(~high_, u * ku)
    for era, a, b in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
        base = ok & kl.notna().values & (idx.year >= a) & (idx.year <= b)
        for grp, m in (("bottom decile", base & low_), ("middle", base & ~low_ & ~high_), ("top decile", base & high_)):
            rows.append({"h": h, "era": era, "position": grp, "n_indep": round(m.sum() / h, 1), "lower_held_before": float((dn[m] >= l[m]).mean()), "lower_held_after": float((dn[m] >= l_new[m]).mean()),
                         "upper_held_before": float((up[m] <= u[m]).mean()), "upper_held_after_mirror": float((up[m] <= u_new[m]).mean()),
                         "lower_widened_pct": 100 * float((l_new[m] / l[m] - 1).mean()), "k_lower": float(kl[m].mean()), "k_upper_mirror": float(ku[m].mean())})
    rows.append({"h": h, "era": "live", "position": "factors", "k_lower": float(kl.dropna().iloc[-1]), "k_upper_mirror": float(ku.dropna().iloc[-1])})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_lower_at_lows.csv", index=False)
pd.set_option("display.width", 240)
S = T[T.era != "live"].copy()
for ccol in ("lower_held_before", "lower_held_after", "upper_held_before", "upper_held_after_mirror"): S[ccol] = (100 * S[ccol]).round(1)
print(S.round(2).to_string(index=False)); print(T[T.era == "live"][["h", "k_lower", "k_upper_mirror"]].to_string(index=False))
