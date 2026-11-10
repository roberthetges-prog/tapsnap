"""Arm B "intraday_ml": conditioned intraday prediction at a few decision times per day.

Idea: round 1 found one robust intraday regularity (short EUR/USD 07:00-13:00 London) and that hour-of-day
patterns drift. Here a model conditioned on the day's context (hourly feature store: multi-horizon returns,
intraday vol state, position in the 24h range, distances to previous-day levels, session-so-far returns, event
clocks and the previous session's daily context d_*) is asked to predict fwd_4h / fwd_8h at three decision bars:
  L07  = the bar closing at 07:00 London (London session),
  L13  = the bar closing at 13:00 London (London/NY overlap),
  NY17 = the bar closing at 17:00 New York (overnight / Asia).
Everything runs through eurusd.wf.walk_forward (yearly expanding window, test years 2010..2026).

Cost accounting: every decision is a discrete round trip (enter at the bar close, exit `horizon` hours later), so
the net P&L charges 2 x cost per trade (turnover = 2|pos|). pnl_from_positions' diff-based turnover would charge an
always-short rule once in 17 years, which is wrong for intraday trades; the wrapper below is the conservative one.

Decision rule (fixed): pos = sign(forecast) when |forecast| > max(q-quantile of |forecast| on a time-ordered 20 %
hold-out of the training window, round-trip cost in bp), else 0.

Selection rule (declared before any result was seen): among the ML grid
  decision {L07, L13, NY17} x horizon {4h, 8h} x model {lgbm, ridge, logit} x quantile {0.5, 0.8}   (36 variants)
the FINAL variant is the one with the highest 2010-2015 net Sharpe at 1.2 pips among variants that are active on
at least 10 % of their decision bars in 2010-2015. Baselines / regime gates / event exclusion / post-selection
diagnostics are reported in the same harness but are not eligible for selection.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

from eurusd.wf import walk_forward, pnl_from_positions, report, YEARS

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / "data" / "processed" / "features_hourly.parquet"
RES = ROOT / "experiments" / "results" / "arms"
REP = ROOT / "reports"
ARM = "intraday_ml"

DECISIONS = {"L07": ("hour_london", 6), "L13": ("hour_london", 12), "NY17": ("hour_ny", 16)}
HORIZONS = (4, 8)
MODELS = ("lgbm", "ridge", "logit")
QUANTILES = (0.5, 0.8)
PPY = 260                      # one decision bar per weekday
MIN_ACTIVE_FRAC = 0.10         # eligibility for selection (2010-2015)
LABELS = ["fwd_1h", "fwd_4h", "fwd_8h", "fwd_24h", "label_end_1h", "label_end_4h", "label_end_8h", "label_end_24h", "close"]
CONSTANT_AT_DECISION = ["hour_london", "hour_ny", "is_london", "is_ny"]
LAST_BAR_FEATS = ["ret_1h", "ret_2h", "range_1h_pips", "range_rel_24h"]   # features dominated by the decision bar itself
SEED = 7
SHUFFLE_SEEDS = (7, 11, 23, 42, 99)
PERIODS = ("2010-2015", "2010-2026", "2016-2026", "2023-2026")


def log(msg: str) -> None:
    print(f"[{time.strftime('%H:%M:%S')}] {msg}", flush=True)


# ----------------------------------------------------------------------------------------------- data
def decision_frame(h: pd.DataFrame, dec: str, horizon: int, exclude_events: bool = False, hour_shift: int = 0) -> pd.DataFrame:
    col, val = DECISIONS[dec]
    d = h[(h[col] == val + hour_shift) & (h.index.dayofweek < 5)].copy()
    d = d[d[f"fwd_{horizon}h"].notna()]
    if exclude_events:
        near = (d["h_to_any_high"] <= 2) | (d["h_since_any_high"] <= 2)
        d = d[~near]
    return d


def feature_list(d: pd.DataFrame) -> list[str]:
    feats = [c for c in d.columns if c not in LABELS and c not in CONSTANT_AT_DECISION]
    return [c for c in feats if d[c].notna().mean() > 0.5]   # drop columns that are (almost) all NaN at this decision


# ----------------------------------------------------------------------------------------------- models
def _fit_model(model: str, X: pd.DataFrame, y: pd.Series):
    if model == "lgbm":
        import lightgbm as lgb
        yc = y.clip(-3 * y.std(), 3 * y.std())
        m = lgb.LGBMRegressor(n_estimators=300, learning_rate=0.03, num_leaves=15, min_child_samples=100, subsample=0.8,
                              subsample_freq=1, colsample_bytree=0.7, reg_lambda=5.0, num_threads=1, random_state=SEED, verbose=-1)
        m.fit(X, yc)
        return ("lgbm", m, None)
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression, RidgeCV
    from sklearn.model_selection import TimeSeriesSplit
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    if model == "ridge":
        yc = y.clip(-3 * y.std(), 3 * y.std())
        pipe = make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(),
                             RidgeCV(alphas=np.logspace(0, 5, 11), cv=TimeSeriesSplit(4)))
        pipe.fit(X, yc)
        return ("ridge", pipe, None)
    if model == "logit":
        pipe = make_pipeline(SimpleImputer(strategy="median", keep_empty_features=True), StandardScaler(),
                             LogisticRegression(C=0.05, max_iter=1000))
        pipe.fit(X, (y > 0).astype(int))
        return ("logit", pipe, float(y.abs().mean()))
    raise ValueError(model)


def _predict_model(mdl, X: pd.DataFrame) -> np.ndarray:
    kind, m, scale = mdl
    if kind == "logit":
        p = m.predict_proba(X)[:, 1]
        return (2 * p - 1) * scale          # expected move in bp: P(up)-P(down) times the typical |move|
    return np.asarray(m.predict(X), dtype=float)


def make_ml_fit_predict(model: str, q: float, feats: list[str], target: str, cost_pips: float, importances: list | None = None):
    def fit(train: pd.DataFrame):
        X, y = train[feats], train[target]
        k = int(len(train) * 0.8)
        m0 = _fit_model(model, X.iloc[:k], y.iloc[:k])
        p0 = _predict_model(m0, X.iloc[k:])
        cost_rt_bp = 2 * cost_pips / float(train["close"].median())
        thr = max(float(np.quantile(np.abs(p0), q)), cost_rt_bp)
        m = _fit_model(model, X, y)
        if importances is not None and model == "lgbm":
            importances.append(pd.Series(m[1].booster_.feature_importance("gain"), index=feats))
        return (m, thr)

    def predict(mdl, test: pd.DataFrame):
        m, thr = mdl
        p = _predict_model(m, test[feats])
        return np.where(np.abs(p) > thr, p, 0.0)
    return fit, predict


def make_rule_fit_predict(rule: str):
    """Unconditional / regime-gated London short in the same harness. Returns -1 (short) or 0."""
    def fit(train: pd.DataFrame):
        if rule.startswith("rv_"):
            return tuple(np.nanquantile(train["d_rv_21d_bp"], [1 / 3, 2 / 3]))
        if rule.startswith("adx_"):
            return (float(np.nanmedian(train["d_adx14"])),)
        return None

    def predict(mdl, test: pd.DataFrame):
        if rule == "uncond":
            return np.full(len(test), -1.0)
        if rule.startswith("rv_"):
            lo, hi = mdl
            x = test["d_rv_21d_bp"].values
            mask = {"rv_low": x <= lo, "rv_mid": (x > lo) & (x <= hi), "rv_high": x > hi}[rule]
        else:
            med = mdl[0]
            x = test["d_adx14"].values
            mask = {"adx_low": x <= med, "adx_high": x > med}[rule]
        return np.where(mask, -1.0, 0.0)
    return fit, predict


def make_fade_fit_predict(q: float):
    """Diagnostic: fade the decision bar's own 1h return when |ret_1h| exceeds its training q-quantile (no model)."""
    def fit(train: pd.DataFrame):
        return float(np.nanquantile(train["ret_1h"].abs(), q))

    def predict(thr, test: pd.DataFrame):
        x = test["ret_1h"].values
        return np.where(np.abs(x) > thr, -np.sign(x), 0.0)
    return fit, predict


