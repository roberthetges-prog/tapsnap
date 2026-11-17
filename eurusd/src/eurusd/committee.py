"""The committee: 110 independent analysts (the original 100 plus a Fed desk of 10) vote on EUR/USD direction,
and the vote is scored against history.

Why it is built this way. A hundred copies of one forecaster agree with each other and their vote share says
nothing. A vote is worth counting only if (1) the voters look at DIFFERENT evidence or learn DIFFERENTLY and
(2) what a given majority was worth is MEASURED out of sample. So:

* 50 views of the evidence in 10 schools (positioning, rate momentum, rate levels, central banks, economy, trend,
  value, risk, curve / oil / dollar, generalists). Every view is one oriented number: positive = long EUR/USD under
  the stated prior. Everything the seven research rounds looked at at the multi-week horizon is represented,
  including the views that failed on their own (a committee is allowed dissenters; the test decides what it is worth).
* Two temperaments read each view, which makes 100 analysts:
    D  doctrinaire: direction fixed by the economic prior; conviction learned from ALL history to date
       (Platt scaling with slope >= 0, so a prior that history contradicts falls silent).
    E  empiricist: no prior; sign and conviction learned from the LAST TEN YEARS only; speaks only when its own
       evidence has |t| >= 1 after correcting for overlapping horizons.
* An analyst has a view only if its own probability is at least 51/49 (EPS). Otherwise it abstains.
* Question put to all of them: will EUR/USD close higher or lower in h sessions (h = 21, 42, 63)?
* Walk-forward, yearly, expanding: for test year Y an analyst is fitted only on rows whose h-session outcome was
  known before Y-01-01. Standardisation uses the training window only.

Committee read-out: up / down / no view counts, share = majority / (up + down), quorum = at least 20 voters.
Majority classes (DECLARED BEFORE ANY RESULT WAS LOOKED AT, 2026-11-17, one design, no tuning):
    split  50-55 %   |   lean  55-65 %   |   clear  65-80 %   |   strong  80-100 %

KEEP BAR (declared with the design; the round-5 extra-vote bar): the 'clear or strong' call (share >= 65 %, quorum met)
earns a vote in the position call only if, on phase-averaged non-overlapping accuracy, it beats the three-signal
agreement rule by >= 3 points at BOTH 21 and 42 sessions in BOTH 2010-26 and 2016-26 with >= 6 independent decisions
a year, AND a copy that is 63 sessions stale loses at least half of the edge over 50 %. If it misses the bar the
read-out stays available as a description, labelled with the hit rate it actually had, and decides nothing.

TRIAL 2 (2026-11-17, declared before running): the owner asked that the analysts also consider Fed meetings and
decisions. A FED school of 5 views (10 analysts) is added: what the Fed did at its latest meeting, the direction of its
last move, the 2-year yield's reaction on decision day, EUR/USD's own reaction on decision day, and what the 2-year
yield prices relative to the policy rate. Each state is held from the decision until the next meeting. Everything
else (temperaments, EPS, quorum, classes, keep bar) is unchanged. The test reports the committee with and without it.

Honesty note: the views carrying a HOUSE prior (marked) had their sign chosen by earlier rounds on this same
history, so the committee's 2010-26 record flatters them. Textbook-prior views do not have this problem.
"""
from __future__ import annotations

import json
import math
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import features as F  # noqa: E402
from eurusd.arms import swing as SW  # noqa: E402
from eurusd.arms import weak_signals as WS  # noqa: E402

RES = ROOT / "experiments" / "results" / "arms"
HORIZONS = (21, 42, 63)
TEST_YEARS = list(range(2006, 2027))
EPS = 0.01                 # an analyst speaks only at 51/49 or better
MIN_ROWS = 750             # training rows an analyst needs before it may speak
E_MEMORY_YEARS = 10
E_MIN_T = 1.0
QUORUM = 20
CLASSES = (("split", 0.50, 0.55), ("lean", 0.55, 0.65), ("clear", 0.65, 0.80), ("strong", 0.80, 1.0001))
ERAS = (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026))
SCHOOLS = {"FED": "Fed meetings", "POS": "Positioning", "RC": "Rate momentum", "RL": "Rate levels", "CB": "Central banks", "ECO": "Economy",
           "TR": "Trend", "VAL": "Value", "RISK": "Risk appetite", "XA": "Curve, oil, dollar", "GEN": "Generalists"}

