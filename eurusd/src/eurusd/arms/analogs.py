"""Arm U ("analogs"): 'history does not repeat, it rhymes' - nearest-neighbour / kernel ANALOG forecasting of the
EUR/USD direction over 21 / 42 / 63 sessions (round 6).

Owner's intuition: "when the economy was like this, rates like that, unemployment like that - what did EUR/USD do
next?"  Describe today by a small state vector, find the past dates whose state was most similar, forecast from
what followed them. A different model class from everything tried so far (linear scores, trees, logistic), and
transparent: the analog dates can be listed.

EVERYTHING IN THIS DOCSTRING DOWN TO "ADDED AFTER THE FIRST RUN" WAS WRITTEN BEFORE ANY RESULT WAS COMPUTED.

Frame
  The continuous daily frame of arm O (`swing.load_prices`): synthetic DEM euro 1975-98 (robustness only), Fed H.10
  noon 1999-2002, feature-store NY-close sessions 2003+ (identical index to the store, so every 2003+ number is on
  the sessions of arm N). Forward outcome over h sessions = log return of the close h sessions ahead.
  MAIN analog library = sessions from 1999-01-04. LONG library (clearly labelled diagnostic) = from 1990-01-01, i.e.
  nine years of the synthetic DEM euro added, for the states whose inputs exist then.

State vectors (defined from economic reasoning; a session enters as decision date or as analog only when every
dimension is known). Every input is what was public the calendar day before the session's closing date.
  A  policy / rates (7): Fed phase and ECB phase (-1 cutting, 0 hold, +1 hiking: `fed_dir3`, `ecb_dir3` of
     data/macro/policy_state.csv, the causal phases of arm T); policy gap = ECB deposit rate - Fed target (the
     project's standing definition) and its 126-session change; US 2y - Fed target; EA - US 2y spread and its
     63-session change. The euro-area AAA 2y yield starts 2004-09-06; before that it is PROXIED by
     3m interbank + 0.18 x (German 10y - 3m interbank) (FRED monthly averages, 45-day lag, the maturity-linear
     interpolation (2 - 0.25) / (10 - 0.25)), shifted by the mean gap to the AAA 2y over its first 250 sessions
     (2004-09 .. 2005-08, i.e. before the first test year). Flagged as a proxy everywhere.
  B  macro (8): US CPI y/y and its 6-month change, euro-area HICP y/y and its 6-month change, US unemployment
     rate and its 6-month change, euro-area unemployment rate and its 6-month change. Publication lags of arm T:
     reference-month end + 21 days (US CPI, US unemployment, HICP; US shutdown months 2025-09..11 not before
     2026-01-31), + 35 days (euro-area unemployment); a value older than 150 days is missing. Latest-vintage data
     (revision risk as documented by arm T; CPI and unemployment rates are lightly revised).
  C  market (7): EUR/USD 63- and 252-session log return, log distance from the 200-session average, percentile of
     the 21-session close-to-close realised volatility within the trailing 1260 sessions, log VIX, DAX minus
     S&P 500 63-session return (arm O's `eqrel63`; S&P 500 before 2003 from Yahoo ^GSPC, new file), 126-session
     log change of Brent. Other markets' closes lagged one calendar day.
  D  positioning (2): cot_z52 (CFTC non-commercial net / open interest, 52-week z, report date + 6 days) and its
     65-session (13-week) change.
  E  union of A-D (24 dimensions) standardised and reduced to its first 4 principal components, loadings fitted on
     the training window only (4 fixed in advance from the "3-5" of the brief; unwhitened scores).
  F  the three inputs of the agreement rule as a state (3): cot_z52, d_spread2y_20 (store) and the house macro score
     (weak_signals t-stat weights). For a decision in year Y the score of EVERY session (decision and analogs) uses
     the weights fitted on sessions whose 1-session label is known before Y - so the library scores are in-sample
     fitted (to next-day returns), which can only flatter the analog probability; noted wherever F is shown.
  Standardisation: mean and sd of each dimension over the library sessions before 1 January of the decision year
  (yearly expanding, never the test year), z clipped at +-5. PCA and the Mahalanobis covariance (shrunk 10 % towards
  the identity) come from the same window.

Analogs
  For a decision at session t the eligible analogs are the library sessions j <= t - 63 (so that the 21-, 42- and
  63-session outcome of every analog is known at t and the analog is not the current episode) with a complete state.
  A forecast is made only when at least 1260 sessions (five years) are eligible.
  The k nearest (Euclidean on the standardised state; Mahalanobis as a diagnostic) are chosen greedily with a minimum
  separation of 21 sessions between chosen analogs: take the nearest, block the 20 sessions either side, repeat.
  The first 20 of the 40 are the k = 20 set. NOTE (deviation from the yearly protocol, as specified by the lead):
  the library grows daily up to t - 63; only the standardisation is frozen per year. A strict-protocol variant
  (library frozen at t0(Y) - 63 for the whole year Y) is reported for comparison.
  Forecast: P(up over h) = share of the k analogs followed by a rise over h in {21, 42, 63} sessions; analog mean
  return. Call = sign(P - 0.5); P = 0.5 exactly is no call. Kernel version (diagnostic): all eligible sessions
  weighted by exp(-d^2 / 2b^2), b = distance of the 20th chosen analog.
  Independent episodes: the chosen analog dates are sorted and a new EPISODE starts when more than 63 sessions
  separate two consecutive ones. n_epi is reported next to every probability; the episode-level probability gives
  each episode one vote.

Evaluation (Round 5 addendum), test years 2006-2026 wherever a state can forecast (F: 2010+)
  * standalone accuracy at 21 / 42 / 63 sessions on the weekly grid of arm N (every 5th store session), on the
    monthly clock (last session of each month) and on the greedy non-overlapping stream (arm N's `seq_idx`; plain
    Wilson interval; the stream for 2010-26 / 2016-26 / 2023-26 / 2010-15 starts in 2010 as in arm N, the stream for
    2006-26 / 2006-15 starts in 2006). Weekly / monthly intervals use arm N's conservative effective n.
  * calibration of the analog probability on the weekly grid: reliability table, Brier score against always-50 % and
    against the library base rate.
  * near-unanimous analogs: accuracy and decisions per year when max(P, 1 - P) >= 0.70 / 0.80.
  * EXTRA VOTE on the agreement rule (rebuilt with arm T's `_context`, reconciled with arm N first): (a) agreement
    rule AND analog call agrees, against the agreement rule alone; (b) analog calls when the three old signals do
    not agree; (c) paired weekly difference, circular block bootstrap.
  * timing placebo: the analog call series shifted by +63 and +126 sessions.
  * daily incremental test against combine(["weak_signals", "regime_trend"], "EW").
Honesty checks specific to analogs
  (i) number of independent episodes behind the forecasts (above);
  (ii) distance must matter: the k FARTHEST eligible sessions (same thinning), k RANDOM eligible sessions (5 draws)
       and the library base rate must do worse than the nearest;
  (iii) shuffled outcomes (the outcomes attached to the analog sessions are permuted);
  (iv) look-ahead controls: analogs allowed from the future with the 63-session embargo, and with no embargo at all
       (adjacent sessions, whose outcome windows overlap the target): accuracy must jump;
  plus the correlation of every state dimension with the forward returns (no label in disguise) and a +21-session
  stale state.

CANDIDATE RULES (12): the 21-session call sign(P21 - 0.5) of state {A, B, C, D, E, F} x k {20, 40}, Euclidean,
  plain share of analogs, main library. The same (state, k) rule at 42 and 63 sessions is reported next to it as the
  rule's record at the other horizons (strict count 36). Mahalanobis, kernel, long-library, unanimity cells and all
  controls are diagnostics, never selected from.
SELECTION RULE (given by the lead): final = the candidate with the highest LOWER Wilson bound of its 2006-2015
  non-overlapping 21-session accuracy among candidates with at least 6 decisions a year there (decisions per year
  measured from the first session the rule can forecast). The full record of the pick is reported whatever it shows.
Extra-vote form of every candidate: "agreement rule AND analog call agrees" (dense signal). Round 5 bar: gain
  >= 3 points at 21 and 42 sessions (non-overlapping) in both 2010-26 and 2016-26 with >= 6 decisions a year, not
  worse in 2023-26, timing placebo loses at least half of the gain.
Daily stream of the final rule: weekly tranches (a call every 5th session, held 21 sessions, weight 1/5 each, so
  |position| <= 1) through wf.pnl_from_positions at 1.2 pips (0.6 as sensitivity).

`explain(date=None)`: for the latest session (or the last one closing on or before `date`) the nearest analog dates
  of every state, what EUR/USD did after each over 21 / 42 / 63 sessions and the resulting probabilities.

ADDED AFTER THE FIRST RUN: see reports/arm_analogs.md, "Protocol notes" (nothing there changes the selection).
"""
from __future__ import annotations

import json
import math
import pickle
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.arms import policy_cycle as PC  # noqa: E402
from eurusd.arms import selective as S  # noqa: E402
from eurusd.arms import swing as SW  # noqa: E402
from eurusd.wf import pnl_from_positions, report  # noqa: E402

MACRO = ROOT / "data" / "macro"
CROSS = ROOT / "data" / "processed" / "cross"
RES = ROOT / "experiments" / "results" / "arms"
REPORTS = ROOT / "reports"
ARM = "analogs"
N_ARMS = 12

HORIZONS = (21, 42, 63)
KS = (20, 40)
KMAX = 40
K_KERNEL = 20
SEP = 21                    # minimum separation between chosen analogs (sessions)
EMBARGO = 63                # analogs must be at least this many sessions before the decision
EPI_GAP = 63                # a new episode starts when consecutive chosen analogs are further apart than this
MIN_LIB = 1260              # eligible analog sessions needed before a forecast is made
N_PC = 4
CLIP = 5.0
STEP = S.STEP               # weekly grid = every 5th store session
TEST_YEARS = list(range(2006, 2027))
PRE_YEARS = list(range(1996, 2006))          # other-era replication of the long-library variants
LIB_START = {"main": pd.Timestamp("1999-01-04"), "long": pd.Timestamp("1990-01-01")}
PERIODS_2010 = (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026), ("2010-15", 2010, 2015))
PERIODS_2006 = (("2006-26", 2006, 2026), ("2006-15", 2006, 2015))
PERIODS_PRE = (("1997-05", 1997, 2005),)
ALL_PERIODS = PERIODS_2006 + PERIODS_2010
PLACEBO_SHIFTS = (63, 126)
MIN_DEC_PER_YEAR = 6.0
UNANIMITY = (0.70, 0.80)

STATE_COLS = {
    "A": ["a_fed_dir", "a_ecb_dir", "a_gap", "a_gap_d126", "a_us_slope", "a_spread2y", "a_spread2y_d63"],
    "B": ["b_us_infl", "b_us_infl_d6", "b_ea_infl", "b_ea_infl_d6", "b_us_unemp", "b_us_unemp_d6", "b_ea_unemp", "b_ea_unemp_d6"],
    "C": ["c_ret63", "c_ret252", "c_dist200", "c_rvpct", "c_vix", "c_eqrel63", "c_brent_d126"],
    "D": ["d_cot_z52", "d_cot_z52_d65"],
    "F": ["f_cot_z52", "f_d_spread2y_20", "f_house"],
}
STATE_COLS["E"] = STATE_COLS["A"] + STATE_COLS["B"] + STATE_COLS["C"] + STATE_COLS["D"]
LONG_COLS = {      # long-library variants (1990+): proxies before the euro, clearly labelled
    "A": ["a_fed_dir", "a_ecb_dir", "aL_gap", "aL_gap_d126", "a_us_slope", "a_spread2y", "a_spread2y_d63"],
    "B": ["bL_us_infl", "bL_us_infl_d6", "bL_ea_infl", "bL_ea_infl_d6", "bL_us_unemp", "bL_us_unemp_d6", "bL_ea_unemp", "bL_ea_unemp_d6"],
    "C": STATE_COLS["C"],
}
STATES = ("A", "B", "C", "D", "E", "F")
STATE_TXT = {"A": "policy / rates", "B": "macro (inflation, unemployment)", "C": "market", "D": "positioning", "E": "union A-D, 4 PCs",
             "F": "agreement-rule inputs"}
