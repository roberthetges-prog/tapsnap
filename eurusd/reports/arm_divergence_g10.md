# Arm V: divergence across G10 (`divergence_g10`) - pre-registered replication of the WIDER lead on nine currencies

Code `src/eurusd/arms/divergence_g10.py` (`run(cost_pips=1.2)`, about 70 seconds, rewrites this file). Results in
`experiments/results/arms/`: `divergence_g10_positions.parquet` (EUR/USD daily stream of the gated rule on the feature-store grid:
`pos`, `fwd_bp`, `net_bp` spot-only, plus `carry_bp`, `net_bp_carry`, `pos_ungated`, `wider`, `cls`), `divergence_g10_report.csv`
(every currency, basket, stream, period; columns `variant`, `carry`, `final`), `divergence_g10_basket.parquet` (daily basket and
per-currency streams), `divergence_g10_tables.csv` (placebo, leak checks, EUR reproduction, added diagnostics), log
`logs/divergence_g10.log`. The frozen definitions and the verdict rule are in the module docstring and were written before any
result; only data availability had been looked at. What was added after the first run is marked ADDED and is outside the verdict.

## Verdict: FAILS
**The divergence mechanism does not replicate. By the pre-registered rule it fails, narrowly on paper and clearly in substance.**

| criterion (eight-currency basket ex EUR, spot + carry, net) | required | observed | |
|---|---|---|---|
| (i) gated-WIDER stream: Sharpe > 0 in 2000-26 and 2010-26, pooled t (2000-26) >= 2 | t >= 2.00 | Sharpe +0.38 / +0.10, t **1.98** (2010-26: t 0.41) | **fail** |
| (ii) on-session Sharpe WIDER minus complement > 0, 2000-26 | >= 6 of 8 | **6 of 8** (GBP +0.35, JPY +0.47, CHF -0.41, AUD +0.71, CAD +0.10, NZD +0.39, SEK +0.70, NOK -0.13) | pass |
| (iii) rotation placebo, 500 draws: share of draws with a basket gap at least as large | <= 0.050 | gap +0.42, p = **0.056** | **fail** |

1. **A near miss in the full sample.** (i) misses by 0.02 of a t-statistic and (iii) by 0.006 of a p-value. ADDED checks of how
   fragile that is: with 5,000 placebo draws p = 0.051; with the literal 1.2-pip cost for USDSEK / USDNOK (I had
   declared 30 pips for those two before the run, see below) t = 2.04 and p = 0.054, so (i) would pass and (iii) would
   still fail. The labelled 6 / 12-month robustness line reads t 1.91 and p 0.034 (it cannot enter the verdict). Under either
   cost convention the verdict is FAILS; nobody should read 1.98 against 2.00 as a refutation by itself.
2. **What decides it is where the number comes from: 2000-09, reversed in 2010-15, weak since.** Basket gated-WIDER Sharpe +0.84
   (t +2.6) in 2000-09 and +0.10 (t +0.4) in 2010-26, +0.32 in 2016-26,
   -0.18 in 2023-26. In 2010-26 the WIDER-minus-complement gap is +0.14 with placebo p 0.33 and positive in
   4 of 8 currencies. In the window of the EUR lead itself (2006-26, ADDED) the basket shows +0.20 (t +0.9)
   inside WIDER against +0.05 outside. 2016-26 is the one stretch after 2009 with the right sign (+0.32, t +1.1,
   against -0.23 outside; spot only +0.17 against -0.14), far from significant, and 2010-15 has the opposite sign (-0.32 inside, +0.38 outside). Nothing
   outside EUR supports the lead at conventional levels in the years it was found on.
3. **And it is carry, not persistence of trends.** A rate differential that is getting wider is, most of the time, moving away from
   zero, so "long the currency whose relative rate rose" is then "long the high yielder": on WIDER sessions the position has the
   sign of the differential 78-86 % of the time, on complement sessions 15-34 %
   (ADDED). The gate therefore sorts the same rule into "earn carry" and "pay carry". Spot only, the basket is +0.20
   (t +1.0) inside WIDER against +0.09 outside, gap +0.11, placebo p 0.34; in 2010-26 -0.04
   against +0.06. The plain carry trade with the same vol scale earned +0.82 in 2000-09 and +0.02 in 2010-26; the gated
   stream is 0.48 correlated with it and its alpha on it has t +1.5 (2000-26) and +0.4 (2010-26).
4. **Stale placebo.** With the rate data six months older the gap is still +0.31 (live +0.42); by the house rule a
   slow signal that scores the same when stale is a regime bet (here: the carry regime before 2008), not timing information.
5. **EUR/USD itself does not show it under these definitions.** Frozen rule on EUR/USD: gated +0.11 against complement
   +0.04 (2000-26), +0.29 against +0.33 (2010-26); spot only +0.04 against +0.12; placebo p 0.38.
   More important, arm S's own signals lose most of their concentration when the class is built from monthly 3-month interbank
   rates instead of daily policy rates (2006-26): positioning +0.73 inside / +0.48 outside (arm S: +1.34 / +0.12), 2y-spread
   trend +0.46 / +0.44 (arm S: +0.95 / +0.10), agreement rule Sharpe +0.45 / +0.55 (arm S: +1.23 / +0.02) and accuracy
   59 % / 61 % inside against 55 % / 60 % outside (arm S: 64 / 70 against 51 / 49). The two classes
   agree on 71 % of sessions (58 % in 2006-15, 83 % in 2016-26). Where they agree (2016-26) the agreement rule keeps its
   concentration (+0.79 inside, +0.02 outside); in 2006-15 it reverses (+0.12 inside, +0.87 outside).

**Plain statement required by the brief: the WIDER lead is likely a third EUR-specific artefact** (after the positioning trend
and residual order flow), and on EUR/USD it is also specific to one way of measuring the policy gap. Step 4 was not run.

**What it means for the engine.** (i) Do not gate the engine on WIDER and do not make "rate-differential trend gated by WIDER" a
rule: on EUR/USD it is +0.15 / +0.07 / -0.80 (2010-26 / 2016-26 / 2023-26, feature-store grid, spot), far below the bar.
(ii) Keep the unconditional agreement rule as the primary rule, at the planning level arm S gave (Sharpe 0.3-0.5). (iii) The paper
scenario `agreement_wider` can keep running because it costs nothing, but it should be read as a scenario whose prior is now
"probably chance"; showing the policy-gap direction next to a call remains harmless context. (iv) No currency outside EUR is a
candidate either: the only positive pocket is SEK (+0.43 gated in 2010-26, t +1.8), one of eight, not selected for in advance.
Monthly class of EUR/USD on the last session (2026-11-05): NARROWER.

