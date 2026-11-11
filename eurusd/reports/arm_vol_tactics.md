# Arm J: vol_tactics - intraday tactics conditioned on a walk-forward range forecast

## Verdict (read this first)
**Clean negative.** The day's range is forecastable (out-of-sample R2 0.42-0.49 in pips, tercile accuracy 61-64 %), but
conditioning the three intraday tactics on that forecast does not make any of them profitable after costs.
All 9 conditioned variants have a NEGATIVE 2010-2026 net Sharpe at the round-1 cost (1.0 pip spread + 0.2 slippage per
stop fill). The variant chosen by the pre-declared rule, `AB_R` (Asian-range breakout on days forecast to be more
volatile than the recent norm), has net Sharpe -0.25 / -0.40 / -0.27 for 2010-26 / 2016-26 / 2023-26 (t -1.04 / -1.33 /
-0.54), hit rate 28 %. It fails every part of the success bar and adds nothing to the two-arm combination.
Conditioning does move results in the hypothesised direction when the class is RELATIVE to the recent norm (breakout:
net SR -0.98 unconditioned -> -0.25 on predicted-volatile days, gross SR -0.30 -> +0.12; mirrored class -0.89), but the
gain is smaller than the cost. With an ABSOLUTE class the hypothesis is reversed: fades do worst on quiet days.
Even PERFECT foresight of the day's realised range tercile would only give net SR +0.78 (breakout, volatile days) and
+1.08 (extension fade, quiet days); a forecast that is right 62 % of the time leaves nothing.

## Idea
Direction is barely predictable, range is strongly predictable. Round 1 tested the Asian-range breakout, range fades
and extension fades unconditionally; all failed after costs. Hypothesis: fades work on days forecast to be quiet and
breakouts on days forecast to be volatile, so a good range forecast known at 07:00 London (or at the prior NY close)
should switch the right tactic on.

## Step 1 - walk-forward range forecast
* One row per NY-close session (22:00 UTC -> 22:00 UTC, the feature store's session key), 2003-2026, 6,178 sessions,
  built from M15 bars (range) and M5 returns (realised vol); cache `data/processed/vol_tactics_days.parquet`.
* Targets: high-low range in pips of (i) the whole session and (ii) the London window 07:00-16:00 London time.
* Model: OLS on log(range), refitted each year with `eurusd.wf.walk_forward` on rows whose target is known before
  Y-01-01 (expanding window from 2003, test years 2010-2026). Forecast in pips = exp(pred + s2/2) (conditional mean, used
  for R2 / RMSE) and exp(pred) (conditional median, used for MAE and for the classes).
* Features known at the session start ("close" forecast): HAR lags (previous session, 5-session mean, 22-session mean)
  of log session range, log realised vol (5-minute returns) and log London-window range; log VIX (store column of the
  previous session, itself lagged one calendar day); dummies for scheduled FOMC / ECB / NFP / US CPI in the session and
  FOMC in the previous session; day-of-week dummies. The "07:00" forecast adds the same day's Asian-session range and
  realised vol (session start -> 07:00 London) and the opening gap.
* Event calendars: `data/macro/fomc_decisions.csv` (scheduled), `ecb_decisions.csv`, `us_bls_releases.csv` (from 2010;
  before 2010 NFP = first Friday of the month, CPI flag = 0). Scheduled dates are known in advance, no lag needed.
  The store's `n_high_next_24h` / `h_to_*` were NOT used directly: the ForexFactory "high impact" coverage is uneven
  (2024-25 nearly empty) and the 24h window measured from Friday's close misses Monday; the flags above are built from
  the same `data/macro` calendars with a consistent definition and the session's own window.
* Sessions with missing bars (fewer than 84 of 96 M15 bars in the session / 33 of 36 in the London window) have no target
  and are not scored: 114 of 258 sessions in 2023 (Feb-Jul, the missing-hours block in `data/DATA_QUALITY.md`)
  and 12 sessions in all other years 2010-2026. Lag features use whatever bars exist.

### Out-of-sample accuracy (pips; R2 = 1 - SSE / SSE of the out-of-sample mean; naive = 20-day mean and yesterday's range)
| forecast | period | n | mean range | R2 | R2 log | R2 20d-mean | R2 yesterday | MAE | MAE 20d-mean | MAE yesterday | RMSE | RMSE 20d-mean | RMSE yesterday |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| session range, forecast at session start (prior NY close) | 2010-2026 | 4248 | 92.0 | 0.42 | 0.47 | 0.35 | -0.04 | 26.4 | 28.5 | 36.5 | 38.9 | 40.9 | 51.9 |
|  | 2016-2026 | 2696 | 76.7 | 0.27 | 0.32 | 0.17 | -0.32 | 22.3 | 24.2 | 30.9 | 32.7 | 34.8 | 44.0 |
|  | 2023-2026 | 884 | 70.4 | 0.21 | 0.24 | 0.11 | -0.28 | 21.3 | 23.4 | 28.6 | 31.3 | 33.2 | 39.6 |
| session range, forecast at 07:00 London (Asian part known) | 2010-2026 | 4248 | 92.0 | 0.49 | 0.53 | 0.35 | -0.04 | 24.9 | 28.5 | 36.5 | 36.3 | 40.9 | 51.9 |
|  | 2016-2026 | 2696 | 76.7 | 0.38 | 0.40 | 0.17 | -0.32 | 21.1 | 24.2 | 30.9 | 30.0 | 34.8 | 44.0 |
|  | 2023-2026 | 884 | 70.4 | 0.33 | 0.33 | 0.11 | -0.28 | 20.3 | 23.4 | 28.6 | 28.8 | 33.2 | 39.6 |
| London-window range, forecast at session start | 2010-2026 | 4249 | 73.6 | 0.43 | 0.47 | 0.34 | -0.11 | 21.0 | 23.0 | 30.1 | 30.3 | 32.4 | 42.1 |
|  | 2016-2026 | 2695 | 61.4 | 0.30 | 0.33 | 0.18 | -0.37 | 17.6 | 19.5 | 25.4 | 25.4 | 27.4 | 35.6 |
|  | 2023-2026 | 882 | 55.5 | 0.19 | 0.21 | 0.08 | -0.48 | 16.8 | 18.5 | 23.7 | 24.0 | 25.5 | 32.4 |
| London-window range, forecast at 07:00 London | 2010-2026 | 4249 | 73.6 | 0.45 | 0.49 | 0.34 | -0.11 | 20.7 | 23.0 | 30.1 | 29.8 | 32.4 | 42.1 |
|  | 2016-2026 | 2695 | 61.4 | 0.34 | 0.36 | 0.18 | -0.37 | 17.3 | 19.5 | 25.4 | 24.7 | 27.4 | 35.6 |
|  | 2023-2026 | 882 | 55.5 | 0.24 | 0.25 | 0.08 | -0.48 | 16.4 | 18.5 | 23.7 | 23.2 | 25.5 | 32.4 |
| session range, HAR-only (3 range lags) | 2010-2026 | 4248 | 92.0 | 0.37 | 0.42 | 0.35 | -0.04 | 27.6 | 28.5 | 36.5 | 40.4 | 40.9 | 51.9 |
|  | 2016-2026 | 2696 | 76.7 | 0.20 | 0.26 | 0.17 | -0.32 | 23.2 | 24.2 | 30.9 | 34.1 | 34.8 | 44.0 |
|  | 2023-2026 | 884 | 70.4 | 0.15 | 0.17 | 0.11 | -0.28 | 22.3 | 23.4 | 28.6 | 32.3 | 33.2 | 39.6 |
| London-window range, HAR-only | 2010-2026 | 4249 | 73.6 | 0.36 | 0.39 | 0.34 | -0.11 | 22.3 | 23.0 | 30.1 | 32.1 | 32.4 | 42.1 |
|  | 2016-2026 | 2695 | 61.4 | 0.21 | 0.25 | 0.18 | -0.37 | 18.8 | 19.5 | 25.4 | 27.0 | 27.4 | 35.6 |
|  | 2023-2026 | 882 | 55.5 | 0.13 | 0.14 | 0.08 | -0.48 | 17.7 | 18.5 | 23.7 | 24.8 | 25.5 | 32.4 |

The forecast beats yesterday's range by 25 % RMSE (as `volatility.py`'s HAR does) and the 20-day mean by 5 % (session
start) to 11 % (07:00 London). Event dummies, day of week and the vol lags add about 5 points of R2 to a plain HAR; the
Asian session adds another 7 points for the whole-session range (partly mechanical: the Asian range is part of it) and 2
points for the London window (not mechanical: disjoint windows). Skill decays in the low-vol years: R2 0.19-0.33 in 2023-26.

