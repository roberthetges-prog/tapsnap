"""Mean-reversion and systematic catalogue entries (M01-M15, Q01-Q06).

Every function has the signature strategy(df, **params) -> list[Order] and is
registered in eurusd.strategies.REGISTRY at import time.  Orders are decided at
the close of bar i (market fill at i+1 open).  Rule-based exits ("close crosses
SMA5", "RSI reaches 50", "z crosses 0") are implemented by scanning forward for
the first bar on which the condition holds and passing it as Order.exit_i (the
engine then closes the trade at that bar's close) - the condition only uses
information available at that bar's close, so there is no look-ahead in the
exit itself.  Daily strategies expect a D1 frame WITHOUT the Sunday/Saturday
stub bars (see experiments/13_meanrev_systematic.py, `daily_frame`).
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

from .backtest import Order
from . import features as F
from .strategies import REGISTRY, _sl_tp, _bars_per_day

PIP = 0.0001
NAN = math.nan


# ----------------------------------------------------------------- helpers
def _next_true(mask) -> np.ndarray:
    """nt[i] = smallest j >= i with mask[j] True, else len(mask)."""
    m = np.asarray(mask, dtype=bool)
    n = len(m)
    idx = np.where(m, np.arange(n), n)
    return np.minimum.accumulate(idx[::-1])[::-1]


def _day_last_index(df: pd.DataFrame, day_start_utc_hour: int = 0) -> np.ndarray:
    """For each bar, the index of the last bar of its (day_start-shifted) day."""
    key = (df.index - pd.Timedelta(hours=day_start_utc_hour)).floor("D")
    pos = np.arange(len(df))
    last = pd.Series(pos, index=df.index).groupby(key.values).transform("max")
    return last.values


def _day_first_index(df: pd.DataFrame, day_start_utc_hour: int = 0) -> np.ndarray:
    key = (df.index - pd.Timedelta(hours=day_start_utc_hour)).floor("D")
    pos = np.arange(len(df))
    return pd.Series(pos, index=df.index).groupby(key.values).transform("min").values


def _adr_by_bar(df: pd.DataFrame, n: int = 14, day_start_utc_hour: int = 22, min_bars: int = 10) -> np.ndarray:
    """Average daily range of the previous n full days, aligned to intraday bars (no lookahead)."""
    d = F.daily_ohlc(df, day_start_utc_hour)
    d = d[d["n"] >= min_bars]
    adr = (d["high"] - d["low"]).rolling(n).mean().shift(1)
    key = (df.index - pd.Timedelta(hours=day_start_utc_hour)).floor("D") + pd.Timedelta(hours=day_start_utc_hour)
    return adr.reindex(key, method="ffill").values


def _first_exit_bar(day_last: np.ndarray, i: int) -> int:
    return int(day_last[i])


# ================================================================= M01 Connors RSI(2)
def connors_rsi2(df, n=2, thr=5, trend_ma=200, exit_ma=5, exit_on_trend_cross=True, sl_atr=NAN,
                 atr_n=14, max_hold=20, sides="both", **kw):
    """M01. Long when close > SMA(trend_ma) and RSI(n) < thr; exit at the first close > SMA(exit_ma)
    (Backtrex also exits when the close falls back below the 200-day SMA). Shorts mirrored with 100-thr.
    No stop in the original (sl_atr=NaN -> metrics in pips); sl_atr adds an ATR stop for an R-based variant."""
    c = df["close"]
    r = F.rsi(c, n).values
    t = F.sma(c, trend_ma).values
    x = F.sma(c, exit_ma).values
    a = F.atr(df, atr_n).values
    cv = c.values
    long_sig = (r < thr) & (cv > t)
    short_sig = (r > 100 - thr) & (cv < t)
    long_exit = _next_true((cv > x) | ((cv < t) if exit_on_trend_cross else False))
    short_exit = _next_true((cv < x) | ((cv > t) if exit_on_trend_cross else False))
    n_ = len(df)
    orders = []
    for i in np.flatnonzero(long_sig | short_sig):
        i = int(i)
        if i + 1 >= n_ or np.isnan(t[i]) or np.isnan(a[i]):
            continue
        side = 1 if long_sig[i] else -1
        if (sides == "long" and side < 0) or (sides == "short" and side > 0):
            continue
        ex = long_exit[i + 1] if side > 0 else short_exit[i + 1]
        sl = cv[i] - side * sl_atr * a[i] if not math.isnan(sl_atr) else NAN
        orders.append(Order(i=i, side=side, sl=sl, tp=NAN, max_hold=max_hold, exit_i=int(min(ex, n_ - 1)), tag="crsi2"))
    return orders


# ================================================================= M02 RSI(14) 30/70 cross-back
def rsi_cross_back(df, n=14, os_=30, ob=70, exit_rsi=50, sl_atr=1.5, atr_n=14, max_hold=30, tp_mode="rsi", **kw):
    """M02. Long when RSI(n) crosses back above `os_`; short when it crosses back below `ob`.
    Stop 1.5xATR(14); exit when RSI reaches exit_rsi (tp_mode 'rsi') or at the 20-bar Bollinger mid ('bbmid')."""
    c = df["close"]
    r = F.rsi(c, n).values
    a = F.atr(df, atr_n).values
    cv = c.values
    mid = F.sma(c, 20).values
    r1 = np.roll(r, 1); r1[0] = np.nan
    longs = (r > os_) & (r1 <= os_)
    shorts = (r < ob) & (r1 >= ob)
    lx = _next_true(r >= exit_rsi)
    sx = _next_true(r <= 100 - exit_rsi)
    n_ = len(df)
    orders = []
    for i in np.flatnonzero(longs | shorts):
        i = int(i)
        if i + 1 >= n_ or np.isnan(a[i]):
            continue
        side = 1 if longs[i] else -1
        sl = cv[i] - side * sl_atr * a[i]
        if tp_mode == "rsi":
            ex = lx[i + 1] if side > 0 else sx[i + 1]
            orders.append(Order(i=i, side=side, sl=sl, tp=NAN, max_hold=max_hold, exit_i=int(min(ex, n_ - 1)), tag="rsix"))
        else:
            tp = mid[i]
            if np.isnan(tp) or (tp - cv[i]) * side <= 0:
                continue
            orders.append(Order(i=i, side=side, sl=sl, tp=tp, max_hold=max_hold, tag="rsix"))
    return orders


# ================================================================= M03 Bollinger fade, exit on mid cross
def bb_fade_cross(df, n=20, k=2.0, rsi_filter=False, rsi_n=14, rsi_lo=30, rsi_hi=70, sl_mode="atr", sl_val=2.0,
                  atr_n=14, max_hold=40, **kw):
    """M03. Long when close < lower band (optionally RSI(14) < 30); exit at the first close back above the
    middle band. Stop: sl_mode 'atr' = sl_val x ATR(14); 'band' = sl_val x band width beyond entry."""
    c = df["close"]
    bb = F.bollinger(c, n, k)
    cv = c.values
    lo, hi, mid = bb["lower"].values, bb["upper"].values, bb["mid"].values
    a = F.atr(df, atr_n).values
    r = F.rsi(c, rsi_n).values
    longs = cv < lo
    shorts = cv > hi
    if rsi_filter:
        longs &= r < rsi_lo
        shorts &= r > rsi_hi
    lx = _next_true(cv > mid)
    sx = _next_true(cv < mid)
    n_ = len(df)
    orders = []
    for i in np.flatnonzero(longs | shorts):
        i = int(i)
        if i + 1 >= n_ or np.isnan(a[i]) or np.isnan(mid[i]):
            continue
        side = 1 if longs[i] else -1
        d = sl_val * a[i] if sl_mode == "atr" else sl_val * (hi[i] - lo[i])
        if d <= 0:
            continue
        ex = lx[i + 1] if side > 0 else sx[i + 1]
        orders.append(Order(i=i, side=side, sl=cv[i] - side * d, tp=NAN, max_hold=max_hold, exit_i=int(min(ex, n_ - 1)), tag="bbx"))
    return orders


# ================================================================= M04 z-score re-entry
def zscore_reentry(df, n=20, entry_z=2.0, exit_z=0.0, stop_mode="z", stop_val=3.0, atr_n=14, max_hold=40, **kw):
    """M04. z = (close - SMA(n)) / sd(n). Long when z crosses back above -entry_z (after having been below),
    exit when z crosses >= exit_z. Stop at z = -stop_val (price = mid - stop_val*sd at entry) or stop_val x ATR."""
    c = df["close"]
    bb = F.bollinger(c, n, 1.0)
    z = bb["z"].values
    mid = bb["mid"].values
    sd = (bb["upper"] - bb["mid"]).values
    a = F.atr(df, atr_n).values
    cv = c.values
    z1 = np.roll(z, 1); z1[0] = np.nan
    longs = (z > -entry_z) & (z1 <= -entry_z)
    shorts = (z < entry_z) & (z1 >= entry_z)
    lx = _next_true(z >= exit_z)
    sx = _next_true(z <= -exit_z)
    n_ = len(df)
    orders = []
    for i in np.flatnonzero(longs | shorts):
        i = int(i)
        if i + 1 >= n_ or np.isnan(a[i]) or np.isnan(sd[i]) or sd[i] <= 0:
            continue
        side = 1 if longs[i] else -1
        if stop_mode == "z":
            sl = mid[i] - side * stop_val * sd[i]
        else:
            sl = cv[i] - side * stop_val * a[i]
        if (cv[i] - sl) * side <= 0:
            continue
        ex = lx[i + 1] if side > 0 else sx[i + 1]
        orders.append(Order(i=i, side=side, sl=sl, tp=NAN, max_hold=max_hold, exit_i=int(min(ex, n_ - 1)), tag="zre"))
    return orders


# ================================================================= M05-M08 pivot families
def pivot_level_sets(lv: pd.DataFrame, ptype: str) -> dict:
    """Level arrays from previous-day OHLC. ptype: classic | fib | woodie | woodie_open | camarilla.
    Returns dict with keys pp, r1, s1, r2, s2 (and h3,h4,l3,l4,c for camarilla)."""
    H, L, C, O = lv["pd_high"].values, lv["pd_low"].values, lv["pd_close"].values, lv["day_open"].values
    rng = H - L
    if ptype == "classic":
        pp = (H + L + C) / 3
        return dict(pp=pp, r1=2 * pp - L, s1=2 * pp - H, r2=pp + rng, s2=pp - rng, r3=H + 2 * (pp - L), s3=L - 2 * (H - pp))
    if ptype == "fib":
        pp = (H + L + C) / 3
        return dict(pp=pp, r1=pp + 0.382 * rng, s1=pp - 0.382 * rng, r2=pp + 0.618 * rng, s2=pp - 0.618 * rng,
                    r3=pp + rng, s3=pp - rng)
    if ptype in ("woodie", "woodie_open"):
        pp = (H + L + 2 * (C if ptype == "woodie" else O)) / 4
        return dict(pp=pp, r1=2 * pp - L, s1=2 * pp - H, r2=pp + rng, s2=pp - rng, r3=H + 2 * (pp - L), s3=L - 2 * (H - pp))
    if ptype == "camarilla":
        return dict(pp=C, c=C, h3=C + rng * 1.1 / 4, l3=C - rng * 1.1 / 4, h4=C + rng * 1.1 / 2, l4=C - rng * 1.1 / 2,
                    h5=np.where(L > 0, H / L * C, np.nan), l5=np.where(H > 0, C - (H / L * C - C), np.nan), rng=rng)
    raise ValueError(ptype)


def pivot_levels(df, ptype="classic", mode="fade", entry_style="limit", day_start=0, start_hour=7, end_hour=16,
                 exit_hour=20, require_open_inside=True, sl_frac=0.5, buffer_pips=2.0, tp_rng=1.0, cam_tp="c", **kw):
    """M05-M08. Classic/Fibonacci/Woodie: mode 'fade' = buy S1 / sell R1 (limit at the level, or 'reject' =
    market entry after a bar that touched the level and closed back inside), stop halfway to the next level
    (sl_frac x (S1-S2)), target PP, only when the day opened between S1 and R1 (require_open_inside).
    mode 'break' = buy when a bar closes above R1 ('close') or buy-stop at R1 ('limit' = stop order),
    stop halfway back to PP, target R2.
    Camarilla: fade = sell H3 / buy L3, stop beyond H4/L4 (+buffer), target prev close (cam_tp 'c') or the
    opposite inner level ('opp'); break = stop order at H4/L4, stop back at H3/L3, target entry +/- tp_rng x range.
    One trade per day, entries only in [start_hour, end_hour) UTC, flat at exit_hour."""
    lv = F.prev_day_levels(df, day_start)
    S = pivot_level_sets(lv, ptype)
    hrs = (df.index.hour + df.index.minute / 60).values
    day = (df.index - pd.Timedelta(hours=day_start)).floor("D").values
    bpd = _bars_per_day(df)
    step_h = 24 / bpd
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
    dopen = lv["day_open"].values
    n_ = len(df)
    orders = []
    last = None
    done = False
    cam = ptype == "camarilla"
    if cam:
        up_lvl, dn_lvl = (S["h3"], S["l3"]) if mode == "fade" else (S["h4"], S["l4"])
    else:
        up_lvl, dn_lvl = S["r1"], S["s1"]
    for i in range(1, n_ - 1):
        if day[i] != last:
            last = day[i]
            done = False
        if done:
            continue
        hr = hrs[i]
        if hr < start_hour or hr >= end_hour:
            continue
        if np.isnan(up_lvl[i]) or np.isnan(dn_lvl[i]) or np.isnan(S["pp"][i]):
            continue
        if require_open_inside and not (dn_lvl[i] < dopen[i] < up_lvl[i]):
            done = True
            continue
        bars_valid = max(1, int((end_hour - hr) / step_h))
        exit_i = i + int((exit_hour - hr) / step_h)
        if mode == "fade":
            if cam:
                lsl = S["l4"][i] - buffer_pips * PIP; ssl = S["h4"][i] + buffer_pips * PIP
                ltp = S["c"][i] if cam_tp == "c" else S["h3"][i]
                stp = S["c"][i] if cam_tp == "c" else S["l3"][i]
            else:
                lsl = S["s1"][i] - sl_frac * (S["s1"][i] - S["s2"][i]); ssl = S["r1"][i] + sl_frac * (S["r2"][i] - S["r1"][i])
                ltp = S["pp"][i]; stp = S["pp"][i]
            if entry_style == "limit":
                done = True
                if dn_lvl[i] < c[i] and ltp > dn_lvl[i]:
                    orders.append(Order(i=i, side=1, entry_type="limit", entry_price=dn_lvl[i], sl=lsl, tp=ltp,
                                        expiry_bars=bars_valid, exit_i=exit_i, tag=f"{ptype}_fade"))
                if up_lvl[i] > c[i] and stp < up_lvl[i]:
                    orders.append(Order(i=i, side=-1, entry_type="limit", entry_price=up_lvl[i], sl=ssl, tp=stp,
                                        expiry_bars=bars_valid, exit_i=exit_i, tag=f"{ptype}_fade"))
            else:  # 'reject': bar touched the level and closed back inside, previous bar did not touch
                if l[i] <= dn_lvl[i] < c[i] and l[i - 1] > dn_lvl[i - 1] and ltp > c[i]:
                    orders.append(Order(i=i, side=1, sl=lsl, tp=ltp, exit_i=exit_i, tag=f"{ptype}_rej")); done = True
                elif h[i] >= up_lvl[i] > c[i] and h[i - 1] < up_lvl[i - 1] and stp < c[i]:
                    orders.append(Order(i=i, side=-1, sl=ssl, tp=stp, exit_i=exit_i, tag=f"{ptype}_rej")); done = True
        else:  # break
            if cam:
                lsl, ssl = S["h3"][i], S["l3"][i]
                ltp = S["h4"][i] + tp_rng * S["rng"][i]; stp = S["l4"][i] - tp_rng * S["rng"][i]
            else:
                lsl = S["r1"][i] - sl_frac * (S["r1"][i] - S["pp"][i]); ssl = S["s1"][i] + sl_frac * (S["pp"][i] - S["s1"][i])
                ltp, stp = S["r2"][i], S["s2"][i]
            if entry_style == "close":
                if c[i] > up_lvl[i] and c[i - 1] <= up_lvl[i - 1] and ltp > c[i] > lsl:
                    orders.append(Order(i=i, side=1, sl=lsl, tp=ltp, exit_i=exit_i, tag=f"{ptype}_brk")); done = True
                elif c[i] < dn_lvl[i] and c[i - 1] >= dn_lvl[i - 1] and stp < c[i] < ssl:
                    orders.append(Order(i=i, side=-1, sl=ssl, tp=stp, exit_i=exit_i, tag=f"{ptype}_brk")); done = True
            else:  # stop orders resting at the levels
                done = True
                if c[i] < up_lvl[i]:
                    orders.append(Order(i=i, side=1, entry_type="stop", entry_price=up_lvl[i] + buffer_pips * PIP, sl=lsl, tp=ltp,
                                        expiry_bars=bars_valid, exit_i=exit_i, tag=f"{ptype}_brk"))
                if c[i] > dn_lvl[i]:
                    orders.append(Order(i=i, side=-1, entry_type="stop", entry_price=dn_lvl[i] - buffer_pips * PIP, sl=ssl, tp=stp,
                                        expiry_bars=bars_valid, exit_i=exit_i, tag=f"{ptype}_brk"))
    return orders


# ================================================================= M09 round numbers
def round_number(df, mode="fade", levels="00", lookback=24, sl_pips=15, tp_pips=25, confirm_pips=12,
                 start_hour=7, end_hour=20, max_hold=48, **kw):
    """M09. levels '00' (step 100 pips), '50' (00 and 50), 'placebo' (25/75 levels = same spacing as '50', offset).
    fade: first touch (no touch of that level in the previous `lookback` bars) of the next level above/below,
    approached from a move into it -> fade at next open, stop sl_pips beyond the level, target tp_pips.
    break: first close more than confirm_pips beyond a level that the previous `lookback` closes were on
    the other side of -> go with the break, stop 2 pips back through the level, target tp_pips."""
    step = 0.0100 if levels == "00" else 0.0050
    off = 0.0025 if levels == "placebo" else 0.0
    o, h, l, c = df["open"].values, df["high"].values, df["low"].values, df["close"].values
    hrs = (df.index.hour + df.index.minute / 60).values
    n_ = len(df)
    pc = np.roll(c, 1); pc[0] = np.nan
    up_lvl = np.floor((pc - off) / step) * step + step + off      # next level above previous close
    dn_lvl = np.ceil((pc - off) / step) * step - step + off       # next level below previous close
    hmax = pd.Series(h).rolling(lookback).max().shift(1).values   # previous `lookback` bars, excluding i
    lmin = pd.Series(l).rolling(lookback).min().shift(1).values
    cmax = pd.Series(c).rolling(lookback).max().shift(1).values
    cmin = pd.Series(c).rolling(lookback).min().shift(1).values
    conf = confirm_pips * PIP
    orders = []
    for i in range(lookback + 1, n_ - 1):
        if hrs[i] < start_hour or hrs[i] >= end_hour or np.isnan(hmax[i]):
            continue
        if mode == "fade":
            if h[i] >= up_lvl[i] and hmax[i] < up_lvl[i]:          # first touch from below
                L = up_lvl[i]
                orders.append(Order(i=i, side=-1, sl=L + sl_pips * PIP, tp=c[i] - tp_pips * PIP, max_hold=max_hold, tag="rn_fade"))
            elif l[i] <= dn_lvl[i] and lmin[i] > dn_lvl[i]:
                L = dn_lvl[i]
                orders.append(Order(i=i, side=1, sl=L - sl_pips * PIP, tp=c[i] + tp_pips * PIP, max_hold=max_hold, tag="rn_fade"))
        else:
            Lb = np.floor((c[i] - conf - off) / step) * step + off   # highest level at least confirm below close
            if c[i] > Lb + conf and pc[i] <= Lb + conf and cmin[i] < Lb:
                orders.append(Order(i=i, side=1, sl=Lb - 2 * PIP, tp=Lb + tp_pips * PIP, max_hold=max_hold, tag="rn_brk"))
                continue
            Ls = np.ceil((c[i] + conf - off) / step) * step + off
            if c[i] < Ls - conf and pc[i] >= Ls - conf and cmax[i] > Ls:
                orders.append(Order(i=i, side=-1, sl=Ls + 2 * PIP, tp=Ls - tp_pips * PIP, max_hold=max_hold, tag="rn_brk"))
    return orders


# ================================================================= M10 previous-day high/low fade
def pdh_pdl_fade(df, day_start=22, sweep_min=3, sweep_max=15, tp="mid", sl_buffer=2.0, start_hour=6, end_hour=20,
                 **kw):
    """M10. A bar trades sweep_min..sweep_max pips beyond the previous day's high (low) - the first bar of the
    day to do so - and closes back inside the range: sell (buy) at the next open, stop at the sweep extreme
    + sl_buffer pips, target the previous day's midpoint ('mid') or the opposite extreme ('opp'), flat at the
    end of the day."""
    lv = F.prev_day_levels(df, day_start)
    pdh, pdl = lv["pd_high"].values, lv["pd_low"].values
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    hrs = (df.index.hour + df.index.minute / 60).values
    key = (df.index - pd.Timedelta(hours=day_start)).floor("D")
    pos = np.arange(len(df))
    day_last = pd.Series(pos, index=df.index).groupby(key.values).transform("max").values
    run_max = pd.Series(h).groupby(key.values).cummax().shift(1).values   # day's max high before bar i
    run_min = pd.Series(l).groupby(key.values).cummin().shift(1).values
    first_of_day = pd.Series(pos, index=df.index).groupby(key.values).transform("min").values
    n_ = len(df)
    orders = []
    for i in range(1, n_ - 1):
        if np.isnan(pdh[i]) or hrs[i] < start_hour or hrs[i] >= end_hour:
            continue
        prev_max = run_max[i] if i != first_of_day[i] else -np.inf
        prev_min = run_min[i] if i != first_of_day[i] else np.inf
        mid = (pdh[i] + pdl[i]) / 2
        ex = int(day_last[i])
        if h[i] - pdh[i] >= sweep_min * PIP and h[i] - pdh[i] <= sweep_max * PIP and c[i] < pdh[i] and prev_max <= pdh[i]:
            tpx = mid if tp == "mid" else pdl[i]
            if tpx < c[i]:
                orders.append(Order(i=i, side=-1, sl=h[i] + sl_buffer * PIP, tp=tpx, exit_i=ex, tag="pdh_fade"))
        elif pdl[i] - l[i] >= sweep_min * PIP and pdl[i] - l[i] <= sweep_max * PIP and c[i] > pdl[i] and prev_min >= pdl[i]:
            tpx = mid if tp == "mid" else pdh[i]
            if tpx > c[i]:
                orders.append(Order(i=i, side=1, sl=l[i] - sl_buffer * PIP, tp=tpx, exit_i=ex, tag="pdl_fade"))
    return orders


def turtle_soup_d1(df, n=20, min_age=4, hold=3, sl_pips=2.0, tp_atr=NAN, atr_n=14, **kw):
    """M10 daily variant (Connors-Raschke turtle soup): today's low undercuts the prior n-day low whose bar is
    at least min_age days old and the close is back above it -> long next open, stop under today's low."""
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    a = F.atr(df, atr_n).values
    lo_n = pd.Series(l).rolling(n).min().shift(1).values
    hi_n = pd.Series(h).rolling(n).max().shift(1).values
    lo_pos = pd.Series(l).rolling(n).apply(lambda x: int(np.argmin(x)), raw=True).shift(1).values  # position in window
    hi_pos = pd.Series(h).rolling(n).apply(lambda x: int(np.argmax(x)), raw=True).shift(1).values
    orders = []
    for i in range(n + 1, len(df) - 1):
        if np.isnan(lo_n[i]) or np.isnan(a[i]):
            continue
        age_lo = n - 1 - lo_pos[i]   # 0 = yesterday
        age_hi = n - 1 - hi_pos[i]
        if l[i] < lo_n[i] and c[i] > lo_n[i] and age_lo >= min_age - 1:
            tp = c[i] + tp_atr * a[i] if not math.isnan(tp_atr) else NAN
            orders.append(Order(i=i, side=1, sl=l[i] - sl_pips * PIP, tp=tp, max_hold=hold, tag="tsoup"))
        elif h[i] > hi_n[i] and c[i] < hi_n[i] and age_hi >= min_age - 1:
            tp = c[i] - tp_atr * a[i] if not math.isnan(tp_atr) else NAN
            orders.append(Order(i=i, side=-1, sl=h[i] + sl_pips * PIP, tp=tp, max_hold=hold, tag="tsoup"))
    return orders


