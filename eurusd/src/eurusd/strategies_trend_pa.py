"""Catalogue entries T01-T18 (breakout/trend), V01-V04 (volatility filters) and P01-P12
(price action) implemented on top of the shared engine.

Every strategy is `f(df, **params) -> list[Order]`, decided at the close of bar i with
information <= i.  Conventions used throughout this module:

* "exit_i" exits (opposite signal, trailing-stop touch, time) close the trade at the close
  of that bar (engine semantics).  A trailing stop is therefore filled at the close of the
  bar on which it is touched, not at the stop level - a small, direction-neutral approximation.
* The engine takes one position at a time and ignores an order placed on the bar a trade is
  closed.  Flip (stop-and-reverse) systems therefore emit the entry at the flip bar AND a
  fallback copy one bar later (`_emit`), so a reversal is entered with a one-bar delay instead
  of being lost.
* Volume is not available (always 0), so every "volume" condition in the catalogue is dropped.
"""
from __future__ import annotations

import math
from functools import lru_cache
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import Order
from . import features as F
from .strategies import REGISTRY

PIP = 0.0001
MACRO = Path(__file__).resolve().parents[2] / "data" / "macro"
BPD = {"D1": 1, "H4": 6, "H1": 24, "M30": 48, "M15": 96, "M5": 288}


# ----------------------------------------------------------------------------- helpers
def _bpd(df) -> int:
    step = (df.index[1:] - df.index[:-1]).min()
    return int(pd.Timedelta("1D") / step)


def _next_true(mask: np.ndarray) -> np.ndarray:
    """nxt[i] = smallest j >= i with mask[j], else len(mask)."""
    n = len(mask)
    idx = np.where(mask, np.arange(n), n)
    return np.minimum.accumulate(idx[::-1])[::-1]


def _exit_at_hour(df, idx, exit_hour):
    """Index of the last bar that *starts* before `exit_hour` UTC on the same calendar day as bar idx
    (so the trade is closed at that bar's close), vectorised, weekend/hole safe."""
    idx = np.asarray(idx)
    targets = df.index[idx].floor("D") + pd.Timedelta(hours=exit_hour)
    pos = df.index.searchsorted(targets, side="left") - 1
    return np.maximum(pos, idx)


def _emit(orders, n, i, side, sl, tp, exit_i, tag, fallback=True, max_hold=10**9):
    if i + 1 >= n:
        return
    if exit_i >= n:
        exit_i = -1
    orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, exit_i=int(exit_i), tag=tag, max_hold=max_hold))
    if fallback and i + 2 < n and (exit_i < 0 or exit_i > i + 1):
        orders.append(Order(i=int(i + 1), side=side, sl=sl, tp=tp, exit_i=int(exit_i), tag=tag + "_fb", max_hold=max_hold))


def fractals(df, k=2):
    """Williams fractal swing highs/lows with k bars each side. Swing at i is *confirmed* at i+k."""
    h = df["high"].values
    l = df["low"].values
    n = len(df)
    sh = np.zeros(n, bool)
    sl = np.zeros(n, bool)
    if n > 2 * k:
        sh[k:n - k] = True
        sl[k:n - k] = True
        for d in range(1, k + 1):
            sh[k:n - k] &= (h[k:n - k] > h[k - d:n - k - d]) & (h[k:n - k] >= h[k + d:n - k + d])
            sl[k:n - k] &= (l[k:n - k] < l[k - d:n - k - d]) & (l[k:n - k] <= l[k + d:n - k + d])
    return sh, sl


def zigzag(df, k=5):
    """Alternating pivot list [(idx, price, +1 high/-1 low)] built from fractals in time order.
    Consecutive same-type pivots are merged (the more extreme one is kept).  Each pivot is known
    from bar idx + k.  Returns the list and, for each pivot position, the list state is reconstructable
    because merging only ever replaces the last element."""
    sh, sl = fractals(df, k)
    h = df["high"].values
    l = df["low"].values
    piv = []
    events = []  # (confirm_bar, position_in_list) for each append/replace so callers can replay
    for i in np.flatnonzero(sh | sl):
        cands = []
        if sh[i]:
            cands.append((i, h[i], 1))
        if sl[i]:
            cands.append((i, l[i], -1))
        for p in cands:
            if piv and piv[-1][2] == p[2]:
                if (p[2] == 1 and p[1] >= piv[-1][1]) or (p[2] == -1 and p[1] <= piv[-1][1]):
                    piv[-1] = p
                    events.append((i + k, len(piv) - 1))
                continue
            piv.append(p)
            events.append((i + k, len(piv) - 1))
    return piv, events


def heikin_ashi(df):
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    hc = (o + h + l + c) / 4
    ho = np.empty(n)
    ho[0] = o[0]
    for i in range(1, n):
        ho[i] = (ho[i - 1] + hc[i - 1]) / 2
    hh = np.maximum.reduce([h, ho, hc])
    hl = np.minimum.reduce([l, ho, hc])
    return pd.DataFrame({"ha_open": ho, "ha_high": hh, "ha_low": hl, "ha_close": hc}, index=df.index)


def psar(df, af0=0.02, step=0.02, af_max=0.2):
    h, l = df["high"].values, df["low"].values
    n = len(df)
    sar = np.full(n, np.nan)
    trend = np.ones(n)
    if n < 3:
        return pd.DataFrame({"sar": sar, "dir": trend}, index=df.index)
    up = h[1] > h[0]
    ep = h[1] if up else l[1]
    s = l[0] if up else h[0]
    af = af0
    for i in range(1, n):
        s = s + af * (ep - s)
        if up:
            s = min(s, l[i - 1], l[i - 2] if i >= 2 else l[i - 1])
            if l[i] < s:  # reversal
                up = False
                s = ep
                ep = l[i]
                af = af0
            else:
                if h[i] > ep:
                    ep = h[i]
                    af = min(af + step, af_max)
        else:
            s = max(s, h[i - 1], h[i - 2] if i >= 2 else h[i - 1])
            if h[i] > s:
                up = True
                s = ep
                ep = h[i]
                af = af0
            else:
                if l[i] < ep:
                    ep = l[i]
                    af = min(af + step, af_max)
        sar[i] = s
        trend[i] = 1 if up else -1
    return pd.DataFrame({"sar": sar, "dir": trend}, index=df.index)


def ichimoku(df, tenkan=9, kijun=26, senkou_b=52, disp=26):
    h, l = df["high"], df["low"]
    t = (h.rolling(tenkan).max() + l.rolling(tenkan).min()) / 2
    k = (h.rolling(kijun).max() + l.rolling(kijun).min()) / 2
    sa = ((t + k) / 2).shift(disp)          # cloud visible at bar i was computed at i-26
    sb = ((h.rolling(senkou_b).max() + l.rolling(senkou_b).min()) / 2).shift(disp)
    return pd.DataFrame({"tenkan": t, "kijun": k, "span_a": sa, "span_b": sb,
                         "cloud_top": np.maximum(sa, sb), "cloud_bot": np.minimum(sa, sb)})


def _trail_exit(h, l, c, base_long, base_short, entry_i, side, max_bars=5000):
    """First bar j > entry_i where the ratcheted trailing stop (built from base_* arrays, which are
    'level' series like HH-k*ATR) computed on bars entry_i..j-1 is touched by bar j.  -1 if never."""
    n = len(h)
    end = min(n, entry_i + max_bars)
    if entry_i + 1 >= n:
        return -1
    if side > 0:
        stop = np.maximum.accumulate(base_long[entry_i:end])
        hit = l[entry_i + 1:end] <= stop[:-1]
    else:
        stop = np.minimum.accumulate(base_short[entry_i:end])
        hit = h[entry_i + 1:end] >= stop[:-1]
    w = np.flatnonzero(hit)
    return int(entry_i + 1 + w[0]) if len(w) else -1


@lru_cache(maxsize=1)
def _m1_hl():
    from .data import load_ohlc
    return load_ohlc("M1")[["high", "low"]]


def _touch(h, l, side, px, kind, spread):
    if kind == "stop":
        hit = (h + spread >= px) if side > 0 else (l <= px)
    else:
        hit = (l + spread <= px) if side > 0 else (h >= px)
    w = np.flatnonzero(hit)
    return int(w[0]) if len(w) else -1


