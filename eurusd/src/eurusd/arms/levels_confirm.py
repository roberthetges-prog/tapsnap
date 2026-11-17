"""Arm EA `levels_confirm` (round 13): confirm or reject round 11's two leads on the LOWER / UPPER levels, frozen, on
markets this project has never scored.

DECLARED BEFORE ANY OUTCOME ON THE NEW MARKETS WAS COMPUTED (2026-11-17). At the time of writing I had read the Round
9 / 11 / 13 addenda, `reports/arm_sharper_levels.md`, `sharper_levels.py`, `bots.py`, `build_data.py`, the download and
session code of arms P (`ofi_replication`) and BA (`reliable_parts`), and had looked only at INPUTS: which files exist,
their shapes and columns, and HistData's index pages for the six symbols (which years are offered). No bar of any new
market had been downloaded and no level of any method had been computed on any of them.

CANDIDATES: 2 (counted), against the baseline. Nothing else is scored as a candidate.
  baseline  `bots`       the median of the 100 bots' levels, `sharper_levels` candidate C0, exactly as coded there.
  K1        `har_d`      round 11's chosen candidate C3 exactly as coded in `sharper_levels.py` (`reg_fit` / `reg_pred`
                         with REG_FEATS["har_d"]: OLS of the log range of the next h sessions on the logs of the 5-, 21-,
                         63- and 252-session volatility of daily close-to-close returns; one pooled 80 % constant).
  K2        `har_rv_ev`  round 11's C6 exactly as coded there (the same regression on hourly realised volatility over
                         1 / 5 / 21 / 63 / 252 sessions plus the count of scheduled events inside the window).
                         Every market below has intraday bars (HistData 1-minute), so NO daily-data substitute is used.
                         Had a market lacked intraday bars, the declared substitute would have been `har_gk`'s regressors
                         (Garman-Klass daily variance, 1 / 5 / 21 / 63 / 252 sessions) plus the same event counts; it is
                         not needed and is not computed.
  Event kinds in K2's regression (the only free setting, fixed here by round 11's own rule "the events of the currencies
  in the pair"): euro crosses = FOMC, ECB, payrolls (the EUR/USD setting); dollar markets (USD/SEK, USD/NOK, gold in
  dollars) = FOMC, payrolls (the setting round 11 used on the six dollar pairs). The event-WEEK reporting split is
  `sharper_levels`' `evweek` column as coded (any of those events, or US CPI, inside the 5-session window).
All three are produced by `sharper_levels.evaluate(X, names=("bots", "har_d", "har_rv_ev"))` on
`sharper_levels.generic_frame(...)`: same frame, same yearly expanding walk-forward (a model for test year Y uses only
outcomes known before Y-01-01; MIN_ROWS = 500), same scoring code. No function of `sharper_levels.py` is changed or copied.

MARKETS (six, chosen before any outcome; none has ever been scored for levels in this project):
  EUR/GBP, EUR/JPY, EUR/CHF (HistData offers 2002+), USD/SEK, USD/NOK (2008+), gold XAU/USD (2009+).
  Source: HistData 1-minute bid bars, fetched the way `build_data.py` / arm P fetched theirs (arm P's `_fetch_period`,
  imported; if the site refuses, the market is dropped, not worked around). The Yahoo daily files are NOT used for
  levels (known stamp change in 2010, doubtful highs / lows); Yahoo gold futures serve only as an independent range check.
  Sessions exactly as the EUR/USD store builds them: 1-minute -> 5-minute -> hourly -> `daily_ohlc(h1, 22)`, sessions with
  at least 10 hourly bars, no Saturday start, frame from 2003 (or the market's first bar). Hourly realised variance by
  `sharper_levels.hourly_rv`.
  Scored years: test years 2010-2026 as far as each market's history allows. USD/SEK, USD/NOK and gold start in 2008 / 2009,
  so with 252 sessions of look-back and 500 training rows their first scored sessions fall in 2011-2012; a market is
  scored from the first session at which the baseline, K1 and K2 all have a level (the common-sample rule of round 11).
  RESERVES, used in this order only if a primary market fails the data-quality rule: EUR/AUD, EUR/CAD (euro-cross
  settings). If fewer than six markets survive after the reserves, the study is reported as incomplete.

DATA-QUALITY RULE (applied mechanically before any level is scored; a market that fails is DROPPED, not repaired):
  Q0  bad-tick rule, the relative form of arm BA's 400-pip rule (400 pips of a major is about 3 % of its price): a
      5-minute bar whose high (low) lies more than 3 % beyond max (min) of its own open and close, the previous bar's
      close and the next bar's open has that wick removed. Applied identically to every market; flagged bars are listed.
      (This is cleaning of single ticks, declared in advance and the same for every method; it is not a repair of a
      failed market.)
  Q1  completeness: every yearly file from the market's first year on the site to 2025 downloads and parses, and every
      calendar year from the first full year to 2025 has at least 245 sessions.
  Q2  independent source. FX markets: the ECB reference rate of the day (14:15 CET; EUR/GBP, EUR/JPY, EUR/CHF directly,
      USD/SEK and USD/NOK as the ratio of two reference rates) must lie inside the [low, high] of the session that
      contains it, widened by 0.05 % of the price (bid bars against a mid fix), on at least 97 % of days in 2010-2026.
      This checks the stamp convention and the highs / lows at once. Gold (no fix in the project): the session's log
      range against the Yahoo gold-futures daily range of the same trade date, 2011-2026: correlation at least 0.85 and
      median ratio between 0.80 and 1.25. (The same Yahoo comparison is reported for the three euro crosses, descriptive.)
  Q3  thin sessions (fewer than 20 hourly bars) outside the known HistData hole of February-July 2023: at most 5 % of the
      sessions of 2010-2026.
  Q4  the 20 largest session ranges (after Q0) are listed. A session has the BAD-TICK SIGNATURE if its range is at least
      5 times the trailing 21-session median range, |close - open| is at most 20 % of the range, and the widest single
      5-minute bar is at least 60 % of the range. A market fails if more than 2 of its 20 largest ranges have it.

SCORING (as round 11, per market and pooled; eras 2010-26 = primary, 2018-26 = reported alone as well):
  holding rate of each level; PROPER SCORE = mean of the pinball losses at the 20 % / 80 % quantiles of the period's lowest
  low / highest high, basis points; spread (max - min) of the holding rate across the three terciles of `g_rv21`, averaged
  over the six cells (3 horizons x 2 levels) of a market; at 5 sessions, holding rate in event weeks against other weeks.
  Horizons 5 / 21 / 63 sessions.
  POOLED SCORE TEST (round 11's `pooled_test`, here primary): per market the per-session loss difference to the baseline
  is divided by the baseline's mean loss in the era; the market series are averaged by date and the mean gets a moving
  block-bootstrap 95 % interval (blocks of max(21, 2h) sessions, 2,000 draws, seed 11). Blocks are therefore contiguous
  runs of sessions within every market, the markets are pooled, and markets that move together on a date are resampled
  together (three of the six share the euro, two are Scandinavian). Reported next to it, descriptive: the same statistic
  with each market's blocks resampled independently.

PASS BAR. Pooled over the surviving markets, 2010-2026, a candidate is CONFIRMED only if ALL hold:
  (1) its pooled proper score is better than the baseline's (pooled relative difference below zero) at 5, 21 AND 63
      sessions, and the interval above excludes zero (on the better side) at two of the three horizons at least;
  (2) its tercile spread of the holding rate (six-cell average, 2010-26) is smaller than the baseline's in at least five
      of the six markets (with N surviving markets: in at least ceil(5N/6));
  (3) each of its six pooled holding rates (lower and upper level, three horizons; all scored sessions of all markets
      pooled) lies between 77 % and 83 %.
  K2 only, in addition: (4) at 5 sessions the EVENT-WEEK SHORTFALL (holding rate in other weeks minus holding rate in
      event weeks, average of the lower and the upper level, sessions of all markets pooled) is at least halved against
      the baseline's. If the baseline shows no shortfall on the new markets (shortfall <= 0) there is nothing to repair
      and clause (4) FAILS (the lead is then not confirmed, which is the honest reading).
Anything else in the report (each market separately, 2018-26 alone, widths) is descriptive.

SANITY (controls): (a) with these imports, the EUR/USD frame of round 11 must reproduce the published 2018-26 scores of
`sharper_levels_scores.csv` for the baseline, K1 and K2; (b) no future data: on EUR/GBP, 20 random sessions of 2010-26,
the session bars and the hourly realised variances are cut off at that session, the frame rebuilt and the three methods'
levels recomputed; they must equal the full-run levels.

IF A CANDIDATE IS CONFIRMED the function to wire into `bots.py` is stated in the report: K1 = `sharper_levels.levels(X,
h, asof, name="har_d")`; K2 = `sharper_levels.levels(X, h, asof, name="har_rv_ev")` on `sharper_levels.build(D, h1)`.

Entry points: `run()` (download if needed, build, quality rule, scoring, report); `python src/eurusd/arms/levels_confirm.py run`.
"""
from __future__ import annotations