# ================================================================= M11 weekly-open mean reversion
def weekly_open_mr(df, dist_adr=1.0, sl_adr=1.0, adr_n=14, days=(1, 2), exit_london_hour=15, **kw):
    """M11. Weekly open = open of the first bar of the week (Sunday 21/22 UTC). On Tuesday/Wednesday (UTC
    weekdays in `days`), when the close is >= dist_adr x ADR(14) away from the weekly open, fade toward it:
    stop sl_adr x ADR beyond entry, target the weekly open, time stop Friday exit_london_hour London."""
    wk = (df.index.tz_convert(None) - pd.Timedelta(hours=21)).to_period("W-SAT")
    pos = np.arange(len(df))
    g = pd.Series(pos, index=df.index).groupby(wk.values)
    wfirst = g.transform("min").values
    wlast = g.transform("max").values
    o, c = df["open"].values, df["close"].values
    wopen = o[wfirst]
    adr = _adr_by_bar(df, adr_n, 22)
    lon = df.index.tz_convert("Europe/London")
    is_exit = (lon.dayofweek == 4) & (lon.hour >= exit_london_hour)
    nt_exit = _next_true(is_exit)
    dow = df.index.dayofweek.values
    n_ = len(df)
    orders = []
    last_wk = None
    for i in range(n_ - 1):
        if wfirst[i] != last_wk:
            last_wk = wfirst[i]; done = False
        if done or dow[i] not in days or np.isnan(adr[i]):
            continue
        d = c[i] - wopen[i]
        if abs(d) >= dist_adr * adr[i]:
            side = -1 if d > 0 else 1
            ex = min(nt_exit[i + 1], wlast[i])
            orders.append(Order(i=i, side=side, sl=c[i] - side * sl_adr * adr[i], tp=wopen[i], exit_i=int(ex), tag="wopen"))
            done = True
    return orders


