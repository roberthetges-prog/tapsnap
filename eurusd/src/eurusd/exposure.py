"""Live daily EUR/USD exposure: the round-2 survivor.

Two walk-forward-validated daily streams, combined equal-weight (the EW rule of arms/meta.py):
  C  weak-signal combination (arms/weak_signals.py, method 'tstat', mapping 'sign'): 14 economic signals
     oriented by prior, weighted by their full-history t-stats, sign position when |score| > median,
     vol-scaled.
  D  positioning trend (arms/regime_trend.py 'cot_regimeK3', identical to the unconditional rule since
     2014): sign(cot_z52) x vol scale, cap 1.5.
Walk-forward record of the EW combination (net of 1.2 pips per unit turnover):
  2010-2026 Sharpe 0.56 (t 2.3) | 2016-2026 Sharpe 0.64 (t 2.1) | 2023-2026 Sharpe 0.36 (t 0.7)
  deflated-Sharpe p = 0.28 for 15 variants: NOT significant after multiple-testing correction.

The target is a continuous position in "units" (1 unit = the vol-target notional of the risk engine).
It is rebalanced only when the target's sign flips or it moves by more than `rebalance_band` units,
so the 1.2-pip cost is paid a few times a year, as in the walk-forward test. A disaster stop of
`stop_atr` x ATR20 sits under every open exposure.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import pandas as pd

from . import features as F
from .arms import weak_signals as WS
from .featstore import build_daily
from .live_data import load_h1_live

ROOT = Path(__file__).resolve().parents[2]
VOL_CAP = 1.5
REBALANCE_BAND = 0.5
STOP_ATR = 2.0


@dataclass
class Exposure:
    asof_session_close: str
    target_units: float          # combined target in units (negative = short EUR/USD)
    c_units: float
    d_units: float
    c_score: float
    c_threshold: float
    c_vol_scale: float
    d_cot_z52: float
    d_vol_scale: float
    top_contributions: dict      # signal -> weighted contribution to the C score
    price: float
    atr20_pips: float
    stop_distance_pips: float
    rebalance_band: float


def _daily_frame(refresh: bool = True) -> pd.DataFrame:
    h1 = load_h1_live(refresh=refresh)
    D = build_daily(save=False, h1=h1)
    # only COMPLETED sessions: the last row is partial if its close lies beyond the last bar's end
    last_bar_end = h1.index[-1] + pd.Timedelta(hours=1)
    return D[D["close_time"] <= last_bar_end]


def compute(refresh: bool = True) -> tuple[Exposure, pd.DataFrame]:
    D = _daily_frame(refresh)
    S = WS.build_raw_signals(D)
    signals = list(WS.SIGNALS)
    S = S.reindex(columns=signals)
    frame = pd.concat([S, D[["fwd_1d", "rv_21d_bp"]]], axis=1)
    # --- C: fit on all rows whose label is known, predict the latest row
    hist = frame[frame["fwd_1d"].notna()]
    fit, predict = WS.make_fit_predict("tstat", "sign", signals)
    m = fit(hist)
    last = frame.iloc[[-1]]
    pos_c = float(predict(m, last).iloc[0])
    Z = WS._scaler_apply(last[signals], m["st"])
    contrib = {k: float(v) for k, v in (Z.iloc[0] * m["w"]).sort_values(key=np.abs, ascending=False).items()}
    score = float(sum(contrib.values()))
    rv_last = float(last["rv_21d_bp"].iloc[0])
    c_scale = min(1.0, m["target_vol"] / rv_last) if rv_last > 0 else 0.0
    # --- D: positioning trend, vol-scaled
    vol_target = float(hist["rv_21d_bp"].median())
    cot_z = float(D["cot_z52"].iloc[-1])
    d_scale = float(np.clip(vol_target / rv_last, 0, VOL_CAP)) if rv_last > 0 else 0.0
    pos_d = float(np.sign(cot_z) * d_scale) if not math.isnan(cot_z) else 0.0
    target = 0.5 * (pos_c + pos_d)
    h1 = load_h1_live(refresh=False)
    daily = F.daily_ohlc(h1[["open", "high", "low", "close"]], 22)
    atr = float(F.atr(daily, 20).iloc[-1]) / 1e-4
    exp = Exposure(asof_session_close=str(D["close_time"].iloc[-1]), target_units=round(target, 3), c_units=round(pos_c, 3), d_units=round(pos_d, 3),
                   c_score=round(score, 4), c_threshold=round(m["thr"]["med"], 4), c_vol_scale=round(c_scale, 3), d_cot_z52=round(cot_z, 2),
                   d_vol_scale=round(d_scale, 3), top_contributions={k: round(v, 4) for k, v in list(contrib.items())[:6]},
                   price=float(h1["close"].iloc[-1]), atr20_pips=round(atr, 1), stop_distance_pips=round(STOP_ATR * atr, 1), rebalance_band=REBALANCE_BAND)
    return exp, D


def plan(exp: Exposure, equity: float, target_annual_vol: float, daily_vol: float, current_units: float = 0.0) -> dict:
    """Translate the target into lots and a rebalance decision.
    1 unit = notional whose daily P&L sd equals the risk engine's daily vol target."""
    unit_notional = target_annual_vol / math.sqrt(252) * equity / max(daily_vol, 1e-6)
    lots_per_unit = unit_notional / 100_000
    flip = np.sign(exp.target_units) != np.sign(current_units) and exp.target_units != 0
    move = abs(exp.target_units - current_units) >= exp.rebalance_band
    action = "rebalance" if (flip or move) else "hold"
    side = "long" if exp.target_units > 0 else ("short" if exp.target_units < 0 else "flat")
    stop = exp.price - np.sign(exp.target_units) * exp.stop_distance_pips * 1e-4 if exp.target_units != 0 else float("nan")
    return {"action": action, "side": side, "target_units": exp.target_units, "current_units": current_units,
            "lots_per_unit": round(lots_per_unit, 3), "target_lots": round(abs(exp.target_units) * lots_per_unit, 2),
            "stop": round(stop, 5) if stop == stop else None, "stop_distance_pips": exp.stop_distance_pips,
            "risk_at_stop_usd": round(abs(exp.target_units) * lots_per_unit * exp.stop_distance_pips * 10, 2)}
