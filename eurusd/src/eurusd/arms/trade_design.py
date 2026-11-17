"""Arm AB ("trade_design"): entry / take-profit / stop / time-limit designs for agreement-rule calls, with a stated
win probability, and how much of that win rate is edge rather than barrier geometry.

EVERYTHING IN THIS DOCSTRING WAS WRITTEN ON 2026-11-17 BEFORE ANY TRADE OUTCOME WAS COMPUTED (a copy with a timestamp
is in experiments/results/arms/logs/trade_design_declaration.txt). Only structural facts were looked at first: the
session grid, how hourly bars map to sessions, the shape of the 2023 data hole, the yearly mean of ATR14.

SIGNAL (not new, not tuned here)
  The walk-forward three-signal agreement rule: sign(cot_z52) = sign(d_spread2y_20) = sign(house score), the house
  score fitted for test year Y on rows whose outcome was known before Y-01-01 (`committee.build_frame`,
  `committee._fold_columns`, exactly as `experiments/70_committee.py::agreement_side`). Calls exist from 2006.
  Step 0 (reconciliation, before anything else): its plain-hold accuracy at 21 / 42 / 63 sessions, phase-averaged,
  2010-26, recomputed with this module's own scoring, must equal the published 58.3 / 63.3 / 66.7 % to 0.1 point.

TRADE MECHANICS (one set of conventions for every design)
  * Entry: at the close of a session on which the rule calls a direction, at that session's close price
    (feature-store NY-close session grid: sessions run 22:00 -> 22:00 UTC).
  * One trade at a time. A trade ends ONLY by its take-profit, its stop or its time limit (a flip of the rule does not
    close it). The next trade is opened at the first session close AT OR AFTER the previous exit on which the rule
    calls (so a trade that ends on time may be renewed on the same close, and after an intraday barrier exit the
    earliest new entry is that session's close). The sequence starts at the first call (2006). Trades per year reported.
  * ATR: the feature store's `atr14_pips` = Wilder ATR(14) of the NY-close daily sessions, as known at the entry
    close. This is the unit in which the project's path / level probabilities were calibrated (a level 2 ATR14 away
    untouched in 10 sessions 69 %, ...). NOT the 13-week weekly ATR of `swing.py` (about 2.2 times larger).
  * Barriers: take-profit = entry + side x tp x ATR, stop = entry - side x sl x ATR, fixed at entry.
  * Path: the hourly bars (`load_ohlc("H1")`) from the entry close to the close of session entry + H. Touch is judged
    on the bar series as given (HistData bid) for both sides; the whole spread is charged as the round-turn cost.
    Stop fills at the stop, or at the bar's open when the bar opens beyond it (gap). Take-profit fills at its level
    (no gap improvement). If one hourly bar touches both barriers, the 1-minute bars of that hour decide; if they
    cannot (same minute, or no 1-minute data) the STOP is assumed first.
  * Time limit: exit at the close of session entry + H. An entry needs a complete window (entry + H inside the data).
  * Costs: 1.2 pips per round turn (headline), 0.6 as sensitivity, plus overnight carry exactly as `swing.simulate`:
    for every night held, side x (EUR overnight rate - Fed target) x days / 360 on the previous close.
  * WIN = net pips after costs and carry > 0. A take-profit exit is a win, a stop exit a loss, a time exit either.
  * A trade belongs to the era of its ENTRY session (index year, as `70_committee.acc_row`).
  * Data hole 2023-02-03 .. 2023-07-28 (about 7 of 24 hourly bars missing on most sessions): trades are simulated on
    the bars that exist (a barrier jumped across missing hours is filled by the gap rule above); every trade alive in
    the hole is flagged, results are also shown without those trades, and for the chosen design the flagged trades
    are cross-checked against Yahoo daily highs / lows.

THE 12 CANDIDATES (counted; barriers in ATR14 units; nothing else will be run as a candidate)
   #  name             take-profit  stop  time limit   geometry (driftless first-touch odds, sl / (tp + sl))
   1  tp1_sl2_h21          1.0      2.0      21         67 %
   2  tp1.5_sl3_h21        1.5      3.0      21         67 %
   3  tp1_sl3_h21          1.0      3.0      21         75 %
   4  tp2_sl2_h21          2.0      2.0      21         50 %  symmetric (earlier work: tb21_2atr)
   5  tp1.5_sl3_h42        1.5      3.0      42         67 %
   6  tp2_sl3_h42          2.0      3.0      42         60 %
   7  tp2_sl4_h42          2.0      4.0      42         67 %
   8  tp3_sl3_h42          3.0      3.0      42         50 %  symmetric (earlier work: tb42_3atr)
   9  tp3_sl4_h42          3.0      4.0      42         57 %
  10  tp3_sl2_h42          3.0      2.0      42         40 %  inverse (target farther than the stop)
  11  hold_h21             none     none     21         reference: plain time-exit hold
  12  hold_h42             none     none     42         reference: plain time-exit hold

REPORTED FOR EVERY DESIGN AND ERA (2010-26, 2016-26, 2023-26, and the split 2010-17 / 2018-26)
  trades, trades per year, win rate with Wilson 95 % interval, average win and loss (net pips), net expectancy per
  trade in pips, in ATR units and in units of the stop distance, its standard error, share of exits by take-profit /
  stop / time, mean holding sessions, net pips per year.
  RANDOM-ENTRY BASELINE (geometry alone): the same design, the same number of trades with the same spacing (the era's
  real entry sessions moved by one random circular shift inside the era's eligible sessions) and an independent
  random direction per trade; 1,000 draws, fixed seed. Baseline win rate / expectancy = mean over draws; also the
  2.5-97.5 % range of the draws and the share of draws at or above the real number (one-sided p).
  EDGE = win rate minus baseline win rate; expectancy minus baseline expectancy (which should be about minus costs).

STATED PROBABILITY (walk-forward)
  For a trade entered in year Y the probability that would have been STATED for its design is the win rate of that
  design's own trades CLOSED before Y-01-01 (all walk-forward trades since 2006; no statement with fewer than 20
  closed trades). Stated versus realised by era, for every design. Next to it the geometry-only statement (win rate
  of the same design over ALL sessions and both directions whose windows closed before Y-01-01) and the Brier score
  of each, so that "is a stated 70 % a realised 70 %" and "does the statement beat pure geometry" are both answered.

SELECTION RULE (the only choice in this arm; made on 2010-2017 entries, 1.2 pips, carry included)
  Among the ten barrier designs (1-10) with a win rate of at least 60 % on their 2010-2017 trades, the one with the
  highest net expectancy per trade in pips on those trades. If none reaches 60 %, the design with the highest
  2010-2017 win rate is carried forward and the arm is a FAIL at the selection stage.
PASS BAR (primary test; chosen design on trades entered 2018-2026, which the choice never saw; 1.2 pips, carry)
  (a) win rate >= 60 %;
  (b) the Wilson 95 % lower bound of that win rate is above the design's random-entry baseline win rate in 2018-26;
  (c) net expectancy per trade > 0;
  (d) net expectancy per trade >= the plain hold's with the same time limit (2018-26) minus one standard error,
      the standard error being that of the chosen design's own mean net pips per trade.
  All four -> PASS, otherwise FAIL, said plainly.

DESCRIPTIVE ONLY (labelled as such; none of it can change the choice or the verdict)
  * stale placebo: the agreement signal of 63 sessions earlier through the chosen design (same sequencing);
  * shuffled direction: the chosen design's real entry dates with random directions (expectancy about minus costs);
  * phase-averaged version: every session with a call treated as an entry (no sequencing), against every session and
    both directions; shows whether the sequenced record is a lucky phase;
  * the bar's (d) with the standard error of the difference, per-year and per-session-held expectancy, 0.6 pips,
    results without the trades alive in the 2023 data hole;
  * spot check of ten trades of the chosen design against the raw hourly bars by an independent plain loop.

POST-RUN NOTES (added after the results existed; nothing above this line was changed)
  * The rule's first walk-forward call is in 2007, not 2006 (2006 has none); the trade history starts there.
  * No hourly bar ever touched both barriers of any simulated trade (0 of 147,666), so the 1-minute bars were never
    needed. Testing that unused path on two made-up cases exposed a timezone bug in it, fixed; no result depends on it.
  * Added, descriptive: the four bar tests applied to every barrier design in 2018-26 (`bar_all_designs`), so that it
    is visible whether a different pick would have passed.
"""
from __future__ import annotations

import importlib.util
import math
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.arms.swing import wilson  # noqa: E402

RES = ROOT / "experiments" / "results" / "arms"
PROC = ROOT / "data" / "processed"
ARM = "trade_design"
PIP = 1e-4
# name, take-profit (ATR14), stop (ATR14), time limit (sessions)          -- the 12 declared candidates, in order
DESIGNS = (("tp1_sl2_h21", 1.0, 2.0, 21), ("tp1.5_sl3_h21", 1.5, 3.0, 21), ("tp1_sl3_h21", 1.0, 3.0, 21), ("tp2_sl2_h21", 2.0, 2.0, 21),
           ("tp1.5_sl3_h42", 1.5, 3.0, 42), ("tp2_sl3_h42", 2.0, 3.0, 42), ("tp2_sl4_h42", 2.0, 4.0, 42), ("tp3_sl3_h42", 3.0, 3.0, 42),
           ("tp3_sl4_h42", 3.0, 4.0, 42), ("tp3_sl2_h42", 3.0, 2.0, 42), ("hold_h21", None, None, 21), ("hold_h42", None, None, 42))
assert len(DESIGNS) == 12
BARRIER = [d[0] for d in DESIGNS if d[1] is not None]
SPEC = {d[0]: d for d in DESIGNS}
ERAS = (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026), ("2010-17", 2010, 2017), ("2018-26", 2018, 2026))
SEL_ERA, CONF_ERA = "2010-17", "2018-26"
MIN_WIN_SEL = 0.60
N_DRAWS = 1000
SEED = 20261117
MIN_STATED = 20
STALE = 63
HOLE = (pd.Timestamp("2023-02-03 22:00", tz="UTC"), pd.Timestamp("2023-07-29 00:00", tz="UTC"))
REASONS = ("take-profit", "stop", "time")
FRAME_CACHE = PROC / "trade_design_frame.parquet"
LOOKUP_CACHE = PROC / "trade_design_lookup.parquet"


