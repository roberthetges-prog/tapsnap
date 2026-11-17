# Arm AC - leg_decomposition: is the agreement rule a euro signal or a dollar signal, and does a hedge help?

Code `src/eurusd/arms/leg_decomposition.py` (`run()`; `PYTHONPATH=src OMP_NUM_THREADS=1 python src/eurusd/arms/leg_decomposition.py`, about half a minute, one process). Results `experiments/results/arms/leg_decomposition_*.csv`, log `experiments/results/arms/logs/leg_decomposition.log`. The primary test, its pass bar, the basket, the weights, the timing rule and the cost rule were written into the module docstring before any outcome on either leg was computed; what was added afterwards is marked ADDED there and here.

## Verdict: **FAIL** against the declared bar

**The hedged expression is worse, not better.** The same agreement calls scored on the euro against a basket (JPY, GBP, CHF, CAD, AUD, 1/5 each) instead of on plain EUR/USD are right 53.2 % instead of 59.2 % at 21 sessions and 57.4 % instead of 62.9 % at 42 sessions (2010-26); 50.3 vs 58.3 % and 55.8 vs 61.3 % since 2016. The bar asked for +3 points in those four cells; the result is -6.0, -8.0, -5.5 and -5.5 points, and at 21 sessions the paired 95 % interval lies entirely below zero in both eras. In 2023-26 it is -1.5 points at 21 sessions (bar: not worse) and +5.5 at 42 sessions on 9 independent calls. The stale-copy condition cannot be met because there is no gain to lose.

|   sessions | era     | condition                                            |   gain, points |   gain with 63-session-stale calls | result                                |
|-----------:|:--------|:-----------------------------------------------------|---------------:|-----------------------------------:|:--------------------------------------|
|         21 | 2010-26 | (a) gain >= +3.0 and (c) stale copy loses half of it |           -6   |                                0   | FAIL (a), (c) not applicable: no gain |
|         21 | 2016-26 | (a) gain >= +3.0 and (c) stale copy loses half of it |           -8   |                                1.7 | FAIL (a), (c) not applicable: no gain |
|         21 | 2023-26 | (b) not worse than plain EUR/USD                     |           -1.5 |                                9.1 | FAIL                                  |
|         42 | 2010-26 | (a) gain >= +3.0 and (c) stale copy loses half of it |           -5.5 |                                1.6 | FAIL (a), (c) not applicable: no gain |
|         42 | 2016-26 | (a) gain >= +3.0 and (c) stale copy loses half of it |           -5.5 |                                1.8 | FAIL (a), (c) not applicable: no gain |
|         42 | 2023-26 | (b) not worse than plain EUR/USD                     |            5.5 |                               10.7 | pass                                  |

**Plain-language answer: it is more a dollar signal than a euro signal, and since 2016 it has been almost only a dollar signal.**

* On the dollar leg alone (dollar against the same basket, euro excluded) the calls are right 56.8 / 62.7 / 65.3 % at 21 / 42 / 63 sessions in 2010-26 and 59.9 / 64.8 / 65.8 % in 2016-26: about what they score on EUR/USD itself (59.2 / 62.9 / 66.2 and 58.3 / 61.3 / 66.1 %). On the euro leg alone they are right 53.2 / 57.4 / 61.2 % and 50.3 / 55.8 / 59.7 %, which a random entry with the same call pattern matches or beats in 31 / 15 / 12 % and 44 / 34 / 26 % of 1,000 draws (dollar leg: 4 / 2 / 0 % and 3 / 1 / 1 %; plain EUR/USD: 4 / 2 / 1 % and 7 / 6 / 4 %).
* Exact split of the profit (EUR/USD = euro leg minus dollar leg, so the P&L of a call splits with no residual): of 403 bp a year gross on EUR/USD in 2010-26, 231 bp came from the dollar leg (t 2.2) and 172 bp from the euro leg (t 1.9). Since 2016: 233 of 253 bp (92 %) from the dollar leg, 20 bp (t 0.2) from the euro leg. Since 2023: 201 of 303 bp from the dollar leg.
* By the attribution rule declared in advance the formal answer is **'cannot be attributed to one leg'**: accuracy on the dollar leg is higher than on the euro leg by 3.6, 9.6, 5.2 and 9.0 points in the four cells (3 were required), but the paired intervals in 2010-26 include zero (-13.2 .. +5.7 at 21 sessions, -16.3 .. +6.2 at 42); only 2016-26 at 21 sessions excludes it (-18.5 .. -0.7). So: both legs before 2016, the dollar leg since, and the data cannot prove the difference between the legs.
* Consequence for the product: **keep trading the calls on plain EUR/USD.** The two legs are almost uncorrelated (correlation of their 21-session moves +0.05 in 2010-26) and EUR/USD is their difference, so the pair collects whatever the calls know about either leg. Hedging the dollar leg throws away the larger half of the edge; hedging the euro leg (trading a dollar basket instead) keeps the accuracy but does not raise it and costs five spreads.

## Key table: the same agreement calls scored on three instruments

Phase-averaged accuracy (every call day scored on the next h sessions; independent calls = call days / h). Entry at the first H.10 fixing after the call, all three instruments on the same two fixings. USD leg: a long-EUR/USD call counts as right when the dollar FELL against the basket.

|   sessions | era     |   independent calls |   per year |   plain EUR/USD % |   EUR leg % |   USD leg % | EUR leg - plain (95 % paired)   | USD leg - plain (95 % paired)   |
|-----------:|:--------|--------------------:|-----------:|------------------:|------------:|------------:|:--------------------------------|:--------------------------------|
|         21 | 2010-26 |                90.8 |        5.3 |              59.2 |        53.2 |        56.8 | -6.0 (-11.2 .. -1.0)            | -2.5 (-8.8 .. +3.5)             |
|         21 | 2016-26 |                57   |        5.2 |              58.3 |        50.3 |        59.9 | -8.0 (-14.5 .. -1.1)            | +1.6 (-3.6 .. +6.9)             |
|         21 | 2023-26 |                19.4 |        4.9 |              52.9 |        51.5 |        48.8 | -1.5 (-18.1 .. +15.2)           | -4.2 (-11.9 .. +3.6)            |
|         42 | 2010-26 |                45   |        2.6 |              62.9 |        57.4 |        62.7 | -5.5 (-14.1 .. +3.1)            | -0.3 (-5.3 .. +4.3)             |
|         42 | 2016-26 |                28   |        2.5 |              61.3 |        55.8 |        64.8 | -5.5 (-16.9 .. +5.7)            | +3.5 (-0.2 .. +7.7)             |
|         42 | 2023-26 |                 9.3 |        2.3 |              48.1 |        53.6 |        49.7 | +5.5 (-18.8 .. +34.2)           | +1.7 (-4.6 .. +7.8)             |
|         63 | 2010-26 |                29.9 |        1.8 |              66.2 |        61.2 |        65.3 | -5.0 (-12.9 .. +3.2)            | -0.9 (-7.2 .. +5.2)             |
|         63 | 2016-26 |                18.7 |        1.7 |              66.1 |        59.7 |        65.8 | -6.4 (-16.6 .. +4.4)            | -0.3 (-6.4 .. +5.6)             |
|         63 | 2023-26 |                 6.1 |        1.5 |              50.6 |        54.5 |        52.2 | +3.9 (-14.0 .. +25.5)           | +1.6 (-13.8 .. +12.9)           |

Sharpe of the daily position streams, net of 1.2 pips on every pair traded (2010-26 / 2016-26 / 2023-26): plain EUR/USD +0.66 / +0.47 / +0.63; EUR leg as a hedge (six pairs) +0.22 / -0.20 / +0.10; EUR leg through five direct crosses +0.34 / -0.05 / +0.30; USD leg +0.43 / +0.47 / +0.41.

Candidates run: **6** (5 declared + 1 added post hoc; cap 12). None passes.

## 1. Data, timing and what was checked before any outcome

* **Used: Federal Reserve H.10 noon-New-York rates** (`data/macro/fred_DEX{USEU,JPUS,USUK,SZUS,CAUS,USAL,SDUS,NOUS}.csv`, 1999-01-04 .. 2026-11-06, 6,984 fixings, no gaps inside the panel; 3.5-4.4 % of weekdays have no fixing, the US holidays). One stamp convention for the whole history and every currency at the same instant, so each euro cross is derived at one timestamp. **Not used: the Yahoo daily bars** in `data/processed/cross/*_D1.parquet` (stamp convention changed in 2010 Q3).
* **Timing rule.** The call is made at the 17:00 New York close of date D; the trade is entered at the first fixing strictly after D (noon of the next fixing day, 19 hours later) and scored at the first fixing strictly after the close date of session i + h. No series stamped at a different time is joined on the same day.
* **H.10 against EUR/USD in the feature store** (same date, noon vs 17:00): median level gap 12 pips; return correlation and sign agreement by horizon:

|   h_fixings |    n |   corr_returns |   sign_agree |   median_abs_gap_bp |
|------------:|-----:|---------------:|-------------:|--------------------:|
|           1 | 5969 |          0.841 |        0.827 |                14.9 |
|           5 | 5965 |          0.967 |        0.931 |                14.7 |
|          21 | 5949 |          0.993 |        0.961 |                15   |
|          42 | 5928 |          0.996 |        0.971 |                15.5 |
|          63 | 5907 |          0.997 |        0.975 |                15.1 |

* **Independent source.** ECB euro reference rates (14:15 CET, `data/processed/cross/leg_ecb_ref_rates.parquet`, fetched 2026-11-17 from the ECB data API, flow EXR, 1999-01-04 .. 2026-11-17). They quote the euro crosses DIRECTLY, whereas H.10 gives the dollar pairs directly and the euro crosses by triangulation. The derived H.10 crosses agree with the direct ECB crosses exactly as well as EUR/USD itself agrees between the two sources (the difference is the 3 h 45 min between the fixings, not triangulation error):

