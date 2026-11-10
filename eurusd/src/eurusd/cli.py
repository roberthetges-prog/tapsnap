"""Command line interface.

  python -m eurusd.cli signals [--asof 2026-11-06T21:00] [--no-refresh] [--json]   # entries, sized by the risk engine
  python -m eurusd.cli exposure [--no-refresh] [--json]   # today's target daily exposure (round-2 survivor) with lots and stop
  python -m eurusd.cli risk [--asof ...] [--no-refresh] [--out reports/risk_latest.md]  # full risk report
  python -m eurusd.cli book add --strategy S --side long|short --entry P --stop P --lots L --opened ISO [--exit ISO]
  python -m eurusd.cli book close --id N --exit-price P --closed ISO
  python -m eurusd.cli book equity --set 10000 | book show
  python -m eurusd.cli update            # download the latest HistData month(s) and rebuild bars
  python -m eurusd.cli backtest NAME TF '{"param": value}' [--period train|validate|holdout]
"""
from __future__ import annotations

import argparse
import json
import sys

import pandas as pd


def _engine(a):
    from .live_data import load_h1_live
    from .risk import RiskEngine
    h1 = load_h1_live(refresh=not getattr(a, "no_refresh", False))
    asof = pd.Timestamp(a.asof, tz="UTC") if getattr(a, "asof", None) else None
    if asof is not None:
        h1 = h1.loc[:asof]
    return RiskEngine(h1), h1


def cmd_signals(a):
    import eurusd.signals as S
    from .signals import generate_signals, signals_to_frame
    eng, h1 = _engine(a)
    S.load_ohlc = lambda tf, _h1=h1, _orig=S.load_ohlc: _h1.drop(columns="source") if tf == "H1" else _orig(tf)
    asof = pd.Timestamp(a.asof, tz="UTC") if a.asof else None
    sig = generate_signals(asof, account=eng.book.equity, risk_per_trade=eng.cfg.max_risk_per_trade)
    rows = []
    for s in sig:
        ref = s.entry_price if s.entry_type != "market" else eng.price
        dec = eng.size(s.strategy_name if hasattr(s, "strategy_name") else _cfg_name(s.strategy), 1 if s.side == "long" else -1, ref, s.stop_loss, pd.Timestamp(s.decided_at))
        d = s.__dict__ | {"approved": dec.approved, "lots": dec.lots, "risk_usd": round(dec.risk_amount, 2), "risk_pct": round(dec.risk_fraction, 4),
                          "binding_cap": dec.binding_cap, "caps": dec.caps, "reasons": "; ".join(dec.reasons)}
        d.pop("size_lots", None)
        rows.append(d)
    if a.json:
        print(json.dumps(rows, indent=2, default=str))
        return
    if not rows:
        print("No actionable signal at", asof or h1.index[-1] + pd.Timedelta(hours=1))
        return
    pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 60)
    cols = ["strategy", "side", "entry_type", "entry_price", "stop_loss", "take_profit", "risk_pips", "hard_exit", "approved", "lots", "risk_usd", "binding_cap", "reasons"]
    print(pd.DataFrame(rows)[cols].to_string(index=False))


def _cfg_name(label: str) -> str:
    from .signals import _load_configs
    for c in _load_configs():
        if (c.label or c.name) == label:
            return c.name
    return label


def cmd_exposure(a):
    from .exposure import compute, plan
    from .risk import RiskEngine, Book
    exp, _ = compute(refresh=not a.no_refresh)
    eng = RiskEngine(__import__("eurusd.live_data", fromlist=["load_h1_live"]).load_h1_live(refresh=False))
    cur = sum(p.lots * p.side for p in eng.book.positions if p.strategy == "macro_exposure")
    vol = eng.vol_forecast()["har_daily_vol"]
    unit_lots = eng.cfg.target_annual_vol / (252 ** 0.5) * (eng.book.equity + eng.mtm()) / vol / 100_000
    cur_units = cur / unit_lots if unit_lots > 0 else 0.0
    pl = plan(exp, eng.book.equity + eng.mtm(), eng.cfg.target_annual_vol, vol, current_units=cur_units)
    st = eng.limits_status()
    if st["trading_halted"]:
        pl["action"] = "halted"; pl["reason"] = [k for k, v in st["checks"].items() if v["breached"]]
    out = {"exposure": exp.__dict__, "plan": pl, "risk_engine": {"har_daily_vol": round(vol, 5), "equity": eng.book.equity, "halted": st["trading_halted"]}}
    if a.json:
        print(json.dumps(out, indent=1, default=str)); return
    e = exp
    print(f"As of session close {e.asof_session_close} | price {e.price:.5f} | ATR20 {e.atr20_pips} pips")
    print(f"Target exposure: {pl['side'].upper()} {abs(e.target_units):.2f} units = {pl['target_lots']} lots (1 unit = {pl['lots_per_unit']} lots at {eng.cfg.target_annual_vol:.0%} vol target)")
    print(f"  C weak-signal combo: {e.c_units:+.2f}  (score {e.c_score:+.3f} vs threshold {e.c_threshold:.3f}, vol scale {e.c_vol_scale}); top contributions: " + ", ".join(f"{k} {v:+.3f}" for k, v in e.top_contributions.items()))
    print(f"  D positioning trend: {e.d_units:+.2f}  (cot_z52 {e.d_cot_z52:+.2f}, vol scale {e.d_vol_scale})")
    print(f"Disaster stop: {pl['stop']} ({e.stop_distance_pips} pips = {STOP_ATR_TXT}); risk at stop {pl['risk_at_stop_usd']} USD")
    print(f"Action: {pl['action'].upper()} (current {pl['current_units']:+.2f} units; rebalance when sign flips or |change| >= {e.rebalance_band})")


