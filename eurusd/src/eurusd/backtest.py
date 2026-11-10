"""
Bar-based backtester for EUR/USD strategies with realistic execution.

Conventions
-----------
* Prices are BID (HistData convention). Buy fills pay the spread: ask = bid + spread.
  Sell fills receive bid. Spread is given in pips (1 pip = 0.0001).
* A strategy produces a list/DataFrame of *orders*; each order says when it is
  placed (bar index i, decided with information up to and including bar i's close),
  how to enter (market at bar i+1 open, or stop/limit at a price, valid for
  `expiry_bars` bars), stop-loss, take-profit, max holding bars and an optional
  hard exit time.
* Intra-bar ambiguity: if both SL and TP lie inside one bar's range, the default
  assumption is the *worse* outcome (SL first).  If a lower-timeframe (e.g. M1)
  array is supplied, the engine resolves the order of touches with it.
* Results are reported in pips and in R-multiples (profit / initial risk) so that
  strategies with different stop sizes can be compared, and as equity curves with
  fixed-fractional risk sizing.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Iterable, Optional

import numpy as np
import pandas as pd

PIP = 0.0001


@dataclass
class Order:
    i: int                      # bar index at which the decision is made (close of bar i)
    side: int                   # +1 long, -1 short
    entry_type: str = "market"  # 'market' | 'stop' | 'limit'
    entry_price: float = math.nan
    sl: float = math.nan        # absolute price
    tp: float = math.nan        # absolute price
    expiry_bars: int = 1        # for stop/limit: bars (after i) during which the order is live
    max_hold: int = 10**9       # max bars in trade (exit at close of the bar when reached)
    exit_i: int = -1            # hard exit: close the trade at the *close* of this bar index (if >=0)
    tag: str = ""


@dataclass
class Trade:
    order_i: int
    entry_i: int
    exit_i: int
    side: int
    entry: float
    exit: float
    sl: float
    tp: float
    reason: str
    tag: str
    pips: float
    r: float


@dataclass
class CostModel:
    spread_pips: float = 1.0       # round-trip cost is spread (paid once: buy at ask, sell at bid)
    slippage_pips: float = 0.0     # extra adverse slippage per fill (entry and exit at market/stop)
    spread_by_hour: Optional[dict] = None  # optional {utc_hour: spread_pips}

    def spread(self, ts: pd.Timestamp) -> float:
        if self.spread_by_hour is not None:
            return self.spread_by_hour.get(ts.hour, self.spread_pips)
        return self.spread_pips


def _resolve_with_ltf(ltf: pd.DataFrame, t0: pd.Timestamp, t1: pd.Timestamp,
                      side: int, sl: float, tp: float) -> str:
    """Return 'sl' or 'tp' depending on which is touched first within [t0, t1) in the lower-TF data."""
    seg = ltf.loc[t0:t1 - pd.Timedelta(seconds=1)]
    if seg.empty:
        return "sl"
    hi = seg["high"].values
    lo = seg["low"].values
    if side > 0:
        hit_sl = lo <= sl
        hit_tp = hi >= tp
    else:
        hit_sl = hi >= sl
        hit_tp = lo <= tp
    i_sl = np.argmax(hit_sl) if hit_sl.any() else 10**9
    i_tp = np.argmax(hit_tp) if hit_tp.any() else 10**9
    if i_sl == i_tp:
        return "sl"  # same minute: still ambiguous, be conservative
    return "sl" if i_sl < i_tp else "tp"


def run_backtest(df: pd.DataFrame, orders: Iterable[Order], cost: CostModel = CostModel(),
                 ltf: Optional[pd.DataFrame] = None, one_at_a_time: bool = True) -> "BacktestResult":
    """Simulate orders on OHLC bars `df` (UTC index, bid prices).

    one_at_a_time: if True, an order placed while a trade is open is ignored
    (keeps the statistics simple and realistic for a single-position system).
    """
    o = df["open"].values
    h = df["high"].values
    l = df["low"].values
    c = df["close"].values
    idx = df.index
    n = len(df)
    orders = sorted(orders, key=lambda x: x.i)
    trades: list[Trade] = []
    busy_until = -1  # bar index until which we are in a trade

    for od in orders:
        if od.i + 1 >= n:
            continue
        if one_at_a_time and od.i < busy_until:
            continue
        spread = cost.spread(idx[od.i + 1]) * PIP
        slip = cost.slippage_pips * PIP
        side = od.side
        # ---- entry ----
        entry_i = -1
        entry = math.nan
        if od.entry_type == "market":
            entry_i = od.i + 1
            entry = o[entry_i] + (spread + slip if side > 0 else -slip)
        else:
            last = min(n - 1, od.i + od.expiry_bars)
            for j in range(od.i + 1, last + 1):
                if od.entry_type == "stop":
                    # buy stop above market: filled when ask >= price  (bid + spread >= price)
                    if side > 0 and h[j] + spread >= od.entry_price:
                        entry_i = j
                        entry = max(od.entry_price, o[j] + spread) + slip
                        break
                    if side < 0 and l[j] <= od.entry_price:
                        entry_i = j
                        entry = min(od.entry_price, o[j]) - slip
                        break
                elif od.entry_type == "limit":
                    if side > 0 and l[j] + spread <= od.entry_price:
                        entry_i = j
                        entry = min(od.entry_price, o[j] + spread)
                        break
                    if side < 0 and h[j] >= od.entry_price:
                        entry_i = j
                        entry = max(od.entry_price, o[j])
                        break
        if entry_i < 0:
            continue
        sl, tp = od.sl, od.tp
        if side > 0 and not (math.isnan(sl)) and sl >= entry:
            continue  # invalid order
        if side < 0 and not (math.isnan(sl)) and sl <= entry:
            continue
        risk = abs(entry - sl) if not math.isnan(sl) else math.nan
        # ---- exit ----
        exit_i = -1
        exit_px = math.nan
        reason = ""
        last_hold = min(n - 1, entry_i + od.max_hold)
        if od.exit_i >= 0:
            last_hold = min(last_hold, od.exit_i)
        for j in range(entry_i, last_hold + 1):
            # on the entry bar, only the part of the bar after entry counts; we approximate by
            # using the full bar but never allowing an exit better than the entry on the same bar
            # for market orders (conservative).
            bid_hi, bid_lo = h[j], l[j]
            if side > 0:
                sl_hit = (not math.isnan(sl)) and bid_lo <= sl
                tp_hit = (not math.isnan(tp)) and bid_hi >= tp
            else:
                sl_hit = (not math.isnan(sl)) and bid_hi + spread >= sl
                tp_hit = (not math.isnan(tp)) and bid_lo + spread <= tp
            if j == entry_i and od.entry_type == "market":
                # cannot know path within entry bar: treat TP hit on entry bar as not happening
                # unless lower-TF data says otherwise; SL hit is allowed (conservative)
                if tp_hit and not sl_hit and ltf is None:
                    tp_hit = False
            if sl_hit and tp_hit:
                if ltf is not None:
                    t1 = idx[j + 1] if j + 1 < n else idx[j] + (idx[j] - idx[j - 1])
                    which = _resolve_with_ltf(ltf, idx[j], t1, side, sl, tp)
                else:
                    which = "sl"
                sl_hit, tp_hit = which == "sl", which == "tp"
            if sl_hit:
                exit_i = j
                exit_px = sl - (slip if side > 0 else -slip)
                # gap through the stop: fill at open if open is beyond the stop
                if side > 0 and o[j] < sl and j != entry_i:
                    exit_px = o[j] - slip
                if side < 0 and o[j] + spread > sl and j != entry_i:
                    exit_px = o[j] + spread + slip
                reason = "sl"
                break
            if tp_hit:
                exit_i = j
                exit_px = tp
                reason = "tp"
                break
            if j == last_hold:
                exit_i = j
                exit_px = c[j] if side > 0 else c[j] + spread
                reason = "time"
                break
        if exit_i < 0:
            continue
        pnl = (exit_px - entry) * side
        pips = pnl / PIP
        r = pnl / risk if (risk and not math.isnan(risk) and risk > 0) else math.nan
        trades.append(Trade(od.i, entry_i, exit_i, side, entry, exit_px, sl, tp, reason, od.tag, pips, r))
        busy_until = exit_i + 1
    return BacktestResult(trades, df)


class BacktestResult:
    def __init__(self, trades: list[Trade], df: pd.DataFrame):
        self.trades = trades
        self.df = df
        self.tdf = pd.DataFrame([t.__dict__ for t in trades])
        if not self.tdf.empty:
            self.tdf["entry_time"] = df.index[self.tdf["entry_i"].values]
            self.tdf["exit_time"] = df.index[self.tdf["exit_i"].values]

    # ---- metrics ----
    def daily_r(self) -> pd.Series:
        if self.tdf.empty:
            return pd.Series(dtype=float)
        s = self.tdf.set_index("exit_time")["r"].fillna(0.0)
        return s.resample("1D").sum()

    def summary(self, risk_per_trade: float = 0.01) -> dict:
        t = self.tdf
        if t.empty:
            return {"trades": 0}
        r = t["r"].fillna(0.0).values
        pips = t["pips"].values
        wins = r > 0
        gross_win = r[wins].sum()
        gross_loss = -r[~wins].sum()
        pf = gross_win / gross_loss if gross_loss > 0 else math.inf
        d = self.daily_r()
        d = d[d.index.dayofweek < 5]
        n_days = max(1, (t["exit_time"].max() - t["entry_time"].min()).days)
        years = n_days / 365.25
        sharpe = (d.mean() / d.std() * math.sqrt(252)) if d.std() > 0 else 0.0
        # fixed-fractional equity curve
        eq = np.cumprod(1 + risk_per_trade * r)
        peak = np.maximum.accumulate(eq)
        mdd = float(((eq - peak) / peak).min())
        cagr = eq[-1] ** (1 / years) - 1 if years > 0 else math.nan
        tstat = r.mean() / (r.std(ddof=1) / math.sqrt(len(r))) if len(r) > 1 and r.std() > 0 else 0.0
        pw = pips > 0
        pf_pips = pips[pw].sum() / -pips[~pw].sum() if (~pw).any() and pips[~pw].sum() < 0 else math.inf
        t_pips = pips.mean() / (pips.std(ddof=1) / math.sqrt(len(pips))) if len(pips) > 1 and pips.std() > 0 else 0.0
        has_r = bool(np.isfinite(t["r"].values).all())
        return {
            "has_r": has_r,
            "profit_factor_pips": float(pf_pips),
            "t_stat_pips": float(t_pips),
            "trades": int(len(r)),
            "trades_per_year": len(r) / years if years > 0 else math.nan,
            "win_rate": float(wins.mean()) if has_r else float(pw.mean()),
            "avg_r": float(r.mean()),
            "avg_pips": float(pips.mean()),
            "total_pips": float(pips.sum()),
            "profit_factor": float(pf),
            "sharpe": float(sharpe),
            "cagr_1pct_risk": float(cagr),
            "max_dd_1pct_risk": mdd,
            "t_stat": float(tstat),
            "years": years,
            "sl_rate": float((t["reason"] == "sl").mean()),
            "tp_rate": float((t["reason"] == "tp").mean()),
        }

    def by_year(self) -> pd.DataFrame:
        t = self.tdf
        if t.empty:
            return pd.DataFrame()
        g = t.groupby(t["exit_time"].dt.year)
        has_r = bool(np.isfinite(t["r"].values).all())
        col = "r" if has_r else "pips"
        out = pd.DataFrame({
            "trades": g.size(),
            "win_rate": g[col].apply(lambda x: (x > 0).mean()),
            "avg_r": g[col].mean(),
            "sum_r": g[col].sum(),
            "sum_pips": g["pips"].sum(),
        })
        return out


def bootstrap_pvalue(r: np.ndarray, n_boot: int = 2000, seed: int = 0) -> float:
    """P-value that mean(r) <= 0 under a stationary bootstrap of trade R-multiples (iid approx)."""
    r = np.asarray(r, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 5:
        return 1.0
    rng = np.random.default_rng(seed)
    centered = r - r.mean()
    means = np.array([rng.choice(centered, len(r), replace=True).mean() for _ in range(n_boot)])
    return float((means >= r.mean()).mean())


def deflated_sharpe_pvalue(sharpe: float, n_obs: int, n_trials: int, skew: float = 0.0, kurt: float = 3.0) -> float:
    """Probability that an observed annualized-daily Sharpe (converted to per-obs) is a fluke
    given `n_trials` strategies were tried (Bailey & Lopez de Prado 2014, simplified)."""
    from scipy.stats import norm
    if n_obs < 10:
        return 1.0
    sr = sharpe / math.sqrt(252)  # per-day
    # expected max Sharpe of n_trials iid trials with sd of SR estimate
    sd_sr = math.sqrt((1 - skew * sr + (kurt - 1) / 4 * sr ** 2) / (n_obs - 1)) if n_obs > 1 else 1.0
    e_max = sd_sr * ((1 - 0.5772) * norm.ppf(1 - 1 / max(n_trials, 2)) + 0.5772 * norm.ppf(1 - 1 / (max(n_trials, 2) * math.e)))
    z = (sr - e_max) / sd_sr if sd_sr > 0 else 0.0
    return float(1 - norm.cdf(z))
