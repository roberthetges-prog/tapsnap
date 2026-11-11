"""Arm M ("flows_calendar"): predictable, non-informational FLOWS on known dates.

PRE-REGISTRATION (written before any result of this arm was computed)
======================================================================
Economic priors
  P1 month-end hedge rebalancing. Foreign holders of US equities hedge a fixed share of the USD value. When US
     equities outperform euro-area equities month-to-date (local currency), their USD assets have grown relative to
     the hedge, so they must SELL USD forward at month-end; US holders of euro-area assets are over-hedged and buy
     back EUR. Both legs point the same way: rel = MTD(S&P 500) - MTD(Euro Stoxx 50) > 0  ->  LONG EUR/USD into
     month-end and into the 16:00 London fix of the last business day. Bigger |rel| -> bigger flow. Quarter-ends and
     year-end carry more benchmark money, so the effect should be larger there.
     (Note the sign is the OPPOSITE of the live `eqrel` momentum signal, which is short EUR/USD after US equity
     outperformance over 20 days. If the flow story is right, eqrel's sign flips in the last sessions of a month.)
  P2 new-month reversal. Flow pressure is price impact without information, so part of it reverses in the first
     sessions of the new month: fade the rebalancing direction (variant a) or fade the realised move of the last
     three sessions (variant b).
  P3 seasonality. Year-end corporate repatriation / window dressing -> December long EUR/USD; dividend season of
     European companies (April-June payments to foreign holders who convert EUR to USD) and "sell in May" -> May
     short; January reversal of December -> short; Japanese fiscal year-end (March) and US tax date (April) have no
     clear EUR/USD sign (JPY and USD legs offset), prior 0. The test is deliberately agnostic: all 12 months,
     empirical-Bayes shrinkage towards zero, walk-forward. If the cross-section of the 12 month t-stats is no wider
     than noise the shrinkage factor is 0 and there is no position.
  P4 IMM roll. Speculative futures positions that are not rolled must be closed before the last trading day
     (Monday before the third Wednesday of Mar/Jun/Sep/Dec): flow AGAINST the net speculative position in the five
     sessions ending on the last trading day -> position = -sign(cot_z52). Equity option-expiry Fridays have no
     directional FX prior: descriptive statistics only.
  P5 holidays. Short-term positions are squared before a long weekend / holiday -> the session before a US or
     TARGET holiday partially reverses the last week's move: position = -sign(ret_5d). Post-holiday sessions and
     the thin year-end week: descriptive only.
  P6 central-bank blackout. In the 10 days before an FOMC meeting and the week before an ECB meeting there is no
     policy communication, so positions keep adjusting to the last message: the 21-day trend persists ->
     position = sign(ret_21d) inside the window (never held through the announcement session itself).
  P7 Treasury refunding / auction settlement: no clean date list reachable (fiscaldata / TreasuryDirect blocked by
     the proxy), SKIPPED.

Candidate variants (12, all counted; nothing else is eligible for selection)
  daily, label fwd_1d, cost = wf harness (cost_pips per unit turnover):
   1 reb_d3         sign(rel) fixed at the close of T-3, held over the last 3 sessions of the month (T-2, T-1, T)
   2 reb_d1         sign(rel) at the close of T-1, held over the last session (T) only
   3 reb_d3_lin     as 1 but size-weighted: clip(rel / Q80_train(|rel| at T-3 decisions), -1, 1)
   4 nm_rev_sig     -sign(rel at the close of T) over the first 2 sessions of the new month
   5 nm_rev_px      -sign(return of the last 3 sessions of the month) over the first 2 sessions of the new month
   6 season_js      month-of-year mean of ECB-fixing monthly returns 1999..Y-1, t-stats shrunk with the
                    positive-part James-Stein factor, position = clip(B * t_m / 2, -1, 1)
   7 imm_fade_cot   -sign(cot_z52) in the 5 sessions ending on the IMM last trading day
   8 hol_square     -sign(ret_5d) over the session before a US federal / Good Friday / TARGET holiday
   9 blackout_trend sign(ret_21d) while 24h < h_to_fomc <= 240h or 24h < h_to_ecb <= 168h
  10 flows_core     clip(reb_d3 + nm_rev_sig + season_js, -1, 1): the proposed replacement of `tom` + `season`
  intraday (M5, London local time with DST, 1.2 pip ROUND-TRIP cost, one decision row per month-end):
  11 fix_reb        last business day: enter 15:00 London, exit 16:00, direction sign(rel through T-1)
  12 fix_follow_reb last business day: follow the 15:00-15:45 move over 15:45-16:00 only when it agrees with sign(rel)
Benchmarks / diagnostics (NOT eligible): round-1 unconditional fix-follow, its "disagree" complement, the live
  `season` (Dec/May) and `tom` rules, a US-vs-rest-of-world (SX5E, FTSE, N225) version of 1, the DAX-based pre-2007
  history of 1, mid-month placebo windows, the non-blackout complement, descriptive tables.

SELECTION RULE (declared before results): the final variant is the candidate with the highest 2010-2015
walk-forward NET Sharpe at the headline cost. Its full 2010-2026 record is then reported whatever it is.
Equity data lag: daily closes stamped <= (session close date - 1 calendar day), as featstore._align_lagged.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.wf import walk_forward, pnl_from_positions, report, _agg  # noqa: E402

FEATURES = ROOT / "data/processed/features_daily.parquet"
CROSS = ROOT / "data/processed/cross"
PROC = ROOT / "data/processed"
MACRO = ROOT / "data/macro"
RES = ROOT / "experiments/results/arms"
ARM = "flows_calendar"
FIX_CACHE = PROC / "flows_calendar_fix_windows.parquet"
N_VARIANTS = 12
DAILY_VARIANTS = ["reb_d3", "reb_d1", "reb_d3_lin", "nm_rev_sig", "nm_rev_px", "season_js", "imm_fade_cot", "hol_square",
                  "blackout_trend", "flows_core"]
INTRADAY_VARIANTS = ["fix_reb", "fix_follow_reb"]
PERIODS = (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026), ("2010-2015", 2010, 2015), ("2016-2022", 2016, 2022))


# ================================================================== data helpers
def _eq_close(name: str) -> pd.Series:
    """Daily close of a cross-asset series indexed by the (naive) local session date."""
    d = pd.read_parquet(CROSS / f"{name}_D1.parquet")
    s = d["close"].dropna()
    s.index = s.index.tz_convert("UTC").normalize().tz_localize(None)
    return s[~s.index.duplicated(keep="last")].sort_index()


def mtd_logret(s: pd.Series) -> pd.Series:
    """Month-to-date log return (bp) of each observation relative to the last close of the previous month."""
    per = s.index.to_period("M")
    last = np.log(s).groupby(per).last()
    base = last.shift(1).reindex(per).values
    return (np.log(s) - base) * 1e4


def align_lagged(s: pd.Series, dates, lag_days: int = 1) -> np.ndarray:
    """Value of s known at the start of each date: last observation stamped <= date - lag_days (featstore convention)."""
    target = pd.DatetimeIndex(dates) - pd.Timedelta(days=lag_days)
    return s.reindex(s.index.union(target)).sort_index().ffill().reindex(target).values


def _third_weekday(year: int, month: int, weekday: int) -> pd.Timestamp:
    d = pd.Timestamp(year, month, 1)
    d += pd.Timedelta(days=(weekday - d.dayofweek) % 7)
    return d + pd.Timedelta(days=14)


def imm_roll_dates(years) -> set:
    """Business days of the 5 sessions ending on the IMM last trading day (Monday before the third Wednesday)."""
    out = set()
    for y in years:
        for m in (3, 6, 9, 12):
            ltd = _third_weekday(y, m, 2) - pd.Timedelta(days=2)
            out.update(pd.bdate_range(end=ltd, periods=5))
    return out


def imm_week_dates(years) -> set:
    out = set()
    for y in years:
        for m in (3, 6, 9, 12):
            w = _third_weekday(y, m, 2)
            out.update(pd.bdate_range(w - pd.Timedelta(days=2), w + pd.Timedelta(days=2)))
    return out


def opex_fridays(years) -> set:
    return {_third_weekday(y, m, 4) for y in years for m in range(1, 13)}


def holiday_sets(start="1998-01-01", end="2028-12-31") -> tuple[set, set]:
    """(US holidays, TARGET holidays) as sets of weekday dates. US = federal holidays (observed) + Good Friday."""
    from dateutil.easter import easter
    from pandas.tseries.holiday import USFederalHolidayCalendar
    us = set(pd.DatetimeIndex(USFederalHolidayCalendar().holidays(start, end)).normalize())
    tgt = set()
    for y in range(pd.Timestamp(start).year, pd.Timestamp(end).year + 1):
        e = pd.Timestamp(easter(y))
        gf, em = e - pd.Timedelta(days=2), e + pd.Timedelta(days=1)
        us.add(gf)
        tgt.update([pd.Timestamp(y, 1, 1), gf, em, pd.Timestamp(y, 5, 1), pd.Timestamp(y, 12, 25), pd.Timestamp(y, 12, 26)])
    us = {d for d in us if d.dayofweek < 5}
    tgt = {d for d in tgt if d.dayofweek < 5}
    return us, tgt


def _prev_business_day(d: pd.Timestamp, hol: set) -> pd.Timestamp:
    p = d - pd.Timedelta(days=1)
    while p.dayofweek >= 5 or p in hol:
        p -= pd.Timedelta(days=1)
    return p


def _next_business_day(d: pd.Timestamp, hol: set) -> pd.Timestamp:
    p = d + pd.Timedelta(days=1)
    while p.dayofweek >= 5 or p in hol:
        p += pd.Timedelta(days=1)
    return p


def ecb_monthly_returns() -> pd.DataFrame:
    """Month-end to month-end log returns (bp) of the ECB reference rate, 1999-02 onwards (year, month, ret)."""
    e = pd.read_csv(PROC / "ecb_EURUSD_D1.csv", parse_dates=["date"]).set_index("date")["usd_per_eur"].astype(float)
    last = np.log(e).groupby(e.index.to_period("M")).last()
    r = (last - last.shift(1)).dropna() * 1e4
    # drop a trailing incomplete month
    if e.index.max() < (e.index.max() + pd.offsets.BMonthEnd(0)):
        r = r.iloc[:-1]
    return pd.DataFrame({"year": r.index.year, "month": r.index.month, "ret": r.values})


def chf_proxy_monthly_returns() -> pd.DataFrame:
    """Pre-1999 proxy: the Fed H.10 file has no DEM column, so the closest available series is USD/CHF (the Swiss franc
    shadowed the D-mark closely before 1999). Proxy EUR/USD return = -dlog(CHF per USD), month-end to month-end."""
    fx = pd.read_csv(MACRO / "datahub_fx_fed_h10_daily.csv", parse_dates=["date"]).set_index("date")["chf_per_usd"].astype(float).dropna()
    last = np.log(fx).groupby(fx.index.to_period("M")).last()
    r = -(last - last.shift(1)).dropna() * 1e4
    return pd.DataFrame({"year": r.index.year, "month": r.index.month, "ret": r.values})


# ================================================================== frame
def load_frame() -> pd.DataFrame:
    df = pd.read_parquet(FEATURES)
    D = df[["fwd_1d", "close", "label_end_1d", "close_time", "bd_to_end", "bd_from_start", "month", "dow", "ret_3d", "ret_5d", "ret_21d",
            "cot_z52", "h_to_fomc", "h_to_ecb", "spx_minus_sx5e_20", "rv_21d_bp"]].copy()
    cdate = pd.DatetimeIndex(D["close_time"].dt.tz_convert("UTC").dt.normalize().dt.tz_localize(None))
    D["cdate"] = cdate
    D["nxt_cdate"] = D["cdate"].shift(-1)
    D["ym"] = cdate.to_period("M")
    D["nxt_month"] = D["month"].shift(-1)
    mtd = {n: mtd_logret(_eq_close(n)) for n in ("spx", "sx5e", "gdaxi", "ftse", "n225")}
    A = {n: align_lagged(s, cdate, 1) for n, s in mtd.items()}
    D["mtd_spx"] = A["spx"]
    D["mtd_sx5e"] = A["sx5e"]
    D["rel"] = A["spx"] - A["sx5e"]                                             # headline signal (2007-04+)
    D["rel_dax"] = A["spx"] - A["gdaxi"]                                        # diagnostic, pre-2007 history (DAX = total return)
    D["rel_row"] = A["spx"] - np.nanmean(np.vstack([A["sx5e"], A["ftse"], A["n225"]]), axis=0) + 0 * A["sx5e"]   # diagnostic
    D["rel_nolag"] = align_lagged(mtd["spx"], cdate, 0) - align_lagged(mtd["sx5e"], cdate, 0)                      # look-ahead control only
    years = range(2000, 2029)
    us, tgt = holiday_sets()
    hol = us | tgt
    D["nxt_imm_roll"] = D["nxt_cdate"].isin(imm_roll_dates(years))
    D["nxt_imm_week"] = D["nxt_cdate"].isin(imm_week_dates(years))
    D["nxt_opex_fri"] = D["nxt_cdate"].isin(opex_fridays(years))
    pre = {_prev_business_day(h, hol) for h in hol}
    post = {_next_business_day(h, hol) for h in hol}
    D["nxt_pre_hol"] = D["nxt_cdate"].isin(pre)
    D["nxt_pre_us_hol"] = D["nxt_cdate"].isin({_prev_business_day(h, hol) for h in us})
    D["nxt_pre_tgt_hol"] = D["nxt_cdate"].isin({_prev_business_day(h, hol) for h in tgt})
    D["nxt_post_hol"] = D["nxt_cdate"].isin(post)
    nd = pd.DatetimeIndex(D["nxt_cdate"])
    D["nxt_yearend_week"] = ((nd.month == 12) & (nd.day >= 24)) | ((nd.month == 1) & (nd.day <= 2))
    D["blackout_fed"] = (D["h_to_fomc"] > 24) & (D["h_to_fomc"] <= 240)
    D["blackout_ecb"] = (D["h_to_ecb"] > 24) & (D["h_to_ecb"] <= 168)
    D["blackout"] = D["blackout_fed"] | D["blackout_ecb"]
    return D


# ================================================================== daily variants (positions on the feature-store grid)
def _month_value(D: pd.DataFrame, col: str, at_bd_to_end: int) -> pd.Series:
    """Value of `col` at the row with bd_to_end == at_bd_to_end, broadcast to every row of the same month."""
    v = D[col].where(D["bd_to_end"] == at_bd_to_end)
    return v.groupby(D["ym"]).transform("first")


def pos_reb_d3(D: pd.DataFrame, col: str = "rel", window=(3, 2, 1), decide_at: int | None = None) -> pd.Series:
    decide_at = max(window) if decide_at is None else decide_at
    s = _month_value(D, col, decide_at)
    return np.sign(s).where(D["bd_to_end"].isin(window), 0.0).fillna(0.0)


def pos_reb_d1(D: pd.DataFrame, col: str = "rel") -> pd.Series:
    return np.sign(D[col]).where(D["bd_to_end"] == 1, 0.0).fillna(0.0)


def raw_reb_d3(D: pd.DataFrame, col: str = "rel") -> pd.Series:
    return _month_value(D, col, 3).where(D["bd_to_end"].isin((3, 2, 1)))


def _newmonth_rows(D: pd.DataFrame) -> pd.Series:
    return (D["bd_to_end"] == 0) | (D["bd_from_start"] == 1)


def _carry_month_end(D: pd.DataFrame, v: pd.Series) -> pd.Series:
    """Value at the month's last row (bd_to_end == 0) carried to the first row of the new month."""
    x = v.where(D["bd_to_end"] == 0)
    return x.ffill(limit=1).where(_newmonth_rows(D))


