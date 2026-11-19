"""The vote: 100 bots, each trained differently and each doing its own research, vote UP or DOWN on EUR/USD and
each gives a lower and an upper level. The count is the prediction; no entries, no take-profit, no stop.

DECLARED BEFORE THE FIRST RUN (2026-11-17, owner's design; one design, fixed seeds, no re-draws):

A bot is defined by its number i (seed 1000 + i) and nothing else. From the seed it draws
  * a DESK: 12 of the ~70 evidence columns (positioning, rates, central banks, Fed meetings, economy, trend, value,
    risk, curve / oil / dollar, calendar, price technicals). A bot never sees the other columns.
  * a way of doing RESEARCH on its desk, repeated every year on its own training history:
      'tstat'    keep the m columns most correlated with the outcome
      'holdout'  learn each column's sign on the first 70 % of its history, keep the m that called the last 30 % best
  * m, the number of columns it keeps: 1, 2, 3 or 5
  * a LEARNER: logistic regression, a shallow decision tree, nearest neighbours, naive Bayes, or a single-signal rule
  * a MEMORY: all history, the last 10 years, or the last 5 years
  * a VOLATILITY GAUGE for its levels: 10-, 21- or 63-session realised volatility, an exponentially weighted one, a
    blend of three windows, or the 14-day average true range.
Every bot MUST vote: P(up) > 50 % is UP, otherwise DOWN. So there are always exactly 100 votes.

Question, for h = 5, 21 and 63 sessions: will EUR/USD close higher or lower than today in h sessions?
Levels, for the same h: LOWER = the level the bot expects the period's lowest price to stay above 8 times in 10;
UPPER = the level it expects the period's highest price to stay below 8 times in 10. Each bot scales the moves it has
seen in its memory by its own volatility gauge. The published level is the median of the 100 bots.

Walk-forward, yearly, expanding (as everywhere in this project): for test year Y a bot researches and fits only on
sessions whose outcome was known before Y-01-01.

How the vote is read (declared): majority side; margin classes by the size of the majority
  thin 50-59 | fair 60-69 | wide 70-79 | very wide 80-100.
What each class was worth is MEASURED and printed next to every vote. A count is not a probability until measured.
Weights (declared, 2 variants): equal; or each bot weighted by its own past out-of-sample hit-rate edge (shrunk by 10
phantom calls, never negative). The weighted vote replaces the equal vote only if it is at least 2 points more accurate
at 21 AND 63 sessions in 2018-26 after being no worse in 2010-17. Otherwise equal.
Level test (declared): each level should hold close to 80 % of the time in 2010-26, 2016-26 and 2023-26 (within
4 points); compared with levels that ignore current volatility.

Known before running (research log, rounds 1-9): direction has been 55-59 % on 2010-26 for every committee built from
this evidence and about 50 % out of time; levels and ranges have been the reliable part.
"""
from __future__ import annotations

import json
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import committee as C  # noqa: E402

RES = C.RES
N_BOTS = 100
DESK = 12
HORIZONS = (5, 10, 21, 63)
TEST_YEARS = list(range(2006, 2027))
MIN_ROWS = 500
LEVEL_Q = 0.80
ERAS = C.ERAS
CLASSES = (("thin", 50, 60), ("fair", 60, 70), ("wide", 70, 80), ("very wide", 80, 101))
LEARNERS = ("logit", "tree", "knn", "bayes", "rule")
RESEARCH = ("tstat", "holdout")
MEMORY = (None, 10, 5)
KEEP = (1, 2, 3, 5)
GAUGES = ("rv10", "rv21", "rv63", "ewma", "blend", "atr14")
EXTRA = ("rsi14", "dist_sma50_atr", "dist_sma200_atr", "adx14", "di_diff", "donch55_pos", "rv_ratio_5_63", "dxy_ret_20",
         "zt_ret_20", "sx5e_ret_20", "usd_jpy_ret_20", "oil_ret_20", "close_in_range", "ret_5d", "ret_10d", "d_us2y_20",
         "d_spread10y_20", "us_curve", "ea_curve", "vix", "cot_net_pct")
