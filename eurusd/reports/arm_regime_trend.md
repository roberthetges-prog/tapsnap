# Arm D: regimes and trend ensembles (`regime_trend`)

Code `src/eurusd/arms/regime_trend.py` (`run(cost_pips=1.2)`), positions `experiments/results/arms/regime_trend_positions.parquet`,
all variants `experiments/results/arms/regime_trend_report.csv` (`variant`, `cost_pips`, `diagnostic`, `final` columns),
regime timelines `experiments/results/arms/regime_trend_timeline_<variant>.csv`, per-year regime->action mappings
and state means `experiments/results/arms/regime_trend_mappings.json`, logs `experiments/results/logs/arm_regime_trend*.log`.
Protocol: `eurusd.wf` yearly expanding walk-forward, test years 2010-2026, one decision per NY close earning `fwd_1d`,
positions in [-1, 1], 1.2 pips per unit turnover (0.6 as sensitivity). hmmlearn 0.3.3 was pip-installed for the HMM.

## Idea
The academic claims that still stand for single-asset FX are (a) vol-scaled multi-horizon time-series momentum and
(b) conditioning on regimes. Build both on the daily feature store, apply the regime model to the trend / mean-reversion
signals and to the three weak round-1 components, and add a Moreira-Muir volatility-managed overlay.

## Building blocks (all causal functions of the feature store)
* **TSMOM ensemble**, lookbacks 21/63/126/252 sessions. `tsmom_sign` = mean of sign(ret_k). `tsmom_scaled` = mean of
  clip(t_k / q_k, -1, 1), t_k = ret_k / (rv_21d_bp * sqrt(k)), q_k = training-window 80th percentile of |t_k|.
* **Baz et al. (2015) EWMA crossover**, speeds (8,24), (16,48), (32,96): x = EWMA_S - EWMA_L of the close,
  y = x / std_63(close), z = y / std_252(y), R(z) = z exp(-z^2/4)/0.89, signal = mean of the three R(z).
* `trend_combo` = mean of `tsmom_scaled` and Baz.
* **Mean reversion** `mr` = mean of -(rsi2-50)/s, -z20/s, -fv_resid_z/s (s = training std, each clipped at 2 sd).
* **Round-1 components**: `fomc` = +1 on the session whose forward day contains a scheduled FOMC statement
  (from `fomc_decisions.csv`, 8/yr), `cot` = sign(cot_z52), `spread` = sign(d_spread2y_20), `round1_combo` = their mean.
* **Vol scaling** (`_vs`): position *= clip(target / rv_21d_bp, 0, 1.5), target = training median of rv_21d_bp.
* **Moreira-Muir overlay** (`_mm`): position *= clip(c / rv_21d_bp^2, 0, 2), c = training median of rv_21d_bp^2.

## Regime model
Gaussian HMM (diagonal covariances) on standardized (log rv_21d_bp, |ret_21d|, adx14, log vix), K = 3 (and 4), fitted
on the training rows of each walk-forward year with 4 EM restarts; the kept restart is the best training likelihood
among those whose states are all persistent (self-transition >= 0.8). This guard was added after the first full run
showed EM returning degenerate solutions in 6 of 17 years (two states with identical means flipping daily); with it,
no year is degenerate. State probabilities on every date come from a **causal forward filter** with the training
parameters (never Viterbi or smoothing), so the test-year regime at t uses only features up to t.

The K=3 states are the same every year (standardized means in `regime_trend_mappings.json`):
*calm/range* (rv -0.3, |ret21| -0.5, adx -0.7, vix -0.3), *trend* (rv -0.2, |ret21| +0.4, adx +0.9, vix -0.1) and
*stressed* (rv +1.5..2.0, |ret21| +0.8..1.1, vix +1.7..2.0; from 2017 the stressed state absorbs the trending one: rv +0.6,
adx +0.9, vix +0.9). Self-transitions 0.96-0.99; out of sample the hard regime switches 181 times in 17 years
(mean run 24 sessions). Mean filtered weight (desc mapping): trend 0.32, range 0.45, stressed 0.23.

Mappings chosen on the training window only:
* `desc`: highest stress score (mean z of log rv, log vix) -> flat; among the rest, trendiness (mean z of adx14, |ret_21d|)
  above the average of the non-stressed states -> trend signal, else -> MR signal.
* `perf`: per hard state, training net Sharpe of the trend and of the MR signal; better one if > 0, else flat.
* `gate`: trend everywhere except the stressed state.
* round-1 components: active in state s iff the component's training net Sharpe in s is > 0.
Soft application: pos = sum_s P(s|t) action_s(t); `hard` uses the argmax state.

OOS regime timeline, `regime_K3_desc_soft`, fraction of sessions by hard action:

