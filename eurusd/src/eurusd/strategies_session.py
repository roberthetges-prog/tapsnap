"""Session / time-of-day, microstructure and calendar strategies from the research catalogue
(research/strategies.json ids S01-S19, B01, C01-C06, Q04).  Registered into eurusd.strategies.REGISTRY
at import time.  All local-time rules use tz_convert (London = Europe/London, ET = America/New_York);
bars are labelled by their START time.

Discretionary ICT concepts (Judas swing, killzone, FVG, silver bullet, power of three, liquidity sweep)
are mechanical RECONSTRUCTIONS - see each docstring.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

from .backtest import Order
from . import features as F
from .strategies import REGISTRY

PIP = 0.0001
NAN = math.nan


# ------------------------------------------------------------------ helpers
def _loc(df: pd.DataFrame, tz: str = "UTC", offset_h: float = 0.0):
    """Local fractional hour (minus offset, mod 24), integer day id (days start at offset_h local)
    and the local DatetimeIndex."""
    loc = df.index.tz_convert(tz)
    hrs = (loc.hour + loc.minute / 60.0).astype(float)
    naive = loc.tz_localize(None) - pd.Timedelta(hours=offset_h)
    dayid = ((naive.normalize() - pd.Timestamp("1970-01-01")) // pd.Timedelta(days=1)).values.astype(np.int64)
    hrs_off = (hrs - offset_h) % 24
    return np.asarray(hrs_off), dayid, loc


def _first_ge(dayid, hrs, hour):
    """per bar: index of the first bar of its day with hrs >= hour (nan if none)."""
    n = len(hrs)
    s = pd.Series(np.where(hrs >= hour, np.arange(n), np.nan))
    return s.groupby(dayid).transform("min").values


def _last_lt(dayid, hrs, hour):
    """per bar: index of the last bar of its day with hrs < hour (nan if none)."""
    n = len(hrs)
    s = pd.Series(np.where(hrs < hour, np.arange(n), np.nan))
    return s.groupby(dayid).transform("max").values


def _run_window(df, dayid, hrs, start, end):
    """Running high/low of the window [start,end) of the current (offset) day, per bar
    (cumulative within the window; NaN before the window starts; carried after it ends)."""
    inwin = (hrs >= start) & (hrs < end)
    hi = pd.Series(np.where(inwin, df["high"].values, np.nan)).groupby(dayid).cummax().groupby(dayid).ffill()
    lo = pd.Series(np.where(inwin, df["low"].values, np.nan)).groupby(dayid).cummin().groupby(dayid).ffill()
    cnt = pd.Series(inwin.astype(float)).groupby(dayid).cumsum()
    return hi.values, lo.values, cnt.values, inwin


def _daily_series(df, kind="adr", n=14, day_start=22):
    """Previous-days ADR (mean H-L) or ATR of NY-close days aligned to each bar (no lookahead)."""
    d = F.daily_ohlc(df, day_start)
    d = d[d["n"] >= 3]
    if kind == "adr":
        s = (d["high"] - d["low"]).rolling(n).mean().shift(1)
    elif kind == "atr":
        s = F.atr(d, n).shift(1)
    elif kind == "dir":  # previous day's close-open sign
        s = np.sign(d["close"] - d["open"]).shift(1)
    else:
        raise ValueError(kind)
    key = (df.index - pd.Timedelta(hours=day_start)).floor("D") + pd.Timedelta(hours=day_start)
    return s.reindex(key).values


def _first_trigger(o, h, l, j0, j1, buy_px, sell_px, spread=PIP):
    """OCO resolution: which pending stop (buy above / sell below) triggers first in bars j0..j1."""
    for j in range(j0, j1 + 1):
        b = not math.isnan(buy_px) and h[j] + spread >= buy_px
        s = not math.isnan(sell_px) and l[j] <= sell_px
        if b and s:
            return (1 if abs(o[j] - buy_px) <= abs(o[j] - sell_px) else -1), j
        if b:
            return 1, j
        if s:
            return -1, j
    return 0, -1


def _sl_tp_prices(side, ref, d_sl, d_tp):
    if side > 0:
        return ref - d_sl, (ref + d_tp if not math.isnan(d_tp) else NAN)
    return ref + d_sl, (ref - d_tp if not math.isnan(d_tp) else NAN)


# ------------------------------------------------------------------ S01/S02/S03/S12/S13/B01: range breakouts
def range_breakout(df, tz="UTC", day_offset=0.0, rng_start=0.0, rng_end=7.0, entry_until=10.0, exit_hour=12.0,
                   entry_mode="stop", buffer_pips=2.0, buffer_atr_frac=NAN,
                   sl_mode="range", sl_val=1.0, sl_cap_pips=NAN, tp_mode="rr", tp_val=2.0,
                   min_range_pips=5.0, max_range_pips=150.0, max_ratio=NAN, min_ratio=NAN, adr_len=14,
                   bias="none", min_bars_frac=0.5, tag="brk", **kw):
    """Generic session-range breakout in local time `tz` (hours measured from `day_offset`).
    Range = [rng_start, rng_end); decision at the close of the last range bar; one trade per day.
    entry_mode 'stop': buy stop at high+buffer / sell stop at low-buffer, OCO-resolved on the bars, valid until
    entry_until; 'close': first bar closing beyond the range (+buffer) -> market at next open.
    buffer = buffer_pips or buffer_atr_frac x ATR(14, NY-close days).
    sl_mode: 'range' (sl_val x range beyond the breakout level + buffer = opposite side when sl_val=1),
             'mid' (range midpoint), 'pips' (sl_val pips); sl_cap_pips caps the distance.
    tp_mode: 'rr' (tp_val x SL distance), 'range' (tp_val x range), 'pips', 'half_adr' (0.5 x ADR(adr_len)).
    max_ratio / min_ratio: only trade when range / ADR(adr_len) is below / above the threshold (S12 filter).
    bias 'prev_day': only in the direction of the previous NY-close day's close-open."""
    hrs, dayid, _ = _loc(df, tz, day_offset)
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    hi, lo, cnt, inwin = _run_window(df, dayid, hrs, rng_start, rng_end)
    last_rng = _last_lt(dayid, hrs, rng_end)
    last_entry = _last_lt(dayid, hrs, entry_until)
    last_exit = _last_lt(dayid, hrs, exit_hour)
    adr = _daily_series(df, "adr", adr_len)
    atr_d = _daily_series(df, "atr", 14) if not math.isnan(buffer_atr_frac) else None
    pdir = _daily_series(df, "dir") if bias == "prev_day" else None
    step_h = 24 / int(pd.Timedelta("1D") / (df.index[1:] - df.index[:-1]).min())
    need = max(1, int(min_bars_frac * (rng_end - rng_start) / step_h))
    n = len(df)
    orders = []
    cand = np.flatnonzero(inwin & (np.arange(n) == np.nan_to_num(last_rng, nan=-1)))
    for i in cand:
        if np.isnan(hi[i]) or cnt[i] < need or np.isnan(last_entry[i]) or np.isnan(last_exit[i]):
            continue
        rng = hi[i] - lo[i]
        if not (min_range_pips * PIP <= rng <= max_range_pips * PIP):
            continue
        if not (math.isnan(max_ratio) and math.isnan(min_ratio)):
            if np.isnan(adr[i]) or adr[i] <= 0:
                continue
            ratio = rng / adr[i]
            if (not math.isnan(max_ratio) and ratio > max_ratio) or (not math.isnan(min_ratio) and ratio < min_ratio):
                continue
        buf = buffer_pips * PIP
        if atr_d is not None:
            if np.isnan(atr_d[i]):
                continue
            buf = buffer_atr_frac * atr_d[i]
        j_last = int(last_entry[i])
        exit_i = int(last_exit[i])
        if j_last <= i or exit_i <= i:
            continue
        buy_px, sell_px = hi[i] + buf, lo[i] - buf
        if bias == "prev_day":
            if np.isnan(pdir[i]) or pdir[i] == 0:
                continue
            if pdir[i] > 0:
                sell_px = NAN
            else:
                buy_px = NAN
        if entry_mode == "stop":
            side, j = _first_trigger(o, h, l, i + 1, min(j_last, n - 1), buy_px, sell_px)
            if side == 0:
                continue
            px = buy_px if side > 0 else sell_px
            oi, etype, ep, exp = i, "stop", px, j_last - i
        else:  # first close beyond the range
            side, j = 0, -1
            for jj in range(i + 1, min(j_last, n - 1) + 1):
                if not math.isnan(buy_px) and c[jj] > buy_px:
                    side, j = 1, jj
                    break
                if not math.isnan(sell_px) and c[jj] < sell_px:
                    side, j = -1, jj
                    break
            if side == 0 or j >= n - 1:
                continue
            px = buy_px if side > 0 else sell_px
            oi, etype, ep, exp = j, "market", NAN, 1
        # stop distance measured from the breakout level px
        if sl_mode == "range":
            d_sl = sl_val * rng + buf
        elif sl_mode == "mid":
            d_sl = rng / 2 + buf
        else:
            d_sl = sl_val * PIP
        if not math.isnan(sl_cap_pips):
            d_sl = min(d_sl, sl_cap_pips * PIP)
        if tp_mode == "rr":
            d_tp = tp_val * d_sl
        elif tp_mode == "range":
            d_tp = tp_val * rng
        elif tp_mode == "pips":
            d_tp = tp_val * PIP
        elif tp_mode == "half_adr":
            if np.isnan(adr[i]):
                continue
            d_tp = 0.5 * adr[i]
        else:
            d_tp = NAN
        sl, tp = _sl_tp_prices(side, px, d_sl, d_tp)
        orders.append(Order(i=int(oi), side=side, entry_type=etype, entry_price=ep, sl=sl, tp=tp,
                            expiry_bars=max(1, int(exp)), exit_i=exit_i, tag=tag))
    return orders


