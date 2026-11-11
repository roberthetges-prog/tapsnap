"""Short, sharp daily brief and weekly forecast/trend for EUR/USD.

  python -m eurusd.cli brief     daily: exposure target + action, book, VaR, limits, next events (<= 12 lines)
  python -m eurusd.cli weekly    weekly: trend state, positioning/macro tilt, expected range (vol cone), levels, events

The weekly "forecast" is honest: a directional tilt from the live exposure plus a volatility cone from the HAR
forecast. The tilt's historical hit rate is ~52-55 % of weeks; the cone is where most of the edge-free movement lies.
"""
from __future__ import annotations

import math
import numpy as np
import pandas as pd

from . import features as F
from .exposure import compute, plan
from .live_data import load_h1_live
from .risk import RiskEngine

PIP = 1e-4


def _engine(refresh: bool):
    h1 = load_h1_live(refresh=refresh)
    return RiskEngine(h1), h1


def daily_brief(refresh: bool = True) -> str:
    from .refresh import refresh_macro, log_signal
    status = refresh_macro() if refresh else ["macro refresh skipped"]
    exp, D = compute(refresh=refresh)
    eng, h1 = _engine(False)
    vol = eng.vol_forecast()
    cur = sum(p.lots * p.side for p in eng.book.positions if p.strategy == "macro_exposure")
    unit_lots = eng.cfg.target_annual_vol / math.sqrt(252) * (eng.book.equity + eng.mtm()) / vol["har_daily_vol"] / 100_000
    pl = plan(exp, eng.book.equity + eng.mtm(), eng.cfg.target_annual_vol, vol["har_daily_vol"], current_units=cur / unit_lots if unit_lots else 0.0)
    st = eng.limits_status()
    ve = eng.var_es()
    ev = eng.events_ahead(48)
    src = h1["source"].iloc[-1] if "source" in h1 else "histdata"
    L = [f"EUR/USD daily brief | {exp.asof_session_close[:10]} close {exp.price:.4f} | data to {h1.index[-1]:%d %b %H:%M} UTC ({src})"]
    L.append(f"Target: {pl['side'].upper()} {abs(exp.target_units):.2f} units = {pl['target_lots']} lots | stop {pl['stop']} ({exp.stop_distance_pips:.0f} pips) | action: {pl['action'].upper()}")
    L.append(f"Drivers: positioning z {exp.d_cot_z52:+.2f} -> {exp.d_units:+.2f}; weak-signal score {exp.c_score:+.3f} vs {exp.c_threshold:.3f} -> {exp.c_units:+.2f} "
             f"(top: " + ", ".join(f"{k} {v:+.2f}" for k, v in list(exp.top_contributions.items())[:3]) + ")")
    if eng.book.positions:
        p = eng.book.positions[0]
        L.append(f"Book: {'short' if p.side < 0 else 'long'} {p.lots} lots from {p.entry:.4f} | P&L {st['mtm']:+.0f} USD | equity {st['equity_with_mtm']:,.0f} | stop {abs(eng.price - p.stop) / PIP:.0f} pips away")
    else:
        L.append(f"Book: flat | equity {st['equity']:,.0f}")
    L.append(f"Risk: 1d VaR99 {ve['parametric']['var']:.0f} USD (hist {ve.get('historical', {}).get('var', 0):.0f}) | vol {vol['har_annual_vol']:.1%} ann, ATR14 {vol['atr14_pips']:.0f} pips")
    breached = [k for k, v in st["checks"].items() if v["breached"]]
    L.append("Limits: " + ("ALL CLEAR" if not breached else "BREACHED " + ", ".join(breached)) + (" | TRADING HALTED" if st["trading_halted"] else ""))
    if not ev.empty:
        nxt = ev.drop_duplicates("time").head(3)
        L.append("Events 48h: " + "; ".join(f"{r.event} in {r.hours_ahead:.0f}h" for r in nxt.itertuples()))
    else:
        L.append("Events 48h: none high-impact")
    bad = [m for m in status if "FAILED" in m or "skipped" in m]
    L.append("Data: " + (status[0] if status and status[0].startswith("COT") else "COT not refreshed") + (" | WARN " + "; ".join(bad) if bad else ""))
    try:
        log_signal(exp, pl, {"var99": round(ve["parametric"]["var"], 2), "equity": round(st["equity_with_mtm"], 2), "halted": st["trading_halted"]})
    except Exception as e:
        L.append(f"(signal log not written: {e})")
    return "\n".join(L)