## Frozen definitions (module docstring, written before any result)
* Currencies EUR, GBP, JPY, CHF, AUD, CAD, NZD, SEK, NOK against USD; identical test for all; EUR is the reference, the other
  eight are the replication sample.
* `d_c(m) = r_c(m) - r_US(m)`, monthly 3-month interbank rates (FRED `IR3TIB01xxM156N`). An observation of month m is usable from
  month end + 30 days, plus one calendar day. Missing months are filled with the previous value for at most three months.
* Policy gap `|d_c|`: WIDER if larger than six months earlier, NARROWER if smaller, SAME if equal; complement = NARROWER or SAME.
* (c) rate-differential trend: `sign(d_c(m) - d_c(m-3))` (+1 = long the foreign currency), position = sign x
  clip(training-median rv_21d / rv_21d, 0, 1.5), set on the first session a new month is usable and held (monthly rebalanced);
  walk-forward through `eurusd.wf.walk_forward`, test years 2000-2026 (the vol median is the only fitted number).
* (d) gated: (c) on WIDER sessions, flat otherwise; complement: (c) on NARROWER / SAME sessions. With and without carry
  ((r_c - r_US) x 100 / 252 bp per session on the position) = 6 streams. Primary P&L = spot + carry.
* Prices: Fed H.10 noon rates from FRED, in "foreign currency vs USD" direction. Cost 1.2 pips of the conventional pair per unit
  turnover; **declared deviation from the brief:** USDSEK and USDNOK are charged 30 pips (about 3-4 bp) because 1.2 pips of a
  10-kroner rate is 0.1 bp, as arm F did for USDMXN; the literal version is in the sensitivity table and in the verdict section.
* Stream Sharpe / t: daily net bp over all sessions with a defined class (flat sessions zero). On-session Sharpe (the statistic
  of the arm S lead): the ungated stream on the sessions of the class. Accuracy: sign(s) x h-session spot return > 0 on greedy
  non-overlapping decisions. Basket: equal weight of the currencies with a defined class on the day.
* Verdict rule, placebo design (same rotation offset for all currencies, at least a year, 500 draws, seed 7) and leak checks as in
  the table above and in section 5. Windows 3 and 6 months were not varied; the 6 / 12 alternative is one labelled line.
* Trials: 6 frozen streams + 1 robustness line. Sensitivities (2x cost, literal cost) change no definition.

## 1. Data, spans, lags
| currency | pair (H.10 series) | rate series | rate span | months filled (<= 3) | streams run | sessions | cost, bp per unit turnover | turnover of (c), units / year |
|---|---|---|---|---|---|---|---|---|
| EUR | EURUSD (DEXUSEU) | IR3TIB01EZM156N | 1994-01 .. 2026-09 | - | 2000-01-03 .. 2026-11-05 | 6731 | 1.0 | 4.6 |
| GBP | GBPUSD (DEXUSUK) | IR3TIB01GBM156N | 1957-01 .. 2026-01 | 2026-02, 2026-03, 2026-04 | 2000-01-03 .. 2026-06-30 | 6642 | 0.8 | 5.9 |
| JPY | USDJPY (DEXJPUS) | IR3TIB01JPM156N | 2002-04 .. 2026-08 | 2026-09 | 2002-12-02 .. 2026-11-05 | 5999 | 1.1 | 6.8 |
| CHF | USDCHF (DEXSZUS) | IR3TIB01CHM156N | 1999-07 .. 2026-09 | - | 2000-03-02 .. 2026-11-05 | 6690 | 1.2 | 7.1 |
| AUD | AUDUSD (DEXUSAL) | IR3TIB01AUM156N | 1968-01 .. 2026-08 | 2026-09 | 2000-01-03 .. 2026-11-05 | 6731 | 1.6 | 5.7 |
| CAD | USDCAD (DEXCAUS) | IR3TIB01CAM156N | 1956-01 .. 2026-09 | - | 2000-01-03 .. 2026-11-05 | 6731 | 1.0 | 6.4 |
| NZD | NZDUSD (DEXUSNZ) | IR3TIB01NZM156N | 1973-12 .. 2026-09 | - | 2000-01-03 .. 2026-11-05 | 6731 | 1.9 | 4.5 |
| SEK | USDSEK (DEXSDUS) | IR3TIB01SEM156N | 1982-01 .. 2026-09 | - | 2000-01-03 .. 2026-11-05 | 6731 | 3.7 | 6.1 |
| NOK | USDNOK (DEXNOUS) | IR3TIB01NOM156N | 1979-01 .. 2026-09 | - | 2000-01-03 .. 2026-11-05 | 6731 | 4.0 | 5.5 |

* US rate: `IR3TIB01USM156N`, 1964-06 .. 2026-09, one missing month (2020-04) filled with the previous value.
* Euro area: `IR3TIB01EZM156N` ends 2026-01 on FRED; from 2026-02 it is continued with `IR3TIB01DEM156N` (Germany), which is the
  same 3-month Euribor (difference below 0.02 points in every month since 1999, asserted). GBP: the FRED series ends 2026-01,
  is carried three months and GBP leaves the basket on 2026-06-30. JPY starts 2002-04, CHF 1999-07 (first sessions in the table).
* New files this arm fetched from FRED (`fredgraph.csv`, curl --http1.1): `fred_DEXSDUS.csv`, `fred_DEXNOUS.csv` (H.10, 1971 ..
  2026-11-06), `fred_IR3TIB01SEM156N.csv` (1982-01 .. 2026-09), `fred_IR3TIB01NOM156N.csv` (1979-01 .. 2026-09). Publication lag
  used for every rate series: month end + 30 days (+1 day). H.10 prices: the price of the decision day (noon New York).
* Daily 2y yields exist in the repo only for EUR and USD and were not used, so the measure is the same for all nine.
* EUR H.10 starts 1999-01-04, so its vol target for 2000-03 rests on 1-4 years; the others have ten years before 2000.

## 2. Step 1 - EUR/USD reproduction with the monthly definitions
(a) The class itself, feature-store sessions:

| period | sessions | % WIDER, policy rates (arm S) | % SAME, policy rates | % WIDER, 3m interbank monthly | % sessions same class (WIDER vs not) | arm S WIDER also WIDER here | WIDER here also arm S WIDER | phi |
|---|---|---|---|---|---|---|---|---|
| 2006-26 | 5409 | 39 | 31 | 56 | 71 | 85 | 59 | 0.46 |
| 2006-15 | 2592 | 30 | 40 | 49 | 58 | 62 | 38 | 0.17 |
| 2016-26 | 2817 | 47 | 23 | 62 | 83 | 99 | 74 | 0.70 |
| 2023-26 | 1000 | 27 | 15 | 41 | 82 | 93 | 61 | 0.64 |

Policy rates move in steps and sit still for long stretches (SAME on 31 % of sessions, 40 % in 2006-15); a monthly average of
interbank rates is never exactly unchanged and in 2007-12 it also carries the Libor / Euribor credit premium, which is not policy.
Nearly every arm S WIDER session after 2016 is also WIDER here (99 %), but the monthly class adds as many sessions again.

(b) Arm S's own table (`regime_dependence.regime_tables`, daily-sign streams, feature-store grid, spot, 1.2 pips) with the two
classes; "in" = WIDER sessions, "out" = the other sessions with a defined class:

| signal | period | arm S class: SR in / out | monthly class: SR in / out | arm S class: acc 21 in / out (n) | monthly class: acc 21 in / out (n) | arm S class: acc 42 in / out | monthly class: acc 42 in / out |
|---|---|---|---|---|---|---|---|
| positioning sign | 2006-26 | +1.34 / +0.12 | +0.73 / +0.48 | 58 / 54 (110 / 164) | 61 / 61 (150 / 117) | 54 / 62 | 59 / 49 |
| positioning sign | 2006-15 | +1.78 / +0.03 | +0.74 / +0.48 | 71 / 52 (42 / 90) | 63 / 62 (65 / 65) | 61 / 66 | 54 / 53 |
| positioning sign | 2016-26 | +1.01 / +0.29 | +0.74 / +0.50 | 50 / 55 (68 / 74) | 59 / 60 (85 / 52) | 50 / 58 | 63 / 44 |
| 2y-spread trend | 2006-26 | +0.95 / +0.10 | +0.46 / +0.44 | 55 / 46 (110 / 164) | 57 / 49 (150 / 117) | 40 / 46 | 41 / 62 |
| 2y-spread trend | 2006-15 | +1.53 / +0.09 | +0.36 / +0.79 | 57 / 43 (42 / 90) | 55 / 49 (65 / 65) | 30 / 38 | 37 / 65 |
| 2y-spread trend | 2016-26 | +0.49 / +0.14 | +0.58 / -0.20 | 54 / 49 (68 / 74) | 58 / 48 (85 / 52) | 47 / 55 | 44 / 59 |
| house score | 2006-26 | +0.54 / +0.43 | +0.30 / +0.73 | 55 / 47 (110 / 164) | 55 / 53 (150 / 117) | 58 / 59 | 55 / 59 |
| house score | 2006-15 | +0.23 / +0.37 | -0.12 / +0.79 | 60 / 48 (42 / 90) | 52 / 52 (65 / 65) | 70 / 55 | 54 / 59 |
| house score | 2016-26 | +0.83 / +0.56 | +0.72 / +0.66 | 51 / 46 (68 / 74) | 56 / 54 (85 / 52) | 50 / 63 | 56 / 59 |
| AGREEMENT RULE | 2006-26 | +1.23 / +0.02 | +0.45 / +0.55 | 64 / 51 (74 / 127) | 59 / 55 (109 / 87) | 70 / 49 | 61 / 60 |
| AGREEMENT RULE | 2006-15 | +1.52 / +0.02 | +0.12 / +0.87 | 68 / 54 (31 / 69) | 57 / 54 (51 / 48) | 70 / 44 | 57 / 67 |
| AGREEMENT RULE | 2016-26 | +1.02 / +0.02 | +0.79 / +0.02 | 60 / 48 (43 / 58) | 60 / 56 (58 / 39) | 70 / 56 | 65 / 52 |

The first column pair reproduces arm S exactly (positioning 1.34 / 0.12, spread trend 0.95 / 0.10, agreement rule 64 % / 70 %
against 51 % / 49 %). With the monthly class the 2006-26 contrast shrinks to a fraction for positioning, vanishes for the spread
trend and reverses in Sharpe for the agreement rule; the distance is entirely 2006-15, where the two classes agree on only
58 % of sessions. So the monthly-rate version is NOT close to arm S's version before 2016 and close after it.

(c) The frozen rule on EUR/USD (H.10 grid) is the EUR row of the next table. ADDED: the same rule on the feature-store grid
(the delivered positions file; store volatility, walk-forward 2010-26; Sharpe (t)):

| period | % WIDER | gated (d), spot = `net_bp` | gated (d), spot + carry | ungated (c), spot | complement, spot |
|---|---|---|---|---|---|
| 2010-26 | 60 | +0.15 (+0.6) | +0.23 (+0.9) | +0.34 (+1.4) | +0.36 (+1.5) |
| 2016-26 | 62 | +0.07 (+0.2) | +0.18 (+0.6) | -0.04 (-0.1) | -0.17 (-0.6) |
| 2023-26 | 41 | -0.80 (-1.6) | -0.70 (-1.4) | -0.63 (-1.3) | -0.14 (-0.3) |

