# Arm I - macro_nowcast: accumulated macro picture (surprise index, data momentum, Taylor rule), round 3

Code: `src/eurusd/arms/macro_nowcast.py` (`run(cost_pips=1.2)`; `python src/eurusd/arms/macro_nowcast.py 1.2` also writes the
leak checks, the bias/timing split and the incremental test; 55 s). Outputs in `experiments/results/arms/`:
`macro_nowcast_positions.parquet` (final variant, OOS: `pos`, `fwd_bp`, `net_bp`), `macro_nowcast_report.csv` (12 candidates at 1.2 pips
+ the same positions at 0.6 pips; `variant`, `kind`, `cost_pips`, `final`), `macro_nowcast_all_positions.parquet`, `macro_nowcast_weights.csv`,
`macro_nowcast_leakchecks.csv`, `macro_nowcast_bias_timing.csv`, `macro_nowcast_incremental.csv`, `macro_nowcast_correlations.csv`,
log `logs/macro_nowcast.log`. New data file: `data/macro/surprise_index.csv`.

## Verdict in one paragraph
The final variant picked by the pre-declared rule is the **EUR-minus-USD economic surprise index with a 60-day half-life**
(`single_esi60`): net Sharpe at 1.2 pips **0.59 (t 2.47) for 2010-2026, 0.41 (t 1.36) for 2016-2026, 0.11 (t 0.22) for 2023-2026**.
It **formally passes** the round-3 bar (standalone 2016-2026 > 0.3, 2023-2026 not negative, three-way EW 0.694 vs two-way 0.636 on
2016-2026) and it is nearly uncorrelated with the live streams (daily P&L correlation 0.18 with weak_signals, 0.07 with positioning).
**I do not regard this as established predictability and recommend NOT adding it to the live combination yet**: the deflated-Sharpe
p is 0.20 for 12 variants, the 2016-2026 record alone has p = 0.13 against a circular-shift null, the result does not collapse when
the signal is lagged by 3-12 months (so it cannot be attributed to timely information), the neighbouring half-lives 10 and 30 days are
at zero, the 2023-2026 number rests on 216 active sessions (the index is undefined from 2024-01-30 to 2026-05-10), and the
actual/forecast feed that would be needed live has ended (EUR rows 2026-09-02, USD rows 2026-10-02): the index is undefined today. Data momentum from published levels shows **no** predictability
except the slow Taylor-rule level (0.50 / 0.31 / -0.04, turnover 2.6 position units per year, fails 2023-2026); the t-stat combination of all
eleven signals fails (0.27 / 0.23 / -0.08).

## Idea
Round 2: single releases are absorbed in the release bar; only slow macro drift survives. The untested middle ground is the
*accumulated* macro picture: (1) a Citi-style surprise index per economy, EUR minus USD; (2) momentum of the published data levels,
US minus euro area, and a Taylor-rule differential (Molodtsova-Papell). One decision per NY-close session, label `fwd_1d`.

## New data: `data/macro/surprise_index.csv`
Source: built by this module from `data/macro/events.csv` (ForexFactory archive 2010-01..2023-12 `ff_archive_2010_2023`, partial
`ff_2025q4_snapshot`, `ff_2026_fxdesk_lowq` + `ff_2026_cwt` for 2026-01-02..2026-10-02). 4,373 rows, one per NY-close session
2010-01-04..2026-11-06, 95 columns: `esi_<USD|EUR|GBP|JPY>_<all|gro|inf>_hl<10|30|60>` (NaN where the validity rule fails),
`raw_*` (same without the validity mask, diagnostic only), `n_<ccy>_<cat>` (releases entering that session) and
`esi_EURmUSD_<cat>_hl<h>`. Publication lag: a release enters the first session whose close is at or after its release minute
(verified archive 2010-2023); the 2025/2026 mirrors have unreliable clock times, so their releases count from the END of their
stamped UTC date (one session late). The row at session T was checked to be unchanged when every release available after T is
deleted (truncation test below). GBP and JPY indices are saved as controls and are not traded.

### Construction
* Universe: every release of an event type that has been rated Medium/High **at or before that release** (causal; ForexFactory
  later downgraded many types to Low, a plain Medium/High filter would shrink the EUR universe from 439 releases in 2014 to 102 in
  2022), with numeric actual and forecast. Overlapping 2026 mirrors are de-duplicated (same type and date, or identical values
  within 3 days).
* surprise = SIGN x (actual - forecast); z = surprise / sd of the previous <= 60 surprises of the same type (at least 8, strictly
  earlier releases only), clipped at +-3. 20,058 usable releases (USD 7,569, EUR 6,640, GBP 3,882, JPY 1,967); pooled z: mean 0.00, sd 1.01.
* Index = exponentially decayed **mean** of the z's (half-life 10 / 30 / 60 calendar days), per currency and per category
  (all / growth / inflation). Medium and High releases have equal weight.
* **Hole 2024-01..2025-09 (and thin 2025-Q4, nothing after 2026-10-07): the index is undefined.** Rule (data driven, no dates
  hard-coded): c_t = 1 when at least 10 (all) / 8 (growth) / 3 (inflation) usable releases of the currency fall in the last 35 days
  and at least one in the last 10 days; the index is valid when the exponentially weighted mean of c_t (same half-life) is >= 0.75,
  i.e. after two half-lives of continuous coverage. Result: the EUR-USD index is valid 2010-09-27..2024-01-09 (half-life 10),
  2010-11-04..2024-01-17 (30), 2011-01-03..2024-01-29 (60), and again 2026-01-29..09-15 (10), 2026-03-10..09-23 (30),
  2026-05-11..09-30 (60); the EUR rows of the 2026 mirror end on 2026-09-02, the USD rows on 2026-10-02. **All surprise variants
  have position 0 from late January 2024 to 2026 (the final: 2024-01-30..2026-05-10 and again from October 2026) and their first
  out-of-sample year is 2012** (250 training rows are required; nothing exists before 2010).