def london_range_fade_second(df, tz="America/New_York", rng_start=3.0, rng_end=8.0, entry_until=16.0, exit_hour=17.0,
                             buffer_pips=1.0, tp_val=1.0, sl_min_frac=0.25, **kw):
    """B01 variant: after the London range (03:00-08:00 ET) breaks on one side and then price breaks the
    OTHER side too, fade the second break (enter back toward the range: short after a second-break-up).
    SL beyond the second-break extreme by max(buffer, sl_min_frac x range), TP = tp_val x range from the entry bar's close back
    toward the first-break side."""
    hrs, dayid, _ = _loc(df, tz)
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    hi, lo, cnt, inwin = _run_window(df, dayid, hrs, rng_start, rng_end)
    last_rng = _last_lt(dayid, hrs, rng_end)
    last_entry = _last_lt(dayid, hrs, entry_until)
    last_exit = _last_lt(dayid, hrs, exit_hour)
    n = len(df)
    orders = []
    for i in np.flatnonzero(inwin & (np.arange(n) == np.nan_to_num(last_rng, nan=-1))):
        if np.isnan(hi[i]) or np.isnan(last_entry[i]) or np.isnan(last_exit[i]):
            continue
        rng = hi[i] - lo[i]
        if rng < 5 * PIP:
            continue
        buf = buffer_pips * PIP
        first = 0
        for j in range(i + 1, min(int(last_entry[i]), n - 2) + 1):
            up, dn = h[j] > hi[i] + buf, l[j] < lo[i] - buf
            if first == 0:
                if up and dn:
                    break
                if up:
                    first = 1
                elif dn:
                    first = -1
                continue
            if first == 1 and dn:      # second break is down -> fade: go long back toward the range
                sl = min(l[j], lo[i]) - max(buf, sl_min_frac * rng)
                tp = c[j] + tp_val * rng
                if sl >= c[j]:
                    break
                orders.append(Order(i=j, side=1, sl=sl, tp=tp, exit_i=int(last_exit[i]), tag="b01f"))
                break
            if first == -1 and up:
                sl = max(h[j], hi[i]) + max(buf, sl_min_frac * rng)
                tp = c[j] - tp_val * rng
                if sl <= c[j]:
                    break
                orders.append(Order(i=j, side=-1, sl=sl, tp=tp, exit_i=int(last_exit[i]), tag="b01f"))
                break
    return orders


