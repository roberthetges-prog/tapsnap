"""Catalogue T01-T18 / V01-V04 / P01-P12: grid on TRAIN, confirm chosen parameters on VALIDATE,
survival rules from eurusd.evaluate.  HOLDOUT is never touched.

Usage:  python experiments/12_trend_vol_pa.py [--part NAME] [family ...]
        python experiments/12_trend_vol_pa.py --merge            (merge part CSVs into trend_vol_pa.csv)

Extra care for limit-entry strategies (P07, P09, P10, P11, P01 'half'): the engine fills a limit and
allows a take-profit on the same bar even when the bar opened beyond the limit, which is optimistic.
Those trades are re-resolved with M1 data (`fix_limit_entries`): the first minute touching the limit is
the fill; TP counts only if touched in a later minute before the stop; otherwise the trade is closed at
the bar's close.  Statistics are recomputed after the fix.
"""
import sys, json, math, time, argparse, copy
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import numpy as np, pandas as pd
from eurusd.backtest import CostModel, BacktestResult, bootstrap_pvalue, PIP
from eurusd.evaluate import run_one, grid, neighbourhood_ok, verdict, RESULTS_DIR
from eurusd.data import load_ohlc
import eurusd.strategies_trend_pa as S  # registers strategies

COST = CostModel(spread_pips=1.0, slippage_pips=0.2)
NAN = math.nan
TF = {}
M1 = {}


def tf(name):
    if name not in TF:
        TF[name] = load_ohlc(name)
    return TF[name]


def m1():
    if "m1" not in M1:
        m = load_ohlc("M1")[["high", "low"]]
        M1["m1"] = m
    return M1["m1"]


LIMIT_FAMILIES = {"harmonic", "supply_demand", "order_block", "fvg_retrace", "pin_bar"}


def fix_limit_entries(res: BacktestResult, df: pd.DataFrame, cost: CostModel) -> tuple[BacktestResult, int]:
    """Re-resolve same-bar limit-fill + TP trades with M1 data (see module docstring)."""
    if res.tdf.empty:
        return res, 0
    o = df["open"].values
    c = df["close"].values
    idx = df.index
    spread = cost.spread_pips * PIP
    slip = cost.slippage_pips * PIP
    n_fixed = 0
    trades = res.trades
    for t in trades:
        if t.reason != "tp" or t.entry_i != t.exit_i:
            continue
        m = t.entry_i
        if t.side > 0:
            if not (t.entry < o[m] + spread - 1e-12):
                continue  # filled at the open: TP after the fill is certain
            limit = t.entry
        else:
            if not (t.entry > o[m] + 1e-12):
                continue
            limit = t.entry
        n_fixed += 1
        t1 = idx[m + 1] if m + 1 < len(idx) else idx[m] + (idx[m] - idx[m - 1])
        seg = m1().loc[idx[m]:t1 - pd.Timedelta(seconds=1)]
        hi, lo = seg["high"].values, seg["low"].values
        if t.side > 0:
            touch = np.flatnonzero(lo + spread <= limit)
        else:
            touch = np.flatnonzero(hi >= limit)
        new_exit, reason = None, None
        if len(touch):
            k = touch[0]
            if t.side > 0:
                tp_hit = np.flatnonzero(hi[k + 1:] >= t.tp)
                sl_hit = np.flatnonzero(lo[k + 1:] <= t.sl) if not math.isnan(t.sl) else np.array([])
            else:
                tp_hit = np.flatnonzero(lo[k + 1:] + spread <= t.tp)
                sl_hit = np.flatnonzero(hi[k + 1:] + spread >= t.sl) if not math.isnan(t.sl) else np.array([])
            i_tp = tp_hit[0] if len(tp_hit) else 10**9
            i_sl = sl_hit[0] if len(sl_hit) else 10**9
            if i_tp < i_sl:
                continue  # TP genuinely after the fill: keep
            if i_sl < 10**9:
                new_exit, reason = (t.sl - slip if t.side > 0 else t.sl + slip), "sl"
        if new_exit is None:
            new_exit, reason = (c[m] if t.side > 0 else c[m] + spread), "time"
        t.exit = new_exit
        t.reason = reason
        pnl = (t.exit - t.entry) * t.side
        t.pips = pnl / PIP
        risk = abs(t.entry - t.sl) if not math.isnan(t.sl) else math.nan
        t.r = pnl / risk if risk and risk > 0 else math.nan
    return BacktestResult(trades, df), n_fixed


