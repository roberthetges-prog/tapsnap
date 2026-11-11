"""Sanity tests for the risk engine on a synthetic book."""
import sys, math, json, tempfile
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import numpy as np, pandas as pd
from pathlib import Path
from eurusd.risk import RiskEngine, RiskConfig, Book, Position
from eurusd.data import load_ohlc

h1 = load_ohlc("H1").loc[:"2026-11-06"]
cfg = RiskConfig(max_risk_per_trade=0.005, max_open_risk=0.015, target_annual_vol=0.08, kelly_fraction=0.25)
tmp = Path(tempfile.mkdtemp()) / "book.json"
tmp.write_text(json.dumps({"equity": 10000, "peak_equity": 10000, "positions": [], "closed_trades": []}))
book = Book(tmp)
eng = RiskEngine(h1, cfg, book)
price = eng.price
vol = eng.vol_forecast()
assert 0.0002 < vol["har_daily_vol"] < 0.02 and 20 < vol["adr14_pips"] < 200, vol

# 1) sizing: hard cap 0.5% = 50 USD on a 50-pip stop -> 0.10 lots max; vol target / kelly may bind lower
d = eng.size("london_short", -1, price, price + 50e-4, decided_at=pd.Timestamp("2026-11-05 06:00", tz="UTC"))
assert d.approved and 0.01 <= d.lots <= 0.10, d
assert d.risk_amount <= 50.0 + 1e-6, d

# 2) event gate: NFP 2026-11-06 13:30 UTC -> an entry at 13:15 is blocked, at 10:00 the size is cut
blocked = eng.size("london_short", -1, price, price + 50e-4, decided_at=pd.Timestamp("2026-11-06 12:15", tz="UTC"))
assert not blocked.approved and any("release window" in r for r in blocked.reasons), blocked
cut = eng.size("london_short", -1, price, price + 50e-4, decided_at=pd.Timestamp("2026-11-06 09:00", tz="UTC"))
assert cut.approved and "event_cut_factor" in cut.caps, cut

# 3) open-risk budget: fill the book to the cap and the next trade is refused for lack of budget
book.add(strategy="cot_trend", side=-1, entry=price, stop=price + 100e-4, lots=0.15, opened="2026-11-05T22:00:00+00:00")  # 150 USD = 1.5 %
full = eng.size("london_short", -1, price, price + 50e-4, decided_at=pd.Timestamp("2026-11-05 06:00", tz="UTC"))
assert not full.approved and full.binding_cap == "open_risk_budget", full

# 4) VaR: historical stop-aware VaR cannot exceed the stop loss (plus 20 % gap allowance)
ve = eng.var_es()
assert ve["historical"]["var"] <= 0.15 * 100 * 10 * 1.2 + 1e-6, ve["historical"]
assert ve["parametric"]["var"] > 0

# 5) stress: SNB-type episode on a short EUR/USD position gains (EUR fell); synthetic +3 ADR gap stops it out at the gap
st = eng.stress()
snb = st[st.scenario.str.startswith("SNB")].iloc[0]
assert snb.book_pnl > 0, snb
gap = st[st.scenario.str.contains(r"\+3 ADR")].iloc[0]
assert gap.book_pnl < 0 and gap.positions_stopped == 1, gap

# 6) kill switch: a 3 % realized loss today halts trading
book.closed.append(dict(id=99, strategy="london_short", side=-1, entry=1.1, exit=1.13, lots=0.1, opened="x", closed=str(eng.now), pnl=-300.0, pips=-300, r=-3))
st2 = eng.limits_status()
assert st2["checks"]["daily_loss"]["breached"] and st2["trading_halted"], st2
halted = eng.size("london_short", -1, price, price + 50e-4, decided_at=pd.Timestamp("2026-11-05 06:00", tz="UTC"))
assert not halted.approved, halted
print("risk engine tests pass")

# ---- alerts
book2 = Book(tmp); book2.positions.clear(); book2.closed.clear(); book2.equity = 10000; book2.peak_equity = 10000
eng2 = RiskEngine(h1, cfg, book2)
codes = lambda e: {a["code"] for a in e.alerts()}
assert not ({"stop_near", "stop_touched", "open_loss", "halted"} & codes(eng2)), eng2.alerts()      # flat book: no position alerts
adr = eng2.vol_forecast()["adr14_pips"]
book2.add(strategy="macro_exposure", side=-1, entry=eng2.price, stop=eng2.price + 0.2 * adr * 1e-4, lots=0.1, opened=str(h1.index[-1]))
assert "stop_near" in codes(eng2), eng2.alerts()                                                     # stop 0.2 ADR away
book2.positions[0].stop = eng2.price - 0.0005                                                        # stop already behind the market for a short
assert "stop_touched" in codes(eng2), eng2.alerts()
book2.positions[0].stop = eng2.price + 0.02; book2.positions[0].entry = eng2.price - 0.0150           # 150 pips under water on 0.1 lots = -150 USD = -1.5 %
c2 = codes(eng2); assert "open_loss" in c2 and "limit_daily_loss_near" in c2, eng2.alerts()
book2.positions[0].entry = eng2.price - 0.0250                                                       # -2.5 % -> daily loss limit breached -> halted
c3 = codes(eng2); assert "limit_daily_loss" in c3 and "halted" in c3 and eng2.alerts()[0]["severity"] == "CRITICAL", eng2.alerts()
assert "cot_stale" not in codes(eng2)
print("alert tests pass")
