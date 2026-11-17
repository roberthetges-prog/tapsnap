"""Arm DA ("bots_experience"): does more experience make the 100-bot vote better?

EVERYTHING IN THIS DOCSTRING DOWN TO "POST-HOC" WAS WRITTEN ON 2026-11-17 BEFORE ANY OUTCOME WAS COMPUTED. What had
been looked at when it was written: file spans and gaps of the price, rate and positioning files (no return, no
label, no accuracy), which FRED series answer, and the code of `eurusd.bots`. Nothing is tuned afterwards.

QUESTION (owner)
Can the bots' experience be expanded, and does the vote get better? Two honest ways: more YEARS (the Deutsche Mark
before 1999, as the synthetic euro) and more MARKETS (six other dollar pairs). Both are tested against the same bots
trained on EUR/USD 1999+ only; every version is scored on EUR/USD in years none of the bots saw.

PRICES (one source, one stamp, for every pair): Federal Reserve H.10 noon-New-York fixings, `data/macro/fred_DEX*.csv`,
as USD per unit of currency ("currency up against the dollar"): EUR = DEXUSEU from 1999-01-04, before that the
synthetic euro of `swing.synthetic_dem_eur()` (1.95583 / mark; daily via the Danish krone, good at 21 sessions and
longer); GBP DEXUSUK, JPY 1/DEXJPUS, CHF 1/DEXSZUS, CAD 1/DEXCAUS, AUD DEXUSAL, NZD DEXUSNZ. One calendar (the
H.10 fixing days). A row dated D is a decision AT the noon fix of D: it may use the fix of D and anything else
stamped D-1 or earlier. The outcome is the sign of the log change from the fix of D to the fix h sessions later
and is known at that later fix.

THE GENERIC EVIDENCE SET (31 columns, built by one function for every pair; + = "currency up" under the plain prior)
 positioning (CFTC legacy futures-only, non-commercial net / open interest; era publication stamps of
 `pre_euro.avail_stamp`, then one more calendar day; a figure is dropped when more than 45 days past its stamp)
   pos_z52     z-score over the reports of the last 364 days (`pre_euro.z52_time`: the same thing for twice-monthly
               and weekly reports)                        pos_z156    the same over 1,092 days (>= 60 reports)
   pos_d4      change against the last report at least 28 days older
   EUR: mark futures (094741) for rows before 1999, Euro FX (099741) from 1999; the two contracts are never mixed in
   one window, so pos_z52 is missing in 1999 and pos_z156 until 2002-01. GBP JPY CHF CAD: `pre_euro_cot_*.csv` to
   1998 joined to `cot_*_legacy.csv` (same contract). AUD: the 1987-98 reports are parsed by this arm from the same
   CFTC archive. NZD: 1999+ only, with holes of up to 3.6 years in 2000-05.
 short rates (monthly 3-month interbank, FRED IR3TIB01xxM156N, minus the US one; month M is stamped M-01 and used
 from M-01 + 45 days, dropped 100 days after that if no newer month has arrived)
   rd_lvl      level          rd_d3   3-month change          rd_d6   6-month change
   EUR uses the German series (1960-2026; it is the euro rate after 1999). GBP 1957+, CAD 1956+, AUD 1968+,
   NZD 1973+, CHF 1999-07+ only, JPY 2002-04+ only (no substitute series is spliced in).
 own price (H.10 fix)
   mom21 mom63 mom126 mom252   log change over 1, 3, 6, 12 months
   ma_state    sign(price - SMA50) + sign(SMA50 - SMA200)
   brk126      place in the 126-session range, -1 (at the low) .. +1 (at the high)
   dist5y      log price minus its 1,260-session mean        stretch20  (price - SMA20) / 20-session sd of price
 dollar factor without the pair itself
   usdx21 usdx63   mean log change of the OTHER six currencies against the dollar over 21 / 63 sessions
 global, the same number on every pair's row (daily series lagged one calendar day)
   vix_lvl (log VIX, 1990+)   vix_d5 (5-session change)   eq_r21 eq_r63 (NASDAQ Composite, the only daily US equity
   index here that spans 1971-2026)   oil_r21 oil_r63 (WTI spot, 1986+)   gold_r3 (3-month change of the monthly
   average gold price, month M used from the 2nd day of M+1)   us_curve (10y - 2y, 1976+)
   us2y_d20n (minus the 20-session change of the 2-year yield)
 Fed meetings, exactly `eurusd.committee.fed_desk` (meetings from 1989-07, target from 1982-09)
   fed_latest fed_cycle fed_surprise fed_priced (global)    fed_fx (the pair's own move over the decision)
 seasonality
   seas_month  t-statistic of the pair's average 21-session return by calendar month, learned for the rows of year Y
               only from outcomes known before Y-01-01 (>= 5 years), scaled to [-1, 1], 0 when |t| < 1
 No column names the pair. The columns of a row are the same under all four trainings (they may use earlier prices
 of the same pair, e.g. the 5-year mean of 1999 uses the synthetic euro); only the TRAINING ROWS differ.

THE BOTS: the product's 100 bots in structure. Bot i keeps the research rule, the number of columns kept, the learner,
the memory and the tree depth of `eurusd.bots.SPECS[i]`; only its desk is redrawn, 12 of the 31 generic columns with
RandomState(1000 + i) (the product's seed and first draw). Research and learners are the product's own functions
(`bots._research`, `bots._fit_predict`), the vote is `bots.count`; every bot must vote. Walk-forward yearly, test
years 2010-2026: for test year Y a bot uses only rows whose outcome was known before Y-01-01, inside its memory.
Training sets (EUR/USD always scored):
  (a) baseline     EUR/USD rows from 1999-01-04
  (b) more years   (a) + the synthetic-euro rows from the first session with a public mark pos_z52 (1987-02)
  (c) more markets (a) + GBP JPY CHF CAD AUD NZD rows from 1999-01-04
  (d) both         every pair from 1987-02 (AUD from its first public pos_z52, 1988; NZD from 1999)
Pooling rule: each pair's columns are standardised with the mean and sd of ITS OWN training rows (clipped at 3,
missing = 0, as the product); a pair joins a bot's training set only with >= 500 such rows; a column is on the desk
if it is usable on EUR/USD (finite on more than half of EUR/USD's training rows, sd > 0) and is set to 0 for a pair
on which it is not; the pooled rows are put in time order before the research step. With one pair this is the
product's `run_bot` exactly (checked numerically). A bot with a 5- or 10-year memory cannot see 1987-98 from any
fold 2010+, so (b) = (a) and (d) = (c) for those bots BY CONSTRUCTION (checked); the all-history bots are also
reported on their own.
Leak rule for pooling, asserted in every fold and tabulated: every training row of every pair has its outcome fix
strictly before Y-01-01, so no row of any pair dated inside EUR/USD's test year can be in training.

PRIMARY TEST (3 candidates: b, c, d; baseline a): the majority vote of the 100 bots on EUR/USD at 21 and 63 sessions.
Accuracy is phase-averaged over every session with a majority and a non-zero outcome; independent votes = sessions / h;
Wilson 95 % interval on that count (the scoring of `experiments/72_bots.py`). Eras 2010-26, 2016-26, 2023-26 and the
split 2010-17 / 2018-26. Difference from (a) on the same sessions with a paired circular block bootstrap (blocks of
max(63, 2h) sessions, 5,000 draws, seed 20261117, percentile 95 % interval).
BAR: a version is ADOPTED only if it is >= 2.0 points more accurate than (a) at BOTH 21 and 63 sessions in 2018-26,
is not worse than (a) at either horizon in 2010-17 (difference >= 0), and the bootstrap interval of the 2018-26
difference excludes zero at one of the two horizons at least. If several pass: the one with the larger smaller gain.
5 sessions is reported, not judged.
DESCRIPTIVE (not candidates): single-bot accuracy; mean pairwise correlation of the bots being right; columns kept
under (a) and (c); the (c) bots' vote scored on each of the other six pairs; the generic baseline next to the
product's bots (also on the product's own closes).
CONTROLS: shuffled outcomes (each pair's daily returns re-ordered by one common permutation; outcomes rebuilt,
evidence untouched; expect about 50 %); truncation (all inputs cut at 2018-12-31, the 2018 fold re-run, forecasts
must be identical); look-ahead (the next 21 sessions' change added to every desk; the harness must find it).

POST-HOC (written 2026-11-17 AFTER the declared run had been read; none of the three candidates met the bar, and
nothing above was changed). Corrections of fact and two added checks, labelled post-hoc in the outputs:
  * AUD's first public pos_z52 is 1993-01, not 1988 as written above: the archive holds only 3-22 AUD reports a year
    before 1993, too few for a 364-day window of 20 reports. So AUD joins training (d) from 1993-01.
  * 28 of the 100 bots have an all-history memory (the roster is inherited from `bots.SPECS`); 72 cannot see 1987-98.
  * The declared shuffle (a permutation) scored 46-49 %, below 50: a permuted path keeps the true total change, so
    what was learned on its past is slightly anti-informative about its rest. Added: outcomes rebuilt from daily
    returns with random signs (one common sign per day for all pairs), 3 seeds, trainings (a) and (c).
  * Added: share of UP votes and accuracy by vote direction under each training (does pooling just flip a bias?).
Candidate count: 3 (b, c, d). No candidate was added, changed or re-run after the outcome.

Run:  PYTHONPATH=src OMP_NUM_THREADS=1 python -m eurusd.arms.bots_experience
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import bots as B  # noqa: E402
from eurusd import committee as C  # noqa: E402
from eurusd.arms import pre_euro as PE  # noqa: E402
from eurusd.arms import swing as SW  # noqa: E402
from eurusd.arms.swing import wilson, _ms, _align_lagged  # noqa: E402

MACRO, PROC, RES = SW.MACRO, SW.PROC, SW.RES
ARM = "bots_experience"
SEED = 20261117
HORIZONS = (5, 21, 63)
TEST_YEARS = list(range(2010, 2027))
ERAS = (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026), ("2010-17", 2010, 2017), ("2018-26", 2018, 2026))
PAIRS = ("eur", "gbp", "jpy", "chf", "cad", "aud", "nzd")
H10 = {"eur": ("DEXUSEU", False), "gbp": ("DEXUSUK", False), "jpy": ("DEXJPUS", True), "chf": ("DEXSZUS", True),
       "cad": ("DEXCAUS", True), "aud": ("DEXUSAL", False), "nzd": ("DEXUSNZ", False)}
RATE = {"eur": "DE", "gbp": "GB", "jpy": "JP", "chf": "CH", "cad": "CA", "aud": "AU", "nzd": "NZ"}
POOL = ["pos_z52", "pos_z156", "pos_d4", "rd_lvl", "rd_d3", "rd_d6", "mom21", "mom63", "mom126", "mom252", "ma_state", "brk126",
        "dist5y", "stretch20", "usdx21", "usdx63", "vix_lvl", "vix_d5", "eq_r21", "eq_r63", "oil_r21", "oil_r63", "gold_r3",
        "us_curve", "us2y_d20n", "fed_latest", "fed_cycle", "fed_surprise", "fed_priced", "fed_fx", "seas_month"]
FAMILY = {**{c: "positioning" for c in POOL[:3]}, **{c: "short rates" for c in POOL[3:6]}, **{c: "own price" for c in POOL[6:14]},
          **{c: "dollar factor" for c in POOL[14:16]}, **{c: "global" for c in POOL[16:25]}, **{c: "Fed meetings" for c in POOL[25:30]},
          "seas_month": "seasonality", "peek": "LOOK-AHEAD"}
T99 = pd.Timestamp("1999-01-04")
T87 = pd.Timestamp("1987-02-01")
FAR = pd.Timestamp("1900-01-01")
N_BOOT = 5000


# ============================================================================= data
def build_aud_pre1999() -> pd.DataFrame:
    """AUD futures 1987-98 from the CFTC archive pre_euro already downloaded (code 232741, IMM)."""
    f = MACRO / f"{ARM}_cot_aud_pre1999.csv"
    if f.exists():
        return pd.read_csv(f, parse_dates=["report_date"])
    df = PE._read_archive()
    code = next(c for c in df.columns if "Contract Market Code" in c)
    name = next(c for c in df.columns if "Market and Exchange" in c)
    date = next(c for c in df.columns if "YYYY-MM-DD" in c)
    t = df[df[code].astype(str).str.strip() == "232741"].copy()
    t["report_date"] = pd.to_datetime(t[date].str.strip())
    t = t[t["report_date"] <= "1998-12-31"]
    assert t[name].str.contains("AUSTRALIAN DOLLAR").all() and t[name].str.contains("INTERNATIONAL MONETARY MARKET").all()
    col = lambda p: next(c for c in df.columns if c.strip().startswith(p))  # noqa: E731
    out = pd.DataFrame({"report_date": t["report_date"], "market": t[name].str.strip(),
                        "open_interest": PE._num(t[col("Open Interest (All)")]),
                        "noncomm_long": PE._num(t[col("Noncommercial Positions-Long (All)")]),
                        "noncomm_short": PE._num(t[col("Noncommercial Positions-Short (All)")])})
    out = out.sort_values("report_date").drop_duplicates("report_date").reset_index(drop=True)
    out.to_csv(f, index=False)
    return out


def _ratio(f: Path) -> pd.Series:
    d = pd.read_csv(f, parse_dates=["report_date"]).set_index("report_date").sort_index()
    r = ((d["noncomm_long"] - d["noncomm_short"]) / d["open_interest"]).replace([np.inf, -np.inf], np.nan).dropna()
    return r[~r.index.duplicated()]


def positioning_ratios(ccy: str) -> list[pd.Series]:
    """Net / open interest by as-of date; one series per contract (EUR: the mark and Euro FX are kept apart)."""
    if ccy == "eur":
        return [_ratio(MACRO / "pre_euro_cot_dem.csv").loc[:"1998-12-31"], _ratio(MACRO / "cot_eurofx_legacy.csv")]
    new = _ratio(MACRO / f"cot_{ccy}_legacy.csv")
    if ccy == "nzd":
        return [new]
    if ccy == "aud":
        build_aud_pre1999()
        old = _ratio(MACRO / f"{ARM}_cot_aud_pre1999.csv")
    else:
        old = _ratio(MACRO / f"pre_euro_cot_{ccy}.csv").loc[:"1998-12-31"]
    s = pd.concat([old, new])
    return [s[~s.index.duplicated(keep="last")].sort_index()]


def _d4(r: pd.Series) -> pd.Series:
    t = r.index.values.astype("datetime64[D]").astype(np.int64)
    v = r.values
    out = np.full(len(v), np.nan)
    for i in range(len(v)):
        j = int(np.searchsorted(t, t[i] - 28, side="right")) - 1
        if j >= 0 and t[i] - t[j] <= 49:
            out[i] = v[i] - v[j]
    return pd.Series(out, index=r.index).dropna()


def _fresh(s: pd.Series, dates: pd.DatetimeIndex, lag: int, max_age: int) -> np.ndarray:
    """Last value stamped <= date - lag, NaN when that stamp is more than max_age days older than date - lag."""
    s = s.dropna()
    if s.empty:
        return np.full(len(dates), np.nan)
    v = _align_lagged(s, dates, lag).values.astype(float)
    st = _align_lagged(pd.Series(s.index.values.astype("datetime64[D]").astype(np.int64).astype(float), index=s.index), dates, lag).values
    age = (dates - pd.Timedelta(days=lag)).values.astype("datetime64[D]").astype(np.int64) - st
    v[~(age <= max_age)] = np.nan
    return v


def positioning_columns(ccy: str, dates: pd.DatetimeIndex, cutoff=None) -> pd.DataFrame:
    out = pd.DataFrame(np.nan, index=dates, columns=["pos_z52", "pos_z156", "pos_d4"])
    for k, r in enumerate(positioning_ratios(ccy)):
        if cutoff is not None:
            r = r.loc[:cutoff]
        if len(r) < 5:
            continue
        cols = {"pos_z52": PE.z52_time(r), "pos_z156": PE.z52_time(r, 1092, 1085, 60), "pos_d4": _d4(r)}
        for c, z in cols.items():
            if z.empty:
                continue
            v = _fresh(PE.stamped(z), dates, 1, 45)
            if ccy == "eur":                      # the mark before 1999, Euro FX from 1999; never both
                use = (dates < T99) if k == 0 else (dates >= T99)
                v = np.where(use, v, np.nan)
            out[c] = np.where(np.isfinite(v), v, out[c].values)
    return out


def price_panel(cutoff=None) -> pd.DataFrame:
    px = {}
    for ccy, (s, inv) in H10.items():
        v = _ms(f"fred_{s}.csv")
        px[ccy] = 1.0 / v if inv else v
    px["eur"] = pd.concat([SW.synthetic_dem_eur(), px["eur"].loc["1999-01-04":]])
    P = pd.DataFrame(px).loc["1975-01-02":]
    P = P[P["eur"].notna()].ffill(limit=3)
    assert P.notna().all().all() and P.index.is_monotonic_increasing
    return P if cutoff is None else P.loc[:cutoff]


def _cut(s: pd.Series, cutoff) -> pd.Series:
    return s if cutoff is None else s.loc[:cutoff]


def global_columns(dates: pd.DatetimeIndex, cutoff=None) -> pd.DataFrame:
    A = lambda s: pd.Series(_fresh(_cut(s, cutoff), dates, 1, 10), index=dates)  # noqa: E731
    G = pd.DataFrame(index=dates)
    vix = A(np.log(_ms("fred_VIXCLS.csv")))
    G["vix_lvl"], G["vix_d5"] = vix, vix.diff(5)
    eq = A(np.log(_ms("fred_NASDAQCOM.csv")))
    G["eq_r21"], G["eq_r63"] = eq.diff(21), eq.diff(63)
    wti = _ms("datahub_wti_daily.csv", "price")
    oil = A(np.log(wti[wti > 0]))
    G["oil_r21"], G["oil_r63"] = oil.diff(21), oil.diff(63)
    gold = np.log(_ms("datahub_gold_monthly.csv", "price"))
    g3 = _cut((gold - gold.shift(3)).dropna(), cutoff)
    g3.index = g3.index + pd.offsets.MonthBegin(1)
    G["gold_r3"] = _fresh(g3, dates, 1, 70)
    us2, us10 = A(_ms("fred_DGS2.csv")), A(_ms("fred_DGS10.csv"))
    G["us_curve"] = us10 - us2
    G["us2y_d20n"] = -us2.diff(20)
    return G


def rate_columns(ccy: str, dates: pd.DatetimeIndex, cutoff=None) -> pd.DataFrame:
    us = _ms("fred_IR3TIB01USM156N.csv")
    d = _cut((_ms(f"fred_IR3TIB01{RATE[ccy]}M156N.csv") - us).dropna(), cutoff)
    d = d.asfreq("MS")
    return pd.DataFrame({"rd_lvl": _fresh(d, dates, 45, 100), "rd_d3": _fresh(d - d.shift(3), dates, 45, 100),
                         "rd_d6": _fresh(d - d.shift(6), dates, 45, 100)}, index=dates)


def seasonality(lc: pd.Series, ct: pd.Series) -> np.ndarray:
    fwd = (lc.shift(-21) - lc).values
    end = ct.shift(-21).values
    yr, mo = lc.index.year.values, lc.index.month.values
    out = np.full(len(lc), np.nan)
    for Y in sorted(set(yr)):
        start = np.datetime64(pd.Timestamp(f"{Y}-01-01"))
        k = (end < start) & np.isfinite(fwd)
        if len(set(yr[k])) < 5:
            continue
        ym = pd.Series(fwd[k]).groupby([mo[k], yr[k]]).mean()
        t = {}
        for m in range(1, 13):
            v = ym.loc[m] if m in ym.index.get_level_values(0) else pd.Series(dtype=float)
            t[m] = float(v.mean() / (v.std() / np.sqrt(len(v)))) if len(v) >= 5 and v.std() > 0 else 0.0
        rows = yr == Y
        tv = pd.Series(mo[rows]).map(t).astype(float).values
        out[rows] = np.where(np.abs(tv) >= 1, np.clip(tv, -3, 3) / 3, 0.0)
    return out


def build_pair(ccy: str, P: pd.DataFrame, G: pd.DataFrame, cutoff=None) -> pd.DataFrame:
    """The 31 generic columns, outcomes and outcome times for one pair. Index = fixing date (naive)."""
    dates = P.index
    s = P[ccy]
    lc = np.log(s)
    ct = pd.Series(dates + pd.Timedelta(hours=17), index=dates)          # noon New York, naive UTC
    X = positioning_columns(ccy, dates, cutoff)
    X = pd.concat([X, rate_columns(ccy, dates, cutoff)], axis=1)
    for k in (21, 63, 126, 252):
        X[f"mom{k}"] = lc.diff(k)
    s50, s200 = s.rolling(50).mean(), s.rolling(200).mean()
    X["ma_state"] = (np.sign(s - s50) + np.sign(s50 - s200)).where(s200.notna())
    lo, hi = s.rolling(126).min(), s.rolling(126).max()
    X["brk126"] = (2 * (s - lo) / (hi - lo) - 1).where(hi > lo)
    X["dist5y"] = lc - lc.rolling(1260).mean()
    X["stretch20"] = (s - s.rolling(20).mean()) / s.rolling(20).std()
    others = np.log(P[[c for c in PAIRS if c != ccy]])
    X["usdx21"], X["usdx63"] = others.diff(21).mean(axis=1), others.diff(63).mean(axis=1)
    for c in G.columns:
        X[c] = G[c]
    Pf = pd.DataFrame({"close": s.values, "src": "h10", "cdate": dates.values}, index=pd.DatetimeIndex(dates).tz_localize("UTC") + pd.Timedelta(hours=17))
    Pf["close_time"] = Pf.index
    A = lambda q, lag=1: pd.Series(_align_lagged(_cut(q, cutoff), dates, lag).values, index=Pf.index)  # noqa: E731
    FD = C.fed_desk(None, Pf, A)
    for c in ("fed_latest", "fed_cycle", "fed_surprise", "fed_priced", "fed_fx"):
        X[c] = FD[c].values
    X["seas_month"] = seasonality(lc, ct)
    X["peek"] = lc.shift(-21) - lc                                       # LOOK-AHEAD control only; never in POOL
    for h in HORIZONS:
        X[f"y{h}"] = np.sign(lc.shift(-h) - lc)
        X[f"yend{h}"] = ct.shift(-h)
    X["__ct"] = ct
    X["__close"] = s
    return X.replace([np.inf, -np.inf], np.nan).loc["1986-01-01":]


def frames(cutoff=None, cache: bool = True) -> dict:
    warnings.filterwarnings("ignore")
    fs = {c: PROC / f"{ARM}_frame_{c}.parquet" for c in PAIRS}
    if cutoff is None and cache and all(f.exists() for f in fs.values()):
        return {c: pd.read_parquet(f) for c, f in fs.items()}
    P = price_panel(cutoff)
    G = global_columns(P.index, cutoff)
    out = {c: build_pair(c, P, G, cutoff) for c in PAIRS}
    if cutoff is None and cache:
        for c, f in fs.items():
            out[c].astype({k: "float32" for k in POOL}).to_parquet(f)
        return {c: pd.read_parquet(f) for c, f in fs.items()}
    return {c: x.astype({k: "float32" for k in POOL}) for c, x in out.items()}


def row_starts(F: dict) -> dict:
    """First training row of each pair under each training."""
    first87 = {}
    for c in PAIRS:
        z = F[c]["pos_z52"]
        z = z[(z.index >= T87) & z.notna()]
        first87[c] = max(z.index[0], T87) if len(z) and z.index[0] < T99 else T99
    return {"a": {"eur": T99}, "b": {"eur": first87["eur"]}, "c": {c: T99 for c in PAIRS}, "d": dict(first87)}


# ============================================================================= bots
def spec(i: int, extra: tuple = ()) -> dict:
    rng = np.random.RandomState(1000 + i)
    desk = list(rng.choice(POOL, size=B.DESK, replace=False)) + list(extra)
    p = B.SPECS[i]
    return {"bot": i, "desk": desk, "research": p["research"], "keep": p["keep"], "learner": p["learner"], "memory": p["memory"],
            "depth": p["depth"], "gauge": p["gauge"]}


SPECS = [spec(i) for i in range(B.N_BOTS)]


class Fold:
    """Arrays of one training set for one horizon; `run` = one bot, one fold."""

    def __init__(self, F: dict, starts: dict, h: int, ycol: str | None = None):
        self.h, self.pairs = h, list(starts)
        self.M, self.y, self.yend, self.ct, self.year, self.first = {}, {}, {}, {}, {}, {}
        for c in F:
            x = F[c]
            self.M[c] = x
            self.y[c] = x[ycol or f"y{h}"].values.astype(float)
            self.yend[c] = x[f"yend{h}"].values.astype("datetime64[ns]")
            self.ct[c] = x["__ct"].values.astype("datetime64[ns]")
            self.year[c] = x.index.year.values
            self.first[c] = np.datetime64(starts.get(c, FAR))
        self.audit = []

    def known(self, c: str, start: pd.Timestamp, memory) -> np.ndarray:
        s = np.datetime64(start)
        k = (self.yend[c] < s) & np.isfinite(self.y[c]) & (self.y[c] != 0) & (self.M[c].index.values >= self.first[c])
        if memory:
            k &= self.ct[c] >= np.datetime64(start - pd.DateOffset(years=memory))
        return k

    def run(self, sp: dict, Y: int, targets=("eur",)) -> dict:
        start = pd.Timestamp(f"{Y}-01-01")
        out = {t: np.full(int((self.year[t] == Y).sum()), np.nan) for t in targets}
        out["kept"] = []
        Z, K, okp = {}, {}, {}
        for c in set(self.pairs) | set(targets):
            k = self.known(c, start, sp["memory"]) if c in self.pairs else np.zeros(len(self.y[c]), bool)
            if c not in self.pairs:                      # scored but not trained on: standardise on its own past rows
                k0 = (self.yend[c] < np.datetime64(start)) & (self.ct[c] >= np.datetime64(start - pd.DateOffset(years=sp["memory"] or 100)))
            else:
                k0 = k
            if k0.sum() < B.MIN_ROWS:
                continue
            M = self.M[c][sp["desk"]].values.astype(float)
            tr = M[k0]
            mu, sd = np.nanmean(tr, axis=0), np.nanstd(tr, axis=0)
            ok = np.isfinite(sd) & (sd > 0) & (np.isfinite(tr).mean(axis=0) > 0.5)
            z = np.zeros_like(M)
            z[:, ok] = np.nan_to_num(np.clip((M[:, ok] - mu[ok]) / sd[ok], -3, 3))
            Z[c], K[c], okp[c] = z, k, ok
        if "eur" not in Z or not okp["eur"].any():
            return out
        ok = okp["eur"]
        tp = [c for c in self.pairs if c in Z]
        for c in tp:                                   # the leak rule, asserted on every training row
            if K[c].any():
                assert self.yend[c][K[c]].max() < np.datetime64(start) and self.ct[c][K[c]].max() < np.datetime64(start)
        A = np.concatenate([Z[c][K[c]][:, ok] for c in tp])
        y = np.concatenate([self.y[c][K[c]] for c in tp])
        if len(tp) > 1:
            o = np.argsort(np.concatenate([self.ct[c][K[c]] for c in tp]), kind="stable")
            A, y = A[o], y[o]
        keep = B._research(A, y, sp["research"], sp["keep"])
        out["kept"] = [np.array(sp["desk"])[ok][c] for c in keep]
        out["n_train"] = len(y)
        tz = [t for t in targets if t in Z]
        Bm = np.concatenate([Z[t][self.year[t] == Y][:, ok][:, keep] for t in tz])
        p = B._fit_predict(sp["learner"], sp["depth"], A[:, keep], y, Bm)
        i = 0
        for t in tz:
            n = len(out[t])
            out[t] = p[i:i + n]
            i += n
        return out

    def leak_row(self, Y: int) -> list[dict]:
        start = pd.Timestamp(f"{Y}-01-01")
        rows = []
        for c in self.pairs:
            k = self.known(c, start, None)
            if k.any():
                rows.append({"h": self.h, "test_year": Y, "pair": c, "training_rows": int(k.sum()), "first_row": str(self.M[c].index[k][0].date()),
                             "last_row": str(self.M[c].index[k][-1].date()), "last_outcome_fix": str(pd.Timestamp(self.yend[c][k].max()).date()),
                             "rows_dated_in_or_after_test_year": int((self.year[c][k] >= Y).sum())})
        return rows


def walk(F: dict, starts: dict, h: int, targets=("eur",), specs=None, years=TEST_YEARS, ycol=None, tag: str = "", verbose=True):
    specs = specs or SPECS
    fo = Fold(F, starts, h, ycol)
    P = {t: [] for t in targets}
    kept, leak = [], []
    t0 = time.time()
    for Y in years:
        cols = {t: {} for t in targets}
        for sp in specs:
            o = fo.run(sp, Y, targets)
            for t in targets:
                cols[t][sp["bot"]] = o[t]
            kept += [{"h": h, "year": Y, "bot": sp["bot"], "col": c} for c in o["kept"]]
        for t in targets:
            P[t].append(pd.DataFrame(cols[t], index=F[t].index[fo.year[t] == Y]))
        leak += fo.leak_row(Y)
        if verbose:
            print(f"  {tag} h={h} {Y} done {time.time() - t0:.0f}s", flush=True)
    return {t: pd.concat(P[t]) for t in targets}, pd.DataFrame(kept), pd.DataFrame(leak)


# ============================================================================= scoring
def hits(side: pd.Series, y: pd.Series) -> pd.Series:
    ok = (side != 0) & side.notna() & y.notna() & (y != 0)
    return (side == y).astype(float).where(ok)


def acc(hit: pd.Series, h: int, a: int, b: int) -> dict:
    v = hit[(hit.index.year >= a) & (hit.index.year <= b)].dropna()
    if len(v) == 0:
        return {"sessions": 0, "n_indep": 0.0, "acc": np.nan, "lo": np.nan, "hi": np.nan}
    p, ni = float(v.mean()), len(v) / h
    lo, hi = wilson(int(round(p * ni)), max(int(round(ni)), 1))
    return {"sessions": len(v), "n_indep": round(ni, 1), "acc": p, "lo": lo, "hi": hi}


def paired(hit_c: pd.Series, hit_a: pd.Series, h: int, a: int, b: int, n_boot: int = N_BOOT) -> dict:
    m = (hit_c.index.year >= a) & (hit_c.index.year <= b)
    x, z = hit_c[m].values, hit_a.reindex(hit_c.index)[m].values
    both = np.isfinite(x) & np.isfinite(z)
    x, z = x[both], z[both]
    n = len(x)
    if n < 5:
        return {"diff": np.nan, "diff_lo": np.nan, "diff_hi": np.nan}
    block = max(63, 2 * h)
    rng = np.random.default_rng(SEED)
    nb = int(np.ceil(n / block))
    d = x - z
    out = np.empty(n_boot)
    for i in range(n_boot):
        st = rng.integers(0, n, nb)
        idx = (st[:, None] + np.arange(block)[None, :]).ravel()[:n] % n
        out[i] = d[idx].mean()
    return {"diff": float(d.mean()), "diff_lo": float(np.percentile(out, 2.5)), "diff_hi": float(np.percentile(out, 97.5))}


def side_of(P: pd.DataFrame) -> pd.Series:
    return B.count(P)["side"]


def bot_stats(P: pd.DataFrame, y: pd.Series, a: int = 2010, b: int = 2026) -> dict:
    m = (P.index.year >= a) & (P.index.year <= b) & y.notna().values & (y != 0).values
    V = np.where(P.values > 0.5, 1.0, np.where(np.isfinite(P.values), -1.0, np.nan))[m]
    H = (V == y.values[m][:, None]).astype(float)
    H[~np.isfinite(V)] = np.nan
    ind = np.nanmean(H, axis=0)
    ch, cv = pd.DataFrame(H).corr().values, pd.DataFrame(V).corr().values
    iu = np.triu_indices_from(ch, 1)
    return {"median": float(np.nanmedian(ind)), "q25": float(np.nanquantile(ind, .25)), "q75": float(np.nanquantile(ind, .75)), "worst": float(np.nanmin(ind)),
            "best": float(np.nanmax(ind)), "share_above_50": float((ind > 0.5).mean()), "corr_right": float(np.nanmean(ch[iu])), "corr_votes": float(np.nanmean(cv[iu])),
            "mean_majority_pct": float(B.count(P)["pct"][m].mean())}


# ============================================================================= run
def _pfile(tr: str, h: int, tgt: str = "eur") -> Path:
    return PROC / f"{ARM}_p_{tr}_h{h}_{tgt}.parquet"


def get_votes(F, S, tr: str, h: int, targets=("eur",)):
    fs = [_pfile(tr, h, t) for t in targets]
    kf, lf = PROC / f"{ARM}_kept_{tr}_h{h}.parquet", PROC / f"{ARM}_leak_{tr}_h{h}.parquet"
    if all(f.exists() for f in fs) and kf.exists():
        return {t: pd.read_parquet(f) for t, f in zip(targets, fs)}, pd.read_parquet(kf), pd.read_parquet(lf)
    P, kept, leak = walk(F, S[tr], h, targets, tag=tr)
    for t, f in zip(targets, fs):
        q = P[t].astype("float32")
        q.columns = q.columns.astype(str)
        q.to_parquet(f)
    kept.to_parquet(kf)
    leak.to_parquet(lf)
    return {t: pd.read_parquet(f) for t, f in zip(targets, fs)}, kept, leak


def coverage(F: dict) -> pd.DataFrame:
    rows = []
    for c in PAIRS:
        x = F[c]
        for col in POOL:
            v = x[col].dropna()
            a = x[col].loc["1999-01-04":]
            rows.append({"pair": c, "column": col, "family": FAMILY[col], "first": str(v.index[0].date()) if len(v) else "", "last": str(v.index[-1].date()) if len(v) else "",
                         "share_present_1987_98": round(float(x[col].loc["1987-02-01":"1998-12-31"].notna().mean()), 3), "share_present_1999_on": round(float(a.notna().mean()), 3)})
    return pd.DataFrame(rows)


def reconcile(F, S) -> pd.DataFrame:
    """With one pair the pooled fold must be the product's own run_bot, bot for bot."""
    rows = []
    for tr in ("a", "b"):
        x = F["eur"][F["eur"].index >= S[tr]["eur"]].copy()
        x.index = pd.DatetimeIndex(x.index).tz_localize("UTC")
        x["__ct"] = pd.DatetimeIndex(x["__ct"]).tz_localize("UTC")
        for g in B.GAUGES:
            x[f"g_{g}"] = np.nan
        for h in (21, 63):
            x[f"yend{h}"] = pd.DatetimeIndex(x[f"yend{h}"]).tz_localize("UTC")
            x[f"dn{h}"], x[f"up{h}"] = np.nan, np.nan
            fo = Fold(F, S[tr], h)
            for Y in (2010, 2019, 2026):
                rws = np.asarray(x.index.year == Y)
                d, same = 0.0, 0
                for sp in SPECS:
                    ref = B.run_bot(x, sp, h, pd.Timestamp(f"{Y}-01-01", tz="UTC"), rws)
                    mine = fo.run(sp, Y)
                    d = max(d, float(np.nanmax(np.abs(ref["p"] - mine["eur"]))))
                    same += int(list(ref["kept"]) == list(mine["kept"]))
                rows.append({"training": tr, "h": h, "year": Y, "max_abs_diff_p": d, "bots_same_columns": same})
    return pd.DataFrame(rows)


