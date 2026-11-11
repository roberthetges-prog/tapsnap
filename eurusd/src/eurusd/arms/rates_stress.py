"""Arm H ("rates_stress"): market-implied policy expectations and stress measures that the feature store does
NOT contain, one decision per NY-close session, horizon = next session (fwd_1d).

NEW RAW DATA (fetch_data() caches it; everything is lagged ONE CALENDAR DAY with featstore._align_lagged):
  data/processed/cross/zq_fut_D1.parquet  Yahoo ZQ=F, CBOT 30-day fed funds futures, front continuous (rolls on the
                                          first business day of the month: front = the current-month contract;
                                          100 - price = market-implied AVERAGE effective funds rate of that month)
  data/processed/cross/move_D1.parquet    Yahoo ^MOVE, ICE BofA Treasury implied-vol index
  data/processed/cross/vvix_D1.parquet    Yahoo ^VVIX, vol of VIX (from 2007)
  data/macro/ea_all_yield_curve.csv       ECB Data Portal YC.B.U2.EUR.4F.G_N_C.SV_C_YM.SR_{3M,1Y,2Y,5Y,10Y}: spot curve
                                          of ALL euro-area central-government bonds (all ratings), from 2004-09-06
already in the repo and used here: ea_aaa_yield_curve.csv (AAA curve), ea_overnight_rates.csv (EONIA / EUR-STR),
fred_DFEDTAR / DFEDTARL / DFEDTARU (target), fred_FEDFUNDS (monthly average effective rate), fred_EFFR (daily, 2022+).
US real yields / breakevens (DFII10, T10YIE) exist only from 2022 in the mirrors: too short, not used.

SIGNALS (10). Each is oriented so that the ECONOMIC PRIOR says "positive -> long EUR/USD over the next session".
Priors, definitions, lookbacks (5 / 20 sessions, the store's standard) were fixed BEFORE any P&L was computed.
  ffgap        -  priced-in Fed move: (100 - ZQ) minus the "status-quo" month average of the effective funds rate
                  (realised days of the month so far + today's effective rate for the remaining days). > 0 = hike
                  priced for the rest of the month -> USD support -> short EUR/USD.
  ffgap_d5     -  5-session change of ffgap (hawkish repricing -> short EUR/USD)
  ffgap_d20    -  20-session change of ffgap
  relpath_d20  +  relative policy-PATH repricing: 20-session change of [(EA AAA 2y - EUR overnight) - (US 2y - fed
                  effective)], i.e. the 2y-spread change with the realised policy-rate moves stripped out
  stress_lvl   -  euro sovereign stress: mean of (all-issuer - AAA) spot spreads at 2y and 10y, LEVEL (demeaned and
                  scaled with training-window statistics); stress high -> short EUR/USD
  stress_d20   -  20-session change of the same stress spread; stress rising -> short EUR/USD
  spr_lowmove  +  the store's spread trend d_spread2y_20, active only when ^MOVE <= its training-window median
                  (prior: rate differentials drive FX in calm rates regimes; in rates-vol spikes flows dominate)
  spr_lowvvix  +  d_spread2y_20, active only when ^VVIX <= its training-window median (same prior, equity vol-of-vol)
  curve_d20    -  Ang-Chen term-spread change: -(20-session change of (EA 10y-2y) - (US 10y-2y)); a relatively
                  steepening EA curve -> short EUR/USD (currencies with flattening curves earn more)
  carry_vol    +  carry-to-vol: policy_diff (ECB DFR - Fed target) / rv_21d_bp

Standardisation (training window only, as arms/weak_signals.py): 'cont' = divide by the training std (no
demeaning, the raw sign is the economic content), clip +-2, /2; 'level' = demean with the training mean first;
'gate' = 'cont' on the base column times 1[gate column <= training median of the gate column]. Missing -> 0.

VARIANTS (12 in total, counted): 10 single-signal variants (sign mapping: +-1 when |z| > training median of |z|)
and 2 combinations with the house method (weights = training-window univariate t-stat of each signal vs fwd_1d,
clipped at 0, normalised): `tstat_sign` and `tstat_linear` (linear: clip(score / Q80_train, -1, 1) with a 20 %
training dead zone). All positions are vol-scaled: pos *= min(1, median_train(rv_21d_bp) / rv_21d_bp).

SELECTION RULE (declared before any result was looked at): the arm's final variant is the COMBINATION variant
(tstat_sign or tstat_linear) with the higher 2010-2015 walk-forward NET Sharpe at 1.2 pips. Single-signal variants
are reported in the same table but are not eligible (they are the diagnostic of which signal carries information).
"""
from __future__ import annotations

