"""Replay the 12 pre-registered paper scenarios through the LIVE scenario engine over history (2010-2026).
Signals at each session are fitted on earlier sessions only (daily expanding refit). Purposes:
  1. check the live engine against the walk-forward research records;
  2. calibrate the 120-session keep/dispose rule: how often does each scenario look bad / good over 6 months?
Output: experiments/results/scenario_replay/ledger.csv, reports/scenario_replay.md
"""
import sys, json, math
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
from pathlib import Path
import numpy as np, pandas as pd
import eurusd.scenarios as SC
from eurusd.data import load_ohlc

OUT = Path("/home/user/tapsnap/eurusd/experiments/results/scenario_replay")
SC.DIR, SC.LEDGER, SC.STATE = OUT, OUT / "ledger.csv", OUT / "positions.json"
if "--analyse" not in sys.argv:
    for p in (SC.LEDGER, SC.STATE):
        p.unlink(missing_ok=True)
    SC.STATE.write_text(json.dumps({"_last": "2009-12-31 22:00:00+00:00", "_start": "2009-12-31 22:00:00+00:00", "pos": {}}))
    D = pd.read_parquet("/home/user/tapsnap/eurusd/data/processed/features_daily.parquet")
    h1 = load_ohlc("H1")
    print(SC.run(D, h1, 1.25), flush=True)

L = pd.read_csv(SC.LEDGER, parse_dates=["session_close"])
P = L.pivot(index="session_close", columns="scenario", values="pnl_bp").fillna(0.0)
roles = {k: v["role"] for k, v in json.loads(SC.CFG.read_text())["scenarios"].items()}
def sr(x): return x.mean() / x.std() * math.sqrt(252) if x.std() > 0 else 0.0
rows = []
W = 120
roll = P.rolling(W).apply(lambda x: x.mean() / x.std() * math.sqrt(252) if x.std() > 0 else 0.0, raw=True).dropna()
base_roll = roll["base"]
for s in P.columns:
    x = P[s]
    r = roll[s]
    half1 = P[s].rolling(W).apply(lambda v: v[:W // 2].sum(), raw=True).reindex(r.index)
    half2 = P[s].rolling(W).apply(lambda v: v[W // 2:].sum(), raw=True).reindex(r.index)
    rows.append({"scenario": s, "role": roles[s], "SR_2010_26": sr(x), "SR_2016_26": sr(x.loc["2016":]), "SR_2023_26": sr(x.loc["2023":]),
                 "last120_bp": x.iloc[-W:].sum(), "last120_SR": sr(x.iloc[-W:]),
                 "P(120d SR<0)": (r < 0).mean(), "median_120d_SR": r.median(), "p10_120d_SR": r.quantile(0.1), "p90_120d_SR": r.quantile(0.9),
                 "P(PROMOTE vs base)": ((r >= base_roll + 0.3) & (half1 > 0) & (half2 > 0)).mean() if s != "base" else np.nan,
                 "bp_per_yr": x.mean() * 252, "max_dd_bp": (x.cumsum() - x.cumsum().cummax()).min()})
T = pd.DataFrame(rows).sort_values("SR_2010_26", ascending=False)
pd.set_option("display.width", 250)
print(T.round(2).to_string(index=False))
md = ["# Scenario replay 2010-2026 through the live paper engine", "",
      "Net bp per unit, 1.2 pips per unit turnover (London control: 1.2 pips per round trip). Signals refitted every session on prior data only.",
      "`P(120d SR<0)` = share of all rolling 120-session windows in which the scenario's Sharpe was negative, i.e. how often the six-month DISPOSE rule would have fired.",
      "`P(PROMOTE vs base)` = share of windows in which the PROMOTE? rule would have fired.", "", T.round(2).to_markdown(index=False), ""]
Path("/home/user/tapsnap/eurusd/reports/scenario_replay.md").write_text("\n".join(md))
T.to_csv(OUT / "summary.csv", index=False)
