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
    oco: int = -1               # one-cancels-other group id (orders with the same id cancel each other on fill)


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


def _limit_entry_bar_ltf(ltf: pd.DataFrame, t0, t1, side: int, level: float, sl: float, tp: float, spread: float) -> str:
    """For a limit order filled inside bar [t0,t1): find the first minute that touches the limit
    level, then return 'tp' / 'sl' / '' depending on what is touched first AFTER the fill minute."""
    seg = ltf.loc[t0:t1 - pd.Timedelta(seconds=1)]
    if seg.empty:
        return ""
    hi = seg["high"].values
    lo = seg["low"].values
    if side > 0:
        filled = lo + spread <= level
    else:
        filled = hi >= level
    if not filled.any():
        return ""
    k = int(np.argmax(filled))
    hi, lo = hi[k:], lo[k:]
    if side > 0:
        hit_sl = lo <= sl if not math.isnan(sl) else np.zeros(len(lo), bool)
        hit_tp = hi >= tp if not math.isnan(tp) else np.zeros(len(hi), bool)
    else:
        hit_sl = hi + spread >= sl if not math.isnan(sl) else np.zeros(len(hi), bool)
        hit_tp = lo + spread <= tp if not math.isnan(tp) else np.zeros(len(lo), bool)
    i_sl = int(np.argmax(hit_sl)) if hit_sl.any() else 10**9
    i_tp = int(np.argmax(hit_tp)) if hit_tp.any() else 10**9
    if i_sl == i_tp:
        return "sl" if i_sl < 10**9 else ""
    return "sl" if i_sl < i_tp else "tp"


def _first_touch_minute(ltf, t0, t1, side, entry_type, level, spread):
    seg = ltf.loc[t0:t1 - pd.Timedelta(seconds=1)]
    if seg.empty:
        return None
    hi = seg["high"].values
    lo = seg["low"].values
    if entry_type == "stop":
        touched = (hi + spread >= level) if side > 0 else (lo <= level)
    else:
        touched = (lo + spread <= level) if side > 0 else (hi >= level)
    return int(np.argmax(touched)) if touched.any() else None


def run_backtest(df: pd.DataFrame, orders: Iterable[Order], cost: CostModel = CostModel(),
                 ltf: Optional[pd.DataFrame] = None, one_at_a_time: bool = True) -> "BacktestResult":
    """Chronological simulation of orders on OHLC bars `df` (UTC index, bid prices).

    * An order decided at bar i becomes live at bar i+1: market orders fill at that open,
      stop/limit orders wait for their level during `expiry_bars` bars.
    * Only one position at a time (one_at_a_time): while a trade is open, nothing else fills;
      a market order that arrives while a trade is open is dropped, pending orders keep waiting.
    * Orders sharing an `oco` id cancel each other when one fills (one-cancels-other). Orders
      placed at the same bar with the same tag are treated as an OCO pair automatically.
    * When several pending orders are touched on the same bar, the one touched first is filled.
      With lower-timeframe data (`ltf`) the order of touches is read from it; without it, the
      level closest to the bar's open is assumed to be touched first.
    """
    o = df["open"].values
    h = df["high"].values
    l = df["low"].values
    c = df["close"].values
    idx = df.index
    n = len(df)
    orders = sorted(orders, key=lambda x: x.i)
    # automatic OCO grouping: same decision bar + same tag
    auto = {}
    for od in orders:
        if od.oco < 0:
            auto.setdefault((od.i, od.tag), []).append(od)
    next_id = 10**6
    for grp in auto.values():
        if len(grp) > 1:
            for od in grp:
                od.oco = next_id
            next_id += 1
    trades: list[Trade] = []
    pending: list[Order] = []
    pos = None  # dict with order, entry_i, entry, sl, tp, risk, spread, slip, last_hold
    k = 0       # pointer into orders
    for j in range(n):
        spread = cost.spread(idx[j]) * PIP
        slip = cost.slippage_pips * PIP
        # ---- activate orders decided at bar j-1
        while k < len(orders) and orders[k].i == j - 1:
            od = orders[k]
            k += 1
            if od.entry_type == "market":
                if pos is not None and one_at_a_time:
                    continue
                side = od.side
                entry = o[j] + (spread + slip if side > 0 else -slip)
                pos = _open(od, j, entry, spread, slip, n)
                if pos is None:
                    continue
                if od.oco >= 0:
                    pending = [p for p in pending if p.oco != od.oco]
            else:
                pending.append(od)
        while k < len(orders) and orders[k].i < j - 1:
            k += 1  # orders decided before the simulation start (should not happen)
        # ---- manage open position on bar j
        if pos is not None:
            done = _check_exit(pos, j, o, h, l, c, idx, n, ltf, entry_bar=(pos["entry_i"] == j))
            if done is not None:
                trades.append(done)
                pos = None
                # nothing else may fill on the exit bar (conservative)
                pending = [p for p in pending if j < p.i + p.expiry_bars]
                continue
        # ---- expire pending orders
        pending = [p for p in pending if j <= p.i + p.expiry_bars]
        if pos is not None or not pending:
            continue
        # ---- fills of pending orders on bar j
        touched = []
        for p in pending:
            side = p.side
            if p.entry_type == "stop":
                hit = (h[j] + spread >= p.entry_price) if side > 0 else (l[j] <= p.entry_price)
            else:
                hit = (l[j] + spread <= p.entry_price) if side > 0 else (h[j] >= p.entry_price)
            if hit:
                touched.append(p)
        if not touched:
            continue
        if len(touched) > 1:
            if ltf is not None:
                t1 = idx[j + 1] if j + 1 < n else idx[j] + (idx[j] - idx[j - 1])
                key = {id(p): _first_touch_minute(ltf, idx[j], t1, p.side, p.entry_type, p.entry_price, spread) for p in touched}
                touched.sort(key=lambda p: (key[id(p)] if key[id(p)] is not None else 10**9, abs(p.entry_price - o[j])))
            else:
                touched.sort(key=lambda p: abs(p.entry_price - o[j]))
        p = touched[0]
        side = p.side
        if p.entry_type == "stop":
            entry = (max(p.entry_price, o[j] + spread) + slip) if side > 0 else (min(p.entry_price, o[j]) - slip)
        else:
            entry = min(p.entry_price, o[j] + spread) if side > 0 else max(p.entry_price, o[j])
        pending = [q for q in pending if q is not p and not (p.oco >= 0 and q.oco == p.oco)]
        pos = _open(p, j, entry, spread, slip, n)
        if pos is None:
            continue
        done = _check_exit(pos, j, o, h, l, c, idx, n, ltf, entry_bar=True)
        if done is not None:
            trades.append(done)
            pos = None
            pending = [q for q in pending if j < q.i + q.expiry_bars]
    return BacktestResult(trades, df)


