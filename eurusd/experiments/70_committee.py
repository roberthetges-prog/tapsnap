"""Walk-forward test of the 100-analyst committee (src/eurusd/committee.py). One design, declared before running.

Writes experiments/results/arms/committee_*.{parquet,csv} and reports/committee.md.
    PYTHONPATH=src OMP_NUM_THREADS=1 python experiments/70_committee.py
"""
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import committee as C  # noqa: E402
from eurusd.arms.swing import wilson  # noqa: E402

RES = C.RES
SETS = {"split": ("split",), "lean": ("lean",), "clear": ("clear",), "strong": ("strong",), "clear+strong": ("clear", "strong"),
        "any majority": ("split", "lean", "clear", "strong")}


def acc_row(side: pd.Series, y: pd.Series, h: int, a: int, b: int) -> dict:
    """Phase-averaged non-overlapping accuracy: every session with a call is scored on the next h sessions; the
    count of INDEPENDENT calls is the average number of calls on one of the h non-overlapping grids."""
    m = (side.index.year >= a) & (side.index.year <= b) & (side != 0).values & y.notna().values & (y != 0).values
    n = int(m.sum())
    if n == 0:
        return {"n_days": 0, "n_indep": 0.0, "acc": np.nan, "lo": np.nan, "hi": np.nan, "per_year": 0.0, "share_of_days": 0.0}
    hit = float((side[m] == y[m]).mean())
    n_ind = n / h
    lo, hi = wilson(int(round(hit * n_ind)), max(int(round(n_ind)), 1))
    era_days = int(((side.index.year >= a) & (side.index.year <= b) & y.notna().values).sum())
    return {"n_days": n, "n_indep": round(n_ind, 1), "acc": hit, "lo": lo, "hi": hi, "per_year": n_ind / (b - a + 1), "share_of_days": n / max(era_days, 1)}


def one_grid(side: pd.Series, y: pd.Series, h: int, a: int, b: int) -> dict:
    s, yy = side.iloc[::h], y.iloc[::h]
    m = (s.index.year >= a) & (s.index.year <= b) & (s != 0).values & yy.notna().values & (yy != 0).values
    n = int(m.sum())
    if n == 0:
        return {"n_days": 0, "n_indep": 0.0, "acc": np.nan, "lo": np.nan, "hi": np.nan, "per_year": 0.0, "share_of_days": np.nan}
    k = int((s[m] == yy[m]).sum())
    lo, hi = wilson(k, n)
    return {"n_days": n, "n_indep": float(n), "acc": k / n, "lo": lo, "hi": hi, "per_year": n / (b - a + 1), "share_of_days": np.nan}


def agreement_side(X: pd.DataFrame) -> pd.Series:
    """Walk-forward three-signal agreement rule (the current position call), same folds as the committee."""
    out = pd.Series(np.nan, index=X.index)
    for Y in C.TEST_YEARS:
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC")
        known = (X["yend21"] < start).values & X["y21"].notna().values
        fc = C._fold_columns(X, known)
        rows = X.index.year == Y
        out[rows] = fc["@agree"][rows]
    return out.fillna(0.0)


def run_votes(X: pd.DataFrame, verbose=True) -> tuple[dict, dict]:
    Ps, Ts = {}, {}
    for h in C.HORIZONS:
        Ps[h] = C.walk_forward(X, h, verbose=verbose)
        Ts[h] = C.tally(Ps[h])
    return Ps, Ts


def record_table(Ts: dict, X: pd.DataFrame, shift: int = 0, label: str = "committee") -> pd.DataFrame:
    rows = []
    for h, T in Ts.items():
        y = X[f"y{h}"].reindex(T.index)
        Tu = T.shift(shift) if shift else T
        for name, members in SETS.items():
            side = Tu["side"].where(Tu["cls"].isin(members), 0.0).fillna(0.0)
            for era, a, b in C.ERAS:
                rows.append({"who": label, "h": h, "cls": name, "era": era, "clock": "phase-averaged", **acc_row(side, y, h, a, b)})
                rows.append({"who": label, "h": h, "cls": name, "era": era, "clock": "one grid", **one_grid(side, y, h, a, b)})
    return pd.DataFrame(rows)


