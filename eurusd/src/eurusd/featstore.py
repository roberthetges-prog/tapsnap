"""Feature store: leak-free daily and hourly feature matrices for all research arms.

Daily frame (index = closing date of the NY-close session, UTC midnight label):
  every feature uses prices up to that session's close and macro data stamped <= the previous
  calendar day (publication lag). Labels are forward returns (bp) and a triple-barrier class.
Hourly frame (index = bar start): features use bars <= t; macro/daily features are those of the
  previous completed session; labels are forward 1h/4h/8h/24h returns (bp).

`label_end` columns give the UTC time at which each row's label is known (walk-forward uses them).
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

from . import features as F
from .data import load_ohlc

ROOT = Path(__file__).resolve().parents[2]
MACRO = ROOT / "data" / "macro"
CROSS = ROOT / "data" / "processed" / "cross"
OUT = ROOT / "data" / "processed"
PIP = 0.0001


# ------------------------------------------------------------------ helpers
def _lr(s: pd.Series, k: int = 1) -> pd.Series:
    return (np.log(s) - np.log(s.shift(k))) * 1e4


def _macro_series(name: str, col: str = "value") -> pd.Series:
    p = MACRO / name
    d = pd.read_csv(p)
    dcol = d.columns[0]
    d[dcol] = pd.to_datetime(d[dcol])
    s = d.set_index(dcol)[col].astype(float)
    return s[~s.index.duplicated()].sort_index()


def _cross_daily(name: str) -> pd.Series:
    p = CROSS / f"{name}_D1.parquet"
    if not p.exists():
        return pd.Series(dtype=float)
    d = pd.read_parquet(p)
    s = d["close"]
    s.index = s.index.tz_convert("UTC").normalize().tz_localize(None)
    return s[~s.index.duplicated(keep="last")].sort_index()


def _align_lagged(s: pd.Series, idx: pd.DatetimeIndex, lag_days: int = 1) -> pd.Series:
    """Value of s known at the start of each date in idx: last observation stamped <= date - lag_days."""
    target = pd.DatetimeIndex(idx) - pd.Timedelta(days=lag_days)
    return pd.Series(s.reindex(s.index.union(target)).sort_index().ffill().reindex(target).values, index=idx)


def _events() -> pd.DataFrame:
    frames = []
    e = pd.read_csv(MACRO / "events_high_eur_usd.csv")
    e = e[e.has_time == True]
    frames.append(pd.DataFrame({"time": pd.to_datetime(e.datetime_utc, utc=True), "ccy": e.currency, "event": e.event}))
    f = pd.read_csv(MACRO / "fomc_decisions.csv"); f = f[f.scheduled == True]
    frames.append(pd.DataFrame({"time": pd.to_datetime(f.statement_utc, utc=True), "ccy": "USD", "event": "FOMC Statement"}))
    c = pd.read_csv(MACRO / "ecb_decisions.csv")
    frames.append(pd.DataFrame({"time": pd.to_datetime(c.decision_utc, utc=True), "ccy": "EUR", "event": "ECB decision"}))
    b = pd.read_csv(MACRO / "us_bls_releases.csv")
    frames.append(pd.DataFrame({"time": pd.to_datetime(b.release_utc, utc=True), "ccy": "USD", "event": "BLS " + b.release}))
    ev = pd.concat(frames).dropna().drop_duplicates(["time", "event"]).sort_values("time").reset_index(drop=True)
    kind = np.select([ev.event.str.contains("FOMC", case=False), ev.event.str.contains("ECB|Main Refinancing|Monetary Policy Statement", case=False, regex=True),
                      ev.event.str.contains("Non-Farm|Employment Situation", case=False, regex=True), ev.event.str.contains("CPI", case=False)],
                     ["fomc", "ecb", "nfp", "cpi"], "other")
    ev["kind"] = kind
    return ev


def _surprises() -> pd.DataFrame:
    """Standardised surprises (actual - forecast)/rolling sd for NFP, CPI m/m, Core CPI, from the ForexFactory archive."""
    e = pd.read_csv(MACRO / "events.csv")
    e = e[(e.has_time == True) & e.source.str.startswith("ff_") & (e.currency == "USD")].copy()
    e["t"] = pd.to_datetime(e.datetime_utc, utc=True)
    def num(x):
        if pd.isna(x): return np.nan
        s = str(x).replace("%", "").replace(",", ""); m = 1000 if s.endswith("K") else (1e6 if s.endswith("M") else 1)
        try: return float(s.rstrip("KMB")) * m
        except ValueError: return np.nan
    e["a"] = e.actual.map(num); e["f"] = e.forecast.map(num)
    out = {}
    for key, pat in (("nfp", "Non-Farm Employment Change"), ("cpi", "CPI m/m"), ("corecpi", "Core CPI m/m"), ("retail", "Retail Sales m/m"), ("ism", "ISM Manufacturing PMI"), ("gdp", "Advance GDP q/q"), ("pce", "Core PCE Price Index m/m"), ("claims", "Unemployment Claims")):
        s = e[e.event.str.contains(pat, regex=False, na=False) & e.a.notna() & e.f.notna()].sort_values("t").drop_duplicates("t")
        sur = (s.a - s.f)
        z = sur / sur.rolling(24, min_periods=6).std()
        out[key] = pd.Series(z.values, index=pd.DatetimeIndex(s.t))
    return pd.DataFrame(out)


# ------------------------------------------------------------------ daily
def build_daily(save: bool = True) -> pd.DataFrame:
    h1 = load_ohlc("H1").loc["2003":]
    d = F.daily_ohlc(h1, 22)
    d = d[(d["n"] >= 10) & (d.index.dayofweek != 5)]
    start = d.index                       # session start (UTC 21/22:00 of previous calendar day)
    close_time = start + pd.Timedelta(days=1)
    X = pd.DataFrame(index=start)
    c, o, hi, lo = d.close, d.open, d.high, d.low
    # ---- price / technical
    for k in (1, 2, 3, 5, 10, 21, 63, 126, 252):
        X[f"ret_{k}d"] = _lr(c, k)
    X["gap_bp"] = (np.log(o) - np.log(c.shift(1))) * 1e4
    X["range_pips"] = (hi - lo) / PIP
    X["range_rel_adr"] = X["range_pips"] / X["range_pips"].rolling(14).mean().shift(1)
    X["close_in_range"] = (c - lo) / (hi - lo).replace(0, np.nan)
    X["body_rel"] = (c - o) / (hi - lo).replace(0, np.nan)
    hr = np.log(h1.close).diff()
    day_key = (h1.index - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
    rv = (hr ** 2).groupby(day_key).sum().reindex(start)
    X["rv_1d_bp"] = np.sqrt(rv) * 1e4
    X["rv_5d_bp"] = np.sqrt(rv.rolling(5).mean()) * 1e4
    X["rv_21d_bp"] = np.sqrt(rv.rolling(21).mean()) * 1e4
    X["rv_ratio_5_63"] = rv.rolling(5).mean() / rv.rolling(63).mean()
    X["gk_1d"] = (0.5 * np.log(hi / lo) ** 2 - (2 * np.log(2) - 1) * np.log(c / o) ** 2) * 1e8
    atr = F.atr(d, 14)
    X["atr14_pips"] = atr / PIP
    for n in (20, 50, 200):
        X[f"dist_sma{n}_atr"] = (c - F.sma(c, n)) / atr
    X["rsi2"] = F.rsi(c, 2); X["rsi14"] = F.rsi(c, 14)
    X["z20"] = F.zscore(c, 20)
    dc20 = F.donchian(d, 20); dc55 = F.donchian(d, 55)
    X["donch20_pos"] = (c - dc20.lower) / (dc20.upper - dc20.lower).replace(0, np.nan)
    X["donch55_pos"] = (c - dc55.lower) / (dc55.upper - dc55.lower).replace(0, np.nan)
    X["broke_prev_high"] = (hi > hi.shift(1)).astype(float); X["broke_prev_low"] = (lo < lo.shift(1)).astype(float)
    sgn = np.sign(c.diff())
    X["streak"] = sgn.groupby((sgn != sgn.shift()).cumsum()).cumcount().add(1) * sgn
    X["abnormal_day"] = (X["ret_1d"].abs() > X["ret_1d"].rolling(20).mean().abs().add(2 * X["ret_1d"].rolling(20).std())).astype(float)
    adx = F.adx(d, 14); X["adx14"] = adx.adx; X["di_diff"] = adx.pdi - adx.mdi
    # session returns inside the day
    hh = h1.index.hour
    lab = np.select([(hh >= 22) | (hh < 7), (hh >= 7) & (hh < 13), (hh >= 13) & (hh < 16), (hh >= 16) & (hh < 22)], ["asia", "london", "overlap", "nypm"], "x")
    sess = (hr * 1e4).groupby([day_key, lab]).sum().unstack().reindex(start)
    for s in ("asia", "london", "overlap", "nypm"):
        X[f"sess_{s}_bp"] = sess.get(s)
    # ---- calendar
    cd = close_time.tz_convert("America/New_York")
    X["dow"] = cd.dayofweek; X["dom"] = cd.day; X["month"] = cd.month
    bd = pd.Series(cd.tz_localize(None).normalize(), index=start)
    ym = bd.dt.to_period("M")
    X["bd_from_start"] = bd.groupby(ym).cumcount() + 1
    X["bd_to_end"] = bd.groupby(ym).transform("size") - X["bd_from_start"]
    X["is_month_end"] = (X["bd_to_end"] == 0).astype(float); X["is_quarter_end_month"] = cd.month.isin([3, 6, 9, 12]).astype(float)
    # ---- events
    ev = _events()
    et = ev.time.values
    def hours_to_next(kind_mask, when):
        times = et[kind_mask]
        pos = np.searchsorted(times, when.values)
        nxt = np.where(pos < len(times), times[np.minimum(pos, len(times) - 1)], np.datetime64("NaT"))
        return (pd.to_datetime(nxt, utc=True) - when).total_seconds() / 3600
    def hours_since_last(kind_mask, when):
        times = et[kind_mask]
        pos = np.searchsorted(times, when.values, side="right") - 1
        prv = np.where(pos >= 0, times[np.maximum(pos, 0)], np.datetime64("NaT"))
        return (when - pd.to_datetime(prv, utc=True)).total_seconds() / 3600
    for k in ("fomc", "ecb", "nfp", "cpi"):
        m = (ev.kind == k).values
        X[f"h_to_{k}"] = np.minimum(hours_to_next(m, close_time), 24 * 45)
        X[f"h_since_{k}"] = np.minimum(hours_since_last(m, close_time), 24 * 45)
    anyhi = np.ones(len(ev), bool)
    X["h_to_any_high"] = np.minimum(hours_to_next(anyhi, close_time), 24 * 10)
    X["n_high_next_24h"] = [((et > a) & (et <= b)).sum() for a, b in zip(close_time.values, (close_time + pd.Timedelta(hours=24)).values)]
    sur = _surprises()
    for col in sur.columns:
        s = sur[col].dropna()
        s.index = pd.DatetimeIndex(s.index)
        if s.index.tz is None:
            s.index = s.index.tz_localize("UTC")
        X[f"last_surprise_{col}"] = pd.Series(s.reindex(s.index.union(close_time)).sort_index().ffill().reindex(close_time).values, index=start)
        X[f"h_since_surprise_{col}"] = np.minimum(hours_since_last(np.isin(et, s.index.values), close_time), 24 * 45)
    # ---- macro (lagged one calendar day relative to the session's closing date)
    cdate = pd.DatetimeIndex(close_time.tz_convert("UTC").normalize().tz_localize(None))
    us2 = _macro_series("fred_DGS2.csv"); us10 = _macro_series("fred_DGS10.csv"); us3m = _macro_series("fred_T10Y3M.csv")
    ea = pd.read_csv(MACRO / "ea_aaa_yield_curve.csv", parse_dates=["date"]).set_index("date")
    ea2, ea10, ea3m = ea["aaa_spot_2y"], ea["aaa_spot_10y"], ea["aaa_spot_3m"]
    pol = pd.read_csv(MACRO / "ecb_policy_rates.csv", parse_dates=["date"]).set_index("date")
    dfr = pol["deposit_facility_rate"].astype(float)
    ffu = _macro_series("fred_DFEDTARU.csv"); fft = _macro_series("fred_DFEDTAR.csv")
    fed = pd.concat([fft, ffu]).sort_index(); fed = fed[~fed.index.duplicated(keep="last")]
    A = lambda s: _align_lagged(s, cdate, 1).values
    X["us2y"] = A(us2); X["us10y"] = A(us10); X["ea2y"] = A(ea2); X["ea10y"] = A(ea10)
    X["spread2y"] = X["ea2y"] - X["us2y"]; X["spread10y"] = X["ea10y"] - X["us10y"]
    X["us_curve"] = X["us10y"] - X["us2y"]; X["ea_curve"] = X["ea10y"] - X["ea2y"]
    X["policy_diff"] = A(dfr) - A(fed)
    for k in (1, 5, 20, 60):
        X[f"d_spread2y_{k}"] = X["spread2y"].diff(k); X[f"d_spread10y_{k}"] = X["spread10y"].diff(k)
        X[f"d_us2y_{k}"] = X["us2y"].diff(k)
    # fair-value residual of log price on the 2y spread (rolling 250d OLS, lagged)
    lp = np.log(c.values)
    sp = X["spread2y"].values
    z = np.full(len(lp), np.nan)
    for t in range(260, len(lp)):
        ys, xs = lp[t - 250:t], sp[t - 250:t]
        ok = ~np.isnan(ys) & ~np.isnan(xs)
        if ok.sum() > 200 and not np.isnan(sp[t]):
            b, a = np.polyfit(xs[ok], ys[ok], 1); res = ys[ok] - (a + b * xs[ok])
            z[t] = (lp[t] - (a + b * sp[t])) / (res.std() + 1e-12)
    X["fv_resid_z"] = z
    vix = _macro_series("fred_VIXCLS.csv"); X["vix"] = A(vix); X["d_vix_5"] = X["vix"].diff(5)
    dxy = _cross_daily("dxy"); spx = _cross_daily("spx"); gold = _cross_daily("gold"); oil = _cross_daily("oil")
    us10f = _cross_daily("us10y_yh"); zt = _cross_daily("zt_fut"); sx5e = _cross_daily("sx5e")
    for name, s in (("dxy", dxy), ("spx", spx), ("gold", gold), ("oil", oil), ("sx5e", sx5e), ("zt", zt)):
        al = pd.Series(A(s), index=start)
        for k in (1, 5, 20):
            X[f"{name}_ret_{k}"] = (np.log(al) - np.log(al.shift(k))) * 1e4
    X["spx_minus_sx5e_20"] = X["spx_ret_20"] - X["sx5e_ret_20"]
    fx = pd.read_csv(MACRO / "datahub_fx_fed_h10_daily.csv", parse_dates=["date"]).set_index("date")
    for ccy in ("gbp", "jpy", "chf", "aud", "cad"):
        s = pd.Series(A(fx[f"{ccy}_per_usd"].astype(float)), index=start)
        X[f"usd_{ccy}_ret_5"] = (np.log(s) - np.log(s.shift(5))) * 1e4
        X[f"usd_{ccy}_ret_20"] = (np.log(s) - np.log(s.shift(20))) * 1e4
    X["usd_factor_5"] = X[[f"usd_{c}_ret_5" for c in ("gbp", "jpy", "chf", "aud", "cad")]].mean(axis=1)
    X["usd_factor_20"] = X[[f"usd_{c}_ret_20" for c in ("gbp", "jpy", "chf", "aud", "cad")]].mean(axis=1)
    X["eur_vs_usd_factor_20"] = -X["ret_21d"] - X["usd_factor_20"]   # EUR idiosyncratic move vs the dollar factor
    # COT (report Tuesday, published Friday 15:30 ET -> usable from the following Monday: +6 days)
    leg = pd.read_csv(MACRO / "cot_eurofx_legacy.csv", parse_dates=["report_date"]).set_index("report_date")
    net = ((leg.noncomm_long - leg.noncomm_short) / leg.open_interest); net.index = net.index + pd.Timedelta(days=6)
    X["cot_net_pct"] = A(net); X["cot_z52"] = A((net - net.rolling(52).mean()) / net.rolling(52).std()); X["cot_d4"] = A(net.diff(4))
    tff = pd.read_csv(MACRO / "cot_eurofx_tff.csv", parse_dates=["report_date"]).set_index("report_date")
    lev = ((tff.lev_funds_long - tff.lev_funds_short) / tff.open_interest); lev.index = lev.index + pd.Timedelta(days=6)
    X["cot_lev_z52"] = A((lev - lev.rolling(52).mean()) / lev.rolling(52).std())
    # ---- labels
    X["fwd_1d"] = _lr(c, 1).shift(-1)
    X["fwd_2d"] = (np.log(c.shift(-2)) - np.log(c)) * 1e4
    X["fwd_5d"] = (np.log(c.shift(-5)) - np.log(c)) * 1e4
    X["fwd_10d"] = (np.log(c.shift(-10)) - np.log(c)) * 1e4
    # triple barrier: +-1 ATR within 5 sessions
    up = c + atr; dn = c - atr
    tb = np.zeros(len(c)); tb[:] = np.nan
    hv, lv = hi.values, lo.values
    for i in range(len(c) - 5):
        tb[i] = 0.0
        for j in range(1, 6):
            if hv[i + j] >= up.iat[i] and lv[i + j] <= dn.iat[i]:
                tb[i] = 0.0; break
            if hv[i + j] >= up.iat[i]:
                tb[i] = 1.0; break
            if lv[i + j] <= dn.iat[i]:
                tb[i] = -1.0; break
    X["tb_5d_1atr"] = tb
    X["label_end_1d"] = close_time + pd.Timedelta(days=1)
    X["label_end_5d"] = close_time + pd.Timedelta(days=8)
    X["label_end_10d"] = close_time + pd.Timedelta(days=15)
    X["close"] = c.values; X["close_time"] = close_time
    X = X.replace([np.inf, -np.inf], np.nan)
    if save:
        X.to_parquet(OUT / "features_daily.parquet")
    return X


# ------------------------------------------------------------------ hourly
def build_hourly(save: bool = True) -> pd.DataFrame:
    h1 = load_ohlc("H1").loc["2003":]
    X = pd.DataFrame(index=h1.index)
    c = h1.close
    for k in (1, 2, 4, 8, 24, 120):
        X[f"ret_{k}h"] = _lr(c, k)
    r = np.log(c).diff()
    X["rv_24h_bp"] = r.rolling(24).std() * 1e4; X["rv_120h_bp"] = r.rolling(120).std() * 1e4
    X["rv_ratio_24_120"] = X["rv_24h_bp"] / X["rv_120h_bp"]
    X["range_1h_pips"] = (h1.high - h1.low) / PIP
    X["range_rel_24h"] = X["range_1h_pips"] / X["range_1h_pips"].rolling(24).mean().shift(1)
    hi24 = h1.high.rolling(24).max(); lo24 = h1.low.rolling(24).min()
    X["pos_in_24h_range"] = (c - lo24) / (hi24 - lo24).replace(0, np.nan)
    X["rsi14h"] = F.rsi(c, 14); X["z24"] = F.zscore(c, 24)
    atr = F.atr(h1, 24); X["atr24_pips"] = atr / PIP
    lv = F.prev_day_levels(h1, 22)
    X["dist_pd_high_atr"] = (lv.pd_high - c) / atr; X["dist_pd_low_atr"] = (c - lv.pd_low) / atr
    X["dist_day_open_atr"] = (c - lv.day_open) / atr; X["dist_pivot_atr"] = (c - lv["pivot"]) / atr
    lon = h1.index.tz_convert("Europe/London"); ny = h1.index.tz_convert("America/New_York")
    X["hour_utc"] = h1.index.hour; X["hour_london"] = lon.hour; X["hour_ny"] = ny.hour; X["dow"] = h1.index.dayofweek
    X["is_london"] = ((lon.hour >= 8) & (lon.hour < 17)).astype(float); X["is_ny"] = ((ny.hour >= 8) & (ny.hour < 17)).astype(float)
    # session-so-far returns
    day_key = (h1.index - pd.Timedelta(hours=22)).floor("D")
    X["ret_since_day_open_bp"] = (np.log(c) - np.log(h1.open.groupby(day_key).transform("first"))) * 1e4
    lon_open_mask = (lon.hour == 8) & (lon.minute == 0)
    lon_open_px = pd.Series(np.where(lon_open_mask, h1.open, np.nan), index=h1.index).groupby(day_key).ffill()
    X["ret_since_london_open_bp"] = (np.log(c) - np.log(lon_open_px)) * 1e4
    # events
    ev = _events(); et = ev.time.values
    t = h1.index + pd.Timedelta(hours=1)   # decision time = bar close
    for k in ("fomc", "ecb", "nfp", "cpi"):
        times = et[(ev.kind == k).values]
        pos = np.searchsorted(times, t.values); nxt = np.where(pos < len(times), times[np.minimum(pos, len(times) - 1)], np.datetime64("NaT"))
        X[f"h_to_{k}"] = np.minimum((pd.to_datetime(nxt, utc=True) - t).total_seconds() / 3600, 24 * 45)
        pos2 = np.searchsorted(times, t.values, side="right") - 1; prv = np.where(pos2 >= 0, times[np.maximum(pos2, 0)], np.datetime64("NaT"))
        X[f"h_since_{k}"] = np.minimum((t - pd.to_datetime(prv, utc=True)).total_seconds() / 3600, 24 * 45)
    pos = np.searchsorted(et, t.values); nxt = np.where(pos < len(et), et[np.minimum(pos, len(et) - 1)], np.datetime64("NaT"))
    X["h_to_any_high"] = np.minimum((pd.to_datetime(nxt, utc=True) - t).total_seconds() / 3600, 24 * 10)
    pos2 = np.searchsorted(et, t.values, side="right") - 1; prv = np.where(pos2 >= 0, et[np.maximum(pos2, 0)], np.datetime64("NaT"))
    X["h_since_any_high"] = np.minimum((t - pd.to_datetime(prv, utc=True)).total_seconds() / 3600, 24 * 10)
    # previous-session daily features (macro, positioning, trend state), joined by the session the bar belongs to
    D = pd.read_parquet(OUT / "features_daily.parquet") if (OUT / "features_daily.parquet").exists() else build_daily()
    keep = ["ret_1d", "ret_5d", "ret_21d", "rv_21d_bp", "dist_sma50_atr", "dist_sma200_atr", "adx14", "spread2y", "d_spread2y_5", "d_spread2y_20",
            "fv_resid_z", "vix", "cot_z52", "cot_d4", "usd_factor_5", "usd_factor_20", "dxy_ret_5", "spx_ret_5", "last_surprise_nfp", "last_surprise_cpi", "bd_to_end", "is_month_end"]
    prev = D[keep].copy()
    prev.index = prev.index + pd.Timedelta(days=1)   # known at the start of the next session
    key = (h1.index - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
    prev = prev[~prev.index.duplicated(keep="last")].sort_index()
    joined = pd.merge_asof(pd.DataFrame({"key": key}), prev.rename_axis("key").reset_index(), on="key", direction="backward")
    for col in keep:
        X[f"d_{col}"] = joined[col].values
    # labels
    for k in (1, 4, 8, 24):
        X[f"fwd_{k}h"] = (np.log(c.shift(-k)) - np.log(c)) * 1e4
        X[f"label_end_{k}h"] = h1.index + pd.Timedelta(hours=k + 1)
    X["close"] = c.values
    X = X.replace([np.inf, -np.inf], np.nan)
    if save:
        X.to_parquet(OUT / "features_hourly.parquet")
    return X


if __name__ == "__main__":
    d = build_daily(); print("daily", d.shape, d.index.min(), d.index.max())
    h = build_hourly(); print("hourly", h.shape)
