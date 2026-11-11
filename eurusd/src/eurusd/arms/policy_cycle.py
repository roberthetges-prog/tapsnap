"""Arm T ("policy_cycle"): central-bank reaction functions, the policy cycle and EUR/USD.

Owner's idea: "when the economy is like this and unemployment is like that, rates go down, up or stay; the same
for the euro area. Can we use that?"  Economically: the REACTION FUNCTION. Three questions, in this order:
  (1) can the next move of the Fed / the ECB be predicted from the economy (walk-forward, against naive baselines,
      and separately AT TURNING POINTS);
  (2) what did EUR/USD do around the policy cycle (event study, every episode listed, n in every cell);
  (3) is anything left that the market has not priced (the "economy vs priced" gap and phase rules as an EXTRA VOTE on
      the agreement rule, judged as the Round 5 addendum prescribes).

EVERYTHING IN THIS DOCSTRING (definitions, priors, the candidate list, the selection rule, the success test) WAS
WRITTEN BEFORE ANY RESULT WAS COMPUTED.

POLICY SERIES
* Fed: target (fred_DFEDTAR to 2008-12-15, midpoint of DFEDTARL/U after, extended past the mirror's last date with the
  target range in fomc_decisions.csv). A change is stamped on its ANNOUNCEMENT date = the FOMC date in fomc_decisions.csv
  at most one day before the change date, else the change date itself (the pre-1994 Fed moved between meetings).
  Before 1982-10 (event study only): monthly effective funds rate (fred_FEDFUNDS) as a PROXY.
* ECB: key-rate index = changes of the main refinancing rate before 2014-06-11 and of the deposit facility rate from
  2014-06-11 (the day the deposit rate went negative and became the steering rate). This drops the purely technical
  corridor changes of January 1999 and 8/9 October 2008 and keeps the MRO-only cuts of 2009-05 and 2013 and the
  DFR-only cuts of 2015-12 and 2019-09. A change is stamped on the Governing Council date (ecb_decisions.csv) at most
  14 days before the effective date. Before 1999 (robustness / event study only): German 3-month interbank rate
  (fred_IR3TIB01DEM156N, monthly average) as a PROXY for the Bundesbank.
* PROXY series become pseudo-moves: a monthly change of at least 12.5 bp, stamped the day after the month ends.
* Direction of the cycle (zig-zag): the direction flips when the cumulative counter-move since the last move in the
  trend direction reaches 20 bp (target era) or 75 bp (proxies). That flip is a TURNING POINT: "first cut after hikes"
  or "first hike after cuts".
* Phase, known causally: hiking / cutting while the last move in the trend direction is at most HOLD_DAYS = 122 days
  (four months) old, afterwards "on hold after hikes" / "on hold after cuts". dir3 = +1 hiking, -1 cutting, 0 on hold.
  The day a bank passes the 122 days is its "pause confirmed" event.

(1) REACTION FUNCTIONS (no exchange rate involved anywhere)
Targets: (next) direction of the policy change from just after one scheduled meeting to just after the next one
  (inter-meeting moves count for the window they fall in; features as known on the day of the earlier meeting, so a
  ~6-week-ahead call); (m3, m6) direction of the cumulative change over the next 3 / 6 months from each month-end.
  Classes cut / hold / hike = sign of the change.
Predictors as known on the decision date, with publication lags from the END of the reference month:
  US CPI, core CPI, unemployment, Sahm gap, payrolls, industrial production, retail sales 21 days; US PCE 35 days;
  initial claims week-ending Saturday + 5 days; NFCI week-ending Friday + 5 days; VIX, 2y yields, overnight rates:
  stamped the same day (the FX tests add the feature store's one-calendar-day lag on top of everything);
  euro-area HICP 21 days (index fred_CP0000EZ19M086NEST, y/y by differencing); euro-area unemployment 35 days;
  German CPI 30 days. US reference months 2025-09..2025-11 (shutdown): not before 2026-01-31. Availability dates are
  made non-decreasing. A value older than 150 days is treated as missing.
  Fed features (25): cpi, core cpi, core pce y/y minus 2; 3-month change of cpi y/y; unemployment gap (rate minus its
  trailing 10-year mean), 3/6/12-month change, Sahm gap; payroll growth 3m annualised and 12m; industrial production
  3m annualised and 12m; real retail sales 12m; claims log(4w mean / 52w mean); NFCI and its 13-week change; log VIX
  and its 63-day change; own policy: zig-zag direction, dir3, months since the last move, change over the last 3 and 6
  months, real rate (target minus core cpi y/y).
  ECB features (15): hicp y/y minus 2 and its 3-month change; unemployment gap and 3/6/12-month change; log VIX and its
  63-day change; own policy block as above (real rate = overnight rate minus hicp y/y); the Fed's dir3 and the Fed's
  6-month change. No euro-area activity series exists in data/macro; none was added.
Models: `taylor` = OLS of the change in bp on [inflation gap, unemployment gap, 6-month change of unemployment, real
  rate], classes by training-frequency-matched quantiles of the fitted value; `ologit` = L2-penalised ordered logit
  (proportional odds, penalty 0.02 x |beta|^2 / 2 on the mean log-loss, features standardised with training statistics,
  clipped at +-4, missing = 0; no search) on all features; baselines `always_hold`, `persistence` (same as the last
  decision / the trailing 3- or 6-month direction) and `last_move` (direction of the last move, never "hold").
  For the 6-month target also `market` (ordered logit on the 2y-minus-policy slope alone) and `ologit+market`.
Walk-forward: yearly expanding; the model for year Y uses rows whose label is known before Y-01-01. Fed training from
  1982-10 (month-ends; first test year 1990) and 1989-07 (meetings; first test year 1996); ECB from 1999, first test
  year 2004. Bundesbank 1975-1998 (training from 1961) is a robustness line with the 3-month rate as the "policy rate"
  and a +-25 bp dead band.
Turning points are scored separately: first cut after hikes, first hike after cuts, first pause (hold right after a
  move), resumption (a move in the old direction after a hold), any change vs no change; for the month-end targets the
  rows whose label differs from the trailing direction, and the forecast made at the last month-end before each
  turning point.

(2) EVENT STUDY. Price: synthetic DEM euro 1975-1998, Fed H.10 / ECB reference rate 1999-2002, feature-store closes
  2003+ (the continuous frame of arms/swing.py). Entry = the first close at least one calendar day after the
  announcement; "before" = the 63 sessions ending at the last close before the announcement. Forward windows 21 / 63 /
  126 / 252 sessions. Every turning point, every phase spell and every joint (Fed dir3 x ECB dir3) spell is listed in
  policy_cycle_events.csv; cell tables give n, mean, median and the count of positive / negative episodes.

(3) TRADEABLE SIGNALS (positive = long EUR/USD). Priors from economics, stated before any result:
  E_model(bank) = expected 6-month policy change in bp from the m6 ordered logit (sum of class probabilities x the
  training mean change of the class), E_priced(bank) = the same from the `market` ordered logit (2y yield minus the
  policy rate: US DGS2 minus target; euro area AAA 2y minus the overnight rate (EONIA, EUR-STR + 8.5 bp from 2019-10,
  10-day median), which equals the deposit rate plus a few bp since 2009 and avoids the 100 bp corridor break a
  literal "minus deposit rate" would put into 2004-2008). gap(bank) = E_model - E_priced.
   1 gap_rel        sign(gap_ECB - gap_Fed): the economy says the ECB path is higher relative to the Fed's than is
                    priced -> the market must reprice in favour of the euro. THE OWNER'S IDEA IN ITS PUREST FORM.
   2 gap_rel_strong the same, only when |gap_rel| is above its median over all days before the test year.
   3 gap_fed        -sign(gap_Fed): the economy says more Fed easing than priced -> dollar lower.
   4 gap_ecb        +sign(gap_ECB).
   5 model_rel      sign(E_model_ECB - E_model_Fed): the relative expected path itself.
   6 mkt_rel        sign(E_priced_ECB - E_priced_Fed): what the market prices; relative tightening priced -> currency
                    supported (the standard "rate expectations drive FX" view; the control for the market leg of 1).
   7 phase_rel      sign(ECB dir3 - Fed dir3): the bank that is tightening relative to the other has the stronger
                    currency (policy divergence).
   8 turn63         for 63 sessions after a turning point: Fed first cut while the ECB is not cutting -> long; Fed first
                    hike while the ECB is not hiking -> short; ECB first cut while the Fed is not cutting -> short; ECB
                    first hike while the Fed is not hiking -> long (divergence continues after the turn). Later events
                    override earlier ones.
   9 fed_phase      -Fed dir3 (the dollar follows the Fed cycle).
  10 ecb_phase      +ECB dir3.
  Ten candidates (the limit is 12). All use information stamped at least one calendar day before the session's closing
  date, as the feature store does. Nothing in a signal is fitted to an exchange rate.
Extra-vote form, fixed by the type of signal: DENSE signals (1, 3, 4, 5, 6: a call on every day) -> "agreement rule AND
  the signal agrees"; SPARSE signals (2, 7, 8, 9, 10: zero most of the time) -> "agreement rule UNLESS the signal
  opposes" (a veto). Both forms are tabulated for every candidate; only the declared form counts.
Evaluation exactly as the Round 5 addendum: standalone accuracy at 21 / 42 / 63 sessions, weekly and non-overlapping
  (Wilson); as an extra vote (a) vote rule vs the agreement rule, with decisions per year, (b) calls of the signal when
  the three old signals do NOT agree, (c) paired difference vote minus agreement rule on the weekly grid with a
  circular block bootstrap (block 2h/5 weeks, 2000 draws); daily incremental test; timing placebo (signal shifted by
  +63 and +126 sessions). Test years 2010-2026; 2006-2009 (votes; the house score exists from 2006) and 2004-2009
  (standalone) are extra years where the signal exists.
SUCCESS TEST (Round 5 bar, made operational before results): gain = non-overlapping accuracy of the vote rule minus
  that of the agreement rule. Pass = gain >= 3 points at 21 AND 42 sessions in 2010-26 AND 2016-26; at least 6
  non-overlapping 21-session decisions a year in both periods (the agreement rule itself makes only 5.3 a year at 42
  sessions, so the count is taken at 21); gain >= 0 at 21 and 42 sessions in 2023-26; and in each of those four main
  cells the placebo gain at BOTH shifts is at most half of the real gain.
FINAL (declared): the candidate whose declared vote rule has the highest non-overlapping 21-session accuracy in
  2010-2015, among candidates whose vote rule makes at least 6 such decisions a year in 2010-2015 and removes at least
  10 % of the agreement rule's weekly decisions in 2010-2015 (a veto that never vetoes is not a rule); ties by the
  42-session accuracy. If none is eligible there is no final and the stream written to disk is the standalone signal
  `gap_rel`, flagged as failing. The delivered daily stream is always the STANDALONE daily sign of the final signal
  (pos in -1/0/+1), so that the incremental test measures new information.

ADDED AFTER THE FIRST RUN (labelled as such in the report; none of it changes a candidate, a signal value inside an
evaluated period, the selection or the success test):
  * `rf_diagnostics`: which block of predictors carries the ordered logit, more shrinkage, trailing-direction signs
    (the first run showed the model below plain persistence; nothing was adopted from the diagnostics);
  * the table "when a model departs from persistence, who is right?" (the false-alarm side of the turning points);
  * `turn63` ignores turning points dated before the price sample starts (the first version painted the first 63
    sessions of 2003 with the last pre-2003 event; 2003 is outside every evaluated period);
  * the report writer and the verdict text.
"""
from __future__ import annotations

import math
import sys
import warnings
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.arms import selective as S  # noqa: E402
from eurusd.wf import pnl_from_positions, report  # noqa: E402

MACRO = ROOT / "data" / "macro"
RES = ROOT / "experiments" / "results" / "arms"
REPORTS = ROOT / "reports"
ARM = "policy_cycle"
HOLD_DAYS = 122
ECB_SWITCH = pd.Timestamp("2014-06-11")
FED_TARGET_START = pd.Timestamp("1982-10-01")
STALE_DAYS = 150
ALPHA = 0.02
HORIZONS = (21, 42, 63)
PERIODS = S.PERIODS                               # 2010-26, 2016-26, 2023-26, 2010-15
P3 = ("2010-26", "2016-26", "2023-26")
EXTRA_VOTE = ("2006-09", 2006, 2009)
EXTRA_SOLO = ("2004-09", 2004, 2009)
CANDIDATES = (("gap_rel", "dense"), ("gap_rel_strong", "sparse"), ("gap_fed", "dense"), ("gap_ecb", "dense"), ("model_rel", "dense"),
              ("mkt_rel", "dense"), ("phase_rel", "sparse"), ("turn63", "sparse"), ("fed_phase", "sparse"), ("ecb_phase", "sparse"))
N_CAND = len(CANDIDATES)
FORM = {"dense": "vote_agree", "sparse": "vote_veto"}
PLACEBO_SHIFTS = (63, 126)
CLS = (-1, 0, 1)
CLSN = {-1: "cut", 0: "hold", 1: "hike"}


# ============================================================================= raw series, publication lags
def _ms(name: str, col: str | None = None) -> pd.Series:
    d = pd.read_csv(MACRO / name)
    d[d.columns[0]] = pd.to_datetime(d[d.columns[0]])
    s = d.set_index(d.columns[0])
    s = pd.to_numeric(s[col] if col else s.iloc[:, 0], errors="coerce").astype(float)
    return s[~s.index.duplicated()].sort_index().dropna()


def _monthly(s: pd.Series) -> tuple[pd.Series, np.ndarray]:
    """Full month-start grid; gaps (e.g. US October 2025) are interpolated ONLY as a base for later changes and are
    flagged so that the missing month itself never yields an observation."""
    full = pd.date_range(s.index[0], s.index[-1], freq="MS")
    x = s.reindex(full)
    miss = x.isna().values
    return x.interpolate("linear"), miss


def _pub(x: pd.Series, lag_days: int, us: bool = False, cut: pd.Timestamp | None = None) -> pd.Series:
    """Monthly reference-month series -> series indexed by the date it is assumed to be public."""
    avail = (x.index + pd.offsets.MonthEnd(0)) + pd.Timedelta(days=lag_days)
    avail = pd.Series(avail, index=x.index)
    if us:
        sh = (x.index >= "2025-09-01") & (x.index <= "2025-11-30")
        avail[sh] = np.maximum(avail[sh].values, np.datetime64("2026-01-31"))
    avail = avail.cummax()
    out = pd.Series(x.values, index=pd.DatetimeIndex(avail.values)).dropna()
    out = out[~out.index.duplicated(keep="last")]
    return out if cut is None else out[out.index <= cut]


def _asof(s: pd.Series, dates: pd.DatetimeIndex, max_stale: int | None = STALE_DAYS) -> np.ndarray:
    if len(s) == 0:
        return np.full(len(dates), np.nan)
    pos = s.index.searchsorted(dates, side="right") - 1
    ok = pos >= 0
    out = np.where(ok, s.values[np.maximum(pos, 0)], np.nan)
    if max_stale is not None:
        age = (dates - s.index[np.maximum(pos, 0)]).days.values
        out = np.where(ok & (age <= max_stale), out, np.nan)
    return out


def _daily(name: str, col: str | None = None, cut: pd.Timestamp | None = None) -> pd.Series:
    s = _ms(name, col)
    return s if cut is None else s[s.index <= cut]


# ============================================================================= policy series, phases
@dataclass
class Policy:
    name: str
    lvl: pd.Series               # announced level (step function; index = announcement / availability date)
    moves: pd.DataFrame          # date, d, src ('target' | 'proxy'), s, dir, turn, trend
    meetings: pd.DatetimeIndex   # scheduled decision dates (target era)
    target_start: pd.Timestamp

    def level(self, dates: pd.DatetimeIndex) -> np.ndarray:
        return _asof(self.lvl, dates, None)

    def state(self, dates: pd.DatetimeIndex) -> pd.DataFrame:
        z = self.moves[self.moves["trend"]]
        pos = z["date"].searchsorted(dates, side="right") - 1
        ok = pos >= 0
        p = np.maximum(pos, 0)
        d = np.where(ok, z["dir"].values[p], 0).astype(float)
        last = pd.DatetimeIndex(np.where(ok, z["date"].values[p], np.datetime64("NaT")))
        days = np.where(ok, (dates - last).days.values, np.nan)
        active = ok & (days <= HOLD_DAYS)
        dir3 = np.where(active, d, 0.0)
        phase = np.select([~ok, active & (d > 0), active & (d < 0), d > 0, d < 0],
                          ["unknown", "hiking", "cutting", "hold_after_hikes", "hold_after_cuts"], "unknown")
        src = np.where(ok, z["src"].values[p], "none")
        return pd.DataFrame({"dir": d, "dir3": dir3, "days": days, "phase": phase, "last_d": np.where(ok, z["d"].values[p], np.nan),
                             "src": src}, index=dates)

    def turning_points(self) -> pd.DataFrame:
        t = self.moves[self.moves["turn"]].copy()
        t["type"] = np.where(t["dir"] < 0, "first_cut_after_hikes", "first_hike_after_cuts")
        return t[["date", "type", "d", "src"]].reset_index(drop=True)

    def pauses(self, end: pd.Timestamp) -> pd.DataFrame:
        z = self.moves[self.moves["trend"]].reset_index(drop=True)
        rows = []
        for i in range(len(z)):
            nxt = z["date"].iloc[i + 1] if i + 1 < len(z) else end + pd.Timedelta(days=1)
            p = z["date"].iloc[i] + pd.Timedelta(days=HOLD_DAYS + 1)
            if p <= nxt and p <= end:
                rows.append({"date": p, "type": "pause_after_hikes" if z["dir"].iloc[i] > 0 else "pause_after_cuts", "d": 0.0, "src": z["src"].iloc[i]})
        return pd.DataFrame(rows)