# view id: (school, column, kind, prior, plain description)
#   kind 'cont'  scaled by the training std (the raw sign is the content), clipped +-2, halved
#        'level' demeaned by the training mean first
#        'bin'   already in [-1, 1]
#   column '@name' = fitted inside each fold (see _fold_columns); '{h}' = horizon-specific column
VIEWS = {
    "fed_latest":  ("FED", "fed_latest", "bin", "textbook", "the Fed's latest meeting: a cut weakens the dollar, a hike lifts it"),
    "fed_cycle":   ("FED", "fed_cycle", "bin", "textbook", "direction of the Fed's last rate move (cutting cycle = dollar weaker)"),
    "fed_surprise": ("FED", "fed_surprise", "cont", "textbook", "the 2-year yield's reaction on Fed decision day (a fall = dovish surprise = dollar weaker)"),
    "fed_fx":      ("FED", "fed_fx", "cont", "textbook", "EUR/USD's own move on Fed decision day: follow it to the next meeting"),
    "fed_priced":  ("FED", "fed_priced", "cont", "textbook", "what markets price for the Fed (2-year yield above the policy rate = hikes priced = dollar stronger)"),
    "cot_z52":     ("POS", "cot_z52", "cont", "HOUSE", "speculators' net euro position vs its 1-year norm: follow them"),
    "cot_z156":    ("POS", "cot_z156", "cont", "HOUSE", "speculators' net euro position vs its 3-year norm: follow them"),
    "cot_d4":      ("POS", "cot_d4", "cont", "follow", "4-week change in speculators' position: follow the flow"),
    "cot_lev":     ("POS", "cot_lev_z52", "cont", "follow", "leveraged funds' position vs its 1-year norm"),
    "cot_ext":     ("POS", "cot_ext", "bin", "textbook", "crowded positioning reverses: fade extremes"),
    "sp2_d20":     ("RC", "d_spread2y_20", "cont", "HOUSE", "1-month change in the euro-US 2-year yield gap"),
    "rd2_d63":     ("RC", "rd2_d63", "cont", "textbook", "3-month change in the 2-year yield gap"),
    "rd2_d126":    ("RC", "rd2_d126", "cont", "textbook", "6-month change in the 2-year yield gap"),
    "rd10_d63":    ("RC", "rd10_d63", "cont", "textbook", "3-month change in the 10-year yield gap"),
    "rd10_d126":   ("RC", "rd10_d126", "cont", "textbook", "6-month change in the 10-year yield gap"),
    "rd2_lvl":     ("RL", "rd2_lvl", "cont", "textbook", "level of the 2-year yield gap: the higher yield attracts money"),
    "rd10_lvl":    ("RL", "rd10_lvl", "cont", "textbook", "level of the 10-year yield gap"),
    "rrd2_lvl":    ("RL", "rrd2_lvl", "cont", "textbook", "2-year gap after inflation (real yields)"),
    "rrd10_lvl":   ("RL", "rrd10_lvl", "cont", "textbook", "10-year gap after inflation (real yields)"),
    "carry":       ("RL", "carry", "cont", "textbook", "overnight rate gap (carry)"),
    "pol_lvl":     ("CB", "pol_lvl", "cont", "textbook", "ECB policy rate minus Fed policy rate"),
    "pol_d63":     ("CB", "pol_d63", "cont", "textbook", "3-month change in the policy-rate gap"),
    "pol_d126":    ("CB", "pol_d126", "cont", "textbook", "6-month change in the policy-rate gap"),
    "fed_dir":     ("CB", "fed_dir", "cont", "textbook", "Fed cutting over the last 6 months = dollar weaker"),
    "ecb_dir":     ("CB", "ecb_dir", "cont", "textbook", "ECB hiking over the last 6 months = euro stronger"),
    "infl_gap":    ("ECO", "infl_gap", "cont", "textbook", "euro-area inflation above US inflation = tighter ECB"),
    "infl_d126":   ("ECO", "infl_d126", "cont", "textbook", "6-month change in the inflation gap"),
    "labour":      ("ECO", "labour", "cont", "textbook", "US unemployment rising faster than euro-area unemployment"),
    "us_surprise": ("ECO", "us_surprise", "cont", "textbook", "US data beating forecasts = dollar stronger"),
    "sahm":        ("ECO", "sahm", "level", "textbook", "US recession warning (Sahm rule) rising = Fed cuts ahead"),
    "mom21":       ("TR", "ret_21d", "cont", "textbook", "1-month price trend"),
    "mom63":       ("TR", "mom63", "cont", "textbook", "3-month price trend"),
    "mom126":      ("TR", "mom126", "cont", "textbook", "6-month price trend"),
    "sma50_200":   ("TR", "sma50_200", "bin", "textbook", "50-day average above the 200-day average"),
    "brk126":      ("TR", "brk126", "bin", "textbook", "last break of the 6-month range was upward"),
    "ppp":         ("VAL", "ppp_dev", "cont", "textbook", "cheap vs purchasing-power parity"),
    "ma5y":        ("VAL", "ma5y_dev", "cont", "textbook", "below its 5-year average"),
    "fair_value":  ("VAL", "fv_neg", "cont", "HOUSE", "cheap vs the level the 2-year gap implies"),
    "rev252":      ("VAL", "rev252", "cont", "HOUSE", "12-month move reverses"),
    "rev20":       ("VAL", "rev20", "cont", "textbook", "stretched vs its 20-day range: snaps back"),
    "vix":         ("RISK", "vix_lvl", "cont", "textbook", "fear (VIX) above normal = dollar bid"),
    "eqrel":       ("RISK", "eqrel63", "cont", "HOUSE", "European shares beating US shares over 3 months"),
    "spx20":       ("RISK", "spx_ret_20", "cont", "textbook", "US shares rising = risk-on, dollar softer"),
    "gold20":      ("RISK", "gold_ret_20", "cont", "textbook", "gold rising = dollar weaker"),
    "vix_d5":      ("RISK", "vix_d5_neg", "cont", "textbook", "fear jumping this week = dollar bid"),
    "slope2":      ("XA", "slope2_diff", "cont", "textbook", "the flatter yield curve's currency outperforms (10y-2y)"),
    "slope3m":     ("XA", "slope3m_diff", "cont", "textbook", "the same with the 3-month rate"),
    "oil63":       ("XA", "oil_d63", "cont", "textbook", "oil falling over 3 months helps the euro area"),
    "oil126":      ("XA", "oil_d126", "cont", "textbook", "oil falling over 6 months"),
    "usd20":       ("XA", "usd_neg", "cont", "HOUSE", "dollar weak against five other majors over a month"),
    "house":       ("GEN", "@house", "cont", "HOUSE", "the live 14-signal macro score"),
    "scorecard":   ("GEN", "scorecard", "bin", "textbook", "equal-weight scorecard of 11 evidence families"),
    "agreement":   ("GEN", "@agree", "bin", "HOUSE", "positioning, rate trend and macro score all agree"),
    "season":      ("GEN", "seas{h}", "bin", "HOUSE", "December strength / May weakness"),
    "month":       ("GEN", "seas_month{h}", "bin", "learned", "month-of-year pattern learned from earlier years"),
}
assert len(VIEWS) == 55
AGENTS = [f"{v}:{t}" for v in VIEWS for t in ("D", "E")]


