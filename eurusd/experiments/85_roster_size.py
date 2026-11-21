"""Round 26 (declared before running, descriptive): how many bots does the product need?

Question: with random rosters of 10, 25, 50 and 100 of the 100 bots (20 draws each), how do (a) the direction vote's
accuracy and (b) the levels' pinball loss and holding rates compare with the full roster, at 5 and 21 sessions,
2010-26? No adoption decision; the answer tells whether the roster could be cut (cheaper, faster) or should be grown.
Writes bots_roster_size.csv.
"""
import sys
from pathlib import Path
import numpy as np, pandas as pd
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B

rng = np.random.default_rng(11)
def pin(x, tau): return np.where(x >= 0, tau * x, (tau - 1) * x)
X = B.build(); rows = []
for h in (5, 21):
    P, LO, HI = B.walk_forward(X, h, verbose=False)
    idx = P.index; c = X["__close"].reindex(idx)
    lo, hi = np.log(LO.div(c, axis=0)), np.log(HI.div(c, axis=0))
    y, dn, up = X[f"y{h}"].reindex(idx), X[f"dn{h}"].reindex(idx), X[f"up{h}"].reindex(idx)
    m = (idx.year >= 2010) & y.notna().values & (y != 0).values & dn.notna().values & lo.notna().all(axis=1).values
    V = np.where(P > 0.5, 1.0, -1.0)
    for n in (10, 25, 50, 100):
        accs, losses, lh, uh = [], [], [], []
        for _ in range(20 if n < 100 else 1):
            cols = rng.choice(100, n, replace=False)
            side = np.sign(V[:, cols].sum(1)); side[side == 0] = 1.0
            accs.append(float((side[m] == y.values[m]).mean()))
            l = np.sort(lo.values[:, cols], axis=1); u = np.sort(hi.values[:, cols], axis=1); k = int(0.2 * n)
            l = l[:, k:n - k].mean(1); u = u[:, k:n - k].mean(1)
            losses.append(1e4 * float((pin(dn.values[m] - l[m], 0.2) + pin(up.values[m] - u[m], 0.8)).mean()))
            lh.append(float((dn.values[m] >= l[m]).mean())); uh.append(float((up.values[m] <= u[m]).mean()))
        rows.append({"h": h, "bots": n, "n_indep": round(m.sum() / h, 1), "vote_acc": np.mean(accs), "vote_acc_sd_across_rosters": np.std(accs),
                     "level_loss_bp": np.mean(losses), "loss_sd_across_rosters": np.std(losses), "lower_held": np.mean(lh), "upper_held": np.mean(uh)})
    print(h, "done", flush=True)
T = pd.DataFrame(rows); T.to_csv(B.RES / "bots_roster_size.csv", index=False)
pd.set_option("display.width", 200); print(T.round(4).to_string(index=False))
