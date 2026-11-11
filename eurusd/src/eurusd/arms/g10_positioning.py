"""Arm F "g10_positioning": out-of-sample validation of "follow the speculative positioning trend" on OTHER
currencies, and a dollar-wide positioning signal for EUR/USD.

The one effect that survived rounds 1-2 is  position = sign(z52 of CFTC non-commercial net / open interest) x vol scale
on EUR/USD (regime_trend `cot_uncond`: net Sharpe 0.70 / 0.60 / 0.31 for 2010-26 / 2016-26 / 2023-26). The rule was
found on EUR/USD, so that record is contaminated. This arm applies the IDENTICAL rule with IDENTICAL parameters to
currencies the project never looked at, then asks whether dollar-wide positioning helps the EUR/USD stream.

PROTOCOL (everything in this docstring was written BEFORE any strategy result was computed)
------------------------------------------------------------------------------------------
Data
* CFTC legacy futures-only COT (`data/raw/cftc/deacot*.zip`, 1999-2026) and TFF (`fut_fin_txt_*.zip`, 2010-2026):
  EUR 099741, GBP 096742, JPY 097741, CHF 092741, AUD 232741, CAD 090741, NZD 112741, MXN 095741. Every code is
  verified against the market name in every file (`build_cot` asserts). net = (long - short) / open interest.
  A report dated Tuesday T is stamped T + 6 days and then lagged one more calendar day (`featstore._align_lagged`),
  i.e. it is first used at the close of T + 7 - exactly the EUR/USD feature-store convention.
* Prices: Federal Reserve H.10 noon New York buying rates from FRED (DEXUSEU, DEXUSUK, DEXJPUS, DEXSZUS, DEXUSAL,
  DEXCAUS, DEXUSNZ, DEXMXUS), converted to USD per unit of foreign currency (= the futures direction), one common
  calendar. PRIMARY price source for the cross-currency test (declared here; chosen for data quality only: official,
  no roll jumps, 2003-2026 for all eight). Sensitivity: Yahoo continuous front futures (6E 6B 6J 6S 6A 6C 6N 6M =F).
  Returns are SPOT log returns in bp, no carry, exactly as EUR/USD `fwd_1d` in the feature store; a carry-adjusted
  sensitivity adds (foreign - US 3-month interbank rate)/252 per day (FRED IR3TIB01xxM156N, lagged 45 days).
* Volatility: rv_21d_bp = sqrt(mean of the last 21 squared daily log returns) in bp (the EUR/USD store uses hourly
  realised variance; only daily data exist for the other currencies - the EUR row on H.10 data shows the difference).

Rule (fixed, no parameter is fitted except the training-median volatility, exactly as regime_trend `cot_uncond`)
  z = (net - mean_52w(net)) / sd_52w(net);  pos = sign(z) * clip(median_train(rv_21d_bp) / rv_21d_bp, 0, 1.5)
  walk-forward through `eurusd.wf` (yearly expanding window, test years 2010-2026), cost = 1.2 pips of the conventional
  pair per unit turnover (GBPUSD, USDJPY [pip 0.01], USDCHF, AUDUSD, USDCAD, NZDUSD 1.2 pips; USDMXN 30 pips because
  1.2 pips of USDMXN is not a real spread), with a 2x-cost sensitivity.

Cross-currency tests (fixed rule, nothing selected): 7 currencies, EW basket of the 5 majors (GBP JPY CHF AUD CAD),
  EW basket of all 7 non-EUR, EW basket of 8 incl. EUR; the same with TFF leveraged-funds and asset-manager net
  positions; pooled evidence = t-stat of the EW ex-EUR basket (respects cross-correlation) + count of positive
  currencies. Diagnostics (flagged, not candidates): sign(126-day return) time-series momentum with the same vol
  scaling (is positioning just trend?), futures prices, carry-adjusted returns, 2x cost.

Cross-sectional versions on the 6 majors (EUR GBP JPY CHF AUD CAD), each leg vol-scaled as above, 3 variants:
  `xs_rank`   weight_i = (rank_i - mean rank) / (sum of |.|/2)   (long high z, short low z, gross 2)
  `xs_demean` weight_i = sign(z_i - cross-sectional mean z)
  `xs_top2`   long the 2 highest z, short the 2 lowest (weights +-1/2)
plus `usd_factor`: every currency gets sign(mean z across the 6) (the pure dollar-positioning trend on the basket).

EUR/USD variants (feature-store grid, label fwd_1d, vol scale = clip(median_train(rv_21d_bp)/rv_21d_bp, 0, 1.5),
1.2 pips; 10 variants, the cap is 12):
   1 `eur_own`        sign(z_EUR)                               reference = regime_trend cot_uncond, NOT eligible
   2 `usd5`           sign(mean z of GBP JPY CHF AUD CAD)       aggregate USD positioning ex EUR
   3 `usd6`           sign(mean z of EUR + the 5)
   4 `usd7x`          sign(mean z of the 5 + NZD + MXN)
   5 `eur_rel`        sign(z_EUR - mean z of the 5)             EUR-specific positioning
   6 `agree`          0.5 * (sign(z_EUR) + sign(mean z of the 5))   long/short only when both agree
   7 `breadth5`       mean of sign(z_i) over the 5              continuous in [-1, 1]
   8 `usd5_notional`  sign(z52 of sum_i net_i*size_i*price_i / sum_i OI_i*size_i*price_i over the 5)  (USD-notional
                      weighted aggregate, the usual "net USD position" measure)
   9 `usd5_lev`       sign(mean z of TFF leveraged funds, the 5)  (data from 2010, signal from mid-2011)
  10 `usd5_am`        sign(mean z of TFF asset managers, the 5)
SELECTION RULE: the arm's EUR/USD stream is the variant among 2..10 with the highest 2010-2015 walk-forward net
Sharpe at 1.2 pips. Nothing is chosen on 2016-2026 or 2023-2026.
Incremental test: `meta.combine(["weak_signals","regime_trend","g10_positioning"],"EW")` vs the two-way combination,
both through `report_combo`, plus daily-P&L correlations with the two survivors.
Leak checks: shuffled labels, signal shifted (lag and lead), list of inputs and their correlation with the label.
"""
from __future__ import annotations

import io
import json
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from eurusd.wf import walk_forward, pnl_from_positions, report, _agg

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "processed" / "features_daily.parquet"
MACRO = ROOT / "data" / "macro"
CROSS = ROOT / "data" / "processed" / "cross"
RAWCFTC = ROOT / "data" / "raw" / "cftc"
OUT = ROOT / "experiments" / "results" / "arms"
ARM = "g10_positioning"

Z_WINDOW = 52
VOL_CAP = 1.5
COT_LAG_DAYS = 6
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/120.0 Safari/537.36")

