"""Arm AA ("pre_euro"): out-of-time replication of the positioning rule on the Deutsche Mark, 1986-1998.

EVERYTHING IN THIS DOCSTRING WAS WRITTEN ON 2026-11-17 BEFORE ANY OUTCOME OF THE 1986-1998 SAMPLE WAS COMPUTED.
What had been looked at when it was written: the CFTC file's contract names and report dates (to learn the report
frequency), which price / rate sources answer from this session, and a calibration of the rate stand-in on INTEREST
RATE DATA ONLY (no exchange-rate outcome). Nothing is tuned afterwards; a clean fail is reported as a fail.

QUESTION
The only directional information that survived rounds 1-8 is "follow speculative positioning": sign of the 52-week
z-score of CFTC non-commercial net position / open interest (`cot_z52`), alone and inside the three-signal agreement
rule. All of it was found on EUR/USD 1999-2026. Does the identical rule work on the euro's predecessor in 1986-1998?

DATA (provenance, spans and checks are in reports/arm_pre_euro.md)
* Positioning: CFTC legacy futures-only history `deacot1986_2016.zip` (one file FUT86_16.txt, all contracts,
  1986-01-15 .. 2016-12-27). Deutsche Mark = CFTC code 094741, International Monetary Market (CME):
  "GERMAN DEUTSCHE MARK" to 1993-01-19, "DEUTSCHE MARK" after. Context currencies: JPY 097741, CHF 092741,
  CAD 090741, GBP 096741 (old 25,000-pound contract, to 1988-05) + 096742 (62,500-pound contract, from 1988-04; the
  two are added in pounds of notional while both are listed).
* Report frequency found in the file: mid-month and month-end "as of" dates from 1986-01-15 to 1992-09-30
  (162 reports), weekly Tuesdays from 1992-10-06.
* PUBLICATION LAG ASSUMED (the CFTC's own history page says: monthly end-of-month reports published on the 11th-12th
  calendar day of the following month; mid-month and month-end reports from 1990, published the 6th business day
  after the as-of date; a report every two weeks from 1992, published the 3rd business day after; weekly from 2000).
  The stamp below is the calendar day from which a number is treated as public; the signal is then lagged one more
  calendar day exactly like every other series in the project (`_align_lagged(..., 1)`):
      as-of before 1990-01-01      : 13th calendar day of the month after the as-of month, for the month-end AND the
                                     mid-month figure (the mid-month figures are in the file, but the CFTC says only
                                     monthly reports were published then, so they are not allowed to arrive earlier)
      1990-01-01 .. 1992-09-30     : as-of + 11 calendar days (6 business days from a Friday, plus a holiday)
      1992-10-01 .. 1992-12-31     : as-of + 17 days (off-week of a fortnightly release still on the 6-business-day rule)
      1993-01-01 .. 1998-12-31     : as-of + 13 days (weekly figures, but released every two weeks: the off-week figure
                                     comes out on the Friday of the FOLLOWING week = as-of + 10; +13 is the Monday after,
                                     the same convention as the project's modern "Tuesday + 6")
      1999-01-01 onwards           : as-of + 6 days (the project's existing convention; used for reconciliation only)
* z-score: the project's `cot_z52` is rolling(52 reports) on weekly data. Reports were not weekly before 1992-10, so
  the "52-week z" is defined on TIME: z_t = (net_t - mean) / sd (ddof 1) over the reports with as-of date in
  (t - 364 days, t], provided the file starts at least 357 days before t (the span of 52 weekly reports) and the
  window holds at least 20 reports.
  On gap-free weekly data this is the same 52 reports as rolling(52); the reconciliation step measures the difference
  on EUR/USD 1999-2026. Usable span of the signal on the mark: first z at the 1987-01-15 report, public 1987-02-13.
* Price of the mark: the synthetic euro of `swing.load_prices()` = 1.95583 / (DEM per USD), DEM daily = DKK daily
  (Fed H.10 noon) x monthly DEM/DKK. Close (noon fix) only; trustworthy at 21 sessions and longer, not daily.
  Other currencies: Fed H.10 noon rates (data/macro/fred_DEX*.csv), oriented as USD per unit of foreign currency.
* Decision sample of the primary test: every session from the first one with a public z (1987-02) whose h-session
  outcome ends on or before 1998-12-31 (the outcome never crosses into the euro). Label = sign of the h-session log
  return of the synthetic euro; a session is a decision if the signal is non-zero and the label is non-zero.

SCORING (identical to experiments/70_committee.py `acc_row`, the function behind the published 58.3 / 63.3 / 66.7 %)
Phase-averaged non-overlapping accuracy: every session with a call is scored on the next h sessions; the count of
INDEPENDENT decisions is (sessions with a call) / h; the 95 % Wilson interval is taken on that count; decisions per
year = independent decisions / years of the span.
Baselines next to every accuracy: (i) always long; (ii) RANDOM TIMING: the same series of calls (same count, same
long / short mix, same run lengths and spacing) shifted circularly against the outcomes by a random offset of at
least 126 sessions, 1,000 draws: mean, 2.5-97.5 % band, and p = share of draws at least as accurate as the rule.

PRIMARY TEST (one trial, candidate 1)
  rule    side_t = sign(z52 of DEM non-commercial net / open interest), lagged as above; long the synthetic euro when
          speculators are net long the mark relative to their own last year, short otherwise.
  sample  1987-02 .. 1998-12 as defined above.
  PASS BAR: accuracy at 42 sessions > 55.0 % AND accuracy at 21 sessions > 50 % AND accuracy at 63 sessions > 50 %.
  Wording fixed in advance:  "clean pass" = bar met and random-timing p <= 0.10 at 42 sessions;
                             "pass, not distinguishable from random timing" = bar met, p > 0.10;
                             "clean fail" = accuracy at 42 sessions <= 50 %;
                             "fail" = anything else (42-session accuracy in 50-55 %, or a horizon on the wrong side).
  The halves 1987-92 (twice-monthly reports) and 1993-98 (weekly reports) are reported as descriptive splits.

STAND-INS DECLARED BEFORE ANY OUTCOME
* Rate-spread trend. Original: sign of the 20-session change of (euro-area AAA 2-year - US 2-year), daily. A German
  2-year yield before 1999 is not reachable from here (Bundesbank API blocked by the session proxy, nothing on FRED
  or the ECB API). Stand-in: sign of the ONE-MONTH change of  [0.5 x German 3-month interbank + 0.5 x German 10-year
  government yield] - US 2-year,  all three as monthly averages (FRED IR3TIB01DEM156N, IRLTLT01DEM156N, mean of daily
  DGS2); the monthly average of month M is treated as known from the first calendar day of month M+1 (rates are
  market prices), then the usual one-day lag. Chosen on rate data only: in 2004-2026 the monthly change of this
  stand-in has the same sign as the monthly change of the true 2-year spread in 83 % of months (corr 0.79); the
  symmetric blend scored 77 %, 3-month only 69 %, 10-year only 75 %.
* Macro score. Original: the 14-signal house score (weak_signals `tstat` weights fitted walk-forward on EUR/USD).
  Rebuilt for 1987-98 as a FROZEN TRANSFER: the weights and scalers of the last walk-forward fold (fitted on EUR/USD
  rows whose label was known before 2026-01-01; no 1986-98 label is used anywhere), applied to the signals that can
  be rebuilt for the whole span: cot (the mark's z52), spread (the stand-in above, scaled by its own expanding
  standard deviation of past months), mom21, mom63, mom252, usdmom (20-day dollar factor from H.10 GBP JPY CHF AUD
  CAD), tom, season, dow. MISSING, contribute zero: fomc (no announcements before 1994), fv (needs a daily 2-year
  spread), gap (needs true weekend opens), vix (starts 1990), eqrel (no euro-area equity index here before 2003).

THE 12 EVALUATIONS (strict count; nothing else is run on outcomes)
   1  PRIMARY: sign(z52) on the mark, 21 / 42 / 63 sessions, plus the Sharpe of the same rule as a daily stream
      (position = sign(z52) every session, 1.2 pips per unit turnover, `wf.pnl_from_positions`), 1987-98.
   2  secondary (a): agreement-style rule on the mark: positioning sign, rate stand-in sign and frozen macro-subset
      score sign all agree.
   3-6  secondary (b), context: rule 1 unchanged on JPY, GBP, CHF and CAD futures, 1987-98, H.10 prices.
   7-8  secondary (c), control: rule 1 with the signal 63 and 126 sessions stale.
   9  control: rule 1 with one extra week of publication delay.
  10  control: shuffled outcomes (the era's daily returns re-ordered at random, 500 paths, rule unchanged).
  11  descriptive: the legs other than the positioning vote on the mark: rate stand-in sign and the macro-subset
      score WITHOUT its cot component agree.
  12  bridge check: the stand-in agreement rule of (2) rebuilt on EUR/USD 2010-26 (true positioning, the same rate
      stand-in, each fold's own house weights restricted to the same 9 signals), against the original rule's
      58.3 / 63.3 / 66.7 %. It says whether (2) is a fair test of the agreement rule at all.
RECONCILIATION (before any of the above; known numbers, not candidates): the agreement rule 58.3 / 63.3 / 66.7 % at
21 / 42 / 63 sessions (2010-26) through `committee._fold_columns`; the positioning stream's Sharpe by era on Fed H.10
prices (+0.15 2000-02, +0.38 2003-09, +0.82 2010-15, +0.83 2016-22, +0.36 2023-26, arm_regime_dependence.md) with
THIS module's z-score, lag and stream functions; the archive's 1999+ rows against the repo's parsed CFTC files.

POST-HOC ADDENDUM (written 2026-11-17 AFTER the 12 evaluations above had been run and read; the primary test had
failed). Nothing above was changed. Four things were added, none of which can turn the fail into a pass, all labelled
post-hoc in the outputs:
  13  robustness of the fail to the conservative lag: rule 1 with "as-of + 6 days" for every report (the modern
      convention). Before 1993 that is EARLIER than the report was published, so it is an optimistic bound for the
      rule, not a tradable variant.
  14  robustness of the fail to the synthetic price: rule 1 scored at month-ends on an independent price (OECD
      end-of-month DEM spot, FRED CCUSSP01DEM650N) next to the synthetic euro on the same month-ends.
  15  pipeline check, not a rule: a LOOK-AHEAD copy of rule 1 (every report treated as known 30 days BEFORE its as-of
      date). If the scoring code and the orientation are right it must score well above 50 %, because speculators
      chase the price; it shows the fail is not a bug.
  --  pooled Sharpe of the positioning stream across eras (arithmetic on streams already computed: the mark 1987-98
      and EUR/USD 2000-2026 on H.10 with the project's rolling(52) z), split into years inside and outside the
      windows on which the rule was selected (2003-2022).
Also after the fact: the reconciliation of the H.10 Sharpe is shown with both z definitions, because the time-window
z differs from rolling(52) on ONE euro-era report (2001-12-21, |z| < 0.03) and that alone moves the 2000-02 Sharpe
from +0.15 to +0.06.

Run:  PYTHONPATH=src OMP_NUM_THREADS=1 python -m eurusd.arms.pre_euro            (everything)
      PYTHONPATH=src OMP_NUM_THREADS=1 python -m eurusd.arms.pre_euro build      (re-download / re-parse the data)
"""
from __future__ import annotations

