"""Command line interface.

  python -m eurusd.cli signals [--asof 2026-11-06T21:00] [--account 10000] [--risk 0.01] [--json]
  python -m eurusd.cli update            # download the latest HistData month(s) and rebuild bars
  python -m eurusd.cli backtest NAME TF '{"param": value}' [--period train|validate|holdout]
"""
from __future__ import annotations

import argparse
import json
import sys

import pandas as pd


def cmd_signals(a):
    from .signals import generate_signals, signals_to_frame
    asof = pd.Timestamp(a.asof, tz="UTC") if a.asof else None
    sig = generate_signals(asof, account=a.account, risk_per_trade=a.risk)
    if a.json:
        print(json.dumps([s.__dict__ for s in sig], indent=2, default=str))
        return
    if not sig:
        print("No actionable signal at", asof or "latest bar")
        return
    pd.set_option("display.width", 200)
    print(signals_to_frame(sig).to_string(index=False))


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
    s = sub.add_parser("signals"); s.add_argument("--asof"); s.add_argument("--account", type=float, default=10_000)
    s.add_argument("--risk", type=float, default=0.01); s.add_argument("--json", action="store_true"); s.set_defaults(f=cmd_signals)
    u = sub.add_parser("update"); u.add_argument("--no-external", action="store_true"); u.set_defaults(f=cmd_update)
    b = sub.add_parser("backtest"); b.add_argument("name"); b.add_argument("timeframe"); b.add_argument("params")
    b.add_argument("--period", default="validate"); b.set_defaults(f=cmd_backtest)
    a = p.parse_args(argv)
    a.f(a)


if __name__ == "__main__":
    main()
