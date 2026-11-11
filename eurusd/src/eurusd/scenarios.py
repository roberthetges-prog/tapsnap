"""Parallel paper scenarios: every pre-registered variant is run every session and every result is kept.

Accounting is in "units" (1 unit = the vol-target notional of the risk engine) and basis points per unit:
  * at each completed NY-close session t: realise P&L of the position held over the session (stop-aware,
    using the session's high/low), then compute the scenario's target with data <= t and apply its
    rebalance rule (sign flip or |change| >= band), paying 1.2 pips per unit of turnover.
  * one row per scenario per session is appended to state/scenarios/ledger.csv; nothing is ever rewritten.
Definitions live in config/scenarios.json and are frozen at registration.
"""
from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pandas as pd

from . import features as F
from .arms import weak_signals as WS

ROOT = Path(__file__).resolve().parents[2]
CFG = ROOT / "config" / "scenarios.json"
DIR = ROOT / "state" / "scenarios"
LEDGER = DIR / "ledger.csv"
STATE = DIR / "positions.json"
PIP = 1e-4
COST_PIPS = 1.2
VOL_CAP = 1.5
COLS = ["session_close", "scenario", "price", "pnl_bp", "cost_bp", "stopped", "target_units", "held_units", "stop", "unit_frac"]


def _signals_asof(Dt: pd.DataFrame) -> dict:
    """Component signals for the LAST row of Dt, fitted on rows before it only."""
    S = WS.build_raw_signals(Dt)
    names = list(WS.SIGNALS)
    frame = pd.concat([S[names], Dt[["fwd_1d", "rv_21d_bp"]]], axis=1)
    hist = frame.iloc[:-1]
    hist = hist[hist["fwd_1d"].notna()]
    last = frame.iloc[[-1]]
    out = {}
    for key, (method, mapping) in {"weak_sign": ("tstat", "sign"), "weak_linear": ("ridge", "linear")}.items():
        fit, predict = WS.make_fit_predict(method, mapping, names)
        out[key] = float(predict(fit(hist), last).iloc[0])
    rv = float(last["rv_21d_bp"].iloc[0])
    scale = float(np.clip(hist["rv_21d_bp"].median() / rv, 0, VOL_CAP)) if rv > 0 else 0.0
    row = Dt.iloc[-1]
    sgn = lambda x: 0.0 if (x != x) else float(np.sign(x))
    out["positioning"] = sgn(row["cot_z52"]) * scale
    out["round1"] = (float(row["h_to_fomc"] < 30) + sgn(row["cot_z52"]) + sgn(row["d_spread2y_20"])) / 3.0 * scale
    out["trend"] = sgn(row["ret_63d"]) * scale
    return out


def _target(expr: str, sig: dict) -> float:
    if expr.startswith("const:"):
        return float(expr.split(":")[1])
    total = 0.0
    for term in expr.split("+"):
        term = term.strip()
        if "*" in term:
            w, name = term.split("*")
            total += float(w) * sig[name.strip()]
        else:
            total += sig[term]
    return float(total)


def _london_short_bp(h1: pd.DataFrame, close_time: pd.Timestamp) -> float | None:
    """Short from the 07:00 London bar open to the 13:00 London bar open on the session's London date."""
    seg = h1.loc[close_time - pd.Timedelta(hours=24):close_time - pd.Timedelta(seconds=1)]
    if seg.empty:
        return None
    lon = seg.index.tz_convert("Europe/London")
    day = close_time.tz_convert("Europe/London").normalize()
    m = (lon.normalize() == day) & (lon.hour >= 7) & (lon.hour < 13)
    w = seg[m]
    if len(w) < 5 or day.dayofweek >= 5:
        return None
    entry, exit_ = w["open"].iloc[0], w["close"].iloc[-1]
    return float(-(math.log(exit_ / entry)) * 1e4 - COST_PIPS * PIP / entry * 1e4)


