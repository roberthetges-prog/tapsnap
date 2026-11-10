"""Catalogue entries M01-M15 (mean reversion) and Q01-Q06 (systematic / vendor audits).

TRAIN 2003-2015: grid-search (small grids) -> pick best by t-stat (min trades) -> parameter neighbourhood
VALIDATE 2016-2022: one run per family with the chosen parameters -> verdict.  HOLDOUT (2023+) is never read.

Usage:  python experiments/13_meanrev_systematic.py [family ...] [--stats] [--ml] [--merge]
Results: experiments/results/meanrev_systematic.csv (one row per family) and the per-family grid CSVs
written by run_grid; the report is reports/catalogue_meanrev_systematic.md.
"""
import sys, json, math, time, warnings
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
from eurusd.data import load_ohlc
from eurusd.backtest import CostModel, run_backtest
from eurusd.evaluate import run_grid, run_one, neighbourhood_ok, verdict, RESULTS_DIR, slice_period, SPLITS
from eurusd.strategies import REGISTRY
from eurusd import features as F
import eurusd.strategies_meanrev as SM  # registers the strategies

COST = CostModel(spread_pips=1.0, slippage_pips=0.2)
NAN = math.nan
OUT = RESULTS_DIR / "meanrev_systematic.csv"
PIP = 0.0001
pd.set_option("display.width", 250); pd.set_option("display.max_columns", 40)

_TF = {}
def tf(name):
    """Timeframe frame; D1 = UTC calendar days without the Sunday/Saturday stub bars."""
    if name not in _TF:
        d = load_ohlc(name)
        if name == "D1":
            d = d[d.index.dayofweek < 5]
        _TF[name] = d
    return _TF[name]