def run(save: bool = True, verbose: bool = True):
    warnings.filterwarnings("ignore")
    F = frames()
    S = row_starts(F)
    y = {c: {h: F[c][f"y{h}"] for h in HORIZONS} for c in PAIRS}
    cov = coverage(F)
    cov.to_csv(RES / f"{ARM}_coverage.csv", index=False)
    pd.DataFrame([{"training": t, "pair": c, "first_training_row": str(d.date())} for t, s in S.items() for c, d in s.items()]).to_csv(RES / f"{ARM}_row_starts.csv", index=False)
    pd.DataFrame([{**{k: v for k, v in s.items() if k != "desk"}, "desk": ", ".join(s["desk"])} for s in SPECS]).to_csv(RES / f"{ARM}_roster.csv", index=False)
    rec = reconcile(F, S)
    rec.to_csv(RES / f"{ARM}_reconcile.csv", index=False)
    print("reconcile with bots.run_bot:\n", rec.to_string(index=False), flush=True)
    assert rec["max_abs_diff_p"].max() < 1e-9 and (rec["bots_same_columns"] == B.N_BOTS).all()

    # ---------------------------------------------------------------- the four trainings
    V, KEPT, LEAK = {}, [], []
    for h in (21, 63, 5):
        for tr in ("a", "b", "c", "d"):
            P, kept, leak = get_votes(F, S, tr, h, PAIRS if tr == "c" else ("eur",))
            V[(tr, h)] = P
            KEPT.append(kept.assign(training=tr)); LEAK.append(leak.assign(training=tr))
    KEPT, LEAK = pd.concat(KEPT), pd.concat(LEAK)
    LEAK.to_csv(RES / f"{ARM}_pool_leak_check.csv", index=False)
    assert (LEAK["rows_dated_in_or_after_test_year"] == 0).all()
    allhist = [str(s["bot"]) for s in SPECS if not s["memory"]]
    mem = [str(s["bot"]) for s in SPECS if s["memory"]]
    same_mem = {f"{p}_vs_{q}_h{h}": float(np.nanmax(np.abs(V[(p, h)]["eur"][mem].values - V[(q, h)]["eur"][mem].values))) for p, q in (("b", "a"), ("d", "c")) for h in HORIZONS}
    rows, votes = [], []
    for subset, cols in (("all 100 bots", None), (f"the {len(allhist)} all-history bots", allhist), (f"the {len(mem)} bots with a 5- or 10-year memory", mem)):
        for h in HORIZONS:
            H = {tr: hits(side_of(V[(tr, h)]["eur"] if cols is None else V[(tr, h)]["eur"][cols]), y["eur"][h].reindex(V[(tr, h)]["eur"].index)) for tr in "abcd"}
            for tr in "abcd":
                if cols is None:
                    t = B.count(V[(tr, h)]["eur"])
                    votes.append(t.assign(training=tr, h=h).reset_index(names="date"))
                for era, a, b in ERAS:
                    r = {"bots": subset, "training": tr, "h": h, "era": era, **acc(H[tr], h, a, b)}
                    r.update(paired(H[tr], H["a"], h, a, b) if tr != "a" else {"diff": 0.0, "diff_lo": np.nan, "diff_hi": np.nan})
                    rows.append(r)
    R = pd.DataFrame(rows)
    R.to_csv(RES / f"{ARM}_record.csv", index=False)
    pd.concat(votes)[["date", "training", "h", "up", "down", "side"]].to_csv(RES / f"{ARM}_votes.csv", index=False)

    # ---------------------------------------------------------------- the declared bar
    g = lambda tr, h, era, k="diff": float(R[(R.bots == "all 100 bots") & (R.training == tr) & (R.h == h) & (R.era == era)][k].iloc[0])  # noqa: E731
    ver = []
    for tr in "bcd":
        d21, d63 = 100 * g(tr, 21, "2018-26"), 100 * g(tr, 63, "2018-26")
        e21, e63 = 100 * g(tr, 21, "2010-17"), 100 * g(tr, 63, "2010-17")
        excl = [(g(tr, h, "2018-26", "diff_lo") > 0) or (g(tr, h, "2018-26", "diff_hi") < 0) for h in (21, 63)]
        c1, c2, c3 = d21 >= 2 and d63 >= 2, e21 >= 0 and e63 >= 0, any(excl)
        ver.append({"training": tr, "gain_21_2018_26": d21, "gain_63_2018_26": d63, "gain_21_2010_17": e21, "gain_63_2010_17": e63, "two_points_at_both": c1,
                    "not_worse_2010_17": c2, "interval_excludes_zero_at_one": c3, "ADOPTED": bool(c1 and c2 and c3)})
    VER = pd.DataFrame(ver)
    VER.to_csv(RES / f"{ARM}_verdict.csv", index=False)

    # ---------------------------------------------------------------- description
    st = []
    for h in HORIZONS:
        for tr in "abcd":
            st.append({"training": tr, "h": h, "bots": "all 100", **bot_stats(V[(tr, h)]["eur"], y["eur"][h].reindex(V[(tr, h)]["eur"].index))})
            st.append({"training": tr, "h": h, "bots": "all-history", **bot_stats(V[(tr, h)]["eur"][allhist], y["eur"][h].reindex(V[(tr, h)]["eur"].index))})
    ST = pd.DataFrame(st)
    ST.to_csv(RES / f"{ARM}_single_bots.csv", index=False)
    KEPT["family"] = KEPT["col"].map(FAMILY)
    n = KEPT.groupby(["training", "h"]).size().rename("slots")
    CO = (KEPT.groupby(["training", "h", "family", "col"]).size().rename("kept").reset_index().merge(n.reset_index(), on=["training", "h"]))
    CO["share"] = CO["kept"] / CO["slots"]
    CO.to_csv(RES / f"{ARM}_columns_kept.csv", index=False)
    oth = []
    for h in HORIZONS:
        for c in PAIRS:
            P = V[("c", h)][c]
            yy = y[c][h].reindex(P.index)
            Hc, Hu = hits(side_of(P), yy), hits(pd.Series(1.0, index=P.index), yy)
            for era, a, b in ERAS:
                oth.append({"pair": c, "h": h, "era": era, **acc(Hc, h, a, b), "always_up": acc(Hu, h, a, b)["acc"],
                            "median_bot": bot_stats(P, yy, a, b)["median"]})
    OT = pd.DataFrame(oth)
    OT.to_csv(RES / f"{ARM}_other_pairs.csv", index=False)
    PR = product_compare(V, F)
    PR.to_csv(RES / f"{ARM}_vs_product.csv", index=False)
    CT = controls(F, S, V)
    CT.to_csv(RES / f"{ARM}_controls.csv", index=False)
    PH = posthoc(F, S, V)
    write_report(R, VER, ST, CO, OT, PR, CT, cov, S, rec, LEAK, same_mem, len(allhist), PH)
    if verbose:
        pd.set_option("display.width", 250); pd.set_option("display.max_rows", 500)
        print(VER.to_string(index=False))
        print(R[(R.bots == "all 100 bots")].round(3).to_string(index=False))
        print(CT.to_string(index=False))
    return R, VER


