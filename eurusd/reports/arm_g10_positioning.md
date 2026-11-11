# Arm F: G10 positioning (`g10_positioning`) - does "follow the speculative positioning trend" exist outside EUR?

Code `src/eurusd/arms/g10_positioning.py` (`run(cost_pips=1.2)`; `python -m eurusd.arms.g10_positioning build` re-parses
the CFTC zips and re-fetches prices). Results in `experiments/results/arms/`: `g10_positioning_positions.parquet`
(EUR/USD OOS stream of the final variant: `pos`, `fwd_bp`, `net_bp`), `g10_positioning_report.csv` (every run, columns
`variant`, `group`, `cost_pips`, `diagnostic`, `final`), `g10_positioning_basket.parquet` (multi-currency daily P&L),
`g10_positioning_incremental.csv`, `g10_positioning_leakchecks.csv`, `g10_positioning_diagnostics.json`,
`g10_positioning_all_positions.parquet`, log `logs/g10_positioning.log`.

## Verdict in four lines
1. **The effect does not exist outside EUR.** The identical rule is positive on 2 of 7 other currencies (GBP +0.12,
   MXN +0.12, both t 0.5) and the equal-weight ex-EUR basket is **negative**: net Sharpe -0.38 / -0.58 / -0.62
   (t -1.5 / -1.9 / -1.2) for 2010-26 / 2016-26 / 2023-26. Same picture with TFF leveraged funds and asset managers.
2. **EUR is the outlier, not the typical case**: rank 1 of 8 in 2010-26 and 2016-26, +0.77 against a mean of -0.16 for
   the others (3.8 null standard errors above them). The cross-currency evidence therefore does not support the
   positioning survivor; it leaves it resting on EUR/USD alone, the pair it was mined on.
3. **Cross-sectional versions lose** (long high z / short low z: -0.38 to -0.44, t -1.6 to -1.8).
4. **Dollar-wide positioning adds nothing to EUR/USD** (`usd5`: -0.01 / -0.27 / -1.05; adding it to the live pair of
   streams lowers the combination from 0.64 to 0.37 on 2016-26). The variant picked by the declared rule, `eur_rel` =
   sign(z_EUR - mean z of the five majors), formally passes the round-3 bar (0.87 / 0.68 / 0.40; three-way 0.71 vs
   two-way 0.64 on 2016-26) but is 0.75 correlated with `regime_trend`, its alpha over the two survivors has t 1.1 on
   2016-26, and the same relative rule loses on all five other majors. **I do not recommend adding it.**

## Protocol (written in the module docstring before any result was computed)
Rule, identical to regime_trend `cot_uncond`: z = 52-week z-score of non-commercial net / open interest;
pos = sign(z) x clip(training-median rv_21d / rv_21d, 0, 1.5); yearly expanding walk-forward through `eurusd.wf`
(test years 2010-2026; the training median of volatility is the only fitted number). No parameter was changed for any
currency. Cost: 1.2 pips of the conventional pair per unit turnover (GBPUSD, USDJPY with pip 0.01, USDCHF, AUDUSD,
USDCAD, NZDUSD; USDMXN 30 pips because 1.2 pips of USDMXN is not a real spread) = 0.8-2.2 bp; 2x cost as sensitivity.
Turnover is 7-13 units a year, so costs are irrelevant (2x cost changes Sharpe by 0.01-0.04).

## Data, sources, lags
| data | source | range | lag used |
|---|---|---|---|
| `data/macro/cot_{gbp,jpy,chf,aud,cad,nzd,mxn}_legacy.csv` | CFTC legacy futures-only, `data/raw/cftc/deacot*.zip` | 1999-01-05 .. 2026-11-03 weekly | report date + 6 days, then one calendar day (first used at the close of report date + 7), as `cot_z52` |
| `data/macro/cot_{...}_tff.csv` | CFTC TFF, `fut_fin_txt_*.zip` | 2010-07-20 .. 2026-11-03 (z from mid-2011) | same |
| `data/macro/fred_DEX{USEU,USUK,JPUS,SZUS,USAL,CAUS,USNZ,MXUS}.csv` | Fed H.10 noon NY rates via FRED `fredgraph.csv` | 1971/1993/1999 .. 2026-11-06 | price of the decision day (primary price source, declared in advance) |
| `data/processed/cross/g10fut_<ccy>_D1.parquet` | Yahoo chart API, 6E 6B 6J 6S 6A 6C 6N 6M `=F` | 2000/2001 .. 2026-11-11 | sensitivity only |
| `data/macro/fred_IR3TIB01{EZ,GB,JP,CH,AU,CA,NZ,MX,US}M156N.csv` | FRED 3-month interbank rates (OECD) | .. 2026-01/09 | 45 days; carry sensitivity only |