# ------------------------------------------------------------------ families
# id: (catalogue id, strategy, timeframe, grid, min_train_trades, one_at_a_time, description)
FAMILIES = {
    "M01_crsi2_d1": ("M01", "connors_rsi2", "D1", dict(thr=[5, 10], exit_on_trend_cross=[True, False], sl_atr=[0, 2.0], sides=["both", "long"]), 30, True,
                     "Connors RSI(2): long close>SMA200 & RSI2<thr (short mirrored), exit first close>SMA5 (opt. also when close<SMA200); no stop (sl_atr=0) / 2xATR stop"),
    "M02_rsi14_d1": ("M02", "rsi_cross_back", "D1", dict(exit_rsi=[50, 60], sl_atr=[1.5, 3.0], tp_mode=["rsi", "bbmid"], max_hold=[10, 30]), 30, True,
                     "RSI(14) crosses back above 30 / below 70; stop k x ATR14; exit RSI>=exit_rsi or 20-bar BB mid"),
    "M02_rsi14_h4": ("M02", "rsi_cross_back", "H4", dict(exit_rsi=[50, 60], sl_atr=[1.5, 3.0], tp_mode=["rsi", "bbmid"], max_hold=[18, 60]), 50, True, "as M02_rsi14_d1 on H4"),
    "M03_bb_d1": ("M03", "bb_fade_cross", "D1", dict(rsi_filter=[False, True], sl_mode=["atr", "band"], sl_val=[1.0, 2.0], max_hold=[20, 40]), 30, True,
                  "BB(20,2) fade: close<lower (opt RSI14<30), exit first close>mid; stop k x ATR or k x band width"),
    "M03_bb_h1": ("M03", "bb_fade_cross", "H1", dict(rsi_filter=[False, True], sl_mode=["atr", "band"], sl_val=[1.0, 2.0], max_hold=[24, 72]), 50, True, "as M03_bb_d1 on H1"),
    "M03_bb_m1": ("M03", "bb_fade_cross", "M1", dict(rsi_filter=[True], k=[2.0, 2.5], sl_mode=["atr"], sl_val=[2.0], max_hold=[60, 240]), 50, True, "NautilusTrader-style BB+RSI fade on M1"),
    "M04_z_h1": ("M04", "zscore_reentry", "H1", dict(entry_z=[2.0, 2.5], stop_mode=["z", "atr"], stop_val=[2.0, 3.0], max_hold=[24, 48]), 50, True,
                 "z=(close-SMA20)/sd20; enter when z crosses back inside +/-entry_z, exit z crosses 0; stop at z=+/-stop_val or stop_val x ATR"),
    "M04_z_d1": ("M04", "zscore_reentry", "D1", dict(entry_z=[2.0, 2.5], stop_mode=["z", "atr"], stop_val=[2.0, 3.0], max_hold=[10, 20]), 30, True, "as M04_z_h1 on D1"),
    "M04_z_m5": ("M04", "zscore_reentry", "M5", dict(entry_z=[2.0, 2.5], stop_mode=["z"], stop_val=[3.0], max_hold=[48]), 50, True, "as M04_z_h1 on M5"),
    "M05_classic_fade": ("M05", "pivot_levels", "H1", dict(ptype=["classic"], mode=["fade"], entry_style=["limit", "reject"], day_start=[0, 22], require_open_inside=[True, False], sl_frac=[0.5, 1.0]), 50, True,
                         "classic pivots: buy S1 / sell R1 (limit at level or rejection bar), stop sl_frac x distance to S2/R2, target PP, 07-16 UTC entries, flat 20 UTC"),
    "M05_classic_break": ("M05", "pivot_levels", "H1", dict(ptype=["classic"], mode=["break"], entry_style=["close", "limit"], day_start=[0, 22], require_open_inside=[True, False], sl_frac=[0.5, 1.0]), 50, True,
                          "classic pivots: buy close above R1 (or buy-stop at R1), stop sl_frac x distance back to PP, target R2"),
    "M05_classic_fade_m15": ("M05", "pivot_levels", "M15", dict(ptype=["classic"], mode=["fade"], entry_style=["limit", "reject"], day_start=[0, 22], require_open_inside=[True], sl_frac=[0.5]), 50, True, "M05 fade on M15"),
    "M06_fib_fade": ("M06", "pivot_levels", "H1", dict(ptype=["fib"], mode=["fade"], entry_style=["limit", "reject"], day_start=[0], require_open_inside=[True, False], sl_frac=[0.5, 1.0]), 50, True, "Fibonacci pivots (0.382/0.618/1.0 x range), fade S1/R1 -> PP"),
    "M06_fib_break": ("M06", "pivot_levels", "H1", dict(ptype=["fib"], mode=["break"], entry_style=["close", "limit"], day_start=[0], require_open_inside=[True, False], sl_frac=[0.5, 1.0]), 50, True, "Fibonacci pivots, break R1 -> R2"),
    "M07_cam_fade": ("M07", "pivot_levels", "H1", dict(ptype=["camarilla"], mode=["fade"], entry_style=["limit", "reject"], cam_tp=["c", "opp"], day_start=[0, 22], require_open_inside=[True, False]), 50, True,
                     "Camarilla: sell H3 / buy L3, stop beyond H4/L4 (+2 pips), target prev close ('c') or opposite L3/H3 ('opp')"),
    "M07_cam_fade_m15": ("M07", "pivot_levels", "M15", dict(ptype=["camarilla"], mode=["fade"], entry_style=["limit"], cam_tp=["c", "opp"], day_start=[0, 22], require_open_inside=[True, False]), 50, True, "M07 fade on M15"),
    "M07_cam_break": ("M07", "pivot_levels", "H1", dict(ptype=["camarilla"], mode=["break"], entry_style=["limit", "close"], tp_rng=[0.5, 1.0], day_start=[0, 22], require_open_inside=[True, False]), 50, True,
                      "Camarilla: stop order at H4/L4 (or close beyond), stop back at H3/L3, target entry +/- tp_rng x prev range"),
    "M08_woodie_fade": ("M08", "pivot_levels", "H1", dict(ptype=["woodie", "woodie_open"], mode=["fade"], entry_style=["limit", "reject"], day_start=[0], require_open_inside=[True], sl_frac=[0.5, 1.0]), 50, True,
                        "Woodie PP=(H+L+2C)/4 (or 2 x today's open), fade S1/R1 -> PP"),
    "M08_woodie_break": ("M08", "pivot_levels", "H1", dict(ptype=["woodie", "woodie_open"], mode=["break"], entry_style=["close", "limit"], day_start=[0], require_open_inside=[True], sl_frac=[0.5, 1.0]), 50, True, "Woodie pivots, break R1 -> R2"),
    "M09_rn_fade": ("M09", "round_number", "M15", dict(mode=["fade"], levels=["00", "50", "placebo"], sl_pips=[15], tp_pips=[25, 50], lookback=[24, 96]), 50, True,
                    "fade first touch (none in previous `lookback` bars) of next 00 (or 00/50, or placebo 25/75) level, stop 15 pips beyond, target tp_pips; 07-20 UTC"),
    "M09_rn_break": ("M09", "round_number", "M15", dict(mode=["break"], levels=["00", "50", "placebo"], confirm_pips=[12], tp_pips=[50, 100], lookback=[24, 96]), 50, True,
                     "first close >12 pips through a 00 (00/50, placebo) level -> with the break, stop 2 pips back through the level, target tp_pips"),
    "M10_pdhl_h1": ("M10", "pdh_pdl_fade", "H1", dict(sweep_min=[3], sweep_max=[15, 30], tp=["mid", "opp"], day_start=[22, 0]), 50, True,
                    "first bar of the day to trade 3..sweep_max pips beyond PDH/PDL and close back inside -> fade at next open, stop beyond sweep +2 pips, target PD mid / opposite, flat end of day"),
    "M10_pdhl_m15": ("M10", "pdh_pdl_fade", "M15", dict(sweep_min=[3], sweep_max=[15, 30], tp=["mid", "opp"], day_start=[22, 0]), 50, True, "as M10_pdhl_h1 on M15"),
    "M10_tsoup_d1": ("M10", "turtle_soup_d1", "D1", dict(n=[20], min_age=[4], hold=[2, 4, 6], tp_atr=[0, 1.0], sl_pips=[2.0, 10.0]), 30, True,
                     "Connors-Raschke turtle soup on D1: low undercuts 20-day low (>=4 days old), close back above -> long, stop under the low"),
    "M11_wopen_h1": ("M11", "weekly_open_mr", "H1", dict(dist_adr=[0.75, 1.0, 1.5], sl_adr=[0.5, 1.0], days=["12", "123"]), 30, True,
                     "Tue/Wed close >= dist_adr x ADR14 from weekly open -> fade, stop sl_adr x ADR, target weekly open, time stop Fri 15:00 London"),
    "M12_dopen_h1": ("M12", "daily_open_mr", "H1", dict(day_start=[0, 22], dist_adr=[0.5, 0.75], sl_adr=[0.25, 0.5], ny_end=[16, 19]), 50, True,
                     "13:00-ny_end UTC: close >= dist_adr x ADR14 from the day open -> fade, stop sl_adr x ADR beyond day extreme, target open, flat 21 UTC"),
    "M13_streak_d1": ("M13", "streak_fade", "D1", dict(streak=[3], min_cum_pct=[0.5, 1.0, 1.5], hold=[1, 2, 3], sl_atr=[0, 1.0], direction=["fade", "momentum"]), 30, True,
                      "3 consecutive closes one way with |cum move|>min_cum_pct% -> enter against (fade) / with (momentum) at next open, exit close hold days later"),
    "M14_abn_d1": ("M14", "abnormal_day_contrarian", "D1", dict(window=[20], k=[1.5, 2.0, 2.5], hold=[1, 2], sl_atr=[0, 1.0], direction=["contrarian", "momentum"]), 30, True,
                   "abnormal day = return beyond mean+/-k sd of previous 20 daily returns; at its close enter against (contrarian) / with (momentum), exit close hold days later"),
    "M14_abn_h1": ("M14", "abnormal_day_momentum", "H1", dict(window=[20], k=[1.5, 2.0, 2.5], last_entry_hour=[15, 18, 20], sl_atr=[0, 1.0]), 30, True,
                   "intraday leg: first H1 bar whose return from the prior day close exceeds the abnormal threshold -> go with it, exit at the day's close"),
    "M15_qs_d1": ("M15", "lowest_close_mr", "D1", dict(n=[3, 5, 7, 10], hold=[1, 2], sides=["long", "both"]), 30, True,
                  "reconstruction: close is the lowest (highest) close of n days -> long (short) next open, exit after hold days"),
    "Q01_macdrsi_h1": ("Q01", "macd_rsi_fixed", "H1", dict(rsi_mode=["above50", "not_extreme", "none"], sl_pips=[30, 45], tp_pips=[60, 90]), 50, True,
                       "Backtrex MACD+RSI replica: MACD(12,26,9) cross with RSI(14) filter, SL 45 / TP 90 pips (and 30/60)"),
    "Q02_macross_h1": ("Q02", "ma_cross_fixed", "H1", dict(kind=["sma", "ema"], tp_pips=[10, 20], sl_pips=[10, 20]), 50, True, "Dukascopy contest sample: MA7/MA14 cross, TP 10 / SL 20"),
    "Q02_macross_m1": ("Q02", "ma_cross_fixed", "M1", dict(kind=["sma"], tp_pips=[10], sl_pips=[20]), 50, True, "Dukascopy contest sample on M1"),
    "Q05_tsmom_d1": ("Q05", "tsmom", "D1", dict(lookback=[20, 60, 120, 250], sl_atr=[0, 3.0]), 20, False,
                     "time-series momentum: position = sign(close - close[lookback]), reverse on flip (always in the market), optional 3 x ATR stop"),
}


