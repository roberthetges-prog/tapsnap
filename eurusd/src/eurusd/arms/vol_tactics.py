"""Arm J ("vol_tactics"): intraday tactics CONDITIONED on a walk-forward forecast of the day's range.

IDEA. Direction is barely predictable, range is strongly predictable. Round 1 tested the Asian-range breakout,
range fades and extension fades unconditionally and all failed after costs. Here every tactic is switched on or off
by the forecast class of the day (quiet / normal / volatile) known at 07:00 London (or at the prior NY close).

STEP 1 - RANGE FORECAST (no direction). One row per NY-close session (22:00 UTC -> 22:00 UTC, the feature store's
session key). Targets: high-low range in pips of (i) the whole session, (ii) the London window 07:00-16:00 London
time. Model: OLS on log(range), refitted every year on rows whose target is known before Y-01-01 (eurusd.wf.walk_forward).
Features known at the session start ("close" forecast): HAR lags (previous session / 5-session / 22-session mean) of
log range, of log realised vol from 5-minute returns and of log London-window range; log VIX (store column, lagged);
scheduled-event dummies for the session (FOMC, ECB, NFP, US CPI; FOMC on the previous session); day-of-week dummies.
The "07:00" forecast adds what is known at 07:00 London: log Asian-session range and realised vol of the same day
(session start -> 07:00 London) and the opening gap. Events: FOMC and ECB decision calendars (full history), BLS
release calendar from 2010 (before 2010: NFP = first Friday of the month, CPI flag = 0). The store's n_high_next_24h
is NOT used: its ForexFactory coverage is uneven (2024-25 nearly empty) and it does not look across weekends.

Day classes (thresholds from the TRAINING window only):
  A  absolute : tercile of the median forecast against the training terciles of the REALISED range
  R  relative : tercile of forecast / mean of the previous 20 realised ranges against the training terciles of the
                same in-sample fitted ratio (quieter / more volatile than the recent norm; balanced within a year)
  C  close    : as A but from the forecast made at the session start for the whole-session range

STEP 2 - TACTICS (M15 bars, eurusd.backtest.run_backtest with M1 arbitration; one trade per day at most; all
parameters fixed here BEFORE any P&L was computed, nothing tuned). Asian range = high/low of [session start, 07:00
London); AR = its width (days with AR < 10 pips or with missing bars in the Asian / London window are skipped).
Orders are placed at 07:00 London, live until 12:00 London, any open trade is closed at 16:00 London.
  AF  fade of the Asian extremes : sell limit at the Asian high, buy limit at the Asian low (OCO), target = Asian
      mid, stop = 0.5 AR beyond the extreme.
  AB  Asian-range breakout       : buy stop 1 pip above the Asian high, sell stop 1 pip below the low (OCO),
      stop = Asian mid, no target (time exit).
  EF  London-morning extension fade : limit orders at session open +- 0.5 x forecast day range (07:00 forecast,
      placed only on a side the Asian session has not already reached), target half-way back (open +- 0.25 F),
      stop = open +- 0.75 F.
Costs: spread = cost_pips / 1.2 paid once per round trip (bid data, buys at ask) and slippage = cost_pips / 6 on
every stop / market fill, i.e. cost_pips = 1.2 is round 1's "1.0 pip spread + 0.2 slippage per fill". Sensitivities:
0.6 and 2.4 (the latter ~ the HOWTO's 1.2 pips per SIDE).

THE 12 VARIANTS (counted; nothing else was run for selection):
  AF_U, AB_U, EF_U                    unconditioned controls (not eligible)
  AF_A, AF_R                          AF on predicted-quiet days (bottom tercile), class A / R
  AB_A, AB_R                          AB on predicted-volatile days (top tercile), class A / R
  EF_A, EF_R                          EF on predicted-quiet days, class A / R
  SW_A, SW_R, SW_C                    switch: AF on quiet + AB on volatile days, class A / R / C
SELECTION RULE (declared before results): final = the conditioned variant (9 eligible) with the best 2010-2015
walk-forward NET Sharpe at cost_pips = 1.2 among those with at least 60 trades in 2010-2015.

Stream format: one row per decision (session, stamped 07:00 London in UTC): pos = side of the trade taken (0 if none),
fwd_bp = price move entry -> exit in bp before costs (pos * fwd_bp = gross trade return), net_bp after costs.
report() uses periods_per_year = decisions per year.
"""
from __future__ import annotations

import math
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.backtest import CostModel, Order, run_backtest  # noqa: E402
from eurusd.data import load_ohlc  # noqa: E402
from eurusd.wf import _agg, report, walk_forward  # noqa: E402

ARM = "vol_tactics"
PROC = ROOT / "data" / "processed"
MACRO = ROOT / "data" / "macro"
RES = ROOT / "experiments" / "results" / "arms"
PIP = 1e-4
H = pd.Timedelta(hours=1)

MIN_AR = 10.0        # pips, minimum Asian range for AF / AB
K_EXT = 0.5          # EF: extension from the session open in units of the forecast day range
ENTRY_UNTIL = 12     # London hour until which orders are live
EXIT_AT = 16         # London hour of the time exit
N_VARIANTS = 12
PERIODS = (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026), ("2010-2015", 2010, 2015), ("2016-2022", 2016, 2022))
ELIGIBLE = ["AF_A", "AF_R", "AB_A", "AB_R", "EF_A", "EF_R", "SW_A", "SW_R", "SW_C"]
CONTROLS = ["AF_U", "AB_U", "EF_U"]