# code: CFTC contract market code; names: allowed prefixes of the market name (asserted for every row);
# h10: FRED series, h10_inv: series quoted as foreign per USD; pip/conv: conventional pair for the cost;
# cost_mult: multiple of the headline pips charged (MXN); size: CME contract size in foreign currency.
CCY = {
    "eur": dict(code="099741", names=("EURO FX - ",), fut="6E=F", h10="DEXUSEU", h10_inv=False, pip=1e-4,
                conv_inv=False, cost_mult=1.0, size=125_000, rate="IR3TIB01EZM156N"),
    "gbp": dict(code="096742", names=("POUND STERLING - ", "BRITISH POUND STERLING - ", "BRITISH POUND - "), fut="6B=F",
                h10="DEXUSUK", h10_inv=False, pip=1e-4, conv_inv=False, cost_mult=1.0, size=62_500, rate="IR3TIB01GBM156N"),
    "jpy": dict(code="097741", names=("JAPANESE YEN - ",), fut="6J=F", h10="DEXJPUS", h10_inv=True, pip=1e-2,
                conv_inv=True, cost_mult=1.0, size=12_500_000, rate="IR3TIB01JPM156N"),
    "chf": dict(code="092741", names=("SWISS FRANC - ",), fut="6S=F", h10="DEXSZUS", h10_inv=True, pip=1e-4,
                conv_inv=True, cost_mult=1.0, size=125_000, rate="IR3TIB01CHM156N"),
    "aud": dict(code="232741", names=("AUSTRALIAN DOLLAR - ", "AUSTRALIAN DOLLARS - "), fut="6A=F", h10="DEXUSAL",
                h10_inv=False, pip=1e-4, conv_inv=False, cost_mult=1.0, size=100_000, rate="IR3TIB01AUM156N"),
    "cad": dict(code="090741", names=("CANADIAN DOLLAR - ",), fut="6C=F", h10="DEXCAUS", h10_inv=True, pip=1e-4,
                conv_inv=True, cost_mult=1.0, size=100_000, rate="IR3TIB01CAM156N"),
    "nzd": dict(code="112741", names=("NEW ZEALAND DOLLAR - ", "NEW ZEALAND DOLLARS - ", "NZ DOLLAR - "), fut="6N=F",
                h10="DEXUSNZ", h10_inv=False, pip=1e-4, conv_inv=False, cost_mult=1.0, size=100_000, rate="IR3TIB01NZM156N"),
    "mxn": dict(code="095741", names=("MEXICAN PESO - ",), fut="6M=F", h10="DEXMXUS", h10_inv=True, pip=1e-4,
                conv_inv=True, cost_mult=25.0, size=500_000, rate="IR3TIB01MXM156N"),
}
MAJ5 = ["gbp", "jpy", "chf", "aud", "cad"]
OTHERS7 = MAJ5 + ["nzd", "mxn"]
MAJ6 = ["eur"] + MAJ5
ALL8 = ["eur"] + OTHERS7
US_RATE = "IR3TIB01USM156N"


# ============================================================================= data builders (run once)
def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.strip().str.replace(",", ""), errors="coerce")