# ================================================================= M12 daily-open mean reversion
def daily_open_mr(df, day_start=0, dist_adr=0.5, sl_adr=0.5, adr_n=14, ny_start=13, ny_end=16, exit_hour=21, **kw):
    """M12. Reference = day open (day_start UTC). During [ny_start, ny_end) UTC, if the close is >= dist_adr x ADR
    from the open, fade toward it: stop sl_adr x ADR beyond the day's extreme so far, target the open,
    flat at exit_hour UTC. One trade per day."""
    lv = F.prev_day_levels(df, day_start)
    dopen = lv["day_open"].values
    key = (df.index - pd.Timedelta(hours=day_start)).floor("D").values
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    run_max = pd.Series(h).groupby(key).cummax().values
    run_min = pd.Series(l).groupby(key).cummin().values
    adr = _adr_by_bar(df, adr_n, 22)
    hrs = (df.index.hour + df.index.minute / 60).values
    bpd = _bars_per_day(df)
    step_h = 24 / bpd
    n_ = len(df)
    orders = []
    last = None
    for i in range(n_ - 1):
        if key[i] != last:
            last = key[i]; done = False
        if done or hrs[i] < ny_start or hrs[i] >= ny_end or np.isnan(adr[i]) or np.isnan(dopen[i]):
            continue
        d = c[i] - dopen[i]
        if abs(d) >= dist_adr * adr[i]:
            side = -1 if d > 0 else 1
            sl = run_max[i] + sl_adr * adr[i] if side < 0 else run_min[i] - sl_adr * adr[i]
            exit_i = i + int((exit_hour - hrs[i]) / step_h)
            orders.append(Order(i=i, side=side, sl=sl, tp=dopen[i], exit_i=exit_i, tag="dopen"))
            done = True
    return orders


