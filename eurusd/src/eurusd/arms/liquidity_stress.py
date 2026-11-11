"""Arm Q ("liquidity_stress"): relative central-bank liquidity and financial stress / credit as an EXTRA VOTE for
multi-week EUR/USD direction (round 5).

EVERYTHING IN THIS DOCSTRING (data, lags, priors, the 12 candidates, the selection rule, the reading of the success
bar) WAS WRITTEN BEFORE ANY RESULT WAS COMPUTED.

New raw data (all cached by `fetch_data()`; files are prefixed `liquidity_stress_`)
  data/macro/liquidity_stress_ecb_ilm_weekly.csv   ECB Data Portal, flow ILM (weekly consolidated financial statement of the
        Eurosystem, EUR mn): total assets `ILM.W.U2.C.T000000.Z5.Z01`, credit institutions' current accounts
        `ILM.W.U2.C.L020100.U2.EUR`, deposit facility `ILM.W.U2.C.L020200.U2.EUR`, marginal lending facility
        `ILM.W.U2.C.A050500.U2.EUR`. The ISO week of the key is stamped with its FRIDAY (the statement date). The statement
        is published the following Tuesday 15:00 CET. LAG USED: 7 calendar days (usable from the session closing on the
        next Friday; 3 days later than publication).
  data/macro/liquidity_stress_fed_h41_weekly.csv   FRED (curl --http1.1) WALCL (H.4.1 total assets, Wednesday level, USD mn),
        WRESBAL (reserve balances, week average ending Wednesday, USD mn), RRPONTSYD (overnight reverse repos, USD bn, the
        value of that Wednesday). H.4.1 is released Thursday 16:30 ET. LAG USED: 7 calendar days from the Wednesday stamp.
  data/macro/liquidity_stress_us_m2.csv            FRED M2SL (monthly, SA, USD bn), stamped with the month END. H.6 is published
        on the fourth Tuesday of the following month. LAG USED: 35 calendar days after month-end. Current vintage.
  data/macro/liquidity_stress_ea_m3.csv            ECB flow BSI: M3 annual growth rate `BSI.M.U2.Y.V.M30.X.I.U2.2300.Z01.A` and
        M3 stock `...X.1.U2.2300.Z01.E`; stamped with the month END; published about the 19th working day of the following
        month. LAG USED: 35 calendar days after month-end. Current vintage.
  data/macro/liquidity_stress_ciss_daily.csv       ECB flow CISS, new daily Composite Indicator of Systemic Stress:
        euro area `CISS.D.U2.Z0Z.4F.EC.SS_CIN.IDX`, United States `CISS.D.US.Z0Z.4F.EC.SS_CIN.IDX`. Day D is on the portal on
        D+1. LAG USED: 2 calendar days. Current vintage (the ECB describes the transformation as recursive, i.e. not revised
        by construction; not verifiable here because no vintages are published).
  data/macro/liquidity_stress_hy_oas.csv           ICE BofA US High Yield option-adjusted spread (BAMLH0A0HYM2). FRED now
        serves only three years, so the history to 2025-06 comes from a GitHub copy of the FRED file and is spliced with
        FRED from 2023-11; the overlap must match exactly or the fetch fails. Market price, never revised. Day D is
        published on D+1. LAG USED: 2 calendar days.
  data/macro/liquidity_stress_us_fci_weekly.csv    FRED NFCI (Chicago Fed, week ending Friday, released the following
        Wednesday) and STLFSI4 (St. Louis Fed, week ending Friday, released the following Thursday). LAG USED: 7 calendar
        days. WARNING: both are CURRENT-VINTAGE model estimates (NFCI is re-estimated over its whole history every week,
        STLFSI4 was back-cast in 2022 with full-sample statistics): any result that uses them is NOT a real-time result.
  VIX: the repo's `data/macro/fred_VIXCLS.csv`, one calendar day (as the feature store).
  data/processed/cross/liquidity_stress_panel.parquet   the aligned session panel (inputs after lags, raw signals, votes).
  The 2022+ files `fred_WALCL / WRESBAL / RRPONTSYD / BAMLH0A0HYM2 / STLFSI4` already in data/macro are not touched.

Signals. A vote is +1 (long EUR/USD), -1 (short) or 0 (silent). Priors are economic and fixed here:
 (A) relative central-bank liquidity
   1 bs_d3m         -sign of the 63-session change of log(ECB total assets / Fed total assets), each in its own currency
                    (so no exchange-rate term enters). Prior: the balance sheet that grows faster weakens its currency.
   2 bs_d6m         the same over 126 sessions.
   3 bs_d12m        the same over 252 sessions.
   4 money_gap      -sign of [(euro-area M3 y/y - US M2 y/y) minus its expanding mean since 1999]. Prior (monetary model):
                    relatively faster money growth weakens the currency; the constant absorbs trend money-demand differences.
   5 xliq_lvl       -sign of [log((ECB current accounts + deposit facility) / (Fed reserve balances + overnight reverse
                    repos)) minus its trailing 756-session mean]: level of relative excess liquidity against its 3-year norm.
                    Prior: relatively abundant euro liquidity weakens the euro.
 (B) financial stress and credit
   6 ciss_diff_lvl  -sign of [(CISS euro area - CISS US) minus its expanding mean since 1999]. Prior: higher relative euro
                    stress weakens the euro.
   7 ciss_diff_d1m  -sign of the 21-session change of (CISS euro area - CISS US).
   8 ciss_diff_d3m  -sign of the 63-session change of (CISS euro area - CISS US).
   9 gstress_hi_rising  G = mean of the expanding z-scores (since 1999) of CISS EA, CISS US, log VIX and log HY spread.
                    -1 when G > 0 and its 63-session change > 0 (stress high and rising: dollar safe-haven bid), +1 when
                    G < 0 and falling, 0 otherwise.
  10 credit_d3m     -sign of the 63-session change of the US high-yield spread (credit-spread momentum: widening = risk-off
                    = dollar up).
  11 usfci_d3m      -sign of the 63-session change of the mean expanding z-score of NFCI and STLFSI4 (US financial
                    conditions tightening = dollar up). NOT REAL-TIME (see the warning above); reported, flagged.
  12 combo_majority sign of the sum of votes 1-10 (the ten real-time votes; 0 on a tie).
 Variant count for deflation: 12. No parameter of any signal is fitted or searched.

The agreement rule (state of the art, reports/arm_selective.md) is rebuilt with the selective helpers: house score
walk-forward (`house_score_wf`), agree3 = sign(cot_z52) = sign(d_spread2y_20) = sign(house score); the reconciliation
table compares every cell with experiments/results/arms/selective_accuracy_coverage.csv.

Evaluation (round-5 addendum), targets = sign of the 21 / 42 / 63-session forward return, selective's Target objects,
selective's weekly grid (every 5th session) and greedy non-overlapping stream, plain Wilson on non-overlapping counts:
  1 standalone: the vote's own calls (direction = vote, silent on 0), weekly and non-overlapping, 2010-26 / 2016-26 / 2023-26.
  2 extra vote: (a) "agree3 AND vote == agreed direction" against agree3 alone, with decisions per year next to every
    accuracy; (b) the vote's calls on sessions where the three old signals do NOT agree (coverage extension);
    (c) paired difference accuracy(extra) - accuracy(agree3) on the weekly grid with a circular block bootstrap (block
    2h/5 weeks, 2000 draws), and - on agree3's own non-overlapping stream - accuracy(kept) - accuracy(all) with an iid
    bootstrap over decisions.
  3 daily-stream incremental test: the final extra-vote rule as a weekly-tranche 21-session book (selective.book_time_exit)
    in meta.combine(["weak_signals","regime_trend",ARM],"EW") against the two-way combination; daily P&L correlations.
  4 timing placebo: the vote made 63 and 126 sessions staler, everything recomputed.

SELECTION RULE (declared by the lead): final = the candidate whose EXTRA-VOTE rule has the highest lower 95 % Wilson bound
  of the 2010-2015 non-overlapping 21-session accuracy, among candidates with at least 6 non-overlapping 21-session
  decisions a year in 2010-2015. If no candidate has 6 a year there is NO eligible final; the stream written to disk is
  then the candidate with the highest lower bound regardless of count, flagged as failing the rule.
SUCCESS BAR (round 5) as I read it, fixed before results: gain = non-overlapping accuracy of the extra-vote rule minus
  that of agree3, in points. Needed: gain >= 3 at 21 AND 42 sessions in 2010-26 AND 2016-26; at least 6 decisions a year
  (judged on the 21-session non-overlapping stream; a 42-session non-overlapping stream cannot exceed 6 a year by
  construction, so its count is reported, not tested); 2023-26 accuracy not below agree3 at 21 and 42; and the placebo
  gain at +63 and at +126 sessions is at most half of the real gain at 21 and 42 sessions (2010-26).
"""
from __future__ import annotations