### Event sign map (hand-made; number of usable releases in brackets)
**USD**
* growth, sign +1 (higher than forecast = stronger): ADP Non-Farm Employment Change (173); Advance GDP q/q (51); Building Permits (167); CB Consumer Confidence (165); CB Leading Index m/m (43); Capacity Utilization Rate (168); Chicago PMI (168); Core Durable Goods Orders m/m (167); Core Retail Sales m/m (166); Durable Goods Orders m/m (169); Empire State Manufacturing Index (167); Existing Home Sales (168); Factory Orders m/m (173); Final GDP q/q (51); Final Manufacturing PMI (38); Final Services PMI (17); Flash Manufacturing PMI (139); Flash Services PMI (46); Housing Starts (166); ISM Manufacturing PMI (173); ISM Services PMI (173); Industrial Production m/m (168); JOLTS Job Openings (137); NAHB Housing Market Index (125); New Home Sales (167); Non-Farm Employment Change (176); Pending Home Sales m/m (168); Personal Income m/m (164); Personal Spending m/m (168); Philly Fed Manufacturing Index (167); Prelim GDP q/q (50); Prelim Nonfarm Productivity q/q (51); Prelim UoM Consumer Sentiment (167); Retail Sales m/m (169); Revised Nonfarm Productivity q/q (51); Revised UoM Consumer Sentiment (168); Richmond Manufacturing Index (55); S&P/CS Composite-20 HPI y/y (168)
* growth, sign -1 (higher than forecast = WEAKER): Unemployment Claims (759); Unemployment Rate (176)
* inflation, sign +1: Advance GDP Price Index q/q (51); Average Hourly Earnings m/m (173); CPI m/m (169); CPI y/y (169); Core CPI m/m (167); Core CPI y/y (1); Core PCE Price Index m/m (168); Core PPI m/m (167); Employment Cost Index q/q (51); Final GDP Price Index q/q (0); ISM Manufacturing Prices (13); Import Prices m/m (169); PPI m/m (170); Prelim GDP Price Index q/q (48); Prelim Unit Labor Costs q/q (51)
* excluded (no growth/inflation reading or not numeric): Business Inventories m/m; Crude Oil Inventories; Current Account; Fed Chairman Nomination Vote; Federal Budget Balance; Federal Funds Rate; Final Wholesale Inventories m/m; Goods Trade Balance; TIC Long-Term Purchases; Trade Balance

**EUR**
* growth, sign +1 (higher than forecast = stronger): Belgian NBB Business Climate (168); Final Manufacturing PMI (150); Final Services PMI (147); Flash GDP q/q (51); Flash Manufacturing PMI (168); Flash Services PMI (168); French Consumer Spending m/m (164); French Flash GDP q/q (10); French Flash Manufacturing PMI (165); French Flash Services PMI (168); French Industrial Production m/m (168); French Prelim GDP q/q (47); French Prelim Private Payrolls q/q (51); German Factory Orders m/m (170); German Final Manufacturing PMI (128); German Final Services PMI (124); German Flash Manufacturing PMI (166); German Flash Services PMI (168); German GfK Consumer Climate (167); German Industrial Production m/m (168); German Prelim GDP q/q (50); German Retail Sales m/m (177); German ZEW Economic Sentiment (168); German ifo Business Climate (167); Industrial New Orders m/m (23); Industrial Production m/m (168); Italian Industrial Production m/m (138); Italian Manufacturing PMI (178); Italian Prelim GDP q/q (42); Italian Services PMI (149); Prelim Flash GDP q/q (26); Retail Sales m/m (170); Sentix Investor Confidence (150); Spanish Flash GDP q/q (51); Spanish Manufacturing PMI (143); Spanish Services PMI (140); ZEW Economic Sentiment (168)
* growth, sign -1 (higher than forecast = WEAKER): German Unemployment Change (178); Italian Monthly Unemployment Rate (135); Italian Quarterly Unemployment Rate (36); Spanish Unemployment Change (142); Spanish Unemployment Rate (51); Unemployment Rate (170)
* inflation, sign +1: CPI Flash Estimate y/y (177); Core CPI Flash Estimate y/y (118); Final CPI y/y (168); Final Core CPI y/y (168); German PPI m/m (168); German Prelim CPI m/m (172); Spanish Flash CPI y/y (133)
* excluded (no growth/inflation reading or not numeric): Current Account; German Trade Balance; Greek Gov Debt Crisis Vote; Irish Stability Treaty Vote; Long Term Refinancing Operation; M3 Money Supply y/y; Main Refinancing Rate; Private Loans y/y