def product_compare(V, F) -> pd.DataFrame:
    """The product's bots and the generic baseline on the PRODUCT's own sessions and closes (2010-26)."""
    D = pd.read_parquet(PROC / "features_daily.parquet", columns=["close", "close_time"])
    cd = pd.DatetimeIndex(D["close_time"]).tz_convert("America/New_York").normalize().tz_localize(None)
    lc = pd.Series(np.log(D["close"].values), index=D.index)
    rows = []
    for h in HORIZONS:
        yp = np.sign(lc.shift(-h) - lc)
        f = RES / f"bots_votes_h{h}.parquet"
        if not f.exists():
            continue
        T = pd.read_parquet(f)
        sp = T["side"].reindex(D.index)
        gen = pd.Series(side_of(V[("a", h)]["eur"]).reindex(cd).values, index=D.index)
        Hp, Hg = hits(sp.fillna(0.0), yp), hits(gen.fillna(0.0), yp)
        Hh = hits(side_of(V[("a", h)]["eur"]), F["eur"][f"y{h}"].reindex(V[("a", h)]["eur"].index))
        for era, a, b in ERAS[:3]:
            rows.append({"what": "product bots (74 EUR-specific columns), product closes", "h": h, "era": era, **acc(Hp, h, a, b)})
            rows.append({"what": "generic baseline (a), same votes scored on product closes", "h": h, "era": era, **acc(Hg, h, a, b), **paired(Hg, Hp, h, a, b)})
            rows.append({"what": "generic baseline (a), H.10 fixings (this arm's scoring)", "h": h, "era": era, **acc(Hh, h, a, b)})
    return pd.DataFrame(rows)


