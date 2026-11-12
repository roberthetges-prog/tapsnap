"""Arm X ("options_info"): what the OPTIONS market knows about multi-week EUR/USD direction (round 7).

EVERYTHING IN THIS DOCSTRING (signals, signs, lags, the evaluation, the selection rule) WAS WRITTEN BEFORE ANY ACCURACY
NUMBER WAS COMPUTED. Only data quality was known (spans, gaps, stale runs, the sign convention, the overlap of the two
implied-vol sources, the same-day correlation of risk-reversal changes with spot returns).

DATA (all fetched 2026-11-11; raw copies in data/raw/options_info/, cleaned files data/macro/options_info_*.csv)
  rr25   EUR/USD 1-month 25-delta risk reversal, a GitHub copy of vendor (Bloomberg BGN) data
         https://raw.githubusercontent.com/GerardWu100/geographic-equity-rotation/main/data/RiskReversalData_Clean.csv
         2003-10-02 .. 2026-07-29, 5,874 values. Positive = EUR calls bid over EUR puts (checked on 2008-10, 2010-05,
         2011-11, 2015-01, 2017-04, 2020-03, 2022-03: see the report). Research use only, no live continuation.
  iv     at-the-money implied vol 1M / 3M / 1Y, GitHub copy of vendor data, 2000-01-25 .. 2022-02-22
         https://raw.githubusercontent.com/frederikbachdk/FXVolTrading/master/data/EURUSD.csv
         and the CBOE EuroCurrency volatility index EVZ, FRED EVZCLS, 2007-11-01 .. 2025-03-11 (discontinued).
         STITCH: 1M implied vol = the ATM 1M quote while it exists; afterwards EVZ divided by the median EVZ / ATM-1M
         ratio of the last 250 common sessions before the splice (EVZ is a model-free vol of FXE options and sits
         4-13 % above the ATM quote). The ratio is fitted on data BEFORE the stitched segment only. The stitched series
         ends 2025-03-11; 3M and 1Y exist only to 2022-02-22, so the term-structure slope is undefined after that.
  cftc   CFTC "futures and options combined" history for Euro FX (code 099741): legacy deahistfo_1995_2016.zip and
         deahistfo{2017..2026}.zip (non-commercial / commercial, weekly from 1999-01-05), Traders in Financial Futures
         fin_com_txt_2006_2016.zip and com_fin_txt_{2017..2026}.zip (dealer / asset manager / leveraged, from 2006-06-13),
         all from https://www.cftc.gov/files/dea/history/. OPTIONS-ONLY position = combined minus futures-only (the
         futures-only rows are the project's data/macro/cot_eurofx_deep.csv). It is a delta-weighted aggregate.
  LAGS   daily option quotes: a value stamped d is used from the session whose closing date is >= d + 1 calendar day
         (featstore._align_lagged; the quote time of the copies is unknown, the ATM file's spot column matches the NY
         close of the same date). A daily series is NEVER carried more than 5 sessions (7 calendar days): beyond that
         the signal is undefined. So: RR signals are undefined from 2026-08-06, implied-vol signals from 2025-03-19,
         the term-structure signal from 2022-03-02. CFTC: report date (Tuesday) + 6 days, then the one-day lag, exactly
         as the store builds cot_z52; a weekly value is dropped when no new report has become available for 20 days.
  All rolling statistics use the session grid of the feature store (z252 = trailing 252 sessions, at least 200 values;
  CFTC z52 = trailing 52 weekly reports as for cot_z52).

PRIORS (positive signal = long EUR/USD). The literature says risk reversals mostly REACT to spot: Farhi, Fraiberger,
Gabaix, Ranciere & Verdelhan ("Crash Risk in Currency Markets", NBER w15062 / 2015) find a currency depreciates
contemporaneously when its risk reversal moves against it, and read the level as a disaster-risk PREMIUM; Brunnermeier,
Nagel & Pedersen ("Carry Trades and Currency Crashes", NBER Macro Annual 2008) find the price of crash insurance rises
AFTER a crash and then predicts LOWER, not higher, crash risk. Both imply that an extreme skew is a premium to be earned
by fading it, not a forecast to follow. The scoping pass found one public test on JPY with the same reading.
  (a) 1 rr_fade_extreme  PRIMARY sign for the level: when |z252(RR)| > 2 vote AGAINST the skew (-sign z); else no vote.
                         Citation: Farhi et al. 2015; Brunnermeier et al. 2008 (insurance is dearest after the move).
      2 rr_z_follow      LABELLED ALTERNATIVE: +z252(RR) (skew towards EUR calls => up). Practitioner reading; no
                         academic support I can cite.
  (b) 3 rr_d21           +(21-session change of RR). Weak prior: a change mostly restates the month's spot move.
  (c) 4 rr_spot_div      sign(21-session RR change) when it is OPPOSITE to the sign of the spot return over the same 21
                         sessions (options leaning against the move), else no vote. Follow the options market.
      5 rr_orth          z252(RR) orthogonalised to the trailing 21- and 63-session spot return (walk-forward OLS with
                         intercept, coefficients from rows before the test year), sign followed. This is the Round 7
                         control promoted to a candidate: it is what is left of the skew once the price move is removed.
  (d) vrp = stitched 1M implied vol minus the trailing 21-session realised vol (hourly returns, annualised, vol points).
      6 vrp_level        -z252(vrp). Della Corte, Ramadorai & Sarno ("Volatility risk premia and exchange rate
                         predictability", JFE 2016): currencies whose volatility insurance is expensive (implied high
                         against realised) DEPRECIATE over the next month, cheap ones appreciate; verified from the
                         abstract. Caveat stated in advance: theirs is a CROSS-SECTIONAL sort of currencies against the
                         dollar; a single pair's time series is a weaker analogue (EUR/USD vol is the same number for
                         both currencies). Londono & Zhou (JFE 2017) report 1-4 month predictability of dollar pairs
                         from the world currency variance premium; I could not verify their sign, so it is not used.
      7 vrp_d21          -(21-session change of vrp): insurance getting dearer => EUR down. Same source, weak.
      8 agree3_vrp_gate  VRP as a CONDITIONING variable: the agreement rule only when vrp is on one side of its
                         trailing-252 mean. I can cite nothing for which side, so the side is TAKEN FROM THE TRAINING
                         WINDOW: for test year Y the side on which the agreement rule's weekly 21-session calls with a
                         label known before Y were more often right (house score walk-forward from 2006; at least 20
                         calls on each side, else no vote that year). A gate has no direction of its own.
  (e) 9 ts_slope         +z252(ATM 1M - ATM 1Y). Ornelas & Mauad ("Implied volatility term structure and exchange rate
                         predictability", Int. J. Forecasting 2019): for developed currencies the LOW-slope (flat or
                         inverted) currencies are bought against the dollar and the steep ones sold. I read their slope
                         as long minus short tenor (abstract only; not verified in the full text), so an inverted
                         EUR/USD curve (1M above 1Y) votes EUR up. The opposite, safe-haven reading (stress => dollar)
                         was already tested in this project and was right 41 % of the time (arm liquidity_stress).
  (f) 10 opt_nc_z52      z52 of the options-only non-commercial net position / futures open interest, FOLLOWED (the
                         same direction in which the project uses futures positioning, sign(cot_z52)).
      11 opt_fut_div     sign(opt_nc_z52) when it DISAGREES with sign(cot_z52), else no vote: follow the options book
                         when option and futures speculators disagree. No citation; weak prior.
      12 opt_lev_z52     z52 of the options-only net position of leveraged funds / TFF futures open interest (from
                         2006-06), followed. Arm G found no trader group specially informed in futures.
  Variant count for deflation: these 12 candidates = 12 AND rules. Controls (orthogonalised copies, stale copies, the
  JPY replication) are not selected from.

EVALUATION (HOWTO_ARMS.md rounds 5 and 7; helpers and conventions of eurusd.arms.selective)
  0 Reconciliation: the agreement rule rebuilt with selective.house_score_wf must reproduce arm N's 56 / 59 / 61 / 72 %
    non-overlapping (n = 291 / 156 / 89 / 61), 2010-26.
  1 Standalone: direction = sign(vote); accuracy at 21 / 42 / 63 sessions on weekly decisions and on the greedy
    non-overlapping stream (Wilson interval), 2010-26 / 2016-26 / 2023-26, decisions per year next to each.
  2 Extra vote: (a) AND rule = agreement rule speaks AND the vote equals its direction, against the agreement rule alone
    and against the agreement rule on the sessions where the signal is defined ("same span": the fair baseline for a
    series that ends early); (b) OUTSIDE = sign(vote) on sessions where the three old signals do NOT agree; (c) paired
    differences on the weekly grid with a circular block bootstrap (block 2h/5 weeks, 2000 draws): AND minus same-span
    agreement, and confirmed minus contradicted agreement calls.
  3 Daily stream: weekly tranches of the final AND rule held 21 sessions (selective.book_time_exit, 1.2 pips per unit
    turnover); protocol table; meta.combine(["weak_signals","regime_trend","options_info"], "EW") against the two-way
    combination; daily P&L correlations.
  4 Timing placebo: the signal made 63 and 126 sessions staler; AND rule, standalone and outside re-evaluated.
  5 Round 7 controls: correlation of every signal with cot_z52, d_spread2y_20, the house score and the trailing 21- and
    63-session spot return; the R2 of the signal on the two spot returns; standalone and AND accuracy of the signal
    ORTHOGONALISED to them (walk-forward residual, as candidate 5).
  6 Replication (round 6 lesson): the identical RR rules (2, 1, 3, 5) on USD/JPY and EUR/JPY, whose 1M 25-delta risk
    reversals are in the same file, against Fed H.10 noon rates. Standalone accuracy only.
  SELECTION RULE (the round-5 rule of the earlier arms): final = the candidate whose AND rule has the highest LOWER
    Wilson bound of the 2010-2015 non-overlapping 21-session accuracy among candidates with at least 6 non-overlapping
    21-session decisions a year in 2010-2015. If none has 6 a year there is NO final rule; the stream written to disk
    is then the highest lower bound among all candidates, flagged as failing.
  SUCCESS BAR (round 5): the AND rule beats the agreement rule by >= 3 accuracy points at 21 AND 42 sessions on
    non-overlapping decisions in BOTH 2010-26 and 2016-26 with at least 6 decisions a year, is not worse in 2023-26, and
    the placebo loses at least half of the gain. Fixed before results: (i) the gain is measured against the SAME-SPAN
    agreement rule (the plain difference is printed too); (ii) the agreement rule itself makes 9.3 (21 sessions) and
    5.3 (42 sessions) non-overlapping decisions a year, so the count is judged on the 21-session stream; (iii) a signal
    with no decision in 2023-26 cannot pass "not worse in 2023-26".
  Leak checks: (1) labels permuted (300 draws); (2) the signal shifted FORWARD in time (-21 sessions, look-ahead) and
    +1 / +5 / +21 staler; a truncation test (raw data cut at five dates, that date's row must be unchanged); (3) the
    correlation of every signal with past returns, the old votes and the forward label.
"""
from __future__ import annotations

import math
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.arms import selective as SL  # noqa: E402
from eurusd.featstore import _align_lagged  # noqa: E402
from eurusd.wf import report  # noqa: E402

MACRO = ROOT / "data" / "macro"
RAW = ROOT / "data" / "raw" / "options_info"
RES = ROOT / "experiments" / "results" / "arms"
ARM = "options_info"
N_ARMS = 12
FETCHED = "2026-11-11"
HORIZONS = (21, 42, 63)
SEL_H = 21
MIN_DEC_PER_YEAR = 6.0
PLACEBO_SHIFTS = (63, 126)
LEAK_SHIFTS = (1, 5, 21, -21)
MAX_CARRY_DAYS = 7          # 5 sessions: a daily quote is never carried further
CFTC_STALE_DAYS = 20
EUROFX_CODE = "099741"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
PERIODS3 = (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026))