**GBP** (control only, not traded)
* growth, sign +1 (higher than forecast = stronger): BRC Retail Sales Monitor y/y (67); CBI Industrial Order Expectations (168); CBI Realized Sales (168); Construction Output m/m (112); Construction PMI (175); Final GDP q/q (50); Final Manufacturing PMI (180); Final Services PMI (177); Flash Manufacturing PMI (50); Flash Services PMI (50); GDP m/m (59); GfK Consumer Confidence (170); Halifax HPI m/m (163); High Street Lending (113); Manufacturing Production m/m (168); Nationwide Consumer Confidence (22); Nationwide HPI m/m (172); Net Lending to Individuals m/m (174); ONS HPI y/y (51); Prelim Business Investment q/q (49); Prelim GDP q/q (49); Prelim Mortgage Approvals (8); RICS House Price Balance (168); Retail Sales m/m (162); Second Estimate GDP q/q (26)
* growth, sign -1 (higher than forecast = WEAKER): Claimant Count Change (164); Unemployment Rate (144)
* inflation, sign +1: Average Earnings Index 3m/y (161); CPI y/y (162); Core CPI y/y (168); PPI Input m/m (167); RPI y/y (165)
* excluded (no growth/inflation reading or not numeric): Asset Purchase Facility; Current Account; Goods Trade Balance; MPC Asset Purchase Facility Votes; MPC Official Bank Rate Votes; Official Bank Rate; Parliament Brexit Vote; Public Sector Net Borrowing; Scottish Independence Vote

**JPY** (control only, not traded)
* growth, sign +1 (higher than forecast = stronger): All Industries Activity m/m (109); BSI Manufacturing Index (50); Capital Spending q/y (50); Core Machinery Orders m/m (167); Final GDP q/q (50); Household Spending y/y (165); Leading Indicators (70); Prelim GDP q/q (51); Prelim Industrial Production m/m (165); Retail Sales y/y (168); Revised Industrial Production m/m (151); Tankan Manufacturing Index (51); Tankan Non-Manufacturing Index (51); Tertiary Industry Activity m/m (168)
* inflation, sign +1: Average Cash Earnings y/y (165); National Core CPI y/y (124); Prelim GDP Price Index y/y (51); Tokyo Core CPI y/y (161)
* excluded (no growth/inflation reading or not numeric): BOJ Policy Rate; Current Account; Monetary Base y/y; Overnight Call Rate; Trade Balance

Judgement calls: house-price indices and mortgage/lending volumes are counted as growth (+); wages, unit labour costs, import prices,
PPI and GDP deflators as inflation (+); productivity as growth (+). External and fiscal balances, monetary aggregates, inventories,
policy rates, votes and auctions are excluded rather than signed. The module raises an error for any event type that is not in the map.

### Usable releases per currency and year (in the universe, mapped, with a z-score)
|   year |   USD all |   USD gro |   USD inf |   EUR all |   EUR gro |   EUR inf |   GBP gro |   GBP inf |   JPY gro |   JPY inf |
|-------:|----------:|----------:|----------:|----------:|----------:|----------:|----------:|----------:|----------:|----------:|
|   2010 |       182 |       150 |        32 |       113 |        92 |        21 |        64 |        17 |        20 |         8 |
|   2011 |       464 |       367 |        97 |       327 |       267 |        60 |       188 |        60 |        64 |        24 |
|   2012 |       502 |       390 |       112 |       354 |       294 |        60 |       207 |        60 |       107 |        28 |
|   2013 |       512 |       400 |       112 |       430 |       365 |        65 |       210 |        60 |       108 |        28 |
|   2014 |       530 |       418 |       112 |       470 |       396 |        74 |       210 |        60 |       108 |        37 |
|   2015 |       534 |       422 |       112 |       505 |       419 |        86 |       218 |        60 |       108 |        39 |
|   2016 |       536 |       424 |       112 |       513 |       426 |        87 |       218 |        60 |       108 |        40 |
|   2017 |       538 |       425 |       113 |       505 |       418 |        87 |       211 |        60 |       108 |        40 |
|   2018 |       536 |       423 |       113 |       506 |       420 |        86 |       206 |        60 |       109 |        40 |
|   2019 |       527 |       418 |       109 |       511 |       427 |        84 |       228 |        60 |       120 |        40 |
|   2020 |       547 |       435 |       112 |       510 |       426 |        84 |       234 |        60 |       117 |        40 |
|   2021 |       574 |       462 |       112 |       515 |       431 |        84 |       240 |        60 |       108 |        39 |
|   2022 |       582 |       469 |       113 |       523 |       436 |        87 |       244 |        59 |       108 |        41 |
|   2023 |       604 |       486 |       118 |       512 |       425 |        87 |       244 |        60 |       108 |        40 |
|   2025 |         7 |         5 |         2 |        11 |         9 |         2 |         3 |         0 |         2 |         0 |
|   2026 |       394 |       308 |        86 |       335 |       285 |        50 |       134 |        27 |        63 |        17 |
2010 is thin because every type needs 8 earlier releases; 2024 has no rows; 2025 has 18 USD/EUR rows (October-November snapshot); 2026
covers 2 January to 2 September (EUR) / 2 October (USD).

## Data momentum from published levels (no archive hole)
| series | file | transformation | publication stamp used |
|---|---|---|---|
| US payrolls | `fred_PAYEMS.csv` | 3m annualised log change minus 12m log change | first "Employment Situation" date in `us_bls_releases.csv` on/after the 1st of the next month (2010+) |
| US unemployment rate | `fred_UNRATE.csv` | -(4 x 3m change - 12m change) | same |
| US CPI (SA) | `fred_CPIAUCSL.csv` | 3m annualised minus 12m; 12m rate for the Taylor rule | first "CPI" date in `us_bls_releases.csv` on/after the 1st of the next month (2010+) |
| US real retail sales | `fred_RSAFS.csv` / CPI | 3m annualised minus 12m | reference month end + 45 days |
| US industrial production | `fred_INDPRO.csv` | 3m annualised minus 12m | reference month end + 45 days |
| US housing starts | `fred_HOUST.csv` | log(3m mean / 12m mean) | reference month end + 45 days |
| US initial claims (weekly) | `fred_ICSA.csv` | -log(4w mean / 52w mean) | week-ending Saturday + 6 days (published the Thursday after) |
| EA HICP (NSA index) | `fred_CP0000EZ19M086NEST.csv` (to 2026-09; `ea_hicp.csv` is stale after 2025-12 and is not used) | causal seasonal adjustment of the monthly change (same-month mean of the previous 5 years minus the mean of the previous 60 months), then 3m annualised minus 12m | reference month end + 45 days |
| EA unemployment rate | `ea_unemployment.csv` | -(4 x 3m change - 12m change) | reference month end + 45 days |