def run(D: pd.DataFrame, h1: pd.DataFrame, unit_frac: float) -> list[str]:
    """Process every completed session not yet in the ledger. Returns short notes."""
    cfg = json.loads(CFG.read_text())["scenarios"]
    DIR.mkdir(parents=True, exist_ok=True)
    state = json.loads(STATE.read_text()) if STATE.exists() else {"_last": None, "_start": None, "pos": {}}
    daily = F.daily_ohlc(h1[["open", "high", "low", "close"]], 22)
    atr = F.atr(daily, 20)
    sessions = list(D.index)
    if state["_last"] is None:
        todo = sessions[-1:]                      # first run: establish positions, no P&L yet
    else:
        last = pd.Timestamp(state["_last"])
        todo = [s for s in sessions if D.loc[s, "close_time"] > last]
    rows, notes = [], []
    for s in todo:
        Dt = D.loc[:s]
        ct = D.loc[s, "close_time"]
        px = float(D.loc[s, "close"])
        prev_px = float(D["close"].shift(1).loc[s]) if s != sessions[0] else px
        hi, lo = float(daily.loc[s, "high"]), float(daily.loc[s, "low"])
        a = float(atr.loc[s])
        sig = _signals_asof(Dt)
        cost_unit_bp = COST_PIPS * PIP / px * 1e4
        first = state["_last"] is None
        for name, sc in cfg.items():
            if name in state.get("retired", {}):
                continue
            if sc["signal"] == "intraday_london_short":
                pnl = None if first else _london_short_bp(h1, ct)
                rows.append([str(ct), name, px, 0.0 if pnl is None else round(pnl, 3), 0.0, False, -1.0, 0.0, None, unit_frac])
                continue
            p = state["pos"].get(name, {"held": 0.0, "stop": None})
            held, stop = p["held"], p["stop"]
            pnl, stopped = 0.0, False
            if not first and held != 0:
                if stop is not None and ((held > 0 and lo <= stop) or (held < 0 and hi + PIP >= stop)):
                    pnl = held * math.log(stop / prev_px) * 1e4
                    stopped, held = True, 0.0
                else:
                    pnl = held * math.log(px / prev_px) * 1e4
            tgt = _target(sc["signal"], sig)
            band = sc.get("band", 0.5)
            flip = np.sign(tgt) != np.sign(held) and (tgt != 0 or held != 0)
            cost = 0.0
            if flip or abs(tgt - held) >= max(band, 1e-9) or (band == 0 and tgt != held):
                cost = abs(tgt - held) * cost_unit_bp
                held = tgt
                sa = sc.get("stop_atr")
                stop = (px - np.sign(held) * sa * a) if (sa and held != 0) else None
            if stopped:
                notes.append(f"{name}: stop hit")
            state["pos"][name] = {"held": round(held, 4), "stop": None if stop is None else round(float(stop), 5)}
            rows.append([str(ct), name, px, round(pnl - cost, 3), round(cost, 3), stopped, round(tgt, 4), round(held, 4),
                         None if stop is None else round(float(stop), 5), round(unit_frac, 4)])
        state["_last"] = str(ct)
        state["_start"] = state["_start"] or str(ct)
    if rows:
        new = pd.DataFrame(rows, columns=COLS)
        new.to_csv(LEDGER, mode="a", header=not LEDGER.exists(), index=False)
        STATE.write_text(json.dumps(state, indent=1))
        notes.insert(0, f"{len(todo)} session(s) logged for {len(cfg)} scenarios")
    return notes


MIN_WATCH, MIN_DECIDE = 60, 120      # sessions before a scenario is watched / decided
PROMOTE_MARGIN = 0.3                 # net Sharpe a challenger must beat base by