import io
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.wf import walk_forward, pnl_from_positions, report, to_positions  # noqa: E402
from eurusd.featstore import _align_lagged, _cross_daily, _macro_series  # noqa: E402

FEATURES = ROOT / "data/processed/features_daily.parquet"
MACRO = ROOT / "data/macro"
CROSS = ROOT / "data/processed/cross"
RES = ROOT / "experiments/results/arms"
ARM = "rates_stress"
N_VARIANTS = 12

YAHOO = {"zq_fut": "ZQ=F", "move": "^MOVE", "vvix": "^VVIX"}
ECB_ALL_KEY = "YC/B.U2.EUR.4F.G_N_C.SV_C_YM.SR_3M+SR_1Y+SR_2Y+SR_5Y+SR_10Y"
ECB_ALL_FILE = MACRO / "ea_all_yield_curve.csv"

# name: (kind, gate column or None, description). Raw columns are already prior-oriented in build_raw_signals.
SIGNALS = {
    "ffgap":       ("cont",  None,     "-(priced-in Fed move): (100-ZQ) minus status-quo month-average effective rate"),
    "ffgap_d5":    ("cont",  None,     "-(5-session change of the priced-in Fed move)"),
    "ffgap_d20":   ("cont",  None,     "-(20-session change of the priced-in Fed move)"),
    "relpath_d20": ("cont",  None,     "+20-session change of [(EA 2y - EUR overnight) - (US 2y - fed effective)]"),
    "stress_lvl":  ("level", None,     "-(all-issuer minus AAA euro spot spread, mean of 2y and 10y), level"),
    "stress_d20":  ("cont",  None,     "-(20-session change of the euro sovereign stress spread)"),
    "spr_lowmove": ("gate",  "g_move", "+d_spread2y_20 when ^MOVE <= training median"),
    "spr_lowvvix": ("gate",  "g_vvix", "+d_spread2y_20 when ^VVIX <= training median"),
    "curve_d20":   ("cont",  None,     "-(20-session change of (EA 10y-2y) - (US 10y-2y)) (Ang-Chen term-spread change)"),
    "carry_vol":   ("cont",  None,     "+policy_diff / rv_21d_bp (carry to vol)"),
}
GATES = ("g_move", "g_vvix")
Q_HI, Q_DEAD, Q_SIGN = 0.80, 0.20, 0.50


# ---------------------------------------------------------------- data fetch (cached)
def _yahoo_daily(symbol: str) -> pd.DataFrame:
    import requests
    last = None
    for attempt in range(4):
        for host in ("query2", "query1"):
            try:
                r = requests.get(f"https://{host}.finance.yahoo.com/v8/finance/chart/{symbol}",
                                 params={"period1": 0, "period2": int(time.time()), "interval": "1d"},
                                 headers={"User-Agent": "Mozilla/5.0"}, timeout=60)
                if r.status_code != 200:
                    last = f"{host}: HTTP {r.status_code}"
                    time.sleep(3)
                    continue
                d = r.json()["chart"]["result"][0]
                q = d["indicators"]["quote"][0]
                df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close", "volume")},
                                  index=pd.to_datetime(d["timestamp"], unit="s", utc=True)).dropna(subset=["close"])
                df.index.name = "time"
                # drop the in-progress bar (session date = today or later, UTC)
                today = pd.Timestamp.now(tz="UTC").normalize()
                return df[df.index.normalize() < today]
            except Exception as e:  # network / parse
                last = f"{host}: {e}"
                time.sleep(3)
    raise RuntimeError(f"Yahoo fetch failed for {symbol}: {last}")