def _zigzag(m: pd.DataFrame) -> pd.DataFrame:
    m = m.sort_values("date").reset_index(drop=True)
    cur, pend = 0, 0.0
    dirs, turn, trend = [], [], []
    for d, src in zip(m["d"].values, m["src"].values):
        thr = 0.75 if src == "proxy" else 0.20
        s = 1 if d > 0 else -1
        tu, tr = False, False
        if cur == 0:
            cur, tr = s, True
        elif s == cur:
            pend, tr = 0.0, True
        else:
            pend += d
            if abs(pend) >= thr - 1e-9:
                cur, pend, tu, tr = s, 0.0, True, True
        dirs.append(cur); turn.append(tu); trend.append(tr)
    m["dir"], m["turn"], m["trend"] = dirs, turn, trend
    return m


def _proxy_moves(monthly: pd.Series, before: pd.Timestamp) -> tuple[pd.DataFrame, pd.Series]:
    avail = (monthly.index + pd.offsets.MonthEnd(0)) + pd.Timedelta(days=1)
    lv = pd.Series(monthly.values, index=avail)
    lv = lv[lv.index < before]
    d = lv.diff()
    mv = d[d.abs() >= 0.125 - 1e-9]
    return pd.DataFrame({"date": mv.index, "d": mv.values, "src": "proxy"}), lv


def fed_policy(cut: pd.Timestamp | None = None) -> Policy:
    t = _ms("fred_DFEDTAR.csv")
    mid = (_ms("fred_DFEDTARU.csv") + _ms("fred_DFEDTARL.csv")) / 2
    lv = pd.concat([t, mid]).sort_index()
    lv = lv[~lv.index.duplicated(keep="last")]
    f = pd.read_csv(MACRO / "fomc_decisions.csv", parse_dates=["date"])
    for d, s in zip(f["date"], f["fed_funds_target"]):               # extend past the mirror's last date
        if d > lv.index[-1] and isinstance(s, str):
            nums = [float(x) for x in s.replace("%", "").replace("–", " ").replace("-", " ").split()]
            if nums:
                lv.loc[d + pd.Timedelta(days=1)] = float(np.mean(nums))
    lv = lv.sort_index()
    ch = lv.diff()
    ch = ch[ch.abs() > 1e-9]
    fd = pd.DatetimeIndex(f["date"])
    ann = []
    for d in ch.index:
        c = fd[(fd <= d) & (fd >= d - pd.Timedelta(days=1))]
        ann.append(c.max() if len(c) else d)
    tm = pd.DataFrame({"date": pd.DatetimeIndex(ann), "d": ch.values, "src": "target"})
    pm, plv = _proxy_moves(_ms("fred_FEDFUNDS.csv"), lv.index[0])
    steps = pd.Series(np.r_[lv.iloc[0], lv.iloc[0] + np.cumsum(tm["d"].values)], index=pd.DatetimeIndex([lv.index[0]]).append(pd.DatetimeIndex(tm["date"])))
    level = pd.concat([plv, steps])
    level = level[~level.index.duplicated(keep="last")].sort_index()
    moves = _zigzag(pd.concat([pm, tm], ignore_index=True))
    meet = pd.DatetimeIndex(f.loc[f["scheduled"] == True, "date"])  # noqa: E712
    if cut is not None:
        level, moves, meet = level[level.index <= cut], moves[moves["date"] <= cut].reset_index(drop=True), meet[meet <= cut]
    return Policy("fed", level, moves, meet, FED_TARGET_START)


def ecb_policy(cut: pd.Timestamp | None = None) -> Policy:
    p = pd.read_csv(MACRO / "ecb_policy_rates.csv", parse_dates=["date"]).set_index("date")
    mro, dfr = p["main_refinancing_rate"].astype(float), p["deposit_facility_rate"].astype(float)
    d = pd.Series(np.where(p.index < ECB_SWITCH, mro.diff().values, dfr.diff().values), index=p.index)
    ch = d[d.abs() > 1e-9]
    e = pd.read_csv(MACRO / "ecb_decisions.csv", parse_dates=["date"])
    ed = pd.DatetimeIndex(e["date"])
    ann = []
    for x in ch.index:
        c = ed[(ed <= x) & (ed >= x - pd.Timedelta(days=14))]
        ann.append(c.max() if len(c) else x)
    tm = pd.DataFrame({"date": pd.DatetimeIndex(ann), "d": ch.values, "src": "target"})
    start = pd.Timestamp("1999-01-01")
    pm, plv = _proxy_moves(_ms("fred_IR3TIB01DEM156N.csv"), start)
    steps = pd.Series(np.r_[mro.iloc[0], mro.iloc[0] + np.cumsum(tm["d"].values)], index=pd.DatetimeIndex([start]).append(pd.DatetimeIndex(tm["date"])))
    level = pd.concat([plv, steps])
    level = level[~level.index.duplicated(keep="last")].sort_index()
    moves = _zigzag(pd.concat([pm, tm], ignore_index=True))
    meet = ed
    if cut is not None:
        level, moves, meet = level[level.index <= cut], moves[moves["date"] <= cut].reset_index(drop=True), meet[meet <= cut]
    return Policy("ecb", level, moves, meet, start)


def ea_overnight(cut: pd.Timestamp | None = None) -> pd.Series:
    o = pd.read_csv(MACRO / "ea_overnight_rates.csv", parse_dates=["date"]).set_index("date")
    x = o["eonia"].astype(float).where(o.index < "2019-10-01", o["estr"].astype(float) + 0.085)
    x = x.dropna().rolling(10, min_periods=3).median().dropna()
    return x if cut is None else x[x.index <= cut]


# ============================================================================= features (as known on each date)
def _yoy(x: pd.Series, k: int = 12) -> pd.Series:
    return (x / x.shift(k) - 1.0) * 100.0


def _ann(x: pd.Series, k: int) -> pd.Series:
    return ((x / x.shift(k)) ** (12.0 / k) - 1.0) * 100.0


def _own_block(pol: Policy, dates: pd.DatetimeIndex) -> pd.DataFrame:
    st = pol.state(dates)
    lv = pol.level(dates)
    out = pd.DataFrame(index=dates)
    out["own_dir"] = st["dir"].values
    out["own_dir3"] = st["dir3"].values
    out["own_msince"] = np.minimum(st["days"].values / 30.44, 36.0) / 12.0
    out["own_chg3"] = lv - pol.level(dates - pd.Timedelta(days=91))
    out["own_chg6"] = lv - pol.level(dates - pd.Timedelta(days=182))
    return out


def us_features(dates: pd.DatetimeIndex, fed: Policy, cut: pd.Timestamp | None = None, extra_lag: int = 0) -> pd.DataFrame:
    """extra_lag (days) is added to every publication lag: > 0 = staler, < 0 = look-ahead (leak control only)."""
    X = pd.DataFrame(index=dates)
    L = lambda n: n + extra_lag                                                    # noqa: E731
    A = lambda s, lag: _asof(_pub(s, L(lag), True, cut), dates)                    # noqa: E731

    def tr(name, f):
        x, miss = _monthly(_ms(name))
        y = f(x)
        y[miss] = np.nan
        return y

    cpi, _ = _monthly(_ms("fred_CPIAUCSL.csv"))
    X["cpi"] = A(tr("fred_CPIAUCSL.csv", _yoy), 21) - 2.0
    X["core"] = A(tr("fred_CPILFESL.csv", _yoy), 21) - 2.0
    X["corepce"] = A(tr("fred_PCEPILFE.csv", _yoy), 35) - 2.0
    X["cpi_d3"] = A(tr("fred_CPIAUCSL.csv", lambda x: _yoy(x).diff(3)), 21)
    u = "fred_UNRATE.csv"
    X["u_gap"] = A(tr(u, lambda x: x - x.rolling(120, min_periods=36).mean()), 21)
    for k in (3, 6, 12):
        X[f"du{k}"] = A(tr(u, lambda x, k=k: x.diff(k)), 21)
    X["sahm"] = A(tr("fred_SAHMREALTIME.csv", lambda x: x), 21)
    X["pay3"] = A(tr("fred_PAYEMS.csv", lambda x: _ann(x, 3)), 21)
    X["pay12"] = A(tr("fred_PAYEMS.csv", _yoy), 21)
    X["ip3"] = A(tr("fred_INDPRO.csv", lambda x: _ann(x, 3)), 21)
    X["ip12"] = A(tr("fred_INDPRO.csv", _yoy), 21)
    rs, _ = _monthly(_ms("fred_RSAFS.csv"))
    X["rs12"] = A(_yoy(rs / cpi.reindex(rs.index)), 21)
    ic = _ms("fred_ICSA.csv")
    cl = np.log(ic.rolling(4).mean() / ic.rolling(52).mean()).dropna()
    cl.index = cl.index + pd.Timedelta(days=L(5))
    X["claims"] = _asof(cl if cut is None else cl[cl.index <= cut], dates, 60)
    nf = _ms("fred_NFCI.csv")
    for nm, s in (("nfci", nf), ("nfci_d13", nf.diff(13).dropna())):
        s = s.copy(); s.index = s.index + pd.Timedelta(days=L(5))
        X[nm] = _asof(s if cut is None else s[s.index <= cut], dates, 60)
    X = X.join(_vix_block(dates, cut, extra_lag))
    X = X.join(_own_block(fed, dates))
    core_raw = X["core"] + 2.0
    X["own_real"] = fed.level(dates) - core_raw
    X["slope"] = _asof(_shift_days(_daily("fred_DGS2.csv", None, cut), extra_lag), dates, 10) - fed.level(dates)
    return X


def _shift_days(s: pd.Series, k: int) -> pd.Series:
    if k == 0:
        return s
    s = s.copy(); s.index = s.index + pd.Timedelta(days=k)
    return s


def _vix_block(dates: pd.DatetimeIndex, cut, extra_lag: int = 0) -> pd.DataFrame:
    v = np.log(_daily("fred_VIXCLS.csv", None, cut))
    out = pd.DataFrame(index=dates)
    out["vix"] = _asof(_shift_days(v, extra_lag), dates, 10)
    out["vix_d63"] = _asof(_shift_days(v.diff(63).dropna(), extra_lag), dates, 10)
    return out


def ea_features(dates: pd.DatetimeIndex, ecb: Policy, fed: Policy, cut: pd.Timestamp | None = None, extra_lag: int = 0) -> pd.DataFrame:
    X = pd.DataFrame(index=dates)
    L = lambda n: n + extra_lag                                                    # noqa: E731
    hx, _ = _monthly(_ms("fred_CP0000EZ19M086NEST.csv"))
    hy = _yoy(hx)
    X["hicp"] = _asof(_pub(hy, L(21), False, cut), dates) - 2.0
    X["hicp_d3"] = _asof(_pub(hy.diff(3), L(21), False, cut), dates)
    un = pd.read_csv(MACRO / "ea_unemployment.csv")
    u = pd.Series(un["unemployment_rate"].astype(float).values, index=pd.to_datetime(un["month"]))
    u, _ = _monthly(u)
    X["u_gap"] = _asof(_pub(u - u.rolling(120, min_periods=36).mean(), L(35), False, cut), dates)
    for k in (3, 6, 12):
        X[f"du{k}"] = _asof(_pub(u.diff(k), L(35), False, cut), dates)
    X = X.join(_vix_block(dates, cut, extra_lag))
    X = X.join(_own_block(ecb, dates))
    on = _asof(_shift_days(ea_overnight(cut), extra_lag), dates, 10)
    X["own_real"] = on - (X["hicp"] + 2.0)
    X["fed_dir3"] = fed.state(dates)["dir3"].values
    X["fed_chg6"] = fed.level(dates) - fed.level(dates - pd.Timedelta(days=182))
    aaa = pd.read_csv(MACRO / "ea_aaa_yield_curve.csv", parse_dates=["date"]).set_index("date")["aaa_spot_2y"].astype(float).dropna()
    aaa = aaa if cut is None else aaa[aaa.index <= cut]
    X["slope"] = _asof(_shift_days(aaa, extra_lag), dates, 10) - on
    return X


US_FULL = ["cpi", "core", "corepce", "cpi_d3", "u_gap", "du3", "du6", "du12", "sahm", "pay3", "pay12", "ip3", "ip12", "rs12", "claims", "nfci",
           "nfci_d13", "vix", "vix_d63", "own_dir", "own_dir3", "own_msince", "own_chg3", "own_chg6", "own_real"]
US_TAYLOR = ["core", "u_gap", "du6", "own_real"]
EA_FULL = ["hicp", "hicp_d3", "u_gap", "du3", "du6", "du12", "vix", "vix_d63", "own_dir", "own_dir3", "own_msince", "own_chg3", "own_chg6",
           "own_real", "fed_dir3", "fed_chg6"]
EA_TAYLOR = ["hicp", "u_gap", "du6", "own_real"]


# ============================================================================= models
def _sig(x):
    return 1.0 / (1.0 + np.exp(-np.clip(x, -35, 35)))


def ologit_fit(Z: np.ndarray, y: np.ndarray, alpha: float = ALPHA):
    """Penalised proportional-odds logit for classes -1/0/1. Half a pseudo-observation per class at x = 0 keeps the
    thresholds finite when a class is missing in the training window."""
    n, p = Z.shape
    Zp = np.vstack([Z, np.zeros((3, p))])
    yp = np.r_[y, -1, 0, 1]
    w = np.r_[np.ones(n), 0.5, 0.5, 0.5]
    lo, mid, hi = yp < 0, yp == 0, yp > 0
    W = w.sum()

    def nll(th):
        b, a, c = th[:p], th[p], th[p + 1]
        t1, t2 = a, a + math.exp(c)
        eta = Zp @ b
        F1, F2 = _sig(t1 - eta), _sig(t2 - eta)
        pm = np.maximum(F2 - F1, 1e-12)
        ll = w * np.where(lo, np.log(np.maximum(F1, 1e-12)), np.where(hi, np.log(np.maximum(1 - F2, 1e-12)), np.log(pm)))
        f1, f2 = F1 * (1 - F1), F2 * (1 - F2)
        g_eta = w * np.where(lo, -(1 - F1), np.where(hi, F2, -(f2 - f1) / pm))
        g_t1 = w * np.where(lo, 1 - F1, np.where(hi, 0.0, -f1 / pm))
        g_t2 = w * np.where(lo, 0.0, np.where(hi, -F2, f2 / pm))
        val = -ll.sum() / W + 0.5 * alpha * float(b @ b)
        gb = -(Zp.T @ g_eta) / W + alpha * b
        ga = -(g_t1.sum() + g_t2.sum()) / W
        gc = -(g_t2.sum() * math.exp(c)) / W
        return val, np.r_[gb, ga, gc]

    th0 = np.r_[np.zeros(p), -1.0, math.log(2.0)]
    r = minimize(nll, th0, jac=True, method="L-BFGS-B", options={"maxiter": 500})
    return r.x


def ologit_proba(th: np.ndarray, Z: np.ndarray) -> np.ndarray:
    p = Z.shape[1]
    b, a, c = th[:p], th[p], th[p + 1]
    eta = Z @ b
    F1, F2 = _sig(a - eta), _sig(a + math.exp(c) - eta)
    return np.column_stack([F1, np.maximum(F2 - F1, 0.0), 1 - F2])


def _standardise(Xtr: np.ndarray):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        mu, sd = np.nanmean(Xtr, axis=0), np.nanstd(Xtr, axis=0)
    nn = np.isfinite(Xtr).sum(axis=0)
    use = (nn >= 24) & np.isfinite(sd) & (sd > 1e-9)
    mu = np.where(use, mu, 0.0)
    sd = np.where(use, sd, np.inf)
    return mu, sd


def _z(X: np.ndarray, mu, sd) -> np.ndarray:
    return np.nan_to_num(np.clip((X - mu) / sd, -4, 4))


