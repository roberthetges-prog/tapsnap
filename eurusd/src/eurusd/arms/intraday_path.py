"""Arm K ("intraday_path"), round 4: what the 1-minute path INSIDE the day says about the next day / week.

The feature store summarises a session with OHLC-type numbers only. This arm computes, from the 1-minute bid bars
(data/processed/EURUSD_M1.parquet, 2003+), eight families of intraday-path measures on exactly the feature-store
session grid (session = [22:00 UTC, 22:00 UTC + 24h), index = session start, everything known at close_time) and
tests each as a standalone standardised directional signal for the next session (fwd_1d) and the next five sessions.

FEATURES (build_features(); cached to data/processed/intraday_path_features.parquet, same index as features_daily)
5-minute sampling: last 1-minute close of each 5-minute bin; r_j = log change between consecutive OBSERVED bins of the
same session (the first return of a session is measured from the session's first 1-minute open, so the weekend /
rollover gap is not in any realised measure). A return that spans more than 15 minutes without a tick (dt > 3 bins) is
"invalid": excluded from every realised measure (it would look like a jump). QUALITY RULE (fixed before any result):
all path features of a session are NaN when it has fewer than 200 valid 5-minute returns or more than 120 minutes of
such holes between its first and last bar (thin holidays, the missing hours of Feb-Jul 2023).
  rsj      signed jump variation (RS+ - RS-) / RV   (Barndorff-Nielsen, Kinnebrock & Shephard 2010; Patton & Sheppard 2015)
  rskew    realised skewness sqrt(n) * sum r^3 / RV^1.5   (Amaya, Christoffersen, Jacobs & Vasquez 2015)
  rkurt    realised kurtosis n * sum r^4 / RV^2   (unsigned: cached and described, not traded as a direction)
  jump     signed jump day: BNS/Huang-Tauchen ratio statistic z = (1 - BV/RV) / sqrt((pi^2/4 + pi - 5)/n * max(1, TQ/BV^2))
           > 2.326 (1% level), sign = sign of the largest |5-minute return| of the session; 0 on no-jump days
  ny_share signed share of the day's session moves made in New York: r_NY / (|r_Asia| + |r_Europe| + |r_NY|), with
           Asia = session start -> 07:00 London, Europe = 07:00 London -> 08:00 New York, NY = 08:00 New York -> close
           (DST-aware local clocks)
  eff      signed efficiency ratio (log close - log open) / sum |r_j|  (Kaufman; +1 = a clean one-way up day)
  late     late-day return: log close - log price at 16:00 New York, in units of the session's realised vol sqrt(RV)
  hl_time  time of the session high minus time of the session low, in fractions of the 24h session (1-minute closes,
           so ghost-tick wicks cannot matter); +1 = low at the open and high at the close
  ofi      tick-rule order-flow proxy on 1-minute bars: sum w_i d_i / sum w_i, d_i = tick-rule sign of the 1-minute
           close change (zero change -> previous sign), w_i = min(high_i - low_i, 30 pips) as the activity weight.
           (Weighting by |close change| instead would be algebraically the 1-minute efficiency ratio.)
  <x>_5d   mean of the last 5 sessions (at least 3 available) of each of the above.

SIGNALS AND PRIORS (written down BEFORE any forward return was looked at)
  rsj      prior NEGATIVE: positive signed jump variation is followed by lower returns over the next week
           (Bollerslev, Li & Zhao 2020 cross-section of stocks; Patton & Sheppard 2015).
  rskew    prior NEGATIVE: high realised skewness -> lower next-week return (Amaya et al. 2015).
  ofi      prior POSITIVE: order flow carries information and its price impact persists / predicts the next day
           (Evans & Lyons 2002, 2005; Rime, Sarno & Sojli 2010).
  jump, ny_share, eff, late, hl_time: NO usable published prior for next-day EUR/USD direction (jump days:
           under-reaction/continuation in stocks (Jiang & Zhu 2017) but FX news is absorbed within minutes (Andersen
           et al. 2003) and the signed-jump prior above says reversal). For these the sign is taken from the TRAINING
           WINDOW every year: orientation = sign of the training-window correlation of the standardised signal with the
           label of the variant's horizon ("auto").

MODEL (house method of arms/weak_signals.py)
  standardise: divide by the training-window sd (no demeaning: all eight are signed around 0), clip +-2, halve;
  `jump` at the 1-day horizon is already in {-1, 0, +1}. A signal needs >= 250 available training rows.
  position target s_t = orientation * sign(z_t) when |z_t| > training median of |z| over available rows, else 0,
  times the vol scale min(1, median_train(rv_21d_bp) / rv_21d_bp).
  horizon d1: daily feature, label fwd_1d, position = s_t (one session).
  horizon w5: 5-day averaged feature, label fwd_5d (train rows with label_end_5d before the test year), position =
           mean of the last five targets (s_t + ... + s_{t-4}) / 5, i.e. every session opens a 1/5 tranche held for
           five sessions; P&L is booked daily on fwd_1d with costs on the change of the summed position.
  combination: weights proportional to max(t_i, 0), t_i = t-stat of the training-window correlation of the oriented
           standardised signal with the horizon's label (for "auto" signals the orientation is fitted first, so their
           weight is |t_i|: stated openly, it favours them); score = sum w_i z_i, same sign/median mapping.

VARIANTS. 11 CANDIDATES for the final (<= 12): the eight single signals at the w5 horizon (the literature horizon is
a week and a daily-flipping position pays ~1 pip a day), combo_d1 (t-stat combination of the eight daily signals),
combo_w5 (of the eight 5-day signals) and combo_both (average of the positions of combo_d1 and combo_w5).
8 DIAGNOSTIC backtests, reported in the same table but not eligible: the eight single signals at the d1 horizon.
Total number of backtests whose result was looked at: 19 (the deflated-Sharpe p uses 19).
SELECTION RULE (declared before any result): the final is the candidate with the highest 2010-2015 walk-forward NET
Sharpe at 1.2 pips. Its full 2010-2026 record is reported; 2016+ and 2023-2026 are never used for any choice.
CONTROLS declared in advance (not candidates): (a) the final's pipeline with every signal replaced by its residual
from a training-window OLS on the existing price features [ret_1d / rv_1d_bp, body_rel, close_in_range - 0.5] (their
5-day means for w5), (b) the final's pipeline run on those three existing features alone ("ret_1d in disguise").

ADDED AFTER THE RESULTS (everything above was written before the first run and is unchanged): the final by the rule is
w5_ofi and it fails (reports/arm_intraday_path.md). Post-hoc functions, none of them a candidate: late_artefact_check()
(one extra backtest: d1_late executed 60 minutes after the close; total backtests looked at = 19 + 2 controls + 1 = 22),
control_followup() (lags / null / combination of control (a), no new variant), residual_corr(), tranche_hit_rate().
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.special import gamma

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.wf import walk_forward, pnl_from_positions, report  # noqa: E402

FEATURES = ROOT / "data/processed/features_daily.parquet"
M1 = ROOT / "data/processed/EURUSD_M1.parquet"
CACHE = ROOT / "data/processed/intraday_path_features.parquet"
RES = ROOT / "experiments/results/arms"
ARM = "intraday_path"
N_CANDIDATES = 11
N_BACKTESTS = 19
MIN_TRAIN_ROWS = 250
Q_SIGN = 0.50
MIN_VALID_5M = 200          # quality rule
MAX_HOLE_MIN = 120
JUMP_Z = 2.326              # 1% one-sided
W_CAP = 30e-4               # cap of the 1-minute range used as order-flow weight (30 pips)
PERIODS = (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026))

# name: (prior sign: -1 / +1 / 0 = from the training window, description)
SIGNALS = {
    "rsj":      (-1, "signed jump variation (RS+ - RS-)/RV; prior: reversal (Bollerslev-Li-Zhao 2020, Patton-Sheppard 2015)"),
    "rskew":    (-1, "realised skewness of 5-minute returns; prior: negative (Amaya et al. 2015)"),
    "jump":     (0,  "signed jump day (BNS ratio test at 1%, sign of the largest 5-minute return); sign from training"),
    "ny_share": (0,  "signed share of the day's session moves made in New York; sign from training"),
    "eff":      (0,  "signed efficiency ratio (close - open) / sum |5-minute moves|; sign from training"),
    "late":     (0,  "return from 16:00 New York to the close in units of the session's realised vol; sign from training"),
    "hl_time":  (0,  "time of the high minus time of the low (fraction of the session); sign from training"),
    "ofi":      (+1, "tick-rule order-flow proxy on 1-minute bars, range-weighted; prior: positive (Evans-Lyons)"),
}
SIG = list(SIGNALS)
CONTROL_COLS = ["c_ret", "c_body", "c_cir"]      # existing price features used in the "new information" controls


# ================================================================================================ features from M1
def _local_utc_ns(dates: pd.DatetimeIndex, hour: int, tz: str) -> np.ndarray:
    """UTC ns of `hour`:00 local time in `tz` on each naive calendar date."""
    return (dates + pd.Timedelta(hours=hour)).tz_localize(tz).tz_convert("UTC").as_unit("ns").asi8


def _group_first(code_sorted: np.ndarray) -> np.ndarray:
    return np.r_[0, np.flatnonzero(np.diff(code_sorted)) + 1]


def build_features(save: bool = True, m1: pd.DataFrame | None = None, end: pd.Timestamp | None = None,
                   index: pd.DatetimeIndex | None = None) -> pd.DataFrame:
    """Daily intraday-path features on the NY-close session grid of features_daily (index = session start).
    Every number of row T uses 1-minute bars stamped in [T, T + 24h) only (the `_5d` columns: the last five rows).
    `end`: drop every bar stamped >= end first (truncation test)."""
    if m1 is None:
        m1 = pd.read_parquet(M1, columns=["open", "high", "low", "close"]).loc["2002-12-31":]
    if end is not None:
        m1 = m1[m1.index < end]
    ts = m1.index.as_unit("ns").asi8
    o, h, l, c = (m1[k].values for k in ("open", "high", "low", "close"))
    DAY, H22, MIN5 = 86_400_000_000_000, 22 * 3_600_000_000_000, 300_000_000_000
    sday = (ts - H22) // DAY
    uniq, code = np.unique(sday, return_inverse=True)
    ns = len(uniq)
    first = _group_first(code)
    last = np.r_[first[1:] - 1, len(code) - 1]
    start_ns = uniq * DAY + H22
    lc = np.log(c)
    lopen, lclose = np.log(o[first]), lc[last]

    # ---- 5-minute returns (last close of each observed bin)
    b = ts // MIN5
    bi = np.r_[np.flatnonzero(np.diff(b)), len(b) - 1]
    bl, bc, bb = lc[bi], code[bi], b[bi]
    same = np.r_[False, bc[1:] == bc[:-1]]
    r = np.where(same, bl - np.roll(bl, 1), bl - lopen[bc])
    dt = np.where(same, bb - np.roll(bb, 1), 1)
    valid = dt <= 3
    n5 = np.bincount(bc, minlength=ns)
    nv = np.bincount(bc, weights=valid, minlength=ns)
    hole = np.bincount(bc, weights=np.where(same & ~valid, (dt - 1) * 5.0, 0.0), minlength=ns)
    rv_ = r * valid
    rv = np.bincount(bc, weights=rv_ ** 2, minlength=ns)
    rsp = np.bincount(bc, weights=np.where(rv_ > 0, rv_ ** 2, 0.0), minlength=ns)
    rsn = np.bincount(bc, weights=np.where(rv_ < 0, rv_ ** 2, 0.0), minlength=ns)
    m3 = np.bincount(bc, weights=rv_ ** 3, minlength=ns)
    m4 = np.bincount(bc, weights=rv_ ** 4, minlength=ns)
    path = np.bincount(bc, weights=np.abs(r), minlength=ns)
    with np.errstate(divide="ignore", invalid="ignore"):
        rsj = (rsp - rsn) / rv
        rskew = np.sqrt(nv) * m3 / rv ** 1.5
        rkurt = nv * m4 / rv ** 2
        # bipower variation and tripower quarticity on adjacent valid returns of the same session
        a = np.abs(r)
        p2 = same & valid & np.roll(valid, 1)
        s2 = np.bincount(bc, weights=np.where(p2, a * np.roll(a, 1), 0.0), minlength=ns)
        n2 = np.bincount(bc, weights=p2, minlength=ns)
        bv = (math.pi / 2) * s2 * nv / n2
        same2 = np.r_[False, False, bc[2:] == bc[:-2]]
        p3 = p2 & same2 & np.roll(valid, 2)
        a43 = a ** (4 / 3)
        s3 = np.bincount(bc, weights=np.where(p3, a43 * np.roll(a43, 1) * np.roll(a43, 2), 0.0), minlength=ns)
        n3 = np.bincount(bc, weights=p3, minlength=ns)
        mu43 = 2 ** (2 / 3) * gamma(7 / 6) / gamma(0.5)
        tq = nv * mu43 ** -3 * s3 * nv / n3
        jz = (1 - bv / rv) / np.sqrt((math.pi ** 2 / 4 + math.pi - 5) / nv * np.maximum(1.0, tq / bv ** 2))
    # sign and size of the largest valid |5-minute return| of each session
    av = np.where(valid, np.abs(r), -1.0)
    order = np.lexsort((av, bc))
    gl = np.r_[np.flatnonzero(np.diff(bc[order])), len(order) - 1]
    big = np.full(ns, np.nan)
    big[bc[order][gl]] = r[order][gl]
    jflag = (jz > JUMP_Z)
    jump = np.where(jflag, np.sign(big), 0.0)

    # ---- session blocks (DST-aware local clocks) and the late-day return
    dates = pd.DatetimeIndex(pd.to_datetime(start_ns + 2 * 3_600_000_000_000)).normalize()   # calendar date of the close
    def price_before(tau: np.ndarray) -> np.ndarray:
        pos = np.searchsorted(ts, tau) - 1                 # last bar that STARTED before tau (it ends at or before tau)
        pos = np.minimum(pos, last)
        return np.where(pos < first, lopen, lc[np.maximum(pos, 0)])
    p_asia = price_before(_local_utc_ns(dates, 7, "Europe/London"))
    p_ny = price_before(_local_utc_ns(dates, 8, "America/New_York"))
    p_late = price_before(_local_utc_ns(dates, 16, "America/New_York"))
    r_asia, r_eur, r_ny = p_asia - lopen, p_ny - p_asia, lclose - p_ny
    r_day = lclose - lopen
    with np.errstate(divide="ignore", invalid="ignore"):
        ny_share = r_ny / (np.abs(r_asia) + np.abs(r_eur) + np.abs(r_ny))
        eff = r_day / path
        late = (lclose - p_late) / np.sqrt(rv)

    # ---- time of the high and of the low (1-minute closes, first occurrence)
    oh = np.lexsort((-c, code)); ol = np.lexsort((c, code))
    t_high = (ts[oh][_group_first(code[oh])] - start_ns) / DAY
    t_low = (ts[ol][_group_first(code[ol])] - start_ns) / DAY

    # ---- tick-rule order-flow proxy on 1-minute bars
    d = np.sign(np.r_[0.0, np.diff(c)])
    d[first] = np.sign(c[first] - o[first])
    # carry the last non-zero sign forward inside the session (a session start resets the carry)
    lastpos = np.arange(len(d))
    reset = np.zeros(len(d), dtype=np.int64)
    reset[first] = first
    seg_start = np.maximum.accumulate(reset)
    known = np.maximum.accumulate(np.where(d != 0, lastpos, -1))
    dd = np.where(known >= seg_start, d[np.maximum(known, 0)], 0.0)
    w = np.minimum(h - l, W_CAP)
    with np.errstate(divide="ignore", invalid="ignore"):
        ofi = np.bincount(code, weights=w * dd, minlength=ns) / np.bincount(code, weights=w, minlength=ns)
        nup = np.bincount(code, weights=(d > 0), minlength=ns); ndn = np.bincount(code, weights=(d < 0), minlength=ns)
        upshare = (nup - ndn) / (nup + ndn)

    X = pd.DataFrame({
        "n_m1": np.bincount(code, minlength=ns), "n5": n5, "n_valid5": nv, "hole_min": hole,
        "rv5_bp": np.sqrt(rv) * 1e4, "rsj": rsj, "rskew": rskew, "rkurt": rkurt, "bv_ratio": bv / np.where(rv > 0, rv, np.nan),
        "jump_z": jz, "jump_flag": jflag.astype(float), "jump": jump, "big_ret_bp": big * 1e4,
        "r_asia_bp": r_asia * 1e4, "r_eur_bp": r_eur * 1e4, "r_ny_bp": r_ny * 1e4, "r_day_bp": r_day * 1e4,
        "ny_share": ny_share, "eff": eff, "late": late, "late_bp": (lclose - p_late) * 1e4,
        "t_high": t_high, "t_low": t_low, "hl_time": t_high - t_low, "ofi": ofi, "upshare": upshare,
        "m1_open": o[first], "m1_close": c[last],
    }, index=pd.DatetimeIndex(pd.to_datetime(start_ns, utc=True), name="time"))
    X = X.replace([np.inf, -np.inf], np.nan)
    X["ok"] = ((X["n_valid5"] >= MIN_VALID_5M) & (X["hole_min"] <= MAX_HOLE_MIN)).astype(float)
    feat = ["rsj", "rskew", "rkurt", "bv_ratio", "jump_z", "jump_flag", "jump", "ny_share", "eff", "late", "hl_time", "ofi", "upshare"]
    X.loc[X["ok"] == 0, feat] = np.nan
    if index is None and FEATURES.exists():
        index = pd.read_parquet(FEATURES, columns=["close"]).index
        if end is not None:
            index = index[index < end]
    if index is not None:
        X.index = X.index.as_unit(index.unit)
        X = X.reindex(index)
    for k in SIG + ["rkurt"]:
        X[f"{k}_5d"] = X[k].rolling(5, min_periods=3).mean()
    if save and end is None:
        X.to_parquet(CACHE)
    return X


def load_features(rebuild: bool = False) -> pd.DataFrame:
    if CACHE.exists() and not rebuild:
        return pd.read_parquet(CACHE)
    return build_features(save=True)


# ================================================================================================ frame
def load_frame(rebuild: bool = False) -> pd.DataFrame:
    df = pd.read_parquet(FEATURES)
    P = load_features(rebuild).reindex(df.index)
    D = pd.DataFrame(index=df.index)
    for k in SIG:
        D[f"d1_{k}"] = P[k]
        D[f"w5_{k}"] = P[f"{k}_5d"]
    # existing price features for the "new information" controls (same session, known at the close)
    D["d1_c_ret"] = df["ret_1d"] / df["rv_1d_bp"].replace(0, np.nan)
    D["d1_c_body"] = df["body_rel"]
    D["d1_c_cir"] = df["close_in_range"] - 0.5
    for k in CONTROL_COLS:
        D[f"w5_{k}"] = D[f"d1_{k}"].rolling(5, min_periods=3).mean()
    return pd.concat([D, df[["fwd_1d", "fwd_5d", "rv_21d_bp", "close", "label_end_1d", "label_end_5d"]]], axis=1)


# ================================================================================================ model (house method)
def _kind(col: str) -> str:
    return "bin" if col == "d1_jump" else "cont"


def _prior(col: str) -> int:
    k = col.split("_", 1)[1]
    return SIGNALS[k][0] if k in SIGNALS else 0


def _tstat(x: np.ndarray, y: np.ndarray) -> float:
    ok = ~np.isnan(x) & ~np.isnan(y)
    if ok.sum() < MIN_TRAIN_ROWS or np.std(x[ok]) == 0:
        return 0.0
    rr = np.corrcoef(x[ok], y[ok])[0, 1]
    return float(rr * np.sqrt(ok.sum() - 2) / np.sqrt(max(1e-12, 1 - rr * rr)))


def make_fit_predict(cols: list[str], label: str, log: dict | None = None, residualise: bool = False):
    hz = cols[0][:2]
    ctrl = [f"{hz}_{k}" for k in CONTROL_COLS]

    def _resid(df: pd.DataFrame, beta: dict | None) -> tuple[pd.DataFrame, dict]:
        if not residualise:
            return df[cols], {}
        out, b = pd.DataFrame(index=df.index), {}
        C = df[ctrl].values
        for k in cols:
            x = df[k].values
            if beta is None:
                ok = ~np.isnan(x) & ~np.isnan(C).any(axis=1)
                b[k] = np.linalg.lstsq(C[ok], x[ok], rcond=None)[0] if ok.sum() >= MIN_TRAIN_ROWS else np.zeros(C.shape[1])
            else:
                b[k] = beta[k]
            out[k] = x - np.nan_to_num(C) @ b[k]
        return out, b

    def _scale(S: pd.DataFrame, st: dict) -> pd.DataFrame:
        Z = pd.DataFrame(index=S.index)
        for k in cols:
            Z[k] = np.nan if st[k] is None else (S[k] if _kind(k) == "bin" and not residualise else (S[k] / st[k]).clip(-2, 2) / 2)
        return Z

    def fit(train: pd.DataFrame):
        S, beta = _resid(train, None)
        st = {}
        for k in cols:
            x = S[k].dropna()
            st[k] = None if len(x) < MIN_TRAIN_ROWS else (float(x.std()) or 1.0)
        Z = _scale(S, st)
        y = train[label].values
        t = np.array([_tstat(Z[k].values, y) for k in cols])
        ori = np.array([(_prior(k) if _prior(k) != 0 else np.sign(t[j])) if st[k] is not None else 0.0 for j, k in enumerate(cols)])
        tt = t * ori                                             # t-stat of the ORIENTED signal
        if len(cols) == 1:
            w = np.abs(ori)
        else:
            w = np.clip(tt, 0, None)
            if w.sum() <= 0:
                w = np.abs(ori)                                  # house fallback: equal weights
            w = w / w.sum() if w.sum() > 0 else w
        score = pd.Series((Z.fillna(0.0).values * ori) @ w, index=train.index)
        avail = Z.loc[:, w > 0].notna().any(axis=1) if (w > 0).any() else pd.Series(False, index=train.index)
        a = score[avail].abs()
        thr = float(np.quantile(a, Q_SIGN)) if len(a) >= MIN_TRAIN_ROWS else np.inf
        if log is not None:
            Y = train.index.max().year + 1
            log[Y] = {"w": dict(zip(cols, w)), "ori": dict(zip(cols, ori)), "t_oriented": dict(zip(cols, tt)), "thr": thr}
        return {"st": st, "beta": beta, "ori": ori, "w": w, "thr": thr, "target_vol": float(train["rv_21d_bp"].median())}

    def predict(m, test: pd.DataFrame) -> pd.Series:
        S, _ = _resid(test, m["beta"])
        Z = _scale(S, m["st"])
        score = pd.Series((Z.fillna(0.0).values * m["ori"]) @ m["w"], index=test.index)
        pos = np.sign(score).where(score.abs() > m["thr"], 0.0)
        vs = (m["target_vol"] / test["rv_21d_bp"].replace(0, np.nan)).clip(upper=1.0).fillna(0.0)
        return pos * vs
    return fit, predict


def targets(D: pd.DataFrame, cols: list[str], log: dict | None = None, residualise: bool = False) -> pd.Series:
    """Walk-forward daily position targets s_t (before the 5-day tranche averaging)."""
    hz = cols[0][:2]
    label, lend = ("fwd_1d", "label_end_1d") if hz == "d1" else ("fwd_5d", "label_end_5d")
    fit, predict = make_fit_predict(cols, label, log, residualise)
    return walk_forward(D, fit, predict, label_end=D[lend], verbose=False).fillna(0.0)


def positions(D: pd.DataFrame, cols: list[str], log: dict | None = None, residualise: bool = False) -> pd.Series:
    s = targets(D, cols, log, residualise)
    return s if cols[0][:2] == "d1" else s.rolling(5, min_periods=1).sum() / 5      # 1/5 tranches held five sessions


def hit_rates(pnl: pd.DataFrame, fwd: pd.Series) -> dict:
    out = {}
    for lab, a, b in PERIODS:
        m = (pnl.index.year >= a) & (pnl.index.year <= b) & (pnl["pos"] != 0) & fwd.reindex(pnl.index).notna()
        x = pnl[m]
        f = fwd.reindex(x.index)
        nz = f != 0
        out[lab] = {"n_active": int(len(x)), "hit_net": float((x["net_bp"] > 0).mean()) if len(x) else np.nan,
                    "hit_sign": float((np.sign(x["pos"][nz]) == np.sign(f[nz])).mean()) if nz.sum() else np.nan}
    return out


def evaluate(D: pd.DataFrame, pos: pd.Series, name: str, kind: str, cost_pips: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    pnl = pnl_from_positions(pos, D["fwd_1d"], D["close"], cost_pips=cost_pips)
    pnl = pnl[pnl.index.year >= 2010]
    tbl = report(pnl, periods_per_year=252, name=ARM, n_arms=N_BACKTESTS)
    tbl.insert(1, "variant", name)
    tbl["kind"] = kind
    tbl["cost_pips"] = cost_pips
    hr = hit_rates(pnl, D["fwd_1d"])
    for c in ("n_active", "hit_net", "hit_sign"):
        tbl[c] = tbl["period"].map(lambda p: hr.get(p, {}).get(c, np.nan))
    tbl["turnover_per_year"] = np.nan
    tbl.loc[tbl["period"] == "2010-2026", "turnover_per_year"] = float(pnl["turnover"].sum() / max(1, pnl.index.year.nunique()))
    return pnl, tbl


def _row(tbl: pd.DataFrame, period: str) -> pd.Series:
    return tbl.set_index("period").loc[period]


def variant_cols() -> dict[str, tuple[str, list[str] | None]]:
    v = {f"w5_{k}": ("candidate", [f"w5_{k}"]) for k in SIG}
    v["combo_d1"] = ("candidate", [f"d1_{k}" for k in SIG])
    v["combo_w5"] = ("candidate", [f"w5_{k}" for k in SIG])
    v["combo_both"] = ("candidate", None)
    v.update({f"d1_{k}": ("diagnostic", [f"d1_{k}"]) for k in SIG})
    return v


def all_positions(D: pd.DataFrame, logs: dict | None = None, only: list[str] | None = None) -> dict[str, pd.Series]:
    out = {}
    V = variant_cols()
    for name, (_, cols) in V.items():
        if cols is None or (only is not None and name not in only):
            continue
        lg = {} if logs is not None else None
        out[name] = positions(D, cols, lg)
        if logs is not None:
            logs[name] = lg
    if only is None or "combo_both" in only:
        for nm in ("combo_d1", "combo_w5"):
            if nm not in out:
                out[nm] = positions(D, V[nm][1])
        out["combo_both"] = 0.5 * (out["combo_d1"] + out["combo_w5"])
    return out


# ================================================================================================ entry point
def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True, rebuild: bool = False):
    """19 backtests (11 candidates + 8 diagnostics) walk-forward, selection rule, cost sensitivities; writes the
    deliverables. Returns (final OOS positions, report DataFrame)."""
    D = load_frame(rebuild)
    V = variant_cols()
    assert sum(k == "candidate" for k, _ in V.values()) == N_CANDIDATES and len(V) == N_BACKTESTS
    logs: dict = {}
    P = all_positions(D, logs)
    rows, store = [], {}
    for name, (kind, _) in V.items():
        pnl, tbl = evaluate(D, P[name], name, kind, cost_pips)
        store[name] = (pnl, tbl)
        rows.append(tbl)
        for cst in (0.6, 0.0):
            rows.append(evaluate(D, P[name], name, "cost_sensitivity", cst)[1])
        if verbose:
            r = tbl.set_index("period")
            g = rows[-1].set_index("period")
            print(f"{name:12s} [{kind[:4]}] 2010-15 SR {r.loc['2010-2015','sharpe']:+.2f} | 2010-26 SR {r.loc['2010-2026','sharpe']:+.2f} t {r.loc['2010-2026','t']:+.2f} "
                  f"hit {r.loc['2010-2026','hit_sign']:.3f} | 2016-26 SR {r.loc['2016-2026','sharpe']:+.2f} t {r.loc['2016-2026','t']:+.2f} | "
                  f"2023-26 SR {r.loc['2023-2026','sharpe']:+.2f} t {r.loc['2023-2026','t']:+.2f} | gross SR 10-26 {g.loc['2010-2026','sharpe']:+.2f} "
                  f"| turn/yr {r.loc['2010-2026','turnover_per_year']:.0f}", flush=True)
    sel = {n: float(_row(store[n][1], "2010-2015")["sharpe"]) for n, (k, _) in V.items() if k == "candidate"}
    final = max(sel, key=sel.get)
    if verbose:
        print(f"FINAL by rule (best 2010-2015 net Sharpe among the {N_CANDIDATES} candidates): {final} ({sel[final]:+.2f})", flush=True)
    for t in rows:
        t["final"] = (t["variant"].iloc[0] == final) & (t["kind"].iloc[0] == "candidate")
    rep = pd.concat(rows, ignore_index=True)
    pnl = store[final][0]
    out = pd.DataFrame({"pos": P[final], "fwd_bp": D["fwd_1d"], "net_bp": pnl["net_bp"].reindex(D.index)})
    out = out[out.index.year >= 2010]
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        out.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        allpos = pd.DataFrame(P)
        allpos[allpos.index.year >= 2010].to_parquet(RES / f"{ARM}_all_positions.parquet")
        js = {v: {str(y): {kk: ({a: float(b) for a, b in vv.items()} if isinstance(vv, dict) else float(vv)) for kk, vv in d.items()}
                  for y, d in lg.items()} for v, lg in logs.items()}
        (RES / f"{ARM}_fitlog.json").write_text(json.dumps(js, indent=1))
    return out["pos"], rep


# ================================================================================================ leak checks
def _quick(D: pd.DataFrame, name: str, cost_pips: float, label: str) -> pd.DataFrame:
    P = all_positions(D, only=[name])
    return evaluate(D, P[name], label, "leak_check", cost_pips)[1].assign(check=label)


def leak_checks(final: str, cost_pips: float = 1.2, seed: int = 0, n_null: int = 200, n_shuffle: int = 40) -> pd.DataFrame:
    """(1) shuffled labels (5 permutations of fwd_1d; fwd_5d rebuilt from the shuffled series); (2) features shifted
    forward by 1, 5, 21 sessions and look-ahead controls (shift -1, -5: the harness must light up, the path features of
    the NEXT session contain its return); (2b) circular-shift null of the final; (3) full-sample correlation of every
    standardised signal with both labels; (4) truncation test of the feature builder."""
    D = load_frame()
    fcols = [c for c in D.columns if c[:3] in ("d1_", "w5_")]
    out = []
    rng = np.random.default_rng(seed)
    shuf = []
    for k in range(n_shuffle):
        Ds = D.copy()
        f1 = pd.Series(rng.permutation(D["fwd_1d"].values), index=D.index)
        Ds["fwd_1d"] = f1
        Ds["fwd_5d"] = f1[::-1].rolling(5, min_periods=5).sum()[::-1]
        if k < 5:
            out.append(_quick(Ds, final, cost_pips, f"shuffled_labels_{k}"))
        pk = all_positions(Ds, only=[final])[final]
        shuf.append([evaluate(Ds, pk, "s", "leak_check", cst)[1].set_index("period").loc["2010-2026", "sharpe"] for cst in (cost_pips, 0.0)])
    shuf = np.array(shuf)
    out.append(pd.DataFrame([{"period": "2010-2026", "n_perm": n_shuffle, "net_mean": shuf[:, 0].mean(), "net_sd": shuf[:, 0].std(),
                              "gross_mean": shuf[:, 1].mean(), "gross_sd": shuf[:, 1].std(), "check": "shuffled_labels_summary"}]))
    for lag in (1, 5, 21, -1, -5):
        Dl = D.copy()
        Dl[fcols] = D[fcols].shift(lag)
        out.append(_quick(Dl, final, cost_pips, f"features_shift_plus{lag}" if lag > 0 else f"features_shift_minus{-lag}_lookahead_control"))
    idx = np.where(D.index.year >= 2010)[0]
    act = _quick(D, final, cost_pips, "actual").set_index("period").loc[[p for p, _, _ in PERIODS], "sharpe"].values
    null = []
    for k in range(n_null):
        off = int(rng.integers(252, len(idx) - 252))
        Dl = D.copy()
        v = D[fcols].values.copy()
        v[idx] = np.roll(v[idx], off, axis=0)
        Dl[fcols] = v
        null.append(_quick(Dl, final, cost_pips, "null").set_index("period").loc[[p for p, _, _ in PERIODS], "sharpe"].values)
    null = np.array(null)
    out.append(pd.DataFrame({"period": [p for p, _, _ in PERIODS], "sharpe": act, "null_mean": null.mean(0), "null_sd": null.std(0),
                             "null_q95": np.quantile(null, 0.95, axis=0), "p_null_ge_actual": (null >= act).mean(0), "check": "circular_shift_null"}))
    rows = []
    for c in [x for x in fcols if x.split("_", 1)[1] in SIGNALS]:
        lab = "fwd_1d" if c.startswith("d1_") else "fwd_5d"
        rows.append({"period": c, "label": lab, "corr_full_sample": D[c].corr(D[lab]), "corr_same_session_ret": D[c].corr(D["fwd_1d"].shift(1)),
                     "n": int(D[c].notna().sum()), "check": "signal_label_corr"})
    out.append(pd.DataFrame(rows))
    out.append(truncation_test())
    return pd.concat(out, ignore_index=True)


def truncation_test(n_dates: int = 12, seed: int = 0) -> pd.DataFrame:
    """Rebuild the features from 1-minute bars stamped before close_time(T) only; the row T must be identical."""
    full = load_features()
    m1 = pd.read_parquet(M1, columns=["open", "high", "low", "close"]).loc["2002-12-31":]
    rng = np.random.default_rng(seed)
    cand = np.where(full.index.year >= 2005)[0]
    cols = [c for c in full.columns if c not in ("ok",)]
    worst, mism = 0.0, 0
    for i in rng.choice(cand, n_dates, replace=False):
        T = full.index[i]
        part = build_features(save=False, m1=m1, end=T + pd.Timedelta(days=1), index=full.index[: i + 1])
        a, b = full.iloc[i][cols].values.astype(float), part.iloc[-1][cols].values.astype(float)
        mism += int((np.isnan(a) != np.isnan(b)).sum())
        dlt = np.abs(a - b)
        worst = max(worst, float(np.nanmax(dlt)) if np.isfinite(dlt).any() else 0.0)
    return pd.DataFrame([{"period": f"{n_dates} random sessions", "max_abs_diff": worst, "nan_mismatch": mism, "check": "feature_truncation"}])


# ================================================================================================ controls / new information
def controls(final: str, cost_pips: float = 1.2) -> pd.DataFrame:
    """(a) the final's signals residualised on the existing price features (training-window OLS); (b) the final's
    pipeline on those existing features alone. For combo_both both legs are treated the same way."""
    D = load_frame()
    V = variant_cols()
    legs = ["combo_d1", "combo_w5"] if final == "combo_both" else [final]
    rows = []
    pa = sum(positions(D, V[n][1], residualise=True) for n in legs) / len(legs)
    pnl_a, ta = evaluate(D, pa, f"{final}_residualised_on_ret1d_body_cir", "control", cost_pips)
    rows.append(ta)
    rows.append(evaluate(D, pa, f"{final}_residualised_on_ret1d_body_cir", "control_cost_sensitivity", 0.6)[1])
    o = pd.DataFrame({"pos": pa, "fwd_bp": D["fwd_1d"], "net_bp": pnl_a["net_bp"].reindex(D.index)})
    o[o.index.year >= 2010].to_parquet(RES / f"{ARM}_control_resid_stream.parquet")      # NOT an arm file (name avoids *_positions.parquet)
    pb = sum(positions(D, [f"{V[n][1][0][:2]}_{k}" for k in CONTROL_COLS]) for n in legs) / len(legs)
    rows.append(evaluate(D, pb, f"{final}_pipeline_on_ret1d_body_cir_only", "control", cost_pips)[1])
    return pd.concat(rows, ignore_index=True)


def residual_corr() -> pd.DataFrame:
    """Descriptive (features only, no label): correlation matrix of the eight daily path signals AFTER removing the
    existing price features [ret_1d/rv, body_rel, close_in_range] by full-sample OLS."""
    D = load_frame()
    C = np.column_stack([D[f"d1_{k}"].values for k in CONTROL_COLS] + [np.ones(len(D))])
    R = pd.DataFrame(index=D.index)
    for k in SIG:
        x = D[f"d1_{k}"].values
        ok = ~np.isnan(x) & ~np.isnan(C).any(axis=1)
        b = np.linalg.lstsq(C[ok], x[ok], rcond=None)[0]
        R[k] = np.where(ok, x - np.nan_to_num(C) @ b, np.nan)
    return R.corr()


def feature_correlations() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Correlation of the eight daily path signals (+ rkurt) with the existing price features of the same session,
    R^2 on [ret_1d/rv, body_rel, close_in_range], and the correlation matrix among the path signals."""
    df = pd.read_parquet(FEATURES)
    P = load_features().reindex(df.index)
    ex = pd.DataFrame({"ret_1d": df["ret_1d"], "ret_1d/rv_1d": df["ret_1d"] / df["rv_1d_bp"].replace(0, np.nan), "range_pips": df["range_pips"],
                       "range_rel_adr": df["range_rel_adr"], "close_in_range": df["close_in_range"], "body_rel": df["body_rel"],
                       "sess_asia_bp": df["sess_asia_bp"], "sess_london_bp": df["sess_london_bp"], "sess_overlap_bp": df["sess_overlap_bp"],
                       "sess_nypm_bp": df["sess_nypm_bp"], "rv_1d_bp": df["rv_1d_bp"]})
    rows = []
    C = np.column_stack([ex["ret_1d/rv_1d"], ex["body_rel"], ex["close_in_range"] - 0.5, np.ones(len(ex))])
    for k in SIG + ["rkurt"]:
        x = P[k]
        r = {"signal": k, **{c: x.corr(ex[c]) for c in ex.columns}, "spearman_ret_1d": x.corr(ex["ret_1d"], method="spearman")}
        ok = x.notna().values & ~np.isnan(C).any(axis=1)
        beta = np.linalg.lstsq(C[ok], x.values[ok], rcond=None)[0]
        res = x.values[ok] - C[ok] @ beta
        r["R2_on_existing"] = 1 - res.var() / x.values[ok].var()
        r["n"] = int(ok.sum())
        rows.append(r)
    return pd.DataFrame(rows), P[SIG + ["rkurt"]].corr()


