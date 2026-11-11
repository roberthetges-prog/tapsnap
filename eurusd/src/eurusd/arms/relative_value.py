"""Arm L "relative_value": EUR/USD relative to the rest of the currency market.

Every EUR/USD move is part dollar move (shared with GBP JPY CHF AUD CAD NZD SEK NOK), part euro move (shared with
the EUR crosses) and part idiosyncratic. This arm decomposes EUR/USD against a basket of the other eight G10 dollar
pairs and tests reversal of the residual, continuation of the dollar component, lead-lag from the other pairs,
dispersion and PCA factors.

PROTOCOL (everything in this docstring was written BEFORE any strategy result was computed; only the data-timing
checks of section "Data", which never touch a label, were run first)
----------------------------------------------------------------------------------------------------------------
Data and timing
* PRIMARY: Federal Reserve H.10 noon-New-York buying rates (datahub.io copy of the full H.10 table, the raw file
  behind data/macro/datahub_fx_fed_h10_daily.csv, 1971..2026-11-06) for GBP JPY CHF AUD CAD NZD SEK NOK and EUR.
  All nine come from one source at one instant (12:00 New York), so the cross-section is synchronous.
* EUR/USD's own value in the decomposition is H10's EUR rate, i.e. the same source and the same instant as the
  basket. That instant is verified against our hourly bars: H10 EUR matches the open of our bar that starts at
  12:00 New York (median |diff| = 1.0 pip, daily-return correlation 0.997; every other hour is worse, e.g. 11:00
  8 pips / 0.94, 13:00 7 pips / 0.96). Our own 12:00 bar is NOT used in the residual because on 26 fast-market days
  it differs from the fixing by more than 20 pips, which would put pure sampling noise into the residual; all P&L
  is on our own 17:00 closes.
* A session row closes at 17:00 New York on NY date D. Its signals use the noon panel up to and including date D:
  noon is 5 hours BEFORE the close at which we trade, so the information is strictly known. This is a tighter lag
  than the feature store's one calendar day (which would be noon of D-1, 29 hours stale); the one-calendar-day
  version is run for every candidate as the "features one period late" leak check, and the opposite shift (noon of
  the NEXT H10 date, i.e. 19 hours inside the label) is the look-ahead probe that must give an impossible Sharpe.
* Yahoo daily closes (GBPUSD=X USDJPY=X USDCHF=X AUDUSD=X USDCAD=X NZDUSD=X USDSEK=X USDNOK=X EURGBP=X EURJPY=X
  EURCHF=X DX-Y.NYB, cached in data/processed/cross/<name>_D1.parquet) are fetched and verified against H10 but NOT
  used for any signal: (a) their stamp convention changes in mid-2010 (before: the bar stamped London date D closes
  at 24:00 London of D, i.e. 2-3 hours AFTER our session close of D; after: it is the price at 00:00 London of D,
  21-22 hours before our close), (b) they are never synchronous with our close, (c) the EUR crosses are triangular
  identities of the dollar pairs, so the H10 panel already contains them (EUR/GBP = EURUSD / GBPUSD at noon).

Decomposition (all returns noon-to-noon log returns in bp on the H10 date grid, quoted as USD per unit of the
currency so that "+" has the sign of EUR/USD up)
* regression basket: rolling OLS of r_EUR on the 8 other returns with intercept over the previous 250 H10 days
  (days t-250..t-1, never day t); dollar/basket component d_t = beta_{t-1}' r_t, residual e_t = r_EUR,t - d_t.
* Robustness rule (added after looking at the raw return panel, before any strategy result): each of the nine daily
  return series is winsorised at +-6 of its own previous-250-day standard deviations (35 currency-days in 23 years:
  SNB floor set / removed, Brexit, October 2008, March 2020, ...), the residual is winsorised the same way, and the
  z-scores of pair_coint are clipped at +-4. Without this the SNB break of 2015-01-15 (CHF +15 %, a -1276 bp
  "residual" because CHF had a 0.8 beta during the floor) dominates every scale and the betas of the next 250 days.
* PCA: for each test year Y the principal components of the 8 non-EUR returns are fitted on H10 dates before
  Y-01-01 (expanding), EUR is regressed on PC1 (dollar) and PC2 (risk/carry) on the same window, and the frozen
  loadings give the residual of year Y. Dates before 2010 use the fit on 2003-2009 (all of it training data).

The 12 candidates (prior sign fixed here; "+" = long EUR/USD over the next session)
   1 res_rev5     -(sum of e over 5 days)                 residual mean reversion over days
   2 res_rev20    -(sum of e over 20 days)                residual mean reversion over weeks
   3 res_coint    -z250(cumulative e)                     cointegration spread: level of the cumulated residual vs
                                                          its previous-250-day mean/sd
   4 usd_trend20  +(sum of d over 20 days)                the dollar component trends (hypothesis 2)
   5 lead_usd1    +d_t                                    yesterday-noon-to-today-noon move of the other dollar pairs,
                                                          in EUR/USD beta units, continues in EUR/USD (diffusion)
   6 lead_comm1   +mean(r_AUD, r_CAD, r_NZD)              commodity currencies lead
   7 lead_risk1   -(r_JPY - mean(r_AUD, r_CAD, r_NZD))    risk-off (yen beats commodity FX) leads EUR/USD lower
   8 lead_eurx1   +(r_EUR - mean(r_GBP, r_JPY, r_CHF))    EUR-cross factor (EURGBP, EURJPY, EURCHF average) leads
   9 disp_cond5   (sum of r_EUR over 5 days) x sign(median of the previous 500 days of disp5 - disp5), disp5 = cross-
                  sectional sd of the nine 5-day returns: follow EUR/USD when the dollar pairs agree (broad dollar
                  move), fade it when they disagree (idiosyncratic move)
  10 pca_rev5     -(sum of PCA residual over 5 days)      loading-adjusted residual reversal
  11 pair_coint   -mean(z250(log EURCHF), z250(log EURGBP))   pairs trade against the two nearest European pairs
  12 combo_tstat  the house t-stat-weighted combination (weak_signals._weights "tstat": weight_i = max(t_i, 0) of
                  the training-window univariate t-stat against fwd_1d) of signals 1-11
Standardisation and position (house method, identical for all): z = signal / training sd (no demeaning), for the
combination clip +-2 and halve; pos = sign(z) when |z| > training median of |z| else 0, times
min(1, median_train(rv_21d_bp) / rv_21d_bp). One decision per NY-close session, label fwd_1d, cost 1.2 pips per unit
turnover (0.6 sensitivity), yearly expanding walk-forward through eurusd.wf.

fwd_5d: every signal is also evaluated for the 5-session horizon as a DIAGNOSTIC that is not eligible for selection:
(a) out-of-sample correlation with fwd_5d and its Newey-West t (4 lags), (b) the P&L of holding each day's position
for 5 sessions (position = mean of the last 5 daily positions, P&L on fwd_1d, cost on the net turnover).
Looks in total: 12 candidates + 12 five-day-hold diagnostics.

SELECTION RULE: the final variant is the candidate (1..12) with the highest 2010-2015 walk-forward NET Sharpe at
1.2 pips; its full 2010-2026 record is then reported whatever it is. Nothing is chosen on 2016-2026 or 2023-2026.
Incremental test: meta.combine(["weak_signals","regime_trend","relative_value"], "EW") against the two-way
combination, and the daily-P&L correlation with both. Hit rates of the final variant for the three periods.
Leak checks: shuffled labels; features one period late (H10 lagged one calendar day, the feature-store convention);
look-ahead probe (next H10 date); correlation of every signal with the label.
"""
from __future__ import annotations