def _run_one(df, strat, params, period, one_at_a_time=True):
    if one_at_a_time:
        return run_one(df, strat, params, period, COST)
    sub = slice_period(df, period)
    a, _ = SPLITS[period]
    orders = REGISTRY[strat](sub, **params)
    first = sub.index.searchsorted(pd.Timestamp(a, tz="UTC"))
    orders = [o for o in orders if o.i >= first]
    res = run_backtest(sub, orders, COST, one_at_a_time=False)
    s = res.summary(); s.update({"strategy": strat, "period": period, "params": json.dumps(params, default=str)})
    if s["trades"] > 0:
        by = res.by_year(); s["years_positive"] = float((by["sum_r"] > 0).mean())
    return s, res


def _grid(df, strat, grid, period, tag, one_at_a_time):
    if one_at_a_time:
        return run_grid(df, strat, grid, period, COST, tag=tag, verbose=False)
    from eurusd.evaluate import grid as mkgrid
    rows = [_run_one(df, strat, p, period, False)[0] for p in mkgrid(grid)]
    out = pd.DataFrame(rows); out.to_csv(RESULTS_DIR / f"{strat}_{tag}_{period}.csv", index=False)
    return out


def _pipsify(tr: pd.DataFrame) -> pd.DataFrame:
    """For rows without a stop (has_r False) judge on pips, as verdict() does."""
    tr = tr.copy()
    if "has_r" not in tr:
        return tr
    m = tr["has_r"] == False  # noqa
    for a, b in (("avg_r", "avg_pips"), ("t_stat", "t_stat_pips"), ("profit_factor", "profit_factor_pips")):
        tr.loc[m, a] = tr.loc[m, b]
    return tr