## 3. Step 2 - per currency and basket (frozen rule, spot + carry, net; Sharpe with t in brackets)
| currency | period | (c) ungated SR (t) | (d) WIDER SR (t) | complement SR (t) | on-session SR WIDER / compl. | % WIDER | WIDER acc 21 / 42 / 63 (n) | compl. acc 21 / 42 / 63 (n) | ungated acc 21 / 42 / 63 |
|---|---|---|---|---|---|---|---|---|---|
| EUR | 2000-26 | +0.11 (+0.6) | +0.11 (+0.6) | +0.04 (+0.2) | +0.15 / +0.07 | 52 | 49 / 57 / 51 (169 / 88 / 61) | 54 / 48 / 59 (156 / 80 / 56) | 50 / 46 / 44 |
| EUR | 2010-26 | +0.43 (+1.8) | +0.29 (+1.2) | +0.33 (+1.4) | +0.37 / +0.52 | 60 | 55 / 62 / 56 (121 / 61 / 43) | 56 / 46 / 59 (81 / 41 / 29) | 51 / 47 / 44 |
| EUR | 2016-26 | +0.05 (+0.2) | +0.22 (+0.7) | -0.24 (-0.8) | +0.29 / -0.39 | 62 | 54 / 62 / 64 (80 / 40 / 28) | 51 / 38 / 53 (49 / 24 / 17) | 49 / 44 / 48 |
| EUR | 2023-26 | -0.62 (-1.2) | -0.66 (-1.3) | -0.25 (-0.5) | -1.03 / -0.33 | 41 | 37 / 70 / 57 (19 / 10 / 7) | 56 / 38 / 56 (27 / 13 / 9) | 44 / 36 / 50 |
| GBP | 2000-26 | +0.17 (+0.9) | +0.25 (+1.3) | -0.01 (-0.1) | +0.34 / -0.02 | 55 | 53 / 53 / 57 (179 / 95 / 67) | 50 / 54 / 53 (148 / 80 / 58) | 51 / 53 / 44 |
| GBP | 2010-26 | +0.23 (+0.9) | +0.32 (+1.3) | +0.01 (+0.0) | +0.44 / +0.01 | 53 | 50 / 53 / 51 (107 / 57 / 41) | 51 / 51 / 62 (96 / 51 / 37) | 49 / 57 / 42 |
| GBP | 2016-26 | +0.18 (+0.6) | +0.39 (+1.3) | -0.11 (-0.4) | +0.56 / -0.15 | 50 | 55 / 51 / 52 (64 / 35 / 25) | 47 / 47 / 72 (64 / 34 / 25) | 49 / 56 / 45 |
| GBP | 2023-26 | +0.07 (+0.1) | +0.45 (+0.8) | -0.25 (-0.5) | +0.74 / -0.31 | 38 | 59 / 73 / 71 (17 / 11 / 7) | 41 / 50 / 70 (27 / 14 / 10) | 49 / 52 / 57 |
| JPY | 2000-26 | +0.01 (+0.1) | +0.18 (+0.9) | -0.15 (-0.7) | +0.26 / -0.21 | 48 | 56 / 54 / 52 (140 / 74 / 52) | 45 / 48 / 51 (155 / 80 / 55) | 51 / 54 / 57 |
| JPY | 2010-26 | -0.13 (-0.5) | +0.11 (+0.4) | -0.29 (-1.2) | +0.15 / -0.41 | 50 | 57 / 54 / 55 (103 / 54 / 38) | 44 / 39 / 49 (104 / 54 / 37) | 52 / 45 / 55 |
| JPY | 2016-26 | +0.03 (+0.1) | +0.37 (+1.2) | -0.36 (-1.2) | +0.49 / -0.54 | 55 | 59 / 61 / 54 (71 / 36 / 24) | 46 / 37 / 47 (59 / 30 / 19) | 55 / 50 / 54 |
| JPY | 2023-26 | -0.66 (-1.3) | +0.31 (+0.6) | -0.95 (-1.9) | +0.56 / -1.14 | 30 | 64 / 71 / 60 (14 / 7 / 5) | 44 / 19 / 30 (32 / 16 / 10) | 51 / 45 / 57 |
| CHF | 2000-26 | +0.22 (+1.1) | +0.01 (+0.0) | +0.29 (+1.5) | +0.01 / +0.42 | 51 | 48 / 47 / 43 (170 / 90 / 65) | 54 / 56 / 51 (162 / 85 / 63) | 51 / 52 / 50 |
| CHF | 2010-26 | +0.19 (+0.8) | +0.01 (+0.0) | +0.26 (+1.0) | +0.01 / +0.40 | 57 | 47 / 41 / 43 (119 / 63 / 46) | 56 / 52 / 47 (90 / 48 / 36) | 50 / 48 / 48 |
| CHF | 2016-26 | +0.14 (+0.5) | +0.08 (+0.3) | +0.12 (+0.4) | +0.10 / +0.21 | 65 | 49 / 42 / 48 (85 / 45 / 33) | 58 / 54 / 50 (48 / 26 / 20) | 52 / 47 / 57 |
| CHF | 2023-26 | -0.60 (-1.2) | -0.64 (-1.2) | -0.20 (-0.4) | -0.81 / -0.30 | 61 | 38 / 38 / 42 (29 / 16 / 12) | 53 / 55 / 56 (19 / 11 / 9) | 51 / 41 / 60 |
| AUD | 2000-26 | +0.31 (+1.6) | +0.47 (+2.4) | -0.02 (-0.1) | +0.67 / -0.03 | 49 | 54 / 57 / 56 (161 / 84 / 57) | 51 / 49 / 50 (164 / 87 / 58) | 53 / 56 / 54 |
| AUD | 2010-26 | -0.05 (-0.2) | +0.03 (+0.1) | -0.09 (-0.4) | +0.04 / -0.11 | 43 | 47 / 48 / 55 (88 / 46 / 31) | 51 / 49 / 49 (116 / 61 / 41) | 50 / 55 / 55 |
| AUD | 2016-26 | -0.23 (-0.7) | -0.09 (-0.3) | -0.22 (-0.7) | -0.13 / -0.29 | 42 | 47 / 41 / 50 (55 / 29 / 20) | 49 / 48 / 50 (75 / 40 / 26) | 47 / 52 / 50 |
| AUD | 2023-26 | -0.46 (-0.9) | -0.53 (-1.0) | -0.18 (-0.4) | -0.79 / -0.24 | 44 | 45 / 50 / 57 (20 / 10 / 7) | 38 / 50 / 56 (26 / 14 / 9) | 44 / 50 / 43 |
| CAD | 2000-26 | -0.07 (-0.4) | -0.02 (-0.1) | -0.09 (-0.5) | -0.02 / -0.12 | 51 | 47 / 55 / 59 (169 / 93 / 66) | 43 / 42 / 53 (168 / 92 / 64) | 50 / 54 / 51 |
| CAD | 2010-26 | -0.13 (-0.5) | -0.13 (-0.5) | -0.06 (-0.2) | -0.17 / -0.08 | 55 | 47 / 57 / 55 (112 / 60 / 42) | 46 / 42 / 53 (96 / 53 / 38) | 49 / 53 / 52 |
| CAD | 2016-26 | -0.24 (-0.8) | -0.10 (-0.3) | -0.24 (-0.8) | -0.13 / -0.36 | 54 | 40 / 54 / 50 (72 / 39 / 28) | 41 / 34 / 50 (63 / 35 / 26) | 46 / 47 / 50 |
| CAD | 2023-26 | -0.51 (-1.0) | -0.26 (-0.5) | -0.55 (-1.1) | -0.32 / -0.93 | 66 | 33 / 56 / 64 (30 / 16 / 11) | 50 / 56 / 43 (16 / 9 / 7) | 42 / 50 / 50 |
| NZD | 2000-26 | -0.14 (-0.7) | +0.03 (+0.2) | -0.24 (-1.2) | +0.05 / -0.34 | 52 | 52 / 53 / 51 (172 / 91 / 65) | 50 / 47 / 48 (159 / 85 / 56) | 46 / 47 / 43 |
| NZD | 2010-26 | -0.34 (-1.4) | -0.27 (-1.1) | -0.21 (-0.9) | -0.38 / -0.29 | 50 | 49 / 44 / 46 (104 / 54 / 39) | 51 / 49 / 47 (103 / 55 / 36) | 44 / 46 / 38 |
| NZD | 2016-26 | -0.25 (-0.8) | -0.37 (-1.2) | -0.02 (-0.1) | -0.55 / -0.02 | 45 | 52 / 39 / 43 (62 / 33 / 23) | 54 / 51 / 54 (71 / 37 / 24) | 47 / 48 / 43 |
| NZD | 2023-26 | -0.14 (-0.3) | -0.17 (-0.3) | -0.03 (-0.1) | -0.22 / -0.04 | 55 | 48 / 33 / 50 (27 / 15 / 10) | 48 / 55 / 50 (21 / 11 / 6) | 50 / 41 / 50 |
| SEK | 2000-26 | +0.37 (+1.9) | +0.50 (+2.6) | +0.00 (+0.0) | +0.70 / +0.01 | 51 | 58 / 60 / 55 (165 / 87 / 62) | 55 / 48 / 52 (163 / 86 / 60) | 56 / 57 / 51 |
| SEK | 2010-26 | +0.50 (+2.0) | +0.43 (+1.8) | +0.25 (+1.0) | +0.58 / +0.38 | 56 | 57 / 62 / 50 (115 / 60 / 44) | 59 / 52 / 48 (90 / 48 / 33) | 57 / 57 / 50 |
| SEK | 2016-26 | +0.67 (+2.2) | +0.66 (+2.2) | +0.21 (+0.7) | +0.83 / +0.36 | 65 | 59 / 68 / 55 (85 / 44 / 31) | 62 / 56 / 41 (47 / 25 / 17) | 59 / 57 / 55 |
| SEK | 2023-26 | +0.15 (+0.3) | +0.30 (+0.6) | -0.13 (-0.3) | +0.40 / -0.20 | 59 | 63 / 64 / 45 (27 / 14 / 11) | 58 / 50 / 29 (19 / 10 / 7) | 57 / 52 / 43 |
| NOK | 2000-26 | -0.02 (-0.1) | -0.07 (-0.4) | +0.02 (+0.1) | -0.10 / +0.04 | 46 | 52 / 55 / 53 (149 / 77 / 53) | 48 / 45 / 45 (175 / 91 / 62) | 51 / 49 / 43 |
| NOK | 2010-26 | -0.14 (-0.6) | -0.19 (-0.8) | -0.03 (-0.1) | -0.29 / -0.04 | 42 | 52 / 51 / 55 (86 / 45 / 31) | 48 / 45 / 46 (116 / 60 / 41) | 48 / 48 / 39 |
| NOK | 2016-26 | -0.20 (-0.7) | +0.08 (+0.3) | -0.32 (-1.1) | +0.12 / -0.42 | 44 | 56 / 67 / 67 (57 / 30 / 21) | 45 / 39 / 35 (73 / 38 / 26) | 48 / 49 / 40 |
| NOK | 2023-26 | -0.05 (-0.1) | +0.02 (+0.0) | -0.09 (-0.2) | +0.03 / -0.12 | 44 | 55 / 90 / 83 (20 / 10 / 6) | 52 / 54 / 33 (25 / 13 / 9) | 50 / 67 / 50 |
| basket8_ex_eur | 2000-26 | +0.22 (+1.1) | +0.38 (+2.0) | -0.03 (-0.2) | - / - | 51 | 52 / 54 / 53 (1305 / 691 / 487) | 49 / 49 / 50 (1294 / 686 / 476) | 51 / 53 / 49 |
| basket8_ex_eur | 2010-26 | +0.04 (+0.2) | +0.10 (+0.4) | -0.04 (-0.2) | - / - | 51 | 51 / 51 / 51 (834 / 439 / 312) | 51 / 47 / 50 (811 / 430 / 299) | 50 / 51 / 47 |
| basket8_ex_eur | 2016-26 | +0.03 (+0.1) | +0.32 (+1.1) | -0.23 (-0.8) | - / - | 52 | 52 / 53 / 52 (551 / 291 / 205) | 50 / 45 / 50 (500 / 265 / 183) | 50 / 51 / 49 |
| basket8_ex_eur | 2023-26 | -0.52 (-1.0) | -0.18 (-0.4) | -0.60 (-1.2) | - / - | 50 | 49 / 57 / 57 (184 / 99 / 69) | 47 / 47 / 46 (185 / 98 / 67) | 49 / 50 / 51 |