### Classification accuracy (thresholds = median / terciles of the realised range in the TRAINING window)
| forecast | period | share above train median | acc median: model | 20d-mean | yesterday | always-majority | acc tercile: model | 20d-mean  | yesterday  | always-majority  | acc vs own 20d mean: model | yesterday   | always-below | Brier model | Brier base rate | Brier yesterday |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| close_day | 2010-2026 | 0.307 | 0.777 | 0.750 | 0.700 | 0.693 | 0.609 | 0.572 | 0.537 | 0.530 | 0.632 | 0.544 | 0.580 | 0.155 | 0.213 | 0.300 |
| close_day | 2016-2026 | 0.219 | 0.802 | 0.777 | 0.733 | 0.781 | 0.637 | 0.596 | 0.557 | 0.615 | 0.635 | 0.540 | 0.583 | 0.143 | 0.171 | 0.267 |
| close_day | 2023-2026 | 0.202 | 0.800 | 0.778 | 0.738 | 0.798 | 0.655 | 0.602 | 0.571 | 0.630 | 0.664 | 0.559 | 0.594 | 0.143 | 0.161 | 0.262 |
| l07_day | 2010-2026 | 0.307 | 0.793 | 0.750 | 0.700 | 0.693 | 0.636 | 0.572 | 0.537 | 0.530 | 0.673 | 0.544 | 0.580 | 0.145 | 0.213 | 0.300 |
| l07_day | 2016-2026 | 0.219 | 0.807 | 0.777 | 0.733 | 0.781 | 0.654 | 0.596 | 0.557 | 0.615 | 0.669 | 0.540 | 0.583 | 0.134 | 0.171 | 0.267 |
| l07_day | 2023-2026 | 0.202 | 0.803 | 0.778 | 0.738 | 0.798 | 0.658 | 0.602 | 0.571 | 0.630 | 0.672 | 0.559 | 0.594 | 0.136 | 0.161 | 0.262 |
| close_lon | 2010-2026 | 0.317 | 0.776 | 0.741 | 0.687 | 0.683 | 0.617 | 0.573 | 0.515 | 0.519 | 0.634 | 0.534 | 0.586 | 0.155 | 0.217 | 0.313 |
| close_lon | 2016-2026 | 0.224 | 0.807 | 0.769 | 0.715 | 0.776 | 0.649 | 0.599 | 0.535 | 0.613 | 0.632 | 0.528 | 0.584 | 0.143 | 0.174 | 0.285 |
| close_lon | 2023-2026 | 0.200 | 0.800 | 0.787 | 0.710 | 0.800 | 0.658 | 0.586 | 0.544 | 0.637 | 0.639 | 0.539 | 0.588 | 0.145 | 0.160 | 0.290 |
| l07_lon | 2010-2026 | 0.317 | 0.776 | 0.741 | 0.687 | 0.683 | 0.616 | 0.573 | 0.515 | 0.519 | 0.646 | 0.534 | 0.586 | 0.152 | 0.217 | 0.313 |
| l07_lon | 2016-2026 | 0.224 | 0.802 | 0.769 | 0.715 | 0.776 | 0.649 | 0.599 | 0.535 | 0.613 | 0.645 | 0.528 | 0.584 | 0.140 | 0.174 | 0.285 |
| l07_lon | 2023-2026 | 0.200 | 0.802 | 0.787 | 0.710 | 0.800 | 0.661 | 0.586 | 0.544 | 0.637 | 0.645 | 0.539 | 0.588 | 0.142 | 0.160 | 0.290 |

Reading: with thresholds from the 2003-onwards training window, 69 % of 2010-2026 days (78 % of 2016-2026) are below the
training median because volatility has fallen, so "always quiet" is a strong baseline. The model is right on 78 % of
days for the median split (always-majority 69 %, 20-day mean 75 %) and on 61-64 % for terciles (always-majority 53 %,
20-day mean 57 %); in 2016-2026 the tercile edge over always-majority is only 2-4 points. The regime-free question
"will today's range exceed its own 20-day mean?" is answered correctly on 63-67 % of days (always-below 58 %, yesterday's
range 54 %). Brier score of P(range > training median) 0.155 vs 0.213 for the base rate. So: real, useful for sizing and
cones, but a 5-10 point edge over simple baselines, not a day-type oracle.

Saved for the scoreboard: `data/processed/vol_tactics_range_forecast.parquet` (index session start; `date`,
`forecast_pips`, `realised_pips`, `class` = quiet / normal / volatile from the session-start forecast; plus the median
forecast, thresholds, naive baselines, and the 07:00 London forecasts and classes for the session and the London window).

