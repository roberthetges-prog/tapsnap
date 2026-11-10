"""Arm D "regime_trend": vol-scaled multi-horizon trend ensembles, HMM regimes and regime-conditional rules.

Everything runs through the fixed walk-forward harness (`eurusd.wf`): for test year Y every scale, threshold,
regime model and regime->action mapping is fitted on rows whose 1-day label is known before Y-01-01.

Building blocks (all causal features of the daily store, see `_add_features`):
* TSMOM ensemble: lookbacks 21/63/126/252 sessions (1/3/6/12 months). "sign" = mean of sign(ret_k);
  "scaled" = mean of clip(t_k / q_k, -1, 1) with t_k = ret_k / (rv_21d_bp * sqrt(k)) and q_k = the training-window
  80th percentile of |t_k|.
* Baz et al. (2015) EWMA crossover: speeds (8,24), (16,48), (32,96); x = EWMA_S - EWMA_L of the close,
  y = x / std_63(close), z = y / std_252(y), response R(z) = z exp(-z^2/4) / 0.89; signal = mean of the three R(z).
* "trend_combo" = mean of TSMOM-scaled and Baz.
* Mean reversion composite ("mr"): mean of -(rsi2-50)/s1, -z20/s2, -fv_resid_z/s3 (s = training std), clipped.
* Round-1 components: FOMC-eve long (session whose forward day contains a scheduled statement), COT trend
  sign(cot_z52), spread momentum sign(d_spread2y_20).
* Vol scaling: position *= clip(target / rv_21d_bp, 0, 1.5), target = training median of rv_21d_bp.
* Moreira-Muir overlay ("mm"): position *= clip(c / rv_21d_bp^2, 0, 2), c = training median of rv_21d_bp^2.
* Regime model: Gaussian HMM (hmmlearn, diagonal covariances) on standardized (log rv_21d_bp, |ret_21d|, adx14,
  log vix), K = 3 or 4 states, fitted on the training window (4 EM restarts; keep the best training likelihood among
  restarts whose states are all persistent, self-transition >= 0.8); state probabilities for every date are obtained by
  CAUSAL forward filtering (never Viterbi / smoothing) with the training-window parameters.
  Mapping state -> action chosen on the training window only:
    "desc": the state with the highest mean stress score (mean z of log rv, log vix) is "stressed" -> flat;
            among the others, states with trendiness (mean z of adx14, |ret_21d|) above the average of the
            non-stressed states -> trend signal, the rest -> mean-reversion signal.
    "perf": per state (hard, argmax filtered prob) the training net Sharpe of trend and of MR; take the better one
            if its Sharpe > 0, else flat.
  Soft application: pos = sum_s P(s|t) * action_s(t); "hard" variant uses argmax.
  Round-1 components conditioned on regimes: component active in state s iff its training net Sharpe in s > 0.

SELECTION RULE (declared before any result was looked at): the final variant is the candidate (every variant
except the leave-one-out diagnostics, which are flagged `diagnostic`) with the highest 2010-2015 walk-forward
net Sharpe at 1.2 pips; its full 2010-2026 record is then reported. Nothing is chosen on 2016-2026.
All positions are clipped to [-1, 1]. Positions are decided at the NY close and earn fwd_1d.
"""
from __future__ import annotations

import math
import time
from pathlib import Path

import numpy as np
import pandas as pd

from eurusd.wf import walk_forward, pnl_from_positions, report, YEARS

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "processed" / "features_daily.parquet"
MACRO = ROOT / "data" / "macro"
OUT = ROOT / "experiments" / "results" / "arms"
ARM = "regime_trend"

LOOKBACKS = (21, 63, 126, 252)
BAZ_SPEEDS = ((8, 24), (16, 48), (32, 96))
REGIME_VARS = ("log_rv", "abs_ret21", "adx14", "log_vix")
STRESS_VARS = ("log_rv", "log_vix")
TREND_VARS = ("adx14", "abs_ret21")
MR_COLS = ("neg_rsi2", "neg_z20", "neg_fvz")
VOL_CAP = 1.5
MM_CAP = 2.0


