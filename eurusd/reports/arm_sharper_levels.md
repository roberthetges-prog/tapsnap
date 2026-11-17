# Arm CA: `sharper_levels` - can the lower / upper levels be made narrower and more evenly reliable?

Round 11. Code `src/eurusd/arms/sharper_levels.py` (`run()`, one process, about eight minutes; `levels(X, h, asof)` gives the chosen candidate's levels). Results `experiments/results/arms/sharper_levels_*.csv`. The candidate list, the scoring, the selection rule and the pass bar were written into the module docstring before any candidate was scored. **Candidates: 12** (the limit), the bots' median level included as the baseline. Nothing was re-run with changed settings.

## Verdict (read this first)

**FAIL against the declared bar.** The declared rule (lowest proper score relative to the bots, averaged over the three horizons, on 2010-2017) picked **C3 HAR daily returns**: a regression of the next h sessions' range on the 5-, 21-, 63- and 252-session volatility of daily returns, one fit per horizon (score -4.2 % against the bots on 2010-17). On 2018-2026, which the selection never saw:

| sessions      |   bots: score (bp) |   chosen: score (bp) | difference   | 95 % interval of the difference (bp)   | bots: lower / upper held %   | chosen: lower / upper held %   | chosen: width vs bots   |   independent periods |
|:--------------|-------------------:|---------------------:|:-------------|:---------------------------------------|:-----------------------------|:-------------------------------|:------------------------|----------------------:|
| 5 (1 week)    |              19.84 |                19.81 | -0.2 %       | -0.25 .. +0.23                         | 79.2 / 80.4                  | 81.3 / 82.5                    | +2.4 %                  |                   459 |
| 21 (1 month)  |              40.25 |                39.71 | -1.3 %       | -1.37 .. +0.27                         | 78.5 / 82.2                  | 80.2 / 85.3                    | +3.7 %                  |                   108 |
| 63 (3 months) |              68.3  |                68.47 | +0.2 %       | -5.06 .. +5.40                         | 80.3 / 79.0                  | 84.3 / 85.2                    | +10.1 %                 |                    36 |

* (i) better proper score at all three horizons: **FAILS** (2 of 3; the three differences are -0.2 %, -1.3 %, +0.2 %).
* (ii) interval excludes zero at two horizons at least: **FAILS** (0 of 3).
* (iii) every level holds 77-83 %: **FAILS** (3 of 6 cells inside; the misses are on the HIGH side: the chosen levels held up to 85.3 %, i.e. they were too wide, not too narrow). Declared with the bar: an exactly calibrated method would pass this clause only 19 % of the time (the 63-session holding rate has a sampling error of about 5 points on 35 independent periods), so (iii) alone would prove little. The bots' own levels were inside 77-83 % in 6 of 6 cells.
* (iv) holding rate more even across volatility terciles: **passes** (average spread 4.7 points against the bots' 9.1).

Descriptive, because only the chosen candidate counts: the same bar applied to each of the eleven non-baseline candidates is passed by 0; 0 have an interval excluding zero at two horizons (the Garman-Klass, hourly and event versions beat the bots at all three horizons, with an interval excluding zero at 5 sessions only). So this is not the rule picking the wrong horse: on EUR/USD, nine unseen years confirm none of them.

**In plain words.**

1. NARROWER: **no**. In 2018-26 the chosen levels were +2.4 % / +3.7 % / +10.1 % wider than the bots' at 5 / 21 / 63 sessions and held more often than 80 %; the proper score, which trades width against misses, is the same to within sampling error.
2. EVENLY RELIABLE: **partly yes, and this part is solid.** The bots' levels hold too rarely in calm markets and too often in volatile ones (spread of the holding rate across volatility terciles 10.2 points in 2010-17, 9.1 in 2018-26); every regression-based candidate roughly halves that (C3 HAR daily returns: 4.4 and 4.7), on both halves of the EUR/USD sample and on six of six other pairs. Event weeks and trending years: small gains, section 3.
3. THE WIDER EVIDENCE (descriptive, pooled test added after the primary result): on the six other pairs, where nothing was selected, the chosen candidate's proper score is -1.1 %* / -2.6 %* / -5.0 %* against the bots at 5 / 21 / 63 sessions in 2010-26 and -0.8 % / -1.8 %* / -2.7 % in 2018-26 (`*` = interval excludes zero); the Garman-Klass version -2.4 %* / -2.4 %* / -4.1 %* in 2018-26. So there very probably is a small real gain in the QUALITY of the levels, two to four percent of the proper score, from letting the weight of today's volatility fall with the horizon. It is not narrower levels, and EUR/USD's own unseen years do not show it.

## 1. The plain table: every candidate on the unseen years (2018-26) and on the selection years (2010-17)

`held` = share of sessions on which the period's lowest low stayed above the lower level / highest high below the upper level [95 % Wilson interval on the number of independent periods = sessions / h]. Width = upper minus lower level in % of price, average over sessions. Proper score = pinball loss at the 20 % / 80 % quantiles, basis points, lower is better; `vs bots` = relative difference (negative = better than the bots), `*` = paired block-bootstrap 95 % interval excludes zero. All figures walk-forward, out of sample; same sessions for every candidate.

**2018-26 (never seen by the selection)**

| candidate                         |   h | lower held %   | upper held %   |   avg width % |   score bp | score vs bots   | width vs bots   |
|:----------------------------------|----:|:---------------|:---------------|--------------:|-----------:|:----------------|:----------------|
| C0 bots (baseline)                |   5 | 79.2 [75-83]   | 80.4 [77-84]   |          2.44 |      19.84 |                 |                 |
| C1 bots, sides pooled             |   5 | 79.3 [75-83]   | 80.4 [77-84]   |          2.44 |      19.81 | -0.1 %          | +0.0 %          |
| C2 one gauge, fitted slope        |   5 | 82.1 [78-85]   | 82.9 [79-86]   |          2.56 |      19.82 | -0.1 %          | +5.0 %          |
| C3 HAR daily returns <- chosen    |   5 | 81.3 [77-85]   | 82.5 [79-86]   |          2.5  |      19.81 | -0.2 %          | +2.4 %          |
| C4 HAR Garman-Klass               |   5 | 81.8 [78-85]   | 82.0 [78-85]   |          2.48 |      19.49 | -1.8 % *        | +1.7 %          |
| C5 HAR hourly realised vol        |   5 | 82.1 [78-85]   | 83.0 [79-86]   |          2.53 |      19.6  | -1.2 % *        | +3.7 %          |
| C6 HAR hourly + events            |   5 | 81.3 [77-85]   | 83.5 [80-87]   |          2.51 |      19.48 | -1.8 % *        | +3.1 %          |
| C7 quantile regression            |   5 | 82.1 [78-85]   | 83.7 [80-87]   |          2.55 |      19.69 | -0.7 %          | +4.5 %          |
| C8 quantile regr., down / up vol  |   5 | 82.0 [78-85]   | 83.9 [80-87]   |          2.55 |      19.74 | -0.5 %          | +4.7 %          |
| C9 adaptive on bots               |   5 | 79.2 [75-83]   | 80.4 [77-84]   |          2.44 |      19.84 | +0.0 %          | +0.0 %          |
| C10 adaptive on C5                |   5 | 82.1 [78-85]   | 83.0 [79-86]   |          2.53 |      19.6  | -1.2 % *        | +3.7 %          |
| C11 average C3 C4 C5 C7           |   5 | 82.0 [78-85]   | 83.0 [79-86]   |          2.51 |      19.58 | -1.3 % *        | +3.1 %          |
| (reference) no volatility scaling |   5 | 90.1 [87-92]   | 89.1 [86-92]   |          3.13 |      22.94 | +15.6 % *       | +28.5 %         |
| C0 bots (baseline)                |  21 | 78.5 [70-85]   | 82.2 [74-88]   |          4.98 |      40.25 |                 |                 |
| C1 bots, sides pooled             |  21 | 77.3 [69-84]   | 83.2 [75-89]   |          4.98 |      39.97 | -0.7 %          | -0.0 %          |
| C2 one gauge, fitted slope        |  21 | 82.0 [74-88]   | 86.0 [78-91]   |          5.28 |      39.88 | -0.9 %          | +5.8 %          |
| C3 HAR daily returns <- chosen    |  21 | 80.2 [72-87]   | 85.3 [77-91]   |          5.17 |      39.71 | -1.3 %          | +3.7 %          |
| C4 HAR Garman-Klass               |  21 | 80.4 [72-87]   | 84.9 [77-90]   |          5.2  |      39.75 | -1.2 %          | +4.4 %          |
| C5 HAR hourly realised vol        |  21 | 80.9 [72-87]   | 85.1 [77-91]   |          5.27 |      40.02 | -0.6 %          | +5.7 %          |
| C6 HAR hourly + events            |  21 | 80.5 [72-87]   | 84.9 [77-90]   |          5.22 |      39.94 | -0.8 %          | +4.7 %          |
| C7 quantile regression            |  21 | 81.7 [73-88]   | 84.8 [77-90]   |          5.3  |      40.19 | -0.1 %          | +6.3 %          |
| C8 quantile regr., down / up vol  |  21 | 81.9 [74-88]   | 84.6 [77-90]   |          5.32 |      40.4  | +0.4 %          | +6.7 %          |
| C9 adaptive on bots               |  21 | 78.5 [70-85]   | 82.2 [74-88]   |          4.98 |      40.25 | +0.0 %          | +0.0 %          |
| C10 adaptive on C5                |  21 | 80.9 [72-87]   | 85.1 [77-91]   |          5.27 |      40.02 | -0.6 %          | +5.7 %          |
| C11 average C3 C4 C5 C7           |  21 | 80.6 [72-87]   | 85.0 [77-91]   |          5.23 |      39.67 | -1.5 %          | +5.0 %          |
| (reference) no volatility scaling |  21 | 88.7 [81-93]   | 89.2 [82-94]   |          6.33 |      44.79 | +11.3 % *       | +26.9 %         |
| C0 bots (baseline)                |  63 | 80.3 [65-90]   | 79.0 [63-89]   |          9    |      68.3  |                 |                 |
| C1 bots, sides pooled             |  63 | 79.3 [63-89]   | 81.1 [65-91]   |          9.05 |      67.29 | -1.5 %          | +0.5 %          |
| C2 one gauge, fitted slope        |  63 | 85.8 [71-94]   | 86.0 [71-94]   |         10.09 |      69.32 | +1.5 %          | +12.2 %         |
| C3 HAR daily returns <- chosen    |  63 | 84.3 [69-93]   | 85.2 [70-93]   |          9.9  |      68.47 | +0.2 %          | +10.1 %         |
| C4 HAR Garman-Klass               |  63 | 83.9 [69-93]   | 86.4 [72-94]   |          9.95 |      67.87 | -0.6 %          | +10.6 %         |
| C5 HAR hourly realised vol        |  63 | 84.9 [70-93]   | 86.7 [72-94]   |         10.07 |      68.25 | -0.1 %          | +11.9 %         |
| C6 HAR hourly + events            |  63 | 82.7 [67-92]   | 84.2 [69-93]   |          9.57 |      67.45 | -1.2 %          | +6.4 %          |
| C7 quantile regression            |  63 | 86.4 [72-94]   | 85.2 [70-93]   |         10.02 |      68.99 | +1.0 %          | +11.4 %         |
| C8 quantile regr., down / up vol  |  63 | 86.1 [71-94]   | 85.0 [70-93]   |         10.2  |      70.86 | +3.8 %          | +13.4 %         |
| C9 adaptive on bots               |  63 | 80.3 [65-90]   | 79.0 [63-89]   |          9    |      68.3  | +0.0 %          | +0.0 %          |
| C10 adaptive on C5                |  63 | 84.9 [70-93]   | 86.7 [72-94]   |         10.07 |      68.25 | -0.1 %          | +11.9 %         |
| C11 average C3 C4 C5 C7           |  63 | 85.4 [70-93]   | 86.0 [71-94]   |          9.99 |      67.96 | -0.5 %          | +11.0 %         |
| (reference) no volatility scaling |  63 | 89.4 [75-96]   | 91.5 [78-97]   |         11.76 |      81.56 | +19.4 % *       | +30.7 %         |

**2010-17 (the selection era)**

| candidate                         |   h | lower held %   | upper held %   |   avg width % |   score bp | score vs bots   | width vs bots   |
|:----------------------------------|----:|:---------------|:---------------|--------------:|-----------:|:----------------|:----------------|
| C0 bots (baseline)                |   5 | 79.1 [75-83]   | 81.0 [77-84]   |          3.26 |      25.97 |                 |                 |
| C1 bots, sides pooled             |   5 | 79.3 [75-83]   | 80.9 [77-84]   |          3.27 |      25.84 | -0.5 %          | +0.0 %          |
| C2 one gauge, fitted slope        |   5 | 79.8 [76-83]   | 81.1 [77-85]   |          3.26 |      25.81 | -0.6 %          | -0.0 %          |
| C3 HAR daily returns <- chosen    |   5 | 79.7 [76-83]   | 80.8 [77-84]   |          3.23 |      25.56 | -1.6 % *        | -1.0 %          |
| C4 HAR Garman-Klass               |   5 | 79.5 [75-83]   | 81.4 [77-85]   |          3.24 |      25.6  | -1.4 % *        | -0.8 %          |
| C5 HAR hourly realised vol        |   5 | 79.3 [75-83]   | 80.7 [77-84]   |          3.25 |      25.61 | -1.4 %          | -0.6 %          |
| C6 HAR hourly + events            |   5 | 79.0 [75-83]   | 80.3 [76-84]   |          3.23 |      25.43 | -2.1 % *        | -1.1 %          |
| C7 quantile regression            |   5 | 78.7 [74-82]   | 81.5 [78-85]   |          3.27 |      25.93 | -0.2 %          | +0.0 %          |
| C8 quantile regr., down / up vol  |   5 | 78.6 [74-82]   | 81.6 [78-85]   |          3.28 |      26.03 | +0.2 %          | +0.5 %          |
| C9 adaptive on bots               |   5 | 79.1 [75-83]   | 81.0 [77-84]   |          3.26 |      25.97 | +0.0 %          | +0.0 %          |
| C10 adaptive on C5                |   5 | 79.3 [75-83]   | 80.7 [77-84]   |          3.25 |      25.61 | -1.4 %          | -0.6 %          |
| C11 average C3 C4 C5 C7           |   5 | 79.3 [75-83]   | 81.1 [77-85]   |          3.25 |      25.52 | -1.7 % *        | -0.6 %          |
| (reference) no volatility scaling |   5 | 82.4 [78-86]   | 82.7 [79-86]   |          3.46 |      27.44 | +5.7 % *        | +6.1 %          |
| C0 bots (baseline)                |  21 | 77.4 [68-85]   | 82.1 [73-88]   |          6.77 |      54.77 |                 |                 |
| C1 bots, sides pooled             |  21 | 79.4 [70-86]   | 80.8 [72-87]   |          6.77 |      53.76 | -1.8 %          | -0.1 %          |
| C2 one gauge, fitted slope        |  21 | 79.6 [71-86]   | 82.0 [73-88]   |          6.65 |      53.3  | -2.7 %          | -1.8 %          |
| C3 HAR daily returns <- chosen    |  21 | 78.6 [70-86]   | 80.4 [71-87]   |          6.53 |      53    | -3.2 % *        | -3.6 %          |
| C4 HAR Garman-Klass               |  21 | 79.2 [70-86]   | 80.6 [72-87]   |          6.58 |      53.42 | -2.5 %          | -2.8 %          |
| C5 HAR hourly realised vol        |  21 | 79.3 [70-86]   | 81.0 [72-87]   |          6.58 |      53.19 | -2.9 % *        | -2.8 %          |
| C6 HAR hourly + events            |  21 | 79.1 [70-86]   | 80.9 [72-87]   |          6.55 |      53.17 | -2.9 % *        | -3.2 %          |
| C7 quantile regression            |  21 | 74.6 [65-82]   | 82.7 [74-89]   |          6.63 |      54.41 | -0.7 %          | -2.1 %          |
| C8 quantile regr., down / up vol  |  21 | 75.6 [66-83]   | 82.7 [74-89]   |          6.69 |      54.73 | -0.1 %          | -1.2 %          |
| C9 adaptive on bots               |  21 | 77.4 [68-85]   | 82.1 [73-88]   |          6.77 |      54.77 | +0.0 %          | +0.0 %          |
| C10 adaptive on C5                |  21 | 79.8 [71-87]   | 81.5 [73-88]   |          6.74 |      53.4  | -2.5 %          | -0.5 %          |
| C11 average C3 C4 C5 C7           |  21 | 78.5 [69-85]   | 81.7 [73-88]   |          6.58 |      52.78 | -3.6 % *        | -2.8 %          |
| (reference) no volatility scaling |  21 | 79.8 [71-87]   | 84.6 [76-90]   |          6.96 |      55.85 | +2.0 %          | +2.7 %          |
| C0 bots (baseline)                |  63 | 75.5 [59-87]   | 85.8 [70-94]   |         12.34 |     103.84 |                 |                 |
| C1 bots, sides pooled             |  63 | 78.8 [62-89]   | 84.6 [69-93]   |         12.47 |      99.87 | -3.8 %          | +1.0 %          |
| C2 one gauge, fitted slope        |  63 | 78.7 [62-89]   | 84.2 [68-93]   |         12.6  |      96.45 | -7.1 %          | +2.1 %          |
| C3 HAR daily returns <- chosen    |  63 | 77.0 [60-88]   | 83.6 [68-93]   |         12.3  |      95.91 | -7.6 % *        | -0.3 %          |
| C4 HAR Garman-Klass               |  63 | 76.3 [60-88]   | 83.2 [67-92]   |         12.28 |      98.82 | -4.8 %          | -0.5 %          |
| C5 HAR hourly realised vol        |  63 | 76.9 [60-88]   | 83.1 [67-92]   |         12.35 |      98.35 | -5.3 %          | +0.0 %          |
| C6 HAR hourly + events            |  63 | 75.6 [59-87]   | 82.4 [66-92]   |         11.99 |      98.83 | -4.8 %          | -2.8 %          |
| C7 quantile regression            |  63 | 71.1 [54-84]   | 84.7 [69-93]   |         11.77 |     109.37 | +5.3 %          | -4.7 %          |
| C8 quantile regr., down / up vol  |  63 | 72.7 [56-85]   | 82.8 [67-92]   |         12.34 |     101.25 | -2.5 %          | -0.1 %          |
| C9 adaptive on bots               |  63 | 75.5 [59-87]   | 85.8 [70-94]   |         12.34 |     103.84 | +0.0 %          | +0.0 %          |
| C10 adaptive on C5                |  63 | 79.4 [63-90]   | 85.7 [70-94]   |         13.03 |      99.24 | -4.4 %          | +5.6 %          |
| C11 average C3 C4 C5 C7           |  63 | 75.8 [59-87]   | 83.8 [68-93]   |         12.18 |      99.74 | -3.9 %          | -1.4 %          |
| (reference) no volatility scaling |  63 | 76.1 [59-87]   | 87.5 [72-95]   |         13.3  |     102.9  | -0.9 %          | +7.7 %          |

**The chosen candidate against the baseline, every era** (n = independent periods)

| candidate            |   h | era     |     n | lower held %   | upper held %   |   both held % |   avg width % |   median width % |   score bp | score vs bots   | worst year: lower / upper held %   |
|:---------------------|----:|:--------|------:|:---------------|:---------------|--------------:|--------------:|-----------------:|-----------:|:----------------|:-----------------------------------|
| C0 bots (baseline)   |   5 | 2010-26 | 873.6 | 79.1 [76-82]   | 80.7 [78-83]   |          60.3 |          2.83 |             2.66 |      22.75 |                 | 71 (2014) / 69 (2020)              |
| C3 HAR daily returns |   5 | 2010-26 | 873.6 | 80.5 [78-83]   | 81.7 [79-84]   |          62.8 |          2.85 |             2.73 |      22.54 | -0.9 % *        | 73 (2010) / 72 (2020)              |
| C0 bots (baseline)   |   5 | 2016-26 | 562.4 | 80.5 [77-84]   | 79.4 [76-83]   |          60.6 |          2.52 |             2.45 |      20.33 |                 | 73 (2022) / 69 (2020)              |
| C3 HAR daily returns |   5 | 2016-26 | 562.4 | 82.3 [79-85]   | 81.4 [78-84]   |          64.3 |          2.57 |             2.53 |      20.27 | -0.3 %          | 73 (2022) / 72 (2020)              |
| C0 bots (baseline)   |   5 | 2023-26 | 199   | 81.7 [76-86]   | 80.6 [75-85]   |          62.5 |          2.4  |             2.36 |      19.08 |                 | 75 (2026) / 78 (2025)              |
| C3 HAR daily returns |   5 | 2023-26 | 199   | 83.4 [78-88]   | 83.2 [77-88]   |          66.6 |          2.46 |             2.46 |      18.99 | -0.5 %          | 77 (2026) / 80 (2025)              |
| C0 bots (baseline)   |   5 | 2010-17 | 414.8 | 79.1 [75-83]   | 81.0 [77-84]   |          60.9 |          3.26 |             3.11 |      25.97 |                 | 71 (2014) / 74 (2016)              |
| C3 HAR daily returns |   5 | 2010-17 | 414.8 | 79.7 [76-83]   | 80.8 [77-84]   |          61.5 |          3.23 |             3.13 |      25.56 | -1.6 % *        | 73 (2010) / 75 (2016)              |
| C0 bots (baseline)   |   5 | 2018-26 | 458.8 | 79.2 [75-83]   | 80.4 [77-84]   |          59.9 |          2.44 |             2.33 |      19.84 |                 | 73 (2022) / 69 (2020)              |
| C3 HAR daily returns |   5 | 2018-26 | 458.8 | 81.3 [77-85]   | 82.5 [79-86]   |          63.9 |          2.5  |             2.43 |      19.81 | -0.2 %          | 73 (2022) / 72 (2020)              |
| C0 bots (baseline)   |  21 | 2010-26 | 207.2 | 78.0 [72-83]   | 82.1 [76-87]   |          60.8 |          5.84 |             5.52 |      47.17 |                 | 58 (2014) / 63 (2017)              |
| C3 HAR daily returns |  21 | 2010-26 | 207.2 | 79.4 [73-84]   | 83.0 [77-87]   |          63   |          5.82 |             5.66 |      46.04 | -2.4 % *        | 64 (2022) / 67 (2020)              |
| C0 bots (baseline)   |  21 | 2016-26 | 133.1 | 80.3 [73-86]   | 79.9 [72-86]   |          61.2 |          5.16 |             5.03 |      40.77 |                 | 66 (2022) / 63 (2017)              |
| C3 HAR daily returns |  21 | 2016-26 | 133.1 | 81.6 [74-87]   | 82.9 [76-88]   |          65.4 |          5.31 |             5.26 |      40.02 | -1.8 % *        | 64 (2022) / 67 (2020)              |
| C0 bots (baseline)   |  21 | 2023-26 |  46.6 | 81.8 [68-90]   | 77.0 [63-87]   |          59.1 |          4.93 |             4.86 |      39.16 |                 | 70 (2026) / 68 (2023)              |
| C3 HAR daily returns |  21 | 2023-26 |  46.6 | 82.3 [69-91]   | 80.9 [67-90]   |          63.3 |          5.08 |             5.05 |      37.86 | -3.3 % *        | 70 (2026) / 72 (2023)              |
| C0 bots (baseline)   |  21 | 2010-17 |  98.8 | 77.4 [68-85]   | 82.1 [73-88]   |          60.1 |          6.77 |             6.46 |      54.77 |                 | 58 (2014) / 63 (2017)              |
| C3 HAR daily returns |  21 | 2010-17 |  98.8 | 78.6 [70-86]   | 80.4 [71-87]   |          59.6 |          6.53 |             6.36 |      53    | -3.2 % *        | 67 (2014) / 68 (2017)              |
| C0 bots (baseline)   |  21 | 2018-26 | 108.5 | 78.5 [70-85]   | 82.2 [74-88]   |          61.4 |          4.98 |             4.78 |      40.25 |                 | 66 (2022) / 66 (2020)              |
| C3 HAR daily returns |  21 | 2018-26 | 108.5 | 80.2 [72-87]   | 85.3 [77-91]   |          66.1 |          5.17 |             5.03 |      39.71 | -1.3 %          | 64 (2022) / 67 (2020)              |
| C0 bots (baseline)   |  63 | 2010-26 |  68.4 | 78.0 [67-86]   | 82.3 [72-90]   |          61.5 |         10.61 |             9.91 |      85.4  |                 | 33 (2014) / 39 (2020)              |
| C3 HAR daily returns |  63 | 2010-26 |  68.4 | 80.8 [70-88]   | 84.4 [74-91]   |          65.5 |         11.06 |            10.9  |      81.67 | -4.4 %          | 46 (2014) / 49 (2017)              |
| C0 bots (baseline)   |  63 | 2016-26 |  43.7 | 81.8 [68-91]   | 77.0 [63-87]   |          60.7 |          9.29 |             8.96 |      72.74 |                 | 53 (2022) / 39 (2020)              |
| C3 HAR daily returns |  63 | 2016-26 |  43.7 | 85.1 [72-93]   | 83.0 [69-91]   |          68.6 |         10.17 |            10.14 |      70.71 | -2.8 %          | 52 (2022) / 49 (2017)              |
| C0 bots (baseline)   |  63 | 2023-26 |  14.9 | 89.1 [65-97]   | 73.6 [48-89]   |          63.8 |          8.96 |             8.74 |      69.39 |                 | 77 (2024) / 59 (2025)              |
| C3 HAR daily returns |  63 | 2023-26 |  14.9 | 90.3 [66-98]   | 82.7 [58-94]   |          73   |          9.67 |             9.55 |      68.17 | -1.8 %          | 77 (2024) / 62 (2025)              |
| C0 bots (baseline)   |  63 | 2010-17 |  32.9 | 75.5 [59-87]   | 85.8 [70-94]   |          61.3 |         12.34 |            11.75 |     103.84 |                 | 33 (2014) / 41 (2017)              |
| C3 HAR daily returns |  63 | 2010-17 |  32.9 | 77.0 [60-88]   | 83.6 [68-93]   |          60.6 |         12.3  |            12.06 |      95.91 | -7.6 % *        | 46 (2014) / 49 (2017)              |
| C0 bots (baseline)   |  63 | 2018-26 |  35.5 | 80.3 [65-90]   | 79.0 [63-89]   |          61.6 |          9    |             8.54 |      68.3  |                 | 53 (2022) / 39 (2020)              |
| C3 HAR daily returns |  63 | 2018-26 |  35.5 | 84.3 [69-93]   | 85.2 [70-93]   |          70.2 |          9.9  |             9.66 |      68.47 | +0.2 %          | 52 (2022) / 53 (2020)              |

Selection table (2010-17, proper score relative to the bots; the rule takes the lowest mean):

| candidate                        |   h = 5 |   h = 21 |   h = 63 |   mean |
|:---------------------------------|--------:|---------:|---------:|-------:|
| C3 HAR daily returns             |   0.984 |    0.968 |    0.924 |  0.958 |
| C2 one gauge, fitted slope       |   0.994 |    0.973 |    0.929 |  0.965 |
| C6 HAR hourly + events           |   0.979 |    0.971 |    0.952 |  0.967 |
| C5 HAR hourly realised vol       |   0.986 |    0.971 |    0.947 |  0.968 |
| C11 average C3 C4 C5 C7          |   0.983 |    0.964 |    0.961 |  0.969 |
| C4 HAR Garman-Klass              |   0.986 |    0.975 |    0.952 |  0.971 |
| C10 adaptive on C5               |   0.986 |    0.975 |    0.956 |  0.972 |
| C1 bots, sides pooled            |   0.995 |    0.982 |    0.962 |  0.979 |
| C8 quantile regr., down / up vol |   1.002 |    0.999 |    0.975 |  0.992 |
| C0 bots (baseline)               |   1     |    1     |    1     |  1     |
| C9 adaptive on bots              |   1     |    1     |    1     |  1     |
| C7 quantile regression           |   0.998 |    0.993 |    1.053 |  1.015 |

Reading. On 2010-17 seven candidates are 3-4 % better than the bots and within a point and a half of each other; the rule's pick among them is close to a coin toss. On 2018-26 the same seven are 0-2 % better at 5 and 21 sessions and indistinguishable from the bots at 63. The only intervals that exclude zero in 2018-26 are at 5 sessions, for the candidates that use intraday information (Garman-Klass ranges, hourly realised volatility, the event count): about -1.2 to -1.8 %. Direct quantile regression (C7, C8) is the weakest family: more parameters fitted on overlapping windows, worse out of sample at 63 sessions. Pooling the two sides (C1) is a small free gain (-0.1 to -1.5 % in 2018-26). The adaptive correction (C9, C10) is IDENTICAL to its base: its step size is chosen each year by past proper score and the choice was always zero (section 7).

## 2. Where the levels hold: calm and volatile markets

Holding rate (%) by tercile of the 21-session volatility at the decision (cut points from the era's own sessions). `spread` = highest minus lowest tercile. Width in % of price.

| era     |   h | candidate                         | lower: calm / middle / volatile   |   spread | upper: calm / middle / volatile   |   spread  | width: calm / middle / volatile   |   periods per tercile |
|:--------|----:|:----------------------------------|:----------------------------------|---------:|:----------------------------------|----------:|:----------------------------------|----------------------:|
| 2010-17 |   5 | C0 bots (baseline)                | 76.7 / 78.9 / 81.6                |      4.9 | 76.6 / 79.6 / 86.7                |      10.1 | 2.27 / 3.14 / 4.39                |                 138.4 |
| 2010-17 |   5 | C3 HAR daily returns              | 79.0 / 79.0 / 81.0                |      2   | 79.5 / 78.7 / 84.2                |       5.5 | 2.43 / 3.12 / 4.14                |                 138.4 |
| 2010-17 |   5 | (reference) no volatility scaling | 92.1 / 84.8 / 70.5                |     21.6 | 90.2 / 83.2 / 74.8                |      15.4 | 3.48 / 3.48 / 3.44                |                 138.4 |
| 2010-17 |  21 | C0 bots (baseline)                | 73.4 / 77.4 / 81.5                |      8.1 | 75.0 / 82.6 / 88.7                |      13.7 | 4.69 / 6.52 / 9.11                |                  33   |
| 2010-17 |  21 | C3 HAR daily returns              | 76.7 / 78.4 / 80.6                |      3.9 | 77.7 / 79.7 / 83.6                |       5.9 | 5.05 / 6.35 / 8.20                |                  33   |
| 2010-17 |  21 | (reference) no volatility scaling | 87.9 / 82.3 / 69.3                |     18.5 | 89.5 / 85.4 / 78.9                |      10.6 | 6.99 / 6.98 / 6.90                |                  33   |
| 2010-17 |  63 | C0 bots (baseline)                | 69.9 / 74.8 / 81.6                |     11.7 | 78.8 / 87.1 / 91.5                |      12.7 | 8.55 / 11.87 / 16.62              |                  11   |
| 2010-17 |  63 | C3 HAR daily returns              | 74.0 / 76.7 / 80.3                |      6.3 | 83.1 / 85.2 / 82.3                |       2.9 | 9.94 / 12.12 / 14.84              |                  11   |
| 2010-17 |  63 | (reference) no volatility scaling | 83.7 / 77.1 / 67.4                |     16.2 | 91.5 / 90.6 / 80.5                |      11   | 13.35 / 13.37 / 13.17             |                  11   |
| 2018-26 |   5 | C0 bots (baseline)                | 73.1 / 81.3 / 83.1                |     10.1 | 77.1 / 81.0 / 83.1                |       6   | 1.74 / 2.34 / 3.23                |                 153   |
| 2018-26 |   5 | C3 HAR daily returns              | 78.2 / 83.0 / 82.7                |      4.8 | 82.1 / 83.0 / 82.5                |       0.9 | 1.93 / 2.45 / 3.12                |                 153   |
| 2018-26 |   5 | (reference) no volatility scaling | 94.4 / 92.4 / 83.4                |     11   | 96.3 / 89.8 / 81.0                |      15.3 | 3.13 / 3.16 / 3.11                |                 153   |
| 2018-26 |  21 | C0 bots (baseline)                | 72.1 / 78.4 / 85.0                |     12.9 | 81.2 / 79.2 / 86.2                |       7   | 3.58 / 4.78 / 6.59                |                  36.2 |
| 2018-26 |  21 | C3 HAR daily returns              | 76.7 / 80.2 / 83.7                |      7   | 88.3 / 82.7 / 85.0                |       5.5 | 4.11 / 5.08 / 6.31                |                  36.2 |
| 2018-26 |  21 | (reference) no volatility scaling | 92.6 / 90.8 / 82.6                |     10   | 95.1 / 89.1 / 83.4                |      11.7 | 6.32 / 6.37 / 6.29                |                  36.2 |
| 2018-26 |  63 | C0 bots (baseline)                | 73.9 / 83.1 / 83.9                |     10   | 75.1 / 78.4 / 83.5                |       8.4 | 6.49 / 8.57 / 11.94               |                  11.8 |
| 2018-26 |  63 | C3 HAR daily returns              | 83.2 / 88.5 / 81.3                |      7.1 | 86.6 / 85.6 / 83.5                |       3.1 | 8.22 / 9.76 / 11.73               |                  11.8 |
| 2018-26 |  63 | (reference) no volatility scaling | 95.2 / 92.1 / 80.9                |     14.2 | 99.6 / 93.4 / 81.5                |      18.1 | 11.81 / 11.85 / 11.63             |                  11.8 |

Average spread over the six cells (3 horizons x 2 levels), points:

| candidate                         |   2010-26 |   2016-26 |   2023-26 |   2010-17 |   2018-26 |
|:----------------------------------|----------:|----------:|----------:|----------:|----------:|
| C0 bots (baseline)                |       8.8 |      11.3 |      13.8 |      10.2 |       9.1 |
| C1 bots, sides pooled             |       9.2 |      11.4 |      13.3 |      10.9 |       9.1 |
| C2 one gauge, fitted slope        |       3.6 |       6   |       7.6 |       3.6 |       4.1 |
| C3 HAR daily returns              |       4.3 |       6.3 |       7.8 |       4.4 |       4.7 |
| C4 HAR Garman-Klass               |       4.4 |       7   |       7   |       4.4 |       4.8 |
| C5 HAR hourly realised vol        |       4.2 |       6.8 |       7.3 |       4   |       4.6 |
| C6 HAR hourly + events            |       4.5 |       6.7 |       7.4 |       3.7 |       4.8 |
| C7 quantile regression            |       5   |       6.3 |       7.6 |       5.3 |       5   |
| C8 quantile regr., down / up vol  |       4.9 |       6.2 |       8.1 |       5.6 |       5.2 |
| C9 adaptive on bots               |       8.8 |      11.3 |      13.8 |      10.2 |       9.1 |
| C10 adaptive on C5                |       3.7 |       6.8 |       7.3 |       4.9 |       4.6 |
| C11 average C3 C4 C5 C7           |       4.4 |       6.4 |       7.3 |       3.7 |       4.5 |
| (reference) no volatility scaling |      16.7 |      10.1 |       9.9 |      15.5 |      13.4 |

What happens: with today's volatility times a constant, the bots' level is too tight when the market is quiet (volatility drifts back up) and too wide when it is volatile. The regression gives the long-run level a weight, so in 2018-26 the chosen levels were +11 % / +15 % / +27 % wider than the bots' in the calm third and -4 % / -4 % / -2 % in the volatile third (5 / 21 / 63 sessions). The calm third's holding rate rises from 72-81 % to 77-88 %; the price is the extra width in calm markets, which in the low-volatility years since 2018 made the levels wider on average and over-reliable at 63 sessions.

What the chosen model is, in one number per horizon: the bots move their level one for one with today's volatility at every horizon. In the fitted regression the level moves by 0.84 / 0.73 / 0.60 percent for one percent of volatility at 5 / 21 / 63 sessions (sum of the slopes, fold 2026; `sharper_levels_coefs.csv`); the rest is a fixed long-run level. The 63-session volatility carries the largest weight at every horizon, the 5-session one almost none, and the 252-session one a small NEGATIVE weight, so the long-run anchor is the constant fitted on all history since 2004, which is why the levels came out too wide in the quiet years since 2018.

## 3. Event weeks, trending markets, worst years

**Weeks with a scheduled FOMC statement, ECB decision, US payrolls or US CPI inside the 5-session window** against the other weeks (holding rate %, 5 sessions; event weeks are about 59 % of all weeks):

| era     | candidate                  | lower: event week / other   | upper: event week / other   | width: event week / other   | periods: event / other   |
|:--------|:---------------------------|:----------------------------|:----------------------------|:----------------------------|:-------------------------|
| 2010-26 | C0 bots (baseline)         | 77.5 / 81.5                 | 78.3 / 84.1                 | 2.84 / 2.82                 | 517 / 357                |
| 2010-26 | C3 HAR daily returns       | 78.7 / 83.2                 | 79.5 / 85.0                 | 2.86 / 2.83                 | 517 / 357                |
| 2010-26 | C5 HAR hourly realised vol | 79.3 / 82.8                 | 79.6 / 85.3                 | 2.88 / 2.86                 | 517 / 357                |
| 2010-26 | C6 HAR hourly + events     | 79.6 / 81.0                 | 80.6 / 84.0                 | 2.93 / 2.74                 | 517 / 357                |
| 2018-26 | C0 bots (baseline)         | 78.2 / 80.4                 | 77.2 / 84.7                 | 2.42 / 2.46                 | 263 / 196                |
| 2018-26 | C3 HAR daily returns       | 80.2 / 82.8                 | 79.3 / 86.9                 | 2.48 / 2.52                 | 263 / 196                |
| 2018-26 | C5 HAR hourly realised vol | 81.1 / 83.4                 | 80.2 / 86.7                 | 2.51 / 2.55                 | 263 / 196                |
| 2018-26 | C6 HAR hourly + events     | 81.5 / 80.9                 | 81.6 / 86.0                 | 2.57 / 2.44                 | 263 / 196                |

The event effect is real and the bots ignore it: their one-week levels hold 2-8 points less often in event weeks. The chosen candidate does not use the calendar and keeps the same gap. The event candidate (C6, not chosen) makes event-week levels 5-7 % wider than the others; it closes most of the gap for the lower level and about half of it for the upper, and it had the best 5-session score of all candidates in 2018-26 (-1.8 %, interval excluding zero). At 21 and 63 sessions every window contains several events, so there is nothing to adjust.

**Trending markets.** Ex ante (tercile of the absolute 63-session move in units of its volatility at the decision; holding rate %, 2010-26):

|   h | candidate            | lower: flat / middle / trending   | upper: flat / middle / trending   |
|----:|:---------------------|:----------------------------------|:----------------------------------|
|   5 | C0 bots (baseline)   | 79.8 / 81.2 / 76.4                | 80.2 / 81.1 / 80.7                |
|   5 | C3 HAR daily returns | 81.2 / 82.6 / 77.8                | 81.9 / 82.1 / 81.1                |
|  21 | C0 bots (baseline)   | 80.2 / 79.8 / 74.0                | 78.9 / 82.2 / 85.3                |
|  21 | C3 HAR daily returns | 81.0 / 81.4 / 75.9                | 81.6 / 82.5 / 84.8                |
|  63 | C0 bots (baseline)   | 82.4 / 80.2 / 71.3                | 78.0 / 83.7 / 85.0                |
|  63 | C3 HAR daily returns | 84.5 / 82.9 / 75.0                | 83.2 / 85.3 / 84.8                |

**Worst single calendar year, 2010-26** (holding rate %, year in brackets; a year has 12 independent 21-session periods and 4 independent 63-session periods, so these are noisy):

| candidate                        | h = 5: lower / upper   | h = 21: lower / upper   | h = 63: lower / upper   |
|:---------------------------------|:-----------------------|:------------------------|:------------------------|
| C0 bots (baseline)               | 71 (2014) / 69 (2020)  | 58 (2014) / 63 (2017)   | 33 (2014) / 39 (2020)   |
| C1 bots, sides pooled            | 71 (2014) / 69 (2020)  | 61 (2014) / 65 (2017)   | 37 (2014) / 41 (2020)   |
| C2 one gauge, fitted slope       | 72 (2010) / 72 (2020)  | 66 (2022) / 67 (2020)   | 50 (2014) / 52 (2017)   |
| C3 HAR daily returns             | 73 (2010) / 72 (2020)  | 64 (2022) / 67 (2020)   | 46 (2014) / 49 (2017)   |
| C4 HAR Garman-Klass              | 70 (2010) / 75 (2017)  | 64 (2022) / 63 (2017)   | 45 (2014) / 46 (2017)   |
| C5 HAR hourly realised vol       | 71 (2010) / 73 (2020)  | 65 (2022) / 64 (2017)   | 47 (2014) / 46 (2017)   |
| C6 HAR hourly + events           | 71 (2010) / 74 (2016)  | 65 (2022) / 63 (2017)   | 45 (2014) / 45 (2017)   |
| C7 quantile regression           | 71 (2010) / 76 (2016)  | 64 (2014) / 64 (2017)   | 31 (2014) / 44 (2017)   |
| C8 quantile regr., down / up vol | 71 (2010) / 76 (2016)  | 65 (2010) / 64 (2017)   | 42 (2014) / 46 (2017)   |
| C9 adaptive on bots              | 71 (2014) / 69 (2020)  | 58 (2014) / 63 (2017)   | 33 (2014) / 39 (2020)   |
| C10 adaptive on C5               | 71 (2010) / 73 (2020)  | 65 (2022) / 64 (2017)   | 47 (2014) / 46 (2017)   |
| C11 average C3 C4 C5 C7          | 72 (2010) / 74 (2020)  | 65 (2022) / 66 (2017)   | 42 (2014) / 46 (2017)   |

A strongly trending year still breaks every method. The regression candidates are less badly broken (63 sessions: the worst year improves from 33 / 39 % to about 46 / 49 %; 21 sessions: 58 / 63 % to 64 / 67 %) mainly because two of the worst years (2014 and 2020) started from the lowest volatility of the sample, where their levels are wider (2014: 63-session lower level held 33 -> 46 %; 2020 upper 39 -> 53 %; 2017, which started from average volatility: 41 -> 49 %). That is the same effect as section 2, not a trend remedy. The remedy that was meant for trends, the adaptive correction, does repair the holding rate after the fact but costs more in width than it saves in misses (section 7).

## 4. Width at matched reliability

Declared device: each candidate's levels are rescaled, side by side, so that its model holds exactly 80 % on its own training rows; then the out-of-sample holding and width are compared (2018-26). The last column is DESCRIPTIVE and was added after the primary result: the width a candidate would need to hold exactly 80 % on each side within 2018-26 itself.

| candidate                         |   h | matched: lower / upper held %   |   matched: avg width % | matched width vs bots   | matched score vs bots   | ex-post 80 % width vs bots (descriptive)   |
|:----------------------------------|----:|:--------------------------------|-----------------------:|:------------------------|:------------------------|:-------------------------------------------|
| C0 bots (baseline)                |   5 | 78.9 / 80.6                     |                   2.44 |                         |                         |                                            |
| C1 bots, sides pooled             |   5 | 78.9 / 80.7                     |                   2.44 | +0.0 %                  | -0.0 %                  | +0.4 %                                     |
| C2 one gauge, fitted slope        |   5 | 81.8 / 83.3                     |                   2.56 | +5.1 %                  | +0.1 %                  | -2.4 %                                     |
| C3 HAR daily returns              |   5 | 81.3 / 82.5                     |                   2.5  | +2.4 %                  | -0.0 %                  | -1.9 %                                     |
| C4 HAR Garman-Klass               |   5 | 81.7 / 82.0                     |                   2.48 | +1.6 %                  | -1.6 %                  | -2.1 %                                     |
| C5 HAR hourly realised vol        |   5 | 82.1 / 83.1                     |                   2.53 | +3.7 %                  | -1.0 %                  | -1.8 %                                     |
| C6 HAR hourly + events            |   5 | 81.4 / 83.3                     |                   2.51 | +3.1 %                  | -1.7 %                  | -1.3 %                                     |
| C7 quantile regression            |   5 | 82.1 / 83.7                     |                   2.55 | +4.5 %                  | -0.6 %                  | -2.2 %                                     |
| C8 quantile regr., down / up vol  |   5 | 82.0 / 83.9                     |                   2.55 | +4.7 %                  | -0.4 %                  | -2.7 %                                     |
| C9 adaptive on bots               |   5 | 80.3 / 80.2                     |                   2.45 | +0.6 %                  | +0.2 %                  | +0.0 %                                     |
| C10 adaptive on C5                |   5 | 81.6 / 81.6                     |                   2.48 | +1.7 %                  | -1.3 %                  | -1.8 %                                     |
| C11 average C3 C4 C5 C7           |   5 | 82.0 / 83.0                     |                   2.51 | +3.1 %                  | -1.2 %                  | -2.7 %                                     |
| (reference) no volatility scaling |   5 | 90.1 / 89.1                     |                   3.13 | +28.5 %                 | +15.8 %                 | -4.3 %                                     |
| C0 bots (baseline)                |  21 | 76.1 / 84.0                     |                   4.99 |                         |                         |                                            |
| C1 bots, sides pooled             |  21 | 76.2 / 84.1                     |                   4.99 | -0.0 %                  | +0.2 %                  | -0.0 %                                     |
| C2 one gauge, fitted slope        |  21 | 80.6 / 86.5                     |                   5.27 | +5.6 %                  | -0.2 %                  | -3.2 %                                     |
| C3 HAR daily returns              |  21 | 80.2 / 85.2                     |                   5.16 | +3.5 %                  | -0.8 %                  | -2.5 %                                     |
| C4 HAR Garman-Klass               |  21 | 80.2 / 84.9                     |                   5.2  | +4.2 %                  | -0.6 %                  | -2.7 %                                     |
| C5 HAR hourly realised vol        |  21 | 80.1 / 85.4                     |                   5.27 | +5.6 %                  | +0.1 %                  | -2.3 %                                     |
| C6 HAR hourly + events            |  21 | 80.2 / 85.2                     |                   5.22 | +4.6 %                  | -0.1 %                  | -2.7 %                                     |
| C7 quantile regression            |  21 | 81.7 / 84.8                     |                   5.3  | +6.2 %                  | +0.1 %                  | -1.8 %                                     |
| C8 quantile regr., down / up vol  |  21 | 81.9 / 84.6                     |                   5.32 | +6.6 %                  | +0.6 %                  | -1.6 %                                     |
| C9 adaptive on bots               |  21 | 79.8 / 80.8                     |                   4.99 | +0.1 %                  | +0.6 %                  | +0.0 %                                     |
| C10 adaptive on C5                |  21 | 81.2 / 83.6                     |                   5.17 | +3.6 %                  | -0.1 %                  | -2.3 %                                     |
| C11 average C3 C4 C5 C7           |  21 | 80.3 / 85.2                     |                   5.23 | +4.9 %                  | -1.0 %                  | -2.4 %                                     |
| (reference) no volatility scaling |  21 | 88.7 / 89.2                     |                   6.33 | +26.8 %                 | +11.5 %                 | -2.6 %                                     |
| C0 bots (baseline)                |  63 | 78.5 / 81.8                     |                   9.18 |                         |                         |                                            |
| C1 bots, sides pooled             |  63 | 78.4 / 81.8                     |                   9.19 | +0.1 %                  | +0.0 %                  | -1.5 %                                     |
| C2 one gauge, fitted slope        |  63 | 84.8 / 86.5                     |                  10.08 | +9.8 %                  | +2.9 %                  | -4.7 %                                     |
| C3 HAR daily returns              |  63 | 85.0 / 84.6                     |                   9.91 | +7.9 %                  | +1.5 %                  | -3.5 %                                     |
| C4 HAR Garman-Klass               |  63 | 84.7 / 85.3                     |                   9.96 | +8.4 %                  | +0.8 %                  | -3.7 %                                     |
| C5 HAR hourly realised vol        |  63 | 85.1 / 86.0                     |                  10.07 | +9.7 %                  | +1.3 %                  | -4.6 %                                     |
| C6 HAR hourly + events            |  63 | 83.4 / 83.5                     |                   9.57 | +4.2 %                  | -0.0 %                  | -3.5 %                                     |
| C7 quantile regression            |  63 | 86.4 / 85.2                     |                  10.02 | +9.1 %                  | +1.9 %                  | -4.2 %                                     |
| C8 quantile regr., down / up vol  |  63 | 86.1 / 85.0                     |                  10.2  | +11.1 %                 | +4.7 %                  | -2.0 %                                     |
| C9 adaptive on bots               |  63 | 82.8 / 76.1                     |                   8.92 | -2.9 %                  | +3.3 %                  | +0.0 %                                     |
| C10 adaptive on C5                |  63 | 84.5 / 84.2                     |                   9.87 | +7.5 %                  | +1.3 %                  | -4.6 %                                     |
| C11 average C3 C4 C5 C7           |  63 | 85.7 / 85.5                     |                   9.99 | +8.8 %                  | +0.8 %                  | -4.5 %                                     |
| (reference) no volatility scaling |  63 | 89.4 / 91.5                     |                  11.76 | +28.1 %                 | +20.5 %                 | -7.9 %                                     |

Two things to read from this. First, matching reliability on the training window does not match it out of sample: the regression candidates then held 80-86 % in 2018-26 and were 2-11 % wider, the bots 76-84 %. Second, the ex-post column says the regression candidates would need 2-5 % LESS width than the bots to reach exactly 80 % in 2018-26, but the same column 'prefers' the level with no volatility scaling at all (-3 to -8 %), which is the worst level on every honest measure. Average width at a given overall holding rate rewards being tight when volatility is high and failing there; it is not a measure of quality on its own. The proper score is, and it shows no confirmed gain.

## 5. Six other pairs, nothing re-tuned

The same 100 bots' median and the chosen candidate (C3 HAR daily returns) on each pair's own sessions (arm BA's cached frames), same walk-forward. `score vs bots` per horizon (`*` = block-bootstrap interval excludes zero); a pair IMPROVES by the declared reading if the mean of the three ratios is below 1 in 2010-26. On these pairs nothing was selected, so all of 2010-26 is out of selection.

| pair    | 2010-26: score vs bots, h = 5 / 21 / 63   | improves   | 2010-26: lower / upper held % (h = 5 / 21 / 63)   | 2010-26: width vs bots   | 2010-26: tercile spread, bots -> chosen   | 2018-26: score vs bots, h = 5 / 21 / 63   | 2018-26: lower / upper held % (h = 5 / 21 / 63)   | 2018-26: width vs bots   | 2018-26: tercile spread, bots -> chosen   |
|:--------|:------------------------------------------|:-----------|:--------------------------------------------------|:-------------------------|:------------------------------------------|:------------------------------------------|:--------------------------------------------------|:-------------------------|:------------------------------------------|
| GBP/USD | -1.1 %* / -3.3 %* / -4.6 %*               | yes        | 81 / 81 ; 79 / 83 ; 76 / 84                       | -0.2 % / -1.4 % / -5.9 % | 10.0 -> 5.9                               | -1.0 % / -3.8 %* / -5.1 %                 | 81 / 81 ; 80 / 83 ; 77 / 82                       | -0.2 % / -1.5 % / -6.2 % | 12.2 -> 7.4                               |
| USD/JPY | -0.9 % / -3.3 %* / -8.1 %*                | yes        | 81 / 82 ; 82 / 81 ; 81 / 81                       | -1.0 % / +1.0 % / +3.0 % | 12.6 -> 4.4                               | -0.6 % / -1.5 % / -5.7 %                  | 81 / 82 ; 82 / 83 ; 82 / 81                       | -1.6 % / +1.7 % / +3.6 % | 13.3 -> 7.0                               |
| AUD/USD | -0.4 % / -1.5 % / -3.8 %                  | yes        | 79 / 82 ; 78 / 85 ; 78 / 86                       | +0.5 % / +0.0 % / +0.5 % | 8.5 -> 5.3                                | -0.8 % / -1.4 % / +0.2 %                  | 79 / 82 ; 78 / 84 ; 82 / 87                       | +0.2 % / -0.0 % / +4.9 % | 12.0 -> 7.8                               |
| USD/CHF | -2.4 %* / -3.2 % / -4.5 %                 | yes        | 81 / 83 ; 79 / 84 ; 79 / 85                       | -0.0 % / -2.0 % / +1.9 % | 10.1 -> 4.0                               | -1.0 % / -2.5 % / -3.4 %                  | 82 / 84 ; 82 / 85 ; 79 / 85                       | +3.2 % / +3.6 % / +8.4 % | 14.0 -> 6.7                               |
| USD/CAD | -0.9 %* / -3.3 %* / -7.5 %*               | yes        | 83 / 78 ; 84 / 77 ; 90 / 78                       | -0.2 % / +0.7 % / +3.8 % | 10.6 -> 5.1                               | -0.6 % / -1.1 % / -1.2 %                  | 83 / 79 ; 84 / 78 ; 90 / 83                       | +0.2 % / +1.3 % / +7.8 % | 13.0 -> 7.2                               |
| NZD/USD | -0.7 %* / -1.3 % / -1.4 %                 | yes        | 80 / 82 ; 80 / 84 ; 83 / 89                       | +0.5 % / +1.3 % / +4.2 % | 12.1 -> 5.8                               | -0.9 %* / -0.4 % / -1.2 %                 | 80 / 82 ; 80 / 85 ; 83 / 87                       | +0.1 % / +0.3 % / +3.2 % | 12.9 -> 7.0                               |

**6 of 6 pairs improve** by the declared reading (2010-26). The interval excludes zero in 10 of 18 pair-horizons in 2010-26 and in 2 of 18 in 2018-26. The holding rate is more even across volatility terciles on 6 of 6 pairs in 2010-26 and 6 of 6 in 2018-26.

Descriptive, added after the primary result: the six pairs pooled into one test (each pair's loss difference divided by its bots' mean loss, averaged across pairs by date, one block bootstrap):

| candidate                  | 2010-26: h = 5 / 21 / 63    | 2010-17: h = 5 / 21 / 63    | 2018-26: h = 5 / 21 / 63    |
|:---------------------------|:----------------------------|:----------------------------|:----------------------------|
| C3 HAR daily returns       | -1.1 %* / -2.6 %* / -5.0 %* | -1.2 %* / -3.4 %* / -6.7 %* | -0.8 % / -1.8 %* / -2.7 %   |
| C4 HAR Garman-Klass        | -2.3 %* / -3.0 %* / -5.8 %* | -2.2 %* / -3.5 %* / -6.9 %* | -2.4 %* / -2.4 %* / -4.1 %* |
| C5 HAR hourly realised vol | -2.1 %* / -2.8 %* / -5.7 %* | -2.0 %* / -3.2 %* / -6.8 %* | -2.2 %* / -2.4 %* / -4.0 %* |
| C1 bots, sides pooled      | -0.1 % / -0.7 %* / -2.1 %*  | -0.2 % / -1.2 %* / -3.1 %*  | +0.0 % / -0.1 % / -0.8 %    |
| C7 quantile regression     | -1.3 %* / -1.3 % / -2.7 %   | -0.8 % / -0.0 % / -1.8 %    | -1.9 %* / -2.9 %* / -3.4 %  |
| C9 adaptive on bots        | +0.0 % / +0.5 %* / +1.5 %*  | +0.0 % / +0.9 %* / +2.8 %*  | +0.0 % / +0.0 % / +0.0 %    |

So across the other pairs the regression levels score better than the bots' in both halves. For the chosen candidate in 2018-26: -0.8 % [-1.6 .. +0.0] / -1.8 % [-3.3 .. -0.3] / -2.7 % [-6.3 .. +0.8] at 5 / 21 / 63 sessions; for the versions fed with intraday ranges (C4, C5) the interval excludes zero at all three horizons. The gain is two to four percent of the score: visible in the pooled data, too small to see on one pair in nine years, and it is NOT narrower levels (the widths are within a few percent of the bots' in either direction). This pooled test was not declared and eleven candidates were looked at, so it is supporting evidence, not a pass. EUR/USD 2018-26 is the weakest of the seven cases, the opposite of the usual pattern in this project. The adaptive correction (C9), which the yearly rule switched on at times on AUD, GBP, CAD and JPY, made the pooled score worse: +0.0 % / +0.9 %* / +2.8 %* in 2010-17.

## 6. Controls

* **Shuffled order** (sessions of 2003-26 permuted, each keeps its own return, high, low and realised variance; frame rebuilt; 10 draws; score relative to the level with no volatility scaling, mean of the three horizons, 2010-26). Real order: bots 0.926, chosen 0.903. Shuffled: bots 1.044 (1.031-1.063), chosen 0.995 (0.989-1.001). With the volatility information destroyed the advantage is gone: the regression learns that the gauges say nothing and falls back to the unscaled level; the bots, which must scale by a gauge that is now noise, become 3-6 % worse than no scaling.
* **No future data.** For 40 random sessions of 2010-26 the hourly bars and the daily frame were cut off at that session's close, the frame rebuilt from scratch (`bots.build` and this module) and the levels of the bots, the chosen candidate and `levels()` recomputed: 600 levels, largest difference from the full run 1.9e-16 in log distance.
* **Reconciliation (step 1).** My scoring of the bots' median level reproduces all 30 rows of `bots_levels.csv` (holding rates, widths, worst years, volatility halves); largest difference 2e-15. The generic frame used for the other pairs reproduces `bots.build()`'s targets and gauges on EUR/USD exactly except in the first 63 sessions of 2003 (the product's frame reaches back to 1999 closes there); the baseline's scores differ by at most 0.15 bp between the two frames.
* **February-July 2023 data hole** (44 % of the 2023 sessions have fewer than 20 hourly bars; highs and lows are understated for every candidate alike). Without decision sessions whose last 21 sessions or forward window touch a thin session, the chosen candidate's score against the bots in 2018-26 is -0.1 % / -1.1 % / -0.5 % (all sessions: -0.2 % / -1.3 % / +0.2 %). The sign at 63 sessions depends on the hole; the size is nil either way.

## 7. The adaptive (conformal-style) correction: why C9 equals C0

Descriptive: the correction on the bots' level at each fixed step size (the declared rule chooses among these each year by past proper score; on EUR/USD it chose 0 in every year from 2010, at every horizon, so C9 = C0 and C10 = C5 exactly).

|   h |   step gamma0 | 2010-26: lower / upper held %   | 2010-26: width vs none   | 2010-26: score vs none   | 2010-26: worst year lower / upper %   | 2018-26: lower / upper held %   | 2018-26: width vs none   | 2018-26: score vs none   | 2018-26: worst year lower / upper %   |
|----:|--------------:|:--------------------------------|:-------------------------|:-------------------------|:--------------------------------------|:--------------------------------|:-------------------------|:-------------------------|:--------------------------------------|
|   5 |          0    | 79.1 / 80.7                     | +0.0 %                   | +0.0 %                   | 71 / 69                               | 79.2 / 80.4                     | +0.0 %                   | +0.0 %                   | 73 / 69                               |
|   5 |          0.1  | 79.9 / 79.9                     | +1.6 %                   | +2.1 %                   | 74 / 73                               | 79.1 / 80.6                     | +1.7 %                   | +2.2 %                   | 74 / 75                               |
|   5 |          0.25 | 79.9 / 79.9                     | +4.6 %                   | +4.8 %                   | 77 / 75                               | 79.4 / 80.3                     | +4.5 %                   | +5.1 %                   | 77 / 77                               |
|   5 |          0.5  | 79.9 / 79.9                     | +8.8 %                   | +10.4 %                  | 78 / 77                               | 79.6 / 80.1                     | +10.3 %                  | +11.1 %                  | 78 / 78                               |
|   5 |          1    | 80.0 / 79.9                     | +20.4 %                  | +24.6 %                  | 78 / 78                               | 79.9 / 80.1                     | +23.4 %                  | +25.7 %                  | 78 / 78                               |
|  21 |          0    | 78.0 / 82.1                     | +0.0 %                   | +0.0 %                   | 58 / 63                               | 78.5 / 82.2                     | +0.0 %                   | +0.0 %                   | 66 / 66                               |
|  21 |          0.1  | 80.1 / 79.9                     | +1.7 %                   | +2.5 %                   | 61 / 63                               | 78.5 / 81.1                     | +1.4 %                   | +2.9 %                   | 65 / 66                               |
|  21 |          0.25 | 79.9 / 79.7                     | +3.2 %                   | +4.8 %                   | 63 / 67                               | 78.2 / 81.0                     | +4.3 %                   | +5.5 %                   | 65 / 67                               |
|  21 |          0.5  | 79.7 / 79.8                     | +8.4 %                   | +10.0 %                  | 65 / 70                               | 78.5 / 80.9                     | +11.0 %                  | +10.3 %                  | 66 / 73                               |
|  21 |          1    | 79.8 / 79.8                     | +19.0 %                  | +20.3 %                  | 70 / 70                               | 79.0 / 80.6                     | +21.4 %                  | +20.1 %                  | 72 / 75                               |
|  63 |          0    | 78.0 / 82.3                     | +0.0 %                   | +0.0 %                   | 33 / 39                               | 80.3 / 79.0                     | +0.0 %                   | +0.0 %                   | 53 / 39                               |
|  63 |          0.1  | 80.5 / 79.0                     | +0.8 %                   | +2.3 %                   | 36 / 35                               | 82.6 / 77.5                     | +1.9 %                   | +3.1 %                   | 58 / 38                               |
|  63 |          0.25 | 81.0 / 78.2                     | +3.4 %                   | +6.1 %                   | 36 / 35                               | 81.6 / 80.0                     | +6.9 %                   | +6.2 %                   | 53 / 45                               |
|  63 |          0.5  | 81.0 / 78.2                     | +8.8 %                   | +14.4 %                  | 36 / 37                               | 80.4 / 81.7                     | +10.4 %                  | +11.4 %                  | 57 / 58                               |
|  63 |          1    | 81.1 / 79.1                     | +17.0 %                  | +23.1 %                  | 41 / 56                               | 79.6 / 81.5                     | +11.4 %                  | +17.7 %                  | 63 / 67                               |

The correction does what it promises for the average: both levels end within a point or two of 80 % and the worst year is less bad (21 sessions: 58 / 63 % to 70 / 70 % at the largest step). But it buys that with width: levels -0 to +23 % wider and a proper score +2 to +27 % WORSE, at every step size, every horizon and in both halves of the sample. A broken level says little about whether the next one will break; widening after misses mostly widens after the move is over. As a remedy for trending years it fails the honest test.

## 8. Candidate count: 12

C0 bots (baseline) | C1 bots, sides pooled | C2 one gauge with fitted slope | C3 HAR daily returns (chosen) | C4 HAR Garman-Klass | C5 HAR hourly realised volatility | C6 C5 + scheduled events | C7 direct quantile regression | C8 quantile regression with down / up semi-volatility | C9 adaptive on C0 | C10 adaptive on C5 | C11 average of C3, C4, C5, C7. Not candidates: the unscaled reference, the matched-reliability rescale (declared device), the controls. Descriptive and added after the primary result, labelled so where they appear: the bar applied to the non-chosen candidates, the ex-post 80 % width, the fixed step sizes of the adaptive correction, the pooled six-pair test, the other candidates on the six pairs.

## 9. Anything suspicious

* **The pick is noisy.** Seven candidates were within one point of each other on 2010-17. The rule picked the plainest HAR (daily returns); on 2018-26 the Garman-Klass and event versions did better at 5 sessions. Re-picking by the 2018-26 score would be hindsight and I have not done it.
* **Clause (iii) of my bar is tight** (an exactly calibrated method passes 16-19 % of the time). It is reported as declared. It is not what decides the verdict: clauses (i) and (ii) fail on their own.
* **The pooled six-pair test is post hoc.** It was added after the EUR/USD result and eleven candidates were looked at on the pairs. Its strength is consistency (every regression candidate, every horizon, both halves, six of six pairs), not a p-value. The six pairs share the dollar and the same calendar years, so they are far from six independent confirmations.
* **Why the regression levels were over-wide in 2018-26.** Their constants and long-run anchor come from an expanding window that starts in 2004 and contains 2008-12; volatility since 2018 has been lower than that history, so shrinking towards the long-run level over-shoots (63 sessions: 84-85 % held). Two thirds of the bots forget after 5 or 10 years and do not have this problem. A rolling window is the obvious next variant; it is NOT tested here (it would be a thirteenth candidate chosen after seeing the result).
* **Average width is not a quality measure** (section 4): the unscaled level looks 'narrowest at 80 %' ex post. Any claim of 'x % narrower at the same reliability' made from average width should be distrusted, this report's included; the proper score is the test.
* **The yearly holding rates swing between 33 % and 100 %** for every method at 63 sessions (`sharper_levels_years.csv`). 2018-26 has 35 independent 63-session periods; nothing at that horizon can be confirmed or refuted on one pair in nine years.
* **Event calendar.** The FOMC file lists some two-day meetings twice (rows within two days dropped; 2015, 2024 and 2025 still show one to three extra dates); payroll dates before 2010 are a first-Friday rule; CPI dates do not exist before 2010 and are not in the regression. The event result of section 3 rests on 2010-26 dates, which are clean.
* **Data hole 2023** and bid-quote ranges: as in arm BA; they affect every candidate alike (section 6).
* On EUR/USD the product's own frame was used (gauges reach back to 1999 closes); on the other pairs the gauges start in 2003. Difference on EUR/USD: at most 0.15 bp of score.

## 10. What a user gains

**No method makes the levels narrower at the same 80 % reliability by a margin that survives the unseen years.** On EUR/USD 2018-26 the chosen levels were +2 / +4 / +10 % wider at one week / one month / three months, held a few points more often than 80 %, and scored within one and a half percent of the bots' levels, not distinguishable from zero. By the declared bar the bots' median level stays the product.

What a user could gain, if the owner wants it, is EVENNESS rather than narrowness, and that part held in both halves of the sample and on all six other pairs: in calm markets (lowest third of volatility, 2010-26) the bots' one-month levels held 71 / 81 % and in volatile markets 81 / 87 %; the regression levels held 76 / 86 % and 80 / 83 %. They do it by being 10-23 % wider when the market is quiet and 5-8 % narrower when it is volatile, and on the six other pairs that re-allocation is worth two to four percent of the proper score (descriptive). If the owner wants that, the honest way in is a shadow run: publish `sharper_levels.levels()` next to the bots' levels in the paper forward test and score both; the history has no unseen years left to confirm it on.

Two caveats belong on the product's levels as they are: (a) 'holds 8 times in 10' is an average; in a quiet market it is nearer 7.5 in 10 and in a volatile one 8.5 in 10; (b) one-week levels hold 2-8 points less often in a week with a Fed or ECB decision, payrolls or CPI. A strongly trending year breaks every version (a three-month level held 33-49 % in the worst year), and widening after misses does not help.
