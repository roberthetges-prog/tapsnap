"""Catalogue session / time-of-day, microstructure and calendar entries (research/strategies.json
S01-S19, B01, C01-C06, Q04): grid on TRAIN, chosen parameters once on VALIDATE, survival rules.
HOLDOUT is never touched.  Usage:
    python experiments/11_session_calendar.py [family ...]        # default: all families
    python experiments/11_session_calendar.py analysis            # S12 ratio buckets + C02 hour statistics
Results: experiments/results/session_calendar.csv (one row per family), per-grid CSVs in results/.
"""
import sys, json, math, time
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import numpy as np, pandas as pd
from eurusd.backtest import CostModel
from eurusd.evaluate import run_grid, run_one, neighbourhood_ok, verdict, RESULTS_DIR, SPLITS
from eurusd import features as F
import eurusd.strategies_session  # noqa: F401  (registers the strategies)

COST = CostModel(spread_pips=1.0, slippage_pips=0.2)
DATA = "/home/user/tapsnap/eurusd/data/processed/"
NAN = math.nan
_TF = {}


def tf(name):
    if name not in _TF:
        if name == "D1NY":  # NY-close daily bars (22 UTC day start) built from H1
            d = F.daily_ohlc(tf("H1"), 22)
            _TF[name] = d[d["n"] >= 10].drop(columns="n")
        else:
            _TF[name] = pd.read_parquet(DATA + f"EURUSD_{name}.parquet")
    return _TF[name]