def resolve_pending(df, orders, spread_pips=1.0):
    """The engine evaluates pending orders one by one over their whole validity window instead of
    chronologically, which (a) lets an order placed earlier but filled later pre-empt one filled earlier and
    (b) for an OCO pair placed on the same bar always prefers the long side.  Here every stop/limit order is
    re-anchored at the bar *before* its first touch with a 1-bar validity (identical fill price), so the engine
    processes fills in time order; OCO pairs (same decision bar and tag, opposite sides) keep only the side
    touched first, a same-bar tie is resolved with M1 data and dropped when still tied."""
    h, l = df["high"].values, df["low"].values
    n = len(df)
    spread = spread_pips * PIP
    idx = df.index
    fills = []
    for o in orders:
        if o.entry_type == "market":
            fills.append((o, o.i + 1))
            continue
        a, b = o.i + 1, min(n, o.i + o.expiry_bars + 1)
        if a >= n:
            continue
        r = _touch(h[a:b], l[a:b], o.side, o.entry_price, o.entry_type, spread)
        fills.append((o, a + r if r >= 0 else -1))
    # OCO resolution
    groups = {}
    for k, (o, j) in enumerate(fills):
        groups.setdefault((o.i, o.tag, o.entry_type != "market"), []).append(k)
    drop = set()
    for key, ks in groups.items():
        if len(ks) != 2 or not key[2]:
            continue
        (o1, j1), (o2, j2) = fills[ks[0]], fills[ks[1]]
        if o1.side == o2.side:
            continue
        if j1 < 0 or j2 < 0:
            continue
        if j1 < j2:
            drop.add(ks[1])
        elif j2 < j1:
            drop.add(ks[0])
        else:  # same bar: minute resolution
            t0 = idx[j1]
            t1 = idx[j1 + 1] if j1 + 1 < n else t0 + (idx[j1] - idx[j1 - 1])
            seg = _m1_hl().loc[t0:t1 - pd.Timedelta(seconds=1)]
            if seg.empty:
                drop.update(ks)
                continue
            m1 = _touch(seg["high"].values, seg["low"].values, o1.side, o1.entry_price, o1.entry_type, spread)
            m2 = _touch(seg["high"].values, seg["low"].values, o2.side, o2.entry_price, o2.entry_type, spread)
            if m1 < 0 or m2 < 0 or m1 == m2:
                drop.update(ks)
            elif m1 < m2:
                drop.add(ks[1])
            else:
                drop.add(ks[0])
    out = []
    for k, (o, j) in enumerate(fills):
        if k in drop or j < 0:
            continue
        if o.entry_type == "market":
            out.append(o)
        else:
            out.append(Order(i=int(j - 1), side=o.side, entry_type=o.entry_type, entry_price=o.entry_price, sl=o.sl,
                             tp=o.tp, expiry_bars=1, max_hold=o.max_hold, exit_i=o.exit_i, tag=o.tag))
    return out


def _sl_tp(side, ref, sl_d, tp_d):
    if math.isnan(tp_d):
        return (ref - sl_d, math.nan) if side > 0 else (ref + sl_d, math.nan)
    return (ref - sl_d, ref + tp_d) if side > 0 else (ref + sl_d, ref - tp_d)


# ----------------------------------------------------------------------------- T01/T02 Turtle
def turtle(df, entry_n=20, exit_n=10, atr_n=20, sl_atr=2.0, **kw):
    """Stop entry at the highest high / lowest low of the last `entry_n` bars (incl. current bar),
    valid for the next bar only (re-placed every bar); 2N initial stop; exit on close beyond the
    opposite `exit_n` channel."""
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    hh = df["high"].rolling(entry_n).max().values
    ll = df["low"].rolling(entry_n).min().values
    a = F.atr(df, atr_n).values
    ex_lo = F.donchian(df, exit_n)["lower"].values
    ex_hi = F.donchian(df, exit_n)["upper"].values
    nx_long_exit = _next_true(c < ex_lo)
    nx_short_exit = _next_true(c > ex_hi)
    orders = []
    for i in range(entry_n + 1, n - 1):
        if np.isnan(a[i]) or np.isnan(ex_lo[i]):
            continue
        # entry bar would be i+1; exit search from i+2
        xl = nx_long_exit[min(i + 2, n - 1)]
        xs = nx_short_exit[min(i + 2, n - 1)]
        orders.append(Order(i=i, side=1, entry_type="stop", entry_price=hh[i], sl=hh[i] - sl_atr * a[i],
                            expiry_bars=1, exit_i=int(xl) if xl < n else -1, tag="turtle"))
        orders.append(Order(i=i, side=-1, entry_type="stop", entry_price=ll[i], sl=ll[i] + sl_atr * a[i],
                            expiry_bars=1, exit_i=int(xs) if xs < n else -1, tag="turtle"))
    return resolve_pending(df, orders)


# ----------------------------------------------------------------------------- T03 golden cross
def ma_cross_exit(df, fast=50, slow=200, kind="sma", sl_atr=math.nan, atr_n=14, **kw):
    """Cross entry, exit on the opposite cross (optional ATR stop)."""
    fn = F.ema if kind == "ema" else F.sma
    f, s = fn(df["close"], fast).values, fn(df["close"], slow).values
    a = F.atr(df, atr_n).values
    c = df["close"].values
    n = len(df)
    up = (f > s) & (np.roll(f, 1) <= np.roll(s, 1))
    dn = (f < s) & (np.roll(f, 1) >= np.roll(s, 1))
    up[:slow + 1] = False
    dn[:slow + 1] = False
    nx_up, nx_dn = _next_true(up), _next_true(dn)
    orders = []
    for i in np.flatnonzero(up | dn):
        side = 1 if up[i] else -1
        if np.isnan(a[i]):
            continue
        ex = nx_dn[min(i + 1, n - 1)] if side > 0 else nx_up[min(i + 1, n - 1)]
        sl = c[i] - side * sl_atr * a[i] if not math.isnan(sl_atr) else math.nan
        _emit(orders, n, i, side, sl, math.nan, ex, "mx")
    return orders


# ----------------------------------------------------------------------------- T04 EMA pullback
def ema_pullback(df, fast=20, slow=50, atr_n=14, sl_mode="atr", sl_atr=1.5, rr=2.0, lookback=5, **kw):
    """EMA(fast) > EMA(slow); a pullback touched EMA(fast) (low <= ema) within `lookback` bars and the
    bar closes back above EMA(fast) (and above the prior close).  SL below the pullback low (+2 pips) or
    sl_atr x ATR; TP = rr x risk; also exit on the opposite cross."""
    e_f, e_s = F.ema(df["close"], fast).values, F.ema(df["close"], slow).values
    a = F.atr(df, atr_n).values
    c, l, h = df["close"].values, df["low"].values, df["high"].values
    n = len(df)
    trend_up = e_f > e_s
    trend_dn = e_f < e_s
    touch_lo = pd.Series(l <= e_f).rolling(lookback).max().values == 1
    touch_hi = pd.Series(h >= e_f).rolling(lookback).max().values == 1
    prev_c = np.roll(c, 1)
    prev_ef = np.roll(e_f, 1)
    long_sig = trend_up & touch_lo & (c > e_f) & (prev_c <= prev_ef)
    short_sig = trend_dn & touch_hi & (c < e_f) & (prev_c >= prev_ef)
    long_sig[:slow] = False
    short_sig[:slow] = False
    nx_up_cross = _next_true(trend_up & ~np.roll(trend_up, 1))
    nx_dn_cross = _next_true(trend_dn & ~np.roll(trend_dn, 1))
    pl = pd.Series(l).rolling(lookback).min().values
    ph = pd.Series(h).rolling(lookback).max().values
    orders = []
    for i in np.flatnonzero(long_sig | short_sig):
        if np.isnan(a[i]):
            continue
        side = 1 if long_sig[i] else -1
        if sl_mode == "swing":
            sl = pl[i] - 2 * PIP if side > 0 else ph[i] + 2 * PIP
            risk = abs(c[i] - sl)
            if risk < 0.3 * a[i]:
                risk = 0.3 * a[i]
                sl = c[i] - side * risk
        else:
            risk = sl_atr * a[i]
            sl = c[i] - side * risk
        tp = c[i] + side * rr * risk if not math.isnan(rr) else math.nan
        ex = nx_dn_cross[min(i + 1, n - 1)] if side > 0 else nx_up_cross[min(i + 1, n - 1)]
        _emit(orders, n, i, side, sl, tp, ex, "emapb", fallback=False)
    return orders


# ----------------------------------------------------------------------------- T05 MACD + RSI
def macd_rsi(df, fast=12, slow=26, signal=9, rsi_n=14, use_rsi=True, sl_pips=45, tp_pips=90,
             exit_on_cross=False, **kw):
    m = F.macd(df["close"], fast, slow, signal)
    r = F.rsi(df["close"], rsi_n).values
    c = df["close"].values
    n = len(df)
    ml, sg = m["macd"].values, m["signal"].values
    up = (ml > sg) & (np.roll(ml, 1) <= np.roll(sg, 1))
    dn = (ml < sg) & (np.roll(ml, 1) >= np.roll(sg, 1))
    up[:slow + signal] = False
    dn[:slow + signal] = False
    nx_up, nx_dn = _next_true(up), _next_true(dn)
    if use_rsi:
        up &= r > 50
        dn &= r < 50
    orders = []
    for i in np.flatnonzero(up | dn):
        side = 1 if up[i] else -1
        sl, tp = _sl_tp(side, c[i], sl_pips * PIP, tp_pips * PIP if tp_pips else math.nan)
        ex = (nx_dn[min(i + 1, n - 1)] if side > 0 else nx_up[min(i + 1, n - 1)]) if exit_on_cross else -1
        _emit(orders, n, i, side, sl, tp, ex, "macdrsi", fallback=False)
    return orders


