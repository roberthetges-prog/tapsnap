"""Arm `daily_ml`: supervised learning on the daily feature store (141 leak-free columns).

Idea: let a regularised learner combine the five information groups of the daily store (price/technical,
calendar, event clocks + macro surprises, macro/yield/cross-asset, CFTC positioning) and find out WHICH
groups add out-of-sample predictability, under the fixed walk-forward protocol of `eurusd.wf`.

Models (all single-threaded, every fit well under a second):
* `ridge`  : ridge regression on standardised features (NaN -> 0 after standardisation), alpha chosen by
             time-ordered CV inside the training window.
* `lgbm`   : LightGBM, <= 400 trees, num_leaves 3..8, strong regularisation, 3-config grid chosen by CV.
* `avg`    : simple average of ridge and lgbm after scaling each by the std of its validation predictions.
* `logit`  : logistic regression on sign(fwd_1d) (pred = p_up - 0.5).
* `lgbm_tb`: LightGBM classifier on tb_5d_1atr (+1 vs -1, zeros dropped from training; pred = p_up - 0.5).

Time-ordered CV: for test year Y the training window holds rows whose label is known before Y-01-01.
Its last two calendar years are the validation block; every hyper-parameter is chosen by the Pearson IC of
the model fitted on the earlier years and evaluated on that block. The decision threshold is the q-quantile
of |prediction| on the validation block (training-window term). Vol scaling: position *= min(1, median
training rv_21d_bp / rv_21d_bp).

Holding: 1-day targets -> one decision per session. 5-day targets -> 1/5 position increments: the daily
position is the mean of the last five raw signals (five overlapping tranches), P&L is marked daily on
fwd_1d (sum of five fwd_1d = fwd_5d), so costs are charged on the smoothed position's turnover.

Selection rule (declared before any result was seen): the FINAL variant is the one with the highest
2010-2015 walk-forward net Sharpe at 1.2 pips among all variants run; its full 2010-2026 record is reported.
"""
from __future__ import annotations

import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from eurusd.wf import YEARS, pnl_from_positions, report, walk_forward  # noqa: E402

warnings.filterwarnings("ignore", category=RuntimeWarning)   # all-NaN columns in early windows (e.g. cot_lev_z52 before 2011)
ROOT = Path(__file__).resolve().parents[3]
STORE = ROOT / "data" / "processed" / "features_daily.parquet"
RES = ROOT / "experiments" / "results" / "arms"
ARM = "daily_ml"
N_ARMS = 6
VAL_YEARS = 2
LABEL_COLS = ["fwd_1d", "fwd_2d", "fwd_5d", "fwd_10d", "tb_5d_1atr", "label_end_1d", "label_end_5d", "label_end_10d", "close", "close_time"]

# ------------------------------------------------------------------ feature groups
GROUPS = {
    "price": ["ret_1d", "ret_2d", "ret_3d", "ret_5d", "ret_10d", "ret_21d", "ret_63d", "ret_126d", "ret_252d", "gap_bp", "range_pips",
              "range_rel_adr", "close_in_range", "body_rel", "rv_1d_bp", "rv_5d_bp", "rv_21d_bp", "rv_ratio_5_63", "gk_1d", "atr14_pips",
              "dist_sma20_atr", "dist_sma50_atr", "dist_sma200_atr", "rsi2", "rsi14", "z20", "donch20_pos", "donch55_pos", "broke_prev_high",
              "broke_prev_low", "streak", "abnormal_day", "adx14", "di_diff", "sess_asia_bp", "sess_london_bp", "sess_overlap_bp", "sess_nypm_bp"],
    "calendar": ["dow", "dom", "month", "bd_from_start", "bd_to_end", "is_month_end", "is_quarter_end_month"],
    "events": ["h_to_fomc", "h_since_fomc", "h_to_ecb", "h_since_ecb", "h_to_nfp", "h_since_nfp", "h_to_cpi", "h_since_cpi", "h_to_any_high",
               "n_high_next_24h"] + [f"{p}_{k}" for k in ("nfp", "cpi", "corecpi", "retail", "ism", "gdp", "pce", "claims") for p in ("last_surprise", "h_since_surprise")],
    "macro": ["us2y", "us10y", "ea2y", "ea10y", "spread2y", "spread10y", "us_curve", "ea_curve", "policy_diff"]
             + [f"d_{s}_{k}" for k in (1, 5, 20, 60) for s in ("spread2y", "spread10y", "us2y")]
             + ["fv_resid_z", "vix", "d_vix_5"] + [f"{n}_ret_{k}" for n in ("dxy", "spx", "gold", "oil", "sx5e", "zt") for k in (1, 5, 20)]
             + ["spx_minus_sx5e_20"] + [f"usd_{c}_ret_{k}" for c in ("gbp", "jpy", "chf", "aud", "cad") for k in (5, 20)]
             + ["usd_factor_5", "usd_factor_20", "eur_vs_usd_factor_20"],
    "positioning": ["cot_net_pct", "cot_z52", "cot_d4", "cot_lev_z52"],
}
FEATURE_SETS = {
    "price": ["price"],
    "price_cal_ev": ["price", "calendar", "events"],
    "price_cal_ev_macro": ["price", "calendar", "events", "macro"],
    "all": ["price", "calendar", "events", "macro", "positioning"],
    "macro_pos": ["macro", "positioning"],
}