Basket accuracy pools the eight currencies' decisions (cross-correlated; no interval claimed). Pooled non-overlapping accuracy
inside WIDER is 52 / 54 / 53 % at 21 / 42 / 63 sessions against 49 / 49 / 50 % outside (2000-26) and 51 / 51 / 51 %
against 51 / 47 / 50 % in 2010-26: a coin in both classes. Per currency the Wilson intervals (in the csv) are about +-8 points
at 21 sessions; of the 162 currency x stream x horizon cells of 2000-26 and 2010-26, 4 exclude 50 % (SEK ungated at 21 sessions in 2000-26: 56 %, n=319; SEK wider at 21 sessions in 2000-26: 58 %, n=165; SEK ungated at 21 sessions in 2010-26: 57 %, n=199; NZD ungated at 63 sessions in 2010-26: 38 %, n=66),
which is what chance gives.

Spot only (no carry in the P&L):

| currency | period | (c) ungated SR (t) | (d) WIDER SR (t) | complement SR (t) | on-session SR WIDER / compl. | % WIDER |
|---|---|---|---|---|---|---|
| EUR | 2000-26 | +0.11 (+0.6) | +0.04 (+0.2) | +0.12 (+0.6) | +0.05 / +0.18 | 52 |
| EUR | 2010-26 | +0.42 (+1.7) | +0.21 (+0.8) | +0.42 (+1.7) | +0.27 / +0.66 | 60 |
| GBP | 2000-26 | +0.14 (+0.7) | +0.18 (+0.9) | +0.01 (+0.1) | +0.25 / +0.02 | 55 |
| GBP | 2010-26 | +0.22 (+0.9) | +0.29 (+1.2) | +0.02 (+0.1) | +0.40 / +0.03 | 53 |
| JPY | 2000-26 | +0.01 (+0.1) | +0.07 (+0.3) | -0.05 (-0.2) | +0.10 / -0.07 | 48 |
| JPY | 2010-26 | -0.12 (-0.5) | +0.03 (+0.1) | -0.21 (-0.8) | +0.04 / -0.29 | 50 |
| CHF | 2000-26 | +0.20 (+1.0) | -0.11 (-0.6) | +0.37 (+1.9) | -0.15 / +0.53 | 51 |
| CHF | 2010-26 | +0.15 (+0.6) | -0.12 (-0.5) | +0.31 (+1.3) | -0.15 / +0.48 | 57 |
| AUD | 2000-26 | +0.31 (+1.6) | +0.38 (+2.0) | +0.06 (+0.3) | +0.55 / +0.08 | 49 |
| AUD | 2010-26 | -0.03 (-0.1) | -0.04 (-0.2) | -0.01 (-0.0) | -0.06 / -0.00 | 43 |
| CAD | 2000-26 | -0.09 (-0.4) | -0.06 (-0.3) | -0.07 (-0.3) | -0.08 / -0.09 | 51 |
| CAD | 2010-26 | -0.14 (-0.6) | -0.17 (-0.7) | -0.04 (-0.2) | -0.22 / -0.06 | 55 |
| NZD | 2000-26 | -0.17 (-0.9) | -0.07 (-0.3) | -0.18 (-0.9) | -0.09 / -0.25 | 52 |
| NZD | 2010-26 | -0.35 (-1.4) | -0.34 (-1.4) | -0.17 (-0.7) | -0.48 / -0.23 | 50 |
| SEK | 2000-26 | +0.36 (+1.8) | +0.43 (+2.2) | +0.06 (+0.3) | +0.61 / +0.09 | 51 |
| SEK | 2010-26 | +0.48 (+2.0) | +0.37 (+1.5) | +0.30 (+1.2) | +0.50 / +0.46 | 56 |
| NOK | 2000-26 | -0.04 (-0.2) | -0.15 (-0.8) | +0.07 (+0.4) | -0.21 / +0.10 | 46 |
| NOK | 2010-26 | -0.14 (-0.6) | -0.23 (-0.9) | -0.00 (-0.0) | -0.35 / +0.00 | 42 |
| basket8_ex_eur | 2000-26 | +0.19 (+1.0) | +0.20 (+1.0) | +0.09 (+0.5) | - / - | 51 |
| basket8_ex_eur | 2010-26 | +0.02 (+0.1) | -0.04 (-0.2) | +0.06 (+0.2) | - / - | 51 |