# ------------------------------------------------------------------ S04/S07/S10/S12: sweep-and-reverse
def asian_sweep_reverse(df, tz="UTC", day_offset=0.0, rng_start=0.0, rng_end=7.0, kz_start=7.0, kz_end=10.0,
                        sweep_min_pips=3.0, sl_buffer_pips=3.0, tp_mode="range", tp_val=2.0, exit_hour=16.0,
                        confirm="close_inside", decide_at=NAN, bias="none", min_ratio=NAN, max_ratio=NAN, adr_len=14,
                        min_range_pips=10.0, max_range_pips=150.0, engulf=False, tag="swp", **kw):
    """RECONSTRUCTION of the Judas swing / Frankfurt trap / Power-of-three manipulation leg.
    Range = [rng_start, rng_end) local hours (Asian range).  In the killzone [kz_start, kz_end): the first bar
    whose killzone running high exceeds the range high by >= sweep_min_pips and that CLOSES back inside the range
    (confirm='close_inside') or back through the day's open (confirm='daily_open') triggers a SHORT at the next
    open (mirror for lows).  SL = killzone extreme + sl_buffer; TP: 'range' = opposite range edge, 'rr' = tp_val x
    risk, 'range_min_rr' = opposite edge but skip if that is < tp_val x risk.  Flat at exit_hour.  One trade/day.
    decide_at: evaluate only at the bar starting at that hour (S04: 8.0 on H1 = the 08:00 candle's close).
    bias 'prev_day': only trade in the direction of the previous NY-close day; 'contra': the opposite.
    engulf: additionally require the confirming bar to close beyond the previous bar's open."""
    hrs, dayid, _ = _loc(df, tz, day_offset)
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    hi, lo, cnt, inwin = _run_window(df, dayid, hrs, rng_start, rng_end)
    kz_hi, kz_lo, _, inkz = _run_window(df, dayid, hrs, kz_start, kz_end)
    last_exit = _last_lt(dayid, hrs, exit_hour)
    day_open = pd.Series(o).groupby(dayid).transform("first").values
    adr = _daily_series(df, "adr", adr_len) if not (math.isnan(min_ratio) and math.isnan(max_ratio)) else None
    pdir = _daily_series(df, "dir") if bias in ("prev_day", "contra") else None
    n = len(df)
    orders = []
    done_day = -1
    smin = sweep_min_pips * PIP
    buf = sl_buffer_pips * PIP
    cand = np.flatnonzero(inkz & (hrs >= rng_end) & ~np.isnan(hi))
    for i in cand:
        if dayid[i] == done_day or i >= n - 1 or np.isnan(last_exit[i]) or last_exit[i] <= i:
            continue
        if not math.isnan(decide_at) and abs(hrs[i] - decide_at) > 1e-9:
            continue
        rng = hi[i] - lo[i]
        if not (min_range_pips * PIP <= rng <= max_range_pips * PIP):
            done_day = dayid[i]
            continue
        if adr is not None:
            if np.isnan(adr[i]) or adr[i] <= 0:
                continue
            ratio = rng / adr[i]
            if (not math.isnan(max_ratio) and ratio > max_ratio) or (not math.isnan(min_ratio) and ratio < min_ratio):
                done_day = dayid[i]
                continue
        level_ref = day_open[i] if confirm == "daily_open" else None
        side = 0
        if kz_hi[i] >= hi[i] + smin and (c[i] < hi[i] if confirm == "close_inside" else c[i] < level_ref):
            side = -1
        elif kz_lo[i] <= lo[i] - smin and (c[i] > lo[i] if confirm == "close_inside" else c[i] > level_ref):
            side = 1
        if side == 0:
            continue
        if engulf and i > 0 and not ((side < 0 and c[i] < o[i - 1]) or (side > 0 and c[i] > o[i - 1])):
            continue
        if pdir is not None:
            if np.isnan(pdir[i]) or pdir[i] == 0:
                continue
            want = pdir[i] if bias == "prev_day" else -pdir[i]
            if side != want:
                continue
        ref = c[i]
        sl = kz_hi[i] + buf if side < 0 else kz_lo[i] - buf
        risk = abs(sl - ref)
        if risk <= 0:
            continue
        if tp_mode == "rr":
            tp = ref - side * 0 + side * tp_val * risk
        else:
            tp = lo[i] if side < 0 else hi[i]
            if (tp - ref) * side <= 0:
                continue
            if tp_mode == "range_min_rr" and abs(tp - ref) < tp_val * risk:
                done_day = dayid[i]
                continue
        done_day = dayid[i]
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, exit_i=int(last_exit[i]), tag=tag))
    return orders


