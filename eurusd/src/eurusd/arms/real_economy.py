"""Arm R ("real_economy"): slow real-economy information as an EXTRA VOTE for multi-week EUR/USD direction (round 5).

EVERYTHING IN THIS DOCSTRING (signals, signs, lags, the evaluation and the selection rule) WAS WRITTEN BEFORE ANY
ACCURACY NUMBER WAS COMPUTED. Only data availability (which host answers, where a series starts and ends) was known.

Idea: the agreement rule of arm N (positioning sign, 20-day 2y-spread trend sign and house macro-score sign all equal)
is the state of the art for 1-3 month direction. Three families of slow real-economy information that none of the
earlier arms used as a vote: (A) energy terms of trade, (B) relative growth leading indicators, (C) US real yields and
inflation expectations as CHANGES. Each candidate is one fixed, signed signal (no fitting, no thresholds): a positive
value is a vote for long EUR/USD, a negative value for short, zero / missing is no vote.

DATA, SPANS AND PUBLICATION LAGS (the lag is applied on top of featstore._align_lagged's one calendar day)
  daily market series (stamp d is used from the session whose closing date is >= d + 1 calendar day):
    Brent spot, USD/bbl        data/macro/datahub_brent_daily.csv (EIA spot, 1987-05..2026-11; repo file, as arm O)
    Dutch TTF gas front month  Yahoo TTF=F, EUR/MWh, 2017-10-23.. (SHORT: no value before 2018, no 2010-15 record)
    Henry Hub front month      Yahoo NG=F, USD/MMBtu, 2000-08..
    Henry Hub spot             FRED DHHNGSP, daily, 1997-01.. (only as a monthly average, see below)
    US 10y TIPS yield          FRED DFII10, daily, 2003-01..   (H.15, published the next business day)
    US 5y5y forward breakeven  FRED T5YIFR, daily, 2003-01..
    EUR/USD for conversions    the store's NY close of the PREVIOUS session (close.shift(1))
  monthly series (reference month m is used from month-end(m) + LAG days, then + 1 day):
    EU natural gas price       FRED PNGASEUUSDM (IMF primary commodity prices, USD/MMBtu, monthly average), 1992-01..;
                               IMF publishes in the first half of m+1, FRED later: LAG 45.
    euro-area goods trade      ECB TRD.M.I10.Y.X/M.TTT.J10.4.VAL (extra-euro-area exports and imports, seasonally
                               adjusted, EUR, changing-composition euro area), 2002-01..; Eurostat releases about
                               day 15-18 of m+2: LAG 50.
    OECD composite leading     FRED USALOLITONOSTSAM, EA19LOLITONOSTSAM, DEU/FRA/ITALOLITONOSTSAM (amplitude adjusted).
    indicators                 FRED froze these at 2024-01 (EA19 at 2022-11) and the OECD API is refused by the proxy,
                               so the CLI signal is UNDEFINED from mid-2024. LAG 45 (about six weeks).
    euro-area sentiment        ECB RTD.M.S0.S.Y_ESIND.F (European Commission Economic Sentiment Indicator), 1980-01..
                               Released on the next-to-last working day of m (early m+1 in a few years): LAG 10.
    US consumer sentiment      FRED UMCSENT (University of Michigan, final), monthly from 1978. Final figure is released
                               on the last or next-to-last Friday of m: LAG 10.
  A monthly signal is switched OFF (no vote) when its newest usable observation became available more than 75 days
  ago (normal spacing is ~30 days); a daily signal when its newest stamp is more than 10 calendar days old.
  All monthly series are the CURRENT VINTAGE (revised data), not real-time vintages; the OECD CLI is known to be
  revised materially, the trade balance moderately, the sentiment indices hardly. This is a look-ahead I cannot
  remove with the reachable sources; it is flagged in the report.
  Euro-area real yields: not built. A nominal AAA yield minus TRAILING HICP is not an expectation, its 1-3 month change
  is the nominal change plus base effects, and arm O already found the trailing-inflation real differential wrongly
  signed. Family C is therefore US-only.
  Not reachable (proxy 403): sdmx.oecd.org, ec.europa.eu (Eurostat / DG ECFIN), api.db.nomics.world. US ISM is not free.

THE 12 CANDIDATE SIGNALS (positive = long EUR/USD) AND THEIR PRIORS
  A. energy terms of trade (the euro area imports its energy)
   1 brent_eur_d63    -(63-session log change of Brent in EUR)        dearer oil worsens the euro-area terms of trade.
   2 brent_eur_d126   -(126-session log change of Brent in EUR)       same. Sign adopted from arm O's table
   3 brent_usd_d126   -(126-session log change of Brent in USD)       (`oil_d126`, 55-58 %), NOT re-fitted here; this
                                                                      one is the exact arm-O predictor.
   4 gasratio_d3m     -(3-month change of log(EU gas / Henry Hub)), monthly averages, common currency (USD)
                                                                      Europe paying more for gas than the US = euro-area
                                                                      terms of trade and competitiveness worse.
   5 ttf_hh_d63       -(63-session change of log(TTF front in USD/MMBtu / NG front)), daily; 2018+ only (short).
   6 ea_tb_mom        +(3-month mean of the SA extra-EA goods balance / (X+M) minus the 3-month mean before it)
                                                                      an improving trade balance is euro demand.
  B. growth leading indicators, euro area minus US (relative growth momentum favours the currency)
   7 cli_d6m_diff     +(6-month change of the euro-area CLI minus 6-month change of the US CLI); EA19 series to
                       2022-11, the DEU/FRA/ITA mean for the 6-month changes after it; undefined from mid-2024.
   8 sent_lvl_diff    +(z(ESI) - z(UMCSENT)); z = expanding mean / sd of the own history up to that month (>= 120 months).
   9 sent_d3m_diff    +(3-month change of ESI - 3-month change of UMCSENT), each divided by its expanding sd.
  C. US real yields and inflation expectations, as changes
  10 tips_d21         -(21-session change of the US 10y TIPS yield)   higher US real yields attract capital to the dollar.
  11 tips_d63         -(63-session change of the US 10y TIPS yield)   same.
  12 bei_d63          +(63-session change of the US 5y5y forward breakeven)  at a given nominal yield, higher expected
                       US inflation is a lower US real yield and an erosion of the dollar. WEAK prior: the opposite
                       story (reflation => Fed tightening => dollar up) is as respectable.
  Caveat known in advance: signals 1, 2 and 5 contain the lagged EUR/USD return by construction (EUR conversion), so
  they carry a piece of EUR/USD momentum (1, 2: with a positive sign; 5: with a negative sign). Signal 3 is the
  currency-free control.

EVALUATION (HOWTO_ARMS.md round 5; helpers and conventions of eurusd.arms.selective, which this module re-uses)
  0 Reconciliation: the agreement rule is rebuilt with selective.house_score_wf and must reproduce arm N's
    56 / 59 / 61 / 72 % non-overlapping (n = 291 / 156 / 89 / 61), 2010-26.
  1 Standalone: direction = sign(signal); accuracy at 21 / 42 / 63 sessions on weekly decisions and on the greedy
    non-overlapping stream (plain Wilson interval), 2010-26 / 2016-26 / 2023-26.
  2 Extra vote. (a) AND rule: the agreement rule speaks AND sign(signal) equals its direction - against the agreement
    rule alone, with decisions per year; (b) OUTSIDE: direction = sign(signal) on the sessions where the three old
    signals do NOT agree (coverage extension); (c) paired differences on the weekly grid with a circular block
    bootstrap (block 2h/5 weeks, 2000 draws): acc(AND) - acc(agreement rule on the sessions where the signal exists),
    and acc(agreement calls the signal confirms) - acc(agreement calls it contradicts).
  3 Daily stream: weekly tranches of the final AND rule held 21 sessions (selective.book_time_exit, 1.2 pips per unit
    turnover); protocol table; meta.combine(["weak_signals","regime_trend","real_economy"], "EW") against the two-way
    combination; daily P&L correlations.
  4 Timing placebo: the signal is made 63 and 126 sessions staler (shift) and the AND rule re-evaluated; also the
    standalone accuracy when stale.
  SELECTION RULE (given by the lead): final = the candidate whose AND rule has the highest LOWER Wilson bound of the
    2010-2015 non-overlapping 21-session accuracy among candidates with at least 6 non-overlapping 21-session decisions a
    year in 2010-2015. If no candidate has 6 a year there is NO final rule; the stream written to disk is then the
    highest lower bound among all candidates, flagged as failing the decisions requirement.
  SUCCESS BAR (round 5): the AND rule beats the agreement rule by >= 3 accuracy points at 21 AND 42 sessions on
    non-overlapping decisions in BOTH 2010-26 and 2016-26 with at least 6 decisions a year, is not worse in 2023-26,
    and the placebo loses at least half of the gain. Note fixed before results: the agreement rule itself makes 9.3
    (21 sessions) and 5.3 (42 sessions) non-overlapping decisions a year, so no AND rule can have 6 a year at 42
    sessions; the count is judged on the 21-session stream and the 42-session count is printed next to every number.
  Leak checks: (1) labels permuted (300 draws) -> the rules must sit at chance; (2) the signal shifted FORWARD in time
    (-21 sessions, look-ahead: must not be needed to get the result; +1 / +5 / +21 staler: a slow signal must barely
    move); a truncation test (raw data cut at four dates, the row of that date must be unchanged); (3) correlation of
    every signal with past EUR/USD returns, with the three old votes and with the forward label.
Variant count for deflation: 12 candidate signals = 12 AND rules. Nothing else is selected from.
"""
from __future__ import annotations