# ----------------------------------------------------------------------------- T07 Ichimoku
def ichimoku_trend(df, variant="full", sl_mode="kijun", tenkan=9, kijun=26, senkou_b=52, disp=26, **kw):
    """variant 'full': close above cloud & tenkan>kijun & close > close[i-26] (chikou above price);
    first bar on which all hold.  variant 'chikou': chikou crosses price (close[i] crosses close[i-26]).
    Exit: tenkan/kijun cross against the trade or close back inside the cloud.  SL: kijun or cloud bottom."""
    ic = ichimoku(df, tenkan, kijun, senkou_b, disp)
    c = df["close"].values
    n = len(df)
    t, k, top, bot = ic["tenkan"].values, ic["kijun"].values, ic["cloud_top"].values, ic["cloud_bot"].values
    chik_up = c > np.roll(c, disp)
    chik_dn = c < np.roll(c, disp)
    bull = (c > top) & (t > k) & chik_up
    bear = (c < bot) & (t < k) & chik_dn
    if variant == "full":
        long_sig = bull & ~np.roll(bull, 1)
        short_sig = bear & ~np.roll(bear, 1)
    else:
        long_sig = chik_up & ~np.roll(chik_up, 1)
        short_sig = chik_dn & ~np.roll(chik_dn, 1)
    long_sig[:senkou_b + disp] = False
    short_sig[:senkou_b + disp] = False
    long_exit = (t < k) | (c < top)
    short_exit = (t > k) | (c > bot)
    if variant == "chikou":
        long_exit = chik_dn
        short_exit = chik_up
    nx_le, nx_se = _next_true(long_exit), _next_true(short_exit)
    orders = []
    for i in np.flatnonzero(long_sig | short_sig):
        side = 1 if long_sig[i] else -1
        if np.isnan(top[i]) or np.isnan(k[i]):
            continue
        if sl_mode == "kijun":
            sl = k[i]
        elif sl_mode == "cloud":
            sl = bot[i] if side > 0 else top[i]
        else:
            sl = math.nan
        if not math.isnan(sl) and (sl - c[i]) * side >= -2 * PIP:
            sl = c[i] - side * 20 * PIP  # kijun on the wrong side (chikou variant): minimal stop
        ex = nx_le[min(i + 1, n - 1)] if side > 0 else nx_se[min(i + 1, n - 1)]
        _emit(orders, n, i, side, sl, math.nan, ex, "ichi")
    return orders


# ----------------------------------------------------------------------------- T08 TTM squeeze
def ttm_squeeze(df, bb_n=20, bb_k=2.0, kc_n=20, kc_k=1.5, atr_n=20, min_on=3, direction="mom",
                sl_mode="atr", sl_atr=1.5, tp_atr=2.0, max_hold=40, **kw):
    """Squeeze on = BB(20,2) inside Keltner(20,1.5xATR20).  Enter on the first bar the squeeze releases
    after >= min_on bars, direction from the TTM momentum histogram (linreg of close - avg(midline, SMA))
    or the release candle's close-open."""
    bb = F.bollinger(df["close"], bb_n, bb_k)
    kc = F.keltner(df, kc_n, kc_k, atr_n)
    a = F.atr(df, atr_n).values
    c, o = df["close"].values, df["open"].values
    n = len(df)
    on = ((bb["upper"] < kc["upper"]) & (bb["lower"] > kc["lower"])).values
    on_len = pd.Series(on).groupby((~pd.Series(on)).cumsum()).cumsum().values  # consecutive on-count
    prev_on_len = np.roll(on_len, 1)
    release = (~on) & (prev_on_len >= min_on)
    release[:kc_n + 1] = False
    mid = (df["high"].rolling(kc_n).max() + df["low"].rolling(kc_n).min()) / 2
    base = df["close"] - (mid + df["close"].rolling(kc_n).mean()) / 2
    # linear regression value (end point) over kc_n bars
    x = np.arange(kc_n) - (kc_n - 1) / 2
    mom = base.rolling(kc_n).apply(lambda y: (y.mean() + (x * (y - y.mean())).sum() / (x ** 2).sum() * x[-1]), raw=True).values
    orders = []
    for i in np.flatnonzero(release):
        if np.isnan(a[i]) or np.isnan(mom[i]):
            continue
        if direction == "mom":
            side = 1 if mom[i] > 0 else -1
        else:
            side = 1 if c[i] > o[i] else -1
        if sl_mode == "kc":
            sl = kc["lower"].iat[i] if side > 0 else kc["upper"].iat[i]
            if (c[i] - sl) * side < 0.3 * a[i]:
                sl = c[i] - side * 0.3 * a[i]
        else:
            sl = c[i] - side * sl_atr * a[i]
        tp = c[i] + side * tp_atr * a[i] if not math.isnan(tp_atr) else math.nan
        _emit(orders, n, i, side, sl, tp, -1, "sqz", fallback=False, max_hold=max_hold)
    return orders


# ----------------------------------------------------------------------------- T09 inside bar
def inside_bar_breakout(df, buffer_pips=2.0, sl_mode="inside", rr=2.0, hold_bars=5, expiry_bars=1,
                        tp_mode="rr", **kw):
    """Inside bar at i (high<high[i-1], low>low[i-1]): buy stop at mother high + buffer, sell stop at mother
    low - buffer, valid `expiry_bars`; SL opposite side of the inside bar ('inside') or mother bar ('mother');
    TP rr x risk or 1 x mother range; time exit after hold_bars from the decision bar."""
    h, l = df["high"].values, df["low"].values
    n = len(df)
    ib = (h < np.roll(h, 1)) & (l > np.roll(l, 1))
    ib[0] = False
    orders = []
    for i in np.flatnonzero(ib):
        mh, ml = h[i - 1], l[i - 1]
        for side, px in ((1, mh + buffer_pips * PIP), (-1, ml - buffer_pips * PIP)):
            if sl_mode == "inside":
                sl = l[i] - 2 * PIP if side > 0 else h[i] + 2 * PIP
            else:
                sl = ml - 2 * PIP if side > 0 else mh + 2 * PIP
            risk = abs(px - sl)
            if risk < 3 * PIP:
                continue
            tp = px + side * (rr * risk if tp_mode == "rr" else (mh - ml))
            orders.append(Order(i=int(i), side=side, entry_type="stop", entry_price=px, sl=sl, tp=tp,
                                expiry_bars=expiry_bars, exit_i=int(i + hold_bars) if i + hold_bars < n else -1, tag="ib"))
    return resolve_pending(df, orders)


# ----------------------------------------------------------------------------- T10 NR7 / ID-NR4
def nr_breakout(df, pattern="nr7", buffer_pips=2.0, exit="day_close", adr_n=10, hold_bars=3, **kw):
    """NR7: today's range is the narrowest of the last 7; ID-NR4: inside day that is the narrowest of 4.
    Buy/sell stop at today's high/low +/- buffer valid next bar; SL opposite side of the NR bar;
    exit at the breakout bar's close ('day_close') or TP = 1 x ADR(adr_n) with a hold of hold_bars."""
    h, l = df["high"].values, df["low"].values
    rng = h - l
    n = len(df)
    if pattern == "nr7":
        sig = rng <= pd.Series(rng).rolling(7).min().values
    else:
        ib = (h < np.roll(h, 1)) & (l > np.roll(l, 1))
        sig = ib & (rng <= pd.Series(rng).rolling(4).min().values)
    sig[:8] = False
    adr = pd.Series(rng).rolling(adr_n).mean().values
    orders = []
    for i in np.flatnonzero(sig):
        for side, px in ((1, h[i] + buffer_pips * PIP), (-1, l[i] - buffer_pips * PIP)):
            sl = l[i] - 2 * PIP if side > 0 else h[i] + 2 * PIP
            if exit == "day_close":
                tp, ex = math.nan, i + 1
            else:
                tp, ex = px + side * adr[i], i + hold_bars
            orders.append(Order(i=int(i), side=side, entry_type="stop", entry_price=px, sl=sl, tp=tp,
                                expiry_bars=1, exit_i=int(ex) if ex < n else -1, tag=pattern))
    return resolve_pending(df, orders)


# ----------------------------------------------------------------------------- T11 Supertrend (flip exit)
def supertrend_flip(df, n=10, k=3.0, **kw):
    st = F.supertrend(df, n, k)
    d = st["dir"].values
    line = st["st"].values
    c = df["close"].values
    N = len(df)
    flip_up = (d == 1) & (np.roll(d, 1) == -1)
    flip_dn = (d == -1) & (np.roll(d, 1) == 1)
    flip_up[:n + 1] = False
    flip_dn[:n + 1] = False
    nx_up, nx_dn = _next_true(flip_up), _next_true(flip_dn)
    orders = []
    for i in np.flatnonzero(flip_up | flip_dn):
        side = 1 if flip_up[i] else -1
        ex = nx_dn[min(i + 1, N - 1)] if side > 0 else nx_up[min(i + 1, N - 1)]
        sl = line[i]
        if (c[i] - sl) * side <= 0:
            continue
        _emit(orders, N, i, side, sl, math.nan, ex, "stf")
    return orders


# ----------------------------------------------------------------------------- T12 Parabolic SAR
def psar_flip(df, af0=0.02, step=0.02, af_max=0.2, **kw):
    ps = psar(df, af0, step, af_max)
    d, s = ps["dir"].values, ps["sar"].values
    c = df["close"].values
    N = len(df)
    flip_up = (d == 1) & (np.roll(d, 1) == -1)
    flip_dn = (d == -1) & (np.roll(d, 1) == 1)
    flip_up[:3] = False
    flip_dn[:3] = False
    nx_up, nx_dn = _next_true(flip_up), _next_true(flip_dn)
    orders = []
    for i in np.flatnonzero(flip_up | flip_dn):
        side = 1 if flip_up[i] else -1
        ex = nx_dn[min(i + 1, N - 1)] if side > 0 else nx_up[min(i + 1, N - 1)]
        sl = s[i]
        if (c[i] - sl) * side <= 0:
            continue
        _emit(orders, N, i, side, sl, math.nan, ex, "psar")
    return orders