def main():
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 400)
    X = C.build_frame()
    print("frame", X.shape, X.index.min(), X.index.max(), flush=True)
    Ps, Ts = run_votes(X)
    for h in C.HORIZONS:
        Ps[h].to_parquet(RES / f"committee_probs_h{h}.parquet")
        Ts[h].to_parquet(RES / f"committee_votes_h{h}.parquet")
    rec = record_table(Ts, X)
    rec.to_csv(RES / "committee_record.csv", index=False)
    # ---- the same committee without the Fed desk (trial 1's roster), and the Fed desk alone
    fed_cols = [a for a in C.AGENTS if C.VIEWS[a.split(":")[0]][0] == "FED"]
    rec_nofed = record_table({h: C.tally(Ps[h].drop(columns=fed_cols)) for h in C.HORIZONS}, X, label="without Fed desk")
    fed_rows = []
    for h in C.HORIZONS:
        up, dn = (Ps[h][fed_cols] > 0.5 + C.EPS).sum(axis=1), (Ps[h][fed_cols] < 0.5 - C.EPS).sum(axis=1)
        side = np.sign(up - dn).astype(float)
        for era, a, b in C.ERAS:
            fed_rows.append({"who": "Fed desk majority (any size)", "h": h, "era": era, **acc_row(side, X[f"y{h}"].reindex(side.index), h, a, b)})
    fed_alone = pd.DataFrame(fed_rows)
    cmp_ = pd.concat([rec.assign(who="with Fed desk"), rec_nofed])
    cmp_ = cmp_[(cmp_.clock == "phase-averaged") & (cmp_.cls == "clear+strong")]
    cmp_.to_csv(RES / "committee_fed_effect.csv", index=False)
    fed_alone.to_csv(RES / "committee_fed_alone.csv", index=False)
    # ---- benchmark: the agreement rule on the same folds
    ag = agreement_side(X)
    bench = []
    for h in C.HORIZONS:
        y = X[f"y{h}"]
        for era, a, b in C.ERAS:
            bench.append({"who": "agreement rule", "h": h, "era": era, **acc_row(ag, y, h, a, b)})
            bench.append({"who": "always long", "h": h, "era": era, **acc_row(pd.Series(1.0, index=X.index), y, h, a, b)})
    bench = pd.DataFrame(bench)
    bench.to_csv(RES / "committee_benchmark.csv", index=False)
    # ---- stale placebos
    stale = pd.concat([record_table(Ts, X, 63, "committee stale 63"), record_table(Ts, X, 126, "committee stale 126")])
    stale.to_csv(RES / "committee_stale.csv", index=False)
    # ---- does the committee add to the agreement rule? (calls of the rule split by what the committee said)
    cond = []
    for h in C.HORIZONS:
        T = Ts[h]
        y = X[f"y{h}"].reindex(T.index)
        a_ = ag.reindex(T.index)
        cs = T["side"].where(T["cls"].isin(("clear", "strong")), 0.0)
        for era, a, b in C.ERAS:
            for name, m in (("rule calls, committee clear majority the same way", (a_ != 0) & (cs == a_)),
                            ("rule calls, committee no clear majority", (a_ != 0) & (cs == 0)),
                            ("rule calls, committee clear majority AGAINST", (a_ != 0) & (cs == -a_)),
                            ("rule silent, committee clear majority", (a_ == 0) & (cs != 0))):
                side = (a_.where(a_ != 0, cs)).where(m, 0.0)
                cond.append({"h": h, "era": era, "case": name, **acc_row(side, y, h, a, b)})
    cond = pd.DataFrame(cond)
    cond.to_csv(RES / "committee_vs_rule.csv", index=False)
    # ---- league table of the analysts (1 month, 2010-26)
    lg = []
    for h in C.HORIZONS:
        P = Ps[h]
        y = X[f"y{h}"].reindex(P.index)
        for a_ in C.AGENTS:
            side = pd.Series(np.where(P[a_] > 0.5 + C.EPS, 1.0, np.where(P[a_] < 0.5 - C.EPS, -1.0, 0.0)), index=P.index)
            v = a_.split(":")[0]
            lg.append({"analyst": a_, "school": C.VIEWS[v][0], "prior": C.VIEWS[v][3], "h": h, **acc_row(side, y, h, 2010, 2026)})
    lg = pd.DataFrame(lg)
    lg.to_csv(RES / "committee_league.csv", index=False)
    # ---- null distribution: the same machine on labels that have nothing to do with the dates
    null = []
    for sft in (1500, 2500, 3500):
        Xn = X.copy()
        for h in C.HORIZONS:
            Xn[f"y{h}"] = np.roll(X[f"y{h}"].values, sft)
        for h in (21, 42):
            T = C.tally(C.walk_forward(Xn, h, verbose=False))
            y = Xn[f"y{h}"].reindex(T.index)
            side = T["side"].where(T["cls"].isin(("clear", "strong")), 0.0)
            null.append({"shift": sft, "h": h, **acc_row(side, y, h, 2010, 2026)})
        print("null shift", sft, "done", flush=True)
    null = pd.DataFrame(null)
    null.to_csv(RES / "committee_null.csv", index=False)
    # ---- look-ahead control: view columns from a frame truncated at 2018 must equal the full frame's
    from eurusd.data import load_ohlc
    D = pd.read_parquet(C.SW.PROC / "features_daily.parquet")
    h1 = load_ohlc("H1").loc["2003":]
    h1 = h1[~h1.index.duplicated(keep="last")]
    cut = pd.Timestamp("2018-12-31", tz="UTC")
    Xt = C.build_frame(D[D.index < cut], h1[h1.index < cut])
    cols = [v[1].replace("{h}", "21") for v in C.VIEWS.values() if not v[1].startswith("@")]
    tail = Xt.index[-250:]
    diff = (Xt.loc[tail, cols].astype(float) - X.loc[tail, cols].astype(float)).abs().max()
    nanmis = (Xt.loc[tail, cols].isna() != X.loc[tail, cols].isna()).sum()
    trunc = pd.DataFrame({"max_abs_diff": diff, "nan_mismatch": nanmis})
    trunc.to_csv(RES / "committee_truncation.csv")
    print("\ntruncation control (columns that differ):\n", trunc[(trunc.max_abs_diff > 1e-9) | (trunc.nan_mismatch > 0)].to_string())

    # ================================================================= verdict and report
    def g(df, **kw):
        m = np.ones(len(df), dtype=bool)
        for k, v in kw.items():
            m &= (df[k] == v).values
        return df[m].iloc[0]

    bar = []
    ok_all = True
    for h in (21, 42):
        for era in ("2010-26", "2016-26"):
            c = g(rec, h=h, cls="clear+strong", era=era, clock="phase-averaged")
            r = g(bench, who="agreement rule", h=h, era=era)
            s = g(stale, who="committee stale 63", h=h, cls="clear+strong", era=era, clock="phase-averaged")
            gain = 100 * (c.acc - r.acc)
            edge, edge_stale = 100 * (c.acc - 0.5), 100 * (s.acc - 0.5)
            p1, p2, p3 = gain >= 3, c.per_year >= 6, (edge > 0 and edge_stale <= 0.5 * edge)
            ok_all &= bool(p1 and p2 and p3)
            bar.append({"h": h, "era": era, "committee clear+strong": f"{100 * c.acc:.1f}", "agreement rule": f"{100 * r.acc:.1f}", "gain pts": f"{gain:+.1f}",
                        "calls/yr": f"{c.per_year:.1f}", "63-stale copy": f"{100 * s.acc:.1f}", ">=3 pts": p1, ">=6/yr": p2, "stale loses half": p3})
    bar = pd.DataFrame(bar)
    bar.to_csv(RES / "committee_bar.csv", index=False)
    verdict = "PASS" if ok_all else "FAIL"

    def tbl(df, cols):
        d = df[cols].copy()
        for c in ("acc", "lo", "hi", "share_of_days"):
            if c in d:
                d[c] = (100 * d[c]).round(1)
        for c in ("per_year",):
            if c in d:
                d[c] = d[c].round(1)
        return d.to_markdown(index=False)

    pa = rec[rec.clock == "phase-averaged"]
    md = ["# The committee: 110 analysts (100 + a Fed desk of 10) vote on EUR/USD direction", "",
          "Code `src/eurusd/committee.py`, test `experiments/70_committee.py`, results `experiments/results/arms/committee_*`.",
          "Design, majority classes and keep bar were written into the module before the first run (2026-11-17). Trial 1: 100 analysts. "
          "Trial 2 (same day, owner's request): a Fed-meeting school of 10 analysts added, nothing else changed.", "",
          f"## Verdict against the declared bar: **{verdict}**", "", bar.to_markdown(index=False), "",
          "## Effect of the Fed desk (clear or strong majority, with and without the 10 Fed analysts)", "",
          tbl(cmp_, ["who", "h", "era", "n_indep", "acc", "lo", "hi", "per_year"]), "",
          "## The Fed desk on its own (majority of the Fed analysts with a view)", "", tbl(fed_alone, ["who", "h", "era", "n_indep", "acc", "lo", "hi", "share_of_days"]), "",
          "## The ten Fed analysts one by one, 2010-26", "",
          tbl(lg[lg.school == "FED"], ["analyst", "h", "n_indep", "acc", "lo", "hi", "share_of_days"]), "",
          "## What a majority was worth (walk-forward, out of sample)", "",
          "`n_indep` = independent calls (calls on one non-overlapping grid, averaged over all grid phases); `lo`-`hi` = 95 % Wilson range on that count; "
          "`share_of_days` = how often the committee was in that class.", ""]
    for h in C.HORIZONS:
        md += [f"### Horizon {h} sessions", "", tbl(pa[pa.h == h], ["cls", "era", "n_days", "n_indep", "acc", "lo", "hi", "per_year", "share_of_days"]), ""]
    md += ["## Benchmarks on the same folds", "", tbl(bench, ["who", "h", "era", "n_indep", "acc", "lo", "hi", "per_year", "share_of_days"]), "",
           "## Stale copies (the vote of 63 / 126 sessions ago, scored on today's outcome)", "",
           tbl(stale[(stale.clock == "phase-averaged") & (stale.cls.isin(["clear+strong", "any majority"]))], ["who", "h", "cls", "era", "n_indep", "acc", "lo", "hi"]), "",
           "## Does the committee add to the three-signal agreement rule?", "", tbl(cond, ["h", "era", "case", "n_indep", "acc", "lo", "hi", "per_year"]), "",
           "## Null: the same machine on labels shifted by years (nothing to find)", "", tbl(null, ["shift", "h", "n_indep", "acc", "lo", "hi"]), "",
           "## Look-ahead control", "",
           f"View columns from a frame cut at 2018-12-31 against the full frame, last 250 sessions: {int(((trunc.max_abs_diff > 1e-9) | (trunc.nan_mismatch > 0)).sum())} of {len(trunc)} columns differ.", "",
           "## League table of the analysts, 1 month, 2010-26 (only analysts with at least 10 independent calls)", ""]
    l21 = lg[(lg.h == 21) & (lg.n_indep >= 10)].sort_values("acc", ascending=False)
    md += [tbl(l21, ["analyst", "school", "prior", "n_indep", "acc", "lo", "hi", "share_of_days"]), ""]
    (ROOT / "reports" / "committee.md").write_text("\n".join(md))
    print("\nVERDICT", verdict)
    print("\nFed effect:\n", cmp_.assign(acc=(100 * cmp_.acc).round(1))[["who", "h", "era", "n_indep", "acc", "per_year"]].to_string(index=False))
    print("\nFed desk alone:\n", fed_alone.assign(acc=(100 * fed_alone.acc).round(1))[["h", "era", "n_indep", "acc", "share_of_days"]].to_string(index=False))
    fl = lg[lg.school == "FED"]
    print("\nFed analysts:\n", fl.assign(acc=(100 * fl.acc).round(1), lo=(100 * fl.lo).round(0), hi=(100 * fl.hi).round(0))[["analyst", "h", "n_indep", "acc", "lo", "hi", "share_of_days"]].to_string(index=False))
    print(bar.to_string(index=False))
    print("\nrecord (phase-averaged):\n", pa.assign(acc=(100 * pa.acc).round(1), lo=(100 * pa.lo).round(1), hi=(100 * pa.hi).round(1))[["h", "cls", "era", "n_indep", "acc", "lo", "hi", "per_year", "share_of_days"]].to_string(index=False))
    print("\nbenchmarks:\n", bench.assign(acc=(100 * bench.acc).round(1))[["who", "h", "era", "n_indep", "acc", "per_year"]].to_string(index=False))
    print("\nstale:\n", stale[(stale.clock == "phase-averaged") & (stale.cls == "clear+strong")].assign(acc=lambda d: (100 * d.acc).round(1))[["who", "h", "era", "n_indep", "acc"]].to_string(index=False))
    print("\nvs rule:\n", cond.assign(acc=(100 * cond.acc).round(1))[["h", "era", "case", "n_indep", "acc"]].to_string(index=False))
    print("\nnull:\n", null.assign(acc=(100 * null.acc).round(1))[["shift", "h", "n_indep", "acc"]].to_string(index=False))


if __name__ == "__main__":
    main()