def _ecb_all_curve() -> pd.DataFrame:
    import requests
    r = requests.get(f"https://data-api.ecb.europa.eu/service/data/{ECB_ALL_KEY}",
                     params={"format": "csvdata", "detail": "dataonly"}, timeout=300)
    r.raise_for_status()
    d = pd.read_csv(io.StringIO(r.text))
    w = d.pivot(index="TIME_PERIOD", columns="DATA_TYPE_FM", values="OBS_VALUE")
    w = w.rename(columns={"SR_3M": "all_spot_3m", "SR_1Y": "all_spot_1y", "SR_2Y": "all_spot_2y", "SR_5Y": "all_spot_5y", "SR_10Y": "all_spot_10y"})
    w = w[["all_spot_3m", "all_spot_1y", "all_spot_2y", "all_spot_5y", "all_spot_10y"]]
    w.index.name = "date"
    return w.sort_index()


def fetch_data(refresh: bool = False, verbose: bool = True) -> dict:
    """Downloads (or re-uses the cached) new raw series. Returns {name: (rows, first, last)}."""
    out = {}
    for name, sym in YAHOO.items():
        p = CROSS / f"{name}_D1.parquet"
        if refresh or not p.exists():
            df = _yahoo_daily(sym)
            df.to_parquet(p)
            time.sleep(1)
        df = pd.read_parquet(p)
        out[name] = (len(df), str(df.index[0].date()), str(df.index[-1].date()))
    if refresh or not ECB_ALL_FILE.exists():
        _ecb_all_curve().to_csv(ECB_ALL_FILE)
    e = pd.read_csv(ECB_ALL_FILE)
    out["ea_all_yield_curve"] = (len(e), e["date"].iloc[0], e["date"].iloc[-1])
    if verbose:
        for k, v in out.items():
            print(f"  data {k:20s} rows {v[0]:5d}  {v[1]} .. {v[2]}", flush=True)
    return out


# ---------------------------------------------------------------- derived raw series (stamped on their own date)
def fed_effective_daily() -> pd.Series:
    """Calendar-daily effective fed funds rate. From 2022-01-03: FRED EFFR (stamped on the day it refers to,
    published the next morning). Before: target (mid-point of the range from 2008-12-16) + the previous month's
    gap between the monthly average effective rate (FEDFUNDS) and that month's average target (known on the first
    business day of the month)."""
    tgt = _macro_series("fred_DFEDTAR.csv")
    lo, hi = _macro_series("fred_DFEDTARL.csv"), _macro_series("fred_DFEDTARU.csv")
    mid = pd.concat([tgt[tgt.index < lo.index[0]], (lo + hi) / 2]).sort_index()
    effr = _macro_series("fred_EFFR.csv").dropna()
    days = pd.date_range(mid.index[0], max(mid.index[-1], effr.index[-1]), freq="D")
    mid = mid.reindex(days).ffill()
    ff = _macro_series("fred_FEDFUNDS.csv")                      # stamped YYYY-MM-01 = average of that month
    mid_m = mid.groupby(mid.index.to_period("M")).mean()
    gap_m = pd.Series(ff.values, index=ff.index.to_period("M")).reindex(mid_m.index) - mid_m
    gap_prev = gap_m.shift(1)                                    # previous month's gap, usable during the current month
    proxy = mid + pd.Series(gap_prev.reindex(days.to_period("M")).values, index=days).ffill()
    # inside the target range once a range exists (the Dec-2008 gap would otherwise push Jan-2009 below zero)
    rng_lo, rng_hi = lo.reindex(days).ffill(), hi.reindex(days).ffill()
    proxy = proxy.where(rng_lo.isna(), proxy.clip(lower=rng_lo, upper=rng_hi))
    eff = proxy.copy()
    e = effr.reindex(days).ffill()
    eff[days >= effr.index[0]] = e[days >= effr.index[0]]
    return eff.dropna()