| year | flat (stressed) | mr (range) | trend |
|---|---|---|---|
| 2010 | 0.17 | 0.23 | 0.61 |
| 2011 | 0.36 | 0.44 | 0.20 |
| 2012 | 0.00 | 0.65 | 0.35 |
| 2013 | 0.00 | 0.53 | 0.47 |
| 2014 | 0.00 | 0.60 | 0.40 |
| 2015 | 0.07 | 0.42 | 0.51 |
| 2016 | 0.03 | 0.53 | 0.44 |
| 2017 | 0.14 | 0.86 | 0.00 |
| 2018 | 0.20 | 0.23 | 0.57 |
| 2019 | 0.00 | 0.87 | 0.13 |
| 2020 | 0.60 | 0.24 | 0.16 |
| 2021 | 0.19 | 0.53 | 0.29 |
| 2022 | 0.46 | 0.15 | 0.38 |
| 2023 | 0.19 | 0.60 | 0.21 |
| 2024 | 0.14 | 0.86 | 0.00 |
| 2025 | 0.22 | 0.41 | 0.37 |
| 2026 | 0.18 | 0.78 | 0.04 |

The `perf` mapping chose "trend" for every state in 10 of 17 years and never found a state where MR beat trend by much;
i.e. on the training windows the regimes did not separate a trend-friendly from a mean-reverting environment.

## Selection rule (declared in the module docstring before results)
Final = the candidate (all variants except the 8 leave-one-out diagnostics) with the highest 2010-2015 walk-forward
net Sharpe at 1.2 pips; its full 2010-2026 record is reported. Nothing was chosen on 2016-2026 or 2023-2026.
**Variants: 34 run (26 candidates + 8 LOO diagnostics).** Deflated-Sharpe p in the csv uses n_trials = 26.

## All variants (net Sharpe at 1.2 pips unless stated)

| variant | SR 2010-15 | SR 2010-26 | SR 2016-26 | SR 2023-26 | t 2010-26 | SR 2010-26 @0.6 |
|---|---|---|---|---|---|---|
| tsmom_sign_vs | 0.38 | 0.11 | -0.06 | -0.18 | 0.46 | 0.13 |
| tsmom_scaled_vs | 0.24 | 0.03 | -0.13 | -0.42 | 0.10 | 0.05 |
| baz_vs | 0.50 | 0.19 | -0.01 | -0.51 | 0.80 | 0.20 |
| trend_combo_vs | 0.39 | 0.12 | -0.06 | -0.48 | 0.52 | 0.14 |
| tsmom_sign_raw (no vol scaling) | 0.27 | 0.05 | -0.10 | -0.17 | 0.22 | 0.08 |
| tsmom_scaled_raw | 0.11 | -0.02 | -0.13 | -0.35 | -0.08 | 0.00 |
| baz_raw | 0.38 | 0.20 | 0.06 | -0.37 | 0.82 | 0.20 |
| mr_vs | -0.27 | -0.10 | 0.01 | 0.14 | -0.40 | -0.01 |
| regime_K3_desc_soft | -0.16 | 0.11 | 0.32 | 0.21 | 0.45 | 0.16 |
| regime_K3_perf_soft | 0.42 | 0.15 | -0.03 | -0.42 | 0.62 | 0.17 |
| regime_K4_desc_soft | -0.70 | -0.59 | -0.52 | -0.89 | -2.46 | -0.53 |
| regime_K4_perf_soft | 0.10 | -0.10 | -0.23 | -0.51 | -0.42 | -0.08 |
| regime_K3_perf_hard | 0.47 | 0.18 | -0.02 | -0.36 | 0.74 | 0.20 |
| regime_K3_gate_trend | 0.39 | 0.20 | 0.06 | -0.52 | 0.83 | 0.21 |
| fomc_uncond | 0.21 | 0.29 | 0.34 | -0.00 | 1.22 | 0.34 |
| fomc_regimeK3 | 0.07 | 0.20 | 0.27 | -0.00 | 0.82 | 0.24 |
| cot_uncond | 0.85 | 0.70 | 0.60 | 0.31 | 2.91 | 0.70 |
| **cot_regimeK3 (final)** | **0.96** | **0.74** | **0.60** | **0.31** | **3.07** | **0.74** |
| spread_uncond | 0.33 | 0.34 | 0.35 | 0.24 | 1.41 | 0.38 |
| spread_regimeK3 | 0.55 | 0.39 | 0.31 | 0.24 | 1.62 | 0.43 |
| round1_combo_uncond | 0.83 | 0.76 | 0.73 | 0.35 | 3.18 | 0.80 |
| round1_combo_regimeK3 | 0.80 | 0.75 | 0.73 | 0.35 | 3.12 | 0.79 |
| trend_combo_vs_mm | 0.53 | 0.15 | -0.06 | -0.53 | 0.64 | 0.16 |
| regime_K3_perf_soft_mm | 0.52 | 0.16 | -0.04 | -0.45 | 0.67 | 0.18 |
| regime_K3_desc_soft_mm | -0.29 | -0.00 | 0.18 | 0.10 | -0.01 | 0.06 |
| round1_combo_regimeK3_mm | 0.87 | 0.73 | 0.67 | 0.28 | 3.02 | 0.77 |
| LOO regime_K3_desc_soft - log_rv (diag) | 0.11 | 0.02 | -0.04 | -0.22 | 0.07 | 0.07 |
| LOO regime_K3_desc_soft - abs_ret21 | -0.33 | -0.09 | 0.09 | -0.30 | -0.37 | -0.05 |
| LOO regime_K3_desc_soft - adx14 | -0.08 | 0.02 | 0.09 | 0.39 | 0.07 | 0.07 |
| LOO regime_K3_desc_soft - log_vix | -0.28 | -0.26 | -0.26 | -0.54 | -1.10 | -0.21 |
| LOO regime_K3_perf_soft - log_rv | 0.03 | -0.22 | -0.37 | -0.48 | -0.90 | -0.19 |
| LOO regime_K3_perf_soft - abs_ret21 | 0.45 | 0.05 | -0.23 | -0.58 | 0.19 | 0.07 |
| LOO regime_K3_perf_soft - adx14 | 0.43 | 0.09 | -0.11 | -0.55 | 0.36 | 0.11 |
| LOO regime_K3_perf_soft - log_vix | 0.38 | -0.02 | -0.29 | -0.27 | -0.07 | 0.00 |