# ============================================================================= inputs
def _committee_test():
    spec = importlib.util.spec_from_file_location("committee_test_70", ROOT / "experiments" / "70_committee.py")
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def agreement_side(X: pd.DataFrame) -> pd.Series:
    """The walk-forward three-signal agreement call (+1 / -1 / 0) per session; own copy of the fold loop."""
    from eurusd import committee as C
    out = pd.Series(np.nan, index=X.index)
    for Y in C.TEST_YEARS:
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC")
        known = (X["yend21"] < start).values & X["y21"].notna().values
        rows = X.index.year == Y
        if rows.any():
            out[rows] = C._fold_columns(X, known)["@agree"][rows]
    return out.fillna(0.0)


def load_frame(refresh: bool = False, verbose: bool = True) -> pd.DataFrame:
    """Session frame 2003+ (index = session start, feature-store grid): close, close_time, cdate, atr (price units),
    acc_pct, the agreement call `ag` and the plain-hold labels. Cached (the committee frame takes a while)."""
    if FRAME_CACHE.exists() and not refresh:
        return pd.read_parquet(FRAME_CACHE)
    warnings.filterwarnings("ignore")
    from eurusd import committee as C
    t0 = time.time()
    X = C.build_frame()
    ag = agreement_side(X)
    ref = _committee_test().agreement_side(X)
    assert (ag.values == ref.values).all(), "own agreement series differs from experiments/70_committee.py"
    D = pd.read_parquet(PROC / "features_daily.parquet", columns=["close", "close_time", "atr14_pips"])
    D.index = pd.DatetimeIndex(D.index).as_unit("us")
    Xs = X.reindex(D.index)
    assert np.allclose(Xs["__close"].values, D["close"].values), "committee frame and feature store closes differ"
    S = pd.DataFrame({"close": D["close"].values, "close_time": pd.DatetimeIndex(D["close_time"]).as_unit("us"),
                      "cdate": pd.DatetimeIndex(Xs["__cdate"]), "atr": D["atr14_pips"].values * PIP, "acc_pct": Xs["acc_pct"].values,
                      "ag": ag.reindex(D.index).values, "y21": Xs["y21"].values, "y42": Xs["y42"].values, "y63": Xs["y63"].values}, index=D.index)
    S.to_parquet(FRAME_CACHE)
    if verbose:
        print(f"frame built in {time.time() - t0:.0f}s: {len(S)} sessions, {int((S.ag != 0).sum())} with a call", flush=True)
    return S


def load_h1() -> pd.DataFrame:
    from eurusd.data import load_ohlc
    h1 = load_ohlc("H1").loc["2003":]
    return h1[~h1.index.duplicated(keep="last")][["open", "high", "low", "close"]]


# ============================================================================= step 0: reconciliation
def reconcile(S: pd.DataFrame) -> pd.DataFrame:
    """Plain-hold accuracy of the agreement rule, own scoring: every session with a call is scored on the sign of the
    next h sessions (phase-averaged; independent calls = scored sessions / h); also one non-overlapping grid."""
    pub = pd.read_csv(RES / "committee_benchmark.csv")
    pub = pub[pub.who == "agreement rule"].set_index(["h", "era"])
    rows = []
    for h in (21, 42, 63):
        y = S[f"y{h}"].values
        for era, a, b in ERAS[:3]:
            yr = S.index.year
            m = (yr >= a) & (yr <= b) & (S.ag.values != 0) & np.isfinite(y) & (y != 0)
            acc = float((S.ag.values[m] == y[m]).mean())
            n_ind = m.sum() / h
            lo, hi = wilson(int(round(acc * n_ind)), max(int(round(n_ind)), 1))
            g = np.zeros(len(S), dtype=bool)
            g[::h] = True
            mg = m & g
            p = pub.loc[(h, era)]
            rows.append({"h": h, "era": era, "n_days": int(m.sum()), "n_indep": round(n_ind, 1), "acc_own": acc, "lo": lo, "hi": hi,
                         "per_year": n_ind / (b - a + 1), "acc_published": float(p.acc), "n_days_published": int(p.n_days),
                         "diff_points": 100 * (acc - float(p.acc)), "one_grid_n": int(mg.sum()),
                         "one_grid_acc": float((S.ag.values[mg] == y[mg]).mean()) if mg.any() else np.nan})
    return pd.DataFrame(rows)


# ============================================================================= the trade engine
def _first(mask: np.ndarray) -> int:
    k = int(np.argmax(mask))
    return k if mask[k] else 10 ** 9


def _resolve_m1(cases: list[dict]) -> dict:
    """For hourly bars that touch both barriers: which came first on the 1-minute bars of that hour?
    Returns {case index: 0 take-profit / 1 stop}; same minute or no minute data -> stop (pessimistic)."""
    out = {}
    if not cases:
        return out
    import pyarrow.dataset as ds
    dset = ds.dataset(PROC / "EURUSD_M1.parquet")
    for i, cs in enumerate(cases):
        t0 = pd.Timestamp(cs["bar_time"])
        t0 = t0.tz_localize("UTC") if t0.tzinfo is None else t0
        t1 = t0 + pd.Timedelta(hours=1)
        m1 = dset.to_table(filter=(ds.field("time") >= t0) & (ds.field("time") < t1), columns=["time", "high", "low"]).to_pandas()
        m1 = (m1.reset_index() if "time" not in m1.columns else m1).sort_values("time")
        cs["m1_bars"] = len(m1)
        if not len(m1):
            out[i] = 1
            continue
        hi, lo = m1["high"].values, m1["low"].values
        if cs["side"] > 0:
            ktp, ksl = _first(hi >= cs["tp_px"]), _first(lo <= cs["sl_px"])
        else:
            ktp, ksl = _first(lo <= cs["tp_px"]), _first(hi >= cs["sl_px"])
        out[i] = 0 if ktp < ksl else 1
    return out


def build_lookup(S: pd.DataFrame, h1: pd.DataFrame | None = None, refresh: bool = False, verbose: bool = True) -> pd.DataFrame:
    """Outcome of every design entered at EVERY session close, long and short (the real trades, the random-entry
    baseline, the placebo and the shuffles are all read from this one table). Long format, cached.
    Columns: sess (session number), design, side, x (exit session number), exit_time, exit_px, reason (0 tp / 1 stop /
    2 time), gross_pips, carry_pips, amb (0 no / 1 both barriers in one hour, decided by 1-minute bars / 2 the same,
    undecidable -> stop)."""
    if LOOKUP_CACHE.exists() and not refresh:
        return pd.read_parquet(LOOKUP_CACHE)
    t_start = time.time()
    h1 = load_h1() if h1 is None else h1
    tb = h1.index.as_unit("us").tz_convert("UTC").tz_localize(None).values.astype("datetime64[us]")
    ho, hh, hl = h1["open"].values, h1["high"].values, h1["low"].values
    ct = pd.DatetimeIndex(S["close_time"]).tz_convert("UTC").tz_localize(None).values.astype("datetime64[us]")
    c, atr = S["close"].values, S["atr"].values
    n = len(S)
    i_close = np.searchsorted(tb, ct, side="left")          # first hourly bar at or after each session close
    sess_of_bar = np.searchsorted(ct, tb, side="right")     # the session in which an hourly bar trades (close_time > bar start)
    days = np.r_[np.diff(S["cdate"].values).astype("timedelta64[D]").astype(float), 1.0]
    night = np.nan_to_num(S["acc_pct"].values) / 100.0 * days / 360.0 * c / PIP      # long carry in pips for the night after session k
    cs = np.r_[0.0, np.cumsum(night)]                        # carry of a long from close e to close x = cs[x] - cs[e]
    rows, cases = [], []
    by_h = {H: [d for d in DESIGNS if d[3] == H] for H in (21, 42)}
    for e in range(n):
        if not (np.isfinite(atr[e]) and atr[e] > 0):
            continue
        for H, ds_ in by_h.items():
            if e + H > n - 1:
                continue
            i0, i1 = i_close[e], i_close[e + H]
            H_, L_, O_ = hh[i0:i1], hl[i0:i1], ho[i0:i1]
            for name, tp, sl, _ in ds_:
                for side in (1, -1):
                    x, reason, px, amb, bt = e + H, 2, c[e + H], 0, ct[e + H]
                    if tp is not None:
                        tp_px, sl_px = c[e] + side * tp * atr[e], c[e] - side * sl * atr[e]
                        if side > 0:
                            ktp, ksl = _first(H_ >= tp_px), _first(L_ <= sl_px)
                        else:
                            ktp, ksl = _first(L_ <= tp_px), _first(H_ >= sl_px)
                        k = min(ktp, ksl)
                        if k < 10 ** 9:
                            b = i0 + k
                            x, bt = int(sess_of_bar[b]), tb[b]
                            if ktp == ksl:
                                amb = 2
                                cases.append({"row": len(rows), "bar_time": tb[b], "side": side, "tp_px": tp_px, "sl_px": sl_px, "open": O_[k]})
                                reason = 1
                            else:
                                reason = 0 if ktp < ksl else 1
                            if reason == 0:
                                px = tp_px
                            else:
                                px = min(O_[k], sl_px) if side > 0 else max(O_[k], sl_px)
                    rows.append([e, name, side, x, bt, px, reason, side * (px - c[e]) / PIP, side * (cs[x] - cs[e]), amb])
        if verbose and e % 1500 == 0:
            print(f"  lookup: session {e}/{n}", flush=True)
    res = _resolve_m1(cases)
    for i, cs_ in enumerate(cases):
        r = rows[cs_["row"]]
        if cs_.get("m1_bars", 0) and res[i] == 0:        # 1-minute bars say the take-profit came first
            r[5], r[6], r[9] = cs_["tp_px"], 0, 1
            r[7] = cs_["side"] * (cs_["tp_px"] - c[r[0]]) / PIP
        elif cs_.get("m1_bars", 0):
            r[9] = 1
    L = pd.DataFrame(rows, columns=["sess", "design", "side", "x", "exit_time", "exit_px", "reason", "gross_pips", "carry_pips", "amb"])
    L["exit_time"] = pd.DatetimeIndex(L["exit_time"]).tz_localize("UTC")
    L.to_parquet(LOOKUP_CACHE)
    if verbose:
        print(f"lookup built in {time.time() - t_start:.0f}s: {len(L)} rows, {len(cases)} hours touched both barriers "
              f"({int((L.amb == 2).sum())} undecidable -> stop)", flush=True)
    return L


