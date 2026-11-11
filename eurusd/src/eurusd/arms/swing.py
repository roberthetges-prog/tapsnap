"""Arm O ("swing"): EUR/USD directional POSITION trading designed for the multi-week horizon from the start.

Product: a handful of directional decisions a month, held for weeks, each with a probability; act when P >= 0.60.
Everything below (data, priors, models, candidate rules, selection rule) was written into this docstring BEFORE any
result was computed. Nothing is chosen on a test year; 2016-2026 and 2023-2026 are never used for a choice.

DATA (see `load_prices`, `build_features`)
* Price, main sample 1999-01-04 .. today: Fed H.10 noon-NY rate (fred_DEXUSEU, ECB reference rate on US holidays)
  1999-2002, then the feature-store NY-close sessions (HistData) from 2003 with true session high/low.
* Price, robustness sample 1975-1998: synthetic euro = 1.95583 / (DEM per USD). The daily H.10 DEM series is no
  longer served by FRED, so DEM/USD(daily) = DKK/USD(daily, H.10) x DEM/DKK(monthly averages EXGEUS / EXDNUS,
  interpolated): exact in monthly averages, an ERM-band approximation day to day. Clearly labelled, never used
  for training the main sample; it only supplies history to slow inputs (5-year average, PPP mean).
* Lags: daily market series one calendar day (featstore._align_lagged); CFTC report date + 6 days (+1);
  monthly-average interest rates 45 days from the month stamp; CPI 60 days from the month stamp.

PREDICTORS (each ORIENTED so that positive = long EUR/USD under the economic prior stated in `PRED`; priors are the
textbook ones except where marked "house" = the sign rounds 1-2 of this project observed on 2003-2026).
Families: RL rate-differential levels, RC their 3/6-month changes, VAL valuation, TR trend, POS positioning (house,
fragile), POSX positioning extremes (contrarian), EQ equity/risk, CURVE slope differential (Ang-Chen), SEAS, OIL,
CARRY.

TARGETS on a decision close t: y21 = sign of the 21-session return, y42 = sign of the 42-session return,
tb = symmetric triple barrier +-2 x ATR(weekly, 13w) within 42 sessions (no touch -> sign of the 42-session return).

MODELS (fitted on WEEKLY decision rows whose label is known before the test year; expanding window):
* S  scorecard: vote_i = sign(oriented predictor); family score = mean vote of the family's available members;
     score = mean of family scores. No fitted number in the score.
* T  house t-stat combination: z_i = oriented predictor / training std (no demeaning, clip +-2, halved); weight_i =
     max(t_i, 0), t_i = training univariate t-stat against the target; predictors with < 156 weekly rows get 0.
* L  ridge-penalised logistic regression on the same z_i (no intercept), C from {0.003, 0.03, 0.3} by inner
     time-ordered CV log-loss.
  Probability: P(up) = sigmoid(b x score), no intercept (no unconditional drift is assumed for an exchange rate),
  b >= 0 fitted in the training window: on the training scores for S, on INNER walk-forward out-of-sample scores
  (yearly expanding, >= 3 inner training years) for T and L, so that the probabilities are not in-sample flattered.
  conf = max(P, 1-P); side = sign(P - 0.5).

DECISION CLOCKS: M = last session of each calendar month, the position lives to the next month-end decision
(non-overlapping by construction, ~21 sessions); W = last session of each week, the position lives 4 weekly
decisions (~20 sessions); one position at a time; a trade closed on time may be renewed on the same close.

THE 12 CANDIDATE RULES: {S, T, L} x {M, W} x {P >= 0.55, P >= 0.60}, all on the 21-session forecaster, initial stop
3 x weekly ATR (intraday on session high/low, gap fills at the open), time exit as above, no profit target,
1.2 pips per round trip plus overnight carry (EUR overnight rate - Fed target, actual/360).
SELECTION RULE: best lower 95 % Wilson bound of the 2006-2015 directional accuracy at the horizon among candidates
with >= 8 trades a year and positive net expectancy in 2006-2015. Fallback, also fixed in advance: if no candidate
qualifies the frequency floor drops to >= 4 trades a year; if still none, the arm reports failure and the candidate
with the best Wilson bound is flagged final only so that a stream exists.
Sensitivities of the final rule only (reported, never selectable): P >= 0.65 / 0.70, stop 2 x ATR, trailing stop,
symmetric 2-ATR barrier target with the tb forecaster, 42-session forecaster and exit, 0.6 pips, retail swap mark-up,
entry delayed one session.
"""
from __future__ import annotations

import math
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import minimize_scalar

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.wf import walk_forward, pnl_from_positions, report, _agg  # noqa: E402

MACRO = ROOT / "data" / "macro"
CROSS = ROOT / "data" / "processed" / "cross"
PROC = ROOT / "data" / "processed"
RES = ROOT / "experiments" / "results" / "arms"
ARM = "swing"
PIP = 1e-4
DEM_PER_EUR = 1.95583
UTC = "UTC"