* Codes verified against the market name in every file (`build_cot` asserts): EUR 099741 "EURO FX", GBP 096742
  "POUND STERLING / BRITISH POUND (STERLING)", JPY 097741 "JAPANESE YEN", CHF 092741 "SWISS FRANC", AUD 232741
  "AUSTRALIAN DOLLAR(S)", CAD 090741 "CANADIAN DOLLAR", NZD 112741 "NEW ZEALAND DOLLAR(S) / NZ DOLLAR", MXN 095741
  "MEXICAN PESO" (exchange suffix IMM in 1999, CME after). My EUR parse equals `cot_eurofx_legacy.csv` / `_tff.csv` row
  for row (asserted), and the EUR z on the feature-store grid equals `cot_z52` (asserted).
* Coverage: 1,453 weekly reports for EUR GBP JPY CAD MXN, 1,451 CHF, 1,426 AUD (gaps only before 2005). NZD has long
  gaps until July 2006 (too few reportable traders) and is continuous afterwards, so it is clean for 2010-2026.
* Quote direction: every return is "foreign currency vs USD" (USD per unit of foreign currency = the futures
  direction; H.10 JPY, CHF, CAD, MXN series are inverted). Checks: (a) FRED H.10 equals the repo's
  `datahub_fx_fed_h10_daily.csv` to 1e-4; (b) H.10 vs Yahoo futures level ratio 0.97-1.08, weekly-return correlation
  0.96-0.98; (c) the weekly change of net/OI is positively correlated with the same week's currency return for all
  eight (0.24-0.43), as it must be if specs chase price and the directions are right; (d) the futures-price run gives the
  same table to +-0.09. All daily moves above 4 % are real events (2008, SNB 2011/2015, Brexit, 2016 election).
* Returns are spot log returns, no carry, exactly as EUR/USD `fwd_1d`. Carry-adjusted sensitivity changes Sharpe by
  at most +0.12 (MXN and JPY in 2023-26; <= 0.03 elsewhere). rv_21d is from daily returns (the EUR/USD store uses hourly realised
  variance); the EUR row below (0.77 / 0.64 / 0.34 on H.10 noon data, daily vol) against the feature-store record
  (0.70 / 0.60 / 0.31) shows the cross-currency pipeline reproduces the known result on independent price data.

## 1. Per currency (legacy non-commercial, net Sharpe at 1.2 pips-equivalent, t in brackets)
| currency | 2010-26 | 2016-26 | 2023-26 | SR 2010-15 | SR 2016-22 | SR 2004-09 (pre-OOS) |
|---|---|---|---|---|---|---|
| **EUR** (reference, H.10 data) | **+0.77 (+3.1)** | **+0.64 (+2.1)** | **+0.34 (+0.7)** | +0.97 | +0.80 | +0.34 |
| GBP | +0.12 (+0.5) | +0.05 (+0.2) | -0.35 (-0.7) | +0.26 | +0.23 | +0.08 |
| JPY | -0.13 (-0.5) | +0.05 (+0.2) | -0.17 (-0.3) | -0.44 | +0.19 | -0.08 |
| CHF | -0.19 (-0.8) | -0.56 (-1.8) | -0.54 (-1.1) | +0.25 | -0.58 | +0.03 |
| AUD | -0.13 (-0.5) | -0.13 (-0.4) | -0.10 (-0.2) | -0.13 | -0.15 | +0.21 |
| CAD | -0.33 (-1.4) | -0.54 (-1.8) | -0.47 (-0.9) | -0.01 | -0.58 | +0.20 |
| NZD | -0.57 (-2.3) | -0.65 (-2.1) | -1.13 (-2.2) | -0.46 | -0.39 | +0.63 |
| MXN | +0.12 (+0.5) | -0.01 (-0.0) | +0.80 (+1.6) | +0.40 | -0.47 | +0.02 |
| **EW basket, 5 majors ex EUR** | **-0.25 (-1.0)** | **-0.43 (-1.4)** | **-0.64 (-1.3)** | -0.02 | -0.32 | |
| **EW basket, 7 ex EUR** | **-0.38 (-1.5)** | **-0.58 (-1.9)** | **-0.62 (-1.2)** | -0.08 | -0.56 | +0.34 (t 0.8) |
| EW basket, 8 incl. EUR | -0.14 (-0.6) | -0.37 (-1.2) | -0.48 (-0.9) | +0.17 | -0.32 | |

