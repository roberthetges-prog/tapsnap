"""Fetch and normalise non-price datasets for EUR/USD research.

Outputs go to ``eurusd/data/macro/`` as small plain CSVs with UTC / ISO-date
indexes.  Raw downloads are kept under ``eurusd/data/raw/`` and treated as
untrusted data (parsed only, never executed).

Run everything::

    python -I eurusd/src/eurusd/macro_fetch.py all

or individual steps: ``ecb``, ``yahoo``, ``mirrors``, ``cftc``, ``calendar``.
Add ``--offline`` to rebuild outputs from files already under data/raw without
hitting the network (mirrors / cftc / calendar steps only).

Sources (see data/macro/README.md for the full documentation):
* ECB Data Portal SDMX CSV API      https://data-api.ecb.europa.eu
* Yahoo Finance chart JSON          https://query1.finance.yahoo.com/v8/finance/chart/<SYM>
* FRED mirrors on GitHub            raw.githubusercontent.com (FRED itself is unreachable here)
* datahub.io "datasets" org         raw.githubusercontent.com/datasets/<repo>/master/data/...
* CFTC Commitments of Traders       https://www.cftc.gov/files/dea/history/
* ForexFactory weekly feed          https://nfs.faireconomy.media/ff_calendar_thisweek.json
* Calendar history (GitHub mirrors) see CALENDAR_SOURCES below
"""
from __future__ import annotations

import argparse
import csv
import html as html_lib
import io
import json
import re
import sys
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import numpy as np
import pandas as pd
import requests

HERE = Path(__file__).resolve()
PROJECT = HERE.parents[2]                      # .../eurusd
MACRO = PROJECT / "data" / "macro"
RAW = PROJECT / "data" / "raw"
GH = "https://raw.githubusercontent.com"

SESSION = requests.Session()
TIMEOUT = 120


def _get(url: str, retries: int = 3, backoff: float = 5.0, **kw) -> requests.Response:
    """GET with simple retry; never spoofs a browser user agent."""
    last = None
    for i in range(retries):
        try:
            r = SESSION.get(url, timeout=TIMEOUT, **kw)
            if r.status_code == 200:
                return r
            last = RuntimeError(f"HTTP {r.status_code} for {url}: {r.text[:80]!r}")
            if r.status_code in (403, 404):
                break
        except requests.RequestException as e:  # proxy / network errors
            last = e
        time.sleep(backoff * (i + 1))
    raise last  # type: ignore[misc]


def _save(df: pd.DataFrame, name: str, index: bool = False) -> Path:
    MACRO.mkdir(parents=True, exist_ok=True)
    p = MACRO / name
    df.to_csv(p, index=index, float_format="%.6g")
    n = len(df)
    first = df.iloc[0, 0] if n and not index else (df.index[0] if n else None)
    last = df.iloc[-1, 0] if n and not index else (df.index[-1] if n else None)
    print(f"  wrote {p.relative_to(PROJECT)}: {n} rows, {first} .. {last}")
    return p


# --------------------------------------------------------------------------- #
# A. ECB Data Portal
# --------------------------------------------------------------------------- #
ECB_API = "https://data-api.ecb.europa.eu/service/data/{flow}/{key}?format=csvdata"

ECB_SERIES = {
    # name: (flow, key, startPeriod or None)
    "dfr": ("FM", "D.U2.EUR.4F.KR.DFR.LEV", None),          # deposit facility rate
    "mrr": ("FM", "D.U2.EUR.4F.KR.MRR_FR.LEV", None),       # main refinancing rate (fixed rate tenders)
    "mrr_var": ("FM", "D.U2.EUR.4F.KR.MRR_MBR.LEV", None),  # MRO minimum bid rate (variable tenders 2000-2008)
    "mlfr": ("FM", "D.U2.EUR.4F.KR.MLFR.LEV", None),        # marginal lending facility rate
    "yc_2y": ("YC", "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_2Y", None),
    "yc_10y": ("YC", "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_10Y", None),
    "yc_3m": ("YC", "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_3M", None),
    "yc_1y": ("YC", "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_1Y", None),
    "yc_5y": ("YC", "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_5Y", None),
    "yc_30y": ("YC", "B.U2.EUR.4F.G_N_A.SV_C_YM.SR_30Y", None),
    "hicp_yoy": ("ICP", "M.U2.N.000000.4.ANR", "1990-01"),   # full-range request 504s at ECB; startPeriod works
    "hicp_index": ("ICP", "M.U2.N.000000.4.INX", "1990-01"),
    "hicp_core_yoy": ("ICP", "M.U2.N.XEF000.4.ANR", "1990-01"),  # ex energy & food
    "unemployment": ("LFSI", "M.I9.S.UNEHRT.TOTAL0.15_74.T", None),
    "estr": ("EST", "B.EU000A2X2A25.WT", None),             # euro short-term rate, volume-weighted trimmed mean
    "eonia": ("EON", "D.EONIA_TO.RATE", None),
}


def ecb_series(flow: str, key: str, start: str | None = None) -> pd.DataFrame:
    url = ECB_API.format(flow=flow, key=key)
    if start:
        url += f"&startPeriod={start}"
    r = _get(url, retries=4, backoff=8)
    df = pd.read_csv(io.StringIO(r.text))
    if "TIME_PERIOD" not in df.columns:
        raise RuntimeError(f"unexpected ECB payload for {flow}.{key}: {df.columns.tolist()[:5]}")
    out = df[["TIME_PERIOD", "OBS_VALUE"]].rename(columns={"TIME_PERIOD": "date", "OBS_VALUE": "value"})
    out["value"] = pd.to_numeric(out["value"], errors="coerce")
    return out.dropna(subset=["value"]).reset_index(drop=True)


def fetch_ecb() -> None:
    print("[ecb]")
    got: dict[str, pd.DataFrame] = {}
    for name, (flow, key, start) in ECB_SERIES.items():
        try:
            got[name] = ecb_series(flow, key, start)
            print(f"  {flow}.{key}: {len(got[name])} obs {got[name]['date'].iloc[0]}..{got[name]['date'].iloc[-1]}")
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED {flow}.{key}: {e}")

    def wide(names: list[str], cols: list[str]) -> pd.DataFrame:
        frames = [got[n].rename(columns={"value": c}).set_index("date") for n, c in zip(names, cols) if n in got]
        return pd.concat(frames, axis=1).sort_index().reset_index()

    # policy rates: daily levels; MRO was a minimum-bid rate for variable tenders 2000-06..2008-10
    pr = wide(["dfr", "mrr", "mrr_var", "mlfr"],
              ["deposit_facility_rate", "mro_fixed_rate", "mro_min_bid_rate", "marginal_lending_rate"])
    pr["main_refinancing_rate"] = pr["mro_fixed_rate"].combine_first(pr.get("mro_min_bid_rate"))
    _save(pr[["date", "deposit_facility_rate", "main_refinancing_rate", "marginal_lending_rate",
              "mro_fixed_rate", "mro_min_bid_rate"]], "ecb_policy_rates.csv")

    yc = wide(["yc_3m", "yc_1y", "yc_2y", "yc_5y", "yc_10y", "yc_30y"],
              ["aaa_spot_3m", "aaa_spot_1y", "aaa_spot_2y", "aaa_spot_5y", "aaa_spot_10y", "aaa_spot_30y"])
    _save(yc, "ea_aaa_yield_curve.csv")

    hicp = wide(["hicp_yoy", "hicp_core_yoy", "hicp_index"], ["hicp_yoy", "hicp_core_yoy", "hicp_index"])
    _save(hicp.rename(columns={"date": "month"}), "ea_hicp.csv")

    if "unemployment" in got:
        _save(got["unemployment"].rename(columns={"date": "month", "value": "unemployment_rate"}), "ea_unemployment.csv")
    on = wide(["eonia", "estr"], ["eonia", "estr"])
    _save(on, "ea_overnight_rates.csv")