TEST_YEARS = list(range(2006, 2027))
PRE_YEARS = list(range(1982, 1999))
ERAS = (("2006-2026", 2006, 2026), ("2006-2015", 2006, 2015), ("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026),
        ("2023-2026", 2023, 2026))
THRESHOLDS = (0.55, 0.60, 0.65, 0.70)
ATR_WEEKS = 13
MIN_ROWS_PRED = 156          # weekly rows a predictor needs in the training window before T / L may use it
C_GRID = (0.003, 0.03, 0.3)
FRED_EXTRA = ("EXGEUS", "EXDNUS", "DEXDNUS", "IR3TIB01DEM156N", "IRLTLT01DEM156N", "IRLTLT01EZM156N",
              "DEUCPIALLMINMEI", "INTDSRDEM193N")

# name: (family, kind, prior, definition, data span)     kind 'cont' = scaled by training std, 'bin' = already in [-1, 1]
PRED = {
    "rd2_lvl":    ("RL", "cont", "+ high relative 2y yield attracts capital (carry / forward-premium puzzle)", "EA AAA 2y - US 2y", "2004-09+"),
    "rd10_lvl":   ("RL", "cont", "+ same at the long end", "EA 10y (German monthly to 2004-09, AAA after) - US 10y", "1975+"),
    "pol_lvl":    ("RL", "cont", "+ same for policy rates", "ECB MRO - Fed target (pre-1999: 3m interbank DE - US)", "1975+"),
    "rrd2_lvl":   ("RL", "cont", "+ real-rate differential (Dornbusch-Frankel)", "2y differential - 12m inflation differential", "2004-09+"),
    "rrd10_lvl":  ("RL", "cont", "+ real-rate differential", "10y differential - 12m inflation differential", "1975+"),
    "rd2_d63":    ("RC", "cont", "+ rising relative yields, slow adjustment of the currency", "3-month change of rd2", "2005-01+"),
    "rd2_d126":   ("RC", "cont", "+ same", "6-month change of rd2", "2005-03+"),
    "rd10_d63":   ("RC", "cont", "+ same", "3-month change of rd10", "1975+"),
    "rd10_d126":  ("RC", "cont", "+ same", "6-month change of rd10", "1975+"),
    "pol_d63":    ("RC", "cont", "+ relative policy tightening", "3-month change of the policy differential", "1975+"),
    "pol_d126":   ("RC", "cont", "+ same", "6-month change of the policy differential", "1975+"),
    "rrd2_d126":  ("RC", "cont", "+ rising real differential", "6-month change of rrd2", "2005-03+"),
    "rrd10_d126": ("RC", "cont", "+ rising real differential", "6-month change of rrd10", "1976+"),
    "ppp_dev":    ("VAL", "cont", "- CPI real exchange rate reverts to its mean (half-life 3-5y => ~1.5 %/month of the gap)", "-(log real rate - expanding mean since 1975)", "1980+"),
    "ma5y_dev":   ("VAL", "cont", "- reversion to the 5-year average", "-(log spot - log 1260-session mean)", "1980+"),
    "mom63":      ("TR", "cont", "+ time-series momentum (Moskowitz-Ooi-Pedersen)", "63-session log return", "1975+"),
    "mom126":     ("TR", "cont", "+ same", "126-session log return", "1975+"),
    "mom252":     ("TR", "cont", "+ same (textbook; rounds 1-2 saw the opposite sign at the daily horizon)", "252-session log return", "1976+"),
    "sma50_200":  ("TR", "bin", "+ trend state", "sign(SMA50 - SMA200)", "1975+"),
    "wma10_40":   ("TR", "bin", "+ trend state", "sign(10-week - 40-week average of weekly closes)", "1975+"),
    "brk126":     ("TR", "bin", "+ breakout of the 6-month range", "+1 after a 126-session closing high, -1 after a low (state)", "1975+"),
    "cot_z52":    ("POS", "cont", "+ follow speculators (HOUSE finding; EUR-specific, fragile)", "non-commercial net/OI, 52-week z", "2000+"),
    "cot_z156":   ("POS", "cont", "+ same on a 3-year window (HOUSE)", "156-week z", "2002+"),
    "cot_ext":    ("POSX", "bin", "- crowded positioning reverses (textbook contrarian)", "-sign(z156) when |z156| > 1.5", "2002+"),
    "eqrel63":    ("EQ", "cont", "+ euro-area equity outperformance draws flows (HOUSE sign F04)", "63-session return DAX - S&P 500 (local)", "2003-04+"),
    "vix_lvl":    ("EQ", "cont", "- high VIX = risk-off, dollar bid (textbook; expected weak)", "-(VIX - its 252-session median)", "1991+"),
    "slope2_diff":  ("CURVE", "cont", "- the steeper relative curve underperforms (Ang-Chen 2010)", "-((EA10-EA2) - (US10-US2))", "2004-09+"),
    "slope3m_diff": ("CURVE", "cont", "- same with the 3-month rate", "-((EA10-EA3m) - (US10-US3m))", "1975+"),
    "seas":       ("SEAS", "bin", "+ December long / May short (HOUSE C03, no economic story)", "share of the horizon in December - share in May", "all"),
    "seas_month": ("SEAS", "bin", "none: sign learned on the expanding training history (|t| >= 1)", "month-of-year mean of the target, prior years only", "5y after start"),
    "oil_d63":    ("OIL", "cont", "- dearer oil worsens euro-area terms of trade", "-(63-session log change of Brent)", "1987-09+"),
    "oil_d126":   ("OIL", "cont", "- same", "-(126-session log change of Brent)", "1987-12+"),
    "carry":      ("CARRY", "cont", "+ short-rate carry (expected weak)", "EUR overnight - Fed target (pre-1999: 3m interbank)", "1975+"),
}
FAMILIES = ("RL", "RC", "VAL", "TR", "POS", "POSX", "EQ", "CURVE", "SEAS", "OIL", "CARRY")
TARGETS = {"h21": dict(fwd="fwd21", h=21, seas="seas21", end="end21"),
           "h42": dict(fwd="fwd42", h=42, seas="seas42", end="end42"),
           "tb": dict(fwd="tb", h=42, seas="seas42", end="end42")}


# ============================================================================= data
def fetch(verbose: bool = True) -> None:
    """FRED series added by this arm (FRED answers curl through the session proxy)."""
    import io
    for s in FRED_EXTRA:
        p = MACRO / f"fred_{s}.csv"
        if p.exists():
            continue
        txt = subprocess.run(["curl", "-sS", "-f", "-m", "120", f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={s}"],
                             capture_output=True, text=True, check=True).stdout
        d = pd.read_csv(io.StringIO(txt))
        d.columns = ["date", "value"]
        d["value"] = pd.to_numeric(d["value"], errors="coerce")
        d.dropna().to_csv(p, index=False)
        if verbose:
            print("fetched", s, len(d), flush=True)


def _ms(name: str, col: str = "value") -> pd.Series:
    d = pd.read_csv(MACRO / name)
    dcol = d.columns[0]
    d[dcol] = pd.to_datetime(d[dcol])
    s = pd.to_numeric(d.set_index(dcol)[col], errors="coerce").astype(float)
    return s[~s.index.duplicated()].sort_index().dropna()


def _align_lagged(s: pd.Series, idx: pd.DatetimeIndex, lag_days: int = 1) -> pd.Series:
    """Identical to featstore._align_lagged: last observation stamped <= date - lag_days."""
    target = pd.DatetimeIndex(idx) - pd.Timedelta(days=lag_days)
    return pd.Series(s.reindex(s.index.union(target)).sort_index().ffill().reindex(target).values, index=idx)


def synthetic_dem_eur() -> pd.Series:
    """Synthetic euro before 1999: 1.95583 / DEM-per-USD, DEM daily = DKK daily x interpolated monthly DEM/DKK."""
    dem_m, dkk_m, dkk_d = _ms("fred_EXGEUS.csv"), _ms("fred_EXDNUS.csv"), _ms("fred_DEXDNUS.csv")
    ratio = (dem_m / dkk_m).dropna()
    ratio.index = ratio.index + pd.Timedelta(days=14)
    r = ratio.reindex(ratio.index.union(dkk_d.index)).sort_index().interpolate("time").reindex(dkk_d.index).ffill().bfill()
    return (DEM_PER_EUR / (dkk_d * r)).loc["1975-01-01":"1998-12-31"]


def load_prices() -> pd.DataFrame:
    """Continuous daily frame 1975 .. today. Index = session start (UTC, as the feature store), `cdate` = closing
    date, `src` in {synth_dem, h10, histdata}. open/high/low are true only for histdata (else = close)."""
    from eurusd.data import load_ohlc
    from eurusd import features as F
    feat = pd.read_parquet(PROC / "features_daily.parquet", columns=["close", "close_time", "fwd_1d"])
    h1 = load_ohlc("H1").loc["2003":]
    h1 = h1[~h1.index.duplicated(keep="last")]
    d = F.daily_ohlc(h1, 22).reindex(feat.index)
    assert np.allclose(d["close"].values, feat["close"].values, equal_nan=True), "session closes differ from the feature store"
    hd = pd.DataFrame({"open": d.open, "high": d.high, "low": d.low, "close": d.close, "src": "histdata"}, index=feat.index)
    hd["cdate"] = pd.DatetimeIndex(feat["close_time"]).tz_convert(UTC).normalize().tz_localize(None)
    h10 = _ms("fred_DEXUSEU.csv")
    ecb = pd.read_csv(PROC / "ecb_EURUSD_D1.csv", parse_dates=["date"]).set_index("date")["usd_per_eur"].astype(float)
    p99 = h10.combine_first(ecb).loc["1999-01-04":"2002-12-31"]
    p99 = p99[p99.index.dayofweek < 5].dropna()
    syn = synthetic_dem_eur()
    frames = []
    for s, src in ((syn, "synth_dem"), (p99, "h10")):
        idx = pd.DatetimeIndex(s.index).tz_localize(UTC) - pd.Timedelta(hours=2)
        frames.append(pd.DataFrame({"open": s.values, "high": s.values, "low": s.values, "close": s.values, "src": src,
                                    "cdate": s.index.values}, index=idx))
    P = pd.concat(frames + [hd])
    P.index = pd.DatetimeIndex(P.index).as_unit("us")
    P.index.name = "time"
    P["cdate"] = pd.to_datetime(P["cdate"])
    assert P.index.is_monotonic_increasing and not P.index.has_duplicates
    ct = pd.Series(pd.DatetimeIndex(P["cdate"]).tz_localize(UTC) + pd.Timedelta(hours=22), index=P.index)
    ct.loc[feat.index] = pd.DatetimeIndex(feat["close_time"]).tz_convert(UTC)
    P["close_time"] = pd.DatetimeIndex(ct).as_unit("us")
    return P


def weekly_atr(P: pd.DataFrame, weeks: int = ATR_WEEKS) -> pd.Series:
    """Mean true range of the last `weeks` weekly bars, as known at each session close (the running week counts only
    on its last session). Close-only history is scaled by the 2003-2005 ratio of true to close-only weekly range."""
    wk = pd.DatetimeIndex(P["cdate"]).to_period("W-FRI")
    g = P.groupby(wk)
    W = pd.DataFrame({"h": g["high"].max(), "l": g["low"].min(), "c": g["close"].last(),
                      "hc": g["close"].max(), "lc": g["close"].min(), "src": g["src"].last()})
    pc = W["c"].shift(1)
    tr = np.maximum(W["h"], pc) - np.minimum(W["l"], pc)
    trc = np.maximum(W["hc"], pc) - np.minimum(W["lc"], pc)
    cal = (W.index.year >= 2003) & (W.index.year <= 2005)
    factor = float(tr[cal].mean() / trc[cal].mean())
    tr = tr.where(W["src"] == "histdata", trc * factor)
    atr = tr.rolling(weeks).mean()
    last_of_week = ~pd.Series(wk, index=P.index).duplicated(keep="last")
    cur = pd.Series(atr.reindex(wk).values, index=P.index)
    prev = pd.Series(atr.shift(1).reindex(wk).values, index=P.index)
    out = cur.where(last_of_week, prev)
    out.attrs["close_only_factor"] = factor
    return out


def build_features(P: pd.DataFrame) -> pd.DataFrame:
    """All ORIENTED predictors (positive = long EUR/USD under the prior) on the daily frame, plus labels and the
    accounting columns the trade simulator needs. Every input is lagged as stated in the module docstring."""
    warnings.filterwarnings("ignore", category=RuntimeWarning)
    cd = pd.DatetimeIndex(P["cdate"])
    A = lambda s, lag=1: pd.Series(_align_lagged(s, cd, lag).values, index=P.index)  # noqa: E731
    c = P["close"]
    lc = np.log(c)
    X = pd.DataFrame(index=P.index)
    euro = pd.Series(cd >= pd.Timestamp("1999-01-04"), index=P.index)
    # ---- rates
    us2, us10 = A(_ms("fred_DGS2.csv")), A(_ms("fred_DGS10.csv"))
    aaa = pd.read_csv(MACRO / "ea_aaa_yield_curve.csv", parse_dates=["date"]).set_index("date")
    de10, de3m, us3m_ib = A(_ms("fred_IRLTLT01DEM156N.csv"), 45), A(_ms("fred_IR3TIB01DEM156N.csv"), 45), A(_ms("fred_IR3TIB01USM156N.csv"), 45)
    ea2 = A(aaa["aaa_spot_2y"])
    aaa10, aaa3m = A(aaa["aaa_spot_10y"]), A(aaa["aaa_spot_3m"])
    has_aaa = aaa10.notna()
    ea10 = aaa10.where(has_aaa, de10)
    ea3m = aaa3m.where(has_aaa, de3m)
    us_slope3m = A(_ms("fred_T10Y3M.csv")).where(has_aaa, us10 - us3m_ib)
    pol = pd.read_csv(MACRO / "ecb_policy_rates.csv", parse_dates=["date"]).set_index("date")
    fed_mid = (_ms("fred_DFEDTARL.csv") + _ms("fred_DFEDTARU.csv")) / 2
    fed = pd.concat([_ms("fred_DFEDTAR.csv"), fed_mid.dropna()]).sort_index()
    fed = fed[~fed.index.duplicated(keep="last")]
    on = pd.read_csv(MACRO / "ea_overnight_rates.csv", parse_dates=["date"]).set_index("date")
    ea_on = on["estr"].where(on["estr"].notna(), on["eonia"]).dropna()
    ib_diff = de3m - us3m_ib
    rd2, rd10 = ea2 - us2, ea10 - us10
    pol_diff = (A(pol["main_refinancing_rate"].astype(float)) - A(fed)).where(euro, ib_diff)
    carry = (A(ea_on) - A(fed)).where(euro, ib_diff)
    us_cpi = _ms("fred_CPIAUCSL.csv")
    hicp = pd.read_csv(MACRO / "ea_hicp.csv")
    ea_cpi = pd.Series(hicp["hicp_index"].values, index=pd.to_datetime(hicp["month"] + "-01")).dropna()
    fr = _ms("fred_CP0000EZ19M086NEST.csv")
    ov = ea_cpi.index.intersection(fr.index)[-12:]
    fr = fr * float((ea_cpi[ov] / fr[ov]).mean())
    ea_cpi = pd.concat([ea_cpi, fr[fr.index > ea_cpi.index.max()]])
    de_cpi = _ms("fred_DEUCPIALLMINMEI.csv")
    ov = ea_cpi.index[:12]
    de_cpi = de_cpi * float((ea_cpi[ov] / de_cpi[ov]).mean())
    ea_cpi = pd.concat([de_cpi[de_cpi.index < ea_cpi.index.min()], ea_cpi])
    pi_us, pi_ea = A(np.log(us_cpi).diff(12) * 100, 60), A(np.log(ea_cpi).diff(12) * 100, 60)
    dpi = pi_ea - pi_us
    rrd2, rrd10 = rd2 - dpi, rd10 - dpi
    X["rd2_lvl"], X["rd10_lvl"], X["pol_lvl"], X["rrd2_lvl"], X["rrd10_lvl"] = rd2, rd10, pol_diff, rrd2, rrd10
    for nm, s in (("rd2", rd2), ("rd10", rd10), ("pol", pol_diff)):
        X[f"{nm}_d63"], X[f"{nm}_d126"] = s.diff(63), s.diff(126)
    X["rrd2_d126"], X["rrd10_d126"] = rrd2.diff(126), rrd10.diff(126)
    n99 = int(np.argmax(euro.values)) if euro.any() else len(X)
    for col in ("pol_d63", "pol_d126"):       # the policy-rate definition changes on 1999-01-04: no change across it
        k = 63 if col.endswith("63") else 126
        X.iloc[n99:n99 + k, X.columns.get_loc(col)] = np.nan
    # ---- valuation
    q = lc + A(np.log(ea_cpi), 60) - A(np.log(us_cpi), 60)
    X["ppp_dev"] = -(q - q.expanding(min_periods=1260).mean())
    X["ma5y_dev"] = -(lc - np.log(c.rolling(1260).mean()))
    # ---- trend
    for k in (63, 126, 252):
        X[f"mom{k}"] = lc - lc.shift(k)
    X["sma50_200"] = np.sign(c.rolling(50).mean() - c.rolling(200).mean())
    w10 = sum(c.shift(5 * i) for i in range(10)) / 10
    w40 = sum(c.shift(5 * i) for i in range(40)) / 40
    X["wma10_40"] = np.sign(w10 - w40)
    hi, lo = c.shift(1).rolling(126).max(), c.shift(1).rolling(126).min()
    X["brk126"] = pd.Series(np.where(c >= hi, 1.0, np.where(c <= lo, -1.0, np.nan)), index=P.index).ffill().where(hi.notna())
    # ---- positioning (report Tuesday, published Friday: usable from report date + 6 days, then the 1-day lag)
    leg = pd.read_csv(MACRO / "cot_eurofx_legacy.csv", parse_dates=["report_date"]).set_index("report_date")
    net = (leg.noncomm_long - leg.noncomm_short) / leg.open_interest
    net.index = net.index + pd.Timedelta(days=6)
    X["cot_z52"] = A((net - net.rolling(52).mean()) / net.rolling(52).std())
    z156 = A((net - net.rolling(156).mean()) / net.rolling(156).std())
    X["cot_z156"] = z156
    X["cot_ext"] = (-np.sign(z156)).where(z156.abs() > 1.5, 0.0).where(z156.notna())
    # ---- equity / risk
    def cross(name):
        s = pd.read_parquet(CROSS / f"{name}_D1.parquet")["close"]
        s.index = s.index.tz_convert(UTC).normalize().tz_localize(None)
        return np.log(A(s[~s.index.duplicated(keep="last")].sort_index()))
    dax, spx = cross("gdaxi"), cross("spx")
    X["eqrel63"] = (dax - dax.shift(63)) - (spx - spx.shift(63))
    vix = A(_ms("fred_VIXCLS.csv"))
    X["vix_lvl"] = -(vix - vix.rolling(252).median())
    # ---- curve
    X["slope2_diff"] = -((ea10 - ea2) - (us10 - us2))
    X["slope3m_diff"] = -((ea10 - ea3m) - us_slope3m)
    # ---- seasonality (calendar only)
    for h, days in ((21, 30), (42, 60)):
        f = np.zeros(len(cd))
        for k in range(1, days + 1):
            m = (cd + pd.Timedelta(days=k)).month
            f += (m == 12).astype(float) - (m == 5).astype(float)
        X[f"seas{h}"] = f / days
    X["fwd_month21"] = (cd + pd.Timedelta(days=15)).month
    X["fwd_month42"] = (cd + pd.Timedelta(days=30)).month
    # ---- oil, carry
    brent = np.log(A(_ms("datahub_brent_daily.csv", "price")))
    X["oil_d63"], X["oil_d126"] = -(brent - brent.shift(63)), -(brent - brent.shift(126))
    X["carry"] = carry
    # ---- accounting: carry accrual (% p.a., contemporaneous), weekly ATR, labels
    A0 = lambda s: pd.Series(_align_lagged(s, cd, 0).values, index=P.index)  # noqa: E731
    acc_euro = A0(ea_on) - A0(fed)
    acc_pre = A0(_ms("fred_IR3TIB01DEM156N.csv")) - A0(_ms("fred_IR3TIB01USM156N.csv"))
    X["acc_pct"] = acc_euro.where(euro, acc_pre)
    X["atr_w"] = weekly_atr(P)
    X["fwd_1d"] = (lc.shift(-1) - lc) * 1e4
    X["fwd21"] = (lc.shift(-21) - lc) * 1e4
    X["fwd42"] = (lc.shift(-42) - lc) * 1e4
    ct = pd.Series(pd.DatetimeIndex(P["close_time"]), index=P.index)
    X["end21"], X["end42"] = ct.shift(-21), ct.shift(-42)
    X["tb"] = triple_barrier(P, X["atr_w"], 2.0, 42)
    wk = pd.Series(cd.to_period("W-FRI"), index=P.index)
    mo = pd.Series(cd.to_period("M"), index=P.index)
    X["is_w"] = ~wk.duplicated(keep="last")
    X["is_m"] = ~mo.duplicated(keep="last")
    if (cd[-1] + pd.offsets.BDay(1)).month == cd[-1].month:      # the running month / week is not a decision yet
        X.iloc[-1, X.columns.get_loc("is_m")] = False
    if cd[-1].dayofweek < 4:
        X.iloc[-1, X.columns.get_loc("is_w")] = False
    return X.replace([np.inf, -np.inf], np.nan)


def triple_barrier(P: pd.DataFrame, atr_w: pd.Series, k: float, horizon: int) -> pd.Series:
    """+1 / -1 for the first touch of close +- k x ATR_w within `horizon` sessions (both the same session -> the sign
    of that session's close versus the entry), otherwise the sign of the horizon return. NaN near the end."""
    c, h, l, a = P["close"].values, P["high"].values, P["low"].values, atr_w.values
    n = len(c)
    out = np.full(n, np.nan)
    for i in range(n - horizon):
        if not np.isfinite(a[i]):
            continue
        up, dn = c[i] + k * a[i], c[i] - k * a[i]
        hh, ll = h[i + 1:i + horizon + 1], l[i + 1:i + horizon + 1]
        tu, td = np.argmax(hh >= up) if (hh >= up).any() else horizon + 1, np.argmax(ll <= dn) if (ll <= dn).any() else horizon + 1
        if tu < td:
            out[i] = 1.0
        elif td < tu:
            out[i] = -1.0
        elif tu <= horizon:
            out[i] = np.sign(c[i + 1 + tu] - c[i])
        else:
            out[i] = np.sign(c[i + horizon] - c[i])
    return pd.Series(out, index=P.index)


def add_seas_month(X: pd.DataFrame) -> pd.DataFrame:
    """Month-of-year effect with the sign learned on PRIOR calendar years only: for a row of year Y, the t-stat of
    the per-year average target return of its calendar month over all weekly rows whose label was known before
    Y-01-01 (>= 5 years); scaled to [-1, 1], zero when |t| < 1. Leak-free under the yearly protocol."""
    W = X[X["is_w"]]
    for tgt, fcol, mcol, ecol in (("21", "fwd21", "fwd_month21", "end21"), ("42", "fwd42", "fwd_month42", "end42")):
        out = pd.Series(np.nan, index=X.index)
        yrs = sorted(set(X.index.year))
        for Y in yrs:
            start = pd.Timestamp(f"{Y}-01-01", tz=UTC)
            hist = W[(W[ecol] < start) & W[fcol].notna()]
            if hist.empty or hist.index.year.nunique() < 5:
                continue
            ym = hist.groupby([hist[mcol].values, hist.index.year])[fcol].mean()
            t = {}
            for m in range(1, 13):
                v = ym.loc[m] if m in ym.index.get_level_values(0) else pd.Series(dtype=float)
                t[m] = float(v.mean() / (v.std() / math.sqrt(len(v)))) if len(v) >= 5 and v.std() > 0 else 0.0
            rows = X.index[X.index.year == Y]
            tv = X.loc[rows, mcol].map(t).astype(float)
            out.loc[rows] = (tv.clip(-3, 3) / 3).where(tv.abs() >= 1, 0.0)
        X[f"seas_month{tgt}"] = out
    return X


# ============================================================================= models
def pred_cols(target: str) -> dict:
    """predictor name -> column in the feature frame for this target."""
    h = "21" if target == "h21" else "42"
    m = {p: p for p in PRED}
    m["seas"] = f"seas{h}"
    m["seas_month"] = f"seas_month{h}"
    return m


def votes(X: pd.DataFrame, target: str, drop: tuple = ()) -> pd.DataFrame:
    cols = pred_cols(target)
    return pd.DataFrame({p: np.sign(X[cols[p]]) for p in PRED if p not in drop}, index=X.index)


def scorecard(V: pd.DataFrame) -> pd.Series:
    fam = {}
    for f in FAMILIES:
        members = [p for p in V.columns if PRED[p][0] == f]
        if members:
            fam[f] = V[members].mean(axis=1, skipna=True)
    return pd.DataFrame(fam).mean(axis=1, skipna=True).fillna(0.0)


def _platt(score: np.ndarray, y: np.ndarray) -> float:
    """b >= 0 maximising the likelihood of P(y = +1) = sigmoid(b * score); y in {-1, +1}."""
    ok = np.isfinite(score) & np.isfinite(y) & (y != 0)
    s, yy = score[ok], y[ok]
    if len(s) < 30 or s.std() == 0:
        return 0.0
    nll = lambda b: float(np.logaddexp(0.0, -b * s * yy).sum())  # noqa: E731
    r = minimize_scalar(nll, bounds=(0.0, 20.0 / s.std()), method="bounded")
    return float(r.x) if nll(r.x) < nll(0.0) - 1e-9 else 0.0


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def _zfit(tr: pd.DataFrame, cols: dict, preds: list) -> dict:
    st = {}
    for p in preds:
        x = tr[cols[p]].dropna()
        if len(x) < MIN_ROWS_PRED:
            continue
        st[p] = 1.0 if PRED[p][1] == "bin" else (float(x.std()) or 1.0)
    return st


def _zapply(df: pd.DataFrame, cols: dict, st: dict) -> pd.DataFrame:
    out = {}
    for p, sd in st.items():
        x = df[cols[p]]
        out[p] = (x if PRED[p][1] == "bin" else (x / sd).clip(-2, 2) / 2).fillna(0.0)
    return pd.DataFrame(out, index=df.index)


def make_model(kind: str, target: str, drop: tuple = ()):
    """Returns (fit, predict) for eurusd.wf.walk_forward. predict gives P(up) for every decision row of the test year."""
    T = TARGETS[target]
    cols = pred_cols(target)
    preds = [p for p in PRED if p not in drop]
    fwd, end = T["fwd"], T["end"]

    def ysign(df):
        return np.sign(df[fwd].values.astype(float))

    def core_fit(tr, C=None):
        st = _zfit(tr, cols, preds)
        Z = _zapply(tr, cols, st)
        y = tr[fwd].values.astype(float)
        ok = np.isfinite(y)
        if kind == "T":
            w = {}
            for p in Z.columns:
                x = Z[p].values[ok & tr[cols[p]].notna().values]
                yy = y[ok & tr[cols[p]].notna().values]
                if len(x) < MIN_ROWS_PRED or x.std() == 0:
                    w[p] = 0.0
                    continue
                r = np.corrcoef(x, yy)[0, 1]
                w[p] = max(r * math.sqrt(len(x) - 2) / math.sqrt(max(1e-12, 1 - r * r)), 0.0)
            tot = sum(w.values())
            w = {p: (v / tot if tot > 0 else 1.0 / max(len(w), 1)) for p, v in w.items()}
            return {"st": st, "w": w}
        from sklearn.linear_model import LogisticRegression
        ys = np.sign(y)
        m = ok & (ys != 0)
        if not len(Z.columns) or m.sum() < 50:
            return {"st": st, "lr": None}
        lr = LogisticRegression(C=C, fit_intercept=False, max_iter=500)
        lr.fit(Z.values[m], (ys[m] > 0).astype(int))
        return {"st": st, "lr": lr, "cols": list(Z.columns)}

    def core_score(m, df):
        Z = _zapply(df, cols, m["st"])
        if kind == "T":
            return sum(m["w"][p] * Z[p].values for p in Z.columns) if len(Z.columns) else np.zeros(len(df))
        if m["lr"] is None:
            return np.zeros(len(df))
        return m["lr"].decision_function(Z[m["cols"]].values)

    def inner_oos(tr, C=None):
        yrs = sorted(set(tr.index.year))
        out = pd.Series(np.nan, index=tr.index)
        for y in yrs:
            if y - yrs[0] < 3:
                continue
            st_ = pd.Timestamp(f"{y}-01-01", tz=UTC)
            itr, ite = tr[tr[end] < st_], tr[tr.index.year == y]
            if len(itr) < 100 or ite.empty:
                continue
            out.loc[ite.index] = core_score(core_fit(itr, C), ite)
        return out

    def fit(train):
        tr = train[train["is_w"] & train[fwd].notna()]
        if kind == "S":
            s = scorecard(votes(tr, target, drop)).values
            return {"b": _platt(s, ysign(tr))}
        y = ysign(tr)
        if kind == "T":
            oos = inner_oos(tr).values
            b = _platt(oos, y) if np.isfinite(oos).sum() >= 100 else 0.5 * _platt(core_score(core_fit(tr), tr), y)
            return {"b": b, "m": core_fit(tr)}
        best = None
        for C in C_GRID:
            oos = inner_oos(tr, C).values
            if np.isfinite(oos).sum() < 100:
                continue
            b = _platt(oos, y)
            ok = np.isfinite(oos) & (y != 0)
            ll = float(np.logaddexp(0.0, -b * oos[ok] * y[ok]).mean())
            if best is None or ll < best[0]:
                best = (ll, C, b)
        if best is None:
            C = C_GRID[1]
            m = core_fit(tr, C)
            return {"b": 0.5 * _platt(core_score(m, tr), y), "m": m, "C": C}
        return {"b": best[2], "m": core_fit(tr, best[1]), "C": best[1]}

    def predict(model, test):
        if kind == "S":
            s = scorecard(votes(test, target, drop)).values
        else:
            s = core_score(model["m"], test)
        return pd.Series(_sigmoid(model["b"] * np.asarray(s, dtype=float)), index=test.index)

    return fit, predict


def forecast(X: pd.DataFrame, kind: str, target: str, years, drop: tuple = ()) -> pd.Series:
    """Out-of-sample P(up) on every decision row (weekly and month-end) of the test years, via the fixed harness."""
    dec = X[X["is_w"] | X["is_m"]]
    fit, predict = make_model(kind, target, drop)
    return walk_forward(dec, fit, predict, label_end=dec[TARGETS[target]["end"]], years=years, min_train_years=5, verbose=False)


# ============================================================================= evaluation helpers
def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (np.nan, np.nan)
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (mid - half, mid + half)


def block_ci(hit: np.ndarray, block: int, n_boot: int = 2000, seed: int = 7) -> tuple[float, float]:
    """Circular block bootstrap of a hit series in time order (NaN = not acted)."""
    n = len(hit)
    if n == 0 or np.isfinite(hit).sum() < 5:
        return (np.nan, np.nan)
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(n / block))
    out = np.empty(n_boot)
    for b in range(n_boot):
        st = rng.integers(0, n, nb)
        idx = (st[:, None] + np.arange(block)[None, :]).ravel()[:n] % n
        out[b] = np.nanmean(hit[idx]) if np.isfinite(hit[idx]).any() else np.nan
    return (float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5)))