* Before 2010 the BLS calendar has no rows: reference month end + 45 days (training window only).
* 2025 US shutdown: the calendar rows for October-December 2025 are the original schedule, so overrides were written **from memory,
  conservatively**: September jobs 2025-11-20, October/November jobs 2025-12-16, September CPI 2025-10-24, November CPI 2025-12-18
  (October CPI and unemployment were never published and are missing in the FRED mirror: the value is interpolated only as a base for
  later changes, the month itself produces no observation); Census/Fed series for reference months 2025-08..2025-11: month end + 100
  days; claims for weeks ending 2025-09-27..2025-11-08: not before 2025-11-21.
* On top of every stamp the feature-store convention adds one calendar day (`_align_lagged`): a release is first used at the next
  session close. A series older than 150 days (claims 60) is treated as missing.
* Scaling: each component is divided by 1.4826 x the median |x| of its previous 120 months (36 minimum, earlier values only; claims
  520 / 156 weeks) and clipped at +-3, so the 2020 collapse does not set the scale. US growth composite = mean of the six US
  components (at least 3). **Euro-area growth has one series only (unemployment)**: there is no EA production, sales or survey level
  series in `data/macro/`, so "US minus EA growth momentum" is a six-series composite against one series; `us_act` tests the US leg alone.
* Taylor rule: TR = 1.5 x 12m inflation - 1.0 x unemployment gap, gap = rate minus its trailing 10-year mean (3 years minimum),
  i.e. weight 0.5 on an output gap with an Okun coefficient of 2; differential = TR_US - TR_EA, level (demeaned with the training mean)
  and 63-session change.
* **Vintage caveat (not a timing leak, but not real-time either):** the FRED mirrors hold the latest revised vintage. Payrolls,
  retail sales, industrial production, housing starts and EA unemployment are revised after first publication; CPI NSA / HICP and the
  US unemployment rate are essentially unrevised. No data-momentum variant is the final, so this does not affect the delivered stream.

## Signals (11), priors fixed before any result
| signal     | kind   | definition (already oriented: positive -> long EUR/USD)                   |
|:-----------|:-------|:--------------------------------------------------------------------------|
| esi10      | cont   | + (EUR - USD) surprise index, all releases, half-life 10 days             |
| esi30      | cont   | + (EUR - USD) surprise index, all releases, half-life 30 days             |
| esi60      | cont   | + (EUR - USD) surprise index, all releases, half-life 60 days             |
| esi_chg    | cont   | + 20-session change of the half-life-30 (EUR - USD) surprise index        |
| esi_gro    | cont   | + (EUR - USD) GROWTH surprise index, half-life 30 days                    |
| esi_inf    | cont   | + (EUR - USD) INFLATION surprise index, half-life 30 days                 |
| gmom       | cont   | - (US growth-momentum composite - EA growth momentum [unemployment only]) |
| imom       | cont   | - (US CPI momentum - EA HICP momentum), 3m annualised minus 12m           |
| taylor     | level  | - Taylor-rule differential TR_US - TR_EA (level, demeaned in training)    |
| taylor_chg | cont   | - 63-session change of the Taylor-rule differential                       |
| us_act     | cont   | - US growth-momentum composite alone (6 series, no EA leg)                |

## Model, mapping, rule (house method of `arms/weak_signals.py`)
* Standardisation inside each training window: `cont` signals divided by the training sd (no demeaning: zero is the economic
  neutral point), `level` demeaned with the training mean; clipped at +-2 and halved. Missing = 0.
* Position = sign(z) when |z| > training median of |z| (over rows where the signal exists), times the vol scale
  min(1, median_train(rv_21d_bp) / rv_21d_bp). No other parameter.
* Combination `combo_tstat`: weight_i = max(t_i, 0), t_i = training-window t-stat of the correlation of signal i with `fwd_1d`
  (signals with fewer than 250 training rows get 0); same sign mapping on the weighted score.
* Walk-forward: `eurusd.wf.walk_forward`, yearly expanding, test years 2010-2026, `label_end_1d`.
* **Variants run: 12 candidates** (11 single signals + 1 combination). Not candidates: the same 12 position streams re-costed at
  0.6 pips, 5 label shuffles, 13 feature-shift re-runs and 200 circular-shift null draws of the final, one bias/timing split,
  and a post-hoc three-way check of four non-final variants (reported below, not used for anything).
* **Selection rule (in the module docstring before any result):** highest 2010-2015 walk-forward net Sharpe at 1.2 pips among
  candidates holding a position in at least 4 of the 6 years 2010-2015. Result: `single_esi60` (0.87, active 2012-2015).
  One design change was made before any return was looked at: the validity rule got the "at least one release in the last 10 days"
  clause after inspecting the index values (not P&L) around January 2024.