import io
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.arms import selective as SEL  # noqa: E402
from eurusd.featstore import _align_lagged  # noqa: E402
from eurusd.wf import report  # noqa: E402

MACRO = ROOT / "data" / "macro"
CROSS = ROOT / "data" / "processed" / "cross"
RES = ROOT / "experiments" / "results" / "arms"
ARM = "liquidity_stress"
PRE = "liquidity_stress_"
N_ARMS = 12
HZ = (21, 42, 63)
PLACEBO = (63, 126)
P3 = ("2010-26", "2016-26", "2023-26")
MIN_DEC_PER_YEAR = 6.0
CANDS = ("bs_d3m", "bs_d6m", "bs_d12m", "money_gap", "xliq_lvl", "ciss_diff_lvl", "ciss_diff_d1m", "ciss_diff_d3m",
         "gstress_hi_rising", "credit_d3m", "usfci_d3m", "combo_majority")
REALTIME10 = CANDS[:10]
LAGS = {"ecb_weekly": 7, "fed_weekly": 7, "money_monthly": 35, "ciss_daily": 2, "hy_daily": 2, "fci_weekly": 7, "vix_daily": 1}

ECB_URL = "https://data-api.ecb.europa.eu/service/data/{flow}/{key}?format=csvdata"
FRED_URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}"
HY_MIRROR = "https://raw.githubusercontent.com/mhidper/talvi/HEAD/data/indicadores/BAMLH0A0HYM2.csv"
ECB_KEYS = {"total_assets": ("ILM", "W.U2.C.T000000.Z5.Z01"), "current_accounts": ("ILM", "W.U2.C.L020100.U2.EUR"),
            "deposit_facility": ("ILM", "W.U2.C.L020200.U2.EUR"), "marginal_lending": ("ILM", "W.U2.C.A050500.U2.EUR"),
            "m3_yoy": ("BSI", "M.U2.Y.V.M30.X.I.U2.2300.Z01.A"), "m3_stock": ("BSI", "M.U2.Y.V.M30.X.1.U2.2300.Z01.E"),
            "ciss_ea": ("CISS", "D.U2.Z0Z.4F.EC.SS_CIN.IDX"), "ciss_us": ("CISS", "D.US.Z0Z.4F.EC.SS_CIN.IDX")}


# ================================================================ fetch (cached)
def _curl(url: str, http11: bool = False, retries: int = 4) -> str:
    cmd = ["curl", "-sS", "-L", "-m", "120", "--fail"] + (["--http1.1"] if http11 else []) + [url]
    err = ""
    for i in range(retries):
        r = subprocess.run(cmd, capture_output=True)
        if r.returncode == 0 and len(r.stdout) > 50:
            return r.stdout.decode("utf-8", "replace")
        err = r.stderr.decode("utf-8", "replace")[:200]
        time.sleep(3 * (i + 1))
    raise RuntimeError(f"fetch failed: {url}: {err}")


def _fred(series: str) -> pd.Series:
    d = pd.read_csv(io.StringIO(_curl(FRED_URL.format(s=series), http11=True)))
    d.columns = ["date", "value"]
    d["date"] = pd.to_datetime(d["date"], errors="coerce")
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    return d.dropna().set_index("date")["value"].sort_index()


def _ecb(name: str) -> pd.Series:
    flow, key = ECB_KEYS[name]
    d = pd.read_csv(io.StringIO(_curl(ECB_URL.format(flow=flow, key=key))))
    return pd.Series(pd.to_numeric(d["OBS_VALUE"], errors="coerce").values, index=d["TIME_PERIOD"].astype(str).values).dropna()


def fetch_data(force: bool = False, verbose: bool = True) -> pd.DataFrame:
    """Downloads every new series once and writes the prefixed CSVs; later calls only read the catalogue."""
    cat_p = MACRO / f"{PRE}sources.csv"
    files = ["ecb_ilm_weekly", "fed_h41_weekly", "us_m2", "ea_m3", "ciss_daily", "hy_oas", "us_fci_weekly"]
    if not force and cat_p.exists() and all((MACRO / f"{PRE}{f}.csv").exists() for f in files):
        return pd.read_csv(cat_p)
    say = print if verbose else (lambda *a, **k: None)
    # ECB weekly financial statement (ISO week -> its Friday)
    ilm = pd.DataFrame({k: _ecb(k) for k in ("total_assets", "current_accounts", "deposit_facility", "marginal_lending")})
    ilm.insert(0, "iso_week", ilm.index)
    ilm.index = pd.to_datetime(ilm["iso_week"] + "-5", format="%G-W%V-%u")
    ilm = ilm.sort_index().rename_axis("date")
    ilm.to_csv(MACRO / f"{PRE}ecb_ilm_weekly.csv"); say("  ECB ILM weekly", ilm.index[0].date(), ilm.index[-1].date(), len(ilm))
    # Fed H.4.1
    walcl, wres, rrp = _fred("WALCL"), _fred("WRESBAL"), _fred("RRPONTSYD")
    fed = pd.DataFrame({"walcl": walcl, "wresbal": wres})
    fed["rrp_mn"] = (rrp.reindex(rrp.index.union(fed.index)).sort_index().ffill(limit=5).reindex(fed.index) * 1000.0).fillna(0.0)
    fed = fed.dropna(subset=["walcl"]).rename_axis("date")
    fed.to_csv(MACRO / f"{PRE}fed_h41_weekly.csv"); say("  Fed H.4.1 weekly", fed.index[0].date(), fed.index[-1].date(), len(fed))
    # money
    try:
        m2 = _fred("M2SL")
    except RuntimeError:
        m2 = pd.read_csv(MACRO / "fred_M2SL.csv", parse_dates=["date"]).set_index("date")["value"]
    m2.index = m2.index + pd.offsets.MonthEnd(0)
    m2.rename("m2sl").rename_axis("date").to_frame().to_csv(MACRO / f"{PRE}us_m2.csv")
    m3 = pd.DataFrame({"m3_yoy": _ecb("m3_yoy"), "m3_stock": _ecb("m3_stock")})
    m3.index = pd.to_datetime(m3.index, format="%Y-%m") + pd.offsets.MonthEnd(0)
    m3.sort_index().rename_axis("date").to_csv(MACRO / f"{PRE}ea_m3.csv"); say("  money", m2.index[-1].date(), m3.index[-1].date())
    # CISS
    ciss = pd.DataFrame({"ciss_ea": _ecb("ciss_ea"), "ciss_us": _ecb("ciss_us")})
    ciss.index = pd.to_datetime(ciss.index)
    ciss.sort_index().rename_axis("date").to_csv(MACRO / f"{PRE}ciss_daily.csv"); say("  CISS", ciss.index[0].date(), ciss.index[-1].date(), len(ciss))
    # HY spread: mirror history + FRED recent, overlap must be identical
    old = pd.read_csv(io.StringIO(_curl(HY_MIRROR)))
    old.columns = ["date", "value"]
    old["date"] = pd.to_datetime(old["date"], errors="coerce"); old["value"] = pd.to_numeric(old["value"], errors="coerce")
    old = old.dropna().set_index("date")["value"].sort_index()
    new = _fred("BAMLH0A0HYM2")
    ov = pd.concat([old, new], axis=1).dropna()
    if len(ov) < 100 or float((ov.iloc[:, 0] - ov.iloc[:, 1]).abs().max()) > 1e-9:
        raise RuntimeError(f"HY spread mirror does not match FRED on the overlap ({len(ov)} days)")
    hy = pd.DataFrame({"value": pd.concat([old[old.index < new.index[0]], new]),
                       "source": ["github mhidper/talvi copy of FRED"] * int((old.index < new.index[0]).sum()) + ["FRED"] * len(new)}).rename_axis("date")
    hy.to_csv(MACRO / f"{PRE}hy_oas.csv"); say("  HY OAS", hy.index[0].date(), hy.index[-1].date(), len(hy), "overlap days identical:", len(ov))
    # US financial conditions (current vintage!)
    fci = pd.DataFrame({"nfci": _fred("NFCI"), "stlfsi4": _fred("STLFSI4")}).rename_axis("date")
    fci.to_csv(MACRO / f"{PRE}us_fci_weekly.csv"); say("  NFCI / STLFSI4", fci.index[0].date(), fci.index[-1].date(), len(fci))
    today = pd.Timestamp.now(tz="UTC").strftime("%Y-%m-%d")
    rows = [
        ("ecb_ilm_weekly", "ECB Data Portal ILM.W.U2.C.{T000000.Z5.Z01, L020100.U2.EUR, L020200.U2.EUR, A050500.U2.EUR}", ilm.index, "Friday statement, published next Tuesday", "7 calendar days"),
        ("fed_h41_weekly", "FRED WALCL, WRESBAL, RRPONTSYD (curl --http1.1)", fed.index, "Wednesday, released Thursday 16:30 ET", "7 calendar days"),
        ("us_m2", "FRED M2SL", m2.index, "month m released 4th Tuesday of m+1", "35 calendar days after month-end"),
        ("ea_m3", "ECB Data Portal BSI.M.U2.Y.V.M30.X.{I,1}.U2.2300.Z01.{A,E}", m3.index, "month m released ~19th working day of m+1", "35 calendar days after month-end"),
        ("ciss_daily", "ECB Data Portal CISS.D.{U2,US}.Z0Z.4F.EC.SS_CIN.IDX", ciss.index, "day D on the portal on D+1", "2 calendar days"),
        ("hy_oas", f"{HY_MIRROR} (to 2023-11) + FRED BAMLH0A0HYM2", hy.index, "day D published D+1", "2 calendar days"),
        ("us_fci_weekly", "FRED NFCI, STLFSI4 (CURRENT VINTAGE, not real-time)", fci.index, "week ending Friday, released next Wed / Thu", "7 calendar days"),
    ]
    cat = pd.DataFrame([{"file": f"data/macro/{PRE}{f}.csv", "source": s, "first": i.min().date(), "last": i.max().date(), "rows": len(i),
                         "publication": p, "lag_used": lag, "fetched": today} for f, s, i, p, lag in rows])
    cat.to_csv(cat_p, index=False)
    return cat