URL_RR = "https://raw.githubusercontent.com/GerardWu100/geographic-equity-rotation/main/data/RiskReversalData_Clean.csv"
URL_ATM = "https://raw.githubusercontent.com/frederikbachdk/FXVolTrading/master/data/EURUSD.csv"
URL_EVZ = "https://fred.stlouisfed.org/graph/fredgraph.csv?id=EVZCLS"
URL_CFTC = "https://www.cftc.gov/files/dea/history/"
CFTC_LEGACY = ["deahistfo_1995_2016.zip"] + [f"deahistfo{y}.zip" for y in range(2017, 2027)]
CFTC_TFF = ["fin_com_txt_2006_2016.zip"] + [f"com_fin_txt_{y}.zip" for y in range(2017, 2027)]

SIGNALS = (  # name, family, kind, prior
    ("rr_fade_extreme", "a", "vote", "- skew when |z252(RR)| > 2 (PRIMARY level sign: the skew is a premium, fade it)"),
    ("rr_z_follow", "a", "cont", "+ z252(RR): skew towards EUR calls => up (labelled ALTERNATIVE)"),
    ("rr_d21", "b", "cont", "+ 21-session change of RR"),
    ("rr_spot_div", "c", "vote", "+ sign of the RR change when it is opposite to the spot move of the same 21 sessions"),
    ("rr_orth", "c", "cont", "+ z252(RR) orthogonalised to the trailing 21- and 63-session spot return"),
    ("vrp_level", "d", "cont", "- z252(implied minus realised vol): expensive insurance => EUR down (Della Corte et al.)"),
    ("vrp_d21", "d", "cont", "- 21-session change of implied minus realised vol"),
    ("agree3_vrp_gate", "d", "gate", "agreement rule only on the VRP side that was better in the training window"),
    ("ts_slope", "e", "cont", "+ z252(ATM 1M - 1Y): inverted curve => EUR up (Ornelas & Mauad); ends 2022-02"),
    ("opt_nc_z52", "f", "cont", "+ z52 of options-only non-commercial net / futures OI (follow, as cot_z52)"),
    ("opt_fut_div", "f", "vote", "+ sign(opt_nc_z52) when it disagrees with sign(cot_z52)"),
    ("opt_lev_z52", "f", "cont", "+ z52 of options-only leveraged-fund net / TFF futures OI (follow)"),
)
NAMES = [s[0] for s in SIGNALS]
KIND = {s[0]: s[2] for s in SIGNALS}
PRIOR = {s[0]: s[3] for s in SIGNALS}
# the continuous variable behind each signal that the Round 7 control orthogonalises (None: nothing to orthogonalise)
UNDERLYING = {"rr_fade_extreme": "u_rr_z_neg", "rr_z_follow": "rr_z_follow", "rr_d21": "rr_d21", "rr_spot_div": "rr_d21",
              "rr_orth": "rr_orth", "vrp_level": "vrp_level", "vrp_d21": "vrp_d21", "agree3_vrp_gate": None, "ts_slope": "ts_slope",
              "opt_nc_z52": "opt_nc_z52", "opt_fut_div": "u_opt_minus_fut", "opt_lev_z52": "opt_lev_z52"}


# ================================================================ cached fetch and cleaning
def _curl(url: str, dest: Path, ua: str | None = None, tries: int = 4) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    err = ""
    for k in range(tries):
        cmd = ["curl", "--http1.1", "-sS", "-m", "300", "-o", str(dest), "-w", "%{http_code}"]
        if ua:
            cmd += ["-A", ua]
        r = subprocess.run(cmd + [url], capture_output=True, text=True)
        if r.stdout.strip() == "200" and dest.exists() and dest.stat().st_size > 500:
            return
        err = f"http {r.stdout.strip()} {r.stderr.strip()[:200]}"
        time.sleep(3 * (k + 1))
    raise RuntimeError(f"fetch failed: {url}: {err}")


def _read_cot_zip(p: Path) -> pd.DataFrame:
    with zipfile.ZipFile(p) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".txt")]
        with z.open(names[0]) as fh:
            df = pd.read_csv(fh, dtype=str, low_memory=False, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    return df


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.strip().str.replace(",", ""), errors="coerce")


def _run_len(s: pd.Series) -> pd.Series:
    """Length of the run of identical consecutive values each row belongs to."""
    run = (s.diff() != 0).cumsum()
    return run.map(run.value_counts())


def _clean_rr() -> pd.DataFrame:
    d = pd.read_csv(RAW / "rr_github.csv", encoding="utf-8-sig")
    d.columns = ["date", "rr25_1m_eurusd", "rr25_1m_usdjpy", "rr25_1m_eurjpy"]
    d["date"] = pd.to_datetime(d["date"])
    d = d.sort_values("date").drop_duplicates("date")
    d = d[d[["rr25_1m_eurusd", "rr25_1m_usdjpy", "rr25_1m_eurjpy"]].notna().any(axis=1)].reset_index(drop=True)
    e = d["rr25_1m_eurusd"]
    d["eurusd_stale_run"] = _run_len(e.dropna()).reindex(d.index)
    d["eurusd_gap_days"] = d.loc[e.notna(), "date"].diff().dt.days.reindex(d.index)
    d["source"] = "github GerardWu100/geographic-equity-rotation (copy of Bloomberg BGN)"
    d["source_url"] = URL_RR
    d["fetched"] = FETCHED
    d["date"] = d["date"].dt.strftime("%Y-%m-%d")
    return d


def _clean_iv() -> tuple[pd.DataFrame, dict]:
    a = pd.read_csv(RAW / "atm_github.csv").dropna(subset=["Dates"])
    a["date"] = pd.to_datetime(a["Dates"])
    a = a.sort_values("date").drop_duplicates("date").set_index("date")
    a = a.rename(columns={"EURUSDV1M": "atm_1m", "EURUSDV3M": "atm_3m", "EURUSDV1Y": "atm_1y", "EURUSDPX_LAST": "atm_file_spot"})
    e = pd.read_csv(RAW / "fred_EVZCLS.csv")
    e.columns = ["date", "evz"]
    e["date"] = pd.to_datetime(e["date"])
    e["evz"] = pd.to_numeric(e["evz"], errors="coerce")
    e = e.dropna().set_index("date")["evz"]
    j = pd.concat([a[["atm_1m", "atm_3m", "atm_1y", "atm_file_spot"]], e], axis=1, sort=True)
    ov = j[["atm_1m", "evz"]].dropna()
    ratio = ov["evz"] / ov["atm_1m"]
    k = float(ratio.iloc[-250:].median())                       # fitted BEFORE the stitched segment
    splice = ov.index[-1]
    j["iv_1m"] = j["atm_1m"]
    late = j.index > a["atm_1m"].last_valid_index()
    j.loc[late, "iv_1m"] = j.loc[late, "evz"] / k
    j["iv_1m_source"] = np.where(j["atm_1m"].notna(), "atm_1m (github copy of Bloomberg)", np.where(j["iv_1m"].notna(), f"EVZCLS (FRED) / {k:.4f}", ""))
    j["evz_stale_run"] = _run_len(j["evz"].dropna()).reindex(j.index)
    resid = ov["evz"] / k - ov["atm_1m"]
    b = np.polyfit(ov["atm_1m"], ov["evz"], 1)
    chk = {"overlap_days": int(len(ov)), "overlap_first": str(ov.index[0].date()), "overlap_last": str(splice.date()),
           "corr_level": float(ov.corr().iloc[0, 1]), "corr_d1": float(ov.diff().corr().iloc[0, 1]), "corr_d5": float(ov.diff(5).corr().iloc[0, 1]),
           "corr_d21": float(ov.diff(21).corr().iloc[0, 1]), "ratio_median_all": float(ratio.median()), "ratio_p05": float(ratio.quantile(0.05)),
           "ratio_p95": float(ratio.quantile(0.95)), "ratio_used_last250": k, "ols_slope": float(b[0]), "ols_intercept": float(b[1]),
           "mapped_minus_atm_mean_all": float(resid.mean()), "mapped_minus_atm_sd_all": float(resid.std()),
           "mapped_minus_atm_mean_last250": float(resid.iloc[-250:].mean()), "mapped_minus_atm_sd_last250": float(resid.iloc[-250:].std()),
           "ratio_by_year": {int(y): round(float(v), 3) for y, v in ratio.groupby(ratio.index.year).median().items()}}
    out = j.reset_index().rename(columns={"index": "date"})
    out["source_url_atm"] = URL_ATM
    out["source_url_evz"] = URL_EVZ
    out["fetched"] = FETCHED
    out["date"] = out["date"].dt.strftime("%Y-%m-%d")
    return out, chk


def _clean_cftc() -> pd.DataFrame:
    leg = []
    for f in CFTC_LEGACY:
        df = _read_cot_zip(RAW / f)
        code = next(c for c in df.columns if "Contract Market Code" in c)
        df = df[df[code].astype(str).str.strip() == EUROFX_CODE].copy()
        df["src_file"] = f
        leg.append(df)
    l = pd.concat(leg, ignore_index=True)
    name_col = next(c for c in l.columns if "Market and Exchange" in c)
    assert l[name_col].str.strip().str.startswith("EURO FX - ").all(), l[name_col].unique()
    col = lambda prefix: next(c for c in l.columns if c.strip().startswith(prefix))  # noqa: E731
    L = pd.DataFrame({"report_date": pd.to_datetime(l[next(c for c in l.columns if "YYYY-MM-DD" in c)].str.strip())})
    for a, b in (("Open Interest (All)", "c_oi"), ("Noncommercial Positions-Long (All)", "c_nc_long"), ("Noncommercial Positions-Short (All)", "c_nc_short"),
                 ("Noncommercial Positions-Spreading (All)", "c_nc_spread"), ("Commercial Positions-Long (All)", "c_comm_long"),
                 ("Commercial Positions-Short (All)", "c_comm_short"), ("Nonreportable Positions-Long (All)", "c_nr_long"),
                 ("Nonreportable Positions-Short (All)", "c_nr_short")):
        L[b] = _num(l[col(a)]).values
    L["src_legacy_combined"] = l["src_file"].values
    L = L.sort_values("report_date").drop_duplicates("report_date").set_index("report_date")
    tff = []
    for f in CFTC_TFF:
        df = _read_cot_zip(RAW / f)
        df = df[df["CFTC_Contract_Market_Code"].astype(str).str.strip() == EUROFX_CODE].copy()
        df["src_file"] = f
        tff.append(df)
    t = pd.concat(tff, ignore_index=True)
    assert t["Market_and_Exchange_Names"].str.strip().str.startswith("EURO FX - ").all()
    Tt = pd.DataFrame({"report_date": pd.to_datetime(t["As_of_Date_In_Form_YYMMDD"].astype(str).str.strip().str.zfill(6), format="%y%m%d")})
    for a, b in (("Open_Interest_All", "c_tff_oi"), ("Dealer_Positions_Long_All", "c_dealer_long"), ("Dealer_Positions_Short_All", "c_dealer_short"),
                 ("Asset_Mgr_Positions_Long_All", "c_am_long"), ("Asset_Mgr_Positions_Short_All", "c_am_short"),
                 ("Lev_Money_Positions_Long_All", "c_lev_long"), ("Lev_Money_Positions_Short_All", "c_lev_short"),
                 ("Other_Rept_Positions_Long_All", "c_other_long"), ("Other_Rept_Positions_Short_All", "c_other_short")):
        Tt[b] = _num(t[a]).values
    Tt["src_tff_combined"] = t["src_file"].values
    Tt = Tt.sort_values("report_date").drop_duplicates("report_date").set_index("report_date")
    fut = pd.read_csv(MACRO / "cot_eurofx_deep.csv", parse_dates=["report_date"]).set_index("report_date")
    fut = fut[["oi", "nc_long", "nc_short", "comm_long", "comm_short", "tff_oi", "dealer_long", "dealer_short", "am_long", "am_short",
               "lev_long", "lev_short"]].add_prefix("f_")
    J = L.join(Tt, how="outer").join(fut, how="outer").sort_index()
    J["opt_oi"] = J["c_oi"] - J["f_oi"]
    J["opt_nc_net"] = (J["c_nc_long"] - J["c_nc_short"]) - (J["f_nc_long"] - J["f_nc_short"])
    J["opt_comm_net"] = (J["c_comm_long"] - J["c_comm_short"]) - (J["f_comm_long"] - J["f_comm_short"])
    J["fut_nc_net"] = J["f_nc_long"] - J["f_nc_short"]
    for g in ("lev", "am", "dealer"):
        J[f"opt_{g}_net"] = (J[f"c_{g}_long"] - J[f"c_{g}_short"]) - (J[f"f_{g}_long"] - J[f"f_{g}_short"])
    J["opt_nc_net_pct_fut_oi"] = J["opt_nc_net"] / J["f_oi"]
    J["fut_nc_net_pct_fut_oi"] = J["fut_nc_net"] / J["f_oi"]
    J["opt_lev_net_pct_fut_oi"] = J["opt_lev_net"] / J["f_tff_oi"]
    J["src_futures_only"] = "data/macro/cot_eurofx_deep.csv (CFTC deacot*.zip, fut_fin_txt_*.zip, fin_fut_txt_2006_2016.zip)"
    J["source_url"] = URL_CFTC
    J["fetched"] = FETCHED
    out = J.reset_index()
    out["report_date"] = out["report_date"].dt.strftime("%Y-%m-%d")
    return out