# ============================================================================= frame
def price_frame(D: pd.DataFrame, h1: pd.DataFrame) -> pd.DataFrame:
    """swing.load_prices() for an arbitrary (possibly live) daily feature frame D and its hourly bars."""
    d = F.daily_ohlc(h1[["open", "high", "low", "close"]], 22).reindex(D.index)
    hd = pd.DataFrame({"open": d.open, "high": d.high, "low": d.low, "close": D["close"], "src": "histdata"}, index=D.index)
    hd["cdate"] = pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None)
    h10 = SW._ms("fred_DEXUSEU.csv")
    ecb = pd.read_csv(SW.PROC / "ecb_EURUSD_D1.csv", parse_dates=["date"]).set_index("date")["usd_per_eur"].astype(float)
    p99 = h10.combine_first(ecb).loc["1999-01-04":"2002-12-31"]
    p99 = p99[p99.index.dayofweek < 5].dropna()
    frames = []
    for s, src in ((SW.synthetic_dem_eur(), "synth_dem"), (p99, "h10")):
        idx = pd.DatetimeIndex(s.index).tz_localize("UTC") - pd.Timedelta(hours=2)
        frames.append(pd.DataFrame({"open": s.values, "high": s.values, "low": s.values, "close": s.values, "src": src,
                                    "cdate": s.index.values}, index=idx))
    P = pd.concat(frames + [hd])
    P.index = pd.DatetimeIndex(P.index).as_unit("us")
    P.index.name = "time"
    P["cdate"] = pd.to_datetime(P["cdate"])
    ct = pd.Series(pd.DatetimeIndex(P["cdate"]).tz_localize("UTC") + pd.Timedelta(hours=22), index=P.index)
    ct.loc[D.index] = pd.DatetimeIndex(D["close_time"]).tz_convert("UTC")
    P["close_time"] = pd.DatetimeIndex(ct).as_unit("us")
    return P