NAMES = {"logit": "logistic", "tree": "decision tree", "knn": "nearest neighbours", "bayes": "naive Bayes", "rule": "single signal"}


# ============================================================================= frame
def pool_columns() -> list[str]:
    cols = []
    for _, (_, col, _, _, _) in C.VIEWS.items():
        if col.startswith("@"):
            continue
        cols.append(col.replace("{h}", "21"))
    return list(dict.fromkeys(cols)) + [f"x_{c}" for c in EXTRA]


def build(D: pd.DataFrame | None = None, h1: pd.DataFrame | None = None) -> pd.DataFrame:
    warnings.filterwarnings("ignore")
    if D is None:
        from eurusd.data import load_ohlc
        D = pd.read_parquet(C.SW.PROC / "features_daily.parquet")
        h1 = load_ohlc("H1").loc["2003":]
        h1 = h1[~h1.index.duplicated(keep="last")]
    X = C.build_frame(D, h1)
    Dj = D.copy()
    Dj.index = pd.DatetimeIndex(Dj.index).as_unit("us")
    j = Dj.reindex(X.index)
    for c in EXTRA:
        X[f"x_{c}"] = j[c]
    lc = np.log(X["__close"])
    r = lc.diff()
    ct = X["__ct"]
    hist = (X["__src"] == "histdata")
    hi, lo = X["__high"].where(hist), X["__low"].where(hist)
    for h in HORIZONS:
        X[f"y{h}"] = np.sign(lc.shift(-h) - lc)
        X[f"yend{h}"] = ct.shift(-h)
        fmin = lo[::-1].rolling(h, min_periods=h).min()[::-1].shift(-1)      # lowest low of the next h sessions
        fmax = hi[::-1].rolling(h, min_periods=h).max()[::-1].shift(-1)
        X[f"dn{h}"] = np.log(fmin / X["__close"])
        X[f"up{h}"] = np.log(fmax / X["__close"])
    # volatility gauges (daily log-return units; any constant factor is absorbed by each bot's own quantiles)
    X["g_rv10"], X["g_rv21"], X["g_rv63"] = r.rolling(10).std(), r.rolling(21).std(), r.rolling(63).std()
    X["g_ewma"] = np.sqrt((r ** 2).ewm(alpha=0.06, adjust=False).mean())
    X["g_blend"] = (r.rolling(5).std() + X["g_rv21"] + X["g_rv63"]) / 3
    X["g_atr14"] = (j["atr14_pips"] * 1e-4 / X["__close"])
    return X


# ============================================================================= the bots
def spec(i: int) -> dict:
    rng = np.random.RandomState(1000 + i)
    pool = pool_columns()
    desk = list(rng.choice(pool, size=DESK, replace=False))
    learner = LEARNERS[rng.randint(len(LEARNERS))]
    return {"bot": i, "desk": desk, "research": RESEARCH[rng.randint(2)], "keep": 1 if learner == "rule" else KEEP[rng.randint(len(KEEP))],
            "learner": learner, "memory": MEMORY[rng.randint(3)], "gauge": GAUGES[rng.randint(len(GAUGES))], "depth": int(rng.randint(2, 4))}


SPECS = [spec(i) for i in range(N_BOTS)]


def _research(Z: np.ndarray, y: np.ndarray, how: str, m: int) -> list[int]:
    """The bot's own research: which of its desk columns to trust. Z, y = its training history (time order)."""
    k = Z.shape[1]
    if how == "tstat":
        score = np.array([abs(np.corrcoef(Z[:, c], y)[0, 1]) if Z[:, c].std() > 0 else 0.0 for c in range(k)])
    else:
        cut = int(0.7 * len(y))
        score = np.zeros(k)
        for c in range(k):
            a, b = Z[:cut, c], Z[cut:, c]
            if a.std() == 0:
                continue
            sgn = np.sign(np.corrcoef(a, y[:cut])[0, 1]) or 1.0
            act = b != 0
            score[c] = ((np.sign(b[act]) * sgn) == y[cut:][act]).mean() if act.sum() > 30 else 0.0
    score = np.nan_to_num(score)
    return list(np.argsort(-score)[:m])