CANDIDATES = tuple((f"{s}_k{k}", s, k) for s in STATES for k in KS)
DIM_TXT = {
    "a_fed_dir": "Fed phase (-1 cutting, 0 hold, +1 hiking)", "a_ecb_dir": "ECB phase (-1 cutting, 0 hold, +1 hiking)",
    "a_gap": "policy gap: ECB deposit - Fed target (pp)", "a_gap_d126": "policy gap, 6-month change (pp)",
    "a_us_slope": "US 2y - Fed target (pp)", "a_spread2y": "EA - US 2y spread (pp)", "a_spread2y_d63": "2y spread, 3-month change (pp)",
    "b_us_infl": "US CPI y/y (%)", "b_us_infl_d6": "US CPI y/y, 6-month change", "b_ea_infl": "euro-area HICP y/y (%)",
    "b_ea_infl_d6": "HICP y/y, 6-month change", "b_us_unemp": "US unemployment (%)", "b_us_unemp_d6": "US unemployment, 6-month change",
    "b_ea_unemp": "euro-area unemployment (%)", "b_ea_unemp_d6": "euro-area unemployment, 6-month change",
    "c_ret63": "EUR/USD 3-month return (log)", "c_ret252": "EUR/USD 12-month return (log)", "c_dist200": "distance from 200-day average (log)",
    "c_rvpct": "realised-volatility percentile (5y)", "c_vix": "log VIX", "c_eqrel63": "DAX - S&P 500 3-month return",
    "c_brent_d126": "Brent 6-month change (log)", "d_cot_z52": "cot_z52", "d_cot_z52_d65": "cot_z52, 13-week change",
    "f_cot_z52": "cot_z52 (store)", "f_d_spread2y_20": "20-day change of the 2y spread", "f_house": "house macro score",
}


# ============================================================================= states
def _lag1(s: pd.Series, cd: pd.DatetimeIndex, lag: int = 1) -> np.ndarray:
    return SW._align_lagged(s, cd, lag).values


def _ea2y(cd: pd.DatetimeIndex) -> tuple[np.ndarray, dict]:
    """Euro-area 2y: AAA spot from 2004-09-06, before that the declared 3m / 10y interpolation proxy."""
    aaa = pd.read_csv(MACRO / "ea_aaa_yield_curve.csv", parse_dates=["date"]).set_index("date")["aaa_spot_2y"].astype(float).dropna()
    a = _lag1(aaa, cd)
    ez3, de3, de10 = SW._ms("fred_IR3TIB01EZM156N.csv"), SW._ms("fred_IR3TIB01DEM156N.csv"), SW._ms("fred_IRLTLT01DEM156N.csv")
    s3 = pd.concat([de3[de3.index < ez3.index[0]], ez3])
    px = (s3 + 0.18 * (de10 - s3)).dropna()
    p = _lag1(px, cd, 45)
    first = int(np.argmax(np.isfinite(a)))
    off = float(np.nanmean(a[first:first + 250] - p[first:first + 250]))
    out = np.where(np.isfinite(a), a, p + off)
    return out, {"first_aaa": str(cd[first].date()), "offset_pp": off,
                 "proxy_rmse_first250_pp": float(np.sqrt(np.nanmean((a[first:first + 250] - p[first:first + 250] - off) ** 2)))}