def ff_gap_series(zq: pd.Series, eff: pd.Series) -> pd.Series:
    """Priced-in Fed move on each ZQ session date D (contract month = calendar month of D, N days):
    (100 - ZQ_D) - [sum of the effective rate over the days of the month up to D + (N - d) * eff_D] / N.
    Uses the effective rate up to and including D (published D+1 morning); the series is then lagged one calendar
    day like every other market series."""
    eff = eff.reindex(pd.date_range(eff.index[0], max(eff.index[-1], zq.index[-1]), freq="D")).ffill()
    per = eff.index.to_period("M")
    cum = eff.groupby(per).cumsum()
    n = pd.Series(eff.index.days_in_month, index=eff.index)
    d = pd.Series(eff.index.day, index=eff.index)
    status_quo = (cum + (n - d) * eff) / n
    return ((100.0 - zq) - status_quo.reindex(zq.index)).dropna()


def ea_overnight() -> pd.Series:
    """EUR overnight rate in EUR-STR terms: EUR-STR from 2019-10-01, before that EONIA - 8.5 bp (the fixed
    EONIA = EUR-STR + 8.5 bp recalibration); 10-observation rolling median to remove EONIA end-of-period spikes."""
    o = pd.read_csv(MACRO / "ea_overnight_rates.csv", parse_dates=["date"]).set_index("date")
    s = o["estr"].astype(float).combine_first(o["eonia"].astype(float) - 0.085).dropna()
    return s.rolling(10, min_periods=3).median()


def stress_spread() -> pd.Series:
    """Euro sovereign stress: all-issuer minus AAA spot yield, mean of the 2y and 10y points (percentage points)."""
    al = pd.read_csv(ECB_ALL_FILE, parse_dates=["date"]).set_index("date")
    aa = pd.read_csv(MACRO / "ea_aaa_yield_curve.csv", parse_dates=["date"]).set_index("date")
    s = 0.5 * ((al["all_spot_2y"] - aa["aaa_spot_2y"]) + (al["all_spot_10y"] - aa["aaa_spot_10y"]))
    return s.dropna()


# ---------------------------------------------------------------- signals
def build_raw_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Raw, prior-ORIENTED signals on the feature-store index (positive = long EUR/USD under the prior) plus the
    gate columns. Every new series is aligned with featstore._align_lagged(..., lag_days=1) on the session's
    closing date, exactly as the store's own macro columns."""
    fetch_data(verbose=False)
    cdate = pd.DatetimeIndex(pd.DatetimeIndex(df["close_time"]).tz_convert("UTC").normalize().tz_localize(None))
    A = lambda s: pd.Series(_align_lagged(s, cdate, 1).values, index=df.index)  # noqa: E731
    eff = fed_effective_daily()
    ffgap = A(ff_gap_series(_cross_daily("zq_fut"), eff))
    us_path = df["us2y"] - A(eff)
    ea_path = df["ea2y"] - A(ea_overnight())
    stress = A(stress_spread())
    S = pd.DataFrame(index=df.index)
    S["ffgap"] = -ffgap
    S["ffgap_d5"] = -ffgap.diff(5)
    S["ffgap_d20"] = -ffgap.diff(20)
    S["relpath_d20"] = (ea_path - us_path).diff(20)
    S["stress_lvl"] = -stress
    S["stress_d20"] = -stress.diff(20)
    S["spr_lowmove"] = df["d_spread2y_20"]
    S["spr_lowvvix"] = df["d_spread2y_20"]
    S["curve_d20"] = -(df["ea_curve"] - df["us_curve"]).diff(20)
    S["carry_vol"] = df["policy_diff"] / df["rv_21d_bp"]
    S["g_move"] = A(_cross_daily("move"))
    S["g_vvix"] = A(_cross_daily("vvix"))
    return S[list(SIGNALS) + list(GATES)]