def feats_of(fset: str) -> list[str]:
    return [c for g in FEATURE_SETS[fset] for c in GROUPS[g]]


# ------------------------------------------------------------------ hyper-parameter grids (fixed before results)
LGB_GRID = [
    dict(num_leaves=4, n_estimators=150, learning_rate=0.03, min_child_samples=200),
    dict(num_leaves=8, n_estimators=300, learning_rate=0.02, min_child_samples=100),
    dict(num_leaves=3, n_estimators=400, learning_rate=0.01, min_child_samples=300),
]
LGB_FIXED = dict(subsample=0.7, subsample_freq=1, colsample_bytree=0.5, reg_lambda=10.0, num_threads=1, verbose=-1, random_state=0)
RIDGE_GRID = [10.0, 100.0, 1000.0, 10000.0]
LOGIT_GRID = [1e-4, 1e-3, 1e-2]


# ------------------------------------------------------------------ component models
class _Ridge:
    def __init__(self, alpha): self.alpha = alpha
    def fit(self, X, y):
        self.mu = np.nanmean(X, axis=0); self.sd = np.nanstd(X, axis=0) + 1e-9
        Z = self._z(X); self.ym = y.mean()
        A = Z.T @ Z + self.alpha * np.eye(Z.shape[1]); self.w = np.linalg.solve(A, Z.T @ (y - self.ym)); return self
    def _z(self, X):
        Z = (X - self.mu) / self.sd; return np.nan_to_num(Z, nan=0.0)
    def predict(self, X): return self._z(X) @ self.w + self.ym
    def importance(self): return np.abs(self.w)


class _Logit:
    def __init__(self, C): self.C = C
    def fit(self, X, y):
        from sklearn.linear_model import LogisticRegression
        self.mu = np.nanmean(X, axis=0); self.sd = np.nanstd(X, axis=0) + 1e-9
        self.m = LogisticRegression(C=self.C, max_iter=500).fit(self._z(X), (y > 0).astype(int)); return self
    def _z(self, X): return np.nan_to_num((X - self.mu) / self.sd, nan=0.0)
    def predict(self, X): return self.m.predict_proba(self._z(X))[:, 1] - 0.5
    def importance(self): return np.abs(self.m.coef_[0])


class _Lgb:
    def __init__(self, cfg, clf=False): self.cfg = cfg; self.clf = clf
    def fit(self, X, y):
        import lightgbm as lgb
        if self.clf:
            self.m = lgb.LGBMClassifier(**self.cfg, **LGB_FIXED).fit(X, (y > 0).astype(int))
        else:
            self.m = lgb.LGBMRegressor(**self.cfg, **LGB_FIXED).fit(X, y)
        return self
    def predict(self, X): return self.m.predict_proba(X)[:, 1] - 0.5 if self.clf else self.m.predict(X)
    def importance(self): return self.m.booster_.feature_importance("gain")


def _candidates(kind: str):
    if kind == "ridge": return [("ridge", a, lambda a=a: _Ridge(a)) for a in RIDGE_GRID]
    if kind == "logit": return [("logit", C, lambda C=C: _Logit(C)) for C in LOGIT_GRID]
    if kind == "lgbm": return [("lgbm", i, lambda c=c: _Lgb(c)) for i, c in enumerate(LGB_GRID)]
    if kind == "lgbm_tb": return [("lgbm_tb", i, lambda c=c: _Lgb(c, clf=True)) for i, c in enumerate(LGB_GRID)]
    raise ValueError(kind)


