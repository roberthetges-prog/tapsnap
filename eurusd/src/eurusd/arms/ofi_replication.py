"""Arm P ("ofi_replication"), round 4: ONE pre-registered replication of arm K's control (a) on six other dollar pairs.

HYPOTHESIS (from reports/arm_intraday_path.md; post-hoc there, best of 22 backtests, deflated p 0.39): the 5-day
tick-rule order-flow proxy, NET of the price move of the same days, predicts the next week with the literature sign
(+). On EUR/USD: net Sharpe +0.53 (t 2.23) / +0.41 / +0.68 for 2010-26 / 2016-26 / 2023-26 at 1.2 pips.
This module runs that rule, and nothing else, on GBPUSD, USDJPY, AUDUSD, USDCHF, USDCAD and NZDUSD.

=====================================================================================================================
FROZEN DEFINITION (STEP 0: written from arm K's code - intraday_path.build_features / load_frame / make_fit_predict(
residualise=True) / positions / evaluate and featstore.build_daily - BEFORE any 1-minute bar of another pair was
downloaded. This is the ONLY variant. Nothing below was changed after results were seen.)

Sessions (featstore.build_daily): 1-minute bid bars in true UTC -> hourly bars (bins anchored at the hour, bins
  with >= 1 bar), rows from 2003-01-01 00:00 UTC. Session = [22:00 UTC, 22:00 UTC + 24h), index = session start.
  Kept: sessions with >= 10 hourly bars whose start is not a Saturday. open / high / low / close of the session
  from those bars. close_time = start + 24h.
Existing price features of session t (the three regressors), all known at close_time:
  c_ret  = ret_1d / rv_1d_bp, ret_1d = 1e4 * log(close_t / close_{t-1}) over kept sessions,
           rv_1d_bp = 1e4 * sqrt(sum of squared hourly log close changes of the hourly bars of the session; the
           first hourly change of a session is measured from the last hourly close before it); 0 -> NaN
  c_body = body_rel = (close - open) / (high - low)
  c_cir  = close_in_range - 0.5 = (close - low) / (high - low) - 0.5
  rv_21d_bp = 1e4 * sqrt(mean of the last 21 sessions' rv)  (vol scale only)
Order-flow proxy of session t (intraday_path.build_features, `ofi`), from the 1-MINUTE bars stamped in the session:
  d_i = sign(close_i - close_{i-1}) (first bar of a session: sign(close - open)); a zero change takes the last
        non-zero sign of the same session (0 until there is one);
  w_i = min(high_i - low_i, 30 pips)   [30e-4 for EUR/USD; 30 pips of the pair = 0.30 for USDJPY]
  ofi = sum(w_i d_i) / sum(w_i).
  NOTE: the weight is the 1-minute RANGE, not the absolute close change (arm K: that would be the efficiency
  ratio), and the bars are 1-minute bars, not 5-minute bars. The brief's one-line paraphrase differs; the code rules.
Quality rule (arm K, unchanged): 5-minute sampling = last 1-minute close of each 5-minute bin; a 5-minute return
  between consecutive observed bins of a session is valid when it spans <= 3 bins (15 minutes); the first one of a
  session (from the session open) counts as valid. ofi = NaN when the session has fewer than 200 valid 5-minute
  returns or more than 120 minutes of holes (sum of (bins spanned - 1) * 5 over the invalid returns).
5-day features: w5_x = mean of the last 5 kept sessions of x, at least 3 available, for x in ofi, c_ret, c_body, c_cir.
Label: fwd_5d = 1e4 * log(close_{t+5} / close_t); label_end_5d = close_time + 8 days. fwd_1d for the P&L.
Walk-forward (eurusd.wf.walk_forward, defaults: test years 2010..2026, min_train_years 5): for test year Y the
  training rows are those with label_end_5d < Y-01-01. In the training window:
  1. residualisation: beta = OLS WITHOUT intercept of w5_ofi on [w5_c_ret, w5_c_body, w5_c_cir] over rows where all
     four are available (>= 250 rows, else beta = 0); residual e = w5_ofi - C beta, with a missing regressor
     counted as 0;
  2. standardisation: sd = sample standard deviation of the training residual (no demeaning; needs >= 250 rows);
     z = clip(e / sd, -2, 2) / 2;
  3. sign: +1 (literature prior; the label is not used for anything in this single-signal variant);
  4. threshold: thr = training median of |z| over available rows;
  5. vol target: v* = training median of rv_21d_bp.
  Test year: target s_t = sign(z_t) if |z_t| > thr else 0, times min(1, v* / rv_21d_bp_t) (0 if rv_21d missing).
Holding: position_t = (s_t + s_{t-1} + ... + s_{t-4}) / 5  (1/5 tranches held five sessions).
P&L: eurusd.wf.pnl_from_positions on fwd_1d, cost = 1.2 pips per unit of |change of position|, converted to bp at
  the session close; rows from 2010; eurusd.wf.report with 252 periods a year.

=====================================================================================================================
REPLICATION PROTOCOL (also fixed in STEP 0, before any new data)
* Pairs: GBPUSD, USDJPY, AUDUSD, USDCHF, USDCAD, NZDUSD, HistData.com 1-minute bid bars, stamps converted
  America/New_York -> UTC (to be VERIFIED per pair on the payroll minute, not assumed). Each pair on its own session
  grid, traded in its own quote direction (long the pair when the signal is positive).
* Data span: the brief says 2008-2026. The frozen harness needs 5 calendar years before the first test year
  (min_train_years = 5) and EUR/USD was trained on 2003-2009 for test year 2010, so a 2008 start would give no
  test year before 2013 unless the harness default were changed. Decision before any download: fetch every pair
  from 2003 (or from its first HistData year if later), exactly the EUR/USD span, and keep the harness untouched.
  A pair whose history starts after 2005 simply has no stream in its first years; it is reported as it comes.
* Pip: 0.0001, USDJPY 0.01. Order-flow weight cap = 30 pips of the pair. Cost = 1.2 pips of the pair in bp at the
  session close (passed to the harness as cost_pips * pip / 1e-4).
* Cleaning: duplicate stamps -> last; bars with a price outside [median / 2, 2 * median] of their file removed
  (the EUR/USD build removes prices outside [0.5, 2.0], the same idea); nothing else.
* Per pair: net Sharpe and t for 2010-26 / 2016-26 / 2023-26, hit rate (share of active sessions with the right
  sign before costs, and with positive net P&L), number of calendar years 2010-2026 with a positive net sum.
* Basket: equal weight of the six, basket net bp of a session = mean of the six pairs' net bp (a pair without a
  row that session contributes 0 if it has a walk-forward stream in that test year, and is left out of the mean
  otherwise).
* Pooled t (the one used for the verdict): each pair's daily net P&L 2010-26 divided by its own standard
  deviation, averaged across pairs per session (same missing rule), t = mean / sd * sqrt(n) of that daily series,
  i.e. the pooled mean with errors clustered by day (dollar pairs are correlated). Also reported, not used for
  the verdict: Stouffer z of the six t-stats assuming independence (an upper bound) and the plain basket t.
* VERDICT RULE: REPLICATES if the basket net Sharpe is positive in 2010-26 AND in 2016-26, AND pooled t >= 2,
  AND at least 4 of the 6 pairs have a positive 2010-26 net Sharpe. FAILS otherwise.
* Leak checks on the basket: (1) labels shuffled (one permutation of the session calendar applied to all pairs,
  fwd_5d rebuilt from the shuffled fwd_1d), 20 draws; (2) all four w5 features lagged one session; (3) look-ahead
  control: features led by one and by five sessions (must light up: the flow of a session contains its return).
* Trials: 1 (six pairs, one rule). No other window, sign, residualisation or weighting is run. Temptations are
  written in the report as notes instead.
* EUR/USD stream of this rule is saved as the arm's positions file whatever the verdict.

Data products: raw zips data/raw/histdata_<pair>/ (git-ignored); data/processed/cross/ofi_<pair>_M5.parquet
(5-minute bid bars, true UTC, float32); data/processed/ofi_replication_daily_<pair>.parquet (the daily frame used
by run(); the order-flow proxy needs the 1-minute bars, so it is computed from the zips at build time).

CLI: python src/eurusd/arms/ofi_replication.py eur | download | build | run [cost] | leak | all
"""
from __future__ import annotations

