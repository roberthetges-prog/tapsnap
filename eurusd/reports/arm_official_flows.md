# Arm Y: actual cross-border flows as an extra vote (`official_flows`)

Code `src/eurusd/arms/official_flows.py` (`run(cost_pips=1.2)`, `fetch_data()` cached, `leak_checks()`, `incremental()`; `python -m eurusd.arms.official_flows` reproduces everything in a few minutes). Results in `experiments/results/arms/`: `official_flows_positions.parquet` (daily weekly-tranche book of the final extra-vote rule: `pos`, `fwd_bp`, `net_bp`), `official_flows_decisions.parquet`, `official_flows_report.csv` (protocol table of all 12 extra-vote books, the agreement-rule baseline and the 0.6-pip run; `variant`, `final`), `official_flows_votes.csv` (agreement rule, extra vote, calls outside agreement, placebos, paired differences), `official_flows_standalone.csv`, `official_flows_orthogonalised.csv` (+ `_slopes`), `official_flows_correlations.csv`, `official_flows_lead_lag.csv`, `official_flows_vintage_check.csv`, `official_flows_replication.csv`, `official_flows_reconciliation.csv`, `official_flows_selection.csv`, `official_flows_bar.csv`, `official_flows_bar_all.csv`, `official_flows_incremental.csv`, `official_flows_leakchecks.csv`. Aligned panel: `data/processed/cross/official_flows_panel.parquet`.

Data, lags, sign priors, the 12 candidates, the controls, the selection rule and the reading of the success bar are in the module docstring and were written before the first result. One thing was added afterwards and is marked as such: the zero-publication-lag control (section 5e). It is not a candidate and changes no selection.

## Verdict (run of 2026-11-11; every number below is regenerated in the tables that follow)
**The round-5 success bar is NOT met, by any of the 12 candidates. Cross-border flow data - official custody holdings, the
foreign repo pool, swap lines, euro-area portfolio and basic-balance flows, US TIC flows - and the survey consensus carry no
usable information about EUR/USD direction at 1-3 months, on their own or as an extra vote. Where a flow is related to the
exchange rate at all, it FOLLOWS it.**

1. **What was obtainable.** Everything in the brief, from official hosts. Fed H.4.1 memo items from FRED (custody is zero on
   FRED before 2007-07-04, so custody signals start in 2009 after the 2-year norm window; repo pool and swap lines from
   2002-12). ECB balance of payments, all asset / liability / equity / debt / direct-investment / current-account keys for the
   current area I10, 1999-04 to 2026-08, plus two frozen vintages (I9, I8) used to size revisions. TIC: the Treasury host is
   blocked, but FRED carries the monthly TIC net-transactions series (1985-01 to 2026-08), so TIC was included. ECB SPF USD/EUR
   assumptions, 100 survey rounds 2002Q1-2026Q4, mapped from target quarter back to survey round.
2. **Reconciliation: exact.** The agreement rule rebuilt here matches `selective_accuracy_coverage.csv` in all 32 cells
   (non-overlapping 56 / 59 / 61 / 72 % at 10 / 21 / 42 / 63 sessions, n = 291 / 156 / 89 / 61, 2010-26).
3. **Standalone: a coin.** Over 2010-26 the twelve votes are right 45-51 % of the time at 21 sessions, 40-55 % at 42 and 42-57 %
   at 63 on non-overlapping decisions (n = 208 / 104 / 69 for the eleven always-on votes; `swap_use` 47 / 49 / 55 % on 64 / 41 /
   33), and 46-52 / 44-52 / 42-52 % on weekly decisions. No 95 % interval excludes 50 % on the right side. The best cells belong to
   the slowest vote, `basic_12m`: 55 / 57 % at 42 / 63 sessions (59 / 66 % since 2016), weekly 51 / 50 %, and its 63- and
   126-session-stale versions score the same 53-54 / 57 % - a regime bet (the basic balance changed sign 0.8 times a year), not
   information. The one interval on the WRONG side is `cust_d4w` at 42 sessions, 40 % [31-50] (weekly 52 %).
   * (a) Custody: primary sign 51 / 40 / 42 % (4 weeks) and 48 / 43 / 43 % (13 weeks); the labelled alternative reading
     ("accumulation follows dollar weakness") is the mirror, 49 / 60 / 58 % and 52 / 57 / 57 %, not confirmed on weekly decisions
     (48 / 48 / 52 %). Neither reading is a signal.
   * (b) Funding stress: `swap_use` speaks on 24 % of sessions (mostly 2010-13 and 2020-21) and is right 47 / 49 / 55 %; the foreign repo
     pool 45 / 54 / 52 %.
   * (c) Euro-area portfolio flows: net 49 / 51 / 45 % (3 months) and 46 / 51 / 51 % (6 months), change 51 / 48 / 45 %, equity
     45 / 46 / 45 %, debt 50 / 52 / 49 %. "Net inflows => euro up" is not visible at any horizon.
   * (TIC) 51 / 44 / 48 %. (e) SPF consensus, contrarian: 47 / 52 / 43 %.
4. **Lead or follow (section 5): they follow, or do nothing.** At the native frequency and without publication lags, custody
   holdings rise in the four weeks AFTER and during a rise of EUR/USD (correlation +0.21 with the previous four weeks' return,
   +0.14 with the same four weeks, n = 252) and are unrelated to the next three periods (+0.02 / -0.02 / +0.04): reserve managers
   lean against dollar weakness, the alternative reading, and it leads nothing. TIC foreign purchases of US securities likewise
   follow a fall of the dollar (+0.15 / +0.10 / +0.11 with the three previous months, n = 283) and do not lead (0.00 / -0.08 /
   0.00). Euro-area net portfolio inflows are slightly NEGATIVELY related to the previous and the same month's return (-0.14 /
   -0.09) and unrelated to later months (+0.07 / +0.05 / -0.01). Swap-line use rises while the euro is falling (-0.13 for the
   same and the two previous periods, -0.17 for the next one; almost all of it is 2008-09 - in 2010-26 it is -0.12 for the same
   period and -0.07 for the next, and the vote is a coin).  The custody pattern holds in both halves (2010-26: +0.20 / +0.15). In the session
   panel the oriented custody signals correlate -0.25 / -0.31 with the trailing 63-session return and at most -0.10 with the
   forward return; R-squared on trailing spot returns is at most 0.10 and on spot plus the three agreement inputs at most 0.12
   (0.25 for `swap_use`). **Orthogonalising changes nothing: 44-53 / 45-57 / 41-55 % after removing the trailing 21- and
   63-session returns, 45-53 / 44-56 / 44-57 % after removing those and the agreement inputs.** So the flows are mostly NOT a
   restatement of the price move - they are independent of the old signals and simply uninformative about the next 1-3 months.
   A zero-publication-lag control (added after the first run, not tradable) gives 42-56 % for the monthly flows: the 7-week
   publication lag is not what kills them.
5. **SPF consensus (the 'is the consensus contrarian?' control): no.** The consensus expected change is negatively related
   to the previous quarters' return (forecasters expect partial mean reversion) and POSITIVELY related to the return of the
   survey quarter and the next three (+0.21 / +0.24 / +0.16 / +0.15, n = 95, about two standard errors each); in 2010-26 it
   correlates +0.13 / +0.21 with the forward 21- / 63-session return. So the contrarian prior is rejected; if anything the
   consensus is weakly right in SIZE. As a sign vote it is nothing either way (following it: 53 / 48 / 57 %, intervals include
   50 %, weekly 52 / 49 / 50 %), it changes sign 0.65 times a year, and its stale versions score the same. Not proposed.
6. **Extra vote: lower accuracy on a smaller sample.** Final by the declared rule = `pf_net_d3m` (2010-15: 52 % [38-66], n=44,
   7.3 a year, against 62 % for the agreement rule alone; only three candidates reach 6 decisions a year in the selection
   window and none of the three beats the agreement rule there). Agreement rule AND the vote, non-overlapping: **55 % (n=95, 5.7 a year)
   against 59 % (n=156, 9.3 a year) at 21 sessions; 57 % (n=61, 3.7 a year) against 61 % (n=89) at 42; 65 % (n=48) against 72 %
   (n=61) at 63.** Since 2016: 57 against 57 % and 53 against 59 %. Since 2023: 50 against 60 % (n=20 v 35) and 50 against 45 %
   (n=12 v 20). Gain -4.2 / -3.3 points (2010-26) and -0.4 / -6.0 (2016-26) where +3 / +3 is required; 5.7 decisions a year where
   6 are required; worse in 2023-26 at 21 sessions. Paired difference on the weekly grid: +0.4 points [-5.8, +6.4] at 21
   sessions, -5.0 [-12.1, +1.3] at 42; on the agreement rule's own stream the decisions the vote confirms are right 59 / 55 %
   and the ones it rejects 59 / 68 %.
   Across all 12 candidates the 21-session gain in 2010-26 is negative for every one (-10.2 to -0.3 points). Positive
   42-session gains (`swap_use` +12.1 on 22 decisions, 1.3 a year; `spf_contra` +8.1; custody and repo pool +3.9 to +4.0) come
   with a negative 21-session gain, and no candidate has more than 6.3 decisions a year. None passes; the orthogonalised votes do
   not pass either.
7. **Coverage extension: no.** Where the three old signals do not agree the votes are right 47-55 % at 21 sessions, 43-53 %
   at 42 and 31-59 % at 63 (2010-26, n = 170 / 93 / 64); every interval includes 50 % except `cust_d4w` at 63 sessions on the
   wrong side.
8. **Timing placebo: nothing to lose.** For the final the 63- and 126-session-stale votes give -6.0 / -4.2 and -7.4 / -4.2 points
   against -4.2 / -3.3 live. Among the standalone votes the stale versions score as high as the live ones (36-65 % against
   40-57 %).
9. **Daily incremental test: worse.** The final rule's weekly-tranche book has net Sharpe 0.45 / 0.26 / -0.22 (2010-26 /
   2016-26 / 2023-26, 1.2 pips) against 0.52 / 0.51 / 0.43 for the agreement rule's own book and is 0.77 correlated with it
   (0.30 with `weak_signals`, 0.46 with `regime_trend`). EW(weak_signals, regime_trend, this arm) = 0.562 / 0.589 / 0.209
   against 0.563 / 0.636 / 0.356 two-way. Round-3 bar failed as well (standalone 2016-26 below 0.3, 2023-26 negative,
   three-way below two-way).
10. **Replication (dollar-side votes on eight non-euro currencies against the dollar): nothing.** 41-54 / 38-56 / 41-55 % at
    21 / 42 / 63 sessions (2010-26). `tic_net_3m` is on the wrong side there (45 / 38 [30-48] / 41 %; weekly 48 / 45 / 47 %):
    one cell in ninety, and turning the sign round would be a post-hoc choice; not proposed.
11. **Revision risk.** The balance-of-payments results use the current vintage. Against the two frozen vintages the votes differ
    on 1-4 % of months (I9, 2013-25) and 5-14 % (I8, 2010-22), and on up to 25 % of the LAST twelve months of a frozen vintage:
    the most recent year is revised by about a third of a standard deviation of the monthly flow (RMS 20-23 against 57 EUR bn).
    A real-time version could only be noisier than what is tested here, and what is tested here shows nothing.
12. **What to keep.** Nothing for the product. The files are clean, lagged and cached; custody holdings, the repo pool, swap
    lines and the SPF consensus path can serve as context panels in the brief (who is accumulating dollars, what the consensus
    expects), never as votes.

## 1. New data: keys, span, publication lag used, revisions

| file                                              | source                                                                                                                                        | first      | last       |   rows | publication                                                         | lag_used                             | fetched    |
|:--------------------------------------------------|:----------------------------------------------------------------------------------------------------------------------------------------------|:-----------|:-----------|-------:|:--------------------------------------------------------------------|:-------------------------------------|:-----------|
| data/macro/official_flows_fed_h41_memo_weekly.csv | FRED WSEFINTL1, WMTSECL1, WLRRAFOIAL, SWPT (curl --http1.1); custody zero before 2007-07-04 set to missing                                    | 2007-07-04 | 2026-11-04 |   1010 | Wednesday level, released Thursday 16:30 ET                         | 7 calendar days                      | 2026-11-11 |
| data/macro/official_flows_ecb_bop_monthly.csv     | ECB Data Portal BPS.M.N.I10.W1.S1.S1.T.{A,L,N}.FA.{P,D}.{F,F5,F3}... + B.CA (11 keys, EUR mn, NSA), CURRENT VINTAGE                           | 1999-04-30 | 2026-08-31 |    329 | month m released ~20th of m+2                                       | 60 calendar days after month-end     | 2026-11-11 |
| data/macro/official_flows_ecb_bop_vintage_i9.csv  | ECB Data Portal BPS.M.N.I9.W1.S1.S1.T.{A,L,N}.FA.{P,D}.{F,F5,F3}... + B.CA (11 keys, EUR mn, NSA), frozen after 2025-12 (revision check only) | 2013-01-31 | 2025-12-31 |    156 | -                                                                   | not used in signals                  | 2026-11-11 |
| data/macro/official_flows_ecb_bop_vintage_i8.csv  | ECB Data Portal BP6.M.N.I8.W1.S1.S1.T.{A,L,N}.FA.{P,D}.{F,F5,F3}... + B.CA (11 keys, EUR mn, NSA), frozen after 2022-12 (revision check only) | 1999-01-31 | 2022-12-31 |    288 | -                                                                   | not used in signals                  | 2026-11-11 |
| data/macro/official_flows_us_tic_monthly.csv      | FRED FORLTTOTALNET69995, FORLTTOTALNET99990, FORLTTREASNET69995, FORLTTREASNET99990 (TIC; ticdata.treasury.gov blocked)                       | 1985-01-31 | 2026-08-31 |    500 | month m released ~17th of m+2                                       | 56 calendar days after month-end     | 2026-11-11 |
| data/macro/official_flows_ecb_spf_usd.csv         | ECB Data Portal SPF.Q.U2.ASSU.USD.{P3M,P6M,P9M,P12M}.Q.AVG, target quarters mapped back to survey rounds                                      | 2002-01-01 | 2026-10-01 |    100 | survey in the first weeks of the quarter, published within ~6 weeks | 50 calendar days after quarter start | 2026-11-11 |