def run_family(fam: str) -> dict:
    cid, strat, tfname, grid, min_tr, oaat, desc = FAMILIES[fam]
    df = tf(tfname)
    t0 = time.time()
    print(f"\n##### {fam} ({cid}) {strat} {tfname}: {desc}", flush=True)
    tr = _grid(df, strat, grid, "train", fam, oaat)
    tr = _pipsify(tr)
    tr["t_stat"] = tr["t_stat"].fillna(0); tr["avg_r"] = tr["avg_r"].fillna(0)
    ok_n = tr["trades"] >= min_tr
    cand = tr[ok_n] if ok_n.any() else tr
    best = cand.loc[cand["t_stat"].idxmax()]
    bp = json.loads(best["params"])
    bp = {k: (NAN if (v is None or (isinstance(v, float) and math.isnan(v))) else (tuple(v) if isinstance(v, list) else v)) for k, v in bp.items()}
    n_ok, n_med = neighbourhood_ok(tr, bp, grid)
    val, vres = _run_one(df, strat, bp, "validate", oaat)
    ok, why = verdict(best, val, n_ok)
    # sanity print: a handful of train trades with the chosen parameters
    s_tr, res = _run_one(df, strat, bp, "train", oaat)
    if s_tr["trades"]:
        t = res.tdf
        print(f"--- {fam} sample TRAIN trades with best params {bp}:")
        print(t[["entry_time", "exit_time", "side", "entry", "exit", "sl", "tp", "reason", "pips", "r"]].sample(min(5, len(t)), random_state=7).sort_values("entry_time").to_string())
    vv = dict(val)
    if not vv.get("has_r", True):
        vv.update(avg_r=vv.get("avg_pips"), t_stat=vv.get("t_stat_pips"), profit_factor=vv.get("profit_factor_pips"))
    row = dict(family=fam, cat_id=cid, strategy=strat, tf=tfname, rules=desc, params=json.dumps(bp, default=str), grid_points=len(tr),
               has_r=bool(best.get("has_r", True)),
               train_trades=int(best["trades"]), train_win=best.get("win_rate", NAN), train_avg_r=best["avg_r"], train_pf=best["profit_factor"], train_t=best["t_stat"],
               train_years_pos=best.get("years_positive", NAN), train_sharpe=best.get("sharpe", NAN), neigh_median=n_med, neigh_ok=bool(n_ok),
               val_trades=vv.get("trades", 0), val_win=vv.get("win_rate", NAN), val_avg_r=vv.get("avg_r", NAN), val_pf=vv.get("profit_factor", NAN), val_t=vv.get("t_stat", NAN),
               val_years_pos=vv.get("years_positive", NAN), val_sharpe=vv.get("sharpe", NAN), val_avg_pips=vv.get("avg_pips", NAN),
               grid_pos_frac=float((tr["avg_r"] > 0).mean()), survives=ok, reason=why, secs=round(time.time() - t0))
    print(json.dumps(row, default=str), flush=True)
    return row