import math
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import features as F  # noqa: E402
from eurusd.arms import sharper_levels as SL  # noqa: E402  (read only)

ARM = "levels_confirm"
PROC = ROOT / "data" / "processed"
CROSS = PROC / "cross"
MACRO = ROOT / "data" / "macro"
RES = ROOT / "experiments" / "results" / "arms"
REPORT = ROOT / "reports" / f"arm_{ARM}.md"

EURO = ("fomc", "ecb", "nfp")
USD = ("fomc", "nfp")
MARKETS = {
    "eurgbp": {"label": "EUR/GBP", "kinds": EURO, "ref": ("ecb", "GBP", None)},
    "eurjpy": {"label": "EUR/JPY", "kinds": EURO, "ref": ("ecb", "JPY", None)},
    "eurchf": {"label": "EUR/CHF", "kinds": EURO, "ref": ("ecb", "CHF", None)},
    "usdsek": {"label": "USD/SEK", "kinds": USD, "ref": ("ecb", "SEK", "USD")},
    "usdnok": {"label": "USD/NOK", "kinds": USD, "ref": ("ecb", "NOK", "USD")},
    "xauusd": {"label": "Gold", "kinds": USD, "ref": ("yahoo", "gold", None)},
}
RESERVES = {
    "euraud": {"label": "EUR/AUD", "kinds": EURO, "ref": ("ecb", "AUD", None)},
    "eurcad": {"label": "EUR/CAD", "kinds": EURO, "ref": ("ecb", "CAD", None)},
}
YAHOO_DESC = {"eurgbp": "eurgbp", "eurjpy": "eurjpy", "eurchf": "eurchf"}
NAMES = ("bots", "har_d", "har_rv_ev")
KNAME = {"bots": "baseline", "har_d": "K1", "har_rv_ev": "K2"}
HORIZONS = SL.HORIZONS
ERAS = (("2010-26", 2010, 2026), ("2018-26", 2018, 2026))
PRIMARY = "2010-26"
WICK_REL = 0.03
THIN_H = 20


# ---- written AFTER the run of 2026-11-17 (interpretation only; the verdict lines of the report are computed) ----
ANSWER = ("**Yes, for K2 only:** by the bar declared in advance, the hourly-volatility regression with the event adjustment (`har_rv_ev`) is confirmed on six markets never scored here, "
          "so the lead may replace the bots' width arithmetic with it, while the daily-returns version K1 is not confirmed and should not be wired in. "
          "Expect a small gain, not a different product (proper score 2-4 % better, levels 3-5 % narrower on these markets at the same 80 % reliability, holding rates about half as dependent on "
          "calm / volatile markets, the event-week weakness of one-week levels removed), and note that the statistical margin at 21 and 63 sessions is thin (below), so the bots' levels should keep "
          "running beside it in the paper forward test.")
DATA_NOTES = ("**Gold was DROPPED by the declared rule and never scored**: its only independent check (session range against Yahoo gold futures, 2011-26) gave a correlation of 0.77 against the "
              "declared minimum of 0.85 (median ratio 1.05, inside the band). The same Yahoo comparison gives 0.70-0.84 on the three euro crosses whose ECB check is perfect, so the failure very "
              "probably says more about Yahoo's daily highs / lows than about the gold bars; the rule was fixed in advance and I did not re-draw it. The first declared reserve, EUR/AUD, took its "
              "place (ECB fix inside the session range on 99.98 % of days). Consequence: four of the six scored markets are euro crosses and none is a commodity. "
              "One blemish that the rule tolerates (one signature in the top 20; more than two fail a market): EUR/GBP has a bad print on 2004-08-31 (session range 60 %), which the 3 % wick rule "
              "did not catch because the bad price is the bar's own close / next open. A second EUR/GBP session of 2004 (03-25, range 11 % with an 11 % open-to-close move) also looks like bad data without carrying the signature. "
              "Both lie in the training years only (scoring starts 2010) and feed all three methods' fits; they were left as they are. "
              "The wick rule changed five 5-minute bars in all (EUR/JPY three in 2004, EUR/AUD one in 2004, USD/SEK 2020-11-12), all single prints 7-50 % away from the market. "
              "USD/SEK and USD/NOK begin in September 2008 on HistData, so their first scored session is 2012-01-01.")