def fetch_all(refresh: bool = False, verbose: bool = True) -> tuple[pd.DataFrame, dict]:
    """Cached fetch: downloads every raw file once into data/raw/options_info/ and writes the cleaned series
    data/macro/options_info_{rr25,iv,cftc_options}.csv. Returns (catalogue, implied-vol overlap check)."""
    jobs = [("rr_github.csv", URL_RR, None), ("atm_github.csv", URL_ATM, None), ("fred_EVZCLS.csv", URL_EVZ, None)]
    jobs += [(f, URL_CFTC + f, UA) for f in CFTC_LEGACY + CFTC_TFF]
    for name, url, ua in jobs:
        p = RAW / name
        if refresh or not p.exists() or p.stat().st_size < 500:
            _curl(url, p, ua)
            time.sleep(0.5)
    outs = {"rr25": MACRO / f"{ARM}_rr25.csv", "iv": MACRO / f"{ARM}_iv.csv", "cftc": MACRO / f"{ARM}_cftc_options.csv", "chk": MACRO / f"{ARM}_iv_overlap_check.csv"}
    if refresh or not all(p.exists() for p in outs.values()):
        _clean_rr().to_csv(outs["rr25"], index=False)
        iv, chk = _clean_iv()
        iv.to_csv(outs["iv"], index=False)
        pd.Series({k: v for k, v in chk.items() if k != "ratio_by_year"} | {f"ratio_{y}": v for y, v in chk["ratio_by_year"].items()}).rename("value").to_csv(outs["chk"], index_label="item")
        _clean_cftc().to_csv(outs["cftc"], index=False)
    chk = pd.read_csv(outs["chk"], index_col=0)["value"].to_dict()
    rr = pd.read_csv(outs["rr25"])
    iv = pd.read_csv(outs["iv"])
    cf = pd.read_csv(outs["cftc"])
    span = lambda d, c, dc="date": (int(d[c].notna().sum()), d.loc[d[c].notna(), dc].iloc[0], d.loc[d[c].notna(), dc].iloc[-1])  # noqa: E731
    rows = []
    for f, d, c, src, dc in ((outs["rr25"], rr, "rr25_1m_eurusd", URL_RR, "date"), (outs["iv"], iv, "atm_1m", URL_ATM, "date"), (outs["iv"], iv, "atm_1y", URL_ATM, "date"),
                             (outs["iv"], iv, "evz", URL_EVZ, "date"), (outs["iv"], iv, "iv_1m", "stitched", "date"),
                             (outs["cftc"], cf, "opt_nc_net", URL_CFTC + "deahistfo*.zip", "report_date"),
                             (outs["cftc"], cf, "opt_lev_net", URL_CFTC + "fin_com_txt_2006_2016.zip, com_fin_txt_*.zip", "report_date")):
        n, a, b = span(d, c, dc)
        rows.append({"file": str(f.relative_to(ROOT)), "column": c, "rows": n, "first": a, "last": b, "source": src, "fetched": FETCHED})
    cat = pd.DataFrame(rows)
    if verbose:
        print(cat.to_string(index=False), flush=True)
    return cat, chk


def load_raw() -> dict:
    rr = pd.read_csv(MACRO / f"{ARM}_rr25.csv", parse_dates=["date"]).set_index("date")
    iv = pd.read_csv(MACRO / f"{ARM}_iv.csv", parse_dates=["date"]).set_index("date")
    cf = pd.read_csv(MACRO / f"{ARM}_cftc_options.csv", parse_dates=["report_date"]).set_index("report_date")
    return {"rr": rr["rr25_1m_eurusd"].dropna(), "rr_usdjpy": rr["rr25_1m_usdjpy"].dropna(), "rr_eurjpy": rr["rr25_1m_eurjpy"].dropna(),
            "iv_1m": iv["iv_1m"].dropna(), "atm_1m": iv["atm_1m"].dropna(), "atm_1y": iv["atm_1y"].dropna(),
            "opt_nc": cf["opt_nc_net_pct_fut_oi"].dropna(), "opt_lev": cf["opt_lev_net_pct_fut_oi"].dropna()}


DAILY_KEYS = ("rr", "rr_usdjpy", "rr_eurjpy", "iv_1m", "atm_1m", "atm_1y")


def truncate_raw(R: dict, asof: pd.Timestamp) -> dict:
    """The raw data as held on calendar date `asof` under the declared lags (daily stamp d from d + 1 day; a CFTC
    report from report date + 6 days + 1 day). Leak check only."""
    out = {}
    for k, s in R.items():
        lag = 1 if k in DAILY_KEYS else 7
        out[k] = s[s.index + pd.Timedelta(days=lag) <= asof]
    return out


# ================================================================ signals
def _cdate(D: pd.DataFrame) -> pd.DatetimeIndex:
    return pd.DatetimeIndex(pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None))


def _on_grid(s: pd.Series, cdate: pd.DatetimeIndex, lag_days: int, max_age: int) -> np.ndarray:
    """Last value stamped <= closing date - lag_days; NaN when that stamp is more than max_age days older than that."""
    s = s.dropna()
    if s.empty:
        return np.full(len(cdate), np.nan)
    v = _align_lagged(s, cdate, lag_days).values
    stamp = _align_lagged(pd.Series(s.index.values.astype("datetime64[ns]").astype("int64").astype(float), index=s.index), cdate, lag_days).values
    age = (cdate.values.astype("datetime64[ns]").astype("int64") - stamp) / 86400e9 - lag_days
    return np.where(age <= max_age, v, np.nan)


def _z(x: np.ndarray, win: int = 252, minp: int = 200) -> np.ndarray:
    s = pd.Series(x)
    return ((s - s.rolling(win, min_periods=minp).mean()) / s.rolling(win, min_periods=minp).std()).values


def _weekly_z52(s: pd.Series, cdate: pd.DatetimeIndex) -> np.ndarray:
    z = ((s - s.rolling(52).mean()) / s.rolling(52).std()).dropna()
    z.index = z.index + pd.Timedelta(days=6)
    return _on_grid(z, cdate, 1, CFTC_STALE_DAYS)


def wf_residual(y: np.ndarray, X: np.ndarray, year: np.ndarray, min_train: int = 500) -> np.ndarray:
    """Residual of y on [1, X] with coefficients from rows of EARLIER calendar years only (yearly expanding window)."""
    out = np.full(len(y), np.nan)
    ok = np.isfinite(y) & np.isfinite(X).all(axis=1)
    A = np.column_stack([np.ones(len(y)), X])
    for Y in sorted(set(year)):
        tr = ok & (year < Y)
        te = ok & (year == Y)
        if tr.sum() < min_train or te.sum() == 0:
            continue
        beta, *_ = np.linalg.lstsq(A[tr], y[tr], rcond=None)
        out[te] = y[te] - A[te] @ beta
    return out


def spot_controls(D: pd.DataFrame) -> np.ndarray:
    """Trailing 21- and 63-session log returns of EUR/USD ending at the PREVIOUS close (the stamp of the option data)."""
    lc = np.log(D["close"]).shift(1)
    return np.column_stack([(lc - lc.shift(21)).values * 1e4, (lc - lc.shift(63)).values * 1e4])


def build_signals(D: pd.DataFrame, R: dict | None = None) -> pd.DataFrame:
    """The 11 directional signals on the session grid (positive = long EUR/USD; 0 = no vote; NaN = undefined), the VRP
    state used by the gate candidate, and the continuous variables behind the three vote-type signals (u_*)."""
    R = load_raw() if R is None else R
    cdate = _cdate(D)
    year = D.index.year.values
    S = pd.DataFrame(index=D.index)
    XC = spot_controls(D)
    # ---- risk reversal
    rr = _on_grid(R["rr"], cdate, 1, MAX_CARRY_DAYS)
    z = _z(rr)
    S["rr_raw"] = rr
    S["rr_fade_extreme"] = np.where(np.isfinite(z), np.where(np.abs(z) > 2.0, -np.sign(z), 0.0), np.nan)
    S["rr_z_follow"] = z
    d21 = pd.Series(rr).diff(21).values
    S["rr_d21"] = d21
    S["rr_spot_div"] = np.where(np.isfinite(d21) & np.isfinite(XC[:, 0]), np.where(np.sign(d21) * np.sign(XC[:, 0]) < 0, np.sign(d21), 0.0), np.nan)
    S["rr_orth"] = wf_residual(z, XC, year)
    S["u_rr_z_neg"] = -z
    # ---- implied minus realised vol
    iv = _on_grid(R["iv_1m"], cdate, 1, MAX_CARRY_DAYS)
    rv = (D["rv_21d_bp"].shift(1) * math.sqrt(252) / 100.0).values
    vrp = iv - rv
    zv = _z(vrp)
    S["iv_1m"], S["rv_21"], S["vrp"] = iv, rv, vrp
    S["vrp_level"] = -zv
    S["vrp_d21"] = -pd.Series(vrp).diff(21).values
    S["vrp_state"] = np.where(np.isfinite(zv), np.where(zv > 0, 1.0, -1.0), np.nan)     # +1 = insurance dear vs its own year
    # ---- term structure (ATM file only)
    slope = _on_grid(R["atm_1m"], cdate, 1, MAX_CARRY_DAYS) - _on_grid(R["atm_1y"], cdate, 1, MAX_CARRY_DAYS)
    S["ts_raw"] = slope
    S["ts_slope"] = _z(slope)
    # ---- CFTC options-only positioning
    zo = _weekly_z52(R["opt_nc"], cdate)
    S["opt_nc_z52"] = zo
    cz = D["cot_z52"].values
    S["opt_fut_div"] = np.where(np.isfinite(zo) & np.isfinite(cz), np.where(np.sign(zo) * np.sign(cz) < 0, np.sign(zo), 0.0), np.nan)
    S["u_opt_minus_fut"] = zo - cz
    S["opt_lev_z52"] = _weekly_z52(R["opt_lev"], cdate)
    return S.replace([np.inf, -np.inf], np.nan)