import io
import json
import math
import re
import sys
import time
import zipfile
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.wf import walk_forward, pnl_from_positions, report, _agg  # noqa: E402

ARM = "ofi_replication"
RES = ROOT / "experiments/results/arms"
PROC = ROOT / "data/processed"
CROSS = PROC / "cross"
EUR_M1 = PROC / "EURUSD_M1.parquet"
PAIRS = {"gbpusd": 1e-4, "usdjpy": 1e-2, "audusd": 1e-4, "usdchf": 1e-4, "usdcad": 1e-4, "nzdusd": 1e-4}   # pip size
FIRST_YEAR = 2003
MIN_TRAIN_ROWS = 250
MIN_VALID_5M = 200
MAX_HOLE_MIN = 120
W_CAP_PIPS = 30.0
PERIODS = (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026))
FCOLS = ["w5_ofi", "w5_c_ret", "w5_c_body", "w5_c_cir"]
CTRL = FCOLS[1:]

HISTDATA = "https://www.histdata.com"
UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def raw_dir(pair: str) -> Path:
    return ROOT / "data/raw" / f"histdata_{pair}"


def daily_path(pair: str) -> Path:
    return PROC / f"{ARM}_daily_{pair}.parquet"


# ================================================================================================ download (HistData)
def _index_url(pair: str) -> str:
    return f"{HISTDATA}/download-free-forex-historical-data/?/ascii/1-minute-bar-quotes/{pair}"


def _zip_path(pair: str, period: str) -> Path:
    y, _, m = period.partition("/")
    tag = f"{int(y):04d}{int(m):02d}" if m else y
    return raw_dir(pair) / f"DAT_ASCII_{pair.upper()}_M1_{tag}.zip"


def _valid_zip(path: Path, pair: str) -> bool:
    try:
        if path.stat().st_size < 1000:
            return False
        with zipfile.ZipFile(path) as zf:
            names = [n for n in zf.namelist() if re.fullmatch(rf"DAT_ASCII_{pair.upper()}_M1_\d{{4,6}}\.csv", n)]
            return len(names) == 1 and zf.testzip() is None
    except (zipfile.BadZipFile, OSError):
        return False


def _fetch_period(pair: str, period: str, retries: int = 3) -> tuple[str, str, int, str]:
    import requests
    out = _zip_path(pair, period)
    if out.exists() and _valid_zip(out, pair):
        return pair, period, out.stat().st_size, "cached"
    sess = requests.Session()
    sess.headers.update({"User-Agent": UA})
    page = f"{_index_url(pair)}/{period}"
    err = ""
    for attempt in range(1, retries + 1):
        try:
            r = sess.get(page, timeout=60)
            r.raise_for_status()
            fields = {}
            for tag in re.findall(r"<input[^>]+>", r.text):
                n, v = re.search(r'name="([^"]+)"', tag), re.search(r'value="([^"]*)"', tag)
                if n and v:
                    fields[n.group(1)] = v.group(1)
            need = {"tk", "date", "datemonth", "platform", "timeframe", "fxpair"}
            if not need <= fields.keys():
                raise RuntimeError(f"form fields missing: {need - fields.keys()}")
            payload = {k: fields[k] for k in need}
            if payload["platform"] != "ASCII" or payload["timeframe"] != "M1" or payload["fxpair"] != pair.upper():
                raise RuntimeError(f"unexpected form fields {payload}")
            time.sleep(1.5)
            resp = sess.post(f"{HISTDATA}/get.php", data=payload, timeout=300, headers={"Referer": page, "Origin": HISTDATA}, stream=True)
            resp.raise_for_status()
            tmp = out.with_suffix(".part")
            with open(tmp, "wb") as fh:
                for chunk in resp.iter_content(1 << 16):
                    fh.write(chunk)
            if not _valid_zip(tmp, pair):
                head = tmp.read_bytes()[:120]
                tmp.unlink(missing_ok=True)
                raise RuntimeError(f"not a valid zip (head={head!r})")
            tmp.replace(out)
            time.sleep(1.5)
            return pair, period, out.stat().st_size, "downloaded"
        except Exception as e:  # noqa: BLE001
            err = f"{type(e).__name__}: {e}"
            time.sleep(4 * attempt)
    return pair, period, 0, f"FAILED: {err}"


