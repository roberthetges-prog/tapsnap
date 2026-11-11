"""Arm S ("regime_dependence"): is the post-2023 fade of the surviving EUR/USD signals noise, decay or regime?

Diagnostic first, tradeable second. EVERYTHING IN THIS DOCSTRING WAS WRITTEN BEFORE ANY RESULT OF THIS ARM WAS
COMPUTED (the only numbers known in advance were the published records of the agreement rule in reports/arm_selective.md).

COMPONENTS (direction d_t in {-1, 0, +1} at each NY close of the feature store; + = long EUR/USD)
  cot     sign(cot_z52)                              speculative positioning, from 2003 (H.10 extension from 2000)
  spread  sign(d_spread2y_20)                        20-day trend of the EA-US 2y spread, from 2004-10
  house   sign(house score)                          weak_signals t-stat combination, walk-forward (selective.house_score_wf,
                                                     test years 2006..2026; identical to the published score from 2010)
  dec     +1 on sessions whose next session closes in December (daily stream); ONE decision a year, at the last
          November close (21 sessions = the December hold; the 42-session figure runs into January and is shown only
          for completeness)
  eqrel   sign(-spx_minus_sx5e_20)                   relative equity momentum, from 2007-04
  agree3  sign(house) when cot, spread and house agree, else silent (the agreement rule of arm N, rebuilt with the
          selective helpers and reconciled against its published record before anything else is read)
Measures: (a) directional accuracy at 21 and 42 sessions on the NON-OVERLAPPING greedy stream (selective.seq_idx logic,
  plain Wilson interval) and on weekly decisions (every 5th session, overlapping; shown next to it, never used for an
  interval); (b) net Sharpe of the daily-sign stream (position = d_t every session, wf.pnl_from_positions, 1.2 pips per
  unit turnover, zero days included); for agree3 also the weekly-tranche book of arm N (the stacking stream).

(1) POWER. Null: the effect of the base window is unchanged. Circular block bootstrap of the base window's sessions
  (each session carries its own signal, direction and realised h-session outcome), block 126 sessions, pseudo-samples of
  the SAME number of sessions as the observed window, the same greedy non-overlapping (or weekly) decision rule run on
  each pseudo-sample; 5,000 draws. p = share of draws with accuracy (Sharpe) <= the observed one. Headline: base
  2010-2022 -> observed 2023-2026. Also reported: base 2016-2022 (not a selection window) -> 2023-26, and the
  selection-step tests base 2010-15 -> 2016-26 / 2016-22 and 2006-15 -> 2016-26. Next to each p: the 5 % critical value
  under the unchanged null and the probability that a process with NO edge (coin for accuracy, de-meaned base P&L for
  Sharpe) would fall below it (= the power of this sample to see a complete loss of the edge), and the analytic
  p-value under "a true 0.5-Sharpe process" (accuracy Phi(0.5 sqrt(h/252)), Sharpe s.e. 1/sqrt(years)).
  Sensitivity: blocks of 63 and 252 sessions. Verdict words fixed in advance: p > 0.10 "not distinguishable from noise",
  0.05-0.10 "weak", < 0.05 "distinguishable".

(2) DECAY. Rolling 3- and 5-calendar-year windows (stepped yearly) of Sharpe and accuracy for every component from its
  first year; eras: 2000-02 (before every selection window; positioning and December only, Fed H.10 noon prices),
  2003-09, 2010-15, 2016-22, 2023-26, 2003-15 (round 1 chose its rules on it), 2016-26. Selection windows: round 1
  2003-2015 (validation 2016-22, holdout 2023-26), round 2 walk-forward variants chosen on 2010-2015. Step statistic
  z = (SR_in - SR_after) / sqrt((1 + SR_in^2/2)/years_in + (1 + SR_after^2/2)/years_after). Signature of mining: a step
  down right after 2015 that is NOT repeated at 2022/23 and is absent in pre-selection data. Signature of decay: a
  monotone decline through 2016-22 into 2023-26.

(3) PRE-DECLARED REGIMES (every label uses data stamped <= close date - 1 calendar day unless a longer lag is stated)
  policy     LB    = ECB deposit rate <= 0.5 AND fed funds target (upper bound from 2008-12-16) <= 0.5
             HIKE  = not LB, at least one bank's last move within 365 days was up and no bank's was down
             CUT   = not LB, at least one down and none up
             OTHER = not LB, one up and one down, or no move by either in 365 days
             (ECB move = change of deposit rate + main refinancing rate, Fed move = change of the target)
  div_level  |deposit rate - fed target| ABOVE / BELOW its expanding median since 1999 (median through the previous day)
  div_change the same gap vs 182 calendar days earlier: WIDER / NARROWER / SAME
  ratevol    60-day standard deviation of daily changes of the US 2y yield (DGS2): LOW / MID / HIGH by the expanding
             terciles of its own history since 1999 (through the previous observation; needs 750 observations)
  dollar     Fed broad dollar index (DTWEXBGS, from 2006; 7-day lag for the weekly H.10 release) ABOVE / BELOW its
             200-observation average; defined from October 2006
  inflation  US CPI (CPIAUCSL) 12-month change > 3 % HIGH / else LOW, usable 60 days after the month stamp
  crowding   |cot_z52| < 1 / 1-2 / > 2
  trend_rel  call direction vs sign(dist_sma200_atr): WITH / COUNTER (component-specific)
  Tables: for every component, regime variable and class: non-overlapping accuracy at 21 / 42 sessions (greedy stream
  of "component speaks AND class holds", stream started 2006) with n and Wilson interval, weekly accuracy, mean net bp,
  and the daily-stream Sharpe on the class's sessions; 2006-26 and 2006-15 / 2016-26.
  SCREEN (fixed now): a class is FAVOURABLE (UNFAVOURABLE) for a component if in BOTH halves its non-overlapping
  accuracy is at least 5 points above (below) that of the component's calls outside the class at BOTH 21 and 42
  sessions, with >= 10 non-overlapping 21-session decisions inside and outside the class in each half, and the daily
  Sharpe inside the class above (below) the Sharpe outside it in both halves. A regime variable passes for the
  agreement rule if one of its classes is favourable or unfavourable. Chance control: all regime labels rotated
  jointly against the calls by a random offset of at least one year (1,000 rotations): how many classes pass, and
  the rotation p-value of the largest consistent gap.

(4) TRADEABLE TEST, only for regime variables that pass (3) for agree3; at most 8 single-variable rules + 1
  conjunction = 9 candidates (cap 12). Walk-forward rule for variable V: for test year Y, among weekly agree3 decisions
  from 2006 whose 21-session label is known before Y-01-01, class c is MUTED iff it holds >= 40 such decisions, the
  other classes hold >= 40, and its 21-session accuracy is >= 5 points below theirs; the rule speaks when agree3 speaks
  and the session's class is not muted (undefined class = speak). Conjunction = muted by any passing variable.
  Evaluation (Round 5): non-overlapping accuracy at 21 / 42 sessions, decisions a year, weekly accuracy, tranche-book
  Sharpe, paired block-bootstrap difference against the unconditional rule (same pseudo-samples for both, block 126,
  2,000 draws), 2010-26 / 2016-26 / 2023-26.
  FINAL (fixed now): among candidates with >= 6 non-overlapping 21-session decisions a year in 2010-2015, the highest
  Wilson lower bound of the 2010-2015 non-overlapping 21-session accuracy. It is ADOPTED only if it beats the
  unconditional rule by >= 3 points at 21 and 42 sessions in both 2010-26 and 2016-26 with >= 6 decisions a year
  (21-session stream), is not worse in 2023-26, and the shuffled-regime placebo does not match its gain. Otherwise,
  and if nothing passes (3), the positions file holds the UNCONDITIONAL agreement rule, flagged conditional = False.
  If nothing passes (3), the walk-forward machinery is exercised once on the variable with the largest consistent gap
  ("near miss"), labelled DIAGNOSTIC, never eligible as final, so that the leak checks have a subject.
  Caveat stated in advance: the walk-forward protects the choice of the muted CLASS, not the choice of the VARIABLE,
  which the screen makes on the whole sample. The full-pipeline rotation placebo (screen + rule) measures that.
Leak checks: regime labels shuffled (i.i.d. permutation and block rotation; gain must vanish); regime labels lagged
  21 / 63 / 126 sessions (a slow regime should not care); look-ahead controls (muted classes chosen with hindsight on
  the test years; an "oracle" regime built from the future outcome, which the harness must expose as ~100 %; the
  agreement rule with features taken 21 sessions ahead); outcomes rotated against the calls (accuracy -> ~50 %).

ADDED AFTER THE FIRST RUN (labelled as such in the report; none of it changes the screen, the candidate declared above
or the final-selection rule):
  * power: p-values with the bootstrap distribution re-centred on what a true 0.5-Sharpe process gives, and a JOINT
    test over the components (same pseudo-samples for all: the pooled mean and the largest standardised drop), because
    the first run showed the fade is not uniform and picking the worst component afterwards is a selection;
  * the non-overlapping accuracy of one window moves by up to 9 points with the phase of the greedy stream (positioning
    2023-26: 47 % or 55 % on the same 47 decisions shifted a few sessions), so the weekly statistic with the block
    bootstrap is shown as the primary power test and the non-overlapping one next to it;
  * screen: the same rotation placebo for the SHARPE concentration (weakest of the two halves' Sharpe gaps);
  * "mix" table: what the 2023-26 regime mix implies for 2023-26 if each class had kept its 2010-22 record;
  * candidate 2, `strict_<variable>`: the literal "speak only in favourable regimes" rule. For test year Y a class is
    FAVOURABLE iff it holds >= 40 weekly training decisions, the others hold >= 40 and its 21-session accuracy is >= 5
    points ABOVE theirs; the rule speaks only in favourable classes, and like the unconditional rule while no class
    qualifies. Post hoc (written after seeing that the declared rule muted NARROWER only while the P&L sits in WIDER);
    counted as a trial, judged against the same bar and its own full-pipeline placebo.
"""
from __future__ import annotations

