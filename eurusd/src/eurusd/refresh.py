"""Keep the live inputs current and keep a forward-test record.

refresh_macro()   incremental CFTC positioning (current-year files merged into the committed CSVs),
                  full ECB yields/rates refresh and FRED-mirror refresh; each step is independent and
                  failures are reported, never fatal (the brief still runs on the stored data).
log_signal()      append today's target, inputs and risk numbers to state/signal_log.csv so the
                  forward record accumulates from day one, traded or not.
"""
from __future__ import annotations

import contextlib
import csv
import io
import time
import traceback
from pathlib import Path

import pandas as pd

from . import macro_fetch as MF

ROOT = Path(__file__).resolve().parents[2]
MACRO = ROOT / "data" / "macro"
LOG = ROOT / "state" / "signal_log.csv"


def _merge_rows(csv_path: Path, new: pd.DataFrame) -> int:
    old = pd.read_csv(csv_path, dtype={"report_date": str})
    add = new[~new["report_date"].isin(set(old["report_date"]))]
    if add.empty:
        return 0
    out = pd.concat([old, add[old.columns]], ignore_index=True).sort_values("report_date")
    out.to_csv(csv_path, index=False)
    return len(add)


def refresh_cot(year: int | None = None) -> str:
    """Download the current year's TFF and legacy files and merge new weekly rows into the CSVs."""
    year = year or pd.Timestamp.utcnow().year
    d = MF.RAW / "cftc"
    d.mkdir(parents=True, exist_ok=True)
    for name in (f"fut_fin_txt_{year}.zip", f"deacot{year}.zip"):
        (d / name).unlink(missing_ok=True)       # always re-download the live year
    MF.download_cftc(years_tff=range(year, year + 1), years_legacy=range(year, year + 1))
    # TFF
    t = MF._read_cot_zip(d / f"fut_fin_txt_{year}.zip")
    t = t[t["CFTC_Contract_Market_Code"].str.strip() == MF.EUROFX_CODE]
    cols = {"Open_Interest_All": "open_interest", "Dealer_Positions_Long_All": "dealer_long", "Dealer_Positions_Short_All": "dealer_short",
            "Asset_Mgr_Positions_Long_All": "asset_mgr_long", "Asset_Mgr_Positions_Short_All": "asset_mgr_short",
            "Lev_Money_Positions_Long_All": "lev_funds_long", "Lev_Money_Positions_Short_All": "lev_funds_short",
            "Other_Rept_Positions_Long_All": "other_rept_long", "Other_Rept_Positions_Short_All": "other_rept_short",
            "NonRept_Positions_Long_All": "nonrept_long", "NonRept_Positions_Short_All": "nonrept_short", "Traders_Tot_All": "traders_total"}
    out = pd.DataFrame({"report_date": pd.to_datetime(t["Report_Date_as_YYYY-MM-DD"].str.strip()).dt.strftime("%Y-%m-%d")})
    for a, b in cols.items():
        out[b] = MF._num(t[a])
    for g in ["dealer", "asset_mgr", "lev_funds", "other_rept", "nonrept"]:
        out[f"{g}_net"] = out[f"{g}_long"] - out[f"{g}_short"]
        out[f"{g}_net_pct_oi"] = (100 * out[f"{g}_net"] / out["open_interest"]).round(2)
    n1 = _merge_rows(MACRO / "cot_eurofx_tff.csv", out.drop_duplicates("report_date"))
    # legacy
    l = MF._read_cot_zip(d / f"deacot{year}.zip")
    code_col = next(c for c in l.columns if "Contract Market Code" in c)
    l = l[l[code_col].astype(str).str.strip() == MF.EUROFX_CODE]
    date_col = next(c for c in l.columns if "YYYY-MM-DD" in c)
    col = lambda prefix: next(c for c in l.columns if c.strip().startswith(prefix))
    o = pd.DataFrame({"report_date": pd.to_datetime(l[date_col].str.strip()).dt.strftime("%Y-%m-%d")})
    o["open_interest"] = MF._num(l[col("Open Interest (All)")])
    o["noncomm_long"] = MF._num(l[col("Noncommercial Positions-Long (All)")]); o["noncomm_short"] = MF._num(l[col("Noncommercial Positions-Short (All)")])
    o["noncomm_spread"] = MF._num(l[col("Noncommercial Positions-Spreading (All)")])
    o["comm_long"] = MF._num(l[col("Commercial Positions-Long (All)")]); o["comm_short"] = MF._num(l[col("Commercial Positions-Short (All)")])
    o["nonrept_long"] = MF._num(l[col("Nonreportable Positions-Long (All)")]); o["nonrept_short"] = MF._num(l[col("Nonreportable Positions-Short (All)")])
    for g in ["noncomm", "comm", "nonrept"]:
        o[f"{g}_net"] = o[f"{g}_long"] - o[f"{g}_short"]
        o[f"{g}_net_pct_oi"] = (100 * o[f"{g}_net"] / o["open_interest"]).round(2)
    n2 = _merge_rows(MACRO / "cot_eurofx_legacy.csv", o.drop_duplicates("report_date"))
    last = pd.read_csv(MACRO / "cot_eurofx_legacy.csv")["report_date"].max()
    return f"COT: +{n2} legacy / +{n1} TFF rows, latest report {last}"


def refresh_macro(budget_s: float = 240) -> list[str]:
    """Run the refresh steps within a time budget; return one status line per step."""
    msgs = []
    t0 = time.time()
    for name, fn in (("cot", refresh_cot), ("ecb", MF.fetch_ecb), ("fred_mirrors", MF.fetch_mirrors)):
        if time.time() - t0 > budget_s:
            msgs.append(f"{name}: skipped (time budget)")
            continue
        try:
            with contextlib.redirect_stdout(io.StringIO()):   # the fetchers print progress; keep the brief short
                r = fn()
            msgs.append(r if isinstance(r, str) else f"{name}: ok")
        except Exception as e:  # network or format change: report, keep going
            msgs.append(f"{name}: FAILED {type(e).__name__}: {str(e)[:120]}")
    return msgs


def log_signal(exp, pl: dict, risk: dict) -> None:
    LOG.parent.mkdir(parents=True, exist_ok=True)
    row = {"asof_session_close": exp.asof_session_close, "price": exp.price, "target_units": exp.target_units, "c_units": exp.c_units,
           "d_units": exp.d_units, "c_score": exp.c_score, "d_cot_z52": exp.d_cot_z52, "atr20_pips": exp.atr20_pips, "stop": pl.get("stop"),
           "action": pl.get("action"), "target_lots": pl.get("target_lots"), **{f"risk_{k}": v for k, v in risk.items()}}
    new = not LOG.exists()
    if not new:
        last = pd.read_csv(LOG, usecols=["asof_session_close"]) if LOG.stat().st_size > 0 else pd.DataFrame()
        if len(last) and last["asof_session_close"].iloc[-1] == row["asof_session_close"]:
            return  # already logged this session
    with LOG.open("a", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(row))
        if new:
            w.writeheader()
        w.writerow(row)
