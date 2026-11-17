# Arm AA (`pre_euro`): the positioning rule on the Deutsche Mark, 1987-1998 (out-of-time replication)

Code `src/eurusd/arms/pre_euro.py` (`run()`; `python -m eurusd.arms.pre_euro build` re-downloads and re-parses the
data). Results `experiments/results/arms/pre_euro_*.csv` and `pre_euro_positions.parquet`; log `logs/pre_euro.log`.
Run on 2026-11-17. Not committed by me (see "Anything suspicious", item 9).

## Verdict

**CLEAN FAIL against the bar declared before any outcome was computed.**

The identical rule, long the (synthetic) euro when the 52-week z-score of CFTC non-commercial net position / open
interest in Deutsche Mark futures is positive and short when it is negative, was right

| horizon | accuracy | independent decisions (per year) | Wilson 95 % | always long | random timing, mean (95 % band) | p (random >= rule) |
|---|---|---|---|---|---|---|
| 21 sessions | **47.6 %** | 141 (11.9) | 39.5-55.7 | 51.5 | 49.7 (44.1-56.2) | 0.77 |
| 42 sessions | **47.5 %** | 70 (5.9) | 35.9-58.7 | 49.8 | 49.7 (42.9-56.8) | 0.72 |
| 63 sessions | **45.0 %** | 46 (4.0) | 32.2-59.8 | 51.3 | 49.3 (42.4-55.4) | 0.86 |

on 1987-02-17 .. 1998-12-31. Bar: above 55 % at 42 sessions with 21 and 63 sessions above 50 %. All three horizons are
below 50 %, so the pre-agreed wording is "clean fail" (42-session accuracy at or below 50 %). As a daily stream
(position = sign of z every session, 1.2 pips per unit turnover) the rule's net Sharpe was **+0.03** (t 0.1) over
11.9 years; +0.07 in 1987-92, -0.01 in 1993-98.

What else the arm found, in five lines:

1. **The fail is not an artefact.** Same answer with one more week of delay (46.3 / 46.6 / 43.1 %), with an
   infeasibly early lag (46.4 / 46.1 / 46.7 %), and on an independent month-end price (47.2 / 51.1 / 48.2 % at 1 / 2 /
   3 months). A look-ahead copy of the signal scores 73.6 / 63.6 / 59.0 %, so the pipeline sees information when it
   is there and the orientation is right. An independent re-computation reproduces 47.6 / 47.5 / 45.0 exactly.
2. **The agreement-style rule fails too**: 48.3 / 45.2 / 42.0 % on 74 / 36 / 24 independent calls. The stand-ins are
   not to blame: the same degraded rule rebuilt on EUR/USD 2010-26 scores 60.3 / 65.7 / 68.3 %, as good as the
   original (58.3 / 63.3 / 66.7 %).
3. **Positioning-following did not work in that era on other currencies either**: JPY, GBP, CHF and CAD average
   48.7 / 50.3 / 49.8 %; none passes the bar; the equal-risk basket's Sharpe is +0.18 (t 0.6).
4. **The mark era differs from 2010-26 at about the 5-10 % level per horizon** (47.6 vs 58.3 %, z 2.0; 47.5 vs
   60.4 %, z 1.7; 45.0 vs 63.1 %, z 1.9). It does not differ from EUR/USD 2000-09 (54.9 / 53.2 / 55.2 %).
5. **Planning Sharpe.** Outside the window on which the rule was selected (2003-2022) there are now 18.7 years of
   record, the mark 1987-98 plus EUR/USD 2000-02 and 2023-26, and their pooled net Sharpe is **+0.10** (t 0.4; 95 %
   range -0.35 to +0.55). The current planning range of 0.3-0.5 is not supported by anything out of selection; its
   upper end is rejected one-sided at about the 5 % level. My reading: plan positioning-driven calls at **0.1-0.3
   (centre 0.2)**. Detail in the last section.

## Key table

Cells: accuracy % (independent decisions; Wilson 95 %). Phase-averaged non-overlapping scoring, identical to
`experiments/70_committee.py acc_row`. Random timing = the same calls shifted circularly against the outcomes by a
random offset of at least 126 sessions, 1,000 draws; p = share of draws at least as accurate as the rule.

