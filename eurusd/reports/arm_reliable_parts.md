# Arm BA: `reliable_parts` - do the range forecast and the level odds hold on six other dollar pairs?

Round 10. Code `src/eurusd/arms/reliable_parts.py` (`run()`, one process, about a minute; `python src/eurusd/arms/reliable_parts.py run`). Results `experiments/results/arms/reliable_parts_*.csv`. Pairs: GBP/USD, USD/JPY, AUD/USD, USD/CHF, USD/CAD, NZD/USD, 2003-2026 (NZD/USD from August 2005), HistData 5-minute bid bars cached by arm P. Nothing was re-tuned: same sessions, same regressors, same walk-forward, same level definition as on EUR/USD. Both primary tests and their pass bars were written into the module docstring before any accuracy or no-touch figure of another pair was computed. **Candidates: 11** (limit 12), listed at the end.

## Verdicts (read this first)

**A. Range forecast: FAILS the declared bar - 1 of 6 pairs pass (5 needed).** The identical model fitted walk-forward on each pair's own history calls next-session range above / below the 1-year median correctly on 68.3-73.9 % of sessions in 2010-26 and 66.3-72.5 % in 2016-26, against 75.1 / 75.6 % on EUR/USD (63.3-70.7 % against 75.0 % in 2023-26). EUR/USD ranks 1 of 7 in 2010-26 and 1 of 7 in 2016-26: once more the pair the number was published on is the best one. More than 4 points below EUR/USD in 2016-26: GBP/USD -5.4, USD/CHF -9.4, USD/CAD -5.1, NZD/USD -7.9. Less than 5 points above 'same class as yesterday' in at least one era: USD/JPY, USD/CHF. Only AUD/USD clears both conditions in both eras. The FROZEN version (EUR/USD's coefficients applied to each pair's ranges relative to its own median, nothing fitted on the pair) passes on 1 of 6 as well and is within about one point of the own fit on every pair: it is not the coefficients that fail to transfer, it is the LEVEL of the score.

What does hold on all six pairs: (i) the forecast is real everywhere - it beats 'same class as yesterday' by 4.4 to 7.9 points in 2010-26 and 2016-26 (EUR/USD 6.9 / 7.6), every block-bootstrap interval excluding zero, and with the session order shuffled it falls to 51.8-52.3 % (baseline 49.7-50.5 %); (ii) the 80 % band of the own fit covers 76.9-81.8 % in every pair and every era (declared 'holds' range 76-84); (iii) the 'volatile day' call is right 84-93 % of the time (EUR/USD 93.5 %), within 5 points of EUR/USD in both eras only on USD/JPY, USD/CHF. So the model form is structural and its error band is calibrated everywhere, but the published '75-78 % / 93 %' are EUR/USD's own figures; on the other six pairs the honest numbers are 66-74 % and 84-93 %.

**B. Level / no-touch odds: the LEVEL clause PASSES (24 of 24 pair-odds within 4 points of the EUR/USD quote; the largest gap is 2.2 points), the STABILITY clause FAILS as written (21 of 24 cells within 4 points across 2010-15 / 2016-22 / 2023-26; all 24 were required). By the letter of the declared bar, B FAILS on stability.** The misses: USD/CAD 2 ATR / 10 sessions, spread 4.3; AUD/USD 3 ATR / 21 sessions, spread 4.2; USD/CAD 3 ATR / 21 sessions, spread 5.4. Declared in advance and reported next to the verdict: a stationary driftless surrogate of the same six histories (signs of the sessions flipped at random, volatility untouched) breaks the same clause in 3.5 of 24 cells on average, passes all 24 in only 6 % of histories and shows at least 3 unstable cells in 64 % (pairs treated as independent). The stability clause as I wrote it would be failed about 19 times in 20 by a process that is perfectly stable, so its failure carries no information; that is a flaw of the bar, stated here rather than repaired after the fact. On the weekly grid of the publication: level 24 of 24, stability 20 of 24.

In substance the odds replicate almost exactly. Pooled over the six pairs (2010-26, every session): 68.7 / 86.5 % for 2 / 3 ATR within 10 sessions and 51.4 / 70.5 % within 21, against the product's 69 / 87 / 52 / 71 % and EUR/USD's own 68.9 / 86.4 / 51.2 / 70.8 % on the same grid.

**And the reason they replicate is that they are arithmetic, not prediction.** A driftless Brownian motion with constant volatility gives P(no touch) = 2 Phi(k x 1.596 / sqrt(h)) - 1 = 68.7 / 87.0 / 51.4 / 70.4 % with no data at all (1.596 = expected session range in units of daily sigma). For every pair and each of the four odds the realised 2010-26 figure lies inside the 95 % range of that pair's sign-flip surrogate (24 of 24; EUR/USD 4 of 4). Nothing about direction or path is being predicted; the only empirical content is that ATR14 measures the volatility of the next 10-21 sessions, which is true of every pair tested. The stop / target layer is therefore structural - and it is also not an edge.

## Test A - next-session range (own fit, candidate C1)

Accuracy = share of sessions on which 'forecast above the trailing 1-year median range' matches 'realised above it'; [95 % Wilson interval]; baseline = same class as yesterday; edge = accuracy minus baseline [paired block-bootstrap interval, 21-session blocks]; n = scored sessions (one decision per session, about 258 a year). EUR/USD = the store's own figure for the same era. 'ok' = within the bar (not more than 4 points below EUR/USD; edge at least 5).