# ------------------------------------------------------------------ daily aggregates
def _london_utc(t0: pd.DatetimeIndex, hour: int) -> pd.DatetimeIndex:
    """UTC time of `hour`:00 London on the calendar date on which the session starting at t0 (22:00 UTC) closes."""
    d = (t0 + 2 * H).tz_localize(None).normalize() + pd.Timedelta(hours=hour)
    return d.tz_localize("Europe/London").tz_convert("UTC")


def _event_flags(t0: pd.DatetimeIndex) -> pd.DataFrame:
    f = pd.read_csv(MACRO / "fomc_decisions.csv"); f = f[f.scheduled == True]  # noqa: E712
    fomc = pd.to_datetime(f.statement_utc, utc=True)
    ecb = pd.to_datetime(pd.read_csv(MACRO / "ecb_decisions.csv").decision_utc, utc=True)
    b = pd.read_csv(MACRO / "us_bls_releases.csv"); bt = pd.to_datetime(b.release_utc, utc=True)
    nfp = bt[b.release == "Employment Situation"]; cpi = bt[b.release == "CPI"]
    # before the BLS calendar starts (2010): NFP = first Friday of the month, 08:30 New York
    first = bt.min()
    days = pd.date_range("2002-12-01", first.tz_localize(None).normalize(), freq="D")
    ff = days[(days.dayofweek == 4) & (days.day <= 7)] + pd.Timedelta(hours=8, minutes=30)
    nfp_rule = ff.tz_localize("America/New_York").tz_convert("UTC")
    nfp = pd.DatetimeIndex(nfp).union(nfp_rule[nfp_rule < first])
    out = pd.DataFrame(index=t0)
    for name, times in (("fomc", fomc), ("ecb", ecb), ("nfp", nfp), ("cpi", cpi)):
        tt = np.sort(pd.DatetimeIndex(times).tz_convert("UTC").as_unit("ns").asi8)
        a = np.searchsorted(tt, t0.as_unit("ns").asi8, side="left")
        b_ = np.searchsorted(tt, (t0 + 24 * H).as_unit("ns").asi8, side="left")
        out[f"ev_{name}"] = (b_ > a).astype(float)
    out["ev_fomc_prev"] = out["ev_fomc"].shift(1).fillna(0.0)
    return out


def build_days(refresh: bool = False) -> pd.DataFrame:
    """Per-session aggregates from M15 / M5 bars (cached). Index = session start (22:00 UTC)."""
    cache = PROC / f"{ARM}_days.parquet"
    if cache.exists() and not refresh:
        return pd.read_parquet(cache)
    m15 = load_ohlc("M15").loc["2002-12-01":, ["open", "high", "low", "close"]]
    key = (m15.index - 22 * H).floor("D") + 22 * H
    g = m15.groupby(key)
    S = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(), "n_day": g.size()})
    S = S[S.index.dayofweek.isin([6, 0, 1, 2, 3]) & (S.n_day >= 40)]
    t0 = pd.DatetimeIndex(S.index)
    L07, L12, L16 = _london_utc(t0, 7), _london_utc(t0, ENTRY_UNTIL), _london_utc(t0, EXIT_AT)
    S["L07"], S["L12"], S["L16"] = L07, L12, L16
    ix = m15.index
    hi, lo, cl = m15.high.values, m15.low.values, m15.close.values
    a0, a1, l1 = ix.searchsorted(t0), ix.searchsorted(L07), ix.searchsorted(L16)
    ah, al, ac, lh, ll = (np.full(len(S), np.nan) for _ in range(5))
    for k in range(len(S)):
        if a1[k] > a0[k]:
            ah[k], al[k], ac[k] = hi[a0[k]:a1[k]].max(), lo[a0[k]:a1[k]].min(), cl[a1[k] - 1]
        if l1[k] > a1[k]:
            lh[k], ll[k] = hi[a1[k]:l1[k]].max(), lo[a1[k]:l1[k]].min()
    S["asia_high"], S["asia_low"], S["asia_close"] = ah, al, ac
    S["lon_high"], S["lon_low"] = lh, ll
    S["n_asia"], S["n_lon"] = a1 - a0, l1 - a1
    S["exp_asia"] = ((L07 - t0) / pd.Timedelta(minutes=15)).astype(int)
    S["range_pips"] = (S.high - S.low) / PIP
    S["asia_range_pips"] = (S.asia_high - S.asia_low) / PIP
    S["lon_range_pips"] = (S.lon_high - S.lon_low) / PIP
    S["gap_pips"] = (S.open - S.close.shift(1)) / PIP
    # realised vol from 5-minute log returns (bp), returns across gaps > 30 min dropped
    m5 = load_ohlc("M5").loc["2002-12-01":, "close"]
    r = np.log(m5).diff()
    dt = m5.index.to_series().diff().dt.total_seconds().values
    r2 = np.where((dt <= 1800) & np.isfinite(r.values), r.values ** 2, 0.0)
    cs = np.concatenate([[0.0], np.cumsum(r2)])
    i5 = m5.index
    b0, b1, b2, b3 = i5.searchsorted(t0), i5.searchsorted(L07), i5.searchsorted(L16), i5.searchsorted(t0 + 24 * H)
    S["rv_day_bp"] = np.sqrt(cs[b3] - cs[b0]) * 1e4
    S["rv_asia_bp"] = np.sqrt(cs[b1] - cs[b0]) * 1e4
    S["rv_lon_bp"] = np.sqrt(cs[b2] - cs[b1]) * 1e4
    S["day_ok"] = S.n_day >= 84
    S["asia_ok"] = (S.n_asia >= 0.85 * S.exp_asia) & (S.n_asia >= 24)
    S["lon_ok"] = S.n_lon >= 33
    S = S.join(_event_flags(t0))
    S = S.loc["2003-01-01":]
    S.to_parquet(cache)
    return S


