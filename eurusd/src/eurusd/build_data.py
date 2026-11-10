"""Download and build the EUR/USD OHLC dataset.

Re-runnable / idempotent:
  * HistData zips already present in data/raw/histdata/ are not re-downloaded
    (unless they fail the zip sanity check, in which case they are replaced).
  * Processed parquet files are always rebuilt from the raw zips (fast).

Sources
-------
1. HistData.com ASCII 1-minute bars (bid).  HistData documents the stamps as
   "EST without DST", but checking the data against ECB 14:15 CET fixings and
   against the 08:30 New York release minute of NFP/CPI shows the stamps follow
   US daylight saving (they are America/New_York local time).  Default
   conversion is therefore tz_localize("America/New_York") -> UTC
   (``--tz-mode ny-local``); ``--tz-mode est-fixed`` adds a flat 5 hours
   instead.  See data/DATA_QUALITY.md section "Timezone verification".
   Full-year files for past years, monthly files for the current year.  The list of available years/months is discovered from the
   HistData index page so the script keeps working as new months appear.
2. Yahoo Finance chart API (EURUSD=X daily/hourly, 6E=F daily), UTC timestamps.
3. ECB daily reference rate (EXR/D.USD.EUR.SP00.A), CSV.

Usage
-----
    python -m eurusd.build_data            # download what is missing + build all
    python -m eurusd.build_data --no-download   # only rebuild from existing zips

Security note: downloaded files are treated as untrusted data.  They are only
ever opened with zipfile/pandas; nothing is executed from the raw directory.
"""
from __future__ import annotations

import argparse
import io
import json
import logging
import re
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd
import requests

log = logging.getLogger("eurusd.build_data")

PKG_DIR = Path(__file__).resolve().parent
PROJECT_DIR = PKG_DIR.parent.parent          # .../eurusd
DATA_DIR = PROJECT_DIR / "data"
RAW_DIR = DATA_DIR / "raw" / "histdata"
PROC_DIR = DATA_DIR / "processed"

HISTDATA_BASE = "https://www.histdata.com"
HISTDATA_INDEX = f"{HISTDATA_BASE}/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/eurusd"
HISTDATA_GET = f"{HISTDATA_BASE}/get.php"
UA = ("Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0 Safari/537.36")

PRICE_MIN, PRICE_MAX = 0.5, 2.0
TIMEFRAMES = {"M5": "5min", "M15": "15min", "M30": "30min", "H1": "1h", "H4": "4h", "D1": "1D"}
MAX_CONCURRENT_DOWNLOADS = 2


# --------------------------------------------------------------------------- #
# HistData download
# --------------------------------------------------------------------------- #
def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA})
    return s


def discover_histdata_periods(sess: requests.Session) -> list[str]:
    """Return period identifiers like '2010' or '2026/3' listed on the index page."""
    r = sess.get(HISTDATA_INDEX, timeout=60)
    r.raise_for_status()
    found = set(re.findall(r'1-minute-bar-quotes/eurusd/(\d{4}(?:/\d{1,2})?)"', r.text, flags=re.I))
    def key(p):
        y, _, m = p.partition("/")
        return (int(y), int(m) if m else 0)
    periods = sorted(found, key=key)
    if not periods:
        raise RuntimeError("could not discover any HistData periods from index page")
    return periods


def _parse_form_fields(html: str) -> dict[str, str]:
    fields: dict[str, str] = {}
    for m in re.finditer(r"<input[^>]+>", html):
        tag = m.group(0)
        n = re.search(r'name="([^"]+)"', tag)
        v = re.search(r'value="([^"]*)"', tag)
        if n and v:
            fields[n.group(1)] = v.group(1)
    return fields


def zip_path_for(period: str) -> Path:
    y, _, m = period.partition("/")
    if m:
        return RAW_DIR / f"DAT_ASCII_EURUSD_M1_{int(y):04d}{int(m):02d}.zip"
    return RAW_DIR / f"DAT_ASCII_EURUSD_M1_{y}.zip"


def is_valid_zip(path: Path) -> bool:
    """A real zip containing exactly one DAT_ASCII_EURUSD_M1_*.csv member."""
    try:
        if path.stat().st_size < 1000:
            return False
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if re.fullmatch(r"DAT_ASCII_EURUSD_M1_\d{4,6}\.csv", n)]
            if len(names) != 1:
                return False
            if zf.testzip() is not None:
                return False
        return True
    except (zipfile.BadZipFile, OSError):
        return False