| cross   | era     |    n |   corr_5d |   corr_21d |   max_abs_5d_gap_bp |   h10_missing_share_of_weekdays |
|:--------|:--------|-----:|----------:|-----------:|--------------------:|--------------------------------:|
| EURJPY  | 2003-09 | 1741 |     0.951 |      0.986 |               421.4 |                           0.034 |
| EURJPY  | 2010-15 | 1486 |     0.94  |      0.987 |               267.1 |                           0.039 |
| EURJPY  | 2016-26 | 2675 |     0.943 |      0.985 |               296.7 |                           0.044 |
| EURGBP  | 2003-09 | 1741 |     0.949 |      0.986 |               226.6 |                           0.034 |
| EURGBP  | 2010-15 | 1486 |     0.934 |      0.982 |               173.5 |                           0.039 |
| EURGBP  | 2016-26 | 2675 |     0.946 |      0.985 |               183.1 |                           0.044 |
| EURCHF  | 2003-09 | 1741 |     0.946 |      0.987 |               172.5 |                           0.034 |
| EURCHF  | 2010-15 | 1486 |     0.963 |      0.99  |               486.5 |                           0.039 |
| EURCHF  | 2016-26 | 2675 |     0.927 |      0.981 |               123   |                           0.044 |
| EURCAD  | 2003-09 | 1741 |     0.916 |      0.979 |               336.3 |                           0.034 |
| EURCAD  | 2010-15 | 1486 |     0.912 |      0.978 |               262.9 |                           0.039 |
| EURCAD  | 2016-26 | 2675 |     0.907 |      0.975 |               349.2 |                           0.044 |
| EURAUD  | 2003-09 | 1741 |     0.945 |      0.983 |               376.6 |                           0.034 |
| EURAUD  | 2010-15 | 1486 |     0.951 |      0.988 |               247.4 |                           0.039 |
| EURAUD  | 2016-26 | 2675 |     0.939 |      0.986 |               327.5 |                           0.044 |
| EURSEK  | 2003-09 | 1741 |     0.922 |      0.979 |               246.9 |                           0.034 |
| EURSEK  | 2010-15 | 1486 |     0.928 |      0.975 |               141.9 |                           0.039 |
| EURSEK  | 2016-26 | 2675 |     0.925 |      0.982 |               216.6 |                           0.044 |
| EURNOK  | 2003-09 | 1741 |     0.941 |      0.986 |               289.8 |                           0.034 |
| EURNOK  | 2010-15 | 1486 |     0.937 |      0.979 |               244.3 |                           0.039 |
| EURNOK  | 2016-26 | 2675 |     0.935 |      0.985 |               328.4 |                           0.044 |
| EURUSD  | 2003-09 | 1741 |     0.931 |      0.984 |               279.6 |                           0.034 |
| EURUSD  | 2010-15 | 1486 |     0.928 |      0.984 |               210.7 |                           0.039 |
| EURUSD  | 2016-26 | 2675 |     0.921 |      0.979 |               272.6 |                           0.044 |

* **SEK and NOK** pass the declared verification rule (verified: 5-session correlation with the ECB rates within 0.01 of the worst core cross in every era), so the robustness basket B7 was run.
* **The identity.** S = E - U holds to floating-point precision on every bar (max error 0.0 bp in `leg_decomposition_leg_stats.csv`), by construction, because the euro crosses are derived from the dollar pairs at the same fixing. What the legs look like (21-session moves unless stated):

| era       |   ann_vol_S_pct |   ann_vol_E_pct |   ann_vol_U_pct |   corr_E_U |   var_share_E |   var_share_U |   sign_agree_S_E |   sign_agree_S_minusU |
|:----------|----------------:|----------------:|----------------:|-----------:|--------------:|--------------:|-----------------:|----------------------:|
| 1999-2009 |            10.5 |             5.7 |             7.6 |      -0.24 |          0.29 |          0.52 |             0.73 |                  0.84 |
| 2010-26   |             7.9 |             5.1 |             6.2 |       0.05 |          0.43 |          0.62 |             0.68 |                  0.79 |
| 2016-26   |             6.6 |             3.9 |             6   |       0.17 |          0.35 |          0.83 |             0.64 |                  0.83 |
| 2023-26   |             6.4 |             3.4 |             5.8 |       0.11 |          0.28 |          0.83 |             0.58 |                  0.89 |

  S = EUR/USD, E = euro against the basket, U = dollar against the basket. The dollar leg is the larger one: its variance is 52-83 % of EUR/USD's, the euro leg's 28-43 % (the shares need not add to 100 because of the covariance); the two are close to uncorrelated; EUR/USD's 21-session direction agrees with the dollar leg's 79-89 % of the time and with the euro leg's 58-73 %.

## 2. Reconciliation

The agreement rule rebuilt with `committee._fold_columns` (identical to `experiments/70_committee.py::agreement_side`) reproduces the published benchmark exactly on the feature-store closes (asserted in `compute()`), and scores within about one point of it on the H.10 fixings:

|   h | era     |   published_2010_26 |   n_indep |   per_year |   store_close |   h10_next_fixing |   h10_same_day_fixing |
|----:|:--------|--------------------:|----------:|-----------:|--------------:|------------------:|----------------------:|
|  21 | 2010-26 |                58.3 |      90.8 |        5.3 |          58.3 |              59.2 |                  58.6 |
|  21 | 2016-26 |               nan   |      57   |        5.2 |          58   |              58.3 |                  58.2 |
|  21 | 2023-26 |               nan   |      19.5 |        4.9 |          53.5 |              52.9 |                  53.3 |
|  42 | 2010-26 |                63.3 |      44.9 |        2.6 |          63.3 |              62.9 |                  62.9 |
|  42 | 2016-26 |               nan   |      28   |        2.5 |          62   |              61.3 |                  61.4 |
|  42 | 2023-26 |               nan   |       9.3 |        2.3 |          47.4 |              48.1 |                  47.7 |
|  63 | 2010-26 |                66.7 |      29.9 |        1.8 |          66.7 |              66.2 |                  66.5 |
|  63 | 2016-26 |               nan   |      18.7 |        1.7 |          67   |              66.1 |                  66.9 |
|  63 | 2023-26 |               nan   |       6.1 |        1.5 |          51.7 |              50.6 |                  51.4 |

Call pattern: 2010-26: calls on 44 % of sessions, 45 % of them long, 340 separate call episodes; 2016-26: calls on 43 % of sessions, 47 % of them long, 200 separate call episodes; 2023-26: calls on 42 % of sessions, 48 % of them long, 71 separate call episodes.

## 3. Descriptive (declared): the rule and each of its three inputs on EUR/USD (S), the euro leg (E) and the dollar leg (U)