2x cost: basket7 -0.41 / -0.62 / -0.66; no currency changes by more than 0.03. Risk-parity weighting: -0.35 / -0.57 /
-0.60. Futures prices: basket7 -0.42 / -0.63 / -0.61. Carry-adjusted: -0.34 / -0.54 / -0.53.
The 2004-09 column (sign rule with an expanding-median vol scale, outside the walk-forward) is mildly positive for the
others (basket t 0.8): the ex-EUR basket went +0.34 (2004-09), -0.08 (2010-15), -0.58 (2016-26), i.e. no stable sign.

Pooled evidence (others = the 7 non-EUR currencies):
| period | positive of 7 | mean SR others | basket7 SR (t) | Stouffer z (indep., upper bound) | EUR SR | EUR rank of 8 | t(EUR - basket7, unit vol) | EUR SR shrunk to the 8-currency mean |
|---|---|---|---|---|---|---|---|---|
| 2010-26 | 2 | -0.16 | -0.38 (-1.5) | -1.7 | +0.77 | 1 | +3.8 | 0.46 |
| 2016-26 | 2 | -0.26 | -0.58 (-1.9) | -2.2 | +0.64 | 1 | +3.2 | 0.25 |
| 2023-26 | 1 | -0.28 | -0.62 (-1.2) | -1.4 | +0.34 | 2 | +1.5 | -0.08 |

TFF trader groups (signal from mid-2011): leveraged funds basket7 -0.37 / -0.50 / -0.79, EUR alone +0.53 / +0.68 / +0.60;
asset managers basket7 -0.41 / -0.73 / -1.77 (t -3.5 in 2023-26), EUR alone +0.25 / +0.58 / +0.10. In every trader
grouping EUR is positive and the rest is zero to negative.

**Answer to (1):** no. Outside EUR the rule has no positive out-of-sample record; the pooled t-stat is -1.5 (2010-26)
and -1.9 (2016-26), i.e. the point estimate is the opposite sign (fading positioning), not significant either
(a sign chosen after the fact with |t| < 2 on a basket; NZD alone is -2.3).
**Answer to (2):** EUR is special in the sample: best of 8 in both long windows and t 3.2-3.8 against the basket. The
other currencies cannot say whether that is a genuine EUR-only effect or the lucky tail of eight draws on a rule that
was selected on EUR. What they do remove is the argument "it is a general property of speculative FX positioning".
A rough empirical-Bayes shrink of the EUR Sharpe toward the 8-currency mean gives 0.46 (2010-26) and 0.25 (2016-26)
instead of 0.77 and 0.64; I would plan with something like 0.25-0.45, not 0.6-0.7.
Is it just trend? Sign(126-day return) with the same vol scaling earns -0.26 / -0.36 / -0.85 on the ex-EUR basket and
+0.25 / +0.06 / -0.48 on EUR; positioning and momentum P&L are 0.3-0.6 correlated in every currency. So outside EUR
positioning behaves like (failed) trend following; on EUR it did much better than price trend.