# ------------------------------------------------------------------ S19: liquidity sweep reversal (H1)
def liquidity_sweep(df, tz="America/New_York", killzones=((2, 5), (7, 10)), level_mode="equal", lookback=48,
                    eq_tol_pips=2.0, sweep_min_pips=3.0, sl_buffer_pips=2.0, tp_rr=2.0, max_hold=48, **kw):
    """RECONSTRUCTION (Backtrex rules): liquidity = equal highs/lows = two confirmed swing highs (lows) within
    eq_tol_pips of each other inside the last `lookback` bars (level_mode 'equal'), or simply the highest high /
    lowest low of the last `lookback` bars ('prior'). Sweep = bar exceeds the level by >= sweep_min_pips and
    closes back inside; only inside the killzones (ET); enter at next open against the sweep; SL beyond the sweep
    extreme + buffer; TP = tp_rr x risk; max_hold bars safety exit."""
    hrs, dayid, _ = _loc(df, tz)
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    n = len(df)
    inkz = np.zeros(n, dtype=bool)
    for a, b in killzones:
        inkz |= (hrs >= a) & (hrs < b)
    smin, buf = sweep_min_pips * PIP, sl_buffer_pips * PIP
    tol = eq_tol_pips * PIP
    # swing highs/lows confirmed two bars later (uses bars k-2..k+2 -> available from k+2)
    sh = np.zeros(n, dtype=bool)
    slw = np.zeros(n, dtype=bool)
    sh[2:-2] = (h[2:-2] > h[1:-3]) & (h[2:-2] > h[:-4]) & (h[2:-2] >= h[3:-1]) & (h[2:-2] >= h[4:])
    slw[2:-2] = (l[2:-2] < l[1:-3]) & (l[2:-2] < l[:-4]) & (l[2:-2] <= l[3:-1]) & (l[2:-2] <= l[4:])
    sh_idx = np.flatnonzero(sh)
    sl_idx = np.flatnonzero(slw)
    orders = []
    for i in np.flatnonzero(inkz):
        if i < lookback + 3 or i >= n - 1:
            continue
        side = 0
        if level_mode == "prior":
            lvl_hi = h[i - lookback:i].max()
            lvl_lo = l[i - lookback:i].min()
        else:
            # swing highs confirmed by i-1 (k+2 <= i-1) and within lookback
            ks = sh_idx[(sh_idx + 2 <= i - 1) & (sh_idx >= i - lookback)]
            lvl_hi = NAN
            if len(ks) >= 2:
                ph = np.sort(h[ks])
                d = np.diff(ph)
                if (d <= tol).any():
                    m = np.flatnonzero(d <= tol)[-1]
                    lvl_hi = max(ph[m], ph[m + 1])
            ks = sl_idx[(sl_idx + 2 <= i - 1) & (sl_idx >= i - lookback)]
            lvl_lo = NAN
            if len(ks) >= 2:
                pl = np.sort(l[ks])
                d = np.diff(pl)
                if (d <= tol).any():
                    m = np.flatnonzero(d <= tol)[0]
                    lvl_lo = min(pl[m], pl[m + 1])
        if not math.isnan(lvl_hi) and h[i] >= lvl_hi + smin and c[i] < lvl_hi:
            side = -1
        elif not math.isnan(lvl_lo) and l[i] <= lvl_lo - smin and c[i] > lvl_lo:
            side = 1
        if side == 0:
            continue
        ref = c[i]
        sl = h[i] + buf if side < 0 else l[i] - buf
        risk = abs(sl - ref)
        if risk <= 0:
            continue
        tp = ref + side * tp_rr * risk
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, max_hold=max_hold, tag="liq"))
    return orders


# ------------------------------------------------------------------ S08/S09: fair value gap entries
def fvg_killzone(df, tz="America/New_York", kz_start=7.0, kz_end=10.0, min_gap_pips=1.0, expiry_bars=8,
                 tp_rr=2.0, exit_hour=16.0, sl_mode="gap", sl_buffer_pips=1.0, require_sweep=False,
                 sweep_lookback=12, sweep_level="session", max_per_day=2, **kw):
    """RECONSTRUCTION of the ICT killzone FVG entry (S08) and Silver Bullet (S09, require_sweep=True).
    Bullish FVG at bars k-2,k-1,k: high[k-2] < low[k] - min_gap (and bar k-1 bullish). Decision at close of k:
    limit buy at low[k] (top of the gap) valid expiry_bars; SL = low[k-2] - buffer ('gap') or the sweep extreme
    ('sweep'); TP = tp_rr x risk; flat at exit_hour local. require_sweep: within the previous sweep_lookback bars a
    bar must have taken out the day's prior low (sweep_level 'session': running low of the day before that bar;
    'prev_day': previous NY-close day's low) and closed back above it (mirror for shorts)."""
    hrs, dayid, _ = _loc(df, tz)
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    n = len(df)
    inkz = (hrs >= kz_start) & (hrs < kz_end)
    last_exit = _last_lt(dayid, hrs, exit_hour)
    g = min_gap_pips * PIP
    buf = sl_buffer_pips * PIP
    bull = np.zeros(n, dtype=bool)
    bear = np.zeros(n, dtype=bool)
    bull[2:] = (h[:-2] < l[2:] - g) & (c[1:-1] > o[1:-1])
    bear[2:] = (l[:-2] > h[2:] + g) & (c[1:-1] < o[1:-1])
    if require_sweep:
        if sweep_level == "prev_day":
            lv = F.prev_day_levels(df, 22)
            ref_hi, ref_lo = lv["pd_high"].values, lv["pd_low"].values
        else:
            run_hi = pd.Series(h).groupby(dayid).cummax().shift(1).values
            run_lo = pd.Series(l).groupby(dayid).cummin().shift(1).values
            same = np.r_[False, dayid[1:] == dayid[:-1]]
            ref_hi = np.where(same, run_hi, np.nan)
            ref_lo = np.where(same, run_lo, np.nan)
        swept_lo = (l < ref_lo) & (c > ref_lo)   # took out the low, closed back above -> bullish
        swept_hi = (h > ref_hi) & (c < ref_hi)
        sw_lo_i = np.where(swept_lo, np.arange(n), -10**9)
        sw_hi_i = np.where(swept_hi, np.arange(n), -10**9)
        last_sw_lo = np.maximum.accumulate(sw_lo_i)
        last_sw_hi = np.maximum.accumulate(sw_hi_i)
        sweep_ext_lo = pd.Series(np.where(swept_lo, l, np.nan)).ffill().values
        sweep_ext_hi = pd.Series(np.where(swept_hi, h, np.nan)).ffill().values
    orders = []
    per_day = {}
    for i in np.flatnonzero(inkz & (bull | bear)):
        if i >= n - 1 or np.isnan(last_exit[i]) or last_exit[i] <= i:
            continue
        if per_day.get(dayid[i], 0) >= max_per_day:
            continue
        side = 1 if bull[i] else -1
        if require_sweep:
            if side > 0:
                if i - last_sw_lo[i] > sweep_lookback or last_sw_lo[i] < 0:
                    continue
            else:
                if i - last_sw_hi[i] > sweep_lookback or last_sw_hi[i] < 0:
                    continue
        if side > 0:
            px = l[i]
            sl = l[i - 2] - buf if sl_mode == "gap" else sweep_ext_lo[i] - buf
            if sl >= px:
                continue
            tp = px + tp_rr * (px - sl)
        else:
            px = h[i]
            sl = h[i - 2] + buf if sl_mode == "gap" else sweep_ext_hi[i] + buf
            if sl <= px:
                continue
            tp = px - tp_rr * (sl - px)
        per_day[dayid[i]] = per_day.get(dayid[i], 0) + 1
        orders.append(Order(i=int(i), side=side, entry_type="limit", entry_price=px, sl=sl, tp=tp,
                            expiry_bars=expiry_bars, exit_i=int(last_exit[i]), tag="fvg"))
    return orders


