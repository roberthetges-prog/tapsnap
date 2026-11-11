"""Arm N ("selective"): selective prediction for EUR/USD position trading - a model that only speaks when it is
confident, judged by its out-of-sample ACCURACY-COVERAGE curve.

Scope (owner, via the lead, 2026-11-11): directional POSITION trading, holding for weeks up to a month or more.
Primary horizons 10 / 21 / 42 / 63 sessions; 1- and 5-session direction are optional diagnostics; the intraday
13:00 continuation item was dropped (optional in the re-scoped brief).

EVERYTHING BELOW WAS WRITTEN BEFORE ANY RESULT WAS COMPUTED.

Targets (symmetric, so a hit rate means something)
  sign{h}      : sign of the h-session forward log return, h in 10, 21, 42, 63 (diagnostic: 1, 5).
  tb{h}_{k}atr : symmetric triple barrier, +k ATR14 before -k ATR14 within h sessions, k in 2, 3 (8 targets). A day
                 that opens beyond a barrier counts as that barrier; a day touching both barriers is unresolved
                 for the label and a STOP (loss) for either direction in the P&L; a time-out is closed at the
                 close of session h. A call is "right" when the trade it implies closes with a gross profit
                 (target first, or time-out in the money), so every decision is right or wrong.
  Label-known time = close of session t+h (exact, stricter than the store's calendar approximation).

Models (one decision per NY-close session, yearly expanding walk-forward, test years 2010..2026)
  house : the house combination score of the 14 economic signals (weak_signals.py, t-stat weights against fwd_1d
          from the training window; one score, the same for every horizon).
  logit : L2 logistic regression on the store's macro + positioning + calendar blocks (every macro column us2y..eur_vs_usd_factor_20,
          the four cot_* columns, calendar numerics, dow and month one-hot), standardised with training statistics, clipped at +-5, NaN -> 0.
          Fixed shrinkage rule C = 4 / n_train (the logistic analogue of the house ridge alpha = n_train). No search.
  avg   : mean of the two calibrated probabilities.
  Calibration: Platt (2-parameter logistic, unconstrained, with intercept) fitted INSIDE the training window on
          time-ordered out-of-sample scores: the training window is cut into 5 consecutive blocks; for blocks 3, 4, 5
          the model is fitted on rows whose label is known before the block starts and scores the block; the Platt
          map and all thresholds come from those pooled forward scores. The final model is refitted on the whole
          training window.
  Decision rules: (a) coverage rules: speak when |p - 0.5| >= the training-window quantile that gives a target
          coverage of 100 / 50 / 25 / 10 / 5 %; (b) probability rules: speak when max(p, 1-p) >= 0.55 / 0.60 / 0.65.
          Direction = sign(p - 0.5).

Evaluation
  non-overlapping : greedy sequential stream on the daily grid - when the model speaks a decision is opened and no
          new decision is possible until it is closed (h sessions, or the barrier exit). At 100 % coverage this is the
          usual every-h-th-session grid. Plain 95 % Wilson interval.
  weekly  : a decision every 5th session whenever the rule speaks, overlapping holds. Interval = Wilson with a
          Newey-West EFFECTIVE sample size (Bartlett kernel, bandwidth ceil(1.5 h / 5) weeks, applied to the
          series speak_t x (hit_t - acc) on the weekly grid; n_eff = acc(1-acc)/var_NW, capped at n). For the
          probability rules and all candidates a circular block bootstrap (block 2h/5 weeks, 2000 draws) is
          reported next to it.
  P&L per decision: direction x forward return (or the barrier-trade return) minus a full round trip
          (2 x cost_pips: 1.2 pips per unit turnover, in and out; no netting between consecutive decisions, which is
          conservative). Trading-rule Sharpe: book of weekly tranches (weight 1/ceil(h/5) each, so |position| <= 1),
          run through wf.pnl_from_positions for time exits (turnover netted by the protocol) and marked to market
          daily for stop/target exits (2 x cost per tranche).
  Base rate = share of up outcomes on the evaluation grid in the period; "chance" = accuracy a no-skill caller with
          the same long/short mix would have had. Evidence = accuracy rising with selectivity AND the interval at
          10 % coverage excluding max(base, 1-base). A single cell is not evidence.

(B) agreement / regime selectors, each a fixed rule: agree3 = sign(cot_z52), sign(d_spread2y_20) and sign(house
  score) all equal; agree3_trend = agree3 and dist_sma50_atr, dist_sma200_atr on the same side; house-score sign on
  predicted-quiet (next-session range forecast < 0.85 x trailing-250 median) vs predicted-volatile (forecast > trailing
  80th percentile) decision days; house-score sign outside / inside the 2 sessions around FOMC/ECB/NFP/CPI
  (an event in the session just closed or the next one). Range forecast = the HAR + events model of
  experiments/50_prediction_scoreboard.py. All evaluated on sign10/21/42/63 with weekly decisions.

(C) path / level predictions: (i) P(next-session range < k x forecast), k = 1, 1.25, 1.5; (ii) P(price does NOT
  touch a level d away from the close within h = 1, 5, 10, 21 sessions), one-sided (upper and lower level pooled),
  d = u x U_h with U_h = forecast mean daily range over the next h sessions x sqrt(h) (walk-forward log-HAR on
  r1, r5, r21, r63; for h = 1 the scoreboard model), u on a fixed grid; also d = k x ATR14 for k = 1, 2, 3 at
  h = 10, 21 (the stop/target of a position trade). Model probability = training-window empirical frequency of the
  scaled excursion; naive = the unconditional training distribution of the excursion in pips (whole window, and the
  trailing 250 sessions, the stronger baseline). Calibration and Brier score against both.

(D) expectancy for every candidate and every weekly cell with accuracy >= 60 %: average win / loss, net expectancy,
  decisions per year, and net Sharpe of (a) the time-exit book and (b) the symmetric stop/target book
  (2 ATR for h = 10, 21; 3 ATR for h = 42, 63; time-out h) for 2016-26 and 2023-26.

CANDIDATE RULES for the final selection (12, all multi-week directional calls, weekly decisions):
   1 sign10_avg_p60      2 sign21_avg_p60      3 sign42_avg_p60      4 sign63_avg_p60
   5 tb10_2atr_avg_p60   6 tb21_2atr_avg_p60   7 tb42_3atr_avg_p60   8 tb63_3atr_avg_p60
   9 sign21_house_p60   10 sign21_logit_p60   11 sign21_agree3      12 sign21_agree3_trend
SELECTION RULE (given by the lead; interval adapted to overlap as stated): final = the candidate with the highest
  LOWER bound of the 2010-2015 accuracy interval (Wilson with Newey-West effective n) among candidates with at
  least 15 decisions per year in 2010-2015 and positive net expectancy per decision in 2010-2015. If no candidate is
  eligible there is NO final rule; the stream written to disk is then the candidate with the highest lower bound
  among those with enough decisions, flagged as failing. The full 2010-26 / 2016-26 / 2023-26 record of the pick is
  reported whatever it shows.
Variant count for deflation: 12 candidate rules. Diagnostics (not selected from): 14 targets x 3 models x 8 rules
  x 2 evaluation modes of curves, 4 x 7 selector cells, the path tables.

ADDED AFTER THE FIRST RUN (none of it changes the selection; all of it is labelled in the report):
  * conservative effective n = min(Newey-West n, decisions x 5 / holding period) and the interval built on it
    (columns n_eff_cons, lo_cons, hi_cons): the Newey-West n proved too generous for 42-63-session holds;
  * the non-overlapping stream for the fixed (B) selectors;
  * a timing placebo for the expectancy table (the rule's own weekly call series rotated by >= 26 weeks, 2000 draws);
  * `final_p60`: the declared rule applied to the ten probability-call candidates only, because the rule picked a fixed
    selector and the owner asked for a probability call; its stream goes to selective_p60_*.parquet;
  * `prob` of the fixed final rule = its own hit rate on decisions whose label was known before the test year.
"""
from __future__ import annotations

import math
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import features as F  # noqa: E402
from eurusd.arms import weak_signals as WS  # noqa: E402
from eurusd.data import load_ohlc  # noqa: E402
from eurusd.wf import YEARS, _agg, pnl_from_positions, report  # noqa: E402

FEATURES = ROOT / "data/processed/features_daily.parquet"
RES = ROOT / "experiments/results/arms"
ARM = "selective"
N_ARMS = 12

HORIZONS = (10, 21, 42, 63)
DIAG_HORIZONS = (1, 5)
TB = tuple((h, k) for h in HORIZONS for k in (2, 3))
COVERAGES = (1.0, 0.5, 0.25, 0.10, 0.05)
PTHR = (0.55, 0.60, 0.65)
MODELS = ("house", "logit", "avg")
PERIODS = (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026), ("2010-15", 2010, 2015))
STEP = 5                                     # weekly decision grid = every 5th session
SYM_K = {1: 2, 5: 2, 10: 2, 21: 2, 42: 3, 63: 3}   # stop/target (ATR) used for the symmetric-exit book of a sign rule
CANDIDATES = (
    ("sign10_avg_p60", "sign10", "avg", "p60"), ("sign21_avg_p60", "sign21", "avg", "p60"),
    ("sign42_avg_p60", "sign42", "avg", "p60"), ("sign63_avg_p60", "sign63", "avg", "p60"),
    ("tb10_2atr_avg_p60", "tb10_2atr", "avg", "p60"), ("tb21_2atr_avg_p60", "tb21_2atr", "avg", "p60"),
    ("tb42_3atr_avg_p60", "tb42_3atr", "avg", "p60"), ("tb63_3atr_avg_p60", "tb63_3atr", "avg", "p60"),
    ("sign21_house_p60", "sign21", "house", "p60"), ("sign21_logit_p60", "sign21", "logit", "p60"),
    ("sign21_agree3", "sign21", "B:agree3", "filter"), ("sign21_agree3_trend", "sign21", "B:agree3_trend", "filter"),
)
MIN_DEC_PER_YEAR = 15
U_GRID = (0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0)
ATR_GRID = (1.0, 2.0, 3.0)
PATH_H = (1, 5, 10, 21)
NAT = np.iinfo(np.int64).min


# ================================================================ data, labels
def load_data() -> pd.DataFrame:
    D = pd.read_parquet(FEATURES)
    h1 = load_ohlc("H1").loc["2003":]
    h1 = h1[~h1.index.duplicated(keep="last")]
    d = F.daily_ohlc(h1[["open", "high", "low", "close"]], 22)
    d = d[(d["n"] >= 10) & (d.index.dayofweek != 5)]
    assert d.index.equals(D.index) and np.allclose(d["close"].values, D["close"].values), "daily bars differ from the store"
    D["open"], D["high"], D["low"] = d["open"].values, d["high"].values, d["low"].values
    return D


def barrier_sim(D: pd.DataFrame, h: int, k: float) -> dict:
    """Symmetric +-k ATR14 barriers around the close of t, sessions t+1..t+h. Returns out (+1 upper first, -1 lower
    first, 0 both in one day or time-out), timeout flag, exit offset, and the exit price of a long and of a short."""
    c, o, hi, lo = (D[x].values for x in ("close", "open", "high", "low"))
    atr = D["atr14_pips"].values * 1e-4
    n = len(c)
    out = np.full(n, np.nan); to = np.zeros(n, bool); off = np.full(n, np.nan)
    xl = np.full(n, np.nan); xs = np.full(n, np.nan)
    for i in range(n - h):
        if not np.isfinite(atr[i]):
            continue
        U, L = c[i] + k * atr[i], c[i] - k * atr[i]
        done = False
        for j in range(1, h + 1):
            q = i + j
            if o[q] >= U:                      # gap through the upper barrier: long target at U, short stopped at the open
                out[i], off[i], xl[i], xs[i] = 1.0, j, U, o[q]; done = True
            elif o[q] <= L:
                out[i], off[i], xl[i], xs[i] = -1.0, j, o[q], L; done = True
            else:
                up, dn = hi[q] >= U, lo[q] <= L
                if up and dn:                  # ambiguous day: both directions are treated as stopped
                    out[i], off[i], xl[i], xs[i] = 0.0, j, L, U; done = True
                elif up:
                    out[i], off[i], xl[i], xs[i] = 1.0, j, U, U; done = True
                elif dn:
                    out[i], off[i], xl[i], xs[i] = -1.0, j, L, L; done = True
            if done:
                break
        if not done:
            out[i], off[i], xl[i], xs[i], to[i] = 0.0, h, c[i + h], c[i + h], True
    return {"out": out, "timeout": to, "off": off, "exit_long": xl, "exit_short": xs}