## 2. Cross-sectional versions (6 majors EUR GBP JPY CHF AUD CAD, each leg vol-scaled)
| variant | 2010-26 | 2016-26 | 2023-26 | SR 2010-15 | SR 2016-22 |
|---|---|---|---|---|---|
| `xs_rank` (long high z, short low z) | -0.38 (-1.6) | -0.43 (-1.4) | -0.37 (-0.7) | -0.33 | -0.46 |
| `xs_demean` sign(z_i - mean z) | -0.02 (-0.1) | -0.31 (-1.0) | -0.08 (-0.2) | +0.34 | -0.42 |
| `xs_top2` (top 2 vs bottom 2) | -0.44 (-1.8) | -0.53 (-1.7) | -0.48 (-0.9) | -0.35 | -0.56 |
| `usd_factor` (all six on sign(mean z)) | +0.29 (+1.2) | +0.18 (+0.6) | -0.47 (-0.9) | +0.48 | +0.56 |

**Answer to (3):** no. Ranking currencies by positioning z loses in every window. The dollar-factor version (trade the
whole basket on the average z) is positive to 2022 and negative since; t 1.2 overall.

## 3. EUR/USD variants (feature-store grid, `fwd_1d`, net at 1.2 pips; 10 variants, cap 12)
| variant | 2010-26 | 2016-26 | 2023-26 | SR 2010-15 (selection) | SR 2016-22 | SR 2010-26 @0.6 / @2.4 |
|---|---|---|---|---|---|---|
| `eur_own` sign(z_EUR) (= regime_trend cot_uncond, reference, not eligible) | +0.70 (+2.9) | +0.60 (+2.0) | +0.31 (+0.6) | +0.85 | +0.76 | 0.70 / 0.69 |
| `usd5` sign(mean z of GBP JPY CHF AUD CAD) | -0.01 (-0.0) | -0.27 (-0.9) | -1.05 (-2.1) | +0.37 | +0.15 | 0.00 / -0.02 |
| `usd6` (adds EUR) | +0.42 (+1.8) | +0.23 (+0.8) | -0.41 (-0.8) | +0.71 | +0.58 | 0.43 / 0.41 |
| `usd7x` (5 + NZD + MXN) | +0.07 (+0.3) | -0.14 (-0.5) | -0.93 (-1.8) | +0.36 | +0.28 | 0.07 / 0.05 |
| **`eur_rel` sign(z_EUR - mean z of the 5) (final)** | **+0.87 (+3.6)** | **+0.68 (+2.3)** | **+0.40 (+0.8)** | **+1.16** | +0.83 | 0.87 / 0.86 |
| `agree` (EUR and usd5 same sign, else flat) | +0.42 (+1.7) | +0.21 (+0.7) | -0.47 (-0.9) | +0.71 | +0.56 | 0.43 / 0.41 |
| `breadth5` mean of sign(z_i) | +0.15 (+0.6) | -0.04 (-0.1) | -0.72 (-1.4) | +0.43 | +0.24 | 0.16 / 0.13 |
| `usd5_notional` (USD-notional aggregate net / OI) | +0.02 (+0.1) | -0.20 (-0.7) | -0.58 (-1.2) | +0.34 | +0.00 | 0.03 / 0.01 |
| `usd5_lev` (TFF leveraged funds) | +0.19 (+0.8) | +0.16 (+0.5) | -0.38 (-0.8) | +0.25 | +0.45 | 0.20 / 0.17 |
| `usd5_am` (TFF asset managers) | +0.02 (+0.1) | -0.29 (-1.0) | -0.78 (-1.6) | +0.56 | -0.02 | 0.03 / 0.01 |

Selection rule (declared): best 2010-2015 walk-forward net Sharpe at 1.2 pips among the nine eligible -> `eur_rel`.
Nothing was chosen on 2016-2026. Deflated-Sharpe p (10 trials) = 0.020.