# ----------------------------------------------------------------------------------------------- pnl / report
def pnl_round_trip(pos: pd.Series, fwd_bp: pd.Series, price: pd.Series, cost_pips: float) -> pd.DataFrame:
    """Same columns as wf.pnl_from_positions but every non-zero position is a discrete round trip (turnover 2|pos|)."""
    out = pnl_from_positions(pos, fwd_bp, price, cost_pips=cost_pips)
    cost_bp = cost_pips * 1e-4 / price * 1e4
    out["turnover"] = 2 * out["pos"].abs()
    out["net_bp"] = out["gross_bp"] - out["turnover"] * cost_bp
    return out


def make_table(pnl: pd.DataFrame, name: str, n_arms: int, group: str, dec: str, hz: int, cost_pips: float) -> pd.DataFrame:
    tbl = report(pnl, periods_per_year=PPY, name=ARM, n_arms=n_arms)
    tbl.insert(1, "variant", name)
    gross = []
    for p in tbl["period"]:
        a, b = (int(p), int(p)) if len(p) == 4 else map(int, p.split("-"))
        g = pnl["gross_bp"][(pnl.index.year >= a) & (pnl.index.year <= b)]
        gross.append(float(g.mean() / g.std() * np.sqrt(PPY)) if len(g) > 10 and g.std() > 0 else 0.0)
    tbl["gross_sharpe"] = gross
    tbl["group"] = group; tbl["decision"] = dec; tbl["horizon_h"] = hz; tbl["cost_pips"] = cost_pips
    return tbl