# family -> (catalogue id, strategy, timeframe, grid, min train trades for selection, short description)
FAMILIES = {
    "S01_m15": ("S01", "range_breakout", "M15",
                dict(rng_start=[0], rng_end=[7], entry_until=[10], exit_hour=[12, 21], entry_mode=["stop", "close"],
                     buffer_pips=[0.0], sl_mode=["pips", "range", "mid"], sl_val=[35, 1.0], tp_mode=["pips", "rr"], tp_val=[70, 2.0]),
                100, "Asian range 00-07 UTC, entry 07-10 UTC stop/close, Backtrex SL35/TP70 or range-based SL with 2R, exit 12 or 21 UTC"),
    "S01_h1": ("S01", "range_breakout", "H1",
               dict(rng_start=[0], rng_end=[7], entry_until=[10], exit_hour=[12, 21], entry_mode=["stop", "close"],
                    buffer_pips=[0.0], sl_mode=["pips", "range"], sl_val=[35, 1.0], tp_mode=["pips", "rr"], tp_val=[70, 2.0]),
               100, "same on H1 (Backtrex timeframe)"),
    "S02_m15": ("S02", "range_breakout", "M15",
                dict(rng_start=[0, 2], rng_end=[7], entry_until=[8], exit_hour=[12], buffer_pips=[3.0], sl_mode=["range"],
                     sl_val=[1.0], sl_cap_pips=[25], tp_mode=["range", "half_adr"], tp_val=[1.0], max_ratio=[0.5, NAN]),
                100, "babypips statistical London breakout: stops +/-3 pips placed 07-08 GMT, SL min(opposite side, 25p), TP 1x range or 0.5 ADR, skip if range > 50% ADR14, flat 12 GMT"),
    "S03_m15": ("S03", "range_breakout", "M15",
                dict(rng_start=[5], rng_end=[7], entry_until=[10, 12], exit_hour=[12, 16], entry_mode=["close"], buffer_pips=[0.0],
                     sl_mode=["range"], sl_val=[1.0], tp_mode=["rr"], tp_val=[1.0, 2.0], min_range_pips=[3]),
                100, "London Ripper: 05:00-07:00 UTC box, first M15 close outside after 07:00, SL opposite edge, TP 1R/2R"),
    "S04_h1": ("S04", "asian_sweep_reverse", "H1",
               dict(rng_start=[0], rng_end=[7], kz_start=[7], kz_end=[9], decide_at=[8.0], sweep_min_pips=[0.0, 3.0],
                    tp_mode=["range", "rr"], tp_val=[1.5], engulf=[False, True], exit_hour=[12]),
               100, "Frankfurt trap H1: 07/08 UTC candle takes out Asian range, 08:00 candle closes back inside -> fade at 09:00, SL beyond spike+3p, TP opposite side or 1.5R, flat 12 UTC"),
    "S04_m15": ("S04", "asian_sweep_reverse", "M15",
                dict(rng_start=[0], rng_end=[7], kz_start=[7], kz_end=[9], sweep_min_pips=[3.0], tp_mode=["range", "rr"],
                     tp_val=[1.5], exit_hour=[12, 16], sl_buffer_pips=[3.0]),
                100, "same on M15: first M15 close back inside the range during 07-09 UTC"),
    "S05_m15": ("S05", "ny_open_reversal", "M15",
                dict(min_london_move_pips=[20, 30, 40], tp_mode=["half", "open"], require_pd_level=[False, True]),
                50, "NY-open reversal: |London move since 07:00 London| >= x pips, rejection bar at a new extreme 08:30-10:00 ET, SL beyond extreme+5p, TP 50% retrace / London open, flat 11:00 ET"),
    "S06_m5": ("S06", "london_close_reversal", "M5",
               dict(sl_pips=[12, 15], tp_pips=[10, 15], sl_mode=["pips", "ext"]),
               100, "London-close scalp 11:00-12:30 ET: new day extreme that fails to close beyond -> fade, TP 10/15p, SL 12/15p or extreme+5p, flat 13:00 ET"),
    "S07_utc": ("S07", "asian_sweep_reverse", "M15",
                dict(rng_start=[0], rng_end=[7], kz_start=[7], kz_end=[10], sweep_min_pips=[3.0, 5.0],
                     tp_mode=["range", "rr", "range_min_rr"], tp_val=[2.0], bias=["none", "prev_day", "contra"], exit_hour=[16]),
                100, "Judas swing (UTC clock): sweep of the 00-07 UTC range by >= x pips with a close back inside during 07-10 UTC, SL beyond sweep+3p, TP opposite side / 2R / opposite side if >= 2R, daily-bias filter, flat 16 UTC"),
    "S07_ny": ("S07", "asian_sweep_reverse", "M15",
               dict(tz=["America/New_York"], day_offset=[17.0], rng_start=[2.0], rng_end=[9.0], kz_start=[9.0], kz_end=[12.0],
                    sweep_min_pips=[3.0, 5.0], tp_mode=["range", "rr", "range_min_rr"], tp_val=[2.0], bias=["none", "prev_day", "contra"], exit_hour=[23.0]),
               100, "Judas swing (ET clock): Asian range 19:00-02:00 ET, London killzone 02:00-05:00 ET, flat 16:00 ET"),
    "S08_m15": ("S08", "fvg_killzone", "M15",
                dict(kz_start=[7.0], kz_end=[10.0], min_gap_pips=[0.5, 2.0], expiry_bars=[4, 8], tp_rr=[1.5, 2.0, 3.0], exit_hour=[16.0]),
                100, "NY AM killzone 07-10 ET 3-candle FVG, limit at the gap edge, SL beyond candle-1 extreme, TP R-multiple, flat 16 ET"),
    "S09_m5": ("S09", "fvg_killzone", "M5",
               dict(kz_start=[10.0], kz_end=[11.0], exit_hour=[11.5], require_sweep=[True], sl_mode=["sweep", "gap"],
                    sweep_level=["session", "prev_day"], sweep_lookback=[12, 24], min_gap_pips=[0.5, 1.5], tp_rr=[2.0], expiry_bars=[6]),
               50, "Silver bullet 10-11 ET M5: sweep of the session / prior-day low-high within the last 1-2 h, then FVG in the reversal direction, SL at sweep extreme or gap, TP 2R, flat 11:30 ET"),
    "S10_m15": ("S10", "asian_sweep_reverse", "M15",
                dict(rng_start=[0], rng_end=[7], kz_start=[7], kz_end=[10], confirm=["daily_open"], sweep_min_pips=[0.0, 3.0],
                     tp_mode=["range", "rr"], tp_val=[2.0], bias=["none", "prev_day"], exit_hour=[17, 21]),
                100, "Power of three: London (07-10 UTC) sweeps the 00-07 range and closes back through the 00:00 UTC open -> trade the reversal, SL beyond manipulation extreme, TP opposite side / 2R, flat 17 (12 ET) or 21 UTC"),
    "S11_m5": ("S11", "asian_range_fade", "M5",
               dict(min_range_pips=[15], max_range_pips=[40, 60], sl_pips=[8, 12], use_rsi=[True, False], rsi_ob=[70], rsi_os=[30]),
               100, "Asian range fade 00-06 UTC: touch of the running 22:00-UTC range edge with RSI14 filter, TP midpoint, SL edge+8/12p, flat 06 UTC"),
    "S12_hostA": ("S12", "range_breakout", "M15",
                  dict(rng_start=[1], rng_end=[8], entry_until=[14], exit_hour=[20], buffer_pips=[2.0], sl_mode=["range"], sl_val=[1.0],
                       tp_mode=["rr"], tp_val=[2.0, 3.0], max_ratio=[0.3, 0.4, 0.5, 0.6, 0.8, NAN], adr_len=[14]),
                  100, "S12 width filter on the lead's best ARB (range 01-08 UTC, stops until 14, SL opposite side, 2-3R, flat 20): breakout only if range/ADR14 <= max_ratio"),
    "S12_hostB": ("S12", "range_breakout", "M15",
                  dict(rng_start=[0], rng_end=[7], entry_until=[10], exit_hour=[12], buffer_pips=[2.0], sl_mode=["range"], sl_val=[1.0],
                       tp_mode=["rr"], tp_val=[2.0], max_ratio=[0.3, 0.4, 0.5, 0.6, 0.8, NAN], adr_len=[14]),
                  100, "S12 width filter on the catalogue S01 window (00-07 UTC, entries 07-10, flat 12 UTC, SL opposite side, 2R)"),
    "S12_fade": ("S12", "asian_sweep_reverse", "M15",
                 dict(rng_start=[0], rng_end=[7], kz_start=[7], kz_end=[10], sweep_min_pips=[3.0], tp_mode=["range"], exit_hour=[16],
                      min_ratio=[NAN, 0.4, 0.5, 0.6, 0.8], adr_len=[14]),
                 50, "S12 fade leg: Judas-swing fade only when range/ADR14 >= min_ratio ('the move already happened')"),
    "S13_m15": ("S13", "range_breakout", "M15",
                dict(tz=["Europe/London"], rng_start=[7.5, 8.0], rng_end=[8.0, 8.5, 9.0], entry_until=[12], exit_hour=[12],
                     buffer_pips=[10.0], buffer_atr_frac=[NAN, 0.1], sl_mode=["range"], sl_val=[1.0], tp_mode=["range"], tp_val=[1.0, 2.0], min_range_pips=[3]),
                100, "London ORB (FXStreet): range 07:30-08:00 / 08:00-08:30 / 08:00-09:00 London local, break +/-10 pips or 0.1 x daily ATR, SL opposite side, TP 1x/2x range, flat 12:00 London"),
    "S14_h1": ("S14", "fix_pattern_pair", "H1",
               dict(legs=["pre", "post"], pre_start=[13.0, 15.0], post_end=[20.0], sl_adr=[0.5, 0.3]),
               100, "WM/R fix pattern: short 13/15:00-16:00 London, long 16:00-20:00 London, 0.3/0.5 ADR stop (legs separately)"),
    "S14_nostop": ("S14", "fix_pattern_pair", "H1",
               dict(legs=["pre", "post"], pre_start=[13.0, 15.0], post_end=[20.0]),
               100, "same without stop (academic version, judged in pips)"),
    "S15_m15": ("S15", "monthend_fix_follow", "M15",
                dict(signal_start=[13.0, 14.0], signal_end=[15.0], exit_hour=[16.0], mode=["follow", "fade"], sl_adr=[0.4]),
                30, "Month-end fix (price-only; equity-rebalancing sign NOT available): last London business day, follow/fade the 13/14:00->15:00 move into the 16:00 fix, 0.4 ADR stop"),
    "S16_h1": ("S16", "weekend_gap", "H1",
               dict(min_gap_pips=[5.0, 10.0, 15.0], max_gap_atr_ratio=[0.5, 1.0, 9.0], sl_mode=["gap", "atr"], time_stop=["wed8", "mon"]),
               30, "Weekend gap fill: |Sunday open - Friday close| >= x pips and <= r x ATR14(daily), trade toward Friday close, SL 1x gap or 0.5 ATR, time stop Wed 08:00 London or Monday close"),
    "S17_m15": ("S17", "rsi_time_filter", "M15",
                dict(use_filter=[True, False], sl_atr=[1.5, 2.5], tp_rr=[1.0, NAN], exit_on_opposite=[True]),
                100, "DailyFX RSI14 30/70 cross range trade, entries only 14:00-06:00 ET (vs 24h control), exit on opposite cross / ATR stop / optional 1R target"),
    "S17_h1": ("S17", "rsi_time_filter", "H1",
               dict(use_filter=[True, False], sl_atr=[1.5, 2.5], tp_rr=[1.0, NAN], exit_on_opposite=[True]),
               100, "same on H1"),
    "S18_h1": ("S18", "local_hours_pair", "H1",
               dict(legs=["short", "long"], short_start=[7.0, 8.0], short_end=[13.0], long_start=[13.0], long_end=[21.0], sl_adr=[0.5, 0.3]),
               100, "Breedon-Ranaldo: short 07/08:00-13:00 London, long 13:00-21:00 London, 0.3/0.5 ADR stop (legs separately)"),
    "S18_nostop": ("S18", "local_hours_pair", "H1",
               dict(legs=["short", "long"], short_start=[7.0, 8.0], short_end=[13.0], long_start=[13.0], long_end=[21.0]),
               100, "same without stop (paper version, judged in pips)"),
    "S19_h1": ("S19", "liquidity_sweep", "H1",
               dict(level_mode=["equal", "prior"], lookback=[24, 48, 96], sweep_min_pips=[3.0], tp_rr=[1.5, 2.0, 3.0], max_hold=[48]),
               100, "Backtrex liquidity sweep: equal highs/lows (2 swing points within 2 pips) or N-bar extreme swept by >= 3 pips with a close back inside, in the London/NY killzones (ET), SL beyond sweep+2p, TP R-multiple"),
    "S19_m15": ("S19", "liquidity_sweep", "M15",
                dict(level_mode=["equal", "prior"], lookback=[96, 192], sweep_min_pips=[3.0], tp_rr=[2.0], max_hold=[96]),
                100, "same on M15 (levels from the last 1-2 days of M15 swings)"),
    "B01_m15": ("B01", "range_breakout", "M15",
                dict(tz=["America/New_York"], rng_start=[3.0], rng_end=[8.0], entry_until=[12.0, 16.0], exit_hour=[17.0], buffer_pips=[1.0],
                     sl_mode=["mid"], tp_mode=["range"], tp_val=[1.0]),
                100, "'London sets the range, NY breaks it': stops at the 03-08 ET range after 08 ET, SL midpoint, TP 1x range, flat 17 ET"),
    "B01_fade": ("B01", "london_range_fade_second", "M15",
                 dict(tp_val=[0.5, 1.0], entry_until=[16.0], exit_hour=[17.0]),
                 50, "B01 second-break fade: when both sides of the London range break, fade the second break (SL beyond its extreme, TP 0.5/1x range)"),
    "C01_h1": ("C01", "dow_pair", "H1",
               dict(mode=["fxday", "utc"], legs=["mon", "fri"]),
               100, "Seasonax day-of-week: short Monday, long Friday (NY-close FX days or UTC calendar days), time exit, no stop"),
    "C03_d1": ("C03", "month_seasonal", "D1NY",
               dict(long_months=[[12]], short_months=[[5], []]),
               10, "Monthly seasonality: long December (last Nov close -> last Dec close), short May"),
    "C04_d1": ("C04", "turn_of_month", "D1NY",
               dict(entry_offset=[-1], exit_offset=[1, 4], side=[1, -1]),
               30, "Turn of month: long/short EUR/USD from T-1 close to T+1 / T+4 close (T = last trading day)"),
    "C05_h1": ("C05", "friday_squaring", "H1",
               dict(min_move_pct=[0.5, 0.75, 1.0], sl_adr=[0.5, 0.3]),
               30, "Friday squaring: if the week's move at 13:00 London Friday >= x %, fade it to the Friday close, 0.3/0.5 ADR stop"),
    "C06_d1": ("C06", "holiday_week", "D1NY",
               dict(which=["both", "tg", "xm"], side_mode=["continue", "fade"], trend_days=[10]),
               10, "Holiday weeks (US Thanksgiving Mon-Fri, Dec 24-Jan 2): continue / fade the prior 10-day trend over the window"),
    "Q04_h1": ("Q04", "window_hold", "H1",
               dict(tz=["Europe/Berlin", "UTC"], entry_hour=[0.0], exit_hour=[3.0], side=[1, -1], dows=[[4]]),
               100, "Popovic-Durovic Friday 00:00-03:00 (CET or UTC) hold, direction chosen on TRAIN"),
}