import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.wf import walk_forward, pnl_from_positions, report, to_positions  # noqa: E402
from eurusd.arms.weak_signals import _weights  # noqa: E402  (house t-stat weighting)

warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", message=".*Sorting by default.*")

FEATURES = ROOT / "data/processed/features_daily.parquet"
H1 = ROOT / "data/processed/EURUSD_H1.parquet"
CROSS = ROOT / "data/processed/cross"
RAW_H10 = ROOT / "data/raw/datahub/exchange-rates_data_daily.csv"
H10_URL = "https://raw.githubusercontent.com/datasets/exchange-rates/master/data/daily.csv"
H10_CACHE = CROSS / "relative_value_h10_g10.parquet"
PANEL_CACHE = CROSS / "relative_value_noon_panel.parquet"
RES = ROOT / "experiments/results/arms"
ARM = "relative_value"
N_VARIANTS = 12

H10_COUNTRY = {"eur": "Euro", "gbp": "United Kingdom", "jpy": "Japan", "chf": "Switzerland", "aud": "Australia",
               "cad": "Canada", "nzd": "New Zealand", "sek": "Sweden", "nok": "Norway"}
BASKET = ["gbp", "jpy", "chf", "aud", "cad", "nzd", "sek", "nok"]
# cache name: (Yahoo symbol, H10 currency or None, +1 if quoted as foreign per USD / -1 if USD per foreign)
YAHOO = {"gbpusd": ("GBPUSD=X", "gbp", -1), "usdjpy": ("USDJPY=X", "jpy", 1), "usdchf": ("USDCHF=X", "chf", 1),
         "audusd": ("AUDUSD=X", "aud", -1), "usdcad": ("USDCAD=X", "cad", 1), "nzdusd": ("NZDUSD=X", "nzd", -1),
         "usdsek": ("USDSEK=X", "sek", 1), "usdnok": ("USDNOK=X", "nok", 1), "eurgbp": ("EURGBP=X", None, 0),
         "eurjpy": ("EURJPY=X", None, 0), "eurchf": ("EURCHF=X", None, 0), "dxy": ("DX-Y.NYB", None, 0)}