def _read_cot_zip(p: Path) -> pd.DataFrame:
    with zipfile.ZipFile(p) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".txt")]
        with z.open(names[0]) as fh:
            df = pd.read_csv(fh, dtype=str, low_memory=False, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    return df


def build_cot(verbose: bool = True) -> dict:
    """Parse the CFTC zips for all eight currencies (same columns as `macro_fetch.build_cftc`), verify the market
    name of every row against the code, write data/macro/cot_<ccy>_legacy.csv and cot_<ccy>_tff.csv.
    EUR is parsed too and compared with the existing cot_eurofx_*.csv (must be identical); no EUR file is written."""
    codes = {v["code"]: k for k, v in CCY.items()}
    leg, tff = [], []
    for p in sorted(RAWCFTC.glob("deacot*.zip")):
        df = _read_cot_zip(p)
        cc = next(c for c in df.columns if "Contract Market Code" in c)
        df = df[df[cc].astype(str).str.strip().isin(codes)].copy()
        df["_ccy"] = df[cc].astype(str).str.strip().map(codes)
        leg.append(df)
    for p in sorted(RAWCFTC.glob("fut_fin_txt_*.zip")):
        df = _read_cot_zip(p)
        df = df[df["CFTC_Contract_Market_Code"].astype(str).str.strip().isin(codes)].copy()
        df["_ccy"] = df["CFTC_Contract_Market_Code"].astype(str).str.strip().map(codes)
        tff.append(df)
    l = pd.concat(leg, ignore_index=True)
    t = pd.concat(tff, ignore_index=True)
    name_col = next(c for c in l.columns if "Market and Exchange" in c)
    date_col = next(c for c in l.columns if "YYYY-MM-DD" in c)

    def col(prefix: str) -> str:
        return next(c for c in l.columns if c.strip().startswith(prefix))

    info = {}
    for ccy, meta in CCY.items():
        # ---------------- legacy
        g = l[l["_ccy"] == ccy]
        nm = g[name_col].str.strip()
        assert nm.str.startswith(meta["names"]).all(), (ccy, nm.unique())
        out = pd.DataFrame({"report_date": pd.to_datetime(g[date_col].str.strip()).dt.strftime("%Y-%m-%d")})
        out["open_interest"] = _num(g[col("Open Interest (All)")]).values
        out["noncomm_long"] = _num(g[col("Noncommercial Positions-Long (All)")]).values
        out["noncomm_short"] = _num(g[col("Noncommercial Positions-Short (All)")]).values
        out["noncomm_spread"] = _num(g[col("Noncommercial Positions-Spreading (All)")]).values
        out["comm_long"] = _num(g[col("Commercial Positions-Long (All)")]).values
        out["comm_short"] = _num(g[col("Commercial Positions-Short (All)")]).values
        out["nonrept_long"] = _num(g[col("Nonreportable Positions-Long (All)")]).values
        out["nonrept_short"] = _num(g[col("Nonreportable Positions-Short (All)")]).values
        for k in ["noncomm", "comm", "nonrept"]:
            out[f"{k}_net"] = out[f"{k}_long"] - out[f"{k}_short"]
            out[f"{k}_net_pct_oi"] = (100 * out[f"{k}_net"] / out["open_interest"]).round(2)
        out = out.sort_values("report_date").drop_duplicates("report_date").reset_index(drop=True)
        # ---------------- TFF
        g2 = t[t["_ccy"] == ccy]
        nm2 = g2["Market_and_Exchange_Names"].str.strip()
        assert nm2.str.startswith(meta["names"]).all(), (ccy, nm2.unique())
        rd = g2["Report_Date_as_YYYY-MM-DD"].combine_first(g2["Report_Date_as_MM_DD_YYYY"]) \
            if "Report_Date_as_MM_DD_YYYY" in g2 else g2["Report_Date_as_YYYY-MM-DD"]
        o2 = pd.DataFrame({"report_date": pd.to_datetime(rd.str.strip(), format="%Y-%m-%d").dt.strftime("%Y-%m-%d")})
        cols = {"Open_Interest_All": "open_interest",
                "Dealer_Positions_Long_All": "dealer_long", "Dealer_Positions_Short_All": "dealer_short",
                "Asset_Mgr_Positions_Long_All": "asset_mgr_long", "Asset_Mgr_Positions_Short_All": "asset_mgr_short",
                "Lev_Money_Positions_Long_All": "lev_funds_long", "Lev_Money_Positions_Short_All": "lev_funds_short",
                "Other_Rept_Positions_Long_All": "other_rept_long", "Other_Rept_Positions_Short_All": "other_rept_short",
                "NonRept_Positions_Long_All": "nonrept_long", "NonRept_Positions_Short_All": "nonrept_short"}
        for a, b in cols.items():
            o2[b] = _num(g2[a]).values
        for k in ["dealer", "asset_mgr", "lev_funds", "other_rept", "nonrept"]:
            o2[f"{k}_net"] = o2[f"{k}_long"] - o2[f"{k}_short"]
            o2[f"{k}_net_pct_oi"] = (100 * o2[f"{k}_net"] / o2["open_interest"]).round(2)
        o2 = o2.sort_values("report_date").drop_duplicates("report_date").reset_index(drop=True)
        if ccy == "eur":
            ref = pd.read_csv(MACRO / "cot_eurofx_legacy.csv")
            m = out.merge(ref, on="report_date", suffixes=("", "_ref"))
            assert len(m) == len(ref) == len(out) and (m["noncomm_net"] == m["noncomm_net_ref"]).all() \
                and (m["open_interest"] == m["open_interest_ref"]).all(), "EUR parse differs from cot_eurofx_legacy.csv"
            ref2 = pd.read_csv(MACRO / "cot_eurofx_tff.csv")
            m2 = o2.merge(ref2, on="report_date", suffixes=("", "_ref"))
            assert len(m2) == len(ref2) == len(o2) and (m2["lev_funds_net"] == m2["lev_funds_net_ref"]).all()
        else:
            out.to_csv(MACRO / f"cot_{ccy}_legacy.csv", index=False, float_format="%.6g")
            o2.to_csv(MACRO / f"cot_{ccy}_tff.csv", index=False, float_format="%.6g")
        d = pd.to_datetime(out["report_date"])
        gaps = d.diff().dt.days.dropna()
        info[ccy] = {"code": meta["code"], "names": sorted(nm.unique()), "legacy_rows": len(out),
                     "legacy_first": out.report_date.iloc[0], "legacy_last": out.report_date.iloc[-1],
                     "legacy_gaps_gt7d": int((gaps > 7).sum()), "legacy_max_gap_days": int(gaps.max()),
                     "legacy_rows_2003on": int((d >= "2003-01-01").sum()),
                     "legacy_gaps_gt7d_2003on": int((gaps[d.iloc[1:].values >= np.datetime64("2003-01-01")] > 7).sum()),
                     "tff_rows": len(o2), "tff_first": o2.report_date.iloc[0], "tff_last": o2.report_date.iloc[-1]}
        if verbose:
            print(ccy, info[ccy], flush=True)
    return info


def _fred(series: str) -> pd.DataFrame:
    # FRED answers curl through the session proxy but drops python-requests connections (2026-11-11), hence curl.
    import subprocess
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    txt = subprocess.run(["curl", "-sS", "-f", "-m", "120", url], capture_output=True, text=True, check=True).stdout
    if not txt.startswith("observation_date"):
        raise RuntimeError(f"unexpected FRED payload for {series}: {txt[:60]!r}")
    d = pd.read_csv(io.StringIO(txt))
    d.columns = ["date", "value"]
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    return d.dropna().reset_index(drop=True)


def _yahoo_daily(symbol: str, start: str = "2000-01-01") -> pd.DataFrame:
    import requests
    from urllib.parse import quote
    p1 = int(pd.Timestamp(start, tz="UTC").timestamp())
    p2 = int(pd.Timestamp.now(tz="UTC").timestamp())
    last = None
    for attempt in range(5):
        for host in ("query1", "query2"):
            r = requests.get(f"https://{host}.finance.yahoo.com/v8/finance/chart/{quote(symbol, safe='')}",
                             params={"period1": p1, "period2": p2, "interval": "1d"}, headers={"User-Agent": UA}, timeout=60)
            if r.status_code == 200:
                res = r.json()["chart"]["result"][0]
                q = res["indicators"]["quote"][0]
                df = pd.DataFrame({k: q.get(k) for k in ("open", "high", "low", "close", "volume")},
                                  index=pd.to_datetime(res["timestamp"], unit="s", utc=True))
                df.index.name = "time"
                return df.dropna(subset=["close"])
            last = f"HTTP {r.status_code}"
        time.sleep(10 * (attempt + 1))
    raise RuntimeError(f"yahoo {symbol}: {last}")


def fetch_prices(verbose: bool = True) -> None:
    """FRED H.10 spot (data/macro/fred_DEX*.csv), 3-month interbank rates (fred_IR3TIB01*.csv) and Yahoo front
    futures (data/processed/cross/g10fut_<ccy>_D1.parquet)."""
    for s in [m["h10"] for m in CCY.values()] + [m["rate"] for m in CCY.values()] + [US_RATE]:
        p = MACRO / f"fred_{s}.csv"
        if p.exists():
            continue
        try:
            d = _fred(s)
        except Exception as e:  # noqa: BLE001
            print(f"  FRED {s} failed: {e}")
            continue
        d.to_csv(p, index=False)
        if verbose:
            print(f"  fred {s}: {len(d)} rows {d.date.iloc[0]}..{d.date.iloc[-1]}", flush=True)
        time.sleep(0.5)
    for ccy, m in CCY.items():
        p = CROSS / f"g10fut_{ccy}_D1.parquet"
        if p.exists():
            continue
        d = _yahoo_daily(m["fut"])
        d.to_parquet(p)
        if verbose:
            print(f"  yahoo {m['fut']}: {len(d)} rows {d.index[0].date()}..{d.index[-1].date()} last {d.close.iloc[-1]:.6g}", flush=True)
        time.sleep(2)


# ============================================================================= loaders
def _align_lagged(s: pd.Series, idx: pd.DatetimeIndex, lag_days: int = 1) -> pd.Series:
    """Identical to featstore._align_lagged: last observation stamped <= date - lag_days."""
    target = pd.DatetimeIndex(idx) - pd.Timedelta(days=lag_days)
    return pd.Series(s.reindex(s.index.union(target)).sort_index().ffill().reindex(target).values, index=idx)


def load_cot(ccy: str, kind: str = "noncomm") -> pd.DataFrame:
    """Weekly frame indexed by report date: net (contracts), oi, ratio = net / oi."""
    if kind == "noncomm":
        f = MACRO / ("cot_eurofx_legacy.csv" if ccy == "eur" else f"cot_{ccy}_legacy.csv")
        d = pd.read_csv(f, parse_dates=["report_date"]).set_index("report_date")
        net = d.noncomm_long - d.noncomm_short
    else:
        f = MACRO / ("cot_eurofx_tff.csv" if ccy == "eur" else f"cot_{ccy}_tff.csv")
        d = pd.read_csv(f, parse_dates=["report_date"]).set_index("report_date")
        g = {"lev": "lev_funds", "am": "asset_mgr"}[kind]
        net = d[f"{g}_long"] - d[f"{g}_short"]
    return pd.DataFrame({"net": net, "oi": d.open_interest, "ratio": net / d.open_interest})


def z52(ratio: pd.Series) -> pd.Series:
    """Exactly the feature-store formula (rolling over weekly report rows)."""
    return (ratio - ratio.rolling(Z_WINDOW).mean()) / ratio.rolling(Z_WINDOW).std()


def stamped_z(ccy: str, kind: str = "noncomm", stamp_days: int = COT_LAG_DAYS) -> pd.Series:
    z = z52(load_cot(ccy, kind)["ratio"])
    z.index = z.index + pd.Timedelta(days=stamp_days)
    return z


def load_px(src: str = "h10") -> pd.DataFrame:
    """Daily panel, USD per unit of foreign currency (futures direction), naive date index (H.10 calendar)."""
    h = {}
    for ccy, m in CCY.items():
        s = pd.read_csv(MACRO / f"fred_{m['h10']}.csv", parse_dates=["date"]).set_index("date")["value"].astype(float)
        h[ccy] = 1.0 / s if m["h10_inv"] else s
    h10 = pd.DataFrame(h).loc["2003-01-01":].dropna(how="all")
    if src == "h10":
        return h10
    f = {}
    for ccy in CCY:
        s = pd.read_parquet(CROSS / f"g10fut_{ccy}_D1.parquet")["close"]
        s.index = s.index.tz_convert("America/New_York").normalize().tz_localize(None)
        f[ccy] = s[~s.index.duplicated(keep="last")]
    fut = pd.DataFrame(f).sort_index().ffill(limit=3)
    return fut.reindex(h10.index, method="ffill").loc["2003-01-01":]


def carry_bp(px_index: pd.DatetimeIndex) -> pd.DataFrame:
    """Daily carry of a long foreign-currency position in bp: (r_foreign - r_us) / 252, monthly 3m interbank rates
    stamped at month start and lagged 45 days (they accrue in real time; the lag only avoids using a monthly average
    before the month is over)."""
    us = pd.read_csv(MACRO / f"fred_{US_RATE}.csv", parse_dates=["date"]).set_index("date")["value"]
    out = {}
    for ccy, m in CCY.items():
        r = pd.read_csv(MACRO / f"fred_{m['rate']}.csv", parse_dates=["date"]).set_index("date")["value"]
        d = (r - us).dropna()
        out[ccy] = _align_lagged(d, px_index, 45).values * 100.0 / 252.0
    return pd.DataFrame(out, index=px_index)


def ccy_frame(ccy: str, px: pd.DataFrame, kind: str = "noncomm", stamp_days: int = COT_LAG_DAYS,
              carry: pd.DataFrame | None = None) -> pd.DataFrame:
    """One row per H.10 date D (17:00 UTC ~ noon New York): decision with data stamped <= D-1, earning D -> D+1."""
    p = px[ccy].dropna()
    dates = pd.DatetimeIndex(p.index)
    idx = (dates + pd.Timedelta(hours=17)).tz_localize("UTC")
    lp = np.log(p.values)
    df = pd.DataFrame(index=idx)
    df["px"] = p.values
    fwd = np.r_[np.diff(lp), np.nan] * 1e4
    if carry is not None:
        fwd = fwd + carry[ccy].reindex(dates).fillna(0.0).values
    df["fwd_1d"] = fwd
    df["label_end"] = idx[1:].append(pd.DatetimeIndex([idx[-1] + pd.Timedelta(days=3)]))   # tz-aware, known at the next fix
    r = pd.Series(np.r_[np.nan, np.diff(lp)], index=idx)
    df["rv_21d_bp"] = np.sqrt((r ** 2).rolling(21).mean()) * 1e4
    df["ret_126d"] = pd.Series(lp, index=idx).diff(126) * 1e4
    df["z"] = _align_lagged(stamped_z(ccy, kind, stamp_days), dates, 1).values
    m = CCY[ccy]
    conv = 1.0 / df["px"] if m["conv_inv"] else df["px"]
    df["cost_px"] = conv * (1e-4 / m["pip"]) / m["cost_mult"]      # pnl_from_positions: cost_bp = cost_pips / cost_px
    return df


# ============================================================================= the rule
def rule_positions(df: pd.DataFrame, sig: pd.Series, label_end: pd.Series, rv_col: str = "rv_21d_bp") -> pd.Series:
    """pos = sig * clip(median_train(rv) / rv, 0, 1.5); the training median is the only fitted quantity."""
    d = df.assign(_sig=sig.reindex(df.index).values)

    def fit(train: pd.DataFrame) -> float:
        return float(train[rv_col].median())

    def predict(med: float, test: pd.DataFrame) -> pd.Series:
        return (test["_sig"].fillna(0.0) * (med / test[rv_col]).clip(0, VOL_CAP).fillna(0.0)).clip(-1, 1)

    return walk_forward(d, fit, predict, label_end=label_end, verbose=False).fillna(0.0)


def _pnl(df: pd.DataFrame, pos: pd.Series, cost_pips: float) -> pd.DataFrame:
    out = pnl_from_positions(pos, df["fwd_1d"], df["cost_px"], cost_pips=cost_pips)
    return out[out.index.year >= 2010]


def _tbl(pnl: pd.DataFrame, variant: str, group: str, cost_pips: float, n_arms: int = 1, diagnostic: bool = False) -> pd.DataFrame:
    t = report(pnl, periods_per_year=252, name=ARM, n_arms=n_arms)
    t.insert(1, "variant", variant)
    t.insert(2, "group", group)
    t.insert(3, "cost_pips", cost_pips)
    t["diagnostic"] = diagnostic
    return t


def _basket(pnls: dict, members: list[str], how: str = "mean") -> pd.DataFrame:
    net = pd.DataFrame({c: pnls[c]["net_bp"] for c in members}).fillna(0.0)
    pos = pd.DataFrame({c: pnls[c]["pos"] for c in members}).fillna(0.0)
    agg = net.mean(axis=1) if how == "mean" else net.sum(axis=1)
    return pd.DataFrame({"net_bp": agg, "pos": pos.abs().mean(axis=1)})


def _xs_weights(Z: pd.DataFrame, kind: str) -> pd.DataFrame:
    ok = Z.notna().all(axis=1)
    if kind == "xs_rank":
        rk = Z.rank(axis=1)
        w = rk.sub(rk.mean(axis=1), axis=0)
        w = w.div(w.abs().sum(axis=1) / 2.0, axis=0)
    elif kind == "xs_demean":
        w = np.sign(Z.sub(Z.mean(axis=1), axis=0))
    elif kind == "xs_top2":
        rk = Z.rank(axis=1)
        n = Z.shape[1]
        w = (rk >= n - 1).astype(float) * 0.5 - (rk <= 2).astype(float) * 0.5
    elif kind == "usd_factor":
        w = pd.DataFrame(np.repeat(np.sign(Z.mean(axis=1)).values[:, None], Z.shape[1], axis=1), index=Z.index, columns=Z.columns)
    else:
        raise ValueError(kind)
    return w.where(ok, 0.0)


# ============================================================================= cross-currency study
def cross_currency(cost_pips: float = 1.2, verbose: bool = True) -> dict:
    px = load_px("h10")
    frames = {c: ccy_frame(c, px) for c in ALL8}
    tables, pnls, summ = [], {}, {}
    # ---- fixed rule per currency, legacy non-commercial (headline), 1x and 2x cost
    for c in ALL8:
        f = frames[c]
        pos = rule_positions(f, np.sign(f["z"]), f["label_end"])
        for cp in (cost_pips, 2 * cost_pips):
            p = _pnl(f, pos, cp)
            tables.append(_tbl(p, f"ccy_{c}", "currency", cp))
            if cp == cost_pips:
                pnls[c] = p
    baskets = {"basket5_majors_ex_eur": MAJ5, "basket7_ex_eur": OTHERS7, "basket8_incl_eur": ALL8}
    for name, mem in baskets.items():
        pnls[name] = _basket(pnls, mem)
        tables.append(_tbl(pnls[name], name, "basket", cost_pips))
    # 2x cost baskets
    for name, mem in baskets.items():
        p2 = {c: _pnl(frames[c], rule_positions(frames[c], np.sign(frames[c]["z"]), frames[c]["label_end"]), 2 * cost_pips) for c in mem}
        tables.append(_tbl(_basket(p2, mem), name, "basket", 2 * cost_pips))
    # ---- TFF leveraged funds / asset managers (signal from mid-2011)
    for kind in ("lev", "am"):
        pk = {}
        for c in ALL8:
            f = ccy_frame(c, px, kind=kind)
            pk[c] = _pnl(f, rule_positions(f, np.sign(f["z"]), f["label_end"]), cost_pips)
            tables.append(_tbl(pk[c], f"ccy_{c}_{kind}", f"currency_tff_{kind}", cost_pips))
        for name, mem in baskets.items():
            pnls[f"{name}_{kind}"] = _basket(pk, mem)
            tables.append(_tbl(pnls[f"{name}_{kind}"], f"{name}_{kind}", f"basket_tff_{kind}", cost_pips))
    # ---- cross-sectional versions on the 6 majors
    Z6 = pd.DataFrame({c: frames[c]["z"] for c in MAJ6})
    for kind in ("xs_rank", "xs_demean", "xs_top2", "usd_factor"):
        W = _xs_weights(Z6, kind)
        pk = {c: _pnl(frames[c], rule_positions(frames[c], W[c], frames[c]["label_end"]), cost_pips) for c in MAJ6}
        pnls[kind] = _basket(pk, MAJ6, how="sum" if kind in ("xs_rank", "xs_top2") else "mean")
        tables.append(_tbl(pnls[kind], kind, "cross_sectional", cost_pips))
    # ---- diagnostics: momentum, futures prices, carry, risk-parity basket
    pm = {}
    for c in ALL8:
        f = frames[c]
        pm[c] = _pnl(f, rule_positions(f, np.sign(f["ret_126d"]), f["label_end"]), cost_pips)
        tables.append(_tbl(pm[c], f"mom126_{c}", "diag_momentum", cost_pips, diagnostic=True))
    pnls["mom126_basket7"] = _basket(pm, OTHERS7)
    tables.append(_tbl(pnls["mom126_basket7"], "mom126_basket7_ex_eur", "diag_momentum", cost_pips, diagnostic=True))
    for c in ALL8:
        pnls[f"mom126_{c}"] = pm[c]
    pxf = load_px("fut")
    pf = {}
    for c in ALL8:
        f = ccy_frame(c, pxf)
        pf[c] = _pnl(f, rule_positions(f, np.sign(f["z"]), f["label_end"]), cost_pips)
        tables.append(_tbl(pf[c], f"fut_{c}", "diag_futures_px", cost_pips, diagnostic=True))
    tables.append(_tbl(_basket(pf, OTHERS7), "fut_basket7_ex_eur", "diag_futures_px", cost_pips, diagnostic=True))
    cb = carry_bp(px.index)
    pc = {}
    for c in ALL8:
        f = ccy_frame(c, px, carry=cb)
        pc[c] = _pnl(f, rule_positions(f, np.sign(f["z"]), f["label_end"]), cost_pips)
        tables.append(_tbl(pc[c], f"carry_{c}", "diag_carry_adj", cost_pips, diagnostic=True))
    tables.append(_tbl(_basket(pc, OTHERS7), "carry_basket7_ex_eur", "diag_carry_adj", cost_pips, diagnostic=True))
    # risk-parity: each currency's P&L divided by its own training-median vol (walk-forward), rescaled
    rp = {}
    for c in OTHERS7:
        f = frames[c]
        med = walk_forward(f, lambda tr: float(tr["rv_21d_bp"].median()), lambda m, te: pd.Series(m, index=te.index),
                           label_end=f["label_end"], verbose=False)
        q = pnls[c].copy()
        q["net_bp"] = q["net_bp"] / med.reindex(q.index) * 60.0
        rp[c] = q
    tables.append(_tbl(_basket(rp, OTHERS7), "basket7_ex_eur_riskparity", "diag_riskparity", cost_pips, diagnostic=True))
    rep = pd.concat(tables, ignore_index=True)
    return {"frames": frames, "pnls": pnls, "report": rep, "px": px}


# ============================================================================= EUR/USD variants
EUR_VARIANTS = ["eur_own", "usd5", "usd6", "usd7x", "eur_rel", "agree", "breadth5", "usd5_notional", "usd5_lev", "usd5_am"]
ELIGIBLE = EUR_VARIANTS[1:]


def notional_agg_z(members: list[str], stamp_days: int = COT_LAG_DAYS) -> pd.Series:
    """z52 of the USD-notional-weighted aggregate net non-commercial position / aggregate open interest."""
    px = load_px("h10")
    net, oi = [], []
    for c in members:
        d = load_cot(c, "noncomm")
        p = _align_lagged(px[c].dropna(), d.index, 0)      # H.10 rate on (or last before) the report date
        net.append(d["net"] * CCY[c]["size"] * p)
        oi.append(d["oi"] * CCY[c]["size"] * p)
    net = pd.concat(net, axis=1).dropna()
    oi = pd.concat(oi, axis=1).reindex(net.index)
    z = z52(net.sum(axis=1) / oi.sum(axis=1))
    z.index = z.index + pd.Timedelta(days=stamp_days)
    return z


def eurusd_signals(X: pd.DataFrame, stamp_days: int = COT_LAG_DAYS) -> pd.DataFrame:
    """All EUR/USD signals in [-1, 1] on the feature-store grid, lagged exactly like `cot_z52`."""
    cdate = pd.DatetimeIndex(X["close_time"].dt.tz_convert("UTC").dt.normalize().dt.tz_localize(None))
    A = lambda s: pd.Series(_align_lagged(s, cdate, 1).values, index=X.index)
    Z = pd.DataFrame({c: A(stamped_z(c, "noncomm", stamp_days)) for c in ALL8})
    Zl = pd.DataFrame({c: A(stamped_z(c, "lev", stamp_days)) for c in MAJ5})
    Za = pd.DataFrame({c: A(stamped_z(c, "am", stamp_days)) for c in MAJ5})
    S = pd.DataFrame(index=X.index)
    usd5 = Z[MAJ5].mean(axis=1)
    S["eur_own"] = np.sign(Z["eur"])
    S["usd5"] = np.sign(usd5)
    S["usd6"] = np.sign(Z[MAJ6].mean(axis=1))
    S["usd7x"] = np.sign(Z[OTHERS7].mean(axis=1))
    S["eur_rel"] = np.sign(Z["eur"] - usd5)
    S["agree"] = 0.5 * (np.sign(Z["eur"]) + np.sign(usd5))
    S["breadth5"] = np.sign(Z[MAJ5]).mean(axis=1)
    S["usd5_notional"] = np.sign(A(notional_agg_z(MAJ5, stamp_days)))
    S["usd5_lev"] = np.sign(Zl.mean(axis=1, skipna=False))
    S["usd5_am"] = np.sign(Za.mean(axis=1, skipna=False))
    S.attrs["Z"] = Z
    return S.fillna(0.0)


def eurusd_position(X: pd.DataFrame, sig: pd.Series) -> pd.Series:
    return rule_positions(X, sig, X["label_end_1d"])


def _eur_pnl(X: pd.DataFrame, pos: pd.Series, cost_pips: float) -> pd.DataFrame:
    p = pnl_from_positions(pos, X["fwd_1d"], X["close"], cost_pips=cost_pips)
    return p[p.index.year >= 2010]


def _sr(net: pd.Series, a: int, b: int) -> tuple[float, float]:
    r = _agg(net[(net.index.year >= a) & (net.index.year <= b)], 252)
    return r["sharpe"], r["t"]


# ============================================================================= incremental test
def incremental(streams: dict | None = None) -> pd.DataFrame:
    """meta.combine EW three-way vs two-way. With `streams` (name -> daily net_bp Series) the third arm is served from
    memory (diagnostic for non-final variants); without, the saved g10_positioning_positions.parquet is used."""
    from eurusd.arms import meta
    rows = []
    base, _ = meta.combine(["weak_signals", "regime_trend"], "EW")
    b = meta.report_combo(base, "EW2_weak+regime", 2).set_index("period")
    ws, rt = meta.load_arm_daily("weak_signals"), meta.load_arm_daily("regime_trend")
    items = streams or {ARM: None}
    orig = meta.load_arm_daily
    for name, s in items.items():
        if s is not None:
            key = (pd.DatetimeIndex(s.index) - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
            daily = s.groupby(key).sum().sort_index()
            meta.load_arm_daily = lambda n, _d=daily, _o=orig: _d if n == "__g10__" else _o(n)   # noqa: E731
            arm = "__g10__"
        else:
            daily = orig(ARM)
            arm = ARM
        try:
            three, w = meta.combine(["weak_signals", "regime_trend", arm], "EW")
        finally:
            meta.load_arm_daily = orig
        t = meta.report_combo(three, f"EW3_+{name}", 3).set_index("period")
        j = pd.concat([daily.rename("x"), ws.rename("ws"), rt.rename("rt")], axis=1).fillna(0.0)
        j = j[j.index.year >= 2010]
        row = {"variant": name, "corr_weak_signals": j["x"].corr(j["ws"]), "corr_regime_trend": j["x"].corr(j["rt"]),
               "years_in_combo": int((w[arm] > 0).sum()) if arm in w else 0}
        for lab, y0 in (("2010-2026", 2010), ("2016-2026", 2016)):      # alpha of the stream on the two survivors (OLS)
            q = j[j.index.year >= y0]
            A_ = np.c_[np.ones(len(q)), q["ws"].values, q["rt"].values]
            beta, *_ = np.linalg.lstsq(A_, q["x"].values, rcond=None)
            res = q["x"].values - A_ @ beta
            se = np.sqrt(res.var(ddof=3) * np.linalg.inv(A_.T @ A_)[0, 0])
            row[f"alpha_bp_{lab}"] = beta[0]; row[f"alpha_t_{lab}"] = beta[0] / se
        for per in ("2010-2026", "2013-2026", "2016-2026", "2023-2026"):
            row[f"SR2_{per}"] = b.loc[per, "sharpe"]; row[f"SR3_{per}"] = t.loc[per, "sharpe"]
            row[f"t2_{per}"] = b.loc[per, "t"]; row[f"t3_{per}"] = t.loc[per, "t"]
        rows.append(row)
    return pd.DataFrame(rows)


# ============================================================================= leak checks
def leak_checks(X: pd.DataFrame, final: str, cost_pips: float, cc: dict) -> pd.DataFrame:
    rows = []

    def add(name, net):
        r = {"check": name}
        for lab, a, b in (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026)):
            r[f"SR_{lab}"], r[f"t_{lab}"] = _sr(net, a, b)
        rows.append(r)

    S = eurusd_signals(X)
    add(f"eurusd {final}: as run", _eur_pnl(X, eurusd_position(X, S[final]), cost_pips)["net_bp"])
    # (1) shuffled labels
    for seed in range(5):
        Xs = X.copy()
        Xs["fwd_1d"] = np.random.default_rng(seed).permutation(X["fwd_1d"].values)
        add(f"eurusd {final}: shuffled labels seed {seed}", _eur_pnl(Xs, eurusd_position(Xs, S[final]), cost_pips)["net_bp"])
    # (2) shifted signal: positive = staler, negative = look-ahead
    for k in (1, 5, 21, 63, -1, -5, -10, -21):
        add(f"eurusd {final}: signal shifted {k:+d} sessions", _eur_pnl(X, eurusd_position(X, S[final].shift(k).fillna(0.0)), cost_pips)["net_bp"])
    for sd, lab in ((3, "stamp +3d (publication day, no weekend margin)"), (0, "stamp +0d (report date, before publication)"),
                    (-7, "stamp -7d (10 days before publication)"), (-28, "stamp -28d")):
        S2 = eurusd_signals(X, stamp_days=sd)
        add(f"eurusd {final}: {lab}", _eur_pnl(X, eurusd_position(X, S2[final]), cost_pips)["net_bp"])
    # the same on the 7-currency basket
    frames = cc["frames"]

    def basket(shift=0, stamp=COT_LAG_DAYS, perm_seed=None):
        px = cc["px"]
        pk = {}
        for c in OTHERS7:
            f = frames[c] if stamp == COT_LAG_DAYS else ccy_frame(c, px, stamp_days=stamp)
            if perm_seed is not None:
                f = f.copy()
                f["fwd_1d"] = f["fwd_1d"].values[np.random.default_rng(perm_seed).permutation(len(f))]   # same permutation for all
            sig = np.sign(f["z"]).shift(shift) if shift else np.sign(f["z"])
            pk[c] = _pnl(f, rule_positions(f, sig, f["label_end"]), cost_pips)
        return _basket(pk, OTHERS7)["net_bp"]

    add("basket7: as run", basket())
    for seed in range(5):
        add(f"basket7: shuffled labels seed {seed}", basket(perm_seed=seed))
    for k in (1, 5, 21, 63, -1, -5, -10, -21):
        add(f"basket7: signal shifted {k:+d} sessions", basket(shift=k))
    for sd in (3, 0, -7, -28):
        add(f"basket7: stamp {sd:+d}d", basket(stamp=sd))
    return pd.DataFrame(rows)


# ============================================================================= extra diagnostics (no selection)
def diagnostics(X: pd.DataFrame, cc: dict, positions: dict, cost_pips: float) -> dict:
    frames, pnls, px = cc["frames"], cc["pnls"], cc["px"]
    out = {}
    # (a) direction sanity: weekly change of net/OI vs the same Tuesday-to-Tuesday currency return (specs chase price,
    #     so this must be clearly positive for every currency if quote directions are right)
    rows = []
    for c in ALL8:
        d = load_cot(c)
        p = np.log(_align_lagged(px[c].dropna(), d.index, 0))
        j = pd.DataFrame({"dpos": d["ratio"].diff(), "ret": p.diff()}).loc["2003":].dropna()
        f = frames[c]
        pos = pnls[c]["pos"]
        rows.append({"ccy": c, "corr_dpos_ret_same_week": j["dpos"].corr(j["ret"]), "weeks": len(j),
                     "long_frac": float((pos > 0).mean()), "turnover_per_year": float(pos.diff().abs().sum() / (len(pos) / 252)),
                     "median_rv21_bp": float(f["rv_21d_bp"].median()),
                     "cost_bp_per_unit_at_1.2": float((cost_pips / f["cost_px"]).iloc[-1])})
    out["sanity"] = pd.DataFrame(rows)
    # (b) pre-2010 record of the fixed rule (never used anywhere; sign only, vol scale from an expanding median)
    rows = []
    for c in ALL8:
        f = frames[c]
        med = f["rv_21d_bp"].expanding(252).median()
        pos = (np.sign(f["z"]) * (med / f["rv_21d_bp"]).clip(0, VOL_CAP)).fillna(0.0)
        p = pnl_from_positions(pos, f["fwd_1d"], f["cost_px"], cost_pips=cost_pips)
        r = _agg(p["net_bp"][(p.index.year >= 2004) & (p.index.year <= 2009)], 252)
        rows.append({"ccy": c, "SR_2004_2009": r["sharpe"], "t_2004_2009": r["t"]})
        pnls[f"pre_{c}"] = p[(p.index.year >= 2004) & (p.index.year <= 2009)]
    pre = pd.DataFrame(rows)
    b7 = _basket({c: pnls[f"pre_{c}"] for c in OTHERS7}, OTHERS7)["net_bp"]
    r = _agg(b7, 252)
    pre = pd.concat([pre, pd.DataFrame([{"ccy": "basket7_ex_eur", "SR_2004_2009": r["sharpe"], "t_2004_2009": r["t"]}])], ignore_index=True)
    out["pre2010"] = pre
    # (c) the final's logic on every major: sign(z_i - mean z of the other five), same harness
    Z6 = pd.DataFrame({c: frames[c]["z"] for c in MAJ6})
    rows = []
    pr = {}
    for c in MAJ6:
        f = frames[c]
        sig = np.sign(Z6[c] - Z6[[k for k in MAJ6 if k != c]].mean(axis=1))
        pr[c] = _pnl(f, rule_positions(f, sig, f["label_end"]), cost_pips)
        row = {"ccy": c}
        for lab, a, b in (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026)):
            row[f"SR_{lab}"], row[f"t_{lab}"] = _sr(pr[c]["net_bp"], a, b)
        rows.append(row)
    bb = _basket(pr, MAJ5)["net_bp"]
    row = {"ccy": "basket5_ex_eur"}
    for lab, a, b in (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026)):
        row[f"SR_{lab}"], row[f"t_{lab}"] = _sr(bb, a, b)
    rows.append(row)
    out["rel_rule_per_currency"] = pd.DataFrame(rows)
    # (d) pooled evidence
    rows = []
    for lab, a, b in (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026)):
        st = {c: _sr(pnls[c]["net_bp"], a, b) for c in ALL8}
        srs = np.array([st[c][0] for c in OTHERS7]); ts = np.array([st[c][1] for c in OTHERS7])
        e = pnls["eur"]["net_bp"]; o = pnls["basket7_ex_eur"]["net_bp"]
        m = (e.index.year >= a) & (e.index.year <= b)
        diff = (e[m] / e[m].std() - o[m] / o[m].std())
        nyr = m.sum() / 252
        rows.append({"period": lab, "n_positive_of_7": int((srs > 0).sum()), "mean_SR_others": srs.mean(), "sd_SR_others": srs.std(ddof=1),
                     "median_SR_others": float(np.median(srs)), "stouffer_z_others_indep": ts.sum() / np.sqrt(len(ts)),
                     "basket7_SR": _sr(o, a, b)[0], "basket7_t": _sr(o, a, b)[1],
                     "basket5_SR": _sr(pnls["basket5_majors_ex_eur"]["net_bp"], a, b)[0], "basket5_t": _sr(pnls["basket5_majors_ex_eur"]["net_bp"], a, b)[1],
                     "EUR_SR": st["eur"][0], "EUR_t": st["eur"][1], "EUR_rank_of_8": int(1 + sum(st[c][0] > st["eur"][0] for c in OTHERS7)),
                     "EUR_minus_others_in_null_sd": (st["eur"][0] - srs.mean()) / (1 / np.sqrt(nyr)),
                     "t_EUR_minus_basket7_unit_vol": float(diff.mean() / diff.std() * np.sqrt(len(diff)))})
        # rough empirical-Bayes shrinkage of the EUR Sharpe towards the 8-currency mean (sampling var = 1 / years)
        all8 = np.r_[st["eur"][0], srs]
        tau2 = max(0.0, all8.var(ddof=1) - 1.0 / nyr)
        rows[-1]["mean_SR_all8"] = all8.mean()
        rows[-1]["EUR_SR_shrunk_EB"] = all8.mean() + tau2 / (tau2 + 1.0 / nyr) * (st["eur"][0] - all8.mean())
    out["pooled"] = pd.DataFrame(rows)
    # (e) positioning vs price momentum, per currency: daily P&L correlation
    out["mom_corr"] = pd.DataFrame([{"ccy": c, "corr_pnl_positioning_vs_mom126": pnls[c]["net_bp"].corr(pnls[f"mom126_{c}"]["net_bp"])} for c in ALL8])
    # (f) EUR/USD: final vs eur_own decomposition, cross-correlation of the EUR/USD variants, signal-label correlation
    S = eurusd_signals(X)
    m = X.index.year >= 2010
    cor = pd.DataFrame({v: _eur_pnl(X, positions[v], cost_pips)["net_bp"] for v in EUR_VARIANTS}).corr()
    out["eurusd_pnl_corr"] = cor
    out["signal_label_corr"] = pd.DataFrame([{"signal": v, "corr_with_fwd_1d": S[v][m].corr(X["fwd_1d"][m]),
                                              "active_frac": float((S[v][m] != 0).mean()), "long_frac": float((S[v][m] > 0).mean()),
                                              "sign_changes_per_year": float((S[v][m].diff().abs() > 0).sum() / (m.sum() / 252))} for v in EUR_VARIANTS])
    fwd = X["fwd_1d"][m]
    rows = []
    for lab, a, b in (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026)):
        mm = (X.index.year >= a) & (X.index.year <= b)
        own, rel = S["eur_own"][mm], S["eur_rel"][mm]
        same = own == rel
        f = X["fwd_1d"][mm]
        rows.append({"period": lab, "frac_same_sign": float(same.mean()),
                     "eur_own_mean_bp_when_same": float((own * f)[same].mean()), "eur_own_mean_bp_when_differ": float((own * f)[~same].mean()),
                     "eur_rel_mean_bp_when_differ": float((rel * f)[~same].mean()), "t_eur_rel_when_differ": float(_agg((rel * f)[~same], 252)["t"]),
                     "n_differ": int((~same).sum())})
    out["final_vs_eur_own"] = pd.DataFrame(rows)
    return out