def refresh_fed_target() -> str:
    """The mirror that feeds fred_DFEDTAR[UL].csv can lag by months; FRED itself answers curl. Overwrite only with a
    longer series."""
    import io
    import subprocess
    out = []
    for sid in ("DFEDTARU", "DFEDTARL"):
        p = SW.MACRO / f"fred_{sid}.csv"
        try:
            txt = subprocess.run(["curl", "-sS", "-f", "--http1.1", "-m", "60", f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}"],
                                 capture_output=True, text=True, check=True).stdout
            d = pd.read_csv(io.StringIO(txt))
            d.columns = ["date", "value"]
            d["value"] = pd.to_numeric(d["value"], errors="coerce")
            d = d.dropna()
            old = pd.read_csv(p)
            if len(d) > 1000 and str(d["date"].iloc[-1]) >= str(old.iloc[-1, 0]):
                d.to_csv(p, index=False)
            out.append(f"{sid} to {d['date'].iloc[-1]}")
        except Exception as e:
            out.append(f"{sid} FAILED {type(e).__name__}")
    return "Fed target: " + ", ".join(out)


def fed_target() -> pd.Series:
    fed_mid = (SW._ms("fred_DFEDTARL.csv") + SW._ms("fred_DFEDTARU.csv")) / 2
    fed = pd.concat([SW._ms("fred_DFEDTAR.csv"), fed_mid.dropna()]).sort_index()
    return fed[~fed.index.duplicated(keep="last")]


def fed_desk(X: pd.DataFrame, P: pd.DataFrame, A) -> pd.DataFrame:
    """The five Fed-meeting views. A decision is public at the statement time, so it is known at the first session
    close at or after it (before 2003 the 'close' is the noon-New-York fix, i.e. the next day's row). The 2-year
    yield of decision day is published a day later, so that view starts one calendar day after the meeting."""
    m = pd.read_csv(SW.MACRO / "fomc_decisions.csv")
    m["t"] = pd.to_datetime(m["statement_utc"], utc=True)
    cd = pd.DatetimeIndex(P["cdate"])
    real_close = pd.DatetimeIndex(np.where(P["src"].values == "histdata", pd.DatetimeIndex(P["close_time"]).tz_convert("UTC").tz_localize(None),
                                           cd + pd.Timedelta(hours=17)))
    last_close = real_close[-1]
    m = m[m["t"].dt.tz_localize(None) <= last_close].sort_values("t")
    tgt = fed_target()
    us2 = SW._ms("fred_DGS2.csv")
    lc = np.log(P["close"].values)
    n = len(P)
    latest, cycle, sur, fx = (np.full(n, np.nan) for _ in range(4))
    meet = np.zeros(n, dtype=int)
    cyc = np.nan
    for d, t in zip(pd.to_datetime(m["date"]), m["t"].dt.tz_localize(None)):
        i = int(real_close.searchsorted(t, side="left"))
        if i >= n or i == 0:
            continue
        if tgt.index[-1] < d + pd.Timedelta(days=1):
            dec = np.nan                                    # target series older than the meeting: decision unknown
        else:
            dec = float(tgt.asof(d + pd.Timedelta(days=1)) - tgt.asof(d - pd.Timedelta(days=1)))
        if dec == dec and abs(dec) > 1e-9:
            cyc = -np.sign(dec)
        meet[i] += 1
        latest[i] = (0.0 - np.sign(dec)) if dec == dec else np.nan
        cycle[i] = cyc
        fx[i] = lc[i] - lc[i - 1]
        a, b = us2.asof(d), us2.asof(d - pd.Timedelta(days=1))
        j = int(cd.searchsorted(d + pd.Timedelta(days=1), side="left"))
        if j < n and a == a and b == b and us2.index[-1] >= d:
            sur[max(i, j)] = -(a - b)
    F_ = pd.DataFrame({"fed_latest": latest, "fed_cycle": cycle, "fed_surprise": sur, "fed_fx": fx}, index=P.index)
    F_ = F_.groupby(np.cumsum(meet)).ffill()                 # hold each state until the next meeting's row
    F_["fed_cycle"] = F_["fed_cycle"].ffill()
    F_["fed_priced"] = -(A(us2) - A(tgt))
    F_.attrs["last_meeting"] = str(m["date"].iloc[-1]) if len(m) else ""
    allm = pd.read_csv(SW.MACRO / "fomc_decisions.csv")
    nxt = allm[(pd.to_datetime(allm["date"]) > cd[-1]) & allm["scheduled"]]["date"]
    F_.attrs["next_meeting"] = str(nxt.iloc[0]) if len(nxt) else ""
    F_.attrs["target_to"] = str(tgt.index[-1].date())
    return F_