## Final variant: `cot_regimeK3`
Position = sign(cot_z52) x vol scale x (filtered probability of the states in which COT had positive training Sharpe).
The gate was only ever partly closed in 2010 (61 % of sessions off), 2012 (35 %) and 2013 (47 %); from 2014 every state
is "on", so from 2014 the final is identical to `cot_uncond`. Turnover 8 units/yr, so 1.2 vs 0.6 pips changes nothing.

| period | n | SR @1.2 | t @1.2 | mean bp/day | SR @0.6 | t @0.6 |
|---|---|---|---|---|---|---|
| 2010 | 260 | 1.39 | 1.41 | 3.28 | 1.39 | 1.41 |
| 2011 | 260 | 1.34 | 1.36 | 5.00 | 1.34 | 1.36 |
| 2012 | 260 | 1.17 | 1.19 | 2.68 | 1.18 | 1.20 |
| 2013 | 259 | -0.22 | -0.22 | -0.45 | -0.20 | -0.21 |
| 2014 | 258 | 2.23 | 2.26 | 5.44 | 2.24 | 2.27 |
| 2015 | 259 | 0.16 | 0.16 | 0.59 | 0.16 | 0.16 |
| 2016 | 259 | 0.68 | 0.69 | 2.10 | 0.69 | 0.70 |
| 2017 | 259 | 1.92 | 1.94 | 5.43 | 1.92 | 1.94 |
| 2018 | 260 | 0.05 | 0.05 | 0.15 | 0.05 | 0.05 |
| 2019 | 260 | -0.05 | -0.05 | -0.10 | -0.04 | -0.04 |
| 2020 | 260 | 0.83 | 0.84 | 2.19 | 0.83 | 0.85 |
| 2021 | 259 | 0.40 | 0.40 | 0.89 | 0.40 | 0.40 |
| 2022 | 260 | 1.17 | 1.19 | 3.57 | 1.18 | 1.20 |
| 2023 | 258 | 0.11 | 0.12 | 0.33 | 0.12 | 0.12 |
| 2024 | 261 | 0.87 | 0.89 | 2.02 | 0.88 | 0.89 |
| 2025 | 260 | 0.01 | 0.01 | 0.02 | 0.01 | 0.01 |
| 2026 (to Nov 5) | 220 | 0.40 | 0.37 | 0.89 | 0.40 | 0.37 |
| **2010-2026** | 4372 | **0.74** | **3.07** | 2.01 | 0.74 | 3.09 |
| **2016-2026** | 2816 | **0.60** | **2.01** | 1.60 | 0.61 | 2.03 |
| **2023-2026** | 999 | **0.31** | **0.62** | 0.81 | 0.32 | 0.63 |
| 2010-2015 | 1556 | 0.96 | 2.39 | 2.76 | 0.97 | 2.41 |
| 2016-2022 | 1817 | 0.76 | 2.03 | 2.03 | 0.76 | 2.05 |

