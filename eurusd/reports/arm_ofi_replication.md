# Arm P - ofi_replication: does arm K's residual order-flow lead exist on other dollar pairs? (round 4)

**ARM STATUS: FAILED. The lead does not replicate.** One pre-registered rule, one run, six new pairs.

Code: `src/eurusd/arms/ofi_replication.py` (`run(cost_pips=1.2)`; CLI `eur | download | build | run | leak`). Outputs in
`experiments/results/arms/`: `ofi_replication_positions.parquet` (EUR/USD stream of the frozen rule, OOS: `pos`, `fwd_bp`,
`net_bp`; saved as instructed although the arm failed - **do not stack it**), `ofi_replication_report.csv` (EUR/USD reference, six
pairs, basket; the same positions at 0.6 and 0 pips; columns `variant`, `group`, `cost_pips`, `final`, `verdict`, hit rates),
`ofi_replication_basket.parquet` (daily basket net / gross bp, per-pair positions and net bp, EUR/USD alongside),
`ofi_replication_pooled.csv`, `ofi_replication_leakchecks.csv`, `ofi_replication_coverage.csv` (pair x year),
`ofi_replication_tzcheck.csv`, `ofi_replication_data.json`, `ofi_replication_fitlog.json`, logs `logs/ofi_replication*.log|csv`.

## Verdict
Rule fixed in the module docstring before any new data: REPLICATES if the six-pair basket is positive in 2010-26 and in 2016-26,
pooled t >= 2, and at least 4 of 6 pairs are positive on 2010-26.

| criterion | result | pass |
|---|---|---|
| basket net Sharpe 2010-26 > 0 | +0.06 (t +0.24) | yes |
| basket net Sharpe 2016-26 > 0 | +0.16 (t +0.53) | yes |
| pooled t >= 2 (2010-26, clustered by day) | **0.46** (Stouffer z assuming independence 0.52) | **no** |
| at least 4 of 6 pairs positive 2010-26 | **3** (GBP, AUD, CAD; USDJPY is -0.00) | **no** |

**FAILS.** The six-pair estimate is indistinguishable from zero (mean pair Sharpe +0.05, hit rate 50.1% of 19,464 pair-days before
costs, 49.0% after). It is not a sign reversal either: gross of costs the basket is +0.24 (t 1.0). EUR/USD (+0.53) is the best of
seven on 2010-26, as it was for positioning in arm F: the pair a rule was found on is again the outlier. The incremental test was
not run (the brief runs it only on replication) and nothing is proposed for the live exposure.

## Frozen definition (written from arm K's code before any download; the only variant)
Full text in the module docstring (unchanged since STEP 0: SHA-256 of the module at that point `12bcc5c0...db9fd300`; the
docstring of the final file is byte-identical). Summary:
* Sessions as the feature store: hourly bars from 1-minute bid bars (UTC), session = [22:00 UTC, +24h), >= 10 hourly bars, not
  starting on a Saturday, rows from 2003.
