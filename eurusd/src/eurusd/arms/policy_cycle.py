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
    acc, conf, tp_rows, coef, grids = [], [], [], [], {}
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
            "daily": daily, "fed": fed, "ecb": ecb}


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
    Sg["phase_rel"] = np.sign(ed - fd)
    Sg["fed_phase"] = -fd
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
        known = cdl - pd.Timedelta(days=1)
        for nm, _ in CANDIDATES:      # the signal value that uses the row of date d is the one of the first session closing after d
            ps[f"sig_{nm}"] = pd.Series(Sg[nm].values, index=known).groupby(level=0).last().reindex(ps.index)
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
    num = [c for c in PS.columns if PS[c].dtype != object]
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


if __name__ == "__main__":
    import pickle
    cp = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
    pos, rep = run(cp)
    o = run.last
    print("final:", o["final"], "|", o["final_status"])
    inc = incremental()
    o["incremental"] = inc
    leak_checks(o)
    (RES / "logs").mkdir(exist_ok=True)
    keep = {k: v for k, v in o.items() if k not in ("K", "rf", "streams")}
    keep["rf_tables"] = {k: o["rf"][k] for k in ("acc", "conf", "tp", "coef")}
    with open(RES / "logs" / f"{ARM}_tables.pkl", "wb") as fh:
        pickle.dump(keep, fh)
    print("done", flush=True)
