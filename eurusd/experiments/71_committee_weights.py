"""How should the analysts' votes be weighted? Eight schemes against the plain equal vote (round 8, trial 3-10).

DECLARED BEFORE RUNNING (2026-11-17). Inputs are the walk-forward votes of the 110 analysts saved by
70_committee.py; every weight for year Y uses only sessions whose outcome was known before Y-01-01.

Common call rule for every scheme: weighted net vote S = sum(w_i * v_i) / sum(|w_i| * |v_i|) over the analysts with a
view (v = +1 / -1); CALL when |S| >= 0.30 (the same as a 65 % weighted majority) and at least 20 analysts have a view.

  W0 equal        every analyst with a view counts the same (the committee as it stands)
  W1 track        weight = the analyst's own past hit-rate edge over 50 % (shrunk towards zero by 10 phantom
                  independent calls at 50 %), never negative: analysts with a bad record are muted
  W2 conviction   weight = how far the analyst's own stated probability is from 50 %
  W3 track x conviction
  W4 schools      each of the 11 schools gets the same total weight (stops a crowded school from outvoting the rest)
  W5 event week   x3 for the Fed desk, central-bank and rate-momentum schools when a Fed meeting is within the next
                  5 sessions (x3 for central-bank and rate-momentum when an ECB meeting is); x3 for the Economy
                  school when US payrolls or CPI is within the next 5 sessions
  W6 pattern      weight = the analyst's hit-rate edge on the 250 past sessions whose vote pattern (net vote of each
                  school) was most like today's: 'when the picture looked like this, who was right?'
  W7 learned      ridge regression of the outcome on all votes (penalty = number of training rows): weights may be
                  negative, i.e. an analyst can be used as a contrary indicator
  W8 replay       no analysts at all: the outcomes that followed the 250 most similar past vote patterns; CALL when
                  65 % of them went one way ('if the pattern reappears, do what worked then')

SELECTION RULE: the pick is the scheme with the highest average of its 21- and 42-session phase-averaged accuracy in
2010-2017, among schemes that make at least 6 independent 21-session calls a year there. It REPLACES the equal vote
only if it then beats the equal vote by >= 2 points at BOTH 21 and 42 sessions in 2018-2026 (which it never saw when
picked). Otherwise the equal vote stays. 2010-26 and 2023-26 are reported for information.
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import committee as C  # noqa: E402
from eurusd.arms.swing import wilson  # noqa: E402

RES = C.RES
CALL, K_NEAR, SHRINK_CALLS, EVENT_X, EVENT_DAYS = 0.30, 250, 10, 3.0, 5
ERAS = (("2010-17 (pick)", 2010, 2017), ("2018-26 (confirm)", 2018, 2026), ("2010-26", 2010, 2026), ("2023-26", 2023, 2026))
SCHOOL_OF = {a: C.VIEWS[a.split(":")[0]][0] for a in C.AGENTS}


def acc(side: pd.Series, y: pd.Series, h: int, a: int, b: int) -> dict:
    m = (side.index.year >= a) & (side.index.year <= b) & (side != 0).values & y.notna().values & (y != 0).values
    n = int(m.sum())
    if n == 0:
        return {"n_indep": 0.0, "acc": np.nan, "lo": np.nan, "hi": np.nan, "per_year": 0.0}
    hit = float((side[m] == y[m]).mean())
    ni = n / h
    lo, hi = wilson(int(round(hit * ni)), max(int(round(ni)), 1))
    return {"n_indep": round(ni, 1), "acc": hit, "lo": lo, "hi": hi, "per_year": ni / (b - a + 1)}


def side_from(W: pd.DataFrame, V: pd.DataFrame) -> pd.Series:
    num = (W * V).sum(axis=1)
    den = (W.abs() * V.abs()).sum(axis=1).replace(0, np.nan)
    S = (num / den).fillna(0.0)
    return np.sign(S).where((S.abs() >= CALL) & (V.abs().sum(axis=1) >= C.QUORUM), 0.0)


def school_vector(V: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({s: V[[a for a in C.AGENTS if SCHOOL_OF[a] == s]].mean(axis=1) for s in C.SCHOOLS})


def build(h: int, X: pd.DataFrame, D: pd.DataFrame) -> dict:
    P = pd.read_parquet(RES / f"committee_probs_h{h}.parquet")[C.AGENTS]
    V = pd.DataFrame(np.where(P > 0.5 + C.EPS, 1.0, np.where(P < 0.5 - C.EPS, -1.0, 0.0)), index=P.index, columns=P.columns)
    y = X[f"y{h}"].reindex(P.index)
    yend = X[f"yend{h}"].reindex(P.index)
    conv = (P - 0.5).abs().fillna(0.0)
    ones = pd.DataFrame(1.0, index=P.index, columns=P.columns)
    hitm = ((V.values == y.values[:, None]) & (V.values != 0)).astype(float)
    callm = (V.values != 0).astype(float)
    SV = school_vector(V)
    out = {"W0 equal": side_from(ones, V), "W2 conviction": side_from(conv, V)}
    # W4 schools
    n_sch = pd.Series(SCHOOL_OF).value_counts()
    voters_s = pd.DataFrame({s: V[[a for a in C.AGENTS if SCHOOL_OF[a] == s]].abs().sum(axis=1) for s in C.SCHOOLS})
    W4 = pd.DataFrame({a: 1.0 / voters_s[SCHOOL_OF[a]].replace(0, np.nan) for a in C.AGENTS}).fillna(0.0)
    out["W4 schools"] = side_from(W4, V)
    # W5 event week
    ev = D.reindex(P.index)
    fed = (ev["h_to_fomc"] <= 24 * EVENT_DAYS * 7 / 5).values          # 5 sessions = 7 calendar days
    ecb = (ev["h_to_ecb"] <= 24 * EVENT_DAYS * 7 / 5).values
    eco = ((ev["h_to_nfp"] <= 24 * EVENT_DAYS * 7 / 5) | (ev["h_to_cpi"] <= 24 * EVENT_DAYS * 7 / 5)).values
    W5 = ones.copy()
    for a in C.AGENTS:
        s = SCHOOL_OF[a]
        m = np.ones(len(P))
        if s == "FED":
            m = np.where(fed, EVENT_X, 1.0)
        elif s in ("CB", "RC"):
            m = np.where(fed | ecb, EVENT_X, 1.0)
        elif s == "ECO":
            m = np.where(eco, EVENT_X, 1.0)
        W5[a] = m
    out["W5 event week"] = side_from(W5, V)
    out["_event_days"] = pd.Series(fed, index=P.index)
    # walk-forward weights
    W1 = pd.DataFrame(0.0, index=P.index, columns=P.columns)
    W6, W7 = W1.copy(), W1.copy()
    replay = pd.Series(0.0, index=P.index)
    k = SHRINK_CALLS * h
    for Y in range(2010, 2027):
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC")
        ref = (yend < start).values & y.notna().values & (y != 0).values
        rows = np.where(P.index.year == Y)[0]
        if ref.sum() < 500 or len(rows) == 0:
            continue
        hits, calls = hitm[ref].sum(0), callm[ref].sum(0)
        edge = np.clip((hits + 0.5 * k) / (calls + k) - 0.5, 0, None)
        W1.iloc[rows] = edge if edge.sum() > 0 else 1.0
        # ridge on the votes
        A, b = V.values[ref], y.values[ref]
        beta = np.linalg.solve(A.T @ A + len(b) * np.eye(A.shape[1]), A.T @ b)
        W7.iloc[rows] = beta
        # nearest vote patterns
        R, T = SV.values[ref], SV.values[rows]
        d2 = ((T[:, None, :] - R[None, :, :]) ** 2).sum(-1)
        nn = np.argsort(d2, axis=1)[:, :K_NEAR]
        hR, cR, yR = hitm[ref], callm[ref], y.values[ref]
        e6 = np.clip((hR[nn].sum(1) + 0.5 * k) / (cR[nn].sum(1) + k) - 0.5, 0, None)
        W6.iloc[rows] = e6
        up = (yR[nn] > 0).mean(1)
        replay.iloc[rows] = np.where(up >= 0.65, 1.0, np.where(up <= 0.35, -1.0, 0.0))
    out["W1 track"] = side_from(W1, V)
    out["W3 track x conviction"] = side_from(W1 * conv, V)
    out["W6 pattern"] = side_from(W6, V)
    out["W7 learned"] = side_from(W7, V)
    out["W8 replay"] = replay
    out["_y"] = y
    out["_W1"] = W1
    return out


def main():
    pd.set_option("display.width", 250)
    pd.set_option("display.max_rows", 400)
    X = C.build_frame()
    D = pd.read_parquet(C.SW.PROC / "features_daily.parquet")
    D.index = pd.DatetimeIndex(D.index).as_unit("us")
    rows, sides = [], {}
    for h in C.HORIZONS:
        o = build(h, X, D)
        sides[h] = o
        for name, s in o.items():
            if name.startswith("_"):
                continue
            for era, a, b in ERAS:
                rows.append({"scheme": name, "h": h, "era": era, **acc(s, o["_y"], h, a, b)})
            st = s.shift(63)
            rows.append({"scheme": name + " (63 stale)", "h": h, "era": "2010-26", **acc(st.fillna(0.0), o["_y"], h, 2010, 2026)})
        # event-week detail: equal vote vs event-weighted vote on Fed-week sessions only
        fw = o["_event_days"]
        for name in ("W0 equal", "W5 event week"):
            s = o[name].where(fw, 0.0)
            rows.append({"scheme": name + " | Fed-week sessions only", "h": h, "era": "2010-26", **acc(s, o["_y"], h, 2010, 2026)})
    T = pd.DataFrame(rows)
    T.to_csv(RES / "committee_weights.csv", index=False)
    main_ = T[~T.scheme.str.contains("stale|Fed-week")]
    piv = main_.pivot_table(index="scheme", columns=["h", "era"], values="acc").mul(100).round(1)
    cnt = main_.pivot_table(index="scheme", columns=["h", "era"], values="per_year").round(1)
    print("accuracy %:\n", piv.to_string())
    print("\nindependent calls per year:\n", cnt.to_string())
    # ---- the declared selection
    pick_era, conf_era = ERAS[0][0], ERAS[1][0]
    g = lambda s, h, e, c="acc": float(T[(T.scheme == s) & (T.h == h) & (T.era == e)][c].iloc[0])  # noqa: E731
    cands = [s for s in main_.scheme.unique() if s != "W0 equal" and g(s, 21, pick_era, "per_year") >= 6]
    score = {s: 0.5 * (g(s, 21, pick_era) + g(s, 42, pick_era)) for s in cands}
    pick = max(score, key=score.get)
    gain21 = 100 * (g(pick, 21, conf_era) - g("W0 equal", 21, conf_era))
    gain42 = 100 * (g(pick, 42, conf_era) - g("W0 equal", 42, conf_era))
    replace = gain21 >= 2 and gain42 >= 2
    print(f"\nPICK on 2010-17: {pick} (score {100 * score[pick]:.1f}; equal vote {50 * (g('W0 equal', 21, pick_era) + g('W0 equal', 42, pick_era)):.1f})")
    print(f"CONFIRM on 2018-26: gain over the equal vote {gain21:+.1f} pts at 21 sessions, {gain42:+.1f} pts at 42 -> {'REPLACES the equal vote' if replace else 'equal vote stays'}")
    print("\nstale and Fed-week rows:\n", T[T.scheme.str.contains("stale|Fed-week")].assign(acc=lambda d: (100 * d.acc).round(1), lo=lambda d: (100 * d.lo).round(0), hi=lambda d: (100 * d.hi).round(0))[["scheme", "h", "n_indep", "acc", "lo", "hi"]].to_string(index=False))
    def fmt(df):
        d = df.copy()
        for c in ("acc", "lo", "hi"):
            d[c] = (100 * d[c]).round(1)
        d["per_year"] = d["per_year"].round(1)
        return d.to_markdown(index=False)
    md = ["# Weighting the analysts: eight schemes against the equal vote", "",
          "Test `experiments/71_committee_weights.py`; schemes, call rule and selection rule are in its docstring, written before the run (2026-11-17).", "",
          f"**Pick on 2010-17: {pick}. Confirmation on 2018-26: {gain21:+.1f} points at one month, {gain42:+.1f} at two against the equal vote -> "
          f"{'it replaces the equal vote' if replace else 'the equal vote stays'}.**", "",
          "## Accuracy (%) by scheme, horizon and era", "", piv.to_markdown(), "", "## Independent calls per year", "", cnt.to_markdown(), "",
          "## Selection scores (average of 21- and 42-session accuracy, 2010-17)", "",
          pd.Series({**{"W0 equal": 0.5 * (g('W0 equal', 21, pick_era) + g('W0 equal', 42, pick_era))}, **score}).mul(100).round(1).sort_values(ascending=False).to_frame("score").to_markdown(), "",
          "## Fed-meeting weeks only, and 63-session-stale copies", "", fmt(T[T.scheme.str.contains("stale|Fed-week")][["scheme", "h", "era", "n_indep", "acc", "lo", "hi", "per_year"]]), "",
          "## All rows", "", fmt(main_[["scheme", "h", "era", "n_indep", "acc", "lo", "hi", "per_year"]]), ""]
    (ROOT / "reports" / "committee_weights.md").write_text("\n".join(md))


if __name__ == "__main__":
    main()