# ================================================================= M13 streak fade
def streak_fade(df, streak=3, min_cum_pct=1.0, hold=1, sl_atr=NAN, atr_n=14, direction="fade", **kw):
    """M13 (tastyfx). After `streak` consecutive closes in one direction with |cumulative move| > min_cum_pct %,
    enter against the streak (direction 'fade') or with it ('momentum') at the next open; exit at the close
    `hold` days later. Optional ATR stop."""
    c = df["close"].values
    a = F.atr(df, atr_n).values
    r = np.diff(c, prepend=np.nan)
    up = pd.Series(r > 0).rolling(streak).sum().values == streak
    dn = pd.Series(r < 0).rolling(streak).sum().values == streak
    cum = c / np.roll(c, streak) - 1
    sgn = 1 if direction == "momentum" else -1
    orders = []
    for i in range(streak, len(df) - 1):
        if np.isnan(a[i]):
            continue
        if up[i] and cum[i] > min_cum_pct / 100:
            side = sgn
        elif dn[i] and cum[i] < -min_cum_pct / 100:
            side = -sgn
        else:
            continue
        sl = c[i] - side * sl_atr * a[i] if not math.isnan(sl_atr) else NAN
        orders.append(Order(i=i, side=side, sl=sl, exit_i=i + hold, tag="streak"))
    return orders