def download(pairs: list[str] | None = None) -> pd.DataFrame:
    """Fetch every missing period (years; months for the current year) from FIRST_YEAR on, 2 requests at a time."""
    import requests
    rows = []
    for pair in pairs or list(PAIRS):
        raw_dir(pair).mkdir(parents=True, exist_ok=True)
        r = requests.get(_index_url(pair), headers={"User-Agent": UA}, timeout=60)
        r.raise_for_status()
        found = set(re.findall(rf"1-minute-bar-quotes/{pair}/(\d{{4}}(?:/\d{{1,2}})?)\"", r.text, flags=re.I))   # '2010' or '2026/3'
        key = lambda q: (int(q.partition("/")[0]), int(q.partition("/")[2] or 0))
        years = sorted({key(q)[0] for q in found})
        periods = sorted([q for q in found if key(q)[0] >= FIRST_YEAR], key=key)
        with ThreadPoolExecutor(max_workers=2) as ex:
            for res in ex.map(lambda q: _fetch_period(pair, q), periods):
                print(f"{res[0]} {res[1]:8s} {res[2]:>10,d} bytes  {res[3]}", flush=True)
                rows.append({"pair": res[0], "period": res[1], "bytes": res[2], "status": res[3], "first_year_on_site": years[0] if years else None})
    out = pd.DataFrame(rows)
    if len(out):
        (RES / "logs").mkdir(parents=True, exist_ok=True)
        out.to_csv(RES / "logs" / f"{ARM}_download.csv", index=False)
    return out


# ================================================================================================ raw -> M1 (UTC)
def read_zip(path: Path) -> pd.DataFrame:
    """One HistData zip -> frame indexed by the RAW naive stamp (open, high, low, close)."""
    with zipfile.ZipFile(path) as zf:
        name = [n for n in zf.namelist() if n.endswith(".csv")][0]
        with zf.open(name) as fh:
            df = pd.read_csv(io.TextIOWrapper(fh, encoding="ascii", errors="strict"), sep=";", header=None,
                             names=["ts", "open", "high", "low", "close", "volume"],
                             dtype={"ts": str, "open": "float64", "high": "float64", "low": "float64", "close": "float64", "volume": "int64"})
    ts = pd.to_datetime(df["ts"], format="%Y%m%d %H%M%S", errors="coerce")
    df = df.loc[ts.notna(), ["open", "high", "low", "close"]]
    df.index = pd.DatetimeIndex(ts[ts.notna()], name="time")
    med = float(df["close"].median())
    bad = ((df < med / 2) | (df > med * 2)).any(axis=1)
    df.attrs["bad_price_rows"] = int(bad.sum())
    return df.loc[~bad]


def load_m1(pair: str) -> tuple[pd.DataFrame, dict]:
    """All zips of a pair -> 1-minute bars in true UTC (stamps are America/New_York local time; verified in tz_check)."""
    frames, bad, files = [], 0, sorted(raw_dir(pair).glob(f"DAT_ASCII_{pair.upper()}_M1_*.zip"))
    for z in files:
        d = read_zip(z)
        bad += d.attrs["bad_price_rows"]
        frames.append(d)
    raw = pd.concat(frames)
    idx = raw.index.tz_localize("America/New_York", ambiguous="NaT", nonexistent="NaT").tz_convert("UTC")
    n_nat = int(idx.isna().sum())
    m1 = raw.set_axis(idx).loc[~idx.isna()].sort_index()
    dup = m1.index.duplicated(keep="last")
    m1 = m1.loc[~dup]
    return m1, {"files": len(files), "rows": int(len(m1)), "bad_price_rows": bad, "dst_dropped": n_nat, "duplicates": int(dup.sum()),
                "first": str(m1.index.min()), "last": str(m1.index.max())}


def tz_check(m1: pd.DataFrame) -> dict:
    """Minute (UTC, after the America/New_York conversion) of the largest 1-minute range between 11:00 and 16:00 UTC on
    the first Friday of every month, by US season. US payrolls are released 08:30 New York time: 12:30 UTC under EDT,
    13:30 UTC under EST. If the stamps were flat EST the conversion would put the summer spike at 11:30 UTC."""
    x = m1.loc[(m1.index.dayofweek == 4) & (m1.index.day <= 7) & (m1.index.hour >= 11) & (m1.index.hour < 16)]
    rng = (x["high"] - x["low"])
    day = x.index.normalize()
    top = rng.groupby(day).idxmax()
    out = {}
    top = pd.DatetimeIndex(top)                                   # tz-aware UTC stamps of the widest minute
    summer = top.tz_convert("America/New_York").map(lambda t: t.dst() != pd.Timedelta(0))
    hm = top.strftime("%H:%M")
    for lab, msk in (("summer_EDT", np.asarray(summer, dtype=bool)), ("winter_EST", ~np.asarray(summer, dtype=bool))):
        vc = pd.Series(hm[msk]).value_counts()
        out[lab] = {"n_first_fridays": int(msk.sum()), "modal_minute_utc": vc.index[0], "share_at_mode": float(vc.iloc[0] / msk.sum()),
                    "share_1230": float(vc.get("12:30", 0) / msk.sum()), "share_1330": float(vc.get("13:30", 0) / msk.sum()),
                    "share_1130": float(vc.get("11:30", 0) / msk.sum())}
    return out