def pos_nm_rev_sig(D: pd.DataFrame, col: str = "rel") -> pd.Series:
    return (-np.sign(_carry_month_end(D, D[col]))).fillna(0.0)


def pos_nm_rev_px(D: pd.DataFrame) -> pd.Series:
    return (-np.sign(_carry_month_end(D, D["ret_3d"]))).fillna(0.0)


def pos_imm(D: pd.DataFrame) -> pd.Series:
    return (-np.sign(D["cot_z52"])).where(D["nxt_imm_roll"], 0.0).fillna(0.0)


def pos_hol(D: pd.DataFrame) -> pd.Series:
    return (-np.sign(D["ret_5d"])).where(D["nxt_pre_hol"], 0.0).fillna(0.0)


def pos_blackout(D: pd.DataFrame, inside: bool = True) -> pd.Series:
    m = D["blackout"] if inside else ~D["blackout"]
    return np.sign(D["ret_21d"]).where(m, 0.0).fillna(0.0)


def season_table(M: pd.DataFrame, before_year: int) -> pd.DataFrame:
    """Month-of-year statistics from monthly returns of years < before_year, with positive-part James-Stein shrinkage
    of the 12 t-stats towards zero. Returns columns mean, t, n, B (shrink factor), pos."""
    tr = M[M["year"] < before_year]
    g = tr.groupby("month")["ret"]
    mean, sd, n = g.mean(), g.std(), g.count()
    t = (mean / (sd / np.sqrt(n))).reindex(range(1, 13)).fillna(0.0)
    nbar = float(n.mean())
    v = (nbar - 1) / (nbar - 3) if nbar > 3 else 3.0                # variance of a t statistic under the null
    k = 12
    ss = float((t ** 2).sum())
    B = max(0.0, 1.0 - (k - 2) * v / ss) if ss > 0 else 0.0
    out = pd.DataFrame({"mean_bp": mean.reindex(range(1, 13)), "t": t, "n": n.reindex(range(1, 13)), "B": B})
    out["pos"] = (B * t / 2).clip(-1, 1)
    return out