# --------------------------------------------------------------------------- #
# B. Yahoo Finance
# --------------------------------------------------------------------------- #
YAHOO_DAILY = ["^IRX", "^FVX", "^TNX", "^TYX", "DX-Y.NYB", "6E=F", "ZT=F", "GC=F", "CL=F", "^GSPC", "^VIX",
               "^STOXX50E", "^GDAXI", "EURJPY=X", "EURGBP=X", "GBPUSD=X", "USDJPY=X", "USDCHF=X", "AUDUSD=X",
               "EURCHF=X", "BTC-USD"]
YAHOO_HOURLY = ["DX-Y.NYB", "6E=F", "^GSPC", "GC=F", "EURGBP=X", "USDJPY=X"]
YAHOO_URL = "https://query{n}.finance.yahoo.com/v8/finance/chart/{sym}?range={rng}&interval={iv}"


def yahoo_chart(symbol: str, rng: str = "max", interval: str = "1d") -> tuple[pd.DataFrame, dict]:
    from urllib.parse import quote
    last: Exception | None = None
    for attempt in range(6):
        for n in (1, 2):
            url = YAHOO_URL.format(n=n, sym=quote(symbol, safe=""), rng=rng, iv=interval)
            try:
                r = SESSION.get(url, timeout=TIMEOUT)
            except requests.RequestException as e:
                last = e
                continue
            if r.status_code == 200:
                res = r.json()["chart"]["result"][0]
                q = res["indicators"]["quote"][0]
                ts = pd.to_datetime(res["timestamp"], unit="s", utc=True)
                df = pd.DataFrame({"open": q.get("open"), "high": q.get("high"), "low": q.get("low"),
                                   "close": q.get("close"), "volume": q.get("volume")}, index=ts)
                df.index.name = "datetime_utc" if interval != "1d" else "date_utc"
                df = df.dropna(subset=["close"])
                return df, res["meta"]
            last = RuntimeError(f"HTTP {r.status_code}: {r.text[:60]!r}")
            if r.status_code != 429:
                break
        time.sleep(15 * (attempt + 1))
    raise last  # type: ignore[misc]


def _yname(symbol: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "_", symbol).strip("_").lower()


def fetch_yahoo(daily: bool = True, hourly: bool = True) -> dict:
    print("[yahoo]")
    status: dict[str, str] = {}
    jobs = ([(s, "max", "1d") for s in YAHOO_DAILY] if daily else []) + \
           ([(s, "730d", "1h") for s in YAHOO_HOURLY] if hourly else [])
    for sym, rng, iv in jobs:
        name = f"yahoo_{_yname(sym)}_{'daily' if iv == '1d' else iv}.csv"
        try:
            df, meta = yahoo_chart(sym, rng, iv)
            if iv == "1d":
                # daily bars: Yahoo stamps them at the exchange's session open; keep the calendar date (exchange tz)
                tz = meta.get("exchangeTimezoneName", "UTC")
                df.index = df.index.tz_convert(tz).normalize().tz_localize(None)
                df.index.name = "date"
                df = df[~df.index.duplicated(keep="last")]
            else:
                df.index = df.index.strftime("%Y-%m-%dT%H:%M:%SZ")
            _save(df.reset_index(), name)
            status[sym + " " + iv] = f"ok ({meta.get('exchangeTimezoneName')}, {meta.get('currency')})"
            time.sleep(2)
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED {sym} {iv}: {e}")
            status[sym + " " + iv] = f"FAILED: {e}"
    (MACRO / "yahoo_status.json").write_text(json.dumps(status, indent=1))
    return status


# --------------------------------------------------------------------------- #
# C. GitHub mirrors of FRED and datahub.io
# --------------------------------------------------------------------------- #
# FRED mirrors.  Repos verified 2026-11-10; "pushed" = repo last push, data end dates recorded in README.
ECONDASH = GH + "/mfenickfau/econ-dashboards/main/data/{s}.csv"           # pushed 2026-11-06, cols date,value
INVDASH = GH + "/cool1990/invest-dashboard_v1/main/data/series/{s}.csv"    # pushed 2026-11-10, cols date,value (2022+)
FEDJEV = GH + "/maybern-tripp-smith/fedjev-bench/main/data/raw/fred/{s}.csv"  # pushed 2026-09-21, cols observation_date,<S>