## Step 2 - tactics (definitions fixed in the module docstring before any P&L was computed; nothing tuned)
M15 bars on `eurusd.backtest.run_backtest` with M1 arbitration of intrabar order, bid prices, buys at ask. Asian range =
high / low of [session start, 07:00 London), AR = its width. Orders placed at 07:00 London, live until 12:00 London,
any open trade closed at 16:00 London; at most one trade per day (OCO). Days with AR < 10 pips (AF / AB) or with missing
bars in the Asian or London window are skipped (114 sessions of 2023).
* **AF** fade of the Asian extremes: sell limit at the Asian high, buy limit at the Asian low, target = Asian mid,
  stop = 0.5 AR beyond the extreme.
* **AB** Asian-range breakout: buy stop 1 pip above the Asian high, sell stop 1 pip below the low, stop = Asian mid,
  no target (time exit).
* **EF** London-morning extension fade: limits at session open +- 0.5 x forecast session range (07:00 forecast; only on
  a side Asia has not already reached), target half-way back (open +- 0.25 F), stop at open +- 0.75 F.
* Costs: `cost_pips = 1.2` = spread 1.0 pip (once per round trip) + 0.2 pip slippage on every stop / market fill (round 1's
  model; 1.2-1.4 pips per round trip). Sensitivities: 0.6 (0.5 + 0.1) and 2.4 (2.0 + 0.4, about the HOWTO's 1.2 pips per
  side). Each cost level is a separate engine run (the spread changes which orders trigger).
* Day classes (thresholds from the training window only): **A** absolute = tercile of the 07:00 London-window forecast
  against the training terciles of the realised London range; **R** relative = tercile of forecast / mean of the previous
  20 realised London ranges against the training terciles of the same fitted ratio (balanced within each year);
  **C** = as A but from the session-start forecast of the whole-session range. Quiet = bottom tercile, volatile = top.
  Under A and C the volatile class is rare after 2011 (0-22 % of days per year, usually under 5 %) and quiet dominates
  the low-vol years (up to 97 % of days), so A / C are close to a regime switch between years; R is balanced within a year.
* Stream: one row per decision (session, stamped 07:00 London in UTC), `pos` = side of the trade taken (0 if none),
  `fwd_bp` = price move entry -> exit before costs (pos x fwd_bp = gross), `net_bp` after costs;
  `report(periods_per_year = 259.5 decisions per year, n_arms = 12)`.

### The 12 variants (all that were run for selection; net Sharpe at cost 1.2 unless stated)
Selection rule declared before results: best 2010-2015 net Sharpe among the 9 conditioned variants with >= 60 trades in
2010-2015. `_U` = unconditioned control; AF_* / EF_* trade predicted-quiet days, AB_* predicted-volatile days, SW_* = AF
on quiet + AB on volatile.
| variant | SR 2010-15 | SR 2010-26 | t 2010-26 | SR 2016-26 | t 2016-26 | SR 2023-26 | t 2023-26 | gross SR 2010-26 | trades | hit net | avg net pips | SR 2010-26 @0.6 | SR 2016-26 @0.6 | SR 2010-26 @2.4 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| AF_U [control] | -0.52 | -0.85 | -3.50 | -1.14 | -3.75 | -0.85 | -1.66 | +0.08 | 3911 | +0.46 | -0.97 | -0.44 | -0.60 | -1.61 |
| AF_A | -1.16 | -1.22 | -5.02 | -1.27 | -4.17 | -1.01 | -1.98 | -0.23 | 2024 | +0.44 | -1.39 | -0.75 | -0.71 | -2.04 |
| AF_R | -0.17 | -0.39 | -1.58 | -0.67 | -2.20 | +0.01 | +0.01 | +0.16 | 1217 | +0.46 | -0.68 | -0.18 | -0.38 | -0.78 |
| AB_U [control] | -1.09 | -0.98 | -4.02 | -0.91 | -3.01 | -0.61 | -1.20 | -0.30 | 3911 | +0.26 | -1.97 | -0.55 | -0.47 | -1.92 |
| AB_A | -0.99 | -0.48 | -1.98 | +0.04 | +0.13 | -0.08 | -0.16 | -0.36 | 371 | +0.25 | -5.70 | -0.40 | +0.17 | -0.63 |
| AB_R (final) | -0.00 | -0.25 | -1.04 | -0.40 | -1.33 | -0.27 | -0.54 | +0.12 | 1400 | +0.28 | -0.88 | +0.04 | -0.09 | -0.82 |
| EF_U [control] | -0.55 | -0.72 | -2.97 | -0.88 | -2.91 | -1.04 | -2.04 | -0.27 | 1462 | +0.46 | -1.73 | -0.45 | -0.59 | -1.22 |
| EF_A | -0.04 | -0.61 | -2.52 | -0.87 | -2.87 | -0.36 | -0.70 | -0.16 | 760 | +0.47 | -1.44 | -0.41 | -0.62 | -1.17 |
| EF_R | -0.35 | -0.29 | -1.19 | -0.26 | -0.87 | -0.09 | -0.18 | -0.03 | 496 | +0.49 | -1.25 | -0.19 | -0.16 | -0.71 |
| SW_A | -1.31 | -1.04 | -4.25 | -0.85 | -2.79 | -0.80 | -1.58 | -0.43 | 2395 | +0.41 | -2.05 | -0.72 | -0.37 | -1.59 |
| SW_R | -0.09 | -0.40 | -1.63 | -0.60 | -1.99 | -0.26 | -0.51 | +0.18 | 2617 | +0.37 | -0.79 | -0.04 | -0.20 | -1.09 |
| SW_C | -1.40 | -1.19 | -4.87 | -1.06 | -3.48 | -0.73 | -1.44 | -0.59 | 2353 | +0.40 | -2.35 | -0.88 | -0.59 | -1.74 |

No variant is positive over 2010-2026 at 1.2 pips; at 0.6 pips the best is +0.04; at 2.4 pips everything is below -0.6.