def make_season_fit_predict(M: pd.DataFrame, month_shift: int = 0, log: dict | None = None):
    def fit(train: pd.DataFrame):
        Y = int(train.index.max().year) + 1
        tab = season_table(M, Y)
        if log is not None:
            log[Y] = tab
        return tab

    def predict(tab, test: pd.DataFrame) -> pd.Series:
        m = test["nxt_month"].fillna(test["month"]).astype(int)
        if month_shift:
            m = ((m - 1 - month_shift) % 12) + 1                      # leak check: estimate of another month
        return m.map(tab["pos"]).astype(float)
    return fit, predict


def _static(fn):
    """Parameter-free rule run through the same walk-forward loop (so the OOS window is identical)."""
    return (lambda train: None), (lambda _m, test: fn(test))


def daily_positions(D: pd.DataFrame, M: pd.DataFrame | None = None, col: str = "rel", season_shift: int = 0,
                    season_log: dict | None = None) -> pd.DataFrame:
    """OOS positions (2010+) of the ten daily candidates. Every rule only reads columns of rows <= t; rules that span a
    month (`_month_value`) are evaluated on the full frame and then cut to the test year by the walk-forward loop."""
    M = ecb_monthly_returns() if M is None else M
    full = {"reb_d3": pos_reb_d3(D, col), "reb_d1": pos_reb_d1(D, col), "nm_rev_sig": pos_nm_rev_sig(D, col), "nm_rev_px": pos_nm_rev_px(D),
            "imm_fade_cot": pos_imm(D), "hol_square": pos_hol(D), "blackout_trend": pos_blackout(D)}
    P = {}
    for k, s in full.items():
        fit, predict = _static(lambda test, s=s: s.reindex(test.index))
        P[k] = walk_forward(D, fit, predict, label_end=D["label_end_1d"], verbose=False)
    Dl = D.copy()
    Dl["_raw"] = raw_reb_d3(D, col)

    def lin_fit(train):
        x = train[col].where(train["bd_to_end"] == 3).dropna().abs()
        return float(x.quantile(0.8)) if len(x) >= 12 else np.nan

    def lin_predict(q, test):
        if not np.isfinite(q) or q <= 0:
            return pd.Series(0.0, index=test.index)
        return (test["_raw"] / q).clip(-1, 1).fillna(0.0)
    P["reb_d3_lin"] = walk_forward(Dl, lin_fit, lin_predict, label_end=D["label_end_1d"], verbose=False)
    fit, predict = make_season_fit_predict(M, season_shift, season_log)
    P["season_js"] = walk_forward(D, fit, predict, label_end=D["label_end_1d"], verbose=False)
    P = pd.DataFrame(P).fillna(0.0)
    P["flows_core"] = (P["reb_d3"] + P["nm_rev_sig"] + P["season_js"]).clip(-1, 1)
    return P[DAILY_VARIANTS]


def daily_pnl(D: pd.DataFrame, pos: pd.Series, cost_pips: float) -> pd.DataFrame:
    pnl = pnl_from_positions(pos, D["fwd_1d"], D["close"], cost_pips=cost_pips)
    return pnl[pnl.index.year >= 2010].copy()


# ================================================================== intraday month-end fix (M5)
def build_fix_windows(refresh: bool = False) -> pd.DataFrame:
    """One row per weekday (London date): price just before 15:00, 15:45 and 16:00 London local time (last M5 close
    inside the preceding 15 minutes). Cached to data/processed/flows_calendar_fix_windows.parquet."""
    if FIX_CACHE.exists() and not refresh:
        return pd.read_parquet(FIX_CACHE)
    m5 = pd.read_parquet(PROC / "EURUSD_M5.parquet", columns=["close"])
    lon = m5.index.tz_convert("Europe/London")
    tod = lon.hour * 60 + lon.minute
    keep = (tod >= 14 * 60 + 45) & (tod < 16 * 60) & (lon.dayofweek < 5)
    x = pd.DataFrame({"close": m5["close"].values[keep], "tod": tod[keep], "date": lon[keep].tz_localize(None).normalize(), "utc": m5.index[keep]})
    x["bucket"] = np.select([x.tod < 15 * 60, (x.tod >= 15 * 60 + 30) & (x.tod < 15 * 60 + 45), x.tod >= 15 * 60 + 45], ["p1500", "p1545", "p1600"], "x")
    x = x[x.bucket != "x"]
    W = x.groupby(["date", "bucket"])["close"].last().unstack()
    W = W.dropna()
    d = pd.DatetimeIndex(W.index)
    W["t1500_utc"] = (d + pd.Timedelta(hours=15)).tz_localize("Europe/London").tz_convert("UTC")
    W["t1545_utc"] = (d + pd.Timedelta(hours=15, minutes=45)).tz_localize("Europe/London").tz_convert("UTC")
    W.to_parquet(FIX_CACHE)
    return W


