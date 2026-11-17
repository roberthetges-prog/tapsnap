"""Tests of the 100-bot vote: fixed roster, exactly 100 votes, levels on the right side, no use of the future."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from eurusd import bots as B


def test_roster_is_fixed_and_varied():
    assert len(B.SPECS) == 100
    assert B.spec(7) == B.SPECS[7] and B.spec(7) == B.spec(7)            # a bot is its number, nothing else
    assert len({tuple(s["desk"]) for s in B.SPECS}) == 100                # no two bots share a desk
    assert {s["learner"] for s in B.SPECS} == set(B.LEARNERS) and {s["memory"] for s in B.SPECS} == set(B.MEMORY)
    assert all(len(s["desk"]) == B.DESK and set(s["desk"]) <= set(B.pool_columns()) for s in B.SPECS)


def test_count():
    P = pd.DataFrame(0.4, index=[0, 1, 2], columns=range(100))
    P.iloc[0, :68] = 0.6                      # 68 up / 32 down
    P.iloc[1, :50] = 0.6                      # tie
    P.iloc[2, :10] = 0.6; P.iloc[2, 90:] = np.nan   # 10 up / 80 down, 10 not voting yet
    T = B.count(P)
    assert (T.loc[0, "up"], T.loc[0, "down"], T.loc[0, "side"], T.loc[0, "cls"]) == (68, 32, 1, "fair")
    assert T.loc[1, "side"] == 0 and T.loc[1, "cls"] == "none"
    assert (T.loc[2, "up"], T.loc[2, "down"]) == (10, 80) and T.loc[2, "cls"] == "very wide" and T.loc[2, "side"] == -1


def test_no_future_and_levels():
    X = B.build()
    start = pd.Timestamp("2015-01-01", tz="UTC")
    rows = np.asarray(X.index.year == 2015)
    P, LO, HI, _ = B.run_fold(X, 21, start, rows)
    assert P.notna().all().all() and P.shape == (int(rows.sum()), 100)   # every bot votes on every session
    c = X["__close"].values[rows][:, None]
    assert (LO.values < c).all() and (HI.values > c).all()               # lower level below the price, upper above
    X2 = X.copy()
    fut = (X2["yend21"] >= start).values | X2["yend21"].isna().values
    for col in ("y21", "dn21", "up21"):
        X2.loc[fut, col] = -X2.loc[fut, col]                             # scramble everything not yet known at the fold start
    P2, LO2, HI2, _ = B.run_fold(X2, 21, start, rows)
    assert np.allclose(P.values, P2.values) and np.allclose(LO.values, LO2.values) and np.allclose(HI.values, HI2.values)


if __name__ == "__main__":
    for f in (test_roster_is_fixed_and_varied, test_count, test_no_future_and_levels):
        f(); print("ok", f.__name__)
