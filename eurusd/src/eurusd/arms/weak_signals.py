"""Arm C ("weak_signals"): forecast combination of many weak economic signals for EUR/USD, one decision per
NY-close session, horizon = next session (fwd_1d).

Idea. Round 1 found a dozen effects whose sign is stable but which are individually insignificant. The classic
way to make such single-asset FX edges usable is to combine them: if the signals are weakly correlated, the
Sharpe of the combination grows roughly with sqrt(k). Every signal is expressed as a standardised daily value
(standardisation statistics from the training window only), oriented so that the ECONOMIC PRIOR says
"positive signal -> long EUR/USD next session". The signals are then combined walk-forward with four methods:

  equal  : equal weights, signs fixed by the prior (no data used for the weights at all)
  ridge  : ridge regression of fwd_1d on the signals, alpha = n_train (strong shrinkage, fixed rule)
  nnls   : sign-restricted least squares (weights >= 0 after the prior orientation)
  tstat  : weights proportional to each signal's training-window t-stat, clipped at 0

and two score -> position mappings (training-quantile thresholds, vol scaling by rv_21d_bp):

  linear : pos = clip(score / Q80_train(|score|), -1, 1), 0 inside the training 20% dead zone
  sign   : pos = sign(score) when |score| > training median of |score|, else 0

8 variants in total. SELECTION RULE (declared before any result was looked at): the final variant is the one
with the highest 2010-2015 walk-forward NET Sharpe at 1.2 pips; its full 2010-2026 record is then reported.
A leave-one-out ablation (drop one signal, re-run the final variant walk-forward) tells which signals carry it.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls as _nnls

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.wf import walk_forward, pnl_from_positions, report, to_positions  # noqa: E402

FEATURES = ROOT / "data/processed/features_daily.parquet"
RES = ROOT / "experiments/results/arms"
ARM = "weak_signals"
N_ARMS = 6

# name: (prior sign applied to the raw column, kind, description)
#   kind 'cont'  : scaled by the training-window std (no demeaning: the raw sign is the economic content), clip +-2, /2
#   kind 'level' : demeaned by the training mean and scaled by the training std, clip +-2, /2
#   kind 'bin'   : already in {-1, 0, +1}
SIGNALS = {
    "fomc":   (+1, "bin",   "+1 on the session before a scheduled FOMC statement (h_to_fomc < 30h): FOMC-day long (round-1 H08)"),
    "cot":    (+1, "cont",  "cot_z52, CFTC non-commercial net position z-score: follow the positioning trend (H31)"),
    "spread": (+1, "cont",  "d_spread2y_20, 20-day change of the EA-US 2y spread: long EUR if the spread rose (C10)"),
    "mom63":  (+1, "cont",  "ret_63d, 3-month time-series momentum (H18)"),
    "mom21":  (+1, "cont",  "ret_21d, 1-month time-series momentum (H19)"),
    "fv":     (-1, "cont",  "-fv_resid_z, mean reversion of the 2y-spread fair-value residual (F01)"),
    "gap":    (-1, "bin",   "fade a large weekend gap (|gap| > ATR14/5) on the Monday-session row, i.e. over Tuesday (H15, 2-day hold)"),
    "tom":    (-1, "bin",   "-1 over the turn of the month (bd_to_end <= 1 or bd_from_start <= 3): short EUR/USD T-1 -> T+4 (C04)"),
    "usdmom": (-1, "cont",  "-usd_factor_20, dollar-factor momentum (USD strong vs 5 majors over 20d -> short EUR/USD)"),
    "vix":    (+1, "level", "VIX level (demeaned): round-1 V04 was consistently NEGATIVE for 'long when VIX<20 / short >30', "
                            "so the kept sign is long EUR/USD when VIX is high (contrary to the risk-on textbook)"),
    "eqrel":  (-1, "cont",  "-spx_minus_sx5e_20, US-vs-EA equity relative momentum: US outperformance -> flows to USD (F04 sign)"),
    "mom252": (-1, "cont",  "-ret_252d, 12-month TSMOM expected negative/weak (H17)"),
    "season": (+1, "bin",   "+1 when the next session closes in December, -1 in May (C03)"),
    "dow":    (+1, "bin",   "-1 when the next session closes on Monday, +1 on Friday (Seasonax day-of-week, C01)"),
}
METHODS = ("equal", "ridge", "nnls", "tstat")
MAPPINGS = ("linear", "sign")
Q_HI, Q_DEAD, Q_SIGN = 0.80, 0.20, 0.50


# ---------------------------------------------------------------- signals
def build_raw_signals(df: pd.DataFrame) -> pd.DataFrame:
    """Raw, prior-ORIENTED signals (positive = long EUR/USD under the prior). NaN = signal unavailable (-> 0)."""
    S = pd.DataFrame(index=df.index)
    S["fomc"] = (df["h_to_fomc"] < 30).astype(float)
    S["cot"] = df["cot_z52"]
    S["spread"] = df["d_spread2y_20"]
    S["mom63"] = df["ret_63d"]
    S["mom21"] = df["ret_21d"]
    S["fv"] = -df["fv_resid_z"]
    atr_bp = df["atr14_pips"] / df["close"]                       # 1 pip = 1/close bp
    is_mon = df["dow"] == 0                                        # session closing on Monday (NY date) = the weekend-gap session
    big = df["gap_bp"].abs() > atr_bp.shift(1) / 5
    S["gap"] = np.where(is_mon & big, -np.sign(df["gap_bp"]), 0.0)
    S["tom"] = np.where((df["bd_to_end"] <= 1) | (df["bd_from_start"] <= 3), -1.0, 0.0)
    S["usdmom"] = -df["usd_factor_20"]
    S["vix"] = df["vix"]
    S["eqrel"] = -df["spx_minus_sx5e_20"]
    S["mom252"] = -df["ret_252d"]
    nxt_dow = df["dow"].shift(-1).fillna((df["dow"] + 1) % 5)      # calendar of the next session (deterministic, no leak)
    nxt_month = df["month"].shift(-1).fillna(df["month"])
    S["season"] = np.where(nxt_month == 12, 1.0, np.where(nxt_month == 5, -1.0, 0.0))
    S["dow"] = np.where(nxt_dow == 0, -1.0, np.where(nxt_dow == 4, 1.0, 0.0))
    return S[list(SIGNALS)]


def _scaler_fit(S: pd.DataFrame) -> dict:
    st = {}
    for k, (_, kind, _) in SIGNALS.items():
        if k not in S.columns:
            continue
        x = S[k].dropna()
        if kind == "cont":
            st[k] = (0.0, float(x.std()) or 1.0)
        elif kind == "level":
            st[k] = (float(x.mean()), float(x.std()) or 1.0)
        else:
            st[k] = (0.0, 1.0)
    return st


def _scaler_apply(S: pd.DataFrame, st: dict) -> pd.DataFrame:
    out = pd.DataFrame(index=S.index)
    for k, (mu, sd) in st.items():
        kind = SIGNALS[k][1]
        z = S[k] if kind == "bin" else ((S[k] - mu) / sd).clip(-2, 2) / 2
        out[k] = z.fillna(0.0)
    return out


# ---------------------------------------------------------------- combination
def _weights(Z: pd.DataFrame, y: pd.Series, method: str) -> np.ndarray:
    X = Z.values
    yy = y.values
    k = X.shape[1]
    if method == "equal":
        w = np.ones(k)
    elif method == "ridge":
        n = len(yy)
        Xc = X - X.mean(0)
        yc = yy - yy.mean()
        w = np.linalg.solve(Xc.T @ Xc + n * np.eye(k), Xc.T @ yc)      # alpha = n_train: strong, fixed shrinkage
    elif method == "nnls":
        Xc = X - X.mean(0)
        yc = yy - yy.mean()
        w, _ = _nnls(Xc, yc)
        if w.sum() <= 0:
            w = np.ones(k)
    elif method == "tstat":
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
    else:
        raise ValueError(method)
    return w / np.abs(w).sum()


def make_fit_predict(method: str, mapping: str, signals: list[str], weight_log: dict | None = None):
    def fit(train: pd.DataFrame):
        S = train[signals]
        st = _scaler_fit(S)
        Z = _scaler_apply(S, st)
        y = train["fwd_1d"]
        ok = y.notna()
        w = _weights(Z[ok], y[ok], method)
        score = Z.values @ w
        a = np.abs(score)
        thr = {"hi": float(np.quantile(a, Q_HI)), "dead": float(np.quantile(a, Q_DEAD)), "med": float(np.quantile(a, Q_SIGN))}
        target_vol = float(train["rv_21d_bp"].median())
        m = {"st": st, "w": w, "thr": thr, "target_vol": target_vol}
        if weight_log is not None:
            weight_log[train.index.max().year + 1] = pd.Series(w, index=signals)
        return m

    def predict(m, test: pd.DataFrame) -> pd.Series:
        Z = _scaler_apply(test[signals], m["st"])
        score = pd.Series(Z.values @ m["w"], index=test.index)
        thr = m["thr"]
        if mapping == "linear":
            pos = (score / max(thr["hi"], 1e-9)).clip(-1, 1).where(score.abs() > thr["dead"], 0.0)
        else:
            pos = np.sign(score).where(score.abs() > thr["med"], 0.0)
        pos = to_positions(pos, "linear", threshold=1.0, vol=test["rv_21d_bp"], target_vol_bp=m["target_vol"])
        return pos
    return fit, predict


def load_frame() -> pd.DataFrame:
    df = pd.read_parquet(FEATURES)
    S = build_raw_signals(df)
    D = pd.concat([S, df[["fwd_1d", "rv_21d_bp", "close", "label_end_1d"]]], axis=1)
    return D


def run_variant(D: pd.DataFrame, method: str, mapping: str, signals: list[str], cost_pips: float, name: str,
                weight_log: dict | None = None, verbose: bool = False):
    fit, predict = make_fit_predict(method, mapping, signals, weight_log)
    pos = walk_forward(D, fit, predict, label_end=D["label_end_1d"], verbose=verbose)
    pos = pos.fillna(0.0)
    pnl = pnl_from_positions(pos, D["fwd_1d"], D["close"], cost_pips=cost_pips)
    pnl = pnl[pos.index.year >= 2010]
    tbl = report(pnl, periods_per_year=252, name=ARM, n_arms=N_ARMS)
    tbl.insert(1, "variant", name)
    return pos, pnl, tbl


def _agg_row(tbl: pd.DataFrame, period: str) -> pd.Series:
    return tbl.set_index("period").loc[period]


# ---------------------------------------------------------------- entry point
def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = False):
    """Runs the 8 combination variants walk-forward, applies the selection rule, runs the leave-one-out ablation
    of the final variant and writes the deliverables. Returns (final OOS positions, report DataFrame)."""
    D = load_frame()
    signals = list(SIGNALS)
    rows, store = [], {}
    for method in METHODS:
        for mapping in MAPPINGS:
            name = f"{method}_{mapping}"
            wl = {}
            pos, pnl, tbl = run_variant(D, method, mapping, signals, cost_pips, name, weight_log=wl, verbose=verbose)
            tbl["final"] = False
            tbl["kind"] = "variant"
            rows.append(tbl)
            store[name] = (pos, pnl, tbl, wl)
            r = tbl.set_index("period")
            print(f"{name:14s} 2010-2015 SR {r.loc['2010-2015','sharpe']:+.2f} | 2010-2026 SR {r.loc['2010-2026','sharpe']:+.2f} "
                  f"t {r.loc['2010-2026','t']:+.2f} | 2016-2026 SR {r.loc['2016-2026','sharpe']:+.2f} | 2023-2026 SR {r.loc['2023-2026','sharpe']:+.2f}", flush=True)
    # selection rule: best 2010-2015 net Sharpe at the headline cost
    sel = {n: float(_agg_row(t, "2010-2015")["sharpe"]) for n, (_, _, t, _) in store.items()}
    final = max(sel, key=sel.get)
    print(f"FINAL variant by rule (best 2010-2015 net Sharpe): {final}  ({sel[final]:+.2f})", flush=True)
    for t in rows:
        if t["variant"].iloc[0] == final:
            t["final"] = True
    fmethod, fmapping = final.split("_")
    # leave-one-out ablation of the final variant
    for s in signals:
        keep = [x for x in signals if x != s]
        name = f"{final}_drop_{s}"
        _, _, tbl = run_variant(D, fmethod, fmapping, keep, cost_pips, name)
        tbl["final"] = False
        tbl["kind"] = "leave_one_out"
        rows.append(tbl)
        r = tbl.set_index("period")
        print(f"  drop {s:7s} 2010-2026 SR {r.loc['2010-2026','sharpe']:+.2f} | 2016-2026 SR {r.loc['2016-2026','sharpe']:+.2f} | 2023-2026 SR {r.loc['2023-2026','sharpe']:+.2f}", flush=True)
    # cost sensitivity of the final variant
    _, pnl06, tbl06 = run_variant(D, fmethod, fmapping, signals, 0.6, f"{final}_cost0.6")
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
    return out["pos"], rep


# ---------------------------------------------------------------- leak checks
def leak_checks(final: str, cost_pips: float = 1.2, seed: int = 0) -> pd.DataFrame:
    """(1) shuffled labels; (2) features lagged one extra session (X.shift(1)); (3) full-sample correlation of each
    standardised signal with the label (a label in disguise would show |corr| >> 0.05)."""
    D = load_frame()
    signals = list(SIGNALS)
    method, mapping = final.split("_")
    out = []
    # (1) shuffle labels (same permutation applied to fwd_1d everywhere: fit AND evaluation see shuffled labels)
    rng = np.random.default_rng(seed)
    Ds = D.copy()
    Ds["fwd_1d"] = rng.permutation(D["fwd_1d"].values)
    _, _, t = run_variant(Ds, method, mapping, signals, cost_pips, "shuffled_labels")
    out.append(t.assign(check="shuffled_labels"))
    # (2) features lagged by one extra session
    Dl = D.copy()
    Dl[signals] = D[signals].shift(1)
    _, _, t = run_variant(Dl, method, mapping, signals, cost_pips, "features_shift_plus1")
    out.append(t.assign(check="features_shift_plus1"))
    # (2b) look-ahead control: features shifted back by one session (uses the next session's signals); this must
    # NOT be read as a result, it only shows the harness would have exposed a look-ahead
    Da = D.copy()
    Da[signals] = D[signals].shift(-1)
    _, _, t = run_variant(Da, method, mapping, signals, cost_pips, "features_shift_minus1_lookahead_control")
    out.append(t.assign(check="features_shift_minus1_lookahead_control"))
    # (3) correlation of each signal with the label on the full sample
    Z = _scaler_apply(D[signals], _scaler_fit(D[signals]))
    c = Z.corrwith(D["fwd_1d"])
    corr = pd.DataFrame({"period": c.index, "corr_with_fwd_1d": c.values})
    corr["check"] = "signal_label_corr"
    return pd.concat(out + [corr], ignore_index=True)


if __name__ == "__main__":
    cost = float(sys.argv[1]) if len(sys.argv) > 1 else 1.2
    pos, rep = run(cost_pips=cost, verbose=False)
    final = rep.loc[rep["final"], "variant"].iloc[0]
    lc = leak_checks(final, cost_pips=cost)
    lc.to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
    for chk in ("shuffled_labels", "features_shift_plus1", "features_shift_minus1_lookahead_control"):
        r = lc[lc.check == chk].set_index("period")
        print(f"leak check {chk:40s} 2010-2026 SR {r.loc['2010-2026','sharpe']:+.2f} t {r.loc['2010-2026','t']:+.2f} | "
              f"2016-2026 SR {r.loc['2016-2026','sharpe']:+.2f} | 2023-2026 SR {r.loc['2023-2026','sharpe']:+.2f}")
    print(lc[lc.check == "signal_label_corr"][["period", "corr_with_fwd_1d"]].to_string(index=False))