def wf_model(G: pd.DataFrame, cols: list[str], kind: str, years, Xd: pd.DataFrame | None = None, need: list[str] | None = None,
             min_train: int = 30, perm_seed: int | None = None, keep: dict | None = None) -> dict:
    """G: one row per decision with columns `origin`, `label_end`, `y` (-1/0/1), `dbp` and the features.
    kind: 'ologit' or 'taylor'. Returns OOS class predictions, probabilities and expected change (bp) on G, and the
    same on the daily frame Xd (rows of year Y scored with the model of year Y)."""
    n = len(G)
    pred = np.full(n, np.nan); proba = np.full((n, 3), np.nan); exp = np.full(n, np.nan)
    dP = np.full((len(Xd), 3), np.nan) if Xd is not None else None
    dE = np.full(len(Xd), np.nan) if Xd is not None else None
    Xall = G[cols].values.astype(float)
    y = G["y"].values.astype(float)
    dbp = np.clip(G["dbp"].values.astype(float), -300, 300)
    oy = G["origin"].dt.year.values
    okrow = np.isfinite(y)
    if need:
        okrow &= np.isfinite(G[need].values.astype(float)).all(axis=1)
    rng = np.random.default_rng(perm_seed) if perm_seed is not None else None
    for Y in years:
        start = pd.Timestamp(f"{Y}-01-01")
        tr = np.where(okrow & (G["label_end"] < start).values)[0]
        te = np.where(oy == Y)[0]
        if len(tr) < min_train:
            continue
        ytr, dtr = y[tr].copy(), dbp[tr].copy()
        if rng is not None:
            pm = rng.permutation(len(tr)); ytr, dtr = ytr[pm], dtr[pm]
        mu, sd = _standardise(Xall[tr])
        Ztr = _z(Xall[tr], mu, sd)
        cm = np.array([dtr[ytr == k].mean() if (ytr == k).any() else 25.0 * k for k in CLS])
        if kind == "ologit":
            th = ologit_fit(Ztr, ytr)
            f = lambda Xn: ologit_proba(th, _z(Xn, mu, sd))                        # noqa: E731
            model = {"theta": th, "mu": mu, "sd": sd, "class_mean_bp": cm, "cols": cols}
        else:
            A = np.column_stack([np.ones(len(tr)), Ztr])
            beta, *_ = np.linalg.lstsq(A, dtr, rcond=None)
            fit = A @ beta
            sc, sh = float((ytr < 0).mean()), float((ytr > 0).mean())
            qlo = np.quantile(fit, sc) if sc > 0 else -np.inf
            qhi = np.quantile(fit, 1 - sh) if sh > 0 else np.inf

            def f(Xn, beta=beta, qlo=qlo, qhi=qhi, mu=mu, sd=sd):
                v = np.column_stack([np.ones(len(Xn)), _z(Xn, mu, sd)]) @ beta
                c = np.where(v < qlo, -1, np.where(v > qhi, 1, 0))
                P = np.zeros((len(Xn), 3)); P[np.arange(len(Xn)), c + 1] = 1.0
                return P
            model = {"beta": beta, "mu": mu, "sd": sd, "cols": cols}
        if len(te):
            P = f(Xall[te])
            bad = ~np.isfinite(G[need].values.astype(float)[te]).all(axis=1) if need else np.zeros(len(te), bool)
            P[bad] = np.nan
            proba[te] = P
            pred[te] = np.where(bad, np.nan, np.argmax(np.nan_to_num(P), axis=1) - 1)
            exp[te] = P @ cm
        if Xd is not None:
            dd = np.where(Xd.index.year == Y)[0]
            if len(dd):
                Xn = Xd[cols].values.astype(float)[dd]
                P = f(Xn)
                if need:
                    P[~np.isfinite(Xd[need].values.astype(float)[dd]).all(axis=1)] = np.nan
                dP[dd] = P; dE[dd] = P @ cm
        if keep is not None:
            keep[Y] = model
    return {"pred": pred, "proba": proba, "exp": exp, "dP": dP, "dE": dE}


# ============================================================================= (1) reaction-function experiments
def _grid_month(pol: Policy, X: pd.DataFrame, h: int, start: pd.Timestamp, end: pd.Timestamp, band: float = 0.0) -> pd.DataFrame:
    G = X.copy()
    o = G.index
    G["origin"] = o
    le = o + pd.offsets.MonthEnd(h)
    G["label_end"] = le
    d = pol.level(pd.DatetimeIndex(le)) - pol.level(o)
    d = np.where(le <= end, d, np.nan)
    G["dbp"] = d * 100
    G["y"] = np.where(np.isfinite(d), np.where(d > band + 1e-9, 1.0, np.where(d < -band - 1e-9, -1.0, 0.0)), np.nan)
    tr = pol.level(o) - pol.level(o - pd.offsets.MonthEnd(h))
    G["b_persistence"] = np.where(tr > band + 1e-9, 1.0, np.where(tr < -band - 1e-9, -1.0, 0.0))
    G["b_last_move"] = pol.state(o)["dir"].values
    G["b_always_hold"] = 0.0
    return G[G["origin"] >= start].reset_index(drop=True)


def _grid_meeting(pol: Policy, feat, end: pd.Timestamp) -> pd.DataFrame:
    m = pol.meetings[(pol.meetings >= pol.target_start) & (pol.meetings <= end)]
    o, le = m[:-1], m[1:]
    G = feat(o).reset_index(drop=True)
    G["origin"], G["label_end"] = o, le
    d = pol.level(le) - pol.level(o)
    G["dbp"] = d * 100
    G["y"] = np.sign(np.round(d, 6))
    prev = np.r_[np.nan, G["y"].values[:-1]]
    G["b_persistence"] = np.nan_to_num(prev)
    G["b_last_move"] = pol.state(o)["dir"].values
    G["b_always_hold"] = 0.0
    return G


def _turn_masks_meeting(y: np.ndarray) -> dict:
    n = len(y)
    prev = np.r_[np.nan, y[:-1]]
    lastnz = np.full(n, np.nan)
    cur = np.nan
    for i in range(n):
        lastnz[i] = cur
        if y[i] != 0 and np.isfinite(y[i]):
            cur = y[i]
    return {"first cut after hikes": (y == -1) & (lastnz == 1), "first hike after cuts": (y == 1) & (lastnz == -1),
            "first pause (hold after a move)": (y == 0) & np.isfinite(prev) & (prev != 0),
            "resumption (same direction after a hold)": (y != 0) & (prev == 0) & (lastnz == y),
            "any change vs previous decision": np.isfinite(prev) & (y != prev), "no change vs previous decision": np.isfinite(prev) & (y == prev)}


def _acc_rows(bank: str, target: str, G: pd.DataFrame, preds: dict, subsets: dict, periods) -> list[dict]:
    y = G["y"].values
    yr = G["origin"].dt.year.values
    rows = []
    for plab, a, b in periods:
        base = np.isfinite(y) & (yr >= a) & (yr <= b) & np.isfinite(preds["ologit"])
        for slab, m in subsets.items():
            k = base & m
            r = {"bank": bank, "target": target, "period": plab, "subset": slab, "n": int(k.sum())}
            if k.sum():
                r.update({"share_cut": float((y[k] < 0).mean()), "share_hold": float((y[k] == 0).mean()), "share_hike": float((y[k] > 0).mean())})
                for nm, p in preds.items():
                    kk = k & np.isfinite(p)
                    r[f"acc_{nm}"] = float((p[kk] == y[kk]).mean()) if kk.sum() else np.nan
                    if nm in ("market", "ologit+market"):
                        r[f"n_{nm}"] = int(kk.sum())
            rows.append(r)
    return rows


def _confusion(bank: str, target: str, y: np.ndarray, p: np.ndarray, model: str, period: str) -> list[dict]:
    rows = []
    for a in CLS:
        r = {"bank": bank, "target": target, "period": period, "model": model, "actual": CLSN[a], "n": int((y == a).sum())}
        for q in CLS:
            r[f"pred_{CLSN[q]}"] = int(((y == a) & (p == q)).sum())
        rows.append(r)
    return rows


def reaction_functions(end: pd.Timestamp, verbose: bool = True, extra_lag: int = 0, perm_seed: int | None = None, drop: tuple = (),
                       light: bool = False) -> dict:
    """All reaction-function experiments. Returns accuracy rows, confusion rows, turning-point rows, coefficient tables
    and (unless light) the daily model-implied / market-priced 6-month change for each bank."""
    fed, ecb = fed_policy(), ecb_policy()
    acc, conf, tp_rows, coef, grids, dis = [], [], [], [], {}, []
    daily = {}
    cfg = {"fed": dict(pol=fed, feat=lambda d: us_features(d, fed, None, extra_lag), full=[c for c in US_FULL if c not in drop], taylor=US_TAYLOR,
                       m_start=FED_TARGET_START, m_years=range(1990, 2027), meet_years=range(1996, 2027),
                       periods_m=(("1990-2026", 1990, 2026), ("2004-2026", 2004, 2026), ("2010-2026", 2010, 2026)),
                       periods_meet=(("1996-2026", 1996, 2026), ("2004-2026", 2004, 2026), ("2010-2026", 2010, 2026))),
           "ecb": dict(pol=ecb, feat=lambda d: ea_features(d, ecb, fed, None, extra_lag), full=[c for c in EA_FULL if c not in drop], taylor=EA_TAYLOR,
                       m_start=pd.Timestamp("1999-01-01"), m_years=range(2004, 2027), meet_years=range(2004, 2027),
                       periods_m=(("2004-2026", 2004, 2026), ("2010-2026", 2010, 2026)),
                       periods_meet=(("2004-2026", 2004, 2026), ("2010-2026", 2010, 2026)))}
    for bank, c in cfg.items():
        pol = c["pol"]
        me = pd.date_range(c["m_start"], end, freq="ME")
        Xm = c["feat"](me)
        dgrid = pd.date_range("1989-12-25", end, freq="D") if not light else None
        Xd = c["feat"](dgrid) if dgrid is not None else None
        for target in ("next", "m3", "m6"):
            if target == "next":
                G = _grid_meeting(pol, c["feat"], end)
                years, periods = c["meet_years"], c["periods_meet"]
                subsets = {"all": np.ones(len(G), bool), **_turn_masks_meeting(G["y"].values)}
            else:
                h = int(target[1:])
                G = _grid_month(pol, Xm, h, c["m_start"], end)
                years, periods = c["m_years"], c["periods_m"]
                chg = G["y"].values != G["b_persistence"].values
                subsets = {"all": np.ones(len(G), bool), "label differs from the trailing direction": chg, "label equals the trailing direction": ~chg}
            keep = {}
            want_daily = (target == "m6") and Xd is not None
            ol = wf_model(G, c["full"], "ologit", years, Xd if want_daily else None, perm_seed=perm_seed, keep=keep)
            ty = wf_model(G, c["taylor"], "taylor", years, perm_seed=perm_seed)
            preds = {"always_hold": G["b_always_hold"].values, "persistence": G["b_persistence"].values, "last_move": G["b_last_move"].values,
                     "taylor": ty["pred"], "ologit": ol["pred"]}
            if target == "m6":
                mk = wf_model(G, ["slope"], "ologit", years, Xd if want_daily else None, need=["slope"], perm_seed=perm_seed)
                bo = wf_model(G, c["full"] + ["slope"], "ologit", years, need=["slope"], perm_seed=perm_seed)
                preds["market"], preds["ologit+market"] = mk["pred"], bo["pred"]
                if want_daily:
                    daily[bank] = pd.DataFrame({"p_cut": ol["dP"][:, 0], "p_hold": ol["dP"][:, 1], "p_hike": ol["dP"][:, 2], "model_bp": ol["dE"],
                                                "priced_bp": mk["dE"], "slope": Xd["slope"].values}, index=dgrid)
                # expected-change skill (RMSE of the 6-month change in bp), macro vs market vs zero
                k = np.isfinite(G["dbp"].values) & np.isfinite(ol["exp"]) & np.isfinite(mk["exp"]) & (G["origin"].dt.year.values >= 2010)
                if k.sum():
                    d_ = G["dbp"].values[k]
                    acc.append({"bank": bank, "target": target, "period": "2010-2026", "subset": "RMSE of the 6m change, bp (rows with a market slope)",
                                "n": int(k.sum()), "acc_always_hold": float(np.sqrt((d_ ** 2).mean())), "acc_ologit": float(np.sqrt(((d_ - ol["exp"][k]) ** 2).mean())),
                                "acc_market": float(np.sqrt(((d_ - mk["exp"][k]) ** 2).mean())), "acc_ologit+market": float(np.sqrt(((d_ - bo["exp"][k]) ** 2).mean()))})
            acc += _acc_rows(bank, target, G, preds, subsets, periods)
            y = G["y"].values
            for mdl in ("taylor", "ologit", "market"):          # when a model departs from persistence, who is right?
                if mdl not in preds:
                    continue
                for plab, a, b in periods[:1] + periods[-1:]:
                    inp = np.isfinite(y) & np.isfinite(preds[mdl]) & np.isfinite(preds["ologit"]) & (G["origin"].dt.year.values >= a) & (G["origin"].dt.year.values <= b)
                    k = inp & (preds[mdl] != preds["persistence"])
                    dis.append({"bank": bank, "target": target, "period": plab, "model": mdl, "n_all": int(inp.sum()), "n_disagree": int(k.sum()),
                                "model_right": float((preds[mdl][k] == y[k]).mean()) if k.sum() else np.nan,
                                "persistence_right": float((preds["persistence"][k] == y[k]).mean()) if k.sum() else np.nan,
                                "neither_right": float(((preds[mdl][k] != y[k]) & (preds["persistence"][k] != y[k])).mean()) if k.sum() else np.nan})
            for plab, a, b in periods[:1] + periods[-1:]:
                k = np.isfinite(y) & np.isfinite(ol["pred"]) & (G["origin"].dt.year.values >= a) & (G["origin"].dt.year.values <= b)
                conf += _confusion(bank, target, y[k], ol["pred"][k], "ologit", plab)
                conf += _confusion(bank, target, y[k], ty["pred"][k], "taylor", plab)
            if target != "next":          # the forecast made at the last month-end before each turning point
                tps = pol.turning_points()
                tps = tps[(tps["src"] == "target") & (tps["date"] >= pd.Timestamp(f"{min(years)}-02-01"))]
                for _, t in tps.iterrows():
                    j = G["origin"].searchsorted(t["date"], side="left") - 1
                    if j < 0 or not np.isfinite(ol["pred"][j]):
                        continue
                    r = {"bank": bank, "target": target, "turn_date": t["date"].date(), "type": t["type"], "origin": G["origin"].iloc[j].date(),
                         "label": G["y"].iloc[j]}
                    for nm, p in preds.items():
                        r[f"pred_{nm}"] = p[j]
                    r["p_cut"], r["p_hold"], r["p_hike"] = ol["proba"][j]
                    tp_rows.append(r)
            if keep:
                Y = max(keep)
                th, cols = keep[Y]["theta"], keep[Y]["cols"]
                k = np.isfinite(y)
                Z = _z(G[cols].values.astype(float), keep[Y]["mu"], keep[Y]["sd"])
                for j, cn in enumerate(cols):
                    cr = float(np.corrcoef(Z[k, j], y[k])[0, 1]) if Z[k, j].std() > 0 else 0.0
                    coef.append({"bank": bank, "target": target, "fit_year": Y, "feature": cn, "coef_std": float(th[j]), "corr_with_label": cr})
            G = G.copy()
            for nm, p in preds.items():
                G[f"pred_{nm}"] = p
            for j, nm in enumerate(("p_cut", "p_hold", "p_hike")):
                G[nm] = ol["proba"][:, j]
            G["exp_bp"] = ol["exp"]
            grids[(bank, target)] = G
            if verbose:
                print(f"  reaction function {bank}/{target}: {len(G)} rows", flush=True)
    return {"acc": pd.DataFrame(acc), "conf": pd.DataFrame(conf), "tp": pd.DataFrame(tp_rows), "coef": pd.DataFrame(coef), "grids": grids,
            "daily": daily, "fed": fed, "ecb": ecb, "dis": pd.DataFrame(dis)}