@dataclass
class Target:
    name: str
    kind: str            # 'sign' or 'tb'
    h: int
    k: float
    y: np.ndarray        # training label 1 / 0 / nan
    long: np.ndarray     # gross bp of a long decision
    short: np.ndarray    # gross bp of a short decision
    hold: np.ndarray     # sessions held
    end: np.ndarray      # int64 ns at which the label is known (NAT if unknown)
    exit_long: np.ndarray | None = None
    exit_short: np.ndarray | None = None
    resolved: np.ndarray | None = None

    def permuted(self, perm: np.ndarray) -> "Target":
        f = lambda a: None if a is None else a[perm]
        return Target(self.name, self.kind, self.h, self.k, self.y[perm], self.long[perm], self.short[perm], self.hold[perm],
                      self.end, f(self.exit_long), f(self.exit_short), f(self.resolved))


def build_targets(D: pd.DataFrame) -> dict[str, Target]:
    lc = np.log(D["close"].values)
    n = len(lc)
    ct = D["close_time"].values.astype("datetime64[ns]").astype(np.int64)
    T = {}
    fwd = {}
    for h in DIAG_HORIZONS + HORIZONS:
        f = np.full(n, np.nan); f[:n - h] = (lc[h:] - lc[:n - h]) * 1e4
        end = np.full(n, NAT, dtype=np.int64); end[:n - h] = ct[h:]
        fwd[h] = (f, end)
        y = np.where(np.isfinite(f), (f > 0).astype(float), np.nan)
        T[f"sign{h}"] = Target(f"sign{h}", "sign", h, 0.0, y, f, -f, np.where(np.isfinite(f), float(h), np.nan), end)
    for h, k in TB:
        b = barrier_sim(D, h, k)
        f, end = fwd[h]
        c = D["close"].values
        long = np.log(b["exit_long"] / c) * 1e4
        short = -np.log(b["exit_short"] / c) * 1e4
        y = np.where(b["out"] > 0, 1.0, np.where(b["out"] < 0, 0.0, np.nan))
        y = np.where(b["timeout"], (f > 0).astype(float), y)
        y = np.where(np.isfinite(b["out"]), y, np.nan)
        T[f"tb{h}_{k}atr"] = Target(f"tb{h}_{k}atr", "tb", h, float(k), y, long, short, b["off"], end, b["exit_long"], b["exit_short"],
                                    (~b["timeout"]) & np.isfinite(b["out"]))
    return T


# ================================================================ features
MACRO_FIRST, MACRO_LAST = "us2y", "eur_vs_usd_factor_20"
POSITIONING = ["cot_net_pct", "cot_z52", "cot_d4", "cot_lev_z52"]
CAL_NUM = ["dom", "bd_from_start", "bd_to_end", "is_month_end", "is_quarter_end_month"]


def logit_matrix(D: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
    cols = list(D.columns)
    macro = cols[cols.index(MACRO_FIRST): cols.index(MACRO_LAST) + 1]
    X = D[macro + POSITIONING + CAL_NUM].astype(float).copy()
    for d in range(5):
        X[f"dow_{d}"] = (D["dow"] == d).astype(float)
    for m in range(1, 13):
        X[f"month_{m}"] = (D["month"] == m).astype(float)
    return X.values, list(X.columns)


@dataclass
class Ctx:
    D: pd.DataFrame
    S: pd.DataFrame          # raw oriented house signals
    X: np.ndarray            # logit design matrix (raw)
    xcols: list
    fwd1: np.ndarray
    ct: np.ndarray           # close_time int64 ns
    year: np.ndarray
    cost_bp: np.ndarray      # bp cost of ONE unit of turnover at cost_pips
    G: pd.DataFrame = None   # raw columns used by the fixed selectors

    def shifted(self, lag: int) -> "Ctx":
        """Features moved by `lag` sessions: lag > 0 = staler information, lag < 0 = look-ahead (control only)."""
        S = self.S.shift(lag)
        X = pd.DataFrame(self.X).shift(lag).values
        return Ctx(self.D, S, X, self.xcols, self.fwd1, self.ct, self.year, self.cost_bp, self.G.shift(lag))

    def with_fwd1(self, fwd1: np.ndarray) -> "Ctx":
        return Ctx(self.D, self.S, self.X, self.xcols, fwd1, self.ct, self.year, self.cost_bp, self.G)


def make_ctx(D: pd.DataFrame, cost_pips: float) -> Ctx:
    S = WS.build_raw_signals(D)
    X, xcols = logit_matrix(D)
    ct = D["close_time"].values.astype("datetime64[ns]").astype(np.int64)
    G = D[["cot_z52", "d_spread2y_20", "dist_sma50_atr", "dist_sma200_atr"]].copy()
    return Ctx(D, S, X, xcols, D["fwd_1d"].values, ct, D.index.year.values, (cost_pips / D["close"]).values, G)


# ---------------------------------------------------------------- the two scorers
def house_fit(ctx: Ctx, idx: np.ndarray):
    S = ctx.S.iloc[idx]
    st = WS._scaler_fit(S)
    Z = WS._scaler_apply(S, st)
    y = pd.Series(ctx.fwd1[idx], index=S.index)
    ok = y.notna().values
    w = WS._weights(Z[ok], y[ok], "tstat")
    return st, w


def house_score(ctx: Ctx, m, idx: np.ndarray) -> np.ndarray:
    st, w = m
    return WS._scaler_apply(ctx.S.iloc[idx], st).values @ w


def logit_fit(ctx: Ctx, idx: np.ndarray, y: np.ndarray):
    ok = np.isfinite(y[idx])
    fi = idx[ok]
    X = ctx.X[fi]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mu = np.nanmean(X, axis=0); sd = np.nanstd(X, axis=0)
    mu = np.where(np.isfinite(mu), mu, 0.0)
    sd = np.where(np.isfinite(sd) & (sd > 1e-12), sd, np.inf)
    Z = np.nan_to_num(np.clip((X - mu) / sd, -5, 5))
    yy = y[fi]
    if len(np.unique(yy)) < 2:
        return mu, sd, None
    lr = LogisticRegression(C=4.0 / len(fi), max_iter=2000, tol=1e-7)
    lr.fit(Z, yy)
    return mu, sd, lr


def logit_score(ctx: Ctx, m, idx: np.ndarray) -> np.ndarray:
    mu, sd, lr = m
    if lr is None:
        return np.zeros(len(idx))
    Z = np.nan_to_num(np.clip((ctx.X[idx] - mu) / sd, -5, 5))
    return lr.decision_function(Z)


def platt_fit(s: np.ndarray, y: np.ndarray):
    ok = np.isfinite(s) & np.isfinite(y)
    s, y = s[ok], y[ok]
    sd = float(s.std()) or 1.0
    if len(np.unique(y)) < 2:
        p = float(np.clip(y.mean() if len(y) else 0.5, 1e-3, 1 - 1e-3))
        return sd, 0.0, math.log(p / (1 - p))
    lr = LogisticRegression(C=1e6, max_iter=1000)
    lr.fit((s / sd)[:, None], y)
    return sd, float(lr.coef_[0, 0]), float(lr.intercept_[0])


def platt_apply(m, s: np.ndarray) -> np.ndarray:
    sd, a, b = m
    return 1.0 / (1.0 + np.exp(-(a * s / sd + b)))


def wf_target(ctx: Ctx, T: Target, years=YEARS, log: dict | None = None) -> dict:
    """Walk-forward calibrated probabilities of the three models and the training-window thresholds for one target."""
    n = len(ctx.D)
    P = {m: np.full(n, np.nan) for m in MODELS}
    THR = {m: {c: np.full(n, np.nan) for c in COVERAGES} for m in MODELS}
    known = T.end != NAT
    for Y in years:
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC").value
        tr = np.where(known & (T.end < start))[0]
        te = np.where(ctx.year == Y)[0]
        if len(tr) < 750 or len(te) == 0:
            continue
        blocks = np.array_split(tr, 5)
        oos = np.concatenate(blocks[2:])
        sc = {"house": np.full(len(oos), np.nan), "logit": np.full(len(oos), np.nan)}
        ptr = 0
        for b in blocks[2:]:
            fit_idx = tr[T.end[tr] <= ctx.ct[b[0]]]          # label known at the decision time of the block's first row
            mh = house_fit(ctx, fit_idx)
            ml = logit_fit(ctx, fit_idx, T.y)
            sc["house"][ptr:ptr + len(b)] = house_score(ctx, mh, b)
            sc["logit"][ptr:ptr + len(b)] = logit_score(ctx, ml, b)
            ptr += len(b)
        yo = T.y[oos]
        pl = {m: platt_fit(sc[m], yo) for m in ("house", "logit")}
        po = {m: platt_apply(pl[m], sc[m]) for m in ("house", "logit")}
        po["avg"] = 0.5 * (po["house"] + po["logit"])
        mh = house_fit(ctx, tr)
        ml = logit_fit(ctx, tr, T.y)
        pt = {"house": platt_apply(pl["house"], house_score(ctx, mh, te)), "logit": platt_apply(pl["logit"], logit_score(ctx, ml, te))}
        pt["avg"] = 0.5 * (pt["house"] + pt["logit"])
        for m in MODELS:
            P[m][te] = pt[m]
            conf = np.abs(po[m] - 0.5)
            for c in COVERAGES:
                THR[m][c][te] = 0.0 if c >= 1.0 else float(np.quantile(conf, 1 - c))
        if log is not None:
            log[Y] = {"platt": pl, "logit": ml, "house": mh, "n_train": len(tr), "train_base": float(np.nanmean(T.y[tr]))}
    return {"P": P, "THR": THR}


def house_score_wf(ctx: Ctx, years=YEARS) -> np.ndarray:
    """The house score itself, walk-forward (weights from rows whose 1-session label is known before the year)."""
    n = len(ctx.D)
    end1 = np.full(n, NAT, dtype=np.int64); end1[:n - 1] = ctx.ct[1:]
    out = np.full(n, np.nan)
    for Y in years:
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC").value
        tr = np.where((end1 != NAT) & (end1 < start))[0]
        te = np.where(ctx.year == Y)[0]
        if len(tr) < 750 or len(te) == 0:
            continue
        out[te] = house_score(ctx, house_fit(ctx, tr), te)
    return out


# ================================================================ intervals
def wilson(p: float, n: float, z: float = 1.959964) -> tuple[float, float]:
    if n <= 0 or not np.isfinite(p):
        return np.nan, np.nan
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(max(p * (1 - p) / n + z * z / (4 * n * n), 0.0)) / den
    return mid - half, mid + half


def nw_neff(s: np.ndarray, hit: np.ndarray, L: int) -> float:
    """Effective number of independent decisions for acc = sum(hit)/sum(s) on an equally spaced grid."""
    n = float(s.sum())
    if n < 2:
        return n
    p = float(hit.sum()) / n
    if p <= 0 or p >= 1:
        return max(1.0, n / (1 + L))
    e = s * (hit - p)
    Tn = len(e)
    lrv = float((e * e).sum()) / Tn
    for l in range(1, min(L, Tn - 1) + 1):
        lrv += 2 * (1 - l / (L + 1)) * float((e[l:] * e[:-l]).sum()) / Tn
    var = Tn * lrv / n ** 2
    if var <= 0:
        return n
    return float(min(n, max(1.0, p * (1 - p) / var)))


def block_boot(s: np.ndarray, hit: np.ndarray, block: int, reps: int = 2000, seed: int = 7) -> tuple[float, float]:
    Tn = len(s)
    if s.sum() < 5 or Tn < 2 * block:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(Tn / block))
    starts = rng.integers(0, Tn, size=(reps, nb))
    idx = (starts[:, :, None] + np.arange(block)[None, None, :]) % Tn
    idx = idx.reshape(reps, -1)[:, :Tn]
    ss, hh = s[idx].sum(1), hit[idx].sum(1)
    acc = np.where(ss > 0, hh / np.maximum(ss, 1), np.nan)
    acc = acc[np.isfinite(acc)]
    return float(np.quantile(acc, 0.025)), float(np.quantile(acc, 0.975))


# ================================================================ decisions and their statistics
def speak_dir(P: np.ndarray, rule: str, thr: dict | None) -> tuple[np.ndarray, np.ndarray]:
    conf = np.abs(P - 0.5)
    ok = np.isfinite(P) & (conf > 0)
    if rule.startswith("cov"):
        c = int(rule[3:]) / 100.0
        sp = ok & (conf >= thr[c])
    else:
        sp = ok & (conf >= int(rule[1:]) / 100.0 - 0.5 - 1e-12)
    return sp, np.where(P > 0.5, 1.0, -1.0)