def build_frame(D: pd.DataFrame | None = None, h1: pd.DataFrame | None = None) -> pd.DataFrame:
    """All view columns, labels and label-end times on the euro-era daily frame (1999+). D = daily feature frame
    (featstore.build_daily output); default = the stored feature store."""
    warnings.filterwarnings("ignore")
    if D is None:
        from eurusd.data import load_ohlc
        D = pd.read_parquet(SW.PROC / "features_daily.parquet")
        h1 = load_ohlc("H1").loc["2003":]
        h1 = h1[~h1.index.duplicated(keep="last")]
    D = D.copy()
    D.index = pd.DatetimeIndex(D.index).as_unit("us")
    P = price_frame(D, h1)
    X = SW.prepare(P)
    cd = pd.DatetimeIndex(P["cdate"])
    A = lambda s, lag=1: pd.Series(SW._align_lagged(s, cd, lag).values, index=P.index)  # noqa: E731
    # ---- central banks (decisions are public the same day; one calendar day lag as everywhere)
    fed = fed_target()
    FD = fed_desk(X, P, A)
    for c in FD.columns:
        X[c] = FD[c]
    pol = pd.read_csv(SW.MACRO / "ecb_policy_rates.csv", parse_dates=["date"]).set_index("date")
    X["fed_dir"] = -A(fed).diff(126)
    X["ecb_dir"] = A(pol["main_refinancing_rate"].astype(float)).diff(126)
    # ---- economy
    X["infl_gap"] = X["rd10_lvl"] - X["rrd10_lvl"]            # = 12-month inflation, euro area minus US (60-day lag)
    X["infl_d126"] = X["infl_gap"].diff(126)
    us_u = SW._ms("fred_UNRATE.csv")
    eu = pd.read_csv(SW.MACRO / "ea_unemployment.csv")
    ea_u = pd.Series(eu["unemployment_rate"].values, index=pd.to_datetime(eu["month"] + "-01")).dropna()
    X["labour"] = A(us_u.diff(12), 45) - A(ea_u.diff(12), 75)  # month stamp + 45 / 75 days: after first publication
    X["sahm"] = A(SW._ms("fred_SAHMREALTIME.csv"), 45)
    # ---- feature-store columns (2003+), already lagged there
    j = D.reindex(X.index)
    sur = j[["last_surprise_nfp", "last_surprise_retail", "last_surprise_ism", "last_surprise_gdp"]]
    X["us_surprise"] = -sur.mean(axis=1, skipna=True)
    for c in ("d_spread2y_20", "ret_21d", "cot_d4", "cot_lev_z52", "spx_ret_20", "gold_ret_20"):
        X[c] = j[c]
    X["fv_neg"] = -j["fv_resid_z"]
    X["rev252"] = -X["mom252"]
    X["rev20"] = -j["z20"]
    X["vix_d5_neg"] = -j["d_vix_5"]
    X["usd_neg"] = -j["usd_factor_20"]
    X["scorecard"] = SW.scorecard(SW.votes(X, "h21"))
    X["seas63"], X["seas_month63"] = X["seas42"], X["seas_month42"]
    # ---- raw weak signals for the fold-fitted house score
    S = WS.build_raw_signals(D).reindex(X.index)
    for k in WS.SIGNALS:
        X[f"ws_{k}"] = S[k]
    X["ws_fwd_1d"], X["ws_rv"] = j["fwd_1d"], j["rv_21d_bp"]
    # ---- labels
    lc = np.log(P["close"])
    ct = pd.Series(pd.DatetimeIndex(P["close_time"]), index=P.index)
    for h in HORIZONS:
        X[f"y{h}"] = np.sign(lc.shift(-h) - lc)
        X[f"yend{h}"] = ct.shift(-h)
    X["__ct"] = ct
    out = X[X["__cdate"] >= "1999-01-04"].replace([np.inf, -np.inf], np.nan)
    out.attrs["fed"] = dict(FD.attrs)
    return out


# ============================================================================= one analyst
def _sig(x):
    return 1.0 / (1.0 + np.exp(-x))


def _scale(col: pd.Series, tr: pd.Series, kind: str) -> tuple[np.ndarray, bool]:
    """Standardise `col` with statistics of the training rows `tr`. Returns (z in [-1, 1] with NaN -> 0, usable)."""
    x = tr.dropna()
    if len(x) < MIN_ROWS:
        return np.zeros(len(col)), False
    if kind == "bin":
        return col.fillna(0.0).clip(-1, 1).values, True
    mu = float(x.mean()) if kind == "level" else 0.0
    sd = float(x.std())
    if not sd > 0:
        return np.zeros(len(col)), False
    return (((col - mu) / sd).clip(-2, 2) / 2).fillna(0.0).values, True