| pair    | era     | accuracy %       | EUR/USD %   | gap   | baseline %   | edge                 | n    | gap ok   | edge ok   |
|:--------|:--------|:-----------------|:------------|:------|:-------------|:---------------------|:-----|:---------|:----------|
| EUR/USD | 2010-26 | 75.1 [73.8-76.3] | 75.1        | +0.0  | 68.2         | +6.9 [+5.6 .. +8.3]  | 4372 |          |           |
| EUR/USD | 2016-26 | 75.6 [74.0-77.2] | 75.6        | +0.0  | 68.0         | +7.6 [+6.1 .. +9.1]  | 2816 |          |           |
| EUR/USD | 2023-26 | 75.0 [72.2-77.6] | 75.0        | +0.0  | 66.9         | +8.1 [+6.0 .. +10.4] | 999  |          |           |
| GBP/USD | 2010-26 | 71.2 [69.8-72.5] | 75.1        | -3.9  | 64.1         | +7.1 [+5.8 .. +8.4]  | 4371 | yes      | yes       |
| GBP/USD | 2016-26 | 70.3 [68.6-71.9] | 75.6        | -5.4  | 63.6         | +6.7 [+5.1 .. +8.4]  | 2815 | NO       | yes       |
| GBP/USD | 2023-26 | 67.7 [64.7-70.5] | 75.0        | -7.3  | 60.3         | +7.4 [+4.7 .. +10.2] | 999  |          |           |
| USD/JPY | 2010-26 | 73.9 [72.6-75.2] | 75.1        | -1.2  | 69.1         | +4.7 [+3.2 .. +6.0]  | 4371 | yes      | NO        |
| USD/JPY | 2016-26 | 71.7 [70.0-73.3] | 75.6        | -4.0  | 66.9         | +4.8 [+3.1 .. +6.5]  | 2815 | yes      | NO        |
| USD/JPY | 2023-26 | 68.4 [65.4-71.2] | 75.0        | -6.6  | 66.3         | +2.1 [-1.1 .. +5.2]  | 999  |          |           |
| AUD/USD | 2010-26 | 71.9 [70.5-73.2] | 75.1        | -3.2  | 64.2         | +7.7 [+6.2 .. +9.1]  | 4372 | yes      | yes       |
| AUD/USD | 2016-26 | 72.5 [70.9-74.2] | 75.6        | -3.1  | 64.8         | +7.7 [+5.9 .. +9.3]  | 2816 | yes      | yes       |
| AUD/USD | 2023-26 | 70.1 [67.2-72.9] | 75.0        | -4.8  | 63.2         | +6.9 [+3.8 .. +9.8]  | 998  |          |           |
| USD/CHF | 2010-26 | 68.3 [66.9-69.6] | 75.1        | -6.8  | 63.7         | +4.5 [+2.9 .. +6.0]  | 4372 | NO       | NO        |
| USD/CHF | 2016-26 | 66.3 [64.5-68.0] | 75.6        | -9.4  | 61.9         | +4.4 [+2.2 .. +6.4]  | 2816 | NO       | NO        |
| USD/CHF | 2023-26 | 63.3 [60.2-66.2] | 75.0        | -11.7 | 60.3         | +3.0 [-0.7 .. +6.8]  | 999  |          |           |
| USD/CAD | 2010-26 | 73.5 [72.1-74.8] | 75.1        | -1.6  | 65.5         | +7.9 [+6.5 .. +9.3]  | 4373 | yes      | yes       |
| USD/CAD | 2016-26 | 70.5 [68.8-72.2] | 75.6        | -5.1  | 63.0         | +7.5 [+5.4 .. +9.3]  | 2817 | NO       | yes       |
| USD/CAD | 2023-26 | 70.7 [67.8-73.4] | 75.0        | -4.3  | 62.2         | +8.5 [+5.3 .. +11.7] | 999  |          |           |
| NZD/USD | 2010-26 | 69.3 [67.9-70.6] | 75.1        | -5.8  | 62.1         | +7.1 [+5.9 .. +8.5]  | 4371 | NO       | yes       |
| NZD/USD | 2016-26 | 67.8 [66.0-69.5] | 75.6        | -7.9  | 59.9         | +7.9 [+6.1 .. +9.5]  | 2815 | NO       | yes       |
| NZD/USD | 2023-26 | 66.9 [64.0-69.8] | 75.0        | -8.0  | 60.8         | +6.1 [+3.2 .. +9.1]  | 998  |          |           |

Pass per pair (both conditions in 2010-26 and in 2016-26): GBP/USD fail, USD/JPY fail, AUD/USD PASS, USD/CHF fail, USD/CAD fail, NZD/USD fail.

### Frozen EUR/USD coefficients (C2), the other figures of the model, and the USD-only flag (C3)

| pair    | own fit 2010-26   | frozen 2010-26   | USD-only flag 2010-26   | own fit 2016-26   | frozen 2016-26   | USD-only flag 2016-26   | frozen edge 2010-26 / 2016-26   | frozen passes   |
|:--------|:------------------|:-----------------|:------------------------|:------------------|:-----------------|:------------------------|:--------------------------------|:----------------|
| EUR/USD | 75.1              | 75.1             | 75.1                    | 75.6              | 75.6             | 75.6                    | +6.9 / +7.6                     |                 |
| GBP/USD | 71.2              | 71.5             | 71.2                    | 70.3              | 70.6             | 70.3                    | +7.4 / +7.0                     | fail            |
| USD/JPY | 73.9              | 73.2             | 73.9                    | 71.7              | 70.8             | 71.7                    | +4.0 / +3.9                     | fail            |
| AUD/USD | 71.9              | 71.7             | 71.5                    | 72.5              | 72.6             | 72.0                    | +7.5 / +7.7                     | PASS            |
| USD/CHF | 68.3              | 68.4             | 68.1                    | 66.3              | 66.5             | 66.1                    | +4.7 / +4.6                     | fail            |
| USD/CAD | 73.5              | 73.0             | 73.1                    | 70.5              | 70.2             | 69.9                    | +7.5 / +7.1                     | fail            |
| NZD/USD | 69.3              | 70.1             | 69.1                    | 67.8              | 68.2             | 67.7                    | +7.9 / +8.3                     | fail            |