Basket including EUR (9 currencies, spot + carry): gated +0.35 (t +1.8) / +0.15 / +0.32 / -0.30.

Sensitivities and the single robustness line (basket of 8 and EUR, spot + carry, Sharpe):

| variant | sample | 2000-26 ungated / WIDER / compl. | 2010-26 ungated / WIDER / compl. | 2016-26 ungated / WIDER / compl. | 2023-26 ungated / WIDER / compl. |
|---|---|---|---|---|---|
| ROBUSTNESS 6m change / 12m gap | basket of 8 | +0.22 / +0.37 / -0.02 | +0.13 / +0.09 / +0.11 | +0.14 / +0.28 / -0.05 | -0.18 / +0.16 / -0.49 |
| ROBUSTNESS 6m change / 12m gap | EUR | +0.12 / -0.03 / +0.20 | +0.32 / +0.02 / +0.46 | +0.15 / +0.06 / +0.18 | -0.41 / -0.23 / -0.35 |
| sensitivity 2x cost | basket of 8 | +0.20 / +0.36 / -0.05 | +0.02 / +0.07 / -0.06 | +0.01 / +0.30 / -0.25 | -0.55 / -0.21 / -0.63 |
| sensitivity 2x cost | EUR | +0.11 / +0.10 / +0.04 | +0.43 / +0.28 / +0.33 | +0.04 / +0.22 / -0.25 | -0.63 / -0.67 / -0.26 |
| sensitivity literal 1.2 pips SEK NOK | basket of 8 | +0.23 / +0.39 / -0.02 | +0.05 / +0.11 / -0.03 | +0.04 / +0.34 / -0.23 | -0.51 / -0.17 / -0.59 |
| sensitivity literal 1.2 pips SEK NOK | EUR | +0.11 / +0.11 / +0.04 | +0.43 / +0.29 / +0.33 | +0.05 / +0.22 / -0.24 | -0.62 / -0.66 / -0.25 |

The 6-month-change / 12-month-gap line gives the same picture (basket gated +0.37, t 1.91, in 2000-26; +0.09 in 2010-26
with a gap of -0.02). It is not eligible and was not used.

