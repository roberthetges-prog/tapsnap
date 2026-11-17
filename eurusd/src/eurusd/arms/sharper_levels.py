"""Arm CA `sharper_levels` (round 11): narrower and more evenly reliable LOWER / UPPER levels for 5, 21 and 63 sessions.

DECLARED BEFORE ANY OUTCOME WAS COMPUTED (2026-11-17). At the time of writing I had read the protocol, the research
log, `bots.py`, `72_bots.py`, the published `bots_levels.csv` and the reports named in the brief, and had looked only at
INPUTS (shapes and columns of the frames, coverage of the event calendar by year). No level of any candidate below had
been scored.

Product being improved: `eurusd.bots` gives, for h = 5 / 21 / 63 sessions, a LOWER level (the period's lowest low is
expected to stay above it 8 times in 10) and an UPPER level (the highest high below it 8 times in 10); the published
level is the median of 100 bots, each = (20 % / 80 % quantile of dn / (g sqrt(h)), up / (g sqrt(h)) in its memory) x its
gauge g today. No direction is forecast here: every candidate is centred on the current close.

Notation. dn_h, up_h = log distance from the close to the lowest low / highest high of the next h sessions (frame
columns `dn{h}`, `up{h}`); a candidate gives log distances l < 0 < u; LOWER = close * exp(l), UPPER = close * exp(u).
"Held" = dn >= l (lower), up <= u (upper).

STEP 1, RECONCILE (before anything else): my own scoring of the bots' median level must reproduce `bots_levels.csv`
(holding rates, widths, worst years by era, and the two volatility halves) on `eurusd.bots.build()`.

WALK-FORWARD (as everywhere): yearly, expanding. For test year Y everything (regression coefficients, quantile
constants, step sizes) is fitted on sessions whose h-session outcome was known before Y-01-01 (`yend{h}` < Y-01-01).
Test years 2007-2026 for the new candidates (2006-2026 for the bots, as published); scored eras start in 2010.

CANDIDATES (12, counted, the baseline included; nothing else will be scored as a candidate):
  C0  bots        BASELINE: the median of the 100 bots' levels exactly as `bots.run_bot` computes them.
  C1  bots_pooled the same 100 bots, but each bot uses ONE constant for both sides: the 80 % quantile of the pooled
                  {-dn, up} / (g sqrt(h)) of its memory (direction is a coin flip, so the two sides share a constant;
                  isolates the calibration change from the volatility estimate).
  C2  shrink      horizon-specific scaling with ONE gauge: OLS of log R_h on [1, log g_blend], R_h = up_h - dn_h (log
                  range of the next h sessions); scale s = exp(fit); level = -/+ q s with q = 80 % quantile of the pooled
                  {-dn, up} / s in the training window. (The slope replaces "today's volatility x sqrt(h)": below 1 it
                  shrinks towards the long-run level, differently per horizon.)
  C3  har_d       as C2 with HAR regressors from daily close-to-close returns: log v_5, v_21, v_63, v_252,
                  v_k = sqrt(mean of r^2 over the last k sessions).
  C4  har_gk      as C2 with range-based regressors: Garman-Klass daily variance, log v_1, v_5, v_21, v_63, v_252.
  C5  har_rv      as C2 with realised variance from HOURLY returns (sum of squared hourly log returns per session, the
                  store's `rv_1d_bp` definition): log v_1, v_5, v_21, v_63, v_252. (Hourly, not 5-minute: the live
                  product has hourly bars; the efficiency lost at multi-day horizons is small.)
  C6  har_rv_ev   EVENT ADJUSTMENT: C5 plus the number of scheduled FOMC statements, ECB decisions and US payroll
                  reports falling inside the window (close, close + ceil(1.4 h) calendar days]. Calendar from
                  data/macro (fomc_decisions scheduled rows, ecb_decisions, us_bls_releases; before 2010 payrolls = first
                  Friday of the month). CPI dates do not exist before 2010 in the project's files, so CPI enters the
                  event-week reporting split but not the regression.
  C7  qr          DIRECT QUANTILE REGRESSION, each side separately: 80 % quantile of -dn_h (lower) and of up_h (upper)
                  on [1, v_1, v_5, v_21, v_63, v_252] sqrt(h) (hourly realised volatilities, levels not logs).
  C8  qr_semi     SEPARATE DOWN-SIDE AND UP-SIDE VOLATILITY: as C7 with regressors [1, d_5, d_21, d_63, u_5, u_21, u_63,
                  v_252] sqrt(h), d_k / u_k = sqrt(2 x mean down / up semivariance of hourly returns over k sessions).
  C9  aci_bots    ADAPTIVE (conformal-style) correction of C0. Each side has a log multiplier lam (start 0):
                  level_t = base_t x exp(lam_t). A level set at s that is broken at session tau <= s + h adds
                  +0.8 gamma to lam at the close of tau (a miss is known when it happens); a level that survives its h
                  sessions subtracts 0.2 gamma at the close of s + h. gamma = gamma0 / h. gamma0 is chosen each year from
                  {0, 0.1, 0.25, 0.5, 1.0} as the value whose adaptive path had the lowest proper score on outcomes
                  known before Y-01-01 (0 if fewer than 250 such sessions); one gamma0 for both sides.
  C10 aci_har     the same adaptive correction on C5.
  C11 avg         simple average of the log distances of C3, C4, C5 and C7.
Reference, not a candidate: `unscaled` = the 20 % / 80 % quantiles of dn_h / up_h in the training window, no
volatility information (the "no volatility scaling" row of the bots' test).

SCORING (every candidate, h = 5 / 21 / 63, eras 2010-26, 2016-26, 2023-26, 2010-17, 2018-26; common sample = sessions
where all 12 candidates have a level and the outcome is known; n_indep = sessions / h; Wilson intervals on n_indep):
  * holding rate of each level; average and median width 100 x (exp(u) - exp(l));
  * PROPER SCORE S_h = mean of [pinball_0.2(dn - l) + pinball_0.8(up - u)] / 2 in basis points (lower is better),
    pinball_tau(x) = x (tau - 1{x < 0});
  * holding rate by tercile of `g_rv21` (cut points from the scored sessions of the era), in event weeks vs other
    weeks (h = 5: a scheduled FOMC statement, ECB decision, US payrolls or US CPI inside the window; at 21 / 63 sessions
    every window contains several, so the split is reported for h = 5 only), and the worst single calendar year;
  * MATCHED RELIABILITY (a reporting device applied identically to every candidate, not a candidate): for test year Y
    each side is multiplied by the constant k that makes the candidate's fold-Y model hold exactly 80 % on its own
    training rows (for the adaptive candidates: on their own walk-forward path before Y); out-of-sample width and
    holding of the rescaled levels are then compared.

SELECTION RULE (fixed now): among C1..C11, the candidate with the lowest mean over h of S_h(candidate) / S_h(C0) on
2010-2017. If no candidate has a mean ratio below 1, the answer is "no method beats the bots' levels" and the arm FAILS.

PASS BAR (primary test), on 2018-2026, which the selection never saw; ALL four clauses:
  (i)   S_h(chosen) < S_h(C0) at h = 5, 21 and 63;
  (ii)  the paired moving-block-bootstrap 95 % interval of S_h(chosen) - S_h(C0) excludes zero at two of the three
        horizons at least (blocks of max(21, 2h) sessions, 2,000 draws, seed fixed);
  (iii) each level (lower and upper) of the chosen candidate holds between 77 % and 83 % at every horizon (six cells);
  (iv)  the spread (max - min) of the holding rate across the three volatility terciles, averaged over the six cells,
        is smaller than the baseline's.
Declared with the bar, because clause (iii) is tight for 63 sessions (about 35 independent periods in 2018-26): the
probability that an exactly calibrated method passes (iii), estimated by block-bootstrapping the chosen candidate's
own hit series re-centred to 80 % (all six cells resampled jointly), is reported next to the verdict. The verdict is
the bar as written.

REPLICATION (nothing re-tuned): the chosen candidate against the same 100 bots' median on GBP/USD, USD/JPY, AUD/USD,
USD/CHF, USD/CAD, NZD/USD, sessions and hourly bars built as arm BA built them (5-minute bars -> hourly -> sessions,
bad-tick rule of that arm), same walk-forward. A pair "improves" if the mean over h of S_h(chosen) / S_h(bots) is below
1 in 2010-26; reported with per-horizon bootstrap intervals, holding rates and tercile spreads; the count of six is
the replication result. (If the chosen candidate uses the event calendar: FOMC and payrolls only on the other pairs.)

SANITY CHECKS (controls, not candidates):
  * shuffled order: the sessions of 2003-2026 are permuted (each session keeps its own return, high, low and realised
    variance; volatility clustering is destroyed), the frame is rebuilt and the walk-forward repeated, 10 draws: the
    advantage of the chosen candidate and of the bots over `unscaled` should vanish;
  * no future data: for 40 random sessions of 2010-2026 the raw inputs (hourly bars, daily frame) are truncated at
    that session's close, the frame rebuilt from scratch and the chosen candidate's and the baseline's levels
    recomputed; they must equal the full-run levels;
  * sensitivity to the February-July 2023 data hole: scores without decision sessions whose look-back (21 sessions)
    or forward window contains a thin session (fewer than 20 hourly bars).
Everything else in the report is labelled descriptive.

Implementation notes, also fixed before the first outcome (inputs only): a one-session volatility estimate (Garman-Klass
or hourly) below a quarter of the 21-session one is floored there (four flat-quote sessions of 2004-05 and a few holiday
sessions; the logarithm needs a positive number); the FOMC file lists some two-day meetings twice, rows within two days
of the previous one are dropped; MIN_ROWS = 500 training rows as in `bots.py`.

Entry points: `run()` (everything; writes experiments/results/arms/sharper_levels_*.csv and reports/arm_sharper_levels.md),
`build()` (the frame), `levels(X, h, asof) -> (lower, upper)` for the chosen candidate.
"""
from __future__ import annotations

import math
import sys
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B  # noqa: E402  (read only: the product's own frame and bot roster)
from eurusd import features as F  # noqa: E402

ARM = "sharper_levels"
PROC = ROOT / "data" / "processed"
CROSS = PROC / "cross"
MACRO = ROOT / "data" / "macro"
RES = ROOT / "experiments" / "results" / "arms"
REPORT = ROOT / "reports" / f"arm_{ARM}.md"

HORIZONS = (5, 21, 63)
BOT_YEARS = list(range(2006, 2027))
TEST_YEARS = list(range(2007, 2027))
ERAS = (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026), ("2010-17", 2010, 2017), ("2018-26", 2018, 2026))
SELECT_ERA, TEST_ERA = "2010-17", "2018-26"
MIN_ROWS = 500
Q = 0.80
GRID = (0.0, 0.1, 0.25, 0.5, 1.0)
ACI_MIN = 250
KS = (1, 5, 21, 63, 252)
THIN_H = 20
PAIRS = {"gbpusd": 1e-4, "usdjpy": 1e-2, "audusd": 1e-4, "usdchf": 1e-4, "usdcad": 1e-4, "nzdusd": 1e-4}
CANDS = ("bots", "bots_pooled", "shrink", "har_d", "har_gk", "har_rv", "har_rv_ev", "qr", "qr_semi", "aci_bots", "aci_har", "avg")
LABEL = {"bots": "C0 bots (baseline)", "bots_pooled": "C1 bots, sides pooled", "shrink": "C2 one gauge, fitted slope", "har_d": "C3 HAR daily returns",
         "har_gk": "C4 HAR Garman-Klass", "har_rv": "C5 HAR hourly realised vol", "har_rv_ev": "C6 HAR hourly + events", "qr": "C7 quantile regression",
         "qr_semi": "C8 quantile regr., down / up vol", "aci_bots": "C9 adaptive on bots", "aci_har": "C10 adaptive on C5", "avg": "C11 average C3 C4 C5 C7",
         "unscaled": "(reference) no volatility scaling"}
REG_FEATS = {"shrink": ["g_blend"], "har_d": [f"vd_{k}" for k in KS[1:]], "har_gk": [f"vg_{k}" for k in KS], "har_rv": [f"vr_{k}" for k in KS],
             "har_rv_ev": [f"vr_{k}" for k in KS]}
QR_FEATS = {"qr": [f"vr_{k}" for k in KS], "qr_semi": [f"sd_{k}" for k in KS[1:4]] + [f"su_{k}" for k in KS[1:4]] + ["vr_252"]}
EV_KINDS = ("fomc", "ecb", "nfp")
DEPENDS = {"aci_bots": ("bots",), "aci_har": ("har_rv",), "avg": ("har_d", "har_gk", "har_rv", "qr")}


# ====================================================================================================== small helpers
def wilson(p: float, n: float, z: float = 1.959964) -> tuple[float, float]:
    if n <= 0 or not np.isfinite(p):
        return np.nan, np.nan
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(max(p * (1 - p) / n + z * z / (4 * n * n), 0.0)) / den
    return mid - half, mid + half


def pinball(x: np.ndarray, tau: float) -> np.ndarray:
    return x * (tau - (x < 0))


def loss_series(l, u, dn, up) -> np.ndarray:
    """Per-session proper score in basis points: mean of the two pinball losses."""
    return 1e4 * 0.5 * (pinball(dn - l, 1 - Q) + pinball(up - u, Q))