def controls(F, S, V) -> pd.DataFrame:
    f = RES / f"{ARM}_controls.csv"
    if f.exists():
        return pd.read_csv(f)
    rows = []
    # ---- look-ahead: the harness must find a column that knows the future
    sp2 = [spec(i, ("peek",)) for i in range(B.N_BOTS)]
    P, kept, _ = walk(F, S["a"], 21, specs=sp2, tag="peek")
    H = hits(side_of(P["eur"]), F["eur"]["y21"].reindex(P["eur"].index))
    rows.append({"control": "look-ahead column on every desk, training (a)", "h": 21, "era": "2010-26", **acc(H, 21, 2010, 2026),
                 "note": f"{100 * (kept.col == 'peek').groupby([kept.year, kept.bot]).any().mean():.0f} % of bot-years kept it; median bot {100 * bot_stats(P['eur'], F['eur']['y21'].reindex(P['eur'].index))['median']:.1f} %"})
    # ---- shuffled outcomes: one common permutation of the daily returns of every pair, outcomes rebuilt
    for seed in (1, 2, 3):
        rng = np.random.default_rng(SEED + seed)
        n = len(F["eur"])
        perm = rng.permutation(n - 1)
        G = {}
        for c in PAIRS:
            x = F[c].copy()
            r = np.diff(np.log(x["__close"].values))[perm]
            lc = pd.Series(np.r_[0.0, np.cumsum(r)], index=x.index)
            x["ys21"] = np.sign(lc.shift(-21) - lc)
            G[c] = x
        for tr in (("a", "c") if seed == 1 else ("a",)):
            P, _, _ = walk(G, S[tr], 21, ycol="ys21", tag=f"shuffle{seed}{tr}")
            ys = G["eur"]["ys21"].reindex(P["eur"].index)
            H = hits(side_of(P["eur"]), ys)
            rows.append({"control": f"shuffled outcomes, seed {seed}, training ({tr})", "h": 21, "era": "2010-26", **acc(H, 21, 2010, 2026),
                         "note": f"always-up on the same shuffled path {100 * acc(hits(pd.Series(1.0, index=P['eur'].index), ys), 21, 2010, 2026)['acc']:.1f} %; median bot {100 * bot_stats(P['eur'], ys)['median']:.1f} %"})
    # ---- truncation: all inputs cut at 2018-12-31, fold 2018 re-run
    Ft = frames(cutoff="2018-12-31", cache=False)
    St = row_starts(Ft)
    for tr in ("a", "b", "c", "d"):
        for h in (21, 63):
            P, _, _ = walk(Ft, St[tr], h, years=[2018], verbose=False)
            full = V[(tr, h)]["eur"]
            full = full[full.index.year == 2018]
            a, b = P["eur"].values.astype("float32"), full.values
            rows.append({"control": f"truncation at 2018-12-31, training ({tr})", "h": h, "era": "2018", "sessions": len(full), "n_indep": np.nan,
                         "acc": np.nan, "lo": np.nan, "hi": np.nan,
                         "note": f"max |difference in P(up)| {float(np.nanmax(np.abs(a - b))):.2e}; votes that differ {int(((a > 0.5) != (b > 0.5)).sum())} of {a.size}; rows {len(P['eur'])} vs {len(full)}"})
    return pd.DataFrame(rows)