def fix_frame(rel_col: str = "rel") -> pd.DataFrame:
    """One row per month: the last weekday of the month with fix-window prices, the equity signal known that morning
    (closes stamped <= T-1) and the window returns in bp."""
    W = build_fix_windows()
    d = pd.DatetimeIndex(W.index)
    last = W.groupby(d.to_period("M")).tail(1).copy()
    ld = pd.DatetimeIndex(last.index)
    # must really be the last weekday of the calendar month (drop months whose last day has no data)
    true_last = pd.DatetimeIndex([(x + pd.offsets.BMonthEnd(0)).normalize() for x in ld])
    last = last[ld == true_last]
    ld = pd.DatetimeIndex(last.index)
    mtd = {n: mtd_logret(_eq_close(n)) for n in ("spx", "sx5e", "gdaxi")}
    a_spx = align_lagged(mtd["spx"], ld, 1)
    last["rel"] = a_spx - align_lagged(mtd["sx5e"], ld, 1)
    last["rel_dax"] = a_spx - align_lagged(mtd["gdaxi"], ld, 1)
    last["r_1500_1600"] = np.log(last.p1600 / last.p1500) * 1e4
    last["r_1500_1545"] = np.log(last.p1545 / last.p1500) * 1e4
    last["r_1545_1600"] = np.log(last.p1600 / last.p1545) * 1e4
    last["month"] = ld.month
    return last


def fix_streams(F: pd.DataFrame, cost_pips: float, rel_col: str = "rel") -> dict:
    """Decision streams (one row per month-end, pos 0 when no trade). Cost = cost_pips per ROUND TRIP."""
    cost = cost_pips * 1e-4 / F["p1500"] * 1e4
    sig = np.sign(F[rel_col]).fillna(0.0)
    mv = np.sign(F["r_1500_1545"])
    out = {}

    def stream(pos, ret, tcol):
        d = pd.DataFrame({"pos": pos.values, "fwd_bp": ret.values, "gross_bp": (pos * ret).values, "net_bp": (pos * ret - pos.abs() * cost).values},
                         index=pd.DatetimeIndex(F[tcol].values, tz="UTC") if F[tcol].dt.tz is None else pd.DatetimeIndex(F[tcol]))
        d.index.name = "time"
        return d
    out["fix_reb"] = stream(sig, F["r_1500_1600"], "t1500_utc")
    out["fix_follow_reb"] = stream(mv.where(mv == sig, 0.0).where(sig != 0, 0.0), F["r_1545_1600"], "t1545_utc")
    out["bench_fix_follow"] = stream(mv, F["r_1545_1600"], "t1545_utc")                        # round-1 H05, unconditional
    out["bench_fix_follow_disagree"] = stream(mv.where((mv == -sig) & (sig != 0), 0.0), F["r_1545_1600"], "t1545_utc")
    return out


# ================================================================== statistics
def hit_rates(pnl: pd.DataFrame, fwd: pd.Series | None = None, per_row: bool = False) -> pd.DataFrame:
    """Share of active decisions with positive net P&L / correct sign before costs, per period, plus decisions per year.
    `episodes` = runs of consecutive active rows with an unchanged position sign (one trade), judged on their net sum;
    per_row=True (intraday decision streams): every row is its own trade."""
    fwd = pnl["fwd_bp"] if fwd is None else fwd.reindex(pnl.index)
    rows = []
    for lab, a, b in PERIODS[:3]:
        m = (pnl.index.year >= a) & (pnl.index.year <= b)
        p = pnl[m]
        f = fwd[m]
        act = p["pos"] != 0
        n = int(act.sum())
        yrs = (min(b, 2026) - a + 1) - (0.15 if b >= 2026 else 0.0)        # the sample ends 2026-11-06
        sg = np.sign(p["pos"])
        ep = (pd.Series(np.arange(len(sg)), index=sg.index) if per_row else (sg != sg.shift()).cumsum())[act]
        epn = p.loc[act, "net_bp"].groupby(ep).sum()
        epg = (p.loc[act, "pos"] * f[act]).groupby(ep).sum()
        rows.append({"period": lab, "decisions": n, "decisions_per_year": n / yrs, "hit_net": float((p.loc[act, "net_bp"] > 0).mean()) if n else np.nan,
                     "hit_sign_gross": float((np.sign(p.loc[act, "pos"]) == np.sign(f[act])).mean()) if n else np.nan,
                     "episodes": int(len(epn)), "episodes_per_year": len(epn) / yrs, "episode_hit_net": float((epn > 0).mean()) if len(epn) else np.nan,
                     "episode_hit_gross": float((epg > 0).mean()) if len(epg) else np.nan,
                     "mean_net_bp_per_decision": float(p.loc[act, "net_bp"].mean()) if n else np.nan,
                     "mean_gross_bp_per_decision": float((p.loc[act, "pos"] * f[act]).mean()) if n else np.nan})
    return pd.DataFrame(rows)


def _ev(x: pd.Series) -> dict:
    x = x.dropna()
    n = len(x)
    if n < 3:
        return {"n": n, "mean_bp": float(x.mean()) if n else np.nan, "t": np.nan, "hit": float((x > 0).mean()) if n else np.nan}
    return {"n": n, "mean_bp": float(x.mean()), "t": float(x.mean() / x.std() * math.sqrt(n)) if x.std() > 0 else 0.0, "hit": float((x > 0).mean())}


ERAS = (("2003-2009", 2003, 2009), ("2010-2015", 2010, 2015), ("2016-2022", 2016, 2022), ("2023-2026", 2023, 2026), ("2010-2026", 2010, 2026))


def month_end_table(D: pd.DataFrame, F: pd.DataFrame) -> pd.DataFrame:
    """Month-end conditioned vs unconditioned: GROSS bp per month-end event (no costs), by era and by month type."""
    rows = []
    # per-month event returns of the daily windows
    f = D["fwd_1d"]
    ev = pd.DataFrame({"ym": D["ym"], "month": D["cdate"].dt.month, "year": D["cdate"].dt.year})
    w3 = f.where(D["bd_to_end"].isin((3, 2, 1))).groupby(D["ym"]).sum(min_count=1)       # return of sessions T-2..T
    w1 = f.where(D["bd_to_end"] == 1).groupby(D["ym"]).sum(min_count=1)                   # return of session T
    nm = f.where(_newmonth_rows(D)).shift(0)
    # new-month window belongs to the month that just ended (row bd_to_end==0) and the first row of the next month
    key_nm = D["ym"].where(D["bd_to_end"] == 0).ffill(limit=1)
    w_nm = nm.groupby(key_nm).sum(min_count=1)
    s3 = {c: D[c].where(D["bd_to_end"] == 3).groupby(D["ym"]).first() for c in ("rel", "rel_dax", "rel_row")}
    s1 = D["rel"].where(D["bd_to_end"] == 1).groupby(D["ym"]).first()
    s0 = D["rel"].where(D["bd_to_end"] == 0).groupby(D["ym"]).first()
    px3 = D["ret_3d"].where(D["bd_to_end"] == 0).groupby(D["ym"]).first()
    E = pd.DataFrame({"w3": w3, "w1": w1, "w_nm": w_nm, "s3": s3["rel"], "s3_dax": s3["rel_dax"], "s3_row": s3["rel_row"], "s1": s1, "s0": s0, "px3": px3})
    E["year"] = E.index.year
    E["month"] = E.index.month
    Fx = F.copy()
    Fx["year"] = pd.DatetimeIndex(Fx.index).year
    sig = np.sign(Fx["rel"])
    mv = np.sign(Fx["r_1500_1545"])
    tests = {
        "daily T-2..T: unconditional long EUR": (E, E["w3"]),
        "daily T-2..T: sign(rel@T-3)  [reb_d3]": (E, np.sign(E["s3"]).replace(0, np.nan) * E["w3"]),
        "daily T-2..T: sign(rel_dax@T-3) (SPX-DAX, diag.)": (E, np.sign(E["s3_dax"]).replace(0, np.nan) * E["w3"]),
        "daily T-2..T: sign(rel_row@T-3) (US vs SX5E/FTSE/N225, diag.)": (E, np.sign(E["s3_row"]).replace(0, np.nan) * E["w3"]),
        "daily T: unconditional long EUR": (E, E["w1"]),
        "daily T: sign(rel@T-1)  [reb_d1]": (E, np.sign(E["s1"]).replace(0, np.nan) * E["w1"]),
        "daily T+1..T+2: unconditional long EUR": (E, E["w_nm"]),
        "daily T+1..T+2: -sign(rel@T)  [nm_rev_sig]": (E, -np.sign(E["s0"]).replace(0, np.nan) * E["w_nm"]),
        "daily T+1..T+2: -sign(ret T-2..T)  [nm_rev_px]": (E, -np.sign(E["px3"]).replace(0, np.nan) * E["w_nm"]),
        "fix 15:00-16:00: unconditional long EUR": (Fx, Fx["r_1500_1600"]),
        "fix 15:00-16:00: sign(rel)  [fix_reb]": (Fx, sig.replace(0, np.nan) * Fx["r_1500_1600"]),
        "fix 15:45-16:00: follow 15:00-15:45 (round-1 H05, unconditional)": (Fx, mv * Fx["r_1545_1600"]),
        "fix 15:45-16:00: follow, move agrees with sign(rel)  [fix_follow_reb]": (Fx, (mv * Fx["r_1545_1600"]).where((mv == sig) & sig.notna() & (sig != 0))),
        "fix 15:45-16:00: follow, move disagrees with sign(rel)": (Fx, (mv * Fx["r_1545_1600"]).where((mv == -sig) & sig.notna() & (sig != 0))),
    }
    types = {"all": lambda m: m > 0, "quarter-end": lambda m: m.isin([3, 6, 9, 12]), "year-end (Dec)": lambda m: m == 12, "non-quarter": lambda m: ~m.isin([3, 6, 9, 12])}
    for name, (frame, x) in tests.items():
        for tname, tf in types.items():
            for lab, a, b in ERAS:
                m = (frame["year"] >= a) & (frame["year"] <= b) & tf(frame["month"])
                rows.append({"test": name, "month_type": tname, "era": lab, **_ev(x[m])})
    return pd.DataFrame(rows)


