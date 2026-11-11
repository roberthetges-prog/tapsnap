"""Arm I ("macro_nowcast"), round 3: the ACCUMULATED macro picture as a slow EUR/USD signal.

Round 2: single releases are absorbed in the release bar (arm_events) and the only surviving predictability is
slow macro drift. Untested middle ground = the accumulated macro picture. Two families of NEW information:

(1) ECONOMIC SURPRISE INDEX per economy (Citi style) from the ForexFactory archive in data/macro/events.csv.
    Universe: every release of an event type that has been rated Medium/High at or before that release (causal,
    keeps the universe stable when ForexFactory later downgrades a type), with numeric actual and forecast.
    surprise = SIGN * (actual - forecast), SIGN from the hand-made map SIGN_MAP below (positive = stronger
    economy / higher inflation; types with no growth/inflation reading are explicitly excluded).
    z = surprise / sd of the previous <= 60 surprises of the same event type (>= 8 needed, strictly earlier
    releases only), clipped at +-3. Index = exponentially decayed mean of the z's (half-life 10/30/60 days).
    Signal for EUR/USD = EUR index - USD index (level, 20-session change, growth-only, inflation-only).
    The archive has NO rows for 2024-01..2025-09 (and thin rows in 2025-Q4, none 2026-10-08..): the index is
    UNDEFINED there. Validity rule (data driven, no dates hard-coded): c_t = 1 when >= NMIN usable releases of the
    currency and category fall in the last 35 days (NMIN = 10 all / 8 growth / 3 inflation) and at least one
    release of the currency in the last 10 days; the index is valid when the exponentially weighted mean of c_t
    (same half-life) is >= 0.75, i.e. two half-lives of continuous coverage. Invalid -> signal NaN -> position 0.
(2) DATA MOMENTUM from the published LEVELS (FRED mirrors, ECB/Eurostat), which have no archive hole:
    US payrolls, unemployment, real retail sales, industrial production, housing starts, weekly jobless claims,
    CPI; EA HICP and unemployment. Momentum = 3-month annualised change minus 12-month change. Each component is
    scaled by a robust trailing scale (1.4826 * median |x| of the previous 120 months, earlier values only).
    US-minus-EA growth and inflation momentum, and a Taylor-rule differential (Molodtsova-Papell):
    TR = 1.5 * inflation(12m) - 1.0 * unemployment gap (gap = rate - trailing 10-year mean; Okun coefficient 2
    on an output-gap weight of 0.5), differential = TR_US - TR_EA, level and 63-session change.
    Publication lags: see PUBLICATION LAGS below; every series is additionally lagged one calendar day
    (featstore._align_lagged), i.e. a release is first used at the NEXT session close.

Orientation: every signal is oriented so that the economic prior says "positive -> long EUR/USD next session".
Standardisation and mapping are the house method of arms/weak_signals.py: `cont` signals divided by the
training-window sd (no demeaning), `level` signals demeaned with the training mean, clipped at +-2 and halved;
position = sign(z) when |z| > training median of |z| (over rows where the signal exists), times the vol scale
min(1, median_train(rv_21d_bp) / rv_21d_bp). A signal needs >= 250 available training rows, otherwise position 0
(the surprise index starts in 2010, so its first out-of-sample year is 2012).

CANDIDATE VARIANTS (12, fixed before any result): 11 single signals (SIGNALS below) + 1 walk-forward
t-stat-weighted combination of all 11 (house `tstat` weights: w_i = max(t_i, 0) of the training-window
correlation with fwd_1d; `sign` mapping).

SELECTION RULE (declared before any result was looked at): the final variant is the candidate with the highest
2010-2015 walk-forward NET Sharpe at 1.2 pips among candidates that hold a position in at least 4 of the 6
years 2010-2015. Its full 2010-2026 record is reported. 2016+ and 2023-2026 are never used for any choice.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.wf import walk_forward, pnl_from_positions, report, to_positions  # noqa: E402

FEATURES = ROOT / "data/processed/features_daily.parquet"
MACRO = ROOT / "data/macro"
RES = ROOT / "experiments/results/arms"
ARM = "macro_nowcast"
N_VARIANTS = 12
CCYS = ("USD", "EUR", "GBP", "JPY")          # GBP / JPY indices are saved as controls only, never traded
HALF_LIVES = (10, 30, 60)
MIN_TRAIN_ROWS = 250
Q_SIGN = 0.50
G, I = "growth", "inflation"

# ------------------------------------------------------------------------------------------------ sign map
# (currency, event) -> (category, sign) ; sign +1: higher than forecast = stronger economy / higher inflation,
# -1: higher than forecast = weaker economy. None = explicitly excluded (no growth / inflation reading:
# policy rates, votes, external and fiscal balances, monetary aggregates, inventories, auctions).
SIGN_MAP: dict[tuple[str, str], tuple[str, int] | None] = {}


def _reg(ccy: str, cat_sign, names: list[str]) -> None:
    for n in names:
        SIGN_MAP[(ccy, n)] = cat_sign


_reg("USD", (G, +1), [
    "ADP Non-Farm Employment Change", "Non-Farm Employment Change", "JOLTS Job Openings",
    "Advance GDP q/q", "Prelim GDP q/q", "Final GDP q/q", "Retail Sales m/m", "Core Retail Sales m/m",
    "Personal Spending m/m", "Personal Income m/m", "Durable Goods Orders m/m", "Core Durable Goods Orders m/m",
    "Factory Orders m/m", "Industrial Production m/m", "Capacity Utilization Rate",
    "ISM Manufacturing PMI", "ISM Services PMI", "Chicago PMI", "Philly Fed Manufacturing Index",
    "Empire State Manufacturing Index", "Richmond Manufacturing Index", "Flash Manufacturing PMI",
    "Flash Services PMI", "Final Manufacturing PMI", "Final Services PMI", "CB Consumer Confidence",
    "Prelim UoM Consumer Sentiment", "Revised UoM Consumer Sentiment", "CB Leading Index m/m",
    "Building Permits", "Housing Starts", "Existing Home Sales", "New Home Sales", "Pending Home Sales m/m",
    "NAHB Housing Market Index", "S&P/CS Composite-20 HPI y/y", "Prelim Nonfarm Productivity q/q",
    "Revised Nonfarm Productivity q/q"])
_reg("USD", (G, -1), ["Unemployment Claims", "Unemployment Rate"])
_reg("USD", (I, +1), [
    "CPI m/m", "CPI y/y", "Core CPI m/m", "Core CPI y/y", "Core PCE Price Index m/m", "PPI m/m", "Core PPI m/m",
    "Import Prices m/m", "Average Hourly Earnings m/m", "Employment Cost Index q/q", "Prelim Unit Labor Costs q/q",
    "Advance GDP Price Index q/q", "Prelim GDP Price Index q/q", "Final GDP Price Index q/q", "ISM Manufacturing Prices"])
_reg("USD", None, [
    "Crude Oil Inventories", "Business Inventories m/m", "Final Wholesale Inventories m/m", "Trade Balance",
    "Goods Trade Balance", "Current Account", "Federal Budget Balance", "TIC Long-Term Purchases",
    "Federal Funds Rate", "Fed Chairman Nomination Vote"])

_reg("EUR", (G, +1), [
    "Flash Manufacturing PMI", "Flash Services PMI", "Final Manufacturing PMI", "Final Services PMI",
    "German Flash Manufacturing PMI", "German Flash Services PMI", "German Final Manufacturing PMI",
    "German Final Services PMI", "French Flash Manufacturing PMI", "French Flash Services PMI",
    "Italian Manufacturing PMI", "Italian Services PMI", "Spanish Manufacturing PMI", "Spanish Services PMI",
    "German ifo Business Climate", "German ZEW Economic Sentiment", "ZEW Economic Sentiment",
    "Sentix Investor Confidence", "Belgian NBB Business Climate", "German GfK Consumer Climate",
    "Flash GDP q/q", "Prelim Flash GDP q/q", "German Prelim GDP q/q", "French Prelim GDP q/q", "French Flash GDP q/q",
    "Italian Prelim GDP q/q", "Spanish Flash GDP q/q", "Retail Sales m/m", "German Retail Sales m/m",
    "French Consumer Spending m/m", "Industrial Production m/m", "German Industrial Production m/m",
    "French Industrial Production m/m", "Italian Industrial Production m/m", "German Factory Orders m/m",
    "Industrial New Orders m/m", "French Prelim Private Payrolls q/q"])
_reg("EUR", (G, -1), [
    "Unemployment Rate", "German Unemployment Change", "Spanish Unemployment Change", "Spanish Unemployment Rate",
    "Italian Monthly Unemployment Rate", "Italian Quarterly Unemployment Rate"])
_reg("EUR", (I, +1), [
    "CPI Flash Estimate y/y", "Core CPI Flash Estimate y/y", "Final CPI y/y", "Final Core CPI y/y",
    "German Prelim CPI m/m", "Spanish Flash CPI y/y", "German PPI m/m"])
_reg("EUR", None, [
    "Main Refinancing Rate", "Long Term Refinancing Operation", "M3 Money Supply y/y", "Private Loans y/y",
    "Current Account", "German Trade Balance", "Greek Gov Debt Crisis Vote", "Irish Stability Treaty Vote"])

_reg("GBP", (G, +1), [
    "Retail Sales m/m", "BRC Retail Sales Monitor y/y", "CBI Realized Sales", "CBI Industrial Order Expectations",
    "Manufacturing Production m/m", "Construction Output m/m", "Construction PMI", "Final Manufacturing PMI",
    "Final Services PMI", "Flash Manufacturing PMI", "Flash Services PMI", "GDP m/m", "Prelim GDP q/q",
    "Second Estimate GDP q/q", "Final GDP q/q", "Prelim Business Investment q/q", "GfK Consumer Confidence",
    "Nationwide Consumer Confidence", "Halifax HPI m/m", "Nationwide HPI m/m", "ONS HPI y/y",
    "RICS House Price Balance", "High Street Lending", "Net Lending to Individuals m/m", "Prelim Mortgage Approvals"])
_reg("GBP", (G, -1), ["Claimant Count Change", "Unemployment Rate"])
_reg("GBP", (I, +1), ["CPI y/y", "Core CPI y/y", "RPI y/y", "PPI Input m/m", "Average Earnings Index 3m/y"])
_reg("GBP", None, [
    "Official Bank Rate", "MPC Official Bank Rate Votes", "Asset Purchase Facility", "MPC Asset Purchase Facility Votes",
    "Current Account", "Goods Trade Balance", "Public Sector Net Borrowing", "Parliament Brexit Vote",
    "Scottish Independence Vote"])

_reg("JPY", (G, +1), [
    "Prelim GDP q/q", "Final GDP q/q", "Tankan Manufacturing Index", "Tankan Non-Manufacturing Index",
    "BSI Manufacturing Index", "Capital Spending q/y", "Core Machinery Orders m/m", "Household Spending y/y",
    "Retail Sales y/y", "Prelim Industrial Production m/m", "Revised Industrial Production m/m",
    "Tertiary Industry Activity m/m", "All Industries Activity m/m", "Leading Indicators"])
_reg("JPY", (I, +1), ["Tokyo Core CPI y/y", "National Core CPI y/y", "Prelim GDP Price Index y/y", "Average Cash Earnings y/y"])
_reg("JPY", None, ["BOJ Policy Rate", "Overnight Call Rate", "Monetary Base y/y", "Current Account", "Trade Balance"])

# ------------------------------------------------------------------------------------------------ signals
# name: (kind, description). All are ALREADY oriented (positive -> long EUR/USD under the prior).
SIGNALS = {
    "esi10":      ("cont",  "+ (EUR - USD) surprise index, all releases, half-life 10 days"),
    "esi30":      ("cont",  "+ (EUR - USD) surprise index, all releases, half-life 30 days"),
    "esi60":      ("cont",  "+ (EUR - USD) surprise index, all releases, half-life 60 days"),
    "esi_chg":    ("cont",  "+ 20-session change of the half-life-30 (EUR - USD) surprise index"),
    "esi_gro":    ("cont",  "+ (EUR - USD) GROWTH surprise index, half-life 30 days"),
    "esi_inf":    ("cont",  "+ (EUR - USD) INFLATION surprise index, half-life 30 days"),
    "gmom":       ("cont",  "- (US growth-momentum composite - EA growth momentum [unemployment only])"),
    "imom":       ("cont",  "- (US CPI momentum - EA HICP momentum), 3m annualised minus 12m"),
    "taylor":     ("level", "- Taylor-rule differential TR_US - TR_EA (level, demeaned in training)"),
    "taylor_chg": ("cont",  "- 63-session change of the Taylor-rule differential"),
    "us_act":     ("cont",  "- US growth-momentum composite alone (6 series, no EA leg)"),
}
SURPRISE_SIGNALS = ("esi10", "esi30", "esi60", "esi_chg", "esi_gro", "esi_inf")

# ------------------------------------------------------------------------------------------------ PUBLICATION LAGS
# stamp = date from which a reference period counts as published; the feature store's extra calendar day is added on top.
#   PAYEMS, UNRATE : first "Employment Situation" date in us_bls_releases.csv on/after the 1st of the following month
#   CPIAUCSL       : first "CPI" date in us_bls_releases.csv on/after the 1st of the following month
#   (before 2010 the calendar has no rows -> reference month end + 45 days)
#   RSAFS, INDPRO, HOUST, EA HICP (FRED CP0000EZ19M086NEST), EA unemployment : reference month end + 45 days
#   ICSA (weekly, week ending Saturday, published the next Thursday) : week end + 6 days
#   2025 US government shutdown (calendar rows are the ORIGINAL schedule there) - overrides written from memory,
#   conservative: Sept-2025 jobs 2025-11-20, Oct/Nov-2025 jobs 2025-12-16, Sept-2025 CPI 2025-10-24,
#   Nov-2025 CPI 2025-12-18 (Oct-2025 CPI and unemployment rate were never published; missing in FRED too);
#   Census/Fed series for reference months 2025-08..2025-11: month end + 100 days; jobless-claims weeks ending
#   2025-09-27..2025-11-08: not before 2025-11-21.
LAG_DEFAULT_DAYS = 45
BLS_OVERRIDE = {
    ("Employment Situation", "2025-09"): "2025-11-20", ("Employment Situation", "2025-10"): "2025-12-16",
    ("Employment Situation", "2025-11"): "2025-12-16", ("CPI", "2025-09"): "2025-10-24",
    ("CPI", "2025-10"): "2025-12-18", ("CPI", "2025-11"): "2025-12-18",
}
SHUTDOWN_MONTHS = pd.period_range("2025-08", "2025-11", freq="M")


# ================================================================================================ surprise index
def _num(x) -> float:
    if pd.isna(x):
        return np.nan
    m = re.fullmatch(r"(-?\d+(?:\.\d+)?)([KMBT]?)", str(x).strip().replace(",", "").replace("%", ""))
    if not m:
        return np.nan
    return float(m.group(1)) * {"": 1.0, "K": 1e3, "M": 1e6, "B": 1e9, "T": 1e12}[m.group(2)]


def load_releases() -> pd.DataFrame:
    """One row per usable release: ccy, event, cat, avail (UTC time from which it may be used), z."""
    e = pd.read_csv(MACRO / "events.csv")
    e = e[e.source.str.startswith("ff_") & e.currency.isin(CCYS)].copy()
    e["t"] = pd.to_datetime(e.datetime_utc, utc=True)
    e = e.sort_values(["t", "source"]).reset_index(drop=True)
    # causal universe: the type has been rated Medium/High at or before this release
    e["mh"] = e.impact.isin(["Medium", "High"])
    e["ever"] = e.groupby(["currency", "event"]).mh.cummax()
    e["a"] = e.actual.map(_num)
    e["f"] = e.forecast.map(_num)
    u = e[e.ever & e.a.notna() & e.f.notna()].copy()
    unmapped = sorted(set(zip(u.currency, u.event)) - set(SIGN_MAP))
    if unmapped:
        raise KeyError(f"event types without an entry in SIGN_MAP: {unmapped}")
    # availability: exact minute for the verified archive; the 2025/2026 mirrors have unreliable clock times
    # ("dates and values are fine"), so they count from the END of their stamped UTC date (one session late)
    exact = (u.source == "ff_archive_2010_2023") & (u.has_time == True)  # noqa: E712
    u["avail"] = np.where(exact, u.t, u.t.dt.floor("D") + pd.Timedelta(days=1))
    u["avail"] = pd.to_datetime(u["avail"], utc=True)
    # de-duplicate overlapping mirrors: same type on the same date, or identical values within 3 days
    u["d"] = u.t.dt.floor("D")
    u = u.drop_duplicates(["currency", "event", "d"], keep="first")
    prev = u.groupby(["currency", "event"])[["t", "a", "f"]].shift(1)
    dup = (u.a == prev.a) & (u.f == prev.f) & ((u.t - prev.t) < pd.Timedelta(days=3))
    u = u[~dup].copy()
    u["map"] = [SIGN_MAP[k] for k in zip(u.currency, u.event)]
    u = u[u["map"].notna()].copy()
    u["cat"] = [m[0] for m in u["map"]]
    u["sgn"] = [m[1] for m in u["map"]]
    u["sur"] = u.sgn * (u.a - u.f)
    sd = u.groupby(["currency", "event"]).sur.transform(lambda s: s.rolling(60, min_periods=8).std().shift(1))
    u["z"] = (u.sur / sd.where(sd > 0)).clip(-3, 3)
    u = u[u.z.notna()]
    return u[["t", "avail", "currency", "event", "cat", "sgn", "a", "f", "z", "impact", "source"]].rename(columns={"currency": "ccy"}).reset_index(drop=True)


def build_surprise_index(close_time: pd.DatetimeIndex, releases: pd.DataFrame | None = None, save: bool = False) -> pd.DataFrame:
    """Session-by-session indices (row j uses releases with avail <= close_time[j]). Columns
    esi_<ccy>_<all|gro|inf>_hl<h> (NaN where the validity rule fails) and raw_/n_ diagnostics."""
    R = load_releases() if releases is None else releases
    ct = pd.DatetimeIndex(close_time)
    ctv = ct.values.astype("datetime64[ns]").astype("int64")
    gap_days = np.r_[1.0, np.diff(ctv) / 86400e9]
    out = {}
    nmin = {"all": 10, "gro": 8, "inf": 3}
    for ccy in CCYS:
        av_all = np.sort(R.avail[R.ccy == ccy].values.astype("datetime64[ns]").astype("int64"))
        n10 = np.searchsorted(av_all, ctv, side="right") - np.searchsorted(av_all, ctv - int(10 * 86400e9), side="right")
        for cat in ("all", "gro", "inf"):
            r = R[(R.ccy == ccy)] if cat == "all" else R[(R.ccy == ccy) & (R.cat == (G if cat == "gro" else I))]
            av = r.avail.values.astype("datetime64[ns]").astype("int64")
            j = np.searchsorted(ctv, av, side="left")              # first session whose close is >= avail
            ok = j < len(ct)
            sumz = np.bincount(j[ok], weights=r.z.values[ok], minlength=len(ct))
            cnt = np.bincount(j[ok], minlength=len(ct)).astype(float)
            avs = np.sort(av)
            n35 = np.searchsorted(avs, ctv, side="right") - np.searchsorted(avs, ctv - int(35 * 86400e9), side="right")
            c = ((n35 >= nmin[cat]) & (n10 >= 1)).astype(float)
            out[f"n_{ccy}_{cat}"] = cnt
            for hl in HALF_LIVES:
                d = 0.5 ** (gap_days / hl)
                num = np.zeros(len(ct)); den = np.zeros(len(ct)); cov = np.zeros(len(ct))
                a = b = k = 0.0
                for i in range(len(ct)):
                    a = a * d[i] + sumz[i]
                    b = b * d[i] + cnt[i]
                    k = k * d[i] + (1 - d[i]) * c[i]
                    num[i], den[i], cov[i] = a, b, k
                raw = np.where(den > 1e-9, num / np.maximum(den, 1e-9), np.nan)
                out[f"esi_{ccy}_{cat}_hl{hl}"] = np.where(cov >= 0.75, raw, np.nan)
                out[f"raw_{ccy}_{cat}_hl{hl}"] = raw
    X = pd.DataFrame(out, index=ct)
    for cat in ("all", "gro", "inf"):
        for hl in HALF_LIVES:
            X[f"esi_EURmUSD_{cat}_hl{hl}"] = X[f"esi_EUR_{cat}_hl{hl}"] - X[f"esi_USD_{cat}_hl{hl}"]
    if save:
        S = X[X.index.year >= 2010].copy()
        S.insert(0, "date", S.index.tz_convert("UTC").strftime("%Y-%m-%d"))
        S.insert(1, "close_time_utc", S.index.strftime("%Y-%m-%dT%H:%M:%SZ"))
        S.round(5).to_csv(MACRO / "surprise_index.csv", index=False)
    return X


# ================================================================================================ data momentum
def _monthly(name: str) -> pd.Series:
    d = pd.read_csv(MACRO / name)
    s = pd.Series(d.iloc[:, 1].astype(float).values, index=pd.PeriodIndex(pd.to_datetime(d.iloc[:, 0]), freq="M"))
    s = s[~s.index.duplicated()].sort_index()
    return s.reindex(pd.period_range(s.index.min(), s.index.max(), freq="M"))   # missing months stay NaN


def _bls_dates(kind: str) -> np.ndarray:
    b = pd.read_csv(MACRO / "us_bls_releases.csv")
    t = pd.to_datetime(b.loc[b.release == kind, "release_utc"], utc=True).dt.tz_localize(None).dt.normalize()
    return np.sort(t.values)


def _stamp(months: pd.PeriodIndex, kind: str | None) -> pd.DatetimeIndex:
    """Publication stamp of each reference month (see PUBLICATION LAGS)."""
    end = months.to_timestamp(how="end").normalize()
    default = end + pd.Timedelta(days=LAG_DEFAULT_DAYS)
    out = pd.Series(default, index=months)
    if kind is None:
        sh = months.isin(SHUTDOWN_MONTHS)
        out[sh] = (end + pd.Timedelta(days=100))[sh]
        return pd.DatetimeIndex(out.values)
    rel = _bls_dates(kind)
    for i, m in enumerate(months):
        ov = BLS_OVERRIDE.get((kind, str(m)))
        if ov is not None:
            out.iloc[i] = pd.Timestamp(ov)
            continue
        lo = (m + 1).to_timestamp().to_datetime64()
        hi = (m + 3).to_timestamp().to_datetime64()
        k = np.searchsorted(rel, lo, side="left")
        if k < len(rel) and rel[k] < hi:
            out.iloc[i] = pd.Timestamp(rel[k])
    return pd.DatetimeIndex(out.values)


def _robust_z(x: pd.Series, window: int = 120, minp: int = 36) -> pd.Series:
    """x / (1.4826 * median |x| of the previous `window` observations), clipped at +-3. Earlier values only."""
    sc = 1.4826 * x.abs().rolling(window, min_periods=minp).median().shift(1)
    return (x / sc.where(sc > 0)).clip(-3, 3)


def _accel(logx: pd.Series) -> pd.Series:
    """3-month annualised change minus 12-month change (in % for a log level, in points for a rate)."""
    return 4 * (logx - logx.shift(3)) - (logx - logx.shift(12))


def _to_daily(s: pd.Series, stamps: pd.DatetimeIndex, cdate: pd.DatetimeIndex, max_stale_days: int = 150) -> pd.Series:
    """Monthly values stamped at their publication date -> value known at each session close (one extra
    calendar day of lag, as featstore._align_lagged); NaN when the newest stamp is older than max_stale_days."""
    v = pd.Series(s.values, index=stamps).dropna()
    v = v[~v.index.duplicated(keep="last")].sort_index()
    v = v[v.index.to_series().cummax().values == v.index.values] if len(v) else v     # keep monotone stamps only
    target = pd.DatetimeIndex(cdate) - pd.Timedelta(days=1)
    val = v.reindex(v.index.union(target)).sort_index().ffill().reindex(target).values
    last = pd.Series(v.index, index=v.index).reindex(v.index.union(target)).sort_index().ffill().reindex(target).values
    age = (target.values - last) / np.timedelta64(1, "D")
    return pd.Series(np.where(age <= max_stale_days, val, np.nan), index=cdate)


def build_data_momentum(cdate: pd.DatetimeIndex) -> pd.DataFrame:
    """Daily (per session close date) data-momentum features. cdate = tz-naive UTC date of each session close."""
    out = pd.DataFrame(index=cdate)
    pay, unr, cpi = _monthly("fred_PAYEMS.csv"), _monthly("fred_UNRATE.csv"), _monthly("fred_CPIAUCSL.csv")
    rs, ip, hs = _monthly("fred_RSAFS.csv"), _monthly("fred_INDPRO.csv"), _monthly("fred_HOUST.csv")
    hicp = _monthly("fred_CP0000EZ19M086NEST.csv")
    eu = pd.read_csv(MACRO / "ea_unemployment.csv")
    eau = pd.Series(eu.unemployment_rate.astype(float).values, index=pd.PeriodIndex(eu.month, freq="M")).sort_index()
    eau = eau.reindex(pd.period_range(eau.index.min(), eau.index.max(), freq="M"))

    def comp(raw: pd.Series, fn, kind):
        """fn on the interior-interpolated series; months that were never published stay NaN."""
        filled = raw.interpolate(limit_area="inside")
        x = fn(filled).where(raw.notna())
        return x, _stamp(raw.index, kind)

    L = lambda s: 100 * np.log(s)  # noqa: E731
    comps = {}
    x, st = comp(pay, lambda s: _accel(L(s)), "Employment Situation");                    comps["payrolls"] = (_robust_z(x), st)
    x, st = comp(unr, lambda s: -_accel(s), "Employment Situation");                      comps["unemployment"] = (_robust_z(x), st)
    cpi_f = cpi.interpolate(limit_area="inside")
    x, st = comp(rs, lambda s: _accel(L(s / cpi_f.reindex(s.index))), None);              comps["real_retail"] = (_robust_z(x), st)
    x, st = comp(ip, lambda s: _accel(L(s)), None);                                       comps["indpro"] = (_robust_z(x), st)
    x, st = comp(hs, lambda s: L(s.rolling(3).mean()) - L(s.rolling(12).mean()), None);   comps["housing_starts"] = (_robust_z(x), st)
    for k, (z, st) in comps.items():
        out[f"us_{k}_z"] = _to_daily(z, st, cdate).values
    # weekly initial claims: 4-week vs 52-week average, sign flipped (fewer claims = stronger)
    ic = pd.read_csv(MACRO / "fred_ICSA.csv", parse_dates=["date"]).set_index("date")["value"].astype(float).sort_index()
    xi = -(100 * np.log(ic.rolling(4).mean()) - 100 * np.log(ic.rolling(52).mean()))
    zi = _robust_z(xi, window=520, minp=156)
    sti = ic.index + pd.Timedelta(days=6)
    sh = (ic.index >= "2025-09-27") & (ic.index <= "2025-11-08")
    sti = pd.DatetimeIndex(np.where(sh, np.maximum(sti.values, np.datetime64("2025-11-21")), sti.values))
    out["us_claims_z"] = _to_daily(zi, sti, cdate, max_stale_days=60).values
    us_cols = [c for c in out.columns if c.startswith("us_") and c.endswith("_z")]
    out["us_growth"] = out[us_cols].mean(axis=1).where(out[us_cols].notna().sum(axis=1) >= 3)
    # EA growth momentum: the unemployment rate is the only euro-area activity series in data/macro
    x, st = comp(eau, lambda s: -_accel(s), None)
    out["ea_growth"] = _to_daily(_robust_z(x), st, cdate).values
    out["gmom_diff"] = out["us_growth"] - out["ea_growth"]
    # inflation momentum: US CPI (SA); EA HICP is NSA -> causal seasonal adjustment of the monthly log change
    # (same-calendar-month mean over the previous 5 years minus the all-month mean of the previous 60 months)
    us_pi3, st_cpi = comp(cpi, lambda s: 4 * (L(s) - L(s).shift(3)), "CPI")
    us_pi12, _ = comp(cpi, lambda s: L(s) - L(s).shift(12), "CPI")
    mm = L(hicp).diff()
    seas = sum(mm.shift(12 * k) for k in range(1, 6)) / 5 - mm.shift(1).rolling(60).mean()
    ea_pi3 = 4 * (mm - seas).rolling(3).sum()
    ea_pi12 = L(hicp) - L(hicp).shift(12)
    st_h = _stamp(hicp.index, None)
    out["us_infl_mom"] = _to_daily(_robust_z(us_pi3 - us_pi12), st_cpi, cdate).values
    out["ea_infl_mom"] = _to_daily(_robust_z(ea_pi3 - ea_pi12), st_h, cdate).values
    out["imom_diff"] = out["us_infl_mom"] - out["ea_infl_mom"]
    # Taylor-rule differential
    ugap_us, st_u = comp(unr, lambda s: s - s.rolling(120, min_periods=36).mean(), "Employment Situation")
    ugap_ea, st_eu = comp(eau, lambda s: s - s.rolling(120, min_periods=36).mean(), None)
    out["us_pi12"] = _to_daily(us_pi12, st_cpi, cdate).values
    out["ea_pi12"] = _to_daily(ea_pi12, st_h, cdate).values
    out["us_ugap"] = _to_daily(ugap_us, st_u, cdate).values
    out["ea_ugap"] = _to_daily(ugap_ea, st_eu, cdate).values
    out["taylor_us"] = 1.5 * out["us_pi12"] - 1.0 * out["us_ugap"]
    out["taylor_ea"] = 1.5 * out["ea_pi12"] - 1.0 * out["ea_ugap"]
    out["taylor_diff"] = out["taylor_us"] - out["taylor_ea"]
    out["taylor_chg63"] = out["taylor_diff"].diff(63)
    return out


# ================================================================================================ signal frame
def build_raw_signals(df: pd.DataFrame, save_index: bool = False) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    ct = pd.DatetimeIndex(df["close_time"])
    X = build_surprise_index(ct, save=save_index)
    X.index = df.index
    cdate = pd.DatetimeIndex(ct.tz_convert("UTC").normalize().tz_localize(None))
    M = build_data_momentum(cdate)
    M.index = df.index
    S = pd.DataFrame(index=df.index)
    S["esi10"] = X["esi_EURmUSD_all_hl10"]
    S["esi30"] = X["esi_EURmUSD_all_hl30"]
    S["esi60"] = X["esi_EURmUSD_all_hl60"]
    S["esi_chg"] = X["esi_EURmUSD_all_hl30"] - X["esi_EURmUSD_all_hl30"].shift(20)
    S["esi_gro"] = X["esi_EURmUSD_gro_hl30"]
    S["esi_inf"] = X["esi_EURmUSD_inf_hl30"]
    S["gmom"] = -M["gmom_diff"]
    S["imom"] = -M["imom_diff"]
    S["taylor"] = -M["taylor_diff"]
    S["taylor_chg"] = -M["taylor_chg63"]
    S["us_act"] = -M["us_growth"]
    return S[list(SIGNALS)], X, M


def load_frame(save_index: bool = False) -> pd.DataFrame:
    df = pd.read_parquet(FEATURES)
    S, _, _ = build_raw_signals(df, save_index=save_index)
    return pd.concat([S, df[["fwd_1d", "rv_21d_bp", "close", "label_end_1d"]]], axis=1)


# ================================================================================================ model (house method)
def _scaler_fit(S: pd.DataFrame) -> dict:
    st = {}
    for k in S.columns:
        x = S[k].dropna()
        if len(x) < MIN_TRAIN_ROWS:
            st[k] = None
            continue
        mu = float(x.mean()) if SIGNALS[k][0] == "level" else 0.0
        st[k] = (mu, float((x - mu).std() if SIGNALS[k][0] == "level" else x.std()) or 1.0)
    return st


def _scaler_apply(S: pd.DataFrame, st: dict) -> pd.DataFrame:
    """Standardised signals in [-1, 1]; NaN where the signal is unavailable (or not yet eligible)."""
    out = pd.DataFrame(index=S.index)
    for k, v in st.items():
        out[k] = np.nan if v is None else ((S[k] - v[0]) / v[1]).clip(-2, 2) / 2
    return out


def _tstat_weights(Z: pd.DataFrame, y: pd.Series) -> np.ndarray:
    t = np.zeros(Z.shape[1])
    elig = np.zeros(Z.shape[1], bool)
    for j, k in enumerate(Z.columns):
        ok = Z[k].notna() & y.notna()
        if ok.sum() < MIN_TRAIN_ROWS or Z.loc[ok, k].std() == 0:
            continue
        elig[j] = True
        r = np.corrcoef(Z.loc[ok, k], y[ok])[0, 1]
        t[j] = r * np.sqrt(ok.sum() - 2) / np.sqrt(max(1e-12, 1 - r * r))
    w = np.clip(t, 0, None)
    if w.sum() <= 0:
        w = elig.astype(float)                      # house fallback: equal weights with the prior signs
    return w / w.sum() if w.sum() > 0 else w


def make_fit_predict(signals: list[str], weight_log: dict | None = None):
    def fit(train: pd.DataFrame):
        st = _scaler_fit(train[signals])
        Z = _scaler_apply(train[signals], st)
        w = _tstat_weights(Z, train["fwd_1d"]) if len(signals) > 1 else np.array([0.0 if st[signals[0]] is None else 1.0])
        score = pd.Series(Z.fillna(0.0).values @ w, index=train.index)
        avail = Z.loc[:, w > 0].notna().any(axis=1) if (w > 0).any() else pd.Series(False, index=train.index)
        a = score[avail].abs()
        thr = float(np.quantile(a, Q_SIGN)) if len(a) >= MIN_TRAIN_ROWS else np.inf
        if weight_log is not None:
            weight_log[train.index.max().year + 1] = pd.Series(w, index=signals)
        return {"st": st, "w": w, "thr": thr, "target_vol": float(train["rv_21d_bp"].median())}

    def predict(m, test: pd.DataFrame) -> pd.Series:
        Z = _scaler_apply(test[signals], m["st"])
        score = pd.Series(Z.fillna(0.0).values @ m["w"], index=test.index)
        pos = np.sign(score).where(score.abs() > m["thr"], 0.0)
        return to_positions(pos, "linear", threshold=1.0, vol=test["rv_21d_bp"], target_vol_bp=m["target_vol"])
    return fit, predict


def run_variant(D: pd.DataFrame, signals: list[str], cost_pips: float, name: str, weight_log: dict | None = None):
    fit, predict = make_fit_predict(signals, weight_log)
    pos = walk_forward(D, fit, predict, label_end=D["label_end_1d"], verbose=False).fillna(0.0)
    pnl = pnl_from_positions(pos, D["fwd_1d"], D["close"], cost_pips=cost_pips)
    pnl = pnl[pos.index.year >= 2010]
    tbl = report(pnl, periods_per_year=252, name=ARM, n_arms=N_VARIANTS)
    tbl.insert(1, "variant", name)
    tbl["cost_pips"] = cost_pips
    return pos, pnl, tbl


def _row(tbl: pd.DataFrame, period: str) -> pd.Series:
    return tbl.set_index("period").loc[period]


def _active_years(tbl: pd.DataFrame, a: int = 2010, b: int = 2015) -> int:
    r = tbl.set_index("period")
    return int(sum(r.loc[str(y), "active_frac"] > 0 for y in range(a, b + 1)))


# ================================================================================================ entry point
def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """12 candidate variants walk-forward, selection rule, cost sensitivity; writes the deliverables.
    Returns (final OOS positions, report DataFrame)."""
    D = load_frame(save_index=write)
    signals = list(SIGNALS)
    cands = {f"single_{s}": [s] for s in signals}
    cands["combo_tstat"] = signals
    assert len(cands) == N_VARIANTS
    rows, store = [], {}
    for name, sigs in cands.items():
        wl = {}
        pos, pnl, tbl = run_variant(D, sigs, cost_pips, name, weight_log=wl)
        tbl["final"] = False
        tbl["kind"] = "candidate"
        store[name] = (pos, pnl, tbl, wl)
        rows.append(tbl)
        _, _, t06 = run_variant(D, sigs, 0.6 if cost_pips != 0.6 else 1.2, name)          # same positions, other cost
        t06["final"] = False
        t06["kind"] = "cost_sensitivity"
        rows.append(t06)
        if verbose:
            r = tbl.set_index("period")
            print(f"{name:18s} 2010-15 SR {r.loc['2010-2015','sharpe']:+.2f} (active yrs {_active_years(tbl)}) | 2010-26 SR {r.loc['2010-2026','sharpe']:+.2f} "
                  f"t {r.loc['2010-2026','t']:+.2f} | 2016-26 SR {r.loc['2016-2026','sharpe']:+.2f} t {r.loc['2016-2026','t']:+.2f} | "
                  f"2023-26 SR {r.loc['2023-2026','sharpe']:+.2f} t {r.loc['2023-2026','t']:+.2f}", flush=True)
    elig = {n: float(_row(t, "2010-2015")["sharpe"]) for n, (_, _, t, _) in store.items() if _active_years(t) >= 4}
    final = max(elig, key=elig.get)
    if verbose:
        print(f"FINAL by rule (best 2010-2015 net Sharpe, >= 4 active years): {final} ({elig[final]:+.2f})", flush=True)
    for t in rows:
        t["final"] = (t["variant"].iloc[0] == final) & (t["kind"].iloc[0] == "candidate")
    rep = pd.concat(rows, ignore_index=True)
    pos, pnl, tbl, wl = store[final]
    out = pd.DataFrame({"pos": pos, "fwd_bp": D["fwd_1d"], "net_bp": pnl["net_bp"].reindex(pos.index)})
    out = out[out.index.year >= 2010]
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        out.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        allpos = pd.DataFrame({n: s[0] for n, s in store.items()})
        allpos = allpos[allpos.index.year >= 2010]
        allpos.to_parquet(RES / f"{ARM}_all_positions.parquet")
        W = pd.DataFrame(store["combo_tstat"][3]).T
        W.index.name = "test_year"
        W.to_csv(RES / f"{ARM}_weights.csv")
    return out["pos"], rep


# ================================================================================================ leak checks
def leak_checks(final: str, cost_pips: float = 1.2, seed: int = 0, n_null: int = 200) -> pd.DataFrame:
    """(1) shuffled labels (5 permutations); (2) features lagged by 1..504 extra sessions and look-ahead controls
    (-5, -21, -63); (2b) circular-shift null: the final signal rolled by a random offset of >= 1 year inside
    2010-2026 (keeps its autocorrelation, destroys its timing) - the right null for a slow signal;
    (3) full-sample correlation of every standardised signal with the label; (4) truncation test of the
    surprise index (value at T must not change when every release available after T is deleted)."""
    D = load_frame()
    signals = list(SIGNALS)
    sigs = signals if final == "combo_tstat" else [final.replace("single_", "")]
    out = []
    rng = np.random.default_rng(seed)
    for k in range(5):
        Ds = D.copy()
        Ds["fwd_1d"] = rng.permutation(D["fwd_1d"].values)
        _, _, t = run_variant(Ds, sigs, cost_pips, f"shuffled_labels_{k}")
        out.append(t.assign(check=f"shuffled_labels_{k}"))
    for lag in (1, 5, 21, 42, 63, 126, 189, 252, 378, 504, -5, -21, -63):
        Dl = D.copy()
        Dl[signals] = D[signals].shift(lag)
        nm = f"features_shift_plus{lag}" if lag > 0 else f"features_shift_minus{-lag}_lookahead_control"
        _, _, t = run_variant(Dl, sigs, cost_pips, nm)
        out.append(t.assign(check=nm))
    idx = np.where(D.index.year >= 2010)[0]
    null = []
    for k in range(n_null):
        off = int(rng.integers(252, len(idx) - 252))
        Dl = D.copy()
        for c in sigs:
            v = D[c].values.copy()
            v[idx] = np.roll(v[idx], off)
            Dl[c] = v
        _, _, t = run_variant(Dl, sigs, cost_pips, "null")
        null.append(t.set_index("period").loc[["2010-2026", "2016-2026", "2023-2026"], "sharpe"].values)
    null = np.array(null)
    _, _, t0 = run_variant(D, sigs, cost_pips, "actual")
    act = t0.set_index("period").loc[["2010-2026", "2016-2026", "2023-2026"], "sharpe"].values
    nulls = pd.DataFrame({"period": ["2010-2026", "2016-2026", "2023-2026"], "sharpe": act, "null_mean": null.mean(0), "null_sd": null.std(0),
                          "null_q95": np.quantile(null, 0.95, axis=0), "p_null_ge_actual": (null >= act).mean(0), "check": "circular_shift_null"})
    st = _scaler_fit(D[signals])
    Z = _scaler_apply(D[signals], st)
    c = Z.corrwith(D["fwd_1d"])
    corr = pd.DataFrame({"period": c.index, "corr_with_fwd_1d": c.values, "n": Z.notna().sum().values, "check": "signal_label_corr"})
    return pd.concat(out + [nulls, corr, truncation_test()], ignore_index=True)


def truncation_test(n_dates: int = 40, seed: int = 0) -> pd.DataFrame:
    """Rebuild the surprise index from releases with avail <= T only and compare the row at T with the full build."""
    df = pd.read_parquet(FEATURES)
    ct = pd.DatetimeIndex(df["close_time"])
    R = load_releases()
    full = build_surprise_index(ct, R)
    cols = [c for c in full.columns if c.startswith("esi_")]
    rng = np.random.default_rng(seed)
    cand = np.where((ct.year >= 2011) & (ct.year <= 2026))[0]
    worst = 0.0
    nan_mismatch = 0
    for i in rng.choice(cand, n_dates, replace=False):
        part = build_surprise_index(ct[: i + 1], R[R.avail <= ct[i]])
        a, b = full.iloc[i][cols].values.astype(float), part.iloc[i][cols].values.astype(float)
        nan_mismatch += int((np.isnan(a) != np.isnan(b)).sum())
        worst = max(worst, float(np.nanmax(np.abs(a - b))) if np.isfinite(a - b).any() else 0.0)
    return pd.DataFrame([{"period": f"{n_dates} random sessions", "max_abs_diff": worst, "nan_mismatch": nan_mismatch, "check": "surprise_index_truncation"}])


def bias_timing(final: str, cost_pips: float = 1.2) -> pd.DataFrame:
    """Is the record a static short/long bias? Splits the final position into its expanding mean (known at t)
    and the remainder, and compares with 'always short at the same size when the arm is active'."""
    D = load_frame()
    sigs = list(SIGNALS) if final == "combo_tstat" else [final.replace("single_", "")]
    pos, _, _ = run_variant(D, sigs, cost_pips, final)
    em = pos.where(pos.index.year >= 2010, 0.0).expanding().mean().shift(1).fillna(0.0)
    rows = []
    for nm, p in (("final", pos), ("timing_only(pos - expanding mean pos)", pos - em), ("bias_only(expanding mean pos)", em),
                  ("always_short_when_active", -pos.abs()), ("always_long_when_active", pos.abs())):
        pnl = pnl_from_positions(p, D["fwd_1d"], D["close"], cost_pips)
        pnl = pnl[pnl.index.year >= 2010]
        t = report(pnl, 252, ARM, 1).set_index("period")
        rows.append({"stream": nm, **{f"SR_{k}": t.loc[k, "sharpe"] for k in ("2010-2026", "2016-2026", "2023-2026")},
                     "t_2010-2026": t.loc["2010-2026", "t"], "long_frac": float((p[p.index.year >= 2010] > 0).mean()),
                     "short_frac": float((p[p.index.year >= 2010] < 0).mean())})
    return pd.DataFrame(rows)


# ================================================================================================ incremental value
def incremental(write: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Three-way vs two-way EW combination (meta.combine / report_combo) and daily-P&L correlations."""
    from eurusd.arms.meta import combine, report_combo, load_arm_daily
    tabs = []
    for name, arms in (("two_way", ["weak_signals", "regime_trend"]), ("three_way", ["weak_signals", "regime_trend", ARM])):
        pnl, w = combine(arms, "EW")
        t = report_combo(pnl, name, len(arms))
        t["weights_last"] = str(w.iloc[-1].round(2).to_dict()) if len(w) else ""
        t["years_arm_in"] = int((w[ARM] > 0).sum()) if ARM in w else 0
        tabs.append(t)
    inc = pd.concat(tabs, ignore_index=True)
    # correlations of daily net P&L with the live streams and with the raw spread-trend / positioning streams
    df = pd.read_parquet(FEATURES)
    mine = load_arm_daily(ARM)
    others = {"weak_signals": load_arm_daily("weak_signals"), "regime_trend(positioning)": load_arm_daily("regime_trend")}
    med = df["rv_21d_bp"].expanding(500).median().shift(1)
    vs = (med / df["rv_21d_bp"]).clip(upper=1.0).fillna(0.0)
    for nm, col in (("raw sign(cot_z52) x vol", "cot_z52"), ("raw sign(d_spread2y_20) x vol", "d_spread2y_20")):
        p = np.sign(df[col]).fillna(0.0) * vs
        s = pnl_from_positions(p, df["fwd_1d"], df["close"], 1.2)["net_bp"]
        key = (s.index - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
        others[nm] = s.groupby(key).sum()
    rows = []
    for nm, s in others.items():
        J = pd.concat([mine.rename("a"), s.rename("b")], axis=1).dropna()
        J = J[J.index.year >= 2010]
        act = J[J.a != 0]
        for lab, a, b in (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026)):
            x = J[(J.index.year >= a) & (J.index.year <= b)]
            xa = act[(act.index.year >= a) & (act.index.year <= b)]
            rows.append({"other": nm, "period": lab, "corr_daily_pnl": x.a.corr(x.b),
                         "corr_when_arm_active": xa.a.corr(xa.b) if len(xa) > 30 else np.nan,
                         "corr_monthly_pnl": x.a.resample("ME").sum().corr(x.b.resample("ME").sum())})
    cor = pd.DataFrame(rows)
    if write:
        inc.to_csv(RES / f"{ARM}_incremental.csv", index=False)
        cor.to_csv(RES / f"{ARM}_correlations.csv", index=False)
    return inc, cor