# ------------------------------------------------------------------ forecast features
def _har(x: pd.Series, name: str) -> pd.DataFrame:
    p = x.shift(1)
    w = p.rolling(5, min_periods=2).mean(); m = p.rolling(22, min_periods=8).mean()
    return pd.DataFrame({f"{name}_d": p.fillna(w), f"{name}_w": w, f"{name}_m": m})


def build_features(S: pd.DataFrame) -> pd.DataFrame:
    F = pd.DataFrame(index=S.index)
    y_day = S.range_pips.where(S.day_ok & (S.range_pips > 0))
    y_lon = S.lon_range_pips.where(S.lon_ok & (S.lon_range_pips > 0))
    F["y_day"], F["y_lon"] = y_day, y_lon
    # lag features / baselines use the range of whatever bars exist (sessions with missing hours, e.g. Feb-Jul 2023, are
    # understated but that is what was observable); TARGETS above require complete windows
    x_day = S.range_pips.where(S.range_pips > 0)
    x_lon = S.lon_range_pips.where((S.n_lon >= 18) & (S.lon_range_pips > 0))
    F = F.join(_har(np.log(x_day), "lr")).join(_har(np.log(S.rv_day_bp.where(S.rv_day_bp > 0)), "lv")).join(_har(np.log(x_lon), "ll"))
    D = pd.read_parquet(PROC / "features_daily.parquet", columns=["vix"])
    F["lvix"] = np.log(D["vix"].reindex(S.index).ffill().shift(1))   # store value of the PREVIOUS session (itself lagged a day)
    for c in ("ev_fomc", "ev_ecb", "ev_nfp", "ev_cpi", "ev_fomc_prev"):
        F[c] = S[c]
    dow = (S.index + 2 * H).dayofweek
    for d in (1, 2, 3, 4):
        F[f"dow_{d}"] = (dow == d).astype(float)
    # known at 07:00 London only
    F["la"] = np.log(S.asia_range_pips.where(S.asia_ok & (S.asia_range_pips > 0)))
    F["lav"] = np.log(S.rv_asia_bp.where(S.asia_ok & (S.rv_asia_bp > 0)))
    F["lgap"] = np.log1p(S.gap_pips.abs())
    # naive baselines and the "recent norm" (all from sessions strictly before this one)
    for t, y in (("day", x_day), ("lon", x_lon)):
        F[f"naive1_{t}"] = y.shift(1).ffill()
        F[f"ma20_{t}"] = y.shift(1).rolling(20, min_periods=8).mean()
    F["label_end"] = S.index + 24 * H
    return F


EV = ["ev_fomc", "ev_ecb", "ev_nfp", "ev_cpi", "ev_fomc_prev"]
DOW = ["dow_1", "dow_2", "dow_3", "dow_4"]
FEATS = {
    "close_day": ["lr_d", "lr_w", "lr_m", "lv_d", "lv_w", "lv_m", "ll_d", "ll_w", "ll_m", "lvix"] + EV + DOW,
    "close_lon": ["lr_d", "lr_w", "lr_m", "lv_d", "lv_w", "lv_m", "ll_d", "ll_w", "ll_m", "lvix"] + EV + DOW,
    "l07_day": ["lr_d", "lr_w", "lr_m", "lv_d", "lv_w", "lv_m", "ll_d", "ll_w", "ll_m", "lvix"] + EV + DOW + ["la", "lav", "lgap"],
    "l07_lon": ["lr_d", "lr_w", "lr_m", "lv_d", "lv_w", "lv_m", "ll_d", "ll_w", "ll_m", "lvix"] + EV + DOW + ["la", "lav", "lgap"],
    "har_day": ["lr_d", "lr_w", "lr_m"],
    "har_lon": ["ll_d", "ll_w", "ll_m"],
}


def wf_forecast(F: pd.DataFrame, model: str, shuffle_seed: int | None = None, shift: int = 0, coefs: dict | None = None) -> pd.DataFrame:
    """Walk-forward OLS forecast of log range. shift = +1: features one session stale; -1: features of the NEXT
    session (deliberate look-ahead, leak-check only). shuffle_seed: permute the training targets."""
    tgt = "y_day" if model.endswith("day") else "y_lon"
    t = tgt[2:]
    feats = FEATS[model]
    df = F[feats + [tgt, f"ma20_{t}"]].copy()
    if shift:
        df[feats] = df[feats].shift(shift)
    side: dict = {}

    def fit(train: pd.DataFrame):
        tr = train.dropna(subset=[tgt])
        med = tr[feats].median()
        X = tr[feats].fillna(med)
        mu, sd = X.mean(), X.std().replace(0, 1.0)
        A = np.column_stack([np.ones(len(X)), ((X - mu) / sd).values])
        y = np.log(tr[tgt].values)
        if shuffle_seed is not None:
            y = np.random.default_rng(shuffle_seed + len(y)).permutation(y)
        beta, *_ = np.linalg.lstsq(A, y, rcond=None)
        fitted = A @ beta
        s2 = float(np.mean((y - fitted) ** 2))
        ratio = np.exp(fitted) / tr[f"ma20_{t}"].values
        ratio = ratio[np.isfinite(ratio)]
        return dict(med=med, mu=mu, sd=sd, beta=beta, s2=s2, q_real=np.quantile(tr[tgt].values, [1 / 3, 0.5, 2 / 3]),
                    q_ratio=np.quantile(ratio, [1 / 3, 2 / 3]), n=len(tr))

    def predict(m, test: pd.DataFrame) -> pd.Series:
        X = test[feats].fillna(m["med"])
        A = np.column_stack([np.ones(len(X)), ((X - m["mu"]) / m["sd"]).values])
        side[int(test.index.year[0])] = m
        if coefs is not None:
            coefs[int(test.index.year[0])] = pd.Series(m["beta"][1:], index=feats)
        return pd.Series(A @ m["beta"], index=test.index)

    pl = walk_forward(df, fit, predict, label_end=F["label_end"], verbose=False)
    out = pd.DataFrame({"pred_log": pl, "realised": F[tgt], "naive1": F[f"naive1_{t}"], "ma20": F[f"ma20_{t}"]})
    yr = pd.Series(out.index.year, index=out.index)
    for col, fn in (("s2", lambda m: m["s2"]), ("thr1", lambda m: m["q_real"][0]), ("thr_med", lambda m: m["q_real"][1]), ("thr2", lambda m: m["q_real"][2]),
                    ("rq1", lambda m: m["q_ratio"][0]), ("rq2", lambda m: m["q_ratio"][1])):
        out[col] = yr.map({y: fn(m) for y, m in side.items()})
    out = out[out.pred_log.notna()].copy()
    out["fc_median"] = np.exp(out.pred_log)
    out["fc_mean"] = np.exp(out.pred_log + 0.5 * out.s2)
    out["cls_abs"] = (out.fc_median > out.thr1).astype(int) + (out.fc_median > out.thr2).astype(int)
    r = out.fc_median / out.ma20
    out["cls_rel"] = ((r > out.rq1).astype(int) + (r > out.rq2).astype(int)).where(r.notna(), 1)
    out["cls_real"] = ((out.realised > out.thr1).astype(int) + (out.realised > out.thr2).astype(int)).where(out.realised.notna())
    return out