def _slope_free(z: np.ndarray, y: np.ndarray, h: int) -> float:
    """Empiricist: logistic slope of either sign; zero unless |t| >= E_MIN_T with the overlap correction sqrt(h)."""
    ok = np.isfinite(z) & np.isfinite(y) & (y != 0) & (z != 0)
    s, yy = z[ok], y[ok]
    if len(s) < MIN_ROWS or s.std() == 0:
        return 0.0
    nll = lambda b: float(np.logaddexp(0.0, -b * s * yy).sum())  # noqa: E731
    r = minimize_scalar(nll, bounds=(-20.0, 20.0), method="bounded")
    b = float(r.x)
    p = _sig(b * s)
    info = float((p * (1 - p) * s * s).sum())
    if info <= 0:
        return 0.0
    se = math.sqrt(h / info)
    return b if abs(b) / se >= E_MIN_T else 0.0


def _slope_prior(z: np.ndarray, y: np.ndarray) -> float:
    ok = (z != 0)
    if ok.sum() < MIN_ROWS:
        return 0.0
    return SW._platt(z[ok], y[ok])


def _fold_columns(X: pd.DataFrame, train_mask: np.ndarray) -> pd.DataFrame:
    """Views that need a model of their own: the 14-signal house score (weights from the training rows only) and
    the three-signal agreement built on its sign."""
    names = list(WS.SIGNALS)
    fr = X[[f"ws_{k}" for k in names] + ["ws_fwd_1d", "ws_rv"]].copy()
    fr.columns = names + ["fwd_1d", "rv_21d_bp"]
    tr = fr[train_mask & fr["fwd_1d"].notna().values & fr["rv_21d_bp"].notna().values]
    out = pd.DataFrame({"@house": np.nan, "@agree": np.nan}, index=X.index)
    if len(tr) < MIN_ROWS:
        return out
    fit, _ = WS.make_fit_predict("tstat", "sign", names)
    m = fit(tr)
    have = fr[names].notna().any(axis=1)
    score = pd.Series(WS._scaler_apply(fr[names], m["st"]).values @ m["w"], index=X.index).where(have)
    out["@house"] = score
    a, b, c = np.sign(X["cot_z52"]), np.sign(X["d_spread2y_20"]), np.sign(score)
    out["@agree"] = pd.Series(np.where((a != 0) & (a == b) & (b == c), a, 0.0), index=X.index).where(score.notna() & a.notna() & b.notna())
    return out


def fit_predict(X: pd.DataFrame, h: int, start: pd.Timestamp, rows: np.ndarray) -> pd.DataFrame:
    """Fit all 100 analysts on rows whose h-session outcome was known before `start`; return P(up) for `rows`
    (boolean mask). NaN = the analyst has no model yet (too little history)."""
    y = X[f"y{h}"].values.astype(float)
    known = (X[f"yend{h}"] < start).values & np.isfinite(y)
    recent = known & (X["__ct"] >= start - pd.DateOffset(years=E_MEMORY_YEARS)).values
    FC = _fold_columns(X, known)
    out = {}
    for v, (_, col, kind, _, _) in VIEWS.items():
        col = col.replace("{h}", str(h))
        s = FC[col] if col.startswith("@") else X[col]
        for t, mask in (("D", known), ("E", recent)):
            z, ok = _scale(s, s[mask], kind)
            if not ok:
                out[f"{v}:{t}"] = np.full(int(rows.sum()), np.nan)
                continue
            z = np.where(s.notna().values, z, 0.0)
            b = _slope_prior(z[mask], y[mask]) if t == "D" else _slope_free(z[mask], y[mask], h)
            p = _sig(b * z[rows])
            out[f"{v}:{t}"] = np.where(s.notna().values[rows], p, np.nan) if (mask & (z != 0)).sum() >= MIN_ROWS else np.full(int(rows.sum()), np.nan)
    return pd.DataFrame(out, index=X.index[rows])[AGENTS]


def walk_forward(X: pd.DataFrame, h: int, years=TEST_YEARS, verbose: bool = True) -> pd.DataFrame:
    parts = []
    for Y in years:
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC")
        rows = (X.index.year == Y)
        if not rows.any():
            continue
        parts.append(fit_predict(X, h, start, rows))
        if verbose:
            print(f"  h={h} year {Y}: {int(parts[-1].notna().any(axis=0).sum())} analysts with a model", flush=True)
    return pd.concat(parts)


# ============================================================================= the vote
def tally(P: pd.DataFrame) -> pd.DataFrame:
    """Counts and majority class per session from the analysts' P(up)."""
    up = (P > 0.5 + EPS).sum(axis=1)
    dn = (P < 0.5 - EPS).sum(axis=1)
    voters = up + dn
    share = (np.maximum(up, dn) / voters.replace(0, np.nan))
    side = np.sign(up - dn).astype(float)
    cls = pd.Series("none", index=P.index, dtype=object)
    for name, lo, hi in CLASSES:
        cls[(share >= lo) & (share < hi) & (voters >= QUORUM) & (side != 0)] = name
    return pd.DataFrame({"up": up, "down": dn, "no_view": P.shape[1] - voters, "voters": voters, "share": share, "side": side,
                         "cls": cls, "mean_p": P.fillna(0.5).mean(axis=1)})