### Conditioned vs unconditioned, every tactic by predicted class (2010-2026, cost 1.2)
"ORACLE" rows use the REALISED London-range tercile (perfect foresight; diagnostic / leak check, not tradable).
| tactic | conditioning | class | days | trades | net SR | t | gross SR | avg net pips | hit net | hit gross |
|---|---|---|---|---|---|---|---|---|---|---|
| AF | none (control) | all | 4369 | 3911 | -0.85 | -3.50 | +0.08 | -0.97 | +0.46 | +0.46 |
| AF | A absolute | quiet | 2288 | 2024 | -1.22 | -5.02 | -0.23 | -1.39 | +0.44 | +0.44 |
| AF | A absolute | normal | 1673 | 1516 | -0.63 | -2.59 | -0.12 | -1.32 | +0.47 | +0.47 |
| AF | A absolute | volatile | 408 | 371 | +0.35 | +1.44 | +0.50 | +2.72 | +0.54 | +0.54 |
| AF | R relative | quiet | 1327 | 1217 | -0.39 | -1.58 | +0.16 | -0.68 | +0.46 | +0.46 |
| AF | R relative | normal | 1434 | 1294 | -0.31 | -1.29 | +0.24 | -0.60 | +0.47 | +0.47 |
| AF | R relative | volatile | 1608 | 1400 | -0.74 | -3.03 | -0.22 | -1.56 | +0.45 | +0.45 |
| AF | ORACLE (realised) | quiet | 2207 | 1979 | -0.47 | -1.93 | +0.44 | -0.55 | +0.47 | +0.47 |
| AF | ORACLE (realised) | normal | 1261 | 1191 | -0.60 | -2.46 | -0.11 | -1.32 | +0.45 | +0.45 |
| AF | ORACLE (realised) | volatile | 781 | 741 | -0.42 | -1.71 | -0.15 | -1.53 | +0.47 | +0.47 |
| AB | none (control) | all | 4369 | 3911 | -0.98 | -4.02 | -0.30 | -1.97 | +0.26 | +0.26 |
| AB | A absolute | quiet | 2288 | 2024 | -0.62 | -2.54 | +0.06 | -1.22 | +0.26 | +0.26 |
| AB | A absolute | normal | 1673 | 1516 | -0.60 | -2.46 | -0.22 | -2.06 | +0.25 | +0.26 |
| AB | A absolute | volatile | 408 | 371 | -0.48 | -1.98 | -0.36 | -5.70 | +0.25 | +0.25 |
| AB | R relative | quiet | 1327 | 1217 | -0.89 | -3.67 | -0.50 | -3.07 | +0.23 | +0.24 |
| AB | R relative | normal | 1434 | 1294 | -0.62 | -2.56 | -0.22 | -2.11 | +0.25 | +0.26 |
| AB | R relative | volatile | 1608 | 1400 | -0.25 | -1.04 | +0.12 | -0.88 | +0.28 | +0.28 |
| AB | ORACLE (realised) | quiet | 2207 | 1979 | -3.72 | -15.25 | -2.85 | -5.53 | +0.23 | +0.23 |
| AB | ORACLE (realised) | normal | 1261 | 1191 | -0.28 | -1.16 | +0.10 | -1.12 | +0.29 | +0.29 |
| AB | ORACLE (realised) | volatile | 781 | 741 | +0.78 | +3.19 | +0.94 | +6.17 | +0.29 | +0.29 |
| EF | none (control) | all | 4369 | 1462 | -0.72 | -2.97 | -0.27 | -1.73 | +0.46 | +0.46 |
| EF | A absolute | quiet | 2288 | 760 | -0.61 | -2.52 | -0.16 | -1.44 | +0.47 | +0.47 |
| EF | A absolute | normal | 1673 | 561 | -0.62 | -2.56 | -0.38 | -2.87 | +0.44 | +0.44 |
| EF | A absolute | volatile | 408 | 141 | +0.08 | +0.31 | +0.16 | +1.23 | +0.52 | +0.52 |
| EF | R relative | quiet | 1327 | 496 | -0.29 | -1.19 | -0.03 | -1.25 | +0.49 | +0.49 |
| EF | R relative | normal | 1434 | 512 | -0.37 | -1.52 | -0.10 | -1.53 | +0.46 | +0.46 |
| EF | R relative | volatile | 1608 | 454 | -0.59 | -2.42 | -0.35 | -2.49 | +0.43 | +0.43 |
| EF | ORACLE (realised) | quiet | 2207 | 596 | +1.08 | +4.41 | +1.45 | +3.05 | +0.59 | +0.59 |
| EF | ORACLE (realised) | normal | 1261 | 499 | -0.41 | -1.68 | -0.15 | -1.55 | +0.42 | +0.42 |
| EF | ORACLE (realised) | volatile | 781 | 367 | -1.56 | -6.39 | -1.40 | -9.76 | +0.31 | +0.31 |

### Same table, 2016-2026
| tactic | conditioning | class | days | trades | net SR | t | gross SR | avg net pips | hit net | hit gross |
|---|---|---|---|---|---|---|---|---|---|---|
| AF | none (control) | all | 2813 | 2473 | -1.14 | -3.75 | -0.03 | -1.14 | +0.46 | +0.46 |
| AF | A absolute | quiet | 1797 | 1585 | -1.27 | -4.17 | -0.13 | -1.24 | +0.45 | +0.45 |
| AF | A absolute | normal | 914 | 803 | -0.51 | -1.67 | +0.02 | -1.05 | +0.47 | +0.47 |
| AF | A absolute | volatile | 102 | 85 | +0.00 | +0.00 | +0.11 | -0.05 | +0.49 | +0.49 |
| AF | R relative | quiet | 657 | 584 | -0.67 | -2.20 | -0.05 | -1.17 | +0.45 | +0.45 |
| AF | R relative | normal | 936 | 834 | -0.56 | -1.83 | +0.15 | -0.90 | +0.46 | +0.46 |
| AF | R relative | volatile | 1220 | 1055 | -0.76 | -2.50 | -0.11 | -1.31 | +0.46 | +0.46 |
| AF | ORACLE (realised) | quiet | 1651 | 1491 | -0.61 | -2.00 | +0.44 | -0.64 | +0.47 | +0.47 |
| AF | ORACLE (realised) | normal | 758 | 715 | -0.86 | -2.83 | -0.30 | -1.76 | +0.43 | +0.43 |
| AF | ORACLE (realised) | volatile | 286 | 267 | -0.50 | -1.63 | -0.26 | -2.28 | +0.45 | +0.45 |
| AB | none (control) | all | 2813 | 2473 | -0.91 | -3.01 | -0.11 | -1.54 | +0.26 | +0.27 |
| AB | A absolute | quiet | 1797 | 1585 | -0.66 | -2.17 | +0.12 | -1.15 | +0.26 | +0.26 |
| AB | A absolute | normal | 914 | 803 | -0.76 | -2.51 | -0.36 | -2.58 | +0.26 | +0.26 |
| AB | A absolute | volatile | 102 | 85 | +0.04 | +0.13 | +0.11 | +0.85 | +0.31 | +0.31 |
| AB | R relative | quiet | 657 | 584 | -0.52 | -1.73 | -0.10 | -1.75 | +0.24 | +0.25 |
| AB | R relative | normal | 936 | 834 | -0.74 | -2.43 | -0.22 | -1.91 | +0.26 | +0.26 |
| AB | R relative | volatile | 1220 | 1055 | -0.40 | -1.33 | +0.06 | -1.14 | +0.27 | +0.28 |
| AB | ORACLE (realised) | quiet | 1651 | 1491 | -3.79 | -12.49 | -2.80 | -4.93 | +0.23 | +0.24 |
| AB | ORACLE (realised) | normal | 758 | 715 | +0.58 | +1.90 | +0.96 | +2.10 | +0.31 | +0.31 |
| AB | ORACLE (realised) | volatile | 286 | 267 | +0.79 | +2.59 | +0.92 | +7.64 | +0.29 | +0.29 |
| EF | none (control) | all | 2813 | 849 | -0.88 | -2.91 | -0.38 | -1.93 | +0.45 | +0.45 |
| EF | A absolute | quiet | 1797 | 562 | -0.87 | -2.87 | -0.37 | -1.93 | +0.45 | +0.45 |
| EF | A absolute | normal | 914 | 258 | -0.36 | -1.18 | -0.12 | -1.70 | +0.46 | +0.46 |
| EF | A absolute | volatile | 102 | 29 | -0.20 | -0.65 | -0.14 | -4.11 | +0.45 | +0.45 |
| EF | R relative | quiet | 657 | 211 | -0.26 | -0.87 | +0.01 | -1.03 | +0.49 | +0.49 |
| EF | R relative | normal | 936 | 306 | -0.35 | -1.15 | -0.03 | -1.30 | +0.47 | +0.47 |
| EF | R relative | volatile | 1220 | 332 | -0.83 | -2.75 | -0.54 | -3.09 | +0.41 | +0.41 |
| EF | ORACLE (realised) | quiet | 1651 | 429 | +0.94 | +3.09 | +1.36 | +2.33 | +0.57 | +0.57 |
| EF | ORACLE (realised) | normal | 758 | 290 | -1.26 | -4.14 | -0.98 | -4.96 | +0.35 | +0.35 |
| EF | ORACLE (realised) | volatile | 286 | 130 | -1.27 | -4.17 | -1.13 | -9.25 | +0.28 | +0.28 |