NOTES = ("## 7. How firm is this? (descriptive, computed once after the verdict, outside `run()`; files `levels_confirm_seed_sensitivity.csv`, `levels_confirm_leave_one_out.csv`)\n\n"
         "* **What is solid for K2:** the point estimate is better than the bots in 18 of 18 market-horizon cells in 2010-26; the 5-session gain (-2.1 %) excludes zero under every seed, with doubled "
         "blocks and with any one market left out; the evenness clause holds in 6 of 6 markets (spread roughly halved); the event-week shortfall falls from +2.5 to +0.4 points and stays below "
         "half with any one market left out (K1, which has no event term, leaves it at +2.0: the repair comes from the event term).\n"
         "* **What is thin:** clause (1) needs a second interval. At 21 sessions the upper bound is -0.07 % (below zero for 20 of 20 bootstrap seeds, but +0.02 % with doubled block length); at 63 "
         "sessions -0.11 % (below zero for 10 of 20 seeds). Leaving out EUR/GBP, EUR/JPY or EUR/AUD leaves only the 5-session interval excluding zero, i.e. clause (1) would fail; in particular the "
         "pass depends on the reserve market EUR/AUD having replaced gold. In 2018-26 alone K2 passes (1), (2), (4) and misses (3) by one cell (63-session lower level held 83.4 %).\n"
         "* **K1:** better at all three horizons and more even in 6 of 6 markets, with all six holding rates inside 77-83 %, but only the 63-session interval excludes zero (and that for 4 of 20 seeds). "
         "The evenness lead is real; the score gain of the daily-returns version is not established. K2 gives the same evenness plus the hourly volatility and event information.\n"
         "* **Side asymmetry:** the regression candidates use ONE constant for both sides; on USD/SEK and USD/NOK, which rose over the sample, K2's 63-session lower level held 86 % and its upper "
         "76 % (bots 78-79 % each side). Pooled it averages out; on a single trending market it does not. The bots' separate constants per side do not have this.\n"
         "* **EUR/USD itself** did not pass in round 11 (C6 in 2018-26: -1.8 %* / -0.8 % / -1.2 %, levels 3-6 % wider there). The confirmation here is on other markets; it says the method "
         "generalises, not that EUR/USD's own history shows the gain beyond 5 sessions.\n"
         "* **Wiring note for the lead:** `sharper_levels.levels(X, h, asof, name=\"har_rv_ev\")` on `sharper_levels.build(D, h1)` needs the hourly bars (the live product has them) and the "
         "scheduled-event files in `data/macro` to extend past the forecast window (FOMC is listed to December 2027; ECB and BLS only to December 2026, so they need refreshing before a "
         "63-session level set in autumn 2026 can count its events correctly).\n")


# ====================================================================================================== download
def download(mkt: str, verbose: bool = True) -> pd.DataFrame:
    """Every yearly file (and the months of the running year) HistData offers for the market, via arm P's fetcher."""
    import re
    import requests
    from concurrent.futures import ThreadPoolExecutor
    from eurusd.arms import ofi_replication as P
    P.raw_dir(mkt).mkdir(parents=True, exist_ok=True)
    r = requests.get(P._index_url(mkt), headers={"User-Agent": P.UA}, timeout=60)
    r.raise_for_status()
    found = set(re.findall(rf"1-minute-bar-quotes/{mkt}/(\d{{4}}(?:/\d{{1,2}})?)\"", r.text, flags=re.I))
    key = lambda q: (int(q.partition("/")[0]), int(q.partition("/")[2] or 0))  # noqa: E731
    periods = sorted(found, key=key)
    rows = []
    with ThreadPoolExecutor(max_workers=2) as ex:
        for res in ex.map(lambda q: P._fetch_period(mkt, q), periods):
            rows.append({"market": mkt, "period": res[1], "bytes": res[2], "status": res[3]})
    out = pd.DataFrame(rows)
    if verbose:
        print(f"  download {mkt}: {len(out)} periods, {int((out.status == 'downloaded').sum())} new, "
              f"{int(out.status.str.startswith('FAILED').sum())} failed, {out.bytes.sum() / 1e6:.0f} MB", flush=True)
    return out


