"""Experiment harness: run a strategy over parameter grids with a fixed
train / validation / holdout protocol and robustness criteria.

Protocol (fixed before any experiment, never changed to fit results):
  TRAIN      2003-01-01 .. 2015-12-31   used to explore and select parameters
  VALIDATE   2016-01-01 .. 2022-12-31   used once per strategy family to confirm
  HOLDOUT    2023-01-01 .. today        touched only by the final system

A strategy "survives" if, on VALIDATE with the parameters chosen on TRAIN:
  * avg R > 0 and t-stat >= 2.0 and profit factor >= 1.15 (after spread + slippage)
  * at least 60 % of calendar years positive in TRAIN+VALIDATE
  * the median of the parameter neighbourhood (all grid points within one step) is also > 0 on TRAIN
"""
from __future__ import annotations

import itertools
import json
import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import CostModel, run_backtest, bootstrap_pvalue
from .strategies import REGISTRY

SPLITS = {
    "train": ("2003-01-01", "2015-12-31"),
    "validate": ("2016-01-01", "2022-12-31"),
    "holdout": ("2023-01-01", "2030-01-01"),
}

RESULTS_DIR = Path(__file__).resolve().parents[2] / "experiments" / "results"


def slice_period(df: pd.DataFrame, period: str, warmup_bars: int = 500) -> pd.DataFrame:
    a, b = SPLITS[period]
    start = df.index.searchsorted(pd.Timestamp(a, tz="UTC"))
    end = df.index.searchsorted(pd.Timestamp(b, tz="UTC") + pd.Timedelta(days=1))
    return df.iloc[max(0, start - warmup_bars):end]


def run_one(df: pd.DataFrame, strategy: str, params: dict, period: str, cost: CostModel,
            ltf: pd.DataFrame | None = None) -> dict:
    sub = slice_period(df, period)
    a, _ = SPLITS[period]
    orders = REGISTRY[strategy](sub, **params)
    # drop orders decided in the warm-up zone
    first = sub.index.searchsorted(pd.Timestamp(a, tz="UTC"))
    orders = [o for o in orders if o.i >= first]
    res = run_backtest(sub, orders, cost, ltf=ltf)
    s = res.summary()
    s.update({"strategy": strategy, "period": period, "params": json.dumps(params, default=str)})
    if s["trades"] > 0:
        by = res.by_year()
        s["years_positive"] = float((by["sum_r"] > 0).mean())
        s["p_boot"] = bootstrap_pvalue(res.tdf["r"].values, n_boot=500)
    return s, res


def grid(param_grid: dict) -> list[dict]:
    keys = list(param_grid)
    return [dict(zip(keys, v)) for v in itertools.product(*[param_grid[k] for k in keys])]


def run_grid(df: pd.DataFrame, strategy: str, param_grid: dict, period: str, cost: CostModel,
             tag: str = "", ltf=None, verbose=True) -> pd.DataFrame:
    rows = []
    t0 = time.time()
    combos = grid(param_grid)
    for k, p in enumerate(combos):
        s, _ = run_one(df, strategy, p, period, cost, ltf)
        rows.append(s)
        if verbose and (k + 1) % 20 == 0:
            print(f"  {strategy} {period}: {k+1}/{len(combos)} ({time.time()-t0:.0f}s)", flush=True)
    out = pd.DataFrame(rows)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out.to_csv(RESULTS_DIR / f"{strategy}{('_' + tag) if tag else ''}_{period}.csv", index=False)
    return out


def neighbourhood_ok(train_df: pd.DataFrame, best: dict, param_grid: dict) -> tuple[bool, float]:
    """Median avg_r of grid points within one step of `best` in every numeric dimension."""
    rows = []
    for _, row in train_df.iterrows():
        p = json.loads(row["params"])
        close = True
        for k, v in best.items():
            if k not in p:
                continue
            vals = sorted(param_grid.get(k, [v]), key=lambda x: (str(type(x)), x))
            if isinstance(v, (int, float)) and not isinstance(v, bool) and len(vals) > 1 and k in param_grid:
                try:
                    pos = vals.index(v)
                    pos2 = vals.index(p[k])
                    if abs(pos - pos2) > 1:
                        close = False
                except ValueError:
                    close = False
            elif p[k] != v:
                close = False
        if close:
            rows.append(row["avg_r"])
    med = float(np.median(rows)) if rows else math.nan
    return (med > 0), med


def verdict(train_best: pd.Series, val: dict, neigh_ok: bool) -> tuple[bool, str]:
    reasons = []
    if not val.get("has_r", True):  # no stop-loss based R: judge on pips
        val = dict(val, avg_r=val.get("avg_pips", 0), t_stat=val.get("t_stat_pips", 0),
                   profit_factor=val.get("profit_factor_pips", 0))
    if val.get("trades", 0) < 30:
        reasons.append("too few validation trades")
    if val.get("avg_r", 0) <= 0:
        reasons.append("negative on validation")
    if val.get("t_stat", 0) < 2.0:
        reasons.append(f"t-stat {val.get('t_stat', 0):.2f} < 2")
    if val.get("profit_factor", 0) < 1.15:
        reasons.append(f"PF {val.get('profit_factor', 0):.2f} < 1.15")
    if val.get("years_positive", 0) < 0.6:
        reasons.append(f"only {val.get('years_positive', 0):.0%} years positive")
    if not neigh_ok:
        reasons.append("parameter neighbourhood not positive on train")
    return (len(reasons) == 0), "; ".join(reasons) if reasons else "survives"