def vrp_gate(ctx: SL.Ctx, T: dict, state: np.ndarray, min_side: int = 20) -> tuple[np.ndarray, pd.DataFrame]:
    """Candidate 8. gate[i] = +1 (open) / -1 (closed) / NaN. For test year Y the open side of the VRP state is the one
    on which the agreement rule's weekly 21-session calls with a label known before Y were more often right."""
    hs = SL.house_score_wf(ctx, years=list(range(2006, 2027)))
    sg = np.sign(hs)
    agree = np.isfinite(hs) & (sg != 0) & (np.sign(ctx.G["cot_z52"].values) == sg) & (np.sign(ctx.G["d_spread2y_20"].values) == sg)
    t = T[f"sign{SEL_H}"]
    idx = SL.weekly_idx(agree & np.isfinite(state), np.isfinite(t.long))
    hit = (np.where(sg[idx] > 0, t.long[idx], t.short[idx]) > 0).astype(float)
    gate = np.full(len(state), np.nan)
    rows = []
    for Y in SL.YEARS:
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC").value
        k = (t.end[idx] != SL.NAT) & (t.end[idx] < start)
        hi, lo = k & (state[idx] > 0), k & (state[idx] < 0)
        r = {"test_year": Y, "n_high": int(hi.sum()), "acc_high": float(hit[hi].mean()) if hi.sum() else np.nan,
             "n_low": int(lo.sum()), "acc_low": float(hit[lo].mean()) if lo.sum() else np.nan, "open_side": ""}
        if hi.sum() >= min_side and lo.sum() >= min_side:
            side = 1.0 if r["acc_high"] > r["acc_low"] else -1.0
            r["open_side"] = "high VRP" if side > 0 else "low VRP"
            te = (ctx.year == Y) & np.isfinite(state)
            gate[te] = np.where(state[te] == side, 1.0, -1.0)
        rows.append(r)
    return gate, pd.DataFrame(rows)


# ================================================================ evaluation helpers (conventions of arm R / arm N)
def old_votes(ctx: SL.Ctx) -> dict:
    hs = SL.house_score_wf(ctx)
    sg = np.sign(hs)
    cot, spr = np.sign(ctx.G["cot_z52"].values), np.sign(ctx.G["d_spread2y_20"].values)
    base = np.isfinite(hs) & (sg != 0)
    return {"hs": hs, "sg": sg, "cot": cot, "spr": spr, "base": base, "agree": base & (cot == sg) & (spr == sg)}


def eval_rule(ctx: SL.Ctx, T: dict, speak: np.ndarray, dirs: np.ndarray, tag: dict, horizons=HORIZONS, keep: dict | None = None) -> list[dict]:
    rows = []
    for h in horizons:
        t = T[f"sign{h}"]
        valid = np.isfinite(t.long)
        for mode in ("weekly", "nonoverlap"):
            idx = SL.weekly_idx(speak, valid) if mode == "weekly" else SL.seq_idx(speak, valid, t.hold)
            dec = SL.decision_frame(ctx, t, idx, dirs, None)
            if keep is not None:
                keep[(h, mode)] = dec
            for r in SL.cell_stats(ctx, t, dec, speak, mode):
                rows.append({**tag, "h": h, "mode": mode, **r})
    return rows


def paired_boot(ctx: SL.Ctx, t: SL.Target, sa: np.ndarray, da: np.ndarray, sb: np.ndarray, db: np.ndarray, a: int, b: int,
                reps: int = 2000, seed: int = 7) -> dict:
    """acc(rule A) - acc(rule B) on the weekly grid of years a..b; both rules resampled with the SAME circular blocks."""
    valid = np.isfinite(t.long)
    g = np.arange(0, len(valid), SL.STEP)
    g = g[valid[g]]
    g = g[(ctx.year[g] >= a) & (ctx.year[g] <= b)]
    out = {"n_a": 0, "n_b": 0, "acc_a": np.nan, "acc_b": np.nan, "diff": np.nan, "lo": np.nan, "hi": np.nan, "p_le0": np.nan}
    if len(g) < 40:
        return out
    xa, xb = sa[g].astype(float), sb[g].astype(float)
    ha = xa * (np.where(da[g] > 0, t.long[g], t.short[g]) > 0)
    hb = xb * (np.where(db[g] > 0, t.long[g], t.short[g]) > 0)
    out.update({"n_a": int(xa.sum()), "n_b": int(xb.sum())})
    if xa.sum() < 5 or xb.sum() < 5:
        return out
    out.update({"acc_a": float(ha.sum() / xa.sum()), "acc_b": float(hb.sum() / xb.sum())})
    out["diff"] = out["acc_a"] - out["acc_b"]
    block = max(2, int(math.ceil(2 * t.h / SL.STEP)))
    Tn = len(g)
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(Tn / block))
    starts = rng.integers(0, Tn, size=(reps, nb))
    idx = ((starts[:, :, None] + np.arange(block)[None, None, :]) % Tn).reshape(reps, -1)[:, :Tn]
    na, nbb = xa[idx].sum(1), xb[idx].sum(1)
    ok = (na > 0) & (nbb > 0)
    d = ha[idx].sum(1)[ok] / na[ok] - hb[idx].sum(1)[ok] / nbb[ok]
    out.update({"lo": float(np.quantile(d, 0.025)), "hi": float(np.quantile(d, 0.975)), "p_le0": float((d <= 0).mean())})
    return out


def _cell(V: pd.DataFrame, **kw) -> pd.Series | None:
    m = np.ones(len(V), bool)
    for k, v in kw.items():
        m &= (V[k] == v).values
    x = V[m]
    return x.iloc[0] if len(x) else None


def _vote(series: pd.Series, k: int, sg: np.ndarray, gate: bool) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(sign of the vote, defined, has a vote) of a signal made k sessions staler. A gate votes with the agreement
    direction when open and against it when closed."""
    v = series.shift(k).values if k else series.values
    if gate:
        v = v * sg
    s = np.sign(v)
    defined = np.isfinite(v)
    return np.where(defined, s, 0.0), defined, defined & (s != 0)


# ================================================================ main computation
def compute(cost_pips: float = 1.2, verbose: bool = True) -> dict:
    cat, ivchk = fetch_all(verbose=verbose)
    D = SL.load_data()
    ctx = SL.make_ctx(D, cost_pips)
    T = SL.build_targets(D)
    R = load_raw()
    S = build_signals(D, R)
    O = old_votes(ctx)
    sg, agree, base = O["sg"], O["agree"], O["base"]
    gate, gate_log = vrp_gate(ctx, T, S["vrp_state"].values)
    S["agree3_vrp_gate"] = gate
    XC = spot_controls(D)
    for nm in NAMES:                                   # Round 7 control: every signal orthogonalised to the spot returns
        u = UNDERLYING[nm]
        if u is not None:
            S[f"orth__{nm}"] = S[u].values if nm == "rr_orth" else wf_residual(S[u].values, XC, ctx.year)
    rows, decs, paired = [], {}, []
    keep = {}
    rows += eval_rule(ctx, T, agree, sg, {"signal": "-", "rule": "agree3"}, horizons=(10, 21, 42, 63), keep=keep)
    decs["agree3"] = keep
    for nm in NAMES:
        is_gate = KIND[nm] == "gate"
        ss, defined, has = _vote(S[nm], 0, sg, is_gate)
        keep = {}
        sp_and = agree & has & (ss == sg)
        rows += eval_rule(ctx, T, sp_and, sg, {"signal": nm, "rule": "and"}, keep=keep)
        decs[nm] = keep
        rows += eval_rule(ctx, T, agree & has & (ss == -sg), sg, {"signal": nm, "rule": "agree3_contradicted"})
        rows += eval_rule(ctx, T, agree & defined, sg, {"signal": nm, "rule": "agree3_same_span"})
        if KIND[nm] == "vote":          # added after the first run: agreement calls on which a vote-type signal is silent
            rows += eval_rule(ctx, T, agree & defined & ~has, sg, {"signal": nm, "rule": "agree3_no_vote"})
        if not is_gate:
            rows += eval_rule(ctx, T, has & base, ss, {"signal": nm, "rule": "standalone"})
            rows += eval_rule(ctx, T, base & ~agree & has, ss, {"signal": nm, "rule": "outside"})
        for k in PLACEBO_SHIFTS + LEAK_SHIFTS:
            sk, dk, hk = _vote(S[nm], k, sg, is_gate)
            keep = {}
            rows += eval_rule(ctx, T, agree & hk & (sk == sg), sg, {"signal": nm, "rule": f"and_shift{k:+d}"}, keep=keep)
            if k in PLACEBO_SHIFTS:
                decs[f"{nm}__stale{k}"] = keep
            if not is_gate:
                rows += eval_rule(ctx, T, hk & base, sk, {"signal": nm, "rule": f"standalone_shift{k:+d}"})
                if k in PLACEBO_SHIFTS:
                    rows += eval_rule(ctx, T, base & ~agree & hk, sk, {"signal": nm, "rule": f"outside_shift{k:+d}"})
        if UNDERLYING[nm] is not None:
            so, do, ho = _vote(S[f"orth__{nm}"], 0, sg, False)
            rows += eval_rule(ctx, T, ho & base, so, {"signal": nm, "rule": "orth_standalone"})
            rows += eval_rule(ctx, T, agree & ho & (so == sg), sg, {"signal": nm, "rule": "orth_and"})
            rows += eval_rule(ctx, T, agree & do, sg, {"signal": nm, "rule": "orth_same_span"})
        for h in HORIZONS:
            t = T[f"sign{h}"]
            for lab, a, b in PERIODS3:
                r1 = paired_boot(ctx, t, sp_and, sg, agree & defined, sg, a, b)
                r2 = paired_boot(ctx, t, sp_and, sg, agree & has & (ss == -sg), sg, a, b)
                paired.append({"signal": nm, "h": h, "period": lab, "n_and": r1["n_a"], "n_agree_same_span": r1["n_b"], "acc_and": r1["acc_a"],
                               "acc_agree_same_span": r1["acc_b"], "diff": r1["diff"], "diff_lo": r1["lo"], "diff_hi": r1["hi"], "p_le0": r1["p_le0"],
                               "n_contradicted": r2["n_b"], "acc_contradicted": r2["acc_b"], "split": r2["diff"], "split_lo": r2["lo"], "split_hi": r2["hi"],
                               "split_p_le0": r2["p_le0"]})
        if verbose:
            print(f"  signal {nm}: done", flush=True)
    # fixed VRP conditioning diagnostic (no selection): the agreement rule on each side of the VRP state
    st = S["vrp_state"].values
    for lab_, side in (("vrp_high", 1.0), ("vrp_low", -1.0)):
        rows += eval_rule(ctx, T, agree & (st == side), sg, {"signal": "vrp_state", "rule": f"agree3_{lab_}"})
    V = pd.DataFrame(rows)
    return {"cat": cat, "ivchk": ivchk, "D": D, "ctx": ctx, "T": T, "R": R, "S": S, "O": O, "V": V, "paired": pd.DataFrame(paired), "decs": decs,
            "gate_log": gate_log, "XC": XC}


def select_final(V: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    rows = []
    for nm in NAMES:
        c = _cell(V, signal=nm, rule="and", h=SEL_H, mode="nonoverlap", period="2010-15")
        rows.append({"signal": nm, "n_2010-15": int(c["n"]), "dec_per_year_2010-15": c.get("dec_per_year", np.nan), "accuracy_2010-15": c.get("accuracy", np.nan),
                     "lo_2010-15": c.get("lo", np.nan), "hi_2010-15": c.get("hi", np.nan)})
    Sx = pd.DataFrame(rows)
    Sx["eligible"] = Sx["dec_per_year_2010-15"] >= MIN_DEC_PER_YEAR
    el = Sx[Sx["eligible"] & Sx["lo_2010-15"].notna()]
    if len(el):
        final, status = el.sort_values("lo_2010-15", ascending=False)["signal"].iloc[0], "selected by the declared rule"
    else:
        pool = Sx[Sx["lo_2010-15"].notna()]
        final = pool.sort_values("lo_2010-15", ascending=False)["signal"].iloc[0]
        status = "NO candidate has 6 decisions a year in 2010-15 - nominal stream only (fails the declared rule)"
    Sx["final"] = Sx["signal"] == final
    return Sx, final, status


def bar_table(V: pd.DataFrame, nm: str) -> pd.DataFrame:
    """The round-5 success bar, cell by cell, for one candidate's AND rule (non-overlapping decisions)."""
    rows = []
    g = lambda c, k: (c.get(k, np.nan) if c is not None else np.nan)  # noqa: E731
    for h in (21, 42, 63):
        for lab in ("2010-26", "2016-26", "2023-26"):
            a = _cell(V, signal=nm, rule="and", h=h, mode="nonoverlap", period=lab)
            b = _cell(V, signal="-", rule="agree3", h=h, mode="nonoverlap", period=lab)
            s = _cell(V, signal=nm, rule="agree3_same_span", h=h, mode="nonoverlap", period=lab)
            r = {"h": h, "period": lab, "agree3_acc": b["accuracy"], "agree3_n": int(b["n"]), "agree3_per_year": b["dec_per_year"],
                 "same_span_acc": g(s, "accuracy"), "same_span_n": int(s["n"]), "and_acc": g(a, "accuracy"), "and_lo": g(a, "lo"), "and_hi": g(a, "hi"),
                 "and_n": int(a["n"]), "and_per_year": g(a, "dec_per_year")}
            r["gain_pts"] = 100 * (r["and_acc"] - r["same_span_acc"])
            r["gain_vs_full_pts"] = 100 * (r["and_acc"] - r["agree3_acc"])
            for k in PLACEBO_SHIFTS:
                p = _cell(V, signal=nm, rule=f"and_shift{k:+d}", h=h, mode="nonoverlap", period=lab)
                r[f"placebo{k}_acc"] = g(p, "accuracy")
                r[f"placebo{k}_n"] = int(p["n"])
                r[f"placebo{k}_gain_pts"] = 100 * (r[f"placebo{k}_acc"] - r["same_span_acc"])
            rows.append(r)
    return pd.DataFrame(rows)