# ================================================================= M14 Caporale-Plastun abnormal days
def abnormal_day_contrarian(df, window=20, k=2.0, hold=1, sl_atr=NAN, atr_n=14, direction="contrarian", **kw):
    """M14 daily leg. Day t is abnormal if its close-to-close return lies beyond mean +/- k sd of the previous
    `window` daily returns. At the close of the abnormal day enter against it ('contrarian') or with it
    ('momentum'), exit at the close `hold` days later."""
    c = df["close"].values
    a = F.atr(df, atr_n).values
    r = pd.Series(c).pct_change()
    mu = r.rolling(window).mean().shift(1).values
    sd = r.rolling(window).std().shift(1).values
    rv = r.values
    sgn = -1 if direction == "contrarian" else 1
    orders = []
    for i in range(window + 1, len(df) - 1):
        if np.isnan(sd[i]) or np.isnan(a[i]):
            continue
        if rv[i] > mu[i] + k * sd[i]:
            side = sgn
        elif rv[i] < mu[i] - k * sd[i]:
            side = -sgn
        else:
            continue
        sl = c[i] - side * sl_atr * a[i] if not math.isnan(sl_atr) else NAN
        orders.append(Order(i=i, side=side, sl=sl, exit_i=i + hold, tag="abn_d"))
    return orders


