# ARM E - event-driven prediction (round 2)

Code: `src/eurusd/arms/events.py` (`run(cost_pips=1.2)`). OOS positions of the final variant:
`experiments/results/arms/events_positions.parquet`; all variants: `experiments/results/arms/events_report.csv`
(`variant`, `cost_pips`, `final` columns; `*_all_variants_oos.parquet` has every variant's OOS decisions).

## Idea
Scheduled releases are the one moment new information arrives. Round 1 only tested unconditional rules around them;
here walk-forward models (yearly expanding, `eurusd.wf`) are fitted on **one decision per event** on three grids:

| grid | decision time | hold | label | decisions (2003/2010-2026) |
|---|---|---|---|---|
| POST | release + 5 min (first M5 jump observed) | 1h / 4h / to 21:00 UTC / 24h | M5-close log return (bp) | 1,390: ecb 238, nfp 207, cpi 203 (CPI+Core merged), fomc 192, ism 173, pce 168, retail 155, gdp 54 |
| PRE | release - 24h | to the bar ending at the release minute | same | 1,283 (same kinds) |
| DIV | close of the 5th session after each FOMC/ECB decision | 5 / 10 sessions | `fwd_5d`/`fwd_10d` from the daily store | 437: ecb 240, fomc 197 |

Event universe: US data (NFP, CPI/Core CPI, retail sales, ISM manufacturing, advance GDP, core PCE) from the ForexFactory archive
2010-2023 + 2026 partial (actual/forecast), BLS verified dates 2017-2026 for NFP/CPI (no surprise value in 2024-25 -> `sur_missing`=1),
FOMC statements (scheduled) and ECB decisions 2003-2026 from the verified tables. Release times for US data use the ET rule
(08:30 ET; ISM 10:00 ET) because the 2026 FF timestamps are inconsistent (09:30Z/11:30Z duplicates); the rule agrees with the
2010-2023 archive on 999/1010 rows and the M5 bar at the rule time carries the jump (|ret| 17 bp vs 2.5 bp in the bars around it).
Simultaneous releases (same minute) are merged into one decision (surprise = mean of the aligned z's, kind by priority).

## Features (all known at the decision time)
* new information: surprise z aligned to EUR/USD direction ((actual-forecast)/expanding sd of past surprises of that series,
  sd shifted so each z uses earlier releases only; US data sign -1, ECB +1), `sur_missing`, first 5-min jump `jump5` (bp),
  `jump_z` = jump / 24h realised 5-min vol, `jump_x_sur` (jump x sign(surprise): under/over-reaction), central-bank rate change.
* context: pre-release 24h and 4h drift, `cot_z52`, `cot_d4`, `d_spread2y_20`, `d_spread2y_5`, `d_us2y_5`, `policy_diff`,
  `rv_21d_bp`, `rv5m`, `vix`, `fv_resid_z`, `ret_5d`, `ret_21d`, `dist_sma50_atr` (daily store row with close_time <= decision),
  previous same-kind release: its 4h reaction, its jump, whether the market followed its surprise (`prev_follow`), `prev_react_x_sur`;
  PRE grid: previous pre-drift; DIV grid: `d_spread2y_5` (the ECB-vs-Fed repricing since the decision), `spread_x_fomc`.
* event-type dummies (8 kinds), pooled models.

## Models and rules (fixed before results)
* Ridge (alpha from {1..3000} by 4-fold expanding time-ordered CV inside the training window, target winsorised at 1/99 pct),
  logistic on sign (C by CV log-loss, output (2p-1) x mean|r|), LightGBM (150 trees, 4 leaves, lr 0.03, lambda 10, 1 thread, no tuning).
  Features standardised with training mean/sd, NaN -> 0.
* Position = sign(forecast) only when |forecast| > round-trip cost at 1.2 pips (2 x 1.2 pips in bp at the entry price); the
  0.6-pip run keeps the same positions. Each decision is a round trip, so cost = 2 x cost_bp x |pos| (asserted equal to
  `wf.pnl_from_positions` on the entry/exit pair). `periods_per_year` = decisions per year of the variant (73.8 for POST, 16.8 for CB-only).
* Walk-forward: `wf.walk_forward` with `label_end` = horizon end; the harness requires >= 200 training rows, so POST/PRE pooled
  models start in 2011 and FOMC/ECB-only models (~20 events/yr from 2003) in 2013. 2010 has no decisions.
* **Selection rule (declared in the module docstring before any OOS result):** the variant with the highest 2010-2015 net
  Sharpe at 1.2 pips among variants with >= 100 OOS decisions in 2010-2015. **Variants run: 16** (15 single + 1 combination),
  plus 9 leak-check reruns that are not candidates. Deflated-Sharpe p in the csv uses n_arms = 16.

## Results (net, 1.2 pips; annualised Sharpe / t)

| variant | 2010-15 | 2010-26 | 2016-26 | 2023-26 | n | active |
|---|---|---|---|---|---|---|
| **P1 post ridge 1h (FINAL by rule)** | 0.37 | **-0.10 / -0.41** | **-0.49 / -1.56** | **-0.60 / -1.00** | 1169 | 0.46 |
| P2 post ridge 4h | 0.28 | -0.13 | -0.49 | -0.21 | 1169 | 0.49 |
| P3 post ridge to-close | 0.18 | -0.10 | -0.39 | 0.53 | 1169 | 0.41 |
| P4 post logit 4h | 0.26 | -0.00 | -0.22 | -0.04 | 1169 | 0.46 |
| P5 post LightGBM 4h | -0.10 | -0.53 | -0.85 | 0.02 | 1169 | 0.73 |
| P6 post ridge 4h, data releases only | -0.48 | -0.26 | -0.22 | 0.07 | 650 | 0.16 |
| P7 post ridge 4h, FOMC+ECB only | 0.48 (n=60) | -0.11 | -0.40 | -0.68 | 230 | 0.81 |
| P8 post ridge 4h, new-information features only | 0.30 | -0.12 | -0.49 | -0.22 | 1169 | 0.47 |
| P9 post ridge 4h, context features only | 0.05 | -0.15 | -0.28 | -0.71 | 1169 | 0.29 |
| P10 post ridge 24h | 0.11 | -0.12 | -0.26 | 0.13 | 743 | 0.80 |
| R1 pre ridge 24h, all events | -0.12 | 0.00 | 0.10 | 0.41 | 1076 | 0.83 |
| R2 pre ridge 24h, FOMC+ECB only | 0.49 (n=60) | 0.64 / 2.39 | 0.70 / 2.24 | 0.18 / 0.35 | 232 | 0.98 |
| R3 pre ridge 24h, FOMC+ECB, kind dummies only | 0.56 (n=60) | 0.67 / 2.47 | 0.70 / 2.24 | 0.18 / 0.35 | 232 | 1.00 |
| D1 div ridge 10d | -0.06 (n=60) | -0.26 | -0.35 | 0.36 | 234 | 0.72 |
| D2 div ridge 5d | 0.33 (n=60) | 0.03 | -0.07 | -0.08 | 234 | 0.85 |
| C1 combo P2+R1+D1 (fixed components) | 0.03 | -0.23 | -0.39 | 0.48 | 2479 | 0.66 |

Final variant P1 per year (net bp/decision, Sharpe at 1.2 | 0.6 pips): 2011 -5.0 (-1.58 | -1.37), 2012 1.0 (0.63 | 0.80),
2013 -0.7 (-0.35 | -0.09), 2014 3.0 (1.41 | 1.60), 2015 6.7 (1.74 | 1.89), 2016 -0.9 (-0.33 | -0.13), 2017 -4.5 (-2.03 | -1.69),
2018 -0.9 (-0.66 | -0.45), 2019 1.2 (0.78 | 1.05), 2020 -1.6 (-1.31 | -1.03), 2021 -0.5 (-0.45 | -0.16), 2022 0.7 (0.26 | 0.48),
2023 0.8 (0.60 | 0.97), 2024 0.9 (0.48 | 0.78), 2025 -8.1 (-3.75 | -3.58), 2026 1.4 (1.55 | 1.78).
Aggregates at 0.6 pips: 2010-2026 0.11 (t 0.44), 2016-2026 -0.24, 2023-2026 -0.33. Gross (no cost) 2010-2026 Sharpe 0.32,
2016-2026 0.00. Deflated-Sharpe p = 0.99. **The arm fails the success bar; the post-release idea is a clean negative.**

## What helped, what did not
* Nothing conditional. After the first 5 minutes, neither the surprise z, the jump (continuation or fade), the jump-vs-surprise
  disagreement, pre-release drift, positioning, rate trend, vol regime nor the previous release's reaction predicts the next
  1h-24h with enough strength to cover 2.4 pips; P8 (new-information only) = P2 (all) = P9 (context only) ~ -0.1 to -0.15
  2010-2026. Gross Sharpe is ~0.1-0.3 for every POST variant: the market absorbs the surprise in the release bar.
* LightGBM is worse than ridge (over-fits 1,000 rows); logistic ~ ridge. Horizon does not matter. Central-bank-only POST (P7) fails.
* DIV (2y-spread repricing after a decision as a 5-20 day signal): no (D1 -0.26, D2 0.03).
* The only positive numbers, R2/R3 (long EUR/USD during the 24h into FOMC and ECB decisions; 0.64-0.67 Sharpe, t 2.4, 2023-2026
  0.18, 16.8 decisions/yr), are **not conditional predictability**: the CV picks alpha = 1000, the model collapses to its intercept
  (228/232 positions are +1), and R3 with only the two kind dummies does the same. This is round-1's H09 "long into FOMC"
  (FOMC 7.8 bp/decision t 2.2, ECB 4.6 bp t 1.3 here). The conditional expectation proxies (`d_us2y_5`, `d_spread2y_*`,
  `policy_diff`, `cot_z52`, `fv_resid_z`, previous pre-drift) add nothing (R2 = R3). The shuffle check makes this explicit:
  permuting labels leaves R2/R3 at 0.56 (gross 0.75) because a permutation preserves the unconditional mean. R2 was also not
  eligible under the pre-declared rule (60 decisions in 2010-2015) and is not the final; the lead may consider the unconditional
  drift separately (it earned -2.8 bp/decision in 2024 and -15 bp in 2026, so the recent record is weak).

## Leak checks (final variant P1; net Sharpe 2010-26 / 2016-26 / 2023-26, gross in brackets)
1. Shuffled labels: -0.52 / -0.76 / -0.91 (gross -0.36 / -0.61 / -0.81): zero skill plus the cost drag; gross ~ 0 within noise.
2. Features lagged by one event (stale, `shift(+1)`): -0.49 / -0.44 / -0.83 (gross -0.20 / -0.16 / -0.58): collapses to the shuffle level.
3. Features shifted to the *next* event (`shift(-1)`, deliberate look-ahead): 0.20 / 0.12 / -0.01 (gross 0.61 / 0.63 / 0.56) -
   look-ahead improves gross Sharpe as it should, confirming the pipeline is sensitive to timing and the true-time result (0.32 gross) is not leaked.
4. Top ridge features (coefficients on standardised inputs, last training window): PRE-CB model: `cot_z52`, `prev_pre`, `d_us2y_5`,
   `ret_5d`, `ret_21d` (all < 1.2 bp per sd vs an intercept of 9 bp); POST 1h model (alpha 3000, all coefficients < 0.7 bp per sd):
   `jump_z`, `jump5`, `prev_react`, `cot_z52`, `rate_chg`.
   None is a label in disguise: `jump5` ends at the entry price, `pre24` ends at the release minute, `prev_react` is the previous
   event's completed label, `sur` uses only the release's own actual/forecast, daily context uses close_time <= decision time
   (macro lagged one calendar day by the store). R2/R3 shuffle/shift checks are in the csv (unchanged by construction, see above).

## Suspicious / caveats
* 2024-2025: ForexFactory has no rows, so only NFP/CPI (BLS dates, no surprise value), FOMC and ECB decisions exist; 2026 values
  come from low-quality FF mirrors (actual/forecast used, times from the ET rule).
* 62 POST decisions start within 4h of the previous one (same-day releases); positions can overlap in time.
* FOMC statement time pre-2008 is the 14:15 ET rule; ECB decisions pre-2022-07 at 13:45 CET; the press conference falls inside
  every POST horizon. DIV decisions use the daily store's one-calendar-day macro lag, so `d_spread2y_5` at the 5th close covers
  decision day .. day 4.
* Walk-forward min-200-rows rule removes 2010 (all grids) and 2010-2012 for the CB-only grids.
