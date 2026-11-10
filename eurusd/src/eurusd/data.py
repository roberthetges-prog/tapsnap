"""Loaders for the processed EUR/USD OHLC dataset.

Timezone conventions
--------------------
* Every DataFrame returned here has a tz-aware ``DatetimeIndex`` in **UTC**,
  named ``time``.  The index value is the **start** of the bar (a 2015-01-15
  09:30 H1 bar covers 09:30:00-10:29:59 UTC).
* HistData *documents* its ASCII stamps as "EST without daylight saving", but
  the data itself (ECB 14:15 CET fixings, 08:30 New York payroll spikes) shows
  the stamps follow US DST, i.e. they are America/New_York local time.
  ``build_data.py`` therefore converts with
  ``tz_localize("America/New_York").tz_convert("UTC")`` (default
  ``--tz-mode ny-local``; the evidence is in data/DATA_QUALITY.md, section 2a).
  Consequently the weekly FX session runs Sunday 17:00 to Friday 17:00 New York
  time = 22:00 UTC in winter and 21:00 UTC during US summer time, with a few
  odd weeks (US on DST, Europe not) opening at 20:00 UTC.
* Daily bars (``D1``) are UTC calendar days (00:00-23:59:59 UTC), *not* the
  New York 17:00 "forex day".  Use ``resample`` on M1/H1 with ``offset`` if you
  need a different day boundary.
* Prices are HistData **bid** quotes, 5 decimals.  ``volume`` is the tick count
  reported by HistData, which is 0 for most of the history; it is kept for
  completeness and must not be interpreted as traded volume.
* Yahoo Finance frames are also UTC (Yahoo returns epoch seconds).  The ECB
  series is a daily reference rate at ~14:15 CET, indexed by calendar date.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent.parent.parent     # .../eurusd
PROC_DIR = PROJECT_DIR / "data" / "processed"

TIMEFRAMES = ("M1", "M5", "M15", "M30", "H1", "H4", "D1")


def _ensure_utc(df: pd.DataFrame) -> pd.DataFrame:
    idx = pd.DatetimeIndex(df.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    df.index = idx
    df.index.name = "time"
    return df


def load_ohlc(timeframe: str = "H1", start: str | pd.Timestamp | None = None,
              end: str | pd.Timestamp | None = None) -> pd.DataFrame:
    """Load HistData-derived EUR/USD bars for ``timeframe``.

    Parameters
    ----------
    timeframe : one of M1, M5, M15, M30, H1, H4, D1 (case-insensitive).
    start, end : optional inclusive bounds (interpreted as UTC if naive).

    Returns
    -------
    DataFrame with columns open, high, low, close, volume and a UTC
    DatetimeIndex named ``time`` (bar start times, sorted, unique).
    """
    tf = timeframe.upper()
    if tf not in TIMEFRAMES:
        raise ValueError(f"timeframe must be one of {TIMEFRAMES}, got {timeframe!r}")
    path = PROC_DIR / f"EURUSD_{tf}.parquet"
    if not path.exists():
        raise FileNotFoundError(f"{path} missing - run `python -m eurusd.build_data` first")
    df = _ensure_utc(pd.read_parquet(path))
    if start is not None:
        df = df.loc[pd.Timestamp(start).tz_localize("UTC") if pd.Timestamp(start).tzinfo is None else pd.Timestamp(start):]
    if end is not None:
        df = df.loc[:pd.Timestamp(end).tz_localize("UTC") if pd.Timestamp(end).tzinfo is None else pd.Timestamp(end)]
    return df


def load_yahoo(name: str = "EURUSD_D1") -> pd.DataFrame:
    """Load a Yahoo cross-check frame: 'EURUSD_D1', 'EURUSD_H1' or '6E_D1'. UTC index."""
    return _ensure_utc(pd.read_parquet(PROC_DIR / f"yahoo_{name}.parquet"))


def load_ecb() -> pd.Series:
    """ECB daily USD-per-EUR reference rate as a Series indexed by date (naive, calendar day)."""
    df = pd.read_csv(PROC_DIR / "ecb_EURUSD_D1.csv", parse_dates=["date"])
    return df.set_index("date")["usd_per_eur"].sort_index()