FRED_MIRRORS = {
    # series: (url template, description, frequency)
    "DGS2": (ECONDASH, "US Treasury 2y constant maturity yield, %", "daily"),
    "DGS10": (ECONDASH, "US Treasury 10y constant maturity yield, %", "daily"),
    "DGS30": (ECONDASH, "US Treasury 30y constant maturity yield, %", "daily"),
    "T10Y2Y": (ECONDASH, "10y minus 2y Treasury spread, pp", "daily"),
    "T10Y3M": (ECONDASH, "10y minus 3m Treasury spread, pp", "daily"),
    "FEDFUNDS": (ECONDASH, "Effective fed funds rate, monthly avg %", "monthly"),
    "DTWEXBGS": (ECONDASH, "Nominal broad USD index (Jan2006=100)", "daily"),
    "CPIAUCSL": (ECONDASH, "US CPI all items SA, index 1982-84=100", "monthly"),
    "CPILFESL": (ECONDASH, "US core CPI SA, index", "monthly"),
    "PCEPI": (ECONDASH, "US PCE price index SA", "monthly"),
    "PCEPILFE": (ECONDASH, "US core PCE price index SA", "monthly"),
    "PAYEMS": (ECONDASH, "US nonfarm payrolls SA, thousands", "monthly"),
    "UNRATE": (ECONDASH, "US unemployment rate SA, %", "monthly"),
    "ICSA": (ECONDASH, "US initial jobless claims SA, persons", "weekly"),
    "CES0500000003": (ECONDASH, "US avg hourly earnings, private, $", "monthly"),
    "JTSJOL": (ECONDASH, "US job openings (JOLTS), thousands", "monthly"),
    "INDPRO": (ECONDASH, "US industrial production index", "monthly"),
    "RSAFS": (ECONDASH, "US retail sales SA, $mn", "monthly"),
    "HOUST": (ECONDASH, "US housing starts SAAR, thousands", "monthly"),
    "GDPC1": (ECONDASH, "US real GDP SAAR, $bn 2017", "quarterly"),
    "M2SL": (ECONDASH, "US M2 money stock SA, $bn", "monthly"),
    "BOPGSTB": (ECONDASH, "US trade balance goods&services SA, $mn", "monthly"),
    "MORTGAGE30US": (ECONDASH, "US 30y fixed mortgage rate, %", "weekly"),
    "VIXCLS": (ECONDASH, "CBOE VIX close", "daily"),
    "SP500": (ECONDASH, "S&P 500 close (FRED, last 10y only)", "daily"),
    "NASDAQCOM": (ECONDASH, "NASDAQ Composite close", "daily"),
    "GASREGW": (ECONDASH, "US regular gasoline price, $/gal", "weekly"),
    "PPIACO": (ECONDASH, "US PPI all commodities", "monthly"),
    "SAHMREALTIME": (ECONDASH, "Sahm rule recession indicator, pp", "monthly"),
    "CP0000EZ19M086NEST": (ECONDASH, "Euro area HICP all items, index 2015=100 (FRED copy)", "monthly"),
    "LRHUTTTTDEM156S": (ECONDASH, "Germany harmonised unemployment rate, %", "monthly"),
    "EFFR": (INVDASH, "Effective fed funds rate, daily %", "daily"),
    "SOFR": (INVDASH, "SOFR, daily %", "daily"),
    "IORB": (INVDASH, "Interest on reserve balances, %", "daily"),
    "T10YIE": (INVDASH, "10y breakeven inflation, %", "daily"),
    "DFII10": (INVDASH, "10y TIPS real yield, %", "daily"),
    "BAMLH0A0HYM2": (INVDASH, "ICE BofA US HY OAS, %", "daily"),
    "WALCL": (INVDASH, "Fed total assets, $mn", "weekly"),
    "RRPONTSYD": (INVDASH, "Fed overnight reverse repo usage, $bn", "daily"),
    "WRESBAL": (INVDASH, "Reserve balances with Fed banks, $mn", "weekly"),
    "STLFSI4": (INVDASH, "St Louis Fed financial stress index", "weekly"),
    "ANFCI": (INVDASH, "Chicago Fed adjusted NFCI", "weekly"),
    "NFCI": (FEDJEV, "Chicago Fed NFCI", "weekly"),
    "DFEDTAR": (FEDJEV, "Fed funds target rate (single, to 2008-12-15), %", "daily"),
    "DFEDTARL": (FEDJEV, "Fed funds target range lower bound, %", "daily"),
    "DFEDTARU": (FEDJEV, "Fed funds target range upper bound, %", "daily"),
}

DATAHUB = GH + "/datasets/{repo}/master/{path}"   # NB: raw serves 'master'; 'main' 404s for these repos
DATAHUB_FILES = {
    # out name: (repo, path, description, frequency)
    "datahub_brent_daily.csv": ("oil-prices", "data/brent-daily.csv", "Brent crude spot $/bbl (EIA)", "daily"),
    "datahub_wti_daily.csv": ("oil-prices", "data/wti-daily.csv", "WTI crude spot $/bbl (EIA)", "daily"),
    "datahub_vix_daily.csv": ("finance-vix", "data/vix-daily.csv", "CBOE VIX OHLC", "daily"),
    "datahub_gold_monthly.csv": ("gold-prices", "data/monthly.csv", "Gold price $/oz monthly avg (LBMA)", "monthly"),
    "datahub_euribor_1w.csv": ("euribor", "data/euribor-1w-weekly.csv", "Euribor 1-week, %", "monthly obs"),
    "datahub_euribor_3m.csv": ("euribor", "data/euribor-3m-monthly.csv", "Euribor 3-month, %", "monthly"),
    "datahub_euribor_12m.csv": ("euribor", "data/euribor-12m-monthly.csv", "Euribor 12-month, %", "monthly"),
    "datahub_us10y_monthly.csv": ("bond-yields-us-10y", "data/monthly.csv", "US 10y yield monthly (Fed H.15)", "monthly"),
    "datahub_cpi_us.csv": ("cpi-us", "data/cpiai.csv", "US CPI index & m/m inflation", "monthly"),
    "datahub_fx_fed_h10_daily.csv": ("exchange-rates", "data/daily.csv", "Fed H.10 daily FX rates, all countries", "daily"),
}


def _norm_fred(text: str, series: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(text))
    df.columns = [c.strip() for c in df.columns]
    dcol = "date" if "date" in df.columns else ("observation_date" if "observation_date" in df.columns else df.columns[0])
    vcol = "value" if "value" in df.columns else (series if series in df.columns else df.columns[1])
    out = pd.DataFrame({"date": pd.to_datetime(df[dcol]).dt.strftime("%Y-%m-%d"),
                        "value": pd.to_numeric(df[vcol], errors="coerce")})
    return out.dropna().reset_index(drop=True)


def fetch_mirrors(offline: bool = False) -> None:
    print("[mirrors]")
    rawdir = RAW / "fred_mirror"
    rawdir.mkdir(parents=True, exist_ok=True)
    meta_rows = []
    for s, (tpl, desc, freq) in FRED_MIRRORS.items():
        url = tpl.format(s=s)
        src = {ECONDASH: "econdash", INVDASH: "invdash", FEDJEV: "fedjev"}[tpl]
        rawp = rawdir / f"{src}_{s}.csv"
        try:
            if not offline:
                rawp.write_text(_get(url).text)
            df = _norm_fred(rawp.read_text(), s)
            _save(df, f"fred_{s}.csv")
            meta_rows.append({"series": s, "description": desc, "frequency": freq, "mirror_url": url,
                              "rows": len(df), "first": df["date"].iloc[0], "last": df["date"].iloc[-1]})
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED {s}: {e}")
            meta_rows.append({"series": s, "description": desc, "frequency": freq, "mirror_url": url, "rows": 0,
                              "first": "", "last": f"FAILED: {e}"})
    pd.DataFrame(meta_rows).to_csv(MACRO / "fred_mirror_catalog.csv", index=False)

    hubdir = RAW / "datahub"
    hubdir.mkdir(parents=True, exist_ok=True)
    for out, (repo, path, desc, freq) in DATAHUB_FILES.items():
        url = DATAHUB.format(repo=repo, path=path)
        rawp = hubdir / f"{repo}_{path.replace('/', '_')}"
        try:
            if not offline:
                rawp.write_text(_get(url).text)
            df = pd.read_csv(rawp)
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
            if out == "datahub_fx_fed_h10_daily.csv":
                # keep only the majors relevant to EUR/USD cross-checks; one column per currency
                keep = {"Euro": "eur_per_usd_inverse", "United Kingdom": "gbp", "Japan": "jpy", "Switzerland": "chf",
                        "Canada": "cad", "Australia": "aud"}
                df = df[df["country"].isin(keep)].pivot(index="date", columns="country", values="exchange_rate")
                df = df.rename(columns=keep).reset_index()
            _save(df, out)
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED {out}: {e}")


