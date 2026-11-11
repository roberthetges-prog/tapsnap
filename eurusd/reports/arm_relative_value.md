# Arm L — relative_value: EUR/USD against the rest of the currency market

Code: `src/eurusd/arms/relative_value.py` (`run(cost_pips=1.2)`; `python src/eurusd/arms/relative_value.py` also writes the
leak checks, incremental test, probes and data checks). Results in `experiments/results/arms/`:
`relative_value_report.csv` (12 candidates + 12 five-day-hold diagnostics + cost sensitivity; `variant`, `kind`, `final`),
`relative_value_positions.parquet` (OOS positions of the final variant: `pos`, `fwd_bp`, `net_bp`),
`relative_value_single_signals.csv`, `_weights.csv`, `_hit_rates.csv`, `_leakchecks.csv`, `_incremental.csv`, `_pnl_corr.csv`,
`_noon_diagnostic.csv`, `_decomposition.csv`, `_yahoo_probe.csv`, `_data_checks.csv`, `_all_net_bp.parquet`.
Log: `experiments/results/arms/logs/relative_value.log`.

**Verdict: clean negative.** None of the 11 relative-value signals nor their t-stat combination predicts EUR/USD after
costs; most are negative even before costs. The final variant picked by the pre-declared rule (`lead_eurx1`) has net
Sharpe -0.23 / -0.48 / -0.32 for 2010-26 / 2016-26 / 2023-26 and a 49 % hit rate. The arm fails the success bar and the
incremental test. The durable output is the timing work on the cross-pair data (section 1).

## 1. Data sources and timing treatment

| series | source | range | role | lag used |
|:--|:--|:--|:--|:--|
| GBP JPY CHF AUD CAD NZD SEK NOK and EUR vs USD | Federal Reserve H.10 noon New York buying rates, datahub.io copy of the full table (`data/raw/datahub/exchange-rates_data_daily.csv`, the raw file behind `data/macro/datahub_fx_fed_h10_daily.csv`); cached as `data/processed/cross/relative_value_h10_g10.parquet` | 2002-01-02 .. 2026-11-06, 6,230 dates | **every signal** | none beyond the fixing itself: noon New York of date D is used at the 17:00 New York close of D (5 hours later). One-calendar-day lag (feature-store convention) run as a leak check |
| EUR/USD hourly | `data/processed/EURUSD_H1.parquet` | 2003 .. 2026-11-06 | all P&L (17:00 NY closes); 12:00 NY bar verifies the H10 instant | - |
| GBPUSD=X USDJPY=X USDCHF=X AUDUSD=X USDCAD=X NZDUSD=X USDSEK=X USDNOK=X EURGBP=X EURJPY=X EURCHF=X DX-Y.NYB | Yahoo chart API, `data/processed/cross/<name>_D1.parquet` (7 already there; `usdcad`, `nzdusd`, `usdsek`, `usdnok`, `eurchf` fetched by this arm, 2003 .. 2026-11-10) | 2003 .. 2026 (AUDUSD=X from 2006-05) | **verification and the look-ahead probe only; not used in any signal** | - |

What was used: H10 for all nine currencies in all years. Yahoo for none, for the three reasons below.

**(a) The H10 instant is noon New York, verified against our own bars.** H10 EUR/USD on date D against the open of our
hourly bar at each New York hour of D (2003-2026):

|   ny_hour_bar_open |    n |   median_abs_diff_pips |   p90_abs_diff_pips |   daily_return_corr |
|-------------------:|-----:|-----------------------:|--------------------:|--------------------:|
|                  8 | 5908 |                 21.242 |              68.2   |               0.623 |
|                  9 | 5914 |                 18.644 |              56.596 |               0.745 |
|                 10 | 5915 |                 14.118 |              44.646 |               0.835 |
|                 11 | 5917 |                  8.223 |              26.153 |               0.941 |
|                 12 | 5911 |                  1.03  |               2.893 |               0.997 |
|                 13 | 5915 |                  6.87  |              21.159 |               0.959 |
|                 14 | 5910 |                  8.652 |              28.88  |               0.925 |
|                 15 | 5905 |                 10.754 |              35.87  |               0.88  |
|                 16 | 5876 |                 11.729 |              39.668 |               0.852 |
|                 17 | 4719 |                 12.576 |              42.97  |               0.866 |

The 12:00 bar matches to 1.0 pip (median) with a daily-return correlation of 0.997; every other hour is far worse. So
the H10 panel is a synchronous snapshot of all nine currencies taken 5 hours before the close at which we trade.
The decomposition uses H10's own EUR rate (same source, same instant as the basket). Our own 12:00 bar is not used in
the residual because on 26 fast-market days (7 of them in March 2020) it differs from the fixing by more than 20
pips, which would be pure sampling noise in a residual whose daily sd is 20 bp.

**(b) Yahoo's daily FX "close" changed meaning in the third quarter of 2010.** Yahoo EURUSD=X close stamped London date
D against our price at 00:00 London of D plus an offset (median absolute difference in pips):

|   hours_after_00:00_London_of_stamp_date |   median_abs_diff_pips_2003_2009 |   median_abs_diff_pips_2011_2015 |   median_abs_diff_pips_2016_2026 |
|-----------------------------------------:|---------------------------------:|---------------------------------:|---------------------------------:|
|                                      -24 |                           62.99  |                           32.628 |                           22.636 |
|                                        0 |                           48.971 |                            2.483 |                            1.993 |
|                                       12 |                           34.015 |                           25.765 |                           17.46  |
|                                       21 |                            6.996 |                           41.66  |                           29.101 |
|                                       24 |                            1.068 |                           43.322 |                           29.48  |
|                                       48 |                           35.03  |                           58.424 |                           38.9   |

Until mid-2010 the bar stamped D closes at 24:00 London of D (1.1 pips; 2-3 hours AFTER our 17:00 New York close of D).
From late 2010 the "close" stamped D is the price at 00:00 London of D, i.e. the START of the stamped day (2.0-2.5
pips; 21-22 hours before our close of D). The share of days closer to the start-of-day reading is 2 % in 2010 Q2,
65 % in 2010 Q3, 95 % in 2010 Q4. This is the "unreliable 2003-2010 Yahoo history" of round 1: the prices are fine,
the stamp convention is different. The same switch shows in every dollar pair and cross (1-day return correlation
with the H10 return of the same day vs the previous day; a 5-day-return correlation is timing-robust):

