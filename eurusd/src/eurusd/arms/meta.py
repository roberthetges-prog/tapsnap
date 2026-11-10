"""Meta-combination of the research arms' OUT-OF-SAMPLE position streams.

Each arm delivers positions (already walk-forward OOS) with per-period net P&L in bp. The combiner
aligns them to a daily grid (sum of each arm's net bp per NY-close session), then forms weights for
year Y from the arms' OOS P&L of years < Y only (walk-forward on top of walk-forward):
  * equal weight (EW) of arms with positive trailing t-stat
  * weights proportional to trailing t-stat, clipped at 0 (TW)
  * non-negative least squares on trailing daily P&L (NNLS)
Each stream is vol-scaled to the same trailing risk before combining, so arms with different
activity levels get comparable weight. Reports the usual table with n_arms deflation.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls

from ..wf import YEARS, _agg, deflated_sharpe_p

RES = Path(__file__).resolve().parents[3] / "experiments" / "results" / "arms"


def load_arm_daily(name: str) -> pd.Series:
    """Net bp per NY-close session for an arm (sums intraday/event P&L into the session it was earned in)."""
    p = RES / f"{name}_positions.parquet"
    if not p.exists():
        return pd.Series(dtype=float)
    d = pd.read_parquet(p)
    if "net_bp" not in d:
        return pd.Series(dtype=float)
    idx = pd.DatetimeIndex(d.index)
    if idx.tz is None:
        idx = idx.tz_localize("UTC")
    # session key: NY-close day that contains the decision time (session starts 22:00 UTC)
    key = (idx - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
    return d["net_bp"].groupby(key).sum().sort_index()


def combine(arms: list[str], method: str = "TW", lookback_years: int = 20, min_history_years: int = 3,
            target_bp: float = 25.0) -> tuple[pd.DataFrame, pd.DataFrame]:
    streams = {a: load_arm_daily(a) for a in arms}
    streams = {a: s for a, s in streams.items() if len(s) > 100}
    df = pd.DataFrame(streams).fillna(0.0)
    df = df[df.index.year >= 2010]
    out = pd.Series(0.0, index=df.index)
    weights_hist = {}
    for Y in sorted(set(df.index.year)):
        hist = df[(df.index.year < Y) & (df.index.year >= Y - lookback_years)]
        if hist.index.year.nunique() < min_history_years:
            continue
        scale = {a: target_bp / max(hist[a].std(), 1e-9) for a in df.columns}
        hs = hist * pd.Series(scale)
        tstats = hs.mean() / hs.std().replace(0, np.nan) * np.sqrt(len(hs))
        if method == "EW":
            w = (tstats > 0).astype(float)
        elif method == "TW":
            w = tstats.clip(lower=0)
        elif method == "NNLS":
            A = hs.fillna(0.0).values
            b = np.full(len(hs), target_bp / 5)   # target a steady positive drift
            w = pd.Series(nnls(A, b)[0], index=df.columns)
        else:
            raise ValueError(method)
        if w.sum() <= 0:
            weights_hist[Y] = w
            continue
        w = w / w.sum()
        weights_hist[Y] = w
        cur = df[df.index.year == Y] * pd.Series(scale)
        out.loc[cur.index] = (cur * w).sum(axis=1)
    # bring the combined stream back to a 1-unit position scale: divide by the typical scale factor (information only)
    pnl = pd.DataFrame({"net_bp": out, "pos": (out != 0).astype(float)})
    return pnl, pd.DataFrame(weights_hist).T


def report_combo(pnl: pd.DataFrame, name: str, n_arms: int) -> pd.DataFrame:
    rows = []
    net = pnl["net_bp"]
    for Y in sorted(set(net.index.year)):
        rows.append({"period": str(Y), **_agg(net[net.index.year == Y], 252)})
    for label, a, b in (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026), ("2013-2026", 2013, 2026)):
        x = net[(net.index.year >= a) & (net.index.year <= b)]
        r = {"period": label, **_agg(x, 252)}
        if label == "2010-2026":
            r["deflated_sharpe_p"] = deflated_sharpe_p(r["sharpe"], r["n"], n_arms, x, 252)
        rows.append(r)
    out = pd.DataFrame(rows)
    out.insert(0, "combo", name)
    return out


if __name__ == "__main__":
    import sys
    arms = sys.argv[1:] or [p.name.replace("_positions.parquet", "") for p in RES.glob("*_positions.parquet")]
    print("arms:", arms)
    for m in ("EW", "TW", "NNLS"):
        pnl, w = combine(arms, m)
        print(f"\n== {m}\n", report_combo(pnl, m, len(arms) * 3).round(3).to_string())
        print("weights by year:\n", w.round(2).to_string())
