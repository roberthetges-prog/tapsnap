# Catalogue test: session / time-of-day, microstructure and calendar entries

Scope: research/strategies.json ids S01-S19, B01, C01-C06, Q04, Q07, Q08 (C07-C10 need event data, left to another agent).
Engine: `eurusd.backtest` (bid data, 1.0 pip spread + 0.2 pip slippage per fill, pessimistic SL-first inside a bar).
Protocol: grid on TRAIN 2003-2015 (best point = avg x sqrt(n) among points with enough trades), the chosen point run once on
VALIDATE 2016-2022; HOLDOUT 2023+ never touched. Survival: val avg > 0, t >= 2, PF >= 1.15, >= 60 % years positive, >= 30
trades, parameter neighbourhood positive on TRAIN. `R` = profit / initial stop; families without a stop are judged in pips.
Code: `src/eurusd/strategies_session.py`; driver `experiments/11_session_calendar.py`; rows `experiments/results/session_calendar.csv`;
per-grid CSVs `experiments/results/*_sc_<family>_train.csv`; S12 buckets `session_calendar_s12_buckets.csv`; C02 `session_calendar_c02_hours.csv`.

Local-time rules use `tz_convert` (Europe/London, America/New_York, Europe/Berlin); the per-trade timestamps were checked by
hand (e.g. S18 enters 07:00 London = 02:00 ET in winter / 03:00 ET in summer; S15 fires 15:00 London in GMT and BST).
ICT entries (S07-S10, S19), S04-S06 and S11 are mechanical RECONSTRUCTIONS of discretionary rules (the docstrings say exactly what).

Engine version: all market- and limit-entry families (every family except S02_m15, S12_hostA, S12_hostB, S13_m15, B01_m15,
which use stop entries only and are unaffected) were re-run on the fixed engine of commit 4fe754c (no same-bar target for limit
fills without M1 proof; market/stop fills may take profit on the entry bar when the stop is not touched).

## Summary

* 26 catalogue ids implemented in 36 families; **none survives validation**.
* Not implementable: Q07 (evidence base, not a strategy), Q08 (GitHub repo inaccessible from this session), S15's equity-rebalancing
  sign (needs MSCI US/Europe monthly returns - Yahoo is rate-limited here; only the price-only month-end variant was tested),
  C02 (a filter, statistic reproduced below, no stand-alone trade).