def _read(name: str) -> pd.DataFrame:
    return pd.read_csv(MACRO / f"{PRE}{name}.csv", parse_dates=["date"]).set_index("date").sort_index()


# ================================================================ panel, raw signals, votes
def _expz(s: pd.Series, start: str, minp: int) -> pd.Series:
    """Expanding z-score from `start`: every value is standardised with observations stamped <= its own stamp."""
    x = s[s.index >= start].dropna()
    return (x - x.expanding(minp).mean()) / x.expanding(minp).std()


def build_panel(D: pd.DataFrame, write: bool = True) -> pd.DataFrame:
    """Session-aligned inputs (after the publication lags), raw signals and the stamp of every observation used."""
    fetch_data(verbose=False)
    cdate = pd.DatetimeIndex(pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None))
    P = pd.DataFrame(index=D.index)
    P["cdate"] = cdate

    def al(s: pd.Series, lag: int, name: str) -> np.ndarray:
        s = s.dropna()
        v = _align_lagged(s, cdate, lag).values
        pos = np.searchsorted(s.index.values, (cdate - pd.Timedelta(days=lag)).values, side="right") - 1
        st = np.where(pos >= 0, s.index.values[np.maximum(pos, 0)].astype("datetime64[ns]"), np.datetime64("NaT", "ns"))
        P[f"stamp_{name}"] = st
        chk = np.where(pos >= 0, s.values[np.maximum(pos, 0)], np.nan)
        assert np.allclose(chk, v, equal_nan=True), name
        return v

    ilm, fed, m2, m3 = _read("ecb_ilm_weekly"), _read("fed_h41_weekly"), _read("us_m2")["m2sl"], _read("ea_m3")
    ciss, hy, fci = _read("ciss_daily"), _read("hy_oas")["value"], _read("us_fci_weekly")
    vix = pd.read_csv(MACRO / "fred_VIXCLS.csv", parse_dates=["date"]).set_index("date")["value"].astype(float).sort_index()
    # (A) balance sheets and excess liquidity
    P["ecb_assets"] = al(ilm["total_assets"], LAGS["ecb_weekly"], "ecb_assets")
    P["fed_assets"] = al(fed["walcl"], LAGS["fed_weekly"], "fed_assets")
    P["ecb_xliq"] = al(ilm["current_accounts"] + ilm["deposit_facility"], LAGS["ecb_weekly"], "ecb_xliq")
    P["fed_xliq"] = al(fed["wresbal"] + fed["rrp_mn"], LAGS["fed_weekly"], "fed_xliq")
    P["bs_rel"] = np.log(P["ecb_assets"]) - np.log(P["fed_assets"])
    xl = np.log(P["ecb_xliq"]) - np.log(P["fed_xliq"])
    P["xliq_rel"] = xl - xl.rolling(756, min_periods=504).mean()
    # money growth gap (monthly, expanding mean since 1999 on the monthly stamps)
    g = (m3["m3_yoy"] - 100.0 * (m2 / m2.shift(12) - 1.0)).dropna()
    g = g[g.index >= "1999-01-01"]
    P["money_diff"] = al(g, LAGS["money_monthly"], "money")
    P["money_gap"] = al(g - g.expanding(36).mean(), LAGS["money_monthly"], "money_gap")
    # (B) stress
    cd = (ciss["ciss_ea"] - ciss["ciss_us"]).dropna()
    cd = cd[cd.index >= "1999-01-01"]
    P["ciss_ea"] = al(ciss["ciss_ea"], LAGS["ciss_daily"], "ciss_ea")
    P["ciss_us"] = al(ciss["ciss_us"], LAGS["ciss_daily"], "ciss_us")
    P["ciss_diff"] = al(cd, LAGS["ciss_daily"], "ciss_diff")
    P["ciss_diff_gap"] = al(cd - cd.expanding(500).mean(), LAGS["ciss_daily"], "ciss_diff_gap")
    P["hy_oas"] = al(hy, LAGS["hy_daily"], "hy")
    z = pd.DataFrame({"ciss_ea": al(_expz(ciss["ciss_ea"], "1999-01-01", 500), LAGS["ciss_daily"], "z_ciss_ea"),
                      "ciss_us": al(_expz(ciss["ciss_us"], "1999-01-01", 500), LAGS["ciss_daily"], "z_ciss_us"),
                      "hy": al(_expz(np.log(hy), "1999-01-01", 500), LAGS["hy_daily"], "z_hy"),
                      "vix": al(_expz(np.log(vix), "1999-01-01", 500), LAGS["vix_daily"], "z_vix")}, index=D.index)
    P["gstress"] = z.mean(axis=1, skipna=False)
    zf = pd.DataFrame({"nfci": al(_expz(fci["nfci"], "1994-01-01", 156), LAGS["fci_weekly"], "z_nfci"),
                       "stlfsi4": al(_expz(fci["stlfsi4"], "1994-01-01", 156), LAGS["fci_weekly"], "z_stlfsi4")}, index=D.index)
    P["usfci"] = zf.mean(axis=1, skipna=False)
    V = make_votes(P)
    for c in CANDS:
        P[f"vote_{c}"] = V[c]
    if write:
        CROSS.mkdir(parents=True, exist_ok=True)
        P.to_parquet(CROSS / f"{PRE}panel.parquet")
    return P


def make_votes(P: pd.DataFrame) -> pd.DataFrame:
    """The 12 candidate votes (+1 long EUR/USD, -1 short, 0 silent). Signs are the priors of the module docstring."""
    V = pd.DataFrame(index=P.index)
    V["bs_d3m"] = -np.sign(P["bs_rel"].diff(63))
    V["bs_d6m"] = -np.sign(P["bs_rel"].diff(126))
    V["bs_d12m"] = -np.sign(P["bs_rel"].diff(252))
    V["money_gap"] = -np.sign(P["money_gap"])
    V["xliq_lvl"] = -np.sign(P["xliq_rel"])
    V["ciss_diff_lvl"] = -np.sign(P["ciss_diff_gap"])
    V["ciss_diff_d1m"] = -np.sign(P["ciss_diff"].diff(21))
    V["ciss_diff_d3m"] = -np.sign(P["ciss_diff"].diff(63))
    G, dG = P["gstress"], P["gstress"].diff(63)
    V["gstress_hi_rising"] = np.where((G > 0) & (dG > 0), -1.0, np.where((G < 0) & (dG < 0), 1.0, np.where(G.notna() & dG.notna(), 0.0, np.nan)))
    V["credit_d3m"] = -np.sign(P["hy_oas"].diff(63))
    V["usfci_d3m"] = -np.sign(P["usfci"].diff(63))
    V = V.fillna(0.0)
    V["combo_majority"] = np.sign(V[list(REALTIME10)].sum(axis=1))
    return V[list(CANDS)]