def weekly_idx(speak: np.ndarray, valid: np.ndarray) -> np.ndarray:
    g = np.arange(0, len(speak), STEP)
    return g[speak[g] & valid[g]]


def seq_idx(speak: np.ndarray, valid: np.ndarray, hold: np.ndarray) -> np.ndarray:
    out = []
    i, n = 0, len(speak)
    while i < n:
        if speak[i] and valid[i]:
            out.append(i)
            i += max(1, int(hold[i]))
        else:
            i += 1
    return np.array(out, dtype=int)


def decision_frame(ctx: Ctx, T: Target, idx: np.ndarray, dirs: np.ndarray, P: np.ndarray | None) -> pd.DataFrame:
    d = dirs[idx]
    gross = np.where(d > 0, T.long[idx], T.short[idx])
    return pd.DataFrame({"i": idx, "pos": d, "prob": (P[idx] if P is not None else np.nan), "gross_bp": gross,
                         "net_bp": gross - 2 * ctx.cost_bp[idx], "hit": (gross > 0).astype(float), "hold": T.hold[idx],
                         "fwd_bp": gross * d, "year": ctx.year[idx]}, index=ctx.D.index[idx])


def cell_stats(ctx: Ctx, T: Target, dec: pd.DataFrame, speak: np.ndarray, mode: str, boot: bool = False) -> list[dict]:
    valid = np.isfinite(T.long)
    grid = np.arange(0, len(valid), STEP) if mode == "weekly" else np.arange(len(valid))
    grid = grid[valid[grid]]
    gy = ctx.year[grid]
    rows = []
    for lab, a, b in PERIODS:
        g = grid[(gy >= a) & (gy <= b)]
        x = dec[(dec["year"] >= a) & (dec["year"] <= b)]
        n = len(x)
        r = {"period": lab, "n": n}
        if len(g) == 0:
            rows.append(r); continue
        yrs = max((ctx.D.index[g[-1]] - ctx.D.index[g[0]]).days / 365.25, 1e-9)
        base = float((T.long[g] > 0).mean())
        r.update({"dec_per_year": n / yrs, "coverage": float(speak[g].mean()), "base_up": base, "majority_base": max(base, 1 - base)})
        if n:
            acc = float(x["hit"].mean())
            sl = float((x["pos"] > 0).mean())
            if mode == "weekly":
                s = np.zeros(len(g)); hh = np.zeros(len(g))
                loc = np.searchsorted(g, x["i"].values)
                s[loc] = 1.0; hh[loc] = x["hit"].values
                neff = nw_neff(s, hh, int(math.ceil(1.5 * T.h / STEP)))
                itype = "wilson_nw_eff_n"
                if boot:
                    r["boot_lo"], r["boot_hi"] = block_boot(s, hh, max(2, int(math.ceil(2 * T.h / STEP))))
            else:
                neff, itype = float(n), "wilson"
            lo, hi = wilson(acc, neff)
            # conservative cross-check (added after the first run, see report): never credit more independent decisions
            # than the number of non-overlapping holding periods the decisions could fill
            neff_c = min(neff, max(1.0, n * STEP / max(float(x["hold"].mean()), STEP))) if mode == "weekly" else neff
            lo_c, hi_c = wilson(acc, neff_c)
            w, l = x.loc[x["net_bp"] > 0, "net_bp"], x.loc[x["net_bp"] <= 0, "net_bp"]
            r.update({"n_eff": neff, "accuracy": acc, "lo": lo, "hi": hi, "interval": itype, "share_long": sl,
                      "n_eff_cons": neff_c, "lo_cons": lo_c, "hi_cons": hi_c, "excl_base_cons": bool(lo_c > max(base, 1 - base)),
                      "chance_acc": sl * base + (1 - sl) * (1 - base), "excl_base": bool(lo > max(base, 1 - base)),
                      "gross_bp": float(x["gross_bp"].mean()), "net_bp": float(x["net_bp"].mean()), "avg_hold": float(x["hold"].mean()),
                      "win_rate_net": float((x["net_bp"] > 0).mean()), "avg_win_bp": float(w.mean()) if len(w) else np.nan,
                      "avg_loss_bp": float(l.mean()) if len(l) else np.nan,
                      "mean_prob_conf": float((x["prob"] - 0.5).abs().mean() + 0.5) if x["prob"].notna().any() else np.nan})
        rows.append(r)
    return rows


# ---------------------------------------------------------------- trading books
def book_time_exit(ctx: Ctx, dec: pd.DataFrame, h: int, cost_pips: float) -> pd.Series:
    n = len(ctx.D)
    w = 1.0 / math.ceil(h / STEP)              # at most ceil(h/5) tranches are open, so |position| <= 1
    pos = np.zeros(n)
    for i, d in zip(dec["i"].values, dec["pos"].values):
        pos[i:i + h] += d * w
    pnl = pnl_from_positions(pd.Series(pos, index=ctx.D.index), ctx.D["fwd_1d"], ctx.D["close"], cost_pips=cost_pips)
    return pnl


def book_barrier(ctx: Ctx, dec: pd.DataFrame, Tb: Target, cost_pips: float) -> pd.DataFrame:
    """Weekly tranches with the symmetric stop/target of barrier target Tb, marked to market at each close."""
    n = len(ctx.D)
    lc = np.log(ctx.D["close"].values)
    w = 1.0 / math.ceil(Tb.h / STEP)
    daily = np.zeros(n); gross_pos = np.zeros(n)
    cb = cost_pips / ctx.D["close"].values                      # bp cost of one unit of turnover
    for i, d in zip(dec["i"].values, dec["pos"].values):
        if not np.isfinite(Tb.hold[i]):
            continue
        j = int(Tb.hold[i])
        px = Tb.exit_long[i] if d > 0 else Tb.exit_short[i]
        if j > 1:
            daily[i:i + j - 1] += d * w * (lc[i + 1:i + j] - lc[i:i + j - 1]) * 1e4
        daily[i + j - 1] += d * w * (math.log(px) - lc[i + j - 1]) * 1e4
        daily[i] -= w * cb[i]
        daily[i + j - 1] -= w * cb[i + j - 1]
        gross_pos[i:i + j] += d * w
    return pd.DataFrame({"pos": gross_pos, "net_bp": daily}, index=ctx.D.index)


def placebo_shift(ctx: Ctx, T: Target, dec: pd.DataFrame, a: int = 2010, b: int = 2026, reps: int = 2000, seed: int = 11) -> dict:
    """Timing placebo (added after the first run): the rule's own weekly call series (direction, 0 when silent) is
    rotated against the labels by a random offset of at least 26 weeks. This keeps the persistence and the long/short
    mix of the calls and the whole label path, and destroys only the timing. p = share of rotations that do as well."""
    valid = np.isfinite(T.long)
    g = np.arange(0, len(valid), STEP); g = g[valid[g]]
    g = g[(ctx.year[g] >= a) & (ctx.year[g] <= b)]
    x = dec[(dec["year"] >= a) & (dec["year"] <= b)]
    if len(x) < 10 or len(g) < 80:
        return {"placebo_p_acc": np.nan, "placebo_p_bp": np.nan, "placebo_mean_acc": np.nan}
    d = np.zeros(len(g)); d[np.searchsorted(g, x["i"].values)] = x["pos"].values
    L, S_ = T.long[g], T.short[g]

    def stat(dd):
        m = dd != 0
        gr = np.where(dd > 0, L, S_)[m]
        return float((gr > 0).mean()), float(gr.mean())

    oa, ob = stat(d)
    rng = np.random.default_rng(seed)
    sh = rng.integers(26, len(g) - 26, size=reps)
    res = np.array([stat(np.roll(d, int(k))) for k in sh])
    return {"placebo_p_acc": float((1 + (res[:, 0] >= oa).sum()) / (reps + 1)), "placebo_p_bp": float((1 + (res[:, 1] >= ob).sum()) / (reps + 1)),
            "placebo_mean_acc": float(res[:, 0].mean())}


def sharpe_periods(net: pd.Series) -> dict:
    out = {}
    for lab, a, b in PERIODS:
        x = net[(net.index.year >= a) & (net.index.year <= b)]
        ag = _agg(x, 252)
        out[f"sharpe_{lab}"] = ag["sharpe"]; out[f"t_{lab}"] = ag["t"]
    return out


# ================================================================ range / volatility forecasts
def har_design(D: pd.DataFrame, h: int):
    r = D["range_pips"]
    if h == 1:   # the scoreboard model: log r1, r5, r21 + event + Monday dummies, target = next session's range
        X = pd.DataFrame({"r1": r, "r5": r.rolling(5).mean(), "r21": r.rolling(21).mean()})
        extra = np.column_stack([(D["n_high_next_24h"] > 0).astype(float).values, (D["dow"] == 4).astype(float).values])
        y = r.shift(-1)
    else:
        X = pd.DataFrame({"r1": r, "r5": r.rolling(5).mean(), "r21": r.rolling(21).mean(), "r63": r.rolling(63).mean()})
        extra = np.zeros((len(D), 0))
        y = r.rolling(h).mean().shift(-h)
    okx = (X > 1.0).all(axis=1).values
    A = np.column_stack([np.ones(len(D)), np.log(X.where(X > 1.0).values), extra])
    return A, okx, y.values


def har_year(D: pd.DataFrame, design, h: int, Y: int):
    A, okx, y = design
    yr = D.index.year.values
    te = np.where((yr == Y) & okx)[0]
    q = np.searchsorted(D.index.values, np.datetime64(pd.Timestamp(f"{Y}-01-01")))
    tr = np.where(okx & np.isfinite(y) & (y > 1.0) & (np.arange(len(D)) + h <= q - 1))[0]
    if len(te) == 0 or len(tr) < 500:
        return None
    beta, *_ = np.linalg.lstsq(A[tr], np.log(y[tr]), rcond=None)
    return {"tr": tr, "te": te, "F_tr": np.exp(A[tr] @ beta), "F_te": np.exp(A[te] @ beta), "y_tr": y[tr]}


def range_forecast_1d(D: pd.DataFrame) -> pd.DataFrame:
    """OOS next-session range forecast with the trailing-250 median / 80th percentile of the training window."""
    des = har_design(D, 1)
    n = len(D)
    Fc = np.full(n, np.nan); med = np.full(n, np.nan); q80 = np.full(n, np.nan)
    for Y in YEARS:
        m = har_year(D, des, 1, Y)
        if m is None:
            continue
        Fc[m["te"]] = m["F_te"]; med[m["te"]] = np.median(m["y_tr"][-250:]); q80[m["te"]] = np.quantile(m["y_tr"][-250:], 0.8)
    return pd.DataFrame({"F": Fc, "med": med, "q80": q80}, index=D.index)