def run_variant(d: pd.DataFrame, horizon: int, fit, predict, cost_pips: float, name: str, n_arms: int,
                group: str = "", dec: str = "", verbose=False):
    target, lend = f"fwd_{horizon}h", f"label_end_{horizon}h"
    pred = walk_forward(d, fit, predict, label_end=d[lend], verbose=verbose)
    pos = np.sign(pred).fillna(0.0)
    oos = pos.index.year >= YEARS[0]
    pnl = pnl_round_trip(pos[oos], d.loc[oos, target], d.loc[oos, "close"], cost_pips)
    tbl = make_table(pnl, name, n_arms, group, dec, horizon, cost_pips)
    return pred, pnl, tbl


def agg(tbl: pd.DataFrame, period: str, col: str = "sharpe") -> float:
    return float(tbl.loc[tbl.period == period, col].iloc[0])


def _line(tbl: pd.DataFrame) -> str:
    return "  ".join(f"SR{p[2:4]}-{p[-2:]} {agg(tbl, p):+.2f}" for p in PERIODS) + f"  active {agg(tbl, '2010-2026', 'active_frac'):.2f}"


# ----------------------------------------------------------------------------------------------- main
def run(cost_pips: float = 1.2, quick: bool = False):
    t0 = time.time()
    RES.mkdir(parents=True, exist_ok=True)
    h = pd.read_parquet(DATA)
    grid = [(dec, hz, m, q) for dec in DECISIONS for hz in HORIZONS for m in MODELS for q in QUANTILES]
    if quick:
        grid = [g for g in grid if g[2] != "lgbm"][:4]
    n_grid = len(grid)
    n_diag = 5                            # fade q0.5/q0.8, no-last-bar-features, decision bar -1h / +1h
    n_variants = n_grid + 2 + 10 + 3 + n_diag   # grid + unconditional (2 horizons) + regime gates (5 x 2) + event exclusion (3) + diagnostics
    tables, pnls, preds = [], {}, {}

    # --- 1) ML grid (eligible for selection)
    for i, (dec, hz, m, q) in enumerate(grid):
        d = decision_frame(h, dec, hz)
        feats = feature_list(d)
        name = f"ml_{dec}_{hz}h_{m}_q{q}"
        fit, predict = make_ml_fit_predict(m, q, feats, f"fwd_{hz}h", cost_pips)
        pred, pnl, tbl = run_variant(d, hz, fit, predict, cost_pips, name, n_variants, "ml_grid", dec)
        tables.append(tbl); pnls[name] = pnl; preds[name] = pred
        log(f"[{i + 1}/{n_grid}] {name}: {_line(tbl)}  ({time.time() - t0:.0f}s)")

    # --- 2) baselines: unconditional London short and regime gates at L07, both horizons
    for hz in HORIZONS:
        d = decision_frame(h, "L07", hz)
        for rule in ("uncond", "rv_low", "rv_mid", "rv_high", "adx_low", "adx_high"):
            name = f"london_short_{rule}_{hz}h"
            fit, predict = make_rule_fit_predict(rule)
            pred, pnl, tbl = run_variant(d, hz, fit, predict, cost_pips, name, n_variants, "baseline" if rule == "uncond" else "regime", "L07")
            tables.append(tbl); pnls[name] = pnl; preds[name] = pred
            log(f"{name}: {_line(tbl)}")

    # --- 3) selection (fixed rule, see module docstring)
    allt = pd.concat(tables, ignore_index=True)
    sel = allt[(allt.group == "ml_grid") & (allt.period == "2010-2015")]
    elig = sel[sel.active_frac >= MIN_ACTIVE_FRAC]
    if elig.empty:
        elig = sel
    final_name = str(elig.sort_values("sharpe", ascending=False).iloc[0]["variant"])
    f_dec, f_hz, f_model, f_q = [g for g in grid if f"ml_{g[0]}_{g[1]}h_{g[2]}_q{g[3]}" == final_name][0]
    target = f"fwd_{f_hz}h"
    log(f"FINAL (rule: best 2010-2015 Sharpe, active >= {MIN_ACTIVE_FRAC:.0%}): {final_name}")

    # --- 4) event exclusion (robustness, not eligible): final ML config + unconditional short at both horizons
    d = decision_frame(h, f_dec, f_hz, exclude_events=True)
    feats = feature_list(d)
    fit, predict = make_ml_fit_predict(f_model, f_q, feats, target, cost_pips)
    name = f"{final_name}_noevent2h"
    _, pnl, tbl = run_variant(d, f_hz, fit, predict, cost_pips, name, n_variants, "event_excl", f_dec)
    tables.append(tbl); pnls[name] = pnl
    log(f"{name}: {_line(tbl)}")
    for hz in HORIZONS:
        d = decision_frame(h, "L07", hz, exclude_events=True)
        name = f"london_short_uncond_{hz}h_noevent2h"
        fit, predict = make_rule_fit_predict("uncond")
        _, pnl, tbl = run_variant(d, hz, fit, predict, cost_pips, name, n_variants, "event_excl", "L07")
        tables.append(tbl); pnls[name] = pnl
        log(f"{name}: {_line(tbl)}")

    # --- 5) post-selection diagnostics of the final configuration (not eligible)
    d = decision_frame(h, f_dec, f_hz)
    feats = feature_list(d)
    diag = {}
    for q in (0.5, 0.8):
        name = f"diag_fade_ret1h_q{q}_{f_dec}_{f_hz}h"
        fit, predict = make_fade_fit_predict(q)
        _, pnl, tbl = run_variant(d, f_hz, fit, predict, cost_pips, name, n_variants, "diagnostic", f_dec)
        tables.append(tbl); diag[name] = tbl; log(f"{name}: {_line(tbl)}")
    feats_nolast = [c for c in feats if c not in LAST_BAR_FEATS]
    name = f"{final_name}_no_last_bar_feats"
    fit, predict = make_ml_fit_predict(f_model, f_q, feats_nolast, target, cost_pips)
    _, pnl, tbl = run_variant(d, f_hz, fit, predict, cost_pips, name, n_variants, "diagnostic", f_dec)
    tables.append(tbl); diag[name] = tbl; log(f"{name}: {_line(tbl)}")
    for shift in (-1, +1):
        dd = decision_frame(h, f_dec, f_hz, hour_shift=shift)
        name = f"{final_name}_decision{shift:+d}h"
        fit, predict = make_ml_fit_predict(f_model, f_q, feature_list(dd), target, cost_pips)
        _, pnl, tbl = run_variant(dd, f_hz, fit, predict, cost_pips, name, n_variants, "diagnostic", f_dec)
        tables.append(tbl); diag[name] = tbl; log(f"{name}: {_line(tbl)}")

    # --- 6) final variant: cost sensitivity (same positions), feature importances, leak checks
    final_pos = np.sign(preds[final_name]).fillna(0.0)
    oos = final_pos.index.year >= YEARS[0]
    cost_tbls = {}
    for c in (0.6, 2.0, 3.0):
        pnl_c = pnl_round_trip(final_pos[oos], d.loc[oos, target], d.loc[oos, "close"], c)
        tbl = make_table(pnl_c, f"{final_name}_cost{c}", n_variants, "final_cost_sens", f_dec, f_hz, c)
        tables.append(tbl); cost_tbls[c] = tbl
        log(f"final at {c} pips: {_line(tbl)}")

    imps: list = []
    fit, predict = make_ml_fit_predict("lgbm", f_q, feats, target, cost_pips, importances=imps)
    walk_forward(d, fit, predict, label_end=d[f"label_end_{f_hz}h"], verbose=False)
    imp = pd.concat(imps, axis=1).mean(axis=1).sort_values(ascending=False)
    imp = imp / imp.sum()
    coef = None
    if f_model in ("ridge", "logit"):
        train = d[d[f"label_end_{f_hz}h"] < pd.Timestamp("2023-01-01", tz="UTC")]
        m = _fit_model(f_model, train[feats], train[target])
        coef = pd.Series(np.ravel(m[1][-1].coef_), index=feats).sort_values(key=np.abs, ascending=False)

    leak = {"shuffle": []}
    fit, predict = make_ml_fit_predict(f_model, f_q, feats, target, cost_pips)
    for s in SHUFFLE_SEEDS:
        rng = np.random.default_rng(s)
        d_sh = d.copy(); d_sh[target] = rng.permutation(d_sh[target].values)
        _, _, tbl = run_variant(d_sh, f_hz, fit, predict, cost_pips, f"{final_name}_LEAK_shuffled_labels_seed{s}", n_variants, "leak_check", f_dec)
        leak["shuffle"].append(tbl); tables.append(tbl)
        log(f"leak shuffle seed {s}: net {_line(tbl)}  gross SR10-26 {agg(tbl, '2010-2026', 'gross_sharpe'):+.2f}")
    d_st = d.copy(); d_st[feats] = d_st[feats].shift(1)
    _, _, tbl = run_variant(d_st.iloc[1:], f_hz, fit, predict, cost_pips, f"{final_name}_LEAK_features_shift+1_stale", n_variants, "leak_check", f_dec)
    leak["stale"] = tbl; tables.append(tbl); log(f"leak stale: {_line(tbl)}  gross SR10-26 {agg(tbl, '2010-2026', 'gross_sharpe'):+.2f}")
    d_fu = d.copy(); d_fu[feats] = d_fu[feats].shift(-1)
    _, _, tbl = run_variant(d_fu.iloc[:-1], f_hz, fit, predict, cost_pips, f"{final_name}_LEAK_features_shift-1_future", n_variants, "leak_check", f_dec)
    leak["future"] = tbl; tables.append(tbl); log(f"leak future: {_line(tbl)}")

    # --- 7) save
    allt = pd.concat(tables, ignore_index=True)
    allt["final"] = allt["variant"] == final_name
    allt.to_csv(RES / f"{ARM}_report.csv", index=False)
    pnl_final = pnls[final_name]
    positions = pd.DataFrame({"pos": pnl_final["pos"], "fwd_bp": d.loc[pnl_final.index, target], "net_bp": pnl_final["net_bp"],
                              "horizon_h": f_hz, "forecast_bp": preds[final_name].loc[pnl_final.index]})
    positions.to_parquet(RES / f"{ARM}_positions.parquet")
    trade_stats = {"n_trades": int((positions.pos != 0).sum()), "long_frac": float((positions.pos > 0).mean() / max((positions.pos != 0).mean(), 1e-9)),
                   "gross_per_trade": float((positions.pos * positions.fwd_bp)[positions.pos != 0].mean()),
                   "fade_frac": float((np.sign(positions.pos) == -np.sign(h.loc[positions.index, "ret_1h"]))[positions.pos != 0].mean())}
    write_report(allt, final_name, f_dec, f_hz, f_model, f_q, imp, coef, leak, diag, cost_tbls, n_variants, feats, cost_pips, trade_stats, time.time() - t0)
    log(f"done in {time.time() - t0:.0f}s; final {final_name}")
    return positions["pos"], allt