### Same table, 2023-2026
| tactic | conditioning | class | days | trades | net SR | t | gross SR | avg net pips | hit net | hit gross |
|---|---|---|---|---|---|---|---|---|---|---|
| AF | none (control) | all | 998 | 790 | -0.85 | -1.66 | +0.27 | -0.82 | +0.46 | +0.46 |
| AF | A absolute | quiet | 675 | 546 | -1.01 | -1.98 | +0.15 | -0.98 | +0.46 | +0.46 |
| AF | A absolute | normal | 299 | 226 | -0.57 | -1.12 | -0.09 | -1.24 | +0.46 | +0.46 |
| AF | A absolute | volatile | 24 | 18 | +0.64 | +1.25 | +0.70 | +9.28 | +0.61 | +0.61 |
| AF | R relative | quiet | 223 | 169 | +0.01 | +0.01 | +0.62 | +0.01 | +0.47 | +0.47 |
| AF | R relative | normal | 339 | 277 | -0.79 | -1.54 | -0.02 | -1.16 | +0.45 | +0.45 |
| AF | R relative | volatile | 436 | 344 | -0.58 | -1.14 | +0.05 | -0.96 | +0.46 | +0.47 |
| AF | ORACLE (realised) | quiet | 562 | 494 | -0.67 | -1.31 | +0.43 | -0.65 | +0.47 | +0.47 |
| AF | ORACLE (realised) | normal | 245 | 228 | -0.82 | -1.61 | -0.27 | -1.67 | +0.44 | +0.44 |
| AF | ORACLE (realised) | volatile | 75 | 68 | +0.13 | +0.25 | +0.33 | +0.78 | +0.50 | +0.50 |
| AB | none (control) | all | 998 | 790 | -0.61 | -1.20 | +0.18 | -1.05 | +0.28 | +0.28 |
| AB | A absolute | quiet | 675 | 546 | -0.70 | -1.38 | +0.11 | -1.17 | +0.27 | +0.28 |
| AB | A absolute | normal | 299 | 226 | -0.16 | -0.32 | +0.19 | -0.63 | +0.30 | +0.30 |
| AB | A absolute | volatile | 24 | 18 | -0.08 | -0.16 | -0.03 | -2.61 | +0.28 | +0.28 |
| AB | R relative | quiet | 223 | 169 | -0.56 | -1.09 | -0.11 | -1.67 | +0.25 | +0.27 |
| AB | R relative | normal | 339 | 277 | -0.36 | -0.70 | +0.18 | -0.91 | +0.28 | +0.29 |
| AB | R relative | volatile | 436 | 344 | -0.27 | -0.54 | +0.17 | -0.85 | +0.29 | +0.29 |
| AB | ORACLE (realised) | quiet | 562 | 494 | -3.62 | -7.10 | -2.59 | -4.49 | +0.24 | +0.25 |
| AB | ORACLE (realised) | normal | 245 | 228 | +0.76 | +1.50 | +1.15 | +2.70 | +0.35 | +0.35 |
| AB | ORACLE (realised) | volatile | 75 | 68 | +0.90 | +1.76 | +0.99 | +11.41 | +0.31 | +0.31 |
| EF | none (control) | all | 998 | 252 | -1.04 | -2.04 | -0.51 | -2.17 | +0.45 | +0.45 |
| EF | A absolute | quiet | 675 | 185 | -0.36 | -0.70 | +0.17 | -0.79 | +0.48 | +0.48 |
| EF | A absolute | normal | 299 | 62 | -1.27 | -2.49 | -1.07 | -6.47 | +0.35 | +0.35 |
| EF | A absolute | volatile | 24 | 5 | +0.00 | +0.00 | +0.04 | +0.30 | +0.60 | +0.60 |
| EF | R relative | quiet | 223 | 52 | -0.09 | -0.18 | +0.19 | -0.46 | +0.50 | +0.50 |
| EF | R relative | normal | 339 | 96 | -0.37 | -0.74 | -0.03 | -1.31 | +0.48 | +0.48 |
| EF | R relative | volatile | 436 | 104 | -1.11 | -2.17 | -0.81 | -3.81 | +0.39 | +0.39 |
| EF | ORACLE (realised) | quiet | 562 | 135 | +1.21 | +2.38 | +1.64 | +2.76 | +0.59 | +0.59 |
| EF | ORACLE (realised) | normal | 245 | 83 | -1.43 | -2.80 | -1.16 | -5.54 | +0.34 | +0.34 |
| EF | ORACLE (realised) | volatile | 75 | 34 | -1.97 | -3.86 | -1.87 | -13.48 | +0.15 | +0.15 |

