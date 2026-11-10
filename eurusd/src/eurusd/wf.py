"""Walk-forward harness shared by all research arms.

Protocol (fixed before any arm runs; do not change it to fit results):
* Yearly expanding-window walk-forward. For test year Y (2010..2026) a model may use only rows whose
  label is fully known before Y-01-01 (the caller must pass `label_end` so rows whose forward window
  spills into the test year are dropped). Any hyper-parameter choice happens INSIDE the training
  window (time-ordered CV), never on the test year.
* Positions are in units of "fraction of equity risked"; P&L = position * forward return (bp) with
  costs charged per unit turnover (1.2 pips retail; 0.6 pips reported as sensitivity).
* Report: per-year Sharpe / t / return, plus 2010-2026, 2016-2026 and 2023-2026 aggregates, and the
  deflated Sharpe probability given the declared number of arms.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import numpy as np
import pandas as pd
from scipy.stats import norm

YEARS = list(range(2010, 2027))
COST_PIPS_RETAIL = 1.2
COST_PIPS_LOW = 0.6


def walk_forward(df: pd.DataFrame, fit: Callable[[pd.DataFrame], object], predict: Callable[[object, pd.DataFrame], pd.Series],
                 label_end: pd.Series, years=YEARS, min_train_years: int = 5, verbose: bool = True) -> pd.Series:
    """df: feature+label frame with a UTC DatetimeIndex. label_end: for each row, the UTC time at which its
    label becomes known. Returns the out-of-sample prediction series (same index, NaN where not predicted)."""
    pred = pd.Series(np.nan, index=df.index)
    first_year = df.index.year.min()
    for Y in years:
        if Y - first_year < min_train_years:
            continue
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC")
        end = pd.Timestamp(f"{Y + 1}-01-01", tz="UTC")
        train = df[(label_end < start)]
        test = df[(df.index >= start) & (df.index < end)]
        if len(train) < 200 or test.empty:
            continue
        model = fit(train)
        p = predict(model, test)
        pred.loc[test.index] = np.asarray(p, dtype=float)
        if verbose:
            print(f"  year {Y}: train {len(train)} rows, test {len(test)}", flush=True)
    return pred


def pnl_from_positions(pos: pd.Series, fwd_ret_bp: pd.Series, price: pd.Series, cost_pips: float = COST_PIPS_RETAIL,
                       bars_per_period: int = 1) -> pd.DataFrame:
    """pos in [-1, 1] (fraction of a unit position), fwd_ret_bp the label return over the holding period.
    Cost per unit of turnover = cost_pips converted to bp at the current price."""
    pos = pos.fillna(0.0)
    cost_bp = cost_pips * 1e-4 / price * 1e4
    turnover = pos.diff().abs().fillna(pos.abs())
    gross = pos * fwd_ret_bp
    net = gross - turnover * cost_bp
    return pd.DataFrame({"pos": pos, "gross_bp": gross, "net_bp": net, "turnover": turnover})


def _agg(x: pd.Series, periods_per_year: float) -> dict:
    x = x.dropna()
    if len(x) < 10 or x.std() == 0:
        return {"n": int(len(x)), "sharpe": 0.0, "t": 0.0, "mean_bp": float(x.mean()) if len(x) else 0.0, "sum_bp": float(x.sum())}
    return {"n": int(len(x)), "sharpe": float(x.mean() / x.std() * math.sqrt(periods_per_year)), "t": float(x.mean() / x.std() * math.sqrt(len(x))),
            "mean_bp": float(x.mean()), "sum_bp": float(x.sum())}


def report(pnl: pd.DataFrame, periods_per_year: float = 252, name: str = "", n_arms: int = 1) -> pd.DataFrame:
    """Per-year and aggregate statistics of net P&L (bp per period). periods_per_year: 252 for daily positions,
    ~6000 for hourly bars that trade every hour, etc. For sparse positions pass the number of *decision* periods."""
    rows = []
    net = pnl["net_bp"]
    for Y in sorted(set(net.index.year)):
        rows.append({"period": str(Y), **_agg(net[net.index.year == Y], periods_per_year), "active_frac": float((pnl["pos"][pnl.index.year == Y] != 0).mean())})
    for label, a, b in (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026), ("2010-2015", 2010, 2015), ("2016-2022", 2016, 2022)):
        x = net[(net.index.year >= a) & (net.index.year <= b)]
        r = {"period": label, **_agg(x, periods_per_year), "active_frac": float((pnl["pos"][(pnl.index.year >= a) & (pnl.index.year <= b)] != 0).mean())}
        if label == "2010-2026":
            r["deflated_sharpe_p"] = deflated_sharpe_p(r["sharpe"], r["n"], n_arms, x, periods_per_year)
        rows.append(r)
    out = pd.DataFrame(rows)
    out.insert(0, "arm", name)
    return out


def deflated_sharpe_p(sharpe_ann: float, n: int, n_trials: int, x: pd.Series, periods_per_year: float) -> float:
    """Probability that the observed Sharpe is below the expected maximum of n_trials zero-skill trials
    (Bailey & Lopez de Prado 2014). Small p => the Sharpe is unlikely to be a selection artefact."""
    if n < 20:
        return 1.0
    sr = sharpe_ann / math.sqrt(periods_per_year)
    skew = float(pd.Series(x).skew()) if len(x) > 3 else 0.0
    kurt = float(pd.Series(x).kurt()) + 3 if len(x) > 3 else 3.0
    sd_sr = math.sqrt(max(1e-12, (1 - skew * sr + (kurt - 1) / 4 * sr ** 2) / (n - 1)))
    e_max = sd_sr * ((1 - 0.5772) * norm.ppf(1 - 1 / max(n_trials, 2)) + 0.5772 * norm.ppf(1 - 1 / (max(n_trials, 2) * math.e)))
    return float(1 - norm.cdf((sr - e_max) / sd_sr))


def to_positions(pred: pd.Series, scale: str = "sign", threshold: float = 0.0, vol: pd.Series | None = None, target_vol_bp: float | None = None) -> pd.Series:
    """Turn a forecast into a position in [-1,1]. 'sign': +-1 when |pred| > threshold. 'linear': clip(pred/threshold).
    Optional vol scaling: position *= min(1, target_vol_bp / vol)."""
    p = pred.copy()
    if scale == "sign":
        pos = np.sign(p).where(p.abs() > threshold, 0.0)
    else:
        pos = (p / max(threshold, 1e-9)).clip(-1, 1).where(p.abs() > 0, 0.0)
    if vol is not None and target_vol_bp is not None:
        pos = pos * (target_vol_bp / vol.replace(0, np.nan)).clip(upper=1.0).fillna(0.0)
    return pos.fillna(0.0)