def tz_check_bls(write: bool = True) -> pd.DataFrame:
    """Second timezone check, on the dated release list data/macro/us_bls_releases.csv (Employment Situation, 2010+):
    the 5-minute bar with the largest range within +-3 hours of each release, relative to the release time, by season.
    Right conversion: offset 0. Stamps that were really flat EST: offset -60 minutes under EDT."""
    b = pd.read_csv(ROOT / "data/macro/us_bls_releases.csv")
    T = pd.DatetimeIndex(pd.to_datetime(b.loc[b["release"] == "Employment Situation", "release_utc"], utc=True))
    rows = []
    for pair in PAIRS:
        m5 = pd.read_parquet(CROSS / f"ofi_{pair}_M5.parquet", columns=["high", "low"])
        rng = (m5["high"] - m5["low"]).astype("float64")
        T_ = T[T <= m5.index.max()].as_unit(m5.index.unit)
        off = []
        for t in T_:
            w = rng.loc[t - pd.Timedelta(hours=3): t + pd.Timedelta(hours=3)]
            off.append((w.idxmax() - t).total_seconds() / 60 if len(w) > 40 else np.nan)
        off = pd.Series(off, index=T_).dropna()
        edt = np.asarray(off.index.tz_convert("America/New_York").map(lambda t: t.dst() != pd.Timedelta(0)), dtype=bool)
        for lab, msk in (("summer_EDT", edt), ("winter_EST", ~edt)):
            o = off[msk]
            rows.append({"pair": pair, "season": lab, "n_releases": int(len(o)), "release_hour_utc": "12:30" if lab == "summer_EDT" else "13:30",
                         "share_offset_0": float((o == 0).mean()), "share_offset_minus60": float((o == -60).mean()), "share_offset_plus60": float((o == 60).mean())})
    out = pd.DataFrame(rows)
    if write:
        out.to_csv(RES / f"{ARM}_tzcheck.csv", index=False)
    return out


# ================================================================================================ M1 -> daily frame
def _group_first(code_sorted: np.ndarray) -> np.ndarray:
    return np.r_[0, np.flatnonzero(np.diff(code_sorted)) + 1]


