"""Arm Y ("official_flows"): ACTUAL CROSS-BORDER FLOWS - official custody holdings, the foreign repo pool and swap lines
at the Fed, euro-area balance-of-payments portfolio flows, US TIC flows and the ECB survey consensus - as an EXTRA VOTE for
multi-week EUR/USD direction (round 7).

EVERYTHING IN THIS DOCSTRING (data, lags, priors, the 12 candidates, the controls, the selection rule, the reading of the
success bar) WAS WRITTEN BEFORE ANY RESULT WAS COMPUTED. Only reachability, spans and accounting identities of the raw
files had been looked at.

New raw data (all cached by `fetch_data()`; files are prefixed `official_flows_`, fetched 2026-11-11)
  data/macro/official_flows_fed_h41_memo_weekly.csv   FRED (curl --http1.1, default user-agent), H.4.1 memo items and
        liabilities, Wednesday levels, USD mn: WSEFINTL1 (securities held in custody for foreign official and international
        accounts, total), WMTSECL1 (of which marketable US Treasury securities), WLRRAFOIAL (reverse repurchase agreements
        with foreign official and international accounts = the foreign repo pool), SWPT (central-bank liquidity swaps
        outstanding). FRED carries rows from 2002-12-18 but the two custody series are ZERO until 2007-06-27 (not reported in
        that FRED release): they are set to missing, so custody starts 2007-07-04. H.4.1 is released Thursday 16:30 ET for the
        Wednesday. LAG USED: 7 calendar days (usable from the session closing the following Wednesday). Essentially unrevised.
  data/macro/official_flows_ecb_bop_monthly.csv       ECB Data Portal flow BPS, monthly euro-area balance of payments, EUR mn,
        not seasonally adjusted, reference area I10 (euro area 21, fixed composition, back-cast to 1999-04), counterpart rest of
        the world: key BPS.M.N.I10.W1.S1.S1.T.{entry}.{item}.{category}.{instrument}.{maturity}.EUR._T.{valuation}.N.ALL with
        portfolio investment assets / liabilities / net  A|L|N.FA.P.F._Z (valuation M), equity and fund shares A|L.FA.P.F5._Z,
        debt securities A|L.FA.P.F3.T, direct investment A|L|N.FA.D.F._Z (valuation _X), current-account balance B.CA._Z._Z._Z.
        Stamped with the month END. The monthly release is on about the 20th of month m+2 (7 weeks). LAG USED: 60 calendar days
        after month-end. CURRENT VINTAGE ONLY: the series is revised for years and the flow has no vintages, so every result
        that uses it overstates what was known in real time. Two frozen older vintages are fetched to size that risk:
  data/macro/official_flows_ecb_bop_vintage_i9.csv    the same keys for area I9 (euro area 20, flow BPS; frozen after 2025-12)
  data/macro/official_flows_ecb_bop_vintage_i8.csv    the same keys for area I8 (euro area 19, flow BP6; frozen after 2022-12)
  data/macro/official_flows_us_tic_monthly.csv        ticdata.treasury.gov is not reachable; FRED carries the TIC monthly
        "foreign net transactions of US long-term securities" (USD mn): FORLTTOTALNET69995 (all securities, all countries),
        FORLTTOTALNET99990 (all securities, foreign official), FORLTTREASNET69995 / 99990 (Treasuries). FRED stamps the month
        start; re-stamped to the month END. Released about the 17th of month m+2. LAG USED: 56 calendar days after month-end
        (government shutdowns delayed a few releases beyond that). Current vintage; estimated from positions since 2023.
  data/macro/official_flows_ecb_spf_usd.csv           ECB flow SPF, key SPF.Q.U2.ASSU.USD.{P3M,P6M,P9M,P12M}.Q.AVG: mean
        assumption for USD per EUR. TIME_PERIOD is the TARGET quarter; the survey round S is recovered as target - 0 / 1 / 2 / 3
        quarters for P3M / P6M / P9M / P12M (P3M = the survey's own quarter). Stamped with the first day of the survey quarter;
        the survey is taken in the first weeks of the quarter and published within about six weeks. LAG USED: 50 calendar days
        after the quarter start. Not revised.
  data/macro/official_flows_sources.csv               catalogue (file, source, span, publication, lag, fetch date).
  data/processed/cross/official_flows_panel.parquet   the aligned session panel (oriented signals after lags, stamps, votes).

Signals. Each candidate has an ORIENTED signal x (positive = long EUR/USD); vote = sign(x): +1 long, -1 short, 0 silent.
"z" = (value - trailing mean) / trailing standard deviation of the SAME quantity over the last 3 years of its own
observations (156 weeks, at least 104; 36 months, at least 24), i.e. flows are scaled by their own volatility and judged
against their own recent norm (GDP scaling would leave multi-year one-sided regimes; not used). No parameter is fitted.
 (a) foreign official custody holdings (primary sign: reserve managers accumulating dollar securities = official dollar
     buying => EUR/USD DOWN. The opposite reading - accumulation FOLLOWS dollar weakness because managers lean against it and
     later diversify into euros, so accumulation => EUR/USD up - is the labelled alternative; its accuracy is 100 % minus the
     primary's on the same decisions and is not a candidate.)
   1 cust_d4w     x = -z of the 4-week change of log WSEFINTL1
   2 cust_d13w    x = -z of the 13-week change of log WSEFINTL1
 (b) dollar funding stress (prior: swap-line usage up / foreign repo pool up = dollar shortage => EUR/USD DOWN)
   3 swap_use     x = -(4-week change of SWPT, USD bn) while SWPT >= USD 1 bn ("lines in use"), 0 = silent otherwise
   4 repo_d13w    x = -z of the 13-week change of log WLRRAFOIAL
 (c) euro-area portfolio flows, net inflow = liabilities - assets (prior: net inflows => EUR/USD UP)
   5 pf_net_3m    x = +z of the 3-month sum of net portfolio inflows
   6 pf_net_6m    x = +z of the 6-month sum
   7 pf_net_d3m   x = +(3-month sum minus the previous 3-month sum), EUR bn (the change of the flow)
   8 pf_eq_3m     x = +z of the 3-month sum of net EQUITY inflows (F5 liabilities - assets)
   9 pf_debt_3m   x = +z of the 3-month sum of net DEBT inflows (F3 liabilities - assets)
 (d) basic balance (prior: surplus => appreciation; expected to be slow)
  10 basic_12m    x = +12-month sum of (current account + net direct-investment inflow + net portfolio inflow), EUR bn
 (TIC) dollar-side mirror (prior: foreigners buying US long-term securities = dollar demand => EUR/USD DOWN)
  11 tic_net_3m   x = -z of the 3-month sum of FORLTTOTALNET69995
 (e) survey consensus (prior, per the survey-forecast literature: CONTRARIAN - consensus expects the euro up => short)
  12 spf_contra   x = -log(P12M / P3M) of the same survey round (the consensus' expected 9-month change of USD per EUR)
 Variant count for deflation: 12. No combination vote, no threshold or window search.

The agreement rule (state of the art, reports/arm_selective.md) is rebuilt with the selective helpers through
liquidity_stress.agreement (house score walk-forward, agree3 = sign(cot_z52) = sign(d_spread2y_20) = sign(house score)); the
reconciliation table compares every cell with experiments/results/arms/selective_accuracy_coverage.csv.

Evaluation (round-5 addendum; identical code path to arm Q: liquidity_stress.evaluate), targets = sign of the 21 / 42 /
63-session forward return, weekly grid (every 5th session) and greedy non-overlapping stream, Wilson on non-overlapping counts:
  1 standalone accuracy of each vote, 2010-26 / 2016-26 / 2023-26, with decisions per year.
  2 extra vote: (a) "agree3 AND vote == agreed direction" against agree3 alone; (b) the vote's calls where the three old
    signals do NOT agree; (c) paired differences (weekly circular block bootstrap; iid bootstrap on agree3's own stream).
  3 daily incremental test: the final extra-vote rule as a weekly-tranche 21-session book in
    meta.combine(["weak_signals","regime_trend",ARM],"EW") against the two-way combination; daily P&L correlations.
  4 timing placebo: the vote made 63 and 126 sessions staler, everything recomputed.
Round-7 controls (declared here; controls are not candidates and nothing is selected from them):
  5 correlation of every x with cot_z52, d_spread2y_20, the house score and EUR/USD's trailing 21- and 63-session return
    (and, for reference, with the forward 21- / 63-session return), 2010-26.
  6 orthogonalised votes: for test year Y, OLS of x on the regressors over sessions that closed before Y-01-01 (at least 250
    rows where x is active, else the year is silent); the vote is the sign of x - (R - mean_train(R)) beta, i.e. only the
    co-movement is removed, the signal keeps its own level. Two regressor sets: SPOT (ret_21d, ret_63d) and ALL (those two +
    cot_z52, d_spread2y_20, house score extended back to 2006 with the same walk-forward). Standalone and extra-vote tables.
  7 lead or follow, at the native frequency and WITHOUT publication lags (economic timing, descriptive, whole sample):
    correlation of the monthly (4-weekly, quarterly) flow with the EUR/USD return of the same period and of the three
    periods before and after it.
  8 revision risk: the six balance-of-payments signals rebuilt from the frozen I9 and I8 vintages; share of months on which
    the vote differs from the current vintage, and the size of the revision of the monthly net portfolio flow.
  9 replication (round 6): the five dollar-side votes (1-4, 11) say "dollar down / up", so the identical votes are scored on
    the equal-weight basket of eight non-euro currencies against the dollar (Fed H.10 noon rates: GBP, JPY, CHF, AUD, CAD,
    NZD, SEK, NOK; entry at the noon AFTER the session close), standalone, 21 / 42 / 63 sessions.
Leak checks: shuffled labels, votes made staler by 1 / 5 / 21 sessions, look-ahead controls (-21 / -63), a planted label,
  the lag audit (age of every observation at the close that uses it).

SELECTION RULE (declared by the lead in round 5, unchanged): final = the candidate whose EXTRA-VOTE rule has the highest lower
  95 % Wilson bound of the 2010-2015 non-overlapping 21-session accuracy, among candidates with at least 6 non-overlapping
  21-session decisions a year in 2010-2015. If no candidate has 6 a year there is NO eligible final; the stream written to
  disk is then the candidate with the highest lower bound regardless of count, flagged as failing the rule.
SUCCESS BAR (round 5), same reading as arm Q, fixed before results: gain = non-overlapping accuracy of the extra-vote rule
  minus that of agree3, in points. Needed: gain >= 3 at 21 AND 42 sessions in 2010-26 AND 2016-26; at least 6 decisions a
  year on the 21-session non-overlapping stream; 2023-26 accuracy not below agree3 at 21 and 42; and the placebo gain at +63
  and at +126 sessions at most half of the real gain at 21 and 42 sessions (2010-26).
"""
from __future__ import annotations