def evaluate(df, strat, params, period, fix_limits=False):
    s, res = run_one(df, strat, params, period, COST)
    n_fixed = 0
    if fix_limits and s.get("trades", 0):
        res, n_fixed = fix_limit_entries(res, res.df, COST)
        s2 = res.summary()
        s2.update({"strategy": strat, "period": period, "params": json.dumps(params, default=str)})
        by = res.by_year()
        s2["years_positive"] = float((by["sum_r"] > 0).mean())
        s2["p_boot"] = bootstrap_pvalue(res.tdf["r"].values, n_boot=500)
        s = s2
    s["n_limit_fixed"] = n_fixed
    return s, res


# --------------------------------------------------------------------------- families
# name: (catalogue id, strategy, timeframe, grid)
FAMILIES = {
    # ---- breakout / trend
    "t01_turtle_d1": ("T01", "turtle", "D1", dict(entry_n=[20], exit_n=[10], atr_n=[20], sl_atr=[1.5, 2.0, 3.0])),
    "t01_turtle_h4": ("T01", "turtle", "H4", dict(entry_n=[20], exit_n=[10], atr_n=[20], sl_atr=[1.5, 2.0, 3.0])),
    "t02_turtle55_d1": ("T02", "turtle", "D1", dict(entry_n=[55], exit_n=[20], atr_n=[20], sl_atr=[1.5, 2.0, 3.0])),
    "t03_macross_d1": ("T03", "ma_cross_exit", "D1", dict(fast=[10, 50], slow=[20, 200], kind=["sma", "ema"], sl_atr=[NAN, 3.0])),
    "t04_emapb_h1": ("T04", "ema_pullback", "H1", dict(sl_mode=["swing", "atr"], rr=[1.5, 2.0, 3.0, NAN], lookback=[5])),
    "t04_emapb_h4": ("T04", "ema_pullback", "H4", dict(sl_mode=["swing", "atr"], rr=[1.5, 2.0, 3.0, NAN], lookback=[5])),
    "t05_macdrsi_h1": ("T05", "macd_rsi", "H1", dict(use_rsi=[True, False], sl_pips=[45, 30, 60], tp_pips=[90, 60], exit_on_cross=[False])),
    "t05_macdrsi_d1": ("T05", "macd_rsi", "D1", dict(use_rsi=[True, False], sl_pips=[100, 200], tp_pips=[0], exit_on_cross=[True])),
    "t07_ichimoku_d1": ("T07", "ichimoku_trend", "D1", dict(variant=["full", "chikou"], sl_mode=["kijun", "cloud"])),
    "t07_ichimoku_h4": ("T07", "ichimoku_trend", "H4", dict(variant=["full", "chikou"], sl_mode=["kijun", "cloud"])),
    "t08_squeeze_h1": ("T08", "ttm_squeeze", "H1", dict(direction=["mom", "candle"], sl_mode=["atr", "kc"], tp_atr=[2.0, 3.0, NAN], max_hold=[60])),
    "t08_squeeze_h4": ("T08", "ttm_squeeze", "H4", dict(direction=["mom", "candle"], sl_mode=["atr", "kc"], tp_atr=[2.0, 3.0, NAN], max_hold=[60])),
    "t08_squeeze_d1": ("T08", "ttm_squeeze", "D1", dict(direction=["mom", "candle"], sl_mode=["atr", "kc"], tp_atr=[2.0, 3.0, NAN], max_hold=[40])),
    "t09_insidebar_d1": ("T09", "inside_bar_breakout", "D1", dict(sl_mode=["inside", "mother"], rr=[1.0, 2.0], tp_mode=["rr", "mother"], hold_bars=[5], expiry_bars=[1])),
    "t09_insidebar_h4": ("T09", "inside_bar_breakout", "H4", dict(sl_mode=["inside", "mother"], rr=[1.0, 2.0], tp_mode=["rr", "mother"], hold_bars=[30], expiry_bars=[6])),
    "t10_nr_d1": ("T10", "nr_breakout", "D1", dict(pattern=["nr7", "idnr4"], exit=["day_close", "adr"], hold_bars=[3])),
    "t11_supertrend_h1": ("T11", "supertrend_flip", "H1", dict(n=[7, 10, 14], k=[2.0, 3.0, 4.0])),
    "t11_supertrend_h4": ("T11", "supertrend_flip", "H4", dict(n=[7, 10, 14], k=[2.0, 3.0, 4.0])),
    "t11_supertrend_d1": ("T11", "supertrend_flip", "D1", dict(n=[7, 10, 14], k=[2.0, 3.0, 4.0])),
    "t12_psar_m30": ("T12", "psar_flip", "M30", dict(af0=[0.01, 0.02, 0.03], step=[0.02], af_max=[0.1, 0.2])),
    "t12_psar_d1": ("T12", "psar_flip", "D1", dict(af0=[0.01, 0.02, 0.03], step=[0.02], af_max=[0.1, 0.2])),
    "t13_ha_h1": ("T13", "heikin_ashi_trend", "H1", dict(filt=["ema100", "ema2050"], sl_mode=["atr", "swing"], exit=["ha", "ema"], confirm=[2, 3])),
    "t13_ha_h4": ("T13", "heikin_ashi_trend", "H4", dict(filt=["ema100", "ema2050"], sl_mode=["atr", "swing"], exit=["ha", "ema"], confirm=[2, 3])),
    "t14_trail_h4": ("T14", "trail_exit_entry", "H4", dict(host=["donchian", "emacross"], trail=["chandelier", "atr"], ch_k=[2.0, 3.0], k=[1.5, 3.0])),
    "t14_trail_d1": ("T14", "trail_exit_entry", "D1", dict(host=["donchian", "emacross"], trail=["chandelier", "atr"], ch_k=[2.0, 3.0], k=[1.5, 3.0])),
    "t15_lw_d1": ("T15", "lw_vol_breakout", "D1", dict(k=[0.25, 0.5, 0.75], range_lookback=[1, 3], sl_mult=[1.0, 2.0], tp_mult=[2.0])),
    "t15_lw_m5": ("T15", "lw_vol_breakout", "M5", dict(k=[0.25, 0.5], day_start=[0, 22, 7], sl_mult=[2.0], tp_mult=[2.0], exit_hour=[21])),
    "t16_pdhl_h1": ("T16", "pdh_pdl_breakout", "H1", dict(sl_mode=["pips", "mid"], sl_pips=[25], rr=[1.0, 2.0, NAN])),
    "t16_pdhl_m15": ("T16", "pdh_pdl_breakout", "M15", dict(sl_mode=["pips", "mid"], sl_pips=[25], rr=[1.0, 2.0, NAN])),
    "t17_tsmom_d1": ("T17", "tsmom", "D1", dict(lookback_m=[1, 3, 12], variant=["single"], use_carry=[True, False])),
    "t17_tsmom_combo_d1": ("T17", "tsmom", "D1", dict(variant=["combo"], use_carry=[True, False])),
    "t18_fractal_h1": ("T18", "fractal_breakout", "H1", dict(k=[2, 3], sl_mode=["pips", "fractal"], sl_pips=[30], tp_pips=[40, 60])),
    # ---- volatility module V01 (ATR stop/target pairs on a squeeze entry)
    "v01_atr_sqz_h4": ("V01", "ttm_squeeze", "H4", dict(direction=["mom"], sl_mode=["atr"], sl_atr=[1.0, 1.5, 2.0], tp_atr=[2.0, 3.0, 4.0], max_hold=[60])),
    # ---- price action
    "p01_pin_h4": ("P01", "pin_bar", "H4", dict(trend=["ema", "none", "counter"], rr=[1.5, 2.0, 3.0], entry=["close", "half"], ema_n=[50], max_hold=[20])),
    "p01_pin_d1": ("P01", "pin_bar", "D1", dict(trend=["ema", "none", "counter"], rr=[1.5, 2.0, 3.0], entry=["close", "half"], ema_n=[50], max_hold=[20])),
    "p02_engulf_h1": ("P02", "engulfing", "H1", dict(strict=[False, True], rr=[1.0, 2.0], direction=["reversal", "momentum"], max_hold=[24])),
    "p02_engulf_h4": ("P02", "engulfing", "H4", dict(strict=[False, True], rr=[1.0, 2.0], direction=["reversal", "momentum"], max_hold=[20])),
    "p02_engulf_d1": ("P02", "engulfing", "D1", dict(strict=[False, True], rr=[1.0, 2.0], direction=["reversal", "momentum"], max_hold=[10])),
    "p03_outside_h1": ("P03", "outside_bar", "H1", dict(rr=[1.0, 1.5, 2.0], trend=["none", "ema"], ema_n=[200], max_hold=[24])),
    "p03_outside_h4": ("P03", "outside_bar", "H4", dict(rr=[1.0, 1.5, 2.0], trend=["none", "ema"], ema_n=[200], max_hold=[20])),
    "p03_outside_d1": ("P03", "outside_bar", "D1", dict(rr=[1.0, 1.5, 2.0], trend=["none", "ema"], ema_n=[200], max_hold=[10])),
    "p04_dtb_h4": ("P04", "double_top_bottom", "H4", dict(k=[3, 5], tol_atr=[0.3, 0.5, 1.0], tp_mode=["height", "rr"])),
    "p04_dtb_d1": ("P04", "double_top_bottom", "D1", dict(k=[3, 5], tol_atr=[0.3, 0.5, 1.0], tp_mode=["height", "rr"])),
    "p05_hs_h4": ("P05", "head_shoulders", "H4", dict(k=[3, 5], sym_tol=[0.3, 0.5], tp_mode=["height", "rr"])),
    "p05_hs_d1": ("P05", "head_shoulders", "D1", dict(k=[3, 5], sym_tol=[0.3, 0.5], tp_mode=["height", "rr"])),
    "p06_flag_m15": ("P06", "flag_breakout", "M15", dict(pole_atr=[1.5, 2.5], pole_bars=[5, 10], tp_mode=["pole", "rr"])),
    "p06_flag_h1": ("P06", "flag_breakout", "H1", dict(pole_atr=[1.5, 2.5], pole_bars=[5, 10], tp_mode=["pole", "rr"])),
    "p06_flag_h4": ("P06", "flag_breakout", "H4", dict(pole_atr=[1.5, 2.5], pole_bars=[5, 10], tp_mode=["pole", "rr"])),
    "p07_harmonic_h1": ("P07", "harmonic", "H1", dict(pattern=["gartley", "bat", "butterfly", "crab"], tp_level=[0.382, 0.618], k=[5])),
    "p07_harmonic_h4": ("P07", "harmonic", "H4", dict(pattern=["gartley", "bat", "butterfly", "crab"], tp_level=[0.382, 0.618], k=[5])),
    "p08_fib_h1": ("P08", "fib_pullback", "H1", dict(level=[0.382, 0.5, 0.618], target=[1.0, 1.272], trend=["ema", "none"])),
    "p08_fib_h4": ("P08", "fib_pullback", "H4", dict(level=[0.382, 0.5, 0.618], target=[1.0, 1.272], trend=["ema", "none"])),
    "p08_fib_d1": ("P08", "fib_pullback", "D1", dict(level=[0.382, 0.5, 0.618], target=[1.0, 1.272], trend=["ema", "none"])),
    "p09_sd_h1": ("P09", "supply_demand", "H1", dict(departure_atr=[2.0, 3.0], rr=[2.0, 3.0], base_atr=[0.6], max_base=[3])),
    "p09_sd_h4": ("P09", "supply_demand", "H4", dict(departure_atr=[2.0, 3.0], rr=[2.0, 3.0], base_atr=[0.6], max_base=[3])),
    "p10_ob_m15": ("P10", "order_block", "M15", dict(displacement_atr=[1.5, 2.5], zone=["open_low", "full"], rr=[2.0])),
    "p10_ob_h1": ("P10", "order_block", "H1", dict(displacement_atr=[1.5, 2.5], zone=["open_low", "full"], rr=[2.0])),
    "p10_ob_h4": ("P10", "order_block", "H4", dict(displacement_atr=[1.5, 2.5], zone=["open_low", "full"], rr=[2.0])),
    "p11_fvg_m5": ("P11", "fvg_retrace", "M5", dict(entry_level=["top", "mid"], min_gap_atr=[0.2, 0.5], rr=[2.0])),
    "p11_fvg_m15": ("P11", "fvg_retrace", "M15", dict(entry_level=["top", "mid"], min_gap_atr=[0.2, 0.5], rr=[2.0])),
    "p11_fvg_h1": ("P11", "fvg_retrace", "H1", dict(entry_level=["top", "mid"], min_gap_atr=[0.2, 0.5], rr=[2.0])),
    "p12_wyckoff_m30": ("P12", "wyckoff_spring", "M30", dict(max_range_atr=[3.0, 5.0], reclaim_bars=[1, 3], tp_mode=["range", "rr"])),
    "p12_wyckoff_h4": ("P12", "wyckoff_spring", "H4", dict(max_range_atr=[3.0, 5.0], reclaim_bars=[1, 3], tp_mode=["range", "rr"])),
}

