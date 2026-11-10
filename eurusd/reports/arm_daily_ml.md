# Arm `daily_ml`: supervised learning on the daily feature store

**Verdict: clean negative.** No variant clears the success bar (2010-2026 net Sharpe > 0.4, 2016-2026 > 0.3,
2023-2026 >= 0 at 1.2 pips). The rule-selected final variant (`ridge_1d_all`) has 2010-2026 net Sharpe 0.26
(t = 1.09), 2016-2026 0.09, 2023-2026 0.23; its 2010-2026 Sharpe is only ~1.2 sd above the shuffled-label null.
What the ablations do say: price/technical features alone are *negative* out of sample; the macro + positioning
block is the only group whose addition consistently moves the result towards zero or slightly positive.

Code: `src/eurusd/arms/daily_ml.py` (`run(cost_pips=1.2)` -> positions, report; `leak_checks()`).
Outputs: `experiments/results/arms/daily_ml_{positions.parquet, report.csv, meta.json, top_features.csv, leak_checks.csv}`.
Total CPU ~17 min for 23 variants + ~1 min for leak checks (single thread).

## Idea, features, models
* Inputs: the 131 feature columns of `data/processed/features_daily.parquet` (labels and meta excluded), split
  into groups **price** (38), **calendar** (7), **events** (26: event clocks, macro-surprise z-scores and their age),
  **macro** (56: yields, spreads and their changes, fair-value residual, VIX, dollar/cross-pair/equity/commodity/
  bond-future returns, USD factor), **positioning** (4 CFTC columns).
* Targets: `fwd_1d`, `fwd_5d` (regression), `tb_5d_1atr` (+1 vs -1, zeros dropped from training) and `sign(fwd_1d)`.
* Models: ridge on standardised features (NaN -> 0 after standardising; alpha in {10, 100, 1e3, 1e4});
  LightGBM (3 configs: 150/300/400 trees, 4/8/3 leaves, lr 0.03/0.02/0.01, min_child_samples 200/100/300,
  colsample 0.5, subsample 0.7, lambda_l2 10, `num_threads=1`); `avg` = mean of ridge and LightGBM after scaling
  each by the std of its validation-block predictions; logistic regression; LightGBM classifier on the barrier label.
* Hyper-parameters: time-ordered CV inside each training window. The last two calendar years of the window are
  the validation block; the config with the highest Pearson IC on it is refitted on the whole window.
* Decision rule: trade when |forecast| exceeds the q-quantile (q = 0.7 headline; 0.5 / 0.85 tested) of |forecast|
  on the validation block (a training-window term); position = sign (or clipped linear forecast/threshold);
  vol scaling: position *= min(1, median training `rv_21d_bp` / `rv_21d_bp`).
* Holding: 1-day targets -> one decision per session (`label_end_1d`). 5-day targets (`label_end_5d`) -> **1/5
  position increments**: the daily position is the mean of the last five raw signals (five overlapping tranches),
  P&L marked daily on `fwd_1d` (five `fwd_1d` sum to `fwd_5d`), costs on the smoothed position's turnover.
* Walk-forward: `eurusd.wf.walk_forward`, test years 2010..2026, expanding window, 252 periods/year.

## Selection rule (declared before results) and number of variants
Final = the variant with the highest **2010-2015** walk-forward net Sharpe at 1.2 pips among all variants run.
**23 variants** were run (8 model/target combinations on all features, 7 decision-rule variants of the `avg`
model, 8 feature-group ablations). Deflated-Sharpe p is computed with `n_arms=6` as the HOWTO prescribes; with
23 variants in this arm the honest deflation is harsher still.