def release_counts() -> pd.DataFrame:
    R = load_releases()
    R["year"] = R.t.dt.year
    return pd.crosstab(R.year, [R.ccy, R.cat])


if __name__ == "__main__":
    cost = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
    pos, rep = run(cost_pips=cost)
    final = rep.loc[rep["final"], "variant"].iloc[0]
    lc = leak_checks(final, cost_pips=cost)
    lc.to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
    skip = ("signal_label_corr", "circular_shift_null", "surprise_index_truncation")
    for chk in [c for c in lc.check.unique() if c not in skip]:
        r = lc[lc.check == chk].set_index("period")
        print(f"leak check {chk:42s} 2010-26 SR {r.loc['2010-2026','sharpe']:+.2f} t {r.loc['2010-2026','t']:+.2f} | "
              f"2016-26 SR {r.loc['2016-2026','sharpe']:+.2f} | 2023-26 SR {r.loc['2023-2026','sharpe']:+.2f}")
    print(lc[lc.check == "circular_shift_null"][["period", "sharpe", "null_mean", "null_sd", "null_q95", "p_null_ge_actual"]].round(3).to_string(index=False))
    print(lc[lc.check == "surprise_index_truncation"][["period", "max_abs_diff", "nan_mismatch"]].to_string(index=False))
    print(lc[lc.check == "signal_label_corr"][["period", "corr_with_fwd_1d", "n"]].to_string(index=False))
    bt = bias_timing(final, cost)
    bt.to_csv(RES / f"{ARM}_bias_timing.csv", index=False)
    print(bt.round(3).to_string(index=False))
    inc, cor = incremental()
    print(inc[inc.period.isin(["2010-2026", "2016-2026", "2023-2026"])].round(3).to_string(index=False))
    print(cor.round(3).to_string(index=False))