What the tables say:
* Relative class (R): the ordering is as hypothesised but weak. Breakout: quiet -0.89, normal -0.63, volatile -0.25
  (gross -0.50 / -0.22 / +0.12). Asian fade: quiet -0.39, volatile -0.74 (gross +0.16 / -0.22). Extension fade: quiet
  -0.29, volatile -0.59. The spread between the right and the wrong class is about 0.3-0.6 Sharpe; costs take 0.3-0.9.
* Absolute class (A): the hypothesis is REVERSED. Fades do best on the (rare, mostly 2010-2011) predicted-volatile days
  (AF +0.35, t 1.4, hit 54 %; 2016-26 0.00) and worst on quiet days (AF -1.22, hit 44 %): a small Asian range gives a
  5-10 pip target against 1.2 pips of cost and, before costs, it is broken slightly more often than it holds (gross
  -0.23). Breakouts lose most per trade on absolute-volatile days (-5.7 pips).
* Hit rates: the fades win 44-49 % of trades with a 1:1 payoff (they need > 50 % plus costs); the breakout wins 25-28 %
  with a payoff that is not large enough. Conditioning moves hit rates by 1-5 points.
* Oracle: with the realised tercile known in advance the breakout earns +0.78 (t 3.2) on truly volatile days and loses
  -3.7 on truly quiet days; the extension fade earns +1.08 on truly quiet days and loses -1.6 on volatile days; the Asian
  fade is still negative net (-0.47, gross +0.44). So the hypothesis is true ex post, but the edge even with a perfect
  class is moderate, and the realistic forecast (tercile accuracy 62 %, about 10 points over always-majority) recovers
  none of it after costs.

## Final variant by the rule: `AB_R` (cost 1.2)
| period | decisions | trades | net SR | t | mean bp/decision | sum_bp | gross SR | hit net | hit gross | avg_net_pips | sum_net_pips |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2010 | 260 | 71 | -0.28 | -0.28 | -0.37 | -96.40 | -0.08 | +0.32 | +0.32 | -1.85 | -131.70 |
| 2011 | 260 | 58 | -0.96 | -0.96 | -1.04 | -270.02 | -0.77 | +0.24 | +0.24 | -6.73 | -390.20 |
| 2012 | 260 | 58 | +0.59 | +0.59 | +0.55 | +143.70 | +0.84 | +0.31 | +0.31 | +3.19 | +185.30 |
| 2013 | 259 | 54 | +1.04 | +1.04 | +0.85 | +219.79 | +1.29 | +0.39 | +0.39 | +5.48 | +296.05 |
| 2014 | 258 | 63 | +0.33 | +0.33 | +0.26 | +66.94 | +0.65 | +0.27 | +0.27 | +1.28 | +80.50 |
| 2015 | 259 | 41 | -0.23 | -0.23 | -0.25 | -65.56 | -0.06 | +0.32 | +0.32 | -1.94 | -79.35 |
| 2016 | 259 | 91 | -2.90 | -2.89 | -2.28 | -590.61 | -2.38 | +0.20 | +0.22 | -7.21 | -656.30 |
| 2017 | 259 | 93 | +0.33 | +0.33 | +0.30 | +77.03 | +0.82 | +0.29 | +0.29 | +0.90 | +83.65 |
| 2018 | 260 | 104 | -1.53 | -1.54 | -1.22 | -317.27 | -0.97 | +0.26 | +0.26 | -3.57 | -371.05 |
| 2019 | 259 | 116 | -1.48 | -1.48 | -1.06 | -273.57 | -0.73 | +0.22 | +0.22 | -2.64 | -306.80 |
| 2020 | 259 | 91 | +0.82 | +0.82 | +1.11 | +287.01 | +1.13 | +0.30 | +0.31 | +3.56 | +324.40 |
| 2021 | 259 | 129 | +0.34 | +0.34 | +0.29 | +75.07 | +1.00 | +0.31 | +0.32 | +0.75 | +96.25 |
| 2022 | 260 | 87 | -0.29 | -0.29 | -0.35 | -91.83 | +0.06 | +0.29 | +0.29 | -0.87 | -75.80 |
| 2023 | 258 | 30 | +0.78 | +0.78 | +0.54 | +138.53 | +0.99 | +0.30 | +0.30 | +5.08 | +152.45 |
| 2024 | 260 | 85 | -1.07 | -1.07 | -0.73 | -188.92 | -0.47 | +0.22 | +0.22 | -2.39 | -202.80 |
| 2025 | 259 | 109 | -0.45 | -0.45 | -0.60 | -154.27 | -0.08 | +0.27 | +0.27 | -1.68 | -183.45 |
| 2026 | 221 | 120 | -0.26 | -0.24 | -0.21 | -46.53 | +0.50 | +0.35 | +0.35 | -0.49 | -58.45 |
| 2010-2026 | 4369 | 1400 | -0.25 | -1.04 | -0.25 | -1086.93 | +0.12 | +0.28 | +0.28 | -0.88 | -1237.30 |
| 2016-2026 | 2813 | 1055 | -0.40 | -1.33 | -0.39 | -1085.37 | +0.06 | +0.27 | +0.28 | -1.14 | -1197.90 |
| 2023-2026 | 998 | 344 | -0.27 | -0.54 | -0.25 | -251.19 | +0.17 | +0.29 | +0.29 | -0.85 | -292.25 |
| 2010-2015 | 1556 | 345 | -0.00 | -0.00 | -0.00 | -1.56 | +0.22 | +0.31 | +0.31 | -0.11 | -39.40 |
| 2016-2022 | 1815 | 711 | -0.47 | -1.25 | -0.46 | -834.18 | +0.01 | +0.27 | +0.27 | -1.27 | -905.65 |

### Hit rates and cost sensitivity of the final variant
| period | cost_pips | decisions | trades | net SR | t | gross SR | hit net (P&L > 0 after cost) | hit gross (right sign before cost) | avg net pips |
|---|---|---|---|---|---|---|---|---|---|
| 2010-2026 | 0.600 | 4369 | 1390 | +0.04 | +0.18 | +0.23 | +0.29 | +0.29 | +0.16 |
| 2010-2026 | 1.200 | 4369 | 1400 | -0.25 | -1.04 | +0.12 | +0.28 | +0.28 | -0.88 |
| 2010-2026 | 2.400 | 4369 | 1409 | -0.82 | -3.38 | -0.05 | +0.25 | +0.26 | -2.79 |
| 2016-2026 | 0.600 | 2813 | 1047 | -0.09 | -0.28 | +0.14 | +0.29 | +0.29 | -0.24 |
| 2016-2026 | 1.200 | 2813 | 1055 | -0.40 | -1.33 | +0.06 | +0.27 | +0.28 | -1.14 |
| 2016-2026 | 2.400 | 2813 | 1063 | -1.24 | -4.08 | -0.26 | +0.24 | +0.24 | -3.39 |
| 2023-2026 | 0.600 | 998 | 342 | -0.01 | -0.01 | +0.21 | +0.30 | +0.30 | -0.06 |
| 2023-2026 | 1.200 | 998 | 344 | -0.27 | -0.54 | +0.17 | +0.29 | +0.29 | -0.85 |
| 2023-2026 | 2.400 | 998 | 348 | -0.98 | -1.91 | -0.04 | +0.26 | +0.26 | -2.83 |