import math
import subprocess
import sys
import warnings
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.arms import swing as SW  # noqa: E402
from eurusd.arms.swing import wilson, _ms, _align_lagged  # noqa: E402
from eurusd.wf import pnl_from_positions  # noqa: E402

MACRO = ROOT / "data" / "macro"
RAW = ROOT / "data" / "raw" / "cftc"
RES = ROOT / "experiments" / "results" / "arms"
ARM = "pre_euro"
ARCHIVE = "deacot1986_2016.zip"
ARCHIVE_URL = "https://www.cftc.gov/files/dea/history/deacot1986_2016.zip"
HORIZONS = (21, 42, 63)
N_BASE = 1000
N_SHUFFLE = 500
MIN_OFFSET = 126
SEED = 20261117

# currency: (CFTC codes, {code: pounds-style notional weight}, name must contain, price file, inverted?, pip of the pair)
CONTRACTS = {
    "dem": (("094741",), "DEUTSCHE MARK"),
    "jpy": (("097741",), "JAPANESE YEN"),
    "gbp": (("096741", "096742"), "POUND"),
    "chf": (("092741",), "SWISS FRANC"),
    "cad": (("090741",), "CANADIAN DOLLAR"),
}
GBP_SIZE = {"096741": 25000.0, "096742": 62500.0}
PRICE = {"jpy": ("fred_DEXJPUS.csv", True, 0.01), "gbp": ("fred_DEXUSUK.csv", False, 1e-4),
         "chf": ("fred_DEXSZUS.csv", True, 1e-4), "cad": ("fred_DEXCAUS.csv", True, 1e-4)}
ERAS_PRE = (("1987-98", 1987, 1998), ("1987-92", 1987, 1992), ("1993-98", 1993, 1998))
ERAS_EUR = (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026))
SUBSET = ("cot", "spread", "mom63", "mom21", "tom", "usdmom", "mom252", "season", "dow")     # rebuildable for 1987-98
MISSING = ("fomc", "fv", "gap", "vix", "eqrel")


# ============================================================================= data
def fetch(verbose: bool = True) -> None:
    """CFTC archive (needs a browser User-Agent on GET) and the OECD end-of-month DEM spot from FRED (needs
    --http1.1 and NO browser User-Agent). Nothing is fetched if the files are already there."""
    RAW.mkdir(parents=True, exist_ok=True)
    p = RAW / ARCHIVE
    if not p.exists() or p.stat().st_size < 1_000_000:
        subprocess.run(["curl", "-sS", "-f", "-A", "Mozilla/5.0", "-m", "600", "-o", str(p), ARCHIVE_URL], check=True)
        if verbose:
            print("downloaded", p.name, p.stat().st_size, flush=True)
    q = MACRO / "pre_euro_fred_CCUSSP01DEM650N.csv"
    if not q.exists():
        txt = subprocess.run(["curl", "-sS", "-f", "--http1.1", "-m", "120", "https://fred.stlouisfed.org/graph/fredgraph.csv?id=CCUSSP01DEM650N"],
                             capture_output=True, text=True, check=True).stdout
        import io
        d = pd.read_csv(io.StringIO(txt))
        d.columns = ["date", "value"]
        d["value"] = pd.to_numeric(d["value"], errors="coerce")
        d.dropna().to_csv(q, index=False)
        if verbose:
            print("fetched CCUSSP01DEM650N", len(d), flush=True)


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.strip().str.replace(",", ""), errors="coerce")