def month_stability_table() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Month-of-year mean return and t by era (ECB fixing 1999+; CHF proxy before), sign stability, and a joint test."""
    M = ecb_monthly_returns()
    C = chf_proxy_monthly_returns()
    eras = (("1975-1998 (CHF proxy)", C, 1975, 1998), ("1999-2009", M, 1999, 2009), ("2010-2017", M, 2010, 2017), ("2018-2026", M, 2018, 2026), ("1999-2026", M, 1999, 2026))
    rows = []
    for m in range(1, 13):
        r = {"month": m}
        for lab, src, a, b in eras:
            x = src[(src.month == m) & (src.year >= a) & (src.year <= b)]["ret"]
            e = _ev(x)
            r[f"{lab} mean_bp"] = e["mean_bp"]
            r[f"{lab} t"] = e["t"]
            r[f"{lab} up/n"] = f"{int((x > 0).sum())}/{len(x)}"
        s = [np.sign(r[f"{lab} mean_bp"]) for lab in ("1999-2009", "2010-2017", "2018-2026")]
        r["stable_sign_3_eras"] = bool(abs(sum(s)) == 3)
        r["stable_incl_chf_proxy"] = bool(r["stable_sign_3_eras"] and np.sign(r["1975-1998 (CHF proxy) mean_bp"]) == s[0])
        rows.append(r)
    T = pd.DataFrame(rows)
    # joint test per era: sum of squared month t-stats ~ chi2(12) under no seasonality (approx.), plus JS factor
    from scipy.stats import chi2
    jrows = []
    for lab, src, a, b in eras:
        x = src[(src.year >= a) & (src.year <= b)]
        g = x.groupby("month")["ret"]
        t = g.mean() / (g.std() / np.sqrt(g.count()))
        ss = float((t ** 2).sum())
        nbar = float(g.count().mean())
        v = (nbar - 1) / (nbar - 3)
        # one-way ANOVA F test of equal month means (does not assume mean zero)
        from scipy.stats import f_oneway
        Fs, Fp = f_oneway(*[x[x.month == m]["ret"].values for m in range(1, 13)])
        jrows.append({"era": lab, "sum_t2": ss, "expected_under_null": 12 * v, "chi2_p_naive": float(1 - chi2.cdf(ss / v, 12)), "anova_F": float(Fs), "anova_p": float(Fp),
                      "JS_factor": max(0.0, 1 - 10 * v / ss)})
    return T, pd.DataFrame(jrows)


def descriptives(D: pd.DataFrame) -> pd.DataFrame:
    """Unconditional long-EUR return (bp per session) and mean |return| inside each calendar window, by era."""
    f = D["fwd_1d"]
    nd = pd.DatetimeIndex(D["nxt_cdate"])
    nxt_fri = pd.Series(nd.dayofweek == 4, index=D.index)
    wins = {
        "IMM roll window (5 sessions to LTD)": D["nxt_imm_roll"], "IMM week (Mon-Fri around 3rd Wed)": D["nxt_imm_week"],
        "opex Friday (3rd Friday)": D["nxt_opex_fri"], "other Fridays": nxt_fri & ~D["nxt_opex_fri"],
        "pre-holiday session (US or TARGET)": D["nxt_pre_hol"], "pre-US-holiday session": D["nxt_pre_us_hol"], "pre-TARGET-holiday session": D["nxt_pre_tgt_hol"],
        "post-holiday session": D["nxt_post_hol"], "year-end week (Dec 24 - Jan 2)": D["nxt_yearend_week"],
        "December 1-23": pd.Series((nd.month == 12) & (nd.day < 24), index=D.index), "May": pd.Series(nd.month == 5, index=D.index),
        "Fed blackout (10d before FOMC)": D["blackout_fed"], "ECB quiet week": D["blackout_ecb"], "any blackout": D["blackout"], "no blackout": ~D["blackout"],
        "all sessions": pd.Series(True, index=D.index),
    }
    rows = []
    for name, m in wins.items():
        for lab, a, b in (("2003-2009", 2003, 2009), ("2010-2017", 2010, 2017), ("2018-2026", 2018, 2026), ("2003-2026", 2003, 2026)):
            x = f[m.values & (D.index.year >= a) & (D.index.year <= b)]
            e = _ev(x)
            rows.append({"window": name, "era": lab, **e, "mean_abs_bp": float(x.abs().mean())})
    return pd.DataFrame(rows)


def fix_follow_by_day(F: pd.DataFrame) -> pd.DataFrame:
    """Is the 15:00-15:45 -> 15:45-16:00 continuation a MONTH-END effect? Same rule (gross bp, no cost) on the last
    business day, on T-1, T-2 and on all other weekdays."""
    W = build_fix_windows().copy()
    d = pd.DatetimeIndex(W.index)
    W["x"] = np.sign(np.log(W.p1545 / W.p1500)) * np.log(W.p1600 / W.p1545) * 1e4
    W["absmove_1545_1600"] = (np.log(W.p1600 / W.p1545) * 1e4).abs()
    rank = W.groupby(d.to_period("M")).cumcount(ascending=False)          # 0 = last day with data in the month
    is_last = pd.Series(d.isin(pd.DatetimeIndex(F.index)), index=W.index)
    grp = np.where(is_last, "last business day (T)", np.where(rank == 1, "T-1", np.where(rank == 2, "T-2", np.where(rank == 0, "x", "all other days"))))
    rows = []
    for g in ("last business day (T)", "T-1", "T-2", "all other days"):
        for lab, a, b in (("2001-2009", 2001, 2009), ("2010-2015", 2010, 2015), ("2016-2022", 2016, 2022), ("2023-2026", 2023, 2026), ("2010-2026", 2010, 2026)):
            m = (grp == g) & (d.year >= a) & (d.year <= b)
            rows.append({"day": g, "era": lab, **_ev(W.loc[m, "x"]), "mean_abs_move_1545_1600_bp": float(W.loc[m, "absmove_1545_1600"].mean())})
    return pd.DataFrame(rows)


def season_legs(D: pd.DataFrame) -> pd.DataFrame:
    """Decomposition of the live `season` rule: December-long and May-short legs separately (ECB monthly returns,
    gross, one observation per year) by era, plus the pooled 1975-2026 record with the CHF proxy before 1999."""
    M = ecb_monthly_returns()
    C = chf_proxy_monthly_returns()
    A = pd.concat([C[C.year <= 1998], M])
    rows = []
    for leg, m, sgn in (("December long", 12, 1.0), ("May short", 5, -1.0), ("January short (prior: reversal of December)", 1, -1.0)):
        for lab, src, a, b in (("1975-1998 (CHF proxy)", C, 1975, 1998), ("1999-2009", M, 1999, 2009), ("2010-2015 (round-1 TRAIN, in-sample for the rule)", M, 2010, 2015),
                               ("2016-2026 (after the rule was chosen)", M, 2016, 2026), ("1999-2026", M, 1999, 2026), ("1975-2026 pooled (proxy + ECB)", A, 1975, 2026)):
            x = sgn * src[(src.month == m) & (src.year >= a) & (src.year <= b)]["ret"]
            rows.append({"leg": leg, "era": lab, **_ev(x)})
    return pd.DataFrame(rows)


def imm_positioning(D: pd.DataFrame) -> pd.DataFrame:
    """Follow-positioning P&L (sign(cot_z52) * fwd_1d, gross bp per session) inside vs outside the IMM roll window."""
    x = np.sign(D["cot_z52"]) * D["fwd_1d"]
    rows = []
    for name, m in (("IMM roll window", D["nxt_imm_roll"]), ("all other sessions", ~D["nxt_imm_roll"])):
        for lab, a, b in (("2003-2009", 2003, 2009), ("2010-2015", 2010, 2015), ("2016-2026", 2016, 2026), ("2010-2026", 2010, 2026)):
            rows.append({"window": name, "era": lab, **_ev(x[m.values & (D.index.year >= a) & (D.index.year <= b)])})
    return pd.DataFrame(rows)


# ================================================================== run
def _tbl(pnl: pd.DataFrame, name: str, ppy: float, kind: str = "candidate") -> pd.DataFrame:
    t = report(pnl, periods_per_year=ppy, name=ARM, n_arms=N_VARIANTS)
    t.insert(1, "variant", name)
    t["final"] = False
    t["kind"] = kind
    return t


def _sr(t: pd.DataFrame, period: str, col: str = "sharpe") -> float:
    return float(t.set_index("period").loc[period, col])


def run_all(cost_pips: float = 1.2, verbose: bool = True):
    """All 12 candidates + benchmarks. Returns dict with frames, per-variant pnl and report tables."""
    D = load_frame()
    M = ecb_monthly_returns()
    slog: dict = {}
    P = daily_positions(D, M, season_log=slog)
    pnl, tbl = {}, {}
    for v in DAILY_VARIANTS:
        pnl[v] = daily_pnl(D, P[v], cost_pips)
        pnl[v]["fwd_bp"] = D["fwd_1d"].reindex(pnl[v].index)
        tbl[v] = _tbl(pnl[v], v, 252)
    F = fix_frame()
    S = fix_streams(F, cost_pips)
    for v in INTRADAY_VARIANTS:
        pnl[v] = S[v][S[v].index.year >= 2010].copy()
        tbl[v] = _tbl(pnl[v], v, 12)
    # benchmarks (not eligible)
    bench = {}
    for v in ("bench_fix_follow", "bench_fix_follow_disagree"):
        bench[v] = (S[v][S[v].index.year >= 2010], 12)
    nxt_month = D["nxt_month"].fillna(D["month"])
    live_season = pd.Series(np.where(nxt_month == 12, 1.0, np.where(nxt_month == 5, -1.0, 0.0)), index=D.index)
    live_tom = pd.Series(np.where((D["bd_to_end"] <= 1) | (D["bd_from_start"] <= 3), -1.0, 0.0), index=D.index)
    extra = {"bench_live_season_dec_may": live_season, "bench_live_tom": live_tom, "bench_blackout_trend_outside": pos_blackout(D, inside=False),
             "diag_reb_d3_row": pos_reb_d3(D, "rel_row"), "diag_reb_d3_dax": pos_reb_d3(D, "rel_dax"),
             "placebo_reb_midmonth_8_6": pos_reb_d3(D, "rel", window=(8, 7, 6)), "placebo_reb_midmonth_13_11": pos_reb_d3(D, "rel", window=(13, 12, 11)),
             "bench_live_season_dec_only": live_season.clip(lower=0), "bench_live_season_may_only": live_season.clip(upper=0),
             "diag_eqrel20_sign_all_days": -np.sign(D["spx_minus_sx5e_20"]).fillna(0.0),
             "diag_eqrel20_sign_last3": (-np.sign(D["spx_minus_sx5e_20"])).where(D["bd_to_end"].isin((3, 2, 1)), 0.0).fillna(0.0)}
    for v, pos in extra.items():
        pos = pos.where(pos.index.year >= 2010, 0.0)
        x = daily_pnl(D, pos, cost_pips)
        x["fwd_bp"] = D["fwd_1d"].reindex(x.index)
        bench[v] = (x, 252)
    btbl = {v: _tbl(x, v, ppy, "benchmark_or_diagnostic") for v, (x, ppy) in bench.items()}
    if verbose:
        for v, t in {**tbl, **btbl}.items():
            print(f"{v:32s} 2010-15 {_sr(t,'2010-2015'):+.2f} | 2010-26 {_sr(t,'2010-2026'):+.2f} t {_sr(t,'2010-2026','t'):+.2f} | "
                  f"2016-26 {_sr(t,'2016-2026'):+.2f} | 2023-26 {_sr(t,'2023-2026'):+.2f}", flush=True)
    return {"D": D, "M": M, "P": P, "F": F, "S": S, "pnl": pnl, "tbl": tbl, "bench": bench, "btbl": btbl, "season_log": slog}


def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Entry point: runs the 12 candidates walk-forward, applies the pre-declared selection rule (best 2010-2015 net
    Sharpe), writes the deliverables. Returns (final OOS positions, report DataFrame with all variants)."""
    R = run_all(cost_pips, verbose)
    tbl, pnl = R["tbl"], R["pnl"]
    sel = {v: _sr(t, "2010-2015") for v, t in tbl.items()}
    final = max(sel, key=sel.get)
    if verbose:
        print(f"FINAL by rule (best 2010-2015 net Sharpe): {final} ({sel[final]:+.2f})", flush=True)
    tbl[final]["final"] = True
    rows = list(tbl.values()) + list(R["btbl"].values())
    # cost sensitivity of every candidate at 0.6 pips
    R06 = run_all(0.6, verbose=False)
    for v, t in R06["tbl"].items():
        t = t.copy()
        t["variant"] = f"{v}_cost0.6"
        t["kind"] = "cost_sensitivity"
        rows.append(t)
    rep = pd.concat(rows, ignore_index=True)
    p = pnl[final]
    out = pd.DataFrame({"pos": p["pos"], "fwd_bp": p["fwd_bp"], "net_bp": p["net_bp"]})
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        out.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        allp = pd.DataFrame({v: _session_sum(x["net_bp"]) for v, x in {**pnl, **{k: b[0] for k, b in R["bench"].items()}}.items()}).fillna(0.0)
        allp.to_parquet(RES / f"{ARM}_all_variants_net_bp.parquet")
        allpnl = {**pnl, **{k: b[0] for k, b in R["bench"].items()}}
        hr = pd.concat([hit_rates(x, per_row=("fix" in v)).assign(variant=v) for v, x in allpnl.items()], ignore_index=True)
        pd.concat([R["S"][v].assign(stream=v) for v in R["S"]]).to_parquet(RES / f"{ARM}_fix_decisions.parquet")
        hr.to_csv(RES / f"{ARM}_hit_rates.csv", index=False)
    R["final"] = final
    R["report"] = rep
    run.last = R
    return out["pos"], rep