def class_of(share: float, voters: int, side: float) -> str:
    if voters < QUORUM or side == 0 or not share == share:
        return "none"
    return next((n for n, lo, hi in CLASSES if lo <= share < hi), "none")


# ============================================================================= live read-out
def live(refresh: bool = True) -> dict:
    """Today's vote: every analyst fitted on all history whose outcome is known, asked about the latest completed
    session. Returns counts per horizon, the per-analyst table and the historical record of the majority class."""
    from eurusd.exposure import _daily_frame
    from eurusd.live_data import load_h1_live
    notes = []
    if refresh:
        from eurusd.refresh import refresh_macro
        notes = refresh_macro() + [refresh_fed_target()]
    D = _daily_frame(refresh)
    X = build_frame(D, load_h1_live(refresh=False))
    last = np.zeros(len(X), dtype=bool)
    last[-1] = True
    now = X["__ct"].iloc[-1] + pd.Timedelta(seconds=1)
    rec = pd.read_csv(RES / "committee_record.csv") if (RES / "committee_record.csv").exists() else pd.DataFrame()
    fed = X.attrs.get("fed", {})
    fl = X[["fed_latest", "fed_cycle", "fed_surprise", "fed_fx", "fed_priced"]].iloc[-1]
    act = {1.0: "cut", -1.0: "hiked", 0.0: "held"}.get(float(fl["fed_latest"]) if fl["fed_latest"] == fl["fed_latest"] else None, "decision not in the data yet")
    out = {"asof": str(X["__ct"].iloc[-1]), "price": float(X["__close"].iloc[-1]), "refresh": notes, "horizons": {},
           "fed": {"last_meeting": fed.get("last_meeting"), "next_meeting": fed.get("next_meeting"), "action": act, "target_data_to": fed.get("target_to"),
                   "last_move": {1.0: "a cut", -1.0: "a hike"}.get(float(fl["fed_cycle"]) if fl["fed_cycle"] == fl["fed_cycle"] else None, "unknown"),
                   "two_year_on_decision_day_pp": -float(fl["fed_surprise"]) if fl["fed_surprise"] == fl["fed_surprise"] else None,
                   "eurusd_on_decision_day_pct": 100 * float(fl["fed_fx"]) if fl["fed_fx"] == fl["fed_fx"] else None,
                   "two_year_minus_policy_pp": -float(fl["fed_priced"]) if fl["fed_priced"] == fl["fed_priced"] else None}}
    for h in HORIZONS:
        P = fit_predict(X, h, now, last)
        t = tally(P).iloc[0]
        p = P.iloc[0]
        rows = []
        for a in AGENTS:
            v, temp = a.split(":")
            pa = float(p[a]) if p[a] == p[a] else float("nan")
            vote = "up" if pa > 0.5 + EPS else ("down" if pa < 0.5 - EPS else "no view")
            rows.append({"analyst": a, "school": VIEWS[v][0], "temperament": temp, "p_up": pa, "vote": vote, "what": VIEWS[v][4]})
        r = {}
        if len(rec):
            grp = "clear+strong" if t["cls"] in ("clear", "strong") else t["cls"]     # majority size does not sort outcomes: pool
            q = rec[(rec.h == h) & (rec.cls == grp) & (rec.clock == "phase-averaged")]
            r = {e: q[q.era == e].iloc[0].to_dict() for e in q.era.unique()}
        voters_p = p[(p > 0.5 + EPS) | (p < 0.5 - EPS)]
        maj = voters_p[voters_p > 0.5] if t["side"] > 0 else 1 - voters_p[voters_p < 0.5]
        out["horizons"][h] = {"up": int(t["up"]), "down": int(t["down"]), "no_view": int(t["no_view"]), "share": float(t["share"]) if t["share"] == t["share"] else None,
                              "side": float(t["side"]), "cls": t["cls"], "mean_p_up": float(t["mean_p"]),
                              "majority_avg_odds": float(maj.mean()) if len(maj) else None, "record": r, "analysts": rows}
    return out


