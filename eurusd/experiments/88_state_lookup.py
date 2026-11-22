"""Round 29 (declared before running): instead of fixing the levels per state, STATE the holding rate for today's state.

Rounds 11, 22-24, 27-28: the levels hold about 80 % on average, less in calm markets, at 3-month lows and in event weeks,
more in volatile markets; every fixed correction over- or under-shot out of sample. Candidate: a look-up. For each
session the state is (volatility tercile x event window yes/no x position: bottom decile / middle / top decile); the
stated holding rate of each level is the walk-forward empirical rate in that state cell (cells with fewer than 150
past sessions fall back to the pooled rate). Bar: in 2018-26, at 5 and 10 sessions, the realised holding rate per
cell is within 5 points of the stated one for every cell with at least 20 independent periods, and the mean absolute
gap across cells is smaller than the pooled statement's. Writes bots_state_lookup.csv and bots_state_table.csv (live).
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B
from eurusd.arms import sharper_levels as SL

X = B.build(); ev = SL.event_times(); rows = []; live = []
c_all = X["__close"]; pos_all = (c_all - c_all.rolling(63).min()) / (c_all.rolling(63).max() - c_all.rolling(63).min())
v_all = X["g_rv21"]; a = pd.DatetimeIndex(X["__ct"]).as_unit("ns").asi8
for h in (5, 10, 21):
    _, LO, HI = B.walk_forward(X, h, verbose=False)
    idx = LO.index; c = c_all.reindex(idx)
    lo = np.log(LO.div(c, axis=0)); hi = np.log(HI.div(c, axis=0)); k20 = 20
    l = np.sort(lo.values, axis=1)[:, k20:100 - k20].mean(1); u = np.sort(hi.values, axis=1)[:, k20:100 - k20].mean(1)
    dn, up, yend = X[f"dn{h}"].reindex(idx).values, X[f"up{h}"].reindex(idx).values, X[f"yend{h}"].reindex(idx)
    b = pd.DatetimeIndex(X["__ct"].reindex(idx) + pd.offsets.BDay(h)).as_unit("ns").asi8
    evw = np.zeros(len(idx), bool)
    for kd in ("fomc", "ecb", "nfp", "cpi"):
        evw |= SL._count_in(ev[kd], a[X.index.get_indexer(idx)], b) > 0
    p = pos_all.reindex(idx).values; v = v_all.reindex(idx).values
    ok = np.isfinite(dn) & np.isfinite(l) & np.isfinite(p) & np.isfinite(v)
    held_l, held_u = (dn >= l), (up <= u)
    st_l = np.full(len(idx), np.nan); st_u = np.full(len(idx), np.nan); pooled_l = np.full(len(idx), np.nan); pooled_u = np.full(len(idx), np.nan); cell = np.full(len(idx), "", dtype=object)
    for Y in range(2010, 2027):
        ref = ok & (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values
        ry = (idx.year == Y)
        if ref.sum() < 500 or not ry.any():
            continue
        q1, q2 = np.quantile(v[ref], [1 / 3, 2 / 3])
        terc = np.where(v < q1, "calm", np.where(v < q2, "normal", "volatile"))
        posc = np.where(p <= 0.1, "low", np.where(p >= 0.9, "high", "mid"))
        key = pd.Series(terc, dtype=object) + "|" + np.where(evw, "event", "quiet") + "|" + pd.Series(posc, dtype=object)
        pl, pu = held_l[ref].mean(), held_u[ref].mean()
        for i in np.where(ry)[0]:
            m = ref & (key.values == key.values[i])
            cell[i] = key.values[i]; pooled_l[i], pooled_u[i] = pl, pu
            st_l[i], st_u[i] = (held_l[m].mean(), held_u[m].mean()) if m.sum() >= 150 else (pl, pu)
    for era, aa, bb in (("2010-26", 2010, 2026), ("2018-26", 2018, 2026)):
        base = ok & np.isfinite(st_l) & (idx.year >= aa) & (idx.year <= bb)
        for ky in sorted(set(cell[base])):
            m = base & (cell == ky)
            rows.append({"h": h, "era": era, "cell": ky, "n_indep": round(m.sum() / h, 1), "stated_lower": st_l[m].mean(), "realised_lower": held_l[m].mean(),
                         "stated_upper": st_u[m].mean(), "realised_upper": held_u[m].mean(), "pooled_lower": pooled_l[m].mean(), "pooled_upper": pooled_u[m].mean()})
    # live table from all known outcomes
    ref = ok & yend.notna().values
    q1, q2 = np.quantile(v[ref], [1 / 3, 2 / 3])
    terc = np.where(v < q1, "calm", np.where(v < q2, "normal", "volatile")); posc = np.where(p <= 0.1, "low", np.where(p >= 0.9, "high", "mid"))
    key = pd.Series(terc, dtype=object) + "|" + np.where(evw, "event", "quiet") + "|" + pd.Series(posc, dtype=object)
    for ky in sorted(set(key[ref])):
        m = ref & (key.values == ky)
        live.append({"h": h, "cell": ky, "n": int(m.sum()), "lower_held": held_l[m].mean() if m.sum() >= 150 else held_l[ref].mean(), "upper_held": held_u[m].mean() if m.sum() >= 150 else held_u[ref].mean(), "fallback": bool(m.sum() < 150)})
    live.append({"h": h, "cell": "pooled", "n": int(ref.sum()), "lower_held": held_l[ref].mean(), "upper_held": held_u[ref].mean(), "fallback": False})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_state_lookup.csv", index=False); pd.DataFrame(live).to_csv(B.RES / "bots_state_table.csv", index=False)
S = T[(T.era == "2018-26") & (T.n_indep >= 20)].copy()
S["gap_l"] = 100 * (S.realised_lower - S.stated_lower); S["gap_u"] = 100 * (S.realised_upper - S.stated_upper)
S["pgap_l"] = 100 * (S.realised_lower - S.pooled_lower); S["pgap_u"] = 100 * (S.realised_upper - S.pooled_upper)
pd.set_option("display.width", 240)
print(S.assign(**{c: (100 * S[c]).round(1) for c in ("stated_lower", "realised_lower", "stated_upper", "realised_upper")})[["h", "cell", "n_indep", "stated_lower", "realised_lower", "gap_l", "stated_upper", "realised_upper", "gap_u", "pgap_l", "pgap_u"]].round(1).to_string(index=False))
for h in (5, 10, 21):
    s = S[S.h == h]; print(f"h={h}: cells {len(s)}, max |gap| lookup {max(s.gap_l.abs().max(), s.gap_u.abs().max()):.1f}, mean |gap| lookup {np.mean(np.r_[s.gap_l.abs(), s.gap_u.abs()]):.1f} vs pooled {np.mean(np.r_[s.pgap_l.abs(), s.pgap_u.abs()]):.1f}")