## Single-signal and combination table (net, 1.2 pips, Sharpe / t; periods_per_year 252; deflated-Sharpe p with n = 12)
| variant                  | 2010-2026     | 2016-2026     | 2023-2026     |   2010-15 |   2016-22 |   first OOS yr |   active |   defl. p |
|:-------------------------|:--------------|:--------------|:--------------|----------:|----------:|---------------:|---------:|----------:|
| single_esi10             | -0.11 / -0.47 | -0.17 / -0.58 | -0.42 / -0.83 |     -0.01 |     -0.1  |           2012 |     0.36 |      0.98 |
| single_esi30             | +0.11 / +0.48 | +0.00 / +0.01 | -0.33 / -0.65 |      0.3  |      0.13 |           2012 |     0.34 |      0.88 |
| **single_esi60 (FINAL)** | +0.59 / +2.47 | +0.41 / +1.36 | +0.11 / +0.22 |      0.87 |      0.53 |           2012 |     0.35 |      0.2  |
| single_esi_chg           | -0.17 / -0.69 | -0.05 / -0.16 | -0.15 / -0.31 |     -0.35 |     -0.02 |           2012 |     0.35 |      0.99 |
| single_esi_gro           | +0.25 / +1.05 | +0.13 / +0.43 | -0.15 / -0.30 |      0.45 |      0.23 |           2012 |     0.35 |      0.73 |
| single_esi_inf           | -0.04 / -0.15 | -0.40 / -1.34 | -1.30 / -2.58 |      0.53 |     -0.15 |           2012 |     0.36 |      0.97 |
| single_gmom              | -0.01 / -0.05 | -0.17 / -0.56 | -0.42 / -0.84 |      0.21 |     -0.02 |           2010 |     0.52 |      0.96 |
| single_imom              | -0.12 / -0.49 | +0.04 / +0.12 | +0.37 / +0.73 |     -0.36 |     -0.1  |           2010 |     0.45 |      0.98 |
| single_taylor            | +0.50 / +2.06 | +0.31 / +1.04 | -0.04 / -0.07 |      0.76 |      0.45 |           2010 |     0.58 |      0.34 |
| single_taylor_chg        | +0.07 / +0.28 | +0.23 / +0.77 | -0.25 / -0.51 |     -0.17 |      0.49 |           2010 |     0.58 |      0.92 |
| single_us_act            | +0.20 / +0.82 | +0.04 / +0.15 | +0.21 / +0.43 |      0.49 |     -0.02 |           2010 |     0.36 |      0.8  |
| combo_tstat              | +0.27 / +1.11 | +0.23 / +0.76 | -0.08 / -0.17 |      0.32 |      0.35 |           2010 |     0.69 |      0.71 |

Same positions at 0.6 pips:

| variant                  | 2010-2026     | 2016-2026     | 2023-2026     |   2010-15 |   2016-22 |   first OOS yr |   active |   defl. p |
|:-------------------------|:--------------|:--------------|:--------------|----------:|----------:|---------------:|---------:|----------:|
| single_esi10             | -0.08 / -0.32 | -0.13 / -0.45 | -0.39 / -0.78 |      0.02 |     -0.05 |           2012 |     0.36 |      0.98 |
| single_esi30             | +0.14 / +0.57 | +0.03 / +0.10 | -0.32 / -0.63 |      0.31 |      0.16 |           2012 |     0.34 |      0.86 |
| **single_esi60 (FINAL)** | +0.60 / +2.52 | +0.42 / +1.41 | +0.11 / +0.22 |      0.88 |      0.55 |           2012 |     0.35 |      0.19 |
| single_esi_chg           | -0.13 / -0.55 | -0.01 / -0.03 | -0.13 / -0.25 |     -0.33 |      0.03 |           2012 |     0.35 |      0.99 |
| single_esi_gro           | +0.27 / +1.13 | +0.15 / +0.52 | -0.14 / -0.28 |      0.46 |      0.26 |           2012 |     0.35 |      0.7  |
| single_esi_inf           | -0.02 / -0.09 | -0.38 / -1.28 | -1.28 / -2.55 |      0.54 |     -0.14 |           2012 |     0.36 |      0.96 |
| single_gmom              | -0.00 / -0.02 | -0.16 / -0.54 | -0.42 / -0.83 |      0.22 |     -0.01 |           2010 |     0.52 |      0.95 |
| single_imom              | -0.11 / -0.47 | +0.04 / +0.14 | +0.38 / +0.75 |     -0.36 |     -0.09 |           2010 |     0.45 |      0.98 |
| single_taylor            | +0.50 / +2.07 | +0.31 / +1.05 | -0.03 / -0.07 |      0.76 |      0.45 |           2010 |     0.58 |      0.34 |
| single_taylor_chg        | +0.08 / +0.32 | +0.24 / +0.81 | -0.24 / -0.48 |     -0.16 |      0.5  |           2010 |     0.58 |      0.91 |
| single_us_act            | +0.20 / +0.84 | +0.05 / +0.17 | +0.22 / +0.44 |      0.49 |     -0.01 |           2010 |     0.36 |      0.8  |
| combo_tstat              | +0.29 / +1.19 | +0.25 / +0.84 | -0.07 / -0.14 |      0.34 |      0.37 |           2010 |     0.69 |      0.68 |

Turnover is low (final: 9.4 units per year; gross Sharpe 0.62), so the cost assumption hardly matters.

Combination weights by test year (`macro_nowcast_weights.csv`):