'Volatile call' = forecast in the top fifth of the last year -> realised range above the median (unconditional rate 44-47 %); 'quiet call' = forecast 15 % below the median -> realised below. Last column: accuracy minus the accuracy of the simpler rule 'is the 21-session mean range above the median' - the regression adds only 1-2 points over that, on EUR/USD too.

| pair    | volatile call 2010-26 (n)   | volatile call 2016-26 (n)   | volatile call 2023-26 (n)   | 80 % band 2010-26   | 80 % band 2016-26   | 80 % band 2023-26   | band frozen 2010-26   | quiet call 2010-26   | vs 21-session-mean class 2010-26   |
|:--------|:----------------------------|:----------------------------|:----------------------------|:--------------------|:--------------------|:--------------------|:----------------------|:---------------------|:-----------------------------------|
| EUR/USD | 93.5 (713)                  | 93.4 (486)                  | 92.0 (87)                   | 80.1                | 80.5                | 78.4                | 80.1                  | 82.0                 | +1.3                               |
| GBP/USD | 84.2 (474)                  | 82.7 (330)                  | 74.0 (50)                   | 79.0                | 78.6                | 77.8                | 80.6                  | 81.6                 | +0.7                               |
| USD/JPY | 93.3 (654)                  | 93.5 (372)                  | 91.9 (37)                   | 79.2                | 80.5                | 78.7                | 73.9                  | 80.7                 | +1.9                               |
| AUD/USD | 88.5 (563)                  | 89.8 (403)                  | 86.3 (73)                   | 81.1                | 81.1                | 81.8                | 82.3                  | 82.5                 | +1.6                               |
| USD/CHF | 91.1 (570)                  | 90.4 (272)                  | 90.0 (40)                   | 79.8                | 80.3                | 77.8                | 78.7                  | 78.9                 | +0.7                               |
| USD/CAD | 89.5 (569)                  | 87.0 (277)                  | 87.7 (73)                   | 79.3                | 78.9                | 77.9                | 80.6                  | 80.7                 | +1.8                               |
| NZD/USD | 84.7 (463)                  | 86.2 (246)                  | 94.6 (37)                   | 79.7                | 79.5                | 80.8                | 82.5                  | 81.5                 | +1.4                               |