import io
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.arms import liquidity_stress as LS  # noqa: E402
from eurusd.arms import selective as SEL  # noqa: E402
from eurusd.featstore import _align_lagged  # noqa: E402
from eurusd.wf import report  # noqa: E402

MACRO = ROOT / "data" / "macro"
CROSS = ROOT / "data" / "processed" / "cross"
RES = ROOT / "experiments" / "results" / "arms"
ARM = "official_flows"
PRE = "official_flows_"
N_ARMS = 12
HZ = (21, 42, 63)
PLACEBO = (63, 126)
P3 = ("2010-26", "2016-26", "2023-26")
CANDS = ("cust_d4w", "cust_d13w", "swap_use", "repo_d13w", "pf_net_3m", "pf_net_6m", "pf_net_d3m", "pf_eq_3m", "pf_debt_3m",
         "basic_12m", "tic_net_3m", "spf_contra")
DOLLAR_SIDE = ("cust_d4w", "cust_d13w", "swap_use", "repo_d13w", "tic_net_3m")
BOP_CANDS = ("pf_net_3m", "pf_net_6m", "pf_net_d3m", "pf_eq_3m", "pf_debt_3m", "basic_12m")
LAGS = {"h41_weekly": 7, "bop_monthly": 60, "tic_monthly": 56, "spf_quarterly": 50}
CAND_LAG = {**{c: "h41_weekly" for c in CANDS[:4]}, **{c: "bop_monthly" for c in BOP_CANDS}, "tic_net_3m": "tic_monthly",
            "spf_contra": "spf_quarterly"}
SWAP_IN_USE_MN = 1000.0
ZW_WEEKS, ZW_WEEKS_MIN, ZW_MONTHS, ZW_MONTHS_MIN = 156, 104, 36, 24

FRED_H41 = ("WSEFINTL1", "WMTSECL1", "WLRRAFOIAL", "SWPT")
FRED_TIC = ("FORLTTOTALNET69995", "FORLTTOTALNET99990", "FORLTTREASNET69995", "FORLTTREASNET99990")
ECB_URL = "https://data-api.ecb.europa.eu/service/data/{flow}/{key}?format=csvdata"
BOP_KEY = "M.N.{area}.W1.S1.S1.T.A+L+N+B.FA+CA.P+D+_Z.F+F5+F3+_Z._Z+T.EUR._T.M+_X.N"
BOP_COLS = {"A.FA.P.F._Z": "pf_a", "L.FA.P.F._Z": "pf_l", "N.FA.P.F._Z": "pf_n", "A.FA.P.F5._Z": "pf_eq_a", "L.FA.P.F5._Z": "pf_eq_l",
            "A.FA.P.F3.T": "pf_debt_a", "L.FA.P.F3.T": "pf_debt_l", "A.FA.D.F._Z": "di_a", "L.FA.D.F._Z": "di_l", "N.FA.D.F._Z": "di_n",
            "B.CA._Z._Z._Z": "ca"}
BOP_VINTAGES = {"monthly": ("BPS", "I10", ".ALL"), "vintage_i9": ("BPS", "I9", ".ALL"), "vintage_i8": ("BP6", "I8", "")}
SPF_KEY = "Q.U2.ASSU.USD.P3M+P6M+P9M+P12M.Q.AVG"


# ================================================================ fetch (cached)
def _bop(flow: str, area: str, tail: str) -> pd.DataFrame:
    d = pd.read_csv(io.StringIO(LS._curl(ECB_URL.format(flow=flow, key=BOP_KEY.format(area=area) + tail))))
    d["k"] = d["KEY"].str.split(".").str[8:13].str.join(".")
    d = d[d["k"].isin(BOP_COLS)]
    w = d.pivot_table(index="TIME_PERIOD", columns="k", values="OBS_VALUE", aggfunc="first").rename(columns=BOP_COLS)
    w.index = pd.to_datetime(w.index, format="%Y-%m") + pd.offsets.MonthEnd(0)
    return w[list(BOP_COLS.values())].sort_index().rename_axis("date").rename_axis(None, axis=1)


def _spf() -> pd.DataFrame:
    d = pd.read_csv(io.StringIO(LS._curl(ECB_URL.format(flow="SPF", key=SPF_KEY))))
    p = d.pivot_table(index="TIME_PERIOD", columns="FCT_HORIZON", values="OBS_VALUE", aggfunc="first")
    p.index = pd.PeriodIndex(p.index.str.replace("-", ""), freq="Q")
    p = p.sort_index()
    full = pd.period_range(p.index[0], p.index[-1], freq="Q")
    p = p.reindex(full)
    S = pd.DataFrame({"p3m": p["P3M"], "p6m": p["P6M"].shift(-1), "p9m": p["P9M"].shift(-2), "p12m": p["P12M"].shift(-3)}).dropna(subset=["p3m", "p12m"])
    S.insert(0, "survey_round", S.index.astype(str))
    S.index = S.index.to_timestamp(how="start")
    return S.rename_axis("date")


def fetch_data(force: bool = False, verbose: bool = True) -> pd.DataFrame:
    """Downloads every new series once and writes the prefixed CSVs; later calls only read the catalogue."""
    cat_p = MACRO / f"{PRE}sources.csv"
    files = ["fed_h41_memo_weekly", "ecb_bop_monthly", "ecb_bop_vintage_i9", "ecb_bop_vintage_i8", "us_tic_monthly", "ecb_spf_usd"]
    if not force and cat_p.exists() and all((MACRO / f"{PRE}{f}.csv").exists() for f in files):
        return pd.read_csv(cat_p)
    say = print if verbose else (lambda *a, **k: None)
    h = pd.DataFrame({s.lower(): LS._fred(s) for s in FRED_H41}).rename_axis("date")
    for c in ("wsefintl1", "wmtsecl1"):                 # FRED carries zeros before the memo item was reported
        h.loc[h[c] <= 0, c] = np.nan
    h.to_csv(MACRO / f"{PRE}fed_h41_memo_weekly.csv"); say("  Fed H.4.1 memo", h.index[0].date(), h.index[-1].date(), len(h))
    bop = {}
    for name, (flow, area, tail) in BOP_VINTAGES.items():
        bop[name] = _bop(flow, area, tail)
        bop[name].to_csv(MACRO / f"{PRE}ecb_bop_{name}.csv"); say("  ECB BoP", name, bop[name].index[0].date(), bop[name].index[-1].date(), len(bop[name]))
    tic = pd.DataFrame({s.lower(): LS._fred(s) for s in FRED_TIC})
    tic.index = tic.index + pd.offsets.MonthEnd(0)
    tic.rename_axis("date").to_csv(MACRO / f"{PRE}us_tic_monthly.csv"); say("  TIC (FRED)", tic.index[0].date(), tic.index[-1].date(), len(tic))
    spf = _spf()
    spf.to_csv(MACRO / f"{PRE}ecb_spf_usd.csv"); say("  ECB SPF", spf["survey_round"].iloc[0], spf["survey_round"].iloc[-1], len(spf))
    today = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")
    bk = "ECB Data Portal {f}.M.N.{a}.W1.S1.S1.T.{{A,L,N}}.FA.{{P,D}}.{{F,F5,F3}}... + B.CA (11 keys, EUR mn, NSA)"
    rows = [
        ("fed_h41_memo_weekly", "FRED WSEFINTL1, WMTSECL1, WLRRAFOIAL, SWPT (curl --http1.1); custody zero before 2007-07-04 set to missing",
         h["wsefintl1"].dropna().index, "Wednesday level, released Thursday 16:30 ET", "7 calendar days"),
        ("ecb_bop_monthly", bk.format(f="BPS", a="I10") + ", CURRENT VINTAGE", bop["monthly"].index, "month m released ~20th of m+2", "60 calendar days after month-end"),
        ("ecb_bop_vintage_i9", bk.format(f="BPS", a="I9") + ", frozen after 2025-12 (revision check only)", bop["vintage_i9"].index, "-", "not used in signals"),
        ("ecb_bop_vintage_i8", bk.format(f="BP6", a="I8") + ", frozen after 2022-12 (revision check only)", bop["vintage_i8"].index, "-", "not used in signals"),
        ("us_tic_monthly", "FRED FORLTTOTALNET69995, FORLTTOTALNET99990, FORLTTREASNET69995, FORLTTREASNET99990 (TIC; ticdata.treasury.gov blocked)",
         tic.index, "month m released ~17th of m+2", "56 calendar days after month-end"),
        ("ecb_spf_usd", "ECB Data Portal SPF.Q.U2.ASSU.USD.{P3M,P6M,P9M,P12M}.Q.AVG, target quarters mapped back to survey rounds", spf.index,
         "survey in the first weeks of the quarter, published within ~6 weeks", "50 calendar days after quarter start"),
    ]
    cat = pd.DataFrame([{"file": f"data/macro/{PRE}{f}.csv", "source": s, "first": i.min().date(), "last": i.max().date(), "rows": len(i),
                         "publication": p, "lag_used": lag, "fetched": today} for f, s, i, p, lag in rows])
    cat.to_csv(cat_p, index=False)
    return cat


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(MACRO / f"{PRE}{name}.csv", parse_dates=["date"]).set_index("date").sort_index()


# ================================================================ oriented signals on their native stamps
def _z(s: pd.Series, win: int, minp: int) -> pd.Series:
    return (s - s.rolling(win, min_periods=minp).mean()) / s.rolling(win, min_periods=minp).std()


def bop_flows(bop: pd.DataFrame) -> pd.DataFrame:
    """Monthly net INFLOWS (liabilities - assets), EUR mn."""
    f = pd.DataFrame(index=bop.index)
    f["pf_net"] = bop["pf_l"] - bop["pf_a"]
    f["pf_eq"] = bop["pf_eq_l"] - bop["pf_eq_a"]
    f["pf_debt"] = bop["pf_debt_l"] - bop["pf_debt_a"]
    f["di_net"] = bop["di_l"] - bop["di_a"]
    f["basic"] = bop["ca"] + f["di_net"] + f["pf_net"]
    return f