class Table:
    """The lookup as (sessions x 2 sides) arrays per design. Side column 0 = long, 1 = short."""

    def __init__(self, S: pd.DataFrame, L: pd.DataFrame):
        self.S, self.n = S, len(S)
        self.year = S.index.year.values
        self.ct = pd.DatetimeIndex(S["close_time"])
        self.a = {}
        for name, g in L.groupby("design", sort=False):
            j = np.where(g["side"].values > 0, 0, 1)
            e = g["sess"].values
            d = {"x": np.full((self.n, 2), -1, dtype=np.int64), "reason": np.full((self.n, 2), -1, dtype=np.int64)}
            for col in ("gross_pips", "carry_pips", "exit_px"):
                d[col] = np.full((self.n, 2), np.nan)
                d[col][e, j] = g[col].values
            d["x"][e, j] = g["x"].values
            d["reason"][e, j] = g["reason"].values
            d["amb"] = np.zeros((self.n, 2), dtype=np.int64)
            d["amb"][e, j] = g["amb"].values
            d["exit_time"] = np.full((self.n, 2), np.datetime64("NaT"), dtype="datetime64[us]")
            d["exit_time"][e, j] = pd.DatetimeIndex(g["exit_time"]).tz_convert("UTC").tz_localize(None).values.astype("datetime64[us]")
            d["valid"] = d["x"][:, 0] >= 0
            self.a[name] = d

    def net(self, design: str, cost: float) -> np.ndarray:
        d = self.a[design]
        return d["gross_pips"] - cost + d["carry_pips"]


def sequence(T: Table, design: str, signal: np.ndarray) -> pd.DataFrame:
    """One trade at a time: enter at the first session close at or after the previous exit on which `signal` calls."""
    d, S = T.a[design], T.S
    _, tp, sl, H = SPEC[design]
    out, e = [], 0
    while e < T.n:
        if signal[e] == 0 or not d["valid"][e] or not np.isfinite(signal[e]):
            e += 1
            continue
        side = int(signal[e])
        j = 0 if side > 0 else 1
        x = int(d["x"][e, j])
        atr_p = S["atr"].values[e] / PIP
        entry = S["close"].values[e]
        et = pd.Timestamp(d["exit_time"][e, j], tz="UTC")
        out.append({"design": design, "sess": e, "entry_time": T.ct[e], "year": int(T.year[e]), "side": side, "entry_px": entry, "atr_pips": atr_p,
                    "tp_px": entry + side * tp * atr_p * PIP if tp else np.nan, "sl_px": entry - side * sl * atr_p * PIP if sl else np.nan,
                    "limit_time": T.ct[e + H], "exit_time": et, "exit_px": float(d["exit_px"][e, j]), "exit_reason": REASONS[int(d["reason"][e, j])],
                    "gross_pips": float(d["gross_pips"][e, j]), "carry_pips": float(d["carry_pips"][e, j]), "hold_sessions": x - e,
                    "amb": int(d["amb"][e, j]), "in_hole": bool(T.ct[e] < HOLE[1] and et > HOLE[0])})
        e = max(x, e + 1)                     # the exit session's close is the earliest next entry
    return pd.DataFrame(out)


# ============================================================================= statistics
def era_years(S: pd.DataFrame, a: int, b: int) -> float:
    end = min(pd.Timestamp(f"{b + 1}-01-01", tz="UTC"), pd.DatetimeIndex(S["close_time"])[-1])
    return (end - pd.Timestamp(f"{a}-01-01", tz="UTC")).days / 365.25


def stats(t: pd.DataFrame, design: str, cost: float, years: float) -> dict:
    _, tp, sl, H = SPEC[design]
    n = len(t)
    if n == 0:
        return {"trades": 0, "trades_per_year": 0.0}
    net = (t["gross_pips"] - cost + t["carry_pips"]).values
    win = net > 0
    k = int(win.sum())
    lo, hi = wilson(k, n)
    return {"trades": n, "trades_per_year": n / years, "share_long": float((t["side"] > 0).mean()), "win_rate": k / n, "win_lo": lo, "win_hi": hi,
            "avg_win_pips": float(net[win].mean()) if k else np.nan, "avg_loss_pips": float(net[~win].mean()) if k < n else np.nan,
            "exp_pips": float(net.mean()), "exp_se": float(net.std(ddof=1) / math.sqrt(n)) if n > 1 else np.nan,
            "exp_atr": float((net / t["atr_pips"].values).mean()), "exp_stop_units": float((net / (sl * t["atr_pips"].values)).mean()) if sl else np.nan,
            "gross_pips": float(t["gross_pips"].mean()), "carry_pips": float(t["carry_pips"].mean()),
            "share_tp": float((t["exit_reason"] == "take-profit").mean()), "share_stop": float((t["exit_reason"] == "stop").mean()),
            "share_time": float((t["exit_reason"] == "time").mean()), "hold_sessions": float(t["hold_sessions"].mean()),
            "pips_per_year": float(net.sum() / years), "pips_per_session_held": float(net.sum() / max(t["hold_sessions"].sum(), 1)),
            "avg_atr_pips": float(t["atr_pips"].mean()), "worst_trade_pips": float(net.min()), "worst_trade_atr": float((net / t["atr_pips"].values).min()),
            "p5_trade_pips": float(np.percentile(net, 5)), "max_drawdown_pips": float((np.maximum.accumulate(np.r_[0.0, net.cumsum()]) - np.r_[0.0, net.cumsum()]).max()),
            "stops_filled_through_gap": int(((t["exit_reason"] == "stop") & ((t["exit_px"] - t["sl_px"]).abs() > 1e-9)).sum()) if sl else 0}


def baseline(T: Table, design: str, entries: np.ndarray, a: int, b: int, cost: float, seed: int, actual_win: float, actual_exp: float) -> dict:
    """Random entry dates (one circular shift of the real entry sessions inside the era's eligible sessions, so count
    and spacing are kept) and an independent random direction per trade; N_DRAWS draws."""
    d = T.a[design]
    E = np.flatnonzero(d["valid"] & (T.year >= a) & (T.year <= b))
    if len(entries) == 0 or len(E) == 0:
        return {}
    net = T.net(design, cost)
    p = np.searchsorted(E, entries)
    rng = np.random.default_rng(seed)
    off = rng.integers(0, len(E), size=N_DRAWS)
    idx = E[(p[None, :] + off[:, None]) % len(E)]
    sd = rng.integers(0, 2, size=idx.shape)
    v = net[idx, sd]
    w, m = (v > 0).mean(axis=1), v.mean(axis=1)
    pop = net[E]
    return {"base_win": float(w.mean()), "base_win_p2.5": float(np.percentile(w, 2.5)), "base_win_p97.5": float(np.percentile(w, 97.5)),
            "p_win_ge_actual": float((w >= actual_win - 1e-12).mean()), "base_exp_pips": float(m.mean()),
            "base_exp_p2.5": float(np.percentile(m, 2.5)), "base_exp_p97.5": float(np.percentile(m, 97.5)),
            "p_exp_ge_actual": float((m >= actual_exp - 1e-12).mean()), "pop_win_all_sessions": float((pop > 0).mean()),
            "pop_exp_all_sessions": float(pop.mean()), "pop_win_long": float((pop[:, 0] > 0).mean()), "pop_win_short": float((pop[:, 1] > 0).mean())}


def phase_averaged(T: Table, design: str, signal: np.ndarray, a: int, b: int, cost: float) -> dict:
    """Descriptive: every session with a call treated as an entry (overlapping), against all sessions, both sides."""
    d = T.a[design]
    net = T.net(design, cost)
    m = d["valid"] & (T.year >= a) & (T.year <= b) & (signal != 0) & np.isfinite(signal)
    if not m.any():
        return {}
    e = np.flatnonzero(m)
    v = net[e, np.where(signal[e] > 0, 0, 1)]
    pop = net[d["valid"] & (T.year >= a) & (T.year <= b)]
    return {"pa_call_sessions": int(m.sum()), "pa_win": float((v > 0).mean()), "pa_exp_pips": float(v.mean()),
            "pa_base_win": float((pop > 0).mean()), "pa_base_exp_pips": float(pop.mean())}


