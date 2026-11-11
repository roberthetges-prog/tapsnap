# Arm Q: relative central-bank liquidity and financial stress as an extra vote (`liquidity_stress`)

Code `src/eurusd/arms/liquidity_stress.py` (`run(cost_pips=1.2)`, `fetch_data()` cached, `leak_checks()`, `incremental()`; `python -m eurusd.arms.liquidity_stress` reproduces everything in under a minute). Results in `experiments/results/arms/`: `liquidity_stress_positions.parquet` (daily weekly-tranche book of the final extra-vote rule: `pos`, `fwd_bp`, `net_bp`), `liquidity_stress_decisions.parquet` (its weekly decisions), `liquidity_stress_report.csv` (protocol table of all 12 extra-vote books, the agreement-rule baseline and the 0.6-pip run; `variant`, `final`), `liquidity_stress_votes.csv` (agreement rule, extra vote, calls outside agreement, placebos, paired differences), `liquidity_stress_standalone.csv`, `liquidity_stress_reconciliation.csv`, `liquidity_stress_selection.csv`, `liquidity_stress_bar.csv`, `liquidity_stress_incremental.csv`, `liquidity_stress_leakchecks.csv`, `liquidity_stress_vote_anatomy.csv`. Aligned panel: `data/processed/cross/liquidity_stress_panel.parquet`.

Data, lags, sign priors, the 12 candidates, the selection rule and the reading of the success bar are in the module docstring and were written before the first result. Nothing was changed afterwards except one addition, marked as such: a planted-label positive control in the leak checks.

## Verdict (run of 2026-11-11; every number below is regenerated in the tables that follow)
**The round-5 success bar is NOT met, by any of the 12 candidates. Neither family carries usable information about
EUR/USD direction at 1-3 months, on its own or as an extra vote.**

1. **Reconciliation: exact.** The agreement rule rebuilt here matches `selective_accuracy_coverage.csv` in all 32 cells
   (4 horizons x 2 decision modes x 4 periods): non-overlapping 56 / 59 / 61 / 72 % at 10 / 21 / 42 / 63 sessions
   (n = 291 / 156 / 89 / 61) for 2010-26, 57 % at 21 sessions since 2016, 60 / 45 / 50 % (n = 35 / 20 / 14) since 2023.
2. **Standalone: nothing.** Over 2010-26 the twelve votes are right 41-57 % of the time at 21 sessions, 44-58 % at 42 and
   38-61 % at 63 on non-overlapping decisions (n = 208 / 104 / 69 for the always-on votes), and 46-52 / 45-53 / 44-55 % on
   weekly decisions. The best cells: `usfci_d3m` 57 % [50-63] at 21 sessions (n=208; weekly 52 %; it is NOT a real-time
   series and its +126-session placebo is 47 %), `ciss_diff_d3m` 54 / 52 / 61 % (weekly 52 / 52 / 51 %; the vote made 63
   sessions staler scores 60 / 53 / 55 %), `ciss_diff_d1m` 58 % at 42 sessions (weekly 52 %). The relative balance-sheet votes
   are 50 / 55-57 / 48-51 %, the money-growth gap 48 / 51 / 38 %, relative excess liquidity 49 / 49 / 42 %. The one cell whose
   interval excludes a coin on the WRONG side is the safe-haven vote `gstress_hi_rising`: 41 % [34-49] at 21 sessions (n=162;
   weekly 46 %), i.e. the "stress high and rising => dollar up" prior did not hold in 2010-26; turning it round would be a
   post-hoc choice and is not proposed.
3. **Extra vote: it lowers accuracy and cuts the sample.** Final by the declared rule = `ciss_diff_d3m` (2010-15: 60 %
   [46-73], n=45, 7.5 a year, against 62 % for the agreement rule alone - no candidate beat the agreement rule in the
   selection window). Agreement rule AND the vote, non-overlapping: **55 % (n=111, 6.6 a year) against 59 % (n=156, 9.3
   a year) at 21 sessions; 61 % (n=71, 4.3 a year) against 61 % (n=89, 5.3 a year) at 42 sessions; 67 % (n=49) against
   72 % (n=61) at 63.** Since 2016: 52 against 57 % and 60 against 59 %. Since 2023: 60 against 60 % (n=20 v 35) and
   53 against 45 % (n=15 v 20). Gain -4.0 / -0.1 points (2010-26) and -5.8 / +1.5 (2016-26) where +3 / +3 is required.
   Paired difference on the weekly grid: +0.8 points [-4.9, +6.3] at 21 sessions, +2.2 [-3.6, +8.4] at 42. On the agreement
   rule's own non-overlapping stream the decisions the vote confirms are right 53 % of the time and the ones it rejects
   65 % (21 sessions, 76 v 80 decisions).
   Across all 12 candidates the 21-session gain in 2010-26 is negative for every one (-1.3 to -12.2 points); no candidate
   has +3 at both horizons in both periods, with or without the decision-count condition.
4. **Coverage extension: no.** On sessions where the three old signals do NOT agree, the votes are right 44-51 % at 21
   sessions, 46-57 % at 42 and 44-59 % at 63 (2010-26, n = 135-170 / 82-93 / 56-64); the final vote 51 / 57 / 58 %, every
   interval including 50 %.
5. **Timing placebo: the stale vote does better than the live one.** With `ciss_diff_d3m` made 63 sessions staler the
   extra-vote rule scores 62 % / 69 % at 21 / 42 sessions (gain +2.8 / +8.3 points, against -4.0 / -0.1 live); 126 sessions
   staler 55 % / 66 % (-3.9 / +5.1). There is no gain to lose, and the spread between live and placebo (up to 8 points)
   is the size of the selection noise in these 70-110-decision subsets. Shifting the vote by ONE session moves the
   42-session accuracy from 61 to 53 %.
6. **Daily incremental test: the same stream as the agreement rule, slightly worse.** The final rule's weekly-tranche
   book has net Sharpe 0.46 / 0.51 / 0.42 (2010-26 / 2016-26 / 2023-26, 1.2 pips) against 0.52 / 0.51 / 0.43 for the
   agreement rule's own book, and is 0.82 correlated with it (0.31 with `weak_signals`, 0.51 with `regime_trend`).
   EW(weak_signals, regime_trend, this arm) = 0.559 / 0.668 / 0.410 against 0.563 / 0.636 / 0.356 two-way: +0.03 on
   2016-26 and -0.004 on 2010-26, which is the agreement rule re-entering the combination, not new information.
7. **What to keep.** Nothing for the product. The data files are clean, lagged and cached, and can serve as context
   series in the brief (balance-sheet ratio, CISS differential), not as signals.

## 1. New data: source, span, publication lag used

| file                                           | source                                                                                                                  | first      | last       |   rows | publication                                 | lag_used                         |
|:-----------------------------------------------|:------------------------------------------------------------------------------------------------------------------------|:-----------|:-----------|-------:|:--------------------------------------------|:---------------------------------|
| data/macro/liquidity_stress_ecb_ilm_weekly.csv | ECB Data Portal ILM.W.U2.C.{T000000.Z5.Z01, L020100.U2.EUR, L020200.U2.EUR, A050500.U2.EUR}                             | 1999-01-01 | 2026-11-06 |   1454 | Friday statement, published next Tuesday    | 7 calendar days                  |
| data/macro/liquidity_stress_fed_h41_weekly.csv | FRED WALCL, WRESBAL, RRPONTSYD (curl --http1.1)                                                                         | 2002-12-18 | 2026-11-04 |   1247 | Wednesday, released Thursday 16:30 ET       | 7 calendar days                  |
| data/macro/liquidity_stress_us_m2.csv          | FRED M2SL                                                                                                               | 1959-01-31 | 2026-09-30 |    813 | month m released 4th Tuesday of m+1         | 35 calendar days after month-end |
| data/macro/liquidity_stress_ea_m3.csv          | ECB Data Portal BSI.M.U2.Y.V.M30.X.{I,1}.U2.2300.Z01.{A,E}                                                              | 1980-01-31 | 2026-09-30 |    561 | month m released ~19th working day of m+1   | 35 calendar days after month-end |
| data/macro/liquidity_stress_ciss_daily.csv     | ECB Data Portal CISS.D.{U2,US}.Z0Z.4F.EC.SS_CIN.IDX                                                                     | 1980-01-02 | 2026-11-10 |  12233 | day D on the portal on D+1                  | 2 calendar days                  |
| data/macro/liquidity_stress_hy_oas.csv         | https://raw.githubusercontent.com/mhidper/talvi/HEAD/data/indicadores/BAMLH0A0HYM2.csv (to 2023-11) + FRED BAMLH0A0HYM2 | 1996-12-31 | 2026-11-09 |   7797 | day D published D+1                         | 2 calendar days                  |
| data/macro/liquidity_stress_us_fci_weekly.csv  | FRED NFCI, STLFSI4 (CURRENT VINTAGE, not real-time)                                                                     | 1971-01-08 | 2026-10-30 |   2913 | week ending Friday, released next Wed / Thu | 7 calendar days                  |

Also used: `data/macro/fred_VIXCLS.csv` (already in the repo, one calendar day, as the feature store). The 2022+ files already in `data/macro` (`fred_WALCL`, `fred_WRESBAL`, `fred_RRPONTSYD`, `fred_BAMLH0A0HYM2`, `fred_STLFSI4`) were not touched; FRED answered `curl --http1.1` from this shell and returned the full history for everything except the ICE BofA spread (three years only), whose history was taken from a GitHub copy of the FRED file and checked to be identical to FRED on the 413 overlapping days (six independent copies agree to the last digit on 5,500-7,300 common days).