def lag_audit(P: pd.DataFrame) -> pd.DataFrame:
    """For every aligned input: the smallest and largest age (calendar days) of the observation used at a session close."""
    need = {"ecb_assets": 7, "ecb_xliq": 7, "fed_assets": 7, "fed_xliq": 7, "money": 35, "money_gap": 35, "ciss_ea": 2, "ciss_us": 2,
            "ciss_diff": 2, "ciss_diff_gap": 2, "hy": 2, "z_ciss_ea": 2, "z_ciss_us": 2, "z_hy": 2, "z_vix": 1, "z_nfci": 7, "z_stlfsi4": 7}
    rows = []
    x = P[P.index.year >= 2010]
    for k, lag in need.items():
        age = (x["cdate"] - x[f"stamp_{k}"]).dt.days
        rows.append({"input": k, "lag_required_days": lag, "min_age_days": int(age.min()), "median_age_days": float(age.median()),
                     "max_age_days": int(age.max()), "ok": bool(age.min() >= lag)})
    return pd.DataFrame(rows)


# ================================================================ rules and their statistics
def agreement(ctx: SEL.Ctx, years=SEL.YEARS):
    """The agreement rule exactly as selective.selectors builds it."""
    hs = SEL.house_score_wf(ctx, years=years)
    sg = np.sign(hs)
    cot, spr = np.sign(ctx.G["cot_z52"].values), np.sign(ctx.G["d_spread2y_20"].values)
    base = np.isfinite(hs) & (sg != 0)
    agree = base & (cot == sg) & (spr == sg)
    return hs, sg, base, agree


def rule_rows(ctx, T, speak, dirs, horizons=HZ, modes=("weekly", "nonoverlap"), keep=None) -> list[dict]:
    out = []
    for h in horizons:
        t = T[f"sign{h}"]
        valid = np.isfinite(t.long)
        for mode in modes:
            idx = SEL.weekly_idx(speak, valid) if mode == "weekly" else SEL.seq_idx(speak, valid, t.hold)
            dec = SEL.decision_frame(ctx, t, idx, dirs, None)
            if keep is not None:
                keep[(h, mode)] = dec
            for r in SEL.cell_stats(ctx, t, dec, speak, mode):
                out.append({"h": h, "mode": mode, **r})
    return out


def _clean_dirs(v: np.ndarray) -> np.ndarray:
    return np.where(np.nan_to_num(v) >= 0, 1.0, -1.0)


def paired_weekly(ctx, t, spA, spE, sg, a, b, reps=2000, seed=7) -> dict:
    """accuracy(extra-vote rule) - accuracy(agreement rule) on the weekly grid, circular block bootstrap."""
    valid = np.isfinite(t.long)
    g = np.arange(0, len(valid), SEL.STEP); g = g[valid[g]]
    g = g[(ctx.year[g] >= a) & (ctx.year[g] <= b)]
    A, E = spA[g].astype(float), spE[g].astype(float)
    hit = np.nan_to_num((np.where(sg[g] > 0, t.long[g], t.short[g]) > 0).astype(float)) * A
    out = {"n_agree": int(A.sum()), "n_extra": int(E.sum())}
    if E.sum() < 5 or A.sum() - E.sum() < 1:
        return out
    aA, aE, aD = hit.sum() / A.sum(), (hit * E).sum() / E.sum(), (hit * (A - E)).sum() / (A - E).sum()
    block = max(2, int(math.ceil(2 * t.h / SEL.STEP)))
    Tn = len(g)
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(Tn / block))
    idx = ((rng.integers(0, Tn, size=(reps, nb))[:, :, None] + np.arange(block)[None, None, :]) % Tn).reshape(reps, -1)[:, :Tn]
    As, Es, Hs = A[idx], E[idx], hit[idx]
    with np.errstate(divide="ignore", invalid="ignore"):
        bA, bE = Hs.sum(1) / As.sum(1), (Hs * Es).sum(1) / Es.sum(1)
        bD = (Hs * (As - Es)).sum(1) / (As - Es).sum(1)
    d1, d2 = bE - bA, bE - bD
    d1, d2 = d1[np.isfinite(d1)], d2[np.isfinite(d2)]
    out.update({"acc_agree": aA, "acc_extra": aE, "acc_dropped": aD, "diff": aE - aA, "diff_lo": float(np.quantile(d1, 0.025)),
                "diff_hi": float(np.quantile(d1, 0.975)), "p_diff_le0": float((d1 <= 0).mean()), "kept_minus_dropped": aE - aD,
                "kd_lo": float(np.quantile(d2, 0.025)), "kd_hi": float(np.quantile(d2, 0.975))})
    return out


def paired_nonoverlap(ctx, t, spA, spE, sg, a, b, reps=4000, seed=7) -> dict:
    """On the agreement rule's OWN non-overlapping stream: accuracy of the decisions the vote confirms minus all."""
    valid = np.isfinite(t.long)
    idx = SEL.seq_idx(spA, valid, t.hold)
    idx = idx[(ctx.year[idx] >= a) & (ctx.year[idx] <= b)]
    hit = (np.where(sg[idx] > 0, t.long[idx], t.short[idx]) > 0).astype(float)
    k = spE[idx].astype(float)
    out = {"n_agree": int(len(idx)), "n_extra": int(k.sum())}
    if k.sum() < 3 or len(idx) - k.sum() < 1:
        return out
    aA, aE, aD = hit.mean(), (hit * k).sum() / k.sum(), (hit * (1 - k)).sum() / (1 - k).sum()
    rng = np.random.default_rng(seed)
    bi = rng.integers(0, len(idx), size=(reps, len(idx)))
    with np.errstate(divide="ignore", invalid="ignore"):
        d1 = (hit[bi] * k[bi]).sum(1) / k[bi].sum(1) - hit[bi].mean(1)
        d2 = (hit[bi] * k[bi]).sum(1) / k[bi].sum(1) - (hit[bi] * (1 - k[bi])).sum(1) / (1 - k[bi]).sum(1)
    d1, d2 = d1[np.isfinite(d1)], d2[np.isfinite(d2)]
    out.update({"acc_agree": aA, "acc_extra": aE, "acc_dropped": aD, "diff": aE - aA, "diff_lo": float(np.quantile(d1, 0.025)),
                "diff_hi": float(np.quantile(d1, 0.975)), "p_diff_le0": float((d1 <= 0).mean()), "kept_minus_dropped": aE - aD,
                "kd_lo": float(np.quantile(d2, 0.025)), "kd_hi": float(np.quantile(d2, 0.975))})
    return out


def evaluate(ctx, T, V: pd.DataFrame, hs, sg, base, agree, cands=CANDS, placebo=PLACEBO, paired: bool = True, keep: dict | None = None):
    """Returns (standalone table, votes table, paired table). `keep` collects the weekly / non-overlapping decision frames."""
    sgc = _clean_dirs(sg)
    A = pd.DataFrame(rule_rows(ctx, T, agree, sgc, keep=None if keep is None else keep.setdefault("agree3", {})))
    A.insert(0, "candidate", "agree3"); A.insert(0, "table", "agree3")
    ref = A.set_index(["h", "mode", "period"])
    st_rows, v_rows, p_rows = [], [A], []

    def add_ref(df):
        k = pd.MultiIndex.from_frame(df[["h", "mode", "period"]])
        df["agree_n"] = ref["n"].reindex(k).values
        df["agree_dec_per_year"] = ref["dec_per_year"].reindex(k).values
        df["agree_accuracy"] = ref["accuracy"].reindex(k).values
        df["gain_pts"] = 100 * (df["accuracy"] - df["agree_accuracy"])
        return df

    for c in cands:
        for lag in (0,) + tuple(placebo):
            v = V[c].shift(lag).fillna(0.0).values if lag else V[c].fillna(0.0).values
            tag = "" if lag == 0 else f"placebo+{lag}"
            # 1 standalone
            s = pd.DataFrame(rule_rows(ctx, T, base & (v != 0), _clean_dirs(v)))
            s.insert(0, "candidate", c); s.insert(0, "table", tag or "standalone"); st_rows.append(s)
            # 2a extra vote
            spE = agree & (v == sg)
            kk = None if (keep is None or lag) else keep.setdefault(c, {})
            e = pd.DataFrame(rule_rows(ctx, T, spE, sgc, keep=kk))
            e.insert(0, "candidate", c); e.insert(0, "table", tag or "extra_vote"); v_rows.append(add_ref(e))
            if lag == 0:
                # 2b the vote's own calls where the old three do not agree
                d = pd.DataFrame(rule_rows(ctx, T, base & ~agree & (v != 0), _clean_dirs(v)))
                d.insert(0, "candidate", c); d.insert(0, "table", "disagree_calls"); v_rows.append(add_ref(d))
                # 2c paired differences
                if paired:
                    for h in HZ:
                        for lab, a, b in SEL.PERIODS:
                            p_rows.append({"table": "paired_weekly", "candidate": c, "h": h, "period": lab, **paired_weekly(ctx, T[f"sign{h}"], agree, spE, sg, a, b)})
                            p_rows.append({"table": "paired_nonoverlap_on_agree3_stream", "candidate": c, "h": h, "period": lab,
                                           **paired_nonoverlap(ctx, T[f"sign{h}"], agree, spE, sg, a, b)})
    return pd.concat(st_rows, ignore_index=True), pd.concat(v_rows, ignore_index=True), pd.DataFrame(p_rows)