MODEL_KINDS = {"ridge": ["ridge"], "lgbm": ["lgbm"], "avg": ["ridge", "lgbm"], "logit": ["logit"], "lgbm_tb": ["lgbm_tb"]}


def _ic(a, b):
    ok = ~np.isnan(a) & ~np.isnan(b)
    return float(np.corrcoef(a[ok], b[ok])[0, 1]) if ok.sum() > 30 and a[ok].std() > 0 else 0.0


# ------------------------------------------------------------------ variant spec -> fit/predict closures
def make_fit_predict(model: str, target: str, fset: str, q: float, info: dict):
    feats = feats_of(fset)
    kinds = MODEL_KINDS[model]

    def _rows(df):
        y = df[target].astype(float)
        ok = y.notna()
        if target == "tb_5d_1atr":
            ok &= y != 0
        return df.loc[ok, feats].astype(float).values, y[ok].values, df.index[ok]

    def fit(train: pd.DataFrame):
        X, y, idx = _rows(train)
        yrs = idx.year
        cut = yrs.max() - VAL_YEARS + 1
        tr, va = yrs < cut, yrs >= cut
        comps, scales, val_parts, chosen, imps = [], [], [], {}, {}
        for kind in kinds:
            best = None
            for name, par, mk in _candidates(kind):
                m = mk().fit(X[tr], y[tr]); pv = m.predict(X[va]); ic = _ic(pv, y[va])
                if best is None or ic > best[0]:
                    best = (ic, par, mk, pv)
            ic, par, mk, pv = best
            sc = float(np.std(pv)) + 1e-12
            chosen[kind] = {"param": par, "val_ic": round(ic, 4)}
            scales.append(sc); val_parts.append(pv / sc)
            full = mk().fit(X, y); comps.append(full); imps[kind] = full.importance()
        ens_val = np.mean(val_parts, axis=0)
        thr = float(np.quantile(np.abs(ens_val), q)) if q > 0 else 1e-12
        Y = int(yrs.max()) + 1
        info[Y] = {"thr": thr, "vol_target": float(np.nanmedian(train["rv_21d_bp"])), "chosen": chosen, "imp": imps, "n_train": int(len(y)),
                   "val_ic_ens": round(_ic(ens_val, y[va]), 4)}
        return (comps, scales, thr)

    def predict(model_, test: pd.DataFrame):
        comps, scales, thr = model_
        X = test[feats].astype(float).values
        p = np.mean([c.predict(X) / s for c, s in zip(comps, scales)], axis=0)
        return p / thr            # |pred| > 1  <=>  beyond the training-window quantile

    return fit, predict


def positions_from_pred(pred: pd.Series, df: pd.DataFrame, info: dict, rule: str, vol_scale: bool, hold: int) -> pd.Series:
    if rule == "sign":
        sig = np.sign(pred).where(pred.abs() > 1.0, 0.0)
    elif rule == "linear":
        sig = pred.clip(-1, 1)
    elif rule == "always":                      # trade every day on the sign (no threshold)
        sig = np.sign(pred)
    else:
        raise ValueError(rule)
    sig = sig.fillna(0.0)
    if vol_scale:
        vt = pd.Series(df.index.year, index=df.index).map({Y: v["vol_target"] for Y, v in info.items()})
        sig = sig * (vt / df["rv_21d_bp"].replace(0, np.nan)).clip(upper=1.0).fillna(0.0)
    if hold > 1:
        sig = sig.rolling(hold, min_periods=1).mean()      # 1/hold position increments (overlapping tranches)
    return sig.fillna(0.0)


# ------------------------------------------------------------------ variants (fixed list; count reported)
def _v(name, model, target, fset="all", q=0.7, rule="sign", vol=True):
    return dict(variant=name, model=model, target=target, fset=fset, q=q, rule=rule, vol=vol)


