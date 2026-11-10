"""Indicator and feature library (pure pandas/numpy, no lookahead).

All functions take a UTC-indexed OHLC DataFrame (columns open, high, low, close)
and return Series/DataFrames aligned to it. Every value at time t uses only bars
<= t.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

PIP = 0.0001


def sma(s: pd.Series, n: int) -> pd.Series:
    return s.rolling(n).mean()


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False).mean()


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    up = d.clip(lower=0)
    dn = -d.clip(upper=0)
    au = up.ewm(alpha=1 / n, adjust=False).mean()
    ad = dn.ewm(alpha=1 / n, adjust=False).mean()
    rs = au / ad.replace(0, np.nan)
    return 100 - 100 / (1 + rs)


def true_range(df: pd.DataFrame) -> pd.Series:
    pc = df["close"].shift(1)
    return pd.concat([df["high"] - df["low"], (df["high"] - pc).abs(), (df["low"] - pc).abs()], axis=1).max(axis=1)


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    return true_range(df).ewm(alpha=1 / n, adjust=False).mean()


def bollinger(close: pd.Series, n: int = 20, k: float = 2.0) -> pd.DataFrame:
    m = close.rolling(n).mean()
    sd = close.rolling(n).std(ddof=0)
    return pd.DataFrame({"mid": m, "upper": m + k * sd, "lower": m - k * sd, "z": (close - m) / sd.replace(0, np.nan)})


def donchian(df: pd.DataFrame, n: int = 20) -> pd.DataFrame:
    # excludes the current bar so a breakout of the channel can be detected on bar t
    return pd.DataFrame({"upper": df["high"].rolling(n).max().shift(1), "lower": df["low"].rolling(n).min().shift(1)})


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    line = ema(close, fast) - ema(close, slow)
    sig = ema(line, signal)
    return pd.DataFrame({"macd": line, "signal": sig, "hist": line - sig})


def adx(df: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    up = df["high"].diff()
    dn = -df["low"].diff()
    plus_dm = np.where((up > dn) & (up > 0), up, 0.0)
    minus_dm = np.where((dn > up) & (dn > 0), dn, 0.0)
    tr = true_range(df)
    atr_ = tr.ewm(alpha=1 / n, adjust=False).mean()
    pdi = 100 * pd.Series(plus_dm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / atr_
    mdi = 100 * pd.Series(minus_dm, index=df.index).ewm(alpha=1 / n, adjust=False).mean() / atr_
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return pd.DataFrame({"adx": dx.ewm(alpha=1 / n, adjust=False).mean(), "pdi": pdi, "mdi": mdi})


def stochastic(df: pd.DataFrame, n: int = 14, d: int = 3) -> pd.DataFrame:
    lo = df["low"].rolling(n).min()
    hi = df["high"].rolling(n).max()
    k = 100 * (df["close"] - lo) / (hi - lo).replace(0, np.nan)
    return pd.DataFrame({"k": k, "d": k.rolling(d).mean()})


def keltner(df: pd.DataFrame, n: int = 20, k: float = 1.5, atr_n: int = 10) -> pd.DataFrame:
    m = ema(df["close"], n)
    a = atr(df, atr_n)
    return pd.DataFrame({"mid": m, "upper": m + k * a, "lower": m - k * a})


def supertrend(df: pd.DataFrame, n: int = 10, k: float = 3.0) -> pd.DataFrame:
    a = atr(df, n)
    hl2 = (df["high"] + df["low"]) / 2
    ub = (hl2 + k * a).values
    lb = (hl2 - k * a).values
    c = df["close"].values
    n_ = len(df)
    fub = ub.copy(); flb = lb.copy(); st = np.full(n_, np.nan); dir_ = np.ones(n_)
    for i in range(1, n_):
        fub[i] = ub[i] if (ub[i] < fub[i - 1] or c[i - 1] > fub[i - 1]) else fub[i - 1]
        flb[i] = lb[i] if (lb[i] > flb[i - 1] or c[i - 1] < flb[i - 1]) else flb[i - 1]
        if np.isnan(st[i - 1]) or st[i - 1] == fub[i - 1]:
            if c[i] <= fub[i]:
                st[i] = fub[i]; dir_[i] = -1
            else:
                st[i] = flb[i]; dir_[i] = 1
        else:
            if c[i] >= flb[i]:
                st[i] = flb[i]; dir_[i] = 1
            else:
                st[i] = fub[i]; dir_[i] = -1
    return pd.DataFrame({"st": st, "dir": dir_}, index=df.index)


# ---------- daily / session structure (for intraday bars) ----------

def daily_ohlc(df: pd.DataFrame, day_start_utc_hour: int = 0) -> pd.DataFrame:
    """Daily bars of an intraday frame, days starting at `day_start_utc_hour` UTC."""
    shifted = df.index - pd.Timedelta(hours=day_start_utc_hour)
    g = df.groupby(shifted.floor("D"))
    out = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(),
                        "close": g["close"].last(), "n": g.size()})
    out.index = out.index + pd.Timedelta(hours=day_start_utc_hour)
    return out


def prev_day_levels(df: pd.DataFrame, day_start_utc_hour: int = 0) -> pd.DataFrame:
    """Previous day's O/H/L/C and classic pivots, aligned to each intraday bar (no lookahead)."""
    d = daily_ohlc(df, day_start_utc_hour)
    prev = d.shift(1)
    piv = (prev["high"] + prev["low"] + prev["close"]) / 3
    lv = pd.DataFrame({
        "pd_open": prev["open"], "pd_high": prev["high"], "pd_low": prev["low"], "pd_close": prev["close"],
        "pivot": piv,
        "r1": 2 * piv - prev["low"], "s1": 2 * piv - prev["high"],
        "r2": piv + (prev["high"] - prev["low"]), "s2": piv - (prev["high"] - prev["low"]),
        "r3": prev["high"] + 2 * (piv - prev["low"]), "s3": prev["low"] - 2 * (prev["high"] - piv),
        "day_open": d["open"],
    })
    # camarilla
    rng = prev["high"] - prev["low"]
    lv["cam_r3"] = prev["close"] + rng * 1.1 / 4
    lv["cam_s3"] = prev["close"] - rng * 1.1 / 4
    lv["cam_r4"] = prev["close"] + rng * 1.1 / 2
    lv["cam_s4"] = prev["close"] - rng * 1.1 / 2
    key = (df.index - pd.Timedelta(hours=day_start_utc_hour)).floor("D") + pd.Timedelta(hours=day_start_utc_hour)
    return lv.reindex(key).set_index(df.index)