def select_final(VT: pd.DataFrame) -> tuple[pd.DataFrame, str, bool, str]:
    x = VT[(VT.table == "extra_vote") & (VT.h == 21) & (VT["mode"] == "nonoverlap") & (VT.period == "2010-15")].copy()
    x = x[["candidate", "n", "dec_per_year", "accuracy", "lo", "hi", "agree_accuracy", "agree_dec_per_year", "gain_pts"]]
    x["eligible"] = x["dec_per_year"] >= MIN_DEC_PER_YEAR
    el = x[x["eligible"] & x["lo"].notna()]
    if len(el):
        final, ok, status = el.sort_values(["lo", "n"], ascending=False)["candidate"].iloc[0], True, "selected by the declared rule"
    else:
        final = x[x["lo"].notna()].sort_values(["lo", "n"], ascending=False)["candidate"].iloc[0]
        ok, status = False, "NO candidate has 6 non-overlapping 21-session decisions a year in 2010-15: nominal stream only (fails the declared rule)"
    x["final"] = x["candidate"] == final
    return x.sort_values("lo", ascending=False).reset_index(drop=True), final, ok, status


def bar_check(VT: pd.DataFrame, cand: str) -> tuple[pd.DataFrame, dict]:
    """The round-5 success bar for one candidate, line by line (reading fixed in the module docstring)."""
    q = VT[(VT.candidate == cand) & (VT["mode"] == "nonoverlap")].set_index(["table", "h", "period"])
    rows = []
    for h in (21, 42, 63):
        for per in P3:
            r = q.loc[("extra_vote", h, per)]
            row = {"h": h, "period": per, "agree_acc": 100 * r["agree_accuracy"], "agree_n": r["agree_n"], "agree_per_year": r["agree_dec_per_year"],
                   "extra_acc": 100 * r.get("accuracy", np.nan), "extra_lo": 100 * r.get("lo", np.nan), "extra_hi": 100 * r.get("hi", np.nan),
                   "extra_n": r["n"], "extra_per_year": r.get("dec_per_year", np.nan), "gain_pts": r.get("gain_pts", np.nan)}
            for k in PLACEBO:
                row[f"placebo{k}_gain_pts"] = q.loc[(f"placebo+{k}", h, per)].get("gain_pts", np.nan)
                row[f"placebo{k}_n"] = q.loc[(f"placebo+{k}", h, per)]["n"]
            rows.append(row)
    B = pd.DataFrame(rows)
    g = B.set_index(["h", "period"])
    c = {}
    c["gain>=3 at 21 and 42, 2010-26"] = bool(g.loc[(21, "2010-26"), "gain_pts"] >= 3 and g.loc[(42, "2010-26"), "gain_pts"] >= 3)
    c["gain>=3 at 21 and 42, 2016-26"] = bool(g.loc[(21, "2016-26"), "gain_pts"] >= 3 and g.loc[(42, "2016-26"), "gain_pts"] >= 3)
    c[">=6 decisions/yr (21-session non-overlapping), 2010-26 and 2016-26"] = bool(g.loc[(21, "2010-26"), "extra_per_year"] >= 6 and g.loc[(21, "2016-26"), "extra_per_year"] >= 6)
    c["2023-26 not worse at 21 and 42"] = bool(g.loc[(21, "2023-26"), "gain_pts"] >= 0 and g.loc[(42, "2023-26"), "gain_pts"] >= 0)
    pl = True
    for h in (21, 42):
        gain = g.loc[(h, "2010-26"), "gain_pts"]
        for k in PLACEBO:
            pg = g.loc[(h, "2010-26"), f"placebo{k}_gain_pts"]
            pl &= bool(gain > 0 and np.isfinite(pg) and pg <= 0.5 * gain)
    c["placebo (+63 and +126) loses >= half of the gain at 21 and 42, 2010-26"] = bool(pl)
    c["BAR MET"] = bool(all(c.values()))
    return B, c


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
    hs, sg, base, agree = agreement(ctx)
    keep: dict = {}
    ST, VT, PT = evaluate(ctx, T, V, hs, sg, base, agree, keep=keep)
    # reconciliation with the selective arm's stored table (all four horizons)
    R = pd.DataFrame(rule_rows(ctx, T, agree, _clean_dirs(sg), horizons=SEL.HORIZONS))
    refp = RES / "selective_accuracy_coverage.csv"
    if refp.exists():
        C = pd.read_csv(refp)
        C = C[(C.model == "B:agree3") & (C.rule == "filter")][["h", "mode", "period", "n", "accuracy", "dec_per_year"]]
        R = R.merge(C.rename(columns={"n": "n_selective", "accuracy": "accuracy_selective", "dec_per_year": "dec_per_year_selective"}), on=["h", "mode", "period"], how="left")
        R["match"] = (R["n"] == R["n_selective"]) & ((R["accuracy"] - R["accuracy_selective"]).abs() < 1e-9)
    SELT, final, eligible, status = select_final(VT)
    BAR, checks = bar_check(VT, final)
    say(f"final = {final} ({status})")
    # protocol tables: weekly-tranche 21-session book of every candidate's extra-vote rule, and of agree3
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
    res = {"ctx": ctx, "T": T, "D": D, "panel": P, "votes_raw": V, "hs": hs, "sg": sg, "base": base, "agree": agree, "standalone": ST, "votes": VT,
           "paired": PT, "reconcile": R, "selection": SELT, "final": final, "eligible": eligible, "status": status, "bar": BAR, "checks": checks,
           "report": rep, "streams": streams, "keep": keep, "daily": daily, "lag_audit": lag_audit(P), "cost_pips": cost_pips}
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        daily.to_parquet(RES / f"{ARM}_positions.parquet")
        keep[final][(21, "weekly")][["pos", "fwd_bp", "net_bp", "gross_bp", "hit", "hold"]].loc["2010":].to_parquet(RES / f"{ARM}_decisions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        pd.concat([VT, PT], ignore_index=True).to_csv(RES / f"{ARM}_votes.csv", index=False)
        ST.to_csv(RES / f"{ARM}_standalone.csv", index=False)
        R.to_csv(RES / f"{ARM}_reconciliation.csv", index=False)
        SELT.to_csv(RES / f"{ARM}_selection.csv", index=False)
        BAR.to_csv(RES / f"{ARM}_bar.csv", index=False)
    run.last = res
    return daily["pos"], rep


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


def leak_checks(res: dict, seed: int = 0) -> tuple[pd.DataFrame, pd.DataFrame]:
    """(1) labels shuffled (targets and the 1-session return the house weights are fitted on); (2) the vote made staler by
    1 / 5 / 21 sessions and, as a control that the harness WOULD expose a look-ahead, taken from 21 / 63 sessions in the
    future; (3) what each vote is correlated with (label, past returns, the three old votes)."""
    ctx, T, V, final = res["ctx"], res["T"], res["votes_raw"], res["final"]
    hs, sg, base, agree = res["hs"], res["sg"], res["base"], res["agree"]
    cands = tuple(dict.fromkeys([final, "combo_majority"]))
    rows = []

    def grab(label, ST, VT):
        for tab, X in (("standalone", ST), ("extra_vote", VT), ("agree3", VT)):
            x = X[(X.table == tab) & (X["mode"] == "nonoverlap") & X.period.isin(P3) & X.h.isin((21, 42))]
            for _, q in x.iterrows():
                rows.append({"check": label, "rule": f"{tab}:{q['candidate']}", "h": q["h"], "period": q["period"], "n": q["n"], "accuracy": q.get("accuracy"),
                             "lo": q.get("lo"), "hi": q.get("hi"), "chance_acc": q.get("chance_acc")})

    def ev(label, cx, Tx, Vx, a4):
        ST, VT, _ = evaluate(cx, Tx, Vx, *a4, cands=cands, placebo=(), paired=False)
        grab(label, ST, VT)

    ev("baseline", ctx, T, V, (hs, sg, base, agree))
    rng = np.random.default_rng(seed)
    for s in range(3):
        perm = rng.permutation(len(ctx.D))
        Ts = {k: (t.permuted(perm) if k.startswith("sign") else t) for k, t in T.items()}
        cx = ctx.with_fwd1(ctx.fwd1[perm])
        ev(f"shuffled_labels_{s}", cx, Ts, V, agreement(cx))
    for lag in (1, 5, 21):
        ev(f"vote_stale_plus{lag}", ctx, T, V.shift(lag), (hs, sg, base, agree))
    for lag in (21, 63):
        ev(f"lookahead_control_minus{lag}", ctx, T, V.shift(-lag), (hs, sg, base, agree))
    # positive control: the vote replaced by the sign of the NEXT 21 sessions' return (a planted look-ahead) must score 100 %
    Vp = V.copy()
    for c in cands:
        Vp[c] = np.sign(T["sign21"].long)
    ev("positive_control_planted_label21", ctx, T, Vp, (hs, sg, base, agree))
    L = pd.DataFrame(rows)
    # (3) what the votes are made of
    D = ctx.D
    k = (D.index.year >= 2010) & base
    f21, f63 = T["sign21"].long, T["sign63"].long
    crow = []
    for c in CANDS:
        v = V[c].fillna(0.0).values
        m = k & (v != 0)
        cc = lambda x: float(np.corrcoef(v[m & np.isfinite(x)], x[m & np.isfinite(x)])[0, 1]) if (m & np.isfinite(x)).sum() > 50 else np.nan
        crow.append({"vote": c, "active_share": float((v[k] != 0).mean()), "share_long": float((v[m] > 0).mean()), "flips_per_year": float((np.diff(v[k]) != 0).sum() / 16.85),
                     "corr_fwd21_bp": cc(f21), "corr_fwd63_bp": cc(f63), "corr_past_ret21": cc(D["ret_21d"].values), "corr_past_ret63": cc(D["ret_63d"].values),
                     "corr_past_ret252": cc(D["ret_252d"].values), "agree_with_cot_sign": float((v[m] == np.sign(D["cot_z52"].values[m])).mean()),
                     "agree_with_spread_trend_sign": float((v[m] == np.sign(D["d_spread2y_20"].values[m])).mean()),
                     "agree_with_house_sign": float((v[m] == sg[m]).mean()), "agree_with_agree3_direction": float((v[m & agree] == sg[m & agree]).mean())})
    Cc = pd.DataFrame(crow)
    L.to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
    Cc.to_csv(RES / f"{ARM}_vote_anatomy.csv", index=False)
    res["leak"], res["anatomy"] = L, Cc
    return L, Cc


def by_year(dec: pd.DataFrame) -> pd.DataFrame:
    g = dec[dec.index.year >= 2010].groupby("year")
    return pd.DataFrame({"decisions": g.size(), "long_share": g["pos"].apply(lambda x: float((x > 0).mean())), "accuracy": g["hit"].mean(),
                         "net_win_rate": g["net_bp"].apply(lambda x: float((x > 0).mean())), "net_bp": g["net_bp"].mean()}).reset_index()


# ================================================================ report
PRIORS = [
    ("bs_d3m", "A", "-", "63-session change of log(ECB total assets / Fed total assets), own currencies", "ECB ILM weekly, FRED WALCL", "7 d"),
    ("bs_d6m", "A", "-", "the same over 126 sessions", "same", "7 d"),
    ("bs_d12m", "A", "-", "the same over 252 sessions", "same", "7 d"),
    ("money_gap", "A", "-", "(EA M3 y/y - US M2 y/y) minus its expanding mean since 1999", "ECB BSI, FRED M2SL", "35 d after month-end"),
    ("xliq_lvl", "A", "-", "log((ECB current accounts + deposit facility) / (Fed reserves + ON RRP)) minus its trailing 756-session mean", "ECB ILM, FRED WRESBAL + RRPONTSYD", "7 d"),
    ("ciss_diff_lvl", "B", "-", "(CISS euro area - CISS US) minus its expanding mean since 1999", "ECB CISS daily", "2 d"),
    ("ciss_diff_d1m", "B", "-", "21-session change of (CISS EA - CISS US)", "ECB CISS daily", "2 d"),
    ("ciss_diff_d3m", "B", "-", "63-session change of (CISS EA - CISS US)", "ECB CISS daily", "2 d"),
    ("gstress_hi_rising", "B", "-", "G = mean expanding z of CISS EA, CISS US, log VIX, log HY spread; -1 if G > 0 and rising over 63 sessions, +1 if G < 0 and falling, else silent", "ECB CISS, VIX, HY OAS", "2 d (VIX 1 d)"),
    ("credit_d3m", "B", "-", "63-session change of the US high-yield spread", "ICE BofA HY OAS", "2 d"),
    ("usfci_d3m", "B", "-", "63-session change of the mean expanding z of NFCI and STLFSI4 (NOT real-time: current-vintage estimates)", "FRED NFCI, STLFSI4", "7 d"),
    ("combo_majority", "A+B", "n/a", "sign of the sum of the ten real-time votes above (all but usfci_d3m); silent on a tie", "-", "-"),
]


def _c(q, ci: bool = False, per_year: bool = True) -> str:
    if not np.isfinite(q.get("accuracy", np.nan)):
        return "-"
    s = f"{100 * q['accuracy']:.0f}"
    if ci:
        s += f" [{100 * q['lo']:.0f}-{100 * q['hi']:.0f}]"
    s += f" n={int(q['n'])}"
    if per_year:
        s += f" ({q['dec_per_year']:.1f}/y)"
    return s


def _piv(X: pd.DataFrame, table: str, mode: str, periods=P3, hs=HZ, ci: bool = False, per_year: bool = True, rows=None) -> str:
    x = X[(X.table == table) & (X["mode"] == mode) & X.period.isin(periods) & X.h.isin(hs)].copy()
    x["cell"] = x.apply(lambda q: _c(q, ci, per_year), axis=1)
    x["col"] = x["period"] + " / " + x["h"].astype(str) + "s"
    order = [f"{p} / {h}s" for p in periods for h in hs]
    t = x.pivot_table(index="candidate", columns="col", values="cell", aggfunc="first")[order]
    t = t.reindex([c for c in (rows or (("agree3",) + CANDS)) if c in t.index])
    return t.rename_axis(None, axis=1).reset_index().to_markdown(index=False)


def _num(X: pd.DataFrame, table: str, mode: str, value: str, periods=P3, hs=(21, 42), fmt="{:+.1f}") -> str:
    x = X[(X.table == table) & (X["mode"] == mode) & X.period.isin(periods) & X.h.isin(hs)].copy()
    x["col"] = x["period"] + " / " + x["h"].astype(str) + "s"
    order = [f"{p} / {h}s" for p in periods for h in hs]
    t = x.pivot_table(index="candidate", columns="col", values=value, aggfunc="first")[order].reindex([c for c in CANDS if c in set(x.candidate)])
    return t.map(lambda v: fmt.format(v) if np.isfinite(v) else "-").rename_axis(None, axis=1).reset_index().to_markdown(index=False)


VERDICT_MD = """
## Verdict (run of 2026-11-11; every number below is regenerated in the tables that follow)
**The round-5 success bar is NOT met, by any of the 12 candidates. Neither family carries usable information about
EUR/USD direction at 1-3 months, on its own or as an extra vote.**

1. **Reconciliation: exact.** The agreement rule rebuilt here matches `selective_accuracy_coverage.csv` in all 32 cells
   (4 horizons x 2 decision modes x 4 periods): non-overlapping 56 / 59 / 61 / 72 % at 10 / 21 / 42 / 63 sessions
   (n = 291 / 156 / 89 / 61) for 2010-26, 57 % at 21 sessions since 2016, 60 / 45 / 50 % (n = 35 / 20 / 14) since 2023.
2. **Standalone: nothing.** Over 2010-26 the twelve votes are right 41-57 % of the time at 21 sessions, 44-58 % at 42 and
   38-61 % at 63 on non-overlapping decisions (n = 208 / 104 / 69 for the always-on votes), and 46-52 / 45-53 / 44-55 % on
   weekly decisions. The best cells: `usfci_d3m` 57 % [50-63] at 21 sessions (n=208; weekly 52 %; it is NOT a real-time
   series and its +126-session placebo is 47 %), `ciss_diff_d3m` 54 / 52 / 61 % (weekly 52 / 52 / 51 %; the vote made 63
   sessions staler scores 60 / 53 / 55 %), `ciss_diff_d1m` 58 % at 42 sessions (weekly 52 %). The relative balance-sheet votes
   are 50 / 55-57 / 48-51 %, the money-growth gap 48 / 51 / 38 %, relative excess liquidity 49 / 49 / 42 %. The one cell whose
   interval excludes a coin on the WRONG side is the safe-haven vote `gstress_hi_rising`: 41 % [34-49] at 21 sessions (n=162;
   weekly 46 %), i.e. the "stress high and rising => dollar up" prior did not hold in 2010-26; turning it round would be a
   post-hoc choice and is not proposed.
3. **Extra vote: it lowers accuracy and cuts the sample.** Final by the declared rule = `ciss_diff_d3m` (2010-15: 60 %
   [46-73], n=45, 7.5 a year, against 62 % for the agreement rule alone - no candidate beat the agreement rule in the
   selection window). Agreement rule AND the vote, non-overlapping: **55 % (n=111, 6.6 a year) against 59 % (n=156, 9.3
   a year) at 21 sessions; 61 % (n=71, 4.3 a year) against 61 % (n=89, 5.3 a year) at 42 sessions; 67 % (n=49) against
   72 % (n=61) at 63.** Since 2016: 52 against 57 % and 60 against 59 %. Since 2023: 60 against 60 % (n=20 v 35) and
   53 against 45 % (n=15 v 20). Gain -4.0 / -0.1 points (2010-26) and -5.8 / +1.5 (2016-26) where +3 / +3 is required.
   Paired difference on the weekly grid: +0.8 points [-4.9, +6.3] at 21 sessions, +2.2 [-3.6, +8.4] at 42. On the agreement
   rule's own non-overlapping stream the decisions the vote confirms are right 53 % of the time and the ones it rejects
   65 % (21 sessions, 76 v 80 decisions).
   Across all 12 candidates the 21-session gain in 2010-26 is negative for every one (-1.3 to -12.2 points); no candidate
   has +3 at both horizons in both periods, with or without the decision-count condition.
4. **Coverage extension: no.** On sessions where the three old signals do NOT agree, the votes are right 44-51 % at 21
   sessions, 46-57 % at 42 and 44-59 % at 63 (2010-26, n = 135-170 / 82-93 / 56-64); the final vote 51 / 57 / 58 %, every
   interval including 50 %.
5. **Timing placebo: the stale vote does better than the live one.** With `ciss_diff_d3m` made 63 sessions staler the
   extra-vote rule scores 62 % / 69 % at 21 / 42 sessions (gain +2.8 / +8.3 points, against -4.0 / -0.1 live); 126 sessions
   staler 55 % / 66 % (-3.9 / +5.1). There is no gain to lose, and the spread between live and placebo (up to 8 points)
   is the size of the selection noise in these 70-110-decision subsets. Shifting the vote by ONE session moves the
   42-session accuracy from 61 to 53 %.
6. **Daily incremental test: the same stream as the agreement rule, slightly worse.** The final rule's weekly-tranche
   book has net Sharpe 0.46 / 0.51 / 0.42 (2010-26 / 2016-26 / 2023-26, 1.2 pips) against 0.52 / 0.51 / 0.43 for the
   agreement rule's own book, and is 0.82 correlated with it (0.31 with `weak_signals`, 0.51 with `regime_trend`).
   EW(weak_signals, regime_trend, this arm) = 0.559 / 0.668 / 0.410 against 0.563 / 0.636 / 0.356 two-way: +0.03 on
   2016-26 and -0.004 on 2010-26, which is the agreement rule re-entering the combination, not new information.
7. **What to keep.** Nothing for the product. The data files are clean, lagged and cached, and can serve as context
   series in the brief (balance-sheet ratio, CISS differential), not as signals.
"""


def write_report(res: dict | None = None, path: Path | None = None) -> None:
    if res is None:
        run(verbose=False)
        res = run.last
    if "leak" not in res:
        leak_checks(res)
    inc = incremental()
    ST, VT, PT, final = res["standalone"], res["votes"], res["paired"], res["final"]
    cat = pd.read_csv(MACRO / f"{PRE}sources.csv")
    P = res["panel"]
    L = []
    A = L.append
    A("# Arm Q: relative central-bank liquidity and financial stress as an extra vote (`liquidity_stress`)\n")
    A("Code `src/eurusd/arms/liquidity_stress.py` (`run(cost_pips=1.2)`, `fetch_data()` cached, `leak_checks()`, `incremental()`; "
      "`python -m eurusd.arms.liquidity_stress` reproduces everything in under a minute). Results in `experiments/results/arms/`: "
      "`liquidity_stress_positions.parquet` (daily weekly-tranche book of the final extra-vote rule: `pos`, `fwd_bp`, `net_bp`), "
      "`liquidity_stress_decisions.parquet` (its weekly decisions), `liquidity_stress_report.csv` (protocol table of all 12 extra-vote books, the "
      "agreement-rule baseline and the 0.6-pip run; `variant`, `final`), `liquidity_stress_votes.csv` (agreement rule, extra vote, calls outside "
      "agreement, placebos, paired differences), `liquidity_stress_standalone.csv`, `liquidity_stress_reconciliation.csv`, `liquidity_stress_selection.csv`, "
      "`liquidity_stress_bar.csv`, `liquidity_stress_incremental.csv`, `liquidity_stress_leakchecks.csv`, `liquidity_stress_vote_anatomy.csv`. "
      "Aligned panel: `data/processed/cross/liquidity_stress_panel.parquet`.\n")
    A("Data, lags, sign priors, the 12 candidates, the selection rule and the reading of the success bar are in the module docstring and were "
      "written before the first result. Nothing was changed afterwards except one addition, marked as such: a planted-label positive control in "
      "the leak checks.")
    A(VERDICT_MD)
    A("## 1. New data: source, span, publication lag used\n")
    A(cat[["file", "source", "first", "last", "rows", "publication", "lag_used"]].to_markdown(index=False))
    A("\nAlso used: `data/macro/fred_VIXCLS.csv` (already in the repo, one calendar day, as the feature store). The 2022+ files already in "
      "`data/macro` (`fred_WALCL`, `fred_WRESBAL`, `fred_RRPONTSYD`, `fred_BAMLH0A0HYM2`, `fred_STLFSI4`) were not touched; FRED answered "
      "`curl --http1.1` from this shell and returned the full history for everything except the ICE BofA spread (three years only), whose history "
      "was taken from a GitHub copy of the FRED file and checked to be identical to FRED on the 413 overlapping days (six independent copies "
      "agree to the last digit on 5,500-7,300 common days).\n")
    A("Lag audit (age in calendar days, at each session's closing date, of the observation actually used; sessions 2010-26). Alignment is "
      "`featstore._align_lagged(series, closing_date, lag)`: last observation stamped <= closing date - lag.\n")
    A(res["lag_audit"].to_markdown(index=False))
    A("\nCaveats. (i) ECB weekly statements are stamped with the Friday of their ISO week and used from the following Friday; the Fed's Wednesday "
      "figures from the following Wednesday. (ii) ECB total assets include quarterly revaluation of gold and reserves: the balance-sheet ratio "
      "jumps at quarter-ends for reasons unrelated to policy. (iii) M2 and M3 are current vintages (revisions are small against a y/y gap that "
      "ranges over +-8 points). (iv) NFCI and STLFSI4 are current-vintage model estimates: `usfci_d3m` is NOT a real-time signal and is excluded "
      "from the combination vote. (v) The daily CISS is a current vintage; no vintages exist to verify that it is unrevised. (vi) Before 2008 "
      "Fed reserve balances were about USD 10 bn, so `xliq_lvl` is only meaningful from the 2008 regime change on (the evaluation starts in 2010 "
      "with a 3-year trailing mean).\n")
    A("## 2. The 12 candidate votes and their priors (fixed before results)\n")
    A("Vote = prior sign x sign(raw quantity): +1 long EUR/USD, -1 short, 0 silent.\n")
    A(pd.DataFrame(PRIORS, columns=["vote", "family", "prior sign", "raw quantity", "data", "lag"]).to_markdown(index=False))
    an = res["anatomy"]
    A("\nWhat the votes look like, 2010-26 (correlations are of the vote with returns in bp; `agree_with_*` = share of active sessions on which "
      "the vote has the same sign as the old signal):\n")
    A(an.round(2).to_markdown(index=False))
    A("\n## 3. Reconciliation of the agreement rule\n")
    R = res["reconcile"]
    R = R[R.period.isin(P3)].copy()
    R["here"] = R.apply(lambda q: f"{100 * q['accuracy']:.1f} n={int(q['n'])}", axis=1)
    R["selective"] = R.apply(lambda q: f"{100 * q['accuracy_selective']:.1f} n={int(q['n_selective'])}", axis=1)
    A(f"Rebuilt with `selective.load_data / make_ctx / build_targets / house_score_wf / weekly_idx / seq_idx / decision_frame / cell_stats`. "
      f"Cells compared with `selective_accuracy_coverage.csv`: {len(res['reconcile'])}; exact matches (n and accuracy): {int(res['reconcile']['match'].sum())}.\n")
    A(R[["h", "mode", "period", "here", "selective", "match"]].to_markdown(index=False))
    A("\n## 4. Standalone accuracy of each vote (direction = the vote; % right, 95 % Wilson interval, decisions, decisions per year)\n")
    for per in P3:
        A(f"\nNon-overlapping decisions, {per}:\n")
        A(_piv(ST, "standalone", "nonoverlap", periods=(per,), ci=True))
    A("\nWeekly decisions (overlapping holds; no interval shown - the effective sample is the non-overlapping count above):\n")
    A(_piv(ST, "standalone", "weekly", per_year=False))
    A("\nTiming placebo of the standalone votes, non-overlapping, 2010-26 (the vote made 63 / 126 sessions staler):\n")
    x = ST[(ST["mode"] == "nonoverlap") & (ST.period == "2010-26")].copy()
    x["cell"] = x.apply(lambda q: _c(q, False, False), axis=1)
    x["col"] = x["h"].astype(str) + "s " + x["table"].replace({"standalone": "live"})
    t = x.pivot_table(index="candidate", columns="col", values="cell", aggfunc="first")
    t = t[[f"{h}s {k}" for h in HZ for k in ("live", "placebo+63", "placebo+126")]].reindex(list(CANDS))
    A(t.rename_axis(None, axis=1).reset_index().to_markdown(index=False))
    A("\n## 5. As an extra vote\n")
    A("### 5a. Agreement rule AND the vote agrees, against the agreement rule alone\n")
    A("Non-overlapping decisions (% right, decisions, decisions per year). First row = the agreement rule alone.\n")
    A(_piv(VT[VT.table.isin(["agree3", "extra_vote"])].assign(table="x"), "x", "nonoverlap"))
    A("\nThe same with 95 % Wilson intervals, 2010-26 only:\n")
    A(_piv(VT[VT.table.isin(["agree3", "extra_vote"])].assign(table="x"), "x", "nonoverlap", periods=("2010-26",), ci=True))
    A("\nGain in accuracy points over the agreement rule, non-overlapping (bar: >= +3 at 21s and 42s in 2010-26 and 2016-26):\n")
    A(_num(VT, "extra_vote", "nonoverlap", "gain_pts", hs=HZ))
    A("\nWeekly decisions:\n")
    A(_piv(VT[VT.table.isin(["agree3", "extra_vote"])].assign(table="x"), "x", "weekly"))
    A("\n### 5b. Coverage extension: the vote's own calls on sessions where the three old signals do NOT agree\n")
    A("Non-overlapping, with 95 % Wilson intervals, 2010-26, then all periods without intervals:\n")
    A(_piv(VT, "disagree_calls", "nonoverlap", periods=("2010-26",), ci=True))
    A("")
    A(_piv(VT, "disagree_calls", "nonoverlap"))
    A("\n### 5c. Paired differences\n")
    A("`paired_weekly`: accuracy(extra-vote rule) - accuracy(agreement rule) on the same weekly grid, circular block bootstrap (block 2h/5 weeks, "
      "2000 draws). `paired_nonoverlap_on_agree3_stream`: on the agreement rule's own non-overlapping decisions, accuracy of those the vote "
      "confirms minus all (iid bootstrap over decisions). `acc_dropped` = accuracy of the agreement-rule decisions the vote rejects; "
      "`p_diff_le0` = bootstrap share with no improvement.\n")
    pp = PT[PT.period.isin(("2010-26", "2016-26")) & PT.h.isin((21, 42))].copy()
    for c in ("acc_agree", "acc_extra", "acc_dropped", "diff", "diff_lo", "diff_hi"):
        pp[c] = (100 * pp[c]).round(1)
    pp["p_diff_le0"] = pp["p_diff_le0"].round(2)
    cols = ["candidate", "h", "period", "n_agree", "n_extra", "acc_agree", "acc_extra", "acc_dropped", "diff", "diff_lo", "diff_hi", "p_diff_le0"]
    for tab in ("paired_weekly", "paired_nonoverlap_on_agree3_stream"):
        A(f"\n{tab} (points):\n")
        A(pp[pp.table == tab][cols].to_markdown(index=False))
    A("\n## 6. Selection and the success bar\n")
    A(f"Declared rule: highest lower Wilson bound of the 2010-15 non-overlapping 21-session accuracy of the extra-vote rule among candidates with "
      f">= {MIN_DEC_PER_YEAR:.0f} such decisions a year. Result: **`{final}`** ({res['status']}).\n")
    S = res["selection"].copy()
    for c in ("accuracy", "lo", "hi", "agree_accuracy"):
        S[c] = (100 * S[c]).round(1)
    A(S.round(2).to_markdown(index=False))
    A(f"\nThe bar for `{final}` (non-overlapping decisions; accuracies in %, gains in points):\n")
    A(res["bar"].round(1).to_markdown(index=False))
    A("")
    for k, v in res["checks"].items():
        A(f"* {k}: **{'yes' if v else 'NO'}**")
    A("\nNote on the count condition: a 42-session non-overlapping stream cannot exceed 6 decisions a year, and the agreement rule itself has "
      "5.3; the count is therefore tested on the 21-session stream only (fixed before results). The '2023-26 not worse' line is met on 20 and 15 "
      "decisions and means nothing by itself.\n")
    A(f"Decisions of `{final}` (extra-vote rule, weekly, 21-session hold) by year:\n")
    A(by_year(res["keep"][final][(21, "weekly")]).round(2).to_markdown(index=False))
    hr = VT[(VT.candidate == final) & (VT.table == "extra_vote") & (VT.h == 21) & VT.period.isin(P3)].copy()
    hr["right_sign_%"] = (100 * hr["accuracy"]).round(1); hr["net_win_%"] = (100 * hr["win_rate_net"]).round(1)
    A("\nHit rates of the final rule at 21 sessions (round-4 format: share with the correct sign before costs, share with positive net P&L):\n")
    A(hr[["mode", "period", "n", "dec_per_year", "right_sign_%", "net_win_%", "gross_bp", "net_bp", "share_long", "chance_acc"]].round(2).to_markdown(index=False))
    A("\n## 7. Timing placebo (the vote made 63 and 126 sessions staler), extra-vote rule, non-overlapping\n")
    for k in PLACEBO:
        A(f"\nPlacebo +{k} sessions (% right, decisions, per year):\n")
        A(_piv(VT, f"placebo+{k}", "nonoverlap"))
        A(f"\nGain over the agreement rule with the +{k} placebo (points):\n")
        A(_num(VT, f"placebo+{k}", "nonoverlap", "gain_pts", hs=HZ))
    A("\n## 8. Daily-stream incremental test (round-3 addendum) and protocol table\n")
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
    A("## 9. Leak checks\n")
    A("No model is fitted in this arm (fixed sign rules; expanding or trailing statistics use data stamped up to each observation; the house score "
      "inside the agreement rule is the selective arm's walk-forward fit). Non-overlapping accuracy, 2010-26 (% right, decisions):\n")
    lk = res["leak"]
    x = lk[lk.period == "2010-26"].copy()
    x["cell"] = x.apply(lambda q: f"{100 * q['accuracy']:.0f} n={int(q['n'])}" if np.isfinite(q["accuracy"]) else "-", axis=1)
    x["col"] = x["rule"] + " " + x["h"].astype(int).astype(str) + "s"
    A(x.pivot_table(index="check", columns="col", values="cell", aggfunc="first").rename_axis(None, axis=1).reset_index().to_markdown(index=False))
    A("\n* (1) Shuffled labels (targets and the 1-session return the house weights are fitted on, three permutations): 43-59 % everywhere, "
      "centred on 50 %.")
    A("* (2) Votes moved forward by 1 / 5 / 21 sessions (staler): no collapse, because nothing was there to collapse; the swings of several points "
      "from a one-session shift show how noisy a 70-110-decision subset is. The look-ahead controls (vote taken from 21 / 63 sessions in the "
      "future) do not help either: the votes are not a label in disguise. Added after the first run: a planted label (vote = sign of the next "
      "21 sessions' return) scores 100 % standalone and 100 % as an extra vote at 21 sessions, so the harness does expose a look-ahead.")
    A("* (3) Vote anatomy (section 2): correlation of every vote with the forward 21- and 63-session return is between -0.12 and +0.16; no vote "
      "uses EUR/USD prices (the balance-sheet ratio is in own currencies; the CISS contains FX volatility, not direction). The stress votes are "
      "mildly correlated with PAST EUR/USD returns (0.1-0.3: stress falls when the euro has risen), i.e. they are weak trend followers.")
    A("* Lag audit: section 1; every observation is at least as old as the stated lag at the session close that uses it.")
    A(f"\n## 10. Variant count\n\n{N_ARMS} candidate votes, each evaluated standalone, as an extra vote and with two placebos; no parameters searched. "
      "One selection (the declared rule). For deflation: 12.\n")
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