`n_indep` = independent decisions, `lo`-`hi` = 95 % Wilson interval on that count, `per_year` = independent decisions a year, `base_*` = matched random entry (the era's own call sequence rotated to a random position, 1,000 draws: same count, spacing and long / short mix), `p_random` = share of random draws at least as accurate.

### Agreement rule

| series   |   h | era     |   n_indep |   per_year |   acc |   lo |   hi |   base_mean |   base_lo |   base_hi |   p_random |
|:---------|----:|:--------|----------:|-----------:|------:|-----:|-----:|------------:|----------:|----------:|-----------:|
| S        |  21 | 2010-26 |      90.7 |        5.3 |  59.2 | 49.1 | 68.9 |        50   |      38.3 |      60.5 |       0.04 |
| E        |  21 | 2010-26 |      90.8 |        5.3 |  53.2 | 42.6 | 62.7 |        49.9 |      39.8 |      60.6 |       0.31 |
| U        |  21 | 2010-26 |      90.8 |        5.3 |  56.8 | 46.9 | 66.8 |        49.9 |      41.6 |      57.7 |       0.04 |
| S        |  21 | 2016-26 |      56.9 |        5.2 |  58.3 | 45   | 69.8 |        49.9 |      39.3 |      62.3 |       0.07 |
| E        |  21 | 2016-26 |      57   |        5.2 |  50.3 | 38.3 | 63.4 |        49.9 |      38.9 |      62   |       0.44 |
| U        |  21 | 2016-26 |      57   |        5.2 |  59.9 | 46.7 | 71.4 |        49.9 |      40.9 |      60.2 |       0.03 |
| S        |  21 | 2023-26 |      19.4 |        4.9 |  52.9 | 31.7 | 72.7 |        49.7 |      38.3 |      64.8 |       0.29 |
| E        |  21 | 2023-26 |      19.4 |        4.9 |  51.5 | 31.7 | 72.7 |        50   |      31.2 |      66.8 |       0.45 |
| U        |  21 | 2023-26 |      19.4 |        4.9 |  48.8 | 27.3 | 68.3 |        49.7 |      36.8 |      66   |       0.54 |
| S        |  42 | 2010-26 |      44.9 |        2.6 |  62.9 | 47.6 | 74.9 |        49.9 |      36.3 |      62.9 |       0.02 |
| E        |  42 | 2010-26 |      45   |        2.6 |  57.4 | 43.3 | 71   |        49.5 |      36   |      63.3 |       0.15 |
| U        |  42 | 2010-26 |      45   |        2.6 |  62.7 | 47.6 | 74.9 |        50.2 |      40   |      60.9 |       0.02 |
| S        |  42 | 2016-26 |      28   |        2.5 |  61.3 | 42.4 | 76.4 |        49.9 |      37   |      64.3 |       0.06 |
| E        |  42 | 2016-26 |      28   |        2.5 |  55.8 | 39.1 | 73.5 |        50.2 |      32.7 |      68.3 |       0.34 |
| U        |  42 | 2016-26 |      28   |        2.5 |  64.8 | 45.8 | 79.3 |        49.9 |      38.3 |      62.5 |       0.01 |
| S        |  42 | 2023-26 |       9.3 |        2.3 |  48.1 | 18.9 | 73.3 |        49.2 |      34.5 |      65.3 |       0.55 |
| E        |  42 | 2023-26 |       9.3 |        2.3 |  53.6 | 26.7 | 81.1 |        49.3 |      32.8 |      66.2 |       0.36 |
| U        |  42 | 2023-26 |       9.3 |        2.3 |  49.7 | 26.7 | 81.1 |        49.4 |      33.6 |      63.6 |       0.45 |
| S        |  63 | 2010-26 |      29.9 |        1.8 |  66.2 | 48.8 | 80.8 |        50.3 |      34.9 |      64   |       0.01 |
| E        |  63 | 2010-26 |      29.9 |        1.8 |  61.2 | 42.3 | 75.4 |        50.4 |      34.9 |      65   |       0.12 |
| U        |  63 | 2010-26 |      29.9 |        1.8 |  65.3 | 48.8 | 80.8 |        50.3 |      38.4 |      60.5 |       0    |
| S        |  63 | 2016-26 |      18.7 |        1.7 |  66.1 | 41   | 80.9 |        49.1 |      30.6 |      66.8 |       0.04 |
| E        |  63 | 2016-26 |      18.7 |        1.7 |  59.7 | 36.3 | 76.9 |        49.4 |      29.4 |      70.5 |       0.26 |
| U        |  63 | 2016-26 |      18.7 |        1.7 |  65.8 | 41   | 80.9 |        49.4 |      37.6 |      60.3 |       0.01 |
| S        |  63 | 2023-26 |       6.1 |        1.5 |  50.6 | 18.8 | 81.2 |        49.2 |      34.7 |      63.2 |       0.47 |
| E        |  63 | 2023-26 |       6.1 |        1.5 |  54.5 | 18.8 | 81.2 |        49   |      30.1 |      70.5 |       0.35 |
| U        |  63 | 2023-26 |       6.1 |        1.5 |  52.2 | 18.8 | 81.2 |        50   |      36.8 |      63.6 |       0.38 |

### Positioning alone (sign of cot_z52, always on)

| series   |   h | era     |   n_indep |   per_year |   acc |   lo |   hi |   base_mean |   base_lo |   base_hi |   p_random |
|:---------|----:|:--------|----------:|-----------:|------:|-----:|-----:|------------:|----------:|----------:|-----------:|
| S        |  21 | 2010-26 |     206.9 |       12.2 |  58.5 | 51.6 | 65   |        49.8 |      40.3 |      57.7 |       0.02 |
| E        |  21 | 2010-26 |     207.2 |       12.2 |  54.8 | 48.3 | 61.7 |        50   |      41.6 |      57.4 |       0.21 |
| U        |  21 | 2010-26 |     207.2 |       12.2 |  55.2 | 48.3 | 61.7 |        50   |      43.7 |      55.9 |       0.04 |
| S        |  21 | 2016-26 |     132.9 |       12.1 |  55.8 | 47.2 | 63.8 |        49.9 |      41.8 |      58.7 |       0.11 |
| E        |  21 | 2016-26 |     133.1 |       12.1 |  53.1 | 44.9 | 61.6 |        50.1 |      41.8 |      58.8 |       0.3  |
| U        |  21 | 2016-26 |     133.1 |       12.1 |  56.6 | 47.9 | 64.5 |        50   |      43.6 |      57.2 |       0.04 |
| S        |  21 | 2023-26 |      46.5 |       11.6 |  49   | 35.3 | 62.8 |        49.8 |      40.8 |      61.5 |       0.53 |
| E        |  21 | 2023-26 |      46.6 |       11.6 |  54.5 | 39.2 | 66.7 |        49.7 |      36.5 |      62.4 |       0.31 |
| U        |  21 | 2023-26 |      46.6 |       11.6 |  45.2 | 31.4 | 58.8 |        50   |      42.9 |      59.5 |       0.88 |
| S        |  42 | 2010-26 |     103   |        6.1 |  60.4 | 50.5 | 69.1 |        49.7 |      37.9 |      59.5 |       0.02 |
| E        |  42 | 2010-26 |     103.1 |        6.1 |  60.6 | 51.5 | 70   |        49.6 |      36.9 |      60.7 |       0.03 |
| U        |  42 | 2010-26 |     103.1 |        6.1 |  56.4 | 46.7 | 65.5 |        49.8 |      42   |      57.2 |       0.03 |
| S        |  42 | 2016-26 |      66   |        6   |  58.5 | 47   | 70.1 |        49.8 |      39   |      61.2 |       0.06 |
| E        |  42 | 2016-26 |      66   |        6   |  60   | 48.5 | 71.5 |        50.3 |      35.8 |      64.6 |       0.14 |
| U        |  42 | 2016-26 |      66   |        6   |  56.7 | 44.1 | 67.4 |        49.7 |      41   |      59.3 |       0.1  |
| S        |  42 | 2023-26 |      22.7 |        5.7 |  48.3 | 29.2 | 67   |        49.7 |      38.9 |      65.2 |       0.55 |
| E        |  42 | 2023-26 |      22.8 |        5.7 |  59.8 | 40.8 | 77.8 |        48.7 |      34.4 |      64.1 |       0.2  |
| U        |  42 | 2023-26 |      22.8 |        5.7 |  44.6 | 25.6 | 63.2 |        50.2 |      43.1 |      61.9 |       0.89 |
| S        |  63 | 2010-26 |      68.3 |        4   |  62.8 | 51.4 | 73.7 |        50   |      37.3 |      61.6 |       0.01 |
| E        |  63 | 2010-26 |      68.4 |        4   |  62   | 49.9 | 72.4 |        50.2 |      36.6 |      63   |       0.06 |
| U        |  63 | 2010-26 |      68.4 |        4   |  57.5 | 45.5 | 68.4 |        49.9 |      40.6 |      57.6 |       0.03 |
| S        |  63 | 2016-26 |      43.7 |        4   |  63.2 | 48.9 | 76.2 |        49.1 |      34.3 |      63.7 |       0.03 |
| E        |  63 | 2016-26 |      43.7 |        4   |  61.8 | 46.6 | 74.3 |        49.4 |      32.5 |      67.8 |       0.13 |
| U        |  63 | 2016-26 |      43.7 |        4   |  58.8 | 44.4 | 72.3 |        49.4 |      39.8 |      59.2 |       0.04 |
| S        |  63 | 2023-26 |      14.8 |        3.7 |  54   | 30.1 | 75.2 |        49.5 |      35.3 |      70.7 |       0.29 |
| E        |  63 | 2023-26 |      14.9 |        3.7 |  60.9 | 35.7 | 80.2 |        48.7 |      30.6 |      67.5 |       0.27 |
| U        |  63 | 2023-26 |      14.9 |        3.7 |  46.3 | 24.8 | 69.9 |        50.5 |      40.5 |      62.3 |       0.79 |

### 2-year spread trend alone (sign of d_spread2y_20)

| series   |   h | era     |   n_indep |   per_year |   acc |   lo |   hi |   base_mean |   base_lo |   base_hi |   p_random |
|:---------|----:|:--------|----------:|-----------:|------:|-----:|-----:|------------:|----------:|----------:|-----------:|
| S        |  21 | 2010-26 |     206.9 |       12.2 |  49.2 | 42.5 | 56   |        50.1 |      45.8 |      55   |       0.64 |
| E        |  21 | 2010-26 |     207.2 |       12.2 |  47.8 | 41.1 | 54.6 |        49.9 |      46.4 |      54.2 |       0.84 |
| U        |  21 | 2010-26 |     207.2 |       12.2 |  50   | 43.5 | 57   |        50   |      45.1 |      54.7 |       0.49 |
| S        |  21 | 2016-26 |     132.9 |       12.1 |  50.3 | 42   | 58.7 |        50   |      44.8 |      55.6 |       0.46 |
| E        |  21 | 2016-26 |     133.1 |       12.1 |  46.8 | 38.4 | 55.1 |        49.9 |      44.8 |      55.4 |       0.85 |
| U        |  21 | 2016-26 |     133.1 |       12.1 |  51.2 | 42.7 | 59.5 |        49.9 |      44.1 |      56   |       0.32 |
| S        |  21 | 2023-26 |      46.5 |       11.6 |  51.2 | 37.2 | 64.7 |        50.1 |      42.1 |      60.2 |       0.41 |
| E        |  21 | 2023-26 |      46.6 |       11.6 |  47.9 | 33.3 | 60.8 |        50.5 |      40.3 |      58.9 |       0.74 |
| U        |  21 | 2023-26 |      46.6 |       11.6 |  49.6 | 35.3 | 62.8 |        50   |      41.4 |      60.9 |       0.51 |
| S        |  42 | 2010-26 |     103   |        6.1 |  50   | 41   | 59.9 |        50.3 |      45.3 |      55.1 |       0.54 |
| E        |  42 | 2010-26 |     103.1 |        6.1 |  46.6 | 37.3 | 56.2 |        49.8 |      45.9 |      55   |       0.93 |
| U        |  42 | 2010-26 |     103.1 |        6.1 |  53.6 | 43.8 | 62.7 |        50.5 |      44.8 |      55.5 |       0.11 |
| S        |  42 | 2016-26 |      66   |        6   |  50.5 | 38.3 | 61.7 |        50.1 |      44.1 |      56   |       0.46 |
| E        |  42 | 2016-26 |      66   |        6   |  47.3 | 35.4 | 58.8 |        50   |      44.5 |      56.4 |       0.76 |
| U        |  42 | 2016-26 |      66   |        6   |  53.4 | 41.2 | 64.6 |        50.1 |      43.6 |      56.3 |       0.16 |
| S        |  42 | 2023-26 |      22.7 |        5.7 |  47.3 | 29.2 | 67   |        49.9 |      40.2 |      59.4 |       0.73 |
| E        |  42 | 2023-26 |      22.8 |        5.7 |  48.5 | 29.2 | 67   |        50.8 |      39.7 |      60.7 |       0.67 |
| U        |  42 | 2023-26 |      22.8 |        5.7 |  48.6 | 29.2 | 67   |        49.5 |      38.7 |      60   |       0.6  |
| S        |  63 | 2010-26 |      68.3 |        4   |  51.3 | 39.8 | 62.9 |        50.3 |      45.5 |      54.8 |       0.39 |
| E        |  63 | 2010-26 |      68.4 |        4   |  48.6 | 37.1 | 60.2 |        50.1 |      45.3 |      55.7 |       0.7  |
| U        |  63 | 2010-26 |      68.4 |        4   |  54.9 | 44.1 | 67.1 |        50.4 |      45.5 |      55.4 |       0.05 |
| S        |  63 | 2016-26 |      43.7 |        4   |  51   | 35.8 | 64.2 |        49.9 |      43.8 |      55.8 |       0.38 |
| E        |  63 | 2016-26 |      43.7 |        4   |  48.2 | 33.8 | 62.1 |        50   |      43   |      56.4 |       0.7  |
| U        |  63 | 2016-26 |      43.7 |        4   |  53.7 | 37.9 | 66.2 |        49.9 |      44.2 |      55.4 |       0.14 |
| S        |  63 | 2023-26 |      14.8 |        3.7 |  43.3 | 19.8 | 64.3 |        50.1 |      41.5 |      58.6 |       0.97 |
| E        |  63 | 2023-26 |      14.9 |        3.7 |  46.4 | 24.8 | 69.9 |        50.8 |      40.8 |      60.1 |       0.8  |
| U        |  63 | 2023-26 |      14.9 |        3.7 |  48   | 24.8 | 69.9 |        49.7 |      41.2 |      58.5 |       0.62 |

### House macro score alone (sign, walk-forward)

| series   |   h | era     |   n_indep |   per_year |   acc |   lo |   hi |   base_mean |   base_lo |   base_hi |   p_random |
|:---------|----:|:--------|----------:|-----------:|------:|-----:|-----:|------------:|----------:|----------:|-----------:|
| S        |  21 | 2010-26 |     206.9 |       12.2 |  54.6 | 47.8 | 61.2 |        50.1 |      44.2 |      56.3 |       0.09 |
| E        |  21 | 2010-26 |     207.2 |       12.2 |  51.9 | 45.4 | 58.9 |        49.9 |      44.3 |      55   |       0.26 |
| U        |  21 | 2010-26 |     207.2 |       12.2 |  53.3 | 46.3 | 59.8 |        50   |      45.5 |      54.8 |       0.11 |
| S        |  21 | 2016-26 |     132.9 |       12.1 |  53.9 | 45.7 | 62.4 |        50.1 |      43.6 |      55.8 |       0.17 |
| E        |  21 | 2016-26 |     133.1 |       12.1 |  49.3 | 41.3 | 58   |        49.8 |      43.3 |      56.5 |       0.54 |
| U        |  21 | 2016-26 |     133.1 |       12.1 |  54.8 | 46.4 | 63.1 |        50   |      44.4 |      55.9 |       0.04 |
| S        |  21 | 2023-26 |      46.5 |       11.6 |  53.6 | 39.2 | 66.7 |        49.3 |      39.9 |      58   |       0.18 |
| E        |  21 | 2023-26 |      46.6 |       11.6 |  50   | 35.3 | 62.8 |        48.5 |      40.2 |      56.8 |       0.38 |
| U        |  21 | 2023-26 |      46.6 |       11.6 |  51.9 | 37.2 | 64.7 |        49.7 |      39.9 |      60.8 |       0.33 |
| S        |  42 | 2010-26 |     103   |        6.1 |  57.6 | 47.6 | 66.4 |        50.1 |      43.4 |      57.2 |       0.02 |
| E        |  42 | 2010-26 |     103.1 |        6.1 |  53.8 | 43.8 | 62.7 |        49.9 |      42.4 |      58   |       0.19 |
| U        |  42 | 2010-26 |     103.1 |        6.1 |  57.4 | 47.6 | 66.4 |        50.2 |      44.7 |      55.9 |       0    |
| S        |  42 | 2016-26 |      66   |        6   |  55.8 | 44.1 | 67.4 |        50.1 |      42   |      58.1 |       0.09 |
| E        |  42 | 2016-26 |      66   |        6   |  51   | 39.7 | 63.2 |        49.9 |      40   |      60.2 |       0.44 |
| U        |  42 | 2016-26 |      66   |        6   |  60.1 | 48.5 | 71.5 |        50.1 |      42.6 |      57.1 |       0.01 |
| S        |  42 | 2023-26 |      22.7 |        5.7 |  50.5 | 29.2 | 67   |        48.8 |      37.2 |      59.4 |       0.37 |
| E        |  42 | 2023-26 |      22.8 |        5.7 |  50.9 | 33   | 70.8 |        47.6 |      37.8 |      56.3 |       0.28 |
| U        |  42 | 2023-26 |      22.8 |        5.7 |  56.2 | 36.8 | 74.4 |        49.7 |      37.6 |      62   |       0.16 |
| S        |  63 | 2010-26 |      68.3 |        4   |  59.7 | 48.4 | 71.1 |        50.4 |      42   |      58   |       0    |
| E        |  63 | 2010-26 |      68.4 |        4   |  57.2 | 45.5 | 68.4 |        50.3 |      41.8 |      59   |       0.06 |
| U        |  63 | 2010-26 |      68.4 |        4   |  59.2 | 47   | 69.7 |        50.4 |      44   |      56.7 |       0    |
| S        |  63 | 2016-26 |      43.7 |        4   |  59.3 | 44.4 | 72.3 |        49.9 |      39.1 |      60   |       0.04 |
| E        |  63 | 2016-26 |      43.7 |        4   |  55.4 | 40.1 | 68.3 |        49.7 |      38.8 |      60.8 |       0.25 |
| U        |  63 | 2016-26 |      43.7 |        4   |  60.5 | 44.4 | 72.3 |        50   |      42.4 |      56.5 |       0    |
| S        |  63 | 2023-26 |      14.8 |        3.7 |  55.4 | 30.1 | 75.2 |        48.6 |      37.4 |      61.4 |       0.17 |
| E        |  63 | 2023-26 |      14.9 |        3.7 |  51.9 | 30.1 | 75.2 |        46.8 |      37.1 |      55.8 |       0.2  |
| U        |  63 | 2023-26 |      14.9 |        3.7 |  59.5 | 35.7 | 80.2 |        50.7 |      39.9 |      62.9 |       0.09 |

What the inputs say:
* **Positioning** (the input the theory was about). Direction accuracy is the same on both legs at 21 sessions (54.8 % euro leg, 55.2 % dollar leg, 2010-26) and somewhat higher on the euro leg at 42 and 63 sessions (60.6 vs 56.4; 62.0 vs 57.5); no paired interval excludes zero. In money terms it is the other way round: 68 % of its 2010-26 P&L and 101 % of its 2016-26 P&L came from the dollar leg (gross Sharpe 0.71 on the dollar leg, -0.01 on the euro leg). 'Net speculative position in euro futures' is a position in the EUR/USD contract; it is at least as much a view on the dollar as on the euro. The premise of the primary test is not supported.
* **House macro score**: dollar leg (54.8 / 60.1 / 60.5 % since 2016; random entry at least as good in 4 / 1 / 0 % of draws) rather than euro leg (49.3 / 51.0 / 55.4 %).
* **2-year spread trend**: about 50 % on everything on its own (known); the little there is sits on the dollar leg at 42-63 sessions (53.6 / 54.9 %).
* **2023-26** runs the other way for positioning (euro leg 54-61 %, dollar leg 45-46 %) on 15-47 independent decisions with intervals 25 points wide: not evidence of anything.

Euro leg minus dollar leg, per input (paired 95 % interval, same call days):

| signal       |   h | era     |   n_indep |   acc_E |   acc_U |   E_minus_U |    lo |   hi |
|:-------------|----:|:--------|----------:|--------:|--------:|------------:|------:|-----:|
| positioning  |  21 | 2010-26 |     207.2 |    54.8 |    55.2 |        -0.4 |  -8.3 |  7.6 |
| positioning  |  21 | 2016-26 |     133.1 |    53.1 |    56.6 |        -3.5 | -11.7 |  5.2 |
| positioning  |  42 | 2010-26 |     103.1 |    60.6 |    56.4 |         4.3 |  -5   | 13.9 |
| positioning  |  42 | 2016-26 |      66   |    60   |    56.7 |         3.3 |  -6.5 | 14.1 |
| positioning  |  63 | 2010-26 |      68.4 |    62   |    57.5 |         4.5 |  -5.4 | 15   |
| positioning  |  63 | 2016-26 |      43.7 |    61.8 |    58.8 |         3   |  -8.3 | 14.9 |
| spread_trend |  21 | 2010-26 |     207.2 |    47.8 |    50   |        -2.2 |  -7.7 |  3.6 |
| spread_trend |  21 | 2016-26 |     133.1 |    46.8 |    51.2 |        -4.4 | -11.1 |  1.9 |
| spread_trend |  42 | 2010-26 |     103.1 |    46.6 |    53.6 |        -6.9 | -13.3 | -0.1 |
| spread_trend |  42 | 2016-26 |      66   |    47.3 |    53.4 |        -6.1 | -14.2 |  1.8 |
| spread_trend |  63 | 2010-26 |      68.4 |    48.6 |    54.9 |        -6.3 | -12.1 | -0.2 |
| spread_trend |  63 | 2016-26 |      43.7 |    48.2 |    53.7 |        -5.5 | -13.5 |  1.9 |
| house_score  |  21 | 2010-26 |     207.2 |    51.9 |    53.3 |        -1.4 |  -6.9 |  4.6 |
| house_score  |  21 | 2016-26 |     133.1 |    49.3 |    54.8 |        -5.5 | -11.3 |  0.6 |
| house_score  |  42 | 2010-26 |     103.1 |    53.8 |    57.4 |        -3.6 | -10.1 |  3.1 |
| house_score  |  42 | 2016-26 |      66   |    51   |    60.1 |        -9.2 | -16.5 | -1.9 |
| house_score  |  63 | 2010-26 |      68.4 |    57.2 |    59.2 |        -1.9 |  -8.6 |  5.1 |
| house_score  |  63 | 2016-26 |      43.7 |    55.4 |    60.5 |        -5   | -12.4 |  2   |

## 4. PRIMARY TEST (candidate 1): the calls on the euro leg against the calls on plain EUR/USD

`acc_ref` = plain EUR/USD, `acc_leg` = euro against the basket, `gain` = difference with its paired block-bootstrap 95 % interval (blocks of 126 sessions, 2,000 draws); `rand_gain_*` = 95 % range of the same difference under matched random entry; `stale_*` = the calls of 63 sessions earlier.

|   h | era     |   n_indep |   per_year |   acc_ref |   acc_leg |   leg_lo |   leg_hi |   gain |   gain_lo |   gain_hi |   rand_gain_lo |   rand_gain_hi |   p_random_gain |   stale_acc_ref |   stale_acc_leg |   stale_gain |
|----:|:--------|----------:|-----------:|----------:|----------:|---------:|---------:|-------:|----------:|----------:|---------------:|---------------:|----------------:|----------------:|----------------:|-------------:|
|  21 | 2010-26 |      90.8 |        5.3 |      59.2 |      53.2 |     42.6 |     62.7 |   -6   |     -11.2 |      -1   |           -6.4 |            6   |            0.97 |            59.4 |            59.4 |          0   |
|  21 | 2016-26 |      57   |        5.2 |      58.3 |      50.3 |     38.3 |     63.4 |   -8   |     -14.5 |      -1.1 |           -8.9 |            7.6 |            0.97 |            59.2 |            60.9 |          1.7 |
|  21 | 2023-26 |      19.4 |        4.9 |      52.9 |      51.5 |     31.7 |     72.7 |   -1.5 |     -18.1 |      15.2 |          -19.7 |           15.8 |            0.58 |            50.5 |            59.6 |          9.1 |
|  42 | 2010-26 |      45   |        2.6 |      62.9 |      57.4 |     43.3 |     71   |   -5.5 |     -14.1 |       3.1 |           -8.6 |            8.3 |            0.88 |            57.2 |            58.8 |          1.6 |
|  42 | 2016-26 |      28   |        2.5 |      61.3 |      55.8 |     39.1 |     73.5 |   -5.5 |     -16.9 |       5.7 |          -11.1 |           10.4 |            0.84 |            58.1 |            59.9 |          1.8 |
|  42 | 2023-26 |       9.3 |        2.3 |      48.1 |      53.6 |     26.7 |     81.1 |    5.5 |     -18.8 |      34.2 |          -19.4 |           24.5 |            0.27 |            42   |            52.7 |         10.7 |
|  63 | 2010-26 |      29.9 |        1.8 |      66.2 |      61.2 |     42.3 |     75.4 |   -5   |     -12.9 |       3.2 |           -9.3 |            9.1 |            0.83 |            59   |            60.3 |          1.3 |
|  63 | 2016-26 |      18.7 |        1.7 |      66.1 |      59.7 |     36.3 |     76.9 |   -6.4 |     -16.6 |       4.4 |          -11.5 |           10.6 |            0.87 |            64.2 |            62.5 |         -1.6 |
|  63 | 2023-26 |       6.1 |        1.5 |      50.6 |      54.5 |     18.8 |     81.2 |    3.9 |     -14   |      25.5 |          -17   |           23.7 |            0.32 |            48.5 |            52.8 |          4.4 |

**FAIL** on (a) in all four cells and on (b) at 21 sessions. Noteworthy in the placebo columns: the 63-session-stale calls score 59.4 % on the euro leg at 21 sessions (live calls 53.2 %) and 51.4 % on the dollar leg (live 56.8 %). Since 2016: stale 60.9 vs live 50.3 % on the euro leg, stale 53.8 vs live 59.9 % on the dollar leg. The timely part of the rule is its dollar part; on the euro leg the three-month-old calls do better than the live ones, so whatever is there is slow drift or noise, not timing.

## 5. Secondary (declared)

### 5a. Mirror (candidate 2): the calls on the dollar leg (long EUR/USD call = short the dollar against the basket)

|   h | era     |   n_indep |   per_year |   acc_ref |   acc_leg |   leg_lo |   leg_hi |   gain |   gain_lo |   gain_hi |   rand_gain_lo |   rand_gain_hi |   p_random_gain |   stale_acc_ref |   stale_acc_leg |   stale_gain |
|----:|:--------|----------:|-----------:|----------:|----------:|---------:|---------:|-------:|----------:|----------:|---------------:|---------------:|----------------:|----------------:|----------------:|-------------:|
|  21 | 2010-26 |      90.8 |        5.3 |      59.2 |      56.8 |     46.9 |     66.8 |   -2.5 |      -8.8 |       3.5 |           -6.8 |            6.2 |            0.73 |            59.4 |            51.4 |         -8   |
|  21 | 2016-26 |      57   |        5.2 |      58.3 |      59.9 |     46.7 |     71.4 |    1.6 |      -3.6 |       6.9 |           -5.6 |            4.7 |            0.33 |            59.2 |            53.8 |         -5.5 |
|  21 | 2023-26 |      19.4 |        4.9 |      52.9 |      48.8 |     27.3 |     68.3 |   -4.2 |     -11.9 |       3.6 |           -7.1 |            6.1 |            0.84 |            50.5 |            42.3 |         -8.1 |
|  42 | 2010-26 |      45   |        2.6 |      62.9 |      62.7 |     47.6 |     74.9 |   -0.3 |      -5.3 |       4.3 |           -8.3 |            8.2 |            0.55 |            57.2 |            54.1 |         -3.1 |
|  42 | 2016-26 |      28   |        2.5 |      61.3 |      64.8 |     45.8 |     79.3 |    3.5 |      -0.2 |       7.7 |           -4.9 |            4.5 |            0.06 |            58.1 |            57.4 |         -0.7 |
|  42 | 2023-26 |       9.3 |        2.3 |      48.1 |      49.7 |     26.7 |     81.1 |    1.7 |      -4.6 |       7.8 |          -11.6 |           10.4 |            0.48 |            42   |            44.4 |          2.3 |
|  63 | 2010-26 |      29.9 |        1.8 |      66.2 |      65.3 |     48.8 |     80.8 |   -0.9 |      -7.2 |       5.2 |           -9.2 |            9.1 |            0.57 |            59   |            53.5 |         -5.4 |
|  63 | 2016-26 |      18.7 |        1.7 |      66.1 |      65.8 |     41   |     80.9 |   -0.3 |      -6.4 |       5.6 |           -8.3 |            7.9 |            0.51 |            64.2 |            57.1 |         -7   |
|  63 | 2023-26 |       6.1 |        1.5 |      50.6 |      52.2 |     18.8 |     81.2 |    1.6 |     -13.8 |      12.9 |          -10.7 |           11.7 |            0.44 |            48.5 |            41.2 |         -7.2 |

Same accuracy as plain EUR/USD within noise (-2.5 / -0.3 points in 2010-26, +1.6 / +3.5 in 2016-26, -4.2 / +1.7 in 2023-26). It would also fail the bar: +3 points is reached in one cell of four.

### 5b. Risk-adjusted comparison and the cost of the hedge

Position = the day's call (+1 / 0 / -1), held from its entry fixing to the next session's entry fixing. Cost arithmetic, 1.2 pips per unit of turnover on EVERY pair traded, in the pair's own pip (0.01 for yen pairs), 2010-26 averages:

| expression | pairs traded | cost per unit of turnover | turnover a year | cost a year |
|:--|:--|--:|--:|--:|
| plain EUR/USD | EUR/USD x 1 | 1.02 bp | 40 | 41 bp |
| USD leg | five dollar pairs x 1/5 | 1.16 bp | 40 | 46 bp |
| EUR leg as a hedge (headline) | EUR/USD x 1 + five dollar pairs x 1/5 = six spreads | 2.18 bp | 40 | 87 bp |
| EUR leg, five direct crosses at 1.2 pips | EUR/JPY, EUR/GBP, EUR/CHF, EUR/CAD, EUR/AUD x 1/5 | 1.01 bp | 40 | 40 bp |
| EUR leg, five direct crosses at 3 pips | same | 2.53 bp | 40 | 101 bp |

The hedge doubles the cost per unit of notional (2.18 against 1.02 bp) while the hedged position is LESS volatile (5.7 against 8.1 % a year in 2010-26, 4.5 against 6.9 % since 2016), so per unit of risk it costs about three times as much. Trading the five crosses directly at a major's spread would cost the same as EUR/USD, but nobody quotes EUR/AUD or EUR/CAD at 1.2 pips; the 3-pip row is the realistic one. The rule changes its call about 40 times a year (20 round trips), so this is 40-100 bp a year against a gross edge of 172 bp a year on the euro leg in 2010-26 and 20 bp since 2016.

| expression                           | cost                          | era     |   sharpe_net |   t_net |   sharpe_gross |   ann_vol_bp_when_in |   turnover_per_year |   cost_bp_per_year |
|:-------------------------------------|:------------------------------|:--------|-------------:|--------:|---------------:|---------------------:|--------------------:|-------------------:|
| plain EUR/USD (H.10)                 | 1 pair, 1.2 pips              | 2010-26 |         0.66 |    2.77 |           0.74 |                807.6 |                39.9 |               40.7 |
| plain EUR/USD (H.10)                 | 1 pair, 1.2 pips              | 2016-26 |         0.47 |    1.56 |           0.55 |                691.2 |                36.3 |               38.9 |
| plain EUR/USD (H.10)                 | 1 pair, 1.2 pips              | 2023-26 |         0.63 |    1.25 |           0.72 |                655.1 |                35.2 |               37.8 |
| EUR leg (EW5)                        | hedge: 6 pairs, 1.2 pips each | 2010-26 |         0.22 |    0.92 |           0.45 |                569.8 |                39.9 |               86.9 |
| EUR leg (EW5)                        | hedge: 6 pairs, 1.2 pips each | 2016-26 |        -0.2  |   -0.68 |           0.07 |                452.6 |                36.3 |               81.1 |
| EUR leg (EW5)                        | hedge: 6 pairs, 1.2 pips each | 2023-26 |         0.1  |    0.2  |           0.45 |                355   |                35.2 |               78.7 |
| EUR leg (EW5), direct crosses        | 5 crosses, 1.2 pips each      | 2010-26 |         0.34 |    1.42 |           0.45 |                569.8 |                39.9 |               40.6 |
| EUR leg (EW5), direct crosses        | 5 crosses, 1.2 pips each      | 2016-26 |        -0.05 |   -0.18 |           0.07 |                452.6 |                36.3 |               36.2 |
| EUR leg (EW5), direct crosses        | 5 crosses, 1.2 pips each      | 2023-26 |         0.3  |    0.59 |           0.45 |                355   |                35.2 |               34.3 |
| EUR leg (EW5), direct crosses 3 pips | 5 crosses, 3 pips each        | 2010-26 |         0.18 |    0.76 |           0.45 |                569.8 |                39.9 |              101.5 |
| EUR leg (EW5), direct crosses 3 pips | 5 crosses, 3 pips each        | 2016-26 |        -0.23 |   -0.78 |           0.07 |                452.6 |                36.3 |               90.5 |
| EUR leg (EW5), direct crosses 3 pips | 5 crosses, 3 pips each        | 2023-26 |         0.07 |    0.14 |           0.45 |                355   |                35.2 |               85.9 |
| USD leg (EW5)                        | 5 pairs, 1.2 pips each        | 2010-26 |         0.43 |    1.79 |           0.54 |                637.6 |                39.9 |               46.2 |
| USD leg (EW5)                        | 5 pairs, 1.2 pips each        | 2016-26 |         0.47 |    1.57 |           0.58 |                608.6 |                36.3 |               42.3 |
| USD leg (EW5)                        | 5 pairs, 1.2 pips each        | 2023-26 |         0.41 |    0.82 |           0.52 |                599.8 |                35.2 |               41   |
| broad dollar USD6 (ADDED)            | 6 pairs at 1/6, 1.2 pips each | 2010-26 |         0.5  |    2.09 |           0.61 |                634.3 |                39.9 |               45.3 |
| broad dollar USD6 (ADDED)            | 6 pairs at 1/6, 1.2 pips each | 2016-26 |         0.49 |    1.63 |           0.59 |                599.8 |                36.3 |               41.7 |
| broad dollar USD6 (ADDED)            | 6 pairs at 1/6, 1.2 pips each | 2023-26 |         0.46 |    0.92 |           0.57 |                594.8 |                35.2 |               40.4 |
| plain EUR/USD (store closes)         | 1 pair, 1.2 pips              | 2010-26 |         0.57 |    2.38 |           0.64 |                830.6 |                39.9 |               40.7 |
| plain EUR/USD (store closes)         | 1 pair, 1.2 pips              | 2016-26 |         0.53 |    1.78 |           0.61 |                718.7 |                36.3 |               38.9 |
| plain EUR/USD (store closes)         | 1 pair, 1.2 pips              | 2023-26 |         0.23 |    0.45 |           0.32 |                664.2 |                35.2 |               37.7 |

Sharpe difference against plain EUR/USD (same calls, paired block bootstrap, 95 %):

| expression                    | era     |   d_sharpe_vs_plain |    lo |    hi |   pnl_corr_with_plain |
|:------------------------------|:--------|--------------------:|------:|------:|----------------------:|
| EUR leg (EW5)                 | 2010-26 |               -0.44 | -0.82 | -0.06 |                  0.62 |
| EUR leg (EW5)                 | 2016-26 |               -0.67 | -1.14 | -0.14 |                  0.5  |
| EUR leg (EW5)                 | 2023-26 |               -0.53 | -1.15 |  0.03 |                  0.42 |
| EUR leg (EW5), direct crosses | 2010-26 |               -0.32 | -0.71 |  0.05 |                  0.62 |
| EUR leg (EW5), direct crosses | 2016-26 |               -0.52 | -1    |  0.01 |                  0.5  |
| EUR leg (EW5), direct crosses | 2023-26 |               -0.33 | -0.94 |  0.25 |                  0.42 |
| USD leg (EW5)                 | 2010-26 |               -0.23 | -0.66 |  0.17 |                  0.71 |
| USD leg (EW5)                 | 2016-26 |                0    | -0.39 |  0.43 |                  0.76 |
| USD leg (EW5)                 | 2023-26 |               -0.22 | -0.66 |  0.29 |                  0.84 |
| broad dollar USD6 (ADDED)     | 2010-26 |               -0.16 | -0.5  |  0.17 |                  0.81 |
| broad dollar USD6 (ADDED)     | 2016-26 |                0.02 | -0.31 |  0.37 |                  0.84 |
| broad dollar USD6 (ADDED)     | 2023-26 |               -0.17 | -0.53 |  0.24 |                  0.89 |

The hedged expression loses 0.44 Sharpe in 2010-26 and 0.67 in 2016-26 (both intervals below zero) and is not better even before costs (gross 0.45 against 0.74; 0.07 against 0.55). The lower volatility of a basket does not rescue it: the edge falls faster than the risk. The dollar-leg expression is level with plain EUR/USD since 2016 and behind it over 2010-26.

Incremental test (Round 3 addendum): `meta.combine` EW of weak_signals + regime_trend, with each stream offered as a third arm:

| third_arm           | era     |   sr_2way |   sr_3way |   d_sr |   years_arm_in |
|:--------------------|:--------|----------:|----------:|-------:|---------------:|
| leg_decomposition   | 2010-26 |      0.56 |      0.5  |  -0.07 |             14 |
| leg_decomposition   | 2016-26 |      0.64 |      0.46 |  -0.17 |             14 |
| leg_decomposition   | 2023-26 |      0.36 |      0.34 |  -0.01 |             14 |
| leg_plain_agreement | 2010-26 |      0.56 |      0.58 |   0.02 |             14 |
| leg_plain_agreement | 2016-26 |      0.64 |      0.64 |   0.01 |             14 |
| leg_plain_agreement | 2023-26 |      0.36 |      0.48 |   0.13 |             14 |
| leg_usd             | 2010-26 |      0.56 |      0.52 |  -0.05 |             14 |
| leg_usd             | 2016-26 |      0.64 |      0.66 |   0.02 |             14 |
| leg_usd             | 2023-26 |      0.36 |      0.42 |   0.07 |             14 |
| leg_usd6            | 2010-26 |      0.56 |      0.53 |  -0.03 |             14 |
| leg_usd6            | 2016-26 |      0.64 |      0.66 |   0.02 |             14 |
| leg_usd6            | 2023-26 |      0.36 |      0.44 |   0.08 |             14 |

| stream              | era     |   corr_weak_signals |   corr_regime_trend |
|:--------------------|:--------|--------------------:|--------------------:|
| leg_decomposition   | 2010-26 |                0.27 |                0.32 |
| leg_decomposition   | 2016-26 |                0.23 |                0.27 |
| leg_plain_agreement | 2010-26 |                0.46 |                0.49 |
| leg_plain_agreement | 2016-26 |                0.49 |                0.52 |
| leg_usd             | 2010-26 |                0.34 |                0.33 |
| leg_usd             | 2016-26 |                0.38 |                0.39 |
| leg_usd6            | 2010-26 |                0.38 |                0.38 |
| leg_usd6            | 2016-26 |                0.41 |                0.43 |

The primary stream (`leg_decomposition` = euro leg, hedge costs) LOWERS the combination on 2016-26 (0.64 -> 0.46): fails. The plain agreement stream is the reference (the existing rule, 0.46-0.52 correlated with the live streams; adds nothing to them on 2016-26, as known).

### 5c. Other basket weights (candidates 3, 4, 5)

* Candidate 3, ECB trade weights: narrow EER group, overall weights including third-market effects, manufactures and services, 2021 (official figures from the ECB data API, `data/processed/cross/leg_ecb_trade_weights.csv`), renormalised over the five: GBP 47.1 %, CHF 26.8 %, JPY 16.5 %, CAD 6.2 %, AUD 3.4 %.
* Candidate 4, Fed broad-dollar-index weights, APPROXIMATE (2019 revision, quoted from memory because federalreserve.gov is blocked here; not verified): CAD 46.2 %, JPY 21.7 %, GBP 18.3 %, CHF 9.0 %, AUD 4.8 % after renormalising.
* Candidate 5, seven currencies at 1/7 (adds SEK and NOK).

| basket   | leg   |   h | era     |   n_indep |   acc_ref |   acc_leg |   gain |   gain_lo |   gain_hi |   stale_gain |
|:---------|:------|----:|:--------|----------:|----------:|----------:|-------:|----------:|----------:|-------------:|
| ECB      | E     |  21 | 2010-26 |      90.8 |      59.2 |      53.9 |   -5.4 |     -10.3 |      -0.4 |          1.7 |
| ECB      | E     |  21 | 2016-26 |      57   |      58.3 |      51.3 |   -7   |     -13.3 |       0   |          3.7 |
| ECB      | E     |  21 | 2023-26 |      19.4 |      52.9 |      53.2 |    0.2 |     -14.1 |      14.9 |          6.9 |
| ECB      | E     |  42 | 2010-26 |      45   |      62.9 |      57.7 |   -5.2 |     -13.7 |       3.2 |          2.1 |
| ECB      | E     |  42 | 2016-26 |      28   |      61.3 |      55.1 |   -6.2 |     -17.1 |       5.2 |          0.6 |
| ECB      | E     |  42 | 2023-26 |       9.3 |      48.1 |      56.7 |    8.6 |     -12.1 |      33.5 |          2.8 |
| ECB      | U     |  21 | 2010-26 |      90.8 |      59.2 |      57.9 |   -1.4 |      -7.2 |       4.1 |         -6.6 |
| ECB      | U     |  21 | 2016-26 |      57   |      58.3 |      61   |    2.7 |      -2.6 |       8.3 |         -6   |
| ECB      | U     |  21 | 2023-26 |      19.4 |      52.9 |      49.5 |   -3.4 |     -11.5 |       4.3 |         -5.5 |
| ECB      | U     |  42 | 2010-26 |      45   |      62.9 |      61.7 |   -1.3 |      -6.1 |       3.1 |         -4   |
| ECB      | U     |  42 | 2016-26 |      28   |      61.3 |      63.6 |    2.3 |      -1.7 |       7   |         -1.8 |
| ECB      | U     |  42 | 2023-26 |       9.3 |      48.1 |      49   |    0.9 |      -5.1 |       6.7 |          4.6 |
| ECB      | E-U   |  21 | 2010-26 |      90.8 |      57.9 |      53.9 |   -4   |     -12.4 |       4.9 |          8.3 |
| ECB      | E-U   |  21 | 2016-26 |      57   |      61   |      51.3 |   -9.7 |     -18.3 |      -0.7 |          9.7 |
| ECB      | E-U   |  21 | 2023-26 |      19.4 |      49.5 |      53.2 |    3.7 |     -12.1 |      21.8 |         12.4 |
| ECB      | E-U   |  42 | 2010-26 |      45   |      61.7 |      57.7 |   -3.9 |     -15.5 |       7.1 |          6   |
| ECB      | E-U   |  42 | 2016-26 |      28   |      63.6 |      55.1 |   -8.5 |     -21.6 |       4.8 |          2.4 |
| ECB      | E-U   |  42 | 2023-26 |       9.3 |      49   |      56.7 |    7.7 |     -14.6 |      34.3 |         -1.7 |
| FED      | E     |  21 | 2010-26 |      90.8 |      59.2 |      55.3 |   -3.9 |      -9.5 |       1.6 |          0.2 |
| FED      | E     |  21 | 2016-26 |      57   |      58.3 |      52.5 |   -5.8 |     -12.7 |       1.7 |          1.8 |
| FED      | E     |  21 | 2023-26 |      19.4 |      52.9 |      55.1 |    2.2 |     -14.6 |      19.2 |         12.7 |
| FED      | E     |  42 | 2010-26 |      45   |      62.9 |      60.3 |   -2.6 |     -10.4 |       5.4 |         -0.5 |
| FED      | E     |  42 | 2016-26 |      28   |      61.3 |      57.5 |   -3.8 |     -14.7 |       6.6 |         -0.8 |
| FED      | E     |  42 | 2023-26 |       9.3 |      48.1 |      56.7 |    8.6 |     -10.8 |      32.2 |          9   |
| FED      | U     |  21 | 2010-26 |      90.8 |      59.2 |      56.8 |   -2.5 |      -9.4 |       3.7 |         -8.7 |
| FED      | U     |  21 | 2016-26 |      57   |      58.3 |      59.1 |    0.8 |      -4.3 |       6   |         -5.6 |
| FED      | U     |  21 | 2023-26 |      19.4 |      52.9 |      47.8 |   -5.1 |     -13.4 |       4.3 |         -7.7 |
| FED      | U     |  42 | 2010-26 |      45   |      62.9 |      60.4 |   -2.6 |      -8.4 |       2.9 |         -2.6 |
| FED      | U     |  42 | 2016-26 |      28   |      61.3 |      63.5 |    2.2 |      -2.4 |       7.7 |          0.7 |
| FED      | U     |  42 | 2023-26 |       9.3 |      48.1 |      51.5 |    3.5 |      -4.9 |      12.3 |          3.8 |
| FED      | E-U   |  21 | 2010-26 |      90.8 |      56.8 |      55.3 |   -1.5 |     -10.9 |       8.2 |          8.9 |
| FED      | E-U   |  21 | 2016-26 |      57   |      59.1 |      52.5 |   -6.6 |     -15.4 |       2.9 |          7.5 |
| FED      | E-U   |  21 | 2023-26 |      19.4 |      47.8 |      55.1 |    7.4 |     -14   |      28   |         20.3 |
| FED      | E-U   |  42 | 2010-26 |      45   |      60.4 |      60.3 |   -0.1 |     -11.5 |      11.4 |          2.1 |
| FED      | E-U   |  42 | 2016-26 |      28   |      63.5 |      57.5 |   -6   |     -19.9 |       6.8 |         -1.5 |
| FED      | E-U   |  42 | 2023-26 |       9.3 |      51.5 |      56.7 |    5.1 |     -19.1 |      33.2 |          5.1 |
| EW7      | E     |  21 | 2010-26 |      90.8 |      59.2 |      51.3 |   -8   |     -13.2 |      -3.1 |         -3.8 |
| EW7      | E     |  21 | 2016-26 |      57   |      58.3 |      48.5 |   -9.8 |     -16.4 |      -2.8 |         -3.6 |
| EW7      | E     |  21 | 2023-26 |      19.4 |      52.9 |      49.5 |   -3.4 |     -19.5 |      14.3 |          7.2 |
| EW7      | E     |  42 | 2010-26 |      45   |      62.9 |      55.2 |   -7.7 |     -17.5 |       2.8 |         -2.2 |
| EW7      | E     |  42 | 2016-26 |      28   |      61.3 |      53.4 |   -7.9 |     -21.7 |       6.6 |         -3.6 |
| EW7      | E     |  42 | 2023-26 |       9.3 |      48.1 |      57.9 |    9.9 |     -17.8 |      41.3 |         12.2 |
| EW7      | U     |  21 | 2010-26 |      90.8 |      59.2 |      57.6 |   -1.6 |      -7   |       3.6 |         -6.9 |
| EW7      | U     |  21 | 2016-26 |      57   |      58.3 |      59.2 |    0.9 |      -3.7 |       5.6 |         -4.2 |
| EW7      | U     |  21 | 2023-26 |      19.4 |      52.9 |      49.8 |   -3.2 |     -11.9 |       5.4 |         -6.9 |
| EW7      | U     |  42 | 2010-26 |      45   |      62.9 |      61.6 |   -1.3 |      -5.5 |       2.8 |         -2.7 |
| EW7      | U     |  42 | 2016-26 |      28   |      61.3 |      62.6 |    1.3 |      -2.4 |       5.4 |         -0.1 |
| EW7      | U     |  42 | 2023-26 |       9.3 |      48.1 |      48.2 |    0.1 |      -4.6 |       4   |          1.6 |
| EW7      | E-U   |  21 | 2010-26 |      90.8 |      57.6 |      51.3 |   -6.3 |     -15.1 |       2.3 |          3.1 |
| EW7      | E-U   |  21 | 2016-26 |      57   |      59.2 |      48.5 |  -10.7 |     -18.9 |      -2   |          0.6 |
| EW7      | E-U   |  21 | 2023-26 |      19.4 |      49.8 |      49.5 |   -0.2 |     -18.8 |      21.8 |         14.1 |
| EW7      | E-U   |  42 | 2010-26 |      45   |      61.6 |      55.2 |   -6.4 |     -18.5 |       6.3 |          0.5 |
| EW7      | E-U   |  42 | 2016-26 |      28   |      62.6 |      53.4 |   -9.2 |     -24.7 |       7.1 |         -3.5 |
| EW7      | E-U   |  42 | 2023-26 |       9.3 |      48.2 |      57.9 |    9.7 |     -21.1 |      44.4 |         10.5 |

`leg` E / U = that leg against plain EUR/USD (`acc_ref` = plain); `E-U` = euro leg against dollar leg (`acc_ref` = dollar leg). **The answer does not change with the weights**: the euro leg is 2.6-9.8 points below plain EUR/USD in every 2010-26 and 2016-26 cell under all three weightings, the dollar leg is within about 3 points of it, and the dollar leg is at or above the euro leg in every such cell. The gap is smallest with the Fed weights, where the basket is half Canadian dollar.

## 6. ADDED after the first run

### 6a. Exact split of the P&L between the legs (descriptive)

Because S = E - U bar by bar, the gross P&L of any call on EUR/USD is the P&L of the same call on the euro leg plus its P&L on the (sign-flipped) dollar leg, with no residual (`identity_err_bp` = 0). bp a year, gross, all sessions:

| signal       | era     |   bp_per_year_eurusd |   bp_per_year_eur_leg |   bp_per_year_usd_leg |   share_from_usd_leg |   t_eurusd |   t_eur_leg |   t_usd_leg |   sharpe_gross_eur_leg |   sharpe_gross_usd_leg |
|:-------------|:--------|---------------------:|----------------------:|----------------------:|---------------------:|-----------:|------------:|------------:|-----------------------:|-----------------------:|
| agreement    | 2010-26 |                403.1 |                 171.8 |                 231.4 |                 0.57 |       3.08 |        1.86 |        2.24 |                   0.45 |                   0.54 |
| agreement    | 2016-26 |                253.2 |                  20.3 |                 233   |                 0.92 |       1.84 |        0.22 |        1.92 |                   0.07 |                   0.58 |
| agreement    | 2023-26 |                302.7 |                 102.1 |                 200.5 |                 0.66 |       1.43 |        0.89 |        1.03 |                   0.45 |                   0.52 |
| positioning  | 2010-26 |                562.6 |                 180.5 |                 382.1 |                 0.68 |       2.85 |        1.37 |        2.42 |                   0.33 |                   0.58 |
| positioning  | 2016-26 |                450.2 |                  -5.3 |                 455.4 |                 1.01 |       2.1  |       -0.04 |        2.39 |                  -0.01 |                   0.71 |
| positioning  | 2023-26 |                238.2 |                  59.3 |                 178.9 |                 0.75 |       0.71 |        0.32 |        0.58 |                   0.16 |                   0.29 |
| spread_trend | 2010-26 |                267.8 |                  86.7 |                 181.1 |                 0.68 |       1.36 |        0.66 |        1.15 |                   0.16 |                   0.28 |
| spread_trend | 2016-26 |                191.6 |                  12.6 |                 179.1 |                 0.93 |       0.89 |        0.09 |        0.94 |                   0.03 |                   0.28 |
| spread_trend | 2023-26 |                456.9 |                 107.4 |                 349.5 |                 0.76 |       1.37 |        0.58 |        1.14 |                   0.29 |                   0.57 |
| house_score  | 2010-26 |                668.3 |                 290.6 |                 377.7 |                 0.57 |       3.39 |        2.21 |        2.39 |                   0.53 |                   0.57 |
| house_score  | 2016-26 |                466.2 |                  94.5 |                 371.7 |                 0.8  |       2.17 |        0.7  |        1.95 |                   0.21 |                   0.58 |
| house_score  | 2023-26 |                302.4 |                 142   |                 160.3 |                 0.53 |       0.9  |        0.77 |        0.52 |                   0.39 |                   0.26 |

For every input and every era more than half of the money came from the dollar leg; over 2016-26 it is 80-100 %. No t-statistic on the euro leg reaches 1 in the 2016-26 or 2023-26 windows. (Direction accuracy and money can disagree: positioning calls the euro leg's direction as often as the dollar leg's, but the dollar leg moves further when it is right.)

### 6b. Candidate 6, POST HOC: the calls on a broad dollar basket (dollar against EUR, JPY, GBP, CHF, CAD, AUD at 1/6 each)

Chosen after seeing the per-pair table below, so it could only ever be a lead. It is not one:

|   h | era     |   n_indep |   per_year |   acc_ref |   acc_leg |   leg_lo |   leg_hi |   gain |   gain_lo |   gain_hi |   rand_gain_lo |   rand_gain_hi |   p_random_gain |   stale_acc_ref |   stale_acc_leg |   stale_gain |
|----:|:--------|----------:|-----------:|----------:|----------:|---------:|---------:|-------:|----------:|----------:|---------------:|---------------:|----------------:|----------------:|----------------:|-------------:|
|  21 | 2010-26 |      90.8 |        5.3 |      59.2 |      57.8 |     46.9 |     66.8 |   -1.4 |      -7.3 |       3.8 |           -5.3 |            4.7 |            0.7  |            59.4 |            53.6 |         -5.8 |
|  21 | 2016-26 |      57   |        5.2 |      58.3 |      61.1 |     48.4 |     72.9 |    2.8 |      -1.3 |       7   |           -4.4 |            3.7 |            0.08 |            59.2 |            55.7 |         -3.5 |
|  21 | 2023-26 |      19.4 |        4.9 |      52.9 |      50.2 |     31.7 |     72.7 |   -2.7 |      -8.6 |       3.7 |           -5.5 |            5.2 |            0.76 |            50.5 |            45   |         -5.5 |
|  42 | 2010-26 |      45   |        2.6 |      62.9 |      62.5 |     47.6 |     74.9 |   -0.4 |      -4.5 |       3.3 |           -6.9 |            7.1 |            0.56 |            57.2 |            54   |         -3.2 |
|  42 | 2016-26 |      28   |        2.5 |      61.3 |      64.3 |     45.8 |     79.3 |    3   |      -0.2 |       6.6 |           -4.1 |            3.9 |            0.07 |            58.1 |            57.3 |         -0.9 |
|  42 | 2023-26 |       9.3 |        2.3 |      48.1 |      50.3 |     26.7 |     81.1 |    2.2 |      -3.1 |       7.4 |          -10.1 |            9.4 |            0.38 |            42   |            44.9 |          2.8 |
|  63 | 2010-26 |      29.9 |        1.8 |      66.2 |      65.3 |     48.8 |     80.8 |   -0.9 |      -6.5 |       4.6 |           -7.9 |            7.9 |            0.59 |            59   |            54.2 |         -4.8 |
|  63 | 2016-26 |      18.7 |        1.7 |      66.1 |      66   |     41   |     80.9 |   -0.1 |      -5.4 |       5.1 |           -7   |            6.3 |            0.49 |            64.2 |            58.2 |         -5.9 |
|  63 | 2023-26 |       6.1 |        1.5 |      50.6 |      51.7 |     18.8 |     81.2 |    1   |     -12.3 |      11.1 |           -8.9 |            8.7 |            0.46 |            48.5 |            44.1 |         -4.4 |

Accuracy within about 3 points of plain EUR/USD in every cell (-1.4 / -0.4 in 2010-26, +2.8 / +3.0 in 2016-26), net Sharpe +0.50 / +0.49 / +0.46 against +0.66 / +0.47 / +0.63 for plain EUR/USD. Spreading the call over six dollar pairs neither helps nor hurts; it is the same bet with six tickets.

### 6c. Per single pair (declared descriptive)

Agreement calls scored on each pair. EURxxx: right when the euro rose against xxx after a long call; USDxxx: right when the dollar FELL against xxx after a long call.

| series   |   h | era     |   n_indep |   acc |   lo |   hi |   base_mean |   p_random |
|:---------|----:|:--------|----------:|------:|-----:|-----:|------------:|-----------:|
| EURJPY   |  21 | 2010-26 |      90.8 |  55.5 | 44.7 | 64.8 |        49.4 |       0.06 |
| EURGBP   |  21 | 2010-26 |      90.8 |  52.3 | 41.5 | 61.6 |        50.2 |       0.31 |
| EURCHF   |  21 | 2010-26 |      90.8 |  54.6 | 44.7 | 64.8 |        50.5 |       0.17 |
| EURCAD   |  21 | 2010-26 |      90.8 |  52.1 | 41.5 | 61.6 |        50   |       0.37 |
| EURAUD   |  21 | 2010-26 |      90.8 |  45.3 | 35.2 | 55.3 |        50.1 |       0.88 |
| USDJPY   |  21 | 2010-26 |      90.5 |  49.1 | 38.8 | 59   |        50.4 |       0.65 |
| USDGBP   |  21 | 2010-26 |      90.5 |  55.6 | 45.3 | 65.4 |        49.7 |       0.05 |
| USDCHF   |  21 | 2010-26 |      90.6 |  56   | 45.8 | 65.8 |        49.7 |       0.1  |
| USDCAD   |  21 | 2010-26 |      90.4 |  56.3 | 46.4 | 66.4 |        50.1 |       0.03 |
| USDAUD   |  21 | 2010-26 |      90.7 |  57.1 | 46.9 | 66.8 |        50   |       0.02 |
| EURJPY   |  21 | 2016-26 |      57   |  53.6 | 41.6 | 66.6 |        49.8 |       0.22 |
| EURGBP   |  21 | 2016-26 |      57   |  48.9 | 36.6 | 61.7 |        50   |       0.62 |
| EURCHF   |  21 | 2016-26 |      57   |  50.4 | 38.3 | 63.4 |        50.3 |       0.5  |
| EURCAD   |  21 | 2016-26 |      57   |  49.9 | 36.6 | 61.7 |        50   |       0.47 |
| EURAUD   |  21 | 2016-26 |      57   |  44.5 | 31.8 | 56.7 |        50   |       0.91 |
| USDJPY   |  21 | 2016-26 |      56.8 |  53.4 | 39.9 | 65   |        50.2 |       0.17 |
| USDGBP   |  21 | 2016-26 |      56.7 |  58.3 | 45   | 69.8 |        49.8 |       0.04 |
| USDCHF   |  21 | 2016-26 |      56.9 |  55.4 | 41.6 | 66.6 |        49.8 |       0.12 |
| USDCAD   |  21 | 2016-26 |      56.8 |  57.9 | 45   | 69.8 |        50.1 |       0.03 |
| USDAUD   |  21 | 2016-26 |      56.9 |  58.9 | 46.7 | 71.4 |        49.9 |       0    |
| EURJPY   |  42 | 2010-26 |      45   |  58.8 | 43.3 | 71   |        49.3 |       0.04 |
| EURGBP   |  42 | 2010-26 |      45   |  56.1 | 41.2 | 69.1 |        50.2 |       0.16 |
| EURCHF   |  42 | 2010-26 |      45   |  56.7 | 43.3 | 71   |        50.5 |       0.11 |
| EURCAD   |  42 | 2010-26 |      45   |  57.2 | 43.3 | 71   |        49.6 |       0.13 |
| EURAUD   |  42 | 2010-26 |      45   |  43.6 | 30.9 | 58.8 |        50   |       0.88 |
| USDJPY   |  42 | 2010-26 |      44.9 |  52.9 | 39.1 | 67.1 |        50.5 |       0.29 |
| USDGBP   |  42 | 2010-26 |      44.9 |  58.3 | 43.3 | 71   |        49.7 |       0.04 |
| USDCHF   |  42 | 2010-26 |      44.9 |  61.8 | 47.6 | 74.9 |        49.5 |       0.02 |
| USDCAD   |  42 | 2010-26 |      44.9 |  58.5 | 43.3 | 71   |        50.2 |       0.02 |
| USDAUD   |  42 | 2010-26 |      44.9 |  63   | 47.6 | 74.9 |        50.1 |       0    |
| EURJPY   |  42 | 2016-26 |      28   |  57.9 | 39.1 | 73.5 |        49.8 |       0.24 |
| EURGBP   |  42 | 2016-26 |      28   |  51.9 | 35.8 | 70.5 |        50   |       0.4  |
| EURCHF   |  42 | 2016-26 |      28   |  57.8 | 39.1 | 73.5 |        50.3 |       0.07 |
| EURCAD   |  42 | 2016-26 |      28   |  51.2 | 32.6 | 67.4 |        50.2 |       0.41 |
| EURAUD   |  42 | 2016-26 |      28   |  42.6 | 26.5 | 60.9 |        50.3 |       0.91 |
| USDJPY   |  42 | 2016-26 |      28   |  56.8 | 39.1 | 73.5 |        49.9 |       0.06 |
| USDGBP   |  42 | 2016-26 |      28   |  61.9 | 42.4 | 76.4 |        49.7 |       0.03 |
| USDCHF   |  42 | 2016-26 |      28   |  60.2 | 42.4 | 76.4 |        49.5 |       0.05 |
| USDCAD   |  42 | 2016-26 |      28   |  60.7 | 42.4 | 76.4 |        49.6 |       0.02 |
| USDAUD   |  42 | 2016-26 |      28   |  62.5 | 42.4 | 76.4 |        49.9 |       0    |

After a long-EUR/USD call the dollar tends to fall against sterling, the franc, the Canadian and the Australian dollar as well (55-63 % in these cells); the yen is the weak spot (49-57 %). The euro itself does best against the yen (54-59 %) and LOSES to the Australian dollar (43-45 %): a 'long EUR/USD' call is in practice a 'dollar down' call, and the euro is not the currency that gains most from it. Ten pairs, four cells each: single-pair differences are descriptive, none is a result.

## 7. Sanity checks

**Timing** (the conclusion must not depend on the fixing used). Accuracy of the same calls on S / E / U and the two gains:

| prices                                     |   h | era     |   n_indep |   acc_S |   acc_E |   acc_U |   gain_E |   gain_U |
|:-------------------------------------------|----:|:--------|----------:|--------:|--------:|--------:|---------:|---------:|
| H.10 same-day fixing (5 h before the call) |  21 | 2010-26 |      90.7 |    58.6 |    53.1 |    57.1 |     -5.4 |     -1.5 |
| H.10 same-day fixing (5 h before the call) |  21 | 2016-26 |      56.9 |    58.2 |    50.4 |    60.9 |     -7.9 |      2.7 |
| H.10 same-day fixing (5 h before the call) |  21 | 2023-26 |      19.5 |    53.3 |    50.9 |    49.4 |     -2.4 |     -3.9 |
| H.10 same-day fixing (5 h before the call) |  42 | 2010-26 |      44.9 |    62.9 |    57.4 |    62.9 |     -5.5 |      0   |
| H.10 same-day fixing (5 h before the call) |  42 | 2016-26 |      28   |    61.4 |    55.5 |    65.2 |     -5.9 |      3.8 |
| H.10 same-day fixing (5 h before the call) |  42 | 2023-26 |       9.3 |    47.7 |    54.4 |    50.5 |      6.7 |      2.8 |
| H.10 next fixing (declared)                |  21 | 2010-26 |      90.7 |    59.2 |    53.2 |    56.8 |     -6   |     -2.5 |
| H.10 next fixing (declared)                |  21 | 2016-26 |      56.9 |    58.3 |    50.3 |    59.9 |     -8   |      1.6 |
| H.10 next fixing (declared)                |  21 | 2023-26 |      19.4 |    52.9 |    51.5 |    48.8 |     -1.5 |     -4.2 |
| H.10 next fixing (declared)                |  42 | 2010-26 |      44.9 |    62.9 |    57.4 |    62.7 |     -5.5 |     -0.3 |
| H.10 next fixing (declared)                |  42 | 2016-26 |      28   |    61.3 |    55.8 |    64.8 |     -5.5 |      3.5 |
| H.10 next fixing (declared)                |  42 | 2023-26 |       9.3 |    48.1 |    53.6 |    49.7 |      5.5 |      1.7 |
| H.10 one fixing later                      |  21 | 2010-26 |      90.6 |    59.5 |    53.5 |    56.6 |     -6   |     -2.8 |
| H.10 one fixing later                      |  21 | 2016-26 |      56.8 |    58.8 |    51   |    59.6 |     -7.8 |      0.8 |
| H.10 one fixing later                      |  21 | 2023-26 |      19.4 |    52.3 |    50.6 |    48.4 |     -1.7 |     -3.9 |
| H.10 one fixing later                      |  42 | 2010-26 |      44.9 |    62.4 |    56.8 |    62.6 |     -5.6 |      0.2 |
| H.10 one fixing later                      |  42 | 2016-26 |      28   |    60.9 |    55.3 |    64.7 |     -5.7 |      3.8 |
| H.10 one fixing later                      |  42 | 2023-26 |       9.3 |    48.2 |    53.1 |    50.5 |      4.9 |      2.3 |
| ECB reference rates, next fixing           |  21 | 2010-26 |      90.7 |    57.9 |    53   |    56.3 |     -4.9 |     -1.6 |
| ECB reference rates, next fixing           |  21 | 2016-26 |      56.9 |    57.4 |    49.8 |    59.8 |     -7.6 |      2.4 |
| ECB reference rates, next fixing           |  21 | 2023-26 |      19.5 |    52.8 |    50.4 |    50.1 |     -2.4 |     -2.7 |
| ECB reference rates, next fixing           |  42 | 2010-26 |      44.9 |    63.7 |    57.1 |    62.4 |     -6.6 |     -1.2 |
| ECB reference rates, next fixing           |  42 | 2016-26 |      28   |    62.9 |    55.5 |    64.3 |     -7.3 |      1.5 |
| ECB reference rates, next fixing           |  42 | 2023-26 |       9.2 |    50.1 |    54.1 |    49.5 |      4   |     -0.6 |

Entering at the same-day fixing (five hours before the call, formally a peek), at the declared next fixing, one fixing later, or on the ECB's 14:15 CET fixings gives the same picture to within a point or two: euro leg 5-8 points below plain EUR/USD in 2010-26 and 2016-26, dollar leg within 4 points of it. Nothing here is a same-day join across stamp conventions, and lagging the cross series by a day changes nothing.

**Shuffled labels** (one joint permutation of all outcomes and of the returns the house score is fitted on, five seeds, 2010-26):

|   seed |   h | era     |   call_days |   acc_S |   acc_E |   acc_U |   gain_E |
|-------:|----:|:--------|------------:|--------:|--------:|--------:|---------:|
|      0 |  21 | 2010-26 |        1835 |    49.3 |    49.5 |    48.3 |      0.2 |
|      0 |  42 | 2010-26 |        1831 |    48.5 |    48.4 |    49.5 |     -0.1 |
|      1 |  21 | 2010-26 |        1454 |    50.8 |    50   |    48.8 |     -0.8 |
|      1 |  42 | 2010-26 |        1452 |    50.1 |    50.7 |    48.5 |      0.7 |
|      2 |  21 | 2010-26 |        2009 |    49.2 |    49   |    48.9 |     -0.2 |
|      2 |  42 | 2010-26 |        2002 |    49   |    50.2 |    49.1 |      1.2 |
|      3 |  21 | 2010-26 |        1714 |    50.2 |    50.2 |    50.5 |      0.1 |
|      3 |  42 | 2010-26 |        1710 |    50.8 |    50.4 |    51.3 |     -0.3 |
|      4 |  21 | 2010-26 |        2023 |    51.6 |    49.8 |    52.3 |     -1.8 |
|      4 |  42 | 2010-26 |        2020 |    51.3 |    50.1 |    51.9 |     -1.2 |

Accuracy 48-52 % on every series and the gain within +-2 points: the pipeline finds nothing when there is nothing.

**Identity**: section 1 (exact). **Look-ahead**: the calls are the committee module's walk-forward calls (its truncation control: 0 of 48 columns differ); no parameter is fitted on the legs; the basket weights are fixed constants (the ECB weights are 2021 figures applied to the whole history, which is a mild anachronism in a robustness run, not a leak of prices).

## 8. Candidates and counts

* Candidates: **6**. Declared: (1) euro leg, equal weights [primary]; (2) dollar leg, equal weights [mirror]; (3) ECB weights; (4) Fed weights; (5) seven-currency basket. Added post hoc: (6) broad dollar. Each was scored at 21 / 42 / 63 sessions in three eras with the same tables; the Sharpe comparison and the incremental test are other yardsticks on candidates 1, 2 and 6, not new candidates.
* Declared descriptive cells: 4 signals x 3 instruments x 9 (horizon, era) = 108 accuracies; 10 single pairs x 9 = 90. Checks: 4 timing variants, 5 shuffles.

## 9. Suspicious, and caveats

* **Entry-time noise in 2023-26.** The same calls on plain EUR/USD have a net Sharpe of 0.63 when entered at the next noon fixing and 0.23 on the feature-store closes 19 hours earlier (2010-26: 0.66 vs 0.57; 2016-26: 0.47 vs 0.53). Accuracy at 21-63 sessions reconciles within a point, so this is the daily-stream yardstick being fragile on four years with about 35 position changes a year, not a data error; all comparisons in this report are between instruments on the SAME fixings, where it cancels. It is one more reason not to read anything into 2023-26.
* **The call flickers.** 340 separate call episodes in 17 years, about 6 sessions each; the phase-averaged accuracy scores every call day on the following 21-63 sessions regardless. This is the published benchmark's convention and is the same for every instrument here.
* **The stale euro leg** (section 4): on the euro leg the three-month-old calls beat the live ones (59 vs 53 % at 21 sessions). Whatever the rule has on the euro side is slow drift or noise, not timing. On plain EUR/USD the stale copy scores the same as the live calls at 21 sessions (59.4 vs 59.2 %), as the committee report already found: the live calls' dollar-leg timing and the stale calls' euro-leg drift happen to add up to the same number.
* **Fed weights are from memory**, not from the source (blocked). They enter one robustness candidate whose result agrees with the other baskets.
* **Spot only.** No carry in any expression, as everywhere in the project. A long-euro-against-basket position earns or pays a different carry from long EUR/USD (the basket holds two low-yield and three higher-yield currencies); with the gross edge on the euro leg at 20 bp a year since 2016 this cannot change the verdict.
* **Small samples.** 2023-26 has 19 / 9 / 6 independent calls at 21 / 42 / 63 sessions; the Wilson intervals are 40-60 points wide.
* **H.10 is one noon snapshot** of buying rates rounded to four decimals (about 1 bp); irrelevant against 21-session moves of 150-230 bp.
* The attribution rule was declared in advance and returns 'cannot be attributed'; the stronger statement in the verdict ('more dollar than euro, almost only dollar since 2016') rests on the exact P&L split, which was added after the first run and is descriptive.

## 10. Files

* `src/eurusd/arms/leg_decomposition.py` - declaration in the docstring, `run()` entry point, `write_report()`.
* `experiments/results/arms/leg_decomposition_*.csv`: `reconcile`, `accuracy`, `primary`, `verdict_rows`, `mirror`, `e_vs_u`, `e_vs_u_inputs`, `alt_baskets`, `broad_dollar`, `sharpe`, `sharpe_diff`, `cost_table`, `incremental`, `pnl_corr`, `attribution`, `call_mix`, `pairs`, `timing`, `shuffled`, `leg_stats`, `check_h10_vs_store`, `check_h10_vs_ecb`.
* `experiments/results/arms/leg_decomposition_positions.parquet` (primary expression, 2010+: `pos`, `fwd_bp`, `net_bp`, booked one session later so that it lines up with the close-to-close arms) and `leg_decomposition_calls.parquet` (the walk-forward calls and the three input signs).
* New data: `data/processed/cross/leg_ecb_ref_rates.parquet` (ECB reference rates, USD JPY GBP CHF CAD AUD SEK NOK per EUR, 1999-01-04 .. 2026-11-17, no lag needed: used only at fixings after the call) and `data/processed/cross/leg_ecb_trade_weights.csv` (ECB narrow-group trade weights, 2021).