def accuracy_table(fc: pd.DataFrame, name: str) -> pd.DataFrame:
    """OOS accuracy of the range forecast vs naive baselines (rows with a valid realised range only)."""
    rows = []
    d = fc.dropna(subset=["realised", "naive1", "ma20"])
    for label, a, b in PERIODS[:3]:
        x = d[(d.index.year >= a) & (d.index.year <= b)]
        y = x.realised.values
        sst = ((y - y.mean()) ** 2).sum()
        ly = np.log(y)
        r = {"model": name, "period": label, "n": len(x), "mean_range": y.mean()}
        for k, p in (("model", x.fc_mean.values), ("naive1", x.naive1.values), ("ma20", x.ma20.values)):
            r[f"r2_{k}"] = 1 - ((y - p) ** 2).sum() / sst
            r[f"rmse_{k}"] = math.sqrt(((y - p) ** 2).mean())
        r["mae_model"] = np.abs(y - x.fc_median.values).mean()
        r["mae_naive1"] = np.abs(y - x.naive1.values).mean(); r["mae_ma20"] = np.abs(y - x.ma20.values).mean()
        r["r2_log_model"] = 1 - ((ly - x.pred_log.values) ** 2).sum() / ((ly - ly.mean()) ** 2).sum()
        r["corr_model"] = np.corrcoef(y, x.fc_mean.values)[0, 1]
        # classification against TRAINING-window thresholds of the realised range
        up = y > x.thr_med.values
        r["base_above_median"] = up.mean()
        r["acc_median_model"] = ((x.fc_median.values > x.thr_med.values) == up).mean()
        r["acc_median_naive1"] = ((x.naive1.values > x.thr_med.values) == up).mean()
        r["acc_median_ma20"] = ((x.ma20.values > x.thr_med.values) == up).mean()
        real3 = x.cls_real.values
        for k, p in (("model", x.fc_median.values), ("naive1", x.naive1.values), ("ma20", x.ma20.values)):
            c3 = (p > x.thr1.values).astype(int) + (p > x.thr2.values).astype(int)
            r[f"acc_tercile_{k}"] = (c3 == real3).mean()
        r["acc_tercile_majority"] = pd.Series(real3).value_counts(normalize=True).max()
        # regime-free version: is today's range above the mean of the previous 20 sessions?
        upr = y > x.ma20.values
        r["base_above_ma20"] = upr.mean()
        r["acc_vs_ma20_model"] = ((x.fc_median.values > x.ma20.values) == upr).mean()
        r["acc_vs_ma20_naive1"] = ((x.naive1.values > x.ma20.values) == upr).mean()
        # Brier score of P(range > training median) from the log-normal forecast vs the climatological base rate
        from scipy.stats import norm
        p_up = 1 - norm.cdf((np.log(x.thr_med.values) - x.pred_log.values) / np.sqrt(x.s2.values))
        r["brier_model"] = ((p_up - up) ** 2).mean()
        r["brier_naive1"] = (((x.naive1.values > x.thr_med.values).astype(float) - up) ** 2).mean()
        r["brier_base"] = ((up.mean() - up) ** 2).mean()
        rows.append(r)
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ tactics on the bar engine
_BARS: dict = {}


def load_bars() -> tuple[pd.DataFrame, pd.DataFrame]:
    if not _BARS:
        _BARS["m15"] = load_ohlc("M15").loc["2009-12-28":, ["open", "high", "low", "close"]]
        m1 = pd.read_parquet(PROC / "EURUSD_M1.parquet", columns=["high", "low"])
        m1.index = pd.DatetimeIndex(m1.index).tz_convert("UTC") if m1.index.tz is not None else pd.DatetimeIndex(m1.index).tz_localize("UTC")
        _BARS["m1"] = m1.loc["2009-12-28":]
    return _BARS["m15"], _BARS["m1"]


