# Arm X: what the options market knows (`options_info`)

Code `src/eurusd/arms/options_info.py` (`run(cost_pips=1.2)`; `python src/eurusd/arms/options_info.py` fetches (cached), runs everything in about a
minute and rebuilds this file; `... options_info.py report` rebuilds the report only). Cleaned series with source columns:
`data/macro/options_info_rr25.csv`, `options_info_iv.csv`, `options_info_cftc_options.csv`, `options_info_iv_overlap_check.csv`; raw downloads in
`data/raw/options_info/` (git-ignored). Results in `experiments/results/arms/`: `options_info_positions.parquet` (daily stream of the final rule:
`pos`, `fwd_bp`, `net_bp`), `options_info_report.csv` (protocol table, every candidate, `variant`, `final`, plus the stale-signal books),
`options_info_votes.csv` (every signal x rule x horizon x mode x period), `options_info_{bar,bar_verdict,paired,candidates,controls,jpy_replication,
vrp_gate_log,book_diff,by_year,hit,incremental,pnl_corr,leakchecks,data_catalogue}.csv`, `options_info_signals.parquet`,
`options_info_stale{63,126}_positions.parquet` (placebo books), log `logs/options_info.log`.

The module docstring (data, lags, the 12 candidates with their signs and citations, the evaluation, the selection rule and the reading of the bar) was
written BEFORE any accuracy number was computed; only data-quality facts were known. Three things were ADDED after the first run and are marked where
they appear: the "agreement call on which a vote-type signal is silent" row, the books with a stale signal, and the daily P&L difference against the
agreement-rule book. None changes the selection.

## Verdict

1. **The round-5 bar is NOT met, by any of the 12 candidates.** No extra vote from the options market lifts the agreement rule by 3 points at both
   21 and 42 sessions in both 2010-26 and 2016-26 on non-overlapping decisions. The rule picked by the declared selection rule, the agreement rule
   confirmed by the risk-reversal skew (`and_rr_z_follow`), moves it by **+0.1 / -2.4 points at 21 sessions and +4.2 / +3.0 at 42** (2010-26 / 2016-26;
   59 % [50-67] n=125 against 59 % n=154 at 21 sessions), is **worse in 2023-26** (-3.5 and -3.2 points on 28 and 18 decisions) and at 42 sessions the
   copy that is **63 sessions stale gains more** (+5.4 / +5.5). It has the decisions (7.5 a year). Four separate failures.
2. **Standalone, no option signal carries directional information at one to three months.** Weekly decisions 2010-26, 21 / 42 / 63 sessions:
   risk-reversal skew followed 55 / 54 / 53 % (n=861; orthogonalised to spot 55 / 55 / 54 %), its one-month change 53 / 53 / 52 %, RR-against-spot
   divergence 55 / 57 / 55 % (n=287), implied-minus-realised vol 51 / 53 / 54 % (n=789) and its change 49 / 51 / 50 %, term-structure slope 51 / 54 / 55 %
   (n=631, ends 2022-02), options-only positioning 50 / 47 / 49 % (n=870) and 52 / 52 / 54 % for leveraged funds. Non-overlapping, the best 21-session
   cell is 56 % [49-63] (n=188) and every interval contains 50 %. The one cell that looks like something, the skew at 63 sessions non-overlapping
   (67 % [55-77], n=69), is 53 % on the weekly grid: a lucky phase of the greedy grid.
3. **The literature's sign for the skew level was wrong here, and so was the practitioner sign in any useful sense.** The PRIMARY reading declared
   from the literature (an extreme skew is a premium: fade |z| > 2) was right **37 % [25-51] of the time** (n=46 non-overlapping, 21 sessions; weekly
   44 / 43 / 36 %, n=72): after an extreme skew EUR/USD more often kept going. Following the skew at all times is the 55 % above. Both are consistent
   with what the literature says first: the risk reversal REACTS. Its daily change is +0.45 correlated with the same day's EUR/USD return, +0.19 with the
   previous day's and +0.03 with the next day's; its level has an R2 of 0.27 on the trailing one- and three-month spot return; and a skew that is
   21 sessions "from the future" scores 68 % - the skew knows the move once it has happened.
4. **The only thing that looks like information is a one-month VETO, and it is not established.** On weekly decisions, a 21-session agreement call
   that the skew contradicts (rule long while the risk reversal is below its one-year mean, or the reverse) was right **49.5 % (n=95)** in 2010-26,
   **41.5 % (n=53)** in 2016-26 and 33 % (n=12) in 2023-26, against 62 / 61 / 57 % when the skew confirms; confirmed minus contradicted
   +12.9 points [-2.0, +29.3], p 0.04, and +19.6 [-1.3, +38.8], p 0.03. For it: the gap is the same after removing the spot return from the skew
   (`rr_orth`: +11.8 / +15.6, p 0.04), it vanishes when the skew is 63 sessions stale (AND rule 59 %, the agreement rule's own level), and arm N's
   trend-confirmed agreement rule showed no such gain, so it is not "price confirms". Against it: it exists at 21 sessions only (+2.0 and +1.6 points
   at 42 and 63); on non-overlapping decisions the confirmed calls are 59 / 55 % (n=125 / 80), no better than the agreement rule (59 / 57 %), with
   the contradicted calls as their own stream at 49 % [38-61] (n=71) and 52 % (n=42), and for the orthogonalised skew the non-overlapping gap is
   +4 points in 2010-26 and -5 in 2016-26; the p-values are unadjusted across 11 candidates x 3 horizons x 2 periods (a Bonferroni threshold for 11
   candidates is 0.0045); the 95 weekly contradicted calls are about 25 independent months; and in money the confirmed-only book earns the SAME bp a
   day as the agreement book (+0.03 bp, Newey-West t 0.2): the higher Sharpe comes from holding 25 % fewer tranches that earned nothing, not from
   earning more. A lead for a paper control, not a result.
5. **Daily stream: passes the round-3 arithmetic, adds a variance cut, not a new return source.** `and_rr_z_follow` as a weekly-tranche book: net
   Sharpe **0.62 / 0.65 / 0.45** (t 2.57 / 2.16 / 0.91; agreement-rule book 0.52 / 0.51 / 0.43), deflated-Sharpe p 0.18 for 12 candidates, hit rate of
   its decisions 62 % / 61 % / 57 % (n=287 / 185 / 60), +64 / +54 / +32 bp a decision after costs. Three-way combination 0.60 / **0.70** / 0.42 against
   0.56 / 0.64 / 0.36 two-way and 0.57 / 0.64 / 0.41 with the plain agreement book; with the skew 63 sessions stale 0.65, 126 stale 0.61 on 2016-26, so
   three quarters of the +0.06 is timing-dependent. It is 0.92 correlated with the agreement-rule book (0.59 with `regime_trend`, 0.40 with
   `weak_signals`). +0.06 Sharpe on a combination is the size this project has called noise before (rates/stress: +0.03).
6. **Variance risk premium (Della Corte et al. sign: expensive insurance => EUR down): no.** 51 / 53 / 54 % standalone, 41 / 42 / 46 % in 2023-25
   (n=114), nothing as a vote (-0.1 points weekly), and the stale copies score higher than the live one. As a CONDITIONING variable: the agreement
   rule was right 62 / 70 / 72 % when insurance was cheap against its own year and 55 / 62 / 64 % when dear (weekly, 2010-26, n=181 / 169), but on
   non-overlapping decisions the gap is 58 vs 52 %, 57 vs 61 %, 66 vs 57 %, the walk-forward gate that chose "cheap" from 2012 on scored 58 / 66 / 68 %
   out of sample against 59 / 66 / 69 % for the ungated rule on the same span, and in 2023-25 the two sides are level (44 against 45 % at 21 sessions
   on 18 and 22 weekly calls). No.
7. **Term-structure slope (inverted curve => EUR up): a slow regime variable that ends in 2022.** 52 / 61 / 61 % weekly in 2016-22 but 58 / 59 / 61 %
   when 63 sessions stale; as a vote +5.9 / +9.6 points at 42 sessions with the 126-stale copy at +8.7 / +5.9, and -5.0 / +4.3 at 21. Undefined after
   2022-02-22, so it cannot be judged in 2023-26 and cannot run.
8. **CFTC options-only positioning: nothing, and probably a hedge book.** The options-only non-commercial net position is small (standard deviation
   1.6 % of futures open interest against 21 % for the futures net) and NEGATIVELY correlated with the futures position (-0.14; leveraged funds
   -0.31). Its z-score followed: 50 / 47 / 49 %; as a vote it lowers the agreement rule by 6 to 8 points on non-overlapping decisions. "Options
   traders disagree with futures traders" can never confirm the agreement rule (it is non-zero only when it opposes `cot_z52`, which the rule requires
   on its side; found after the first run, it is structural); standalone it is right 41 / 36 / 35 % (n=418), i.e. it is the futures signal with the
   sign flipped, and agreement calls on which options disagree with futures were as good (59 / 65 %, n=179) as the rest (60 / 65 %, n=208).
9. **Does the options market know something the three slow signals do not?** Not that this data can show. Skew, implied-minus-realised vol,
   vol-curve slope and option positioning are each at 49-55 % alone; the skew is the price move restated plus a possible one-month veto that fails
   the non-overlapping test; nothing extends coverage (outside the agreement 33-58 % at 21-42 sessions, live no better than stale); and the identical skew rules on
   USD/JPY and EUR/JPY score 46-51 %. **Recommendation: adopt nothing.** If a live skew feed is ever arranged (CME CVOL skew or an own FXE chain;
   this copy ends 2026-07-29, so nothing here can run today), the veto may be registered as a paper control `agreement_rr_veto` starting from zero.

## 1 Data: provenance, sign convention, gaps

| file                                     | column         |   rows | first      | last       | source                                                                                                        | fetched    |
|:-----------------------------------------|:---------------|-------:|:-----------|:-----------|:--------------------------------------------------------------------------------------------------------------|:-----------|
| data/macro/options_info_rr25.csv         | rr25_1m_eurusd |   5874 | 2003-10-02 | 2026-07-29 | https://raw.githubusercontent.com/GerardWu100/geographic-equity-rotation/main/data/RiskReversalData_Clean.csv | 2026-11-11 |
| data/macro/options_info_iv.csv           | atm_1m         |   5761 | 2000-01-25 | 2022-02-22 | https://raw.githubusercontent.com/frederikbachdk/FXVolTrading/master/data/EURUSD.csv                          | 2026-11-11 |
| data/macro/options_info_iv.csv           | atm_1y         |   5761 | 2000-01-25 | 2022-02-22 | https://raw.githubusercontent.com/frederikbachdk/FXVolTrading/master/data/EURUSD.csv                          | 2026-11-11 |
| data/macro/options_info_iv.csv           | evz            |   4360 | 2007-11-01 | 2025-03-11 | https://fred.stlouisfed.org/graph/fredgraph.csv?id=EVZCLS                                                     | 2026-11-11 |
| data/macro/options_info_iv.csv           | iv_1m          |   6525 | 2000-01-25 | 2025-03-11 | stitched                                                                                                      | 2026-11-11 |
| data/macro/options_info_cftc_options.csv | opt_nc_net     |   1453 | 1999-01-05 | 2026-11-03 | https://www.cftc.gov/files/dea/history/deahistfo*.zip                                                         | 2026-11-11 |
| data/macro/options_info_cftc_options.csv | opt_lev_net    |   1065 | 2006-06-13 | 2026-11-03 | https://www.cftc.gov/files/dea/history/fin_com_txt_2006_2016.zip, com_fin_txt_*.zip                           | 2026-11-11 |

All files were fetched on 2026-11-11 (HTTP 200 on every URL; cftc.gov needs a browser user-agent, FRED `curl --http1.1` without one). The two GitHub
files are third-party copies of vendor (Bloomberg) data: research use only, no licence, and no live continuation.

**Risk reversal.** 5874 EUR/USD values 2003-10-02 .. 2026-07-29; 76 further dates in the file have the yen pairs but no EUR/USD value (2003-05, 2007).
* Gaps of more than 5 calendar days: 2004-02-02 (10 d), 2004-04-26 (6 d), 2004-05-07 (8 d), 2004-05-17 (7 d), 2004-05-25 (8 d), 2004-07-15 (13 d), 2004-09-16 (7 d), 2005-03-02 (7 d); none after March 2005. Missing business days: 62 in 2004, 11 in 2005, 5 in 2007, none from 2008.
* Stale runs (>= 5 identical consecutive values): 19, the longest 10 sessions, the last one starting 2008-02-11. Until 2005 the series is
  quoted in steps of 0.05 (90-98 % of values), so short runs there are rounding, not missing updates. No stale run from 2008-03 on; the test period
  2010-26 has no gap and no stale run. The z-score window first fills in mid-2004, so the gaps only touch the pre-2010 warm-up.
* The 1-month tenor jumps when it first spans a dated event: -2.2 in five sessions into 2016-06-14 (UK referendum), -1.85 on 2017-04-06 and +2.56 on
  2017-04-24 (French election), -1.28 on 2016-11-09 (US election). These are event premia, not views on the trend; they are left in.
* No independent source of EUR/USD risk reversals is reachable (no ECB or FRED series, no second GitHub copy), so the cross-checks are indirect:
  (i) the sign convention, table below: every dated episode has the sign it should have under "positive = EUR calls over EUR puts";
  (ii) daily RR change against the store's NY-close EUR/USD return: +0.45 same day, +0.19 previous day, -0.02 two days before,
  +0.03 next day, +0.00 two days after - a series stamped a day late would show its peak at the previous day, one stamped early would
  correlate with the next day; the +0.19 with the previous day says the quote is taken before the NY close or reacts with a lag;
  (iii) the sister file from the same vendor (ATM vols) carries a spot column that equals the store's NY close of the SAME date: median absolute
  difference 2.0 pips on 4959 days, return correlation 0.993 same day, +0.002 / -0.010 at one day's lead / lag. So vendor dates
  are NY dates, and the one-calendar-day lag used here is conservative.
* After 2026-07-29 there is no value: every RR signal is undefined from the session of 2026-08-06 (5-session carry limit). The 2026 tests stop there.


**Sign-convention check** (value of the series on dates whose skew direction is known from the event):

| date       | episode                                                             | expected sign   |   RR 1M 25d |   change over 5 sessions |   EUR/USD 21-session return, % |
|:-----------|:--------------------------------------------------------------------|:----------------|------------:|-------------------------:|-------------------------------:|
| 2008-10-27 | Lehman aftermath, dollar squeeze, EUR/USD 1.60 -> 1.25              | -               |       -2.91 |                    -2.01 |                          -16   |
| 2010-06-04 | Greek crisis, EUR/USD at 1.19                                       | -               |       -3.15 |                    -0.23 |                           -5.4 |
| 2011-11-09 | Italian yields above 7 %, euro break-up fear                        | -               |       -4.19 |                    -0.48 |                           -0.8 |
| 2015-01-16 | day after the SNB floor exit, a week before ECB QE                  | -               |       -2.26 |                    -1.51 |                           -7.9 |
| 2016-06-14 | ahead of the UK referendum (1M tenor spans the vote)                | -               |       -3.34 |                    -2.15 |                           -1   |
| 2017-04-18 | ahead of the French election first round                            | -               |       -4.12 |                    -0.31 |                           -0.1 |
| 2017-04-24 | the day after the first round (Macron first): put premium collapses | up              |       -1.39 |                     2.73 |                            0.6 |
| 2020-03-09 | carry unwind / EUR short squeeze, EUR/USD spikes to 1.14-1.15       | +               |        2.9  |                     2.14 |                            4.4 |
| 2020-03-20 | dollar funding squeeze, EUR/USD back to 1.07                        | -               |       -2.95 |                    -3.27 |                           -0.8 |
| 2022-03-04 | Ukraine invasion, EUR/USD below 1.10                                | -               |       -3.5  |                    -2.88 |                           -4.5 |
| 2025-04-11 | April 2025 dollar sell-off, EUR/USD through 1.13                    | +               |        1.28 |                     1.05 |                            4.5 |

**Risk reversal by year** (EUR/USD column of the file):

|   year |   values |   missing business days |   runs of >= 5 identical values |   share quoted in 0.05 steps |   mean |   min |   max |
|-------:|---------:|------------------------:|--------------------------------:|-----------------------------:|-------:|------:|------:|
|   2003 |       62 |                       3 |                               1 |                         0.9  |   0.51 | -0.07 |  0.85 |
|   2004 |      200 |                      62 |                               2 |                         0.91 |   0.17 | -0.25 |  0.6  |
|   2005 |      249 |                      11 |                               7 |                         0.98 |  -0.14 | -0.7  |  0.35 |
|   2006 |      260 |                       0 |                               3 |                         0.58 |   0.23 | -0.25 |  0.76 |
|   2007 |      256 |                       5 |                               4 |                         0.45 |  -0.03 | -0.7  |  0.49 |
|   2008 |      262 |                       0 |                               2 |                         0.15 |  -0.48 | -2.91 |  0.73 |
|   2009 |      261 |                       0 |                               0 |                         0.05 |  -0.02 | -1.56 |  1.31 |
|   2010 |      261 |                       0 |                               0 |                         0.03 |  -1.42 | -3.14 | -0.16 |
|   2011 |      260 |                       0 |                               0 |                         0.07 |  -2.16 | -4.19 | -0.64 |
|   2012 |      261 |                       0 |                               0 |                         0.05 |  -0.99 | -2.38 | -0.07 |
|   2013 |      261 |                       0 |                               0 |                         0.07 |  -0.72 | -1.55 |  0.08 |
|   2014 |      261 |                       0 |                               0 |                         0.03 |  -0.56 | -1.1  | -0.27 |
|   2015 |      261 |                       0 |                               0 |                         0.07 |  -0.89 | -2.26 | -0.09 |
|   2016 |      261 |                       0 |                               0 |                         0.04 |  -0.49 | -3.34 |  1.04 |
|   2017 |      260 |                       0 |                               0 |                         0.07 |  -0.22 | -4.12 |  0.72 |
|   2018 |      261 |                       0 |                               0 |                         0.07 |  -0.37 | -1.29 |  0.74 |
|   2019 |      261 |                       0 |                               0 |                         0.05 |  -0.01 | -0.55 |  0.49 |
|   2020 |      262 |                       0 |                               0 |                         0.05 |   0.1  | -2.95 |  2.9  |
|   2021 |      261 |                       0 |                               0 |                         0.05 |  -0.09 | -0.62 |  0.32 |
|   2022 |      260 |                       0 |                               0 |                         0.1  |  -1.11 | -3.5  |  0.25 |
|   2023 |      260 |                       0 |                               0 |                         0.2  |  -0.37 | -1.34 | -0.03 |
|   2024 |      262 |                       0 |                               0 |                         0.09 |  -0.33 | -1.53 |  0.31 |
|   2025 |      261 |                       0 |                               0 |                         0.02 |   0.17 | -0.97 |  1.28 |
|   2026 |      150 |                       0 |                               0 |                         0.05 |  -0.28 | -1.46 |  1.67 |


**Implied vol and the stitch.** ATM 1M / 3M / 1Y: 5,761 rows 2000-01-25 .. 2022-02-22, no gap over 5 days, no stale run of 5 in the 1M quote (two
in 3M and four in 1Y, all 2003-06). EVZ: 4,360 values 2007-11-01 .. 2025-03-11 (169 holiday blanks dropped).
* Overlap check on 3596 common days (2007-11-01 .. 2022-02-22): level correlation 0.991; correlation of changes 0.65 daily (different fixing times and a
  thin ETF option market), 0.84 over 5 sessions, 0.94 over 21. EVZ / ATM-1M ratio: median 1.083, 5-95 % range 1.013-1.166; by year
  2007 1.05, 2008 1.06, 2009 1.06, 2010 1.08, 2011 1.11, 2012 1.09, 2013 1.08, 2014 1.09, 2015 1.07, 2016 1.09, 2017 1.09, 2018 1.09, 2019 1.11, 2020 1.09, 2021 1.06, 2022 1.05. The ratio is not constant, so a splice is an approximation.
* Stitch used: ATM 1M to 2022-02-22, then EVZ / 1.0517 (median ratio of the last 250 common sessions, i.e. fitted before the stitched segment).
  On those 250 sessions the mapped EVZ minus ATM is +0.02 +- 0.24 vol points; with the same ratio over the whole overlap +0.27 +- 0.50.
  The implied-minus-realised gap has a standard deviation of 1.35 vol points, so the splice error is about a fifth of the signal's scale.
* EVZ quality decays before it dies: share of days sitting in a run of >= 4 identical values - 2009 2 %, 2021 6 %, 2023 5 %, 2024 21 %, 2025 22 %; longest run 8 sessions (2024-10). The
  2023-25 part of every VRP signal therefore rests on a partly stale index. VRP signals are undefined from 2025-03-19; the term-structure slope
  (ATM file only) from 2022-03-02.
* Realised vol = the store's `rv_21d_bp` (sum of squared hourly returns, 21 sessions) annualised with sqrt(252), lagged one session to match the
  option stamp. Mean implied 8.9, realised 8.4, gap +0.40 vol points, positive on 61 % of sessions.