def download_histdata_period(period: str, sess: requests.Session | None = None,
                             retries: int = 3) -> tuple[str, Path, int, str]:
    """Download one HistData period. Returns (period, path, size, status)."""
    sess = sess or _session()
    out = zip_path_for(period)
    if out.exists() and is_valid_zip(out):
        return period, out, out.stat().st_size, "cached"
    page_url = f"{HISTDATA_INDEX}/{period}"
    last_err = ""
    for attempt in range(1, retries + 1):
        try:
            r = sess.get(page_url, timeout=60)
            r.raise_for_status()
            fields = _parse_form_fields(r.text)
            needed = {"tk", "date", "datemonth", "platform", "timeframe", "fxpair"}
            if not needed <= fields.keys():
                raise RuntimeError(f"form fields missing: {needed - fields.keys()}")
            payload = {k: fields[k] for k in needed}
            if payload["platform"] != "ASCII" or payload["timeframe"] != "M1" or payload["fxpair"] != "EURUSD":
                raise RuntimeError(f"unexpected form fields {payload}")
            resp = sess.post(HISTDATA_GET, data=payload, timeout=300,
                             headers={"Referer": page_url, "Origin": HISTDATA_BASE},
                             stream=True)
            resp.raise_for_status()
            tmp = out.with_suffix(".part")
            with open(tmp, "wb") as fh:
                for chunk in resp.iter_content(1 << 16):
                    fh.write(chunk)
            ctype = resp.headers.get("Content-Type", "")
            if not is_valid_zip(tmp):
                head = tmp.read_bytes()[:200]
                tmp.unlink(missing_ok=True)
                raise RuntimeError(f"not a valid zip (content-type={ctype!r}, head={head!r})")
            tmp.replace(out)
            return period, out, out.stat().st_size, "downloaded"
        except Exception as e:  # noqa: BLE001
            last_err = f"{type(e).__name__}: {e}"
            log.warning("period %s attempt %d failed: %s", period, attempt, last_err)
            time.sleep(3 * attempt)
    return period, out, 0, f"FAILED: {last_err}"


def download_all_histdata(periods: list[str] | None = None) -> list[tuple[str, Path, int, str]]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    sess = _session()
    periods = periods or discover_histdata_periods(sess)
    log.info("HistData periods available: %s", periods)
    results = []
    with ThreadPoolExecutor(max_workers=MAX_CONCURRENT_DOWNLOADS) as ex:
        for res in ex.map(lambda p: download_histdata_period(p, _session()), periods):
            log.info("%-8s %-10s %12s bytes  %s", res[0], res[3].split(":")[0], f"{res[2]:,}", res[1].name)
            results.append(res)
    with open(RAW_DIR / "download_log.json", "w") as fh:
        json.dump([{"period": p, "file": str(f.name), "size": s, "status": st} for p, f, s, st in results],
                  fh, indent=1)
    return results


# --------------------------------------------------------------------------- #
# Parse + build
# --------------------------------------------------------------------------- #
TZ_MODE = "ny-local"   # or "est-fixed"; set from main()


def stamps_to_utc(ts: pd.Series, mode: str = "ny-local") -> pd.DatetimeIndex:
    """Convert raw HistData stamps (naive) to a UTC DatetimeIndex."""
    naive = pd.DatetimeIndex(ts)
    if mode == "est-fixed":
        return (naive + pd.Timedelta(hours=5)).tz_localize("UTC")
    if mode == "ny-local":
        # FX is closed at 02:00 Sunday local when US clocks change, so ambiguous /
        # nonexistent stamps do not occur in practice; map any that do to NaT.
        return naive.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC")
    raise ValueError(mode)