# ----------------------------------------------------------------------------- T13 Heikin-Ashi + EMA
def heikin_ashi_trend(df, filt="ema100", ema_n=100, confirm=2, sl_mode="atr", sl_atr=1.5, atr_n=14, exit="ha", **kw):
    """`confirm` consecutive bullish HA candles with no lower wick (ha_low == ha_open) while close > EMA(ema_n)
    ('ema100') or EMA20 > EMA50 ('ema2050'); exit on the first opposite-colour HA candle with a wick
    (or EMA cross); SL = sl_atr x ATR or below the lowest low of the confirming candles."""
    ha = heikin_ashi(df)
    ho, hh, hl, hc = ha["ha_open"].values, ha["ha_high"].values, ha["ha_low"].values, ha["ha_close"].values
    c, l, h = df["close"].values, df["low"].values, df["high"].values
    n = len(df)
    a = F.atr(df, atr_n).values
    bull_nw = (hc > ho) & (hl >= ho - 1e-9)
    bear_nw = (hc < ho) & (hh <= ho + 1e-9)
    bull_run = pd.Series(bull_nw).rolling(confirm).min().values == 1
    bear_run = pd.Series(bear_nw).rolling(confirm).min().values == 1
    if filt == "ema100":
        e = F.ema(df["close"], ema_n).values
        up_ok, dn_ok = c > e, c < e
        up_cross = (c > e) & (np.roll(c, 1) <= np.roll(e, 1))
        dn_cross = (c < e) & (np.roll(c, 1) >= np.roll(e, 1))
    else:
        e1, e2 = F.ema(df["close"], 20).values, F.ema(df["close"], 50).values
        up_ok, dn_ok = e1 > e2, e1 < e2
        up_cross = up_ok & ~np.roll(up_ok, 1)
        dn_cross = dn_ok & ~np.roll(dn_ok, 1)
    long_sig = bull_run & ~np.roll(bull_run, 1) & up_ok
    short_sig = bear_run & ~np.roll(bear_run, 1) & dn_ok
    long_sig[:ema_n] = False
    short_sig[:ema_n] = False
    bear_wick = (hc < ho) & (hh > ho + 1e-9)
    bull_wick = (hc > ho) & (hl < ho - 1e-9)
    if exit == "ha":
        nx_le, nx_se = _next_true(bear_wick | dn_cross), _next_true(bull_wick | up_cross)
    else:
        nx_le, nx_se = _next_true(dn_cross), _next_true(up_cross)
    ll = pd.Series(l).rolling(confirm).min().values
    hh_ = pd.Series(h).rolling(confirm).max().values
    orders = []
    for i in np.flatnonzero(long_sig | short_sig):
        if np.isnan(a[i]):
            continue
        side = 1 if long_sig[i] else -1
        if sl_mode == "swing":
            sl = ll[i] - 2 * PIP if side > 0 else hh_[i] + 2 * PIP
            if (c[i] - sl) * side < 0.3 * a[i]:
                sl = c[i] - side * 0.3 * a[i]
        else:
            sl = c[i] - side * sl_atr * a[i]
        ex = nx_le[min(i + 1, n - 1)] if side > 0 else nx_se[min(i + 1, n - 1)]
        _emit(orders, n, i, side, sl, math.nan, ex, "ha")
    return orders


# ----------------------------------------------------------------------------- T14 chandelier / ATR trail exit engine
def trail_exit_entry(df, host="donchian", entry_n=20, fast=20, slow=50, trail="chandelier", ch_n=22, ch_k=3.0,
                     atr_n=14, k=2.0, sl_atr=2.0, **kw):
    """Exit module: entries from a trend host ('donchian' = close beyond entry_n channel; 'emacross' =
    EMA fast/slow cross), exit when the ratcheted trailing stop is touched (filled at that bar's close) or
    the initial sl_atr stop is hit.  trail 'chandelier': HH(ch_n) - ch_k x ATR(ch_n); 'atr': close - k x ATR(atr_n)."""
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    a = F.atr(df, atr_n).values
    if trail == "chandelier":
        a2 = F.atr(df, ch_n).values
        base_long = df["high"].rolling(ch_n).max().values - ch_k * a2
        base_short = df["low"].rolling(ch_n).min().values + ch_k * a2
    else:
        base_long = c - k * a
        base_short = c + k * a
    if host == "donchian":
        ch = F.donchian(df, entry_n)
        up = c > ch["upper"].values
        dn = c < ch["lower"].values
        up, dn = up & ~np.roll(up, 1), dn & ~np.roll(dn, 1)
    else:
        f, s = F.ema(df["close"], fast).values, F.ema(df["close"], slow).values
        up = (f > s) & (np.roll(f, 1) <= np.roll(s, 1))
        dn = (f < s) & (np.roll(f, 1) >= np.roll(s, 1))
    up[:max(entry_n, slow, ch_n) + 1] = False
    dn[:max(entry_n, slow, ch_n) + 1] = False
    orders = []
    for i in np.flatnonzero(up | dn):
        if np.isnan(a[i]) or np.isnan(base_long[i]):
            continue
        side = 1 if up[i] else -1
        ex = _trail_exit(h, l, c, base_long, base_short, i + 1, side)
        sl = c[i] - side * sl_atr * a[i]
        orders.append(Order(i=int(i), side=side, sl=sl, exit_i=ex, tag="trail"))
    return orders


# ----------------------------------------------------------------------------- T15 Larry Williams volatility breakout
def lw_vol_breakout(df, k=0.25, range_lookback=1, sl_mult=2.0, tp_mult=2.0, day_start=0, exit_hour=21, **kw):
    """At the first bar of the day (day starts at `day_start` UTC): buy stop = open + k x prev range,
    sell stop = open - k x prev range (prev range = avg high-low of the last `range_lookback` days);
    SL = sl_mult x band, TP = tp_mult x band from entry; time exit at `exit_hour` UTC; one trade/day.
    On D1 bars the day open is proxied by the previous close (the decision is made at that close)."""
    n = len(df)
    bpd = _bpd(df)
    orders = []
    if bpd == 1:
        h, l, c = df["high"].values, df["low"].values, df["close"].values
        rng = pd.Series(h - l).rolling(range_lookback).mean().values
        for i in range(range_lookback, n - 1):
            band = k * rng[i]
            if np.isnan(band) or band < 3 * PIP:
                continue
            for side in (1, -1):
                px = c[i] + side * band
                sl, tp = px - side * sl_mult * band, px + side * tp_mult * band
                orders.append(Order(i=i, side=side, entry_type="stop", entry_price=px, sl=sl, tp=tp,
                                    expiry_bars=1, exit_i=i + 1, tag="lw"))
        return resolve_pending(df, orders)
    d = F.daily_ohlc(df, day_start)
    d["rng"] = (d["high"] - d["low"]).rolling(range_lookback).mean()
    key = (df.index - pd.Timedelta(hours=day_start)).floor("D") + pd.Timedelta(hours=day_start)
    prev_rng = d["rng"].shift(1).reindex(key).values
    day_open = d["open"].reindex(key).values
    hrs = (df.index.hour + df.index.minute / 60).values
    step_h = 24 / bpd
    is_first = key.values != np.roll(key.values, 1)
    is_first[0] = False
    exit_offset = ((exit_hour - day_start) % 24)
    firsts = np.flatnonzero(is_first)
    ex_all = _exit_at_hour(df, firsts, exit_hour) if len(firsts) else firsts
    for i, ex in zip(firsts, ex_all):
        band = k * prev_rng[i]
        if np.isnan(band) or band < 3 * PIP:
            continue
        bars_valid = int(exit_offset / step_h) - 1
        if bars_valid < 2 or ex <= i + 1 or ex >= n:
            continue
        bars_valid = min(bars_valid, int(ex - i))
        for side in (1, -1):
            px = day_open[i] + side * band
            sl, tp = px - side * sl_mult * band, px + side * tp_mult * band
            orders.append(Order(i=int(i), side=side, entry_type="stop", entry_price=px, sl=sl, tp=tp,
                                expiry_bars=bars_valid, exit_i=int(ex), tag="lw"))
    return resolve_pending(df, orders)


# ----------------------------------------------------------------------------- T16 previous-day high/low breakout
def pdh_pdl_breakout(df, buffer_pips=2.0, sl_mode="pips", sl_pips=25, rr=1.5, start_hour=7, end_hour=17,
                     exit_hour=21, day_start=22, **kw):
    """At the first bar >= start_hour (London local) place buy stop at PDH+buffer / sell stop at PDL-buffer
    valid until end_hour London; SL fixed pips or the prior day's midpoint; TP rr x risk (nan = EOD);
    hard exit at exit_hour UTC.  Previous day = NY-close day (day_start UTC)."""
    lv = F.prev_day_levels(df, day_start)
    pdh, pdl = lv["pd_high"].values, lv["pd_low"].values
    n = len(df)
    bpd = _bpd(df)
    step_h = 24 / bpd
    loc = df.index.tz_convert("Europe/London")
    lhr = (loc.hour + loc.minute / 60).values
    uhr = (df.index.hour + df.index.minute / 60).values
    day = df.index.floor("D").values
    c = df["close"].values
    orders = []
    last = None
    for i in range(n):
        if day[i] != last:
            last = day[i]
            placed = False
        if placed or lhr[i] < start_hour or lhr[i] >= end_hour:
            continue
        placed = True
        if np.isnan(pdh[i]):
            continue
        bars_valid = max(1, int((end_hour - lhr[i]) / step_h))
        ex = int(_exit_at_hour(df, [i], exit_hour)[0])
        if ex <= i or ex >= n:
            continue
        mid = (pdh[i] + pdl[i]) / 2
        for side, px in ((1, pdh[i] + buffer_pips * PIP), (-1, pdl[i] - buffer_pips * PIP)):
            if (px - c[i]) * side <= 0:
                continue  # already beyond the level: no breakout to wait for
            sl = px - side * sl_pips * PIP if sl_mode == "pips" else mid
            risk = abs(px - sl)
            if risk < 5 * PIP:
                continue
            tp = px + side * rr * risk if not math.isnan(rr) else math.nan
            orders.append(Order(i=i, side=side, entry_type="stop", entry_price=px, sl=sl, tp=tp,
                                expiry_bars=bars_valid, exit_i=int(ex), tag="pdhl"))
    return resolve_pending(df, orders)