def _scaler_fit(S: pd.DataFrame, signals: list[str]) -> dict:
    st = {}
    for k in signals:
        kind, gate, _ = SIGNALS[k]
        x = S[k].dropna()
        sd = float(x.std()) if len(x) > 20 and x.std() > 0 else 1.0
        mu = float(x.mean()) if kind == "level" and len(x) > 20 else 0.0
        thr = float(S[gate].median()) if gate is not None and S[gate].notna().sum() > 20 else np.nan
        st[k] = (mu, sd, thr)
    return st


def _scaler_apply(S: pd.DataFrame, st: dict) -> pd.DataFrame:
    out = pd.DataFrame(index=S.index)
    for k, (mu, sd, thr) in st.items():
        z = ((S[k] - mu) / sd).clip(-2, 2) / 2
        gate = SIGNALS[k][1]
        if gate is not None:
            z = z.where(S[gate] <= thr, 0.0)          # NaN gate or NaN threshold -> 0
        out[k] = z.fillna(0.0)
    return out


def _tstat_weights(Z: pd.DataFrame, y: pd.Series) -> np.ndarray:
    X, yy = Z.values, y.values
    k = X.shape[1]
    if k == 1:
        return np.ones(1)
    t = np.zeros(k)
    for j in range(k):
        x = X[:, j]
        if x.std() == 0:
            continue
        r = np.corrcoef(x, yy)[0, 1]
        t[j] = r * np.sqrt(len(yy) - 2) / np.sqrt(max(1e-12, 1 - r * r))
    w = np.clip(t, 0, None)
    if w.sum() <= 0:
        w = np.ones(k)
    return w / np.abs(w).sum()


def make_fit_predict(mapping: str, signals: list[str], weight_log: dict | None = None):
    def fit(train: pd.DataFrame):
        st = _scaler_fit(train, signals)
        Z = _scaler_apply(train, st)
        ok = train["fwd_1d"].notna()
        w = _tstat_weights(Z[ok], train["fwd_1d"][ok])
        a = np.abs(Z.values @ w)
        thr = {"hi": float(np.quantile(a, Q_HI)), "dead": float(np.quantile(a, Q_DEAD)), "med": float(np.quantile(a, Q_SIGN))}
        if weight_log is not None:
            weight_log[train.index.max().year + 1] = pd.Series(w, index=signals)
        return {"st": st, "w": w, "thr": thr, "target_vol": float(train["rv_21d_bp"].median())}

    def predict(m, test: pd.DataFrame) -> pd.Series:
        Z = _scaler_apply(test, m["st"])
        score = pd.Series(Z.values @ m["w"], index=test.index)
        thr = m["thr"]
        if mapping == "linear":
            pos = (score / max(thr["hi"], 1e-9)).clip(-1, 1).where(score.abs() > thr["dead"], 0.0)
        else:
            pos = np.sign(score).where(score.abs() > thr["med"], 0.0)
        return to_positions(pos, "linear", threshold=1.0, vol=test["rv_21d_bp"], target_vol_bp=m["target_vol"])
    return fit, predict


def load_frame() -> pd.DataFrame:
    df = pd.read_parquet(FEATURES)
    S = build_raw_signals(df)
    return pd.concat([S, df[["fwd_1d", "rv_21d_bp", "close", "label_end_1d"]]], axis=1)


def run_variant(D: pd.DataFrame, mapping: str, signals: list[str], cost_pips: float, name: str, weight_log: dict | None = None):
    fit, predict = make_fit_predict(mapping, signals, weight_log)
    pos = walk_forward(D, fit, predict, label_end=D["label_end_1d"], verbose=False).fillna(0.0)
    pnl = pnl_from_positions(pos, D["fwd_1d"], D["close"], cost_pips=cost_pips)
    pnl = pnl[pos.index.year >= 2010]
    tbl = report(pnl, periods_per_year=252, name=ARM, n_arms=N_VARIANTS)
    tbl.insert(1, "variant", name)
    return pos, pnl, tbl