def n_independent(locs: np.ndarray, h: int) -> int:
    """Greedy count of acted decisions whose h-session windows do not overlap."""
    cnt, nxt = 0, -1
    for x in np.sort(locs):
        if x >= nxt:
            cnt += 1
            nxt = x + h
    return cnt


def accuracy_rows(X: pd.DataFrame, P_up: pd.Series, target: str, clock: str, label: str, eras=ERAS) -> list[dict]:
    """Directional accuracy of a forecaster by era and probability threshold. Clock W: weekly rows, overlapping
    horizon -> block-bootstrap interval and the number of non-overlapping bets. Clock M: month-end rows scored on
    the return to the next (h21) or second-next (h42, every other month) month-end -> Wilson interval."""
    T = TARGETS[target]
    loc = pd.Series(np.arange(len(X)), index=X.index)
    rows = []
    if clock == "W":
        d = X[X["is_w"]]
        y = np.sign(d[T["fwd"]].astype(float))
    else:
        d = X[X["is_m"]]
        step = 1 if T["h"] == 21 else 2
        lc = np.log(X["__close"].reindex(d.index))
        y = np.sign(lc.shift(-step) - lc)
        if target == "tb":
            y = np.sign(d["tb"].astype(float))
        if step == 2:
            d, y = d.iloc[::2], y.iloc[::2]
    p = P_up.reindex(d.index)
    ok = p.notna() & y.notna() & (y != 0)
    d, y, p = d[ok], y[ok], p[ok]
    conf = np.maximum(p, 1 - p)
    side = np.where(p >= 0.5, 1.0, -1.0)
    hit = (side == y.values).astype(float)
    for era, a, b in eras:
        m = (d.index.year >= a) & (d.index.year <= b)
        if m.sum() == 0:
            continue
        up = float((y[m] > 0).mean())
        brier = float(((p[m] - (y[m] > 0)) ** 2).mean())
        for thr in (0.5,) + THRESHOLDS:
            act = m & (conf.values >= thr) & ((conf.values > 0.5) | (thr > 0.5))
            n = int(act.sum())
            k = int(hit[act].sum())
            r = {"forecaster": label, "target": target, "clock": clock, "era": era, "thr": thr, "n_decisions": int(m.sum()),
                 "n_acted": n, "acc": k / n if n else np.nan, "naive_majority": max(up, 1 - up), "brier": brier, "brier_naive": 0.25,
                 "acted_per_year": n / (b - a + 1)}
            if clock == "W":
                hh = np.where(act[m], hit[m], np.nan)
                r["ci_lo"], r["ci_hi"] = block_ci(hh, block=int(math.ceil(2 * T["h"] / 5)))
                r["n_independent"] = n_independent(loc.reindex(d.index[act]).values, T["h"])
            else:
                r["ci_lo"], r["ci_hi"] = wilson(k, n)
                r["n_independent"] = n
            rows.append(r)
    return rows