def _session_sum(net: pd.Series) -> pd.Series:
    idx = pd.DatetimeIndex(net.index)
    key = (idx - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
    return net.groupby(key).sum().sort_index()


# ================================================================== incremental value
def _combo(streams: dict, arms: list[str]) -> pd.DataFrame:
    """meta.combine(arms, 'EW') with in-memory streams for names that are not files (meta itself is not modified)."""
    from eurusd.arms import meta
    orig = meta.load_arm_daily
    meta.load_arm_daily = lambda name: streams[name] if name in streams else orig(name)
    try:
        pnl, w = meta.combine(arms, "EW")
        t = meta.report_combo(pnl, "+".join(arms), N_VARIANTS)
    finally:
        meta.load_arm_daily = orig
    return t


def incremental(R: dict, names: list[str] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Three-way vs two-way EW combination, and daily-P&L correlations with the live arms, for the final variant and
    (for information) every other candidate."""
    from eurusd.arms.meta import load_arm_daily
    allp = {**R["pnl"], **{k: b[0] for k, b in R["bench"].items()}}
    names = (list(R["pnl"]) + ["bench_fix_follow", "bench_live_season_dec_may", "bench_live_tom"]) if names is None else names
    ws, rt = load_arm_daily("weak_signals"), load_arm_daily("regime_trend")
    base = _combo({}, ["weak_signals", "regime_trend"]).set_index("period")
    rows = [{"combo": "weak_signals+regime_trend", **{p: base.loc[p, "sharpe"] for p in ("2010-2026", "2016-2026", "2023-2026", "2013-2026")}}]
    crow = []
    for v in names:
        s = _session_sum(allp[v]["net_bp"])
        t = _combo({"x": s}, ["weak_signals", "regime_trend", "x"]).set_index("period")
        rows.append({"combo": f"weak_signals+regime_trend+{v}", **{p: t.loc[p, "sharpe"] for p in ("2010-2026", "2016-2026", "2023-2026", "2013-2026")}})
        X = pd.DataFrame({"x": s, "ws": ws, "rt": rt}).fillna(0.0)
        X = X[X.index.year >= 2010]
        act = X[X["x"] != 0]
        crow.append({"variant": v, "corr_weak_signals": X.corr().loc["x", "ws"], "corr_regime_trend": X.corr().loc["x", "rt"],
                     "corr_ws_active_days": act.corr().loc["x", "ws"] if len(act) > 20 else np.nan,
                     "corr_rt_active_days": act.corr().loc["x", "rt"] if len(act) > 20 else np.nan,
                     "corr_2016_2026_ws": X[X.index.year >= 2016].corr().loc["x", "ws"], "corr_2016_2026_rt": X[X.index.year >= 2016].corr().loc["x", "rt"]})
    return pd.DataFrame(rows), pd.DataFrame(crow)


def replace_test(R: dict, cost_pips: float = 1.2) -> pd.DataFrame:
    """Should the flow signals REPLACE `season` and `tom` inside the live weak-signal combination? Re-runs the live
    final variant (tstat_sign) of arms/weak_signals.py in-process with (a) the original 14 signals, (b) season/tom
    dropped, (c) season -> season_js and tom -> reb_d3 + nm_rev_sig, (d) the originals plus the new ones.
    The weak_signals module and its files are not modified (its SIGNALS dict is extended in memory only)."""
    from eurusd.arms import weak_signals as WS
    from eurusd.arms.meta import load_arm_daily
    Dw = WS.load_frame()
    D = R["D"]
    # new raw signals on the FULL history (the training window needs them): parameter-free rules on all rows, and the
    # season estimate re-built walk-forward for every year from 2004 (table for year Y uses ECB months of years < Y)
    M = R["M"]
    nm = D["nxt_month"].fillna(D["month"]).astype(int)
    sj = pd.Series(0.0, index=D.index)
    for Y in sorted(set(D.index.year)):
        if Y < 2004:
            continue
        tab = season_table(M, Y)
        m = D.index.year == Y
        sj[m] = nm[m].map(tab["pos"]).values
    Dw["fc_season"] = sj.reindex(Dw.index).fillna(0.0)       # kind 'cont': scaled by the TRAINING-window std inside weak_signals
    Dw["fc_monthend"] = (pos_reb_d3(D) + pos_nm_rev_sig(D)).clip(-1, 1).reindex(Dw.index).fillna(0.0)
    added = {"fc_season": (+1, "cont", "flows_calendar season_js"), "fc_monthend": (+1, "bin", "flows_calendar reb_d3 + nm_rev_sig")}
    base = list(WS.SIGNALS)
    WS.SIGNALS.update(added)
    rt = load_arm_daily("regime_trend")
    rows = []
    try:
        sets = {"original_14": base, "drop_season_tom": [s for s in base if s not in ("season", "tom")],
                "replace_season_tom_with_flows": [s for s in base if s not in ("season", "tom")] + ["fc_season", "fc_monthend"],
                "replace_season_only": [s for s in base if s != "season"] + ["fc_season"],
                "replace_tom_only": [s for s in base if s != "tom"] + ["fc_monthend"],
                "add_flows_keep_originals": base + ["fc_season", "fc_monthend"]}
        for nm_, sigs in sets.items():
            pos, pnl, t = WS.run_variant(Dw, "tstat", "sign", sigs, cost_pips, nm_)
            c = _combo({"ws_alt": _session_sum(pnl["net_bp"])}, ["ws_alt", "regime_trend"]).set_index("period")
            rows.append({"weak_signals_inputs": nm_, "n_signals": len(sigs), "SR_2010_2026": _sr(t, "2010-2026"), "t_2010_2026": _sr(t, "2010-2026", "t"),
                         "SR_2016_2026": _sr(t, "2016-2026"), "SR_2023_2026": _sr(t, "2023-2026"),
                         "EW_with_regime_trend_2010_2026": c.loc["2010-2026", "sharpe"], "EW_with_regime_trend_2016_2026": c.loc["2016-2026", "sharpe"],
                         "EW_with_regime_trend_2023_2026": c.loc["2023-2026", "sharpe"]})
    finally:
        for k in added:
            WS.SIGNALS.pop(k, None)
    return pd.DataFrame(rows)


# ================================================================== leak checks
def leak_checks(R: dict, cost_pips: float = 1.2, seed: int = 0, n_shuffles: int = 20) -> pd.DataFrame:
    """(1) shuffled labels (fwd_1d / fix-window returns / ECB training months permuted): Sharpe ~ 0;
    (2) signals shifted forward by one period (previous month's equity signal; month-of-year estimate of the previous
        month; calendar windows moved one session late) and a look-ahead control (unlagged equity signal measured
        through the trading window);
    (3) correlation of every raw signal with the label."""
    D, M, F = R["D"], R["M"], R["F"]
    out = []

    def rec(check, variant, pnl, ppy):
        t = report(pnl, periods_per_year=ppy, name=ARM, n_arms=1).set_index("period")
        out.append({"check": check, "variant": variant, "SR_2010_2026": t.loc["2010-2026", "sharpe"], "t_2010_2026": t.loc["2010-2026", "t"],
                    "SR_2016_2026": t.loc["2016-2026", "sharpe"], "SR_2023_2026": t.loc["2023-2026", "sharpe"]})
    for v in DAILY_VARIANTS:
        rec("actual", v, R["pnl"][v], 252)
    for v in INTRADAY_VARIANTS:
        rec("actual", v, R["pnl"][v], 12)
    # (1) shuffled labels: average over n_shuffles permutations (single permutations of a 12-decisions-a-year rule are noisy)
    rng = np.random.default_rng(seed)
    acc = {v: [] for v in DAILY_VARIANTS + INTRADAY_VARIANTS}
    for _ in range(n_shuffles):
        Ds = D.copy()
        ok = D["fwd_1d"].notna().values
        y = D["fwd_1d"].values.copy()
        y[ok] = rng.permutation(y[ok])
        Ds["fwd_1d"] = y
        Ms = M.copy()
        Ms["ret"] = rng.permutation(M["ret"].values)
        Ps = daily_positions(Ds, Ms)
        for v in DAILY_VARIANTS:
            x = daily_pnl(Ds, Ps[v], cost_pips)
            acc[v].append(_agg(x["net_bp"], 252)["sharpe"])
        Fs = F.copy()
        for c in ("r_1500_1600", "r_1545_1600"):                       # labels; the signal window r_1500_1545 stays in place
            Fs[c] = F[c].values[rng.permutation(len(F))]
        Ss = fix_streams(Fs, cost_pips)
        for v in INTRADAY_VARIANTS:
            x = Ss[v][Ss[v].index.year >= 2010]
            acc[v].append(_agg(x["net_bp"], 12)["sharpe"])
    for v, a in acc.items():
        out.append({"check": f"shuffled_labels_mean_of_{n_shuffles}", "variant": v, "SR_2010_2026": float(np.mean(a)), "t_2010_2026": np.nan,
                    "SR_2016_2026": np.nan, "SR_2023_2026": np.nan, "sd_across_shuffles": float(np.std(a))})
    # (2a) equity signal of the PREVIOUS month (shifted forward by one period = one month)
    Dp = D.copy()
    for c in ("rel",):
        e3 = D[c].where(D["bd_to_end"] == 3).groupby(D["ym"]).first().shift(1)
        e1 = D[c].where(D["bd_to_end"] == 1).groupby(D["ym"]).first().shift(1)
        e0 = D[c].where(D["bd_to_end"] == 0).groupby(D["ym"]).first().shift(1)
        Dp[c] = np.where(D["bd_to_end"] == 0, D["ym"].map(e0), np.where(D["bd_to_end"] == 1, D["ym"].map(e1), D["ym"].map(e3)))
    Pp = daily_positions(Dp, M, season_shift=1)
    for v in ("reb_d3", "reb_d1", "reb_d3_lin", "nm_rev_sig", "season_js", "flows_core"):
        x = daily_pnl(D, Pp[v], cost_pips)
        rec("signal_shifted_one_period (prev month's equity signal / prev month's season estimate)", v, x, 252)
    # (2b) all daily positions one session late
    for v in DAILY_VARIANTS:
        x = daily_pnl(D, R["P"][v].shift(1).fillna(0.0), cost_pips)
        rec("positions_one_session_late", v, x, 252)
    for v in ("blackout_trend", "hol_square", "nm_rev_px"):
        x = daily_pnl(D, R["P"][v].shift(-1).fillna(0.0), cost_pips)
        rec("LOOKAHEAD_CONTROL positions from the next session's signal", v, x, 252)
    Fp = F.copy()
    Fp["rel"] = F["rel"].shift(1)
    Sp = fix_streams(Fp, cost_pips)
    for v in INTRADAY_VARIANTS:
        rec("signal_shifted_one_period (prev month's equity signal / prev month's season estimate)", v, Sp[v][Sp[v].index.year >= 2010], 12)
    # (2c) look-ahead control: unlagged equity signal measured at the END of the trading window (must not be read as a result)
    Da = D.copy()
    endval = D["rel_nolag"].where(D["bd_to_end"] == 0).groupby(D["ym"]).first()
    Da["rel"] = D["ym"].map(endval).values
    x = daily_pnl(D, pos_reb_d3(Da).where(D.index.year >= 2010, 0.0), cost_pips)
    rec("LOOKAHEAD_CONTROL rel measured through T, unlagged", "reb_d3", x, 252)
    x = daily_pnl(D, np.sign(D["fwd_1d"]).where(D["bd_to_end"].isin((3, 2, 1)) & (D.index.year >= 2010), 0.0).fillna(0.0), cost_pips)
    rec("LOOKAHEAD_CONTROL perfect foresight on the 3 month-end sessions", "reb_d3", x, 252)
    # (3) signal / label correlations
    raw = {"rel@T-3 vs sum fwd (T-2..T)": (D["rel"].where(D["bd_to_end"] == 3).groupby(D["ym"]).first(), D["fwd_1d"].where(D["bd_to_end"].isin((3, 2, 1))).groupby(D["ym"]).sum(min_count=1)),
           "rel (all rows) vs fwd_1d": (D["rel"], D["fwd_1d"]), "-cot_z52 (IMM rows) vs fwd_1d": (-D["cot_z52"].where(D["nxt_imm_roll"]), D["fwd_1d"]),
           "-ret_5d (pre-holiday rows) vs fwd_1d": (-D["ret_5d"].where(D["nxt_pre_hol"]), D["fwd_1d"]),
           "ret_21d (blackout rows) vs fwd_1d": (D["ret_21d"].where(D["blackout"]), D["fwd_1d"]),
           "season_js position vs fwd_1d": (R["P"]["season_js"].where(R["P"].index.year >= 2010), D["fwd_1d"]),
           "rel@fix vs r_1500_1600": (F["rel"], F["r_1500_1600"])}
    for k, (a, b) in raw.items():
        j = pd.concat([a, b], axis=1).dropna()
        out.append({"check": "signal_label_corr", "variant": k, "corr": float(j.corr().iloc[0, 1]), "n": len(j)})
    return pd.DataFrame(out)


if __name__ == "__main__":
    cost = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    pos, rep = run(cost_pips=cost)
    R = run.last
    final = R["final"]
    print("\n== hit rates (final)\n", hit_rates(R["pnl"][final], per_row=("fix" in final)).round(3).to_string(index=False))
    met = month_end_table(R["D"], R["F"])
    met.to_csv(RES / f"{ARM}_month_end_table.csv", index=False)
    T, J = month_stability_table()
    T.to_csv(RES / f"{ARM}_month_stability.csv", index=False)
    J.to_csv(RES / f"{ARM}_month_joint_test.csv", index=False)
    pd.concat([t.assign(test_year=y) for y, t in R["season_log"].items()]).to_csv(RES / f"{ARM}_season_wf_table.csv")
    descriptives(R["D"]).to_csv(RES / f"{ARM}_descriptives.csv", index=False)
    ffd = fix_follow_by_day(R["F"]); ffd.to_csv(RES / f"{ARM}_fix_follow_by_day.csv", index=False)
    sl = season_legs(R["D"]); sl.to_csv(RES / f"{ARM}_season_legs.csv", index=False)
    ip = imm_positioning(R["D"]); ip.to_csv(RES / f"{ARM}_imm_positioning.csv", index=False)
    print("\n== fix follow by day\n", ffd.round(2).to_string(index=False), "\n== season legs\n", sl.round(2).to_string(index=False), "\n== imm positioning\n", ip.round(2).to_string(index=False))
    inc, cor = incremental(R)
    inc.to_csv(RES / f"{ARM}_incremental.csv", index=False)
    cor.to_csv(RES / f"{ARM}_pnl_corr.csv", index=False)
    print("\n== incremental\n", inc.round(3).to_string(index=False), "\n", cor.round(3).to_string(index=False))
    rp = replace_test(R, cost)
    rp.to_csv(RES / f"{ARM}_replace_test.csv", index=False)
    print("\n== replace test\n", rp.round(3).to_string(index=False))
    lc = leak_checks(R, cost)
    lc.to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
    print("\n== leak checks\n", lc.round(3).to_string(index=False))