def abnormal_day_momentum(df, window=20, k=2.0, last_entry_hour=18, sl_atr=NAN, atr_n=14, min_bars=12, **kw):
    """M14 intraday leg (H1). Daily (UTC-day) return threshold = mean +/- k sd of the previous `window` daily
    close-to-close returns. On the first hourly bar whose close-to-close return from the previous day's close
    exceeds the threshold, enter in that direction (next bar open) and exit at the close of the day."""
    d = F.daily_ohlc(df, 0)
    d = d[d["n"] >= min_bars]
    r = d["close"].pct_change()
    thr_hi = (r.rolling(window).mean() + k * r.rolling(window).std()).shift(1)
    thr_lo = (r.rolling(window).mean() - k * r.rolling(window).std()).shift(1)
    pclose = d["close"].shift(1)
    key = df.index.floor("D")
    hi = thr_hi.reindex(key).values; lo = thr_lo.reindex(key).values; pc = pclose.reindex(key).values
    c = df["close"].values
    a = F.atr(df, atr_n).values
    ret = c / pc - 1
    day_last = _day_last_index(df, 0)
    hrs = df.index.hour.values
    keyv = key.values
    orders = []
    last = None
    for i in range(1, len(df) - 1):
        if keyv[i] != last:
            last = keyv[i]; done = False
        if done or np.isnan(hi[i]) or np.isnan(ret[i]) or hrs[i] > last_entry_hour:
            continue
        if ret[i] > hi[i]:
            side = 1
        elif ret[i] < lo[i]:
            side = -1
        else:
            continue
        done = True
        if int(day_last[i]) <= i + 1:
            continue
        sl = c[i] - side * sl_atr * a[i] if not math.isnan(sl_atr) else NAN
        orders.append(Order(i=i, side=side, sl=sl, exit_i=int(day_last[i]), tag="abn_h"))
    return orders