# ============================================================================= the trade
def simulate(X: pd.DataFrame, P_up: pd.Series, clock: str, thr: float, k: float = 3.0, steps: int | None = None,
             target_k: float | None = None, trail: bool = False, cost_pips: float = 1.2, markup_pct: float = 0.0,
             delay: int = 0, use_carry: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Runs the position trader on one decision clock. Returns (trades, daily stream).
    Entry at the decision close when flat and conf >= thr; initial stop k x ATR_w (intraday on high/low, gap -> open);
    optional target target_k x ATR_w and trailing stop (k x ATR_w under the best close); time exit `steps` decisions
    later at that close; carry accrues actual/360 on (EUR overnight - Fed target) for every night held."""
    steps = steps or (1 if clock == "M" else 4)
    c, o, h, l = (X[f"__{f}"].values for f in ("close", "open", "high", "low"))
    atr, acc = X["atr_w"].values, np.nan_to_num(X["acc_pct"].values)
    cd = pd.DatetimeIndex(X["__cdate"])
    days = np.r_[np.diff(cd.values).astype("timedelta64[D]").astype(float), 1.0]
    ct = pd.DatetimeIndex(X["__close_time"])
    n = len(c)
    dmask = (X["is_m"] if clock == "M" else X["is_w"]).values
    dec = np.flatnonzero(dmask)
    p_all = P_up.reindex(X.index).values
    pos, adj, carry_bp = np.zeros(n), np.zeros(n), np.zeros(n)
    trades = []
    free = -1
    for j, e in enumerate(dec):
        p = p_all[e]
        if e < free or not np.isfinite(p) or j + steps >= len(dec):
            continue
        conf = max(p, 1 - p)
        if conf < thr or conf <= 0.5 or not np.isfinite(atr[e]):
            continue
        side = 1.0 if p > 0.5 else -1.0
        e0, xp = e + delay, dec[j + steps]
        entry, risk = c[e0], k * atr[e]
        stop = entry - side * risk
        tgt = entry + side * target_k * atr[e] if target_k else np.nan
        best, x, exit_px, reason, carry_pips = entry, xp, c[xp], "time", 0.0
        for t in range(e0 + 1, xp + 1):
            night = (side * acc[t - 1] - markup_pct) / 100.0 * days[t - 1] / 360.0
            carry_pips += night * c[t - 1] / PIP if use_carry else 0.0
            carry_bp[t - 1] += night * 1e4 if use_carry else 0.0
            if side > 0:
                if l[t] <= stop:
                    x, exit_px, reason = t, min(o[t], stop), ("trail" if trail and stop > entry - risk + 1e-12 else "stop")
                    break
                if target_k and h[t] >= tgt:
                    x, exit_px, reason = t, max(o[t], tgt), "target"
                    break
                if trail:
                    best = max(best, c[t]); stop = max(stop, best - risk)
            else:
                if h[t] >= stop:
                    x, exit_px, reason = t, max(o[t], stop), ("trail" if trail and stop < entry + risk - 1e-12 else "stop")
                    break
                if target_k and l[t] <= tgt:
                    x, exit_px, reason = t, min(o[t], tgt), "target"
                    break
                if trail:
                    best = min(best, c[t]); stop = min(stop, best + risk)
        pos[e0:x] = side
        if reason != "time":
            adj[x - 1] += side * (math.log(exit_px) - math.log(c[x])) * 1e4
        gross = side * (exit_px - entry) / PIP
        net = gross - cost_pips + carry_pips
        trades.append({"entry_time": ct[e0], "exit_time": ct[x], "side": int(side), "prob": conf, "entry_px": entry, "exit_px": exit_px,
                       "stop": entry - side * risk, "target": tgt, "exit_reason": reason, "atr_w_pips": atr[e] / PIP,
                       "gross_pips": gross, "carry_pips": carry_pips, "cost_pips": cost_pips, "pips": net, "R": net / (risk / PIP),
                       "holding_sessions": int(x - e0), "holding_days": int((cd[x] - cd[e0]).days),
                       "dir_correct": bool(side * (c[xp] - entry) > 0), "horizon_pips": side * (c[xp] - entry) / PIP,
                       "entry_loc": int(e0)})
        free = x
    tr = pd.DataFrame(trades)
    pos_s = pd.Series(pos, index=X.index)
    pnl = pnl_from_positions(pos_s, X["fwd_1d"].fillna(0.0), X["__close"], cost_pips=cost_pips)
    stream = pd.DataFrame({"pos": pos_s, "fwd_bp": X["fwd_1d"], "gross_bp": pnl["gross_bp"] + adj, "carry_bp": carry_bp,
                           "net_bp": pnl["net_bp"] + adj + carry_bp, "turnover": pnl["turnover"]}, index=X.index)
    return tr, stream


def trade_stats(tr: pd.DataFrame, stream: pd.DataFrame, a: int, b: int) -> dict:
    """Trade statistics for trades ENTERED in [a, b] and the monthly net P&L Sharpe of the stream over the same years."""
    yrs = b - a + 1
    s = stream[(stream.index.year >= a) & (stream.index.year <= b)]
    if len(s):
        yrs = max((s.index[-1] - s.index[0]).days / 365.25, 0.5)
    out = {"n_trades": 0, "trades_per_year": 0.0}
    if len(tr):
        ey = pd.DatetimeIndex(tr["entry_time"]).year
        t = tr[(ey >= a) & (ey <= b)]
    else:
        t = tr
    if len(t):
        win, los = t[t.pips > 0], t[t.pips <= 0]
        k = int(t.dir_correct.sum())
        lo, hi = wilson(k, len(t))
        cumR = t["R"].cumsum().values
        dd = float((np.maximum.accumulate(np.r_[0.0, cumR]) - np.r_[0.0, cumR]).max())
        out = {"n_trades": len(t), "trades_per_year": len(t) / yrs, "share_long": float((t.side > 0).mean()),
               "win_share": float((t.pips > 0).mean()), "dir_acc": k / len(t), "dir_acc_lo": lo, "dir_acc_hi": hi,
               "avg_win_pips": float(win.pips.mean()) if len(win) else 0.0, "avg_loss_pips": float(los.pips.mean()) if len(los) else 0.0,
               "expectancy_pips": float(t.pips.mean()), "expectancy_R": float(t.R.mean()), "gross_pips": float(t.gross_pips.mean()),
               "carry_pips": float(t.carry_pips.mean()), "avg_hold_sessions": float(t.holding_sessions.mean()),
               "stop_share": float(t.exit_reason.isin(["stop", "trail"]).mean()), "target_share": float((t.exit_reason == "target").mean()),
               "max_dd_R": dd, "total_pips": float(t.pips.sum()), "t_pips": float(t.pips.mean() / t.pips.std() * math.sqrt(len(t))) if len(t) > 2 and t.pips.std() > 0 else 0.0}
    if len(s):
        mo = s["net_bp"].groupby([s.index.year, s.index.month]).sum()
        out["sharpe_monthly"] = float(mo.mean() / mo.std() * math.sqrt(12)) if mo.std() > 0 else 0.0
        out["sharpe_daily"] = float(s.net_bp.mean() / s.net_bp.std() * math.sqrt(252)) if s.net_bp.std() > 0 else 0.0
        out["net_bp_per_year"] = float(s.net_bp.sum() / yrs)
        out["active_frac"] = float((s.pos != 0).mean())
    return out


def hit_rates(stream: pd.DataFrame, a: int, b: int) -> dict:
    """Round-4 reporting on the daily stream: share of active sessions with positive net P&L / correct sign."""
    s = stream[(stream.index.year >= a) & (stream.index.year <= b) & (stream.pos != 0) & stream.fwd_bp.notna()]
    if not len(s):
        return {"n_active_sessions": 0}
    return {"n_active_sessions": len(s), "session_net_positive": float((s.net_bp > 0).mean()),
            "session_sign_correct": float((np.sign(s.fwd_bp) == np.sign(s.pos)).mean())}


def wf_report(stream: pd.DataFrame, name: str, n_arms: int) -> pd.DataFrame:
    """The harness table (per year + 2010-26 / 2016-26 / 2023-26 ...) plus the 2006-based aggregates of this arm."""
    rep = report(stream[["pos", "net_bp"]], periods_per_year=252, name=ARM, n_arms=n_arms)
    extra = []
    for lab, a, b in (("2006-2026", 2006, 2026), ("2006-2015", 2006, 2015)):
        m = (stream.index.year >= a) & (stream.index.year <= b)
        extra.append({"arm": ARM, "period": lab, **_agg(stream.net_bp[m], 252), "active_frac": float((stream.pos[m] != 0).mean())})
    rep = pd.concat([rep, pd.DataFrame(extra)], ignore_index=True)
    rep.insert(1, "variant", name)
    return rep


# ============================================================================= pipeline
def prepare(P: pd.DataFrame | None = None, feature_shift: int = 0) -> pd.DataFrame:
    P = load_prices() if P is None else P
    X = build_features(P)
    if feature_shift:
        keep = [c for c in X.columns if c in PRED or c in ("seas21", "seas42")]
        X[keep] = X[keep].shift(feature_shift)
    X = add_seas_month(X)
    if feature_shift:
        X[["seas_month21", "seas_month42"]] = X[["seas_month21", "seas_month42"]].shift(feature_shift)
    for f in ("close", "open", "high", "low", "cdate", "close_time", "src"):
        X[f"__{f}"] = P[f]
    return X


def main_sample(X: pd.DataFrame) -> pd.DataFrame:
    return X[X["__cdate"] >= "1999-01-04"]


def pre_sample(X: pd.DataFrame) -> pd.DataFrame:
    return X[X["__cdate"] < "1999-01-01"]     # labels of the last weeks of 1998 run into the euro (same asset by construction)


CANDIDATES = [(f"{kind}_{clock}_p{int(thr * 100)}", kind, clock, thr) for kind in ("S", "T", "L") for clock in ("M", "W") for thr in (0.55, 0.60)]


def select_final(stats: pd.DataFrame) -> tuple[str, str]:
    """The declared rule on the 2006-2015 trade statistics of the 12 candidates."""
    s = stats[stats.era == "2006-2015"].set_index("variant")
    for floor, tag in ((8.0, "rule (>= 8 trades a year)"), (4.0, "fallback (>= 4 trades a year)")):
        ok = s[(s.trades_per_year >= floor) & (s.expectancy_pips > 0)]
        if len(ok):
            return ok["dir_acc_lo"].idxmax(), tag
    return s["dir_acc_lo"].idxmax(), "FAILED: no candidate qualifies; best Wilson bound flagged only so that a stream exists"


def run(cost_pips: float = 1.2, save: bool = True, verbose: bool = True):
    """Entry point: returns (positions Series of the final rule, harness report DataFrame of all 12 candidates)."""
    say = (lambda *a: print(*a, flush=True)) if verbose else (lambda *a: None)
    Xall = prepare()
    X = main_sample(Xall)
    say("main sample", X.index[0], X.index[-1], len(X), "weekly rows", int(X.is_w.sum()), "month-ends", int(X.is_m.sum()))
    # ---- forecasts: 3 models x 3 targets
    F = {}
    for kind in ("S", "T", "L"):
        for target in TARGETS:
            F[(kind, target)] = forecast(X, kind, target, TEST_YEARS)
            say("forecast", kind, target, "rows", int(F[(kind, target)].notna().sum()))
    acc = []
    for (kind, target), p in F.items():
        for clock in ("M", "W"):
            acc += accuracy_rows(X, p, target, clock, kind)
    acc = pd.DataFrame(acc)
    # ---- the 12 candidates
    stats, reps, sims = [], [], {}
    for name, kind, clock, thr in CANDIDATES:
        tr, st = simulate(X, F[(kind, "h21")], clock, thr, k=3.0, cost_pips=cost_pips)
        st = st[st.index.year >= TEST_YEARS[0]]
        sims[name] = (tr, st)
        for era, a, b in ERAS:
            stats.append({"variant": name, "group": "candidate", "era": era, **trade_stats(tr, st, a, b)})
        reps.append(wf_report(st, name, n_arms=len(CANDIDATES)))
    stats = pd.DataFrame(stats)
    final, how = select_final(stats)
    say("selection:", final, "|", how)
    _, fk, fc, fthr = next(c for c in CANDIDATES if c[0] == final)
    rep = pd.concat(reps, ignore_index=True)
    rep["cost_pips"] = cost_pips
    rep["final"] = rep["variant"] == final
    # ---- sensitivities of the final rule (never selectable)
    sens = {
        "p65": dict(P=F[(fk, "h21")], thr=0.65), "p70": dict(P=F[(fk, "h21")], thr=0.70),
        "p55": dict(P=F[(fk, "h21")], thr=0.55), "p60": dict(P=F[(fk, "h21")], thr=0.60), "p50_always": dict(P=F[(fk, "h21")], thr=0.5),
        "stop2": dict(P=F[(fk, "h21")], thr=fthr, k=2.0), "trail3": dict(P=F[(fk, "h21")], thr=fthr, trail=True),
        "nostop": dict(P=F[(fk, "h21")], thr=fthr, k=50.0),
        "barrier2_tb": dict(P=F[(fk, "tb")], thr=fthr, k=2.0, target_k=2.0, steps=2 if fc == "M" else 8),
        "h42": dict(P=F[(fk, "h42")], thr=fthr, steps=2 if fc == "M" else 8),
        "cost0.6": dict(P=F[(fk, "h21")], thr=fthr, cost_pips=0.6), "swap_markup0.75": dict(P=F[(fk, "h21")], thr=fthr, markup_pct=0.75),
        "no_carry": dict(P=F[(fk, "h21")], thr=fthr, use_carry=False), "entry_delay1": dict(P=F[(fk, "h21")], thr=fthr, delay=1),
    }
    sens_stats = []
    for nm, kw in sens.items():
        kw = dict(kw)
        P_ = kw.pop("P")
        kw.setdefault("cost_pips", cost_pips)
        tr, st = simulate(X, P_, fc, **kw)
        st = st[st.index.year >= TEST_YEARS[0]]
        for era, a, b in ERAS:
            sens_stats.append({"variant": f"{final}|{nm}", "group": "sensitivity", "era": era, **trade_stats(tr, st, a, b)})
        if nm == "cost0.6":
            r6 = wf_report(st, final, n_arms=len(CANDIDATES)); r6["cost_pips"] = 0.6; r6["final"] = True
            rep = pd.concat([rep, r6], ignore_index=True)
    stats_all = pd.concat([stats, pd.DataFrame(sens_stats)], ignore_index=True)
    tr_f, st_f = sims[final]
    out = st_f[["pos", "fwd_bp", "net_bp", "gross_bp", "carry_bp"]].copy()
    if save:
        RES.mkdir(parents=True, exist_ok=True)
        out.to_parquet(RES / f"{ARM}_positions.parquet")
        tf = tr_f.drop(columns=["entry_loc"]).copy()
        tf.insert(0, "variant", final)
        tf.to_csv(RES / f"{ARM}_trades.csv", index=False, float_format="%.6g")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        stats_all.to_csv(RES / f"{ARM}_trade_stats.csv", index=False, float_format="%.5g")
        acc.to_csv(RES / f"{ARM}_accuracy.csv", index=False, float_format="%.5g")
        pd.DataFrame({f"{k}_{t}": p for (k, t), p in F.items()}).dropna(how="all").to_parquet(RES / f"{ARM}_probabilities.parquet")
        pd.concat([tr.drop(columns=["entry_loc"]).assign(variant=nm) for nm, (tr, _) in sims.items() if len(tr)]).to_csv(
            RES / f"{ARM}_trades_all_candidates.csv", index=False, float_format="%.6g")
    run.state = {"X": X, "Xall": Xall, "F": F, "sims": sims, "final": final, "how": how, "stats": stats_all, "acc": acc, "rep": rep}
    return out["pos"], rep


# ============================================================================= diagnostics (not candidates)
def predictor_table(Xall: pd.DataFrame) -> pd.DataFrame:
    """Single-predictor directional accuracy of the prior-signed vote on weekly rows (no fitting involved)."""
    rows = []
    spans = (("1999-2026", "1999-01-04", "2100"), ("2006-2026", "2006-01-01", "2100"), ("2016-2026", "2016-01-01", "2100"),
             ("1980-1998 (synthetic DEM)", "1980-01-01", "1998-12-31"))
    W = Xall[Xall["is_w"]]
    for p, (fam, kind, prior, definition, span) in PRED.items():
        r = {"predictor": p, "family": fam, "prior": prior, "definition": definition, "data_from": span}
        first = W[pred_cols("h21")[p]].first_valid_index()
        r["first_value"] = str(W.loc[first, "__cdate"].date()) if first is not None else ""
        for tgt in ("h21", "h42"):
            col, T = pred_cols(tgt)[p], TARGETS[tgt]
            for lab, a, b in spans:
                d = W[(W["__cdate"] >= a) & (W["__cdate"] <= b)]
                v, y = np.sign(d[col]), np.sign(d[T["fwd"]])
                ok = v.notna() & y.notna() & (v != 0) & (y != 0)
                n = int(ok.sum())
                key = f"{tgt}_{lab}"
                r[f"acc_{key}"] = float((v[ok] == y[ok]).mean()) if n >= 40 else np.nan
                r[f"n_{key}"] = n
                r[f"neff_{key}"] = n * 5 / T["h"]
        rows.append(r)
    return pd.DataFrame(rows)


def calibration_table(X: pd.DataFrame, P_up: pd.Series, clock: str, target: str = "h21") -> pd.DataFrame:
    T = TARGETS[target]
    d = X[X["is_m"] if clock == "M" else X["is_w"]]
    if clock == "M":
        lc = np.log(d["__close"])
        y = np.sign(lc.shift(-(1 if T["h"] == 21 else 2)) - lc)
    else:
        y = np.sign(d[T["fwd"]])
    p = P_up.reindex(d.index)
    ok = p.notna() & y.notna() & (y != 0)
    conf = np.maximum(p[ok], 1 - p[ok])
    hit = (np.where(p[ok] >= 0.5, 1.0, -1.0) == y[ok].values).astype(float)
    yr = d.index[ok].year
    rows = []
    edges = [0.5, 0.525, 0.55, 0.575, 0.60, 0.65, 0.70, 1.01]
    for era, a, b in ERAS:
        m = (yr >= a) & (yr <= b)
        for lo, hi in zip(edges[:-1], edges[1:]):
            s = m & (conf.values >= lo) & (conf.values < hi)
            n = int(s.sum())
            ci = wilson(int(hit[s].sum()), n) if n else (np.nan, np.nan)
            rows.append({"clock": clock, "target": target, "era": era, "bin": f"[{lo:.3f}, {min(hi, 1):.3f})", "n": n,
                         "mean_predicted": float(conf.values[s].mean()) if n else np.nan, "realised": float(hit[s].mean()) if n else np.nan,
                         "wilson_lo": ci[0], "wilson_hi": ci[1], "n_independent": n if clock == "M" else int(round(n * 5 / T["h"]))})
    return pd.DataFrame(rows)


def incremental(stream: pd.Series | None = None) -> pd.DataFrame:
    """Round-3 test: EW(weak_signals, regime_trend, swing) vs EW(weak_signals, regime_trend) via meta.report_combo."""
    from eurusd.arms import meta
    base, _ = meta.combine(["weak_signals", "regime_trend"], "EW")
    b = meta.report_combo(base, "EW2", 2).set_index("period")
    three, w = meta.combine(["weak_signals", "regime_trend", ARM], "EW")
    t = meta.report_combo(three, "EW3", 3).set_index("period")
    x, ws, rt = meta.load_arm_daily(ARM), meta.load_arm_daily("weak_signals"), meta.load_arm_daily("regime_trend")
    j = pd.concat([x.rename("x"), ws.rename("ws"), rt.rename("rt")], axis=1).fillna(0.0)
    j = j[j.index.year >= 2010]
    row = {"corr_weak_signals": j.x.corr(j.ws), "corr_regime_trend": j.x.corr(j.rt), "corr_two_way": j.x.corr(base["net_bp"].reindex(j.index).fillna(0.0)),
           "years_in_combo": int((w[ARM] > 0).sum()) if ARM in w else 0}
    for lab, y0 in (("2010-2026", 2010), ("2016-2026", 2016), ("2023-2026", 2023)):
        qd = j[j.index.year >= y0]
        A_ = np.c_[np.ones(len(qd)), qd.ws.values, qd.rt.values]
        beta, *_ = np.linalg.lstsq(A_, qd.x.values, rcond=None)
        res = qd.x.values - A_ @ beta
        se = math.sqrt(res.var(ddof=3) * np.linalg.inv(A_.T @ A_)[0, 0])
        row[f"alpha_bp_{lab}"], row[f"alpha_t_{lab}"] = beta[0], beta[0] / se
    for per in ("2010-2026", "2013-2026", "2016-2026", "2023-2026"):
        row[f"SR2_{per}"], row[f"SR3_{per}"] = b.loc[per, "sharpe"], t.loc[per, "sharpe"]
        row[f"t2_{per}"], row[f"t3_{per}"] = b.loc[per, "t"], t.loc[per, "t"]
    return pd.DataFrame([row])


def _final_eval(X: pd.DataFrame, kind: str, clock: str, thr: float, cost_pips: float, years=TEST_YEARS, drop: tuple = (), P_up=None) -> dict:
    p = forecast(X, kind, "h21", years, drop) if P_up is None else P_up
    tr, st = simulate(X, p, clock, thr, k=3.0, cost_pips=cost_pips)
    st = st[st.index.year >= years[0]]
    out = {}
    for era, a, b in (ERAS if years[0] >= 2000 else ((f"{years[0]}-{years[-1]}", years[0], years[-1]),)):
        s = trade_stats(tr, st, a, b)
        out[era] = {k: s.get(k, np.nan) for k in ("n_trades", "trades_per_year", "dir_acc", "win_share", "expectancy_pips", "sharpe_monthly", "sharpe_daily")}
    return out


def permuted_prices(P: pd.DataFrame, seed: int) -> pd.DataFrame:
    """Null path for the main sample: the daily bars from 1999 are re-ordered at random (each day keeps its own
    return and its open/high/low relative to its close), so prices carry no relation to dates, macro or positioning."""
    rng = np.random.default_rng(seed)
    Q = P.copy()
    i0 = int(np.argmax(P["cdate"].values >= np.datetime64("1999-01-04")))
    lc = np.log(P["close"].values)
    r = np.diff(lc)[i0 - 1:]
    rel = {f: np.log(P[f].values[i0:]) - lc[i0:] for f in ("open", "high", "low")}
    perm = rng.permutation(len(r))
    new_lc = lc[i0 - 1] + np.cumsum(r[perm])
    Q.iloc[i0:, Q.columns.get_loc("close")] = np.exp(new_lc)
    for f in ("open", "high", "low"):
        Q.iloc[i0:, Q.columns.get_loc(f)] = np.exp(new_lc + rel[f][perm])
    return Q


def leak_checks(cost_pips: float = 1.2, n_perm: int = 20, verbose: bool = True) -> pd.DataFrame:
    """(1) shuffled labels / permuted price path -> chance; (2) features shifted by extra weeks (and the look-ahead
    control with features from the future); (3) is delivered by `label_correlations`."""
    st = run.state
    X, final = st["X"], st["final"]
    _, kind, clock, thr = next(c for c in CANDIDATES if c[0] == final)
    rows = []

    def add(name, res, **extra):
        for era, d in res.items():
            rows.append({"check": name, "era": era, **d, **extra})
        if verbose:
            e = res.get("2006-2026") or next(iter(res.values()))
            print(f"  {name:38s} acc {e['dir_acc']:.3f} n {e['n_trades']:4.0f} exp {e['expectancy_pips']:+.1f} SRm {e['sharpe_monthly']:+.2f}", flush=True)

    add("final (reference)", _final_eval(X, kind, clock, thr, cost_pips))
    P = load_prices()
    for sh, nm in ((5, "features_lag_plus1week"), (20, "features_lag_plus4weeks"), (65, "features_lag_plus13weeks"),
                   (-5, "features_from_1week_AHEAD_lookahead_control"), (-21, "features_from_21sessions_AHEAD_lookahead_control")):
        add(nm, _final_eval(main_sample(prepare(P, feature_shift=sh)), kind, clock, thr, cost_pips))
    # harness sensitivity: the trend family alone, always in the market, honest vs fed with features from the future
    tr_only = tuple(q for q in PRED if PRED[q][0] != "TR")
    add("control_trend_family_only_honest", _final_eval(X, kind, clock, 0.5, cost_pips, drop=tr_only))
    add("control_trend_family_only_21sessions_AHEAD", _final_eval(main_sample(prepare(P, feature_shift=-21)), kind, clock, 0.5, cost_pips, drop=tr_only))
    # (1a) labels permuted among decision rows, used for fitting AND for scoring
    accs = []
    for seed in range(n_perm):
        rng = np.random.default_rng(100 + seed)
        Xs = X.copy()
        lab = Xs[["fwd21", "fwd42", "tb"]].values.copy()
        ok = np.flatnonzero(np.isfinite(lab[:, 0]))
        lab[ok] = lab[rng.permutation(ok)]
        Xs[["fwd21", "fwd42", "tb"]] = lab
        Xs = add_seas_month(Xs)
        p = forecast(Xs, kind, "h21", TEST_YEARS)
        a = pd.DataFrame(accuracy_rows(Xs, p, "h21", "W", kind, eras=(("2006-2026", 2006, 2026),)))
        accs.append({"seed": seed, **{f"acc_thr{r.thr}": r.acc for r in a.itertuples()}, **{f"n_thr{r.thr}": r.n_acted for r in a.itertuples()}})
    A = pd.DataFrame(accs)
    for thr_ in (0.5, 0.55, 0.60):
        col = f"acc_thr{thr_}"
        nn = A[f"n_thr{thr_}"]
        rows.append({"check": f"shuffled_labels_weekly_accuracy_thr{thr_} (pooled over seeds)", "era": "2006-2026",
                     "dir_acc": float((A[col].fillna(0) * nn).sum() / max(nn.sum(), 1)), "acc_sd_across_seeds": float(A[col].std()),
                     "n_trades": float(nn.mean()), "n_seeds": n_perm})
    if verbose:
        print("  shuffled labels:", {r["check"][:44]: (round(r["dir_acc"], 3), round(r["n_trades"], 1)) for r in rows[-3:]}, flush=True)
    # (1b) permuted price path through the whole pipeline incl. the trade simulation
    res, res0 = [], []
    for seed in range(n_perm):
        Xp = main_sample(prepare(permuted_prices(P, seed)))
        pp = forecast(Xp, kind, "h21", TEST_YEARS)
        res.append(_final_eval(Xp, kind, clock, thr, cost_pips, P_up=pp)["2006-2026"])
        res0.append(_final_eval(Xp, kind, clock, 0.5, cost_pips, P_up=pp)["2006-2026"])
    R0 = pd.DataFrame(res0)
    pooled0 = {c: float((R0[c].fillna(0) * R0.n_trades).sum() / max(R0.n_trades.sum(), 1)) for c in ("dir_acc", "win_share", "expectancy_pips")}
    rows.append({"check": "permuted_price_path_always_in_market (pooled over seeds)", "era": "2006-2026", **{**R0.mean().to_dict(), **pooled0}, "n_seeds": n_perm,
                 "acc_sd_across_seeds": float(R0.dir_acc.std()), "sharpe_sd_across_seeds": float(R0.sharpe_monthly.std()),
                 "sharpe_max_across_seeds": float(R0.sharpe_monthly.max())})
    if verbose:
        print("  permuted path, always in:", {k: round(v, 3) for k, v in rows[-1].items() if isinstance(v, float)}, flush=True)
    R = pd.DataFrame(res)
    pooled = {c: float((R[c].fillna(0) * R.n_trades).sum() / max(R.n_trades.sum(), 1)) for c in ("dir_acc", "win_share", "expectancy_pips")}
    rows.append({"check": "permuted_price_path_full_pipeline (accuracy pooled over seeds)", "era": "2006-2026", **{**R.mean().to_dict(), **pooled}, "n_seeds": n_perm,
                 "acc_sd_across_seeds": float(R.dir_acc.std()), "sharpe_sd_across_seeds": float(R.sharpe_monthly.std()),
                 "sharpe_max_across_seeds": float(R.sharpe_monthly.max())})
    if verbose:
        print("  permuted path:", {k: round(v, 3) for k, v in rows[-1].items() if isinstance(v, float)}, flush=True)
    out = pd.DataFrame(rows)
    out.to_csv(RES / f"{ARM}_leakchecks.csv", index=False, float_format="%.5g")
    return out


def label_correlations(X: pd.DataFrame) -> pd.DataFrame:
    W = X[X["is_w"]]
    rows = []
    for p in PRED:
        r = {"predictor": p}
        for tgt in ("h21", "h42"):
            col = pred_cols(tgt)[p]
            r[f"corr_fwd_{tgt}"] = W[col].corr(W[TARGETS[tgt]["fwd"]])
        rows.append(r)
    return pd.DataFrame(rows)


def ablation(cost_pips: float = 1.2) -> pd.DataFrame:
    """Leave-one-family-out re-runs of the final rule (diagnostic: which predictors carry it)."""
    st = run.state
    X, final = st["X"], st["final"]
    _, kind, clock, thr = next(c for c in CANDIDATES if c[0] == final)
    rows = []
    ref = _final_eval(X, kind, clock, thr, cost_pips)
    for era, d in ref.items():
        rows.append({"ablation": "none (final)", "era": era, **d})
    for fam in FAMILIES:
        drop = tuple(p for p in PRED if PRED[p][0] == fam)
        for era, d in _final_eval(X, kind, clock, thr, cost_pips, drop=drop).items():
            rows.append({"ablation": f"drop {fam}", "era": era, **d})
    for fam in FAMILIES:
        drop = tuple(p for p in PRED if PRED[p][0] != fam)
        for era, d in _final_eval(X, kind, clock, 0.5, cost_pips, drop=drop).items():
            rows.append({"ablation": f"only {fam} (always in the market)", "era": era, **d})
    out = pd.DataFrame(rows)
    out.to_csv(RES / f"{ARM}_ablation.csv", index=False, float_format="%.5g")
    return out


def pre1999(cost_pips: float = 1.2) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Robustness sample 1975-1998 (synthetic DEM-euro, close-only): the same pipeline walked forward over 1982-1998
    for all 12 candidates, with the available predictors only. Never used for any choice."""
    st = run.state
    Xp = pre_sample(st["Xall"])
    rows, accs = [], []
    F = {k: forecast(Xp, k, "h21", PRE_YEARS) for k in ("S", "T", "L")}
    for name, kind, clock, thr in CANDIDATES:
        tr, s = simulate(Xp, F[kind], clock, thr, k=3.0, cost_pips=cost_pips)
        s = s[s.index.year >= PRE_YEARS[0]]
        for era, a, b in (("1982-1998", 1982, 1998), ("1982-1989", 1982, 1989), ("1990-1998", 1990, 1998)):
            rows.append({"variant": name, "era": era, "final": name == st["final"], **trade_stats(tr, s, a, b)})
    for kind, p in F.items():
        for clock in ("M", "W"):
            accs += accuracy_rows(Xp, p, "h21", clock, kind, eras=(("1982-1998", 1982, 1998),))
    a, b = pd.DataFrame(rows), pd.DataFrame(accs)
    a.to_csv(RES / f"{ARM}_pre1999_trade_stats.csv", index=False, float_format="%.5g")
    b.to_csv(RES / f"{ARM}_pre1999_accuracy.csv", index=False, float_format="%.5g")
    return a, b


def weights_table() -> pd.DataFrame:
    """Walk-forward weights of the T and L forecasters (h21) by test year, and the calibration slope b of all three."""
    X = run.state["X"]
    dec = X[X["is_w"] | X["is_m"]]
    rows = []
    for kind in ("S", "T", "L"):
        fit, _ = make_model(kind, "h21")
        for Y in TEST_YEARS:
            tr = dec[dec["end21"] < pd.Timestamp(f"{Y}-01-01", tz=UTC)]
            m = fit(tr)
            r = {"model": kind, "test_year": Y, "b": m["b"], "C": m.get("C", np.nan)}
            if kind == "T":
                r.update(m["m"]["w"])
            elif kind == "L" and m["m"]["lr"] is not None:
                r.update(dict(zip(m["m"]["cols"], m["m"]["lr"].coef_[0])))
            rows.append(r)
    out = pd.DataFrame(rows)
    out.to_csv(RES / f"{ARM}_weights.csv", index=False, float_format="%.4g")
    return out


def live_benchmark(cost_pips: float = 1.2) -> pd.DataFrame:
    """Benchmark, not a candidate: the sign of the LIVE daily exposure (0.5 weak_signals + 0.5 regime_trend, both
    walk-forward from 2010) read at each month-end / week-end and run through the same trade simulator."""
    X = run.state["X"]
    ws = pd.read_parquet(RES / "weak_signals_positions.parquet")["pos"]
    rt = pd.read_parquet(RES / "regime_trend_positions.parquet")["pos"]
    live = (0.5 * ws + 0.5 * rt).reindex(X.index)
    p = (0.5 + 0.2 * np.sign(live)).where(live.notna() & (live != 0))
    rows = []
    for clock in ("M", "W"):
        tr, st = simulate(X, p, clock, 0.55, k=3.0, cost_pips=cost_pips)
        st = st[st.index.year >= 2010]
        for era, a, b in ERAS[2:]:
            rows.append({"variant": f"live_exposure_sign_{clock}", "era": era, **trade_stats(tr, st, a, b)})
    out = pd.DataFrame(rows)
    out.to_csv(RES / f"{ARM}_live_benchmark.csv", index=False, float_format="%.5g")
    return out


def light_state() -> dict:
    """Rebuilds what the diagnostics need (features + the name of the final rule from the saved report) without
    re-running the nine forecasters."""
    Xall = prepare()
    rep = pd.read_csv(RES / f"{ARM}_report.csv")
    run.state = {"X": main_sample(Xall), "Xall": Xall, "final": rep.loc[rep.final, "variant"].iloc[0]}
    return run.state


def full(cost_pips: float = 1.2, n_perm: int = 20) -> None:
    pos, rep = run(cost_pips)
    st = run.state
    X, final = st["X"], st["final"]
    _, kind, clock, thr = next(c for c in CANDIDATES if c[0] == final)
    predictor_table(st["Xall"]).to_csv(RES / f"{ARM}_predictors.csv", index=False, float_format="%.4g")
    pd.concat([calibration_table(X, st["F"][(k, "h21")], c).assign(model=k) for k in ("S", "T", "L") for c in ("M", "W")]).to_csv(
        RES / f"{ARM}_calibration.csv", index=False, float_format="%.4g")
    label_correlations(X).to_csv(RES / f"{ARM}_label_corr.csv", index=False, float_format="%.4g")
    weights_table()
    stream = st["sims"][final][1]
    hr = pd.DataFrame([{"era": era, **hit_rates(stream, a, b)} for era, a, b in ERAS])
    hr.to_csv(RES / f"{ARM}_hitrates.csv", index=False, float_format="%.4g")
    inc = incremental()
    inc.to_csv(RES / f"{ARM}_incremental.csv", index=False, float_format="%.4g")
    print(inc.T.round(3).to_string(), flush=True)
    live_benchmark(cost_pips)
    ablation(cost_pips)
    pre1999(cost_pips)
    leak_checks(cost_pips, n_perm=n_perm)
    print("done", flush=True)


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "full"
    if cmd == "fetch":
        fetch()
    elif cmd == "leak":
        light_state()
        leak_checks()
    elif cmd == "run":
        pos, rep = run()
        print(run.state["stats"][run.state["stats"].group == "candidate"].round(3).to_string())
    else:
        full()