|    n | pair     | era       | first      |   corr_h10_prev_day |   corr_h10_same_day |   corr_h10_next_day |   corr_5d_returns |   n_abs_5d_gap_gt_200bp |
|-----:|:---------|:----------|:-----------|--------------------:|--------------------:|--------------------:|------------------:|------------------------:|
| 1523 | GBPUSD=X | 2003-2009 | 2003-12-01 |               0.008 |               0.856 |               0.18  |             0.967 |                       7 |
| 1252 | GBPUSD=X | 2011-2015 | 2003-12-01 |               0.809 |               0.16  |              -0.008 |             0.823 |                       5 |
| 2706 | GBPUSD=X | 2016-2026 | 2003-12-01 |               0.814 |               0.223 |               0.015 |             0.848 |                      37 |
| 1739 | USDJPY=X | 2003-2009 | 2003-01-02 |              -0.01  |               0.569 |               0.085 |             0.865 |                      16 |
| 1252 | USDJPY=X | 2011-2015 | 2003-01-02 |               0.779 |               0.201 |              -0.031 |             0.832 |                      25 |
| 2706 | USDJPY=X | 2016-2026 | 2003-01-02 |               0.796 |               0.2   |               0.008 |             0.837 |                      63 |
| 1576 | USDCHF=X | 2003-2009 | 2003-09-17 |              -0.048 |               0.754 |               0.13  |             0.944 |                      11 |
| 1249 | USDCHF=X | 2011-2015 | 2003-09-17 |               0.838 |               0.234 |              -0.06  |             0.846 |                      33 |
| 2706 | USDCHF=X | 2016-2026 | 2003-09-17 |               0.784 |               0.238 |               0.013 |             0.843 |                      11 |
|  909 | AUDUSD=X | 2003-2009 | 2006-05-16 |              -0.165 |               0.788 |               0.142 |             0.954 |                      25 |
| 1251 | AUDUSD=X | 2011-2015 | 2006-05-16 |               0.755 |               0.196 |              -0.01  |             0.83  |                      50 |
| 2706 | AUDUSD=X | 2016-2026 | 2006-05-16 |               0.777 |               0.179 |               0.028 |             0.829 |                      65 |
| 1576 | USDCAD=X | 2003-2009 | 2003-09-17 |              -0.028 |               0.799 |               0.225 |             0.963 |                      12 |
| 1251 | USDCAD=X | 2011-2015 | 2003-09-17 |               0.766 |               0.182 |               0.034 |             0.837 |                       6 |
| 2706 | USDCAD=X | 2016-2026 | 2003-09-17 |               0.734 |               0.269 |              -0.018 |             0.841 |                       7 |
| 1514 | NZDUSD=X | 2003-2009 | 2003-12-01 |              -0.017 |               0.778 |               0.264 |             0.958 |                      29 |
| 1252 | NZDUSD=X | 2011-2015 | 2003-12-01 |               0.679 |               0.253 |              -0.005 |             0.841 |                      43 |
| 2706 | NZDUSD=X | 2016-2026 | 2003-12-01 |               0.754 |               0.205 |              -0.008 |             0.834 |                      52 |
| 1594 | USDSEK=X | 2003-2009 | 2003-01-02 |              -0.059 |               0.83  |               0.165 |             0.961 |                      17 |
| 1252 | USDSEK=X | 2011-2015 | 2003-01-02 |               0.792 |               0.118 |              -0.04  |             0.792 |                      63 |
| 2706 | USDSEK=X | 2016-2026 | 2003-01-02 |               0.787 |               0.189 |               0.019 |             0.834 |                      61 |
| 1594 | USDNOK=X | 2003-2009 | 2003-01-02 |              -0.067 |               0.821 |               0.173 |             0.961 |                      13 |
| 1252 | USDNOK=X | 2011-2015 | 2003-01-02 |               0.813 |               0.159 |              -0.037 |             0.816 |                      61 |
| 2706 | USDNOK=X | 2016-2026 | 2003-01-02 |               0.495 |               0.006 |               0.033 |             0.638 |                     101 |

| era       | series   |   corr_5d_returns_vs_h10_synthetic |   corr_1d_same_day |   corr_1d_h10_prev_day |
|:----------|:---------|-----------------------------------:|-------------------:|-----------------------:|
| 2003-2009 | EURGBP=X |                              0.971 |              0.859 |                  0.065 |
| 2011-2015 | EURGBP=X |                              0.811 |              0.146 |                  0.828 |
| 2016-2026 | EURGBP=X |                              0.83  |              0.155 |                  0.823 |
| 2003-2009 | EURJPY=X |                              0.958 |              0.817 |                 -0.055 |
| 2011-2015 | EURJPY=X |                              0.838 |              0.176 |                  0.796 |
| 2016-2026 | EURJPY=X |                              0.815 |              0.146 |                  0.824 |
| 2003-2009 | EURCHF=X |                              0.889 |              0.609 |                 -0.048 |
| 2011-2015 | EURCHF=X |                              0.835 |              0.263 |                  0.856 |
| 2016-2026 | EURCHF=X |                              0.821 |              0.158 |                  0.81  |
| 2003-2009 | DX-Y.NYB |                              0.973 |              0.873 |                 -0.02  |
| 2011-2015 | DX-Y.NYB |                              0.973 |              0.863 |                 -0.019 |
| 2016-2026 | DX-Y.NYB |                              0.974 |              0.869 |                  0.013 |

Quality: the eight pairs agree with H10 on 5-day returns at 0.94-0.97 before 2010 (USDJPY=X 0.87) and 0.79-0.85 after
(the lower figure is the larger timing offset to noon, not noise), except **USDNOK=X after 2016 (0.64, 101 five-day
gaps above 200 bp): bad**. AUDUSD=X only starts in 2006-05. The EUR crosses equal the H10 triangular values
(EURUSD/GBPUSD etc.) to the same degree, so they carry no information beyond the dollar pairs. DX-Y.NYB is stamped on
the New York date and matches the H10 synthetic DXY at 0.97 in every era (its close is a few hours after noon of the
same day), but it is 58 % EUR, so it cannot serve as the "rest of the market".
Side note for the feature store: `_cross_daily` normalises stamps in UTC. Yahoo `=X` bars are stamped 23:00 UTC in
summer, so if these files are ever fed through `_cross_daily` + `_align_lagged(.., 1)` the pre-2010 summer rows would
see a price 2-3 hours after the session close. Today the store builds `usd_*` from H10 with a one-day lag, which is
honest (and 24 hours more conservative than necessary).