# ------------------------------------------------------------------ S05: NY-open reversal of the London move
def ny_open_reversal(df, min_london_move_pips=40.0, win_start=8.5, win_end=10.0, exit_hour=11.0, sl_buffer_pips=5.0,
                     tp_mode="half", require_pd_level=False, **kw):
    """RECONSTRUCTION: London move = close at the NY window start (08:30 ET) minus the 07:00 London-local
    reference close. If |move| >= min pips, the first M15 bar in [win_start, win_end) ET that makes a new
    extreme of the London move and closes in the opposite third of its range (rejection) -> enter against London
    at next open. SL beyond the window extreme + buffer; TP 'half' = 50 % retrace of the London range,
    'open' = the 07:00 London price; flat at exit_hour ET (11:00 ET = 16:00 London fix).
    require_pd_level: the extreme must be beyond the previous day's high/low."""
    hrs, dayid, loc = _loc(df, "America/New_York")
    lhrs, ldayid, _ = _loc(df, "Europe/London")
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    n = len(df)
    # reference price: close of the last bar before 07:00 London each London day
    ref_idx = _last_lt(ldayid, lhrs, 7.0)
    ref_px = np.where(np.isnan(ref_idx), np.nan, c[np.nan_to_num(ref_idx, nan=0).astype(int)])
    # running high/low since 07:00 London (London day)
    lon_hi, lon_lo, _, _ = _run_window(df, ldayid, lhrs, 7.0, 24.0)
    last_exit = _last_lt(dayid, hrs, exit_hour)
    inwin = (hrs >= win_start) & (hrs < win_end)
    lv = F.prev_day_levels(df, 22) if require_pd_level else None
    buf = sl_buffer_pips * PIP
    orders = []
    done = -1
    for i in np.flatnonzero(inwin):
        if dayid[i] == done or i >= n - 1 or np.isnan(ref_px[i]) or np.isnan(last_exit[i]) or last_exit[i] <= i:
            continue
        move = c[i] - ref_px[i]
        if abs(move) < min_london_move_pips * PIP or i == 0:
            continue
        rng_bar = h[i] - l[i]
        if rng_bar <= 0:
            continue
        pos = (c[i] - l[i]) / rng_bar
        if move > 0 and h[i] >= lon_hi[i - 1] and pos < 1 / 3:
            side = -1
        elif move < 0 and l[i] <= lon_lo[i - 1] and pos > 2 / 3:
            side = 1
        else:
            continue
        if require_pd_level:
            if side < 0 and not h[i] > lv["pd_high"].iat[i]:
                continue
            if side > 0 and not l[i] < lv["pd_low"].iat[i]:
                continue
        ext = lon_hi[i] if side < 0 else lon_lo[i]
        sl = ext + buf if side < 0 else ext - buf
        if tp_mode == "half":
            tp = (ext + ref_px[i]) / 2
        else:
            tp = ref_px[i]
        if (tp - c[i]) * side <= 0 or (sl - c[i]) * side >= 0:
            continue
        done = dayid[i]
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, exit_i=int(last_exit[i]), tag="nyrev"))
    return orders


# ------------------------------------------------------------------ S06: London-close reversal scalp
def london_close_reversal(df, win_start=11.0, win_end=12.5, exit_hour=13.0, sl_pips=12.0, tp_pips=10.0,
                          sl_mode="pips", sl_buffer_pips=5.0, **kw):
    """RECONSTRUCTION: between win_start and win_end ET, a bar that pushes to a new day high (running high since
    the NY-close day start) but fails to close above the PREVIOUS day-high (close < prior running high) -> short
    at next open (mirror for lows); only if the day's direction (close vs day open) agrees with the push.
    SL = sl_pips or the extreme + buffer; TP = tp_pips; flat at exit_hour ET. One trade per day."""
    hrs, dayid, _ = _loc(df, "America/New_York", offset_h=17.0)  # NY-close day starting 17:00 ET
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    n = len(df)
    run_hi = pd.Series(h).groupby(dayid).cummax().values
    run_lo = pd.Series(l).groupby(dayid).cummin().values
    day_open = pd.Series(o).groupby(dayid).transform("first").values
    wh = (win_start - 17.0) % 24
    we = (win_end - 17.0) % 24
    ex = (exit_hour - 17.0) % 24
    last_exit = _last_lt(dayid, hrs, ex)
    inwin = (hrs >= wh) & (hrs < we)
    orders = []
    done = -1
    for i in np.flatnonzero(inwin):
        if dayid[i] == done or i == 0 or i >= n - 1 or dayid[i - 1] != dayid[i] or np.isnan(last_exit[i]) or last_exit[i] <= i:
            continue
        side = 0
        if h[i] > run_hi[i - 1] and c[i] < run_hi[i - 1] and c[i] > day_open[i]:
            side = -1
        elif l[i] < run_lo[i - 1] and c[i] > run_lo[i - 1] and c[i] < day_open[i]:
            side = 1
        if side == 0:
            continue
        ref = c[i]
        if sl_mode == "pips":
            sl = ref - side * sl_pips * PIP
        else:
            sl = (h[i] + sl_buffer_pips * PIP) if side < 0 else (l[i] - sl_buffer_pips * PIP)
        tp = ref + side * tp_pips * PIP
        done = dayid[i]
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, exit_i=int(last_exit[i]), tag="lcr"))
    return orders


