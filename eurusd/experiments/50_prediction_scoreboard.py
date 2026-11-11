"""Prediction scoreboard: out-of-sample accuracy of everything the engine predicts, honest baselines included.
Output: reports/prediction_scoreboard.md
"""
import sys, math
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import numpy as np, pandas as pd
from eurusd.arms.meta import combine

D = pd.read_parquet("/home/user/tapsnap/eurusd/data/processed/features_daily.parquet")
R = "/home/user/tapsnap/eurusd/experiments/results/arms/"
rows = []
def add(target, model, period, n, acc, base, note=""):
    rows.append({"target": target, "model": model, "period": period, "n": int(n), "accuracy": round(100 * acc, 1), "naive_baseline": round(100 * base, 1), "edge_pts": round(100 * (acc - base), 1), "note": note})
PERIODS = (("2010-26", "2010", "2026"), ("2016-26", "2016", "2026"), ("2023-26", "2023", "2026"))

# ---- 1. direction, daily: live exposure streams (walk-forward OOS)
ws = pd.read_parquet(R + "weak_signals_positions.parquet"); rt = pd.read_parquet(R + "regime_trend_positions.parquet")
J = pd.DataFrame({"c": ws["pos"], "d": rt["pos"], "fwd": ws["fwd_bp"]}).dropna()
J["pos"] = 0.5 * J["c"] + 0.5 * J["d"]
for lab, a, b in PERIODS:
    x = J.loc[a:b]; act = x[x.pos != 0]
    up = (x.fwd > 0).mean()
    add("direction next session", "live exposure (when active)", lab, len(act), (np.sign(act.pos) == np.sign(act.fwd)).mean(), max(up, 1 - up), f"active {len(act) / len(x):.0%} of sessions")
    both = x[(np.sign(x.c) == np.sign(x.d)) & (x.c != 0)]
    if len(both) > 50:
        add("direction next session", "both components agree", lab, len(both), (np.sign(both.pos) == np.sign(both.fwd)).mean(), max(up, 1 - up), f"{len(both) / len(x):.0%} of sessions")
# ---- 2. direction, weekly and monthly (non-overlapping), held position
for horizon, lab_h in ((5, "next 5 sessions"), (21, "next 21 sessions")):
    f = J["fwd"].rolling(horizon).sum().shift(-horizon + 1)
    K = pd.DataFrame({"pos": J["pos"], "f": f}).dropna().iloc[::horizon]
    for lab, a, b in PERIODS:
        x = K.loc[a:b]; act = x[x.pos != 0]; up = (x.f > 0).mean()
        add(f"direction {lab_h}", "live exposure (when active)", lab, len(act), (np.sign(act.pos) == np.sign(act.f)).mean(), max(up, 1 - up))
# ---- 3. range / volatility: walk-forward HAR-type forecast of next session's range
X = pd.DataFrame({"r1": D["range_pips"], "r5": D["range_pips"].rolling(5).mean(), "r21": D["range_pips"].rolling(21).mean(),
                  "ev": (D["n_high_next_24h"] > 0).astype(float), "mon": (D["dow"] == 4).astype(float)})   # dow of the closing session; next session Monday
