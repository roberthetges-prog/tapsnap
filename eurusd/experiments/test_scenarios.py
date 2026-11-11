"""Scenario engine tests on a temporary ledger (no network)."""
import sys, json, math, tempfile
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
from pathlib import Path
import numpy as np, pandas as pd
import eurusd.scenarios as SC

tmp = Path(tempfile.mkdtemp())
SC.DIR, SC.LEDGER, SC.STATE = tmp, tmp / "ledger.csv", tmp / "positions.json"
# synthetic ledger: 130 sessions; 'base' drifts +1 bp, 'weak_signals_sign' -2 bp, 'positioning_only' +4 bp steadily
rng = np.random.default_rng(1)
rows = []
for i in range(261):
    ct = str(pd.Timestamp("2026-01-01", tz="UTC") + pd.Timedelta(days=i))
    for name, mu in (("base", 1.0), ("weak_signals_sign", -3.0), ("positioning_only", 4.0), ("always_long", -3.0)):
        pnl = -1.0 if i == 0 else mu + rng.normal(0, 10)
        rows.append([ct, name, 1.1, pnl, 0.0, False, 1.0, 1.0, None, 1.25])
pd.DataFrame(rows, columns=SC.COLS).to_csv(SC.LEDGER, index=False)
SC.STATE.write_text(json.dumps({"_last": rows[-1][0], "_start": rows[0][0], "pos": {}}))
lb = SC.leaderboard().set_index("scenario")
assert lb.loc["base", "sessions"] == 260 and lb.loc["base", "verdict"].startswith("watch (next gate 500"), lb
assert lb.loc["weak_signals_sign", "verdict"] == "DISPOSE", lb
assert lb.loc["positioning_only", "verdict"] == "PROMOTE?", lb
assert lb.loc["always_long", "verdict"] == "yardstick", lb          # benchmarks are never disposed
notes = SC.review(apply=True)
assert any("disposed weak_signals_sign" in n for n in notes) and any("PROMOTE? positioning_only" in n for n in notes), notes
st = json.loads(SC.STATE.read_text())
assert "weak_signals_sign" in st["retired"] and "positioning_only" not in st.get("retired", {})
assert SC.leaderboard().set_index("scenario").loc["weak_signals_sign", "verdict"].startswith("DISPOSED")
assert len(pd.read_csv(SC.LEDGER)) == len(rows)                     # disposal never deletes results
# 130 sessions: only a disaster (Sharpe < -1) is disposed; a challenger cannot be promoted yet
pd.DataFrame(rows[:131 * 4], columns=SC.COLS).to_csv(SC.LEDGER, index=False)
SC.STATE.write_text(json.dumps({"_last": rows[131 * 4 - 1][0], "_start": rows[0][0], "pos": {}}))
mid = SC.leaderboard().set_index("scenario")
assert mid.loc["positioning_only", "verdict"] != "PROMOTE?", mid
assert mid.loc["base", "verdict"].startswith("watch (next gate 250"), mid
# early ledger: verdict is 'too early'
pd.DataFrame(rows[:160], columns=SC.COLS).to_csv(SC.LEDGER, index=False)
SC.STATE.write_text(json.dumps({"_last": rows[159][0], "_start": rows[0][0], "pos": {}}))
assert SC.leaderboard().set_index("scenario").loc["base", "verdict"].startswith("too early")
# expression parser
assert abs(SC._target("0.5*weak_sign + 0.5*positioning", {"weak_sign": 1.0, "positioning": -1.34}) + 0.17) < 1e-9
assert SC._target("const:-1", {}) == -1.0
print("scenario tests pass")