Final `eur_rel`, per year (net, 1.2 pips; 0.6 and 2.4 pips differ by <= 0.02): 2010 +1.13, 2011 +1.24, 2012 +1.40,
2013 +0.47, 2014 +2.14, 2015 +0.86, 2016 -0.18, 2017 +1.97, 2018 +0.05, 2019 +0.30, 2020 +1.66, 2021 +1.39, 2022 +0.76,
2023 -0.11, 2024 +1.08, 2025 +0.39, 2026 +0.40. Mean 2.5 bp/day; always in the market; 54 sign flips in 17 years.
Hit rates (round-4 reporting; one decision per session): net P&L > 0 on 52.2 % of 4,372 decisions in 2010-26, 51.4 % of
2,816 in 2016-26, 52.1 % of 999 in 2023-26 (correct sign before costs 52.3 / 51.5 / 52.1 %; always-long baseline
49.9 / 49.8 / 49.5 %; `eur_own` 51.8 / 51.1 / 51.2 %).

**Answer to (4):** the dollar-wide signal itself is worthless for EUR/USD: `usd5`, `usd7x`, `usd5_notional`, `breadth5`
and both TFF versions are 0.0-0.2 over 2010-26, negative on 2016-26 (except leveraged funds +0.16) and all negative in
2023-26. Mixing it into the EUR signal (`usd6`, `agree`) only dilutes it. The one construction that beats the EUR-own
signal uses the other currencies with the OPPOSITE sign: EUR positioning relative to the rest.

## 4. Incremental test (`meta.combine(..., "EW")` through `report_combo`)
| combination | 2010-26 SR (t) | 2013-26 | 2016-26 SR (t) | 2023-26 SR (t) |
|---|---|---|---|---|
| EW(weak_signals, regime_trend) | 0.56 (2.35) | 0.62 | 0.64 (2.13) | 0.36 (0.71) |
| **EW(weak_signals, regime_trend, g10_positioning = `eur_rel`)** | **0.67 (2.78)** | **0.74** | **0.71 (2.36)** | **0.39 (0.78)** |
| diagnostic: third arm = `eur_own` (a copy of regime_trend from 2014) | 0.57 | 0.63 | 0.65 | 0.35 |
| diagnostic: third arm = `usd5` | 0.34 | 0.37 | 0.37 | -0.21 |
| diagnostic: third arm = `usd5_lev` | 0.51 | 0.57 | 0.56 | 0.09 |
| diagnostic: third arm = ex-EUR basket P&L stream (basket7; the EW rule admits it only in 2017, where it costs 400 bp) | 0.48 | 0.53 | 0.52 | 0.36 |

Daily-P&L correlation of `eur_rel` with weak_signals 0.26, with regime_trend **0.75** (with `eur_own` 0.79).
OLS alpha of the `eur_rel` stream on the two survivors: +0.84 bp/day, t 1.8 (2010-26); +0.52 bp/day, **t 1.1** (2016-26).

Against the round-3 bar: standalone 2016-26 net Sharpe 0.68 > 0.3: pass. 2023-26 not negative (0.40): pass. Three-way
beats two-way on 2016-26 (0.71 vs 0.64): pass. **Formally the arm passes; substantively I would not add it**, because:
* it is the same bet as the positioning stream already in the combination (0.75 correlated; same sign as `eur_own`
  on 87 % of sessions). Of the +0.07 on 2016-26 about +0.01 is just a heavier weight on positioning (the `eur_own`
  diagnostic) and +0.06 comes from the 13 % of sessions where the two disagree, on which `eur_rel` earns +2.0 bp/day
  with t 1.0 (2010-26) and +0.6 bp/day with t 0.3 (2016-26; 390 sessions). 2023-26 has 50 such sessions.
* the same construction on the other five majors, sign(z_i - mean z of the other five), loses on every one of them
  (GBP -0.16, JPY -0.24, CHF -0.04, AUD -0.07, CAD -0.44; basket -0.43 / -0.65 / -0.30, t -1.8 / -2.1 / -0.6). A relative
  rule that works only on the currency whose absolute rule also works only there is not independent confirmation.
* the selection window 2010-2015 is the window in which the EUR positioning rule itself was mined in round 1, and
  `eur_rel` inherits that through its 0.79 correlation with `eur_own`.