# ================================================================= M15 Quantified Strategies reconstruction
def lowest_close_mr(df, n=5, hold=1, sides="long", sl_atr=NAN, atr_n=14, **kw):
    """M15 (reconstruction - rules not public). Long at the next open when today's close is the lowest close
    of the last n days; short when it is the highest (sides 'both'); exit at the close `hold` days later."""
    c = df["close"].values
    a = F.atr(df, atr_n).values
    lo = pd.Series(c).rolling(n).min().values
    hi = pd.Series(c).rolling(n).max().values
    orders = []
    for i in range(n, len(df) - 1):
        if np.isnan(a[i]):
            continue
        if c[i] <= lo[i] and sides in ("long", "both"):
            side = 1
        elif c[i] >= hi[i] and sides in ("short", "both"):
            side = -1
        else:
            continue
        sl = c[i] - side * sl_atr * a[i] if not math.isnan(sl_atr) else NAN
        orders.append(Order(i=i, side=side, sl=sl, exit_i=i + hold, tag="lcmr"))
    return orders


# ================================================================= Q01 Backtrex MACD+RSI (H1, SL45/TP90)
def macd_rsi_fixed(df, fast=12, slow=26, signal=9, rsi_n=14, rsi_mode="above50", sl_pips=45, tp_pips=90, max_hold=10**6, **kw):
    """Q01 replica. Long on a MACD line/signal bullish cross with an RSI(14) filter ('above50': RSI > 50,
    'not_extreme': RSI < 70; mirrored for shorts); fixed stop/target in pips (Backtrex: 45/90)."""
    m = F.macd(df["close"], fast, slow, signal)
    r = F.rsi(df["close"], rsi_n).values
    line, sig = m["macd"].values, m["signal"].values
    l1, s1 = np.roll(line, 1), np.roll(sig, 1)
    up = (line > sig) & (l1 <= s1)
    dn = (line < sig) & (l1 >= s1)
    if rsi_mode == "above50":
        up &= r > 50; dn &= r < 50
    elif rsi_mode == "not_extreme":
        up &= r < 70; dn &= r > 30
    c = df["close"].values
    orders = []
    for i in np.flatnonzero(up | dn):
        i = int(i)
        if i == 0 or np.isnan(r[i]):
            continue
        side = 1 if up[i] else -1
        sl, tp = _sl_tp(side, c[i], sl_pips * PIP, tp_pips * PIP)
        orders.append(Order(i=i, side=side, sl=sl, tp=tp, max_hold=max_hold, tag="macdrsi"))
    return orders