# ------------------------------------------------------------------ descriptive statistics (TRAIN only)
def stats_pivot_touch():
    """M05: replicate the MQL5 touch-frequency study (classic pivots, UTC days) on 2003-2010 and 2003-2015."""
    d = tf("D1")
    prev = d.shift(1)
    pp = (prev.high + prev.low + prev.close) / 3
    lv = dict(pp=pp, r1=2 * pp - prev.low, s1=2 * pp - prev.high, r2=pp + (prev.high - prev.low), s2=pp - (prev.high - prev.low),
              r3=prev.high + 2 * (pp - prev.low), s3=prev.low - 2 * (prev.high - pp))
    out = []
    for a, b in (("2003", "2010"), ("2003", "2015")):
        x = d.loc[a:b]
        row = {"period": f"{a}-{b}", "days": len(x)}
        for k in ("pp", "r1", "r2", "r3"):
            row[f"high>={k}"] = round(float((x.high >= lv[k].loc[a:b]).mean()) * 100, 1)
        for k in ("pp", "s1", "s2", "s3"):
            row[f"low<={k}"] = round(float((x.low <= lv[k].loc[a:b]).mean()) * 100, 1)
        below = x.open < lv["pp"].loc[a:b]
        row["low<=s1|open<pp"] = round(float((x.low <= lv["s1"].loc[a:b])[below].mean()) * 100, 1)
        row["low<=s1|open>=pp"] = round(float((x.low <= lv["s1"].loc[a:b])[~below].mean()) * 100, 1)
        row["high>=r1|open>pp"] = round(float((x.high >= lv["r1"].loc[a:b])[x.open > lv["pp"].loc[a:b]].mean()) * 100, 1)
        out.append(row)
    return pd.DataFrame(out)


def stats_round_number(fwd_bars=2, lookback=24):
    """M09: 30-min forward move after the first touch of a 00 / 50 / placebo(25,75) level, M15 TRAIN, 07-20 UTC."""
    df = slice_period(tf("M15"), "train")
    h, l, c = df.high.values, df.low.values, df.close.values
    pc = np.roll(c, 1)
    hmax = pd.Series(h).rolling(lookback).max().shift(1).values
    lmin = pd.Series(l).rolling(lookback).min().shift(1).values
    hrs = df.index.hour.values
    out = []
    for name, step, off in (("00", 0.01, 0.0), ("50 (00+50)", 0.005, 0.0), ("placebo 25/75", 0.005, 0.0025)):
        up = np.floor((pc - off) / step) * step + step + off
        dn = np.ceil((pc - off) / step) * step - step + off
        tu = (h >= up) & (hmax < up) & (hrs >= 7) & (hrs < 20)
        td = (l <= dn) & (lmin > dn) & (hrs >= 7) & (hrs < 20)
        fwd = (np.roll(c, -fwd_bars) - c) / PIP
        fu, fd = fwd[tu], fwd[td]
        cont = np.concatenate([fu, -fd])   # continuation move (pips) in the direction of the approach
        out.append({"level": name, "touches": int(tu.sum() + td.sum()), "mean_fwd30m_cont_pips": round(float(cont.mean()), 2),
                    "t": round(float(cont.mean() / cont.std() * math.sqrt(len(cont))), 2), "p_reverse": round(float((cont < 0).mean()), 3),
                    "mean_|fwd|": round(float(np.abs(cont).mean()), 2)})
    return pd.DataFrame(out)