def _stats(g: pd.DataFrame) -> dict:
    x = g["pnl_bp"]                                   # row 0 = entry cost only
    n = len(x) - 1
    live = x.iloc[1:]
    cum = x.cumsum()
    sharpe = float(live.mean() / live.std() * math.sqrt(252)) if n >= 20 and live.std() > 0 else None
    half = n // 2
    return {"sessions": n, "net_bp": round(float(x.sum()), 1), "pct_equity": round(float((x / 1e4 * g["unit_frac"]).sum() * 100), 2),
            "bp_per_session": round(float(live.mean()), 2) if n else 0.0, "sharpe": None if sharpe is None else round(sharpe, 2),
            "hit_rate": round(float((live > 0).sum() / max(1, (live != 0).sum())), 2) if n else None,
            "max_dd_bp": round(float((cum - cum.cummax()).min()), 1), "held_units": float(g["held_units"].iloc[-1]), "stops": int(g["stopped"].sum()),
            "_h1": float(live.iloc[:half].sum()) if n >= 2 else 0.0, "_h2": float(live.iloc[half:].sum()) if n >= 2 else 0.0}


def leaderboard() -> pd.DataFrame:
    """All scenarios, live and retired, with the pre-registered verdict:
    too early (< 60 sessions) | watch (60-119) | from 120: KEEP / PROMOTE? / DISPOSE.  Benchmarks and controls are yardsticks."""
    if not LEDGER.exists():
        return pd.DataFrame()
    L = pd.read_csv(LEDGER)
    cfg = json.loads(CFG.read_text())["scenarios"]
    state = json.loads(STATE.read_text()) if STATE.exists() else {}
    retired = state.get("retired", {})
    rows = {name: _stats(g) for name, g in L.groupby("scenario", sort=False)}
    base_sr = rows.get("base", {}).get("sharpe")
    out = []
    for name, r in rows.items():
        role = cfg.get(name, {}).get("role", "?")
        n, sr = r["sessions"], r["sharpe"]
        if name in retired:
            v = f"DISPOSED {retired[name]['date'][:10]}"
        elif role in ("benchmark", "control"):
            v = "yardstick"
        elif n < MIN_WATCH:
            v = f"too early ({n}/{MIN_WATCH})"
        elif n < MIN_DECIDE:
            v = f"watch ({n}/{MIN_DECIDE})"
        elif sr is not None and sr < 0:
            v = "REVIEW: primary negative" if role == "primary" else "DISPOSE"
        elif role != "primary" and base_sr is not None and sr is not None and sr >= base_sr + PROMOTE_MARGIN and r["_h1"] > 0 and r["_h2"] > 0:
            v = "PROMOTE?"
        else:
            v = "KEEP"
        out.append({"scenario": name, "role": role, **{k: v2 for k, v2 in r.items() if not k.startswith("_")}, "verdict": v})
    return pd.DataFrame(out).sort_values("net_bp", ascending=False).reset_index(drop=True)


def review(apply: bool = True) -> list[str]:
    """Apply the disposal rule: scenarios with verdict DISPOSE stop being run; their ledger rows stay forever."""
    lb = leaderboard()
    if lb.empty:
        return []
    state = json.loads(STATE.read_text())
    notes = []
    for r in lb.itertuples():
        if r.verdict == "DISPOSE":
            notes.append(f"disposed {r.scenario}: Sharpe {r.sharpe} after {r.sessions} sessions (ledger kept)")
            if apply:
                state.setdefault("retired", {})[r.scenario] = {"date": state["_last"], "reason": f"net Sharpe {r.sharpe} < 0 after {r.sessions} sessions"}
        elif r.verdict in ("PROMOTE?", "REVIEW: primary negative"):
            notes.append(f"{r.verdict} {r.scenario}: Sharpe {r.sharpe} after {r.sessions} sessions (needs the owner's decision)")
    if apply and notes:
        STATE.write_text(json.dumps(state, indent=1))
    return notes


def summary_line() -> str:
    lb = leaderboard()
    if lb.empty or lb["sessions"].max() == 0:
        return "Scenarios: registered, first P&L next session"
    base = lb[lb.scenario == "base"].iloc[0]
    best, worst = lb.iloc[0], lb.iloc[-1]
    return (f"Scenarios ({int(base.sessions)} sessions, net bp/unit): base {base.net_bp:+.0f} | best {best.scenario} {best.net_bp:+.0f} | "
            f"worst {worst.scenario} {worst.net_bp:+.0f}")