y = D["range_pips"].shift(-1)
F = pd.concat([X, y.rename("y")], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
F = F[(F[["r1", "r5", "r21", "y"]] > 1.0).all(axis=1)]
pred = pd.Series(np.nan, index=F.index); med = pd.Series(np.nan, index=F.index); q80 = pd.Series(np.nan, index=F.index); resid_sd = pd.Series(np.nan, index=F.index)
for Y in range(2010, 2027):
    tr = F[F.index < pd.Timestamp(f"{Y}-01-01", tz="UTC")].iloc[:-1]; te = F[(F.index.year == Y)]
    if te.empty: continue
    A = np.column_stack([np.ones(len(tr)), np.log(tr[["r1", "r5", "r21"]].values), tr[["ev", "mon"]].values])
    beta, *_ = np.linalg.lstsq(A, np.log(tr["y"].values), rcond=None)
    At = np.column_stack([np.ones(len(te)), np.log(te[["r1", "r5", "r21"]].values), te[["ev", "mon"]].values])
    pred.loc[te.index] = np.exp(At @ beta)
    resid_sd.loc[te.index] = (np.log(tr["y"].values) - A @ beta).std()
    med.loc[te.index] = tr["y"].iloc[-250:].median(); q80.loc[te.index] = tr["y"].iloc[-250:].quantile(0.8)
G = pd.DataFrame({"y": F["y"], "p": pred, "med": med, "q80": q80, "sd": resid_sd, "r1": F["r1"]}).dropna()
for lab, a, b in PERIODS:
    x = G.loc[a:b]
    acc = ((x.p > x.med) == (x.y > x.med)).mean(); naive = ((x.r1 > x.med) == (x.y > x.med)).mean()
    add("next session range above/below 1-year median", "HAR + events (walk-forward)", lab, len(x), acc, naive, "baseline = yesterday's class")
    # big-day warning: predicted in top quintile -> realised above median
    hi = x[x.p > x.q80]
    if len(hi) > 30:
        add("'volatile day' call (forecast in top 20%) -> range above median", "HAR + events", lab, len(hi), (hi.y > hi.med).mean(), (x.y > x.med).mean(), "baseline = unconditional rate")
    lo = x[x.p < x.med * 0.85]
    if len(lo) > 30:
        add("'quiet day' call (forecast 15% below median) -> range below median", "HAR + events", lab, len(lo), (lo.y < lo.med).mean(), (x.y < x.med).mean(), "baseline = unconditional rate")
    # interval coverage: 80 % band for the range
    lo_b, hi_b = x.p * np.exp(-1.2816 * x.sd), x.p * np.exp(1.2816 * x.sd)
    add("next session range inside the 80% forecast band", "HAR + events", lab, len(x), ((x.y >= lo_b) & (x.y <= hi_b)).mean(), 0.80, "calibration target = 80%")
    mae = (x.p - x.y).abs().mean(); mae_n = (x.r1 - x.y).abs().mean()
    rows.append({"target": "next session range, mean abs error (pips)", "model": "HAR + events", "period": lab, "n": len(x), "accuracy": round(mae, 1), "naive_baseline": round(mae_n, 1), "edge_pts": round(mae_n - mae, 1), "note": "lower is better; baseline = yesterday's range"})
# ---- 4. price cone: close-to-close move inside the 1-sigma / 2-sigma daily cone from forecast vol (rv_21d as sigma)
c = pd.DataFrame({"f": D["fwd_1d"].abs(), "s": D["rv_21d_bp"]}).dropna()
for lab, a, b in PERIODS:
    x = c.loc[a:b]
    add("next close inside the 1-sigma cone", "21-day realised vol", lab, len(x), (x.f <= x.s).mean(), 0.683, "calibration target = 68.3%")
    add("next close inside the 2-sigma cone", "21-day realised vol", lab, len(x), (x.f <= 2 * x.s).mean(), 0.954, "calibration target = 95.4%")
T = pd.DataFrame(rows)
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(T.to_string(index=False))
md = ["# Prediction scoreboard (all out-of-sample, walk-forward)", "",
      "Accuracy in percent; `edge_pts` = accuracy minus the naive baseline (for calibration rows: minus the target coverage).",
      "Direction is barely predictable; range and volatility are strongly predictable. Any system claiming 70-90 % on direction has a leak.", "",
      T.to_markdown(index=False), ""]
open("/home/user/tapsnap/eurusd/reports/prediction_scoreboard.md", "w").write("\n".join(md))
T.to_csv("/home/user/tapsnap/eurusd/experiments/results/prediction_scoreboard.csv", index=False)