def _fit_predict(learner: str, depth: int, A: np.ndarray, y: np.ndarray, B: np.ndarray) -> np.ndarray:
    yy = (y > 0).astype(int)
    if yy.min() == yy.max():
        return np.full(len(B), float(yy[0]))
    if learner in ("logit", "rule"):
        from sklearn.linear_model import LogisticRegression
        mdl = LogisticRegression(C=0.1, max_iter=200)
    elif learner == "tree":
        from sklearn.tree import DecisionTreeClassifier
        mdl = DecisionTreeClassifier(max_depth=depth, min_samples_leaf=max(25, len(yy) // 20), random_state=0)
    elif learner == "knn":
        from sklearn.neighbors import KNeighborsClassifier
        mdl = KNeighborsClassifier(n_neighbors=max(15, int(np.sqrt(len(yy)))))
    else:
        from sklearn.naive_bayes import GaussianNB
        mdl = GaussianNB()
    mdl.fit(A, yy)
    return mdl.predict_proba(B)[:, 1]


def run_bot(X: pd.DataFrame, sp: dict, h: int, start: pd.Timestamp, rows: np.ndarray) -> dict:
    """One bot, one fold: research + fit on outcomes known before `start`, then P(up) and levels for `rows`."""
    y = X[f"y{h}"].values.astype(float)
    known = (X[f"yend{h}"] < start).values & np.isfinite(y) & (y != 0)
    if sp["memory"]:
        known &= (X["__ct"] >= start - pd.DateOffset(years=sp["memory"])).values
    n = int(rows.sum())
    out = {"p": np.full(n, np.nan), "lo": np.full(n, np.nan), "hi": np.full(n, np.nan), "kept": []}
    M = X[sp["desk"]].values.astype(float)
    tr = M[known]
    if len(tr) >= MIN_ROWS:
        mu, sd = np.nanmean(tr, axis=0), np.nanstd(tr, axis=0)
        ok = np.isfinite(sd) & (sd > 0) & (np.isfinite(tr).mean(axis=0) > 0.5)
        if ok.any():
            Z = np.nan_to_num(np.clip((M[:, ok] - mu[ok]) / sd[ok], -3, 3))
            keep = _research(Z[known], y[known], sp["research"], sp["keep"])
            out["kept"] = [np.array(sp["desk"])[ok][c] for c in keep]
            out["p"] = _fit_predict(sp["learner"], sp["depth"], Z[known][:, keep], y[known], Z[rows][:, keep])
    # levels: the moves of its memory, scaled by its own volatility gauge
    g = X[f"g_{sp['gauge']}"].values.astype(float)
    dn, up = X[f"dn{h}"].values / (g * np.sqrt(h)), X[f"up{h}"].values / (g * np.sqrt(h))
    kl = (X[f"yend{h}"] < start).values & np.isfinite(dn) & np.isfinite(up)
    if sp["memory"]:
        kl &= (X["__ct"] >= start - pd.DateOffset(years=sp["memory"])).values
    if kl.sum() >= MIN_ROWS:
        qlo, qhi = np.quantile(dn[kl], 1 - LEVEL_Q), np.quantile(up[kl], LEVEL_Q)
        c = X["__close"].values[rows]
        out["lo"] = c * np.exp(qlo * g[rows] * np.sqrt(h))
        out["hi"] = c * np.exp(qhi * g[rows] * np.sqrt(h))
    return out


def run_fold(X: pd.DataFrame, h: int, start: pd.Timestamp, rows: np.ndarray) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, list]:
    idx = X.index[rows]
    P, LO, HI, kept = {}, {}, {}, []
    for sp in SPECS:
        o = run_bot(X, sp, h, start, rows)
        P[sp["bot"]], LO[sp["bot"]], HI[sp["bot"]] = o["p"], o["lo"], o["hi"]
        kept.append(o["kept"])
    return pd.DataFrame(P, index=idx), pd.DataFrame(LO, index=idx), pd.DataFrame(HI, index=idx), kept


def walk_forward(X: pd.DataFrame, h: int, years=TEST_YEARS, verbose: bool = True):
    Ps, Ls, Hs = [], [], []
    for Y in years:
        rows = np.asarray(X.index.year == Y)
        if not rows.any():
            continue
        p, lo, hi, _ = run_fold(X, h, pd.Timestamp(f"{Y}-01-01", tz="UTC"), rows)
        Ps.append(p); Ls.append(lo); Hs.append(hi)
        if verbose:
            print(f"  h={h} year {Y}: {int(p.notna().any(axis=0).sum())} bots voting", flush=True)
    return pd.concat(Ps), pd.concat(Ls), pd.concat(Hs)


# ============================================================================= the count
def count(P: pd.DataFrame, W: pd.DataFrame | None = None) -> pd.DataFrame:
    """Votes per session. A bot with no model yet does not vote (early years only)."""
    up = (P > 0.5)
    dn = (P <= 0.5) & P.notna()
    if W is None:
        nu, nd = up.sum(axis=1).astype(float), dn.sum(axis=1).astype(float)
    else:
        nu, nd = (up * W).sum(axis=1), (dn * W).sum(axis=1)
    tot = (nu + nd).replace(0, np.nan)
    pct = 100 * np.maximum(nu, nd) / tot
    side = np.sign(nu - nd)
    cls = pd.Series("none", index=P.index, dtype=object)
    for name, a, b in CLASSES:
        cls[(pct >= a) & (pct < b) & (side != 0)] = name
    return pd.DataFrame({"up": up.sum(axis=1), "down": dn.sum(axis=1), "pct": pct, "side": side, "cls": cls})


def class_of(pct: float) -> str:
    return next((n for n, a, b in CLASSES if a <= pct < b), "none")


# ============================================================================= live
def live(refresh: bool = True) -> dict:
    from eurusd.exposure import _daily_frame
    from eurusd.live_data import load_h1_live
    notes = []
    if refresh:
        from eurusd.refresh import refresh_macro
        notes = refresh_macro() + [C.refresh_fed_target()]
    D = _daily_frame(refresh)
    X = build(D, load_h1_live(refresh=False))
    last = np.zeros(len(X), dtype=bool)
    last[-1] = True
    now = X["__ct"].iloc[-1] + pd.Timedelta(seconds=1)
    rec = pd.read_csv(RES / "bots_record.csv") if (RES / "bots_record.csv").exists() else pd.DataFrame()
    lev = pd.read_csv(RES / "bots_levels.csv") if (RES / "bots_levels.csv").exists() else pd.DataFrame()
    out = {"asof": str(X["__ct"].iloc[-1]), "price": float(X["__close"].iloc[-1]), "refresh": notes, "horizons": {}}
    alt = {}
    try:      # round 13: event-adjusted, more even levels (confirmed on six other markets, thin margin): shown beside the bots' levels
        from eurusd.arms import sharper_levels as SL
        Xs = SL.build(D, load_h1_live(refresh=False))
        ev = SL.event_times()
        cal_end = min(pd.Timestamp(int(v.max()), unit="ns", tz="UTC") for k, v in ev.items() if k in ("ecb", "nfp", "cpi"))
        for h in HORIZONS:
            # the method counts the scheduled events inside the window: usable only while the calendars cover it
            if X["__ct"].iloc[-1] + pd.offsets.BDay(h) <= cal_end:
                alt[h] = SL.levels(Xs, h, name="har_rv_ev")
            else:
                out["refresh"].append(f"event-adjusted levels for {h} sessions unavailable: the event calendars end {cal_end.date()}; the bots' levels are published instead")
    except Exception as e:
        out["refresh"].append(f"event-adjusted levels unavailable: {type(e).__name__}")
    for h in HORIZONS:
        P, LO, HI, kept = run_fold(X, h, now, last)
        t = count(P).iloc[0]
        r = {}
        if len(rec):
            q = rec[(rec.h == h) & (rec.cls == t["cls"]) & (rec.weights == "equal")]
            r = {e: q[q.era == e].iloc[0].to_dict() for e in q.era.unique()}
        lv = {}
        if len(lev):
            q = lev[(lev.h == h) & (lev.kind == "bots")]
            lv = {e: q[q.era == e].iloc[0].to_dict() for e in q.era.unique()}
        bots = [{"bot": sp["bot"], "vote": ("up" if P.iloc[0][sp["bot"]] > 0.5 else "down") if P.iloc[0][sp["bot"]] == P.iloc[0][sp["bot"]] else "none",
                 "p_up": float(P.iloc[0][sp["bot"]]), "learner": sp["learner"], "memory": sp["memory"] or "all", "research": sp["research"],
                 "trusts": list(k), "lower": float(LO.iloc[0][sp["bot"]]), "upper": float(HI.iloc[0][sp["bot"]])} for sp, k in zip(SPECS, kept)]
        out["horizons"][h] = {"up": int(t["up"]), "down": int(t["down"]), "pct": float(t["pct"]), "side": float(t["side"]), "cls": t["cls"],
                              "lower": float(np.nanmedian(LO.iloc[0])), "upper": float(np.nanmedian(HI.iloc[0])),
                              "lower_range": [float(np.nanquantile(LO.iloc[0], 0.1)), float(np.nanquantile(LO.iloc[0], 0.9))],
                              "upper_range": [float(np.nanquantile(HI.iloc[0], 0.1)), float(np.nanquantile(HI.iloc[0], 0.9))],
                              "event_adjusted": list(map(float, alt[h])) if h in alt else None,
                              "bots_lower": float(np.nanmedian(LO.iloc[0])), "bots_upper": float(np.nanmedian(HI.iloc[0])),
                              "record": r, "level_record": lv, "bots": bots}
    # round 14: the wide band, both sides holding together 8 times in 10 (bots' levels stretched by a tested factor)
    try:
        jb = pd.read_csv(RES / "bots_joint_band.csv")
        for h, r in out["horizons"].items():
            k = float(jb[(jb.h == h) & (jb.era == "live")]["avg_factor"].iloc[0])
            p0 = out["price"]
            r["band"] = [p0 * (r["bots_lower"] / p0) ** k, p0 * (r["bots_upper"] / p0) ** k]
            r["band_held"] = float(jb[(jb.h == h) & (jb.era == "2010-26")]["both_held"].iloc[0])
    except Exception:
        pass
    # round 16: the same band at 90 and 95 % confidence, calibrated at 5 and 21 sessions only (too wide at 63)
    try:
        bc = pd.read_csv(RES / "bots_band_confidence.csv")
        for h, r in out["horizons"].items():
            if h in (5, 10, 21) and "bots_lower" in r:
                p0 = out["price"]
                r["bands_hi"] = {}
                for t in (0.90, 0.95):
                    k = float(bc[(bc.h == h) & (bc.era == "live") & (bc.target == t)]["avg_factor"].iloc[0])
                    held = float(bc[(bc.h == h) & (bc.era == "2010-26") & (bc.target == t)]["both_held"].iloc[0])
                    r["bands_hi"][str(int(100 * t))] = [p0 * (r["bots_lower"] / p0) ** k, p0 * (r["bots_upper"] / p0) ** k, held]
    except Exception:
        pass
    # owner's decision 2026-11-18: the event-adjusted levels are the published ones where they can be computed (5, 21 sessions)
    for h, r in out["horizons"].items():
        if r.get("event_adjusted"):
            r["lower"], r["upper"] = r["event_adjusted"]
            r["levels_from"] = "event-adjusted"
        else:
            r["levels_from"] = "bots"
    return out


def format_vote(o: dict, detail: bool = True) -> str:
    names = {5: "1 WEEK", 10: "2 WEEKS", 21: "1 MONTH", 63: "3 MONTHS"}
    L = [f"EUR/USD VOTE of {N_BOTS} bots | session close {o['asof'][:16]} UTC | price {o['price']:.4f}"]
    for h, r in o["horizons"].items():
        if h == 63 and r.get("levels_from") == "bots":
            pass
        side = "UP" if r["side"] > 0 else ("DOWN" if r["side"] < 0 else "TIED")
        L.append(f"\n{names[h]}: {r['up']} UP / {r['down']} DOWN  ->  {side}   |   lower level {r['lower']:.4f}   upper level {r['upper']:.4f}")
        rec = (r["record"] or {}).get("2010-26")
        if rec and rec.get("n_indep", 0) and rec["acc"] == rec["acc"]:
            L.append(f"  A {r['cls']} majority like this was right {100 * rec['acc']:.0f} % of the time in 2010-26 ({rec['n_indep']:.0f} independent votes, "
                     f"95 % range {100 * rec['lo']:.0f}-{100 * rec['hi']:.0f} %)"
                     + "".join(f"; {100 * r['record'][e]['acc']:.0f} % in {e}" for e in ("2016-26", "2023-26") if e in r["record"] and r["record"][e]["acc"] == r["record"][e]["acc"]))
        lv = (r["level_record"] or {}).get("2010-26")
        if r.get("levels_from") == "event-adjusted":
            L.append(f"  Levels: event-adjusted method (on six other markets each level held 78-82 % of the time, evenly in calm and volatile markets and in event weeks; "
                     f"not separately proven on EUR/USD). The bots' own levels: {r['bots_lower']:.4f} / {r['bots_upper']:.4f}")
        elif lv:
            L.append(f"  Levels: the low stayed above the lower level {100 * lv['lower_held']:.0f} % of the time and the high below the upper level "
                     f"{100 * lv['upper_held']:.0f} % (2010-26); both held {100 * lv['both_held']:.0f} %")
        if r.get("band"):
            L.append(f"  Wide band: {r['band'][0]:.4f} to {r['band'][1]:.4f} (the whole period's price action stayed inside such a band {100 * r['band_held']:.0f} % of the time, 2010-26)")
        if r.get("bands_hi"):
            L.append("  Rarely breached: " + " | ".join(f"{int(k)} %: {v[0]:.4f} to {v[1]:.4f} (held {100 * v[2]:.0f} %)" for k, v in r["bands_hi"].items()))
        if detail:
            df = pd.DataFrame(r["bots"])
            by = df[df.vote != "none"].groupby("learner")["vote"].value_counts().unstack(fill_value=0).reindex(columns=["up", "down"], fill_value=0)
            L.append("  By method: " + "; ".join(f"{NAMES[k]} {int(by.loc[k, 'up'])} up / {int(by.loc[k, 'down'])} down" for k in LEARNERS if k in by.index))
            tr = pd.Series([c for b in r["bots"] for c in b["trusts"]]).value_counts().head(5)
            L.append("  Evidence the bots chose most: " + ", ".join(f"{k.replace('x_', '')} ({v})" for k, v in tr.items()))
    L.append("\nHow to read it: over 2010-26 the direction vote was right 50 % at one week, 52 % at one month and 53 % at three months, "
             "and a bigger majority was no more reliable than a small one, so the count is close to a coin flip. "
             "The levels are the reliable part: each held about 8 times in 10 in every period tested, less often in a strongly trending year. "
             "In quiet markets they held nearer 7.5 in 10 and in volatile ones 8.5 in 10; one-week levels held a few points less often in weeks with a Fed or ECB meeting, payrolls or CPI.")
    return "\n".join(L)


def one_line(o: dict) -> str:
    parts = []
    for h, r in o["horizons"].items():
        side = "UP" if r["side"] > 0 else ("DOWN" if r["side"] < 0 else "TIED")
        parts.append(f"{h}d {max(r['up'], r['down'])}-{min(r['up'], r['down'])} {side}, levels {r['lower']:.4f} / {r['upper']:.4f}")
    return f"VOTE ({N_BOTS} bots): " + " | ".join(parts)


if __name__ == "__main__":
    o = live(refresh="--no-refresh" not in sys.argv)
    print(format_vote(o))
    if "--json" in sys.argv:
        print(json.dumps(o, indent=1, default=str))