## 4. Step 3 - rotation placebo and the verdict
| sample | period | WIDER stream SR (t) | complement SR | gap G | placebo G mean / 95th pct | p(G_rot >= G) | mean on-session gap (p) | currencies with gap > 0 (p) |
|---|---|---|---|---|---|---|---|---|
| basket of 8, spot + carry (VERDICT) | 2000-26 | +0.38 (+1.98) | -0.03 | +0.42 | -0.02 / +0.42 | 0.056 | +0.27 (0.058) | 6 (0.17) |
| basket of 8, spot + carry (VERDICT) | 2010-26 | +0.10 (+0.41) | -0.04 | +0.14 | -0.00 / +0.52 | 0.332 | +0.07 (0.370) | 4 (0.59) |
| ADDED: same, 5,000 draws | 2000-26 | +0.38 (+1.98) | -0.03 | +0.42 | -0.01 / +0.42 | 0.051 | +0.27 (0.065) | 6 (0.17) |
| ADDED: same, 5,000 draws | 2010-26 | +0.10 (+0.41) | -0.04 | +0.14 | -0.00 / +0.54 | 0.328 | +0.07 (0.367) | 4 (0.61) |
| ADDED: same, literal 1.2 pips for SEK / NOK | 2000-26 | +0.39 (+2.04) | -0.02 | +0.42 | -0.02 / +0.42 | 0.054 | +0.27 (0.058) | 6 (0.17) |
| ADDED: same, literal 1.2 pips for SEK / NOK | 2010-26 | +0.11 (+0.46) | -0.03 | +0.15 | -0.00 / +0.52 | 0.326 | +0.07 (0.360) | 4 (0.59) |
| basket of 8, spot only | 2000-26 | +0.20 (+1.05) | +0.09 | +0.11 | -0.01 / +0.44 | 0.336 | +0.07 (0.334) | 6 (0.19) |
| basket of 8, spot only | 2010-26 | -0.04 (-0.17) | +0.06 | -0.10 | +0.01 / +0.51 | 0.624 | -0.09 (0.654) | 3 (0.83) |
| EUR alone, spot + carry | 2000-26 | +0.11 (+0.57) | +0.04 | +0.07 | -0.01 / +0.54 | 0.384 | +0.09 (0.384) | 1 (0.45) |
| EUR alone, spot + carry | 2010-26 | +0.29 (+1.17) | +0.33 | -0.04 | +0.01 / +0.52 | 0.584 | -0.15 (0.632) | 0 (1.00) |
| ROBUSTNESS LINE 6m change / 12m gap, basket of 8 | 2000-26 | +0.37 (+1.91) | -0.02 | +0.39 | -0.03 / +0.35 | 0.034 | +0.26 (0.028) | 6 (0.10) |
| ROBUSTNESS LINE 6m change / 12m gap, basket of 8 | 2010-26 | +0.09 (+0.37) | +0.11 | -0.02 | -0.03 / +0.45 | 0.480 | -0.02 (0.498) | 3 (0.82) |

G = Sharpe of the basket WIDER stream minus Sharpe of the basket complement stream. Rotating the class series against the
positions leaves the unconditional Sharpe of the rule in place and asks only whether the TIMING of the WIDER label matters.
Verdict by the frozen rule: (i) fail, (ii) pass, (iii) fail -> **FAILS**.

ADDED after the first run (outside the verdict) - eras:

| sample | P&L | period | ungated SR (t) | WIDER SR (t) | complement SR (t) | gap |
|---|---|---|---|---|---|---|
| basket of 8 | spot + carry | 2000-26 | +0.22 (+1.1) | +0.38 (+2.0) | -0.03 (-0.2) | +0.42 |
| basket of 8 | spot + carry | 2000-09 | +0.52 (+1.6) | +0.84 (+2.6) | -0.02 (-0.1) | +0.86 |
| basket of 8 | spot + carry | 2006-26 | +0.16 (+0.7) | +0.20 (+0.9) | +0.05 (+0.2) | +0.15 |
| basket of 8 | spot + carry | 2010-26 | +0.04 (+0.2) | +0.10 (+0.4) | -0.04 (-0.2) | +0.14 |
| basket of 8 | spot + carry | 2010-15 | +0.05 (+0.1) | -0.32 (-0.8) | +0.38 (+0.9) | -0.69 |
| basket of 8 | spot + carry | 2016-26 | +0.03 (+0.1) | +0.32 (+1.1) | -0.23 (-0.8) | +0.56 |
| EUR | spot + carry | 2000-26 | +0.11 (+0.6) | +0.11 (+0.6) | +0.04 (+0.2) | +0.07 |
| EUR | spot + carry | 2000-09 | -0.38 (-1.2) | -0.23 (-0.7) | -0.31 (-1.0) | +0.08 |
| EUR | spot + carry | 2006-26 | +0.32 (+1.5) | +0.14 (+0.7) | +0.32 (+1.5) | -0.18 |
| EUR | spot + carry | 2010-26 | +0.43 (+1.8) | +0.29 (+1.2) | +0.33 (+1.4) | -0.04 |
| EUR | spot + carry | 2010-15 | +1.07 (+2.6) | +0.40 (+1.0) | +1.14 (+2.8) | -0.74 |
| EUR | spot + carry | 2016-26 | +0.05 (+0.2) | +0.22 (+0.7) | -0.24 (-0.8) | +0.47 |
| basket of 8 | spot only | 2000-26 | +0.19 (+1.0) | +0.20 (+1.0) | +0.09 (+0.5) | +0.11 |
| basket of 8 | spot only | 2000-09 | +0.48 (+1.5) | +0.60 (+1.9) | +0.16 (+0.5) | +0.43 |
| basket of 8 | spot only | 2006-26 | +0.14 (+0.6) | +0.04 (+0.2) | +0.17 (+0.8) | -0.12 |
| basket of 8 | spot only | 2010-26 | +0.02 (+0.1) | -0.04 (-0.2) | +0.06 (+0.2) | -0.10 |
| basket of 8 | spot only | 2010-15 | +0.04 (+0.1) | -0.44 (-1.1) | +0.48 (+1.2) | -0.93 |
| basket of 8 | spot only | 2016-26 | +0.01 (+0.0) | +0.17 (+0.6) | -0.14 (-0.5) | +0.31 |
| EUR | spot only | 2000-26 | +0.11 (+0.6) | +0.04 (+0.2) | +0.12 (+0.6) | -0.09 |
| EUR | spot only | 2000-09 | -0.37 (-1.2) | -0.29 (-0.9) | -0.24 (-0.8) | -0.05 |
| EUR | spot only | 2006-26 | +0.31 (+1.4) | +0.06 (+0.3) | +0.41 (+1.9) | -0.35 |
| EUR | spot only | 2010-26 | +0.42 (+1.7) | +0.21 (+0.8) | +0.42 (+1.7) | -0.21 |
| EUR | spot only | 2010-15 | +1.06 (+2.6) | +0.38 (+0.9) | +1.16 (+2.8) | -0.78 |
| EUR | spot only | 2016-26 | +0.04 (+0.1) | +0.11 (+0.4) | -0.10 (-0.3) | +0.21 |

ADDED - is the gate a carry sort? Share of active sessions on which the position of rule (c) has the sign of `r_c - r_US`:

| currency | position has the sign of the rate differential: WIDER sessions | complement sessions | mean abs(r_c - r_US), % |
|---|---|---|---|
| EUR | 84 % | 15 % | 1.24 |
| GBP | 81 % | 34 % | 0.90 |
| JPY | 86 % | 23 % | 1.75 |
| CHF | 79 % | 20 % | 1.76 |
| AUD | 81 % | 17 % | 1.89 |
| CAD | 78 % | 33 % | 0.66 |
| NZD | 83 % | 27 % | 2.10 |
| SEK | 83 % | 23 % | 1.42 |
| NOK | 85 % | 26 % | 1.46 |