Deflated-Sharpe p (26 trials) = 0.15. It meets the arm bar (2010-2026 > 0.4, 2016-2026 > 0.3, 2023-2026 >= 0) but
15 of 17 years positive with a 2016-2026 t of 2.0 is modest evidence, and see the caveats below.

## What regimes added, what did not
* **Plain vol-scaled trend is dead on EUR/USD daily data**: all TSMOM / Baz ensembles are SR 0.0-0.2 over 2010-2026,
  about zero over 2016-2026 and -0.2 to -0.5 over 2023-2026. Vol scaling and the Moreira-Muir overlay change Sharpe by
  +-0.05, consistently small. The Baz crossover is the best of the trend measures but is 0.98 correlated with TSMOM.
* **Regimes do not rescue it.** The HMM finds the sensible trend / range / stressed structure every year, but the
  performance-mapped version (K3 perf, SR 0.15 / -0.03 / -0.42) is no better than unconditional trend, and the
  descriptive mapping (trend in trend states, MR in range states, flat in stress) is slightly positive post-2016 only
  because being flat in stress and in MR-land avoids the trend losses; its 2010-2015 is negative and the LOO diagnostics
  flip sign depending on which variable is dropped (drop vix: -0.26; drop adx: +0.02; drop rv: +0.02), i.e. the regime
  signal is not robust. K=4 is clearly worse (-0.59). MR in range regimes loses money (mr_vs -0.10; MR by regime never
  earned a positive training Sharpe in most years).
* **Round-1 components**: regime conditioning is a wash: cot 0.70 -> 0.74 (gate active only 2010-2013), spread 0.34 ->
  0.39, fomc 0.29 -> 0.20, combo 0.76 -> 0.75. The equal-weight round-1 combo (fomc + cot + spread) has the highest t
  (3.18) but was not picked by the 2010-2015 rule; its 2016-2026 SR 0.73 / 2023-2026 0.35 is the most useful number in
  this arm for the lead's stack.
* The only thing that survives is the **COT positioning sign**, which this arm did not invent: it is the round-1
  `cot_trend` component held as a continuous daily vol-scaled exposure instead of with a 2 x ATR stop and 5-day hold.
  Its P&L is 0.60 correlated with the price-trend ensemble (positions 0.58), so it is largely a slow trend proxy that
  happens to work much better than price trend itself (sign(ret_126d) earns SR 0.19 on the same sample).

## Leak checks (final variant, `experiments/results/logs/arm_regime_trend_leak.log`)
1. **Shuffled labels** (fwd_1d permuted, 5 seeds; the permuted labels also feed the training-window regime gating):
   2010-2026 SR -0.08, -0.27, +0.54, -0.08, -0.20 (mean -0.02; the sd of a 4372-day Sharpe is 0.24, seed 2 is a 2.3 sd draw).
2. **Features shifted**: lagged one extra session (stale decision) SR 0.74 -> 0.63 / 0.60 -> 0.50 / 0.31 -> 0.22; the
   signal is weekly, so a one-day delay costs little, as it should. Led one session (deliberately feeding tomorrow's
   features, which would expose a hidden alignment leak) gives 0.66 / 0.55 / 0.20: no jump, because cot_z52 changes only on
   Tuesday closes and the gate is almost always open. The same lead test on the composite MR signal gives SR -8.5 and on
   trend_combo 1.31 (from 0.12), so the pipeline is alignment-sensitive where it should be, and the real run is not leaking.
3. **Features used**: ret_21/63/126/252d, rv_21d_bp, close (EWMAs), rsi2, z20, fv_resid_z, adx14, vix, cot_z52,
   d_spread2y_20, scheduled FOMC statement times. None is a label in disguise; |corr with fwd_1d| <= 0.04 for all. COT:
   report Tuesday, published Friday, used from the following Tuesday's close (the feature store adds 6 days then lags one
   more calendar day; cot_z52 changes on Tuesday closes in 1225 of 1245 changes). The COT edge is unchanged when the
   signal is lagged 1, 5, 10 or 20 further sessions (SR 0.62-0.81), which rules out a timing leak.

## Caveats
* The COT rule (sign of the 52-week z-score) was chosen in round 1 on 2003-2015 among many candidates, so 2010-2015 here
  is not clean; 2016-2022 was round 1's validation and 2023-2026 its holdout. Only the 2016-2026 record (SR 0.60, t 2.0)
  should be treated as evidence, and it was not used for any choice in this arm.
* The COT file is the current CFTC history; whether it equals the as-published values cannot be verified here
  (CFTC revisions are rare).
* The regime model itself is a clean negative: it produces an interpretable, stable regime timeline, but no mapping of
  it to trend / mean-reversion / flat earned money out of sample.
