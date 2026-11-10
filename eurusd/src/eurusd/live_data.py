"""Recent bars for live use.

HistData's monthly file lags by several days, so for signals and risk we splice the
most recent hourly bars from Yahoo Finance (verified against HistData: median gap
~3 pips, hourly return correlation 0.92) on top of the clean history. Spliced bars
are flagged in the `source` column.
"""
from __future__ import annotations

import time
from pathlib import Path

import pandas as pd
import requests

from .data import load_ohlc

RECENT = Path(__file__).resolve().parents[2] / "data" / "processed" / "recent_yahoo_H1.parquet"


def fetch_recent_yahoo(days: int = 5) -> pd.DataFrame:
    last_err = None
    for host in ("query2", "query1"):
        try:
            r = requests.get(f"https://{host}.finance.yahoo.com/v8/finance/chart/EURUSD=X",
                             params={"range": f"{days}d", "interval": "1h"},
                             headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            if r.status_code != 200:
                last_err = f"{host}: HTTP {r.status_code}"
                time.sleep(2)
                continue
            d = r.json()["chart"]["result"][0]
            q = d["indicators"]["quote"][0]
            df = pd.DataFrame({"open": q["open"], "high": q["high"], "low": q["low"], "close": q["close"]},
                              index=pd.to_datetime(d["timestamp"], unit="s", utc=True)).dropna()
            df = df[df.index.minute == 0]
            df = df[df.index + pd.Timedelta(hours=1) <= pd.Timestamp.now(tz="UTC")]   # drop the in-progress bar
            df["volume"] = 0
            df.index.name = "time"
            RECENT.parent.mkdir(parents=True, exist_ok=True)
            df.to_parquet(RECENT)
            return df
        except Exception as e:  # network / parse
            last_err = f"{host}: {e}"
            time.sleep(2)
    raise RuntimeError(f"Yahoo fetch failed: {last_err}")


def load_h1_live(refresh: bool = False) -> pd.DataFrame:
    """Clean HistData H1 history plus the newest Yahoo hourly bars (column `source`)."""
    h1 = load_ohlc("H1").copy()
    h1["source"] = "histdata"
    if refresh:
        try:
            fetch_recent_yahoo()
        except Exception as e:
            print(f"warning: could not refresh recent bars ({e}); using stored data")
    if RECENT.exists():
        y = pd.read_parquet(RECENT)
        y = y[y.index > h1.index[-1]]
        if not y.empty:
            y["source"] = "yahoo"
            h1 = pd.concat([h1, y[h1.columns]])
    return h1