def read_histdata_zip(path: Path, tz_mode: str | None = None) -> pd.DataFrame:
    """Parse one HistData M1 zip into a UTC-indexed OHLCV frame (no dedupe)."""
    tz_mode = tz_mode or TZ_MODE
    with zipfile.ZipFile(path) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        with zf.open(name) as fh:
            df = pd.read_csv(
                io.TextIOWrapper(fh, encoding="ascii", errors="strict"),
                sep=";", header=None,
                names=["ts", "open", "high", "low", "close", "volume"],
                dtype={"ts": str, "open": "float64", "high": "float64", "low": "float64",
                       "close": "float64", "volume": "int64"},
                engine="c",
            )
    ts = pd.to_datetime(df["ts"], format="%Y%m%d %H%M%S", errors="coerce")
    bad = ts.isna().sum()
    if bad:
        log.warning("%s: %d unparseable timestamps dropped", path.name, bad)
    df = df.loc[~ts.isna()].copy()
    idx = stamps_to_utc(ts[~ts.isna()], tz_mode)
    if idx.isna().any():
        log.warning("%s: %d stamps fell in a DST transition and were dropped", path.name, int(idx.isna().sum()))
        df = df.loc[~idx.isna()]
        idx = idx[~idx.isna()]
    df.index = idx
    df.index.name = "time"
    df = df.drop(columns="ts")
    df.attrs["source_file"] = path.name
    return df


def build_m1(zips: list[Path]) -> tuple[pd.DataFrame, dict]:
    frames, per_file = [], {}
    for z in sorted(zips):
        d = read_histdata_zip(z)
        per_file[z.name] = {"rows": int(len(d)), "first": str(d.index.min()), "last": str(d.index.max())}
        frames.append(d)
    m1 = pd.concat(frames)
    n_raw = len(m1)
    m1 = m1.sort_index()
    dup_mask = m1.index.duplicated(keep="last")
    n_dup = int(dup_mask.sum())
    m1 = m1.loc[~dup_mask]
    # Remove physically impossible bars (EUR/USD has never traded outside 0.8-1.6;
    # the bounds below only catch corrupt ticks such as 1965.0 or -0.0001).
    px = m1[["open", "high", "low", "close"]]
    bad_mask = ((px < PRICE_MIN) | (px > PRICE_MAX)).any(axis=1)
    bad_rows = m1.loc[bad_mask]
    for t, row in bad_rows.iterrows():
        log.warning("dropping impossible bar %s: %s", t, row.to_dict())
    m1 = m1.loc[~bad_mask]
    m1 = m1[["open", "high", "low", "close", "volume"]].astype(
        {"open": "float64", "high": "float64", "low": "float64", "close": "float64", "volume": "int64"})
    stats = {"rows_raw": int(n_raw), "duplicates_removed": n_dup,
             "impossible_price_rows_removed": int(bad_mask.sum()),
             "impossible_price_rows": [{"time": str(t), **{k: float(v) for k, v in r.items()}}
                                       for t, r in bad_rows.iterrows()],
             "tz_mode": TZ_MODE, "rows": int(len(m1)), "per_file": per_file}
    return m1, stats