# ---- phase 2: filters (T06, V02, V03, V04) on fixed host presets (chosen from phase-1 TRAIN results)
HOSTS = {
    "turtle_d1": ("D1", "turtle", dict(entry_n=20, exit_n=10, atr_n=20, sl_atr=2.0)),
    "turtle_h4": ("H4", "turtle", dict(entry_n=20, exit_n=10, atr_n=20, sl_atr=2.0)),
    "ichimoku_d1": ("D1", "ichimoku_trend", dict(variant="full", sl_mode="kijun")),
    "emapb_h4": ("H4", "ema_pullback", dict(sl_mode="atr", rr=2.0, lookback=5)),
    "supertrend_h4": ("H4", "supertrend_flip", dict(n=10, k=3.0)),
    "macdrsi_h1": ("H1", "macd_rsi", dict(use_rsi=True, sl_pips=45, tp_pips=90, exit_on_cross=False)),
    "nr7_d1": ("D1", "nr_breakout", dict(pattern="nr7", exit="day_close", hold_bars=3)),
    "insidebar_d1": ("D1", "inside_bar_breakout", dict(sl_mode="inside", rr=2.0, tp_mode="rr", hold_bars=5, expiry_bars=1)),
    "lw_d1": ("D1", "lw_vol_breakout", dict(k=0.5, range_lookback=1, sl_mult=2.0, tp_mult=2.0)),
}