def session_range(df: pd.DataFrame, start_hour: int, end_hour: int) -> pd.DataFrame:
    """High/low of the window [start_hour, end_hour) UTC of the *current* day, available only
    from end_hour onwards (NaN before). Handles windows that do not cross midnight."""
    day = df.index.floor("D")
    hrs = df.index.hour + df.index.minute / 60
    inwin = (hrs >= start_hour) & (hrs < end_hour)
    hi = pd.Series(np.where(inwin, df["high"], np.nan), index=df.index).groupby(day).cummax().groupby(day).ffill()
    lo = pd.Series(np.where(inwin, df["low"], np.nan), index=df.index).groupby(day).cummin().groupby(day).ffill()
    done = hrs >= end_hour
    return pd.DataFrame({"win_high": hi.where(done), "win_low": lo.where(done)})


def time_features(df: pd.DataFrame) -> pd.DataFrame:
    ix = df.index
    return pd.DataFrame({"hour": ix.hour, "minute": ix.minute, "dow": ix.dayofweek, "month": ix.month,
                         "dom": ix.day, "year": ix.year}, index=ix)


def realized_vol(close: pd.Series, n: int) -> pd.Series:
    return np.log(close).diff().rolling(n).std()


def zscore(s: pd.Series, n: int) -> pd.Series:
    return (s - s.rolling(n).mean()) / s.rolling(n).std(ddof=0)