VARIANTS = [
    # A. model / target comparison on the full feature set
    _v("ridge_1d_all", "ridge", "fwd_1d"), _v("lgbm_1d_all", "lgbm", "fwd_1d"), _v("avg_1d_all", "avg", "fwd_1d"),
    _v("logit_sign1d_all", "logit", "fwd_1d"), _v("lgbmtb_5d_all", "lgbm_tb", "tb_5d_1atr"),
    _v("ridge_5d_all", "ridge", "fwd_5d"), _v("lgbm_5d_all", "lgbm", "fwd_5d"), _v("avg_5d_all", "avg", "fwd_5d"),
    # B. decision-rule variants (avg model)
    _v("avg_1d_all_q50", "avg", "fwd_1d", q=0.5), _v("avg_1d_all_q85", "avg", "fwd_1d", q=0.85),
    _v("avg_1d_all_linear", "avg", "fwd_1d", rule="linear"), _v("avg_1d_all_always", "avg", "fwd_1d", rule="always"),
    _v("avg_1d_all_novol", "avg", "fwd_1d", vol=False),
    _v("avg_5d_all_q50", "avg", "fwd_5d", q=0.5), _v("avg_5d_all_linear", "avg", "fwd_5d", rule="linear"),
    # C. feature-group ablations (avg model, 1d and 5d)
    _v("avg_1d_price", "avg", "fwd_1d", fset="price"), _v("avg_1d_price_cal_ev", "avg", "fwd_1d", fset="price_cal_ev"),
    _v("avg_1d_price_cal_ev_macro", "avg", "fwd_1d", fset="price_cal_ev_macro"), _v("avg_1d_macro_pos", "avg", "fwd_1d", fset="macro_pos"),
    _v("avg_5d_price", "avg", "fwd_5d", fset="price"), _v("avg_5d_price_cal_ev", "avg", "fwd_5d", fset="price_cal_ev"),
    _v("avg_5d_price_cal_ev_macro", "avg", "fwd_5d", fset="price_cal_ev_macro"), _v("avg_5d_macro_pos", "avg", "fwd_5d", fset="macro_pos"),
]
SELECTION_PERIOD = "2010-2015"


def load_store() -> pd.DataFrame:
    return pd.read_parquet(STORE)


def run_variant(df: pd.DataFrame, spec: dict, cost_pips: float = 1.2, verbose: bool = False, shuffle_labels: bool = False,
                feature_shift: int = 0, seed: int = 0):
    """Walk-forward one variant. Returns (positions, pnl at cost_pips, info dict, pred).
    shuffle_labels / feature_shift are the leak-check switches (never used for the reported variants)."""
    d = df.copy()
    feats = feats_of(spec["fset"])
    if shuffle_labels:
        rng = np.random.default_rng(seed)
        for col in ("fwd_1d", "fwd_5d", "tb_5d_1atr"):
            v = d[col].values.copy(); rng.shuffle(v); d[col] = v
    if feature_shift:
        d[feats] = d[feats].shift(feature_shift)
    hold = 5 if spec["target"] in ("fwd_5d", "tb_5d_1atr") else 1
    label_end = d["label_end_5d"] if hold == 5 else d["label_end_1d"]
    info = {}
    fit, predict = make_fit_predict(spec["model"], spec["target"], spec["fset"], spec["q"], info)
    pred = walk_forward(d, fit, predict, label_end=label_end, verbose=verbose)
    pos = positions_from_pred(pred, d, info, spec["rule"], spec["vol"], hold)
    pos = pos[pos.index.year >= YEARS[0]]
    pnl = pnl_from_positions(pos, df.loc[pos.index, "fwd_1d"], df.loc[pos.index, "close"], cost_pips=cost_pips)
    return pos, pnl, info, pred


def _tables(pos, df, name, cost_list=(1.2, 0.6)):
    out = []
    for c in cost_list:
        pnl = pnl_from_positions(pos, df.loc[pos.index, "fwd_1d"], df.loc[pos.index, "close"], cost_pips=c)
        t = report(pnl, periods_per_year=252, name=ARM, n_arms=N_ARMS); t.insert(1, "variant", name); t.insert(2, "cost_pips", c)
        out.append(t)
    return pd.concat(out, ignore_index=True)


def _top_features(info: dict, feats: list[str], k: int = 15) -> pd.DataFrame:
    rows = {}
    for Y, v in info.items():
        for kind, imp in v["imp"].items():
            imp = np.asarray(imp, float); imp = imp / (imp.sum() + 1e-12)
            rows.setdefault(kind, []).append(pd.Series(imp, index=feats))
    out = pd.DataFrame({kind: pd.concat(v, axis=1).mean(axis=1) for kind, v in rows.items()})
    out["mean"] = out.mean(axis=1)
    return out.sort_values("mean", ascending=False).head(k)