def format_readout(o: dict, detail: bool = True) -> str:
    L = [f"EUR/USD COMMITTEE ({len(AGENTS)} analysts: 100 + Fed desk of 10) | session close {o['asof'][:16]} UTC | price {o['price']:.4f}"]
    f = o.get("fed") or {}
    if f:
        bits = [f"last meeting {f['last_meeting']}: {f['action']}", f"last rate move was {f['last_move']}"]
        if f.get("two_year_on_decision_day_pp") is not None:
            bits.append(f"2-year yield {f['two_year_on_decision_day_pp']:+.2f} pp on decision day")
        if f.get("eurusd_on_decision_day_pct") is not None:
            bits.append(f"EUR/USD {f['eurusd_on_decision_day_pct']:+.2f} % that day")
        if f.get("two_year_minus_policy_pp") is not None:
            bits.append(f"2-year yield {f['two_year_minus_policy_pp']:+.2f} pp vs policy rate ({'hikes' if f['two_year_minus_policy_pp'] > 0 else 'cuts'} priced)")
        if f.get("next_meeting"):
            bd = int(np.busday_count(pd.Timestamp(o["asof"][:10]).date(), pd.Timestamp(f["next_meeting"]).date()))
            bits.append(f"next meeting {f['next_meeting']} (in about {bd} sessions)")
        L.append("Fed: " + " | ".join(bits))
    names = {21: "1 MONTH", 42: "2 MONTHS", 63: "3 MONTHS"}
    for h, r in o["horizons"].items():
        side = "UP" if r["side"] > 0 else ("DOWN" if r["side"] < 0 else "TIED")
        maj = max(r["up"], r["down"])
        voters = r["up"] + r["down"]
        rec = r["record"].get("2010-26") if r["record"] else None
        has = bool(rec and rec.get("n_indep", 0) and rec["acc"] == rec["acc"])
        if r["cls"] in ("clear", "strong") and has:
            L.append(f"\n{names[h]}: {side}, probability {100 * rec['acc']:.0f} %")
        elif r["cls"] in ("lean", "split") and has:
            L.append(f"\n{names[h]}: NO CALL (majority too thin; it leans {side}, and such leans were right {100 * rec['acc']:.0f} %)")
        else:
            L.append(f"\n{names[h]}: NO CALL (fewer than {QUORUM} analysts have a view, or a tie)")
        L.append(f"  Vote: UP {r['up']} | DOWN {r['down']} | no view {r['no_view']}" + (f" -> {maj} of the {voters} with a view say {side} ({100 * r['share']:.0f} %)" if voters else ""))
        if has:
            L.append(f"  The probability is how often such a majority was right out of sample in 2010-26 ({rec['n_indep']:.0f} independent calls, "
                     f"95 % range {100 * rec['lo']:.0f}-{100 * rec['hi']:.0f} %)"
                     + "".join(f"; {100 * r['record'][e]['acc']:.0f} % in {e}" for e in ("2016-26", "2023-26") if e in r["record"] and r["record"][e]["acc"] == r["record"][e]["acc"]))
        if detail:
            df = pd.DataFrame(r["analysts"])
            by = df.groupby("school")["vote"].value_counts().unstack(fill_value=0).reindex(columns=["up", "down", "no view"], fill_value=0)
            L.append("  By school: " + "; ".join(f"{SCHOOLS[s]} {int(by.loc[s, 'up'])}up/{int(by.loc[s, 'down'])}dn" for s in SCHOOLS if s in by.index))
            fd = df[df.school == "FED"]
            L.append("  Fed desk: " + "; ".join(f"{a.what.split(':')[0].split('(')[0].strip()} [{'theory' if a.temperament == 'D' else '10y'}] {a.vote}" for _, a in fd.iterrows() if a.vote != "no view")
                     if (fd.vote != "no view").any() else "  Fed desk: none of the 10 has a view")
            loud = df[df.vote != "no view"].assign(c=lambda d: (d.p_up - 0.5).abs()).sort_values("c", ascending=False).head(4)
            for _, a in loud.iterrows():
                L.append(f"    {a.vote.upper():4s} {100 * max(a.p_up, 1 - a.p_up):.0f} %  {a.what} [{'theory' if a.temperament == 'D' else 'last 10y'}]")
    return "\n".join(L)


def one_line(o: dict) -> str:
    """Short form for the weekly outlook."""
    parts = []
    for h, r in o["horizons"].items():
        side = "UP" if r["side"] > 0 else ("DOWN" if r["side"] < 0 else "TIED")
        rec = (r["record"] or {}).get("2010-26")
        worth = f", such majorities were right {100 * rec['acc']:.0f} %" if rec and rec.get("n_indep", 0) and rec["acc"] == rec["acc"] else ""
        parts.append(f"{h}d {max(r['up'], r['down'])} of {r['up'] + r['down']} say {side} ({r['cls']}{worth})")
    return f"COMMITTEE ({len(AGENTS)} analysts incl. Fed desk; describes, decides nothing): " + " | ".join(parts)


if __name__ == "__main__":
    o = live(refresh="--no-refresh" not in sys.argv)
    print(format_readout(o))
    if "--json" in sys.argv:
        print(json.dumps(o, indent=1, default=str))