def bop_signals(bop: pd.DataFrame) -> dict[str, pd.Series]:
    f = bop_flows(bop)
    s3 = f["pf_net"].rolling(3).sum()
    return {"pf_net_3m": _z(s3, ZW_MONTHS, ZW_MONTHS_MIN),
            "pf_net_6m": _z(f["pf_net"].rolling(6).sum(), ZW_MONTHS, ZW_MONTHS_MIN),
            "pf_net_d3m": (s3 - s3.shift(3)) / 1000.0,
            "pf_eq_3m": _z(f["pf_eq"].rolling(3).sum(), ZW_MONTHS, ZW_MONTHS_MIN),
            "pf_debt_3m": _z(f["pf_debt"].rolling(3).sum(), ZW_MONTHS, ZW_MONTHS_MIN),
            "basic_12m": f["basic"].rolling(12).sum() / 1000.0}


def native_signals() -> dict[str, pd.Series]:
    """The 12 oriented signals (positive = long EUR/USD) on the stamps of their own observations."""
    h, bop, tic, spf = _read("fed_h41_memo_weekly"), _read("ecb_bop_monthly"), _read("us_tic_monthly"), _read("ecb_spf_usd")
    lc, lr = np.log(h["wsefintl1"]), np.log(h["wlrrafoial"])
    d4 = h["swpt"].diff(4)
    X = {"cust_d4w": -_z(lc.diff(4), ZW_WEEKS, ZW_WEEKS_MIN),
         "cust_d13w": -_z(lc.diff(13), ZW_WEEKS, ZW_WEEKS_MIN),
         "swap_use": (-(d4 / 1000.0)).where(h["swpt"] >= SWAP_IN_USE_MN, 0.0).where(d4.notna()),
         "repo_d13w": -_z(lr.diff(13), ZW_WEEKS, ZW_WEEKS_MIN)}
    X.update(bop_signals(bop))
    X["tic_net_3m"] = -_z(tic["forlttotalnet69995"].rolling(3).sum(), ZW_MONTHS, ZW_MONTHS_MIN)
    X["spf_contra"] = -np.log(spf["p12m"] / spf["p3m"]) * 100.0
    return {c: X[c].dropna() for c in CANDS}


def build_panel(D: pd.DataFrame, write: bool = True) -> pd.DataFrame:
    """Session-aligned oriented signals (after the publication lags), the stamp of every observation used, and the votes."""
    fetch_data(verbose=False)
    cdate = pd.DatetimeIndex(pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None))
    P = pd.DataFrame(index=D.index)
    P["cdate"] = cdate
    X = native_signals()
    for c in CANDS:
        s, lag = X[c], LAGS[CAND_LAG[c]]
        v = _align_lagged(s, cdate, lag).values
        pos = np.searchsorted(s.index.values, (cdate - pd.Timedelta(days=lag)).values, side="right") - 1
        P[f"stamp_{c}"] = np.where(pos >= 0, s.index.values[np.maximum(pos, 0)].astype("datetime64[ns]"), np.datetime64("NaT", "ns"))
        assert np.allclose(np.where(pos >= 0, s.values[np.maximum(pos, 0)], np.nan), v, equal_nan=True), c
        P[f"x_{c}"] = v
    for c in CANDS:
        P[f"vote_{c}"] = np.sign(P[f"x_{c}"]).fillna(0.0)
    if write:
        CROSS.mkdir(parents=True, exist_ok=True)
        P.to_parquet(CROSS / f"{PRE}panel.parquet")
    return P


def lag_audit(P: pd.DataFrame) -> pd.DataFrame:
    rows = []
    x = P[P.index.year >= 2010]
    for c in CANDS:
        lag = LAGS[CAND_LAG[c]]
        age = (x["cdate"] - x[f"stamp_{c}"]).dt.days.dropna()
        rows.append({"signal": c, "lag_required_days": lag, "min_age_days": int(age.min()), "median_age_days": float(age.median()),
                     "max_age_days": int(age.max()), "first_session_with_value": str(P.index[P[f"x_{c}"].notna()][0].date()),
                     "ok": bool(age.min() >= lag)})
    return pd.DataFrame(rows)


# ================================================================ round-7 controls
def orthogonalise(Xs: pd.DataFrame, R: pd.DataFrame, year: np.ndarray, years=SEL.YEARS, min_rows: int = 250) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Walk-forward residual of each oriented signal on R. For test year Y the slope comes from sessions of earlier years
    only; the residual is x - (R - mean_train(R)) beta (the signal keeps its own level). Returns (residuals, slopes log)."""
    out = pd.DataFrame(np.nan, index=Xs.index, columns=Xs.columns)
    Rv = R.values
    okR = np.isfinite(Rv).all(axis=1)
    log = []
    for c in Xs.columns:
        x = Xs[c].values
        act = np.isfinite(x) & (x != 0) & okR
        for Y in years:
            tr = act & (year < Y)
            te = act & (year == Y)
            if tr.sum() < min_rows or te.sum() == 0:
                continue
            mu = Rv[tr].mean(axis=0)
            A = np.column_stack([np.ones(tr.sum()), Rv[tr] - mu])
            beta, *_ = np.linalg.lstsq(A, x[tr], rcond=None)
            fit = A @ beta
            r2 = 1.0 - float(((x[tr] - fit) ** 2).sum() / max(((x[tr] - x[tr].mean()) ** 2).sum(), 1e-12))
            out.loc[out.index[te], c] = x[te] - (Rv[te] - mu) @ beta[1:]
            log.append({"signal": c, "year": Y, "n_train": int(tr.sum()), "r2_train": r2, **{f"b_{k}": float(b) for k, b in zip(R.columns, beta[1:])}})
    return out, pd.DataFrame(log)


def correlations(ctx, T, P: pd.DataFrame, hs: np.ndarray, base: np.ndarray, agree: np.ndarray, sg: np.ndarray) -> pd.DataFrame:
    """What each oriented signal is correlated with, sessions 2010-26 on which the vote is active."""
    D = ctx.D
    cols = {"cot_z52": D["cot_z52"].values, "d_spread2y_20": D["d_spread2y_20"].values, "house_score": hs, "past_ret21": D["ret_21d"].values,
            "past_ret63": D["ret_63d"].values, "fwd_ret21": T["sign21"].long, "fwd_ret63": T["sign63"].long}
    k = (D.index.year >= 2010) & base
    rows = []
    for c in CANDS:
        x = P[f"x_{c}"].values
        m = k & np.isfinite(x) & (x != 0)
        r = {"signal": c, "active_share": float(m.sum() / k.sum()), "share_long": float((x[m] > 0).mean()),
             "flips_per_year": float((np.diff(np.sign(np.nan_to_num(x[k]))) != 0).sum() / 16.85)}
        for n, y in cols.items():
            q = m & np.isfinite(y)
            r[f"corr_{n}"] = float(np.corrcoef(x[q], y[q])[0, 1]) if q.sum() > 50 else np.nan
        for name, regs in (("r2_spot", ("past_ret21", "past_ret63")), ("r2_all5", ("past_ret21", "past_ret63", "cot_z52", "d_spread2y_20", "house_score"))):
            Rm = np.column_stack([cols[g] for g in regs])
            q = m & np.isfinite(Rm).all(axis=1)
            if q.sum() > 50:
                A = np.column_stack([np.ones(q.sum()), Rm[q]])
                b, *_ = np.linalg.lstsq(A, x[q], rcond=None)
                r[name] = 1.0 - float(((x[q] - A @ b) ** 2).sum() / ((x[q] - x[q].mean()) ** 2).sum())
        v = np.sign(x)
        r["same_sign_as_cot"] = float((v[m] == np.sign(cols["cot_z52"][m])).mean())
        r["same_sign_as_spread_trend"] = float((v[m] == np.sign(cols["d_spread2y_20"][m])).mean())
        r["same_sign_as_house"] = float((v[m] == sg[m]).mean())
        r["same_sign_as_agree3_when_agreed"] = float((v[m & agree] == sg[m & agree]).mean()) if (m & agree).sum() else np.nan
        r["same_sign_as_past_ret63"] = float((v[m] == np.sign(cols["past_ret63"][m])).mean())
        rows.append(r)
    return pd.DataFrame(rows)


def lead_lag(D: pd.DataFrame, lags=(-3, -2, -1, 0, 1, 2, 3)) -> pd.DataFrame:
    """Native-frequency cross-correlation of each flow with the EUR/USD log return, NO publication lag (economic timing).
    Column k<0: the exchange-rate return of k periods BEFORE the flow period (the flow follows the price); k=0 the same
    period; k>0 the return of later periods (the flow leads). Whole available sample; descriptive only."""
    cd = pd.DatetimeIndex(pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None))
    px = pd.Series(np.log(D["close"].values), index=cd)
    px = px[~px.index.duplicated(keep="last")]
    h, bop, tic, spf = _read("fed_h41_memo_weekly"), _read("ecb_bop_monthly"), _read("us_tic_monthly"), _read("ecb_spf_usd")
    f = bop_flows(bop)
    pm = px.resample("ME").last()
    rm = pm.diff() * 100
    series = []
    for name, s in (("EA net portfolio inflow (monthly)", f["pf_net"]), ("EA net equity inflow (monthly)", f["pf_eq"]), ("EA net debt inflow (monthly)", f["pf_debt"]),
                    ("EA basic balance (monthly)", f["basic"]), ("EA current account (monthly)", bop["ca"]),
                    ("TIC foreign net purchases of US LT securities (monthly)", tic["forlttotalnet69995"]),
                    ("TIC, foreign official only (monthly)", tic["forlttotalnet99990"])):
        series.append((name, "month", s, rm))
    # 4-week blocks ending on H.4.1 Wednesdays
    w = h.iloc[::-1].iloc[::4].iloc[::-1]
    pw = px.reindex(px.index.union(w.index)).sort_index().ffill().reindex(w.index)
    rw = pw.diff() * 100
    for name, s in (("custody holdings, total (4-week log change)", np.log(w["wsefintl1"]).diff()), ("custody, Treasuries only (4-week log change)", np.log(w["wmtsecl1"]).diff()),
                    ("foreign repo pool (4-week log change)", np.log(w["wlrrafoial"]).diff()), ("swap lines (4-week change, USD bn)", w["swpt"].diff() / 1000.0)):
        series.append((name, "4 weeks", s, rw))
    pq = px.resample("QS").first()
    rq = (pq.shift(-1) - pq) * 100                     # return of the quarter that starts on the stamp
    series.append(("SPF expected 9-month change (quarterly survey)", "quarter", np.log(spf["p12m"] / spf["p3m"]) * 100, rq))
    rows = []
    for name, per, s, r in series:
        x = pd.concat([s.rename("f"), r.rename("r")], axis=1, sort=True).dropna(subset=["f"])
        x = x[x.index >= "2003-01-01"]
        row = {"flow": name, "period": per, "first": str(x.index[0].date()), "n": int(x["r"].notna().sum())}
        for k in lags:
            q = pd.concat([x["f"], r.reindex(x.index.union(r.index)).sort_index().shift(-k).reindex(x.index).rename("r")], axis=1).dropna()
            row[f"k={k:+d}"] = float(q.corr().iloc[0, 1]) if len(q) > 20 else np.nan
        rows.append(row)
    return pd.DataFrame(rows)


def vintage_check() -> pd.DataFrame:
    """The six balance-of-payments signals rebuilt from the frozen I9 / I8 vintages against the current I10 vintage."""
    cur = _read("ecb_bop_monthly")
    sc, fc = bop_signals(cur), bop_flows(cur)
    rows = []
    for name in ("vintage_i9", "vintage_i8"):
        old = _read(f"ecb_bop_{name}")
        so, fo = bop_signals(old), bop_flows(old)
        j = pd.concat([fc["pf_net"].rename("cur"), fo["pf_net"].rename("old")], axis=1, sort=True).dropna()
        j = j[j.index >= "2008-01-01"]
        last12 = j.iloc[-12:]
        base = {"vintage": name, "span": f"{old.index[0].date()} .. {old.index[-1].date()}", "months_compared": len(j),
                "sd_monthly_net_pf_bn": float(j["cur"].std() / 1000), "rms_diff_all_bn": float(np.sqrt(((j["cur"] - j["old"]) ** 2).mean()) / 1000),
                "rms_diff_last12_bn": float(np.sqrt(((last12["cur"] - last12["old"]) ** 2).mean()) / 1000),
                "corr_monthly": float(j.corr().iloc[0, 1]), "corr_last12": float(last12.corr().iloc[0, 1])}
        for c in BOP_CANDS:
            q = pd.concat([sc[c].rename("cur"), so[c].rename("old")], axis=1, sort=True).dropna()
            q = q[q.index >= "2010-01-01"]
            rows.append({**base, "signal": c, "months": len(q), "vote_differs_share": float((np.sign(q["cur"]) != np.sign(q["old"])).mean()),
                         "vote_differs_last12": float((np.sign(q["cur"]) != np.sign(q["old"])).iloc[-12:].mean()), "corr_signal": float(q.corr().iloc[0, 1])})
    return pd.DataFrame(rows)


MONTHLY = BOP_CANDS + ("tic_net_3m",)


def zero_lag_votes(D: pd.DataFrame) -> pd.DataFrame:
    """CONTROL ADDED AFTER THE FIRST RUN (not tradable, not a candidate): the seven monthly votes as if month m's flow were
    known at the close of its last day (publication lag 0 instead of 60 / 56 days). It separates 'the flow is published too
    late' from 'the flow does not lead'."""
    cdate = pd.DatetimeIndex(pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None))
    X = native_signals()
    return pd.DataFrame({c: np.sign(_align_lagged(X[c], cdate, 0).values) for c in MONTHLY}, index=D.index).fillna(0.0)