def decision_days(S: pd.DataFrame, fc_day07: pd.DataFrame) -> pd.DataFrame:
    """Sessions on which a 07:00 London decision is taken (OOS forecast available). `tradeable` = bars complete."""
    m15, _ = load_bars()
    d = S.loc[fc_day07.index.intersection(S.index)].copy()
    d = d[d.index >= pd.Timestamp("2010-01-01", tz="UTC") - 2 * H]
    ix = m15.index
    d["i"] = ix.searchsorted(pd.DatetimeIndex(d.L07)) - 1
    d["i12"] = ix.searchsorted(pd.DatetimeIndex(d.L12)) - 1
    d["i16"] = ix.searchsorted(pd.DatetimeIndex(d.L16)) - 1
    last = ix[np.clip(d.i.values, 0, len(ix) - 1)]
    fresh = (pd.DatetimeIndex(d.L07) - last) <= pd.Timedelta(minutes=30)
    d["tradeable"] = d.asia_ok & d.lon_ok & fresh & (d.i12 > d.i) & (d.i16 >= d.i12) & (d.i >= 0)
    d["F_day"] = fc_day07["fc_median"].reindex(d.index)
    return d


def make_orders(d: pd.DataFrame, tactic: str) -> list[Order]:
    orders = []
    for t0, r in d[d.tradeable].iterrows():
        i, exp, ex = int(r.i), int(r.i12 - r.i), int(r.i16)
        ah, al = r.asia_high, r.asia_low
        ar = ah - al
        if tactic in ("AF", "AB"):
            if ar < MIN_AR * PIP:
                continue
            mid = 0.5 * (ah + al)
            if tactic == "AF":
                orders.append(Order(i=i, side=-1, entry_type="limit", entry_price=ah, sl=ah + 0.5 * ar, tp=mid, expiry_bars=exp, exit_i=ex, tag="AF"))
                orders.append(Order(i=i, side=+1, entry_type="limit", entry_price=al, sl=al - 0.5 * ar, tp=mid, expiry_bars=exp, exit_i=ex, tag="AF"))
            else:
                orders.append(Order(i=i, side=+1, entry_type="stop", entry_price=ah + PIP, sl=mid, expiry_bars=exp, exit_i=ex, tag="AB"))
                orders.append(Order(i=i, side=-1, entry_type="stop", entry_price=al - PIP, sl=mid, expiry_bars=exp, exit_i=ex, tag="AB"))
        elif tactic == "EF":
            f = r.F_day * PIP
            if not np.isfinite(f) or f <= 0:
                continue
            e = K_EXT * f
            up, dn = r.open + e, r.open - e
            if ah < up:
                orders.append(Order(i=i, side=-1, entry_type="limit", entry_price=up, sl=up + 0.5 * e, tp=up - 0.5 * e, expiry_bars=exp, exit_i=ex, tag="EF"))
            if al > dn:
                orders.append(Order(i=i, side=+1, entry_type="limit", entry_price=dn, sl=dn - 0.5 * e, tp=dn + 0.5 * e, expiry_bars=exp, exit_i=ex, tag="EF"))
        else:
            raise ValueError(tactic)
    return orders


def simulate(d: pd.DataFrame, tactic: str, cost_pips: float = 1.2) -> pd.DataFrame:
    """Run one tactic on every tradeable day. Returns one row per trade indexed by session start."""
    m15, m1 = load_bars()
    spread, slip = cost_pips / 1.2, cost_pips / 6.0
    orders = make_orders(d, tactic)
    etype = {(o.i, o.side): o.entry_type for o in orders}
    res = run_backtest(m15, orders, CostModel(spread_pips=spread, slippage_pips=slip), ltf=m1)
    t = res.tdf
    if t.empty:
        return pd.DataFrame()
    k = np.searchsorted(d.i.values, t.order_i.values)          # d.i is increasing: decision bar -> session
    assert (d.i.values[k] == t.order_i.values).all()
    t = t.assign(session=d.index[k])
    assert t.session.is_unique and (t.exit_i.values <= d.i16.values[k]).all() and (t.entry_i.values <= d.i12.values[k]).all()
    stop_entry = np.array([etype[(a, b)] != "limit" for a, b in zip(t.order_i, t.side)])
    t["gross_pips"] = t.pips + spread + slip * stop_entry + slip * (t.reason == "sl")
    t["net_bp"] = t.pips * PIP / t.entry * 1e4
    t["gross_bp"] = t.gross_pips * PIP / t.entry * 1e4
    return t.set_index("session")[["side", "entry", "exit", "reason", "pips", "gross_pips", "net_bp", "gross_bp", "entry_time", "exit_time"]]


def stream(d: pd.DataFrame, trades: pd.DataFrame, mask: pd.Series) -> pd.DataFrame:
    """Arm stream: one row per decision day (index = 07:00 London in UTC)."""
    t = trades.reindex(d.index)
    on = mask.reindex(d.index).fillna(False).values & t.side.notna().values
    pos = np.where(on, t.side.fillna(0.0).values, 0.0)
    gross = np.where(on, t.gross_bp.fillna(0.0).values, 0.0)
    out = pd.DataFrame({"pos": pos, "fwd_bp": gross * pos, "gross_bp": gross, "net_bp": np.where(on, t.net_bp.fillna(0.0).values, 0.0),
                        "pips": np.where(on, t.pips.fillna(0.0).values, 0.0), "session": d.index}, index=pd.DatetimeIndex(d.L07.values, tz="UTC", name="time"))
    return out


def build_variants(d: pd.DataFrame, sims: dict, cls: pd.DataFrame) -> dict:
    """cls: columns A, R, C (0 quiet / 1 normal / 2 volatile) indexed by session."""
    all_ = pd.Series(True, index=d.index)
    V = {"AF_U": stream(d, sims["AF"], all_), "AB_U": stream(d, sims["AB"], all_), "EF_U": stream(d, sims["EF"], all_)}
    for c in ("A", "R"):
        V[f"AF_{c}"] = stream(d, sims["AF"], cls[c] == 0)
        V[f"AB_{c}"] = stream(d, sims["AB"], cls[c] == 2)
        V[f"EF_{c}"] = stream(d, sims["EF"], cls[c] == 0)
    for c in ("A", "R", "C"):
        a, b = stream(d, sims["AF"], cls[c] == 0), stream(d, sims["AB"], cls[c] == 2)
        s = a.copy()
        for col in ("pos", "fwd_bp", "gross_bp", "net_bp", "pips"):
            s[col] = a[col] + b[col]          # the two masks are disjoint
        V[f"SW_{c}"] = s
    return V