def _open(od: Order, j: int, entry: float, spread: float, slip: float, n: int):
    sl, tp = od.sl, od.tp
    side = od.side
    if side > 0 and not math.isnan(sl) and sl >= entry:
        return None
    if side < 0 and not math.isnan(sl) and sl <= entry:
        return None
    if side > 0 and not math.isnan(tp) and tp <= entry:
        return None
    if side < 0 and not math.isnan(tp) and tp >= entry:
        return None
    risk = abs(entry - sl) if not math.isnan(sl) else math.nan
    last_hold = min(n - 1, j + od.max_hold)
    if od.exit_i >= 0:
        last_hold = min(last_hold, max(od.exit_i, j))
    return dict(order=od, entry_i=j, entry=entry, sl=sl, tp=tp, risk=risk, spread=spread, slip=slip, last_hold=last_hold)


def _check_exit(pos, j, o, h, l, c, idx, n, ltf, entry_bar: bool):
    od = pos["order"]
    side = od.side
    sl, tp, spread, slip = pos["sl"], pos["tp"], pos["spread"], pos["slip"]
    if side > 0:
        sl_hit = (not math.isnan(sl)) and l[j] <= sl
        tp_hit = (not math.isnan(tp)) and h[j] >= tp
    else:
        sl_hit = (not math.isnan(sl)) and h[j] + spread >= sl
        tp_hit = (not math.isnan(tp)) and l[j] + spread <= tp
    exit_px = math.nan
    reason = ""
    if entry_bar and od.entry_type == "limit" and tp_hit:
        # a limit fills on a pull-back: the bar's extreme beyond the target may precede the fill
        if ltf is None:
            tp_hit = False
        else:
            t1 = idx[j + 1] if j + 1 < n else idx[j] + (idx[j] - idx[j - 1])
            which = _limit_entry_bar_ltf(ltf, idx[j], t1, side, od.entry_price, sl, tp, spread)
            sl_hit, tp_hit = which == "sl", which == "tp"
    if sl_hit and tp_hit:
        if ltf is not None:
            t1 = idx[j + 1] if j + 1 < n else idx[j] + (idx[j] - idx[j - 1])
            which = _resolve_with_ltf(ltf, idx[j], t1, side, sl, tp)
        else:
            which = "sl"
        sl_hit, tp_hit = which == "sl", which == "tp"
    if sl_hit:
        exit_px = sl - (slip if side > 0 else -slip)
        if not entry_bar:  # gap through the stop
            if side > 0 and o[j] < sl:
                exit_px = o[j] - slip
            if side < 0 and o[j] + spread > sl:
                exit_px = o[j] + spread + slip
        reason = "sl"
    elif tp_hit:
        exit_px = tp
        reason = "tp"
    elif j >= pos["last_hold"]:
        exit_px = c[j] if side > 0 else c[j] + spread
        reason = "time"
    if not reason:
        return None
    entry = pos["entry"]
    pnl = (exit_px - entry) * side
    risk = pos["risk"]
    r = pnl / risk if (risk and not math.isnan(risk) and risk > 0) else math.nan
    return Trade(od.i, pos["entry_i"], j, side, entry, exit_px, sl, tp, reason, od.tag, pnl / PIP, r)


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