Lag audit (age in calendar days, at each session's closing date, of the observation actually used; sessions 2010-26). Alignment is `featstore._align_lagged(series, closing_date, lag)`: last observation stamped <= closing date - lag.

| input         |   lag_required_days |   min_age_days |   median_age_days |   max_age_days | ok   |
|:--------------|--------------------:|---------------:|------------------:|---------------:|:-----|
| ecb_assets    |                   7 |              7 |                11 |             13 | True |
| ecb_xliq      |                   7 |              7 |                11 |             13 | True |
| fed_assets    |                   7 |              7 |                 9 |             13 | True |
| fed_xliq      |                   7 |              7 |                 9 |             13 | True |
| money         |                  35 |             35 |                50 |             65 | True |
| money_gap     |                  35 |             35 |                50 |             65 | True |
| ciss_ea       |                   2 |              2 |                 2 |              4 | True |
| ciss_us       |                   2 |              2 |                 2 |              4 | True |
| ciss_diff     |                   2 |              2 |                 2 |              4 | True |
| ciss_diff_gap |                   2 |              2 |                 2 |              4 | True |
| hy            |                   2 |              2 |                 2 |              5 | True |
| z_ciss_ea     |                   2 |              2 |                 2 |              4 | True |
| z_ciss_us     |                   2 |              2 |                 2 |              4 | True |
| z_hy          |                   2 |              2 |                 2 |              5 | True |
| z_vix         |                   1 |              1 |                 1 |              5 | True |
| z_nfci        |                   7 |              7 |                11 |             13 | True |
| z_stlfsi4     |                   7 |              7 |                11 |             13 | True |

Caveats. (i) ECB weekly statements are stamped with the Friday of their ISO week and used from the following Friday; the Fed's Wednesday figures from the following Wednesday. (ii) ECB total assets include quarterly revaluation of gold and reserves: the balance-sheet ratio jumps at quarter-ends for reasons unrelated to policy. (iii) M2 and M3 are current vintages (revisions are small against a y/y gap that ranges over +-8 points). (iv) NFCI and STLFSI4 are current-vintage model estimates: `usfci_d3m` is NOT a real-time signal and is excluded from the combination vote. (v) The daily CISS is a current vintage; no vintages exist to verify that it is unrevised. (vi) Before 2008 Fed reserve balances were about USD 10 bn, so `xliq_lvl` is only meaningful from the 2008 regime change on (the evaluation starts in 2010 with a 3-year trailing mean).

## 2. The 12 candidate votes and their priors (fixed before results)

Vote = prior sign x sign(raw quantity): +1 long EUR/USD, -1 short, 0 silent.

| vote              | family   | prior sign   | raw quantity                                                                                                                                    | data                              | lag                  |
|:------------------|:---------|:-------------|:------------------------------------------------------------------------------------------------------------------------------------------------|:----------------------------------|:---------------------|
| bs_d3m            | A        | -            | 63-session change of log(ECB total assets / Fed total assets), own currencies                                                                   | ECB ILM weekly, FRED WALCL        | 7 d                  |
| bs_d6m            | A        | -            | the same over 126 sessions                                                                                                                      | same                              | 7 d                  |
| bs_d12m           | A        | -            | the same over 252 sessions                                                                                                                      | same                              | 7 d                  |
| money_gap         | A        | -            | (EA M3 y/y - US M2 y/y) minus its expanding mean since 1999                                                                                     | ECB BSI, FRED M2SL                | 35 d after month-end |
| xliq_lvl          | A        | -            | log((ECB current accounts + deposit facility) / (Fed reserves + ON RRP)) minus its trailing 756-session mean                                    | ECB ILM, FRED WRESBAL + RRPONTSYD | 7 d                  |
| ciss_diff_lvl     | B        | -            | (CISS euro area - CISS US) minus its expanding mean since 1999                                                                                  | ECB CISS daily                    | 2 d                  |
| ciss_diff_d1m     | B        | -            | 21-session change of (CISS EA - CISS US)                                                                                                        | ECB CISS daily                    | 2 d                  |
| ciss_diff_d3m     | B        | -            | 63-session change of (CISS EA - CISS US)                                                                                                        | ECB CISS daily                    | 2 d                  |
| gstress_hi_rising | B        | -            | G = mean expanding z of CISS EA, CISS US, log VIX, log HY spread; -1 if G > 0 and rising over 63 sessions, +1 if G < 0 and falling, else silent | ECB CISS, VIX, HY OAS             | 2 d (VIX 1 d)        |
| credit_d3m        | B        | -            | 63-session change of the US high-yield spread                                                                                                   | ICE BofA HY OAS                   | 2 d                  |
| usfci_d3m         | B        | -            | 63-session change of the mean expanding z of NFCI and STLFSI4 (NOT real-time: current-vintage estimates)                                        | FRED NFCI, STLFSI4                | 7 d                  |
| combo_majority    | A+B      | n/a          | sign of the sum of the ten real-time votes above (all but usfci_d3m); silent on a tie                                                           | -                                 | -                    |

What the votes look like, 2010-26 (correlations are of the vote with returns in bp; `agree_with_*` = share of active sessions on which the vote has the same sign as the old signal):

| vote              |   active_share |   share_long |   flips_per_year |   corr_fwd21_bp |   corr_fwd63_bp |   corr_past_ret21 |   corr_past_ret63 |   corr_past_ret252 |   agree_with_cot_sign |   agree_with_spread_trend_sign |   agree_with_house_sign |   agree_with_agree3_direction |
|:------------------|---------------:|-------------:|-----------------:|----------------:|----------------:|------------------:|------------------:|-------------------:|----------------------:|-------------------------------:|------------------------:|------------------------------:|
| bs_d3m            |           1    |         0.39 |             6.65 |            0.01 |           -0.03 |              0.02 |              0.15 |               0.16 |                  0.58 |                           0.54 |                    0.52 |                          0.6  |
| bs_d6m            |           1    |         0.4  |             4.39 |           -0.06 |           -0.12 |              0.03 |              0.13 |               0.27 |                  0.57 |                           0.54 |                    0.5  |                          0.59 |
| bs_d12m           |           1    |         0.42 |             2.14 |           -0.06 |           -0.06 |             -0.01 |              0.01 |               0.22 |                  0.51 |                           0.55 |                    0.48 |                          0.53 |
| money_gap         |           1    |         0.57 |             0.71 |           -0.07 |           -0.12 |             -0.1  |             -0.17 |              -0.02 |                  0.47 |                           0.47 |                    0.48 |                          0.44 |
| xliq_lvl          |           1    |         0.5  |             1.42 |           -0.04 |           -0.1  |             -0.06 |             -0.14 |              -0.04 |                  0.45 |                           0.49 |                    0.44 |                          0.42 |
| ciss_diff_lvl     |           1    |         0.58 |             7    |           -0.03 |           -0.08 |              0.02 |              0.08 |               0.41 |                  0.49 |                           0.49 |                    0.42 |                          0.45 |
| ciss_diff_d1m     |           1    |         0.54 |            22.55 |           -0.02 |           -0    |              0.08 |              0.07 |               0.03 |                  0.52 |                           0.5  |                    0.53 |                          0.53 |
| ciss_diff_d3m     |           1    |         0.54 |            18.1  |            0.04 |            0.05 |              0.1  |              0.13 |               0.1  |                  0.53 |                           0.51 |                    0.53 |                          0.55 |
| gstress_hi_rising |           0.62 |         0.78 |            20.18 |           -0.05 |           -0.11 |              0.12 |              0.29 |               0.35 |                  0.55 |                           0.44 |                    0.43 |                          0.47 |
| credit_d3m        |           0.99 |         0.62 |            13.59 |            0.04 |            0.08 |              0.12 |              0.2  |               0.18 |                  0.57 |                           0.47 |                    0.48 |                          0.53 |
| usfci_d3m         |           1    |         0.56 |             9.79 |            0.07 |            0.16 |              0.1  |              0.19 |               0.13 |                  0.56 |                           0.49 |                    0.49 |                          0.53 |
| combo_majority    |           0.86 |         0.51 |            18.64 |           -0.03 |           -0.07 |              0.04 |              0.16 |               0.26 |                  0.57 |                           0.54 |                    0.49 |                          0.58 |

## 3. Reconciliation of the agreement rule

Rebuilt with `selective.load_data / make_ctx / build_targets / house_score_wf / weekly_idx / seq_idx / decision_frame / cell_stats`. Cells compared with `selective_accuracy_coverage.csv`: 32; exact matches (n and accuracy): 32.

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

| candidate         | 2010-26 / 21s             | 2010-26 / 42s            | 2010-26 / 63s           |
|:------------------|:--------------------------|:-------------------------|:------------------------|
| bs_d3m            | 50 [43-56] n=208 (12.4/y) | 56 [46-65] n=104 (6.2/y) | 51 [39-62] n=69 (4.2/y) |
| bs_d6m            | 50 [43-56] n=208 (12.4/y) | 55 [45-64] n=104 (6.2/y) | 51 [39-62] n=69 (4.2/y) |
| bs_d12m           | 50 [43-56] n=208 (12.4/y) | 57 [47-66] n=104 (6.2/y) | 48 [36-59] n=69 (4.2/y) |
| money_gap         | 48 [41-55] n=208 (12.4/y) | 51 [41-60] n=104 (6.2/y) | 38 [27-49] n=69 (4.2/y) |
| xliq_lvl          | 49 [42-55] n=208 (12.4/y) | 49 [40-59] n=104 (6.2/y) | 42 [31-54] n=69 (4.2/y) |
| ciss_diff_lvl     | 53 [46-60] n=208 (12.4/y) | 48 [39-58] n=104 (6.2/y) | 54 [42-65] n=69 (4.2/y) |
| ciss_diff_d1m     | 50 [44-57] n=208 (12.4/y) | 58 [48-67] n=104 (6.2/y) | 54 [42-65] n=69 (4.2/y) |
| ciss_diff_d3m     | 54 [47-60] n=208 (12.4/y) | 52 [42-61] n=104 (6.2/y) | 61 [49-72] n=69 (4.2/y) |
| gstress_hi_rising | 41 [34-49] n=162 (9.7/y)  | 44 [35-55] n=90 (5.4/y)  | 39 [28-51] n=62 (3.7/y) |
| credit_d3m        | 52 [46-59] n=208 (12.4/y) | 49 [40-59] n=104 (6.2/y) | 54 [42-65] n=69 (4.2/y) |
| usfci_d3m         | 57 [50-63] n=208 (12.4/y) | 52 [42-61] n=104 (6.2/y) | 52 [41-64] n=69 (4.2/y) |
| combo_majority    | 49 [43-56] n=198 (11.8/y) | 55 [45-64] n=102 (6.1/y) | 49 [37-60] n=68 (4.1/y) |

Non-overlapping decisions, 2016-26:

| candidate         | 2016-26 / 21s             | 2016-26 / 42s           | 2016-26 / 63s           |
|:------------------|:--------------------------|:------------------------|:------------------------|
| bs_d3m            | 47 [38-55] n=133 (12.4/y) | 53 [41-65] n=66 (6.2/y) | 52 [38-66] n=44 (4.2/y) |
| bs_d6m            | 51 [43-59] n=133 (12.4/y) | 58 [46-69] n=66 (6.2/y) | 55 [40-68] n=44 (4.2/y) |
| bs_d12m           | 50 [42-59] n=133 (12.4/y) | 58 [46-69] n=66 (6.2/y) | 50 [36-64] n=44 (4.2/y) |
| money_gap         | 49 [41-57] n=133 (12.4/y) | 55 [43-66] n=66 (6.2/y) | 36 [24-51] n=44 (4.2/y) |
| xliq_lvl          | 52 [43-60] n=133 (12.4/y) | 48 [37-60] n=66 (6.2/y) | 43 [30-58] n=44 (4.2/y) |
| ciss_diff_lvl     | 55 [46-63] n=133 (12.4/y) | 47 [35-59] n=66 (6.2/y) | 55 [40-68] n=44 (4.2/y) |
| ciss_diff_d1m     | 48 [40-57] n=133 (12.4/y) | 58 [46-69] n=66 (6.2/y) | 50 [36-64] n=44 (4.2/y) |
| ciss_diff_d3m     | 54 [46-62] n=133 (12.4/y) | 52 [40-63] n=66 (6.2/y) | 64 [49-76] n=44 (4.2/y) |
| gstress_hi_rising | 39 [30-48] n=106 (9.9/y)  | 41 [30-54] n=58 (5.4/y) | 33 [21-49] n=39 (3.7/y) |
| credit_d3m        | 50 [42-59] n=133 (12.4/y) | 47 [35-59] n=66 (6.2/y) | 55 [40-68] n=44 (4.2/y) |
| usfci_d3m         | 58 [49-66] n=133 (12.4/y) | 52 [40-63] n=66 (6.2/y) | 55 [40-68] n=44 (4.2/y) |
| combo_majority    | 53 [44-61] n=127 (11.8/y) | 57 [45-68] n=65 (6.1/y) | 51 [37-65] n=43 (4.1/y) |

Non-overlapping decisions, 2023-26:

| candidate         | 2023-26 / 21s            | 2023-26 / 42s           | 2023-26 / 63s           |
|:------------------|:-------------------------|:------------------------|:------------------------|
| bs_d3m            | 45 [31-59] n=47 (12.5/y) | 43 [26-63] n=23 (6.2/y) | 40 [20-64] n=15 (4.2/y) |
| bs_d6m            | 47 [33-61] n=47 (12.5/y) | 43 [26-63] n=23 (6.2/y) | 40 [20-64] n=15 (4.2/y) |
| bs_d12m           | 45 [31-59] n=47 (12.5/y) | 35 [19-55] n=23 (6.2/y) | 33 [15-58] n=15 (4.2/y) |
| money_gap         | 47 [33-61] n=47 (12.5/y) | 52 [33-71] n=23 (6.2/y) | 27 [11-52] n=15 (4.2/y) |
| xliq_lvl          | 53 [39-67] n=47 (12.5/y) | 57 [37-74] n=23 (6.2/y) | 47 [25-70] n=15 (4.2/y) |
| ciss_diff_lvl     | 60 [45-72] n=47 (12.5/y) | 52 [33-71] n=23 (6.2/y) | 67 [42-85] n=15 (4.2/y) |
| ciss_diff_d1m     | 55 [41-69] n=47 (12.5/y) | 65 [45-81] n=23 (6.2/y) | 47 [25-70] n=15 (4.2/y) |
| ciss_diff_d3m     | 53 [39-67] n=47 (12.5/y) | 48 [29-67] n=23 (6.2/y) | 53 [30-75] n=15 (4.2/y) |
| gstress_hi_rising | 39 [26-55] n=38 (10.1/y) | 50 [30-70] n=20 (5.4/y) | 50 [27-73] n=14 (3.9/y) |
| credit_d3m        | 43 [30-57] n=47 (12.5/y) | 39 [22-59] n=23 (6.2/y) | 47 [25-70] n=15 (4.2/y) |
| usfci_d3m         | 53 [39-67] n=47 (12.5/y) | 48 [29-67] n=23 (6.2/y) | 40 [20-64] n=15 (4.2/y) |
| combo_majority    | 41 [28-56] n=44 (11.7/y) | 36 [20-57] n=22 (6.0/y) | 53 [30-75] n=15 (4.2/y) |

Weekly decisions (overlapping holds; no interval shown - the effective sample is the non-overlapping count above):

| candidate         | 2010-26 / 21s   | 2010-26 / 42s   | 2010-26 / 63s   | 2016-26 / 21s   | 2016-26 / 42s   | 2016-26 / 63s   | 2023-26 / 21s   | 2023-26 / 42s   | 2023-26 / 63s   |
|:------------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|
| bs_d3m            | 51 n=870        | 53 n=866        | 52 n=862        | 51 n=559        | 54 n=555        | 54 n=551        | 45 n=195        | 45 n=191        | 50 n=187        |
| bs_d6m            | 50 n=870        | 50 n=866        | 50 n=862        | 54 n=559        | 54 n=555        | 56 n=551        | 50 n=195        | 44 n=191        | 50 n=187        |
| bs_d12m           | 48 n=870        | 50 n=866        | 54 n=862        | 51 n=559        | 54 n=555        | 60 n=551        | 46 n=195        | 44 n=191        | 53 n=187        |
| money_gap         | 47 n=870        | 49 n=866        | 47 n=862        | 47 n=559        | 50 n=555        | 48 n=551        | 46 n=195        | 50 n=191        | 43 n=187        |
| xliq_lvl          | 49 n=870        | 48 n=866        | 49 n=862        | 52 n=559        | 50 n=555        | 50 n=551        | 53 n=195        | 50 n=191        | 53 n=187        |
| ciss_diff_lvl     | 47 n=870        | 46 n=866        | 44 n=862        | 49 n=559        | 48 n=555        | 46 n=551        | 50 n=195        | 56 n=191        | 52 n=187        |
| ciss_diff_d1m     | 49 n=870        | 52 n=866        | 50 n=862        | 49 n=559        | 52 n=555        | 50 n=551        | 51 n=195        | 52 n=191        | 48 n=187        |
| ciss_diff_d3m     | 52 n=870        | 52 n=866        | 51 n=862        | 53 n=559        | 54 n=555        | 55 n=551        | 51 n=195        | 48 n=191        | 56 n=187        |
| gstress_hi_rising | 46 n=547        | 45 n=545        | 46 n=542        | 44 n=361        | 42 n=359        | 42 n=356        | 43 n=130        | 44 n=128        | 47 n=125        |
| credit_d3m        | 50 n=864        | 50 n=861        | 52 n=857        | 47 n=553        | 49 n=550        | 51 n=546        | 36 n=191        | 38 n=188        | 42 n=184        |
| usfci_d3m         | 52 n=870        | 52 n=866        | 55 n=862        | 51 n=559        | 52 n=555        | 56 n=551        | 43 n=195        | 43 n=191        | 51 n=187        |
| combo_majority    | 50 n=747        | 50 n=743        | 50 n=739        | 53 n=465        | 52 n=461        | 54 n=457        | 46 n=165        | 40 n=161        | 46 n=157        |

Timing placebo of the standalone votes, non-overlapping, 2010-26 (the vote made 63 / 126 sessions staler):

| candidate         | 21s live   | 21s placebo+63   | 21s placebo+126   | 42s live   | 42s placebo+63   | 42s placebo+126   | 63s live   | 63s placebo+63   | 63s placebo+126   |
|:------------------|:-----------|:-----------------|:------------------|:-----------|:-----------------|:------------------|:-----------|:-----------------|:------------------|
| bs_d3m            | 50 n=208   | 48 n=208         | 49 n=208          | 56 n=104   | 54 n=104         | 52 n=104          | 51 n=69    | 48 n=69          | 41 n=69           |
| bs_d6m            | 50 n=208   | 48 n=208         | 46 n=208          | 55 n=104   | 53 n=104         | 52 n=104          | 51 n=69    | 45 n=69          | 43 n=69           |
| bs_d12m           | 50 n=208   | 46 n=208         | 45 n=208          | 57 n=104   | 51 n=104         | 47 n=104          | 48 n=69    | 42 n=69          | 39 n=69           |
| money_gap         | 48 n=208   | 48 n=208         | 48 n=208          | 51 n=104   | 48 n=104         | 46 n=104          | 38 n=69    | 43 n=69          | 43 n=69           |
| xliq_lvl          | 49 n=208   | 45 n=208         | 41 n=208          | 49 n=104   | 45 n=104         | 38 n=104          | 42 n=69    | 42 n=69          | 39 n=69           |
| ciss_diff_lvl     | 53 n=208   | 50 n=208         | 46 n=208          | 48 n=104   | 44 n=104         | 52 n=104          | 54 n=69    | 42 n=69          | 49 n=69           |
| ciss_diff_d1m     | 50 n=208   | 57 n=208         | 48 n=208          | 58 n=104   | 51 n=104         | 56 n=104          | 54 n=69    | 51 n=69          | 61 n=69           |
| ciss_diff_d3m     | 54 n=208   | 60 n=208         | 51 n=208          | 52 n=104   | 53 n=104         | 61 n=104          | 61 n=69    | 55 n=69          | 62 n=69           |
| gstress_hi_rising | 41 n=162   | 47 n=160         | 42 n=157          | 44 n=90    | 51 n=88          | 39 n=87           | 39 n=62    | 46 n=61          | 43 n=60           |
| credit_d3m        | 52 n=208   | 50 n=208         | 48 n=208          | 49 n=104   | 55 n=104         | 47 n=104          | 54 n=69    | 59 n=69          | 46 n=69           |
| usfci_d3m         | 57 n=208   | 52 n=208         | 47 n=208          | 52 n=104   | 55 n=104         | 47 n=104          | 52 n=69    | 58 n=69          | 48 n=69           |
| combo_majority    | 49 n=198   | 46 n=198         | 45 n=198          | 55 n=102   | 46 n=101         | 45 n=102          | 49 n=68    | 43 n=68          | 41 n=68           |

## 5. As an extra vote

### 5a. Agreement rule AND the vote agrees, against the agreement rule alone

Non-overlapping decisions (% right, decisions, decisions per year). First row = the agreement rule alone.

| candidate         | 2010-26 / 21s    | 2010-26 / 42s   | 2010-26 / 63s   | 2016-26 / 21s   | 2016-26 / 42s   | 2016-26 / 63s   | 2023-26 / 21s   | 2023-26 / 42s   | 2023-26 / 63s   |
|:------------------|:-----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|
| agree3            | 59 n=156 (9.3/y) | 61 n=89 (5.3/y) | 72 n=61 (3.7/y) | 57 n=96 (8.9/y) | 59 n=56 (5.2/y) | 71 n=38 (3.6/y) | 60 n=35 (9.3/y) | 45 n=20 (5.4/y) | 50 n=14 (3.9/y) |
| bs_d3m            | 55 n=106 (6.3/y) | 58 n=64 (3.8/y) | 67 n=45 (2.7/y) | 61 n=61 (5.7/y) | 59 n=37 (3.5/y) | 67 n=27 (2.5/y) | 61 n=23 (6.1/y) | 50 n=14 (3.8/y) | 40 n=10 (2.8/y) |
| bs_d6m            | 51 n=103 (6.1/y) | 59 n=61 (3.7/y) | 67 n=42 (2.5/y) | 58 n=65 (6.0/y) | 61 n=38 (3.6/y) | 73 n=26 (2.5/y) | 54 n=24 (6.4/y) | 43 n=14 (3.8/y) | 56 n=9 (2.5/y)  |
| bs_d12m           | 49 n=93 (5.5/y)  | 62 n=55 (3.3/y) | 71 n=41 (2.5/y) | 58 n=57 (5.3/y) | 68 n=34 (3.2/y) | 80 n=25 (2.4/y) | 64 n=14 (3.7/y) | 67 n=9 (2.4/y)  | 50 n=8 (2.2/y)  |
| money_gap         | 53 n=79 (4.7/y)  | 64 n=47 (2.8/y) | 67 n=36 (2.2/y) | 56 n=52 (4.8/y) | 61 n=31 (2.9/y) | 71 n=24 (2.3/y) | 58 n=19 (5.0/y) | 55 n=11 (3.0/y) | 56 n=9 (2.5/y)  |
| xliq_lvl          | 57 n=77 (4.6/y)  | 62 n=47 (2.8/y) | 71 n=34 (2.0/y) | 70 n=47 (4.4/y) | 59 n=29 (2.7/y) | 76 n=21 (2.0/y) | 68 n=22 (5.8/y) | 43 n=14 (3.8/y) | 60 n=10 (2.8/y) |
| ciss_diff_lvl     | 51 n=86 (5.1/y)  | 55 n=53 (3.2/y) | 63 n=41 (2.5/y) | 50 n=54 (5.0/y) | 52 n=33 (3.1/y) | 65 n=26 (2.5/y) | 58 n=19 (5.0/y) | 55 n=11 (3.0/y) | 56 n=9 (2.5/y)  |
| ciss_diff_d1m     | 52 n=105 (6.3/y) | 56 n=73 (4.4/y) | 54 n=52 (3.1/y) | 52 n=66 (6.1/y) | 50 n=46 (4.3/y) | 53 n=32 (3.0/y) | 54 n=24 (6.4/y) | 50 n=18 (4.9/y) | 25 n=12 (3.3/y) |
| ciss_diff_d3m     | 55 n=111 (6.6/y) | 61 n=71 (4.3/y) | 67 n=49 (3.0/y) | 52 n=66 (6.1/y) | 60 n=43 (4.0/y) | 72 n=29 (2.7/y) | 60 n=20 (5.3/y) | 53 n=15 (4.1/y) | 70 n=10 (2.8/y) |
| gstress_hi_rising | 47 n=62 (3.7/y)  | 50 n=40 (2.4/y) | 55 n=33 (2.0/y) | 44 n=36 (3.3/y) | 38 n=24 (2.2/y) | 48 n=21 (2.0/y) | 54 n=13 (3.5/y) | 44 n=9 (2.4/y)  | 50 n=8 (2.2/y)  |
| credit_d3m        | 55 n=103 (6.1/y) | 58 n=64 (3.8/y) | 62 n=48 (2.9/y) | 53 n=64 (5.9/y) | 51 n=41 (3.8/y) | 57 n=30 (2.8/y) | 43 n=21 (5.6/y) | 31 n=13 (3.5/y) | 30 n=10 (2.8/y) |
| usfci_d3m         | 58 n=104 (6.2/y) | 60 n=68 (4.1/y) | 68 n=50 (3.0/y) | 57 n=63 (5.9/y) | 65 n=43 (4.0/y) | 65 n=31 (2.9/y) | 55 n=22 (5.8/y) | 56 n=16 (4.3/y) | 50 n=10 (2.8/y) |
| combo_majority    | 55 n=101 (6.0/y) | 64 n=61 (3.7/y) | 71 n=48 (2.9/y) | 62 n=60 (5.6/y) | 65 n=37 (3.5/y) | 70 n=30 (2.8/y) | 55 n=20 (5.3/y) | 46 n=13 (3.5/y) | 40 n=10 (2.8/y) |

The same with 95 % Wilson intervals, 2010-26 only:

| candidate         | 2010-26 / 21s            | 2010-26 / 42s           | 2010-26 / 63s           |
|:------------------|:-------------------------|:------------------------|:------------------------|
| agree3            | 59 [51-66] n=156 (9.3/y) | 61 [50-70] n=89 (5.3/y) | 72 [60-82] n=61 (3.7/y) |
| bs_d3m            | 55 [45-64] n=106 (6.3/y) | 58 [46-69] n=64 (3.8/y) | 67 [52-79] n=45 (2.7/y) |
| bs_d6m            | 51 [42-61] n=103 (6.1/y) | 59 [46-70] n=61 (3.7/y) | 67 [52-79] n=42 (2.5/y) |
| bs_d12m           | 49 [40-59] n=93 (5.5/y)  | 62 [49-73] n=55 (3.3/y) | 71 [56-82] n=41 (2.5/y) |
| money_gap         | 53 [42-64] n=79 (4.7/y)  | 64 [50-76] n=47 (2.8/y) | 67 [50-80] n=36 (2.2/y) |
| xliq_lvl          | 57 [46-68] n=77 (4.6/y)  | 62 [47-74] n=47 (2.8/y) | 71 [54-83] n=34 (2.0/y) |
| ciss_diff_lvl     | 51 [41-61] n=86 (5.1/y)  | 55 [41-67] n=53 (3.2/y) | 63 [48-76] n=41 (2.5/y) |
| ciss_diff_d1m     | 52 [43-62] n=105 (6.3/y) | 56 [45-67] n=73 (4.4/y) | 54 [41-67] n=52 (3.1/y) |
| ciss_diff_d3m     | 55 [46-64] n=111 (6.6/y) | 61 [49-71] n=71 (4.3/y) | 67 [53-79] n=49 (3.0/y) |
| gstress_hi_rising | 47 [35-59] n=62 (3.7/y)  | 50 [35-65] n=40 (2.4/y) | 55 [38-70] n=33 (2.0/y) |
| credit_d3m        | 55 [46-65] n=103 (6.1/y) | 58 [46-69] n=64 (3.8/y) | 62 [48-75] n=48 (2.9/y) |
| usfci_d3m         | 58 [48-67] n=104 (6.2/y) | 60 [48-71] n=68 (4.1/y) | 68 [54-79] n=50 (3.0/y) |
| combo_majority    | 55 [46-65] n=101 (6.0/y) | 64 [51-75] n=61 (3.7/y) | 71 [57-82] n=48 (2.9/y) |

Gain in accuracy points over the agreement rule, non-overlapping (bar: >= +3 at 21s and 42s in 2010-26 and 2016-26):

| candidate         |   2010-26 / 21s |   2010-26 / 42s |   2010-26 / 63s |   2016-26 / 21s |   2016-26 / 42s |   2016-26 / 63s |   2023-26 / 21s |   2023-26 / 42s |   2023-26 / 63s |
|:------------------|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|
| bs_d3m            |            -4.3 |            -2.9 |            -5.5 |             3.4 |             0.5 |            -4.4 |             0.9 |             5   |           -10   |
| bs_d6m            |            -7.5 |            -1.7 |            -5.5 |             1.2 |             1.6 |             2   |            -5.8 |            -2.1 |             5.6 |
| bs_d12m           |            -9.5 |             1.1 |            -1.4 |             0.6 |             8.7 |             8.9 |             4.3 |            21.7 |             0   |
| money_gap         |            -5.8 |             3.2 |            -5.5 |            -1.5 |             2.4 |            -0.2 |            -2.1 |             9.5 |             5.6 |
| xliq_lvl          |            -1.8 |             1   |            -1.5 |            12.9 |            -0.3 |             5.1 |             8.2 |            -2.1 |            10   |
| ciss_diff_lvl     |            -7.8 |            -6   |            -8.7 |            -7.3 |            -7.4 |            -5.7 |            -2.1 |             9.5 |             5.6 |
| ciss_diff_d1m     |            -6.6 |            -4.5 |           -18.3 |            -5.8 |            -8.9 |           -17.9 |            -5.8 |             5   |           -25   |
| ciss_diff_d3m     |            -4   |            -0.1 |            -4.8 |            -5.8 |             1.5 |             1.4 |             0   |             8.3 |            20   |
| gstress_hi_rising |           -12.2 |           -10.7 |           -17.6 |           -12.8 |           -21.4 |           -23.4 |            -6.2 |            -0.6 |             0   |
| credit_d3m        |            -3.6 |            -2.9 |            -9.6 |            -4.2 |            -7.7 |           -14.4 |           -17.1 |           -14.2 |           -20   |
| usfci_d3m         |            -1.3 |            -0.4 |            -4.1 |            -0.1 |             6.2 |            -6.5 |            -5.5 |            11.2 |             0   |
| combo_majority    |            -3.5 |             3.3 |            -1.3 |             4.4 |             5.9 |            -1.1 |            -5   |             1.2 |           -10   |

Weekly decisions:

| candidate         | 2010-26 / 21s     | 2010-26 / 42s     | 2010-26 / 63s     | 2016-26 / 21s     | 2016-26 / 42s     | 2016-26 / 63s     | 2023-26 / 21s    | 2023-26 / 42s    | 2023-26 / 63s    |
|:------------------|:------------------|:------------------|:------------------|:------------------|:------------------|:------------------|:-----------------|:-----------------|:-----------------|
| agree3            | 59 n=387 (23.1/y) | 65 n=383 (23.0/y) | 67 n=383 (23.1/y) | 57 n=243 (22.6/y) | 63 n=239 (22.4/y) | 67 n=239 (22.6/y) | 55 n=77 (20.6/y) | 47 n=73 (19.9/y) | 53 n=73 (20.4/y) |
| bs_d3m            | 61 n=231 (13.8/y) | 65 n=231 (13.9/y) | 67 n=231 (13.9/y) | 63 n=134 (12.5/y) | 68 n=134 (12.6/y) | 74 n=134 (12.7/y) | 56 n=39 (10.4/y) | 44 n=39 (10.7/y) | 62 n=39 (10.9/y) |
| bs_d6m            | 59 n=230 (13.7/y) | 63 n=230 (13.8/y) | 66 n=230 (13.9/y) | 64 n=154 (14.3/y) | 68 n=154 (14.4/y) | 73 n=154 (14.5/y) | 59 n=44 (11.8/y) | 50 n=44 (12.0/y) | 61 n=44 (12.3/y) |
| bs_d12m           | 57 n=206 (12.3/y) | 65 n=206 (12.4/y) | 69 n=206 (12.4/y) | 61 n=137 (12.8/y) | 69 n=137 (12.8/y) | 79 n=137 (12.9/y) | 71 n=24 (6.4/y)  | 54 n=24 (6.6/y)  | 88 n=24 (6.7/y)  |
| money_gap         | 55 n=166 (9.9/y)  | 64 n=166 (10.0/y) | 59 n=166 (10.0/y) | 54 n=116 (10.8/y) | 68 n=116 (10.9/y) | 62 n=116 (11.0/y) | 58 n=38 (10.2/y) | 66 n=38 (10.4/y) | 47 n=38 (10.6/y) |
| xliq_lvl          | 60 n=150 (9.0/y)  | 63 n=150 (9.0/y)  | 64 n=150 (9.0/y)  | 66 n=91 (8.5/y)   | 66 n=91 (8.5/y)   | 71 n=91 (8.6/y)   | 64 n=36 (9.6/y)  | 56 n=36 (9.8/y)  | 67 n=36 (10.0/y) |
| ciss_diff_lvl     | 54 n=178 (10.6/y) | 58 n=178 (10.7/y) | 59 n=178 (10.7/y) | 57 n=115 (10.7/y) | 59 n=115 (10.8/y) | 61 n=115 (10.9/y) | 47 n=36 (9.6/y)  | 42 n=36 (9.8/y)  | 44 n=36 (10.0/y) |
| ciss_diff_d1m     | 59 n=206 (12.3/y) | 66 n=202 (12.1/y) | 66 n=202 (12.2/y) | 59 n=124 (11.5/y) | 66 n=120 (11.3/y) | 65 n=120 (11.3/y) | 56 n=43 (11.5/y) | 44 n=39 (10.7/y) | 46 n=39 (10.9/y) |
| ciss_diff_d3m     | 60 n=216 (12.9/y) | 67 n=212 (12.7/y) | 67 n=212 (12.8/y) | 60 n=132 (12.3/y) | 66 n=128 (12.0/y) | 69 n=128 (12.1/y) | 56 n=39 (10.4/y) | 37 n=35 (9.6/y)  | 51 n=35 (9.8/y)  |
| gstress_hi_rising | 50 n=123 (7.3/y)  | 53 n=123 (7.4/y)  | 57 n=123 (7.4/y)  | 49 n=71 (6.6/y)   | 49 n=71 (6.7/y)   | 55 n=71 (6.7/y)   | 48 n=21 (5.6/y)  | 29 n=21 (5.7/y)  | 43 n=21 (5.9/y)  |
| credit_d3m        | 55 n=205 (12.2/y) | 60 n=203 (12.2/y) | 63 n=203 (12.2/y) | 50 n=121 (11.3/y) | 60 n=119 (11.2/y) | 66 n=119 (11.2/y) | 35 n=26 (7.0/y)  | 17 n=24 (6.6/y)  | 33 n=24 (6.7/y)  |
| usfci_d3m         | 59 n=207 (12.4/y) | 62 n=205 (12.3/y) | 66 n=205 (12.4/y) | 57 n=127 (11.8/y) | 60 n=125 (11.7/y) | 66 n=125 (11.8/y) | 50 n=30 (8.0/y)  | 32 n=28 (7.6/y)  | 50 n=28 (7.8/y)  |
| combo_majority    | 59 n=186 (11.1/y) | 61 n=186 (11.2/y) | 62 n=186 (11.2/y) | 68 n=112 (10.4/y) | 68 n=112 (10.5/y) | 73 n=112 (10.6/y) | 68 n=28 (7.5/y)  | 43 n=28 (7.6/y)  | 64 n=28 (7.8/y)  |

### 5b. Coverage extension: the vote's own calls on sessions where the three old signals do NOT agree

Non-overlapping, with 95 % Wilson intervals, 2010-26, then all periods without intervals:

| candidate         | 2010-26 / 21s             | 2010-26 / 42s           | 2010-26 / 63s           |
|:------------------|:--------------------------|:------------------------|:------------------------|
| bs_d3m            | 50 [43-57] n=170 (10.1/y) | 54 [44-64] n=93 (5.6/y) | 44 [32-56] n=64 (3.9/y) |
| bs_d6m            | 50 [43-57] n=170 (10.1/y) | 47 [37-57] n=93 (5.6/y) | 45 [34-57] n=64 (3.9/y) |
| bs_d12m           | 48 [41-56] n=170 (10.1/y) | 48 [38-58] n=93 (5.6/y) | 52 [40-63] n=64 (3.9/y) |
| money_gap         | 48 [40-55] n=170 (10.1/y) | 52 [42-62] n=93 (5.6/y) | 50 [38-62] n=64 (3.9/y) |
| xliq_lvl          | 48 [41-56] n=170 (10.1/y) | 46 [36-56] n=93 (5.6/y) | 45 [34-57] n=64 (3.9/y) |
| ciss_diff_lvl     | 49 [41-56] n=170 (10.1/y) | 46 [36-56] n=93 (5.6/y) | 48 [37-60] n=64 (3.9/y) |
| ciss_diff_d1m     | 48 [40-55] n=170 (10.1/y) | 49 [40-59] n=93 (5.6/y) | 50 [38-62] n=64 (3.9/y) |
| ciss_diff_d3m     | 51 [44-59] n=170 (10.1/y) | 57 [47-67] n=93 (5.6/y) | 58 [46-69] n=64 (3.9/y) |
| gstress_hi_rising | 44 [36-52] n=135 (8.1/y)  | 48 [37-58] n=82 (4.9/y) | 46 [34-59] n=56 (3.4/y) |
| credit_d3m        | 44 [37-52] n=170 (10.1/y) | 52 [42-62] n=93 (5.6/y) | 56 [44-68] n=64 (3.9/y) |
| usfci_d3m         | 51 [43-58] n=170 (10.1/y) | 55 [45-65] n=93 (5.6/y) | 59 [47-71] n=64 (3.9/y) |
| combo_majority    | 50 [42-58] n=162 (9.7/y)  | 52 [42-62] n=91 (5.5/y) | 55 [43-66] n=64 (3.9/y) |

| candidate         | 2010-26 / 21s     | 2010-26 / 42s   | 2010-26 / 63s   | 2016-26 / 21s     | 2016-26 / 42s   | 2016-26 / 63s   | 2023-26 / 21s    | 2023-26 / 42s   | 2023-26 / 63s   |
|:------------------|:------------------|:----------------|:----------------|:------------------|:----------------|:----------------|:-----------------|:----------------|:----------------|
| bs_d3m            | 50 n=170 (10.1/y) | 54 n=93 (5.6/y) | 44 n=64 (3.9/y) | 48 n=109 (10.1/y) | 55 n=60 (5.6/y) | 39 n=41 (3.9/y) | 37 n=38 (10.1/y) | 52 n=21 (5.7/y) | 29 n=14 (3.9/y) |
| bs_d6m            | 50 n=170 (10.1/y) | 47 n=93 (5.6/y) | 45 n=64 (3.9/y) | 52 n=109 (10.1/y) | 50 n=60 (5.6/y) | 44 n=41 (3.9/y) | 42 n=38 (10.1/y) | 43 n=21 (5.7/y) | 29 n=14 (3.9/y) |
| bs_d12m           | 48 n=170 (10.1/y) | 48 n=93 (5.6/y) | 52 n=64 (3.9/y) | 50 n=109 (10.1/y) | 48 n=60 (5.6/y) | 56 n=41 (3.9/y) | 37 n=38 (10.1/y) | 38 n=21 (5.7/y) | 36 n=14 (3.9/y) |
| money_gap         | 48 n=170 (10.1/y) | 52 n=93 (5.6/y) | 50 n=64 (3.9/y) | 50 n=109 (10.1/y) | 53 n=60 (5.6/y) | 46 n=41 (3.9/y) | 45 n=38 (10.1/y) | 52 n=21 (5.7/y) | 36 n=14 (3.9/y) |
| xliq_lvl          | 48 n=170 (10.1/y) | 46 n=93 (5.6/y) | 45 n=64 (3.9/y) | 50 n=109 (10.1/y) | 48 n=60 (5.6/y) | 41 n=41 (3.9/y) | 45 n=38 (10.1/y) | 52 n=21 (5.7/y) | 36 n=14 (3.9/y) |
| ciss_diff_lvl     | 49 n=170 (10.1/y) | 46 n=93 (5.6/y) | 48 n=64 (3.9/y) | 54 n=109 (10.1/y) | 47 n=60 (5.6/y) | 51 n=41 (3.9/y) | 61 n=38 (10.1/y) | 52 n=21 (5.7/y) | 43 n=14 (3.9/y) |
| ciss_diff_d1m     | 48 n=170 (10.1/y) | 49 n=93 (5.6/y) | 50 n=64 (3.9/y) | 49 n=109 (10.1/y) | 47 n=60 (5.6/y) | 49 n=41 (3.9/y) | 47 n=38 (10.1/y) | 62 n=21 (5.7/y) | 43 n=14 (3.9/y) |
| ciss_diff_d3m     | 51 n=170 (10.1/y) | 57 n=93 (5.6/y) | 58 n=64 (3.9/y) | 55 n=109 (10.1/y) | 58 n=60 (5.6/y) | 61 n=41 (3.9/y) | 53 n=38 (10.1/y) | 57 n=21 (5.7/y) | 57 n=14 (3.9/y) |
| gstress_hi_rising | 44 n=135 (8.1/y)  | 48 n=82 (4.9/y) | 46 n=56 (3.4/y) | 41 n=88 (8.2/y)   | 40 n=53 (5.0/y) | 41 n=37 (3.5/y) | 42 n=31 (8.2/y)  | 47 n=19 (5.2/y) | 54 n=13 (3.6/y) |
| credit_d3m        | 44 n=170 (10.1/y) | 52 n=93 (5.6/y) | 56 n=64 (3.9/y) | 37 n=109 (10.1/y) | 48 n=60 (5.6/y) | 56 n=41 (3.9/y) | 24 n=38 (10.1/y) | 29 n=21 (5.7/y) | 50 n=14 (3.9/y) |
| usfci_d3m         | 51 n=170 (10.1/y) | 55 n=93 (5.6/y) | 59 n=64 (3.9/y) | 50 n=109 (10.1/y) | 52 n=60 (5.6/y) | 61 n=41 (3.9/y) | 45 n=38 (10.1/y) | 48 n=21 (5.7/y) | 57 n=14 (3.9/y) |
| combo_majority    | 50 n=162 (9.7/y)  | 52 n=91 (5.5/y) | 55 n=64 (3.9/y) | 51 n=102 (9.5/y)  | 57 n=58 (5.4/y) | 54 n=41 (3.9/y) | 44 n=36 (9.6/y)  | 38 n=21 (5.7/y) | 36 n=14 (3.9/y) |

### 5c. Paired differences

`paired_weekly`: accuracy(extra-vote rule) - accuracy(agreement rule) on the same weekly grid, circular block bootstrap (block 2h/5 weeks, 2000 draws). `paired_nonoverlap_on_agree3_stream`: on the agreement rule's own non-overlapping decisions, accuracy of those the vote confirms minus all (iid bootstrap over decisions). `acc_dropped` = accuracy of the agreement-rule decisions the vote rejects; `p_diff_le0` = bootstrap share with no improvement.


paired_weekly (points):

| candidate         |   h | period   |   n_agree |   n_extra |   acc_agree |   acc_extra |   acc_dropped |   diff |   diff_lo |   diff_hi |   p_diff_le0 |
|:------------------|----:|:---------|----------:|----------:|------------:|------------:|--------------:|-------:|----------:|----------:|-------------:|
| bs_d3m            |  21 | 2010-26  |       387 |       231 |        59.4 |        61   |          57.1 |    1.6 |      -4.1 |       7.7 |         0.28 |
| bs_d3m            |  21 | 2016-26  |       243 |       134 |        57.2 |        63.4 |          49.5 |    6.2 |      -1.3 |      14.1 |         0.06 |
| bs_d3m            |  42 | 2010-26  |       383 |       231 |        64.8 |        64.9 |          64.5 |    0.2 |      -6.9 |       6.9 |         0.47 |
| bs_d3m            |  42 | 2016-26  |       239 |       134 |        63.2 |        67.9 |          57.1 |    4.7 |      -4.8 |      13.2 |         0.17 |
| bs_d6m            |  21 | 2010-26  |       387 |       230 |        59.4 |        59.1 |          59.9 |   -0.3 |      -6.4 |       5.7 |         0.51 |
| bs_d6m            |  21 | 2016-26  |       243 |       154 |        57.2 |        63.6 |          46.1 |    6.4 |      -0.4 |      13.9 |         0.04 |
| bs_d6m            |  42 | 2010-26  |       383 |       230 |        64.8 |        63.5 |          66.7 |   -1.3 |      -8.8 |       5.6 |         0.64 |
| bs_d6m            |  42 | 2016-26  |       239 |       154 |        63.2 |        68.2 |          54.1 |    5   |      -2.6 |      12.6 |         0.1  |
| bs_d12m           |  21 | 2010-26  |       387 |       206 |        59.4 |        56.8 |          62.4 |   -2.6 |      -9.7 |       4.4 |         0.76 |
| bs_d12m           |  21 | 2016-26  |       243 |       137 |        57.2 |        61.3 |          51.9 |    4.1 |      -4.1 |      12.7 |         0.16 |
| bs_d12m           |  42 | 2010-26  |       383 |       206 |        64.8 |        64.6 |          65   |   -0.2 |      -8.8 |       7.3 |         0.5  |
| bs_d12m           |  42 | 2016-26  |       239 |       137 |        63.2 |        68.6 |          55.9 |    5.4 |      -3.2 |      14.1 |         0.12 |
| money_gap         |  21 | 2010-26  |       387 |       166 |        59.4 |        55.4 |          62.4 |   -4   |     -12.5 |       4   |         0.83 |
| money_gap         |  21 | 2016-26  |       243 |       116 |        57.2 |        54.3 |          59.8 |   -2.9 |     -13.1 |       6.1 |         0.71 |
| money_gap         |  42 | 2010-26  |       383 |       166 |        64.8 |        64.5 |          65   |   -0.3 |     -10.5 |       8.7 |         0.51 |
| money_gap         |  42 | 2016-26  |       239 |       116 |        63.2 |        68.1 |          58.5 |    4.9 |      -6.4 |      14.9 |         0.17 |
| xliq_lvl          |  21 | 2010-26  |       387 |       150 |        59.4 |        60   |          59.1 |    0.6 |      -8.6 |       9.6 |         0.44 |
| xliq_lvl          |  21 | 2016-26  |       243 |        91 |        57.2 |        65.9 |          52   |    8.7 |      -2.8 |      20.2 |         0.07 |
| xliq_lvl          |  42 | 2010-26  |       383 |       150 |        64.8 |        62.7 |          66.1 |   -2.1 |     -13.7 |       8.4 |         0.66 |
| xliq_lvl          |  42 | 2016-26  |       239 |        91 |        63.2 |        65.9 |          61.5 |    2.8 |     -12.1 |      15.7 |         0.34 |
| ciss_diff_lvl     |  21 | 2010-26  |       387 |       178 |        59.4 |        53.9 |          64.1 |   -5.5 |     -13.2 |       1.7 |         0.93 |
| ciss_diff_lvl     |  21 | 2016-26  |       243 |       115 |        57.2 |        57.4 |          57   |    0.2 |      -9.1 |       9.4 |         0.47 |
| ciss_diff_lvl     |  42 | 2010-26  |       383 |       178 |        64.8 |        58.4 |          70.2 |   -6.3 |     -16.7 |       2.6 |         0.91 |
| ciss_diff_lvl     |  42 | 2016-26  |       239 |       115 |        63.2 |        59.1 |          66.9 |   -4   |     -16   |       6   |         0.75 |
| ciss_diff_d1m     |  21 | 2010-26  |       387 |       206 |        59.4 |        59.2 |          59.7 |   -0.2 |      -5.6 |       5   |         0.55 |
| ciss_diff_d1m     |  21 | 2016-26  |       243 |       124 |        57.2 |        58.9 |          55.5 |    1.7 |      -6.1 |       9.2 |         0.33 |
| ciss_diff_d1m     |  42 | 2010-26  |       383 |       202 |        64.8 |        66.3 |          63   |    1.6 |      -3.3 |       6.5 |         0.26 |
| ciss_diff_d1m     |  42 | 2016-26  |       239 |       120 |        63.2 |        65.8 |          60.5 |    2.7 |      -3.8 |       9.1 |         0.2  |
| ciss_diff_d3m     |  21 | 2010-26  |       387 |       216 |        59.4 |        60.2 |          58.5 |    0.8 |      -4.9 |       6.3 |         0.41 |
| ciss_diff_d3m     |  21 | 2016-26  |       243 |       132 |        57.2 |        59.8 |          54.1 |    2.6 |      -4.7 |       9.5 |         0.24 |
| ciss_diff_d3m     |  42 | 2010-26  |       383 |       212 |        64.8 |        67   |          62   |    2.2 |      -3.6 |       8.4 |         0.23 |
| ciss_diff_d3m     |  42 | 2016-26  |       239 |       128 |        63.2 |        65.6 |          60.4 |    2.4 |      -5.1 |       9.8 |         0.27 |
| gstress_hi_rising |  21 | 2010-26  |       387 |       123 |        59.4 |        50.4 |          63.6 |   -9   |     -19.3 |       0.8 |         0.96 |
| gstress_hi_rising |  21 | 2016-26  |       243 |        71 |        57.2 |        49.3 |          60.5 |   -7.9 |     -20.3 |       4.2 |         0.89 |
| gstress_hi_rising |  42 | 2010-26  |       383 |       123 |        64.8 |        52.8 |          70.4 |  -11.9 |     -24.9 |      -0.5 |         0.98 |
| gstress_hi_rising |  42 | 2016-26  |       239 |        71 |        63.2 |        49.3 |          69   |  -13.9 |     -31.7 |       2   |         0.95 |
| credit_d3m        |  21 | 2010-26  |       387 |       205 |        59.4 |        55.1 |          64.3 |   -4.3 |     -11.2 |       2.2 |         0.9  |
| credit_d3m        |  21 | 2016-26  |       243 |       121 |        57.2 |        50.4 |          63.9 |   -6.8 |     -15.9 |       1.4 |         0.94 |
| credit_d3m        |  42 | 2010-26  |       383 |       203 |        64.8 |        60.1 |          70   |   -4.7 |     -12.2 |       2.8 |         0.9  |
| credit_d3m        |  42 | 2016-26  |       239 |       119 |        63.2 |        59.7 |          66.7 |   -3.5 |     -13.7 |       5.4 |         0.77 |
| usfci_d3m         |  21 | 2010-26  |       387 |       207 |        59.4 |        58.9 |          60   |   -0.5 |      -6.5 |       5.8 |         0.55 |
| usfci_d3m         |  21 | 2016-26  |       243 |       127 |        57.2 |        56.7 |          57.8 |   -0.5 |      -7.4 |       7.4 |         0.55 |
| usfci_d3m         |  42 | 2010-26  |       383 |       205 |        64.8 |        62.4 |          67.4 |   -2.3 |      -9.9 |       4.3 |         0.74 |
| usfci_d3m         |  42 | 2016-26  |       239 |       125 |        63.2 |        60   |          66.7 |   -3.2 |     -13.4 |       4.6 |         0.78 |
| combo_majority    |  21 | 2010-26  |       387 |       186 |        59.4 |        59.1 |          59.7 |   -0.3 |      -7.1 |       6.5 |         0.52 |
| combo_majority    |  21 | 2016-26  |       243 |       112 |        57.2 |        67.9 |          48.1 |   10.7 |       2.6 |      19.2 |         0.01 |
| combo_majority    |  42 | 2010-26  |       383 |       186 |        64.8 |        61.3 |          68   |   -3.5 |     -11.7 |       4.2 |         0.81 |
| combo_majority    |  42 | 2016-26  |       239 |       112 |        63.2 |        67.9 |          59.1 |    4.7 |      -3.7 |      13.2 |         0.14 |

paired_nonoverlap_on_agree3_stream (points):

| candidate         |   h | period   |   n_agree |   n_extra |   acc_agree |   acc_extra |   acc_dropped |   diff |   diff_lo |   diff_hi |   p_diff_le0 |
|:------------------|----:|:---------|----------:|----------:|------------:|------------:|--------------:|-------:|----------:|----------:|-------------:|
| bs_d3m            |  21 | 2010-26  |       156 |        87 |        59   |        59.8 |          58   |    0.8 |      -6.2 |       7.7 |         0.42 |
| bs_d3m            |  21 | 2016-26  |        96 |        47 |        57.3 |        59.6 |          55.1 |    2.3 |      -7.4 |      12.9 |         0.33 |
| bs_d3m            |  42 | 2010-26  |        89 |        44 |        60.7 |        59.1 |          62.2 |   -1.6 |     -11.8 |       8.8 |         0.61 |
| bs_d3m            |  42 | 2016-26  |        56 |        24 |        58.9 |        58.3 |          59.4 |   -0.6 |     -16.1 |      14.9 |         0.54 |
| bs_d6m            |  21 | 2010-26  |       156 |        87 |        59   |        56.3 |          62.3 |   -2.7 |      -9.7 |       4   |         0.78 |
| bs_d6m            |  21 | 2016-26  |        96 |        54 |        57.3 |        57.4 |          57.1 |    0.1 |      -8.6 |       8.9 |         0.49 |
| bs_d6m            |  42 | 2010-26  |        89 |        46 |        60.7 |        56.5 |          65.1 |   -4.2 |     -14   |       5.8 |         0.8  |
| bs_d6m            |  42 | 2016-26  |        56 |        29 |        58.9 |        58.6 |          59.3 |   -0.3 |     -13.7 |      12.5 |         0.52 |
| bs_d12m           |  21 | 2010-26  |       156 |        82 |        59   |        53.7 |          64.9 |   -5.3 |     -12.9 |       2   |         0.93 |
| bs_d12m           |  21 | 2016-26  |        96 |        52 |        57.3 |        55.8 |          59.1 |   -1.5 |     -10.5 |       7.8 |         0.62 |
| bs_d12m           |  42 | 2010-26  |        89 |        44 |        60.7 |        63.6 |          57.8 |    3   |      -7   |      14   |         0.28 |
| bs_d12m           |  42 | 2016-26  |        56 |        29 |        58.9 |        69   |          48.1 |   10   |      -2.7 |      23.2 |         0.07 |
| money_gap         |  21 | 2010-26  |       156 |        72 |        59   |        54.2 |          63.1 |   -4.8 |     -13.1 |       3.4 |         0.88 |
| money_gap         |  21 | 2016-26  |        96 |        48 |        57.3 |        54.2 |          60.4 |   -3.1 |     -13.5 |       6.8 |         0.73 |
| money_gap         |  42 | 2010-26  |        89 |        40 |        60.7 |        60   |          61.2 |   -0.7 |     -12.2 |      10.3 |         0.56 |
| money_gap         |  42 | 2016-26  |        56 |        27 |        58.9 |        59.3 |          58.6 |    0.3 |     -13.5 |      14   |         0.49 |
| xliq_lvl          |  21 | 2010-26  |       156 |        72 |        59   |        61.1 |          57.1 |    2.1 |      -6.3 |      10.6 |         0.31 |
| xliq_lvl          |  21 | 2016-26  |        96 |        45 |        57.3 |        68.9 |          47.1 |   11.6 |       1   |      22.3 |         0.02 |
| xliq_lvl          |  42 | 2010-26  |        89 |        39 |        60.7 |        61.5 |          60   |    0.9 |     -10.7 |      12.6 |         0.45 |
| xliq_lvl          |  42 | 2016-26  |        56 |        24 |        58.9 |        62.5 |          56.2 |    3.6 |     -11.9 |      18.5 |         0.33 |
| ciss_diff_lvl     |  21 | 2010-26  |       156 |        69 |        59   |        55.1 |          62.1 |   -3.9 |     -13   |       4.5 |         0.82 |
| ciss_diff_lvl     |  21 | 2016-26  |        96 |        39 |        57.3 |        56.4 |          57.9 |   -0.9 |     -13.7 |      11.7 |         0.55 |
| ciss_diff_lvl     |  42 | 2010-26  |        89 |        39 |        60.7 |        51.3 |          68   |   -9.4 |     -21.3 |       2.1 |         0.94 |
| ciss_diff_lvl     |  42 | 2016-26  |        56 |        20 |        58.9 |        50   |          63.9 |   -8.9 |     -27.4 |       8.9 |         0.84 |
| ciss_diff_d1m     |  21 | 2010-26  |       156 |        76 |        59   |        55.3 |          62.5 |   -3.7 |     -11.8 |       4.4 |         0.82 |
| ciss_diff_d1m     |  21 | 2016-26  |        96 |        50 |        57.3 |        54   |          60.9 |   -3.3 |     -12.9 |       6.2 |         0.75 |
| ciss_diff_d1m     |  42 | 2010-26  |        89 |        35 |        60.7 |        54.3 |          64.8 |   -6.4 |     -19.2 |       6.6 |         0.83 |
| ciss_diff_d1m     |  42 | 2016-26  |        56 |        21 |        58.9 |        47.6 |          65.7 |  -11.3 |     -29   |       5.5 |         0.91 |
| ciss_diff_d3m     |  21 | 2010-26  |       156 |        76 |        59   |        52.6 |          65   |   -6.3 |     -14.3 |       1.6 |         0.94 |
| ciss_diff_d3m     |  21 | 2016-26  |        96 |        43 |        57.3 |        51.2 |          62.3 |   -6.1 |     -17.5 |       5.3 |         0.85 |
| ciss_diff_d3m     |  42 | 2010-26  |        89 |        41 |        60.7 |        61   |          60.4 |    0.3 |     -10.9 |      11.6 |         0.47 |
| ciss_diff_d3m     |  42 | 2016-26  |        56 |        21 |        58.9 |        52.4 |          62.9 |   -6.5 |     -23.9 |      10.1 |         0.78 |
| gstress_hi_rising |  21 | 2010-26  |       156 |        51 |        59   |        51   |          62.9 |   -8   |     -19.6 |       3.3 |         0.92 |
| gstress_hi_rising |  21 | 2016-26  |        96 |        29 |        57.3 |        48.3 |          61.2 |   -9   |     -24.8 |       6.7 |         0.87 |
| gstress_hi_rising |  42 | 2010-26  |        89 |        25 |        60.7 |        44   |          67.2 |  -16.7 |     -33.5 |       0   |         0.97 |
| gstress_hi_rising |  42 | 2016-26  |        56 |        15 |        58.9 |        33.3 |          68.3 |  -25.6 |     -48.2 |      -3.6 |         0.99 |
| credit_d3m        |  21 | 2010-26  |       156 |        84 |        59   |        54.8 |          63.9 |   -4.2 |     -11.5 |       3   |         0.88 |
| credit_d3m        |  21 | 2016-26  |        96 |        50 |        57.3 |        52   |          63   |   -5.3 |     -15   |       4.2 |         0.86 |
| credit_d3m        |  42 | 2010-26  |        89 |        49 |        60.7 |        63.3 |          57.5 |    2.6 |      -6.4 |      11.6 |         0.3  |
| credit_d3m        |  42 | 2016-26  |        56 |        31 |        58.9 |        61.3 |          56   |    2.4 |      -9.4 |      14.3 |         0.35 |
| usfci_d3m         |  21 | 2010-26  |       156 |        82 |        59   |        58.5 |          59.5 |   -0.4 |      -8.2 |       7.3 |         0.55 |
| usfci_d3m         |  21 | 2016-26  |        96 |        49 |        57.3 |        57.1 |          57.4 |   -0.1 |      -9.6 |       9.6 |         0.5  |
| usfci_d3m         |  42 | 2010-26  |        89 |        51 |        60.7 |        60.8 |          60.5 |    0.1 |      -8.9 |       9.1 |         0.5  |
| usfci_d3m         |  42 | 2016-26  |        56 |        32 |        58.9 |        59.4 |          58.3 |    0.4 |     -10.9 |      11.9 |         0.5  |
| combo_majority    |  21 | 2010-26  |       156 |        70 |        59   |        52.9 |          64   |   -6.1 |     -15.2 |       2.5 |         0.92 |
| combo_majority    |  21 | 2016-26  |        96 |        38 |        57.3 |        52.6 |          60.3 |   -4.7 |     -17.2 |       8   |         0.76 |
| combo_majority    |  42 | 2010-26  |        89 |        36 |        60.7 |        52.8 |          66   |   -7.9 |     -20.7 |       4.6 |         0.89 |
| combo_majority    |  42 | 2016-26  |        56 |        22 |        58.9 |        54.5 |          61.8 |   -4.4 |     -21.4 |      13.1 |         0.7  |

## 6. Selection and the success bar

Declared rule: highest lower Wilson bound of the 2010-15 non-overlapping 21-session accuracy of the extra-vote rule among candidates with >= 6 such decisions a year. Result: **`ciss_diff_d3m`** (selected by the declared rule).

| candidate         |   n |   dec_per_year |   accuracy |   lo |   hi |   agree_accuracy |   agree_dec_per_year |   gain_pts | eligible   | final   |
|:------------------|----:|---------------:|-----------:|-----:|-----:|-----------------:|---------------------:|-----------:|:-----------|:--------|
| ciss_diff_d3m     |  45 |           7.52 |       60   | 45.5 | 73   |             61.7 |                10.02 |      -1.67 | True       | True    |
| credit_d3m        |  39 |           6.51 |       59   | 43.4 | 72.9 |             61.7 |                10.02 |      -2.69 | True       | False   |
| usfci_d3m         |  41 |           6.85 |       58.5 | 43.4 | 72.2 |             61.7 |                10.02 |      -3.13 | True       | False   |
| ciss_diff_d1m     |  39 |           6.51 |       53.8 | 38.6 | 68.4 |             61.7 |                10.02 |      -7.82 | True       | False   |
| ciss_diff_lvl     |  32 |           5.34 |       53.1 | 36.4 | 69.1 |             61.7 |                10.02 |      -8.54 | False      | False   |
| bs_d3m            |  45 |           7.52 |       46.7 | 32.9 | 60.9 |             61.7 |                10.02 |     -15    | True       | False   |
| gstress_hi_rising |  26 |           4.34 |       50   | 32.1 | 67.9 |             61.7 |                10.02 |     -11.67 | False      | False   |
| combo_majority    |  41 |           6.85 |       46.3 | 32.1 | 61.3 |             61.7 |                10.02 |     -15.33 | True       | False   |
| money_gap         |  27 |           4.51 |       48.1 | 30.7 | 66   |             61.7 |                10.02 |     -13.52 | False      | False   |
| bs_d6m            |  38 |           6.35 |       39.5 | 25.6 | 55.3 |             61.7 |                10.02 |     -22.19 | True       | False   |
| bs_d12m           |  36 |           6.01 |       36.1 | 22.5 | 52.4 |             61.7 |                10.02 |     -25.56 | True       | False   |
| xliq_lvl          |  30 |           5.01 |       36.7 | 21.9 | 54.5 |             61.7 |                10.02 |     -25    | False      | False   |

The bar for `ciss_diff_d3m` (non-overlapping decisions; accuracies in %, gains in points):

|   h | period   |   agree_acc |   agree_n |   agree_per_year |   extra_acc |   extra_lo |   extra_hi |   extra_n |   extra_per_year |   gain_pts |   placebo63_gain_pts |   placebo63_n |   placebo126_gain_pts |   placebo126_n |
|----:|:---------|------------:|----------:|-----------------:|------------:|-----------:|-----------:|----------:|-----------------:|-----------:|---------------------:|--------------:|----------------------:|---------------:|
|  21 | 2010-26  |        59   |       156 |              9.3 |        55   |       45.7 |       63.9 |       111 |              6.6 |       -4   |                  2.8 |           115 |                  -3.9 |            109 |
|  21 | 2016-26  |        57.3 |        96 |              8.9 |        51.5 |       39.7 |       63.2 |        66 |              6.1 |       -5.8 |                  9.4 |            75 |                  -0.8 |             69 |
|  21 | 2023-26  |        60   |        35 |              9.3 |        60   |       38.7 |       78.1 |        20 |              5.3 |        0   |                  2.5 |            24 |                 -13.8 |             26 |
|  42 | 2010-26  |        60.7 |        89 |              5.3 |        60.6 |       48.9 |       71.1 |        71 |              4.3 |       -0.1 |                  8.3 |            71 |                   5.1 |             73 |
|  42 | 2016-26  |        58.9 |        56 |              5.2 |        60.5 |       45.6 |       73.6 |        43 |              4   |        1.5 |                 16.6 |            45 |                   8.5 |             46 |
|  42 | 2023-26  |        45   |        20 |              5.4 |        53.3 |       30.1 |       75.2 |        15 |              4.1 |        8.3 |                 33.6 |            14 |                  -0.6 |             18 |
|  63 | 2010-26  |        72.1 |        61 |              3.7 |        67.3 |       53.4 |       78.8 |        49 |              3   |       -4.8 |                 -2.3 |            53 |                 -16.4 |             52 |
|  63 | 2016-26  |        71.1 |        38 |              3.6 |        72.4 |       54.3 |       85.3 |        29 |              2.7 |        1.4 |                  1.7 |            33 |                 -10.4 |             33 |
|  63 | 2023-26  |        50   |        14 |              3.9 |        70   |       39.7 |       89.2 |        10 |              2.8 |       20   |                 13.6 |            11 |                 -16.7 |             12 |

* gain>=3 at 21 and 42, 2010-26: **NO**
* gain>=3 at 21 and 42, 2016-26: **NO**
* >=6 decisions/yr (21-session non-overlapping), 2010-26 and 2016-26: **yes**
* 2023-26 not worse at 21 and 42: **yes**
* placebo (+63 and +126) loses >= half of the gain at 21 and 42, 2010-26: **NO**
* BAR MET: **NO**

Note on the count condition: a 42-session non-overlapping stream cannot exceed 6 decisions a year, and the agreement rule itself has 5.3; the count is therefore tested on the 21-session stream only (fixed before results). The '2023-26 not worse' line is met on 20 and 15 decisions and means nothing by itself.

Decisions of `ciss_diff_d3m` (extra-vote rule, weekly, 21-session hold) by year:

|   year |   decisions |   long_share |   accuracy |   net_win_rate |   net_bp |
|-------:|------------:|-------------:|-----------:|---------------:|---------:|
|   2010 |          15 |         0.47 |       0.53 |           0.53 |   117.21 |
|   2011 |          16 |         0.38 |       0.62 |           0.62 |   132.14 |
|   2012 |          15 |         0.53 |       0.6  |           0.6  |    36.39 |
|   2013 |           7 |         1    |       0.43 |           0.43 |  -119.12 |
|   2014 |          16 |         0.19 |       0.81 |           0.81 |   114.35 |
|   2015 |          15 |         0.2  |       0.53 |           0.53 |   -41.25 |
|   2016 |          10 |         0.6  |       0.6  |           0.6  |     3.54 |
|   2017 |          19 |         1    |       0.68 |           0.68 |   113.05 |
|   2018 |           9 |         0    |       0.67 |           0.67 |    50.69 |
|   2019 |           5 |         1    |       0.8  |           0.8  |    -3.13 |
|   2020 |          17 |         1    |       0.41 |           0.41 |    -2.13 |
|   2021 |          14 |         0.14 |       0.5  |           0.5  |     9.62 |
|   2022 |          19 |         0.26 |       0.74 |           0.74 |   129.54 |
|   2023 |          13 |         0.85 |       0.46 |           0.46 |   -12.17 |
|   2024 |           8 |         0    |       0.62 |           0.62 |    87.73 |
|   2025 |           9 |         1    |       0.67 |           0.67 |    79.03 |
|   2026 |           9 |         0.44 |       0.56 |           0.56 |     4.58 |

Hit rates of the final rule at 21 sessions (round-4 format: share with the correct sign before costs, share with positive net P&L):

| mode       | period   |   n |   dec_per_year |   right_sign_% |   net_win_% |   gross_bp |   net_bp |   share_long |   chance_acc |
|:-----------|:---------|----:|---------------:|---------------:|------------:|-----------:|---------:|-------------:|-------------:|
| weekly     | 2010-26  | 216 |          12.91 |           60.2 |        60.2 |      54.24 |    52.2  |         0.52 |         0.5  |
| weekly     | 2016-26  | 132 |          12.29 |           59.8 |        59.8 |      51.24 |    49.09 |         0.59 |         0.5  |
| weekly     | 2023-26  |  39 |          10.44 |           56.4 |        56.4 |      35.39 |    33.23 |         0.62 |         0.51 |
| nonoverlap | 2010-26  | 111 |           6.62 |           55   |        55   |      42.13 |    40.1  |         0.52 |         0.5  |
| nonoverlap | 2016-26  |  66 |           6.13 |           51.5 |        51.5 |      19.86 |    17.71 |         0.56 |         0.5  |
| nonoverlap | 2023-26  |  20 |           5.31 |           60   |        60   |      41.91 |    39.75 |         0.5  |         0.5  |

## 7. Timing placebo (the vote made 63 and 126 sessions staler), extra-vote rule, non-overlapping


Placebo +63 sessions (% right, decisions, per year):

| candidate         | 2010-26 / 21s    | 2010-26 / 42s   | 2010-26 / 63s   | 2016-26 / 21s   | 2016-26 / 42s   | 2016-26 / 63s   | 2023-26 / 21s   | 2023-26 / 42s   | 2023-26 / 63s   |
|:------------------|:-----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|
| bs_d3m            | 55 n=97 (5.8/y)  | 60 n=58 (3.5/y) | 67 n=42 (2.5/y) | 65 n=63 (5.9/y) | 63 n=38 (3.6/y) | 69 n=26 (2.5/y) | 67 n=24 (6.4/y) | 60 n=15 (4.1/y) | 50 n=10 (2.8/y) |
| bs_d6m            | 55 n=91 (5.4/y)  | 60 n=53 (3.2/y) | 71 n=38 (2.3/y) | 59 n=63 (5.9/y) | 65 n=37 (3.5/y) | 77 n=26 (2.5/y) | 55 n=22 (5.8/y) | 46 n=13 (3.5/y) | 60 n=10 (2.8/y) |
| bs_d12m           | 54 n=78 (4.7/y)  | 63 n=49 (2.9/y) | 74 n=35 (2.1/y) | 65 n=51 (4.7/y) | 66 n=32 (3.0/y) | 82 n=22 (2.1/y) | 62 n=13 (3.5/y) | 33 n=9 (2.4/y)  | 43 n=7 (1.9/y)  |
| money_gap         | 53 n=78 (4.7/y)  | 62 n=50 (3.0/y) | 74 n=34 (2.0/y) | 56 n=50 (4.6/y) | 61 n=33 (3.1/y) | 77 n=22 (2.1/y) | 57 n=21 (5.6/y) | 54 n=13 (3.5/y) | 56 n=9 (2.5/y)  |
| xliq_lvl          | 59 n=76 (4.5/y)  | 61 n=46 (2.8/y) | 73 n=33 (2.0/y) | 66 n=47 (4.4/y) | 59 n=29 (2.7/y) | 76 n=21 (2.0/y) | 62 n=21 (5.6/y) | 46 n=13 (3.5/y) | 70 n=10 (2.8/y) |
| ciss_diff_lvl     | 57 n=82 (4.9/y)  | 65 n=51 (3.1/y) | 63 n=38 (2.3/y) | 63 n=52 (4.8/y) | 66 n=32 (3.0/y) | 67 n=24 (2.3/y) | 68 n=22 (5.8/y) | 62 n=13 (3.5/y) | 45 n=11 (3.1/y) |
| ciss_diff_d1m     | 61 n=121 (7.2/y) | 67 n=75 (4.5/y) | 71 n=55 (3.3/y) | 63 n=78 (7.2/y) | 68 n=47 (4.4/y) | 73 n=33 (3.1/y) | 64 n=28 (7.4/y) | 53 n=17 (4.6/y) | 64 n=11 (3.1/y) |
| ciss_diff_d3m     | 62 n=115 (6.9/y) | 69 n=71 (4.3/y) | 70 n=53 (3.2/y) | 67 n=75 (7.0/y) | 76 n=45 (4.2/y) | 73 n=33 (3.1/y) | 62 n=24 (6.4/y) | 79 n=14 (3.8/y) | 64 n=11 (3.1/y) |
| gstress_hi_rising | 48 n=62 (3.7/y)  | 57 n=44 (2.6/y) | 64 n=33 (2.0/y) | 51 n=35 (3.3/y) | 56 n=25 (2.3/y) | 60 n=20 (1.9/y) | 57 n=14 (3.7/y) | 55 n=11 (3.0/y) | 50 n=8 (2.2/y)  |
| credit_d3m        | 51 n=89 (5.3/y)  | 64 n=59 (3.5/y) | 72 n=43 (2.6/y) | 55 n=55 (5.1/y) | 65 n=37 (3.5/y) | 70 n=27 (2.5/y) | 65 n=17 (4.5/y) | 58 n=12 (3.3/y) | 67 n=9 (2.5/y)  |
| usfci_d3m         | 64 n=101 (6.0/y) | 66 n=61 (3.7/y) | 74 n=47 (2.8/y) | 68 n=62 (5.8/y) | 68 n=37 (3.5/y) | 76 n=29 (2.7/y) | 70 n=20 (5.3/y) | 67 n=12 (3.3/y) | 67 n=9 (2.5/y)  |
| combo_majority    | 59 n=87 (5.2/y)  | 64 n=55 (3.3/y) | 78 n=40 (2.4/y) | 68 n=56 (5.2/y) | 69 n=35 (3.3/y) | 85 n=26 (2.5/y) | 68 n=19 (5.0/y) | 55 n=11 (3.0/y) | 67 n=9 (2.5/y)  |

Gain over the agreement rule with the +63 placebo (points):

| candidate         |   2010-26 / 21s |   2010-26 / 42s |   2010-26 / 63s |   2016-26 / 21s |   2016-26 / 42s |   2016-26 / 63s |   2023-26 / 21s |   2023-26 / 42s |   2023-26 / 63s |
|:------------------|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|
| bs_d3m            |            -4.3 |            -0.3 |            -5.5 |             7.8 |             4.2 |            -1.8 |             6.7 |            15   |             0   |
| bs_d6m            |            -4   |            -0.3 |            -1.1 |             1.4 |             5.9 |             5.9 |            -5.5 |             1.2 |            10   |
| bs_d12m           |            -5.1 |             2.6 |             2.2 |             7.4 |             6.7 |            10.8 |             1.5 |           -11.7 |            -7.1 |
| money_gap         |            -6.4 |             1.3 |             1.4 |            -1.3 |             1.7 |             6.2 |            -2.9 |             8.8 |             5.6 |
| xliq_lvl          |             0.2 |             0.2 |             0.6 |             8.7 |            -0.3 |             5.1 |             1.9 |             1.2 |            20   |
| ciss_diff_lvl     |            -1.7 |             4   |            -9   |             6.2 |             6.7 |            -4.4 |             8.2 |            16.5 |            -4.5 |
| ciss_diff_d1m     |             2.2 |             6   |            -1.2 |             5.5 |             9.2 |             1.7 |             4.3 |             7.9 |            13.6 |
| ciss_diff_d3m     |             2.8 |             8.3 |            -2.3 |             9.4 |            16.6 |             1.7 |             2.5 |            33.6 |            13.6 |
| gstress_hi_rising |           -10.6 |            -3.9 |            -8.5 |            -5.9 |            -2.9 |           -11.1 |            -2.9 |             9.5 |             0   |
| credit_d3m        |            -8.4 |             3.7 |            -0   |            -2.7 |             5.9 |            -0.7 |             4.7 |            13.3 |            16.7 |
| usfci_d3m         |             5.4 |             4.9 |             2.3 |            10.5 |             8.6 |             4.8 |            10   |            21.7 |            16.7 |
| combo_majority    |            -0.4 |             3   |             5.4 |            10.6 |             9.6 |            13.6 |             8.4 |             9.5 |            16.7 |

Placebo +126 sessions (% right, decisions, per year):

| candidate         | 2010-26 / 21s    | 2010-26 / 42s   | 2010-26 / 63s   | 2016-26 / 21s   | 2016-26 / 42s   | 2016-26 / 63s   | 2023-26 / 21s   | 2023-26 / 42s   | 2023-26 / 63s   |
|:------------------|:-----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|:----------------|
| bs_d3m            | 60 n=87 (5.2/y)  | 69 n=55 (3.3/y) | 77 n=39 (2.3/y) | 62 n=58 (5.4/y) | 70 n=37 (3.5/y) | 80 n=25 (2.4/y) | 47 n=19 (5.0/y) | 46 n=13 (3.5/y) | 60 n=10 (2.8/y) |
| bs_d6m            | 56 n=85 (5.1/y)  | 67 n=54 (3.2/y) | 79 n=38 (2.3/y) | 60 n=58 (5.4/y) | 69 n=36 (3.4/y) | 84 n=25 (2.4/y) | 56 n=18 (4.8/y) | 50 n=12 (3.3/y) | 56 n=9 (2.5/y)  |
| bs_d12m           | 52 n=67 (4.0/y)  | 68 n=41 (2.5/y) | 73 n=33 (2.0/y) | 58 n=43 (4.0/y) | 69 n=26 (2.4/y) | 85 n=20 (1.9/y) | 36 n=11 (2.9/y) | 43 n=7 (1.9/y)  | 50 n=6 (1.7/y)  |
| money_gap         | 51 n=77 (4.6/y)  | 66 n=47 (2.8/y) | 74 n=34 (2.0/y) | 53 n=47 (4.4/y) | 67 n=30 (2.8/y) | 81 n=21 (2.0/y) | 47 n=17 (4.5/y) | 50 n=10 (2.7/y) | 57 n=7 (1.9/y)  |
| xliq_lvl          | 55 n=76 (4.5/y)  | 61 n=46 (2.8/y) | 66 n=35 (2.1/y) | 59 n=51 (4.7/y) | 59 n=32 (3.0/y) | 70 n=23 (2.2/y) | 50 n=22 (5.8/y) | 43 n=14 (3.8/y) | 60 n=10 (2.8/y) |
| ciss_diff_lvl     | 49 n=77 (4.6/y)  | 51 n=51 (3.1/y) | 47 n=36 (2.2/y) | 49 n=43 (4.0/y) | 47 n=30 (2.8/y) | 41 n=22 (2.1/y) | 56 n=18 (4.8/y) | 38 n=13 (3.5/y) | 22 n=9 (2.5/y)  |
| ciss_diff_d1m     | 56 n=116 (6.9/y) | 64 n=81 (4.9/y) | 72 n=53 (3.2/y) | 56 n=75 (7.0/y) | 67 n=51 (4.8/y) | 68 n=34 (3.2/y) | 50 n=26 (6.9/y) | 47 n=19 (5.2/y) | 58 n=12 (3.3/y) |
| ciss_diff_d3m     | 55 n=109 (6.5/y) | 66 n=73 (4.4/y) | 56 n=52 (3.1/y) | 57 n=69 (6.4/y) | 67 n=46 (4.3/y) | 61 n=33 (3.1/y) | 46 n=26 (6.9/y) | 44 n=18 (4.9/y) | 33 n=12 (3.3/y) |
| gstress_hi_rising | 40 n=63 (3.8/y)  | 57 n=42 (2.5/y) | 50 n=32 (1.9/y) | 43 n=37 (3.4/y) | 58 n=24 (2.2/y) | 56 n=18 (1.7/y) | 54 n=13 (3.5/y) | 44 n=9 (2.4/y)  | 29 n=7 (1.9/y)  |
| credit_d3m        | 52 n=97 (5.8/y)  | 56 n=62 (3.7/y) | 64 n=44 (2.7/y) | 58 n=60 (5.6/y) | 60 n=40 (3.7/y) | 67 n=27 (2.5/y) | 69 n=26 (6.9/y) | 53 n=17 (4.6/y) | 55 n=11 (3.1/y) |
| usfci_d3m         | 49 n=99 (5.9/y)  | 58 n=62 (3.7/y) | 60 n=48 (2.9/y) | 50 n=60 (5.6/y) | 58 n=38 (3.6/y) | 59 n=29 (2.7/y) | 48 n=25 (6.6/y) | 31 n=16 (4.3/y) | 45 n=11 (3.1/y) |
| combo_majority    | 51 n=77 (4.6/y)  | 61 n=51 (3.1/y) | 73 n=37 (2.2/y) | 58 n=48 (4.5/y) | 58 n=33 (3.1/y) | 78 n=23 (2.2/y) | 44 n=18 (4.8/y) | 38 n=13 (3.5/y) | 56 n=9 (2.5/y)  |

Gain over the agreement rule with the +126 placebo (points):

| candidate         |   2010-26 / 21s |   2010-26 / 42s |   2010-26 / 63s |   2016-26 / 21s |   2016-26 / 42s |   2016-26 / 63s |   2023-26 / 21s |   2023-26 / 42s |   2023-26 / 63s |
|:------------------|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|----------------:|
| bs_d3m            |             0.8 |             8.4 |             4.8 |             4.8 |            11.3 |             8.9 |           -12.6 |             1.2 |            10   |
| bs_d6m            |            -2.5 |             6   |             6.8 |             3.1 |            10.5 |            12.9 |            -4.4 |             5   |             5.6 |
| bs_d12m           |            -6.7 |             7.6 |             0.6 |             0.8 |            10.3 |            13.9 |           -23.6 |            -2.1 |             0   |
| money_gap         |            -8.3 |             5.3 |             1.4 |            -4.1 |             7.7 |             9.9 |           -12.9 |             5   |             7.1 |
| xliq_lvl          |            -3.7 |             0.2 |            -6.4 |             1.5 |             0.4 |            -1.5 |           -10   |            -2.1 |            10   |
| ciss_diff_lvl     |            -9.6 |            -9.7 |           -24.9 |            -8.5 |           -12.3 |           -30.1 |            -4.4 |            -6.5 |           -27.8 |
| ciss_diff_d1m     |            -2.9 |             3.5 |            -0.4 |            -1.3 |             7.7 |            -3.4 |           -10   |             2.4 |             8.3 |
| ciss_diff_d3m     |            -3.9 |             5.1 |           -16.4 |            -0.8 |             8.5 |           -10.4 |           -13.8 |            -0.6 |           -16.7 |
| gstress_hi_rising |           -19.3 |            -3.5 |           -22.1 |           -14   |            -0.6 |           -15.5 |            -6.2 |            -0.6 |           -21.4 |
| credit_d3m        |            -7.4 |            -4.2 |            -8.5 |             1   |             1.1 |            -4.4 |             9.2 |             7.9 |             4.5 |
| usfci_d3m         |            -9.5 |            -2.6 |           -11.7 |            -7.3 |            -1   |           -12.4 |           -12   |           -13.8 |            -4.5 |
| combo_majority    |            -8.3 |             0.1 |             0.8 |             1   |            -1.4 |             7.2 |           -15.6 |            -6.5 |             5.6 |

## 8. Daily-stream incremental test (round-3 addendum) and protocol table

Net Sharpe at 1.2 pips of the weekly-tranche 21-session book of each extra-vote rule (the agreement rule's own book first):

| variant                          |   2010-2026 |   2016-2026 |   2023-2026 |   2010-2015 |   t 2010-2026 |
|:---------------------------------|------------:|------------:|------------:|------------:|--------------:|
| agree3_baseline                  |        0.52 |        0.51 |        0.43 |        0.56 |          2.17 |
| extra_vote_bs_d3m                |        0.41 |        0.46 |        0.26 |        0.39 |          1.71 |
| extra_vote_bs_d6m                |        0.29 |        0.57 |        0.49 |       -0.05 |          1.22 |
| extra_vote_bs_d12m               |        0.26 |        0.54 |        0.65 |       -0.11 |          1.09 |
| extra_vote_money_gap             |        0.16 |        0.21 |        0.27 |        0.08 |          0.66 |
| extra_vote_xliq_lvl              |        0.29 |        0.49 |        0.77 |        0.04 |          1.19 |
| extra_vote_ciss_diff_lvl         |        0.17 |        0.4  |       -0.01 |       -0.08 |          0.71 |
| extra_vote_ciss_diff_d1m         |        0.41 |        0.44 |        0.3  |        0.42 |          1.73 |
| extra_vote_ciss_diff_d3m         |        0.46 |        0.51 |        0.42 |        0.44 |          1.93 |
| extra_vote_gstress_hi_rising     |        0.01 |        0.06 |       -0.1  |       -0.03 |          0.05 |
| extra_vote_credit_d3m            |        0.31 |        0.23 |       -0.37 |        0.43 |          1.3  |
| extra_vote_usfci_d3m             |        0.39 |        0.37 |       -0.07 |        0.44 |          1.63 |
| extra_vote_combo_majority        |        0.26 |        0.62 |        0.47 |       -0.13 |          1.09 |
| extra_vote_ciss_diff_d3m_cost0.6 |        0.47 |        0.52 |        0.43 |        0.45 |          1.97 |

Final book `extra_vote_ciss_diff_d3m` per year (deflated-Sharpe p for 12 candidates: 0.40):

| period    |    n |   sharpe |     t |   mean_bp |   sum_bp |   active_frac |
|:----------|-----:|---------:|------:|----------:|---------:|--------------:|
| 2010      |  260 |     0.78 |  0.8  |      1.35 |   351.64 |          0.55 |
| 2011      |  260 |     0.87 |  0.88 |      1.54 |   400.31 |          0.59 |
| 2012      |  260 |     0.57 |  0.58 |      0.55 |   142.53 |          0.67 |
| 2013      |  259 |    -0.97 | -0.99 |     -0.69 |  -177.57 |          0.33 |
| 2014      |  258 |     1.35 |  1.36 |      1.42 |   365.86 |          0.49 |
| 2015      |  259 |    -0.24 | -0.24 |     -0.44 |  -114.93 |          0.59 |
| 2016      |  259 |     0.12 |  0.12 |      0.11 |    27.51 |          0.47 |
| 2017      |  259 |     1.25 |  1.27 |      1.55 |   400.35 |          0.64 |
| 2018      |  260 |     0.45 |  0.46 |      0.35 |    91.23 |          0.32 |
| 2019      |  260 |     0.68 |  0.69 |      0.16 |    42.89 |          0.14 |
| 2020      |  260 |    -0.05 | -0.05 |     -0.04 |   -11.3  |          0.65 |
| 2021      |  259 |     0.05 |  0.05 |      0.04 |     9.42 |          0.59 |
| 2022      |  260 |     1.11 |  1.13 |      1.41 |   367.2  |          0.66 |
| 2023      |  258 |     0.21 |  0.22 |      0.27 |    68.91 |          0.45 |
| 2024      |  261 |     0.89 |  0.91 |      0.57 |   148.87 |          0.46 |
| 2025      |  260 |     0.77 |  0.79 |      0.5  |   129.21 |          0.36 |
| 2026      |  220 |     0.07 |  0.07 |      0.06 |    12.77 |          0.49 |
| 2010-2026 | 4372 |     0.46 |  1.93 |      0.52 |  2254.89 |          0.5  |
| 2016-2026 | 2816 |     0.51 |  1.7  |      0.46 |  1287.05 |          0.48 |
| 2023-2026 |  999 |     0.42 |  0.83 |      0.36 |   359.76 |          0.44 |
| 2010-2015 | 1556 |     0.44 |  1.09 |      0.62 |   967.84 |          0.54 |
| 2016-2022 | 1817 |     0.56 |  1.5  |      0.51 |   927.29 |          0.5  |

Combination test, `meta.combine(..., 'EW')`:

| combo                     | period    |   sharpe |     t |   mean_bp |
|:--------------------------|:----------|---------:|------:|----------:|
| weak_signals+regime_trend | 2010-2026 |    0.563 | 2.347 |     0.583 |
| weak_signals+regime_trend | 2016-2026 |    0.636 | 2.128 |     0.738 |
| weak_signals+regime_trend | 2023-2026 |    0.356 | 0.708 |     0.42  |
| +liquidity_stress         | 2010-2026 |    0.559 | 2.329 |     0.521 |
| +liquidity_stress         | 2016-2026 |    0.668 | 2.235 |     0.685 |
| +liquidity_stress         | 2023-2026 |    0.41  | 0.816 |     0.442 |

Daily P&L correlation of the final book, 2010-26: `weak_signals` 0.31, `regime_trend` 0.51, agreement-rule book (`selective_daily`) 0.82.

## 9. Leak checks

No model is fitted in this arm (fixed sign rules; expanding or trailing statistics use data stamped up to each observation; the house score inside the agreement rule is the selective arm's walk-forward fit). Non-overlapping accuracy, 2010-26 (% right, decisions):

| check                            | agree3:agree3 21s   | agree3:agree3 42s   | extra_vote:ciss_diff_d3m 21s   | extra_vote:ciss_diff_d3m 42s   | extra_vote:combo_majority 21s   | extra_vote:combo_majority 42s   | standalone:ciss_diff_d3m 21s   | standalone:ciss_diff_d3m 42s   | standalone:combo_majority 21s   | standalone:combo_majority 42s   |
|:---------------------------------|:--------------------|:--------------------|:-------------------------------|:-------------------------------|:--------------------------------|:--------------------------------|:-------------------------------|:-------------------------------|:--------------------------------|:--------------------------------|
| baseline                         | 59 n=156            | 61 n=89             | 55 n=111                       | 61 n=71                        | 55 n=101                        | 64 n=61                         | 54 n=208                       | 52 n=104                       | 49 n=198                        | 55 n=102                        |
| lookahead_control_minus21        | 59 n=156            | 61 n=89             | 52 n=106                       | 64 n=73                        | 53 n=108                        | 61 n=67                         | 55 n=208                       | 49 n=104                       | 53 n=198                        | 48 n=101                        |
| lookahead_control_minus63        | 59 n=156            | 61 n=89             | 58 n=117                       | 63 n=76                        | 58 n=115                        | 62 n=68                         | 50 n=206                       | 50 n=103                       | 54 n=196                        | 52 n=101                        |
| positive_control_planted_label21 | 59 n=156            | 61 n=89             | 100 n=122                      | 82 n=72                        | 100 n=122                       | 82 n=72                         | 100 n=208                      | 81 n=104                       | 100 n=208                       | 81 n=104                        |
| shuffled_labels_0                | 48 n=143            | 59 n=85             | 49 n=98                        | 56 n=66                        | 52 n=88                         | 44 n=57                         | 47 n=209                       | 47 n=105                       | 50 n=199                        | 50 n=103                        |
| shuffled_labels_1                | 54 n=118            | 54 n=70             | 49 n=79                        | 53 n=57                        | 54 n=67                         | 50 n=46                         | 48 n=209                       | 50 n=105                       | 50 n=199                        | 47 n=103                        |
| shuffled_labels_2                | 52 n=106            | 51 n=65             | 55 n=73                        | 54 n=54                        | 43 n=63                         | 55 n=44                         | 52 n=209                       | 43 n=105                       | 47 n=199                        | 51 n=103                        |
| vote_stale_plus1                 | 59 n=156            | 61 n=89             | 52 n=110                       | 53 n=72                        | 57 n=100                        | 58 n=60                         | 53 n=208                       | 52 n=104                       | 53 n=198                        | 54 n=102                        |
| vote_stale_plus21                | 59 n=156            | 61 n=89             | 55 n=113                       | 61 n=77                        | 53 n=93                         | 65 n=60                         | 55 n=208                       | 47 n=104                       | 49 n=198                        | 49 n=101                        |
| vote_stale_plus5                 | 59 n=156            | 61 n=89             | 52 n=115                       | 59 n=76                        | 61 n=94                         | 65 n=60                         | 57 n=208                       | 51 n=104                       | 49 n=199                        | 48 n=102                        |

* (1) Shuffled labels (targets and the 1-session return the house weights are fitted on, three permutations): 43-59 % everywhere, centred on 50 %.
* (2) Votes moved forward by 1 / 5 / 21 sessions (staler): no collapse, because nothing was there to collapse; the swings of several points from a one-session shift show how noisy a 70-110-decision subset is. The look-ahead controls (vote taken from 21 / 63 sessions in the future) do not help either: the votes are not a label in disguise. Added after the first run: a planted label (vote = sign of the next 21 sessions' return) scores 100 % standalone and 100 % as an extra vote at 21 sessions, so the harness does expose a look-ahead.
* (3) Vote anatomy (section 2): correlation of every vote with the forward 21- and 63-session return is between -0.12 and +0.16; no vote uses EUR/USD prices (the balance-sheet ratio is in own currencies; the CISS contains FX volatility, not direction). The stress votes are mildly correlated with PAST EUR/USD returns (0.1-0.3: stress falls when the euro has risen), i.e. they are weak trend followers.
* Lag audit: section 1; every observation is at least as old as the stated lag at the session close that uses it.

## 10. Variant count

12 candidate votes, each evaluated standalone, as an extra vote and with two placebos; no parameters searched. One selection (the declared rule). For deflation: 12.

