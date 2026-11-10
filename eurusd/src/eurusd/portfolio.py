"""Combine several strategy results into one portfolio and evaluate it.

Each strategy contributes its trade list (R-multiples or pips). Daily P&L per
strategy is aggregated (fixed-fractional risk per trade), then combined with
weights. Reports correlation between strategies, combined Sharpe, drawdown,
and per-year results. Used for the final HOLDOUT evaluation only once.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

from .backtest import BacktestResult


def daily_pnl(res: BacktestResult, risk: float = 0.01, use_pips_if_no_r: float = 20.0) -> pd.Series:
    """Daily P&L as a fraction of equity. Trades without a stop are scaled as pips / use_pips_if_no_r."""
    t = res.tdf
    if t.empty:
        return pd.Series(dtype=float)
    r = t["r"].where(np.isfinite(t["r"]), t["pips"] / use_pips_if_no_r)
    s = pd.Series(r.values * risk, index=t["exit_time"].values)
    s = s.groupby(pd.DatetimeIndex(s.index).floor("D")).sum()
    return s


def combine(pnls: dict[str, pd.Series], weights: dict[str, float] | None = None) -> pd.DataFrame:
    df = pd.DataFrame(pnls).fillna(0.0)
    df = df[df.index.dayofweek < 5]
    w = pd.Series(weights or {k: 1.0 for k in df.columns})
    df["portfolio"] = (df[w.index] * w).sum(axis=1)
    return df


def stats(daily: pd.Series) -> dict:
    d = daily.dropna()
    if d.empty:
        return {}
    eq = (1 + d).cumprod()
    peak = eq.cummax()
    years = max((d.index[-1] - d.index[0]).days / 365.25, 1e-9)
    return {
        "days": int(len(d)),
        "ann_return": float(eq.iloc[-1] ** (1 / years) - 1),
        "ann_vol": float(d.std() * math.sqrt(252)),
        "sharpe": float(d.mean() / d.std() * math.sqrt(252)) if d.std() > 0 else 0.0,
        "max_dd": float(((eq - peak) / peak).min()),
        "t_stat": float(d.mean() / d.std() * math.sqrt(len(d))) if d.std() > 0 else 0.0,
        "pct_days_positive": float((d > 0).mean()),
    }


def by_year(daily: pd.Series) -> pd.Series:
    return daily.groupby(daily.index.year).sum()


def correlation(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in df.columns if c != "portfolio"]
    return df[cols].corr()