# ================================================================ (C) path / level events
def path_events(D: pd.DataFrame, ctx: Ctx) -> tuple[pd.DataFrame, pd.DataFrame]:
    c, hi, lo = D["close"].values, D["high"].values, D["low"].values
    atr = D["atr14_pips"].values
    n = len(D)
    lc = np.log(c)
    rec = []        # per test row and event: probabilities and outcomes
    for h in PATH_H:
        mx = pd.Series(hi).rolling(h).max().shift(-h).values
        mn = pd.Series(lo).rolling(h).min().shift(-h).values
        up = (mx - c) * 1e4; dn = (c - mn) * 1e4                 # pips
        ch = np.full(n, np.nan); ch[:n - h] = c[h:]
        des = har_design(D, h)
        for Y in YEARS:
            m = har_year(D, des, h, Y)
            if m is None:
                continue
            tr, te = m["tr"], m["te"]
            te = te[np.isfinite(up[te])]
            Fte = pd.Series(m["F_te"], index=m["te"]).reindex(te).values
            U_tr, U_te = m["F_tr"] * math.sqrt(h), Fte * math.sqrt(h)
            terc = np.quantile(m["F_tr"], [1 / 3, 2 / 3])
            fbin = np.where(Fte < terc[0], "F_low", np.where(Fte < terc[1], "F_mid", "F_high"))
            exc_tr = np.concatenate([up[tr], dn[tr]])
            exc_1y = np.sort(np.concatenate([up[tr[-250:]], dn[tr[-250:]]]))
            exc_all = np.sort(exc_tr)
            ecdf = lambda srt, v: np.searchsorted(srt, v, side="left") / len(srt)      # P(excursion < v)
            base = {"h": h, "i": te, "fbin": fbin}
            if h == 1:
                ratio_tr = m["y_tr"] / m["F_tr"]
                y_all, y_1y = np.sort(m["y_tr"]), np.sort(m["y_tr"][-250:])
                yte = D["range_pips"].shift(-1).values[te]
                for k in (1.0, 1.25, 1.5):
                    rec.append(pd.DataFrame({**base, "family": "range_below_kF", "param": k, "p_model": float((ratio_tr < k).mean()),
                                             "p_naive_all": ecdf(y_all, k * Fte), "p_naive_1y": ecdf(y_1y, k * Fte),
                                             "o_up": (yte < k * Fte).astype(float), "o_dn": np.nan, "pnl_fade": np.nan}))
            scaled_tr = exc_tr / np.concatenate([U_tr, U_tr])
            for u in U_GRID:
                d = u * U_te
                fade = _fade_pnl(c[te], ch[te], up[te], dn[te], d, ctx.cost_bp[te])
                rec.append(pd.DataFrame({**base, "family": "notouch_uF", "param": u, "p_model": float((scaled_tr < u).mean()),
                                         "p_naive_all": ecdf(exc_all, d), "p_naive_1y": ecdf(exc_1y, d),
                                         "o_up": (up[te] < d).astype(float), "o_dn": (dn[te] < d).astype(float), "pnl_fade": fade}))
            if h >= 10:
                sc_atr = exc_tr / np.concatenate([atr[tr], atr[tr]])
                for k in ATR_GRID:
                    d = k * atr[te]
                    fade = _fade_pnl(c[te], ch[te], up[te], dn[te], d, ctx.cost_bp[te])
                    rec.append(pd.DataFrame({**base, "family": "notouch_kATR", "param": k, "p_model": float((sc_atr < k).mean()),
                                             "p_naive_all": ecdf(exc_all, d), "p_naive_1y": ecdf(exc_1y, d),
                                             "o_up": (up[te] < d).astype(float), "o_dn": (dn[te] < d).astype(float), "pnl_fade": fade}))
    R = pd.concat(rec, ignore_index=True)
    R["year"] = ctx.year[R["i"].values]
    R["o"] = R[["o_up", "o_dn"]].mean(axis=1)
    two = R["o_dn"].notna()
    for nm in ("model", "naive_all", "naive_1y"):
        e_up = (R[f"p_{nm}"] - R["o_up"]) ** 2
        e_dn = (R[f"p_{nm}"] - R["o_dn"]) ** 2
        R[f"b_{nm}"] = np.where(two, 0.5 * (e_up + e_dn), e_up)
    rows = []
    for (fam, h, par), g0 in R.groupby(["family", "h", "param"]):
        g0 = g0[g0["i"] % STEP == 0] if h > 1 else g0          # multi-session windows: weekly grid
        L = 0 if h == 1 else int(math.ceil(1.5 * h / STEP))
        for lab, a, b in PERIODS:
            gp = g0[(g0["year"] >= a) & (g0["year"] <= b)]
            for bn in ("all", "F_low", "F_mid", "F_high"):
                g = gp if bn == "all" else gp[gp["fbin"] == bn]
                if len(g) < 20:
                    continue
                real = float(g["o"].mean())
                if bn == "all" and L > 0:
                    e = (g["o"].values - real)
                    Tn = len(e); lrv = float((e * e).sum()) / Tn
                    for l in range(1, min(L, Tn - 1) + 1):
                        lrv += 2 * (1 - l / (L + 1)) * float((e[l:] * e[:-l]).sum()) / Tn
                    ev = Tn * (2 if g["o_dn"].notna().any() else 1)          # upper and lower level are two events per session
                    neff = min(float(ev), max(1.0, real * (1 - real) / (lrv / Tn))) if 0 < real < 1 and lrv > 0 else float(ev)
                    neff = min(neff, max(1.0, ev * STEP / h))                 # conservative cap: non-overlapping windows only
                else:
                    neff = float(len(g))
                lo_, hi_ = wilson(real, neff)
                r = {"family": fam, "h": h, "param": par, "period": lab, "bin": bn, "n": len(g), "n_eff": neff,
                     "predicted": float(g["p_model"].mean()), "realised": real, "lo": lo_, "hi": hi_,
                     "brier_model": float(g["b_model"].mean()), "brier_naive_all": float(g["b_naive_all"].mean()),
                     "brier_naive_1y": float(g["b_naive_1y"].mean())}
                r["skill_vs_naive_all"] = 1 - r["brier_model"] / r["brier_naive_all"] if r["brier_naive_all"] > 0 else np.nan
                r["skill_vs_naive_1y"] = 1 - r["brier_model"] / r["brier_naive_1y"] if r["brier_naive_1y"] > 0 else np.nan
                if bn == "all" and g["pnl_fade"].notna().any():
                    x = g["pnl_fade"].values
                    r["fade_net_bp_per_decision"] = float(x.mean())
                    r["fade_fill_rate"] = float((x != 0).mean())
                    Tn = len(x); e = x - x.mean(); lrv = float((e * e).sum()) / Tn
                    for l in range(1, min(L, Tn - 1) + 1):
                        lrv += 2 * (1 - l / (L + 1)) * float((e[l:] * e[:-l]).sum()) / Tn
                    r["fade_t_nw"] = float(x.mean() / math.sqrt(lrv / Tn)) if lrv > 0 else np.nan
                rows.append(r)
    return pd.DataFrame(rows), R


def _fade_pnl(c, ch, up, dn, d, cost_bp):
    """The only spot expression of a no-touch call: resting orders that fade a touch of close +- d (pips) and are
    closed at the close of session h. Zero when the level is not touched. Net of a round trip per fill."""
    dpx = d * 1e-4
    short = np.where(up >= d, (np.log(c + dpx) - np.log(ch)) * 1e4 - 2 * cost_bp, 0.0)
    long = np.where(dn >= d, (np.log(ch) - np.log(np.maximum(c - dpx, 1e-9))) * 1e4 - 2 * cost_bp, 0.0)
    return short + long


# ================================================================ main computation
def compute(cost_pips: float = 1.2, verbose: bool = True, targets: list[str] | None = None, ctx: Ctx | None = None,
            T: dict | None = None, light: bool = False) -> dict:
    D = load_data() if ctx is None else ctx.D
    ctx = make_ctx(D, cost_pips) if ctx is None else ctx
    T = build_targets(D) if T is None else T
    names = targets or list(T)
    curves, decs, probs = [], {}, {}
    for nm in names:
        t = T[nm]
        log = {}
        wf = wf_target(ctx, t, log=log)
        probs[nm] = {"P": wf["P"], "log": log}
        valid = np.isfinite(t.long)
        for m in MODELS:
            P = wf["P"][m]
            for rule in [f"cov{int(c * 100)}" for c in COVERAGES] + [f"p{int(p * 100)}" for p in PTHR]:
                sp, dirs = speak_dir(P, rule, wf["THR"][m])
                for mode in ("weekly", "nonoverlap"):
                    if light and mode == "nonoverlap":
                        continue
                    idx = weekly_idx(sp, valid) if mode == "weekly" else seq_idx(sp, valid, t.hold)
                    dec = decision_frame(ctx, t, idx, dirs, P)
                    is_cand = any(c[1] == nm and c[2] == m and c[3] == rule for c in CANDIDATES)
                    for r in cell_stats(ctx, t, dec, sp, mode, boot=(mode == "weekly" and (rule.startswith("p") or is_cand))):
                        curves.append({"target": nm, "kind": t.kind, "h": t.h, "k_atr": t.k, "model": m, "rule": rule, "mode": mode, **r})
                    if mode == "weekly":
                        decs[(nm, m, rule)] = dec
        if verbose:
            print(f"  target {nm}: done", flush=True)
    return {"ctx": ctx, "T": T, "curves": pd.DataFrame(curves), "decs": decs, "probs": probs}


def selectors(ctx: Ctx, T: dict, res: dict, horizons=HORIZONS) -> pd.DataFrame:
    """(B) fixed agreement / regime selectors on the sign targets, weekly decisions (and the non-overlapping stream)."""
    D = ctx.D
    hs = house_score_wf(ctx)
    sg = np.sign(hs)
    cot, spr = np.sign(ctx.G["cot_z52"].values), np.sign(ctx.G["d_spread2y_20"].values)
    agree = np.isfinite(hs) & (sg != 0) & (cot == sg) & (spr == sg)
    trend = agree & (np.sign(ctx.G["dist_sma50_atr"].values) == sg) & (np.sign(ctx.G["dist_sma200_atr"].values) == sg)
    rf = range_forecast_1d(D)
    quiet = (rf["F"] < 0.85 * rf["med"]).values; vol = (rf["F"] > rf["q80"]).values
    evw = ((D[["h_to_fomc", "h_to_ecb", "h_to_nfp", "h_to_cpi"]] < 24).any(axis=1) | (D[["h_since_fomc", "h_since_ecb", "h_since_nfp", "h_since_cpi"]] < 24).any(axis=1)).values
    base = np.isfinite(hs) & (sg != 0)
    sel = {"house_sign_all": base, "agree3": agree, "agree3_trend": trend, "house_quiet": base & quiet, "house_volatile": base & vol,
           "house_nonevent": base & ~evw, "house_event": base & evw}
    rows = []
    for h in horizons:
        t = T[f"sign{h}"]
        valid = np.isfinite(t.long)
        for nm, sp in sel.items():
            dec = decision_frame(ctx, t, weekly_idx(sp, valid), sg, None)
            res["decs"][(t.name, f"B:{nm}", "filter")] = dec
            for r in cell_stats(ctx, t, dec, sp, "weekly", boot=True):
                rows.append({"target": t.name, "kind": "sign", "h": h, "k_atr": 0.0, "model": f"B:{nm}", "rule": "filter", "mode": "weekly", **r})
            dn = decision_frame(ctx, t, seq_idx(sp, valid, t.hold), sg, None)
            for r in cell_stats(ctx, t, dn, sp, "nonoverlap"):
                rows.append({"target": t.name, "kind": "sign", "h": h, "k_atr": 0.0, "model": f"B:{nm}", "rule": "filter", "mode": "nonoverlap", **r})
    res["house_score"] = hs
    res["selector_masks"] = sel
    res["range_fc"] = rf
    return pd.DataFrame(rows)


def expectancy_rows(ctx: Ctx, T: dict, res: dict, cells: list[tuple], cost_pips: float) -> pd.DataFrame:
    """(D) for each (target, model, rule) weekly cell: win/loss/expectancy and the two trading books."""
    C = res["curves_all"]
    rows = []
    for (nm, m, rule) in cells:
        t = T[nm]
        dec = res["decs"][(nm, m, rule)]
        st = C[(C.target == nm) & (C.model == m) & (C.rule == rule) & (C["mode"] == "weekly")].set_index("period")
        r = {"target": nm, "model": m, "rule": rule}
        for lab, _, _ in PERIODS:
            if lab in st.index:
                for k in ("n", "dec_per_year", "accuracy", "lo", "hi", "win_rate_net", "avg_win_bp", "avg_loss_bp", "net_bp", "avg_hold"):
                    r[f"{k}_{lab}"] = st.loc[lab].get(k, np.nan)
        te = book_time_exit(ctx, dec, t.h, cost_pips)
        for k, v in sharpe_periods(te["net_bp"][te.index.year >= 2010]).items():
            r[f"timeexit_{k}"] = v
        tb = t if t.kind == "tb" else T[f"tb{t.h}_{SYM_K[t.h]}atr"] if f"tb{t.h}_{SYM_K[t.h]}atr" in T else None
        if tb is not None:
            bb = book_barrier(ctx, dec, tb, cost_pips)
            for k, v in sharpe_periods(bb["net_bp"][bb.index.year >= 2010]).items():
                r[f"symexit_{k}"] = v
            r["symexit_barrier"] = f"{int(tb.k)} ATR / {tb.h} sessions"
        r.update(placebo_shift(ctx, t, dec))
        for k, v in placebo_shift(ctx, t, dec, 2016, 2026).items():
            r[f"{k}_2016-26"] = v
        rows.append(r)
    return pd.DataFrame(rows)


def reliability(ctx: Ctx, T: dict, res: dict) -> pd.DataFrame:
    """Predicted confidence vs realised accuracy by confidence bucket (weekly decisions, all three models)."""
    edges = [0.5, 0.55, 0.60, 0.65, 0.70, 1.0001]
    rows = []
    for nm, pr in res["probs"].items():
        t = T[nm]
        if t.h < 10:
            continue
        valid = np.isfinite(t.long)
        g = np.arange(0, len(valid), STEP); g = g[valid[g]]
        for m in MODELS:
            P = pr["P"][m]
            gg = g[np.isfinite(P[g])]
            conf = np.maximum(P[gg], 1 - P[gg]); d = np.where(P[gg] > 0.5, 1.0, -1.0)
            hit = (np.where(d > 0, t.long[gg], t.short[gg]) > 0).astype(float)
            for lab, a, b in PERIODS:
                py = (ctx.year[gg] >= a) & (ctx.year[gg] <= b)
                for lo_, hi_ in zip(edges[:-1], edges[1:]):
                    k = py & (conf >= lo_) & (conf < hi_)
                    if k.sum() == 0:
                        continue
                    s = (py & (conf >= lo_) & (conf < hi_))[py].astype(float)
                    neff = nw_neff(s, hit[py] * s, int(math.ceil(1.5 * t.h / STEP)))
                    acc = float(hit[k].mean()); wl, wh = wilson(acc, neff)
                    rows.append({"target": nm, "model": m, "period": lab, "bucket": f"{lo_:.2f}-{min(hi_, 1.0):.2f}", "n": int(k.sum()), "n_eff": neff,
                                 "mean_predicted": float(conf[k].mean()), "realised": acc, "lo": wl, "hi": wh})
    return pd.DataFrame(rows)