The frozen band is too narrow on USD/JPY (its forecast error is larger: log sd 0.42-0.44 against EUR/USD's 0.38) and fine on the other five. The USD-only event flag changes nothing (at most 0.6 points): the other currency's calendar is not what the model lives on.

### Why EUR/USD scores highest (post hoc, descriptive)

| pair    | spread of the forecast around the 1-year median (log sd)   | out-of-sample forecast error (log sd)   | log R2 against the median   | accuracy implied by those two %   | realised %   | forecasts within 10 % of the median %   |
|:--------|:-----------------------------------------------------------|:----------------------------------------|:----------------------------|:----------------------------------|:-------------|:----------------------------------------|
| EUR/USD | 0.35                                                       | 0.38                                    | 0.45                        | 74.2                              | 75.1         | 21.5                                    |
| GBP/USD | 0.29                                                       | 0.38                                    | 0.36                        | 71.5                              | 71.2         | 24.0                                    |
| USD/JPY | 0.41                                                       | 0.44                                    | 0.46                        | 72.6                              | 73.9         | 21.4                                    |
| AUD/USD | 0.30                                                       | 0.36                                    | 0.39                        | 71.5                              | 71.9         | 26.3                                    |
| USD/CHF | 0.31                                                       | 0.39                                    | 0.36                        | 69.3                              | 68.3         | 31.9                                    |
| USD/CAD | 0.32                                                       | 0.38                                    | 0.41                        | 72.4                              | 73.5         | 23.4                                    |
| NZD/USD | 0.27                                                       | 0.36                                    | 0.33                        | 69.7                              | 69.3         | 30.5                                    |

The forecast error is about the same size on all seven pairs. What differs is how far each pair's volatility wanders from its year-ago median: when the forecast sits far from the median the class is easy, when it sits on it the call is a coin flip. A Gaussian calculation from the two columns reproduces every pair's accuracy to within 1.3 points. So 'accuracy on above / below the median' is a regime-width number, not a pure forecast-quality number: single-year accuracy ranges from 54 % to 94 % across the seven pairs and 17 years (EUR/USD 59-91 %; `reliable_parts_range_by_year.csv`). The transferable statements are the error band and the edge over the baseline.

## Test B - level / no-touch odds (candidate C4: every test session; one-sided, upper and lower level pooled)

Share of sessions (percent) on which a level k x ATR14 away from the close is NOT touched within h sessions, by intraday highs and lows. [95 % Wilson interval on the effective number of events: non-overlapping windows only, about 436 independent 10-session and 207 independent 21-session windows per pair in 2010-26]. n = 4,351-4,364 sessions per pair (about 257 a year). 'RW' = analytic driftless Brownian motion, no data.

**2010-26**

| pair                             | 2 ATR / 10 s   | 3 ATR / 10 s   | 2 ATR / 21 s   | 3 ATR / 21 s   |
|:---------------------------------|:---------------|:---------------|:---------------|:---------------|
| EUR/USD                          | 68.9 [66-72]   | 86.4 [84-88]   | 51.2 [46-56]   | 70.8 [66-75]   |
| GBP/USD                          | 68.6 [65-72]   | 86.6 [84-89]   | 50.9 [46-56]   | 70.3 [66-74]   |
| USD/JPY                          | 68.3 [65-71]   | 84.8 [82-87]   | 50.9 [46-56]   | 69.5 [65-74]   |
| AUD/USD                          | 68.7 [66-72]   | 87.6 [85-90]   | 51.4 [47-56]   | 71.4 [67-76]   |
| USD/CHF                          | 68.9 [66-72]   | 86.5 [84-89]   | 51.4 [47-56]   | 70.0 [65-74]   |
| USD/CAD                          | 68.8 [66-72]   | 86.9 [84-89]   | 52.2 [47-57]   | 71.5 [67-76]   |
| NZD/USD                          | 68.7 [66-72]   | 86.7 [84-89]   | 51.6 [47-56]   | 70.4 [66-75]   |
| six pairs pooled                 | 68.7           | 86.5           | 51.4           | 70.5           |
| EUR/USD as quoted by the product | 69             | 87             | 52             | 71             |
| RW (analytic)                    | 68.7           | 87.0           | 51.4           | 70.4           |

**By era (bar: max - min of the three eras at most 4 points)**

| pair    | level / window   | 2010-15   | 2016-22   | 2023-26   | spread   | stable   | EUR/USD quote   | 2010-26 minus quote   | surrogate: share of histories with spread > 4   |
|:--------|:-----------------|:----------|:----------|:----------|:---------|:---------|:----------------|:----------------------|:------------------------------------------------|
| EUR/USD | 2 ATR / 10 s     | 68.2      | 69.2      | 69.5      | 1.4      | yes      | 69              | -0.1                  | 6 %                                             |
| EUR/USD | 3 ATR / 10 s     | 86.3      | 85.7      | 87.7      | 2.0      | yes      | 87              | -0.6                  | 2 %                                             |
| EUR/USD | 2 ATR / 21 s     | 50.7      | 51.8      | 50.8      | 1.1      | yes      | 52              | -0.8                  | 10 %                                            |
| EUR/USD | 3 ATR / 21 s     | 71.0      | 71.9      | 68.4      | 3.5      | yes      | 71              | -0.2                  | 26 %                                            |
| GBP/USD | 2 ATR / 10 s     | 68.4      | 68.6      | 68.9      | 0.5      | yes      | 69              | -0.4                  | 8 %                                             |
| GBP/USD | 3 ATR / 10 s     | 86.9      | 86.1      | 87.2      | 1.1      | yes      | 87              | -0.4                  | 6 %                                             |
| GBP/USD | 2 ATR / 21 s     | 51.2      | 51.1      | 50.0      | 1.2      | yes      | 52              | -1.1                  | 8 %                                             |
| GBP/USD | 3 ATR / 21 s     | 70.9      | 70.0      | 69.6      | 1.3      | yes      | 71              | -0.7                  | 34 %                                            |
| USD/JPY | 2 ATR / 10 s     | 68.8      | 67.5      | 69.1      | 1.7      | yes      | 69              | -0.7                  | 11 %                                            |
| USD/JPY | 3 ATR / 10 s     | 85.4      | 84.0      | 85.3      | 1.4      | yes      | 87              | -2.2                  | 3 %                                             |
| USD/JPY | 2 ATR / 21 s     | 52.5      | 50.2      | 49.5      | 2.9      | yes      | 52              | -1.1                  | 22 %                                            |
| USD/JPY | 3 ATR / 21 s     | 71.3      | 68.7      | 67.9      | 3.5      | yes      | 71              | -1.5                  | 32 %                                            |
| AUD/USD | 2 ATR / 10 s     | 68.3      | 68.8      | 69.1      | 0.7      | yes      | 69              | -0.3                  | 14 %                                            |
| AUD/USD | 3 ATR / 10 s     | 88.3      | 86.6      | 88.7      | 2.1      | yes      | 87              | +0.6                  | 7 %                                             |
| AUD/USD | 2 ATR / 21 s     | 51.7      | 50.6      | 52.3      | 1.7      | yes      | 52              | -0.6                  | 20 %                                            |
| AUD/USD | 3 ATR / 21 s     | 71.7      | 69.7      | 73.9      | 4.2      | NO       | 71              | +0.4                  | 35 %                                            |
| USD/CHF | 2 ATR / 10 s     | 67.1      | 70.0      | 69.7      | 2.8      | yes      | 69              | -0.1                  | 8 %                                             |
| USD/CHF | 3 ATR / 10 s     | 85.6      | 86.7      | 87.4      | 1.7      | yes      | 87              | -0.5                  | 5 %                                             |
| USD/CHF | 2 ATR / 21 s     | 50.2      | 51.8      | 52.7      | 2.5      | yes      | 52              | -0.6                  | 9 %                                             |
| USD/CHF | 3 ATR / 21 s     | 68.5      | 71.1      | 70.5      | 2.6      | yes      | 71              | -1.0                  | 28 %                                            |
| USD/CAD | 2 ATR / 10 s     | 70.1      | 69.4      | 65.9      | 4.3      | NO       | 69              | -0.2                  | 2 %                                             |
| USD/CAD | 3 ATR / 10 s     | 87.7      | 87.3      | 84.8      | 2.9      | yes      | 87              | -0.1                  | 4 %                                             |
| USD/CAD | 2 ATR / 21 s     | 53.5      | 52.3      | 49.8      | 3.7      | yes      | 52              | +0.2                  | 11 %                                            |
| USD/CAD | 3 ATR / 21 s     | 74.0      | 70.8      | 68.6      | 5.4      | NO       | 71              | +0.5                  | 33 %                                            |
| NZD/USD | 2 ATR / 10 s     | 69.9      | 67.9      | 68.0      | 2.0      | yes      | 69              | -0.3                  | 9 %                                             |
| NZD/USD | 3 ATR / 10 s     | 86.7      | 86.0      | 88.0      | 2.0      | yes      | 87              | -0.3                  | 2 %                                             |
| NZD/USD | 2 ATR / 21 s     | 52.6      | 50.6      | 51.8      | 2.0      | yes      | 52              | -0.4                  | 10 %                                            |
| NZD/USD | 3 ATR / 21 s     | 70.5      | 69.4      | 72.1      | 2.7      | yes      | 71              | -0.6                  | 30 %                                            |

Last column: how often a perfectly stationary, driftless version of the same pair (sign-flip surrogate, 200 draws) shows an era spread above 4 points in that cell. Summed over the 24 cells of the six pairs that is 3.5 expected failures; 3 were observed. EUR/USD's own four cells are all stable (it would fail at least one in 32 % of its surrogate histories).

Upper and lower side separately (2010-26): the pooled figure hides a side asymmetry wherever the pair trended over the sample.

| pair    | 2 ATR / 10 s: upper / lower   | 3 ATR / 10 s: upper / lower   | 2 ATR / 21 s: upper / lower   | 3 ATR / 21 s: upper / lower   |
|:--------|:------------------------------|:------------------------------|:------------------------------|:------------------------------|
| EUR/USD | 70.2 / 67.7                   | 87.0 / 85.7                   | 52.5 / 49.8                   | 71.6 / 70.0                   |
| GBP/USD | 69.4 / 67.8                   | 87.9 / 85.3                   | 49.9 / 51.9                   | 70.5 / 70.1                   |
| USD/JPY | 67.3 / 69.4                   | 84.6 / 85.0                   | 48.9 / 52.8                   | 67.7 / 71.2                   |
| AUD/USD | 70.4 / 67.0                   | 90.0 / 85.3                   | 52.6 / 50.2                   | 73.8 / 69.0                   |
| USD/CHF | 68.9 / 68.9                   | 87.4 / 85.5                   | 52.2 / 50.6                   | 71.6 / 68.4                   |
| USD/CAD | 65.4 / 72.3                   | 84.1 / 89.7                   | 48.1 / 56.3                   | 67.0 / 75.9                   |
| NZD/USD | 69.6 / 67.7                   | 87.8 / 85.6                   | 52.0 / 51.2                   | 72.0 / 68.9                   |

## Is anything being predicted? (secondary 4a, candidate C6)

| level / window   | product quote   | EUR/USD realised   | six pairs pooled   | analytic Brownian   | Monte Carlo, constant vol, 288 steps   | sign-flip surrogate, six pairs (mean; widest 95 % range)   | pairs inside their own surrogate range   |
|:-----------------|:----------------|:-------------------|:-------------------|:--------------------|:---------------------------------------|:-----------------------------------------------------------|:-----------------------------------------|
| 2 ATR / 10 s     | 69              | 68.9               | 68.7               | 68.7                | 67.2                                   | 68.4; 66.7-70.0                                            | 6 of 6 (+ EUR/USD yes)                   |
| 3 ATR / 10 s     | 87              | 86.4               | 86.5               | 87.0                | 85.7                                   | 86.0; 83.4-88.0                                            | 6 of 6 (+ EUR/USD yes)                   |
| 2 ATR / 21 s     | 52              | 51.2               | 51.4               | 51.4                | 50.2                                   | 51.2; 49.2-53.1                                            | 6 of 6 (+ EUR/USD yes)                   |
| 3 ATR / 21 s     | 71              | 70.8               | 70.5               | 70.4                | 69.1                                   | 69.7; 66.6-72.7                                            | 6 of 6 (+ EUR/USD yes)                   |

The sign-flip surrogate keeps every session's range and all volatility clustering and removes any drift, trend or reversal across sessions. The realised odds sit inside its range for every pair and every level: the odds are what a driftless walk with the measured volatility gives. The formula works because the ATR is a fixed multiple of daily sigma: ATR14 / sigma of daily returns in 2010-26 is EUR/USD 1.49, GBP/USD 1.46, USD/JPY 1.42, AUD/USD 1.52, USD/CHF 1.29, USD/CAD 1.51, NZD/USD 1.56 (Brownian motion: 1.60; a 5-minute Gaussian walk: 1.53). Fat tails lower the ratio (USD/CHF's 2015 de-peg, USD/JPY's intervention days). USD/JPY's 3-ATR / 10-session odds are the lowest of the seven (84.8 %); its own surrogate gives 84.6 %, so that too is its volatility pattern, not direction. The full grid (k = 0.5 .. 4 ATR, h = 5, 10, 21) per pair, pooled and against both random walks is in `reliable_parts_calibration_notouch.csv`: pooled realised and analytic differ by at most 1.1 points over the 21 cells.

## Does the range forecast improve the odds? (secondary 4b, candidates C7, C8)

| pair    | 2 x ATR level, 10 s: quiet / normal / volatile   | 2 x forecast level, 10 s: quiet / normal / volatile   | 2 x ATR level, 21 s: quiet / normal / volatile   | 2 x forecast level, 21 s: quiet / normal / volatile   | 2 ATR, 10 s by forecast / ATR tercile: low / mid / high   |
|:--------|:-------------------------------------------------|:------------------------------------------------------|:-------------------------------------------------|:------------------------------------------------------|:----------------------------------------------------------|
| EUR/USD | 65.2 / 70.1 / 74.3                               | 66.2 / 70.1 / 73.4                                    | 48.2 / 52.2 / 55.2                               | 49.4 / 52.8 / 54.8                                    | 69.2 / 68.8 / 68.8                                        |
| GBP/USD | 66.8 / 68.7 / 73.6                               | 68.3 / 69.0 / 72.4                                    | 49.9 / 50.3 / 57.2                               | 51.7 / 51.2 / 55.6                                    | 69.4 / 68.5 / 68.3                                        |
| USD/JPY | 65.7 / 69.8 / 70.0                               | 66.8 / 68.8 / 68.1                                    | 47.5 / 52.6 / 53.1                               | 50.3 / 52.5 / 50.7                                    | 68.9 / 69.6 / 67.1                                        |
| AUD/USD | 66.5 / 69.2 / 71.9                               | 66.7 / 69.3 / 71.2                                    | 48.2 / 52.2 / 56.2                               | 49.7 / 53.0 / 55.7                                    | 69.4 / 68.3 / 68.5                                        |
| USD/CHF | 64.7 / 70.2 / 72.2                               | 66.3 / 71.0 / 70.0                                    | 47.6 / 52.5 / 54.8                               | 49.6 / 53.5 / 53.2                                    | 69.0 / 69.2 / 68.8                                        |
| USD/CAD | 67.1 / 68.8 / 74.2                               | 67.3 / 69.1 / 73.4                                    | 50.9 / 51.7 / 57.7                               | 51.7 / 52.3 / 57.4                                    | 69.1 / 68.6 / 68.8                                        |
| NZD/USD | 65.2 / 69.5 / 73.1                               | 66.7 / 70.4 / 72.6                                    | 48.1 / 52.0 / 58.2                               | 49.7 / 53.6 / 57.2                                    | 69.4 / 68.3 / 68.5                                        |

Day class = the range model's own call at the decision session (quiet: forecast 15 % below the 1-year median, about a third of sessions; volatile: forecast in the top fifth of the last year, 11-16 %). Two findings, the same on all seven pairs. (1) The quoted odds are an average over volatility states: a 2-ATR level survives 10 sessions 65-67 % of the time when the forecast says quiet and 70-74 % when it says volatile (volatility reverts to its mean, the ATR lags it): a spread of 4.3-9.1 points at 2 ATR / 10 sessions and 4.7-11.8 points at 21 sessions. (2) Relative to the ATR the one-session forecast adds nothing: by terciles of forecast / ATR14 the odds are flat (within 2 points). Setting the level from the multi-session forecast instead of the ATR (C8) narrows the quiet-volatile spread by more than half a point in 28 of 28 pair-odds (by 0.5 to 5.2 points), but the yearly odds become MORE dispersed (smaller yearly standard deviation in only 3 of 28 pair-odds). By the reading declared in advance (both smaller on at least 5 of 7 pairs) the forecast does NOT improve the odds. The honest use of finding (1) is a caveat on the quote, not a new level rule.

## Pooled calibration data (secondary 4c, candidate C9)

| predicted P(range above median) bin   | six pairs, own fit: predicted   | realised   | n    | six pairs, frozen: realised   | EUR/USD: predicted   | EUR/USD: realised   | EUR/USD n   |
|:--------------------------------------|:--------------------------------|:-----------|:-----|:------------------------------|:---------------------|:--------------------|:------------|
| 0-10 %                                | 6.3                             | 7.1        | 995  | 7.3                           | 6.7                  | 6.6                 | 288         |
| 10-20 %                               | 15.5                            | 14.8       | 2684 | 15.1                          | 15.0                 | 14.6                | 583         |
| 20-30 %                               | 25.1                            | 22.7       | 3664 | 23.1                          | 25.0                 | 22.6                | 584         |
| 30-40 %                               | 35.0                            | 30.6       | 3768 | 30.9                          | 35.1                 | 31.0                | 564         |
| 40-50 %                               | 44.9                            | 39.7       | 3557 | 39.9                          | 44.5                 | 40.8                | 505         |
| 50-60 %                               | 54.9                            | 49.6       | 3018 | 50.4                          | 55.1                 | 53.4                | 395         |
| 60-70 %                               | 64.9                            | 59.5       | 2587 | 59.0                          | 64.9                 | 62.7                | 346         |
| 70-80 %                               | 74.8                            | 71.9       | 2159 | 71.6                          | 74.6                 | 69.4                | 304         |
| 80-90 %                               | 84.8                            | 79.4       | 1863 | 79.3                          | 85.1                 | 85.1                | 316         |
| 90-100 %                              | 95.5                            | 94.9       | 1935 | 94.2                          | 95.0                 | 95.9                | 487         |

P(above median) from the log-normal forecast is reliable at the ends and 3-5 points too high in the middle bins on the six pairs (2-4 on EUR/USD): the forecast error is right-skewed, so 'forecast = median' means about 45 %, not 50 %, of exceeding it. Files: `reliable_parts_calibration_range.csv` (per pair, pooled, own fit and frozen), `reliable_parts_calibration_notouch.csv`.

## Step 1 - reconcile on EUR/USD (done before any other pair)

* Sessions: this module's 5-minute -> hourly -> `daily_ohlc(h1, 22)` code on `EURUSD_M5` gives the store's 6,186 sessions with close, range and ATR14 differences of exactly 0; the generic event-flag constructor (USD rows of the store's list + ForexFactory 'High' rows of the other currency) reproduces the store's EUR + USD flag on 100 % of sessions.
* Range forecast: all 21 published scoreboard figures reproduced (largest difference 0.05 points = rounding; n identical: 4,372 / 2,816 / 999).
* No-touch odds: the 12 published weekly-grid figures reproduced to 0.05 points, and realised and predicted frequencies equal to `selective_path_calibration.csv` in all 32 cells (largest difference 0.000000). On every session instead of every fifth, EUR/USD gives 68.9 / 86.4 / 51.2 / 70.8 %.
* Independent re-computation: brute-force loops over the cached daily frames (no shared code) return the same USD/JPY and GBP/USD odds to 0.01 point and the same USD/JPY range accuracy.

## Data and checks

Source: `data/processed/cross/ofi_<pair>_M5.parquet` (HistData 1-minute bid bars aggregated to 5 minutes by arm P, stamps converted America/New_York -> UTC there). Sessions exactly as the EUR/USD store builds them. GBP/USD 6,187 sessions; USD/JPY 6,189 sessions; AUD/USD 6,188 sessions; USD/CHF 6,180 sessions; USD/CAD 6,190 sessions; NZD/USD 5,505 sessions. No bar with inconsistent open / high / low / close.

* **Time stamps re-checked against the Fed H.10 noon New York rate** (`fred_DEX*.csv`, 5,200-5,900 days per pair): the 5-minute bar ending 12:00 New York time differs from the H.10 rate by a median of 0.8-2.0 pips in US summer and in US winter alike; the bars one hour earlier or later differ by 5.0-12.0 pips. The stamps are right in both seasons on all six pairs (`reliable_parts_check_timestamps.csv`).
* **Sessions against independent daily sources.** (a) The H.10 rate lies inside the [low, high] of the session that contains noon New York on 99.5-99.8 % of days, and within 2 pips of it on 99.9 % or more (bid bars against a mid-market fix). (b) Session log range against the CME futures daily range of the same trade date (Yahoo), 2003-2016, all six pairs: correlation 0.91-0.99, median ratio 0.99-1.06. From 2017 the futures file itself degrades for GBP, JPY, AUD and CAD (median daily volume a few hundred contracts instead of ~100,000: stub bars; EUR shows the same, CHF and NZD do not): on the days with real volume the median ratio is still 0.99-1.00, on the stub days 1.15-1.40. So for those four pairs 2017-26 is only partly verified by futures. (c) Sessions built with the same code from Yahoo HOURLY spot bars, 2024-01-23 .. 2026-11-05, four pairs: range correlation 0.986-0.997, median ratio 0.99-1.02, closes within 4 pips at the median. Yahoo's DAILY spot bars are too poor to judge by (correlation 0.5-0.7) but their ratio to the sessions does not move between eras (1.03-1.14). `reliable_parts_check_range_sources.csv`.
* **The 2023 hole is in all six pairs**, as in EUR/USD: 113-114 sessions of February-July 2023 have fewer than 20 hourly bars (34-37 such sessions in all other years together, 15 for NZD/USD). Their ranges are understated. Primary treatment identical to the store (kept); sensitivity below.

* **Bad ticks.** Rule fixed before any accuracy was computed: a 5-minute bar whose high (low) lies more than 400 pips beyond its own open and close, the previous close and the next open has that wick removed. It flags 4 bars: USD/JPY 2004-06-17 07:45 (494 pips); USD/CHF 2004-03-30 14:55 (6,387 pips); USD/CHF 2004-05-17 15:35 (6,401 pips); USD/CHF 2005-01-11 12:45 (4,997 pips). All are in 2004-05, i.e. inside training windows only; nothing is flagged on EUR/USD and the largest wick left in place is 263 pips (GBP/USD, referendum night). HistData's noisy January 2004 (wicks of about 100 pips in every pair, EUR/USD included) is left as it is, as in the store. Nothing in the test years 2010-26 was altered.

* **Largest 20 session ranges per pair** (session start date, pips; `*` = changed by the rule). The rest are known events: October-December 2008, the May 2010 flash crash, August 2011, the SNB de-peg (USD/CHF session of 2015-01-14: 1,884 pips, real), August 2015, the Brexit vote and the October 2016 sterling flash crash, March 2020, September 2022, the 2022-24 yen interventions. Full table with the widest single bar of each session: `reliable_parts_check_top_ranges.csv`.

  * GBP/USD: 2016-06-23 1,779, 2008-10-23 1,034, 2008-12-17 731, 2020-03-17 680, 2008-11-02 617, 2008-10-27 610, 2022-09-25 604, 2008-10-26 600, 2008-11-30 592, 2016-10-06 591, 2008-11-11 586, 2009-01-19 581, 2008-10-21 579, 2008-10-20 553, 2008-11-24 551, 2008-10-28 536, 2015-03-17 533, 2008-10-12 515, 2008-09-07 505, 2008-11-03 502
  * USD/JPY: 2016-06-23 764, 2008-10-23 709, 2022-12-19 691, 2008-10-27 676, 2022-11-09 639, 2015-08-23 589, 2004-06-16 585*, 2026-07-29 578, 2022-10-20 576, 2010-05-05 572, 2023-12-06 568, 2024-04-28 568, 2022-09-21 556, 2026-04-29 517, 2024-04-30 500, 2008-10-05 493, 2024-08-04 489, 2007-08-15 474, 2016-11-08 470, 2011-03-15 467
  * AUD/USD: 2008-10-05 729, 2008-10-07 697, 2008-10-23 693, 2008-10-14 579, 2008-10-09 546, 2008-10-27 512, 2008-10-08 488, 2011-08-08 487, 2008-10-28 459, 2008-10-12 458, 2020-03-18 457, 2010-05-19 426, 2008-10-15 426, 2008-11-03 411, 2011-09-21 388, 2011-11-29 388, 2007-08-15 384, 2010-05-05 384, 2020-03-08 378, 2008-12-17 375
  * USD/CHF: 2004-05-16 6,560*, 2004-03-29 6,454*, 2005-01-10 5,017*, 2015-01-14 1,884, 2011-09-05 786, 2008-12-16 533, 2011-08-08 510, 2009-03-11 471, 2009-03-17 456, 2008-12-17 455, 2008-12-15 453, 2011-08-10 449, 2015-03-17 440, 2009-02-19 422, 2015-01-15 420, 2009-01-04 419, 2008-12-18 394, 2009-06-23 390, 2015-12-02 389, 2008-09-21 362
  * USD/CAD: 2008-10-28 744, 2008-10-09 674, 2008-11-23 534, 2008-10-21 492, 2020-03-17 484, 2008-11-19 462, 2010-05-05 458, 2008-12-10 450, 2008-10-30 436, 2008-11-03 421, 2025-02-02 405, 2008-11-11 404, 2008-10-23 397, 2008-12-15 392, 2009-01-13 387, 2008-10-14 387, 2015-03-17 386, 2020-03-19 386, 2009-01-22 383, 2008-11-05 372
  * NZD/USD: 2008-10-23 478, 2008-10-07 466, 2020-03-18 448, 2011-08-08 447, 2020-03-08 444, 2015-08-23 439, 2008-10-05 419, 2007-08-16 373, 2008-10-14 363, 2007-08-15 363, 2011-08-03 358, 2008-10-08 355, 2011-08-09 339, 2008-10-27 331, 2011-09-21 312, 2008-10-21 303, 2008-12-17 300, 2009-01-12 295, 2008-01-21 291, 2009-06-02 291

## Controls and sensitivities

* **Shuffled-order control** (range series permuted across sessions, 20 draws per pair): model accuracy 51.8-52.3 %, 'same class as yesterday' 49.7-50.5 %, always-majority 50.3 %. The accuracy falls to the baseline, as it should; the 2 points left over come from the noisy 250-session median (the fit knows the long-run median better than one year's sample does), not from order information.
* **2023 hole (C10).** Without test rows whose last or target session is thin: accuracy moves by at most 0.6 points in 2010-26 / 2016-26 and 1.3 in 2023-26. Without decision sessions whose window (14 sessions back to h ahead) contains a thin session: the odds move by at most 0.7 points in 2010-26 and 1.8 in 2023-26. No verdict changes.
* **Uncleaned frames (C11).** USD/JPY: identical (73.9 %). USD/CHF own fit: 67.1 % instead of 68.3 % in 2010-26 - the three 2004-05 bad ticks sit in the training window and distort the fit; cleaning helps USD/CHF by about a point and it still fails. The no-touch odds are unchanged to the decimal (test rows untouched).
* **USD-only event flag (C3):** within 0.6 points of the primary on every pair and era.
* **Weekly grid (C5):** level 24 of 24 within 4 points (largest gap 2.4); stability 20 of 24 (one fifth of the sessions, so noisier).

## Candidate count: 11

C1 range, own fit (PRIMARY A). C2 range, frozen EUR/USD coefficients. C3 range, USD-only event flag. C4 no-touch odds, every session (PRIMARY B). C5 no-touch odds, weekly grid. C6 random-walk benchmarks (analytic, Monte Carlo, sign-flip surrogate). C7 odds by forecast class and by forecast / ATR tercile. C8 levels set from the multi-session forecast. C9 pooled calibration data. C10 thin-session sensitivity. C11 uncleaned frames. Controls (not candidates): shuffled order, the data checks. Post hoc and labelled so: the signal-to-noise table, accuracy by year, the joint surrogate count for the stability clause.

## Anything suspicious

* **The stability clause of bar B was mis-specified by me**: 4 points across three eras is tighter than a 21-session window can resolve with 3-7 years per era. I report the failure as declared and the surrogate that shows it is uninformative; I did not re-draw the bar.
* **EUR/USD is again the best of seven** on the published statistic (range accuracy). Unlike the directional findings this one was not mined (one simple model, no search), and the post-hoc decomposition explains the gap by regime width rather than luck, but the pattern is the same as in rounds 3, 4 and 6 and the published figure should not be quoted for other pairs.
* USD/CAD is the one pair whose era figures drift (2-ATR / 10 sessions 70.1 -> 69.4 -> 65.9 %; 3 of its 12 era cells fall outside its surrogate range, about 0.6 expected). Its upper level was touched more often than its lower one over 2010-26 (USD/CAD rose over the sample). One pair of seven; worth watching, not a finding.
* The futures cross-check cannot fully verify GBP, JPY, AUD and CAD ranges after 2016 (Yahoo's futures bars degrade); the Yahoo hourly check covers only 2024-26. The HistData hole of February-July 2023 is in every pair.
* The event flag is uneven by construction (almost empty before 2010 and in 2024-25, for every currency); the model's event coefficient is correspondingly small and the flag is not what makes it work.
* All bars are bid quotes of one vendor; ranges and ATR include the spread widening of the roll-over hour. This affects levels of range, not the odds (ATR and excursions share it).

## What the product may honestly say about stops and targets

1. **Level odds: say them, for any liquid dollar pair, and say what they are.** 'A level 2 ATR from the close is left untouched over 10 sessions about 69 % of the time, 3 ATR about 87 %; over 21 sessions about 51 % and 70 %.' That held within 2.2 points on six other pairs and in every era within sampling noise. It must be labelled as the arithmetic of a driftless market with today's volatility (the same numbers come out of a formula with no data), not as a forecast and not as an edge: a stop placed with it has known odds of being hit by noise, and zero expectancy.
2. **Two caveats belong on the quote.** (a) It is an average over volatility states: after a quiet-forecast day the same level survives 2-4 points less often (65-67 % for 2 ATR / 10 sessions), after a volatile-forecast day 1-6 points more often (70-74 %). (b) It is the average of both sides; over 2010-26 the two sides differed by up to 9 points on a pair that trended (USD/CAD), 2.7 on EUR/USD.
3. **Range forecast: keep it for sizing and for the band, drop the headline accuracy outside EUR/USD.** What is structural: next-session range is forecastable on every pair from its own last 21 sessions, with frozen EUR/USD coefficients if need be, and the 80 % band of a pair's own fit contains the outcome 77-82 % of the time in every pair and era. What is EUR/USD-specific and must be labelled so: '75-78 % right on above / below normal' (66-74 % on the other six) and '93 % on volatile-day calls' (84-93 %). Even on EUR/USD the regression adds only 1-2 points over 'is the 21-session average range above normal'.
4. Nothing here changes the directional verdict of round 9. The stop / target / sizing layer is sound because it claims nothing about direction.