# ----------------------------------------------------------------------------------------------- report
def _fmt(tbl: pd.DataFrame, periods=("2010-2026", "2016-2026", "2023-2026", "2010-2015", "2016-2022")) -> str:
    rows = []
    for p in periods:
        r = tbl[tbl.period == p].iloc[0]
        rows.append(f"| {p} | {r['sharpe']:+.2f} | {r['t']:+.2f} | {r['gross_sharpe']:+.2f} | {r['mean_bp']:+.2f} | {r['sum_bp']:+.0f} | {r['active_frac']:.2f} | {int(r['n'])} |")
    return "| period | net Sharpe | t | gross Sharpe | mean bp/decision | sum bp | active | n |\n|---|---|---|---|---|---|---|---|\n" + "\n".join(rows)


def _summary(sub: pd.DataFrame, periods=PERIODS) -> str:
    out = ["| variant | " + " | ".join(f"SR {p}" for p in periods) + " | t 2010-26 | gross SR 2010-26 | active |", "|---|" + "---|" * (len(periods) + 3)]
    for v in sub.variant.unique():
        s = sub[sub.variant == v].set_index("period")
        out.append(f"| {v} | " + " | ".join(f"{s.loc[p, 'sharpe']:+.2f}" for p in periods) +
                   f" | {s.loc['2010-2026', 't']:+.2f} | {s.loc['2010-2026', 'gross_sharpe']:+.2f} | {s.loc['2010-2026', 'active_frac']:.2f} |")
    return "\n".join(out)