## All variants (net Sharpe at 1.2 pips; t and active fraction for 2010-2026)
| variant | 2010-15 | 2016-22 | 2010-26 | 2016-26 | 2023-26 | t | active |
|---|---|---|---|---|---|---|---|
| **ridge_1d_all (FINAL)** | **0.50** | 0.03 | 0.26 | 0.09 | 0.23 | 1.09 | 0.29 |
| avg_1d_all_always (no threshold) | 0.36 | 0.53 | 0.38 | 0.41 | 0.17 | 1.60 | 1.00 |
| avg_1d_all_q85 | 0.34 | 0.37 | 0.27 | 0.23 | -0.07 | 1.14 | 0.14 |
| avg_5d_price | 0.30 | 0.09 | 0.07 | -0.13 | -0.48 | 0.29 | 0.53 |
| avg_5d_price_cal_ev | 0.28 | -0.08 | -0.01 | -0.33 | -0.69 | -0.04 | 0.51 |
| avg_1d_price_cal_ev | 0.26 | -0.42 | -0.16 | -0.52 | -0.70 | -0.68 | 0.28 |
| avg_1d_all_linear | 0.24 | 0.15 | 0.26 | 0.28 | 0.53 | 1.08 | 1.00 |
| lgbm_5d_all | 0.20 | 0.14 | 0.10 | 0.01 | -0.28 | 0.40 | 0.52 |
| avg_5d_all_linear | 0.10 | 0.24 | 0.09 | 0.09 | -0.25 | 0.39 | 1.00 |
| lgbm_1d_all | 0.09 | 0.19 | 0.19 | 0.27 | 0.40 | 0.80 | 0.27 |
| avg_1d_all | 0.06 | -0.08 | 0.04 | 0.03 | 0.25 | 0.18 | 0.28 |
| avg_1d_all_novol | 0.05 | -0.07 | 0.03 | 0.01 | 0.18 | 0.12 | 0.28 |
| logit_sign1d_all | -0.00 | -0.40 | -0.02 | -0.03 | 0.58 | -0.07 | 0.27 |
| avg_5d_all_q50 | -0.09 | 0.42 | 0.10 | 0.24 | -0.17 | 0.42 | 0.77 |
| avg_1d_all_q50 | -0.12 | -0.02 | 0.15 | 0.33 | 1.03 | 0.61 | 0.48 |
| lgbmtb_5d_all | -0.12 | 0.23 | 0.09 | 0.21 | 0.18 | 0.37 | 0.53 |
| avg_1d_price_cal_ev_macro | -0.13 | -0.23 | -0.11 | -0.09 | 0.20 | -0.45 | 0.28 |
| avg_1d_price | -0.24 | 0.02 | -0.25 | -0.26 | -0.71 | -1.02 | 0.29 |
| avg_1d_macro_pos | -0.29 | 0.24 | 0.05 | 0.26 | 0.32 | 0.20 | 0.28 |
| avg_5d_macro_pos | -0.29 | 0.26 | 0.01 | 0.20 | 0.07 | 0.06 | 0.51 |
| avg_5d_all | -0.31 | 0.53 | 0.05 | 0.32 | -0.13 | 0.20 | 0.54 |
| ridge_5d_all | -0.39 | 0.55 | 0.06 | 0.36 | -0.02 | 0.26 | 0.51 |
| avg_5d_price_cal_ev_macro | -0.47 | 0.12 | -0.26 | -0.09 | -0.57 | -1.08 | 0.51 |

Nothing is stable across sub-periods: the 2010-2015 ranking is almost uncorrelated with 2016-2026 (e.g. the
5-day ridge/avg models are the worst 2010-2015 and among the best 2016-2026). The one variant that is positive in
all three windows with the largest t (`avg_1d_all_always`, 0.38 / 0.41 / 0.17, t = 1.6) is not the rule-selected
one, and even it misses the 2016-2026 > 0.3-plus-2010-2026 > 0.4 bar; with 23 trials a t of 1.6 is unremarkable.

## Feature-group ablation (avg model, q = 0.7 sign rule, vol-scaled; net Sharpe at 1.2 pips)
| feature set | 1d: 2010-26 | 1d: 2016-26 | 1d: 2023-26 | 5d: 2010-26 | 5d: 2016-26 | 5d: 2023-26 |
|---|---|---|---|---|---|---|
| price only | -0.25 | -0.26 | -0.71 | 0.07 | -0.13 | -0.48 |
| + calendar + events | -0.16 | -0.52 | -0.70 | -0.01 | -0.33 | -0.69 |
| + macro | -0.11 | -0.09 | 0.20 | -0.26 | -0.09 | -0.57 |
| + positioning (= all) | 0.04 | 0.03 | 0.25 | 0.05 | 0.32 | -0.13 |
| macro + positioning only | 0.05 | 0.26 | 0.32 | 0.01 | 0.20 | 0.07 |

What the new information does and does not add:
* **Price/technical alone is negative** out of sample for both horizons once 1.2 pips are charged - a learner on
  daily technicals is worse than not trading.
* **Calendar + event clocks / surprises add nothing** on top of price (1d: -0.25 -> -0.16; 5d: 0.07 -> -0.01;
  2016-2026 gets worse in both).
* **Macro (yields/spreads/fair value/cross-asset) + positioning is where the small positive sign lives**: every
  set that contains macro and positioning is >= 0 for 2010-2026 and 2016-2026, and `macro_pos` alone is as good
  as `all`. The improvement is however tiny (Sharpe 0.0-0.3, t < 1) and not tradeable at retail cost.
* Ridge beats LightGBM on the 1-day target (0.26 vs 0.19) and the simple average is not better than either: the
  signal, if any, is linear and weak; trees find nothing non-linear worth the extra variance.
* Vol scaling matters little (0.04 vs 0.03), the threshold mainly changes activity, not quality.

## Final variant: `ridge_1d_all` - per-year record
Ridge on all 131 features, 1-day target, trade when |forecast| is in the top 30 % of the validation-block
distribution, sign position, vol-scaled. Chosen alpha is 1e3-1e4 in most years (very strong shrinkage);
validation IC of the chosen model is 0.00-0.17, mean 0.05. Long 13.6 % / short 15.4 % of days; essentially all
of the net P&L (2441 of 2442 bp) comes from short days.

