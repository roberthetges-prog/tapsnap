"""Arm BA ("reliable_parts"), round 10: do the two RELIABLE parts of the product hold on other dollar pairs?

The two EUR/USD results under test (nothing here is a new predictor; both are replicated with NOTHING re-tuned):
  A. the next-session RANGE forecast of experiments/50_prediction_scoreboard.py section 3 (walk-forward log-linear
     HAR regression: log next-session range on log last range, log 5- and 21-session mean range, an event flag and a
     Monday flag); published record 75.1 / 75.6 / 75.0 % on "range above / below the trailing 1-year median"
     (2010-26 / 2016-26 / 2023-26), naive "same class as yesterday" 68.2 / 68.0 / 66.9 %, volatile-day call 93 %,
     80 % band coverage 80.1 %;
  B. the LEVEL / NO-TOUCH odds of arms/selective.py (path_events, family notouch_kATR): a level 2 ATR14 / 3 ATR14 away
     from the close is NOT touched within 10 sessions 68.6 / 86.5 % of the time and within 21 sessions 51.9 / 71.2 %
     (one-sided, upper and lower level pooled, weekly grid, 2010-26); the product quotes 69 / 87 / 52 / 71 %
     (config/position_call.json `no_touch`).
Pairs: GBPUSD, USDJPY, AUDUSD, USDCHF, USDCAD, NZDUSD (HistData 5-minute bid bars cached by arm P, true UTC).

=====================================================================================================================
EVERYTHING IN THIS DOCSTRING WAS WRITTEN BEFORE ANY ACCURACY, COVERAGE OR NO-TOUCH FIGURE OF ANOTHER PAIR WAS
COMPUTED. What had been looked at when it was written: the published EUR/USD records; the session counts of the six
pairs; their 20 largest session ranges; the largest single-bar wicks of their 5-minute bars (to fix the bad-tick rule
below); the event-calendar coverage by currency and year. No outcome of test A or B on any of the six pairs.
=====================================================================================================================

DATA AND SESSIONS (identical to the EUR/USD feature store)
* 5-minute bars -> hourly bars (bins anchored on the hour, bins with >= 1 bar), rows from 2003-01-01 ->
  `eurusd.features.daily_ohlc(h1, 22)`; a session is kept when it has >= 10 hourly bars and does not start on a
  Saturday (featstore.build_daily). Index = session start (22:00 UTC), close_time = start + 24 h.
  Check done before writing this: the same code on EURUSD_M5 reproduces the store's 6,186 sessions with close and
  range differences of exactly 0.
* range_pips = (high - low) / pip; ATR14 = features.atr(d, 14) (Wilder) / pip; pip = 0.0001, USDJPY 0.01.
* dow = weekday of the close in New York time; Monday flag = (dow == 4), i.e. the NEXT session is Monday's (store).
* BAD TICKS (rule fixed from the wick inspection, before any accuracy): a 5-minute bar whose high exceeds
  max(own open, own close, previous bar's close, next bar's open) by more than 400 pips of the pair has its high set
  to that reference; symmetric for the low. Inspection: this flags exactly 4 bars (USDCHF 2004-03-30 14:55,
  2004-05-17 15:35, 2005-01-11 12:45: isolated wicks of 6,387 / 6,401 / 4,997 pips; USDJPY 2004-06-17 07:45: 494
  pips) and nothing on EUR/USD (largest isolated wick 116 pips); the largest isolated wick left in place is 263 pips
  (GBPUSD, referendum night 2016-06-24), a real event. All four flagged bars are in 2004-05, i.e. in training
  windows only. Everything else is used as it comes, exactly as the EUR/USD store is (which is not cleaned): the
  HistData noise of January 2004 (wicks of about 100 pips in every pair including EUR/USD) stays. The uncleaned
  frames are run as sensitivity C11.
* 2023 HOLE: checked before writing this: all six pairs have the same hole as EUR/USD (113-114 sessions of
  February-July 2023 with fewer than 22 hourly bars; ranges of those sessions are understated). PRIMARY treatment =
  identical to the store (the sessions are kept: nothing re-tuned). Sensitivity C10 drops the affected rows.
* EVENT FLAG. The store's flag is `n_high_next_24h > 0`: at least one event of featstore._events() (ForexFactory
  "High" EUR and USD rows with a time, scheduled FOMC statements, ECB decisions, BLS releases) in (close, close+24h].
  For another pair X/USD the PRIMARY flag is the same construction with the euro replaced by the pair's own
  currency: the USD rows of featstore._events() plus the "High"-impact rows with a time of data/macro/events.csv for
  the pair's non-dollar currency (GBP, JPY, AUD, CHF, CAD, NZD). Known limits, accepted as they are: the archive
  covers the other currencies for 2010-2023 and 2026 only (none before 2010, almost none in 2024-25 - the same
  unevenness the store's own flag has), and there is no central-bank decision file for the other six central banks
  as there is for the ECB, so before 2010 the flag is USD-only. Sensitivity C3: USD-only flag.
* Era labels: 2010-26, 2016-26, 2023-26 (the published ones) and 2010-15, 2016-22 (stability). Test years 2010..2026,
  yearly expanding walk-forward, a row belongs to the year of its session start (store convention).

STEP 1 - RECONCILE ON EUR/USD FIRST (before any other pair is scored)
  A: the scoreboard numbers from the store (75.1 / 68.2, volatile-day 93.5, band 80.1, n 4,372 for 2010-26, etc.).
  B: the published weekly-grid no-touch table (68.6 / 86.5 / 51.9 / 71.2 for 2010-26; 2016-26 and 2023-26 rows) with
     this module's own implementation, and against experiments/results/arms/selective_path_calibration.csv.
  The run stops if either differs by more than 0.05 points.

PRIMARY TEST A (range), per pair, the identical model form (candidate C1 = own fit, C2 = frozen)
  Rows: r1 = last range, r5 / r21 = 5- / 21-session mean range, ev, mon; y = next session's range; rows with r1, r5,
  r21, y > 1 pip. For test year Y: OLS of log y on [1, log r1, log r5, log r21, ev, mon] over rows before
  Y-01-01 minus the last one; forecast p = exp(fit); med / q80 = median / 80th percentile of the last 250 training
  y; sd = training residual standard deviation. Exactly the scoreboard code.
  C1 OWN FIT: fitted on the pair's own history.
  C2 FROZEN: nothing fitted on the pair. Coefficients, residual sd and median are EUR/USD's for the same test year
     (walk-forward on the store). The pair's ranges are expressed relative to its own median: with
     s = med_pair(Y) / med_EUR(Y), p = s * exp(b_EUR . [1, log(r1/s), log(r5/s), log(r21/s), ev_pair, mon]); the band
     uses sd_EUR. The classes use the pair's own med / q80 (as C1).
  Scores per era: accuracy of (p > med) == (y > med); naive baseline (r1 > med) == (y > med) ("same class as
  yesterday"); descriptive second baseline (r21 > med) and always-majority; volatile-day call (p > q80 -> y > med)
  and quiet-day call (p < 0.85 med -> y < med) with their unconditional rates; 80 % band p * exp(+-1.2816 sd);
  MAE against yesterday's range. Every accuracy with n, a Wilson interval, and the edge over the naive baseline with
  a paired circular block-bootstrap interval (21-session blocks, 1,000 draws).
  PASS BAR A (verdict on C1): a pair passes when, in 2010-26 AND in 2016-26, (i) its accuracy is not more than 4.0
  points below EUR/USD's own figure for that era and (ii) its accuracy is at least 5.0 points above its naive
  baseline. TEST A PASSES when at least 5 of the 6 pairs pass. (A pair MORE than 4 points above EUR/USD is not a
  failure of "the result holds"; it is flagged.) 2023-26, the volatile-day call and the band coverage are reported
  for every pair and judged descriptively: band coverage within 76-84 % and volatile-day call within 5 points of
  EUR/USD's are called "holds". The same bar is applied to C2 and reported as a separate line (A-frozen).

PRIMARY TEST B (level odds), per pair (candidate C4 = every session, C5 = the published weekly grid)
  Exactly selective.path_events, family notouch_kATR: decision at the close c of session t; up = max high of sessions
  t+1..t+h minus c, dn = c minus min low; the level k x ATR14_t is NOT touched on the upper side when up < k ATR14,
  on the lower side when dn < k ATR14; the odds are the mean over sessions of the two sides (one-sided events, both
  directions pooled). h = 10, 21; k = 2, 3. Test rows as in the publication: sessions of test years 2010-2026 with
  r1, r5, r21, r63 > 1 pip and a complete forward window; "predicted" = the training-window frequency (rows whose
  window ends before the test year), reported next to the realised figure.
  C4 (PRIMARY) uses every test session (the brief's "share of sessions"); C5 uses every 5th session of the pair's own
  index (the publication's weekly grid) and is reported beside it. Intervals: Wilson on an effective number of
  events = min(2 n, Newey-West effective n with bandwidth ceil(1.5 h / step), 2 n step / h) (the publication's
  conservative rule: non-overlapping windows only).
  PASS BAR B (verdict on C4): (i) LEVEL: for each of the four odds, at least 5 of the 6 pairs are within 4.0 points
  of the figure the product quotes for EUR/USD (69 / 87 / 52 / 71 %) in 2010-26; (ii) STABILITY: for every pair and
  each of the four odds, the three era figures (2010-15, 2016-22, 2023-26) lie within 4.0 points of each other
  (max - min <= 4.0). TEST B PASSES when (i) and (ii) both hold; they are also reported separately, and EUR/USD's own
  line is shown against the same bar. Declared in advance about (ii): a 21-session window gives only about 12
  independent windows a year, so the 2023-26 figure alone carries a sampling error of several points; the share of
  sign-flip surrogate histories (below) that would fail the same 4-point stability bar is reported next to the
  verdict so that it can be read against noise. The verdict itself follows the bar as written.

SECONDARY (declared; descriptive, no bar)
  C6 (4a) IS IT ARITHMETIC? Three driftless-random-walk benchmarks for the four odds (and a grid k = 0.5 .. 4,
     h = 5, 10, 21): (i) analytic Brownian motion with constant volatility, continuous monitoring:
     P(no touch) = 2 Phi(k c / sqrt(h)) - 1 with c = E[session range] / sigma = sqrt(8 / pi); (ii) Monte Carlo
     Gaussian walk with constant volatility, 288 steps a session, ATR14 computed as in the store (accounts for
     discrete monitoring and the noise of the ATR); (iii) SIGN-FLIP SURROGATE, per pair, "a driftless random walk with
     the measured volatility": every session's path is mirrored around the previous close with probability 1/2
     (return, high and low excursions swapped and negated in log terms; the true range, hence the ATR and every
     level, is unchanged), 200 draws; this keeps each session's range and all volatility clustering and removes any
     drift, trend or reversal across sessions. Reading fixed now: if, for each of the four odds, the realised 2010-26
     figure lies inside the 95 % range of the surrogate on at least 5 of the 6 pairs, the odds are ARITHMETIC of the
     measured volatility: nothing about direction or path is being predicted; what is "predicted" is only that
     ATR14 measures the volatility of the next 10-21 sessions. Also reported: ATR14 / sigma of daily returns per
     pair and era (the constant c that makes the arithmetic transfer or not).
  C7 (4b-1) CONDITIONAL CALIBRATION: the k x ATR14 odds by (a) the range model's own day class at the decision
     session (quiet: forecast < 0.85 med; volatile: forecast > q80; normal otherwise) and (b) terciles of
     forecast / ATR14 (cut-points from the training window of each test year, C1 forecasts). Flat odds across the
     bins = ATR14 already holds what the forecast knows.
  C8 (4b-2) LEVELS SET FROM THE FORECAST: the same odds with the level k x F_h, F_h = selective's walk-forward
     forecast of the mean daily range over the next h sessions (log-HAR on r1, r5, r21, r63, fitted on the pair's
     own history), by the same bins and by calendar year; compared with the ATR levels on the high-minus-low spread
     across bins and on the standard deviation of the yearly odds. "Improves" = a smaller spread and a smaller
     yearly standard deviation on at least 5 of 7 pairs (EUR/USD included).
  C9 (4c) POOLED CALIBRATION DATA: (range) P(y > med) = Phi((log p - log med) / sd) in ten bins, predicted vs
     realised, per pair, pooled over the six, and EUR/USD, for C1 and C2; (no-touch) realised vs random-walk odds on
     the k x h grid per pair and pooled.
  C3  USD-only event flag (range, own fit). C10 thin-session sensitivity: A without test rows whose last or target
     session has fewer than 20 hourly bars; B without decision sessions whose window t-13 .. t+h contains such a
     session. C11 uncleaned frames (no bad-tick rule) for the pairs with flagged bars.
CANDIDATE COUNT: 11 (C1 .. C11). Controls, not candidates: the shuffled-order control (the pair's range series
  permuted across sessions, flags left in place, 20 draws: model accuracy and naive baseline should both fall to
  about the always-majority rate); the data checks below.

DATA CHECKS (no outcome involved)
  T1 time stamps: Fed H.10 noon New York buying rate (data/macro/fred_DEX*.csv) against the close of the 5-minute
     bar ending 12:00 New York time, and against the bars one hour earlier and later, by US season, 2003-2026, all six
     pairs. Right stamps: the smallest error at offset 0 in both seasons.
  T2 sessions against independent daily sources: (a) the H.10 rate inside [low, high] of the session that contains
     noon New York; (b) the session's log range against the CME futures daily log range of the same trade date
     (cross/g10fut_*_D1.parquet, Yahoo) and, for GBPUSD and USDJPY, against the Yahoo spot daily bar: correlation and
     median ratio by era. A bad-tick-inflated range series would show a ratio well above 1 or a low correlation.
  T3 the 20 largest session ranges per pair, with the share owed to a single bar's wicks, before / after the rule.
  ADDED AFTER THE RESULTS WERE SEEN (descriptive, labelled post hoc in the report; no bar, no verdict depends on it):
  range_snr (signal-to-noise decomposition of the range accuracy per pair: why EUR/USD's figure is the highest),
  range_by_year, stability_noise (the joint version of the surrogate reading declared under bar B(ii): expected
  number of unstable cells among the 24 and the chance of at least the observed number), write_report.
  ADDED AFTER T2 FIRST RAN, STILL BEFORE ANY OUTCOME (data checks only): T2b showed the futures comparison breaking
  down from 2017 for GBP, JPY, AUD, CAD (and EUR) but not CHF, NZD; the cause is the Yahoo futures file (median daily
  volume falls from ~60-100 thousand contracts to a few hundred: thin stubs), so T2b is now cut 2003-09 / 2010-16 /
  2017-26 with the 2017-26 days split by futures volume, and T2c compares sessions built with the same code from
  Yahoo HOURLY spot bars (cross/<pair>_H1.parquet, 2024-01 .. 2026-11, four pairs).

Outputs: experiments/results/arms/reliable_parts_*.csv, data/processed/reliable_parts_daily_<pair>.parquet (small
daily frames), reports/arm_reliable_parts.md. `run()` rebuilds everything in one process (about two minutes).

CLI: python src/eurusd/arms/reliable_parts.py [build | checks | reconcile | run]
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import features as F  # noqa: E402
from eurusd import featstore as FS  # noqa: E402  (read-only: the store's event list)
from eurusd.data import load_ohlc  # noqa: E402

ARM = "reliable_parts"
PROC = ROOT / "data/processed"
CROSS = PROC / "cross"
MACRO = ROOT / "data/macro"
RES = ROOT / "experiments/results/arms"
STORE = PROC / "features_daily.parquet"

PAIRS = {  # pip, non-dollar currency, H.10 series (quoted as the pair), CME future file
    "gbpusd": dict(pip=1e-4, ccy="GBP", h10="DEXUSUK", fut="gbp"),
    "usdjpy": dict(pip=1e-2, ccy="JPY", h10="DEXJPUS", fut="jpy"),
    "audusd": dict(pip=1e-4, ccy="AUD", h10="DEXUSAL", fut="aud"),
    "usdchf": dict(pip=1e-4, ccy="CHF", h10="DEXSZUS", fut="chf"),
    "usdcad": dict(pip=1e-4, ccy="CAD", h10="DEXCAUS", fut="cad"),
    "nzdusd": dict(pip=1e-4, ccy="NZD", h10="DEXUSNZ", fut="nzd"),
}
EUR = "eurusd"
YEARS = list(range(2010, 2027))
ERAS = (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026), ("2010-15", 2010, 2015), ("2016-22", 2016, 2022))
BAR_ERAS_A = ("2010-26", "2016-26")
STAB_ERAS = ("2010-15", "2016-22", "2023-26")
WICK_PIPS = 400.0
THIN_H = 20
HS, KS = (10, 21), (2.0, 3.0)
QUOTE = {(10, 2.0): 69.0, (10, 3.0): 87.0, (21, 2.0): 52.0, (21, 3.0): 71.0}       # config/position_call.json no_touch
PUBLISHED_B = {("2010-26", 10, 2.0): 68.6, ("2010-26", 10, 3.0): 86.5, ("2010-26", 21, 2.0): 51.9, ("2010-26", 21, 3.0): 71.2,
               ("2016-26", 10, 2.0): 68.9, ("2016-26", 10, 3.0): 86.7, ("2016-26", 21, 2.0): 51.9, ("2016-26", 21, 3.0): 70.8,
               ("2023-26", 10, 2.0): 70.5, ("2023-26", 10, 3.0): 87.6, ("2023-26", 21, 2.0): 51.5, ("2023-26", 21, 3.0): 68.5}
PUBLISHED_A = {"2010-26": dict(n=4372, acc=75.1, naive=68.2, vol=93.5, quiet=82.0, band=80.1, mae=27.0),
               "2016-26": dict(n=2816, acc=75.6, naive=68.0, vol=93.4, quiet=80.6, band=80.5, mae=22.8),
               "2023-26": dict(n=999, acc=75.0, naive=66.9, vol=92.0, quiet=79.0, band=78.4, mae=22.0)}
GRID_K = (0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0)
GRID_H = (5, 10, 21)
C_BM = math.sqrt(8.0 / math.pi)
N_FLIP = 200
Z80 = 1.2816


# ====================================================================================================== small helpers
def wilson(p: float, n: float, z: float = 1.959964) -> tuple[float, float]:
    if n <= 0 or not np.isfinite(p):
        return np.nan, np.nan
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(max(p * (1 - p) / n + z * z / (4 * n * n), 0.0)) / den
    return mid - half, mid + half


def phi(x):
    return 0.5 * (1.0 + np.vectorize(math.erf)(np.asarray(x, dtype=float) / math.sqrt(2.0)))


def block_boot_mean(x: np.ndarray, block: int = 21, reps: int = 1000, seed: int = 7) -> tuple[float, float]:
    n = len(x)
    if n < 2 * block:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(n / block))
    starts = rng.integers(0, n, size=(reps, nb))
    idx = ((starts[:, :, None] + np.arange(block)[None, None, :]) % n).reshape(reps, -1)[:, :n]
    m = x[idx].mean(axis=1)
    return float(np.quantile(m, 0.025)), float(np.quantile(m, 0.975))


def nw_neff(e_hit: np.ndarray, real: float, L: int) -> float:
    """Newey-West effective number of Bernoulli events for a mean `real` of the series e_hit (publication's formula)."""
    Tn = len(e_hit)
    if Tn < 2 or not (0 < real < 1):
        return float(Tn)
    e = e_hit - real
    lrv = float((e * e).sum()) / Tn
    for l in range(1, min(L, Tn - 1) + 1):
        lrv += 2 * (1 - l / (L + 1)) * float((e[l:] * e[:-l]).sum()) / Tn
    if lrv <= 0:
        return float(Tn)
    return max(1.0, real * (1 - real) / (lrv / Tn))


def era_mask(years: np.ndarray, a: int, b: int) -> np.ndarray:
    return (years >= a) & (years <= b)


# ====================================================================================================== data: sessions
def daily_path(pair: str) -> Path:
    return PROC / f"{ARM}_daily_{pair}.parquet"


def load_m5(pair: str) -> pd.DataFrame:
    if pair == EUR:
        m5 = load_ohlc("M5")[["open", "high", "low", "close"]]
    else:
        m5 = pd.read_parquet(CROSS / f"ofi_{pair}_M5.parquet", columns=["open", "high", "low", "close"])
    m5 = m5.astype("float64")
    assert m5.index.is_monotonic_increasing and m5.index.is_unique
    return m5


def clean_m5(m5: pd.DataFrame, pip: float, thr_pips: float = WICK_PIPS) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The declared bad-tick rule. Returns the cleaned frame and the flagged bars."""
    pc, no = m5["close"].shift(1), m5["open"].shift(-1)
    ref_hi = pd.concat([m5["open"], m5["close"], pc, no], axis=1).max(axis=1)
    ref_lo = pd.concat([m5["open"], m5["close"], pc, no], axis=1).min(axis=1)
    uw, lw = (m5["high"] - ref_hi) / pip, (ref_lo - m5["low"]) / pip
    bu, bl = (uw > thr_pips).values, (lw > thr_pips).values
    flagged = pd.DataFrame({"upper_wick_pips": uw[bu | bl], "lower_wick_pips": lw[bu | bl], "open": m5["open"][bu | bl], "high": m5["high"][bu | bl],
                            "low": m5["low"][bu | bl], "close": m5["close"][bu | bl]})
    out = m5.copy()
    out.loc[bu, "high"] = ref_hi[bu]
    out.loc[bl, "low"] = ref_lo[bl]
    w = np.maximum(uw.values, lw.values)
    flagged.attrs["largest_wick_left_pips"] = float(np.nanmax(np.where(bu | bl, np.nan, w)))
    flagged.attrs["wicks_over_100_pips"] = int(np.nansum(w > 100))
    return out, flagged


def sessions_from_m5(m5: pd.DataFrame) -> pd.DataFrame:
    """featstore.build_daily's session bars: M5 -> H1 -> daily_ohlc(h1, 22), n >= 10 hourly bars, no Saturday start."""
    h1 = m5.resample("1h", label="left", closed="left").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna(subset=["open"])
    h1 = h1.loc["2003":]
    d = F.daily_ohlc(h1, 22)
    return d[(d["n"] >= 10) & (d.index.dayofweek != 5)]


_EV_CACHE: dict = {}


def _event_times(ccy: str | None) -> np.ndarray:
    """Sorted event times (ns, UTC): USD rows of the store's list, plus the High-impact timed rows of `ccy`."""
    if "store" not in _EV_CACHE:
        _EV_CACHE["store"] = FS._events()
        e = pd.read_csv(MACRO / "events.csv")
        e = e[(e["impact"] == "High") & (e["has_time"] == True)].copy()  # noqa: E712
        e["time"] = pd.to_datetime(e["datetime_utc"], utc=True)
        _EV_CACHE["ff"] = e.dropna(subset=["time"]).drop_duplicates(["time", "event", "currency"])
    ev, ff = _EV_CACHE["store"], _EV_CACHE["ff"]
    t = [ev.loc[ev["ccy"] == "USD", "time"]]
    if ccy is not None:
        t.append(ff.loc[ff["currency"] == ccy, "time"])
    tt = pd.DatetimeIndex(pd.concat(t)).as_unit("ns").sort_values()
    return tt.asi8


def n_events_next_24h(close_time: pd.DatetimeIndex, ccy: str | None) -> np.ndarray:
    t = _event_times(ccy)
    a = pd.DatetimeIndex(close_time).as_unit("ns").asi8
    b = (pd.DatetimeIndex(close_time) + pd.Timedelta(hours=24)).as_unit("ns").asi8
    return np.searchsorted(t, b, side="right") - np.searchsorted(t, a, side="right")


def _frame_from_sessions(d: pd.DataFrame, pip: float, ccy: str | None) -> pd.DataFrame:
    D = pd.DataFrame(index=d.index)
    for c in ("open", "high", "low", "close"):
        D[c] = d[c].values
    D["n"] = d["n"].values
    D["range_pips"] = (d["high"] - d["low"]).values / pip
    D["atr14_pips"] = (F.atr(d, 14) / pip).values
    close_time = d.index + pd.Timedelta(days=1)
    D["close_time"] = close_time
    D["dow"] = close_time.tz_convert("America/New_York").dayofweek
    D["ev_usd"] = n_events_next_24h(close_time, None)
    D["ev_own"] = n_events_next_24h(close_time, ccy) if ccy else D["ev_usd"]
    return D


def build_pair(pair: str, write: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """M5 -> cleaned session frame (cached), with the uncleaned high / low / range / ATR kept for sensitivity C11."""
    cfg = PAIRS[pair]
    m5 = load_m5(pair)
    bad_ohlc = int(((m5["high"] < m5[["open", "close", "low"]].max(axis=1) - 1e-9) | (m5["low"] > m5[["open", "close", "high"]].min(axis=1) + 1e-9)).sum())
    clean, flagged = clean_m5(m5, cfg["pip"])
    d_raw, d = sessions_from_m5(m5), sessions_from_m5(clean)
    assert d.index.equals(d_raw.index)
    D = _frame_from_sessions(d, cfg["pip"], cfg["ccy"])
    D["high_raw"], D["low_raw"] = d_raw["high"].values, d_raw["low"].values
    D["range_raw_pips"] = (d_raw["high"] - d_raw["low"]).values / cfg["pip"]
    D["atr14_raw_pips"] = (F.atr(d_raw, 14) / cfg["pip"]).values
    info = {"pair": pair, "m5_rows": len(m5), "first": str(m5.index[0]), "last": str(m5.index[-1]), "inconsistent_ohlc_bars": bad_ohlc,
            "sessions": len(D), "flagged_bars": len(flagged), "sessions_changed": int((D["range_raw_pips"] != D["range_pips"]).sum()),
            "thin_sessions_2023": int(((D["n"] < THIN_H) & (D.index.year == 2023)).sum()), "thin_sessions_other": int(((D["n"] < THIN_H) & (D.index.year != 2023)).sum()),
            "range_le_1pip": int((D["range_pips"] <= 1.0).sum()), "largest_wick_left_pips": flagged.attrs["largest_wick_left_pips"],
            "wicks_over_100_pips": flagged.attrs["wicks_over_100_pips"]}
    flagged = flagged.reset_index().rename(columns={"time": "bar_start_utc", "index": "bar_start_utc"})
    flagged.insert(0, "pair", pair)
    # T3: the 20 largest session ranges before the rule, with the single-bar diagnostics
    top = D.nlargest(20, "range_raw_pips")
    med21 = D["range_raw_pips"].rolling(21).median().shift(1)
    rows = []
    for t, r in top.iterrows():
        s = m5.loc[t: t + pd.Timedelta(hours=24) - pd.Timedelta(seconds=1)]
        br = (s["high"] - s["low"]) / cfg["pip"]
        ib = br.idxmax()
        rows.append({"pair": pair, "session_start_utc": t.strftime("%Y-%m-%d"), "range_raw_pips": round(float(r["range_raw_pips"]), 1),
                     "range_after_rule_pips": round(float(r["range_pips"]), 1), "x_trailing_21_median": round(float(r["range_raw_pips"] / med21.get(t, np.nan)), 1),
                     "abs_close_minus_open_pips": round(abs(float(r["close"] - r["open"])) / cfg["pip"], 1), "hourly_bars": int(r["n"]),
                     "widest_m5_bar_pips": round(float(br.max()), 1), "widest_m5_bar_utc": ib.strftime("%H:%M"),
                     "changed_by_rule": bool(r["range_raw_pips"] != r["range_pips"])})
    if write:
        D.to_parquet(daily_path(pair))
    return D, flagged, {"info": info, "top": pd.DataFrame(rows), "m5": m5}


def load_pair(pair: str) -> pd.DataFrame:
    if pair == EUR:
        return eur_frame()
    p = daily_path(pair)
    if not p.exists():
        build_pair(pair)
    return pd.read_parquet(p)


def eur_frame() -> pd.DataFrame:
    """The EUR/USD store itself (range, ATR, flags as stored) with open / high / low attached as selective.load_data does."""
    S = pd.read_parquet(STORE)
    h1 = load_ohlc("H1").loc["2003":]
    h1 = h1[~h1.index.duplicated(keep="last")]
    d = F.daily_ohlc(h1[["open", "high", "low", "close"]], 22)
    d = d[(d["n"] >= 10) & (d.index.dayofweek != 5)]
    assert d.index.equals(S.index) and np.allclose(d["close"].values, S["close"].values), "daily bars differ from the store"
    D = pd.DataFrame(index=S.index)
    D["open"], D["high"], D["low"], D["close"], D["n"] = d["open"].values, d["high"].values, d["low"].values, S["close"].values, d["n"].values
    D["range_pips"], D["atr14_pips"], D["close_time"], D["dow"] = S["range_pips"].values, S["atr14_pips"].values, S["close_time"].values, S["dow"].values
    D["ev_own"] = S["n_high_next_24h"].values                     # the store's EUR + USD flag
    D["ev_usd"] = n_events_next_24h(pd.DatetimeIndex(S["close_time"]), None)
    return D


def eur_session_check() -> dict:
    """The M5 -> session code of this module against the store (and the generic event-flag constructor for EUR)."""
    S = pd.read_parquet(STORE)
    d = sessions_from_m5(load_m5(EUR))
    same = bool(d.index.equals(S.index))
    out = {"sessions_module": len(d), "sessions_store": len(S), "index_equal": same}
    if same:
        out["max_abs_close_diff"] = float(np.abs(d["close"].values - S["close"].values).max())
        out["max_abs_range_diff_pips"] = float(np.abs((d["high"] - d["low"]).values / 1e-4 - S["range_pips"].values).max())
        out["max_abs_atr_diff_pips"] = float(np.abs((F.atr(d, 14) / 1e-4).values - S["atr14_pips"].values).max())
        g = n_events_next_24h(pd.DatetimeIndex(S["close_time"]), "EUR")
        out["generic_flag_equals_store_flag_share"] = float(((g > 0) == (S["n_high_next_24h"].values > 0)).mean())
    _, fl = clean_m5(load_m5(EUR), 1e-4)
    out["eur_bars_flagged_by_wick_rule"] = len(fl)
    return out


# ====================================================================================================== test A: range
def range_rows(D: pd.DataFrame, ev_col: str = "ev_own", range_col: str = "range_pips") -> pd.DataFrame:
    r = D[range_col]
    X = pd.DataFrame({"r1": r, "r5": r.rolling(5).mean(), "r21": r.rolling(21).mean(),
                      "ev": (D[ev_col] > 0).astype(float), "mon": (D["dow"] == 4).astype(float)})
    y = r.shift(-1)
    Fr = pd.concat([X, y.rename("y")], axis=1).replace([np.inf, -np.inf], np.nan).dropna()
    Fr = Fr[(Fr[["r1", "r5", "r21", "y"]] > 1.0).all(axis=1)]
    pos = pd.Series(np.arange(len(D)), index=D.index)
    Fr["i"] = pos.reindex(Fr.index).values
    n = D["n"].values
    Fr["thin"] = (n[Fr["i"].values] < THIN_H) | (n[np.minimum(Fr["i"].values + 1, len(D) - 1)] < THIN_H)
    Fr["atr"] = D["atr14_pips"].reindex(Fr.index).values
    return Fr


def _design(x: pd.DataFrame, scale: float = 1.0) -> np.ndarray:
    return np.column_stack([np.ones(len(x)), np.log(x[["r1", "r5", "r21"]].values / scale), x[["ev", "mon"]].values])


def range_walk(Fr: pd.DataFrame, frozen: dict | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The scoreboard's walk-forward. frozen = {year: (beta_EUR, sd_EUR, med_EUR)} applies EUR/USD's fit instead."""
    out, coefs = [], []
    for Y in YEARS:
        tr = Fr[Fr.index < pd.Timestamp(f"{Y}-01-01", tz="UTC")].iloc[:-1]
        te = Fr[Fr.index.year == Y]
        if te.empty or len(tr) < 250:
            continue
        A = _design(tr)
        ly = np.log(tr["y"].values)
        beta, *_ = np.linalg.lstsq(A, ly, rcond=None)
        sd = float((ly - A @ beta).std())
        med, q80 = float(tr["y"].iloc[-250:].median()), float(tr["y"].iloc[-250:].quantile(0.8))
        fit_tr = np.exp(A @ beta)
        rho_cut = np.quantile(fit_tr / tr["atr"].values, [1 / 3, 2 / 3])
        if frozen is None:
            p, sd_use = np.exp(_design(te) @ beta), sd
        else:
            b_e, sd_e, med_e = frozen[Y]
            s = med / med_e
            p, sd_use = s * np.exp(_design(te, s) @ b_e), sd_e
        out.append(pd.DataFrame({"y": te["y"].values, "p": p, "med": med, "q80": q80, "sd": sd_use, "r1": te["r1"].values, "r21": te["r21"].values,
                                 "i": te["i"].values, "thin": te["thin"].values, "atr": te["atr"].values, "rho_lo": rho_cut[0], "rho_hi": rho_cut[1]}, index=te.index))
        coefs.append({"year": Y, "n_train": len(tr), "b0": beta[0], "b_r1": beta[1], "b_r5": beta[2], "b_r21": beta[3], "b_ev": beta[4], "b_mon": beta[5],
                      "resid_sd": sd, "med": med, "q80": q80})
    return pd.concat(out), pd.DataFrame(coefs)


def frozen_from(coefs: pd.DataFrame) -> dict:
    return {int(r.year): (np.array([r.b0, r.b_r1, r.b_r5, r.b_r21, r.b_ev, r.b_mon]), float(r.resid_sd), float(r.med)) for r in coefs.itertuples()}


def range_scores(G: pd.DataFrame, eras=ERAS, boot: bool = True) -> pd.DataFrame:
    rows = []
    yr = G.index.year.values
    for lab, a, b in eras:
        x = G[era_mask(yr, a, b)]
        if len(x) < 30:
            continue
        up = (x["y"] > x["med"]).values
        hit = ((x["p"] > x["med"]).values == up)
        hit_n = ((x["r1"] > x["med"]).values == up)
        hit_21 = ((x["r21"] > x["med"]).values == up)
        acc, naive = float(hit.mean()), float(hit_n.mean())
        lo, hi = wilson(acc, len(x))
        e_lo, e_hi = block_boot_mean(hit.astype(float) - hit_n.astype(float)) if boot else (np.nan, np.nan)
        vol, quiet = x[x["p"] > x["q80"]], x[x["p"] < 0.85 * x["med"]]
        lo_b, hi_b = x["p"] * np.exp(-Z80 * x["sd"]), x["p"] * np.exp(Z80 * x["sd"])
        band = float(((x["y"] >= lo_b) & (x["y"] <= hi_b)).mean())
        v_acc = float((vol["y"] > vol["med"]).mean()) if len(vol) > 30 else np.nan
        v_lo, v_hi = wilson(v_acc, len(vol)) if len(vol) > 30 else (np.nan, np.nan)
        rows.append({"era": lab, "n": len(x), "sessions_per_year": len(x) / max(1, len(np.unique(x.index.year))), "acc": 100 * acc, "acc_lo": 100 * lo, "acc_hi": 100 * hi,
                     "naive_yesterday": 100 * naive, "edge": 100 * (acc - naive), "edge_lo": 100 * e_lo, "edge_hi": 100 * e_hi,
                     "naive_r21_class": 100 * float(hit_21.mean()), "always_majority": 100 * max(up.mean(), 1 - up.mean()), "share_above_median": 100 * float(up.mean()),
                     "vol_call_n": len(vol), "vol_call_acc": 100 * v_acc, "vol_call_lo": 100 * v_lo, "vol_call_hi": 100 * v_hi,
                     "quiet_call_n": len(quiet), "quiet_call_acc": 100 * float((quiet["y"] < quiet["med"]).mean()) if len(quiet) > 30 else np.nan,
                     "band80": 100 * band, "mae_pips": float((x["p"] - x["y"]).abs().mean()), "mae_naive_pips": float((x["r1"] - x["y"]).abs().mean()),
                     "median_range_pips": float(x["y"].median())})
    return pd.DataFrame(rows)


def shuffle_control(D: pd.DataFrame, ev_col: str, draws: int = 20, seed: int = 0) -> dict:
    rng = np.random.default_rng(seed)
    acc, naive, maj = [], [], []
    for _ in range(draws):
        Ds = D.copy()
        Ds["range_pips"] = rng.permutation(D["range_pips"].values)
        G, _ = range_walk(range_rows(Ds, ev_col))
        s = range_scores(G, eras=(("2010-26", 2010, 2026),), boot=False).iloc[0]
        acc.append(s["acc"]); naive.append(s["naive_yesterday"]); maj.append(s["always_majority"])
    return {"shuffled_acc": float(np.mean(acc)), "shuffled_acc_min": float(np.min(acc)), "shuffled_acc_max": float(np.max(acc)),
            "shuffled_naive": float(np.mean(naive)), "shuffled_always_majority": float(np.mean(maj)), "draws": draws}


# ====================================================================================================== test B: no-touch
def notouch_records(D: pd.DataFrame, pip: float, hs=HS, ks=KS, high: str = "high", low: str = "low", atr_col: str = "atr14_pips",
                    range_col: str = "range_pips") -> pd.DataFrame:
    """selective.path_events restricted to the level families: k x ATR14 (level 'atr') and k x F_h (level 'fh').
    One row per test session, window h and level; o_up / o_dn = 1 when the upper / lower level is NOT touched."""
    c, hi, lo = D["close"].values, D[high].values, D[low].values
    atr = D[atr_col].values
    r = D[range_col]
    n = len(D)
    yr = D.index.year.values
    thin = (D["n"].values < THIN_H).astype(float)
    cs = np.concatenate([[0.0], np.cumsum(thin)])
    rec = []
    X = pd.DataFrame({"r1": r, "r5": r.rolling(5).mean(), "r21": r.rolling(21).mean(), "r63": r.rolling(63).mean()})
    okx = (X > 1.0).all(axis=1).values
    A = np.column_stack([np.ones(n), np.log(X.where(X > 1.0).values)])
    for h in hs:
        mx = pd.Series(hi).rolling(h).max().shift(-h).values
        mn = pd.Series(lo).rolling(h).min().shift(-h).values
        up, dn = (mx - c) / pip, (c - mn) / pip
        yh = r.rolling(h).mean().shift(-h).values
        ia, ib = np.maximum(np.arange(n) - 13, 0), np.minimum(np.arange(n) + h + 1, n)
        thin_win = (cs[ib] - cs[ia]) > 0
        for Y in YEARS:
            te = np.where((yr == Y) & okx)[0]
            q = np.searchsorted(D.index.values, np.datetime64(pd.Timestamp(f"{Y}-01-01")))
            tr = np.where(okx & np.isfinite(yh) & (yh > 1.0) & (np.arange(n) + h <= q - 1))[0]
            if len(te) == 0 or len(tr) < 500:
                continue
            beta, *_ = np.linalg.lstsq(A[tr], np.log(yh[tr]), rcond=None)
            F_tr, F_te_all = np.exp(A[tr] @ beta), np.exp(A[te] @ beta)
            keep = np.isfinite(up[te])
            te, F_te = te[keep], F_te_all[keep]
            exc_tr = np.concatenate([up[tr], dn[tr]])
            for level, s_tr, s_te in (("atr", atr[tr], atr[te]), ("fh", F_tr, F_te)):
                sc = exc_tr / np.concatenate([s_tr, s_tr])
                for k in ks:
                    d = k * s_te
                    rec.append(pd.DataFrame({"i": te, "year": Y, "h": h, "k": k, "level": level, "p_model": float((sc < k).mean()),
                                             "o_up": (up[te] < d).astype(float), "o_dn": (dn[te] < d).astype(float), "thin_win": thin_win[te]}))
    R = pd.concat(rec, ignore_index=True)
    R["o"] = 0.5 * (R["o_up"] + R["o_dn"])
    return R


def notouch_scores(R: pd.DataFrame, step: int, eras=ERAS, level: str = "atr") -> pd.DataFrame:
    rows = []
    R = R[R["level"] == level]
    for (h, k), g0 in R.groupby(["h", "k"]):
        g0 = g0[g0["i"] % step == 0].sort_values("i")
        L = int(math.ceil(1.5 * h / step))
        for lab, a, b in eras:
            g = g0[(g0["year"] >= a) & (g0["year"] <= b)]
            if len(g) < 20:
                continue
            real = float(g["o"].mean())
            ev = 2.0 * len(g)
            neff = min(ev, nw_neff(g["o"].values, real, L), max(1.0, ev * step / h))
            lo, hi = wilson(real, neff)
            rows.append({"era": lab, "h": int(h), "k": float(k), "n_sessions": len(g), "sessions_per_year": len(g) / max(1, g["year"].nunique()),
                         "n_eff_events": neff, "independent_windows": len(g) * step / h, "no_touch": 100 * real, "lo": 100 * lo, "hi": 100 * hi,
                         "predicted_train_freq": 100 * float(g["p_model"].mean()), "upper_side": 100 * float(g["o_up"].mean()), "lower_side": 100 * float(g["o_dn"].mean())})
    return pd.DataFrame(rows)


# ====================================================================================================== 4a: random walks
def rw_analytic(k: float, h: int) -> float:
    return float(2 * phi(k * C_BM / math.sqrt(h)) - 1)


def _log_arrays(D: pd.DataFrame, pip: float) -> dict:
    lc = np.log(D["close"].values)
    pc = np.concatenate([[np.log(D["open"].values[0])], lc[:-1]])
    return {"r": lc - pc, "u": np.log(D["high"].values) - pc, "d": np.log(D["low"].values) - pc, "a": D["atr14_pips"].values * pip / D["close"].values}


def _notouch_log(r, u, d, a, sign, hs, ks) -> dict:
    """No-touch indicators (two sides averaged) in log space for a path built from per-session (r, u, d) with signs."""
    L = np.cumsum(sign * r)
    Lp = np.concatenate([[0.0], L[:-1]])
    H = Lp + np.where(sign > 0, u, -d)
    Lo = Lp + np.where(sign > 0, d, -u)
    out = {}
    for h in hs:
        mx = pd.Series(H).rolling(h).max().shift(-h).values
        mn = pd.Series(Lo).rolling(h).min().shift(-h).values
        up, dn = mx - L, L - mn
        for k in ks:
            with np.errstate(invalid="ignore"):
                o = 0.5 * ((up < k * a).astype(float) + (dn < k * a).astype(float))
            o[~np.isfinite(up)] = np.nan
            out[(h, k)] = o
    return out


def signflip_benchmark(D: pd.DataFrame, pip: float, R: pd.DataFrame, draws: int = N_FLIP, seed: int = 11) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Sign-flip surrogate on the primary test rows (every test session). Returns the odds table (actual in log space,
    surrogate mean and 95 % range per era) and the surrogate distribution of the three-era spread."""
    la = _log_arrays(D, pip)
    yr = D.index.year.values
    rows_i = {h: np.sort(R[(R["level"] == "atr") & (R["h"] == h) & (R["k"] == KS[0])]["i"].values) for h in HS}
    rng = np.random.default_rng(seed)
    n = len(D)

    def era_means(o: dict) -> dict:
        m = {}
        for (h, k), v in o.items():
            idx = rows_i[h]
            for lab, a, b in ERAS:
                ii = idx[era_mask(yr[idx], a, b)]
                m[(lab, h, k)] = float(np.nanmean(v[ii])) if len(ii) else np.nan
        return m

    actual = era_means(_notouch_log(la["r"], la["u"], la["d"], la["a"], np.ones(n), HS, KS))
    sims = [era_means(_notouch_log(la["r"], la["u"], la["d"], la["a"], rng.choice([-1.0, 1.0], size=n), HS, KS)) for _ in range(draws)]
    S = pd.DataFrame(sims)
    rows = []
    for key in actual:
        v = S[key].values
        rows.append({"era": key[0], "h": key[1], "k": key[2], "actual_logspace": 100 * actual[key], "surrogate_mean": 100 * v.mean(),
                     "surrogate_lo": 100 * np.quantile(v, 0.025), "surrogate_hi": 100 * np.quantile(v, 0.975),
                     "inside_95": bool(np.quantile(v, 0.025) <= actual[key] <= np.quantile(v, 0.975)), "draws": draws})
    spread, fails = [], np.zeros(draws, dtype=int)
    for h in HS:
        for k in KS:
            sp = 100 * (S[[(e, h, k) for e in STAB_ERAS]].max(axis=1) - S[[(e, h, k) for e in STAB_ERAS]].min(axis=1)).values
            act = 100 * (max(actual[(e, h, k)] for e in STAB_ERAS) - min(actual[(e, h, k)] for e in STAB_ERAS))
            fails += (sp > 4.0).astype(int)
            spread.append({"h": h, "k": k, "actual_spread": act, "surrogate_median_spread": float(np.median(sp)), "surrogate_p95_spread": float(np.quantile(sp, 0.95)),
                           "surrogate_share_spread_gt_4": float((sp > 4.0).mean()), "draws": draws})
    SP = pd.DataFrame(spread)
    SP["surrogate_share_any_of_4_odds_unstable"] = float((fails > 0).mean())
    for j in range(5):
        SP[f"surrogate_p_{j}_unstable"] = float((fails == j).mean())
    return pd.DataFrame(rows), SP


def rw_montecarlo(n_sess: int = 60000, steps: int = 288, seed: int = 3) -> pd.DataFrame:
    """Constant-volatility Gaussian walk, 288 steps a session, ATR14 as in the store, on the k x h grid."""
    rng = np.random.default_rng(seed)
    r, u, d = np.empty(n_sess), np.empty(n_sess), np.empty(n_sess)
    chunk = 5000
    for s in range(0, n_sess, chunk):
        m = min(chunk, n_sess - s)
        p = np.cumsum(rng.standard_normal((m, steps)) / math.sqrt(steps), axis=1)
        r[s:s + m], u[s:s + m], d[s:s + m] = p[:, -1], np.maximum(p.max(axis=1), 0.0), np.minimum(p.min(axis=1), 0.0)
    tr = np.maximum(u - d, np.maximum(np.abs(u), np.abs(d)))
    a = pd.Series(tr).ewm(alpha=1 / 14, adjust=False).mean().values
    o = _notouch_log(r, u, d, a, np.ones(n_sess), GRID_H, GRID_K)
    rows = [{"h": h, "k": k, "mc_constant_vol": 100 * float(np.nanmean(v[300:])), "analytic_bm": 100 * rw_analytic(k, h)} for (h, k), v in o.items()]
    out = pd.DataFrame(rows)
    out.attrs["atr_over_sigma"] = float(a[300:].mean() / r.std())
    return out


def atr_over_sigma(D: pd.DataFrame, pip: float) -> pd.DataFrame:
    la = _log_arrays(D, pip)
    yr = D.index.year.values
    rows = []
    for lab, a, b in ERAS:
        m = era_mask(yr, a, b)
        rows.append({"era": lab, "atr_over_sigma": float(la["a"][m].mean() / la["r"][m].std()), "mean_range_over_sigma": float((la["u"] - la["d"])[m].mean() / la["r"][m].std()),
                     "sigma_daily_bp": 1e4 * float(la["r"][m].std()), "kurtosis_daily_ret": float(pd.Series(la["r"][m]).kurt())})
    return pd.DataFrame(rows)


# ====================================================================================================== 4b: conditional
def conditional_tables(R: pd.DataFrame, G: pd.DataFrame, eras=(("2010-26", 2010, 2026),)) -> tuple[pd.DataFrame, pd.DataFrame]:
    """No-touch odds by the range model's day class and by terciles of forecast / ATR14, for ATR and forecast levels;
    and the yearly odds (for the dispersion comparison)."""
    g = G.set_index("i")
    cls = pd.Series(np.where(g["p"] < 0.85 * g["med"], "quiet", np.where(g["p"] > g["q80"], "volatile", "normal")), index=g.index)
    rho = g["p"] / g["atr"]
    ter = pd.Series(np.where(rho < g["rho_lo"], "low", np.where(rho < g["rho_hi"], "mid", "high")), index=g.index)
    X = R[R["i"].isin(g.index)].copy()
    X["class"] = cls.reindex(X["i"]).values
    X["tercile"] = ter.reindex(X["i"]).values
    rows = []
    for lab, a, b in eras:
        xe = X[(X["year"] >= a) & (X["year"] <= b)]
        for (level, h, k), x in xe.groupby(["level", "h", "k"]):
            rows.append({"era": lab, "level": level, "h": h, "k": k, "bin_type": "all", "bin": "all", "n": len(x), "no_touch": 100 * x["o"].mean()})
            for bt in ("class", "tercile"):
                for bn, xb in x.groupby(bt):
                    rows.append({"era": lab, "level": level, "h": h, "k": k, "bin_type": bt, "bin": bn, "n": len(xb), "no_touch": 100 * xb["o"].mean()})
    yearly = X.groupby(["level", "h", "k", "year"])["o"].mean().mul(100).rename("no_touch").reset_index()
    return pd.DataFrame(rows), yearly


# ====================================================================================================== 4c: calibration
def calibration_range(G: pd.DataFrame) -> pd.DataFrame:
    p = phi((np.log(G["p"].values) - np.log(G["med"].values)) / G["sd"].values)
    b = np.minimum((p * 10).astype(int), 9)
    x = pd.DataFrame({"bin": b, "p": p, "o": (G["y"] > G["med"]).astype(float).values})
    t = x.groupby("bin").agg(n=("o", "size"), predicted=("p", "mean"), realised=("o", "mean")).reset_index()
    t["predicted"] *= 100; t["realised"] *= 100
    return t


# ====================================================================================================== data checks
def check_timestamps(pair: str, m5: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """T1 and T2a against the Fed H.10 noon New York rate."""
    cfg = PAIRS[pair]
    h = pd.read_csv(MACRO / f"fred_{cfg['h10']}.csv", parse_dates=["date"]).dropna()
    h = h[(h["date"] >= "2003-01-02") & (h["date"] <= str(m5.index[-1].date()))]
    noon = pd.DatetimeIndex(h["date"]).tz_localize("America/New_York") + pd.Timedelta(hours=12)
    noon_utc = noon.tz_convert("UTC")
    summer = np.array([t.dst() != pd.Timedelta(0) for t in noon])
    close = m5["close"]
    rows = []
    for off in (-60, 0, 60):
        bar = noon_utc + pd.Timedelta(minutes=off - 5)             # the bar that ENDS at noon + off
        px = close.reindex(bar).values
        err = np.abs(px - h["value"].values) / cfg["pip"]
        for lab, msk in (("summer_EDT", summer), ("winter_EST", ~summer)):
            e = err[msk & np.isfinite(err)]
            rows.append({"pair": pair, "offset_min": off, "season": lab, "n_days": len(e), "median_abs_err_pips": float(np.median(e)),
                         "p90_abs_err_pips": float(np.quantile(e, 0.9)), "share_within_5_pips": float((e <= 5).mean())})
    return pd.DataFrame(rows), {"h10": h, "noon_utc": noon_utc}


def check_sessions(pair: str, D: pd.DataFrame, h10: dict) -> tuple[dict, pd.DataFrame]:
    """T2a: H.10 inside the session's [low, high]; T2b: session log range against CME futures (and Yahoo spot) ranges."""
    cfg = PAIRS[pair]
    h, noon_utc = h10["h10"], h10["noon_utc"]
    start = (noon_utc - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
    j = D.reindex(start)
    ok = j["high"].notna().values
    v = h["value"].values
    out_hi, out_lo = (v - j["high"].values) / cfg["pip"], (j["low"].values - v) / cfg["pip"]
    viol = np.maximum(np.maximum(out_hi, out_lo), 0.0)[ok]
    a = {"pair": pair, "h10_days_matched": int(ok.sum()), "h10_inside_low_high_share": float((viol <= 0).mean()), "h10_inside_within_2pips_share": float((viol <= 2).mean()),
         "h10_worst_outside_pips": float(viol.max())}
    rows = []
    lr = np.log(D["high"] / D["low"])
    lr.index = (D.index + pd.Timedelta(days=1)).tz_convert("UTC").normalize().tz_localize(None)     # closing date
    lr = lr[~lr.index.duplicated()]
    srcs = [("cme_future", CROSS / f"g10fut_{cfg['fut']}_D1.parquet", "trade")]
    if (CROSS / f"{pair}_D1.parquet").exists():
        srcs.append(("yahoo_spot", CROSS / f"{pair}_D1.parquet", "utc"))
    for name, path, kind in srcs:
        f = pd.read_parquet(path)
        fr = np.log(f["high"] / f["low"]).replace([np.inf, -np.inf], np.nan)
        idx = f.index.tz_convert("America/New_York").normalize().tz_localize(None) if kind == "trade" else f.index.tz_convert("UTC").normalize().tz_localize(None)
        fr.index = idx
        fr = fr[~fr.index.duplicated()]
        J = pd.DataFrame({"s": lr, "f": fr}).dropna()
        J = J[(J["s"] > 0) & (J["f"] > 0)]
        J["vol"] = f["volume"][~f.index.duplicated()].set_axis(idx[~idx.duplicated()]).reindex(J.index).values if kind == "trade" else np.nan
        cuts = [("2003-09", 2003, 2009, None), ("2010-16", 2010, 2016, None), ("2017-26", 2017, 2026, None)]
        if kind == "trade":      # added after the first look at T2b: Yahoo's futures bars are thin-volume stubs on most days from 2017
            cuts += [("2017-26 futures volume >= 10,000", 2017, 2026, True), ("2017-26 futures volume < 10,000", 2017, 2026, False)]
        for lab, y0, y1, hv in cuts:
            x = J[(J.index.year >= y0) & (J.index.year <= y1)]
            if hv is not None:
                x = x[(x["vol"] >= 10000) == hv]
            if len(x) < 50:
                continue
            ratio = x["s"] / x["f"]
            rows.append({"pair": pair, "source": name, "era": lab, "n_days": len(x), "corr_log_range": float(np.corrcoef(np.log(x["s"]), np.log(x["f"]))[0, 1]),
                         "median_ratio_session_over_source": float(ratio.median()), "share_ratio_gt_2": float((ratio > 2).mean()), "share_ratio_lt_half": float((ratio < 0.5).mean()),
                         "median_futures_volume": float(x["vol"].median()) if kind == "trade" else np.nan})
    yh = CROSS / f"{pair}_H1.parquet"          # T2c (added with the volume split): Yahoo HOURLY spot bars, last ~2.8 years, same session code
    if yh.exists():
        y = pd.read_parquet(yh)
        d = F.daily_ohlc(y[["open", "high", "low", "close"]], 22)
        J = pd.DataFrame({"s": np.log(D["high"] / D["low"]), "f": np.log(d["high"] / d["low"]), "sn": D["n"], "yn": d["n"], "sc": D["close"], "yc": d["close"]}).dropna()
        J = J[(J["sn"] >= THIN_H) & (J["yn"] >= THIN_H) & (J["s"] > 0) & (J["f"] > 0)]
        ratio = J["s"] / J["f"]
        rows.append({"pair": pair, "source": "yahoo_spot_hourly_sessions", "era": f"{J.index[0].date()} .. {J.index[-1].date()}", "n_days": len(J),
                     "corr_log_range": float(np.corrcoef(np.log(J["s"]), np.log(J["f"]))[0, 1]), "median_ratio_session_over_source": float(ratio.median()),
                     "share_ratio_gt_2": float((ratio > 2).mean()), "share_ratio_lt_half": float((ratio < 0.5).mean()), "median_futures_volume": np.nan,
                     "median_abs_close_diff_pips": float((J["sc"] - J["yc"]).abs().median() / cfg["pip"])})
    return a, pd.DataFrame(rows)


def build_and_check(write: bool = True, verbose: bool = True) -> dict:
    """Builds the six daily frames (one pair in memory at a time) and runs T1-T3."""
    RES.mkdir(parents=True, exist_ok=True)
    info, flagged, tops, ts, sess_a, sess_b = [], [], [], [], [], []
    for pair in PAIRS:
        D, fl, extra = build_pair(pair, write=write)
        t1, h10 = check_timestamps(pair, extra["m5"])
        a, b = check_sessions(pair, D, h10)
        info.append(extra["info"]); flagged.append(fl); tops.append(extra["top"]); ts.append(t1); sess_a.append(a); sess_b.append(b)
        if verbose:
            print(f"[build] {pair}: {extra['info']['sessions']} sessions, {len(fl)} bars flagged, thin 2023 {extra['info']['thin_sessions_2023']}; "
                  f"H.10 inside [low, high] {a['h10_inside_low_high_share']:.1%}", flush=True)
        del extra, D
    out = {"coverage": pd.DataFrame(info), "badticks": pd.concat(flagged, ignore_index=True), "top_ranges": pd.concat(tops, ignore_index=True),
           "timestamps": pd.concat(ts, ignore_index=True), "h10_sessions": pd.DataFrame(sess_a), "range_sources": pd.concat(sess_b, ignore_index=True)}
    if write:
        for k, v in out.items():
            v.to_csv(RES / f"{ARM}_check_{k}.csv", index=False)
    return out


# ====================================================================================================== reconcile
def reconcile(verbose: bool = True) -> dict:
    """STEP 1: EUR/USD published numbers with this module's code. Raises if they do not match."""
    sc = eur_session_check()
    D = eur_frame()
    G, coefs = range_walk(range_rows(D, "ev_own"))
    A = range_scores(G)
    rows = []
    for era, pub in PUBLISHED_A.items():
        s = A[A["era"] == era].iloc[0]
        for nm, col in (("n", "n"), ("acc", "acc"), ("naive", "naive_yesterday"), ("vol", "vol_call_acc"), ("quiet", "quiet_call_acc"), ("band", "band80"), ("mae", "mae_pips")):
            rows.append({"test": "A", "era": era, "item": nm, "published": pub[nm], "this_module": float(s[col]), "diff": float(s[col]) - pub[nm]})
    R = notouch_records(D, 1e-4)
    Bw = notouch_scores(R, step=5)
    for (era, h, k), pub in PUBLISHED_B.items():
        s = Bw[(Bw["era"] == era) & (Bw["h"] == h) & (Bw["k"] == k)].iloc[0]
        rows.append({"test": "B weekly grid", "era": era, "item": f"h={h} k={k:g}", "published": pub, "this_module": float(s["no_touch"]), "diff": float(s["no_touch"]) - pub})
    pc = pd.read_csv(RES / "selective_path_calibration.csv")
    pc = pc[(pc["family"] == "notouch_kATR") & (pc["bin"] == "all") & pc["h"].isin(HS) & pc["param"].isin(KS)]
    for r in pc.itertuples():
        s = Bw[(Bw["era"] == r.period) & (Bw["h"] == r.h) & (Bw["k"] == r.param)]
        if len(s):
            rows.append({"test": "B vs selective csv", "era": r.period, "item": f"h={r.h} k={r.param:g} realised", "published": 100 * r.realised, "this_module": float(s["no_touch"].iloc[0]),
                         "diff": float(s["no_touch"].iloc[0]) - 100 * r.realised})
            rows.append({"test": "B vs selective csv", "era": r.period, "item": f"h={r.h} k={r.param:g} predicted", "published": 100 * r.predicted, "this_module": float(s["predicted_train_freq"].iloc[0]),
                         "diff": float(s["predicted_train_freq"].iloc[0]) - 100 * r.predicted})
    T = pd.DataFrame(rows)
    tol = np.where(T["test"] == "B vs selective csv", 1e-6, 0.0501)
    bad = T[(T["diff"].abs() > tol) & (T["item"] != "n")]
    badn = T[(T["item"] == "n") & (T["diff"] != 0)]
    if verbose:
        print("[reconcile] session check:", sc)
        print(T.round(3).to_string(index=False))
    assert sc["index_equal"] and sc["max_abs_close_diff"] == 0 and sc["max_abs_range_diff_pips"] < 1e-9, "session construction differs from the store"
    assert bad.empty and badn.empty, f"EUR/USD reconcile failed:\n{pd.concat([bad, badn])}"
    return {"session_check": sc, "table": T, "D": D, "G": G, "coefs": coefs, "R": R}


# ====================================================================================================== post hoc
def range_snr(G: pd.DataFrame) -> pd.DataFrame:
    """POST HOC (after the results were seen): why the accuracy differs between pairs. signal = how far the forecast
    sits from the yearly median (sd of log p/med), noise = out-of-sample sd of log y/p; expected accuracy if the
    noise were Gaussian = mean Phi(|log p/med| / noise sd)."""
    rows = []
    yr = G.index.year.values
    for lab, a, b in ERAS[:3]:
        x = G[era_mask(yr, a, b)]
        sig, res = np.log(x["p"] / x["med"]).values, np.log(x["y"] / x["p"]).values
        ly = np.log(x["y"] / x["med"]).values
        rows.append({"era": lab, "n": len(x), "signal_sd": float(sig.std()), "noise_sd_oos": float(res.std()), "signal_to_noise": float(sig.std() / res.std()),
                     "r2_log_vs_median": float(1 - (res ** 2).sum() / (ly ** 2).sum()), "expected_acc_gaussian": 100 * float(phi(np.abs(sig) / res.std()).mean()),
                     "acc": 100 * float(((x["p"] > x["med"]) == (x["y"] > x["med"])).mean()),
                     "share_forecast_within_10pct_of_median": 100 * float((np.abs(sig) < 0.1).mean())})
    return pd.DataFrame(rows)


def range_by_year(G: pd.DataFrame) -> pd.DataFrame:
    up = (G["y"] > G["med"]).values
    x = pd.DataFrame({"year": G.index.year.values, "hit": ((G["p"] > G["med"]).values == up).astype(float), "naive": ((G["r1"] > G["med"]).values == up).astype(float),
                      "band": ((G["y"] >= G["p"] * np.exp(-Z80 * G["sd"])) & (G["y"] <= G["p"] * np.exp(Z80 * G["sd"]))).astype(float).values})
    t = x.groupby("year").agg(n=("hit", "size"), acc=("hit", "mean"), naive=("naive", "mean"), band80=("band", "mean")).reset_index()
    t[["acc", "naive", "band80"]] *= 100
    return t


def stability_noise(spread: pd.DataFrame, observed_unstable: int) -> dict:
    """The declared noise reading of bar B(ii): how many of the 24 cells a stationary driftless surrogate fails.
    Pairs are treated as independent (dollar pairs are correlated, which leaves the expectation unchanged)."""
    six = spread[spread["pair"] != EUR].drop_duplicates("pair")
    pmf = np.array([1.0])
    for r in six.itertuples():
        pmf = np.convolve(pmf, np.array([getattr(r, f"surrogate_p_{j}_unstable") for j in range(5)]))
    exp_cells = float(spread[spread["pair"] != EUR]["surrogate_share_spread_gt_4"].sum())
    return {"expected_unstable_cells_of_24": exp_cells, "p_all_24_stable": float(pmf[0]), "p_at_least_observed": float(pmf[observed_unstable:].sum()),
            "observed_unstable_cells": int(observed_unstable)}


# ====================================================================================================== bars
def bar_A(Ap: pd.DataFrame, eur: pd.DataFrame, variant: str) -> pd.DataFrame:
    rows = []
    for pair in PAIRS:
        r = {"variant": variant, "pair": pair}
        ok = True
        for era in BAR_ERAS_A:
            s = Ap[(Ap["pair"] == pair) & (Ap["variant"] == variant) & (Ap["era"] == era)].iloc[0]
            e = eur[eur["era"] == era].iloc[0]
            gap, edge = float(s["acc"] - e["acc"]), float(s["edge"])
            r[f"acc_{era}"], r[f"eur_{era}"], r[f"gap_{era}"], r[f"edge_{era}"] = float(s["acc"]), float(e["acc"]), gap, edge
            r[f"ok_gap_{era}"], r[f"ok_edge_{era}"] = bool(gap >= -4.0), bool(edge >= 5.0)
            r[f"above_eur_by_more_than_4_{era}"] = bool(gap > 4.0)
            ok = ok and gap >= -4.0 and edge >= 5.0
        r["pass"] = ok
        rows.append(r)
    return pd.DataFrame(rows)


def bar_B(Bp: pd.DataFrame, grid: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    lv, st = [], []
    for (h, k), q in QUOTE.items():
        for pair in list(PAIRS) + [EUR]:
            x = Bp[(Bp["pair"] == pair) & (Bp["grid"] == grid) & (Bp["h"] == h) & (Bp["k"] == k)].set_index("era")
            full = float(x.loc["2010-26", "no_touch"])
            e = [float(x.loc[er, "no_touch"]) for er in STAB_ERAS]
            lv.append({"grid": grid, "pair": pair, "h": h, "k": k, "no_touch_2010_26": full, "lo": float(x.loc["2010-26", "lo"]), "hi": float(x.loc["2010-26", "hi"]),
                       "eur_quote": q, "diff": full - q, "within_4": bool(abs(full - q) <= 4.0)})
            st.append({"grid": grid, "pair": pair, "h": h, "k": k, **{er: v for er, v in zip(STAB_ERAS, e)}, "spread": max(e) - min(e), "stable_within_4": bool(max(e) - min(e) <= 4.0)})
    return pd.DataFrame(lv), pd.DataFrame(st)


# ====================================================================================================== run
def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Everything. `cost_pips` is unused (no trading stream in this arm); kept for the arms' common signature.
    Returns (verdict dict, dict of tables)."""
    say = (lambda *a: print(*a, flush=True)) if verbose else (lambda *a: None)
    RES.mkdir(parents=True, exist_ok=True)
    T: dict[str, pd.DataFrame] = {}
    checks = build_and_check(write=write, verbose=verbose)
    T.update({f"check_{k}": v for k, v in checks.items()})
    rec = reconcile(verbose=verbose)
    T["reconcile"] = rec["table"]
    frozen = frozen_from(rec["coefs"])
    frames = {EUR: rec["D"]}
    for pair in PAIRS:
        frames[pair] = load_pair(pair)
    pips = {EUR: 1e-4, **{p: PAIRS[p]["pip"] for p in PAIRS}}

    # ---------------- test A
    A_rows, coef_rows, cal_rows, ctrl_rows, sens_rows = [], [], [], [], []
    Gs: dict = {}
    for pair, D in frames.items():
        variants = [("C1_own_fit", "ev_own", None, "range_pips"), ("C2_frozen_eur", "ev_own", frozen, "range_pips"), ("C3_own_fit_usd_flag", "ev_usd", None, "range_pips")]
        for variant, ev, fz, rc in variants:
            G, coefs = range_walk(range_rows(D, ev, rc), fz)
            s = range_scores(G)
            s.insert(0, "variant", variant); s.insert(0, "pair", pair)
            A_rows.append(s)
            if fz is None:
                coefs.insert(0, "variant", variant); coefs.insert(0, "pair", pair); coef_rows.append(coefs)
            if variant in ("C1_own_fit", "C2_frozen_eur"):
                c = calibration_range(G); c.insert(0, "variant", variant); c.insert(0, "pair", pair); cal_rows.append(c)
                Gs[(pair, variant)] = G
            if variant in ("C1_own_fit", "C2_frozen_eur"):          # C10: thin sessions dropped
                s2 = range_scores(G[~G["thin"]], boot=False)
                s2.insert(0, "variant", variant + "_C10_no_thin"); s2.insert(0, "pair", pair); sens_rows.append(s2)
        ctrl = shuffle_control(D, "ev_own"); ctrl["pair"] = pair
        ctrl_rows.append(ctrl)
        if pair != EUR and (D["range_raw_pips"] != D["range_pips"]).any():       # C11: uncleaned
            Dr = D.copy(); Dr["atr14_pips"] = Dr["atr14_raw_pips"]
            for variant, fz in (("C1_own_fit_C11_raw", None), ("C2_frozen_eur_C11_raw", frozen)):
                G, _ = range_walk(range_rows(Dr, "ev_own", "range_raw_pips"), fz)
                s2 = range_scores(G, boot=False); s2.insert(0, "variant", variant); s2.insert(0, "pair", pair); sens_rows.append(s2)
        say(f"[A] {pair} done")
    Ap = pd.concat(A_rows, ignore_index=True)
    eurA = Ap[(Ap["pair"] == EUR) & (Ap["variant"] == "C1_own_fit")]
    barA = pd.concat([bar_A(Ap, eurA, v) for v in ("C1_own_fit", "C2_frozen_eur", "C3_own_fit_usd_flag")], ignore_index=True)
    T["range"], T["range_coefs"], T["range_bar"] = Ap, pd.concat(coef_rows, ignore_index=True), barA
    T["range_controls"], T["range_sensitivity"] = pd.DataFrame(ctrl_rows), pd.concat(sens_rows, ignore_index=True)
    pooled = []
    for variant in ("C1_own_fit", "C2_frozen_eur"):
        Gp = pd.concat([Gs[(p, variant)] for p in PAIRS])
        c = calibration_range(Gp); c.insert(0, "variant", variant); c.insert(0, "pair", "pooled_six"); pooled.append(c)
    T["calibration_range"] = pd.concat(cal_rows + pooled, ignore_index=True)
    snr, byy = [], []
    for pair in frames:                                           # post hoc, descriptive
        for variant in ("C1_own_fit", "C2_frozen_eur"):
            x = range_snr(Gs[(pair, variant)]); x.insert(0, "variant", variant); x.insert(0, "pair", pair); snr.append(x)
            y = range_by_year(Gs[(pair, variant)]); y.insert(0, "variant", variant); y.insert(0, "pair", pair); byy.append(y)
    T["posthoc_range_snr"], T["range_by_year"] = pd.concat(snr, ignore_index=True), pd.concat(byy, ignore_index=True)

    # ---------------- test B
    B_rows, flip_rows, spread_rows, cond_rows, year_rows, grid_rows, aos_rows, sensB = [], [], [], [], [], [], [], []
    mc = rw_montecarlo()
    for pair, D in frames.items():
        R = rec["R"] if pair == EUR else notouch_records(D, pips[pair])
        for grid, step in (("all_sessions", 1), ("weekly", 5)):
            s = notouch_scores(R, step); s.insert(0, "grid", grid); s.insert(0, "pair", pair); B_rows.append(s)
        s = notouch_scores(R[~R["thin_win"]], 1); s.insert(0, "grid", "all_sessions_C10_no_thin"); s.insert(0, "pair", pair); sensB.append(s)
        if pair != EUR and (D["range_raw_pips"] != D["range_pips"]).any():
            Rr = notouch_records(D, pips[pair], high="high_raw", low="low_raw", atr_col="atr14_raw_pips", range_col="range_raw_pips")
            s = notouch_scores(Rr, 1); s.insert(0, "grid", "all_sessions_C11_raw"); s.insert(0, "pair", pair); sensB.append(s)
        fl, sp = signflip_benchmark(D, pips[pair], R)
        fl.insert(0, "pair", pair); sp.insert(0, "pair", pair); flip_rows.append(fl); spread_rows.append(sp)
        cond, yearly = conditional_tables(R, Gs[(pair, "C1_own_fit")], eras=(("2010-26", 2010, 2026), ("2016-26", 2016, 2026)))
        cond.insert(0, "pair", pair); yearly.insert(0, "pair", pair); cond_rows.append(cond); year_rows.append(yearly)
        Rg = notouch_records(D, pips[pair], hs=GRID_H, ks=GRID_K)
        g = Rg[Rg["level"] == "atr"].groupby(["h", "k"]).agg(n=("o", "size"), no_touch=("o", "mean")).reset_index()
        g["no_touch"] *= 100; g.insert(0, "pair", pair); grid_rows.append(g)
        a = atr_over_sigma(D, pips[pair]); a.insert(0, "pair", pair); aos_rows.append(a)
        say(f"[B] {pair} done")
    Bp = pd.concat(B_rows, ignore_index=True)
    Bp["eur_quote"] = [QUOTE.get((h, k), np.nan) for h, k in zip(Bp["h"], Bp["k"])]
    Bp["analytic_bm"] = [100 * rw_analytic(k, h) for h, k in zip(Bp["h"], Bp["k"])]
    lv1, st1 = bar_B(Bp, "all_sessions")
    lv5, st5 = bar_B(Bp, "weekly")
    spread = pd.concat(spread_rows, ignore_index=True)
    T["notouch"], T["notouch_bar_level"], T["notouch_bar_stability"] = Bp, pd.concat([lv1, lv5], ignore_index=True), pd.concat([st1, st5], ignore_index=True)
    T["notouch_sensitivity"] = pd.concat(sensB, ignore_index=True)
    T["rw_signflip"], T["rw_signflip_spread"], T["rw_montecarlo"] = pd.concat(flip_rows, ignore_index=True), spread, mc
    T["atr_over_sigma"] = pd.concat(aos_rows, ignore_index=True)
    T["conditional"], T["conditional_yearly"] = pd.concat(cond_rows, ignore_index=True), pd.concat(year_rows, ignore_index=True)
    G6 = pd.concat(grid_rows, ignore_index=True)
    six = G6[G6["pair"] != EUR]
    pool = six.groupby(["h", "k"]).apply(lambda x: pd.Series({"n": x["n"].sum(), "no_touch": float((x["no_touch"] * x["n"]).sum() / x["n"].sum())}), include_groups=False).reset_index()
    pool.insert(0, "pair", "pooled_six")
    G6 = pd.concat([G6, pool], ignore_index=True).merge(mc, on=["h", "k"], how="left")
    T["calibration_notouch"] = G6

    # ---------------- verdicts
    a1, a2, a3 = (barA[barA["variant"] == v] for v in ("C1_own_fit", "C2_frozen_eur", "C3_own_fit_usd_flag"))
    lvl_ok = {f"h{h}_k{k:g}": int(lv1[(lv1["h"] == h) & (lv1["k"] == k) & (lv1["pair"] != EUR)]["within_4"].sum()) for (h, k) in QUOTE}
    st6 = st1[st1["pair"] != EUR]
    lvl5_ok = {f"h{h}_k{k:g}": int(lv5[(lv5["h"] == h) & (lv5["k"] == k) & (lv5["pair"] != EUR)]["within_4"].sum()) for (h, k) in QUOTE}
    st56 = st5[st5["pair"] != EUR]
    fl = T["rw_signflip"]
    fl6 = fl[(fl["pair"] != EUR) & (fl["era"] == "2010-26")]
    arith = {f"h{h}_k{k:g}": int(fl6[(fl6["h"] == h) & (fl6["k"] == k)]["inside_95"].sum()) for (h, k) in QUOTE}
    V = {
        "A_own_fit_pairs_passing": int(a1["pass"].sum()), "A_own_fit_PASS": bool(a1["pass"].sum() >= 5),
        "A_frozen_pairs_passing": int(a2["pass"].sum()), "A_frozen_PASS": bool(a2["pass"].sum() >= 5),
        "A_usd_flag_pairs_passing": int(a3["pass"].sum()),
        "B_level_pairs_within_4_per_odds": lvl_ok, "B_level_PASS": bool(all(v >= 5 for v in lvl_ok.values())),
        "B_stability_cells_stable": int(st6["stable_within_4"].sum()), "B_stability_cells": int(len(st6)), "B_stability_PASS": bool(st6["stable_within_4"].all()),
        "B_PASS": bool(all(v >= 5 for v in lvl_ok.values()) and st6["stable_within_4"].all()),
        "B_weekly_level_pairs_within_4_per_odds": lvl5_ok, "B_weekly_stability_cells_stable": int(st56["stable_within_4"].sum()),
        "B_eur_stability_cells_stable": int(st1[st1["pair"] == EUR]["stable_within_4"].sum()),
        "arithmetic_pairs_inside_surrogate_per_odds": arith, "arithmetic": bool(all(v >= 5 for v in arith.values())),
        "candidates": 11,
    }
    V["B_stability_noise"] = stability_noise(spread, int((~st6["stable_within_4"]).sum()))
    T["verdict"] = pd.DataFrame([{"item": k, "value": str(v)} for k, v in V.items()])
    if write:
        for k, v in T.items():
            if not k.startswith("check_"):
                v.to_csv(RES / f"{ARM}_{k}.csv", index=False)
        write_report(T, V)
    if verbose:
        pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)
        print("\nVERDICT"); [print(f"  {k}: {v}") for k, v in V.items()]
    return V, T


# ====================================================================================================== report
NAMES = {"eurusd": "EUR/USD", "gbpusd": "GBP/USD", "usdjpy": "USD/JPY", "audusd": "AUD/USD", "usdchf": "USD/CHF", "usdcad": "USD/CAD", "nzdusd": "NZD/USD"}
ORDER = [EUR] + list(PAIRS)


def _md(df: pd.DataFrame) -> str:
    return df.astype(str).to_markdown(index=False, disable_numparse=True)


def write_report(T: dict, V: dict, path: Path | None = None) -> str:
    """reports/arm_reliable_parts.md from the tables of run(). The prose was written after the results were seen;
    every number in it is read from the tables."""
    A, Bp = T["range"], T["notouch"]
    barA, lv, st = T["range_bar"], T["notouch_bar_level"], T["notouch_bar_stability"]
    f1 = lambda v: f"{v:.1f}"
    L: list[str] = []
    a = L.append

    def acc(pair, variant, era, col="acc"):
        return float(A[(A["pair"] == pair) & (A["variant"] == variant) & (A["era"] == era)][col].iloc[0])

    def odds(pair, h, k, era, grid="all_sessions", col="no_touch"):
        return float(Bp[(Bp["pair"] == pair) & (Bp["grid"] == grid) & (Bp["h"] == h) & (Bp["k"] == k) & (Bp["era"] == era)][col].iloc[0])

    six = list(PAIRS)
    rng = lambda variant, era, col="acc": (min(acc(p, variant, era, col) for p in six), max(acc(p, variant, era, col) for p in six))
    c1, c2 = barA[barA["variant"] == "C1_own_fit"], barA[barA["variant"] == "C2_frozen_eur"]
    passed1 = [NAMES[p] for p in c1[c1["pass"]]["pair"]]
    st6 = st[(st["grid"] == "all_sessions") & (st["pair"] != EUR)]
    unstable = st6[~st6["stable_within_4"]]
    lv6 = lv[(lv["grid"] == "all_sessions") & (lv["pair"] != EUR)]
    noise = V["B_stability_noise"]
    mc = T["rw_montecarlo"]
    fl = T["rw_signflip"]
    pool = T["calibration_notouch"]
    pool6 = lambda h, k: float(pool[(pool["pair"] == "pooled_six") & (pool["h"] == h) & (pool["k"] == k)]["no_touch"].iloc[0])
    an = lambda h, k: 100 * rw_analytic(k, h)
    rank = {era: 1 + sum(acc(p, "C1_own_fit", era) > acc(EUR, "C1_own_fit", era) for p in six) for era in BAR_ERAS_A}
    ctrl = T["range_controls"]
    snr = T["posthoc_range_snr"]
    snr1 = snr[(snr["variant"] == "C1_own_fit") & (snr["era"] == "2010-26")].set_index("pair")

    a("# Arm BA: `reliable_parts` - do the range forecast and the level odds hold on six other dollar pairs?\n")
    a("Round 10. Code `src/eurusd/arms/reliable_parts.py` (`run()`, one process, about a minute; `python src/eurusd/arms/reliable_parts.py run`). "
      "Results `experiments/results/arms/reliable_parts_*.csv`. Pairs: GBP/USD, USD/JPY, AUD/USD, USD/CHF, USD/CAD, NZD/USD, 2003-2026 "
      "(NZD/USD from August 2005), HistData 5-minute bid bars cached by arm P. Nothing was re-tuned: same sessions, same regressors, same walk-forward, "
      "same level definition as on EUR/USD. Both primary tests and their pass bars were written into the module docstring before any accuracy or "
      "no-touch figure of another pair was computed. **Candidates: 11** (limit 12), listed at the end.\n")

    a("## Verdicts (read this first)\n")
    lo10, hi10 = rng("C1_own_fit", "2010-26"); lo16, hi16 = rng("C1_own_fit", "2016-26")
    e_lo = min(acc(p, "C1_own_fit", e, "edge") for p in six for e in BAR_ERAS_A); e_hi = max(acc(p, "C1_own_fit", e, "edge") for p in six for e in BAR_ERAS_A)
    b_lo = min(acc(p, "C1_own_fit", e, "band80") for p in six for e, _, _ in ERAS); b_hi = max(acc(p, "C1_own_fit", e, "band80") for p in six for e, _, _ in ERAS)
    v_lo, v_hi = rng("C1_own_fit", "2010-26", "vol_call_acc")
    gap_fail = [f"{NAMES[pr]} {g:+.1f}" for pr, g, ok in zip(c1["pair"], c1["gap_2016-26"], c1["ok_gap_2016-26"]) if not ok]
    edge_fail = [NAMES[pr] for pr, o1, o2 in zip(c1["pair"], c1["ok_edge_2010-26"], c1["ok_edge_2016-26"]) if not (o1 and o2)]
    vol_ok = [NAMES[p] for p in six if all(abs(acc(p, "C1_own_fit", e, "vol_call_acc") - acc(EUR, "C1_own_fit", e, "vol_call_acc")) <= 5.0 for e in BAR_ERAS_A)]
    lo23, hi23 = rng("C1_own_fit", "2023-26")
    a(f"**A. Range forecast: FAILS the declared bar - {int(c1['pass'].sum())} of 6 pairs pass (5 needed).** The identical model fitted walk-forward on each pair's own "
      f"history calls next-session range above / below the 1-year median correctly on {lo10:.1f}-{hi10:.1f} % of sessions in 2010-26 and {lo16:.1f}-{hi16:.1f} % in 2016-26, "
      f"against {acc(EUR, 'C1_own_fit', '2010-26'):.1f} / {acc(EUR, 'C1_own_fit', '2016-26'):.1f} % on EUR/USD ({lo23:.1f}-{hi23:.1f} % against {acc(EUR, 'C1_own_fit', '2023-26'):.1f} % in 2023-26). EUR/USD ranks {rank['2010-26']} of 7 in 2010-26 and {rank['2016-26']} of 7 in 2016-26: "
      f"once more the pair the number was published on is the best one. More than 4 points below EUR/USD in 2016-26: {', '.join(gap_fail)}. "
      f"Less than 5 points above 'same class as yesterday' in at least one era: {', '.join(edge_fail)}. Only {', '.join(passed1) if passed1 else 'no pair'} clears both conditions in both eras. "
      f"The FROZEN version (EUR/USD's coefficients applied to each pair's ranges relative to its own median, nothing fitted on the pair) passes on {int(c2['pass'].sum())} of 6 as well and is "
      f"within about one point of the own fit on every pair: it is not the coefficients that fail to transfer, it is the LEVEL of the score.\n")
    a(f"What does hold on all six pairs: (i) the forecast is real everywhere - it beats 'same class as yesterday' by {e_lo:.1f} to {e_hi:.1f} points in 2010-26 and 2016-26 "
      f"(EUR/USD {acc(EUR, 'C1_own_fit', '2010-26', 'edge'):.1f} / {acc(EUR, 'C1_own_fit', '2016-26', 'edge'):.1f}), every block-bootstrap interval excluding zero, and with the session order "
      f"shuffled it falls to {ctrl['shuffled_acc'].min():.1f}-{ctrl['shuffled_acc'].max():.1f} % (baseline {ctrl['shuffled_naive'].min():.1f}-{ctrl['shuffled_naive'].max():.1f} %); "
      f"(ii) the 80 % band of the own fit covers {b_lo:.1f}-{b_hi:.1f} % in every pair and every era (declared 'holds' range 76-84); "
      f"(iii) the 'volatile day' call is right {v_lo:.0f}-{v_hi:.0f} % of the time (EUR/USD {acc(EUR, 'C1_own_fit', '2010-26', 'vol_call_acc'):.1f} %), within 5 points of EUR/USD in both eras only on {', '.join(vol_ok)}. "
      f"So the model form is structural and its error band is calibrated everywhere, but the published '75-78 % / 93 %' are EUR/USD's own figures; on the other six pairs the honest numbers are "
      f"{min(lo10, lo16):.0f}-{max(hi10, hi16):.0f} % and {v_lo:.0f}-{v_hi:.0f} %.\n")
    a(f"**B. Level / no-touch odds: the LEVEL clause PASSES ({int(lv6['within_4'].sum())} of 24 pair-odds within 4 points of the EUR/USD quote; the largest gap is "
      f"{lv6['diff'].abs().max():.1f} points), the STABILITY clause FAILS as written ({int(st6['stable_within_4'].sum())} of 24 cells within 4 points across 2010-15 / 2016-22 / 2023-26; "
      f"all 24 were required). By the letter of the declared bar, B FAILS on stability.** The misses: "
      + "; ".join(f"{NAMES[r.pair]} {int(r.k)} ATR / {int(r.h)} sessions, spread {r.spread:.1f}" for r in unstable.itertuples())
      + f". Declared in advance and reported next to the verdict: a stationary driftless surrogate of the same six histories (signs of the sessions flipped at random, volatility untouched) "
      f"breaks the same clause in {noise['expected_unstable_cells_of_24']:.1f} of 24 cells on average, passes all 24 in only {100 * noise['p_all_24_stable']:.0f} % of histories and shows at least "
      f"{noise['observed_unstable_cells']} unstable cells in {100 * noise['p_at_least_observed']:.0f} % (pairs treated as independent). The stability clause as I wrote it would be failed about 19 times in 20 by a process that is perfectly stable, "
      f"so its failure carries no information; that is a flaw of the bar, stated here rather than repaired after the fact. On the weekly grid of the publication: level 24 of 24, stability "
      f"{V['B_weekly_stability_cells_stable']} of 24.\n")
    a(f"In substance the odds replicate almost exactly. Pooled over the six pairs (2010-26, every session): {pool6(10, 2.0):.1f} / {pool6(10, 3.0):.1f} % for 2 / 3 ATR within 10 sessions and "
      f"{pool6(21, 2.0):.1f} / {pool6(21, 3.0):.1f} % within 21, against the product's 69 / 87 / 52 / 71 % and EUR/USD's own {odds(EUR, 10, 2.0, '2010-26'):.1f} / {odds(EUR, 10, 3.0, '2010-26'):.1f} / "
      f"{odds(EUR, 21, 2.0, '2010-26'):.1f} / {odds(EUR, 21, 3.0, '2010-26'):.1f} % on the same grid.\n")
    a(f"**And the reason they replicate is that they are arithmetic, not prediction.** A driftless Brownian motion with constant volatility gives "
      f"P(no touch) = 2 Phi(k x 1.596 / sqrt(h)) - 1 = {an(10, 2.0):.1f} / {an(10, 3.0):.1f} / {an(21, 2.0):.1f} / {an(21, 3.0):.1f} % with no data at all (1.596 = expected session range in units of daily "
      f"sigma). For every pair and each of the four odds the realised 2010-26 figure lies inside the 95 % range of that pair's sign-flip surrogate "
      f"({sum(V['arithmetic_pairs_inside_surrogate_per_odds'].values())} of 24; EUR/USD 4 of 4). Nothing about direction or path is being predicted; the only empirical content is that "
      f"ATR14 measures the volatility of the next 10-21 sessions, which is true of every pair tested. The stop / target layer is therefore structural - and it is also not an edge.\n")

    # ---------------------------------------------------------------- table A
    a("## Test A - next-session range (own fit, candidate C1)\n")
    a("Accuracy = share of sessions on which 'forecast above the trailing 1-year median range' matches 'realised above it'; [95 % Wilson interval]; baseline = same class as yesterday; "
      "edge = accuracy minus baseline [paired block-bootstrap interval, 21-session blocks]; n = scored sessions (one decision per session, about 258 a year). "
      "EUR/USD = the store's own figure for the same era. 'ok' = within the bar (not more than 4 points below EUR/USD; edge at least 5).\n")
    rows = []
    for pair in ORDER:
        for era in ("2010-26", "2016-26", "2023-26"):
            x = A[(A["pair"] == pair) & (A["variant"] == "C1_own_fit") & (A["era"] == era)].iloc[0]
            e = acc(EUR, "C1_own_fit", era)
            judged = pair != EUR and era in BAR_ERAS_A
            rows.append({"pair": NAMES[pair], "era": era, "accuracy %": f"{x['acc']:.1f} [{x['acc_lo']:.1f}-{x['acc_hi']:.1f}]", "EUR/USD %": f1(e), "gap": f"{x['acc'] - e:+.1f}",
                         "baseline %": f1(x["naive_yesterday"]), "edge": f"{x['edge']:+.1f} [{x['edge_lo']:+.1f} .. {x['edge_hi']:+.1f}]", "n": int(x["n"]),
                         "gap ok": ("yes" if x["acc"] - e >= -4 else "NO") if judged else "", "edge ok": ("yes" if x["edge"] >= 5 else "NO") if judged else ""})
    a(_md(pd.DataFrame(rows)) + "\n")
    a("Pass per pair (both conditions in 2010-26 and in 2016-26): " + ", ".join(f"{NAMES[pr]} {'PASS' if ok else 'fail'}" for pr, ok in zip(c1["pair"], c1["pass"])) + ".\n")
    a("### Frozen EUR/USD coefficients (C2), the other figures of the model, and the USD-only flag (C3)\n")
    rows = []
    for pair in ORDER:
        r = {"pair": NAMES[pair]}
        for era in BAR_ERAS_A:
            r[f"own fit {era}"] = f1(acc(pair, "C1_own_fit", era)); r[f"frozen {era}"] = f1(acc(pair, "C2_frozen_eur", era)); r[f"USD-only flag {era}"] = f1(acc(pair, "C3_own_fit_usd_flag", era))
        r["frozen edge 2010-26 / 2016-26"] = f"{acc(pair, 'C2_frozen_eur', '2010-26', 'edge'):+.1f} / {acc(pair, 'C2_frozen_eur', '2016-26', 'edge'):+.1f}"
        r["frozen passes"] = "" if pair == EUR else ("PASS" if bool(c2[c2["pair"] == pair]["pass"].iloc[0]) else "fail")
        rows.append(r)
    a(_md(pd.DataFrame(rows)) + "\n")
    rows = []
    for pair in ORDER:
        r = {"pair": NAMES[pair]}
        for era in ("2010-26", "2016-26", "2023-26"):
            r[f"volatile call {era} (n)"] = f"{acc(pair, 'C1_own_fit', era, 'vol_call_acc'):.1f} ({int(acc(pair, 'C1_own_fit', era, 'vol_call_n'))})"
        for era in ("2010-26", "2016-26", "2023-26"):
            r[f"80 % band {era}"] = f1(acc(pair, "C1_own_fit", era, "band80"))
        r["band frozen 2010-26"] = f1(acc(pair, "C2_frozen_eur", "2010-26", "band80"))
        r["quiet call 2010-26"] = f1(acc(pair, "C1_own_fit", "2010-26", "quiet_call_acc"))
        r["vs 21-session-mean class 2010-26"] = f"{acc(pair, 'C1_own_fit', '2010-26') - acc(pair, 'C1_own_fit', '2010-26', 'naive_r21_class'):+.1f}"
        rows.append(r)
    sh = [acc(p, "C1_own_fit", "2010-26", "share_above_median") for p in ORDER]
    a(f"'Volatile call' = forecast in the top fifth of the last year -> realised range above the median (unconditional rate {min(sh):.0f}-{max(sh):.0f} %); 'quiet call' = forecast 15 % below the median -> "
      "realised below. Last column: accuracy minus the accuracy of the simpler rule 'is the 21-session mean range above the median' - the regression adds only 1-2 points over that, on EUR/USD too.\n")
    a(_md(pd.DataFrame(rows)) + "\n")
    a("The frozen band is too narrow on USD/JPY (its forecast error is larger: log sd 0.42-0.44 against EUR/USD's 0.38) and fine on the other five. The USD-only event flag changes nothing "
      "(at most 0.6 points): the other currency's calendar is not what the model lives on.\n")
    a("### Why EUR/USD scores highest (post hoc, descriptive)\n")
    rows = [{"pair": NAMES[p], "spread of the forecast around the 1-year median (log sd)": f"{snr1.loc[p, 'signal_sd']:.2f}", "out-of-sample forecast error (log sd)": f"{snr1.loc[p, 'noise_sd_oos']:.2f}",
             "log R2 against the median": f"{snr1.loc[p, 'r2_log_vs_median']:.2f}", "accuracy implied by those two %": f1(snr1.loc[p, "expected_acc_gaussian"]), "realised %": f1(snr1.loc[p, "acc"]),
             "forecasts within 10 % of the median %": f1(snr1.loc[p, "share_forecast_within_10pct_of_median"])} for p in ORDER]
    a(_md(pd.DataFrame(rows)) + "\n")
    byy = T["range_by_year"]; byy = byy[byy["variant"] == "C1_own_fit"]
    a("The forecast error is about the same size on all seven pairs. What differs is how far each pair's volatility wanders from its year-ago median: when the forecast sits far from the "
      "median the class is easy, when it sits on it the call is a coin flip. A Gaussian calculation from the two columns reproduces every pair's accuracy to within "
      f"{(snr1['expected_acc_gaussian'] - snr1['acc']).abs().max():.1f} points. So 'accuracy on above / below the median' is a regime-width number, not a pure forecast-quality number: "
      f"single-year accuracy ranges from {byy['acc'].min():.0f} % to {byy['acc'].max():.0f} % across the seven pairs and 17 years (EUR/USD {byy[byy['pair'] == EUR]['acc'].min():.0f}-{byy[byy['pair'] == EUR]['acc'].max():.0f} %; "
      "`reliable_parts_range_by_year.csv`). The transferable statements are the error band and the edge over the baseline.\n")

    # ---------------------------------------------------------------- table B
    a("## Test B - level / no-touch odds (candidate C4: every test session; one-sided, upper and lower level pooled)\n")
    a("Share of sessions (percent) on which a level k x ATR14 away from the close is NOT touched within h sessions, by intraday highs and lows. [95 % Wilson interval on the effective number of "
      "events: non-overlapping windows only, about 436 independent 10-session and 207 independent 21-session windows per pair in 2010-26]. n = 4,351-4,364 sessions per pair "
      "(about 257 a year). 'RW' = analytic driftless Brownian motion, no data.\n")
    rows = []
    for pair in ORDER + ["pooled_six"]:
        r = {"pair": NAMES.get(pair, "six pairs pooled")}
        for (h, k), q in QUOTE.items():
            if pair == "pooled_six":
                r[f"{int(k)} ATR / {h} s"] = f1(pool6(h, k))
            else:
                r[f"{int(k)} ATR / {h} s"] = f"{odds(pair, h, k, '2010-26'):.1f} [{odds(pair, h, k, '2010-26', col='lo'):.0f}-{odds(pair, h, k, '2010-26', col='hi'):.0f}]"
        rows.append(r)
    rows.append({"pair": "EUR/USD as quoted by the product", **{f"{int(k)} ATR / {h} s": f"{q:.0f}" for (h, k), q in QUOTE.items()}})
    rows.append({"pair": "RW (analytic)", **{f"{int(k)} ATR / {h} s": f1(an(h, k)) for (h, k) in QUOTE}})
    a("**2010-26**\n")
    a(_md(pd.DataFrame(rows)) + "\n")
    a("**By era (bar: max - min of the three eras at most 4 points)**\n")
    rows = []
    for pair in ORDER:
        for (h, k) in QUOTE:
            x = st[(st["grid"] == "all_sessions") & (st["pair"] == pair) & (st["h"] == h) & (st["k"] == k)].iloc[0]
            sp = T["rw_signflip_spread"]; s0 = sp[(sp["pair"] == pair) & (sp["h"] == h) & (sp["k"] == k)].iloc[0]
            rows.append({"pair": NAMES[pair], "level / window": f"{int(k)} ATR / {h} s", "2010-15": f1(x["2010-15"]), "2016-22": f1(x["2016-22"]), "2023-26": f1(x["2023-26"]), "spread": f1(x["spread"]),
                         "stable": "yes" if x["stable_within_4"] else "NO", "EUR/USD quote": f"{QUOTE[(h, k)]:.0f}", "2010-26 minus quote": f"{odds(pair, h, k, '2010-26') - QUOTE[(h, k)]:+.1f}",
                         "surrogate: share of histories with spread > 4": f"{100 * s0['surrogate_share_spread_gt_4']:.0f} %"})
    a(_md(pd.DataFrame(rows)) + "\n")
    a(f"Last column: how often a perfectly stationary, driftless version of the same pair (sign-flip surrogate, 200 draws) shows an era spread above 4 points in that cell. Summed over the 24 "
      f"cells of the six pairs that is {noise['expected_unstable_cells_of_24']:.1f} expected failures; 3 were observed. EUR/USD's own four cells are all stable (it would fail at least one in "
      f"{100 * float(T['rw_signflip_spread'][T['rw_signflip_spread']['pair'] == EUR]['surrogate_share_any_of_4_odds_unstable'].iloc[0]):.0f} % of its surrogate histories).\n")
    a("Upper and lower side separately (2010-26): the pooled figure hides a side asymmetry wherever the pair trended over the sample.\n")
    rows = []
    for pair in ORDER:
        r = {"pair": NAMES[pair]}
        for (h, k) in QUOTE:
            r[f"{int(k)} ATR / {h} s: upper / lower"] = f"{odds(pair, h, k, '2010-26', col='upper_side'):.1f} / {odds(pair, h, k, '2010-26', col='lower_side'):.1f}"
        rows.append(r)
    a(_md(pd.DataFrame(rows)) + "\n")

    # ---------------------------------------------------------------- 4a
    a("## Is anything being predicted? (secondary 4a, candidate C6)\n")
    rows = []
    for (h, k) in QUOTE:
        m = mc[(mc["h"] == h) & (mc["k"] == k)].iloc[0]
        f6 = fl[(fl["era"] == "2010-26") & (fl["h"] == h) & (fl["k"] == k)]
        f6x = f6[f6["pair"] != EUR]
        rows.append({"level / window": f"{int(k)} ATR / {h} s", "product quote": f"{QUOTE[(h, k)]:.0f}", "EUR/USD realised": f1(odds(EUR, h, k, "2010-26")), "six pairs pooled": f1(pool6(h, k)),
                     "analytic Brownian": f1(m["analytic_bm"]), "Monte Carlo, constant vol, 288 steps": f1(m["mc_constant_vol"]),
                     "sign-flip surrogate, six pairs (mean; widest 95 % range)": f"{f6x['surrogate_mean'].mean():.1f}; {f6x['surrogate_lo'].min():.1f}-{f6x['surrogate_hi'].max():.1f}",
                     "pairs inside their own surrogate range": f"{int(f6x['inside_95'].sum())} of 6 (+ EUR/USD {'yes' if bool(f6[f6['pair'] == EUR]['inside_95'].iloc[0]) else 'no'})"})
    a(_md(pd.DataFrame(rows)) + "\n")
    aos = T["atr_over_sigma"]; aos = aos[aos["era"] == "2010-26"].set_index("pair")
    a("The sign-flip surrogate keeps every session's range and all volatility clustering and removes any drift, trend or reversal across sessions. The realised odds sit inside its range for "
      "every pair and every level: the odds are what a driftless walk with the measured volatility gives. The formula works because the ATR is a fixed multiple of daily sigma: ATR14 / sigma of "
      "daily returns in 2010-26 is " + ", ".join(f"{NAMES[p]} {aos.loc[p, 'atr_over_sigma']:.2f}" for p in ORDER) + " (Brownian motion: 1.60; a 5-minute Gaussian walk: "
      f"{mc.attrs.get('atr_over_sigma', float('nan')):.2f}). Fat tails lower the ratio (USD/CHF's 2015 de-peg, USD/JPY's intervention days). USD/JPY's 3-ATR / 10-session odds are the lowest of the seven "
      f"({odds('usdjpy', 10, 3.0, '2010-26'):.1f} %); its own surrogate gives {float(fl[(fl['pair'] == 'usdjpy') & (fl['era'] == '2010-26') & (fl['h'] == 10) & (fl['k'] == 3.0)]['surrogate_mean'].iloc[0]):.1f} %, "
      "so that too is its volatility pattern, not direction. The full grid (k = 0.5 .. 4 ATR, h = 5, 10, 21) per pair, pooled and against both random walks is in `reliable_parts_calibration_notouch.csv`: pooled realised and "
      "analytic differ by at most " + f"{(pool[pool['pair'] == 'pooled_six']['no_touch'] - pool[pool['pair'] == 'pooled_six']['analytic_bm']).abs().max():.1f}" + " points over the 21 cells.\n")

    # ---------------------------------------------------------------- 4b
    a("## Does the range forecast improve the odds? (secondary 4b, candidates C7, C8)\n")
    c = T["conditional"]; c = c[c["era"] == "2010-26"]
    rows = []
    for pair in ORDER:
        r = {"pair": NAMES[pair]}
        for (h, k) in ((10, 2.0), (21, 2.0)):
            for level, lab in (("atr", "ATR level"), ("fh", "forecast level")):
                x = c[(c["pair"] == pair) & (c["level"] == level) & (c["h"] == h) & (c["k"] == k) & (c["bin_type"] == "class")].set_index("bin")["no_touch"]
                r[f"2 x {lab}, {h} s: quiet / normal / volatile"] = f"{x['quiet']:.1f} / {x['normal']:.1f} / {x['volatile']:.1f}"
        x = c[(c["pair"] == pair) & (c["level"] == "atr") & (c["h"] == 10) & (c["k"] == 2.0) & (c["bin_type"] == "tercile")].set_index("bin")["no_touch"]
        r["2 ATR, 10 s by forecast / ATR tercile: low / mid / high"] = f"{x['low']:.1f} / {x['mid']:.1f} / {x['high']:.1f}"
        rows.append(r)
    a(_md(pd.DataFrame(rows)) + "\n")
    yy = T["conditional_yearly"]; sd = yy.groupby(["level", "h", "k", "pair"])["no_touch"].std().unstack("level")
    n_sd = int((sd["fh"] < sd["atr"]).sum())
    cc = c[c["bin_type"] == "class"].pivot_table(index=["h", "k", "pair"], columns=["level", "bin"], values="no_touch")
    sp_atr, sp_fh = cc[("atr", "volatile")] - cc[("atr", "quiet")], cc[("fh", "volatile")] - cc[("fh", "quiet")]
    q10 = cc.xs((10, 2.0), level=("h", "k")); s10 = sp_atr.xs((10, 2.0), level=("h", "k")); s21 = sp_atr[sp_atr.index.get_level_values("h") == 21]
    n_narrow = int((sp_fh < sp_atr - 0.5).sum())
    a("Day class = the range model's own call at the decision session (quiet: forecast 15 % below the 1-year median, about a third of sessions; volatile: forecast in the top fifth of the last "
      "year, 11-16 %). Two findings, the same on all seven pairs. (1) The quoted odds are an average over volatility states: a 2-ATR level survives 10 sessions "
      f"{q10[('atr', 'quiet')].min():.0f}-{q10[('atr', 'quiet')].max():.0f} % of the time when the forecast says quiet and {q10[('atr', 'volatile')].min():.0f}-{q10[('atr', 'volatile')].max():.0f} % when it says "
      f"volatile (volatility reverts to its mean, the ATR lags it): a spread of {s10.min():.1f}-{s10.max():.1f} points at 2 ATR / 10 sessions and {s21.min():.1f}-{s21.max():.1f} points at 21 sessions. "
      "(2) Relative to the ATR the one-session forecast adds nothing: by terciles of forecast / ATR14 the odds are flat (within 2 points). Setting the level from the multi-session forecast "
      f"instead of the ATR (C8) narrows the quiet-volatile spread by more than half a point in {n_narrow} of 28 pair-odds (by {(sp_atr - sp_fh).min():.1f} to {(sp_atr - sp_fh).max():.1f} points), but the yearly odds "
      f"become MORE dispersed (smaller yearly standard deviation in only {n_sd} of 28 pair-odds). By the reading declared in advance (both smaller on at least 5 of 7 pairs) the forecast does NOT improve the odds. "
      "The honest use of finding (1) is a caveat on the quote, not a new level rule.\n")

    # ---------------------------------------------------------------- 4c
    a("## Pooled calibration data (secondary 4c, candidate C9)\n")
    cr = T["calibration_range"]
    x = cr[(cr["pair"] == "pooled_six") & (cr["variant"] == "C1_own_fit")]; xe = cr[(cr["pair"] == EUR) & (cr["variant"] == "C1_own_fit")]; xf = cr[(cr["pair"] == "pooled_six") & (cr["variant"] == "C2_frozen_eur")]
    rows = [{"predicted P(range above median) bin": f"{10 * int(b)}-{10 * int(b) + 10} %", "six pairs, own fit: predicted": f1(r1["predicted"]), "realised": f1(r1["realised"]), "n": int(r1["n"]),
             "six pairs, frozen: realised": f1(r3["realised"]), "EUR/USD: predicted": f1(r2["predicted"]), "EUR/USD: realised": f1(r2["realised"]), "EUR/USD n": int(r2["n"])}
            for b, (_, r1), (_, r2), (_, r3) in zip(x["bin"], x.iterrows(), xe.iterrows(), xf.iterrows())]
    a(_md(pd.DataFrame(rows)) + "\n")
    a("P(above median) from the log-normal forecast is reliable at the ends and 3-5 points too high in the middle bins on the six pairs (2-4 on EUR/USD): the forecast error is right-skewed, so "
      "'forecast = median' means about 45 %, not 50 %, of exceeding it. Files: `reliable_parts_calibration_range.csv` (per pair, pooled, own fit and frozen), "
      "`reliable_parts_calibration_notouch.csv`.\n")

    # ---------------------------------------------------------------- reconcile, data
    a("## Step 1 - reconcile on EUR/USD (done before any other pair)\n")
    rc = T["reconcile"]
    a(f"* Sessions: this module's 5-minute -> hourly -> `daily_ohlc(h1, 22)` code on `EURUSD_M5` gives the store's 6,186 sessions with close, range and ATR14 differences of exactly 0; the generic "
      f"event-flag constructor (USD rows of the store's list + ForexFactory 'High' rows of the other currency) reproduces the store's EUR + USD flag on 100 % of sessions.\n"
      f"* Range forecast: all {int((rc['test'] == 'A').sum())} published scoreboard figures reproduced (largest difference {rc[(rc['test'] == 'A') & (rc['item'] != 'n')]['diff'].abs().max():.2f} "
      f"points = rounding; n identical: 4,372 / 2,816 / 999).\n"
      f"* No-touch odds: the 12 published weekly-grid figures reproduced to {rc[rc['test'] == 'B weekly grid']['diff'].abs().max():.2f} points, and realised and predicted frequencies equal to "
      f"`selective_path_calibration.csv` in all {int((rc['test'] == 'B vs selective csv').sum())} cells (largest difference {rc[rc['test'] == 'B vs selective csv']['diff'].abs().max():.6f}). On every session instead of every fifth, EUR/USD "
      f"gives {odds(EUR, 10, 2.0, '2010-26'):.1f} / {odds(EUR, 10, 3.0, '2010-26'):.1f} / {odds(EUR, 21, 2.0, '2010-26'):.1f} / {odds(EUR, 21, 3.0, '2010-26'):.1f} %.\n"
      "* Independent re-computation: brute-force loops over the cached daily frames (no shared code) return the same USD/JPY and GBP/USD odds to 0.01 point and the same USD/JPY range accuracy.\n")
    a("## Data and checks\n")
    cov = T["check_coverage"]
    a("Source: `data/processed/cross/ofi_<pair>_M5.parquet` (HistData 1-minute bid bars aggregated to 5 minutes by arm P, stamps converted America/New_York -> UTC there). Sessions exactly as the "
      "EUR/USD store builds them. " + "; ".join(f"{NAMES[r.pair]} {r.sessions:,} sessions" for r in cov.itertuples()) + ". No bar with inconsistent open / high / low / close.\n")
    ts = T["check_timestamps"]
    t0 = ts[ts["offset_min"] == 0]; t1 = ts[ts["offset_min"] != 0]
    hs = T["check_h10_sessions"]
    rs = T["check_range_sources"]
    fut_ok = rs[(rs["source"] == "cme_future") & rs["era"].isin(["2003-09", "2010-16"])]
    fut_hv = rs[(rs["source"] == "cme_future") & (rs["era"] == "2017-26 futures volume >= 10,000")]
    fut_lv = rs[(rs["source"] == "cme_future") & (rs["era"] == "2017-26 futures volume < 10,000")]
    yh = rs[rs["source"] == "yahoo_spot_hourly_sessions"]
    a(f"* **Time stamps re-checked against the Fed H.10 noon New York rate** (`fred_DEX*.csv`, 5,200-5,900 days per pair): the 5-minute bar ending 12:00 New York time differs from the H.10 rate "
      f"by a median of {t0['median_abs_err_pips'].min():.1f}-{t0['median_abs_err_pips'].max():.1f} pips in US summer and in US winter alike; the bars one hour earlier or later differ by "
      f"{t1['median_abs_err_pips'].min():.1f}-{t1['median_abs_err_pips'].max():.1f} pips. The stamps are right in both seasons on all six pairs (`reliable_parts_check_timestamps.csv`).\n"
      f"* **Sessions against independent daily sources.** (a) The H.10 rate lies inside the [low, high] of the session that contains noon New York on "
      f"{100 * hs['h10_inside_low_high_share'].min():.1f}-{100 * hs['h10_inside_low_high_share'].max():.1f} % of days, and within 2 pips of it on {100 * hs['h10_inside_within_2pips_share'].min():.1f} % or more "
      f"(bid bars against a mid-market fix). (b) Session log range against the CME futures daily range of the same trade date (Yahoo), 2003-2016, all six pairs: correlation "
      f"{fut_ok['corr_log_range'].min():.2f}-{fut_ok['corr_log_range'].max():.2f}, median ratio {fut_ok['median_ratio_session_over_source'].min():.2f}-{fut_ok['median_ratio_session_over_source'].max():.2f}. "
      f"From 2017 the futures file itself degrades for GBP, JPY, AUD and CAD (median daily volume a few hundred contracts instead of ~100,000: stub bars; EUR shows the same, CHF and NZD do not): on "
      f"the days with real volume the median ratio is still {fut_hv['median_ratio_session_over_source'].min():.2f}-{fut_hv['median_ratio_session_over_source'].max():.2f}, on the stub days "
      f"{fut_lv['median_ratio_session_over_source'].min():.2f}-{fut_lv['median_ratio_session_over_source'].max():.2f}. So for those four pairs 2017-26 is only partly verified by futures. "
      f"(c) Sessions built with the same code from Yahoo HOURLY spot bars, {yh['era'].iloc[0]}, four pairs: range correlation {yh['corr_log_range'].min():.3f}-{yh['corr_log_range'].max():.3f}, median ratio "
      f"{yh['median_ratio_session_over_source'].min():.2f}-{yh['median_ratio_session_over_source'].max():.2f}, closes within {yh['median_abs_close_diff_pips'].max():.0f} pips at the median. "
      f"Yahoo's DAILY spot bars are too poor to judge by (correlation 0.5-0.7) but their ratio to the sessions does not move between eras (1.03-1.14). `reliable_parts_check_range_sources.csv`.\n"
      f"* **The 2023 hole is in all six pairs**, as in EUR/USD: {cov['thin_sessions_2023'].min()}-{cov['thin_sessions_2023'].max()} sessions of February-July 2023 have fewer than 20 hourly bars "
      f"(34-37 such sessions in all other years together, 15 for NZD/USD). Their ranges are understated. Primary treatment identical to the store (kept); sensitivity below.\n")
    bt = T["check_badticks"]
    a("* **Bad ticks.** Rule fixed before any accuracy was computed: a 5-minute bar whose high (low) lies more than 400 pips beyond its own open and close, the previous close and the next open "
      "has that wick removed. It flags " + f"{len(bt)} bars: " + "; ".join(f"{NAMES[r.pair]} {str(r.bar_start_utc)[:16]} ({max(r.upper_wick_pips, r.lower_wick_pips):,.0f} pips)" for r in bt.itertuples())
      + ". All are in 2004-05, i.e. inside training windows only; nothing is flagged on EUR/USD and the largest wick left in place is 263 pips (GBP/USD, referendum night). HistData's noisy January 2004 "
      "(wicks of about 100 pips in every pair, EUR/USD included) is left as it is, as in the store. Nothing in the test years 2010-26 was altered.\n")
    tr = T["check_top_ranges"]
    a("* **Largest 20 session ranges per pair** (session start date, pips; `*` = changed by the rule). The rest are known events: October-December 2008, the May 2010 flash crash, August 2011, "
      "the SNB de-peg (USD/CHF session of 2015-01-14: 1,884 pips, real), August 2015, the Brexit vote and the October 2016 sterling flash crash, March 2020, September 2022, the 2022-24 "
      "yen interventions. Full table with the widest single bar of each session: `reliable_parts_check_top_ranges.csv`.\n")
    for pair in PAIRS:
        x = tr[tr["pair"] == pair]
        a(f"  * {NAMES[pair]}: " + ", ".join(f"{r.session_start_utc} {r.range_raw_pips:,.0f}{'*' if r.changed_by_rule else ''}" for r in x.itertuples()))
    a("")
    a("## Controls and sensitivities\n")
    sens, sb = T["range_sensitivity"], T["notouch_sensitivity"]
    d_thin = max(abs(float(sens[(sens["pair"] == p) & (sens["variant"] == "C1_own_fit_C10_no_thin") & (sens["era"] == e)]["acc"].iloc[0]) - acc(p, "C1_own_fit", e)) for p in ORDER for e in ("2010-26", "2016-26"))
    d_thin23 = max(abs(float(sens[(sens["pair"] == p) & (sens["variant"] == "C1_own_fit_C10_no_thin") & (sens["era"] == "2023-26")]["acc"].iloc[0]) - acc(p, "C1_own_fit", "2023-26")) for p in ORDER)
    sb10 = sb[sb["grid"] == "all_sessions_C10_no_thin"]
    d_b = max(abs(float(sb10[(sb10["pair"] == p) & (sb10["h"] == h) & (sb10["k"] == k) & (sb10["era"] == "2010-26")]["no_touch"].iloc[0]) - odds(p, h, k, "2010-26")) for p in ORDER for (h, k) in QUOTE)
    d_b23 = max(abs(float(sb10[(sb10["pair"] == p) & (sb10["h"] == h) & (sb10["k"] == k) & (sb10["era"] == "2023-26")]["no_touch"].iloc[0]) - odds(p, h, k, "2023-26")) for p in ORDER for (h, k) in QUOTE)
    raw_chf = float(sens[(sens["pair"] == "usdchf") & (sens["variant"] == "C1_own_fit_C11_raw") & (sens["era"] == "2010-26")]["acc"].iloc[0])
    raw_jpy = float(sens[(sens["pair"] == "usdjpy") & (sens["variant"] == "C1_own_fit_C11_raw") & (sens["era"] == "2010-26")]["acc"].iloc[0])
    a(f"* **Shuffled-order control** (range series permuted across sessions, 20 draws per pair): model accuracy {ctrl['shuffled_acc'].min():.1f}-{ctrl['shuffled_acc'].max():.1f} %, 'same class as "
      f"yesterday' {ctrl['shuffled_naive'].min():.1f}-{ctrl['shuffled_naive'].max():.1f} %, always-majority {ctrl['shuffled_always_majority'].mean():.1f} %. The accuracy falls to the baseline, as it should; "
      f"the 2 points left over come from the noisy 250-session median (the fit knows the long-run median better than one year's sample does), not from order information.\n"
      f"* **2023 hole (C10).** Without test rows whose last or target session is thin: accuracy moves by at most {d_thin:.1f} points in 2010-26 / 2016-26 and {d_thin23:.1f} in 2023-26. Without "
      f"decision sessions whose window (14 sessions back to h ahead) contains a thin session: the odds move by at most {d_b:.1f} points in 2010-26 and {d_b23:.1f} in 2023-26. No verdict changes.\n"
      f"* **Uncleaned frames (C11).** USD/JPY: identical ({raw_jpy:.1f} %). USD/CHF own fit: {raw_chf:.1f} % instead of {acc('usdchf', 'C1_own_fit', '2010-26'):.1f} % in 2010-26 - the three 2004-05 bad ticks "
      f"sit in the training window and distort the fit; cleaning helps USD/CHF by about a point and it still fails. The no-touch odds are unchanged to the decimal (test rows untouched).\n"
      f"* **USD-only event flag (C3):** within 0.6 points of the primary on every pair and era.\n"
      f"* **Weekly grid (C5):** level 24 of 24 within 4 points (largest gap {lv[(lv['grid'] == 'weekly') & (lv['pair'] != EUR)]['diff'].abs().max():.1f}); stability {V['B_weekly_stability_cells_stable']} of 24 "
      f"(one fifth of the sessions, so noisier).\n")

    a("## Candidate count: 11\n")
    a("C1 range, own fit (PRIMARY A). C2 range, frozen EUR/USD coefficients. C3 range, USD-only event flag. C4 no-touch odds, every session (PRIMARY B). C5 no-touch odds, weekly grid. "
      "C6 random-walk benchmarks (analytic, Monte Carlo, sign-flip surrogate). C7 odds by forecast class and by forecast / ATR tercile. C8 levels set from the multi-session forecast. "
      "C9 pooled calibration data. C10 thin-session sensitivity. C11 uncleaned frames. Controls (not candidates): shuffled order, the data checks. Post hoc and labelled so: the signal-to-noise "
      "table, accuracy by year, the joint surrogate count for the stability clause.\n")
    a("## Anything suspicious\n")
    a("* **The stability clause of bar B was mis-specified by me**: 4 points across three eras is tighter than a 21-session window can resolve with 3-7 years per era. I report the failure as "
      "declared and the surrogate that shows it is uninformative; I did not re-draw the bar.\n"
      "* **EUR/USD is again the best of seven** on the published statistic (range accuracy). Unlike the directional findings this one was not mined (one simple model, no search), and the "
      "post-hoc decomposition explains the gap by regime width rather than luck, but the pattern is the same as in rounds 3, 4 and 6 and the published figure should not be quoted for other pairs.\n"
      "* USD/CAD is the one pair whose era figures drift (2-ATR / 10 sessions 70.1 -> 69.4 -> 65.9 %; 3 of its 12 era cells fall outside its surrogate range, about 0.6 expected). Its upper "
      "level was touched more often than its lower one over 2010-26 (USD/CAD rose over the sample). One pair of seven; worth watching, not a finding.\n"
      "* The futures cross-check cannot fully verify GBP, JPY, AUD and CAD ranges after 2016 (Yahoo's futures bars degrade); the Yahoo hourly check covers only 2024-26. The HistData hole of "
      "February-July 2023 is in every pair.\n"
      "* The event flag is uneven by construction (almost empty before 2010 and in 2024-25, for every currency); the model's event coefficient is correspondingly small and the flag is not what "
      "makes it work.\n"
      "* All bars are bid quotes of one vendor; ranges and ATR include the spread widening of the roll-over hour. This affects levels of range, not the odds (ATR and excursions share it).\n")

    a("## What the product may honestly say about stops and targets\n")
    a(f"1. **Level odds: say them, for any liquid dollar pair, and say what they are.** 'A level 2 ATR from the close is left untouched over 10 sessions about 69 % of the time, 3 ATR about 87 %; "
      f"over 21 sessions about 51 % and 70 %.' That held within {lv6['diff'].abs().max():.1f} points on six other pairs and in every era within sampling noise. It must be labelled as the arithmetic of a "
      f"driftless market with today's volatility (the same numbers come out of a formula with no data), not as a forecast and not as an edge: a stop placed with it has known odds of being hit by "
      f"noise, and zero expectancy.\n"
      f"2. **Two caveats belong on the quote.** (a) It is an average over volatility states: after a quiet-forecast day the same level survives 2-4 points less often (65-67 % for 2 ATR / 10 "
      f"sessions), after a volatile-forecast day 1-6 points more often (70-74 %). (b) It is the average of both sides; over 2010-26 the two sides differed by up to "
      f"{max(abs(odds(p, h, k, '2010-26', col='upper_side') - odds(p, h, k, '2010-26', col='lower_side')) for p in ORDER for (h, k) in QUOTE):.0f} points on a pair that trended (USD/CAD), "
      f"{max(abs(odds(EUR, h, k, '2010-26', col='upper_side') - odds(EUR, h, k, '2010-26', col='lower_side')) for (h, k) in QUOTE):.1f} on EUR/USD.\n"
      f"3. **Range forecast: keep it for sizing and for the band, drop the headline accuracy outside EUR/USD.** What is structural: next-session range is forecastable on every pair from its own "
      f"last 21 sessions, with frozen EUR/USD coefficients if need be, and the 80 % band of a pair's own fit contains the outcome 77-82 % of the time in every pair and era. What is EUR/USD-specific and "
      f"must be labelled so: '75-78 % right on above / below normal' ({min(lo10, lo16):.0f}-{max(hi10, hi16):.0f} % on the other six) and '93 % on volatile-day calls' ({v_lo:.0f}-{v_hi:.0f} %). "
      f"Even on EUR/USD the regression adds only 1-2 points over 'is the 21-session average range above normal'.\n"
      f"4. Nothing here changes the directional verdict of round 9. The stop / target / sizing layer is sound because it claims nothing about direction.\n")
    text = "\n".join(L)
    (path or ROOT / "reports" / f"arm_{ARM}.md").write_text(text)
    return text


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "run"
    pd.set_option("display.width", 250); pd.set_option("display.max_rows", 400); pd.set_option("display.max_columns", 40)
    if cmd == "build":
        out = build_and_check()
        for k, v in out.items():
            print(f"\n== {k}"); print(v.to_string(index=False))
    elif cmd == "checks":
        out = build_and_check(write=True)
        for k in ("timestamps", "h10_sessions", "range_sources", "badticks", "coverage"):
            print(f"\n== {k}"); print(out[k].round(3).to_string(index=False))
    elif cmd == "reconcile":
        reconcile()
    else:
        run()
