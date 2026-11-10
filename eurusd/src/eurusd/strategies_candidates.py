"""Candidate components: the effects that kept their sign in TRAIN and VALIDATE
across the hypothesis tests and catalogue backtests, each expressed as concrete
orders with a stop-loss, a take-profit and/or a time exit so the live engine can
emit them. All decisions use information available at the decision bar.

Local-time rules use tz_convert so DST is handled.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pandas as pd

from .backtest import Order
from .strategies import REGISTRY, _bars_per_day
from . import features as F

PIP = 0.0001
MACRO = Path(__file__).resolve().parents[2] / "data" / "macro"


def _local(df, tz):
    loc = df.index.tz_convert(tz)
    return loc.hour * 60 + loc.minute, loc.normalize()


def _adr(df, n=14):
    """Average daily range (pips) of the previous n NY-close days, aligned to intraday bars."""
    d = F.daily_ohlc(df, 22)
    d = d[d["n"] >= 10]
    adr = ((d["high"] - d["low"]) / PIP).rolling(n).mean().shift(1)
    key = (df.index - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
    return adr.reindex(key).to_numpy()


# 1. Short EUR/USD during London morning (Breedon-Ranaldo local-hours effect)
def london_short(df, entry_min=7 * 60, exit_min=13 * 60, stop_adr=1.0, tz="Europe/London", **kw):
    """Short at `entry_min` London local (minutes), flat at `exit_min`; disaster stop = stop_adr x ADR14."""
    mins, day = _local(df, tz)
    adr = _adr(df)
    bpd = _bars_per_day(df)
    step = int(24 * 60 / bpd)
    orders = []
    n = len(df)
    for i in range(n - 1):
        # decide at bar i so that the fill is the open of bar i+1 at entry_min
        if mins[i] + step == entry_min and day[i + 1] == day[i] and df.index[i + 1].dayofweek < 5:
            exit_i = i + 1 + (exit_min - entry_min) // step - 1
            if exit_i >= n or np.isnan(adr[i]):
                continue
            c = df["close"].iat[i]
            orders.append(Order(i=i, side=-1, sl=c + stop_adr * adr[i] * PIP, tp=math.nan, exit_i=exit_i, tag="london_short"))
    return orders


# 2. Asian-range breakout (stop orders, SL = opposite side of range, TP = tp_rr x range)
def asian_breakout(df, start=1, end=8, entry_until=14, tp_rr=3.0, exit_hour=20, buffer_pips=2.0, min_range=10, max_range=80, **kw):
    from .strategies import asian_range_breakout
    orders = asian_range_breakout(df, start=start, end=end, entry_until=entry_until, sl_mode="range", sl_val=1.0,
                                  tp_rr=tp_rr, exit_hour=exit_hour, buffer_pips=buffer_pips,
                                  min_range_pips=min_range, max_range_pips=max_range)
    for o in orders:
        o.tag = "asian_breakout"
    return orders


# 3. Month-end London fix: follow the 15:00-15:45 move into the 16:00 fix (last London business day)
def month_end_fix(df, start_min=15 * 60, entry_min=15 * 60 + 45, fix_min=16 * 60, stop_pips=15, min_move_pips=3, **kw):
    mins, day = _local(df, "Europe/London")
    bpd = _bars_per_day(df)
    step = int(24 * 60 / bpd)
    s_day = pd.Series(day, index=df.index)
    month = s_day.dt.to_period("M")
    last_bd = s_day.groupby(month).transform("max")
    is_me = (s_day == last_bd).to_numpy()
    close = df["close"].to_numpy()
    orders = []
    n = len(df)
    start_px = {}
    for i in range(n - 1):
        if not is_me[i]:
            continue
        if mins[i] == start_min:
            start_px[day[i]] = df["open"].iat[i]
        if mins[i] + step == entry_min and day[i] in start_px:
            move = (close[i] - start_px[day[i]]) / PIP
            if abs(move) < min_move_pips:
                continue
            side = 1 if move > 0 else -1
            exit_i = i + 1 + (fix_min - entry_min) // step - 1
            if exit_i >= n:
                continue
            orders.append(Order(i=i, side=side, sl=close[i] - side * stop_pips * PIP, tp=math.nan, exit_i=exit_i, tag="month_end_fix"))
    return orders


# 4. Large weekend gap fade (daily bars, NY-close days): gap > gap_atr x ATR20, hold `hold` days, stop 1 ATR
def weekend_gap_fade(df_daily, gap_atr=0.2, hold=1, stop_atr=1.0, **kw):
    d = df_daily
    atr = F.atr(d, 20).shift(1).to_numpy()
    o = d["open"].to_numpy(); c = d["close"].to_numpy()
    dow = d.index.dayofweek
    orders = []
    for i in range(1, len(d) - 1):
        # the first bar of the week is the Sunday 21/22 UTC bar (dayofweek 6) on NY-close days
        if dow[i] != 6 or np.isnan(atr[i]):
            continue
        gap = o[i] - c[i - 1]
        if abs(gap) <= gap_atr * atr[i]:
            continue
        side = -1 if gap > 0 else 1
        # decision is "at the open" of bar i: emulate with a market order decided at bar i-1 (fills at bar i open)
        orders.append(Order(i=i - 1, side=side, sl=o[i] - side * stop_atr * atr[i], tp=math.nan, exit_i=i + hold - 1, tag="weekend_gap_fade"))
    return orders


# 5. FOMC-day: long EUR/USD from the T-1 NY close to the T NY close (scheduled meetings)
def fomc_day_long(df_daily, stop_atr=1.5, **kw):
    f = pd.read_csv(MACRO / "fomc_decisions.csv", parse_dates=["statement_utc"])
    f = f[(f.scheduled == True) & (f.status.isin(["held", "tentative"]))]
    stmt = pd.to_datetime(f.statement_utc, utc=True)
    # NY-close day containing the statement = the daily bar whose start <= stmt < next start
    d = df_daily
    atr = F.atr(d, 20).shift(1).to_numpy()
    pos = d.index.searchsorted(stmt, side="right") - 1
    orders = []
    for p in pos:
        if 1 <= p < len(d) and not np.isnan(atr[p]):
            c = d["close"].iat[p - 1]
            orders.append(Order(i=p - 1, side=1, sl=c - stop_atr * atr[p], tp=math.nan, exit_i=p, tag="fomc_day_long"))
    return orders


# 6. COT non-commercial positioning trend: weekly position in the direction of the 52-week z-score
def cot_trend(df_daily, z_win=52, hold_days=5, stop_atr=2.0, min_abs_z=0.0, **kw):
    leg = pd.read_csv(MACRO / "cot_eurofx_legacy.csv", parse_dates=["report_date"]).set_index("report_date")
    net = (leg["noncomm_long"] - leg["noncomm_short"]) / leg["open_interest"]
    z = (net - net.rolling(z_win).mean()) / net.rolling(z_win).std()
    z.index = (z.index + pd.Timedelta(days=6)).tz_localize("UTC")  # Tuesday positions published Friday -> usable from Monday
    d = df_daily
    atr = F.atr(d, 20).shift(1).to_numpy()
    zz = z.reindex(d.index, method="ffill").to_numpy()
    orders = []
    i = 1
    n = len(d)
    while i < n - 1:
        if np.isnan(zz[i]) or np.isnan(atr[i]) or abs(zz[i]) < min_abs_z:
            i += 1
            continue
        side = 1 if zz[i] > 0 else -1
        c = d["close"].iat[i]
        orders.append(Order(i=i, side=side, sl=c - side * stop_atr * atr[i], tp=math.nan, exit_i=min(n - 1, i + hold_days), tag="cot_trend"))
        i += hold_days
    return orders


REGISTRY.update({
    "london_short": london_short,
    "asian_breakout": asian_breakout,
    "month_end_fix": month_end_fix,
    "weekend_gap_fade": weekend_gap_fade,
    "fomc_day_long": fomc_day_long,
    "cot_trend": cot_trend,
})