# ============================================================================= driver
def run(cost_pips: float = 1.2, save: bool = True, verbose: bool = True):
    """Cross-currency study + EUR/USD variants + declared selection + deliverables. Returns (positions, report)."""
    cc = cross_currency(cost_pips, verbose=verbose)
    rep_cc = cc["report"]
    X = pd.read_parquet(DATA)
    S = eurusd_signals(X)
    Z = S.attrs["Z"]
    assert np.allclose(Z["eur"].fillna(0).values, X["cot_z52"].fillna(0).values, atol=1e-9), "EUR z differs from cot_z52"
    tables, positions = [], {}
    for v in EUR_VARIANTS:
        pos = eurusd_position(X, S[v])
        positions[v] = pos
        for cp in (cost_pips, 0.5 * cost_pips, 2 * cost_pips):
            t = _tbl(_eur_pnl(X, pos, cp), v, "eurusd", cp, n_arms=len(EUR_VARIANTS))
            tables.append(t)
    rep_eu = pd.concat(tables, ignore_index=True)
    sel = rep_eu[(rep_eu.period == "2010-2015") & (rep_eu.cost_pips == cost_pips) & rep_eu.variant.isin(ELIGIBLE)]
    final = sel.sort_values("sharpe", ascending=False).iloc[0]["variant"]
    rep = pd.concat([rep_eu, rep_cc], ignore_index=True)
    rep["final"] = (rep["variant"] == final) & (rep["group"] == "eurusd")
    rep["n_eurusd_variants"] = len(EUR_VARIANTS)
    pos = positions[final]
    out = pd.DataFrame({"pos": pos, "fwd_bp": X["fwd_1d"], "net_bp": pnl_from_positions(pos, X["fwd_1d"], X["close"], cost_pips=cost_pips)["net_bp"]})
    out = out[out.index.year >= 2010]
    extra = {}
    if save:
        OUT.mkdir(parents=True, exist_ok=True)
        out.to_parquet(OUT / f"{ARM}_positions.parquet")
        rep.to_csv(OUT / f"{ARM}_report.csv", index=False)
        allpos = pd.DataFrame(positions)
        allpos[allpos.index.year >= 2010].to_parquet(OUT / f"{ARM}_all_positions.parquet")
        # multi-currency basket daily P&L for the lead (index = H.10 date at 17:00 UTC; net_bp = 7-currency ex-EUR basket)
        pn = cc["pnls"]
        bk = pd.DataFrame({"net_bp": pn["basket7_ex_eur"]["net_bp"], "pos": pn["basket7_ex_eur"]["pos"],
                           "basket5_majors_ex_eur": pn["basket5_majors_ex_eur"]["net_bp"],
                           "basket8_incl_eur": pn["basket8_incl_eur"]["net_bp"],
                           **{f"net_{c}": pn[c]["net_bp"] for c in ALL8}, **{f"pos_{c}": pn[c]["pos"] for c in ALL8},
                           **{k: pn[k]["net_bp"] for k in ("xs_rank", "xs_demean", "xs_top2", "usd_factor")}})
        bk.to_parquet(OUT / f"{ARM}_basket.parquet")
        # incremental value: official (final, from file) + diagnostic for every EUR/USD variant and the basket stream
        inc = incremental()
        inc.insert(1, "official", True)
        streams = {v: _eur_pnl(X, positions[v], cost_pips)["net_bp"] for v in EUR_VARIANTS}
        streams["basket7_ex_eur(stream)"] = pn["basket7_ex_eur"]["net_bp"]
        streams["basket5_majors_ex_eur(stream)"] = pn["basket5_majors_ex_eur"]["net_bp"]
        inc2 = incremental(streams)
        inc2.insert(1, "official", False)
        inc = pd.concat([inc, inc2], ignore_index=True)
        inc.to_csv(OUT / f"{ARM}_incremental.csv", index=False)
        lk = leak_checks(X, final, cost_pips, cc)
        lk.to_csv(OUT / f"{ARM}_leakchecks.csv", index=False)
        dg = diagnostics(X, cc, positions, cost_pips)
        with open(OUT / f"{ARM}_diagnostics.json", "w") as fh:
            json.dump({k: json.loads(v.to_json(orient="table" if k == "eurusd_pnl_corr" else "records")) for k, v in dg.items()}, fh, indent=1)
        extra = {"incremental": inc, "leak": lk, **dg}
    if verbose:
        _print_summary(rep, cost_pips, final, extra)
    return out["pos"], rep