SIGNALS = {
    "res_rev5":    "-(5-day sum of the regression residual): residual reversal over days",
    "res_rev20":   "-(20-day sum of the regression residual): residual reversal over weeks",
    "res_coint":   "-z250 of the cumulated regression residual: cointegration-spread reversion",
    "usd_trend20": "+(20-day sum of the dollar/basket component): the dollar component trends",
    "lead_usd1":   "+1-day dollar/basket component (noon to noon): other dollar pairs lead",
    "lead_comm1":  "+1-day mean return of AUD, CAD, NZD vs USD: commodity currencies lead",
    "lead_risk1":  "-(1-day JPY return minus commodity-FX return): risk-off leads EUR/USD lower",
    "lead_eurx1":  "+1-day EUR-cross factor (EUR vs GBP, JPY, CHF): the euro factor leads",
    "disp_cond5":  "5-day EUR/USD return, followed when cross-sectional dispersion is below its trailing median, faded when above",
    "pca_rev5":    "-(5-day sum of the PCA residual, PC1+PC2 loadings frozen on the training window)",
    "pair_coint":  "-mean z250 of log EURCHF and log EURGBP: pairs reversion against the nearest European pairs",
}
COMBO = "combo_tstat"
BETA_WIN, Z_WIN, DISP_WIN = 250, 250, 500