**CFTC options-only positioning.** 1453 weekly legacy rows 1999-01-05 .. 2026-11-03 and 1065 TFF rows 2006-06-13 .. 2026-11-03, every report date
present in both the combined and the futures-only file; combined open interest is never below futures-only open interest (0 violations).
Options add a median 16 % to futures open interest (2010-26). Options-only non-commercial net / futures OI has a standard deviation of 1.6 %
against 21 % for the futures-only net, and the two are correlated -0.14 (leveraged funds: -0.31): the option book is small and leans
against the futures book. Caveats: a delta-weighted aggregate (no strikes, expiries, put/call split); in the TFF report a trader's long futures
against short option delta moves into "spreading", so gross legs are not comparable across the two reports - only NET positions are used; the weeks of
the 2013, 2018-19 and 2025 shutdowns are in the history files with their original report dates although they were published late (same treatment
as `cot_z52` in the store; arm G showed the positioning signal is insensitive to it).

## 2 The 12 candidates and their priors (fixed before any result; citations in the module docstring and at the end)

|   # | signal          | family   | type   | prior (positive = long EUR/USD)                                                          |
|----:|:----------------|:---------|:-------|:-----------------------------------------------------------------------------------------|
|   1 | rr_fade_extreme | a        | vote   | - skew when |z252(RR)| > 2 (PRIMARY level sign: the skew is a premium, fade it)          |
|   2 | rr_z_follow     | a        | cont   | + z252(RR): skew towards EUR calls => up (labelled ALTERNATIVE)                          |
|   3 | rr_d21          | b        | cont   | + 21-session change of RR                                                                |
|   4 | rr_spot_div     | c        | vote   | + sign of the RR change when it is opposite to the spot move of the same 21 sessions     |
|   5 | rr_orth         | c        | cont   | + z252(RR) orthogonalised to the trailing 21- and 63-session spot return                 |
|   6 | vrp_level       | d        | cont   | - z252(implied minus realised vol): expensive insurance => EUR down (Della Corte et al.) |
|   7 | vrp_d21         | d        | cont   | - 21-session change of implied minus realised vol                                        |
|   8 | agree3_vrp_gate | d        | gate   | agreement rule only on the VRP side that was better in the training window               |
|   9 | ts_slope        | e        | cont   | + z252(ATM 1M - 1Y): inverted curve => EUR up (Ornelas & Mauad); ends 2022-02            |
|  10 | opt_nc_z52      | f        | cont   | + z52 of options-only non-commercial net / futures OI (follow, as cot_z52)               |
|  11 | opt_fut_div     | f        | vote   | + sign(opt_nc_z52) when it disagrees with sign(cot_z52)                                  |
|  12 | opt_lev_z52     | f        | cont   | + z52 of options-only leveraged-fund net / TFF futures OI (follow)                       |