| year | n | SR @1.2 | t @1.2 | sum bp @1.2 | active | SR @0.6 | sum bp @0.6 |
|---|---|---|---|---|---|---|---|
| 2010 | 260 | 0.39 | 0.39 | 271 | 0.53 | 0.42 | 296 |
| 2011 | 260 | 0.64 | 0.65 | 273 | 0.23 | 0.70 | 301 |
| 2012 | 260 | 1.97 | 2.00 | 820 | 0.20 | 2.05 | 851 |
| 2013 | 259 | 0.55 | 0.56 | 245 | 0.40 | 0.65 | 287 |
| 2014 | 258 | -1.46 | -1.48 | -592 | 0.42 | -1.35 | -546 |
| 2015 | 259 | 0.89 | 0.91 | 482 | 0.23 | 0.95 | 512 |
| 2016 | 259 | 1.00 | 1.02 | 491 | 0.27 | 1.08 | 529 |
| 2017 | 259 | 0.68 | 0.69 | 238 | 0.25 | 0.81 | 284 |
| 2018 | 260 | -2.12 | -2.15 | -1006 | 0.35 | -2.05 | -969 |
| 2019 | 260 | 0.26 | 0.26 | 62 | 0.25 | 0.42 | 101 |
| 2020 | 260 | 1.86 | 1.89 | 784 | 0.27 | 1.92 | 806 |
| 2021 | 259 | -0.56 | -0.57 | -136 | 0.17 | -0.45 | -110 |
| 2022 | 260 | -0.62 | -0.63 | -339 | 0.49 | -0.52 | -284 |
| 2023 | 258 | -0.58 | -0.59 | -223 | 0.21 | -0.48 | -185 |
| 2024 | 261 | 1.36 | 1.38 | 344 | 0.13 | 1.43 | 361 |
| 2025 | 260 | -0.60 | -0.61 | -167 | 0.09 | -0.55 | -153 |
| 2026 | 220 | 0.99 | 0.92 | 339 | 0.48 | 1.12 | 382 |
| **2010-2026** | 4372 | **0.26** | **1.09** | 1885 | 0.29 | 0.34 | 2463 |
| 2016-2026 | 2816 | 0.09 | 0.31 | 385 | 0.27 | 0.18 | 763 |
| 2023-2026 | 999 | 0.23 | 0.45 | 292 | 0.22 | 0.32 | 405 |
| 2010-2015 | 1556 | 0.50 | 1.24 | 1500 | 0.34 | 0.57 | 1700 |
| 2016-2022 | 1817 | 0.03 | 0.09 | 93 | 0.29 | 0.12 | 358 |

Deflated-Sharpe p (n_arms = 6) = 0.59. Fails the bar on 2010-2026 (0.26 < 0.4) and 2016-2026 (0.09 < 0.3).

## Leak checks (final variant, 2010-2026, 1.2 pips)
1. **Shuffled labels** (`fwd_1d`, `fwd_5d`, `tb_5d_1atr` permuted; whole pipeline re-run, 10 seeds):
   mean Sharpe **-0.08**, sd across seeds 0.26, range -0.48 .. +0.26. The null is centred on zero as it should be;
   note the baseline 0.26 is only ~1.2 sd above it, i.e. not distinguishable from a lucky shuffle.
2. **Features lagged one extra session** (`X.shift(1)`): Sharpe **-0.05**, t -0.21 - the result collapses, so whatever
   signal exists is in the freshest observation. **Positive control**, features from t+1 (`X.shift(-1)`, which
   contains `ret_1d`(t+1) = the label): Sharpe **+8.70**, t 36 - the harness does detect a leak when one is present.
3. **Top features** (ridge |coef| on standardised inputs, share of total, averaged over the 17 yearly fits):
   `gold_ret_1` 2.6 %, `ret_252d` 2.6 %, `h_since_fomc` 2.1 %, `cot_net_pct` 1.9 %, `range_pips` 1.9 %,
   `d_spread2y_5` 1.9 %, `spx_minus_sx5e_20` 1.7 %, `cot_z52` 1.7 %, `donch20_pos` 1.6 %, `d_spread2y_20` 1.6 %,
   `body_rel` 1.5 %, `atr14_pips` 1.5 %, `rv_ratio_5_63` 1.4 %, `gold_ret_5` 1.4 %, `ret_1d` 1.3 %.
   Weights are spread thinly (no feature above 3 %), none is a label in disguise: all are built from data <= the
   session close (macro and cross-asset series lagged one calendar day, COT lagged six days in `featstore.py`).

## Anything suspicious / caveats
* The macro-surprise columns are entirely NaN before 2010 and `cot_lev_z52` before mid-2011, so the first test
  years are fitted with those columns imputed to 0 (ridge) or missing (LightGBM); that cannot leak but it means
  the 2010-2012 fits do not really use the surprise block.
* The 2010-2015 selection window and 2016-2026 disagree strongly on the ranking; selecting by any other
  pre-declared window would have chosen a different variant with an equally unconvincing full-sample record.
* The whole P&L of the final variant is on the short side; a learner picking up the EUR/USD down-drift of
  2014/2018/2022 inside a 30 % activity rule is a plausible explanation and not a tradeable signal.