def weekly_outlook(refresh: bool = True) -> str:
    from .refresh import refresh_macro
    if refresh:
        refresh_macro()
    exp, D = compute(refresh=refresh)
    eng, h1 = _engine(False)
    vol = eng.vol_forecast()
    d = eng.daily
    c = d["close"]
    px = exp.price
    atr = float(F.atr(d, 20).iloc[-1])
    last = D.iloc[-1]
    # trend state
    r1, r3, r12 = last["ret_21d"], last["ret_63d"], last["ret_252d"]
    sma50, sma200 = last["dist_sma50_atr"], last["dist_sma200_atr"]
    adx = last["adx14"]
    trend = "UP" if (sma50 > 0 and sma200 > 0) else ("DOWN" if (sma50 < 0 and sma200 < 0) else "MIXED")
    strength = "strong" if adx >= 25 else ("moderate" if adx >= 18 else "weak/range")
    # weekly cone from HAR daily vol
    wk_vol_bp = vol["har_daily_vol"] * math.sqrt(5) * 1e4
    cone1 = px * wk_vol_bp / 1e4
    tilt_bp = 0.58 * 5 * exp.target_units          # OOS mean bp/session/unit x 5 sessions x units
    p_up = 0.5 + 0.5 * math.erf((tilt_bp / wk_vol_bp) / math.sqrt(2)) if wk_vol_bp > 0 else 0.5
    # levels
    wk = d.iloc[-5:]
    prev_wk_hi, prev_wk_lo = float(wk["high"].max()), float(wk["low"].min())
    piv = (prev_wk_hi + prev_wk_lo + float(wk["close"].iloc[-1])) / 3
    rv_pct = float((D["rv_21d_bp"].rank(pct=True)).iloc[-1])
    ev = eng.events_ahead(24 * 7).drop_duplicates("time")
    key = ev[ev.event.str.contains("FOMC|ECB|Non-Farm|Employment Situation|CPI|PPI|GDP|PCE|Retail", case=False, regex=True)].head(6)
    L = [f"EUR/USD weekly outlook | as of {exp.asof_session_close[:10]} | {px:.4f}"]
    L.append(f"Trend: {trend} ({strength}, ADX {adx:.0f}) | 1m {r1:+.0f} bp, 3m {r3:+.0f} bp, 12m {r12:+.0f} bp | vs SMA50 {sma50:+.1f} ATR, SMA200 {sma200:+.1f} ATR")
    L.append(f"Regime: 21d vol {last['rv_21d_bp']:.0f} bp/day ({rv_pct:.0%} pct of history) | HAR week vol {wk_vol_bp:.0f} bp | ATR20 {atr / PIP:.0f} pips")
    L.append(f"Macro: EA-US 2y spread {last['spread2y']:+.2f} ({last['d_spread2y_20']:+.2f} over 20d) | fair-value residual z {last['fv_resid_z']:+.2f} | USD factor 20d {last['usd_factor_20']:+.0f} bp | VIX {last['vix']:.0f}")
    L.append(f"Positioning: CFTC non-commercial z {last['cot_z52']:+.2f} (4w change {last['cot_d4']:+.3f} of OI)")
    L.append(f"Forecast (tilt + cone): {'DOWN' if exp.target_units < 0 else ('UP' if exp.target_units > 0 else 'FLAT')} tilt {tilt_bp:+.0f} bp, P(up week) {p_up:.0%} | 1-sigma week range {px - cone1:.4f} - {px + cone1:.4f} | 2-sigma {px - 2 * cone1:.4f} - {px + 2 * cone1:.4f}")
    L.append(f"Levels: last week H {prev_wk_hi:.4f} / L {prev_wk_lo:.4f} | weekly pivot {piv:.4f} | stop for the live exposure {exp.price + (exp.stop_distance_pips * PIP if exp.target_units < 0 else -exp.stop_distance_pips * PIP):.4f}")
    L.append(f"Exposure: {'SHORT' if exp.target_units < 0 else ('LONG' if exp.target_units > 0 else 'FLAT')} {abs(exp.target_units):.2f} units (positioning {exp.d_units:+.2f}, weak-signal {exp.c_units:+.2f})")
    L.append("Events this week: " + ("; ".join(f"{r.event} {r.time:%a %H:%M}Z" for r in key.itertuples()) if not key.empty else "none high-impact"))
    L.append("Honesty note: the tilt's historical weekly hit rate is ~52-55 %; the cone is where most movement lies.")
    return "\n".join(L)