import json
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.arms import selective as SL  # noqa: E402
from eurusd.featstore import _align_lagged  # noqa: E402
from eurusd.wf import report  # noqa: E402

MACRO = ROOT / "data" / "macro"
CROSS = ROOT / "data" / "processed" / "cross"
RAW = ROOT / "data" / "raw" / "real_economy"
RES = ROOT / "experiments" / "results" / "arms"
ARM = "real_economy"
N_ARMS = 12
HORIZONS = (21, 42, 63)
SEL_H = 21
MIN_DEC_PER_YEAR = 6.0
STALE_M, STALE_D = 75, 10
PLACEBO_SHIFTS = (63, 126)
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

FRED_IDS = ("DFII10", "T5YIFR", "DHHNGSP", "PNGASEUUSDM", "UMCSENT", "USALOLITONOSTSAM", "EA19LOLITONOSTSAM",
            "DEULOLITONOSTSAM", "FRALOLITONOSTSAM", "ITALOLITONOSTSAM")
YAHOO = {"ttf": "TTF=F", "ng": "NG=F"}
ECB = {"esi": "RTD/M.S0.S.Y_ESIND.F", "trade_x": "TRD/M.I10.Y.X.TTT.J10.4.VAL", "trade_m": "TRD/M.I10.Y.M.TTT.J10.4.VAL"}
LAG = {"gas": 45, "trade": 50, "cli": 45, "esi": 10, "umich": 10}

SIGNALS = (  # name, family, prior
    ("brent_eur_d63", "A", "- dearer oil (EUR terms, 3 months) worsens euro-area terms of trade"),
    ("brent_eur_d126", "A", "- same, 6 months"),
    ("brent_usd_d126", "A", "- same in USD: arm O's `oil_d126`, sign adopted from its table"),
    ("gasratio_d3m", "A", "- Europe/US gas price ratio up (monthly, 3 months) = euro-area terms of trade worse"),
    ("ttf_hh_d63", "A", "- same, daily TTF / Henry Hub futures, 2018+ only"),
    ("ea_tb_mom", "A", "+ improving euro-area goods trade balance"),
    ("cli_d6m_diff", "B", "+ euro-area minus US 6-month change of the OECD leading indicator (ends mid-2024)"),
    ("sent_lvl_diff", "B", "+ euro-area ESI minus US Michigan sentiment, expanding z-scores"),
    ("sent_d3m_diff", "B", "+ 3-month change of the same differential"),
    ("tips_d21", "C", "- US 10y real yield up over 1 month = dollar up"),
    ("tips_d63", "C", "- same over 3 months"),
    ("bei_d63", "C", "+ US 5y5y breakeven up over 3 months = dollar down (weak prior)"),
)
NAMES = [s[0] for s in SIGNALS]


# ================================================================ cached fetch
def _curl(url: str, dest: Path, ua: str | None = None, tries: int = 5) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    err = ""
    for k in range(tries):
        cmd = ["curl", "--http1.1", "-sS", "-m", "120", "-o", str(dest), "-w", "%{http_code}"]
        if ua:
            cmd += ["-A", ua]
        r = subprocess.run(cmd + [url], capture_output=True, text=True)
        if r.stdout.strip() == "200" and dest.exists() and dest.stat().st_size > 50:
            return
        err = f"http {r.stdout.strip()} {r.stderr.strip()[:200]}"
        time.sleep(3 * (k + 1))
    raise RuntimeError(f"fetch failed: {url}: {err}")


def fetch_all(refresh: bool = False, verbose: bool = True) -> pd.DataFrame:
    """Downloads every new raw series once (raw copy in data/raw/real_economy/) and writes the cleaned files
    data/macro/real_economy_*.csv and data/processed/cross/real_economy_*_D1.parquet. Returns the catalogue."""
    rows = []
    for sid in FRED_IDS:
        out = MACRO / f"{ARM}_fred_{sid}.csv"
        if refresh or not out.exists():
            raw = RAW / f"fred_{sid}.csv"
            _curl(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}", raw)
            d = pd.read_csv(raw)
            d.columns = ["date", "value"]
            d["value"] = pd.to_numeric(d["value"], errors="coerce")
            d.dropna().to_csv(out, index=False)
            time.sleep(0.5)
        d = pd.read_csv(out)
        rows.append({"file": str(out.relative_to(ROOT)), "source": f"FRED {sid}", "rows": len(d), "first": d["date"].iloc[0], "last": d["date"].iloc[-1]})
    for nm, tk in YAHOO.items():
        out = CROSS / f"{ARM}_{nm}_D1.parquet"
        if refresh or not out.exists():
            raw = RAW / f"yahoo_{nm}.json"
            err = None
            for host in ("query2", "query1"):
                try:
                    _curl(f"https://{host}.finance.yahoo.com/v8/finance/chart/{tk}?period1=946684800&period2=1900000000&interval=1d", raw, ua=UA)
                    err = None
                    break
                except RuntimeError as e:  # noqa: PERF203
                    err = e
            if err is not None:
                raise err
            j = json.loads(raw.read_text())["chart"]["result"][0]
            # bar stamps are midnight in the exchange time zone (04:00 / 05:00 UTC): convert with the zone, not with the
            # current gmtoffset, or every summer bar would be stamped one day early (a one-day look-ahead)
            ts = pd.to_datetime(np.array(j["timestamp"], dtype="int64"), unit="s", utc=True).tz_convert(j["meta"]["exchangeTimezoneName"])
            d = pd.DataFrame({"close": j["indicators"]["quote"][0]["close"]}, index=ts.normalize().tz_localize(None))
            d = d[~d.index.duplicated(keep="last")].dropna()
            d.index.name = "date"
            d.to_parquet(out)
            time.sleep(1.0)
        d = pd.read_parquet(out)
        rows.append({"file": str(out.relative_to(ROOT)), "source": f"Yahoo {tk}", "rows": len(d), "first": str(d.index[0].date()), "last": str(d.index[-1].date())})
    for nm, key in ECB.items():
        out = MACRO / f"{ARM}_ecb_{nm}.csv"
        if refresh or not out.exists():
            raw = RAW / f"ecb_{nm}.csv"
            _curl(f"https://data-api.ecb.europa.eu/service/data/{key}?format=csvdata&detail=dataonly", raw)
            d = pd.read_csv(raw)[["TIME_PERIOD", "OBS_VALUE"]]
            d.columns = ["month", "value"]
            d.dropna().to_csv(out, index=False)
        d = pd.read_csv(out)
        rows.append({"file": str(out.relative_to(ROOT)), "source": f"ECB {key}", "rows": len(d), "first": d["month"].iloc[0], "last": d["month"].iloc[-1]})
    b = pd.read_csv(MACRO / "datahub_brent_daily.csv")
    rows.append({"file": "data/macro/datahub_brent_daily.csv", "source": "datahub oil-prices (EIA Brent spot), repo file", "rows": len(b), "first": b["date"].iloc[0], "last": b["date"].iloc[-1]})
    cat = pd.DataFrame(rows)
    if verbose:
        print(cat.to_string(index=False), flush=True)
    return cat


# ================================================================ raw series
def _fred(sid: str) -> pd.Series:
    d = pd.read_csv(MACRO / f"{ARM}_fred_{sid}.csv", parse_dates=["date"])
    return d.set_index("date")["value"].astype(float).sort_index()


def _monthly(s: pd.Series) -> pd.Series:
    s = s.copy()
    s.index = pd.PeriodIndex(s.index, freq="M")
    return s[~s.index.duplicated(keep="last")].sort_index()


def load_raw() -> dict:
    R = {}
    b = pd.read_csv(MACRO / "datahub_brent_daily.csv", parse_dates=["date"]).set_index("date")["price"].astype(float)
    R["brent"] = b[~b.index.duplicated()].sort_index()
    for nm in YAHOO:
        R[nm] = pd.read_parquet(CROSS / f"{ARM}_{nm}_D1.parquet")["close"].astype(float).sort_index()
    R["tips"] = _fred("DFII10")
    R["bei"] = _fred("T5YIFR")
    R["hh_spot"] = _fred("DHHNGSP")
    R["eu_gas"] = _monthly(_fred("PNGASEUUSDM"))
    um = _fred("UMCSENT")
    R["umich"] = _monthly(um[um.index >= "1978-01-01"])
    for k, sid in (("cli_us", "USALOLITONOSTSAM"), ("cli_ea", "EA19LOLITONOSTSAM"), ("cli_de", "DEULOLITONOSTSAM"),
                   ("cli_fr", "FRALOLITONOSTSAM"), ("cli_it", "ITALOLITONOSTSAM")):
        R[k] = _monthly(_fred(sid))
    for nm in ECB:
        d = pd.read_csv(MACRO / f"{ARM}_ecb_{nm}.csv")
        R[nm] = pd.Series(d["value"].astype(float).values, index=pd.PeriodIndex(d["month"], freq="M")).sort_index()
    return R