def _line(name: str, tbl: pd.DataFrame) -> str:
    r = tbl.set_index("period")
    return (f"{name:14s} 2010-15 SR {r.loc['2010-2015','sharpe']:+.2f} | 2010-26 SR {r.loc['2010-2026','sharpe']:+.2f} t {r.loc['2010-2026','t']:+.2f} | "
            f"2016-26 SR {r.loc['2016-2026','sharpe']:+.2f} t {r.loc['2016-2026','t']:+.2f} | 2023-26 SR {r.loc['2023-2026','sharpe']:+.2f} t {r.loc['2023-2026','t']:+.2f}")


# ---------------------------------------------------------------- entry point
def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Runs the 10 single-signal variants and the 2 t-stat combinations walk-forward, applies the selection rule,
    adds the 0.6-pip sensitivity of the final variant and writes the deliverables.
    Returns (final OOS positions, report DataFrame)."""
    D = load_frame()
    signals = list(SIGNALS)
    rows, store = [], {}
    for s in signals:
        pos, pnl, tbl = run_variant(D, "sign", [s], cost_pips, s)
        tbl["final"] = False
        tbl["kind"] = "single_signal"
        rows.append(tbl)
        store[s] = (pos, pnl, tbl, None)
        if verbose:
            print(_line(s, tbl), flush=True)
    for mapping in ("sign", "linear"):
        name = f"tstat_{mapping}"
        wl = {}
        pos, pnl, tbl = run_variant(D, mapping, signals, cost_pips, name, weight_log=wl)
        tbl["final"] = False
        tbl["kind"] = "combination"
        rows.append(tbl)
        store[name] = (pos, pnl, tbl, wl)
        if verbose:
            print(_line(name, tbl), flush=True)
    sel = {n: float(store[n][2].set_index("period").loc["2010-2015", "sharpe"]) for n in ("tstat_sign", "tstat_linear")}
    final = max(sel, key=sel.get)
    if verbose:
        print(f"FINAL variant by rule (combination with the best 2010-2015 net Sharpe): {final} ({sel[final]:+.2f})", flush=True)
    for t in rows:
        if t["variant"].iloc[0] == final:
            t["final"] = True
    _, _, tbl06 = run_variant(D, final.split("_")[1], signals, 0.6, f"{final}_cost0.6")
    tbl06["final"] = False
    tbl06["kind"] = "cost_sensitivity"
    rows.append(tbl06)
    rep = pd.concat(rows, ignore_index=True)
    pos, pnl, tbl, wl = store[final]
    out = pd.DataFrame({"pos": pos, "fwd_bp": D["fwd_1d"], "net_bp": pnl["net_bp"].reindex(pos.index)})
    out = out[out.index.year >= 2010]
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        out.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        W = pd.DataFrame(wl).T
        W.index.name = "test_year"
        W.to_csv(RES / f"{ARM}_weights.csv")
        allpos = pd.DataFrame({n: v[1]["net_bp"] for n, v in store.items()})
        allpos.to_parquet(RES / f"{ARM}_all_variants_net_bp.parquet")
    return out["pos"], rep


# ---------------------------------------------------------------- leak checks
def leak_checks(final: str, cost_pips: float = 1.2, seed: int = 0) -> pd.DataFrame:
    """(1) shuffled labels; (2) signals lagged by 1 / 5 / 21 extra sessions and a look-ahead control (signals of the
    NEXT session); (3) full-sample correlation of each standardised signal with the label."""
    D = load_frame()
    signals = list(SIGNALS)
    cols = signals + list(GATES)
    mapping = final.split("_")[1]
    out = []
    rng = np.random.default_rng(seed)
    Ds = D.copy()
    Ds["fwd_1d"] = rng.permutation(D["fwd_1d"].values)
    _, _, t = run_variant(Ds, mapping, signals, cost_pips, "shuffled_labels")
    out.append(t.assign(check="shuffled_labels"))
    for lag, nm in ((1, "features_shift_plus1"), (5, "features_shift_plus5"), (21, "features_shift_plus21"), (-1, "features_shift_minus1_lookahead_control")):
        Dl = D.copy()
        Dl[cols] = D[cols].shift(lag)
        _, _, t = run_variant(Dl, mapping, signals, cost_pips, nm)
        out.append(t.assign(check=nm))
    Z = _scaler_apply(D, _scaler_fit(D, signals))
    c = Z.corrwith(D["fwd_1d"])
    corr = pd.DataFrame({"period": c.index, "corr_with_fwd_1d": c.values})
    corr["check"] = "signal_label_corr"
    return pd.concat(out + [corr], ignore_index=True)


# ---------------------------------------------------------------- incremental value and correlations
def incremental() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Three-way vs two-way EW meta-combination (round-3 addendum) and daily-P&L correlations with the live arms.
    Needs the positions file written by run()."""
    from eurusd.arms.meta import combine, load_arm_daily, report_combo
    tabs = []
    for arms, nm in ((["weak_signals", "regime_trend"], "EW_2way"), (["weak_signals", "regime_trend", ARM], "EW_3way")):
        pnl, w = combine(arms, "EW")
        t = report_combo(pnl, nm, N_VARIANTS)
        t["weights_last_year"] = str(w.iloc[-1].round(2).to_dict())
        tabs.append(t)
    streams = pd.DataFrame({a: load_arm_daily(a) for a in ("weak_signals", "regime_trend", ARM)}).fillna(0.0)
    rows = []
    for lab, a, b in (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026)):
        x = streams[(streams.index.year >= a) & (streams.index.year <= b)]
        c = x.corr()
        rows.append({"period": lab, "corr_weak_signals": c.loc[ARM, "weak_signals"], "corr_regime_trend": c.loc[ARM, "regime_trend"],
                     "corr_weak_vs_regime": c.loc["weak_signals", "regime_trend"]})
    return pd.concat(tabs, ignore_index=True), pd.DataFrame(rows)