# ----------------------------------------------------------------------------- features (all causal)
def _add_features(df: pd.DataFrame) -> pd.DataFrame:
    X = df.copy()
    c = X["close"]
    rv = X["rv_21d_bp"]
    for k in LOOKBACKS:
        X[f"tsmom_t_{k}"] = X[f"ret_{k}d"] / (rv * math.sqrt(k))
        X[f"tsmom_sign_{k}"] = np.sign(X[f"ret_{k}d"])
    for s, l in BAZ_SPEEDS:
        x = c.ewm(alpha=1.0 / s, adjust=False).mean() - c.ewm(alpha=1.0 / l, adjust=False).mean()
        y = x / c.rolling(63).std()
        z = y / y.rolling(252).std()
        X[f"baz_{s}_{l}"] = z * np.exp(-z ** 2 / 4) / 0.89
    X["baz"] = X[[f"baz_{s}_{l}" for s, l in BAZ_SPEEDS]].mean(axis=1)
    X["neg_rsi2"] = -(X["rsi2"] - 50.0)
    X["neg_z20"] = -X["z20"]
    X["neg_fvz"] = -X["fv_resid_z"]
    # regime variables
    X["log_rv"] = np.log(rv)
    X["abs_ret21"] = X["ret_21d"].abs()
    X["log_vix"] = np.log(X["vix"])
    # round-1 components
    X["cot_sign"] = np.sign(X["cot_z52"]).fillna(0.0)
    X["spread_sign"] = np.sign(X["d_spread2y_20"]).fillna(0.0)
    f = pd.read_csv(MACRO / "fomc_decisions.csv")
    f = f[f.scheduled == True]
    stmt = pd.to_datetime(f.statement_utc, utc=True).sort_values().values
    ct = X["close_time"].values
    nxt = np.append(ct[1:], ct[-1] + np.timedelta64(3, "D"))   # end of the forward-1d window
    # flag the session whose fwd_1d window (close_t, close_{t+1}] contains a scheduled statement
    cnt = np.searchsorted(stmt, nxt, side="right") - np.searchsorted(stmt, ct, side="right")
    X["fomc_eve"] = (cnt > 0).astype(float)
    return X