# --------------------------------------------------------------------------- #
# D. CFTC Commitments of Traders, EURO FX (CME), code 099741
# --------------------------------------------------------------------------- #
CFTC_TFF = "https://www.cftc.gov/files/dea/history/fut_fin_txt_{y}.zip"      # Traders in Financial Futures, 2010+
CFTC_LEGACY = "https://www.cftc.gov/files/dea/history/deacot{y}.zip"          # legacy futures-only, 1986+
EUROFX_CODE = "099741"


def download_cftc(years_tff=range(2010, 2027), years_legacy=range(1999, 2027)) -> None:
    d = RAW / "cftc"
    d.mkdir(parents=True, exist_ok=True)
    for name, url in [(f"fut_fin_txt_{y}.zip", CFTC_TFF.format(y=y)) for y in years_tff] + \
                     [(f"deacot{y}.zip", CFTC_LEGACY.format(y=y)) for y in years_legacy]:
        p = d / name
        if p.exists() and p.stat().st_size > 1000:
            continue
        r = _get(url)
        if r.content[:2] != b"PK":
            print(f"  not a zip: {name}")
            continue
        p.write_bytes(r.content)
        print(f"  downloaded {name} ({len(r.content)} bytes)")
        time.sleep(1)


def _read_cot_zip(p: Path) -> pd.DataFrame:
    with zipfile.ZipFile(p) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".txt")]
        with z.open(names[0]) as fh:
            df = pd.read_csv(fh, dtype=str, low_memory=False, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    return df


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.strip().str.replace(",", ""), errors="coerce")


def build_cftc() -> None:
    print("[cftc]")
    d = RAW / "cftc"
    # --- TFF
    tff = []
    for p in sorted(d.glob("fut_fin_txt_*.zip")):
        df = _read_cot_zip(p)
        df = df[df["CFTC_Contract_Market_Code"].str.strip() == EUROFX_CODE]
        tff.append(df)
    t = pd.concat(tff, ignore_index=True)
    assert t["Market_and_Exchange_Names"].str.strip().eq("EURO FX - CHICAGO MERCANTILE EXCHANGE").all()
    cols = {"Open_Interest_All": "open_interest",
            "Dealer_Positions_Long_All": "dealer_long", "Dealer_Positions_Short_All": "dealer_short",
            "Asset_Mgr_Positions_Long_All": "asset_mgr_long", "Asset_Mgr_Positions_Short_All": "asset_mgr_short",
            "Lev_Money_Positions_Long_All": "lev_funds_long", "Lev_Money_Positions_Short_All": "lev_funds_short",
            "Other_Rept_Positions_Long_All": "other_rept_long", "Other_Rept_Positions_Short_All": "other_rept_short",
            "NonRept_Positions_Long_All": "nonrept_long", "NonRept_Positions_Short_All": "nonrept_short",
            "Traders_Tot_All": "traders_total"}
    out = pd.DataFrame({"report_date": pd.to_datetime(t["Report_Date_as_YYYY-MM-DD"]).dt.strftime("%Y-%m-%d")})
    for a, b in cols.items():
        out[b] = _num(t[a])
    for g in ["dealer", "asset_mgr", "lev_funds", "other_rept", "nonrept"]:
        out[f"{g}_net"] = out[f"{g}_long"] - out[f"{g}_short"]
        out[f"{g}_net_pct_oi"] = (100 * out[f"{g}_net"] / out["open_interest"]).round(2)
    out = out.sort_values("report_date").drop_duplicates("report_date").reset_index(drop=True)
    _save(out, "cot_eurofx_tff.csv")

    # --- legacy futures-only (non-commercial / commercial)
    leg = []
    for p in sorted(d.glob("deacot*.zip")):
        df = _read_cot_zip(p)
        code_col = next(c for c in df.columns if "Contract Market Code" in c)
        df = df[df[code_col].astype(str).str.strip() == EUROFX_CODE]
        leg.append(df)
    l = pd.concat(leg, ignore_index=True)
    name_col = next(c for c in l.columns if "Market and Exchange" in c)
    assert l[name_col].str.strip().eq("EURO FX - CHICAGO MERCANTILE EXCHANGE").all()
    date_col = next(c for c in l.columns if "YYYY-MM-DD" in c)

    def col(prefix: str) -> str:
        return next(c for c in l.columns if c.strip().startswith(prefix))

    out = pd.DataFrame({"report_date": pd.to_datetime(l[date_col].str.strip()).dt.strftime("%Y-%m-%d")})
    out["open_interest"] = _num(l[col("Open Interest (All)")])
    out["noncomm_long"] = _num(l[col("Noncommercial Positions-Long (All)")])
    out["noncomm_short"] = _num(l[col("Noncommercial Positions-Short (All)")])
    out["noncomm_spread"] = _num(l[col("Noncommercial Positions-Spreading (All)")])
    out["comm_long"] = _num(l[col("Commercial Positions-Long (All)")])
    out["comm_short"] = _num(l[col("Commercial Positions-Short (All)")])
    out["nonrept_long"] = _num(l[col("Nonreportable Positions-Long (All)")])
    out["nonrept_short"] = _num(l[col("Nonreportable Positions-Short (All)")])
    for g in ["noncomm", "comm", "nonrept"]:
        out[f"{g}_net"] = out[f"{g}_long"] - out[f"{g}_short"]
        out[f"{g}_net_pct_oi"] = (100 * out[f"{g}_net"] / out["open_interest"]).round(2)
    out = out.sort_values("report_date").drop_duplicates("report_date").reset_index(drop=True)
    _save(out, "cot_eurofx_legacy.csv")


# --------------------------------------------------------------------------- #
# E. Economic calendar
# --------------------------------------------------------------------------- #
FF_FEED = "https://nfs.faireconomy.media/ff_calendar_{w}.json"