ADDED - spot and carry parts of the two basket streams (gross bp a year, before costs):

| period | WIDER stream: spot bp / year | WIDER stream: carry bp / year | complement: spot bp / year | complement: carry bp / year |
|---|---|---|---|---|
| 2000-26 | +72 | +57 | +38 | -42 |
| 2000-09 | +199 | +78 | +55 | -55 |
| 2006-26 | +21 | +49 | +65 | -41 |
| 2010-26 | -5 | +45 | +27 | -34 |
| 2010-15 | -126 | +38 | +159 | -33 |
| 2016-26 | +63 | +48 | -46 | -35 |

ADDED - benchmark, not a candidate: plain carry `sign(r_c - r_US)` with the same vol scale and monthly rebalance, basket of 8:

| period | plain carry basket SR (t) | corr. with the gated WIDER basket | alpha of the gated basket on carry, bp / year (t) |
|---|---|---|---|
| 2000-26 | +0.28 (+1.4) | 0.48 | +79 (+1.5) |
| 2000-09 | +0.82 (+2.6) | 0.50 | +138 (+1.6) |
| 2006-26 | -0.08 (-0.3) | 0.46 | +72 (+1.2) |
| 2010-26 | +0.02 (+0.1) | 0.48 | +29 (+0.4) |
| 2010-15 | -0.71 (-1.7) | 0.51 | +14 (+0.1) |
| 2016-26 | +0.44 (+1.4) | 0.46 | +38 (+0.4) |

In 2000-09 the WIDER stream earned more than carry alone (spot +199 bp a year next to +78 of carry; alpha on the carry
basket t +1.6): that decade was the one-way dollar decline with rate differentials widening in favour of AUD, NZD, SEK and GBP.
Since 2010 the spot part is -5 bp a year and only the carry accrual (+45) is left.

## 5. Leak checks (basket of 8, spot + carry; Sharpe 2000-26 / 2010-26)
| check | ungated 2000-26 / 2010-26 | WIDER | complement | gap WIDER - complement |
|---|---|---|---|---|
| as run (frozen rule, basket of 8, spot + carry) | +0.22 / +0.04 | +0.38 / +0.10 | -0.03 / -0.04 | +0.42 / +0.14 |
| (1) forward returns shuffled, mean of 40 seeds | -0.07 / -0.05 | -0.01 / -0.01 | -0.10 / -0.07 | +0.09 / +0.06 |
| (1) forward returns shuffled, sd of 40 seeds | +0.19 / +0.22 | +0.19 / +0.24 | +0.17 / +0.19 | +0.24 / +0.30 |
| (1) forward returns shuffled, mean of the first 5 seeds (first run) | -0.21 / -0.19 | -0.09 / -0.06 | -0.22 / -0.21 | +0.13 / +0.15 |
| (1) class labels shuffled by month, mean of 20 seeds | +0.22 / +0.04 | +0.11 / -0.03 | +0.20 / +0.04 | -0.09 / -0.07 |
| (1) class labels shuffled by month, sd of 20 seeds | +0.00 / +0.00 | +0.09 / +0.12 | +0.09 / +0.11 | +0.18 / +0.23 |
| (2) rate data lagged +1 month (month end + 60 d) | +0.10 / -0.08 | +0.29 / +0.10 | -0.13 / -0.20 | +0.43 / +0.30 |
| (2) stale placebo: rate data lagged +3 months | +0.26 / +0.26 | +0.21 / -0.01 | +0.19 / +0.38 | +0.02 / -0.39 |
| (2) stale placebo: rate data lagged +6 months | +0.22 / +0.07 | +0.32 / +0.15 | +0.01 / -0.04 | +0.31 / +0.19 |
| (3) look-ahead: no publication lag (stamped at month end) | +0.24 / +0.09 | +0.36 / +0.07 | +0.03 / +0.06 | +0.33 / +0.01 |
| (3) look-ahead: month average known at the start of its own month | +0.38 / +0.29 | +0.52 / +0.31 | +0.06 / +0.12 | +0.46 / +0.19 |
| (3) look-ahead: known one month before the month starts | +0.74 / +0.69 | +0.65 / +0.44 | +0.49 / +0.60 | +0.16 / -0.16 |
| (3) look-ahead: known two months before the month starts | +0.99 / +1.00 | +0.94 / +0.82 | +0.60 / +0.70 | +0.35 / +0.12 |

* (1) Shuffled forward returns: about zero (the small negative mean is costs plus the 0.19 s.d. of a 27-year Sharpe; the first
  run's five seeds happened to average -0.21 and I extended the check to 40). Class labels shuffled by month: the gap goes to
  -0.09 +- 0.18 (real +0.42), i.e. it vanishes; 2 s.d. of that shuffle is the size of the real gap.
* (2) One more month of lag changes nothing in the gap; three more months remove it, six more months bring three quarters of
  it back. A gap that returns when the data are half a year old is a slow state (carry regime), not information.
* (3) Look-ahead control: removing the publication lag changes nothing (+0.24 against +0.22 ungated), so the result does not sit on the
  edge of the lag; knowing the month's average one and two months early gives +0.74 and +0.99 (t 3.8 and 5.1): the harness exposes
  foresight, and rate differentials and currencies move together within the quarter, which is why the honest lag leaves little.
* Inputs: monthly interbank rates (lagged), H.10 prices, trailing realised volatility. No forward return enters a signal or a
  class. Current-vintage OECD rates (monthly averages are not revised in any way that matters).

## Caveats
* This arm tests the MECHANISM with a rate-differential trend rule; it cannot test the agreement rule on other currencies (no
  house score or validated positioning signal exists there). A failure of the mechanism does not prove the EUR pattern is
  chance, but together with section 2 (the pattern depends on how the gap is measured) nothing independent now supports it.
* Three-month interbank rates are not policy rates: in 2007-12 and March 2020 they carry credit and liquidity premia. Policy
  rates for nine central banks were not in the repo; the brief fixed the interbank rate as the primary measure for all.
* The verdict was a near miss on two thresholds; the reading above rests on the era split and the carry decomposition, both
  ADDED after the first run and therefore descriptive. The pre-registered answer is FAILS either way.
* H.10 is a noon New York fix. The basket weights currencies equally in position units, not in risk units. 2026 runs to 6 November.