DAILY_KEYS = ("brent", "ttf", "ng", "tips", "bei", "hh_spot")
MONTHLY_LAG = {"eu_gas": "gas", "umich": "umich", "cli_us": "cli", "cli_ea": "cli", "cli_de": "cli", "cli_fr": "cli",
               "cli_it": "cli", "esi": "esi", "trade_x": "trade", "trade_m": "trade"}


def truncate_raw(R: dict, asof: pd.Timestamp) -> dict:
    """The raw data as a user would have held it on calendar date `asof` under the declared publication lags
    (daily stamp d exists from d + 1 day; month m from month-end + LAG days). Leak check only."""
    out = {}
    for k, s in R.items():
        if k in DAILY_KEYS:
            out[k] = s[s.index + pd.Timedelta(days=1) <= asof]
        else:
            av = s.index.to_timestamp(how="end").normalize() + pd.Timedelta(days=LAG[MONTHLY_LAG[k]])
            out[k] = s[av <= asof]
    return out


# ================================================================ signals
def _daily(s: pd.Series, cdate: pd.DatetimeIndex) -> np.ndarray:
    """Daily market series on the session grid: last stamp <= closing date - 1 day; NaN when that stamp is stale."""
    v = _align_lagged(s, cdate, 1).values
    stamp = _align_lagged(pd.Series(s.index.values.astype("datetime64[ns]").astype("int64").astype(float), index=s.index), cdate, 1).values
    age = (cdate.values.astype("datetime64[ns]").astype("int64") - stamp) / 86400e9
    return np.where(age <= STALE_D + 1, v, np.nan)


def _monthly_on_grid(s: pd.Series, lag_days: int, cdate: pd.DatetimeIndex) -> np.ndarray:
    """Monthly statistic (PeriodIndex) on the session grid: usable from month-end + lag_days (+ 1 day), switched off
    when the newest usable observation became available more than STALE_M days ago."""
    s = s.dropna()
    if s.empty:
        return np.full(len(cdate), np.nan)
    av = s.index.to_timestamp(how="end").normalize() + pd.Timedelta(days=lag_days)
    v = _align_lagged(pd.Series(s.values, index=av), cdate, 1).values
    stamp = _align_lagged(pd.Series(av.values.astype("datetime64[ns]").astype("int64").astype(float), index=av), cdate, 1).values
    age = (cdate.values.astype("datetime64[ns]").astype("int64") - stamp) / 86400e9
    return np.where(age <= STALE_M + 1, v, np.nan)


def _exp_sd(s: pd.Series, min_periods: int = 120) -> pd.Series:
    return s.expanding(min_periods=min_periods).std()


def build_signals(D: pd.DataFrame, R: dict | None = None) -> pd.DataFrame:
    """The 12 oriented signals on the session grid of the feature store (positive = long EUR/USD)."""
    R = load_raw() if R is None else R
    cdate = pd.DatetimeIndex(pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None))
    S = pd.DataFrame(index=D.index)
    eur_prev = D["close"].shift(1).values                      # NY close of the previous session
    ld = lambda a, k: pd.Series(np.log(a)).diff(k).values      # k-session log change on the session grid
    dd = lambda a, k: pd.Series(a).diff(k).values
    # ---- A energy
    brent = _daily(R["brent"], cdate)
    brent_eur = brent / eur_prev
    S["brent_eur_d63"] = -ld(brent_eur, 63)
    S["brent_eur_d126"] = -ld(brent_eur, 126)
    S["brent_usd_d126"] = -ld(brent, 126)
    hh_m = R["hh_spot"].groupby(pd.PeriodIndex(R["hh_spot"].index, freq="M")).mean()
    n_m = R["hh_spot"].groupby(pd.PeriodIndex(R["hh_spot"].index, freq="M")).size()
    hh_m = hh_m[n_m >= 15]                                     # complete months only
    ratio_m = np.log(R["eu_gas"] / hh_m).dropna()
    ratio_m = ratio_m.reindex(pd.period_range(ratio_m.index[0], ratio_m.index[-1], freq="M")) if len(ratio_m) else ratio_m
    S["gasratio_d3m"] = -_monthly_on_grid(ratio_m.diff(3), LAG["gas"], cdate)
    ttf_usd = _daily(R["ttf"], cdate) * eur_prev / 3.412142   # EUR/MWh -> USD/MMBtu
    S["ttf_hh_d63"] = -ld(ttf_usd / _daily(R["ng"], cdate), 63)
    tb = ((R["trade_x"] - R["trade_m"]) / (R["trade_x"] + R["trade_m"])).dropna()
    tb3 = tb.rolling(3).mean()
    S["ea_tb_mom"] = _monthly_on_grid(tb3 - tb3.shift(3), LAG["trade"], cdate)
    # ---- B growth
    big3 = pd.concat([R["cli_de"], R["cli_fr"], R["cli_it"]], axis=1).dropna().mean(axis=1)
    d6_ea = R["cli_ea"].diff(6).combine_first(big3.diff(6))    # EA19 while it exists, DEU/FRA/ITA mean after
    S["cli_d6m_diff"] = _monthly_on_grid((d6_ea - R["cli_us"].diff(6)).dropna(), LAG["cli"], cdate)
    esi, um = R["esi"], R["umich"]
    z_esi = (esi - esi.expanding(min_periods=120).mean()) / _exp_sd(esi)
    z_um = (um - um.expanding(min_periods=120).mean()) / _exp_sd(um)
    S["sent_lvl_diff"] = _monthly_on_grid(z_esi, LAG["esi"], cdate) - _monthly_on_grid(z_um, LAG["umich"], cdate)
    S["sent_d3m_diff"] = _monthly_on_grid(esi.diff(3) / _exp_sd(esi), LAG["esi"], cdate) - _monthly_on_grid(um.diff(3) / _exp_sd(um), LAG["umich"], cdate)
    # ---- C real yields
    tips = _daily(R["tips"], cdate)
    S["tips_d21"] = -dd(tips, 21)
    S["tips_d63"] = -dd(tips, 63)
    S["bei_d63"] = dd(_daily(R["bei"], cdate), 63)
    return S[NAMES].replace([np.inf, -np.inf], np.nan)


# ================================================================ evaluation helpers
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


# ================================================================ main
def compute(cost_pips: float = 1.2, verbose: bool = True) -> dict:
    cat = fetch_all(verbose=verbose)
    D = SL.load_data()
    ctx = SL.make_ctx(D, cost_pips)
    T = SL.build_targets(D)
    R = load_raw()
    S = build_signals(D, R)
    O = old_votes(ctx)
    sg, agree = O["sg"], O["agree"]
    n = len(D)
    rows, decs = [], {}
    # ---- 0 reconciliation: the agreement rule alone (10 sessions included for the comparison with arm N)
    keep = {}
    rows += eval_rule(ctx, T, agree, sg, {"signal": "-", "rule": "agree3"}, horizons=(10, 21, 42, 63), keep=keep)
    decs["agree3"] = keep
    P = [(lab, a, b) for lab, a, b in SL.PERIODS if lab != "2010-15"]
    paired = []
    for nm in NAMES:
        s = S[nm].values
        ss = np.sign(s)
        has = np.isfinite(s) & (ss != 0)
        # 1 standalone
        rows += eval_rule(ctx, T, has & O["base"], ss, {"signal": nm, "rule": "standalone"})
        # 2a AND rule, 2b outside the agreement, baseline on the sessions where the signal exists
        keep = {}
        sp_and = agree & has & (ss == sg)
        rows += eval_rule(ctx, T, sp_and, sg, {"signal": nm, "rule": "and"}, keep=keep)
        decs[nm] = keep
        rows += eval_rule(ctx, T, agree & has & (ss == -sg), sg, {"signal": nm, "rule": "agree3_contradicted"})
        rows += eval_rule(ctx, T, agree & has, sg, {"signal": nm, "rule": "agree3_same_span"})
        rows += eval_rule(ctx, T, O["base"] & ~agree & has, ss, {"signal": nm, "rule": "outside"})
        # 4 placebo: staler signal
        for k in PLACEBO_SHIFTS + (1, 5, 21, -21):
            sk = S[nm].shift(k).values
            sks = np.sign(sk)
            hk = np.isfinite(sk) & (sks != 0)
            rows += eval_rule(ctx, T, agree & hk & (sks == sg), sg, {"signal": nm, "rule": f"and_shift{k:+d}"})
            rows += eval_rule(ctx, T, hk & O["base"], sks, {"signal": nm, "rule": f"standalone_shift{k:+d}"})
            if k in PLACEBO_SHIFTS:
                rows += eval_rule(ctx, T, O["base"] & ~agree & hk, sks, {"signal": nm, "rule": f"outside_shift{k:+d}"})
        # 2c paired bootstrap
        for h in HORIZONS:
            t = T[f"sign{h}"]
            for lab, a, b in P:
                r1 = paired_boot(ctx, t, sp_and, sg, agree & has, sg, a, b)
                r2 = paired_boot(ctx, t, sp_and, sg, agree & has & (ss == -sg), sg, a, b)
                paired.append({"signal": nm, "h": h, "period": lab, "n_and": r1["n_a"], "n_agree_same_span": r1["n_b"], "acc_and": r1["acc_a"],
                               "acc_agree_same_span": r1["acc_b"], "diff": r1["diff"], "diff_lo": r1["lo"], "diff_hi": r1["hi"], "p_le0": r1["p_le0"],
                               "n_contradicted": r2["n_b"], "acc_contradicted": r2["acc_b"], "split": r2["diff"], "split_lo": r2["lo"], "split_hi": r2["hi"],
                               "split_p_le0": r2["p_le0"]})
        if verbose:
            print(f"  signal {nm}: done", flush=True)
    V = pd.DataFrame(rows)
    return {"cat": cat, "D": D, "ctx": ctx, "T": T, "R": R, "S": S, "O": O, "V": V, "paired": pd.DataFrame(paired), "decs": decs, "n": n}


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
    for h in (21, 42, 63):
        for lab in ("2010-26", "2016-26", "2023-26"):
            a = _cell(V, signal=nm, rule="and", h=h, mode="nonoverlap", period=lab)
            b = _cell(V, signal="-", rule="agree3", h=h, mode="nonoverlap", period=lab)
            r = {"h": h, "period": lab, "agree3_acc": b["accuracy"], "agree3_n": int(b["n"]), "agree3_per_year": b["dec_per_year"],
                 "and_acc": a.get("accuracy", np.nan), "and_lo": a.get("lo", np.nan), "and_hi": a.get("hi", np.nan), "and_n": int(a["n"]),
                 "and_per_year": a.get("dec_per_year", np.nan)}
            r["gain_pts"] = 100 * (r["and_acc"] - r["agree3_acc"])
            for k in PLACEBO_SHIFTS:
                p = _cell(V, signal=nm, rule=f"and_shift{k:+d}", h=h, mode="nonoverlap", period=lab)
                r[f"placebo{k}_acc"] = p.get("accuracy", np.nan)
                r[f"placebo{k}_n"] = int(p["n"])
                r[f"placebo{k}_gain_pts"] = 100 * (r[f"placebo{k}_acc"] - r["agree3_acc"])
            rows.append(r)
    return pd.DataFrame(rows)