Sign sources. Skew level, primary: Farhi, Fraiberger, Gabaix, Ranciere & Verdelhan, "Crash Risk in Currency Markets" (NBER w15062; 2015 version) -
the risk reversal prices disaster risk, moves with the currency contemporaneously, and its level is a premium; Brunnermeier, Nagel & Pedersen,
"Carry Trades and Currency Crashes" (NBER Macroeconomics Annual 2008) - the price of crash insurance rises after the crash. I could reach the
abstracts and summaries only (the regression tables were not readable from here), so the primary sign rests on my reading of these two papers.
VRP: Della Corte, Ramadorai & Sarno, "Volatility risk premia and exchange rate predictability" (JFE 120, 2016) - sign verified from the abstract
(cheap insurance appreciates, expensive depreciates, over the next month, spot-driven); a cross-sectional result used here as a time-series analogue.
Londono & Zhou (JFE 124, 2017) - sign not verifiable, not used. Slope: Ornelas & Mauad, "Implied volatility term structure and exchange rate
predictability" (Int. J. Forecasting 35, 2019) - developed currencies: buy low slope, sell high slope; slope read as long minus short tenor, not
verified in the full text (bcb.gov.br is outside the session's network). Options-only positioning and the two divergence votes: no citation.
The gate's side (candidate 8) was taken from the training window, as declared.

## 3 Reconciliation with arm N

The agreement rule rebuilt here (non-overlapping decisions; accuracy % [Wilson 95 %] n (decisions a year)):

| period   | 10 sessions               | 21 sessions              | 42 sessions             | 63 sessions             |
|:---------|:--------------------------|:-------------------------|:------------------------|:------------------------|
| 2010-26  | 56 [50-62] n=291 (17.3/y) | 59 [51-66] n=156 (9.3/y) | 61 [50-70] n=89 (5.3/y) | 72 [60-82] n=61 (3.7/y) |
| 2016-26  | 53 [46-61] n=178 (16.5/y) | 57 [47-67] n=96 (8.9/y)  | 59 [46-71] n=56 (5.2/y) | 71 [55-83] n=38 (3.6/y) |
| 2023-26  | 54 [42-66] n=63 (16.6/y)  | 60 [44-74] n=35 (9.3/y)  | 45 [26-66] n=20 (5.4/y) | 50 [27-73] n=14 (3.9/y) |

Arm N reports 56 / 59 / 61 / 72 % on n = 291 / 156 / 89 / 61 for 2010-26: reproduced exactly (2016-26: 53 / 57 / 59 / 71 %, 2023-26: 54 / 60 / 45 / 50 %).

## 4 Standalone accuracy of each signal (direction = sign of the vote)


**Non-overlapping decisions, 2010-26** (accuracy % [Wilson 95 %] n (decisions a year)):

| signal          | h 21                      | h 42                     | h 63                    |
|:----------------|:--------------------------|:-------------------------|:------------------------|
| rr_fade_extreme | 37 [25-51] n=46 (2.7/y)   | 45 [30-62] n=33 (2.0/y)  | 44 [27-63] n=25 (1.5/y) |
| rr_z_follow     | 53 [46-60] n=206 (12.3/y) | 50 [40-59] n=103 (6.2/y) | 67 [55-77] n=69 (4.2/y) |
| rr_d21          | 53 [46-60] n=206 (12.3/y) | 48 [38-57] n=103 (6.2/y) | 59 [48-70] n=69 (4.2/y) |
| rr_spot_div     | 52 [44-60] n=155 (9.2/y)  | 52 [41-62] n=89 (5.3/y)  | 57 [45-69] n=61 (3.7/y) |
| rr_orth         | 50 [43-57] n=206 (12.3/y) | 51 [42-61] n=103 (6.2/y) | 61 [49-72] n=69 (4.2/y) |
| vrp_level       | 56 [49-63] n=188 (11.2/y) | 49 [39-59] n=94 (5.6/y)  | 56 [43-67] n=63 (3.8/y) |
| vrp_d21         | 45 [38-52] n=188 (11.2/y) | 45 [35-55] n=94 (5.6/y)  | 54 [42-66] n=63 (3.8/y) |
| agree3_vrp_gate | -                         | -                        | -                       |
| ts_slope        | 51 [43-59] n=151 (9.0/y)  | 57 [45-67] n=76 (4.6/y)  | 51 [38-64] n=51 (3.1/y) |
| opt_nc_z52      | 46 [40-53] n=208 (12.4/y) | 43 [34-53] n=104 (6.2/y) | 51 [39-62] n=69 (4.2/y) |
| opt_fut_div     | 45 [37-54] n=133 (7.9/y)  | 43 [33-54] n=79 (4.7/y)  | 38 [27-51] n=55 (3.3/y) |
| opt_lev_z52     | 52 [46-59] n=208 (12.4/y) | 54 [44-63] n=104 (6.2/y) | 51 [39-62] n=69 (4.2/y) |

**Non-overlapping decisions, 2016-26** (accuracy % [Wilson 95 %] n (decisions a year)):

| signal          | h 21                      | h 42                    | h 63                    |
|:----------------|:--------------------------|:------------------------|:------------------------|
| rr_fade_extreme | 41 [26-59] n=29 (2.7/y)   | 50 [31-69] n=22 (2.1/y) | 47 [26-69] n=17 (1.6/y) |
| rr_z_follow     | 50 [42-59] n=131 (12.2/y) | 51 [39-63] n=65 (6.1/y) | 70 [56-82] n=44 (4.2/y) |
| rr_d21          | 49 [40-57] n=131 (12.2/y) | 43 [32-55] n=65 (6.1/y) | 59 [44-72] n=44 (4.2/y) |
| rr_spot_div     | 52 [42-61] n=99 (9.2/y)   | 59 [46-71] n=56 (5.2/y) | 64 [48-77] n=39 (3.7/y) |
| rr_orth         | 48 [40-57] n=131 (12.2/y) | 52 [40-64] n=65 (6.1/y) | 61 [47-74] n=44 (4.2/y) |
| vrp_level       | 56 [47-65] n=113 (10.5/y) | 45 [32-58] n=56 (5.2/y) | 53 [37-68] n=38 (3.6/y) |
| vrp_d21         | 44 [35-53] n=113 (10.5/y) | 45 [32-58] n=56 (5.2/y) | 50 [35-65] n=38 (3.6/y) |
| agree3_vrp_gate | -                         | -                       | -                       |
| ts_slope        | 51 [40-62] n=76 (7.1/y)   | 61 [45-74] n=38 (3.6/y) | 54 [35-71] n=26 (2.5/y) |
| opt_nc_z52      | 46 [38-54] n=133 (12.4/y) | 44 [33-56] n=66 (6.2/y) | 57 [42-70] n=44 (4.2/y) |
| opt_fut_div     | 44 [34-55] n=79 (7.3/y)   | 46 [33-60] n=48 (4.5/y) | 38 [24-55] n=34 (3.2/y) |
| opt_lev_z52     | 50 [41-58] n=133 (12.4/y) | 52 [40-63] n=66 (6.2/y) | 55 [40-68] n=44 (4.2/y) |

**Non-overlapping decisions, 2023-26** (accuracy % [Wilson 95 %] n (decisions a year)):

| signal          | h 21                     | h 42                    | h 63                    |
|:----------------|:-------------------------|:------------------------|:------------------------|
| rr_fade_extreme | 50 [24-76] n=10 (2.7/y)  | 62 [31-86] n=8 (2.2/y)  | 60 [23-88] n=5 (1.4/y)  |
| rr_z_follow     | 40 [27-55] n=45 (12.0/y) | 45 [27-65] n=22 (6.0/y) | 67 [42-85] n=15 (4.2/y) |
| rr_d21          | 49 [35-63] n=45 (12.0/y) | 55 [35-73] n=22 (6.0/y) | 53 [30-75] n=15 (4.2/y) |
| rr_spot_div     | 53 [37-69] n=34 (9.0/y)  | 60 [39-78] n=20 (5.4/y) | 75 [47-91] n=12 (3.3/y) |
| rr_orth         | 40 [27-55] n=45 (12.0/y) | 45 [27-65] n=22 (6.0/y) | 73 [48-89] n=15 (4.2/y) |
| vrp_level       | 52 [34-69] n=27 (7.2/y)  | 38 [18-64] n=13 (3.5/y) | 56 [27-81] n=9 (2.5/y)  |
| vrp_d21         | 41 [25-59] n=27 (7.2/y)  | 38 [18-64] n=13 (3.5/y) | 67 [35-88] n=9 (2.5/y)  |
| agree3_vrp_gate | -                        | -                       | -                       |
| ts_slope        | -                        | -                       | -                       |
| opt_nc_z52      | 38 [26-53] n=47 (12.5/y) | 43 [26-63] n=23 (6.2/y) | 47 [25-70] n=15 (4.2/y) |
| opt_fut_div     | 42 [26-61] n=26 (6.9/y)  | 53 [30-75] n=15 (4.1/y) | 45 [21-72] n=11 (3.1/y) |
| opt_lev_z52     | 38 [26-53] n=47 (12.5/y) | 39 [22-59] n=23 (6.2/y) | 67 [42-85] n=15 (4.2/y) |

**Weekly decisions, 2010-26** (accuracy % [Newey-West effective-n interval] n; live, then 63 and 126 sessions stale):

| signal          | live 21          | live 42          | live 63          | stale63 21   | stale63 42   | stale63 63   | stale126 21   | stale126 42   | stale126 63   |
|:----------------|:-----------------|:-----------------|:-----------------|:-------------|:-------------|:-------------|:--------------|:--------------|:--------------|
| rr_fade_extreme | 44 [31-59] n=72  | 43 [25-63] n=72  | 36 [20-56] n=72  | 38 n=87      | 31 n=87      | 33 n=87      | 39 n=79       | 50 n=76       | 59 n=74       |
| rr_z_follow     | 55 [50-60] n=861 | 54 [48-60] n=861 | 53 [46-60] n=861 | 51 n=870     | 51 n=866     | 51 n=862     | 47 n=870      | 46 n=866      | 45 n=862      |
| rr_d21          | 53 [49-57] n=859 | 53 [49-57] n=859 | 52 [48-56] n=859 | 50 n=867     | 50 n=863     | 51 n=860     | 54 n=862      | 51 n=858      | 53 n=854      |
| rr_spot_div     | 55 [48-62] n=287 | 57 [50-64] n=287 | 55 [47-62] n=287 | 48 n=299     | 48 n=297     | 50 n=296     | 59 n=279      | 56 n=279      | 60 n=278      |
| rr_orth         | 55 [50-60] n=861 | 55 [49-61] n=861 | 54 [47-61] n=861 | 50 n=870     | 51 n=866     | 51 n=862     | 49 n=870      | 48 n=866      | 48 n=862      |
| vrp_level       | 51 [46-56] n=789 | 53 [48-58] n=789 | 54 [48-59] n=789 | 49 n=802     | 51 n=802     | 53 n=802     | 58 n=815      | 57 n=815      | 56 n=815      |
| vrp_d21         | 49 [44-53] n=789 | 51 [47-55] n=789 | 50 [46-54] n=789 | 48 n=802     | 50 n=802     | 49 n=802     | 54 n=815      | 54 n=815      | 53 n=815      |
| agree3_vrp_gate | -                | -                | -                | -            | -            | -            | -             | -             | -             |
| ts_slope        | 51 [45-56] n=631 | 54 [47-61] n=631 | 55 [47-63] n=631 | 59 n=644     | 59 n=644     | 59 n=644     | 54 n=656      | 56 n=656      | 58 n=656      |
| opt_nc_z52      | 50 [45-55] n=870 | 47 [42-53] n=866 | 49 [42-56] n=862 | 54 n=870     | 55 n=866     | 58 n=862     | 48 n=870      | 49 n=866      | 50 n=862      |
| opt_fut_div     | 41 [34-49] n=418 | 36 [28-44] n=416 | 35 [28-44] n=412 | 50 n=410     | 52 n=410     | 54 n=410     | 50 n=414      | 51 n=414      | 51 n=410      |
| opt_lev_z52     | 52 [48-57] n=870 | 52 [46-58] n=866 | 54 [47-60] n=862 | 53 n=870     | 54 n=866     | 55 n=862     | 49 n=870      | 48 n=866      | 47 n=862      |

**Weekly decisions, 2016-26** (accuracy % [Newey-West effective-n interval] n; live, then 63 and 126 sessions stale):

| signal          | live 21          | live 42          | live 63          | stale63 21   | stale63 42   | stale63 63   | stale126 21   | stale126 42   | stale126 63   |
|:----------------|:-----------------|:-----------------|:-----------------|:-------------|:-------------|:-------------|:--------------|:--------------|:--------------|
| rr_fade_extreme | 54 [37-70] n=48  | 50 [28-72] n=48  | 42 [22-65] n=48  | 38 n=48      | 31 n=48      | 31 n=48      | 28 n=47       | 39 n=44       | 57 n=42       |
| rr_z_follow     | 54 [48-60] n=550 | 54 [47-61] n=550 | 54 [46-62] n=550 | 52 n=559     | 52 n=555     | 54 n=551     | 48 n=559      | 48 n=555      | 46 n=551      |
| rr_d21          | 51 [46-56] n=548 | 51 [46-55] n=548 | 51 [46-55] n=548 | 50 n=556     | 49 n=552     | 51 n=549     | 54 n=555      | 53 n=551      | 55 n=547      |
| rr_spot_div     | 55 [47-63] n=175 | 59 [50-67] n=175 | 55 [46-63] n=175 | 49 n=180     | 48 n=178     | 48 n=177     | 60 n=171      | 58 n=171      | 64 n=170      |
| rr_orth         | 55 [49-61] n=550 | 57 [49-64] n=550 | 55 [46-63] n=550 | 51 n=559     | 52 n=555     | 51 n=551     | 50 n=559      | 50 n=555      | 48 n=551      |
| vrp_level       | 51 [44-57] n=478 | 53 [46-60] n=478 | 53 [46-60] n=478 | 49 n=491     | 51 n=491     | 55 n=491     | 55 n=504      | 54 n=504      | 53 n=504      |
| vrp_d21         | 46 [41-52] n=478 | 49 [43-54] n=478 | 48 [43-53] n=478 | 50 n=491     | 50 n=491     | 50 n=491     | 56 n=504      | 54 n=504      | 55 n=504      |
| agree3_vrp_gate | -                | -                | -                | -            | -            | -            | -             | -             | -             |
| ts_slope        | 52 [45-59] n=320 | 61 [52-69] n=320 | 61 [50-70] n=320 | 58 n=333     | 59 n=333     | 61 n=333     | 54 n=345      | 52 n=345      | 58 n=345      |
| opt_nc_z52      | 50 [44-56] n=559 | 49 [42-56] n=555 | 51 [42-60] n=551 | 55 n=559     | 56 n=555     | 60 n=551     | 48 n=559      | 49 n=555      | 51 n=551      |
| opt_fut_div     | 42 [33-52] n=242 | 38 [28-49] n=240 | 36 [26-46] n=236 | 50 n=236     | 53 n=236     | 53 n=236     | 47 n=246      | 51 n=246      | 52 n=242      |
| opt_lev_z52     | 54 [48-60] n=559 | 51 [45-58] n=555 | 53 [45-61] n=551 | 52 n=559     | 51 n=555     | 53 n=551     | 47 n=559      | 45 n=555      | 44 n=551      |

**Weekly decisions, 2023-26** (accuracy % [Newey-West effective-n interval] n; live, then 63 and 126 sessions stale):

| signal          | live 21          | live 42          | live 63          | stale63 21   | stale63 42   | stale63 63   | stale126 21   | stale126 42   | stale126 63   |
|:----------------|:-----------------|:-----------------|:-----------------|:-------------|:-------------|:-------------|:--------------|:--------------|:--------------|
| rr_fade_extreme | 56 [29-79] n=18  | 56 [17-88] n=18  | 33 [9-72] n=18   | 20 n=15      | 40 n=15      | 40 n=15      | 14 n=14       | 9 n=11        | 33 n=9        |
| rr_z_follow     | 49 [39-60] n=186 | 47 [37-57] n=186 | 50 [39-61] n=186 | 53 n=195     | 48 n=191     | 48 n=187     | 50 n=195      | 46 n=191      | 41 n=187      |
| rr_d21          | 52 [43-60] n=186 | 47 [37-57] n=186 | 46 [37-55] n=186 | 48 n=193     | 51 n=189     | 45 n=186     | 56 n=193      | 56 n=189      | 55 n=185      |
| rr_spot_div     | 62 [48-74] n=50  | 70 [55-82] n=50  | 58 [42-72] n=50  | 45 n=53      | 57 n=51      | 56 n=50      | 63 n=46       | 52 n=46       | 69 n=45       |
| rr_orth         | 52 [42-62] n=186 | 49 [40-59] n=186 | 53 [42-63] n=186 | 50 n=195     | 46 n=191     | 42 n=187     | 51 n=195      | 47 n=191      | 43 n=187      |
| vrp_level       | 41 [31-53] n=114 | 42 [32-53] n=114 | 46 [32-60] n=114 | 54 n=127     | 59 n=127     | 64 n=127     | 53 n=140      | 52 n=140      | 50 n=140      |
| vrp_d21         | 45 [36-54] n=114 | 40 [32-50] n=114 | 39 [30-48] n=114 | 48 n=127     | 55 n=127     | 54 n=127     | 60 n=140      | 52 n=140      | 56 n=140      |
| agree3_vrp_gate | -                | -                | -                | -            | -            | -            | -             | -             | -             |
| ts_slope        | -                | -                | -                | -            | -            | -            | -             | -             | -             |
| opt_nc_z52      | 45 [36-55] n=195 | 42 [32-53] n=191 | 41 [28-55] n=187 | 50 n=195     | 49 n=191     | 55 n=187     | 51 n=195      | 53 n=191      | 59 n=187      |
| opt_fut_div     | 45 [29-61] n=83  | 43 [28-60] n=81  | 35 [22-50] n=77  | 49 n=73      | 56 n=73      | 55 n=73      | 56 n=85       | 65 n=85       | 68 n=81       |
| opt_lev_z52     | 50 [41-59] n=195 | 52 [44-61] n=191 | 52 [43-62] n=187 | 50 n=195     | 41 n=191     | 42 n=187     | 47 n=195      | 50 n=191      | 44 n=187      |

Reading. The up-share of 21-session returns on the weekly grid is 48 % in 2010-26, and every signal is long 47-58 % of the time, so "chance" is
50 % for all of them. Nothing clears it from above: the weekly intervals (already generous for overlapping holds) contain 50 % except the lower edge of the
two skew signals at 21 sessions (50-60 %), and those fall to 51 % when 63 sessions stale and 45-49 % when 126 stale, to 47-53 % in 2023-26, and to
53 % and 50 % on non-overlapping decisions. `rr_fade_extreme` (the primary sign) is BELOW chance: 37 % [25-51], n=46. `opt_fut_div` is below chance
because, where it votes, it is minus the futures-positioning sign.

## 5 Round 7 controls: is it new, or the price move restated?

Correlations on 2010-26 sessions (Pearson, of the continuous variable behind each signal; `sign_agree_*` = share of sessions on which the vote has the sign of that old input):

| signal          | variable        | last       |   votes_2010-26 |   share_long |   sign_flips_per_year |   corr_cot_z52 |   corr_d_spread2y_20 |   corr_house_score |   corr_ret_21d |   corr_ret_63d |   r2_on_spot_21_63 |   sign_agree_cot |   sign_agree_spr |   sign_agree_house |
|:----------------|:----------------|:-----------|----------------:|-------------:|----------------------:|---------------:|---------------------:|-------------------:|---------------:|---------------:|-------------------:|-----------------:|-----------------:|-------------------:|
| rr_fade_extreme | u_rr_z_neg      | 2026-08-05 |            0.09 |         0.8  |                  7.89 |          -0.31 |                -0.22 |              -0.28 |          -0.45 |          -0.48 |               0.27 |             0.36 |             0.36 |               0.33 |
| rr_z_follow     | rr_z_follow     | 2026-08-05 |            0.98 |         0.55 |                 10.95 |           0.31 |                 0.22 |               0.28 |           0.45 |           0.48 |               0.27 |             0.66 |             0.58 |               0.6  |
| rr_d21          | rr_d21          | 2026-08-05 |            0.98 |         0.5  |                 27.31 |          -0.03 |                 0.13 |               0.16 |           0.37 |           0.06 |               0.17 |             0.49 |             0.57 |               0.56 |
| rr_spot_div     | rr_d21          | 2026-08-05 |            0.33 |         0.54 |                 43.34 |          -0.03 |                 0.13 |               0.16 |           0.37 |           0.06 |               0.17 |             0.3  |             0.4  |               0.4  |
| rr_orth         | rr_orth         | 2026-08-05 |            0.98 |         0.58 |                 14.52 |           0.14 |                 0.08 |               0.16 |           0.08 |           0.19 |               0.04 |             0.61 |             0.52 |               0.57 |
| vrp_level       | vrp_level       | 2025-03-18 |            0.9  |         0.52 |                 23.86 |           0.06 |                 0.03 |               0.13 |           0.11 |          -0.07 |               0.04 |             0.51 |             0.46 |               0.56 |
| vrp_d21         | vrp_d21         | 2025-03-18 |            0.9  |         0.49 |                 29.33 |           0    |                 0.02 |               0.03 |           0.08 |          -0.04 |               0.02 |             0.49 |             0.48 |               0.51 |
| ts_slope        | ts_slope        | 2022-03-01 |            0.72 |         0.47 |                 13.77 |           0.09 |                 0.09 |               0.09 |          -0.16 |          -0.19 |               0.04 |             0.53 |             0.53 |               0.54 |
| opt_nc_z52      | opt_nc_z52      | 2026-11-05 |            1    |         0.49 |                  8.24 |           0.11 |                 0.03 |               0.11 |          -0.02 |           0    |               0    |             0.52 |             0.51 |               0.53 |
| opt_fut_div     | u_opt_minus_fut | 2026-11-05 |            0.48 |         0.47 |                 10.2  |          -0.74 |                -0.14 |              -0.33 |          -0.3  |          -0.48 |               0.24 |             0    |             0.47 |               0.38 |
| opt_lev_z52     | opt_lev_z52     | 2026-11-05 |            1    |         0.47 |                  8.3  |           0.1  |                 0.01 |               0.02 |           0.03 |           0.06 |               0    |             0.54 |             0.51 |               0.51 |

**Raw against orthogonalised, 2010-26** (weekly decisions, accuracy % n; `sa` = standalone, `and` = extra vote on the agreement rule):

| signal          | sa 21    | sa 42    | sa 63    | sa orth 21   | sa orth 42   | sa orth 63   | and 21   | and 42   | and 63   | and orth 21   | and orth 42   | and orth 63   |
|:----------------|:---------|:---------|:---------|:-------------|:-------------|:-------------|:---------|:---------|:---------|:--------------|:--------------|:--------------|
| rr_fade_extreme | 44 n=72  | 43 n=72  | 36 n=72  | 45 n=861     | 45 n=861     | 46 n=861     | 50 n=6   | 83 n=6   | 67 n=6   | 51 n=134      | 63 n=134      | 66 n=134      |
| rr_z_follow     | 55 n=861 | 54 n=861 | 53 n=861 | 55 n=861     | 55 n=861     | 54 n=861     | 62 n=287 | 65 n=287 | 67 n=287 | 63 n=248      | 66 n=248      | 67 n=248      |
| rr_d21          | 53 n=859 | 53 n=859 | 52 n=859 | 51 n=861     | 53 n=861     | 52 n=861     | 63 n=227 | 66 n=227 | 67 n=227 | 61 n=190      | 65 n=190      | 67 n=190      |
| rr_spot_div     | 55 n=287 | 57 n=287 | 55 n=287 | 51 n=861     | 53 n=861     | 52 n=861     | 73 n=26  | 81 n=26  | 73 n=26  | 61 n=190      | 65 n=190      | 67 n=190      |
| rr_orth         | 55 n=861 | 55 n=861 | 54 n=861 | 55 n=861     | 55 n=861     | 54 n=861     | 63 n=248 | 66 n=248 | 67 n=248 | 63 n=248      | 66 n=248      | 67 n=248      |
| vrp_level       | 51 n=789 | 53 n=789 | 54 n=789 | 51 n=789     | 52 n=789     | 53 n=789     | 59 n=177 | 66 n=177 | 70 n=177 | 59 n=190      | 66 n=190      | 68 n=190      |
| vrp_d21         | 49 n=789 | 51 n=789 | 50 n=789 | 49 n=789     | 51 n=789     | 51 n=789     | 56 n=167 | 69 n=167 | 70 n=167 | 56 n=171      | 68 n=171      | 70 n=171      |
| ts_slope        | 51 n=631 | 54 n=631 | 55 n=631 | 52 n=631     | 56 n=631     | 56 n=631     | 61 n=164 | 71 n=164 | 72 n=164 | 62 n=178      | 71 n=178      | 71 n=178      |
| opt_nc_z52      | 50 n=870 | 47 n=866 | 49 n=862 | 49 n=870     | 47 n=866     | 49 n=862     | 60 n=208 | 65 n=206 | 67 n=206 | 59 n=205      | 64 n=203      | 67 n=203      |
| opt_fut_div     | 41 n=418 | 36 n=416 | 35 n=412 | 41 n=870     | 37 n=866     | 38 n=862     | -        | -        | -        | 48 n=94       | 48 n=93       | 60 n=93       |
| opt_lev_z52     | 52 n=870 | 52 n=866 | 54 n=862 | 52 n=870     | 51 n=866     | 53 n=862     | 62 n=210 | 66 n=209 | 70 n=209 | 61 n=217      | 65 n=216      | 69 n=216      |

**The same on non-overlapping decisions, 2010-26:**

| signal          | sa 21    | sa 42    | sa 63   | sa orth 21   | sa orth 42   | sa orth 63   | and 21   | and 42   | and 63   | and orth 21   | and orth 42   | and orth 63   |
|:----------------|:---------|:---------|:--------|:-------------|:-------------|:-------------|:---------|:---------|:---------|:--------------|:--------------|:--------------|
| rr_fade_extreme | 37 n=46  | 45 n=33  | 44 n=25 | 50 n=206     | 49 n=103     | 39 n=69      | 43 n=7   | 71 n=7   | 71 n=7   | 55 n=86       | 62 n=56       | 70 n=40       |
| rr_z_follow     | 53 n=206 | 50 n=103 | 67 n=69 | 50 n=206     | 51 n=103     | 61 n=69      | 59 n=125 | 64 n=76  | 70 n=54  | 59 n=111      | 65 n=68       | 70 n=50       |
| rr_d21          | 53 n=206 | 48 n=103 | 59 n=69 | 54 n=206     | 47 n=103     | 54 n=69      | 60 n=121 | 67 n=75  | 69 n=54  | 56 n=108      | 74 n=69       | 72 n=54       |
| rr_spot_div     | 52 n=155 | 52 n=89  | 57 n=61 | 54 n=206     | 47 n=103     | 54 n=69      | 60 n=35  | 70 n=30  | 64 n=28  | 56 n=108      | 74 n=69       | 72 n=54       |
| rr_orth         | 50 n=206 | 51 n=103 | 61 n=69 | 50 n=206     | 51 n=103     | 61 n=69      | 59 n=111 | 65 n=68  | 70 n=50  | 59 n=111      | 65 n=68       | 70 n=50       |
| vrp_level       | 56 n=188 | 49 n=94  | 56 n=63 | 54 n=188     | 48 n=94      | 54 n=63      | 57 n=101 | 58 n=64  | 61 n=46  | 55 n=108      | 55 n=69       | 60 n=48       |
| vrp_d21         | 45 n=188 | 45 n=94  | 54 n=63 | 46 n=188     | 45 n=94      | 56 n=63      | 55 n=113 | 59 n=71  | 62 n=50  | 55 n=113      | 58 n=71       | 66 n=50       |
| ts_slope        | 51 n=151 | 57 n=76  | 51 n=51 | 52 n=151     | 57 n=76      | 51 n=51      | 51 n=82  | 70 n=50  | 70 n=37  | 51 n=86       | 67 n=52       | 76 n=37       |
| opt_nc_z52      | 46 n=208 | 43 n=104 | 51 n=69 | 45 n=208     | 43 n=104     | 49 n=69      | 53 n=100 | 53 n=66  | 62 n=47  | 55 n=99       | 51 n=65       | 57 n=47       |
| opt_fut_div     | 45 n=133 | 43 n=79  | 38 n=55 | 41 n=208     | 35 n=104     | 39 n=69      | -        | -        | -        | 44 n=52       | 51 n=39       | 52 n=33       |
| opt_lev_z52     | 52 n=208 | 54 n=104 | 51 n=69 | 51 n=208     | 53 n=104     | 52 n=69      | 57 n=104 | 61 n=67  | 72 n=50  | 58 n=102      | 60 n=67       | 73 n=51       |

**Raw against orthogonalised, 2016-26** (weekly decisions, accuracy % n; `sa` = standalone, `and` = extra vote on the agreement rule):

| signal          | sa 21    | sa 42    | sa 63    | sa orth 21   | sa orth 42   | sa orth 63   | and 21   | and 42   | and 63   | and orth 21   | and orth 42   | and orth 63   |
|:----------------|:---------|:---------|:---------|:-------------|:-------------|:-------------|:---------|:---------|:---------|:--------------|:--------------|:--------------|
| rr_fade_extreme | 54 n=48  | 50 n=48  | 42 n=48  | 45 n=550     | 43 n=550     | 45 n=550     | 40 n=5   | 80 n=5   | 80 n=5   | 46 n=74       | 55 n=74       | 65 n=74       |
| rr_z_follow     | 54 n=550 | 54 n=550 | 54 n=550 | 55 n=550     | 57 n=550     | 55 n=550     | 61 n=185 | 65 n=185 | 68 n=185 | 62 n=164      | 66 n=164      | 68 n=164      |
| rr_d21          | 51 n=548 | 51 n=548 | 51 n=548 | 50 n=550     | 51 n=550     | 52 n=550     | 62 n=142 | 64 n=142 | 67 n=142 | 59 n=124      | 62 n=124      | 68 n=124      |
| rr_spot_div     | 55 n=175 | 59 n=175 | 55 n=175 | 50 n=550     | 51 n=550     | 52 n=550     | 80 n=15  | 80 n=15  | 67 n=15  | 59 n=124      | 62 n=124      | 68 n=124      |
| rr_orth         | 55 n=550 | 57 n=550 | 55 n=550 | 55 n=550     | 57 n=550     | 55 n=550     | 62 n=164 | 66 n=164 | 68 n=164 | 62 n=164      | 66 n=164      | 68 n=164      |
| vrp_level       | 51 n=478 | 53 n=478 | 53 n=478 | 49 n=478     | 52 n=478     | 53 n=478     | 54 n=105 | 66 n=105 | 71 n=105 | 53 n=109      | 65 n=109      | 70 n=109      |
| vrp_d21         | 46 n=478 | 49 n=478 | 48 n=478 | 47 n=478     | 49 n=478     | 48 n=478     | 51 n=93  | 68 n=93  | 73 n=93  | 51 n=94       | 68 n=94       | 73 n=94       |
| ts_slope        | 52 n=320 | 61 n=320 | 61 n=320 | 54 n=320     | 63 n=320     | 62 n=320     | 59 n=94  | 76 n=94  | 79 n=94  | 59 n=99       | 76 n=99       | 77 n=99       |
| opt_nc_z52      | 50 n=559 | 49 n=555 | 51 n=551 | 50 n=559     | 49 n=555     | 52 n=551     | 56 n=148 | 62 n=146 | 68 n=146 | 56 n=149      | 61 n=147      | 68 n=147      |
| opt_fut_div     | 42 n=242 | 38 n=240 | 36 n=236 | 43 n=559     | 37 n=555     | 38 n=551     | -        | -        | -        | 50 n=72       | 46 n=71       | 65 n=71       |
| opt_lev_z52     | 54 n=559 | 51 n=555 | 53 n=551 | 54 n=559     | 51 n=555     | 53 n=551     | 58 n=144 | 59 n=143 | 68 n=143 | 59 n=144      | 60 n=143      | 68 n=143      |

**The same on non-overlapping decisions, 2016-26:**

| signal          | sa 21    | sa 42   | sa 63   | sa orth 21   | sa orth 42   | sa orth 63   | and 21   | and 42   | and 63   | and orth 21   | and orth 42   | and orth 63   |
|:----------------|:---------|:--------|:--------|:-------------|:-------------|:-------------|:---------|:---------|:---------|:--------------|:--------------|:--------------|
| rr_fade_extreme | 41 n=29  | 50 n=22 | 47 n=17 | 52 n=131     | 48 n=65      | 39 n=44      | 50 n=6   | 67 n=6   | 83 n=6   | 61 n=51       | 66 n=35       | 79 n=24       |
| rr_z_follow     | 50 n=131 | 51 n=65 | 70 n=44 | 48 n=131     | 52 n=65      | 61 n=44      | 55 n=80  | 61 n=49  | 69 n=35  | 56 n=73       | 60 n=45       | 65 n=34       |
| rr_d21          | 49 n=131 | 43 n=65 | 59 n=44 | 53 n=131     | 43 n=65      | 52 n=44      | 63 n=76  | 67 n=46  | 64 n=33  | 62 n=69       | 72 n=43       | 73 n=33       |
| rr_spot_div     | 52 n=99  | 59 n=56 | 64 n=39 | 53 n=131     | 43 n=65      | 52 n=44      | 52 n=21  | 68 n=19  | 59 n=17  | 62 n=69       | 72 n=43       | 73 n=33       |
| rr_orth         | 48 n=131 | 52 n=65 | 61 n=44 | 48 n=131     | 52 n=65      | 61 n=44      | 56 n=73  | 60 n=45  | 65 n=34  | 56 n=73       | 60 n=45       | 65 n=34       |
| vrp_level       | 56 n=113 | 45 n=56 | 53 n=38 | 53 n=113     | 45 n=56      | 50 n=38      | 53 n=60  | 51 n=39  | 50 n=26  | 50 n=62       | 52 n=40       | 54 n=28       |
| vrp_d21         | 44 n=113 | 45 n=56 | 50 n=38 | 44 n=113     | 45 n=56      | 50 n=38      | 50 n=68  | 63 n=41  | 64 n=28  | 50 n=68       | 63 n=41       | 64 n=28       |
| ts_slope        | 51 n=76  | 61 n=38 | 54 n=26 | 57 n=76      | 63 n=38      | 62 n=26      | 54 n=46  | 74 n=27  | 68 n=19  | 53 n=45       | 77 n=26       | 78 n=18       |
| opt_nc_z52      | 46 n=133 | 44 n=66 | 57 n=44 | 45 n=133     | 44 n=66      | 57 n=44      | 51 n=68  | 51 n=45  | 66 n=32  | 54 n=69       | 51 n=45       | 61 n=33       |
| opt_fut_div     | 44 n=79  | 46 n=48 | 38 n=34 | 44 n=133     | 33 n=66      | 41 n=44      | -        | -        | -        | 47 n=38       | 48 n=27       | 59 n=22       |
| opt_lev_z52     | 50 n=133 | 52 n=66 | 55 n=44 | 50 n=133     | 52 n=66      | 55 n=44      | 53 n=70  | 56 n=43  | 76 n=33  | 54 n=69       | 56 n=43       | 76 n=33       |

Reading. (i) The skew is the most "restated" variable: correlation +0.45 / +0.48 with the trailing 21- / 63-session return (R2 0.27), +0.31 with
`cot_z52`, +0.28 with the house score, and it has the sign of positioning on 66 % of sessions. Its one-month change is +0.37 with the one-month
return. Implied-minus-realised vol, the slope and option positioning are nearly uncorrelated with everything old (|r| <= 0.19, R2 on spot <= 0.04):
new, but empty. (ii) Orthogonalising changes almost nothing anywhere: skew 55 / 54 / 53 % raw, 55 / 55 / 54 % orthogonalised; as a vote 62 / 65 / 67 %
raw, 63 / 66 / 67 % orthogonalised (2010-26, weekly). So what little the skew shows does not come from its linear overlap with the recent price move -
and what the other signals lack is not restored by it. (iii) For the two vote-type RR signals the orthogonalised column is the orthogonalised
one-month change, and for `rr_fade_extreme` the orthogonalised fade-at-all-times (45 %): the contrarian reading fails with or without the control.

## 6 Each signal as an EXTRA VOTE on the agreement rule

### (a) AND rule against the agreement rule, non-overlapping decisions (the measure of the bar)

| signal          |   h | period   | agreement, same span   | AND rule                 |   gain, pts |   gain vs full-period agreement | 63 stale: acc n   |   63 stale gain | 126 stale: acc n   |   126 stale gain |
|:----------------|----:|:---------|:-----------------------|:-------------------------|------------:|--------------------------------:|:------------------|----------------:|:-------------------|-----------------:|
| rr_fade_extreme |  21 | 2010-26  | 59 n=154               | 43 [16-75] n=7 (0.4/y)   |       -16.2 |                           -16.1 | 67 n=9            |             7.6 | 40 n=10            |            -19.1 |
| rr_fade_extreme |  21 | 2016-26  | 57 n=94                | 50 [19-81] n=6 (0.6/y)   |        -7.4 |                            -7.3 | 71 n=7            |            14   | 50 n=6             |             -7.4 |
| rr_fade_extreme |  21 | 2023-26  | 61 n=33                | 0 [0-79] n=1 (0.3/y)     |       -60.6 |                           -60   | 67 n=3            |             6.1 | 0 n=1              |            -60.6 |
| rr_fade_extreme |  42 | 2010-26  | 60 n=88                | 71 [36-92] n=7 (0.4/y)   |        11.2 |                            10.8 | 67 n=9            |             6.4 | 56 n=9             |             -4.7 |
| rr_fade_extreme |  42 | 2016-26  | 58 n=55                | 67 [30-90] n=6 (0.6/y)   |         8.5 |                             7.7 | 71 n=7            |            13.2 | 60 n=5             |              1.8 |
| rr_fade_extreme |  42 | 2023-26  | 42 n=19                | 100 [21-100] n=1 (0.3/y) |        57.9 |                            55   | 67 n=3            |            24.6 | -                  |            nan   |
| rr_z_follow     |  21 | 2010-26  | 59 n=154               | 59 [50-67] n=125 (7.5/y) |         0.1 |                             0.2 | 54 n=111          |            -5   | 53 n=106           |             -6.3 |
| rr_z_follow     |  21 | 2016-26  | 57 n=94                | 55 [44-65] n=80 (7.4/y)  |        -2.4 |                            -2.3 | 56 n=73           |            -1.3 | 54 n=70            |             -3.2 |
| rr_z_follow     |  21 | 2023-26  | 61 n=33                | 57 [39-73] n=28 (7.4/y)  |        -3.5 |                            -2.9 | 59 n=22           |            -1.5 | 65 n=20            |              4.4 |
| rr_z_follow     |  42 | 2010-26  | 60 n=88                | 64 [53-74] n=76 (4.6/y)  |         4.2 |                             3.8 | 66 n=67           |             5.4 | 59 n=66            |             -1.1 |
| rr_z_follow     |  42 | 2016-26  | 58 n=55                | 61 [47-74] n=49 (4.6/y)  |         3   |                             2.3 | 64 n=44           |             5.5 | 60 n=43            |              2.3 |
| rr_z_follow     |  42 | 2023-26  | 42 n=19                | 39 [20-61] n=18 (4.9/y)  |        -3.2 |                            -6.1 | 54 n=13           |            11.7 | 46 n=13            |              4   |
| rr_d21          |  21 | 2010-26  | 59 n=154               | 60 [51-69] n=121 (7.2/y) |         1.2 |                             1.4 | 53 n=118          |            -6.5 | 58 n=128           |             -1.3 |
| rr_d21          |  21 | 2016-26  | 57 n=94                | 63 [52-73] n=76 (7.1/y)  |         5.7 |                             5.9 | 51 n=74           |            -6.1 | 58 n=76            |              0.4 |
| rr_d21          |  21 | 2023-26  | 61 n=33                | 58 [39-76] n=24 (6.4/y)  |        -2.3 |                            -1.7 | 50 n=28           |           -10.6 | 54 n=24            |             -6.4 |
| rr_d21          |  42 | 2010-26  | 60 n=88                | 67 [55-76] n=75 (4.5/y)  |         6.4 |                             6   | 66 n=77           |             6   | 60 n=80            |             -0.2 |
| rr_d21          |  42 | 2016-26  | 58 n=55                | 67 [53-79] n=46 (4.3/y)  |         9.2 |                             8.5 | 65 n=48           |             6.4 | 57 n=49            |             -1   |
| rr_d21          |  42 | 2023-26  | 42 n=19                | 38 [18-61] n=16 (4.3/y)  |        -4.6 |                            -7.5 | 53 n=17           |            10.8 | 29 n=17            |            -12.7 |
| rr_spot_div     |  21 | 2010-26  | 59 n=154               | 60 [44-74] n=35 (2.1/y)  |         0.9 |                             1   | 51 n=63           |            -8.3 | 66 n=73            |              6.7 |
| rr_spot_div     |  21 | 2016-26  | 57 n=94                | 52 [32-72] n=21 (2.0/y)  |        -5.1 |                            -4.9 | 46 n=39           |           -11.3 | 70 n=43            |             12.3 |
| rr_spot_div     |  21 | 2023-26  | 61 n=33                | 57 [25-84] n=7 (1.9/y)   |        -3.5 |                            -2.9 | 50 n=12           |           -10.6 | 82 n=11            |             21.2 |
| rr_spot_div     |  42 | 2010-26  | 60 n=88                | 70 [52-83] n=30 (1.8/y)  |         9.8 |                             9.3 | 60 n=50           |            -0.2 | 65 n=55            |              5.2 |
| rr_spot_div     |  42 | 2016-26  | 58 n=55                | 68 [46-85] n=19 (1.8/y)  |        10.2 |                             9.5 | 56 n=32           |            -1.9 | 61 n=33            |              2.4 |
| rr_spot_div     |  42 | 2023-26  | 42 n=19                | 57 [25-84] n=7 (1.9/y)   |        15   |                            12.1 | 55 n=11           |            12.4 | 36 n=11            |             -5.7 |
| rr_orth         |  21 | 2010-26  | 59 n=154               | 59 [50-68] n=111 (6.6/y) |         0.4 |                             0.5 | 54 n=112          |            -5.5 | 54 n=115           |             -5.2 |
| rr_orth         |  21 | 2016-26  | 57 n=94                | 56 [45-67] n=73 (6.8/y)  |        -1.3 |                            -1.1 | 55 n=73           |            -2.7 | 59 n=73            |              1.5 |
| rr_orth         |  21 | 2023-26  | 61 n=33                | 54 [35-71] n=26 (6.9/y)  |        -6.8 |                            -6.2 | 59 n=22           |            -1.5 | 76 n=21            |             15.6 |
| rr_orth         |  42 | 2010-26  | 60 n=88                | 65 [53-75] n=68 (4.1/y)  |         4.5 |                             4   | 73 n=70           |            12.6 | 58 n=71            |             -2.5 |
| rr_orth         |  42 | 2016-26  | 58 n=55                | 60 [45-73] n=45 (4.2/y)  |         1.8 |                             1.1 | 72 n=46           |            13.6 | 61 n=46            |              2.7 |
| rr_orth         |  42 | 2023-26  | 42 n=19                | 35 [17-59] n=17 (4.6/y)  |        -6.8 |                            -9.7 | 53 n=15           |            11.2 | 46 n=13            |              4   |
| vrp_level       |  21 | 2010-26  | 57 n=141               | 57 [48-67] n=101 (6.0/y) |         0.7 |                            -1.5 | 46 n=110          |           -10.4 | 65 n=114           |              8.2 |
| vrp_level       |  21 | 2016-26  | 53 n=81                | 53 [41-65] n=60 (5.6/y)  |         0.2 |                            -4   | 46 n=61           |            -7.2 | 66 n=67            |             12.6 |
| vrp_level       |  21 | 2023-26  | 45 n=20                | 36 [16-61] n=14 (3.7/y)  |        -9.3 |                           -24.3 | 59 n=17           |            13.8 | 62 n=21            |             16.9 |
| vrp_level       |  42 | 2010-26  | 60 n=81                | 58 [46-69] n=64 (3.8/y)  |        -2.7 |                            -2.9 | 58 n=69           |            -2.5 | 64 n=74            |              3   |
| vrp_level       |  42 | 2016-26  | 58 n=48                | 51 [36-66] n=39 (3.7/y)  |        -7.1 |                            -7.6 | 51 n=37           |            -7   | 68 n=44            |              9.8 |
| vrp_level       |  42 | 2023-26  | 33 n=12                | 33 [12-65] n=9 (2.4/y)   |         0   |                           -11.7 | 60 n=10           |            26.7 | 54 n=13            |             20.5 |
| vrp_d21         |  21 | 2010-26  | 57 n=141               | 55 [46-64] n=113 (6.7/y) |        -1.9 |                            -4.1 | 52 n=112          |            -5   | 59 n=114           |              2   |
| vrp_d21         |  21 | 2016-26  | 53 n=81                | 50 [38-62] n=68 (6.3/y)  |        -3.1 |                            -7.3 | 52 n=66           |            -1.6 | 63 n=67            |              9.6 |
| vrp_d21         |  21 | 2023-26  | 45 n=20                | 35 [17-59] n=17 (4.5/y)  |        -9.7 |                           -24.7 | 56 n=16           |            11.2 | 71 n=17            |             25.6 |
| vrp_d21         |  42 | 2010-26  | 60 n=81                | 59 [48-70] n=71 (4.3/y)  |        -1.3 |                            -1.5 | 64 n=73           |             3.9 | 68 n=74            |              7.1 |
| vrp_d21         |  42 | 2016-26  | 58 n=48                | 63 [48-76] n=41 (3.8/y)  |         5.1 |                             4.5 | 67 n=42           |             8.3 | 73 n=44            |             14.4 |
| vrp_d21         |  42 | 2023-26  | 33 n=12                | 30 [11-60] n=10 (2.7/y)  |        -3.3 |                           -15   | 55 n=11           |            21.2 | 55 n=11            |             21.2 |
| agree3_vrp_gate |  21 | 2010-26  | 56 n=131               | 53 [43-63] n=94 (5.6/y)  |        -3.3 |                            -5.8 | 55 n=93           |            -1.6 | 61 n=90            |              4.6 |
| agree3_vrp_gate |  21 | 2016-26  | 53 n=81                | 51 [38-63] n=57 (5.3/y)  |        -2.2 |                            -6.4 | 57 n=56           |             4.1 | 60 n=58            |              7.3 |
| agree3_vrp_gate |  21 | 2023-26  | 45 n=20                | 27 [10-57] n=11 (2.9/y)  |       -17.7 |                           -32.7 | 46 n=13           |             1.2 | 56 n=16            |             11.2 |
| agree3_vrp_gate |  42 | 2010-26  | 58 n=76                | 55 [43-67] n=62 (3.7/y)  |        -3.1 |                            -5.8 | 58 n=60           |             0.4 | 55 n=58            |             -2.7 |
| agree3_vrp_gate |  42 | 2016-26  | 58 n=48                | 55 [40-70] n=38 (3.6/y)  |        -3.1 |                            -3.7 | 61 n=36           |             2.8 | 56 n=39            |             -1.9 |
| agree3_vrp_gate |  42 | 2023-26  | 33 n=12                | 29 [8-64] n=7 (1.9/y)    |        -4.8 |                           -16.4 | 57 n=7            |            23.8 | 33 n=12            |              0   |
| ts_slope        |  21 | 2010-26  | 56 n=112               | 51 [41-62] n=82 (4.9/y)  |        -5   |                            -7.8 | 57 n=87           |             1.2 | 64 n=88            |              7.4 |
| ts_slope        |  21 | 2016-26  | 50 n=52                | 54 [40-68] n=46 (4.3/y)  |         4.3 |                            -2.9 | 53 n=45           |             3.3 | 65 n=43            |             15.1 |
| ts_slope        |  21 | 2023-26  | -                      | - n=0                    |       nan   |                           nan   | -                 |           nan   | -                  |            nan   |
| ts_slope        |  42 | 2010-26  | 64 n=64                | 70 [56-81] n=50 (3.0/y)  |         5.9 |                             9.3 | 67 n=57           |             2.6 | 73 n=55            |              8.7 |
| ts_slope        |  42 | 2016-26  | 65 n=31                | 74 [55-87] n=27 (2.5/y)  |         9.6 |                            15.1 | 63 n=30           |            -1.2 | 70 n=27            |              5.9 |
| ts_slope        |  42 | 2023-26  | -                      | - n=0                    |       nan   |                           nan   | -                 |           nan   | -                  |            nan   |
| opt_nc_z52      |  21 | 2010-26  | 59 n=156               | 53 [43-62] n=100 (6.0/y) |        -6   |                            -6   | 55 n=101          |            -3.5 | 57 n=97            |             -2.3 |
| opt_nc_z52      |  21 | 2016-26  | 57 n=96                | 51 [40-63] n=68 (6.3/y)  |        -5.8 |                            -5.8 | 56 n=68           |            -1.4 | 56 n=62            |             -0.8 |
| opt_nc_z52      |  21 | 2023-26  | 60 n=35                | 42 [24-61] n=24 (6.4/y)  |       -18.3 |                           -18.3 | 43 n=21           |           -17.1 | 50 n=22            |            -10   |
| opt_nc_z52      |  42 | 2010-26  | 61 n=89                | 53 [41-65] n=66 (4.0/y)  |        -7.6 |                            -7.6 | 65 n=63           |             4.4 | 63 n=62            |              2.2 |
| opt_nc_z52      |  42 | 2016-26  | 59 n=56                | 51 [37-65] n=45 (4.2/y)  |        -7.8 |                            -7.8 | 64 n=42           |             5.4 | 65 n=40            |              6.1 |
| opt_nc_z52      |  42 | 2023-26  | 45 n=20                | 44 [23-67] n=16 (4.3/y)  |        -1.3 |                            -1.3 | 42 n=12           |            -3.3 | 53 n=15            |              8.3 |
| opt_fut_div     |  21 | 2010-26  | 59 n=156               | - n=0                    |       nan   |                           nan   | 62 n=37           |             3.2 | 50 n=56            |             -9   |
| opt_fut_div     |  21 | 2016-26  | 57 n=96                | - n=0                    |       nan   |                           nan   | 65 n=23           |             7.9 | 44 n=34            |            -13.2 |
| opt_fut_div     |  21 | 2023-26  | 60 n=35                | - n=0                    |       nan   |                           nan   | 67 n=6            |             6.7 | 40 n=10            |            -20   |
| opt_fut_div     |  42 | 2010-26  | 61 n=89                | - n=0                    |       nan   |                           nan   | 69 n=29           |             8.3 | 62 n=40            |              1.8 |
| opt_fut_div     |  42 | 2016-26  | 59 n=56                | - n=0                    |       nan   |                           nan   | 65 n=17           |             5.8 | 64 n=25            |              5.1 |
| opt_fut_div     |  42 | 2023-26  | 45 n=20                | - n=0                    |       nan   |                           nan   | 60 n=5            |            15   | 56 n=9             |             10.6 |
| opt_lev_z52     |  21 | 2010-26  | 59 n=156               | 57 [47-66] n=104 (6.2/y) |        -2.2 |                            -2.2 | 57 n=107          |            -2   | 49 n=93            |             -9.5 |
| opt_lev_z52     |  21 | 2016-26  | 57 n=96                | 53 [41-64] n=70 (6.5/y)  |        -4.4 |                            -4.4 | 52 n=69           |            -5.1 | 52 n=56            |             -5.5 |
| opt_lev_z52     |  21 | 2023-26  | 60 n=35                | 46 [30-64] n=28 (7.4/y)  |       -13.6 |                           -13.6 | 44 n=27           |           -15.6 | 36 n=22            |            -23.6 |
| opt_lev_z52     |  42 | 2010-26  | 61 n=89                | 61 [49-72] n=67 (4.0/y)  |         0.5 |                             0.5 | 58 n=69           |            -2.7 | 57 n=61            |             -3.3 |
| opt_lev_z52     |  42 | 2016-26  | 59 n=56                | 56 [41-70] n=43 (4.0/y)  |        -3.1 |                            -3.1 | 57 n=44           |            -2.1 | 57 n=37            |             -2.2 |
| opt_lev_z52     |  42 | 2023-26  | 45 n=20                | 47 [25-70] n=15 (4.1/y)  |         1.7 |                             1.7 | 41 n=17           |            -3.8 | 44 n=16            |             -1.3 |

**Bar, cell by cell** (gain >= 3 pts at 21 and 42 sessions in 2010-26 and 2016-26; >= 6 non-overlapping 21-session decisions a year; not worse in 2023-26; each stale copy keeps at most half of the gain):

| signal          | gain_ok   | count21_ok   | count42_ok   | not_worse_2023   | placebo_ok   | met   |
|:----------------|:----------|:-------------|:-------------|:-----------------|:-------------|:------|
| rr_fade_extreme | False     | False        | False        | False            | False        | False |
| rr_z_follow     | False     | True         | False        | False            | False        | False |
| rr_d21          | False     | True         | False        | False            | False        | False |
| rr_spot_div     | False     | False        | False        | False            | False        | False |
| rr_orth         | False     | True         | False        | False            | False        | False |
| vrp_level       | False     | False        | False        | False            | False        | False |
| vrp_d21         | False     | True         | False        | False            | False        | False |
| agree3_vrp_gate | False     | False        | False        | False            | False        | False |
| ts_slope        | False     | False        | False        | False            | False        | False |
| opt_nc_z52      | False     | False        | False        | False            | False        | False |
| opt_fut_div     | False     | False        | False        | False            | False        | False |
| opt_lev_z52     | False     | True         | False        | False            | False        | False |

### The same on weekly decisions (accuracy % n; `same span` = agreement rule where the signal is defined, `contra` = agreement calls the signal contradicts)


*2010-26*

| signal          | same span 21   | same span 42   | same span 63   | AND 21   | AND 42   | AND 63   | stale63 21   | stale63 42   | stale63 63   | stale126 21   | stale126 42   | stale126 63   | contra 21   | contra 42   | contra 63   |
|:----------------|:---------------|:---------------|:---------------|:---------|:---------|:---------|:-------------|:-------------|:-------------|:--------------|:--------------|:--------------|:------------|:------------|:------------|
| rr_fade_extreme | 59 n=382       | 65 n=382       | 66 n=382       | 50 n=6   | 83 n=6   | 67 n=6   | 45 n=11      | 45 n=11      | 45 n=11      | 50 n=8        | 50 n=8        | 62 n=8        | 61 n=23     | 78 n=23     | 74 n=23     |
| rr_z_follow     | 59 n=382       | 65 n=382       | 66 n=382       | 62 n=287 | 65 n=287 | 67 n=287 | 59 n=246     | 63 n=242     | 67 n=242     | 56 n=217      | 61 n=213      | 62 n=213      | 49 n=95     | 63 n=95     | 65 n=95     |
| rr_d21          | 59 n=382       | 65 n=382       | 66 n=382       | 63 n=227 | 66 n=227 | 67 n=227 | 59 n=205     | 61 n=203     | 65 n=203     | 60 n=223      | 61 n=220      | 66 n=220      | 54 n=155    | 63 n=155    | 66 n=155    |
| rr_spot_div     | 59 n=382       | 65 n=382       | 66 n=382       | 73 n=26  | 81 n=26  | 73 n=26  | 58 n=67      | 61 n=67      | 66 n=67      | 65 n=88       | 67 n=88       | 72 n=88       | 54 n=103    | 58 n=103    | 61 n=103    |
| rr_orth         | 59 n=382       | 65 n=382       | 66 n=382       | 63 n=248 | 66 n=248 | 67 n=248 | 59 n=239     | 63 n=235     | 67 n=235     | 57 n=223      | 62 n=219      | 66 n=219      | 51 n=134    | 63 n=134    | 66 n=134    |
| vrp_level       | 59 n=350       | 66 n=350       | 68 n=350       | 59 n=177 | 66 n=177 | 70 n=177 | 60 n=186     | 65 n=186     | 72 n=186     | 67 n=212      | 68 n=212      | 71 n=212      | 59 n=173    | 66 n=173    | 66 n=173    |
| vrp_d21         | 59 n=350       | 66 n=350       | 68 n=350       | 56 n=167 | 69 n=167 | 70 n=167 | 60 n=184     | 66 n=184     | 68 n=184     | 62 n=182      | 67 n=182      | 70 n=182      | 61 n=183    | 63 n=183    | 66 n=183    |
| agree3_vrp_gate | 59 n=319       | 66 n=319       | 69 n=319       | 58 n=165 | 66 n=165 | 68 n=165 | 61 n=156     | 68 n=156     | 71 n=156     | 58 n=151      | 68 n=151      | 69 n=151      | 59 n=154    | 67 n=154    | 69 n=154    |
| ts_slope        | 59 n=286       | 68 n=286       | 69 n=286       | 61 n=164 | 71 n=164 | 72 n=164 | 66 n=175     | 74 n=175     | 76 n=175     | 60 n=162      | 72 n=162      | 75 n=162      | 57 n=122    | 64 n=122    | 65 n=122    |
| opt_nc_z52      | 59 n=387       | 65 n=383       | 67 n=383       | 60 n=208 | 65 n=206 | 67 n=206 | 61 n=191     | 69 n=187     | 74 n=187     | 55 n=185      | 65 n=181      | 66 n=181      | 59 n=179    | 65 n=177    | 66 n=177    |
| opt_fut_div     | 59 n=387       | 65 n=383       | 67 n=383       | -        | -        | -        | 60 n=60      | 67 n=60      | 67 n=60      | 48 n=96       | 68 n=96       | 68 n=96       | 59 n=179    | 65 n=177    | 66 n=177    |
| opt_lev_z52     | 59 n=387       | 65 n=383       | 67 n=383       | 62 n=210 | 66 n=209 | 70 n=209 | 60 n=203     | 66 n=199     | 69 n=199     | 58 n=173      | 64 n=169      | 64 n=169      | 56 n=177    | 64 n=174    | 63 n=174    |

*2016-26*

| signal          | same span 21   | same span 42   | same span 63   | AND 21   | AND 42   | AND 63   | stale63 21   | stale63 42   | stale63 63   | stale126 21   | stale126 42   | stale126 63   | contra 21   | contra 42   | contra 63   |
|:----------------|:---------------|:---------------|:---------------|:---------|:---------|:---------|:-------------|:-------------|:-------------|:--------------|:--------------|:--------------|:------------|:------------|:------------|
| rr_fade_extreme | 57 n=238       | 63 n=238       | 67 n=238       | 40 n=5   | 80 n=5   | 80 n=5   | 44 n=9       | 44 n=9       | 44 n=9       | 100 n=3       | 67 n=3        | 100 n=3       | 50 n=12     | 83 n=12     | 75 n=12     |
| rr_z_follow     | 57 n=238       | 63 n=238       | 67 n=238       | 61 n=185 | 65 n=185 | 68 n=185 | 58 n=161     | 64 n=157     | 69 n=157     | 55 n=145      | 62 n=141      | 65 n=141      | 42 n=53     | 57 n=53     | 64 n=53     |
| rr_d21          | 57 n=238       | 63 n=238       | 67 n=238       | 62 n=142 | 64 n=142 | 67 n=142 | 57 n=121     | 60 n=119     | 66 n=119     | 55 n=135      | 61 n=132      | 70 n=132      | 49 n=96     | 61 n=96     | 67 n=96     |
| rr_spot_div     | 57 n=238       | 63 n=238       | 67 n=238       | 80 n=15  | 80 n=15  | 67 n=15  | 54 n=37      | 49 n=37      | 57 n=37      | 57 n=46       | 72 n=46       | 83 n=46       | 46 n=56     | 54 n=56     | 59 n=56     |
| rr_orth         | 57 n=238       | 63 n=238       | 67 n=238       | 62 n=164 | 66 n=164 | 68 n=164 | 57 n=160     | 63 n=156     | 67 n=156     | 57 n=148      | 65 n=144      | 70 n=144      | 46 n=74     | 55 n=74     | 65 n=74     |
| vrp_level       | 56 n=206       | 65 n=206       | 69 n=206       | 54 n=105 | 66 n=105 | 71 n=105 | 58 n=108     | 64 n=108     | 76 n=108     | 62 n=130      | 66 n=130      | 71 n=130      | 57 n=101    | 64 n=101    | 67 n=101    |
| vrp_d21         | 56 n=206       | 65 n=206       | 69 n=206       | 51 n=93  | 68 n=93  | 73 n=93  | 61 n=115     | 65 n=115     | 70 n=115     | 61 n=117      | 66 n=117      | 73 n=117      | 60 n=113    | 63 n=113    | 66 n=113    |
| agree3_vrp_gate | 56 n=206       | 65 n=206       | 69 n=206       | 57 n=101 | 70 n=101 | 73 n=101 | 62 n=94      | 71 n=94      | 76 n=94      | 53 n=100      | 68 n=100      | 71 n=100      | 54 n=105    | 60 n=105    | 66 n=105    |
| ts_slope        | 56 n=142       | 68 n=142       | 72 n=142       | 59 n=94  | 76 n=94  | 79 n=94  | 63 n=94      | 72 n=94      | 78 n=94      | 59 n=82       | 74 n=82       | 79 n=82       | 50 n=48     | 54 n=48     | 58 n=48     |
| opt_nc_z52      | 57 n=243       | 63 n=239       | 67 n=239       | 56 n=148 | 62 n=146 | 68 n=146 | 60 n=144     | 67 n=140     | 75 n=140     | 56 n=131      | 65 n=127      | 68 n=127      | 59 n=95     | 65 n=93     | 65 n=93     |
| opt_fut_div     | 57 n=243       | 63 n=239       | 67 n=239       | -        | -        | -        | 61 n=36      | 64 n=36      | 64 n=36      | 43 n=60       | 67 n=60       | 67 n=60       | 59 n=95     | 65 n=93     | 65 n=93     |
| opt_lev_z52     | 57 n=243       | 63 n=239       | 67 n=239       | 58 n=144 | 59 n=143 | 68 n=143 | 57 n=141     | 60 n=137     | 65 n=137     | 57 n=109      | 63 n=105      | 64 n=105      | 56 n=99     | 69 n=96     | 66 n=96     |

*2023-26*

| signal          | same span 21   | same span 42   | same span 63   | AND 21   | AND 42   | AND 63   | stale63 21   | stale63 42   | stale63 63   | stale126 21   | stale126 42   | stale126 63   | contra 21   | contra 42   | contra 63   |
|:----------------|:---------------|:---------------|:---------------|:---------|:---------|:---------|:-------------|:-------------|:-------------|:--------------|:--------------|:--------------|:------------|:------------|:------------|
| rr_fade_extreme | 53 n=72        | 46 n=72        | 53 n=72        | -        | -        | -        | 0 n=2        | 0 n=2        | 0 n=2        | -             | -             | -             | 50 n=2      | 50 n=2      | 50 n=2      |
| rr_z_follow     | 53 n=72        | 46 n=72        | 53 n=72        | 57 n=60  | 45 n=60  | 57 n=60  | 62 n=40      | 44 n=36      | 56 n=36      | 53 n=36       | 41 n=32       | 44 n=32       | 33 n=12     | 50 n=12     | 33 n=12     |
| rr_d21          | 53 n=72        | 46 n=72        | 53 n=72        | 60 n=48  | 48 n=48  | 54 n=48  | 53 n=32      | 40 n=30      | 50 n=30      | 56 n=36       | 48 n=33       | 55 n=33       | 38 n=24     | 42 n=24     | 50 n=24     |
| rr_spot_div     | 53 n=72        | 46 n=72        | 53 n=72        | 100 n=4  | 100 n=4  | 100 n=4  | 40 n=5       | 40 n=5       | 40 n=5       | 71 n=7        | 57 n=7        | 100 n=7       | 20 n=15     | 20 n=15     | 40 n=15     |
| rr_orth         | 53 n=72        | 46 n=72        | 53 n=72        | 59 n=58  | 47 n=58  | 59 n=58  | 58 n=36      | 38 n=32      | 47 n=32      | 55 n=33       | 41 n=29       | 55 n=29       | 29 n=14     | 43 n=14     | 29 n=14     |
| vrp_level       | 45 n=40        | 42 n=40        | 55 n=40        | 29 n=21  | 29 n=21  | 48 n=21  | 52 n=29      | 52 n=29      | 69 n=29      | 59 n=29       | 55 n=29       | 62 n=29       | 63 n=19     | 58 n=19     | 63 n=19     |
| vrp_d21         | 45 n=40        | 42 n=40        | 55 n=40        | 38 n=16  | 38 n=16  | 50 n=16  | 60 n=20      | 55 n=20      | 70 n=20      | 62 n=26       | 46 n=26       | 65 n=26       | 50 n=24     | 46 n=24     | 58 n=24     |
| agree3_vrp_gate | 45 n=40        | 42 n=40        | 55 n=40        | 44 n=18  | 56 n=18  | 61 n=18  | 55 n=20      | 45 n=20      | 75 n=20      | 55 n=20       | 60 n=20       | 65 n=20       | 45 n=22     | 32 n=22     | 50 n=22     |
| ts_slope        | -              | -              | -              | -        | -        | -        | -            | -            | -            | -             | -             | -             | -           | -           | -           |
| opt_nc_z52      | 55 n=77        | 47 n=73        | 53 n=73        | 49 n=51  | 45 n=49  | 55 n=49  | 50 n=42      | 39 n=38      | 61 n=38      | 56 n=41       | 57 n=37       | 68 n=37       | 65 n=26     | 50 n=24     | 50 n=24     |
| opt_fut_div     | 55 n=77        | 47 n=73        | 53 n=73        | -        | -        | -        | 78 n=9       | 67 n=9       | 56 n=9       | 29 n=14       | 57 n=14       | 71 n=14       | 65 n=26     | 50 n=24     | 50 n=24     |
| opt_lev_z52     | 55 n=77        | 47 n=73        | 53 n=73        | 55 n=56  | 51 n=55  | 60 n=55  | 50 n=50      | 33 n=46      | 43 n=46      | 47 n=34       | 50 n=30       | 47 n=30       | 52 n=21     | 33 n=18     | 33 n=18     |

### Confirmed against contradicted agreement calls, each as its own non-overlapping stream (accuracy % [Wilson 95 %] n)


*2010-26*

| signal          | confirmed 21     | confirmed 42    | confirmed 63    | contradicted 21   | contradicted 42   | contradicted 63   |
|:----------------|:-----------------|:----------------|:----------------|:------------------|:------------------|:------------------|
| rr_fade_extreme | 43 [16-75] n=7   | 71 [36-92] n=7  | 71 [36-92] n=7  | 59 [41-75] n=27   | 74 [51-88] n=19   | 75 [51-90] n=16   |
| rr_z_follow     | 59 [50-67] n=125 | 64 [53-74] n=76 | 70 [57-81] n=54 | 49 [38-61] n=71   | 59 [45-72] n=49   | 69 [53-82] n=36   |
| rr_d21          | 60 [51-69] n=121 | 67 [55-76] n=75 | 69 [55-79] n=54 | 50 [41-59] n=108  | 64 [53-74] n=75   | 66 [53-77] n=53   |
| rr_spot_div     | 60 [44-74] n=35  | 70 [52-83] n=30 | 64 [46-79] n=28 | 52 [42-63] n=82   | 64 [51-75] n=61   | 60 [46-73] n=48   |
| rr_orth         | 59 [50-68] n=111 | 65 [53-75] n=68 | 70 [56-81] n=50 | 55 [44-65] n=86   | 62 [49-74] n=56   | 70 [55-82] n=40   |
| vrp_level       | 57 [48-67] n=101 | 58 [46-69] n=64 | 61 [46-74] n=46 | 53 [44-63] n=101  | 65 [53-75] n=68   | 67 [53-79] n=46   |
| vrp_d21         | 55 [46-64] n=113 | 59 [48-70] n=71 | 62 [48-74] n=50 | 60 [51-69] n=106  | 64 [53-74] n=70   | 69 [55-80] n=49   |
| agree3_vrp_gate | 53 [43-63] n=94  | 55 [43-67] n=62 | 60 [44-73] n=42 | 55 [45-65] n=93   | 62 [50-73] n=61   | 57 [42-71] n=42   |
| ts_slope        | 51 [41-62] n=82  | 70 [56-81] n=50 | 70 [54-83] n=37 | 58 [47-69] n=72   | 62 [48-75] n=45   | 71 [54-83] n=34   |
| opt_nc_z52      | 53 [43-62] n=100 | 53 [41-65] n=66 | 62 [47-74] n=47 | 59 [48-68] n=92   | 63 [50-74] n=62   | 74 [60-85] n=43   |
| opt_lev_z52     | 57 [47-66] n=104 | 61 [49-72] n=67 | 72 [58-83] n=50 | 48 [38-58] n=96   | 64 [52-75] n=59   | 60 [44-73] n=42   |

*2016-26*

| signal          | confirmed 21    | confirmed 42    | confirmed 63    | contradicted 21   | contradicted 42   | contradicted 63   |
|:----------------|:----------------|:----------------|:----------------|:------------------|:------------------|:------------------|
| rr_fade_extreme | 50 [19-81] n=6  | 67 [30-90] n=6  | 83 [44-97] n=6  | 60 [36-80] n=15   | 75 [47-91] n=12   | 78 [45-94] n=9    |
| rr_z_follow     | 55 [44-65] n=80 | 61 [47-74] n=49 | 69 [52-81] n=35 | 52 [38-67] n=42   | 60 [42-75] n=30   | 73 [52-87] n=22   |
| rr_d21          | 63 [52-73] n=76 | 67 [53-79] n=46 | 64 [47-78] n=33 | 49 [38-61] n=69   | 65 [51-77] n=46   | 64 [47-78] n=33   |
| rr_spot_div     | 52 [32-72] n=21 | 68 [46-85] n=19 | 59 [36-78] n=17 | 56 [42-69] n=50   | 65 [49-78] n=37   | 60 [42-75] n=30   |
| rr_orth         | 56 [45-67] n=73 | 60 [45-73] n=45 | 65 [48-79] n=34 | 61 [47-73] n=51   | 66 [49-79] n=35   | 79 [60-91] n=24   |
| vrp_level       | 53 [41-65] n=60 | 51 [36-66] n=39 | 50 [32-68] n=26 | 54 [42-66] n=59   | 69 [54-81] n=39   | 63 [44-78] n=27   |
| vrp_d21         | 50 [38-62] n=68 | 63 [48-76] n=41 | 64 [46-79] n=28 | 66 [54-77] n=62   | 69 [54-81] n=39   | 79 [62-90] n=29   |
| agree3_vrp_gate | 51 [38-63] n=57 | 55 [40-70] n=38 | 60 [41-77] n=25 | 53 [41-65] n=62   | 61 [46-74] n=41   | 52 [34-69] n=27   |
| ts_slope        | 54 [40-68] n=46 | 74 [55-87] n=27 | 68 [46-85] n=19 | 61 [44-76] n=31   | 60 [39-78] n=20   | 64 [39-84] n=14   |
| opt_nc_z52      | 51 [40-63] n=68 | 51 [37-65] n=45 | 66 [48-80] n=32 | 64 [50-76] n=50   | 59 [42-74] n=34   | 70 [49-84] n=23   |
| opt_lev_z52     | 53 [41-64] n=70 | 56 [41-70] n=43 | 76 [59-87] n=33 | 49 [36-62] n=53   | 64 [48-78] n=36   | 54 [35-72] n=24   |

*2023-26*

| signal          | confirmed 21    | confirmed 42     | confirmed 63     | contradicted 21   | contradicted 42   | contradicted 63   |
|:----------------|:----------------|:-----------------|:-----------------|:------------------|:------------------|:------------------|
| rr_fade_extreme | 0 [0-79] n=1    | 100 [21-100] n=1 | 100 [21-100] n=1 | 60 [23-88] n=5    | 50 [15-85] n=4    | 67 [21-94] n=3    |
| rr_z_follow     | 57 [39-73] n=28 | 39 [20-61] n=18  | 50 [25-75] n=12  | 50 [27-73] n=14   | 50 [24-76] n=10   | 75 [41-93] n=8    |
| rr_d21          | 58 [39-76] n=24 | 38 [18-61] n=16  | 33 [14-61] n=12  | 48 [29-67] n=23   | 53 [31-74] n=17   | 38 [18-64] n=13   |
| rr_spot_div     | 57 [25-84] n=7  | 57 [25-84] n=7   | 57 [25-84] n=7   | 56 [34-75] n=18   | 53 [30-75] n=15   | 27 [10-57] n=11   |
| rr_orth         | 54 [35-71] n=26 | 35 [17-59] n=17  | 46 [23-71] n=13  | 67 [44-84] n=18   | 54 [29-77] n=13   | 80 [49-94] n=10   |
| vrp_level       | 36 [16-61] n=14 | 33 [12-65] n=9   | 17 [3-56] n=6    | 50 [27-73] n=14   | 44 [19-73] n=9    | 50 [22-78] n=8    |
| vrp_d21         | 35 [17-59] n=17 | 30 [11-60] n=10  | 14 [3-51] n=7    | 50 [27-73] n=14   | 62 [31-86] n=8    | 88 [53-98] n=8    |
| agree3_vrp_gate | 27 [10-57] n=11 | 29 [8-64] n=7    | 0 [0-43] n=5     | 53 [31-74] n=17   | 50 [25-75] n=12   | 38 [14-69] n=8    |
| ts_slope        | -               | -                | -                | -                 | -                 | -                 |
| opt_nc_z52      | 42 [24-61] n=24 | 44 [23-67] n=16  | 36 [15-65] n=11  | 63 [41-81] n=19   | 58 [32-81] n=12   | 78 [45-94] n=9    |
| opt_lev_z52     | 46 [30-64] n=28 | 47 [25-70] n=15  | 67 [39-86] n=12  | 45 [26-66] n=20   | 43 [21-67] n=14   | 40 [17-69] n=10   |

### (c) Paired differences, weekly grid, circular block bootstrap (2000 draws; points; p = share of draws <= 0, one-sided, NOT adjusted for 12 candidates)

| signal          |   h | period   | AND acc n   | agreement same span   | AND - agreement             | contradicted acc n   | confirmed - contradicted    |
|:----------------|----:|:---------|:------------|:----------------------|:----------------------------|:---------------------|:----------------------------|
| rr_fade_extreme |  21 | 2010-26  | 50.0 n=6    | 59.2 n=382            | -9.2 [-57.7, +45.5] p=0.59  | 60.9 n=23            | -10.9 [-60.7, +55.9] p=0.58 |
| rr_fade_extreme |  21 | 2016-26  | 40.0 n=5    | 56.7 n=238            | -16.7 [-59.1, +47.9] p=0.64 | 50.0 n=12            | -10.0 [-64.1, +72.7] p=0.56 |
| rr_fade_extreme |  42 | 2010-26  | 83.3 n=6    | 64.7 n=382            | +18.7 [+0.3, +41.3] p=0.02  | 78.3 n=23            | +5.1 [-21.6, +42.1] p=0.36  |
| rr_fade_extreme |  42 | 2016-26  | 80.0 n=5    | 63.0 n=238            | +17.0 [-2.9, +43.8] p=0.04  | 83.3 n=12            | -3.3 [-30.7, +40.0] p=0.52  |
| rr_fade_extreme |  63 | 2010-26  | 66.7 n=6    | 66.5 n=382            | +0.2 [-59.9, +36.0] p=0.47  | 73.9 n=23            | -7.2 [-66.7, +43.9] p=0.62  |
| rr_fade_extreme |  63 | 2016-26  | 80.0 n=5    | 66.8 n=238            | +13.2 [-4.2, +42.3] p=0.07  | 75.0 n=12            | +5.0 [-26.7, +64.6] p=0.38  |
| rr_z_follow     |  21 | 2010-26  | 62.4 n=287  | 59.2 n=382            | +3.2 [-0.5, +7.0] p=0.04    | 49.5 n=95            | +12.9 [-2.0, +29.3] p=0.04  |
| rr_z_follow     |  21 | 2016-26  | 61.1 n=185  | 56.7 n=238            | +4.4 [-0.3, +8.7] p=0.03    | 41.5 n=53            | +19.6 [-1.3, +38.8] p=0.03  |
| rr_z_follow     |  42 | 2010-26  | 65.2 n=287  | 64.7 n=382            | +0.5 [-4.1, +4.9] p=0.40    | 63.2 n=95            | +2.0 [-15.1, +21.5] p=0.40  |
| rr_z_follow     |  42 | 2016-26  | 64.9 n=185  | 63.0 n=238            | +1.8 [-3.6, +6.9] p=0.27    | 56.6 n=53            | +8.3 [-15.0, +31.8] p=0.27  |
| rr_z_follow     |  63 | 2010-26  | 66.9 n=287  | 66.5 n=382            | +0.4 [-3.9, +4.4] p=0.41    | 65.3 n=95            | +1.6 [-14.2, +19.7] p=0.41  |
| rr_z_follow     |  63 | 2016-26  | 67.6 n=185  | 66.8 n=238            | +0.8 [-4.0, +5.5] p=0.39    | 64.2 n=53            | +3.4 [-17.3, +26.4] p=0.39  |
| rr_d21          |  21 | 2010-26  | 63.0 n=227  | 59.2 n=382            | +3.8 [-0.5, +8.9] p=0.05    | 53.5 n=155           | +9.4 [-1.4, +22.1] p=0.05   |
| rr_d21          |  21 | 2016-26  | 62.0 n=142  | 56.7 n=238            | +5.2 [-0.7, +11.5] p=0.05   | 49.0 n=96            | +13.0 [-1.6, +27.7] p=0.05  |
| rr_d21          |  42 | 2010-26  | 65.6 n=227  | 64.7 n=382            | +1.0 [-3.4, +5.5] p=0.32    | 63.2 n=155           | +2.4 [-8.4, +13.4] p=0.32   |
| rr_d21          |  42 | 2016-26  | 64.1 n=142  | 63.0 n=238            | +1.1 [-4.1, +6.1] p=0.36    | 61.5 n=96            | +2.6 [-10.3, +15.2] p=0.36  |
| rr_d21          |  63 | 2010-26  | 66.5 n=227  | 66.5 n=382            | +0.0 [-4.1, +4.4] p=0.50    | 66.5 n=155           | +0.1 [-9.9, +10.6] p=0.50   |
| rr_d21          |  63 | 2016-26  | 66.9 n=142  | 66.8 n=238            | +0.1 [-4.0, +5.0] p=0.48    | 66.7 n=96            | +0.2 [-10.0, +12.4] p=0.48  |
| rr_spot_div     |  21 | 2010-26  | 73.1 n=26   | 59.2 n=382            | +13.9 [-4.4, +32.3] p=0.06  | 54.4 n=103           | +18.7 [-2.0, +41.4] p=0.04  |
| rr_spot_div     |  21 | 2016-26  | 80.0 n=15   | 56.7 n=238            | +23.3 [+1.2, +45.9] p=0.02  | 46.4 n=56            | +33.6 [+7.0, +59.7] p=0.01  |
| rr_spot_div     |  42 | 2010-26  | 80.8 n=26   | 64.7 n=382            | +16.1 [-0.3, +32.4] p=0.03  | 58.3 n=103           | +22.5 [+2.5, +42.9] p=0.02  |
| rr_spot_div     |  42 | 2016-26  | 80.0 n=15   | 63.0 n=238            | +17.0 [-4.2, +40.9] p=0.06  | 53.6 n=56            | +26.4 [+2.0, +53.3] p=0.02  |
| rr_spot_div     |  63 | 2010-26  | 73.1 n=26   | 66.5 n=382            | +6.6 [-22.9, +28.8] p=0.30  | 61.2 n=103           | +11.9 [-22.3, +38.8] p=0.22 |
| rr_spot_div     |  63 | 2016-26  | 66.7 n=15   | 66.8 n=238            | -0.1 [-31.4, +34.4] p=0.46  | 58.9 n=56            | +7.7 [-27.8, +50.0] p=0.32  |
| rr_orth         |  21 | 2010-26  | 63.3 n=248  | 59.2 n=382            | +4.1 [-0.5, +8.5] p=0.04    | 51.5 n=134           | +11.8 [-1.5, +24.9] p=0.04  |
| rr_orth         |  21 | 2016-26  | 61.6 n=164  | 56.7 n=238            | +4.9 [-0.5, +10.1] p=0.04   | 45.9 n=74            | +15.6 [-1.7, +31.7] p=0.04  |
| rr_orth         |  42 | 2010-26  | 65.7 n=248  | 64.7 n=382            | +1.1 [-5.2, +6.8] p=0.36    | 62.7 n=134           | +3.0 [-13.8, +20.1] p=0.36  |
| rr_orth         |  42 | 2016-26  | 66.5 n=164  | 63.0 n=238            | +3.4 [-3.4, +10.2] p=0.17   | 55.4 n=74            | +11.1 [-11.0, +32.4] p=0.17 |
| rr_orth         |  63 | 2010-26  | 66.9 n=248  | 66.5 n=382            | +0.4 [-5.8, +6.0] p=0.43    | 65.7 n=134           | +1.3 [-15.6, +17.5] p=0.43  |
| rr_orth         |  63 | 2016-26  | 67.7 n=164  | 66.8 n=238            | +0.9 [-5.9, +7.2] p=0.41    | 64.9 n=74            | +2.8 [-17.9, +25.0] p=0.41  |
| vrp_level       |  21 | 2010-26  | 58.8 n=177  | 58.9 n=350            | -0.1 [-6.5, +6.2] p=0.53    | 59.0 n=173           | -0.2 [-13.4, +12.5] p=0.53  |
| vrp_level       |  21 | 2016-26  | 54.3 n=105  | 55.8 n=206            | -1.5 [-9.9, +7.0] p=0.67    | 57.4 n=101           | -3.1 [-20.0, +14.0] p=0.67  |
| vrp_level       |  42 | 2010-26  | 66.1 n=177  | 66.0 n=350            | +0.1 [-7.2, +7.0] p=0.49    | 65.9 n=173           | +0.2 [-14.3, +14.2] p=0.49  |
| vrp_level       |  42 | 2016-26  | 65.7 n=105  | 65.0 n=206            | +0.7 [-7.9, +9.2] p=0.47    | 64.4 n=101           | +1.4 [-15.5, +18.4] p=0.47  |
| vrp_level       |  63 | 2010-26  | 70.1 n=177  | 68.0 n=350            | +2.1 [-4.9, +9.0] p=0.29    | 65.9 n=173           | +4.2 [-10.0, +17.6] p=0.29  |
| vrp_level       |  63 | 2016-26  | 71.4 n=105  | 69.4 n=206            | +2.0 [-5.3, +10.1] p=0.33   | 67.3 n=101           | +4.1 [-10.8, +19.8] p=0.33  |
| vrp_d21         |  21 | 2010-26  | 56.3 n=167  | 58.9 n=350            | -2.6 [-8.8, +3.6] p=0.80    | 61.2 n=183           | -4.9 [-16.5, +7.1] p=0.80   |
| vrp_d21         |  21 | 2016-26  | 50.5 n=93   | 55.8 n=206            | -5.3 [-14.4, +3.2] p=0.90   | 60.2 n=113           | -9.6 [-25.3, +5.9] p=0.90   |
| vrp_d21         |  42 | 2010-26  | 68.9 n=167  | 66.0 n=350            | +2.9 [-3.2, +9.0] p=0.18    | 63.4 n=183           | +5.5 [-6.2, +17.0] p=0.18   |
| vrp_d21         |  42 | 2016-26  | 67.7 n=93   | 65.0 n=206            | +2.7 [-6.0, +10.0] p=0.26   | 62.8 n=113           | +4.9 [-10.5, +18.9] p=0.26  |
| vrp_d21         |  63 | 2010-26  | 70.1 n=167  | 68.0 n=350            | +2.1 [-4.0, +8.5] p=0.25    | 66.1 n=183           | +3.9 [-7.9, +16.0] p=0.25   |
| vrp_d21         |  63 | 2016-26  | 73.1 n=93   | 69.4 n=206            | +3.7 [-2.9, +9.7] p=0.12    | 66.4 n=113           | +6.7 [-5.0, +18.1] p=0.12   |
| agree3_vrp_gate |  21 | 2010-26  | 58.2 n=165  | 58.6 n=319            | -0.4 [-6.7, +5.8] p=0.56    | 59.1 n=154           | -0.9 [-13.6, +11.8] p=0.56  |
| agree3_vrp_gate |  21 | 2016-26  | 57.4 n=101  | 55.8 n=206            | +1.6 [-6.6, +9.8] p=0.38    | 54.3 n=105           | +3.1 [-12.9, +19.4] p=0.38  |
| agree3_vrp_gate |  42 | 2010-26  | 66.1 n=165  | 66.5 n=319            | -0.4 [-6.6, +5.7] p=0.53    | 66.9 n=154           | -0.8 [-13.5, +12.0] p=0.53  |
| agree3_vrp_gate |  42 | 2016-26  | 70.3 n=101  | 65.0 n=206            | +5.2 [-2.2, +13.5] p=0.09   | 60.0 n=105           | +10.3 [-4.2, +26.1] p=0.09  |
| agree3_vrp_gate |  63 | 2010-26  | 68.5 n=165  | 69.0 n=319            | -0.5 [-6.6, +5.3] p=0.56    | 69.5 n=154           | -1.0 [-13.7, +10.9] p=0.56  |
| agree3_vrp_gate |  63 | 2016-26  | 73.3 n=101  | 69.4 n=206            | +3.8 [-2.8, +10.1] p=0.13   | 65.7 n=105           | +7.6 [-5.3, +19.5] p=0.13   |
| ts_slope        |  21 | 2010-26  | 61.0 n=164  | 59.4 n=286            | +1.5 [-4.8, +7.9] p=0.32    | 57.4 n=122           | +3.6 [-11.2, +18.1] p=0.32  |
| ts_slope        |  21 | 2016-26  | 58.5 n=94   | 55.6 n=142            | +2.9 [-4.0, +10.0] p=0.19   | 50.0 n=48            | +8.5 [-11.7, +28.5] p=0.19  |
| ts_slope        |  42 | 2010-26  | 70.7 n=164  | 67.8 n=286            | +2.9 [-4.2, +10.0] p=0.21   | 63.9 n=122           | +6.8 [-9.6, +23.7] p=0.21   |
| ts_slope        |  42 | 2016-26  | 75.5 n=94   | 68.3 n=142            | +7.2 [-0.3, +15.4] p=0.03   | 54.2 n=48            | +21.4 [-0.9, +42.9] p=0.03  |
| ts_slope        |  63 | 2010-26  | 72.0 n=164  | 68.9 n=286            | +3.1 [-5.7, +10.4] p=0.24   | 64.8 n=122           | +7.2 [-12.5, +26.4] p=0.24  |
| ts_slope        |  63 | 2016-26  | 78.7 n=94   | 71.8 n=142            | +6.9 [-2.0, +16.7] p=0.07   | 58.3 n=48            | +20.4 [-6.1, +47.7] p=0.07  |
| opt_nc_z52      |  21 | 2010-26  | 59.6 n=208  | 59.4 n=387            | +0.2 [-6.0, +6.3] p=0.50    | 59.2 n=179           | +0.4 [-12.7, +13.4] p=0.50  |
| opt_nc_z52      |  21 | 2016-26  | 56.1 n=148  | 57.2 n=243            | -1.1 [-8.0, +5.8] p=0.61    | 58.9 n=95            | -2.9 [-20.3, +15.1] p=0.61  |
| opt_nc_z52      |  42 | 2010-26  | 64.6 n=206  | 64.8 n=383            | -0.2 [-6.6, +6.3] p=0.52    | 65.0 n=177           | -0.4 [-13.9, +13.2] p=0.52  |
| opt_nc_z52      |  42 | 2016-26  | 62.3 n=146  | 63.2 n=239            | -0.9 [-7.0, +5.9] p=0.58    | 64.5 n=93            | -2.2 [-18.6, +14.7] p=0.58  |
| opt_nc_z52      |  63 | 2010-26  | 67.5 n=206  | 66.6 n=383            | +0.9 [-6.7, +7.9] p=0.41    | 65.5 n=177           | +1.9 [-14.0, +17.4] p=0.41  |
| opt_nc_z52      |  63 | 2016-26  | 68.5 n=146  | 66.9 n=239            | +1.5 [-6.5, +8.1] p=0.33    | 64.5 n=93            | +4.0 [-15.9, +22.1] p=0.33  |
| opt_fut_div     |  21 | 2010-26  | - n=0       | -                     | -                           | - n=179              | -                           |
| opt_fut_div     |  21 | 2016-26  | - n=0       | -                     | -                           | - n=95               | -                           |
| opt_fut_div     |  42 | 2010-26  | - n=0       | -                     | -                           | - n=177              | -                           |
| opt_fut_div     |  42 | 2016-26  | - n=0       | -                     | -                           | - n=93               | -                           |
| opt_fut_div     |  63 | 2010-26  | - n=0       | -                     | -                           | - n=177              | -                           |
| opt_fut_div     |  63 | 2016-26  | - n=0       | -                     | -                           | - n=93               | -                           |
| opt_lev_z52     |  21 | 2010-26  | 61.9 n=210  | 59.4 n=387            | +2.5 [-3.3, +8.4] p=0.21    | 56.5 n=177           | +5.4 [-6.9, +18.4] p=0.21   |
| opt_lev_z52     |  21 | 2016-26  | 58.3 n=144  | 57.2 n=243            | +1.1 [-5.9, +7.9] p=0.37    | 55.6 n=99            | +2.8 [-13.8, +20.7] p=0.37  |
| opt_lev_z52     |  42 | 2010-26  | 65.6 n=209  | 64.8 n=383            | +0.8 [-6.2, +8.0] p=0.41    | 63.8 n=174           | +1.8 [-13.4, +17.7] p=0.41  |
| opt_lev_z52     |  42 | 2016-26  | 59.4 n=143  | 63.2 n=239            | -3.7 [-12.2, +4.1] p=0.82   | 68.8 n=96            | -9.3 [-27.1, +11.0] p=0.82  |
| opt_lev_z52     |  63 | 2010-26  | 69.9 n=209  | 66.6 n=383            | +3.3 [-4.0, +9.1] p=0.16    | 62.6 n=174           | +7.2 [-7.9, +21.5] p=0.16   |
| opt_lev_z52     |  63 | 2016-26  | 67.8 n=143  | 66.9 n=239            | +0.9 [-6.9, +7.8] p=0.37    | 65.6 n=96            | +2.2 [-15.6, +23.3] p=0.37  |

### (b) Does the signal extend coverage? Calls on sessions where the three old signals do NOT agree (non-overlapping; live, 63 and 126 sessions stale)


*2010-26*

| signal          | live 21                   | live 42                 | live 63                 | stale63 21   | stale63 42   | stale63 63   | stale126 21   | stale126 42   | stale126 63   |
|:----------------|:--------------------------|:------------------------|:------------------------|:-------------|:-------------|:-------------|:--------------|:--------------|:--------------|
| rr_fade_extreme | 33 [19-51] n=30 (1.8/y)   | 50 [31-69] n=24 (1.4/y) | 47 [27-68] n=19 (1.1/y) | 29 n=35      | 37 n=30      | 46 n=24      | 37 n=35       | 44 n=27       | 52 n=21       |
| rr_z_follow     | 54 [46-61] n=168 (10.0/y) | 54 [44-64] n=92 (5.5/y) | 56 [44-68] n=64 (3.9/y) | 51 n=170     | 52 n=93      | 50 n=64      | 48 n=170      | 48 n=93       | 44 n=64       |
| rr_d21          | 50 [43-57] n=168 (10.0/y) | 48 [38-58] n=92 (5.5/y) | 47 [35-59] n=64 (3.9/y) | 53 n=170     | 55 n=93      | 47 n=64      | 55 n=170      | 58 n=93       | 52 n=64       |
| rr_spot_div     | 50 [41-58] n=127 (7.6/y)  | 56 [45-66] n=82 (4.9/y) | 55 [42-68] n=56 (3.4/y) | 42 n=124     | 57 n=79      | 41 n=54      | 55 n=119      | 57 n=79       | 50 n=52       |
| rr_orth         | 54 [47-62] n=168 (10.0/y) | 53 [43-63] n=92 (5.5/y) | 56 [44-68] n=64 (3.9/y) | 51 n=170     | 51 n=93      | 45 n=64      | 52 n=170      | 54 n=93       | 45 n=64       |
| vrp_level       | 55 [47-63] n=153 (9.1/y)  | 58 [48-68] n=84 (5.0/y) | 61 [48-72] n=59 (3.6/y) | 51 n=156     | 52 n=86      | 63 n=60      | 53 n=158      | 54 n=87       | 57 n=61       |
| vrp_d21         | 48 [40-56] n=153 (9.1/y)  | 55 [44-65] n=84 (5.0/y) | 59 [47-71] n=59 (3.6/y) | 51 n=156     | 55 n=86      | 63 n=60      | 50 n=158      | 53 n=87       | 52 n=61       |
| ts_slope        | 52 [43-61] n=125 (7.5/y)  | 50 [38-62] n=68 (4.1/y) | 60 [45-72] n=47 (2.8/y) | 59 n=127     | 62 n=69      | 56 n=48      | 55 n=129      | 56 n=71       | 61 n=49       |
| opt_nc_z52      | 45 [38-53] n=170 (10.1/y) | 40 [30-50] n=93 (5.6/y) | 42 [31-54] n=64 (3.9/y) | 52 n=170     | 58 n=93      | 53 n=64      | 44 n=170      | 47 n=93       | 55 n=64       |
| opt_fut_div     | 40 [32-50] n=109 (6.5/y)  | 43 [32-55] n=65 (3.9/y) | 31 [20-45] n=49 (3.0/y) | 50 n=106     | 52 n=67      | 52 n=50      | 50 n=111      | 50 n=68       | 53 n=51       |
| opt_lev_z52     | 52 [45-60] n=170 (10.1/y) | 56 [46-66] n=93 (5.6/y) | 48 [37-60] n=64 (3.9/y) | 53 n=170     | 51 n=93      | 48 n=64      | 46 n=170      | 46 n=93       | 56 n=64       |

*2016-26*

| signal          | live 21                   | live 42                 | live 63                 | stale63 21   | stale63 42   | stale63 63   | stale126 21   | stale126 42   | stale126 63   |
|:----------------|:--------------------------|:------------------------|:------------------------|:-------------|:-------------|:-------------|:--------------|:--------------|:--------------|
| rr_fade_extreme | 37 [19-59] n=19 (1.8/y)   | 56 [33-77] n=16 (1.5/y) | 50 [25-75] n=12 (1.1/y) | 42 n=19      | 39 n=18      | 53 n=15      | 38 n=21       | 47 n=17       | 57 n=14       |
| rr_z_follow     | 51 [42-61] n=107 (9.9/y)  | 49 [37-62] n=59 (5.5/y) | 61 [46-74] n=41 (3.9/y) | 50 n=109     | 52 n=60      | 56 n=41      | 49 n=109      | 47 n=60       | 46 n=41       |
| rr_d21          | 45 [36-54] n=107 (9.9/y)  | 39 [28-52] n=59 (5.5/y) | 46 [32-61] n=41 (3.9/y) | 50 n=109     | 52 n=60      | 49 n=41      | 60 n=109      | 62 n=60       | 61 n=41       |
| rr_spot_div     | 49 [38-60] n=80 (7.4/y)   | 65 [51-76] n=54 (5.1/y) | 59 [42-74] n=34 (3.2/y) | 44 n=80      | 61 n=49      | 38 n=34      | 53 n=77       | 57 n=51       | 42 n=33       |
| rr_orth         | 51 [42-61] n=107 (9.9/y)  | 51 [38-63] n=59 (5.5/y) | 59 [43-72] n=41 (3.9/y) | 52 n=109     | 48 n=60      | 49 n=41      | 52 n=109      | 53 n=60       | 46 n=41       |
| vrp_level       | 54 [44-64] n=92 (8.6/y)   | 59 [45-71] n=51 (4.8/y) | 67 [50-80] n=36 (3.4/y) | 52 n=95      | 47 n=53      | 57 n=37      | 56 n=97       | 54 n=54       | 53 n=38       |
| vrp_d21         | 43 [34-54] n=92 (8.6/y)   | 51 [38-64] n=51 (4.8/y) | 67 [50-80] n=36 (3.4/y) | 53 n=95      | 49 n=53      | 51 n=37      | 48 n=97       | 48 n=54       | 42 n=38       |
| ts_slope        | 55 [43-66] n=64 (5.9/y)   | 51 [36-67] n=35 (3.3/y) | 62 [43-79] n=24 (2.3/y) | 56 n=66      | 61 n=36      | 52 n=25      | 49 n=68       | 53 n=38       | 58 n=26       |
| opt_nc_z52      | 46 [37-55] n=109 (10.1/y) | 43 [32-56] n=60 (5.6/y) | 54 [39-68] n=41 (3.9/y) | 54 n=109     | 58 n=60      | 56 n=41      | 43 n=109      | 48 n=60       | 59 n=41       |
| opt_fut_div     | 42 [31-54] n=64 (5.9/y)   | 45 [30-60] n=38 (3.6/y) | 37 [22-54] n=30 (2.8/y) | 50 n=64      | 54 n=41      | 52 n=31      | 50 n=68       | 48 n=42       | 52 n=33       |
| opt_lev_z52     | 55 [46-64] n=109 (10.1/y) | 58 [46-70] n=60 (5.6/y) | 49 [34-64] n=41 (3.9/y) | 54 n=109     | 52 n=60      | 49 n=41      | 47 n=109      | 48 n=60       | 54 n=41       |

### VRP as a conditioning variable

The agreement rule on each side of the VRP state (implied minus realised above / below its trailing-252 mean), fixed split, no selection:

| decisions   | period   | vrp_high 21      | vrp_high 42     | vrp_high 63     | vrp_low 21      | vrp_low 42      | vrp_low 63      |
|:------------|:---------|:-----------------|:----------------|:----------------|:----------------|:----------------|:----------------|
| weekly      | 2010-26  | 55 n=169         | 62 n=169        | 64 n=169        | 62 n=181        | 70 n=181        | 72 n=181        |
| weekly      | 2016-26  | 54 n=105         | 60 n=105        | 66 n=105        | 57 n=101        | 70 n=101        | 73 n=101        |
| weekly      | 2023-26  | 45 n=22          | 32 n=22         | 50 n=22         | 44 n=18         | 56 n=18         | 61 n=18         |
| nonoverlap  | 2010-26  | 51 [42-61] n=103 | 61 [49-72] n=67 | 57 [42-70] n=46 | 58 [48-67] n=98 | 57 [45-68] n=65 | 66 [51-78] n=44 |
| nonoverlap  | 2016-26  | 53 [41-65] n=62  | 61 [46-74] n=41 | 52 [34-69] n=27 | 51 [38-63] n=57 | 55 [40-70] n=38 | 60 [41-77] n=25 |
| nonoverlap  | 2023-26  | 53 [31-74] n=17  | 50 [25-75] n=12 | 38 [14-69] n=8  | 27 [10-57] n=11 | 29 [8-64] n=7   | 0 [0-43] n=5    |

Side chosen for candidate 8 from the training window (weekly 21-session agreement calls with a label known before the test year):

|   test_year |   n_high |   acc_high |   n_low |   acc_low | open_side   |
|------------:|---------:|-----------:|--------:|----------:|:------------|
|        2010 |       20 |      0.4   |      13 |     0.538 |             |
|        2011 |       37 |      0.541 |      30 |     0.533 | high VRP    |
|        2012 |       51 |      0.49  |      45 |     0.644 | low VRP     |
|        2013 |       63 |      0.508 |      64 |     0.641 | low VRP     |
|        2014 |       66 |      0.5   |      69 |     0.638 | low VRP     |
|        2015 |       81 |      0.531 |      78 |     0.667 | low VRP     |
|        2016 |       85 |      0.529 |      94 |     0.66  | low VRP     |
|        2017 |      102 |      0.539 |     101 |     0.653 | low VRP     |
|        2018 |      110 |      0.555 |     113 |     0.655 | low VRP     |
|        2019 |      123 |      0.569 |     121 |     0.645 | low VRP     |
|        2020 |      127 |      0.559 |     126 |     0.643 | low VRP     |
|        2021 |      137 |      0.577 |     141 |     0.624 | low VRP     |
|        2022 |      155 |      0.542 |     157 |     0.618 | low VRP     |
|        2023 |      168 |      0.548 |     174 |     0.626 | low VRP     |
|        2024 |      178 |      0.545 |     184 |     0.62  | low VRP     |
|        2025 |      190 |      0.537 |     195 |     0.615 | low VRP     |
|        2026 |      190 |      0.537 |     196 |     0.617 | low VRP     |

Reading of the three sub-tests.
* (a) On the bar's own measure nothing passes: the largest two-horizon, two-period minimum gain is `rr_d21`'s +1.2 points, and wherever a 42-session
  gain appears (RR family +3 to +10, slope +6 to +10) a stale copy does as well or better. Non-overlapping streams of different rules start on
  different sessions, so single cells move by several points for no reason; that is why the weekly grid and the paired bootstrap are shown next to it.
* On the weekly grid the RR family lifts the 21-session accuracy from 59 to 62-63 % (2010-26) and from 57 to 61-62 % (2016-26); stale copies fall
  back to 56-60 %. At 42 and 63 sessions the lift is 0-2 points. VRP, the gate, option positioning: within +-3 points, wrong-signed as often as not.
  `rr_spot_div` (options leaning against the month's move) confirms very few calls (26 weekly decisions in 17 years, 2 non-overlapping a year):
  73-81 % on those, far too few to mean anything, and its contradicted side is the same 54-58 % as the others'.
* (c) The paired intervals for "AND minus agreement" include zero for every candidate, horizon and period except `rr_fade_extreme` and `rr_spot_div`
  cells built on 5-26 decisions. The smallest honest p-values are 0.03-0.05 for the RR family at 21 sessions; 66 such tests were run on 11 candidates.
* (b) Outside the agreement rule (where the three old signals disagree) no signal makes a usable call: 33-58 % at 21-42 sessions, live no better than
  stale. The options market does not extend coverage.
* Confirmed against contradicted on non-overlapping decisions (table above): for the skew 59 against 49 % at 21 sessions in 2010-26 and 55 against 52 %
  in 2016-26; for the orthogonalised skew 59 against 55 % and 56 against 61 %; at 42-63 sessions no gap. The weekly-grid veto of verdict 4 is not
  confirmed here.

## 7 Selection by the declared rule, and the final rule's record

| signal          |   n_2010-15 |   dec_per_year_2010-15 |   accuracy_2010-15 |   lo_2010-15 |   hi_2010-15 | eligible   | final   |
|:----------------|------------:|-----------------------:|-------------------:|-------------:|-------------:|:-----------|:--------|
| rr_fade_extreme |           1 |                  0.167 |              0     |        0     |        0.793 | False      | False   |
| rr_z_follow     |          45 |                  7.515 |              0.667 |        0.521 |        0.786 | True       | True    |
| rr_d21          |          45 |                  7.515 |              0.556 |        0.412 |        0.691 | True       | False   |
| rr_spot_div     |          14 |                  2.338 |              0.714 |        0.454 |        0.883 | False      | False   |
| rr_orth         |          38 |                  6.346 |              0.658 |        0.499 |        0.788 | True       | False   |
| vrp_level       |          41 |                  6.847 |              0.634 |        0.481 |        0.764 | True       | False   |
| vrp_d21         |          45 |                  7.515 |              0.622 |        0.476 |        0.749 | True       | False   |
| agree3_vrp_gate |          37 |                  6.179 |              0.568 |        0.409 |        0.713 | True       | False   |
| ts_slope        |          36 |                  6.012 |              0.472 |        0.32  |        0.63  | True       | False   |
| opt_nc_z52      |          32 |                  5.344 |              0.562 |        0.393 |        0.718 | False      | False   |
| opt_fut_div     |           0 |                  0     |            nan     |      nan     |      nan     | False      | False   |
| opt_lev_z52     |          34 |                  5.678 |              0.647 |        0.479 |        0.785 | False      | False   |

**Final: `and_rr_z_follow`** - selected by the declared rule.

|   h | period   |   agree3_acc |   agree3_n |   same_span_acc |   same_span_n |   and_acc |   and_lo |   and_hi |   and_n |   and_per_year |   gain_pts |   placebo63_gain_pts |   placebo126_gain_pts |
|----:|:---------|-------------:|-----------:|----------------:|--------------:|----------:|---------:|---------:|--------:|---------------:|-----------:|---------------------:|----------------------:|
|  21 | 2010-26  |        0.59  |        156 |           0.591 |           154 |     0.592 |    0.504 |    0.674 |     125 |          7.459 |      0.109 |               -5.037 |                -6.261 |
|  21 | 2016-26  |        0.573 |         96 |           0.574 |            94 |     0.55  |    0.441 |    0.654 |      80 |          7.435 |     -2.447 |               -1.282 |                -3.161 |
|  21 | 2023-26  |        0.6   |         35 |           0.606 |            33 |     0.571 |    0.391 |    0.735 |      28 |          7.438 |     -3.463 |               -1.515 |                 4.394 |
|  42 | 2010-26  |        0.607 |         89 |           0.602 |            88 |     0.645 |    0.533 |    0.743 |      76 |          4.557 |      4.246 |                5.444 |                -1.136 |
|  42 | 2016-26  |        0.589 |         56 |           0.582 |            55 |     0.612 |    0.472 |    0.736 |      49 |          4.588 |      3.043 |                5.455 |                 2.283 |
|  42 | 2023-26  |        0.45  |         20 |           0.421 |            19 |     0.389 |    0.203 |    0.614 |      18 |          4.884 |     -3.216 |               11.741 |                 4.049 |
|  63 | 2010-26  |        0.721 |         61 |           0.717 |            60 |     0.704 |    0.572 |    0.809 |      54 |          3.253 |     -1.296 |               -1.667 |                -6.282 |
|  63 | 2016-26  |        0.711 |         38 |           0.703 |            37 |     0.686 |    0.52  |    0.814 |      35 |          3.302 |     -1.699 |               -3.604 |                -0.573 |
|  63 | 2023-26  |        0.5   |         14 |           0.462 |            13 |     0.5   |    0.254 |    0.746 |      12 |          3.328 |      3.846 |               -0.699 |                 8.392 |

Hit rate of the final rule's weekly decisions (21-session hold; gross = correct sign, net = positive after a 2.4-pip round trip):

| period   |   decisions |   hit_gross |   hit_net |   net_bp |
|:---------|------------:|------------:|----------:|---------:|
| 2010-26  |         287 |       0.624 |     0.62  |   64.02  |
| 2016-26  |         185 |       0.611 |     0.611 |   53.629 |
| 2023-26  |          60 |       0.567 |     0.567 |   31.793 |

By year (weekly decisions):

|   year |   decisions |   long_share |   accuracy |   net_bp |   agree3_decisions |   agree3_accuracy |
|-------:|------------:|-------------:|-----------:|---------:|-------------------:|------------------:|
|   2010 |          29 |        0.345 |      0.655 |  111.334 |                 31 |             0.613 |
|   2011 |          30 |        0.467 |      0.633 |  109.012 |                 33 |             0.636 |
|   2012 |           9 |        1     |      0.889 |  100.143 |                 28 |             0.607 |
|   2013 |           6 |        1     |      0.333 | -139.488 |                  7 |             0.429 |
|   2014 |          11 |        0.273 |      0.636 |   55.544 |                 24 |             0.75  |
|   2015 |          17 |        0.294 |      0.647 |   75.184 |                 21 |             0.619 |
|   2016 |          18 |        0.5   |      0.722 |   66.72  |                 24 |             0.583 |
|   2017 |          12 |        1     |      0.583 |   91.362 |                 19 |             0.684 |
|   2018 |          21 |        0     |      0.619 |   50.853 |                 21 |             0.619 |
|   2019 |           9 |        1     |      0.444 |  -37.69  |                 12 |             0.5   |
|   2020 |          15 |        1     |      0.533 |   45.031 |                 25 |             0.52  |
|   2021 |          26 |        0.038 |      0.577 |   35.042 |                 34 |             0.441 |
|   2022 |          24 |        0.25  |      0.792 |  141.715 |                 31 |             0.742 |
|   2023 |          14 |        0.786 |      0.357 |  -43.75  |                 17 |             0.353 |
|   2024 |          17 |        0.176 |      0.588 |   60.528 |                 23 |             0.522 |
|   2025 |          18 |        1     |      0.611 |   64.481 |                 19 |             0.632 |
|   2026 |          11 |        0.182 |      0.727 |   30.04  |                 18 |             0.667 |

## 8 Daily stream and the incremental test (round 3 addendum)

Net Sharpe at 1.2 pips of each AND rule as a book of weekly tranches held 21 sessions:

| variant                 |   2010-2015 |   2010-2026 |   2016-2026 |   2023-2026 |
|:------------------------|------------:|------------:|------------:|------------:|
| agree3_reference        |        0.56 |        0.52 |        0.51 |        0.43 |
| and_agree3_vrp_gate     |        0.02 |        0.18 |        0.35 |        0.09 |
| and_opt_fut_div         |        0    |        0    |        0    |        0    |
| and_opt_lev_z52         |        0.39 |        0.42 |        0.44 |        0.4  |
| and_opt_nc_z52          |        0.48 |        0.45 |        0.44 |        0.11 |
| and_rr_d21              |        0.44 |        0.46 |        0.5  |        0.58 |
| and_rr_fade_extreme     |        0.06 |       -0.03 |       -0.06 |        0    |
| and_rr_orth             |        0.65 |        0.62 |        0.62 |        0.47 |
| and_rr_spot_div         |        0.42 |        0.37 |        0.41 |        1    |
| and_rr_z_follow         |        0.62 |        0.62 |        0.65 |        0.45 |
| and_rr_z_follow_cost0.6 |        0.63 |        0.63 |        0.66 |        0.47 |
| and_ts_slope            |        0.38 |        0.39 |        0.41 |        0    |
| and_vrp_d21             |        0.48 |        0.34 |        0.23 |        0.2  |
| and_vrp_level           |        0.34 |        0.32 |        0.32 |       -0.08 |

The same books with the signal 63 / 126 sessions stale:

| variant                      |   2010-2015 |   2010-2026 |   2016-2026 |   2023-2026 |
|:-----------------------------|------------:|------------:|------------:|------------:|
| and_agree3_vrp_gate_stale126 |        0.09 |        0.19 |        0.26 |        0.64 |
| and_agree3_vrp_gate_stale63  |        0.17 |        0.37 |        0.58 |        0.44 |
| and_opt_fut_div_stale126     |        0.04 |       -0.02 |       -0.06 |       -0.28 |
| and_opt_fut_div_stale63      |        0.33 |        0.34 |        0.36 |        0.63 |
| and_opt_lev_z52_stale126     |        0.33 |        0.39 |        0.46 |        0.48 |
| and_opt_lev_z52_stale63      |        0.64 |        0.53 |        0.46 |        0.12 |
| and_opt_nc_z52_stale126      |        0.2  |        0.43 |        0.57 |        0.71 |
| and_opt_nc_z52_stale63       |        0.46 |        0.59 |        0.65 |        0.34 |
| and_rr_d21_stale126          |        0.49 |        0.38 |        0.31 |        0.33 |
| and_rr_d21_stale63           |        0.49 |        0.42 |        0.39 |        0.38 |
| and_rr_fade_extreme_stale126 |       -0.63 |       -0.27 |        0.17 |        0.37 |
| and_rr_fade_extreme_stale63  |       -0.23 |       -0.13 |       -0.11 |       -0.57 |
| and_rr_orth_stale126         |        0.09 |        0.27 |        0.42 |        0.52 |
| and_rr_orth_stale63          |        0.44 |        0.41 |        0.4  |        0.43 |
| and_rr_spot_div_stale126     |        0.71 |        0.5  |        0.33 |        0.36 |
| and_rr_spot_div_stale63      |        0.2  |        0.15 |        0.11 |        0.34 |
| and_rr_z_follow_stale126     |        0.13 |        0.25 |        0.35 |        0.36 |
| and_rr_z_follow_stale63      |        0.43 |        0.43 |        0.46 |        0.54 |
| and_ts_slope_stale126        |        0.46 |        0.47 |        0.54 |        0    |
| and_ts_slope_stale63         |        0.64 |        0.55 |        0.5  |        0    |
| and_vrp_d21_stale126         |        0.63 |        0.52 |        0.44 |        0.41 |
| and_vrp_d21_stale63          |        0.4  |        0.42 |        0.44 |        0.35 |
| and_vrp_level_stale126       |        0.81 |        0.67 |        0.57 |        0.49 |
| and_vrp_level_stale63        |        0.37 |        0.35 |        0.35 |        0.3  |

Final stream:

| period    |    n |   sharpe |     t |   mean_bp |   active_frac |   deflated_sharpe_p |
|:----------|-----:|---------:|------:|----------:|--------------:|--------------------:|
| 2010-2026 | 4372 |    0.616 | 2.568 |     0.84  |         0.583 |               0.181 |
| 2016-2026 | 2816 |    0.645 | 2.157 |     0.705 |         0.586 |             nan     |
| 2023-2026 |  999 |    0.455 | 0.906 |     0.483 |         0.547 |             nan     |

Combination (meta.combine, EW) and daily P&L correlation of the final stream:

| combo                                                                 | period    |   sharpe |     t |
|:----------------------------------------------------------------------|:----------|---------:|------:|
| two-way weak_signals + regime_trend                                   | 2010-2026 |    0.563 | 2.347 |
| two-way weak_signals + regime_trend                                   | 2016-2026 |    0.636 | 2.128 |
| two-way weak_signals + regime_trend                                   | 2023-2026 |    0.356 | 0.708 |
| three-way + options_info                                              | 2010-2026 |    0.602 | 2.506 |
| three-way + options_info                                              | 2016-2026 |    0.696 | 2.329 |
| three-way + options_info                                              | 2023-2026 |    0.421 | 0.838 |
| three-way + selective (agreement rule book, for reference)            | 2010-2026 |    0.57  | 2.376 |
| three-way + selective (agreement rule book, for reference)            | 2016-2026 |    0.641 | 2.143 |
| three-way + selective (agreement rule book, for reference)            | 2023-2026 |    0.405 | 0.807 |
| three-way + options_info with the signal 63 sessions stale (placebo)  | 2010-2026 |    0.572 | 2.384 |
| three-way + options_info with the signal 63 sessions stale (placebo)  | 2016-2026 |    0.649 | 2.17  |
| three-way + options_info with the signal 63 sessions stale (placebo)  | 2023-2026 |    0.445 | 0.887 |
| three-way + options_info with the signal 126 sessions stale (placebo) | 2010-2026 |    0.509 | 2.12  |
| three-way + options_info with the signal 126 sessions stale (placebo) | 2016-2026 |    0.614 | 2.051 |
| three-way + options_info with the signal 126 sessions stale (placebo) | 2023-2026 |    0.406 | 0.809 |

| other                 |   corr_all_days |   corr_active_days |   corr_2016-26 |
|:----------------------|----------------:|-------------------:|---------------:|
| weak_signals          |            0.4  |               0.48 |           0.44 |
| regime_trend          |            0.59 |               0.75 |           0.59 |
| selective_daily       |            0.92 |               0.97 |           0.91 |
| options_info_stale63  |            0.81 |               0.85 |           0.78 |
| options_info_stale126 |            0.64 |               0.7  |           0.72 |

Daily net P&L of each AND book MINUS the agreement-rule book (bp a day, Newey-West t with 21 lags):

| signal          | version   |   diff_bp_day_2010-26 |   nw_t_2010-26 |   diff_bp_day_2016-26 |   nw_t_2016-26 |   diff_bp_day_2023-26 |   nw_t_2023-26 |
|:----------------|:----------|----------------------:|---------------:|----------------------:|---------------:|----------------------:|---------------:|
| rr_fade_extreme | live      |                 -0.82 |          -2.29 |                 -0.67 |          -1.92 |                 -0.51 |          -0.9  |
| rr_fade_extreme | stale63   |                 -0.84 |          -2.39 |                 -0.68 |          -2.02 |                 -0.58 |          -1.03 |
| rr_fade_extreme | stale126  |                 -0.87 |          -2.48 |                 -0.64 |          -1.82 |                 -0.48 |          -0.85 |
| rr_z_follow     | live      |                  0.03 |           0.21 |                  0.05 |           0.31 |                 -0.03 |          -0.12 |
| rr_z_follow     | stale63   |                 -0.27 |          -1.48 |                 -0.2  |          -0.93 |                 -0.14 |          -0.33 |
| rr_z_follow     | stale126  |                 -0.54 |          -2.2  |                 -0.33 |          -1.61 |                 -0.27 |          -0.63 |
| rr_d21          | live      |                 -0.31 |          -1.49 |                 -0.21 |          -1.12 |                  0.03 |           0.11 |
| rr_d21          | stale63   |                 -0.36 |          -1.93 |                 -0.37 |          -1.7  |                 -0.29 |          -0.77 |
| rr_d21          | stale126  |                 -0.41 |          -1.96 |                 -0.4  |          -1.83 |                 -0.3  |          -0.74 |
| rr_spot_div     | live      |                 -0.69 |          -2.05 |                 -0.58 |          -1.73 |                 -0.36 |          -0.65 |
| rr_spot_div     | stale63   |                 -0.74 |          -2.37 |                 -0.62 |          -2.01 |                 -0.43 |          -0.84 |
| rr_spot_div     | stale126  |                 -0.48 |          -1.7  |                 -0.5  |          -1.64 |                 -0.41 |          -0.8  |
| rr_orth         | live      |                 -0.04 |          -0.23 |                 -0.03 |          -0.14 |                 -0.02 |          -0.07 |
| rr_orth         | stale63   |                 -0.31 |          -1.59 |                 -0.26 |          -1.2  |                 -0.21 |          -0.48 |
| rr_orth         | stale126  |                 -0.51 |          -2.26 |                 -0.25 |          -1.33 |                 -0.17 |          -0.42 |
| vrp_level       | live      |                 -0.51 |          -2.11 |                 -0.4  |          -1.75 |                 -0.56 |          -1.4  |
| vrp_level       | stale63   |                 -0.47 |          -2.06 |                 -0.37 |          -1.63 |                 -0.27 |          -0.77 |
| vrp_level       | stale126  |                 -0.12 |          -0.61 |                 -0.15 |          -0.79 |                 -0.15 |          -0.41 |
| vrp_d21         | live      |                 -0.51 |          -2.13 |                 -0.5  |          -1.96 |                 -0.41 |          -0.94 |
| vrp_d21         | stale63   |                 -0.4  |          -1.86 |                 -0.28 |          -1.27 |                 -0.26 |          -0.64 |
| vrp_d21         | stale126  |                 -0.32 |          -1.47 |                 -0.29 |          -1.34 |                 -0.22 |          -0.55 |
| agree3_vrp_gate | live      |                 -0.64 |          -2.35 |                 -0.4  |          -1.57 |                 -0.46 |          -1.01 |
| agree3_vrp_gate | stale63   |                 -0.47 |          -1.75 |                 -0.24 |          -1.03 |                 -0.24 |          -0.57 |
| agree3_vrp_gate | stale126  |                 -0.65 |          -2.29 |                 -0.46 |          -1.91 |                 -0.12 |          -0.3  |
| ts_slope        | live      |                 -0.45 |          -1.69 |                 -0.35 |          -1.25 |                 -0.51 |          -0.9  |
| ts_slope        | stale63   |                 -0.28 |          -1.15 |                 -0.29 |          -1.06 |                 -0.51 |          -0.9  |
| ts_slope        | stale126  |                 -0.33 |          -1.5  |                 -0.27 |          -1.03 |                 -0.51 |          -0.9  |
| opt_nc_z52      | live      |                 -0.37 |          -1.45 |                 -0.25 |          -1.12 |                 -0.41 |          -1.22 |
| opt_nc_z52      | stale63   |                 -0.27 |          -1.03 |                 -0.03 |          -0.16 |                 -0.22 |          -0.69 |
| opt_nc_z52      | stale126  |                 -0.41 |          -1.51 |                 -0.14 |          -0.62 |                  0.09 |           0.3  |
| opt_fut_div     | live      |                 -0.81 |          -2.27 |                 -0.66 |          -1.87 |                 -0.51 |          -0.9  |
| opt_fut_div     | stale63   |                 -0.63 |          -1.96 |                 -0.49 |          -1.57 |                 -0.24 |          -0.5  |
| opt_fut_div     | stale126  |                 -0.82 |          -2.58 |                 -0.69 |          -2.21 |                 -0.61 |          -1.26 |
| opt_lev_z52     | live      |                 -0.39 |          -1.48 |                 -0.23 |          -1.07 |                 -0.12 |          -0.49 |
| opt_lev_z52     | stale63   |                 -0.29 |          -1.12 |                 -0.23 |          -1.07 |                 -0.42 |          -1.18 |
| opt_lev_z52     | stale126  |                 -0.42 |          -1.67 |                 -0.28 |          -1.11 |                 -0.23 |          -0.59 |

Reading. The final stream clears the round-3 arithmetic (standalone 2016-26 Sharpe 0.65 > 0.3, 2023-26 0.45 not negative, three-way 0.70 > 0.64
two-way), and the stale copies decay in order (0.65 -> 0.46 -> 0.35 stand-alone; 0.70 -> 0.65 -> 0.61 in the combination). But the agreement-rule
book alone also clears that arithmetic (0.51, 0.43, 0.641 > 0.636), which arm N judged to be nothing, and the step from it to this stream is a
position cut: the confirmed-only book earns +0.03 bp a day more than the agreement book (t 0.2) while being in the market 58 % instead of 73 % of
sessions. `and_rr_orth` is the same picture (-0.04 bp, t -0.2). Every other AND book earns LESS than the agreement book (-0.3 to -0.8 bp a day,
t -1.5 to -2.4): those votes remove calls that made money.
At 0.6 pips the final stream is 0.63 / 0.66 / 0.47 (turnover is tiny).

## 9 Replication of the risk-reversal rules on USD/JPY and EUR/JPY (same file, identical rules, Fed H.10 noon rates)


*2010-26* (shift = sessions the signal is made stale)

| pair       | signal          |   shift | nonoverlap 21   | nonoverlap 42   | nonoverlap 63   | weekly 21   | weekly 42   | weekly 63   |
|:-----------|:----------------|--------:|:----------------|:----------------|:----------------|:------------|:------------|:------------|
| EURJPY     | rr_d21          |       0 | 45 n=198        | 58 n=99         | 64 n=66         | 50 n=830    | 50 n=830    | 51 n=830    |
| EURJPY     | rr_d21          |      63 | 45 n=200        | 43 n=99         | 44 n=66         | 48 n=839    | 50 n=835    | 50 n=831    |
| EURJPY     | rr_fade_extreme |       0 | 64 n=36         | 66 n=29         | 74 n=23         | 53 n=57     | 47 n=57     | 46 n=57     |
| EURJPY     | rr_fade_extreme |      63 | 44 n=36         | 55 n=29         | 43 n=23         | 58 n=59     | 61 n=59     | 66 n=59     |
| EURJPY     | rr_orth         |       0 | 50 n=197        | 50 n=98         | 45 n=65         | 51 n=830    | 50 n=830    | 51 n=830    |
| EURJPY     | rr_orth         |      63 | 53 n=199        | 57 n=99         | 58 n=65         | 52 n=839    | 55 n=835    | 52 n=831    |
| EURJPY     | rr_z_follow     |       0 | 45 n=198        | 43 n=99         | 52 n=66         | 50 n=830    | 48 n=830    | 50 n=830    |
| EURJPY     | rr_z_follow     |      63 | 51 n=200        | 53 n=99         | 53 n=66         | 52 n=839    | 55 n=835    | 54 n=831    |
| EURUSD_h10 | rr_d21          |       0 | 55 n=198        | 57 n=99         | 56 n=66         | 52 n=828    | 52 n=828    | 50 n=828    |
| EURUSD_h10 | rr_d21          |      63 | 56 n=200        | 59 n=99         | 53 n=66         | 50 n=835    | 52 n=831    | 51 n=827    |
| EURUSD_h10 | rr_fade_extreme |       0 | 47 n=43         | 50 n=32         | 42 n=24         | 41 n=70     | 39 n=70     | 31 n=70     |
| EURUSD_h10 | rr_fade_extreme |      63 | 38 n=45         | 42 n=33         | 44 n=25         | 35 n=77     | 29 n=77     | 35 n=77     |
| EURUSD_h10 | rr_orth         |       0 | 54 n=197        | 60 n=98         | 48 n=65         | 55 n=830    | 55 n=830    | 53 n=830    |
| EURUSD_h10 | rr_orth         |      63 | 54 n=199        | 51 n=99         | 45 n=65         | 51 n=839    | 51 n=835    | 51 n=831    |
| EURUSD_h10 | rr_z_follow     |       0 | 59 n=197        | 55 n=99         | 50 n=66         | 54 n=830    | 53 n=830    | 53 n=830    |
| EURUSD_h10 | rr_z_follow     |      63 | 51 n=199        | 51 n=99         | 56 n=66         | 51 n=839    | 50 n=835    | 50 n=831    |
| USDJPY     | rr_d21          |       0 | 50 n=198        | 55 n=99         | 56 n=66         | 51 n=830    | 49 n=830    | 54 n=830    |
| USDJPY     | rr_d21          |      63 | 49 n=200        | 47 n=99         | 56 n=66         | 51 n=836    | 50 n=832    | 51 n=828    |
| USDJPY     | rr_fade_extreme |       0 | 46 n=48         | 50 n=34         | 46 n=28         | 43 n=60     | 53 n=60     | 48 n=60     |
| USDJPY     | rr_fade_extreme |      63 | 50 n=48         | 59 n=34         | 61 n=28         | 53 n=59     | 47 n=59     | 49 n=59     |
| USDJPY     | rr_orth         |       0 | 45 n=197        | 50 n=98         | 51 n=65         | 49 n=830    | 51 n=830    | 53 n=830    |
| USDJPY     | rr_orth         |      63 | 54 n=199        | 57 n=99         | 55 n=65         | 51 n=839    | 53 n=835    | 55 n=831    |
| USDJPY     | rr_z_follow     |       0 | 47 n=198        | 51 n=99         | 56 n=66         | 48 n=830    | 49 n=830    | 51 n=830    |
| USDJPY     | rr_z_follow     |      63 | 46 n=200        | 48 n=99         | 48 n=66         | 49 n=839    | 52 n=835    | 55 n=831    |

*2016-26* (shift = sessions the signal is made stale)

| pair       | signal          |   shift | nonoverlap 21   | nonoverlap 42   | nonoverlap 63   | weekly 21   | weekly 42   | weekly 63   |
|:-----------|:----------------|--------:|:----------------|:----------------|:----------------|:------------|:------------|:------------|
| EURJPY     | rr_d21          |       0 | 40 n=126        | 51 n=63         | 55 n=42         | 47 n=529    | 46 n=529    | 45 n=529    |
| EURJPY     | rr_d21          |      63 | 41 n=128        | 46 n=63         | 45 n=42         | 47 n=538    | 50 n=534    | 51 n=530    |
| EURJPY     | rr_fade_extreme |       0 | 75 n=24         | 60 n=20         | 69 n=16         | 57 n=30     | 63 n=30     | 67 n=30     |
| EURJPY     | rr_fade_extreme |      63 | 46 n=24         | 50 n=20         | 50 n=16         | 62 n=32     | 66 n=32     | 62 n=32     |
| EURJPY     | rr_orth         |       0 | 50 n=126        | 46 n=63         | 43 n=42         | 52 n=529    | 49 n=529    | 53 n=529    |
| EURJPY     | rr_orth         |      63 | 53 n=128        | 54 n=63         | 55 n=42         | 53 n=538    | 55 n=534    | 53 n=530    |
| EURJPY     | rr_z_follow     |       0 | 46 n=126        | 48 n=63         | 50 n=42         | 50 n=529    | 48 n=529    | 51 n=529    |
| EURJPY     | rr_z_follow     |      63 | 51 n=128        | 61 n=64         | 52 n=42         | 53 n=538    | 57 n=534    | 57 n=530    |
| EURUSD_h10 | rr_d21          |       0 | 48 n=126        | 54 n=63         | 50 n=42         | 51 n=528    | 49 n=528    | 48 n=528    |
| EURUSD_h10 | rr_d21          |      63 | 55 n=128        | 56 n=63         | 60 n=42         | 49 n=536    | 52 n=532    | 51 n=528    |
| EURUSD_h10 | rr_fade_extreme |       0 | 52 n=27         | 57 n=21         | 47 n=17         | 55 n=42     | 48 n=42     | 38 n=42     |
| EURUSD_h10 | rr_fade_extreme |      63 | 44 n=27         | 52 n=21         | 53 n=17         | 33 n=42     | 26 n=42     | 31 n=42     |
| EURUSD_h10 | rr_orth         |       0 | 52 n=126        | 62 n=63         | 52 n=42         | 55 n=529    | 56 n=529    | 53 n=529    |
| EURUSD_h10 | rr_orth         |      63 | 54 n=128        | 49 n=63         | 40 n=42         | 52 n=538    | 52 n=534    | 51 n=530    |
| EURUSD_h10 | rr_z_follow     |       0 | 56 n=126        | 56 n=63         | 48 n=42         | 54 n=529    | 54 n=529    | 53 n=529    |
| EURUSD_h10 | rr_z_follow     |      63 | 49 n=128        | 53 n=64         | 55 n=42         | 52 n=538    | 53 n=534    | 52 n=530    |
| USDJPY     | rr_d21          |       0 | 46 n=126        | 60 n=63         | 52 n=42         | 50 n=529    | 50 n=529    | 54 n=529    |
| USDJPY     | rr_d21          |      63 | 50 n=128        | 48 n=63         | 48 n=42         | 50 n=536    | 50 n=532    | 49 n=528    |
| USDJPY     | rr_fade_extreme |       0 | 48 n=27         | 53 n=19         | 71 n=17         | 54 n=35     | 57 n=35     | 57 n=35     |
| USDJPY     | rr_fade_extreme |      63 | 54 n=28         | 60 n=20         | 61 n=18         | 58 n=33     | 52 n=33     | 52 n=33     |
| USDJPY     | rr_orth         |       0 | 46 n=126        | 52 n=63         | 52 n=42         | 49 n=529    | 51 n=529    | 52 n=529    |
| USDJPY     | rr_orth         |      63 | 53 n=128        | 57 n=63         | 57 n=42         | 51 n=538    | 54 n=534    | 57 n=530    |
| USDJPY     | rr_z_follow     |       0 | 44 n=126        | 54 n=63         | 55 n=42         | 46 n=529    | 48 n=529    | 49 n=529    |
| USDJPY     | rr_z_follow     |      63 | 45 n=128        | 51 n=63         | 48 n=42         | 50 n=538    | 53 n=534    | 56 n=530    |

Reading. `EURUSD_h10` is the same rule run through this simpler H.10 pipeline, as a check on the pipeline: 54 / 53 / 53 % weekly for the skew,
55 / 55 / 53 % orthogonalised - the store-based numbers. On USD/JPY the skew followed is right 48 / 49 / 51 % (2016-26: 46 / 48 / 49 %) and on EUR/JPY
50 / 48 / 50 %; orthogonalised 49-53 %; the one-month change 49-54 %; the stale copies are as good or better. The contrarian extreme scores 43-53 % on
USD/JPY and 46-53 % on EUR/JPY weekly (57-67 % on 30 EUR/JPY decisions since 2016). So even the weak standalone 54-55 % of the EUR/USD skew is, once
more, a EUR/USD-only number. The veto of verdict 4 cannot be replicated: there is no agreement rule for the yen pairs.

## 10 Leak checks

**(1) Labels permuted** (300 draws, weekly decisions 2010-26):

| signal      | rule       |   h |   n_weekly |   real_acc |   shuffled_mean |   shuffled_p05 |   shuffled_p95 |   p_shuffled_ge_real |
|:------------|:-----------|----:|-----------:|-----------:|----------------:|---------------:|---------------:|---------------------:|
| rr_z_follow | and        |  21 |        287 |      0.624 |           0.5   |          0.446 |          0.544 |                0     |
| rr_z_follow | standalone |  21 |        861 |      0.548 |           0.498 |          0.47  |          0.525 |                0     |
| rr_orth     | and        |  21 |        248 |      0.633 |           0.5   |          0.444 |          0.552 |                0     |
| rr_orth     | standalone |  21 |        861 |      0.549 |           0.498 |          0.468 |          0.526 |                0.003 |
| rr_z_follow | and        |  42 |        287 |      0.652 |           0.504 |          0.456 |          0.554 |                0     |
| rr_z_follow | standalone |  42 |        861 |      0.538 |           0.499 |          0.474 |          0.527 |                0.01  |
| rr_orth     | and        |  42 |        248 |      0.657 |           0.499 |          0.448 |          0.552 |                0     |
| rr_orth     | standalone |  42 |        861 |      0.551 |           0.495 |          0.466 |          0.523 |                0     |
| rr_z_follow | and        |  63 |        287 |      0.669 |           0.505 |          0.456 |          0.551 |                0     |
| rr_z_follow | standalone |  63 |        861 |      0.53  |           0.496 |          0.471 |          0.52  |                0.02  |
| rr_orth     | and        |  63 |        248 |      0.669 |           0.502 |          0.452 |          0.552 |                0     |
| rr_orth     | standalone |  63 |        861 |      0.538 |           0.497 |          0.468 |          0.527 |                0.007 |

**(2) Shifted signal** (weekly decisions 2010-26, accuracy % n; +k = k sessions staler, -21 = LOOK-AHEAD of 21 sessions):

| signal          | AND live 21   | +1 21    | +5 21    | +21 21   | -21 (look-ahead) 21   |
|:----------------|:--------------|:---------|:---------|:---------|:----------------------|
| rr_fade_extreme | 50 n=6        | 50 n=6   | 50 n=6   | 80 n=5   | 14 n=7                |
| rr_z_follow     | 62 n=287      | 62 n=287 | 62 n=288 | 59 n=263 | 73 n=258              |
| rr_d21          | 63 n=227      | 62 n=228 | 63 n=226 | 60 n=204 | 75 n=179              |
| rr_spot_div     | 73 n=26       | 70 n=33  | 76 n=33  | 62 n=50  | 10 n=41               |
| rr_orth         | 63 n=248      | 63 n=256 | 63 n=256 | 61 n=252 | 64 n=239              |
| vrp_level       | 59 n=177      | 56 n=175 | 58 n=179 | 62 n=195 | 66 n=177              |
| vrp_d21         | 56 n=167      | 56 n=168 | 54 n=159 | 61 n=169 | 64 n=166              |
| agree3_vrp_gate | 58 n=165      | 58 n=166 | 62 n=173 | 61 n=158 | 61 n=163              |
| ts_slope        | 61 n=164      | 61 n=152 | 61 n=160 | 61 n=151 | 58 n=156              |
| opt_nc_z52      | 60 n=208      | 59 n=209 | 58 n=215 | 57 n=213 | 64 n=202              |
| opt_fut_div     | -             | 40 n=5   | 44 n=9   | 36 n=36  | 47 n=19               |
| opt_lev_z52     | 62 n=210      | 62 n=209 | 61 n=205 | 60 n=201 | 66 n=192              |

| signal          | standalone live 21   | +1 21    | +5 21    | +21 21   | -21 (look-ahead) 21   |
|:----------------|:---------------------|:---------|:---------|:---------|:----------------------|
| rr_fade_extreme | 44 n=72              | 47 n=74  | 45 n=73  | 44 n=78  | 21 n=71               |
| rr_z_follow     | 55 n=861             | 54 n=862 | 55 n=862 | 52 n=866 | 68 n=857              |
| rr_d21          | 53 n=859             | 52 n=854 | 52 n=860 | 52 n=858 | 66 n=856              |
| rr_spot_div     | 55 n=287             | 52 n=271 | 54 n=287 | 54 n=272 | 13 n=278              |
| rr_orth         | 55 n=861             | 55 n=862 | 54 n=862 | 53 n=866 | 56 n=857              |
| vrp_level       | 51 n=789             | 50 n=790 | 52 n=790 | 53 n=794 | 55 n=785              |
| vrp_d21         | 49 n=789             | 49 n=790 | 47 n=790 | 51 n=794 | 55 n=785              |
| ts_slope        | 51 n=631             | 51 n=631 | 50 n=632 | 51 n=635 | 51 n=627              |
| opt_nc_z52      | 50 n=870             | 50 n=870 | 49 n=870 | 47 n=870 | 55 n=870              |
| opt_fut_div     | 41 n=418             | 41 n=420 | 39 n=419 | 39 n=420 | 43 n=415              |
| opt_lev_z52     | 52 n=870             | 52 n=870 | 52 n=870 | 49 n=870 | 55 n=870              |

**Truncation test** (raw files cut at the date under the declared lags; the row of that date rebuilt and compared):

| asof       |   signals_defined |   rows_equal |   of |   max_abs_diff | mismatch   |
|:-----------|------------------:|-------------:|-----:|---------------:|:-----------|
| 2012-06-29 |                13 |           13 |   13 |              0 |            |
| 2016-11-15 |                13 |           13 |   13 |              0 |            |
| 2020-03-16 |                13 |           13 |   13 |              0 |            |
| 2022-09-30 |                12 |           13 |   13 |              0 |            |
| 2025-02-14 |                12 |           13 |   13 |              0 |            |

**(3) What the signals are** - correlation of each with the FORWARD return (2010-26, daily sessions):

| signal          | variable        |   corr_fwd21 |   corr_fwd63 |   corr_ret_21d |   corr_ret_63d |
|:----------------|:----------------|-------------:|-------------:|---------------:|---------------:|
| rr_fade_extreme | u_rr_z_neg      |       -0.117 |       -0.131 |         -0.451 |         -0.481 |
| rr_z_follow     | rr_z_follow     |        0.117 |        0.131 |          0.451 |          0.481 |
| rr_d21          | rr_d21          |        0.078 |        0.077 |          0.368 |          0.062 |
| rr_spot_div     | rr_d21          |        0.078 |        0.077 |          0.368 |          0.062 |
| rr_orth         | rr_orth         |        0.116 |        0.124 |          0.076 |          0.192 |
| vrp_level       | vrp_level       |       -0.011 |        0.009 |          0.11  |         -0.066 |
| vrp_d21         | vrp_d21         |       -0.046 |       -0.016 |          0.08  |         -0.045 |
| ts_slope        | ts_slope        |       -0.045 |        0.009 |         -0.16  |         -0.186 |
| opt_nc_z52      | opt_nc_z52      |       -0.069 |       -0.091 |         -0.017 |          0.001 |
| opt_fut_div     | u_opt_minus_fut |       -0.21  |       -0.309 |         -0.296 |         -0.485 |
| opt_lev_z52     | opt_lev_z52     |       -0.045 |        0.014 |          0.027 |          0.063 |

* (1) With permuted labels every rule sits at 50 % (the AND rules too: the agreement rule's own 59 % disappears with the labels, as it must).
* (2) One, five and 21 sessions of extra staleness change the AND rules by 0-5 points and the standalone numbers by 0-3: nothing hinges on the last
  day's quote or on the lag convention. The 21-session LOOK-AHEAD copy lifts the skew to 68 % standalone and 73 % as a vote, and the divergence vote
  falls to 13 % (a skew that will have risen against a falling spot is a spot that then rose): the pipeline does respond to future information, so its
  absence in the live numbers is real, and the skew's dependence on the move it accompanies is shown directly. The orthogonalised skew gains only
  1 point from the look-ahead (the future spot move is regressed out), VRP 4, option positioning 5.
* Truncation: with every raw file cut at five dates under the declared lags, the row of that date is identical (13 of 13 columns, max difference 0).
* (3) No signal is a label in disguise: the highest correlation with the forward 21- / 63-session return is +0.12 / +0.13 (skew), against +0.45 / +0.48
  with the PAST returns. `opt_fut_div`'s -0.21 / -0.31 is `cot_z52` entering with a minus sign.
* The gate (candidate 8) uses labels, and only labels known before the test year (log in section 6); the orthogonalisation uses no label.
* Residual look-ahead I could not remove: the copies are final vendor values (no evidence of revisions in option quotes, but unverifiable), and CFTC
  weeks published late during shutdowns carry their original report dates.


## 11 Variant count, what was added after the first run, what could not be done

* **12 candidates, declared before results** (11 distinct AND rules: `opt_fut_div`'s is empty by construction). Controls not selected from: 11
  orthogonalised copies, 6 stale / look-ahead copies of each, the fixed VRP split, the yen replication (2 pairs x 4 rules).
* Added after the first run, none affecting selection: the `agree3_no_vote` row for vote-type signals, the stale-signal books and their
  combination rows, the book-difference table.
* Not done: no independent risk-reversal source to cross-check values against (indirect checks only); no other-currency test of the extra vote
  (no agreement rule elsewhere); 3M and 1Y vols and any implied vol after 2025-03 are unavailable, so the slope has no 2022-26 record and the VRP
  none after 2025-03; butterflies, other tenors and strike-level positioning do not exist in free form.
* For the research log: options-market information (skew level, change, divergence from spot, orthogonalised skew, implied-minus-realised vol,
  vol-curve slope, CFTC options-only positioning): standalone 49-55 %, no extra vote passes the round-5 bar; the risk reversal reacts to spot
  (same-day correlation 0.45, look-ahead copy 68 %); fading an extreme skew was right 37 %; one unadjusted lead (skew contradicts a 21-session
  agreement call: 49.5 %, n=95) that fails on non-overlapping decisions and cannot run without a live feed.

## Sources

* Risk reversal copy: https://raw.githubusercontent.com/GerardWu100/geographic-equity-rotation/main/data/RiskReversalData_Clean.csv
* ATM vol copy: https://raw.githubusercontent.com/frederikbachdk/FXVolTrading/master/data/EURUSD.csv ; EVZ: https://fred.stlouisfed.org/graph/fredgraph.csv?id=EVZCLS
* CFTC combined history: https://www.cftc.gov/files/dea/history/ (deahistfo_1995_2016.zip, deahistfo2017..2026.zip, fin_com_txt_2006_2016.zip, com_fin_txt_2017..2026.zip)
* Della Corte, Ramadorai & Sarno (2016): https://econpapers.repec.org/RePEc:eee:jfinec:v:120:y:2016:i:1:p:21-40 ; https://openaccess.city.ac.uk/id/eprint/13156/
* Londono & Zhou (2017): https://econpapers.repec.org/RePEc:eee:jfinec:v:124:y:2017:i:2:p:415-440
* Ornelas & Mauad (2019): https://econpapers.repec.org/RePEc:eee:intfor:v:35:y:2019:i:4:p:1800-1813 ; https://ideas.repec.org/p/bcb/wpaper/492.html
* Farhi, Fraiberger, Gabaix, Ranciere & Verdelhan: https://www.nber.org/system/files/working_papers/w15062/w15062.pdf
* Brunnermeier, Nagel & Pedersen (2008), "Carry Trades and Currency Crashes", NBER Macroeconomics Annual 23 (cited from memory; not fetched).