import math
import sys
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pandas as pd
from numba import njit
from scipy.stats import binom, norm

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.arms import selective as SEL  # noqa: E402
from eurusd.featstore import MACRO, _align_lagged, _macro_series  # noqa: E402
from eurusd.wf import YEARS, _agg, pnl_from_positions, report  # noqa: E402

RES = ROOT / "experiments/results/arms"
REPORTS = ROOT / "reports"
ARM = "regime_dependence"
HS = (21, 42)
STEP = 5
BLOCK = 126
COMPONENTS = ("cot", "spread", "house", "dec", "eqrel", "agree3")
REGVARS = ("policy", "div_level", "div_change", "ratevol", "dollar", "inflation", "crowding", "trend_rel")
HALVES = (("2006-15", 2006, 2015), ("2016-26", 2016, 2026))
PERIODS3 = (("2006-26", 2006, 2026),) + HALVES
EVAL = (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026), ("2010-15", 2010, 2015))
ERAS = (("2000-02", 2000, 2002), ("2003-09", 2003, 2009), ("2010-15", 2010, 2015), ("2016-22", 2016, 2022), ("2023-26", 2023, 2026),
        ("2003-15", 2003, 2015), ("2016-26", 2016, 2026))
STEPS = (("2010-22", 2010, 2022, "2023-26", 2023, 2026), ("2016-22", 2016, 2022, "2023-26", 2023, 2026),
         ("2010-15", 2010, 2015, "2016-26", 2016, 2026), ("2010-15", 2010, 2015, "2016-22", 2016, 2022),
         ("2006-15", 2006, 2015, "2016-26", 2016, 2026))
GAP = 0.05           # screen: accuracy gap, both horizons, both halves
MIN_N = 10           # screen: non-overlapping 21-session decisions inside and outside the class, per half
MUTE_MIN = 40        # walk-forward: weekly training decisions needed inside and outside a class
BAR = 0.03           # Round 5 success bar
MIN_DEC_YR = 6.0


# ================================================================ numba kernels
@njit(cache=True)
def _greedy_idx(speak, h):
    out = np.empty(len(speak), np.int64)
    k = 0
    i = 0
    n = len(speak)
    while i < n:
        if speak[i]:
            out[k] = i
            k += 1
            i += h
        else:
            i += 1
    return out[:k]


@njit(cache=True)
def _draw_idx(idx, Tb, L):
    p = 0
    T = len(idx)
    while p < T:
        s = np.random.randint(0, Tb)
        for j in range(L):
            if p >= T:
                break
            idx[p] = (s + j) % Tb
            p += 1


@njit(cache=True)
def _boot_acc2(speakA, speakB, hit, h, T_out, L, reps, seed, weekly):
    """Circular block bootstrap of sessions; the same pseudo-sample feeds rule A and rule B. Returns acc and n of each."""
    np.random.seed(seed)
    Tb = len(hit)
    aA = np.full(reps, np.nan); aB = np.full(reps, np.nan)
    nA = np.zeros(reps); nB = np.zeros(reps)
    idx = np.empty(T_out, np.int64)
    for r in range(reps):
        _draw_idx(idx, Tb, L)
        for which in range(2):
            n = 0; hh = 0.0; i = 0
            while i < T_out:
                j = idx[i]
                sp = speakA[j] if which == 0 else speakB[j]
                if weekly:
                    if sp:
                        n += 1; hh += hit[j]
                    i += 5
                elif sp:
                    n += 1; hh += hit[j]; i += h
                else:
                    i += 1
            if which == 0:
                nA[r] = n
                if n > 0:
                    aA[r] = hh / n
            else:
                nB[r] = n
                if n > 0:
                    aB[r] = hh / n
    return aA, aB, nA, nB


@njit(cache=True)
def _boot_sharpe(x, T_out, L, reps, seed):
    np.random.seed(seed)
    Tb = len(x)
    out = np.full(reps, np.nan)
    idx = np.empty(T_out, np.int64)
    for r in range(reps):
        _draw_idx(idx, Tb, L)
        s = 0.0; s2 = 0.0
        for i in range(T_out):
            v = x[idx[i]]
            s += v; s2 += v * v
        m = s / T_out
        var = (s2 - T_out * m * m) / (T_out - 1)
        if var > 0:
            out[r] = m / math.sqrt(var) * math.sqrt(252.0)
    return out


@njit(cache=True)
def _boot_weekly_multi(speak, hit, T_out, L, reps, seed):
    """speak, hit: (K, Tb). Weekly-grid accuracy of K rules on the SAME pseudo-samples."""
    np.random.seed(seed)
    K, Tb = hit.shape
    out = np.full((reps, K), np.nan)
    idx = np.empty(T_out, np.int64)
    for r in range(reps):
        _draw_idx(idx, Tb, L)
        for k in range(K):
            n = 0; hh = 0.0; i = 0
            while i < T_out:
                j = idx[i]
                if speak[k, j]:
                    n += 1; hh += hit[k, j]
                i += 5
            if n > 0:
                out[r, k] = hh / n
    return out


@njit(cache=True)
def _boot_sharpe_multi(X, T_out, L, reps, seed):
    np.random.seed(seed)
    K, Tb = X.shape
    out = np.full((reps, K), np.nan)
    idx = np.empty(T_out, np.int64)
    for r in range(reps):
        _draw_idx(idx, Tb, L)
        for k in range(K):
            s = 0.0; s2 = 0.0
            for i in range(T_out):
                v = X[k, idx[i]]
                s += v; s2 += v * v
            m = s / T_out
            var = (s2 - T_out * m * m) / (T_out - 1)
            if var > 0:
                out[r, k] = m / math.sqrt(var) * math.sqrt(252.0)
    return out


# ================================================================ data
@dataclass
class Panel:
    index: pd.DatetimeIndex
    year: np.ndarray
    close: np.ndarray
    f1: np.ndarray
    F: dict
    ct: np.ndarray
    cost_bp: np.ndarray
    dirs: dict = field(default_factory=dict)
    speak: dict = field(default_factory=dict)
    net: dict = field(default_factory=dict)
    exists: dict = field(default_factory=dict)
    extra: dict = field(default_factory=dict)

    def add(self, name: str, d: np.ndarray, speak: np.ndarray | None = None, cost_pips: float = 1.2, exists: np.ndarray | None = None):
        d = np.nan_to_num(np.asarray(d, dtype=float))
        self.dirs[name] = d
        self.speak[name] = (d != 0) if speak is None else speak
        s = pd.Series(d, index=self.index)
        pnl = pnl_from_positions(s, pd.Series(self.f1, index=self.index), pd.Series(self.close, index=self.index), cost_pips=cost_pips)
        self.net[name] = pnl["net_bp"].values
        if exists is None:
            nz = np.flatnonzero(d != 0)
            exists = np.arange(len(d)) >= (nz[0] if len(nz) else len(d))
        self.exists[name] = exists


def _fwd(lc: np.ndarray, h: int) -> np.ndarray:
    f = np.full(len(lc), np.nan)
    f[:len(lc) - h] = (lc[h:] - lc[:-h]) * 1e4
    return f