def bar_verdict(B: pd.DataFrame) -> dict:
    g = lambda h, lab, c: float(B[(B.h == h) & (B.period == lab)][c].iloc[0])
    v = {}
    v["gain_ok"] = all(g(h, lab, "gain_pts") >= 3.0 for h in (21, 42) for lab in ("2010-26", "2016-26"))
    v["count21_ok"] = all(g(21, lab, "and_per_year") >= MIN_DEC_PER_YEAR for lab in ("2010-26", "2016-26"))
    v["count42_ok"] = all(g(42, lab, "and_per_year") >= MIN_DEC_PER_YEAR for lab in ("2010-26", "2016-26"))
    v["not_worse_2023"] = all(g(h, "2023-26", "gain_pts") >= 0 for h in (21, 42))
    pl = []
    for h in (21, 42):
        for lab in ("2010-26", "2016-26"):
            gain = g(h, lab, "gain_pts")
            pl.append(all(g(h, lab, f"placebo{k}_gain_pts") <= 0.5 * gain for k in PLACEBO_SHIFTS) if gain > 0 else False)
    v["placebo_ok"] = all(pl)
    v["met"] = bool(v["gain_ok"] and v["count21_ok"] and v["not_worse_2023"] and v["placebo_ok"])
    v["met_strict_42_count"] = bool(v["met"] and v["count42_ok"])
    return v


def leak_checks(res: dict, final: str, reps: int = 300) -> dict:
    ctx, T, S, O, D, R = res["ctx"], res["T"], res["S"], res["O"], res["D"], res["R"]
    sg, agree = O["sg"], O["agree"]
    out = {}
    # (1) permuted labels
    rng = np.random.default_rng(3)
    rows = []
    for h in HORIZONS:
        t = T[f"sign{h}"]
        valid = np.isfinite(t.long) & (ctx.year >= 2010)
        vi = np.where(valid)[0]
        g = np.arange(0, len(valid), SL.STEP)
        g = g[valid[g]]
        for nm in dict.fromkeys([final, "brent_usd_d126"]):
            s = np.sign(S[nm].values)
            has = np.isfinite(S[nm].values) & (s != 0)
            for rule, sp, dr in (("and", agree & has & (s == sg), sg), ("standalone", has & O["base"], s)):
                gi = g[sp[g]]
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
    # (2b) truncation test: the row of date T0 built from raw data cut at T0 must equal the full build
    rows = []
    cdate = pd.DatetimeIndex(pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None))
    for d0 in ("2012-06-29", "2016-11-15", "2020-03-16", "2022-09-30", "2025-02-14"):
        i = int(np.searchsorted(cdate.values, np.datetime64(d0), side="right") - 1)
        St = build_signals(D.iloc[: i + 1], truncate_raw(R, cdate[i]))
        a, b = S.iloc[i].values.astype(float), St.iloc[i].values.astype(float)
        same = np.isclose(a, b, rtol=1e-9, atol=1e-12, equal_nan=True)
        rows.append({"asof": str(cdate[i].date()), "signals_defined": int(np.isfinite(a).sum()), "rows_equal": int(same.sum()), "of": len(a),
                     "max_abs_diff": float(np.nanmax(np.abs(a - b))) if np.isfinite(a - b).any() else 0.0, "mismatch": ",".join(np.array(NAMES)[~same])})
    out["truncation"] = pd.DataFrame(rows)
    # (3) what the signals are correlated with
    y = D.index.year.values >= 2010
    rows = []
    for nm in NAMES:
        s = S[nm]
        r = {"signal": nm, "first_value": str(s.first_valid_index())[:10], "last_value": str(s.last_valid_index())[:10],
             "defined_2010-26": float(s[y].notna().mean()), "share_long_2010-26": float((s[y] > 0).sum() / max(s[y].notna().sum(), 1)),
             "sign_flips_per_year": float((np.sign(s[y]).diff().abs() > 0).sum() / (y.sum() / 252))}
        for c in ("ret_21d", "ret_63d", "ret_126d"):
            r[f"corr_{c}"] = float(s[y].corr(D[c][y]))
        for c, v in (("cot", O["cot"]), ("spr", O["spr"]), ("house", sg)):
            ok = y & np.isfinite(s.values) & np.isfinite(v) & (v != 0) & (np.sign(s.values) != 0)
            r[f"sign_agree_{c}"] = float((np.sign(s.values[ok]) == v[ok]).mean()) if ok.sum() else np.nan
        for h in (21, 63):
            f = pd.Series(res["T"][f"sign{h}"].long, index=D.index)
            r[f"corr_fwd{h}"] = float(s[y].corr(f[y]))
        rows.append(r)
    out["features"] = pd.DataFrame(rows)
    return out


def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True) -> tuple[pd.Series, pd.DataFrame]:
    """Arm entry point: (daily positions of the final AND rule, protocol report). Writes the deliverables."""
    pos, rep, _ = run_full(cost_pips, write, verbose)
    return pos, rep


