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
    import requests
    r = requests.get(f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}", headers={"User-Agent": UA}, timeout=120)
    r.raise_for_status()
    d = pd.read_csv(io.StringIO(r.text))
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