def select_final(C: pd.DataFrame, bound: str = "lo") -> tuple[pd.DataFrame, str | None, str, str | None]:
    """Applies the declared rule. Returns the candidate table, the final over all 12 candidates, its status, and the
    pick of the same rule restricted to the ten probability-call (P >= 60 %) candidates."""
    rows = []
    for name, tg, m, rule in CANDIDATES:
        x = C[(C.target == tg) & (C.model == m) & (C.rule == rule) & (C["mode"] == "weekly")].set_index("period")
        r = {"candidate": name, "target": tg, "model": m, "rule": rule}
        for lab, _, _ in PERIODS:
            for k in ("n", "n_eff", "n_eff_cons", "dec_per_year", "accuracy", "lo", "hi", "lo_cons", "hi_cons", "boot_lo", "boot_hi", "base_up",
                      "chance_acc", "net_bp", "gross_bp", "win_rate_net", "avg_win_bp", "avg_loss_bp", "avg_hold", "share_long"):
                r[f"{k}_{lab}"] = x.loc[lab].get(k, np.nan) if lab in x.index else np.nan
        r["enough_decisions"] = bool(r["dec_per_year_2010-15"] >= MIN_DEC_PER_YEAR)
        r["positive_expectancy_2010-15"] = bool(r["net_bp_2010-15"] > 0)
        r["eligible"] = r["enough_decisions"] and r["positive_expectancy_2010-15"]
        rows.append(r)
    S = pd.DataFrame(rows)
    key = f"{bound}_2010-15"

    def pick(tab):
        el = tab[tab["eligible"]]
        if len(el):
            return el.sort_values(key, ascending=False)["candidate"].iloc[0], "selected by the declared rule"
        en = tab[tab["enough_decisions"] & tab[key].notna()]
        pool = en if len(en) else tab[tab[key].notna()]
        return (pool.sort_values(key, ascending=False)["candidate"].iloc[0] if len(pool) else None), "NO candidate eligible - nominal stream only (fails the declared rule)"

    final, status = pick(S)
    final_p60, _ = pick(S[S["rule"] == "p60"])
    S["final"] = S["candidate"] == final
    S["final_p60"] = S["candidate"] == final_p60
    return S, final, status, final_p60


def rule_history_prob(ctx: Ctx, T: dict, target: str = "sign21", sel: str = "agree3") -> tuple[np.ndarray, pd.DataFrame]:
    """Calibrated probability of a FIXED rule = its own hit rate on weekly decisions whose label was known before the
    test year (house score walk-forward from 2006, so 2006-2009 serve as history for 2010), Laplace-smoothed.
    Information only: it gates nothing."""
    hs = house_score_wf(ctx, years=list(range(2006, 2027)))
    sg = np.sign(hs)
    sp = np.isfinite(hs) & (sg != 0) & (np.sign(ctx.G["cot_z52"].values) == sg) & (np.sign(ctx.G["d_spread2y_20"].values) == sg)
    if sel == "agree3_trend":
        sp = sp & (np.sign(ctx.G["dist_sma50_atr"].values) == sg) & (np.sign(ctx.G["dist_sma200_atr"].values) == sg)
    t = T[target]
    idx = weekly_idx(sp, np.isfinite(t.long))
    hit = (np.where(sg[idx] > 0, t.long[idx], t.short[idx]) > 0).astype(float)
    pc = np.full(len(hs), np.nan)
    rows = []
    for Y in YEARS:
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC").value
        k = (t.end[idx] != NAT) & (t.end[idx] < start)
        n, h = int(k.sum()), float(hit[k].sum())
        p = (h + 1) / (n + 2)
        pc[ctx.year == Y] = p
        rows.append({"test_year": Y, "history_decisions": n, "history_hit_rate": h / n if n else np.nan, "prob_correct_used": p})
    return pc, pd.DataFrame(rows)


def by_year(dec: pd.DataFrame) -> pd.DataFrame:
    g = dec[dec.index.year >= 2010].groupby("year")
    return pd.DataFrame({"decisions": g.size(), "long_share": g["pos"].apply(lambda x: float((x > 0).mean())), "accuracy": g["hit"].mean(),
                         "net_win_rate": g["net_bp"].apply(lambda x: float((x > 0).mean())), "gross_bp": g["gross_bp"].mean(),
                         "net_bp": g["net_bp"].mean(), "avg_hold": g["hold"].mean()}).reset_index()


def _cand(name):
    return next(c for c in CANDIDATES if c[0] == name)