def _nan2str(v):
    return "nan" if isinstance(v, float) and math.isnan(v) else v


def neigh_ok_nan_safe(train_df, best, grid):
    """neighbourhood_ok with NaN grid values mapped to the string 'nan' (NaN != NaN breaks list.index)."""
    t = train_df.copy()
    t["params"] = t["params"].map(lambda s: json.dumps({k: _nan2str(v) for k, v in json.loads(s).items()}))
    b = {k: _nan2str(v) for k, v in best.items()}
    g = {k: [_nan2str(v) for v in vals] for k, vals in grid.items()}
    return neighbourhood_ok(t, b, g)


def _score(df):
    has_r = df["has_r"].fillna(False).astype(bool) if "has_r" in df else pd.Series(True, index=df.index)
    base = np.where(has_r, df["avg_r"], df["avg_pips"])
    return pd.Series(base * np.sqrt(df["trades"].clip(lower=1)), index=df.index)


def run_family(fam):
    cid, strat, tfname, grid, min_tr, desc = FAMILIES[fam]
    df = tf(tfname)
    t0 = time.time()
    tr = run_grid(df, strat, grid, "train", COST, tag="sc_" + fam, verbose=False)
    tr = tr[tr["trades"] > 0].copy() if (tr["trades"] > 0).any() else tr
    if tr.empty or tr["trades"].max() == 0:
        row = dict(family=fam, id=cid, strategy=strat, tf=tfname, desc=desc, params="{}", grid_points=0, survives=False,
                   reason="no trades on train", secs=round(time.time() - t0))
        print(json.dumps(row, default=str), flush=True)
        return row
    for col in ("avg_r", "avg_pips", "t_stat", "profit_factor", "years_positive", "win_rate", "has_r"):
        if col not in tr:
            tr[col] = np.nan
    sel = tr[tr["trades"] >= min_tr] if (tr["trades"] >= min_tr).any() else tr
    best = sel.loc[_score(sel).idxmax()]
    bp = json.loads(best["params"])
    has_r = bool(best["has_r"]) if not pd.isna(best["has_r"]) else True
    trn = tr.copy()
    if not has_r:  # judge no-stop strategies on pips (same convention as verdict())
        trn["avg_r"] = trn["avg_pips"]
    n_ok, n_med = neigh_ok_nan_safe(trn, bp, grid)
    val, _ = run_one(df, strat, bp, "validate", COST)
    ok, why = verdict(best, val, n_ok)
    if val.get("trades", 0) == 0:
        ok, why = False, "no validation trades"
    unit = "R" if has_r else "pips"
    row = dict(family=fam, id=cid, strategy=strat, tf=tfname, desc=desc, params=json.dumps(bp, default=str), grid_points=len(tr), unit=unit,
               train_trades=int(best["trades"]), train_wr=best["win_rate"],
               train_avg=best["avg_r"] if has_r else best["avg_pips"],
               train_pf=best["profit_factor"] if has_r else best["profit_factor_pips"],
               train_t=best["t_stat"] if has_r else best["t_stat_pips"], train_years_pos=best.get("years_positive", np.nan),
               neigh_median=n_med, val_trades=val.get("trades", 0), val_wr=val.get("win_rate", np.nan),
               val_avg=val.get("avg_r" if has_r else "avg_pips", np.nan),
               val_pf=val.get("profit_factor" if has_r else "profit_factor_pips", np.nan),
               val_t=val.get("t_stat" if has_r else "t_stat_pips", np.nan), val_years_pos=val.get("years_positive", np.nan),
               survives=ok, reason=why, secs=round(time.time() - t0))
    print(json.dumps(row, default=str), flush=True)
    return row


