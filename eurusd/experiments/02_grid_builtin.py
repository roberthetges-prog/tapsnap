"""Grid-search the built-in strategy families on TRAIN, confirm the chosen
parameters on VALIDATE, apply the survival rules. Holdout is NOT touched here.
Usage: python experiments/02_grid_builtin.py [family ...]
"""
import sys, json, math, time
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import numpy as np, pandas as pd
from eurusd.backtest import CostModel
from eurusd.evaluate import run_grid, run_one, neighbourhood_ok, verdict, RESULTS_DIR

COST = CostModel(spread_pips=1.0, slippage_pips=0.2)
DATA = "/home/user/tapsnap/eurusd/data/processed/"
TF = {}
def tf(name):
    if name not in TF:
        TF[name] = pd.read_parquet(DATA + f"EURUSD_{name}.parquet")
    return TF[name]

FAMILIES = {
    # name: (strategy, timeframe, grid)
    "arb_m15": ("asian_range_breakout", "M15", dict(start=[0, 1], end=[6, 7, 8], entry_until=[10, 12, 14], sl_mode=["range"], sl_val=[0.5, 1.0], tp_rr=[1.0, 1.5, 2.0, 3.0], exit_hour=[16, 20], buffer_pips=[2.0])),
    "arb_m15_pips": ("asian_range_breakout", "M15", dict(start=[0], end=[7, 8], entry_until=[12], sl_mode=["pips"], sl_val=[15, 25, 35], tp_rr=[1.0, 2.0, 3.0], exit_hour=[16, 20], buffer_pips=[2.0])),
    "orb_ny_m5": ("opening_range_breakout", "M5", dict(open_hour=[13, 14], open_minute=[30], range_minutes=[15, 30, 60], entry_until_hour=[17], sl_mode=["range"], sl_val=[1.0], tp_rr=[1.0, 2.0, 3.0], exit_hour=[20])),
    "orb_london_m5": ("opening_range_breakout", "M5", dict(open_hour=[7, 8], open_minute=[0], range_minutes=[15, 30, 60], entry_until_hour=[12], sl_mode=["range"], sl_val=[1.0], tp_rr=[1.0, 2.0, 3.0], exit_hour=[16, 20])),
    "ma_h1": ("ma_cross", "H1", dict(fast=[5, 10, 20, 50], slow=[20, 50, 100, 200], kind=["ema", "sma"], sl_atr=[1.5, 3.0], tp_atr=[3.0, 6.0, math.nan])),
    "ma_h4": ("ma_cross", "H4", dict(fast=[5, 10, 20], slow=[20, 50, 100], kind=["ema"], sl_atr=[2.0, 3.0], tp_atr=[4.0, math.nan])),
    "ma_d1": ("ma_cross", "D1", dict(fast=[5, 10, 20, 50], slow=[20, 50, 100, 200], kind=["ema", "sma"], sl_atr=[2.0, 4.0], tp_atr=[math.nan])),
    "don_h1": ("donchian_breakout", "H1", dict(n=[20, 55, 100, 200], sl_atr=[2.0, 3.0], tp_atr=[math.nan, 4.0], atr_n=[14])),
    "don_h4": ("donchian_breakout", "H4", dict(n=[10, 20, 55], sl_atr=[2.0, 3.0], tp_atr=[math.nan, 4.0])),
    "don_d1": ("donchian_breakout", "D1", dict(n=[10, 20, 55, 100], sl_atr=[2.0, 3.0], tp_atr=[math.nan])),
    "macd_h1": ("macd_trend", "H1", dict(fast=[12], slow=[26], signal=[9], sl_atr=[1.5, 2.0, 3.0], tp_atr=[2.0, 3.0, 6.0], trend_ma=[100, 200])),
    "macd_h4": ("macd_trend", "H4", dict(fast=[12], slow=[26], signal=[9], sl_atr=[2.0, 3.0], tp_atr=[3.0, 6.0], trend_ma=[50, 200])),
    "st_h1": ("supertrend_follow", "H1", dict(n=[7, 10, 14], k=[2.0, 3.0, 4.0], sl_atr=[2.0, 3.0])),
    "st_h4": ("supertrend_follow", "H4", dict(n=[7, 10, 14], k=[2.0, 3.0], sl_atr=[2.0, 3.0])),
    "rsi_h1": ("rsi_reversion", "H1", dict(n=[2, 3, 14], lo=[10, 20, 30], hi=[70, 80, 90], sl_atr=[1.5, 3.0], tp_atr=[0.5, 1.0, 2.0], max_hold=[6, 24], use_trend=[True, False])),
    "rsi_d1": ("rsi_reversion", "D1", dict(n=[2, 3], lo=[5, 10, 20], hi=[80, 90, 95], sl_atr=[2.0, 3.0], tp_atr=[1.0, 2.0], max_hold=[3, 5, 10], use_trend=[True, False])),
    "bb_h1": ("bollinger_fade", "H1", dict(n=[20, 50], k=[2.0, 2.5, 3.0], sl_atr=[1.5, 2.5], tp=["mid"], max_hold=[12, 48])),
    "bb_m15": ("bollinger_fade", "M15", dict(n=[20, 50], k=[2.0, 2.5, 3.0], sl_atr=[1.5, 2.5], tp=["mid"], max_hold=[16, 64])),
    "piv_m15": ("pivot_bounce", "M15", dict(level=["s1", "s2r2"], sl_pips=[10, 15, 25], day_start=[22], start_hour=[7], end_hour=[16, 20], exit_hour=[20])),
}

def run_family(fam):
    strat, tfname, grid = FAMILIES[fam]
    df = tf(tfname)
    t0 = time.time()
    tr = run_grid(df, strat, grid, "train", COST, tag=fam, verbose=False)
    tr = tr[tr["trades"] >= 100] if (tr["trades"] >= 100).any() else tr
    score = tr["avg_r"] * np.sqrt(tr["trades"].clip(lower=1))  # ~ t-stat but favours more trades
    best = tr.loc[score.idxmax()]
    bp = json.loads(best["params"])
    bp = {k: (v if not (isinstance(v, float) and math.isnan(v)) else math.nan) for k, v in bp.items()}
    n_ok, n_med = neighbourhood_ok(tr, bp, grid)
    val, _ = run_one(df, strat, bp, "validate", COST)
    ok, why = verdict(best, val, n_ok)
    row = dict(family=fam, strategy=strat, tf=tfname, params=json.dumps(bp), grid_points=len(tr),
               train_trades=int(best["trades"]), train_avg_r=best["avg_r"], train_t=best["t_stat"], train_pf=best["profit_factor"], train_years_pos=best.get("years_positive", np.nan),
               neigh_median_avg_r=n_med, val_trades=val.get("trades", 0), val_avg_r=val.get("avg_r", np.nan), val_t=val.get("t_stat", np.nan), val_pf=val.get("profit_factor", np.nan),
               val_years_pos=val.get("years_positive", np.nan), survives=ok, reason=why, secs=round(time.time() - t0))
    print(json.dumps(row, default=str), flush=True)
    return row

if __name__ == "__main__":
    fams = sys.argv[1:] or list(FAMILIES)
    rows = [run_family(f) for f in fams]
    out = pd.DataFrame(rows)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    path = RESULTS_DIR / "builtin_summary.csv"
    if path.exists():
        old = pd.read_csv(path)
        out = pd.concat([old[~old.family.isin(out.family)], out])
    out.to_csv(path, index=False)
    print(out.to_string())