* `ofi` of a session, from its **1-minute** bars: d_i = tick-rule sign of the close change (zero change -> last sign of the
  session), w_i = min(high_i - low_i, 30 pips of the pair), ofi = sum(w d) / sum(w). (The brief's paraphrase "weighted by absolute
  move, 5-minute bars" is not what arm K ran; the code is the definition.)
* Quality rule (arm K): `ofi` = NaN when the session has < 200 valid 5-minute returns or > 120 minutes of holes.
* Regressors, same session: ret_1d / rv_1d_bp, body_rel, close_in_range - 0.5 (feature-store definitions). 5-day means of all four
  (at least 3 of 5 sessions).
* Per test year, on rows with `label_end_5d` before 1 January: OLS without intercept of the 5-day ofi on the three 5-day
  regressors; residual / training sd, clipped at +-2, halved; target = **+**sign(z) when |z| > training median of |z|, else 0,
  times min(1, training-median rv_21d / rv_21d).
* Position = mean of the last five targets (1/5 tranches held five sessions). P&L on `fwd_1d`, 1.2 pips per unit turnover,
  `eurusd.wf` harness with its defaults (test years 2010-2026, 5 training years minimum).

Decisions taken in STEP 0 that the brief left open or that deviate from it:
* **History from 2003, not 2008.** The harness needs five calendar years before the first test year and EUR/USD trained on
  2003-2009; a 2008 start would have given no test year before 2013 unless the harness default were changed. NZDUSD exists on
  HistData only from August 2005, which still gives a 2010 test year (1,125 training rows; the others 1,790-1,809).
* M5 files are stored as asked, but the tick rule needs 1-minute bars, so the daily frame is computed from the zips at build time
  and cached in `data/processed/ofi_replication_daily_<pair>.parquet`.
* Pip 0.0001 (USDJPY 0.01); weight cap 30 pips of the pair; cost 1.2 pips of the pair = 0.87 bp GBP, 1.09 JPY, 1.56 AUD, 1.29 CHF,
  0.98 CAD, 1.75 NZD on average (EUR 1.02).
* Basket = mean of the six pairs' net bp per session. Pooled t = t of the daily mean of the six unit-variance P&L series.

Code changes after STEP 0, none touching features or the rule: period discovery on the HistData index (monthly 2026 links), a
timezone bug in `tz_check`, an equivalent rewrite of the basket's "pair has a stream this year" mask, `years_total`, and
`tz_check_bls` (added).

## EUR/USD reproduction (STEP 0)
This module rebuilds everything from `EURUSD_M1.parquet` with its own code. Against the feature store and arm K's cache: session
index identical; close, ret_1d, rv_1d_bp, rv_21d_bp, body_rel, close_in_range, fwd_1d, fwd_5d, ofi, ofi_5d, n_valid5 and the
quality flag all differ by 0.0 with no NaN mismatch. Against arm K's saved control-(a) stream: maximum absolute difference of the
positions 0.0, of the net P&L 0.0.

| | 2010-26 SR (t) | 2016-26 SR (t) | 2023-26 SR (t) | hit sign 2010-26 | years + |
|---|---|---|---|---|---|
| arm K control (a) | 0.5349 (2.228) | 0.4141 (1.384) | 0.6787 (1.351) | 51.1% | 13/17 |
| this module | 0.5349 (2.228) | 0.4141 (1.384) | 0.6787 (1.351) | 51.1% | 13/17 |

## New data
Source: HistData.com ASCII 1-minute bid bars, GBPUSD, USDJPY, AUDUSD, USDCHF, USDCAD (2003 .. 2026-11-06) and NZDUSD
(2005-08-12 .. 2026-11-06); 202 zips (23 yearly files, 21 for NZDUSD, plus the 11 monthly files of 2026 per pair), 1.5-second pauses, two requests at a time, no
failures; raw zips in `data/raw/histdata_<pair>/` (git-ignored). Publication lag: none needed, every feature of a session uses bars
stamped inside it and is known at its close. Processed: `data/processed/cross/ofi_<pair>_M5.parquet` (5-minute OHLC, UTC, float32,
21-24 MB each, 138 MB together - see the note at the end).

Cleaning: duplicate stamps (429-535 per pair) keep the last; prices outside [median / 2, 2 x median] of their file removed
(2 AUDUSD bars, 1 NZDUSD bar, none elsewhere); no stamp fell in a DST transition. Largest daily moves are real events (GBP
2016-06-23, CHF 2015-01-14, JPY / AUD / CAD / NZD October 2008).

| pair | 1-minute bars (m) | sessions | fail quality rule | of which 2003-09 | 2010-22 | 2023 | 2024-26 | fewest sessions in a year 2010-25 |
|---|---|---|---|---|---|---|---|---|
| GBPUSD | 8.39 | 6,187 | 144 | 19 | 8 | 114 | 3 | 258 |
| USDJPY | 8.39 | 6,189 | 140 | 17 | 7 | 113 | 3 | 258 |
| AUDUSD | 8.20 | 6,188 | 156 | 30 | 10 | 114 | 2 | 258 |
| USDCHF | 8.38 | 6,180 | 144 | 16 | 10 | 114 | 4 | 258 |
| USDCAD | 7.88 | 6,190 | 192 | 66 | 10 | 113 | 3 | 258 |
| NZDUSD | 7.29 | 5,505 | 138 | 12 | 11 | 114 | 1 | 258 |

Every pair has the same hole as EUR/USD (113-114 sessions closing between 20 February and 28 July 2023: hours missing in
HistData's 2023 file), where the signal is 0 (the pairs are active on 41-52% of the 2023 sessions instead of ~80%). Outside it at
most 3 sessions a year fail from 2008 on. Median valid 5-minute returns per session: 258-288 up to 2009 (USDCAD thinnest),
285-288 from 2010, 276-281 in 2023. Per pair and year: `ofi_replication_coverage.csv`.

Timezone, verified on each pair (stamps converted America/New_York -> UTC):

| pair | widest minute 11:00-16:00 UTC, first Fridays 2003-26: mode EDT (share) | mode EST (share) | share at 11:30 EDT (flat-EST signature) | payroll dates 2010-26: widest 5-minute bar is the release bar, EDT / EST | one hour early, EDT |
|---|---|---|---|---|---|
| GBPUSD | 12:30 (58%) | 13:30 (58%) | 2% | 76% / 68% | 5% |
| USDJPY | 12:30 (73%) | 13:30 (62%) | 3% | 87% / 75% | 4% |
| AUDUSD | 12:30 (65%) | 13:30 (57%) | 2% | 83% / 80% | 3% |
| USDCHF | 12:30 (64%) | 13:30 (55%) | 3% | 77% / 80% | 4% |
| USDCAD | 12:30 (57%) | 13:30 (57%) | 3% | 82% / 78% | 4% |
| NZDUSD | 12:30 (63%) | 13:30 (52%) | 3% | 80% / 79% | 4% |

The payroll spike sits at 12:30 UTC under US daylight time and at 13:30 UTC under standard time on all six pairs, never at 13:30
in summer or 12:30 in winter (0% in every cell but one: USDJPY, 1 summer Friday of 176), so the stamps are New York local time with DST, as for EUR/USD. Had they been flat
EST the summer spike would be at 11:30.

## Results at 1.2 pips, walk-forward 2010-2026 (each pair in its own quote direction)
Hit = share of active sessions with the right sign before costs / with positive net P&L (n active sessions).

| pair | 2010-26 SR (t) | 2016-26 SR (t) | 2023-26 SR (t) | SR 2010-15 | hit 2010-26 (n) | hit 2016-26 (n) | hit 2023-26 (n) | years + | gross SR 2010-26 | SR at 0.6 pips | turnover / yr |
|---|---|---|---|---|---|---|---|---|---|---|---|
| EUR/USD (reference, arm K) | +0.53 (+2.23) | +0.41 (+1.38) | +0.68 (+1.35) | +0.73 | 51.1% / 50.1% (3344) | 50.8% / 50.0% (2168) | 50.4% / 49.3% (743) | 13/17 | +0.62 | +0.58 | 30 |
| GBPUSD | +0.39 (+1.61) | +0.58 (+1.95) | +0.18 (+0.36) | +0.00 | 51.0% / 50.0% (3384) | 51.7% / 50.4% (2211) | 51.9% / 48.9% (756) | 12/17 | +0.45 | +0.42 | 30 |
| USDJPY | -0.00 (-0.00) | +0.09 (+0.30) | +0.42 (+0.83) | -0.15 | 50.0% / 49.2% (3314) | 50.0% / 49.4% (2098) | 47.0% / 46.6% (701) | 8/17 | +0.08 | +0.04 | 28 |
| AUDUSD | +0.12 (+0.49) | +0.22 (+0.73) | +0.43 (+0.85) | -0.05 | 49.7% / 48.7% (3114) | 50.5% / 49.4% (2038) | 51.4% / 49.7% (727) | 9/17 | +0.22 | +0.17 | 27 |
| USDCHF | -0.09 (-0.37) | -0.25 (-0.85) | +0.18 (+0.36) | +0.06 | 49.3% / 47.7% (3301) | 49.0% / 47.2% (2142) | 49.9% / 47.2% (754) | 7/17 | -0.01 | -0.05 | 28 |
| USDCAD | +0.31 (+1.29) | +0.44 (+1.46) | +0.48 (+0.96) | +0.11 | 50.9% / 50.0% (3258) | 51.7% / 50.7% (2088) | 54.0% / 51.9% (695) | 10/17 | +0.39 | +0.35 | 29 |
| NZDUSD | -0.42 (-1.74) | -0.53 (-1.76) | -0.81 (-1.61) | -0.25 | 49.7% / 48.5% (3093) | 49.6% / 48.3% (2039) | 50.6% / 49.4% (693) | 5/17 | -0.31 | -0.36 | 29 |
| **EW basket, six ex EUR** | **+0.06 (+0.24)** | **+0.16 (+0.53)** | **+0.21 (+0.42)** | -0.10 | 50.6% / 49.7% (4262 days) | 51.0% / 50.0% (2707) | 52.1% / 51.1% (890) | 11/17 | +0.24 | +0.15 | |

(Basket hit rate = share of days with positive basket P&L before / after costs. EUR/USD gross and 0.6-pip values recomputed with
this module; the 0.6-pip one equals arm K's.)

Pooled evidence:

| period | pairs positive of 6 | mean pair SR | basket SR (t) | pooled t, clustered by day (verdict) | Stouffer z (independent, upper bound) | pooled hit sign / net (pair-days) | EUR/USD SR | EUR rank of 7 | t(EUR - basket, unit vol) |
|---|---|---|---|---|---|---|---|---|---|
| 2010-26 | 3 | +0.05 | +0.06 (+0.24) | **+0.46** | +0.52 | 50.1% / 49.0% (19,464) | +0.53 | 1 | +1.5 |
| 2016-26 | 4 | +0.09 | +0.16 (+0.53) | +0.66 | +0.75 | 50.4% / 49.2% (12,616) | +0.41 | 3 | +0.7 |
| 2023-26 | 5 | +0.15 | +0.21 (+0.42) | +0.61 | +0.71 | 50.8% / 48.9% (4,326) | +0.68 | 1 | +0.8 |

The six P&L streams are nearly uncorrelated with each other (mean pairwise 0.05; AUD-NZD 0.26) and with EUR/USD (0.01-0.12), so
the clustered and the independent pooled t agree. Basket at 0.6 pips: +0.15 / +0.26 / +0.32; gross: +0.24 / +0.36 / +0.42.

Per year, net Sharpe:

| year | EUR/USD | GBPUSD | USDJPY | AUDUSD | USDCHF | USDCAD | NZDUSD | basket6 |
|---|---|---|---|---|---|---|---|---|
| 2010 | +1.39 | +0.08 | -0.11 | +0.66 | -0.84 | +0.98 | -0.17 | +0.17 |
| 2011 | +0.81 | +0.20 | +0.58 | +0.53 | +1.15 | -0.84 | -0.80 | +0.25 |
| 2012 | +0.99 | -0.59 | -0.33 | -1.17 | -0.70 | -0.16 | -0.04 | -0.98 |
| 2013 | +0.78 | -0.47 | -0.80 | +0.15 | -0.34 | +0.98 | +1.39 | +0.28 |
| 2014 | -0.13 | -1.00 | -0.08 | -1.53 | -0.73 | -0.85 | +0.26 | -1.16 |
| 2015 | +0.31 | +1.00 | -0.31 | -0.21 | +0.63 | +0.46 | -1.55 | +0.22 |
| 2016 | -0.26 | +0.40 | -1.39 | +1.98 | -0.65 | +1.98 | +1.34 | +1.29 |
| 2017 | +0.79 | +0.89 | +0.41 | -0.15 | -0.10 | +0.47 | -0.04 | +0.69 |
| 2018 | -0.47 | +0.59 | -0.04 | +0.21 | -2.10 | -0.04 | +0.27 | -0.21 |
| 2019 | +1.03 | +0.69 | +1.13 | +0.28 | -1.10 | +1.69 | -1.09 | +0.55 |
| 2020 | +0.24 | +0.50 | -0.43 | +0.77 | -1.23 | -0.78 | -2.81 | -1.41 |
| 2021 | -0.45 | -0.35 | +0.13 | -1.10 | +0.48 | +0.45 | +0.54 | +0.08 |
| 2022 | +1.26 | +2.24 | +0.20 | -1.47 | +0.76 | -0.12 | -1.77 | -0.14 |
| 2023 | +1.18 | +0.96 | -0.28 | +0.92 | +0.03 | +0.12 | -0.35 | +0.43 |
| 2024 | +0.09 | +0.86 | +0.60 | -0.30 | +0.95 | -0.35 | -0.33 | +0.53 |
| 2025 | +1.23 | -1.75 | +0.94 | +1.40 | +0.36 | +1.01 | -0.54 | +0.60 |
| 2026 | +0.03 | +0.62 | +0.25 | -0.53 | -0.62 | +1.31 | -1.94 | -0.71 |
| 2010-2015 | +0.73 | +0.00 | -0.15 | -0.05 | +0.06 | +0.11 | -0.25 | -0.10 |
| 2016-2022 | +0.30 | +0.77 | -0.09 | +0.12 | -0.52 | +0.44 | -0.38 | +0.13 |

Reading:
* Two pairs come close to EUR/USD (GBPUSD +0.39, USDCAD +0.31), one is clearly negative (NZDUSD -0.42, t -1.7), three are zero.
  No pair reaches t 2 in 2010-26. The strongest block of the EUR/USD record, 2010-2015 (+0.73), has no counterpart anywhere
  (-0.25 to +0.11, basket -0.10).
* EUR/USD is not statistically different from the six (t 1.5 / 0.7 / 0.8), so the simplest reading is one common effect near
  zero with EUR/USD as the lucky draw of seven on a rule that was already the best of 22 backtests. The mean of the seven Sharpes is
  0.12 / 0.14 / 0.22: that, not 0.53, is the planning number if one insists on having one, and the seven-pair basket including
  EUR/USD has t 0.8 (Sharpe 0.20 / 0.26 / 0.36).
* The estimates rise toward the recent window (5 of 6 positive in 2023-26, basket +0.21) but with t 0.4, and the verdict rule was
  written on 2010-26.

## Leak checks on the basket (`ofi_replication_leakchecks.csv`)
| check | 2010-26 | 2016-26 | 2023-26 |
|---|---|---|---|
| as run | +0.06 (t +0.24) | +0.16 | +0.21 |
| (1) shuffled labels, 20 draws (one permutation of the session calendar for all pairs; fwd_5d rebuilt), net: mean (sd) | -0.14 (0.23) | -0.22 (0.32) | -0.21 (0.38) |
| same, gross of costs | +0.02 (0.23) | -0.06 (0.32) | -0.05 (0.38) |
| (2) all features lagged +1 session | +0.10 (t +0.41) | +0.20 | +0.20 |
| (3) look-ahead control: features led 1 session | **-0.51 (t -2.13)** | -0.32 | -0.41 |
| (3) look-ahead control: features led 5 sessions (the label window) | **-2.25 (t -9.36)** | -1.53 | -1.85 |

* Shuffled labels give the cost drag and nothing else (first five draws: -0.25, +0.48, -0.07, +0.00, +0.09). The actual basket is
  0.8 null standard deviations above the shuffled mean: consistent with no effect.
* The one-session lag changes nothing, as expected for a 5-day average held five sessions; there is no closing-price artefact,
  and nothing to collapse.
* The harness lights up when the features see the label window, with |t| 9, so the alignment is tight. **The sign is negative**:
  inside the same week the residual flow goes against the return (every pair between -0.55 and -1.95 at a five-session lead in an
  ad-hoc per-pair run; EUR/USD -0.37, and +0.22 at a one-session lead in arm K's file). The likely reason is mechanical: the
  flow proxy is bounded while returns are not, so in the weeks with the largest moves the linear fit over-predicts the flow and
  the residual has the opposite sign of the move, and those weeks dominate P&L in bp. Whatever the reason, the rule's positive
  forward sign cannot come from seeing the label: contemporaneous information would push it the other way.
* Label in disguise: the inputs are four same-session price aggregates known at the close, and the fit does not use the label at
  all (the sign is the prior, the threshold a training median of |z|, the scale a training median of volatility).

## Temptations, written down and not run
1. Drop NZDUSD (shortest history, widest spread, the only clearly negative pair): the five-pair basket would look better.
2. Call it "a post-2016 effect" (4 of 6 positive, GBPUSD t 1.95) or "strengthening since 2023" (5 of 6).
3. Judge the majors at 0.6 pips or gross (shown as the protocol's sensitivity only; basket t stays near 1).
4. Risk-parity or dollar-direction-aligned basket weights; removing a common dollar factor from the flows.
5. Adopt the one-session lag (+0.10 instead of +0.06) or flip the sign after seeing the look-ahead control.
6. Change the residualisation (intercept, a non-linear term because the proxy saturates) or the 5-day window.
None was computed. Trial count for the research log: **1** (one rule, six pairs, one basket; cost sensitivities of the same positions).

## What this means
* Arm K's lead is closed: EUR/USD-only, best of 22, not confirmed on six independent pairs. It joins positioning (arm F) as an
  effect that lives on the pair it was found on, with the difference that here the cross-pair estimate is about zero rather than
  negative.
* `ofi_replication_positions.parquet` holds the EUR/USD stream (identical to arm K's control stream) for the record only. It
  should not enter `meta.combine`; the incremental test was not run.
* Caveats: bid bars only, no traded volume (the proxy measures the direction of quoting); the six pairs share the 2023 hole;
  NZDUSD trains on 4.4 years for 2010. None of this can turn a pooled t of 0.5 into 2.

## Housekeeping note
While this arm was running, commits `4b8d1a6` and `73e58e9` (not made by this arm) swept its in-progress files into git, including
the six `data/processed/cross/ofi_*_M5.parquet` files (138 MB) and an early copy of the module. `EURUSD_M5.parquet` is git-ignored
for size; the lead may want the same for `data/processed/cross/ofi_*_M5.parquet` (they are rebuilt by `build` from the zips).