def stated_table(T: Table, trades: dict, cost: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Walk-forward stated probability per trade (win rate of the design's own trades closed before the entry year)
    and the geometry-only statement (all sessions, both sides, closed before the entry year); summary by era."""
    per_trade, rows = [], []
    for design, tr in trades.items():
        if not len(tr):
            continue
        net = (tr["gross_pips"] - cost + tr["carry_pips"]).values
        win = (net > 0).astype(float)
        d = T.a[design]
        allnet = T.net(design, cost)
        warm = T.year >= 2004
        st, geo, nh = np.full(len(tr), np.nan), np.full(len(tr), np.nan), np.zeros(len(tr), dtype=int)
        for Y in sorted(tr["year"].unique()):
            cut = pd.Timestamp(f"{Y}-01-01", tz="UTC")
            hist = (tr["exit_time"] < cut).values
            rows_y = (tr["year"] == Y).values
            nh[rows_y] = int(hist.sum())
            if hist.sum() >= MIN_STATED:
                st[rows_y] = win[hist].mean()
            cutn = np.datetime64(cut.tz_localize(None), "us")
            ok = d["valid"][:, None] & warm[:, None] & (d["exit_time"] < cutn)
            if ok.sum() >= 250:
                geo[rows_y] = float((allnet[ok] > 0).mean())
        q = tr[["design", "sess", "entry_time", "year", "side", "exit_reason"]].copy()
        q["win"], q["stated"], q["stated_geometry"], q["n_history"] = win, st, geo, nh
        per_trade.append(q)
        for era, a, b in ERAS:
            m = (q["year"] >= a) & (q["year"] <= b) & q["stated"].notna()
            if not m.any():
                continue
            w, s_, g_ = q.loc[m, "win"].values, q.loc[m, "stated"].values, q.loc[m, "stated_geometry"].values
            lo, hi = wilson(int(w.sum()), len(w))
            rows.append({"design": design, "era": era, "trades_with_statement": int(m.sum()), "stated": float(s_.mean()), "stated_min": float(s_.min()),
                         "stated_max": float(s_.max()), "realised": float(w.mean()), "realised_lo": lo, "realised_hi": hi,
                         "realised_minus_stated_pts": 100 * float(w.mean() - s_.mean()), "stated_inside_interval": bool(lo <= s_.mean() <= hi),
                         "stated_geometry": float(np.nanmean(g_)), "brier_stated": float(((s_ - w) ** 2).mean()),
                         "brier_geometry": float(((g_ - w) ** 2).mean()), "brier_coin": float(((0.5 - w) ** 2).mean())})
    return pd.concat(per_trade, ignore_index=True), pd.DataFrame(rows)


# ============================================================================= checks
def spot_check(tr: pd.DataFrame, S: pd.DataFrame, h1: pd.DataFrame, n: int = 10, seed: int = 7) -> tuple[pd.DataFrame, str]:
    """Ten trades re-walked bar by bar with a plain loop that shares no code with the engine: entry price = close of
    the last hourly bar before the entry time; then the first hourly bar whose high / low reaches each barrier."""
    rng = np.random.default_rng(seed)
    pick = []
    for reason, k in (("take-profit", 4), ("stop", 3), ("time", 3)):
        g = tr.index[tr["exit_reason"] == reason].values
        pick += list(rng.choice(g, size=min(k, len(g)), replace=False))
    rest = [i for i in tr.index if i not in pick]
    pick += list(rng.choice(rest, size=max(0, min(n - len(pick), len(rest))), replace=False))
    rows, text = [], []
    for i in sorted(pick):
        r = tr.loc[i]
        before = h1.loc[:r["entry_time"] - pd.Timedelta(seconds=1)]
        entry_bar_px = float(before["close"].iloc[-1])
        path = h1.loc[r["entry_time"]:r["limit_time"] - pd.Timedelta(seconds=1)]
        found, when, px, first_tp, first_sl = "time", r["limit_time"], float(path["close"].iloc[-1]), None, None
        for t, bar in path.iterrows():
            if r["side"] > 0:
                hit_tp, hit_sl = bar["high"] >= r["tp_px"], bar["low"] <= r["sl_px"]
            else:
                hit_tp, hit_sl = bar["low"] <= r["tp_px"], bar["high"] >= r["sl_px"]
            if hit_tp and first_tp is None:
                first_tp = t
            if hit_sl and first_sl is None:
                first_sl = t
            if hit_tp or hit_sl:
                if hit_sl:
                    found, when = "stop", t
                    px = min(bar["open"], r["sl_px"]) if r["side"] > 0 else max(bar["open"], r["sl_px"])
                else:
                    found, when, px = "take-profit", t, r["tp_px"]
                break
        ok = (found == r["exit_reason"]) and (when == r["exit_time"]) and abs(px - r["exit_px"]) < 1e-9 and abs(entry_bar_px - r["entry_px"]) < 1e-9
        rows.append({"entry_time": r["entry_time"], "side": "long" if r["side"] > 0 else "short", "entry_px_engine": r["entry_px"],
                     "last_hourly_close_before_entry": entry_bar_px, "atr_pips": r["atr_pips"], "tp_px": r["tp_px"], "sl_px": r["sl_px"],
                     "limit_time": r["limit_time"], "hourly_bars_walked": len(path), "exit_engine": r["exit_reason"], "exit_loop": found,
                     "exit_time_engine": r["exit_time"], "exit_time_loop": when, "exit_px_engine": r["exit_px"], "exit_px_loop": px,
                     "gross_pips_engine": r["gross_pips"], "gross_pips_loop": r["side"] * (px - entry_bar_px) / PIP, "match": bool(ok)})
        if found != "time":
            j = path.index.get_loc(when)
            bars = path.iloc[max(0, j - 2):j + 1]
            text.append(f"{r['entry_time']:%Y-%m-%d} {'long' if r['side'] > 0 else 'short'} @ {r['entry_px']:.5f}  tp {r['tp_px']:.5f}  sl {r['sl_px']:.5f} -> {found} in bar {when:%Y-%m-%d %H:%M}\n"
                        + bars.round(5).to_string())
        else:
            text.append(f"{r['entry_time']:%Y-%m-%d} {'long' if r['side'] > 0 else 'short'} @ {r['entry_px']:.5f}  tp {r['tp_px']:.5f}  sl {r['sl_px']:.5f} -> time exit {when:%Y-%m-%d %H:%M} @ {px:.5f}; "
                        f"path high {path['high'].max():.5f} low {path['low'].min():.5f}")
    return pd.DataFrame(rows), "\n\n".join(text)


def hole_check(tr: pd.DataFrame) -> pd.DataFrame:
    """Trades of the chosen design alive in the 2023 data hole, against Yahoo daily highs / lows of the UTC days that
    lie wholly inside the trade (a breach = beyond the barrier by at least 2 pips)."""
    from eurusd.data import load_yahoo
    y = load_yahoo("EURUSD_D1")
    rows = []
    for _, r in tr[tr["in_hole"]].iterrows():
        d = y[(y.index >= r["entry_time"]) & (y.index + pd.Timedelta(days=1) <= r["exit_time"])]
        if r["side"] > 0:
            tp_b, sl_b = (d["high"] >= r["tp_px"] + 2 * PIP), (d["low"] <= r["sl_px"] - 2 * PIP)
        else:
            tp_b, sl_b = (d["low"] <= r["tp_px"] - 2 * PIP), (d["high"] >= r["sl_px"] + 2 * PIP)
        rows.append({"entry_time": r["entry_time"], "exit_time": r["exit_time"], "side": r["side"], "exit_reason": r["exit_reason"],
                     "net_pips_1.2": r["gross_pips"] - 1.2 + r["carry_pips"], "yahoo_days_inside": len(d),
                     "yahoo_tp_breach_before_exit": bool(tp_b.any()), "yahoo_stop_breach_before_exit": bool(sl_b.any())})
    return pd.DataFrame(rows)


# ============================================================================= the run
def _design_rows(T: Table, S: pd.DataFrame, trades: dict, signal: np.ndarray, cost: float, with_baseline: bool = True, drop_hole: bool = False) -> pd.DataFrame:
    rows = []
    for di, (name, tp, sl, H) in enumerate(DESIGNS):
        tr = trades[name]
        if drop_hole:
            tr = tr[~tr["in_hole"]]
        for ei, (era, a, b) in enumerate(ERAS):
            t = tr[(tr["year"] >= a) & (tr["year"] <= b)]
            r = {"design": name, "tp_atr": tp, "sl_atr": sl, "limit_sessions": H, "era": era, "cost_pips": cost, **stats(t, name, cost, era_years(S, a, b))}
            if with_baseline and len(t):
                bl = baseline(T, name, t["sess"].values, a, b, cost, SEED + 100 * di + ei, r["win_rate"], r["exp_pips"])
                r.update(bl)
                r["edge_win_pts"] = 100 * (r["win_rate"] - bl["base_win"])
                r["edge_exp_pips"] = r["exp_pips"] - bl["base_exp_pips"]
                r["wilson_lo_above_baseline"] = bool(r["win_lo"] > bl["base_win"])
                r.update(phase_averaged(T, name, signal, a, b, cost))
            rows.append(r)
    return pd.DataFrame(rows)


def select(tab: pd.DataFrame) -> tuple[str, pd.DataFrame, bool]:
    """The declared rule on the 2010-17 rows (1.2 pips). Returns (chosen design, the selection table, qualified?)."""
    s = tab[(tab["era"] == SEL_ERA) & tab["design"].isin(BARRIER)].set_index("design")[["trades", "win_rate", "exp_pips"]].copy()
    s["qualifies"] = s["win_rate"] >= MIN_WIN_SEL
    q = s[s["qualifies"]]
    chosen = q["exp_pips"].idxmax() if len(q) else s["win_rate"].idxmax()
    s["chosen"] = s.index == chosen
    return chosen, s.reset_index(), bool(len(q))


def pass_bar(tab: pd.DataFrame, chosen: str, qualified: bool) -> tuple[pd.DataFrame, str]:
    c = tab[(tab["design"] == chosen) & (tab["era"] == CONF_ERA)].iloc[0]
    h = tab[(tab["design"] == f"hold_h{SPEC[chosen][3]}") & (tab["era"] == CONF_ERA)].iloc[0]
    se_diff = math.sqrt(c["exp_se"] ** 2 + h["exp_se"] ** 2)
    rows = [{"test": "(a) win rate >= 60 %", "value": f"{100 * c.win_rate:.1f} % ({int(c.trades)} trades)", "threshold": "60 %", "pass": bool(c.win_rate >= 0.60)},
            {"test": "(b) Wilson lower bound above the random-entry baseline", "value": f"lower bound {100 * c.win_lo:.1f} %", "threshold": f"baseline {100 * c.base_win:.1f} %",
             "pass": bool(c.win_lo > c.base_win)},
            {"test": "(c) net expectancy per trade > 0", "value": f"{c.exp_pips:+.1f} pips", "threshold": "0", "pass": bool(c.exp_pips > 0)},
            {"test": "(d) expectancy >= plain hold's minus one standard error (own SE)", "value": f"{c.exp_pips:+.1f} pips (SE {c.exp_se:.1f})",
             "threshold": f"hold {h.exp_pips:+.1f} - {c.exp_se:.1f} = {h.exp_pips - c.exp_se:+.1f}", "pass": bool(c.exp_pips >= h.exp_pips - c.exp_se)},
            {"test": "selection stage: some design reached 60 % in 2010-17", "value": str(qualified), "threshold": "True", "pass": bool(qualified)},
            {"test": "descriptive: (d) with the SE of the difference", "value": f"{c.exp_pips:+.1f} pips", "threshold": f"hold {h.exp_pips:+.1f} - {se_diff:.1f} = {h.exp_pips - se_diff:+.1f}",
             "pass": bool(c.exp_pips >= h.exp_pips - se_diff)}]
    bar = pd.DataFrame(rows)
    return bar, ("PASS" if bar["pass"].iloc[:5].all() else "FAIL")


def bar_all_designs(tab: pd.DataFrame) -> pd.DataFrame:
    """Descriptive: the four tests of the bar for every barrier design on the confirmation era."""
    rows = []
    for name in BARRIER:
        c = tab[(tab["design"] == name) & (tab["era"] == CONF_ERA)].iloc[0]
        h = tab[(tab["design"] == f"hold_h{SPEC[name][3]}") & (tab["era"] == CONF_ERA)].iloc[0]
        t = [bool(c.win_rate >= 0.60), bool(c.win_lo > c.base_win), bool(c.exp_pips > 0), bool(c.exp_pips >= h.exp_pips - c.exp_se)]
        rows.append({"design": name, "trades": int(c.trades), "win_rate": c.win_rate, "win_lo": c.win_lo, "base_win": c.base_win, "exp_pips": c.exp_pips,
                     "exp_se": c.exp_se, "hold_exp_pips": h.exp_pips, "pips_per_year": c.pips_per_year, "hold_pips_per_year": h.pips_per_year,
                     "a_win_60": t[0], "b_above_baseline": t[1], "c_exp_positive": t[2], "d_vs_hold": t[3], "all_four": all(t)})
    return pd.DataFrame(rows)


def _pct(v, d=1):
    return "" if v != v else f"{100 * v:.{d}f}"


def _plain_rows(tab: pd.DataFrame, designs: list, eras: list) -> pd.DataFrame:
    rows = []
    for name in designs:
        _, tp, sl, H = SPEC[name]
        label = f"hold {H} sessions, no barriers" if tp is None else f"target {tp:g} ATR, stop {sl:g} ATR, limit {H} sessions"
        for era in eras:
            r = tab[(tab["design"] == name) & (tab["era"] == era)].iloc[0]
            rows.append({"design": label, "era": era, "trades": int(r.trades), "trades a year": f"{r.trades_per_year:.1f}",
                         "win rate %": f"{_pct(r.win_rate)} [{_pct(r.win_lo, 0)}-{_pct(r.win_hi, 0)}]", "random-entry baseline %": _pct(r.base_win),
                         "edge (points)": f"{r.edge_win_pts:+.1f}", "average win (pips)": f"{r.avg_win_pips:+.0f}", "average loss (pips)": f"{r.avg_loss_pips:+.0f}",
                         "expectancy (pips a trade)": f"{r.exp_pips:+.0f}", "random-entry expectancy": f"{r.base_exp_pips:+.0f}"})
    return pd.DataFrame(rows)


def _full_rows(tab: pd.DataFrame, era: str) -> pd.DataFrame:
    rows = []
    for name, tp, sl, H in DESIGNS:
        r = tab[(tab["design"] == name) & (tab["era"] == era)].iloc[0]
        rows.append({"design": name, "trades": int(r.trades), "per year": f"{r.trades_per_year:.1f}", "long %": _pct(r.share_long, 0),
                     "win % [Wilson 95 %]": f"{_pct(r.win_rate)} [{_pct(r.win_lo)}-{_pct(r.win_hi)}]",
                     "baseline win % [draws 2.5-97.5]": f"{_pct(r.base_win)} [{_pct(r['base_win_p2.5'], 0)}-{_pct(r['base_win_p97.5'], 0)}]",
                     "edge pts": f"{r.edge_win_pts:+.1f}", "p (draws >= real)": f"{r.p_win_ge_actual:.3f}",
                     "avg win": f"{r.avg_win_pips:+.0f}", "avg loss": f"{r.avg_loss_pips:+.0f}", "expectancy pips (SE)": f"{r.exp_pips:+.1f} ({r.exp_se:.1f})",
                     "baseline exp.": f"{r.base_exp_pips:+.1f}", "p exp.": f"{r.p_exp_ge_actual:.3f}",
                     "exp. in ATR": f"{r.exp_atr:+.3f}", "exp. in stop units": "" if r.exp_stop_units != r.exp_stop_units else f"{r.exp_stop_units:+.3f}",
                     "exits tp / stop / time %": f"{_pct(r.share_tp, 0)} / {_pct(r.share_stop, 0)} / {_pct(r.share_time, 0)}",
                     "hold (sessions)": f"{r.hold_sessions:.1f}", "pips a year": f"{r.pips_per_year:+.0f}"})
    return pd.DataFrame(rows)


def write_report(o: dict) -> str:
    tab, tab06, nohole, stated, sel, bar, verdict, chosen = (o[k] for k in ("tab", "tab06", "nohole", "stated", "sel", "bar", "verdict", "chosen"))
    rec, placebo, sanity, spot, hole, bar_all, amb_n, n_lookup, trades = (o[k] for k in ("rec", "placebo", "sanity", "spot", "hole", "bar_all", "amb_n", "n_lookup", "trades"))
    g = lambda d, **kw: d[np.logical_and.reduce([(d[k] == v).values for k, v in kw.items()])].iloc[0]  # noqa: E731
    _, tp, sl, H = SPEC[chosen]
    hold = f"hold_h{H}"
    c, h, c_all, h_all = g(tab, design=chosen, era=CONF_ERA), g(tab, design=hold, era=CONF_ERA), g(tab, design=chosen, era="2010-26"), g(tab, design=hold, era="2010-26")
    c23 = g(tab, design=chosen, era="2023-26")
    top = tab[(tab.era == "2010-26") & tab.design.isin(BARRIER)].sort_values("win_rate", ascending=False).iloc[0]
    top_c = g(tab, design=top.design, era=CONF_ERA)
    top_h_c = g(tab, design=f"hold_h{SPEC[top.design][3]}", era=CONF_ERA)
    top_st = g(stated, design=top.design, era=CONF_ERA)
    b10 = tab[(tab.era == "2010-26") & tab.design.isin(BARRIER)]
    bconf = tab[(tab.era == CONF_ERA) & tab.design.isin(BARRIER)]
    b23 = tab[(tab.era == "2023-26") & tab.design.isin(BARRIER)]
    failed = [t.split(")")[0] + ")" for t, ok in zip(bar["test"].iloc[:4], bar["pass"].iloc[:4]) if not ok]
    st_c = g(stated, design=chosen, era=CONF_ERA)
    pl = placebo.set_index(["signal", "era"])
    live_, stale_ = pl.loc[("live signal", "2010-26")], pl.loc[(f"signal of {STALE} sessions earlier", "2010-26")]
    live_c, stale_c = pl.loc[("live signal", CONF_ERA)], pl.loc[(f"signal of {STALE} sessions earlier", CONF_ERA)]
    best_year_b = bconf.sort_values("pips_per_year", ascending=False).iloc[0]
    h21c, h42c = g(tab, design="hold_h21", era=CONF_ERA), g(tab, design="hold_h42", era=CONF_ERA)
    n_pass_all = int(bar_all.all_four.sum())
    md = []
    a = md.append
    a("# Arm AB: trade design (`trade_design`) - take-profit, stop and time limit for agreement-rule calls\n")
    a("Code `src/eurusd/arms/trade_design.py` (`run()`; `PYTHONPATH=src OMP_NUM_THREADS=1 python -m eurusd.arms.trade_design`, about 15 seconds; "
      "`--refresh` rebuilds the two caches under `data/processed/trade_design_*`). Results `experiments/results/arms/trade_design_*.csv`. "
      "The 12 candidates, the selection rule and the pass bar were written into the module docstring before any trade outcome was computed "
      "(timestamped copy: `experiments/results/arms/logs/trade_design_declaration.txt`).\n")
    a(f"## Verdict against the declared bar: **{verdict}**\n")
    a(f"Candidates run: **12** (10 barrier designs + 2 plain time-exit holds as references). Nothing else was run as a candidate.\n")
    a(f"The declared rule (highest net expectancy per trade in 2010-2017 among barrier designs with a win rate of at least 60 % there) picks "
      f"**take-profit {tp:g} ATR, stop {sl:g} ATR, time limit {H} sessions** (`{chosen}`; ATR = 14-day ATR of the daily sessions at entry). "
      f"On the trades entered in 2018-2026, which the choice never saw:\n")
    a(bar.iloc[:5][["test", "value", "threshold", "pass"]].to_markdown(index=False) + "\n")
    a(f"It fails {' and '.join(failed) if failed else 'nothing'}. In words: {int(c.trades)} trades, {_pct(c.win_rate)} % winners "
      f"(95 % interval {_pct(c.win_lo)}-{_pct(c.win_hi)} %), while the same design entered on random dates in random directions wins {_pct(c.base_win)} % "
      f"by geometry alone, which is inside the interval ({100 * c.p_win_ge_actual:.1f} % of the 1,000 random-entry draws reach the real win rate, "
      f"{100 * c.p_exp_ge_actual:.1f} % the real expectancy); average win {c.avg_win_pips:+.0f} pips, average loss {c.avg_loss_pips:+.0f} pips, net expectancy "
      f"{c.exp_pips:+.1f} pips a trade (standard error {c.exp_se:.1f}), against {h.exp_pips:+.1f} pips a trade for simply holding {H} sessions with no barriers. "
      f"With the standard error of the difference instead of the design's own, test (d) would {'pass' if bool(bar.iloc[5]['pass']) else 'also fail'} "
      f"(descriptive). Applied to every barrier design, the four tests are passed by **{n_pass_all} of 10** in 2018-26 (section 6)" + (": the verdict does not hinge on the pick.\n" if n_pass_all == 0 else ".\n"))
    a("**The honest answer to the owner's question.**\n")
    a(f"* **A 70-78 % win rate is available and its stated probability holds out of sample, but almost all of it is geometry.** "
      f"`{top.design}` (take-profit {SPEC[top.design][1]:g} ATR, stop {SPEC[top.design][2]:g} ATR, {SPEC[top.design][3]} sessions) won {_pct(top.win_rate)} % in 2010-26 and "
      f"{_pct(top_c.win_rate)} % in 2018-26; the probability one would have stated walk-forward for 2018-26 was {_pct(top_st.stated)} %. But the same barriers on "
      f"random dates and random directions win {_pct(top.base_win)} % / {_pct(top_c.base_win)} %. The edge is {top.edge_win_pts:+.1f} / {top_c.edge_win_pts:+.1f} points; "
      f"the price of the high win rate is an average loss ({top_c.avg_loss_pips:+.0f} pips) {abs(top_c.avg_loss_pips / top_c.avg_win_pips):.1f} times the average win "
      f"({top_c.avg_win_pips:+.0f} pips), and the expectancy is {top_c.exp_pips:+.0f} pips a trade, {top_c.pips_per_year:+.0f} pips a year, against "
      f"{top_h_c.exp_pips:+.0f} pips a trade and {top_h_c.pips_per_year:+.0f} pips a year for the plain {SPEC[top.design][3]}-session hold (2018-26).\n"
      f"* **The edge of the agreement rule is a similar handful of points whatever the barriers.** Win rate above the random-entry baseline, 2010-26: "
      f"{b10.edge_win_pts.min():+.1f} to {b10.edge_win_pts.max():+.1f} points across the ten barrier designs (plain holds {g(tab, design='hold_h21', era='2010-26').edge_win_pts:+.1f} and "
      f"{g(tab, design='hold_h42', era='2010-26').edge_win_pts:+.1f}); 2018-26: {bconf.edge_win_pts.min():+.1f} to {bconf.edge_win_pts.max():+.1f}; "
      f"2023-26: {b23.edge_win_pts.min():+.1f} to {b23.edge_win_pts.max():+.1f} (unconfirmed, as everything since 2023). The barriers move the win rate between "
      f"{_pct(b10.win_rate.min(), 0)} % and {_pct(b10.win_rate.max(), 0)} % by moving the baseline between {_pct(b10.base_win.min(), 0)} % and {_pct(b10.base_win.max(), 0)} %.\n"
      f"* **Barriers add no expectancy: {int((bconf.pips_per_year > max(h21c.pips_per_year, h42c.pips_per_year)).sum())} of the 10 barrier designs earn more a year than the better "
      f"plain hold in 2018-26, {int((b10.pips_per_year > max(g(tab, design='hold_h21', era='2010-26').pips_per_year, g(tab, design='hold_h42', era='2010-26').pips_per_year)).sum())} of 10 "
      f"in 2010-26.** Net pips a year, 2018-26: plain hold 21 sessions {h21c.pips_per_year:+.0f}, plain hold 42 sessions "
      f"{h42c.pips_per_year:+.0f}; best barrier design {best_year_b.pips_per_year:+.0f} (`{best_year_b.design}`), the others {bconf.pips_per_year.min():+.0f} to "
      f"{bconf.sort_values('pips_per_year').iloc[-2].pips_per_year:+.0f}. 2010-26: {g(tab, design='hold_h21', era='2010-26').pips_per_year:+.0f} and "
      f"{g(tab, design='hold_h42', era='2010-26').pips_per_year:+.0f} for the holds, {b10.pips_per_year.min():+.0f} to {b10.pips_per_year.max():+.0f} for the barrier designs. "
      f"The differences are inside the noise, so the accurate statement is 'no better', not 'worse'. Take-profits and stops reshape the distribution of outcomes "
      f"(section 6b: the worst trade and the drawdown); they do not add expectancy (same finding as `arm_swing.md`: stops made no measurable difference).\n"
      f"* **Stale placebo.** The agreement signal of 63 sessions earlier through the chosen design still wins {_pct(stale_.win_rate)} % (live {_pct(live_.win_rate)} %, baseline "
      f"{_pct(live_.base_win)} %) but earns {stale_.exp_pips:+.0f} instead of {live_.exp_pips:+.0f} pips a trade (2010-26): most of the win-rate edge is a slow regime read.\n"
      f"* **What can honestly be stated on a trade ticket.** For the chosen design: 'wins about {_pct(st_c.stated, 0)} % of the time; {_pct(c.base_win, 0)} points of that are what "
      f"these barriers give anyone on a random date; the call adds about {c.edge_win_pts:.0f} points and about {c.exp_pips:.0f} pips a trade, not confirmed since 2023 "
      f"({int(c23.trades)} trades, {_pct(c23.win_rate)} % [{_pct(c23.win_lo, 0)}-{_pct(c23.win_hi, 0)}] against a baseline of {_pct(c23.base_win)} %)'.\n")
    a("## The key table\n")
    a("Win = net result after 1.2 pips and overnight carry is positive. Random-entry baseline = the same take-profit, stop and time limit on random dates in random "
      "directions (same number of trades, same spacing, 1,000 draws): what the barrier geometry alone produces. Edge = win rate minus baseline. "
      f"Brackets: 95 % Wilson interval. ATR = 14-day ATR at entry (about {c_all.avg_atr_pips:.0f} pips on average over the 2010-26 trades; 150-160 pips in 2010-11, 55-85 since 2019). "
      "2018-26 is the period the choice never saw.\n")
    key = [chosen, hold] + ([top.design] if top.design != chosen else []) + (["hold_h21"] if hold != "hold_h21" else ["hold_h42"])
    a(_plain_rows(tab, key, ["2010-26", "2016-26", "2023-26", "2018-26"]).to_markdown(index=False, disable_numparse=True) + "\n")
    a("## 1. What exactly was simulated\n")
    a("* Signal: the walk-forward three-signal agreement rule, rebuilt with `committee.build_frame` / `_fold_columns`; the series is asserted identical to "
      "`experiments/70_committee.py::agreement_side`. First call 2007.\n"
      "* Entry at the close of a session on which the rule calls, at that close. One trade at a time; a trade ends only by take-profit, stop or time limit (a flip of "
      "the rule does not close it); the next trade opens at the first session close at or after the exit on which the rule calls (a trade that times out may be renewed "
      "on the same close).\n"
      "* Barriers in units of `atr14_pips` (Wilder ATR(14) of the NY-close daily sessions, known at the entry close; the unit of the project's calibrated path "
      "probabilities; not the 13-week weekly ATR of `swing.py`).\n"
      f"* Path: hourly bars from the entry close to the close of session entry + limit. Stop fills at the stop or at the bar's open if it opens beyond it; take-profit "
      f"fills at its level. One hourly bar touching both barriers would be decided by 1-minute bars, stop first if undecidable: this happened in **{amb_n} of {n_lookup:,}** "
      f"simulated trades (every design at every session, both directions), so the 1-minute data were never needed.\n"
      "* Costs: 1.2 pips per round turn, plus carry as in `swing.simulate` (EUR overnight rate minus Fed target, actual/360, every night held). "
      f"Carry averages {c_all.carry_pips:+.1f} pips a trade for the chosen design (the rule is long {_pct(c_all.share_long, 0)} % of the time). 0.6 pips adds 0.6 pips to "
      f"every expectancy and moves no win rate by more than {100 * float((tab06['win_rate'].values - tab['win_rate'].values).__abs__().max()):.1f} points "
      "(`trade_design_designs.csv`, `cost_pips` = 0.6).\n"
      "* Every outcome (real trades, baseline draws, placebo, shuffles) is read from one table holding the result of each design entered at each session close in each "
      "direction (`data/processed/trade_design_lookup.parquet`).\n")
    a("## 2. Reconciliation (step 0)\n")
    a("Plain-hold accuracy of the agreement rule, phase-averaged, own scoring against `committee_benchmark.csv`:\n")
    r_ = rec.copy()
    for col in ("acc_own", "acc_published", "lo", "hi", "one_grid_acc"):
        r_[col] = (100 * r_[col]).round(1)
    r_["diff_points"] = r_["diff_points"].round(3)
    a(r_[["h", "era", "n_days", "n_indep", "acc_own", "acc_published", "diff_points", "lo", "hi", "one_grid_n", "one_grid_acc"]].to_markdown(index=False) + "\n")
    a("58.3 / 63.3 / 66.7 % at 21 / 42 / 63 sessions (2010-26) reproduced exactly. Note what the sequenced plain holds below show next to it: "
      f"{_pct(g(tab, design='hold_h21', era='2010-26').win_rate)} % of {int(g(tab, design='hold_h21', era='2010-26').trades)} 21-session trades and "
      f"{_pct(h_all.win_rate if hold == 'hold_h42' else g(tab, design='hold_h42', era='2010-26').win_rate)} % of "
      f"{int(g(tab, design='hold_h42', era='2010-26').trades)} 42-session trades closed in profit; the 63.3 % at 42 sessions is the average over all entry phases, "
      "one actual sequence of trades can sit several points either side of it.\n")
    a("## 3. All twelve designs, by era (1.2 pips, carry included)\n")
    a("`p (draws >= real)` = share of the 1,000 random-entry draws with a win rate at least as high as the real one; `p exp.` the same for expectancy. "
      "Baseline expectancy should be about minus the cost (-1.2); for the barrier designs it ranges from about -8 to +6 pips, which is the sample's own mean reversion "
      "seen through asymmetric barriers and is within its sampling error (the plain holds give -1.2 exactly over all sessions).\n")
    for era, _, _ in ERAS:
        a(f"**{era}**" + (" (selection period)" if era == SEL_ERA else " (confirmation period)" if era == CONF_ERA else "") + "\n")
        a(_full_rows(tab, era).to_markdown(index=False, disable_numparse=True) + "\n")
    a("## 4. Edge versus geometry\n")
    e_ = []
    for name, tp_, sl_, H_ in DESIGNS:
        row = {"design": name, "driftless odds sl/(tp+sl) %": "" if tp_ is None else f"{100 * sl_ / (tp_ + sl_):.0f}"}
        for era in ("2010-26", "2018-26", "2023-26"):
            r = g(tab, design=name, era=era)
            row[f"{era}: win / baseline / edge"] = f"{_pct(r.win_rate)} / {_pct(r.base_win)} / {r.edge_win_pts:+.1f}"
            row[f"{era}: exp. / baseline (pips)"] = f"{r.exp_pips:+.0f} / {r.base_exp_pips:+.0f}"
        r = g(tab, design=name, era="2010-26")
        row["2010-26 all call sessions: win / all sessions"] = f"{_pct(r.pa_win)} / {_pct(r.pa_base_win)}"
        e_.append(row)
    a(pd.DataFrame(e_).to_markdown(index=False, disable_numparse=True) + "\n")
    t10 = tab[tab.era == "2010-26"]
    n_pa = int(((t10.pa_win - t10.pa_base_win) >= (t10.win_rate - t10.base_win)).sum())
    a("The last column treats every session with a call as an entry (no sequencing) against every session in both directions: the sequenced record is not a lucky "
      f"phase (the phase-averaged edge is at least as large as the sequenced one in {n_pa} of 12 designs). The edge in win rate is of the same order in every geometry, "
      "5 to 10 points in 2010-26, somewhat larger for the wide designs and the plain holds; a nearer take-profit lifts the real win rate and the baseline together.\n")
    a("## 5. Stated probability versus realised (walk-forward)\n")
    a(f"Stated for a trade entered in year Y = win rate of the design's own trades closed before Y-01-01 (at least {MIN_STATED} closed trades). "
      "`stated_geometry` = win rate of the design over all sessions and both directions closed before Y (what the barriers alone would have told you). "
      "Brier scores: lower is better; coin = 0.25.\n")
    s_ = stated.copy()
    for col in ("stated", "stated_min", "stated_max", "realised", "realised_lo", "realised_hi", "stated_geometry"):
        s_[col] = (100 * s_[col]).round(1)
    for col in ("brier_stated", "brier_geometry", "brier_coin"):
        s_[col] = s_[col].round(4)
    s_["realised_minus_stated_pts"] = s_["realised_minus_stated_pts"].round(1)
    s_ = s_[s_.era.isin(["2010-26", "2018-26", "2023-26"])]
    a(s_[["design", "era", "trades_with_statement", "stated", "realised", "realised_lo", "realised_hi", "realised_minus_stated_pts", "stated_inside_interval",
          "stated_geometry", "brier_stated", "brier_geometry", "brier_coin"]].to_markdown(index=False) + "\n")
    sc = stated[stated.era == CONF_ERA]
    s23 = stated[stated.era == "2023-26"]
    a(f"Is a stated 70 % a realised 70 %? In 2018-26, yes to within {sc.realised_minus_stated_pts.abs().max():.1f} points for every design "
      f"(mean absolute gap {sc.realised_minus_stated_pts.abs().mean():.1f} points; the stated value is inside the realised interval in {int(sc.stated_inside_interval.sum())} of {len(sc)}). "
      f"In 2023-26 the realised rate is below the stated one in {int((s23.realised_minus_stated_pts < 0).sum())} of {len(s23)} designs, by up to "
      f"{-s23.realised_minus_stated_pts.min():.1f} points, always inside intervals that are 25-40 points wide. The statement is good because most of it is geometry, "
      f"which is stable: the Brier score of the walk-forward statement beats the geometry-only statement by {1000 * (sc.brier_geometry - sc.brier_stated).mean():.1f} thousandths "
      f"on average in 2018-26 ({int((sc.brier_stated < sc.brier_geometry).sum())} of {len(sc)} designs), i.e. hardly at all.\n")
    a("## 6. Selection and the bar\n")
    q = sel.copy()
    q["win_rate"] = (100 * q["win_rate"]).round(1)
    q["exp_pips"] = q["exp_pips"].round(1)
    a("Selection table, 2010-2017 entries:\n")
    a(q.to_markdown(index=False) + "\n")
    a("Because the declared rule ranks by expectancy PER TRADE, it favours the widest, slowest design; the plain hold is slower still and has the highest expectancy "
      "per trade of all, which is why test (d) is hard for any barrier design. Per year the picture is the same (last two columns below).\n")
    a("The four tests for every barrier design on 2018-26 (descriptive; added after the run):\n")
    ba = bar_all.copy()
    for col in ("win_rate", "win_lo", "base_win"):
        ba[col] = (100 * ba[col]).round(1)
    for col in ("exp_pips", "exp_se", "hold_exp_pips"):
        ba[col] = ba[col].round(1)
    for col in ("pips_per_year", "hold_pips_per_year"):
        ba[col] = ba[col].round(0)
    a(ba.to_markdown(index=False) + "\n")
    a(f"Bar as declared, with the descriptive variant of (d):\n\n{bar[['test', 'value', 'threshold', 'pass']].to_markdown(index=False)}\n")
    a("### 6b. What the barriers do change: the shape, not the mean (descriptive)\n")
    t_ = []
    for name, tp_, sl_, H_ in DESIGNS:
        row = {"design": name}
        for era in ("2010-26", "2018-26"):
            r = g(tab, design=name, era=era)
            row[f"{era}: worst trade (pips / ATR)"] = f"{r.worst_trade_pips:+.0f} / {r.worst_trade_atr:+.1f}"
            row[f"{era}: 5 % worst (pips)"] = f"{r.p5_trade_pips:+.0f}"
            row[f"{era}: max drawdown (pips)"] = f"{r.max_drawdown_pips:.0f}"
            row[f"{era}: pips a year"] = f"{r.pips_per_year:+.0f}"
            row[f"{era}: pips per session held"] = f"{r.pips_per_session_held:+.2f}"
        t_.append(row)
    a(pd.DataFrame(t_).to_markdown(index=False, disable_numparse=True) + "\n")
    hh_ = g(tab, design="hold_h42", era="2010-26")
    a(f"A stop caps the single worst trade near the stop distance (the 42-session hold's worst trade was {hh_.worst_trade_pips:+.0f} pips, {-hh_.worst_trade_atr:.1f} ATR; with a "
      f"stop the worst is the stop distance plus costs, carry and the rare gap). The drawdown of the whole sequence is not consistently lower: 2010-26 "
      f"{b10.max_drawdown_pips.min():.0f} to {b10.max_drawdown_pips.max():.0f} pips for the barrier designs against {g(tab, design='hold_h21', era='2010-26').max_drawdown_pips:.0f} and "
      f"{hh_.max_drawdown_pips:.0f} for the holds; 2018-26 {bconf.max_drawdown_pips.min():.0f} to {bconf.max_drawdown_pips.max():.0f} against {h21c.max_drawdown_pips:.0f} and "
      f"{h42c.max_drawdown_pips:.0f} (a stopped trade is re-entered while the rule still calls).\n")
    a(f"## 7. Stale placebo: the signal of {STALE} sessions earlier through `{chosen}`\n")
    p_ = placebo.copy()
    for col in ("win_rate", "win_lo", "win_hi", "base_win", "pa_win", "pa_base_win"):
        p_[col] = (100 * p_[col]).round(1)
    for col in ("exp_pips", "exp_se", "pa_exp_pips", "trades_per_year", "pips_per_year"):
        p_[col] = p_[col].round(1)
    a(p_[["signal", "era", "trades", "trades_per_year", "win_rate", "win_lo", "win_hi", "base_win", "exp_pips", "exp_se", "pips_per_year", "pa_win", "pa_exp_pips"]].to_markdown(index=False) + "\n")
    keep_w = (stale_.win_rate - stale_.base_win) / (live_.win_rate - live_.base_win)
    keep_e = stale_.exp_pips / live_.exp_pips
    a(f"A three-month-old signal keeps {100 * keep_w:.0f} % of the win-rate edge over the baseline ({_pct(stale_.win_rate)} % against {_pct(live_.win_rate)} %) and "
      f"{100 * keep_e:.0f} % of the expectancy ({stale_.exp_pips:+.0f} against {live_.exp_pips:+.0f} pips a trade) in 2010-26; in 2018-26 "
      f"{_pct(stale_c.win_rate)} % against {_pct(live_c.win_rate)} % and {stale_c.exp_pips:+.0f} against {live_c.exp_pips:+.0f} pips. Consistent with the earlier rounds: "
      "the rule is largely a slow regime read; timing contributes to the size of the wins more than to their frequency.\n")
    a("## 8. Sanity checks\n")
    a(f"**Shuffled direction** (real entry dates of `{chosen}`, random direction, 1,000 draws). Expectancy should be about minus costs:\n")
    a(sanity.round(2).to_markdown(index=False) + "\n")
    a(f"**Spot check of ten trades by an independent plain loop over the raw hourly bars** (entry price = close of the last hourly bar before the entry time; first bar "
      f"whose high / low reaches each barrier): {int(spot.match.sum())} of {len(spot)} agree on exit type, exit bar and exit price. The bars around each exit are printed in "
      "`experiments/results/arms/logs/trade_design_spotcheck_bars.txt` and were read by eye; exit hours fall on known events (e.g. 2019-03-07 and 2020-06-04 ECB days). "
      "Gap fills were also read by eye: e.g. a short entered 2010-04-08 with its stop at 1.3601 is filled at 1.3660, the Sunday 2010-04-11 21:00 open after the weekend gap.\n")
    sp = spot.copy()
    for col in ("entry_time", "exit_time_engine", "exit_time_loop"):
        sp[col] = pd.DatetimeIndex(sp[col]).strftime("%Y-%m-%d %H:%M")
    for col in ("entry_px_engine", "last_hourly_close_before_entry", "tp_px", "sl_px", "exit_px_engine", "exit_px_loop"):
        sp[col] = sp[col].round(5)
    sp["atr_pips"], sp["gross_pips_engine"] = sp["atr_pips"].round(1), sp["gross_pips_engine"].round(1)
    a(sp[["entry_time", "side", "entry_px_engine", "last_hourly_close_before_entry", "atr_pips", "tp_px", "sl_px", "exit_engine", "exit_loop", "exit_time_engine",
          "exit_time_loop", "exit_px_engine", "exit_px_loop", "gross_pips_engine", "match"]].to_markdown(index=False) + "\n")
    a("Also verified in code or by separate scripts: every entry is on a call session in the called direction, no two trades of a design overlap, each entry is the first "
      "eligible call after the previous exit, the plain-hold gross result equals side x (close[t+H] - close[t]) to 1e-13 pips, and the carry of every trade of the "
      "chosen design equals an independent night-by-night loop to 1e-12 pips.\n")
    nh_c, nh_23 = g(nohole, design=chosen, era=CONF_ERA), g(nohole, design=chosen, era="2023-26")
    a(f"**Data hole (2023-02-03 to 2023-07-28, about 7 of 24 hourly bars missing on most sessions).** {int(len(hole))} trades of the chosen design were alive in it; "
      f"Yahoo daily highs / lows show a barrier breach the hourly bars missed in {int((hole.yahoo_tp_breach_before_exit | hole.yahoo_stop_breach_before_exit).sum()) if len(hole) else 0} of them. "
      f"Without those trades the chosen design has {int(nh_c.trades)} trades, {_pct(nh_c.win_rate)} % winners and {nh_c.exp_pips:+.1f} pips a trade in 2018-26 "
      f"({int(nh_23.trades)} trades, {_pct(nh_23.win_rate)} %, {nh_23.exp_pips:+.1f} pips in 2023-26); all designs in `trade_design_designs_without_hole_trades.csv`. "
      "Entries inside the hole use a session close that can be a few hours stale. The verdict does not change.\n")
    if len(hole):
        hl = hole.copy()
        for col in ("entry_time", "exit_time"):
            hl[col] = pd.DatetimeIndex(hl[col]).strftime("%Y-%m-%d %H:%M")
        hl["net_pips_1.2"] = hl["net_pips_1.2"].round(1)
        a(hl.to_markdown(index=False) + "\n")
    a("## 9. Caveats\n")
    a("* Departures from the declaration, all immaterial: the docstring says calls exist from 2006, the first is in 2007; the table of the four tests for every design "
      "(section 6) and the tail table (6b) were added after the run and are descriptive; a timezone bug in the never-used 1-minute path was fixed after a test on made-up cases.\n")
    a("* The agreement rule's inputs carry signs chosen by earlier rounds on this same history; its 2010-26 record is flattered and it is unconfirmed since 2023. "
      "Nothing here changes that; this arm only re-expresses the same information as a trade with barriers.\n"
      "* Wilson intervals treat sequenced trades as independent. Trades of one design do not overlap in time, but the fast designs re-enter the same call several times "
      "in a row (up to 28 trades a year from about 5 independent one-month calls), so their intervals are too narrow; the random-entry draws, which keep the spacing, "
      "are the better yardstick (`p (draws >= real)`).\n"
      "* Expectancies are in pips; ATR fell from about 150 pips (2010-11) to about 60-80 (2019-26), so a pip in 2010-17 is not a pip in 2018-26. The ATR-unit and "
      "stop-unit columns are scale-free and tell the same story.\n"
      "* Barrier touches are judged on the bid series for both directions and the whole spread is charged as the round-turn cost; take-profits get no gap improvement; "
      f"{int(g(tab, design=chosen, era='2010-26').stops_filled_through_gap)} stops of the chosen design were filled through a gap in 2010-26 "
      f"({int(tab[(tab.era == '2010-26')].stops_filled_through_gap.sum())} across all designs).\n")
    a("## Files\n")
    a("`src/eurusd/arms/trade_design.py`; `experiments/results/arms/trade_design_designs.csv` (all designs, eras, both costs, baselines, phase-averaged columns), "
      "`trade_design_designs_without_hole_trades.csv`, `trade_design_reconciliation.csv`, `trade_design_selection.csv`, `trade_design_bar.csv`, "
      "`trade_design_bar_all_designs.csv`, `trade_design_stated_vs_realised.csv`, `trade_design_stated_per_trade.csv`, `trade_design_placebo.csv`, "
      "`trade_design_sanity.csv`, `trade_design_spotcheck.csv`, `trade_design_hole_check.csv`, `trade_design_trades_chosen.csv` (trade list of the chosen design), "
      "`trade_design_trades_all.csv` (trade lists of all twelve), `logs/trade_design_declaration.txt`, `logs/trade_design_spotcheck_bars.txt`; caches "
      "`data/processed/trade_design_frame.parquet`, `data/processed/trade_design_lookup.parquet`.\n")
    text = "\n".join(md)
    (ROOT / "reports" / "arm_trade_design.md").write_text(text)
    return text


def run(cost_pips: float = 1.2, save: bool = True, verbose: bool = True, refresh: bool = False):
    """Everything, reproducibly. Returns (trade list of the chosen design, table of all designs / eras at cost_pips)."""
    pd.set_option("display.width", 250)
    S = load_frame(refresh=refresh, verbose=verbose)
    h1 = load_h1()
    rec = reconcile(S)
    assert (rec[rec.era == "2010-26"]["diff_points"].abs() < 0.1).all(), "agreement rule does not reconcile with the published numbers"
    L = build_lookup(S, h1, refresh=refresh, verbose=verbose)
    T = Table(S, L)
    sig = S["ag"].values.astype(float)
    trades = {d[0]: sequence(T, d[0], sig) for d in DESIGNS}
    tab = _design_rows(T, S, trades, sig, cost_pips)
    tab06 = _design_rows(T, S, trades, sig, 0.6)
    tab_nohole = _design_rows(T, S, trades, sig, cost_pips, with_baseline=False, drop_hole=True)
    per_trade, stated = stated_table(T, trades, cost_pips)
    chosen, sel, qualified = select(tab)
    bar, verdict = pass_bar(tab, chosen, qualified)
    # ---- descriptive: stale placebo, shuffled direction, spot check, data hole
    stale_sig = pd.Series(sig).shift(STALE).fillna(0.0).values
    tr_c = trades[chosen]
    tr_stale = sequence(T, chosen, stale_sig)
    placebo = []
    for ei, (era, a, b) in enumerate(ERAS):
        for label, t_, sg in (("live signal", tr_c, sig), (f"signal of {STALE} sessions earlier", tr_stale, stale_sig)):
            t = t_[(t_["year"] >= a) & (t_["year"] <= b)]
            r = {"signal": label, "design": chosen, "era": era, **stats(t, chosen, cost_pips, era_years(S, a, b))}
            if len(t):
                r.update(baseline(T, chosen, t["sess"].values, a, b, cost_pips, SEED + 7000 + ei, r["win_rate"], r["exp_pips"]))
                r.update(phase_averaged(T, chosen, sg, a, b, cost_pips))
            placebo.append(r)
    placebo = pd.DataFrame(placebo)
    net_c = T.net(chosen, cost_pips)
    rng = np.random.default_rng(SEED + 9000)
    sanity = []
    for era, a, b in ERAS:
        t = tr_c[(tr_c["year"] >= a) & (tr_c["year"] <= b)]
        if not len(t):
            continue
        e = t["sess"].values
        v = net_c[e[None, :], rng.integers(0, 2, size=(N_DRAWS, len(e)))]
        gross_both = T.a[chosen]["gross_pips"][e].mean()
        sanity.append({"design": chosen, "era": era, "trades": len(t), "real_exp_pips": float((t["gross_pips"] - cost_pips + t["carry_pips"]).mean()),
                       "shuffled_direction_exp_pips": float(v.mean()), "shuffled_p2.5": float(np.percentile(v.mean(axis=1), 2.5)),
                       "shuffled_p97.5": float(np.percentile(v.mean(axis=1), 97.5)), "shuffled_direction_win": float((v > 0).mean()),
                       "both_sides_gross_pips_at_real_entries": float(gross_both), "minus_cost": -cost_pips})
    sanity = pd.DataFrame(sanity)
    spot, spot_text = spot_check(tr_c, S, h1)
    hole = hole_check(tr_c)
    amb = L.groupby("design")["amb"].agg(lambda s: int((s > 0).sum())).rename("hours_touching_both_barriers").reset_index()
    out_tr = tr_c.copy()
    out_tr["net_pips"] = out_tr["gross_pips"] - cost_pips + out_tr["carry_pips"]
    out_tr["win"] = out_tr["net_pips"] > 0
    out_tr = out_tr.merge(per_trade[per_trade.design == chosen][["sess", "stated", "stated_geometry", "n_history"]], on="sess", how="left")
    ball = bar_all_designs(tab)
    if save:
        ball.to_csv(RES / f"{ARM}_bar_all_designs.csv", index=False)
        if cost_pips == 1.2:
            write_report({"tab": tab, "tab06": tab06, "nohole": tab_nohole, "stated": stated, "sel": sel, "bar": bar, "verdict": verdict, "chosen": chosen,
                          "rec": rec, "placebo": placebo, "sanity": sanity, "spot": spot, "hole": hole, "bar_all": ball, "amb_n": int((L["amb"] > 0).sum()),
                          "n_lookup": len(L), "trades": trades})
        rec.to_csv(RES / f"{ARM}_reconciliation.csv", index=False)
        pd.concat([tab, tab06], ignore_index=True).assign(chosen=lambda d: d["design"] == chosen).to_csv(RES / f"{ARM}_designs.csv", index=False)
        tab_nohole.to_csv(RES / f"{ARM}_designs_without_hole_trades.csv", index=False)
        stated.to_csv(RES / f"{ARM}_stated_vs_realised.csv", index=False)
        per_trade.to_csv(RES / f"{ARM}_stated_per_trade.csv", index=False)
        sel.to_csv(RES / f"{ARM}_selection.csv", index=False)
        bar.assign(verdict=verdict, chosen=chosen).to_csv(RES / f"{ARM}_bar.csv", index=False)
        placebo.to_csv(RES / f"{ARM}_placebo.csv", index=False)
        sanity.to_csv(RES / f"{ARM}_sanity.csv", index=False)
        spot.to_csv(RES / f"{ARM}_spotcheck.csv", index=False)
        (RES / "logs" / f"{ARM}_spotcheck_bars.txt").write_text(spot_text)
        hole.to_csv(RES / f"{ARM}_hole_check.csv", index=False)
        out_tr.to_csv(RES / f"{ARM}_trades_chosen.csv", index=False)
        pd.concat(trades.values(), ignore_index=True).to_csv(RES / f"{ARM}_trades_all.csv", index=False)
    if verbose:
        f = lambda d, cols: d[cols].to_string(index=False, float_format=lambda v: f"{v:.3f}")  # noqa: E731
        print("\nRECONCILIATION\n", f(rec, ["h", "era", "n_indep", "acc_own", "acc_published", "diff_points"]))
        cols = ["design", "era", "trades", "trades_per_year", "win_rate", "win_lo", "win_hi", "base_win", "edge_win_pts", "p_win_ge_actual", "avg_win_pips",
                "avg_loss_pips", "exp_pips", "exp_se", "base_exp_pips", "p_exp_ge_actual", "exp_stop_units", "share_tp", "share_stop", "share_time",
                "hold_sessions", "pips_per_year"]
        for era, _, _ in ERAS:
            print(f"\nDESIGNS {era} at {cost_pips} pips\n", f(tab[tab.era == era], cols))
        print("\nSELECTION (2010-17)\n", sel.to_string(index=False))
        print(f"\nCHOSEN: {chosen}   VERDICT: {verdict}\n", bar.to_string(index=False))
        print("\nSTATED vs REALISED\n", f(stated, ["design", "era", "trades_with_statement", "stated", "realised", "realised_lo", "realised_hi", "stated_geometry",
                                                  "brier_stated", "brier_geometry", "brier_coin"]))
        print("\nPLACEBO\n", f(placebo, ["signal", "era", "trades", "win_rate", "win_lo", "win_hi", "base_win", "exp_pips", "exp_se", "pa_win", "pa_exp_pips", "pa_base_win"]))
        print("\nSANITY\n", sanity.round(2).to_string(index=False))
        print("\nSPOT CHECK\n", spot[["entry_time", "side", "exit_engine", "exit_loop", "exit_time_engine", "exit_time_loop", "match"]].to_string(index=False))
        print("\nHOLE\n", hole.to_string(index=False))
        print("\nambiguous hours\n", amb.to_string(index=False))
    return out_tr, tab


if __name__ == "__main__":
    run(refresh="--refresh" in sys.argv)