Success bar (standalone 2016-2026 net Sharpe > 0.3, 2023-2026 not negative, three-way combination better than two-way
on 2016-2026): **FAILED on all three.** Deflated-Sharpe p (12 trials) = 1.00.

## Incremental test
| combo | period | sharpe | t | mean_bp | sum_bp |
|---|---|---|---|---|---|
| EW[weak_signals,regime_trend] | 2010-2026 | +0.56 | +2.35 | +0.58 | +2547.29 |
| EW[weak_signals,regime_trend] | 2016-2026 | +0.64 | +2.13 | +0.74 | +2078.30 |
| EW[weak_signals,regime_trend] | 2023-2026 | +0.36 | +0.71 | +0.42 | +420.28 |
| EW[weak_signals,regime_trend] | 2013-2026 | +0.62 | +2.35 | +0.71 | +2547.29 |
| EW[weak_signals,regime_trend,vol_tactics] | 2010-2026 | +0.57 | +2.36 | +0.57 | +2513.11 |
| EW[weak_signals,regime_trend,vol_tactics] | 2016-2026 | +0.64 | +2.13 | +0.74 | +2078.30 |
| EW[weak_signals,regime_trend,vol_tactics] | 2023-2026 | +0.36 | +0.71 | +0.42 | +420.28 |
| EW[weak_signals,regime_trend,vol_tactics] | 2013-2026 | +0.63 | +2.36 | +0.70 | +2513.11 |

Daily P&L correlation of the final stream with the two live arms:
| arm | corr_daily_all | corr_on_my_trade_days | corr_2016_2026 | n |
|---|---|---|---|---|
| weak_signals | -0.013 | -0.024 | -0.029 | 4373 |
| regime_trend | -0.019 | -0.034 | -0.032 | 4373 |

`combine(..., "EW")` gives an arm weight only when its trailing walk-forward t-stat is positive; vol_tactics weight by
year: 2013: 0.00, 2014: 0.00, 2015: 0.33, 2016: 0.00, 2017: 0.00, 2018: 0.00, 2019: 0.00, 2020: 0.00, 2021: 0.00, 2022: 0.00, 2023: 0.00, 2024: 0.00, 2025: 0.00, 2026: 0.00. It gets zero weight in every year from 2016, so the three-way combination is identical to the two-way one on
2016-2026 and 2023-2026 (0.636 / 0.356), and marginally different on 2010-2026 (0.567 vs 0.563, one year at weight 1/3).
The stream is uncorrelated with the others (-0.01 / -0.02) but has a negative mean: **no incremental value.**

## Leak checks
(1) Shuffled labels: the forecast's training targets are permuted (5 seeds), the classes rebuilt and the final variant
re-run. (2) Features shifted one session forward (stale) and one session back (deliberate look-ahead: the "lag-1" range
is then the target day itself), plus the oracle class and the mirrored class. (3) Coefficients.

Forecast accuracy under the checks (2010-2026):
| model | n | R2 log | R2 pips | acc median | acc tercile | acc vs 20d mean |
|---|---|---|---|---|---|---|
| real l07_lon | 4249 | 0.486 | 0.445 | 0.776 | 0.616 | 0.646 |
| real close_day | 4248 | 0.471 | 0.416 | 0.777 | 0.609 | 0.632 |
| shuffled targets seed 0 l07_lon | 4249 | -0.115 | -0.123 | 0.519 | 0.297 | 0.481 |
| shuffled targets seed 1 l07_lon | 4249 | -0.124 | -0.132 | 0.498 | 0.297 | 0.489 |
| shuffled targets seed 2 l07_lon | 4249 | -0.147 | -0.155 | 0.463 | 0.297 | 0.485 |
| shuffled targets seed 3 l07_lon | 4249 | -0.134 | -0.142 | 0.478 | 0.297 | 0.489 |
| shuffled targets seed 4 l07_lon | 4249 | -0.147 | -0.159 | 0.426 | 0.297 | 0.479 |
| features +1 session (stale) l07_lon | 4249 | 0.430 | 0.387 | 0.758 | 0.602 | 0.607 |
| features +1 session (stale) close_day | 4248 | 0.435 | 0.383 | 0.768 | 0.599 | 0.584 |
| features -1 session (future) l07_lon | 4249 | 1.000 | 1.000 | 1.000 | 0.999 | 1.000 |
| features -1 session (future) close_day | 4248 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |

Final variant's P&L under the checks (cost 1.2):
| check | trades | net SR 2010-2026 | t 2010-2026 | gross SR 2010-2026 | net SR 2016-2026 | net SR 2023-2026 | avg net pips | expectation |
|---|---|---|---|---|---|---|---|---|
| real | 1400 | -0.25 | -1.04 | +0.12 | -0.40 | -0.27 | -0.88 | the reported record |
| shuffled targets seed 0 | 2367 | -0.58 | -2.36 | +0.09 | -0.58 | -0.12 | -1.19 | no forecast skill; conditioning = arbitrary subset |
| shuffled targets seed 1 | 2320 | -0.48 | -1.99 | +0.18 | -0.68 | -0.23 | -0.98 | no forecast skill; conditioning = arbitrary subset |
| shuffled targets seed 2 | 2344 | -0.46 | -1.88 | +0.21 | -0.55 | -0.07 | -0.94 | no forecast skill; conditioning = arbitrary subset |
| shuffled targets seed 3 | 2331 | -0.54 | -2.21 | +0.13 | -0.62 | -0.35 | -1.09 | no forecast skill; conditioning = arbitrary subset |
| shuffled targets seed 4 | 2346 | -0.54 | -2.23 | +0.13 | -0.61 | -0.22 | -1.09 | no forecast skill; conditioning = arbitrary subset |
| features +1 session (stale) | 1511 | -0.09 | -0.35 | +0.33 | -0.26 | -0.10 | -0.23 | forecast degrades; class less informative |
| features -1 session (future) | 1307 | +1.33 | +5.46 | +1.60 | +1.44 | +1.54 | +6.48 | forecast accuracy jumps (lag-1 features = the target day) |
| oracle class (realised London tercile) | 741 | +0.78 | +3.19 | +0.94 | +0.79 | +0.90 | +6.17 | P&L jumps: the harness is sensitive to class look-ahead |
| mirrored class (quiet <-> volatile) | 1217 | -0.89 | -3.67 | -0.50 | -0.52 | -0.56 | -3.07 | should not beat the real class if conditioning carries information |