def run(cost_pips: float = 1.2, variants=None, log=print):
    """Entry point: runs all variants, applies the pre-declared selection rule, writes deliverables.
    Returns (positions Series of the final variant, report DataFrame of all variants)."""
    RES.mkdir(parents=True, exist_ok=True)
    df = load_store()
    variants = variants or VARIANTS
    tables, cache = [], {}
    t0 = time.time()
    for spec in variants:
        t1 = time.time()
        pos, pnl, info, pred = run_variant(df, spec, cost_pips=cost_pips)
        tab = _tables(pos, df, spec["variant"]); tables.append(tab)
        cache[spec["variant"]] = (pos, info, pred)
        sel = tab[(tab.period == SELECTION_PERIOD) & (tab.cost_pips == cost_pips)].sharpe.iloc[0]
        full = tab[(tab.period == "2010-2026") & (tab.cost_pips == cost_pips)].sharpe.iloc[0]
        log(f"[{spec['variant']:28s}] sel({SELECTION_PERIOD}) SR={sel:+.2f}  2010-2026 SR={full:+.2f}  ({time.time() - t1:.0f}s, total {time.time() - t0:.0f}s)")
    rep = pd.concat(tables, ignore_index=True)
    sel = rep[(rep.period == SELECTION_PERIOD) & (rep.cost_pips == cost_pips)].set_index("variant").sharpe
    final = sel.idxmax()
    rep["final"] = rep.variant == final
    rep["n_variants"] = len(variants)
    rep.to_csv(RES / f"{ARM}_report.csv", index=False)
    pos, info, pred = cache[final]
    pnl = pnl_from_positions(pos, df.loc[pos.index, "fwd_1d"], df.loc[pos.index, "close"], cost_pips=cost_pips)
    out = pd.DataFrame({"pos": pos, "fwd_bp": df.loc[pos.index, "fwd_1d"], "net_bp": pnl["net_bp"], "pred": pred.loc[pos.index]})
    out.to_parquet(RES / f"{ARM}_positions.parquet")
    spec = next(v for v in variants if v["variant"] == final)
    meta = {"final": final, "spec": spec, "n_variants": len(variants), "selection_rule": f"max {SELECTION_PERIOD} net Sharpe at {cost_pips} pips",
            "per_year": {str(Y): {k: (v[k] if not isinstance(v[k], np.ndarray) else None) for k in ("thr", "vol_target", "chosen", "n_train", "val_ic_ens")} for Y, v in info.items()}}
    (RES / f"{ARM}_meta.json").write_text(json.dumps(meta, indent=1, default=str))
    log(f"FINAL variant by rule '{meta['selection_rule']}': {final}")
    return pos, rep


def leak_checks(cost_pips: float = 1.2, log=print):
    """(1) shuffled labels, (2a) features lagged one extra session, (2b) features from t+1 (positive control),
    (3) top features. Runs on the final variant recorded in the meta file."""
    df = load_store()
    meta = json.loads((RES / f"{ARM}_meta.json").read_text())
    spec = meta["spec"]
    feats = feats_of(spec["fset"])
    res = {}
    for name, kw in (("baseline", {}), ("shuffled_labels", {"shuffle_labels": True}), ("features_lagged_+1", {"feature_shift": 1}),
                     ("features_from_t+1_(positive_control)", {"feature_shift": -1})):
        t1 = time.time()
        pos, pnl, info, pred = run_variant(df, spec, cost_pips=cost_pips, **kw)
        tab = _tables(pos, df, name, cost_list=(cost_pips,))
        r = tab[tab.period == "2010-2026"].iloc[0]
        res[name] = {"sharpe": round(float(r.sharpe), 2), "t": round(float(r.t), 2), "active_frac": round(float(r.active_frac), 2)}
        if name == "baseline":
            res["top_features"] = _top_features(info, feats)
        log(f"leak check {name:40s} 2010-2026 SR={r.sharpe:+.2f} t={r.t:+.2f} ({time.time() - t1:.0f}s)")
    tf = res.pop("top_features")
    tf.to_csv(RES / f"{ARM}_top_features.csv")
    pd.DataFrame(res).T.to_csv(RES / f"{ARM}_leak_checks.csv")
    return res, tf


if __name__ == "__main__":
    what = sys.argv[1] if len(sys.argv) > 1 else "run"
    if what == "run":
        run()
    elif what == "leaks":
        leak_checks()
    elif what == "all":
        run(); leak_checks()