def block_boot(x: np.ndarray, block: int, reps: int = 2000, seed: int = 11) -> tuple[float, float]:
    """Moving (circular) block bootstrap 95 % interval of the mean of x."""
    n = len(x)
    if n < 2 * block:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(n / block))
    starts = rng.integers(0, n, size=(reps, nb))
    idx = ((starts[:, :, None] + np.arange(block)[None, None, :]) % n).reshape(reps, -1)[:, :n]
    m = x[idx].mean(axis=1)
    return float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def utc(y: int) -> pd.Timestamp:
    return pd.Timestamp(f"{y}-01-01", tz="UTC")


# ====================================================================================================== frame
def hourly_rv(h1: pd.DataFrame) -> pd.DataFrame:
    """Realised variance and down / up semivariance per session from hourly close-to-close log returns (featstore's
    `rv_1d_bp` definition: sessions keyed at 22:00 UTC; the first return of a session spans the gap from the previous bar)."""
    hr = np.log(h1["close"].astype("float64")).diff()
    key = (h1.index - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
    sq = hr ** 2
    out = pd.DataFrame({"rv": sq.groupby(key).sum(), "rsn": sq.where(hr < 0, 0.0).groupby(key).sum(), "rsp": sq.where(hr > 0, 0.0).groupby(key).sum(),
                        "nbar": hr.groupby(key).size()})
    out.index = pd.DatetimeIndex(out.index).as_unit("us")
    return out


_EV: dict = {}


def event_times() -> dict:
    """Scheduled event times (UTC, ns): FOMC statements, ECB decisions, US payrolls (first Friday rule before 2010), US CPI (2010+)."""
    if _EV:
        return _EV
    f = pd.read_csv(MACRO / "fomc_decisions.csv")
    f = pd.to_datetime(f[f.scheduled == True].statement_utc, utc=True).sort_values()  # noqa: E712
    f = f[(f.diff().dt.days.fillna(99) > 2).values]                                   # the file lists a few meetings twice (two-day meetings)
    e = pd.to_datetime(pd.read_csv(MACRO / "ecb_decisions.csv").decision_utc, utc=True).sort_values()
    b = pd.read_csv(MACRO / "us_bls_releases.csv")
    bt = pd.to_datetime(b.release_utc, utc=True)
    nfp = bt[b.release == "Employment Situation"].sort_values()
    cpi = bt[b.release == "CPI"].sort_values()
    months = pd.date_range(pd.Timestamp("2002-12-01", tz="UTC"), nfp.min() - pd.Timedelta(days=20), freq="MS")
    early = pd.Series([m + pd.Timedelta(days=(4 - m.dayofweek) % 7, hours=13, minutes=30) for m in months])
    nfp = pd.concat([early, nfp]).sort_values()
    for k, s in (("fomc", f), ("ecb", e), ("nfp", nfp), ("cpi", cpi)):
        _EV[k] = pd.DatetimeIndex(s).as_unit("ns").asi8
    return _EV


def _count_in(t: np.ndarray, a: np.ndarray, b: np.ndarray) -> np.ndarray:
    return (np.searchsorted(t, b, side="right") - np.searchsorted(t, a, side="right")).astype(float)


def add_targets_gauges(X: pd.DataFrame) -> pd.DataFrame:
    """bots.build()'s labels, level targets and gauges for a plain session frame (__open/__high/__low/__close/__ct, __atr)."""
    lc = np.log(X["__close"])
    r = lc.diff()
    ct = X["__ct"]
    hi, lo = X["__high"], X["__low"]
    for h in HORIZONS:
        X[f"yend{h}"] = ct.shift(-h)
        fmin = lo[::-1].rolling(h, min_periods=h).min()[::-1].shift(-1)
        fmax = hi[::-1].rolling(h, min_periods=h).max()[::-1].shift(-1)
        X[f"dn{h}"] = np.log(fmin / X["__close"])
        X[f"up{h}"] = np.log(fmax / X["__close"])
    X["g_rv10"], X["g_rv21"], X["g_rv63"] = r.rolling(10).std(), r.rolling(21).std(), r.rolling(63).std()
    X["g_ewma"] = np.sqrt((r ** 2).ewm(alpha=0.06, adjust=False).mean())
    X["g_blend"] = (r.rolling(5).std() + X["g_rv21"] + X["g_rv63"]) / 3
    X["g_atr14"] = X["__atr"] / X["__close"]
    return X


def add_features(X: pd.DataFrame, rvd: pd.DataFrame, kinds=EV_KINDS) -> pd.DataFrame:
    """This arm's own columns, computed on the sessions that have true highs and lows (2003+), identically for every pair.
    vd_k / vg_k / vr_k = sqrt(mean over k sessions of the daily variance estimate: squared close-to-close return /
    Garman-Klass / hourly realised variance); sd_k, su_k = down / up semi-volatility; ev{h}_* = scheduled events in the window."""
    ok = X["__high"].notna().values
    S = X.loc[ok]
    lc = np.log(S["__close"])
    r = lc.diff()
    gk = 0.5 * np.log(S["__high"] / S["__low"]) ** 2 - (2 * np.log(2) - 1) * np.log(S["__close"] / S["__open"]) ** 2
    rv = rvd.reindex(S.index)
    new = {}
    for k in KS:
        new[f"vd_{k}"] = np.sqrt((r ** 2).rolling(k).mean())
        new[f"vg_{k}"] = np.sqrt(gk.rolling(k).mean())
        new[f"vr_{k}"] = np.sqrt(rv["rv"].rolling(k).mean())
        new[f"sd_{k}"] = np.sqrt(2 * rv["rsn"].rolling(k).mean())
        new[f"su_{k}"] = np.sqrt(2 * rv["rsp"].rolling(k).mean())
    for c in ("vg", "vr"):                                      # floor declared in the docstring
        new[f"{c}_1"] = np.maximum(new[f"{c}_1"], 0.25 * new[f"{c}_21"]).where(new[f"{c}_21"].notna())
    new["thin"] = (rv["nbar"] < THIN_H).astype(float)
    ev = event_times()
    a = pd.DatetimeIndex(S["__ct"]).as_unit("ns").asi8
    for h in HORIZONS:
        b = a + int(math.ceil(1.4 * h)) * 86400 * 10 ** 9
        for kd in ("fomc", "ecb", "nfp", "cpi"):
            new[f"ev{h}_{kd}"] = pd.Series(_count_in(ev[kd], a, b) if (kd in kinds or kd == "cpi") else 0.0, index=S.index)
    new["evweek"] = pd.Series((sum(new[f"ev5_{kd}"] for kd in ("fomc", "ecb", "nfp", "cpi")) > 0).astype(float), index=S.index)
    trend = (lc - lc.shift(63)).abs() / (r.rolling(63).std() * np.sqrt(63))
    new["trend63"] = trend
    N = pd.DataFrame(new, index=S.index).reindex(X.index)
    return pd.concat([X, N], axis=1)


def build(D: pd.DataFrame | None = None, h1: pd.DataFrame | None = None) -> pd.DataFrame:
    """EUR/USD: the bots' own frame (`bots.build`, untouched) plus this arm's columns. D, h1 as in `bots.build` (live use)."""
    warnings.filterwarnings("ignore")
    if h1 is None:
        from eurusd.data import load_ohlc
        h1 = load_ohlc("H1").loc["2003":]
        h1 = h1[~h1.index.duplicated(keep="last")]
        X = B.build()
    else:
        X = B.build(D, h1)
    X = X.copy()
    hist = (X["__src"] == "histdata")
    X["__high"], X["__low"], X["__open"] = X["__high"].where(hist), X["__low"].where(hist), X["__open"].where(hist)
    return add_features(X, hourly_rv(h1.loc["2003":]))


def generic_frame(d: pd.DataFrame, rvd: pd.DataFrame, kinds=EV_KINDS) -> pd.DataFrame:
    """The same frame for any pair from its session bars d (open, high, low, close, close_time; index = session start)."""
    X = pd.DataFrame(index=pd.DatetimeIndex(d.index).as_unit("us"))
    for c in ("open", "high", "low", "close"):
        X[f"__{c}"] = d[c].values.astype(float)
    ct = pd.DatetimeIndex(d["close_time"])
    X["__ct"] = (ct.tz_localize("UTC") if ct.tz is None else ct.tz_convert("UTC")).as_unit("us")
    X["__atr"] = F.atr(pd.DataFrame({"high": X["__high"], "low": X["__low"], "close": X["__close"]}), 14)
    X = add_targets_gauges(X)
    return add_features(X, rvd, kinds)


def eur_sessions() -> tuple[pd.DataFrame, pd.DataFrame]:
    """EUR/USD session bars exactly as the store builds them, and the hourly bars."""
    from eurusd.data import load_ohlc
    h1 = load_ohlc("H1").loc["2003":]
    h1 = h1[~h1.index.duplicated(keep="last")]
    d = F.daily_ohlc(h1[["open", "high", "low", "close"]], 22)
    d = d[(d["n"] >= 10) & (d.index.dayofweek != 5)].copy()
    d["close_time"] = d.index + pd.Timedelta(days=1)
    return d, h1


def pair_inputs(pair: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Session bars of another pair (arm BA's cached, cleaned frame) and its hourly realised variances (cached, small)."""
    d = pd.read_parquet(PROC / f"reliable_parts_daily_{pair}.parquet")
    p = PROC / f"{ARM}_rv_{pair}.parquet"
    if p.exists():
        rvd = pd.read_parquet(p)
    else:
        m5 = pd.read_parquet(CROSS / f"ofi_{pair}_M5.parquet", columns=["close"]).astype("float64")
        h1 = m5.resample("1h", label="left", closed="left").agg({"close": "last"}).dropna().loc["2003":]
        rvd = hourly_rv(h1)
        rvd.to_parquet(p)
    return d, rvd


# ====================================================================================================== candidates
_GROUPS = Counter((s["gauge"], s["memory"]) for s in B.SPECS)       # 18 distinct (gauge, memory) pairs among the 100 bots


def bots_fit(X: pd.DataFrame, h: int, start: pd.Timestamp, pooled: bool = False) -> dict:
    yend, ct = X[f"yend{h}"], X["__ct"]
    out = {}
    for (gname, mem) in _GROUPS:
        g = X[f"g_{gname}"].values.astype(float)
        dn, up = X[f"dn{h}"].values / (g * np.sqrt(h)), X[f"up{h}"].values / (g * np.sqrt(h))
        kl = (yend < start).values & np.isfinite(dn) & np.isfinite(up)
        if mem:
            kl &= (ct >= start - pd.DateOffset(years=mem)).values
        if kl.sum() < MIN_ROWS:
            out[(gname, mem)] = (np.nan, np.nan)
        elif pooled:
            q = np.quantile(np.concatenate([-dn[kl], up[kl]]), Q)
            out[(gname, mem)] = (-q, q)
        else:
            out[(gname, mem)] = (np.quantile(dn[kl], 1 - Q), np.quantile(up[kl], Q))
    return out


def bots_pred(model: dict, X: pd.DataFrame, h: int, rows: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """Median over the 100 bots in price space (as experiments/72_bots.py), returned as log distances."""
    c = X["__close"].values[rows]
    LO, HI = [], []
    for (gname, mem), cnt in _GROUPS.items():
        g = X[f"g_{gname}"].values.astype(float)[rows]
        qlo, qhi = model[(gname, mem)]
        LO += [c * np.exp(qlo * g * np.sqrt(h))] * cnt
        HI += [c * np.exp(qhi * g * np.sqrt(h))] * cnt
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        lo, hi = np.nanmedian(np.array(LO), axis=0), np.nanmedian(np.array(HI), axis=0)
    return np.log(lo / c), np.log(hi / c)


def _reg_design(X: pd.DataFrame, name: str, h: int) -> np.ndarray:
    cols = [np.ones(len(X))] + [np.log(X[c].values.astype(float)) for c in REG_FEATS[name]]
    if name == "har_rv_ev":
        cols += [X[f"ev{h}_{k}"].values.astype(float) for k in EV_KINDS if X[f"ev{h}_{k}"].abs().sum() > 0]
    with np.errstate(all="ignore"):
        return np.column_stack(cols)


def reg_fit(X: pd.DataFrame, name: str, h: int, start: pd.Timestamp) -> dict | None:
    A = _reg_design(X, name, h)
    dn, up = X[f"dn{h}"].values, X[f"up{h}"].values
    with np.errstate(all="ignore"):
        y = np.log(up - dn)
    ok = (X[f"yend{h}"] < start).values & np.isfinite(A).all(axis=1) & np.isfinite(y)
    if ok.sum() < MIN_ROWS:
        return None
    beta, *_ = np.linalg.lstsq(A[ok], y[ok], rcond=None)
    s = np.exp(A[ok] @ beta)
    q = float(np.quantile(np.concatenate([-dn[ok] / s, up[ok] / s]), Q))
    return {"beta": beta, "q": q, "n": int(ok.sum())}


def reg_pred(model: dict, X: pd.DataFrame, name: str, h: int, rows: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    s = np.exp(_reg_design(X, name, h)[rows] @ model["beta"])
    return -model["q"] * s, model["q"] * s


def _qr_design(X: pd.DataFrame, name: str, h: int) -> np.ndarray:
    return np.column_stack([np.ones(len(X))] + [100 * np.sqrt(h) * X[c].values.astype(float) for c in QR_FEATS[name]])


def qr_fit(X: pd.DataFrame, name: str, h: int, start: pd.Timestamp) -> dict | None:
    from statsmodels.regression.quantile_regression import QuantReg
    A = _qr_design(X, name, h)
    dn, up = 100 * X[f"dn{h}"].values, 100 * X[f"up{h}"].values
    ok = (X[f"yend{h}"] < start).values & np.isfinite(A).all(axis=1) & np.isfinite(dn) & np.isfinite(up)
    if ok.sum() < MIN_ROWS:
        return None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        bl = QuantReg(-dn[ok], A[ok]).fit(q=Q, max_iter=2000, p_tol=1e-7).params
        bu = QuantReg(up[ok], A[ok]).fit(q=Q, max_iter=2000, p_tol=1e-7).params
    return {"bl": np.asarray(bl), "bu": np.asarray(bu), "n": int(ok.sum())}


def qr_pred(model: dict, X: pd.DataFrame, name: str, h: int, rows: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    A = _qr_design(X, name, h)[rows]
    return -np.maximum(A @ model["bl"], 1e-3) / 100, np.maximum(A @ model["bu"], 1e-3) / 100


def unscaled_fit(X: pd.DataFrame, h: int, start: pd.Timestamp) -> dict | None:
    dn, up = X[f"dn{h}"].values, X[f"up{h}"].values
    ok = (X[f"yend{h}"] < start).values & np.isfinite(dn) & np.isfinite(up)
    if ok.sum() < MIN_ROWS:
        return None
    return {"l": float(np.quantile(dn[ok], 1 - Q)), "u": float(np.quantile(up[ok], Q))}


def fit(X: pd.DataFrame, name: str, h: int, start: pd.Timestamp):
    if name in ("bots", "bots_pooled"):
        return bots_fit(X, h, start, pooled=(name == "bots_pooled"))
    if name in REG_FEATS:
        return reg_fit(X, name, h, start)
    if name in QR_FEATS:
        return qr_fit(X, name, h, start)
    if name == "unscaled":
        return unscaled_fit(X, h, start)
    raise KeyError(name)


def predict(model, X: pd.DataFrame, name: str, h: int, rows: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = int(rows.sum())
    if model is None:
        return np.full(n, np.nan), np.full(n, np.nan)
    if name in ("bots", "bots_pooled"):
        return bots_pred(model, X, h, rows)
    if name in REG_FEATS:
        return reg_pred(model, X, name, h, rows)
    if name in QR_FEATS:
        return qr_pred(model, X, name, h, rows)
    return np.full(n, model["l"]), np.full(n, model["u"])


def _match_k(l: np.ndarray, u: np.ndarray, dn: np.ndarray, up: np.ndarray, min_n: int = MIN_ROWS) -> tuple[float, float]:
    """Multipliers that make the levels hold exactly 80 % on the given rows."""
    ok = np.isfinite(l) & np.isfinite(u) & np.isfinite(dn) & np.isfinite(up)
    if ok.sum() < min_n:
        return 1.0, 1.0
    return float(np.quantile(dn[ok] / l[ok], Q)), float(np.quantile(up[ok] / u[ok], Q))


def aci(X: pd.DataFrame, h: int, l0: np.ndarray, u0: np.ndarray, fixed: float | None = None) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Adaptive correction of the base path (l0, u0; arrays over all rows of X, NaN where no base level).
    Returns the selected path, its matched-reliability version and the gamma0 used at each row.
    `fixed` (descriptive use only) forces one step size instead of the declared yearly choice."""
    grid = GRID if fixed is None else (fixed,)
    n = len(X)
    c, lo, hi = X["__close"].values, X["__low"].values, X["__high"].values
    dn, up, yend = X[f"dn{h}"].values, X[f"up{h}"].values, X[f"yend{h}"]
    years = X.index.year.values
    have = np.isfinite(l0) & np.isfinite(u0)
    p0 = int(np.argmax(have)) if have.any() else n
    paths = {}
    for g0 in grid:
        g = g0 / h
        L, U = np.full(n, np.nan), np.full(n, np.nan)
        Lp, Up = np.full(n, np.nan), np.full(n, np.nan)
        mL, mU = np.zeros(n, bool), np.zeros(n, bool)
        ll = lu = 0.0
        for t in range(p0, n):
            s0 = max(p0, t - h)
            if t > s0 and g > 0:
                nl = (~mL[s0:t]) & (lo[t] < Lp[s0:t])
                nu = (~mU[s0:t]) & (hi[t] > Up[s0:t])
                ll += 0.8 * g * nl.sum(); lu += 0.8 * g * nu.sum()
                mL[s0:t] |= nl; mU[s0:t] |= nu
                if t - h >= p0:
                    if np.isfinite(Lp[t - h]) and not mL[t - h]:
                        ll -= 0.2 * g
                    if np.isfinite(Up[t - h]) and not mU[t - h]:
                        lu -= 0.2 * g
            if have[t]:
                L[t], U[t] = l0[t] * math.exp(ll), u0[t] * math.exp(lu)
                Lp[t], Up[t] = c[t] * math.exp(L[t]), c[t] * math.exp(U[t])
        paths[g0] = (L, U, loss_series(L, U, dn, up))
    Ls, Us, G0 = np.full(n, np.nan), np.full(n, np.nan), np.full(n, np.nan)
    Lm, Um = np.full(n, np.nan), np.full(n, np.nan)
    for Y in np.unique(years[have]):
        known = (yend < utc(Y)).values
        rows = years == Y
        best = grid[0]
        sc = {g0: paths[g0][2][known & np.isfinite(paths[g0][2])] for g0 in grid}
        if len(sc[grid[0]]) >= ACI_MIN:
            best = min(grid, key=lambda g0: sc[g0].mean())
        Ls[rows], Us[rows], G0[rows] = paths[best][0][rows], paths[best][1][rows], best
        kl, ku = _match_k(np.where(known, Ls, np.nan), np.where(known, Us, np.nan), dn, up, ACI_MIN)   # own walk-forward path before Y
        Lm[rows], Um[rows] = kl * Ls[rows], ku * Us[rows]
    return Ls, Us, Lm, Um, G0


def needed(names) -> list[str]:
    out = []
    for nm in names:
        for d in DEPENDS.get(nm, ()):
            if d not in out:
                out.append(d)
        if nm not in out:
            out.append(nm)
    return out


def walk(X: pd.DataFrame, h: int, names=CANDS + ("unscaled",), years=None, matched: bool = True) -> pd.DataFrame:
    """Walk-forward levels (log distances) of the named candidates. Columns: <name>|l, <name>|u (as declared) and
    <name>|lm, <name>|um (matched reliability). One row per session of X; NaN outside the test years."""
    names = needed(names)
    n = len(X)
    yr = X.index.year.values
    O = {}
    for nm in names:
        if nm in DEPENDS:
            continue
        l, u, lm, um = (np.full(n, np.nan) for _ in range(4))
        dn, up = X[f"dn{h}"].values, X[f"up{h}"].values
        for Y in (years or (BOT_YEARS if nm in ("bots", "unscaled") else TEST_YEARS)):
            rows = yr == Y
            if not rows.any():
                continue
            start = utc(Y)
            mdl = fit(X, nm, h, start)
            l[rows], u[rows] = predict(mdl, X, nm, h, rows)
            if matched and mdl is not None:
                known = (X[f"yend{h}"] < start).values
                li, ui = predict(mdl, X, nm, h, known)
                kl, ku = _match_k(li, ui, dn[known], up[known])
                lm[rows], um[rows] = kl * l[rows], ku * u[rows]
        O[nm] = (l, u, lm, um)
    for nm in names:
        if nm in ("aci_bots", "aci_har"):
            b = O[DEPENDS[nm][0]]
            O[nm] = aci(X, h, b[0], b[1])[:4]
        elif nm == "avg":
            parts = [O[d] for d in DEPENDS[nm]]
            O[nm] = tuple(np.mean([p[i] for p in parts], axis=0) for i in range(4))
    out = {}
    for nm in names:
        for i, sfx in enumerate(("l", "u", "lm", "um")):
            out[f"{nm}|{sfx}"] = O[nm][i]
    return pd.DataFrame(out, index=X.index)


# ====================================================================================================== scoring
def score_rows(l, u, dn, up, m, h: int, years=None) -> dict:
    """Holding rates, width and proper score on the rows m."""
    n = int(m.sum())
    if n == 0:
        return {"sessions": 0}
    lh, uh = dn[m] >= l[m], up[m] <= u[m]
    ni = n / h
    out = {"sessions": n, "n_indep": round(ni, 1), "lower_held": float(lh.mean()), "upper_held": float(uh.mean()), "both_held": float((lh & uh).mean()),
           "lower_lo": wilson(float(lh.mean()), ni)[0], "lower_hi": wilson(float(lh.mean()), ni)[1],
           "upper_lo": wilson(float(uh.mean()), ni)[0], "upper_hi": wilson(float(uh.mean()), ni)[1],
           "avg_width_pct": 100 * float((np.exp(u[m]) - np.exp(l[m])).mean()), "med_width_pct": 100 * float(np.median(np.exp(u[m]) - np.exp(l[m]))),
           "score_bp": float(loss_series(l[m], u[m], dn[m], up[m]).mean())}
    if years is not None:
        yr = pd.DataFrame({"l": lh, "u": uh}).groupby(years[m]).mean()
        out.update({"worst_year_lower": float(yr["l"].min()), "worst_year_upper": float(yr["u"].min()),
                    "worst_year_lower_y": int(yr["l"].idxmin()), "worst_year_upper_y": int(yr["u"].idxmin())})
    return out


def era_mask(years: np.ndarray, a: int, b: int) -> np.ndarray:
    return (years >= a) & (years <= b)


def reconcile(X: pd.DataFrame | None = None, verbose: bool = True) -> pd.DataFrame:
    """STEP 1: my scoring of the bots' median level against the published experiments/results/arms/bots_levels.csv."""
    X = build() if X is None else X
    pub = pd.read_csv(RES / "bots_levels.csv")
    yr = X.index.year.values
    rows = []
    for h in HORIZONS:
        W = walk(X, h, names=("bots", "unscaled"), matched=False)
        dn, up = X[f"dn{h}"].values, X[f"up{h}"].values
        for kind, nm in (("bots", "bots"), ("no volatility scaling", "unscaled")):
            l, u = W[f"{nm}|l"].values, W[f"{nm}|u"].values
            ok = np.isfinite(l) & np.isfinite(dn)
            for era, a, b in ERAS[:3]:
                rows.append({"h": h, "kind": kind, "era": era, **score_rows(l, u, dn, up, ok & era_mask(yr, a, b), h, yr)})
            m = ok & (yr >= 2010)
            g21 = X["g_rv21"].values
            hv = g21 > np.median(g21[m])
            for nmv, mm in (("volatility above its median", m & hv), ("volatility below its median", m & ~hv)):
                rows.append({"h": h, "kind": f"{kind} | {nmv}", "era": "2010-26", **score_rows(l, u, dn, up, mm, h)})
    mine = pd.DataFrame(rows)
    j = pub.merge(mine, on=["h", "kind", "era"], suffixes=("_pub", ""), how="left")
    cols = ["sessions", "lower_held", "upper_held", "both_held", "avg_width_pct", "worst_year_lower", "worst_year_upper"]
    for c in cols:
        j[f"d_{c}"] = j[c] - j[f"{c}_pub"]
    j["max_abs_diff"] = j[[f"d_{c}" for c in cols]].abs().max(axis=1)
    if verbose:
        print(f"RECONCILE: {len(j)} published rows, {int(j[cols[0]].notna().sum())} matched, largest absolute difference over all figures "
              f"{j['max_abs_diff'].max():.2e}")
    return j


def tercile_cells(l, u, dn, up, state: np.ndarray, m: np.ndarray) -> dict:
    """Holding rate of each level in the three terciles of `state` (cut points from the rows m)."""
    q1, q2 = np.quantile(state[m], [1 / 3, 2 / 3])
    out = {}
    for nm, mm in (("low", m & (state <= q1)), ("mid", m & (state > q1) & (state <= q2)), ("high", m & (state > q2))):
        out[nm] = (float((dn[mm] >= l[mm]).mean()), float((up[mm] <= u[mm]).mean()), int(mm.sum()),
                   100 * float((np.exp(u[mm]) - np.exp(l[mm])).mean()), float(loss_series(l[mm], u[mm], dn[mm], up[mm]).mean()))
    return out


def evaluate(X: pd.DataFrame, names=CANDS, base: str = "bots", boot: bool = True, verbose: bool = True) -> dict:
    """All scoring tables for the frame X. `names` must contain `base`."""
    yr = X.index.year.values
    S, ST, YR, BT, WK, LS = [], [], [], [], {}, {}
    for h in HORIZONS:
        W = walk(X, h, names=tuple(names) + ("unscaled",))
        WK[h] = W
        dn, up = X[f"dn{h}"].values, X[f"up{h}"].values
        ok = np.isfinite(dn) & np.isfinite(up) & (yr >= 2010)
        for nm in names:
            ok &= np.isfinite(W[f"{nm}|l"].values) & np.isfinite(W[f"{nm}|u"].values)
        g21, evw, tr = X["g_rv21"].values, X["evweek"].values, X["trend63"].values
        L = {nm: loss_series(W[f"{nm}|l"].values, W[f"{nm}|u"].values, dn, up) for nm in list(names) + ["unscaled"]}
        LS[h] = pd.DataFrame({**L, "ok": ok}, index=X.index)
        for nm in list(names) + ["unscaled"]:
            l, u, lm, um = (W[f"{nm}|{s}"].values for s in ("l", "u", "lm", "um"))
            for era, a, b in ERAS:
                m = ok & era_mask(yr, a, b)
                r = score_rows(l, u, dn, up, m, h, yr)
                rm = score_rows(lm, um, dn, up, m & np.isfinite(lm), h) if np.isfinite(lm[m]).any() else {}
                row = {"candidate": nm, "h": h, "era": era, **r, "lower_held_matched": rm.get("lower_held", np.nan), "upper_held_matched": rm.get("upper_held", np.nan),
                       "avg_width_matched_pct": rm.get("avg_width_pct", np.nan), "score_matched_bp": rm.get("score_bp", np.nan)}
                S.append(row)
                # state dependence
                for state, arr, lab in (("vol tercile", g21, None), ("trend tercile", tr, None)):
                    mm = m & np.isfinite(arr)
                    for k, v in tercile_cells(l, u, dn, up, arr, mm).items():
                        ST.append({"candidate": nm, "h": h, "era": era, "state": state, "class": k, "sessions": v[2], "n_indep": round(v[2] / h, 1),
                                   "lower_held": v[0], "upper_held": v[1], "avg_width_pct": v[3], "score_bp": v[4]})
                if h == 5:
                    for k, mm in (("event week", m & (evw > 0)), ("other week", m & (evw == 0))):
                        ST.append({"candidate": nm, "h": h, "era": era, "state": "scheduled events", "class": k, "sessions": int(mm.sum()), "n_indep": round(mm.sum() / h, 1),
                                   "lower_held": float((dn[mm] >= l[mm]).mean()), "upper_held": float((up[mm] <= u[mm]).mean()),
                                   "avg_width_pct": 100 * float((np.exp(u[mm]) - np.exp(l[mm])).mean()), "score_bp": float(L[nm][mm].mean())})
                # paired difference with the baseline
                if boot and nm != base:
                    d = (L[nm] - L[base])[m]
                    lo, hi = block_boot(d, max(21, 2 * h))
                    BT.append({"candidate": nm, "h": h, "era": era, "sessions": int(m.sum()), "diff_bp": float(d.mean()), "lo": lo, "hi": hi,
                               "ratio": float(L[nm][m].mean() / L[base][m].mean()), "excludes_zero": bool(hi < 0 or lo > 0)})
            m = ok
            for Y in np.unique(yr[m]):
                my = m & (yr == Y)
                YR.append({"candidate": nm, "h": h, "year": int(Y), "sessions": int(my.sum()), "lower_held": float((dn[my] >= l[my]).mean()),
                           "upper_held": float((up[my] <= u[my]).mean()), "avg_width_pct": 100 * float((np.exp(u[my]) - np.exp(l[my])).mean()), "score_bp": float(L[nm][my].mean())})
        if verbose:
            print(f"  h={h}: {int(ok.sum())} scored sessions 2010-26", flush=True)
    S, ST, YR = pd.DataFrame(S), pd.DataFrame(ST), pd.DataFrame(YR)
    BT = pd.DataFrame(BT)
    b = S[S.candidate == base].set_index(["h", "era"])
    key = list(zip(S.h, S.era))
    S["score_ratio"] = S["score_bp"].values / b["score_bp"].reindex(key).values
    S["width_ratio"] = S["avg_width_pct"].values / b["avg_width_pct"].reindex(key).values
    S["width_matched_ratio"] = S["avg_width_matched_pct"].values / b["avg_width_matched_pct"].reindex(key).values
    S["score_matched_ratio"] = S["score_matched_bp"].values / b["score_matched_bp"].reindex(key).values
    # spread of the holding rate across volatility terciles (six cells per candidate and era)
    v = ST[ST.state == "vol tercile"]
    g = v.groupby(["candidate", "era", "h"])
    sp = pd.DataFrame({"spread_lower": g["lower_held"].max() - g["lower_held"].min(), "spread_upper": g["upper_held"].max() - g["upper_held"].min()}).reset_index()
    spm = sp.groupby(["candidate", "era"]).apply(lambda d: float(np.mean(list(d.spread_lower) + list(d.spread_upper)))).rename("mean_spread").reset_index()
    return {"scores": S, "states": ST, "years": YR, "boot": BT, "spread_cells": sp, "spread": spm, "walk": WK, "loss": LS}


def select(S: pd.DataFrame, names=CANDS, base: str = "bots") -> tuple[str, pd.DataFrame]:
    """The declared rule: lowest mean over h of S_h / S_h(baseline) on 2010-17, among the non-baseline candidates."""
    t = S[(S.era == SELECT_ERA) & S.candidate.isin(names)].pivot(index="candidate", columns="h", values="score_ratio")
    t["mean_ratio"] = t.mean(axis=1)
    t = t.sort_values("mean_ratio")
    cand = t.drop(index=base)
    best = cand.index[0]
    return (best if cand["mean_ratio"].iloc[0] < 1 else base), t.reset_index()


def calibration_noise(X: pd.DataFrame, W: dict, name: str, a: int = 2018, b: int = 2026, reps: int = 5000, seed: int = 5) -> dict:
    """How often would an exactly calibrated method pass clause (iii)? Joint block bootstrap (126-session blocks) of the
    candidate's six hit series, each re-centred to 80 %."""
    yr = X.index.year.values
    m = era_mask(yr, a, b)
    H = []
    for h in HORIZONS:
        l, u = W[h][f"{name}|l"].values, W[h][f"{name}|u"].values
        dn, up = X[f"dn{h}"].values, X[f"up{h}"].values
        ok = np.isfinite(l) & np.isfinite(dn)
        H += [np.where(ok, dn >= l, np.nan)[m], np.where(ok, up <= u, np.nan)[m]]
    H = np.array(H, dtype=float).T
    n, block = len(H), 126
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(n / block))
    obs = np.nanmean(H, axis=0)
    inside, sd = 0, []
    for _ in range(reps):
        idx = ((rng.integers(0, n, nb)[:, None] + np.arange(block)[None, :]) % n).ravel()[:n]
        r = np.nanmean(H[idx], axis=0)
        sd.append(r)
        rc = r - obs + Q
        inside += int(((rc >= 0.77) & (rc <= 0.83)).all())
    sd = np.std(np.array(sd), axis=0)
    return {"p_pass_if_exactly_calibrated": inside / reps, "boot_sd_points": [round(100 * float(x), 1) for x in sd], "observed": [round(100 * float(x), 1) for x in obs]}


def verdict(E: dict, chosen: str, X: pd.DataFrame, base: str = "bots", noise: bool = True) -> dict:
    S, BT, SP = E["scores"], E["boot"], E["spread"]
    out = {"chosen": chosen}
    if chosen == base:
        out.update({"pass": False, "reason": "no candidate has a mean score ratio below 1 on 2010-17"})
        return out
    s = S[(S.candidate == chosen) & (S.era == TEST_ERA)].set_index("h")
    s0 = S[(S.candidate == base) & (S.era == TEST_ERA)].set_index("h")
    bt = BT[(BT.candidate == chosen) & (BT.era == TEST_ERA)].set_index("h")
    c1 = {h: bool(s.loc[h, "score_bp"] < s0.loc[h, "score_bp"]) for h in HORIZONS}
    c2 = {h: bool(bt.loc[h, "hi"] < 0) for h in HORIZONS}
    c3 = {(h, side): bool(0.77 <= s.loc[h, f"{side}_held"] <= 0.83) for h in HORIZONS for side in ("lower", "upper")}
    sp = float(SP[(SP.candidate == chosen) & (SP.era == TEST_ERA)]["mean_spread"].iloc[0])
    sp0 = float(SP[(SP.candidate == base) & (SP.era == TEST_ERA)]["mean_spread"].iloc[0])
    out.update({"clause_i_better_score_all_h": all(c1.values()), "clause_i_detail": c1,
                "clause_ii_interval_excludes_zero_at_2_of_3": sum(c2.values()) >= 2, "clause_ii_detail": c2,
                "clause_iii_all_six_within_77_83": all(c3.values()), "clause_iii_detail": {f"{h}_{side}": round(100 * float(s.loc[h, f'{side}_held']), 1) for h, side in c3},
                "clause_iii_baseline": {f"{h}_{side}": round(100 * float(s0.loc[h, f'{side}_held']), 1) for h, side in c3},
                "clause_iv_spread_smaller": bool(sp < sp0), "spread_chosen_points": round(100 * sp, 1), "spread_baseline_points": round(100 * sp0, 1)})
    if noise:
        out.update({"noise_chosen": calibration_noise(X, E["walk"], chosen), "noise_baseline": calibration_noise(X, E["walk"], base)})
    out["pass"] = bool(out["clause_i_better_score_all_h"] and out["clause_ii_interval_excludes_zero_at_2_of_3"] and out["clause_iii_all_six_within_77_83"]
                       and out["clause_iv_spread_smaller"])
    return out


# ====================================================================================================== chosen candidate
CHOSEN = "har_d"      # set by the declared selection rule on 2010-17 (see `select`); `run()` asserts that the rule still returns it


def levels(X: pd.DataFrame, h: int, asof=None, fit_before: pd.Timestamp | None = None, name: str = CHOSEN) -> tuple[float, float]:
    """LOWER and UPPER level (prices) of the chosen candidate for the session `asof` (index label of X; default the last
    session) and horizon h. X = `build()` (or `build(D, h1)` live). The model is fitted on sessions whose h-session
    outcome was known before `fit_before` (default: just after the close of `asof`, as `bots.live` does)."""
    pos = len(X) - 1 if asof is None else int(X.index.get_loc(pd.Timestamp(asof)))
    start = X["__ct"].iloc[pos] + pd.Timedelta(seconds=1) if fit_before is None else fit_before
    rows = np.zeros(len(X), bool)
    rows[pos] = True
    Xs = X.iloc[: pos + 1]
    if name in DEPENDS:
        raise NotImplementedError("combination candidates are produced by walk()")
    l, u = predict(fit(Xs, name, h, start), Xs, name, h, rows[: pos + 1])
    c = float(X["__close"].iloc[pos])
    return c * math.exp(float(l[0])), c * math.exp(float(u[0]))


# ====================================================================================================== descriptive extras
def expost_width(X: pd.DataFrame, WK: dict, names) -> pd.DataFrame:
    """DESCRIPTIVE (added after the primary result): the width each candidate would need to hold exactly 80 % on each side
    WITHIN the era (one multiplier per side fitted on the era itself). Pure sharpness at equal realised reliability."""
    yr = X.index.year.values
    rows = []
    for h in HORIZONS:
        W = WK[h]
        dn, up = X[f"dn{h}"].values, X[f"up{h}"].values
        ok = np.isfinite(dn) & np.isfinite(up) & (yr >= 2010)
        for nm in names:
            ok &= np.isfinite(W[f"{nm}|l"].values)
        for nm in list(names) + ["unscaled"]:
            l, u = W[f"{nm}|l"].values, W[f"{nm}|u"].values
            for era, a, b in ERAS:
                m = ok & era_mask(yr, a, b)
                kl, ku = _match_k(l[m], u[m], dn[m], up[m], 1)
                rows.append({"candidate": nm, "h": h, "era": era, "k_lower": kl, "k_upper": ku, "expost_width_pct": 100 * float((np.exp(ku * u[m]) - np.exp(kl * l[m])).mean()),
                             "expost_score_bp": float(loss_series(kl * l[m], ku * u[m], dn[m], up[m]).mean())})
    T = pd.DataFrame(rows)
    b = T[T.candidate == "bots"].set_index(["h", "era"])
    T["expost_width_ratio"] = T["expost_width_pct"].values / b["expost_width_pct"].reindex(list(zip(T.h, T.era))).values
    return T


def aci_fixed(X: pd.DataFrame, WK: dict, base: str = "bots") -> pd.DataFrame:
    """DESCRIPTIVE: what each fixed step size of the adaptive correction does (the internals of C9; the yearly rule chose among these)."""
    yr = X.index.year.values
    rows = []
    for h in HORIZONS:
        dn, up = X[f"dn{h}"].values, X[f"up{h}"].values
        for g0 in GRID:
            L, U = aci(X, h, WK[h][f"{base}|l"].values, WK[h][f"{base}|u"].values, fixed=g0)[:2]
            ok = np.isfinite(L) & np.isfinite(dn)
            for era, a, b in ERAS:
                rows.append({"base": base, "gamma0": g0, "h": h, "era": era, **score_rows(L, U, dn, up, ok & era_mask(yr, a, b), h, yr)})
    return pd.DataFrame(rows)


# ====================================================================================================== replication and controls
def replicate(names=CANDS, verbose: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """The same candidates, nothing re-tuned, on the six other pairs (and EUR/USD through the same generic frame as a check)."""
    S, B_, SP, REL = [], [], [], {}
    d, h1 = eur_sessions()
    frames = {"eurusd_generic": lambda: generic_frame(d, hourly_rv(h1))}
    for p in PAIRS:
        frames[p] = (lambda p=p: generic_frame(*pair_inputs(p), kinds=("fomc", "nfp")))
    for p, mk in frames.items():
        X = mk()
        E = evaluate(X, names=names, verbose=False)
        for k, lst in (("scores", S), ("boot", B_), ("spread", SP)):
            t = E[k].copy()
            t.insert(0, "pair", p)
            lst.append(t)
        for h in HORIZONS:
            REL[(p, h)] = E["loss"][h]
        if verbose:
            s = E["scores"]
            r = s[(s.candidate == CHOSEN) & (s.era == "2010-26")].set_index("h")["score_ratio"]
            print(f"  {p}: {len(X)} sessions; {CHOSEN} / bots score ratio 2010-26: " + " / ".join(f"{r[h]:.3f}" for h in HORIZONS), flush=True)
    return pd.concat(S, ignore_index=True), pd.concat(B_, ignore_index=True), pd.concat(SP, ignore_index=True), pooled_test(REL, [c for c in names if c != "bots"])


def pooled_test(REL: dict, names, base: str = "bots") -> pd.DataFrame:
    """DESCRIPTIVE (added after the primary result): the six other pairs pooled. Per pair the per-session loss difference
    to the bots is divided by the bots' mean loss in the era; the six series are averaged by date and the mean is given a
    moving-block-bootstrap interval (blocks of max(21, 2h) sessions). One test instead of six correlated ones."""
    rows = []
    for nm in names:
        for h in HORIZONS:
            for era, a, b in ERAS:
                parts = []
                for p in PAIRS:
                    L = REL[(p, h)]
                    m = L["ok"].values & era_mask(L.index.year.values, a, b)
                    parts.append(((L[nm] - L[base]) / L[base][m].mean())[m].rename(p))
                J = pd.concat(parts, axis=1)
                J.index = J.index.normalize()
                d = J.groupby(level=0).mean().mean(axis=1).dropna().values
                lo, hi = block_boot(d, max(21, 2 * h))
                rows.append({"candidate": nm, "h": h, "era": era, "dates": len(d), "pooled_rel_diff_pct": 100 * float(d.mean()), "lo_pct": 100 * lo, "hi_pct": 100 * hi,
                             "excludes_zero": bool(hi < 0 or lo > 0)})
    return pd.DataFrame(rows)


def shuffle_control(draws: int = 10, seed: int = 0, names=("bots", CHOSEN), verbose: bool = True) -> pd.DataFrame:
    """Sessions permuted (each keeps its own return, high, low and realised variance): volatility clustering destroyed."""
    d, h1 = eur_sessions()
    rvd = hourly_rv(h1).reindex(pd.DatetimeIndex(d.index).as_unit("us"))
    pc = d["close"].shift(1).fillna(d["open"])
    rel = np.log(d[["open", "high", "low", "close"]].div(pc, axis=0)).values
    rng = np.random.default_rng(seed)
    out = []
    for k in range(draws + 1):
        perm = np.arange(len(d)) if k == 0 else rng.permutation(len(d))
        R = rel[perm]
        c = float(d["open"].iloc[0]) * np.exp(np.cumsum(R[:, 3]))
        prev = np.concatenate([[float(d["open"].iloc[0])], c[:-1]])
        dd = pd.DataFrame({"open": prev * np.exp(R[:, 0]), "high": prev * np.exp(R[:, 1]), "low": prev * np.exp(R[:, 2]), "close": c, "close_time": d["close_time"].values}, index=d.index)
        rr = pd.DataFrame(rvd.values[perm], index=rvd.index, columns=rvd.columns)
        E = evaluate(generic_frame(dd, rr), names=names, boot=False, verbose=False)
        s = E["scores"]
        s = s[s.era == "2010-26"].copy()
        u = s[s.candidate == "unscaled"].set_index("h")["score_bp"]
        s["ratio_to_unscaled"] = s["score_bp"].values / u.reindex(s.h).values
        s.insert(0, "draw", k)
        sp = E["spread"]
        s["vol_tercile_spread"] = s.candidate.map(sp[sp.era == "2010-26"].set_index("candidate")["mean_spread"])
        out.append(s[["draw", "candidate", "h", "lower_held", "upper_held", "avg_width_pct", "score_bp", "ratio_to_unscaled", "vol_tercile_spread"]])
        if verbose:
            print(f"  shuffle draw {k}: " + "; ".join(f"{nm} {s[(s.candidate == nm)]['ratio_to_unscaled'].mean():.3f}" for nm in names), flush=True)
    return pd.concat(out, ignore_index=True)


def truncation_check(X: pd.DataFrame, WK: dict, n: int = 40, seed: int = 3, names=("bots", CHOSEN), verbose: bool = True) -> pd.DataFrame:
    """Recompute levels from raw inputs cut off at the session's close; compare with the full run."""
    from eurusd.data import load_ohlc
    D = pd.read_parquet(PROC / "features_daily.parquet")
    h1 = load_ohlc("H1").loc["2003":]
    h1 = h1[~h1.index.duplicated(keep="last")]
    rng = np.random.default_rng(seed)
    cand = X.index[(X.index.year >= 2010) & np.isfinite(WK[5][f"{CHOSEN}|l"].values)]
    pick = sorted(rng.choice(len(cand), size=n, replace=False))
    rows = []
    for i in pick:
        t = cand[i]
        Dt = D.loc[D.index <= t]
        ht = h1.loc[h1.index < t + pd.Timedelta(days=1)]
        Xt = build(Dt, ht)
        assert Xt.index[-1] == t
        for h in HORIZONS:
            Wt = walk(Xt, h, names=names, years=[t.year], matched=False)
            for nm in names:
                for sfx in ("l", "u"):
                    full, cut = float(WK[h].loc[t, f"{nm}|{sfx}"]), float(Wt[f"{nm}|{sfx}"].iloc[-1])
                    rows.append({"session": str(t)[:10], "h": h, "candidate": nm, "side": sfx, "full_run": full, "truncated": cut, "abs_diff": abs(full - cut)})
            lo, up_ = levels(Xt, h, asof=t, fit_before=utc(t.year))
            c = float(Xt["__close"].iloc[-1])
            rows.append({"session": str(t)[:10], "h": h, "candidate": f"levels() {CHOSEN}", "side": "l", "full_run": float(WK[h].loc[t, f"{CHOSEN}|l"]), "truncated": math.log(lo / c),
                         "abs_diff": abs(float(WK[h].loc[t, f"{CHOSEN}|l"]) - math.log(lo / c))})
    T = pd.DataFrame(rows)
    if verbose:
        print(f"  truncation: {n} sessions, {len(T)} levels, largest |difference| in log distance {T['abs_diff'].max():.2e}", flush=True)
    return T


def hole_sensitivity(X: pd.DataFrame, WK: dict, names=CANDS) -> pd.DataFrame:
    """Scores without decision sessions whose last 21 sessions or forward window contain a thin session (2023 data hole)."""
    yr = X.index.year.values
    thin = X["thin"].fillna(0).values
    rows = []
    for h in HORIZONS:
        back = pd.Series(thin).rolling(21, min_periods=1).max().values
        fwd = pd.Series(thin)[::-1].rolling(h, min_periods=1).max()[::-1].shift(-1).fillna(0).values
        clean = (back == 0) & (fwd == 0)
        dn, up = X[f"dn{h}"].values, X[f"up{h}"].values
        ok = np.isfinite(dn) & (yr >= 2010)
        for nm in names:
            ok &= np.isfinite(WK[h][f"{nm}|l"].values)
        for nm in names:
            l, u = WK[h][f"{nm}|l"].values, WK[h][f"{nm}|u"].values
            for era, a, b in (("2018-26", 2018, 2026), ("2023-26", 2023, 2026)):
                m = ok & era_mask(yr, a, b)
                r0, r1 = score_rows(l, u, dn, up, m, h), score_rows(l, u, dn, up, m & clean, h)
                rows.append({"candidate": nm, "h": h, "era": era, "sessions_all": r0["sessions"], "sessions_clean": r1["sessions"], "score_all": r0["score_bp"], "score_clean": r1["score_bp"],
                             "lower_all": r0["lower_held"], "lower_clean": r1["lower_held"], "upper_all": r0["upper_held"], "upper_clean": r1["upper_held"]})
    T = pd.DataFrame(rows)
    for c in ("all", "clean"):
        b = T[T.candidate == "bots"].set_index(["h", "era"])[f"score_{c}"]
        T[f"ratio_{c}"] = T[f"score_{c}"].values / b.reindex(list(zip(T.h, T.era))).values
    return T


def coefficients(X: pd.DataFrame, name: str = CHOSEN) -> pd.DataFrame:
    """DESCRIPTIVE: the chosen model's fitted coefficients per fold (what would be wired into the product)."""
    rows = []
    for h in HORIZONS:
        for Y in TEST_YEARS:
            m = fit(X, name, h, utc(Y))
            if m is None:
                continue
            rows.append({"candidate": name, "h": h, "test_year": Y, "train_rows": m["n"], "q80": m["q"],
                         **{f"b_{c}": float(v) for c, v in zip(["const"] + REG_FEATS[name], m["beta"])}})
    return pd.DataFrame(rows)


# ====================================================================================================== run
def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Everything, in the declared order. Returns (verdict dict, score table). `cost_pips` is unused (no trades here)."""
    import json
    pd.set_option("display.width", 250)
    X = build()
    T = {"reconcile": reconcile(X, verbose)}
    assert T["reconcile"]["max_abs_diff"].max() < 1e-9, "the bots' published level record is not reproduced"
    if verbose:
        print("scoring 12 candidates on EUR/USD ...", flush=True)
    E = evaluate(X, verbose=verbose)
    chosen, sel = select(E["scores"])
    assert chosen == CHOSEN, f"the declared rule now returns {chosen}; CHOSEN must not be edited by hand"
    V = verdict(E, chosen, X)
    T["bar_all"] = pd.DataFrame([{"candidate": nm, **{k: v for k, v in verdict(E, nm, X, noise=False).items() if not isinstance(v, dict) and k != "chosen"}}
                                 for nm in CANDS if nm != "bots"])
    if verbose:
        print(f"chosen by the 2010-17 rule: {chosen}; PASS = {V['pass']}", flush=True)
    S = E["scores"].copy()
    S["final"] = S.candidate == chosen
    T.update({"scores": S, "selection": sel, "boot": E["boot"], "states": E["states"], "spread_cells": E["spread_cells"], "spread": E["spread"], "years": E["years"],
              "expost": expost_width(X, E["walk"], CANDS), "aci_fixed": pd.concat([aci_fixed(X, E["walk"], "bots"), aci_fixed(X, E["walk"], "har_rv")], ignore_index=True),
              "hole": hole_sensitivity(X, E["walk"]), "coefs": coefficients(X)})
    if verbose:
        print("replication on six pairs ...", flush=True)
    T["replication"], T["replication_boot"], T["replication_spread"], T["replication_pooled"] = replicate(verbose=verbose)
    if verbose:
        print("controls ...", flush=True)
    T["shuffle"] = shuffle_control(verbose=verbose)
    T["truncation"] = truncation_check(X, E["walk"], verbose=verbose)
    lv = []
    for h in HORIZONS:
        W = E["walk"][h]
        t = pd.DataFrame({"h": h, "close": X["__close"], "lowest_low_next_h": X["__close"] * np.exp(X[f"dn{h}"]), "highest_high_next_h": X["__close"] * np.exp(X[f"up{h}"])})
        for nm in ("bots", chosen):
            t[f"{nm}_lower"], t[f"{nm}_upper"] = X["__close"] * np.exp(W[f"{nm}|l"]), X["__close"] * np.exp(W[f"{nm}|u"])
        lv.append(t[(t.index.year >= 2010) & t[f"{chosen}_lower"].notna()].reset_index())
    T["levels"] = pd.concat(lv, ignore_index=True).round(5)
    T["verdict"] = pd.DataFrame([{"key": k, "value": json.dumps(v, default=str)} for k, v in V.items()])
    if write:
        for k, t in T.items():
            t.to_csv(RES / f"{ARM}_{k}.csv", index=False)
        REPORT.write_text(write_report(T, V))
        if verbose:
            print(f"wrote {len(T)} tables to {RES}/{ARM}_*.csv and {REPORT}", flush=True)
    return V, S


# ====================================================================================================== report
def _md(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


def _held(p: float, lo: float, hi: float) -> str:
    return f"{100 * p:.1f} [{100 * lo:.0f}-{100 * hi:.0f}]"


def write_report(T: dict, V: dict) -> str:
    S, BT, ST, SPC, SP = T["scores"], T["boot"], T["states"], T["spread_cells"], T["spread"]
    ch = V["chosen"]
    hn = {5: "5 (1 week)", 21: "21 (1 month)", 63: "63 (3 months)"}

    def sc(c, h, era, col):
        return float(S[(S.candidate == c) & (S.h == h) & (S.era == era)][col].iloc[0])

    def bt(c, h, era):
        r = BT[(BT.candidate == c) & (BT.h == h) & (BT.era == era)].iloc[0]
        return r

    def spread(c, era):
        return 100 * float(SP[(SP.candidate == c) & (SP.era == era)]["mean_spread"].iloc[0])

    L = []
    a = L.append
    a(f"# Arm CA: `{ARM}` - can the lower / upper levels be made narrower and more evenly reliable?")
    a("")
    a(f"Round 11. Code `src/eurusd/arms/{ARM}.py` (`run()`, one process, about eight minutes; `levels(X, h, asof)` gives the chosen candidate's levels). "
      f"Results `experiments/results/arms/{ARM}_*.csv`. The candidate list, the scoring, the selection rule and the pass bar were written into the module docstring "
      "before any candidate was scored. **Candidates: 12** (the limit), the bots' median level included as the baseline. Nothing was re-run with changed settings.")
    a("")
    a("## Verdict (read this first)")
    a("")
    sel = T["selection"].set_index("candidate")
    a(f"**FAIL against the declared bar.** The declared rule (lowest proper score relative to the bots, averaged over the three horizons, on 2010-2017) picked "
      f"**{LABEL[ch]}**: a regression of the next h sessions' range on the 5-, 21-, 63- and 252-session volatility of daily returns, one fit per horizon "
      f"(score {100 * (sel.loc[ch, 'mean_ratio'] - 1):+.1f} % against the bots on 2010-17). On 2018-2026, which the selection never saw:")
    a("")
    rows = []
    for h in HORIZONS:
        b = bt(ch, h, TEST_ERA)
        rows.append({"sessions": hn[h], "bots: score (bp)": f"{sc('bots', h, TEST_ERA, 'score_bp'):.2f}", "chosen: score (bp)": f"{sc(ch, h, TEST_ERA, 'score_bp'):.2f}",
                     "difference": f"{100 * (b['ratio'] - 1):+.1f} %", "95 % interval of the difference (bp)": f"{b['lo']:+.2f} .. {b['hi']:+.2f}",
                     "bots: lower / upper held %": f"{100 * sc('bots', h, TEST_ERA, 'lower_held'):.1f} / {100 * sc('bots', h, TEST_ERA, 'upper_held'):.1f}",
                     "chosen: lower / upper held %": f"{100 * sc(ch, h, TEST_ERA, 'lower_held'):.1f} / {100 * sc(ch, h, TEST_ERA, 'upper_held'):.1f}",
                     "chosen: width vs bots": f"{100 * (sc(ch, h, TEST_ERA, 'width_ratio') - 1):+.1f} %", "independent periods": f"{sc(ch, h, TEST_ERA, 'n_indep'):.0f}"})
    a(_md(pd.DataFrame(rows)))
    a("")
    ok = lambda b: "passes" if b else "FAILS"  # noqa: E731
    n_i = sum(V["clause_i_detail"].values())
    n_ii = sum(V["clause_ii_detail"].values())
    n_iii = sum(0.77 <= v / 100 <= 0.83 for v in V["clause_iii_detail"].values())
    a(f"* (i) better proper score at all three horizons: **{ok(V['clause_i_better_score_all_h'])}** ({n_i} of 3; the three differences are " + ", ".join(f"{100 * (bt(ch, h, TEST_ERA)['ratio'] - 1):+.1f} %" for h in HORIZONS) + ").")
    a(f"* (ii) interval excludes zero at two horizons at least: **{ok(V['clause_ii_interval_excludes_zero_at_2_of_3'])}** ({n_ii} of 3).")
    a(f"* (iii) every level holds 77-83 %: **{ok(V['clause_iii_all_six_within_77_83'])}** ({n_iii} of 6 cells inside; the misses are on the HIGH side: the chosen levels held "
      f"up to {max(V['clause_iii_detail'].values()):.1f} %, i.e. they were too wide, not too narrow). Declared with the bar: an exactly calibrated method would pass this clause only "
      f"{100 * V['noise_chosen']['p_pass_if_exactly_calibrated']:.0f} % of the time (the 63-session holding rate has a sampling error of about "
      f"{V['noise_chosen']['boot_sd_points'][4]:.0f} points on 35 independent periods), so (iii) alone would prove little. The bots' own levels were inside 77-83 % in "
      f"{sum(0.77 <= v / 100 <= 0.83 for v in V['clause_iii_baseline'].values())} of 6 cells.")
    a(f"* (iv) holding rate more even across volatility terciles: **{ok(V['clause_iv_spread_smaller'])}** (average spread {V['spread_chosen_points']:.1f} points against the bots' {V['spread_baseline_points']:.1f}).")
    a("")
    ba = T["bar_all"]
    npass = int(ba["pass"].sum())
    n2 = int(ba["clause_ii_interval_excludes_zero_at_2_of_3"].sum())
    RPv = T["replication_pooled"]

    def pooled(c, era):
        x = RPv[(RPv.candidate == c) & (RPv.era == era)].set_index("h")
        return " / ".join(f"{x.loc[h, 'pooled_rel_diff_pct']:+.1f} %{'*' if x.loc[h, 'excludes_zero'] else ''}" for h in HORIZONS)

    a(f"Descriptive, because only the chosen candidate counts: the same bar applied to each of the eleven non-baseline candidates is passed by {npass}; {n2} have an interval excluding zero "
      "at two horizons (the Garman-Klass, hourly and event versions beat the bots at all three horizons, with an interval excluding zero at 5 sessions only). So this is not the rule "
      "picking the wrong horse: on EUR/USD, nine unseen years confirm none of them.")
    a("")
    a("**In plain words.**")
    a("")
    a("1. NARROWER: **no**. In 2018-26 the chosen levels were "
      + " / ".join(f"{100 * (sc(ch, h, TEST_ERA, 'width_ratio') - 1):+.1f} %" for h in HORIZONS)
      + " wider than the bots' at 5 / 21 / 63 sessions and held more often than 80 %; the proper score, which trades width against misses, is the same to within sampling error.")
    a("2. EVENLY RELIABLE: **partly yes, and this part is solid.** The bots' levels hold too rarely in calm markets and too often in volatile ones "
      f"(spread of the holding rate across volatility terciles {spread('bots', SELECT_ERA):.1f} points in 2010-17, {spread('bots', TEST_ERA):.1f} in 2018-26); every regression-based candidate "
      f"roughly halves that ({LABEL[ch]}: {spread(ch, SELECT_ERA):.1f} and {spread(ch, TEST_ERA):.1f}), on both halves of the EUR/USD sample and on six of six other pairs. "
      "Event weeks and trending years: small gains, section 3.")
    a(f"3. THE WIDER EVIDENCE (descriptive, pooled test added after the primary result): on the six other pairs, where nothing was selected, the chosen candidate's proper score is "
      f"{pooled(ch, '2010-26')} against the bots at 5 / 21 / 63 sessions in 2010-26 and {pooled(ch, TEST_ERA)} in 2018-26 (`*` = interval excludes zero); the Garman-Klass version "
      f"{pooled('har_gk', TEST_ERA)} in 2018-26. So there very probably is a small real gain in the QUALITY of the levels, two to four percent of the proper score, from letting the weight "
      "of today's volatility fall with the horizon. It is not narrower levels, and EUR/USD's own unseen years do not show it.")
    a("")

    # ---- 1. key table
    a("## 1. The plain table: every candidate on the unseen years (2018-26) and on the selection years (2010-17)")
    a("")
    a("`held` = share of sessions on which the period's lowest low stayed above the lower level / highest high below the upper level [95 % Wilson interval on the number of "
      "independent periods = sessions / h]. Width = upper minus lower level in % of price, average over sessions. Proper score = pinball loss at the 20 % / 80 % quantiles, "
      "basis points, lower is better; `vs bots` = relative difference (negative = better than the bots), `*` = paired block-bootstrap 95 % interval excludes zero. "
      "All figures walk-forward, out of sample; same sessions for every candidate.")
    for era in (TEST_ERA, SELECT_ERA):
        a("")
        a(f"**{era}{' (never seen by the selection)' if era == TEST_ERA else ' (the selection era)'}**")
        a("")
        rows = []
        for h in HORIZONS:
            for c in list(CANDS) + ["unscaled"]:
                r = S[(S.candidate == c) & (S.h == h) & (S.era == era)].iloc[0]
                star = ""
                if c != "bots":
                    star = " *" if bool(bt(c, h, era)["excludes_zero"]) else ""
                rows.append({"candidate": LABEL[c] + (" <- chosen" if c == ch else ""), "h": h, "lower held %": _held(r.lower_held, r.lower_lo, r.lower_hi),
                             "upper held %": _held(r.upper_held, r.upper_lo, r.upper_hi), "avg width %": f"{r.avg_width_pct:.2f}", "score bp": f"{r.score_bp:.2f}",
                             "score vs bots": "" if c == "bots" else f"{100 * (r.score_ratio - 1):+.1f} %{star}", "width vs bots": "" if c == "bots" else f"{100 * (r.width_ratio - 1):+.1f} %"})
        a(_md(pd.DataFrame(rows)))
    a("")
    a(f"**The chosen candidate against the baseline, every era** (n = independent periods)")
    a("")
    rows = []
    for h in HORIZONS:
        for era, _, _ in ERAS:
            for c in ("bots", ch):
                r = S[(S.candidate == c) & (S.h == h) & (S.era == era)].iloc[0]
                star = ""
                if c != "bots":
                    star = " *" if bool(bt(c, h, era)["excludes_zero"]) else ""
                rows.append({"candidate": LABEL[c], "h": h, "era": era, "n": r.n_indep, "lower held %": _held(r.lower_held, r.lower_lo, r.lower_hi), "upper held %": _held(r.upper_held, r.upper_lo, r.upper_hi),
                             "both held %": f"{100 * r.both_held:.1f}", "avg width %": f"{r.avg_width_pct:.2f}", "median width %": f"{r.med_width_pct:.2f}", "score bp": f"{r.score_bp:.2f}",
                             "score vs bots": "" if c == "bots" else f"{100 * (r.score_ratio - 1):+.1f} %{star}",
                             "worst year: lower / upper held %": f"{100 * r.worst_year_lower:.0f} ({int(r.worst_year_lower_y)}) / {100 * r.worst_year_upper:.0f} ({int(r.worst_year_upper_y)})"})
    a(_md(pd.DataFrame(rows)))
    a("")
    a("Selection table (2010-17, proper score relative to the bots; the rule takes the lowest mean):")
    a("")
    t = T["selection"].copy()
    t["candidate"] = t["candidate"].map(LABEL)
    for c in (5, 21, 63, "mean_ratio"):
        t[c] = t[c].map(lambda x: f"{x:.3f}")
    a(_md(t.rename(columns={5: "h = 5", 21: "h = 21", 63: "h = 63", "mean_ratio": "mean"})))
    a("")
    a("Reading. On 2010-17 seven candidates are 3-4 % better than the bots and within a point and a half of each other; the rule's pick among them is close to a coin toss. On 2018-26 the same "
      "seven are 0-2 % better at 5 and 21 sessions and indistinguishable from the bots at 63. The only intervals that exclude zero in 2018-26 are at 5 sessions, for the candidates that "
      "use intraday information (Garman-Klass ranges, hourly realised volatility, the event count): about -1.2 to -1.8 %. Direct quantile regression (C7, C8) is the weakest family: "
      "more parameters fitted on overlapping windows, worse out of sample at 63 sessions. Pooling the two sides (C1) is a small free gain (-0.1 to -1.5 % in 2018-26). "
      "The adaptive correction (C9, C10) is IDENTICAL to its base: its step size is chosen each year by past proper score and the choice was always zero (section 7).")
    a("")

    # ---- 2. state dependence
    a("## 2. Where the levels hold: calm and volatile markets")
    a("")
    a("Holding rate (%) by tercile of the 21-session volatility at the decision (cut points from the era's own sessions). `spread` = highest minus lowest tercile. Width in % of price.")
    a("")
    rows = []
    for era in (SELECT_ERA, TEST_ERA):
        for h in HORIZONS:
            for c in ("bots", ch, "unscaled"):
                v = ST[(ST.candidate == c) & (ST.h == h) & (ST.era == era) & (ST.state == "vol tercile")].set_index("class")
                cell = SPC[(SPC.candidate == c) & (SPC.h == h) & (SPC.era == era)].iloc[0]
                rows.append({"era": era, "h": h, "candidate": LABEL[c], "lower: calm / middle / volatile": " / ".join(f"{100 * v.loc[k, 'lower_held']:.1f}" for k in ("low", "mid", "high")),
                             "spread": f"{100 * cell.spread_lower:.1f}", "upper: calm / middle / volatile": " / ".join(f"{100 * v.loc[k, 'upper_held']:.1f}" for k in ("low", "mid", "high")),
                             "spread ": f"{100 * cell.spread_upper:.1f}", "width: calm / middle / volatile": " / ".join(f"{v.loc[k, 'avg_width_pct']:.2f}" for k in ("low", "mid", "high")),
                             "periods per tercile": v.loc["low", "n_indep"]})
    a(_md(pd.DataFrame(rows)))
    a("")
    t = SP.pivot(index="candidate", columns="era", values="mean_spread").reindex(list(CANDS) + ["unscaled"])[[e for e, _, _ in ERAS]]
    t = (100 * t).round(1).reset_index()
    t["candidate"] = t["candidate"].map(LABEL)
    a("Average spread over the six cells (3 horizons x 2 levels), points:")
    a("")
    a(_md(t))
    a("")
    v = ST[(ST.state == "vol tercile") & (ST.era == TEST_ERA)].set_index(["candidate", "h", "class"])
    a("What happens: with today's volatility times a constant, the bots' level is too tight when the market is quiet (volatility drifts back up) and too wide when it is "
      "volatile. The regression gives the long-run level a weight, so in 2018-26 the chosen levels were "
      + " / ".join(f"{100 * (v.loc[(ch, h, 'low'), 'avg_width_pct'] / v.loc[('bots', h, 'low'), 'avg_width_pct'] - 1):+.0f} %" for h in HORIZONS)
      + " wider than the bots' in the calm third and "
      + " / ".join(f"{100 * (v.loc[(ch, h, 'high'), 'avg_width_pct'] / v.loc[('bots', h, 'high'), 'avg_width_pct'] - 1):+.0f} %" for h in HORIZONS)
      + " in the volatile third (5 / 21 / 63 sessions). The calm third's holding rate rises from "
      f"{100 * min(v.loc[('bots', h, 'low'), c] for h in HORIZONS for c in ('lower_held', 'upper_held')):.0f}-{100 * max(v.loc[('bots', h, 'low'), c] for h in HORIZONS for c in ('lower_held', 'upper_held')):.0f} % to "
      f"{100 * min(v.loc[(ch, h, 'low'), c] for h in HORIZONS for c in ('lower_held', 'upper_held')):.0f}-{100 * max(v.loc[(ch, h, 'low'), c] for h in HORIZONS for c in ('lower_held', 'upper_held')):.0f} %; "
      "the price is the extra width in calm markets, which in the low-volatility years since 2018 made the levels wider on average and over-reliable at 63 sessions.")
    a("")
    cf = T["coefs"]
    last = cf[cf.test_year == cf.test_year.max()].set_index("h")
    bcols = [c for c in cf.columns if c.startswith("b_") and c != "b_const"]
    a("What the chosen model is, in one number per horizon: the bots move their level one for one with today's volatility at every horizon. In the fitted regression the level moves by "
      + " / ".join(f"{float(last.loc[h, bcols].sum()):.2f}" for h in HORIZONS)
      + f" percent for one percent of volatility at 5 / 21 / 63 sessions (sum of the slopes, fold {int(cf.test_year.max())}; `{ARM}_coefs.csv`); the rest is a fixed long-run level. "
      "The 63-session volatility carries the largest weight at every horizon, the 5-session one almost none, and the 252-session one a small NEGATIVE weight, so the long-run anchor "
      "is the constant fitted on all history since 2004, which is why the levels came out too wide in the quiet years since 2018.")
    a("")

    # ---- 3. events, trends, worst years
    a("## 3. Event weeks, trending markets, worst years")
    a("")
    a("**Weeks with a scheduled FOMC statement, ECB decision, US payrolls or US CPI inside the 5-session window** against the other weeks (holding rate %, 5 sessions; "
      "event weeks are about 59 % of all weeks):")
    a("")
    rows = []
    for era in ("2010-26", TEST_ERA):
        for c in ("bots", ch, "har_rv", "har_rv_ev"):
            v = ST[(ST.candidate == c) & (ST.h == 5) & (ST.era == era) & (ST.state == "scheduled events")].set_index("class")
            rows.append({"era": era, "candidate": LABEL[c], "lower: event week / other": f"{100 * v.loc['event week', 'lower_held']:.1f} / {100 * v.loc['other week', 'lower_held']:.1f}",
                         "upper: event week / other": f"{100 * v.loc['event week', 'upper_held']:.1f} / {100 * v.loc['other week', 'upper_held']:.1f}",
                         "width: event week / other": f"{v.loc['event week', 'avg_width_pct']:.2f} / {v.loc['other week', 'avg_width_pct']:.2f}",
                         "periods: event / other": f"{v.loc['event week', 'n_indep']:.0f} / {v.loc['other week', 'n_indep']:.0f}"})
    a(_md(pd.DataFrame(rows)))
    a("")
    a("The event effect is real and the bots ignore it: their one-week levels hold 2-8 points less often in event weeks. The chosen candidate does not use the calendar and keeps "
      "the same gap. The event candidate (C6, not chosen) makes event-week levels 5-7 % wider than the others; it closes most of the gap for the lower level and about half of it for the upper, "
      "and it had the best 5-session score of all candidates in 2018-26 (-1.8 %, interval excluding zero). At 21 and 63 sessions every window contains several events, so there is nothing to adjust.")
    a("")
    a("**Trending markets.** Ex ante (tercile of the absolute 63-session move in units of its volatility at the decision; holding rate %, 2010-26):")
    a("")
    rows = []
    for h in HORIZONS:
        for c in ("bots", ch):
            v = ST[(ST.candidate == c) & (ST.h == h) & (ST.era == "2010-26") & (ST.state == "trend tercile")].set_index("class")
            rows.append({"h": h, "candidate": LABEL[c], "lower: flat / middle / trending": " / ".join(f"{100 * v.loc[k, 'lower_held']:.1f}" for k in ("low", "mid", "high")),
                         "upper: flat / middle / trending": " / ".join(f"{100 * v.loc[k, 'upper_held']:.1f}" for k in ("low", "mid", "high"))})
    a(_md(pd.DataFrame(rows)))
    a("")
    a("**Worst single calendar year, 2010-26** (holding rate %, year in brackets; a year has 12 independent 21-session periods and 4 independent 63-session periods, so these are noisy):")
    a("")
    rows = []
    for c in list(CANDS):
        r = {"candidate": LABEL[c]}
        for h in HORIZONS:
            x = S[(S.candidate == c) & (S.h == h) & (S.era == "2010-26")].iloc[0]
            r[f"h = {h}: lower / upper"] = f"{100 * x.worst_year_lower:.0f} ({int(x.worst_year_lower_y)}) / {100 * x.worst_year_upper:.0f} ({int(x.worst_year_upper_y)})"
        rows.append(r)
    a(_md(pd.DataFrame(rows)))
    a("")
    a("A strongly trending year still breaks every method. The regression candidates are less badly broken (63 sessions: the worst year improves from 33 / 39 % to about 46 / 49 %; "
      "21 sessions: 58 / 63 % to 64 / 67 %) mainly because two of the worst years (2014 and 2020) started from the lowest volatility of the sample, where their levels are wider "
      "(2014: 63-session lower level held 33 -> 46 %; 2020 upper 39 -> 53 %; 2017, which started from average volatility: 41 -> 49 %). That is the same effect as section 2, "
      "not a trend remedy. The remedy that was meant for trends, the adaptive correction, does repair the holding rate after the fact but costs more in width than it saves in misses (section 7).")
    a("")

    # ---- 4. matched reliability
    a("## 4. Width at matched reliability")
    a("")
    a("Declared device: each candidate's levels are rescaled, side by side, so that its model holds exactly 80 % on its own training rows; then the out-of-sample holding and width are compared "
      f"({TEST_ERA}). The last column is DESCRIPTIVE and was added after the primary result: the width a candidate would need to hold exactly 80 % on each side within {TEST_ERA} itself.")
    a("")
    EX = T["expost"]
    rows = []
    for h in HORIZONS:
        for c in list(CANDS) + ["unscaled"]:
            r = S[(S.candidate == c) & (S.h == h) & (S.era == TEST_ERA)].iloc[0]
            e = EX[(EX.candidate == c) & (EX.h == h) & (EX.era == TEST_ERA)].iloc[0]
            rows.append({"candidate": LABEL[c], "h": h, "matched: lower / upper held %": f"{100 * r.lower_held_matched:.1f} / {100 * r.upper_held_matched:.1f}",
                         "matched: avg width %": f"{r.avg_width_matched_pct:.2f}", "matched width vs bots": "" if c == "bots" else f"{100 * (r.width_matched_ratio - 1):+.1f} %",
                         "matched score vs bots": "" if c == "bots" else f"{100 * (r.score_matched_ratio - 1):+.1f} %",
                         "ex-post 80 % width vs bots (descriptive)": "" if c == "bots" else f"{100 * (e.expost_width_ratio - 1):+.1f} %"})
    a(_md(pd.DataFrame(rows)))
    a("")
    a("Two things to read from this. First, matching reliability on the training window does not match it out of sample: the regression candidates then held 80-86 % in 2018-26 and were "
      "2-11 % wider, the bots 76-84 %. Second, the ex-post column says the regression candidates would need 2-5 % LESS width than the bots to reach exactly 80 % in 2018-26, "
      "but the same column 'prefers' the level with no volatility scaling at all (-3 to -8 %), which is the worst level on every honest measure. Average width at a given overall holding rate "
      "rewards being tight when volatility is high and failing there; it is not a measure of quality on its own. The proper score is, and it shows no confirmed gain.")
    a("")

    # ---- 5. replication
    R, RB, RSP, RP = T["replication"], T["replication_boot"], T["replication_spread"], T["replication_pooled"]
    a("## 5. Six other pairs, nothing re-tuned")
    a("")
    a(f"The same 100 bots' median and the chosen candidate ({LABEL[ch]}) on each pair's own sessions (arm BA's cached frames), same walk-forward. `score vs bots` per horizon "
      "(`*` = block-bootstrap interval excludes zero); a pair IMPROVES by the declared reading if the mean of the three ratios is below 1 in 2010-26. On these pairs nothing was selected, "
      "so all of 2010-26 is out of selection.")
    a("")
    rows = []
    nimp = 0
    for p in PAIRS:
        r = {"pair": p[:3].upper() + "/" + p[3:].upper()}
        for era in ("2010-26", TEST_ERA):
            x = R[(R.pair == p) & (R.candidate == ch) & (R.era == era)].set_index("h")
            b = RB[(RB.pair == p) & (RB.candidate == ch) & (RB.era == era)].set_index("h")
            r[f"{era}: score vs bots, h = 5 / 21 / 63"] = " / ".join(f"{100 * (x.loc[h, 'score_ratio'] - 1):+.1f} %{'*' if b.loc[h, 'excludes_zero'] else ''}" for h in HORIZONS)
            if era == "2010-26":
                m = float(x["score_ratio"].mean())
                nimp += int(m < 1)
                r["improves"] = "yes" if m < 1 else "NO"
            r[f"{era}: lower / upper held % (h = 5 / 21 / 63)"] = " ; ".join(f"{100 * x.loc[h, 'lower_held']:.0f} / {100 * x.loc[h, 'upper_held']:.0f}" for h in HORIZONS)
            r[f"{era}: width vs bots"] = " / ".join(f"{100 * (x.loc[h, 'width_ratio'] - 1):+.1f} %" for h in HORIZONS)
            r[f"{era}: tercile spread, bots -> chosen"] = (f"{100 * float(RSP[(RSP.pair == p) & (RSP.candidate == 'bots') & (RSP.era == era)]['mean_spread'].iloc[0]):.1f} -> "
                                                            f"{100 * float(RSP[(RSP.pair == p) & (RSP.candidate == ch) & (RSP.era == era)]['mean_spread'].iloc[0]):.1f}")
        rows.append(r)
    a(_md(pd.DataFrame(rows)))
    a("")
    nstar = {era: int(RB[(RB.candidate == ch) & (RB.era == era) & RB.pair.isin(list(PAIRS))]["excludes_zero"].sum()) for era in ("2010-26", TEST_ERA)}
    nsp = {era: sum(float(RSP[(RSP.pair == p) & (RSP.candidate == ch) & (RSP.era == era)]["mean_spread"].iloc[0]) < float(RSP[(RSP.pair == p) & (RSP.candidate == "bots") & (RSP.era == era)]["mean_spread"].iloc[0])
                    for p in PAIRS) for era in ("2010-26", TEST_ERA)}
    a(f"**{nimp} of 6 pairs improve** by the declared reading (2010-26). The interval excludes zero in {nstar['2010-26']} of 18 pair-horizons in 2010-26 and in {nstar[TEST_ERA]} of 18 in 2018-26. "
      f"The holding rate is more even across volatility terciles on {nsp['2010-26']} of 6 pairs in 2010-26 and {nsp[TEST_ERA]} of 6 in 2018-26.")
    a("")
    a("Descriptive, added after the primary result: the six pairs pooled into one test (each pair's loss difference divided by its bots' mean loss, averaged across pairs by date, one block bootstrap):")
    a("")
    rows = []
    for c in (ch, "har_gk", "har_rv", "bots_pooled", "qr", "aci_bots"):
        r = {"candidate": LABEL[c]}
        for era in ("2010-26", SELECT_ERA, TEST_ERA):
            x = RP[(RP.candidate == c) & (RP.era == era)].set_index("h")
            r[f"{era}: h = 5 / 21 / 63"] = " / ".join(f"{x.loc[h, 'pooled_rel_diff_pct']:+.1f} %{'*' if x.loc[h, 'excludes_zero'] else ''}" for h in HORIZONS)
        rows.append(r)
    a(_md(pd.DataFrame(rows)))
    a("")
    x = RP[(RP.candidate == ch) & (RP.era == TEST_ERA)].set_index("h")
    a("So across the other pairs the regression levels score better than the bots' in both halves. For the chosen candidate in 2018-26: "
      + " / ".join(f"{x.loc[h, 'pooled_rel_diff_pct']:+.1f} % [{x.loc[h, 'lo_pct']:+.1f} .. {x.loc[h, 'hi_pct']:+.1f}]" for h in HORIZONS)
      + " at 5 / 21 / 63 sessions; for the versions fed with intraday ranges (C4, C5) the interval excludes zero at all three horizons. The gain is two to four percent of the score: visible in "
      "the pooled data, too small to see on one pair in nine years, and it is NOT narrower levels (the widths are within a few percent of the bots' in either direction). This pooled test was "
      "not declared and eleven candidates were looked at, so it is supporting evidence, not a pass. EUR/USD 2018-26 is the weakest of the seven cases, the opposite of the usual pattern in this project. "
      f"The adaptive correction (C9), which the yearly rule switched on at times on AUD, GBP, CAD and JPY, made the pooled score worse: {pooled('aci_bots', SELECT_ERA)} in 2010-17.")
    a("")

    # ---- 6. controls
    SH, TR, HO = T["shuffle"], T["truncation"], T["hole"]
    a("## 6. Controls")
    a("")
    g = SH.groupby(["draw", "candidate"])[["ratio_to_unscaled", "vol_tercile_spread"]].mean().reset_index()
    real = g[g.draw == 0].set_index("candidate")
    shf = g[g.draw > 0].groupby("candidate").agg(mean=("ratio_to_unscaled", "mean"), lo=("ratio_to_unscaled", "min"), hi=("ratio_to_unscaled", "max"))
    a(f"* **Shuffled order** (sessions of 2003-26 permuted, each keeps its own return, high, low and realised variance; frame rebuilt; {int(SH.draw.max())} draws; score relative to the level with "
      f"no volatility scaling, mean of the three horizons, 2010-26). Real order: bots {real.loc['bots', 'ratio_to_unscaled']:.3f}, chosen {real.loc[ch, 'ratio_to_unscaled']:.3f}. "
      f"Shuffled: bots {shf.loc['bots', 'mean']:.3f} ({shf.loc['bots', 'lo']:.3f}-{shf.loc['bots', 'hi']:.3f}), chosen {shf.loc[ch, 'mean']:.3f} ({shf.loc[ch, 'lo']:.3f}-{shf.loc[ch, 'hi']:.3f}). "
      "With the volatility information destroyed the advantage is gone: the regression learns that the gauges say nothing and falls back to the unscaled level; the bots, which must "
      "scale by a gauge that is now noise, become 3-6 % worse than no scaling.")
    a(f"* **No future data.** For {TR.session.nunique()} random sessions of 2010-26 the hourly bars and the daily frame were cut off at that session's close, the frame rebuilt from scratch "
      f"(`bots.build` and this module) and the levels of the bots, the chosen candidate and `levels()` recomputed: {len(TR)} levels, largest difference from the full run "
      f"{TR.abs_diff.max():.1e} in log distance.")
    rc = T["reconcile"]
    a(f"* **Reconciliation (step 1).** My scoring of the bots' median level reproduces all {len(rc)} rows of `bots_levels.csv` (holding rates, widths, worst years, volatility halves); "
      f"largest difference {rc['max_abs_diff'].max():.0e}. The generic frame used for the other pairs reproduces `bots.build()`'s targets and gauges on EUR/USD exactly except in the first "
      "63 sessions of 2003 (the product's frame reaches back to 1999 closes there); the baseline's scores differ by at most 0.15 bp between the two frames.")
    x = HO[(HO.candidate == ch)].set_index(["h", "era"])
    a("* **February-July 2023 data hole** (44 % of the 2023 sessions have fewer than 20 hourly bars; highs and lows are understated for every candidate alike). Without decision "
      "sessions whose last 21 sessions or forward window touch a thin session, the chosen candidate's score against the bots in 2018-26 is "
      + " / ".join(f"{100 * (x.loc[(h, TEST_ERA), 'ratio_clean'] - 1):+.1f} %" for h in HORIZONS) + " (all sessions: "
      + " / ".join(f"{100 * (x.loc[(h, TEST_ERA), 'ratio_all'] - 1):+.1f} %" for h in HORIZONS) + "). The sign at 63 sessions depends on the hole; the size is nil either way.")
    a("")

    # ---- 7. adaptive
    AF = T["aci_fixed"]
    a("## 7. The adaptive (conformal-style) correction: why C9 equals C0")
    a("")
    a("Descriptive: the correction on the bots' level at each fixed step size (the declared rule chooses among these each year by past proper score; on EUR/USD it chose 0 in every "
      "year from 2010, at every horizon, so C9 = C0 and C10 = C5 exactly).")
    a("")
    rows = []
    for h in HORIZONS:
        for g0 in GRID:
            r = {"h": h, "step gamma0": g0}
            for era in ("2010-26", TEST_ERA):
                x = AF[(AF.base == "bots") & (AF.h == h) & (AF.gamma0 == g0) & (AF.era == era)].iloc[0]
                x0 = AF[(AF.base == "bots") & (AF.h == h) & (AF.gamma0 == 0.0) & (AF.era == era)].iloc[0]
                r[f"{era}: lower / upper held %"] = f"{100 * x.lower_held:.1f} / {100 * x.upper_held:.1f}"
                r[f"{era}: width vs none"] = f"{100 * (x.avg_width_pct / x0.avg_width_pct - 1):+.1f} %"
                r[f"{era}: score vs none"] = f"{100 * (x.score_bp / x0.score_bp - 1):+.1f} %"
                r[f"{era}: worst year lower / upper %"] = f"{100 * x.worst_year_lower:.0f} / {100 * x.worst_year_upper:.0f}"
            rows.append(r)
    a(_md(pd.DataFrame(rows)))
    a("")
    pos = AF[(AF.base == "bots") & (AF.gamma0 > 0) & AF.era.isin(["2010-17", TEST_ERA])].merge(
        AF[(AF.base == "bots") & (AF.gamma0 == 0)][["h", "era", "avg_width_pct", "score_bp"]], on=["h", "era"], suffixes=("", "_0"))
    wr, sr = 100 * (pos.avg_width_pct / pos.avg_width_pct_0 - 1), 100 * (pos.score_bp / pos.score_bp_0 - 1)
    a("The correction does what it promises for the average: both levels end within a point or two of 80 % and the worst year is less bad (21 sessions: 58 / 63 % to 70 / 70 % at the "
      f"largest step). But it buys that with width: levels {wr.min():+.0f} to {wr.max():+.0f} % wider and a proper score {sr.min():+.0f} to {sr.max():+.0f} % WORSE, at every step size, every horizon "
      "and in both halves of the sample. A broken level says little about whether the next one will break; widening after misses mostly widens after the move is over. "
      "As a remedy for trending years it fails the honest test.")
    a("")

    # ---- 8. count, 9. suspicious, 10. gain
    a("## 8. Candidate count: 12")
    a("")
    a("C0 bots (baseline) | C1 bots, sides pooled | C2 one gauge with fitted slope | C3 HAR daily returns (chosen) | C4 HAR Garman-Klass | C5 HAR hourly realised volatility | "
      "C6 C5 + scheduled events | C7 direct quantile regression | C8 quantile regression with down / up semi-volatility | C9 adaptive on C0 | C10 adaptive on C5 | C11 average of C3, C4, C5, C7. "
      "Not candidates: the unscaled reference, the matched-reliability rescale (declared device), the controls. Descriptive and added after the primary result, labelled so where they "
      "appear: the bar applied to the non-chosen candidates, the ex-post 80 % width, the fixed step sizes of the adaptive correction, the pooled six-pair test, the other candidates on the six pairs.")
    a("")
    a("## 9. Anything suspicious")
    a("")
    a("* **The pick is noisy.** Seven candidates were within one point of each other on 2010-17. The rule picked the plainest HAR (daily returns); on 2018-26 the Garman-Klass and "
      "event versions did better at 5 sessions. Re-picking by the 2018-26 score would be hindsight and I have not done it.")
    a("* **Clause (iii) of my bar is tight** (an exactly calibrated method passes 16-19 % of the time). It is reported as declared. It is not what decides the verdict: clauses (i) and (ii) fail on their own.")
    a("* **The pooled six-pair test is post hoc.** It was added after the EUR/USD result and eleven candidates were looked at on the pairs. Its strength is consistency (every regression "
      "candidate, every horizon, both halves, six of six pairs), not a p-value. The six pairs share the dollar and the same calendar years, so they are far from six independent confirmations.")
    a("* **Why the regression levels were over-wide in 2018-26.** Their constants and long-run anchor come from an expanding window that starts in 2004 and contains 2008-12; "
      "volatility since 2018 has been lower than that history, so shrinking towards the long-run level over-shoots (63 sessions: 84-85 % held). Two thirds of the bots forget after 5 or 10 "
      "years and do not have this problem. A rolling window is the obvious next variant; it is NOT tested here (it would be a thirteenth candidate chosen after seeing the result).")
    a("* **Average width is not a quality measure** (section 4): the unscaled level looks 'narrowest at 80 %' ex post. Any claim of 'x % narrower at the same reliability' made from "
      "average width should be distrusted, this report's included; the proper score is the test.")
    a("* **The yearly holding rates swing between 33 % and 100 %** for every method at 63 sessions (`sharper_levels_years.csv`). 2018-26 has 35 independent 63-session periods; nothing "
      "at that horizon can be confirmed or refuted on one pair in nine years.")
    a("* **Event calendar.** The FOMC file lists some two-day meetings twice (rows within two days dropped; 2015, 2024 and 2025 still show one to three extra dates); payroll dates before "
      "2010 are a first-Friday rule; CPI dates do not exist before 2010 and are not in the regression. The event result of section 3 rests on 2010-26 dates, which are clean.")
    a("* **Data hole 2023** and bid-quote ranges: as in arm BA; they affect every candidate alike (section 6).")
    a("* On EUR/USD the product's own frame was used (gauges reach back to 1999 closes); on the other pairs the gauges start in 2003. Difference on EUR/USD: at most 0.15 bp of score.")
    a("")
    a("## 10. What a user gains")
    a("")
    cal = ST[(ST.state == "vol tercile") & (ST.era == "2010-26")].set_index(["candidate", "h", "class"])
    wq = {k: [100 * (cal.loc[(ch, h, k), 'avg_width_pct'] / cal.loc[('bots', h, k), 'avg_width_pct'] - 1) for h in HORIZONS] for k in ("low", "high")}
    a("**No method makes the levels narrower at the same 80 % reliability by a margin that survives the unseen years.** On EUR/USD 2018-26 the chosen levels were "
      f"{100 * (sc(ch, 5, TEST_ERA, 'width_ratio') - 1):+.0f} / {100 * (sc(ch, 21, TEST_ERA, 'width_ratio') - 1):+.0f} / {100 * (sc(ch, 63, TEST_ERA, 'width_ratio') - 1):+.0f} % "
      "wider at one week / one month / three months, held a few points more often than 80 %, and scored within one and a half percent of the bots' levels, not distinguishable from zero. "
      "By the declared bar the bots' median level stays the product.")
    a("")
    a("What a user could gain, if the owner wants it, is EVENNESS rather than narrowness, and that part held in both halves of the sample and on all six other pairs: "
      f"in calm markets (lowest third of volatility, 2010-26) the bots' one-month levels held {100 * cal.loc[('bots', 21, 'low'), 'lower_held']:.0f} / {100 * cal.loc[('bots', 21, 'low'), 'upper_held']:.0f} % "
      f"and in volatile markets {100 * cal.loc[('bots', 21, 'high'), 'lower_held']:.0f} / {100 * cal.loc[('bots', 21, 'high'), 'upper_held']:.0f} %; the regression levels held "
      f"{100 * cal.loc[(ch, 21, 'low'), 'lower_held']:.0f} / {100 * cal.loc[(ch, 21, 'low'), 'upper_held']:.0f} % and {100 * cal.loc[(ch, 21, 'high'), 'lower_held']:.0f} / {100 * cal.loc[(ch, 21, 'high'), 'upper_held']:.0f} %. "
      f"They do it by being {min(wq['low']):.0f}-{max(wq['low']):.0f} % wider when the market is quiet and {-max(wq['high']):.0f}-{-min(wq['high']):.0f} % narrower when it is volatile, "
      "and on the six other pairs that re-allocation is worth two to four percent of the proper score (descriptive). If the owner wants that, the honest way in is a shadow run: publish "
      f"`{ARM}.levels()` next to the bots' levels in the paper forward test and score both; the history has no unseen years left to confirm it on.")
    a("")
    a("Two caveats belong on the product's levels as they are: (a) 'holds 8 times in 10' is an average; in a quiet market it is nearer 7.5 in 10 and in a volatile one 8.5 in 10; "
      "(b) one-week levels hold 2-8 points less often in a week with a Fed or ECB decision, payrolls or CPI. A strongly trending year breaks every version "
      "(a three-month level held 33-49 % in the worst year), and widening after misses does not help.")
    a("")
    return "\n".join(L)


if __name__ == "__main__":
    run()