|   test_year |   esi10 |   esi30 |   esi60 |   esi_chg |   esi_gro |   esi_inf |   gmom |   imom |   taylor |   taylor_chg |   us_act |
|------------:|--------:|--------:|--------:|----------:|----------:|----------:|-------:|-------:|---------:|-------------:|---------:|
|        2010 |    0    |    0    |    0    |      0    |      0    |      0    |   0.34 |   0.43 |     0.17 |         0.06 |     0    |
|        2011 |    0    |    0    |    0    |      0    |      0    |      0    |   0.3  |   0.04 |     0.25 |         0.37 |     0.04 |
|        2012 |    0.14 |    0.14 |    0.16 |      0.12 |      0.18 |      0    |   0.11 |   0.02 |     0.06 |         0.05 |     0.01 |
|        2013 |    0.15 |    0.15 |    0.17 |      0.12 |      0.18 |      0    |   0.11 |   0.02 |     0.05 |         0.04 |     0.02 |
|        2014 |    0.16 |    0.14 |    0.16 |      0.11 |      0.17 |      0    |   0.13 |   0.02 |     0.04 |         0.04 |     0.02 |
|        2015 |    0.14 |    0.15 |    0.18 |      0.09 |      0.17 |      0.02 |   0.1  |   0    |     0.09 |         0.02 |     0.02 |
|        2016 |    0.1  |    0.15 |    0.17 |      0.02 |      0.15 |      0.07 |   0.14 |   0    |     0.15 |         0    |     0.04 |
|        2017 |    0.11 |    0.15 |    0.17 |      0.02 |      0.17 |      0.05 |   0.13 |   0    |     0.15 |         0    |     0.05 |
|        2018 |    0.12 |    0.16 |    0.18 |      0.04 |      0.16 |      0.07 |   0.11 |   0    |     0.11 |         0    |     0.03 |
|        2019 |    0.13 |    0.16 |    0.18 |      0.04 |      0.16 |      0.08 |   0.11 |   0    |     0.11 |         0    |     0.03 |
|        2020 |    0.13 |    0.16 |    0.18 |      0.04 |      0.16 |      0.09 |   0.1  |   0    |     0.1  |         0    |     0.03 |
|        2021 |    0.12 |    0.14 |    0.16 |      0.02 |      0.14 |      0.09 |   0.11 |   0    |     0.14 |         0.04 |     0.04 |
|        2022 |    0.12 |    0.15 |    0.17 |      0.01 |      0.15 |      0.08 |   0.07 |   0    |     0.15 |         0.06 |     0.04 |
|        2023 |    0.1  |    0.14 |    0.16 |      0.03 |      0.16 |      0.04 |   0.08 |   0    |     0.18 |         0.06 |     0.05 |
|        2024 |    0.11 |    0.13 |    0.15 |      0.03 |      0.16 |      0.02 |   0.08 |   0    |     0.19 |         0.06 |     0.06 |
|        2025 |    0.1  |    0.13 |    0.15 |      0.03 |      0.16 |      0.02 |   0.09 |   0    |     0.18 |         0.06 |     0.06 |
|        2026 |    0.11 |    0.13 |    0.16 |      0.03 |      0.16 |      0.02 |   0.07 |   0    |     0.2  |         0.07 |     0.06 |

## Final variant `single_esi60`, per year
|   year |   net bp/session |   sum bp |   Sharpe 1.2 |   Sharpe 0.6 |   active |
|-------:|-----------------:|---------:|-------------:|-------------:|---------:|
|   2010 |             0    |        0 |         0    |         0    |     0    |
|   2011 |             0    |        0 |         0    |         0    |     0    |
|   2012 |             1.97 |      513 |         1.13 |         1.15 |     0.39 |
|   2013 |             2.2  |      571 |         1    |         1.01 |     0.58 |
|   2014 |             5.05 |     1304 |         2.38 |         2.39 |     0.66 |
|   2015 |             0.63 |      162 |         0.21 |         0.22 |     0.66 |
|   2016 |             0.72 |      188 |         0.56 |         0.57 |     0.15 |
|   2017 |             3.72 |      964 |         1.73 |         1.74 |     0.51 |
|   2018 |             1.82 |      473 |         0.73 |         0.74 |     0.79 |
|   2019 |             0.1  |       27 |         0.09 |         0.14 |     0.36 |
|   2020 |            -1.82 |     -473 |        -0.98 |        -0.96 |     0.66 |
|   2021 |             1.25 |      323 |         1.21 |         1.24 |     0.2  |
|   2022 |             0.35 |       92 |         0.5  |         0.53 |     0.05 |
|   2023 |            -0.56 |     -145 |        -0.25 |        -0.24 |     0.64 |
|   2024 |             0.33 |       86 |         0.77 |         0.78 |     0.08 |
|   2025 |             0    |        0 |         0    |         0    |     0    |
|   2026 |             0.88 |      193 |         1.15 |         1.16 |     0.14 |

2010-2026: Sharpe 0.59, t 2.47, +4,278 bp; 2016-2026: 0.41, t 1.36, +1,728 bp; 2023-2026: 0.11, t 0.22, +134 bp; 2010-2015: 0.87;
2016-2022: 0.53. Position: long 13 % of sessions, short 21 %, flat 65 %. Half of the total comes from 2014 (+1,304 bp, short on 66 % of
sessions and never long: euro-area data missed forecasts relative to US data into the EUR/USD collapse) and 2017 (+964 bp, long on 51 %, never short).

## Incremental value (`meta.combine(..., "EW")`, `report_combo`)
| combo     | period    |    n |   sharpe |     t |   mean_bp |   sum_bp |
|:----------|:----------|-----:|---------:|------:|----------:|---------:|
| two_way   | 2010-2026 | 4373 |    0.563 | 2.347 |     0.583 | 2547.29  |
| two_way   | 2016-2026 | 2817 |    0.636 | 2.128 |     0.738 | 2078.3   |
| two_way   | 2023-2026 | 1000 |    0.356 | 0.708 |     0.42  |  420.283 |
| two_way   | 2013-2026 | 3593 |    0.622 | 2.347 |     0.709 | 2547.29  |
| three_way | 2010-2026 | 4373 |    0.74  | 3.081 |     0.695 | 3038.1   |
| three_way | 2016-2026 | 2817 |    0.694 | 2.32  |     0.67  | 1886.1   |
| three_way | 2023-2026 | 1000 |    0.347 | 0.692 |     0.322 |  322.14  |
| three_way | 2013-2026 | 3593 |    0.816 | 3.081 |     0.846 | 3038.1   |