# ----------------------------------------------------------------------------- T17 time-series momentum
@lru_cache(maxsize=1)
def _carry_daily() -> pd.Series:
    """Daily (EUR o/n - US fed funds) in % p.a., forward-filled; EONIA/ESTR vs FEDFUNDS (monthly)."""
    try:
        ea = pd.read_csv(MACRO / "ea_overnight_rates.csv", parse_dates=["date"]).set_index("date")
        eur = ea["eonia"].fillna(ea["estr"]) if "estr" in ea else ea["eonia"]
        ff = pd.read_csv(MACRO / "fred_FEDFUNDS.csv", parse_dates=["date"]).set_index("date")["value"]
        idx = pd.date_range("1999-01-01", "2030-01-01", freq="D")
        return (eur.reindex(idx).ffill() - ff.reindex(idx).ffill()).ffill()
    except Exception:
        return pd.Series(dtype=float)


def tsmom(df, lookback_m=12, variant="single", use_carry=True, **kw):
    """Daily bars.  At each month-end close: signal = sign of the trailing lookback_m-month excess return
    (spot return + average carry differential x years).  'single' uses one lookback; 'combo' uses the sign
    of the sum of the 1-, 3- and 12-month signs (flat when 0).  Position held until the signal changes at a
    later month-end; no stop (judged in pips)."""
    c = df["close"].values
    n = len(df)
    months = df.index.year * 12 + df.index.month
    me = np.zeros(n, bool)
    me[:-1] = months[1:] != months[:-1]
    carry = _carry_daily() if use_carry else pd.Series(dtype=float)
    cd = carry.reindex(df.index.tz_localize(None).floor("D")).values if len(carry) else np.zeros(n)
    cd = np.nan_to_num(cd)
    cum_c = np.cumsum(cd) / 365.0 / 100.0  # cumulative carry in return units (daily accrual of % p.a.)

    def excess(i, m):
        j = i - 21 * m
        if j < 0:
            return np.nan
        return c[i] / c[j] - 1 + (cum_c[i] - cum_c[j])

    sig = np.zeros(n)
    for i in np.flatnonzero(me):
        if variant == "single":
            e = excess(i, lookback_m)
            sig[i] = 0 if np.isnan(e) else np.sign(e)
        else:
            s = [np.sign(excess(i, m)) for m in (1, 3, 12)]
            if any(np.isnan(x) for x in s):
                sig[i] = 0
            else:
                sig[i] = np.sign(sum(s))
    orders = []
    me_idx = np.flatnonzero(me)
    pos = 0
    for a_, i in enumerate(me_idx):
        s = sig[i]
        if s == pos:
            continue
        pos = s
        if s == 0:
            continue
        # exit at the next month-end where the signal differs
        ex = -1
        for j in me_idx[a_ + 1:]:
            if sig[j] != s:
                ex = int(j)
                break
        _emit(orders, n, int(i), int(s), math.nan, math.nan, ex, "tsmom")
    return orders


# ----------------------------------------------------------------------------- T18 fractal breakout H1
def fractal_breakout(df, k=2, sl_mode="pips", sl_pips=30, tp_pips=50, start_hour=7, end_hour=19, exit_hour=21, **kw):
    """Williams fractal (k bars each side, 5-bar for k=2).  When a new up-fractal is confirmed during
    start_hour-end_hour UTC place a buy stop 1 pip above it (sell stop below a new down-fractal), valid until
    end_hour; SL fixed pips or the opposite most recent fractal; TP fixed pips; hard exit at exit_hour."""
    sh, sl_ = fractals(df, k)
    h, l = df["high"].values, df["low"].values
    n = len(df)
    bpd = _bpd(df)
    step_h = 24 / bpd
    hrs = (df.index.hour + df.index.minute / 60).values
    last_up = pd.Series(np.where(sh, h, np.nan)).shift(k).ffill().values   # known at i (confirmed at i)
    last_dn = pd.Series(np.where(sl_, l, np.nan)).shift(k).ffill().values
    new_up = np.roll(sh, k)
    new_dn = np.roll(sl_, k)
    new_up[:k] = False
    new_dn[:k] = False
    c = df["close"].values
    orders = []
    cand = np.flatnonzero((new_up | new_dn) & (hrs >= start_hour) & (hrs < end_hour))
    ex_all = _exit_at_hour(df, cand, exit_hour) if len(cand) else cand
    for i, ex in zip(cand, ex_all):
        bars_valid = max(1, int((end_hour - hrs[i]) / step_h))
        ex = int(ex)
        if ex >= n or ex <= i:
            continue
        for side, flag, px in ((1, new_up[i], last_up[i] + PIP), (-1, new_dn[i], last_dn[i] - PIP)):
            if not flag or np.isnan(px) or (px - c[i]) * side <= 0:
                continue
            if sl_mode == "pips":
                sl = px - side * sl_pips * PIP
            else:
                opp = last_dn[i] if side > 0 else last_up[i]
                if np.isnan(opp) or (px - opp) * side < 5 * PIP:
                    continue
                sl = opp - side * PIP
            tp = px + side * tp_pips * PIP if tp_pips else math.nan
            orders.append(Order(i=int(i), side=side, entry_type="stop", entry_price=px, sl=sl, tp=tp,
                                expiry_bars=bars_valid, exit_i=int(ex), tag="frac"))
    return resolve_pending(df, orders)


# ----------------------------------------------------------------------------- V02/V03/V04/T06 filters
@lru_cache(maxsize=4)
def _garch_regime(refit_each_year=True) -> pd.Series:
    """Daily GARCH(1,1) one-step-ahead sigma forecast for day t (made at the close of t-1) using parameters
    fitted on data strictly before the calendar year of t (annual expanding refits, first fit on
    2000-2002).  Regime = tercile of the forecast within the trailing 500 forecasts: 0 low, 1 mid, 2 high.
    Only computed up to 2022-12-31 (holdout untouched).  Cached to experiments/results/garch_regime.csv."""
    out_path = MACRO.parents[1] / "experiments" / "results" / "garch_regime.csv"
    if out_path.exists():
        s = pd.read_csv(out_path, parse_dates=["date"]).set_index("date")
        return s["regime"]
    from arch import arch_model
    from .data import load_ohlc
    d1 = load_ohlc("D1")
    d1 = d1[d1.index < pd.Timestamp("2023-01-01", tz="UTC")]
    r = 100 * np.log(d1["close"]).diff().dropna()
    r.index = r.index.tz_localize(None)
    sig = pd.Series(np.nan, index=r.index)
    years = sorted(set(r.index.year))
    params = None
    for y in years:
        if y < 2003:
            continue
        hist = r[r.index.year < y]
        if len(hist) < 300:
            continue
        am = arch_model(hist, vol="GARCH", p=1, q=1, mean="Zero", dist="normal")
        res = am.fit(disp="off")
        om, al, be = res.params["omega"], res.params["alpha[1]"], res.params["beta[1]"]
        # filter conditional variance over the whole series with these params, use forecasts in year y
        v = np.empty(len(r))
        v[0] = hist.var()
        rv = r.values
        for t in range(1, len(r)):
            v[t] = om + al * rv[t - 1] ** 2 + be * v[t - 1]
        mask = r.index.year == y
        sig[mask] = np.sqrt(v[mask])  # v[t] uses returns up to t-1: forecast for day t
    rank = sig.rolling(500, min_periods=250).rank(pct=True)
    regime = pd.Series(np.where(rank < 1 / 3, 0, np.where(rank > 2 / 3, 2, 1)), index=r.index).where(rank.notna())
    out = pd.DataFrame({"sigma_fc": sig, "pct": rank, "regime": regime})
    out.index.name = "date"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.to_csv(out_path)
    return out["regime"]


@lru_cache(maxsize=1)
def _vix_daily() -> pd.Series:
    v = pd.read_csv(MACRO / "fred_VIXCLS.csv", parse_dates=["date"]).set_index("date")["value"]
    idx = pd.date_range("1990-01-01", "2030-01-01", freq="D")
    return v.reindex(idx).ffill()


