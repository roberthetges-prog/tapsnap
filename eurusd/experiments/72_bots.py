"""Walk-forward test of the 100-bot vote and its levels (src/eurusd/bots.py; design declared there before running).

Writes experiments/results/arms/bots_*.{parquet,csv} and reports/bots.md.
    PYTHONPATH=src OMP_NUM_THREADS=1 python experiments/72_bots.py
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B  # noqa: E402
from eurusd import committee as C  # noqa: E402
from eurusd.arms.swing import wilson  # noqa: E402

RES = B.RES
SETS = {"thin": ("thin",), "fair": ("fair",), "wide": ("wide",), "very wide": ("very wide",), "fair or wider": ("fair", "wide", "very wide"),
        "every vote": ("thin", "fair", "wide", "very wide")}
ERAS = B.ERAS + (("2010-17", 2010, 2017), ("2018-26", 2018, 2026))


def acc(side: pd.Series, y: pd.Series, h: int, a: int, b: int) -> dict:
    m = (side.index.year >= a) & (side.index.year <= b) & (side != 0).values & y.notna().values & (y != 0).values
    n = int(m.sum())
    era_days = int(((side.index.year >= a) & (side.index.year <= b) & y.notna().values).sum())
    if n == 0:
        return {"n_indep": 0.0, "acc": np.nan, "lo": np.nan, "hi": np.nan, "per_year": 0.0, "share_of_days": 0.0}
    hit = float((side[m] == y[m]).mean())
    ni = n / h
    lo, hi = wilson(int(round(hit * ni)), max(int(round(ni)), 1))
    return {"n_indep": round(ni, 1), "acc": hit, "lo": lo, "hi": hi, "per_year": ni / (b - a + 1), "share_of_days": n / max(era_days, 1)}


def track_weights(P: pd.DataFrame, y: pd.Series, yend: pd.Series, h: int) -> pd.DataFrame:
    V = np.where(P > 0.5, 1.0, np.where(P.notna(), -1.0, 0.0))
    hit = ((V == y.values[:, None]) & (V != 0)).astype(float)
    call = (V != 0).astype(float)
    W = pd.DataFrame(1.0, index=P.index, columns=P.columns)
    k = 10 * h
    for Y in range(2010, 2027):
        ref = (yend < pd.Timestamp(f"{Y}-01-01", tz="UTC")).values & y.notna().values & (y != 0).values
        rows = P.index.year == Y
        if ref.sum() < 500 or not rows.any():
            continue
        edge = np.clip((hit[ref].sum(0) + 0.5 * k) / (call[ref].sum(0) + k) - 0.5, 0, None)
        W.loc[rows] = edge if edge.sum() > 0 else 1.0
    return W


def main():
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 500)
    X = B.build()
    print("frame", X.shape, flush=True)
    rec, lev, cal, extra = [], [], [], []
    for h in B.HORIZONS:
        P, LO, HI = B.walk_forward(X, h)
        P.columns = P.columns.astype(str); LO.columns = LO.columns.astype(str); HI.columns = HI.columns.astype(str)
        P.to_parquet(RES / f"bots_probs_h{h}.parquet")
        y = X[f"y{h}"].reindex(P.index)
        yend = X[f"yend{h}"].reindex(P.index)
        T = B.count(P)
        Tw = B.count(P, track_weights(P, y, yend, h))
        T.to_parquet(RES / f"bots_votes_h{h}.parquet")
        for wname, t in (("equal", T), ("track record", Tw)):
            for name, members in SETS.items():
                side = t["side"].where(t["cls"].isin(members), 0.0)
                for era, a, b in ERAS:
                    rec.append({"weights": wname, "h": h, "cls": name, "era": era, **acc(side, y, h, a, b)})
        # stale copy, benchmark, always long
        st = T.shift(63)
        for era, a, b in B.ERAS:
            extra.append({"what": "vote of 63 sessions ago (every vote)", "h": h, "era": era, **acc(st["side"].fillna(0.0), y, h, a, b)})
            extra.append({"what": "vote of 63 sessions ago (fair or wider)", "h": h, "era": era, **acc(st["side"].where(st["cls"].isin(SETS["fair or wider"]), 0.0).fillna(0.0), y, h, a, b)})
            extra.append({"what": "always up", "h": h, "era": era, **acc(pd.Series(1.0, index=P.index), y, h, a, b)})
        # is the count a probability? realised share of UP outcomes by number of UP votes
        ok = y.notna() & (y != 0) & (P.index.year >= 2010)
        grp = pd.cut(T["up"][ok], [-1, 19, 29, 39, 49, 59, 69, 79, 100], labels=["0-19", "20-29", "30-39", "40-49", "50-59", "60-69", "70-79", "80-100"])
        g = (y[ok] > 0).groupby(grp, observed=True).agg(["mean", "size"])
        for k_, r in g.iterrows():
            cal.append({"h": h, "up_votes": k_, "went_up": r["mean"], "sessions": int(r["size"]), "n_indep": round(r["size"] / h, 1)})
        # individual bots and diversity
        V = np.where(P > 0.5, 1.0, np.where(P.notna(), -1.0, np.nan))
        m10 = (P.index.year >= 2010) & y.notna().values & (y != 0).values
        ind = pd.Series(np.nanmean((V[m10] == y.values[m10][:, None]).astype(float), axis=0))
        cc = pd.DataFrame(V[m10]).corr().values
        extra.append({"what": f"single bots: median accuracy {100 * ind.median():.1f} %, best {100 * ind.max():.1f} %, worst {100 * ind.min():.1f} %, share above 50 %: {100 * (ind > 0.5).mean():.0f} %; mean correlation between two bots' votes {np.nanmean(cc[np.triu_indices_from(cc, 1)]):.2f}",
                      "h": h, "era": "2010-26", "n_indep": np.nan, "acc": float(ind.median()), "lo": np.nan, "hi": np.nan, "per_year": np.nan, "share_of_days": np.nan})
        # levels
        lo_med, hi_med = LO.median(axis=1), HI.median(axis=1)
        c = X["__close"].reindex(P.index)
        dn, up = X[f"dn{h}"].reindex(P.index), X[f"up{h}"].reindex(P.index)
        real_lo, real_hi = c * np.exp(dn), c * np.exp(up)
        # naive levels: the same quantiles with no volatility scaling (expanding history, yearly)
        nlo, nhi = pd.Series(np.nan, index=P.index), pd.Series(np.nan, index=P.index)
        for Y in B.TEST_YEARS:
            start = pd.Timestamp(f"{Y}-01-01", tz="UTC")
            k_ = (X[f"yend{h}"] < start).values & X[f"dn{h}"].notna().values
            rows = P.index.year == Y
            if k_.sum() < B.MIN_ROWS or not rows.any():
                continue
            nlo[rows] = c[rows] * np.exp(np.quantile(X[f"dn{h}"].values[k_], 1 - B.LEVEL_Q))
            nhi[rows] = c[rows] * np.exp(np.quantile(X[f"up{h}"].values[k_], B.LEVEL_Q))
        for kind, a_lo, a_hi in (("bots", lo_med, hi_med), ("no volatility scaling", nlo, nhi)):
            for era, a, b in B.ERAS:
                m = (P.index.year >= a) & (P.index.year <= b) & real_lo.notna().values & a_lo.notna().values
                lh, uh = (real_lo[m] >= a_lo[m]), (real_hi[m] <= a_hi[m])
                width = ((a_hi[m] - a_lo[m]) / c[m]).mean()
                # stability: how far the yearly holding rate strays from 80 %
                yr = pd.DataFrame({"l": lh, "u": uh}).groupby(lh.index.year).mean()
                lev.append({"h": h, "kind": kind, "era": era, "sessions": int(m.sum()), "n_indep": round(m.sum() / h, 1), "lower_held": float(lh.mean()), "upper_held": float(uh.mean()),
                            "both_held": float((lh & uh).mean()), "avg_width_pct": 100 * float(width), "worst_year_lower": float(yr["l"].min()), "worst_year_upper": float(yr["u"].min())})
        # conditional calibration: do the levels hold as well when volatility is high as when it is low?
        g21 = X["g_rv21"].reindex(P.index)
        m = (P.index.year >= 2010) & real_lo.notna().values & lo_med.notna().values
        hi_vol = g21 > g21[m].median()
        for nm, mm in (("volatility above its median", m & hi_vol.values), ("volatility below its median", m & ~hi_vol.values)):
            for kind, a_lo, a_hi in (("bots", lo_med, hi_med), ("no volatility scaling", nlo, nhi)):
                lev.append({"h": h, "kind": f"{kind} | {nm}", "era": "2010-26", "sessions": int(mm.sum()), "n_indep": round(mm.sum() / h, 1), "lower_held": float((real_lo[mm] >= a_lo[mm]).mean()),
                            "upper_held": float((real_hi[mm] <= a_hi[mm]).mean()), "both_held": float(((real_lo[mm] >= a_lo[mm]) & (real_hi[mm] <= a_hi[mm])).mean()),
                            "avg_width_pct": 100 * float(((a_hi[mm] - a_lo[mm]) / c[mm]).mean()), "worst_year_lower": np.nan, "worst_year_upper": np.nan})
    rec, lev, cal, extra = pd.DataFrame(rec), pd.DataFrame(lev), pd.DataFrame(cal), pd.DataFrame(extra)
    # benchmark: the three-signal agreement rule and the committee on the same folds
    import importlib.util
    spc = importlib.util.spec_from_file_location("c70", ROOT / "experiments" / "70_committee.py")
    c70 = importlib.util.module_from_spec(spc); spc.loader.exec_module(c70)
    Xc = C.build_frame()
    ag = c70.agreement_side(Xc)
    bench = []
    for h in B.HORIZONS:
        yy = X[f"y{h}"].reindex(ag.index)
        for era, a, b in B.ERAS:
            bench.append({"what": "three-signal agreement rule", "h": h, "era": era, **acc(ag, yy, h, a, b)})
    extra = pd.concat([extra, pd.DataFrame(bench)], ignore_index=True)
    rec.to_csv(RES / "bots_record.csv", index=False); lev.to_csv(RES / "bots_levels.csv", index=False)
    cal.to_csv(RES / "bots_count_vs_outcome.csv", index=False); extra.to_csv(RES / "bots_extra.csv", index=False)
    pd.DataFrame([{**{k: v for k, v in s.items() if k != "desk"}, "desk": ", ".join(s["desk"])} for s in B.SPECS]).to_csv(RES / "bots_roster.csv", index=False)

    # ---- declared weight decision
    g = lambda w, h, cls, era: float(rec[(rec.weights == w) & (rec.h == h) & (rec.cls == cls) & (rec.era == era)]["acc"].iloc[0])  # noqa: E731
    d = {(h, e): 100 * (g("track record", h, "every vote", e) - g("equal", h, "every vote", e)) for h in (21, 63) for e in ("2010-17", "2018-26")}
    weighted_wins = d[(21, "2018-26")] >= 2 and d[(63, "2018-26")] >= 2 and d[(21, "2010-17")] >= 0 and d[(63, "2010-17")] >= 0
    lv_ok = all(abs(r.lower_held - 0.8) <= 0.04 and abs(r.upper_held - 0.8) <= 0.04 for r in lev[(lev.kind == "bots")].itertuples())

    def pct(df, cols):
        d_ = df.copy()
        for c_ in cols:
            if c_ in d_:
                d_[c_] = (100 * d_[c_]).round(1)
        for c_ in ("per_year", "avg_width_pct"):
            if c_ in d_:
                d_[c_] = d_[c_].round(1 if c_ == "per_year" else 2)
        return d_

    eq = rec[(rec.weights == "equal") & rec.era.isin(["2010-26", "2016-26", "2023-26"])]
    md = ["# The vote: 100 bots, direction and levels", "",
          "Code `src/eurusd/bots.py` (design declared in its docstring before the first run, 2026-11-17), test `experiments/72_bots.py`, results `experiments/results/arms/bots_*`.", "",
          f"**Weights: {'the track-record weighting replaces the equal vote' if weighted_wins else 'the equal vote stays'}** "
          f"(track record minus equal, every vote: {d[(21, '2010-17')]:+.1f} / {d[(21, '2018-26')]:+.1f} points at 21 sessions in 2010-17 / 2018-26, {d[(63, '2010-17')]:+.1f} / {d[(63, '2018-26')]:+.1f} at 63).",
          f"**Levels: {'PASS' if lv_ok else 'see table'}** against the declared test (each level holds within 4 points of 80 % in every era).", "",
          "## What a vote was worth (equal weights, walk-forward, out of sample)", "",
          "`n_indep` = independent votes (sessions divided by the horizon); `lo`-`hi` = 95 % range; `share_of_days` = how often the vote was in that class.", ""]
    for h in B.HORIZONS:
        md += [f"### {h} sessions", "", pct(eq[eq.h == h], ["acc", "lo", "hi", "share_of_days"])[["cls", "era", "n_indep", "acc", "lo", "hi", "per_year", "share_of_days"]].to_markdown(index=False), ""]
    md += ["## Is the count a probability? Share of sessions that went UP, by number of UP votes (2010-26)", "", pct(cal, ["went_up"]).to_markdown(index=False), "",
           "## Levels: how often they held", "",
           "`lower_held` = the period's lowest price stayed above the lower level; `upper_held` = the highest stayed below the upper level; target 80 % each.", "",
           pct(lev, ["lower_held", "upper_held", "both_held", "worst_year_lower", "worst_year_upper"]).to_markdown(index=False), "",
           "## Equal vote against track-record weights", "",
           pct(rec[(rec.cls == "every vote")], ["acc", "lo", "hi", "share_of_days"])[["weights", "h", "era", "n_indep", "acc", "lo", "hi"]].to_markdown(index=False), "",
           "## Stale vote, always-up, the agreement rule, and the bots one by one", "", pct(extra, ["acc", "lo", "hi", "share_of_days"])[["what", "h", "era", "n_indep", "acc", "lo", "hi"]].to_markdown(index=False), ""]
    (ROOT / "reports" / "bots.md").write_text("\n".join(md))
    print("\nWEIGHTS:", "track record replaces equal" if weighted_wins else "equal stays", d)
    print("LEVELS within 4 points of 80 % everywhere:", lv_ok)
    print("\nrecord (equal):\n", pct(eq, ["acc", "lo", "hi", "share_of_days"])[["h", "cls", "era", "n_indep", "acc", "lo", "hi", "share_of_days"]].to_string(index=False))
    print("\ncount vs outcome:\n", pct(cal, ["went_up"]).to_string(index=False))
    print("\nlevels:\n", pct(lev, ["lower_held", "upper_held", "both_held", "worst_year_lower", "worst_year_upper"]).to_string(index=False))
    print("\nextra:\n", pct(extra, ["acc", "lo", "hi"])[["what", "h", "era", "n_indep", "acc"]].to_string(index=False))
    tw = rec[(rec.cls == "every vote") & rec.era.isin(["2010-17", "2018-26", "2010-26"])]
    print("\nweights:\n", pct(tw, ["acc"])[["weights", "h", "era", "n_indep", "acc"]].to_string(index=False))


if __name__ == "__main__":
    main()