Per year (Sharpe):

| combo     |   2010 |   2011 |   2012 |   2013 |   2014 |   2015 |   2016 |   2017 |   2018 |   2019 |   2020 |   2021 |   2022 |   2023 |   2024 |   2025 |   2026 |
|:----------|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|-------:|
| two_way   |      0 |      0 |      0 |  -0.28 |   2.23 |   0    |   0.52 |   1.73 |  -0.05 |   0.51 |   1.12 |   0.57 |   1.21 |   0.09 |   0.34 |   0.53 |   0.63 |
| three_way |      0 |      0 |      0 |   0.79 |   2.47 |   0.18 |   0.71 |   1.86 |   0.34 |   0.42 |   0.4  |   0.96 |   1.35 |  -0.06 |   0.45 |   0.53 |   0.88 |

The arm enters the EW from 2013 (14 years; its trailing t-stat is positive every year). Three-way beats two-way on 2010-2026
(0.74 vs 0.56) and on 2016-2026 (0.69 vs 0.64); on 2023-2026 it is marginally lower (0.35 vs 0.36) because the arm is flat for most
of that period and only dilutes. The 2016-2026 gain of 0.06 Sharpe is far inside the noise (the standard error of a Sharpe over 11 years is about 0.30).

Daily net-P&L correlation of the final stream with the live streams and with the raw building blocks:

| other                         | period    |   corr_daily_pnl |   corr_when_arm_active |   corr_monthly_pnl |
|:------------------------------|:----------|-----------------:|-----------------------:|-------------------:|
| weak_signals                  | 2010-2026 |             0.18 |                   0.34 |               0.1  |
| weak_signals                  | 2016-2026 |             0.23 |                   0.41 |               0.1  |
| weak_signals                  | 2023-2026 |             0.26 |                   0.55 |               0.23 |
| regime_trend(positioning)     | 2010-2026 |             0.07 |                   0.11 |               0.14 |
| regime_trend(positioning)     | 2016-2026 |             0.13 |                   0.23 |               0.11 |
| regime_trend(positioning)     | 2023-2026 |             0.03 |                   0.06 |               0.05 |
| raw sign(cot_z52) x vol       | 2010-2026 |             0.08 |                   0.14 |               0.14 |
| raw sign(cot_z52) x vol       | 2016-2026 |             0.13 |                   0.23 |               0.11 |
| raw sign(cot_z52) x vol       | 2023-2026 |             0.03 |                   0.06 |               0.05 |
| raw sign(d_spread2y_20) x vol | 2010-2026 |             0.07 |                   0.12 |               0.04 |
| raw sign(d_spread2y_20) x vol | 2016-2026 |             0.16 |                   0.28 |               0.15 |
| raw sign(d_spread2y_20) x vol | 2023-2026 |             0.16 |                   0.34 |               0.11 |

`corr_when_arm_active` uses only sessions where this arm holds a position. The stream is not a copy of positioning or of the spread
trend; its overlap with weak_signals is modest overall but rises to 0.55 on the few active sessions of 2023-2026.

Post-hoc, for information only (three-way EW Sharpe 2010-26 / 2016-26 / 2023-26 if another variant had been the final):
`single_taylor` 0.67 / 0.67 / 0.29, `combo_tstat` 0.60 / 0.61 / 0.26, `single_esi_gro` 0.55 / 0.58 / 0.25, `single_us_act` 0.48 / 0.49 / 0.35
(two-way: 0.56 / 0.64 / 0.36). Only the Taylor level would also have added on 2016-2026, and it loses on 2023-2026.

## Leak checks (final variant; net Sharpe 2010-26 / 2016-26 / 2023-26 at 1.2 pips)
1. **Shuffled labels** (5 permutations, fit and evaluation both see the shuffled label): +0.23 / +0.30 / -0.02; -0.05 / +0.31 / -0.76; -0.26 / -0.28 / -0.94; -0.11 / -0.18 / -0.04; -0.21 / +0.04 / +0.14. Mean of the five 2010-2026 values
   -0.08: zero skill, as it should be.
2. **Features shifted forward** (stale signal) and look-ahead controls:

| shift (sessions)         | 2010-26 / 2016-26 / 2023-26   |
|:-------------------------|:------------------------------|
| +1                       | +0.52 / +0.37 / +0.21         |
| +5                       | +0.42 / +0.36 / +0.17         |
| +21                      | +0.38 / +0.19 / -0.19         |
| +42                      | +0.47 / +0.15 / +0.28         |
| +63                      | +0.48 / +0.21 / +0.30         |
| +126                     | +0.40 / +0.41 / +0.09         |
| +189                     | +0.22 / +0.26 / -0.23         |
| +252                     | +0.29 / +0.40 / +0.45         |
| +378                     | -0.29 / -0.17 / -0.81         |
| +504                     | +0.24 / +0.26 / +0.34         |
| -5 (look-ahead control)  | +0.67 / +0.68 / +0.16         |
| -21 (look-ahead control) | +0.39 / +0.53 / +0.22         |
| -63 (look-ahead control) | -0.24 / +0.11 / +0.39         |

   **The result does NOT collapse.** One session of lag costs nothing material (expected for a 60-day half-life), but a lag of 126
   sessions, where the lagged index has autocorrelation 0.03 with the timely one, still gives 0.40 / 0.41, and 252 sessions gives
   0.29 / 0.40. Looking ahead by 5 sessions helps a little (0.67 / 0.68), by 21 or 63 sessions not at all. So there is no sign of a timing leak, and equally no
   evidence that the *timeliness* of the surprise information is what earns the P&L.
   Circular-shift null (the signal rolled by a random offset of at least one year inside 2010-2026, 200 draws; keeps the
   autocorrelation, destroys the timing):