def filter_family(cid, name, hosts, filt, extra):
    """One family per (filter, host): the grid varies the filter parameters only."""
    out = {}
    for hname in hosts:
        tfname, strat, hp = HOSTS[hname]
        g = dict(host=[strat], hp=[hp], filt=[filt])
        g.update(extra)
        out[f"{name}_{hname}"] = (cid, "filtered", tfname, g)
    return out


FAMILIES.update(filter_family("T06", "t06_adx", ["turtle_d1", "turtle_h4", "emapb_h4", "supertrend_h4", "macdrsi_h1"], "adx",
                              dict(adx_thr=[20, 25, 30], di_agree=[True])))
FAMILIES.update(filter_family("V02", "v02_vol", ["insidebar_d1", "nr7_d1", "lw_d1", "turtle_d1"], "vol",
                              dict(mode=["contraction", "expansion"], ratio=[0.8, 1.2])))
FAMILIES.update(filter_family("V03", "v03_garch", ["turtle_d1", "ichimoku_d1", "emapb_h4", "supertrend_h4"], "garch",
                              dict(regime_keep=[(1,), (0, 1), (1, 2), (0,), (2,)])))
FAMILIES.update(filter_family("V04", "v04_vix", ["turtle_d1", "ichimoku_d1", "nr7_d1", "insidebar_d1"], "vix",
                              dict(vix_mode=["low", "mid", "high", "notstress"], vix_lo=[15.0], vix_hi=[30.0])))