# ----------------------------------------------------------------------------- regime model
class RegimeHMM:
    """Gaussian HMM fitted on training rows; causal filtered probabilities for any row set."""

    def __init__(self, cols, n_states=3, seed=0):
        self.cols = list(cols)
        self.K = n_states
        self.seed = seed

    def fit(self, train: pd.DataFrame):
        from hmmlearn.hmm import GaussianHMM
        Z = train[self.cols].dropna()
        self.mu, self.sd = Z.mean(), Z.std().replace(0, 1.0)
        Zs = ((Z - self.mu) / self.sd).values
        # restarts chosen on the training likelihood only; EM often returns a degenerate solution in which two
        # states share a mean and flip every day (self-transition ~0), so among the restarts we keep the best
        # likelihood subject to every state being persistent (self-transition >= 0.8), falling back to the best
        # likelihood when no restart satisfies it.
        fits = []
        for s in range(4):
            m = GaussianHMM(n_components=self.K, covariance_type="diag", n_iter=100, tol=1e-3, random_state=self.seed + s)
            m.fit(Zs)
            fits.append((m.score(Zs), float(np.diag(m.transmat_).min()), m))
        good = [f for f in fits if f[1] >= 0.8]
        self.m = max(good or fits, key=lambda f: f[0])[2]
        self.degenerate = not good
        # order states by stress score so state ids are comparable across years
        self.means = pd.DataFrame(self.m.means_, columns=self.cols)
        return self

    def _log_emission(self, Zs: np.ndarray) -> np.ndarray:
        mu, var = self.m.means_, self.m.covars_   # (K,d); covars_ for diag returns (K,d,d) -> take diagonal
        if var.ndim == 3:
            var = np.array([np.diag(v) for v in var])
        out = np.empty((len(Zs), self.K))
        for k in range(self.K):
            out[:, k] = -0.5 * (((Zs - mu[k]) ** 2 / var[k]) + np.log(2 * np.pi * var[k])).sum(axis=1)
        return out

    def filter(self, X: pd.DataFrame) -> pd.DataFrame:
        """Causal forward filter P(s_t | x_1..x_t) over the rows of X in order. NaN rows keep the previous posterior."""
        Zs = ((X[self.cols] - self.mu) / self.sd).values
        ok = ~np.isnan(Zs).any(axis=1)
        logB = np.zeros((len(Zs), self.K))
        logB[ok] = self._log_emission(Zs[ok])
        A = self.m.transmat_
        alpha = self.m.startprob_.copy()
        P = np.empty((len(Zs), self.K))
        for t in range(len(Zs)):
            if ok[t]:
                pred = alpha @ A
                a = pred * np.exp(logB[t] - logB[t].max())
                s = a.sum()
                alpha = a / s if s > 0 else pred
            else:
                alpha = alpha @ A
            P[t] = alpha
        return pd.DataFrame(P, index=X.index, columns=[f"s{k}" for k in range(self.K)])

    def state_scores(self):
        st = [c for c in STRESS_VARS if c in self.cols]
        tr = [c for c in TREND_VARS if c in self.cols]
        stress = self.means[st].mean(axis=1) if st else pd.Series(0.0, index=self.means.index)
        trendy = self.means[tr].mean(axis=1) if tr else pd.Series(0.0, index=self.means.index)
        return stress, trendy


# ----------------------------------------------------------------------------- signals from fitted scales
def _fit_scales(train: pd.DataFrame) -> dict:
    sc = {}
    for k in LOOKBACKS:
        sc[f"q_{k}"] = float(np.nanpercentile(train[f"tsmom_t_{k}"].abs(), 80))
    for c in MR_COLS:
        sc[f"sd_{c}"] = float(train[c].std())
    sc["vol_target"] = float(train["rv_21d_bp"].median())
    sc["mm_c"] = float((train["rv_21d_bp"] ** 2).median())
    return sc


def _trend_signal(X: pd.DataFrame, sc: dict, kind: str) -> pd.Series:
    if kind == "tsmom_sign":
        return X[[f"tsmom_sign_{k}" for k in LOOKBACKS]].mean(axis=1)
    if kind == "tsmom_scaled":
        return pd.concat([(X[f"tsmom_t_{k}"] / sc[f"q_{k}"]).clip(-1, 1) for k in LOOKBACKS], axis=1).mean(axis=1)
    if kind == "baz":
        return X["baz"]
    if kind == "trend_combo":
        return 0.5 * (_trend_signal(X, sc, "tsmom_scaled") + _trend_signal(X, sc, "baz"))
    raise ValueError(kind)


def _mr_signal(X: pd.DataFrame, sc: dict) -> pd.Series:
    parts = [(X[c] / sc[f"sd_{c}"]).clip(-2, 2) / 2 for c in MR_COLS]
    return pd.concat(parts, axis=1).mean(axis=1)   # nanmean: fv_resid_z missing early on


def _component_signal(X: pd.DataFrame, name: str) -> pd.Series:
    if name == "fomc":
        return X["fomc_eve"]
    if name == "cot":
        return X["cot_sign"]
    if name == "spread":
        return X["spread_sign"]
    if name == "round1_combo":
        return (X["fomc_eve"] + X["cot_sign"] + X["spread_sign"]) / 3.0
    raise ValueError(name)


def _vol_scale(X: pd.DataFrame, sc: dict) -> pd.Series:
    return (sc["vol_target"] / X["rv_21d_bp"]).clip(0, VOL_CAP).fillna(0.0)


