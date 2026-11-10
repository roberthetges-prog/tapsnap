"""Strategy library. Every strategy is a function

    strategy(df, **params) -> list[Order]

where df is a UTC-indexed OHLC frame of the strategy's timeframe (bid prices)
and the orders are decided at the close of bar i using information <= i.
Stops/targets are expressed via helper `sl_tp` in pips or ATR multiples.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

from .backtest import Order
from . import features as F

PIP = 0.0001


def _sl_tp(side: int, ref: float, sl_dist: float, tp_dist: float):
    if side > 0:
        return ref - sl_dist, ref + tp_dist
    return ref + sl_dist, ref - tp_dist


def _dist(mode: str, value: float, atr_val: float) -> float:
    """distance in price units: mode 'pips' or 'atr'."""
    if mode == "pips":
        return value * PIP
    return value * atr_val


def _bars_per_day(df: pd.DataFrame) -> int:
    step = (df.index[1:] - df.index[:-1]).min()
    return int(pd.Timedelta("1D") / step)


# ------------------------------------------------------------------ session breakouts
def asian_range_breakout(df, start=0, end=7, entry_until=12, sl_mode="range", sl_val=1.0, tp_rr=2.0,
                         buffer_pips=2.0, exit_hour=21, min_range_pips=10, max_range_pips=80, **kw):
    """London/Asian-range breakout: range built over [start,end) UTC, buy-stop above / sell-stop
    below with buffer, orders valid until `entry_until` UTC, flat at `exit_hour` UTC.
    sl_mode 'range' => SL at opposite side of range * sl_val ; 'pips' => fixed pips."""
    win = F.session_range(df, start, end)
    hrs = df.index.hour + df.index.minute / 60
    orders = []
    day = df.index.floor("D")
    last_day = None
    bpd = _bars_per_day(df)
    step_h = 24 / bpd
    for i in range(len(df)):
        if day[i] != last_day:
            last_day = day[i]
            placed = False
        if placed or hrs[i] < end or hrs[i] >= entry_until:
            continue
        hi, lo = win["win_high"].iat[i], win["win_low"].iat[i]
        if np.isnan(hi) or np.isnan(lo):
            continue
        rng = hi - lo
        if not (min_range_pips * PIP <= rng <= max_range_pips * PIP):
            placed = True
            continue
        placed = True
        bars_valid = int((entry_until - hrs[i]) / step_h)
        exit_i = i + int((exit_hour - hrs[i]) / step_h)
        for side, px in ((1, hi + buffer_pips * PIP), (-1, lo - buffer_pips * PIP)):
            sl_d = rng * sl_val if sl_mode == "range" else sl_val * PIP
            sl, tp = _sl_tp(side, px, sl_d, sl_d * tp_rr)
            orders.append(Order(i=i, side=side, entry_type="stop", entry_price=px, sl=sl, tp=tp,
                                expiry_bars=max(1, bars_valid), exit_i=exit_i, tag="arb"))
    return orders


def opening_range_breakout(df, open_hour=13, open_minute=30, range_minutes=30, entry_until_hour=17,
                           sl_mode="range", sl_val=1.0, tp_rr=2.0, exit_hour=20, buffer_pips=1.0, **kw):
    """ORB around a session open (default NY 13:30 UTC, winter-time approximation)."""
    start = open_hour + open_minute / 60
    end = start + range_minutes / 60
    return asian_range_breakout(df, start=start, end=end, entry_until=entry_until_hour, sl_mode=sl_mode,
                                sl_val=sl_val, tp_rr=tp_rr, buffer_pips=buffer_pips, exit_hour=exit_hour,
                                min_range_pips=3, max_range_pips=200)


# ------------------------------------------------------------------ trend following
def ma_cross(df, fast=20, slow=50, kind="ema", sl_atr=2.0, tp_atr=4.0, atr_n=14, max_hold=10**6, **kw):
    f = (F.ema if kind == "ema" else F.sma)(df["close"], fast)
    s = (F.ema if kind == "ema" else F.sma)(df["close"], slow)
    a = F.atr(df, atr_n)
    cross_up = (f > s) & (f.shift(1) <= s.shift(1))
    cross_dn = (f < s) & (f.shift(1) >= s.shift(1))
    orders = []
    c = df["close"].values
    for i in np.flatnonzero(cross_up.values | cross_dn.values):
        if np.isnan(a.iat[i]):
            continue
        side = 1 if cross_up.iat[i] else -1
        sl, tp = _sl_tp(side, c[i], sl_atr * a.iat[i], tp_atr * a.iat[i])
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, max_hold=max_hold, tag="ma"))
    return orders


def donchian_breakout(df, n=20, sl_atr=2.0, tp_atr=math.nan, atr_n=14, max_hold=10**6, exit_n=10, **kw):
    """Turtle-style: enter on close beyond n-bar channel; exit by ATR stop or opposite exit_n channel."""
    ch = F.donchian(df, n)
    a = F.atr(df, atr_n)
    c = df["close"]
    up = c > ch["upper"]
    dn = c < ch["lower"]
    orders = []
    for i in np.flatnonzero(up.values | dn.values):
        if np.isnan(a.iat[i]):
            continue
        side = 1 if up.iat[i] else -1
        sl = c.iat[i] - side * sl_atr * a.iat[i]
        tp = c.iat[i] + side * tp_atr * a.iat[i] if not math.isnan(tp_atr) else math.nan
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, max_hold=max_hold, tag="don"))
    return orders


def macd_trend(df, fast=12, slow=26, signal=9, sl_atr=2.0, tp_atr=3.0, atr_n=14, trend_ma=200, **kw):
    m = F.macd(df["close"], fast, slow, signal)
    a = F.atr(df, atr_n)
    t = F.ema(df["close"], trend_ma)
    c = df["close"]
    up = (m["macd"] > m["signal"]) & (m["macd"].shift(1) <= m["signal"].shift(1)) & (c > t)
    dn = (m["macd"] < m["signal"]) & (m["macd"].shift(1) >= m["signal"].shift(1)) & (c < t)
    orders = []
    for i in np.flatnonzero(up.values | dn.values):
        if np.isnan(a.iat[i]):
            continue
        side = 1 if up.iat[i] else -1
        sl, tp = _sl_tp(side, c.iat[i], sl_atr * a.iat[i], tp_atr * a.iat[i])
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, tag="macd"))
    return orders


def supertrend_follow(df, n=10, k=3.0, sl_atr=2.0, tp_atr=math.nan, **kw):
    st = F.supertrend(df, n, k)
    a = F.atr(df, n)
    c = df["close"]
    flip_up = (st["dir"] == 1) & (st["dir"].shift(1) == -1)
    flip_dn = (st["dir"] == -1) & (st["dir"].shift(1) == 1)
    orders = []
    for i in np.flatnonzero(flip_up.values | flip_dn.values):
        side = 1 if flip_up.iat[i] else -1
        sl = c.iat[i] - side * sl_atr * a.iat[i]
        tp = c.iat[i] + side * tp_atr * a.iat[i] if not math.isnan(tp_atr) else math.nan
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, tag="st"))
    return orders


# ------------------------------------------------------------------ mean reversion
def rsi_reversion(df, n=2, lo=10, hi=90, sl_atr=2.0, tp_atr=1.0, atr_n=14, max_hold=5, trend_ma=200, use_trend=True, **kw):
    r = F.rsi(df["close"], n)
    a = F.atr(df, atr_n)
    t = F.sma(df["close"], trend_ma)
    c = df["close"]
    longs = (r < lo) & ((c > t) if use_trend else True)
    shorts = (r > hi) & ((c < t) if use_trend else True)
    orders = []
    for i in np.flatnonzero(longs.values | shorts.values):
        if np.isnan(a.iat[i]):
            continue
        side = 1 if longs.iat[i] else -1
        sl, tp = _sl_tp(side, c.iat[i], sl_atr * a.iat[i], tp_atr * a.iat[i])
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, max_hold=max_hold, tag="rsi"))
    return orders


def bollinger_fade(df, n=20, k=2.0, sl_atr=1.5, tp="mid", atr_n=14, max_hold=20, **kw):
    bb = F.bollinger(df["close"], n, k)
    a = F.atr(df, atr_n)
    c = df["close"]
    longs = (c < bb["lower"]) & (c.shift(1) >= bb["lower"].shift(1))
    shorts = (c > bb["upper"]) & (c.shift(1) <= bb["upper"].shift(1))
    orders = []
    for i in np.flatnonzero(longs.values | shorts.values):
        if np.isnan(a.iat[i]) or np.isnan(bb["mid"].iat[i]):
            continue
        side = 1 if longs.iat[i] else -1
        sl = c.iat[i] - side * sl_atr * a.iat[i]
        tpx = bb["mid"].iat[i] if tp == "mid" else c.iat[i] + side * float(tp) * a.iat[i]
        if (tpx - c.iat[i]) * side <= 0:
            continue
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tpx, max_hold=max_hold, tag="bb"))
    return orders


def pivot_bounce(df, level="s1", sl_pips=15, tp_level="pivot", day_start=0, start_hour=7, end_hour=16, exit_hour=20, **kw):
    """Limit order at previous-day pivot support/resistance during the session, target the pivot."""
    lv = F.prev_day_levels(df, day_start)
    hrs = df.index.hour + df.index.minute / 60
    day = df.index.floor("D")
    bpd = _bars_per_day(df)
    step_h = 24 / bpd
    orders = []
    last = None
    for i in range(len(df)):
        if day[i] != last:
            last = day[i]
            done = False
        if done or hrs[i] < start_hour or hrs[i] >= end_hour:
            continue
        done = True
        s, r, p = lv["s1"].iat[i], lv["r1"].iat[i], lv["pivot"].iat[i]
        if level == "s2r2":
            s, r = lv["s2"].iat[i], lv["r2"].iat[i]
        if np.isnan(s) or np.isnan(p):
            continue
        bars_valid = int((end_hour - hrs[i]) / step_h)
        exit_i = i + int((exit_hour - hrs[i]) / step_h)
        c = df["close"].iat[i]
        if s < c:
            orders.append(Order(i=i, side=1, entry_type="limit", entry_price=s, sl=s - sl_pips * PIP, tp=p,
                                expiry_bars=bars_valid, exit_i=exit_i, tag="piv"))
        if r > c:
            orders.append(Order(i=i, side=-1, entry_type="limit", entry_price=r, sl=r + sl_pips * PIP, tp=p,
                                expiry_bars=bars_valid, exit_i=exit_i, tag="piv"))
    return orders


# ------------------------------------------------------------------ calendar / time-of-day
def time_of_day(df, entry_hour=7, exit_hour=16, side=1, sl_pips=math.nan, tp_pips=math.nan, dows=(0, 1, 2, 3, 4), **kw):
    """Hold a position from entry_hour (UTC, entered at that bar's open) to exit_hour close on given weekdays."""
    hrs = df.index.hour + df.index.minute / 60
    bpd = _bars_per_day(df)
    step_h = 24 / bpd
    dow = df.index.dayofweek
    orders = []
    n = len(df)
    for i in range(n - 1):
        # decide at bar i so that entry is the open of bar i+1 == entry_hour
        if abs(hrs[i] + step_h - entry_hour) < 1e-9 and dow[i + 1] in dows:
            exit_i = i + 1 + int(round((exit_hour - entry_hour) / step_h)) - 1
            if exit_i >= n:
                continue
            c = df["close"].iat[i]
            sl = c - side * sl_pips * PIP if not math.isnan(sl_pips) else math.nan
            tp = c + side * tp_pips * PIP if not math.isnan(tp_pips) else math.nan
            orders.append(Order(i=i, side=side, sl=sl, tp=tp, exit_i=exit_i, tag="tod"))
    return orders


def day_of_week_hold(df_daily, dow=0, side=1, hold_days=1, **kw):
    """Daily bars: enter at the open of weekday `dow` (0=Mon) and exit at the close `hold_days` later."""
    orders = []
    d = df_daily.index.dayofweek
    for i in range(len(df_daily) - 1):
        if d[i + 1] == dow:
            orders.append(Order(i=i, side=side, exit_i=i + hold_days, tag="dow"))
    return orders


REGISTRY = {
    "asian_range_breakout": asian_range_breakout,
    "opening_range_breakout": opening_range_breakout,
    "ma_cross": ma_cross,
    "donchian_breakout": donchian_breakout,
    "macd_trend": macd_trend,
    "supertrend_follow": supertrend_follow,
    "rsi_reversion": rsi_reversion,
    "bollinger_fade": bollinger_fade,
    "pivot_bounce": pivot_bounce,
    "time_of_day": time_of_day,
    "day_of_week_hold": day_of_week_hold,
}
