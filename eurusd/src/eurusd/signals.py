"""Signal engine: turn the surviving strategies into live trade proposals.

A *strategy config* names a registered strategy, its timeframe and parameters
(exactly those that survived the evaluation protocol).  The engine replays the
strategy on the most recent bars and keeps the orders that are actionable now:

* market orders decided at the latest closed bar (to be executed at the next open)
* pending stop/limit orders whose validity window still includes the next bar

Every signal carries entry, stop-loss, take-profit, direction, validity and a
position size computed from account equity and risk per trade.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

import pandas as pd

from .backtest import Order, PIP
from .data import load_ohlc
from .strategies import REGISTRY

CONFIG_PATH = Path(__file__).resolve().parents[2] / "config" / "live_strategies.json"


@dataclass
class StrategyConfig:
    name: str                 # registered strategy function
    timeframe: str            # M5, M15, H1, ...
    params: dict
    label: str = ""
    weight: float = 1.0       # relative risk weight (1.0 = full risk_per_trade)
    lookback_bars: int = 3000 # bars replayed before `asof` (must cover indicator warm-up)
    notes: str = ""
    validation: dict = field(default_factory=dict)  # stats recorded at selection time


@dataclass
class Signal:
    strategy: str
    timeframe: str
    decided_at: str           # close time of the bar on which the decision is made (UTC)
    side: str                 # 'long' | 'short'
    entry_type: str           # market | stop | limit
    entry_price: float        # NaN for market (next open)
    stop_loss: float
    take_profit: float
    risk_pips: float
    reward_pips: float
    valid_until: str          # last bar close at which a pending order may still fill
    hard_exit: str            # time-based exit if any
    size_lots: float          # standard lots (100k) for the given account / risk
    rationale: str


def _load_configs(path: Path = CONFIG_PATH) -> list[StrategyConfig]:
    if not path.exists():
        return []
    raw = json.loads(path.read_text())
    return [StrategyConfig(**c) for c in raw]


def _bar_step(df: pd.DataFrame) -> pd.Timedelta:
    return (df.index[1:] - df.index[:-1]).min()


def orders_now(df: pd.DataFrame, cfg: StrategyConfig) -> list[Order]:
    """Replay the strategy and return the orders that are live at the last bar."""
    orders = REGISTRY[cfg.name](df, **cfg.params)
    last = len(df) - 1
    live = []
    for o in orders:
        if o.entry_type == "market" and o.i == last:
            live.append(o)
        elif o.entry_type in ("stop", "limit") and o.i <= last < o.i + o.expiry_bars:
            # pending order placed earlier and still valid (we cannot know if it filled already
            # without a trade log; the caller should reconcile with the broker)
            live.append(o)
    return live


def size_lots(risk_amount: float, risk_pips: float, pip_value_per_lot: float = 10.0) -> float:
    if risk_pips <= 0 or math.isnan(risk_pips):
        return 0.0
    return round(risk_amount / (risk_pips * pip_value_per_lot), 2)


def generate_signals(asof: Optional[pd.Timestamp] = None, configs: Optional[list[StrategyConfig]] = None,
                     account: float = 10_000.0, risk_per_trade: float = 0.01) -> list[Signal]:
    configs = configs if configs is not None else _load_configs()
    out: list[Signal] = []
    cache: dict[str, pd.DataFrame] = {}
    for cfg in configs:
        if cfg.timeframe not in cache:
            cache[cfg.timeframe] = load_ohlc(cfg.timeframe)
        df = cache[cfg.timeframe]
        if asof is not None:
            df = df.loc[:asof]
        df = df.iloc[-cfg.lookback_bars:]
        step = _bar_step(df)
        last_close_time = df.index[-1] + step
        for o in orders_now(df, cfg):
            ref = o.entry_price if o.entry_type != "market" else df["close"].iat[-1]
            risk_pips = abs(ref - o.sl) / PIP if not math.isnan(o.sl) else math.nan
            reward_pips = abs(o.tp - ref) / PIP if not math.isnan(o.tp) else math.nan
            valid_until = df.index[o.i] + step * (o.expiry_bars + 1) if o.entry_type != "market" else last_close_time + step
            hard_exit = (df.index[o.i] + step * (o.exit_i - o.i + 1)) if o.exit_i >= 0 else None
            out.append(Signal(
                strategy=cfg.label or cfg.name, timeframe=cfg.timeframe, decided_at=str(last_close_time),
                side="long" if o.side > 0 else "short", entry_type=o.entry_type,
                entry_price=float(o.entry_price) if o.entry_type != "market" else float("nan"),
                stop_loss=float(o.sl), take_profit=float(o.tp), risk_pips=round(risk_pips, 1), reward_pips=round(reward_pips, 1),
                valid_until=str(valid_until), hard_exit=str(hard_exit) if hard_exit is not None else "",
                size_lots=size_lots(account * risk_per_trade * cfg.weight, risk_pips), rationale=cfg.notes,
            ))
    return out


def signals_to_frame(signals: list[Signal]) -> pd.DataFrame:
    return pd.DataFrame([asdict(s) for s in signals])