def _mm_scale(X: pd.DataFrame, sc: dict) -> pd.Series:
    return (sc["mm_c"] / X["rv_21d_bp"] ** 2).clip(0, MM_CAP).fillna(0.0)


def _net_sharpe(pos: pd.Series, X: pd.DataFrame, cost_pips: float, mask=None) -> float:
    p = pnl_from_positions(pos.fillna(0.0), X["fwd_1d"], X["close"], cost_pips)["net_bp"]
    if mask is not None:
        p = p[mask]
    p = p.dropna()
    if len(p) < 30 or p.std() == 0:
        return 0.0
    return float(p.mean() / p.std() * math.sqrt(252))


# ----------------------------------------------------------------------------- variant specification
def make_variant(name, base="trend_combo", vol=True, mm=False, regime=None, mapping="perf", soft=True,
                 regime_vars=REGIME_VARS, component=None, diagnostic=False, note=""):
    """regime: None or K (number of HMM states). base: trend kind, 'mr', or (with component) a round-1 component."""
    return dict(name=name, base=base, vol=vol, mm=mm, regime=regime, mapping=mapping, soft=soft,
                regime_vars=tuple(regime_vars), component=component, diagnostic=diagnostic, note=note)


def _base_signal(X, sc, v):
    if v["component"] is not None:
        return _component_signal(X, v["component"])
    if v["base"] == "mr":
        return _mr_signal(X, sc)
    return _trend_signal(X, sc, v["base"])


def build_fit_predict(X_all: pd.DataFrame, v: dict, cost_pips: float, log: dict | None = None):
    """Closures for wf.walk_forward. X_all is the full feature frame (used only for causal regime filtering)."""

    def fit(train: pd.DataFrame):
        sc = _fit_scales(train)
        model = {"sc": sc}
        if v["regime"]:
            hmm = RegimeHMM(v["regime_vars"], n_states=v["regime"]).fit(train)
            model["hmm"] = hmm
            # filtered probabilities on the training rows (causal, in-sample parameters)
            P = hmm.filter(train)
            hard = P.values.argmax(axis=1)
            K = hmm.K
            if v["component"] is not None:
                sig = _component_signal(train, v["component"])
                vs = _vol_scale(train, sc) if v["vol"] else 1.0
                pos = (sig * vs).clip(-1, 1)
                act = {}
                for s in range(K):
                    act[s] = "on" if _net_sharpe(pos, train, cost_pips, mask=(hard == s)) > 0 else "off"
            elif v["mapping"] == "desc":
                stress, trendy = hmm.state_scores()
                s_stress = int(stress.idxmax())
                others = [s for s in range(K) if s != s_stress]
                thr = float(trendy.iloc[others].mean())
                act = {s_stress: "flat"}
                for s in others:
                    act[s] = "trend" if trendy.iloc[s] > thr else "mr"
            elif v["mapping"] == "perf":
                vs = _vol_scale(train, sc) if v["vol"] else 1.0
                ptr = (_trend_signal(train, sc, v["base"]) * vs).clip(-1, 1)
                pmr = (_mr_signal(train, sc) * vs).clip(-1, 1)
                act = {}
                for s in range(K):
                    m = hard == s
                    a, b = _net_sharpe(ptr, train, cost_pips, m), _net_sharpe(pmr, train, cost_pips, m)
                    act[s] = ("trend" if a >= b else "mr") if max(a, b) > 0 else "flat"
            elif v["mapping"] == "gate":   # trend everywhere except the stressed state
                stress, _ = hmm.state_scores()
                act = {s: "trend" for s in range(K)}
                act[int(stress.idxmax())] = "flat"
            else:
                raise ValueError(v["mapping"])
            model["act"] = act
            model["train_end"] = train.index[-1]
            if log is not None:
                log.setdefault("mappings", []).append({"year": train.index[-1].year + 1, "act": dict(act),
                                                       "state_means": hmm.means.round(2).to_dict("index"),
                                                       "transmat_diag": np.round(np.diag(hmm.m.transmat_), 3).tolist(), "degenerate": hmm.degenerate})
        return model

    def predict(model, test: pd.DataFrame) -> pd.Series:
        sc = model["sc"]
        if not v["regime"]:
            pos = _base_signal(test, sc, v)
        else:
            hmm, act = model["hmm"], model["act"]
            hist = X_all.loc[:test.index[-1]]          # causal filter over the history up to each test date
            P = hmm.filter(hist).loc[test.index]
            if not v["soft"]:
                P = pd.DataFrame(np.eye(hmm.K)[P.values.argmax(axis=1)], index=P.index, columns=P.columns)
            if v["component"] is not None:
                sig = _component_signal(test, v["component"])
                w = sum(P[f"s{s}"] for s in range(hmm.K) if act[s] == "on")
                pos = sig * w
            else:
                tr = _trend_signal(test, sc, v["base"])
                mr = _mr_signal(test, sc)
                pos = pd.Series(0.0, index=test.index)
                for s in range(hmm.K):
                    if act[s] == "trend":
                        pos = pos + P[f"s{s}"] * tr
                    elif act[s] == "mr":
                        pos = pos + P[f"s{s}"] * mr
            if log is not None:
                tl = pd.DataFrame({"p_" + a: sum(P[f"s{s}"] for s in range(hmm.K) if act[s] == a) for a in ("trend", "mr", "flat", "on", "off")
                                   if any(act[s] == a for s in range(hmm.K))}, index=test.index)
                tl["state"] = P.values.argmax(axis=1)
                tl["action"] = [act[s] for s in tl["state"]]
                log.setdefault("timeline", []).append(tl)
        if v["vol"]:
            pos = pos * _vol_scale(test, sc)
        if v["mm"]:
            pos = pos * _mm_scale(test, sc)
        return pos.clip(-1, 1).fillna(0.0)

    return fit, predict