# ====================================================================================================== build
def clean_m5(m5: pd.DataFrame, thr: float = WICK_REL) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Q0: the relative wick rule. Returns the cleaned bars and the flagged ones."""
    pc, no = m5["close"].shift(1), m5["open"].shift(-1)
    ref = pd.concat([m5["open"], m5["close"], pc, no], axis=1)
    ref_hi, ref_lo = ref.max(axis=1), ref.min(axis=1)
    uw, lw = m5["high"] / ref_hi - 1, 1 - m5["low"] / ref_lo
    bu, bl = (uw > thr).values, (lw > thr).values
    fl = m5.loc[bu | bl].copy()
    fl["upper_wick_pct"], fl["lower_wick_pct"] = 100 * uw[bu | bl], 100 * lw[bu | bl]
    out = m5.copy()
    out.loc[bu, "high"] = ref_hi[bu]
    out.loc[bl, "low"] = ref_lo[bl]
    return out, fl


def daily_path(mkt: str) -> Path:
    return PROC / f"{ARM}_daily_{mkt}.parquet"


def rv_path(mkt: str) -> Path:
    return PROC / f"{ARM}_rv_{mkt}.parquet"


def build_market(mkt: str, verbose: bool = True) -> dict:
    """1-minute zips -> cleaned session bars and hourly realised variances (both cached, small) + quality diagnostics."""
    from eurusd.arms import ofi_replication as P
    m1, info = P.load_m1(mkt)
    agg = {"open": "first", "high": "max", "low": "min", "close": "last"}
    m5 = m1.resample("5min", label="left", closed="left").agg(agg).dropna(subset=["open"]).astype("float64")
    del m1
    bad_ohlc = int(((m5["high"] < m5[["open", "close", "low"]].max(axis=1) - 1e-9) | (m5["low"] > m5[["open", "close", "high"]].min(axis=1) + 1e-9)).sum())
    clean, flagged = clean_m5(m5)

    def sessions(x):
        h1 = x.resample("1h", label="left", closed="left").agg(agg).dropna(subset=["open"]).loc["2003":]
        d = F.daily_ohlc(h1, 22)
        return d[(d["n"] >= 10) & (d.index.dayofweek != 5)].copy(), h1

    d_raw, _ = sessions(m5)
    d, h1 = sessions(clean)
    assert d.index.equals(d_raw.index)
    d["close_time"] = d.index + pd.Timedelta(days=1)
    d["high_raw"], d["low_raw"] = d_raw["high"].values, d_raw["low"].values
    rvd = SL.hourly_rv(h1[["close"]])
    d.to_parquet(daily_path(mkt))
    rvd.to_parquet(rv_path(mkt))
    # Q4 diagnostics on the 20 largest ranges (after Q0)
    rng = np.log(d["high"] / d["low"])
    med21 = rng.rolling(21).median().shift(1)
    rows = []
    for t in rng.nlargest(20).index:
        s = clean.loc[t: t + pd.Timedelta(hours=24) - pd.Timedelta(seconds=1)]
        br = np.log(s["high"] / s["low"])
        r = d.loc[t]
        body = abs(math.log(r["close"] / r["open"]))
        x_med = float(rng[t] / med21.get(t, np.nan))
        sig = bool(x_med >= 5 and body <= 0.2 * rng[t] and br.max() >= 0.6 * rng[t])
        rows.append({"market": mkt, "session_start_utc": t.strftime("%Y-%m-%d"), "range_pct": round(100 * float(rng[t]), 2), "x_trailing_21_median": round(x_med, 1),
                     "abs_close_minus_open_pct": round(100 * body, 2), "hourly_bars": int(r["n"]), "widest_m5_bar_pct": round(100 * float(br.max()), 2),
                     "widest_m5_bar_utc": br.idxmax().strftime("%H:%M"), "changed_by_wick_rule": bool(r["high"] != r["high_raw"] or r["low"] != r["low_raw"]),
                     "bad_tick_signature": sig})
    fl = flagged.reset_index().rename(columns={"index": "bar_start_utc", "time": "bar_start_utc"})
    fl.insert(0, "market", mkt)
    if verbose:
        print(f"  build {mkt}: {info['files']} files, {len(m5):,} 5-minute bars {str(m5.index[0])[:10]}..{str(m5.index[-1])[:10]}, {len(d)} sessions, "
              f"{len(flagged)} bars changed by the wick rule", flush=True)
    return {"info": {**info, "m5_rows": len(m5), "inconsistent_ohlc_bars": bad_ohlc, "wick_rule_bars": len(flagged)}, "top": pd.DataFrame(rows), "flagged": fl}


def load_market(mkt: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    return pd.read_parquet(daily_path(mkt)), pd.read_parquet(rv_path(mkt))


def _yahoo_range_check(d: pd.DataFrame, name: str) -> dict:
    y = pd.read_parquet(CROSS / f"{name}_D1.parquet")
    y = y[(y["high"] > y["low"]) & (y["low"] > 0)]
    yr = pd.Series(np.log(y["high"] / y["low"]).values, index=pd.DatetimeIndex(y.index.tz_convert("UTC").date))
    yr = yr[~yr.index.duplicated()]
    mine = pd.Series(np.log(d["high"] / d["low"]).values, index=pd.DatetimeIndex((d.index + pd.Timedelta(days=1)).date))
    j = pd.concat([mine.rename("m"), yr.rename("y")], axis=1).dropna().loc["2011":]
    j = j[(j.m > 0) & (j.y > 0)]
    return {"yahoo_days": len(j), "yahoo_logrange_corr": float(np.corrcoef(np.log(j.m), np.log(j.y))[0, 1]), "yahoo_range_median_ratio": float((j.m / j.y).median())}


def quality(mkt: str, cfg: dict, dl: pd.DataFrame, B: dict) -> dict:
    """The declared rule Q1-Q4 for one market (inputs only; no level is computed here)."""
    d, _ = load_market(mkt)
    out = {"market": mkt, "label": cfg["label"], **{k: B["info"][k] for k in ("files", "first", "last", "bad_price_rows", "inconsistent_ohlc_bars", "wick_rule_bars")},
           "sessions": len(d)}
    # Q1
    failed = int(dl.status.str.startswith("FAILED").sum()) if len(dl) else 0
    yrs = sorted({int(p.partition("/")[0]) for p in dl.period}) if len(dl) else []
    per_year = d.groupby(d.index.year).size()
    first_full = int(d.index[0].year) + (0 if d.index[0].dayofyear <= 10 else 1)
    py = per_year.loc[first_full:2025]
    missing = [y for y in range(yrs[0], 2026) if y not in yrs] if yrs else ["no listing"]
    out.update({"files_failed": failed, "years_missing_on_site": str(missing), "first_full_year": first_full, "min_sessions_in_a_year": int(py.min()),
                "min_sessions_year": int(py.idxmin()), "sessions_2026": int(per_year.get(2026, 0))})
    q1 = failed == 0 and not missing and py.min() >= 245
    # Q2
    kind, a, b = cfg["ref"]
    if kind == "ecb":
        E = pd.read_parquet(CROSS / "leg_ecb_ref_rates.parquet")
        ref = (E[a] if b is None else E[a] / E[b]).dropna()
        ref.index = pd.DatetimeIndex(ref.index).tz_localize("UTC") - pd.Timedelta(hours=2)      # the session that starts at 22:00 UTC the day before
        j = pd.concat([d[["low", "high"]], ref.rename("ref")], axis=1).dropna().loc["2010":]
        inside = ((j.ref >= j.low * (1 - 5e-4)) & (j.ref <= j.high * (1 + 5e-4)))
        out.update({"ref_source": f"ECB reference rate {a}" + (f"/{b}" if b else ""), "ref_days": len(j), "ref_inside_pct": 100 * float(inside.mean()),
                    "ref_median_abs_gap_to_range_pct": float(100 * (np.maximum(j.low / j.ref - 1, 0) + np.maximum(j.ref / j.high - 1, 0))[~inside].median()) if (~inside).any() else 0.0})
        q2 = inside.mean() >= 0.97 and len(j) >= 2000
        if mkt in YAHOO_DESC:
            out.update(_yahoo_range_check(d, YAHOO_DESC[mkt]))
    else:
        yc = _yahoo_range_check(d, a)
        out.update({"ref_source": "Yahoo gold futures daily range", **yc})
        q2 = yc["yahoo_logrange_corr"] >= 0.85 and 0.80 <= yc["yahoo_range_median_ratio"] <= 1.25 and yc["yahoo_days"] >= 2000
    # Q3
    s = d.loc["2010":]
    hole = (s.index >= pd.Timestamp("2023-02-01", tz=s.index.tz)) & (s.index < pd.Timestamp("2023-08-01", tz=s.index.tz))
    thin = (s["n"] < THIN_H).values
    out.update({"thin_sessions_in_2023_hole": int((thin & hole).sum()), "thin_sessions_elsewhere_pct": 100 * float((thin & ~hole).sum() / len(s))})
    q3 = out["thin_sessions_elsewhere_pct"] <= 5.0
    # Q4
    nsig = int(B["top"]["bad_tick_signature"].sum())
    out["top20_with_bad_tick_signature"] = nsig
    q4 = nsig <= 2
    out.update({"Q1_complete": bool(q1), "Q2_independent_source": bool(q2), "Q3_thin": bool(q3), "Q4_top20": bool(q4), "PASS": bool(q1 and q2 and q3 and q4)})
    return out


# ====================================================================================================== scoring
def frame(mkt: str, kinds, upto: pd.Timestamp | None = None) -> pd.DataFrame:
    d, rvd = load_market(mkt)
    if upto is not None:
        d, rvd = d.loc[d.index <= upto], rvd.loc[rvd.index <= upto]
    return SL.generic_frame(d, rvd, kinds=kinds)


def per_session(X: pd.DataFrame, E: dict) -> dict:
    """Per horizon: one row per scored session with the losses, hits, event-week flag and volatility state."""
    out = {}
    for h in HORIZONS:
        W, L = E["walk"][h], E["loss"][h]
        dn, up = X[f"dn{h}"].values, X[f"up{h}"].values
        P_ = pd.DataFrame({"ok": L["ok"].values, "year": X.index.year.values, "evweek": X["evweek"].values, "g_rv21": X["g_rv21"].values}, index=X.index)
        for nm in NAMES:
            l, u = W[f"{nm}|l"].values, W[f"{nm}|u"].values
            P_[f"{nm}|loss"] = L[nm].values
            P_[f"{nm}|lh"], P_[f"{nm}|uh"] = (dn >= l).astype(float), (up <= u).astype(float)
            P_[f"{nm}|w"] = 100 * (np.exp(u) - np.exp(l))
        out[h] = P_[P_["ok"]].drop(columns="ok")
    return out


def boot_draws(x: np.ndarray, block: int, reps: int = 2000, seed: int = 11) -> np.ndarray:
    n = len(x)
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(n / block))
    starts = rng.integers(0, n, size=(reps, nb))
    idx = ((starts[:, :, None] + np.arange(block)[None, None, :]) % n).reshape(reps, -1)[:, :n]
    return x[idx].mean(axis=1)


def pooled_tables(PS: dict, markets: list[str]) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Pooled score test, pooled holding rates, pooled event-week split."""
    T, Hd, Ev = [], [], []
    for era, a, b in ERAS:
        for h in HORIZONS:
            sub = {m: PS[m][h][(PS[m][h].year >= a) & (PS[m][h].year <= b)] for m in markets}
            allr = pd.concat(sub.values())
            for nm in NAMES:
                n = len(allr)
                ni = n / h
                lh, uh = float(allr[f"{nm}|lh"].mean()), float(allr[f"{nm}|uh"].mean())
                Hd.append({"candidate": nm, "h": h, "era": era, "sessions": n, "n_indep_summed": round(ni, 1), "lower_held": lh, "upper_held": uh,
                           "avg_width_pct": float(allr[f"{nm}|w"].mean()), "score_bp": float(allr[f"{nm}|loss"].mean()),
                           "mean_score_ratio_over_markets": float(np.mean([sub[m][f"{nm}|loss"].mean() / sub[m]["bots|loss"].mean() for m in markets]))})
                if h == 5:
                    for k, mm in (("event week", allr.evweek > 0), ("other week", allr.evweek == 0)):
                        Ev.append({"candidate": nm, "era": era, "class": k, "sessions": int(mm.sum()), "n_indep_summed": round(mm.sum() / h, 1),
                                   "lower_held": float(allr.loc[mm, f"{nm}|lh"].mean()), "upper_held": float(allr.loc[mm, f"{nm}|uh"].mean()),
                                   "score_bp": float(allr.loc[mm, f"{nm}|loss"].mean())})
            for nm in NAMES[1:]:
                parts, ind = [], []
                for i, m in enumerate(markets):
                    s = sub[m]
                    rel = ((s[f"{nm}|loss"] - s["bots|loss"]) / s["bots|loss"].mean()).rename(m)
                    ind.append(boot_draws(rel.values, max(21, 2 * h), seed=100 + i))
                    rel.index = rel.index.normalize()
                    parts.append(rel)
                d = pd.concat(parts, axis=1).groupby(level=0).mean().mean(axis=1).dropna().values
                lo, hi = SL.block_boot(d, max(21, 2 * h))
                iv = np.mean(ind, axis=0)
                T.append({"candidate": nm, "h": h, "era": era, "dates": len(d), "pooled_rel_diff_pct": 100 * float(d.mean()), "lo_pct": 100 * lo, "hi_pct": 100 * hi,
                          "better": bool(d.mean() < 0), "excludes_zero_better_side": bool(hi < 0),
                          "indep_blocks_mean_pct": 100 * float(np.mean([p.mean() for p in parts])), "indep_blocks_lo_pct": 100 * float(np.quantile(iv, 0.025)),
                          "indep_blocks_hi_pct": 100 * float(np.quantile(iv, 0.975))})
    return pd.DataFrame(T), pd.DataFrame(Hd), pd.DataFrame(Ev)