def ppy_of(s: pd.DataFrame) -> float:
    yrs = (s.index[-1] - s.index[0]).days / 365.25
    return len(s) / yrs


def variant_report(s: pd.DataFrame, name: str, n_arms: int = N_VARIANTS) -> pd.DataFrame:
    ppy = ppy_of(s)
    tbl = report(s[["pos", "net_bp"]], periods_per_year=ppy, name=ARM, n_arms=n_arms)
    g = {}
    for _, row in tbl.iterrows():
        p = row["period"]
        a, b = (int(p), int(p)) if "-" not in p else map(int, p.split("-"))
        x = s[(s.index.year >= a) & (s.index.year <= b)]
        act = x[x.pos != 0]
        g[p] = {"gross_sharpe": _agg(x.gross_bp, ppy)["sharpe"], "trades": len(act), "hit_net": float((act.net_bp > 0).mean()) if len(act) else np.nan,
                "hit_gross": float((act.gross_bp > 0).mean()) if len(act) else np.nan, "avg_net_pips": float(act.pips.mean()) if len(act) else np.nan,
                "sum_net_pips": float(act.pips.sum())}
    tbl = tbl.join(pd.DataFrame(g).T, on="period")
    tbl.insert(1, "variant", name)
    tbl["periods_per_year"] = ppy
    return tbl


def _key(tbl: pd.DataFrame, period: str, col: str = "sharpe") -> float:
    return float(tbl.loc[tbl.period == period, col].iloc[0])


def select_final(reports: dict) -> str:
    cand = {v: _key(reports[v], "2010-2015") for v in ELIGIBLE if _key(reports[v], "2010-2015", "trades") >= 60}
    return max(cand, key=cand.get)


# ------------------------------------------------------------------ pipeline
def prepare(verbose: bool = True) -> dict:
    S = build_days()
    F = build_features(S)
    fcs = {m: wf_forecast(F, m) for m in FEATS}
    d = decision_days(S, fcs["l07_day"])
    cls = pd.DataFrame({"A": fcs["l07_lon"].cls_abs, "R": fcs["l07_lon"].cls_rel, "C": fcs["close_day"].cls_abs}).reindex(d.index)
    if verbose:
        print(f"sessions {len(S)}, decision days {len(d)} ({int(d.tradeable.sum())} tradeable)", flush=True)
    return dict(S=S, F=F, fcs=fcs, d=d, cls=cls)


def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True, ctx: dict | None = None):
    """Returns (OOS positions of the final variant, report of all 12 variants). The final variant is selected at the
    headline cost (1.2) and re-priced at `cost_pips` by re-running the engine with the scaled spread / slippage."""
    t_start = time.time()
    ctx = ctx or prepare(verbose)
    d, cls = ctx["d"], ctx["cls"]
    sims = {t: simulate(d, t, cost_pips) for t in ("AF", "AB", "EF")}
    V = build_variants(d, sims, cls)
    reports = {v: variant_report(s, v) for v, s in V.items()}
    if abs(cost_pips - 1.2) < 1e-9:
        final = select_final(reports)
    else:
        sims0 = {t: simulate(d, t, 1.2) for t in ("AF", "AB", "EF")}
        final = select_final({v: variant_report(s, v) for v, s in build_variants(d, sims0, cls).items()})
    rep = pd.concat(reports.values(), ignore_index=True)
    rep["final"] = rep.variant == final
    rep["cost_pips"] = cost_pips
    rep["eligible"] = rep.variant.isin(ELIGIBLE)
    pos = V[final]
    if verbose:
        print(f"cost {cost_pips}: final = {final}  ({time.time() - t_start:.0f}s)", flush=True)
        for v in V:
            r = reports[v]
            print(f"  {v:5s} SR 10-15 {_key(r, '2010-2015'):+.2f} | 10-26 {_key(r, '2010-2026'):+.2f} t {_key(r, '2010-2026', 't'):+.2f} | 16-26 {_key(r, '2016-2026'):+.2f} | "
                  f"23-26 {_key(r, '2023-2026'):+.2f} | trades {int(_key(r, '2010-2026', 'trades'))} hit {_key(r, '2010-2026', 'hit_net'):.2f} gross SR {_key(r, '2010-2026', 'gross_sharpe'):+.2f}", flush=True)
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        pos.to_parquet(RES / f"{ARM}_positions.parquet")
        rp = RES / f"{ARM}_report.csv"                       # keep the other cost levels already on file
        prev = pd.read_csv(rp) if rp.exists() else pd.DataFrame()
        prev = prev[(prev.cost_pips - cost_pips).abs() > 1e-9] if "cost_pips" in prev else pd.DataFrame()
        pd.concat([rep, prev], ignore_index=True).to_csv(rp, index=False)
        allv = pd.concat({v: s[["pos", "gross_bp", "net_bp"]] for v, s in V.items()}, axis=1)
        allv.to_parquet(RES / f"{ARM}_all_variants.parquet")
    ctx.update(sims=sims, V=V, reports=reports, final=final)
    return pos["pos"], rep