def _read_archive() -> pd.DataFrame:
    with zipfile.ZipFile(RAW / ARCHIVE) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".txt")]
        with z.open(names[0]) as fh:
            df = pd.read_csv(fh, dtype=str, low_memory=False, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    return df


def build_cot(verbose: bool = True) -> dict:
    """Parse the archive into data/macro/pre_euro_cot_<ccy>.csv (1986-01-15 .. 1999-12-28; the mark to its last
    report) and cross-check the archive's 1999-2016 rows against the repo's parsed per-year files."""
    df = _read_archive()
    code_col = next(c for c in df.columns if "Contract Market Code" in c)
    name_col = next(c for c in df.columns if "Market and Exchange" in c)
    date_col = next(c for c in df.columns if "YYYY-MM-DD" in c)
    df["code"] = df[code_col].astype(str).str.strip()
    df["name"] = df[name_col].astype(str).str.strip()
    df["report_date"] = pd.to_datetime(df[date_col].str.strip())

    def col(prefix: str) -> str:
        return next(c for c in df.columns if c.strip().startswith(prefix))

    fields = {"open_interest": "Open Interest (All)", "noncomm_long": "Noncommercial Positions-Long (All)",
              "noncomm_short": "Noncommercial Positions-Short (All)", "noncomm_spread": "Noncommercial Positions-Spreading (All)",
              "comm_long": "Commercial Positions-Long (All)", "comm_short": "Commercial Positions-Short (All)",
              "nonrept_long": "Nonreportable Positions-Long (All)", "nonrept_short": "Nonreportable Positions-Short (All)"}
    info = {}
    for ccy, (codes, must) in CONTRACTS.items():
        t = df[df["code"].isin(codes)].copy()
        assert t["name"].str.contains(must).all(), (ccy, t["name"].unique())
        assert t["name"].str.contains("INTERNATIONAL MONETARY MARKET|CHICAGO MERCANTILE EXCHANGE").all(), (ccy, t["name"].unique())
        out = pd.DataFrame({"report_date": t["report_date"], "code": t["code"], "market": t["name"]})
        for k, v in fields.items():
            out[k] = _num(t[col(v)])
        if ccy == "gbp":                                   # two contract sizes listed side by side in 1988-04/05
            w = out["code"].map(GBP_SIZE) / 62500.0
            for k in fields:
                out[k] = out[k] * w
            g = out.groupby("report_date")
            out = pd.concat([g[list(fields)].sum(), g["code"].agg("+".join), g["market"].agg(" + ".join)], axis=1).reset_index()
        out = out.sort_values("report_date").drop_duplicates("report_date").reset_index(drop=True)
        last = "1999-12-31" if ccy != "dem" else "2000-12-31"
        out = out[out["report_date"] <= last]
        out["noncomm_net_pct_oi"] = (100 * (out["noncomm_long"] - out["noncomm_short"]) / out["open_interest"]).round(3)
        out["report_date"] = out["report_date"].dt.strftime("%Y-%m-%d")
        out.to_csv(MACRO / f"pre_euro_cot_{ccy}.csv", index=False)
        d = pd.to_datetime(out["report_date"])
        info[ccy] = {"first": out["report_date"].iloc[0], "last": out["report_date"].iloc[-1], "reports": len(out),
                     "reports_to_1992-09": int((d <= "1992-09-30").sum()), "reports_1992-10_to_1998": int(((d > "1992-09-30") & (d <= "1998-12-31")).sum()),
                     "max_gap_days_weekly_era": int(d[(d > "1992-10-01") & (d <= "1998-12-31")].diff().dt.days.max()),
                     "markets": " | ".join(sorted(set(" + ".join(out["market"].unique()).split(" + "))))}
        if verbose:
            print(ccy, info[ccy], flush=True)
    # ---- cross-check against the repo's per-year parse (1999-2016)
    checks = {}
    eur = df[(df["code"] == "099741") & df["name"].str.startswith("EURO FX")]
    for ccy, codes, repo in (("eur", ("099741",), "cot_eurofx_legacy.csv"), ("jpy", ("097741",), "cot_jpy_legacy.csv"), ("gbp", ("096742",), "cot_gbp_legacy.csv"),
                             ("chf", ("092741",), "cot_chf_legacy.csv"), ("cad", ("090741",), "cot_cad_legacy.csv")):
        t = eur if ccy == "eur" else df[df["code"].isin(codes)]
        t = t[t["report_date"] >= "1999-01-01"].sort_values("report_date").drop_duplicates("report_date")
        a = pd.DataFrame({k: _num(t[col(v)]).values for k, v in fields.items()}, index=pd.DatetimeIndex(t["report_date"]))
        b = pd.read_csv(MACRO / repo, parse_dates=["report_date"]).set_index("report_date")
        common = a.index.intersection(b.index)
        diff = float((a.loc[common, list(fields)] - b.loc[common, list(fields)]).abs().to_numpy().max())
        checks[ccy] = {"rows_archive_1999_2016": len(a), "rows_in_both": len(common), "max_abs_difference": diff}
        if verbose:
            print("archive vs repo", ccy, checks[ccy], flush=True)
    pd.DataFrame(info).T.rename_axis("ccy").to_csv(RES / f"{ARM}_cot_coverage.csv")
    pd.DataFrame(checks).T.rename_axis("ccy").to_csv(RES / f"{ARM}_cot_archive_check.csv")
    return {"coverage": info, "archive_check": checks}


def load_net(ccy: str) -> pd.Series:
    """Non-commercial net / open interest by as-of date."""
    f = MACRO / (f"pre_euro_cot_{ccy}.csv" if ccy != "eur" else "cot_eurofx_legacy.csv")
    d = pd.read_csv(f, parse_dates=["report_date"]).set_index("report_date").sort_index()
    return ((d["noncomm_long"] - d["noncomm_short"]) / d["open_interest"]).dropna()


def avail_stamp(asof: pd.DatetimeIndex, extra_days: int = 0) -> pd.DatetimeIndex:
    """First calendar day on which a report is treated as public (see the module docstring)."""
    out = []
    for d in pd.DatetimeIndex(asof):
        if d < pd.Timestamp("1990-01-01"):
            s = (d.to_period("M") + 1).to_timestamp() + pd.Timedelta(days=12)
        elif d < pd.Timestamp("1992-10-01"):
            s = d + pd.Timedelta(days=11)
        elif d < pd.Timestamp("1993-01-01"):
            s = d + pd.Timedelta(days=17)
        elif d < pd.Timestamp("1999-01-01"):
            s = d + pd.Timedelta(days=13)
        else:
            s = d + pd.Timedelta(days=6)
        out.append(s + pd.Timedelta(days=extra_days))
    return pd.DatetimeIndex(out)


def z52_time(net: pd.Series, window_days: int = 364, min_history_days: int = 357, min_reports: int = 20) -> pd.Series:
    """52-week z-score on a TIME window, so that it means the same thing for twice-monthly and weekly reports."""
    net = net.dropna().sort_index()
    t = net.index.values.astype("datetime64[D]").astype(np.int64)
    v = net.values.astype(float)
    z = np.full(len(v), np.nan)
    for i in range(len(v)):
        if t[i] - t[0] < min_history_days:
            continue
        j = int(np.searchsorted(t, t[i] - window_days, side="right"))
        w = v[j:i + 1]
        if len(w) < min_reports:
            continue
        sd = w.std(ddof=1)
        if sd > 0:
            z[i] = (v[i] - w.mean()) / sd
    return pd.Series(z, index=net.index).dropna()


def stamped(z: pd.Series, extra_days: int = 0, fixed_lag_days: int | None = None) -> pd.Series:
    """z by the day it became public. Two reports made public on the same day: the later as-of date wins.
    fixed_lag_days: ignore the era rules and stamp every report as-of + that many days (post-hoc check 13 only)."""
    idx = avail_stamp(z.index, extra_days) if fixed_lag_days is None else z.index + pd.Timedelta(days=fixed_lag_days)
    s = pd.Series(z.values, index=idx)
    s = s[~s.index.duplicated(keep="last")]
    assert s.index.is_monotonic_increasing
    return s


def aligned_z(ccy: str, dates: pd.DatetimeIndex, extra_days: int = 0, fixed_lag_days: int | None = None, rolling52: bool = False) -> pd.Series:
    net = load_net(ccy)
    z = ((net - net.rolling(52).mean()) / net.rolling(52).std()).dropna() if rolling52 else z52_time(net)
    return pd.Series(_align_lagged(stamped(z, extra_days, fixed_lag_days), dates, 1).values, index=dates)


def price_series(ccy: str) -> tuple[pd.Series, float]:
    """(USD per unit of foreign currency by date, pip of the conventional pair expressed in that orientation's bp)."""
    if ccy == "dem":
        P = SW.load_prices()
        s = pd.Series(P["close"].values, index=pd.DatetimeIndex(P["cdate"]))
        return s[s.index <= "1998-12-31"], 1e-4
    if ccy == "eur":
        s = _ms("fred_DEXUSEU.csv").dropna()
        return s[s > 0], 1e-4
    f, inv, pip = PRICE[ccy]
    s = _ms(f).dropna()
    s = s[s > 0]
    return (1.0 / s if inv else s), pip


def cost_bp_series(ccy: str, px: pd.Series, cost_pips: float) -> pd.Series:
    """Cost per unit turnover in bp: cost_pips of the conventionally quoted pair (USD/JPY pip 0.01)."""
    if ccy in ("dem", "eur", "gbp"):
        return cost_pips * 1e-4 / px * 1e4
    _, _, pip = PRICE[ccy]
    return cost_pips * pip * px * 1e4            # quoted pair = 1 / px


# ============================================================================= scoring
def labels(px: pd.Series) -> pd.DataFrame:
    lc = np.log(px)
    return pd.DataFrame({f"y{h}": np.sign(lc.shift(-h) - lc) for h in HORIZONS} | {"fwd_1d": (lc.shift(-1) - lc) * 1e4}, index=px.index)


def _mask(idx: pd.DatetimeIndex, side: np.ndarray, y: np.ndarray, a: int, b: int) -> np.ndarray:
    return (idx.year >= a) & (idx.year <= b) & (side != 0) & np.isfinite(side) & np.isfinite(y) & (y != 0)


def acc_row(side: pd.Series, y: pd.Series, h: int, a: int, b: int) -> dict:
    """Identical to experiments/70_committee.py acc_row (phase-averaged; n_indep = sessions with a call / h)."""
    s, yy = side.fillna(0.0).values.astype(float), y.values.astype(float)
    idx = pd.DatetimeIndex(side.index)
    m = _mask(idx, s, yy, a, b)
    n = int(m.sum())
    if n == 0:
        return {"n_days": 0, "n_indep": 0.0, "acc": np.nan, "lo": np.nan, "hi": np.nan, "per_year": 0.0, "share_of_days": 0.0, "share_long": np.nan}
    hit = float((s[m] == yy[m]).mean())
    n_ind = n / h
    lo, hi = wilson(int(round(hit * n_ind)), max(int(round(n_ind)), 1))
    era = (idx.year >= a) & (idx.year <= b) & np.isfinite(yy)
    span_years = max((idx[era][-1] - idx[era][0]).days / 365.25, 1e-9)
    return {"n_days": n, "n_indep": round(n_ind, 1), "acc": hit, "lo": lo, "hi": hi, "per_year": n_ind / span_years,
            "share_of_days": n / max(int(era.sum()), 1), "share_long": float((s[m] > 0).mean())}


def baselines(side: pd.Series, y: pd.Series, h: int, a: int, b: int, n_draws: int = N_BASE, seed: int = SEED) -> dict:
    """Always long, and random timing: the same calls shifted circularly against the outcomes inside the era."""
    s, yy = side.fillna(0.0).values.astype(float), y.values.astype(float)
    idx = pd.DatetimeIndex(side.index)
    era = (idx.year >= a) & (idx.year <= b) & np.isfinite(yy)
    s, yy = s[era], yy[era]
    ok = yy != 0
    out = {"always_long": float((yy[ok] > 0).mean()) if ok.any() else np.nan}
    n = len(s)
    obs_m = (s != 0) & ok
    if n < 4 * MIN_OFFSET or obs_m.sum() == 0:
        return out | {"base_mean": np.nan, "base_lo": np.nan, "base_hi": np.nan, "base_p": np.nan}
    obs = float((s[obs_m] == yy[obs_m]).mean())
    rng = np.random.default_rng(seed + h)
    offs = rng.integers(MIN_OFFSET, n - MIN_OFFSET, n_draws)
    acc = np.empty(n_draws)
    for i, k in enumerate(offs):
        r = np.roll(s, int(k))
        m = (r != 0) & ok
        acc[i] = (r[m] == yy[m]).mean() if m.any() else np.nan
    return out | {"base_mean": float(np.nanmean(acc)), "base_lo": float(np.nanpercentile(acc, 2.5)), "base_hi": float(np.nanpercentile(acc, 97.5)),
                  "base_p": float((acc >= obs - 1e-12).mean())}


def score_rule(name: str, sample: str, kind: str, side: pd.Series, L: pd.DataFrame, eras, base: bool = True) -> list[dict]:
    rows = []
    for era, a, b in eras:
        for h in HORIZONS:
            r = {"rule": name, "sample": sample, "kind": kind, "era": era, "h": h, **acc_row(side, L[f"y{h}"], h, a, b)}
            if base:
                r |= baselines(side, L[f"y{h}"], h, a, b)
            rows.append(r)
    return rows


def stream(ccy: str, px: pd.Series, side: pd.Series, L: pd.DataFrame, cost_pips: float = 1.2) -> pd.DataFrame:
    """Daily stream of the sign rule: position = side every session, 1.2 pips per unit turnover."""
    pos = side.fillna(0.0)
    cost = cost_bp_series(ccy, px, cost_pips)
    pnl = pnl_from_positions(pos, L["fwd_1d"], px, cost_pips=0.0)          # gross, then this currency's own cost in bp
    pnl["net_bp"] = pnl["gross_bp"] - pnl["turnover"] * cost
    return pnl


def sharpe_rows(name: str, sample: str, pnl: pd.DataFrame, eras) -> list[dict]:
    rows = []
    for era, a, b in eras:
        x = pnl[(pnl.index.year >= a) & (pnl.index.year <= b)]
        x = x[x["net_bp"].notna()]
        first = np.flatnonzero(x["pos"].values != 0)
        x = x.iloc[first[0]:] if len(first) else x.iloc[:0]
        v = x["net_bp"].values
        if len(v) < 60 or v.std() == 0:
            continue
        sr = float(v.mean() / v.std(ddof=1) * math.sqrt(252))
        blocks = []                                       # 21-session block Sharpe, averaged over the 21 phases
        for ph in range(21):
            w = v[ph:]
            k = len(w) // 21
            if k >= 12:
                bsum = w[:k * 21].reshape(k, 21).sum(axis=1)
                blocks.append(bsum.mean() / bsum.std(ddof=1) * math.sqrt(12))
        rows.append({"rule": name, "sample": sample, "era": era, "sessions": len(v), "years": len(v) / 252.0, "sharpe_daily": sr,
                     "t_daily": float(v.mean() / v.std(ddof=1) * math.sqrt(len(v))), "sharpe_21session_blocks": float(np.mean(blocks)) if blocks else np.nan,
                     "mean_net_bp_per_day": float(v.mean()), "ann_net_pct": float(v.mean() * 252 / 100), "turnover_per_year": float(x["turnover"].sum() / (len(v) / 252.0)),
                     "share_long": float((x["pos"] > 0).mean())})
    return rows


# ============================================================================= stand-ins (declared in the docstring)
def rate_standin() -> pd.Series:
    """One-month change of [0.5 DE 3m interbank + 0.5 DE 10y] - US 2y (monthly averages), stamped on the first
    calendar day of the following month. Returns the change; `rate_standin_sd` its expanding past-only std."""
    de3, de10 = _ms("fred_IR3TIB01DEM156N.csv"), _ms("fred_IRLTLT01DEM156N.csv")
    us2 = _ms("fred_DGS2.csv").resample("MS").mean()
    us2 = us2[us2.index < _ms("fred_DGS2.csv").index[-1].to_period("M").to_timestamp()]      # complete months only
    d = (0.5 * (de3 + de10) - us2).dropna().diff().dropna()
    d.index = d.index + pd.offsets.MonthBegin(1)
    return d


def rate_standin_z(dates: pd.DatetimeIndex) -> tuple[pd.Series, pd.Series]:
    d = rate_standin()
    sd = d.expanding(min_periods=36).std()
    raw = pd.Series(_align_lagged(d, dates, 1).values, index=dates)
    z = (raw / pd.Series(_align_lagged(sd, dates, 1).values, index=dates)).clip(-2, 2) / 2
    return raw, z


def _house_fit(X: pd.DataFrame, train_mask: np.ndarray):
    """The fold fit of committee._fold_columns (14-signal tstat model), returned with the scaled signals."""
    from eurusd.arms import weak_signals as WS
    names = list(WS.SIGNALS)
    fr = X[[f"ws_{k}" for k in names] + ["ws_fwd_1d", "ws_rv"]].copy()
    fr.columns = names + ["fwd_1d", "rv_21d_bp"]
    tr = fr[train_mask & fr["fwd_1d"].notna().values & fr["rv_21d_bp"].notna().values]
    if len(tr) < 750:
        return None, None, names
    fit, _ = WS.make_fit_predict("tstat", "sign", names)
    m = fit(tr)
    Z = WS._scaler_apply(fr[names], m["st"])
    Z = Z.where(fr[names].notna().any(axis=1))
    return m, Z, names


def dem_signals(px: pd.Series, z_cot: pd.Series) -> pd.DataFrame:
    """Raw prior-oriented house signals that can be rebuilt on the pre-1999 frame (same definitions as
    weak_signals.build_raw_signals / featstore)."""
    d = px.index
    lr = lambda k: (np.log(px) - np.log(px.shift(k))) * 1e4  # noqa: E731
    S = pd.DataFrame(index=d)
    S["cot"] = z_cot
    S["mom63"], S["mom21"], S["mom252"] = lr(63), lr(21), -lr(252)
    fx = pd.read_csv(MACRO / "datahub_fx_fed_h10_daily.csv", parse_dates=["date"]).set_index("date")
    parts = []
    for c in ("gbp", "jpy", "chf", "aud", "cad"):
        s = pd.Series(_align_lagged(fx[f"{c}_per_usd"].astype(float), d, 1).values, index=d)
        parts.append((np.log(s) - np.log(s.shift(20))) * 1e4)
    S["usdmom"] = -pd.concat(parts, axis=1).mean(axis=1)
    bd = pd.Series(d, index=d)
    ym = bd.dt.to_period("M")
    from_start = bd.groupby(ym).cumcount() + 1
    to_end = bd.groupby(ym).transform("size") - from_start
    S["tom"] = np.where((to_end <= 1) | (from_start <= 3), -1.0, 0.0)
    dow, month = pd.Series(d.dayofweek, index=d), pd.Series(d.month, index=d)
    nxt_dow = dow.shift(-1).fillna((dow + 1) % 5)
    nxt_month = month.shift(-1).fillna(month)
    S["season"] = np.where(nxt_month == 12, 1.0, np.where(nxt_month == 5, -1.0, 0.0))
    S["dow"] = np.where(nxt_dow == 0, -1.0, np.where(nxt_dow == 4, 1.0, 0.0))
    return S


# ============================================================================= steps
def euro_frame():
    from eurusd import committee as C
    warnings.filterwarnings("ignore")
    return C, C.build_frame()


def reconcile(C, X, verbose: bool = True) -> tuple[pd.DataFrame, pd.Series, dict]:
    """Known euro-era numbers, with this module's scoring functions. Returns (table, agreement side, last-fold model)."""
    rows = []
    # ---- (1) the agreement rule on the committee folds
    ag = pd.Series(np.nan, index=X.index)
    for Y in C.TEST_YEARS:
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC")
        known = (X["yend21"] < start).values & X["y21"].notna().values
        fc = C._fold_columns(X, known)
        r = X.index.year == Y
        ag[r] = fc["@agree"][r]
    ag = ag.fillna(0.0)
    pub = {21: 0.583, 42: 0.633, 63: 0.667}
    bench = pd.read_csv(RES / "committee_benchmark.csv")
    for era, a, b in ERAS_EUR:
        for h in HORIZONS:
            r = acc_row(ag, X[f"y{h}"], h, a, b)
            q = bench[(bench.who == "agreement rule") & (bench.h == h) & (bench.era == era)]
            rows.append({"check": "agreement rule (committee folds)", "era": era, "h": h, "this_module": r["acc"], "published": float(q["acc"].iloc[0]) if len(q) else np.nan,
                         "n_indep": r["n_indep"], "lo": r["lo"], "hi": r["hi"]})
            if era == "2010-26":
                assert abs(r["acc"] - pub[h]) < 0.0015, (h, r["acc"])
    # ---- (2) time-window z against the project's rolling(52) z, EUR 1999-2026
    net = load_net("eur")
    z_roll = ((net - net.rolling(52).mean()) / net.rolling(52).std()).dropna()
    z_time = z52_time(net)
    both = pd.concat([z_roll, z_time], axis=1, keys=["roll", "time"]).dropna()
    rows.append({"check": "z52: time window vs rolling(52), EUR weekly reports (sign agreement)", "era": "2000-26", "h": 0,
                 "this_module": float((np.sign(both["roll"]) == np.sign(both["time"])).mean()), "published": 1.0, "n_indep": len(both),
                 "lo": float(np.corrcoef(both["roll"], both["time"])[0, 1]), "hi": np.nan})
    # ---- (3) Sharpe of the positioning stream on Fed H.10 prices, by era (arm_regime_dependence.md)
    px, _ = price_series("eur")
    L = labels(px)
    known_sr = {"2000-02": 0.15, "2003-09": 0.38, "2010-15": 0.82, "2016-22": 0.83, "2023-26": 0.36}
    eras = tuple((k, int(k[:4]), 2000 + int(k[-2:])) for k in known_sr)
    for lab, roll in (("rolling(52) z (the project's definition)", True), ("time-window z (this module's definition)", False)):
        pnl = stream("eur", px, np.sign(aligned_z("eur", px.index, rolling52=roll)), L)
        for r in sharpe_rows("sign(z52) EUR", "EUR/USD H.10", pnl, eras):
            rows.append({"check": f"positioning stream Sharpe, H.10 noon, 1.2 pips, {lab}", "era": r["era"], "h": 0, "this_module": r["sharpe_daily"],
                         "published": known_sr[r["era"]], "n_indep": r["sessions"], "lo": r["sharpe_21session_blocks"], "hi": np.nan})
            if roll:
                assert abs(r["sharpe_daily"] - known_sr[r["era"]]) < 0.006, r
    T = pd.DataFrame(rows)
    T["difference"] = T["this_module"] - T["published"]
    # the last fold's house model = the frozen transfer used on the mark
    start = pd.Timestamp("2026-01-01", tz="UTC")
    known = (X["yend21"] < start).values & X["y21"].notna().values
    m, _, names = _house_fit(X, known)
    model = {"w": pd.Series(m["w"], index=names), "st": m["st"]}
    if verbose:
        print(T.to_string(index=False), flush=True)
        print("last-fold house weights:\n", model["w"].round(3).to_string(), flush=True)
    return T, ag, model


def euro_reference(X, ag: pd.Series) -> list[dict]:
    """Reference rows for the key table: the same two rules on EUR/USD (feature-store closes), same scoring and
    baselines. Known numbers in a new layout, not candidates."""
    L = pd.DataFrame({f"y{h}": X[f"y{h}"] for h in HORIZONS}, index=X.index)
    side = np.sign(X["cot_z52"])
    rows = score_rule("sign(z52), EUR futures", "EUR/USD", "reference", side, L, (("2000-09", 2000, 2009),) + ERAS_EUR)
    rows += score_rule("agreement rule (original)", "EUR/USD", "reference", ag, L, ERAS_EUR)
    return rows


def bridge_check(C, X) -> tuple[list[dict], dict]:
    """Evaluation 12: the stand-in agreement rule on EUR/USD 2010-26 (each fold's own weights, 9 signals, rate stand-in)."""
    cd = pd.DatetimeIndex(X["__cdate"])
    raw, zs = rate_standin_z(cd)
    raw.index, zs.index = X.index, X.index
    side = pd.Series(np.nan, index=X.index)
    for Y in C.TEST_YEARS:
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC")
        known = (X["yend21"] < start).values & X["y21"].notna().values
        m, Z, names = _house_fit(X, known)
        if m is None:
            continue
        w = pd.Series(m["w"], index=names)
        sub = [k for k in SUBSET if k != "spread"]
        score = (Z[sub] * w[sub]).sum(axis=1, min_count=1) + w["spread"] * zs.fillna(0.0)
        a, b, c = np.sign(X["cot_z52"]), np.sign(raw), np.sign(score)
        agr = pd.Series(np.where((a != 0) & (a == b) & (b == c), a, 0.0), index=X.index).where(score.notna() & a.notna() & b.notna())
        r = X.index.year == Y
        side[r] = agr[r]
    side = side.fillna(0.0)
    L = pd.DataFrame({f"y{h}": X[f"y{h}"] for h in HORIZONS}, index=X.index)
    rows = score_rule("stand-in agreement rule (bridge check)", "EUR/USD", "bridge", side, L, ERAS_EUR)
    # how close is the stand-in to the real thing, on signals only
    true = np.sign(X["d_spread2y_20"])
    ok = true.notna() & raw.notna() & (X.index.year >= 2010) & (true != 0)
    info = {"standin_sign_equals_d_spread2y_20_sign_2010_26": float((np.sign(raw[ok]) == true[ok]).mean())}
    return rows, info


def price_checks() -> pd.DataFrame:
    """Is the synthetic euro trustworthy at 21+ sessions in 1986-1998?
    (a) month-end levels against the OECD end-of-month spot (FRED CCUSSP01DEM650N, an independent source);
    (b) swing's method: the same DKK-bridge construction in 1999-2001 against the true euro (H.10)."""
    rows = []
    syn = SW.synthetic_dem_eur()
    oecd = _ms("pre_euro_fred_CCUSSP01DEM650N.csv")
    oecd.index = oecd.index + pd.offsets.MonthEnd(0)
    eom = syn.groupby(syn.index.to_period("M")).last()
    eom.index = eom.index.to_timestamp(how="end").normalize()
    J = pd.concat([np.log(eom), np.log(oecd)], axis=1, keys=["syn", "oecd"]).dropna()
    for lab, a, b in (("1986-1998", "1986", "1998"), ("1986-1991", "1986", "1991"), ("1992-1993 (ERM crises)", "1992", "1993"), ("1994-1998", "1994", "1998")):
        j = J.loc[a:b]
        d1 = j.diff().dropna()
        for k in (1, 2, 3):
            dk = j.diff(k).dropna()
            rows.append({"check": "month-end synthetic vs OECD end-of-month spot", "period": lab, "horizon": f"{k} month(s)", "n": len(dk),
                         "corr_of_returns": float(np.corrcoef(dk["syn"], dk["oecd"])[0, 1]), "same_sign_share": float((np.sign(dk["syn"]) == np.sign(dk["oecd"])).mean()),
                         "sd_of_return_difference_pct": float((dk["syn"] - dk["oecd"]).std() * 100), "sd_of_level_gap_pct": float((j["syn"] - j["oecd"]).std() * 100),
                         "mean_level_gap_pct": float((j["syn"] - j["oecd"]).mean() * 100), "sd_of_true_return_pct": float(dk["oecd"].std() * 100)})
        del d1
    dem_m, dkk_m, dkk_d = _ms("fred_EXGEUS.csv"), _ms("fred_EXDNUS.csv"), _ms("fred_DEXDNUS.csv")
    ratio = (dem_m / dkk_m).dropna()
    ratio.index = ratio.index + pd.Timedelta(days=14)
    r = ratio.reindex(ratio.index.union(dkk_d.index)).sort_index().interpolate("time").reindex(dkk_d.index).ffill().bfill()
    s99 = (SW.DEM_PER_EUR / (dkk_d * r)).loc["1999-01-04":"2001-11-30"]
    true = _ms("fred_DEXUSEU.csv").reindex(s99.index)
    J = pd.concat([np.log(s99), np.log(true)], axis=1, keys=["syn", "true"]).dropna()
    for h in (1, 21, 42, 63):
        dk = (J.shift(-h) - J).dropna()
        rows.append({"check": "same construction on 1999-2001 vs the true euro (H.10)", "period": "1999-01..2001-11", "horizon": f"{h} session(s)", "n": len(dk),
                     "corr_of_returns": float(np.corrcoef(dk["syn"], dk["true"])[0, 1]), "same_sign_share": float((np.sign(dk["syn"]) == np.sign(dk["true"])).mean()),
                     "sd_of_return_difference_pct": float((dk["syn"] - dk["true"]).std() * 100), "sd_of_level_gap_pct": float((J["syn"] - J["true"]).std() * 100),
                     "mean_level_gap_pct": float((J["syn"] - J["true"]).mean() * 100), "sd_of_true_return_pct": float(dk["true"].std() * 100)})
    return pd.DataFrame(rows)


def shuffled(px: pd.Series, side: pd.Series, a: int, b: int, n_paths: int = N_SHUFFLE, seed: int = SEED) -> list[dict]:
    """Evaluation 10: the era's daily log returns re-ordered at random; the rule's calls are left where they are."""
    m = (px.index.year >= a) & (px.index.year <= b)
    lc = np.log(px[m].values)
    r = np.diff(lc)
    s = side[m].fillna(0.0).values
    rng = np.random.default_rng(seed)
    acc = {h: np.empty(n_paths) for h in HORIZONS}
    for i in range(n_paths):
        p = np.r_[0.0, np.cumsum(rng.permutation(r))]
        for h in HORIZONS:
            y = np.sign(p[h:] - p[:-h])
            ss = s[:-h]
            ok = (ss != 0) & (y != 0)
            acc[h][i] = (ss[ok] == y[ok]).mean()
    return [{"h": h, "paths": n_paths, "mean": float(acc[h].mean()), "p2_5": float(np.percentile(acc[h], 2.5)), "p97_5": float(np.percentile(acc[h], 97.5)),
             "sd": float(acc[h].std())} for h in HORIZONS]


def month_end_rescore(px: pd.Series, side: pd.Series) -> pd.DataFrame:
    """Post-hoc 14: rule 1 at month-ends, scored on the OECD end-of-month DEM spot (independent of the DKK bridge)
    and on the synthetic euro at the same month-ends. Decisions = month-ends 1987-02 .. 1998; k-month outcomes."""
    oecd = _ms("pre_euro_fred_CCUSSP01DEM650N.csv")
    oecd.index = oecd.index.to_period("M")
    per = px.index.to_period("M")
    syn = px.groupby(per).last()
    sd = side.groupby(per).last()
    J = pd.concat([np.log(syn), np.log(oecd), sd], axis=1, keys=["syn", "oecd", "side"]).loc["1987-02":"1998-12"]
    rows = []
    for era, a, b in (("1987-98", "1987", "1998"), ("1987-92", "1987", "1992"), ("1993-98", "1993", "1998")):
        for k in (1, 2, 3):
            for src in ("oecd", "syn"):
                y = np.sign(J[src].shift(-k) - J[src])
                j = pd.concat([J["side"], y], axis=1, keys=["s", "y"]).loc[a:b].dropna()
                j = j[(j.s != 0) & (j.y != 0)]
                n_ind = len(j) / k
                hit = float((j.s == j.y).mean())
                lo, hi = wilson(int(round(hit * n_ind)), max(int(round(n_ind)), 1))
                rows.append({"rule": "14 post-hoc: rule 1 at month-ends", "price": "OECD end-of-month spot" if src == "oecd" else "synthetic euro", "era": era,
                             "months_ahead": k, "n_month_ends": len(j), "n_indep": round(n_ind, 1), "acc": hit, "lo": lo, "hi": hi,
                             "always_long": float((j.y > 0).mean())})
    return pd.DataFrame(rows)


def pooled_sharpe(pnl_dem: pd.DataFrame, cost_pips: float = 1.2) -> pd.DataFrame:
    """Post-hoc, descriptive: the positioning stream pooled across eras (the mark 1987-98; EUR/USD H.10 2000-2026 with
    the project's rolling(52) z). The rule was selected on 2003-2015 (round 1) and 2010-2015 (round 2) and its
    2016-22 record is what kept it alive, so 2003-2022 is treated as the selection window."""
    px, _ = price_series("eur")
    pe = stream("eur", px, np.sign(aligned_z("eur", px.index, rolling52=True)), labels(px), cost_pips)
    d = pnl_dem[(pnl_dem.index.year >= 1987) & (pnl_dem["pos"] != 0)]["net_bp"].dropna()
    e = pe[(pe.index.year >= 2000) & (pe["pos"] != 0)]["net_bp"].dropna()
    x = pd.concat([d, e])
    yr = x.index.year
    sets = {"mark 1987-98": yr <= 1998, "EUR/USD 2000-02": (yr >= 2000) & (yr <= 2002), "EUR/USD 2003-22 (selection window)": (yr >= 2003) & (yr <= 2022),
            "EUR/USD 2023-26": yr >= 2023, "outside the selection window: 1987-98 + 2000-02 + 2023-26": (yr <= 2002) | (yr >= 2023),
            "never looked at before this arm or after selection: 1987-98 + 2023-26": (yr <= 1998) | (yr >= 2023),
            "everything 1987-2026 (includes the selection window)": yr >= 1987}
    rows = []
    for k, m in sets.items():
        v = x[m].values
        sr = v.mean() / v.std(ddof=1) * math.sqrt(252)
        yrs = len(v) / 252.0
        rows.append({"set": k, "years": yrs, "sharpe": sr, "t": v.mean() / v.std(ddof=1) * math.sqrt(len(v)), "se_sharpe": 1 / math.sqrt(yrs),
                     "lo95": sr - 1.96 / math.sqrt(yrs), "hi95": sr + 1.96 / math.sqrt(yrs), "ann_net_pct": v.mean() * 252 / 100})
    return pd.DataFrame(rows)


# ============================================================================= entry point
def run(cost_pips: float = 1.2, save: bool = True, verbose: bool = True):
    """Everything, in the declared order. Returns (daily positions of the primary rule, accuracy table)."""
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    warnings.filterwarnings("ignore")
    fetch(verbose)
    if not (MACRO / "pre_euro_cot_dem.csv").exists():
        build_cot(verbose)
    # ---------------------------------------------------------------- reconciliation first
    C, X = euro_frame()
    REC, ag, model = reconcile(C, X, verbose)
    PC = price_checks()
    if verbose:
        print(PC.round(4).to_string(index=False), flush=True)
    acc, sr = [], []
    acc += euro_reference(X, ag)
    # ---------------------------------------------------------------- 1: PRIMARY
    px, _ = price_series("dem")
    L = labels(px)
    z = aligned_z("dem", px.index)
    side = np.sign(z)
    acc += score_rule("1 PRIMARY sign(z52), DEM futures", "synthetic euro", "primary", side, L, ERAS_PRE)
    pnl = stream("dem", px, side, L, cost_pips)
    sr += sharpe_rows("1 PRIMARY sign(z52), DEM futures", "synthetic euro", pnl, ERAS_PRE)
    # ---------------------------------------------------------------- 2 and 11: agreement-style rule
    S = dem_signals(px, z)
    raw, zs = rate_standin_z(px.index)
    from eurusd.arms import weak_signals as WS
    w, st = model["w"], model["st"]
    sub = [k for k in SUBSET if k != "spread"]
    Z = WS._scaler_apply(S[sub], {k: st[k] for k in sub})
    score = (Z[sub] * w[sub]).sum(axis=1) + w["spread"] * zs.fillna(0.0)
    have = z.notna() & raw.notna()
    a_, b_, c_ = np.sign(z), np.sign(raw), np.sign(score)
    agree = pd.Series(np.where((a_ != 0) & (a_ == b_) & (b_ == c_), a_, 0.0), index=px.index).where(have, 0.0)
    acc += score_rule("2 agreement-style (positioning + rate stand-in + macro subset)", "synthetic euro", "secondary", agree, L, ERAS_PRE)
    sr += sharpe_rows("2 agreement-style", "synthetic euro", stream("dem", px, agree, L, cost_pips), ERAS_PRE)
    score_nocot = score - Z["cot"] * w["cot"]
    c2 = np.sign(score_nocot)
    legs = pd.Series(np.where((b_ != 0) & (b_ == c2), b_, 0.0), index=px.index).where(have, 0.0)
    acc += score_rule("11 non-positioning legs agree (rate stand-in + macro subset without cot)", "synthetic euro", "descriptive", legs, L, ERAS_PRE)
    era_m = (px.index.year >= 1987) & (px.index.year <= 1998) & have.values
    votes = {"share_sessions_agreement": float((agree[era_m] != 0).mean()), "share_sessions_non_positioning_legs_agree": float((legs[era_m] != 0).mean()),
             "sign_agreement_positioning_vs_rate_standin": float((a_[era_m] == b_[era_m]).mean()),
             "sign_agreement_positioning_vs_macro_subset": float((a_[era_m] == c_[era_m]).mean()),
             "sign_agreement_rate_standin_vs_macro_subset": float((b_[era_m] == c_[era_m]).mean()),
             "weight_share_rebuilt": float(w[list(SUBSET)].sum()), "weight_share_missing": float(w[list(MISSING)].sum())}
    # ---------------------------------------------------------------- 3-6: other currencies
    others = {}
    for ccy in ("jpy", "gbp", "chf", "cad"):
        p2, _ = price_series(ccy)
        p2 = p2[(p2.index >= "1975-01-01") & (p2.index <= "1998-12-31")]
        L2 = labels(p2)
        s2 = np.sign(aligned_z(ccy, p2.index))
        nm = f"{dict(jpy=3, gbp=4, chf=5, cad=6)[ccy]} sign(z52), {ccy.upper()} futures"
        acc += score_rule(nm, f"{ccy.upper()}/USD H.10", "context", s2, L2, ERAS_PRE)
        pn2 = stream(ccy, p2, s2, L2, cost_pips)
        sr += sharpe_rows(nm, f"{ccy.upper()}/USD H.10", pn2, ERAS_PRE)
        others[ccy] = pn2["net_bp"]
    B = pd.concat(others, axis=1)
    B = B[(B.index.year >= 1987)].dropna(how="all")
    sd = B.std()
    basket = (B / sd).mean(axis=1) * sd.mean()
    sr += sharpe_rows("3-6 equal-risk basket of the four", "JPY GBP CHF CAD", pd.DataFrame({"net_bp": basket, "pos": 1.0, "turnover": 0.0}), ERAS_PRE)
    # ---------------------------------------------------------------- 7-9: controls of the primary rule
    for k in (63, 126):
        acc += score_rule(f"{7 if k == 63 else 8} control: primary signal {k} sessions stale", "synthetic euro", "control", side.shift(k), L, ERAS_PRE)
    side_late = np.sign(aligned_z("dem", px.index, extra_days=7))
    acc += score_rule("9 control: primary with one extra week of publication delay", "synthetic euro", "control", side_late, L, ERAS_PRE)
    sr += sharpe_rows("9 control: one extra week of delay", "synthetic euro", stream("dem", px, side_late, L, cost_pips), ERAS_PRE)
    # ---------------------------------------------------------------- 10: shuffled outcomes
    SH = pd.DataFrame(shuffled(px, side, 1987, 1998))
    SH.insert(0, "rule", "10 control: shuffled daily returns, primary rule unchanged")
    # ---------------------------------------------------------------- 12: bridge check on EUR/USD
    brows, binfo = bridge_check(C, X)
    acc += brows
    votes |= binfo
    # ---------------------------------------------------------------- post-hoc 13, 14 and the pooled Sharpe (see the addendum)
    side_early = np.sign(aligned_z("dem", px.index, fixed_lag_days=6))
    acc += score_rule("13 post-hoc: primary with as-of + 6 days throughout (optimistic bound)", "synthetic euro", "post-hoc", side_early, L, ERAS_PRE)
    sr += sharpe_rows("13 post-hoc: as-of + 6 days throughout", "synthetic euro", stream("dem", px, side_early, L, cost_pips), ERAS_PRE)
    side_look = np.sign(aligned_z("dem", px.index, fixed_lag_days=-30))
    acc += score_rule("15 pipeline check: LOOK-AHEAD copy (report known 30 days before its as-of date)", "synthetic euro", "pipeline-check", side_look, L, ERAS_PRE)
    ME = month_end_rescore(px, side)
    POOL = pooled_sharpe(pnl, cost_pips)
    ACC, SR = pd.DataFrame(acc), pd.DataFrame(sr)
    # ---------------------------------------------------------------- verdict against the declared bar
    q = ACC[(ACC.kind == "primary") & (ACC.era == "1987-98")].set_index("h")
    a21, a42, a63 = float(q.loc[21, "acc"]), float(q.loc[42, "acc"]), float(q.loc[63, "acc"])
    bar = (a42 > 0.55) and (a21 > 0.50) and (a63 > 0.50)
    p42 = float(q.loc[42, "base_p"])
    verdict = ("CLEAN PASS" if bar and p42 <= 0.10 else "PASS, NOT DISTINGUISHABLE FROM RANDOM TIMING" if bar else "CLEAN FAIL" if a42 <= 0.50 else "FAIL")
    summary = {"verdict": verdict, "acc21": a21, "acc42": a42, "acc63": a63, "random_timing_p42": p42, **votes,
               "first_decision": str(side.dropna().index[0].date()), "last_label_end": str(px.index[-1].date())}
    if save:
        RES.mkdir(parents=True, exist_ok=True)
        REC.to_csv(RES / f"{ARM}_reconcile.csv", index=False)
        PC.to_csv(RES / f"{ARM}_price_check.csv", index=False)
        ACC.to_csv(RES / f"{ARM}_accuracy.csv", index=False)
        SR.to_csv(RES / f"{ARM}_sharpe.csv", index=False)
        SH.to_csv(RES / f"{ARM}_shuffled.csv", index=False)
        ME.to_csv(RES / f"{ARM}_month_end_rescore.csv", index=False)
        POOL.to_csv(RES / f"{ARM}_pooled_sharpe.csv", index=False)
        pd.Series(summary).rename("value").rename_axis("item").to_csv(RES / f"{ARM}_summary.csv")
        model["w"].rename("weight").rename_axis("signal").to_frame().assign(rebuilt_for_1987_98=lambda d: d.index.isin(SUBSET)).to_csv(RES / f"{ARM}_house_weights.csv")
        out = pd.DataFrame({"pos": pnl["pos"], "z52": z, "fwd_bp": L["fwd_1d"], "net_bp": pnl["net_bp"], "close": px})
        out = out[(out.index >= "1987-01-01")]
        out.to_parquet(RES / f"{ARM}_positions.parquet")
    if verbose:
        f = lambda d: d.assign(**{c: (100 * d[c]).round(1) for c in ("acc", "lo", "hi", "always_long", "base_mean", "base_lo", "base_hi") if c in d})  # noqa: E731
        cols = ["rule", "era", "h", "n_indep", "per_year", "acc", "lo", "hi", "always_long", "base_mean", "base_lo", "base_hi", "base_p", "share_of_days", "share_long"]
        print(f(ACC)[cols].round(3).to_string(index=False), flush=True)
        print(SR.round(3).to_string(index=False), flush=True)
        print(SH.round(4).to_string(index=False), flush=True)
        print(ME.round(3).to_string(index=False), flush=True)
        print(POOL.round(3).to_string(index=False), flush=True)
        print(pd.Series(summary).to_string(), flush=True)
    return pnl["pos"], ACC


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "build":
        fetch()
        build_cot()
    else:
        run()