def posthoc(F, S, V) -> tuple[pd.DataFrame, pd.DataFrame]:
    """POST-HOC descriptive checks (see the module docstring)."""
    f1, f2 = RES / f"{ARM}_posthoc_signflip.csv", RES / f"{ARM}_posthoc_vote_direction.csv"
    rows = []
    for h in (21, 63):
        sa = side_of(V[("a", h)]["eur"])
        for tr in "abcd":
            P = V[(tr, h)]["eur"]
            y = F["eur"][f"y{h}"].reindex(P.index)
            s = side_of(P)
            H = hits(s, y)
            m = H.notna() & (P.index.year >= 2010)
            rows.append({"training": tr, "h": h, "up_share": float((s[m] > 0).mean()), "went_up": float((y[m] > 0).mean()), "acc_when_up": float(H[m & (s > 0)].mean()),
                         "acc_when_down": float(H[m & (s < 0)].mean()), "same_side_as_a": float((s == sa.reindex(s.index))[m].mean())})
    D = pd.DataFrame(rows)
    D.to_csv(f2, index=False)
    if f1.exists():
        return pd.read_csv(f1), D
    out = []
    for seed in (1, 2, 3):
        rng = np.random.default_rng(SEED + 100 + seed)
        flip = rng.choice([-1.0, 1.0], len(F["eur"]) - 1)
        G = {}
        for c in PAIRS:
            x = F[c].copy()
            lc = pd.Series(np.r_[0.0, np.cumsum(np.diff(np.log(x["__close"].values)) * flip)], index=x.index)
            x["ys21"] = np.sign(lc.shift(-21) - lc)
            G[c] = x
        for tr in ("a", "c"):
            P, _, _ = walk(G, S[tr], 21, ycol="ys21", verbose=False)
            ys = G["eur"]["ys21"].reindex(P["eur"].index)
            H = hits(side_of(P["eur"]), ys)
            out.append({"control": f"outcomes from sign-flipped daily returns, seed {seed}, training ({tr})", "h": 21, "era": "2010-26", **acc(H, 21, 2010, 2026),
                        "note": f"always-up {100 * acc(hits(pd.Series(1.0, index=P['eur'].index), ys), 21, 2010, 2026)['acc']:.1f} %; median bot {100 * bot_stats(P['eur'], ys)['median']:.1f} %"})
    O = pd.DataFrame(out)
    O.to_csv(f1, index=False)
    return O, D