def bundesbank_robustness() -> pd.DataFrame:
    """Robustness line only: the German 3-month interbank rate as the Bundesbank's 'policy rate', 1961-1998."""
    r = _ms("fred_IR3TIB01DEM156N.csv")
    avail = (r.index + pd.offsets.MonthEnd(0)) + pd.Timedelta(days=1)
    lv = pd.Series(r.values, index=avail)
    lv = lv[lv.index < "1999-01-05"]
    pol = Policy("bbk", lv, _zigzag(_proxy_moves(r, pd.Timestamp("1999-01-05"))[0]), pd.DatetimeIndex([]), lv.index[0])
    me = pd.date_range("1961-01-31", "1998-12-31", freq="ME")
    cx, _ = _monthly(_ms("fred_DEUCPIALLMINMEI.csv"))
    cy = _yoy(cx)
    X = pd.DataFrame(index=me)
    X["cpi"] = _asof(_pub(cy, 30), me) - 2.0
    X["cpi_d3"] = _asof(_pub(cy.diff(3), 30), me)
    X = X.join(_own_block(pol, me))
    X["own_real"] = pol.level(me) - (X["cpi"] + 2.0)
    ff = _ms("fred_FEDFUNDS.csv")
    ffl = pd.Series(ff.values, index=(ff.index + pd.offsets.MonthEnd(0)) + pd.Timedelta(days=1))
    X["fed_chg6"] = _asof(ffl, me, None) - _asof(ffl, me - pd.Timedelta(days=182), None)
    rows = []
    for h in (3, 6):
        G = _grid_month(pol, X, h, pd.Timestamp("1961-01-01"), pd.Timestamp("1998-12-31"), band=0.25)
        years = range(1975, 1999)
        ol = wf_model(G, ["cpi", "cpi_d3", "own_dir", "own_dir3", "own_msince", "own_chg3", "own_chg6", "own_real", "fed_chg6"], "ologit", years)
        ty = wf_model(G, ["cpi", "cpi_d3", "own_real"], "taylor", years)
        preds = {"always_hold": G["b_always_hold"].values, "persistence": G["b_persistence"].values, "last_move": G["b_last_move"].values,
                 "taylor": ty["pred"], "ologit": ol["pred"]}
        chg = G["y"].values != G["b_persistence"].values
        rows += _acc_rows("bundesbank (3m rate proxy, +-25bp band)", f"m{h}", G, preds,
                          {"all": np.ones(len(G), bool), "label differs from the trailing direction": chg}, (("1975-1998", 1975, 1998),))
    return pd.DataFrame(rows)


def rf_diagnostics(end: pd.Timestamp) -> pd.DataFrame:
    """ADDED AFTER THE FIRST RUN OF PART (1) (diagnostic only, nothing is selected from it and no signal uses it): which
    block of predictors carries the ordered logit, and does more shrinkage or handing it the trailing direction help?"""
    fed, ecb = fed_policy(), ecb_policy()
    rows = []

    def add_tr(X, pol):
        lv = pol.level(X.index)
        for nm, k in (("own_tr1", 45), ("own_tr3", 91), ("own_tr6", 182)):
            X[nm] = np.sign(np.round(lv - pol.level(X.index - pd.Timedelta(days=k)), 6))
        return X

    for bank, pol, feat, full, start, years in (("fed", fed, lambda d: add_tr(us_features(d, fed), fed), US_FULL, FED_TARGET_START, range(1990, 2027)),
                                                ("ecb", ecb, lambda d: add_tr(ea_features(d, ecb, fed), ecb), EA_FULL, pd.Timestamp("1999-01-01"), range(2004, 2027))):
        Xm = feat(pd.date_range(start, end, freq="ME"))
        own = [c for c in full if c.startswith("own")]
        mac = [c for c in full if not c.startswith("own")]
        tr = ["own_tr1", "own_tr3", "own_tr6"]
        for h in (3, 6):
            G = _grid_month(pol, Xm, h, start, end)
            y, yr = G["y"].values, G["origin"].dt.year.values
            base = wf_model(G, full, "ologit", years)["pred"]
            k = np.isfinite(y) & np.isfinite(base)
            r = {"bank": bank, "target": f"m{h}", "period": f"{min(years)}-2026", "n": int(k.sum()),
                 "always_hold": float((y[k] == 0).mean()), "persistence": float((G["b_persistence"].values[k] == y[k]).mean()),
                 "ologit (declared: all predictors, penalty 0.02)": float((base[k] == y[k]).mean())}
            for lab, cols in (("own-policy block only", own), ("economy and markets only (no own-policy block)", mac),
                              ("all + trailing-direction signs", full + tr), ("trailing-direction signs only", tr)):
                p = wf_model(G, cols, "ologit", years)["pred"]
                r[lab] = float((p[k] == y[k]).mean())
            d0 = ologit_fit.__defaults__
            for al in (0.2, 1.0):
                ologit_fit.__defaults__ = (al,)
                p = wf_model(G, full, "ologit", years)["pred"]
                r[f"all predictors, penalty {al}"] = float((p[k] == y[k]).mean())
            ologit_fit.__defaults__ = d0
            kk = np.isfinite(y)
            X = G[full].values.astype(float)[kk]
            mu, sd = _standardise(X)
            Z = _z(X, mu, sd)
            r["IN-SAMPLE fit on the whole history (ceiling)"] = float((np.argmax(ologit_proba(ologit_fit(Z, y[kk]), Z), 1) - 1 == y[kk]).mean())
            rows.append(r)
    return pd.DataFrame(rows)


# ============================================================================= (2) event study
def load_prices() -> pd.DataFrame:
    from eurusd.arms import swing as SW
    P = SW.load_prices()
    return P[["close", "cdate", "src"]].copy()


def _fwd(lc: np.ndarray, i: int, h: int) -> float:
    return float((lc[i + h] - lc[i]) * 100) if 0 <= i and i + h < len(lc) else np.nan


def _spells(lab: np.ndarray) -> list[tuple[int, int, object]]:
    out, s = [], 0
    for i in range(1, len(lab) + 1):
        if i == len(lab) or lab[i] != lab[s]:
            out.append((s, i - 1, lab[s])); s = i
    return out


def event_study(fed: Policy, ecb: Policy, end: pd.Timestamp) -> tuple[pd.DataFrame, pd.DataFrame]:
    P = load_prices()
    P = P[P["cdate"] <= end]
    cd = pd.DatetimeIndex(P["cdate"])
    lc = np.log(P["close"].values)
    n = len(P)
    known = cd - pd.Timedelta(days=1)                       # information date of each session (feature-store lag)
    ev = []
    # ---- turning points and confirmed pauses
    for bank, pol in (("fed", fed), ("ecb", ecb)):
        tps = pd.concat([pol.turning_points(), pol.pauses(end)], ignore_index=True).sort_values("date")
        for _, t in tps.iterrows():
            a = t["date"]
            i0 = cd.searchsorted(a + pd.Timedelta(days=1), side="left")
            ip = cd.searchsorted(a, side="left") - 1
            if ip < 63 or i0 >= n:
                continue
            other = (ecb if bank == "fed" else fed).state(pd.DatetimeIndex([a]))["phase"].iloc[0]
            pr = {"first_cut_after_hikes": 1, "first_hike_after_cuts": -1}.get(t["type"], 0) * (1 if bank == "fed" else -1)
            ev.append({"kind": "turning_point" if t["type"].startswith("first") else "pause", "bank": bank, "type": t["type"], "state": "",
                       "start": a.date(), "end": "", "sessions": np.nan, "source": t["src"], "price_src": P["src"].iloc[min(i0, n - 1)],
                       "other_bank_phase": other, "prior_sign": pr, "move_pp": t["d"], "pre63_pct": _fwd(lc, ip - 63, 63), "react_pct": float((lc[i0] - lc[ip]) * 100),
                       "f21_pct": _fwd(lc, i0, 21), "f63_pct": _fwd(lc, i0, 63), "f126_pct": _fwd(lc, i0, 126), "f252_pct": _fwd(lc, i0, 252), "spell_pct": np.nan})
    # ---- phases (causal), per bank and jointly
    sf, se = fed.state(known), ecb.state(known)
    lvl_diff = fed.level(known) - ecb.level(known)
    rel = sf["dir3"].values - se["dir3"].values
    name3 = {1.0: "hiking", 0.0: "hold", -1.0: "cutting"}
    j9 = np.array([f"fed_{name3[a]}|ecb_{name3[b]}" for a, b in zip(sf["dir3"].values, se["dir3"].values)], dtype=object)
    both_known = (sf["phase"].values != "unknown") & (se["phase"].values != "unknown")
    j9 = np.where(both_known, j9, "unknown")
    div = np.where(~both_known, "unknown", np.where(rel == 0, "parallel", np.where(rel * np.sign(lvl_diff) > 0, "widening", "narrowing")))
    div = np.array([f"{d}|{'fed_tighter' if r > 0 else 'ecb_tighter' if r < 0 else 'same'}" if d != "unknown" else d for d, r in zip(div, rel)], dtype=object)
    src_e = np.where((sf["src"].values == "target") & (se["src"].values == "target"), "target", "proxy")
    sets = (("phase", "fed", sf["phase"].values, sf["src"].values), ("phase", "ecb", se["phase"].values, se["src"].values),
            ("joint", "fed x ecb", j9, src_e), ("divergence", "fed x ecb", div, src_e))
    r1 = np.r_[np.diff(lc), np.nan] * 100
    drift = []
    for kind, bank, lab, src in sets:
        for s, e, v in _spells(lab):
            if v == "unknown":
                continue
            ev.append({"kind": f"{kind}_episode", "bank": bank, "type": v, "state": v, "start": cd[s].date(), "end": cd[e].date(), "sessions": e - s + 1,
                       "source": src[s], "price_src": P["src"].iloc[s], "other_bank_phase": "", "prior_sign": 0, "move_pp": np.nan,
                       "pre63_pct": _fwd(lc, s - 63, 63) if s >= 63 else np.nan, "react_pct": np.nan,
                       "f21_pct": _fwd(lc, s, 21), "f63_pct": _fwd(lc, s, 63), "f126_pct": _fwd(lc, s, 126), "f252_pct": _fwd(lc, s, 252),
                       "spell_pct": float((lc[min(e + 1, n - 1)] - lc[s]) * 100)})
        for era, m in (("1975-2026", np.ones(n, bool)), ("1999-2026", cd >= "1999-01-01"), ("1975-1998", cd < "1999-01-01")):
            for v in sorted(set(lab)):
                k = (lab == v) & m & np.isfinite(r1)
                if v == "unknown" or k.sum() < 5:
                    continue
                x = r1[k]
                drift.append({"kind": kind, "bank": bank, "state": v, "era": era, "sessions": int(k.sum()), "years": k.sum() / 252,
                              "ann_drift_pct": float(x.mean() * 252), "t_daily_naive": float(x.mean() / x.std() * math.sqrt(len(x))) if x.std() > 0 else 0.0,
                              "share_up_days": float((x > 0).mean())})
    return pd.DataFrame(ev), pd.DataFrame(drift)


def event_cells(E: pd.DataFrame) -> pd.DataFrame:
    """One row per (kind, bank, type, era): n and, for every window, mean / median / count positive / count negative."""
    E = E.copy()
    E["year"] = pd.to_datetime(E["start"]).dt.year
    rows = []
    for era, a, b in (("1975-2026", 1975, 2026), ("1999-2026", 1999, 2026), ("1975-1998", 1975, 1998)):
        x = E[(E["year"] >= a) & (E["year"] <= b)]
        for (kind, bank, typ), g in x.groupby(["kind", "bank", "type"]):
            r = {"kind": kind, "bank": bank, "type": typ, "era": era, "n": len(g), "median_sessions": float(g["sessions"].median()) if g["sessions"].notna().any() else np.nan}
            for w in ("pre63", "react", "f21", "f63", "f126", "f252", "spell"):
                v = g[f"{w}_pct"].dropna()
                r[f"{w}_n"] = len(v)
                if len(v):
                    r[f"{w}_mean"], r[f"{w}_median"] = float(v.mean()), float(v.median())
                    r[f"{w}_pos"], r[f"{w}_neg"] = int((v > 0).sum()), int((v < 0).sum())
                    ps = g.loc[v.index, "prior_sign"]
                    if (ps != 0).all():
                        r[f"{w}_prior_hits"] = int((np.sign(v) == ps).sum())
            rows.append(r)
    return pd.DataFrame(rows)


# ============================================================================= daily policy state
def policy_state(end: pd.Timestamp, rf: dict | None = None, cut: pd.Timestamp | None = None, verbose: bool = False) -> pd.DataFrame:
    """Calendar-daily table of what is known at the END of each date. With `cut`, every raw series is truncated to what
    was public on `cut` (truncation test: rows up to `cut` must not change)."""
    if cut is not None or rf is None:
        rf = _daily_models(end if cut is None else cut, cut)
    fed, ecb, daily = rf["fed"], rf["ecb"], rf["daily"]
    idx = daily["fed"].index
    sf, se = fed.state(idx), ecb.state(idx)
    out = pd.DataFrame(index=idx)
    p = pd.read_csv(MACRO / "ecb_policy_rates.csv", parse_dates=["date"]).set_index("date")
    if cut is not None:
        p = p[p.index <= cut]
    out["fed_target"] = fed.level(idx)
    out["ecb_deposit_rate"] = _asof(p["deposit_facility_rate"].astype(float), idx, None)
    out["ecb_main_refi_rate"] = _asof(p["main_refinancing_rate"].astype(float), idx, None)
    out["ecb_key_index"] = ecb.level(idx)
    for b, st in (("fed", sf), ("ecb", se)):
        out[f"{b}_phase"] = st["phase"].values
        out[f"{b}_dir3"] = st["dir3"].values
        out[f"{b}_months_since_move"] = np.round(st["days"].values / 30.44, 2)
        out[f"{b}_last_move_pp"] = st["last_d"].values
    out["joint_state"] = [f"fed_{a}|ecb_{b}" for a, b in zip(out["fed_phase"], out["ecb_phase"])]
    for b in ("fed", "ecb"):
        d = daily[b]
        out[f"{b}_p_cut_6m"], out[f"{b}_p_hold_6m"], out[f"{b}_p_hike_6m"] = d["p_cut"].values, d["p_hold"].values, d["p_hike"].values
        out[f"{b}_model_chg6m_bp"] = d["model_bp"].values
        out[f"{b}_slope_2y_minus_policy"] = d["slope"].values
        out[f"{b}_priced_chg6m_bp"] = d["priced_bp"].values
        out[f"{b}_gap_bp"] = out[f"{b}_model_chg6m_bp"] - out[f"{b}_priced_chg6m_bp"]
    out["model_rel_bp"] = out["ecb_model_chg6m_bp"] - out["fed_model_chg6m_bp"]
    out["priced_rel_bp"] = out["ecb_priced_chg6m_bp"] - out["fed_priced_chg6m_bp"]
    out["gap_rel_bp"] = out["ecb_gap_bp"] - out["fed_gap_bp"]
    out.index.name = "date"
    return out


def _daily_models(end: pd.Timestamp, cut: pd.Timestamp | None) -> dict:
    """Only what policy_state needs (the m6 ordered logit and the market model on the daily grid), honouring `cut`."""
    fed, ecb = fed_policy(cut), ecb_policy(cut)
    dgrid = pd.date_range("1989-12-25", end, freq="D")
    daily = {}
    for bank, pol, feat, full, start, years in (("fed", fed, lambda d: us_features(d, fed, cut), US_FULL, FED_TARGET_START, range(1990, 2027)),
                                                ("ecb", ecb, lambda d: ea_features(d, ecb, fed, cut), EA_FULL, pd.Timestamp("1999-01-01"), range(2004, 2027))):
        me = pd.date_range(start, end, freq="ME")
        G = _grid_month(pol, feat(me), 6, start, end)
        Xd = feat(dgrid)
        ol = wf_model(G, full, "ologit", years, Xd)
        mk = wf_model(G, ["slope"], "ologit", years, Xd, need=["slope"])
        daily[bank] = pd.DataFrame({"p_cut": ol["dP"][:, 0], "p_hold": ol["dP"][:, 1], "p_hike": ol["dP"][:, 2], "model_bp": ol["dE"],
                                    "priced_bp": mk["dE"], "slope": Xd["slope"].values}, index=dgrid)
    return {"fed": fed, "ecb": ecb, "daily": daily}


# ============================================================================= (3) signals on the feature-store grid
def build_signals(D: pd.DataFrame, PS: pd.DataFrame, fed: Policy, ecb: Policy) -> pd.DataFrame:
    """Signals in -1/0/+1 per session. Every input is the policy_state row of (closing date - 1 calendar day)."""
    cd = pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None)
    known = cd - pd.Timedelta(days=1)
    row = PS.index.searchsorted(known, side="right") - 1
    g = lambda c: PS[c].values[row].astype(float)                                  # noqa: E731
    sg = lambda x: np.where(np.isfinite(x), np.sign(x), np.nan)                    # noqa: E731
    Sg = pd.DataFrame(index=D.index)
    gap = g("gap_rel_bp")
    Sg["gap_rel"] = sg(gap)
    yr = D.index.year.values
    strong = np.full(len(D), np.nan)
    for Y in sorted(set(yr)):
        hist = np.abs(gap[(yr < Y) & np.isfinite(gap)])
        te = yr == Y
        if len(hist) >= 250:
            strong[te] = np.where(np.isfinite(gap[te]), np.where(np.abs(gap[te]) >= np.median(hist), np.sign(gap[te]), 0.0), np.nan)
    Sg["gap_rel_strong"] = strong
    Sg["gap_fed"] = -sg(g("fed_gap_bp"))
    Sg["gap_ecb"] = sg(g("ecb_gap_bp"))
    Sg["model_rel"] = sg(g("model_rel_bp"))
    Sg["mkt_rel"] = sg(g("priced_rel_bp"))
    fd, ed = g("fed_dir3"), g("ecb_dir3")
    Sg["phase_rel"] = np.sign(ed - fd) + 0.0
    Sg["fed_phase"] = 0.0 - fd + 0.0
    Sg["ecb_phase"] = ed
    t63 = np.zeros(len(D))
    evs = []
    for bank, pol, other in (("fed", fed, ecb), ("ecb", ecb, fed)):
        for _, t in pol.turning_points().iterrows():
            if t["src"] != "target":
                continue
            cut_ = t["type"] == "first_cut_after_hikes"
            od = other.state(pd.DatetimeIndex([t["date"]]))["dir3"].iloc[0]
            if (cut_ and od == -1) or ((not cut_) and od == 1):
                continue                                        # the other bank is already moving the same way
            s = (1.0 if cut_ else -1.0) * (1.0 if bank == "fed" else -1.0)
            evs.append((t["date"], s))
    for a, s in sorted(evs):
        if a + pd.Timedelta(days=1) < cd[0]:
            continue                                            # before the price sample
        i0 = cd.searchsorted(a + pd.Timedelta(days=1), side="left")
        t63[i0:i0 + 63] = s
    Sg["turn63"] = t63
    return Sg