def filtered(df, host="turtle", hp=None, filt="adx", adx_n=14, adx_thr=25, di_agree=True,
             short_atr=5, long_atr=20, ratio=0.8, mode="contraction", pct_n=50, pct_q=0.2,
             regime_keep=(1,), vix_lo=15.0, vix_hi=30.0, vix_mode="low", **kw):
    """Keep only the host's orders whose decision bar passes the filter:
    'adx'   (T06): ADX(adx_n) > adx_thr and (optionally) +DI/-DI agree with the order's side.
    'vol'   (V02): mode 'contraction': ATR(5)/ATR(20) < ratio OR day range in bottom pct_q of pct_n days;
                   mode 'expansion': ATR(5)/ATR(20) > ratio.
    'garch' (V03): previous day's GARCH(1,1) sigma-forecast regime in regime_keep (0 low,1 mid,2 high).
    'vix'   (V04): previous day's VIX close: 'low' => VIX < vix_lo, 'high' => VIX > vix_hi, 'mid' between,
                   'notstress' => VIX < vix_hi."""
    hp = dict(hp or {})
    orders = REGISTRY[host](df, **hp)
    n = len(df)
    if filt == "adx":
        ad = F.adx(df, adx_n)
        ok_long = ((ad["adx"] > adx_thr) & ((ad["pdi"] > ad["mdi"]) if di_agree else True)).values
        ok_short = ((ad["adx"] > adx_thr) & ((ad["mdi"] > ad["pdi"]) if di_agree else True)).values
    elif filt == "vol":
        bpd = _bpd(df)
        if bpd == 1:
            a5, a20 = F.atr(df, short_atr), F.atr(df, long_atr)
            rng = df["high"] - df["low"]
            low_rng = rng <= rng.rolling(pct_n).quantile(pct_q)
            rr = (a5 / a20).values
        else:
            d = F.daily_ohlc(df, 22)
            a5, a20 = F.atr(d, short_atr), F.atr(d, long_atr)
            rng = d["high"] - d["low"]
            key = (df.index - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
            # use the *previous* completed day for intraday hosts
            rr = (a5 / a20).shift(1).reindex(key).values
            low_rng = (rng <= rng.rolling(pct_n).quantile(pct_q)).shift(1).reindex(key).fillna(False).values
        if mode == "contraction":
            ok = (rr < ratio) | np.asarray(low_rng, bool)
        else:
            ok = rr > ratio
        ok_long = ok_short = ok
    elif filt == "garch":
        reg = _garch_regime()
        days = df.index.tz_localize(None).floor("D")
        bpd = _bpd(df)
        # intraday: regime for the current calendar day (forecast made at the previous close) is fine;
        # daily bars: the decision at close t concerns day t+1 -> use regime of day t+1 is NOT known... use day t's forecast
        rv = reg.reindex(days).values
        ok = np.isin(rv, list(regime_keep))
        ok_long = ok_short = ok
    elif filt == "vix":
        vx = _vix_daily()
        days = df.index.tz_localize(None).floor("D") - pd.Timedelta(days=1)
        v = vx.reindex(days).values
        if vix_mode == "low":
            ok = v < vix_lo
        elif vix_mode == "high":
            ok = v > vix_hi
        elif vix_mode == "mid":
            ok = (v >= vix_lo) & (v <= vix_hi)
        else:
            ok = v < vix_hi
        ok_long = ok_short = ok
    else:
        raise ValueError(filt)
    out = []
    for o in orders:
        ok = ok_long[o.i] if o.side > 0 else ok_short[o.i]
        if ok and not (isinstance(ok, float) and np.isnan(ok)):
            out.append(o)
    return out


# ----------------------------------------------------------------------------- P01 pin bar
def pin_bar(df, tail_ratio=0.667, sl_buffer_pips=5.0, rr=2.0, trend="ema", ema_n=50, max_hold=20, entry="close", **kw):
    """Bullish pin: lower tail >= tail_ratio x range and body (and close) in the top third; bearish mirrored.
    Trend filter: pin in the direction of the EMA(ema_n) trend ('ema'), or none.  Entry at the close
    ('close') or a limit at the 50 % level of the pin valid 3 bars ('half').  SL beyond the tail + buffer,
    TP rr x risk, max_hold bars."""
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    rng = h - l
    body_top, body_bot = np.maximum(o, c), np.minimum(o, c)
    lower_tail = body_bot - l
    upper_tail = h - body_top
    with np.errstate(invalid="ignore", divide="ignore"):
        bull = (lower_tail >= tail_ratio * rng) & (body_bot >= l + 2 / 3 * rng) & (rng > 5 * PIP)
        bear = (upper_tail >= tail_ratio * rng) & (body_top <= h - 2 / 3 * rng) & (rng > 5 * PIP)
    if trend == "ema":
        e = F.ema(df["close"], ema_n).values
        bull &= c > e
        bear &= c < e
    elif trend == "counter":
        e = F.ema(df["close"], ema_n).values
        bull &= c < e
        bear &= c > e
    bull[:ema_n] = False
    bear[:ema_n] = False
    orders = []
    for i in np.flatnonzero(bull | bear):
        side = 1 if bull[i] else -1
        sl = l[i] - sl_buffer_pips * PIP if side > 0 else h[i] + sl_buffer_pips * PIP
        if entry == "close":
            ref = c[i]
            risk = abs(ref - sl)
            tp = ref + side * rr * risk
            orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, max_hold=max_hold, tag="pin"))
        else:
            ref = (h[i] + l[i]) / 2
            risk = abs(ref - sl)
            tp = ref + side * rr * risk
            orders.append(Order(i=int(i), side=side, entry_type="limit", entry_price=ref, sl=sl, tp=tp,
                                expiry_bars=3, max_hold=max_hold, tag="pin50"))
    return resolve_pending(df, orders)


# ----------------------------------------------------------------------------- P02 engulfing
def engulfing(df, strict=False, rr=2.0, max_hold=20, min_body_atr=0.0, atr_n=14, direction="reversal", **kw):
    """Bearish engulfing: bearish candle whose body (strict: full range) covers the prior candle's body
    (range) and the prior candle is bullish.  Enter at the close counter to the prior move; SL beyond the
    engulfing candle's extreme; TP rr x risk; max_hold bars.  direction 'momentum' fades the pattern."""
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    a = F.atr(df, atr_n).values
    po, pc, ph, pl = np.roll(o, 1), np.roll(c, 1), np.roll(h, 1), np.roll(l, 1)
    body = np.abs(c - o)
    if strict:
        bear = (c < o) & (pc > po) & (h >= ph) & (l <= pl) & (c < pl) & (o > ph)
        bull = (c > o) & (pc < po) & (h >= ph) & (l <= pl) & (c > ph) & (o < pl)
    else:
        bear = (c < o) & (pc > po) & (o >= pc) & (c <= po) & (body > np.abs(pc - po))
        bull = (c > o) & (pc < po) & (o <= pc) & (c >= po) & (body > np.abs(pc - po))
    bear &= body >= min_body_atr * a
    bull &= body >= min_body_atr * a
    bear[:atr_n + 1] = False
    bull[:atr_n + 1] = False
    orders = []
    for i in np.flatnonzero(bear | bull):
        side = -1 if bear[i] else 1
        if direction == "momentum":
            side = -side
            sl = h[i] + 2 * PIP if side < 0 else l[i] - 2 * PIP
        else:
            sl = h[i] + 2 * PIP if side < 0 else l[i] - 2 * PIP
        risk = abs(c[i] - sl)
        if risk < 3 * PIP:
            continue
        tp = c[i] + side * rr * risk
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, max_hold=max_hold, tag="eng"))
    return orders


# ----------------------------------------------------------------------------- P03 outside bar
def outside_bar(df, rr=1.5, max_hold=20, trend="none", ema_n=200, **kw):
    """Outside bar (high > prior high and low < prior low): enter at the next open in the direction of the
    bar's close (close > open => long); SL at the opposite side of the outside bar; TP rr x risk;
    optional EMA(ema_n) trend filter."""
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    ob = (h > np.roll(h, 1)) & (l < np.roll(l, 1)) & (c != o)
    ob[0] = False
    e = F.ema(df["close"], ema_n).values
    orders = []
    for i in np.flatnonzero(ob):
        side = 1 if c[i] > o[i] else -1
        if trend == "ema" and ((side > 0 and c[i] < e[i]) or (side < 0 and c[i] > e[i])):
            continue
        sl = l[i] - 2 * PIP if side > 0 else h[i] + 2 * PIP
        risk = abs(c[i] - sl)
        if risk < 3 * PIP:
            continue
        tp = c[i] + side * rr * risk
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, max_hold=max_hold, tag="ob"))
    return orders


# ----------------------------------------------------------------------------- P04 double top / bottom
def double_top_bottom(df, k=5, tol_atr=0.5, min_bars=5, max_bars=60, max_wait=30, tp_mode="height", rr=2.0, atr_n=14, **kw):
    """Two swing highs (fractal k) within tol_atr x ATR of each other, min_bars..max_bars apart, with a swing
    low (neckline) between; after the second peak is confirmed, short on the first close below the neckline
    within max_wait bars.  SL above the higher peak + 2 pips; TP = pattern height below the neckline
    ('height') or rr x risk.  Bottoms mirrored."""
    piv, _ = zigzag(df, k)
    c = df["close"].values
    n = len(df)
    a = F.atr(df, atr_n).values
    orders = []
    for p in range(2, len(piv)):
        i1, p1, t1 = piv[p - 2]
        i2, p2, t2 = piv[p - 1]
        i3, p3, t3 = piv[p]
        if t1 != t3 or t2 == t1:
            continue
        gap = i3 - i1
        if gap < min_bars or gap > max_bars:
            continue
        conf = i3 + k
        if conf >= n or np.isnan(a[conf]):
            continue
        if abs(p3 - p1) > tol_atr * a[conf]:
            continue
        side = -1 if t1 == 1 else 1  # double top -> short
        neck = p2
        height = abs(max(p1, p3) - neck) if side < 0 else abs(neck - min(p1, p3))
        if height < 5 * PIP:
            continue
        # neckline break within max_wait bars after confirmation
        seg = c[conf:min(n, conf + max_wait)]
        brk = np.flatnonzero(seg < neck) if side < 0 else np.flatnonzero(seg > neck)
        if not len(brk):
            continue
        j = conf + brk[0]
        # the pattern must still be intact: no new extreme beyond the peaks before the break
        if side < 0 and df["high"].values[i3 + 1:j + 1].max() > max(p1, p3):
            continue
        if side > 0 and df["low"].values[i3 + 1:j + 1].min() < min(p1, p3):
            continue
        sl = max(p1, p3) + 2 * PIP if side < 0 else min(p1, p3) - 2 * PIP
        risk = abs(c[j] - sl)
        if risk < 3 * PIP:
            continue
        tp = neck - height if side < 0 else neck + height
        if tp_mode == "rr":
            tp = c[j] + side * rr * risk
        if (tp - c[j]) * side <= 0:
            continue
        orders.append(Order(i=int(j), side=side, sl=sl, tp=tp, max_hold=max_bars, tag="dtb"))
    return orders