# ----------------------------------------------------------------------------- variant list
def variants() -> list[dict]:
    V = []
    for kind in ("tsmom_sign", "tsmom_scaled", "baz", "trend_combo"):
        V.append(make_variant(f"{kind}_vs", base=kind, vol=True))
    for kind in ("tsmom_sign", "tsmom_scaled", "baz"):
        V.append(make_variant(f"{kind}_raw", base=kind, vol=False, note="no vol scaling (sensitivity)"))
    V.append(make_variant("mr_vs", base="mr", vol=True))
    for K in (3, 4):
        V.append(make_variant(f"regime_K{K}_desc_soft", regime=K, mapping="desc"))
        V.append(make_variant(f"regime_K{K}_perf_soft", regime=K, mapping="perf"))
    V.append(make_variant("regime_K3_perf_hard", regime=3, mapping="perf", soft=False))
    V.append(make_variant("regime_K3_gate_trend", regime=3, mapping="gate", note="trend except in the stressed state, no MR"))
    for comp in ("fomc", "cot", "spread", "round1_combo"):
        V.append(make_variant(f"{comp}_uncond", component=comp, vol=True))
        V.append(make_variant(f"{comp}_regimeK3", component=comp, regime=3, vol=True))
    V.append(make_variant("trend_combo_vs_mm", base="trend_combo", vol=True, mm=True))
    V.append(make_variant("regime_K3_perf_soft_mm", regime=3, mapping="perf", mm=True))
    V.append(make_variant("regime_K3_desc_soft_mm", regime=3, mapping="desc", mm=True))
    V.append(make_variant("round1_combo_regimeK3_mm", component="round1_combo", regime=3, mm=True))
    # leave-one-out diagnostics of the regime variables (both K3 mappings)
    for mp in ("desc", "perf"):
        for drop in REGIME_VARS:
            V.append(make_variant(f"regime_K3_{mp}_soft_LOO_{drop}", regime=3, mapping=mp,
                                  regime_vars=tuple(c for c in REGIME_VARS if c != drop), diagnostic=True))
    return V


# ----------------------------------------------------------------------------- driver
def load() -> pd.DataFrame:
    return _add_features(pd.read_parquet(DATA))