def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Runs every target / model / rule walk-forward, applies the declared selection rule and writes the deliverables.
    Returns (decision positions of the final rule as a Series, report DataFrame)."""
    res = compute(cost_pips, verbose=verbose)
    ctx, T = res["ctx"], res["T"]
    B = selectors(ctx, T, res)
    res["curves_all"] = pd.concat([res["curves"], B], ignore_index=True)
    C = res["curves_all"]
    S, final, status, final_p60 = select_final(C)
    res["selection"], res["final"], res["final_status"], res["final_p60"] = S, final, status, final_p60
    res["selection_sensitivity"] = {b: select_final(C, b)[1::2] for b in ("lo", "lo_cons", "boot_lo")}
    # (D) expectancy: all candidates + every weekly cell with accuracy >= 60 % on 2010-26 and at least 30 decisions
    hi = C[(C["mode"] == "weekly") & (C.period == "2010-26") & (C.accuracy >= 0.60) & (C.n >= 30) & (C.h >= 10)]
    cells = [(c[1], c[2], c[3]) for c in CANDIDATES]
    cells += [k for k in zip(hi.target, hi.model, hi.rule) if k not in cells]
    E = expectancy_rows(ctx, T, res, cells, cost_pips)
    E.insert(0, "candidate", [next((c[0] for c in CANDIDATES if (c[1], c[2], c[3]) == k), "") for k in cells])
    res["expectancy"] = E
    res["reliability"] = reliability(ctx, T, res)
    PC, PR = path_events(ctx.D, ctx)
    res["path"] = PC
    pc, hist = rule_history_prob(ctx, T, "sign21", "agree3")
    res["agree3_history"] = hist
    # report table (protocol format) for every candidate: weekly-tranche book, daily
    reps, streams = [], {}

    def book(name, cx, cp):
        _, tg, m, rule = _cand(name)
        t = T[tg]; dec = res["decs"][(tg, m, rule)]
        pnl = book_barrier(cx, dec, t, cp) if t.kind == "tb" else book_time_exit(cx, dec, t.h, cp)
        return pnl[pnl.index.year >= 2010]

    for name, tg, m, rule in CANDIDATES:
        streams[name] = book(name, ctx, cost_pips)
        tb = report(streams[name], periods_per_year=252, name=ARM, n_arms=N_ARMS)
        tb.insert(1, "variant", name); tb["final"] = name == final; tb["final_p60"] = name == final_p60
        tb["kind"] = "candidate"; tb["cost_pips"] = cost_pips
        reps.append(tb)
    for name in dict.fromkeys([f for f in (final, final_p60) if f is not None]):
        tb = report(book(name, make_ctx(ctx.D, 0.6), 0.6), periods_per_year=252, name=ARM, n_arms=N_ARMS)
        tb.insert(1, "variant", f"{name}_cost0.6"); tb["final"] = False; tb["final_p60"] = False; tb["kind"] = "cost_sensitivity"; tb["cost_pips"] = 0.6
        reps.append(tb)
    rep = pd.concat(reps, ignore_index=True)
    res["report"], res["streams"] = rep, streams
    pos = pd.Series(dtype=float)
    outs = {}
    for tag, name in (("", final), ("_p60", final_p60)):
        if name is None:
            continue
        _, tg, m, rule = _cand(name)
        dec = res["decs"][(tg, m, rule)]
        out = dec[["pos", "fwd_bp", "net_bp", "prob", "gross_bp", "hit", "hold"]].copy()
        if m.startswith("B:agree3") and tg == "sign21" and m == "B:agree3":
            out["prob"] = np.where(out["pos"] > 0, pc[dec["i"].values], 1 - pc[dec["i"].values])   # P(up) from the rule's own history
        out = out[out.index.year >= 2010]
        daily = streams[name].copy()
        daily["fwd_bp"] = ctx.D["fwd_1d"].reindex(daily.index)
        outs[tag] = (name, out, daily[["pos", "fwd_bp", "net_bp"]])
        res[f"by_year{tag}"] = by_year(dec)
    if "" in outs:
        pos = outs[""][1]["pos"]
    res["outs"] = outs
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        for tag, (name, out, daily) in outs.items():
            out.to_parquet(RES / f"{ARM}{tag}_positions.parquet")
            daily.to_parquet(RES / f"{ARM}{tag}_daily_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        C.to_csv(RES / f"{ARM}_accuracy_coverage.csv", index=False)
        PC.to_csv(RES / f"{ARM}_path_calibration.csv", index=False)
        S.to_csv(RES / f"{ARM}_candidates.csv", index=False)
        E.to_csv(RES / f"{ARM}_expectancy.csv", index=False)
        res["reliability"].to_csv(RES / f"{ARM}_reliability.csv", index=False)
    run.last = res
    return pos, rep


# ================================================================ incremental value and leak checks
def incremental(tag: str = "") -> pd.DataFrame:
    """EW(weak_signals, regime_trend) against EW(weak_signals, regime_trend, this arm's daily book)."""
    from eurusd.arms.meta import combine, load_arm_daily, report_combo
    arm = f"{ARM}{tag}_daily"
    two, _ = combine(["weak_signals", "regime_trend"], "EW")
    three, w = combine(["weak_signals", "regime_trend", arm], "EW")
    out = pd.concat([report_combo(two, "weak_signals+regime_trend", 2), report_combo(three, f"+{ARM}{tag}", 3)], ignore_index=True)
    s = load_arm_daily(arm)
    for o in ("weak_signals", "regime_trend"):
        x = pd.concat([s, load_arm_daily(o)], axis=1).dropna()
        x = x[x.index.year >= 2010]
        out[f"corr_{o}"] = float(x.corr().iloc[0, 1])
    out["stream"] = arm
    return out


def leak_checks(res: dict, cost_pips: float = 1.2, seed: int = 0) -> pd.DataFrame:
    """(1) labels shuffled (all labels, including the 1-session return the house weights are fitted on);
    (2) features made staler by 1 / 21 / 63 sessions and, as a control that the harness WOULD expose a look-ahead,
    features taken from h sessions in the future; (3) top logit coefficients / house weights."""
    ctx, T = res["ctx"], res["T"]
    todo = sorted({_cand(f)[1] for f in (res["final"], res["final_p60"]) if f} | {"sign21"})
    rows = []

    def summarise(label, C, nm, cells):
        for m, rule in cells:
            x = C[(C.target == nm) & (C.model == m) & (C.rule == rule) & (C["mode"] == "weekly")]
            for _, q in x.iterrows():
                rows.append({"check": label, "target": nm, "model": m, "rule": rule, "period": q["period"], "n": q["n"], "accuracy": q.get("accuracy"),
                             "lo": q.get("lo"), "hi": q.get("hi"), "base_up": q.get("base_up"), "chance_acc": q.get("chance_acc"), "net_bp": q.get("net_bp")})

    mcells = (("avg", "cov100"), ("avg", "cov10"), ("avg", "p60"), ("house", "cov100"), ("house", "cov25"), ("house", "p60"), ("logit", "cov100"), ("logit", "p60"))
    bcells = (("B:house_sign_all", "filter"), ("B:agree3", "filter"), ("B:agree3_trend", "filter"))

    def both(label, cx, Tx, nm):
        summarise(label, compute(cost_pips, False, [nm], cx, Tx, light=True)["curves"], nm, mcells)
        if nm.startswith("sign"):
            summarise(label, selectors(cx, Tx, {"decs": {}}, horizons=(Tx[nm].h,)), nm, bcells)

    for nm in todo:
        t = T[nm]
        both("baseline", ctx, T, nm)
        rng = np.random.default_rng(seed)
        for s in range(3):
            perm = rng.permutation(len(t.y))
            Ts = dict(T); Ts[nm] = t.permuted(perm)
            both(f"shuffled_labels_{s}", ctx.with_fwd1(ctx.fwd1[perm]), Ts, nm)
        for lag in (1, 21, 63):
            both(f"features_stale_plus{lag}", ctx.shifted(lag), T, nm)
        both(f"lookahead_control_minus{t.h}", ctx.shifted(-t.h), T, nm)
    L = pd.DataFrame(rows)
    # (3) top logit coefficients of the last fit, and each standardised feature's correlation with the label
    feats = []
    for nm in todo:
        lg = res["probs"][nm]["log"]
        Y = max(lg)
        mu, sd, lr = lg[Y]["logit"]
        if lr is None:
            continue
        coef = pd.Series(lr.coef_[0], index=ctx.xcols)
        Z = np.nan_to_num(np.clip((ctx.X - mu) / sd, -5, 5))
        y = T[nm].y
        ok = np.isfinite(y)
        cor = pd.Series([np.corrcoef(Z[ok, j], y[ok])[0, 1] if Z[ok, j].std() > 0 else 0.0 for j in range(Z.shape[1])], index=ctx.xcols)
        for f in coef.abs().sort_values(ascending=False).head(10).index:
            feats.append({"target": nm, "fit_year": Y, "model": "logit", "feature": f, "weight": float(coef[f]), "corr_with_label_full_sample": float(cor[f])})
        st, w = lg[Y]["house"]
        Zh = WS._scaler_apply(ctx.S, st)
        for sname, wt in zip(WS.SIGNALS, w):
            c = float(np.corrcoef(Zh[sname].values[ok], y[ok])[0, 1]) if Zh[sname].values[ok].std() > 0 else 0.0
            feats.append({"target": nm, "fit_year": Y, "model": "house", "feature": sname, "weight": float(wt), "corr_with_label_full_sample": c})
        feats.append({"target": nm, "fit_year": Y, "model": "logit", "feature": "MAX |corr| of any of the 82 logit columns with the label", "weight": np.nan,
                      "corr_with_label_full_sample": float(cor.abs().max())})
    res["leak"], res["leak_features"] = L, pd.DataFrame(feats)
    return L


# ================================================================ report
ORDER = [f"sign{h}" for h in HORIZONS] + [f"tb{h}_{k}atr" for h, k in TB]
COVR = ["cov100", "cov50", "cov25", "cov10", "cov5"]
P3 = ("2010-26", "2016-26", "2023-26")


def _fmt(q, bp: bool = False) -> str:
    if not np.isfinite(q.get("accuracy", np.nan)) or q["n"] == 0:
        return "-"
    lo, hi = (q["lo_cons"], q["hi_cons"]) if np.isfinite(q.get("lo_cons", np.nan)) else (q["lo"], q["hi"])
    s = f"{100 * q['accuracy']:.0f} [{100 * lo:.0f}-{100 * hi:.0f}] n={int(q['n'])}"
    return s + (f" {q['net_bp']:+.0f}bp" if bp else "")


def _piv(C, mask, cols, index="target", columns="rule", order=None, bp=False) -> str:
    x = C[mask].copy()
    if x.empty:
        return "(no rows)"
    x["s"] = x.apply(lambda q: _fmt(q, bp), axis=1)
    t = x.pivot(index=index, columns=columns, values="s").reindex(columns=cols)
    t = t.reindex([o for o in (order or ORDER) if o in t.index]).fillna("-")
    return t.to_markdown()


def write_report(K: dict, path: Path | None = None) -> None:
    C, S, E, R, P, L = K["curves_all"], K["selection"], K["expectancy"], K["reliability"], K["path"], K["leak"]
    W, Wn = C["mode"] == "weekly", C["mode"] == "nonoverlap"
    main = C["h"] >= 10
    bcol = [("B:house_sign_all", "filter", "always on: raw house-score sign (100 %)"), ("B:agree3", "filter", "three-way agreement (44 %)"),
            ("house", "cov25", "calibrated house score, 25 %"), ("house", "cov10", "10 %"), ("house", "cov5", "5 %")]
    summ = []
    for per in P3:
        rows = []
        for h in HORIZONS:
            r = {"hold (sessions)": h}
            for m, rule, lab in bcol:
                w = C[W & (C.target == f"sign{h}") & (C.model == m) & (C.rule == rule) & (C.period == per)]
                n_ = C[Wn & (C.target == f"sign{h}") & (C.model == m) & (C.rule == rule) & (C.period == per)]
                r[lab] = f"W {_fmt(w.iloc[0])} / N {_fmt(n_.iloc[0])}"
            rows.append(r)
        summ.append(f"*{per}*\n\n" + pd.DataFrame(rows).to_markdown(index=False))
    pa = P[(P.bin == "all") & P.h.isin([10, 21]) & (((P.family == "notouch_kATR") & P.param.isin([2.0, 3.0])) | ((P.family == "notouch_uF") & P.param.isin([0.75, 1.0])))]
    rows = []
    for (fam, h, par), g in pa.groupby(["family", "h", "param"]):
        g = g.set_index("period")
        rows.append({"window (sessions)": h, "level": f"{par:g} x ATR14" if fam == "notouch_kATR" else f"{par:g} x forecast vol (U)",
                     "predicted %": round(100 * g.loc["2010-26", "predicted"], 1),
                     **{f"realised % {per}": f"{100 * g.loc[per, 'realised']:.1f} [{100 * g.loc[per, 'lo']:.0f}-{100 * g.loc[per, 'hi']:.0f}]" for per in P3},
                     "Brier skill vs naive %": round(100 * g.loc["2010-26", "skill_vs_naive_1y"], 1),
                     "fade net bp / decision (t)": f"{g.loc['2010-26', 'fade_net_bp_per_decision']:+.1f} ({g.loc['2010-26', 'fade_t_nw']:+.1f})"})
    md = [VERDICT_MD.strip().replace("{SUMMARY_DIRECTION}", "\n\n".join(summ)).replace("{SUMMARY_PATH}", pd.DataFrame(rows).to_markdown(index=False)), ""]
    a = md.append
    a("## 1. Targets")
    a("`up_share` = share of sessions 2003-2026 on which a long would have closed in profit; `resolved_share` = barrier hit before the time-out.")
    a(K["targets"].round(3).to_markdown(index=False)); a("")
    a("## 2. (A) Accuracy-coverage curves, direction")
    a("Cells: accuracy % [95 % interval] n decisions. Weekly tables: decisions every 5th session, overlapping holds; the interval is "
      "Wilson with the SMALLER of the Newey-West effective n and n x 5 / holding period (the conservative one; the Newey-West-only "
      "interval, the block bootstrap and every other column are in `selective_accuracy_coverage.csv`). Non-overlapping tables: plain Wilson.")
    for m in MODELS:
        for per in P3 if m == "house" else ("2010-26",):
            a(f"\n**{m} model, weekly decisions, {per}**\n"); a(_piv(C, W & main & (C.model == m) & (C.period == per), COVR))
        for per in P3 if m == "house" else (("2010-26",) if m == "avg" else ()):
            a(f"\n**{m} model, NON-OVERLAPPING decisions, {per}**\n"); a(_piv(C, Wn & main & (C.model == m) & (C.period == per), COVR))
    a("\n**Net P&L per decision (bp, after a 2 x 1.2 pip round trip), house model, weekly: 2010-26 / 2016-26 / 2023-26**\n")
    x = C[W & main & (C.model == "house") & C.rule.isin(COVR) & C.period.isin(P3)]
    t = x.pivot_table(index=["target", "rule"], columns="period", values="net_bp").reindex(columns=list(P3))
    t["s"] = t.apply(lambda q: " / ".join("-" if not np.isfinite(v) else f"{v:+.0f}" for v in q), axis=1)
    a(t["s"].unstack("rule").reindex(columns=COVR).reindex(ORDER).to_markdown())
    a("\n**Is the 10 % cell evidence? accuracy at 10 % coverage against the majority base rate (max of up-share, 1 - up-share), 2010-26**\n")
    rows = []
    for m in ("house", "avg"):
        for tg in ORDER:
            w = C[W & (C.model == m) & (C.target == tg) & (C.rule == "cov10") & (C.period == "2010-26")]
            n_ = C[Wn & (C.model == m) & (C.target == tg) & (C.rule == "cov10") & (C.period == "2010-26")]
            if w.empty or n_.empty:
                continue
            w, n_ = w.iloc[0], n_.iloc[0]
            rows.append({"model": m, "target": tg, "majority base %": round(100 * w["majority_base"], 1), "weekly": _fmt(w),
                         "weekly lower bound > base (NW / conservative)": f"{'yes' if w['excl_base'] else 'no'} / {'yes' if w['excl_base_cons'] else 'no'}",
                         "non-overlapping": _fmt(n_), "non-overlapping lower bound > base": "yes" if n_["excl_base"] else "no"})
    a(pd.DataFrame(rows).to_markdown(index=False))
    a("\n### Probability rules: speak only when the calibrated probability is at least 55 / 60 / 65 %")
    for m in MODELS:
        a(f"\n**{m} model, weekly, 2010-26**\n"); a(_piv(C, W & main & (C.model == m) & (C.period == "2010-26"), ["p55", "p60", "p65"]))
    a("\n**P >= 60 % calls by period (weekly; accuracy [interval] n, net bp per decision)**\n")
    x = C[W & main & (C.rule == "p60") & C.period.isin(P3) & C.model.isin(MODELS)].copy()
    x["s"] = x.apply(lambda q: _fmt(q, True), axis=1); x["mp"] = x["model"] + " " + x["period"]
    a(x.pivot(index="target", columns="mp", values="s").reindex(columns=[f"{m} {p_}" for m in MODELS for p_ in P3]).reindex(ORDER).fillna("-").to_markdown())
    a("\n**Reliability, 2010-26, weekly: realised accuracy % (mean predicted confidence %) n, by confidence bucket**\n")
    for m in ("house", "avg"):
        x = R[(R.model == m) & (R.period == "2010-26")].copy()
        x["s"] = x.apply(lambda q: f"{100 * q.realised:.0f} ({100 * q.mean_predicted:.0f}) n={q.n}", axis=1)
        a(f"\n*{m}*\n"); a(x.pivot(index="target", columns="bucket", values="s").reindex(ORDER).fillna("-").to_markdown())
    a("\n### Optional diagnostics: 1- and 5-session direction (non-overlapping, 2010-26)\n")
    x = C[Wn & (C["h"] < 10) & (C.period == "2010-26")].copy(); x["s"] = x.apply(_fmt, axis=1); x["tm"] = x["target"] + " " + x["model"]
    a(x.pivot(index="tm", columns="rule", values="s").reindex(columns=COVR + ["p55", "p60"]).fillna("-").to_markdown())
    a("\n## 3. (B) Agreement and regime selectors (fixed rules, sign targets)")
    a("Direction = sign of the walk-forward house score. Cells: accuracy % [interval] n, net bp per decision.")
    bsel = ["B:house_sign_all", "B:agree3", "B:agree3_trend", "B:house_quiet", "B:house_volatile", "B:house_nonevent", "B:house_event"]
    for mode, mk in (("weekly", W), ("NON-OVERLAPPING", Wn)):
        for per in P3:
            a(f"\n**{mode}, {per}**\n")
            a(_piv(C, mk & C.model.str.startswith("B:") & (C.period == per), [f"sign{h}" for h in HORIZONS], index="model", columns="target", order=bsel, bp=True))
    a("\n## 4. (C) Path / level events: calibration and Brier score")
    a("`predicted` = model probability (training-window frequency of the scaled excursion), `realised` = out-of-sample frequency. "
      "Skill = 1 - Brier(model) / Brier(naive); naive = unconditional training distribution in pips (whole window / trailing 250 sessions). "
      "Multi-session windows are sampled weekly; interval = Wilson with min(Newey-West effective n, non-overlapping count).")
    pp = P[P.bin == "all"]
    def ptab(fam, h):
        x = pp[(pp.family == fam) & (pp.h == h)]
        b = x[x.period == "2010-26"].set_index("param")
        o = pd.DataFrame({"predicted %": (100 * b.predicted).round(1), "realised % 2010-26": (100 * b.realised).round(1),
                          "95 % interval": [f"{100 * l_:.0f}-{100 * h_:.0f}" for l_, h_ in zip(b.lo, b.hi)], "n": b.n,
                          "realised % 2016-26": (100 * x[x.period == "2016-26"].set_index("param").realised).round(1),
                          "realised % 2023-26": (100 * x[x.period == "2023-26"].set_index("param").realised).round(1),
                          "Brier model": b.brier_model.round(4), "Brier naive (all)": b.brier_naive_all.round(4), "Brier naive (1y)": b.brier_naive_1y.round(4),
                          "skill vs naive 1y %": (100 * b.skill_vs_naive_1y).round(1),
                          "skill 2023-26 %": (100 * x[x.period == "2023-26"].set_index("param").skill_vs_naive_1y).round(1)})
        if "fade_net_bp_per_decision" in b and b["fade_net_bp_per_decision"].notna().any():
            o["fade: net bp / decision (t)"] = [f"{v:+.1f} ({t_:+.1f})" for v, t_ in zip(b.fade_net_bp_per_decision, b.fade_t_nw)]
        return o.to_markdown()
    a("\n**(i) next-session range stays below k x forecast range** (param = k)\n"); a(ptab("range_below_kF", 1))
    for h in PATH_H:
        a(f"\n**(ii) price does NOT touch a level u x U away within {h} session(s)** (param = u; U = forecast mean daily range x sqrt({h}); upper and lower level pooled)\n")
        a(ptab("notouch_uF", h))
    for h in (10, 21):
        a(f"\n**(ii) price does NOT touch a level k x ATR14 away within {h} sessions** (param = k)\n"); a(ptab("notouch_kATR", h))
    a("\n**Calibration inside volatility regimes (terciles of the forecast, 2010-26): realised % (predicted %)**\n")
    x = P[(P.bin != "all") & (P.period == "2010-26") & (((P.family == "notouch_uF") & P.param.isin([0.75, 1.0])) | ((P.family == "notouch_kATR") & P.param.isin([2.0, 3.0])))].copy()
    x["ev"] = x.family + " h=" + x.h.astype(str) + " param=" + x.param.astype(str)
    x["s"] = x.apply(lambda q: f"{100 * q.realised:.0f} ({100 * q.predicted:.0f}) n={q.n}", axis=1)
    a(x.pivot(index="ev", columns="bin", values="s").reindex(columns=["F_low", "F_mid", "F_high"]).to_markdown())
    a("\n## 5. (D) Expectancy: accuracy is not edge")
    a("Every candidate, then the weekly cells with accuracy >= 60 % on 2010-26 and at least 150 decisions (all 73 cells with >= 30 decisions are in "
      "`selective_expectancy.csv`). win / loss = average net bp of winning / "
      "losing decisions; Sharpe = net, daily, weekly-tranche book (time exit at the horizon | symmetric stop/target with time-out). "
      "`placebo p` = share of 2,000 random rotations of the rule's own call series (>= 26 weeks) that reach the same accuracy / mean bp.")
    e = E[(E["candidate"] != "") | (E["n_2010-26"] >= 150)].copy()
    e["rule"] = np.where(e["candidate"] != "", e["candidate"], e["target"] + " " + e["model"] + " " + e["rule"])
    o = pd.DataFrame({"rule": e["rule"], "n": e["n_2010-26"].astype(int), "dec/yr": e["dec_per_year_2010-26"].round(1), "acc %": (100 * e["accuracy_2010-26"]).round(0),
                      "win": e["avg_win_bp_2010-26"].round(0), "loss": e["avg_loss_bp_2010-26"].round(0),
                      "net bp 10-26 / 16-26 / 23-26": [" / ".join("-" if not np.isfinite(v) else f"{v:+.0f}" for v in q) for q in e[["net_bp_2010-26", "net_bp_2016-26", "net_bp_2023-26"]].values],
                      "hold": e["avg_hold_2010-26"].round(0),
                      "Sharpe time exit 10-26 / 16-26 / 23-26": [" / ".join(f"{v:+.2f}" for v in q) for q in e[["timeexit_sharpe_2010-26", "timeexit_sharpe_2016-26", "timeexit_sharpe_2023-26"]].values],
                      "Sharpe stop/target 10-26 / 16-26 / 23-26": [" / ".join(f"{v:+.2f}" for v in q) for q in e[["symexit_sharpe_2010-26", "symexit_sharpe_2016-26", "symexit_sharpe_2023-26"]].values],
                      "placebo p acc / bp": [f"{x_:.2f} / {y_:.2f}" if np.isfinite(x_) else "-" for x_, y_ in zip(e["placebo_p_acc"], e["placebo_p_bp"])]})
    a(o.to_markdown(index=False))
    a("\n## 6. Final selection (declared rule) and the record of the picks")
    cs = pd.DataFrame({"candidate": S.candidate, "n 10-15": S["n_2010-15"].astype(int), "dec/yr 10-15": S["dec_per_year_2010-15"].round(1),
                       "acc % 10-15": (100 * S["accuracy_2010-15"]).round(1), "lower bound % (NW)": (100 * S["lo_2010-15"]).round(1),
                       "lower % (conservative)": (100 * S["lo_cons_2010-15"]).round(1), "lower % (bootstrap)": (100 * S["boot_lo_2010-15"]).round(1),
                       "net bp 10-15": S["net_bp_2010-15"].round(1), ">= 15/yr": S.enough_decisions, "expectancy > 0": S["positive_expectancy_2010-15"],
                       "eligible": S.eligible, "final": S.final, "P>=60 pick": S.final_p60})
    a(cs.to_markdown(index=False))
    a(f"\nSelection under the three interval variants (all 12 / P >= 60 % only): {K['selection_sensitivity']}\n")
    for tag, nm in (("", K["final"]), ("_p60", K["final_p60"])):
        if nm is None:
            continue
        q = S[S.candidate == nm].iloc[0]
        a(f"\n### `{nm}`" + (" - FINAL by the declared rule" if tag == "" else " - pick of the same rule among the ten P >= 60 % probability calls"))
        rows = []
        for per in ("2010-15",) + P3:
            g = lambda k: q[f"{k}_{per}"]
            rows.append({"period": per, "decisions": int(g("n")), "per year": round(g("dec_per_year"), 1), "correct sign before costs %": round(100 * g("accuracy"), 1),
                         "interval NW": f"{100 * g('lo'):.0f}-{100 * g('hi'):.0f}", "interval conservative": f"{100 * g('lo_cons'):.0f}-{100 * g('hi_cons'):.0f}",
                         "interval bootstrap": f"{100 * g('boot_lo'):.0f}-{100 * g('boot_hi'):.0f}", "eff. n NW / cons": f"{g('n_eff'):.0f} / {g('n_eff_cons'):.0f}",
                         "up base %": round(100 * g("base_up"), 1), "no-skill acc %": round(100 * g("chance_acc"), 1), "positive net P&L %": round(100 * g("win_rate_net"), 1),
                         "avg win bp": round(g("avg_win_bp")), "avg loss bp": round(g("avg_loss_bp")), "net bp / decision": round(g("net_bp"), 1),
                         "avg hold (sessions)": round(g("avg_hold"), 1), "long share %": round(100 * g("share_long"))})
        a(pd.DataFrame(rows).to_markdown(index=False))
        a("\nNon-overlapping stream of the same rule: " + "; ".join(
            f"{per} {_fmt(x_.iloc[0], True)}" for per in P3
            for x_ in [C[Wn & (C.target == q['target']) & (C.model == q['model']) & (C.rule == q['rule']) & (C.period == per)]] if len(x_)))
        rp = K["report"]
        r1 = rp[rp.variant == nm].set_index("period"); r6 = rp[rp.variant == f"{nm}_cost0.6"].set_index("period")
        a("\nWeekly-tranche book, daily net P&L (protocol table): " + "; ".join(
            f"{per} Sharpe {r1.loc[per, 'sharpe']:+.2f} (t {r1.loc[per, 't']:+.2f}, {r1.loc[per, 'sum_bp']:+.0f} bp)" for per in ("2010-2026", "2016-2026", "2023-2026", "2010-2015"))
          + f"; deflated-Sharpe p (12 candidates) {r1.loc['2010-2026', 'deflated_sharpe_p']:.2f}; at 0.6 pips: "
          + " / ".join(f"{r6.loc[per, 'sharpe']:+.2f}" for per in ("2010-2026", "2016-2026", "2023-2026")) + ".")
        a("\nPer year (decisions by decision date):\n")
        by = K[f"by_year{tag}"].copy()
        yy = r1[r1.index.str.len() == 4][["sharpe"]].rename(columns={"sharpe": "book Sharpe"})
        by["year"] = by["year"].astype(str); by = by.set_index("year").join(yy)
        a(by.round(2).to_markdown())
        inc = K["incremental"]; ii = inc[inc.stream == f"{ARM}{tag}_daily"]
        two = ii[ii.combo == "weak_signals+regime_trend"].set_index("period"); three = ii[ii.combo != "weak_signals+regime_trend"].set_index("period")
        a("\nIncremental test, EW(weak_signals, regime_trend) -> EW(+ this stream), net Sharpe: " + "; ".join(
            f"{per} {two.loc[per, 'sharpe']:.2f} -> {three.loc[per, 'sharpe']:.2f}" for per in ("2010-2026", "2016-2026", "2023-2026"))
          + f". Daily P&L correlation with weak_signals {ii['corr_weak_signals'].iloc[0]:.2f}, with regime_trend {ii['corr_regime_trend'].iloc[0]:.2f}.")
    a("\n**The fixed rule's own probability** (hit rate of `sign21_agree3` weekly decisions whose label was known before the test year; history starts 2006; "
      "this is the `prob` column of the positions file, converted to P(up)):\n")
    a(K["agree3_history"].round(3).to_markdown(index=False))
    a("\n## 7. Leak checks")
    a("Weekly decisions, 2010-26, accuracy / n. `shuffled_labels`: every label permuted (target and the 1-session return the house weights are fitted on). "
      "`features_stale_plusK`: all features K sessions older. `lookahead_control`: features taken h sessions in the future - NOT a result, it shows the "
      "harness would expose a look-ahead.")
    x = L[L.period == "2010-26"].copy()
    x["s"] = x.apply(lambda q: f"{100 * q.accuracy:.1f} / {int(q.n)}" if q.n > 0 and np.isfinite(q.accuracy) else "-", axis=1)
    x["mr"] = x.model.str.replace("B:", "") + " " + x.rule.str.replace("filter", "")
    for tg in x.target.unique():
        a(f"\n*{tg}*\n"); a(x[x.target == tg].pivot(index="check", columns="mr", values="s").fillna("-").to_markdown())
    a("\n**Top weights of the last fit (2026) and full-sample correlation of each input with the label**\n")
    lf = K["leak_features"]
    a(lf[lf.target == lf.target.iloc[0]].round(3).to_markdown(index=False))
    a("\n(The same table for the other target is in `selective_leak_features.csv`; its largest |corr| is "
      f"{lf[lf.feature.str.startswith('MAX')]['corr_with_label_full_sample'].max():.2f}.)")
    a("")
    (path or ROOT / "reports" / f"arm_{ARM}.md").write_text("\n".join(md))


VERDICT_MD = """
# Arm N: selective prediction (`selective`) - how often can a call be right, and is it real?

Code `src/eurusd/arms/selective.py` (`run(cost_pips=1.2)`; `python -m eurusd.arms.selective` runs everything in 2 minutes,
`... selective report` rebuilds this file). Results in `experiments/results/arms/`: `selective_positions.parquet` (decision stream
of the final rule: `pos`, `fwd_bp`, `net_bp`, `prob`, `gross_bp`, `hit`, `hold`), `selective_daily_positions.parquet` (the same rule
as a daily weekly-tranche book - use THIS one for stacking), `selective_p60_positions.parquet` / `selective_p60_daily_positions.parquet`
(the pick among the probability calls), `selective_report.csv` (protocol table of all 12 candidates, `variant`, `final`),
`selective_accuracy_coverage.csv` (every target x model x rule x mode x period), `selective_path_calibration.csv`,
`selective_candidates.csv`, `selective_expectancy.csv`, `selective_reliability.csv`, `selective_leakchecks.csv`,
`selective_leak_features.csv`, `selective_incremental.csv`, log `logs/selective.log`.

Scope as re-set by the owner during the run: POSITION trading. Primary horizons 10 / 21 / 42 / 63 sessions (sign of the forward
return and symmetric 2- and 3-ATR barriers), path events over 10 / 21 sessions; 1- and 5-session direction are diagnostics, the
intraday 13:00 item was dropped. The whole protocol, the 12 candidates and the selection rule are in the module docstring and were
written before the first result. Four things were ADDED after the first run and are marked as such: a conservative effective
sample size, the non-overlapping stream for the fixed selectors, a timing placebo, and the second pick (same rule, probability
calls only). None of them changes which rule is selected.

## Verdict
1. **Direction, as the owner asked for it (a calibrated probability, speak only at P >= 60 %): no.** When the averaged model says
   "at least 60 %" it is right 25 % (n=4), 46 % (n=37), 49 % (n=169) and 51 % (n=226) of the time on the 10 / 21 / 42 / 63-session
   sign, and 40-82 % on the eight barrier targets with nothing systematic (weekly decisions, 2010-26). The logistic model on the
   macro + positioning + calendar blocks is anti-informative out of sample at long horizons (its 10 % most confident calls: 22 %
   right at 42 sessions, 15 % at 63): it fits macro LEVELS and a base rate from 2003-09 that did not persist. Only the house score
   alone is roughly calibrated at 42-63 sessions (P >= 60 % calls right 59-63 %, n 219-407 weekly), and the non-overlapping
   stream of those same calls gives 51-63 %. The pick of the declared rule among the ten probability calls,
   `tb63_3atr_avg_p60`, shows 62 % on weekly decisions and **50 % (n=102, +4 bp) on its non-overlapping stream**; it was 100 % long
   in 2010-15 and earns its record in 2021-22. It is not a 60 % call. Its weekly-tranche book does clear the round-3 bar on paper
   (stand-alone net Sharpe 0.39 / 0.78 / 0.51, three-way combination 0.75 against 0.64 on 2016-26, correlation 0.19 / 0.15 with
   the two live streams), but 2010-15 was 0.13, the deflated-Sharpe p is 0.51, the placebo p 0.05, and its seven sibling
   probability calls sit between 25 % and 82 %. I do not recommend it; at most a paper forward test under its own name.
2. **Direction, what is real: the known macro + positioning drift, and its hit rate rises with the HOLDING PERIOD, not with model
   confidence.** The raw sign of the house score is right 53 / 56 / 58 / 60 % of the time at 10 / 21 / 42 / 63 sessions
   (non-overlapping 53 / 55 / 61 / 64 %). That is exactly what a Sharpe of 0.56 implies: accuracy = Phi(Sharpe x sqrt(h/252)) =
   54 / 56 / 59 / 61 %. Requiring positioning, the 2y-spread trend and the house score to agree (44 % of weeks) lifts it to
   **57 / 59 / 65 / 67 %** (non-overlapping 56 / 59 / 61 / 72 %), +29 / +46 / +108 / +153 bp per decision after costs, timing
   placebo p 0.018 / 0.005 / 0.007 at 21 / 42 / 63 sessions. So a >= 60 % directional accuracy does exist out of sample, at 42-63-session
   holds, 23 weekly decisions a year (4-5 non-overlapping positions a year), positive expectancy.
   * 2016-26: holds (55 / 57 / 63 / 67 %; non-overlapping 53 / 57 / 59 / 71 %).
   * 2023-26: **not confirmed** (57 / 55 / 47 / 53 %; non-overlapping 54 / 60 / 45 / 50 % on 63 / 35 / 20 / 14 decisions). The
     intervals are 25-60 points wide: this period can neither confirm 60 % nor reject it.
   * Statistically: the conservative interval of the agreement rule includes the majority base rate at every horizon
     (e.g. 63 sessions: 67 % [49-81]); only the non-overlapping 63-session stream excludes it (72 % [60-82], n=61). The 387 weekly
     decisions of the final rule are 27 directional episodes in 17 years.
   * More selectivity (the calibrated house score at 25 / 10 / 5 % coverage) raises weekly accuracy at 63 sessions to 67 / 70 / 71 %
     (3-ATR barrier: 71 / 70 / 81 %), but the non-overlapping streams do not confirm a rising curve (54 / 63 / 67 % on 50 / 30 / 18
     decisions; barrier 55 / 66 / 60 %), at 10 % coverage only 2 of 12 targets have a non-overlapping lower bound above the base
     rate, none under the conservative weekly interval, and after 2023 the same cells are 38-50 % on the 42- and 63-session sign
     and 52-73 % on the barriers with 19-66 decisions each. Suggestive, not established.
3. **Final by the declared rule: `sign21_agree3`** (21-session call when positioning, spread trend and house score agree).
   2010-26: 387 decisions, 23 a year, **59.4 % right** (interval 52-66 Newey-West, 49-69 conservative; non-overlapping 59 % [51-66],
   n=156), 59.2 % with positive net P&L, average win +185 bp / loss -156 bp, **+46 bp per decision after costs**, hold 21 sessions.
   2016-26: 57.2 % [44-69], +38 bp. 2023-26: 54.5 % [33-74], +27 bp (non-overlapping 60 % [44-74], n=35). Book Sharpe
   0.52 / 0.51 / 0.43 (t 2.17 / 1.72 / 0.85), deflated-Sharpe p 0.31 for 12 candidates. Its own track record before each test year
   is 56-61 % from 2012 on (table in section 6), i.e. it is a "58 % call", not a 60 % one. **It is not new information**: daily
   P&L correlation 0.63 with `regime_trend` and 0.43 with `weak_signals`; adding it moves the combination from 0.64 to 0.64 on
   2016-26 (0.636 -> 0.641; 2010-26 0.56 -> 0.57, 2023-26 0.36 -> 0.40). It clears the round-3 bar by 0.005 Sharpe, which is
   nothing; I do not recommend a new stream.
4. **Path / level events: yes, 60-90 % is real, calibrated and unchanged after 2023 - and it carries no expectancy.** Predicted
   and realised frequencies agree to 1-3 points in every period and to within 5 points inside each volatility regime (table
   below, section 4).
   Example for a position trade: a level 2 ATR away is not touched within 10 sessions 69 % of the time (predicted 68 %), 3 ATR
   86 % (86 %); within 21 sessions 52 % and 71 %. The gain over the naive unconditional rule is modest (Brier skill 5-10 % for
   no-touch, 22-32 % for the next-session range); the value is the calibration. The only spot expression (fade a touch of the
   level, close at the end of the window) earns +0.2 to +3.9 bp per decision at these levels with t at most 1.2, and is negative
   after costs in the 1-session version (t down to -4.9). These numbers size stops and targets; they are not an edge.
5. **What the 60-80 % target means in this data.** With the edge that exists (Sharpe about 0.5), 60 % needs a holding period of
   about a quarter. 70 % at a 63-session hold would need a Sharpe of 1.05 and 80 % a Sharpe of 1.7; at a 21-session hold 60 %
   already needs 0.9. Nothing here supports that. A system that shows 70-80 % on multi-week direction is either quoting a path
   event (stop not hit), an asymmetric stop/target, or a handful of overlapping decisions from one trend.

**Direction: accuracy % [95 % interval] n; W = weekly decisions (conservative interval), N = non-overlapping stream (Wilson)**

{SUMMARY_DIRECTION}

**Path / level: probability that a level is NOT touched (one-sided), weekly samples**

{SUMMARY_PATH}

## Protocol notes, additions and what looked suspicious
* Walk-forward as in `wf.py`: for test year Y everything (house weights, logistic fit, Platt map, coverage thresholds, range
  and volatility models, the excursion distributions) uses rows whose label is known before Y-01-01. Label-known time is the
  close of session t+h exactly; the store's `label_end_1d` (close + 1 day) lets a Friday row into the training set one session
  early at a year boundary, so I did not use it.
* Costs: 1.2 pips per unit turnover. Per-decision P&L is charged a full round trip (2.4 pips, no netting); the books use
  `pnl_from_positions` (time exit, turnover netted) or 2.4 pips per tranche (stop/target exit). At 21-63-session holds costs are
  about 1 % of the average absolute move; 0.6 pips changes the final's Sharpe by 0.01-0.02.
* ADDED after the first run (not in the docstring): (a) conservative effective n = min(Newey-West n, decisions x 5 / holding
  period). The declared Newey-West n credits 192 independent decisions to 862 weekly 63-session calls where only 69
  non-overlapping periods exist, so it is too generous; every interval printed in this file is the conservative one unless
  labelled. (b) Non-overlapping stream for the fixed selectors. (c) Timing placebo. (d) The pick of the declared rule
  restricted to the ten probability calls, because the declared final turned out to be a fixed rule and the owner asked for a
  probability call. Selection is identical under the Newey-West and the conservative bound; under the bootstrap bound the
  probability pick would be `tb42_3atr_avg_p60` (56 % weekly, 2023-26 46 %), no better.
* Weekly and non-overlapping numbers differ by up to 16 points for the same rule (e.g. calibrated house score, 25 % coverage,
  3-ATR / 63 sessions: 71 % weekly, 55 % non-overlapping). Weekly sampling counts a long trend many times; with about 69
  independent 63-session periods in the whole out-of-sample span any single accuracy has roughly +-12 points of error. Quote
  the non-overlapping number when in doubt.
* Platt calibration with an intercept imports the training base rate: sign of the calibrated house probability is right 54 %
  at 63 sessions where the raw sign is right 60 %. For a drift-free asset the prior P(up) = 0.5 is better than the fitted one.
* The event selector is unreliable: the store's FOMC / ECB / NFP patterns also catch minutes, speeches and ADP (38-52 % of
  sessions are "event" sessions in 2010-23, 29-30 % in 2024-25 where the calendar is thinner). Quiet / volatile / event filters
  show no consistent effect on multi-week direction (section 3).
* Leak checks (section 7). Labels shuffled: 47.6-51.3 % on all weekly 21-session decisions for the three models, 43-54 % for the
  agreement rule, and not a single P >= 60 % call is issued. Look-ahead control (features from h sessions ahead): 86-88 % at
  21 sessions, 75 % on the 63-session barrier, so the harness would expose a leak. Features made 1 / 21 / 63 sessions older:
  the final rule gives 59.3 / 57.5 / 58.9 % against 59.4 %. A leak would vanish at lag 1; this does not, because the
  information is slow (52-week positioning z-score, 20-day spread trend, 27 directional episodes in 17 years). It does mean
  the calls are regime calls and the independent sample is small. Largest full-sample correlation of any input with the label:
  0.15 (cot_z52, 21-session sign), 0.22 (63-session barrier); none is a label in disguise.
* What helped: the holding period, and agreement of the three slow signals. What did not: the logistic model on the macro +
  positioning + calendar blocks, probability calibration, model confidence beyond the agreement rule, the trend-state filter
  (never better than agreement alone), the quiet / volatile / event filters.
* Variant count for deflation: 12 candidate rules. Diagnostics computed but not selected from: 14 targets x 3 models x 8 rules x
  2 evaluation modes, 4 x 7 selector cells x 2 modes, the path tables.
"""


if __name__ == "__main__":
    import pickle
    if len(sys.argv) > 1 and sys.argv[1] == "report":          # rebuild the markdown from the saved tables of the last run
        write_report(pickle.load(open(RES / "logs" / f"{ARM}_tables.pkl", "rb")))
        sys.exit(0)
    cost = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
    pos, rep = run(cost_pips=cost)
    res = run.last
    print("FINAL:", res["final"], "|", res["final_status"], "| P>=60% pick:", res["final_p60"], "| sensitivity:", res["selection_sensitivity"])
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
    print(res["selection"][["candidate", "n_2010-15", "dec_per_year_2010-15", "accuracy_2010-15", "lo_2010-15", "net_bp_2010-15", "eligible", "final", "final_p60"]].round(3).to_string(index=False))
    L = leak_checks(res, cost)
    L.to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
    res["leak_features"].to_csv(RES / f"{ARM}_leak_features.csv", index=False)
    inc = pd.concat([incremental(tag) for tag in res["outs"]], ignore_index=True)
    inc.to_csv(RES / f"{ARM}_incremental.csv", index=False)
    res["incremental"] = inc
    keep = {k: res[k] for k in ("curves_all", "selection", "final", "final_status", "final_p60", "selection_sensitivity", "expectancy", "reliability", "path",
                                "report", "leak", "leak_features", "agree3_history", "by_year", "by_year_p60", "incremental") if k in res}
    keep["targets"] = pd.DataFrame([{"target": k, "kind": t.kind, "h": t.h, "k_atr": t.k, "n": int(np.isfinite(t.long).sum()),
                                     "up_share": float(np.nanmean((t.long > 0)[np.isfinite(t.long)])),
                                     "resolved_share": float(t.resolved[np.isfinite(t.long)].mean()) if t.resolved is not None else np.nan,
                                     "avg_hold": float(np.nanmean(t.hold)), "mean_abs_bp": float(np.nanmean(np.abs(t.long)))} for k, t in res["T"].items()])
    keep["cost_pips"] = cost
    pickle.dump(keep, open(RES / "logs" / f"{ARM}_tables.pkl", "wb"))
    if cost == 1.2 and "write_report" in globals():
        write_report(keep)