# ----------------------------------------------------------------------------- P05 head and shoulders
def head_shoulders(df, k=5, sym_tol=0.3, max_wait=30, max_span=80, tp_mode="height", rr=2.0, **kw):
    """Five alternating pivots SH1 SL1 SH2 SL2 SH3 with SH2 the highest, shoulders within sym_tol x
    (head - neckline) of each other; neckline through SL1/SL2 (extrapolated); short on the first close below the
    neckline within max_wait bars after the right shoulder is confirmed.  SL above the right shoulder;
    TP = head - neckline projected from the break.  Inverse mirrored."""
    piv, _ = zigzag(df, k)
    c = df["close"].values
    h, l = df["high"].values, df["low"].values
    n = len(df)
    orders = []
    for p in range(4, len(piv)):
        pts = piv[p - 4:p + 1]
        types = [t for _, _, t in pts]
        if types not in ([1, -1, 1, -1, 1], [-1, 1, -1, 1, -1]):
            continue
        (iA, A, _), (iB, B, _), (iC, C_, _), (iD, D, _), (iE, E, _) = pts
        if iE - iA > max_span:
            continue
        side = -1 if types[0] == 1 else 1
        if side < 0:
            if not (C_ > A and C_ > E):
                continue
        else:
            if not (C_ < A and C_ < E):
                continue
        slope = (D - B) / (iD - iB)
        neck_at_head = B + slope * (iC - iB)
        height = abs(C_ - neck_at_head)
        if height < 5 * PIP or abs(A - E) > sym_tol * height:
            continue
        conf = iE + k
        if conf >= n:
            continue
        found = -1
        for j in range(conf, min(n, conf + max_wait)):
            neck = B + slope * (j - iB)
            if (side < 0 and c[j] < neck) or (side > 0 and c[j] > neck):
                found = j
                break
            if (side < 0 and h[j] > E) or (side > 0 and l[j] < E):
                break  # right shoulder violated
        if found < 0:
            continue
        j = found
        sl = E + 2 * PIP if side < 0 else E - 2 * PIP
        risk = abs(c[j] - sl)
        if risk < 3 * PIP:
            continue
        tp = c[j] + side * (height if tp_mode == "height" else rr * risk)
        orders.append(Order(i=int(j), side=side, sl=sl, tp=tp, max_hold=max_span, tag="hs"))
    return orders


# ----------------------------------------------------------------------------- P06 flags
def flag_breakout(df, pole_atr=1.5, pole_bars=8, min_flag=5, max_flag=20, max_retrace=0.5, atr_n=14, tp_mode="pole", rr=2.0, **kw):
    """Pole: close-to-close move >= pole_atr x ATR over pole_bars bars ending at the pole top (a local high).
    Flag: the following min_flag..max_flag bars stay above pole_top - max_retrace x pole height and make
    no new high; enter long on the first close above the flag's highest high of the last 5 bars (channel
    break) that is also above the flag midpoint.  SL at the flag low; TP = pole height from the entry close
    ('pole') or rr x risk.  Bear flags mirrored."""
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    a = F.atr(df, atr_n).values
    move = c - np.roll(c, pole_bars)
    move[:pole_bars] = 0
    orders = []
    i = pole_bars + atr_n
    while i < n - min_flag - 1:
        if np.isnan(a[i]):
            i += 1
            continue
        if abs(move[i]) >= pole_atr * a[i]:
            side = 1 if move[i] > 0 else -1
            pole_h = abs(move[i])
            top = h[i] if side > 0 else l[i]
            base = c[i - pole_bars]
            # walk the flag
            j = i + 1
            fired = False
            while j < n and j - i <= max_flag:
                if side > 0:
                    if h[j] > top:
                        break  # new high without a 5-bar flag: continue the scan from here
                    if l[j] < top - max_retrace * pole_h:
                        break
                    if j - i >= min_flag:
                        hh5 = h[j - 5:j].max()
                        flag_lo = l[i + 1:j].min()
                        if c[j] > hh5 and c[j] > (top + flag_lo) / 2:
                            sl = flag_lo - 2 * PIP
                            risk = c[j] - sl
                            tp = c[j] + (pole_h if tp_mode == "pole" else rr * risk)
                            if risk > 3 * PIP:
                                orders.append(Order(i=int(j), side=1, sl=sl, tp=tp, max_hold=max_flag * 2, tag="flag"))
                            fired = True
                            break
                else:
                    if l[j] < top:
                        break
                    if h[j] > top + max_retrace * pole_h:
                        break
                    if j - i >= min_flag:
                        ll5 = l[j - 5:j].min()
                        flag_hi = h[i + 1:j].max()
                        if c[j] < ll5 and c[j] < (top + flag_hi) / 2:
                            sl = flag_hi + 2 * PIP
                            risk = sl - c[j]
                            tp = c[j] - (pole_h if tp_mode == "pole" else rr * risk)
                            if risk > 3 * PIP:
                                orders.append(Order(i=int(j), side=-1, sl=sl, tp=tp, max_hold=max_flag * 2, tag="flag"))
                            fired = True
                            break
                j += 1
            i = j if fired else i + 1
        else:
            i += 1
    return orders


# ----------------------------------------------------------------------------- P07 harmonic patterns
HARMONIC = {
    # name: (B retrace of XA range, D retrace/extension of XA)
    "gartley": ((0.618, 0.618), 0.786),
    "bat": ((0.382, 0.5), 0.886),
    "butterfly": ((0.786, 0.786), 1.27),
    "crab": ((0.382, 0.618), 1.618),
}


def harmonic(df, pattern="gartley", k=5, tol=0.05, tp_level=0.618, expiry_bars=60, **kw):
    """XABCD from alternating fractal pivots.  Bullish: X low, A high, B low, C high.  B must retrace XA by
    the pattern's ratio (+/- tol), C between 0.382 and 0.886 of AB; once C is confirmed a limit buy is placed at
    D = A - d x XA (d = pattern's D ratio), valid expiry_bars; SL beyond X (or 1.618 XA for butterfly/crab,
    beyond D by 0.1 XA); TP at tp_level retracement of AD.  Bearish mirrored."""
    (b_lo, b_hi), d_ratio = HARMONIC[pattern]
    piv, _ = zigzag(df, k)
    n = len(df)
    c = df["close"].values
    orders = []
    for p in range(3, len(piv)):
        (iX, X, tX), (iA, A, _), (iB, B, _), (iC, C_, _) = piv[p - 3:p + 1]
        side = 1 if tX == -1 else -1
        xa = abs(A - X)
        if xa < 10 * PIP:
            continue
        b_ret = abs(A - B) / xa
        if not (b_lo - tol <= b_ret <= b_hi + tol):
            continue
        ab = abs(A - B)
        c_ret = abs(C_ - B) / ab if ab > 0 else 0
        if not (0.382 - tol <= c_ret <= 0.886 + tol):
            continue
        conf = iC + k
        if conf >= n - 1:
            continue
        D = A - side * d_ratio * xa
        if (c[conf] - D) * side <= 0:
            continue  # already through D
        if d_ratio <= 1:
            sl = X - side * 0.1 * xa
        else:
            sl = D - side * 0.3 * xa
        tp = D + side * tp_level * abs(A - D)
        orders.append(Order(i=int(conf), side=side, entry_type="limit", entry_price=D, sl=sl, tp=tp,
                            expiry_bars=expiry_bars, max_hold=expiry_bars * 2, tag=pattern))
    return resolve_pending(df, orders)


# ----------------------------------------------------------------------------- P08 Fibonacci pullback
def fib_pullback(df, k=5, level=0.5, stop_level=0.786, target=1.0, trend="ema", ema_n=50, tol=0.1, max_wait=40, **kw):
    """Impulse = last alternating pivot pair (swing low X -> swing high A, confirmed at A+k) with price above
    EMA(ema_n) (trend filter).  Rejection entry: a later bar whose low touches the `level` retracement zone
    (within tol x XA) and closes back above the level -> market long; SL below the stop_level retracement;
    TP at target (1.0 = A, 1.272/1.618 extensions).  Shorts mirrored."""
    piv, _ = zigzag(df, k)
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    e = F.ema(df["close"], ema_n).values
    orders = []
    for p in range(1, len(piv)):
        (iX, X, tX), (iA, A, tA) = piv[p - 1], piv[p]
        side = 1 if tA == 1 else -1
        xa = abs(A - X)
        if xa < 10 * PIP:
            continue
        conf = iA + k
        if conf >= n:
            continue
        if trend == "ema" and ((side > 0 and c[conf] < e[conf]) or (side < 0 and c[conf] > e[conf])):
            continue
        lvl = A - side * level * xa
        stop = A - side * stop_level * xa
        for j in range(conf, min(n, conf + max_wait)):
            if (side > 0 and (h[j] > A or l[j] < stop)) or (side < 0 and (l[j] < A or h[j] > stop)):
                break  # swing invalidated or already resumed
            touched = (l[j] <= lvl + tol * xa) if side > 0 else (h[j] >= lvl - tol * xa)
            rejected = (c[j] > lvl) if side > 0 else (c[j] < lvl)
            if touched and rejected:
                tp = X + side * target * xa if target >= 1 else A
                sl = stop - side * 2 * PIP
                risk = abs(c[j] - sl)
                if risk >= 3 * PIP and (tp - c[j]) * side > 0:
                    orders.append(Order(i=int(j), side=side, sl=sl, tp=tp, max_hold=max_wait * 2, tag="fib"))
                break
    return orders