def replication(ctx, V: pd.DataFrame, base: np.ndarray) -> pd.DataFrame:
    """The dollar-side votes scored on the equal-weight basket of eight non-euro currencies against the dollar."""
    p = CROSS / "relative_value_h10_g10.parquet"
    if not p.exists():
        return pd.DataFrame()
    G = pd.read_parquet(p).drop(columns=["eur"]).dropna(how="all")
    b = G.diff().mean(axis=1).fillna(0.0).cumsum()               # EW log basket, USD per foreign currency
    D = ctx.D
    cd = pd.DatetimeIndex(pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None))
    pos = np.searchsorted(b.index.values, cd.values, side="right")          # first noon fixing AFTER the closing date
    px = np.where(pos < len(b), b.values[np.minimum(pos, len(b) - 1)], np.nan)
    n = len(D)
    Tb = {}
    for h in HZ:
        f = np.full(n, np.nan); f[:n - h] = (px[h:] - px[:n - h]) * 1e4
        end = np.full(n, SEL.NAT, dtype=np.int64); end[:n - h] = ctx.ct[h:]
        Tb[f"sign{h}"] = SEL.Target(f"sign{h}", "sign", h, 0.0, np.where(np.isfinite(f), (f > 0).astype(float), np.nan), f, -f,
                                    np.where(np.isfinite(f), float(h), np.nan), end)
    rows = []
    for c in DOLLAR_SIDE:
        v = V[c].fillna(0.0).values
        for tgt, TT in (("non-EUR basket vs USD", Tb),):
            s = pd.DataFrame(LS.rule_rows(ctx, TT, base & (v != 0), LS._clean_dirs(v)))
            s.insert(0, "candidate", c); s.insert(0, "table", tgt); rows.append(s)
    return pd.concat(rows, ignore_index=True)