PHASE2 = [f for f in FAMILIES if f.startswith(("t06_", "v02_", "v03_", "v04_"))]


def clean_params(p):
    return {k: (v if not (isinstance(v, float) and math.isnan(v)) else NAN) for k, v in p.items()}


def run_family(fam, log):
    cid, strat, tfname, g = FAMILIES[fam]
    df = tf(tfname)
    fix = strat in LIMIT_FAMILIES
    t0 = time.time()
    rows = []
    combos = grid(g)
    for p in combos:
        s, _ = evaluate(df, strat, p, "train", fix)
        rows.append(s)
    tr = pd.DataFrame(rows)
    tr.to_csv(RESULTS_DIR / f"tvp_{fam}_train.csv", index=False)
    if "trades" not in tr or tr["trades"].max() == 0:
        row = dict(family=fam, id=cid, strategy=strat, tf=tfname, params="{}", grid_points=len(tr), train_trades=0,
                   survives=False, reason="no trades on train", secs=round(time.time() - t0))
        print(json.dumps(row, default=str), file=log, flush=True)
        return row
    min_tr = 50 if (tr["trades"] >= 50).any() else 1
    cand = tr[tr["trades"] >= min_tr].copy()
    metric = np.where(cand["has_r"].fillna(True), cand["avg_r"], cand["avg_pips"])
    score = metric * np.sqrt(cand["trades"].clip(lower=1))
    best = cand.loc[score.idxmax()]
    bp = clean_params(json.loads(best["params"]))
    # tuples in grids (regime_keep) come back as lists from json
    for k, v in bp.items():
        if isinstance(v, list):
            bp[k] = tuple(v)
    n_ok, n_med = neighbourhood_ok(tr, bp, g)
    val, vres = evaluate(df, strat, bp, "validate", fix)
    ok, why = verdict(best, val, n_ok)
    has_r = bool(best.get("has_r", True))
    row = dict(family=fam, id=cid, strategy=strat, tf=tfname, params=json.dumps(bp, default=str), grid_points=len(tr),
               has_r=has_r,
               train_trades=int(best["trades"]), train_win=best["win_rate"], train_avg_r=best["avg_r"], train_avg_pips=best["avg_pips"],
               train_pf=best["profit_factor"] if has_r else best["profit_factor_pips"],
               train_t=best["t_stat"] if has_r else best["t_stat_pips"], train_years_pos=best.get("years_positive", NAN),
               neigh_median=n_med, neigh_ok=n_ok,
               val_trades=val.get("trades", 0), val_win=val.get("win_rate", NAN), val_avg_r=val.get("avg_r", NAN),
               val_avg_pips=val.get("avg_pips", NAN),
               val_pf=val.get("profit_factor", NAN) if has_r else val.get("profit_factor_pips", NAN),
               val_t=val.get("t_stat", NAN) if has_r else val.get("t_stat_pips", NAN),
               val_years_pos=val.get("years_positive", NAN), val_sl_rate=val.get("sl_rate", NAN),
               n_limit_fixed=int(best.get("n_limit_fixed", 0)) + int(val.get("n_limit_fixed", 0)),
               survives=ok, reason=why, secs=round(time.time() - t0))
    print(json.dumps(row, default=str), file=log, flush=True)
    # sanity sample of validate trades
    if val.get("trades", 0):
        t = vres.tdf[["entry_time", "exit_time", "side", "entry", "exit", "sl", "tp", "reason", "pips", "r", "tag"]]
        print(f"--- {fam} validate sample ({val['trades']} trades):", file=log)
        print(t.head(3).to_string(), file=log)
        print(t.sample(min(3, len(t)), random_state=0).to_string(), file=log, flush=True)
    return row