def _dec_arrays(month_next: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    d = (month_next == 12).astype(float)
    first = (d == 1) & (np.r_[0.0, d[:-1]] == 0)        # the last November close
    return d, first


def load_panel(cost_pips: float = 1.2, shift: int = 0) -> Panel:
    """The feature-store panel with the six components. shift != 0 moves every signal input by that many sessions
    (negative = look-ahead, control only)."""
    D = SEL.load_data()
    ctx = SEL.make_ctx(D, cost_pips)
    if shift:
        ctx = ctx.shifted(shift)
    hs = SEL.house_score_wf(ctx, years=list(range(2006, 2027)))
    lc = np.log(D["close"].values)
    ct = D["close_time"].values.astype("datetime64[ns]").astype(np.int64)
    P = Panel(D.index, D.index.year.values, D["close"].values, D["fwd_1d"].values, {h: _fwd(lc, h) for h in HS}, ct,
              (cost_pips / D["close"]).values)
    G = ctx.G
    sg = np.sign(hs)
    cot, spr = np.sign(G["cot_z52"].values), np.sign(G["d_spread2y_20"].values)
    eq = np.sign(-(D["spx_minus_sx5e_20"].shift(shift) if shift else D["spx_minus_sx5e_20"]).values)
    agree = np.isfinite(hs) & (sg != 0) & (cot == sg) & (spr == sg)
    nxt_month = D["month"].shift(-1).fillna(D["month"]).values
    dec, dec_first = _dec_arrays(nxt_month)
    P.add("cot", cot, cost_pips=cost_pips)
    P.add("spread", spr, cost_pips=cost_pips)
    P.add("house", np.where(np.isfinite(hs), sg, 0.0), cost_pips=cost_pips)
    P.add("dec", dec, speak=dec_first, cost_pips=cost_pips, exists=np.ones(len(D), bool))
    P.add("eqrel", eq, cost_pips=cost_pips)
    P.add("agree3", np.where(agree, sg, 0.0), cost_pips=cost_pips, exists=np.isfinite(hs))
    P.extra.update({"D": D, "ctx": ctx, "hs": hs, "cot_z": G["cot_z52"].values, "sma200": np.sign(G["dist_sma200_atr"].values)})
    return P


def load_h10_panel(cost_pips: float = 1.2) -> Panel:
    """Fed H.10 noon panel 1999-2026 for the pre-2003 years: positioning sign and December only."""
    px = _macro_series("fred_DEXUSEU.csv").dropna()
    px = px[px > 0]
    idx = pd.DatetimeIndex(px.index).tz_localize("UTC")
    lc = np.log(px.values)
    f1 = _fwd(lc, 1)
    leg = pd.read_csv(MACRO / "cot_eurofx_legacy.csv", parse_dates=["report_date"]).set_index("report_date")
    net = (leg.noncomm_long - leg.noncomm_short) / leg.open_interest
    net.index = net.index + pd.Timedelta(days=6)
    z = (net - net.rolling(52).mean()) / net.rolling(52).std()
    zal = _align_lagged(z, px.index, 1).values
    P = Panel(idx, idx.year.values, px.values, f1, {h: _fwd(lc, h) for h in HS}, idx.values.astype("datetime64[ns]").astype(np.int64),
              cost_pips / px.values)
    P.add("cot", np.sign(zal), cost_pips=cost_pips)
    m = px.index.month.values
    dec, dec_first = _dec_arrays(np.r_[m[1:], m[-1]])
    P.add("dec", dec, speak=dec_first, cost_pips=cost_pips, exists=np.ones(len(px), bool))
    return P


# ================================================================ regimes
def _last_move(s: pd.Series) -> tuple[pd.Series, pd.Series]:
    d = s.diff().fillna(0.0)
    sign = np.sign(d).where(d != 0)
    pos = pd.Series(np.where(d != 0, np.arange(len(s)), np.nan), index=s.index).ffill()
    since = pd.Series(np.arange(len(s)), index=s.index) - pos
    last = sign.ffill()
    return (last > 0) & (since <= 365), (last < 0) & (since <= 365)


def build_regimes(D: pd.DataFrame) -> pd.DataFrame:
    """Session-level regime labels (object columns, NaN = undefined), each from data known at the session close."""
    cdate = pd.DatetimeIndex(D["close_time"].dt.tz_convert("UTC").dt.normalize().dt.tz_localize(None))
    cal = pd.date_range("1999-01-04", cdate.max())
    pol = pd.read_csv(MACRO / "ecb_policy_rates.csv", parse_dates=["date"]).set_index("date")
    dfr = pol["deposit_facility_rate"].astype(float).reindex(cal).ffill()
    mro = pol["main_refinancing_rate"].astype(float).reindex(cal).ffill()
    fed = pd.concat([_macro_series("fred_DFEDTAR.csv"), _macro_series("fred_DFEDTARU.csv")]).sort_index()
    fed = fed[~fed.index.duplicated(keep="last")].reindex(cal).ffill()
    e_up, e_dn = _last_move(dfr + mro)
    f_up, f_dn = _last_move(fed)
    lb = (dfr <= 0.5) & (fed <= 0.5)
    up, dn = e_up | f_up, e_dn | f_dn
    policy = pd.Series(np.select([lb, up & ~dn, dn & ~up], ["LB", "HIKE", "CUT"], "OTHER"), index=cal)
    gap = (dfr - fed).abs()
    med = gap.expanding(min_periods=1095).median().shift(1)
    div_level = pd.Series(np.where(med.isna(), None, np.where(gap > med, "ABOVE", "BELOW")), index=cal)
    dg = gap - gap.shift(182)
    div_change = pd.Series(np.where(dg.isna(), None, np.where(dg > 1e-9, "WIDER", np.where(dg < -1e-9, "NARROWER", "SAME"))), index=cal)
    us2 = _macro_series("fred_DGS2.csv").loc["1999":].dropna()
    rv = (us2.diff() * 100).rolling(60).std()
    q1 = rv.expanding(min_periods=750).quantile(1 / 3).shift(1)
    q2 = rv.expanding(min_periods=750).quantile(2 / 3).shift(1)
    ratevol = pd.Series(np.where(q1.isna() | rv.isna(), None, np.where(rv <= q1, "LOW", np.where(rv <= q2, "MID", "HIGH"))), index=rv.index)
    bd = _macro_series("fred_DTWEXBGS.csv").dropna()
    sma = bd.rolling(200).mean()
    dollar = pd.Series(np.where(sma.isna(), None, np.where(bd > sma, "ABOVE", "BELOW")), index=bd.index)
    cpi = _macro_series("fred_CPIAUCSL.csv")
    yoy = (cpi / cpi.shift(12) - 1) * 100
    infl = pd.Series(np.where(yoy.isna(), None, np.where(yoy > 3.0, "HIGH", "LOW")), index=yoy.index + pd.Timedelta(days=60))

    def al(s, lag=1):
        s = s.dropna()
        codes, cats = pd.factorize(s)
        a = _align_lagged(pd.Series(codes.astype(float), index=s.index), cdate, lag).values
        return np.array([cats[int(x)] if np.isfinite(x) else None for x in a], dtype=object)

    R = pd.DataFrame(index=D.index)
    R["policy"] = al(policy); R["div_level"] = al(div_level); R["div_change"] = al(div_change)
    R["ratevol"] = al(ratevol); R["dollar"] = al(dollar, 7); R["inflation"] = al(infl)
    az = D["cot_z52"].abs().values
    R["crowding"] = np.where(np.isnan(az), None, np.where(az < 1, "<1", np.where(az <= 2, "1-2", ">2")))
    return R


def class_arrays(P: Panel, R: pd.DataFrame, comp: str, sma200: np.ndarray | None = None) -> dict:
    """{(var, class): bool mask} for one component; trend_rel depends on the component's own direction."""
    out = {}
    for v in REGVARS[:-1]:
        col = R[v].values
        for c in [x for x in pd.unique(col) if x is not None and x == x]:
            out[(v, c)] = col == c
    s = P.extra["sma200"] if sma200 is None else sma200
    d = P.dirs[comp]
    ok = np.isfinite(s) & (s != 0) & (d != 0)
    out[("trend_rel", "WITH")] = ok & (s == d)
    out[("trend_rel", "COUNTER")] = ok & (s == -d)
    return out


# ================================================================ statistics
def wilson(k: float, n: float) -> tuple[float, float]:
    return SEL.wilson(k / n, n) if n > 0 else (np.nan, np.nan)


def decisions(P: Panel, comp: str, h: int, mode: str, start: int, mask: np.ndarray | None = None, speak: np.ndarray | None = None) -> np.ndarray:
    sp = (P.speak[comp] if speak is None else speak) & np.isfinite(P.F[h]) & (P.year >= start)
    if mask is not None:
        sp = sp & mask
    if mode == "N":
        return _greedy_idx(sp, h)
    g = np.arange(0, len(sp), STEP)
    return g[sp[g]]


def cell(P: Panel, comp: str, h: int, idx: np.ndarray, a: int, b: int) -> dict:
    idx = idx[(P.year[idx] >= a) & (P.year[idx] <= b)]
    n = len(idx)
    if n == 0:
        return {"n": 0, "acc": np.nan, "lo": np.nan, "hi": np.nan, "net_bp": np.nan}
    g = P.dirs[comp][idx] * P.F[h][idx]
    k = float((g > 0).sum())
    lo, hi = wilson(k, n)
    return {"n": n, "acc": k / n, "lo": lo, "hi": hi, "net_bp": float((g - 2 * P.cost_bp[idx]).mean())}


def sharpe(x: np.ndarray) -> tuple[float, float, int]:
    x = x[np.isfinite(x)]
    if len(x) < 20 or x.std() == 0:
        return np.nan, np.nan, len(x)
    return float(x.mean() / x.std(ddof=1) * math.sqrt(252)), float(x.mean() / x.std(ddof=1) * math.sqrt(len(x))), len(x)


def years_span(P: Panel, m: np.ndarray) -> float:
    return float(m.sum()) / 252.0


# ---------------------------------------------------------------- reconcile with arm N
def reconcile(P: Panel) -> pd.DataFrame:
    rows = []
    for h in HS:
        for mode in ("W", "N"):
            idx = decisions(P, "agree3", h, mode, 2010)
            for lab, a, b in EVAL[:3]:
                rows.append({"h": h, "mode": mode, "period": lab, **cell(P, "agree3", h, idx, a, b)})
    return pd.DataFrame(rows)


def tranche_book(P: Panel, idx: np.ndarray, d: np.ndarray, h: int, cost_pips: float) -> pd.DataFrame:
    w = 1.0 / math.ceil(h / STEP)
    pos = np.zeros(len(P.close))
    for i in idx:
        pos[i:i + h] += d[i] * w
    pnl = pnl_from_positions(pd.Series(pos, index=P.index), pd.Series(P.f1, index=P.index), pd.Series(P.close, index=P.index), cost_pips=cost_pips)
    return pnl


# ---------------------------------------------------------------- (1) power
def power_tables(P: Panel, streams: dict, reps: int = 5000, blocks=(BLOCK, 63, 252)) -> pd.DataFrame:
    rows = []
    for comp in list(COMPONENTS) + list(streams):
        for (bl, ba, bb, ol, oa, ob) in STEPS:
            base = (P.year >= ba) & (P.year <= bb)
            obs = (P.year >= oa) & (P.year <= ob)
            yrs = years_span(P, obs)
            # ---- Sharpe
            x = streams[comp] if comp in streams else P.net[comp]
            ex = np.isfinite(x) if comp in streams else P.exists[comp]
            xb, xo = x[base & ex], x[obs & ex]
            if len(xb) > 250 and len(xo) > 100:
                so = sharpe(xo)[0]; sb = sharpe(xb)[0]
                for L in blocks:
                    bs = _boot_sharpe(np.ascontiguousarray(xb), len(xo), L, reps, 11)
                    crit = float(np.nanquantile(bs, 0.05))
                    b0 = _boot_sharpe(np.ascontiguousarray(xb - xb.mean()), len(xo), L, reps, 12)
                    rows.append({"table": "power", "component": comp, "stat": "sharpe", "mode": "daily", "base": bl, "observed_window": ol, "block": L,
                                 "base_value": sb, "observed": so, "n_obs": len(xo), "null_mean": float(np.nanmean(bs)), "null_p05": crit,
                                 "p_unchanged": float((1 + (bs <= so).sum()) / (reps + 1)), "power_vs_no_edge": float((b0 <= crit).mean()),
                                 "p_recentred_sr05": float((bs - np.nanmean(bs) + 0.5 <= so).mean()),
                                 "p_true_sr05": float(norm.cdf((so - 0.5) * math.sqrt(len(xo) / 252.0)))})
            if comp in streams:
                continue
            # ---- accuracy
            for h in HS:
                valid = np.isfinite(P.F[h])
                hit = (P.dirs[comp] * np.nan_to_num(P.F[h]) > 0).astype(float)
                sp = P.speak[comp] & valid
                for mode in ("N", "W"):
                    idx = decisions(P, comp, h, mode, 2010 if ba >= 2010 else 2006)
                    co = cell(P, comp, h, idx, oa, ob); cb = cell(P, comp, h, idx, ba, bb)
                    if co["n"] == 0 or cb["n"] < 5:
                        continue
                    T_out = int((obs & valid).sum())
                    for L in blocks:
                        a_, _, n_, _ = _boot_acc2(sp[base], sp[base], hit[base], h, T_out, L, reps, 21 + h, mode == "W")
                        a_ = a_[np.isfinite(a_)]
                        crit = float(np.quantile(a_, 0.05))
                        ptrue = norm.cdf(0.5 * math.sqrt(h / 252.0))
                        k_obs = round(co["acc"] * co["n"])
                        rows.append({"table": "power", "component": comp, "stat": f"acc{h}", "mode": mode, "base": bl, "observed_window": ol, "block": L,
                                     "base_value": cb["acc"], "base_n": cb["n"], "observed": co["acc"], "n_obs": co["n"],
                                     "null_mean": float(a_.mean()), "null_p05": crit, "null_mean_n": float(n_.mean()),
                                     "p_unchanged": float((1 + (a_ <= co["acc"] + 1e-12).sum()) / (len(a_) + 1)),
                                     "p_recentred_sr05": float((a_ - a_.mean() + ptrue <= co["acc"] + 1e-12).mean()),
                                     "power_vs_no_edge": float(binom.cdf(math.floor(crit * co["n"] + 1e-9), co["n"], 0.5)) if mode == "N" else np.nan,
                                     "p_true_sr05": float(binom.cdf(k_obs, co["n"], ptrue)) if mode == "N" else np.nan})
    return pd.DataFrame(rows)


def joint_power(P: Panel, reps: int = 5000, blocks=(BLOCK, 252)) -> pd.DataFrame:
    """Added after the first run: one test for all components on common pseudo-samples (2010-22 -> 2023-26)."""
    rows = []
    base = (P.year >= 2010) & (P.year <= 2022); obs = (P.year >= 2023) & (P.year <= 2026)
    comps = ("cot", "spread", "house", "eqrel")
    keys, SP, HT, ob = [], [], [], []
    for c in comps:
        for h in HS:
            valid = np.isfinite(P.F[h])
            SP.append((P.speak[c] & valid)[base]); HT.append((P.dirs[c] * np.nan_to_num(P.F[h]) > 0).astype(float)[base])
            ob.append(cell(P, c, h, decisions(P, c, h, "W", 2010), 2023, 2026)["acc"]); keys.append(f"{c}@{h}")
    T_out = int((obs & np.isfinite(P.F[42])).sum())
    ob = np.array(ob)
    for L in blocks:
        A = _boot_weekly_multi(np.array(SP), np.array(HT), T_out, L, reps, 41)
        mu, sd = np.nanmean(A, 0), np.nanstd(A, 0)
        z_obs = (mu - ob) / sd
        zb = (mu[None, :] - A) / sd[None, :]
        for name, sel in (("all four components x 21/42", np.arange(len(keys))), ("positioning excluded (spread, house, eqrel)", np.arange(2, len(keys))),
                          ("spread and eqrel only (no positioning input)", np.array([2, 3, 6, 7]))):
            rows.append({"table": "power_joint", "stat": "weekly accuracy", "set": name, "block": L, "observed_mean": float(ob[sel].mean()),
                         "null_mean": float(mu[sel].mean()), "p_pooled_mean": float((np.nanmean(A[:, sel], 1) <= ob[sel].mean()).mean()),
                         "worst": keys[sel[int(np.argmax(z_obs[sel]))]], "worst_z": float(z_obs[sel].max()),
                         "p_largest_drop": float((np.nanmax(zb[:, sel], 1) >= z_obs[sel].max()).mean())})
        sc = ("cot", "spread", "house", "dec", "eqrel")
        m0 = base & P.exists["eqrel"]
        X = np.array([P.net[c][m0] for c in sc])
        so = np.array([sharpe(P.net[c][obs])[0] for c in sc])
        B = _boot_sharpe_multi(X, int(obs.sum()), L, reps, 43)
        mu, sd = np.nanmean(B, 0), np.nanstd(B, 0)
        z_obs = (mu - so) / sd
        zb = (mu[None, :] - B) / sd[None, :]
        rows.append({"table": "power_joint", "stat": "daily Sharpe", "set": "five component streams", "block": L, "observed_mean": float(so.mean()),
                     "null_mean": float(mu.mean()), "p_pooled_mean": float((np.nanmean(B, 1) <= so.mean()).mean()), "worst": sc[int(np.argmax(z_obs))],
                     "worst_z": float(z_obs.max()), "p_largest_drop": float((np.nanmax(zb, 1) >= z_obs.max()).mean())})
    return pd.DataFrame(rows)


def mix_table(P: Panel, R: pd.DataFrame, comps=("cot", "spread", "house", "eqrel", "agree3")) -> pd.DataFrame:
    """Added after the first run: 2023-26 by regime class next to 2010-22, and what the 2023-26 regime MIX alone implies."""
    rows = []
    base = (P.year >= 2010) & (P.year <= 2022); obs = (P.year >= 2023) & (P.year <= 2026)
    for comp in comps:
        W = {h: decisions(P, comp, h, "W", 2010) for h in HS}
        hit = {h: (P.dirs[comp][W[h]] * P.F[h][W[h]] > 0).astype(float) for h in HS}
        for v in REGVARS[:-1]:
            col = R[v].values
            cats = [x for x in pd.unique(col) if x is not None and x == x]
            imp = {"mean_bp": 0.0, 21: 0.0, 42: 0.0}
            wsum = {21: 0.0, 42: 0.0}
            for c in cats:
                m = col == c
                r = {"table": "mix", "component": comp, "regime": v, "class": c, "share_2010-22": float((m & base).sum() / base.sum()),
                     "share_2023-26": float((m & obs).sum() / obs.sum())}
                for lab, per in (("2010-22", base), ("2023-26", obs)):
                    x = P.net[comp][m & per]
                    r[f"mean_bp_{lab}"] = float(np.nanmean(x)) if len(x) else np.nan
                    r[f"sharpe_{lab}"] = sharpe(x)[0]
                    for h in HS:
                        k = m[W[h]] & per[W[h]]
                        r[f"W{h}_n_{lab}"] = int(k.sum()); r[f"W{h}_acc_{lab}"] = float(hit[h][k].mean()) if k.sum() else np.nan
                rows.append(r)
                if np.isfinite(r["mean_bp_2010-22"]):
                    imp["mean_bp"] += r["share_2023-26"] * r["mean_bp_2010-22"]
                for h in HS:
                    if r[f"W{h}_n_2010-22"] > 0:
                        imp[h] += r[f"W{h}_n_2023-26"] * r[f"W{h}_acc_2010-22"]; wsum[h] += r[f"W{h}_n_2023-26"]
            r = {"table": "mix", "component": comp, "regime": v, "class": "__MIX_IMPLIED__", "mean_bp_2010-22": float(np.nanmean(P.net[comp][base])),
                 "mean_bp_2023-26": float(np.nanmean(P.net[comp][obs])), "mix_implied_mean_bp_2023-26": imp["mean_bp"]}
            for h in HS:
                kb, ko = base[W[h]], obs[W[h]]
                r[f"W{h}_acc_2010-22"] = float(hit[h][kb].mean()); r[f"W{h}_acc_2023-26"] = float(hit[h][ko].mean())
                r[f"mix_implied_W{h}_acc_2023-26"] = imp[h] / wsum[h] if wsum[h] else np.nan
            rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- (2) decay
def rolling_tables(P: Panel, tag: str, comps, first_year: int) -> pd.DataFrame:
    rows = []
    for comp in comps:
        ex = P.exists[comp]
        y0 = max(first_year, int(P.year[ex].min()))
        dec = {(h, m): decisions(P, comp, h, m, y0) for h in HS for m in ("N", "W")}

        def stats(a, b, kind, label):
            m = ex & (P.year >= a) & (P.year <= b)
            if m.sum() < 200 * (b - a + 1) * 0.6:
                return
            sr, t, n = sharpe(P.net[comp][m])
            r = {"table": kind, "panel": tag, "component": comp, "window": label, "start": a, "end": b, "sharpe": sr, "t": t, "sessions": n,
                 "active_frac": float((P.dirs[comp][m] != 0).mean())}
            for (h, md), idx in dec.items():
                c = cell(P, comp, h, idx if not (comp == "dec" and md == "W") else idx[:0], a, b)   # one decision a year: no weekly grid
                r.update({f"{md}{h}_n": c["n"], f"{md}{h}_acc": c["acc"], f"{md}{h}_lo": c["lo"], f"{md}{h}_hi": c["hi"], f"{md}{h}_net_bp": c["net_bp"]})
            rows.append(r)

        for W in (3, 5):
            for Y in range(y0 + W - 1, 2027):
                stats(Y - W + 1, Y, f"rolling{W}y", f"{Y - W + 1}-{Y}")
        for lab, a, b in ERAS:
            stats(a, b, "eras", lab)
    return pd.DataFrame(rows)


def step_z(sr_in, y_in, sr_out, y_out) -> float:
    if not (np.isfinite(sr_in) and np.isfinite(sr_out)):
        return np.nan
    return float((sr_in - sr_out) / math.sqrt((1 + sr_in ** 2 / 2) / y_in + (1 + sr_out ** 2 / 2) / y_out))


# ---------------------------------------------------------------- (3) regimes
def regime_tables(P: Panel, R: pd.DataFrame, comps=COMPONENTS) -> pd.DataFrame:
    rows = []
    for comp in comps:
        CA = class_arrays(P, R, comp)
        for (v, c), m in CA.items():
            defined = np.zeros(len(m), bool)
            for (v2, c2), m2 in CA.items():
                if v2 == v:
                    defined |= m2
            rest = defined & ~m
            dn = {(h, md, w): decisions(P, comp, h, md, 2006, mask=(m if w == "in" else rest)) for h in HS for md in ("N", "W") for w in ("in", "out")}
            for lab, a, b in PERIODS3:
                per = (P.year >= a) & (P.year <= b)
                sr_in, t_in, n_in = sharpe(P.net[comp][per & m & P.exists[comp]])
                sr_out, _, n_out = sharpe(P.net[comp][per & rest & P.exists[comp]])
                r = {"table": "regime", "component": comp, "regime": v, "class": c, "period": lab, "sessions": int((per & m).sum()),
                     "share_of_defined": float((per & m).sum() / max(1, (per & defined).sum())), "sharpe_in": sr_in, "t_in": t_in, "sharpe_out": sr_out}
                for (h, md, w), idx in dn.items():
                    x = cell(P, comp, h, idx, a, b)
                    for k, val in x.items():
                        r[f"{md}{h}_{w}_{k}"] = val
                rows.append(r)
    return pd.DataFrame(rows)


def screen(T: pd.DataFrame) -> pd.DataFrame:
    """Applies the pre-declared screen to the regime table of each component."""
    rows = []
    for (comp, v, c), g in T.groupby(["component", "regime", "class"], sort=False):
        g = g.set_index("period")
        gaps, ok_n, sgap = [], True, []
        for lab, _, _ in HALVES:
            q = g.loc[lab]
            for h in HS:
                gaps.append(q[f"N{h}_in_acc"] - q[f"N{h}_out_acc"])
            ok_n &= bool(q["N21_in_n"] >= MIN_N and q["N21_out_n"] >= MIN_N)
            sgap.append(q["sharpe_in"] - q["sharpe_out"])
        gaps = np.array(gaps, dtype=float); sgap = np.array(sgap, dtype=float)
        fin = np.isfinite(gaps).all() and np.isfinite(sgap).all()
        fav = bool(fin and ok_n and (gaps >= GAP - 1e-12).all() and (sgap > 0).all())
        unf = bool(fin and ok_n and (gaps <= -GAP + 1e-12).all() and (sgap < 0).all())
        cons = float(max(gaps.min(), (-gaps).min())) if np.isfinite(gaps).all() and ok_n else np.nan     # weakest of the four gaps, signed-consistent
        scons = float(max(sgap.min(), (-sgap).min())) if np.isfinite(sgap).all() and ok_n else np.nan    # weakest of the two Sharpe gaps
        q = g.loc["2006-26"]
        rows.append({"table": "screen", "component": comp, "regime": v, "class": c, "gap21_2006-15": gaps[0], "gap42_2006-15": gaps[1],
                     "gap21_2016-26": gaps[2], "gap42_2016-26": gaps[3], "sharpe_gap_2006-15": sgap[0], "sharpe_gap_2016-26": sgap[1],
                     "enough_n": ok_n, "favourable": fav, "unfavourable": unf, "passes": fav or unf, "consistent_gap": cons, "consistent_sharpe_gap": scons,
                     "gap21_2006-26": q["N21_in_acc"] - q["N21_out_acc"], "gap42_2006-26": q["N42_in_acc"] - q["N42_out_acc"],
                     "n21_in_2006-26": q["N21_in_n"], "n21_out_2006-26": q["N21_out_n"]})
    return pd.DataFrame(rows)


def _rotate_regimes(R: pd.DataFrame, sma: np.ndarray, lo: int, hi: int, k: int) -> tuple[pd.DataFrame, np.ndarray]:
    """Rotate every regime label (and the 200-day trend state) by k sessions inside [lo, hi)."""
    Rr = R.copy()
    for v in R.columns:
        a = R[v].values.copy()
        a[lo:hi] = np.roll(a[lo:hi], k)
        Rr[v] = a
    s = sma.copy()
    s[lo:hi] = np.roll(s[lo:hi], k)
    return Rr, s


def screen_placebo(P: Panel, R: pd.DataFrame, comp: str = "agree3", reps: int = 1000, seed: int = 5) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Joint rotation of all regime labels against the calls: number of passing classes and the largest consistent gap."""
    rng = np.random.default_rng(seed)
    lo = int(np.flatnonzero(P.year >= 2006)[0]); hi = len(P.year)
    npass = np.zeros(reps, int); mx = np.zeros(reps); mxs = np.zeros(reps)
    per_class = {}
    sma0 = P.extra["sma200"]
    for r in range(reps):
        k = int(rng.integers(252, hi - lo - 252))
        Rr, s = _rotate_regimes(R, sma0, lo, hi, k)
        P.extra["sma200"] = s
        S = screen(regime_tables(P, Rr, comps=(comp,)))
        npass[r] = int(S["passes"].sum())
        mx[r] = float(np.nanmax(S["consistent_gap"].values)) if S["consistent_gap"].notna().any() else np.nan
        mxs[r] = float(np.nanmax(S["consistent_sharpe_gap"].values)) if S["consistent_sharpe_gap"].notna().any() else np.nan
        for (v, c, g, g2) in zip(S["regime"], S["class"], S["consistent_gap"], S["consistent_sharpe_gap"]):
            per_class.setdefault((v, c), []).append((g, g2))
    P.extra["sma200"] = sma0
    pc = pd.DataFrame([{"regime": v, "class": c, "placebo_gaps": np.array([x[0] for x in g], dtype=float),
                        "placebo_sharpe_gaps": np.array([x[1] for x in g], dtype=float)} for (v, c), g in per_class.items()])
    return pc, npass, (mx, mxs)


# ---------------------------------------------------------------- (4) walk-forward conditional rule
def wf_mute(P: Panel, cls: np.ndarray, hindsight: bool = False, comp: str = "agree3", strict: bool = False) -> tuple[np.ndarray, list]:
    """cls: object array of class labels per session (None = undefined). Returns the speak mask of the conditional rule
    and the per-year log of muted classes."""
    h = 21
    idx = decisions(P, comp, h, "W", 2006)
    hit = (P.dirs[comp][idx] * P.F[h][idx] > 0).astype(float)
    end = P.ct[np.minimum(idx + h, len(P.ct) - 1)]
    c_idx = cls[idx]
    cats = [x for x in pd.unique(cls) if x is not None and x == x]
    defined = np.array([x is not None and x == x for x in c_idx], dtype=bool)
    is_c = {c: (c_idx == c) for c in cats}
    full = {c: (cls == c) for c in cats}
    muted_mask = np.zeros(len(cls), bool)
    log = []
    for Y in YEARS:
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC").value
        tr = (P.year[idx] >= 2010) if hindsight else (end < start)
        muted, fav = [], []
        for c in cats:
            inn = tr & is_c[c]
            out = tr & ~is_c[c] & defined
            if inn.sum() >= MUTE_MIN and out.sum() >= MUTE_MIN:
                if hit[inn].mean() <= hit[out].mean() - GAP:
                    muted.append(c)
                if hit[inn].mean() >= hit[out].mean() + GAP:
                    fav.append(c)
        log.append({"year": Y, "muted": "|".join(map(str, muted)), "favourable": "|".join(map(str, fav)), "n_train": int(tr.sum())})
        if strict:
            if fav:                                  # speak only in favourable classes (added after the first run)
                keep = np.zeros(len(cls), bool)
                for c in fav:
                    keep |= full[c]
                muted_mask |= (P.year == Y) & ~keep
        else:
            for c in muted:
                muted_mask |= (P.year == Y) & full[c]
    return P.speak[comp] & ~muted_mask, log


def eval_rule(P: Panel, speak: np.ndarray, name: str, cost_pips: float, reps: int = 2000, comp: str = "agree3", boot: bool = True) -> pd.DataFrame:
    """Round-5 evaluation of a conditional rule against the unconditional one."""
    rows = []
    d = P.dirs[comp]
    for h in HS:
        valid = np.isfinite(P.F[h])
        hit = (d * np.nan_to_num(P.F[h]) > 0).astype(float)
        spU, spC = P.speak[comp] & valid, speak & valid
        for mode in ("N", "W"):
            iU = decisions(P, comp, h, mode, 2010)
            iC = decisions(P, comp, h, mode, 2010, speak=speak)
            for lab, a, b in EVAL:
                per = (P.year >= a) & (P.year <= b)
                yrs = years_span(P, per & valid)
                cu, cc = cell(P, comp, h, iU, a, b), cell(P, comp, h, iC, a, b)
                r = {"table": "candidates", "rule": name, "h": h, "mode": mode, "period": lab, "n_uncond": cu["n"], "acc_uncond": cu["acc"],
                     "lo_uncond": cu["lo"], "hi_uncond": cu["hi"], "net_bp_uncond": cu["net_bp"], "dec_yr_uncond": cu["n"] / yrs,
                     "n": cc["n"], "acc": cc["acc"], "lo": cc["lo"], "hi": cc["hi"], "net_bp": cc["net_bp"], "dec_yr": cc["n"] / yrs,
                     "diff": cc["acc"] - cu["acc"] if cc["n"] else np.nan}
                # calls of the unconditional rule that the conditional rule refuses (weekly grid only: a clean partition)
                if mode == "W":
                    ref = np.setdiff1d(iU, iC)
                    cr = cell(P, comp, h, ref, a, b)
                    r.update({"n_refused": cr["n"], "acc_refused": cr["acc"]})
                if boot and cc["n"] >= 5:
                    m = per
                    aC, aU, nC, _ = _boot_acc2(spC[m], spU[m], hit[m], h, int(m.sum()), BLOCK, reps, 31 + h, mode == "W")
                    dd = aC - aU
                    dd = dd[np.isfinite(dd)]
                    if len(dd) > 100:
                        r.update({"boot_diff_mean": float(dd.mean()), "boot_lo": float(np.quantile(dd, 0.025)), "boot_hi": float(np.quantile(dd, 0.975)),
                                  "boot_p_le0": float((dd <= 0).mean())})
                rows.append(r)
    return pd.DataFrame(rows)


def rule_book(P: Panel, speak: np.ndarray, cost_pips: float, comp: str = "agree3") -> pd.DataFrame:
    idx = decisions(P, comp, 21, "W", 2010, speak=speak)
    pnl = tranche_book(P, idx, P.dirs[comp], 21, cost_pips)
    return pnl[pnl.index.year >= 2010]


def daily_gated(P: Panel, speak: np.ndarray, cost_pips: float, comp: str = "agree3") -> pd.DataFrame:
    """Added after the first run: the daily-sign stream held only on sessions on which the conditional rule speaks."""
    pos = pd.Series(np.where(speak, P.dirs[comp], 0.0), index=P.index)
    pnl = pnl_from_positions(pos, pd.Series(P.f1, index=P.index), pd.Series(P.close, index=P.index), cost_pips=cost_pips)
    return pnl[pnl.index.year >= 2010]


def gain(P: Panel, speak: np.ndarray, comp: str = "agree3") -> dict:
    """Non-overlapping accuracy gain of a conditional rule over the unconditional one (2010-26, 2016-26), no bootstrap."""
    out = {}
    for h in HS:
        iU = decisions(P, comp, h, "N", 2010); iC = decisions(P, comp, h, "N", 2010, speak=speak)
        for lab, a, b in EVAL[:3]:
            cu, cc = cell(P, comp, h, iU, a, b), cell(P, comp, h, iC, a, b)
            out[f"gain{h}_{lab}"] = cc["acc"] - cu["acc"] if cc["n"] else np.nan
            out[f"n{h}_{lab}"] = cc["n"]; out[f"acc{h}_{lab}"] = cc["acc"]
    return out


def shift_labels(cls: np.ndarray, k: int) -> np.ndarray:
    out = np.empty(len(cls), dtype=object)
    out[:] = None
    if k > 0:
        out[k:] = cls[:-k]
    elif k < 0:
        out[:k] = cls[-k:]
    else:
        out[:] = cls
    return out


def conj_speak(P: Panel, masks: list[np.ndarray]) -> np.ndarray:
    sp = P.speak["agree3"].copy()
    for m in masks:
        sp &= m
    return sp


def leak_checks(P: Panel, cls_by_var: dict, subject: str, cost_pips: float, reps: int = 300, seed: int = 9, strict: bool = False) -> pd.DataFrame:
    """Leak checks of the walk-forward conditional rule on regime variable `subject` (or the conjunction of several)."""
    rng = np.random.default_rng(seed)
    vars_ = subject.split("+")
    lo = int(np.flatnonzero(P.year >= 2006)[0]); hi = len(P.year)

    def rule(tr=lambda a: a, hindsight=False):
        return conj_speak(P, [wf_mute(P, tr(cls_by_var[v]), hindsight, strict=strict)[0] for v in vars_])

    rows = []
    base = gain(P, rule())
    rows.append({"table": "leak", "subject": subject, "check": "baseline (walk-forward class choice)", **base})
    for lag in (21, 63, 126):
        rows.append({"table": "leak", "subject": subject, "check": f"regime labels lagged +{lag} sessions", **gain(P, rule(lambda a, k=lag: shift_labels(a, k)))})
    rows.append({"table": "leak", "subject": subject, "check": "look-ahead control: regime labels from 126 sessions ahead", **gain(P, rule(lambda a: shift_labels(a, -126)))})
    rows.append({"table": "leak", "subject": subject, "check": "look-ahead control: muted classes chosen with hindsight (2010-26)", **gain(P, rule(hindsight=True))})
    # oracle regime: the class IS the future outcome of the call; the harness must expose it
    orc = np.where(P.dirs["agree3"] * np.nan_to_num(P.F[21]) > 0, "RIGHT", "WRONG").astype(object)
    rows.append({"table": "leak", "subject": "oracle", "check": "look-ahead control: oracle regime = future 21-session outcome", **gain(P, wf_mute(P, orc, strict=strict)[0])})
    for kind in ("iid shuffle", "block rotation"):
        G = []
        for r in range(reps):
            if kind == "iid shuffle":
                perm = lo + rng.permutation(hi - lo)
                tr = lambda a, perm=perm: np.r_[a[:lo], a[perm]]
            else:
                k = int(rng.integers(252, hi - lo - 252))
                tr = lambda a, k=k: np.r_[a[:lo], np.roll(a[lo:], k)]
            G.append(gain(P, rule(tr)))
        G = pd.DataFrame(G)
        r = {"table": "leak", "subject": subject, "check": f"regime labels shuffled ({kind}, {reps} draws): mean"}
        r.update({c: float(G[c].mean()) for c in G.columns})
        for h in HS:
            for lab in ("2010-26", "2016-26"):
                g0 = base[f"gain{h}_{lab}"]
                r[f"p_placebo_ge_real_{h}_{lab}"] = float((G[f"gain{h}_{lab}"].fillna(0) >= g0 - 1e-12).mean())
        r["share_draws_muting_something"] = float((G["n21_2010-26"] != base_n_uncond(P)).mean())
        rows.append(r)
    # outcomes rotated against the calls
    acc = {h: [] for h in HS}
    spc = rule()
    for r in range(200):
        k = int(rng.integers(252, hi - lo - 252))
        for h in HS:
            f = P.F[h].copy(); f[lo:] = np.roll(f[lo:], k)
            sp = spc & np.isfinite(f) & (P.year >= 2010)
            idx = _greedy_idx(sp, h)
            acc[h].append(float((P.dirs["agree3"][idx] * f[idx] > 0).mean()) if len(idx) else np.nan)
    rows.append({"table": "leak", "subject": subject, "check": "outcomes rotated against the calls (200 draws): mean accuracy of the conditional rule",
                 "acc21_2010-26": float(np.nanmean(acc[21])), "acc42_2010-26": float(np.nanmean(acc[42]))})
    return pd.DataFrame(rows)


def base_n_uncond(P: Panel) -> int:
    return int(cell(P, "agree3", 21, decisions(P, "agree3", 21, "N", 2010), 2010, 2026)["n"])


def pipeline_placebo(P: Panel, R: pd.DataFrame, reps: int = 300, seed: int = 17) -> pd.DataFrame:
    """Full pipeline on rotated regimes: screen on the whole sample, then the walk-forward rule on whatever passes."""
    rng = np.random.default_rng(seed)
    lo = int(np.flatnonzero(P.year >= 2006)[0]); hi = len(P.year)
    sma0 = P.extra["sma200"]
    rows = []
    for r in range(reps):
        k = int(rng.integers(252, hi - lo - 252))
        Rr, s = _rotate_regimes(R, sma0, lo, hi, k)
        P.extra["sma200"] = s
        S = screen(regime_tables(P, Rr, comps=("agree3",)))
        pv = list(dict.fromkeys(S.loc[S["passes"], "regime"]))
        row = {"draw": r, "n_vars_pass": len(pv)}
        if pv:
            cb = cls_by_var_of(P, Rr)
            sp = conj_speak(P, [wf_mute(P, cb[v])[0] for v in pv])
            row.update(gain(P, sp))
            sp2 = conj_speak(P, [wf_mute(P, cb[v], strict=True)[0] for v in pv])
            row.update({f"strict_{k}": x for k, x in gain(P, sp2).items()})
            for nm, spx in (("", sp), ("strict_", sp2)):
                bk = rule_book(P, spx, 1.2)["net_bp"]
                dg = daily_gated(P, spx, 1.2)["net_bp"]
                for lab, a, b in EVAL[:3]:
                    row[f"{nm}book_sharpe_{lab}"] = sharpe(bk[(bk.index.year >= a) & (bk.index.year <= b)].values)[0]
                    row[f"{nm}daily_sharpe_{lab}"] = sharpe(dg[(dg.index.year >= a) & (dg.index.year <= b)].values)[0]
        rows.append(row)
    P.extra["sma200"] = sma0
    return pd.DataFrame(rows)


def cls_by_var_of(P: Panel, R: pd.DataFrame, comp: str = "agree3") -> dict:
    out = {v: R[v].values for v in REGVARS[:-1]}
    s, d = P.extra["sma200"], P.dirs[comp]
    tr = np.empty(len(d), dtype=object); tr[:] = None
    ok = np.isfinite(s) & (s != 0) & (d != 0)
    tr[ok & (s == d)] = "WITH"; tr[ok & (s == -d)] = "COUNTER"
    out["trend_rel"] = tr
    return out


# ================================================================ run
def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True, fast: bool = False):
    """Returns (daily positions of the final stream as a Series, protocol report DataFrame)."""
    warnings.filterwarnings("ignore")
    say = (lambda *a: print(*a, flush=True)) if verbose else (lambda *a: None)
    P = load_panel(cost_pips)
    D = P.extra["D"]
    res = {"P": P}
    # ---- reconcile with arm N
    rec = reconcile(P)
    res["reconcile"] = rec
    bookU = rule_book(P, P.speak["agree3"], cost_pips)
    repU = report(bookU, periods_per_year=252, name=ARM, n_arms=1)
    q = rec[(rec.h == 21)].set_index(["mode", "period"])
    say(f"reconcile agree3 @21: weekly 2010-26 {q.loc[('W', '2010-26'), 'acc']:.3f} n={q.loc[('W', '2010-26'), 'n']} (arm N: 0.594, 387); "
        f"non-overlapping {q.loc[('N', '2010-26'), 'acc']:.3f} n={q.loc[('N', '2010-26'), 'n']} (0.59, 156); book Sharpe "
        + " / ".join(f"{repU.set_index('period').loc[p, 'sharpe']:.2f}" for p in ("2010-2026", "2016-2026", "2023-2026")) + " (0.52 / 0.51 / 0.43)")
    assert q.loc[("W", "2010-26"), "n"] == 387 and abs(q.loc[("W", "2010-26"), "acc"] - 0.594) < 0.001, "agreement rule does not reconcile with arm N"
    assert q.loc[("N", "2010-26"), "n"] == 156
    # ---- (1) power
    streams = {"agree3_book": bookU["net_bp"].reindex(P.index).values,
               "ew5": np.where(P.exists["eqrel"], np.mean([P.net[c] for c in ("cot", "spread", "house", "dec", "eqrel")], axis=0), np.nan)}
    PW = power_tables(P, streams, reps=1000 if fast else 5000)
    res["power"] = PW
    res["power_joint"] = joint_power(P, reps=1000 if fast else 5000)
    say("power done")
    # ---- (2) decay
    H = load_h10_panel(cost_pips)
    ROLL = pd.concat([rolling_tables(P, "store", COMPONENTS, 2003), rolling_tables(H, "h10", ("cot", "dec"), 2000)], ignore_index=True)
    er = ROLL[ROLL.table == "eras"].set_index(["panel", "component", "window"])
    stp = []
    for (pn, comp) in dict.fromkeys(zip(ROLL["panel"], ROLL["component"])):
        for (a, b) in (("2010-15", "2016-22"), ("2010-15", "2016-26"), ("2003-15", "2016-26"), ("2016-22", "2023-26"), ("2003-09", "2010-15"), ("2000-02", "2003-15")):
            if (pn, comp, a) in er.index and (pn, comp, b) in er.index:
                x, y = er.loc[(pn, comp, a)], er.loc[(pn, comp, b)]
                stp.append({"table": "step", "panel": pn, "component": comp, "from": a, "to": b, "sharpe_from": x["sharpe"], "sharpe_to": y["sharpe"],
                            "z": step_z(x["sharpe"], x["sessions"] / 252, y["sharpe"], y["sessions"] / 252),
                            "W21_from": x["W21_acc"], "W21_to": y["W21_acc"], "N21_from": x["N21_acc"], "N21_to": y["N21_acc"],
                            "N21_n_from": x["N21_n"], "N21_n_to": y["N21_n"]})
    res["rolling"], res["step"] = ROLL, pd.DataFrame(stp)
    say("decay done")
    # ---- (3) regimes
    R = build_regimes(D)
    res["R"] = R
    T = regime_tables(P, R)
    S = screen(T)
    res["regime"], res["screen"] = T, S
    SA = S[S.component == "agree3"]
    pc, npass, (mx, mxs) = screen_placebo(P, R, reps=200 if fast else 1000)
    obs_max = float(np.nanmax(SA["consistent_gap"].values))
    obs_maxs = float(np.nanmax(SA["consistent_sharpe_gap"].values))
    pl = {"table": "screen_placebo", "component": "agree3", "observed_classes_passing": int(SA["passes"].sum()),
          "placebo_mean_classes_passing": float(npass.mean()), "placebo_share_draws_with_any_pass": float((npass > 0).mean()),
          "p_at_least_as_many_pass": float((npass >= SA["passes"].sum()).mean()), "observed_max_consistent_gap": obs_max,
          "placebo_p95_max_consistent_gap": float(np.nanquantile(mx, 0.95)), "p_max_consistent_gap": float((mx >= obs_max - 1e-12).mean()),
          "observed_max_consistent_sharpe_gap": obs_maxs, "placebo_p95_max_consistent_sharpe_gap": float(np.nanquantile(mxs, 0.95)),
          "p_max_consistent_sharpe_gap": float((mxs >= obs_maxs - 1e-12).mean())}
    res["screen_placebo"] = pd.DataFrame([pl])
    pcm = {(v, c): g for v, c, g in zip(pc["regime"], pc["class"], pc["placebo_gaps"])}
    pcs = {(v, c): g for v, c, g in zip(pc["regime"], pc["class"], pc["placebo_sharpe_gaps"])}
    S["placebo_p_consistent_gap"] = [float((np.nan_to_num(pcm[(v, c)], nan=-1) >= g - 1e-12).mean()) if comp == "agree3" and (v, c) in pcm and np.isfinite(g) else np.nan
                                     for comp, v, c, g in zip(S["component"], S["regime"], S["class"], S["consistent_gap"])]
    S["placebo_p_consistent_sharpe_gap"] = [float((np.nan_to_num(pcs[(v, c)], nan=-9) >= g - 1e-12).mean()) if comp == "agree3" and (v, c) in pcs and np.isfinite(g) else np.nan
                                            for comp, v, c, g in zip(S["component"], S["regime"], S["class"], S["consistent_sharpe_gap"])]
    res["mix"] = mix_table(P, R)
    oth = []
    for comp in ("cot", "spread", "house", "eqrel"):
        Sc = S[S.component == comp]
        _, npc, (mxc, mxsc) = screen_placebo(P, R, comp=comp, reps=100 if fast else 400, seed=6)
        om, oms = float(np.nanmax(Sc["consistent_gap"].values)), float(np.nanmax(Sc["consistent_sharpe_gap"].values))
        oth.append({"table": "screen_placebo", "component": comp, "observed_classes_passing": int(Sc["passes"].sum()),
                    "placebo_mean_classes_passing": float(npc.mean()), "placebo_share_draws_with_any_pass": float((npc > 0).mean()),
                    "p_at_least_as_many_pass": float((npc >= Sc["passes"].sum()).mean()), "observed_max_consistent_gap": om,
                    "placebo_p95_max_consistent_gap": float(np.nanquantile(mxc, 0.95)), "p_max_consistent_gap": float((mxc >= om - 1e-12).mean()),
                    "observed_max_consistent_sharpe_gap": oms, "placebo_p95_max_consistent_sharpe_gap": float(np.nanquantile(mxsc, 0.95)),
                    "p_max_consistent_sharpe_gap": float((mxsc >= oms - 1e-12).mean())})
    res["screen_placebo"] = pd.concat([res["screen_placebo"], pd.DataFrame(oth)], ignore_index=True)
    SA = S[S.component == "agree3"]
    passing = list(dict.fromkeys(SA.loc[SA["passes"], "regime"]))
    say(f"screen: agree3 passing variables {passing}; classes passing {int(SA['passes'].sum())}; placebo mean {npass.mean():.2f}, p {pl['p_at_least_as_many_pass']:.3f}")
    # ---- (4) tradeable test
    cb = cls_by_var_of(P, R)
    cand, logs, speaks = [], [], {}
    if passing:
        for v in passing:
            sp, lg = wf_mute(P, cb[v])
            speaks[f"cond_{v}"] = sp
            logs += [{"table": "mute_log", "rule": f"cond_{v}", **x} for x in lg]
        if len(passing) >= 2:
            speaks["cond_all_passing"] = conj_speak(P, [speaks[f"cond_{v}"] for v in passing])
        for v in passing:                                # post hoc, added after the first run
            sp, lg = wf_mute(P, cb[v], strict=True)
            speaks[f"strict_{v}"] = sp
            logs += [{"table": "mute_log", "rule": f"strict_{v}", **x} for x in lg]
        diagnostic = False
        subject = "+".join(passing)
    else:
        res["bar"] = pd.DataFrame()
        nm = SA.sort_values("consistent_gap", ascending=False).iloc[0]["regime"]
        sp, lg = wf_mute(P, cb[nm])
        speaks[f"diag_{nm}"] = sp
        logs += [{"table": "mute_log", "rule": f"diag_{nm}", **x} for x in lg]
        diagnostic = True
        subject = nm
    for name, sp in speaks.items():
        cand.append(eval_rule(P, sp, name, cost_pips, reps=500 if fast else 2000))
    C = pd.concat(cand, ignore_index=True)
    C["diagnostic"] = diagnostic
    C["post_hoc"] = C["rule"].str.startswith("strict_")
    bar = []
    for name in speaks:
        x = C[(C.rule == name) & (C["mode"] == "N")].set_index(["h", "period"])
        bar.append({"table": "bar", "rule": name, "post_hoc": name.startswith("strict_"),
                    "gain_ge_3pts_21_and_42_in_2010-26_and_2016-26": bool(all(x.loc[(h, p), "diff"] >= BAR - 1e-12 for h in HS for p in ("2010-26", "2016-26"))),
                    "ge_6_decisions_a_year_21": bool(all(x.loc[(21, p), "dec_yr"] >= MIN_DEC_YR for p in ("2010-26", "2016-26"))),
                    "not_worse_2023-26": bool(all(x.loc[(h, "2023-26"), "diff"] >= -1e-12 for h in HS)),
                    "ge_6_decisions_a_year_2010-15": bool(x.loc[(21, "2010-15"), "dec_yr"] >= MIN_DEC_YR), "wilson_lo_2010-15": float(x.loc[(21, "2010-15"), "lo"])})
    res["bar"] = pd.DataFrame(bar)
    res["candidates"], res["mute_log"], res["speaks"] = C, pd.DataFrame(logs), speaks
    # final by the declared rule
    final, adopted, why = None, False, "nothing passed the screen (3)"
    if not diagnostic:
        q = C[(C.h == 21) & (C["mode"] == "N") & (C.period == "2010-15") & ~C["post_hoc"]]       # the pool declared before the first run
        el = q[q["dec_yr"] >= MIN_DEC_YR]
        if len(el):
            final = el.sort_values("lo", ascending=False)["rule"].iloc[0]
            x = C[(C.rule == final) & (C["mode"] == "N")].set_index(["h", "period"])
            ok = all(x.loc[(h, p), "diff"] >= BAR - 1e-12 for h in HS for p in ("2010-26", "2016-26"))
            ok &= all(x.loc[(21, p), "dec_yr"] >= MIN_DEC_YR for p in ("2010-26", "2016-26"))
            ok &= all(x.loc[(h, "2023-26"), "diff"] >= -1e-12 for h in HS)
            adopted, why = bool(ok), ("meets the Round 5 bar before the placebo test" if ok else "fails the Round 5 bar")
        else:
            why = "no candidate has 6 decisions a year in 2010-2015"
    res["final"], res["adopted"], res["why"] = final, adopted, why
    say(f"candidates {list(speaks)}; diagnostic={diagnostic}; final={final}; adopted={adopted} ({why})")
    # ---- leak checks
    LK = leak_checks(P, cb, subject, cost_pips, reps=60 if fast else 300)
    LK["rule"] = "diag" if diagnostic else "cond"
    if not diagnostic:
        L2 = leak_checks(P, cb, subject, cost_pips, reps=60 if fast else 300, strict=True)
        L2["rule"] = "strict (post hoc)"
        LK = pd.concat([LK, L2], ignore_index=True)
    LK["diagnostic"] = diagnostic
    Pl = load_panel(cost_pips, shift=-21)
    recl = reconcile(Pl)
    LK = pd.concat([LK, pd.DataFrame([{"table": "leak", "subject": "agree3", "check": "look-ahead control: agreement rule with features from 21 sessions ahead (weekly)",
                                       "acc21_2010-26": float(recl[(recl.h == 21) & (recl["mode"] == "W") & (recl.period == "2010-26")]["acc"].iloc[0])}])], ignore_index=True)
    res["leak"] = LK
    PP = pipeline_placebo(P, R, reps=60 if fast else 300)
    res["pipeline_placebo"] = PP
    if adopted:
        x = LK[LK.check.str.contains("block rotation") & (LK["rule"] == "cond")].iloc[0]
        if max(x["p_placebo_ge_real_21_2010-26"], x["p_placebo_ge_real_42_2010-26"]) > 0.10:
            adopted, why = False, "meets the Round 5 bar but the shuffled-regime placebo matches its gain"
            res["adopted"], res["why"] = adopted, why
    say("leak checks done")
    # ---- streams and protocol report
    reps_ = []
    tb = repU.copy(); tb.insert(1, "variant", "agree3_unconditional"); tb["kind"] = "reference"; tb["cost_pips"] = cost_pips
    tb["final"] = not adopted
    reps_.append(tb)
    books = {"agree3_unconditional": bookU}
    for name, sp in speaks.items():
        bk = rule_book(P, sp, cost_pips)
        books[name] = bk
        tb = report(bk, periods_per_year=252, name=ARM, n_arms=max(1, len(speaks)))
        tb.insert(1, "variant", name); tb["kind"] = "diagnostic" if diagnostic else "candidate"; tb["cost_pips"] = cost_pips
        tb["final"] = bool(adopted and name == final)
        reps_.append(tb)
    dU = daily_gated(P, P.speak["agree3"], cost_pips)
    for name, pnl_ in [("daily_agree3_unconditional", dU)] + [(f"daily_{n}", daily_gated(P, sp, cost_pips)) for n, sp in speaks.items()]:
        tb = report(pnl_, periods_per_year=252, name=ARM, n_arms=max(1, 2 * len(speaks)))
        tb.insert(1, "variant", name); tb["kind"] = "daily-sign stream (added after the first run)"; tb["cost_pips"] = cost_pips; tb["final"] = False
        reps_.append(tb)
        books[name] = pnl_
    P06 = load_panel(0.6)
    for name, sp in [("agree3_unconditional", P.speak["agree3"])] + list(speaks.items()):
        tb = report(rule_book(P06, sp, 0.6), periods_per_year=252, name=ARM, n_arms=max(1, len(speaks)))
        tb.insert(1, "variant", f"{name}_cost0.6"); tb["kind"] = "cost_sensitivity"; tb["cost_pips"] = 0.6; tb["final"] = False
        reps_.append(tb)
    rep = pd.concat(reps_, ignore_index=True)
    fname = final if adopted else "agree3_unconditional"
    out = books[fname][["pos", "net_bp"]].copy()
    out.insert(1, "fwd_bp", D["fwd_1d"].reindex(out.index))
    out["conditional"] = bool(adopted)
    out["rule"] = fname
    res["report"], res["positions"], res["books"] = rep, out, books
    res["variants_run"] = 0 if diagnostic else len(speaks)
    for name in speaks:
        if name.startswith("strict_"):
            sx = books[name][["pos", "net_bp"]].copy()
            sx.insert(1, "fwd_bp", D["fwd_1d"].reindex(sx.index))
            sx["rule"] = name; sx["post_hoc"] = True
            res["strict_positions"] = sx
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        out.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        tabs = [PW, res["power_joint"], ROLL, res["step"], T, S, res["screen_placebo"], res["mix"], C, res["bar"] if "bar" in res else pd.DataFrame(),
                res["mute_log"], LK, PP.assign(table="pipeline_placebo"),
                rec.assign(table="reconcile"), regime_timeline(P, R).assign(table="regime_timeline")]
        if "strict_positions" in res:
            res["strict_positions"].to_parquet(RES / f"{ARM}_strict_posthoc_positions.parquet")
        pd.concat(tabs, ignore_index=True).to_csv(RES / f"{ARM}_tables.csv", index=False)
        try:
            inc = incremental()
            inc.to_csv(RES / f"{ARM}_incremental.csv", index=False)
            res["incremental"] = inc
        except Exception as e:  # pragma: no cover
            say("incremental failed:", e)
    run.last = res
    return out["pos"], rep


def regime_timeline(P: Panel, R: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for v in REGVARS[:-1]:
        for Y in range(2006, 2027):
            m = P.year == Y
            vc = pd.Series(R[v].values[m]).value_counts(normalize=True, dropna=True)
            rows.append({"regime": v, "year": Y, **{f"share_{k}": float(x) for k, x in vc.items()}})
    return pd.DataFrame(rows)


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
    return out


if __name__ == "__main__":
    import pickle
    fast = "fast" in sys.argv
    pos, rep = run(1.2, write=not fast, fast=fast)
    r = run.last
    keep = {k: v for k, v in r.items() if k not in ("P",)}
    scratch = Path(sys.argv[sys.argv.index("--dump") + 1]) if "--dump" in sys.argv else None
    if scratch is not None:
        with open(scratch, "wb") as f:
            pickle.dump(keep, f)
    print(rep[rep.period.isin(["2010-2026", "2016-2026", "2023-2026"])][["variant", "period", "sharpe", "t", "final"]].to_string())