# ---------------------------------------------------------------- data
def fetch_yahoo_daily(refresh: bool = False) -> dict:
    """Daily bars 2003+ from the Yahoo chart API for the 12 symbols, cached as data/processed/cross/<name>_D1.parquet.
    Existing caches (shared with the feature store) are never overwritten unless refresh=True."""
    import requests
    out = {}
    for name, (sym, _, _) in YAHOO.items():
        p = CROSS / f"{name}_D1.parquet"
        if p.exists() and not refresh:
            out[name] = "cached"
            continue
        status = "failed"
        for host in ("query2", "query1"):
            try:
                r = requests.get(f"https://{host}.finance.yahoo.com/v8/finance/chart/{sym}",
                                 params={"period1": 1041379200, "period2": int(time.time()), "interval": "1d"},
                                 headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
                if r.status_code != 200:
                    time.sleep(2)
                    continue
                d = r.json()["chart"]["result"][0]
                q = d["indicators"]["quote"][0]
                df = pd.DataFrame({k: q[k] for k in ("open", "high", "low", "close")},
                                  index=pd.to_datetime(d["timestamp"], unit="s", utc=True)).dropna()
                df["volume"] = 0.0
                df.index.name = "time"
                df.to_parquet(p)
                status = f"fetched {len(df)}"
                break
            except Exception as e:  # noqa: BLE001
                status = f"failed: {e}"
                time.sleep(2)
        out[name] = status
        time.sleep(1)
    return out


def load_h10() -> pd.DataFrame:
    """H.10 noon New York rates as log(USD per unit of currency) for EUR and the 8 basket currencies, 2002+.
    Source: datahub.io `exchange-rates` daily file (every rate is foreign units per USD). Cached."""
    if H10_CACHE.exists():
        return pd.read_parquet(H10_CACHE)
    if RAW_H10.exists():
        raw = pd.read_csv(RAW_H10)
    else:
        import io
        import requests
        raw = pd.read_csv(io.StringIO(requests.get(H10_URL, timeout=60).text))
    raw.columns = [c.strip() for c in raw.columns]
    w = raw.pivot(index="Date", columns="Country", values="Exchange rate")
    w.index = pd.to_datetime(w.index)
    w = w[[H10_COUNTRY[k] for k in H10_COUNTRY]].rename(columns={v: k for k, v in H10_COUNTRY.items()})
    w = -np.log(w.astype(float).loc["2002":].dropna(how="any"))       # foreign per USD -> log USD per foreign
    w.index.name = "date"
    w.to_parquet(H10_CACHE)
    return w


def eur_noon_from_h1() -> pd.Series:
    """Our EUR/USD at 12:00 New York: open of the hourly bar starting at 12:00 NY local time, indexed by NY date."""
    h1 = pd.read_parquet(H1, columns=["open"]).loc["2002":]
    ny = h1.index.tz_convert("America/New_York")
    m = ny.hour == 12
    s = pd.Series(h1["open"].values[m], index=pd.DatetimeIndex(ny[m].tz_localize(None).normalize()))
    return s[~s.index.duplicated()].sort_index()


def _zprev(x: pd.Series, n: int) -> pd.Series:
    """z-score of x_t against the mean / sd of the PREVIOUS n observations (t-n..t-1)."""
    mu = x.rolling(n, min_periods=n).mean().shift(1)
    sd = x.rolling(n, min_periods=n).std().shift(1)
    return (x - mu) / sd


def _winsor(x, n: int = 250, k: float = 6.0):
    """Clip each observation at +-k standard deviations of the PREVIOUS n observations (point-in-time)."""
    sd = x.rolling(n, min_periods=60).std().shift(1)
    return x.clip(lower=-k * sd, upper=k * sd).where(sd.notna(), x)


def _rolling_resid(y: np.ndarray, X: np.ndarray, win: int) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Residual and fitted basket component of y_t using OLS betas (with intercept) fitted on rows t-win..t-1."""
    n, k = X.shape
    e = np.full(n, np.nan)
    d = np.full(n, np.nan)
    B = np.full((n, k), np.nan)
    Xc = np.column_stack([np.ones(n), X])
    for t in range(win, n):
        a, b = Xc[t - win:t], y[t - win:t]
        if np.isnan(a).any() or np.isnan(b).any() or np.isnan(X[t]).any() or np.isnan(y[t]):
            continue
        beta = np.linalg.lstsq(a, b, rcond=None)[0]
        d[t] = X[t] @ beta[1:]
        e[t] = y[t] - d[t]
        B[t] = beta[1:]
    return e, d, B


def _pca_resid(R: pd.DataFrame, years=range(2010, 2027)) -> pd.Series:
    """EUR residual after PC1 + PC2 of the 8 non-EUR returns; PCs and EUR loadings fitted on dates < Y-01-01 only."""
    e = pd.Series(np.nan, index=R.index)
    first = True
    for Y in years:
        tr = R[R.index < pd.Timestamp(f"{Y}-01-01")].dropna()
        if len(tr) < 500:
            continue
        mu = tr[BASKET].mean().values
        sd = tr[BASKET].std().values
        Zt = (tr[BASKET].values - mu) / sd
        _, _, Vt = np.linalg.svd(Zt, full_matrices=False)
        V = Vt[:2].T                                                   # loadings of PC1, PC2
        F = np.column_stack([np.ones(len(tr)), Zt @ V])
        b = np.linalg.lstsq(F, tr["eur"].values, rcond=None)[0]
        mask = (R.index.year == Y) | ((R.index.year < Y) if first else False)
        cur = R[mask]
        Fc = np.column_stack([np.ones(len(cur)), ((cur[BASKET].values - mu) / sd) @ V])
        e.loc[cur.index] = cur["eur"].values - Fc @ b
        first = False
    return _winsor(e)


def build_noon_panel(save: bool = True) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Signals on the H10 date grid (prior-ORIENTED: positive = long EUR/USD) and the decomposition diagnostics."""
    L = load_h10().copy()
    noon = np.log(eur_noon_from_h1()).reindex(L.index)                 # verification only
    R = _winsor(L[["eur"] + BASKET].diff() * 1e4)                      # bp, USD per unit of currency
    e, d, B = _rolling_resid(R["eur"].values, R[BASKET].values, BETA_WIN)
    e = _winsor(pd.Series(e, index=R.index))
    d = pd.Series(d, index=R.index)
    d = R["eur"] - e                                                   # basket component consistent with the winsorised residual
    S = pd.DataFrame(index=R.index)
    S["res_rev5"] = -e.rolling(5).sum()
    S["res_rev20"] = -e.rolling(20).sum()
    S["res_coint"] = -_zprev(e.cumsum(), Z_WIN)
    S["usd_trend20"] = d.rolling(20).sum()
    S["lead_usd1"] = d
    comm = R[["aud", "cad", "nzd"]].mean(axis=1)
    S["lead_comm1"] = comm
    S["lead_risk1"] = -(R["jpy"] - comm)
    S["lead_eurx1"] = R["eur"] - R[["gbp", "jpy", "chf"]].mean(axis=1)
    r5 = R.rolling(5).sum()
    disp5 = r5.std(axis=1)
    med = disp5.rolling(DISP_WIN, min_periods=DISP_WIN).median().shift(1)
    S["disp_cond5"] = r5["eur"] * np.sign(med - disp5)
    e_pca = _pca_resid(R)
    S["pca_rev5"] = -e_pca.rolling(5).sum()
    S["pair_coint"] = -0.5 * (_zprev(L["eur"] - L["chf"], Z_WIN).clip(-4, 4) + _zprev(L["eur"] - L["gbp"], Z_WIN).clip(-4, 4))
    diag = pd.DataFrame({"r_eur": R["eur"], "resid": e, "basket": d, "resid_pca": e_pca, "disp5": disp5,
                         "eur_noon_minus_h10_pips": (np.exp(noon) - np.exp(L["eur"])) * 1e4})
    for j, c in enumerate(BASKET):
        diag[f"beta_{c}"] = B[:, j]
    if save:
        S.join(diag).to_parquet(PANEL_CACHE)
    return S[list(SIGNALS)], diag


def align_to_sessions(S: pd.DataFrame, df: pd.DataFrame, shift_obs: int = 0, lag_days: int = 0) -> pd.DataFrame:
    """Value of each noon signal usable at each session close. The session closes at 17:00 NY on NY date D and takes
    the last H10 date <= D - lag_days (noon < 17:00, so lag_days=0 is already strictly in the past), then moves
    `shift_obs` rows along the H10 grid (+1 = the NEXT noon: look-ahead probe only)."""
    D = pd.DatetimeIndex(df["close_time"].dt.tz_convert("America/New_York").dt.tz_localize(None).dt.normalize())
    pos = np.searchsorted(S.index.values, (D - pd.Timedelta(days=lag_days)).values, side="right") - 1 + shift_obs
    ok = (pos >= 0) & (pos < len(S))
    out = pd.DataFrame(np.nan, index=df.index, columns=S.columns)
    out.iloc[np.where(ok)[0]] = S.values[pos[ok]]
    return out


def load_frame(shift_obs: int = 0, lag_days: int = 0) -> pd.DataFrame:
    df = pd.read_parquet(FEATURES, columns=["fwd_1d", "fwd_5d", "rv_21d_bp", "close", "close_time", "label_end_1d"])
    S, _ = build_noon_panel(save=(shift_obs == 0 and lag_days == 0))
    A = align_to_sessions(S, df, shift_obs, lag_days)
    return pd.concat([A, df], axis=1)


# ---------------------------------------------------------------- walk-forward pieces
def make_single(sig: str):
    def fit(train: pd.DataFrame):
        x = train[sig].dropna()
        sd = float(x.std()) or 1.0
        return {"sd": sd, "thr": float((x / sd).abs().median()), "target_vol": float(train["rv_21d_bp"].median())}

    def predict(m, test: pd.DataFrame) -> pd.Series:
        z = (test[sig] / m["sd"]).fillna(0.0)
        pos = np.sign(z).where(z.abs() > m["thr"], 0.0)
        return to_positions(pos, "linear", threshold=1.0, vol=test["rv_21d_bp"], target_vol_bp=m["target_vol"])
    return fit, predict


def _Z(S: pd.DataFrame, sd: pd.Series) -> pd.DataFrame:
    return ((S / sd).clip(-2, 2) / 2).fillna(0.0)


def make_combo(signals: list[str], weight_log: dict | None = None):
    def fit(train: pd.DataFrame):
        sd = train[signals].std().replace(0, 1.0)
        Z = _Z(train[signals], sd)
        y = train["fwd_1d"]
        ok = y.notna() & train[signals].notna().all(axis=1)
        w = _weights(Z[ok], y[ok], "tstat")
        score = Z[ok].values @ w
        m = {"sd": sd, "w": w, "thr": float(np.median(np.abs(score))), "target_vol": float(train["rv_21d_bp"].median())}
        if weight_log is not None:
            weight_log[train.index.max().year + 1] = pd.Series(w, index=signals)
        return m

    def predict(m, test: pd.DataFrame) -> pd.Series:
        score = pd.Series(_Z(test[signals], m["sd"]).values @ m["w"], index=test.index)
        pos = np.sign(score).where(score.abs() > m["thr"], 0.0)
        return to_positions(pos, "linear", threshold=1.0, vol=test["rv_21d_bp"], target_vol_bp=m["target_vol"])
    return fit, predict


def run_variant(D: pd.DataFrame, name: str, cost_pips: float, weight_log: dict | None = None):
    fit, predict = make_combo(list(SIGNALS), weight_log) if name == COMBO else make_single(name)
    pos = walk_forward(D, fit, predict, label_end=D["label_end_1d"], verbose=False).fillna(0.0)
    return pos


def table(pos: pd.Series, D: pd.DataFrame, cost_pips: float, name: str, kind: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    pnl = pnl_from_positions(pos, D["fwd_1d"], D["close"], cost_pips=cost_pips)
    pnl = pnl[pnl.index.year >= 2010]
    t = report(pnl, periods_per_year=252, name=ARM, n_arms=N_VARIANTS)
    t.insert(1, "variant", name)
    t["kind"] = kind
    t["cost_pips"] = cost_pips
    t["final"] = False
    return pnl, t


def hit_rates(pnl: pd.DataFrame, fwd: pd.Series) -> pd.DataFrame:
    """Share of active decisions (pos != 0, label known) with positive net P&L and with the correct sign before costs."""
    rows = []
    f = fwd.reindex(pnl.index)
    for label, a, b in (("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026), ("2023-2026", 2023, 2026)):
        m = (pnl.index.year >= a) & (pnl.index.year <= b) & (pnl["pos"] != 0) & f.notna()
        x = pnl[m]
        g = (np.sign(x["pos"]) * f[m])
        rows.append({"period": label, "n_decisions": int(m.sum()), "hit_net": float((x["net_bp"] > 0).mean()) if len(x) else np.nan,
                     "hit_sign_gross": float((g > 0).mean()) if len(x) else np.nan,
                     "base_rate_up": float((f[(pnl.index.year >= a) & (pnl.index.year <= b)] > 0).mean())})
    return pd.DataFrame(rows)


def _nw_t(x: pd.Series, y: pd.Series, lags: int) -> tuple[float, float, int]:
    """Correlation of x with y and the Newey-West t-stat of the OLS slope (Bartlett kernel, `lags` lags)."""
    ok = x.notna() & y.notna()
    x, y = x[ok].values, y[ok].values
    n = len(x)
    if n < 50 or x.std() == 0:
        return np.nan, np.nan, n
    xc, yc = x - x.mean(), y - y.mean()
    b = (xc @ yc) / (xc @ xc)
    u = xc * (yc - b * xc)
    s = u @ u
    for L in range(1, lags + 1):
        s += 2 * (1 - L / (lags + 1)) * (u[L:] @ u[:-L])
    return float(np.corrcoef(x, y)[0, 1]), float(b / (np.sqrt(s) / (xc @ xc))), n


def _sr(t: pd.DataFrame, period: str, col: str = "sharpe") -> float:
    return float(t.set_index("period").loc[period, col])


# ---------------------------------------------------------------- entry point
def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Runs the 12 candidates walk-forward, applies the selection rule, writes the deliverables.
    Returns (final OOS positions, report DataFrame)."""
    fetch_yahoo_daily()
    D = load_frame()
    names = list(SIGNALS) + [COMBO]
    rows, store, single = [], {}, []
    wl: dict = {}
    oos = D.index.year >= 2010
    for name in names:
        pos = run_variant(D, name, cost_pips, wl if name == COMBO else None)
        pnl, t = table(pos, D, cost_pips, name, "candidate")
        _, tg = table(pos, D, 0.0, name, "gross")
        pos5 = pos.rolling(5, min_periods=1).mean()
        pnl5, t5 = table(pos5, D, cost_pips, name + "_hold5", "hold5_diagnostic")
        rows += [t, t5]
        store[name] = (pos, pnl, t)
        h = hit_rates(pnl, D["fwd_1d"]).set_index("period")
        rec = {"signal": name, "sr_2010_2015": _sr(t, "2010-2015"), "sr_2010_2026": _sr(t, "2010-2026"), "t_2010_2026": _sr(t, "2010-2026", "t"),
               "sr_2016_2026": _sr(t, "2016-2026"), "t_2016_2026": _sr(t, "2016-2026", "t"), "sr_2023_2026": _sr(t, "2023-2026"),
               "t_2023_2026": _sr(t, "2023-2026", "t"), "gross_sr_2010_2026": _sr(tg, "2010-2026"), "gross_sr_2016_2026": _sr(tg, "2016-2026"),
               "turnover_per_day": float(pnl["turnover"].mean()), "active_frac": _sr(t, "2010-2026", "active_frac"),
               "hit_net_2010_2026": h.loc["2010-2026", "hit_net"], "hit_sign_2010_2026": h.loc["2010-2026", "hit_sign_gross"],
               "hit_sign_2016_2026": h.loc["2016-2026", "hit_sign_gross"], "hit_sign_2023_2026": h.loc["2023-2026", "hit_sign_gross"],
               "hold5_sr_2010_2026": _sr(t5, "2010-2026"), "hold5_sr_2016_2026": _sr(t5, "2016-2026"), "hold5_sr_2023_2026": _sr(t5, "2023-2026"),
               "hold5_gross_sr_2010_2026": _sr(table(pos5, D, 0.0, name, "x")[1], "2010-2026")}
        if name != COMBO:
            c1, t1, n1 = _nw_t(D.loc[oos, name], D.loc[oos, "fwd_1d"], 0)
            c5, t5nw, _ = _nw_t(D.loc[oos, name], D.loc[oos, "fwd_5d"], 4)
            rec.update({"ic_fwd1d": c1, "t_fwd1d": t1, "ic_fwd5d": c5, "nw_t_fwd5d": t5nw, "n_oos": n1})
        single.append(rec)
        if verbose:
            print(f"{name:12s} 10-15 {rec['sr_2010_2015']:+.2f} | 10-26 {rec['sr_2010_2026']:+.2f} (t {rec['t_2010_2026']:+.2f}, gross {rec['gross_sr_2010_2026']:+.2f}) "
                  f"| 16-26 {rec['sr_2016_2026']:+.2f} | 23-26 {rec['sr_2023_2026']:+.2f} | hit {rec['hit_sign_2010_2026']:.3f} | hold5 {rec['hold5_sr_2010_2026']:+.2f}/{rec['hold5_sr_2016_2026']:+.2f}/{rec['hold5_sr_2023_2026']:+.2f}", flush=True)
    sel = {n: _sr(store[n][2], "2010-2015") for n in names}
    final = max(sel, key=sel.get)
    if verbose:
        print(f"FINAL by rule (best 2010-2015 net Sharpe at {cost_pips} pips): {final} ({sel[final]:+.2f})", flush=True)
    for t in rows:
        if t["variant"].iloc[0] == final:
            t["final"] = True
    pos, pnl, _ = store[final]
    _, t06 = table(pos, D, 0.6, final + "_cost0.6", "cost_sensitivity")
    rows.append(t06)
    rep = pd.concat(rows, ignore_index=True)
    out = pd.DataFrame({"pos": pos, "fwd_bp": D["fwd_1d"], "net_bp": pnl["net_bp"].reindex(pos.index)})
    out = out[out.index.year >= 2010]
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        out.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        pd.DataFrame(single).to_csv(RES / f"{ARM}_single_signals.csv", index=False)
        W = pd.DataFrame(wl).T
        W.index.name = "test_year"
        W.to_csv(RES / f"{ARM}_weights.csv")
        hit_rates(pnl, D["fwd_1d"]).assign(variant=final).to_csv(RES / f"{ARM}_hit_rates.csv", index=False)
        pd.DataFrame({n: store[n][1]["net_bp"] for n in names}).to_parquet(RES / f"{ARM}_all_net_bp.parquet")
    return out["pos"], rep


# ---------------------------------------------------------------- leak checks, incremental test, data checks
def leak_checks(final: str, cost_pips: float = 1.2, seed: int = 0) -> pd.DataFrame:
    """(1) shuffled labels, (2) noon panel one calendar day late (feature-store convention) and one extra session late,
    (2b) look-ahead probe: the NEXT H10 noon (19 h inside the label), (3) signal/label correlations."""
    D = load_frame()
    names = list(SIGNALS) + [COMBO]
    rows = []

    def add(Dx, check, which):
        for n in which:
            pos = run_variant(Dx, n, cost_pips)
            _, t = table(pos, Dx, cost_pips, n, check)
            a = t.set_index("period")
            rows.append({"check": check, "variant": n, **{f"sr_{p.replace('-', '_')}": float(a.loc[p, "sharpe"]) for p in ("2010-2026", "2016-2026", "2023-2026")},
                         "t_2010_2026": float(a.loc["2010-2026", "t"])})
    add(D, "baseline", names)
    rng = np.random.default_rng(seed)
    Ds = D.copy()
    Ds["fwd_1d"] = rng.permutation(D["fwd_1d"].values)
    add(Ds, "shuffled_labels", sorted({final, COMBO}))
    add(load_frame(lag_days=1), "h10_lag_one_calendar_day", names)
    Dl = D.copy()
    Dl[list(SIGNALS)] = D[list(SIGNALS)].shift(1)
    add(Dl, "features_shift_plus1_session", names)
    add(load_frame(shift_obs=1), "LOOKAHEAD_next_h10_noon", names)
    out = pd.DataFrame(rows)
    c = D[list(SIGNALS)].corrwith(D["fwd_1d"])
    cc = pd.DataFrame({"check": "signal_label_corr", "variant": c.index, "corr_with_fwd_1d": c.values})
    return pd.concat([out, cc], ignore_index=True)


def incremental() -> tuple[pd.DataFrame, pd.DataFrame]:
    from eurusd.arms.meta import combine, report_combo, load_arm_daily
    base = ["weak_signals", "regime_trend"]
    p2, _ = combine(base, "EW")
    p3, w3 = combine(base + [ARM], "EW")
    t2 = report_combo(p2, "EW_2way", 2).set_index("period")
    t3 = report_combo(p3, "EW_3way", 3).set_index("period")
    per = ["2010-2026", "2013-2026", "2016-2026", "2023-2026"]
    inc = pd.DataFrame({"sr_2way": t2.loc[per, "sharpe"], "t_2way": t2.loc[per, "t"], "sr_3way": t3.loc[per, "sharpe"], "t_3way": t3.loc[per, "t"]})
    inc["d_sr"] = inc["sr_3way"] - inc["sr_2way"]
    inc["years_arm_in_3way"] = float(w3[ARM].gt(0).sum()) if ARM in w3 else 0.0
    s = pd.DataFrame({a: load_arm_daily(a) for a in base + [ARM]}).fillna(0.0)
    s = s[s.index.year >= 2010]
    corr = pd.concat({"2010-2026": s.corr()[ARM], "2016-2026": s[s.index.year >= 2016].corr()[ARM]}, axis=1)
    return inc.reset_index(), corr


def data_checks() -> dict[str, pd.DataFrame]:
    """Timing and quality evidence (no labels involved): H10 EUR vs our hourly bars by NY hour; Yahoo EURUSD=X close
    vs our price at the start / end of the London day by era; each Yahoo pair vs H10."""
    h1 = pd.read_parquet(H1).loc["2003":]
    ny = h1.index.tz_convert("America/New_York")
    Lh = load_h10().loc["2003":]
    h10e = np.exp(Lh["eur"])
    a_rows = []
    for h in range(8, 18):
        m = ny.hour == h
        s = pd.Series(h1["open"].values[m], index=pd.DatetimeIndex(ny[m].tz_localize(None).normalize()))
        z = pd.concat([h10e.rename("h10"), s[~s.index.duplicated()].rename("h1")], axis=1).dropna()
        dd = (z["h10"] - z["h1"]).abs() * 1e4
        a_rows.append({"ny_hour_bar_open": h, "n": len(z), "median_abs_diff_pips": dd.median(), "p90_abs_diff_pips": dd.quantile(0.9),
                       "daily_return_corr": float(np.log(z["h10"]).diff().corr(np.log(z["h1"]).diff()))})
    A = pd.DataFrame(a_rows)

    def ld(name, col="close"):
        y = pd.read_parquet(CROSS / f"{name}_D1.parquet") if name != "eurusd" else pd.read_parquet(ROOT / "data/processed/yahoo_EURUSD_D1.parquet")
        s = pd.Series(y[col].values, index=y.index.tz_convert("Europe/London").tz_localize(None).normalize())
        return s[~s.index.duplicated(keep="last")].sort_index()
    yd = ld("eurusd")
    hc = h1["close"].copy()
    hc.index = hc.index + pd.Timedelta(hours=1)
    hc = hc[~hc.index.duplicated()]
    base = yd.index.tz_localize("Europe/London").tz_convert("UTC")
    eras = (("2003", "2009"), ("2011", "2015"), ("2016", "2026"))
    b_rows = []
    for off in (-24, 0, 12, 21, 24, 48):
        tt = base + pd.Timedelta(hours=off)
        p = hc.reindex(hc.index.union(tt)).sort_index().ffill().reindex(tt).values
        dd = pd.Series(np.abs(yd.values - p) * 1e4, index=yd.index)
        b_rows.append({"hours_after_00:00_London_of_stamp_date": off, **{f"median_abs_diff_pips_{a}_{b}": dd.loc[a:b].median() for a, b in eras}})
    B = pd.DataFrame(b_rows)
    c_rows = []
    for name, (sym, ccy, sg) in YAHOO.items():
        if ccy is None or not (CROSS / f"{name}_D1.parquet").exists():
            continue
        s = np.log(ld(name)) * (-sg)                                    # log USD per unit of currency
        z = pd.concat([s.rename("y"), Lh[ccy].rename("h")], axis=1).dropna()
        ry, rh = z["y"].diff(), z["h"].diff()
        for a, b in eras:
            c_rows.append({"pair": sym, "era": f"{a}-{b}", "n": int(ry.loc[a:b].notna().sum()), "first": str(z.index[0].date()),
                           "corr_h10_prev_day": ry.loc[a:b].corr(rh.shift(1).loc[a:b]), "corr_h10_same_day": ry.loc[a:b].corr(rh.loc[a:b]),
                           "corr_h10_next_day": ry.loc[a:b].corr(rh.shift(-1).loc[a:b]),
                           "corr_5d_returns": z["y"].diff(5).loc[a:b].corr(z["h"].diff(5).loc[a:b]),
                           "n_abs_5d_gap_gt_200bp": int(((z["y"].diff(5) - z["h"].diff(5)).loc[a:b].abs() * 1e4 > 200).sum())})
    C = pd.DataFrame(c_rows)
    # EUR crosses and DXY against their H10 triangular / basket equivalents (5-day returns, timing-robust)
    x_rows = []
    synth = {"eurgbp": Lh["eur"] - Lh["gbp"], "eurjpy": Lh["eur"] - Lh["jpy"], "eurchf": Lh["eur"] - Lh["chf"],
             "dxy": -(0.576 * Lh["eur"] + 0.136 * Lh["jpy"] + 0.119 * Lh["gbp"] + 0.091 * Lh["cad"] + 0.042 * Lh["sek"] + 0.036 * Lh["chf"])}
    for name, sx in synth.items():
        if not (CROSS / f"{name}_D1.parquet").exists():
            continue
        y = pd.read_parquet(CROSS / f"{name}_D1.parquet")
        tz = "America/New_York" if name == "dxy" else "Europe/London"
        s = pd.Series(np.log(y["close"].values), index=y.index.tz_convert(tz).tz_localize(None).normalize())
        z = pd.concat([s[~s.index.duplicated(keep="last")].rename("y"), sx.rename("h")], axis=1).dropna()
        for a, b in eras:
            x_rows.append({"series": YAHOO[name][0], "era": f"{a}-{b}", "corr_5d_returns_vs_h10_synthetic": z["y"].diff(5).loc[a:b].corr(z["h"].diff(5).loc[a:b]),
                           "corr_1d_same_day": z["y"].diff().loc[a:b].corr(z["h"].diff().loc[a:b]),
                           "corr_1d_h10_prev_day": z["y"].diff().loc[a:b].corr(z["h"].diff().shift(1).loc[a:b])})
    return {"h10_vs_h1_by_hour": A, "yahoo_eurusd_close_timing": B, "yahoo_pairs_vs_h10": C, "yahoo_crosses_vs_h10_synthetic": pd.DataFrame(x_rows)}


if __name__ == "__main__":
    cost = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
    pos, rep = run(cost_pips=cost)
    final = rep.loc[rep["final"] & (rep["kind"] == "candidate"), "variant"].iloc[0]
    lc = leak_checks(final, cost_pips=cost)
    lc.to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
    print(lc.round(3).to_string())
    inc, corr = incremental()
    inc.to_csv(RES / f"{ARM}_incremental.csv", index=False)
    corr.to_csv(RES / f"{ARM}_pnl_corr.csv")
    print(inc.round(3).to_string())
    print(corr.round(3).to_string())
    dc = data_checks()
    pd.concat([v.assign(table=k) for k, v in dc.items()], ignore_index=True).to_csv(RES / f"{ARM}_data_checks.csv", index=False)
    for k, v in dc.items():
        print("\n", k, "\n", v.round(3).to_string())