def merge():
    parts = sorted(RESULTS_DIR.glob("trend_vol_pa_part_*.csv"))
    out = pd.concat([pd.read_csv(p) for p in parts], ignore_index=True)
    out = out.drop_duplicates("family", keep="last")
    out["order"] = out["id"].str[0].map({"T": 0, "V": 1, "P": 2}) * 1000 + out["id"].str[1:].astype(int)
    out = out.sort_values(["order", "family"]).drop(columns="order")
    out.to_csv(RESULTS_DIR / "trend_vol_pa.csv", index=False)
    print(out[["family", "id", "tf", "train_trades", "train_avg_r", "train_t", "val_trades", "val_avg_r", "val_t", "val_pf",
               "val_years_pos", "survives", "reason"]].to_string())


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--part", default="a")
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--phase2", action="store_true")
    ap.add_argument("fams", nargs="*")
    a = ap.parse_args()
    if a.merge:
        merge()
        sys.exit()
    fams = a.fams or ([f for f in FAMILIES if f in PHASE2] if a.phase2 else [f for f in FAMILIES if f not in PHASE2])
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (RESULTS_DIR / "logs").mkdir(exist_ok=True)
    log = open(RESULTS_DIR / "logs" / f"tvp_{a.part}.log", "a")
    path = RESULTS_DIR / f"trend_vol_pa_part_{a.part}.csv"
    rows = []
    for f in fams:
        try:
            rows.append(run_family(f, log))
        except Exception as e:  # keep going, record the failure
            import traceback
            traceback.print_exc(file=log)
            rows.append(dict(family=f, id=FAMILIES[f][0], strategy=FAMILIES[f][1], tf=FAMILIES[f][2], survives=False, reason=f"ERROR {e}"))
        out = pd.DataFrame(rows)
        if path.exists():
            old = pd.read_csv(path)
            out = pd.concat([old[~old.family.isin(out.family)], out])
        out.to_csv(path, index=False)
    print("done", a.part, file=log, flush=True)