* Shuffled targets: forecast R2 < 0, tercile accuracy 0.30 (the forecast collapses to the training mean); the conditioned
  tactic becomes an arbitrary subset of the unconditioned breakout (gross about +0.1-0.2, net about -0.5).
* Stale features: accuracy falls only a little (R2 log 0.49 -> 0.43) because volatility is persistent and the monthly
  HAR term carries most of the level; the P&L is as indistinguishable from zero-edge as the real one. This is a
  statement about how little the same-day information adds, not a leak.
* Look-ahead features: R2 jumps to 1.00 and the tactic to net SR +1.33; oracle class +0.78. The harness would show a
  leak; the real run has none of that signature. Mirrored class: -0.89 (worse than the real class, as it should be).
* Timing asserted in code: the Asian range uses bars that start before 07:00 London; every entry is at or after 07:00
  and before 12:00 London, every exit before 16:00 London of the same session. The only forward-looking element is the
  data-quality filter (days whose London window has missing bars are skipped), which is unrelated to price.

Standardised coefficients of the log-range regressions (mean over the 17 yearly fits and the last fit):
| feature (standardised) | l07_lon_mean_beta | l07_lon_beta_2026 | close_day_mean_beta | close_day_beta_2026 |
|---|---|---|---|---|
| lr_m | +0.149 | +0.151 | +0.312 | +0.339 |
| lv_m | -0.140 | -0.171 | -0.142 | -0.178 |
| ll_m | +0.101 | +0.144 | -0.010 | +0.014 |
| lav | +0.086 | +0.097 | - | - |
| dow_4 | +0.082 | +0.077 | +0.051 | +0.045 |
| lv_w | +0.080 | +0.093 | +0.131 | +0.136 |
| dow_3 | +0.077 | +0.077 | +0.046 | +0.047 |
| dow_1 | +0.070 | +0.072 | +0.043 | +0.044 |
| dow_2 | +0.063 | +0.062 | +0.045 | +0.044 |
| ev_nfp | +0.057 | +0.061 | +0.037 | +0.040 |
| ev_ecb | +0.051 | +0.063 | +0.041 | +0.051 |
| lr_w | +0.043 | +0.002 | +0.027 | +0.018 |
| lr_d | -0.029 | -0.017 | -0.025 | -0.013 |
| ev_fomc | -0.021 | -0.023 | +0.031 | +0.041 |
| lvix | +0.018 | +0.012 | +0.030 | +0.019 |
| lv_d | +0.017 | +0.035 | +0.055 | +0.077 |
| ev_cpi | +0.013 | +0.027 | +0.014 | +0.024 |
| la | +0.013 | +0.017 | - | - |
| lgap | +0.011 | +0.014 | - | - |
| ll_w | -0.010 | +0.007 | -0.024 | -0.018 |
| ev_fomc_prev | +0.003 | +0.000 | +0.010 | +0.013 |
| ll_d | +0.002 | -0.010 | -0.022 | -0.029 |

None is a label in disguise: every lag is from sessions that closed before the session start, `la` / `lav` / `lgap` end at
07:00 London while the London target starts at 07:00 London (disjoint windows; for the whole-session target at 07:00 the
Asian range is a known part of the target, which is why that R2 is higher and why the classes for trading use the London
target). The level is carried by the monthly range term (`lr_m`, `ll_m`), with the realised-vol lags of opposite sign
(collinear with the range lags); NFP, ECB and the weekday dummies each carry 0.04-0.08 (log range per feature
standard deviation); the Asian realised vol (`lav`) is the main same-day variable.

## What was learned
* Range is predictable (R2 0.4-0.5, tercile accuracy 61-64 %) but most of that is the slow volatility level, which a
  20-day mean already has. The day-specific part (events, weekday, Asian session) is a 5-10 point classification edge.
* That edge moves tactic P&L in the expected direction only when the class is relative to the recent norm, and by less
  than the cost of one round trip. In absolute terms quiet days are simply the days on which a fixed 1.2-pip cost is
  largest relative to the available move.
* The tactics are not profitable even gross (unconditioned gross Sharpe +0.08 / -0.30 / -0.27), so there is no hidden
  edge for a filter to isolate; and the oracle shows the ceiling of range-conditioning for these tactics is a Sharpe of
  about 0.8-1.1 with perfect information.
* Use for the forecast: sizing, stop distances and cone calibration (lead's scoreboard), not tactic selection.

## Caveats
* 2023: 114 of 258 sessions (Feb-Jul) are not traded and not scored because whole hours are missing at the source;
  2023-2026 therefore has 998 decisions and 344 trades for the final variant.
* M15 bars with M1 arbitration were used; M5 bars were not run (the M1 arbitration already resolves intrabar order).
* Variants: 12 (3 controls + 9 conditioned), all reported above. The by-class table additionally shows the cells that
  are not variants (normal class, wrong-way cells, class C per tactic in the CSV, oracle); none was eligible.
  Leak-check re-runs and the two cost re-pricings are not counted.

## Run
`OMP_NUM_THREADS=1 PYTHONPATH=src python -m eurusd.arms.vol_tactics` (about 45 s; log in
`experiments/results/arms/logs/vol_tactics.log`). Entry point `run(cost_pips=1.2) -> (positions, report)`.
Files: `src/eurusd/arms/vol_tactics.py`; `experiments/results/arms/vol_tactics_positions.parquet` (final variant, OOS;
`pos`, `fwd_bp`, `gross_bp`, `net_bp`, `pips`, `session`); `vol_tactics_report.csv` (12 variants x 3 cost levels, `variant`,
`final`, `eligible`, `cost_pips`, hit rates); `vol_tactics_all_variants.parquet`; `vol_tactics_by_class.csv`;
`vol_tactics_forecast_accuracy.csv`; `vol_tactics_leakchecks.csv`, `vol_tactics_leakchecks_forecast.csv`;
`vol_tactics_coefficients.csv`; `vol_tactics_incremental.csv`, `vol_tactics_pnl_corr.csv`;
`data/processed/vol_tactics_range_forecast.parquet`; `data/processed/vol_tactics_days.parquet` (cache).