# ------------------------------------------------------------------ S11: Asian range fade
def asian_range_fade(df, win_start=0.0, win_end=6.0, min_range_pips=15.0, max_range_pips=40.0, sl_pips=10.0,
                     rsi_len=14, rsi_ob=70.0, rsi_os=30.0, use_rsi=True, max_per_day=2, **kw):
    """S11: range measured from 22:00 UTC (running). Between win_start and win_end UTC, when the bar touches the
    running range high (high >= previous running high) with RSI(rsi_len) > rsi_ob, short at next open; SL =
    range high + sl_pips; TP = range midpoint; flat at win_end UTC. Mirror for the low."""
    hrs, dayid, _ = _loc(df, "UTC", offset_h=22.0)
    o, h, l, c = (df[k].values for k in ("open", "high", "low", "close"))
    n = len(df)
    run_hi = pd.Series(h).groupby(dayid).cummax().values
    run_lo = pd.Series(l).groupby(dayid).cummin().values
    r = F.rsi(df["close"], rsi_len).values
    ws, we = (win_start - 22.0) % 24, (win_end - 22.0) % 24
    last_exit = _last_lt(dayid, hrs, we)
    inwin = (hrs >= ws) & (hrs < we)
    orders = []
    per_day = {}
    for i in np.flatnonzero(inwin):
        if i == 0 or i >= n - 1 or dayid[i - 1] != dayid[i] or np.isnan(last_exit[i]) or last_exit[i] <= i:
            continue
        if per_day.get(dayid[i], 0) >= max_per_day:
            continue
        rng = run_hi[i - 1] - run_lo[i - 1]
        if not (min_range_pips * PIP <= rng <= max_range_pips * PIP):
            continue
        mid = (run_hi[i - 1] + run_lo[i - 1]) / 2
        side = 0
        if h[i] >= run_hi[i - 1] and (not use_rsi or r[i] > rsi_ob):
            side = -1
        elif l[i] <= run_lo[i - 1] and (not use_rsi or r[i] < rsi_os):
            side = 1
        if side == 0 or (mid - c[i]) * side <= 0:
            continue
        sl = run_hi[i] + sl_pips * PIP if side < 0 else run_lo[i] - sl_pips * PIP
        per_day[dayid[i]] = per_day.get(dayid[i], 0) + 1
        orders.append(Order(i=int(i), side=side, sl=sl, tp=mid, exit_i=int(last_exit[i]), tag="afade"))
    return orders


# ------------------------------------------------------------------ S17: RSI range trading with ET time filter
def rsi_time_filter(df, rsi_len=14, os_=30.0, ob=70.0, allowed=((14, 24), (0, 6)), use_filter=True, sl_atr=2.0,
                    tp_rr=NAN, atr_n=14, max_hold=96, exit_on_opposite=True, **kw):
    """S17 (DailyFX): long when RSI crosses UP through os_, short when it crosses DOWN through ob; entries only
    when the ET hour is inside `allowed` (default 14:00-06:00 ET). Exit at the opposite signal (precomputed), the
    ATR stop, an optional tp_rr x risk target, or max_hold bars."""
    hrs, dayid, _ = _loc(df, "America/New_York")
    c = df["close"].values
    r = F.rsi(df["close"], rsi_len).values
    a = F.atr(df, atr_n).values
    n = len(df)
    up = np.zeros(n, dtype=bool)
    dn = np.zeros(n, dtype=bool)
    up[1:] = (r[1:] > os_) & (r[:-1] <= os_)
    dn[1:] = (r[1:] < ob) & (r[:-1] >= ob)
    ok = np.ones(n, dtype=bool)
    if use_filter:
        ok = np.zeros(n, dtype=bool)
        for s, e in allowed:
            ok |= (hrs >= s) & (hrs < e)
    up_idx, dn_idx = np.flatnonzero(up), np.flatnonzero(dn)
    orders = []
    for i in np.flatnonzero((up | dn) & ok):
        if np.isnan(a[i]) or i >= n - 1:
            continue
        side = 1 if up[i] else -1
        opp = dn_idx if side > 0 else up_idx
        exit_i = -1
        if exit_on_opposite:
            k = np.searchsorted(opp, i + 1)
            if k < len(opp):
                exit_i = int(opp[k])
        d_sl = sl_atr * a[i]
        sl = c[i] - side * d_sl
        tp = c[i] + side * tp_rr * d_sl if not math.isnan(tp_rr) else NAN
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, max_hold=max_hold, exit_i=exit_i, tag="rsitf"))
    return orders


# ------------------------------------------------------------------ S14/S18/C01/Q04: local-time window holds
def window_hold(df, tz="Europe/London", entry_hour=13.0, exit_hour=16.0, side=1, sl_adr=NAN, sl_pips=NAN,
                dows=(0, 1, 2, 3, 4), exit_day_offset=0, adr_len=14, tag="win", **kw):
    """Enter at the open of the first bar of the local day with hour >= entry_hour (weekday in dows, local day
    of that bar), exit at the close of the last bar with hour < exit_hour on the day + exit_day_offset.
    Optional stop at sl_adr x ADR(adr_len) or sl_pips; no target (time exit)."""
    hrs, dayid, loc = _loc(df, tz)
    c = df["close"].values
    n = len(df)
    first_ge = _first_ge(dayid, hrs, entry_hour)
    last_lt = _last_lt(dayid, hrs, exit_hour)
    dow = loc.dayofweek.values
    # map dayid -> exit index
    ex_map = {}
    for d_, j in zip(dayid, last_lt):
        if not np.isnan(j):
            ex_map[d_] = int(j)
    adr = _daily_series(df, "adr", adr_len) if not math.isnan(sl_adr) else None
    orders = []
    seen = set()
    for i in range(1, n):
        e = first_ge[i]
        if np.isnan(e) or int(e) != i or dayid[i] in seen or dow[i] not in dows:
            continue
        seen.add(dayid[i])
        exit_i = ex_map.get(dayid[i] + exit_day_offset)
        if exit_i is None or exit_i < i:
            continue
        ref = c[i - 1]
        sl = NAN
        if adr is not None and not np.isnan(adr[i - 1]):
            sl = ref - side * sl_adr * adr[i - 1]
        elif not math.isnan(sl_pips):
            sl = ref - side * sl_pips * PIP
        orders.append(Order(i=i - 1, side=side, sl=sl, exit_i=exit_i, tag=tag))
    return orders