# ================================================================ run
def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Rebuilds the agreement rule, evaluates the 12 votes, applies the declared selection rule and writes the deliverables.
    Returns (daily position Series of the final extra-vote rule, protocol report DataFrame)."""
    say = print if verbose else (lambda *a, **k: None)
    fetch_data(verbose=verbose)
    D = SEL.load_data()
    ctx = SEL.make_ctx(D, cost_pips)
    T = SEL.build_targets(D)
    P = build_panel(D, write=write)
    V = P[[f"vote_{c}" for c in CANDS]].rename(columns=lambda c: c[5:])
    Xs = P[[f"x_{c}" for c in CANDS]].rename(columns=lambda c: c[2:])
    hs, sg, base, agree = LS.agreement(ctx)
    keep: dict = {}
    ST, VT, PT = LS.evaluate(ctx, T, V, hs, sg, base, agree, cands=CANDS, placebo=PLACEBO, keep=keep)
    # reconciliation with the selective arm's stored table (all four horizons)
    R = pd.DataFrame(LS.rule_rows(ctx, T, agree, LS._clean_dirs(sg), horizons=SEL.HORIZONS))
    refp = RES / "selective_accuracy_coverage.csv"
    if refp.exists():
        C = pd.read_csv(refp)
        C = C[(C.model == "B:agree3") & (C.rule == "filter")][["h", "mode", "period", "n", "accuracy", "dec_per_year"]]
        R = R.merge(C.rename(columns={"n": "n_selective", "accuracy": "accuracy_selective", "dec_per_year": "dec_per_year_selective"}), on=["h", "mode", "period"], how="left")
        R["match"] = (R["n"] == R["n_selective"]) & ((R["accuracy"] - R["accuracy_selective"]).abs() < 1e-9)
    SELT, final, eligible, status = LS.select_final(VT)
    BAR, checks = LS.bar_check(VT, final)
    say(f"final = {final} ({status})")
    # ---- round-7 controls
    hs_ext = SEL.house_score_wf(ctx, years=list(range(2006, 2027)))
    assert np.allclose(hs_ext[np.isfinite(hs)], hs[np.isfinite(hs)])
    Rspot = pd.DataFrame({"ret_21d": D["ret_21d"].values, "ret_63d": D["ret_63d"].values}, index=D.index)
    Rall = Rspot.assign(cot_z52=D["cot_z52"].values, d_spread2y_20=D["d_spread2y_20"].values, house_score=hs_ext)
    OST, OVT, ologs = [], [], []
    for tag, Rm in (("orth_spot", Rspot), ("orth_all5", Rall)):
        E, lg = orthogonalise(Xs, Rm, ctx.year)
        Vo = np.sign(E).fillna(0.0)
        s, v, _ = LS.evaluate(ctx, T, Vo, hs, sg, base, agree, cands=CANDS, placebo=(), paired=False)
        s["table"] = tag; OST.append(s)
        v = v[v.table == "extra_vote"].copy(); v["table"] = f"{tag}_extra_vote"; OVT.append(v)
        lg.insert(0, "control", tag); ologs.append(lg)
        P[[f"{tag}_{c}" for c in CANDS]] = E.values
    ORTH = pd.concat(OST + OVT, ignore_index=True)
    zs, zv, _ = LS.evaluate(ctx, T, zero_lag_votes(D), hs, sg, base, agree, cands=MONTHLY, placebo=(), paired=False)
    zs["table"] = "zero_lag"
    zv = zv[zv.table == "extra_vote"].copy(); zv["table"] = "zero_lag_extra_vote"
    ZERO = pd.concat([zs, zv], ignore_index=True)
    CORR = correlations(ctx, T, P, hs, base, agree, sg)
    # ---- protocol tables: weekly-tranche 21-session book of every candidate's extra-vote rule, and of agree3
    reps, streams = [], {}
    for name in ("agree3",) + CANDS:
        pnl = SEL.book_time_exit(ctx, keep[name][(21, "weekly")], 21, cost_pips)
        streams[name] = pnl[pnl.index.year >= 2010]
        tb = report(streams[name], periods_per_year=252, name=ARM, n_arms=N_ARMS)
        tb.insert(1, "variant", "agree3_baseline" if name == "agree3" else f"extra_vote_{name}")
        tb["final"] = name == final; tb["kind"] = "baseline" if name == "agree3" else "candidate"; tb["cost_pips"] = cost_pips
        reps.append(tb)
    ctx6 = SEL.make_ctx(D, 0.6)
    p6 = SEL.book_time_exit(ctx6, keep[final][(21, "weekly")], 21, 0.6)
    tb = report(p6[p6.index.year >= 2010], periods_per_year=252, name=ARM, n_arms=N_ARMS)
    tb.insert(1, "variant", f"extra_vote_{final}_cost0.6"); tb["final"] = False; tb["kind"] = "cost_sensitivity"; tb["cost_pips"] = 0.6
    reps.append(tb)
    rep = pd.concat(reps, ignore_index=True)
    daily = streams[final].copy()
    daily["fwd_bp"] = D["fwd_1d"].reindex(daily.index)
    daily = daily[["pos", "fwd_bp", "net_bp"]]
    res = {"ctx": ctx, "T": T, "D": D, "panel": P, "votes_raw": V, "x": Xs, "hs": hs, "sg": sg, "base": base, "agree": agree, "standalone": ST,
           "votes": VT, "paired": PT, "reconcile": R, "selection": SELT, "final": final, "eligible": eligible, "status": status, "bar": BAR,
           "checks": checks, "report": rep, "streams": streams, "keep": keep, "daily": daily, "lag_audit": lag_audit(P), "cost_pips": cost_pips,
           "zero_lag": ZERO, "orth": ORTH, "orth_log": pd.concat(ologs, ignore_index=True), "corr": CORR, "lead_lag": lead_lag(D), "vintage": vintage_check(),
           "replication": replication(ctx, V, base)}
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        P.to_parquet(CROSS / f"{PRE}panel.parquet")
        daily.to_parquet(RES / f"{ARM}_positions.parquet")
        keep[final][(21, "weekly")][["pos", "fwd_bp", "net_bp", "gross_bp", "hit", "hold"]].loc["2010":].to_parquet(RES / f"{ARM}_decisions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        pd.concat([VT, PT], ignore_index=True).to_csv(RES / f"{ARM}_votes.csv", index=False)
        ST.to_csv(RES / f"{ARM}_standalone.csv", index=False)
        ORTH.to_csv(RES / f"{ARM}_orthogonalised.csv", index=False)
        ZERO.to_csv(RES / f"{ARM}_zero_lag_control.csv", index=False)
        res["orth_log"].to_csv(RES / f"{ARM}_orthogonalised_slopes.csv", index=False)
        CORR.to_csv(RES / f"{ARM}_correlations.csv", index=False)
        res["lead_lag"].to_csv(RES / f"{ARM}_lead_lag.csv", index=False)
        res["vintage"].to_csv(RES / f"{ARM}_vintage_check.csv", index=False)
        res["replication"].to_csv(RES / f"{ARM}_replication.csv", index=False)
        R.to_csv(RES / f"{ARM}_reconciliation.csv", index=False)
        SELT.to_csv(RES / f"{ARM}_selection.csv", index=False)
        BAR.to_csv(RES / f"{ARM}_bar.csv", index=False)
    run.last = res
    return daily["pos"], rep


def bar_all(VT: pd.DataFrame) -> pd.DataFrame:
    """The success bar evaluated for every candidate (information only; the final is fixed by the declared rule)."""
    rows = []
    for c in CANDS:
        B, ch = LS.bar_check(VT, c)
        g = B.set_index(["h", "period"])
        rows.append({"candidate": c, "gain21_2010": g.loc[(21, "2010-26"), "gain_pts"], "gain42_2010": g.loc[(42, "2010-26"), "gain_pts"],
                     "gain21_2016": g.loc[(21, "2016-26"), "gain_pts"], "gain42_2016": g.loc[(42, "2016-26"), "gain_pts"],
                     "gain21_2023": g.loc[(21, "2023-26"), "gain_pts"], "gain42_2023": g.loc[(42, "2023-26"), "gain_pts"],
                     "per_year_21_2010": g.loc[(21, "2010-26"), "extra_per_year"], "placebo63_gain21": g.loc[(21, "2010-26"), "placebo63_gain_pts"],
                     "placebo126_gain21": g.loc[(21, "2010-26"), "placebo126_gain_pts"], "placebo63_gain42": g.loc[(42, "2010-26"), "placebo63_gain_pts"],
                     "placebo126_gain42": g.loc[(42, "2010-26"), "placebo126_gain_pts"],
                     **{k: v for k, v in ch.items()}})
    return pd.DataFrame(rows)


# ================================================================ incremental value and leak checks
def incremental() -> pd.DataFrame:
    """EW(weak_signals, regime_trend) against EW(weak_signals, regime_trend, this arm's daily book), round-3 addendum."""
    from eurusd.arms.meta import combine, load_arm_daily, report_combo
    two, _ = combine(["weak_signals", "regime_trend"], "EW")
    three, _ = combine(["weak_signals", "regime_trend", ARM], "EW")
    out = pd.concat([report_combo(two, "weak_signals+regime_trend", 2), report_combo(three, f"+{ARM}", 3)], ignore_index=True)
    s = load_arm_daily(ARM)
    for o in ("weak_signals", "regime_trend", "selective_daily"):
        x = pd.concat([s, load_arm_daily(o)], axis=1).dropna()
        x = x[x.index.year >= 2010]
        out[f"corr_{o}"] = float(x.corr().iloc[0, 1]) if len(x) > 10 else np.nan
    out.to_csv(RES / f"{ARM}_incremental.csv", index=False)
    return out


def leak_checks(res: dict, seed: int = 0) -> pd.DataFrame:
    """(1) labels shuffled (targets and the 1-session return the house weights are fitted on, three permutations);
    (2) the votes made staler by 1 / 5 / 21 sessions and, as a control that the harness WOULD expose a look-ahead, taken
    from 21 / 63 sessions in the future; a planted label; (3) the anatomy of the votes is the correlation table."""
    ctx, T, V, final = res["ctx"], res["T"], res["votes_raw"], res["final"]
    hs, sg, base, agree = res["hs"], res["sg"], res["base"], res["agree"]
    rows = []

    def ev(label, cx, Tx, Vx, a4):
        ST, VT, _ = LS.evaluate(cx, Tx, Vx, *a4, cands=CANDS, placebo=(), paired=False)
        for tab, X in (("standalone", ST), ("extra_vote", VT), ("agree3", VT)):
            x = X[(X.table == tab) & (X["mode"] == "nonoverlap") & X.period.isin(P3) & X.h.isin((21, 42))]
            for _, q in x.iterrows():
                rows.append({"check": label, "table": tab, "candidate": q["candidate"], "h": q["h"], "period": q["period"], "n": q["n"],
                             "accuracy": q.get("accuracy"), "lo": q.get("lo"), "hi": q.get("hi"), "chance_acc": q.get("chance_acc")})

    ev("baseline", ctx, T, V, (hs, sg, base, agree))
    rng = np.random.default_rng(seed)
    for s in range(3):
        perm = rng.permutation(len(ctx.D))
        Ts = {k: (t.permuted(perm) if k.startswith("sign") else t) for k, t in T.items()}
        cx = ctx.with_fwd1(ctx.fwd1[perm])
        ev(f"shuffled_labels_{s}", cx, Ts, V, LS.agreement(cx))
    for lag in (1, 5, 21):
        ev(f"vote_stale_plus{lag}", ctx, T, V.shift(lag), (hs, sg, base, agree))
    for lag in (21, 63):
        ev(f"lookahead_control_minus{lag}", ctx, T, V.shift(-lag), (hs, sg, base, agree))
    Vp = V.copy()
    for c in CANDS:
        Vp[c] = np.sign(T["sign21"].long)
    ev("positive_control_planted_label21", ctx, T, Vp, (hs, sg, base, agree))
    L = pd.DataFrame(rows)
    L.to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
    res["leak"] = L
    return L


# ================================================================ report
PRIORS = [
    ("cust_d4w", "a", "-", "z of the 4-week change of log custody holdings (WSEFINTL1)", "FRED H.4.1", "7 d"),
    ("cust_d13w", "a", "-", "z of the 13-week change of log custody holdings", "FRED H.4.1", "7 d"),
    ("swap_use", "b", "-", "4-week change of swap lines outstanding (SWPT) while SWPT >= USD 1 bn; silent otherwise", "FRED H.4.1", "7 d"),
    ("repo_d13w", "b", "-", "z of the 13-week change of log foreign repo pool (WLRRAFOIAL)", "FRED H.4.1", "7 d"),
    ("pf_net_3m", "c", "+", "z of the 3-month sum of euro-area net portfolio inflows (liabilities - assets)", "ECB BPS", "60 d after month-end"),
    ("pf_net_6m", "c", "+", "z of the 6-month sum", "ECB BPS", "60 d"),
    ("pf_net_d3m", "c", "+", "3-month sum minus the previous 3-month sum", "ECB BPS", "60 d"),
    ("pf_eq_3m", "c", "+", "z of the 3-month sum of net equity inflows", "ECB BPS", "60 d"),
    ("pf_debt_3m", "c", "+", "z of the 3-month sum of net debt inflows", "ECB BPS", "60 d"),
    ("basic_12m", "d", "+", "12-month sum of current account + net direct + net portfolio inflows (level against zero)", "ECB BPS", "60 d"),
    ("tic_net_3m", "TIC", "-", "z of the 3-month sum of foreign net purchases of US long-term securities", "FRED (TIC)", "56 d after month-end"),
    ("spf_contra", "e", "- (contrarian)", "log(P12M / P3M): the SPF consensus' expected 9-month change of USD per EUR", "ECB SPF", "50 d after quarter start"),
]


def _piv(X: pd.DataFrame, table: str, mode: str, periods=P3, hs=HZ, ci: bool = False, per_year: bool = True, rows=None) -> str:
    return LS._piv(X, table, mode, periods=periods, hs=hs, ci=ci, per_year=per_year, rows=rows or (("agree3",) + CANDS))


def _num(X: pd.DataFrame, table: str, mode: str, value: str, periods=P3, hs=HZ, fmt="{:+.1f}") -> str:
    x = X[(X.table == table) & (X["mode"] == mode) & X.period.isin(periods) & X.h.isin(hs)].copy()
    x["col"] = x["period"] + " / " + x["h"].astype(str) + "s"
    order = [f"{p} / {h}s" for p in periods for h in hs]
    t = x.pivot_table(index="candidate", columns="col", values=value, aggfunc="first")[order].reindex([c for c in CANDS if c in set(x.candidate)])
    return t.map(lambda v: fmt.format(v) if np.isfinite(v) else "-").rename_axis(None, axis=1).reset_index().to_markdown(index=False)


def _side(ST: pd.DataFrame, tables: dict, mode: str, period: str, hs=HZ, ci: bool = False) -> str:
    """One row per candidate, columns = h x table label."""
    x = ST[ST.table.isin(tables) & (ST["mode"] == mode) & (ST.period == period) & ST.h.isin(hs)].copy()
    x["cell"] = x.apply(lambda q: LS._c(q, ci, False), axis=1)
    x["col"] = x["h"].astype(str) + "s " + x["table"].map(tables)
    t = x.pivot_table(index="candidate", columns="col", values="cell", aggfunc="first")
    t = t[[f"{h}s {k}" for h in hs for k in tables.values()]].reindex(list(CANDS))
    return t.rename_axis(None, axis=1).reset_index().to_markdown(index=False)


VERDICT_MD = """
## Verdict (run of 2026-11-11; every number below is regenerated in the tables that follow)
**The round-5 success bar is NOT met, by any of the 12 candidates. Cross-border flow data - official custody holdings, the
foreign repo pool, swap lines, euro-area portfolio and basic-balance flows, US TIC flows - and the survey consensus carry no
usable information about EUR/USD direction at 1-3 months, on their own or as an extra vote. Where a flow is related to the
exchange rate at all, it FOLLOWS it.**

1. **What was obtainable.** Everything in the brief, from official hosts. Fed H.4.1 memo items from FRED (custody is zero on
   FRED before 2007-07-04, so custody signals start in 2009 after the 2-year norm window; repo pool and swap lines from
   2002-12). ECB balance of payments, all asset / liability / equity / debt / direct-investment / current-account keys for the
   current area I10, 1999-04 to 2026-08, plus two frozen vintages (I9, I8) used to size revisions. TIC: the Treasury host is
   blocked, but FRED carries the monthly TIC net-transactions series (1985-01 to 2026-08), so TIC was included. ECB SPF USD/EUR
   assumptions, 100 survey rounds 2002Q1-2026Q4, mapped from target quarter back to survey round.
2. **Reconciliation: exact.** The agreement rule rebuilt here matches `selective_accuracy_coverage.csv` in all 32 cells
   (non-overlapping 56 / 59 / 61 / 72 % at 10 / 21 / 42 / 63 sessions, n = 291 / 156 / 89 / 61, 2010-26).
3. **Standalone: a coin.** Over 2010-26 the twelve votes are right 45-51 % of the time at 21 sessions, 40-55 % at 42 and 42-57 %
   at 63 on non-overlapping decisions (n = 208 / 104 / 69 for the eleven always-on votes; `swap_use` 47 / 49 / 55 % on 64 / 41 /
   33), and 46-52 / 44-52 / 42-52 % on weekly decisions. No 95 % interval excludes 50 % on the right side. The best cells belong to
   the slowest vote, `basic_12m`: 55 / 57 % at 42 / 63 sessions (59 / 66 % since 2016), weekly 51 / 50 %, and its 63- and
   126-session-stale versions score the same 53-54 / 57 % - a regime bet (the basic balance changed sign 0.8 times a year), not
   information. The one interval on the WRONG side is `cust_d4w` at 42 sessions, 40 % [31-50] (weekly 52 %).
   * (a) Custody: primary sign 51 / 40 / 42 % (4 weeks) and 48 / 43 / 43 % (13 weeks); the labelled alternative reading
     ("accumulation follows dollar weakness") is the mirror, 49 / 60 / 58 % and 52 / 57 / 57 %, not confirmed on weekly decisions
     (48 / 48 / 52 %). Neither reading is a signal.
   * (b) Funding stress: `swap_use` speaks on 24 % of sessions (mostly 2010-13 and 2020-21) and is right 47 / 49 / 55 %; the foreign repo
     pool 45 / 54 / 52 %.
   * (c) Euro-area portfolio flows: net 49 / 51 / 45 % (3 months) and 46 / 51 / 51 % (6 months), change 51 / 48 / 45 %, equity
     45 / 46 / 45 %, debt 50 / 52 / 49 %. "Net inflows => euro up" is not visible at any horizon.
   * (TIC) 51 / 44 / 48 %. (e) SPF consensus, contrarian: 47 / 52 / 43 %.
4. **Lead or follow (section 5): they follow, or do nothing.** At the native frequency and without publication lags, custody
   holdings rise in the four weeks AFTER and during a rise of EUR/USD (correlation +0.21 with the previous four weeks' return,
   +0.14 with the same four weeks, n = 252) and are unrelated to the next three periods (+0.02 / -0.02 / +0.04): reserve managers
   lean against dollar weakness, the alternative reading, and it leads nothing. TIC foreign purchases of US securities likewise
   follow a fall of the dollar (+0.15 / +0.10 / +0.11 with the three previous months, n = 283) and do not lead (0.00 / -0.08 /
   0.00). Euro-area net portfolio inflows are slightly NEGATIVELY related to the previous and the same month's return (-0.14 /
   -0.09) and unrelated to later months (+0.07 / +0.05 / -0.01). Swap-line use rises while the euro is falling (-0.13 for the
   same and the two previous periods, -0.17 for the next one; almost all of it is 2008-09 - in 2010-26 it is -0.12 for the same
   period and -0.07 for the next, and the vote is a coin).  The custody pattern holds in both halves (2010-26: +0.20 / +0.15). In the session
   panel the oriented custody signals correlate -0.25 / -0.31 with the trailing 63-session return and at most -0.10 with the
   forward return; R-squared on trailing spot returns is at most 0.10 and on spot plus the three agreement inputs at most 0.12
   (0.25 for `swap_use`). **Orthogonalising changes nothing: 44-53 / 45-57 / 41-55 % after removing the trailing 21- and
   63-session returns, 45-53 / 44-56 / 44-57 % after removing those and the agreement inputs.** So the flows are mostly NOT a
   restatement of the price move - they are independent of the old signals and simply uninformative about the next 1-3 months.
   A zero-publication-lag control (added after the first run, not tradable) gives 42-56 % for the monthly flows: the 7-week
   publication lag is not what kills them.
5. **SPF consensus (the 'is the consensus contrarian?' control): no.** The consensus expected change is negatively related
   to the previous quarters' return (forecasters expect partial mean reversion) and POSITIVELY related to the return of the
   survey quarter and the next three (+0.21 / +0.24 / +0.16 / +0.15, n = 95, about two standard errors each); in 2010-26 it
   correlates +0.13 / +0.21 with the forward 21- / 63-session return. So the contrarian prior is rejected; if anything the
   consensus is weakly right in SIZE. As a sign vote it is nothing either way (following it: 53 / 48 / 57 %, intervals include
   50 %, weekly 52 / 49 / 50 %), it changes sign 0.65 times a year, and its stale versions score the same. Not proposed.
6. **Extra vote: lower accuracy on a smaller sample.** Final by the declared rule = `pf_net_d3m` (2010-15: 52 % [38-66], n=44,
   7.3 a year, against 62 % for the agreement rule alone; only three candidates reach 6 decisions a year in the selection
   window and none of the three beats the agreement rule there). Agreement rule AND the vote, non-overlapping: **55 % (n=95, 5.7 a year)
   against 59 % (n=156, 9.3 a year) at 21 sessions; 57 % (n=61, 3.7 a year) against 61 % (n=89) at 42; 65 % (n=48) against 72 %
   (n=61) at 63.** Since 2016: 57 against 57 % and 53 against 59 %. Since 2023: 50 against 60 % (n=20 v 35) and 50 against 45 %
   (n=12 v 20). Gain -4.2 / -3.3 points (2010-26) and -0.4 / -6.0 (2016-26) where +3 / +3 is required; 5.7 decisions a year where
   6 are required; worse in 2023-26 at 21 sessions. Paired difference on the weekly grid: +0.4 points [-5.8, +6.4] at 21
   sessions, -5.0 [-12.1, +1.3] at 42; on the agreement rule's own stream the decisions the vote confirms are right 59 / 55 %
   and the ones it rejects 59 / 68 %.
   Across all 12 candidates the 21-session gain in 2010-26 is negative for every one (-10.2 to -0.3 points). Positive
   42-session gains (`swap_use` +12.1 on 22 decisions, 1.3 a year; `spf_contra` +8.1; custody and repo pool +3.9 to +4.0) come
   with a negative 21-session gain, and no candidate has more than 6.3 decisions a year. None passes; the orthogonalised votes do
   not pass either.
7. **Coverage extension: no.** Where the three old signals do not agree the votes are right 47-55 % at 21 sessions, 43-53 %
   at 42 and 31-59 % at 63 (2010-26, n = 170 / 93 / 64); every interval includes 50 % except `cust_d4w` at 63 sessions on the
   wrong side.
8. **Timing placebo: nothing to lose.** For the final the 63- and 126-session-stale votes give -6.0 / -4.2 and -7.4 / -4.2 points
   against -4.2 / -3.3 live. Among the standalone votes the stale versions score as high as the live ones (36-65 % against
   40-57 %).
9. **Daily incremental test: worse.** The final rule's weekly-tranche book has net Sharpe 0.45 / 0.26 / -0.22 (2010-26 /
   2016-26 / 2023-26, 1.2 pips) against 0.52 / 0.51 / 0.43 for the agreement rule's own book and is 0.77 correlated with it
   (0.30 with `weak_signals`, 0.46 with `regime_trend`). EW(weak_signals, regime_trend, this arm) = 0.562 / 0.589 / 0.209
   against 0.563 / 0.636 / 0.356 two-way. Round-3 bar failed as well (standalone 2016-26 below 0.3, 2023-26 negative,
   three-way below two-way).
10. **Replication (dollar-side votes on eight non-euro currencies against the dollar): nothing.** 41-54 / 38-56 / 41-55 % at
    21 / 42 / 63 sessions (2010-26). `tic_net_3m` is on the wrong side there (45 / 38 [30-48] / 41 %; weekly 48 / 45 / 47 %):
    one cell in ninety, and turning the sign round would be a post-hoc choice; not proposed.
11. **Revision risk.** The balance-of-payments results use the current vintage. Against the two frozen vintages the votes differ
    on 1-4 % of months (I9, 2013-25) and 5-14 % (I8, 2010-22), and on up to 25 % of the LAST twelve months of a frozen vintage:
    the most recent year is revised by about a third of a standard deviation of the monthly flow (RMS 20-23 against 57 EUR bn).
    A real-time version could only be noisier than what is tested here, and what is tested here shows nothing.
12. **What to keep.** Nothing for the product. The files are clean, lagged and cached; custody holdings, the repo pool, swap
    lines and the SPF consensus path can serve as context panels in the brief (who is accumulating dollars, what the consensus
    expects), never as votes.
"""


def write_report(res: dict | None = None, path: Path | None = None) -> None:
    if res is None:
        run(verbose=False)
        res = run.last
    if "leak" not in res:
        leak_checks(res)
    inc = incremental()
    ST, VT, PT, final = res["standalone"], res["votes"], res["paired"], res["final"]
    OR = res["orth"]
    cat = pd.read_csv(MACRO / f"{PRE}sources.csv")
    L = []
    A = L.append
    A("# Arm Y: actual cross-border flows as an extra vote (`official_flows`)\n")
    A("Code `src/eurusd/arms/official_flows.py` (`run(cost_pips=1.2)`, `fetch_data()` cached, `leak_checks()`, `incremental()`; "
      "`python -m eurusd.arms.official_flows` reproduces everything in a few minutes). Results in `experiments/results/arms/`: "
      "`official_flows_positions.parquet` (daily weekly-tranche book of the final extra-vote rule: `pos`, `fwd_bp`, `net_bp`), "
      "`official_flows_decisions.parquet`, `official_flows_report.csv` (protocol table of all 12 extra-vote books, the agreement-rule baseline and the "
      "0.6-pip run; `variant`, `final`), `official_flows_votes.csv` (agreement rule, extra vote, calls outside agreement, placebos, paired differences), "
      "`official_flows_standalone.csv`, `official_flows_orthogonalised.csv` (+ `_slopes`), `official_flows_correlations.csv`, `official_flows_lead_lag.csv`, "
      "`official_flows_vintage_check.csv`, `official_flows_replication.csv`, `official_flows_reconciliation.csv`, `official_flows_selection.csv`, "
      "`official_flows_bar.csv`, `official_flows_bar_all.csv`, `official_flows_incremental.csv`, `official_flows_leakchecks.csv`. "
      "Aligned panel: `data/processed/cross/official_flows_panel.parquet`.\n")
    A("Data, lags, sign priors, the 12 candidates, the controls, the selection rule and the reading of the success bar are in the module docstring and "
      "were written before the first result. One thing was added afterwards and is marked as such: the zero-publication-lag control (section 5e). "
      "It is not a candidate and changes no selection.")
    A(VERDICT_MD)
    A("## 1. New data: keys, span, publication lag used, revisions\n")
    A(cat[["file", "source", "first", "last", "rows", "publication", "lag_used", "fetched"]].to_markdown(index=False))
    A("\nLag audit (age in calendar days, at each session's closing date, of the observation actually used; sessions 2010-26). Alignment is "
      "`featstore._align_lagged(series, closing_date, lag)`: last observation stamped <= closing date - lag.\n")
    A(res["lag_audit"].to_markdown(index=False))
    A("\nRevision risk of the balance-of-payments signals: the six signals rebuilt from the two frozen vintages the ECB still serves (I9 = euro area 20, "
      "last updated for 2025-12; I8 = euro area 19, flow BP6, last updated for 2022-12) against the current I10 vintage. The differences mix genuine "
      "revisions with the change of composition (Croatia, Bulgaria). `rms_diff` = root-mean-square difference of the MONTHLY net portfolio flow "
      "(EUR bn; its standard deviation is in `sd_monthly_net_pf_bn`); `vote_differs` = share of months (from 2010) on which the vote has the other sign.\n")
    A(res["vintage"].round(3).to_markdown(index=False))
    A("\n## 2. The 12 candidate votes and their priors (fixed before results)\n")
    A("Vote = sign of the oriented signal: +1 long EUR/USD, -1 short, 0 silent. z = against the trailing 3-year mean and standard deviation of the "
      "same quantity (156 weeks / 36 months).\n")
    A(pd.DataFrame(PRIORS, columns=["vote", "family", "prior sign", "raw quantity", "data", "lag"]).to_markdown(index=False))
    A("\nCustody (a): the primary sign is 'accumulation = official dollar buying = EUR/USD down'. The labelled alternative ('accumulation follows dollar "
      "weakness, managers lean against it') is the mirror image: its accuracy is 100 minus the primary's.\n")
    A("\n## 3. Reconciliation of the agreement rule\n")
    R = res["reconcile"]
    Rr = R[R.period.isin(P3)].copy()
    Rr["here"] = Rr.apply(lambda q: f"{100 * q['accuracy']:.1f} n={int(q['n'])}", axis=1)
    Rr["selective"] = Rr.apply(lambda q: f"{100 * q['accuracy_selective']:.1f} n={int(q['n_selective'])}", axis=1)
    A(f"Rebuilt with the selective helpers (through `liquidity_stress.agreement / rule_rows`). Cells compared with `selective_accuracy_coverage.csv`: "
      f"{len(R)}; exact matches (n and accuracy): {int(R['match'].sum())}.\n")
    A(Rr[["h", "mode", "period", "here", "selective", "match"]].to_markdown(index=False))
    A("\n## 4. Standalone accuracy of each vote (direction = the vote; % right, 95 % Wilson interval, decisions, decisions per year)\n")
    for per in P3:
        A(f"\nNon-overlapping decisions, {per}:\n")
        A(_piv(ST, "standalone", "nonoverlap", periods=(per,), ci=True, rows=CANDS))
    A("\nWeekly decisions (overlapping holds; no interval shown - the effective sample is the non-overlapping count above):\n")
    A(_piv(ST, "standalone", "weekly", per_year=False, rows=CANDS))
    A("\nTiming placebo of the standalone votes, non-overlapping, 2010-26 (the vote made 63 / 126 sessions staler):\n")
    A(_side(ST, {"standalone": "live", "placebo+63": "placebo+63", "placebo+126": "placebo+126"}, "nonoverlap", "2010-26"))
    A("\n## 5. Round-7 controls: is it new information, or the exchange rate restated?\n")
    A("### 5a. Correlation of each oriented signal with the agreement inputs and with EUR/USD's own trailing and forward return (active sessions, 2010-26)\n")
    C = res["corr"]
    A(C[["signal", "active_share", "share_long", "flips_per_year", "corr_cot_z52", "corr_d_spread2y_20", "corr_house_score", "corr_past_ret21", "corr_past_ret63",
         "r2_spot", "r2_all5", "corr_fwd_ret21", "corr_fwd_ret63"]].round(2).to_markdown(index=False))
    A("\nShare of active sessions on which the vote has the same sign as ...\n")
    A(C[["signal", "same_sign_as_cot", "same_sign_as_spread_trend", "same_sign_as_house", "same_sign_as_agree3_when_agreed", "same_sign_as_past_ret63"]].round(2).to_markdown(index=False))
    A("\n### 5b. Lead or follow? Native-frequency correlation of each flow with the EUR/USD return, no publication lag\n")
    A("`k<0`: return of the k-th period BEFORE the flow period (the flow follows the exchange rate); `k=0`: same period; `k>0`: later periods (the flow "
      "leads). Flows are raw (inflows positive; SPF = expected change of USD per EUR), sample 2003-2026, descriptive. A correlation of 0.12 is about "
      "two standard errors at n = 280 and 0.11 at n = 320 (4-week blocks: 0.13 at n = 250; quarterly: 0.21 at n = 90).\n")
    A(res["lead_lag"].round(2).to_markdown(index=False))
    A("\n### 5c. Standalone accuracy after orthogonalising (walk-forward) to the trailing 21- and 63-session return (`spot`) and to those plus cot_z52, "
      "d_spread2y_20 and the house score (`all5`)\n")
    for per in ("2010-26", "2016-26"):
        A(f"\nNon-overlapping, {per} (% right, decisions):\n")
        A(_side(pd.concat([ST[ST.table == "standalone"], OR[OR.table.isin(["orth_spot", "orth_all5"])]]),
                {"standalone": "raw", "orth_spot": "orth spot", "orth_all5": "orth all5"}, "nonoverlap", per))
    A("\nWeekly decisions, 2010-26:\n")
    A(_side(pd.concat([ST[ST.table == "standalone"], OR[OR.table.isin(["orth_spot", "orth_all5"])]]),
            {"standalone": "raw", "orth_spot": "orth spot", "orth_all5": "orth all5"}, "weekly", "2010-26"))
    A("\n### 5d. Replication: the dollar-side votes on the equal-weight basket of eight non-euro currencies against the dollar\n")
    RP = res["replication"]
    if len(RP):
        A("Non-overlapping (% right, 95 % Wilson interval, decisions); weekly below.\n")
        A(LS._piv(RP, "non-EUR basket vs USD", "nonoverlap", ci=True, per_year=False, rows=DOLLAR_SIDE))
        A("")
        A(LS._piv(RP, "non-EUR basket vs USD", "weekly", per_year=False, rows=DOLLAR_SIDE))
    A("\n### 5e. Zero-publication-lag control (ADDED AFTER THE FIRST RUN; not tradable, not a candidate)\n")
    A("The seven monthly votes as if month m's flow were known at the close of its last day (lag 0 instead of 60 / 56 days). Standalone, "
      "non-overlapping (% right, decisions), with the tradable (lagged) vote next to it, then the gain as an extra vote in points:\n")
    Z = res["zero_lag"]
    zz = pd.concat([ST[(ST.table == "standalone") & ST.candidate.isin(MONTHLY)], Z[Z.table == "zero_lag"]])
    for per in ("2010-26", "2016-26"):
        x = zz[(zz["mode"] == "nonoverlap") & (zz.period == per)].copy()
        x["cell"] = x.apply(lambda q: LS._c(q, False, False), axis=1)
        x["col"] = x["h"].astype(str) + "s " + x["table"].map({"standalone": "published", "zero_lag": "zero lag"})
        t = x.pivot_table(index="candidate", columns="col", values="cell", aggfunc="first")
        A(f"\n{per}:\n")
        A(t[[f"{h}s {k}" for h in HZ for k in ("published", "zero lag")]].reindex(list(MONTHLY)).rename_axis(None, axis=1).reset_index().to_markdown(index=False))
    A("\nExtra-vote gain over the agreement rule with the zero-lag votes (points, non-overlapping):\n")
    A(_num(Z, "zero_lag_extra_vote", "nonoverlap", "gain_pts"))
    A("\n## 6. As an extra vote\n")
    A("### 6a. Agreement rule AND the vote agrees, against the agreement rule alone\n")
    A("Non-overlapping decisions (% right, decisions, decisions per year). First row = the agreement rule alone.\n")
    X = VT[VT.table.isin(["agree3", "extra_vote"])].assign(table="x")
    A(_piv(X, "x", "nonoverlap"))
    A("\nThe same with 95 % Wilson intervals, 2010-26 only:\n")
    A(_piv(X, "x", "nonoverlap", periods=("2010-26",), ci=True))
    A("\nGain in accuracy points over the agreement rule, non-overlapping (bar: >= +3 at 21s and 42s in 2010-26 and 2016-26):\n")
    A(_num(VT, "extra_vote", "nonoverlap", "gain_pts"))
    A("\nWeekly decisions:\n")
    A(_piv(X, "x", "weekly"))
    A("\nThe extra vote with the ORTHOGONALISED signals (gain in points over the agreement rule, non-overlapping):\n")
    for tag in ("orth_spot", "orth_all5"):
        A(f"\n`{tag}`:\n")
        A(_num(OR, f"{tag}_extra_vote", "nonoverlap", "gain_pts"))
    A("\n### 6b. Coverage extension: the vote's own calls on sessions where the three old signals do NOT agree\n")
    A("Non-overlapping, with 95 % Wilson intervals, 2010-26, then all periods without intervals:\n")
    A(_piv(VT, "disagree_calls", "nonoverlap", periods=("2010-26",), ci=True, rows=CANDS))
    A("")
    A(_piv(VT, "disagree_calls", "nonoverlap", rows=CANDS))
    A("\n### 6c. Paired differences\n")
    A("`paired_weekly`: accuracy(extra-vote rule) - accuracy(agreement rule) on the same weekly grid, circular block bootstrap (block 2h/5 weeks, "
      "2000 draws). `paired_nonoverlap_on_agree3_stream`: on the agreement rule's own non-overlapping decisions, accuracy of those the vote "
      "confirms minus all (iid bootstrap over decisions). `acc_dropped` = accuracy of the agreement-rule decisions the vote rejects.\n")
    pp = PT[PT.period.isin(("2010-26", "2016-26")) & PT.h.isin((21, 42))].copy()
    for c in ("acc_agree", "acc_extra", "acc_dropped", "diff", "diff_lo", "diff_hi"):
        pp[c] = (100 * pp[c]).round(1)
    pp["p_diff_le0"] = pp["p_diff_le0"].round(2)
    cols = ["candidate", "h", "period", "n_agree", "n_extra", "acc_agree", "acc_extra", "acc_dropped", "diff", "diff_lo", "diff_hi", "p_diff_le0"]
    for tab in ("paired_weekly", "paired_nonoverlap_on_agree3_stream"):
        A(f"\n{tab} (points):\n")
        A(pp[pp.table == tab][cols].to_markdown(index=False))
    A("\n## 7. Selection and the success bar\n")
    A(f"Declared rule: highest lower Wilson bound of the 2010-15 non-overlapping 21-session accuracy of the extra-vote rule among candidates with "
      f">= {LS.MIN_DEC_PER_YEAR:.0f} such decisions a year. Result: **`{final}`** ({res['status']}).\n")
    S = res["selection"].copy()
    for c in ("accuracy", "lo", "hi", "agree_accuracy"):
        S[c] = (100 * S[c]).round(1)
    A(S.round(2).to_markdown(index=False))
    A(f"\nThe bar for `{final}` (non-overlapping decisions; accuracies in %, gains in points):\n")
    A(res["bar"].round(1).to_markdown(index=False))
    A("")
    for k, v in res["checks"].items():
        A(f"* {k}: **{'yes' if v else 'NO'}**")
    BA = bar_all(VT)
    BA.to_csv(RES / f"{ARM}_bar_all.csv", index=False)
    A("\nThe same bar for every candidate (information only; gains in points, non-overlapping):\n")
    A(BA[["candidate", "gain21_2010", "gain42_2010", "gain21_2016", "gain42_2016", "gain21_2023", "gain42_2023", "per_year_21_2010", "placebo63_gain21",
          "placebo126_gain21", "placebo63_gain42", "placebo126_gain42", "BAR MET"]].round(1).to_markdown(index=False))
    A(f"\nDecisions of `{final}` (extra-vote rule, weekly, 21-session hold) by year:\n")
    A(LS.by_year(res["keep"][final][(21, "weekly")]).round(2).to_markdown(index=False))
    hr = VT[(VT.candidate == final) & (VT.table == "extra_vote") & (VT.h == 21) & VT.period.isin(P3)].copy()
    hr["right_sign_%"] = (100 * hr["accuracy"]).round(1); hr["net_win_%"] = (100 * hr["win_rate_net"]).round(1)
    A("\nHit rates of the final rule at 21 sessions (round-4 format: share with the correct sign before costs, share with positive net P&L):\n")
    A(hr[["mode", "period", "n", "dec_per_year", "right_sign_%", "net_win_%", "gross_bp", "net_bp", "share_long", "chance_acc"]].round(2).to_markdown(index=False))
    A("\n## 8. Timing placebo (the vote made 63 and 126 sessions staler), extra-vote rule, non-overlapping\n")
    for k in PLACEBO:
        A(f"\nPlacebo +{k} sessions (% right, decisions, per year):\n")
        A(_piv(VT, f"placebo+{k}", "nonoverlap", rows=CANDS))
        A(f"\nGain over the agreement rule with the +{k} placebo (points):\n")
        A(_num(VT, f"placebo+{k}", "nonoverlap", "gain_pts"))
    A("\n## 9. Daily-stream incremental test (round-3 addendum) and protocol table\n")
    rep = res["report"]
    ag = rep[rep.period.isin(["2010-2026", "2016-2026", "2023-2026", "2010-2015"])]
    t = ag.pivot_table(index="variant", columns="period", values="sharpe")[["2010-2026", "2016-2026", "2023-2026", "2010-2015"]].round(2)
    tt = ag.pivot_table(index="variant", columns="period", values="t")[["2010-2026"]].round(2).rename(columns={"2010-2026": "t 2010-2026"})
    A("Net Sharpe at 1.2 pips of the weekly-tranche 21-session book of each extra-vote rule (the agreement rule's own book first):\n")
    A(t.join(tt).reindex(["agree3_baseline"] + [f"extra_vote_{c}" for c in CANDS] + [f"extra_vote_{final}_cost0.6"]).reset_index().to_markdown(index=False))
    f = rep[rep.variant == f"extra_vote_{final}"]
    A(f"\nFinal book `extra_vote_{final}` per year (deflated-Sharpe p for 12 candidates: {float(f[f.period == '2010-2026']['deflated_sharpe_p'].iloc[0]):.2f}):\n")
    A(f[["period", "n", "sharpe", "t", "mean_bp", "sum_bp", "active_frac"]].round(2).to_markdown(index=False))
    A("\nCombination test, `meta.combine(..., 'EW')`:\n")
    A(inc[inc.period.isin(["2010-2026", "2016-2026", "2023-2026"])][["combo", "period", "sharpe", "t", "mean_bp"]].round(3).to_markdown(index=False))
    A(f"\nDaily P&L correlation of the final book, 2010-26: `weak_signals` {inc['corr_weak_signals'].iloc[0]:.2f}, `regime_trend` {inc['corr_regime_trend'].iloc[0]:.2f}, "
      f"agreement-rule book (`selective_daily`) {inc['corr_selective_daily'].iloc[0]:.2f}.\n")
    A("## 10. Leak checks\n")
    A("No model is fitted in this arm (fixed sign rules; trailing statistics use observations stamped up to each observation's own stamp; the house "
      "score inside the agreement rule is the selective arm's walk-forward fit; the orthogonalisation slopes come from earlier years only).\n")
    lk = res["leak"]
    x = lk[(lk.period == "2010-26") & (((lk.table == "agree3") & (lk.candidate == "agree3")) | (lk.candidate == final))].copy()
    x["cell"] = x.apply(lambda q: f"{100 * q['accuracy']:.0f} n={int(q['n'])}" if np.isfinite(q["accuracy"]) else "-", axis=1)
    x["col"] = x["table"] + ":" + x["candidate"] + " " + x["h"].astype(int).astype(str) + "s"
    A(f"Non-overlapping accuracy, 2010-26 (% right, decisions), agreement rule and the final `{final}`:\n")
    A(x.pivot_table(index="check", columns="col", values="cell", aggfunc="first").rename_axis(None, axis=1).reset_index().to_markdown(index=False))
    y = lk[(lk.period == "2010-26") & (lk.table == "standalone") & (lk.h == 21)]
    g = y.groupby("check")["accuracy"].agg(["min", "median", "max"]).mul(100).round(0)
    A("\nRange over the 12 candidates of the standalone 21-session non-overlapping accuracy, 2010-26, per check (min / median / max, %):\n")
    A(g.reset_index().to_markdown(index=False))
    A("\n* (1) Shuffled labels (targets and the 1-session return the house weights are fitted on, three permutations): standalone 41-58 % over the "
      "12 votes and both horizons, mean 50 %.")
    A("* (2) Votes made staler by 1 / 5 / 21 sessions: 41-64 % over both horizons, 45-53 % at 21 sessions (nothing to collapse). A planted label (vote = sign of the next 21 sessions' return) "
      "scores 100 %, so the harness does expose a look-ahead. Votes taken from 21 / 63 sessions in the FUTURE: 39-59 % / 38-63 % standalone. The four "
      "euro-area 3-month portfolio votes do improve when taken from 63 sessions ahead (as extra votes 60-66 % at 21 and 63-73 % at 42 sessions, "
      "against 52-55 % and 54-57 % live): with a 60-day lag that is the flow of the very months in which the return is earned. Together with the "
      "zero-lag control (section 5e, 42-56 %) it says the flows move WITH the exchange rate and do not precede it.")
    A("* Lag audit: section 1; every observation is at least as old as the stated lag at the session close that uses it.")
    A("* Label in disguise: none of the signals uses EUR/USD prices except `spf_contra`, whose two legs are forecasts of the same survey round; "
      "correlations with the forward return are in section 5a.")
    A(f"\n## 11. Variant count\n\n{N_ARMS} candidate votes, each evaluated standalone, as an extra vote and with two placebos; no parameter searched. "
      "Controls that are not candidates and from which nothing is selected: two orthogonalised versions of each vote, the native-frequency lead-lag "
      "table, the vintage comparison, the replication of the five dollar-side votes on the non-euro basket. One selection (the declared rule). "
      "For deflation: 12.\n")
    path = path or (ROOT / "reports" / f"arm_{ARM}.md")
    path.write_text("\n".join(L) + "\n")


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    run()
    r = run.last
    leak_checks(r)
    write_report(r)
    print(r["bar"].round(1).to_string())
    print(r["checks"])