# ----------------------------------------------------------------------------- accuracy cells (generalises S.cell_stats)
def cells(ctx, T, dec: pd.DataFrame, speak: np.ndarray, mode: str, periods) -> list[dict]:
    valid = np.isfinite(T.long)
    grid = np.arange(0, len(valid), S.STEP) if mode == "weekly" else np.arange(len(valid))
    grid = grid[valid[grid]]
    gy = ctx.year[grid]
    rows = []
    for lab, a, b in periods:
        g = grid[(gy >= a) & (gy <= b)]
        x = dec[(dec["year"] >= a) & (dec["year"] <= b)]
        n = len(x)
        r = {"period": lab, "n": n}
        if len(g) == 0:
            rows.append(r); continue
        yrs = max((ctx.D.index[g[-1]] - ctx.D.index[g[0]]).days / 365.25, 1e-9)
        base = float((T.long[g] > 0).mean())
        r.update({"dec_per_year": n / yrs, "coverage": float(speak[g].mean()), "base_up": base})
        if n:
            acc = float(x["hit"].mean())
            if mode == "weekly":
                s = np.zeros(len(g)); hh = np.zeros(len(g))
                loc = np.searchsorted(g, x["i"].values)
                s[loc] = 1.0; hh[loc] = x["hit"].values
                neff = S.nw_neff(s, hh, int(math.ceil(1.5 * T.h / S.STEP)))
                neff = min(neff, max(1.0, n * S.STEP / T.h))             # the conservative effective n of arm N
            else:
                neff = float(n)
            lo, hi = S.wilson(acc, neff)
            sl = float((x["pos"] > 0).mean())
            r.update({"accuracy": acc, "lo": lo, "hi": hi, "n_eff": neff, "share_long": sl, "chance_acc": sl * base + (1 - sl) * (1 - base),
                      "net_bp": float(x["net_bp"].mean())})
        rows.append(r)
    return rows


def _decide(ctx, T, speak: np.ndarray, dirs: np.ndarray, mode: str) -> pd.DataFrame:
    valid = np.isfinite(T.long)
    idx = S.weekly_idx(speak, valid) if mode == "weekly" else S.seq_idx(speak, valid, T.hold)
    return S.decision_frame(ctx, T, idx, dirs, None)


def _rules(s: np.ndarray, agree: np.ndarray, sg: np.ndarray, hs_ok: np.ndarray) -> dict:
    s0 = np.nan_to_num(s)
    live = np.isfinite(s) & (s != 0)
    return {"standalone": (live, s0), "agree3": (agree, sg), "vote_agree": (agree & live & (s0 == sg), sg), "vote_veto": (agree & (s0 != -sg), sg),
            "extend": (hs_ok & ~agree & live, s0), "agree3_signal_opposes": (agree & live & (s0 == -sg), sg),
            "agree3_signal_silent_or_opposes": (agree & ~(live & (s0 == sg)), sg)}


def evaluate(K: dict, name: str, s: np.ndarray, T: dict | None = None, tests: tuple | None = None, extra: bool = True) -> pd.DataFrame:
    ctx, agree, sg, hs_ok = K["ctx"], K["agree"], K["sg"], K["hs_ok"]
    T = T or K["T"]
    yr = ctx.year
    rows = []
    for h in HORIZONS:
        t = T[f"sign{h}"]
        scopes = [("main", yr >= 2010, PERIODS, PERIODS)]
        if extra:
            scopes.append(("extra", (yr >= 2006) & (yr <= 2009), (EXTRA_VOTE,), (EXTRA_SOLO,)))
        for scope, inyr, pv, ps in scopes:
            R = _rules(s, agree, sg, hs_ok)
            for test, (sp, dirs) in R.items():
                if tests and test not in tests:
                    continue
                per = ps if test == "standalone" else pv
                m = inyr if not (scope == "extra" and test == "standalone") else (yr >= 2004) & (yr <= 2009)
                sp = sp & m
                for mode in ("weekly", "nonoverlap"):
                    dec = _decide(ctx, t, sp, dirs, mode)
                    for r in cells(ctx, t, dec, sp, mode, per):
                        rows.append({"signal": name, "test": test, "h": h, "mode": mode, **r})
    return pd.DataFrame(rows)


def paired_boot(K: dict, s: np.ndarray, form: str, h: int, a: int, b: int, reps: int = 2000, seed: int = 5) -> dict:
    """Weekly grid: accuracy of the vote rule minus accuracy of the agreement rule, circular block bootstrap."""
    ctx, t = K["ctx"], K["T"][f"sign{h}"]
    valid = np.isfinite(t.long)
    g = np.arange(0, len(valid), S.STEP); g = g[valid[g] & (ctx.year[g] >= a) & (ctx.year[g] <= b)]
    R = _rules(s, K["agree"], K["sg"], K["hs_ok"])
    A, V = R["agree3"][0][g].astype(float), R[form][0][g].astype(float)
    hit = (np.where(K["sg"][g] > 0, t.long[g], t.short[g]) > 0).astype(float)
    if A.sum() < 10 or V.sum() < 5:
        return {"diff": np.nan, "lo": np.nan, "hi": np.nan, "diff_kept_minus_dropped": np.nan, "lo_kd": np.nan, "hi_kd": np.nan}
    Dr = A - V                                                   # dropped decisions
    f = lambda A_, V_, D_, H_: ((V_ * H_).sum(-1) / np.maximum(V_.sum(-1), 1) - (A_ * H_).sum(-1) / np.maximum(A_.sum(-1), 1),   # noqa: E731
                                (V_ * H_).sum(-1) / np.maximum(V_.sum(-1), 1) - (D_ * H_).sum(-1) / np.maximum(D_.sum(-1), 1))
    d0, k0 = f(A, V, Dr, hit)
    rng = np.random.default_rng(seed)
    Tn, block = len(g), max(2, int(math.ceil(2 * h / S.STEP)))
    nb = int(math.ceil(Tn / block))
    st = rng.integers(0, Tn, size=(reps, nb))
    ix = ((st[:, :, None] + np.arange(block)[None, None, :]) % Tn).reshape(reps, -1)[:, :Tn]
    d, k = f(A[ix], V[ix], Dr[ix], hit[ix])
    okv = V[ix].sum(1) > 0
    okd = okv & (Dr[ix].sum(1) > 0)
    return {"diff": float(d0), "lo": float(np.quantile(d[okv], 0.025)), "hi": float(np.quantile(d[okv], 0.975)),
            "diff_kept_minus_dropped": float(k0) if Dr.sum() else np.nan,
            "lo_kd": float(np.quantile(k[okd], 0.025)) if okd.sum() > 50 else np.nan, "hi_kd": float(np.quantile(k[okd], 0.975)) if okd.sum() > 50 else np.nan}


def _get(V: pd.DataFrame, signal: str, test: str, h: int, mode: str, period: str, col: str = "accuracy") -> float:
    x = V[(V.signal == signal) & (V.test == test) & (V.h == h) & (V["mode"] == mode) & (V.period == period)]
    return float(x[col].iloc[0]) if len(x) and col in x and pd.notna(x[col].iloc[0]) else np.nan


def bar_table(V: pd.DataFrame, PL: pd.DataFrame) -> pd.DataFrame:
    """The Round 5 success test for every candidate in its declared form (see the module docstring)."""
    rows = []
    for name, typ in CANDIDATES:
        form = FORM[typ]
        r = {"candidate": name, "type": typ, "form": form}
        ok_gain, ok_plc = True, True
        for per in ("2010-26", "2016-26", "2023-26", "2010-15", "2006-09"):
            for h in (21, 42, 63):
                a0 = _get(V, name, "agree3", h, "nonoverlap", per)
                a1 = _get(V, name, form, h, "nonoverlap", per)
                r[f"agree3_{h}_{per}"], r[f"vote_{h}_{per}"], r[f"gain_{h}_{per}"] = a0, a1, a1 - a0
                r[f"vote_n_{h}_{per}"] = _get(V, name, form, h, "nonoverlap", per, "n")
                r[f"vote_dpy_{h}_{per}"] = _get(V, name, form, h, "nonoverlap", per, "dec_per_year")
                if per in ("2010-26", "2016-26") and h in (21, 42):
                    gn = a1 - a0
                    ok_gain &= bool(gn >= 0.03 - 1e-12)
                    for k in PLACEBO_SHIFTS:
                        pg = _get(PL, f"{name}+{k}", form, h, "nonoverlap", per) - a0
                        r[f"placebo{k}_gain_{h}_{per}"] = pg
                        ok_plc &= bool(np.isfinite(pg) and gn > 0 and pg <= 0.5 * gn + 1e-12)
        dpy = min(r["vote_dpy_21_2010-26"], r["vote_dpy_21_2016-26"])
        ok_n = bool(dpy >= 6)
        ok_23 = bool(r["gain_21_2023-26"] >= -1e-12 and r["gain_42_2023-26"] >= -1e-12)
        wk_a, wk_v = _get(V, name, "agree3", 21, "weekly", "2010-15", "n"), _get(V, name, form, 21, "weekly", "2010-15", "n")
        r.update({"pass_gain_3pts": ok_gain, "pass_6_per_year": ok_n, "pass_2023_not_worse": ok_23, "pass_placebo": ok_plc,
                  "PASS_ROUND5_BAR": bool(ok_gain and ok_n and ok_23 and ok_plc), "share_removed_2010-15": 1 - wk_v / wk_a if wk_a else np.nan})
        r["eligible_for_final"] = bool(r["vote_dpy_21_2010-15"] >= 6 and r["share_removed_2010-15"] >= 0.10)
        rows.append(r)
    B = pd.DataFrame(rows)
    el = B[B["eligible_for_final"]].sort_values(["vote_21_2010-15", "vote_42_2010-15"], ascending=False)
    B["final"] = B["candidate"] == (el["candidate"].iloc[0] if len(el) else None)
    return B


# ============================================================================= run
def _context(cost_pips: float) -> dict:
    D = S.load_data()
    ctx = S.make_ctx(D, cost_pips)
    T = S.build_targets(D)
    hs = S.house_score_wf(ctx, years=list(range(2006, 2027)))          # identical to arm N from 2010; 2006-09 are extra years
    sg = np.sign(hs)
    hs_ok = np.isfinite(hs) & (sg != 0)
    agree = hs_ok & (np.sign(ctx.G["cot_z52"].values) == sg) & (np.sign(ctx.G["d_spread2y_20"].values) == sg)
    return {"D": D, "ctx": ctx, "T": T, "hs": hs, "sg": sg, "hs_ok": hs_ok, "agree": agree}


def reconcile(K: dict) -> pd.DataFrame:
    """The agreement rule rebuilt here against arm N's published cells (reports/arm_selective.md, section 3)."""
    pub = {(21, "weekly"): (387, 0.594), (42, "weekly"): (383, 0.648), (63, "weekly"): (383, 0.666),
           (21, "nonoverlap"): (156, 0.59), (42, "nonoverlap"): (89, 0.61), (63, "nonoverlap"): (61, 0.72)}
    ctx = K["ctx"]
    rows = []
    for (h, mode), (n_pub, a_pub) in pub.items():
        t = K["T"][f"sign{h}"]
        sp = K["agree"] & (ctx.year >= 2010)
        dec = _decide(ctx, t, sp, K["sg"], mode)
        mine = cells(ctx, t, dec, sp, mode, PERIODS)[0]
        ref = S.cell_stats(ctx, t, dec, sp, mode)[0]
        rows.append({"h": h, "mode": mode, "n_here": mine["n"], "acc_here": mine["accuracy"], "n_selective_code": ref["n"], "acc_selective_code": ref["accuracy"],
                     "n_published": n_pub, "acc_published": a_pub})
    return pd.DataFrame(rows)


def daily_stream(K: dict, s: np.ndarray, cost_pips: float) -> pd.DataFrame:
    D = K["D"]
    pos = pd.Series(np.nan_to_num(s), index=D.index)
    pnl = pnl_from_positions(pos, D["fwd_1d"], D["close"], cost_pips=cost_pips)
    pnl = pnl[pnl.index.year >= 2010]
    pnl["fwd_bp"] = D["fwd_1d"].reindex(pnl.index)
    return pnl