def run_full(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Builds the signals, evaluates the 12 candidates as the round-5 addendum prescribes, applies the declared
    selection rule and writes the deliverables. Returns (daily positions, protocol report, every intermediate table)."""
    res = compute(cost_pips, verbose=verbose)
    ctx, T, V, D = res["ctx"], res["T"], res["V"], res["D"]
    Sx, final, status = select_final(V)
    res["selection"], res["final"], res["final_status"] = Sx, final, status
    res["bar"] = bar_table(V, final)
    res["bar_verdict"] = bar_verdict(res["bar"])
    res["bar_all"] = pd.concat([bar_table(V, nm).assign(signal=nm) for nm in NAMES], ignore_index=True)
    res["bar_verdict_all"] = pd.DataFrame([{"signal": nm, **bar_verdict(bar_table(V, nm))} for nm in NAMES])
    # daily books (weekly tranches held 21 sessions) of every AND rule + the agreement rule as reference
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
    tb = report(book(res["decs"][final][(SEL_H, "weekly")], 0.6), periods_per_year=252, name=ARM, n_arms=N_ARMS)
    tb.insert(1, "variant", f"and_{final}_cost0.6"); tb["final"] = False; tb["kind"] = "cost_sensitivity"; tb["cost_pips"] = 0.6
    reps.append(tb)
    rep = pd.concat(reps, ignore_index=True)
    daily = streams[final].copy()
    daily["fwd_bp"] = D["fwd_1d"].reindex(daily.index)
    daily = daily[["pos", "fwd_bp", "net_bp"]]
    res["report"], res["streams"], res["daily"] = rep, streams, daily
    by = SL.by_year(res["decs"][final][(SEL_H, "weekly")])
    ref = SL.by_year(res["decs"]["agree3"][(SEL_H, "weekly")]).set_index("year")
    by["agree3_decisions"] = by["year"].map(ref["decisions"])
    by["agree3_accuracy"] = by["year"].map(ref["accuracy"])
    yr = rep[(rep["variant"] == f"and_{final}") & rep["period"].str.fullmatch(r"\d{4}")]
    by["book_sharpe"] = by["year"].map(pd.Series(yr["sharpe"].values, index=yr["period"].astype(int).values))
    res["by_year"] = by
    res["leak"] = leak_checks(res, final)
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        daily.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        V.insert(0, "arm", ARM) if "arm" not in V else None
        V["final"] = (V["signal"] == final) & (V["rule"] == "and")
        V.to_csv(RES / f"{ARM}_votes.csv", index=False)
        res["paired"].to_csv(RES / f"{ARM}_paired.csv", index=False)
        Sx.to_csv(RES / f"{ARM}_candidates.csv", index=False)
        res["bar_all"].to_csv(RES / f"{ARM}_bar.csv", index=False)
        res["S"].to_parquet(RES / f"{ARM}_signals.parquet")
        res["cat"].to_csv(RES / f"{ARM}_data_catalogue.csv", index=False)
        pd.concat([v.assign(check=k) for k, v in res["leak"].items()], ignore_index=True).to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
        res["incremental"], res["corr"] = incremental(streams, final)
        res["incremental"].to_csv(RES / f"{ARM}_incremental.csv", index=False)
    return daily["pos"], rep, res


def incremental(streams: dict, final: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    from eurusd.arms import meta
    rows = []
    for lab, arms in (("two-way weak_signals + regime_trend", ["weak_signals", "regime_trend"]),
                      (f"three-way + {ARM}", ["weak_signals", "regime_trend", ARM]),
                      ("three-way + selective (agreement rule book, for reference)", ["weak_signals", "regime_trend", "selective_daily"])):
        if "selective_daily" in arms and not (RES / "selective_daily_positions.parquet").exists():
            continue
        pnl, _ = meta.combine(arms, "EW")
        tb = meta.report_combo(pnl, lab, N_ARMS)
        rows.append(tb[tb.period.isin(["2010-2026", "2016-2026", "2023-2026"])])
    inc = pd.concat(rows, ignore_index=True)
    me = meta.load_arm_daily(ARM)
    cr = []
    for other in ("weak_signals", "regime_trend", "selective_daily"):
        o = meta.load_arm_daily(other)
        if len(o) < 100:
            continue
        j = pd.concat([me, o], axis=1, keys=["me", "o"]).fillna(0.0)
        j = j[j.index.year >= 2010]
        act = j[j["me"] != 0]
        cr.append({"other": other, "corr_all_days": float(j["me"].corr(j["o"])), "corr_active_days": float(act["me"].corr(act["o"])),
                   "corr_2016-26": float(j[j.index.year >= 2016]["me"].corr(j[j.index.year >= 2016]["o"]))})
    return inc, pd.DataFrame(cr)


# ================================================================ report (python real_economy.py report)
LAG_TXT = {"DFII10": "1 calendar day", "T5YIFR": "1 calendar day", "DHHNGSP": "monthly mean, month-end + 45 d", "PNGASEUUSDM": "month-end + 45 d",
           "UMCSENT": "month-end + 10 d", "LOLITONOSTSAM": "month-end + 45 d", "TTF=F": "1 calendar day", "NG=F": "1 calendar day",
           "Y_ESIND": "month-end + 10 d", "TRD/": "month-end + 50 d", "datahub": "1 calendar day"}


def _fmt(c, ci: bool = True, py: bool = False) -> str:
    if c is None or not c["n"] or not np.isfinite(c.get("accuracy", np.nan)):
        return "-"
    s = f"{100 * c['accuracy']:.0f}"
    if ci:
        s += f" [{100 * c['lo']:.0f}-{100 * c['hi']:.0f}]"
    s += f" n={int(c['n'])}"
    if py:
        s += f" ({c['dec_per_year']:.1f}/y)"
    return s


def _grid(V: pd.DataFrame, rule: str, mode: str, period: str, sigs, ci=True, py=False, hs=HORIZONS, gain_vs: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    for nm in sigs:
        r = {"signal": nm}
        for h in hs:
            c = _cell(V, signal=nm, rule=rule, h=h, mode=mode, period=period)
            txt = _fmt(c, ci, py)
            if gain_vs is not None and c is not None and c["n"]:
                b = _cell(gain_vs, h=h, mode=mode, period=period)
                txt += f" {100 * (c['accuracy'] - b['accuracy']):+.1f}"
            r[f"{h} s"] = txt
        rows.append(r)
    return pd.DataFrame(rows)


def write_report(path: Path | None = None) -> str:
    r = pd.read_pickle(RES / "logs" / f"{ARM}_tables.pkl")
    V, P, final = r["V"], r["paired"], r["final"]
    A = V[(V.signal == "-") & (V.rule == "agree3")]
    md = [VERDICT_MD.strip(), ""]
    # ---- data
    cat = r["cat"].copy()
    cat["lag used"] = [next((v for k, v in LAG_TXT.items() if k in s), "") for s in cat["source"]]
    md += ["## 1. Data: sources, spans, publication lags", cat.to_markdown(index=False), "", DATA_MD.strip(), ""]
    # ---- signals
    F = r["leak"]["features"].set_index("signal")
    rows = []
    for nm, fam, prior in SIGNALS:
        f = F.loc[nm]
        rows.append({"signal": nm, "fam": fam, "prior (sign on the raw quantity)": prior, "first value": f["first_value"], "last value": f["last_value"],
                     "defined 2010-26": f"{100 * f['defined_2010-26']:.0f} %", "long share": f"{100 * f['share_long_2010-26']:.0f} %",
                     "sign flips / yr": f"{f['sign_flips_per_year']:.1f}"})
    md += ["## 2. The 12 candidate signals and their priors (fixed before any result)", pd.DataFrame(rows).to_markdown(index=False), "", PRIORS_MD.strip(), ""]
    # ---- reconciliation
    rows = []
    armN = {("nonoverlap", "2010-26"): "56 n=291 / 59 n=156 / 61 n=89 / 72 n=61", ("nonoverlap", "2016-26"): "53 n=178 / 57 n=96 / 59 n=56 / 71 n=38",
            ("nonoverlap", "2023-26"): "54 n=63 / 60 n=35 / 45 n=20 / 50 n=14", ("weekly", "2010-26"): "57 n=390 / 59 n=387 / 65 n=383 / 67 n=383",
            ("weekly", "2016-26"): "55 n=246 / 57 n=243 / 63 n=239 / 67 n=239", ("weekly", "2023-26"): "57 n=80 / 55 n=77 / 47 n=73 / 53 n=73"}
    for (mode, per), ref in armN.items():
        mine = " / ".join(_fmt(_cell(A, h=h, mode=mode, period=per), ci=False) for h in (10, 21, 42, 63))
        dy = " / ".join(f"{_cell(A, h=h, mode=mode, period=per)['dec_per_year']:.1f}" for h in (10, 21, 42, 63))
        rows.append({"decisions": mode, "period": per, "arm N report (10 / 21 / 42 / 63 s)": ref, "rebuilt here": mine, "identical": ref == mine, "decisions / yr": dy})
    md += ["## 3. Reconciliation of the agreement rule", RECON_MD.strip(), "", pd.DataFrame(rows).to_markdown(index=False), ""]
    # ---- standalone
    md += ["## 4. Standalone accuracy of each signal (direction = sign of the oriented signal)", STANDALONE_MD.strip(), ""]
    for per in ("2010-26", "2016-26", "2023-26"):
        a = _grid(V, "standalone", "nonoverlap", per, NAMES).rename(columns={f"{h} s": f"non-overlapping {h} s" for h in HORIZONS})
        b = _grid(V, "standalone", "weekly", per, NAMES, ci=False).rename(columns={f"{h} s": f"weekly {h} s" for h in HORIZONS})
        md += [f"*{per}* (accuracy % [Wilson 95 %] n)", "", a.merge(b, on="signal").to_markdown(index=False), ""]
    # ---- extra vote
    md += ["## 5. As an extra vote", EXTRA_MD.strip(), ""]
    for per in ("2010-26", "2016-26", "2023-26"):
        base = pd.DataFrame([{"signal": "agreement rule alone", **{f"{h} s": _fmt(_cell(A, h=h, mode="nonoverlap", period=per), py=True) for h in HORIZONS}}])
        a = _grid(V, "and", "nonoverlap", per, NAMES, py=True, gain_vs=A)
        md += [f"**(a) AND rule, non-overlapping decisions, {per}** (accuracy % [Wilson] n (decisions / year), then the gain in points over the agreement rule)", "",
               pd.concat([base, a], ignore_index=True).to_markdown(index=False), ""]
    for per in ("2010-26", "2016-26"):
        rows = []
        for nm in NAMES:
            x = {"signal": nm}
            for h in HORIZONS:
                x[f"{h} s: same span / confirmed / contradicted"] = " / ".join(_fmt(_cell(V, signal=nm, rule=rl, h=h, mode="weekly", period=per), ci=False)
                                                                                for rl in ("agree3_same_span", "and", "agree3_contradicted"))
            rows.append(x)
        md += [f"**(a') weekly decisions, {per}**: the agreement rule on the sessions where the signal exists / calls the signal confirms (= AND rule) / calls it contradicts", "",
               pd.DataFrame(rows).to_markdown(index=False), ""]
    for per in ("2010-26", "2016-26", "2023-26"):
        a = _grid(V, "outside", "nonoverlap", per, NAMES, py=True).rename(columns={f"{h} s": f"non-overlapping {h} s" for h in HORIZONS})
        b = _grid(V, "outside", "weekly", per, NAMES, ci=False).rename(columns={f"{h} s": f"weekly {h} s" for h in HORIZONS})
        md += [f"**(b) calls of the signal when the three old signals do NOT agree, {per}**", "", a.merge(b, on="signal").to_markdown(index=False), ""]
    for col, lo, hi, ttl in (("diff", "diff_lo", "diff_hi", "(c) paired difference, weekly grid: accuracy(AND rule) - accuracy(agreement rule on the same sessions), points [bootstrap 95 %]"),
                             ("split", "split_lo", "split_hi", "(c') accuracy(agreement calls the signal confirms) - accuracy(agreement calls it contradicts), points [bootstrap 95 %]")):
        rows = []
        for nm in NAMES:
            x = {"signal": nm}
            for per in ("2010-26", "2016-26", "2023-26"):
                for h in HORIZONS:
                    q = P[(P.signal == nm) & (P.h == h) & (P.period == per)].iloc[0]
                    x[f"{per} {h} s"] = f"{100 * q[col]:+.0f} [{100 * q[lo]:+.0f},{100 * q[hi]:+.0f}]" if np.isfinite(q[col]) else "-"
            rows.append(x)
        md += [f"**{ttl}**", "", pd.DataFrame(rows).to_markdown(index=False), ""]
    ex = int(((P["diff_lo"] > 0) | (P["diff_hi"] < 0)).sum())
    md += [f"Of the {int(P['diff'].notna().sum())} paired intervals in (c), {ex} exclude zero ({int((P['diff_lo'] > 0).sum())} positive, {int((P['diff_hi'] < 0).sum())} negative); "
           f"about {0.05 * P['diff'].notna().sum():.0f} would by chance.", ""]
    # ---- selection and final
    Sx = r["selection"].copy()
    for c in ("accuracy_2010-15", "lo_2010-15", "hi_2010-15"):
        Sx[c] = (100 * Sx[c]).round(1)
    Sx["dec_per_year_2010-15"] = Sx["dec_per_year_2010-15"].round(1)
    md += ["## 6. Selection by the declared rule and the record of the pick", SELECT_MD.strip(), "", Sx.to_markdown(index=False), "",
           f"**Final: `{final}`** ({r['final_status']}). Round-5 bar, cell by cell (non-overlapping decisions):", ""]
    B = r["bar"].copy()
    rows = []
    for _, b in B.iterrows():
        rows.append({"h": int(b.h), "period": b.period, "agreement rule": f"{100 * b.agree3_acc:.0f} n={int(b.agree3_n)} ({b.agree3_per_year:.1f}/y)",
                     "AND rule": f"{100 * b.and_acc:.0f} [{100 * b.and_lo:.0f}-{100 * b.and_hi:.0f}] n={int(b.and_n)} ({b.and_per_year:.1f}/y)", "gain pts": f"{b.gain_pts:+.1f}",
                     "placebo +63": f"{100 * b.placebo63_acc:.0f} n={int(b.placebo63_n)} ({b.placebo63_gain_pts:+.1f})",
                     "placebo +126": f"{100 * b.placebo126_acc:.0f} n={int(b.placebo126_n)} ({b.placebo126_gain_pts:+.1f})"})
    md += [pd.DataFrame(rows).to_markdown(index=False), "", "Bar components: " + ", ".join(f"{k} = {v}" for k, v in r["bar_verdict"].items()), ""]
    x = V[(V.signal == final) & (V.rule == "and") & (V.h == SEL_H) & (V.period != "2010-15")]
    rows = [{"decisions": q["mode"], "period": q.period, "n": int(q.n), "per year": round(q.dec_per_year, 1), "correct sign before costs %": round(100 * q.accuracy, 1),
             "interval": f"{100 * q.lo:.0f}-{100 * q.hi:.0f}", "positive net P&L %": round(100 * q.win_rate_net, 1), "net bp / decision": round(q.net_bp, 1),
             "avg win bp": round(q.avg_win_bp, 0), "avg loss bp": round(q.avg_loss_bp, 0), "long share %": round(100 * q.share_long, 0)} for _, q in x.iterrows()]
    md += ["Hit rates of the final rule at 21 sessions (round-4 format; weekly interval = Wilson with Newey-West effective n):", "", pd.DataFrame(rows).to_markdown(index=False), "",
           "Per year (weekly decisions by decision date; the agreement rule next to it):", "", r["by_year"].round(2).to_markdown(index=False), ""]
    BV = r["bar_verdict_all"]
    md += ["The same bar applied to every candidate (none was selected from this table; it shows that the verdict does not hinge on the pick):", "",
           BV.to_markdown(index=False), ""]
    # ---- placebo
    md += ["## 7. Timing placebo (signal made 63 / 126 sessions staler)", PLACEBO_MD.strip(), ""]
    BA = r["bar_all"]
    for mode_lab, tabf in (("non-overlapping", None),):
        rows = []
        for nm in NAMES:
            x = {"signal": nm}
            for per in ("2010-26", "2016-26"):
                for h in (21, 42):
                    b = BA[(BA.signal == nm) & (BA.h == h) & (BA.period == per)].iloc[0]
                    x[f"{per} {h} s: gain fresh / +63 / +126"] = f"{b.gain_pts:+.1f} / {b.placebo63_gain_pts:+.1f} / {b.placebo126_gain_pts:+.1f}"
            rows.append(x)
        md += ["AND rule, gain in points over the agreement rule, non-overlapping decisions:", "", pd.DataFrame(rows).to_markdown(index=False), ""]
    rows = []
    for nm in NAMES:
        x = {"signal": nm}
        for h in (21, 63):
            x[f"standalone {h} s: -21 (look-ahead) / fresh / +1 / +5 / +21 / +63 / +126"] = " / ".join(
                f"{100 * _cell(V, signal=nm, rule=rl, h=h, mode='weekly', period='2010-26')['accuracy']:.0f}"
                for rl in ("standalone_shift-21", "standalone", "standalone_shift+1", "standalone_shift+5", "standalone_shift+21", "standalone_shift+63", "standalone_shift+126"))
        x["AND 21 s: fresh / +63 / +126"] = " / ".join(f"{100 * _cell(V, signal=nm, rule=rl, h=21, mode='weekly', period='2010-26')['accuracy']:.0f}" for rl in ("and", "and_shift+63", "and_shift+126"))
        x["outside 21 s: fresh / +63 / +126"] = " / ".join(f"{100 * _cell(V, signal=nm, rule=rl, h=21, mode='weekly', period='2010-26')['accuracy']:.0f}" for rl in ("outside", "outside_shift+63", "outside_shift+126"))
        rows.append(x)
    md += ["Weekly decisions, 2010-26, accuracy % as the signal is shifted in time:", "", pd.DataFrame(rows).to_markdown(index=False), ""]
    # ---- daily stream
    rep = r["report"]
    x = rep[rep.period.isin(["2010-2026", "2016-2026", "2023-2026", "2010-2015"])]
    piv = x.pivot_table(index="variant", columns="period", values="sharpe", aggfunc="first").round(2)
    piv["t 2010-26"] = x[x.period == "2010-2026"].set_index("variant")["t"].round(2)
    piv["deflated p"] = x[x.period == "2010-2026"].set_index("variant")["deflated_sharpe_p"].round(2)
    piv["active"] = x[x.period == "2010-2026"].set_index("variant")["active_frac"].round(2)
    order = [f"and_{n}" for n in NAMES] + [f"and_{final}_cost0.6", "agree3_reference"]
    piv = piv.reindex(order).reset_index()
    piv["final"] = piv["variant"] == f"and_{final}"
    md += ["## 8. Daily stream and incremental test", STREAM_MD.strip(), "", piv.to_markdown(index=False), "",
           "Incremental test (EW, walk-forward weights, `meta.combine` / `report_combo`):", "", r["incremental"].round(3).to_markdown(index=False), "",
           "Daily net P&L correlation of the final stream:", "", r["corr"].round(2).to_markdown(index=False), ""]
    # ---- leak checks
    md += ["## 9. Leak checks", LEAK_MD.strip(), "", "(1) labels permuted (300 draws, weekly decisions, 2010-26):", "", r["leak"]["shuffle"].round(3).to_markdown(index=False), "",
           "(2b) truncation test (raw data cut at the date under the declared lags; the 12 signal values of that session must be unchanged):", "",
           r["leak"]["truncation"].to_markdown(index=False), "",
           "(3) what each signal is correlated with (2010-26; correlations of the signal VALUE, agreement shares of its SIGN):", "",
           r["leak"]["features"].drop(columns=["first_value", "last_value", "defined_2010-26", "share_long_2010-26", "sign_flips_per_year"]).round(3).to_markdown(index=False), "",
           TAIL_MD.strip(), ""]
    txt = "\n".join(md)
    (path or ROOT / "reports" / f"arm_{ARM}.md").write_text(txt)
    return txt


# ---- narrative of the report (written AFTER the results; the numbers quoted are those of the tables below it)
VERDICT_MD = r"""
# Arm R: real economy (`real_economy`) - energy terms of trade, growth leading indicators and US real yields as an extra vote

Code `src/eurusd/arms/real_economy.py` (`run(cost_pips=1.2)`; `python -I src/eurusd/arms/real_economy.py` fetches (cached), runs
everything in about 20 seconds once the data are cached and rebuilds this file; `... real_economy.py report` rebuilds the file only). Results in
`experiments/results/arms/`: `real_economy_positions.parquet` (daily stream of the final extra-vote rule: `pos`, `fwd_bp`, `net_bp`),
`real_economy_report.csv` (protocol table of the 12 candidates, `variant`, `final`, plus the agreement rule as reference and the 0.6-pip
run), `real_economy_votes.csv` (every signal x rule x horizon x decision mode x period: n, decisions per year, accuracy, Wilson
interval, net bp), `real_economy_paired.csv`, `real_economy_bar.csv`, `real_economy_candidates.csv`, `real_economy_leakchecks.csv`,
`real_economy_incremental.csv`, `real_economy_signals.parquet`, `real_economy_data_catalogue.csv`, log `logs/real_economy.log`.
The docstring of the module (signals, signs, lags, evaluation, selection rule) was written before the first accuracy number.

## Verdict
1. **The round-5 success bar is NOT met - not by the rule the declared selection picks, and not by any of the other 11.**
   The pick is `cli_d6m_diff` (agreement rule AND the euro-area-minus-US 6-month change of the OECD leading indicator agrees).
   Non-overlapping decisions, against the agreement rule alone:
   * 21 sessions: 60 % [49-69] n=87 vs 59 % n=156 in 2010-26 (**+0.8 points**), 60 % n=45 vs 57 % n=96 in 2016-26 (**+2.7**),
     50 % n=10 vs 60 % n=35 in 2023-26 (**-10**). 5.2 / 4.2 decisions a year (bar: 6).
   * 42 sessions: 65 % n=51 vs 61 % n=89 (+4.0), 63 % n=27 vs 59 % n=56 (+4.0), 50 % n=6 vs 45 % n=20; 3.1 / 2.5 decisions a year.
   * 63 sessions: 68 % n=40 vs 72 % n=61 (-4.6), 62 % n=21 vs 71 % n=38 (-9.1).
   Bar components: gain of 3 points at 21 AND 42 sessions in both periods - no (21 sessions fails twice); 6 decisions a year - no;
   not worse in 2023-26 - no (21 sessions); placebo loses half the gain - yes, but there is no gain to lose. In its own selection
   period (2010-15) the AND rule is at 59.5 % (n=42) and the agreement rule alone at 61.7 % (n=60): the pick "wins" a contest in which
   every entrant is below the benchmark. The runner-up (`gasratio_d3m`, lower bound 44.4 % against 44.5 %) is at -1.4 / -0.8 points.
   The pick also rests on revised (not real-time) OECD data and has no value after May 2024 (FRED froze the series, the OECD API is
   blocked here).
2. **A fourth vote from these three families does not sharpen the agreement rule.** Across the 12 candidates the non-overlapping gain
   over the agreement rule is negative for 11 of 12 at 21 sessions in 2010-26 (median -3.8 points, range -10.1 .. +0.8), about zero at
   42 sessions (median +1.5, range -5.1 .. +8.2 on 37-76 decisions) and negative for all 12 at 63 sessions (-1.9 .. -13.0). No candidate
   reaches +3 at 21 sessions in 2010-26, and none has +3 at both 21 and 42 sessions in both periods. The AND rules make 3.5-7.1
   non-overlapping decisions a year at 21 sessions and 2.2-4.6 at 42. On the weekly grid, paired with the agreement rule on the same
   sessions, no difference at 21 sessions excludes zero in 2010-26 or 2016-26 for any candidate. Calls that the new vote CONTRADICTS are
   right about as often as calls it confirms (46-61 % against 49-60 % at 21 sessions, non-overlapping, 2010-26): the vote does not sort.
3. **Standalone, at 1-3 months, only 6-month Brent carries anything, and it is arm O's finding, not timely information.**
   `brent_usd_d126` (sign adopted from arm O, not re-fitted): 55 % [48-61] n=208 / 57 % [47-66] n=104 / 68 % [56-78] n=69 at
   21 / 42 / 63 sessions non-overlapping in 2010-26 (weekly 56 / 56 / 58, n=869); 2016-26 55 / 61 / 73 (n=133 / 66 / 44), weekly
   58 / 59 / 60; 2023-26 47 / 61 / 80 (n=47 / 23 / 15), weekly 53 / 50 / 52. That reproduces arm O's 55-58 %. But the same signal made
   63 sessions STALER scores 59 % at 21 sessions (fresh 56 %) and 59 % at 63 (fresh 58 %): it is a slow regime bet (the 2014-16 and
   2020-22 oil cycles), not information that has to be fresh. In EUR terms it is weaker (53 / 53 / 64; weekly 53 / 53 / 55).
   Everything else is at chance:
   * Europe-vs-US gas, monthly (`gasratio_d3m`): 52 / 53 / 49 (n=208 / 104 / 69). Daily TTF / Henry Hub (`ttf_hh_d63`, 2018-26 only):
     57 % [48-66] n=108 / 59 % [46-71] n=54 / 47 % [32-63] n=36, weekly 55 / 60 / 59 (n=452) - one gas shock, intervals contain 50.
   * Euro-area trade balance momentum: 56 / 53 / 59 non-overlapping, 52 / 51 / 51 weekly.
   * Growth: CLI differential 52 / 48 / 48; sentiment level differential 44 / 42 / 46; sentiment 3-month change 45 / 50 / 51.
   * US real yields as CHANGES: `tips_d21` 50 / 47 / 48, `tips_d63` 46 / 53 / 52 (weekly 46-49: if anything wrongly signed, as arm O
     found for levels); 5y5y breakeven 51 / 41 / 48.
4. **Coverage extension (calls when the three old signals do not agree): no.** 42-58 % at 21 sessions in 2010-26 and 2016-26; only `brent_usd_d126` is
   above 53 % with any consistency (55 % [47-62] n=170 / 56 % n=93 / 56 % n=64; weekly 55 / 56 / 56, n=482), and its 63-session-stale
   version does 58 / 59 / 57.
5. **Daily stream and incremental test: fails.** The final rule as a weekly-tranche book: net Sharpe 0.47 / 0.35 / -0.19
   (2010-26 / 2016-26 / 2023-26) at 1.2 pips against 0.52 / 0.51 / 0.43 for the agreement rule itself; three-way EW 0.62 against
   two-way 0.64 on 2016-26 (0.26 against 0.36 on 2023-26). Daily P&L correlation 0.98 with the agreement-rule book on active days,
   0.78 with `regime_trend`. It is a thinned copy of the existing stream.
6. **Two leads, neither a result.** (i) Daily TTF / Henry Hub as a confirmation: on WEEKLY decisions the AND rule is 63 / 74 / 75 %
   (n=123 / 119 / 119) against 56 / 62 / 65 % for the agreement rule on the same 2018-26 sessions, paired difference
   +7 [-1,+14] / +12 [+3,+21] / +10 [+3,+17] points, and it fades when the signal is made stale (55 / 57 at 21 sessions). The
   non-overlapping stream does NOT confirm it (53 / 62 / 67 % on 59 / 37 / 27 decisions against 58 / 61 / 69 %), the history is 8.8
   years with one gas shock, it has no 2010-15 record so the declared rule could not pick it, and 12 of the 108 paired intervals
   exclude zero where about 5 would by chance (8 positive, 4 negative, heavily overlapping cells). Worth a forward look, nothing more.
   (ii) US real-yield changes are wrongly signed as a vote: when `tips_d21` contradicts the agreement rule the rule is right more
   often (2016-26, 42 sessions: confirmed minus contradicted -20 points [-34,-5]). I did not flip the sign: that would be fitting it.
"""

DATA_MD = r"""
* **Lags.** Daily market series: stamp d is used from the session whose NY-close date is >= d + 1 calendar day
  (`featstore._align_lagged(..., 1)`, the convention of every earlier arm). Monthly series: reference month m is used from
  month-end(m) + LAG days, plus the same one day. LAG = 45 d for the OECD leading indicators (published about six weeks after
  the month) and for the IMF European gas price (IMF publishes in the first half of m+1, FRED later); 50 d for euro-area trade
  (Eurostat releases around day 15-18 of m+2); 10 d for the Commission's Economic Sentiment Indicator (released on the
  next-to-last working day of m, a few times in the first week of m+1) and for the final Michigan sentiment (last or
  next-to-last Friday of m). A monthly signal gives no vote once its newest usable observation is more than 75 days old; a daily
  one once its newest stamp is more than 10 days old.