| period    |   sharpe |   null_mean |   null_sd |   null_q95 |   p_null_ge_actual |
|:----------|---------:|------------:|----------:|-----------:|-------------------:|
| 2010-2026 |    0.593 |       0.01  |     0.243 |      0.405 |              0.01  |
| 2016-2026 |    0.407 |      -0.017 |     0.326 |      0.526 |              0.125 |
| 2023-2026 |    0.109 |      -0.085 |     0.488 |      0.711 |              0.38  |

   2010-2026 is at p = 0.01 against this null before any correction for the 12 variants; the part that was not used for selection
   (2016-2026) is at p = 0.13.
3. **Top features / label in disguise.** The final uses one feature, `esi_EURmUSD_all_hl60`, built only from releases whose
   availability time is <= the session close; truncation test on 40 random sessions: max |difference| = 0.0e+00, validity
   mismatches = 0. Full-sample correlation of each standardised signal with `fwd_1d` (a disguised label would be far above 0.05):

| signal     |   corr_with_fwd_1d |    n |
|:-----------|-------------------:|-----:|
| esi10      |             0.0209 | 3611 |
| esi30      |             0.027  | 3567 |
| esi60      |             0.0341 | 3494 |
| esi_chg    |             0.0062 | 3527 |
| esi_gro    |             0.0341 | 3571 |
| esi_inf    |             0.0025 | 3552 |
| gmom       |             0.0116 | 5878 |
| imom       |            -0.0044 | 5571 |
| taylor     |             0.0312 | 6154 |
| taylor_chg |             0.0107 | 6091 |
| us_act     |             0.0099 | 6186 |

4. **Static bias?** (`macro_nowcast_bias_timing.csv`)

| stream                                |   SR_2010-2026 |   SR_2016-2026 |   SR_2023-2026 |   t_2010-2026 |   long_frac |   short_frac |
|:--------------------------------------|---------------:|---------------:|---------------:|--------------:|------------:|-------------:|
| final                                 |           0.59 |           0.41 |           0.11 |          2.47 |        0.13 |         0.21 |
| timing_only(pos - expanding mean pos) |           0.57 |           0.41 |           0.13 |          2.38 |        0.64 |         0.24 |
| bias_only(expanding mean pos)         |           0.26 |           0.04 |          -0.15 |          1.1  |        0.04 |         0.84 |
| always_short_when_active              |          -0.09 |          -0.44 |           0.03 |         -0.37 |        0    |         0.35 |
| always_long_when_active               |           0.04 |           0.39 |          -0.05 |          0.17 |        0.35 |         0    |

   The record is not a constant short: the timing part carries it (0.57 / 0.41) and "always short when active" is negative. On
   2016-2026, however, "always long when active" earns the same 0.39 as the signal itself.

## What showed predictability, what did not
* **Surprise index, EUR minus USD.** Only the slowest version: half-life 60 days 0.59 / 0.41 / 0.11; 30 days 0.11 / 0.00 / -0.33;
  10 days -0.11 / -0.17 / -0.42; 20-session change -0.17 / -0.05 / -0.15. The monotone pattern (slower is better) agrees with round 2
  (fast surprise information is priced), but a result that exists at one of three half-lives is fragile.
* **Growth vs inflation surprises.** Growth 0.25 / 0.13 / -0.15 (right sign, insignificant). Inflation -0.04 / -0.40 / **-1.30
  (t -2.58)**: after 2016 the prior "higher relative inflation surprise -> stronger currency" has the wrong sign; the total index
  works despite, not because of, its inflation part.
* **Data momentum.** US-minus-EA growth momentum -0.01 / -0.17 / -0.42; inflation momentum -0.12 / +0.04 / +0.37; US activity alone
  0.20 / 0.04 / 0.21. Nothing.
* **Taylor-rule differential.** Level 0.50 (t 2.06) / 0.31 / -0.04; change 0.07 / 0.23 / -0.25. The level is a very slow position
  (turnover 2.6 position units per year: short EUR/USD 52 % of 2010-2015, long 30 % of 2023-2026 and never short there), so its t-stat rests on a
  handful of regimes; it fails the 2023-2026 condition.
* **Combination** of all eleven with t-stat weights: 0.27 / 0.23 / -0.08. Fails. The weights spread over five correlated surprise
  signals of which four do not work.

## Suspicious / caveats
* Selection among 12 by 2010-2015 Sharpe: the surprise variants have only 2012-2015 in that window, and 2014 alone (Sharpe 2.38)
  carries most of it (runner-up: `single_taylor` 0.76). The honest out-of-selection record is 2016-2026: 0.41, t 1.36.
* 2023-2026 "not negative" = 2023 (-0.25, 64 % active), January 2024, nothing in 2025, May-June 2026 only (+1.15 on 14 % of the year's sessions).
* The 2026 values come from low-quality mirrors (dates and values fine, times not) and the rows end on 2026-09-02 (EUR) /
  2026-10-02 (USD): **the index is currently undefined and cannot be run live without a new actual/forecast source.**
* The sign map and the growth/inflation split are hand-made judgement (listed above in full).
* A continuous archive for 2024-2025 would be the decisive test; with it the 60-day index would get about 500 more out-of-sample sessions.