# ================================================================================================ incremental value
def incremental(write: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Three-way vs two-way EW combination (meta.combine / report_combo) and daily-P&L correlations."""
    from eurusd.arms.meta import combine, report_combo, load_arm_daily
    tabs = []
    for name, arms in (("two_way", ["weak_signals", "regime_trend"]), ("three_way", ["weak_signals", "regime_trend", ARM])):
        pnl, w = combine(arms, "EW")
        t = report_combo(pnl, name, len(arms))
        t["years_arm_in"] = int((w[ARM] > 0).sum()) if ARM in w else 0
        t["years_arm_in_2016plus"] = int((w.loc[w.index >= 2016, ARM] > 0).sum()) if ARM in w else 0
        tabs.append(t)
    inc = pd.concat(tabs, ignore_index=True)
    mine = load_arm_daily(ARM)
    rows = []
    for nm in ("weak_signals", "regime_trend"):
        J = pd.concat([mine.rename("a"), load_arm_daily(nm).rename("b")], axis=1).dropna()
        for lab, a, b in PERIODS:
            x = J[(J.index.year >= a) & (J.index.year <= b)]
            xa = x[x.a != 0]
            rows.append({"other": nm, "period": lab, "corr_daily_pnl": x.a.corr(x.b), "corr_when_arm_active": xa.a.corr(xa.b) if len(xa) > 30 else np.nan,
                         "corr_monthly_pnl": x.a.resample("ME").sum().corr(x.b.resample("ME").sum())})
    cor = pd.DataFrame(rows)
    if write:
        inc.to_csv(RES / f"{ARM}_incremental.csv", index=False)
        cor.to_csv(RES / f"{ARM}_correlations.csv", index=False)
    return inc, cor

# ================================================================================================ post-hoc: is `late` a bid-price artefact?
def late_artefact_check(cost_pips: float = 1.2, write: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """POST-HOC (written after the 19 results were seen; not a candidate). The only single signal with a positive
    record is d1_late, and its training-window sign is NEGATIVE (fade the last hour). The M1 file holds BID prices and
    the session closes inside the 17:00 New York rollover, when spreads widen and the bid is marked down: a depressed
    closing bid makes `late` negative and the next close-to-close return positive without anything tradable.
    Checks: (1) where the 'predicted' return is realised: fwd_1d = [close -> m minutes into the next session] + rest;
    (2) which part of `late` predicts: 16:00 -> 16:45 New York vs 16:45 New York -> close;
    (3) the d1_late positions executed 60 minutes after each close (entry and exit prices 60 minutes into the next
    session) - one extra backtest."""
    df = pd.read_parquet(FEATURES)
    P = load_features().reindex(df.index)
    m1 = pd.read_parquet(M1, columns=["close"]).loc["2002-12-31":]
    ts = m1.index.as_unit("ns").asi8
    lc = np.log(m1["close"].values)
    S = df.index.as_unit("ns").asi8
    MIN = 60_000_000_000
    def px(tau, lo):                                    # last 1-minute close stamped in [lo, tau)
        pos = np.searchsorted(ts, tau) - 1
        return np.where((pos >= 0) & (ts[np.maximum(pos, 0)] >= lo), lc[np.maximum(pos, 0)], np.nan)
    lclose = np.log(df["close"].values)
    out = pd.DataFrame(index=df.index)
    for m in (5, 15, 30, 60, 120, 240):
        pm = px(S + m * MIN, S)                         # price m minutes into each session
        out[f"early_{m}"] = (np.r_[pm[1:], np.nan] - lclose) * 1e4
        out[f"rest_{m}"] = df["fwd_1d"].values - out[f"early_{m}"].values
        out[f"p_{m}"] = pm
    dates = pd.DatetimeIndex(pd.to_datetime(S + 2 * 60 * MIN)).normalize()
    t1600 = _local_utc_ns(dates, 16, "America/New_York")
    p1600 = px(t1600, S); p1645 = px(t1600 + 45 * MIN, S)
    rv = (P["rv5_bp"].values / 1e4)
    out["late"] = P["late"].values
    rv = np.where(rv > 0, rv, np.nan)
    out["late_a_1600_1645"] = (p1645 - p1600) / rv
    out["late_b_1645_close"] = (lclose - p1645) / rv
    out.loc[P["ok"].values == 0, ["late_a_1600_1645", "late_b_1645_close"]] = np.nan
    out["fwd_1d"] = df["fwd_1d"].values
    summer = pd.Series((df["close_time"].dt.tz_convert("America/New_York").dt.hour == 18).values, index=df.index)   # close = 18:00 NY
    rows = []
    for lab, msk in (("all", pd.Series(True, index=df.index)), ("close=17:00 NY (US winter)", ~summer), ("close=18:00 NY (US summer)", summer),
                     ("2010-2026", pd.Series(df.index.year >= 2010, index=df.index)), ("2016-2026", pd.Series(df.index.year >= 2016, index=df.index))):
        o = out[msk.values]
        r = {"sample": lab, "n": int(o["late"].notna().sum()), "corr(late,fwd_1d)": o["late"].corr(o["fwd_1d"])}
        for m in (5, 15, 30, 60, 120, 240):
            r[f"corr(late,first_{m}min)"] = o["late"].corr(o[f"early_{m}"])
            r[f"corr(late,rest_after_{m}min)"] = o["late"].corr(o[f"rest_{m}"])
        r["corr(late_a,fwd_1d)"] = o["late_a_1600_1645"].corr(o["fwd_1d"])
        r["corr(late_b,fwd_1d)"] = o["late_b_1645_close"].corr(o["fwd_1d"])
        r["corr(late_a,rest_after_60min)"] = o["late_a_1600_1645"].corr(o["rest_60"])
        r["corr(late_b,rest_after_60min)"] = o["late_b_1645_close"].corr(o["rest_60"])
        r["mean_late_bp"] = float(P.loc[msk.values, "late_bp"].mean())
        r["mean_first_60min_bp"] = float(o["early_60"].mean())
        rows.append(r)
    tab = pd.DataFrame(rows)
    # (3) same positions, executed 60 minutes after the close
    D = load_frame()
    pos = positions(D, ["d1_late"])
    p60 = out["p_60"].values
    fwd60 = pd.Series((np.r_[p60[2:], np.nan, np.nan] - np.r_[p60[1:], np.nan]) * 1e4, index=df.index)   # 60 min after close(t) -> 60 min after close(t+1)
    D2 = D.copy(); D2["fwd_1d"] = fwd60
    t_lag = evaluate(D2, pos, "d1_late_executed_60min_after_close", "post_hoc", cost_pips)[1]
    t_g = evaluate(D2, pos, "d1_late_executed_60min_after_close", "post_hoc", 0.0)[1]
    bt = pd.concat([t_lag, t_g], ignore_index=True)
    if write:
        tab.to_csv(RES / f"{ARM}_late_artefact.csv", index=False)
        bt.to_csv(RES / f"{ARM}_late_lagged_execution.csv", index=False)
    return tab, bt


def tranche_hit_rate(final: str) -> pd.DataFrame:
    """Hit rate of the final's daily targets against the label of its own horizon (overlapping for w5)."""
    D = load_frame()
    V = variant_cols()
    legs = ["combo_d1", "combo_w5"] if final == "combo_both" else [final]
    rows = []
    for n in legs:
        s = targets(D, V[n][1])
        y = D["fwd_1d"] if V[n][1][0].startswith("d1") else D["fwd_5d"]
        for lab, a, b in PERIODS:
            m = (s.index.year >= a) & (s.index.year <= b) & (s != 0) & y.notna() & (y != 0)
            rows.append({"leg": n, "period": lab, "n_targets": int(m.sum()), "hit_sign_own_horizon": float((np.sign(s[m]) == np.sign(y[m])).mean())})
    return pd.DataFrame(rows)

def control_followup(final: str, cost_pips: float = 1.2, n_null: int = 200, seed: int = 1, write: bool = True) -> pd.DataFrame:
    """POST-HOC robustness of control (a) (the final's signals residualised on the existing price features), run only
    because that pre-declared control came out positive. No new variant: the same stream is (i) lagged by 1/5/21
    sessions, (ii) compared with a circular-shift null, (iii) correlated with the live streams and (iv) put through the
    three-way EW combination in a temporary directory (nothing is written next to the arms' position files)."""
    import shutil
    import tempfile
    from eurusd.arms import meta
    D = load_frame()
    V = variant_cols()
    legs = ["combo_d1", "combo_w5"] if final == "combo_both" else [final]
    fcols = [c for c in D.columns if c[:3] in ("d1_", "w5_")]
    def stream(Dx):
        pos = sum(positions(Dx, V[n][1], residualise=True) for n in legs) / len(legs)
        return pos, evaluate(Dx, pos, "ctrl", "post_hoc", cost_pips)
    pos0, (pnl0, t0) = stream(D)
    per = [p for p, _, _ in PERIODS]
    rows = [{"check": "control_a_actual", **{f"SR_{p}": t0.set_index("period").loc[p, "sharpe"] for p in per + ["2010-2015"]}}]
    for lag in (1, 5, 21, -1):
        Dl = D.copy(); Dl[fcols] = D[fcols].shift(lag)
        tl = stream(Dl)[1][1].set_index("period")
        rows.append({"check": f"control_a_features_shift_{lag:+d}", **{f"SR_{p}": tl.loc[p, "sharpe"] for p in per + ["2010-2015"]}})
    rng = np.random.default_rng(seed)
    idx = np.where(D.index.year >= 2010)[0]
    null = []
    for _ in range(n_null):
        Dl = D.copy(); v = D[fcols].values.copy(); v[idx] = np.roll(v[idx], int(rng.integers(252, len(idx) - 252)), axis=0); Dl[fcols] = v
        null.append(stream(Dl)[1][1].set_index("period").loc[per, "sharpe"].values)
    null = np.array(null); act = t0.set_index("period").loc[per, "sharpe"].values
    rows.append({"check": "control_a_circular_null_mean", **{f"SR_{p}": null[:, j].mean() for j, p in enumerate(per)}})
    rows.append({"check": "control_a_circular_null_q95", **{f"SR_{p}": np.quantile(null[:, j], 0.95) for j, p in enumerate(per)}})
    rows.append({"check": "control_a_p_null_ge_actual", **{f"SR_{p}": (null[:, j] >= act[j]).mean() for j, p in enumerate(per)}})
    old = meta.RES
    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        for a in ("weak_signals", "regime_trend"):
            shutil.copy(old / f"{a}_positions.parquet", td / f"{a}_positions.parquet")
        o = pd.DataFrame({"pos": pos0, "fwd_bp": D["fwd_1d"], "net_bp": pnl0["net_bp"].reindex(D.index)})
        o[o.index.year >= 2010].to_parquet(td / "ctrl_positions.parquet")
        meta.RES = td
        try:
            for nm, arms in (("two_way", ["weak_signals", "regime_trend"]), ("three_way_with_control_a", ["weak_signals", "regime_trend", "ctrl"])):
                t = meta.report_combo(meta.combine(arms, "EW")[0], nm, len(arms)).set_index("period")
                rows.append({"check": f"EW_{nm}", **{f"SR_{p}": t.loc[p, "sharpe"] for p in per}})
            mine = meta.load_arm_daily("ctrl")
            for a in ("weak_signals", "regime_trend"):
                J = pd.concat([mine.rename("a"), meta.load_arm_daily(a).rename("b")], axis=1).dropna()
                rows.append({"check": f"control_a_corr_daily_pnl_{a}", **{f"SR_{p}": J[(J.index.year >= x) & (J.index.year <= y)].corr().iloc[0, 1] for p, x, y in PERIODS}})
        finally:
            meta.RES = old
    out = pd.DataFrame(rows)
    if write:
        out.to_csv(RES / f"{ARM}_control_followup.csv", index=False)
    return out


if __name__ == "__main__":
    cost = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
    pos, rep = run(cost_pips=cost, rebuild="--rebuild" in sys.argv)
    final = rep.loc[rep["final"], "variant"].iloc[0]
    fc, cm = feature_correlations()
    fc.to_csv(RES / f"{ARM}_feature_corr.csv", index=False)
    cm.to_csv(RES / f"{ARM}_signal_corr.csv")
    print(fc.round(3).to_string(index=False))
    print(cm.round(2).to_string())
    rc = residual_corr()
    rc.to_csv(RES / f"{ARM}_residual_signal_corr.csv")
    print("residual correlations (after removing ret_1d/rv, body_rel, close_in_range)"); print(rc.round(2).to_string())
    ct = controls(final, cost)
    ct.to_csv(RES / f"{ARM}_controls.csv", index=False)
    for v in ct.variant.unique():
        r = ct[(ct.variant == v) & (ct.cost_pips == cost)].set_index("period")
        print(f"control {v:48s} 2010-26 SR {r.loc['2010-2026','sharpe']:+.2f} t {r.loc['2010-2026','t']:+.2f} | 2016-26 SR {r.loc['2016-2026','sharpe']:+.2f} | 2023-26 SR {r.loc['2023-2026','sharpe']:+.2f}")
    lc = leak_checks(final, cost_pips=cost)
    lc.to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
    skip = ("signal_label_corr", "circular_shift_null", "feature_truncation", "shuffled_labels_summary")
    print(lc[lc.check == "shuffled_labels_summary"][["period", "n_perm", "net_mean", "net_sd", "gross_mean", "gross_sd"]].round(3).to_string(index=False))
    for chk in [c for c in lc.check.unique() if c not in skip]:
        r = lc[lc.check == chk].set_index("period")
        print(f"leak check {chk:42s} 2010-26 SR {r.loc['2010-2026','sharpe']:+.2f} t {r.loc['2010-2026','t']:+.2f} | "
              f"2016-26 SR {r.loc['2016-2026','sharpe']:+.2f} | 2023-26 SR {r.loc['2023-2026','sharpe']:+.2f}")
    print(lc[lc.check == "circular_shift_null"][["period", "sharpe", "null_mean", "null_sd", "null_q95", "p_null_ge_actual"]].round(3).to_string(index=False))
    print(lc[lc.check == "feature_truncation"][["period", "max_abs_diff", "nan_mismatch"]].to_string(index=False))
    print(lc[lc.check == "signal_label_corr"][["period", "label", "corr_full_sample", "corr_same_session_ret", "n"]].round(4).to_string(index=False))
    inc, cor = incremental()
    print(inc[inc.period.isin(["2010-2026", "2016-2026", "2023-2026"])].round(3).to_string(index=False))
    print(cor.round(3).to_string(index=False))
    th = tranche_hit_rate(final)
    th.to_csv(RES / f"{ARM}_tranche_hit.csv", index=False)
    print(th.round(3).to_string(index=False))
    print(control_followup(final, cost).round(3).to_string(index=False))
    tab, bt = late_artefact_check(cost)
    print(tab.round(3).T.to_string())
    for cst in bt.cost_pips.unique():
        r = bt[bt.cost_pips == cst].set_index("period")
        print(f"post-hoc d1_late executed 60 min after the close, cost {cst}: 2010-26 SR {r.loc['2010-2026','sharpe']:+.2f} t {r.loc['2010-2026','t']:+.2f} | "
              f"2016-26 SR {r.loc['2016-2026','sharpe']:+.2f} | 2023-26 SR {r.loc['2023-2026','sharpe']:+.2f} | hit_sign {r.loc['2010-2026','hit_sign']:.3f}")