def save_rows(rows, path=None):
    import os
    path = path or RESULTS_DIR / os.environ.get("SC_OUT", "session_calendar.csv")  # SC_OUT: per-process file for parallel runs
    out = pd.DataFrame(rows)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    if path.exists():
        old = pd.read_csv(path)
        out = pd.concat([old[~old.family.isin(out.family)], out])
    out.to_csv(path, index=False)


def analysis():
    """S12: breakout / fade expectancy by Asian-range-to-ADR bucket on TRAIN.  C02: hour (ET) that sets the daily
    high / low, TRAIN vs VALIDATE (descriptive)."""
    rows = []
    buckets = [(0, 0.3), (0.3, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.8), (0.8, 9)]
    m15 = tf("M15")
    hostA = dict(rng_start=1, rng_end=8, entry_until=14, exit_hour=20, buffer_pips=2.0, sl_mode="range", sl_val=1.0, tp_mode="rr", tp_val=3.0)
    hostB = dict(rng_start=0, rng_end=7, entry_until=10, exit_hour=12, buffer_pips=2.0, sl_mode="range", sl_val=1.0, tp_mode="rr", tp_val=2.0)
    fade = dict(rng_start=0, rng_end=7, kz_start=7, kz_end=10, sweep_min_pips=3.0, tp_mode="range", exit_hour=16)
    for name, strat, host in (("breakout_hostA(01-08,flat20,3R)", "range_breakout", hostA),
                              ("breakout_hostB(00-07,flat12,2R)", "range_breakout", hostB),
                              ("judas_fade(00-07,kz07-10,TP=range)", "asian_sweep_reverse", fade)):
        for lo, hi in buckets:
            p = dict(host, min_ratio=lo, max_ratio=hi)
            s, _ = run_one(m15, strat, p, "train", COST)
            rows.append(dict(host=name, bucket=f"[{lo},{hi})", trades=s.get("trades", 0), win_rate=s.get("win_rate"), avg_r=s.get("avg_r"),
                             pf=s.get("profit_factor"), t=s.get("t_stat"), years_pos=s.get("years_positive")))
            print(rows[-1], flush=True)
    pd.DataFrame(rows).to_csv(RESULTS_DIR / "session_calendar_s12_buckets.csv", index=False)
    # C02 statistic
    h1 = tf("H1")
    out = []
    for period in ("train", "validate"):
        a, b = SPLITS[period]
        sub = h1.loc[a:b]
        loc = sub.index.tz_convert("America/New_York")
        day = (loc.tz_localize(None) - pd.Timedelta(hours=17)).normalize()
        g = pd.DataFrame({"h": sub["high"].values, "l": sub["low"].values, "hour": loc.hour, "day": day})
        n_days = g["day"].nunique()
        ih = g.loc[g.groupby("day")["h"].idxmax(), "hour"].value_counts().sort_index() / n_days
        il = g.loc[g.groupby("day")["l"].idxmin(), "hour"].value_counts().sort_index() / n_days
        for hr in range(24):
            out.append(dict(period=period, hour_et=hr, p_high=ih.get(hr, 0.0), p_low=il.get(hr, 0.0)))
    pd.DataFrame(out).to_csv(RESULTS_DIR / "session_calendar_c02_hours.csv", index=False)
    print(pd.DataFrame(out).pivot(index="hour_et", columns="period", values=["p_high", "p_low"]).round(3).to_string())


if __name__ == "__main__":
    args = sys.argv[1:]
    if args == ["analysis"]:
        analysis()
        sys.exit(0)
    fams = args or list(FAMILIES)
    rows = []
    for f in fams:
        try:
            rows.append(run_family(f))
        except Exception as e:  # keep going, record the failure
            import traceback; traceback.print_exc()
            rows.append(dict(family=f, id=FAMILIES[f][0], strategy=FAMILIES[f][1], tf=FAMILIES[f][2], desc=FAMILIES[f][5],
                             survives=False, reason=f"ERROR {e!r}"))
        save_rows(rows[-1:])
    print(pd.DataFrame(rows).to_string())