def stats_open_return():
    """M11/M12 base rates on H1 TRAIN: P(price trades back through the weekly open before Friday 15:00 London |
    distance at Tuesday 23:00 UTC >= x ADR) and P(back through the daily open by 21:00 UTC | distance at 13:00 UTC >= x ADR)."""
    df = slice_period(tf("H1"), "train")
    adr = SM._adr_by_bar(df, 14, 22)
    o, h, l, c = df.open.values, df.high.values, df.low.values, df.close.values
    # weekly
    wk = (df.index.tz_convert(None) - pd.Timedelta(hours=21)).to_period("W-SAT")
    lon = df.index.tz_convert("Europe/London")
    rows = []
    recs = []
    pos = np.arange(len(df))
    for _, idx in pd.Series(pos, index=df.index).groupby(wk.values):
        idx = idx.values
        if len(idx) < 60:
            continue
        wopen = o[idx[0]]
        tue = [i for i in idx if df.index[i].dayofweek == 1 and df.index[i].hour == 23]
        if not tue:
            continue
        i0 = tue[0]
        if np.isnan(adr[i0]):
            continue
        dist = (c[i0] - wopen) / adr[i0]
        later = [i for i in idx if i > i0 and not (lon[i].dayofweek == 4 and lon[i].hour >= 15)]
        if not later:
            continue
        touched = bool(((l[later] <= wopen) & (h[later] >= wopen)).any())
        recs.append((abs(dist), touched))
    r = pd.DataFrame(recs, columns=["dist", "touched"])
    for lo_, hi_ in ((0, 0.5), (0.5, 1.0), (1.0, 1.5), (1.5, 9)):
        m = (r.dist >= lo_) & (r.dist < hi_)
        rows.append({"ref": "weekly open (Tue 23:00 UTC)", "dist_adr": f"[{lo_},{hi_})", "n": int(m.sum()), "p_return": round(float(r.touched[m].mean()), 3) if m.any() else NAN})
    # daily
    day = df.index.floor("D")
    recs = []
    for _, idx in pd.Series(pos, index=df.index).groupby(day.values):
        idx = idx.values
        if len(idx) < 20:
            continue
        dopen = o[idx[0]]
        i0 = [i for i in idx if df.index[i].hour == 13]
        if not i0 or np.isnan(adr[i0[0]]):
            continue
        i0 = i0[0]
        dist = abs(c[i0] - dopen) / adr[i0]
        later = [i for i in idx if i > i0 and df.index[i].hour < 21]
        if not later:
            continue
        recs.append((dist, bool(((l[later] <= dopen) & (h[later] >= dopen)).any())))
    r = pd.DataFrame(recs, columns=["dist", "touched"])
    for lo_, hi_ in ((0, 0.25), (0.25, 0.5), (0.5, 0.75), (0.75, 1.0), (1.0, 9)):
        m = (r.dist >= lo_) & (r.dist < hi_)
        rows.append({"ref": "daily open (13:00 UTC)", "dist_adr": f"[{lo_},{hi_})", "n": int(m.sum()), "p_return": round(float(r.touched[m].mean()), 3) if m.any() else NAN})
    return pd.DataFrame(rows)