## 5. Leak checks (`g10_positioning_leakchecks.csv`)
| check | EUR/USD `eur_rel` 2010-26 / 2016-26 / 2023-26 | ex-EUR basket7 |
|---|---|---|
| as run | +0.87 / +0.68 / +0.40 | -0.38 / -0.58 / -0.62 |
| (1) shuffled labels, 5 seeds (2010-26) | +0.08, +0.36, -0.01, +0.26, -0.29 (mean +0.08; sd of a 17-year Sharpe 0.24) | +0.26, -0.08, -0.02, -0.57, +0.07 (mean -0.07) |
| (2) signal lagged +1 / +5 / +21 / +63 sessions (2010-26) | 0.82 / 0.75 / 0.78 / 0.32 | -0.28 / -0.24 / -0.19 / -0.22 |
| (2) signal led -1 / -5 sessions | 0.84 / 0.65 | -0.45 / -0.39 |
| (2) signal led -10 / -21 sessions (overlaps the label) | 0.93 / **1.07** (2023-26: 1.27) | +0.43 / **+2.23** |
| stamp +3 d (publication day) / +0 d (report date) | 0.84 / 0.71 | -0.44 / -0.44 |
| stamp -7 d / -28 d (look-ahead control) | 0.85 / 0.94 (2016-26 0.94, 2023-26 1.21) | +0.08 / **+2.33** (t 9.5) |

* The signal is weekly and persistent (3 sign changes a year), so a one-day or one-week shift does not collapse it, as
  for the other slow arms; it decays by +63 sessions. No jump from a 1-5 session lead or from removing the publication
  lag, so there is no timing leak. A lead long enough to overlap the label (>= 10 sessions, or stamping the report 28
  days early) produces a large jump (basket from -0.38 to +2.2/+2.3, t 9), which shows the harness is alignment-
  sensitive and that positioning is strongly contemporaneous with returns: speculators chase the move, and by the time
  the report is tradable nothing is left outside EUR.
* (3) Inputs: CFTC net/OI z-scores (weekly, lagged 7 days) and trailing realised volatility only. Correlation of the
  position sign with `fwd_1d` (2010-26): `eur_rel` 0.053, `eur_own` 0.044, `usd5` -0.002; nothing near a label.
  `eur_own` reproduces regime_trend `cot_uncond` exactly (0.70 / 0.60 / 0.31, t 2.91).
* Selection used 2010-2015 only; no threshold, window or currency set was changed after seeing results.

## Counts
* EUR/USD variants: **10** (9 eligible + the `eur_own` reference), each at 0.6 / 1.2 / 2.4 pips.
* Cross-currency runs of the fixed rule (nothing selected): 8 currencies x 3 trader groups, 9 baskets, 4
  cross-sectional = 37. Diagnostics: 28 in the csv (momentum, futures prices, carry, risk parity), plus 6 relative-rule
  runs, the 2004-09 pre-sample table and the leak checks.

## Caveats
* Spot returns without carry (as for EUR/USD); the carry sensitivity uses monthly OECD 3-month rates and moves nothing.
* H.10 is a noon New York fix; decisions are dated to it. With a weekly signal lagged 7 days the time of day is
  immaterial (futures-settlement prices give the same table).
* CFTC files are the current history, not vintages (revisions are rare). MXN cost is an assumption (30 pips).
* The negative ex-EUR basket should not be read as a new "fade positioning" signal: the sign is chosen after the fact
  and the t-stats are 1.5-1.9 (2004-09 was +0.3).

## What this means for the live EUR/USD exposure
The positioning half of the live exposure is now supported only by its own EUR/USD record (2016-26 t 2.0). It did not
replicate on seven other currencies, in the cross-section, or as a dollar-wide factor. That does not prove the EUR
effect is spurious (EUR is statistically different from the others in the sample), but it removes the generality
argument, and a shrunk expectation of roughly 0.25-0.45 Sharpe is more defensible than the 0.6-0.7 headline. Suggested
action: keep the positioning stream but do not raise its weight, and do not add `eur_rel` or any dollar-wide signal.