def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Runs (1), (2), (3), applies the declared selection rule and writes the deliverables.
    Returns (daily positions of the final signal as a Series, protocol report DataFrame)."""
    K = _context(cost_pips)
    D = K["D"]
    end = pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None)[-1]
    if verbose:
        print(f"policy_cycle: data end {end.date()}", flush=True)
    rf = reaction_functions(end, verbose=verbose)
    bbk = bundesbank_robustness()
    fed, ecb = rf["fed"], rf["ecb"]
    PS = policy_state(end, rf)
    E, drift = event_study(fed, ecb, end)
    EC = event_cells(E)
    Sg = build_signals(D, PS, fed, ecb)
    rec = reconcile(K)
    V = pd.concat([evaluate(K, nm, Sg[nm].values) for nm, _ in CANDIDATES], ignore_index=True)
    PL = pd.concat([evaluate(K, f"{nm}+{k}", Sg[nm].shift(k).values, tests=("vote_agree", "vote_veto", "standalone", "extend"), extra=False)
                    for nm, _ in CANDIDATES for k in PLACEBO_SHIFTS], ignore_index=True)
    B = bar_table(V, PL)
    final = B.loc[B["final"], "candidate"].iloc[0] if B["final"].any() else None
    status = "selected by the declared rule" if final else "NO candidate eligible - stream = standalone gap_rel, flagged as failing"
    stream_name = final or "gap_rel"
    boots = []
    for nm, typ in CANDIDATES:
        for form in ("vote_agree", "vote_veto"):
            for h in HORIZONS:
                for lab, a, b in (("2010-26", 2010, 2026), ("2016-26", 2016, 2026)):
                    boots.append({"signal": nm, "form": form, "declared_form": form == FORM[typ], "h": h, "period": lab,
                                  **paired_boot(K, Sg[nm].values, form, h, a, b)})
    BO = pd.DataFrame(boots)
    reps, streams = [], {}
    for nm, typ in CANDIDATES:
        streams[nm] = daily_stream(K, Sg[nm].values, cost_pips)
        tb = report(streams[nm], periods_per_year=252, name=ARM, n_arms=N_CAND)
        tb.insert(1, "variant", nm); tb["final"] = nm == stream_name; tb["kind"] = "candidate (standalone daily sign)"; tb["cost_pips"] = cost_pips
        reps.append(tb)
    lo = daily_stream(K, Sg[stream_name].values, 0.6)
    tb = report(lo, periods_per_year=252, name=ARM, n_arms=N_CAND)
    tb.insert(1, "variant", f"{stream_name}_cost0.6"); tb["final"] = False; tb["kind"] = "cost_sensitivity"; tb["cost_pips"] = 0.6
    reps.append(tb)
    # weekly-tranche books of the agreement rule and of the final's vote rule (information only)
    ctx = K["ctx"]
    form = FORM[dict(CANDIDATES)[stream_name]]
    for lab, (sp, dirs) in (("book21_agree3", _rules(Sg[stream_name].values, K["agree"], K["sg"], K["hs_ok"])["agree3"]),
                            (f"book21_{form}_{stream_name}", _rules(Sg[stream_name].values, K["agree"], K["sg"], K["hs_ok"])[form])):
        dec = _decide(ctx, K["T"]["sign21"], sp & (ctx.year >= 2010), dirs, "weekly")
        bk = S.book_time_exit(ctx, dec, 21, cost_pips)
        tb = report(bk[bk.index.year >= 2010], periods_per_year=252, name=ARM, n_arms=N_CAND)
        tb.insert(1, "variant", lab); tb["final"] = False; tb["kind"] = "weekly-tranche book (information)"; tb["cost_pips"] = cost_pips
        reps.append(tb)
    rep = pd.concat(reps, ignore_index=True)
    pos = streams[stream_name][["pos", "fwd_bp", "net_bp"]]
    # hit rates of the delivered daily stream (Round 4 addendum)
    hr = []
    for lab, a, b in (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026)):
        x = streams[stream_name]; x = x[(x.index.year >= a) & (x.index.year <= b) & (x["pos"] != 0)]
        hr.append({"period": lab, "active_sessions": len(x), "share_net_positive": float((x["net_bp"] > 0).mean()) if len(x) else np.nan,
                   "share_correct_sign": float((x["gross_bp"] > 0).mean()) if len(x) else np.nan})
    out = {"K": K, "rf": rf, "bbk": bbk, "PS": PS, "events": E, "drift": drift, "event_cells": EC, "signals": Sg, "reconcile": rec, "votes": V,
           "placebo": PL, "bar": B, "boot": BO, "report": rep, "final": final, "final_status": status, "stream_name": stream_name, "streams": streams,
           "hit": pd.DataFrame(hr), "end": end, "cost_pips": cost_pips}
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        pos.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        racc = pd.concat([rf["acc"], bbk], ignore_index=True)
        racc.to_csv(RES / f"{ARM}_reaction_accuracy.csv", index=False)
        rf["conf"].to_csv(RES / f"{ARM}_reaction_confusion.csv", index=False)
        rf["tp"].to_csv(RES / f"{ARM}_reaction_turning_points.csv", index=False)
        rf["coef"].to_csv(RES / f"{ARM}_reaction_coefficients.csv", index=False)
        rf["dis"].to_csv(RES / f"{ARM}_reaction_disagreement.csv", index=False)
        E.to_csv(RES / f"{ARM}_events.csv", index=False)
        EC.to_csv(RES / f"{ARM}_event_cells.csv", index=False)
        drift.to_csv(RES / f"{ARM}_event_drift.csv", index=False)
        vv = pd.concat([V.assign(kind="signal"), PL.assign(kind="timing_placebo")], ignore_index=True)
        vv.to_csv(RES / f"{ARM}_votes.csv", index=False)
        B.to_csv(RES / f"{ARM}_bar.csv", index=False)
        BO.to_csv(RES / f"{ARM}_paired_bootstrap.csv", index=False)
        pd.DataFrame(Sg).to_parquet(RES / f"{ARM}_signals.parquet")
        ps = PS[(PS.index.dayofweek < 5) & (PS.index >= "1990-01-01")].copy()
        cdl = pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None)
        for nm, _ in CANDIDATES:      # sig_<name> on date d = the signal in force for the session CLOSING on d (it uses the row of d - 1)
            ps[f"sig_{nm}"] = pd.Series(Sg[nm].values, index=cdl).groupby(level=0).last().reindex(ps.index)
        ps.round(4).to_csv(MACRO / "policy_state.csv")
    run.last = out
    return pos["pos"], rep


# ============================================================================= incremental test, leak checks
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


def leak_checks(out: dict, verbose: bool = True) -> pd.DataFrame:
    """(1) labels shuffled: exchange-rate labels for every candidate, policy labels inside the reaction-function
    training windows; (2) information made staler / taken from the future; (3) top coefficients; (4) truncation test of
    the whole daily state table."""
    K, Sg, end = out["K"], out["signals"], out["end"]
    rows = []
    # (1a) FX labels shuffled
    rng = np.random.default_rng(0)
    for rep_ in range(3):
        perm = rng.permutation(len(K["D"]))
        Tp = {k: (v.permuted(perm) if k.startswith("sign") else v) for k, v in K["T"].items()}
        for nm, typ in CANDIDATES:
            V = evaluate(K, nm, Sg[nm].values, T=Tp, tests=("standalone", "agree3", FORM[typ]), extra=False)
            for h in (21, 42):
                rows.append({"check": f"fx_labels_shuffled_{rep_}", "signal": nm, "h": h,
                             "standalone_weekly_2010-26": _get(V, nm, "standalone", h, "weekly", "2010-26"),
                             "vote_nonoverlap_2010-26": _get(V, nm, FORM[typ], h, "nonoverlap", "2010-26"),
                             "agree3_nonoverlap_2010-26": _get(V, nm, "agree3", h, "nonoverlap", "2010-26")})
    # (2a) signals staler / from the future
    for lag in (0, 1, 5, 21, -21, -63):
        for nm, typ in CANDIDATES:
            V = evaluate(K, nm, Sg[nm].shift(lag).values, tests=("standalone", "agree3", FORM[typ]), extra=False)
            for h in (21, 42):
                rows.append({"check": "baseline" if lag == 0 else (f"signal_stale_plus{lag}" if lag > 0 else f"signal_from_future_minus{-lag}"),
                             "signal": nm, "h": h, "standalone_weekly_2010-26": _get(V, nm, "standalone", h, "weekly", "2010-26"),
                             "vote_nonoverlap_2010-26": _get(V, nm, FORM[typ], h, "nonoverlap", "2010-26"),
                             "agree3_nonoverlap_2010-26": _get(V, nm, "agree3", h, "nonoverlap", "2010-26")})
    L = pd.DataFrame(rows)
    # (1b, 2b) reaction functions: shuffled policy labels, stale and look-ahead publication lags, no NFCI
    rr = []
    variants = (("baseline", {}), ("policy_labels_shuffled_in_training", {"perm_seed": 1}), ("features_365_days_staler", {"extra_lag": 365}),
                ("lookahead_control_features_from_182_days_ahead", {"extra_lag": -182}), ("without_nfci", {"drop": ("nfci", "nfci_d13")}))
    for lab, kw in variants:
        r = reaction_functions(end, verbose=False, light=True, **kw)["acc"]
        r = r[(r["subset"].isin(["all", "any change vs previous decision", "label differs from the trailing direction"]))]
        r = r[r["period"].isin(["1996-2026", "1990-2026", "2004-2026"])]
        r = r[~((r["bank"] == "fed") & (r["period"] == "2004-2026"))]
        for _, q in r.iterrows():
            rr.append({"check": lab, "bank": q["bank"], "target": q["target"], "period": q["period"], "subset": q["subset"], "n": q["n"],
                       "acc_ologit": q.get("acc_ologit"), "acc_taylor": q.get("acc_taylor"), "acc_always_hold": q.get("acc_always_hold"),
                       "acc_persistence": q.get("acc_persistence")})
        if verbose:
            print(f"  leak check reaction functions: {lab}", flush=True)
    RL = pd.DataFrame(rr)
    # (4) truncation test: the state table rebuilt from data cut at three dates
    tr = []
    PS = out["PS"]
    num = list(PS.select_dtypes(include="number").columns)
    for cut in ("2012-06-29", "2019-03-29", "2024-09-30"):
        cut = pd.Timestamp(cut)
        P2 = policy_state(end, None, cut=cut)
        a, b = PS.loc[:cut, num], P2.loc[:cut, num]
        diff = (a - b).abs()
        both = a.notna() & b.notna()
        tr.append({"cut": cut.date(), "rows_compared": len(a), "max_abs_diff_numeric": float(diff.where(both).max().max()),
                   "cells_nan_mismatch": int((a.isna() != b.isna()).sum().sum()),
                   "phase_mismatch": int((PS.loc[:cut, "joint_state"] != P2.loc[:cut, "joint_state"]).sum())})
        if verbose:
            print(f"  truncation test {cut.date()}: {tr[-1]}", flush=True)
    TR = pd.DataFrame(tr)
    L.to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
    RL.to_csv(RES / f"{ARM}_leakchecks_reaction.csv", index=False)
    TR.to_csv(RES / f"{ARM}_leakchecks_truncation.csv", index=False)
    out["leak"], out["leak_rf"], out["leak_trunc"] = L, RL, TR
    return L


# ============================================================================= report
VERDICT = """**The owner's idea was tested properly and it does not give a tradeable edge. No candidate meets the Round 5 bar; the arm adds no vote.**
The three questions, in order:

1. **Can we predict what each central bank does from the economy? Not better than "it will keep doing what it has been doing".**
   Out of sample (walk-forward), three classes cut / hold / hike:
   * Next meeting. Fed 1996-2026 (252 meetings; 12 % cuts, 70 % holds, 18 % hikes): ordered logit on the economy + own policy 71 %, "always
     hold" 70 %, "same as the last decision" 77 %, transparent Taylor-type rule 46 %. ECB 2004-2026 (227 meetings; 11 / 79 / 10): 80 % vs 79 %
     vs 76 % vs 49 %. The model equals the base rate.
   * Direction over the next 3 / 6 months. Fed 1990-2026: model 48 % / 45 %, persistence (the trailing direction) 71 % / 63 %, always hold
     54 % / 39 %, Taylor rule 32 % / 32 %. ECB 2004-2026: model 66 % / 45 %, persistence 72 % / 60 %, always hold 61 % / 49 %, Taylor 39 % / 32 %.
     The economy-only part of the model (no own-policy block) is at 34-42 %, below "always hold"; even fitted IN-SAMPLE on the whole history the
     model reaches only 63-74 %. Bundesbank 1975-98 (3-month rate as proxy): model 35 % / 41 %, persistence 52 % / 46 %.
   * **At turning points** (where persistence is wrong by construction). Meetings: first cut after hikes - Fed 1 of 5, ECB 0 of 3; first hike
     after cuts - Fed 1 of 6, ECB 0 of 4; all decisions that differ from the previous one - Fed 47 % (n=59) against 51 % for "always hold", ECB
     48 % (n=54) against 50 %. Month-ends whose 6-month label differs from the trailing direction: Fed 32 % (n=160) against 44 % for "always
     hold", ECB 28 % (n=108) against 43 %. The one place the Fed model looks good - at the last month-end before each first cut / first hike it
     names the 6-month direction in 8 of 12 cases (Taylor rule 7 of 12) - is matched exactly by the 2-year yield alone (8 of 12): by then the
     market knows. And the price of those hits is false alarms: when the ordered logit departs from persistence (227 of 436 months) it is right
     23 % of the time and persistence 58 %. ECB at the same month-ends: 1 of 6 (2-year yield 2 of 5).
   * Why: reaction functions are unstable across regimes (the 1980s disinflation, the zero bound 2009-15 and 2020-21, 2022's inflation - on
     2022-02-28 both the logit and the Taylor rule said "cut"). Forecasting the 6-month change in bp, 2010-26: Fed RMSE 79 bp for the model, 69 bp
     for "no change", 66 bp for the 2-year slope; ECB 58 / 56 / 53. The market slope is the best of a poor lot; the economy adds nothing to it.
   * Data-revision risk (latest-vintage payrolls, production, NFCI) can only flatter the model; it does not change a negative.
2. **What did EUR/USD do around the cycle? Nothing systematic; every cell is small and split.** 1975-2026, forward 3-month return from the day after
   the announcement, mean (up / down episodes): Fed first cut after hikes n=16: +0.2 % (7 / 9); Fed first hike after cuts n=17: -0.1 % (8 / 8);
   ECB / Bundesbank first cut n=10: -0.7 % (6 / 4); first hike n=11: -0.5 % (6 / 5). With true target data only (1999-2026) there are 4-5 episodes
   per cell. The textbook prior (the bank that turns to easing gets the weaker currency) is right in 7 of 16, 8 of 16, 4 of 10 and 6 of 11 cases at
   3 months. The only lopsided cell is BEFORE the event: in the 3 months before a first Fed hike EUR/USD fell in 14 of 17 episodes (mean -3.1 %;
   4 of 5 since 1999) - the dollar moves in anticipation, not afterwards (afterwards 8 up / 8 down). Joint states, 1999-2026, n spells and 3-month
   return from the start of the spell: both hiking n=4, -2.7 % (1 up / 2 down); Fed hiking, ECB on hold n=5, -0.2 % (3 / 2); Fed hiking, ECB cutting
   n=2, +3.5 % (2 / 0); Fed cutting, ECB on hold n=9, +2.4 % (6 / 3); Fed cutting, ECB hiking n=3, -4.7 % (1 / 2); both cutting n=7, +0.8 % (5 / 2);
   both on hold n=16, +0.6 % (9 / 7); Fed on hold, ECB cutting n=12, +1.1 % (8 / 4); Fed on hold, ECB hiking n=6, -1.4 % (3 / 3). With the 1975-98
   proxies: "Fed cutting, ECB on hold" n=19, +3.1 % (15 / 4) is the one cell that leans the way economics says, but the 19 spells come from 11 Fed
   easing cycles (median spell 31 sessions; 9 spells from 4 cycles since 1999), the drift inside the state is +6.9 % a year with t 1.5 (0.3 %, t 0.05 since 1999), and
   the rule built on it (below) is at 49 % in 2010-26. Divergence widening with the Fed tightening: -0.8 % a year (t -0.3) over 1975-2026.