def shortfall(Ev: pd.DataFrame, nm: str, era: str) -> float:
    e = Ev[(Ev.candidate == nm) & (Ev.era == era)].set_index("class")
    return float(((e.loc["other week", "lower_held"] - e.loc["event week", "lower_held"]) + (e.loc["other week", "upper_held"] - e.loc["event week", "upper_held"])) / 2)


def verdicts(T: pd.DataFrame, Hd: pd.DataFrame, Ev: pd.DataFrame, SP: pd.DataFrame, markets: list[str], era: str = PRIMARY) -> pd.DataFrame:
    rows = []
    need = int(math.ceil(5 * len(markets) / 6))
    sp = SP[SP.era == era].pivot(index="market", columns="candidate", values="mean_spread")
    for nm in NAMES[1:]:
        t = T[(T.candidate == nm) & (T.era == era)].set_index("h")
        c1a = bool(t["better"].all())
        c1b = int(t["excludes_zero_better_side"].sum())
        nsp = int((sp[nm] < sp["bots"]).sum())
        hd = Hd[(Hd.candidate == nm) & (Hd.era == era)]
        cells = list(hd["lower_held"]) + list(hd["upper_held"])
        c3 = all(0.77 <= x <= 0.83 for x in cells)
        r = {"candidate": KNAME[nm], "name": nm, "era": era, "markets": len(markets),
             "c1_better_at_all_three": c1a, "c1_intervals_excluding_zero": c1b, "c1_pass": bool(c1a and c1b >= 2),
             "c1_detail": "; ".join(f"h={h}: {t.loc[h, 'pooled_rel_diff_pct']:+.2f} % [{t.loc[h, 'lo_pct']:+.2f}, {t.loc[h, 'hi_pct']:+.2f}]" for h in HORIZONS),
             "c2_markets_with_smaller_spread": nsp, "c2_needed": need, "c2_pass": bool(nsp >= need),
             "c3_cells_inside_77_83": int(sum(0.77 <= x <= 0.83 for x in cells)), "c3_pass": bool(c3),
             "c3_detail": "; ".join(f"h={int(x.h)}: {100 * x.lower_held:.1f} / {100 * x.upper_held:.1f}" for x in hd.itertuples())}
        ok = r["c1_pass"] and r["c2_pass"] and r["c3_pass"]
        if nm == "har_rv_ev":
            s0, s2 = shortfall(Ev, "bots", era), shortfall(Ev, nm, era)
            c4 = bool(s0 > 0 and s2 <= 0.5 * s0)
            r.update({"c4_shortfall_baseline_points": 100 * s0, "c4_shortfall_candidate_points": 100 * s2, "c4_shortfall_K1_points": 100 * shortfall(Ev, "har_d", era), "c4_pass": c4})
            ok = ok and c4
        r["CONFIRMED"] = bool(ok)
        rows.append(r)
    return pd.DataFrame(rows)


