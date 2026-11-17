"""Tests of the committee: roster size, vote counting, majority classes, and no use of the future."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from eurusd import committee as C


def test_roster():
    assert len(C.AGENTS) == 100 and len(set(C.AGENTS)) == 100
    assert sum(len([v for v in C.VIEWS.values() if v[0] == s]) for s in C.SCHOOLS) == 50
    assert all(len([v for v in C.VIEWS.values() if v[0] == s]) == 5 for s in C.SCHOOLS)


def test_tally_and_classes():
    P = pd.DataFrame(0.5, index=[0, 1, 2, 3], columns=C.AGENTS)
    P.iloc[0, :26] = 0.60; P.iloc[0, 26:40] = 0.40            # 26 up, 14 down -> 65 % of 40 voters: clear, up
    P.iloc[1, :10] = 0.60; P.iloc[1, 10:15] = 0.40            # 15 voters: below quorum
    P.iloc[2, :11] = 0.505                                   # inside the 51/49 band: nobody has a view
    P.iloc[3, :5] = 0.60; P.iloc[3, 5:50] = 0.30; P.iloc[3, 50:] = np.nan   # 45 of 50 down: strong
    T = C.tally(P)
    assert (T.loc[0, "up"], T.loc[0, "down"], T.loc[0, "no_view"]) == (26, 14, 60) and T.loc[0, "cls"] == "clear" and T.loc[0, "side"] == 1
    assert T.loc[1, "cls"] == "none" and T.loc[2, "voters"] == 0 and T.loc[2, "cls"] == "none"
    assert T.loc[3, "cls"] == "strong" and T.loc[3, "side"] == -1 and T.loc[3, "no_view"] == 50
    assert C.class_of(0.65, 40, 1.0) == "clear" and C.class_of(0.9, 10, 1.0) == "none" and C.class_of(0.52, 30, -1.0) == "split"


def test_no_future_in_fit():
    """Changing every outcome that was not yet known at the fold start must not change any analyst's forecast."""
    X = C.build_frame()
    start = pd.Timestamp("2015-01-01", tz="UTC")
    rows = np.asarray(X.index.year == 2015)
    a = C.fit_predict(X, 21, start, rows)
    X2 = X.copy()
    fut = (X2["yend21"] >= start).values | X2["yend21"].isna().values
    X2.loc[fut, "y21"] = -X2.loc[fut, "y21"]
    X2.loc[X2["__ct"] >= start, "ws_fwd_1d"] = -X2.loc[X2["__ct"] >= start, "ws_fwd_1d"]
    b = C.fit_predict(X2, 21, start, rows)
    assert np.allclose(a.values, b.values, equal_nan=True)
    assert a.notna().any(axis=0).sum() >= 80                 # most analysts have a model by 2015
    assert ((a.dropna(axis=1, how="all") >= 0) & (a.dropna(axis=1, how="all") <= 1)).all().all()


if __name__ == "__main__":
    for f in (test_roster, test_tally_and_classes, test_no_future_in_fit):
        f(); print("ok", f.__name__)