STOP_ATR_TXT = "2 x ATR20"


def cmd_risk(a):
    eng, _ = _engine(a)
    txt = eng.report()
    print(txt)
    if a.out:
        from pathlib import Path
        Path(a.out).write_text(txt)


def cmd_book(a):
    from .risk import Book, RiskConfig
    b = Book()
    cfg = RiskConfig.load()
    if a.action == "show":
        print(json.dumps({"equity": b.equity, "peak_equity": b.peak_equity, "positions": [p.__dict__ for p in b.positions], "closed": b.closed[-10:]}, indent=1, default=str))
        return
    if a.action == "equity":
        b.equity = float(a.set); b.peak_equity = max(b.peak_equity, b.equity); b.save(); print("equity set to", b.equity); return
    if a.action == "add":
        p = b.add(strategy=a.strategy, side=1 if a.side == "long" else -1, entry=a.entry, stop=a.stop, lots=a.lots, opened=a.opened, hard_exit=a.exit or "")
        b.save(); print("added position", p); return
    if a.action == "close":
        rec = b.close(a.id, a.exit_price, a.closed, cfg.pip_value_per_lot); b.save(); print("closed", rec); return


def cmd_update(a):
    from . import build_data
    build_data.main(["--skip-external"] if a.no_external else [])


def cmd_backtest(a):
    from .backtest import CostModel
    from .evaluate import run_one
    from .data import load_ohlc
    import eurusd.strategies  # noqa: F401  (registers built-ins)
    for mod in ("strategies_session", "strategies_trend_pa", "strategies_meanrev", "strategies_events"):
        try:
            __import__(f"eurusd.{mod}")
        except ImportError:
            pass
    df = load_ohlc(a.timeframe)
    s, res = run_one(df, a.name, json.loads(a.params), a.period, CostModel(spread_pips=1.0, slippage_pips=0.2))
    print(json.dumps({k: (round(v, 4) if isinstance(v, float) else v) for k, v in s.items()}, indent=1))
    print(res.by_year().round(3).to_string())


def main(argv=None):
    p = argparse.ArgumentParser(prog="eurusd")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("signals"); s.add_argument("--asof"); s.add_argument("--no-refresh", action="store_true")
    s.add_argument("--json", action="store_true"); s.set_defaults(f=cmd_signals)
    x = sub.add_parser("exposure"); x.add_argument("--no-refresh", action="store_true"); x.add_argument("--json", action="store_true"); x.set_defaults(f=cmd_exposure)
    r = sub.add_parser("risk"); r.add_argument("--asof"); r.add_argument("--no-refresh", action="store_true"); r.add_argument("--out"); r.set_defaults(f=cmd_risk)
    k = sub.add_parser("book"); k.add_argument("action", choices=["show", "add", "close", "equity"]); k.add_argument("--strategy"); k.add_argument("--side", choices=["long", "short"])
    k.add_argument("--entry", type=float); k.add_argument("--stop", type=float); k.add_argument("--lots", type=float); k.add_argument("--opened"); k.add_argument("--exit")
    k.add_argument("--id", type=int); k.add_argument("--exit-price", type=float, dest="exit_price"); k.add_argument("--closed"); k.add_argument("--set"); k.set_defaults(f=cmd_book)
    u = sub.add_parser("update"); u.add_argument("--no-external", action="store_true"); u.set_defaults(f=cmd_update)
    b = sub.add_parser("backtest"); b.add_argument("name"); b.add_argument("timeframe"); b.add_argument("params")
    b.add_argument("--period", default="validate"); b.set_defaults(f=cmd_backtest)
    a = p.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