def eurusd_sanity(verbose: bool = True) -> pd.DataFrame:
    """(a) the published round-11 EUR/USD scores from these imports."""
    E = SL.evaluate(SL.build(), names=NAMES, boot=False, verbose=False)
    s = E["scores"]
    pub = pd.read_csv(RES / "sharper_levels_scores.csv")
    cols = ["sessions", "lower_held", "upper_held", "avg_width_pct", "score_bp"]
    j = s[s.candidate.isin(NAMES)][["candidate", "h", "era"] + cols].merge(pub[["candidate", "h", "era"] + cols], on=["candidate", "h", "era"], suffixes=("", "_published"))
    for c in cols:
        j[f"d_{c}"] = j[c] - j[f"{c}_published"]
    j["max_abs_diff"] = j[[f"d_{c}" for c in cols]].abs().max(axis=1)
    if verbose:
        k = j[(j.era == "2018-26") & (j.h == 5)].set_index("candidate")
        print(f"  EUR/USD sanity: {len(j)} published cells re-computed, largest absolute difference {j['max_abs_diff'].max():.2e}; 2018-26, 5 sessions: bots "
              f"{k.loc['bots', 'score_bp']:.2f} bp (published {k.loc['bots', 'score_bp_published']:.2f}), K1 {k.loc['har_d', 'score_bp']:.2f} ({k.loc['har_d', 'score_bp_published']:.2f}), "
              f"K2 {k.loc['har_rv_ev', 'score_bp']:.2f} ({k.loc['har_rv_ev', 'score_bp_published']:.2f})", flush=True)
    return j


def truncation_check(mkt: str, kinds, WK: dict, X: pd.DataFrame, n: int = 20, seed: int = 3, verbose: bool = True) -> pd.DataFrame:
    """(b) inputs cut off at the session; levels must equal the full run."""
    rng = np.random.default_rng(seed)
    ok = (X.index.year >= 2010) & np.all([np.isfinite(WK[5][f"{nm}|l"].values) for nm in NAMES], axis=0)
    cand = X.index[ok]
    rows = []
    for i in sorted(rng.choice(len(cand), size=n, replace=False)):
        t = cand[i]
        Xt = frame(mkt, kinds, upto=t)
        assert Xt.index[-1] == t
        for h in HORIZONS:
            Wt = SL.walk(Xt, h, names=NAMES, years=[t.year], matched=False)
            for nm in NAMES:
                for sfx in ("l", "u"):
                    full, cut = float(WK[h].loc[t, f"{nm}|{sfx}"]), float(Wt[f"{nm}|{sfx}"].iloc[-1])
                    rows.append({"market": mkt, "session": str(t)[:10], "h": h, "candidate": nm, "side": sfx, "full_run": full, "truncated": cut, "abs_diff": abs(full - cut)})
    T = pd.DataFrame(rows)
    if verbose:
        print(f"  truncation ({mkt}): {n} sessions, {len(T)} levels, largest |difference| in log distance {T['abs_diff'].max():.2e} "
              f"(not finite: {int((~np.isfinite(T['abs_diff'])).sum())})", flush=True)
    return T


# ====================================================================================================== run
def prepare(todo: dict, verbose: bool = True) -> tuple[list, list, list, list]:
    Q, TOP, FL, DL = [], [], [], []
    for mkt, cfg in todo.items():
        try:
            dl = download(mkt, verbose)
        except Exception as e:  # noqa: BLE001  (site refused: the market is dropped, not worked around)
            Q.append({"market": mkt, "label": cfg["label"], "PASS": False, "error": f"download refused: {type(e).__name__}: {e}"})
            continue
        DL.append(dl)
        B = build_market(mkt, verbose)
        Q.append(quality(mkt, cfg, dl, B))
        TOP.append(B["top"])
        FL.append(B["flagged"])
        time.sleep(0.1)
    return Q, TOP, FL, DL


def run(write: bool = True, verbose: bool = True) -> dict:
    warnings.filterwarnings("ignore")
    RES.mkdir(parents=True, exist_ok=True)
    print("STEP 0: EUR/USD sanity (round 11's published numbers from these imports)", flush=True)
    SAN = eurusd_sanity(verbose)
    print("STEP 1: data (download, sessions, the declared quality rule; no level computed yet)", flush=True)
    Q, TOP, FL, DL = prepare(MARKETS, verbose)
    cfgs = dict(MARKETS)
    nfail = sum(not q["PASS"] for q in Q)
    for mkt, cfg in list(RESERVES.items())[:nfail]:
        print(f"  a primary market failed the rule: reserve {mkt} is brought in", flush=True)
        q2, t2, f2, d2 = prepare({mkt: cfg}, verbose)
        Q, TOP, FL, DL = Q + q2, TOP + t2, FL + f2, DL + d2
        cfgs[mkt] = cfg
    Q = pd.DataFrame(Q)
    TOP, FL, DL = pd.concat(TOP, ignore_index=True), pd.concat(FL, ignore_index=True), pd.concat(DL, ignore_index=True)
    markets = [m for m in Q.market if bool(Q.set_index("market").loc[m, "PASS"])]
    if verbose:
        qc = [c for c in ("market", "sessions", "first", "min_sessions_in_a_year", "ref_inside_pct", "yahoo_logrange_corr", "yahoo_range_median_ratio",
                          "thin_sessions_elsewhere_pct", "top20_with_bad_tick_signature", "wick_rule_bars", "Q1_complete", "Q2_independent_source", "Q3_thin", "Q4_top20", "PASS") if c in Q]
        print(Q[qc].round(3).to_string(index=False), flush=True)
        print(f"  markets scored: {markets}", flush=True)
    if write:
        Q.to_csv(RES / f"{ARM}_quality.csv", index=False)
        TOP.to_csv(RES / f"{ARM}_top_ranges.csv", index=False)
        FL.to_csv(RES / f"{ARM}_wick_rule_bars.csv", index=False)
        DL.to_csv(RES / f"{ARM}_download.csv", index=False)
    print("STEP 2: scoring (frozen: baseline, K1, K2)", flush=True)
    S, BT, SP, SPC, ST, YR, PS = [], [], [], [], [], [], {}
    TR = None
    for mkt in markets:
        X = frame(mkt, cfgs[mkt]["kinds"])
        E = SL.evaluate(X, names=NAMES, verbose=False)
        for k, lst in (("scores", S), ("boot", BT), ("spread", SP), ("spread_cells", SPC), ("states", ST), ("years", YR)):
            t = E[k][E[k].candidate.isin(NAMES)].copy()
            if "era" in t:
                t = t[t.era.isin([e[0] for e in ERAS])]
            t.insert(0, "market", mkt)
            lst.append(t)
        PS[mkt] = per_session(X, E)
        if TR is None:
            TR = truncation_check(mkt, cfgs[mkt]["kinds"], E["walk"], X, verbose=verbose)
        if verbose:
            s = E["scores"]
            p5 = PS[mkt][5]
            msg = "; ".join(f"{KNAME[nm]} " + " / ".join(f"{s[(s.candidate == nm) & (s.era == PRIMARY) & (s.h == h)]['score_ratio'].iloc[0]:.3f}" for h in HORIZONS) for nm in NAMES[1:])
            print(f"  {mkt}: {len(X)} sessions, scored from {str(p5.index[0])[:10]} ({len(p5)} at h=5); score ratio to the bots 5 / 21 / 63, 2010-26: {msg}", flush=True)
    S, BT, SP, SPC, ST, YR = (pd.concat(x, ignore_index=True) for x in (S, BT, SP, SPC, ST, YR))
    T, Hd, Ev = pooled_tables(PS, markets)
    V = pd.concat([verdicts(T, Hd, Ev, SP, markets, era) for era, _, _ in ERAS], ignore_index=True)
    out = {"quality": Q, "top": TOP, "flagged": FL, "scores": S, "boot": BT, "spread": SP, "spread_cells": SPC, "states": ST, "years": YR, "pooled": T, "pooled_held": Hd,
           "events": Ev, "verdict": V, "sanity": SAN, "truncation": TR, "markets": markets, "cfgs": cfgs,
           "starts": {m: {h: str(PS[m][h].index[0])[:10] for h in HORIZONS} for m in markets}}
    if write:
        for k in ("scores", "boot", "spread", "spread_cells", "states", "years", "pooled", "pooled_held", "events", "verdict", "sanity", "truncation"):
            out[k].to_csv(RES / f"{ARM}_{k}.csv", index=False)
        REPORT.write_text(write_report(out))
    if verbose:
        print(V.T.to_string(), flush=True)
    return out


