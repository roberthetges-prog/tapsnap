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
          conservative). Trading-rule Sharpe: book of weekly tranches (weight 5/h each, so always-on = 1 unit),
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

    def shifted(self, lag: int) -> "Ctx":
        """Features moved by `lag` sessions: lag > 0 = staler information, lag < 0 = look-ahead (control only)."""
        S = self.S.shift(lag)
        X = pd.DataFrame(self.X).shift(lag).values
        return Ctx(self.D, S, X, self.xcols, self.fwd1, self.ct, self.year, self.cost_bp)


def make_ctx(D: pd.DataFrame, cost_pips: float) -> Ctx:
    S = WS.build_raw_signals(D)
    X, xcols = logit_matrix(D)
    ct = D["close_time"].values.astype("datetime64[ns]").astype(np.int64)
    return Ctx(D, S, X, xcols, D["fwd_1d"].values, ct, D.index.year.values, (cost_pips / D["close"]).values)


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
            w, l = x.loc[x["net_bp"] > 0, "net_bp"], x.loc[x["net_bp"] <= 0, "net_bp"]
            r.update({"n_eff": neff, "accuracy": acc, "lo": lo, "hi": hi, "interval": itype, "share_long": sl,
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
    w = min(1.0, STEP / h)
    pos = np.zeros(n)
    for i, d in zip(dec["i"].values, dec["pos"].values):
        pos[i:i + h] += d * w
    pnl = pnl_from_positions(pd.Series(pos, index=ctx.D.index), ctx.D["fwd_1d"], ctx.D["close"], cost_pips=cost_pips)
    return pnl


def book_barrier(ctx: Ctx, dec: pd.DataFrame, Tb: Target, cost_pips: float) -> pd.DataFrame:
    """Weekly tranches with the symmetric stop/target of barrier target Tb, marked to market at each close."""
    n = len(ctx.D)
    lc = np.log(ctx.D["close"].values)
    w = min(1.0, STEP / Tb.h)
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
                    neff = min(float(Tn), max(1.0, real * (1 - real) / (lrv / Tn))) if 0 < real < 1 and lrv > 0 else float(Tn)
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


def selectors(ctx: Ctx, T: dict, res: dict) -> pd.DataFrame:
    """(B) fixed agreement / regime selectors on the sign targets, weekly decisions."""
    D = ctx.D
    hs = house_score_wf(ctx)
    sg = np.sign(hs)
    cot, spr = np.sign(D["cot_z52"].values), np.sign(D["d_spread2y_20"].values)
    agree = np.isfinite(hs) & (sg != 0) & (cot == sg) & (spr == sg)
    trend = agree & (np.sign(D["dist_sma50_atr"].values) == sg) & (np.sign(D["dist_sma200_atr"].values) == sg)
    rf = range_forecast_1d(D)
    quiet = (rf["F"] < 0.85 * rf["med"]).values; vol = (rf["F"] > rf["q80"]).values
    evw = ((D[["h_to_fomc", "h_to_ecb", "h_to_nfp", "h_to_cpi"]] < 24).any(axis=1) | (D[["h_since_fomc", "h_since_ecb", "h_since_nfp", "h_since_cpi"]] < 24).any(axis=1)).values
    base = np.isfinite(hs) & (sg != 0)
    sel = {"house_sign_all": base, "agree3": agree, "agree3_trend": trend, "house_quiet": base & quiet, "house_volatile": base & vol,
           "house_nonevent": base & ~evw, "house_event": base & evw}
    rows = []
    for h in HORIZONS:
        t = T[f"sign{h}"]
        valid = np.isfinite(t.long)
        for nm, sp in sel.items():
            dec = decision_frame(ctx, t, weekly_idx(sp, valid), sg, None)
            res["decs"][(t.name, f"B:{nm}", "filter")] = dec
            is_cand = any(c[1] == t.name and c[2] == f"B:{nm}" for c in CANDIDATES)
            for r in cell_stats(ctx, t, dec, sp, "weekly", boot=True):
                rows.append({"target": t.name, "kind": "sign", "h": h, "k_atr": 0.0, "model": f"B:{nm}", "rule": "filter", "mode": "weekly", **r})
    res["house_score"] = hs
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


def select_final(C: pd.DataFrame) -> tuple[pd.DataFrame, str | None, str]:
    rows = []
    for name, tg, m, rule in CANDIDATES:
        x = C[(C.target == tg) & (C.model == m) & (C.rule == rule) & (C["mode"] == "weekly")].set_index("period")
        r = {"candidate": name, "target": tg, "model": m, "rule": rule}
        for lab, _, _ in PERIODS:
            for k in ("n", "n_eff", "dec_per_year", "accuracy", "lo", "hi", "boot_lo", "boot_hi", "base_up", "chance_acc", "net_bp", "gross_bp", "avg_hold", "share_long"):
                r[f"{k}_{lab}"] = x.loc[lab].get(k, np.nan) if lab in x.index else np.nan
        r["enough_decisions"] = bool(r["dec_per_year_2010-15"] >= MIN_DEC_PER_YEAR)
        r["positive_expectancy_2010-15"] = bool(r["net_bp_2010-15"] > 0)
        r["eligible"] = r["enough_decisions"] and r["positive_expectancy_2010-15"]
        rows.append(r)
    S = pd.DataFrame(rows)
    el = S[S["eligible"]]
    if len(el):
        final, status = el.sort_values("lo_2010-15", ascending=False)["candidate"].iloc[0], "selected by the declared rule"
    else:
        en = S[S["enough_decisions"] & S["lo_2010-15"].notna()]
        pool = en if len(en) else S[S["lo_2010-15"].notna()]
        final = pool.sort_values("lo_2010-15", ascending=False)["candidate"].iloc[0] if len(pool) else None
        status = "NO candidate eligible - nominal stream only (fails the declared rule)"
    S["final"] = S["candidate"] == final
    return S, final, status


def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Runs every target / model / rule walk-forward, applies the declared selection rule and writes the deliverables.
    Returns (decision positions of the final rule as a Series, report DataFrame)."""
    res = compute(cost_pips, verbose=verbose)
    ctx, T = res["ctx"], res["T"]
    B = selectors(ctx, T, res)
    res["curves_all"] = pd.concat([res["curves"], B], ignore_index=True)
    C = res["curves_all"]
    S, final, status = select_final(C)
    res["selection"], res["final"], res["final_status"] = S, final, status
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
    # report table (protocol format) for every candidate: time-exit book, daily
    reps, streams = [], {}
    for name, tg, m, rule in CANDIDATES:
        dec = res["decs"][(tg, m, rule)]
        t = T[tg]
        pnl = book_barrier(ctx, dec, t, cost_pips) if t.kind == "tb" else book_time_exit(ctx, dec, t.h, cost_pips)
        pnl = pnl[pnl.index.year >= 2010]
        streams[name] = pnl
        tb = report(pnl, periods_per_year=252, name=ARM, n_arms=N_ARMS)
        tb.insert(1, "variant", name); tb["final"] = name == final; tb["kind"] = "candidate"; tb["cost_pips"] = cost_pips
        reps.append(tb)
    if final is not None:
        _, tg, m, rule = next(c for c in CANDIDATES if c[0] == final)
        t = T[tg]; dec = res["decs"][(tg, m, rule)]
        for cp in (0.6,):
            cx = make_ctx(ctx.D, cp)
            pnl = book_barrier(cx, dec, t, cp) if t.kind == "tb" else book_time_exit(cx, dec, t.h, cp)
            tb = report(pnl[pnl.index.year >= 2010], periods_per_year=252, name=ARM, n_arms=N_ARMS)
            tb.insert(1, "variant", f"{final}_cost{cp}"); tb["final"] = False; tb["kind"] = "cost_sensitivity"; tb["cost_pips"] = cp
            reps.append(tb)
    rep = pd.concat(reps, ignore_index=True)
    res["report"], res["streams"] = rep, streams
    pos = pd.Series(dtype=float)
    if final is not None:
        out = dec[["pos", "fwd_bp", "net_bp", "prob", "gross_bp", "hit", "hold"]].copy()
        out = out[out.index.year >= 2010]
        pos = out["pos"]
        res["final_decisions"] = out
        daily = streams[final].copy()
        daily["fwd_bp"] = ctx.D["fwd_1d"].reindex(daily.index)
        res["final_daily"] = daily[["pos", "fwd_bp", "net_bp"]]
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        if final is not None:
            out.to_parquet(RES / f"{ARM}_positions.parquet")
            res["final_daily"].to_parquet(RES / f"{ARM}_daily_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        C.to_csv(RES / f"{ARM}_accuracy_coverage.csv", index=False)
        PC.to_csv(RES / f"{ARM}_path_calibration.csv", index=False)
        S.to_csv(RES / f"{ARM}_candidates.csv", index=False)
        E.to_csv(RES / f"{ARM}_expectancy.csv", index=False)
        res["reliability"].to_csv(RES / f"{ARM}_reliability.csv", index=False)
    run.last = res
    return pos, rep


# ================================================================ incremental value and leak checks
def incremental(res: dict) -> pd.DataFrame:
    from eurusd.arms.meta import combine, load_arm_daily, report_combo
    two, _ = combine(["weak_signals", "regime_trend"], "EW")
    three, _ = combine(["weak_signals", "regime_trend", f"{ARM}_daily"], "EW")
    a = report_combo(two, "weak_signals+regime_trend", 2); b = report_combo(three, "+selective", 3)
    out = pd.concat([a, b], ignore_index=True)
    s = load_arm_daily(f"{ARM}_daily")
    cor = {}
    for o in ("weak_signals", "regime_trend"):
        x = pd.concat([s, load_arm_daily(o)], axis=1).dropna()
        x = x[x.index.year >= 2010]
        cor[o] = float(x.corr().iloc[0, 1])
    out.attrs["corr"] = cor
    return out


def leak_checks(res: dict, cost_pips: float = 1.2, seed: int = 0) -> pd.DataFrame:
    """(1) labels shuffled; (2) features made staler by 1 / 21 / 63 sessions and, as a control that the harness
    WOULD expose a look-ahead, features taken from h sessions in the future; (3) top logit coefficients."""
    ctx, T = res["ctx"], res["T"]
    final = res["final"]
    tg = next(c[1] for c in CANDIDATES if c[0] == final) if final else "sign21"
    todo = sorted({tg, "sign21"})
    rows = []

    def summarise(label, r, nm):
        C = r["curves"]
        for m, rule in (("avg", "cov100"), ("avg", "cov10"), ("avg", "p60"), ("house", "cov100"), ("logit", "cov100"), ("logit", "p60")):
            x = C[(C.target == nm) & (C.model == m) & (C.rule == rule) & (C["mode"] == "weekly")]
            for _, q in x.iterrows():
                rows.append({"check": label, "target": nm, "model": m, "rule": rule, "period": q["period"], "n": q["n"], "accuracy": q.get("accuracy"),
                             "lo": q.get("lo"), "hi": q.get("hi"), "base_up": q.get("base_up"), "chance_acc": q.get("chance_acc"), "net_bp": q.get("net_bp")})

    for nm in todo:
        t = T[nm]
        summarise("baseline", compute(cost_pips, False, [nm], ctx, T, light=True), nm)
        rng = np.random.default_rng(seed)
        for s in range(3):
            Ts = dict(T); Ts[nm] = t.permuted(rng.permutation(len(t.y)))
            summarise(f"shuffled_labels_{s}", compute(cost_pips, False, [nm], ctx, Ts, light=True), nm)
        for lag in (1, 21, 63):
            summarise(f"features_stale_plus{lag}", compute(cost_pips, False, [nm], ctx.shifted(lag), T, light=True), nm)
        summarise(f"lookahead_control_minus{t.h}", compute(cost_pips, False, [nm], ctx.shifted(-t.h), T, light=True), nm)
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
        top = coef.abs().sort_values(ascending=False).head(12).index
        for f in top:
            feats.append({"target": nm, "fit_year": Y, "feature": f, "coef_std": float(coef[f]), "corr_with_label_full_sample": float(cor[f])})
        st, w = lg[Y]["house"]
        for sname, wt in zip(WS.SIGNALS, w):
            feats.append({"target": nm, "fit_year": Y, "feature": f"house:{sname}", "coef_std": float(wt), "corr_with_label_full_sample": np.nan})
        feats.append({"target": nm, "fit_year": Y, "feature": "MAX |corr| of any logit feature with the label", "coef_std": np.nan,
                      "corr_with_label_full_sample": float(cor.abs().max())})
    res["leak"], res["leak_features"] = L, pd.DataFrame(feats)
    return L


if __name__ == "__main__":
    cost = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
    pos, rep = run(cost_pips=cost)
    res = run.last
    print("FINAL:", res["final"], "|", res["final_status"])
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40); pd.set_option("display.max_rows", 400)
    print(res["selection"][["candidate", "n_2010-15", "dec_per_year_2010-15", "accuracy_2010-15", "lo_2010-15", "net_bp_2010-15", "eligible", "final"]].round(3).to_string(index=False))
    L = leak_checks(res, cost)
    L.to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
    res["leak_features"].to_csv(RES / f"{ARM}_leak_features.csv", index=False)
    if res["final"] is not None:
        inc = incremental(res)
        inc.to_csv(RES / f"{ARM}_incremental.csv", index=False)
        print("corr with weak_signals / regime_trend:", inc.attrs["corr"])
    import pickle
    keep = {k: res[k] for k in ("curves_all", "selection", "final", "final_status", "expectancy", "reliability", "path", "report", "leak", "leak_features")}
    pickle.dump(keep, open(RES / "logs" / f"{ARM}_tables.pkl", "wb"))