* **TTF history is short.** Yahoo `TTF=F` starts 2017-10-23; with a 63-session change the signal exists from 2018-01-22, i.e. for
  52 % of 2010-26 and not at all in the 2010-15 selection window. The long-history stand-in is the IMF monthly European gas price
  (FRED `PNGASEUUSDM`, USD/MMBtu: TTF in recent years, border prices before) against the monthly mean of the Henry Hub spot
  (FRED `DHHNGSP`, months with at least 15 quotes; FRED's file is thin before 2007, so the ratio signal starts 2007-09).
* **Conversions.** Brent in EUR = Brent (USD) / previous-session EUR/USD close; TTF in USD/MMBtu = EUR/MWh x previous-session
  EUR/USD / 3.412. The gas ratios are in a common currency. Signals built this way contain the lagged EUR/USD return by
  construction; `brent_usd_d126` is the currency-free control (correlations in section 9).
* **Vintage.** Every monthly series is the CURRENT vintage. The OECD CLI is revised materially (the trend is re-estimated every
  month), the trade balance moderately, sentiment hardly. ALFRED (real-time vintages) is refused by the proxy, so this look-ahead
  could not be removed or measured. It favours the CLI signal, which is the one the selection rule picked; it failed anyway.
* **OECD CLI stops.** FRED froze the OECD series at 2024-01 (`EA19LOLITONOSTSAM` at 2022-11; after that the 6-month change of the
  DEU/FRA/ITA mean is used). `sdmx.oecd.org` answers 403 through the proxy, so `cli_d6m_diff` has no value after 2024-05-30.
* **Euro-area real yields: not built.** An AAA yield minus TRAILING HICP is not an expectation; its 1-3 month change is the nominal
  change plus base effects, and arm O found the trailing-inflation real differential wrongly signed (43-48 %). Family C is US-only.
* **Not reachable (proxy 403):** `sdmx.oecd.org`, `ec.europa.eu` (Eurostat, DG ECFIN), `api.db.nomics.world`, `alfred.stlouisfed.org`,
  `www.eia.gov`. Reachable: `fred.stlouisfed.org` with `curl --http1.1`, the Yahoo chart API with a browser User-Agent, the ECB data
  API. The ESI comes from the ECB flow `RTD` (the ECB `SUR` flow only has quarterly items); it ends 2026-08 there. US ISM: not free, skipped.
* **A bug caught before any result:** Yahoo daily bars are stamped at midnight exchange time (04:00 or 05:00 UTC). Converting with
  the current `gmtoffset` put every summer bar one day EARLY (a one-day look-ahead on TTF and NG). The fetch converts with the
  exchange time zone; the cached parquet files carry the trading date.
"""

PRIORS_MD = r"""
* Positive value = vote for long EUR/USD. No fitting, no thresholds, no sign learned from the data; the vote is the sign.
* Oil: arm O's table has `oil_d126` = -(126-session log change of Brent) with the prior "dearer oil worsens euro-area terms of
  trade" and 55-58 %. That sign is adopted for all three Brent signals and for the gas signals; it was not re-fitted.
* `bei_d63` has a weak prior (the opposite story is as respectable); `sent_lvl_diff` is long 81 % of the time because Michigan
  sentiment has sat below its own history since 2008 far more than the ESI has: by construction a regime bet.
"""

RECON_MD = r"""
Rebuilt with `selective.load_data`, `make_ctx`, `build_targets` and `house_score_wf` (walk-forward house score), agreement =
sign(cot_z52) = sign(d_spread2y_20) = sign(house score), evaluated with `selective.weekly_idx` / `seq_idx` / `cell_stats`. Every
accuracy and every n equals arm N's report; the weekly-tranche book of the 21-session rule has net Sharpe 0.52 / 0.51 / 0.43, also
identical. The agreement rule itself makes 9.3 non-overlapping decisions a year at 21 sessions and 5.3 at 42, so "at least 6 a year"
cannot hold at 42 sessions for ANY rule that only removes calls; the count is judged at 21 sessions and printed everywhere.
"""

STANDALONE_MD = r"""
One decision whenever the signal is non-zero: weekly grid (every 5th session, overlapping holds; no interval shown because the
overlap makes a plain one meaningless) and the greedy non-overlapping stream (plain Wilson 95 %). The up-base rate is 48-52 % in every
period, so 50 % is the mark to beat. `ttf_hh_d63` exists from 2018 only (its 2010-26 and 2016-26 rows are the same 8.8 years);
`cli_d6m_diff` ends in May 2024.
"""

EXTRA_MD = r"""
(a) AND rule = the agreement rule speaks and the sign of the new signal equals its direction. (b) OUTSIDE = direction of the new
signal on sessions where the three old signals do not agree. (c) paired differences on the weekly grid with a circular block
bootstrap (block 2h/5 weeks, 2000 draws, the same blocks for both rules); the baseline in (c) is the agreement rule restricted to
the sessions where the signal exists, so a signal with a short history is compared like for like. The gains printed in (a) are
against the agreement rule on the WHOLE period, which is what the bar asks for.
"""

SELECT_MD = r"""
Declared rule: highest LOWER Wilson bound of the 2010-2015 non-overlapping 21-session accuracy of the AND rule, among candidates with
at least 6 such decisions a year in 2010-2015. For reference the agreement rule alone in 2010-15: 61.7 % [49.0-72.9], n=60, 10.0 a
year - higher than every AND rule in the table.
"""

PLACEBO_MD = r"""
The signal is shifted by +63 and +126 sessions (staler) and the rule re-evaluated. A vote that helps as much when it is three or six
months old is a regime bet. Reading: the pick (`cli_d6m_diff`) loses everything when stale, but its fresh gain is +0.8 / +2.7 points
at 21 sessions, i.e. nothing. The Brent signals do NOT pass: their AND-rule and standalone numbers are as good or better 63 sessions
stale (`brent_usd_d126` AND rule, weekly 21 sessions: 65 % fresh, 65 % at +63; standalone 56 % fresh, 59 % at +63). `ea_tb_mom`'s +8
points at 42 sessions falls to +0.4 / -0.3 when stale, but it is -3.9 at 21 sessions and -13.0 at 63 on 44-98 decisions: noise around zero.
The look-ahead column (-21: the signal as it will be 21 sessions later) shows the test has power where information exists:
`tips_d21` goes from 49 % to 60 %, because real yields and EUR/USD move together within the month and not afterwards.
"""

STREAM_MD = r"""
Each AND rule as a book of weekly tranches held 21 sessions (`selective.book_time_exit`: weight 1/5 per tranche, turnover netted,
1.2 pips per unit turnover), net Sharpe by period; `agree3_reference` is the agreement rule through the same code (arm N: 0.52 / 0.51 /
0.43). Deflated-Sharpe p for 12 candidates. The final stream misses the round-3 bar as well (2023-26 negative, three-way below two-way).
Some AND books have a higher Sharpe than the reference in 2016-26 (`brent_eur_d63` 0.76, `brent_usd_d126` 0.68); with twelve thinned
copies of a 0.51 stream that is expected, none was selected, and their 2010-15 and placebo records (above) do not support them.
"""

LEAK_MD = r"""
* (1) Permuted labels: every rule falls to 50-51 % (5-95 % band 45-57 %).
* (2) Shifted features. One period staler (+1) changes nothing for 3-6-month signals (table in section 7: within a point), so
  "collapses when shifted by one" cannot apply to slow votes; the round-5 placebo (+63 / +126) is the meaningful version and is in
  section 7. The look-ahead control (-21) raises `tips_d21` from 49 to 60 %, the CLI from 54 to 56 %, `gasratio_d3m` from 53 to 55 % and
  `brent_eur_d63` from 51 to 55 % (its EUR conversion then contains the future EUR/USD return), and does not help `brent_usd_d126`
  (56 -> 53): the test sees look-ahead where there is some, and the honest signals do not have it.
* (2b) Truncation: raw data cut at five dates under the declared lags reproduce the stored signal row exactly (12 of 12 each time),
  so no value uses an observation that would not yet have been published (revisions aside, see section 1).
* (3) No signal is a label in disguise: correlation with the forward 21-session return is between -0.07 and +0.13, with the forward
  63-session return between -0.13 and +0.14. Several are correlated with PAST EUR/USD returns (with the
  126-session return: `cli_d6m_diff` +0.27, `ea_tb_mom` +0.24, `brent_usd_d126` -0.21; with the 63-session return: `gasratio_d3m`
  +0.22, `tips_d63` +0.21; with the 21-session return: `tips_d21` +0.22): part of what they vote is price momentum, which rounds
  1-4 found to be worthless here. Their signs agree with each old vote 40-61 % of the time.
"""

TAIL_MD = r"""
## 10. Variants, caveats, what is worth keeping
* **Variant count: 12** candidate signals = 12 AND rules, one selection rule, one final. Not selected from: the standalone, outside,
  contradicted and shifted versions of the same 12 signals. The module was run in full five times: the first run, then re-runs that
  added diagnostics only (the outside-agreement placebo rows, the per-year table, this report); signals, candidates, the selection and
  every number of the first run are unchanged.
* Non-overlapping and weekly numbers disagree for several AND rules (`ttf_hh_d63` against its same-span baseline: weekly
  +7 / +12 / +10 points, non-overlapping -5 / +1 / -2; `brent_usd_d126` at 21 sessions: weekly +5, non-overlapping -3.7). The weekly
  grid counts one directional episode five to thirteen times; the non-overlapping stream is the one the bar is written on, and it
  says no.
* The 2023-26 cells have 5-30 non-overlapping decisions each; nothing can be read from them in either direction.
* What I would keep: (1) the cached data set (TTF, Henry Hub, TIPS and breakevens from 2003, ESI from 1980, euro-area trade from 2002)
  for later arms; (2) the negative result that real-yield and breakeven CHANGES, the CLI and sentiment differentials, trade-balance
  momentum and the monthly gas ratio do not predict 1-3 month EUR/USD direction (45-54 % on weekly decisions), which closes families
  B and C and most of A;
  (3) 6-month Brent as a known 55-58 % slow regime variable that adds nothing to the agreement rule; (4) TTF / Henry Hub as a
  forward-test note only.
"""


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        write_report()
        sys.exit(0)
    cp = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
    pos, rep, res = run_full(cp)
    pd.to_pickle({k: res[k] for k in ("V", "paired", "selection", "final", "final_status", "bar", "bar_verdict", "bar_all", "bar_verdict_all",
                                      "report", "leak", "incremental", "corr", "cat", "S", "by_year")}, RES / "logs" / f"{ARM}_tables.pkl")
    print("\nFINAL:", res["final"], "-", res["final_status"])
    print(res["selection"].round(3).to_string(index=False))
    print(res["bar"].round(3).to_string(index=False))
    print(res["bar_verdict"])
    write_report()