def signal_correlations() -> pd.DataFrame:
    """Full-sample (2004-09..) correlation of the standardised new signals with each other and with the existing
    macro signals of the live combination (spread trend, fair-value residual, equity relative momentum, COT)."""
    df = pd.read_parquet(FEATURES)
    D = load_frame()
    Z = _scaler_apply(D, _scaler_fit(D, list(SIGNALS)))
    Z["old_spread"] = df["d_spread2y_20"]
    Z["old_fv"] = -df["fv_resid_z"]
    Z["old_eqrel"] = -df["spx_minus_sx5e_20"]
    Z["old_cot"] = df["cot_z52"]
    Z["old_mom252"] = -df["ret_252d"]
    return Z[Z.index >= "2004-10-01"].corr()


if __name__ == "__main__":
    cost = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
    fetch_data()
    pos, rep = run(cost_pips=cost)
    final = rep.loc[rep["final"], "variant"].iloc[0]
    lc = leak_checks(final, cost_pips=cost)
    lc.to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
    for chk in ("shuffled_labels", "features_shift_plus1", "features_shift_plus5", "features_shift_plus21", "features_shift_minus1_lookahead_control"):
        print("leak", _line(chk[:14], lc[lc.check == chk]), chk)
    print(lc[lc.check == "signal_label_corr"][["period", "corr_with_fwd_1d"]].to_string(index=False))
    inc, cor = incremental()
    inc.to_csv(RES / f"{ARM}_incremental.csv", index=False)
    cor.to_csv(RES / f"{ARM}_pnl_corr.csv", index=False)
    print(inc[inc.period.isin(["2010-2026", "2013-2026", "2016-2026", "2023-2026"])].round(3).to_string(index=False))
    print(cor.round(3).to_string(index=False))
    sc = signal_correlations()
    sc.to_csv(RES / f"{ARM}_signal_corr.csv")
    print(sc.round(2).to_string())