def write_report(R, VER, ST, CO, OT, PR, CT, cov, S, rec, LEAK, same_mem, n_all, PH):
    pc = lambda d, cols: d.assign(**{c: (100 * d[c]).round(1) for c in cols if c in d})  # noqa: E731
    names = {"a": "(a) EUR/USD 1999+", "b": "(b) + mark era 1987-98", "c": "(c) + six other pairs 1999+", "d": "(d) all pairs 1987+"}
    adopted = VER[VER.ADOPTED]
    main = pc(R[R.bots == "all 100 bots"], ["acc", "lo", "hi", "diff", "diff_lo", "diff_hi"])
    main["training"] = main["training"].map(names)
    L = ["# Arm DA `bots_experience`: does more experience make the vote better?", "",
         "Code `src/eurusd/arms/bots_experience.py` (design, bar and controls in its docstring before any outcome was computed, 2026-11-17). Results `experiments/results/arms/bots_experience_*.csv`.", "",
         "## Verdict", ""]
    if len(adopted):
        L.append(f"**ADOPTED against the declared bar: training ({', '.join(adopted.training)}).**")
    else:
        L.append("**NOT ADOPTED. None of the three expanded trainings meets the declared bar** (at least +2 points over the EUR/USD-only bots at both 21 and 63 sessions in 2018-26, not worse in 2010-17, bootstrap interval excluding zero at one horizon).")
    L += ["", pc(VER.assign(**{c: VER[c] / 100 for c in VER.columns if c.startswith("gain")}), [c for c in VER.columns if c.startswith("gain")]).assign(training=VER.training.map(names)).to_markdown(index=False), "",
          "Gains are accuracy points of the 100-bot majority on EUR/USD against baseline (a).", "",
          "## The table: majority vote on EUR/USD, walk-forward, out of sample", "",
          "`n_indep` = independent votes (sessions / horizon); `lo`-`hi` = Wilson 95 %; `diff` = accuracy minus baseline (a) on the same sessions, with a paired block-bootstrap 95 % interval. 5 sessions is reported, not judged.", ""]
    for h in (21, 63, 5):
        L += [f"### {h} sessions", "", main[main.h == h][["training", "era", "acc", "n_indep", "lo", "hi", "diff", "diff_lo", "diff_hi"]].to_markdown(index=False), ""]
    L += ["## Bots that can actually see the extra years", "",
          f"A bot with a 5- or 10-year memory never sees 1987-98 from a 2010+ fold, so for those {100 - n_all} bots (b) = (a) and (d) = (c) by construction "
          f"(checked: largest difference in any P(up) {max(same_mem.values()):.1e}). Only the {n_all} all-history bots can use the mark era; their own majority:", ""]
    sub = pc(R[R.bots.str.contains("all-history") & R.h.isin([21, 63])], ["acc", "lo", "hi", "diff", "diff_lo", "diff_hi"])
    sub["training"] = sub["training"].map(names)
    L += [sub[["training", "h", "era", "acc", "n_indep", "lo", "hi", "diff", "diff_lo", "diff_hi"]].to_markdown(index=False), "",
          "## One bot at a time, and how alike the bots are (EUR/USD, 2010-26)", "",
          "`corr_right` = mean correlation between two bots of being right; `corr_votes` = of their votes; `mean_majority_pct` = average size of the majority.", "",
          pc(ST, ["median", "q25", "q75", "worst", "best", "share_above_50", ]).round(3).assign(training=ST.training.map(names)).to_markdown(index=False), "",
          "## What the bots chose to trust: share of kept columns by family", ""]
    fam = CO.groupby(["h", "training", "family"])["share"].sum().unstack("training").reset_index()
    for c in "abcd":
        fam[c] = (100 * fam[c]).round(1)
    pool_share = pd.Series(FAMILY).drop("peek").value_counts() / len(POOL)
    fam["share_of_the_31_columns"] = fam["family"].map((100 * pool_share).round(1))
    L += [fam.rename(columns=names).to_markdown(index=False), "", "Single columns kept most often (share of all kept slots, %, 21 sessions):", ""]
    top = CO[CO.h == 21].pivot_table(index="col", columns="training", values="share", fill_value=0.0) * 100
    L += [top.sort_values("a", ascending=False).round(1).rename(columns=names).reset_index().to_markdown(index=False), "",
          "## The pooled (c) bots scored on every pair", "",
          "The same pooled model; each pair's rows standardised on its own history. `always_up` = share of sessions the currency rose.", "",
          pc(OT[OT.h.isin([21, 63]) & OT.era.isin(["2010-26", "2018-26"])], ["acc", "lo", "hi", "always_up", "median_bot"])[["pair", "h", "era", "acc", "n_indep", "lo", "hi", "always_up", "median_bot"]].to_markdown(index=False), "",
          "## Generic evidence against the product's own bots", "", pc(PR, ["acc", "lo", "hi", "diff", "diff_lo", "diff_hi"]).drop(columns=["sessions"]).to_markdown(index=False), "",
          "## Controls", "", pc(CT, ["acc", "lo", "hi"]).to_markdown(index=False), "",
          "Reconciliation: with one pair the pooled fold reproduces `bots.run_bot` bot for bot "
          f"(largest difference in P(up) {rec.max_abs_diff_p.max():.1e} over {len(rec)} fold checks of 100 bots; same kept columns for every bot).",
          f"Pooling leak rule: {len(LEAK)} (training, horizon, year, pair) cells; training rows dated in or after the test year: {int(LEAK.rows_dated_in_or_after_test_year.sum())}; "
          "every training outcome fix is before 1 January of the test year (asserted for every bot and fold; table `bots_experience_pool_leak_check.csv`).", "",
          "## Training rows", "", pd.DataFrame([{"training": names[t], **{c: str(d.date()) for c, d in s.items()}} for t, s in S.items()]).fillna("").to_markdown(index=False), "",
          "## Which column exists from when (first date; share of sessions present before / after 1999)", ""]
    cv = cov.pivot(index="column", columns="pair", values="first").reindex(POOL)[list(PAIRS)]
    L += [cv.reset_index().to_markdown(index=False), "",
          "Share of 1987-98 sessions on which the column is present:", "",
          cov.pivot(index="column", columns="pair", values="share_present_1987_98").reindex(POOL)[list(PAIRS)].reset_index().to_markdown(index=False), ""]
    Lp = ["## Post-hoc checks (added after the declared run was read; descriptive)", "",
          "Outcomes rebuilt from daily returns with random signs (no structure left, no fixed total): what the harness scores on pure noise.", "",
          pc(PH[0], ["acc", "lo", "hi"]).to_markdown(index=False), "",
          "Vote direction on EUR/USD, 2010-26 (`up_share` = share of sessions the majority voted UP; `went_up` = share that rose):", "",
          pc(PH[1], ["up_share", "went_up", "acc_when_up", "acc_when_down", "same_side_as_a"]).assign(training=PH[1].training.map(names)).to_markdown(index=False), ""]
    text = "\n".join(L) + "\n"
    head = (ROOT / "reports" / f"arm_{ARM}_notes.md")
    notes = head.read_text() if head.exists() else ""
    i = text.index("## The table")
    j = text.index("## Training rows")
    top, _, end = notes.partition("<!-- END -->")           # hand-written reading (top) and the plain answer (end)
    (ROOT / "reports" / f"arm_{ARM}.md").write_text(text[:i] + top + text[i:j] + "\n".join(Lp) + "\n" + text[j:] + end)


if __name__ == "__main__":
    run()