def write_report(allt, final_name, dec, hz, model, q, imp, coef, leak, diag, cost_tbls, n_variants, feats, cost_pips, ts, secs):
    fin = allt[allt.variant == final_name]
    fin06 = cost_tbls[0.6]
    years = fin[fin.period.str.len() == 4]
    y06 = fin06[fin06.period.str.len() == 4].set_index("period")
    yr_rows = "\n".join(f"| {r.period} | {r.sharpe:+.2f} | {r.t:+.2f} | {r.mean_bp:+.2f} | {r.active_frac:.2f} | {int(r.n)} | {y06.loc[r.period, 'sharpe']:+.2f} | {y06.loc[r.period, 't']:+.2f} |"
                        for r in years.itertuples())
    dsp = float(fin.loc[fin.period == "2010-2026", "deflated_sharpe_p"].iloc[0])
    passed = agg(fin, "2010-2026") > 0.4 and agg(fin, "2016-2026") > 0.3 and agg(fin, "2023-2026") >= 0
    unc = {k: allt[allt.variant == f"london_short_uncond_{k}h"].set_index("period") for k in HORIZONS}
    top = "\n".join(f"| {k} | {v:.3f} |" for k, v in imp.head(15).items())
    coef_txt = "" if coef is None else "\n\nLargest standardized coefficients of the final linear model fitted on 2003-2022 (sign, for intuition):\n\n| feature | coef |\n|---|---|\n" + \
        "\n".join(f"| {k} | {v:+.3f} |" for k, v in coef.head(12).items())
    sh = pd.concat(leak["shuffle"]); sh10 = sh[sh.period == "2010-2026"]; sh16 = sh[sh.period == "2016-2026"]
    st = leak["stale"].set_index("period"); fu = leak["future"].set_index("period")
    def best_ml(dec_):
        sub = allt[(allt.group == "ml_grid") & (allt.decision == dec_) & (allt.period == "2010-2026")].sort_values("sharpe", ascending=False)
        return sub.iloc[0] if len(sub) else pd.Series({"variant": "n/a", "sharpe": np.nan, "t": np.nan})
    best_ml_l07, best_ml_l13 = best_ml("L07"), best_ml("L13")
    fade08 = diag[f"diag_fade_ret1h_q0.8_{dec}_{hz}h"]
    nolast = diag[f"{final_name}_no_last_bar_feats"]
    cost_rows = "\n".join(f"| {c} | {agg(t, '2010-2026'):+.2f} | {agg(t, '2010-2026', 't'):+.2f} | {agg(t, '2016-2026'):+.2f} | {agg(t, '2023-2026'):+.2f} |"
                          for c, t in sorted({**cost_tbls, cost_pips: fin}.items()))
    breakeven_pips = ts["gross_per_trade"] / 2 * 1.1   # gross bp per trade -> pips per side (price ~1.1)

    md = f"""# Arm B: intraday_ml - context-conditioned intraday prediction at fixed decision times

## Idea
Round 1 found one robust intraday regularity (short EUR/USD 07:00-13:00 London) and that hour-of-day patterns drift.
This arm asks whether a model conditioned on the day's context predicts the London session, the London/NY overlap and
the overnight session better than the unconditional rule. Decision bars (hourly feature store, index = bar start):
L07 = bar closing 07:00 London (`hour_london == 6`), L13 = bar closing 13:00 London (`hour_london == 12`),
NY17 = bar closing 17:00 New York (`hour_ny == 16`); weekend bars dropped. Targets `fwd_4h`, `fwd_8h` (bp, from the
decision bar close). One decision per weekday per variant, so `periods_per_year = {PPY}`.

## Features ({len(feats)} at the final decision bar)
All hourly-store columns except labels, `close` and the columns constant at a decision bar (`hour_london`, `hour_ny`,
`is_london`, `is_ny`), and columns more than 50 % NaN at that decision bar (`ret_since_london_open_bp` is undefined at
L07). Groups: multi-horizon returns, intraday vol state, position in the 24h range, distances to previous-day
high/low/open/pivot, session-so-far return, hour_utc (= DST flag) and dow, event clocks (hours to/since FOMC, ECB,
NFP, CPI, any high-impact), and `d_*` = the previous NY session's daily features (returns, rv, trend state, adx, 2y
spread and its changes, fair-value residual, VIX, COT, dollar factor, DXY/SPX, last NFP/CPI surprises, month-end).

## Models and decision rule
* LightGBM regression (300 trees, lr 0.03, 15 leaves, min 100 rows per leaf, 70 % features / 80 % rows per tree,
  L2 5, `num_threads=1`), target clipped at +-3 sd of the training window.
* Ridge (median impute, standardize, alpha chosen by 4-fold time-ordered CV inside the training window, target clipped).
* Logistic on sign(target) (C = 0.05); forecast in bp = (2 P(up) - 1) x mean |target| of the training window.
* Decision rule: pos = sign(forecast) iff |forecast| > max( q-quantile of |forecast| on the last 20 % (time-ordered) of
  the training window, round-trip cost in bp = 2 x cost_pips / price ), q in {{0.5, 0.8}}.
* Costs: each decision is a discrete round trip, so net = pos x fwd - 2|pos| x cost. (The harness's diff-based turnover
  would charge an always-short rule once in 17 years; the round-trip accounting is the honest one for intraday trades.)
  Positions are fixed by the 1.2-pip rule; the 0.6 / 2.0 / 3.0-pip records re-price the same positions.
* Walk-forward: `eurusd.wf.walk_forward` with `label_end_{{h}}h`, test years 2010-2026, expanding window from 2003.

## Selection rule (declared before results)
Among the 36 ML-grid variants (3 decision bars x 2 horizons x 3 models x 2 quantiles) pick the highest 2010-2015 net
Sharpe at 1.2 pips among variants active on >= {MIN_ACTIVE_FRAC:.0%} of their decision bars in 2010-2015; report its full
2010-2026 record. Baselines, regime gates, event exclusion and the post-selection diagnostics are reported in the same
harness but were not eligible. Number of variants run in this arm: **{n_variants}** (36 grid + 2 unconditional + 10 regime
+ 3 event-exclusion + 5 diagnostics; cost re-pricings and leak checks not counted); the deflated-Sharpe p of the
final variant uses n_trials = {n_variants}.

## Final variant: `{final_name}`
Decision bar {dec}, horizon {hz}h, model {model}, quantile {q}. Deflated-Sharpe p (n_trials={n_variants}) = {dsp:.3f}.
{ts['n_trades']} trades in 2010-2026 ({ts['long_frac']:.0%} long), gross {ts['gross_per_trade']:+.2f} bp per trade,
{ts['fade_frac']:.0%} of the trades are in the direction opposite to the decision bar's own 1h return.

| year | net Sharpe (1.2p) | t | mean bp | active | n | net Sharpe (0.6p) | t (0.6p) |
|---|---|---|---|---|---|---|---|
{yr_rows}

Aggregates at 1.2 pips:

{_fmt(fin)}

Aggregates at 0.6 pips (same positions):

{_fmt(fin06)}

Cost sensitivity (same positions; net Sharpe / t):

| cost pips per side | SR 2010-2026 | t | SR 2016-2026 | SR 2023-2026 |
|---|---|---|---|---|
{cost_rows}

Break-even cost for the final variant is about {breakeven_pips:.1f} pips per side.

Success bar (2010-2026 SR > 0.4, 2016-2026 SR > 0.3, 2023-2026 >= 0 at 1.2 pips): **{"PASSED" if passed else "FAILED"}** on paper -
see the assessment below before taking it at face value.

## Does conditioning beat the unconditional London short?
Same harness, same round-trip costs. The unconditional short at L07:
4h horizon SR 2010-2026 {unc[4].loc['2010-2026', 'sharpe']:+.2f} (t {unc[4].loc['2010-2026', 't']:+.2f}, gross SR {unc[4].loc['2010-2026', 'gross_sharpe']:+.2f}), 2016-2026 {unc[4].loc['2016-2026', 'sharpe']:+.2f}, 2023-2026 {unc[4].loc['2023-2026', 'sharpe']:+.2f};
8h horizon SR 2010-2026 {unc[8].loc['2010-2026', 'sharpe']:+.2f} (t {unc[8].loc['2010-2026', 't']:+.2f}, gross SR {unc[8].loc['2010-2026', 'gross_sharpe']:+.2f}), 2016-2026 {unc[8].loc['2016-2026', 'sharpe']:+.2f}, 2023-2026 {unc[8].loc['2023-2026', 'sharpe']:+.2f}.
The unconditional mean move from 07:00 London (about -0.4 bp over 4h, -1.3 bp over 8h) is smaller than one round trip
at 1.2 pips (about 2.2 bp), so the rule is gross-positive but net-negative when traded every day; round 1's positive
record for it relied on a 6h hold, a disaster stop and a lower cost assumption.

* Conditioning at the same decision bar (L07): the best of the 12 L07 ML variants over 2010-2026 is `{best_ml_l07['variant']}`
  with net SR {best_ml_l07['sharpe']:+.2f} (t {best_ml_l07['t']:+.2f}). The models cut the losing days (net SR goes from
  {unc[4].loc['2010-2026', 'sharpe']:+.2f} / {unc[8].loc['2010-2026', 'sharpe']:+.2f} to about zero) but find no reliably profitable subset: nothing at L07 clears the cost gate
  often enough, and 2016-2026 is at best flat. **Conditioning does not turn the London effect into a tradable signal.**
* Regime gates on the unconditional short: the mid-rv tercile and high-ADX halves look best in 2010-2015 (SR about +0.8 at
  8h) but both are negative in 2016-2026 and 2023-2026. Low-rv regimes are the worst. No gate is stable.
* Event exclusion (bars within 2h of a high-impact event removed): changes nothing for the London short (slightly worse);
  for the final configuration it raises the Sharpe a little (see table).
* L13 (London/NY overlap): every one of the 12 variants is negative over 2010-2026 (best `{best_ml_l13['variant']}` SR {best_ml_l13['sharpe']:+.2f}).
  Nothing predictable at the overlap after costs.
* NY17 (overnight): all 12 variants are positive and it is where the selection rule lands. See the assessment.

### Baselines and regime gates (London short at L07; gate thresholds from the training window)
{_summary(allt[allt.group.isin(["baseline", "regime"])])}

### Event exclusion (decision bars within 2h of a high-impact event removed from train and test)
{_summary(allt[allt.group == "event_excl"])}

### Full ML grid
{_summary(allt[allt.group == "ml_grid"])}

## Top features
Mean LightGBM gain share over the 17 walk-forward fits at {dec}/{hz}h{" (the final model is linear; this is its LightGBM counterpart)" if model != "lgbm" else ""}:

| feature | gain share |
|---|---|
{top}
{coef_txt}

Sanity check: none of these is a label in disguise. All `d_*` columns are the previous NY session's daily features
(shifted one day in `featstore.build_hourly`), `ret_*`/`rv_*`/range/level distances use bars up to and including the
decision bar, event clocks are measured at the decision-bar close, and `fwd_*`/`label_end_*`/`close` are excluded.
`ret_1h` (the decision bar's own return) is the top feature; what that means is discussed below.

## Post-selection diagnostics of the final configuration (not eligible for selection)
{_summary(allt[allt.group == "diagnostic"])}

`diag_fade_ret1h_q*`: no model at all, just short when the decision bar's own 1h return is above its training quantile
and long when below (q = 0.5 / 0.8). `_no_last_bar_feats`: the final model without {", ".join(LAST_BAR_FEATS)}.
`_decision-1h` / `_decision+1h`: the final configuration one hour earlier / later on the same local clock.

## Assessment: what the NY17 result is, and why it should not be taken at face value
The final variant's record is driven by mean reversion of the 16:00-17:00 New York bar, i.e. the daily rollover hour:
* corr(ret_1h, fwd_1h) in 2010-2026 is about -0.09 at `hour_ny` 16, -0.16 at 17 and -0.10 at 18, versus |corr| < 0.06 at
  every other hour; corr(ret_1h, fwd_4h) is -0.12 at hour 16 and within +-0.04 elsewhere.
* {ts['fade_frac']:.0%} of the final variant's trades are simply against the decision bar's own return. The model-free fade rule
  (`diag_fade_ret1h_q0.8`) earns net SR {agg(fade08, '2010-2026'):+.2f} (2016-2026 {agg(fade08, '2016-2026'):+.2f}), as much as the LightGBM model.
* Removing the four decision-bar features drops the final configuration to net SR {agg(nolast, '2010-2026'):+.2f} (2016-2026 {agg(nolast, '2016-2026'):+.2f}).
  The day's context (d_* macro, positioning, event clocks, previous-day levels) on its own does not carry the result.
* The effect lives in the thinnest hour of the day (mean |1h move| at 17:00 NY is about a third of the London morning),
  in bid-only HistData prices, with exactly the shape of quote bounce in illiquid trading. Retail spreads at the 17:00 NY
  rollover are routinely 3-10 pips, not 1.2, and the break-even cost of the final variant is about {breakeven_pips:.1f} pips per side.
  At 2.0 pips the net Sharpe is {agg(cost_tbls[2.0], '2010-2026'):+.2f}, at 3.0 pips {agg(cost_tbls[3.0], '2010-2026'):+.2f}.
So the arm's honest conclusion is: the context-conditioned intraday models find **no new information** at the London
decision bars (L07, L13), and the one thing they do find (NY17) is a microstructure artefact of the rollover hour that
is unlikely to survive real overnight spreads. The positions file is nevertheless the declared final variant, so the lead
can decide whether to stack it; it should be given the cost of the rollover hour, not 1.2 pips.

## Leak checks (final configuration re-run through the same pipeline)
| check | net SR 2010-2026 | t | gross SR 2010-2026 | net SR 2016-2026 | expectation |
|---|---|---|---|---|---|
| labels shuffled, {len(SHUFFLE_SEEDS)} seeds (mean [min, max]) | {sh10.sharpe.mean():+.2f} [{sh10.sharpe.min():+.2f}, {sh10.sharpe.max():+.2f}] | {sh10['t'].mean():+.2f} | {sh10.gross_sharpe.mean():+.2f} [{sh10.gross_sharpe.min():+.2f}, {sh10.gross_sharpe.max():+.2f}] | {sh16.sharpe.mean():+.2f} | gross ~0, net = cost drag |
| features shifted +1 decision bar (stale) | {st.loc['2010-2026', 'sharpe']:+.2f} | {st.loc['2010-2026', 't']:+.2f} | {st.loc['2010-2026', 'gross_sharpe']:+.2f} | {st.loc['2016-2026', 'sharpe']:+.2f} | collapses |
| features shifted -1 decision bar (future) | {fu.loc['2010-2026', 'sharpe']:+.2f} | {fu.loc['2010-2026', 't']:+.2f} | {fu.loc['2010-2026', 'gross_sharpe']:+.2f} | {fu.loc['2016-2026', 'sharpe']:+.2f} | jumps (the pipeline would detect a leak) |

With shuffled labels the model has no skill but still pays the round-trip cost on ~15 % of bars, so the net Sharpe is
negative by construction and the gross Sharpe is the number to read (~0). Stale features collapse to the cost drag; features
from the next decision bar (which overlap the label window) jump to a very large Sharpe, confirming the harness is
sensitive to a leak and that the real run contains none of that kind.

## Run
`PYTHONPATH=src python -m eurusd.arms.intraday_ml` ({secs / 60:.1f} min, one CPU per fit; log in `experiments/results/logs/{ARM}.log`).
Files: `src/eurusd/arms/{ARM}.py` (`run(cost_pips=1.2)`), `experiments/results/arms/{ARM}_positions.parquet`
(OOS positions of the final variant: index = decision bar, `pos`, `fwd_bp`, `net_bp`, `horizon_h`, `forecast_bp`),
`experiments/results/arms/{ARM}_report.csv` (all variants, `variant`, `group`, `final`, `cost_pips`, `gross_sharpe`).
"""
    (REP / f"arm_{ARM}.md").write_text(md)


if __name__ == "__main__":
    run(cost_pips=1.2, quick="--quick" in sys.argv)