3. **Is there a signal the market has not priced? No.** Ten candidates, priors fixed before any result.
   * The owner's idea in its purest form, `gap_rel` (the economy implies a higher ECB-minus-Fed path than the 2-year yields price): standalone
     50 / 50 / 52 % at 21 / 42 / 63 sessions (non-overlapping, n = 208 / 104 / 69, 2010-26), daily Sharpe +0.02 / -0.19 / -0.29. As an extra vote it
     moves the agreement rule by +2.6 / +0.6 points (2010-26) and +5.2 / +7.7 (2016-26) at 21 / 42 sessions on 4.7 decisions a year, is 10 points WORSE
     at 21 sessions in 2023-26, and the signal made 63 sessions stale "gains" more (+6.1 / +1.6 and +11.7 / +10.5): a regime artefact.
   * Phase rules. `turn63` ("Fed has turned to cutting while the ECB has not => long for 3 months", and its mirror images): 43 % at 21 sessions
     (n=21), 36 % at 42 (n=14); 7 qualifying turns in 2010-26. `phase_rel` (the relatively tightening bank's currency): 50 / 49 / 43 %. `fed_phase`
     49 / 51 / 48 %, `ecb_phase` 51 / 44 / 36 %. As vetoes on the agreement rule they change it by -4.7 to +2.5 points
     (2010-26).
   * The best-looking numbers belong to the MARKET leg, not to the economy: `mkt_rel` (sign of the priced relative path) 54 / 56 / 61 % standalone,
     daily Sharpe +0.30 / +0.33 / +0.11, vote gain +0.8 / +9.7 (2010-26) and +3.4 / +10.8 (2016-26). It fails the bar on three counts: under 3 points
     at 21 sessions in 2010-26, 5.5 / 5.2 decisions a year, and the placebo keeps two thirds of the 42-session gain (+6.6 and +4.6 of +9.7). On
     the weekly grid the same vote is -1.0 points [-8.7, +6.2] at 42 sessions, so the non-overlapping "gain" is which trades the greedy stream
     happened to pick. `gap_fed` (+3.5 / +4.7; +2.0 / +6.7; 5.3 / 5.0 a year) is the same story: at 21 sessions the stale signal gains more
     (+5.2 and +3.9) than the timely one.
   * Coverage extension: when the three old signals do not agree, the new signals are right 35-56 % of the time at 21 sessions (n = 20-170,
     2010-26).
   * Paired weekly difference (block bootstrap): every interval of every candidate at every horizon contains zero.
   * Extra years: in 2006-09 the vote gain at 21 sessions is positive for 9 of 10 candidates (+0.5 to +27 points) but on 7-36 non-overlapping
     decisions each, against an agreement rule that itself has 36; standalone 2004-09 is 44-61 % at 21 sessions for the signals with at least
     25 decisions. Too small to weigh against 2010-26.
   * **Final by the declared rule: `phase_rel`** as a veto (best eligible 2010-15 vote accuracy, 59 %). Full record: gain -4.7 / -2.3 points
     (2010-26), -6.0 / -2.1 (2016-26), -13.6 / -7.5 (2023-26) at 21 / 42 sessions; standalone daily stream net Sharpe **+0.01 / -0.10 / -0.40**
     (2010-26 / 2016-26 / 2023-26), hit rate 49.6 / 48.5 / 46.9 %; three-way combination 0.45 / 0.44 / 0.15 against 0.56 / 0.64 / 0.36 for the
     two live streams (worse), correlation +0.02 / -0.02. **Round 5 bar: not met** (0 of 10 candidates pass the 3-point test, 0 of 10 the
     placebo test). Round 3 bar: not met.

What is worth keeping: `data/macro/policy_state.csv` as CONTEXT for the weekly outlook (phase of each bank, months since the last move, the
2-year slope as the priced path). The model-implied 6-month change is in the file because it was asked for; its out-of-sample error is larger
than "no change", so it should be shown, if at all, as a low-confidence line and never as a call. Leak checks are clean (section 4): shuffled
exchange-rate labels give 50 %, the daily state table rebuilt from data truncated at three dates is identical to the last digit, shuffled
policy labels take the Fed 6-month model from 45 % to 25 %."""


def _vc(V: pd.DataFrame, signal: str, test: str, h: int, mode: str, period: str) -> str:
    x = V[(V.signal == signal) & (V.test == test) & (V.h == h) & (V["mode"] == mode) & (V.period == period)]
    if not len(x) or x["n"].iloc[0] == 0 or "accuracy" not in x or pd.isna(x["accuracy"].iloc[0]):
        return "-"
    q = x.iloc[0]
    return f"{100 * q['accuracy']:.0f} [{100 * q['lo']:.0f}-{100 * q['hi']:.0f}] n={int(q['n'])} ({q['dec_per_year']:.1f}/y)"


def _md(df: pd.DataFrame, floatfmt: str = ".2f", numparse: bool = True) -> str:
    if not len(df):
        return "(no rows)"
    return df.to_markdown(index=False, floatfmt=floatfmt) if numparse else df.to_markdown(index=False, disable_numparse=True)


def _acc_table(A: pd.DataFrame, subsets, banks=("fed", "ecb")) -> pd.DataFrame:
    x = A[A["subset"].isin(subsets) & A["bank"].isin(banks)].copy()
    rows = []
    for _, q in x.iterrows():
        r = {"bank": q["bank"], "target": q["target"], "period": q["period"], "subset": q["subset"], "n": int(q["n"])}
        if q["n"]:
            r["cut / hold / hike %"] = f"{100 * q['share_cut']:.0f} / {100 * q['share_hold']:.0f} / {100 * q['share_hike']:.0f}"
            for m, lab in (("always_hold", "always hold"), ("persistence", "persistence"), ("last_move", "same as last move"), ("taylor", "Taylor-type rule"),
                           ("ologit", "ordered logit"), ("market", "market slope only"), ("ologit+market", "logit + slope")):
                v = q.get(f"acc_{m}", np.nan)
                r[lab] = f"{100 * v:.0f}" if pd.notna(v) else ""
        rows.append(r)
    return pd.DataFrame(rows)


def _ev(g: pd.Series, w: str) -> str:
    n = g.get(f"{w}_n", 0)
    if not n or pd.isna(n):
        return "-"
    return f"{g[f'{w}_mean']:+.1f} ({int(g[f'{w}_pos'])}+/{int(g[f'{w}_neg'])}-)"


def _event_table(EC: pd.DataFrame, kind: str, era: str, bank: str | None = None, prior: bool = False) -> pd.DataFrame:
    x = EC[(EC.kind == kind) & (EC.era == era)]
    if bank:
        x = x[x.bank == bank]
    rows = []
    for _, g in x.iterrows():
        r = {"bank": g["bank"], "state / event": g["type"], "n episodes": int(g["n"])}
        if pd.notna(g.get("median_sessions", np.nan)):
            r["median length (sessions)"] = int(g["median_sessions"])
        if kind in ("turning_point", "pause"):
            r["3m before"] = _ev(g, "pre63")
        for w, lab in (("f21", "+1m"), ("f63", "+3m"), ("f126", "+6m"), ("f252", "+12m")):
            r[lab] = _ev(g, w)
        if kind.endswith("episode"):
            r["over the spell"] = _ev(g, "spell")
        if prior:
            for w, lab in (("f63", "+3m"), ("f126", "+6m")):
                v = g.get(f"{w}_prior_hits", np.nan)
                r[f"prior sign right {lab}"] = f"{int(v)}/{int(g[f'{w}_n'])}" if pd.notna(v) else ""
        rows.append(r)
    return pd.DataFrame(rows)


def write_report(o: dict, path: Path | None = None) -> None:
    A, CONF, TP, COEF = (o["rf_tables"][k] for k in ("acc", "conf", "tp", "coef")) if "rf_tables" in o else (o["rf"][k] for k in ("acc", "conf", "tp", "coef"))
    V, PL, B, BO, REP, E, EC, DR = o["votes"], o["placebo"], o["bar"], o["boot"], o["report"], o["events"], o["event_cells"], o["drift"]
    Sg = o["signals"]
    L = []
    w = L.append
    w("# Arm T - policy_cycle: central-bank reaction functions, the policy cycle and EUR/USD (round 5)\n")
    w("Code `src/eurusd/arms/policy_cycle.py` (`run(cost_pips=1.2)`; `PYTHONPATH=src python -m eurusd.arms.policy_cycle` runs everything incl. leak "
      "checks and this report in under a minute on one core; `... policy_cycle report` rebuilds this file from the saved tables). Outputs in "
      "`experiments/results/arms/`: `policy_cycle_positions.parquet` (daily stream of the final signal: `pos`, `fwd_bp`, `net_bp`), "
      "`policy_cycle_report.csv` (protocol table, all 10 candidates, `variant`, `final`), `policy_cycle_reaction_accuracy.csv`, "
      "`policy_cycle_reaction_confusion.csv`, `policy_cycle_reaction_turning_points.csv`, `policy_cycle_reaction_coefficients.csv`, "
      "`policy_cycle_reaction_diagnostics.csv`, `policy_cycle_events.csv` (every turning point, phase spell and joint-state spell with dates and "
      "forward returns), `policy_cycle_event_cells.csv`, `policy_cycle_event_drift.csv`, `policy_cycle_votes.csv` (every signal x test x horizon x mode "
      "x period, incl. the timing placebo), `policy_cycle_bar.csv` (the Round 5 success test), `policy_cycle_paired_bootstrap.csv`, "
      "`policy_cycle_signals.parquet`, `policy_cycle_incremental.csv`, `policy_cycle_leakchecks*.csv`. New data file `data/macro/policy_state.csv` "
      "(daily, reproducible from `run()`). Everything in the module docstring (definitions, priors, the 10 candidates, the selection rule, the "
      "success test) was written before the first result.\n")
    w("## Verdict\n")
    w(VERDICT + "\n")
    # ------------------------------------------------------------------ data
    w("## 0. Data, lags, definitions\n")
    w("| series | file | range | publication lag assumed |\n|---|---|---|---|\n"
      "| Fed target | `fred_DFEDTAR`, `fred_DFEDTARL/U`, `fomc_decisions.csv` (meeting dates, target after the mirror ends 2026-09-20) | 1982-09-27 .. 2026-10-28 | announcement day (FOMC date at most one day before the change date) |\n"
      "| Fed proxy before 1982-10 (event study only) | `fred_FEDFUNDS` monthly | 1954 .. 1982-08 | day after month end |\n"
      "| ECB key-rate index | `ecb_policy_rates.csv` (MRO changes before 2014-06-11, deposit-rate changes after), `ecb_decisions.csv` | 1999 .. 2026-11-10 | Governing Council date (at most 14 days before the effective date) |\n"
      "| Bundesbank proxy before 1999 | `fred_IR3TIB01DEM156N` (German 3-month interbank, monthly average) | 1960 .. 1998 | day after month end |\n"
      "| US CPI, core CPI, unemployment, Sahm gap, payrolls, industrial production, retail sales | `fred_CPIAUCSL`, `CPILFESL`, `UNRATE`, `SAHMREALTIME`, `PAYEMS`, `INDPRO`, `RSAFS` | to 2026-09 | reference-month end + 21 days |\n"
      "| US core PCE | `fred_PCEPILFE` | to 2026-09 | + 35 days |\n"
      "| US initial claims / NFCI | `fred_ICSA` / `fred_NFCI` (ends 2026-09-11, then stale > 60 days = missing) | weekly | week end + 5 days |\n"
      "| VIX, US 2y, euro-area AAA 2y, EONIA / EUR-STR | `fred_VIXCLS`, `fred_DGS2`, `ea_aaa_yield_curve.csv` (2004-09+), `ea_overnight_rates.csv` | daily | same day in `policy_state.csv`; the FX tests read the row of closing date - 1 |\n"
      "| Euro-area HICP | `fred_CP0000EZ19M086NEST` (index, y/y by differencing; `ea_hicp.csv` is stale after 2025-12 and not used) | 1996-12 .. 2026-09 | + 21 days |\n"
      "| Euro-area unemployment | `ea_unemployment.csv` | 2000-01 .. 2026-09 | + 35 days |\n"
      "| German CPI (Bundesbank line) | `fred_DEUCPIALLMINMEI` | 1955 .. 1998 used | + 30 days |\n"
      "| EUR/USD | synthetic DEM euro 1975-98, H.10 / ECB reference 1999-2002, feature store 2003+ (`arms/swing.load_prices`) | 1975 .. 2026-11-06 | - |\n")
    w("* US reference months 2025-09..2025-11 (shutdown) are not used before 2026-01-31; October 2025 CPI / unemployment are missing in the mirror and "
      "yield no observation. Availability dates are forced to be non-decreasing; a value older than 150 days (weekly series 60, daily 10) is missing.\n"
      "* **Data-revision risk.** The FRED mirrors hold the LATEST vintage. Unemployment rate and CPI are lightly revised (seasonal factors only), "
      "`SAHMREALTIME` is a real-time series by construction; payrolls, industrial production and retail sales are revised materially (benchmark "
      "revisions of payrolls can move the 12-month growth by 0.3-0.5 points), and the NFCI is re-estimated on the full sample every week, so its "
      "history contains information that was not available at the time (the reaction functions are re-run without it in section 5: nothing "
      "changes). Euro-area unemployment is revised by 0.1-0.3 points. Revisions favour the fitted models, so the true real-time accuracy of the "
      "reaction functions is, if anything, lower than shown; the conclusions below do not depend on a small margin.\n"
      "* No euro-area activity series (production, surveys) exists in `data/macro/`; the ECB reaction function has inflation, unemployment, VIX, "
      "its own policy block and the Fed's stance only. Core HICP is not used because `ea_hicp.csv` stops in 2025-12.\n"
      "* `data/macro/policy_state.csv` (business days 1990-01-01 .. data end, rebuilt by `run()`): each row is what is known at the END of that "
      "date. Columns: `fed_target`, `ecb_deposit_rate`, `ecb_main_refi_rate`, `ecb_key_index` (an index of key-rate CHANGES, not a rate); per bank "
      "`*_phase` (hiking / cutting / hold_after_hikes / hold_after_cuts), `*_dir3`, `*_months_since_move`, `*_last_move_pp`; `joint_state`; "
      "`*_p_cut_6m / p_hold_6m / p_hike_6m` and `*_model_chg6m_bp` (walk-forward ordered logit; Fed from 1990, ECB from 2004), "
      "`*_slope_2y_minus_policy` (pp) and `*_priced_chg6m_bp` (the market model; ECB from 2008), `*_gap_bp` = model - priced, `model_rel_bp`, "
      "`priced_rel_bp`, `gap_rel_bp` (ECB minus Fed); `sig_<candidate>` = the signal in force for the session CLOSING on that date (it uses the "
      "row of the previous calendar day).\n"
      f"* Phases are causal: a bank is hiking / cutting while its last move in the trend direction is at most {HOLD_DAYS} days old, then on hold. "
      "Turning points = the first move against the trend (cumulative 20 bp; 75 bp for the monthly proxies).\n")
    # ------------------------------------------------------------------ (1)
    w("## 1. Can the next policy move be predicted from the economy?\n")
    w("Walk-forward (yearly expanding; a model for year Y sees only rows whose label is known before Y-01-01). `next` = direction of the change from "
      "just after one scheduled meeting to just after the next (features as known on the day of the earlier meeting); `m3`, `m6` = direction of the "
      "cumulative change over the next 3 / 6 months from each month-end. Accuracy in %, three classes.\n")
    w("**Overall accuracy against the naive baselines**\n")
    w(_md(_acc_table(A, ["all"])) + "\n")
    w("**At turning points - meetings (`next`)**: persistence is right by construction on the 'no change' rows and wrong on every 'change' row, "
      "so these rows are where a reaction function has to earn its keep.\n")
    tsub = ["first cut after hikes", "first hike after cuts", "first pause (hold after a move)", "resumption (same direction after a hold)",
            "any change vs previous decision", "no change vs previous decision"]
    x = _acc_table(A[(A.target == "next")], tsub)
    w(_md(x.drop(columns=["market slope only", "logit + slope"], errors="ignore")) + "\n")
    w("**At turning points - month-end targets**: rows whose label differs from the trailing 3- / 6-month direction (persistence is wrong on all of them).\n")
    x = _acc_table(A[A.target.isin(["m3", "m6"])], ["label differs from the trailing direction"])
    w(_md(x) + "\n")
    DIS = (o["rf_tables"] if "rf_tables" in o else o["rf"]).get("dis")
    if DIS is not None and len(DIS):
        d = DIS.copy()
        d["departs from persistence"] = d.apply(lambda q: f"{int(q['n_disagree'])} of {int(q['n_all'])}", axis=1)
        for c in ("model_right", "persistence_right", "neither_right"):
            d[c] = d[c].map(lambda v: f"{100 * v:.0f}" if pd.notna(v) else "")
        w("**When a model departs from persistence, who is right?** (% of the decisions on which the model's call differs from the persistence "
          "call; this is the false-alarm side of the turning-point tables)\n")
        w(_md(d[["bank", "target", "period", "model", "departs from persistence", "model_right", "persistence_right", "neither_right"]], numparse=False) + "\n")
    w("**The forecast made at the last month-end before each first cut / first hike** (the label is the realised direction over the following "
      "3 / 6 months; 2026 turns have no 6-month label yet). Count of correct calls:\n")
    rows = []
    for (bank, tg), g in TP.groupby(["bank", "target"]):
        g = g[g["label"].notna()]
        r = {"bank": bank, "target": tg, "turning points": len(g)}
        for m in ("always_hold", "persistence", "last_move", "taylor", "ologit", "market", "ologit+market"):
            c = f"pred_{m}"
            if c in g:
                k = g[c].notna()
                r[m] = f"{int((g.loc[k, c] == g.loc[k, 'label']).sum())}/{int(k.sum())}" if k.sum() else ""
        rows.append(r)
    w(_md(pd.DataFrame(rows)) + "\n")
    t6 = TP[TP.target == "m6"].copy()
    for c in ("label", "pred_persistence", "pred_taylor", "pred_ologit", "pred_market"):
        t6[c] = t6[c].map({-1.0: "cut", 0.0: "hold", 1.0: "hike"}).fillna("")
    t6 = t6.rename(columns={"turn_date": "turn", "origin": "forecast date", "label": "realised 6m", "pred_persistence": "persistence", "pred_taylor": "Taylor",
                            "pred_ologit": "ordered logit", "pred_market": "market slope"})
    for c in ("p_cut", "p_hold", "p_hike"):
        t6[c] = (100 * t6[c]).round(0)
    w("Every turn, 6-month model (probabilities in %):\n")
    w(_md(t6[["bank", "turn", "type", "forecast date", "realised 6m", "persistence", "Taylor", "ordered logit", "p_cut", "p_hold", "p_hike", "market slope"]], ".0f") + "\n")
    w("**Is the reaction function already in the 2-year yield?** RMSE of the realised 6-month change (bp), 2010-2026, rows where a slope exists:\n")
    x = A[A["subset"].str.startswith("RMSE")][["bank", "n", "acc_always_hold", "acc_ologit", "acc_market", "acc_ologit+market"]]
    x.columns = ["bank", "n", "forecast = no change", "ordered logit (economy + own policy)", "market slope only", "both"]
    w(_md(x, ".1f") + "\n")
    w("**Confusion matrices, ordered logit (rows = what happened, columns = what was predicted), longest out-of-sample period**\n")
    for bank in ("fed", "ecb"):
        for tg in ("next", "m6"):
            c = CONF[(CONF.bank == bank) & (CONF.target == tg) & (CONF.model == "ologit")]
            c = c[c.period == c.period.iloc[0]]
            w(f"*{bank}, {tg}, {c.period.iloc[0]}*\n\n" + _md(c[["actual", "n", "pred_cut", "pred_hold", "pred_hike"]]) + "\n")
    w("**Bundesbank robustness line** (German 3-month rate as the policy proxy, +-25 bp dead band, test years 1975-1998):\n")
    w(_md(_acc_table(o["bbk"], ["all", "label differs from the trailing direction"], banks=tuple(o["bbk"]["bank"].unique()))) + "\n")
    if "rf_diag" in o:
        d = o["rf_diag"].copy()
        for c in d.columns[4:]:
            d[c] = (100 * d[c]).round(0)
        d = d.drop(columns=["period"]).set_index(["bank", "target"]).T.reset_index().rename(columns={"index": "variant (accuracy %, all out-of-sample months)"})
        d.columns = [" ".join(c) if isinstance(c, tuple) else c for c in d.columns]
        w("**Diagnostics added after the first run of this part** (nothing selected from them, no signal uses them): which block carries the model?\n")
        w(_md(d, ".0f") + "\n")
    w("**Largest standardised coefficients of the last fit (2026), ordered logit**; `corr` = full-sample correlation of the standardised feature "
      "with the label (leak check 3: the largest is the bank's own recent change, i.e. persistence; nothing is a label in disguise).\n")
    rows = []
    for (bank, tg), g in COEF.groupby(["bank", "target"]):
        g = g.reindex(g["coef_std"].abs().sort_values(ascending=False).index).head(6)
        rows.append({"bank": bank, "target": tg, "top features (coef, corr)": "; ".join(f"{a} ({b:+.2f}, {c:+.2f})" for a, b, c in zip(g.feature, g.coef_std, g.corr_with_label))})
    w(_md(pd.DataFrame(rows)) + "\n")
    # ------------------------------------------------------------------ (2)
    w("## 2. What did EUR/USD do around the policy cycle?\n")
    w("Returns in % (log x 100) of EUR/USD, entry at the first close at least one calendar day after the announcement; `3m before` = the 63 sessions "
      "ending at the last close before it. Cells: mean (count of positive / negative episodes). **n is the number of episodes; with n of 4-17 a mean "
      "of +-2 % is noise** (one 63-session return has a standard deviation of about 5 %, so the standard error of a mean over 10 episodes is 1.6 %).\n")
    tp = E[(E.kind == "turning_point")].copy()
    tp = tp[["bank", "type", "start", "source", "price_src", "other_bank_phase", "pre63_pct", "react_pct", "f21_pct", "f63_pct", "f126_pct", "f252_pct"]]
    tp.columns = ["bank", "turn", "announced", "policy series", "price", "other bank then", "3m before", "day of", "+1m", "+3m", "+6m", "+12m"]
    w("**Every turning point since 1975** (`proxy` = monthly market-rate proxy: Fed before 1982-10, Bundesbank before 1999; confirmed only when the "
      "counter-move reaches 75 bp, so dated late; `ecb` before 1999 = Bundesbank):\n")
    w(_md(tp, ".1f") + "\n")
    for era in ("1999-2026", "1975-2026"):
        w(f"**Turning points, {era}** (prior: the bank that turns to easing has the weaker currency; `prior sign right` counts episodes moving that way):\n")
        w(_md(_event_table(EC, "turning_point", era, prior=True)) + "\n")
    w("**Pause confirmed (122 days after the last move), 1975-2026:**\n")
    w(_md(_event_table(EC, "pause", "1975-2026")) + "\n")
    for era in ("1999-2026", "1975-2026"):
        w(f"**Phases of each bank, {era}** (forward returns from the first session of each spell):\n")
        w(_md(_event_table(EC, "phase_episode", era)) + "\n")
    for era in ("1999-2026", "1975-2026"):
        w(f"**Joint states (Fed x ECB; hiking / hold / cutting), {era}:**\n")
        w(_md(_event_table(EC, "joint_episode", era)) + "\n")
    for era in ("1999-2026", "1975-2026"):
        w(f"**Policy divergence, {era}** (widening / narrowing of the policy-rate gap, and who is tightening relative to the other):\n")
        w(_md(_event_table(EC, "divergence_episode", era)) + "\n")
    d = DR[DR.era.isin(["1999-2026", "1975-2026"]) & DR.kind.isin(["joint", "divergence"])].copy()
    d = d[["kind", "state", "era", "sessions", "years", "ann_drift_pct", "t_daily_naive", "share_up_days"]]
    w("**Drift of EUR/USD while each joint state lasted** (annualised %, t from daily returns; the t-statistic treats days as independent and still "
      "finds nothing above 2 in 1999-2026):\n")
    w(_md(d, ".2f") + "\n")
    # ------------------------------------------------------------------ (3)
    w("## 3. Is there a tradeable signal the market has not priced?\n")
    cov = []
    for nm, typ in CANDIDATES:
        x = Sg[nm][Sg.index.year >= 2010]
        cov.append({"candidate": nm, "type": typ, "declared vote form": {"vote_agree": "agreement rule AND signal agrees", "vote_veto": "agreement rule UNLESS signal opposes"}[FORM[typ]],
                    "long %": round(100 * float((x > 0).mean())), "short %": round(100 * float((x < 0).mean())), "silent %": round(100 * float(((x == 0) | x.isna()).mean())),
                    "sign changes / year": round(float((np.sign(x.fillna(0)).diff().abs() > 0).sum()) / 16.85, 1)})
    w("**The ten candidates (2010-2026 coverage)**; definitions and priors in the module docstring.\n")
    w(_md(pd.DataFrame(cov)) + "\n")
    rc = o["reconcile"].copy()
    w("**Reconciliation of the agreement rule with arm N** (2010-26):\n")
    w(_md(rc, ".3f") + "\n")
    w("### 3.1 Standalone accuracy (direction of the next 21 / 42 / 63 sessions), % [95 % interval] n (decisions a year)\n")
    for mode, lab in (("nonoverlap", "NON-OVERLAPPING decisions (Wilson interval)"), ("weekly", "weekly decisions (Wilson with the conservative effective n of arm N)")):
        rows = []
        for nm, _ in CANDIDATES:
            for h in HORIZONS:
                rows.append({"candidate": nm, "h": h, **{per: _vc(V, nm, "standalone", h, mode, per) for per in ("2010-26", "2016-26", "2023-26", "2004-09")}})
        w(f"*{lab}*\n\n" + _md(pd.DataFrame(rows)) + "\n")
    w("### 3.2 As an extra vote on the agreement rule (non-overlapping decisions)\n")
    rows = []
    for h in HORIZONS:
        rows.append({"rule": "AGREEMENT RULE alone", "h": h, **{per: _vc(V, CANDIDATES[0][0], "agree3", h, "nonoverlap", per) for per in ("2010-26", "2016-26", "2023-26", "2006-09")}})
    for nm, typ in CANDIDATES:
        for h in HORIZONS:
            rows.append({"rule": f"{nm} ({'agrees' if typ == 'dense' else 'veto'})", "h": h,
                         **{per: _vc(V, nm, FORM[typ], h, "nonoverlap", per) for per in ("2010-26", "2016-26", "2023-26", "2006-09")}})
    w("(a) vote rule in its declared form against the agreement rule alone:\n")
    w(_md(pd.DataFrame(rows)) + "\n")
    rows = []
    for nm, typ in CANDIDATES:
        if typ == "sparse":
            for h in HORIZONS:
                rows.append({"rule": f"{nm} (agrees; NOT the declared form)", "h": h, **{per: _vc(V, nm, "vote_agree", h, "nonoverlap", per) for per in ("2010-26", "2016-26", "2023-26", "2006-09")}})
    w("The other form for the sparse signals (reported, never selectable; note the decisions a year):\n")
    w(_md(pd.DataFrame(rows)) + "\n")
    rows = []
    for nm, _ in CANDIDATES:
        for h in HORIZONS:
            rows.append({"candidate": nm, "h": h, **{per: _vc(V, nm, "extend", h, "nonoverlap", per) for per in ("2010-26", "2016-26", "2023-26", "2006-09")}})
    w("(b) calls the signal makes when the three old signals do NOT agree (does it extend coverage?):\n")
    w(_md(pd.DataFrame(rows)) + "\n")
    bo = BO[BO.declared_form].copy()
    bo["weekly accuracy, vote minus agreement rule (points) [95 % block bootstrap]"] = bo.apply(lambda q: f"{100 * q['diff']:+.1f} [{100 * q['lo']:+.1f}, {100 * q['hi']:+.1f}]" if pd.notna(q["diff"]) else "-", axis=1)
    bo["kept minus removed decisions"] = bo.apply(lambda q: f"{100 * q['diff_kept_minus_dropped']:+.1f} [{100 * q['lo_kd']:+.1f}, {100 * q['hi_kd']:+.1f}]" if pd.notna(q["diff_kept_minus_dropped"]) and pd.notna(q["lo_kd"]) else "-", axis=1)
    w("(c) paired difference on the weekly grid (circular block bootstrap, block 2h/5 weeks, 2000 draws):\n")
    w(_md(bo[["signal", "h", "period", "weekly accuracy, vote minus agreement rule (points) [95 % block bootstrap]", "kept minus removed decisions"]]) + "\n")
    w("### 3.3 The Round 5 success test and the timing placebo\n")
    rows = []
    for _, q in B.iterrows():
        r = {"candidate": q["candidate"], "form": "agrees" if q["form"] == "vote_agree" else "veto"}
        for per in ("2010-26", "2016-26", "2023-26"):
            for h in (21, 42):
                r[f"gain {h}s {per}"] = f"{100 * q[f'gain_{h}_{per}']:+.1f}"
        r["dec/y 21s (2010-26 / 2016-26)"] = f"{q['vote_dpy_21_2010-26']:.1f} / {q['vote_dpy_21_2016-26']:.1f}"
        for k in PLACEBO_SHIFTS:
            r[f"placebo +{k}: gain 21s / 42s (2010-26; 2016-26)"] = (f"{100 * q[f'placebo{k}_gain_21_2010-26']:+.1f} / {100 * q[f'placebo{k}_gain_42_2010-26']:+.1f}; "
                                                                      f"{100 * q[f'placebo{k}_gain_21_2016-26']:+.1f} / {100 * q[f'placebo{k}_gain_42_2016-26']:+.1f}")
        for c, lab in (("pass_gain_3pts", ">= 3 pts x4"), ("pass_6_per_year", ">= 6 / y"), ("pass_2023_not_worse", "2023-26 not worse"), ("pass_placebo", "placebo loses half"),
                       ("PASS_ROUND5_BAR", "BAR MET")):
            r[lab] = "yes" if q[c] else "no"
        r["2010-15 vote acc 21s (selection)"] = f"{100 * q['vote_21_2010-15']:.0f}" + (" *" if q["final"] else "") + ("" if q["eligible_for_final"] else " (not eligible)")
        rows.append(r)
    w("Gain = non-overlapping accuracy of the vote rule minus the agreement rule, in points. The bar: gain >= 3 at 21 and 42 sessions in 2010-26 "
      "and 2016-26, at least 6 non-overlapping 21-session decisions a year, 2023-26 not worse, and the signal shifted by +63 and +126 sessions keeps "
      "at most half of the gain. `*` = final by the declared rule (best 2010-15 vote accuracy at 21 sessions among eligible candidates).\n")
    w(_md(pd.DataFrame(rows), numparse=False) + "\n")
    w(f"**Final by the declared rule: `{o['final']}`** ({o['final_status']}). Delivered stream = its standalone daily sign.\n")
    w("### 3.4 Protocol table (standalone daily sign of each candidate, 1.2 pips, net Sharpe / t) and the incremental test\n")
    rows = []
    for vn, g in REP.groupby("variant", sort=False):
        g = g.set_index("period")
        r = {"variant": vn, "kind": g["kind"].iloc[0], "final": bool(g["final"].iloc[0])}
        for per in ("2010-2026", "2016-2026", "2023-2026", "2010-2015"):
            r[per] = f"{g.loc[per, 'sharpe']:+.2f} ({g.loc[per, 't']:+.1f})"
        r["active"] = f"{100 * g.loc['2010-2026', 'active_frac']:.0f} %"
        r["deflated-Sharpe p (n=10)"] = f"{g.loc['2010-2026', 'deflated_sharpe_p']:.2f}"
        rows.append(r)
    w(_md(pd.DataFrame(rows)) + "\n")
    hit = o["hit"].copy()
    w("Hit rate of the delivered daily stream (active sessions):\n\n" + _md(hit, ".3f") + "\n")
    if "incremental" in o:
        inc = o["incremental"]
        x = inc[inc.period.isin(["2010-2026", "2016-2026", "2023-2026"])][["combo", "period", "sharpe", "t"]]
        w("Incremental test (`meta.combine(..., 'EW')`, `report_combo`):\n\n" + _md(x, ".3f") + "\n")
        w(f"Daily-P&L correlation of the delivered stream with `weak_signals` {inc['corr_weak_signals'].iloc[0]:+.2f}, with `regime_trend` {inc['corr_regime_trend'].iloc[0]:+.2f}.\n")
    # ------------------------------------------------------------------ leak checks
    w("## 4. Leak checks\n")
    if "leak" in o:
        Lk = o["leak"]
        x = Lk[Lk.h == 21].groupby(["check"], sort=False)[["standalone_weekly_2010-26", "vote_nonoverlap_2010-26"]].mean().reset_index()
        x["agreement rule itself"] = Lk[Lk.h == 21].groupby(["check"], sort=False)["agree3_nonoverlap_2010-26"].mean().values
        w("(1) and (2) for the exchange-rate side: average over the ten candidates, 21 sessions, 2010-26 (standalone weekly accuracy; non-overlapping "
          "accuracy of the declared vote rule; the agreement rule on the same labels). No signal is fitted to an exchange rate, so the shuffle "
          "must give a coin and does. Shifting the signals INTO THE FUTURE does not help either: the signals contain no price, so there is nothing "
          "for a look-ahead to exploit, and making them 1-21 sessions staler changes nothing, which is the same message as the timing placebo: "
          "what little they show is regime, not timing.\n")
        w(_md(x, ".3f") + "\n")
        fin = o["stream_name"]
        y = Lk[(Lk.signal == fin)][["check", "h", "standalone_weekly_2010-26", "vote_nonoverlap_2010-26", "agree3_nonoverlap_2010-26"]]
        w(f"The same for the final signal `{fin}`:\n\n" + _md(y, ".3f") + "\n")
    if "leak_rf" in o:
        R = o["leak_rf"]
        x = R[(R.subset == "all")].pivot_table(index=["bank", "target", "period"], columns="check", values="acc_ologit", sort=False).reset_index()
        w("(1) and (2) for the reaction functions (ordered logit, accuracy on all out-of-sample decisions): policy labels shuffled inside every "
          "training window; every publication lag 365 days longer; every publication lag 182 days SHORTER (a deliberate look-ahead: the Fed's "
          "3- and 6-month targets gain 5-7 points, the meeting target and the ECB do not, i.e. what limits these models is the instability of "
          "the relation, not the timeliness of the data); the model without the NFCI (revision risk: no difference).\n")
        w(_md(x, ".3f") + "\n")
    if "leak_trunc" in o:
        w("(4) Truncation test: `policy_state` rebuilt from raw data cut at three dates; every numeric column of every row up to the cut is compared "
          "with the full-history table (phases, model probabilities, priced path, gaps).\n")
        w(_md(o["leak_trunc"], ".2e") + "\n")
    w("(3) Top features: see the coefficient table in section 1. The reaction functions never see an exchange rate; the FX signals are fixed-sign "
      "rules, so no feature can be an FX label in disguise.\n")
    w("## 5. Variant count, caveats\n")
    w("* **Exchange-rate candidates: 10** (limit 12), each with one declared vote form; the other vote form of the five sparse signals is tabulated "
      "and not selectable (strict count 15). Not candidates: the timing placebo (20 shifted copies), 3 label shuffles, 5 staleness / look-ahead "
      "shifts, one 0.6-pip re-costing.\n"
      "* Reaction functions (no exchange rate involved): 2 banks x 3 targets x (ordered logit, Taylor-type rule) + 2 x 2 market / combined models, "
      "one Bundesbank line, and the diagnostics table added after the first run (4 feature-block variants and 2 penalties per bank and target; "
      "nothing was adopted from it: the declared model is the one used everywhere).\n"
      "* Added after the first run and labelled as such: the diagnostics table, the 'departs from persistence' table, and a fix that keeps "
      "pre-2003 turning points out of the first 63 sessions of `turn63` (2003 is outside every evaluated period). Candidates, signals, "
      "selection rule and success test are exactly as declared in the module docstring before the first result.\n"
      "* The 2026 policy history in the mirrors (ECB hikes of 2026-06 and 2026-09, Fed hike of 2026-09) is taken as given.\n"
      "* The market-priced path is a 2-year yield minus the policy rate. It mixes a term premium and two years of expectations; proper pricing "
      "(OIS / futures strips) is not reachable from here (see arm H). That limits the 'economy vs priced' test.\n")
    (path or REPORTS / f"arm_{ARM}.md").write_text("\n".join(L))


if __name__ == "__main__":
    import pickle
    pk = RES / "logs" / f"{ARM}_tables.pkl"
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        with open(pk, "rb") as fh:
            write_report(pickle.load(fh))
        print("report rebuilt")
        sys.exit(0)
    cp = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
    pos, rep = run(cp)
    o = run.last
    print("final:", o["final"], "|", o["final_status"], flush=True)
    o["rf_diag"] = rf_diagnostics(o["end"])
    o["rf_diag"].to_csv(RES / f"{ARM}_reaction_diagnostics.csv", index=False)
    o["incremental"] = incremental()
    leak_checks(o)
    (RES / "logs").mkdir(exist_ok=True)
    keep = {k: v for k, v in o.items() if k not in ("K", "rf", "streams")}
    keep["rf_tables"] = {k: o["rf"][k] for k in ("acc", "conf", "tp", "coef", "dis")}
    with open(pk, "wb") as fh:
        pickle.dump(keep, fh)
    write_report(keep)
    print("done", flush=True)