def resample_ohlc(m1: pd.DataFrame, rule: str) -> pd.DataFrame:
    """Resample M1 bars to `rule`. Bars labelled by start time (left, closed left,
    anchored at midnight UTC). Only periods containing >=1 M1 bar are kept."""
    agg = m1.resample(rule, label="left", closed="left", origin="start_day").agg(
        {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"})
    agg = agg.dropna(subset=["open"])
    agg["volume"] = agg["volume"].astype("int64")
    return agg


def build_all_timeframes(m1: pd.DataFrame) -> dict[str, Path]:
    PROC_DIR.mkdir(parents=True, exist_ok=True)
    out = {}
    p = PROC_DIR / "EURUSD_M1.parquet"
    m1.to_parquet(p, compression="zstd")
    out["M1"] = p
    for tf, rule in TIMEFRAMES.items():
        df = resample_ohlc(m1, rule)
        p = PROC_DIR / f"EURUSD_{tf}.parquet"
        df.to_parquet(p, compression="zstd")
        out[tf] = p
        log.info("%s: %d bars -> %s", tf, len(df), p.name)
    return out


# --------------------------------------------------------------------------- #
# Yahoo + ECB
# --------------------------------------------------------------------------- #
YAHOO_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")


def fetch_yahoo(symbol: str, rng: str | None, interval: str, retries: int = 4,
                period1: int | None = None, period2: int | None = None) -> pd.DataFrame:
    """Yahoo chart API. Returns 429 'Too Many Requests' erratically from shared egress
    IPs (it normally wants an A1/A3 cookie from fc.yahoo.com, which may be blocked), so
    we alternate query2/query1 hosts and back off between attempts."""
    last = None
    for attempt in range(retries):
        host = "query2" if attempt % 2 == 0 else "query1"
        url = f"https://{host}.finance.yahoo.com/v8/finance/chart/{symbol}"
        params = {"interval": interval, "includePrePost": "false"}
        if period1 is not None:   # explicit window: 'range=max&interval=1d' silently returns MONTHLY bars
            params.update(period1=int(period1), period2=int(period2 or time.time()))
        else:
            params["range"] = rng
        r = requests.get(url, params=params,
                         headers={"User-Agent": YAHOO_UA, "Accept": "application/json"}, timeout=60)
        if r.status_code == 200:
            break
        last = f"{r.status_code} from {host}: {r.text[:80]!r}"
        log.warning("yahoo %s attempt %d: %s", symbol, attempt + 1, last)
        time.sleep(15 * (attempt + 1))
    else:
        raise RuntimeError(f"yahoo {symbol} failed: {last}")
    js = r.json()
    res = js["chart"]["result"][0]
    q = res["indicators"]["quote"][0]
    df = pd.DataFrame({"open": q["open"], "high": q["high"], "low": q["low"], "close": q["close"],
                       "volume": q.get("volume")},
                      index=pd.to_datetime(res["timestamp"], unit="s", utc=True))
    df.index.name = "time"
    df = df.dropna(subset=["close"])
    df.attrs["meta"] = {k: res["meta"].get(k) for k in ("symbol", "exchangeTimezoneName", "gmtoffset", "currency")}
    return df


def fetch_ecb() -> pd.DataFrame:
    url = "https://data-api.ecb.europa.eu/service/data/EXR/D.USD.EUR.SP00.A"
    r = _session().get(url, params={"format": "csvdata"}, timeout=120)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    df = df[["TIME_PERIOD", "OBS_VALUE"]].rename(columns={"TIME_PERIOD": "date", "OBS_VALUE": "usd_per_eur"})
    df["date"] = pd.to_datetime(df["date"])
    return df.sort_values("date").reset_index(drop=True)


# --------------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-download", action="store_true", help="only rebuild from existing zips")
    ap.add_argument("--skip-external", action="store_true", help="skip Yahoo/ECB fetches")
    ap.add_argument("--tz-mode", choices=["ny-local", "est-fixed"], default="ny-local",
                    help="how to interpret HistData stamps (default ny-local, see docstring)")
    args = ap.parse_args(argv)
    global TZ_MODE
    TZ_MODE = args.tz_mode
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    if not args.no_download:
        download_all_histdata()
    zips = [p for p in sorted(RAW_DIR.glob("DAT_ASCII_EURUSD_M1_*.zip")) if is_valid_zip(p)]
    log.info("valid zips: %d", len(zips))
    m1, stats = build_m1(zips)
    log.info("M1 rows=%d (raw %d, dups removed %d, impossible removed %d, tz=%s) range %s .. %s",
             stats["rows"], stats["rows_raw"], stats["duplicates_removed"],
             stats["impossible_price_rows_removed"], TZ_MODE, m1.index.min(), m1.index.max())
    with open(PROC_DIR / "build_stats.json", "w") as fh:
        json.dump(stats, fh, indent=1)
    build_all_timeframes(m1)

    if not args.skip_external:
        for sym, rng, iv, name, p1 in [("EURUSD=X", None, "1d", "yahoo_EURUSD_D1", 946684800),
                                       ("EURUSD=X", "730d", "1h", "yahoo_EURUSD_H1", None),
                                       ("6E=F", None, "1d", "yahoo_6E_D1", 946684800)]:
            try:
                df = fetch_yahoo(sym, rng, iv, period1=p1)
                df.to_parquet(PROC_DIR / f"{name}.parquet")
                log.info("%s: %d rows %s .. %s meta=%s", name, len(df), df.index.min(), df.index.max(), df.attrs["meta"])
            except Exception as e:  # noqa: BLE001
                log.error("%s failed: %s", name, e)
        try:
            ecb = fetch_ecb()
            ecb.to_csv(PROC_DIR / "ecb_EURUSD_D1.csv", index=False)
            log.info("ECB: %d rows %s .. %s", len(ecb), ecb["date"].min().date(), ecb["date"].max().date())
        except Exception as e:  # noqa: BLE001
            log.error("ECB failed: %s", e)
    return 0


if __name__ == "__main__":
    sys.exit(main())