def build_states(P: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """All static state dimensions on the frame of `swing.load_prices` (NaN where unknown)."""
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    cd = pd.DatetimeIndex(P["cdate"])
    known = cd - pd.Timedelta(days=1)
    X = pd.DataFrame(index=P.index)
    info = {}
    # ---- A: policy / rates
    PS = pd.read_csv(MACRO / "policy_state.csv", parse_dates=["date"]).set_index("date")
    row = PS.index.searchsorted(known, side="right") - 1
    okr = row >= 0
    g = lambda c: np.where(okr, PS[c].values.astype(float)[np.maximum(row, 0)], np.nan)      # noqa: E731
    stale = np.where(okr, (known - PS.index[np.maximum(row, 0)]).days.values, 9999) > 10
    fed, dfr, key = g("fed_target"), g("ecb_deposit_rate"), g("ecb_key_index")
    X["a_fed_dir"], X["a_ecb_dir"] = g("fed_dir3"), g("ecb_dir3")
    gap = pd.Series(dfr - fed, index=P.index)
    X["a_gap"], X["a_gap_d126"] = gap, gap - gap.shift(126)
    gapL = pd.Series(key - fed, index=P.index)
    X["aL_gap"], X["aL_gap_d126"] = gapL, gapL - gapL.shift(126)
    us2 = _lag1(SW._ms("fred_DGS2.csv"), cd)
    X["a_us_slope"] = us2 - fed
    ea2, info["ea2y_proxy"] = _ea2y(cd)
    spr = pd.Series(ea2 - us2, index=P.index)
    X["a_spread2y"], X["a_spread2y_d63"] = spr, spr - spr.shift(63)
    acols = [c for c in X.columns if c.startswith("a")]
    X.loc[stale, acols] = np.nan
    # ---- B: macro (arm T's helpers and lags)
    A = lambda s, lag, us: PC._asof(PC._pub(s, lag, us, None), known)                            # noqa: E731

    def tr(x, miss, f):
        y = f(x).copy()
        y[miss] = np.nan
        return y

    cpi, mc = PC._monthly(PC._ms("fred_CPIAUCSL.csv"))
    un, mu = PC._monthly(PC._ms("fred_UNRATE.csv"))
    hx, mh = PC._monthly(PC._ms("fred_CP0000EZ19M086NEST.csv"))
    eu = pd.read_csv(MACRO / "ea_unemployment.csv")
    eu = pd.Series(eu["unemployment_rate"].astype(float).values, index=pd.to_datetime(eu["month"]))
    eu, me = PC._monthly(eu)
    us_y, ea_y = tr(cpi, mc, PC._yoy), tr(hx, mh, PC._yoy)
    for pre in ("b", "bL"):
        X[f"{pre}_us_infl"] = A(us_y, 21, True)
        X[f"{pre}_us_infl_d6"] = A(tr(cpi, mc, lambda x: PC._yoy(x).diff(6)), 21, True)
        X[f"{pre}_us_unemp"] = A(tr(un, mu, lambda x: x), 21, True)
        X[f"{pre}_us_unemp_d6"] = A(tr(un, mu, lambda x: x.diff(6)), 21, True)
    X["b_ea_infl"] = A(ea_y, 21, False)
    X["b_ea_infl_d6"] = A(tr(hx, mh, lambda x: PC._yoy(x).diff(6)), 21, False)
    X["b_ea_unemp"] = A(tr(eu, me, lambda x: x), 35, False)
    X["b_ea_unemp_d6"] = A(tr(eu, me, lambda x: x.diff(6)), 35, False)
    # long-library splice: German CPI y/y before HICP y/y exists, German unemployment + level offset before 2000
    de_cpi, _ = PC._monthly(PC._ms("fred_DEUCPIALLMINMEI.csv"))
    de_y = PC._yoy(de_cpi)
    spl_y = pd.concat([de_y[de_y.index < ea_y.dropna().index[0]], ea_y.dropna()])
    de_u, _ = PC._monthly(PC._ms("fred_LRHUTTTTDEM156S.csv"))
    ov = eu.index[:12]
    off_u = float((eu.reindex(ov) - de_u.reindex(ov)).mean())
    spl_u = pd.concat([de_u[de_u.index < eu.index[0]] + off_u, eu])
    info["long_unemp_offset_pp"] = off_u
    X["bL_ea_infl"], X["bL_ea_infl_d6"] = A(spl_y, 21, False), A(spl_y.diff(6), 21, False)
    X["bL_ea_unemp"], X["bL_ea_unemp_d6"] = A(spl_u, 35, False), A(spl_u.diff(6), 35, False)
    # ---- C: market
    lc = np.log(P["close"])
    X["c_ret63"], X["c_ret252"] = lc - lc.shift(63), lc - lc.shift(252)
    X["c_dist200"] = lc - np.log(P["close"].rolling(200).mean())
    rv = lc.diff().rolling(21).std()
    X["c_rvpct"] = rv.rolling(1260, min_periods=504).rank(pct=True)
    X["c_vix"] = np.log(_lag1(SW._ms("fred_VIXCLS.csv"), cd))

    def cross(names):
        s = pd.concat([pd.read_parquet(CROSS / f"{n}_D1.parquet")["close"] for n in names])
        s.index = pd.DatetimeIndex(s.index).tz_convert("UTC").normalize().tz_localize(None)
        s = s[~s.index.duplicated(keep="last")].sort_index()
        return pd.Series(np.log(_lag1(s, cd)), index=P.index)

    dax, spx = cross(["gdaxi"]), cross(["analogs_spx_pre2003", "spx"])
    X["c_eqrel63"] = (dax - dax.shift(63)) - (spx - spx.shift(63))
    brent = pd.Series(np.log(_lag1(SW._ms("datahub_brent_daily.csv", "price"), cd)), index=P.index)
    X["c_brent_d126"] = brent - brent.shift(126)
    # ---- D: positioning
    leg = pd.read_csv(MACRO / "cot_eurofx_legacy.csv", parse_dates=["report_date"]).set_index("report_date")
    net = (leg.noncomm_long - leg.noncomm_short) / leg.open_interest
    net.index = net.index + pd.Timedelta(days=6)
    z = pd.Series(_lag1((net - net.rolling(52).mean()) / net.rolling(52).std(), cd), index=P.index)
    X["d_cot_z52"], X["d_cot_z52_d65"] = z, z - z.shift(65)
    return X.replace([np.inf, -np.inf], np.nan), info


# ============================================================================= environment
class Env:
    """Frame, outcomes, states and the per-year standardised state matrices."""

    def __init__(self, cost_pips: float = 1.2, K: dict | None = None, light: bool = False):
        P = SW.load_prices()
        self.P = P
        self.n = len(P)
        self.cd = pd.DatetimeIndex(P["cdate"])
        self.year = P.index.year.values
        self.close = P["close"].values
        lc = np.log(self.close)
        self.lc = lc
        self.fwd = {}
        for h in (1,) + HORIZONS:
            f = np.full(self.n, np.nan)
            f[:self.n - h] = (lc[h:] - lc[:self.n - h]) * 1e4
            self.fwd[h] = f
        self.X, self.info = build_states(P)
        self.cost_pips = cost_pips
        self.cost_bp = cost_pips / self.close
        self.lib_lo = {k: int(np.searchsorted(self.cd.values, np.datetime64(v))) for k, v in LIB_START.items()}
        # store part
        if K is None and not light:
            K = PC._context(cost_pips)
        if K is not None:
            self.K = K
            D, ctx = K["D"], K["ctx"]
        else:
            self.K = None
            D = S.load_data()
            ctx = S.make_ctx(D, cost_pips)
        self.D, self.ctx = D, ctx
        self.nD = len(D)
        self.off = self.n - self.nD
        assert P.index[self.off:].equals(D.index), "frame and store sessions differ"
        full = lambda v: np.concatenate([np.full(self.off, np.nan), np.asarray(v, dtype=float)])      # noqa: E731
        self.full = full
        self.X["f_cot_z52"] = full(D["cot_z52"].values)
        self.X["f_d_spread2y_20"] = full(D["d_spread2y_20"].values)
        self.wk = np.zeros(self.n, bool)
        self.wk[(np.arange(self.n) - self.off) % STEP == 0] = True
        mo = pd.Series(self.cd.to_period("M"), index=P.index)
        self.me = (~mo.duplicated(keep="last")).values
        if K is not None:
            self.agree = np.concatenate([np.zeros(self.off, bool), K["agree"]])
            self.sg = np.nan_to_num(full(K["sg"]))
            self.hs_ok = np.concatenate([np.zeros(self.off, bool), K["hs_ok"]])
        self._house, self._Z = {}, {}
        # library base rate known at each session: share of rising outcomes among library sessions j <= t - EMBARGO
        self.base = {}
        for lib, lo in self.lib_lo.items():
            for h in HORIZONS:
                up = np.where(np.isfinite(self.fwd[h]), (self.fwd[h] > 0).astype(float), 0.0)
                cnt = np.isfinite(self.fwd[h]).astype(float)
                up[:lo] = 0.0; cnt[:lo] = 0.0
                cu, cc = np.cumsum(up), np.cumsum(cnt)
                b = np.full(self.n, np.nan)
                b[EMBARGO:] = cu[:-EMBARGO] / np.maximum(cc[:-EMBARGO], 1)
                b[:lo + EMBARGO + 250] = np.nan
                self.base[(lib, h)] = b

    # ---- house score for state F: weights fitted before year Y, applied to every session
    def house(self, Y: int) -> np.ndarray:
        if Y not in self._house:
            ctx = self.ctx
            nD = self.nD
            end1 = np.full(nD, S.NAT, dtype=np.int64)
            end1[:nD - 1] = ctx.ct[1:]
            start = pd.Timestamp(f"{Y}-01-01", tz="UTC").value
            tr = np.where((end1 != S.NAT) & (end1 < start))[0]
            if len(tr) < 750:
                self._house[Y] = np.full(self.n, np.nan)
            else:
                sc = S.house_score(ctx, S.house_fit(ctx, tr), np.arange(nD))
                self._house[Y] = self.full(sc)
        return self._house[Y]

    def raw(self, state: str, lib: str, Y: int) -> tuple[np.ndarray, list]:
        cols = (LONG_COLS if lib == "long" else STATE_COLS)[state]
        if state == "F":
            M = np.column_stack([self.X["f_cot_z52"].values, self.X["f_d_spread2y_20"].values, self.house(Y)])
        else:
            M = self.X[cols].values.astype(float)
        return M, cols

    def Z(self, state: str, lib: str, metric: str, Y: int, shift: int = 0) -> np.ndarray:
        """Standardised (and for E projected, for Mahalanobis whitened) state matrix for decisions in year Y."""
        key = (state, lib, metric, Y, shift)
        if key in self._Z:
            return self._Z[key]
        M, _ = self.raw(state, lib, Y)
        if shift:
            M = pd.DataFrame(M).shift(shift).values
        lo = self.lib_lo[lib]
        tr = np.zeros(self.n, bool)
        tr[lo:] = True
        tr &= (self.year < Y) & np.isfinite(M).all(1)
        if tr.sum() < 500:
            out = np.full((self.n, M.shape[1] if state != "E" else N_PC), np.nan)
            self._Z[key] = out
            return out
        mu, sd = M[tr].mean(0), M[tr].std(0)
        sd = np.where(sd > 1e-12, sd, np.inf)
        Zs = np.clip((M - mu) / sd, -CLIP, CLIP)
        if state == "E":
            Zt = Zs[tr] - Zs[tr].mean(0)
            _, sv, Vt = np.linalg.svd(Zt, full_matrices=False)
            V = Vt[:N_PC].T
            Zs = (Zs - Zs[tr].mean(0)) @ V
            if metric == "mahal":
                Zs = Zs / (sv[:N_PC] / math.sqrt(max(tr.sum() - 1, 1)))
            self._pca = getattr(self, "_pca", {})
            self._pca[(lib, Y)] = {"loadings": V, "explained": (sv[:N_PC] ** 2) / (sv ** 2).sum()}
        elif metric == "mahal":
            C = np.cov(Zs[tr].T) if Zs.shape[1] > 1 else np.array([[Zs[tr].var()]])
            C = 0.9 * C + 0.1 * np.eye(C.shape[0])
            L = np.linalg.cholesky(np.linalg.inv(C))
            Zs = Zs @ L
        if not shift:
            self._Z[key] = Zs
        return Zs


# ============================================================================= the neighbour engine
def knn_pass(E: Env, state: str, lib: str = "main", metric: str = "euclid", mode: str = "nearest", years=TEST_YEARS,
             embargo: int = EMBARGO, future: bool = False, freeze: bool = False, seed: int = 0, kernel: bool = False,
             dec_idx: np.ndarray | None = None, shift: int = 0) -> dict:
    """Greedy thinned neighbours of every decision session. Returns nn (n x KMAX frame indices, -1 = none), d2
    (squared distances; ranks for the controls), n_elig, and with kernel=True the kernel probabilities."""
    n = E.n
    nn = np.full((n, KMAX), -1, dtype=np.int32)
    d2 = np.full((n, KMAX), np.nan)
    n_elig = np.zeros(n, dtype=np.int32)
    kp = {h: np.full(n, np.nan) for h in HORIZONS}
    kneff = np.full(n, np.nan)
    rng = np.random.default_rng(seed)
    lo = E.lib_lo[lib]
    known = np.isfinite(E.fwd[max(HORIZONS)])
    for Y in years:
        Z = E.Z(state, lib, metric, Y, shift)
        ok = np.isfinite(Z).all(1)
        dec = np.where(ok & (E.year == Y))[0]
        if dec_idx is not None:
            dec = np.intersect1d(dec, dec_idx)
        if len(dec) == 0:
            continue
        hi = n if future else int(dec[-1]) - embargo + 1
        if hi <= lo:
            continue
        cols = np.arange(lo, hi)
        libok = ok[lo:hi] & known[lo:hi]
        Zl = np.where(libok[:, None], Z[lo:hi], 0.0)
        Zd = Z[dec]
        D2 = (Zd ** 2).sum(1)[:, None] + (Zl ** 2).sum(1)[None, :] - 2.0 * Zd @ Zl.T
        np.maximum(D2, 0.0, out=D2)
        D2[:, ~libok] = np.inf
        I, J = dec[:, None], cols[None, :]
        if future:
            D2[np.abs(J - I) < embargo] = np.inf
        elif freeze:
            i0 = int(np.argmax(E.year == Y))
            D2[:, cols > i0 - embargo] = np.inf
        else:
            D2[J > I - embargo] = np.inf
        fin = np.isfinite(D2)
        ne = fin.sum(1)
        n_elig[dec] = ne
        valid = ne >= MIN_LIB
        if mode == "farthest":
            D2 = np.where(fin, -D2, np.inf)
        elif mode == "random":
            D2 = np.where(fin, rng.random(D2.shape), np.inf)
        D0 = D2.copy() if kernel else None
        r = np.arange(len(dec))
        m = D2.shape[1]
        picks = np.full((len(dec), KMAX), -1, dtype=np.int64)
        pd2 = np.full((len(dec), KMAX), np.nan)
        offs = np.arange(-(SEP - 1), SEP)
        for s in range(KMAX):
            j = D2.argmin(1)
            dm = D2[r, j]
            good = np.isfinite(dm)
            picks[good, s] = cols[j[good]]
            pd2[good, s] = dm[good]
            jj = np.clip(j[:, None] + offs[None, :], 0, m - 1)
            D2[r[:, None], jj] = np.inf
        picks[~valid] = -1
        pd2[~valid] = np.nan
        nn[dec] = picks
        d2[dec] = pd2
        if kernel:
            b2 = pd2[:, K_KERNEL - 1]
            with np.errstate(over="ignore", invalid="ignore", divide="ignore"):
                W = np.exp(-0.5 * D0 / np.maximum(b2[:, None], 1e-12))
            W[~np.isfinite(D0)] = 0.0
            sw = W.sum(1)
            for h in HORIZONS:
                up = np.nan_to_num((E.fwd[h][lo:hi] > 0).astype(float))
                p = (W @ up) / np.maximum(sw, 1e-300)
                p[~valid | ~np.isfinite(b2)] = np.nan
                kp[h][dec] = p
            ke = sw ** 2 / np.maximum((W ** 2).sum(1), 1e-300)
            ke[~valid] = np.nan
            kneff[dec] = ke
    return {"nn": nn, "d2": d2, "n_elig": n_elig, "kernel_p": kp, "kernel_neff": kneff, "state": state, "lib": lib, "metric": metric, "mode": mode}


def forecast(E: Env, nn: np.ndarray, k: int, h: int, fwd: np.ndarray | None = None) -> dict:
    """P(up), mean return, episodes and episode-level P from the first k chosen analogs."""
    f_all = E.fwd[h] if fwd is None else fwd
    idx = nn[:, :k]
    valid = idx[:, k - 1] >= 0
    srt = np.sort(np.where(idx >= 0, idx, 0), axis=1)
    f = f_all[srt]
    up = (f > 0).astype(float)
    p = up.mean(1)
    mret = np.nanmean(f, axis=1)
    newep = np.concatenate([np.zeros((len(srt), 1), bool), np.diff(srt, axis=1) > EPI_GAP], axis=1)
    eid = np.cumsum(newep, axis=1)
    n_epi = eid[:, -1] + 1
    onehot = eid[:, :, None] == np.arange(k)[None, None, :]
    size = onehot.sum(1)
    upsum = (onehot * up[:, :, None]).sum(1)
    with np.errstate(invalid="ignore", divide="ignore"):
        share = np.where(size > 0, upsum / np.maximum(size, 1), np.nan)
    p_epi = np.nanmean(share, axis=1)
    yrs = np.array([len(set(row)) for row in E.year[srt]])
    out = {"p": p, "mean_bp": mret, "n_epi": n_epi.astype(float), "p_epi": p_epi, "n_years": yrs.astype(float)}
    for v in out.values():
        v[~valid] = np.nan
    return out


def call(p: np.ndarray, thr: float = 0.5) -> np.ndarray:
    """-1 / 0 / +1 call from a probability; thr > 0.5 = speak only when max(p, 1-p) >= thr. NaN where no forecast."""
    s = np.where(p > 0.5, 1.0, np.where(p < 0.5, -1.0, 0.0))
    if thr > 0.5:
        s = np.where(np.maximum(p, 1 - p) >= thr - 1e-12, s, 0.0)
    return np.where(np.isfinite(p), s, np.nan)


# ============================================================================= evaluation on the frame
def decide(E: Env, h: int, speak: np.ndarray, mode: str) -> np.ndarray:
    valid = np.isfinite(E.fwd[h])
    sp = speak & valid
    if mode == "weekly":
        return np.where(E.wk & sp)[0]
    if mode == "monthly":
        return np.where(E.me & sp)[0]
    out, i, n = [], 0, E.n
    nz = np.where(sp)[0]
    if len(nz) == 0:
        return np.array([], dtype=int)
    i = int(nz[0])
    while i < n:
        if sp[i]:
            out.append(i)
            i += h
        else:
            i += 1
    return np.array(out, dtype=int)


def cells(E: Env, h: int, idx: np.ndarray, dirs: np.ndarray, speak: np.ndarray, mode: str, periods, avail: np.ndarray | None = None) -> list[dict]:
    """Accuracy cells in the form of arm T's `cells` (Wilson; conservative effective n on overlapping grids)."""
    fw = E.fwd[h]
    valid = np.isfinite(fw)
    grid = np.where((E.wk if mode == "weekly" else E.me if mode == "monthly" else np.ones(E.n, bool)) & valid)[0]
    gy = E.year[grid]
    d = dirs[idx]
    gross = d * fw[idx]
    hit = (gross > 0).astype(float)
    net = gross - 2 * E.cost_bp[idx]
    yr = E.year[idx]
    step = {"weekly": STEP, "monthly": 21, "nonoverlap": h}[mode]
    rows = []
    for lab, a, b in periods:
        g = grid[(gy >= a) & (gy <= b)]
        m = (yr >= a) & (yr <= b)
        nd = int(m.sum())
        r = {"period": lab, "n": nd}
        if len(g) == 0:
            rows.append(r); continue
        g0 = g[0]
        if avail is not None:
            av = g[avail[g]]
            g0 = av[0] if len(av) else g[0]
        yrs = max((E.P.index[g[-1]] - E.P.index[g0]).days / 365.25, 1e-9)
        base = float((fw[g] > 0).mean())
        r.update({"dec_per_year": nd / yrs, "coverage": float(speak[g].mean()), "base_up": base})
        if nd:
            acc = float(hit[m].mean())
            if mode == "nonoverlap":
                neff = float(nd)
            else:
                neff = float(nd)
                if mode == "weekly":
                    s = np.zeros(len(g)); hh = np.zeros(len(g))
                    loc = np.searchsorted(g, idx[m])
                    s[loc] = 1.0; hh[loc] = hit[m]
                    neff = S.nw_neff(s, hh, int(math.ceil(1.5 * h / STEP)))
                neff = min(neff, max(1.0, nd * step / max(h, step)))
            lo, hi = S.wilson(acc, neff)
            sl = float((d[m] > 0).mean())
            r.update({"accuracy": acc, "lo": lo, "hi": hi, "n_eff": neff, "share_long": sl, "chance_acc": sl * base + (1 - sl) * (1 - base),
                      "gross_bp": float(gross[m].mean()), "net_bp": float(net[m].mean())})
        rows.append(r)
    return rows


def eval_call(E: Env, s: np.ndarray, h: int, tag: dict, modes=("weekly", "monthly", "nonoverlap"), pre: bool = False) -> list[dict]:
    """Standalone record of a call series s (-1/0/+1, NaN = no forecast) at horizon h."""
    s0 = np.nan_to_num(s)
    live = np.isfinite(s) & (s0 != 0)
    avail = np.isfinite(s)
    rows = []
    for mode in modes:
        if pre:
            scopes = ((1997, PERIODS_PRE),)
        elif mode == "nonoverlap":
            scopes = ((2006, PERIODS_2006), (2010, PERIODS_2010))
        else:
            scopes = ((2006, ALL_PERIODS),)
        for y0, periods in scopes:
            sp = live & (E.year >= y0) & ((E.year <= 2005) if pre else True)
            idx = decide(E, h, sp, mode)
            for r in cells(E, h, idx, s0, sp, mode, periods, avail):
                rows.append({**tag, "h": h, "mode": mode, **r})
    return rows


def rules(E: Env, s: np.ndarray) -> dict:
    s0 = np.nan_to_num(s)
    live = np.isfinite(s) & (s0 != 0)
    a, sg = E.agree, E.sg
    return {"standalone": (live, s0), "agree3": (a, sg), "vote_agree": (a & live & (s0 == sg), sg), "vote_veto": (a & ~(live & (s0 == -sg)), sg),
            "extend": (E.hs_ok & ~a & live, s0), "agree3_signal_opposes": (a & live & (s0 == -sg), sg)}


def eval_votes(E: Env, s: np.ndarray, h: int, tag: dict, tests=("agree3", "vote_agree", "vote_veto", "extend", "agree3_signal_opposes")) -> list[dict]:
    rows = []
    R = rules(E, s)
    avail = np.isfinite(s)
    for test in tests:
        sp0, dirs = R[test]
        for mode in ("weekly", "nonoverlap"):
            scopes = ((2006, PERIODS_2006), (2010, PERIODS_2010)) if mode == "nonoverlap" else ((2006, ALL_PERIODS),)
            for y0, periods in scopes:
                sp = sp0 & (E.year >= y0)
                idx = decide(E, h, sp, mode)
                for r in cells(E, h, idx, dirs, sp, mode, periods, avail if test != "agree3" else None):
                    rows.append({**tag, "test": test, "h": h, "mode": mode, **r})
    return rows


def paired_boot(E: Env, s: np.ndarray, form: str, h: int, a: int, b: int, reps: int = 2000, seed: int = 5) -> dict:
    """Weekly grid: accuracy of the vote rule minus accuracy of the agreement rule, circular block bootstrap (arm T)."""
    fw = E.fwd[h]
    g = np.where(E.wk & np.isfinite(fw) & (E.year >= a) & (E.year <= b))[0]
    R = rules(E, s)
    A, V = R["agree3"][0][g].astype(float), R[form][0][g].astype(float)
    hit = (E.sg[g] * fw[g] > 0).astype(float)
    nan = {"diff": np.nan, "lo": np.nan, "hi": np.nan, "kept_minus_dropped": np.nan, "lo_kd": np.nan, "hi_kd": np.nan}
    if A.sum() < 10 or V.sum() < 5:
        return nan
    Dr = A - V
    f = lambda A_, V_, D_, H_: ((V_ * H_).sum(-1) / np.maximum(V_.sum(-1), 1) - (A_ * H_).sum(-1) / np.maximum(A_.sum(-1), 1),   # noqa: E731
                                (V_ * H_).sum(-1) / np.maximum(V_.sum(-1), 1) - (D_ * H_).sum(-1) / np.maximum(D_.sum(-1), 1))
    d0, k0 = f(A, V, Dr, hit)
    rng = np.random.default_rng(seed)
    Tn, block = len(g), max(2, int(math.ceil(2 * h / STEP)))
    nb = int(math.ceil(Tn / block))
    st = rng.integers(0, Tn, size=(reps, nb))
    ix = ((st[:, :, None] + np.arange(block)[None, None, :]) % Tn).reshape(reps, -1)[:, :Tn]
    d, k = f(A[ix], V[ix], Dr[ix], hit[ix])
    okv = V[ix].sum(1) > 0
    okd = okv & (Dr[ix].sum(1) > 0)
    return {"diff": float(d0), "lo": float(np.quantile(d[okv], 0.025)), "hi": float(np.quantile(d[okv], 0.975)),
            "kept_minus_dropped": float(k0) if Dr.sum() else np.nan,
            "lo_kd": float(np.quantile(k[okd], 0.025)) if okd.sum() > 50 else np.nan, "hi_kd": float(np.quantile(k[okd], 0.975)) if okd.sum() > 50 else np.nan}


def reliability(E: Env, p: np.ndarray, h: int, tag: dict, lib: str = "main", periods=ALL_PERIODS) -> list[dict]:
    """Weekly-grid reliability of P(up): bins, realised share, Brier against 50 % and against the library base rate."""
    fw = E.fwd[h]
    ok = E.wk & np.isfinite(p) & np.isfinite(fw)
    y = (fw > 0).astype(float)
    base = E.base[(lib, h)]
    edges = [0.0, 0.2, 0.3, 0.4, 0.5 - 1e-9, 0.5 + 1e-9, 0.6, 0.7, 0.8, 1.0 + 1e-9]
    labs = ["<20", "20-30", "30-40", "40-50", "=50", "50-60", "60-70", "70-80", ">=80"]
    rows = []
    for lab, a, b in periods:
        m = ok & (E.year >= a) & (E.year <= b)
        if m.sum() < 20:
            continue
        pp, yy, bb = p[m], y[m], np.where(np.isfinite(base[m]), base[m], 0.5)
        brier = float(((pp - yy) ** 2).mean())
        sl = float(np.polyfit(pp, yy, 1)[0]) if pp.std() > 1e-9 else np.nan
        conf = np.maximum(pp, 1 - pp)
        hitc = np.where(pp > 0.5, yy, 1 - yy)
        live = pp != 0.5
        rows.append({**tag, "h": h, "period": lab, "bin": "ALL", "n": int(m.sum()), "mean_p": float(pp.mean()), "share_up": float(yy.mean()),
                     "brier": brier, "brier_50": 0.25, "brier_base_rate": float(((bb - yy) ** 2).mean()), "calib_slope": sl,
                     "mean_conf": float(conf[live].mean()) if live.any() else np.nan, "accuracy": float(hitc[live].mean()) if live.any() else np.nan})
        for i, bl in enumerate(labs):
            q = (pp >= edges[i]) & (pp < edges[i + 1])
            if q.sum():
                rows.append({**tag, "h": h, "period": lab, "bin": bl, "n": int(q.sum()), "mean_p": float(pp[q].mean()), "share_up": float(yy[q].mean())})
        for cl, c0, c1 in (("conf50-60", 0.5 + 1e-9, 0.6), ("conf60-70", 0.6, 0.7), ("conf70-80", 0.7, 0.8), ("conf>=80", 0.8, 1.01)):
            q = (conf >= c0 - 1e-12) & (conf < c1 - 1e-12)
            if q.sum():
                rows.append({**tag, "h": h, "period": lab, "bin": cl, "n": int(q.sum()), "mean_p": float(conf[q].mean()), "share_up": float(hitc[q].mean())})
    return rows


def tranche_book(E: Env, s: np.ndarray, h: int, cost_pips: float, y0: int = 2006) -> pd.DataFrame:
    """Weekly tranches of the call series (held h sessions, weight 1/ceil(h/5)), store sessions only."""
    s0 = np.nan_to_num(s)
    live = np.isfinite(s) & (s0 != 0) & (E.year >= y0)
    idx = np.where(E.wk & live)[0]
    w = 1.0 / math.ceil(h / STEP)
    pos = np.zeros(E.n)
    for i in idx:
        pos[i:i + h] += s0[i] * w
    D = E.D
    pnl = pnl_from_positions(pd.Series(pos[E.off:], index=D.index), D["fwd_1d"], D["close"], cost_pips=cost_pips)
    pnl["fwd_bp"] = D["fwd_1d"]
    return pnl[pnl.index.year >= y0]


# ============================================================================= run
def compute(cost_pips: float = 1.2, verbose: bool = True) -> dict:
    E = Env(cost_pips)
    log = (lambda *a: print(*a, flush=True)) if verbose else (lambda *a: None)
    # ---- reconciliation of the agreement rule with arm N
    pub = {(21, "weekly"): (387, 0.594), (42, "weekly"): (383, 0.648), (63, "weekly"): (383, 0.666),
           (21, "nonoverlap"): (156, 0.59), (42, "nonoverlap"): (89, 0.61), (63, "nonoverlap"): (61, 0.72)}
    rec = []
    for (h, mode), (npub, apub) in pub.items():
        sp = E.agree & (E.year >= 2010)
        idx = decide(E, h, sp, mode)
        c = cells(E, h, idx, E.sg, sp, mode, PERIODS_2010)[0]
        rec.append({"h": h, "mode": mode, "n_here": c["n"], "acc_here": c["accuracy"], "n_published": npub, "acc_published": apub})
    rec = pd.DataFrame(rec)
    log(rec.to_string())
    # ---- neighbour passes
    passes, FC = {}, {}
    for st in STATES:
        passes[(st, "main", "euclid")] = knn_pass(E, st, kernel=True)
        passes[(st, "main", "mahal")] = knn_pass(E, st, metric="mahal")
        log(f"  neighbours {st}: first forecast {E.cd[np.argmax(passes[(st, 'main', 'euclid')]['nn'][:, KMAX - 1] >= 0)].date()}")
    for st in LONG_COLS:
        passes[(st, "long", "euclid")] = knn_pass(E, st, lib="long", years=PRE_YEARS + TEST_YEARS)
    for key, ps in passes.items():
        for k in KS:
            for h in HORIZONS:
                FC[key + (k, h)] = forecast(E, ps["nn"], k, h)
    # ---- standalone accuracy, calibration, unanimity
    acc, cal, una = [], [], []
    for (st, lib, metric), ps in passes.items():
        for k in KS:
            for h in HORIZONS:
                fc = FC[(st, lib, metric, k, h)]
                tag = {"state": st, "k": k, "lib": lib, "metric": metric, "model": "knn", "rule": f"{st}_k{k}"}
                acc += eval_call(E, call(fc["p"]), h, {**tag, "call": "all"})
                if lib == "long":
                    acc += eval_call(E, call(fc["p"]), h, {**tag, "call": "all"}, modes=("weekly", "nonoverlap"), pre=True)
                cal += reliability(E, fc["p"], h, tag, lib)
                if metric == "euclid":
                    cal += reliability(E, fc["p_epi"], h, {**tag, "model": "knn_episode_level"}, lib)
                for thr in UNANIMITY:
                    s = call(fc["p"], thr)
                    rr = eval_call(E, s, h, {**tag, "call": f"p>={int(thr * 100)}"}, modes=("weekly", "nonoverlap"))
                    live = np.nan_to_num(s) != 0
                    for r in rr:
                        a, b = [(x[1], x[2]) for x in ALL_PERIODS if x[0] == r["period"]][0]
                        m = live & E.wk & (E.year >= a) & (E.year <= b)
                        r["mean_n_epi"] = float(np.nanmean(fc["n_epi"][m])) if m.any() else np.nan
                    una += rr
        if metric == "euclid" and lib == "main":
            for h in HORIZONS:
                tag = {"state": st, "k": K_KERNEL, "lib": lib, "metric": metric, "model": "kernel", "rule": f"{st}_kernel"}
                acc += eval_call(E, call(ps["kernel_p"][h]), h, {**tag, "call": "all"})
                cal += reliability(E, ps["kernel_p"][h], h, tag, lib)
    acc, cal, una = pd.DataFrame(acc), pd.DataFrame(cal), pd.DataFrame(una)
    log("  standalone / calibration done")
    # ---- episodes behind the forecasts
    epi = []
    for (st, lib, metric), ps in passes.items():
        if metric != "euclid":
            continue
        for k in KS:
            fc = FC[(st, lib, metric, k, 21)]
            m = E.wk & np.isfinite(fc["p"]) & (E.year >= 2006)
            if not m.any():
                continue
            ages = (np.arange(E.n)[:, None] - ps["nn"][:, :k])[m] / 252.0
            r = {"state": st, "k": k, "lib": lib, "n_forecasts_weekly": int(m.sum()), "mean_n_epi": float(fc["n_epi"][m].mean()),
                 "median_n_epi": float(np.median(fc["n_epi"][m])), "p10_n_epi": float(np.quantile(fc["n_epi"][m], 0.1)),
                 "mean_distinct_years": float(fc["n_years"][m].mean()), "median_analog_age_years": float(np.median(ages)),
                 "mean_dist_k": float(np.sqrt(ps["d2"][m, k - 1]).mean()), "mean_dist_1": float(np.sqrt(ps["d2"][m, 0]).mean())}
            for h in HORIZONS:
                f2 = FC[(st, lib, metric, k, h)]
                for thr in UNANIMITY:
                    q = m & (np.maximum(f2["p"], 1 - f2["p"]) >= thr - 1e-12)
                    r[f"h{h}_share_p>={int(thr * 100)}"] = float(q.sum() / m.sum())
                    r[f"h{h}_n_epi_when_p>={int(thr * 100)}"] = float(f2["n_epi"][q].mean()) if q.any() else np.nan
                    qe = m & (np.maximum(f2["p_epi"], 1 - f2["p_epi"]) >= thr - 1e-12)
                    r[f"h{h}_share_episode_p>={int(thr * 100)}"] = float(qe.sum() / m.sum())
            epi.append(r)
    epi = pd.DataFrame(epi)
    # ---- extra votes, placebo, bootstrap for the 12 candidates
    votes, plc, boots = [], [], []
    for nm, st, k in CANDIDATES:
        for h in HORIZONS:
            p = FC[(st, "main", "euclid", k, h)]["p"]
            s = call(p)
            tag = {"rule": nm, "state": st, "k": k}
            votes += eval_votes(E, s, h, {**tag, "signal": "call"})
            votes += eval_votes(E, call(p, 0.7), h, {**tag, "signal": "call_p>=70"}, tests=("vote_agree", "extend"))
            for sh in PLACEBO_SHIFTS:
                ss = pd.Series(s).shift(sh).values
                plc += eval_votes(E, ss, h, {**tag, "signal": f"call+{sh}"}, tests=("vote_agree",))
                plc += [{**r, "test": "standalone"} for r in eval_call(E, ss, h, {**tag, "signal": f"call+{sh}"}, modes=("weekly", "nonoverlap"))]
            for lab, a, b in (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2006-26", 2006, 2026)):
                boots.append({**tag, "h": h, "period": lab, "form": "vote_agree", **paired_boot(E, s, "vote_agree", h, a, b)})
    votes, plc, boots = pd.DataFrame(votes), pd.DataFrame(plc), pd.DataFrame(boots)
    log("  votes / placebo done")
    # ---- controls: farthest, random, base rate, shuffled outcomes, look-ahead, frozen library, stale state
    ctl = []
    rng = np.random.default_rng(11)
    for st in STATES:
        far = knn_pass(E, st, mode="farthest")
        fut = knn_pass(E, st, future=True)
        adj = knn_pass(E, st, future=True, embargo=1)
        frz = knn_pass(E, st, freeze=True)
        stale = knn_pass(E, st, shift=21)
        rnd = [knn_pass(E, st, mode="random", seed=100 + i) for i in range(5)]
        near = passes[(st, "main", "euclid")]
        for k in KS:
            for h in HORIZONS:
                tag = {"state": st, "k": k, "rule": f"{st}_k{k}"}
                ev = lambda nn_, lab_, fwd_=None: [{**tag, "control": lab_, **r} for r in                          # noqa: E731
                                                   eval_call(E, call(forecast(E, nn_, k, h, fwd_)["p"]), h, {}, modes=("weekly", "nonoverlap"))]
                ctl += ev(near["nn"], "nearest")
                ctl += ev(far["nn"], "farthest")
                ctl += ev(fut["nn"], "lookahead_future_allowed_embargo63")
                ctl += ev(adj["nn"], "lookahead_no_embargo")
                ctl += ev(frz["nn"], "library_frozen_at_year_start")
                ctl += ev(stale["nn"], "state_stale_21")
                for i, rp in enumerate(rnd):
                    ctl += ev(rp["nn"], f"random_{i}")
                for i in range(5):
                    perm = rng.permutation(E.n)
                    ctl += ev(near["nn"], f"shuffled_outcomes_{i}", E.fwd[h][perm])
                # second-nearest set (ranks k+1..2k) for k = 20: does the vote decay with distance?
                if k == 20:
                    nn2 = np.concatenate([near["nn"][:, 20:], near["nn"][:, 20:]], axis=1)
                    ctl += ev(nn2, "ranks_21_40")
        for h in HORIZONS:
            b = E.base[("main", h)]
            ok = np.isfinite(passes[(st, "main", "euclid")]["nn"][:, KMAX - 1].astype(float)) & (passes[(st, "main", "euclid")]["nn"][:, KMAX - 1] >= 0)
            sb = np.where(ok & np.isfinite(b), np.where(b > 0.5, 1.0, -1.0), np.nan)
            ctl += [{"state": st, "k": 0, "rule": f"{st}_base", "control": "library_base_rate", **r} for r in eval_call(E, sb, h, {}, modes=("weekly", "nonoverlap"))]
        log(f"  controls {st} done")
    ctl = pd.DataFrame(ctl)
    # ---- label-in-disguise check: correlation of each state dimension with the forward returns (weekly grid, 2006+)
    lab = []
    for st in ("A", "B", "C", "D", "F"):
        M, cols = E.raw(st, "main", 2026)
        for c_, x in zip(cols, M.T):
            r = {"state": st, "dimension": c_}
            for h in (1,) + HORIZONS:
                m = np.isfinite(x) & np.isfinite(E.fwd[h]) & (E.year >= 1999)
                r[f"corr_fwd{h}"] = float(np.corrcoef(x[m], E.fwd[h][m])[0, 1]) if m.sum() > 50 else np.nan
            m = E.wk & np.isfinite(x) & np.isfinite(E.fwd[1]) & (E.year >= 1999)
            r["corr_fwd1_weekly_grid"] = float(np.corrcoef(x[m], E.fwd[1][m])[0, 1]) if m.sum() > 50 else np.nan
            lab.append(r)
    lab = pd.DataFrame(lab)
    # ---- reference: the plain SIGN rules on the same inputs (existing signals, not new trials)
    D = E.D
    sgn = lambda v: np.where(np.isfinite(v), np.sign(v), np.nan)                               # noqa: E731
    cot, spr, hsg = sgn(E.full(D["cot_z52"].values)), sgn(E.full(D["d_spread2y_20"].values)), np.where(E.hs_ok, E.sg, np.nan)
    maj = np.sign(cot + spr + hsg)
    refs = {"sign(cot_z52)": cot, "sign(d_spread2y_20)": spr, "sign(house score)": hsg, "majority of the three signs": maj,
            "agreement rule (all three agree)": np.where(E.agree, E.sg, np.where(E.hs_ok, 0.0, np.nan))}
    bench = []
    for nm, s in refs.items():
        s = np.where(E.year >= 2006, s, np.nan)
        for h in HORIZONS:
            bench += eval_call(E, s, h, {"reference": nm})
    bench = pd.DataFrame(bench)
    return {"E": E, "reconcile": rec, "passes": passes, "FC": FC, "acc": acc, "cal": cal, "una": una, "epi": epi, "votes": votes, "placebo": plc,
            "boot": boots, "controls": ctl, "labelcorr": lab, "bench": bench}


def _get(T: pd.DataFrame, col: str = "accuracy", **kw) -> float:
    m = np.ones(len(T), bool)
    for k, v in kw.items():
        m &= (T[k] == v).values
    x = T[m]
    return float(x[col].iloc[0]) if len(x) and col in x and pd.notna(x[col].iloc[0]) else np.nan


def select_final(acc: pd.DataFrame) -> tuple[pd.DataFrame, str | None]:
    rows = []
    for nm, st, k in CANDIDATES:
        q = dict(rule=nm, lib="main", metric="euclid", model="knn", call="all", h=21, mode="nonoverlap", period="2006-15")
        r = {"candidate": nm, "state": st, "k": k}
        for c in ("n", "dec_per_year", "accuracy", "lo", "hi", "net_bp", "share_long", "base_up"):
            r[f"{c}_2006-15"] = _get(acc, c, **q)
        r["eligible"] = bool(r["dec_per_year_2006-15"] >= MIN_DEC_PER_YEAR)
        for per in ("2006-26", "2010-26", "2016-26", "2023-26"):
            for h in HORIZONS:
                qq = dict(q, h=h, period=per)
                r[f"acc{h}_{per}"] = _get(acc, "accuracy", **qq)
                r[f"n{h}_{per}"] = _get(acc, "n", **qq)
        rows.append(r)
    C = pd.DataFrame(rows)
    el = C[C["eligible"]].sort_values("lo_2006-15", ascending=False)
    final = el["candidate"].iloc[0] if len(el) else None
    C["final"] = C["candidate"] == final
    return C, final


def bar_table(votes: pd.DataFrame, plc: pd.DataFrame) -> pd.DataFrame:
    """Round 5 success test for every candidate in the declared form (agreement rule AND analog call agrees)."""
    rows = []
    for nm, st, k in CANDIDATES:
        r = {"candidate": nm}
        ok_gain, ok_plc = True, True
        for per in ("2010-26", "2016-26", "2023-26", "2006-26"):
            for h in HORIZONS:
                q = dict(rule=nm, signal="call", h=h, mode="nonoverlap", period=per)
                a0, a1 = _get(votes, "accuracy", test="agree3", **q), _get(votes, "accuracy", test="vote_agree", **q)
                r[f"agree3_{h}_{per}"], r[f"vote_{h}_{per}"], r[f"gain_{h}_{per}"] = a0, a1, a1 - a0
                r[f"vote_n_{h}_{per}"] = _get(votes, "n", test="vote_agree", **q)
                r[f"vote_dpy_{h}_{per}"] = _get(votes, "dec_per_year", test="vote_agree", **q)
                r[f"extend_{h}_{per}"] = _get(votes, "accuracy", test="extend", **q)
                r[f"extend_n_{h}_{per}"] = _get(votes, "n", test="extend", **q)
                if per in ("2010-26", "2016-26") and h in (21, 42):
                    gn = a1 - a0
                    ok_gain &= bool(gn >= 0.03 - 1e-12)
                    for sh in PLACEBO_SHIFTS:
                        pg = _get(plc, "accuracy", rule=nm, signal=f"call+{sh}", test="vote_agree", h=h, mode="nonoverlap", period=per) - a0
                        r[f"placebo{sh}_gain_{h}_{per}"] = pg
                        ok_plc &= bool(np.isfinite(pg) and gn > 0 and pg <= 0.5 * gn + 1e-12)
        dpy = np.nanmin([r["vote_dpy_21_2010-26"], r["vote_dpy_21_2016-26"]])
        ok_n = bool(dpy >= 6)
        ok_23 = bool(r["gain_21_2023-26"] >= -1e-12 and r["gain_42_2023-26"] >= -1e-12)
        r.update({"pass_gain_3pts": ok_gain, "pass_6_per_year": ok_n, "pass_2023_not_worse": ok_23, "pass_placebo": ok_plc,
                  "PASS_ROUND5_BAR": bool(ok_gain and ok_n and ok_23 and ok_plc)})
        rows.append(r)
    return pd.DataFrame(rows)


def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Runs everything, applies the declared selection rule and writes the deliverables.
    Returns (daily positions of the final rule's weekly-tranche book as a Series, protocol report DataFrame)."""
    R = compute(cost_pips, verbose)
    E, FC = R["E"], R["FC"]
    C, final = select_final(R["acc"])
    status = "selected by the declared rule" if final else "NO candidate eligible"
    stream_name = final or "C_k20"
    B = bar_table(R["votes"], R["placebo"])
    reps, streams = [], {}
    cand = {nm: (st, k) for nm, st, k in CANDIDATES}
    for nm, (st, k) in cand.items():
        s = call(FC[(st, "main", "euclid", k, 21)]["p"])
        streams[nm] = tranche_book(E, s, 21, cost_pips)
        tb = report(streams[nm], periods_per_year=252, name=ARM, n_arms=N_ARMS)
        tb.insert(1, "variant", nm); tb["final"] = nm == stream_name; tb["kind"] = "candidate (weekly-tranche book of the 21-session call)"
        tb["cost_pips"] = cost_pips
        reps.append(tb)
    st, k = cand[stream_name]
    sfin = call(FC[(st, "main", "euclid", k, 21)]["p"])
    lo = tranche_book(E, sfin, 21, 0.6)
    tb = report(lo, periods_per_year=252, name=ARM, n_arms=N_ARMS)
    tb.insert(1, "variant", f"{stream_name}_cost0.6"); tb["final"] = False; tb["kind"] = "cost_sensitivity"; tb["cost_pips"] = 0.6
    reps.append(tb)
    D = E.D
    ds = pnl_from_positions(pd.Series(np.nan_to_num(sfin)[E.off:], index=D.index), D["fwd_1d"], D["close"], cost_pips=cost_pips)
    ds = ds[ds.index.year >= 2006]
    tb = report(ds, periods_per_year=252, name=ARM, n_arms=N_ARMS)
    tb.insert(1, "variant", f"{stream_name}_daily_sign"); tb["final"] = False; tb["kind"] = "daily sign of the call (information)"; tb["cost_pips"] = cost_pips
    reps.append(tb)
    rep = pd.concat(reps, ignore_index=True)
    pos = streams[stream_name][["pos", "fwd_bp", "net_bp"]]
    hr = []
    for lab, a, b in (("2006-26", 2006, 2026), ("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026)):
        x = streams[stream_name]
        x = x[(x.index.year >= a) & (x.index.year <= b) & (x["pos"] != 0)]
        hr.append({"period": lab, "active_sessions": len(x), "share_net_positive": float((x["net_bp"] > 0).mean()) if len(x) else np.nan,
                   "share_correct_sign": float((x["gross_bp"] > 0).mean()) if len(x) else np.nan})
    by = []
    live = np.isfinite(sfin) & (np.nan_to_num(sfin) != 0)
    for h in HORIZONS:
        sh = call(FC[(st, "main", "euclid", k, h)]["p"])
        lv = np.isfinite(sh) & (np.nan_to_num(sh) != 0) & (E.year >= 2010)
        idx = decide(E, h, lv, "nonoverlap")
        hit = (np.nan_to_num(sh)[idx] * E.fwd[h][idx] > 0)
        for Y in sorted(set(E.year[idx])):
            m = E.year[idx] == Y
            by.append({"h": h, "year": int(Y), "n": int(m.sum()), "right": int(hit[m].sum()), "accuracy": float(hit[m].mean()),
                       "net_bp": float((np.nan_to_num(sh)[idx][m] * E.fwd[h][idx][m] - 2 * E.cost_bp[idx][m]).mean())})
    R.update({"candidates": C, "final": final, "final_status": status, "stream_name": stream_name, "bar": B, "report": rep, "streams": streams,
              "hit": pd.DataFrame(hr), "cost_pips": cost_pips, "final_by_year": pd.DataFrame(by)})
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        pos.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        R["acc"].to_csv(RES / f"{ARM}_accuracy.csv", index=False)
        pd.concat([R["cal"].assign(table="reliability"), R["una"].assign(table="unanimous_calls")], ignore_index=True).to_csv(RES / f"{ARM}_calibration.csv", index=False)
        pd.concat([R["votes"].assign(kind="signal"), R["placebo"].assign(kind="timing_placebo")], ignore_index=True).to_csv(RES / f"{ARM}_votes.csv", index=False)
        B.to_csv(RES / f"{ARM}_bar.csv", index=False)
        R["boot"].to_csv(RES / f"{ARM}_paired_bootstrap.csv", index=False)
        C.to_csv(RES / f"{ARM}_candidates.csv", index=False)
        R["controls"].to_csv(RES / f"{ARM}_controls.csv", index=False)
        R["epi"].to_csv(RES / f"{ARM}_episodes.csv", index=False)
        R["labelcorr"].to_csv(RES / f"{ARM}_label_corr.csv", index=False)
        R["reconcile"].to_csv(RES / f"{ARM}_reconciliation.csv", index=False)
        R["bench"].to_csv(RES / f"{ARM}_reference_sign_rules.csv", index=False)
        R["incremental"] = incremental()
        ex = explain(env=E, final=stream_name)
        (RES / f"{ARM}_latest.json").write_text(json.dumps(ex, indent=1))
        R["latest"] = ex
        keep = {k: v for k, v in R.items() if k not in ("E", "passes", "FC", "streams")}
        keep["info"] = E.info
        keep["first_forecast"] = {st: str(E.cd[int(np.argmax(R["passes"][(st, "main", "euclid")]["nn"][:, KMAX - 1] >= 0))].date()) for st in STATES}
        keep["pca"] = {str(k): {"explained": v["explained"].tolist()} for k, v in getattr(E, "_pca", {}).items()}
        (RES / "logs").mkdir(exist_ok=True)
        with open(RES / "logs" / f"{ARM}_tables.pkl", "wb") as fh:
            pickle.dump(keep, fh)
    run.last = R
    return pos["pos"], rep


def incremental() -> pd.DataFrame:
    from eurusd.arms.meta import combine, load_arm_daily, report_combo
    two, _ = combine(["weak_signals", "regime_trend"], "EW")
    three, _ = combine(["weak_signals", "regime_trend", ARM], "EW")
    out = pd.concat([report_combo(two, "weak_signals+regime_trend", 2), report_combo(three, f"+{ARM}", 3)], ignore_index=True)
    s = load_arm_daily(ARM)
    for o in ("weak_signals", "regime_trend"):
        x = pd.concat([s, load_arm_daily(o)], axis=1).dropna()
        x = x[x.index.year >= 2010]
        out[f"corr_{o}"] = float(x.corr().iloc[0, 1])
    out.to_csv(RES / f"{ARM}_incremental.csv", index=False)
    return out


# ============================================================================= explain
def _final_name() -> str:
    p = RES / f"{ARM}_report.csv"
    if p.exists():
        r = pd.read_csv(p)
        f = r.loc[r["final"] == True, "variant"]          # noqa: E712
        if len(f):
            return str(f.iloc[0])
    return "C_k20"


def explain(date=None, n_show: int = 10, env: Env | None = None, final: str | None = None, states=STATES) -> dict:
    """The analogs of the latest session (or of the last session closing on or before `date`): for every state the
    `n_show` nearest analog dates, what EUR/USD did after each over 21 / 42 / 63 sessions, and the probabilities
    from the 10 / 20 / 40 nearest. Context for the weekly outlook, whatever the verdict on the method."""
    E = env or Env(light=True)
    final = final or _final_name()
    fstate, fk = final.split("_k")[0], int(final.split("_k")[1])
    if date is None:
        i = E.n - 1
    else:
        i = int(np.searchsorted(E.cd.values, np.datetime64(pd.Timestamp(date)), side="right")) - 1
    Y = int(E.year[i])
    pips = lambda bp, j: float(bp * 1e-4 * E.close[j] / 1e-4) if np.isfinite(bp) else None      # noqa: E731
    out = {"asof_session_close": str(E.cd[i].date()), "eurusd_close": float(E.close[i]), "final_rule": final,
           "method": f"k nearest past sessions by Euclidean distance on the standardised state, at least {EMBARGO} sessions old, "
                     f"chosen analogs at least {SEP} sessions apart; P(up) = share of analogs followed by a rise",
           "states": {}}
    rec = None
    if (RES / f"{ARM}_accuracy.csv").exists():
        rec = pd.read_csv(RES / f"{ARM}_accuracy.csv")
        rec = rec[(rec["lib"] == "main") & (rec["metric"] == "euclid") & (rec["model"] == "knn") & (rec["call"] == "all") & (rec["mode"] == "nonoverlap")
                  & (rec["period"] == "2010-26")]
    for st in states:
        ps = knn_pass(E, st, years=[Y], dec_idx=np.array([i]), kernel=True)
        nn = ps["nn"][i]
        M, cols = E.raw(st, "main", Y)
        if nn[KMAX - 1] < 0:
            out["states"][st] = {"name": STATE_TXT[st], "available": False,
                                 "reason": "state incomplete on this date or fewer than 1260 eligible analog sessions"}
            continue
        Zs = E.Z(st, "main", "euclid", Y)
        blk = {"name": STATE_TXT[st], "available": True, "n_eligible_sessions": int(ps["n_elig"][i]),
               "library_from": str(E.cd[max(E.lib_lo["main"], int(np.argmax(np.isfinite(Zs).all(1))))].date())}
        if st != "E":
            lo = E.lib_lo["main"]
            tr = (np.arange(E.n) >= lo) & (E.year < Y) & np.isfinite(M).all(1)
            mu, sd = M[tr].mean(0), M[tr].std(0)
            blk["today"] = {c: {"label": DIM_TXT.get(c, c), "value": round(float(M[i, q]), 4), "z": round(float((M[i, q] - mu[q]) / sd[q]), 2)}
                            for q, c in enumerate(cols)}
        else:
            blk["today"] = {f"PC{q + 1}": {"label": f"principal component {q + 1} of the 24 standardised dimensions", "value": round(float(Zs[i, q]), 3)}
                            for q in range(N_PC)}
        an = []
        for r_, j in enumerate(nn[:max(n_show, 0)]):
            row = {"rank": r_ + 1, "date": str(E.cd[j].date()), "distance": round(float(math.sqrt(ps["d2"][i, r_])), 3), "eurusd_close": round(float(E.close[j]), 4),
                   "source": str(E.P["src"].iloc[j])}
            for h in HORIZONS:
                row[f"ret{h}_pct"] = round(float(E.fwd[h][j]) / 100.0, 2)
                row[f"ret{h}_pips"] = round(pips(E.fwd[h][j], j), 0)
            if st != "E":
                row["state"] = {c: round(float(M[j, q]), 3) for q, c in enumerate(cols)}
            an.append(row)
        blk["analogs"] = an
        blk["forecast"] = {}
        for h in HORIZONS:
            fh = {}
            for k in (10, 20, 40):
                fc = forecast(E, ps["nn"][i:i + 1], k, h)
                p, ne = float(fc["p"][0]), float(fc["n_epi"][0])
                lo_, hi_ = S.wilson(p, ne)
                fh[f"k{k}"] = {"p_up": round(p, 3), "n_up": int(round(p * k)), "k": k, "mean_ret_pct": round(float(fc["mean_bp"][0]) / 100, 2),
                               "n_episodes": int(ne), "p_up_episode_level": round(float(fc["p_epi"][0]), 3), "distinct_years": int(fc["n_years"][0]),
                               "wilson95_on_episodes": [round(lo_, 2), round(hi_, 2)]}
            fh["kernel_p_up"] = round(float(ps["kernel_p"][h][i]), 3)
            fh["library_base_rate_up"] = round(float(E.base[("main", h)][i]), 3)
            blk["forecast"][f"{h}_sessions"] = fh
        blk["episodes_k20"] = _episode_list(E, np.sort(nn[:20]))
        if rec is not None:
            q = rec[(rec["state"] == st) & (rec["k"] == 20)]
            blk["out_of_sample_record_k20_2010_26"] = {
                f"{h}_sessions": {"accuracy_non_overlapping": round(float(x["accuracy"].iloc[0]), 3), "n": int(x["n"].iloc[0]),
                                  "wilson95": [round(float(x["lo"].iloc[0]), 2), round(float(x["hi"].iloc[0]), 2)]}
                for h in HORIZONS for x in [q[q["h"] == h]] if len(x)}
        out["states"][st] = blk
    fb = out["states"].get(fstate, {})
    if fb.get("available"):
        out["headline"] = {"state": fstate, "k": fk, **{f"p_up_{h}": fb["forecast"][f"{h}_sessions"][f"k{fk}"]["p_up"] for h in HORIZONS},
                           "n_episodes": fb["forecast"]["21_sessions"][f"k{fk}"]["n_episodes"]}
    out["how_to_read"] = ("Context, not a call: see reports/arm_analogs.md for the out-of-sample record of these probabilities. "
                          "'n_episodes' is the number of distinct historical episodes behind the k analogs (analogs within 63 sessions of each other "
                          "are one episode); the Wilson interval treats episodes, not analogs, as observations.")
    return out


def _episode_list(E: Env, srt: np.ndarray) -> list:
    eps, cur = [], [int(srt[0])]
    for j in srt[1:]:
        if j - cur[-1] > EPI_GAP:
            eps.append(cur); cur = [int(j)]
        else:
            cur.append(int(j))
    eps.append(cur)
    return [{"from": str(E.cd[e[0]].date()), "to": str(E.cd[e[-1]].date()), "n_analogs": len(e),
             **{f"share_up_{h}": round(float((E.fwd[h][e] > 0).mean()), 2) for h in HORIZONS}} for e in eps]


# ============================================================================= report
def _md(df: pd.DataFrame, index: bool = False) -> str:
    return df.to_markdown(index=index, disable_numparse=True)


def _pc(x, d: int = 0) -> str:
    return "" if x is None or not np.isfinite(x) else f"{100 * x:.{d}f}"


def _cell(T: pd.DataFrame, ci: bool = False, n: bool = True, **kw) -> str:
    a = _get(T, "accuracy", **kw)
    if not np.isfinite(a):
        return ""
    out = _pc(a, 1)
    if ci:
        out += f" [{_pc(_get(T, 'lo', **kw))}-{_pc(_get(T, 'hi', **kw))}]"
    if n:
        out += f" ({int(_get(T, 'n', **kw))})"
    return out


def _grid(T: pd.DataFrame, rows: list, rowkey: str, periods, hs=HORIZONS, ci: bool = False, n: bool = True, **kw) -> pd.DataFrame:
    out = []
    for r in rows:
        d = {rowkey: r}
        for per in periods:
            for h in hs:
                d[f"{per} h{h}"] = _cell(T, ci, n, **{rowkey: r, "period": per, "h": h, **kw})
        out.append(d)
    return pd.DataFrame(out)


def write_report(path: Path | None = None) -> str:
    with open(RES / "logs" / f"{ARM}_tables.pkl", "rb") as fh:
        R = pickle.load(fh)
    acc, cal, una, votes, plc, B, bo, ctl, epi, C = (R[k] for k in ("acc", "cal", "una", "votes", "placebo", "bar", "boot", "controls", "epi", "candidates"))
    rep, inc, hit, lab, bench, rec, J = R["report"], R["incremental"], R["hit"], R["labelcorr"], R["bench"], R["reconcile"], R["latest"]
    final = R["stream_name"]
    fst, fk = final.split("_k")[0], int(final.split("_k")[1])
    rules_ = [c[0] for c in CANDIDATES]
    main = acc[(acc.lib == "main") & (acc.metric == "euclid") & (acc.model == "knn") & (acc.call == "all")]
    L = []
    A = L.append
    A("# Arm U - analogs: 'history rhymes' nearest-neighbour forecasting of EUR/USD (round 6)\n")
    A("Code `src/eurusd/arms/analogs.py` (`run(cost_pips=1.2)`, `explain(date=None)`; `PYTHONPATH=src python -m eurusd.arms.analogs` runs everything "
      "incl. controls and this report in about four minutes on one core; `... analogs report` rebuilds this file; `... analogs explain [date]` prints the "
      "analogs of a date). Outputs in `experiments/results/arms/`: `analogs_positions.parquet` (daily weekly-tranche book of the final rule: `pos`, `fwd_bp`, "
      "`net_bp`), `analogs_report.csv` (protocol table, 12 candidates, `variant`, `final`), `analogs_accuracy.csv` (every state x k x horizon x metric x "
      "mode x period), `analogs_calibration.csv` (reliability tables and the near-unanimous calls), `analogs_votes.csv` (extra-vote tests and the timing "
      "placebo), `analogs_bar.csv`, `analogs_paired_bootstrap.csv`, `analogs_controls.csv` (farthest / random / shuffled / look-ahead), "
      "`analogs_episodes.csv`, `analogs_candidates.csv`, `analogs_reference_sign_rules.csv`, `analogs_label_corr.csv`, `analogs_incremental.csv`, "
      "`analogs_reconciliation.csv`, `analogs_latest.json` (output of `explain()` for the latest session). The module docstring (states, analog rule, "
      "12 candidates, selection rule) was written before the first result.\n")
    A("## Verdict\n")
    A(VERDICT_MD.strip() + "\n")
    A("## Protocol notes, deviations, additions after the first run\n")
    A(NOTES_MD.strip().format(**R["info"]["ea2y_proxy"], off_u=R["info"]["long_unemp_offset_pp"]) + "\n")
    # ---------------------------------------------------------------- 1 states
    A("## 1. State vectors and data\n")
    A(STATES_MD.strip() + "\n")
    ex = R.get("pca", {})
    k26 = [k for k in ex if "2026" in k and "main" in k]
    if k26:
        A(f"PCA of state E (loadings fitted before each test year): the first {N_PC} components explain "
          f"{', '.join(_pc(v) for v in ex[k26[0]]['explained'])} % of the variance of the 24 standardised dimensions in the 2026 window "
          f"({_pc(sum(ex[k26[0]]['explained']))} % together).\n")
    A("First session with a forecast (1260 eligible analog sessions): " + ", ".join(f"{k} {v}" for k, v in R["first_forecast"].items())
      + " (test years start in 2006; F needs the store's 2y-spread change, which starts 2004-10).\n")
    # ---------------------------------------------------------------- 2 reconciliation
    A("## 2. Reconciliation of the agreement rule with arm N\n")
    A("Rebuilt on this arm's frame and evaluator (2010-26); `n` and accuracy against the published cells of reports/arm_selective.md.\n")
    A(_md(rec.round(4)) + "\n")
    # ---------------------------------------------------------------- 3 standalone
    A("## 3. Standalone accuracy of the analog call sign(P - 0.5)\n")
    A("Accuracy in %, number of decisions in brackets. Main library (1999+), Euclidean distance, plain share of the k analogs. A call is made whenever "
      "P is not exactly 0.5 (about 12 non-overlapping 21-session decisions a year, 6 at 42 sessions, 4 at 63).\n")
    A("**Non-overlapping decisions** (greedy stream; 2006-26 from the stream started in 2006, the others from the stream started in 2010)\n")
    A(_md(_grid(main[main["mode"] == "nonoverlap"], rules_, "rule", ("2006-26", "2010-26", "2016-26", "2023-26"))) + "\n")
    A("**The same with 95 % Wilson intervals, 2010-26, and decisions per year**\n")
    t = _grid(main[main["mode"] == "nonoverlap"], rules_, "rule", ("2010-26",), ci=True)
    for h in HORIZONS:
        t[f"dec/yr h{h}"] = [f"{_get(main, 'dec_per_year', rule=r, mode='nonoverlap', period='2010-26', h=h):.1f}" for r in rules_]
    t["share long h21"] = [_pc(_get(main, "share_long", rule=r, mode="nonoverlap", period="2010-26", h=21)) for r in rules_]
    A(_md(t) + "\n")
    A("**Weekly decisions** (every 5th session; overlapping holds, so the effective n is about n x 5 / h)\n")
    A(_md(_grid(main[main["mode"] == "weekly"], rules_, "rule", ("2006-26", "2010-26", "2016-26", "2023-26"), n=False)) + "\n")
    A("**Monthly clock** (last session of each month)\n")
    A(_md(_grid(main[main["mode"] == "monthly"], rules_, "rule", ("2006-26", "2010-26", "2016-26", "2023-26"), n=False)) + "\n")
    A("**Reference: the plain SIGN of the same inputs** (existing signals, same evaluator, non-overlapping; not new trials)\n")
    refs = list(bench["reference"].unique())
    A(_md(_grid(bench[bench["mode"] == "nonoverlap"], refs, "reference", ("2006-26", "2010-26", "2016-26", "2023-26"))) + "\n")
    A("Weekly grid:\n")
    A(_md(_grid(bench[bench["mode"] == "weekly"], refs, "reference", ("2006-26", "2010-26", "2016-26", "2023-26"), n=False)) + "\n")
    # ---------------------------------------------------------------- 4 calibration
    A("## 4. Calibration: does '70 % of the analogs rose' come true 70 % of the time?\n")
    A("Weekly grid, 2006-26 (F: 2009-11 onwards). `Brier` of the analog P(up) against 0.250 for 'always 50 %' and against the library base rate "
      "(share of rising outcomes among all eligible library sessions); `slope` = regression of the outcome on P (1 = calibrated, 0 = no information, "
      "negative = anti-informative); `stated` = mean of max(P, 1-P) on the calls, `realised` = their accuracy.\n")
    c0 = cal[(cal.lib == "main") & (cal.metric == "euclid") & (cal.period == "2006-26")]
    rows = []
    for nm, st, k in CANDIDATES:
        for model, lab_ in (("knn", "share of analogs"),):
            r = {"rule": nm}
            for h in HORIZONS:
                q = dict(state=st, k=k, model=model, h=h, bin="ALL")
                r[f"Brier h{h}"] = f"{_get(c0, 'brier', **q):.3f}"
                r[f"base-rate Brier h{h}"] = f"{_get(c0, 'brier_base_rate', **q):.3f}"
                r[f"slope h{h}"] = f"{_get(c0, 'calib_slope', **q):+.2f}"
                r[f"stated / realised h{h}"] = f"{_pc(_get(c0, 'mean_conf', **q))} / {_pc(_get(c0, 'accuracy', **q))}"
            rows.append(r)
    A(_md(pd.DataFrame(rows)) + "\n")
    bins = ["<20", "20-30", "30-40", "40-50", "=50", "50-60", "60-70", "70-80", ">=80"]
    for h in (21, 63):
        A(f"**Reliability, k = 20, {h} sessions**: realised share of rises in % (number of weekly forecasts) by the stated P(up)\n")
        rows = []
        for st in STATES:
            r = {"state": st}
            for b in bins:
                q = dict(state=st, k=20, model="knn", h=h, bin=b)
                nn_ = _get(c0, "n", **q)
                r[f"P {b}"] = f"{_pc(_get(c0, 'share_up', **q))} ({int(nn_)})" if np.isfinite(nn_) else ""
            rows.append(r)
        pool = c0[(c0.k == 20) & (c0.model == "knn") & (c0.h == h)]
        for lab_, sts in (("A+B+C+E pooled", list("ABCE")), ("all six pooled", list(STATES))):
            r = {"state": lab_}
            for b in bins:
                x = pool[(pool.bin == b) & pool.state.isin(sts)]
                r[f"P {b}"] = f"{_pc((x.share_up * x.n).sum() / x.n.sum())} ({int(x.n.sum())})" if len(x) and x.n.sum() else ""
            rows.append(r)
        A(_md(pd.DataFrame(rows)) + "\n")
    A("**Accuracy by stated confidence max(P, 1-P), k = 20, weekly grid 2006-26, pooled over states** (hits / calls)\n")
    rows = []
    for lab_, sts in (("A, B, C, E (the new information)", list("ABCE")), ("D (positioning)", ["D"]), ("F (agreement inputs)", ["F"])):
        for h in HORIZONS:
            r = {"states": lab_, "h": h}
            for b in ("conf50-60", "conf60-70", "conf70-80", "conf>=80"):
                x = c0[(c0.k == 20) & (c0.model == "knn") & (c0.h == h) & (c0.bin == b) & c0.state.isin(sts)]
                r[b.replace("conf", "stated ")] = f"{_pc((x.share_up * x.n).sum() / x.n.sum())} ({int(x.n.sum())})" if len(x) and x.n.sum() else ""
            rows.append(r)
    A(_md(pd.DataFrame(rows)) + "\n")
    kk = cal[(cal.model == "kernel") & (cal.period == "2006-26") & (cal.bin == "ALL")]
    ee = cal[(cal.model == "knn_episode_level") & (cal.lib == "main") & (cal.period == "2006-26") & (cal.bin == "ALL") & (cal.k == 20)]
    rows = []
    for st in STATES:
        r = {"state": st}
        for h in HORIZONS:
            r[f"kernel Brier / slope / acc h{h}"] = f"{_get(kk, 'brier', state=st, h=h):.3f} / {_get(kk, 'calib_slope', state=st, h=h):+.2f} / {_pc(_get(kk, 'accuracy', state=st, h=h))}"
            r[f"episode-level Brier / slope / acc h{h}"] = f"{_get(ee, 'brier', state=st, h=h):.3f} / {_get(ee, 'calib_slope', state=st, h=h):+.2f} / {_pc(_get(ee, 'accuracy', state=st, h=h))}"
        rows.append(r)
    A("**Kernel-weighted probability and the episode-level probability (each episode one vote, k = 20)**, weekly grid 2006-26\n")
    A(_md(pd.DataFrame(rows)) + "\n")
    # ---------------------------------------------------------------- 5 unanimity
    A("## 5. Near-unanimous analogs (>= 70 % / >= 80 % one way)\n")
    A("k = 20 (with k = 40 unanimity is rare: see `analogs_calibration.csv`). Accuracy in % (decisions) and decisions per year on the non-overlapping "
      "stream; weekly-grid accuracy (calls) next to it; `epi` = mean number of independent episodes behind those calls.\n")
    u = una[(una.lib == "main") & (una.metric == "euclid") & (una.k == 20)]
    for per in ("2010-26", "2006-26"):
        rows = []
        for st in STATES:
            for thr in ("p>=70", "p>=80"):
                r = {"state": st, "call": thr}
                for h in HORIZONS:
                    q = dict(state=st, call=thr, h=h, period=per)
                    r[f"h{h} non-overlapping"] = _cell(u, True, True, mode="nonoverlap", **q)
                    d = _get(u, "dec_per_year", mode="nonoverlap", **q)
                    r[f"h{h} dec/yr"] = f"{d:.1f}" if np.isfinite(d) else ""
                    r[f"h{h} weekly"] = _cell(u, False, True, mode="weekly", **q)
                r["epi"] = f"{_get(u, 'mean_n_epi', state=st, call=thr, h=21, period=per, mode='weekly'):.1f}"
                rows.append(r)
        A(f"**{per}**\n")
        A(_md(pd.DataFrame(rows)) + "\n")
    # ---------------------------------------------------------------- 6 honesty
    A("## 6. Honesty checks specific to analogs\n")
    A("### (i) Independent episodes behind a forecast\n")
    A("Weekly forecasts 2006-26. An episode = chosen analogs chained with gaps of at most 63 sessions.\n")
    e = epi.copy()
    e["rule"] = e["state"] + "_k" + e["k"].astype(str) + np.where(e["lib"] == "long", " (long library)", "")
    cols = ["rule", "mean_n_epi", "median_n_epi", "p10_n_epi", "mean_distinct_years", "median_analog_age_years", "mean_dist_1", "mean_dist_k",
            "h21_share_p>=70", "h21_n_epi_when_p>=70", "h21_share_episode_p>=70", "h63_share_p>=70", "h63_share_episode_p>=70"]
    A(_md(e[cols].round(2)) + "\n")
    A("`share_p>=70` = share of forecasts where at least 70 % of the analogs agree; `share_episode_p>=70` = the same when each episode has one vote. "
      "`mean_dist_1` / `mean_dist_k` = Euclidean distance (in standard deviations) of the nearest and of the k-th analog.\n")
    A("### (ii)-(iv) Distance must matter; shuffled outcomes; look-ahead\n")
    ctl = ctl.copy()
    ctl["ctl"] = ctl["control"].str.replace(r"_\d$", "", regex=True)
    order = [("nearest", "nearest k (the method)"), ("ranks_21_40", "ranks 21-40"), ("random", "random k (mean of 5 draws)"), ("farthest", "farthest k"),
             ("library_base_rate", "library base rate"), ("shuffled_outcomes", "shuffled outcomes (mean of 5)"),
             ("lookahead_future_allowed_embargo63", "look-ahead: future analogs, 63-session embargo"), ("lookahead_no_embargo", "look-ahead: no embargo"),
             ("library_frozen_at_year_start", "library frozen at year start (strict protocol)"), ("state_stale_21", "state 21 sessions stale")]
    for mode in ("weekly", "nonoverlap"):
        for h in HORIZONS:
            x = ctl[(ctl["mode"] == mode) & (ctl.period == "2006-26") & (ctl.h == h) & (ctl.k.isin([0, 20]))]
            pv = x.pivot_table(index="ctl", columns="state", values="accuracy", aggfunc="mean")
            t = pd.DataFrame([{"control (k = 20)": lab_, **{st: _pc(pv.loc[key, st], 1) if key in pv.index else "" for st in STATES}} for key, lab_ in order])
            A(f"**{mode}, {h} sessions, 2006-26** (accuracy in %)\n")
            A(_md(t) + "\n")
    rs = ctl[(ctl["mode"] == "weekly") & (ctl.period == "2006-26") & (ctl.ctl == "random") & (ctl.k == 20)].groupby(["state", "h"]).accuracy.agg(["min", "max"])
    A("Range of the five random draws (weekly, k = 20): " + "; ".join(f"{st} h{h} {_pc(r['min'])}-{_pc(r['max'])}" for (st, h), r in rs.iterrows()) + ".\n")
    A("### Label in disguise? Correlation of every state dimension with the forward returns (all sessions 1999+)\n")
    A(_md(lab.round(3)) + "\n")
    # ---------------------------------------------------------------- 7 votes
    A("## 7. As an EXTRA VOTE on the agreement rule\n")
    A("Form: agreement rule AND the analog call for the same horizon points the same way. Non-overlapping decisions; accuracy of the agreement rule alone, "
      "of the vote rule, the gain in points, the vote rule's decisions (per year).\n")
    Bi = B.set_index("candidate")
    for per in ("2010-26", "2016-26", "2023-26"):
        rows = []
        for nm in rules_:
            r = {"candidate": nm}
            for h in HORIZONS:
                r[f"h{h} agree3"] = _pc(Bi.loc[nm, f"agree3_{h}_{per}"], 1)
                r[f"h{h} vote"] = _pc(Bi.loc[nm, f"vote_{h}_{per}"], 1)
                r[f"h{h} gain"] = f"{100 * Bi.loc[nm, f'gain_{h}_{per}']:+.1f}"
                r[f"h{h} n (per yr)"] = f"{int(Bi.loc[nm, f'vote_n_{h}_{per}'])} ({Bi.loc[nm, f'vote_dpy_{h}_{per}']:.1f})"
            rows.append(r)
        A(f"**(a) {per}**\n")
        A(_md(pd.DataFrame(rows)) + "\n")
    rows = []
    for nm in rules_:
        r = {"candidate": nm}
        for per in ("2010-26", "2016-26"):
            for h in HORIZONS:
                r[f"{per} h{h}"] = f"{_pc(Bi.loc[nm, f'extend_{h}_{per}'], 1)} ({int(Bi.loc[nm, f'extend_n_{h}_{per}'])})"
        rows.append(r)
    A("**(b) Coverage extension: accuracy of the analog call when the three old signals do NOT agree** (non-overlapping, decisions in brackets)\n")
    A(_md(pd.DataFrame(rows)) + "\n")
    x = bo[bo.period.isin(["2010-26", "2016-26"])]
    rows = []
    for nm in rules_:
        r = {"candidate": nm}
        for per in ("2010-26", "2016-26"):
            for h in HORIZONS:
                q = x[(x.rule == nm) & (x.period == per) & (x.h == h)].iloc[0]
                r[f"{per} h{h}"] = f"{100 * q['diff']:+.1f} [{100 * q['lo']:+.1f}, {100 * q['hi']:+.1f}]"
        rows.append(r)
    A("**(c) Paired difference on the weekly grid** (vote rule minus agreement rule, points, 95 % circular block bootstrap)\n")
    A(_md(pd.DataFrame(rows)) + "\n")
    rows = []
    for nm in rules_:
        r = {"candidate": nm}
        for per in ("2010-26", "2016-26"):
            for h in (21, 42):
                r[f"{per} h{h}: gain / +63 / +126"] = (f"{100 * Bi.loc[nm, f'gain_{h}_{per}']:+.1f} / {100 * Bi.loc[nm, f'placebo63_gain_{h}_{per}']:+.1f} / "
                                                       f"{100 * Bi.loc[nm, f'placebo126_gain_{h}_{per}']:+.1f}")
        for c_ in ("pass_gain_3pts", "pass_6_per_year", "pass_2023_not_worse", "pass_placebo", "PASS_ROUND5_BAR"):
            r[c_.replace("pass_", "").replace("PASS_", "")] = "yes" if Bi.loc[nm, c_] else "no"
        rows.append(r)
    A("**Timing placebo and the Round 5 bar** (vote gain with the live call / the call 63 sessions stale / 126 sessions stale)\n")
    A(_md(pd.DataFrame(rows)) + "\n")
    v70 = votes[(votes.signal == "call_p>=70") & (votes.test == "vote_agree") & (votes["mode"] == "nonoverlap")]
    rows = []
    for nm in rules_:
        r = {"candidate": nm}
        for per in ("2010-26", "2016-26"):
            for h in HORIZONS:
                r[f"{per} h{h}"] = _cell(v70, False, True, rule=nm, period=per, h=h)
        rows.append(r)
    A("**Agreement rule AND near-unanimous analogs (>= 70 %) the same way** (non-overlapping accuracy, decisions)\n")
    A(_md(pd.DataFrame(rows)) + "\n")
    ps = plc[(plc.test == "standalone") & (plc["mode"] == "nonoverlap") & (plc.period == "2010-26")]
    rows = []
    for nm in rules_:
        r = {"candidate": nm}
        for h in HORIZONS:
            r[f"h{h}: live / +63 / +126"] = (f"{_pc(_get(main, 'accuracy', rule=nm, mode='nonoverlap', period='2010-26', h=h), 1)} / "
                                             f"{_pc(_get(ps, 'accuracy', rule=nm, signal='call+63', h=h), 1)} / {_pc(_get(ps, 'accuracy', rule=nm, signal='call+126', h=h), 1)}")
        rows.append(r)
    A("**Standalone timing placebo** (non-overlapping accuracy 2010-26 of the live call and of the call made 63 / 126 sessions stale)\n")
    A(_md(pd.DataFrame(rows)) + "\n")
    # ---------------------------------------------------------------- 8 final
    A("## 8. Selection by the declared rule and the record of the pick\n")
    cc = C[["candidate", "n_2006-15", "dec_per_year_2006-15", "accuracy_2006-15", "lo_2006-15", "hi_2006-15", "net_bp_2006-15", "share_long_2006-15", "eligible", "final"]].copy()
    cc.columns = ["candidate", "n 2006-15", "dec / yr", "accuracy", "Wilson lo", "Wilson hi", "net bp / decision", "share long", "eligible", "final"]
    A("Non-overlapping 21-session decisions 2006-2015 (F can forecast from 2009-11 only):\n")
    A(_md(cc.round(3)) + "\n")
    A(f"**Final: `{final}`** ({R['final_status']}).\n")
    fm = main[main.rule == final]
    rows = []
    for mode in ("nonoverlap", "weekly", "monthly"):
        for per in ("2006-15", "2010-26", "2016-26", "2023-26"):
            r = {"mode": mode, "period": per}
            for h in HORIZONS:
                r[f"h{h}"] = _cell(fm, True, True, mode=mode, period=per, h=h)
                r[f"h{h} net bp"] = f"{_get(fm, 'net_bp', mode=mode, period=per, h=h):+.0f}"
            rows.append(r)
    A(_md(pd.DataFrame(rows)) + "\n")
    by = R["final_by_year"]
    pv = by.pivot(index="year", columns="h", values="right").astype(int).astype(str) + " / " + by.pivot(index="year", columns="h", values="n").astype(int).astype(str)
    pv.columns = [f"right / n, h{h}" for h in pv.columns]
    A("By year (non-overlapping stream started in 2010):\n")
    A(_md(pv.reset_index()) + "\n")
    A("**Protocol table (weekly-tranche books at 1.2 pips, net Sharpe)**\n")
    x = rep[rep.period.isin(["2010-2015", "2016-2022", "2010-2026", "2016-2026", "2023-2026"])]
    pv = x.pivot(index="variant", columns="period", values="sharpe")[["2010-2015", "2016-2022", "2010-2026", "2016-2026", "2023-2026"]].round(2)
    tt = x[x.period == "2010-2026"].set_index("variant")
    pv["t 2010-26"] = tt["t"].round(2)
    pv["deflated-Sharpe p"] = tt["deflated_sharpe_p"].round(2)
    pv["final"] = ["FINAL" if v == final else "" for v in pv.index]
    A(_md(pv.reset_index()) + "\n")
    A("Hit rate of the delivered daily stream (active sessions):\n")
    A(_md(hit.round(3)) + "\n")
    ii = inc[inc.period.isin(["2010-2026", "2016-2026", "2023-2026"])][["combo", "period", "sharpe", "t"]].round(3)
    A("**Daily incremental test** (EW combination, walk-forward weights):\n")
    A(_md(ii) + "\n")
    A(f"Daily P&L correlation of the final stream with `weak_signals` {inc['corr_weak_signals'].iloc[0]:.2f}, with `regime_trend` {inc['corr_regime_trend'].iloc[0]:.2f}.\n")
    # ---------------------------------------------------------------- 9 diagnostics
    A("## 9. Diagnostics (never selected from)\n")
    A("**Mahalanobis distance and the kernel-weighted vote** (non-overlapping accuracy in %, 2010-26; Euclidean k-NN repeated for comparison)\n")
    d = acc[(acc.lib == "main") & (acc.call == "all") & (acc["mode"] == "nonoverlap") & (acc.period == "2010-26")]
    rows = []
    for st in STATES:
        for k in KS:
            r = {"state": st, "k": k}
            for h in HORIZONS:
                r[f"h{h} Euclid"] = _pc(_get(d, "accuracy", state=st, k=k, metric="euclid", model="knn", h=h), 1)
                r[f"h{h} Mahalanobis"] = _pc(_get(d, "accuracy", state=st, k=k, metric="mahal", model="knn", h=h), 1)
                r[f"h{h} kernel"] = _pc(_get(d, "accuracy", state=st, k=K_KERNEL, metric="euclid", model="kernel", h=h), 1) if k == K_KERNEL else ""
            rows.append(r)
    A(_md(pd.DataFrame(rows)) + "\n")
    A("**Long library (analogs from 1990, synthetic DEM euro before 1999, proxies as stated) and the other-era replication 1997-2005**\n")
    lg = acc[(acc.lib == "long") & (acc.call == "all") & (acc["mode"] == "nonoverlap")]
    rows = []
    for st in LONG_COLS:
        for k in KS:
            r = {"state": st, "k": k}
            for per in ("1997-05", "2006-26", "2010-26"):
                for h in HORIZONS:
                    r[f"{per} h{h}"] = _cell(lg, False, per == "1997-05", state=st, k=k, period=per, h=h)
            for h in HORIZONS:
                r[f"main lib 2010-26 h{h}"] = _pc(_get(main, "accuracy", state=st, k=k, mode="nonoverlap", period="2010-26", h=h), 1)
            rows.append(r)
    A(_md(pd.DataFrame(rows)) + "\n")
    # ---------------------------------------------------------------- 10 explain
    A("## 10. `explain(date)`: the current reading\n")
    A(f"`explain()` for the session closing {J['asof_session_close']} (EUR/USD {J['eurusd_close']:.4f}); full output in `analogs_latest.json`. "
      "For each state: the state today (value, z against the library before this year), the 10 nearest analog dates with the 21 / 42 / 63-session "
      "return that followed, P(up) from the 10 / 20 / 40 nearest with the number of independent episodes and a Wilson interval on EPISODES, the kernel "
      "probability, the library base rate, the episode list, and the out-of-sample record of that state's call.\n")
    rows = []
    for st, b in J["states"].items():
        if not b.get("available"):
            continue
        r = {"state": f"{st} {b['name']}"}
        for h in HORIZONS:
            f = b["forecast"][f"{h}_sessions"]["k20"]
            r[f"P(up) h{h} (k=20)"] = f"{_pc(f['p_up'])} % [{_pc(f['wilson95_on_episodes'][0])}-{_pc(f['wilson95_on_episodes'][1])}]"
        r["episodes"] = b["forecast"]["21_sessions"]["k20"]["n_episodes"]
        o = b.get("out_of_sample_record_k20_2010_26", {})
        r["OOS accuracy of this call 2010-26 (21 / 42 / 63)"] = " / ".join(_pc(o.get(f"{h}_sessions", {}).get("accuracy_non_overlapping", np.nan)) for h in HORIZONS)
        rows.append(r)
    A(_md(pd.DataFrame(rows)) + "\n")
    for st in dict.fromkeys(["B", "A", fst]):
        b = J["states"][st]
        if not b.get("available"):
            continue
        A(f"**The 10 most similar moments, state {st} ({b['name']})** - today: " + "; ".join(f"{v['label']} {v['value']}" for v in b["today"].values()) + "\n")
        t = pd.DataFrame([{"rank": a["rank"], "analog date": a["date"], "distance": a["distance"], "EUR/USD then": a["eurusd_close"],
                           "next 21 s. %": a["ret21_pct"], "next 42 s. %": a["ret42_pct"], "next 63 s. %": a["ret63_pct"]} for a in b["analogs"]])
        A(_md(t) + "\n")
        A("Episodes behind the 20 nearest: " + "; ".join(f"{e_['from']}..{e_['to']} ({e_['n_analogs']})" for e_ in b["episodes_k20"]) + ".\n")
    A(TAIL_MD.strip() + "\n")
    txt = "\n".join(L)
    path = path or (REPORTS / f"arm_{ARM}.md")
    path.write_text(txt)
    return txt


VERDICT_MD = """
(verdict pending)
"""

NOTES_MD = """
(notes pending) {first_aaa} {offset_pp:.3f} {proxy_rmse_first250_pp:.3f} {off_u:.2f}
"""

STATES_MD = """
(states pending)
"""

TAIL_MD = """
(tail pending)
"""


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "full"
    if arg == "explain":
        print(json.dumps(explain(sys.argv[2] if len(sys.argv) > 2 else None), indent=1))
    elif arg == "report":
        write_report()
    else:
        pos, rep = run()
        R = run.last
        print(R["candidates"].round(3).to_string())
        print("final:", R["final"], "|", R["final_status"])
        write_report()