def bar_verdict(B: pd.DataFrame) -> dict:
    g = lambda h, lab, c: float(B[(B.h == h) & (B.period == lab)][c].iloc[0])  # noqa: E731
    v = {}
    v["gain_ok"] = all(g(h, lab, "gain_pts") >= 3.0 for h in (21, 42) for lab in ("2010-26", "2016-26"))
    v["count21_ok"] = all(g(21, lab, "and_per_year") >= MIN_DEC_PER_YEAR for lab in ("2010-26", "2016-26"))
    v["count42_ok"] = all(g(42, lab, "and_per_year") >= MIN_DEC_PER_YEAR for lab in ("2010-26", "2016-26"))
    v["not_worse_2023"] = all(g(h, "2023-26", "gain_pts") >= 0 for h in (21, 42))      # NaN (no decision) fails
    pl = []
    for h in (21, 42):
        for lab in ("2010-26", "2016-26"):
            gain = g(h, lab, "gain_pts")
            pl.append(all(g(h, lab, f"placebo{k}_gain_pts") <= 0.5 * gain for k in PLACEBO_SHIFTS) if gain > 0 else False)
    v["placebo_ok"] = all(pl)
    v["met"] = bool(v["gain_ok"] and v["count21_ok"] and v["not_worse_2023"] and v["placebo_ok"])
    return v


def controls_table(res: dict) -> pd.DataFrame:
    """Round 7: what each signal is correlated with (2010-26, sessions where it is defined), and the R2 on spot."""
    D, S, O, XC = res["D"], res["S"], res["O"], res["XC"]
    y10 = D.index.year.values >= 2010
    refs = {"cot_z52": D["cot_z52"].values, "d_spread2y_20": D["d_spread2y_20"].values, "house_score": O["hs"], "ret_21d": XC[:, 0], "ret_63d": XC[:, 1]}
    rows = []
    for nm in NAMES:
        if KIND[nm] == "gate":
            continue
        col = UNDERLYING[nm] if KIND[nm] == "vote" else nm
        x = S[col].values.astype(float)
        vote = S[nm].values.astype(float)
        ok = y10 & np.isfinite(x)
        r = {"signal": nm, "variable": col, "first": str(S[nm].first_valid_index())[:10], "last": str(S[nm].last_valid_index())[:10],
             "defined_2010-26": float(np.isfinite(vote[y10]).mean()), "votes_2010-26": float((np.isfinite(vote[y10]) & (vote[y10] != 0)).mean()),
             "share_long": float((vote[y10] > 0).sum() / max((np.isfinite(vote[y10]) & (vote[y10] != 0)).sum(), 1)),
             "sign_flips_per_year": float((pd.Series(np.sign(vote[y10])).diff().abs() > 0).sum() / (y10.sum() / 252))}
        for k, v in refs.items():
            m = ok & np.isfinite(v)
            r[f"corr_{k}"] = float(np.corrcoef(x[m], v[m])[0, 1]) if m.sum() > 50 else np.nan
        m = ok & np.isfinite(XC).all(axis=1)
        A = np.column_stack([np.ones(m.sum()), XC[m]])
        beta, *_ = np.linalg.lstsq(A, x[m], rcond=None)
        r["r2_on_spot_21_63"] = float(1 - ((x[m] - A @ beta) ** 2).sum() / ((x[m] - x[m].mean()) ** 2).sum())
        for k, v in (("cot", O["cot"]), ("spr", O["spr"]), ("house", O["sg"])):
            m = y10 & np.isfinite(vote) & (vote != 0) & np.isfinite(v) & (v != 0)
            r[f"sign_agree_{k}"] = float((np.sign(vote[m]) == v[m]).mean()) if m.sum() else np.nan
        for h in (21, 63):
            f = res["T"][f"sign{h}"].long
            m = ok & np.isfinite(f)
            r[f"corr_fwd{h}"] = float(np.corrcoef(x[m], f[m])[0, 1]) if m.sum() > 50 else np.nan
        rows.append(r)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- replication on the two yen pairs in the same file
def jpy_replication(R: dict) -> pd.DataFrame:
    """The identical RR rules on USD/JPY and EUR/JPY (1M 25-delta risk reversals from the same file; positive = calls on
    the FIRST currency of the pair), Fed H.10 noon rates, signal lagged one calendar day. Standalone accuracy."""
    jp = pd.read_csv(MACRO / "fred_DEXJPUS.csv", parse_dates=["date"]).set_index("date")["value"].astype(float).dropna()
    eu = pd.read_csv(MACRO / "fred_DEXUSEU.csv", parse_dates=["date"]).set_index("date")["value"].astype(float).dropna()
    px = {"USDJPY": jp, "EURJPY": (jp * eu).dropna(), "EURUSD_h10": eu}
    rrs = {"USDJPY": R["rr_usdjpy"], "EURJPY": R["rr_eurjpy"], "EURUSD_h10": R["rr"]}
    rows = []
    for pair, p in px.items():
        p = p[p.index >= "2003-01-01"]
        idx = p.index
        lc = np.log(p.values)
        year = idx.year.values
        rr = _on_grid(rrs[pair], idx, 1, MAX_CARRY_DAYS)
        z = _z(rr)
        lcl = pd.Series(lc).shift(1)
        XC = np.column_stack([(lcl - lcl.shift(21)).values * 1e4, (lcl - lcl.shift(63)).values * 1e4])
        sigs = {"rr_z_follow": z, "rr_fade_extreme": np.where(np.isfinite(z), np.where(np.abs(z) > 2, -np.sign(z), 0.0), np.nan),
                "rr_d21": pd.Series(rr).diff(21).values, "rr_orth": wf_residual(z, XC, year)}
        n = len(lc)
        for h in HORIZONS:
            f = np.full(n, np.nan)
            f[:n - h] = lc[h:] - lc[:n - h]
            for nm, s in sigs.items():
                for k in (0, 63):
                    v = pd.Series(s).shift(k).values if k else s
                    sp = np.isfinite(v) & (v != 0) & np.isfinite(f)
                    for mode in ("weekly", "nonoverlap"):
                        ii = SL.weekly_idx(sp, np.isfinite(f)) if mode == "weekly" else SL.seq_idx(sp, np.isfinite(f), np.full(n, float(h)))
                        for lab, a, b in PERIODS3[:2]:
                            jj = ii[(year[ii] >= a) & (year[ii] <= b)]
                            hit = (np.sign(v[jj]) * f[jj] > 0)
                            acc = float(hit.mean()) if len(jj) else np.nan
                            lo, hi = SL.wilson(acc, len(jj)) if (mode == "nonoverlap" and len(jj)) else (np.nan, np.nan)
                            rows.append({"pair": pair, "signal": nm, "shift": k, "h": h, "mode": mode, "period": lab, "n": len(jj), "accuracy": acc,
                                         "lo": lo, "hi": hi, "base_up": float((f[(year >= a) & (year <= b) & np.isfinite(f)] > 0).mean())})
    return pd.DataFrame(rows)


def leak_checks(res: dict, final: str, reps: int = 300) -> dict:
    ctx, T, S, O, D, R = res["ctx"], res["T"], res["S"], res["O"], res["D"], res["R"]
    sg, agree = O["sg"], O["agree"]
    out = {}
    rng = np.random.default_rng(3)
    rows = []
    for h in HORIZONS:
        t = T[f"sign{h}"]
        valid = np.isfinite(t.long) & (ctx.year >= 2010)
        vi = np.where(valid)[0]
        g = np.arange(0, len(valid), SL.STEP)
        g = g[valid[g]]
        for nm in dict.fromkeys([final, "rr_z_follow", "rr_orth"]):
            ss, defined, has = _vote(S[nm], 0, sg, KIND[nm] == "gate")
            rules = [("and", agree & has & (ss == sg), sg)] + ([] if KIND[nm] == "gate" else [("standalone", has & O["base"], ss)])
            for rule, sp, dr in rules:
                gi = g[sp[g]]
                if len(gi) == 0:
                    continue
                real = float((np.where(dr[gi] > 0, t.long[gi], t.short[gi]) > 0).mean())
                acc = []
                for _ in range(reps):
                    perm = np.arange(len(valid))
                    perm[vi] = rng.permutation(vi)
                    L = t.long[perm]
                    acc.append(float((np.where(dr[gi] > 0, L[gi], -L[gi]) > 0).mean()))
                acc = np.array(acc)
                rows.append({"signal": nm, "rule": rule, "h": h, "n_weekly": len(gi), "real_acc": real, "shuffled_mean": acc.mean(),
                             "shuffled_p05": np.quantile(acc, 0.05), "shuffled_p95": np.quantile(acc, 0.95), "p_shuffled_ge_real": float((acc >= real).mean())})
    out["shuffle"] = pd.DataFrame(rows)
    rows = []
    cdate = _cdate(D)
    cols = [c for c in NAMES if KIND[c] != "gate"] + ["vrp_state", "u_opt_minus_fut"]
    for d0 in ("2012-06-29", "2016-11-15", "2020-03-16", "2022-09-30", "2025-02-14"):
        i = int(np.searchsorted(cdate.values, np.datetime64(d0), side="right") - 1)
        St = build_signals(D.iloc[: i + 1], truncate_raw(R, cdate[i]))
        a, b = S[cols].iloc[i].values.astype(float), St[cols].iloc[i].values.astype(float)
        same = np.isclose(a, b, rtol=1e-9, atol=1e-12, equal_nan=True)
        rows.append({"asof": str(cdate[i].date()), "signals_defined": int(np.isfinite(a).sum()), "rows_equal": int(same.sum()), "of": len(a),
                     "max_abs_diff": float(np.nanmax(np.abs(a - b))) if np.isfinite(a - b).any() else 0.0, "mismatch": ",".join(np.array(cols)[~same])})
    out["truncation"] = pd.DataFrame(rows)
    return out