**(c) Synchronicity.** A Yahoo close is 21-22 hours older than our close (after 2010), H10 is 5 hours older. H10 it is.

**Session alignment.** A feature-store row closes at 17:00 New York on NY date D and takes the last H10 date <= D
(96.5 % of sessions: the same date; the rest are US holidays, where the previous fixing is used). Label-free check of
the alignment: the noon-to-noon EUR/USD return aligned this way correlates 0.81 with the session's own `ret_1d`
(19 of 24 hours overlap) and -0.014 with `fwd_1d`.

**Look-ahead probes** (required: show that mistimed cross data gives an impossible Sharpe).
1. H10 one fixing ahead (noon of the next H10 date, 19 hours inside the label), all 12 candidates, net at 1.2 pips:

| variant     |   sr_2010_2026 |   sr_2016_2026 |   sr_2023_2026 |   t_2010_2026 |
|:------------|---------------:|---------------:|---------------:|--------------:|
| res_rev5    |          -2.64 |          -2.21 |          -2.39 |        -11.01 |
| res_rev20   |          -1.28 |          -1.17 |          -1.73 |         -5.35 |
| res_coint   |          -1.01 |          -1.14 |          -1.32 |         -4.2  |
| usd_trend20 |           2.23 |           2.15 |           1.99 |          9.31 |
| lead_usd1   |           8.58 |           8.67 |           8.57 |         35.73 |
| lead_comm1  |           5.47 |           5.9  |           6.57 |         22.78 |
| lead_risk1  |           1.43 |           0.97 |           0.46 |          5.97 |
| lead_eurx1  |           5.42 |           3.88 |           2.42 |         22.58 |
| disp_cond5  |          -0.65 |          -0.7  |          -0.18 |         -2.7  |
| pca_rev5    |          -2.21 |          -1.23 |          -1.15 |         -9.22 |
| pair_coint  |          -0.85 |          -0.82 |          -0.74 |         -3.53 |
| combo_tstat |           8.69 |           8.51 |           8.06 |         36.18 |

   `lead_usd1` 8.6, `combo_tstat` 8.7, `lead_eurx1` 5.4: impossible, as they should be. (The reversal signals turn
   strongly NEGATIVE because they bet against a residual move that is now inside the label.)
2. Yahoo, 2011-2026 (constant stamp convention), signal = 1-day return of the equal-weight basket of 7 Yahoo dollar
   pairs (USDNOK=X dropped), same sign-mapped walk-forward:

| alignment                               |   cost_pips |   sr_2011_2026 |   sr_2016_2026 |   sr_2023_2026 |   corr_signal_fwd_1d |
|:----------------------------------------|------------:|---------------:|---------------:|---------------:|---------------------:|
| honest_last_bar_le_D                    |         1.2 |          0.034 |         -0.146 |         -0.598 |                0.012 |
| honest_last_bar_le_D                    |         0   |          0.365 |          0.235 |         -0.203 |                0.012 |
| LOOKAHEAD_plus_1_bar_(2-3h_after_close) |         1.2 |         -0.289 |         -0.058 |         -0.301 |                0.018 |
| LOOKAHEAD_plus_1_bar_(2-3h_after_close) |         0   |          0.053 |          0.332 |          0.1   |                0.018 |
| LOOKAHEAD_plus_2_bars                   |         1.2 |          7.323 |          8.161 |          8.775 |                0.759 |
| LOOKAHEAD_plus_2_bars                   |         0   |          7.506 |          8.394 |          9.049 |                0.759 |

   One full bar ahead gives Sharpe 7-9 (signal/label correlation 0.76). The bar stamped D+1, which is the price only
   2-3 hours after our close and is what a naive same-date join delivers under the pre-2010 convention, does NOT
   inflate the result (correlation 0.018 vs 0.012 honest): the two quiet hours after 17:00 New York carry almost no
   information. It is still formally a look-ahead and is not used anywhere.

## 2. Decomposition method

All returns are noon-to-noon log returns in bp on the H10 date grid, quoted as USD per unit of the currency (so "+"
means the currency rose against the dollar, the sign of EUR/USD up).
* Regression basket: rolling OLS of the EUR return on the eight other returns with intercept over the PREVIOUS 250 H10
  days (t-250..t-1); basket (dollar) component d_t = beta' r_t, residual e_t = r_EUR,t - d_t.
* PCA: for each test year Y the PCs of the eight non-EUR returns (standardised) are fitted on dates before Y-01-01,
  EUR is regressed on PC1 (dollar) and PC2 (risk/carry) on the same window, the frozen loadings give the residual of
  year Y. Dates before 2010 use the 2003-2009 fit (all training data).
* Robustness rule, added after looking at the raw return panel and before any strategy result: every daily return
  series is winsorised at +-6 of its own previous-250-day sd (35 currency-days in 23 years), the residual likewise,
  and the pair z-scores are clipped at +-4. Without it the SNB break of 2015-01-15 produces a -1276 bp "residual"
  (CHF had a 0.8 beta during the floor) that dominates every scale and the betas of the following 250 days.

Out-of-sample decomposition statistics:

|:----------------------|:----------|:----------|:----------|:----------|
| period                | 2004-2009 | 2010-2015 | 2016-2022 | 2023-2026 |
| sd_eur_bp             | 66.164    | 61.422    | 46.499    | 43.414    |
| sd_basket_bp          | 65.257    | 52.942    | 43.095    | 39.79     |
| sd_resid_bp           | 19.456    | 28.293    | 21.877    | 19.858    |
| r2_regression_oos     | 0.914     | 0.788     | 0.779     | 0.791     |
| r2_pca_oos            | 0.871     | 0.686     | 0.67      | 0.705     |
| resid_autocorr_1      | 0.088     | 0.068     | -0.048    | -0.068    |
| resid_autocorr_5d_sum | 0.097     | -0.097    | -0.005    | -0.013    |
| basket_autocorr_1     | -0.053    | -0.026    | 0.076     | -0.011    |
| beta_gbp              | 0.063     | 0.113     | 0.095     | 0.285     |
| beta_jpy              | -0.019    | 0.007     | 0.015     | 0.018     |
| beta_chf              | 0.484     | 0.432     | 0.459     | 0.301     |
| beta_aud              | 0.048     | -0.009    | 0.017     | 0.031     |
| beta_cad              | 0.015     | -0.014    | -0.044    | 0.029     |
| beta_nzd              | 0.019     | 0.014     | 0.02      | -0.042    |
| beta_sek              | 0.23      | 0.257     | 0.259     | 0.222     |
| beta_nok              | 0.064     | 0.109     | 0.095     | 0.015     |

The other eight dollar pairs explain 78-91 % of EUR/USD's daily variance out of sample (PCA with two factors 67-87 %).
The basket is mostly CHF (0.30-0.48), SEK (0.22-0.26), GBP (0.06-0.29) and NOK: EUR/USD is priced off the European
block, the commodity currencies and JPY have ~0 beta once those are in. The residual has a daily sd of ~20 bp and a
lag-1 autocorrelation of +0.07..+0.09 before 2016 and -0.05..-0.07 after: there is no stable sign to trade.

## 3. Candidates, priors and selection rule (all declared in the module docstring before any result)

| # | candidate | prior-oriented definition ("+" = long EUR/USD next session) | hypothesis |
|--:|:--|:--|:--|
| 1 | `res_rev5` | -(5-day sum of e) | (1) residual reverts over days |
| 2 | `res_rev20` | -(20-day sum of e) | (1) residual reverts over weeks |
| 3 | `res_coint` | -z250 of the cumulated residual | (1) cointegration spread |
| 4 | `usd_trend20` | +(20-day sum of d) | (2) the dollar component trends |
| 5 | `lead_usd1` | +d_t (1-day basket component) | (3) other dollar pairs lead |
| 6 | `lead_comm1` | +mean 1-day return of AUD, CAD, NZD | (3) commodity currencies lead |
| 7 | `lead_risk1` | -(1-day JPY return - commodity-FX return) | (3) risk-off leads EUR/USD lower |
| 8 | `lead_eurx1` | +(1-day EUR return - mean of GBP, JPY, CHF) = EURGBP/EURJPY/EURCHF average | (3) the EUR-cross factor leads |
| 9 | `disp_cond5` | 5-day EUR/USD return x sign(trailing-500-day median dispersion - dispersion of the nine 5-day returns) | (4) follow when pairs agree, fade when they disagree |
| 10 | `pca_rev5` | -(5-day sum of the PCA residual) | (5) loading-adjusted residual reverts |
| 11 | `pair_coint` | -mean z250 of log EURCHF and log EURGBP | (1) pairs trade vs the nearest European pairs |
| 12 | `combo_tstat` | house t-stat-weighted combination of 1-11 (`weak_signals._weights("tstat")`) | all |

House mapping for every candidate: z = signal / training sd; pos = sign(z) when |z| > training median |z|, else 0;
times min(1, median_train(rv_21d_bp)/rv_21d_bp); one decision per session, label `fwd_1d`, 1.2 pips per unit turnover,
yearly expanding walk-forward (`eurusd.wf`), test years 2010-2026.
**Selection rule:** the candidate with the highest 2010-2015 walk-forward net Sharpe at 1.2 pips.
**Variant count: 12 candidates.** Additional looks that were not eligible for selection: 12 five-day-hold diagnostics
(the same positions held 5 sessions), the noon-to-noon IC table, 1 cost-sensitivity run, the leak-check re-runs and 3
Yahoo probe alignments. Deflate with 12, or with 24 to be strict.

## 4. Single signals and the combination (net, 1.2 pips, 252 periods per year)

| candidate   |   SR 10-15 (selection) |   SR 10-26 |   t 10-26 |   SR 16-26 |   t 16-26 |   SR 23-26 |   t 23-26 |   gross SR 10-26 |   turnover/day |   active |   hit sign 10-26 |   hit sign 16-26 |   hit sign 23-26 |   hit net 10-26 |
|:------------|-----------------------:|-----------:|----------:|-----------:|----------:|-----------:|----------:|-----------------:|---------------:|---------:|-----------------:|-----------------:|-----------------:|----------------:|
| res_rev5    |                  -1    |      -0.46 |     -1.9  |      -0.05 |     -0.18 |      -0.38 |     -0.76 |            -0.32 |           0.31 |     0.53 |            0.492 |            0.498 |            0.506 |           0.488 |
| res_rev20   |                  -0.25 |      -0.18 |     -0.75 |      -0.14 |     -0.46 |      -0.42 |     -0.84 |            -0.11 |           0.15 |     0.56 |            0.502 |            0.502 |            0.478 |           0.501 |
| res_coint   |                  -0.57 |      -0.42 |     -1.75 |      -0.32 |     -1.05 |      -0.07 |     -0.14 |            -0.39 |           0.06 |     0.45 |            0.481 |            0.484 |            0.466 |           0.481 |
| usd_trend20 |                   0.03 |      -0.12 |     -0.5  |      -0.22 |     -0.75 |      -0.23 |     -0.46 |            -0.05 |           0.13 |     0.41 |            0.489 |            0.483 |            0.476 |           0.487 |
| lead_usd1   |                  -0.25 |      -0.26 |     -1.08 |      -0.27 |     -0.92 |      -0.44 |     -0.88 |             0.04 |           0.58 |     0.43 |            0.484 |            0.49  |            0.47  |           0.473 |
| lead_comm1  |                  -0.65 |      -0.53 |     -2.21 |      -0.45 |     -1.5  |      -1.08 |     -2.15 |            -0.22 |           0.62 |     0.45 |            0.488 |            0.502 |            0.475 |           0.478 |
| lead_risk1  |                  -0.36 |      -0.14 |     -0.59 |       0.02 |      0.06 |      -0.17 |     -0.33 |             0.15 |           0.6  |     0.46 |            0.512 |            0.522 |            0.518 |           0.502 |
| lead_eurx1  |                   0.08 |      -0.23 |     -0.98 |      -0.48 |     -1.61 |      -0.32 |     -0.64 |             0.07 |           0.63 |     0.47 |            0.491 |            0.492 |            0.493 |           0.485 |
| disp_cond5  |                  -0.24 |      -0.14 |     -0.57 |      -0.06 |     -0.2  |      -0.32 |     -0.63 |             0.05 |           0.37 |     0.42 |            0.509 |            0.503 |            0.5   |           0.505 |
| pca_rev5    |                  -0.49 |      -0.28 |     -1.19 |      -0.13 |     -0.44 |      -0.35 |     -0.69 |            -0.14 |           0.3  |     0.53 |            0.497 |            0.499 |            0.523 |           0.494 |
| pair_coint  |                  -0.46 |      -0.46 |     -1.9  |      -0.48 |     -1.59 |      -0.4  |     -0.8  |            -0.43 |           0.06 |     0.53 |            0.482 |            0.485 |            0.47  |           0.481 |
| combo_tstat |                  -0    |      -0.2  |     -0.82 |      -0.35 |     -1.18 |      -0.09 |     -0.17 |             0.1  |           0.62 |     0.47 |            0.492 |            0.496 |            0.499 |           0.484 |

