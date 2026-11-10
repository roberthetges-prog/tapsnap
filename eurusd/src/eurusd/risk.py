"""Risk engine: everything between a signal and an order, and everything that watches the book.

Pieces
------
* RiskConfig / Book            limits (config/risk_limits.json) and the position book (state/book.json)
* RiskEngine.size()            vol-target, fractional-Kelly and hard caps -> lots for a signal, or a block with reasons
* RiskEngine.var_es()          1-day VaR / Expected Shortfall of the open book: parametric (HAR vol), historical
                               simulation (26 years of daily returns, stop-aware), Monte Carlo of the strategy mix
* RiskEngine.stress()          replay of the open book through historical shock episodes and synthetic gaps
* RiskEngine.events_ahead()    high-impact releases coming up (FOMC, ECB, NFP, CPI, ...)
* RiskEngine.limits_status()   kill switches: daily / monthly loss, drawdown, consecutive losses, data age, spread
* RiskEngine.component_health()is each live strategy still behaving like its validation record?
* RiskEngine.report()          one markdown report with all of the above
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd
from scipy.stats import norm

from . import features as F
from .volatility import har_forecast

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "config" / "risk_limits.json"
BOOK = ROOT / "state" / "book.json"
RESULTS = ROOT / "experiments" / "results"
MACRO = ROOT / "data" / "macro"
PIP = 0.0001

# historical shock episodes (UTC). Replayed as return paths on the current book.
SCENARIOS = {
    "SNB floor removal 2015-01-15": ("2015-01-15 09:00", "2015-01-16 00:00"),
    "FOMC 2015-03-18 (120 pips/min)": ("2015-03-18 17:00", "2015-03-19 00:00"),
    "ECB 2015-12-03 (168 pips/min)": ("2015-12-03 12:00", "2015-12-04 00:00"),
    "Brexit night 2016-06-23/24": ("2016-06-23 21:00", "2016-06-24 12:00"),
    "US election night 2016-11-08/09": ("2016-11-08 22:00", "2016-11-09 12:00"),
    "COVID dash for cash 2020-03-09..20": ("2020-03-09 00:00", "2020-03-20 21:00"),
    "Ukraine invasion 2022-02-24": ("2022-02-23 21:00", "2022-02-24 21:00"),
    "Dollar surge Sep 2022 (10 days)": ("2022-09-13 12:00", "2022-09-27 21:00"),
    "Tariff weekend gap 2025-02-02": ("2025-01-31 21:00", "2025-02-03 12:00"),
}


@dataclass
class RiskConfig:
    account_currency: str = "USD"
    pip_value_per_lot: float = 10.0
    max_risk_per_trade: float = 0.005
    target_annual_vol: float = 0.08
    kelly_fraction: float = 0.25
    max_open_risk: float = 0.015
    max_daily_loss: float = 0.02
    max_monthly_loss: float = 0.05
    max_drawdown: float = 0.10
    max_consecutive_losses: int = 8
    event_block_minutes_before: int = 30
    event_block_minutes_after: int = 15
    event_size_cut_hours_before: float = 4.0
    event_size_cut_factor: float = 0.5
    max_spread_pips: float = 2.5
    max_data_age_hours: float = 30.0
    var_confidence: float = 0.99
    stress_gap_adr_multiples: list = field(default_factory=lambda: [1.0, 2.0, 3.0])
    health_window_trades: int = 40
    health_z_alert: float = -2.0

    @classmethod
    def load(cls, path: Path = CONFIG) -> "RiskConfig":
        return cls(**json.loads(path.read_text())) if path.exists() else cls()


@dataclass
class Position:
    id: int
    strategy: str
    side: int               # +1 long, -1 short
    entry: float
    stop: float
    lots: float
    opened: str             # ISO UTC
    take_profit: float = math.nan
    hard_exit: str = ""

    def pnl(self, price: float, pip_value: float) -> float:
        return (price - self.entry) * self.side / PIP * self.lots * pip_value

    def risk_at_stop(self, pip_value: float) -> float:
        return abs(self.entry - self.stop) / PIP * self.lots * pip_value


class Book:
    def __init__(self, path: Path = BOOK):
        self.path = path
        d = json.loads(path.read_text()) if path.exists() else {"equity": 10000.0, "peak_equity": 10000.0, "positions": [], "closed_trades": []}
        self.equity: float = d["equity"]
        self.peak_equity: float = d.get("peak_equity", self.equity)
        self.positions: list[Position] = [Position(**p) for p in d.get("positions", [])]
        self.closed: list[dict] = d.get("closed_trades", [])

    def save(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps({"equity": self.equity, "peak_equity": self.peak_equity,
                                         "positions": [asdict(p) for p in self.positions],
                                         "closed_trades": self.closed}, indent=1, default=str))

    def add(self, **kw) -> Position:
        pid = 1 + max([p.id for p in self.positions] + [t.get("id", 0) for t in self.closed] + [0])
        p = Position(id=pid, **kw)
        self.positions.append(p)
        return p

    def close(self, pid: int, exit_price: float, when: str, pip_value: float) -> dict:
        p = next(x for x in self.positions if x.id == pid)
        pnl = p.pnl(exit_price, pip_value)
        risk = p.risk_at_stop(pip_value)
        rec = dict(id=p.id, strategy=p.strategy, side=p.side, entry=p.entry, exit=exit_price, lots=p.lots,
                   opened=p.opened, closed=when, pnl=pnl, pips=(exit_price - p.entry) * p.side / PIP,
                   r=(pnl / risk) if risk > 0 else math.nan)
        self.positions.remove(p)
        self.closed.append(rec)
        self.equity += pnl
        self.peak_equity = max(self.peak_equity, self.equity)
        return rec


@dataclass
class SizingDecision:
    approved: bool
    lots: float
    risk_amount: float
    risk_fraction: float
    binding_cap: str
    caps: dict
    reasons: list


class RiskEngine:
    def __init__(self, h1: pd.DataFrame, cfg: Optional[RiskConfig] = None, book: Optional[Book] = None,
                 now: Optional[pd.Timestamp] = None):
        self.cfg = cfg or RiskConfig.load()
        self.book = book or Book()
        self.h1 = h1
        self.now = now or (h1.index[-1] + pd.Timedelta(hours=1))
        self.price = float(h1["close"].iloc[-1])
        self.daily = F.daily_ohlc(h1[["open", "high", "low", "close"]], 22)
        self.daily = self.daily[self.daily["n"] >= 10]
        self._events = None
        self._vol = None

    # ------------------------------------------------------------------ volatility
    def vol_forecast(self) -> dict:
        """One-day-ahead volatility (fraction of price) from HAR on daily realized variance of hourly returns."""
        if self._vol is None:
            r = np.log(self.h1["close"]).diff()
            day = (self.h1.index - pd.Timedelta(hours=22)).floor("D")
            rv = (r ** 2).groupby(day).sum()
            n = r.groupby(day).size()
            rv = rv[n >= 10].iloc[-1500:]
            har = har_forecast(rv, window=500)
            f = har.dropna()
            last = float(f.iloc[-1]) if len(f) else float(rv.iloc[-22:].mean())
            atr = float(F.atr(self.daily, 14).iloc[-1]) / self.price
            self._vol = {"har_daily_vol": math.sqrt(last), "har_annual_vol": math.sqrt(last * 252),
                         "realized_22d_annual_vol": float(np.sqrt(rv.iloc[-22:].mean() * 252)),
                         "atr14_pips": atr * self.price / PIP, "adr14_pips": float(((self.daily.high - self.daily.low) / PIP).iloc[-14:].mean())}
        return self._vol

    # ------------------------------------------------------------------ events
    def events(self) -> pd.DataFrame:
        if self._events is None:
            frames = []
            p = MACRO / "events_high_eur_usd.csv"
            if p.exists():
                e = pd.read_csv(p)
                e = e[e.has_time == True]
                frames.append(pd.DataFrame({"time": pd.to_datetime(e.datetime_utc, utc=True), "event": e.currency + " " + e.event, "source": e.source}))
            for fn, col, label in (("fomc_decisions.csv", "statement_utc", "FOMC statement"), ("ecb_decisions.csv", "decision_utc", "ECB decision"), ("us_bls_releases.csv", "release_utc", None)):
                q = MACRO / fn
                if q.exists():
                    d = pd.read_csv(q)
                    frames.append(pd.DataFrame({"time": pd.to_datetime(d[col], utc=True), "event": (label or ("US " + d["release"])), "source": fn}))
            ev = pd.concat(frames).dropna().drop_duplicates(["time", "event"]).sort_values("time") if frames else pd.DataFrame(columns=["time", "event", "source"])
            self._events = ev
        return self._events

    def events_ahead(self, hours: float = 48) -> pd.DataFrame:
        ev = self.events()
        m = (ev.time > self.now) & (ev.time <= self.now + pd.Timedelta(hours=hours))
        out = ev[m].copy()
        out["hours_ahead"] = ((out.time - self.now).dt.total_seconds() / 3600).round(1)
        return out.head(25)

    def event_gate(self, at: pd.Timestamp) -> tuple[str, Optional[str]]:
        """'block' inside the release window, 'cut' within the pre-event hours, else 'ok'."""
        ev = self.events()
        before = pd.Timedelta(minutes=self.cfg.event_block_minutes_before)
        after = pd.Timedelta(minutes=self.cfg.event_block_minutes_after)
        hit = ev[(ev.time >= at - after) & (ev.time <= at + before)]
        if not hit.empty:
            return "block", f"{hit.iloc[0].event} at {hit.iloc[0].time:%Y-%m-%d %H:%M} UTC"
        soon = ev[(ev.time > at) & (ev.time <= at + pd.Timedelta(hours=self.cfg.event_size_cut_hours_before))]
        if not soon.empty:
            return "cut", f"{soon.iloc[0].event} in {(soon.iloc[0].time - at).total_seconds() / 3600:.1f}h"
        return "ok", None

    # ------------------------------------------------------------------ component statistics
    def component_trades(self, strategy: str) -> pd.DataFrame:
        parts = []
        for period in ("validate", "holdout"):
            p = RESULTS / f"trades_{strategy}_{period}.csv"
            if p.exists():
                t = pd.read_csv(p)
                t["period"] = period
                parts.append(t)
        return pd.concat(parts) if parts else pd.DataFrame()

    def component_stats(self, strategy: str) -> dict:
        t = self.component_trades(strategy)
        if t.empty:
            return {}
        r = t["r"].replace([np.inf, -np.inf], np.nan).dropna()
        wins, losses = r[r > 0], r[r <= 0]
        p = len(wins) / len(r)
        b = (wins.mean() / -losses.mean()) if len(losses) and losses.mean() < 0 else np.nan
        kelly = (p - (1 - p) / b) if b and not np.isnan(b) and b > 0 else 0.0
        return {"trades": int(len(r)), "win_rate": p, "avg_win_r": float(wins.mean()) if len(wins) else 0.0,
                "avg_loss_r": float(losses.mean()) if len(losses) else 0.0, "payoff_b": float(b) if b == b else np.nan,
                "mean_r": float(r.mean()), "sd_r": float(r.std()), "kelly_full": float(max(kelly, 0.0)),
                "trades_per_year": float(len(r) / max(1e-9, (pd.to_datetime(t["exit_time"]).max() - pd.to_datetime(t["entry_time"]).min()).days / 365.25))}

    # ------------------------------------------------------------------ limits
    def open_risk(self) -> float:
        return sum(p.risk_at_stop(self.cfg.pip_value_per_lot) for p in self.book.positions)

    def mtm(self) -> float:
        return sum(p.pnl(self.price, self.cfg.pip_value_per_lot) for p in self.book.positions)

    def realized(self, since: pd.Timestamp) -> float:
        return sum(t["pnl"] for t in self.book.closed if pd.Timestamp(t["closed"]).tz_convert("UTC") >= since)

    def consecutive_losses(self, strategy: Optional[str] = None) -> int:
        seq = [t for t in sorted(self.book.closed, key=lambda t: t["closed"]) if strategy is None or t["strategy"] == strategy]
        n = 0
        for t in reversed(seq):
            if t["pnl"] < 0:
                n += 1
            else:
                break
        return n

    def limits_status(self) -> dict:
        eq = self.book.equity
        mtm = self.mtm()
        today = self.now.normalize()
        month = self.now.normalize().replace(day=1)
        day_pnl = self.realized(today) + mtm
        month_pnl = self.realized(month) + mtm
        dd = (eq + mtm) / self.book.peak_equity - 1 if self.book.peak_equity > 0 else 0.0
        age_h = (self.now - self.h1.index[-1]).total_seconds() / 3600 - 1
        checks = {
            "daily_loss": (day_pnl / eq, -self.cfg.max_daily_loss, day_pnl / eq <= -self.cfg.max_daily_loss),
            "monthly_loss": (month_pnl / eq, -self.cfg.max_monthly_loss, month_pnl / eq <= -self.cfg.max_monthly_loss),
            "drawdown": (dd, -self.cfg.max_drawdown, dd <= -self.cfg.max_drawdown),
            "open_risk": (self.open_risk() / eq, self.cfg.max_open_risk, self.open_risk() / eq > self.cfg.max_open_risk),
            "consecutive_losses": (self.consecutive_losses(), self.cfg.max_consecutive_losses, self.consecutive_losses() >= self.cfg.max_consecutive_losses),
            "data_age_hours": (age_h, self.cfg.max_data_age_hours, age_h > self.cfg.max_data_age_hours),
        }
        return {"equity": eq, "mtm": mtm, "equity_with_mtm": eq + mtm, "peak_equity": self.book.peak_equity,
                "checks": {k: {"value": v[0], "limit": v[1], "breached": bool(v[2])} for k, v in checks.items()},
                "trading_halted": any(v[2] for k, v in checks.items() if k != "open_risk")}

    # ------------------------------------------------------------------ sizing
    def size(self, strategy: str, side: int, entry: float, stop: float, decided_at: Optional[pd.Timestamp] = None,
             spread_pips: Optional[float] = None) -> SizingDecision:
        cfg = self.cfg
        eq = self.book.equity + self.mtm()
        stop_pips = abs(entry - stop) / PIP
        reasons, caps = [], {}
        if stop_pips <= 0 or np.isnan(stop_pips):
            return SizingDecision(False, 0.0, 0.0, 0.0, "invalid", {}, ["no valid stop"])
        caps["hard_cap"] = cfg.max_risk_per_trade * eq
        stats = self.component_stats(strategy)
        if stats:
            caps["fractional_kelly"] = cfg.kelly_fraction * stats["kelly_full"] * eq
            if stats["kelly_full"] <= 0:
                reasons.append("component has no positive Kelly fraction in validation+holdout trades")
        vol = self.vol_forecast()
        # vol target: daily P&L sd of the position = target; notional = target*eq / sigma_daily; risk = notional * stop distance
        notional = cfg.target_annual_vol / math.sqrt(252) * eq / max(vol["har_daily_vol"], 1e-6)
        caps["vol_target"] = notional * stop_pips * PIP / entry
        remaining = cfg.max_open_risk * eq - self.open_risk()
        caps["open_risk_budget"] = max(0.0, remaining)
        risk = min(caps.values())
        binding = min(caps, key=caps.get)
        at = decided_at or self.now
        gate, why = self.event_gate(at + pd.Timedelta(hours=1))
        if gate == "block":
            reasons.append(f"entry inside release window: {why}")
        elif gate == "cut":
            risk *= cfg.event_size_cut_factor
            caps["event_cut_factor"] = cfg.event_size_cut_factor
            reasons.append(f"size cut x{cfg.event_size_cut_factor}: {why}")
        st = self.limits_status()
        for k, v in st["checks"].items():
            if v["breached"] and k != "open_risk":
                reasons.append(f"limit breached: {k} = {v['value']:.3f} (limit {v['limit']})")
        if self.consecutive_losses(strategy) >= cfg.max_consecutive_losses:
            reasons.append(f"{strategy}: {self.consecutive_losses(strategy)} consecutive losses")
        if spread_pips is not None and spread_pips > cfg.max_spread_pips:
            reasons.append(f"spread {spread_pips} pips > {cfg.max_spread_pips}")
        health = self.component_health().get(strategy, {})
        if health.get("alert"):
            reasons.append(f"{strategy} health alert: z = {health['z']:.2f} vs validation")
        approved = gate != "block" and not st["trading_halted"] and risk > 0 and not any("consecutive" in r or "spread" in r or "health" in r for r in reasons)
        lots = math.floor(risk / (stop_pips * cfg.pip_value_per_lot) * 100) / 100 if approved else 0.0
        if approved and lots < 0.01:
            approved, lots = False, 0.0
            reasons.append("risk budget below the minimum lot size")
        return SizingDecision(approved, lots, lots * stop_pips * cfg.pip_value_per_lot, lots * stop_pips * cfg.pip_value_per_lot / eq if eq else 0.0,
                              binding, {k: round(v, 2) for k, v in caps.items()}, reasons)

    # ------------------------------------------------------------------ VaR / ES
    def var_es(self) -> dict:
        cfg = self.cfg
        pv = cfg.pip_value_per_lot
        alpha = cfg.var_confidence
        z = norm.ppf(alpha)
        vol = self.vol_forecast()
        out = {"confidence": alpha, "horizon": "1 day"}
        if not self.book.positions:
            out["note"] = "no open positions"
        # net exposure in USD per 1.0 move... P&L per unit log-return = sum(side * lots * 100000 * price_in_usd) ~ lots*100k
        exposure = sum(p.side * p.lots * 100_000 for p in self.book.positions)  # USD notional (EUR/USD quoted in USD)
        sigma = vol["har_daily_vol"]
        out["parametric"] = {"var": abs(exposure) * sigma * z, "es": abs(exposure) * sigma * norm.pdf(z) / (1 - alpha), "net_exposure_usd": exposure, "daily_vol": sigma}
        # historical simulation with stops: apply every historical NY-close daily return to the book
        rets = np.log(self.daily["close"]).diff().dropna().values
        pnl = np.zeros(len(rets))
        for p in self.book.positions:
            move = self.price * (np.exp(rets) - 1)                # price change
            raw = p.side * move / PIP * p.lots * pv
            max_loss = -(abs(self.price - p.stop) / PIP * p.lots * pv) * 1.2   # stop with 20 % gap allowance
            pnl += np.maximum(raw, max_loss) if p.side * (p.stop - self.price) < 0 else raw
        if self.book.positions:
            q = np.quantile(pnl, 1 - alpha)
            out["historical"] = {"var": float(-q), "es": float(-pnl[pnl <= q].mean()), "days": int(len(rets)), "worst_day": float(pnl.min())}
        # Monte Carlo of the strategy mix over 1 month / 1 year at the configured risk per trade
        mc = self.monte_carlo()
        if mc:
            out["monte_carlo_strategy_mix"] = mc
        return out

    def monte_carlo(self, n_paths: int = 4000, seed: int = 7) -> dict:
        cfg = self.cfg
        strategies = [c["name"] for c in json.loads((ROOT / "config" / "live_strategies.json").read_text())]
        pools, rates = [], []
        for s in strategies:
            st = self.component_stats(s)
            t = self.component_trades(s)
            if t.empty or not st:
                continue
            r = t["r"].replace([np.inf, -np.inf], np.nan).dropna().values
            pools.append(r)
            rates.append(st["trades_per_year"])
        if not pools:
            return {}
        rng = np.random.default_rng(seed)
        f = cfg.max_risk_per_trade
        res = {}
        for label, years in (("1_month", 1 / 12), ("1_year", 1.0)):
            finals, maxdd = np.empty(n_paths), np.empty(n_paths)
            for k in range(n_paths):
                parts = []
                for pool, rate in zip(pools, rates):
                    n = rng.poisson(rate * years)
                    if n:
                        parts.append(rng.choice(pool, n))
                seq = np.concatenate(parts) if parts else np.array([0.0])
                rng.shuffle(seq)
                eq = np.cumprod(1 + f * seq)
                finals[k] = eq[-1] - 1
                maxdd[k] = (eq / np.maximum.accumulate(eq) - 1).min()
            res[label] = {"median_return": float(np.median(finals)), "p5_return": float(np.quantile(finals, 0.05)),
                          "p95_return": float(np.quantile(finals, 0.95)), "var_99": float(-np.quantile(finals, 0.01)),
                          "p_loss": float((finals < 0).mean()), "median_max_dd": float(np.median(maxdd)),
                          "p_breach_max_drawdown": float((maxdd <= -cfg.max_drawdown).mean())}
        res["risk_per_trade"] = f
        res["trades_per_year_total"] = float(sum(rates))
        return res

    # ------------------------------------------------------------------ stress
    def stress(self) -> pd.DataFrame:
        pv = self.cfg.pip_value_per_lot
        rows = []
        if not self.book.positions:
            return pd.DataFrame()
        for name, (a, b) in SCENARIOS.items():
            seg = self.h1.loc[a:b]
            if len(seg) < 2:
                continue
            base = seg["open"].iloc[0]
            total = 0.0
            stopped = []
            for p in self.book.positions:
                # rescale the episode's path onto today's price
                hi = self.price * seg["high"].values / base
                lo = self.price * seg["low"].values / base
                op = self.price * seg["open"].values / base
                cl = self.price * seg["close"].iloc[-1] / base
                exit_px = cl
                for j in range(len(seg)):
                    if p.side > 0 and lo[j] <= p.stop:
                        exit_px = min(p.stop, op[j]); stopped.append(p.id); break
                    if p.side < 0 and hi[j] >= p.stop:
                        exit_px = max(p.stop, op[j]); stopped.append(p.id); break
                total += (exit_px - self.price) * p.side / PIP * p.lots * pv
            move = (seg["close"].iloc[-1] / base - 1) * 1e4
            rows.append(dict(scenario=name, episode_move_bp=round(move, 0), book_pnl=round(total, 2),
                             pct_equity=round(total / self.book.equity, 4), positions_stopped=len(stopped)))
        adr = self.vol_forecast()["adr14_pips"]
        for m in self.cfg.stress_gap_adr_multiples:
            for direction in (+1, -1):
                total = 0.0
                for p in self.book.positions:
                    gap_px = self.price * (1 + direction * m * adr * PIP / self.price)
                    exit_px = gap_px
                    if (p.side > 0 and gap_px <= p.stop) or (p.side < 0 and gap_px >= p.stop):
                        exit_px = gap_px  # gap through the stop fills at the gap price
                    total += (exit_px - self.price) * p.side / PIP * p.lots * pv
                rows.append(dict(scenario=f"synthetic gap {'+' if direction > 0 else '-'}{m:.0f} ADR ({m * adr:.0f} pips)",
                                 episode_move_bp=round(direction * m * adr * PIP / self.price * 1e4, 0), book_pnl=round(total, 2),
                                 pct_equity=round(total / self.book.equity, 4), positions_stopped=sum(1 for p in self.book.positions if (p.side > 0 and self.price * (1 + direction * m * adr * PIP / self.price) <= p.stop) or (p.side < 0 and self.price * (1 + direction * m * adr * PIP / self.price) >= p.stop))))
        return pd.DataFrame(rows)

    # ------------------------------------------------------------------ component health
    def component_health(self) -> dict:
        out = {}
        strategies = [c["name"] for c in json.loads((ROOT / "config" / "live_strategies.json").read_text())]
        for s in strategies:
            st = self.component_stats(s)
            live = [t for t in self.book.closed if t["strategy"] == s and t.get("r") == t.get("r")]
            rec = {"validation_mean_r": st.get("mean_r"), "validation_sd_r": st.get("sd_r"), "live_trades": len(live)}
            if st and live:
                rs = np.array([t["r"] for t in live[-self.cfg.health_window_trades:]])
                z = (rs.mean() - st["mean_r"]) / (st["sd_r"] / math.sqrt(len(rs))) if st["sd_r"] > 0 else 0.0
                rec.update({"live_mean_r": float(rs.mean()), "z": float(z), "alert": bool(z < self.cfg.health_z_alert),
                            "consecutive_losses": self.consecutive_losses(s)})
            else:
                rec.update({"live_mean_r": None, "z": None, "alert": False, "consecutive_losses": self.consecutive_losses(s)})
            out[s] = rec
        return out

    # ------------------------------------------------------------------ report
    def report(self) -> str:
        L = []
        P = L.append
        src = self.h1["source"].iloc[-1] if "source" in self.h1 else "histdata"
        P(f"# Risk report  {self.now:%Y-%m-%d %H:%M} UTC\n")
        P(f"Last bar {self.h1.index[-1]:%Y-%m-%d %H:%M} UTC (source: {src}), price {self.price:.5f}\n")
        vol = self.vol_forecast()
        P(f"## Volatility\nHAR 1-day vol {vol['har_daily_vol'] * 1e4:.0f} bp ({vol['har_annual_vol']:.1%} annualised); realized 22d {vol['realized_22d_annual_vol']:.1%}; ATR14 {vol['atr14_pips']:.0f} pips; ADR14 {vol['adr14_pips']:.0f} pips\n")
        st = self.limits_status()
        P(f"## Book\nEquity {st['equity']:,.2f} | open P&L {st['mtm']:+,.2f} | peak {st['peak_equity']:,.2f} | open risk at stops {self.open_risk():,.2f} ({self.open_risk() / st['equity']:.2%})\n")
        if self.book.positions:
            rows = []
            for p in self.book.positions:
                rows.append(dict(id=p.id, strategy=p.strategy, side="long" if p.side > 0 else "short", lots=p.lots, entry=p.entry, stop=p.stop,
                                 stop_dist_pips=round(abs(self.price - p.stop) / PIP, 1), stop_dist_adr=round(abs(self.price - p.stop) / PIP / vol["adr14_pips"], 2),
                                 pnl=round(p.pnl(self.price, self.cfg.pip_value_per_lot), 2), risk_at_stop=round(p.risk_at_stop(self.cfg.pip_value_per_lot), 2), exit=p.hard_exit))
            P(pd.DataFrame(rows).to_markdown(index=False) + "\n")
        else:
            P("No open positions.\n")
        P("## Limits (kill switches)")
        for k, v in st["checks"].items():
            P(f"- {k}: {v['value']:+.4f} vs limit {v['limit']} -> {'BREACHED' if v['breached'] else 'ok'}")
        P(f"\nTrading halted: **{st['trading_halted']}**\n")
        ve = self.var_es()
        P(f"## Value at risk ({ve['confidence']:.0%}, 1 day)")
        pa = ve["parametric"]
        P(f"- Parametric (HAR vol): VaR {pa['var']:,.2f}, ES {pa['es']:,.2f}, net exposure {pa['net_exposure_usd']:,.0f} USD")
        if "historical" in ve:
            h = ve["historical"]
            P(f"- Historical simulation ({h['days']} days, stop-aware): VaR {h['var']:,.2f}, ES {h['es']:,.2f}, worst day {h['worst_day']:,.2f}")
        mc = ve.get("monte_carlo_strategy_mix")
        if mc:
            for hzn in ("1_month", "1_year"):
                m = mc[hzn]
                P(f"- Monte Carlo strategy mix {hzn.replace('_', ' ')} at {mc['risk_per_trade']:.2%} risk/trade: median {m['median_return']:+.2%}, 5th pct {m['p5_return']:+.2%}, 95th pct {m['p95_return']:+.2%}, P(loss) {m['p_loss']:.0%}, median max DD {m['median_max_dd']:.2%}, P(breach {self.cfg.max_drawdown:.0%} DD) {m['p_breach_max_drawdown']:.1%}")
        P("")
        stx = self.stress()
        P("## Stress tests (open book replayed through the episode's path, stops honoured, gaps fill at the gap)")
        P(stx.to_markdown(index=False) + "\n" if not stx.empty else "No open positions.\n")
        ev = self.events_ahead(72)
        P("## High-impact events, next 72h")
        P(ev[["time", "event", "hours_ahead"]].to_markdown(index=False) + "\n" if not ev.empty else "none\n")
        P("## Component health (live trades vs validation record)")
        P(pd.DataFrame(self.component_health()).T.to_markdown() + "\n")
        return "\n".join(L)