# ====================================================================================================== report
def _md(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False)


def write_report(R: dict) -> str:
    S, SP, T, Hd, Ev, V, Q, markets, cfgs = R["scores"], R["spread"], R["pooled"], R["pooled_held"], R["events"], R["verdict"], R["quality"], R["markets"], R["cfgs"]
    lab = {m: cfgs[m]["label"] for m in cfgs}
    v = V[V.era == PRIMARY].set_index("candidate")
    v18 = V[V.era == "2018-26"].set_index("candidate")
    yn = lambda b: "passes" if b else "FAILS"  # noqa: E731
    L = [f"# Arm EA: `{ARM}` - are round 11's two leads on the levels confirmed on markets never scored here?", "",
         f"Round 13. Code `src/eurusd/arms/{ARM}.py` (`run()`, one process). Results `experiments/results/arms/{ARM}_*.csv`. The two candidates, the market list, "
         "the data-quality rule, the scoring and the pass bar were written into the module docstring before any bar of the new markets was downloaded. "
         "**Candidates: 2**, against the bots' median level. Nothing was re-run with changed settings.", "",
         "## Verdict (read this first)", ""]
    for k, nm, desc in (("K1", "har_d", "regression levels from daily returns (round 11's C3)"), ("K2", "har_rv_ev", "hourly-volatility regression with the event adjustment (round 11's C6)")):
        r = v.loc[k]
        L.append(f"**{k}, {desc}: {'CONFIRMED' if r.CONFIRMED else 'NOT CONFIRMED'}** on {int(r.markets)} new markets pooled, 2010-26.")
        L.append("")
        L.append(f"* (1) better proper score at all three horizons, interval excluding zero at two at least: **{yn(r.c1_pass)}** ({r.c1_detail}; "
                 f"{int(r.c1_intervals_excluding_zero)} of 3 intervals exclude zero).")
        L.append(f"* (2) holding rate more even across volatility terciles in at least {int(r.c2_needed)} of {int(r.markets)} markets: **{yn(r.c2_pass)}** "
                 f"({int(r.c2_markets_with_smaller_spread)} of {int(r.markets)}).")
        L.append(f"* (3) every pooled level holds 77-83 %: **{yn(r.c3_pass)}** ({int(r.c3_cells_inside_77_83)} of 6 cells inside; lower / upper held: {r.c3_detail}).")
        if k == "K2":
            L.append(f"* (4) event-week shortfall of the one-week holding rate at least halved: **{yn(r.c4_pass)}** (baseline {r.c4_shortfall_baseline_points:+.1f} points, "
                     f"K2 {r.c4_shortfall_candidate_points:+.1f}; K1 for comparison {r.c4_shortfall_K1_points:+.1f}; positive = levels hold less often in event weeks).")
        r8 = v18.loc[k]
        L.append(f"* 2018-26 alone (descriptive): (1) {yn(r8.c1_pass)} ({r8.c1_detail}); (2) {int(r8.c2_markets_with_smaller_spread)} of {int(r8.markets)}; "
                 f"(3) {int(r8.c3_cells_inside_77_83)} of 6 cells ({r8.c3_detail})" + (f"; (4) baseline {r8.c4_shortfall_baseline_points:+.1f}, K2 {r8.c4_shortfall_candidate_points:+.1f} points." if k == "K2" else "."))
        L.append("")
    any_ok = bool(v.CONFIRMED.any())
    L += ["## Should the product's levels change?", "", "@@ANSWER@@", ""]
    if any_ok:
        w = [k for k in v.index if v.loc[k, "CONFIRMED"]]
        fn = {"K1": '`sharper_levels.levels(X, h, asof, name="har_d")` on `sharper_levels.build(D, h1)`', "K2": '`sharper_levels.levels(X, h, asof, name="har_rv_ev")` on `sharper_levels.build(D, h1)`'}
        L += ["Function to wire into `bots.py` (by the lead, not by this arm): " + "; ".join(f"{k}: {fn[k]}" for k in w) + ".", ""]
    # plain table
    L += ["## 1. The plain table (2010-26, walk-forward, out of sample, same sessions for the three methods)", "",
          "`held` = share of sessions on which the period's lowest low stayed above the lower level / highest high below the upper level (design: 80 %). Score = pinball loss at the "
          "20 % / 80 % quantiles, basis points, lower is better; in brackets the relative difference to the baseline, `*` = this market's own paired block-bootstrap 95 % interval excludes zero. "
          "Tercile spread = max minus min of the holding rate across the three volatility terciles, points, average of the lower and the upper level at that horizon.", ""]
    for era, _, _ in ERAS:
        rows = []
        for m in markets + ["POOLED"]:
            for h in HORIZONS:
                row = {"market": lab.get(m, "ALL POOLED"), "h": h}
                for nm in NAMES:
                    if m == "POOLED":
                        s = Hd[(Hd.candidate == nm) & (Hd.h == h) & (Hd.era == era)].iloc[0]
                        sc = f"{s.score_bp:.1f}"
                        if nm != "bots":
                            t = T[(T.candidate == nm) & (T.h == h) & (T.era == era)].iloc[0]
                            sc += f" ({t.pooled_rel_diff_pct:+.1f} %{'*' if (t.hi_pct < 0 or t.lo_pct > 0) else ''})"
                        c = R["spread_cells"]
                        c = c[(c.candidate == nm) & (c.h == h) & (c.era == era)]
                        spv = 100 * float((c.spread_lower.mean() + c.spread_upper.mean()) / 2)
                        spt = f"{spv:.1f} (mean)"
                    else:
                        s = S[(S.market == m) & (S.candidate == nm) & (S.h == h) & (S.era == era)].iloc[0]
                        sc = f"{s.score_bp:.1f}"
                        if nm != "bots":
                            b = R["boot"]
                            b = b[(b.market == m) & (b.candidate == nm) & (b.h == h) & (b.era == era)].iloc[0]
                            sc += f" ({100 * (s.score_ratio - 1):+.1f} %{'*' if b.excludes_zero else ''})"
                        c = R["spread_cells"]
                        c = c[(c.market == m) & (c.candidate == nm) & (c.h == h) & (c.era == era)].iloc[0]
                        spt = f"{100 * (c.spread_lower + c.spread_upper) / 2:.1f}"
                    k = KNAME[nm]
                    row[f"{k}: lower / upper held %"] = f"{100 * s.lower_held:.1f} / {100 * s.upper_held:.1f}"
                    row[f"{k}: score bp"] = sc
                    row[f"{k}: tercile spread"] = spt
                rows.append(row)
        L += [f"**{era}**" + (" (the declared primary era)" if era == PRIMARY else " (descriptive)"), "", _md(pd.DataFrame(rows)), ""]
    L += ["Pooled row: holding rates and score over all scored sessions of all markets; the bracket is the declared pooled test (per-market relative loss difference, averaged by date, "
          "block bootstrap over dates). First scored session per market (5 sessions): " + ", ".join(f"{lab[m]} {R['starts'][m][5]}" for m in markets) + ".", ""]
    # pooled test
    t = T.copy()
    t.insert(0, "method", t.candidate.map(KNAME))
    t = t.drop(columns=["candidate", "better", "excludes_zero_better_side"]).round(2)
    L += ["## 2. The pooled score test", "",
          "`pooled_rel_diff_pct` = mean over dates of the market-average relative loss difference to the bots (negative = better), with the declared interval (`lo` / `hi`: date blocks, "
          "cross-market dependence kept). `indep_blocks_*` = the same with each market resampled independently (descriptive; narrower because it ignores that the markets move together).", "",
          _md(t), ""]
    # spread per market
    sp = SP.pivot_table(index=["era", "market"], columns="candidate", values="mean_spread").reset_index()
    sp = sp.rename(columns={nm: f"{KNAME[nm]} spread (points)" for nm in NAMES})
    for c in sp.columns[2:]:
        sp[c] = (100 * sp[c]).round(1)
    sp["market"] = sp.market.map(lab)
    L += ["## 3. Evenness: spread of the holding rate across volatility terciles (six-cell average per market)", "", _md(sp), ""]
    # events
    e = Ev.copy()
    e.insert(0, "method", e.candidate.map(KNAME))
    for c in ("lower_held", "upper_held"):
        e[c] = (100 * e[c]).round(1)
    e["score_bp"] = e.score_bp.round(2)
    L += ["## 4. One-week levels in event weeks against other weeks (pooled)", "",
          "Event week = a scheduled FOMC statement, ECB decision (euro crosses), US payrolls or US CPI inside the 5-session window, as `sharper_levels` codes it.", "",
          _md(e.drop(columns=["candidate"])), ""]
    em = R["states"]
    em = em[(em.state == "scheduled events") & (em.era == PRIMARY)].pivot_table(index=["market", "candidate"], columns="class", values=["lower_held", "upper_held"])
    em = (100 * em).round(1)
    em.columns = [f"{a.replace('_', ' ')} %, {b}" for a, b in em.columns]
    em = em.reset_index()
    em["market"], em["candidate"] = em.market.map(lab), em.candidate.map(KNAME)
    L += ["Per market, 2010-26:", "", _md(em), ""]
    # data
    qc = [c for c in ("label", "first", "last", "sessions", "files", "files_failed", "min_sessions_in_a_year", "min_sessions_year", "ref_source", "ref_days", "ref_inside_pct", "yahoo_days",
                      "yahoo_logrange_corr", "yahoo_range_median_ratio", "thin_sessions_in_2023_hole", "thin_sessions_elsewhere_pct", "bad_price_rows", "inconsistent_ohlc_bars",
                      "wick_rule_bars", "top20_with_bad_tick_signature", "Q1_complete", "Q2_independent_source", "Q3_thin", "Q4_top20", "PASS", "error") if c in Q]
    qq = Q[qc].copy()
    for c in ("first", "last"):
        if c in qq:
            qq[c] = qq[c].astype(str).str[:10]
    L += ["## 5. Data: the markets and the declared quality rule", "",
          "HistData 1-minute bid bars (stamps America/New_York -> UTC as arm P verified), aggregated to 5 minutes, hourly bars and 22:00-UTC sessions exactly as the EUR/USD store. "
          "The rule (module docstring) was applied before any level was computed.", "", _md(qq.round(3).T.reset_index().rename(columns={"index": "check"})), "",
          "@@DATA_NOTES@@", "",
          f"The 20 largest session ranges per market are in `{ARM}_top_ranges.csv`, the bars changed by the wick rule in `{ARM}_wick_rule_bars.csv`. The five largest per market:", ""]
    top = R["top"]
    t5 = top.groupby("market", sort=False).head(5).copy()
    t5["market"] = t5.market.map(lab)
    L += [_md(t5), ""]
    # sanity
    sn = R["sanity"]
    k = sn[(sn.era == "2018-26")][["candidate", "h", "score_bp", "score_bp_published", "lower_held", "lower_held_published", "upper_held", "upper_held_published"]].round(4)
    tr = R["truncation"]
    L += ["## 6. Sanity", "",
          f"* **EUR/USD, round 11's numbers from these imports:** {len(sn)} published cells (three methods x three horizons x five eras; sessions, both holding rates, width, score) re-computed; "
          f"largest absolute difference {sn['max_abs_diff'].max():.2e}. 2018-26:", "", _md(k), "",
          f"* **No future data:** {tr.session.nunique()} random sessions of {lab[tr.market.iloc[0]]}, inputs (session bars and hourly realised variances) cut off at the session, frame rebuilt, "
          f"{len(tr)} levels of the three methods recomputed: largest difference in log distance {tr['abs_diff'].max():.2e}.", "",
          "@@NOTES@@", ""]
    return "\n".join(L).replace("@@ANSWER@@", ANSWER).replace("@@DATA_NOTES@@", DATA_NOTES).replace("@@NOTES@@", NOTES)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        run()