def stats_vendor_window():
    """Q01: fixed vendor rules (no parameter choice) on the part of the Backtrex window that is not HOLDOUT:
    2016-10-02 .. 2022-12-31.  The vendor window runs to 2026-10-01; 2023+ is never touched here."""
    rows = []
    for name, strat, tfname, p in (
        ("Backtrex Connors RSI(2) D1 (RSI<5, exit SMA5 or close<SMA200, no stop)", "connors_rsi2", "D1", dict(thr=5, exit_on_trend_cross=True, sl_atr=NAN, sides="both")),
        ("Backtrex Connors RSI(2) D1 long only", "connors_rsi2", "D1", dict(thr=5, exit_on_trend_cross=True, sl_atr=NAN, sides="long")),
        ("Backtrex MACD+RSI H1 SL45/TP90 (RSI>50 filter)", "macd_rsi_fixed", "H1", dict(rsi_mode="above50", sl_pips=45, tp_pips=90)),
        ("Backtrex MACD+RSI H1 SL45/TP90 (RSI not extreme)", "macd_rsi_fixed", "H1", dict(rsi_mode="not_extreme", sl_pips=45, tp_pips=90)),
        ("Dukascopy MA7/14 H1 TP10/SL20", "ma_cross_fixed", "H1", dict(kind="sma", tp_pips=10, sl_pips=20)),
    ):
        df = tf(tfname)
        a = df.index.searchsorted(pd.Timestamp("2016-10-02", tz="UTC")); b = df.index.searchsorted(pd.Timestamp("2023-01-01", tz="UTC"))
        sub = df.iloc[max(0, a - 500):b]
        orders = [o for o in REGISTRY[strat](sub, **p) if o.i >= 500]
        res = run_backtest(sub, orders, COST)
        s = res.summary()
        rows.append({"rule": name, "window": "2016-10-02..2022-12-31", "trades": s.get("trades", 0), "win_rate": round(s.get("win_rate", NAN), 3),
                     "pf_pips": round(s.get("profit_factor_pips", NAN), 2), "avg_pips": round(s.get("avg_pips", NAN), 1), "total_pips": round(s.get("total_pips", NAN), 0),
                     "t_pips": round(s.get("t_stat_pips", NAN), 2)})
    return pd.DataFrame(rows)


def stats_tsmom_sharpe():
    """Q05: Sharpe of daily TSMOM returns (close-to-close, 1.4 pips per flip) for each lookback, TRAIN and VALIDATE."""
    d = tf("D1")
    r = d.close.pct_change()
    rows = []
    for lb in (20, 60, 120, 250):
        sig = np.sign(d.close - d.close.shift(lb)).shift(1)  # position held during day t decided at t-1 close
        cost = (sig.diff().abs() / 2) * 1.4 * PIP / d.close.shift(1)
        ret = sig * r - cost.fillna(0)
        for per in ("train", "validate"):
            a, b = SPLITS[per]
            x = ret.loc[a:b].dropna()
            rows.append({"lookback": lb, "period": per, "ann_ret_pct": round(float(x.mean() * 252 * 100), 2), "sharpe": round(float(x.mean() / x.std() * math.sqrt(252)), 2),
                         "years_pos": round(float((x.groupby(x.index.year).sum() > 0).mean()), 2)})
    return pd.DataFrame(rows)