def save_forecast(ctx: dict) -> pd.DataFrame:
    """Walk-forward range forecast for the lead's scoreboard (primary = forecast made at the session start)."""
    f, g, l = ctx["fcs"]["close_day"], ctx["fcs"]["l07_day"], ctx["fcs"]["l07_lon"]
    names = {0: "quiet", 1: "normal", 2: "volatile"}
    out = pd.DataFrame({
        "date": (f.index + 2 * H).tz_localize(None).normalize(),
        "forecast_pips": f.fc_mean, "realised_pips": f.realised, "class": f.cls_abs.map(names),
        "forecast_median_pips": f.fc_median, "class_realised": f.cls_real.map(names),
        "thr_tercile1": f.thr1, "thr_median": f.thr_med, "thr_tercile2": f.thr2, "naive_prev_pips": f.naive1, "naive_ma20_pips": f.ma20,
        "forecast_pips_0700": g.fc_mean.reindex(f.index), "class_0700": g.cls_abs.reindex(f.index).map(names),
        "london_forecast_pips_0700": l.fc_mean.reindex(f.index), "london_realised_pips": l.realised.reindex(f.index),
        "london_class_0700": l.cls_abs.reindex(f.index).map(names), "london_class_rel_0700": l.cls_rel.reindex(f.index).map(names),
        "london_class_realised": l.cls_real.reindex(f.index).map(names),
    })
    out.index.name = "session_start"
    out.to_parquet(PROC / f"{ARM}_range_forecast.parquet")
    return out


def by_class_table(ctx: dict) -> pd.DataFrame:
    """Every tactic's trades split by the predicted class (the conditioned-vs-unconditioned table) and by the
    REALISED class of the London window (oracle = perfect foresight, leak-check only)."""
    d, sims, cls = ctx["d"], ctx["sims"], ctx["cls"]
    oracle = ctx["fcs"]["l07_lon"].cls_real.reindex(d.index)
    rows = []
    for tac in ("AF", "AB", "EF"):
        for cname, c in (("A", cls["A"]), ("R", cls["R"]), ("C", cls["C"]), ("oracle", oracle)):
            for k, lab in ((None, "all"), (0, "quiet"), (1, "normal"), (2, "volatile")):
                if k is None and cname != "A":
                    continue
                mask = pd.Series(True, index=d.index) if k is None else (c == k)
                s = stream(d, sims[tac], mask)
                ppy = ppy_of(s)
                for label, a, b in PERIODS[:4]:
                    x = s[(s.index.year >= a) & (s.index.year <= b)]
                    act = x[x.pos != 0]
                    rows.append({"tactic": tac, "class_def": "none" if k is None else cname, "class": lab, "period": label, "days_in_class": int(mask[(d.L07.dt.year >= a) & (d.L07.dt.year <= b)].sum()),
                                 "trades": len(act), "net_sharpe": _agg(x.net_bp, ppy)["sharpe"], "t": _agg(x.net_bp, ppy)["t"], "gross_sharpe": _agg(x.gross_bp, ppy)["sharpe"],
                                 "avg_net_pips": act.pips.mean() if len(act) else np.nan, "avg_gross_bp": act.gross_bp.mean() if len(act) else np.nan,
                                 "t_trade_net": (act.net_bp.mean() / act.net_bp.std() * math.sqrt(len(act))) if len(act) > 5 else np.nan,
                                 "hit_net": (act.net_bp > 0).mean() if len(act) else np.nan, "hit_gross": (act.gross_bp > 0).mean() if len(act) else np.nan})
    return pd.DataFrame(rows)


def _final_parts(final: str) -> list[tuple[str, str, int]]:
    """(tactic, class definition, class value) pieces of a variant."""
    tac, c = final.split("_")
    if tac == "SW":
        return [("AF", c, 0), ("AB", c, 2)]
    return [(tac, c, 2 if tac == "AB" else 0)]


def _stream_from_cls(ctx: dict, final: str, clsdict: dict) -> pd.DataFrame:
    d, sims = ctx["d"], ctx["sims"]
    out = None
    for tac, c, k in _final_parts(final):
        s = stream(d, sims[tac], clsdict[c].reindex(d.index) == k)
        if out is None:
            out = s
        else:
            for col in ("pos", "fwd_bp", "gross_bp", "net_bp", "pips"):
                out[col] = out[col] + s[col]
    return out