Hit rate = share of active decisions with the correct sign before costs ("hit sign") or with positive net P&L ("hit
net"). Base rate of an up day 2010-2026: 49.9 %.

* Not one candidate has a positive net Sharpe over 2010-2026 or 2023-2026, and only `lead_risk1` reaches +0.02 over
  2016-2026. Gross of costs the best is `lead_risk1` +0.15 (t 0.6); 7 of 12 are negative gross.
* (1) **The residual does not revert.** `res_rev5` -0.46 (t -1.9, gross -0.32), `res_coint` -0.42 (t -1.8),
  `pair_coint` -0.46 (t -1.9), `pca_rev5` -0.28, `res_rev20` -0.18. If anything EUR-specific strength persisted
  (2010-2015: `res_rev5` -1.00, the euro-crisis years; 2016-2022: +0.12; 2023-2026: -0.38), i.e. no stable sign.
* (2) **The dollar component does not trend**: `usd_trend20` -0.12 (gross -0.05), in line with `usdmom` in
  `arm_weak_signals.md`. Decomposing and trading the parts with opposite signs is two zeros.
* (3) **No lead-lag at the daily horizon.** `lead_usd1` gross +0.04, `lead_eurx1` gross +0.07, `lead_risk1` gross
  +0.15; a 1-day signal turns over 0.6 units a day, which costs ~0.3 Sharpe, so all are negative net.
  `lead_comm1` is the largest |t| of the arm, -2.2, with the WRONG sign (and -1.08 in 2023-2026).
* (4) Dispersion conditioning: -0.14 (gross +0.05). (5) PCA residual: see (1).
* **Combination** (`combo_tstat`): -0.20 / -0.35 / -0.09. Eight to ten of the eleven signals have a negative training t-stat
  against their prior in every year, so the weights collapse onto `lead_eurx1` (0.6-1.0), with `usd_trend20`
  in 2011-2013 and `lead_risk1` (0.27-0.40) from 2021; the combination is `lead_eurx1` with noise (P&L corr 0.93).

Walk-forward weights of the combination:

|   test_year |   res_rev5 |   res_rev20 |   res_coint |   usd_trend20 |   lead_usd1 |   lead_comm1 |   lead_risk1 |   lead_eurx1 |   disp_cond5 |   pca_rev5 |   pair_coint |
|------------:|-----------:|------------:|------------:|--------------:|------------:|-------------:|-------------:|-------------:|-------------:|-----------:|-------------:|
|        2010 |          0 |        0    |       0.058 |         0     |           0 |            0 |        0.14  |        0.802 |            0 |          0 |            0 |
|        2011 |          0 |        0    |       0     |         0.244 |           0 |            0 |        0     |        0.756 |            0 |          0 |            0 |
|        2012 |          0 |        0    |       0     |         0.119 |           0 |            0 |        0     |        0.881 |            0 |          0 |            0 |
|        2013 |          0 |        0    |       0     |         0.116 |           0 |            0 |        0     |        0.884 |            0 |          0 |            0 |
|        2014 |          0 |        0    |       0     |         0     |           0 |            0 |        0     |        1     |            0 |          0 |            0 |
|        2015 |          0 |        0    |       0     |         0.011 |           0 |            0 |        0     |        0.989 |            0 |          0 |            0 |
|        2016 |          0 |        0    |       0     |         0     |           0 |            0 |        0     |        1     |            0 |          0 |            0 |
|        2017 |          0 |        0    |       0     |         0     |           0 |            0 |        0     |        1     |            0 |          0 |            0 |
|        2018 |          0 |        0    |       0     |         0     |           0 |            0 |        0     |        1     |            0 |          0 |            0 |
|        2019 |          0 |        0    |       0     |         0     |           0 |            0 |        0     |        1     |            0 |          0 |            0 |
|        2020 |          0 |        0    |       0     |         0     |           0 |            0 |        0     |        1     |            0 |          0 |            0 |
|        2021 |          0 |        0    |       0     |         0     |           0 |            0 |        0.265 |        0.735 |            0 |          0 |            0 |
|        2022 |          0 |        0    |       0     |         0     |           0 |            0 |        0.277 |        0.723 |            0 |          0 |            0 |
|        2023 |          0 |        0.02 |       0     |         0     |           0 |            0 |        0.318 |        0.662 |            0 |          0 |            0 |
|        2024 |          0 |        0    |       0     |         0     |           0 |            0 |        0.345 |        0.655 |            0 |          0 |            0 |
|        2025 |          0 |        0    |       0     |         0     |           0 |            0 |        0.357 |        0.643 |            0 |          0 |            0 |
|        2026 |          0 |        0    |       0     |         0     |           0 |            0 |        0.402 |        0.598 |            0 |          0 |            0 |

### 5-session horizon (diagnostic, not eligible for selection)

IC = out-of-sample (2010-2026) correlation of the raw signal with the label; hold-5 = each day's position held for five
sessions (mean of the last five daily positions, P&L on `fwd_1d`, cost on the net turnover).

| signal      |   IC fwd_1d |      t |   IC fwd_5d |   NW t (4 lags) |   hold-5 net SR 10-26 |   hold-5 net SR 16-26 |   hold-5 net SR 23-26 |   hold-5 gross SR 10-26 |
|:------------|------------:|-------:|------------:|----------------:|----------------------:|----------------------:|----------------------:|------------------------:|
| res_rev5    |      -0.016 |  -0.8  |      -0.015 |           -0.5  |                 -0.36 |                 -0.35 |                 -1.03 |                   -0.28 |
| res_rev20   |       0.007 |   0.4  |       0.012 |            0.37 |                 -0.2  |                 -0.22 |                 -0.4  |                   -0.17 |
| res_coint   |      -0.022 |  -1.5  |      -0.05  |           -1.84 |                 -0.45 |                 -0.45 |                 -0.28 |                   -0.44 |
| usd_trend20 |      -0.004 |  -0.19 |      -0.002 |           -0.06 |                 -0.17 |                 -0.32 |                 -0.33 |                   -0.14 |
| lead_usd1   |       0.003 |   0.15 |      -0.017 |           -0.98 |                 -0.24 |                 -0.37 |                 -0.71 |                   -0.1  |
| lead_comm1  |       0.003 |   0.16 |      -0.003 |           -0.17 |                 -0.32 |                 -0.38 |                 -1.18 |                   -0.18 |
| lead_risk1  |       0.006 |   0.35 |       0.005 |            0.27 |                 -0.14 |                 -0.29 |                 -1.12 |                   -0    |
| lead_eurx1  |       0.016 |   0.93 |       0.012 |            0.61 |                 -0.09 |                 -0.25 |                  0.11 |                    0.04 |
| disp_cond5  |       0.006 |   0.31 |       0.005 |            0.2  |                 -0.27 |                 -0.15 |                 -0.49 |                   -0.17 |
| pca_rev5    |      -0.008 |  -0.44 |      -0.019 |           -0.62 |                 -0.17 |                 -0.17 |                 -0.49 |                   -0.09 |
| pair_coint  |      -0.026 |  -1.65 |      -0.061 |           -2.09 |                 -0.53 |                 -0.68 |                 -0.61 |                   -0.52 |
| combo_tstat |     nan     | nan    |     nan     |          nan    |                 -0.25 |                 -0.35 |                 -0.32 |                   -0.12 |

Nothing at 5 days either. The only |t| near 2 are `pair_coint` (NW t -2.1) and `res_coint` (-1.8) with the wrong sign:
when EUR is rich against CHF and GBP on a 250-day view it kept getting richer. All hold-5 Sharpes are negative or ~0.

### Zero-staleness diagnostic (not a candidate)

Is the 5-hour gap between the fixing and our close what kills it? Each signal known at noon of H10 date g against
EUR/USD from noon g to noon g+1 and g+5, measured on our own 12:00 bar (an independent sample of the same instant, so
fixing noise cannot create a mechanical reversal):

| period    | signal      |   ic_noon_1d |   t_noon_1d |   ic_noon_5d |   nw_t_noon_5d |    n |
|:----------|:------------|-------------:|------------:|-------------:|---------------:|-----:|
| 2010-2026 | res_rev5    |       -0.024 |      -1.237 |       -0.014 |         -0.479 | 4124 |
| 2010-2026 | res_rev20   |        0.008 |       0.444 |        0.021 |          0.654 | 4124 |
| 2010-2026 | res_coint   |       -0.02  |      -1.297 |       -0.046 |         -1.646 | 4124 |
| 2010-2026 | usd_trend20 |       -0.004 |      -0.208 |       -0.005 |         -0.165 | 4124 |
| 2010-2026 | lead_usd1   |        0.007 |       0.374 |       -0.024 |         -1.409 | 4124 |
| 2010-2026 | lead_comm1  |        0.003 |       0.15  |       -0.018 |         -0.985 | 4124 |
| 2010-2026 | lead_risk1  |       -0     |      -0.017 |       -0.003 |         -0.175 | 4124 |
| 2010-2026 | lead_eurx1  |        0.02  |       1.105 |        0.01  |          0.528 | 4124 |
| 2010-2026 | disp_cond5  |        0.018 |       1.021 |        0.015 |          0.598 | 4124 |
| 2010-2026 | pca_rev5    |       -0.017 |      -0.909 |       -0.02  |         -0.66  | 4124 |
| 2010-2026 | pair_coint  |       -0.026 |      -1.626 |       -0.06  |         -2.012 | 4124 |
| 2016-2026 | res_rev5    |        0.005 |       0.223 |       -0.029 |         -0.849 | 2622 |
| 2016-2026 | res_rev20   |        0.016 |       0.698 |       -0     |         -0.002 | 2622 |
| 2016-2026 | res_coint   |       -0.008 |      -0.441 |       -0.035 |         -1.056 | 2622 |
| 2016-2026 | usd_trend20 |       -0.015 |      -0.695 |       -0.046 |         -1.274 | 2622 |
| 2016-2026 | lead_usd1   |        0.031 |       1.308 |       -0.011 |         -0.497 | 2622 |
| 2016-2026 | lead_comm1  |        0.046 |       1.966 |       -0.004 |         -0.18  | 2622 |
| 2016-2026 | lead_risk1  |        0.046 |       1.926 |        0.006 |          0.268 | 2622 |
| 2016-2026 | lead_eurx1  |        0.006 |       0.25  |        0.006 |          0.262 | 2622 |
| 2016-2026 | disp_cond5  |        0.006 |       0.237 |        0.035 |          1.066 | 2622 |
| 2016-2026 | pca_rev5    |        0.004 |       0.179 |       -0.02  |         -0.524 | 2622 |
| 2016-2026 | pair_coint  |       -0.036 |      -1.791 |       -0.089 |         -2.577 | 2622 |

No: with no staleness at all the 1-day ICs over 2010-2026 are within +-0.026 (|t| <= 1.6). Over 2016-2026 `lead_comm1`
and `lead_risk1` reach IC 0.046 (t 1.9-2.0) with the prior sign, 2 of 22 statistics at |t| ~ 2, and at our close they
deliver gross Sharpe -0.08 and +0.37, net -0.45 and +0.02. `pair_coint` at 5 days is again the wrong sign (-2.0 / -2.6).

## 5. Final variant: `lead_eurx1` (by the rule: best 2010-2015 net Sharpe, +0.08)

| period    |    n |   sharpe |     t |   mean_bp |   sum_bp |   active_frac |   sharpe_0.6pip |   t_0.6pip |   sum_bp_0.6pip |
|:----------|-----:|---------:|------:|----------:|---------:|--------------:|----------------:|-----------:|----------------:|
| 2010      |  260 |     1.88 |  1.91 |      5.98 |  1555.95 |          0.69 |            1.98 |       2.01 |         1636.96 |
| 2011      |  260 |     0.1  |  0.1  |      0.31 |    81.09 |          0.65 |            0.19 |       0.2  |          152.7  |
| 2012      |  260 |    -0.88 | -0.9  |     -2.13 |  -553.11 |          0.52 |           -0.75 |      -0.76 |         -468.61 |
| 2013      |  259 |    -1.72 | -1.74 |     -3.64 |  -942.24 |          0.52 |           -1.56 |      -1.58 |         -854.16 |
| 2014      |  258 |    -0.5  | -0.51 |     -0.62 |  -159.04 |          0.28 |           -0.34 |      -0.34 |         -106.89 |
| 2015      |  259 |     0.44 |  0.45 |      1.26 |   325.7  |          0.64 |            0.58 |       0.58 |          421.95 |
| 2016      |  259 |    -0.95 | -0.96 |     -2.09 |  -540.47 |          0.48 |           -0.78 |      -0.79 |         -443.15 |
| 2017      |  259 |    -0.31 | -0.32 |     -0.65 |  -169.51 |          0.53 |           -0.13 |      -0.13 |          -71.79 |
| 2018      |  260 |    -0.1  | -0.11 |     -0.19 |   -49.44 |          0.45 |            0.07 |       0.07 |           32.9  |
| 2019      |  260 |    -1.73 | -1.76 |     -2.11 |  -549.83 |          0.38 |           -1.47 |      -1.49 |         -467.42 |
| 2020      |  260 |     0.29 |  0.3  |      0.55 |   142.39 |          0.48 |            0.48 |       0.48 |          231.1  |
| 2021      |  259 |    -1.36 | -1.38 |     -1.78 |  -461.32 |          0.27 |           -1.19 |      -1.21 |         -404.2  |
| 2022      |  260 |    -0.49 | -0.5  |     -1.18 |  -307.96 |          0.62 |           -0.33 |      -0.34 |         -207.42 |
| 2023      |  258 |    -2.57 | -2.6  |     -4.98 | -1284.4  |          0.45 |           -2.38 |      -2.41 |        -1187.57 |
| 2024      |  261 |     0.62 |  0.63 |      0.95 |   248.24 |          0.45 |            0.87 |       0.89 |          349.15 |
| 2025      |  260 |     1.5  |  1.52 |      2.89 |   751.22 |          0.35 |            1.64 |       1.67 |          825.7  |
| 2026      |  220 |    -1.03 | -0.96 |     -1.16 |  -255.58 |          0.24 |           -0.84 |      -0.79 |         -208.81 |
| 2010-2026 | 4372 |    -0.23 | -0.98 |     -0.5  | -2168.31 |          0.47 |           -0.08 |      -0.35 |         -769.55 |
| 2016-2026 | 2816 |    -0.48 | -1.61 |     -0.88 | -2476.65 |          0.43 |           -0.3  |      -1.01 |        -1551.5  |
| 2023-2026 |  999 |    -0.32 | -0.64 |     -0.54 |  -540.52 |          0.38 |           -0.13 |      -0.26 |         -221.53 |
| 2010-2015 | 1556 |     0.08 |  0.19 |      0.2  |   308.34 |          0.55 |            0.2  |       0.49 |          781.95 |
| 2016-2022 | 1817 |    -0.56 | -1.52 |     -1.07 | -1936.13 |          0.46 |           -0.39 |      -1.04 |        -1329.97 |

2010-2026 net Sharpe -0.23 (t -0.98, deflated-Sharpe p 0.996 for 12 variants); 2016-2026 -0.48 (t -1.6);
2023-2026 -0.32 (t -0.6). At 0.6 pips: -0.08 / -0.30 / -0.13. Gross: +0.07 over 2010-2026.
**Fails the bar** (2016-2026 > 0.3 and 2023-2026 >= 0 required).

Hit rates of the final variant (active decisions only):

| period    |   n_decisions |   hit_net |   hit_sign_gross |   base_rate_up | variant    |
|:----------|--------------:|----------:|-----------------:|---------------:|:-----------|
| 2010-2026 |          2064 |    0.485  |           0.4913 |         0.4985 | lead_eurx1 |
| 2016-2026 |          1211 |    0.4855 |           0.4922 |         0.4973 | lead_eurx1 |
| 2023-2026 |           377 |    0.4828 |           0.4934 |         0.495  | lead_eurx1 |

48.3-48.6 % of decisions make money after costs and 49.1-49.3 % have the right sign before costs, against a 49.5-49.9 %
base rate of up days: no directional information.

## 6. Incremental test

`meta.combine([weak_signals, regime_trend, relative_value], "EW")` vs the two-way combination (`report_combo`):

| period    |   sr_2way |   t_2way |   sr_3way |   t_3way |   d_sr |   years_arm_in_3way |
|:----------|----------:|---------:|----------:|---------:|-------:|--------------------:|
| 2010-2026 |     0.563 |    2.347 |     0.46  |    1.914 | -0.104 |                   3 |
| 2013-2026 |     0.622 |    2.347 |     0.507 |    1.914 | -0.115 |                   3 |
| 2016-2026 |     0.636 |    2.128 |     0.596 |    1.992 | -0.041 |                   3 |
| 2023-2026 |     0.356 |    0.708 |     0.356 |    0.708 |  0     |                   3 |

Daily net P&L correlation of `relative_value` with the two live streams:

| Unnamed: 0     |   2010-2026 |   2016-2026 |
|:---------------|------------:|------------:|
| weak_signals   |       0.062 |       0.055 |
| regime_trend   |       0.072 |       0.053 |
| relative_value |       1     |       1     |

The stream is uncorrelated with the live combination (0.05-0.07) but has no return: the three-way combination is worse
over 2010-2026 (-0.10) and 2016-2026 (-0.04) and identical over 2023-2026 (the EW combiner only admits an arm with a
positive trailing t-stat, which this arm had only for 2013, 2014 and 2016; it has weight 0 from 2017 on). **Fails.**

## 7. Leak checks

Net Sharpe 2010-2026 at 1.2 pips for every candidate under each check:

| signal      |   baseline |   h10_lag_one_calendar_day |   features_shift_plus1_session |   LOOKAHEAD_next_h10_noon |   shuffled_labels |
|:------------|-----------:|---------------------------:|-------------------------------:|--------------------------:|------------------:|
| res_rev5    |      -0.46 |                      -0.3  |                          -0.3  |                     -2.64 |            nan    |
| res_rev20   |      -0.18 |                      -0.24 |                          -0.24 |                     -1.28 |            nan    |
| res_coint   |      -0.42 |                      -0.53 |                          -0.53 |                     -1.01 |            nan    |
| usd_trend20 |      -0.12 |                      -0.23 |                          -0.23 |                      2.23 |            nan    |
| lead_usd1   |      -0.26 |                      -0.04 |                          -0.03 |                      8.58 |            nan    |
| lead_comm1  |      -0.53 |                      -0.11 |                          -0.12 |                      5.47 |            nan    |
| lead_risk1  |      -0.14 |                      -0.23 |                          -0.23 |                      1.43 |            nan    |
| lead_eurx1  |      -0.23 |                      -0.37 |                          -0.37 |                      5.42 |             -0.12 |
| disp_cond5  |      -0.14 |                      -0.43 |                          -0.43 |                     -0.65 |            nan    |
| pca_rev5    |      -0.28 |                      -0.09 |                          -0.09 |                     -2.21 |            nan    |
| pair_coint  |      -0.46 |                      -0.51 |                          -0.51 |                     -0.85 |            nan    |
| combo_tstat |      -0.2  |                      -0.23 |                          -0.24 |                      8.69 |             -0.21 |

1. **Shuffled labels** (one global permutation of `fwd_1d`, used for fitting and evaluation), final variant and
   combination:

| variant     |   sr_2010_2026 |   sr_2016_2026 |   sr_2023_2026 |   t_2010_2026 |   gross_sr_2010_2026 |
|:------------|---------------:|---------------:|---------------:|--------------:|---------------------:|
| combo_tstat |          -0.21 |          -0.22 |           0.11 |         -0.89 |                -0.15 |
| lead_eurx1  |          -0.12 |           0.01 |           0.02 |         -0.52 |                 0.16 |

   ~0 (the negative net figures are the cost of the turnover; gross +0.16 and -0.15).
2. **Features one period late**: the H10 panel lagged one calendar day (the feature-store convention, noon of D-1) and,
   equivalently, all signals shifted one session. There is no edge to collapse: the final variant goes from -0.23 to
   -0.37, the combination from -0.20 to -0.23/-0.24; nothing becomes positive.
   **Look-ahead probe** (section 1): +5.4 for the final variant, +8.6/+8.7 for `lead_usd1` and the combination, so the
   harness exposes a mistimed series loudly, and the honest results are nowhere near it.
3. **Label in disguise**: full-sample correlation of each signal with `fwd_1d`:

| variant     |   corr_with_fwd_1d |
|:------------|-------------------:|
| res_rev5    |            -0.0324 |
| res_rev20   |            -0.0133 |
| res_coint   |            -0.0241 |
| usd_trend20 |            -0.0043 |
| lead_usd1   |            -0.0298 |
| lead_comm1  |            -0.0268 |
| lead_risk1  |            -0.0015 |
| lead_eurx1  |             0.0209 |
| disp_cond5  |            -0.0026 |
| pca_rev5    |            -0.0202 |
| pair_coint  |            -0.0384 |

   All within +-0.04. Every input is a noon fixing of date <= the session's closing date; rolling betas, z-scores, the
   dispersion median and the winsorisation bands use previous observations only; PCA loadings are frozen before each
   test year. The only label-touching quantities are the training-window sd / median / t-stats inside `walk_forward`.

## 8. What helped, what did not, what is suspicious

* New information that helped: none for direction. Useful by-products: (i) the Yahoo daily FX stamp convention and its
  2010 switch, (ii) H10 is a clean noon-New-York snapshot of the whole G10 cross-section that can be used the same day,
  (iii) EUR/USD is 78-91 % explained by CHF, SEK, GBP and NOK on the day, leaving a ~20 bp idiosyncratic residual.
* Why relative value does not help a single-pair trader: the residual is only ~20 % of EUR/USD's variance and its
  autocorrelation is within +-0.09 with a sign that flips between sub-periods; a stat-arb desk would trade the
  residual itself (EUR/USD against the hedged basket, 20 bp of risk a day), whereas this account can only trade the
  EUR/USD leg and would carry the full 45-60 bp dollar-factor noise for a 1-2 bp expected reversion.
* Suspicious / caveats. (a) The priors were mostly wrong-signed (all 11 single signals negative net, 7 negative
  gross). Flipping signs afterwards would be 11 new variants; the largest flipped |t| is 2.2 (`lead_comm1`) and 1.9
  (`res_rev5`, `pair_coint`), which is what the best of 12 zero-skill trials looks like, and the flipped residual
  signal is EUR-specific momentum that worked in 2010-2015 only. Not pursued. (b) The signals are 5 hours stale at the
  close; the noon-to-noon diagnostic says this is not the reason. A 17:00-synchronous panel exists only from 2024
  (Yahoo hourly bars for four pairs), too short to test. (c) H10 is a single fixing; the 4-decimal rounding is
  ~0.5 bp, negligible against a 20 bp residual. (d) Live use would need a noon-New-York snapshot of eight dollar pairs,
  which the project does not collect; moot given the result.