CALENDAR_SOURCES = {
    # local raw name: (url, note)
    "pinna_fomc_calendar_verified.csv": (
        GH + "/francescopinna03/Monetary_surprises_and_volatility/main/Raw/Certification/fomc_calendar_verified.csv",
        "FOMC statement release times (UTC) 2008-12..2026-03, hand-verified against Fed pages"),
    "pinna_ecb_calendar_verified_v2.csv": (
        GH + "/francescopinna03/Monetary_surprises_and_volatility/main/Raw/Certification/ecb_calendar_verified_v2.csv",
        "ECB press release (PR) / press conference (PC) UTC times 2000..2012, hand-verified"),
    "pinna_event_registry_snapshot.csv": (
        GH + "/francescopinna03/Monetary_surprises_and_volatility/main/Raw/Certification/final_analysis_event_registry_snapshot.csv",
        "ECB PR/PC UTC anchors 2013-01..2026-03 (same author's event registry)"),
    "yildirim_fed_mpd.csv": (
        GH + "/yildirimalper/yildirim-masters-thesis/main/processed_data/monetary_policy_dates/fed_mpd.csv",
        "FOMC meeting dates 1989..2024 (Hillenbrand 2021 + Fed calendar), dates only"),
    "yildirim_ecb_mpd.csv": (
        GH + "/yildirimalper/yildirim-masters-thesis/main/processed_data/monetary_policy_dates/ecb_mpd.csv",
        "ECB monetary policy decision dates 1999..2024, dates only"),
    "fedjev_meetings.csv": (
        GH + "/maybern-tripp-smith/fedjev-bench/main/data/clean/meetings.csv",
        "FOMC meetings 2011..2026-09 with statement URL, scheduled flag, SEP flag, chair"),
    "aansensei_fomc_meetings.csv": (
        GH + "/aansensei/macro-event-lab/main/pipeline/src/macro_event_lab/seeds/fomc_meetings.csv",
        "FOMC statement dates 2021..2027 incl. tentative future meetings"),
    "gcmbo_events_bls.csv": (
        GH + "/Vrushabh43/GC-MBO-ML/main/data/calendar/events_bls.csv",
        "BLS Employment Situation / CPI / PPI release UTC times 2017..2026 from archived bls.gov schedules"),
    "gcmbo_events_fomc.csv": (
        GH + "/Vrushabh43/GC-MBO-ML/main/data/calendar/events_fomc.csv",
        "FOMC statement UTC times 2017..2026-12 (14:00 ET rule applied to Fed calendar dates)"),
}
SPOLUAN = GH + "/spoluan/forex-factory-scraper/master/datasets/forex_factory_calendar_{y}.csv"   # 2010..2023
FXDESK = GH + "/datpro12345/fx-desk/main/data/bronze/landing/calendar_events/2026_{m:02d}.csv"   # 2026-01..09
CWT_RAW = GH + "/Gourav232003/cwt-macro-pipeline/main/data/raw/{f}.json"
CWT_FILES = ["ff_2026-04-10_2026-04-16", "ff_2026-04-10_2026-05-09", "ff_2026-04-17_2026-04-23", "ff_2026-04-24_2026-04-30",
             "ff_2026-05-08_2026-05-14", "ff_2026-05-10_2026-06-08", "ff_2026-05-15_2026-05-21", "ff_2026-05-22_2026-05-28",
             "ff_2026-06-05_2026-06-11", "ff_2026-06-09_2026-07-08", "ff_2026-06-19_2026-06-25", "ff_2026-06-26_2026-07-02",
             "ff_2026-07-03_2026-07-09", "ff_2026-07-09_2026-08-07", "ff_2026-07-10_2026-07-16", "ff_2026-07-12_2026-07-18",
             "ff_2026-07-24_2026-07-30", "ff_2026-07-31_2026-08-06", "ff_2026-08-07_2026-08-13", "ff_2026-08-08_2026-09-06",
             "ff_2026-08-14_2026-08-20", "ff_2026-08-21_2026-08-27", "ff_2026-08-28_2026-09-03", "ff_2026-09-04_2026-09-10",
             "ff_2026-09-07_2026-09-13", "ff_2026-09-11_2026-09-17", "ff_2026-09-16_2026-09-25", "ff_2026-09-28_2026-10-04",
             "ff_2026-10-02_2026-10-07", "ff_2026-10-07_2026-10-07"]
CRYPTOPRISM = GH + "/CryptoPrism-io/ForexFactory-Calendar-Scraper/main/Economic_Calendar_FF_export_20251109_012607.csv"
WIKI_FOMC = "https://en.wikipedia.org/wiki/History_of_Federal_Open_Market_Committee_actions"

ET = ZoneInfo("America/New_York")
EVENT_COLS = ["datetime_utc", "currency", "event", "impact", "actual", "forecast", "previous", "source"]


def download_calendar() -> None:
    (RAW / "ff").mkdir(parents=True, exist_ok=True)
    for w in ("thisweek", "nextweek", "lastweek"):
        try:
            r = _get(FF_FEED.format(w=w), retries=1)
            (RAW / "ff" / f"ff_calendar_{w}.json").write_text(r.text)
            print(f"  ff_calendar_{w}.json ok")
        except Exception as e:  # noqa: BLE001
            print(f"  ff_calendar_{w}.json unavailable: {e}")
    cal = RAW / "calendar_github"
    cal.mkdir(exist_ok=True)
    for name, (url, _) in CALENDAR_SOURCES.items():
        try:
            (cal / name).write_text(_get(url).text)
        except Exception as e:  # noqa: BLE001
            print(f"  FAILED {name}: {e}")
    ffh = RAW / "ff_history"
    ffh.mkdir(exist_ok=True)
    for y in range(2010, 2024):
        p = ffh / f"spoluan_ff_{y}.csv"
        if not p.exists():
            p.write_text(_get(SPOLUAN.format(y=y)).text)
    for m in range(1, 10):
        p = ffh / f"fxdesk_2026_{m:02d}.csv"
        if not p.exists():
            p.write_text(_get(FXDESK.format(m=m)).text)
    (ffh / "cwt_raw").mkdir(exist_ok=True)
    for f in CWT_FILES:
        p = ffh / "cwt_raw" / f"{f}.json"
        if not p.exists():
            p.write_text(_get(CWT_RAW.format(f=f)).text)
    p = ffh / "cryptoprism_ff_export_20251109.csv"
    if not p.exists():
        p.write_text(_get(CRYPTOPRISM).text)
    (RAW / "wikipedia").mkdir(exist_ok=True)
    try:
        (RAW / "wikipedia" / "History_of_Federal_Open_Market_Committee_actions.html").write_text(_get(WIKI_FOMC).text)
    except Exception as e:  # noqa: BLE001
        print(f"  wikipedia unavailable: {e}")


def _parse_wiki_fomc() -> pd.DataFrame:
    p = RAW / "wikipedia" / "History_of_Federal_Open_Market_Committee_actions.html"
    s = p.read_text(encoding="utf-8", errors="replace")
    tables = re.findall(r"<table[^>]*wikitable.*?</table>", s, re.S)
    rows = []
    for t in tables:
        for r in re.findall(r"<tr.*?</tr>", t, re.S):
            cells = [html_lib.unescape(re.sub(r"<[^>]+>", "", c)).strip()
                     for c in re.findall(r"<t[hd][^>]*>(.*?)</t[hd]>", r, re.S)]
            if len(cells) >= 3 and re.match(r"^[A-Z][a-z]+ \d{1,2}, \d{4}$", cells[0]):
                try:
                    d = datetime.strptime(cells[0], "%B %d, %Y").date()
                except ValueError:
                    continue
                rows.append({"date": d.isoformat(), "fed_funds_target": cells[1], "discount_rate": cells[2],
                             "votes": cells[3] if len(cells) > 3 else "",
                             "note": re.sub(r"\s+", " ", cells[4])[:200] if len(cells) > 4 else ""})
    df = pd.DataFrame(rows).drop_duplicates("date").sort_values("date").reset_index(drop=True)
    return df