| rule | era | 21 sessions | 42 sessions | 63 sessions | decisions / yr (21 / 42 / 63) | always long % | random timing: mean % / p, at 21, 42, 63 |
|---|---|---|---|---|---|---|---|
| **1 PRIMARY sign(z52), DEM futures, synthetic euro** | **1987-98** | **47.6** (141; 39-56) | **47.5** (70; 36-59) | **45.0** (46; 32-60) | 11.9 / 5.9 / 4.0 | 52 / 50 / 51 | 49.7 / p 0.77 ; 49.7 / p 0.72 ; 49.3 / p 0.86 |
| same, twice-monthly reports | 1987-92 | **51.0** (70; 40-63) | **50.8** (35; 36-67) | **48.1** (24; 29-67) | 11.7 / 5.9 / 3.9 | 54 / 54 / 56 | 49.6 / p 0.34 ; 49.4 / p 0.37 ; 49.0 / p 0.53 |
| same, weekly reports | 1993-98 | **44.2** (71; 33-55) | **44.2** (35; 28-59) | **41.8** (23; 26-63) | 12.0 / 6.0 / 4.0 | 49 / 45 / 47 | 49.7 / p 0.91 ; 49.3 / p 0.87 ; 49.1 / p 0.96 |
| sign(z52), EUR futures, EUR/USD (reference) | 2000-09 | **54.9** (123; 46-64) | **53.2** (62; 41-65) | **55.2** (41; 41-70) | 12.3 / 6.2 / 4.1 | 54 / 58 / 60 | 50.2 / p 0.07 ; 50.4 / p 0.26 ; 50.4 / p 0.17 |
| sign(z52), EUR futures, EUR/USD (reference) | 2010-26 | **58.3** (207; 52-65) | **60.4** (103; 51-69) | **63.1** (68; 51-74) | 12.4 / 6.2 / 4.1 | 48 / 47 / 47 | 49.4 / p 0.00 ; 49.4 / p 0.00 ; 49.0 / p 0.00 |
| sign(z52), EUR futures, EUR/USD (reference) | 2016-26 | **56.2** (133; 48-65) | **58.4** (66; 47-70) | **63.8** (44; 49-76) | 12.4 / 6.2 / 4.1 | 49 / 47 / 47 | 49.3 / p 0.05 ; 48.7 / p 0.06 ; 48.4 / p 0.03 |
| sign(z52), EUR futures, EUR/USD (reference) | 2023-26 | **49.6** (47; 35-63) | **47.6** (23; 29-67) | **54.2** (15; 30-75) | 12.4 / 6.2 / 4.1 | 51 / 51 / 54 | 49.1 / p 0.39 ; 49.5 / p 0.49 ; 49.3 / p 0.17 |

