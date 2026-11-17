# Arm EA: `levels_confirm` - are round 11's two leads on the levels confirmed on markets never scored here?

Round 13. Code `src/eurusd/arms/levels_confirm.py` (`run()`, one process). Results `experiments/results/arms/levels_confirm_*.csv`. The two candidates, the market list, the data-quality rule, the scoring and the pass bar were written into the module docstring before any bar of the new markets was downloaded. **Candidates: 2**, against the bots' median level. Nothing was re-run with changed settings.

## Verdict (read this first)

**K1, regression levels from daily returns (round 11's C3): NOT CONFIRMED** on 6 new markets pooled, 2010-26.

* (1) better proper score at all three horizons, interval excluding zero at two at least: **FAILS** (h=5: -1.00 % [-2.49, +0.28]; h=21: -1.81 % [-4.25, +0.55]; h=63: -3.89 % [-7.58, -0.05]; 1 of 3 intervals exclude zero).
* (2) holding rate more even across volatility terciles in at least 5 of 6 markets: **passes** (6 of 6).
* (3) every pooled level holds 77-83 %: **passes** (6 of 6 cells inside; lower / upper held: h=5: 81.6 / 79.3; h=21: 81.3 / 79.2; h=63: 82.9 / 79.2).
* 2018-26 alone (descriptive): (1) FAILS (h=5: -0.58 % [-1.52, +0.42]; h=21: -0.87 % [-2.71, +0.87]; h=63: -3.07 % [-6.63, +0.26]); (2) 6 of 6; (3) 5 of 6 cells (h=5: 82.3 / 79.7; h=21: 82.1 / 80.7; h=63: 83.9 / 81.9).

**K2, hourly-volatility regression with the event adjustment (round 11's C6): CONFIRMED** on 6 new markets pooled, 2010-26.

* (1) better proper score at all three horizons, interval excluding zero at two at least: **passes** (h=5: -2.12 % [-3.53, -0.91]; h=21: -2.40 % [-4.85, -0.07]; h=63: -3.80 % [-7.27, -0.11]; 3 of 3 intervals exclude zero).
* (2) holding rate more even across volatility terciles in at least 5 of 6 markets: **passes** (6 of 6).
* (3) every pooled level holds 77-83 %: **passes** (6 of 6 cells inside; lower / upper held: h=5: 81.9 / 79.5; h=21: 81.4 / 79.4; h=63: 82.1 / 78.0).
* (4) event-week shortfall of the one-week holding rate at least halved: **passes** (baseline +2.5 points, K2 +0.4; K1 for comparison +2.0; positive = levels hold less often in event weeks).
* 2018-26 alone (descriptive): (1) passes (h=5: -1.57 % [-2.32, -0.84]; h=21: -1.04 % [-2.70, +0.62]; h=63: -3.85 % [-7.89, -0.03]); (2) 6 of 6; (3) 5 of 6 cells (h=5: 82.8 / 79.8; h=21: 82.3 / 80.9; h=63: 83.4 / 80.7); (4) baseline +2.3, K2 -0.3 points.

## Should the product's levels change?

**Yes, for K2 only:** by the bar declared in advance, the hourly-volatility regression with the event adjustment (`har_rv_ev`) is confirmed on six markets never scored here, so the lead may replace the bots' width arithmetic with it, while the daily-returns version K1 is not confirmed and should not be wired in. Expect a small gain, not a different product (proper score 2-4 % better, levels 3-5 % narrower on these markets at the same 80 % reliability, holding rates about half as dependent on calm / volatile markets, the event-week weakness of one-week levels removed), and note that the statistical margin at 21 and 63 sessions is thin (below), so the bots' levels should keep running beside it in the paper forward test.

Function to wire into `bots.py` (by the lead, not by this arm): K2: `sharper_levels.levels(X, h, asof, name="har_rv_ev")` on `sharper_levels.build(D, h1)`.

## 1. The plain table (2010-26, walk-forward, out of sample, same sessions for the three methods)

`held` = share of sessions on which the period's lowest low stayed above the lower level / highest high below the upper level (design: 80 %). Score = pinball loss at the 20 % / 80 % quantiles, basis points, lower is better; in brackets the relative difference to the baseline, `*` = this market's own paired block-bootstrap 95 % interval excludes zero. Tercile spread = max minus min of the holding rate across the three volatility terciles, points, average of the lower and the upper level at that horizon.

**2010-26** (the declared primary era)

| market     |   h | baseline: lower / upper held %   |   baseline: score bp | baseline: tercile spread   | K1: lower / upper held %   | K1: score bp   | K1: tercile spread   | K2: lower / upper held %   | K2: score bp   | K2: tercile spread   |
|:-----------|----:|:---------------------------------|---------------------:|:---------------------------|:---------------------------|:---------------|:---------------------|:---------------------------|:---------------|:---------------------|
| EUR/GBP    |   5 | 79.4 / 81.0                      |                 20   | 7.3                        | 81.8 / 80.0                | 19.8 (-0.8 %)  | 2.5                  | 82.1 / 80.0                | 19.6 (-1.9 %*) | 2.4                  |
| EUR/GBP    |  21 | 80.1 / 82.5                      |                 39.2 | 7.0                        | 81.8 / 81.5                | 38.6 (-1.4 %)  | 3.3                  | 82.4 / 81.6                | 38.5 (-1.7 %)  | 4.2                  |
| EUR/GBP    |  63 | 77.9 / 84.1                      |                 69.8 | 9.2                        | 84.7 / 81.0                | 66.3 (-5.1 %*) | 6.9                  | 85.4 / 81.1                | 67.6 (-3.2 %)  | 5.6                  |
| EUR/JPY    |   5 | 80.9 / 79.5                      |                 29   | 7.4                        | 79.0 / 81.7                | 28.7 (-1.3 %*) | 1.9                  | 78.9 / 81.6                | 28.4 (-2.2 %*) | 2.1                  |
| EUR/JPY    |  21 | 81.1 / 78.9                      |                 61.3 | 8.3                        | 78.3 / 81.4                | 59.5 (-2.9 %*) | 2.9                  | 78.4 / 81.5                | 59.3 (-3.2 %*) | 2.1                  |
| EUR/JPY    |  63 | 81.3 / 76.0                      |                102.6 | 12.6                       | 79.8 / 78.7                | 96.2 (-6.3 %*) | 7.9                  | 76.5 / 76.4                | 98.2 (-4.2 %)  | 7.7                  |
| EUR/CHF    |   5 | 80.6 / 79.9                      |                 18.2 | 7.1                        | 79.9 / 79.0                | 17.6 (-2.8 %)  | 5.6                  | 80.4 / 80.2                | 17.5 (-3.6 %)  | 6.9                  |
| EUR/CHF    |  21 | 80.1 / 79.7                      |                 40   | 12.9                       | 78.0 / 79.8                | 38.5 (-3.8 %)  | 10.1                 | 78.2 / 81.4                | 38.2 (-4.4 %)  | 10.2                 |
| EUR/CHF    |  63 | 80.0 / 80.1                      |                 77.4 | 15.3                       | 75.8 / 82.1                | 73.3 (-5.2 %)  | 11.4                 | 75.4 / 82.8                | 73.0 (-5.6 %)  | 12.0                 |
| USD/SEK    |   5 | 80.2 / 79.1                      |                 28.2 | 9.4                        | 82.5 / 78.1                | 28.1 (-0.6 %)  | 5.4                  | 83.4 / 78.9                | 27.7 (-1.7 %*) | 4.7                  |
| USD/SEK    |  21 | 78.2 / 77.9                      |                 56.1 | 13.8                       | 81.5 / 75.6                | 55.5 (-1.1 %)  | 5.4                  | 82.9 / 75.6                | 55.1 (-1.9 %)  | 4.9                  |
| USD/SEK    |  63 | 78.8 / 77.2                      |                102.9 | 19.2                       | 85.7 / 76.9                | 100.8 (-2.1 %) | 8.2                  | 86.1 / 75.9                | 99.8 (-3.0 %)  | 10.1                 |
| USD/NOK    |   5 | 79.7 / 79.4                      |                 31.7 | 10.0                       | 83.4 / 77.5                | 31.5 (-0.7 %)  | 1.8                  | 84.1 / 77.9                | 31.1 (-1.8 %*) | 2.1                  |
| USD/NOK    |  21 | 78.3 / 79.4                      |                 65.7 | 9.4                        | 84.6 / 76.7                | 64.8 (-1.5 %)  | 4.6                  | 84.3 / 76.4                | 64.0 (-2.6 %)  | 3.5                  |
| USD/NOK    |  63 | 78.0 / 78.3                      |                117.6 | 12.5                       | 86.2 / 77.2                | 116.1 (-1.3 %) | 7.6                  | 86.3 / 75.7                | 112.1 (-4.6 %) | 4.0                  |
| EUR/AUD    |   5 | 80.9 / 79.4                      |                 25.9 | 7.3                        | 83.2 / 79.0                | 25.6 (-0.9 %)  | 2.6                  | 82.8 / 78.1                | 25.3 (-2.1 %*) | 2.4                  |
| EUR/AUD    |  21 | 80.2 / 79.6                      |                 54.3 | 7.1                        | 83.8 / 79.2                | 53.5 (-1.4 %)  | 6.3                  | 82.8 / 79.2                | 53.4 (-1.6 %)  | 6.7                  |
| EUR/AUD    |  63 | 81.8 / 79.6                      |                 97   | 14.5                       | 85.9 / 79.1                | 92.8 (-4.3 %*) | 5.7                  | 83.9 / 75.7                | 93.0 (-4.1 %)  | 5.0                  |
| ALL POOLED |   5 | 80.3 / 79.7                      |                 25.3 | 8.1 (mean)                 | 81.6 / 79.3                | 25.0 (-1.0 %)  | 3.3 (mean)           | 81.9 / 79.5                | 24.8 (-2.1 %*) | 3.4 (mean)           |
| ALL POOLED |  21 | 79.8 / 79.7                      |                 52.4 | 9.8 (mean)                 | 81.3 / 79.2                | 51.4 (-1.8 %)  | 5.4 (mean)           | 81.4 / 79.4                | 51.1 (-2.4 %*) | 5.3 (mean)           |
| ALL POOLED |  63 | 79.7 / 79.3                      |                 93.9 | 13.9 (mean)                | 82.9 / 79.2                | 90.2 (-3.9 %*) | 7.9 (mean)           | 82.1 / 78.0                | 90.0 (-3.8 %*) | 7.4 (mean)           |

**2018-26** (descriptive)

| market     |   h | baseline: lower / upper held %   |   baseline: score bp | baseline: tercile spread   | K1: lower / upper held %   | K1: score bp   | K1: tercile spread   | K2: lower / upper held %   | K2: score bp   | K2: tercile spread   |
|:-----------|----:|:---------------------------------|---------------------:|:---------------------------|:---------------------------|:---------------|:---------------------|:---------------------------|:---------------|:---------------------|
| EUR/GBP    |   5 | 79.6 / 81.3                      |                 16.8 | 7.5                        | 84.2 / 82.4                | 16.8 (-0.2 %)  | 2.2                  | 84.8 / 81.9                | 16.5 (-1.7 %*) | 3.2                  |
| EUR/GBP    |  21 | 82.9 / 82.8                      |                 32.5 | 9.9                        | 86.0 / 84.0                | 32.6 (+0.3 %)  | 3.0                  | 86.7 / 84.3                | 32.6 (+0.2 %)  | 3.8                  |
| EUR/GBP    |  63 | 80.3 / 83.1                      |                 56.3 | 14.7                       | 88.3 / 82.9                | 56.5 (+0.3 %)  | 10.0                 | 88.4 / 82.7                | 57.3 (+1.8 %)  | 8.9                  |
| EUR/JPY    |   5 | 81.2 / 80.2                      |                 23.8 | 7.7                        | 80.3 / 82.3                | 23.8 (-0.2 %)  | 4.0                  | 79.9 / 82.7                | 23.6 (-0.7 %)  | 3.7                  |
| EUR/JPY    |  21 | 81.6 / 79.7                      |                 47.7 | 9.5                        | 79.6 / 83.0                | 46.9 (-1.6 %)  | 3.9                  | 79.4 / 82.8                | 47.2 (-1.1 %)  | 3.5                  |
| EUR/JPY    |  63 | 81.2 / 77.1                      |                 73.2 | 20.3                       | 83.3 / 82.3                | 67.3 (-8.1 %*) | 12.9                 | 80.8 / 79.0                | 67.5 (-7.7 %*) | 11.5                 |
| EUR/CHF    |   5 | 77.9 / 79.5                      |                 14.2 | 9.5                        | 78.6 / 80.1                | 14.1 (-0.3 %)  | 4.0                  | 79.6 / 80.8                | 14.1 (-0.5 %)  | 3.2                  |
| EUR/CHF    |  21 | 75.3 / 81.2                      |                 28.5 | 12.9                       | 75.3 / 82.4                | 28.3 (-0.7 %)  | 3.3                  | 75.3 / 83.8                | 28.5 (-0.1 %)  | 6.0                  |
| EUR/CHF    |  63 | 78.3 / 82.2                      |                 46.6 | 21.3                       | 75.0 / 87.3                | 43.8 (-6.0 %)  | 6.8                  | 73.5 / 88.2                | 43.8 (-5.9 %)  | 7.1                  |
| USD/SEK    |   5 | 80.1 / 78.4                      |                 29.2 | 10.4                       | 82.0 / 76.4                | 28.8 (-1.1 %)  | 5.1                  | 82.8 / 77.1                | 28.5 (-2.1 %*) | 3.9                  |
| USD/SEK    |  21 | 79.9 / 78.4                      |                 59   | 13.6                       | 81.1 / 74.7                | 58.0 (-1.8 %)  | 5.8                  | 81.7 / 74.0                | 57.7 (-2.3 %)  | 5.6                  |
| USD/SEK    |  63 | 79.7 / 80.9                      |                101.4 | 15.2                       | 84.3 / 77.2                | 99.2 (-2.2 %)  | 4.8                  | 85.2 / 77.1                | 98.2 (-3.1 %)  | 5.4                  |
| USD/NOK    |   5 | 80.6 / 79.3                      |                 32.5 | 10.5                       | 83.3 / 76.4                | 32.1 (-1.3 %)  | 5.0                  | 83.7 / 76.7                | 31.8 (-2.0 %)  | 3.6                  |
| USD/NOK    |  21 | 78.2 / 81.5                      |                 67.6 | 7.8                        | 82.7 / 77.4                | 66.4 (-1.8 %)  | 6.9                  | 82.9 / 76.8                | 66.2 (-2.0 %)  | 6.7                  |
| USD/NOK    |  63 | 76.5 / 83.1                      |                121.1 | 10.5                       | 83.5 / 78.5                | 120.2 (-0.7 %) | 13.2                 | 84.8 / 76.7                | 117.0 (-3.4 %) | 9.4                  |
| EUR/AUD    |   5 | 81.4 / 80.5                      |                 22.1 | 8.6                        | 85.6 / 80.6                | 22.1 (-0.3 %)  | 2.1                  | 85.8 / 79.5                | 21.6 (-2.3 %*) | 3.0                  |
| EUR/AUD    |  21 | 81.7 / 81.5                      |                 48.7 | 9.1                        | 88.3 / 83.0                | 48.9 (+0.3 %)  | 3.9                  | 87.8 / 83.6                | 48.3 (-0.9 %)  | 4.9                  |
| EUR/AUD    |  63 | 81.2 / 81.5                      |                 91.8 | 14.9                       | 88.8 / 83.3                | 90.2 (-1.7 %)  | 5.4                  | 87.6 / 80.3                | 87.3 (-4.8 %*) | 7.1                  |
| ALL POOLED |   5 | 80.1 / 79.9                      |                 23.1 | 9.1 (mean)                 | 82.3 / 79.7                | 22.9 (-0.6 %)  | 3.7 (mean)           | 82.8 / 79.8                | 22.7 (-1.6 %*) | 3.4 (mean)           |
| ALL POOLED |  21 | 79.9 / 80.8                      |                 47.3 | 10.5 (mean)                | 82.1 / 80.7                | 46.8 (-0.9 %)  | 4.5 (mean)           | 82.3 / 80.9                | 46.7 (-1.0 %)  | 5.1 (mean)           |
| ALL POOLED |  63 | 79.5 / 81.3                      |                 81.7 | 16.2 (mean)                | 83.9 / 81.9                | 79.5 (-3.1 %)  | 8.8 (mean)           | 83.4 / 80.7                | 78.5 (-3.9 %*) | 8.2 (mean)           |

Pooled row: holding rates and score over all scored sessions of all markets; the bracket is the declared pooled test (per-market relative loss difference, averaged by date, block bootstrap over dates). First scored session per market (5 sessions): EUR/GBP 2010-01-03, EUR/JPY 2010-01-03, EUR/CHF 2010-01-03, USD/SEK 2012-01-01, USD/NOK 2012-01-01, EUR/AUD 2010-01-03.

## 2. The pooled score test

`pooled_rel_diff_pct` = mean over dates of the market-average relative loss difference to the bots (negative = better), with the declared interval (`lo` / `hi`: date blocks, cross-market dependence kept). `indep_blocks_*` = the same with each market resampled independently (descriptive; narrower because it ignores that the markets move together).

| method   |   h | era     |   dates |   pooled_rel_diff_pct |   lo_pct |   hi_pct |   indep_blocks_mean_pct |   indep_blocks_lo_pct |   indep_blocks_hi_pct |
|:---------|----:|:--------|--------:|----------------------:|---------:|---------:|------------------------:|----------------------:|----------------------:|
| K1       |   5 | 2010-26 |    4374 |                 -1    |    -2.49 |     0.28 |                   -1.18 |                 -2.46 |                 -0.06 |
| K2       |   5 | 2010-26 |    4374 |                 -2.12 |    -3.53 |    -0.91 |                   -2.24 |                 -3.54 |                 -1.15 |
| K1       |  21 | 2010-26 |    4358 |                 -1.81 |    -4.25 |     0.55 |                   -2.01 |                 -4.31 |                  0.04 |
| K2       |  21 | 2010-26 |    4358 |                 -2.4  |    -4.85 |    -0.07 |                   -2.58 |                 -4.83 |                 -0.58 |
| K1       |  63 | 2010-26 |    4316 |                 -3.89 |    -7.58 |    -0.05 |                   -4.04 |                 -7.61 |                 -0.63 |
| K2       |  63 | 2010-26 |    4316 |                 -3.8  |    -7.27 |    -0.11 |                   -4.14 |                 -7.67 |                 -0.75 |
| K1       |   5 | 2018-26 |    2299 |                 -0.58 |    -1.52 |     0.42 |                   -0.58 |                 -1.18 |                  0.03 |
| K2       |   5 | 2018-26 |    2299 |                 -1.57 |    -2.32 |    -0.84 |                   -1.56 |                 -2.24 |                 -0.92 |
| K1       |  21 | 2018-26 |    2283 |                 -0.87 |    -2.71 |     0.87 |                   -0.87 |                 -2.14 |                  0.34 |
| K2       |  21 | 2018-26 |    2283 |                 -1.04 |    -2.7  |     0.62 |                   -1.04 |                 -2.28 |                  0.19 |
| K1       |  63 | 2018-26 |    2241 |                 -3.07 |    -6.63 |     0.26 |                   -3.06 |                 -5.66 |                 -0.54 |
| K2       |  63 | 2018-26 |    2241 |                 -3.85 |    -7.89 |    -0.03 |                   -3.85 |                 -6.44 |                 -1.31 |

## 3. Evenness: spread of the holding rate across volatility terciles (six-cell average per market)

| era     | market   |   baseline spread (points) |   K1 spread (points) |   K2 spread (points) |
|:--------|:---------|---------------------------:|---------------------:|---------------------:|
| 2010-26 | EUR/AUD  |                        9.7 |                  4.9 |                  4.7 |
| 2010-26 | EUR/CHF  |                       11.7 |                  9   |                  9.7 |
| 2010-26 | EUR/GBP  |                        7.8 |                  4.2 |                  4.1 |
| 2010-26 | EUR/JPY  |                        9.4 |                  4.2 |                  3.9 |
| 2010-26 | USD/NOK  |                       10.6 |                  4.7 |                  3.2 |
| 2010-26 | USD/SEK  |                       14.2 |                  6.3 |                  6.6 |
| 2018-26 | EUR/AUD  |                       10.9 |                  3.8 |                  5   |
| 2018-26 | EUR/CHF  |                       14.6 |                  4.7 |                  5.4 |
| 2018-26 | EUR/GBP  |                       10.7 |                  5.1 |                  5.3 |
| 2018-26 | EUR/JPY  |                       12.5 |                  6.9 |                  6.2 |
| 2018-26 | USD/NOK  |                        9.6 |                  8.3 |                  6.5 |
| 2018-26 | USD/SEK  |                       13.1 |                  5.2 |                  4.9 |

## 4. One-week levels in event weeks against other weeks (pooled)

Event week = a scheduled FOMC statement, ECB decision (euro crosses), US payrolls or US CPI inside the 5-session window, as `sharper_levels` codes it.

| method   | era     | class      |   sessions |   n_indep_summed |   lower_held |   upper_held |   score_bp |
|:---------|:--------|:-----------|-----------:|-----------------:|-------------:|-------------:|-----------:|
| baseline | 2010-26 | event week |      14386 |           2877.2 |         78.9 |         79   |      26.11 |
| baseline | 2010-26 | other week |      10803 |           2160.6 |         82.1 |         80.7 |      24.23 |
| K1       | 2010-26 | event week |      14386 |           2877.2 |         80.4 |         78.8 |      25.78 |
| K1       | 2010-26 | other week |      10803 |           2160.6 |         83.2 |         80   |      24.02 |
| K2       | 2010-26 | event week |      14386 |           2877.2 |         81.4 |         79.6 |      25.57 |
| K2       | 2010-26 | other week |      10803 |           2160.6 |         82.5 |         79.3 |      23.67 |
| baseline | 2018-26 | event week |       7646 |           1529.2 |         78.4 |         79.5 |      23.27 |
| baseline | 2018-26 | other week |       6137 |           1227.4 |         82.2 |         80.3 |      22.86 |
| K1       | 2018-26 | event week |       7646 |           1529.2 |         81.1 |         79.9 |      23.08 |
| K1       | 2018-26 | other week |       6137 |           1227.4 |         83.9 |         79.5 |      22.75 |
| K2       | 2018-26 | event week |       7646 |           1529.2 |         82.1 |         80.7 |      22.96 |
| K2       | 2018-26 | other week |       6137 |           1227.4 |         83.6 |         78.6 |      22.39 |

Per market, 2010-26:

| market   | candidate   |   lower held %, event week |   lower held %, other week |   upper held %, event week |   upper held %, other week |
|:---------|:------------|---------------------------:|---------------------------:|---------------------------:|---------------------------:|
| EUR/AUD  | baseline    |                       79.8 |                       82.4 |                       79   |                       80   |
| EUR/AUD  | K1          |                       82.5 |                       84.2 |                       78.9 |                       79.2 |
| EUR/AUD  | K2          |                       83.2 |                       82.3 |                       78.5 |                       77.4 |
| EUR/CHF  | baseline    |                       79.8 |                       81.7 |                       78.6 |                       81.7 |
| EUR/CHF  | K1          |                       79.3 |                       80.8 |                       78.1 |                       80.4 |
| EUR/CHF  | K2          |                       80.1 |                       80.9 |                       79.8 |                       80.8 |
| EUR/GBP  | baseline    |                       78.4 |                       80.8 |                       80   |                       82.5 |
| EUR/GBP  | K1          |                       81   |                       82.8 |                       79.3 |                       81.2 |
| EUR/GBP  | K2          |                       82.3 |                       81.7 |                       79.3 |                       81   |
| EUR/JPY  | baseline    |                       80   |                       82.2 |                       78.9 |                       80.3 |
| EUR/JPY  | K1          |                       78.1 |                       80.4 |                       81.1 |                       82.7 |
| EUR/JPY  | K2          |                       78.4 |                       79.6 |                       81.6 |                       81.7 |
| USD/NOK  | baseline    |                       76.2 |                       83.5 |                       78.6 |                       80.4 |
| USD/NOK  | K1          |                       80.6 |                       86.5 |                       76.8 |                       78.3 |
| USD/NOK  | K2          |                       82.5 |                       85.9 |                       78.2 |                       77.6 |
| USD/SEK  | baseline    |                       78.5 |                       82.1 |                       78.9 |                       79.3 |
| USD/SEK  | K1          |                       80.7 |                       84.4 |                       77.9 |                       78.4 |
| USD/SEK  | K2          |                       82.6 |                       84.3 |                       80.1 |                       77.6 |

## 5. Data: the markets and the declared quality rule

HistData 1-minute bid bars (stamps America/New_York -> UTC as arm P verified), aggregated to 5 minutes, hourly bars and 22:00-UTC sessions exactly as the EUR/USD store. The rule (module docstring) was applied before any level was computed.

| check                         | 0                      | 1                      | 2                      | 3                          | 4                          | 5                              | 6                      |
|:------------------------------|:-----------------------|:-----------------------|:-----------------------|:---------------------------|:---------------------------|:-------------------------------|:-----------------------|
| label                         | EUR/GBP                | EUR/JPY                | EUR/CHF                | USD/SEK                    | USD/NOK                    | Gold                           | EUR/AUD                |
| first                         | 2002-03-04             | 2002-03-04             | 2002-01-14             | 2008-08-31                 | 2008-08-31                 | 2009-03-15                     | 2002-08-19             |
| last                          | 2026-11-13             | 2026-11-13             | 2026-11-13             | 2026-11-13                 | 2026-11-13                 | 2026-11-13                     | 2026-11-13             |
| sessions                      | 6195                   | 6193                   | 6190                   | 4720                       | 4717                       | 4561                           | 6183                   |
| files                         | 35                     | 35                     | 35                     | 29                         | 29                         | 28                             | 35                     |
| files_failed                  | 0                      | 0                      | 0                      | 0                          | 0                          | 0                              | 0                      |
| min_sessions_in_a_year        | 258                    | 258                    | 254                    | 258                        | 258                        | 257                            | 255                    |
| min_sessions_year             | 2006                   | 2006                   | 2003                   | 2014                       | 2014                       | 2014                           | 2003                   |
| ref_source                    | ECB reference rate GBP | ECB reference rate JPY | ECB reference rate CHF | ECB reference rate SEK/USD | ECB reference rate NOK/USD | Yahoo gold futures daily range | ECB reference rate AUD |
| ref_days                      | 4317.0                 | 4316.0                 | 4317.0                 | 4317.0                     | 4315.0                     | nan                            | 4317.0                 |
| ref_inside_pct                | 100.0                  | 100.0                  | 100.0                  | 100.0                      | 100.0                      | nan                            | 99.977                 |
| yahoo_days                    | 3623.0                 | 3622.0                 | 3621.0                 | nan                        | nan                        | 3875.0                         | nan                    |
| yahoo_logrange_corr           | 0.702                  | 0.697                  | 0.841                  | nan                        | nan                        | 0.765                          | nan                    |
| yahoo_range_median_ratio      | 1.085                  | 1.093                  | 1.089                  | nan                        | nan                        | 1.052                          | nan                    |
| thin_sessions_in_2023_hole    | 113                    | 113                    | 113                    | 113                        | 114                        | 114                            | 114                    |
| thin_sessions_elsewhere_pct   | 0.274                  | 0.297                  | 0.297                  | 0.274                      | 0.274                      | 0.85                           | 0.274                  |
| bad_price_rows                | 0                      | 1                      | 0                      | 0                          | 0                          | 0                              | 0                      |
| inconsistent_ohlc_bars        | 0                      | 0                      | 0                      | 0                          | 0                          | 0                              | 0                      |
| wick_rule_bars                | 0                      | 3                      | 0                      | 1                          | 0                          | 0                              | 1                      |
| top20_with_bad_tick_signature | 1                      | 0                      | 0                      | 0                          | 0                          | 0                              | 0                      |
| Q1_complete                   | True                   | True                   | True                   | True                       | True                       | True                           | True                   |
| Q2_independent_source         | True                   | True                   | True                   | True                       | True                       | False                          | True                   |
| Q3_thin                       | True                   | True                   | True                   | True                       | True                       | True                           | True                   |
| Q4_top20                      | True                   | True                   | True                   | True                       | True                       | True                           | True                   |
| PASS                          | True                   | True                   | True                   | True                       | True                       | False                          | True                   |

**Gold was DROPPED by the declared rule and never scored**: its only independent check (session range against Yahoo gold futures, 2011-26) gave a correlation of 0.77 against the declared minimum of 0.85 (median ratio 1.05, inside the band). The same Yahoo comparison gives 0.70-0.84 on the three euro crosses whose ECB check is perfect, so the failure very probably says more about Yahoo's daily highs / lows than about the gold bars; the rule was fixed in advance and I did not re-draw it. The first declared reserve, EUR/AUD, took its place (ECB fix inside the session range on 99.98 % of days). Consequence: four of the six scored markets are euro crosses and none is a commodity. One blemish that the rule tolerates (one signature in the top 20; more than two fail a market): EUR/GBP has a bad print on 2004-08-31 (session range 60 %), which the 3 % wick rule did not catch because the bad price is the bar's own close / next open. A second EUR/GBP session of 2004 (03-25, range 11 % with an 11 % open-to-close move) also looks like bad data without carrying the signature. Both lie in the training years only (scoring starts 2010) and feed all three methods' fits; they were left as they are. The wick rule changed five 5-minute bars in all (EUR/JPY three in 2004, EUR/AUD one in 2004, USD/SEK 2020-11-12), all single prints 7-50 % away from the market. USD/SEK and USD/NOK begin in September 2008 on HistData, so their first scored session is 2012-01-01.

The 20 largest session ranges per market are in `levels_confirm_top_ranges.csv`, the bars changed by the wick rule in `levels_confirm_wick_rule_bars.csv`. The five largest per market:

| market   | session_start_utc   |   range_pct |   x_trailing_21_median |   abs_close_minus_open_pct |   hourly_bars |   widest_m5_bar_pct | widest_m5_bar_utc   | changed_by_wick_rule   | bad_tick_signature   |
|:---------|:--------------------|------------:|-----------------------:|---------------------------:|--------------:|--------------------:|:--------------------|:-----------------------|:---------------------|
| EUR/GBP  | 2004-08-31          |       60.48 |                  103.7 |                       0.58 |            24 |               59.83 | 21:00               | False                  | True                 |
| EUR/GBP  | 2004-03-25          |       11.38 |                   15.5 |                      11.24 |            24 |               10.81 | 21:20               | False                  | False                |
| EUR/GBP  | 2016-06-23          |        8.95 |                    9   |                       6.32 |            23 |                3.34 | 23:15               | False                  | False                |
| EUR/GBP  | 2022-09-25          |        4.71 |                    6.5 |                       0.6  |            24 |                2.22 | 01:00               | False                  | False                |
| EUR/GBP  | 2009-01-04          |        4.3  |                    2.8 |                       3.12 |            24 |                0.55 | 08:25               | False                  | False                |
| EUR/JPY  | 2008-10-23          |       11.02 |                    3.6 |                       6.52 |            23 |                2.12 | 09:30               | False                  | False                |
| EUR/JPY  | 2016-06-23          |       10.63 |                    9.6 |                       6.95 |            23 |                4.98 | 02:40               | False                  | False                |
| EUR/JPY  | 2008-10-27          |       10.5  |                    3.2 |                       9.36 |            24 |                0.93 | 05:55               | False                  | False                |
| EUR/JPY  | 2010-05-05          |        8.75 |                    6.9 |                       4.83 |            24 |                1.57 | 18:45               | False                  | False                |
| EUR/JPY  | 2008-11-12          |        6.9  |                    1.7 |                       4.89 |            24 |                1.44 | 19:35               | False                  | False                |
| EUR/CHF  | 2004-03-25          |       44.45 |                  106.1 |                      44.02 |            24 |                0.15 | 07:35               | False                  | False                |
| EUR/CHF  | 2015-01-14          |       21.28 |                  275.1 |                      20.92 |            24 |                8.81 | 09:30               | False                  | False                |
| EUR/CHF  | 2011-09-05          |       10.09 |                    4   |                       8.43 |            24 |                5.23 | 08:00               | False                  | False                |
| EUR/CHF  | 2011-08-08          |        7.18 |                    4.2 |                       3.01 |            24 |                1.75 | 18:20               | False                  | False                |
| EUR/CHF  | 2011-08-10          |        6.28 |                    3.7 |                       5.46 |            24 |                1.22 | 13:10               | False                  | False                |
| USD/SEK  | 2016-06-23          |        7.66 |                    9.1 |                       4.34 |            23 |                1.18 | 02:30               | False                  | False                |
| USD/SEK  | 2020-03-17          |        5.45 |                    4.2 |                       3.57 |            24 |                0.69 | 19:05               | False                  | False                |
| USD/SEK  | 2008-11-23          |        5.3  |                    1.9 |                       5.08 |            24 |                0.56 | 18:45               | False                  | False                |
| USD/SEK  | 2009-03-17          |        5.05 |                    2   |                       4.66 |            24 |                1.38 | 18:15               | False                  | False                |
| USD/SEK  | 2008-11-12          |        5.02 |                    1.6 |                       3.05 |            24 |                0.69 | 19:35               | False                  | False                |
| USD/NOK  | 2020-03-17          |        9.99 |                    8.4 |                       7.05 |            24 |                1.27 | 14:25               | False                  | False                |
| USD/NOK  | 2020-03-19          |        9.81 |                    6   |                       4.78 |            20 |                2.56 | 12:25               | False                  | False                |
| USD/NOK  | 2020-03-18          |        8.25 |                    6.5 |                       0.5  |            22 |                2.38 | 08:35               | False                  | False                |
| USD/NOK  | 2016-06-23          |        7.31 |                    6.8 |                       4.45 |            23 |                0.99 | 23:15               | False                  | False                |
| USD/NOK  | 2020-03-22          |        6.34 |                    3.8 |                       3.43 |            24 |                1.49 | 14:00               | False                  | False                |
| Gold     | 2026-01-29          |       15.25 |                    7.2 |                       9.61 |            23 |                1.93 | 18:40               | False                  | False                |
| Gold     | 2013-04-14          |       11.33 |                   10.9 |                       9.16 |            24 |                1.7  | 20:15               | False                  | False                |
| Gold     | 2026-02-01          |       10.42 |                    4.9 |                       3.39 |            23 |                2.56 | 01:05               | False                  | False                |
| Gold     | 2026-03-22          |        9.63 |                    3.8 |                       1.59 |            23 |                3.2  | 10:05               | False                  | False                |
| Gold     | 2026-01-28          |        9.32 |                    5   |                       0.71 |            23 |                4.06 | 15:25               | False                  | False                |
| EUR/AUD  | 2008-10-07          |        9.8  |                    5.9 |                       5.72 |            24 |                1.76 | 12:45               | False                  | False                |
| EUR/AUD  | 2020-03-18          |        9.38 |                    6.6 |                       0.35 |            24 |                2.71 | 00:55               | False                  | False                |
| EUR/AUD  | 2008-10-05          |        8.83 |                    5.6 |                       7.19 |            24 |                1.52 | 14:10               | False                  | False                |
| EUR/AUD  | 2008-10-23          |        7.65 |                    2.3 |                       5.51 |            23 |                1.22 | 09:35               | False                  | False                |
| EUR/AUD  | 2008-10-14          |        6.89 |                    2.2 |                       5.67 |            24 |                0.83 | 21:35               | False                  | False                |

## 6. Sanity

* **EUR/USD, round 11's numbers from these imports:** 45 published cells (three methods x three horizons x five eras; sessions, both holding rates, width, score) re-computed; largest absolute difference 1.42e-14. 2018-26:

| candidate   |   h |   score_bp |   score_bp_published |   lower_held |   lower_held_published |   upper_held |   upper_held_published |
|:------------|----:|-----------:|---------------------:|-------------:|-----------------------:|-------------:|-----------------------:|
| bots        |   5 |    19.8382 |              19.8382 |       0.7916 |                 0.7916 |       0.8043 |                 0.8043 |
| har_d       |   5 |    19.8079 |              19.8079 |       0.813  |                 0.813  |       0.8252 |                 0.8252 |
| har_rv_ev   |   5 |    19.4803 |              19.4803 |       0.8126 |                 0.8126 |       0.8352 |                 0.8352 |
| bots        |  21 |    40.2526 |              40.2526 |       0.7849 |                 0.7849 |       0.8218 |                 0.8218 |
| har_d       |  21 |    39.7103 |              39.7103 |       0.802  |                 0.802  |       0.8534 |                 0.8534 |
| har_rv_ev   |  21 |    39.94   |              39.94   |       0.8051 |                 0.8051 |       0.8494 |                 0.8494 |
| bots        |  63 |    68.2971 |              68.2971 |       0.8028 |                 0.8028 |       0.7898 |                 0.7898 |
| har_d       |  63 |    68.4672 |              68.4672 |       0.8435 |                 0.8435 |       0.8524 |                 0.8524 |
| har_rv_ev   |  63 |    67.4526 |              67.4526 |       0.8269 |                 0.8269 |       0.8417 |                 0.8417 |

* **No future data:** 20 random sessions of EUR/GBP, inputs (session bars and hourly realised variances) cut off at the session, frame rebuilt, 360 levels of the three methods recomputed: largest difference in log distance 4.16e-17.

## 7. How firm is this? (descriptive, computed once after the verdict, outside `run()`; files `levels_confirm_seed_sensitivity.csv`, `levels_confirm_leave_one_out.csv`)

* **What is solid for K2:** the point estimate is better than the bots in 18 of 18 market-horizon cells in 2010-26; the 5-session gain (-2.1 %) excludes zero under every seed, with doubled blocks and with any one market left out; the evenness clause holds in 6 of 6 markets (spread roughly halved); the event-week shortfall falls from +2.5 to +0.4 points and stays below half with any one market left out (K1, which has no event term, leaves it at +2.0: the repair comes from the event term).
* **What is thin:** clause (1) needs a second interval. At 21 sessions the upper bound is -0.07 % (below zero for 20 of 20 bootstrap seeds, but +0.02 % with doubled block length); at 63 sessions -0.11 % (below zero for 10 of 20 seeds). Leaving out EUR/GBP, EUR/JPY or EUR/AUD leaves only the 5-session interval excluding zero, i.e. clause (1) would fail; in particular the pass depends on the reserve market EUR/AUD having replaced gold. In 2018-26 alone K2 passes (1), (2), (4) and misses (3) by one cell (63-session lower level held 83.4 %).
* **K1:** better at all three horizons and more even in 6 of 6 markets, with all six holding rates inside 77-83 %, but only the 63-session interval excludes zero (and that for 4 of 20 seeds). The evenness lead is real; the score gain of the daily-returns version is not established. K2 gives the same evenness plus the hourly volatility and event information.
* **Side asymmetry:** the regression candidates use ONE constant for both sides; on USD/SEK and USD/NOK, which rose over the sample, K2's 63-session lower level held 86 % and its upper 76 % (bots 78-79 % each side). Pooled it averages out; on a single trending market it does not. The bots' separate constants per side do not have this.
* **EUR/USD itself** did not pass in round 11 (C6 in 2018-26: -1.8 %* / -0.8 % / -1.2 %, levels 3-6 % wider there). The confirmation here is on other markets; it says the method generalises, not that EUR/USD's own history shows the gain beyond 5 sessions.
* **Wiring note for the lead:** `sharper_levels.levels(X, h, asof, name="har_rv_ev")` on `sharper_levels.build(D, h1)` needs the hourly bars (the live product has them) and the scheduled-event files in `data/macro` to extend past the forecast window (FOMC is listed to December 2027; ECB and BLS only to December 2026, so they need refreshing before a 63-session level set in autumn 2026 can count its events correctly).