# ================================================================= Q02 Dukascopy contest sample
def ma_cross_fixed(df, fast=7, slow=14, tp_pips=10, sl_pips=20, kind="sma", max_hold=10**6, **kw):
    """Q02 replica: MA(7)/MA(14) cross, TP 10 pips, SL 20 pips."""
    fn = F.sma if kind == "sma" else F.ema
    f, s = fn(df["close"], fast).values, fn(df["close"], slow).values
    f1, s1 = np.roll(f, 1), np.roll(s, 1)
    up = (f > s) & (f1 <= s1)
    dn = (f < s) & (f1 >= s1)
    c = df["close"].values
    orders = []
    for i in np.flatnonzero(up | dn):
        i = int(i)
        if i == 0 or np.isnan(s[i]):
            continue
        side = 1 if up[i] else -1
        sl, tp = _sl_tp(side, c[i], sl_pips * PIP, tp_pips * PIP)
        orders.append(Order(i=i, side=side, sl=sl, tp=tp, max_hold=max_hold, tag="macross"))
    return orders


# ================================================================= Q05 time-series momentum (EPAT)
def tsmom(df, lookback=120, sl_atr=NAN, atr_n=14, **kw):
    """Q05. Daily time-series momentum: position = sign(close - close[lookback]); enter at the next open when
    the sign flips, exit at the close of the bar on which it flips back (then the opposite trade starts).
    Must be run with one_at_a_time=False (the new trade is decided on the exit bar). Optional ATR stop."""
    c = df["close"].values
    a = F.atr(df, atr_n).values
    sig = np.sign(c - np.roll(c, lookback))
    sig[:lookback] = 0
    flip = np.zeros(len(c), dtype=bool)
    flip[1:] = (sig[1:] != sig[:-1]) & (sig[1:] != 0)
    nxt = _next_true(flip)
    orders = []
    n_ = len(c)
    for i in np.flatnonzero(flip):
        i = int(i)
        if i + 1 >= n_ or np.isnan(a[i]):
            continue
        side = int(sig[i])
        ex = nxt[i + 1]
        sl = c[i] - side * sl_atr * a[i] if not math.isnan(sl_atr) else NAN
        orders.append(Order(i=i, side=side, sl=sl, exit_i=int(min(ex, n_ - 1)), tag="tsmom"))
    return orders


# ================================================================= Q06 ML features (daily)
def ml_daily_features(df: pd.DataFrame, n_lags: int = 10) -> pd.DataFrame:
    """Feature matrix for next-day direction prediction (all features use bars <= t; target is sign of the
    close-to-close return of t+1)."""
    c = df["close"]
    r = np.log(c).diff()
    X = pd.DataFrame(index=df.index)
    for k in range(1, n_lags + 1):
        X[f"r{k}"] = r.shift(k - 1)          # r1 = today's return
    X["rv5"] = r.rolling(5).std()
    X["rv20"] = r.rolling(20).std()
    X["rv60"] = r.rolling(60).std()
    X["mom20"] = c / c.shift(20) - 1
    X["mom60"] = c / c.shift(60) - 1
    X["sma200_dist"] = c / c.rolling(200).mean() - 1
    X["rsi2"] = F.rsi(c, 2)
    X["rsi14"] = F.rsi(c, 14)
    X["z20"] = F.zscore(c, 20)
    X["range1"] = (df["high"] - df["low"]) / c
    X["range5"] = X["range1"].rolling(5).mean()
    X["body1"] = (c - df["open"]) / c
    X["dow"] = df.index.dayofweek
    X["month"] = df.index.month
    X["y_ret"] = r.shift(-1)                 # next-day log return (target)
    X["y"] = (X["y_ret"] > 0).astype(int)
    return X


REGISTRY.update({
    "connors_rsi2": connors_rsi2,
    "rsi_cross_back": rsi_cross_back,
    "bb_fade_cross": bb_fade_cross,
    "zscore_reentry": zscore_reentry,
    "pivot_levels": pivot_levels,
    "round_number": round_number,
    "pdh_pdl_fade": pdh_pdl_fade,
    "turtle_soup_d1": turtle_soup_d1,
    "weekly_open_mr": weekly_open_mr,
    "daily_open_mr": daily_open_mr,
    "streak_fade": streak_fade,
    "abnormal_day_contrarian": abnormal_day_contrarian,
    "abnormal_day_momentum": abnormal_day_momentum,
    "lowest_close_mr": lowest_close_mr,
    "macd_rsi_fixed": macd_rsi_fixed,
    "ma_cross_fixed": ma_cross_fixed,
    "tsmom": tsmom,
})