def local_hours_pair(df, sl_adr=NAN, short_start=8.0, short_end=13.0, long_start=13.0, long_end=21.0, legs="both", **kw):
    """S18 practitioner variant: short EUR/USD short_start-short_end London, long long_start-long_end London,
    optional 0.5 x ADR stop on each leg. legs: 'both' | 'short' | 'long' (the engine cannot open the long leg on the
    bar that closes the short leg, so the legs are evaluated separately in the experiments)."""
    out = []
    if legs in ("both", "short"):
        out += window_hold(df, "Europe/London", short_start, short_end, -1, sl_adr=sl_adr, tag="s18s")
    if legs in ("both", "long"):
        out += window_hold(df, "Europe/London", long_start, long_end, 1, sl_adr=sl_adr, tag="s18l")
    return out


def fix_pattern_pair(df, sl_adr=NAN, pre_start=13.0, post_end=20.0, legs="both", **kw):
    """S14 practitioner variant: short pre_start-16:00 London (into the WM/R fix), long 16:00-post_end London."""
    out = []
    if legs in ("both", "pre"):
        out += window_hold(df, "Europe/London", pre_start, 16.0, -1, sl_adr=sl_adr, tag="s14pre")
    if legs in ("both", "post"):
        out += window_hold(df, "Europe/London", 16.0, post_end, 1, sl_adr=sl_adr, tag="s14post")
    return out


def dow_pair(df, mode="fxday", legs="both", **kw):
    """C01: short Monday, long Friday. mode 'fxday': NY-close days (Sun 17:00 -> Mon 17:00 ET; Thu 17:00 -> Fri 17:00);
    'utc': calendar UTC days (Monday 00:00-24:00, Friday 00:00-24:00)."""
    out = []
    if mode == "fxday":
        if legs in ("both", "mon"):
            out += window_hold(df, "America/New_York", 17.0, 17.0, -1, dows=(6,), exit_day_offset=1, tag="c01mon")
        if legs in ("both", "fri"):
            out += window_hold(df, "America/New_York", 17.0, 17.0, 1, dows=(3,), exit_day_offset=1, tag="c01fri")
    else:
        if legs in ("both", "mon"):
            out += window_hold(df, "UTC", 0.0, 24.0, -1, dows=(0,), tag="c01mon")
        if legs in ("both", "fri"):
            out += window_hold(df, "UTC", 0.0, 24.0, 1, dows=(4,), tag="c01fri")
    return out


# ------------------------------------------------------------------ C05: Friday position squaring
def friday_squaring(df, min_move_pct=1.0, entry_hour=13.0, sl_adr=0.5, **kw):
    """C05: at Friday entry_hour London, if the move since the week's open (first bar after the weekend gap)
    is >= min_move_pct, fade it until the Friday close (last bar of the week); SL = sl_adr x ADR."""
    hrs, dayid, loc = _loc(df, "Europe/London")
    o, c = df["open"].values, df["close"].values
    n = len(df)
    gap = np.r_[True, (df.index[1:] - df.index[:-1]) > pd.Timedelta(hours=12)]
    week_open = pd.Series(np.where(gap, o, np.nan)).ffill().values
    first_ge = _first_ge(dayid, hrs, entry_hour)
    dow = loc.dayofweek.values
    adr = _daily_series(df, "adr", 14)
    gap_idx = np.flatnonzero(gap)
    orders = []
    for i in np.flatnonzero((dow == 4) & (first_ge == np.arange(n))):
        if i == 0 or i >= n - 1 or np.isnan(week_open[i]) or np.isnan(adr[i]):
            continue
        move = c[i - 1] / week_open[i] - 1
        if abs(move) < min_move_pct / 100:
            continue
        k = np.searchsorted(gap_idx, i + 1)
        exit_i = int(gap_idx[k]) - 1 if k < len(gap_idx) else n - 1
        if exit_i - i > 60:  # not a Friday close within the day (data hole)
            continue
        side = -1 if move > 0 else 1
        sl = c[i - 1] - side * sl_adr * adr[i]
        orders.append(Order(i=i - 1, side=side, sl=sl, exit_i=exit_i, tag="c05"))
    return orders


# ------------------------------------------------------------------ S15: month-end fix (price-only variant)
def monthend_fix_follow(df, signal_start=13.0, signal_end=15.0, exit_hour=16.0, sl_adr=0.4, mode="follow", **kw):
    """S15 price-only variant (the equity-rebalancing signal needs index data we do not have): on the last London
    business day of the month, direction = sign of the signal_start->signal_end London move ('follow') or its
    opposite ('fade'); hold from signal_end to exit_hour (the 16:00 fix); SL = sl_adr x ADR."""
    hrs, dayid, loc = _loc(df, "Europe/London")
    c = df["close"].values
    n = len(df)
    first_ge = _first_ge(dayid, hrs, signal_end)
    sig_ref = _last_lt(dayid, hrs, signal_start)
    last_exit = _last_lt(dayid, hrs, exit_hour)
    month = (loc.year * 12 + loc.month).values
    nxt_month = pd.Series(month).groupby(dayid).transform("first")
    # last trading day of month = day whose next day id (in data) has a different month
    days = pd.DataFrame({"d": dayid, "m": month}).drop_duplicates("d")
    days["next_m"] = days["m"].shift(-1)
    last_days = set(days.loc[days["m"] != days["next_m"], "d"])
    adr = _daily_series(df, "adr", 14)
    orders = []
    for i in np.flatnonzero(first_ge == np.arange(n)):
        if dayid[i] not in last_days or i == 0 or np.isnan(sig_ref[i]) or np.isnan(last_exit[i]) or np.isnan(adr[i]):
            continue
        move = c[i - 1] - c[int(sig_ref[i])]
        if move == 0:
            continue
        side = int(np.sign(move)) * (1 if mode == "follow" else -1)
        exit_i = int(last_exit[i])
        if exit_i <= i - 1:
            continue
        sl = c[i - 1] - side * sl_adr * adr[i]
        orders.append(Order(i=i - 1, side=side, sl=sl, exit_i=exit_i, tag="s15"))
    return orders