def incremental(final: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    from eurusd.arms import meta
    rows = []
    for lab, arms in (("two-way weak_signals + regime_trend", ["weak_signals", "regime_trend"]),
                      (f"three-way + {ARM}", ["weak_signals", "regime_trend", ARM]),
                      ("three-way + selective (agreement rule book, for reference)", ["weak_signals", "regime_trend", "selective_daily"]),
                      (f"three-way + {ARM} with the signal 63 sessions stale (placebo)", ["weak_signals", "regime_trend", f"{ARM}_stale63"]),
                      (f"three-way + {ARM} with the signal 126 sessions stale (placebo)", ["weak_signals", "regime_trend", f"{ARM}_stale126"])):
        if not (RES / f"{arms[-1]}_positions.parquet").exists():
            continue
        pnl, _ = meta.combine(arms, "EW")
        tb = meta.report_combo(pnl, lab, N_ARMS)
        rows.append(tb[tb.period.isin(["2010-2026", "2016-2026", "2023-2026"])])
    inc = pd.concat(rows, ignore_index=True)
    me = meta.load_arm_daily(ARM)
    cr = []
    for other in ("weak_signals", "regime_trend", "selective_daily", f"{ARM}_stale63", f"{ARM}_stale126"):
        o = meta.load_arm_daily(other)
        if len(o) < 100:
            continue
        j = pd.concat([me, o], axis=1, keys=["me", "o"]).fillna(0.0)
        j = j[j.index.year >= 2010]
        act = j[j["me"] != 0]
        cr.append({"other": other, "corr_all_days": float(j["me"].corr(j["o"])), "corr_active_days": float(act["me"].corr(act["o"])),
                   "corr_2016-26": float(j[j.index.year >= 2016]["me"].corr(j[j.index.year >= 2016]["o"]))})
    return inc, pd.DataFrame(cr)


def _nw_t(x: np.ndarray, lag: int = 21) -> float:
    x = x[np.isfinite(x)]
    n = len(x)
    if n < 50 or x.std() == 0:
        return np.nan
    e = x - x.mean()
    lrv = float((e * e).sum()) / n
    for l in range(1, lag + 1):
        lrv += 2 * (1 - l / (lag + 1)) * float((e[l:] * e[:-l]).sum()) / n
    return float(x.mean() / math.sqrt(lrv / n)) if lrv > 0 else np.nan


def book_diff(streams: dict) -> pd.DataFrame:
    """Added after the first run: daily net P&L of each AND book minus the agreement-rule book (= minus the book of the
    calls the signal does not confirm), mean bp a day and Newey-West t (21 lags), live and with the signal stale."""
    ref = streams["agree3"]["net_bp"]
    rows = []
    for nm in NAMES:
        for tag in ("", "__stale63", "__stale126"):
            d = (streams[nm + tag]["net_bp"] - ref).dropna()
            r = {"signal": nm, "version": tag.replace("__", "") or "live"}
            for lab, a, b in PERIODS3:
                x = d[(d.index.year >= a) & (d.index.year <= b)].values
                r[f"diff_bp_day_{lab}"] = float(x.mean()) if len(x) else np.nan
                r[f"nw_t_{lab}"] = _nw_t(x)
            rows.append(r)
    return pd.DataFrame(rows)


def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True) -> tuple[pd.Series, pd.DataFrame]:
    """Arm entry point: (daily positions of the final AND rule, protocol report). Writes the deliverables."""
    pos, rep, _ = run_full(cost_pips, write, verbose)
    return pos, rep