def _pivot(rep: pd.DataFrame, cost_pips: float, groups: list[str] | None = None) -> pd.DataFrame:
    r = rep[np.isclose(rep.cost_pips, cost_pips)]
    if groups:
        r = r[r.group.isin(groups)]
    per = ["2010-2026", "2016-2026", "2023-2026", "2010-2015", "2016-2022"]
    r = r[r.period.isin(per)]
    sr = r.pivot_table(index=["group", "variant"], columns="period", values="sharpe", sort=False)[per]
    tt = r.pivot_table(index=["group", "variant"], columns="period", values="t", sort=False)[per[:3]]
    sr.columns = [f"SR {c}" for c in sr.columns]
    tt.columns = [f"t {c}" for c in tt.columns]
    return pd.concat([sr, tt], axis=1)


def _print_summary(rep, cost_pips, final, extra):
    pd.set_option("display.width", 250, "display.max_rows", 500, "display.max_columns", 30)
    print(f"\n== all variants, net, {cost_pips} pips-equivalent")
    print(_pivot(rep, cost_pips).round(2).to_string())
    print(f"\n== 2x cost ({2 * cost_pips} pips)")
    print(_pivot(rep, 2 * cost_pips).round(2).to_string())
    print("\nFINAL EUR/USD variant by the declared rule (best 2010-2015 among eligible):", final)
    for k, v in extra.items():
        print(f"\n== {k}\n", v.round(3).to_string())


if __name__ == "__main__":
    import sys
    if "build" in sys.argv:
        print(json.dumps(build_cot(verbose=False), indent=1))
        fetch_prices()
    run()