def ofi_sessions(m1: pd.DataFrame, pip: float) -> pd.DataFrame:
    """Order-flow proxy and the quality counts per 22:00-UTC session (index = session start)."""
    ts = m1.index.as_unit("ns").asi8
    o, h, l, c = (m1[k].values for k in ("open", "high", "low", "close"))
    DAY, H22, MIN5 = 86_400_000_000_000, 22 * 3_600_000_000_000, 300_000_000_000
    uniq, code = np.unique((ts - H22) // DAY, return_inverse=True)
    ns = len(uniq)
    first = _group_first(code)
    # 5-minute sampling and the quality rule
    b = ts // MIN5
    bi = np.r_[np.flatnonzero(np.diff(b)), len(b) - 1]
    bc, bb = code[bi], b[bi]
    same = np.r_[False, bc[1:] == bc[:-1]]
    dt = np.where(same, bb - np.roll(bb, 1), 1)
    valid = dt <= 3
    nv = np.bincount(bc, weights=valid, minlength=ns)
    hole = np.bincount(bc, weights=np.where(same & ~valid, (dt - 1) * 5.0, 0.0), minlength=ns)
    # tick rule on 1-minute closes, zero change -> last non-zero sign of the session
    d = np.sign(np.r_[0.0, np.diff(c)])
    d[first] = np.sign(c[first] - o[first])
    pos = np.arange(len(d))
    reset = np.zeros(len(d), dtype=np.int64)
    reset[first] = first
    seg_start = np.maximum.accumulate(reset)
    known = np.maximum.accumulate(np.where(d != 0, pos, -1))
    dd = np.where(known >= seg_start, d[np.maximum(known, 0)], 0.0)
    w = np.minimum(h - l, W_CAP_PIPS * pip)
    with np.errstate(divide="ignore", invalid="ignore"):
        ofi = np.bincount(code, weights=w * dd, minlength=ns) / np.bincount(code, weights=w, minlength=ns)
    X = pd.DataFrame({"n_m1": np.bincount(code, minlength=ns), "n_valid5": nv, "hole_min": hole, "ofi": ofi},
                     index=pd.DatetimeIndex(pd.to_datetime(uniq * DAY + H22, utc=True), name="time"))
    X = X.replace([np.inf, -np.inf], np.nan)
    X["ok"] = ((X["n_valid5"] >= MIN_VALID_5M) & (X["hole_min"] <= MAX_HOLE_MIN)).astype(float)
    X.loc[X["ok"] == 0, "ofi"] = np.nan
    return X


def _ohlc(m1: pd.DataFrame, rule: str) -> pd.DataFrame:
    g = m1.resample(rule, label="left", closed="left", origin="start_day")
    return g.agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna(subset=["open"])


def daily_frame(m1: pd.DataFrame, pip: float) -> pd.DataFrame:
    """The frozen daily frame (see the module docstring) from 1-minute bars in UTC."""
    h1 = _ohlc(m1, "1h").loc[str(FIRST_YEAR):]
    key = (h1.index - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
    g = h1.groupby(key)
    d = pd.DataFrame({"open": g["open"].first(), "high": g["high"].max(), "low": g["low"].min(), "close": g["close"].last(), "n": g.size()})
    d = d[(d["n"] >= 10) & (d.index.dayofweek != 5)]
    idx = d.index
    c, o, hi, lo = d["close"], d["open"], d["high"], d["low"]
    close_time = idx + pd.Timedelta(days=1)
    rv = (np.log(h1["close"]).diff() ** 2).groupby(key).sum().reindex(idx)
    D = pd.DataFrame(index=idx)
    D["close"] = c
    D["ret_1d"] = (np.log(c) - np.log(c.shift(1))) * 1e4
    D["rv_1d_bp"] = np.sqrt(rv) * 1e4
    D["rv_21d_bp"] = np.sqrt(rv.rolling(21).mean()) * 1e4
    D["d1_c_ret"] = D["ret_1d"] / D["rv_1d_bp"].replace(0, np.nan)
    D["d1_c_body"] = (c - o) / (hi - lo).replace(0, np.nan)
    D["d1_c_cir"] = (c - lo) / (hi - lo).replace(0, np.nan) - 0.5
    P = ofi_sessions(m1, pip)
    P.index = P.index.as_unit(idx.unit)
    P = P.reindex(idx)
    D["ofi"], D["n_valid5"], D["hole_min"], D["ok"] = P["ofi"], P["n_valid5"], P["hole_min"], P["ok"]
    D = D.replace([np.inf, -np.inf], np.nan)
    D["w5_ofi"] = D["ofi"].rolling(5, min_periods=3).mean()
    for k in ("c_ret", "c_body", "c_cir"):
        D[f"w5_{k}"] = D[f"d1_{k}"].rolling(5, min_periods=3).mean()
    D["fwd_1d"] = D["ret_1d"].shift(-1)
    D["fwd_5d"] = (np.log(c.shift(-5)) - np.log(c)) * 1e4
    D["close_time"] = close_time
    D["label_end_1d"] = close_time + pd.Timedelta(days=1)
    D["label_end_5d"] = close_time + pd.Timedelta(days=8)
    return D


def build(pairs: list[str] | None = None) -> dict:
    """Raw zips -> M5 parquet, daily frame cache, coverage and timezone tables."""
    info = {}
    CROSS.mkdir(parents=True, exist_ok=True)
    cov = []
    for pair in pairs or list(PAIRS):
        m1, st = load_m1(pair)
        st["tz_check"] = tz_check(m1)
        m5 = _ohlc(m1, "5min").astype("float32")
        m5.to_parquet(CROSS / f"ofi_{pair}_M5.parquet", compression="zstd")
        D = daily_frame(m1, PAIRS[pair])
        D.to_parquet(daily_path(pair))
        st["m5_rows"], st["sessions"] = int(len(m5)), int(len(D))
        info[pair] = st
        yr = D.groupby(D.index.year)
        c = pd.DataFrame({"pair": pair, "sessions": yr.size(), "ok_sessions": yr["ok"].sum().astype(int), "excluded": (yr.size() - yr["ok"].sum()).astype(int),
                          "median_valid5": yr["n_valid5"].median(), "m1_bars": m1.groupby(m1.index.year).size().reindex(yr.size().index)})
        cov.append(c.rename_axis("year").reset_index())
        print(f"{pair}: {st['rows']:,} M1 rows {st['first']} .. {st['last']}, {len(D)} sessions, {int((D['ok'] == 0).sum())} fail the quality rule; "
              f"tz {st['tz_check']['summer_EDT']['modal_minute_utc']} ({st['tz_check']['summer_EDT']['share_at_mode']:.0%}) / "
              f"{st['tz_check']['winter_EST']['modal_minute_utc']} ({st['tz_check']['winter_EST']['share_at_mode']:.0%})", flush=True)
        del m1, m5
    pd.concat(cov, ignore_index=True).to_csv(RES / f"{ARM}_coverage.csv", index=False)
    (RES / f"{ARM}_data.json").write_text(json.dumps(info, indent=1))
    return info


def load_daily(pair: str) -> pd.DataFrame:
    if pair == "eurusd":
        return daily_frame(pd.read_parquet(EUR_M1, columns=["open", "high", "low", "close"]).loc["2002-12-31":], 1e-4)
    return pd.read_parquet(daily_path(pair))


# ================================================================================================ the frozen rule
def _fit(train: pd.DataFrame) -> dict:
    x, C = train["w5_ofi"].values, train[CTRL].values
    ok = ~np.isnan(x) & ~np.isnan(C).any(axis=1)
    beta = np.linalg.lstsq(C[ok], x[ok], rcond=None)[0] if ok.sum() >= MIN_TRAIN_ROWS else np.zeros(C.shape[1])
    e = pd.Series(x - np.nan_to_num(C) @ beta).dropna()
    sd = None if len(e) < MIN_TRAIN_ROWS else (float(e.std()) or 1.0)
    thr = np.inf
    if sd is not None:
        thr = float(np.quantile(((e / sd).clip(-2, 2) / 2).abs(), 0.5))
    return {"beta": beta, "sd": sd, "thr": thr, "target_vol": float(train["rv_21d_bp"].median()), "n_fit": int(ok.sum())}


def _predict(m: dict, test: pd.DataFrame) -> pd.Series:
    if m["sd"] is None:
        return pd.Series(0.0, index=test.index)
    e = test["w5_ofi"] - np.nan_to_num(test[CTRL].values) @ m["beta"]
    z = ((e / m["sd"]).clip(-2, 2) / 2).fillna(0.0)
    s = np.sign(z).where(z.abs() > m["thr"], 0.0)
    vs = (m["target_vol"] / test["rv_21d_bp"].replace(0, np.nan)).clip(upper=1.0).fillna(0.0)
    return s * vs


def positions(D: pd.DataFrame, log: dict | None = None) -> pd.Series:
    def fit(train):
        m = _fit(train)
        if log is not None:
            log[int(train.index.max().year) + 1] = {"beta": [float(b) for b in m["beta"]], "sd": m["sd"], "thr": m["thr"], "target_vol": m["target_vol"], "n_fit": m["n_fit"]}
        return m
    s = walk_forward(D, fit, _predict, label_end=D["label_end_5d"], verbose=False).fillna(0.0)
    return s.rolling(5, min_periods=1).sum() / 5


def evaluate(D: pd.DataFrame, pos: pd.Series, pip: float, cost_pips: float, name: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    pnl = pnl_from_positions(pos, D["fwd_1d"], D["close"], cost_pips=cost_pips * pip / 1e-4)
    pnl = pnl[pnl.index.year >= 2010]
    tbl = report(pnl, periods_per_year=252, name=ARM, n_arms=1)
    tbl.insert(1, "variant", name)
    tbl["cost_pips"] = cost_pips
    f = D["fwd_1d"].reindex(pnl.index)
    for lab, a, b in PERIODS:
        m = (pnl.index.year >= a) & (pnl.index.year <= b) & (pnl["pos"] != 0) & f.notna()
        x, fx = pnl[m], f[m]
        nz = fx != 0
        tbl.loc[tbl["period"] == lab, ["n_active", "hit_net", "hit_sign"]] = [
            int(len(x)), float((x["net_bp"] > 0).mean()) if len(x) else np.nan,
            float((np.sign(x["pos"][nz]) == np.sign(fx[nz])).mean()) if nz.sum() else np.nan]
    yrs = tbl[tbl["period"].str.fullmatch(r"\d{4}")]
    tbl.loc[tbl["period"] == "2010-2026", "years_positive"] = int((yrs["sum_bp"] > 0).sum())
    tbl.loc[tbl["period"] == "2010-2026", "years_total"] = int((yrs["active_frac"] > 0).sum())
    tbl.loc[tbl["period"] == "2010-2026", "turnover_per_year"] = float(pnl["turnover"].sum() / max(1, pnl.index.year.nunique()))
    tbl.loc[tbl["period"] == "2010-2026", "cost_bp_mean"] = float((cost_pips * pip / D["close"].reindex(pnl.index) * 1e4).mean())
    return pnl, tbl


def basket(pnls: dict[str, pd.DataFrame], col: str = "net_bp", unit_vol: bool = False) -> pd.Series:
    """Equal-weight mean across pairs per session; a pair is in the mean of a test year when the harness gave it a
    stream that year (its missing sessions count as 0)."""
    cols = {}
    for p, x in pnls.items():
        s = x[col].copy()
        if unit_vol:
            s = s / s.std()
        cols[p] = s
    J = pd.DataFrame(cols).sort_index()
    live = {}
    for p, x in pnls.items():
        act = x["pos"].abs().groupby(x.index.year).sum()
        live[p] = np.isin(J.index.year, act.index[act > 0].values)          # test years in which the pair has a stream
    live = pd.DataFrame(live, index=J.index)
    num = J.where(live).fillna(0.0).where(live)
    return num.mean(axis=1, skipna=True).dropna()


def _stats(x: pd.Series) -> dict:
    out = {}
    for lab, a, b in PERIODS + (("2010-2015", 2010, 2015),):
        r = _agg(x[(x.index.year >= a) & (x.index.year <= b)], 252)
        out[lab] = (r["sharpe"], r["t"])
    return out


def run_pairs(frames: dict[str, pd.DataFrame], cost_pips: float = 1.2, logs: dict | None = None) -> tuple[dict, dict]:
    pnls, tabs = {}, {}
    for p, D in frames.items():
        lg = {} if logs is not None else None
        pnls[p], tabs[p] = evaluate(D, positions(D, lg), PAIRS.get(p, 1e-4), cost_pips, p)
        if logs is not None:
            logs[p] = lg
    return pnls, tabs


def basket_table(pnls: dict[str, pd.DataFrame], name: str = "basket6", cost_pips: float = 1.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    bk = basket(pnls)
    act = pd.DataFrame({p: x["pos"] for p, x in pnls.items()}).reindex(bk.index).fillna(0.0)
    bp = pd.DataFrame({"net_bp": bk, "pos": (act != 0).any(axis=1).astype(float), "gross_bp": basket(pnls, "gross_bp").reindex(bk.index)})
    tbl = report(bp, periods_per_year=252, name=ARM, n_arms=1)
    tbl.insert(1, "variant", name)
    tbl["cost_pips"] = cost_pips
    for lab, a, b in PERIODS:
        m = (bp.index.year >= a) & (bp.index.year <= b) & (bp["pos"] != 0)
        tbl.loc[tbl["period"] == lab, ["n_active", "hit_net", "hit_sign"]] = [int(m.sum()), float((bp.loc[m, "net_bp"] > 0).mean()), float((bp.loc[m, "gross_bp"] > 0).mean())]
    yrs = tbl[tbl["period"].str.fullmatch(r"\d{4}")]
    tbl.loc[tbl["period"] == "2010-2026", "years_positive"] = int((yrs["sum_bp"] > 0).sum())
    tbl.loc[tbl["period"] == "2010-2026", "years_total"] = int((yrs["n"] > 0).sum())
    return bp, tbl


def pooled(pnls: dict[str, pd.DataFrame], tabs: dict[str, pd.DataFrame]) -> pd.DataFrame:
    rows = []
    for lab, a, b in PERIODS:
        sub = {p: x[(x.index.year >= a) & (x.index.year <= b)] for p, x in pnls.items()}
        u = basket(sub, unit_vol=True)
        ts = np.array([tabs[p].set_index("period").loc[lab, "t"] for p in pnls])
        sr = np.array([tabs[p].set_index("period").loc[lab, "sharpe"] for p in pnls])
        bkt = _agg(basket(sub), 252)
        rows.append({"period": lab, "pooled_t_clustered_by_day": float(u.mean() / u.std() * math.sqrt(len(u))), "stouffer_z_independent": float(ts.sum() / math.sqrt(len(ts))),
                     "basket_sharpe": bkt["sharpe"], "basket_t": bkt["t"], "pairs_positive": int((sr > 0).sum()), "n_pairs": len(sr), "mean_pair_sharpe": float(sr.mean())})
    return pd.DataFrame(rows)


def verdict(pool: pd.DataFrame) -> tuple[str, dict]:
    p = pool.set_index("period")
    c = {"basket_2010_26_positive": bool(p.loc["2010-2026", "basket_sharpe"] > 0), "basket_2016_26_positive": bool(p.loc["2016-2026", "basket_sharpe"] > 0),
         "pooled_t_ge_2": bool(p.loc["2010-2026", "pooled_t_clustered_by_day"] >= 2.0), "at_least_4_of_6_positive": bool(p.loc["2010-2026", "pairs_positive"] >= 4)}
    return ("REPLICATES" if all(c.values()) else "FAILS"), c


# ================================================================================================ EUR/USD reproduction (STEP 0)
def reproduce_eur(cost_pips: float = 1.2, verbose: bool = True) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, dict]:
    """This module's implementation on EUR/USD against arm K's saved control-(a) stream and feature store."""
    D = load_daily("eurusd")
    fs = pd.read_parquet(PROC / "features_daily.parquet", columns=["close", "ret_1d", "rv_1d_bp", "rv_21d_bp", "body_rel", "close_in_range", "fwd_1d", "fwd_5d"])
    ip = pd.read_parquet(PROC / "intraday_path_features.parquet", columns=["ofi", "ofi_5d", "n_valid5", "hole_min", "ok"])
    chk = {"index_equal": bool(D.index.equals(fs.index))}
    for a, b in (("close", fs["close"]), ("ret_1d", fs["ret_1d"]), ("rv_1d_bp", fs["rv_1d_bp"]), ("rv_21d_bp", fs["rv_21d_bp"]), ("d1_c_body", fs["body_rel"]),
                 ("d1_c_cir", fs["close_in_range"] - 0.5), ("fwd_1d", fs["fwd_1d"]), ("fwd_5d", fs["fwd_5d"]), ("ofi", ip["ofi"]), ("w5_ofi", ip["ofi_5d"]),
                 ("n_valid5", ip["n_valid5"]), ("ok", ip["ok"])):
        x, y = D[a].reindex(fs.index), b.reindex(fs.index)
        chk[f"maxdiff_{a}"] = float((x - y).abs().max())
        chk[f"nan_mismatch_{a}"] = int((x.isna() != y.isna()).sum())
    log: dict = {}
    pos = positions(D, log)
    pnl, tbl = evaluate(D, pos, 1e-4, cost_pips, "eurusd")
    ref = pd.read_parquet(RES / "intraday_path_control_resid_stream.parquet")
    chk["max_abs_pos_diff_vs_armK"] = float((pos.reindex(ref.index) - ref["pos"]).abs().max())
    chk["max_abs_net_diff_vs_armK"] = float((pnl["net_bp"].reindex(ref.index) - ref["net_bp"]).abs().max())
    refc = pd.read_csv(RES / "intraday_path_controls.csv")
    refc = refc[(refc["kind"] == "control") & refc["variant"].str.contains("residualised")].set_index("period")
    t = tbl.set_index("period")
    for lab, _, _ in PERIODS:
        chk[f"sharpe_{lab}"] = float(t.loc[lab, "sharpe"]); chk[f"armK_sharpe_{lab}"] = float(refc.loc[lab, "sharpe"])
        chk[f"t_{lab}"] = float(t.loc[lab, "t"])
    if verbose:
        print(json.dumps(chk, indent=1))
    assert all(abs(chk[f"sharpe_{lab}"] - chk[f"armK_sharpe_{lab}"]) < 0.02 for lab, _, _ in PERIODS), "EUR/USD reproduction failed"
    out = pd.DataFrame({"pos": pos, "fwd_bp": D["fwd_1d"], "net_bp": pnl["net_bp"].reindex(D.index)})
    return out[out.index.year >= 2010], tbl, pnl, {"checks": chk, "fitlog": log}


# ================================================================================================ entry point
def load_frames() -> dict[str, pd.DataFrame]:
    return {p: load_daily(p) for p in PAIRS}


def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """The single pre-registered run. Returns (EUR/USD OOS positions of the frozen rule, report DataFrame)."""
    eur_out, eur_tbl, eur_pnl, eur_info = reproduce_eur(cost_pips, verbose=False)
    frames = load_frames()
    logs: dict = {}
    pnls, tabs = run_pairs(frames, cost_pips, logs)
    bp, btbl = basket_table(pnls, "basket6_ex_eur", cost_pips)
    pool = pooled(pnls, tabs)
    verd, crit = verdict(pool)
    rows = [eur_tbl.assign(group="eurusd_reference", final=True)] + [tabs[p].assign(group="pair", final=False) for p in PAIRS] + [btbl.assign(group="basket", final=False)]
    for cst in (0.6, 0.0):                                   # same positions, cost sensitivity only
        pn2, tb2 = run_pairs(frames, cst)
        rows += [tb2[p].assign(group="pair_cost_sensitivity", final=False) for p in PAIRS]
        rows.append(basket_table(pn2, "basket6_ex_eur", cst)[1].assign(group="basket_cost_sensitivity", final=False))
    rep = pd.concat(rows, ignore_index=True)
    rep["verdict"] = verd
    if verbose:
        for nm, tb in [("eurusd", eur_tbl)] + [(p, tabs[p]) for p in PAIRS] + [("basket6", btbl)]:
            r = tb.set_index("period")
            print(f"{nm:8s} 2010-26 SR {r.loc['2010-2026','sharpe']:+.2f} t {r.loc['2010-2026','t']:+.2f} | 2016-26 SR {r.loc['2016-2026','sharpe']:+.2f} t {r.loc['2016-2026','t']:+.2f} | "
                  f"2023-26 SR {r.loc['2023-2026','sharpe']:+.2f} t {r.loc['2023-2026','t']:+.2f} | hit sign {r.loc['2010-2026','hit_sign']:.3f} net {r.loc['2010-2026','hit_net']:.3f} "
                  f"(n {r.loc['2010-2026','n_active']:.0f}) | years + {r.loc['2010-2026','years_positive']:.0f}/{r.loc['2010-2026','years_total']:.0f}", flush=True)
        print(pool.round(3).to_string(index=False))
        print("VERDICT:", verd, crit, flush=True)
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        eur_out.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        B = pd.DataFrame({"basket_net_bp": bp["net_bp"], "basket_gross_bp": bp["gross_bp"]})
        for p in PAIRS:
            B[f"{p}_pos"], B[f"{p}_net_bp"] = pnls[p]["pos"].reindex(B.index), pnls[p]["net_bp"].reindex(B.index)
        B["eurusd_pos"], B["eurusd_net_bp"] = eur_pnl["pos"].reindex(B.index), eur_pnl["net_bp"].reindex(B.index)
        B.to_parquet(RES / f"{ARM}_basket.parquet")
        pool.to_csv(RES / f"{ARM}_pooled.csv", index=False)
        js = {"verdict": verd, "criteria": crit, "eur_checks": eur_info["checks"], "fitlog": {"eurusd": eur_info["fitlog"], **logs}}
        (RES / f"{ARM}_fitlog.json").write_text(json.dumps(js, indent=1, default=float))
    return eur_out["pos"], rep


# ================================================================================================ leak checks (basket)
def _basket_sr(frames: dict[str, pd.DataFrame], cost_pips: float) -> dict:
    pnls, _ = run_pairs(frames, cost_pips)
    return _stats(basket(pnls))


def leak_checks(cost_pips: float = 1.2, n_shuffle: int = 20, seed: int = 0, write: bool = True) -> pd.DataFrame:
    frames = load_frames()
    rows = []
    def add(check, st, **kw):
        rows.append({"check": check, **{f"SR_{k}": v[0] for k, v in st.items()}, **{f"t_{k}": v[1] for k, v in st.items()}, **kw})
    add("actual", _basket_sr(frames, cost_pips))
    for lag, nm in ((1, "features_lag_plus1"), (-1, "lookahead_control_features_lead1"), (-5, "lookahead_control_features_lead5")):
        fl = {}
        for p, D in frames.items():
            Dl = D.copy(); Dl[FCOLS] = D[FCOLS].shift(lag); fl[p] = Dl
        add(nm, _basket_sr(fl, cost_pips))
    # shuffled labels: one permutation of the common session calendar, applied to every pair
    cal = pd.DatetimeIndex(sorted(set().union(*[set(D.index) for D in frames.values()])))
    rng = np.random.default_rng(seed)
    sh = {c: [] for c in (cost_pips, 0.0)}
    for k in range(n_shuffle):
        perm = rng.permutation(len(cal))
        fs = {}
        for p, D in frames.items():
            f1 = pd.Series(D["fwd_1d"].reindex(cal).values[perm], index=cal).reindex(D.index)
            Ds = D.copy()
            Ds["fwd_1d"] = f1
            Ds["fwd_5d"] = f1[::-1].rolling(5, min_periods=5).sum()[::-1]
            fs[p] = Ds
        for c in sh:
            st = _basket_sr(fs, c)
            sh[c].append([st[lab][0] for lab, _, _ in PERIODS])
            if c == cost_pips and k < 5:
                add(f"shuffled_labels_{k}", st)
    for c, v in sh.items():
        v = np.array(v)
        rows.append({"check": f"shuffled_labels_summary_cost{c}", **{f"SR_{lab}": v[:, j].mean() for j, (lab, _, _) in enumerate(PERIODS)},
                     **{f"sd_{lab}": v[:, j].std() for j, (lab, _, _) in enumerate(PERIODS)}, "n_perm": n_shuffle})
    out = pd.DataFrame(rows)
    if write:
        out.to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
    return out


def incremental(write: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Round-3 incremental test for the EUR/USD stream (run only if the replication succeeds)."""
    from eurusd.arms.meta import combine, report_combo, load_arm_daily
    tabs = []
    for name, arms in (("two_way", ["weak_signals", "regime_trend"]), ("three_way", ["weak_signals", "regime_trend", ARM])):
        pnl, w = combine(arms, "EW")
        t = report_combo(pnl, name, len(arms))
        t["years_arm_in"] = int((w[ARM] > 0).sum()) if ARM in w else 0
        tabs.append(t)
    inc = pd.concat(tabs, ignore_index=True)
    mine = load_arm_daily(ARM)
    rows = []
    for nm in ("weak_signals", "regime_trend"):
        J = pd.concat([mine.rename("a"), load_arm_daily(nm).rename("b")], axis=1).dropna()
        for lab, a, b in PERIODS:
            x = J[(J.index.year >= a) & (J.index.year <= b)]
            rows.append({"other": nm, "period": lab, "corr_daily_pnl": x.a.corr(x.b), "corr_monthly_pnl": x.a.resample("ME").sum().corr(x.b.resample("ME").sum())})
    cor = pd.DataFrame(rows)
    if write:
        inc.to_csv(RES / f"{ARM}_incremental.csv", index=False)
        cor.to_csv(RES / f"{ARM}_correlations.csv", index=False)
    return inc, cor


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "all"
    cost = float(sys.argv[2]) if len(sys.argv) > 2 else 1.2
    if cmd == "eur":
        reproduce_eur(cost)
    if cmd == "download":
        print(download().groupby(["pair", "status"]).size())
    if cmd in ("build", "all"):
        build()
    if cmd in ("run", "all"):
        _, rep = run(cost)
        if rep["verdict"].iloc[0] == "REPLICATES":
            inc, cor = incremental()
            print(inc[inc.period.isin(["2010-2026", "2016-2026", "2023-2026"])].round(3).to_string(index=False))
            print(cor.round(3).to_string(index=False))
    if cmd in ("leak", "all"):
        print(leak_checks(cost).round(3).to_string(index=False))