def run_full(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    res = compute(cost_pips, verbose=verbose)
    ctx, V, D = res["ctx"], res["V"], res["D"]
    Sx, final, status = select_final(V)
    res["selection"], res["final"], res["final_status"] = Sx, final, status
    res["bar_all"] = pd.concat([bar_table(V, nm).assign(signal=nm) for nm in NAMES], ignore_index=True)
    res["bar_verdict_all"] = pd.DataFrame([{"signal": nm, **bar_verdict(bar_table(V, nm))} for nm in NAMES])
    res["controls"] = controls_table(res)
    res["jpy"] = jpy_replication(res["R"])
    reps, streams = [], {}

    def book(dec, cp):
        cx = ctx if cp == cost_pips else SL.make_ctx(D, cp)
        b = SL.book_time_exit(cx, dec, SEL_H, cp)
        return b[b.index.year >= 2010]

    for nm in NAMES + ["agree3"]:
        dec = res["decs"][nm][(SEL_H, "weekly")]
        streams[nm] = book(dec, cost_pips)
        tb = report(streams[nm], periods_per_year=252, name=ARM, n_arms=N_ARMS)
        tb.insert(1, "variant", f"and_{nm}" if nm != "agree3" else "agree3_reference")
        tb["final"] = nm == final
        tb["kind"] = "candidate" if nm != "agree3" else "reference"
        tb["cost_pips"] = cost_pips
        reps.append(tb)
    for nm in NAMES:                   # added after the first run: the same books with the signal 63 / 126 sessions stale
        for k in PLACEBO_SHIFTS:
            streams[f"{nm}__stale{k}"] = book(res["decs"][f"{nm}__stale{k}"][(SEL_H, "weekly")], cost_pips)
            tb = report(streams[f"{nm}__stale{k}"], periods_per_year=252, name=ARM, n_arms=N_ARMS)
            tb.insert(1, "variant", f"and_{nm}_stale{k}")
            tb["final"], tb["kind"], tb["cost_pips"] = False, "placebo_book", cost_pips
            reps.append(tb)
    tb = report(book(res["decs"][final][(SEL_H, "weekly")], 0.6), periods_per_year=252, name=ARM, n_arms=N_ARMS)
    tb.insert(1, "variant", f"and_{final}_cost0.6")
    tb["final"], tb["kind"], tb["cost_pips"] = False, "cost_sensitivity", 0.6
    reps.append(tb)
    rep = pd.concat(reps, ignore_index=True)
    res["book_diff"] = book_diff(streams)
    daily = streams[final].copy()
    daily["fwd_bp"] = D["fwd_1d"].reindex(daily.index)
    daily = daily[["pos", "fwd_bp", "net_bp"]]
    res["report"], res["streams"], res["daily"] = rep, streams, daily
    dec_f = res["decs"][final][(SEL_H, "weekly")]
    by = SL.by_year(dec_f)
    ref = SL.by_year(res["decs"]["agree3"][(SEL_H, "weekly")]).set_index("year")
    by["agree3_decisions"] = by["year"].map(ref["decisions"])
    by["agree3_accuracy"] = by["year"].map(ref["accuracy"])
    res["by_year"] = by
    hits = []
    for lab, a, b in PERIODS3:
        x = dec_f[(dec_f["year"] >= a) & (dec_f["year"] <= b)]
        hits.append({"period": lab, "decisions": len(x), "hit_gross": float(x["hit"].mean()) if len(x) else np.nan,
                     "hit_net": float((x["net_bp"] > 0).mean()) if len(x) else np.nan, "net_bp": float(x["net_bp"].mean()) if len(x) else np.nan})
    res["hit"] = pd.DataFrame(hits)
    res["leak"] = leak_checks(res, final)
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        daily.to_parquet(RES / f"{ARM}_positions.parquet")
        for k in PLACEBO_SHIFTS:
            pl = streams[f"{final}__stale{k}"].copy()
            pl["fwd_bp"] = D["fwd_1d"].reindex(pl.index)
            pl[["pos", "fwd_bp", "net_bp"]].to_parquet(RES / f"{ARM}_stale{k}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        V.insert(0, "arm", ARM) if "arm" not in V else None
        V["final"] = (V["signal"] == final) & (V["rule"] == "and")
        V.to_csv(RES / f"{ARM}_votes.csv", index=False)
        res["paired"].to_csv(RES / f"{ARM}_paired.csv", index=False)
        Sx.to_csv(RES / f"{ARM}_candidates.csv", index=False)
        res["bar_all"].to_csv(RES / f"{ARM}_bar.csv", index=False)
        res["bar_verdict_all"].to_csv(RES / f"{ARM}_bar_verdict.csv", index=False)
        res["controls"].to_csv(RES / f"{ARM}_controls.csv", index=False)
        res["jpy"].to_csv(RES / f"{ARM}_jpy_replication.csv", index=False)
        res["gate_log"].to_csv(RES / f"{ARM}_vrp_gate_log.csv", index=False)
        res["book_diff"].to_csv(RES / f"{ARM}_book_diff.csv", index=False)
        res["by_year"].to_csv(RES / f"{ARM}_by_year.csv", index=False)
        res["hit"].to_csv(RES / f"{ARM}_hit.csv", index=False)
        res["S"].to_parquet(RES / f"{ARM}_signals.parquet")
        res["cat"].to_csv(RES / f"{ARM}_data_catalogue.csv", index=False)
        pd.concat([v.assign(check=k) for k, v in res["leak"].items()], ignore_index=True).to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
        res["incremental"], res["corr"] = incremental(final)
        res["incremental"].to_csv(RES / f"{ARM}_incremental.csv", index=False)
        res["corr"].to_csv(RES / f"{ARM}_pnl_corr.csv", index=False)
    return daily["pos"], rep, res


if __name__ == "__main__":
    import pickle
    pos, rep, res = run_full()
    print(res["selection"].round(3).to_string(index=False))
    print("FINAL:", res["final"], "-", res["final_status"])
    print(res["bar_verdict_all"].to_string(index=False))
    (RES / "logs").mkdir(exist_ok=True)
    keep = {k: res[k] for k in ("V", "paired", "selection", "final", "final_status", "bar_all", "bar_verdict_all", "controls", "jpy", "gate_log",
                                "by_year", "hit", "leak", "incremental", "corr", "report", "cat", "ivchk", "book_diff")}
    with open(RES / "logs" / f"{ARM}_tables.pkl", "wb") as fh:
        pickle.dump(keep, fh)


# ================================================================ report (reports/arm_options_info.md)
def data_quality() -> dict:
    """Data-quality tables for the report (no accuracy): spans, gaps, stale runs, the sign-convention episodes."""
    rr = pd.read_csv(MACRO / f"{ARM}_rr25.csv", parse_dates=["date"]).set_index("date")
    s = rr["rr25_1m_eurusd"].dropna()
    gaps = s.index.to_series().diff().dt.days
    bd = pd.bdate_range(s.index[0], s.index[-1]).difference(s.index)
    run = (s.diff() != 0).cumsum()
    rl = s.groupby(run).size()
    long_runs = [(s[run == r].index[0], int(rl[r])) for r in rl[rl >= 5].index]
    by = pd.DataFrame({"values": s.groupby(s.index.year).size(), "missing business days": pd.Series(1, index=bd).groupby(bd.year).sum(),
                       "runs of >= 5 identical values": pd.Series(1, index=[d.year for d, _ in long_runs]).groupby(level=0).sum(),
                       "share quoted in 0.05 steps": ((s * 20).round(6) % 1 == 0).groupby(s.index.year).mean().round(2),
                       "mean": s.groupby(s.index.year).mean().round(2), "min": s.groupby(s.index.year).min().round(2),
                       "max": s.groupby(s.index.year).max().round(2)}).fillna(0)
    for c in ("values", "missing business days", "runs of >= 5 identical values"):
        by[c] = by[c].astype(int)
    ep = [("2008-10-27", "Lehman aftermath, dollar squeeze, EUR/USD 1.60 -> 1.25", "-"), ("2010-06-04", "Greek crisis, EUR/USD at 1.19", "-"),
          ("2011-11-09", "Italian yields above 7 %, euro break-up fear", "-"), ("2015-01-16", "day after the SNB floor exit, a week before ECB QE", "-"),
          ("2016-06-14", "ahead of the UK referendum (1M tenor spans the vote)", "-"), ("2017-04-18", "ahead of the French election first round", "-"),
          ("2017-04-24", "the day after the first round (Macron first): put premium collapses", "up"),
          ("2020-03-09", "carry unwind / EUR short squeeze, EUR/USD spikes to 1.14-1.15", "+"), ("2020-03-20", "dollar funding squeeze, EUR/USD back to 1.07", "-"),
          ("2022-03-04", "Ukraine invasion, EUR/USD below 1.10", "-"), ("2025-04-11", "April 2025 dollar sell-off, EUR/USD through 1.13", "+")]
    D = pd.read_parquet(SL.FEATURES, columns=["close", "close_time"])
    ny = pd.Series(D["close"].values, index=_cdate(D))
    rows = []
    for d, what, exp in ep:
        d0 = pd.Timestamp(d)
        rows.append({"date": d, "episode": what, "expected sign": exp, "RR 1M 25d": round(float(s.asof(d0)), 2), "change over 5 sessions": round(float(s.asof(d0) - s.shift(5).asof(d0)), 2),
                     "EUR/USD 21-session return, %": round(float(100 * np.log(ny.asof(d0) / ny.shift(21).asof(d0))), 1)})
    j = pd.concat([s.diff(), np.log(ny).diff()], axis=1, sort=True).dropna()
    j.columns = ["drr", "ret"]
    lead = {k: float(j["drr"].corr(j["ret"].shift(-k))) for k in (-2, -1, 0, 1, 2)}
    iv = pd.read_csv(MACRO / f"{ARM}_iv.csv", parse_dates=["date"]).set_index("date")
    px = pd.concat([iv["atm_file_spot"], ny], axis=1, sort=True).dropna()
    px.columns = ["file", "ny"]
    r1, r2 = np.log(px["file"]).diff(), np.log(px["ny"]).diff()
    e = iv["evz"].dropna()
    st = iv["evz_stale_run"].dropna()
    cf = pd.read_csv(MACRO / f"{ARM}_cftc_options.csv", parse_dates=["report_date"]).set_index("report_date")
    y = cf[cf.index.year >= 2010]
    return {"rr_by_year": by, "episodes": pd.DataFrame(rows), "rr_n": len(s), "rr_nan_rows": int(rr["rr25_1m_eurusd"].isna().sum()),
            "rr_gaps": [(str(d.date()), int(g)) for d, g in gaps[gaps > 5].items()], "rr_long_runs": [(str(d.date()), n) for d, n in long_runs],
            "rr_lead": lead, "rr_big_moves": s.diff().abs().sort_values().tail(4).round(2).to_dict(),
            "px_median_pips": float((px["file"] - px["ny"]).abs().median() * 1e4), "px_corr": {k: float(r1.corr(r2.shift(-k))) for k in (-1, 0, 1)},
            "px_n": len(px), "evz_n": len(e), "evz_stale_share": (st >= 4).groupby(st.index.year).mean().round(2).to_dict(),
            "evz_max_run": int(st.max()), "atm_n": int(iv["atm_1m"].notna().sum()),
            "cftc_weeks": len(cf), "cftc_tff_weeks": int(cf["c_tff_oi"].notna().sum()), "cftc_oi_violations": int((cf["c_oi"] < cf["f_oi"]).sum()),
            "opt_oi_share": float((y["opt_oi"] / y["f_oi"]).median()), "opt_sd": float(y["opt_nc_net_pct_fut_oi"].std()), "fut_sd": float(y["fut_nc_net_pct_fut_oi"].std()),
            "opt_fut_corr": float(y["opt_nc_net_pct_fut_oi"].corr(y["fut_nc_net_pct_fut_oi"])),
            "lev_corr": float(y["opt_lev_net"].corr(y["f_lev_long"] - y["f_lev_short"]))}


def _c(r, ci: bool = True, py: bool = True) -> str:
    if r is None or not np.isfinite(r.get("accuracy", np.nan)):
        return "-"
    s = f"{100 * r['accuracy']:.0f}"
    if ci:
        s += f" [{100 * r['lo']:.0f}-{100 * r['hi']:.0f}]"
    s += f" n={int(r['n'])}"
    if py:
        s += f" ({r['dec_per_year']:.1f}/y)"
    return s


def _grid(V: pd.DataFrame, rules, mode: str, period: str, sigs=None, hs=HORIZONS, ci=True, py=True, short=None) -> pd.DataFrame:
    rows = []
    for nm in (sigs or NAMES):
        r = {"signal": nm}
        for rule in rules:
            for h in hs:
                lab = (short or {}).get(rule, rule)
                r[f"{lab} {h}"] = _c(_cell(V, signal=nm, rule=rule, h=h, mode=mode, period=period), ci, py)
        rows.append(r)
    return pd.DataFrame(rows)


def write_report(K: dict | None = None, path: Path | None = None) -> str:
    import pickle
    if K is None:
        with open(RES / "logs" / f"{ARM}_tables.pkl", "rb") as fh:
            K = pickle.load(fh)
    V, B, P = K["V"], K["bar_all"], K["paired"]
    Q = data_quality()
    chk = {k: (float(v) if str(v).replace(".", "", 1).replace("-", "", 1).isdigit() else v) for k, v in K["ivchk"].items()}
    md = lambda d, **kw: d.to_markdown(index=False, **kw)  # noqa: E731
    out = [HEAD_MD, VERDICT_MD]
    # ---- 1 data
    out.append("## 1 Data: provenance, sign convention, gaps\n")
    out.append(md(K["cat"]))
    out.append(DATA_MD.format(rr_n=Q["rr_n"], rr_nan=Q["rr_nan_rows"], gaps=", ".join(f"{d} ({g} d)" for d, g in Q["rr_gaps"]),
                              nruns=len(Q["rr_long_runs"]), lastrun=Q["rr_long_runs"][-1][0], maxrun=max(n for _, n in Q["rr_long_runs"]),
                              l_2=Q["rr_lead"][-2], l_1=Q["rr_lead"][-1], l0=Q["rr_lead"][0], l1=Q["rr_lead"][1], l2=Q["rr_lead"][2],
                              pxm=Q["px_median_pips"], pxn=Q["px_n"], pc_1=Q["px_corr"][-1], pc0=Q["px_corr"][0], pc1=Q["px_corr"][1]))
    out.append("**Sign-convention check** (value of the series on dates whose skew direction is known from the event):\n")
    out.append(md(Q["episodes"]))
    out.append("\n**Risk reversal by year** (EUR/USD column of the file):\n")
    out.append(md(Q["rr_by_year"].reset_index().rename(columns={"index": "year", "date": "year"})))
    out.append(IV_MD.format(n=int(chk["overlap_days"]), a=chk["overlap_first"], b=chk["overlap_last"], cl=chk["corr_level"], c1=chk["corr_d1"], c5=chk["corr_d5"],
                            c21=chk["corr_d21"], rm=chk["ratio_median_all"], r05=chk["ratio_p05"], r95=chk["ratio_p95"], k=chk["ratio_used_last250"],
                            m250=chk["mapped_minus_atm_mean_last250"], s250=chk["mapped_minus_atm_sd_last250"], mall=chk["mapped_minus_atm_mean_all"],
                            sall=chk["mapped_minus_atm_sd_all"], ry=", ".join(f"{k[6:]} {float(v):.2f}" for k, v in chk.items() if k.startswith("ratio_2")),
                            st=", ".join(f"{y} {100 * v:.0f} %" for y, v in Q["evz_stale_share"].items() if v > 0), mr=Q["evz_max_run"]))
    out.append(CFTC_MD.format(w=Q["cftc_weeks"], tw=Q["cftc_tff_weeks"], viol=Q["cftc_oi_violations"], sh=100 * Q["opt_oi_share"], so=100 * Q["opt_sd"],
                              sf=100 * Q["fut_sd"], c=Q["opt_fut_corr"], lc=Q["lev_corr"]))
    # ---- 2 priors
    out.append("## 2 The 12 candidates and their priors (fixed before any result; citations in the module docstring and at the end)\n")
    out.append(md(pd.DataFrame([{"#": i + 1, "signal": s[0], "family": s[1], "type": s[2], "prior (positive = long EUR/USD)": s[3]} for i, s in enumerate(SIGNALS)])))
    out.append(PRIORS_MD)
    # ---- 3 reconciliation
    x = V[(V.signal == "-") & (V["mode"] == "nonoverlap")]
    rec = pd.DataFrame([{"period": lab, **{f"{h} sessions": _c(_cell(x, h=h, period=lab)) for h in (10, 21, 42, 63)}} for lab in ("2010-26", "2016-26", "2023-26")])
    out.append("## 3 Reconciliation with arm N\n\nThe agreement rule rebuilt here (non-overlapping decisions; accuracy % [Wilson 95 %] n (decisions a year)):\n")
    out.append(md(rec))
    out.append(RECON_MD)
    # ---- 4 standalone
    out.append("## 4 Standalone accuracy of each signal (direction = sign of the vote)\n")
    for lab in ("2010-26", "2016-26", "2023-26"):
        out.append(f"\n**Non-overlapping decisions, {lab}** (accuracy % [Wilson 95 %] n (decisions a year)):\n")
        out.append(md(_grid(V, ["standalone"], "nonoverlap", lab, short={"standalone": "h"})))
    for lab in ("2010-26", "2016-26", "2023-26"):
        out.append(f"\n**Weekly decisions, {lab}** (accuracy % [Newey-West effective-n interval] n; live, then 63 and 126 sessions stale):\n")
        g = _grid(V, ["standalone"], "weekly", lab, short={"standalone": "live"}, py=False)
        for k in PLACEBO_SHIFTS:
            g2 = _grid(V, [f"standalone_shift{k:+d}"], "weekly", lab, ci=False, py=False, short={f"standalone_shift{k:+d}": f"stale{k}"})
            g = g.merge(g2, on="signal")
        out.append(md(g))
    out.append(STANDALONE_MD)
    # ---- 5 controls
    out.append("## 5 Round 7 controls: is it new, or the price move restated?\n")
    C = K["controls"].copy()
    cc = C[["signal", "variable", "last", "votes_2010-26", "share_long", "sign_flips_per_year", "corr_cot_z52", "corr_d_spread2y_20", "corr_house_score",
            "corr_ret_21d", "corr_ret_63d", "r2_on_spot_21_63", "sign_agree_cot", "sign_agree_spr", "sign_agree_house"]].round(2)
    out.append("Correlations on 2010-26 sessions (Pearson, of the continuous variable behind each signal; `sign_agree_*` = share of sessions on which the vote has the sign of that old input):\n")
    out.append(md(cc))
    for lab in ("2010-26", "2016-26"):
        out.append(f"\n**Raw against orthogonalised, {lab}** (weekly decisions, accuracy % n; `sa` = standalone, `and` = extra vote on the agreement rule):\n")
        g = _grid(V, ["standalone", "orth_standalone", "and", "orth_and"], "weekly", lab, sigs=[n for n in NAMES if KIND[n] != "gate"], ci=False, py=False,
                  short={"standalone": "sa", "orth_standalone": "sa orth", "and": "and", "orth_and": "and orth"})
        out.append(md(g))
        out.append(f"\n**The same on non-overlapping decisions, {lab}:**\n")
        g = _grid(V, ["standalone", "orth_standalone", "and", "orth_and"], "nonoverlap", lab, sigs=[n for n in NAMES if KIND[n] != "gate"], ci=False, py=False,
                  short={"standalone": "sa", "orth_standalone": "sa orth", "and": "and", "orth_and": "and orth"})
        out.append(md(g))
    out.append(CONTROLS_MD)
    # ---- 6 extra vote
    out.append("## 6 Each signal as an EXTRA VOTE on the agreement rule\n")
    out.append("### (a) AND rule against the agreement rule, non-overlapping decisions (the measure of the bar)\n")
    b = B[B.h.isin([21, 42])].copy()
    tb = pd.DataFrame({"signal": b["signal"], "h": b["h"], "period": b["period"],
                       "agreement, same span": [f"{100 * a:.0f} n={n}" if np.isfinite(a) else "-" for a, n in zip(b["same_span_acc"], b["same_span_n"])],
                       "AND rule": [f"{100 * a:.0f} [{100 * lo:.0f}-{100 * hi:.0f}] n={n} ({py:.1f}/y)" if np.isfinite(a) else f"- n={n}"
                                    for a, lo, hi, n, py in zip(b["and_acc"], b["and_lo"], b["and_hi"], b["and_n"], b["and_per_year"])],
                       "gain, pts": b["gain_pts"].round(1), "gain vs full-period agreement": b["gain_vs_full_pts"].round(1),
                       "63 stale: acc n": [f"{100 * a:.0f} n={n}" if np.isfinite(a) else "-" for a, n in zip(b["placebo63_acc"], b["placebo63_n"])],
                       "63 stale gain": b["placebo63_gain_pts"].round(1),
                       "126 stale: acc n": [f"{100 * a:.0f} n={n}" if np.isfinite(a) else "-" for a, n in zip(b["placebo126_acc"], b["placebo126_n"])],
                       "126 stale gain": b["placebo126_gain_pts"].round(1)})
    out.append(md(tb))
    out.append("\n**Bar, cell by cell** (gain >= 3 pts at 21 and 42 sessions in 2010-26 and 2016-26; >= 6 non-overlapping 21-session decisions a year; not worse in 2023-26; "
               "each stale copy keeps at most half of the gain):\n")
    out.append(md(K["bar_verdict_all"]))
    out.append("\n### The same on weekly decisions (accuracy % n; `same span` = agreement rule where the signal is defined, `contra` = agreement calls the signal contradicts)\n")
    for lab in ("2010-26", "2016-26", "2023-26"):
        out.append(f"\n*{lab}*\n")
        g = _grid(V, ["agree3_same_span", "and", "and_shift+63", "and_shift+126", "agree3_contradicted"], "weekly", lab, hs=(21, 42, 63), ci=False, py=False,
                  short={"agree3_same_span": "same span", "and": "AND", "and_shift+63": "stale63", "and_shift+126": "stale126", "agree3_contradicted": "contra"})
        out.append(md(g))
    out.append("\n### (c) Paired differences, weekly grid, circular block bootstrap (2000 draws; points; p = share of draws <= 0, one-sided, NOT adjusted for 12 candidates)\n")
    p = P[P.period.isin(["2010-26", "2016-26"])].copy()
    pt = pd.DataFrame({"signal": p["signal"], "h": p["h"], "period": p["period"], "AND acc n": [f"{100 * a:.1f} n={n}" if np.isfinite(a) else f"- n={n}" for a, n in zip(p["acc_and"], p["n_and"])],
                       "agreement same span": [f"{100 * a:.1f} n={n}" if np.isfinite(a) else "-" for a, n in zip(p["acc_agree_same_span"], p["n_agree_same_span"])],
                       "AND - agreement": [f"{100 * d:+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}] p={q:.2f}" if np.isfinite(d) else "-" for d, lo, hi, q in zip(p["diff"], p["diff_lo"], p["diff_hi"], p["p_le0"])],
                       "contradicted acc n": [f"{100 * a:.1f} n={n}" if np.isfinite(a) else f"- n={n}" for a, n in zip(p["acc_contradicted"], p["n_contradicted"])],
                       "confirmed - contradicted": [f"{100 * d:+.1f} [{100 * lo:+.1f}, {100 * hi:+.1f}] p={q:.2f}" if np.isfinite(d) else "-" for d, lo, hi, q in zip(p["split"], p["split_lo"], p["split_hi"], p["split_p_le0"])]})
    out.append(md(pt))
    out.append("\n### (b) Does the signal extend coverage? Calls on sessions where the three old signals do NOT agree (non-overlapping; live, 63 and 126 sessions stale)\n")
    for lab in ("2010-26", "2016-26"):
        out.append(f"\n*{lab}*\n")
        g = _grid(V, ["outside", "outside_shift+63", "outside_shift+126"], "nonoverlap", lab, sigs=[n for n in NAMES if KIND[n] != "gate"], ci=False, py=False,
                  short={"outside": "live", "outside_shift+63": "stale63", "outside_shift+126": "stale126"})
        g1 = _grid(V, ["outside"], "nonoverlap", lab, sigs=[n for n in NAMES if KIND[n] != "gate"], short={"outside": "live"})
        for h in HORIZONS:
            g[f"live {h}"] = g1[f"live {h}"]
        out.append(md(g))
    out.append("\n### VRP as a conditioning variable\n\nThe agreement rule on each side of the VRP state (implied minus realised above / below its trailing-252 mean), fixed split, no selection:\n")
    x = V[V.signal == "vrp_state"]
    rows = []
    for mode in ("weekly", "nonoverlap"):
        for lab in ("2010-26", "2016-26", "2023-26"):
            r = {"decisions": mode, "period": lab}
            for side in ("vrp_high", "vrp_low"):
                for h in HORIZONS:
                    r[f"{side} {h}"] = _c(_cell(x, rule=f"agree3_{side}", h=h, mode=mode, period=lab), ci=(mode == "nonoverlap"), py=False)
            rows.append(r)
    out.append(md(pd.DataFrame(rows)))
    out.append("\nSide chosen for candidate 8 from the training window (weekly 21-session agreement calls with a label known before the test year):\n")
    out.append(md(K["gate_log"].round(3)))
    out.append(EXTRA_MD)
    # ---- 7 selection and final
    out.append("## 7 Selection by the declared rule, and the final rule's record\n")
    out.append(md(K["selection"].round(3)))
    out.append(f"\n**Final: `and_{K['final']}`** - {K['final_status']}.\n")
    fb = B[B.signal == K["final"]]
    out.append(md(fb[["h", "period", "agree3_acc", "agree3_n", "same_span_acc", "same_span_n", "and_acc", "and_lo", "and_hi", "and_n", "and_per_year", "gain_pts",
                      "placebo63_gain_pts", "placebo126_gain_pts"]].round(3)))
    out.append("\nHit rate of the final rule's weekly decisions (21-session hold; gross = correct sign, net = positive after a 2.4-pip round trip):\n")
    out.append(md(K["hit"].round(3)))
    out.append("\nBy year (weekly decisions):\n")
    out.append(md(K["by_year"][["year", "decisions", "long_share", "accuracy", "net_bp", "agree3_decisions", "agree3_accuracy"]].round(3)))
    # ---- 8 daily stream
    out.append("\n## 8 Daily stream and the incremental test (round 3 addendum)\n")
    R = K["report"]
    piv = R[R.period.isin(["2010-2015", "2010-2026", "2016-2026", "2023-2026"])].pivot(index="variant", columns="period", values="sharpe").round(2)
    live = piv[~piv.index.str.contains("stale")].reset_index()
    out.append("Net Sharpe at 1.2 pips of each AND rule as a book of weekly tranches held 21 sessions:\n")
    out.append(md(live))
    st = piv[piv.index.str.contains("stale")].reset_index()
    out.append("\nThe same books with the signal 63 / 126 sessions stale:\n")
    out.append(md(st))
    f = R[(R["final"]) & R.period.isin(["2010-2026", "2016-2026", "2023-2026"])][["period", "n", "sharpe", "t", "mean_bp", "active_frac", "deflated_sharpe_p"]].round(3)
    out.append("\nFinal stream:\n")
    out.append(md(f))
    out.append("\nCombination (meta.combine, EW) and daily P&L correlation of the final stream:\n")
    out.append(md(K["incremental"][["combo", "period", "sharpe", "t"]].round(3)))
    out.append("")
    out.append(md(K["corr"].round(2)))
    out.append("\nDaily net P&L of each AND book MINUS the agreement-rule book (bp a day, Newey-West t with 21 lags):\n")
    out.append(md(K["book_diff"].round(2)))
    out.append(STREAM_MD)
    # ---- 9 replication
    out.append("## 9 Replication of the risk-reversal rules on USD/JPY and EUR/JPY (same file, identical rules, Fed H.10 noon rates)\n")
    J = K["jpy"].copy()
    J["cell"] = [f"{100 * a:.0f} n={n}" if np.isfinite(a) else "-" for a, n in zip(J["accuracy"], J["n"])]
    for lab in ("2010-26", "2016-26"):
        x = J[J.period == lab].pivot_table(index=["pair", "signal", "shift"], columns=["mode", "h"], values="cell", aggfunc="first")
        x.columns = [f"{m} {h}" for m, h in x.columns]
        out.append(f"\n*{lab}* (shift = sessions the signal is made stale)\n")
        out.append(md(x.reset_index()))
    out.append(JPY_MD)
    # ---- 10 leak checks
    out.append("## 10 Leak checks\n\n**(1) Labels permuted** (300 draws, weekly decisions 2010-26):\n")
    out.append(md(K["leak"]["shuffle"].round(3)))
    out.append("\n**(2) Shifted signal** (weekly decisions 2010-26, accuracy % n; +k = k sessions staler, -21 = LOOK-AHEAD of 21 sessions):\n")
    sh = {"and": "AND live", "and_shift+1": "+1", "and_shift+5": "+5", "and_shift+21": "+21", "and_shift-21": "-21 (look-ahead)"}
    out.append(md(_grid(V, list(sh), "weekly", "2010-26", hs=(21,), ci=False, py=False, short=sh)))
    sh = {"standalone": "standalone live", "standalone_shift+1": "+1", "standalone_shift+5": "+5", "standalone_shift+21": "+21", "standalone_shift-21": "-21 (look-ahead)"}
    out.append("")
    out.append(md(_grid(V, list(sh), "weekly", "2010-26", sigs=[n for n in NAMES if KIND[n] != "gate"], hs=(21,), ci=False, py=False, short=sh)))
    out.append("\n**Truncation test** (raw files cut at the date under the declared lags; the row of that date rebuilt and compared):\n")
    out.append(md(K["leak"]["truncation"]))
    out.append("\n**(3) What the signals are** - correlation of each with the FORWARD return (2010-26, daily sessions):\n")
    out.append(md(K["controls"][["signal", "variable", "corr_fwd21", "corr_fwd63", "corr_ret_21d", "corr_ret_63d"]].round(3)))
    out.append(LEAK_MD)
    out.append(TAIL_MD)
    txt = "\n".join(out) + "\n"
    path = path or ROOT / "reports" / f"arm_{ARM}.md"
    path.write_text(txt)
    return txt