# ------------------------------------------------------------------ S16: weekend gap fill (H1)
def weekend_gap(df, min_gap_pips=10.0, max_gap_atr_ratio=0.5, sl_mode="gap", sl_atr=0.5, time_stop="wed8", **kw):
    """S16: at the first bar after the weekend (gap > 12h in the index), gap = open - Friday close. If |gap| >=
    min_gap_pips and |gap| <= max_gap_atr_ratio x ATR(14, NY-close days): trade toward Friday's close at the next
    bar's open (the engine fills market orders at i+1), TP = Friday close, SL = 1 x gap beyond the open ('gap')
    or sl_atr x ATR ('atr'); time stop Wednesday 08:00 London ('wed8') or Monday close ('mon')."""
    hrs, dayid, loc = _loc(df, "Europe/London")
    o, c = df["open"].values, df["close"].values
    n = len(df)
    gap = np.r_[False, (df.index[1:] - df.index[:-1]) > pd.Timedelta(hours=12)]
    atr_d = _daily_series(df, "atr", 14)
    dow = loc.dayofweek.values
    wed8 = np.flatnonzero((dow == 2) & (hrs >= 8))
    orders = []
    for i in np.flatnonzero(gap):
        if i >= n - 1 or np.isnan(atr_d[i]):
            continue
        g = o[i] - c[i - 1]
        if abs(g) < min_gap_pips * PIP or abs(g) > max_gap_atr_ratio * atr_d[i]:
            continue
        side = -1 if g > 0 else 1
        tp = c[i - 1]
        if sl_mode == "gap":
            sl = o[i] + side * -1 * abs(g)  # 1x gap beyond the open, away from the target
        else:
            sl = o[i] - side * sl_atr * atr_d[i]
        if time_stop == "wed8":
            k = np.searchsorted(wed8, i + 1)
            exit_i = int(wed8[k]) - 1 if k < len(wed8) else n - 1
        else:
            exit_i = min(n - 1, i + 23)
        if (tp - c[i]) * side <= 0:
            continue  # already filled by the close of the first bar
        orders.append(Order(i=int(i), side=side, sl=sl, tp=tp, exit_i=exit_i, tag="gap"))
    return orders


# ------------------------------------------------------------------ C03/C04/C06: daily-frame calendar strategies
def month_seasonal(df_daily, long_months=(12,), short_months=(5,), **kw):
    """C03 on daily bars: long from the close of the last trading day of the month before each long month to the
    close of the last trading day of that month; short likewise for short_months."""
    m = df_daily.index.month.values
    y = df_daily.index.year.values
    ym = y * 12 + m
    last_of_month = np.r_[ym[1:] != ym[:-1], True]
    idx = np.flatnonzero(last_of_month)
    orders = []
    for k in range(len(idx) - 1):
        i, j = idx[k], idx[k + 1]
        nm = m[j]
        if nm in long_months:
            orders.append(Order(i=int(i), side=1, exit_i=int(j), tag="c03L"))
        elif nm in short_months:
            orders.append(Order(i=int(i), side=-1, exit_i=int(j), tag="c03S"))
    return orders


def turn_of_month(df_daily, entry_offset=-1, exit_offset=1, side=1, **kw):
    """C04 on daily bars: T = last trading day of the month; enter at the close of T+entry_offset, exit at the close
    of T+exit_offset (both in trading days)."""
    m = df_daily.index.month.values
    y = df_daily.index.year.values
    ym = y * 12 + m
    idx = np.flatnonzero(np.r_[ym[1:] != ym[:-1], False])
    n = len(df_daily)
    orders = []
    for t in idx:
        i, j = t + entry_offset, t + exit_offset
        if i < 0 or j >= n or j <= i:
            continue
        orders.append(Order(i=int(i), side=side, exit_i=int(j), tag="c04"))
    return orders


def _holiday_windows(index):
    """(start_date, end_date) pairs for US Thanksgiving week (Mon-Fri) and Dec 24 - Jan 2."""
    out = []
    for yr in sorted(set(index.year)):
        nov = pd.date_range(f"{yr}-11-01", f"{yr}-11-30")
        thu = [d for d in nov if d.dayofweek == 3][3]
        out.append(("tg", thu - pd.Timedelta(days=3), thu + pd.Timedelta(days=1)))
        out.append(("xm", pd.Timestamp(f"{yr}-12-24"), pd.Timestamp(f"{yr + 1}-01-02")))
    return out


def holiday_week(df_daily, which="both", trend_days=10, side_mode="continue", **kw):
    """C06 on daily bars: over each holiday window (Thanksgiving week, Dec 24-Jan 2) hold a position in the
    direction of the prior trend_days return ('continue') or against it ('fade'); enter at the close before the
    window, exit at the close of the last day in the window."""
    # NY-close daily bars are labelled by their start (22:00 UTC the evening before): session date = start + 2h
    dates = (df_daily.index.tz_convert("UTC").tz_localize(None) + pd.Timedelta(hours=2)).normalize()
    c = df_daily["close"].values
    n = len(df_daily)
    orders = []
    for kind, a, b in _holiday_windows(dates):
        if which != "both" and kind != which:
            continue
        i0 = np.searchsorted(dates.values, np.datetime64(a))
        i1 = np.searchsorted(dates.values, np.datetime64(b), side="right") - 1
        i = i0 - 1
        if i < trend_days or i1 <= i or i1 >= n:
            continue
        tr = np.sign(c[i] - c[i - trend_days])
        if tr == 0:
            continue
        side = int(tr) if side_mode == "continue" else -int(tr)
        orders.append(Order(i=int(i), side=side, exit_i=int(i1), tag=f"c06{kind}"))
    return orders


REGISTRY.update({
    "range_breakout": range_breakout,
    "london_range_fade_second": london_range_fade_second,
    "asian_sweep_reverse": asian_sweep_reverse,
    "liquidity_sweep": liquidity_sweep,
    "fvg_killzone": fvg_killzone,
    "ny_open_reversal": ny_open_reversal,
    "london_close_reversal": london_close_reversal,
    "asian_range_fade": asian_range_fade,
    "rsi_time_filter": rsi_time_filter,
    "window_hold": window_hold,
    "local_hours_pair": local_hours_pair,
    "fix_pattern_pair": fix_pattern_pair,
    "dow_pair": dow_pair,
    "friday_squaring": friday_squaring,
    "monthend_fix_follow": monthend_fix_follow,
    "weekend_gap": weekend_gap,
    "month_seasonal": month_seasonal,
    "turn_of_month": turn_of_month,
    "holiday_week": holiday_week,
})