def build_fomc() -> pd.DataFrame:
    cal = RAW / "calendar_github"
    ver = pd.read_csv(cal / "pinna_fomc_calendar_verified.csv")
    ver = ver[ver["decision"].str.startswith("include")]
    ver = ver[["event_date", "release_utc", "time_source"]].rename(columns={"event_date": "date"})
    ver["release_utc"] = pd.to_datetime(ver["release_utc"], utc=True)
    ver["time_quality"] = "verified:" + ver["time_source"].astype(str)
    ver = ver.drop(columns="time_source")

    mpd = pd.read_csv(cal / "yildirim_fed_mpd.csv", header=None)[0].astype(str).str.strip()
    mpd = pd.DataFrame({"date": pd.to_datetime(mpd, errors="coerce").dt.strftime("%Y-%m-%d")}).dropna()
    mpd["in_hillenbrand_meeting_list"] = True

    fj = pd.read_csv(cal / "fedjev_meetings.csv")
    fj = fj.rename(columns={"is_scheduled": "scheduled", "is_sep": "has_sep"})[["date", "scheduled", "has_sep", "chair"]]

    seed = pd.read_csv(cal / "aansensei_fomc_meetings.csv").rename(columns={"statement_date": "date"})
    seed["scheduled"] = seed["meeting_type"].eq("scheduled_meeting")
    seed = seed[["date", "scheduled", "has_sep", "status"]]

    gc = pd.read_csv(cal / "gcmbo_events_fomc.csv")
    gc = pd.DataFrame({"date": gc["ts_utc"].str[:10], "release_utc_rule": pd.to_datetime(gc["ts_utc"], utc=True)})

    wiki = _parse_wiki_fomc()

    dates = sorted(set(ver["date"]) | set(mpd["date"]) | set(fj["date"]) | set(seed["date"]) | set(gc["date"]) | set(wiki["date"]))
    out = pd.DataFrame({"date": dates})
    out = out.merge(ver, on="date", how="left").merge(mpd, on="date", how="left")
    out = out.merge(fj, on="date", how="left", suffixes=("", "_fj"))
    out = out.merge(seed, on="date", how="left", suffixes=("", "_seed"))
    out["scheduled"] = out["scheduled"].combine_first(out["scheduled_seed"])
    out["has_sep"] = out["has_sep"].combine_first(out["has_sep_seed"])
    out = out.merge(gc, on="date", how="left").merge(wiki, on="date", how="left")
    # scheduled flag: from fedjev/seed if present, else membership in the Hillenbrand scheduled-meeting list
    out["scheduled"] = out["scheduled"].where(out["scheduled"].notna(), out["in_hillenbrand_meeting_list"].fillna(False))
    out["status"] = out["status"].fillna("held")
    # Fill missing release times by rule: 14:00 ET from 2013-03 on (Fed release of 13 Mar 2013); 14:15 ET for
    # 1994..2013-01 regular meetings (press-conference meetings Apr 2011..Jan 2013 were 12:30 ET, covered by `ver`).
    d = pd.to_datetime(out["date"])
    rule_time = np.where(d >= pd.Timestamp("2013-03-01"), "14:00", "14:15")
    rule_utc = [datetime.combine(dd.date(), datetime.strptime(tt, "%H:%M").time(), ET).astimezone(timezone.utc)
                for dd, tt in zip(d, rule_time)]
    out["statement_utc"] = out["release_utc"].combine_first(out["release_utc_rule"]).combine_first(pd.Series(rule_utc, index=out.index))
    out["time_quality"] = out["time_quality"].fillna(np.where(out["release_utc_rule"].notna(), "rule:14:00ET(gcmbo)", "rule:" + pd.Series(rule_time, index=out.index) + "ET"))
    out["statement_utc"] = pd.to_datetime(out["statement_utc"], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    out["in_wikipedia_actions_table"] = out["fed_funds_target"].notna()
    cols = ["date", "statement_utc", "time_quality", "scheduled", "has_sep", "status", "chair", "fed_funds_target",
            "discount_rate", "votes", "in_hillenbrand_meeting_list", "in_wikipedia_actions_table", "note"]
    out = out[cols].sort_values("date").reset_index(drop=True)
    return _finish(out)


def _finish(df: pd.DataFrame) -> pd.DataFrame:
    for c in df.columns:
        if df[c].dtype == object:
            df[c] = df[c].fillna("")
    return df


def build_ecb() -> pd.DataFrame:
    cal = RAW / "calendar_github"
    v = pd.read_csv(cal / "pinna_ecb_calendar_verified_v2.csv")
    v = v[v["verification_status"].eq("verified") & v["actual_phase_present"].astype(str).str.lower().eq("true")]
    v = v[["event_date", "phase", "event_datetime_utc"]].assign(time_quality="verified(pinna)")
    reg = pd.read_csv(cal / "pinna_event_registry_snapshot.csv")
    reg = reg[reg["event_id"].str.startswith("ECB_")][["trade_date", "phase", "phase_anchor_utc"]]
    reg = reg.rename(columns={"trade_date": "event_date", "phase_anchor_utc": "event_datetime_utc"}).drop_duplicates(["event_date", "phase"])
    reg["time_quality"] = "registry(pinna)"
    both = pd.concat([v, reg]).drop_duplicates(["event_date", "phase"], keep="first")
    wide = both.pivot(index="event_date", columns="phase", values="event_datetime_utc").reset_index()
    wide = wide.rename(columns={"event_date": "date", "PR": "decision_utc", "PC": "press_conference_utc"})
    q = both.drop_duplicates("event_date")[["event_date", "time_quality"]].rename(columns={"event_date": "date"})
    wide = wide.merge(q, on="date", how="left")

    mpd = pd.read_csv(cal / "yildirim_ecb_mpd.csv", header=None)[0].astype(str).str.strip()
    mpd = pd.DataFrame({"date": pd.to_datetime(mpd, format="%d %B %Y", errors="coerce").dt.strftime("%Y-%m-%d")}).dropna()
    mpd["in_ecb_decision_list_1999_2024"] = True
    out = pd.DataFrame({"date": sorted(set(wide["date"]) | set(mpd["date"]))})
    out = out.merge(wide, on="date", how="left").merge(mpd, on="date", how="left")

    # rule-derived times for dates lacking a verified time: 13:45 CET decision / 14:30 CET press conference until
    # 2022-07-21; 14:15 / 14:45 CET from 2022-07-21 (ECB moved the release time at the July 2022 meeting).
    cet = ZoneInfo("Europe/Berlin")
    d = pd.to_datetime(out["date"])
    late = d >= pd.Timestamp("2022-07-21")
    pr = [datetime.combine(dd.date(), datetime.strptime("14:15" if l else "13:45", "%H:%M").time(), cet).astimezone(timezone.utc) for dd, l in zip(d, late)]
    pc = [datetime.combine(dd.date(), datetime.strptime("14:45" if l else "14:30", "%H:%M").time(), cet).astimezone(timezone.utc) for dd, l in zip(d, late)]
    out["decision_utc"] = pd.to_datetime(out["decision_utc"], utc=True).combine_first(pd.Series(pr, index=out.index))
    out["press_conference_utc"] = pd.to_datetime(out["press_conference_utc"], utc=True).combine_first(pd.Series(pc, index=out.index))
    out["time_quality"] = out["time_quality"].fillna("rule:13:45/14:30CET(14:15/14:45 from 2022-07)")
    for c in ("decision_utc", "press_conference_utc"):
        out[c] = pd.to_datetime(out[c], utc=True).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    # attach policy-rate levels from the ECB API output if available
    pr_path = MACRO / "ecb_policy_rates.csv"
    if pr_path.exists():
        rates = pd.read_csv(pr_path)[["date", "deposit_facility_rate", "main_refinancing_rate"]]
        rates["date"] = pd.to_datetime(rates["date"])
        out = out.sort_values("date")
        out["_d"] = pd.to_datetime(out["date"]) + pd.Timedelta(days=7)   # level a week after the meeting = new rate
        out = pd.merge_asof(out, rates.rename(columns={"date": "_d"}).sort_values("_d"), on="_d", direction="backward").drop(columns="_d")
        out = out.rename(columns={"deposit_facility_rate": "dfr_after", "main_refinancing_rate": "mrr_after"})
    return _finish(out.sort_values("date").reset_index(drop=True))


def build_us_releases() -> pd.DataFrame:
    cal = RAW / "calendar_github"
    g = pd.read_csv(cal / "gcmbo_events_bls.csv")
    g = pd.DataFrame({"release_utc": pd.to_datetime(g["ts_utc"], utc=True), "release": g["name"].str.replace(" (NFP)", "", regex=False),
                      "source": "bls.gov schedule pages via web.archive.org (GC-MBO-ML mirror)", "time_quality": "verified(bls schedule archive)"})
    # extend backwards (2010..2016) from the ForexFactory archive, 8:30 ET rows for NFP and CPI
    ff = _load_spoluan()
    m = ff[(ff["currency"] == "USD") & ff["event"].isin(["Non-Farm Employment Change", "CPI m/m", "PPI m/m"])]
    m = m[m["datetime_utc"] < g["release_utc"].min()]
    m = pd.DataFrame({"release_utc": m["datetime_utc"],
                      "release": m["event"].map({"Non-Farm Employment Change": "Employment Situation", "CPI m/m": "CPI", "PPI m/m": "PPI"}),
                      "source": "ForexFactory archive (spoluan mirror), time converted from UTC+8 display zone",
                      "time_quality": "ff-archive(unverified)"})
    out = pd.concat([m, g]).sort_values(["release_utc", "release"]).drop_duplicates(["release", "release_utc"])
    out["release_utc"] = out["release_utc"].dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return out.reset_index(drop=True)


_SPOLUAN_CACHE: pd.DataFrame | None = None


def _load_spoluan() -> pd.DataFrame:
    """ForexFactory calendar 2010..2023 scraped with the site in a fixed UTC+8 display zone.

    Evidence: US NFP (08:30 ET) shows as 8:30pm in US summer (12:30 UTC) and 9:30pm in US winter (13:30 UTC),
    i.e. a constant +8h offset with no DST, so datetime_utc = displayed local time - 8h."""
    global _SPOLUAN_CACHE
    if _SPOLUAN_CACHE is not None:
        return _SPOLUAN_CACHE
    frames = []
    for p in sorted((RAW / "ff_history").glob("spoluan_ff_*.csv")):
        year = int(p.stem[-4:])
        df = pd.read_csv(p, dtype=str)
        df.columns = [c.strip().lower() for c in df.columns]
        # some leap-day rows carry 'Wed Feb 29' instead of an ISO date
        d = pd.to_datetime(df["date"], format="%Y-%m-%d", errors="coerce")
        bad = d.isna()
        if bad.any():
            d[bad] = pd.to_datetime(df.loc[bad, "date"].str[-6:] + f" {year}", format="%b %d %Y", errors="coerce")
        t = pd.to_datetime(df["time"].str.strip(), format="%I:%M%p", errors="coerce")
        has_time = t.notna()
        local = d + pd.to_timedelta(t.dt.hour.fillna(0), unit="h") + pd.to_timedelta(t.dt.minute.fillna(0), unit="m")
        utc = local - pd.Timedelta(hours=8)
        utc[~has_time] = d[~has_time]     # all-day / tentative rows: keep the calendar date at 00:00 UTC
        frames.append(pd.DataFrame({"datetime_utc": utc, "currency": df["currency"], "event": df["event"].str.strip(),
                                    "impact": df["impact"], "actual": df["actual"], "forecast": df["forecast"],
                                    "previous": df["previous"], "has_time": has_time,
                                    "source": "forexfactory archive 2010-2023 (github spoluan/forex-factory-scraper), UTC+8 display zone"}))
    _SPOLUAN_CACHE = pd.concat(frames).dropna(subset=["datetime_utc"]).reset_index(drop=True)
    return _SPOLUAN_CACHE


def _load_fxdesk() -> pd.DataFrame:
    frames = []
    for p in sorted((RAW / "ff_history").glob("fxdesk_2026_*.csv")):
        df = pd.read_csv(p, dtype=str)
        d = pd.to_datetime(df["date"].str.strip() + " 2026", format="%b %d %Y", errors="coerce")
        t = pd.to_datetime(df["time"].str.strip(), format="%I:%M%p", errors="coerce")
        has_time = t.notna()
        local = d + pd.to_timedelta(t.dt.hour.fillna(0), unit="h") + pd.to_timedelta(t.dt.minute.fillna(0), unit="m")
        utc = local - pd.Timedelta(hours=7)   # scraper display zone looks like UTC+7 (NFP at 8:30pm/7:30pm); not fully consistent
        utc[~has_time] = d[~has_time]
        imp = df["impact"].map({"red": "High", "orange": "Medium", "yellow": "Low", "gray": "Holiday"}).fillna(df["impact"])
        frames.append(pd.DataFrame({"datetime_utc": utc, "currency": df["currency"], "event": df["event"].str.strip(),
                                    "impact": imp, "actual": df["actual"].replace("N/A", ""), "forecast": df["forecast"].replace("N/A", ""),
                                    "previous": df["previous"].replace("N/A", ""), "has_time": has_time,
                                    "source": "forexfactory 2026 Jan-Sep (github datpro12345/fx-desk), UTC+7 assumed, TIMES UNRELIABLE"}))
    return pd.concat(frames).dropna(subset=["datetime_utc"]).reset_index(drop=True)


def _load_cwt() -> pd.DataFrame:
    rows = []
    for p in sorted((RAW / "ff_history" / "cwt_raw").glob("*.json")):
        for e in json.loads(p.read_text()):
            if not isinstance(e, dict) or not e.get("date"):
                continue
            tm = e.get("time") or ""
            try:
                local = datetime.strptime(f"{e['date']} {tm}", "%Y-%m-%d %H:%M").replace(tzinfo=ET)
                utc = local.astimezone(timezone.utc).replace(tzinfo=None)
                has_time = True
            except ValueError:
                utc = datetime.strptime(e["date"], "%Y-%m-%d")
                has_time = False
            rows.append({"datetime_utc": utc, "currency": e.get("currency"), "event": e.get("title"),
                         "impact": str(e.get("impact", "")).capitalize(), "actual": e.get("actual") or "",
                         "forecast": e.get("forecast") or "", "previous": e.get("previous") or "", "has_time": has_time,
                         "source": "forexfactory 2026 Apr-Oct (github Gourav232003/cwt-macro-pipeline raw), America/New_York display zone"})
    return pd.DataFrame(rows).drop_duplicates(["datetime_utc", "currency", "event"])


def _load_cryptoprism() -> pd.DataFrame:
    p = RAW / "ff_history" / "cryptoprism_ff_export_20251109.csv"
    df = pd.read_csv(p, dtype=str)
    ist = ZoneInfo("Asia/Kolkata")
    rows = []
    for _, r in df.iterrows():
        try:
            local = datetime.strptime(f"{r['date']} {r['time'].strip()}", "%Y-%m-%d %I:%M%p").replace(tzinfo=ist)
            utc, has_time = local.astimezone(timezone.utc).replace(tzinfo=None), True
        except (ValueError, AttributeError):
            utc, has_time = datetime.strptime(r["date"], "%Y-%m-%d"), False
        rows.append({"datetime_utc": utc, "currency": r["currency"], "event": r["event"], "impact": str(r["impact"]).capitalize(),
                     "actual": r.get("actual") or "", "forecast": r.get("forecast") or "", "previous": r.get("previous") or "",
                     "has_time": has_time, "source": "forexfactory Oct-Dec 2025 snapshot (github CryptoPrism-io), IST display zone"})
    return pd.DataFrame(rows).fillna("")


def _load_ff_feed() -> pd.DataFrame:
    rows = []
    for p in sorted((RAW / "ff").glob("ff_calendar_*.json")):
        try:
            data = json.loads(p.read_text())
        except json.JSONDecodeError:
            continue
        for e in data:
            dt = pd.Timestamp(e["date"]).tz_convert("UTC").tz_localize(None)
            rows.append({"datetime_utc": dt, "currency": e.get("country"), "event": e.get("title"), "impact": e.get("impact"),
                         "actual": e.get("actual", ""), "forecast": e.get("forecast", ""), "previous": e.get("previous", ""),
                         "has_time": True, "source": f"forexfactory live feed nfs.faireconomy.media/{p.name}"})
    return pd.DataFrame(rows)


def build_events(fomc: pd.DataFrame, ecb: pd.DataFrame, bls: pd.DataFrame) -> pd.DataFrame:
    parts = [_load_spoluan(), _load_cryptoprism(), _load_fxdesk(), _load_cwt(), _load_ff_feed()]
    ff = pd.concat(parts, ignore_index=True)
    ff["impact"] = ff["impact"].replace({"Non-economic": "Non-Economic", "high": "High", "medium": "Medium", "low": "Low"})
    # structured, verified lists appended as events (currency tagged, no actual/forecast)
    f = pd.DataFrame({"datetime_utc": pd.to_datetime(fomc["statement_utc"]).dt.tz_localize(None), "currency": "USD",
                      "event": "FOMC Statement", "impact": "High", "actual": fomc["fed_funds_target"], "forecast": "", "previous": "",
                      "has_time": True, "source": "fomc_decisions.csv (" + fomc["time_quality"] + ")"})
    e1 = pd.DataFrame({"datetime_utc": pd.to_datetime(ecb["decision_utc"]).dt.tz_localize(None), "currency": "EUR",
                       "event": "ECB Monetary Policy Decision", "impact": "High", "actual": ecb.get("dfr_after", ""), "forecast": "", "previous": "",
                       "has_time": True, "source": "ecb_decisions.csv (" + ecb["time_quality"] + ")"})
    e2 = e1.copy()
    e2["datetime_utc"] = pd.to_datetime(ecb["press_conference_utc"]).dt.tz_localize(None)
    e2["event"] = "ECB Press Conference"
    b = pd.DataFrame({"datetime_utc": pd.to_datetime(bls["release_utc"]).dt.tz_localize(None), "currency": "USD",
                      "event": "BLS " + bls["release"], "impact": "High", "actual": "", "forecast": "", "previous": "",
                      "has_time": True, "source": "us_bls_releases.csv (" + bls["time_quality"] + ")"})
    allev = pd.concat([ff, f, e1, e2, b], ignore_index=True)
    allev["datetime_utc"] = pd.to_datetime(allev["datetime_utc"]).dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    allev = allev.sort_values(["datetime_utc", "currency", "event"]).reset_index(drop=True)
    return _finish(allev[EVENT_COLS + ["has_time"]])


def build_calendar() -> None:
    print("[calendar]")
    fomc = build_fomc()
    _save(fomc, "fomc_decisions.csv")
    ecb = build_ecb()
    _save(ecb, "ecb_decisions.csv")
    bls = build_us_releases()
    _save(bls, "us_bls_releases.csv")
    ev = build_events(fomc, ecb, bls)
    _save(ev, "events.csv")
    # compact high-impact EUR/USD subset for convenience
    sub = ev[ev["currency"].isin(["USD", "EUR"]) & ev["impact"].eq("High") & ev["has_time"]]
    _save(sub, "events_high_eur_usd.csv")


# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("steps", nargs="*", default=["all"], help="all | ecb | yahoo | mirrors | cftc | calendar")
    ap.add_argument("--offline", action="store_true", help="rebuild from data/raw without downloading")
    a = ap.parse_args(argv)
    steps = set(a.steps)
    if "all" in steps:
        steps = {"ecb", "mirrors", "cftc", "calendar", "yahoo"}
    if "ecb" in steps:
        fetch_ecb()
    if "mirrors" in steps:
        fetch_mirrors(offline=a.offline)
    if "cftc" in steps:
        if not a.offline:
            download_cftc()
        build_cftc()
    if "calendar" in steps:
        if not a.offline:
            download_calendar()
        build_calendar()
    if "yahoo" in steps:
        fetch_yahoo()


if __name__ == "__main__":
    main()