Lag audit (age in calendar days, at each session's closing date, of the observation actually used; sessions 2010-26). Alignment is `featstore._align_lagged(series, closing_date, lag)`: last observation stamped <= closing date - lag.

| signal     |   lag_required_days |   min_age_days |   median_age_days |   max_age_days | first_session_with_value   | ok   |
|:-----------|--------------------:|---------------:|------------------:|---------------:|:---------------------------|:-----|
| cust_d4w   |                   7 |              7 |                 9 |             13 | 2009-07-28                 | True |
| cust_d13w  |                   7 |              7 |                 9 |             13 | 2009-09-29                 | True |
| swap_use   |                   7 |              7 |                 9 |             13 | 2003-01-21                 | True |
| repo_d13w  |                   7 |              7 |                 9 |             13 | 2005-03-15                 | True |
| pf_net_3m  |                  60 |             60 |                75 |             90 | 2003-01-01                 | True |
| pf_net_6m  |                  60 |             60 |                75 |             90 | 2003-01-01                 | True |
| pf_net_d3m |                  60 |             60 |                75 |             90 | 2003-01-01                 | True |
| pf_eq_3m   |                  60 |             60 |                75 |             90 | 2003-01-01                 | True |
| pf_debt_3m |                  60 |             60 |                75 |             90 | 2003-01-01                 | True |
| basic_12m  |                  60 |             60 |                75 |             90 | 2003-01-01                 | True |
| tic_net_3m |                  56 |             56 |                71 |             86 | 2003-01-01                 | True |
| spf_contra |                  50 |             50 |                96 |            141 | 2003-01-01                 | True |

Revision risk of the balance-of-payments signals: the six signals rebuilt from the two frozen vintages the ECB still serves (I9 = euro area 20, last updated for 2025-12; I8 = euro area 19, flow BP6, last updated for 2022-12) against the current I10 vintage. The differences mix genuine revisions with the change of composition (Croatia, Bulgaria). `rms_diff` = root-mean-square difference of the MONTHLY net portfolio flow (EUR bn; its standard deviation is in `sd_monthly_net_pf_bn`); `vote_differs` = share of months (from 2010) on which the vote has the other sign.

| vintage    | span                     |   months_compared |   sd_monthly_net_pf_bn |   rms_diff_all_bn |   rms_diff_last12_bn |   corr_monthly |   corr_last12 | signal     |   months |   vote_differs_share |   vote_differs_last12 |   corr_signal |
|:-----------|:-------------------------|------------------:|-----------------------:|------------------:|---------------------:|---------------:|--------------:|:-----------|---------:|---------------------:|----------------------:|--------------:|
| vintage_i9 | 2013-01-31 .. 2025-12-31 |               156 |                 57.083 |             7.922 |               20.358 |          0.99  |         0.863 | pf_net_3m  |      131 |                0.023 |                 0.083 |         0.987 |
| vintage_i9 | 2013-01-31 .. 2025-12-31 |               156 |                 57.083 |             7.922 |               20.358 |          0.99  |         0.863 | pf_net_6m  |      128 |                0.016 |                 0.167 |         0.988 |
| vintage_i9 | 2013-01-31 .. 2025-12-31 |               156 |                 57.083 |             7.922 |               20.358 |          0.99  |         0.863 | pf_net_d3m |      151 |                0.02  |                 0.25  |         0.994 |
| vintage_i9 | 2013-01-31 .. 2025-12-31 |               156 |                 57.083 |             7.922 |               20.358 |          0.99  |         0.863 | pf_eq_3m   |      131 |                0.031 |                 0.083 |         0.971 |
| vintage_i9 | 2013-01-31 .. 2025-12-31 |               156 |                 57.083 |             7.922 |               20.358 |          0.99  |         0.863 | pf_debt_3m |      131 |                0.038 |                 0.167 |         0.986 |
| vintage_i9 | 2013-01-31 .. 2025-12-31 |               156 |                 57.083 |             7.922 |               20.358 |          0.99  |         0.863 | basic_12m  |      145 |                0.007 |                 0     |         0.996 |
| vintage_i8 | 1999-01-31 .. 2022-12-31 |               180 |                 55.157 |            15.838 |               23.111 |          0.959 |         0.947 | pf_net_3m  |      156 |                0.09  |                 0     |         0.966 |
| vintage_i8 | 1999-01-31 .. 2022-12-31 |               180 |                 55.157 |            15.838 |               23.111 |          0.959 |         0.947 | pf_net_6m  |      156 |                0.083 |                 0.083 |         0.981 |
| vintage_i8 | 1999-01-31 .. 2022-12-31 |               180 |                 55.157 |            15.838 |               23.111 |          0.959 |         0.947 | pf_net_d3m |      156 |                0.071 |                 0.083 |         0.967 |
| vintage_i8 | 1999-01-31 .. 2022-12-31 |               180 |                 55.157 |            15.838 |               23.111 |          0.959 |         0.947 | pf_eq_3m   |      156 |                0.135 |                 0     |         0.937 |
| vintage_i8 | 1999-01-31 .. 2022-12-31 |               180 |                 55.157 |            15.838 |               23.111 |          0.959 |         0.947 | pf_debt_3m |      156 |                0.051 |                 0     |         0.985 |
| vintage_i8 | 1999-01-31 .. 2022-12-31 |               180 |                 55.157 |            15.838 |               23.111 |          0.959 |         0.947 | basic_12m  |      156 |                0.071 |                 0.167 |         0.986 |

## 2. The 12 candidate votes and their priors (fixed before results)

Vote = sign of the oriented signal: +1 long EUR/USD, -1 short, 0 silent. z = against the trailing 3-year mean and standard deviation of the same quantity (156 weeks / 36 months).

| vote       | family   | prior sign     | raw quantity                                                                              | data       | lag                      |
|:-----------|:---------|:---------------|:------------------------------------------------------------------------------------------|:-----------|:-------------------------|
| cust_d4w   | a        | -              | z of the 4-week change of log custody holdings (WSEFINTL1)                                | FRED H.4.1 | 7 d                      |
| cust_d13w  | a        | -              | z of the 13-week change of log custody holdings                                           | FRED H.4.1 | 7 d                      |
| swap_use   | b        | -              | 4-week change of swap lines outstanding (SWPT) while SWPT >= USD 1 bn; silent otherwise   | FRED H.4.1 | 7 d                      |
| repo_d13w  | b        | -              | z of the 13-week change of log foreign repo pool (WLRRAFOIAL)                             | FRED H.4.1 | 7 d                      |
| pf_net_3m  | c        | +              | z of the 3-month sum of euro-area net portfolio inflows (liabilities - assets)            | ECB BPS    | 60 d after month-end     |
| pf_net_6m  | c        | +              | z of the 6-month sum                                                                      | ECB BPS    | 60 d                     |
| pf_net_d3m | c        | +              | 3-month sum minus the previous 3-month sum                                                | ECB BPS    | 60 d                     |
| pf_eq_3m   | c        | +              | z of the 3-month sum of net equity inflows                                                | ECB BPS    | 60 d                     |
| pf_debt_3m | c        | +              | z of the 3-month sum of net debt inflows                                                  | ECB BPS    | 60 d                     |
| basic_12m  | d        | +              | 12-month sum of current account + net direct + net portfolio inflows (level against zero) | ECB BPS    | 60 d                     |
| tic_net_3m | TIC      | -              | z of the 3-month sum of foreign net purchases of US long-term securities                  | FRED (TIC) | 56 d after month-end     |
| spf_contra | e        | - (contrarian) | log(P12M / P3M): the SPF consensus' expected 9-month change of USD per EUR                | ECB SPF    | 50 d after quarter start |

Custody (a): the primary sign is 'accumulation = official dollar buying = EUR/USD down'. The labelled alternative ('accumulation follows dollar weakness, managers lean against it') is the mirror image: its accuracy is 100 minus the primary's.


## 3. Reconciliation of the agreement rule

Rebuilt with the selective helpers (through `liquidity_stress.agreement / rule_rows`). Cells compared with `selective_accuracy_coverage.csv`: 32; exact matches (n and accuracy): 32.

|   h | mode       | period   | here       | selective   | match   |
|----:|:-----------|:---------|:-----------|:------------|:--------|
|  10 | weekly     | 2010-26  | 57.2 n=390 | 57.2 n=390  | True    |
|  10 | weekly     | 2016-26  | 54.9 n=246 | 54.9 n=246  | True    |
|  10 | weekly     | 2023-26  | 57.5 n=80  | 57.5 n=80   | True    |
|  10 | nonoverlap | 2010-26  | 56.0 n=291 | 56.0 n=291  | True    |
|  10 | nonoverlap | 2016-26  | 53.4 n=178 | 53.4 n=178  | True    |
|  10 | nonoverlap | 2023-26  | 54.0 n=63  | 54.0 n=63   | True    |
|  21 | weekly     | 2010-26  | 59.4 n=387 | 59.4 n=387  | True    |
|  21 | weekly     | 2016-26  | 57.2 n=243 | 57.2 n=243  | True    |
|  21 | weekly     | 2023-26  | 54.5 n=77  | 54.5 n=77   | True    |
|  21 | nonoverlap | 2010-26  | 59.0 n=156 | 59.0 n=156  | True    |
|  21 | nonoverlap | 2016-26  | 57.3 n=96  | 57.3 n=96   | True    |
|  21 | nonoverlap | 2023-26  | 60.0 n=35  | 60.0 n=35   | True    |
|  42 | weekly     | 2010-26  | 64.8 n=383 | 64.8 n=383  | True    |
|  42 | weekly     | 2016-26  | 63.2 n=239 | 63.2 n=239  | True    |
|  42 | weekly     | 2023-26  | 46.6 n=73  | 46.6 n=73   | True    |
|  42 | nonoverlap | 2010-26  | 60.7 n=89  | 60.7 n=89   | True    |
|  42 | nonoverlap | 2016-26  | 58.9 n=56  | 58.9 n=56   | True    |
|  42 | nonoverlap | 2023-26  | 45.0 n=20  | 45.0 n=20   | True    |
|  63 | weekly     | 2010-26  | 66.6 n=383 | 66.6 n=383  | True    |
|  63 | weekly     | 2016-26  | 66.9 n=239 | 66.9 n=239  | True    |
|  63 | weekly     | 2023-26  | 53.4 n=73  | 53.4 n=73   | True    |
|  63 | nonoverlap | 2010-26  | 72.1 n=61  | 72.1 n=61   | True    |
|  63 | nonoverlap | 2016-26  | 71.1 n=38  | 71.1 n=38   | True    |
|  63 | nonoverlap | 2023-26  | 50.0 n=14  | 50.0 n=14   | True    |

## 4. Standalone accuracy of each vote (direction = the vote; % right, 95 % Wilson interval, decisions, decisions per year)


Non-overlapping decisions, 2010-26:

| candidate   | 2010-26 / 21s             | 2010-26 / 42s            | 2010-26 / 63s           |
|:------------|:--------------------------|:-------------------------|:------------------------|
| cust_d4w    | 51 [44-58] n=208 (12.4/y) | 40 [31-50] n=104 (6.2/y) | 42 [31-54] n=69 (4.2/y) |
| cust_d13w   | 48 [41-54] n=208 (12.4/y) | 43 [34-53] n=104 (6.2/y) | 43 [32-55] n=69 (4.2/y) |
| swap_use    | 47 [35-59] n=64 (3.8/y)   | 49 [34-64] n=41 (2.5/y)  | 55 [38-70] n=33 (2.0/y) |
| repo_d13w   | 45 [39-52] n=208 (12.4/y) | 54 [44-63] n=104 (6.2/y) | 52 [41-64] n=69 (4.2/y) |
| pf_net_3m   | 49 [42-55] n=208 (12.4/y) | 51 [41-60] n=104 (6.2/y) | 45 [34-57] n=69 (4.2/y) |
| pf_net_6m   | 46 [39-52] n=208 (12.4/y) | 51 [41-60] n=104 (6.2/y) | 51 [39-62] n=69 (4.2/y) |
| pf_net_d3m  | 51 [44-58] n=208 (12.4/y) | 48 [39-58] n=104 (6.2/y) | 45 [34-57] n=69 (4.2/y) |
| pf_eq_3m    | 45 [39-52] n=208 (12.4/y) | 46 [37-56] n=104 (6.2/y) | 45 [34-57] n=69 (4.2/y) |
| pf_debt_3m  | 50 [43-57] n=208 (12.4/y) | 52 [42-61] n=104 (6.2/y) | 49 [38-61] n=69 (4.2/y) |
| basic_12m   | 47 [40-53] n=208 (12.4/y) | 55 [45-64] n=104 (6.2/y) | 57 [45-68] n=69 (4.2/y) |
| tic_net_3m  | 51 [44-58] n=208 (12.4/y) | 44 [35-54] n=104 (6.2/y) | 48 [36-59] n=69 (4.2/y) |
| spf_contra  | 47 [40-53] n=208 (12.4/y) | 52 [42-61] n=104 (6.2/y) | 43 [32-55] n=69 (4.2/y) |

Non-overlapping decisions, 2016-26:

| candidate   | 2016-26 / 21s             | 2016-26 / 42s           | 2016-26 / 63s           |
|:------------|:--------------------------|:------------------------|:------------------------|
| cust_d4w    | 50 [42-59] n=133 (12.4/y) | 42 [31-54] n=66 (6.2/y) | 41 [28-56] n=44 (4.2/y) |
| cust_d13w   | 50 [41-58] n=133 (12.4/y) | 50 [38-62] n=66 (6.2/y) | 43 [30-58] n=44 (4.2/y) |
| swap_use    | 50 [34-66] n=34 (3.2/y)   | 48 [30-67] n=25 (2.3/y) | 67 [45-83] n=21 (2.0/y) |
| repo_d13w   | 44 [36-53] n=133 (12.4/y) | 58 [46-69] n=66 (6.2/y) | 55 [40-68] n=44 (4.2/y) |
| pf_net_3m   | 47 [39-56] n=133 (12.4/y) | 48 [37-60] n=66 (6.2/y) | 45 [32-60] n=44 (4.2/y) |
| pf_net_6m   | 44 [35-52] n=133 (12.4/y) | 50 [38-62] n=66 (6.2/y) | 50 [36-64] n=44 (4.2/y) |
| pf_net_d3m  | 50 [41-58] n=133 (12.4/y) | 39 [29-51] n=66 (6.2/y) | 41 [28-56] n=44 (4.2/y) |
| pf_eq_3m    | 49 [41-57] n=133 (12.4/y) | 50 [38-62] n=66 (6.2/y) | 50 [36-64] n=44 (4.2/y) |
| pf_debt_3m  | 47 [38-55] n=133 (12.4/y) | 47 [35-59] n=66 (6.2/y) | 43 [30-58] n=44 (4.2/y) |
| basic_12m   | 50 [42-59] n=133 (12.4/y) | 59 [47-70] n=66 (6.2/y) | 66 [51-78] n=44 (4.2/y) |
| tic_net_3m  | 50 [41-58] n=133 (12.4/y) | 42 [31-54] n=66 (6.2/y) | 45 [32-60] n=44 (4.2/y) |
| spf_contra  | 53 [44-61] n=133 (12.4/y) | 58 [46-69] n=66 (6.2/y) | 45 [32-60] n=44 (4.2/y) |

Non-overlapping decisions, 2023-26:

| candidate   | 2023-26 / 21s            | 2023-26 / 42s           | 2023-26 / 63s           |
|:------------|:-------------------------|:------------------------|:------------------------|
| cust_d4w    | 60 [45-72] n=47 (12.5/y) | 52 [33-71] n=23 (6.2/y) | 40 [20-64] n=15 (4.2/y) |
| cust_d13w   | 57 [43-70] n=47 (12.5/y) | 48 [29-67] n=23 (6.2/y) | 60 [36-80] n=15 (4.2/y) |
| swap_use    | 50 [9-91] n=2 (0.5/y)    | 50 [9-91] n=2 (0.5/y)   | 50 [9-91] n=2 (0.6/y)   |
| repo_d13w   | 43 [30-57] n=47 (12.5/y) | 57 [37-74] n=23 (6.2/y) | 53 [30-75] n=15 (4.2/y) |
| pf_net_3m   | 43 [30-57] n=47 (12.5/y) | 52 [33-71] n=23 (6.2/y) | 47 [25-70] n=15 (4.2/y) |
| pf_net_6m   | 38 [26-53] n=47 (12.5/y) | 43 [26-63] n=23 (6.2/y) | 40 [20-64] n=15 (4.2/y) |
| pf_net_d3m  | 57 [43-70] n=47 (12.5/y) | 52 [33-71] n=23 (6.2/y) | 33 [15-58] n=15 (4.2/y) |
| pf_eq_3m    | 55 [41-69] n=47 (12.5/y) | 52 [33-71] n=23 (6.2/y) | 60 [36-80] n=15 (4.2/y) |
| pf_debt_3m  | 38 [26-53] n=47 (12.5/y) | 39 [22-59] n=23 (6.2/y) | 40 [20-64] n=15 (4.2/y) |
| basic_12m   | 49 [35-63] n=47 (12.5/y) | 52 [33-71] n=23 (6.2/y) | 73 [48-89] n=15 (4.2/y) |
| tic_net_3m  | 47 [33-61] n=47 (12.5/y) | 35 [19-55] n=23 (6.2/y) | 47 [25-70] n=15 (4.2/y) |
| spf_contra  | 53 [39-67] n=47 (12.5/y) | 57 [37-74] n=23 (6.2/y) | 40 [20-64] n=15 (4.2/y) |

Weekly decisions (overlapping holds; no interval shown - the effective sample is the non-overlapping count above):

| candidate   | 2010-26 / 21s   | 2010-26 / 42s   | 2010-26 / 63s   | 2016-26 / 21s   | 2016-26 / 42s   | 2016-26 / 63s   | 2023-26 / 21s   | 2023-26 / 42s   | 2023-26 / 63s   |
|:------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|
| cust_d4w    | 52 n=870        | 52 n=866        | 48 n=862        | 50 n=559        | 50 n=555        | 47 n=551        | 54 n=195        | 58 n=191        | 56 n=187        |
| cust_d13w   | 51 n=870        | 51 n=866        | 45 n=862        | 51 n=559        | 51 n=555        | 44 n=551        | 58 n=195        | 57 n=191        | 50 n=187        |
| swap_use    | 48 n=208        | 46 n=208        | 50 n=208        | 49 n=95         | 49 n=95         | 58 n=95         | 40 n=5          | 40 n=5          | 40 n=5          |
| repo_d13w   | 48 n=870        | 50 n=866        | 52 n=862        | 50 n=559        | 51 n=555        | 54 n=551        | 53 n=195        | 54 n=191        | 57 n=187        |
| pf_net_3m   | 47 n=870        | 47 n=866        | 45 n=862        | 48 n=559        | 46 n=555        | 42 n=551        | 44 n=195        | 41 n=191        | 37 n=187        |
| pf_net_6m   | 47 n=870        | 47 n=866        | 48 n=862        | 48 n=559        | 47 n=555        | 50 n=551        | 43 n=195        | 43 n=191        | 49 n=187        |
| pf_net_d3m  | 49 n=870        | 47 n=866        | 46 n=862        | 47 n=559        | 42 n=555        | 40 n=551        | 44 n=195        | 41 n=191        | 34 n=187        |
| pf_eq_3m    | 46 n=870        | 44 n=866        | 42 n=862        | 47 n=559        | 47 n=555        | 46 n=551        | 46 n=195        | 50 n=191        | 56 n=187        |
| pf_debt_3m  | 48 n=870        | 50 n=866        | 50 n=862        | 48 n=559        | 48 n=555        | 49 n=551        | 42 n=195        | 39 n=191        | 35 n=187        |
| basic_12m   | 47 n=870        | 51 n=866        | 50 n=862        | 50 n=559        | 54 n=555        | 54 n=551        | 51 n=195        | 55 n=191        | 51 n=187        |
| tic_net_3m  | 50 n=870        | 50 n=866        | 51 n=862        | 49 n=559        | 48 n=555        | 53 n=551        | 44 n=195        | 45 n=191        | 54 n=187        |
| spf_contra  | 48 n=870        | 51 n=866        | 50 n=862        | 51 n=559        | 56 n=555        | 56 n=551        | 52 n=195        | 54 n=191        | 53 n=187        |

Timing placebo of the standalone votes, non-overlapping, 2010-26 (the vote made 63 / 126 sessions staler):

| candidate   | 21s live   | 21s placebo+63   | 21s placebo+126   | 42s live   | 42s placebo+63   | 42s placebo+126   | 63s live   | 63s placebo+63   | 63s placebo+126   |
|:------------|:-----------|:-----------------|:------------------|:-----------|:-----------------|:------------------|:-----------|:-----------------|:------------------|
| cust_d4w    | 51 n=208   | 45 n=208         | 55 n=207          | 40 n=104   | 38 n=104         | 55 n=103          | 42 n=69    | 36 n=69          | 54 n=69           |
| cust_d13w   | 48 n=208   | 41 n=208         | 54 n=205          | 43 n=104   | 43 n=104         | 48 n=102          | 43 n=69    | 43 n=69          | 46 n=68           |
| swap_use    | 47 n=64    | 51 n=67          | 44 n=70           | 49 n=41    | 49 n=43          | 52 n=44           | 55 n=33    | 38 n=34          | 51 n=35           |
| repo_d13w   | 45 n=208   | 51 n=208         | 53 n=208          | 54 n=104   | 46 n=104         | 56 n=104          | 52 n=69    | 48 n=69          | 57 n=69           |
| pf_net_3m   | 49 n=208   | 46 n=208         | 50 n=208          | 51 n=104   | 55 n=104         | 50 n=104          | 45 n=69    | 51 n=69          | 49 n=69           |
| pf_net_6m   | 46 n=208   | 47 n=208         | 56 n=208          | 51 n=104   | 47 n=104         | 61 n=104          | 51 n=69    | 54 n=69          | 65 n=69           |
| pf_net_d3m  | 51 n=208   | 51 n=208         | 47 n=208          | 48 n=104   | 59 n=104         | 42 n=104          | 45 n=69    | 58 n=69          | 49 n=69           |
| pf_eq_3m    | 45 n=208   | 50 n=208         | 48 n=208          | 46 n=104   | 47 n=104         | 49 n=104          | 45 n=69    | 48 n=69          | 57 n=69           |
| pf_debt_3m  | 50 n=208   | 50 n=208         | 52 n=208          | 52 n=104   | 57 n=104         | 50 n=104          | 49 n=69    | 57 n=69          | 45 n=69           |
| basic_12m   | 47 n=208   | 49 n=208         | 50 n=208          | 55 n=104   | 53 n=104         | 54 n=104          | 57 n=69    | 57 n=69          | 57 n=69           |
| tic_net_3m  | 51 n=208   | 49 n=208         | 43 n=208          | 44 n=104   | 53 n=104         | 47 n=104          | 48 n=69    | 52 n=69          | 54 n=69           |
| spf_contra  | 47 n=208   | 49 n=208         | 50 n=208          | 52 n=104   | 52 n=104         | 49 n=104          | 43 n=69    | 42 n=69          | 43 n=69           |

## 5. Round-7 controls: is it new information, or the exchange rate restated?

### 5a. Correlation of each oriented signal with the agreement inputs and with EUR/USD's own trailing and forward return (active sessions, 2010-26)

| signal     |   active_share |   share_long |   flips_per_year |   corr_cot_z52 |   corr_d_spread2y_20 |   corr_house_score |   corr_past_ret21 |   corr_past_ret63 |   r2_spot |   r2_all5 |   corr_fwd_ret21 |   corr_fwd_ret63 |
|:-----------|---------------:|-------------:|-----------------:|---------------:|---------------------:|-------------------:|------------------:|------------------:|----------:|----------:|-----------------:|-----------------:|
| cust_d4w   |           1    |         0.58 |            11.51 |          -0.12 |                 0.06 |              -0.05 |             -0.14 |             -0.25 |      0.06 |      0.08 |            -0.01 |            -0.03 |
| cust_d13w  |           1    |         0.64 |             4.04 |          -0.23 |                 0.04 |              -0.06 |             -0.12 |             -0.31 |      0.1  |      0.12 |            -0.03 |            -0.1  |
| swap_use   |           0.24 |         0.47 |             4.87 |          -0.11 |                -0.21 |              -0.09 |              0.17 |              0.27 |      0.07 |      0.25 |             0    |            -0.17 |
| repo_d13w  |           1    |         0.55 |             8.55 |           0.13 |                -0.06 |              -0.05 |              0.01 |              0.15 |      0.03 |      0.05 |            -0.03 |            -0    |
| pf_net_3m  |           1    |         0.48 |             2.85 |          -0.09 |                 0.02 |              -0.02 |             -0.01 |              0.04 |      0    |      0.03 |            -0.02 |            -0.06 |
| pf_net_6m  |           1    |         0.48 |             1.31 |          -0.12 |                 0.07 |              -0.01 |             -0.06 |             -0.02 |      0    |      0.04 |            -0.07 |            -0.05 |
| pf_net_d3m |           1    |         0.5  |             3.98 |          -0.03 |                -0.04 |              -0.01 |              0.05 |              0.09 |      0.01 |      0.03 |             0.02 |            -0.07 |
| pf_eq_3m   |           1    |         0.56 |             3.68 |           0.04 |                -0.06 |               0.03 |             -0.01 |              0.13 |      0.03 |      0.04 |            -0.09 |            -0.17 |
| pf_debt_3m |           1    |         0.45 |             2.85 |          -0.12 |                 0.08 |              -0.02 |             -0.01 |             -0.02 |      0    |      0.03 |             0.02 |             0.03 |
| basic_12m  |           1    |         0.65 |             0.83 |          -0.03 |                 0.13 |              -0.01 |             -0    |              0.04 |      0    |      0.04 |            -0.01 |            -0    |
| tic_net_3m |           1    |         0.44 |             3.15 |           0.15 |                 0.04 |               0.14 |              0.06 |              0.12 |      0.01 |      0.03 |             0.03 |            -0.01 |
| spf_contra |           1    |         0.33 |             0.65 |          -0.08 |                -0.14 |              -0.1  |             -0.14 |             -0.23 |      0.05 |      0.07 |            -0.13 |            -0.21 |

Share of active sessions on which the vote has the same sign as ...

| signal     |   same_sign_as_cot |   same_sign_as_spread_trend |   same_sign_as_house |   same_sign_as_agree3_when_agreed |   same_sign_as_past_ret63 |
|:-----------|-------------------:|----------------------------:|---------------------:|----------------------------------:|--------------------------:|
| cust_d4w   |               0.44 |                        0.49 |                 0.47 |                              0.45 |                      0.4  |
| cust_d13w  |               0.38 |                        0.51 |                 0.48 |                              0.41 |                      0.38 |
| swap_use   |               0.57 |                        0.53 |                 0.48 |                              0.56 |                      0.66 |
| repo_d13w  |               0.58 |                        0.44 |                 0.47 |                              0.51 |                      0.54 |
| pf_net_3m  |               0.45 |                        0.51 |                 0.5  |                              0.44 |                      0.48 |
| pf_net_6m  |               0.41 |                        0.53 |                 0.47 |                              0.43 |                      0.43 |
| pf_net_d3m |               0.53 |                        0.48 |                 0.48 |                              0.49 |                      0.59 |
| pf_eq_3m   |               0.46 |                        0.45 |                 0.46 |                              0.4  |                      0.46 |
| pf_debt_3m |               0.47 |                        0.55 |                 0.49 |                              0.5  |                      0.5  |
| basic_12m  |               0.48 |                        0.54 |                 0.49 |                              0.51 |                      0.52 |
| tic_net_3m |               0.49 |                        0.49 |                 0.55 |                              0.51 |                      0.53 |
| spf_contra |               0.5  |                        0.47 |                 0.53 |                              0.48 |                      0.48 |

### 5b. Lead or follow? Native-frequency correlation of each flow with the EUR/USD return, no publication lag

`k<0`: return of the k-th period BEFORE the flow period (the flow follows the exchange rate); `k=0`: same period; `k>0`: later periods (the flow leads). Flows are raw (inflows positive; SPF = expected change of USD per EUR), sample 2003-2026, descriptive. A correlation of 0.12 is about two standard errors at n = 280 and 0.11 at n = 320 (4-week blocks: 0.13 at n = 250; quarterly: 0.21 at n = 90).

| flow                                                    | period   | first      |   n |   k=-3 |   k=-2 |   k=-1 |   k=+0 |   k=+1 |   k=+2 |   k=+3 |
|:--------------------------------------------------------|:---------|:-----------|----:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| EA net portfolio inflow (monthly)                       | month    | 2003-01-31 | 283 |   0.01 |   0.08 |  -0.14 |  -0.09 |   0.07 |   0.05 |  -0.01 |
| EA net equity inflow (monthly)                          | month    | 2003-01-31 | 283 |  -0.1  |  -0.05 |  -0.12 |   0.01 |   0.12 |   0.02 |   0.05 |
| EA net debt inflow (monthly)                            | month    | 2003-01-31 | 283 |   0.07 |   0.11 |  -0.07 |  -0.1  |  -0.01 |   0.04 |  -0.04 |
| EA basic balance (monthly)                              | month    | 2003-01-31 | 283 |   0.04 |   0.08 |  -0.08 |  -0.06 |   0.09 |   0.11 |  -0.01 |
| EA current account (monthly)                            | month    | 2003-01-31 | 283 |   0.07 |  -0.01 |  -0.06 |  -0    |  -0.05 |  -0.1  |  -0.03 |
| TIC foreign net purchases of US LT securities (monthly) | month    | 2003-01-31 | 283 |   0.11 |   0.1  |   0.15 |   0.01 |  -0    |  -0.08 |   0    |
| TIC, foreign official only (monthly)                    | month    | 2003-01-31 | 283 |   0.09 |   0.13 |   0.15 |   0.01 |  -0.01 |  -0.06 |   0.02 |
| custody holdings, total (4-week log change)             | 4 weeks  | 2007-08-08 | 252 |  -0.04 |   0.04 |   0.21 |   0.14 |   0.02 |  -0.02 |   0.04 |
| custody, Treasuries only (4-week log change)            | 4 weeks  | 2007-08-08 | 252 |  -0.07 |  -0.04 |   0.17 |   0.1  |  -0.02 |  -0.02 |  -0.01 |
| foreign repo pool (4-week log change)                   | 4 weeks  | 2003-01-29 | 310 |   0.01 |  -0.1  |  -0.07 |  -0.02 |  -0.05 |   0.07 |   0.01 |
| swap lines (4-week change, USD bn)                      | 4 weeks  | 2003-01-29 | 310 |  -0.01 |  -0.13 |  -0.13 |  -0.13 |  -0.17 |   0.05 |   0.07 |
| SPF expected 9-month change (quarterly survey)          | quarter  | 2003-01-01 |  95 |  -0.13 |  -0.07 |  -0.1  |   0.21 |   0.24 |   0.16 |   0.15 |

### 5c. Standalone accuracy after orthogonalising (walk-forward) to the trailing 21- and 63-session return (`spot`) and to those plus cot_z52, d_spread2y_20 and the house score (`all5`)


Non-overlapping, 2010-26 (% right, decisions):

| candidate   | 21s raw   | 21s orth spot   | 21s orth all5   | 42s raw   | 42s orth spot   | 42s orth all5   | 63s raw   | 63s orth spot   | 63s orth all5   |
|:------------|:----------|:----------------|:----------------|:----------|:----------------|:----------------|:----------|:----------------|:----------------|
| cust_d4w    | 51 n=208  | 52 n=195        | 49 n=195        | 40 n=104  | 57 n=97         | 55 n=97         | 42 n=69   | 46 n=65         | 48 n=65         |
| cust_d13w   | 48 n=208  | 45 n=195        | 47 n=195        | 43 n=104  | 49 n=97         | 51 n=97         | 43 n=69   | 43 n=65         | 46 n=65         |
| swap_use    | 47 n=64   | 50 n=64         | 47 n=64         | 49 n=41   | 51 n=41         | 51 n=41         | 55 n=33   | 52 n=33         | 52 n=33         |
| repo_d13w   | 45 n=208  | 47 n=208        | 47 n=208        | 54 n=104  | 54 n=104        | 53 n=104        | 52 n=69   | 55 n=69         | 57 n=69         |
| pf_net_3m   | 49 n=208  | 49 n=208        | 48 n=208        | 51 n=104  | 51 n=104        | 53 n=104        | 45 n=69   | 43 n=69         | 45 n=69         |
| pf_net_6m   | 46 n=208  | 45 n=208        | 45 n=208        | 51 n=104  | 51 n=104        | 49 n=104        | 51 n=69   | 51 n=69         | 48 n=69         |
| pf_net_d3m  | 51 n=208  | 50 n=208        | 50 n=208        | 48 n=104  | 47 n=104        | 48 n=104        | 45 n=69   | 43 n=69         | 45 n=69         |
| pf_eq_3m    | 45 n=208  | 44 n=208        | 46 n=208        | 46 n=104  | 49 n=104        | 44 n=104        | 45 n=69   | 48 n=69         | 43 n=69         |
| pf_debt_3m  | 50 n=208  | 53 n=208        | 53 n=208        | 52 n=104  | 53 n=104        | 53 n=104        | 49 n=69   | 51 n=69         | 52 n=69         |
| basic_12m   | 47 n=208  | 47 n=208        | 47 n=208        | 55 n=104  | 54 n=104        | 56 n=104        | 57 n=69   | 54 n=69         | 55 n=69         |
| tic_net_3m  | 51 n=208  | 51 n=208        | 52 n=208        | 44 n=104  | 45 n=104        | 52 n=104        | 48 n=69   | 48 n=69         | 51 n=69         |
| spf_contra  | 47 n=208  | 49 n=208        | 51 n=208        | 52 n=104  | 51 n=104        | 55 n=104        | 43 n=69   | 41 n=69         | 48 n=69         |

Non-overlapping, 2016-26 (% right, decisions):

| candidate   | 21s raw   | 21s orth spot   | 21s orth all5   | 42s raw   | 42s orth spot   | 42s orth all5   | 63s raw   | 63s orth spot   | 63s orth all5   |
|:------------|:----------|:----------------|:----------------|:----------|:----------------|:----------------|:----------|:----------------|:----------------|
| cust_d4w    | 50 n=133  | 49 n=133        | 44 n=133        | 42 n=66   | 55 n=66         | 52 n=66         | 41 n=44   | 48 n=44         | 48 n=44         |
| cust_d13w   | 50 n=133  | 42 n=133        | 43 n=133        | 50 n=66   | 45 n=66         | 52 n=66         | 43 n=44   | 43 n=44         | 43 n=44         |
| swap_use    | 50 n=34   | 59 n=34         | 56 n=34         | 48 n=25   | 60 n=25         | 64 n=25         | 67 n=21   | 57 n=21         | 57 n=21         |
| repo_d13w   | 44 n=133  | 47 n=133        | 47 n=133        | 58 n=66   | 56 n=66         | 56 n=66         | 55 n=44   | 55 n=44         | 55 n=44         |
| pf_net_3m   | 47 n=133  | 47 n=133        | 46 n=133        | 48 n=66   | 47 n=66         | 50 n=66         | 45 n=44   | 45 n=44         | 45 n=44         |
| pf_net_6m   | 44 n=133  | 44 n=133        | 42 n=133        | 50 n=66   | 50 n=66         | 47 n=66         | 50 n=44   | 50 n=44         | 50 n=44         |
| pf_net_d3m  | 50 n=133  | 50 n=133        | 51 n=133        | 39 n=66   | 41 n=66         | 42 n=66         | 41 n=44   | 39 n=44         | 43 n=44         |
| pf_eq_3m    | 49 n=133  | 48 n=133        | 50 n=133        | 50 n=66   | 53 n=66         | 50 n=66         | 50 n=44   | 55 n=44         | 52 n=44         |
| pf_debt_3m  | 47 n=133  | 47 n=133        | 47 n=133        | 47 n=66   | 45 n=66         | 45 n=66         | 43 n=44   | 43 n=44         | 43 n=44         |
| basic_12m   | 50 n=133  | 50 n=133        | 50 n=133        | 59 n=66   | 58 n=66         | 59 n=66         | 66 n=44   | 61 n=44         | 61 n=44         |
| tic_net_3m  | 50 n=133  | 50 n=133        | 47 n=133        | 42 n=66   | 42 n=66         | 48 n=66         | 45 n=44   | 45 n=44         | 43 n=44         |
| spf_contra  | 53 n=133  | 56 n=133        | 55 n=133        | 58 n=66   | 58 n=66         | 58 n=66         | 45 n=44   | 45 n=44         | 50 n=44         |

Weekly decisions, 2010-26:

| candidate   | 21s raw   | 21s orth spot   | 21s orth all5   | 42s raw   | 42s orth spot   | 42s orth all5   | 63s raw   | 63s orth spot   | 63s orth all5   |
|:------------|:----------|:----------------|:----------------|:----------|:----------------|:----------------|:----------|:----------------|:----------------|
| cust_d4w    | 52 n=870  | 52 n=818        | 51 n=818        | 52 n=866  | 52 n=814        | 52 n=814        | 48 n=862  | 50 n=810        | 49 n=810        |
| cust_d13w   | 51 n=870  | 50 n=818        | 53 n=818        | 51 n=866  | 49 n=814        | 52 n=814        | 45 n=862  | 44 n=810        | 47 n=810        |
| swap_use    | 48 n=208  | 53 n=208        | 50 n=208        | 46 n=208  | 51 n=208        | 49 n=208        | 50 n=208  | 53 n=208        | 51 n=208        |
| repo_d13w   | 48 n=870  | 48 n=870        | 48 n=870        | 50 n=866  | 50 n=866        | 50 n=866        | 52 n=862  | 51 n=862        | 52 n=862        |
| pf_net_3m   | 47 n=870  | 47 n=870        | 48 n=870        | 47 n=866  | 46 n=866        | 47 n=866        | 45 n=862  | 44 n=862        | 45 n=862        |
| pf_net_6m   | 47 n=870  | 46 n=870        | 45 n=870        | 47 n=866  | 46 n=866        | 45 n=866        | 48 n=862  | 47 n=862        | 47 n=862        |
| pf_net_d3m  | 49 n=870  | 50 n=870        | 50 n=870        | 47 n=866  | 47 n=866        | 48 n=866        | 46 n=862  | 45 n=862        | 46 n=862        |
| pf_eq_3m    | 46 n=870  | 45 n=870        | 44 n=870        | 44 n=866  | 44 n=866        | 43 n=866        | 42 n=862  | 42 n=862        | 42 n=862        |
| pf_debt_3m  | 48 n=870  | 50 n=870        | 50 n=870        | 50 n=866  | 51 n=866        | 51 n=866        | 50 n=862  | 51 n=862        | 51 n=862        |
| basic_12m   | 47 n=870  | 48 n=870        | 49 n=870        | 51 n=866  | 50 n=866        | 52 n=866        | 50 n=862  | 49 n=862        | 51 n=862        |
| tic_net_3m  | 50 n=870  | 51 n=870        | 51 n=870        | 50 n=866  | 51 n=866        | 52 n=866        | 51 n=862  | 52 n=862        | 54 n=862        |
| spf_contra  | 48 n=870  | 47 n=870        | 52 n=870        | 51 n=866  | 50 n=866        | 56 n=866        | 50 n=862  | 49 n=862        | 56 n=862        |

### 5d. Replication: the dollar-side votes on the equal-weight basket of eight non-euro currencies against the dollar

Non-overlapping (% right, 95 % Wilson interval, decisions); weekly below.

| candidate   | 2010-26 / 21s    | 2010-26 / 42s    | 2010-26 / 63s   | 2016-26 / 21s    | 2016-26 / 42s   | 2016-26 / 63s   | 2023-26 / 21s    | 2023-26 / 42s   | 2023-26 / 63s   |
|:------------|:-----------------|:-----------------|:----------------|:-----------------|:----------------|:----------------|:-----------------|:----------------|:----------------|
| cust_d4w    | 50 [44-57] n=208 | 46 [37-56] n=104 | 46 [35-58] n=69 | 50 [42-59] n=133 | 48 [37-60] n=66 | 41 [28-56] n=44 | 60 [45-72] n=47  | 57 [37-74] n=23 | 53 [30-75] n=15 |
| cust_d13w   | 54 [47-60] n=208 | 51 [41-60] n=104 | 45 [34-57] n=69 | 51 [43-59] n=133 | 50 [38-62] n=66 | 43 [30-58] n=44 | 62 [47-74] n=47  | 52 [33-71] n=23 | 73 [48-89] n=15 |
| swap_use    | 41 [29-53] n=64  | 46 [32-61] n=41  | 55 [38-70] n=33 | 50 [34-66] n=34  | 52 [33-70] n=25 | 67 [45-83] n=21 | 100 [34-100] n=2 | 50 [9-91] n=2   | 50 [9-91] n=2   |
| repo_d13w   | 52 [46-59] n=208 | 56 [46-65] n=104 | 51 [39-62] n=69 | 50 [42-59] n=133 | 55 [43-66] n=66 | 50 [36-64] n=44 | 51 [37-65] n=47  | 61 [41-78] n=23 | 53 [30-75] n=15 |
| tic_net_3m  | 45 [38-52] n=208 | 38 [30-48] n=104 | 41 [30-52] n=69 | 48 [40-57] n=133 | 42 [31-54] n=66 | 41 [28-56] n=44 | 47 [33-61] n=47  | 30 [16-51] n=23 | 47 [25-70] n=15 |

| candidate   | 2010-26 / 21s   | 2010-26 / 42s   | 2010-26 / 63s   | 2016-26 / 21s   | 2016-26 / 42s   | 2016-26 / 63s   | 2023-26 / 21s   | 2023-26 / 42s   | 2023-26 / 63s   |
|:------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|
| cust_d4w    | 54 n=870        | 52 n=866        | 51 n=862        | 50 n=559        | 51 n=555        | 50 n=551        | 52 n=195        | 54 n=191        | 58 n=187        |
| cust_d13w   | 54 n=870        | 52 n=866        | 49 n=862        | 50 n=559        | 51 n=555        | 46 n=551        | 55 n=195        | 56 n=191        | 53 n=187        |
| swap_use    | 45 n=208        | 46 n=208        | 48 n=208        | 46 n=95         | 52 n=95         | 59 n=95         | 60 n=5          | 40 n=5          | 40 n=5          |
| repo_d13w   | 50 n=870        | 52 n=866        | 53 n=862        | 48 n=559        | 50 n=555        | 53 n=551        | 52 n=195        | 54 n=191        | 55 n=187        |
| tic_net_3m  | 48 n=870        | 45 n=866        | 47 n=862        | 50 n=559        | 48 n=555        | 49 n=551        | 47 n=195        | 43 n=191        | 49 n=187        |

### 5e. Zero-publication-lag control (ADDED AFTER THE FIRST RUN; not tradable, not a candidate)

The seven monthly votes as if month m's flow were known at the close of its last day (lag 0 instead of 60 / 56 days). Standalone, non-overlapping (% right, decisions), with the tradable (lagged) vote next to it, then the gain as an extra vote in points:


2010-26:

| candidate   | 21s published   | 21s zero lag   | 42s published   | 42s zero lag   | 63s published   | 63s zero lag   |
|:------------|:----------------|:---------------|:----------------|:---------------|:----------------|:---------------|
| pf_net_3m   | 49 n=208        | 48 n=208       | 51 n=104        | 45 n=104       | 45 n=69         | 48 n=69        |
| pf_net_6m   | 46 n=208        | 42 n=208       | 51 n=104        | 47 n=104       | 51 n=69         | 46 n=69        |
| pf_net_d3m  | 51 n=208        | 52 n=208       | 48 n=104        | 51 n=104       | 45 n=69         | 49 n=69        |
| pf_eq_3m    | 45 n=208        | 51 n=208       | 46 n=104        | 43 n=104       | 45 n=69         | 43 n=69        |
| pf_debt_3m  | 50 n=208        | 50 n=208       | 52 n=104        | 49 n=104       | 49 n=69         | 49 n=69        |
| basic_12m   | 47 n=208        | 52 n=208       | 55 n=104        | 54 n=104       | 57 n=69         | 54 n=69        |
| tic_net_3m  | 51 n=208        | 56 n=208       | 44 n=104        | 52 n=104       | 48 n=69         | 49 n=69        |

2016-26:

| candidate   | 21s published   | 21s zero lag   | 42s published   | 42s zero lag   | 63s published   | 63s zero lag   |
|:------------|:----------------|:---------------|:----------------|:---------------|:----------------|:---------------|
| pf_net_3m   | 47 n=133        | 47 n=133       | 48 n=66         | 38 n=66        | 45 n=44         | 45 n=44        |
| pf_net_6m   | 44 n=133        | 41 n=133       | 50 n=66         | 42 n=66        | 50 n=44         | 45 n=44        |
| pf_net_d3m  | 50 n=133        | 51 n=133       | 39 n=66         | 45 n=66        | 41 n=44         | 48 n=44        |
| pf_eq_3m    | 49 n=133        | 53 n=133       | 50 n=66         | 47 n=66        | 50 n=44         | 48 n=44        |
| pf_debt_3m  | 47 n=133        | 50 n=133       | 47 n=66         | 44 n=66        | 43 n=44         | 50 n=44        |
| basic_12m   | 50 n=133        | 55 n=133       | 59 n=66         | 61 n=66        | 66 n=44         | 61 n=44        |
| tic_net_3m  | 50 n=133        | 55 n=133       | 42 n=66         | 55 n=66        | 45 n=44         | 48 n=44        |

Extra-vote gain over the agreement rule with the zero-lag votes (points, non-overlapping):

| candidate   |   2010-26 / 21s |   2010-26 / 42s |   2010-26 / 63s |   2016-26 / 21s |   2016-26 / 42s |   2016-26 / 63s |   2023-26 / 21s |   2023-26 / 42s |   2023-26 / 63s |
|:------------|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|
| pf_net_3m   |            -3.8 |            -1.4 |            -4.6 |             2.3 |             1.1 |            -2.9 |            16.9 |            -7.5 |            33.3 |
| pf_net_6m   |           -10.3 |            -7.5 |           -12.1 |            -7.3 |            -8.9 |           -13.2 |           -14.5 |           -20   |           -10   |
| pf_net_d3m  |             2.9 |             0.3 |            -2.6 |             9.4 |            -3.7 |             2   |             8.4 |             1.2 |            27.8 |
| pf_eq_3m    |            -0.7 |            -0.3 |            -1.1 |             5.8 |            -0.9 |            -1.5 |             0   |             9.5 |            21.4 |
| pf_debt_3m  |             0.1 |            -0.7 |             6.4 |             6.2 |             2.8 |            12.3 |            13.3 |             5   |            21.4 |
| basic_12m   |            -6   |             2.8 |           -10.6 |             0.3 |             9.6 |            -1.8 |             8.8 |             9.5 |             5.6 |
| tic_net_3m  |            -1.8 |             2.1 |            -7.3 |             2   |            -3.4 |           -11.1 |            -7.4 |            -6.5 |           -21.4 |

## 6. As an extra vote

### 6a. Agreement rule AND the vote agrees, against the agreement rule alone

Non-overlapping decisions (% right, decisions, decisions per year). First row = the agreement rule alone.

| candidate   | 2010-26 / 21s    | 2010-26 / 42s   | 2010-26 / 63s   | 2016-26 / 21s   | 2016-26 / 42s   | 2016-26 / 63s   | 2023-26 / 21s   | 2023-26 / 42s   | 2023-26 / 63s   |
|:------------|:-----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|
| agree3      | 59 n=156 (9.3/y) | 61 n=89 (5.3/y) | 72 n=61 (3.7/y) | 57 n=96 (8.9/y) | 59 n=56 (5.2/y) | 71 n=38 (3.6/y) | 60 n=35 (9.3/y) | 45 n=20 (5.4/y) | 50 n=14 (3.9/y) |
| cust_d4w    | 58 n=98 (5.8/y)  | 65 n=65 (3.9/y) | 71 n=48 (2.9/y) | 64 n=61 (5.7/y) | 59 n=41 (3.8/y) | 73 n=30 (2.8/y) | 62 n=24 (6.4/y) | 67 n=15 (4.1/y) | 73 n=11 (3.1/y) |
| cust_d13w   | 59 n=75 (4.5/y)  | 65 n=51 (3.1/y) | 59 n=37 (2.2/y) | 57 n=49 (4.6/y) | 59 n=34 (3.2/y) | 52 n=23 (2.2/y) | 63 n=19 (5.0/y) | 54 n=13 (3.5/y) | 50 n=8 (2.2/y)  |
| swap_use    | 55 n=29 (1.7/y)  | 73 n=22 (1.3/y) | 74 n=19 (1.1/y) | 69 n=13 (1.2/y) | 82 n=11 (1.0/y) | 80 n=10 (0.9/y) | 50 n=2 (0.5/y)  | 50 n=2 (0.5/y)  | 50 n=2 (0.6/y)  |
| repo_d13w   | 53 n=105 (6.3/y) | 65 n=68 (4.1/y) | 66 n=50 (3.0/y) | 59 n=63 (5.9/y) | 62 n=40 (3.7/y) | 63 n=30 (2.8/y) | 59 n=27 (7.2/y) | 50 n=16 (4.3/y) | 50 n=12 (3.3/y) |
| pf_net_3m   | 55 n=83 (5.0/y)  | 56 n=57 (3.4/y) | 57 n=42 (2.5/y) | 55 n=49 (4.6/y) | 58 n=33 (3.1/y) | 54 n=24 (2.3/y) | 47 n=15 (4.0/y) | 36 n=11 (3.0/y) | 38 n=8 (2.2/y)  |
| pf_net_6m   | 49 n=71 (4.2/y)  | 52 n=46 (2.8/y) | 59 n=34 (2.0/y) | 49 n=43 (4.0/y) | 56 n=27 (2.5/y) | 63 n=19 (1.8/y) | 33 n=9 (2.4/y)  | 17 n=6 (1.6/y)  | 40 n=5 (1.4/y)  |
| pf_net_d3m  | 55 n=95 (5.7/y)  | 57 n=61 (3.7/y) | 65 n=48 (2.9/y) | 57 n=51 (4.7/y) | 53 n=34 (3.2/y) | 59 n=27 (2.5/y) | 50 n=20 (5.3/y) | 50 n=12 (3.3/y) | 50 n=10 (2.8/y) |
| pf_eq_3m    | 52 n=82 (4.9/y)  | 54 n=54 (3.2/y) | 60 n=40 (2.4/y) | 56 n=50 (4.6/y) | 56 n=32 (3.0/y) | 58 n=24 (2.3/y) | 41 n=17 (4.5/y) | 45 n=11 (3.0/y) | 33 n=9 (2.5/y)  |
| pf_debt_3m  | 55 n=87 (5.2/y)  | 57 n=58 (3.5/y) | 71 n=42 (2.5/y) | 53 n=55 (5.1/y) | 54 n=37 (3.5/y) | 73 n=26 (2.5/y) | 50 n=16 (4.3/y) | 33 n=12 (3.3/y) | 62 n=8 (2.2/y)  |
| basic_12m   | 49 n=84 (5.0/y)  | 63 n=51 (3.1/y) | 68 n=37 (2.2/y) | 53 n=60 (5.6/y) | 64 n=36 (3.4/y) | 72 n=25 (2.4/y) | 71 n=17 (4.5/y) | 50 n=12 (3.3/y) | 56 n=9 (2.5/y)  |
| tic_net_3m  | 58 n=89 (5.3/y)  | 62 n=60 (3.6/y) | 64 n=42 (2.5/y) | 56 n=57 (5.3/y) | 59 n=39 (3.7/y) | 62 n=26 (2.5/y) | 55 n=20 (5.3/y) | 46 n=13 (3.5/y) | 62 n=8 (2.2/y)  |
| spf_contra  | 50 n=80 (4.8/y)  | 69 n=48 (2.9/y) | 73 n=37 (2.2/y) | 58 n=50 (4.6/y) | 70 n=30 (2.8/y) | 78 n=23 (2.2/y) | 55 n=22 (5.8/y) | 58 n=12 (3.3/y) | 67 n=9 (2.5/y)  |

The same with 95 % Wilson intervals, 2010-26 only:

| candidate   | 2010-26 / 21s            | 2010-26 / 42s           | 2010-26 / 63s           |
|:------------|:-------------------------|:------------------------|:------------------------|
| agree3      | 59 [51-66] n=156 (9.3/y) | 61 [50-70] n=89 (5.3/y) | 72 [60-82] n=61 (3.7/y) |
| cust_d4w    | 58 [48-67] n=98 (5.8/y)  | 65 [52-75] n=65 (3.9/y) | 71 [57-82] n=48 (2.9/y) |
| cust_d13w   | 59 [47-69] n=75 (4.5/y)  | 65 [51-76] n=51 (3.1/y) | 59 [43-74] n=37 (2.2/y) |
| swap_use    | 55 [38-72] n=29 (1.7/y)  | 73 [52-87] n=22 (1.3/y) | 74 [51-88] n=19 (1.1/y) |
| repo_d13w   | 53 [44-63] n=105 (6.3/y) | 65 [53-75] n=68 (4.1/y) | 66 [52-78] n=50 (3.0/y) |
| pf_net_3m   | 55 [45-66] n=83 (5.0/y)  | 56 [43-68] n=57 (3.4/y) | 57 [42-71] n=42 (2.5/y) |
| pf_net_6m   | 49 [38-61] n=71 (4.2/y)  | 52 [38-66] n=46 (2.8/y) | 59 [42-74] n=34 (2.0/y) |
| pf_net_d3m  | 55 [45-64] n=95 (5.7/y)  | 57 [45-69] n=61 (3.7/y) | 65 [50-77] n=48 (2.9/y) |
| pf_eq_3m    | 52 [42-63] n=82 (4.9/y)  | 54 [41-66] n=54 (3.2/y) | 60 [45-74] n=40 (2.4/y) |
| pf_debt_3m  | 55 [45-65] n=87 (5.2/y)  | 57 [44-69] n=58 (3.5/y) | 71 [56-83] n=42 (2.5/y) |
| basic_12m   | 49 [38-59] n=84 (5.0/y)  | 63 [49-75] n=51 (3.1/y) | 68 [51-80] n=37 (2.2/y) |
| tic_net_3m  | 58 [48-68] n=89 (5.3/y)  | 62 [49-73] n=60 (3.6/y) | 64 [49-77] n=42 (2.5/y) |
| spf_contra  | 50 [39-61] n=80 (4.8/y)  | 69 [55-80] n=48 (2.9/y) | 73 [57-85] n=37 (2.2/y) |

Gain in accuracy points over the agreement rule, non-overlapping (bar: >= +3 at 21s and 42s in 2010-26 and 2016-26):

| candidate   |   2010-26 / 21s |   2010-26 / 42s |   2010-26 / 63s |   2016-26 / 21s |   2016-26 / 42s |   2016-26 / 63s |   2023-26 / 21s |   2023-26 / 42s |   2023-26 / 63s |
|:------------|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|
| cust_d4w    |            -0.8 |             3.9 |            -1.3 |             6.6 |            -0.4 |             2.3 |             2.5 |            21.7 |            22.7 |
| cust_d13w   |            -0.3 |             4   |           -12.7 |            -0.1 |            -0.1 |           -18.9 |             3.2 |             8.8 |             0   |
| swap_use    |            -3.8 |            12.1 |             1.6 |            11.9 |            22.9 |             8.9 |           -10   |             5   |             0   |
| repo_d13w   |            -5.6 |             4   |            -6.1 |             1.4 |             3.6 |            -7.7 |            -0.7 |             5   |             0   |
| pf_net_3m   |            -3.6 |            -4.5 |           -15   |            -2.2 |            -1.4 |           -16.9 |           -13.3 |            -8.6 |           -12.5 |
| pf_net_6m   |            -9.7 |            -8.5 |           -13.3 |            -8.5 |            -3.4 |            -7.9 |           -26.7 |           -28.3 |           -10   |
| pf_net_d3m  |            -4.2 |            -3.3 |            -7.5 |            -0.4 |            -6   |           -11.8 |           -10   |             5   |             0   |
| pf_eq_3m    |            -6.5 |            -7   |           -12.1 |            -1.3 |            -2.7 |           -12.7 |           -18.8 |             0.5 |           -16.7 |
| pf_debt_3m  |            -3.8 |            -3.8 |            -0.7 |            -4.6 |            -4.9 |             2   |           -10   |           -11.7 |            12.5 |
| basic_12m   |           -10.2 |             2.1 |            -4.6 |            -4   |             5   |             0.9 |            10.6 |             5   |             5.6 |
| tic_net_3m  |            -0.5 |             1   |            -7.8 |            -1.2 |             0   |            -9.5 |            -5   |             1.2 |            12.5 |
| spf_contra  |            -9   |             8.1 |             0.8 |             0.7 |            11.1 |             7.2 |            -5.5 |            13.3 |            16.7 |

Weekly decisions:

| candidate   | 2010-26 / 21s     | 2010-26 / 42s     | 2010-26 / 63s     | 2016-26 / 21s     | 2016-26 / 42s     | 2016-26 / 63s     | 2023-26 / 21s    | 2023-26 / 42s    | 2023-26 / 63s    |
|:------------|:------------------|:------------------|:------------------|:------------------|:------------------|:------------------|:-----------------|:-----------------|:-----------------|
| agree3      | 59 n=387 (23.1/y) | 65 n=383 (23.0/y) | 67 n=383 (23.1/y) | 57 n=243 (22.6/y) | 63 n=239 (22.4/y) | 67 n=239 (22.6/y) | 55 n=77 (20.6/y) | 47 n=73 (19.9/y) | 53 n=73 (20.4/y) |
| cust_d4w    | 63 n=175 (10.5/y) | 68 n=173 (10.4/y) | 66 n=173 (10.4/y) | 60 n=118 (11.0/y) | 66 n=116 (10.9/y) | 67 n=116 (11.0/y) | 66 n=41 (11.0/y) | 56 n=39 (10.7/y) | 62 n=39 (10.9/y) |
| cust_d13w   | 61 n=158 (9.4/y)  | 66 n=157 (9.4/y)  | 60 n=157 (9.5/y)  | 59 n=104 (9.7/y)  | 62 n=103 (9.7/y)  | 56 n=103 (9.7/y)  | 62 n=37 (9.9/y)  | 50 n=36 (9.8/y)  | 50 n=36 (10.0/y) |
| swap_use    | 61 n=46 (2.7/y)   | 54 n=46 (2.8/y)   | 65 n=46 (2.8/y)   | 73 n=15 (1.4/y)   | 80 n=15 (1.4/y)   | 100 n=15 (1.4/y)  | 100 n=1 (0.3/y)  | 100 n=1 (0.3/y)  | 100 n=1 (0.3/y)  |
| repo_d13w   | 56 n=200 (11.9/y) | 65 n=198 (11.9/y) | 64 n=198 (11.9/y) | 54 n=124 (11.5/y) | 64 n=122 (11.4/y) | 66 n=122 (11.5/y) | 57 n=37 (9.9/y)  | 51 n=35 (9.6/y)  | 49 n=35 (9.8/y)  |
| pf_net_3m   | 57 n=171 (10.2/y) | 60 n=171 (10.3/y) | 62 n=171 (10.3/y) | 56 n=104 (9.7/y)  | 58 n=104 (9.8/y)  | 62 n=104 (9.8/y)  | 44 n=25 (6.7/y)  | 36 n=25 (6.8/y)  | 52 n=25 (7.0/y)  |
| pf_net_6m   | 59 n=163 (9.7/y)  | 65 n=163 (9.8/y)  | 71 n=163 (9.8/y)  | 59 n=104 (9.7/y)  | 63 n=104 (9.8/y)  | 74 n=104 (9.8/y)  | 58 n=19 (5.1/y)  | 42 n=19 (5.2/y)  | 79 n=19 (5.3/y)  |
| pf_net_d3m  | 60 n=194 (11.6/y) | 60 n=194 (11.6/y) | 64 n=194 (11.7/y) | 57 n=99 (9.2/y)   | 52 n=99 (9.3/y)   | 60 n=99 (9.4/y)   | 44 n=32 (8.6/y)  | 31 n=32 (8.7/y)  | 38 n=32 (8.9/y)  |
| pf_eq_3m    | 55 n=148 (8.8/y)  | 57 n=148 (8.9/y)  | 59 n=148 (8.9/y)  | 57 n=86 (8.0/y)   | 59 n=86 (8.1/y)   | 65 n=86 (8.1/y)   | 52 n=23 (6.2/y)  | 39 n=23 (6.3/y)  | 65 n=23 (6.4/y)  |
| pf_debt_3m  | 58 n=193 (11.5/y) | 65 n=193 (11.6/y) | 70 n=193 (11.6/y) | 57 n=123 (11.5/y) | 61 n=123 (11.5/y) | 70 n=123 (11.6/y) | 43 n=30 (8.0/y)  | 33 n=30 (8.2/y)  | 50 n=30 (8.4/y)  |
| basic_12m   | 53 n=189 (11.3/y) | 61 n=189 (11.3/y) | 62 n=189 (11.4/y) | 55 n=153 (14.2/y) | 64 n=153 (14.3/y) | 67 n=153 (14.5/y) | 47 n=30 (8.0/y)  | 40 n=30 (8.2/y)  | 40 n=30 (8.4/y)  |
| tic_net_3m  | 57 n=194 (11.6/y) | 67 n=190 (11.4/y) | 72 n=190 (11.5/y) | 56 n=131 (12.2/y) | 68 n=127 (11.9/y) | 75 n=127 (12.0/y) | 54 n=35 (9.4/y)  | 45 n=31 (8.5/y)  | 65 n=31 (8.6/y)  |
| spf_contra  | 56 n=183 (10.9/y) | 67 n=179 (10.7/y) | 66 n=179 (10.8/y) | 60 n=126 (11.7/y) | 75 n=122 (11.4/y) | 76 n=122 (11.5/y) | 62 n=42 (11.2/y) | 61 n=38 (10.4/y) | 58 n=38 (10.6/y) |

The extra vote with the ORTHOGONALISED signals (gain in points over the agreement rule, non-overlapping):


`orth_spot`:

| candidate   |   2010-26 / 21s |   2010-26 / 42s |   2010-26 / 63s |   2016-26 / 21s |   2016-26 / 42s |   2016-26 / 63s |   2023-26 / 21s |   2023-26 / 42s |   2023-26 / 63s |
|:------------|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|
| cust_d4w    |            -3.8 |             7   |             2.9 |             0.5 |             7.7 |            10.2 |            -0.7 |            21.7 |            25   |
| cust_d13w   |            -5.5 |           -13.4 |           -20.9 |            -5.6 |           -14.2 |           -21.1 |             0.9 |             1.7 |            -4.5 |
| swap_use    |            -9   |            22.7 |            17.9 |             2.7 |            26.8 |            28.9 |            40   |            55   |            50   |
| repo_d13w   |            -8   |             5.5 |            -9.6 |            -4.1 |             6.1 |            -7.7 |            -6.2 |            11.2 |             0   |
| pf_net_3m   |            -6.8 |            -2.1 |           -14   |            -1.3 |            -1.4 |           -16.9 |           -10   |            -8.6 |           -12.5 |
| pf_net_6m   |           -10.4 |            -8.5 |           -16.2 |            -8.5 |            -3.4 |            -7.9 |           -26.7 |           -28.3 |           -10   |
| pf_net_d3m  |            -4.8 |            -2.6 |            -7.5 |            -0.4 |            -6   |           -11.8 |           -10   |             5   |             0   |
| pf_eq_3m    |            -5.8 |            -4.9 |           -15.7 |            -1.5 |             2.8 |           -15.1 |           -21.1 |            -3.3 |           -20   |
| pf_debt_3m  |            -5   |            -3.1 |            -2.6 |            -3.8 |            -5.1 |             3   |           -10   |           -11.7 |            12.5 |
| basic_12m   |            -9.6 |             2.6 |            -4.6 |            -3.8 |             5.8 |             0.9 |            13.3 |             5   |             5.6 |
| tic_net_3m  |            -1.8 |             2.7 |            -3.1 |            -1.2 |             0   |            -9.5 |            -5   |             1.2 |            12.5 |
| spf_contra  |            -9.5 |             6.6 |            -4.6 |             3.4 |            10.8 |             4.9 |            -5.5 |            13.3 |            16.7 |

`orth_all5`:

| candidate   |   2010-26 / 21s |   2010-26 / 42s |   2010-26 / 63s |   2016-26 / 21s |   2016-26 / 42s |   2016-26 / 63s |   2023-26 / 21s |   2023-26 / 42s |   2023-26 / 63s |
|:------------|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|
| cust_d4w    |            -6.1 |             3.4 |             2.3 |            -2.1 |             6.9 |             9.6 |            -7.8 |            19.3 |            13.6 |
| cust_d13w   |            -1.5 |            -6.4 |           -15   |             1   |            -1   |           -19.2 |             2.5 |            -1.3 |            -4.5 |
| swap_use    |            -3.4 |            17.9 |            18.8 |             4.2 |            31.1 |            28.9 |            40   |            55   |            50   |
| repo_d13w   |            -6.5 |             5.5 |            -5.5 |            -3.3 |             6.1 |            -5.5 |            -2.3 |            11.2 |             4.5 |
| pf_net_3m   |            -6.8 |            -3   |           -14.4 |            -4.5 |            -0.1 |           -17.2 |           -10   |            -8.6 |           -12.5 |
| pf_net_6m   |            -3.8 |           -10.7 |           -14.6 |            -8.5 |            -5.1 |           -11.1 |           -26.7 |           -28.3 |           -10   |
| pf_net_d3m  |            -4.4 |            -2.2 |            -6.8 |             0.1 |            -4.9 |           -10.3 |            -7.6 |             8.8 |            -4.5 |
| pf_eq_3m    |            -7.6 |            -8.7 |           -15.7 |            -0.1 |            -1.4 |           -12.7 |           -15.6 |             1.2 |           -10   |
| pf_debt_3m  |            -2.5 |            -0.1 |             0.8 |            -2.1 |            -2.5 |             3.9 |            -7.1 |            -6.5 |            16.7 |
| basic_12m   |            -6.2 |             3   |            -7.1 |            -3.2 |             7.7 |             2   |             8.8 |             9.5 |             5.6 |
| tic_net_3m  |            -4   |             0.3 |            -1   |            -5.6 |            -1.4 |            -0.7 |           -12.4 |            -6.5 |            27.8 |
| spf_contra  |            -3.7 |            11.9 |            -1.7 |             3.7 |            13.3 |             5.9 |            -3.5 |            16.5 |            16.7 |

### 6b. Coverage extension: the vote's own calls on sessions where the three old signals do NOT agree

Non-overlapping, with 95 % Wilson intervals, 2010-26, then all periods without intervals:

| candidate   | 2010-26 / 21s             | 2010-26 / 42s           | 2010-26 / 63s           |
|:------------|:--------------------------|:------------------------|:------------------------|
| cust_d4w    | 54 [47-61] n=170 (10.1/y) | 52 [42-62] n=93 (5.6/y) | 31 [21-43] n=64 (3.9/y) |
| cust_d13w   | 49 [42-57] n=170 (10.1/y) | 52 [42-62] n=93 (5.6/y) | 42 [31-54] n=64 (3.9/y) |
| swap_use    | 47 [34-60] n=53 (3.2/y)   | 51 [36-67] n=37 (2.2/y) | 43 [27-61] n=30 (1.8/y) |
| repo_d13w   | 48 [40-55] n=170 (10.1/y) | 43 [33-53] n=93 (5.6/y) | 55 [43-66] n=64 (3.9/y) |
| pf_net_3m   | 49 [41-56] n=170 (10.1/y) | 48 [38-58] n=93 (5.6/y) | 39 [28-51] n=64 (3.9/y) |
| pf_net_6m   | 48 [41-56] n=170 (10.1/y) | 45 [35-55] n=93 (5.6/y) | 42 [31-54] n=64 (3.9/y) |
| pf_net_d3m  | 55 [48-63] n=170 (10.1/y) | 53 [43-63] n=93 (5.6/y) | 59 [47-71] n=64 (3.9/y) |
| pf_eq_3m    | 48 [40-55] n=170 (10.1/y) | 44 [34-54] n=93 (5.6/y) | 56 [44-68] n=64 (3.9/y) |
| pf_debt_3m  | 52 [44-59] n=170 (10.1/y) | 49 [40-59] n=93 (5.6/y) | 50 [38-62] n=64 (3.9/y) |
| basic_12m   | 48 [40-55] n=170 (10.1/y) | 46 [36-56] n=93 (5.6/y) | 59 [47-71] n=64 (3.9/y) |
| tic_net_3m  | 51 [43-58] n=170 (10.1/y) | 52 [42-62] n=93 (5.6/y) | 47 [35-59] n=64 (3.9/y) |
| spf_contra  | 49 [42-57] n=170 (10.1/y) | 48 [38-58] n=93 (5.6/y) | 50 [38-62] n=64 (3.9/y) |

| candidate   | 2010-26 / 21s     | 2010-26 / 42s   | 2010-26 / 63s   | 2016-26 / 21s     | 2016-26 / 42s   | 2016-26 / 63s   | 2023-26 / 21s    | 2023-26 / 42s   | 2023-26 / 63s   |
|:------------|:------------------|:----------------|:----------------|:------------------|:----------------|:----------------|:-----------------|:----------------|:----------------|
| cust_d4w    | 54 n=170 (10.1/y) | 52 n=93 (5.6/y) | 31 n=64 (3.9/y) | 53 n=109 (10.1/y) | 50 n=60 (5.6/y) | 29 n=41 (3.9/y) | 55 n=38 (10.1/y) | 52 n=21 (5.7/y) | 36 n=14 (3.9/y) |
| cust_d13w   | 49 n=170 (10.1/y) | 52 n=93 (5.6/y) | 42 n=64 (3.9/y) | 49 n=109 (10.1/y) | 47 n=60 (5.6/y) | 39 n=41 (3.9/y) | 55 n=38 (10.1/y) | 52 n=21 (5.7/y) | 50 n=14 (3.9/y) |
| swap_use    | 47 n=53 (3.2/y)   | 51 n=37 (2.2/y) | 43 n=30 (1.8/y) | 50 n=28 (2.6/y)   | 55 n=22 (2.1/y) | 50 n=18 (1.7/y) | 50 n=2 (0.5/y)   | 50 n=2 (0.5/y)  | 50 n=2 (0.6/y)  |
| repo_d13w   | 48 n=170 (10.1/y) | 43 n=93 (5.6/y) | 55 n=64 (3.9/y) | 47 n=109 (10.1/y) | 43 n=60 (5.6/y) | 59 n=41 (3.9/y) | 50 n=38 (10.1/y) | 43 n=21 (5.7/y) | 57 n=14 (3.9/y) |
| pf_net_3m   | 49 n=170 (10.1/y) | 48 n=93 (5.6/y) | 39 n=64 (3.9/y) | 51 n=109 (10.1/y) | 50 n=60 (5.6/y) | 39 n=41 (3.9/y) | 50 n=38 (10.1/y) | 57 n=21 (5.7/y) | 43 n=14 (3.9/y) |
| pf_net_6m   | 48 n=170 (10.1/y) | 45 n=93 (5.6/y) | 42 n=64 (3.9/y) | 47 n=109 (10.1/y) | 45 n=60 (5.6/y) | 44 n=41 (3.9/y) | 34 n=38 (10.1/y) | 38 n=21 (5.7/y) | 43 n=14 (3.9/y) |
| pf_net_d3m  | 55 n=170 (10.1/y) | 53 n=93 (5.6/y) | 59 n=64 (3.9/y) | 54 n=109 (10.1/y) | 50 n=60 (5.6/y) | 56 n=41 (3.9/y) | 53 n=38 (10.1/y) | 62 n=21 (5.7/y) | 57 n=14 (3.9/y) |
| pf_eq_3m    | 48 n=170 (10.1/y) | 44 n=93 (5.6/y) | 56 n=64 (3.9/y) | 50 n=109 (10.1/y) | 52 n=60 (5.6/y) | 66 n=41 (3.9/y) | 47 n=38 (10.1/y) | 52 n=21 (5.7/y) | 86 n=14 (3.9/y) |
| pf_debt_3m  | 52 n=170 (10.1/y) | 49 n=93 (5.6/y) | 50 n=64 (3.9/y) | 53 n=109 (10.1/y) | 48 n=60 (5.6/y) | 49 n=41 (3.9/y) | 42 n=38 (10.1/y) | 48 n=21 (5.7/y) | 21 n=14 (3.9/y) |
| basic_12m   | 48 n=170 (10.1/y) | 46 n=93 (5.6/y) | 59 n=64 (3.9/y) | 52 n=109 (10.1/y) | 50 n=60 (5.6/y) | 59 n=41 (3.9/y) | 50 n=38 (10.1/y) | 48 n=21 (5.7/y) | 57 n=14 (3.9/y) |
| tic_net_3m  | 51 n=170 (10.1/y) | 52 n=93 (5.6/y) | 47 n=64 (3.9/y) | 52 n=109 (10.1/y) | 52 n=60 (5.6/y) | 46 n=41 (3.9/y) | 42 n=38 (10.1/y) | 48 n=21 (5.7/y) | 57 n=14 (3.9/y) |
| spf_contra  | 49 n=170 (10.1/y) | 48 n=93 (5.6/y) | 50 n=64 (3.9/y) | 52 n=109 (10.1/y) | 55 n=60 (5.6/y) | 56 n=41 (3.9/y) | 55 n=38 (10.1/y) | 57 n=21 (5.7/y) | 57 n=14 (3.9/y) |

### 6c. Paired differences

`paired_weekly`: accuracy(extra-vote rule) - accuracy(agreement rule) on the same weekly grid, circular block bootstrap (block 2h/5 weeks, 2000 draws). `paired_nonoverlap_on_agree3_stream`: on the agreement rule's own non-overlapping decisions, accuracy of those the vote confirms minus all (iid bootstrap over decisions). `acc_dropped` = accuracy of the agreement-rule decisions the vote rejects.


paired_weekly (points):

| candidate   |   h | period   |   n_agree |   n_extra |   acc_agree |   acc_extra |   acc_dropped |   diff |   diff_lo |   diff_hi |   p_diff_le0 |
|:------------|----:|:---------|----------:|----------:|------------:|------------:|--------------:|-------:|----------:|----------:|-------------:|
| cust_d4w    |  21 | 2010-26  |       387 |       175 |        59.4 |        63.4 |          56.1 |    4   |      -2.4 |      10.5 |         0.12 |
| cust_d4w    |  21 | 2016-26  |       243 |       118 |        57.2 |        60.2 |          54.4 |    3   |      -4.4 |      11   |         0.23 |
| cust_d4w    |  42 | 2010-26  |       383 |       173 |        64.8 |        67.6 |          62.4 |    2.9 |      -4.6 |      10.2 |         0.22 |
| cust_d4w    |  42 | 2016-26  |       239 |       116 |        63.2 |        65.5 |          61   |    2.3 |      -8.2 |      12.6 |         0.33 |
| cust_d13w   |  21 | 2010-26  |       387 |       158 |        59.4 |        61.4 |          58.1 |    2   |      -6.9 |      10.4 |         0.32 |
| cust_d13w   |  21 | 2016-26  |       243 |       104 |        57.2 |        58.7 |          56.1 |    1.5 |      -9.1 |      11.2 |         0.4  |
| cust_d13w   |  42 | 2010-26  |       383 |       157 |        64.8 |        65.6 |          64.2 |    0.9 |      -9.3 |       9.6 |         0.42 |
| cust_d13w   |  42 | 2016-26  |       239 |       103 |        63.2 |        62.1 |          64   |   -1   |     -13.6 |       9.8 |         0.57 |
| swap_use    |  21 | 2010-26  |       387 |        46 |        59.4 |        60.9 |          59.2 |    1.4 |     -15.1 |      19.3 |         0.41 |
| swap_use    |  21 | 2016-26  |       243 |        15 |        57.2 |        73.3 |          56.1 |   16.1 |     -11.4 |      40.1 |         0.1  |
| swap_use    |  42 | 2010-26  |       383 |        46 |        64.8 |        54.3 |          66.2 |  -10.4 |     -25.6 |      10.9 |         0.86 |
| swap_use    |  42 | 2016-26  |       239 |        15 |        63.2 |        80   |          62.1 |   16.8 |      -6.3 |      39   |         0.06 |
| repo_d13w   |  21 | 2010-26  |       387 |       200 |        59.4 |        56   |          63.1 |   -3.4 |      -9.5 |       2.4 |         0.87 |
| repo_d13w   |  21 | 2016-26  |       243 |       124 |        57.2 |        54   |          60.5 |   -3.2 |     -11.7 |       4.5 |         0.79 |
| repo_d13w   |  42 | 2010-26  |       383 |       198 |        64.8 |        64.6 |          64.9 |   -0.1 |      -6.5 |       5.9 |         0.51 |
| repo_d13w   |  42 | 2016-26  |       239 |       122 |        63.2 |        63.9 |          62.4 |    0.8 |      -8.3 |       8.6 |         0.44 |
| pf_net_3m   |  21 | 2010-26  |       387 |       171 |        59.4 |        57.3 |          61.1 |   -2.1 |      -9.5 |       4.8 |         0.71 |
| pf_net_3m   |  21 | 2016-26  |       243 |       104 |        57.2 |        55.8 |          58.3 |   -1.4 |     -11.4 |       9.1 |         0.61 |
| pf_net_3m   |  42 | 2010-26  |       383 |       171 |        64.8 |        60.2 |          68.4 |   -4.5 |     -13.6 |       3.6 |         0.87 |
| pf_net_3m   |  42 | 2016-26  |       239 |       104 |        63.2 |        57.7 |          67.4 |   -5.5 |     -17.2 |       4.6 |         0.85 |
| pf_net_6m   |  21 | 2010-26  |       387 |       163 |        59.4 |        58.9 |          59.8 |   -0.5 |      -8.8 |       6.8 |         0.53 |
| pf_net_6m   |  21 | 2016-26  |       243 |       104 |        57.2 |        58.7 |          56.1 |    1.5 |      -9.2 |      12.2 |         0.4  |
| pf_net_6m   |  42 | 2010-26  |       383 |       163 |        64.8 |        65   |          64.5 |    0.3 |     -10.7 |       9.3 |         0.46 |
| pf_net_6m   |  42 | 2016-26  |       239 |       104 |        63.2 |        63.5 |          63   |    0.3 |     -12.7 |      12.7 |         0.47 |
| pf_net_d3m  |  21 | 2010-26  |       387 |       194 |        59.4 |        59.8 |          59.1 |    0.4 |      -5.8 |       6.4 |         0.47 |
| pf_net_d3m  |  21 | 2016-26  |       243 |        99 |        57.2 |        56.6 |          57.6 |   -0.6 |     -10.8 |       9.4 |         0.52 |
| pf_net_d3m  |  42 | 2010-26  |       383 |       194 |        64.8 |        59.8 |          69.8 |   -5   |     -12.1 |       1.3 |         0.93 |
| pf_net_d3m  |  42 | 2016-26  |       239 |        99 |        63.2 |        51.5 |          71.4 |  -11.7 |     -22.9 |      -1.5 |         0.99 |
| pf_eq_3m    |  21 | 2010-26  |       387 |       148 |        59.4 |        54.7 |          62.3 |   -4.7 |     -14   |       3.5 |         0.86 |
| pf_eq_3m    |  21 | 2016-26  |       243 |        86 |        57.2 |        57   |          57.3 |   -0.2 |     -12.1 |      11.6 |         0.49 |
| pf_eq_3m    |  42 | 2010-26  |       383 |       148 |        64.8 |        56.8 |          69.8 |   -8   |     -18.4 |       1.9 |         0.95 |
| pf_eq_3m    |  42 | 2016-26  |       239 |        86 |        63.2 |        59.3 |          65.4 |   -3.9 |     -15.7 |       8.2 |         0.74 |
| pf_debt_3m  |  21 | 2010-26  |       387 |       193 |        59.4 |        58   |          60.8 |   -1.4 |      -8.6 |       5.3 |         0.63 |
| pf_debt_3m  |  21 | 2016-26  |       243 |       123 |        57.2 |        56.9 |          57.5 |   -0.3 |      -8.5 |       8.4 |         0.53 |
| pf_debt_3m  |  42 | 2010-26  |       383 |       193 |        64.8 |        65.3 |          64.2 |    0.5 |      -8   |       8.5 |         0.46 |
| pf_debt_3m  |  42 | 2016-26  |       239 |       123 |        63.2 |        61   |          65.5 |   -2.2 |     -12.2 |       7.1 |         0.68 |
| basic_12m   |  21 | 2010-26  |       387 |       189 |        59.4 |        52.9 |          65.7 |   -6.5 |     -13.7 |       0.7 |         0.96 |
| basic_12m   |  21 | 2016-26  |       243 |       153 |        57.2 |        54.9 |          61.1 |   -2.3 |     -10.4 |       5.4 |         0.73 |
| basic_12m   |  42 | 2010-26  |       383 |       189 |        64.8 |        61.4 |          68   |   -3.4 |     -13.7 |       5.4 |         0.77 |
| basic_12m   |  42 | 2016-26  |       239 |       153 |        63.2 |        64.1 |          61.6 |    0.9 |      -7.3 |       8.8 |         0.4  |
| tic_net_3m  |  21 | 2010-26  |       387 |       194 |        59.4 |        57.2 |          61.7 |   -2.2 |      -9.5 |       4.5 |         0.75 |
| tic_net_3m  |  21 | 2016-26  |       243 |       131 |        57.2 |        55.7 |          58.9 |   -1.5 |     -10.5 |       7   |         0.64 |
| tic_net_3m  |  42 | 2010-26  |       383 |       190 |        64.8 |        66.8 |          62.7 |    2.1 |      -6.2 |       9.9 |         0.31 |
| tic_net_3m  |  42 | 2016-26  |       239 |       127 |        63.2 |        67.7 |          58   |    4.5 |      -5.6 |      13.7 |         0.17 |
| spf_contra  |  21 | 2010-26  |       387 |       183 |        59.4 |        56.3 |          62.3 |   -3.1 |     -10.4 |       3.6 |         0.81 |
| spf_contra  |  21 | 2016-26  |       243 |       126 |        57.2 |        59.5 |          54.7 |    2.3 |      -6.5 |      11   |         0.29 |
| spf_contra  |  42 | 2010-26  |       383 |       179 |        64.8 |        67   |          62.7 |    2.3 |      -7.1 |      11   |         0.31 |
| spf_contra  |  42 | 2016-26  |       239 |       122 |        63.2 |        74.6 |          51.3 |   11.4 |       1.7 |      20.6 |         0.01 |

paired_nonoverlap_on_agree3_stream (points):

| candidate   |   h | period   |   n_agree |   n_extra |   acc_agree |   acc_extra |   acc_dropped |   diff |   diff_lo |   diff_hi |   p_diff_le0 |
|:------------|----:|:---------|----------:|----------:|------------:|------------:|--------------:|-------:|----------:|----------:|-------------:|
| cust_d4w    |  21 | 2010-26  |       156 |        67 |        59   |        61.2 |          57.3 |    2.2 |      -7.1 |      11.3 |         0.32 |
| cust_d4w    |  21 | 2016-26  |        96 |        40 |        57.3 |        62.5 |          53.6 |    5.2 |      -6.4 |      16.8 |         0.19 |
| cust_d4w    |  42 | 2010-26  |        89 |        36 |        60.7 |        61.1 |          60.4 |    0.4 |     -12.4 |      12.9 |         0.47 |
| cust_d4w    |  42 | 2016-26  |        56 |        25 |        58.9 |        56   |          61.3 |   -2.9 |     -17.3 |      11.6 |         0.66 |
| cust_d13w   |  21 | 2010-26  |       156 |        66 |        59   |        63.6 |          55.6 |    4.7 |      -4.7 |      13.9 |         0.15 |
| cust_d13w   |  21 | 2016-26  |        96 |        42 |        57.3 |        64.3 |          51.9 |    7   |      -4.2 |      18.9 |         0.1  |
| cust_d13w   |  42 | 2010-26  |        89 |        37 |        60.7 |        64.9 |          57.7 |    4.2 |      -8   |      16.1 |         0.25 |
| cust_d13w   |  42 | 2016-26  |        56 |        23 |        58.9 |        60.9 |          57.6 |    1.9 |     -13.6 |      18.2 |         0.4  |
| swap_use    |  21 | 2010-26  |       156 |        19 |        59   |        57.9 |          59.1 |   -1.1 |     -23.3 |      19.7 |         0.54 |
| swap_use    |  21 | 2016-26  |        96 |         7 |        57.3 |        57.1 |          57.3 |   -0.1 |     -41.7 |      40.6 |         0.51 |
| swap_use    |  42 | 2010-26  |        89 |        16 |        60.7 |        62.5 |          60.3 |    1.8 |     -20.6 |      24.1 |         0.42 |
| swap_use    |  42 | 2016-26  |        56 |         7 |        58.9 |        57.1 |          59.2 |   -1.8 |     -41.1 |      35.7 |         0.55 |
| repo_d13w   |  21 | 2010-26  |       156 |        79 |        59   |        55.7 |          62.3 |   -3.3 |     -11.3 |       4.3 |         0.8  |
| repo_d13w   |  21 | 2016-26  |        96 |        52 |        57.3 |        55.8 |          59.1 |   -1.5 |     -10.5 |       8.1 |         0.62 |
| repo_d13w   |  42 | 2010-26  |        89 |        46 |        60.7 |        63   |          58.1 |    2.4 |      -7.6 |      12.3 |         0.32 |
| repo_d13w   |  42 | 2016-26  |        56 |        30 |        58.9 |        60   |          57.7 |    1.1 |     -10.7 |      13.3 |         0.46 |
| pf_net_3m   |  21 | 2010-26  |       156 |        72 |        59   |        56.9 |          60.7 |   -2   |     -10.4 |       6.3 |         0.69 |
| pf_net_3m   |  21 | 2016-26  |        96 |        44 |        57.3 |        52.3 |          61.5 |   -5   |     -15.9 |       6.2 |         0.82 |
| pf_net_3m   |  42 | 2010-26  |        89 |        44 |        60.7 |        56.8 |          64.4 |   -3.9 |     -14.1 |       6.6 |         0.76 |
| pf_net_3m   |  42 | 2016-26  |        56 |        27 |        58.9 |        51.9 |          65.5 |   -7.1 |     -21.1 |       6.9 |         0.85 |
| pf_net_6m   |  21 | 2010-26  |       156 |        65 |        59   |        53.8 |          62.6 |   -5.1 |     -14.3 |       4   |         0.86 |
| pf_net_6m   |  21 | 2016-26  |        96 |        40 |        57.3 |        47.5 |          64.3 |   -9.8 |     -22.2 |       2.4 |         0.94 |
| pf_net_6m   |  42 | 2010-26  |        89 |        39 |        60.7 |        53.8 |          66   |   -6.8 |     -18.5 |       5   |         0.87 |
| pf_net_6m   |  42 | 2016-26  |        56 |        24 |        58.9 |        54.2 |          62.5 |   -4.8 |     -20.4 |      10.7 |         0.74 |
| pf_net_d3m  |  21 | 2010-26  |       156 |        85 |        59   |        58.8 |          59.2 |   -0.2 |      -7.3 |       7.1 |         0.53 |
| pf_net_d3m  |  21 | 2016-26  |        96 |        46 |        57.3 |        56.5 |          58   |   -0.8 |     -11.5 |       9.5 |         0.56 |
| pf_net_d3m  |  42 | 2010-26  |        89 |        49 |        60.7 |        55.1 |          67.5 |   -5.6 |     -15.1 |       3   |         0.89 |
| pf_net_d3m  |  42 | 2016-26  |        56 |        27 |        58.9 |        44.4 |          72.4 |  -14.5 |     -28.9 |      -0.9 |         0.98 |
| pf_eq_3m    |  21 | 2010-26  |       156 |        73 |        59   |        54.8 |          62.7 |   -4.2 |     -12.8 |       3.8 |         0.85 |
| pf_eq_3m    |  21 | 2016-26  |        96 |        44 |        57.3 |        56.8 |          57.7 |   -0.5 |     -11.5 |      10.9 |         0.53 |
| pf_eq_3m    |  42 | 2010-26  |        89 |        41 |        60.7 |        53.7 |          66.7 |   -7   |     -18.2 |       3.9 |         0.89 |
| pf_eq_3m    |  42 | 2016-26  |        56 |        25 |        58.9 |        56   |          61.3 |   -2.9 |     -18.1 |      11.9 |         0.66 |
| pf_debt_3m  |  21 | 2010-26  |       156 |        76 |        59   |        57.9 |          60   |   -1.1 |      -9   |       6.8 |         0.62 |
| pf_debt_3m  |  21 | 2016-26  |        96 |        48 |        57.3 |        52.1 |          62.5 |   -5.2 |     -15.7 |       4.8 |         0.84 |
| pf_debt_3m  |  42 | 2010-26  |        89 |        45 |        60.7 |        64.4 |          56.8 |    3.8 |      -6.2 |      14.3 |         0.23 |
| pf_debt_3m  |  42 | 2016-26  |        56 |        29 |        58.9 |        62.1 |          55.6 |    3.1 |      -8.9 |      15.8 |         0.32 |
| basic_12m   |  21 | 2010-26  |       156 |        78 |        59   |        51.3 |          66.7 |   -7.7 |     -15.5 |       0.2 |         0.97 |
| basic_12m   |  21 | 2016-26  |        96 |        56 |        57.3 |        55.4 |          60   |   -1.9 |     -10.4 |       6.6 |         0.67 |
| basic_12m   |  42 | 2010-26  |        89 |        45 |        60.7 |        64.4 |          56.8 |    3.8 |      -6.1 |      14.2 |         0.22 |
| basic_12m   |  42 | 2016-26  |        56 |        32 |        58.9 |        68.8 |          45.8 |    9.8 |      -1.3 |      21.8 |         0.05 |
| tic_net_3m  |  21 | 2010-26  |       156 |        80 |        59   |        60   |          57.9 |    1   |      -6.4 |       8.6 |         0.38 |
| tic_net_3m  |  21 | 2016-26  |        96 |        50 |        57.3 |        56   |          58.7 |   -1.3 |     -11.1 |       8.3 |         0.6  |
| tic_net_3m  |  42 | 2010-26  |        89 |        44 |        60.7 |        59.1 |          62.2 |   -1.6 |     -11.8 |       8.3 |         0.62 |
| tic_net_3m  |  42 | 2016-26  |        56 |        28 |        58.9 |        53.6 |          64.3 |   -5.4 |     -19   |       8   |         0.8  |
| spf_contra  |  21 | 2010-26  |       156 |        74 |        59   |        54.1 |          63.4 |   -4.9 |     -13.2 |       3.5 |         0.88 |
| spf_contra  |  21 | 2016-26  |        96 |        47 |        57.3 |        57.4 |          57.1 |    0.2 |     -10.3 |      10.3 |         0.5  |
| spf_contra  |  42 | 2010-26  |        89 |        41 |        60.7 |        63.4 |          58.3 |    2.7 |      -8.4 |      13.6 |         0.31 |
| spf_contra  |  42 | 2016-26  |        56 |        28 |        58.9 |        67.9 |          50   |    8.9 |      -4.1 |      22.6 |         0.1  |

## 7. Selection and the success bar

Declared rule: highest lower Wilson bound of the 2010-15 non-overlapping 21-session accuracy of the extra-vote rule among candidates with >= 6 such decisions a year. Result: **`pf_net_d3m`** (selected by the declared rule).

| candidate   |   n |   dec_per_year |   accuracy |   lo |   hi |   agree_accuracy |   agree_dec_per_year |   gain_pts | eligible   | final   |
|:------------|----:|---------------:|-----------:|-----:|-----:|-----------------:|---------------------:|-----------:|:-----------|:--------|
| tic_net_3m  |  32 |           5.34 |       62.5 | 45.3 | 77.1 |             61.7 |                10.02 |       0.83 | False      | False   |
| cust_d13w   |  26 |           4.34 |       61.5 | 42.5 | 77.6 |             61.7 |                10.02 |      -0.13 | False      | False   |
| pf_debt_3m  |  32 |           5.34 |       59.4 | 42.3 | 74.5 |             61.7 |                10.02 |      -2.29 | False      | False   |
| pf_net_3m   |  34 |           5.68 |       55.9 | 39.5 | 71.1 |             61.7 |                10.02 |      -5.78 | False      | False   |
| pf_net_d3m  |  44 |           7.35 |       52.3 | 37.9 | 66.2 |             61.7 |                10.02 |      -9.39 | True       | True    |
| cust_d4w    |  37 |           6.18 |       48.6 | 33.4 | 64.1 |             61.7 |                10.02 |     -13.02 | True       | False   |
| pf_net_6m   |  28 |           4.68 |       50   | 32.6 | 67.4 |             61.7 |                10.02 |     -11.67 | False      | False   |
| repo_d13w   |  42 |           7.01 |       45.2 | 31.2 | 60.1 |             61.7 |                10.02 |     -16.43 | True       | False   |
| pf_eq_3m    |  32 |           5.34 |       46.9 | 30.9 | 63.6 |             61.7 |                10.02 |     -14.79 | False      | False   |
| swap_use    |  16 |           2.67 |       43.8 | 23.1 | 66.8 |             61.7 |                10.02 |     -17.92 | False      | False   |
| spf_contra  |  30 |           5.01 |       36.7 | 21.9 | 54.5 |             61.7 |                10.02 |     -25    | False      | False   |
| basic_12m   |  24 |           4.01 |       37.5 | 21.2 | 57.3 |             61.7 |                10.02 |     -24.17 | False      | False   |

The bar for `pf_net_d3m` (non-overlapping decisions; accuracies in %, gains in points):

|   h | period   |   agree_acc |   agree_n |   agree_per_year |   extra_acc |   extra_lo |   extra_hi |   extra_n |   extra_per_year |   gain_pts |   placebo63_gain_pts |   placebo63_n |   placebo126_gain_pts |   placebo126_n |
|----:|:---------|------------:|----------:|-----------------:|------------:|-----------:|-----------:|----------:|-----------------:|-----------:|---------------------:|--------------:|----------------------:|---------------:|
|  21 | 2010-26  |        59   |       156 |              9.3 |        54.7 |       44.7 |       64.4 |        95 |              5.7 |       -4.2 |                 -6   |            85 |                  -7.4 |             93 |
|  21 | 2016-26  |        57.3 |        96 |              8.9 |        56.9 |       43.3 |       69.5 |        51 |              4.7 |       -0.4 |                 -4.2 |            49 |                  -5.6 |             58 |
|  21 | 2023-26  |        60   |        35 |              9.3 |        50   |       29.9 |       70.1 |        20 |              5.3 |      -10   |                  2.5 |            16 |                 -22.5 |             24 |
|  42 | 2010-26  |        60.7 |        89 |              5.3 |        57.4 |       44.9 |       69   |        61 |              3.7 |       -3.3 |                 -4.2 |            62 |                  -4.2 |             62 |
|  42 | 2016-26  |        58.9 |        56 |              5.2 |        52.9 |       36.7 |       68.5 |        34 |              3.2 |       -6   |                 -6.2 |            36 |                  -3.9 |             40 |
|  42 | 2023-26  |        45   |        20 |              5.4 |        50   |       25.4 |       74.6 |        12 |              3.3 |        5   |                  9.5 |            11 |                  -1.3 |             16 |
|  63 | 2010-26  |        72.1 |        61 |              3.7 |        64.6 |       50.4 |       76.6 |        48 |              2.9 |       -7.5 |                 -2.6 |            46 |                 -10.8 |             44 |
|  63 | 2016-26  |        71.1 |        38 |              3.6 |        59.3 |       40.7 |       75.5 |        27 |              2.5 |      -11.8 |                 -0.7 |            27 |                 -11.8 |             27 |
|  63 | 2023-26  |        50   |        14 |              3.9 |        50   |       23.7 |       76.3 |        10 |              2.8 |        0   |                 27.8 |             9 |                   5.6 |              9 |

* gain>=3 at 21 and 42, 2010-26: **NO**
* gain>=3 at 21 and 42, 2016-26: **NO**
* >=6 decisions/yr (21-session non-overlapping), 2010-26 and 2016-26: **NO**
* 2023-26 not worse at 21 and 42: **NO**
* placebo (+63 and +126) loses >= half of the gain at 21 and 42, 2010-26: **NO**
* BAR MET: **NO**

The same bar for every candidate (information only; gains in points, non-overlapping):

| candidate   |   gain21_2010 |   gain42_2010 |   gain21_2016 |   gain42_2016 |   gain21_2023 |   gain42_2023 |   per_year_21_2010 |   placebo63_gain21 |   placebo126_gain21 |   placebo63_gain42 |   placebo126_gain42 | BAR MET   |
|:------------|--------------:|--------------:|--------------:|--------------:|--------------:|--------------:|-------------------:|-------------------:|--------------------:|-------------------:|--------------------:|:----------|
| cust_d4w    |          -0.8 |           3.9 |           6.6 |          -0.4 |           2.5 |          21.7 |                5.8 |               -5   |                -8   |               -5.5 |                -2.2 | False     |
| cust_d13w   |          -0.3 |           4   |          -0.1 |          -0.1 |           3.2 |           8.8 |                4.5 |              -10.1 |                -2.2 |               -7.3 |                 0.7 | False     |
| swap_use    |          -3.8 |          12.1 |          11.9 |          22.9 |         -10   |           5   |                1.7 |               -4.1 |               -17.6 |                6   |                -1.6 | False     |
| repo_d13w   |          -5.6 |           4   |           1.4 |           3.6 |          -0.7 |           5   |                6.3 |               -3.1 |                -6   |                0.5 |                 2.4 | False     |
| pf_net_3m   |          -3.6 |          -4.5 |          -2.2 |          -1.4 |         -13.3 |          -8.6 |                5   |              -11.4 |                -3.5 |               -2.8 |                 0   | False     |
| pf_net_6m   |          -9.7 |          -8.5 |          -8.5 |          -3.4 |         -26.7 |         -28.3 |                4.2 |               -7.8 |                -1.1 |                1.8 |                 7.2 | False     |
| pf_net_d3m  |          -4.2 |          -3.3 |          -0.4 |          -6   |         -10   |           5   |                5.7 |               -6   |                -7.4 |               -4.2 |                -4.2 | False     |
| pf_eq_3m    |          -6.5 |          -7   |          -1.3 |          -2.7 |         -18.8 |           0.5 |                4.9 |              -10.2 |                -9.5 |               -7.1 |                 1.2 | False     |
| pf_debt_3m  |          -3.8 |          -3.8 |          -4.6 |          -4.9 |         -10   |         -11.7 |                5.2 |               -9   |                -3.8 |                2   |                 3.5 | False     |
| basic_12m   |         -10.2 |           2.1 |          -4   |           5   |          10.6 |           5   |                5   |               -6.6 |                -3.3 |                6   |                11.3 | False     |
| tic_net_3m  |          -0.5 |           1   |          -1.2 |           0   |          -5   |           1.2 |                5.3 |               -2.9 |                -7.4 |                0.6 |                 4.9 | False     |
| spf_contra  |          -9   |           8.1 |           0.7 |          11.1 |          -5.5 |          13.3 |                4.8 |               -7.1 |                -2.8 |                6.7 |                 9.1 | False     |

Decisions of `pf_net_d3m` (extra-vote rule, weekly, 21-session hold) by year:

|   year |   decisions |   long_share |   accuracy |   net_win_rate |   net_bp |
|-------:|------------:|-------------:|-----------:|---------------:|---------:|
|   2010 |          28 |         0.32 |       0.68 |           0.64 |   139.52 |
|   2011 |          18 |         0.33 |       0.61 |           0.61 |    54.86 |
|   2012 |          26 |         0.31 |       0.62 |           0.62 |    15.8  |
|   2013 |           3 |         1    |       0    |           0    |  -199.82 |
|   2014 |          13 |         0.23 |       0.69 |           0.69 |    86.54 |
|   2015 |           7 |         0.14 |       0.71 |           0.71 |   292.29 |
|   2016 |           7 |         0.71 |       0.71 |           0.71 |    38.16 |
|   2017 |          10 |         1    |       0.7  |           0.7  |    81.15 |
|   2018 |           8 |         0    |       0.62 |           0.62 |    76.94 |
|   2019 |           6 |         0.83 |       0.5  |           0.5  |   -19.08 |
|   2020 |          11 |         1    |       0.73 |           0.73 |   128.89 |
|   2021 |          10 |         0    |       0.3  |           0.3  |   -12.9  |
|   2022 |          15 |         0.6  |       0.73 |           0.73 |    81.28 |
|   2023 |           9 |         0.67 |       0.11 |           0.11 |  -137.46 |
|   2024 |           9 |         0.33 |       0.22 |           0.22 |   -47.34 |
|   2025 |           4 |         1    |       1    |           1    |    85.35 |
|   2026 |          10 |         0.3  |       0.7  |           0.7  |     0.31 |

Hit rates of the final rule at 21 sessions (round-4 format: share with the correct sign before costs, share with positive net P&L):

| mode       | period   |   n |   dec_per_year |   right_sign_% |   net_win_% |   gross_bp |   net_bp |   share_long |   chance_acc |
|:-----------|:---------|----:|---------------:|---------------:|------------:|-----------:|---------:|-------------:|-------------:|
| weekly     | 2010-26  | 194 |          11.59 |           59.8 |        59.3 |      56.86 |    54.87 |         0.44 |          0.5 |
| weekly     | 2016-26  |  99 |           9.22 |           56.6 |        56.6 |      30.12 |    27.97 |         0.57 |          0.5 |
| weekly     | 2023-26  |  32 |           8.56 |           43.8 |        43.8 |     -39.06 |   -41.21 |         0.5  |          0.5 |
| nonoverlap | 2010-26  |  95 |           5.67 |           54.7 |        54.7 |      58.85 |    56.84 |         0.49 |          0.5 |
| nonoverlap | 2016-26  |  51 |           4.74 |           56.9 |        56.9 |      29.97 |    27.8  |         0.59 |          0.5 |
| nonoverlap | 2023-26  |  20 |           5.31 |           50   |        50   |     -30.85 |   -33.04 |         0.45 |          0.5 |

## 8. Timing placebo (the vote made 63 and 126 sessions staler), extra-vote rule, non-overlapping


Placebo +63 sessions (% right, decisions, per year):

| candidate   | 2010-26 / 21s    | 2010-26 / 42s   | 2010-26 / 63s   | 2016-26 / 21s   | 2016-26 / 42s   | 2016-26 / 63s   | 2023-26 / 21s   | 2023-26 / 42s   | 2023-26 / 63s   |
|:------------|:-----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|
| cust_d4w    | 54 n=100 (6.0/y) | 55 n=67 (4.0/y) | 60 n=52 (3.1/y) | 58 n=65 (6.0/y) | 58 n=43 (4.0/y) | 56 n=34 (3.2/y) | 52 n=27 (7.2/y) | 53 n=17 (4.6/y) | 46 n=13 (3.6/y) |
| cust_d13w   | 49 n=88 (5.3/y)  | 53 n=60 (3.6/y) | 60 n=43 (2.6/y) | 51 n=59 (5.5/y) | 54 n=39 (3.7/y) | 64 n=28 (2.6/y) | 48 n=21 (5.6/y) | 38 n=13 (3.5/y) | 50 n=10 (2.8/y) |
| swap_use    | 55 n=31 (1.8/y)  | 67 n=24 (1.4/y) | 84 n=19 (1.1/y) | 62 n=16 (1.5/y) | 57 n=14 (1.3/y) | 73 n=11 (1.0/y) | 100 n=1 (0.3/y) | 0 n=1 (0.3/y)   | 100 n=1 (0.3/y) |
| repo_d13w   | 56 n=102 (6.1/y) | 61 n=67 (4.0/y) | 72 n=47 (2.8/y) | 59 n=61 (5.7/y) | 60 n=40 (3.7/y) | 78 n=27 (2.5/y) | 73 n=22 (5.8/y) | 62 n=13 (3.5/y) | 70 n=10 (2.8/y) |
| pf_net_3m   | 48 n=82 (4.9/y)  | 58 n=57 (3.4/y) | 75 n=40 (2.4/y) | 51 n=47 (4.4/y) | 59 n=32 (3.0/y) | 74 n=23 (2.2/y) | 44 n=9 (2.4/y)  | 67 n=6 (1.6/y)  | 83 n=6 (1.7/y)  |
| pf_net_6m   | 51 n=86 (5.1/y)  | 62 n=56 (3.4/y) | 71 n=41 (2.5/y) | 51 n=57 (5.3/y) | 60 n=35 (3.3/y) | 72 n=25 (2.4/y) | 54 n=13 (3.5/y) | 50 n=10 (2.7/y) | 67 n=9 (2.5/y)  |
| pf_net_d3m  | 53 n=85 (5.1/y)  | 56 n=62 (3.7/y) | 70 n=46 (2.8/y) | 53 n=49 (4.6/y) | 53 n=36 (3.4/y) | 70 n=27 (2.5/y) | 62 n=16 (4.3/y) | 55 n=11 (3.0/y) | 78 n=9 (2.5/y)  |
| pf_eq_3m    | 49 n=82 (4.9/y)  | 54 n=56 (3.4/y) | 59 n=41 (2.5/y) | 48 n=56 (5.2/y) | 51 n=39 (3.7/y) | 59 n=27 (2.5/y) | 68 n=19 (5.0/y) | 57 n=14 (3.8/y) | 62 n=8 (2.2/y)  |
| pf_debt_3m  | 50 n=88 (5.3/y)  | 63 n=59 (3.5/y) | 81 n=42 (2.5/y) | 56 n=50 (4.6/y) | 70 n=33 (3.1/y) | 88 n=24 (2.3/y) | 40 n=10 (2.7/y) | 50 n=8 (2.2/y)  | 83 n=6 (1.7/y)  |
| basic_12m   | 52 n=86 (5.1/y)  | 67 n=51 (3.1/y) | 68 n=40 (2.4/y) | 55 n=58 (5.4/y) | 68 n=34 (3.2/y) | 73 n=26 (2.5/y) | 67 n=15 (4.0/y) | 50 n=10 (2.7/y) | 56 n=9 (2.5/y)  |
| tic_net_3m  | 56 n=98 (5.8/y)  | 61 n=62 (3.7/y) | 67 n=48 (2.9/y) | 52 n=62 (5.8/y) | 58 n=38 (3.6/y) | 60 n=30 (2.8/y) | 52 n=21 (5.6/y) | 55 n=11 (3.0/y) | 40 n=10 (2.8/y) |
| spf_contra  | 52 n=81 (4.8/y)  | 67 n=49 (2.9/y) | 70 n=37 (2.2/y) | 59 n=54 (5.0/y) | 67 n=33 (3.1/y) | 79 n=24 (2.3/y) | 55 n=22 (5.8/y) | 54 n=13 (3.5/y) | 67 n=9 (2.5/y)  |

Gain over the agreement rule with the +63 placebo (points):

| candidate   |   2010-26 / 21s |   2010-26 / 42s |   2010-26 / 63s |   2016-26 / 21s |   2016-26 / 42s |   2016-26 / 63s |   2023-26 / 21s |   2023-26 / 42s |   2023-26 / 63s |
|:------------|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|
| cust_d4w    |            -5   |            -5.5 |           -12.5 |             1.2 |            -0.8 |           -15.2 |            -8.1 |             7.9 |            -3.8 |
| cust_d13w   |           -10.1 |            -7.3 |           -11.7 |            -6.4 |            -5.1 |            -6.8 |           -12.4 |            -6.5 |             0   |
| swap_use    |            -4.1 |             6   |            12.1 |             5.2 |            -1.8 |             1.7 |            40   |           -45   |            50   |
| repo_d13w   |            -3.1 |             0.5 |             0.2 |             1.7 |             1.1 |             6.7 |            12.7 |            16.5 |            20   |
| pf_net_3m   |           -11.4 |            -2.8 |             2.9 |            -6.2 |             0.4 |             2.9 |           -15.6 |            21.7 |            33.3 |
| pf_net_6m   |            -7.8 |             1.8 |            -1.4 |            -6.4 |             1.1 |             0.9 |            -6.2 |             5   |            16.7 |
| pf_net_d3m  |            -6   |            -4.2 |            -2.6 |            -4.2 |            -6.2 |            -0.7 |             2.5 |             9.5 |            27.8 |
| pf_eq_3m    |           -10.2 |            -7.1 |           -13.6 |            -9.1 |            -7.6 |           -11.8 |             8.4 |            12.1 |            12.5 |
| pf_debt_3m  |            -9   |             2   |             8.8 |            -1.3 |            10.8 |            16.4 |           -20   |             5   |            33.3 |
| basic_12m   |            -6.6 |             6   |            -4.6 |            -2.1 |             8.7 |             2   |             6.7 |             5   |             5.6 |
| tic_net_3m  |            -2.9 |             0.6 |            -5.5 |            -5.7 |            -1   |           -11.1 |            -7.6 |             9.5 |           -10   |
| spf_contra  |            -7.1 |             6.7 |            -1.9 |             2   |             7.7 |             8.1 |            -5.5 |             8.8 |            16.7 |

Placebo +126 sessions (% right, decisions, per year):

| candidate   | 2010-26 / 21s    | 2010-26 / 42s   | 2010-26 / 63s   | 2016-26 / 21s   | 2016-26 / 42s   | 2016-26 / 63s   | 2023-26 / 21s   | 2023-26 / 42s   | 2023-26 / 63s   |
|:------------|:-----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|
| cust_d4w    | 51 n=98 (5.8/y)  | 58 n=65 (3.9/y) | 63 n=49 (3.0/y) | 53 n=62 (5.8/y) | 54 n=41 (3.8/y) | 65 n=31 (2.9/y) | 45 n=22 (5.8/y) | 46 n=13 (3.5/y) | 45 n=11 (3.1/y) |
| cust_d13w   | 57 n=88 (5.3/y)  | 61 n=57 (3.4/y) | 67 n=42 (2.5/y) | 56 n=59 (5.5/y) | 58 n=38 (3.6/y) | 66 n=29 (2.7/y) | 57 n=21 (5.6/y) | 64 n=11 (3.0/y) | 50 n=10 (2.8/y) |
| swap_use    | 41 n=29 (1.7/y)  | 59 n=22 (1.3/y) | 71 n=17 (1.0/y) | 50 n=12 (1.1/y) | 50 n=10 (0.9/y) | 67 n=9 (0.8/y)  | 0 n=1 (0.3/y)   | 0 n=1 (0.3/y)   | 0 n=1 (0.3/y)   |
| repo_d13w   | 53 n=102 (6.1/y) | 63 n=65 (3.9/y) | 77 n=48 (2.9/y) | 57 n=61 (5.7/y) | 61 n=41 (3.8/y) | 76 n=29 (2.7/y) | 58 n=26 (6.9/y) | 50 n=16 (4.3/y) | 55 n=11 (3.1/y) |
| pf_net_3m   | 55 n=92 (5.5/y)  | 61 n=56 (3.4/y) | 68 n=40 (2.4/y) | 57 n=56 (5.2/y) | 63 n=35 (3.3/y) | 67 n=24 (2.3/y) | 56 n=18 (4.8/y) | 42 n=12 (3.3/y) | 56 n=9 (2.5/y)  |
| pf_net_6m   | 58 n=95 (5.7/y)  | 68 n=56 (3.4/y) | 79 n=43 (2.6/y) | 55 n=60 (5.6/y) | 71 n=35 (3.3/y) | 81 n=26 (2.5/y) | 62 n=16 (4.3/y) | 70 n=10 (2.7/y) | 78 n=9 (2.5/y)  |
| pf_net_d3m  | 52 n=93 (5.5/y)  | 56 n=62 (3.7/y) | 61 n=44 (2.7/y) | 52 n=58 (5.4/y) | 55 n=40 (3.7/y) | 59 n=27 (2.5/y) | 38 n=24 (6.4/y) | 44 n=16 (4.3/y) | 56 n=9 (2.5/y)  |
| pf_eq_3m    | 49 n=97 (5.8/y)  | 62 n=63 (3.8/y) | 62 n=48 (2.9/y) | 51 n=67 (6.2/y) | 68 n=44 (4.1/y) | 64 n=33 (3.1/y) | 50 n=28 (7.4/y) | 62 n=16 (4.3/y) | 46 n=13 (3.6/y) |
| pf_debt_3m  | 55 n=87 (5.2/y)  | 64 n=53 (3.2/y) | 76 n=42 (2.5/y) | 59 n=51 (4.7/y) | 66 n=32 (3.0/y) | 77 n=26 (2.5/y) | 57 n=14 (3.7/y) | 50 n=10 (2.7/y) | 62 n=8 (2.2/y)  |
| basic_12m   | 56 n=88 (5.3/y)  | 72 n=50 (3.0/y) | 71 n=38 (2.3/y) | 61 n=56 (5.2/y) | 71 n=31 (2.9/y) | 71 n=24 (2.3/y) | 79 n=14 (3.7/y) | 62 n=8 (2.2/y)  | 57 n=7 (1.9/y)  |
| tic_net_3m  | 52 n=93 (5.5/y)  | 66 n=61 (3.7/y) | 71 n=45 (2.7/y) | 48 n=60 (5.6/y) | 70 n=40 (3.7/y) | 72 n=29 (2.7/y) | 40 n=20 (5.3/y) | 50 n=12 (3.3/y) | 56 n=9 (2.5/y)  |
| spf_contra  | 56 n=89 (5.3/y)  | 70 n=53 (3.2/y) | 74 n=38 (2.3/y) | 60 n=60 (5.6/y) | 72 n=36 (3.4/y) | 76 n=25 (2.4/y) | 48 n=23 (6.1/y) | 54 n=13 (3.5/y) | 56 n=9 (2.5/y)  |

Gain over the agreement rule with the +126 placebo (points):

| candidate   |   2010-26 / 21s |   2010-26 / 42s |   2010-26 / 63s |   2016-26 / 21s |   2016-26 / 42s |   2016-26 / 63s |   2023-26 / 21s |   2023-26 / 42s |   2023-26 / 63s |
|:------------|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|
| cust_d4w    |            -8   |            -2.2 |            -8.9 |            -4.1 |            -5.3 |            -6.5 |           -14.5 |             1.2 |            -4.5 |
| cust_d13w   |            -2.2 |             0.7 |            -5.5 |            -1.4 |            -1   |            -5.5 |            -2.9 |            18.6 |             0   |
| swap_use    |           -17.6 |            -1.6 |            -1.5 |            -7.3 |            -8.9 |            -4.4 |           -60   |           -45   |           -50   |
| repo_d13w   |            -6   |             2.4 |             5   |             0.1 |             2   |             4.8 |            -2.3 |             5   |             4.5 |
| pf_net_3m   |            -3.5 |             0   |            -4.6 |            -0.1 |             3.9 |            -4.4 |            -4.4 |            -3.3 |             5.6 |
| pf_net_6m   |            -1.1 |             7.2 |             6.9 |            -2.3 |            12.5 |             9.7 |             2.5 |            25   |            27.8 |
| pf_net_d3m  |            -7.4 |            -4.2 |           -10.8 |            -5.6 |            -3.9 |           -11.8 |           -22.5 |            -1.3 |             5.6 |
| pf_eq_3m    |            -9.5 |             1.2 |            -9.6 |            -6.5 |             9.3 |            -7.4 |           -10   |            17.5 |            -3.8 |
| pf_debt_3m  |            -3.8 |             3.5 |             4.1 |             1.5 |             6.7 |             5.9 |            -2.9 |             5   |            12.5 |
| basic_12m   |            -3.3 |            11.3 |            -1.1 |             3.4 |            12   |            -0.2 |            18.6 |            17.5 |             7.1 |
| tic_net_3m  |            -7.4 |             4.9 |            -1   |            -9   |            11.1 |             1.4 |           -20   |             5   |             5.6 |
| spf_contra  |            -2.8 |             9.1 |             1.6 |             2.7 |            13.3 |             4.9 |           -12.2 |             8.8 |             5.6 |

## 9. Daily-stream incremental test (round-3 addendum) and protocol table

Net Sharpe at 1.2 pips of the weekly-tranche 21-session book of each extra-vote rule (the agreement rule's own book first):

| variant                       |   2010-2026 |   2016-2026 |   2023-2026 |   2010-2015 |   t 2010-2026 |
|:------------------------------|------------:|------------:|------------:|------------:|--------------:|
| agree3_baseline               |        0.52 |        0.51 |        0.43 |        0.56 |          2.17 |
| extra_vote_cust_d4w           |        0.49 |        0.46 |        0.69 |        0.53 |          2.02 |
| extra_vote_cust_d13w          |        0.23 |        0.18 |        0.39 |        0.3  |          0.94 |
| extra_vote_swap_use           |        0.1  |        0.56 |        0.18 |       -0.13 |          0.4  |
| extra_vote_repo_d13w          |        0.32 |        0.37 |        0.54 |        0.29 |          1.33 |
| extra_vote_pf_net_3m          |        0.25 |        0.2  |       -0.04 |        0.31 |          1.03 |
| extra_vote_pf_net_6m          |        0.25 |        0.34 |        0.35 |        0.14 |          1.03 |
| extra_vote_pf_net_d3m         |        0.45 |        0.26 |       -0.22 |        0.67 |          1.87 |
| extra_vote_pf_eq_3m           |        0.13 |        0.32 |        0.44 |       -0.04 |          0.56 |
| extra_vote_pf_debt_3m         |        0.32 |        0.35 |       -0.16 |        0.28 |          1.33 |
| extra_vote_basic_12m          |        0.16 |        0.37 |       -0.02 |       -0.28 |          0.68 |
| extra_vote_tic_net_3m         |        0.34 |        0.34 |        0.43 |        0.34 |          1.4  |
| extra_vote_spf_contra         |        0.2  |        0.51 |        0.64 |       -0.27 |          0.85 |
| extra_vote_pf_net_d3m_cost0.6 |        0.46 |        0.27 |       -0.21 |        0.68 |          1.9  |

Final book `extra_vote_pf_net_d3m` per year (deflated-Sharpe p for 12 candidates: 0.42):

| period    |    n |   sharpe |     t |   mean_bp |   sum_bp |   active_frac |
|:----------|-----:|---------:|------:|----------:|---------:|--------------:|
| 2010      |  260 |     1.25 |  1.27 |      3    |   781.26 |          0.82 |
| 2011      |  260 |     0.46 |  0.46 |      0.73 |   188.76 |          0.7  |
| 2012      |  260 |     0.19 |  0.19 |      0.35 |    90.96 |          0.88 |
| 2013      |  259 |    -1.28 | -1.3  |     -0.46 |  -119.9  |          0.18 |
| 2014      |  258 |     1.36 |  1.37 |      0.87 |   224.97 |          0.54 |
| 2015      |  259 |     1.33 |  1.35 |      1.58 |   409.15 |          0.38 |
| 2016      |  259 |     0.39 |  0.39 |      0.32 |    82.7  |          0.25 |
| 2017      |  259 |     0.68 |  0.69 |      0.51 |   133.04 |          0.51 |
| 2018      |  260 |     0.66 |  0.67 |      0.47 |   123.08 |          0.28 |
| 2019      |  260 |    -0.07 | -0.07 |     -0.02 |    -6.39 |          0.27 |
| 2020      |  260 |     1.6  |  1.62 |      1.19 |   309.04 |          0.41 |
| 2021      |  259 |    -0.33 | -0.33 |     -0.26 |   -67.78 |          0.37 |
| 2022      |  260 |     0.53 |  0.54 |      0.55 |   143.26 |          0.43 |
| 2023      |  258 |    -0.5  | -0.5  |     -0.52 |  -134.95 |          0.33 |
| 2024      |  261 |    -0.63 | -0.64 |     -0.34 |   -88.64 |          0.46 |
| 2025      |  260 |     0.53 |  0.54 |      0.23 |    59.77 |          0.2  |
| 2026      |  220 |     0    |  0    |      0    |     0.58 |          0.39 |
| 2010-2026 | 4372 |     0.45 |  1.87 |      0.49 |  2128.92 |          0.44 |
| 2016-2026 | 2816 |     0.26 |  0.87 |      0.2  |   553.72 |          0.35 |
| 2023-2026 |  999 |    -0.22 | -0.45 |     -0.16 |  -163.24 |          0.34 |
| 2010-2015 | 1556 |     0.67 |  1.66 |      1.01 |  1575.2  |          0.58 |
| 2016-2022 | 1817 |     0.51 |  1.38 |      0.39 |   716.95 |          0.36 |

Combination test, `meta.combine(..., 'EW')`:

| combo                     | period    |   sharpe |     t |   mean_bp |
|:--------------------------|:----------|---------:|------:|----------:|
| weak_signals+regime_trend | 2010-2026 |    0.563 | 2.347 |     0.583 |
| weak_signals+regime_trend | 2016-2026 |    0.636 | 2.128 |     0.738 |
| weak_signals+regime_trend | 2023-2026 |    0.356 | 0.708 |     0.42  |
| +official_flows           | 2010-2026 |    0.562 | 2.34  |     0.477 |
| +official_flows           | 2016-2026 |    0.589 | 1.97  |     0.568 |
| +official_flows           | 2023-2026 |    0.209 | 0.416 |     0.208 |

Daily P&L correlation of the final book, 2010-26: `weak_signals` 0.30, `regime_trend` 0.46, agreement-rule book (`selective_daily`) 0.77.

## 10. Leak checks

No model is fitted in this arm (fixed sign rules; trailing statistics use observations stamped up to each observation's own stamp; the house score inside the agreement rule is the selective arm's walk-forward fit; the orthogonalisation slopes come from earlier years only).

Non-overlapping accuracy, 2010-26 (% right, decisions), agreement rule and the final `pf_net_d3m`:

| check                            | agree3:agree3 21s   | agree3:agree3 42s   | extra_vote:pf_net_d3m 21s   | extra_vote:pf_net_d3m 42s   | standalone:pf_net_d3m 21s   | standalone:pf_net_d3m 42s   |
|:---------------------------------|:--------------------|:--------------------|:----------------------------|:----------------------------|:----------------------------|:----------------------------|
| baseline                         | 59 n=156            | 61 n=89             | 55 n=95                     | 57 n=61                     | 51 n=208                    | 48 n=104                    |
| lookahead_control_minus21        | 59 n=156            | 61 n=89             | 60 n=96                     | 68 n=65                     | 53 n=208                    | 49 n=104                    |
| lookahead_control_minus63        | 59 n=156            | 61 n=89             | 66 n=90                     | 73 n=60                     | 57 n=206                    | 54 n=103                    |
| positive_control_planted_label21 | 59 n=156            | 61 n=89             | 100 n=122                   | 82 n=72                     | 100 n=208                   | 81 n=104                    |
| shuffled_labels_0                | 48 n=143            | 59 n=85             | 49 n=87                     | 48 n=58                     | 51 n=209                    | 45 n=105                    |
| shuffled_labels_1                | 54 n=118            | 54 n=70             | 52 n=67                     | 48 n=46                     | 47 n=209                    | 44 n=105                    |
| shuffled_labels_2                | 52 n=106            | 51 n=65             | 61 n=66                     | 50 n=44                     | 48 n=209                    | 45 n=105                    |
| vote_stale_plus1                 | 59 n=156            | 61 n=89             | 54 n=94                     | 59 n=61                     | 51 n=208                    | 48 n=104                    |
| vote_stale_plus21                | 59 n=156            | 61 n=89             | 48 n=89                     | 56 n=62                     | 48 n=208                    | 48 n=104                    |
| vote_stale_plus5                 | 59 n=156            | 61 n=89             | 55 n=92                     | 59 n=61                     | 50 n=208                    | 50 n=104                    |

Range over the 12 candidates of the standalone 21-session non-overlapping accuracy, 2010-26, per check (min / median / max, %):

| check                            |   min |   median |   max |
|:---------------------------------|------:|---------:|------:|
| baseline                         |    45 |       47 |    51 |
| lookahead_control_minus21        |    41 |       47 |    59 |
| lookahead_control_minus63        |    38 |       53 |    63 |
| positive_control_planted_label21 |   100 |      100 |   100 |
| shuffled_labels_0                |    45 |       50 |    56 |
| shuffled_labels_1                |    44 |       49 |    56 |
| shuffled_labels_2                |    44 |       51 |    58 |
| vote_stale_plus1                 |    45 |       47 |    51 |
| vote_stale_plus21                |    45 |       47 |    52 |
| vote_stale_plus5                 |    46 |       48 |    53 |

* (1) Shuffled labels (targets and the 1-session return the house weights are fitted on, three permutations): standalone 41-58 % over the 12 votes and both horizons, mean 50 %.
* (2) Votes made staler by 1 / 5 / 21 sessions: 41-64 % over both horizons, 45-53 % at 21 sessions (nothing to collapse). A planted label (vote = sign of the next 21 sessions' return) scores 100 %, so the harness does expose a look-ahead. Votes taken from 21 / 63 sessions in the FUTURE: 39-59 % / 38-63 % standalone. The four euro-area 3-month portfolio votes do improve when taken from 63 sessions ahead (as extra votes 60-66 % at 21 and 63-73 % at 42 sessions, against 52-55 % and 54-57 % live): with a 60-day lag that is the flow of the very months in which the return is earned. Together with the zero-lag control (section 5e, 42-56 %) it says the flows move WITH the exchange rate and do not precede it.
* Lag audit: section 1; every observation is at least as old as the stated lag at the session close that uses it.
* Label in disguise: none of the signals uses EUR/USD prices except `spf_contra`, whose two legs are forecasts of the same survey round; correlations with the forward return are in section 5a.

## 11. Variant count

12 candidate votes, each evaluated standalone, as an extra vote and with two placebos; no parameter searched. Controls that are not candidates and from which nothing is selected: two orthogonalised versions of each vote, the native-frequency lead-lag table, the vintage comparison, the replication of the five dollar-side votes on the non-euro basket. One selection (the declared rule). For deflation: 12.