def leak_checks(ctx: dict, seeds=(0, 1, 2, 3, 4)) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """(1) training targets shuffled -> forecast skill ~0, class = noise; (2) features one session stale / one session
    ahead (look-ahead) + oracle class; (3) coefficients of the forecast model."""
    F, final, d = ctx["F"], ctx["final"], ctx["d"]
    rows, frows = [], []

    def add(name, s, expectation):
        ppy = ppy_of(s)
        act = s[s.pos != 0]
        r = {"check": name, "trades": len(act), "expectation": expectation}
        for label, a, b in PERIODS[:3]:
            x = s[(s.index.year >= a) & (s.index.year <= b)]
            r[f"net_sharpe_{label}"] = _agg(x.net_bp, ppy)["sharpe"]; r[f"gross_sharpe_{label}"] = _agg(x.gross_bp, ppy)["sharpe"]
        r["t_2010-2026"] = _agg(s.net_bp, ppy)["t"]
        r["avg_net_pips"] = act.pips.mean() if len(act) else np.nan
        rows.append(r)

    def facc(name, fc):
        a = accuracy_table(fc, name)
        frows.append(a[a.period == "2010-2026"][["model", "n", "r2_log_model", "r2_model", "acc_median_model", "acc_tercile_model", "acc_vs_ma20_model"]])

    def classes(shuffle_seed=None, shift=0):
        fl = wf_forecast(F, "l07_lon", shuffle_seed=shuffle_seed, shift=shift)
        fd = wf_forecast(F, "close_day", shuffle_seed=shuffle_seed, shift=shift)
        return fl, fd, {"A": fl.cls_abs, "R": fl.cls_rel, "C": fd.cls_abs}

    add("real", ctx["V"][final], "the reported record")
    facc("real l07_lon", ctx["fcs"]["l07_lon"]); facc("real close_day", ctx["fcs"]["close_day"])
    sh = []
    for sd in seeds:
        fl, fd, c = classes(shuffle_seed=1000 * (sd + 1))
        s = _stream_from_cls(ctx, final, c)
        sh.append(s)
        facc(f"shuffled targets seed {sd} l07_lon", fl)
        add(f"shuffled targets seed {sd}", s, "no forecast skill; conditioning = arbitrary subset")
    fl, fd, c = classes(shift=1)
    facc("features +1 session (stale) l07_lon", fl); facc("features +1 session (stale) close_day", fd)
    add("features +1 session (stale)", _stream_from_cls(ctx, final, c), "forecast degrades; class less informative")
    fl, fd, c = classes(shift=-1)
    facc("features -1 session (future) l07_lon", fl); facc("features -1 session (future) close_day", fd)
    add("features -1 session (future)", _stream_from_cls(ctx, final, c), "forecast accuracy jumps (lag-1 features = the target day)")
    oracle = ctx["fcs"]["l07_lon"].cls_real.reindex(d.index)
    add("oracle class (realised London tercile)", _stream_from_cls(ctx, final, {"A": oracle, "R": oracle, "C": oracle}), "P&L jumps: the harness is sensitive to class look-ahead")
    # mirrored class: the tactic on the WRONG days
    wrong = {k: 2 - v for k, v in ctx["cls"].items()}
    add("mirrored class (quiet <-> volatile)", _stream_from_cls(ctx, final, wrong), "should not beat the real class if conditioning carries information")
    coefs: dict = {}
    wf_forecast(F, "l07_lon", coefs=coefs)
    c1 = pd.DataFrame(coefs).T
    coefs2: dict = {}
    wf_forecast(F, "close_day", coefs=coefs2)
    c2 = pd.DataFrame(coefs2).T
    ctab = pd.DataFrame({"l07_lon_mean_beta": c1.mean(), "l07_lon_beta_2026": c1.iloc[-1], "close_day_mean_beta": c2.mean(), "close_day_beta_2026": c2.iloc[-1]})
    return pd.DataFrame(rows), pd.concat(frows, ignore_index=True), ctab


def incremental() -> tuple[pd.DataFrame, pd.DataFrame]:
    from eurusd.arms.meta import combine, load_arm_daily, report_combo
    base = ["weak_signals", "regime_trend"]
    rows = []
    for name, arms in (("EW[weak_signals,regime_trend]", base), (f"EW[weak_signals,regime_trend,{ARM}]", base + [ARM])):
        pnl, w = combine(arms, "EW")
        r = report_combo(pnl, name, len(arms))
        r["weights_last_year"] = str(w.iloc[-1].round(2).to_dict()) if len(w) else ""
        rows.append(r[r.period.isin(["2010-2026", "2013-2026", "2016-2026", "2023-2026"])])
    mine = load_arm_daily(ARM)
    cor = []
    for a in base:
        o = load_arm_daily(a)
        j = pd.concat([mine, o], axis=1, keys=["mine", a], sort=True).fillna(0.0)
        j = j[j.index.year >= 2010]
        act = j[j["mine"] != 0]
        cor.append({"arm": a, "corr_daily_all": j["mine"].corr(j[a]), "corr_on_my_trade_days": act["mine"].corr(act[a]) if len(act) > 10 else np.nan,
                    "corr_2016_2026": j[j.index.year >= 2016]["mine"].corr(j[j.index.year >= 2016][a]), "n": len(j)})
    return pd.concat(rows, ignore_index=True), pd.DataFrame(cor)


def main():
    t0 = time.time()
    ctx = prepare()
    acc = pd.concat([accuracy_table(fc, m) for m, fc in ctx["fcs"].items()], ignore_index=True)
    acc.to_csv(RES / f"{ARM}_forecast_accuracy.csv", index=False)
    print(acc.round(3).to_string(), flush=True)
    save_forecast(ctx)
    cls = ctx["cls"]
    print("class shares by year (A / R / C):")
    print(pd.concat({c: cls[c].groupby(ctx["d"].L07.dt.year).value_counts(normalize=True).unstack().round(2) for c in cls}, axis=1).to_string(), flush=True)
    sens = []
    for cp in (0.6, 2.4):
        c2 = dict(ctx)
        _, rep = run(cp, write=False, ctx=c2)
        sens.append(rep)
    _, rep = run(1.2, write=True, ctx=ctx)
    pd.concat([rep] + sens, ignore_index=True).to_csv(RES / f"{ARM}_report.csv", index=False)
    bc = by_class_table(ctx); bc.to_csv(RES / f"{ARM}_by_class.csv", index=False)
    lc, lf, ctab = leak_checks(ctx)
    lc.to_csv(RES / f"{ARM}_leakchecks.csv", index=False); lf.to_csv(RES / f"{ARM}_leakchecks_forecast.csv", index=False); ctab.to_csv(RES / f"{ARM}_coefficients.csv")
    print(lc.round(3).to_string()); print(lf.round(3).to_string()); print(ctab.round(3).to_string(), flush=True)
    inc, cor = incremental()
    inc.to_csv(RES / f"{ARM}_incremental.csv", index=False); cor.to_csv(RES / f"{ARM}_pnl_corr.csv", index=False)
    print(inc.round(3).to_string()); print(cor.round(3).to_string())
    print(f"done in {time.time() - t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