# ----------------------------------------------------------------------------- P09 supply / demand zones
def supply_demand(df, max_base=3, base_atr=0.6, departure_atr=2.0, depart_bars=3, rr=3.0, atr_n=14, expiry_bars=200, max_hold=100, **kw):
    """Base = 1..max_base consecutive candles each with range <= base_atr x ATR; departure = the next
    depart_bars bars travel >= departure_atr x ATR away from the base (close beyond base +/- that distance).
    Zone = base high/low.  Demand (rally away): limit buy at the zone's proximal edge (base high) on the first
    return, valid expiry_bars; SL below the distal edge - 2 pips; TP rr x risk."""
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    a = F.atr(df, atr_n).values
    small = (h - l) <= base_atr * a
    orders = []
    i = atr_n + 1
    while i < n - depart_bars - 1:
        if not small[i] or np.isnan(a[i]):
            i += 1
            continue
        # base = run of small candles starting at i (<= max_base)
        j = i
        while j + 1 < n and small[j + 1] and j + 1 - i < max_base:
            j += 1
        if j + 1 - i > max_base:
            i = j + 1
            continue
        zh, zl = h[i:j + 1].max(), l[i:j + 1].min()
        end = min(n, j + 1 + depart_bars)
        seg_c = c[j + 1:end]
        if not len(seg_c):
            break
        dep = j + 1 + np.flatnonzero((seg_c - zh) >= departure_atr * a[j])
        dep_dn = j + 1 + np.flatnonzero((zl - seg_c) >= departure_atr * a[j])
        if len(dep) and (not len(dep_dn) or dep[0] < dep_dn[0]):
            k_ = int(dep[0])
            sl = zl - 2 * PIP
            risk = zh - sl
            orders.append(Order(i=k_, side=1, entry_type="limit", entry_price=zh, sl=sl, tp=zh + rr * risk,
                                expiry_bars=expiry_bars, max_hold=max_hold, tag="demand"))
            i = k_ + 1
        elif len(dep_dn):
            k_ = int(dep_dn[0])
            sl = zh + 2 * PIP
            risk = sl - zl
            orders.append(Order(i=k_, side=-1, entry_type="limit", entry_price=zl, sl=sl, tp=zl - rr * risk,
                                expiry_bars=expiry_bars, max_hold=max_hold, tag="supply"))
            i = k_ + 1
        else:
            i = j + 1
    return resolve_pending(df, orders)


# ----------------------------------------------------------------------------- P10 order blocks
def order_block(df, displacement_atr=1.5, zone="open_low", rr=2.0, atr_n=14, struct_n=10, expiry_bars=50, max_hold=60, **kw):
    """Bullish OB = last bearish candle before an up-move: within the next 3 bars the close rises >=
    displacement_atr x ATR above the OB candle's close AND breaks the prior struct_n-bar high (structure break).
    Entry: limit at the OB top (its open for 'open_low', its high for 'full') on the first retrace within
    expiry_bars; SL below the OB low - 2 pips; TP rr x risk.  Bearish mirrored."""
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    a = F.atr(df, atr_n).values
    hh = pd.Series(h).rolling(struct_n).max().shift(1).values
    ll = pd.Series(l).rolling(struct_n).min().shift(1).values
    orders = []
    i = struct_n + atr_n
    while i < n - 4:
        if np.isnan(a[i]):
            i += 1
            continue
        if c[i] < o[i]:  # bearish candle: candidate bullish OB
            for d in (1, 2, 3):
                j = i + d
                if c[j] - c[i] >= displacement_atr * a[i] and c[j] > hh[j]:
                    top = o[i] if zone == "open_low" else h[i]
                    sl = l[i] - 2 * PIP
                    risk = top - sl
                    if risk > 3 * PIP and c[j] > top:
                        orders.append(Order(i=int(j), side=1, entry_type="limit", entry_price=top, sl=sl, tp=top + rr * risk,
                                            expiry_bars=expiry_bars, max_hold=max_hold, tag="ob_bull"))
                        i = j
                    break
        elif c[i] > o[i]:
            for d in (1, 2, 3):
                j = i + d
                if c[i] - c[j] >= displacement_atr * a[i] and c[j] < ll[j]:
                    bot = o[i] if zone == "open_low" else l[i]
                    sl = h[i] + 2 * PIP
                    risk = sl - bot
                    if risk > 3 * PIP and c[j] < bot:
                        orders.append(Order(i=int(j), side=-1, entry_type="limit", entry_price=bot, sl=sl, tp=bot - rr * risk,
                                            expiry_bars=expiry_bars, max_hold=max_hold, tag="ob_bear"))
                        i = j
                    break
        i += 1
    return resolve_pending(df, orders)


# ----------------------------------------------------------------------------- P11 fair value gaps
def fvg_retrace(df, entry_level="top", min_gap_atr=0.2, rr=2.0, atr_n=14, expiry_bars=30, max_hold=40,
                start_hour=-1, end_hour=25, **kw):
    """Bullish FVG at bar i: high[i-2] < low[i] (gap = low[i] - high[i-2] >= min_gap_atr x ATR).  Limit buy at
    the gap top (low[i]) or its 50 % level, valid expiry_bars; SL below the gap (high[i-2]) - 2 pips; TP rr x risk.
    Optional UTC hour window for the signal bar.  Bearish mirrored."""
    h, l = df["high"].values, df["low"].values
    n = len(df)
    a = F.atr(df, atr_n).values
    hrs = df.index.hour.values
    gap_up = l - np.roll(h, 2)
    gap_dn = np.roll(l, 2) - h
    gap_up[:2] = gap_dn[:2] = 0
    bull = gap_up >= min_gap_atr * a
    bear = gap_dn >= min_gap_atr * a
    orders = []
    for i in np.flatnonzero(bull | bear):
        if not (start_hour <= hrs[i] < end_hour):
            continue
        if bull[i]:
            top, bot = l[i], h[i - 2]
            px = top if entry_level == "top" else (top + bot) / 2
            sl = bot - 2 * PIP
            risk = px - sl
            orders.append(Order(i=int(i), side=1, entry_type="limit", entry_price=px, sl=sl, tp=px + rr * risk,
                                expiry_bars=expiry_bars, max_hold=max_hold, tag="fvg"))
        else:
            bot, top = h[i], l[i - 2]
            px = bot if entry_level == "top" else (top + bot) / 2
            sl = top + 2 * PIP
            risk = sl - px
            orders.append(Order(i=int(i), side=-1, entry_type="limit", entry_price=px, sl=sl, tp=px - rr * risk,
                                expiry_bars=expiry_bars, max_hold=max_hold, tag="fvg"))
    return resolve_pending(df, orders)


# ----------------------------------------------------------------------------- P12 Wyckoff spring / upthrust
def wyckoff_spring(df, range_bars=20, max_range_atr=3.0, reclaim_bars=3, tp_mode="range", rr=2.0, atr_n=14, max_hold=40, **kw):
    """Range = high/low of the previous range_bars bars with height <= max_range_atr x ATR.  Spring: a bar
    breaks below the range low and price closes back inside within reclaim_bars bars; buy that close; SL below
    the spring low - 2 pips; TP the range top ('range') or rr x risk.  Upthrust mirrored.  (No volume.)"""
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    n = len(df)
    a = F.atr(df, atr_n).values
    rh = pd.Series(h).rolling(range_bars).max().shift(1).values
    rl = pd.Series(l).rolling(range_bars).min().shift(1).values
    tight = (rh - rl) <= max_range_atr * a
    brk_dn = (l < rl) & tight
    brk_up = (h > rh) & tight
    orders = []
    last_fire = -10**9
    for i in np.flatnonzero(brk_dn | brk_up):
        if i - last_fire < reclaim_bars:
            continue
        side = 1 if brk_dn[i] else -1
        lo_r, hi_r = rl[i], rh[i]
        ext = l[i] if side > 0 else h[i]
        for j in range(i, min(n, i + reclaim_bars)):
            ext = min(ext, l[j]) if side > 0 else max(ext, h[j])
            if (side > 0 and c[j] > lo_r) or (side < 0 and c[j] < hi_r):
                sl = ext - side * 2 * PIP
                risk = abs(c[j] - sl)
                tp = (hi_r if side > 0 else lo_r) if tp_mode == "range" else c[j] + side * rr * risk
                if risk >= 3 * PIP and (tp - c[j]) * side > 3 * PIP:
                    orders.append(Order(i=int(j), side=side, sl=sl, tp=tp, max_hold=max_hold, tag="spring" if side > 0 else "upthrust"))
                    last_fire = j
                break
    return orders


REGISTRY.update({
    "turtle": turtle, "ma_cross_exit": ma_cross_exit, "ema_pullback": ema_pullback, "macd_rsi": macd_rsi,
    "ichimoku_trend": ichimoku_trend, "ttm_squeeze": ttm_squeeze, "inside_bar_breakout": inside_bar_breakout,
    "nr_breakout": nr_breakout, "supertrend_flip": supertrend_flip, "psar_flip": psar_flip,
    "heikin_ashi_trend": heikin_ashi_trend, "trail_exit_entry": trail_exit_entry, "lw_vol_breakout": lw_vol_breakout,
    "pdh_pdl_breakout": pdh_pdl_breakout, "tsmom": tsmom, "fractal_breakout": fractal_breakout, "filtered": filtered,
    "pin_bar": pin_bar, "engulfing": engulfing, "outside_bar": outside_bar, "double_top_bottom": double_top_bottom,
    "head_shoulders": head_shoulders, "flag_breakout": flag_breakout, "harmonic": harmonic, "fib_pullback": fib_pullback,
    "supply_demand": supply_demand, "order_block": order_block, "fvg_retrace": fvg_retrace, "wyckoff_spring": wyckoff_spring,
})