* Near-miss: S18_nostop (short EUR/USD 07:00-13:00 London, no stop): val +1.46 pips/day, t 2.05, PF 1.14, 7/7 years positive -
  fails only PF >= 1.15; the 0.3-0.5 ADR stop versions and the long US-hours leg are negative on validation (confirms the lead's H01).
* S12 (Asian range width / ADR as breakout filter): on TRAIN the lead's ARB host is best for ratio < 0.4 (avg +0.06R, t 1.8) and the
  0.4-0.6 bucket is negative, but the filtered breakout is flat on VALIDATE (avg -0.006R, t -0.1). The fade leg (Judas, ratio >= 0.6)
  is +0.23R on train in the 0.6-0.8 bucket (n=161) and -0.17R on validate. The width filter does not rescue the London breakout.
* S04/S07 (sweep-and-reverse mirror image): S07 with the 'contra prior-day' bias and TP = opposite side if >= 2R is +0.11-0.14R on
  TRAIN (t 1.2-1.5, n ~420) and -0.10R on VALIDATE; the H1 Frankfurt trap (S04) is negative in both periods. The mirror image of the
  breakout loses too: early-London false breaks are not systematically reversed after costs.
* The Backtrex S01 settings exactly (SL 35 / TP 70 pips, 07-10 UTC entry, flat 12 UTC) give avg -0.026R, PF 0.93, t -1.6 on TRAIN -
  consistent with the vendor's PF 0.87.

## Results (one row per family; several families per catalogue id where the catalogue gives variants)

| id | family | tf | implemented rules | train best params | TRAIN | VALIDATE | verdict |
|---|---|---|---|---|---|---|---|
| S01 | S01_h1 | H1 | same on H1 (Backtrex timeframe) | rng_start=0, rng_end=7, entry_until=10, exit_hour=21, entry_mode=stop, buffer_pips=0.0, sl_mode=range, sl_val=1.0, tp_mode=rr, tp_val=70 | n=2938, wr=0.38, avg=0.023R, PF=1.04, t=0.81, yrs+=0.69 | n=1686, wr=0.37, avg=-0.030R, PF=0.95, t=-0.88, yrs+=0.57 | fails: negative on validation; t-stat -0.88 < 2; PF 0.95 < 1.15; only 57% years positive; parameter neighbourhood not positive on train |
| S01 | S01_m15 | M15 | Asian range 00-07 UTC, entry 07-10 UTC stop/close, Backtrex SL35/TP70 or range-based SL with 2R, exit 12 or 21 UTC | rng_start=0, rng_end=7, entry_until=10, exit_hour=21, entry_mode=stop, buffer_pips=0.0, sl_mode=range, sl_val=1.0, tp_mode=rr, tp_val=70 | n=2938, wr=0.38, avg=0.022R, PF=1.04, t=0.78, yrs+=0.69 | n=1686, wr=0.37, avg=-0.030R, PF=0.95, t=-0.88, yrs+=0.57 | fails: negative on validation; t-stat -0.88 < 2; PF 0.95 < 1.15; only 57% years positive; parameter neighbourhood not positive on train |
| S02 | S02_m15 | M15 | babypips statistical London breakout: stops +/-3 pips placed 07-08 GMT, SL min(opposite side, 25p), TP 1x range or 0.5 ADR, skip if range > 50% ADR14, flat 12 GMT | rng_start=0, rng_end=7, entry_until=8, exit_hour=12, buffer_pips=3.0, sl_mode=range, sl_val=1.0, sl_cap_pips=25, tp_mode=half_adr, tp_val=1.0, max_ratio=0.5 | n=1517, wr=0.37, avg=-0.118R, PF=0.78, t=-4.02, yrs+=0.15 | n=834, wr=0.43, avg=-0.093R, PF=0.79, t=-2.89, yrs+=0.29 | fails: negative on validation; t-stat -2.89 < 2; PF 0.79 < 1.15; only 29% years positive; parameter neighbourhood not positive on train |
| S03 | S03_m15 | M15 | London Ripper: 05:00-07:00 UTC box, first M15 close outside after 07:00, SL opposite edge, TP 1R/2R | rng_start=5, rng_end=7, entry_until=12, exit_hour=12, entry_mode=close, buffer_pips=0.0, sl_mode=range, sl_val=1.0, tp_mode=rr, tp_val=2.0, min_range_pips=3 | n=3170, wr=0.46, avg=-0.049R, PF=0.87, t=-3.28, yrs+=0.08 | n=1767, wr=0.45, avg=-0.090R, PF=0.79, t=-4.37, yrs+=0.14 | fails: negative on validation; t-stat -4.37 < 2; PF 0.79 < 1.15; only 14% years positive; parameter neighbourhood not positive on train |
| S04 | S04_h1 | H1 | Frankfurt trap H1: 07/08 UTC candle takes out Asian range, 08:00 candle closes back inside -> fade at 09:00, SL beyond spike+3p, TP opposite side or 1.5R, flat 12 UTC | rng_start=0, rng_end=7, kz_start=7, kz_end=9, decide_at=8.0, sweep_min_pips=0.0, tp_mode=rr, tp_val=1.5, engulf=True, exit_hour=12 | n=745, wr=0.48, avg=-0.007R, PF=0.98, t=-0.24, yrs+=0.46 | n=459, wr=0.46, avg=-0.013R, PF=0.96, t=-0.39, yrs+=0.29 | fails: negative on validation; t-stat -0.39 < 2; PF 0.96 < 1.15; only 29% years positive; parameter neighbourhood not positive on train |
| S04 | S04_m15 | M15 | same on M15: first M15 close back inside the range during 07-09 UTC | rng_start=0, rng_end=7, kz_start=7, kz_end=9, sweep_min_pips=3.0, tp_mode=range, tp_val=1.5, exit_hour=16, sl_buffer_pips=3.0 | n=1587, wr=0.37, avg=0.005R, PF=1.01, t=0.13, yrs+=0.54 | n=813, wr=0.40, avg=-0.062R, PF=0.90, t=-1.35, yrs+=0.29 | fails: negative on validation; t-stat -1.35 < 2; PF 0.90 < 1.15; only 29% years positive; parameter neighbourhood not positive on train |
| S05 | S05_m15 | M15 | NY-open reversal: |London move since 07:00 London| >= x pips, rejection bar at a new extreme 08:30-10:00 ET, SL beyond extreme+5p, TP 50% retrace / London open, flat 11:00 ET | min_london_move_pips=20, tp_mode=open, require_pd_level=True | n=534, wr=0.37, avg=-0.208R, PF=0.62, t=-4.86, yrs+=0.15 | n=269, wr=0.49, avg=0.042R, PF=1.09, t=0.62, yrs+=0.71 | fails: t-stat 0.62 < 2; PF 1.09 < 1.15; parameter neighbourhood not positive on train |
| S06 | S06_m5 | M5 | London-close scalp 11:00-12:30 ET: new day extreme that fails to close beyond -> fade, TP 10/15p, SL 12/15p or extreme+5p, flat 13:00 ET | sl_pips=15, tp_pips=15, sl_mode=pips | n=972, wr=0.52, avg=-0.034R, PF=0.92, t=-1.26, yrs+=0.38 | n=523, wr=0.44, avg=-0.117R, PF=0.67, t=-3.87, yrs+=0.14 | fails: negative on validation; t-stat -3.87 < 2; PF 0.67 < 1.15; only 14% years positive; parameter neighbourhood not positive on train |
| S07 | S07_ny | M15 | Judas swing (ET clock): Asian range 19:00-02:00 ET, London killzone 02:00-05:00 ET, flat 16:00 ET | tz=America/New_York, day_offset=17.0, rng_start=2.0, rng_end=9.0, kz_start=9.0, kz_end=12.0, sweep_min_pips=3.0, tp_mode=range_min_rr, tp_val=2.0, bias=contra, exit_hour=23.0 | n=407, wr=0.29, avg=0.138R, PF=1.19, t=1.47, yrs+=0.62 | n=177, wr=0.25, avg=-0.094R, PF=0.88, t=-0.76, yrs+=0.43 | fails: negative on validation; t-stat -0.76 < 2; PF 0.88 < 1.15; only 43% years positive |
| S07 | S07_utc | M15 | Judas swing (UTC clock): sweep of the 00-07 UTC range by >= x pips with a close back inside during 07-10 UTC, SL beyond sweep+3p, TP opposite side / 2R / opposite side if >= 2R, daily-bias filter, flat 16 UTC | rng_start=0, rng_end=7, kz_start=7, kz_end=10, sweep_min_pips=3.0, tp_mode=range_min_rr, tp_val=2.0, bias=contra, exit_hour=16 | n=423, wr=0.29, avg=0.114R, PF=1.16, t=1.24, yrs+=0.69 | n=197, wr=0.26, avg=-0.102R, PF=0.86, t=-0.91, yrs+=0.71 | fails: negative on validation; t-stat -0.91 < 2; PF 0.86 < 1.15 |
| S08 | S08_m15 | M15 | NY AM killzone 07-10 ET 3-candle FVG, limit at the gap edge, SL beyond candle-1 extreme, TP R-multiple, flat 16 ET | kz_start=7.0, kz_end=10.0, min_gap_pips=2.0, expiry_bars=8, tp_rr=2.0, exit_hour=16.0 | n=2772, wr=0.37, avg=-0.013R, PF=0.98, t=-0.53, yrs+=0.23 | n=1323, wr=0.36, avg=-0.058R, PF=0.90, t=-1.68, yrs+=0.14 | fails: negative on validation; t-stat -1.68 < 2; PF 0.90 < 1.15; only 14% years positive; parameter neighbourhood not positive on train |
| S09 | S09_m5 | M5 | Silver bullet 10-11 ET M5: sweep of the session / prior-day low-high within the last 1-2 h, then FVG in the reversal direction, SL at sweep extreme or gap, TP 2R, flat 11:30 ET | kz_start=10.0, kz_end=11.0, exit_hour=11.5, require_sweep=True, sl_mode=gap, sweep_level=prev_day, sweep_lookback=12, min_gap_pips=1.5, tp_rr=2.0, expiry_bars=6 | n=451, wr=0.46, avg=0.029R, PF=1.07, t=0.58, yrs+=0.54 | n=221, wr=0.45, avg=0.024R, PF=1.06, t=0.34, yrs+=0.57 | fails: t-stat 0.34 < 2; PF 1.06 < 1.15; only 57% years positive; parameter neighbourhood not positive on train |
| S10 | S10_m15 | M15 | Power of three: London (07-10 UTC) sweeps the 00-07 range and closes back through the 00:00 UTC open -> trade the reversal, SL beyond manipulation extreme, TP opposite side / 2R, flat 17 (12 ET) or 21 UTC | rng_start=0, rng_end=7, kz_start=7, kz_end=10, confirm=daily_open, sweep_min_pips=3.0, tp_mode=range, tp_val=2.0, bias=none, exit_hour=17 | n=671, wr=0.63, avg=0.037R, PF=1.11, t=1.03, yrs+=0.54 | n=352, wr=0.64, avg=-0.044R, PF=0.87, t=-1.02, yrs+=0.43 | fails: negative on validation; t-stat -1.02 < 2; PF 0.87 < 1.15; only 43% years positive |
| S11 | S11_m5 | M5 | Asian range fade 00-06 UTC: touch of the running 22:00-UTC range edge with RSI14 filter, TP midpoint, SL edge+8/12p, flat 06 UTC | min_range_pips=15, max_range_pips=60, sl_pips=12, use_rsi=True, rsi_ob=70, rsi_os=30 | n=2281, wr=0.47, avg=-0.062R, PF=0.85, t=-3.38, yrs+=0.23 | n=1087, wr=0.46, avg=-0.089R, PF=0.74, t=-4.20, yrs+=0.00 | fails: negative on validation; t-stat -4.20 < 2; PF 0.74 < 1.15; only 0% years positive; parameter neighbourhood not positive on train |
| S12 | S12_fade | M15 | S12 fade leg: Judas-swing fade only when range/ADR14 >= min_ratio ('the move already happened') | rng_start=0, rng_end=7, kz_start=7, kz_end=10, sweep_min_pips=3.0, tp_mode=range, exit_hour=16, min_ratio=0.4, adr_len=14 | n=749, wr=0.31, avg=0.036R, PF=1.05, t=0.57, yrs+=0.69 | n=367, wr=0.29, avg=-0.167R, PF=0.76, t=-2.28, yrs+=0.00 | fails: negative on validation; t-stat -2.28 < 2; PF 0.76 < 1.15; only 0% years positive |
| S12 | S12_hostA | M15 | S12 width filter on the lead's best ARB (range 01-08 UTC, stops until 14, SL opposite side, 2-3R, flat 20): breakout only if range/ADR14 <= max_ratio | rng_start=1, rng_end=8, entry_until=14, exit_hour=20, buffer_pips=2.0, sl_mode=range, sl_val=1.0, tp_mode=rr, tp_val=3.0, max_ratio=0.4, adr_len=14 | n=1412, wr=0.40, avg=0.063R, PF=1.12, t=1.76, yrs+=0.69 | n=759, wr=0.40, avg=-0.006R, PF=0.99, t=-0.12, yrs+=0.71 | fails: negative on validation; t-stat -0.12 < 2; PF 0.99 < 1.15 |
| S12 | S12_hostB | M15 | S12 width filter on the catalogue S01 window (00-07 UTC, entries 07-10, flat 12 UTC, SL opposite side, 2R) | rng_start=0, rng_end=7, entry_until=10, exit_hour=12, buffer_pips=2.0, sl_mode=range, sl_val=1.0, tp_mode=rr, tp_val=2.0, max_ratio=0.3, adr_len=14 | n=892, wr=0.43, avg=-0.025R, PF=0.94, t=-0.75, yrs+=0.46 | n=505, wr=0.37, avg=-0.162R, PF=0.67, t=-3.89, yrs+=0.14 | fails: negative on validation; t-stat -3.89 < 2; PF 0.67 < 1.15; only 14% years positive; parameter neighbourhood not positive on train |
| S13 | S13_m15 | M15 | London ORB (FXStreet): range 07:30-08:00 / 08:00-08:30 / 08:00-09:00 London local, break +/-10 pips or 0.1 x daily ATR, SL opposite side, TP 1x/2x range, flat 12:00 London | tz=Europe/London, rng_start=8.0, rng_end=9.0, entry_until=12, exit_hour=12, buffer_pips=10.0, buffer_atr_frac=0.1, sl_mode=range, sl_val=1.0, tp_mode=range, tp_val=2.0, min_range_pips=3 | n=2424, wr=0.46, avg=0.010R, PF=1.04, t=0.83, yrs+=0.62 | n=1323, wr=0.42, avg=-0.051R, PF=0.79, t=-3.28, yrs+=0.14 | fails: negative on validation; t-stat -3.28 < 2; PF 0.79 < 1.15; only 14% years positive; parameter neighbourhood not positive on train |
| S14 | S14_h1 | H1 | WM/R fix pattern: short 13/15:00-16:00 London, long 16:00-20:00 London, 0.3/0.5 ADR stop (legs separately) | legs=post, pre_start=13.0, post_end=20.0, sl_adr=0.3 | n=3361, wr=0.49, avg=0.028R, PF=1.10, t=2.02, yrs+=0.77 | n=1814, wr=0.46, avg=-0.029R, PF=0.91, t=-1.49, yrs+=0.29 | fails: negative on validation; t-stat -1.49 < 2; PF 0.91 < 1.15; only 29% years positive |
| S14 | S14_nostop | H1 | same without stop (academic version, judged in pips) | legs=post, pre_start=13.0, post_end=20.0 | n=3361, wr=0.51, avg=1.207pips, PF=1.11, t=2.02, yrs+=0.77 | n=1814, wr=0.48, avg=-0.358pips, PF=0.96, t=-0.66, yrs+=0.14 | fails: negative on validation; t-stat -0.66 < 2; PF 0.96 < 1.15; only 14% years positive |
| S15 | S15_m15 | M15 | Month-end fix (price-only; equity-rebalancing sign NOT available): last London business day, follow/fade the 13/14:00->15:00 move into the 16:00 fix, 0.4 ADR stop | signal_start=14.0, signal_end=15.0, exit_hour=16.0, mode=follow, sl_adr=0.4 | n=132, wr=0.58, avg=0.185R, PF=1.87, t=2.94, yrs+=0.85 | n=71, wr=0.48, avg=-0.073R, PF=0.79, t=-0.83, yrs+=0.29 | fails: negative on validation; t-stat -0.83 < 2; PF 0.79 < 1.15; only 29% years positive |
| S16 | S16_h1 | H1 | Weekend gap fill: |Sunday open - Friday close| >= x pips and <= r x ATR14(daily), trade toward Friday close, SL 1x gap or 0.5 ATR, time stop Wed 08:00 London or Monday close | min_gap_pips=10.0, max_gap_atr_ratio=9.0, sl_mode=atr, time_stop=mon | n=125, wr=0.76, avg=0.087R, PF=1.41, t=1.36, yrs+=0.77 | n=43, wr=0.60, avg=-0.138R, PF=0.59, t=-1.40, yrs+=0.29 | fails: negative on validation; t-stat -1.40 < 2; PF 0.59 < 1.15; only 29% years positive |
| S17 | S17_h1 | H1 | same on H1 | use_filter=True, sl_atr=1.5, exit_on_opposite=True | n=1222, wr=0.22, avg=-0.022R, PF=0.97, t=-0.38, yrs+=0.54 | n=589, wr=0.20, avg=-0.081R, PF=0.90, t=-1.00, yrs+=0.43 | fails: negative on validation; t-stat -1.00 < 2; PF 0.90 < 1.15; only 43% years positive; parameter neighbourhood not positive on train |
| S17 | S17_m15 | M15 | DailyFX RSI14 30/70 cross range trade, entries only 14:00-06:00 ET (vs 24h control), exit on opposite cross / ATR stop / optional 1R target | use_filter=True, sl_atr=2.5, exit_on_opposite=True | n=3553, wr=0.32, avg=-0.010R, PF=0.99, t=-0.36, yrs+=0.46 | n=1863, wr=0.31, avg=-0.073R, PF=0.89, t=-2.02, yrs+=0.14 | fails: negative on validation; t-stat -2.02 < 2; PF 0.89 < 1.15; only 14% years positive; parameter neighbourhood not positive on train |
| S18 | S18_h1 | H1 | Breedon-Ranaldo: short 07/08:00-13:00 London, long 13:00-21:00 London, 0.3/0.5 ADR stop (legs separately) | legs=short, short_start=8.0, short_end=13.0, long_start=13.0, long_end=21.0, sl_adr=0.3 | n=3365, wr=0.47, avg=0.042R, PF=1.11, t=2.41, yrs+=0.69 | n=1814, wr=0.46, avg=-0.025R, PF=0.94, t=-1.06, yrs+=0.43 | fails: negative on validation; t-stat -1.06 < 2; PF 0.94 < 1.15; only 43% years positive |
| S18 | S18_nostop | H1 | same without stop (paper version, judged in pips) | legs=short, short_start=7.0, short_end=13.0, long_start=13.0, long_end=21.0 | n=3365, wr=0.51, avg=1.666pips, PF=1.11, t=2.15, yrs+=0.85 | n=1817, wr=0.52, avg=1.459pips, PF=1.14, t=2.05, yrs+=1.00 | fails: PF 1.14 < 1.15 |
| S19 | S19_h1 | H1 | Backtrex liquidity sweep: equal highs/lows (2 swing points within 2 pips) or N-bar extreme swept by >= 3 pips with a close back inside, in the London/NY killzones (ET), SL beyond sweep+2p, TP R-multiple | level_mode=equal, lookback=48, sweep_min_pips=3.0, tp_rr=3.0, max_hold=48 | n=1019, wr=0.30, avg=0.083R, PF=1.12, t=1.57, yrs+=0.69 | n=553, wr=0.28, avg=-0.050R, PF=0.93, t=-0.75, yrs+=0.43 | fails: negative on validation; t-stat -0.75 < 2; PF 0.93 < 1.15; only 43% years positive |
| S19 | S19_m15 | M15 | same on M15 (levels from the last 1-2 days of M15 swings) | level_mode=equal, lookback=192, sweep_min_pips=3.0, tp_rr=2.0, max_hold=96 | n=2513, wr=0.35, avg=-0.011R, PF=0.98, t=-0.42, yrs+=0.38 | n=1088, wr=0.35, avg=-0.048R, PF=0.93, t=-1.20, yrs+=0.57 | fails: negative on validation; t-stat -1.20 < 2; PF 0.93 < 1.15; only 57% years positive; parameter neighbourhood not positive on train |
| B01 | B01_fade | M15 | B01 second-break fade: when both sides of the London range break, fade the second break (SL beyond its extreme, TP 0.5/1x range) | tp_val=0.5, entry_until=16.0, exit_hour=17.0 | n=609, wr=0.43, avg=-0.155R, PF=0.71, t=-3.94, yrs+=0.08 | n=315, wr=0.39, avg=-0.254R, PF=0.55, t=-4.95, yrs+=0.00 | fails: negative on validation; t-stat -4.95 < 2; PF 0.55 < 1.15; only 0% years positive; parameter neighbourhood not positive on train |
| B01 | B01_m15 | M15 | 'London sets the range, NY breaks it': stops at the 03-08 ET range after 08 ET, SL midpoint, TP 1x range, flat 17 ET | tz=America/New_York, rng_start=3.0, rng_end=8.0, entry_until=16.0, exit_hour=17.0, buffer_pips=1.0, sl_mode=mid, tp_mode=range, tp_val=1.0 | n=3029, wr=0.37, avg=-0.107R, PF=0.81, t=-5.13, yrs+=0.15 | n=1664, wr=0.36, avg=-0.141R, PF=0.75, t=-5.27, yrs+=0.00 | fails: negative on validation; t-stat -5.27 < 2; PF 0.75 < 1.15; only 0% years positive; parameter neighbourhood not positive on train |
| C01 | C01_h1 | H1 | Seasonax day-of-week: short Monday, long Friday (NY-close FX days or UTC calendar days), time exit, no stop | mode=utc, legs=mon | n=674, wr=0.51, avg=3.391pips, PF=1.13, t=1.17, yrs+=0.69 | n=365, wr=0.45, avg=-3.584pips, PF=0.80, t=-1.60, yrs+=0.29 | fails: negative on validation; t-stat -1.60 < 2; PF 0.80 < 1.15; only 29% years positive |
| C03 | C03_d1 | D1NY | Monthly seasonality: long December (last Nov close -> last Dec close), short May | long_months=[12], short_months=[5] | n=26, wr=0.62, avg=122.985pips, PF=1.84, t=1.19, yrs+=0.62 | n=14, wr=0.64, avg=38.893pips, PF=1.60, t=0.75, yrs+=0.57 | fails: too few validation trades; t-stat 0.75 < 2; only 57% years positive |
| C04 | C04_d1 | D1NY | Turn of month: long/short EUR/USD from T-1 close to T+1 / T+4 close (T = last trading day) | entry_offset=-1, exit_offset=4, side=-1 | n=155, wr=0.55, avg=27.199pips, PF=1.49, t=1.94, yrs+=0.69 | n=83, wr=0.58, avg=-1.918pips, PF=0.96, t=-0.14, yrs+=0.57 | fails: negative on validation; t-stat -0.14 < 2; PF 0.96 < 1.15; only 57% years positive; parameter neighbourhood not positive on train |
| C05 | C05_h1 | H1 | Friday squaring: if the week's move at 13:00 London Friday >= x %, fade it to the Friday close, 0.3/0.5 ADR stop | min_move_pct=0.5, sl_adr=0.5 | n=461, wr=0.44, avg=-0.050R, PF=0.88, t=-1.14, yrs+=0.31 | n=208, wr=0.51, avg=0.042R, PF=1.13, t=0.71, yrs+=0.43 | fails: t-stat 0.71 < 2; PF 1.13 < 1.15; only 43% years positive; parameter neighbourhood not positive on train |
| C06 | C06_d1 | D1NY | Holiday weeks (US Thanksgiving Mon-Fri, Dec 24-Jan 2): continue / fade the prior 10-day trend over the window | which=tg, side_mode=continue, trend_days=10 | n=13, wr=0.77, avg=103.600pips, PF=4.23, t=2.00, yrs+=0.77 | n=7, wr=0.29, avg=0.114pips, PF=1.00, t=0.00, yrs+=0.29 | fails: too few validation trades; t-stat 0.00 < 2; PF 1.00 < 1.15; only 29% years positive |
| Q04 | Q04_h1 | H1 | Popovic-Durovic Friday 00:00-03:00 (CET or UTC) hold, direction chosen on TRAIN | tz=Europe/Berlin, entry_hour=0.0, exit_hour=3.0, side=-1, dows=[4] | n=671, wr=0.54, avg=1.790pips, PF=1.35, t=2.64, yrs+=0.62 | n=364, wr=0.38, avg=-1.870pips, PF=0.64, t=-2.52, yrs+=0.29 | fails: negative on validation; t-stat -2.52 < 2; PF 0.64 < 1.15; only 29% years positive; parameter neighbourhood not positive on train |

Notes: `tp_val=70` with `tp_mode=rr` (S01) is effectively 'no target' (time exit). Stop/limit OCO pairs are resolved on the
bars (the side that triggers first is the one placed), so the breakout rows are not biased toward the long side.

## S12: expectancy by Asian-range / ADR(14) bucket (TRAIN only)

| host | bucket | n | win rate | avg R | PF | t | years+ |
|---|---|---|---|---|---|---|---|
| breakout_hostA(01-08,flat20,3R) | [0,0.3) | 609 | 0.38 | 0.062 | 1.11 | 1.06 | 0.69 |
| breakout_hostA(01-08,flat20,3R) | [0.3,0.4) | 803 | 0.42 | 0.063 | 1.13 | 1.42 | 0.54 |
| breakout_hostA(01-08,flat20,3R) | [0.4,0.5) | 732 | 0.43 | -0.028 | 0.94 | -0.71 | 0.46 |
| breakout_hostA(01-08,flat20,3R) | [0.5,0.6) | 426 | 0.46 | -0.022 | 0.94 | -0.49 | 0.38 |
| breakout_hostA(01-08,flat20,3R) | [0.6,0.8) | 400 | 0.47 | 0.017 | 1.05 | 0.43 | 0.62 |
| breakout_hostA(01-08,flat20,3R) | [0.8,9) | 174 | 0.57 | 0.086 | 1.49 | 2.09 | 0.54 |
| breakout_hostB(00-07,flat12,2R) | [0,0.3) | 892 | 0.43 | -0.025 | 0.94 | -0.75 | 0.46 |
| breakout_hostB(00-07,flat12,2R) | [0.3,0.4) | 821 | 0.47 | -0.019 | 0.95 | -0.66 | 0.38 |
| breakout_hostB(00-07,flat12,2R) | [0.4,0.5) | 510 | 0.46 | -0.036 | 0.88 | -1.12 | 0.23 |
| breakout_hostB(00-07,flat12,2R) | [0.5,0.6) | 285 | 0.51 | 0.018 | 1.08 | 0.52 | 0.38 |
| breakout_hostB(00-07,flat12,2R) | [0.6,0.8) | 238 | 0.42 | -0.044 | 0.81 | -1.33 | 0.38 |
| breakout_hostB(00-07,flat12,2R) | [0.8,9) | 78 | 0.49 | 0.007 | 1.06 | 0.18 | 0.46 |
| judas_fade(00-07,kz07-10,TP=range) | [0,0.3) | 605 | 0.44 | -0.053 | 0.90 | -1.10 | 0.46 |
| judas_fade(00-07,kz07-10,TP=range) | [0.3,0.4) | 552 | 0.41 | 0.036 | 1.06 | 0.58 | 0.62 |
| judas_fade(00-07,kz07-10,TP=range) | [0.4,0.5) | 346 | 0.34 | 0.080 | 1.12 | 0.88 | 0.46 |
| judas_fade(00-07,kz07-10,TP=range) | [0.5,0.6) | 188 | 0.28 | -0.065 | 0.91 | -0.53 | 0.46 |
| judas_fade(00-07,kz07-10,TP=range) | [0.6,0.8) | 161 | 0.33 | 0.233 | 1.35 | 1.40 | 0.62 |
| judas_fade(00-07,kz07-10,TP=range) | [0.8,9) | 54 | 0.19 | -0.477 | 0.40 | -3.00 | 0.17 |

## C02: share of NY-close days whose high / low is set in each ET hour (random = 0.042)

| hour ET | P(high) train | P(high) validate | P(low) train | P(low) validate |
|---|---|---|---|---|
| 00 | 0.011 | 0.011 | 0.013 | 0.008 |
| 01 | 0.020 | 0.025 | 0.016 | 0.017 |
| 02 | 0.060 | 0.044 | 0.046 | 0.046 |
| 03 | 0.051 | 0.076 | 0.060 | 0.059 |
| 04 | 0.051 | 0.047 | 0.038 | 0.031 |
| 05 | 0.037 | 0.033 | 0.030 | 0.038 |
| 06 | 0.031 | 0.031 | 0.028 | 0.029 |
| 07 | 0.028 | 0.034 | 0.036 | 0.036 |
| 08 | 0.070 | 0.068 | 0.082 | 0.071 |
| 09 | 0.054 | 0.066 | 0.056 | 0.067 |
| 10 | 0.073 | 0.092 | 0.087 | 0.089 |
| 11 | 0.064 | 0.052 | 0.070 | 0.057 |
| 12 | 0.050 | 0.031 | 0.046 | 0.043 |
| 13 | 0.038 | 0.043 | 0.032 | 0.033 |
| 14 | 0.046 | 0.048 | 0.046 | 0.051 |
| 15 | 0.032 | 0.040 | 0.028 | 0.041 |
| 16 | 0.049 | 0.051 | 0.044 | 0.061 |
| 17 | 0.086 | 0.041 | 0.062 | 0.088 |
| 18 | 0.030 | 0.033 | 0.036 | 0.025 |
| 19 | 0.039 | 0.028 | 0.037 | 0.023 |
| 20 | 0.027 | 0.033 | 0.049 | 0.043 |
| 21 | 0.021 | 0.037 | 0.034 | 0.022 |
| 22 | 0.018 | 0.019 | 0.017 | 0.015 |
| 23 | 0.012 | 0.017 | 0.010 | 0.009 |

The DailyFX pattern is reproduced: the 08-11 ET block sets the daily extreme ~7-9 % per hour (random 4.2 %), the 02-04 ET
(European open) block 5-6 %, and 17 ET (NY close / Asian open) 4-9 %; 22-01 ET almost never. It is a stop-placement / filter
fact, not a trade.

## Not implementable / not tested

| id | reason |
|---|---|
| S15 (signal) | needs MSCI US vs Europe monthly returns (no equity index data in data/macro; Yahoo returns HTTP 429 here); price-only variant tested above |
| C02 | filter / statistic only (reproduced above) |
| Q07 | academic evidence base for M03/M04 (1-min mean reversion), not a strategy |
| Q08 | GitHub repository not reachable from this session (gh api 403); no rules in the catalogue to reconstruct |
| C07-C10 | out of scope (event data being collected by another agent) |