# ------------------------------------------------------------------ Q06 machine-learning baseline
def run_ml():
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import make_pipeline
    from sklearn.model_selection import TimeSeriesSplit
    from scipy.stats import binomtest
    import lightgbm as lgb
    d = tf("D1")
    X = SM.ml_daily_features(d).dropna()
    feats = [c for c in X.columns if c not in ("y", "y_ret")]
    tr = X.loc["2003":"2015"]; va = X.loc["2016":"2022"]
    models = {
        "logit": lambda: make_pipeline(StandardScaler(), LogisticRegression(C=0.05, max_iter=2000)),
        "lgbm": lambda: lgb.LGBMClassifier(n_estimators=300, learning_rate=0.02, num_leaves=7, min_child_samples=100, subsample=0.8,
                                           subsample_freq=1, colsample_bytree=0.8, reg_lambda=5.0, verbose=-1, random_state=0),
    }
    rows = []
    for name, mk in models.items():
        m = mk().fit(tr[feats], tr["y"])
        acc_in = float((m.predict(tr[feats]) == tr["y"]).mean())
        cv = []
        for a, b in TimeSeriesSplit(5).split(tr):
            mm = mk().fit(tr.iloc[a][feats], tr.iloc[a]["y"]); cv.append(float((mm.predict(tr.iloc[b][feats]) == tr.iloc[b]["y"]).mean()))
        # VALIDATE: expanding-window refit at the start of every year
        probs = []
        for y in range(2016, 2023):
            fit = X.loc["2003":str(y - 1)]
            mm = mk().fit(fit[feats], fit["y"])
            probs.append(pd.Series(mm.predict_proba(va.loc[str(y)][feats])[:, 1], index=va.loc[str(y)].index))
        p = pd.concat(probs)
        y = va["y"]; ret_pips = (np.exp(va["y_ret"]) - 1) * d["close"].reindex(va.index) / PIP
        acc = float(((p > 0.5).astype(int) == y).mean())
        pv = binomtest(int(((p > 0.5).astype(int) == y).sum()), len(y), 0.5, alternative="greater").pvalue
        row = {"model": name, "train_acc_insample": round(acc_in, 4), "train_cv_acc": round(float(np.mean(cv)), 4), "val_acc": round(acc, 4), "val_binom_p": round(float(pv), 3),
               "val_days": len(y), "val_up_frac": round(float(y.mean()), 3)}
        for thr in (0.5, 0.55):
            pos = np.where(p > thr, 1, np.where(p < 1 - thr, -1, 0)).astype(float)
            pos_s = pd.Series(pos, index=p.index)
            cost = pos_s.diff().abs().fillna(abs(pos_s.iloc[0])) * 0.7  # 1.4 pips per round trip
            pnl = pos_s * ret_pips - cost
            days = pnl[pos_s != 0]
            yr = pnl.groupby(pnl.index.year).sum()
            sharpe = float(pnl.mean() / pnl.std() * math.sqrt(252)) if pnl.std() > 0 else 0.0
            t = float(days.mean() / days.std() * math.sqrt(len(days))) if len(days) > 1 else 0.0
            pf = float(days[days > 0].sum() / -days[days < 0].sum()) if (days < 0).any() else math.inf
            row.update({f"thr{thr}_days_in": int((pos_s != 0).sum()), f"thr{thr}_avg_pips": round(float(days.mean()), 2) if len(days) else NAN, f"thr{thr}_total_pips": round(float(pnl.sum()), 0),
                        f"thr{thr}_pf": round(pf, 3), f"thr{thr}_t": round(t, 2), f"thr{thr}_sharpe": round(sharpe, 2), f"thr{thr}_years_pos": round(float((yr > 0).mean()), 2)})
        rows.append(row)
        print(json.dumps(row), flush=True)
    # feature importance of the lgbm fit on TRAIN for the record
    m = models["lgbm"]().fit(tr[feats], tr["y"])
    imp = pd.Series(m.feature_importances_, index=feats).sort_values(ascending=False)
    print("lgbm top features (train):", imp.head(8).to_dict())
    return pd.DataFrame(rows)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    flags = [a for a in sys.argv[1:] if a.startswith("--")]
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if "--stats" in flags:
        print("\n### M05 pivot touch frequencies (classic, UTC days)\n", stats_pivot_touch().to_string(index=False))
        print("\n### M09 round-number first-touch 30-min forward move (M15 train)\n", stats_round_number().to_string(index=False))
        print("\n### M11/M12 return-to-open base rates (H1 train)\n", stats_open_return().to_string(index=False))
        print("\n### Q01/Q02 vendor rules on 2016-10..2022-12 (holdout excluded)\n", stats_vendor_window().to_string(index=False))
        print("\n### Q05 TSMOM daily Sharpe\n", stats_tsmom_sharpe().to_string(index=False))
    if "--ml" in flags:
        ml = run_ml()
        ml.to_csv(RESULTS_DIR / "meanrev_systematic_ml.csv", index=False)
        print(ml.to_string(index=False))
    fams = args if args else ([] if flags else list(FAMILIES))
    if fams:
        part = "--part=" in " ".join(flags)
        rows = [run_family(f) for f in fams]
        out = pd.DataFrame(rows)
        path = OUT if not part else RESULTS_DIR / ("meanrev_systematic_" + [f for f in flags if f.startswith("--part=")][0].split("=")[1] + ".csv")
        if path.exists():
            old = pd.read_csv(path)
            out = pd.concat([old[~old.family.isin(out.family)], out])
        out.to_csv(path, index=False)
        print(out[["family", "cat_id", "tf", "train_trades", "train_t", "train_pf", "val_trades", "val_avg_r", "val_t", "val_pf", "val_years_pos", "survives", "reason"]].to_string())
    if "--merge" in flags:
        parts = sorted(RESULTS_DIR.glob("meanrev_systematic_p*.csv"))
        out = pd.concat([pd.read_csv(p) for p in parts])
        out = out.drop_duplicates("family", keep="last")
        out["order"] = out.family.map({f: k for k, f in enumerate(FAMILIES)})
        out = out.sort_values("order").drop(columns="order")
        out.to_csv(OUT, index=False)
        print(out[["family", "cat_id", "tf", "train_trades", "train_t", "train_pf", "val_trades", "val_avg_r", "val_t", "val_pf", "val_years_pos", "survives", "reason"]].to_string())