The EUR/USD rows are the known rule in this arm's layout (feature-store closes from 2003, H.10 before), not new
candidates. Shuffled-outcome control (evaluation 10; the era's daily returns re-ordered, 500 paths, rule unchanged):
mean 50.0 % at every horizon, 95 % band 44.4-55.9 / 43.3-57.0 / 42.2-57.9 at 21 / 42 / 63 sessions. The primary
result sits inside that band: indistinguishable from a coin, on the low side.

## Daily-stream Sharpe (position = sign(z52) every session, 1.2 pips per unit turnover, net)

| sample | era | years | Sharpe (t) | Sharpe from 21-session blocks | turnover / yr | % of sessions long |
|---|---|---|---|---|---|---|
| **mark, synthetic euro** | **1987-98** | 11.9 | **+0.03 (0.1)** | +0.04 | 14.6 | 48 |
| mark | 1987-92 | 5.9 | +0.07 (0.2) | +0.03 | 12.8 | 47 |
| mark | 1993-98 | 6.0 | -0.01 (-0.0) | +0.00 | 16.4 | 49 |
| EUR/USD H.10, research log | 2000-02 | 3.0 | +0.15 (0.3) | | | |
| EUR/USD H.10, research log | 2003-09 | 7.0 | +0.38 | | | |
| EUR/USD H.10, research log | 2010-15 / 2016-22 | 6.0 / 6.9 | +0.82 / +0.83 | | | |
| EUR/USD H.10, research log | 2023-26 | 3.8 | +0.36 (0.7) | | | |

The synthetic euro's DAILY returns carry bridge noise (daily correlation with the true series 0.91 in 1999-2001), which
inflates daily volatility; the Sharpe from 21-session blocks (averaged over the 21 phases) does not have that problem
and says the same: +0.04. The standard error of an 11.9-year Sharpe is 0.29, so the 95 % range of the mark-era figure
is about -0.54 to +0.60.

## Data provenance

| data | source, fetched 2026-11-17 | span | notes |
|---|---|---|---|
| CFTC legacy futures-only | `https://www.cftc.gov/files/dea/history/deacot1986_2016.zip` with `curl -A "Mozilla/5.0"`; HTTP 200, 22,917,634 bytes, sha256 `e9221f0f...84791`; one member `FUT86_16.txt`, 146,677 rows, all contracts | 1986-01-15 .. 2016-12-27 | saved in `data/raw/cftc/` (git-ignored) |
| `data/macro/pre_euro_cot_dem.csv` | code 094741, "GERMAN DEUTSCHE MARK - INTERNATIONAL MONETARY MARKET" to 1993-01-19, "DEUTSCHE MARK - ..." after | 1986-01-15 .. 2000-03-07, 550 reports | 162 twice-monthly reports to 1992-09-30, then weekly Tuesdays (327 to end-1998, largest gap 8 days) |
| `pre_euro_cot_{jpy,chf,cad}.csv` | 097741, 092741, 090741 (IMM) | 1986-01-15 .. 1999-12-28, 541 reports each | same calendar as the mark |
| `pre_euro_cot_gbp.csv` | 096741 (25,000-pound contract, to 1988-05-31) + 096742 (62,500-pound, from 1988-04-29), added in pounds of notional on the 3 dates both are listed (1988-04-29, 05-13, 05-31) | 1986-01-15 .. 1999-12-28 | |
| `pre_euro_fred_CCUSSP01DEM650N.csv` | FRED (OECD), end-of-month spot, USD per euro-equivalent of the mark; `curl --http1.1` | 1960-01 .. 2023-12 | independent month-end check of the synthetic euro only |
| price of the mark | `swing.load_prices()`: 1.95583 / (DKK per USD daily H.10 x monthly DEM/DKK from FRED EXGEUS / EXDNUS) | 1975-01-02 .. 1998-12-31 | noon New York fix, close only |
| prices of JPY, GBP, CHF, CAD | repo `data/macro/fred_DEX{JPUS,USUK,SZUS,CAUS}.csv` (H.10 noon), as USD per unit of foreign currency | 1971+ | |
| rates for the stand-in | repo `fred_IR3TIB01DEM156N`, `fred_IRLTLT01DEM156N` (monthly averages), `fred_DGS2` (daily, averaged by month) | 1976-06+ | |

Checks on the CFTC file: long + spreading + commercial + non-reportable equals open interest on every row of every
series; the archive's 1999-2016 rows equal the repo's per-year parse row for row (EUR, JPY, GBP, CAD 939 rows, CHF 937,
largest difference 0); between-report changes of net / open interest correlate +0.45 to +0.58 with the currency's
return over the same interval in 1986-98 (speculators chase the price, and the orientation is right).

**Publication lag assumed.** The CFTC's own history page
(`cftc.gov/MarketReports/CommitmentsofTraders/AbouttheCOTReports`, read 2026-11-17) says: monthly end-of-month reports
published on the 11th or 12th calendar day of the following month; mid-month and month-end reports from 1990,
published on the sixth business day after the as-of date; a report every two weeks from 1992, published on the third
business day; weekly from 2000. The file nevertheless holds mid-month figures from 1986 and weekly figures from
1992-10-06. Which of these were public when is not recorded in the file, so every case is resolved against the rule:

| as-of date | treated as public from | then |
|---|---|---|
| before 1990 | the 13th of the month after the as-of month, for the month-end AND the mid-month figure | + one calendar day, as every series in the project |
| 1990-01 .. 1992-09 | as-of + 11 days | same |
| 1992-10 .. 1992-12 | as-of + 17 days (off-week of a fortnightly release, six-business-day rule) | same |
| 1993 .. 1998 | as-of + 13 days (off-week figure is released on the Friday of the following week; + 13 is the Monday after) | same |

**52-week z on twice-monthly data.** The project's `cot_z52` is `rolling(52)` reports. Here the window is 364 days of
time (24 reports while they were twice-monthly, 52 when weekly), first value at the 1987-01-15 report, public
1987-02-13, first decision 1987-02-17. So the usable span is **1987-02-17 .. 1998-12-31**, not 1986: the first year is
consumed by the z-score. Outcomes never cross into 1999.

**A better daily DEM/USD source: none reachable.** FRED returns 404 for `DEXGEUS` and for the other legacy daily
series tried (`DEXNEUS`, `DEXAUUS`, `DEXBEUS`, `DEXFRUS`, `DEXITUS`). The session proxy refuses
`www.federalreserve.gov` (H.10 history files), `stats.bis.org`, `alfred.stlouisfed.org` and
`api.statistiken.bundesbank.de` with HTTP 403; `stooq.com` reset the connection; the ECB data API has no DEM/USD series
and no German benchmark yields before 1999. None of these was worked around. The DKK-bridge synthetic euro stays the
price, with the check below.

**Is the synthetic euro trustworthy at 21 sessions and longer in this period?** Two checks
(`pre_euro_price_check.csv`):

| check | period | horizon | n | correlation of returns | same sign | sd of the return difference | sd of the true return |
|---|---|---|---|---|---|---|---|
| month-end synthetic vs OECD end-of-month spot | 1986-98 | 1 / 2 / 3 months | 155 / 154 / 153 | 0.969 / 0.988 / 0.992 | 91.6 / 96.1 / 94.1 % | 0.82 / 0.73 / 0.74 % | 3.3 / 4.7 / 5.9 % |
| same | 1992-93 (ERM crises) | 1 / 2 / 3 months | 23 / 22 / 21 | 0.950 / 0.990 / 0.990 | 91.3 / 86.4 / 95.2 % | 1.09 / 0.85 / 1.03 % | 3.5 / 5.9 / 7.2 % |
| same | 1994-98 | 1 / 2 / 3 months | 59 / 58 / 57 | 0.972 / 0.984 / 0.991 | 94.9 / 100 / 91.2 % | 0.62 / 0.69 / 0.60 % | 2.5 / 3.7 / 4.5 % |
| same construction on 1999-2001 vs the true euro (swing's method) | 1999-01 .. 2001-11 | 1 / 21 / 42 / 63 sessions | 733 / 713 / 692 / 671 | 0.906 / 0.995 / 0.997 / 0.998 | 95.0 / 99.4 / 99.1 / 99.6 % | 0.31 % at every horizon | 0.67 / 3.0 / 4.3 / 5.2 % |

The level error against the OECD series has an sd of 0.53 % (0.69 % in 1992-93) and no drift (mean gap -0.01 %); part
of it is the different time of day of the two fixes. It is larger than in 1999-2001 (0.22 %) because the krone moved
inside a wider band before 1999. Consequence: 4-8 % of the multi-week labels may carry the wrong sign. Random label
flips of that size pull any accuracy towards 50 % by at most a sixth of its distance from 50 %: a true 58 % would have
read about 57 %. They cannot produce 47.6 %. Direct confirmation (post-hoc evaluation 14): the rule scored at
month-ends on the OECD price is right 47.2 / 51.1 / 48.2 % at 1 / 2 / 3 months (142 / 70.5 / 46.3 independent
decisions; Wilson 39-55, 40-63, 34-62) against 48.6 / 52.5 / 45.0 % on the synthetic euro at the same month-ends.

## Reconciliation (done before the new period was touched)

| known number | published | this module |
|---|---|---|
| agreement rule, 21 / 42 / 63 sessions, 2010-26 (`committee._fold_columns`) | 58.3 / 63.3 / 66.7 % | 58.29 / 63.26 / 66.68 %, equal to `committee_benchmark.csv` to 1e-16 in all nine era x horizon cells |
| positioning stream Sharpe on H.10, 2000-02 / 2003-09 / 2010-15 / 2016-22 / 2023-26 (`arm_regime_dependence.md`), with this module's lag and stream functions and the project's rolling(52) z | +0.15 / +0.38 / +0.82 / +0.83 / +0.36 | +0.153 / +0.375 / +0.821 / +0.834 / +0.364 |
| the same with this module's time-window z | | +0.063 / +0.375 / +0.821 / +0.834 / +0.364 |
| time-window z vs rolling(52) z, sign on 1,403 weekly EUR reports | | equal on 1,402 (correlation 0.999998) |

The one differing report is 2001-12-21 (an extra Friday report before a missing week; z +0.009 with one window, -0.030
with the other). It flips the position for two and a half weeks and moves the three-year 2000-02 Sharpe from +0.15 to
+0.06. The scoring code is proven; the episode also shows how little a three-year Sharpe means.

## Secondary (a): the agreement-style rule on the mark

Declared stand-ins (docstring, before any outcome):
* **Rate-spread trend.** Sign of the one-month change of [0.5 x German 3-month interbank + 0.5 x German 10-year] minus
  the US 2-year, monthly averages, known from the first day of the following month, then one day's lag. Chosen on rate
  data only: in 2004-26 its monthly change has the sign of the true 2-year spread's monthly change in 83 % of months
  (correlation 0.79; symmetric blend 77 %, 3-month only 69 %, 10-year only 75 %). On the daily grid its sign equals the
  sign of the original `d_spread2y_20` on only 60 % of sessions in 2010-26: it is a slower, staler object.
* **Macro score.** The house score's last walk-forward fold (weights and scalers fitted on EUR/USD rows whose label
  was known before 2026-01-01; no 1987-98 label enters) applied to the 9 of 14 signals that exist for the whole span:
  cot, spread (the stand-in), mom21, mom63, mom252, usdmom, tom, season, dow. They carry 60 % of the fold's weight.
  **Missing (40 % of the weight): eqrel 17.3 %, fomc 12.0 %, gap 6.9 %, fv 3.8 %, vix 0.1 %.**

| rule | era | 21 sessions | 42 sessions | 63 sessions | decisions / yr (21 / 42 / 63) | random timing: mean % / p, at 21, 42, 63 |
|---|---|---|---|---|---|---|
| **2 agreement-style, mark** | **1987-98** | **48.3** (74; 38-60) | **45.2** (36; 30-60) | **42.0** (24; 24-61) | 6.2 / 3.1 / 2.0 | 49.4 / p 0.58 ; 49.7 / p 0.80 ; 49.0 / p 0.89 |
| same | 1987-92 | **59.7** (32; 42-74) | **56.4** (16; 33-77) | **49.5** (11; 21-72) | 5.3 / 2.6 / 1.8 | 49.6 / p 0.08 ; 49.3 / p 0.26 ; 48.7 / p 0.49 |
| same | 1993-98 | **39.6** (42; 27-56) | **36.6** (20; 18-57) | **36.0** (13; 18-64) | 7.1 / 3.5 / 2.3 | 49.7 / p 0.96 ; 50.2 / p 0.99 ; 49.8 / p 1.00 |
| 11 non-positioning legs agree (rate stand-in + macro subset without cot), mark | 1987-98 | **49.2** (96; 39-59) | **46.6** (47; 33-61) | **42.9** (31; 26-59) | 8.0 / 4.0 / 2.7 | 49.7 / p 0.57 ; 50.1 / p 0.73 ; 49.4 / p 0.93 |
| 12 bridge check: the same stand-in rule on EUR/USD | 2010-26 | **60.3** (98; 50-69) | **65.7** (49; 51-77) | **68.3** (32; 50-80) | 5.9 / 2.9 / 2.0 | 49.6 / p 0.01 ; 49.8 / p 0.00 ; 49.5 / p 0.00 |
| same | 2016-26 | **59.5** (61; 46-70) | **61.5** (30; 46-78) | **66.2** (20; 43-82) | 5.7 / 2.8 / 1.9 | 49.2 / p 0.04 ; 49.0 / p 0.05 ; 48.9 / p 0.05 |
| same | 2023-26 | **49.1** (24; 33-71) | **43.9** (12; 19-68) | **53.7** (8; 22-78) | 6.2 / 3.2 / 2.1 | 49.1 / p 0.51 ; 49.3 / p 0.68 ; 49.1 / p 0.38 |
| agreement rule, original, EUR/USD (reference) | 2010-26 | **58.3** (91; 48-68) | **63.3** (45; 48-75) | **66.7** (30; 49-81) | 5.4 / 2.7 / 1.8 | 49.5 / p 0.02 ; 49.6 / p 0.01 ; 49.1 / p 0.00 |

* The rule calls on 52 % of sessions in 1987-98 (44 % in the euro era). Positioning and the macro subset agree in sign
  on 79 % of sessions, positioning and the rate stand-in on 58 %.
* The bridge check says the test is fair: with the same two stand-ins the rule keeps its whole euro-era record. So the
  mark-era failure belongs to the era, not to the stand-ins. (It also says the precise rate-trend input is not what
  makes the agreement rule work in 2010-26.)
* The two halves point in opposite directions (60 / 56 / 50 % then 40 / 37 / 36 %); with 11-42 independent calls per
  cell neither is distinguishable from the random-timing band.
* The daily stream of the agreement-style rule has a net Sharpe of +0.36 (t 1.2) in 1987-98: +0.64 in 1987-92, +0.04
  in 1993-98. A position held only while the three inputs agree made a little money, while the same calls held for
  21-63 sessions were wrong more often than right. Neither figure is significant; the product is the multi-week
  call, and that failed.

## Secondary (b): the same positioning rule on JPY, GBP, CHF, CAD futures, 1987-98 (context)

| currency | era | 21 sessions | 42 sessions | 63 sessions | random timing p at 21, 42, 63 | daily-stream Sharpe (t) |
|---|---|---|---|---|---|---|
| JPY | 1987-98 | **47.2** (141; 39-56) | **50.2** (70; 39-61) | **49.9** (46; 36-64) | 0.84 ; 0.42 ; 0.44 | +0.05 (0.2) |
| GBP | 1987-98 | **47.4** (141; 39-56) | **49.8** (70; 39-61) | **50.1** (46; 36-64) | 0.84 ; 0.51 ; 0.47 | +0.04 (0.1) |
| CHF | 1987-98 | **48.3** (141; 40-56) | **48.7** (70; 37-60) | **48.2** (46; 34-62) | 0.65 ; 0.52 ; 0.57 | +0.45 (1.5) |
| CAD | 1987-98 | **52.0** (141; 44-60) | **52.4** (70; 41-64) | **50.9** (46; 38-66) | 0.25 ; 0.25 ; 0.38 | -0.11 (-0.4) |
| mean of the four | 1987-98 | 48.7 | 50.3 | 49.8 | | equal-risk basket +0.18 (0.6) |
| mean of the four | 1987-92 / 1993-98 | 50.1 / 47.4 | 52.5 / 48.0 | 52.2 / 47.3 | | basket +0.30 (0.7) / +0.06 (0.1) |

No currency passes the bar; at 42 sessions two of four are above 50 %, by 0.2 and 2.4 points. The answer to "does
positioning-following work in that era at all, or only on the mark?" is: on none of the five. Halves by currency are
in `pre_euro_accuracy.csv`; they flip sign (GBP 53 / 59 / 58 % in 1987-92, then 42 / 40 / 42 %; CAD the other way), which
is what noise looks like. CHF's Sharpe of +0.45 comes with an accuracy below 50 % and is +0.76 in 1987-92, +0.10 after.

## Secondary (c) and leak / sanity checks (all on the primary rule, 1987-98)

| check | 21 sessions | 42 sessions | 63 sessions | reading |
|---|---|---|---|---|
| 7 signal 63 sessions stale | **49.5** (138; 41-58) | **49.5** (69; 38-61) | **51.2** (45; 37-65) | the stale copy is no worse than the live rule: there is no timing information to lose |
| 8 signal 126 sessions stale | **49.6** (135; 41-58) | **51.9** (67; 40-64) | **53.8** (44; 40-68) | same |
| 9 one extra week of publication delay | **46.3** (141; 38-54) | **46.6** (70; 36-59) | **43.1** (46; 30-58) | the result does not hinge on the lag; stream Sharpe +0.14 |
| 10 shuffled outcomes, 500 paths | 50.0 (44.4-55.9) | 50.0 (43.3-57.0) | 50.0 (42.2-57.9) | the noise band of this sample is +-6 to +-8 points |
| 13 post-hoc: as-of + 6 days for every report (earlier than publication before 1993) | **46.4** (142; 38-55) | **46.1** (70; 35-58) | **46.7** (47; 33-61) | the conservative lag did not cause the fail; stream Sharpe -0.08 |
| 14 post-hoc: month-ends on the OECD price | **47.2** (142; 39-55) | **51.1** (70.5; 40-63) | **48.2** (46.3; 34-62) | the synthetic price did not cause the fail |
| 15 pipeline check: look-ahead copy (report known 30 days before its as-of date) | **73.6** (143; 66-80) | **63.6** (71; 52-74) | **59.0** (47; 45-72) | the code detects information when it exists; random-timing p 0.000 |

Independent re-computation of the primary number with a separate script that shares no signal code with the module
(naive loops over the saved CSV): 47.6 / 47.5 / 45.0 % on 141.3 / 70.1 / 46.4 independent decisions, identical.

The round-3 incremental test against the live streams and the round-5 extra-vote test do not apply: there is no
overlap in time between this sample and the 2010-26 streams.

## Candidates and evaluations run (strict count)

* **Rules that could have been read as support (candidates): 6** = the primary, the agreement-style rule, and the
  four other currencies. All six fail the bar.
* **Declared in the docstring before any outcome: 12 evaluations** = those 6, the two stale copies, the extra week of
  delay, the shuffled-outcome control, the non-positioning-legs rule and the euro-era bridge check.
* **Added after the result was seen: 3**, all labelled post-hoc, none able to create a pass: the optimistic lag (13),
  the month-end rescoring on the OECD price (14) and the look-ahead pipeline check (15). Plus the pooled Sharpe below,
  which is arithmetic on streams already computed.
* Total looks at real outcomes of the new period: 13 (the shuffled control never touches real outcomes; the bridge
  check is on EUR/USD 2010-26). Nothing was tuned; no parameter was changed after the first run.

## Anything suspicious

1. **Mid-month reports before 1990.** The file has them; the CFTC says only monthly reports were published then. I
   let them arrive with the month-end report. If they were in fact public earlier, the rule was given stale data for
   three years; the optimistic-lag check (13) covers that case and fails the same way.
2. **Fortnightly publication in 1992-98.** Which weeks were release weeks is not in the file, so every weekly figure
   is treated as an off-week one (as-of + 13 days). The project's euro-era convention (as-of + 6) ignores that 1999
   was still fortnightly; it does not matter there because the euro z-score only starts in 2000.
3. **The stale copies beat the live signal in 1993-98** (56.7 / 55.7 / 57.9 % at 63 sessions stale against 44.2 / 44.2 /
   41.8 % live; random-timing p 0.05-0.07): in those years following speculators was a contrarian indicator at the
   multi-week horizon. One six-year half, inside the shuffle band; noted, not interpreted.
4. **One week of delay moves the 1987-92 half's stream Sharpe from +0.07 to +0.56** and the 1993-98 half from -0.01
   to -0.35. Six-year Sharpes of this rule are noise of about +-0.4.
5. **The signal behaved in 1987-98 as it did in 2000-09, not as in 2010-26**: 7.3 sign flips a year (7.1 in 2000-09,
   3.0 in 2010-26), mean run 34 sessions (35; 83), correlation with the trailing 126-session return +0.20 (+0.13;
   +0.53). The 2010-22 stretch is the unusual one in the signal's own behaviour too: long, persistent positioning
   regimes aligned with multi-month trends. (Signals only; no outcome involved.)
6. **The agreement-style stream's Sharpe (+0.36) against its sub-50 % accuracy**: see secondary (a). Not significant
   either way.
7. **The macro score is a frozen transfer with 40 % of its weight missing** (no equity-momentum input, no FOMC-day
   input). The bridge check shows that this degraded score still works in 2010-26, but "the agreement rule failed on
   the mark" strictly means "this rebuildable version failed".
8. **Pre-registration evidence.** The docstring (rule, lags, stand-ins, bar, the 12 evaluations) was written before
   the first outcome run of this session, and the module's post-hoc addendum is marked as such. I was told not to
   commit, so no commit of mine separates the two; the order rests on this session's record.
9. Two commits, `0e882cc` and `38230d6` ("research arm work in progress (round 9)"), made by another process from
   18:02 UTC on, swept this arm's files into git together with another arm's. They were not made by me and both
   post-date the first run.
10. **Power.** With 70 independent 42-session decisions the 95 % interval is 36-59 %. The mark era alone cannot
    exclude a true 55-58 %; it does exclude the 2010-26 point estimates (60.4 % at 42 sessions, 63.1 % at 63).

## What this implies for the planning Sharpe of the positioning-driven calls (currently 0.3-0.5)

Pooled net Sharpe of the daily positioning stream (`pre_euro_pooled_sharpe.csv`; the mark 1987-98 on the synthetic
euro, EUR/USD 2000-26 on H.10 with the project's rolling(52) z; post-hoc arithmetic, descriptive):

| years | length | Sharpe (t) | 95 % range (s.e. = 1 / sqrt(years)) |
|---|---|---|---|
| mark 1987-98 (never looked at before this arm) | 11.9 y | +0.03 (0.1) | -0.54 .. +0.60 |
| EUR/USD 2000-02 (before every selection window) | 3.0 y | +0.15 (0.3) | -0.98 .. +1.29 |
| EUR/USD 2003-22 (the windows on which the rule was chosen and kept) | 19.9 y | +0.64 (2.9) | +0.20 .. +1.08 |
| EUR/USD 2023-26 (after selection) | 3.8 y | +0.36 (0.7) | -0.64 .. +1.37 |
| **everything outside the selection window** | **18.7 y** | **+0.10 (0.4)** | **-0.35 .. +0.55** |
| everything, 1987-2026, selection window included | 38.6 y | +0.37 (2.3) | +0.06 .. +0.69 |

* Before this arm the out-of-selection record was 6.8 years (2000-02 and 2023-26). It is now 18.7 years, and it says
  +0.10. The all-years figure of +0.37 is an upper bound, because half of it is the window the rule was picked on.
* Against the planning range: +0.3 is 0.9 standard errors above the out-of-selection estimate (not rejected); +0.5
  is 1.7 above (rejected one-sided at about 4 %). On accuracy the mark era is 1.2-1.5 standard errors below what a
  0.3-Sharpe process gives (53.4 / 54.9 / 56.0 % at 21 / 42 / 63 sessions) and 1.8-2.0 below a 0.5-Sharpe process
  (55.7 / 58.1 / 59.9 %).
* Together with arm G (no replication on seven other currencies in 2010-26) the positioning effect now rests on
  EUR/USD 2003-2022 alone: it is absent on the same instrument's predecessor in 1987-98, absent on four other
  currencies in 1987-98, absent on seven other currencies in 2010-26, weak in 2000-02 and in 2023-26.
* **Recommendation: lower the planning Sharpe for positioning-driven calls from 0.3-0.5 to 0.1-0.3, centre 0.2.**
  Arithmetic behind the centre: the selection window at half its measured Sharpe (0.32, a conventional haircut) and
  the out-of-selection years at face value (0.10), weighted by length, give 0.21. At 0.2 the expected accuracy of a
  positioning call is about 52 / 53 / 54 % at 21 / 42 / 63 sessions, not 58-63 %.
* For the agreement rule the published 59 / 63 / 67 % (2010-26) has no out-of-time support either: its rebuildable
  version scored 48 / 45 / 42 % in 1987-98 (74 / 36 / 24 independent calls; the 2010-26 figures at 42 and 63 sessions
  lie outside those intervals). The stated probabilities attached to agreement calls should be read as the record of
  one 17-year window on one pair, and I would not quote them above the high 50s.
* What this arm cannot say: whether 2003-22 was luck or a real regime (central-bank-driven, persistent positioning
  trends) that may return. The signal's own behaviour (item 5 above) is consistent with "a regime": it was a
  different, much more persistent object in 2010-26. That is a description, not a tradable distinction.

## Files

* `src/eurusd/arms/pre_euro.py`
* `reports/arm_pre_euro.md`
* `experiments/results/arms/pre_euro_accuracy.csv` (every rule x era x horizon, with baselines),
  `pre_euro_sharpe.csv`, `pre_euro_pooled_sharpe.csv`, `pre_euro_shuffled.csv`, `pre_euro_month_end_rescore.csv`,
  `pre_euro_price_check.csv`, `pre_euro_reconcile.csv`, `pre_euro_house_weights.csv`, `pre_euro_cot_coverage.csv`,
  `pre_euro_cot_archive_check.csv`, `pre_euro_summary.csv`, `pre_euro_positions.parquet` (daily stream of the primary
  rule: `pos`, `z52`, `fwd_bp`, `net_bp`, `close`)
* `data/macro/pre_euro_cot_{dem,jpy,gbp,chf,cad}.csv`, `data/macro/pre_euro_fred_CCUSSP01DEM650N.csv`
* `data/raw/cftc/deacot1986_2016.zip` (git-ignored), `logs/pre_euro.log`