def run_variant(X: pd.DataFrame, v: dict, cost_pips: float = 1.2, log: dict | None = None, verbose=False) -> pd.Series:
    fit, predict = build_fit_predict(X, v, cost_pips, log)
    return walk_forward(X, fit, predict, label_end=X["label_end_1d"], verbose=verbose).fillna(0.0)


def evaluate(X: pd.DataFrame, pos: pd.Series, name: str, n_arms: int) -> pd.DataFrame:
    out = []
    for cp in (1.2, 0.6):
        pnl = pnl_from_positions(pos, X["fwd_1d"], X["close"], cost_pips=cp)
        t = report(pnl, periods_per_year=252, name=ARM, n_arms=n_arms)
        t.insert(1, "variant", name)
        t.insert(2, "cost_pips", cp)
        out.append(t)
    return pd.concat(out, ignore_index=True)


def run(cost_pips: float = 1.2, save: bool = True, verbose: bool = True):
    """Run every variant, apply the declared selection rule, save deliverables. Returns (positions, report)."""
    X = load()
    V = variants()
    n_cand = sum(1 for v in V if not v["diagnostic"])
    tables, positions, logs = [], {}, {}
    for v in V:
        t0 = time.time()
        log = {} if v["regime"] else None
        pos = run_variant(X, v, cost_pips=cost_pips, log=log)
        positions[v["name"]] = pos
        logs[v["name"]] = log
        tbl = evaluate(X, pos, v["name"], n_arms=n_cand)
        tbl["diagnostic"] = v["diagnostic"]
        tables.append(tbl)
        if verbose:
            r = tbl[(tbl.cost_pips == cost_pips)].set_index("period")
            print(f"{v['name']:34s} 10-26 SR {r.loc['2010-2026','sharpe']:+.2f} t {r.loc['2010-2026','t']:+.2f} | "
                  f"10-15 {r.loc['2010-2015','sharpe']:+.2f} | 16-26 {r.loc['2016-2026','sharpe']:+.2f} | "
                  f"23-26 {r.loc['2023-2026','sharpe']:+.2f}  ({time.time()-t0:.0f}s)", flush=True)
    rep = pd.concat(tables, ignore_index=True)
    # declared rule: best 2010-2015 net Sharpe at 1.2 pips among non-diagnostic variants
    sel = rep[(rep.period == "2010-2015") & (rep.cost_pips == 1.2) & (~rep.diagnostic)]
    final = sel.sort_values("sharpe", ascending=False).iloc[0]["variant"]
    rep["final"] = rep["variant"] == final
    rep["n_variants"] = len(V)
    rep["n_candidates"] = n_cand
    pos = positions[final]
    out = pd.DataFrame({"pos": pos, "fwd_bp": X["fwd_1d"],
                        "net_bp": pnl_from_positions(pos, X["fwd_1d"], X["close"], cost_pips=cost_pips)["net_bp"]})
    out = out[out.index.year >= 2010]
    if save:
        OUT.mkdir(parents=True, exist_ok=True)
        out.to_parquet(OUT / f"{ARM}_positions.parquet")
        rep.to_csv(OUT / f"{ARM}_report.csv", index=False)
        allpos = pd.DataFrame(positions)
        allpos[allpos.index.year >= 2010].to_parquet(OUT / f"{ARM}_all_positions.parquet")
        # regime timelines of the regime variants
        diag = {v["name"] for v in V if v["diagnostic"] or v["mm"]}
        for name, lg in logs.items():
            if lg and "timeline" in lg and name not in diag:
                pd.concat(lg["timeline"]).to_csv(OUT / f"{ARM}_timeline_{name}.csv")
        import json
        json.dump({k: v.get("mappings", []) for k, v in logs.items() if v}, open(OUT / f"{ARM}_mappings.json", "w"), indent=1, default=str)
    print("FINAL:", final)
    return out["pos"], rep


if __name__ == "__main__":
    run()
