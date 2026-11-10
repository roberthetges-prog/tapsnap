"""ARM E - event-driven prediction of EUR/USD around scheduled macro releases.

One decision per event (not per bar). Three decision grids, each walk-forward per `eurusd.wf`:
  * POST  : decision 5 minutes after the release (first M5 jump observed), hold 1h / 4h / to 21:00 UTC.
            Features: standardised surprise (EUR/USD-direction aligned), first 5-min jump, jump x surprise,
            pre-release 24h drift, positioning (cot_z52), 2y-spread trend, vol regime, previous release's reaction,
            central-bank rate change, event-type dummies.
  * PRE   : decision 24h before the release, hold until the bar before the release (expectation proxies:
            d_us2y_5, d_spread2y_5/20, policy_diff, cot_z52, ret_5d/21d, fv_resid_z, vol, previous pre-drift).
  * DIV   : decision at the close of the 5th session after each FOMC / ECB decision; the change in the 2y spread
            over those sessions (ECB-vs-Fed repricing) as a signal for the next 5 / 10 sessions.
Costs: each decision is a round trip (entry + exit at the horizon), so 2 x cost per unit position; this equals
`wf.pnl_from_positions` applied to the (entry, exit) pair of every trade (asserted in `run`).

Selection rule, declared before any OOS result was looked at: the final variant is the one with the highest
2010-2015 net Sharpe at 1.2 pips among variants with >= 100 OOS decisions in 2010-2015; its full record is reported.
All thresholds are fixed rules: a trade is taken only when |forecast| > round-trip cost at 1.2 pips (in bp), and the
same positions are kept for the 0.6-pip sensitivity run.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

from eurusd.data import load_ohlc
from eurusd.wf import YEARS, pnl_from_positions, report, walk_forward

ROOT = Path(__file__).resolve().parents[3]
MACRO = ROOT / "data" / "macro"
PROC = ROOT / "data" / "processed"
RES = ROOT / "experiments" / "results" / "arms"
ARM = "events"
COST_HEADLINE = 1.2

KINDS = ["nfp", "cpi", "retail", "ism", "gdp", "pce", "fomc", "ecb"]
KIND_PRIORITY = {k: i for i, k in enumerate(["fomc", "ecb", "nfp", "cpi", "pce", "gdp", "retail", "ism"])}
# ForexFactory event name -> (kind, sign of EUR/USD response to a positive (actual > forecast) surprise)
FF_EVENTS = {"Non-Farm Employment Change": ("nfp", -1), "CPI m/m": ("cpi", -1), "Core CPI m/m": ("cpi", -1),
             "Retail Sales m/m": ("retail", -1), "ISM Manufacturing PMI": ("ism", -1), "Advance GDP q/q": ("gdp", -1),
             "Core PCE Price Index m/m": ("pce", -1), "Federal Funds Rate": ("fomc", -1), "Main Refinancing Rate": ("ecb", +1)}
ET_RULE_HOUR = {"nfp": (8, 30), "cpi": (8, 30), "retail": (8, 30), "gdp": (8, 30), "pce": (8, 30), "ism": (10, 0)}

CTX_DAILY = ["cot_z52", "d_spread2y_20", "d_spread2y_5", "d_us2y_5", "rv_21d_bp", "vix", "fv_resid_z", "ret_5d", "ret_21d",
             "policy_diff", "dist_sma50_atr", "cot_d4"]


# ------------------------------------------------------------------ data helpers
def _num(x):
    if pd.isna(x):
        return np.nan
    s = str(x).replace("%", "").replace(",", "").replace("<", "").strip()
    m = 1e3 if s.endswith("K") else (1e6 if s.endswith("M") else (1e9 if s.endswith("B") else 1))
    try:
        return float(s.rstrip("KMB")) * m
    except ValueError:
        return np.nan


def _m5_close() -> pd.Series:
    """M5 closes indexed by bar END (UTC); asof lookups give the last traded price at a time."""
    m5 = load_ohlc("M5")
    px = m5["close"].copy()
    px.index = px.index + pd.Timedelta(minutes=5)
    return px


def _asof(px: pd.Series, times: pd.DatetimeIndex, tol: pd.Timedelta | None = None) -> np.ndarray:
    """Last price at or before each time (NaN when the last bar is older than tol)."""
    idx = px.index.values
    t = pd.DatetimeIndex(times).values
    pos = np.searchsorted(idx, t, side="right") - 1
    ok = pos >= 0
    out = np.full(len(t), np.nan)
    out[ok] = px.values[pos[ok]]
    if tol is not None:
        age = t - idx[np.maximum(pos, 0)]
        out[ok & (age > np.timedelta64(tol))] = np.nan
    return out


def _next_close_2100(t: pd.DatetimeIndex, min_hold: pd.Timedelta = pd.Timedelta(hours=1)) -> pd.DatetimeIndex:
    """Next 21:00 UTC at least min_hold after t (NY-close proxy, summer 17:00 / winter 16:00 New York)."""
    base = (t + min_hold).floor("D") + pd.Timedelta(hours=21)
    return pd.DatetimeIndex(np.where(base >= t + min_hold, base, base + pd.Timedelta(days=1)))


def _ff_surprises() -> pd.DataFrame:
    """One row per (date, kind): EUR/USD-aligned standardised surprise. The standardisation sd is the expanding sd of past
    surprises of the same series (shifted, so each z uses earlier releases only). CPI and Core CPI are averaged."""
    e = pd.read_csv(MACRO / "events.csv")
    e = e[(e.has_time == True) & e.source.str.startswith("ff_") & e.event.isin(FF_EVENTS)].copy()
    e = e[np.where(e.event == "Main Refinancing Rate", e.currency == "EUR", e.currency == "USD")]
    e["t"] = pd.to_datetime(e.datetime_utc, utc=True)
    e["date"] = e.t.dt.tz_convert("America/New_York").dt.date
    e["a"], e["f"] = e.actual.map(_num), e.forecast.map(_num)
    e = e[e.a.notna() & e.f.notna()]
    out = []
    for name, (kind, sgn) in FF_EVENTS.items():
        s = e[e.event == name].sort_values("t").drop_duplicates("date", keep="first").copy()
        raw = s.a - s.f
        sd = raw.expanding(min_periods=6).std().shift(1)
        s["z"] = sgn * raw / sd.replace(0, np.nan)
        s["kind"] = kind
        out.append(s[["date", "kind", "z", "t"]].rename(columns={"t": "ff_time"}))
    z = pd.concat(out)
    return z.groupby(["date", "kind"]).agg(z=("z", "mean"), ff_time=("ff_time", "first")).reset_index()


def event_table() -> pd.DataFrame:
    """All event decisions: UTC time, kind, aligned surprise z (NaN if unknown), central-bank rate change (pct points)."""
    rows = []
    # --- US data releases: dates from ForexFactory (actual/forecast) and BLS (2017-2026 verified, no values), ET-rule times
    sur = _ff_surprises()
    us = sur[sur.kind.isin(ET_RULE_HOUR)].copy()
    bls = pd.read_csv(MACRO / "us_bls_releases.csv")
    bls["t"] = pd.to_datetime(bls.release_utc, utc=True)
    bls = bls[bls.release.isin(["Employment Situation", "CPI"])]
    bls["kind"] = bls.release.map({"Employment Situation": "nfp", "CPI": "cpi"})
    bls["date"] = bls.t.dt.tz_convert("America/New_York").dt.date
    us = us.merge(bls[["date", "kind", "t"]].rename(columns={"t": "bls_time"}), on=["date", "kind"], how="outer")
    us = us[us.date.map(lambda d: d.year) >= 2010]
    ny = pd.DatetimeIndex([pd.Timestamp(d) for d in us.date]).tz_localize("America/New_York")
    rule = pd.DatetimeIndex([n.replace(hour=ET_RULE_HOUR[k][0], minute=ET_RULE_HOUR[k][1]) for n, k in zip(ny, us.kind)]).tz_convert("UTC")
    us["time"] = pd.DatetimeIndex(np.where(us.bls_time.notna(), us.bls_time, rule)).tz_localize("UTC") if us.bls_time.dt.tz is None else \
        pd.DatetimeIndex([b if pd.notna(b) else r for b, r in zip(us.bls_time, rule)])
    mism = us[us.ff_time.notna() & (us.ff_time.dt.year <= 2023) & ((us.ff_time - us.time).abs() > pd.Timedelta(minutes=1))]
    print(f"  event_table: {len(us)} US data events, {len(mism)} archive-time/ET-rule mismatches (ET rule used)", flush=True)
    for r in us.itertuples():
        rows.append({"time": r.time, "kind": r.kind, "sur": r.z, "rate_chg": 0.0})
    # --- FOMC statements (scheduled), rate change from the decision table, surprise from FF 'Federal Funds Rate'
    f = pd.read_csv(MACRO / "fomc_decisions.csv")
    f = f[f.scheduled == True].copy()
    f["t"] = pd.to_datetime(f.statement_utc, utc=True)
    f = f[(f.t >= "2003-01-01") & (f.t <= pd.Timestamp.utcnow())].sort_values("t")
    tgt = f.fed_funds_target.map(_num)
    f["rate_chg"] = tgt.diff().fillna(0.0)
    fsur = sur[sur.kind == "fomc"].set_index("date").z
    for r in f.itertuples():
        d = r.t.tz_convert("America/New_York").date()
        rows.append({"time": r.t, "kind": "fomc", "sur": fsur.get(d, np.nan), "rate_chg": float(r.rate_chg)})
    # --- ECB decisions (decision time; press conference 30-45 min later lies inside every horizon)
    c = pd.read_csv(MACRO / "ecb_decisions.csv")
    c["t"] = pd.to_datetime(c.decision_utc, utc=True)
    c = c[(c.t >= "2003-01-01") & (c.t <= pd.Timestamp.utcnow())].sort_values("t")
    c["rate_chg"] = c.dfr_after.astype(float).diff().fillna(0.0)
    csur = sur[sur.kind == "ecb"].set_index("date").z
    for r in c.itertuples():
        d = r.t.tz_convert("America/New_York").date()
        rows.append({"time": r.t, "kind": "ecb", "sur": csur.get(d, np.nan), "rate_chg": float(r.rate_chg)})
    ev = pd.DataFrame(rows).dropna(subset=["time"]).sort_values("time").reset_index(drop=True)
    ev = ev[ev.time <= pd.Timestamp.utcnow()]
    # merge simultaneous releases (same minute) into one decision; the surprise is the mean of the aligned z's
    ev["prio"] = ev.kind.map(KIND_PRIORITY)
    g = ev.sort_values(["time", "prio"]).groupby("time")
    ev = pd.DataFrame({"kind": g.kind.first(), "sur": g.sur.mean(), "rate_chg": g.rate_chg.sum(), "n_merged": g.size()}).reset_index()
    return ev


def _daily_context() -> pd.DataFrame:
    D = pd.read_parquet(PROC / "features_daily.parquet")
    ctx = D[CTX_DAILY + ["close_time", "close", "fwd_5d", "fwd_10d", "label_end_5d", "label_end_10d"]].copy()
    ctx["close_time"] = pd.to_datetime(ctx.close_time, utc=True)
    return ctx.sort_values("close_time").reset_index(drop=True)


def _merge_ctx(frame: pd.DataFrame, when: pd.Series, ctx: pd.DataFrame) -> pd.DataFrame:
    """Attach the latest daily-store row whose close_time <= when (features known at that close)."""
    left = pd.DataFrame({"when": pd.DatetimeIndex(when).tz_convert("UTC")}, index=frame.index).sort_values("when")
    left.index.name = "_row"
    m = pd.merge_asof(left.reset_index(), ctx[CTX_DAILY + ["close_time"]], left_on="when", right_on="close_time", direction="backward")
    m = m.set_index("_row").reindex(frame.index)
    for c in CTX_DAILY:
        frame[c] = m[c].values
    return frame


# ------------------------------------------------------------------ decision frames
def build_post(px: pd.Series, ev: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    """Decision at release + 5 min. Labels: fwd_1h, fwd_4h, fwd_close (to 21:00 UTC), fwd_24h."""
    t = pd.DatetimeIndex(ev.time)
    t0 = t + pd.Timedelta(minutes=5)
    X = pd.DataFrame(index=t0)
    X.index.name = "time"
    X["event_time"] = t
    X["kind"] = ev.kind.values
    X["sur"] = ev.sur.values
    X["rate_chg"] = ev.rate_chg.values
    p_pre = _asof(px, t, tol=pd.Timedelta(minutes=30))          # bar ending at the release minute (pre-release price)
    p0 = _asof(px, t0, tol=pd.Timedelta(minutes=5))             # release bar close = entry price
    X["close"] = p0
    X["jump5"] = (np.log(p0) - np.log(p_pre)) * 1e4
    X["pre24"] = (np.log(p_pre) - np.log(_asof(px, t - pd.Timedelta(hours=24), tol=pd.Timedelta(hours=3)))) * 1e4
    X["pre4h"] = (np.log(p_pre) - np.log(_asof(px, t - pd.Timedelta(hours=4), tol=pd.Timedelta(hours=3)))) * 1e4
    # realised 5-min vol over the 24h before the release (bp per 5-min bar)
    r5 = np.log(px).diff() * 1e4
    rv = r5.rolling(288, min_periods=100).std()
    X["rv5m"] = _asof(rv, t, tol=pd.Timedelta(hours=3))
    X["jump_z"] = X.jump5 / X.rv5m.replace(0, np.nan)
    for h in (1, 4, 24):
        X[f"fwd_{h}h"] = (np.log(_asof(px, t0 + pd.Timedelta(hours=h), tol=pd.Timedelta(hours=3))) - np.log(p0)) * 1e4
        X[f"label_end_{h}h"] = t0 + pd.Timedelta(hours=h, minutes=5)
    tc = _next_close_2100(t0)
    X["fwd_closeh"] = (np.log(_asof(px, tc, tol=pd.Timedelta(hours=3))) - np.log(p0)) * 1e4
    X["label_end_closeh"] = tc + pd.Timedelta(minutes=5)
    X["hold_closeh"] = (tc - t0).total_seconds() / 3600
    X = _merge_ctx(X, X.event_time, ctx)
    X["sur_missing"] = X.sur.isna().astype(float)
    X["sur"] = X.sur.fillna(0.0)
    X["jump_x_sur"] = X.jump5 * np.sign(X.sur)
    X["cb"] = X.kind.isin(["fomc", "ecb"]).astype(float)
    for k in KINDS:
        X[f"k_{k}"] = (X.kind == k).astype(float)
    # previous release of the same kind: its reaction (4h), its jump, and whether the market followed the surprise
    g = X.groupby("kind")
    X["prev_react"] = g.fwd_4h.shift(1)
    X["prev_jump"] = g.jump5.shift(1)
    X["prev_follow"] = np.sign(g.fwd_4h.shift(1)) * np.sign(g.sur.shift(1))
    X["prev_react_x_sur"] = X.prev_react * np.sign(X.sur)
    return X[X.close.notna() & X.jump5.notna()]


def build_pre(px: pd.Series, ev: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    """Decision 24h before the release; hold to the bar ending at the release minute."""
    t = pd.DatetimeIndex(ev.time)
    t0 = t - pd.Timedelta(hours=24)
    X = pd.DataFrame(index=t0)
    X.index.name = "time"
    X["event_time"] = t
    X["kind"] = ev.kind.values
    p0 = _asof(px, t0, tol=pd.Timedelta(hours=3))
    p_pre = _asof(px, t, tol=pd.Timedelta(minutes=30))
    X["close"] = p0
    X["fwd_pre"] = (np.log(p_pre) - np.log(p0)) * 1e4
    X["label_end_pre"] = t
    X["ret_24h"] = (np.log(p0) - np.log(_asof(px, t0 - pd.Timedelta(hours=24), tol=pd.Timedelta(hours=3)))) * 1e4
    X = _merge_ctx(X, X.index.to_series(), ctx)
    X["dow"] = t0.dayofweek.astype(float)
    X["cb"] = X.kind.isin(["fomc", "ecb"]).astype(float)
    for k in KINDS:
        X[f"k_{k}"] = (X.kind == k).astype(float)
    X["prev_pre"] = X.groupby("kind").fwd_pre.shift(1)
    return X[X.close.notna() & X.fwd_pre.notna()]


def build_div(ev: pd.DataFrame, ctx: pd.DataFrame) -> pd.DataFrame:
    """Decision at the close of the 5th session after each FOMC / ECB decision."""
    cb = ev[ev.kind.isin(["fomc", "ecb"])]
    ct = ctx.close_time.values
    rows = []
    for r in cb.itertuples():
        i = np.searchsorted(ct, pd.Timestamp(r.time).tz_convert("UTC").to_datetime64()) + 4   # sessions closing after the event: #1 .. #5
        if i >= len(ctx):
            continue
        d = ctx.iloc[i]
        rows.append({"time": d.close_time, "event_time": r.time, "kind": r.kind, "rate_chg": r.rate_chg, "close": d.close,
                     **{c: d[c] for c in CTX_DAILY}, "fwd_5d": d.fwd_5d, "fwd_10d": d.fwd_10d,
                     "label_end_5d": d.label_end_5d, "label_end_10d": d.label_end_10d})
    X = pd.DataFrame(rows).drop_duplicates("time").set_index("time")
    X.index = pd.DatetimeIndex(X.index).tz_convert("UTC")
    X.index.name = "time"
    for c in ("label_end_5d", "label_end_10d"):
        X[c] = pd.to_datetime(X[c], utc=True)
    for k in ("fomc", "ecb"):
        X[f"k_{k}"] = (X.kind == k).astype(float)
    X["spread_x_fomc"] = X.d_spread2y_5 * X.k_fomc
    return X


# ------------------------------------------------------------------ models
ALPHAS = [1.0, 3.0, 10.0, 30.0, 100.0, 300.0, 1000.0, 3000.0]
CS = [0.001, 0.003, 0.01, 0.03, 0.1, 0.3, 1.0]


def _prep(train: pd.DataFrame, feats: list[str]):
    mu = train[feats].mean()
    sd = train[feats].std().replace(0, np.nan).fillna(1.0)
    return mu, sd


def _xmat(df: pd.DataFrame, feats, mu, sd) -> np.ndarray:
    return ((df[feats] - mu) / sd).fillna(0.0).clip(-5, 5).values


def _folds(n: int, k: int = 4):
    """Expanding time-ordered folds over row positions (rows are time-sorted)."""
    edges = np.linspace(0, n, k + 2).astype(int)
    for i in range(1, k + 1):
        yield np.arange(0, edges[i]), np.arange(edges[i], edges[i + 1])


def _winsor(y: pd.Series, lo=0.01, hi=0.99) -> np.ndarray:
    a, b = y.quantile(lo), y.quantile(hi)
    return y.clip(a, b).values


def fit_ridge(train: pd.DataFrame, feats: list[str], target: str) -> dict:
    from sklearn.linear_model import Ridge
    tr = train.sort_index()
    mu, sd = _prep(tr, feats)
    Xm, y = _xmat(tr, feats, mu, sd), _winsor(tr[target])
    best, best_mse = ALPHAS[-1], np.inf
    for a in ALPHAS:
        err = []
        for i_tr, i_va in _folds(len(y)):
            if len(i_tr) < 30 or len(i_va) < 10:
                continue
            m = Ridge(alpha=a).fit(Xm[i_tr], y[i_tr])
            err.append(np.mean((m.predict(Xm[i_va]) - y[i_va]) ** 2))
        mse = np.mean(err) if err else np.inf
        if mse < best_mse:
            best, best_mse = a, mse
    model = Ridge(alpha=best).fit(Xm, y)
    return {"m": model, "mu": mu, "sd": sd, "feats": feats, "alpha": best, "kind": "ridge"}


def fit_logit(train: pd.DataFrame, feats: list[str], target: str) -> dict:
    from sklearn.linear_model import LogisticRegression
    tr = train.sort_index()
    mu, sd = _prep(tr, feats)
    Xm = _xmat(tr, feats, mu, sd)
    y = tr[target].values
    yc = (y > 0).astype(int)
    best, best_ll = CS[0], np.inf
    for C in CS:
        ll = []
        for i_tr, i_va in _folds(len(y)):
            if len(i_tr) < 30 or len(i_va) < 10 or len(set(yc[i_tr])) < 2:
                continue
            m = LogisticRegression(C=C, max_iter=500).fit(Xm[i_tr], yc[i_tr])
            p = np.clip(m.predict_proba(Xm[i_va])[:, 1], 1e-6, 1 - 1e-6)
            ll.append(-np.mean(yc[i_va] * np.log(p) + (1 - yc[i_va]) * np.log(1 - p)))
        v = np.mean(ll) if ll else np.inf
        if v < best_ll:
            best, best_ll = C, v
    model = LogisticRegression(C=best, max_iter=500).fit(Xm, yc)
    return {"m": model, "mu": mu, "sd": sd, "feats": feats, "C": best, "kind": "logit", "scale": float(np.mean(np.abs(y)))}


def fit_lgbm(train: pd.DataFrame, feats: list[str], target: str) -> dict:
    import lightgbm as lgb
    tr = train.sort_index()
    mu, sd = _prep(tr, feats)
    Xm, y = _xmat(tr, feats, mu, sd), _winsor(tr[target])
    m = lgb.LGBMRegressor(n_estimators=150, learning_rate=0.03, num_leaves=4, min_child_samples=25, subsample=0.8, subsample_freq=1,
                          colsample_bytree=0.8, reg_lambda=10.0, num_threads=1, verbose=-1, random_state=0).fit(Xm, y)
    return {"m": m, "mu": mu, "sd": sd, "feats": feats, "kind": "lgbm"}


def predict(model: dict, test: pd.DataFrame) -> np.ndarray:
    Xm = _xmat(test, model["feats"], model["mu"], model["sd"])
    if model["kind"] == "logit":
        return (2 * model["m"].predict_proba(Xm)[:, 1] - 1) * model["scale"]   # expected return proxy in bp
    return model["m"].predict(Xm)


FITTERS = {"ridge": fit_ridge, "logit": fit_logit, "lgbm": fit_lgbm}

# ------------------------------------------------------------------ feature sets
F_POST_NEW = ["sur", "sur_missing", "jump5", "jump_z", "jump_x_sur", "rate_chg"]
F_POST_CTX = ["pre24", "pre4h", "cot_z52", "d_spread2y_20", "d_us2y_5", "rv_21d_bp", "rv5m", "vix", "fv_resid_z", "ret_5d",
              "prev_react", "prev_follow", "prev_react_x_sur"]
F_KIND = [f"k_{k}" for k in KINDS]
F_POST_ALL = F_POST_NEW + F_POST_CTX + F_KIND
F_PRE = ["d_us2y_5", "d_spread2y_5", "d_spread2y_20", "policy_diff", "cot_z52", "cot_d4", "ret_5d", "ret_21d", "ret_24h", "fv_resid_z",
         "rv_21d_bp", "vix", "dist_sma50_atr", "prev_pre", "dow"] + F_KIND
F_DIV = ["d_spread2y_5", "d_us2y_5", "d_spread2y_20", "spread_x_fomc", "rate_chg", "ret_5d", "cot_z52", "fv_resid_z", "k_fomc", "k_ecb"]

# variant: (grid, model, feature set, label column, label_end column, row filter, horizon hours)
VARIANTS = {
    "P1_post_ridge_1h": ("post", "ridge", F_POST_ALL, "fwd_1h", "label_end_1h", None, 1),
    "P2_post_ridge_4h": ("post", "ridge", F_POST_ALL, "fwd_4h", "label_end_4h", None, 4),
    "P3_post_ridge_close": ("post", "ridge", F_POST_ALL, "fwd_closeh", "label_end_closeh", None, None),
    "P4_post_logit_4h": ("post", "logit", F_POST_ALL, "fwd_4h", "label_end_4h", None, 4),
    "P5_post_lgbm_4h": ("post", "lgbm", F_POST_ALL, "fwd_4h", "label_end_4h", None, 4),
    "P6_post_ridge_4h_data_only": ("post", "ridge", F_POST_ALL, "fwd_4h", "label_end_4h", "data", 4),
    "P7_post_ridge_4h_cb_only": ("post", "ridge", F_POST_ALL, "fwd_4h", "label_end_4h", "cb", 4),
    "P8_post_ridge_4h_newinfo_only": ("post", "ridge", F_POST_NEW + F_KIND, "fwd_4h", "label_end_4h", None, 4),
    "P9_post_ridge_4h_context_only": ("post", "ridge", F_POST_CTX + F_KIND, "fwd_4h", "label_end_4h", None, 4),
    "P10_post_ridge_24h": ("post", "ridge", F_POST_ALL, "fwd_24h", "label_end_24h", None, 24),
    "R1_pre_ridge_24h": ("pre", "ridge", F_PRE, "fwd_pre", "label_end_pre", None, 24),
    "R2_pre_ridge_24h_cb_only": ("pre", "ridge", F_PRE, "fwd_pre", "label_end_pre", "cb", 24),
    "D1_div_ridge_10d": ("div", "ridge", F_DIV, "fwd_10d", "label_end_10d", None, 240),
    "D2_div_ridge_5d": ("div", "ridge", F_DIV, "fwd_5d", "label_end_5d", None, 120),
}
COMBINED = {"C1_combo_P2_R1_D1": ["P2_post_ridge_4h", "R1_pre_ridge_24h", "D1_div_ridge_10d"]}


# ------------------------------------------------------------------ harness
def event_pnl(pos: pd.Series, fwd_bp: pd.Series, price: pd.Series, cost_pips: float) -> pd.DataFrame:
    """Round-trip P&L per decision: identical to wf.pnl_from_positions on the (entry, exit) pair of each trade."""
    pos = pos.fillna(0.0)
    cost_bp = cost_pips * 1e-4 / price * 1e4
    turnover = 2.0 * pos.abs()
    gross = pos * fwd_bp
    return pd.DataFrame({"pos": pos, "gross_bp": gross, "net_bp": gross - turnover * cost_bp, "turnover": turnover})


def _check_pnl_equivalence():
    idx = pd.DatetimeIndex(["2015-01-01 12:35", "2015-01-01 16:35"], tz="UTC")
    pos = pd.Series([1.0, 0.0], index=idx)
    fwd = pd.Series([12.0, 0.0], index=idx)
    px = pd.Series([1.2, 1.2], index=idx)
    ref = pnl_from_positions(pos, fwd, px, cost_pips=1.2).net_bp.sum()
    mine = event_pnl(pos.iloc[:1], fwd.iloc[:1], px.iloc[:1], 1.2).net_bp.sum()
    assert abs(ref - mine) < 1e-9, (ref, mine)


def _hurdle(price: pd.Series, cost_pips: float = COST_HEADLINE) -> pd.Series:
    return 2.0 * cost_pips * 1e-4 / price * 1e4


def _ppy(idx: pd.DatetimeIndex) -> float:
    span = max((idx.max() - idx.min()).days / 365.25, 1.0)
    return len(idx) / span


def run_variant(name: str, frames: dict, shuffle: bool = False, shift: int = 0, seed: int = 0, verbose: bool = False) -> pd.DataFrame:
    grid, mname, feats, ycol, ecol, filt, hz = VARIANTS[name]
    df = frames[grid].copy()
    if filt == "data":
        df = df[df.cb == 0]
    elif filt == "cb":
        df = df[df.cb == 1]
    df = df[df[ycol].notna()].sort_index()
    if shift:
        df[feats] = df[feats].shift(shift)        # stale (shift>0) or future (shift<0) features, leak check only
    if shuffle:
        rng = np.random.default_rng(seed)
        df[ycol] = rng.permutation(df[ycol].values)
    fitter = FITTERS[mname]
    pred = walk_forward(df, lambda tr: fitter(tr, feats, ycol), predict, label_end=df[ecol], verbose=verbose)
    out = df.loc[pred.notna(), ["kind", "close", ycol, ecol]].rename(columns={ycol: "fwd_bp", ecol: "label_end", "kind": "event"})
    out["pred"] = pred[pred.notna()]
    out["pos"] = np.sign(out.pred).where(out.pred.abs() > _hurdle(out.close), 0.0)
    out["horizon_h"] = hz if hz is not None else df.loc[out.index, "hold_closeh"].round(2)
    out["variant"] = name
    return out


def _report(out: pd.DataFrame, name: str, cost_pips: float, n_arms: int) -> pd.DataFrame:
    pnl = event_pnl(out.pos, out.fwd_bp, out.close, cost_pips)
    tbl = report(pnl, periods_per_year=_ppy(out.index), name=ARM, n_arms=n_arms)
    tbl.insert(1, "variant", name)
    tbl.insert(2, "cost_pips", cost_pips)
    tbl.insert(3, "ppy", round(_ppy(out.index), 1))
    return tbl


def _agg_row(tbl: pd.DataFrame, period: str, col: str = "sharpe") -> float:
    return float(tbl.loc[tbl.period == period, col].iloc[0])


def build_frames() -> dict:
    px = _m5_close()
    ev = event_table()
    ctx = _daily_context()
    frames = {"post": build_post(px, ev, ctx), "pre": build_pre(px, ev, ctx), "div": build_div(ev, ctx)}
    return frames


def run(cost_pips: float = COST_HEADLINE, save: bool = True, verbose: bool = True):
    """Run every variant walk-forward, pick the final by the pre-declared rule, save positions + report, leak checks."""
    _check_pnl_equivalence()
    frames = build_frames()
    if verbose:
        for k, f in frames.items():
            print(f"  frame {k}: {len(f)} decisions {f.index.min():%Y-%m-%d} .. {f.index.max():%Y-%m-%d}; by kind:",
                  f.kind.value_counts().to_dict(), flush=True)
    outs, tables = {}, []
    n_arms = len(VARIANTS) + len(COMBINED)
    for name in VARIANTS:
        if verbose:
            print(f"variant {name}", flush=True)
        outs[name] = run_variant(name, frames)
        for c in (cost_pips, 0.6):
            tables.append(_report(outs[name], name, c, n_arms))
    for name, parts in COMBINED.items():
        outs[name] = pd.concat([outs[p] for p in parts]).sort_index()
        outs[name]["variant"] = name
        for c in (cost_pips, 0.6):
            tables.append(_report(outs[name], name, c, n_arms))
    rep = pd.concat(tables, ignore_index=True)
    # --- selection rule (declared in the module docstring): best 2010-2015 net Sharpe at headline cost, >= 100 decisions
    sel = rep[(rep.cost_pips == cost_pips) & (rep.period == "2010-2015") & (rep.n >= 100)].sort_values("sharpe", ascending=False)
    final = str(sel.variant.iloc[0])
    rep["final"] = rep.variant == final
    # --- leak checks on the final variant
    base = outs[final] if final in VARIANTS else outs[COMBINED[final][0]]
    chk_name = final if final in VARIANTS else COMBINED[final][0]
    checks = {}
    for lab, kw in (("shuffle_labels", {"shuffle": True}), ("features_shift_+1_stale", {"shift": 1}), ("features_shift_-1_future", {"shift": -1})):
        o = run_variant(chk_name, frames, **kw)
        t = _report(o, f"{chk_name}__{lab}", cost_pips, n_arms)
        checks[lab] = {p: round(_agg_row(t, p), 2) for p in ("2010-2026", "2016-2026", "2023-2026")}
        t["final"] = False
        rep = pd.concat([rep, t], ignore_index=True)
    rep.attrs["final"] = final
    rep.attrs["leak_checks"] = checks
    pos = outs[final][["pos", "fwd_bp", "event", "horizon_h", "close", "label_end", "pred"]].copy()
    pos["net_bp"] = event_pnl(pos.pos, pos.fwd_bp, pos.close, cost_pips).net_bp
    pos = pos[["pos", "fwd_bp", "net_bp", "event", "horizon_h", "label_end", "pred", "close"]]
    if save:
        RES.mkdir(parents=True, exist_ok=True)
        pos.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        pd.concat(outs.values()).to_parquet(RES / f"{ARM}_all_variants_oos.parquet")
    if verbose:
        print("FINAL:", final, checks, flush=True)
    return pos, rep


if __name__ == "__main__":
    pos, rep = run()
    cols = ["variant", "cost_pips", "period", "n", "ppy", "sharpe", "t", "mean_bp", "active_frac", "final"]
    print(rep[rep.period.isin(["2010-2015", "2010-2026", "2016-2026", "2023-2026"])][cols].to_string())
