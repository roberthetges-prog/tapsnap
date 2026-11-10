"""Volatility estimators and forecasts for sizing / regime filters (no direction).

* garman_klass(daily)      : daily variance estimate from OHLC
* realized_var(m5)         : daily realized variance from 5-minute log returns (NY-close days)
* har_forecast(rv)         : HAR-RV (Corsi 2009) one-day-ahead forecast fitted on a rolling window
* vol_target_scale(...)    : position scale = target_vol / forecast_vol, capped
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def garman_klass(d: pd.DataFrame) -> pd.Series:
    return 0.5 * np.log(d["high"] / d["low"]) ** 2 - (2 * np.log(2) - 1) * np.log(d["close"] / d["open"]) ** 2


def realized_var(intraday: pd.DataFrame, day_start_utc_hour: int = 22) -> pd.Series:
    r = np.log(intraday["close"]).diff()
    day = (intraday.index - pd.Timedelta(hours=day_start_utc_hour)).floor("D") + pd.Timedelta(hours=day_start_utc_hour)
    rv = (r ** 2).groupby(day).sum()
    n = r.groupby(day).size()
    return rv[n >= 50]


def har_features(rv: pd.Series) -> pd.DataFrame:
    return pd.DataFrame({"d": rv.shift(1), "w": rv.rolling(5).mean().shift(1), "m": rv.rolling(22).mean().shift(1)})


def har_forecast(rv: pd.Series, window: int = 500) -> pd.Series:
    """Rolling-window OLS HAR forecast of rv[t] using only data < t."""
    X = har_features(rv)
    y = rv
    out = pd.Series(np.nan, index=rv.index)
    vals = X.values
    yv = y.values
    for t in range(window + 22, len(rv)):
        xs = vals[t - window:t]
        ys = yv[t - window:t]
        ok = ~np.isnan(xs).any(axis=1) & ~np.isnan(ys)
        A = np.column_stack([np.ones(ok.sum()), xs[ok]])
        beta, *_ = np.linalg.lstsq(A, ys[ok], rcond=None)
        xt = vals[t]
        if not np.isnan(xt).any():
            out.iloc[t] = beta[0] + xt @ beta[1:]
    return out.clip(lower=1e-10)


def vol_target_scale(forecast_daily_vol: pd.Series, target_annual_vol: float = 0.10, cap: float = 3.0) -> pd.Series:
    return (target_annual_vol / np.sqrt(252) / forecast_daily_vol).clip(upper=cap)
