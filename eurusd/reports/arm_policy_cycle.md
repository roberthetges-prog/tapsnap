# Arm T - policy_cycle: central-bank reaction functions, the policy cycle and EUR/USD (round 5)

Code `src/eurusd/arms/policy_cycle.py` (`run(cost_pips=1.2)`; `PYTHONPATH=src python -m eurusd.arms.policy_cycle` runs everything incl. leak checks and this report in under a minute on one core; `... policy_cycle report` rebuilds this file from the saved tables). Outputs in `experiments/results/arms/`: `policy_cycle_positions.parquet` (daily stream of the final signal: `pos`, `fwd_bp`, `net_bp`), `policy_cycle_report.csv` (protocol table, all 10 candidates, `variant`, `final`), `policy_cycle_reaction_accuracy.csv`, `policy_cycle_reaction_confusion.csv`, `policy_cycle_reaction_turning_points.csv`, `policy_cycle_reaction_coefficients.csv`, `policy_cycle_reaction_diagnostics.csv`, `policy_cycle_events.csv` (every turning point, phase spell and joint-state spell with dates and forward returns), `policy_cycle_event_cells.csv`, `policy_cycle_event_drift.csv`, `policy_cycle_votes.csv` (every signal x test x horizon x mode x period, incl. the timing placebo), `policy_cycle_bar.csv` (the Round 5 success test), `policy_cycle_paired_bootstrap.csv`, `policy_cycle_signals.parquet`, `policy_cycle_incremental.csv`, `policy_cycle_leakchecks*.csv`. New data file `data/macro/policy_state.csv` (daily, reproducible from `run()`). Everything in the module docstring (definitions, priors, the 10 candidates, the selection rule, the success test) was written before the first result.

## Verdict

**The owner's idea was tested properly and it does not give a tradeable edge. No candidate meets the Round 5 bar; the arm adds no vote.**
The three questions, in order:

1. **Can we predict what each central bank does from the economy? Not better than "it will keep doing what it has been doing".**
   Out of sample (walk-forward), three classes cut / hold / hike:
   * Next meeting. Fed 1996-2026 (252 meetings; 12 % cuts, 70 % holds, 18 % hikes): ordered logit on the economy + own policy 71 %, "always
     hold" 70 %, "same as the last decision" 77 %, transparent Taylor-type rule 46 %. ECB 2004-2026 (227 meetings; 11 / 79 / 10): 80 % vs 79 %
     vs 76 % vs 49 %. The model equals the base rate.
   * Direction over the next 3 / 6 months. Fed 1990-2026: model 48 % / 45 %, persistence (the trailing direction) 71 % / 63 %, always hold
     54 % / 39 %, Taylor rule 32 % / 32 %. ECB 2004-2026: model 66 % / 45 %, persistence 72 % / 60 %, always hold 61 % / 49 %, Taylor 39 % / 32 %.
     The economy-only part of the model (no own-policy block) is at 34-42 %, below "always hold"; even fitted IN-SAMPLE on the whole history the
     model reaches only 63-74 %. Bundesbank 1975-98 (3-month rate as proxy): model 35 % / 41 %, persistence 52 % / 46 %.
   * **At turning points** (where persistence is wrong by construction). Meetings: first cut after hikes - Fed 1 of 5, ECB 0 of 3; first hike
     after cuts - Fed 1 of 6, ECB 0 of 4; all decisions that differ from the previous one - Fed 47 % (n=59) against 51 % for "always hold", ECB
     48 % (n=54) against 50 %. Month-ends whose 6-month label differs from the trailing direction: Fed 32 % (n=160) against 44 % for "always
     hold", ECB 28 % (n=108) against 43 %. The one place the Fed model looks good - at the last month-end before each first cut / first hike it
     names the 6-month direction in 8 of 12 cases (Taylor rule 7 of 12) - is matched exactly by the 2-year yield alone (8 of 12): by then the
     market knows. And the price of those hits is false alarms: when the ordered logit departs from persistence (227 of 436 months) it is right
     23 % of the time and persistence 58 %. ECB at the same month-ends: 1 of 6 (2-year yield 2 of 5).
   * Why: reaction functions are unstable across regimes (the 1980s disinflation, the zero bound 2009-15 and 2020-21, 2022's inflation - on
     2022-02-28 both the logit and the Taylor rule said "cut"). Forecasting the 6-month change in bp, 2010-26: Fed RMSE 79 bp for the model, 69 bp
     for "no change", 66 bp for the 2-year slope; ECB 58 / 56 / 53. The market slope is the best of a poor lot; the economy adds nothing to it.
   * Data-revision risk (latest-vintage payrolls, production, NFCI) can only flatter the model; it does not change a negative.
2. **What did EUR/USD do around the cycle? Nothing systematic; every cell is small and split.** 1975-2026, forward 3-month return from the day after
   the announcement, mean (up / down episodes): Fed first cut after hikes n=16: +0.2 % (7 / 9); Fed first hike after cuts n=17: -0.1 % (8 / 8);
   ECB / Bundesbank first cut n=10: -0.7 % (6 / 4); first hike n=11: -0.5 % (6 / 5). With true target data only (1999-2026) there are 4-5 episodes
   per cell. The textbook prior (the bank that turns to easing gets the weaker currency) is right in 7 of 16, 8 of 16, 4 of 10 and 6 of 11 cases at
   3 months. The only lopsided cell is BEFORE the event: in the 3 months before a first Fed hike EUR/USD fell in 14 of 17 episodes (mean -3.1 %;
   4 of 5 since 1999) - the dollar moves in anticipation, not afterwards (afterwards 8 up / 8 down). Joint states, 1999-2026, n spells and 3-month
   return from the start of the spell: both hiking n=4, -2.7 % (1 up / 2 down); Fed hiking, ECB on hold n=5, -0.2 % (3 / 2); Fed hiking, ECB cutting
   n=2, +3.5 % (2 / 0); Fed cutting, ECB on hold n=9, +2.4 % (6 / 3); Fed cutting, ECB hiking n=3, -4.7 % (1 / 2); both cutting n=7, +0.8 % (5 / 2);
   both on hold n=16, +0.6 % (9 / 7); Fed on hold, ECB cutting n=12, +1.1 % (8 / 4); Fed on hold, ECB hiking n=6, -1.4 % (3 / 3). With the 1975-98
   proxies: "Fed cutting, ECB on hold" n=19, +3.1 % (15 / 4) is the one cell that leans the way economics says, but the 19 spells come from 11 Fed
   easing cycles (median spell 31 sessions; 9 spells from 4 cycles since 1999), the drift inside the state is +6.9 % a year with t 1.5 (0.3 %, t 0.05 since 1999), and
   the rule built on it (below) is at 49 % in 2010-26. Divergence widening with the Fed tightening: -0.8 % a year (t -0.3) over 1975-2026.
3. **Is there a signal the market has not priced? No.** Ten candidates, priors fixed before any result.
   * The owner's idea in its purest form, `gap_rel` (the economy implies a higher ECB-minus-Fed path than the 2-year yields price): standalone
     50 / 50 / 52 % at 21 / 42 / 63 sessions (non-overlapping, n = 208 / 104 / 69, 2010-26), daily Sharpe +0.02 / -0.19 / -0.29. As an extra vote it
     moves the agreement rule by +2.6 / +0.6 points (2010-26) and +5.2 / +7.7 (2016-26) at 21 / 42 sessions on 4.7 decisions a year, is 10 points WORSE
     at 21 sessions in 2023-26, and the signal made 63 sessions stale "gains" more (+6.1 / +1.6 and +11.7 / +10.5): a regime artefact.
   * Phase rules. `turn63` ("Fed has turned to cutting while the ECB has not => long for 3 months", and its mirror images): 43 % at 21 sessions
     (n=21), 36 % at 42 (n=14); 7 qualifying turns in 2010-26. `phase_rel` (the relatively tightening bank's currency): 50 / 49 / 43 %. `fed_phase`
     49 / 51 / 48 %, `ecb_phase` 51 / 44 / 36 %. As vetoes on the agreement rule they change it by -4.7 to +2.5 points
     (2010-26).
   * The best-looking numbers belong to the MARKET leg, not to the economy: `mkt_rel` (sign of the priced relative path) 54 / 56 / 61 % standalone,
     daily Sharpe +0.30 / +0.33 / +0.11, vote gain +0.8 / +9.7 (2010-26) and +3.4 / +10.8 (2016-26). It fails the bar on three counts: under 3 points
     at 21 sessions in 2010-26, 5.5 / 5.2 decisions a year, and the placebo keeps two thirds of the 42-session gain (+6.6 and +4.6 of +9.7). On
     the weekly grid the same vote is -1.0 points [-8.7, +6.2] at 42 sessions, so the non-overlapping "gain" is which trades the greedy stream
     happened to pick. `gap_fed` (+3.5 / +4.7; +2.0 / +6.7; 5.3 / 5.0 a year) is the same story: at 21 sessions the stale signal gains more
     (+5.2 and +3.9) than the timely one.
   * Coverage extension: when the three old signals do not agree, the new signals are right 35-56 % of the time at 21 sessions (n = 20-170,
     2010-26).
   * Paired weekly difference (block bootstrap): every interval of every candidate at every horizon contains zero.
   * Extra years: in 2006-09 the vote gain at 21 sessions is positive for 9 of 10 candidates (+0.5 to +27 points) but on 7-36 non-overlapping
     decisions each, against an agreement rule that itself has 36; standalone 2004-09 is 44-61 % at 21 sessions for the signals with at least
     25 decisions. Too small to weigh against 2010-26.
   * **Final by the declared rule: `phase_rel`** as a veto (best eligible 2010-15 vote accuracy, 59 %). Full record: gain -4.7 / -2.3 points
     (2010-26), -6.0 / -2.1 (2016-26), -13.6 / -7.5 (2023-26) at 21 / 42 sessions; standalone daily stream net Sharpe **+0.01 / -0.10 / -0.40**
     (2010-26 / 2016-26 / 2023-26), hit rate 49.6 / 48.5 / 46.9 %; three-way combination 0.45 / 0.44 / 0.15 against 0.56 / 0.64 / 0.36 for the
     two live streams (worse), correlation +0.02 / -0.02. **Round 5 bar: not met** (0 of 10 candidates pass the 3-point test, 0 of 10 the
     placebo test). Round 3 bar: not met.

What is worth keeping: `data/macro/policy_state.csv` as CONTEXT for the weekly outlook (phase of each bank, months since the last move, the
2-year slope as the priced path). The model-implied 6-month change is in the file because it was asked for; its out-of-sample error is larger
than "no change", so it should be shown, if at all, as a low-confidence line and never as a call. Leak checks are clean (section 4): shuffled
exchange-rate labels give 50 %, the daily state table rebuilt from data truncated at three dates is identical to the last digit, shuffled
policy labels take the Fed 6-month model from 45 % to 25 %.

## 0. Data, lags, definitions

| series | file | range | publication lag assumed |
|---|---|---|---|
| Fed target | `fred_DFEDTAR`, `fred_DFEDTARL/U`, `fomc_decisions.csv` (meeting dates, target after the mirror ends 2026-09-20) | 1982-09-27 .. 2026-10-28 | announcement day (FOMC date at most one day before the change date) |
| Fed proxy before 1982-10 (event study only) | `fred_FEDFUNDS` monthly | 1954 .. 1982-08 | day after month end |
| ECB key-rate index | `ecb_policy_rates.csv` (MRO changes before 2014-06-11, deposit-rate changes after), `ecb_decisions.csv` | 1999 .. 2026-11-10 | Governing Council date (at most 14 days before the effective date) |
| Bundesbank proxy before 1999 | `fred_IR3TIB01DEM156N` (German 3-month interbank, monthly average) | 1960 .. 1998 | day after month end |
| US CPI, core CPI, unemployment, Sahm gap, payrolls, industrial production, retail sales | `fred_CPIAUCSL`, `CPILFESL`, `UNRATE`, `SAHMREALTIME`, `PAYEMS`, `INDPRO`, `RSAFS` | to 2026-09 | reference-month end + 21 days |
| US core PCE | `fred_PCEPILFE` | to 2026-09 | + 35 days |
| US initial claims / NFCI | `fred_ICSA` / `fred_NFCI` (ends 2026-09-11, then stale > 60 days = missing) | weekly | week end + 5 days |
| VIX, US 2y, euro-area AAA 2y, EONIA / EUR-STR | `fred_VIXCLS`, `fred_DGS2`, `ea_aaa_yield_curve.csv` (2004-09+), `ea_overnight_rates.csv` | daily | same day in `policy_state.csv`; the FX tests read the row of closing date - 1 |
| Euro-area HICP | `fred_CP0000EZ19M086NEST` (index, y/y by differencing; `ea_hicp.csv` is stale after 2025-12 and not used) | 1996-12 .. 2026-09 | + 21 days |
| Euro-area unemployment | `ea_unemployment.csv` | 2000-01 .. 2026-09 | + 35 days |
| German CPI (Bundesbank line) | `fred_DEUCPIALLMINMEI` | 1955 .. 1998 used | + 30 days |
| EUR/USD | synthetic DEM euro 1975-98, H.10 / ECB reference 1999-2002, feature store 2003+ (`arms/swing.load_prices`) | 1975 .. 2026-11-06 | - |

* US reference months 2025-09..2025-11 (shutdown) are not used before 2026-01-31; October 2025 CPI / unemployment are missing in the mirror and yield no observation. Availability dates are forced to be non-decreasing; a value older than 150 days (weekly series 60, daily 10) is missing.
* **Data-revision risk.** The FRED mirrors hold the LATEST vintage. Unemployment rate and CPI are lightly revised (seasonal factors only), `SAHMREALTIME` is a real-time series by construction; payrolls, industrial production and retail sales are revised materially (benchmark revisions of payrolls can move the 12-month growth by 0.3-0.5 points), and the NFCI is re-estimated on the full sample every week, so its history contains information that was not available at the time (the reaction functions are re-run without it in section 5: nothing changes). Euro-area unemployment is revised by 0.1-0.3 points. Revisions favour the fitted models, so the true real-time accuracy of the reaction functions is, if anything, lower than shown; the conclusions below do not depend on a small margin.
* No euro-area activity series (production, surveys) exists in `data/macro/`; the ECB reaction function has inflation, unemployment, VIX, its own policy block and the Fed's stance only. Core HICP is not used because `ea_hicp.csv` stops in 2025-12.
* `data/macro/policy_state.csv` (business days 1990-01-01 .. data end, rebuilt by `run()`): each row is what is known at the END of that date. Columns: `fed_target`, `ecb_deposit_rate`, `ecb_main_refi_rate`, `ecb_key_index` (an index of key-rate CHANGES, not a rate); per bank `*_phase` (hiking / cutting / hold_after_hikes / hold_after_cuts), `*_dir3`, `*_months_since_move`, `*_last_move_pp`; `joint_state`; `*_p_cut_6m / p_hold_6m / p_hike_6m` and `*_model_chg6m_bp` (walk-forward ordered logit; Fed from 1990, ECB from 2004), `*_slope_2y_minus_policy` (pp) and `*_priced_chg6m_bp` (the market model; ECB from 2008), `*_gap_bp` = model - priced, `model_rel_bp`, `priced_rel_bp`, `gap_rel_bp` (ECB minus Fed); `sig_<candidate>` = the signal in force for the session CLOSING on that date (it uses the row of the previous calendar day).
* Phases are causal: a bank is hiking / cutting while its last move in the trend direction is at most 122 days old, then on hold. Turning points = the first move against the trend (cumulative 20 bp; 75 bp for the monthly proxies).

## 1. Can the next policy move be predicted from the economy?

Walk-forward (yearly expanding; a model for year Y sees only rows whose label is known before Y-01-01). `next` = direction of the change from just after one scheduled meeting to just after the next (features as known on the day of the earlier meeting); `m3`, `m6` = direction of the cumulative change over the next 3 / 6 months from each month-end. Accuracy in %, three classes.

**Overall accuracy against the naive baselines**

| bank   | target   | period    | subset   |   n | cut / hold / hike %   |   always hold |   persistence |   same as last move |   Taylor-type rule |   ordered logit |   market slope only |   logit + slope |
|:-------|:---------|:----------|:---------|----:|:----------------------|--------------:|--------------:|--------------------:|-------------------:|----------------:|--------------------:|----------------:|
| fed    | next     | 1996-2026 | all      | 252 | 12 / 70 / 18          |            70 |            77 |                  25 |                 46 |              71 |                     |                 |
| fed    | next     | 2004-2026 | all      | 188 | 10 / 70 / 20          |            70 |            78 |                  26 |                 48 |              71 |                     |                 |
| fed    | next     | 2010-2026 | all      | 140 | 7 / 78 / 15           |            78 |            74 |                  19 |                 47 |              74 |                     |                 |
| fed    | m3       | 1990-2026 | all      | 439 | 22 / 54 / 24          |            54 |            71 |                  37 |                 32 |              48 |                     |                 |
| fed    | m3       | 2004-2026 | all      | 271 | 13 / 59 / 28          |            59 |            76 |                  34 |                 37 |              57 |                     |                 |
| fed    | m3       | 2010-2026 | all      | 199 | 11 / 65 / 24          |            65 |            76 |                  28 |                 28 |              54 |                     |                 |
| fed    | m6       | 1990-2026 | all      | 436 | 31 / 39 / 30          |            39 |            63 |                  44 |                 32 |              45 |                  32 |              45 |
| fed    | m6       | 2004-2026 | all      | 268 | 20 / 47 / 33          |            47 |            69 |                  39 |                 30 |              48 |                  29 |              48 |
| fed    | m6       | 2010-2026 | all      | 196 | 16 / 53 / 31          |            53 |            69 |                  34 |                 19 |              43 |                  25 |              44 |
| ecb    | next     | 2004-2026 | all      | 227 | 11 / 79 / 10          |            79 |            76 |                  18 |                 49 |              80 |                     |                 |
| ecb    | next     | 2010-2026 | all      | 154 | 12 / 79 / 9           |            79 |            79 |                  18 |                 48 |              81 |                     |                 |
| ecb    | m3       | 2004-2026 | all      | 271 | 20 / 61 / 19          |            61 |            72 |                  31 |                 39 |              66 |                     |                 |
| ecb    | m3       | 2010-2026 | all      | 199 | 22 / 64 / 14          |            64 |            69 |                  28 |                 36 |              67 |                     |                 |
| ecb    | m6       | 2004-2026 | all      | 268 | 29 / 49 / 22          |            49 |            60 |                  37 |                 32 |              45 |                  37 |              47 |
| ecb    | m6       | 2010-2026 | all      | 196 | 34 / 50 / 16          |            50 |            59 |                  36 |                 31 |              39 |                  42 |              49 |

**At turning points - meetings (`next`)**: persistence is right by construction on the 'no change' rows and wrong on every 'change' row, so these rows are where a reaction function has to earn its keep.

| bank   | target   | period    | subset                                   |   n | cut / hold / hike %   |   always hold |   persistence |   same as last move |   Taylor-type rule |   ordered logit |
|:-------|:---------|:----------|:-----------------------------------------|----:|:----------------------|--------------:|--------------:|--------------------:|-------------------:|----------------:|
| fed    | next     | 1996-2026 | first cut after hikes                    |   5 | 100 / 0 / 0           |             0 |             0 |                   0 |                  0 |              20 |
| fed    | next     | 1996-2026 | first hike after cuts                    |   6 | 0 / 0 / 100           |             0 |             0 |                   0 |                 17 |              17 |
| fed    | next     | 1996-2026 | first pause (hold after a move)          |  30 | 0 / 100 / 0           |           100 |             0 |                   0 |                 83 |              70 |
| fed    | next     | 1996-2026 | resumption (same direction after a hold) |  18 | 39 / 0 / 61           |             0 |             0 |                 100 |                  6 |              28 |
| fed    | next     | 1996-2026 | any change vs previous decision          |  59 | 20 / 51 / 29          |            51 |             0 |                  31 |                 46 |              47 |
| fed    | next     | 1996-2026 | no change vs previous decision           | 193 | 9 / 76 / 15           |            76 |           100 |                  24 |                 46 |              78 |
| fed    | next     | 2004-2026 | first cut after hikes                    |   3 | 100 / 0 / 0           |             0 |             0 |                   0 |                  0 |               0 |
| fed    | next     | 2004-2026 | first hike after cuts                    |   4 | 0 / 0 / 100           |             0 |             0 |                   0 |                 25 |              25 |
| fed    | next     | 2004-2026 | first pause (hold after a move)          |  21 | 0 / 100 / 0           |           100 |             0 |                   0 |                 86 |              62 |
| fed    | next     | 2004-2026 | resumption (same direction after a hold) |  14 | 36 / 0 / 64           |             0 |             0 |                 100 |                  7 |              29 |
| fed    | next     | 2004-2026 | any change vs previous decision          |  42 | 19 / 50 / 31          |            50 |             0 |                  33 |                 48 |              43 |
| fed    | next     | 2004-2026 | no change vs previous decision           | 146 | 7 / 76 / 17           |            76 |           100 |                  24 |                 49 |              79 |
| fed    | next     | 2010-2026 | first cut after hikes                    |   2 | 100 / 0 / 0           |             0 |             0 |                   0 |                  0 |               0 |
| fed    | next     | 2010-2026 | first hike after cuts                    |   3 | 0 / 0 / 100           |             0 |             0 |                   0 |                  0 |               0 |
| fed    | next     | 2010-2026 | first pause (hold after a move)          |  18 | 0 / 100 / 0           |           100 |             0 |                   0 |                 94 |              67 |
| fed    | next     | 2010-2026 | resumption (same direction after a hold) |  13 | 31 / 0 / 69           |             0 |             0 |                 100 |                  0 |              23 |
| fed    | next     | 2010-2026 | any change vs previous decision          |  36 | 17 / 50 / 33          |            50 |             0 |                  36 |                 47 |              42 |
| fed    | next     | 2010-2026 | no change vs previous decision           | 104 | 4 / 88 / 9            |            88 |           100 |                  12 |                 47 |              86 |
| ecb    | next     | 2004-2026 | first cut after hikes                    |   3 | 100 / 0 / 0           |             0 |             0 |                   0 |                 33 |               0 |
| ecb    | next     | 2004-2026 | first hike after cuts                    |   4 | 0 / 0 / 100           |             0 |             0 |                   0 |                  0 |               0 |
| ecb    | next     | 2004-2026 | first pause (hold after a move)          |  27 | 0 / 100 / 0           |           100 |             0 |                   0 |                 33 |              78 |
| ecb    | next     | 2004-2026 | resumption (same direction after a hold) |  20 | 50 / 0 / 50           |             0 |             0 |                 100 |                 45 |              25 |
| ecb    | next     | 2004-2026 | any change vs previous decision          |  54 | 24 / 50 / 26          |            50 |             0 |                  37 |                 35 |              48 |
| ecb    | next     | 2004-2026 | no change vs previous decision           | 173 | 7 / 88 / 5            |            88 |           100 |                  12 |                 53 |              90 |
| ecb    | next     | 2010-2026 | first cut after hikes                    |   2 | 100 / 0 / 0           |             0 |             0 |                   0 |                  0 |               0 |
| ecb    | next     | 2010-2026 | first hike after cuts                    |   3 | 0 / 0 / 100           |             0 |             0 |                   0 |                  0 |               0 |
| ecb    | next     | 2010-2026 | first pause (hold after a move)          |  16 | 0 / 100 / 0           |           100 |             0 |                   0 |                 50 |             100 |
| ecb    | next     | 2010-2026 | resumption (same direction after a hold) |  11 | 82 / 0 / 18           |             0 |             0 |                 100 |                  9 |               0 |
| ecb    | next     | 2010-2026 | any change vs previous decision          |  32 | 34 / 50 / 16          |            50 |             0 |                  34 |                 28 |              50 |
| ecb    | next     | 2010-2026 | no change vs previous decision           | 122 | 6 / 87 / 7            |            87 |           100 |                  13 |                 53 |              89 |

**At turning points - month-end targets**: rows whose label differs from the trailing 3- / 6-month direction (persistence is wrong on all of them).

| bank   | target   | period    | subset                                    |   n | cut / hold / hike %   |   always hold |   persistence |   same as last move |   Taylor-type rule |   ordered logit |   market slope only |   logit + slope |
|:-------|:---------|:----------|:------------------------------------------|----:|:----------------------|--------------:|--------------:|--------------------:|-------------------:|----------------:|--------------------:|----------------:|
| fed    | m3       | 1990-2026 | label differs from the trailing direction | 129 | 30 / 50 / 20          |            50 |             0 |                  21 |                 38 |              26 |                     |                 |
| fed    | m3       | 2004-2026 | label differs from the trailing direction |  66 | 26 / 48 / 26          |            48 |             0 |                  21 |                 52 |              29 |                     |                 |
| fed    | m3       | 2010-2026 | label differs from the trailing direction |  48 | 23 / 48 / 29          |            48 |             0 |                  23 |                 50 |              17 |                     |                 |
| fed    | m6       | 1990-2026 | label differs from the trailing direction | 160 | 29 / 44 / 28          |            44 |             0 |                  11 |                 41 |              32 |                  33 |              36 |
| fed    | m6       | 2004-2026 | label differs from the trailing direction |  83 | 25 / 45 / 30          |            45 |             0 |                  11 |                 46 |              39 |                  36 |              45 |
| fed    | m6       | 2010-2026 | label differs from the trailing direction |  60 | 25 / 42 / 33          |            42 |             0 |                  15 |                 50 |              35 |                  37 |              43 |
| ecb    | m3       | 2004-2026 | label differs from the trailing direction |  76 | 36 / 45 / 20          |            45 |             0 |                  28 |                 26 |              37 |                     |                 |
| ecb    | m3       | 2010-2026 | label differs from the trailing direction |  61 | 39 / 46 / 15          |            46 |             0 |                  30 |                 26 |              43 |                     |                 |
| ecb    | m6       | 2004-2026 | label differs from the trailing direction | 108 | 33 / 43 / 24          |            43 |             0 |                  20 |                 37 |              28 |                  41 |              35 |
| ecb    | m6       | 2010-2026 | label differs from the trailing direction |  81 | 37 / 42 / 21          |            42 |             0 |                  23 |                 35 |              26 |                  48 |              42 |

**When a model departs from persistence, who is right?** (% of the decisions on which the model's call differs from the persistence call; this is the false-alarm side of the turning-point tables)

| bank   | target   | period    | model   | departs from persistence   | model_right   | persistence_right   | neither_right   |
|:-------|:---------|:----------|:--------|:---------------------------|:--------------|:--------------------|:----------------|
| fed    | next     | 1996-2026 | taylor  | 136 of 252                 | 20            | 77                  | 3               |
| fed    | next     | 2010-2026 | taylor  | 73 of 140                  | 23            | 75                  | 1               |
| fed    | next     | 1996-2026 | ologit  | 71 of 252                  | 39            | 59                  | 1               |
| fed    | next     | 2010-2026 | ologit  | 30 of 140                  | 50            | 50                  | 0               |
| fed    | m3       | 1990-2026 | taylor  | 299 of 439                 | 16            | 73                  | 11              |
| fed    | m3       | 2010-2026 | taylor  | 144 of 199                 | 17            | 83                  | 1               |
| fed    | m3       | 1990-2026 | ologit  | 190 of 439                 | 17            | 70                  | 13              |
| fed    | m3       | 2010-2026 | ologit  | 60 of 199                  | 13            | 85                  | 2               |
| fed    | m6       | 1990-2026 | taylor  | 312 of 436                 | 21            | 65                  | 14              |
| fed    | m6       | 2010-2026 | taylor  | 167 of 196                 | 18            | 77                  | 5               |
| fed    | m6       | 1990-2026 | ologit  | 227 of 436                 | 23            | 58                  | 19              |
| fed    | m6       | 2010-2026 | ologit  | 97 of 196                  | 22            | 74                  | 4               |
| fed    | m6       | 1990-2026 | market  | 298 of 436                 | 18            | 63                  | 19              |
| fed    | m6       | 2010-2026 | market  | 144 of 196                 | 15            | 76                  | 9               |
| ecb    | next     | 2004-2026 | taylor  | 111 of 227                 | 17            | 73                  | 10              |
| ecb    | next     | 2010-2026 | taylor  | 77 of 154                  | 12            | 74                  | 14              |
| ecb    | next     | 2004-2026 | ologit  | 44 of 227                  | 59            | 41                  | 0               |
| ecb    | next     | 2010-2026 | ologit  | 29 of 154                  | 55            | 45                  | 0               |
| ecb    | m3       | 2004-2026 | taylor  | 159 of 271                 | 13            | 69                  | 18              |
| ecb    | m3       | 2010-2026 | taylor  | 125 of 199                 | 13            | 66                  | 21              |
| ecb    | m3       | 2004-2026 | ologit  | 84 of 271                  | 33            | 54                  | 13              |
| ecb    | m3       | 2010-2026 | ologit  | 61 of 199                  | 43            | 49                  | 8               |
| ecb    | m6       | 2004-2026 | taylor  | 190 of 268                 | 21            | 60                  | 19              |
| ecb    | m6       | 2010-2026 | taylor  | 143 of 196                 | 20            | 57                  | 23              |
| ecb    | m6       | 2004-2026 | ologit  | 132 of 268                 | 23            | 53                  | 24              |
| ecb    | m6       | 2010-2026 | ologit  | 108 of 196                 | 19            | 56                  | 25              |
| ecb    | m6       | 2004-2026 | market  | 138 of 220                 | 28            | 59                  | 13              |
| ecb    | m6       | 2010-2026 | market  | 119 of 196                 | 33            | 61                  | 7               |

**The forecast made at the last month-end before each first cut / first hike** (the label is the realised direction over the following 3 / 6 months; 2026 turns have no 6-month label yet). Count of correct calls:

| bank   | target   |   turning points | always_hold   | persistence   | last_move   | taylor   | ologit   | market   | ologit+market   |
|:-------|:---------|-----------------:|:--------------|:--------------|:------------|:---------|:---------|:---------|:----------------|
| ecb    | m3       |                7 | 0/7           | 0/7           | 0/7         | 3/7      | 0/7      |          |                 |
| ecb    | m6       |                6 | 0/6           | 0/6           | 0/6         | 4/6      | 1/6      | 2/5      | 1/5             |
| fed    | m3       |               12 | 0/12          | 0/12          | 0/12        | 5/12     | 6/12     |          |                 |
| fed    | m6       |               12 | 0/12          | 0/12          | 0/12        | 7/12     | 8/12     | 8/12     | 8/12            |

Every turn, 6-month model (probabilities in %):

| bank   | turn       | type                  | forecast date   | realised 6m   | persistence   | Taylor   | ordered logit   |   p_cut |   p_hold |   p_hike | market slope   |
|:-------|:-----------|:----------------------|:----------------|:--------------|:--------------|:---------|:----------------|--------:|---------:|---------:|:---------------|
| fed    | 1994-02-04 | first_hike_after_cuts | 1994-01-31      | hike          | hold          | hike     | cut             |      43 |       21 |       36 | cut            |
| fed    | 1995-07-06 | first_cut_after_hikes | 1995-06-30      | cut           | hike          | hike     | cut             |      62 |       16 |       21 | cut            |
| fed    | 1997-03-25 | first_hike_after_cuts | 1997-02-28      | hike          | hold          | hike     | hike            |      22 |       20 |       58 | cut            |
| fed    | 1998-09-29 | first_cut_after_hikes | 1998-08-31      | cut           | hold          | hike     | hike            |       0 |        1 |       99 | cut            |
| fed    | 1999-06-30 | first_hike_after_cuts | 1999-05-31      | hike          | hold          | hike     | hike            |       6 |       12 |       83 | cut            |
| fed    | 2001-01-03 | first_cut_after_hikes | 2000-12-31      | cut           | hold          | cut      | cut             |      95 |        4 |        2 | cut            |
| fed    | 2004-06-30 | first_hike_after_cuts | 2004-05-31      | hike          | hold          | hike     | hike            |       5 |       10 |       85 | hike           |
| fed    | 2007-09-18 | first_cut_after_hikes | 2007-08-31      | cut           | hold          | hold     | cut             |      87 |        9 |        4 | cut            |
| fed    | 2015-12-16 | first_hike_after_cuts | 2015-11-30      | hike          | hold          | hike     | hike            |       9 |       35 |       56 | hold           |
| fed    | 2019-07-31 | first_cut_after_hikes | 2019-06-30      | cut           | hold          | hold     | hold            |      16 |       47 |       37 | cut            |
| fed    | 2022-03-16 | first_hike_after_cuts | 2022-02-28      | hike          | hold          | cut      | cut             |      63 |       29 |        7 | hike           |
| fed    | 2024-09-18 | first_cut_after_hikes | 2024-08-31      | cut           | hold          | cut      | cut             |      42 |       42 |       16 | cut            |
| fed    | 2026-09-16 | first_hike_after_cuts | 2026-08-31      |               | hold          | hold     | hold            |      29 |       46 |       25 | hike           |
| ecb    | 2005-12-01 | first_hike_after_cuts | 2005-11-30      | hike          | hold          | cut      | hold            |      23 |       69 |        8 |                |
| ecb    | 2008-10-08 | first_cut_after_hikes | 2008-09-30      | cut           | hike          | cut      | cut             |      89 |       10 |        0 | hold           |
| ecb    | 2011-04-07 | first_hike_after_cuts | 2011-03-31      | hike          | hold          | hike     | hold            |      15 |       69 |       16 | hike           |
| ecb    | 2011-11-03 | first_cut_after_hikes | 2011-10-31      | cut           | hike          | cut      | hold            |      27 |       65 |        8 | hold           |
| ecb    | 2022-07-21 | first_hike_after_cuts | 2022-06-30      | hike          | hold          | cut      | hold            |      25 |       63 |       11 | hold           |
| ecb    | 2024-06-06 | first_cut_after_hikes | 2024-05-31      | cut           | hold          | cut      | hold            |       5 |       48 |       47 | cut            |
| ecb    | 2026-06-11 | first_hike_after_cuts | 2026-05-31      |               | hold          | hold     | hold            |      13 |       58 |       30 | hold           |

**Is the reaction function already in the 2-year yield?** RMSE of the realised 6-month change (bp), 2010-2026, rows where a slope exists:

| bank   |   n |   forecast = no change |   ordered logit (economy + own policy) |   market slope only |   both |
|:-------|----:|-----------------------:|---------------------------------------:|--------------------:|-------:|
| fed    | 196 |                   69.3 |                                   78.6 |                66.1 |   77.5 |
| ecb    | 196 |                   55.7 |                                   58.0 |                52.6 |   48.4 |

**Confusion matrices, ordered logit (rows = what happened, columns = what was predicted), longest out-of-sample period**

*fed, next, 1996-2026*

| actual   |   n |   pred_cut |   pred_hold |   pred_hike |
|:---------|----:|-----------:|------------:|------------:|
| cut      |  30 |         14 |          15 |           1 |
| hold     | 177 |         17 |         149 |          11 |
| hike     |  45 |          0 |          29 |          16 |

*fed, m6, 1990-2026*

| actual   |   n |   pred_cut |   pred_hold |   pred_hike |
|:---------|----:|-----------:|------------:|------------:|
| cut      | 133 |         78 |          15 |          40 |
| hold     | 172 |         58 |          29 |          85 |
| hike     | 131 |         30 |          11 |          90 |

*ecb, next, 2004-2026*

| actual   |   n |   pred_cut |   pred_hold |   pred_hike |
|:---------|----:|-----------:|------------:|------------:|
| cut      |  25 |          5 |          20 |           0 |
| hold     | 179 |          3 |         169 |           7 |
| hike     |  23 |          0 |          16 |           7 |

*ecb, m6, 2004-2026*

| actual   |   n |   pred_cut |   pred_hold |   pred_hike |
|:---------|----:|-----------:|------------:|------------:|
| cut      |  79 |         21 |          42 |          16 |
| hold     | 130 |         18 |          67 |          45 |
| hike     |  59 |         10 |          17 |          32 |

**Bundesbank robustness line** (German 3-month rate as the policy proxy, +-25 bp dead band, test years 1975-1998):

| bank                                    | target   | period    | subset                                    |   n | cut / hold / hike %   |   always hold |   persistence |   same as last move |   Taylor-type rule |   ordered logit | market slope only   | logit + slope   |
|:----------------------------------------|:---------|:----------|:------------------------------------------|----:|:----------------------|--------------:|--------------:|--------------------:|-------------------:|----------------:|:--------------------|:----------------|
| bundesbank (3m rate proxy, +-25bp band) | m3       | 1975-1998 | all                                       | 285 | 35 / 42 / 24          |            42 |            52 |                  36 |                 36 |              35 |                     |                 |
| bundesbank (3m rate proxy, +-25bp band) | m3       | 1975-1998 | label differs from the trailing direction | 137 | 34 / 40 / 26          |            40 |             0 |                  26 |                 33 |              28 |                     |                 |
| bundesbank (3m rate proxy, +-25bp band) | m6       | 1975-1998 | all                                       | 282 | 40 / 31 / 29          |            31 |            46 |                  42 |                 34 |              41 |                     |                 |
| bundesbank (3m rate proxy, +-25bp band) | m6       | 1975-1998 | label differs from the trailing direction | 152 | 29 / 39 / 32          |            39 |             0 |                  19 |                 34 |              38 |                     |                 |

**Diagnostics added after the first run of this part** (nothing selected from them, no signal uses them): which block carries the model?

| variant (accuracy %, all out-of-sample months)    |   fed m3 |   fed m6 |   ecb m3 |   ecb m6 |
|:--------------------------------------------------|---------:|---------:|---------:|---------:|
| n                                                 |      439 |      436 |      271 |      268 |
| always_hold                                       |       54 |       39 |       61 |       49 |
| persistence                                       |       71 |       63 |       72 |       60 |
| ologit (declared: all predictors, penalty 0.02)   |       48 |       45 |       66 |       45 |
| own-policy block only                             |       56 |       48 |       71 |       54 |
| economy and markets only (no own-policy block)    |       36 |       38 |       42 |       34 |
| all + trailing-direction signs                    |       52 |       45 |       68 |       48 |
| trailing-direction signs only                     |       63 |       54 |       73 |       56 |
| all predictors, penalty 0.2                       |       53 |       42 |       73 |       48 |
| all predictors, penalty 1.0                       |       53 |       42 |       68 |       47 |
| IN-SAMPLE fit on the whole history (ceiling)      |       67 |       66 |       74 |       63 |

**Largest standardised coefficients of the last fit (2026), ordered logit**; `corr` = full-sample correlation of the standardised feature with the label (leak check 3: the largest is the bank's own recent change, i.e. persistence; nothing is a label in disguise).

| bank   | target   | top features (coef, corr)                                                                                                                           |
|:-------|:---------|:----------------------------------------------------------------------------------------------------------------------------------------------------|
| ecb    | m3       | own_chg3 (+0.67, +0.58); own_dir (+0.51, +0.44); fed_dir3 (+0.51, +0.45); own_dir3 (+0.40, +0.55); hicp_d3 (+0.38, +0.16); vix_d63 (-0.35, -0.11)   |
| ecb    | m6       | own_chg3 (+0.70, +0.50); fed_dir3 (+0.55, +0.45); fed_chg6 (+0.50, +0.45); u_gap (-0.42, -0.24); hicp_d3 (+0.41, +0.19); vix_d63 (-0.36, -0.07)     |
| ecb    | next     | vix_d63 (-0.56, -0.21); fed_dir3 (+0.54, +0.38); own_dir3 (+0.36, +0.41); own_dir (+0.32, +0.34); own_chg3 (+0.29, +0.50); own_real (-0.28, -0.21)  |
| fed    | m3       | own_dir3 (+0.79, +0.54); own_real (-0.66, -0.14); pay12 (+0.45, +0.20); nfci_d13 (-0.41, -0.04); own_chg3 (+0.38, +0.45); own_msince (-0.38, +0.01) |
| fed    | m6       | own_dir3 (+0.74, +0.49); own_real (-0.73, -0.21); own_msince (-0.44, +0.06); pay12 (+0.42, +0.17); rs12 (+0.39, +0.23); core (-0.38, -0.10)         |
| fed    | next     | own_dir3 (+0.70, +0.61); own_real (-0.60, -0.18); own_chg3 (+0.51, +0.60); pay12 (+0.48, +0.23); own_chg6 (+0.45, +0.59); core (-0.37, -0.07)       |

## 2. What did EUR/USD do around the policy cycle?

Returns in % (log x 100) of EUR/USD, entry at the first close at least one calendar day after the announcement; `3m before` = the 63 sessions ending at the last close before it. Cells: mean (count of positive / negative episodes). **n is the number of episodes; with n of 4-17 a mean of +-2 % is noise** (one 63-session return has a standard deviation of about 5 %, so the standard error of a mean over 10 episodes is 1.6 %).

**Every turning point since 1975** (`proxy` = monthly market-rate proxy: Fed before 1982-10, Bundesbank before 1999; confirmed only when the counter-move reaches 75 bp, so dated late; `ecb` before 1999 = Bundesbank):

| bank   | turn                  | announced   | policy series   | price     | other bank then   |   3m before |   day of |   +1m |   +3m |   +6m |   +12m |
|:-------|:----------------------|:------------|:----------------|:----------|:------------------|------------:|---------:|------:|------:|------:|-------:|
| fed    | first_hike_after_cuts | 1975-08-01  | proxy           | synth_dem | cutting           |        -8.1 |      0.2 |  -0.2 |   0.6 |  -0.2 |    1.2 |
| fed    | first_cut_after_hikes | 1975-12-01  | proxy           | synth_dem | cutting           |        -1.4 |      0.3 |  -0.2 |   0.8 |   0.7 |    8.1 |
| fed    | first_hike_after_cuts | 1977-09-01  | proxy           | synth_dem | hold_after_hikes  |         0.0 |      0.3 |   2.2 |   7.2 |  12.8 |   16.3 |
| fed    | first_cut_after_hikes | 1980-06-01  | proxy           | synth_dem | hiking            |         0.5 |     -0.3 |   0.8 |  -1.0 |  -8.9 |  -30.7 |
| fed    | first_hike_after_cuts | 1980-10-01  | proxy           | synth_dem | cutting           |        -2.7 |      0.0 |  -5.8 |  -7.3 | -16.2 |  -21.6 |
| fed    | first_cut_after_hikes | 1981-03-01  | proxy           | synth_dem | hiking            |       -11.2 |     -1.1 |   2.3 |  -7.6 | -13.2 |   -9.9 |
| fed    | first_hike_after_cuts | 1981-05-01  | proxy           | synth_dem | hiking            |        -5.5 |     -1.6 |  -5.3 |  -9.6 |  -0.3 |   -3.3 |
| fed    | first_cut_after_hikes | 1981-09-01  | proxy           | synth_dem | hold_after_hikes  |        -2.7 |      0.3 |   7.0 |   8.5 |   3.1 |   -2.0 |
| fed    | first_hike_after_cuts | 1982-02-01  | proxy           | synth_dem | cutting           |        -0.4 |     -0.7 |  -0.8 |  -0.2 |  -4.5 |   -6.1 |
| fed    | first_cut_after_hikes | 1982-07-01  | proxy           | synth_dem | cutting           |        -1.7 |     -0.7 |   1.7 |  -1.2 |   4.8 |   -2.6 |
| fed    | first_hike_after_cuts | 1983-05-25  | target          | synth_dem | cutting           |        -3.0 |     -0.4 |  -1.7 |  -5.5 |  -8.1 |   -9.2 |
| fed    | first_cut_after_hikes | 1984-09-20  | target          | synth_dem | hiking            |       -10.8 |      0.9 |   0.8 |  -2.0 |  -0.3 |   13.7 |
| fed    | first_hike_after_cuts | 1985-02-14  | target          | synth_dem | hiking            |       -11.3 |      0.9 |   0.0 |   6.1 |  17.3 |   34.9 |
| fed    | first_cut_after_hikes | 1985-04-25  | target          | synth_dem | hiking            |         1.8 |     -0.1 |   0.5 |   8.8 |  16.0 |   35.8 |
| fed    | first_hike_after_cuts | 1985-09-06  | target          | synth_dem | cutting           |         6.6 |     -2.9 |  10.5 |  14.9 |  24.7 |   35.3 |
| fed    | first_cut_after_hikes | 1985-12-18  | target          | synth_dem | cutting           |        13.6 |     -0.3 |   2.6 |   9.6 |  11.4 |   24.1 |
| fed    | first_hike_after_cuts | 1987-04-30  | target          | synth_dem | cutting           |        -0.2 |      0.7 |  -1.1 |  -3.5 |   2.8 |    5.5 |
| fed    | first_cut_after_hikes | 1987-11-04  | target          | synth_dem | hiking            |         8.6 |      2.9 |   0.3 |  -1.7 |  -1.1 |   -6.4 |
| fed    | first_hike_after_cuts | 1988-03-30  | target          | synth_dem | cutting           |        -4.2 |      0.5 |  -1.4 |  -9.7 | -12.2 |  -12.7 |
| fed    | first_cut_after_hikes | 1989-06-06  | target          | synth_dem | hiking            |        -6.0 |      0.0 |   4.3 |  -0.5 |  10.4 |   14.9 |
| fed    | first_hike_after_cuts | 1994-02-04  | target          | synth_dem | cutting           |        -2.6 |     -1.2 |   2.8 |   5.4 |  10.7 |   13.8 |
| fed    | first_cut_after_hikes | 1995-07-06  | target          | synth_dem | cutting           |        -0.5 |     -0.7 |  -0.8 |  -2.5 |  -3.4 |   -9.2 |
| fed    | first_hike_after_cuts | 1997-03-25  | target          | synth_dem | hold_after_cuts   |        -7.9 |     -0.3 |  -1.3 |  -2.0 |  -6.0 |   -7.6 |
| fed    | first_cut_after_hikes | 1998-09-29  | target          | synth_dem | hold_after_cuts   |         7.0 |      0.7 |   0.6 |   0.8 |  -8.3 |  -11.3 |
| fed    | first_hike_after_cuts | 1999-06-30  | target          | h10       | cutting           |        -4.2 |     -1.0 |   4.4 |   2.6 |  -1.1 |   -6.2 |
| fed    | first_cut_after_hikes | 2001-01-03  | target          | h10       | hiking            |         8.0 |     -0.2 |  -1.0 |  -5.6 | -10.9 |   -7.4 |
| fed    | first_hike_after_cuts | 2004-06-30  | target          | histdata  | hold_after_cuts   |        -2.3 |      0.6 |  -1.1 |   1.4 |  10.7 |   -1.0 |
| fed    | first_cut_after_hikes | 2007-09-18  | target          | histdata  | hiking            |         3.4 |      0.8 |   2.3 |   3.1 |  11.9 |    1.0 |
| fed    | first_hike_after_cuts | 2015-12-16  | target          | histdata  | cutting           |        -4.4 |     -0.9 |   0.7 |   4.4 |   3.5 |   -0.7 |
| fed    | first_cut_after_hikes | 2019-07-31  | target          | histdata  | hold_after_cuts   |        -0.2 |     -0.6 |  -0.9 |   0.3 |  -0.6 |    4.0 |
| fed    | first_hike_after_cuts | 2022-03-16  | target          | histdata  | hold_after_cuts   |        -3.3 |      1.2 |  -2.6 |  -6.3 | -10.0 |   -3.8 |
| fed    | first_cut_after_hikes | 2024-09-18  | target          | histdata  | cutting           |         3.7 |      0.4 |  -2.7 |  -6.2 |  -2.2 |    4.8 |
| fed    | first_hike_after_cuts | 2026-09-16  | target          | histdata  | hiking            |         0.7 |     -0.6 |  -2.1 | nan   | nan   |  nan   |
| ecb    | first_hike_after_cuts | 1976-08-01  | proxy           | synth_dem | cutting           |        -0.9 |      0.5 |   1.0 |   5.0 |   5.2 |   10.3 |
| ecb    | first_cut_after_hikes | 1978-01-01  | proxy           | synth_dem | hiking            |        10.0 |      0.3 |  -0.1 |   3.3 |   1.0 |   12.7 |
| ecb    | first_hike_after_cuts | 1979-05-01  | proxy           | synth_dem | hiking            |        -1.9 |     -0.0 |  -2.2 |   3.5 |   4.8 |    4.9 |
| ecb    | first_cut_after_hikes | 1980-09-01  | proxy           | synth_dem | cutting           |        -1.0 |      0.8 |  -1.5 |  -8.8 | -17.7 |  -31.0 |
| ecb    | first_hike_after_cuts | 1981-01-01  | proxy           | synth_dem | hiking            |        -8.1 |     -0.9 |  -6.9 |  -7.3 | -19.9 |  -13.4 |
| ecb    | first_cut_after_hikes | 1981-10-01  | proxy           | synth_dem | cutting           |         4.6 |      1.6 |   2.2 |   0.0 |  -7.2 |  -11.3 |
| ecb    | first_hike_after_cuts | 1983-11-01  | proxy           | synth_dem | hiking            |         1.9 |     -0.5 |  -3.3 |  -3.6 |  -4.4 |  -10.5 |
| ecb    | first_cut_after_hikes | 1985-08-01  | proxy           | synth_dem | cutting           |        12.3 |     -0.9 |  -1.3 |   7.5 |  16.4 |   29.9 |
| ecb    | first_hike_after_cuts | 1987-11-01  | proxy           | synth_dem | hiking            |         6.4 |      1.0 |   3.1 |   1.7 |   1.8 |   -3.6 |
| ecb    | first_cut_after_hikes | 1987-12-01  | proxy           | synth_dem | cutting           |        10.1 |     -0.6 |   3.8 |  -2.2 |  -4.3 |   -4.6 |
| ecb    | first_hike_after_cuts | 1988-08-01  | proxy           | synth_dem | hiking            |       -10.4 |     -0.1 |  -0.8 |   4.4 |  -0.8 |    0.1 |
| ecb    | first_cut_after_hikes | 1992-11-01  | proxy           | synth_dem | cutting           |        -4.0 |     -1.6 |  -1.8 |  -5.7 |  -1.2 |   -7.8 |
| ecb    | first_hike_after_cuts | 1999-11-04  | target          | h10       | hiking            |        -2.7 |     -0.8 |  -1.4 |  -6.3 | -13.1 |  -21.8 |
| ecb    | first_cut_after_hikes | 2001-05-10  | target          | h10       | cutting           |        -4.7 |     -1.0 |  -3.9 |   0.2 |   2.3 |    3.1 |
| ecb    | first_hike_after_cuts | 2005-12-01  | target          | histdata  | hiking            |        -6.2 |     -0.6 |   3.3 |   2.5 |   8.9 |   11.1 |
| ecb    | first_cut_after_hikes | 2008-10-08  | target          | histdata  | cutting           |       -14.8 |     -0.1 |  -6.7 |   0.8 |  -2.5 |    7.3 |
| ecb    | first_hike_after_cuts | 2011-04-07  | target          | histdata  | hold_after_cuts   |        10.5 |      1.1 |  -0.9 |  -1.2 |  -9.3 |   -8.4 |
| ecb    | first_cut_after_hikes | 2011-11-03  | target          | histdata  | hold_after_cuts   |        -3.8 |      0.3 |  -2.9 |  -4.7 |  -4.1 |   -6.0 |
| ecb    | first_hike_after_cuts | 2022-07-21  | target          | histdata  | hiking            |        -5.9 |      0.3 |  -2.7 |  -4.4 |   5.8 |    8.6 |
| ecb    | first_cut_after_hikes | 2024-06-06  | target          | histdata  | hold_after_hikes  |        -0.6 |     -0.6 |   0.2 |   2.6 |  -2.9 |    4.5 |
| ecb    | first_hike_after_cuts | 2026-06-11  | target          | histdata  | hold_after_cuts   |         1.0 |      0.3 |  -1.6 |   0.6 | nan   |  nan   |

**Turning points, 1999-2026** (prior: the bank that turns to easing has the weaker currency; `prior sign right` counts episodes moving that way):

| bank   | state / event         |   n episodes | 3m before    | +1m          | +3m          | +6m          | +12m         | prior sign right +3m   | prior sign right +6m   |
|:-------|:----------------------|-------------:|:-------------|:-------------|:-------------|:-------------|:-------------|:-----------------------|:-----------------------|
| ecb    | first_cut_after_hikes |            4 | -6.0 (0+/4-) | -3.3 (1+/3-) | -0.3 (3+/1-) | -1.8 (1+/3-) | +2.2 (3+/1-) | 1/4                    | 3/4                    |
| ecb    | first_hike_after_cuts |            5 | -0.6 (2+/3-) | -0.7 (1+/4-) | -1.7 (2+/3-) | -1.9 (2+/2-) | -2.6 (2+/2-) | 2/5                    | 2/4                    |
| fed    | first_cut_after_hikes |            4 | +3.7 (3+/1-) | -0.6 (1+/3-) | -2.1 (2+/2-) | -0.4 (1+/3-) | +0.6 (3+/1-) | 2/4                    | 1/4                    |
| fed    | first_hike_after_cuts |            5 | -2.7 (1+/4-) | -0.1 (2+/3-) | +0.5 (3+/1-) | +0.8 (2+/2-) | -2.9 (0+/4-) | 1/4                    | 2/4                    |

**Turning points, 1975-2026** (prior: the bank that turns to easing has the weaker currency; `prior sign right` counts episodes moving that way):

| bank   | state / event         |   n episodes | 3m before     | +1m           | +3m          | +6m          | +12m          | prior sign right +3m   | prior sign right +6m   |
|:-------|:----------------------|-------------:|:--------------|:--------------|:-------------|:-------------|:--------------|:-----------------------|:-----------------------|
| ecb    | first_cut_after_hikes |           10 | +0.8 (4+/6-)  | -1.2 (3+/7-)  | -0.7 (6+/4-) | -2.0 (3+/7-) | -0.3 (5+/5-)  | 4/10                   | 7/10                   |
| ecb    | first_hike_after_cuts |           11 | -1.5 (4+/7-)  | -1.1 (3+/8-)  | -0.5 (6+/5-) | -2.1 (5+/5-) | -2.3 (5+/5-)  | 6/11                   | 5/10                   |
| fed    | first_cut_after_hikes |           16 | +0.8 (8+/8-)  | +1.1 (11+/5-) | +0.2 (7+/9-) | +0.6 (7+/9-) | +1.7 (8+/8-)  | 7/16                   | 7/16                   |
| fed    | first_hike_after_cuts |           17 | -3.1 (3+/14-) | -0.2 (6+/11-) | -0.1 (8+/8-) | +1.5 (7+/9-) | +2.2 (6+/10-) | 8/16                   | 9/16                   |

**Pause confirmed (122 days after the last move), 1975-2026:**

| bank   | state / event     |   n episodes | 3m before      | +1m            | +3m            | +6m            | +12m           |
|:-------|:------------------|-------------:|:---------------|:---------------|:---------------|:---------------|:---------------|
| ecb    | pause_after_cuts  |           26 | -0.0 (14+/12-) | -0.3 (14+/12-) | +0.8 (15+/11-) | +1.6 (15+/11-) | -0.2 (12+/14-) |
| ecb    | pause_after_hikes |           11 | -1.0 (6+/5-)   | +0.5 (7+/4-)   | +1.1 (6+/5-)   | +1.3 (6+/5-)   | -1.8 (6+/5-)   |
| fed    | pause_after_cuts  |           18 | -0.4 (8+/10-)  | +0.5 (9+/9-)   | +1.6 (12+/6-)  | +1.7 (11+/7-)  | +2.5 (10+/7-)  |
| fed    | pause_after_hikes |           10 | -1.6 (4+/6-)   | +0.4 (5+/5-)   | +1.7 (7+/3-)   | +1.8 (6+/4-)   | -1.0 (4+/6-)   |

**Phases of each bank, 1999-2026** (forward returns from the first session of each spell):

| bank   | state / event    |   n episodes |   median length (sessions) | +1m          | +3m          | +6m          | +12m         | over the spell   |
|:-------|:-----------------|-------------:|---------------------------:|:-------------|:-------------|:-------------|:-------------|:-----------------|
| ecb    | cutting          |           12 |                        131 | -0.6 (5+/7-) | +0.7 (9+/3-) | +1.5 (7+/5-) | +0.2 (7+/5-) | +1.7 (8+/3-)     |
| ecb    | hiking           |            6 |                        237 | -0.7 (1+/5-) | -3.4 (2+/4-) | -3.8 (2+/3-) | -4.4 (2+/3-) | -1.6 (2+/4-)     |
| ecb    | hold_after_cuts  |           12 |                        185 | -0.5 (5+/7-) | +0.6 (7+/5-) | -1.0 (5+/7-) | -1.3 (6+/6-) | -1.0 (4+/8-)     |
| ecb    | hold_after_hikes |            3 |                        103 | +0.6 (1+/2-) | -0.6 (1+/2-) | +1.6 (1+/2-) | -3.1 (1+/2-) | +1.5 (1+/2-)     |
| fed    | cutting          |            9 |                        146 | -1.3 (2+/7-) | +0.1 (5+/4-) | +2.3 (4+/5-) | +4.0 (7+/2-) | +1.1 (6+/3-)     |
| fed    | hiking           |            7 |                        317 | +0.7 (4+/3-) | +1.6 (5+/1-) | +1.7 (3+/3-) | -0.4 (1+/5-) | -0.8 (3+/4-)     |
| fed    | hold_after_cuts  |           10 |                        110 | -0.0 (4+/6-) | +1.6 (6+/4-) | +1.7 (7+/3-) | +4.3 (7+/2-) | -1.4 (4+/6-)     |
| fed    | hold_after_hikes |            6 |                        124 | +0.6 (3+/3-) | +1.1 (4+/2-) | +1.9 (3+/3-) | +0.2 (2+/4-) | +1.9 (3+/3-)     |

**Phases of each bank, 1975-2026** (forward returns from the first session of each spell):

| bank   | state / event    |   n episodes |   median length (sessions) | +1m            | +3m            | +6m            | +12m           | over the spell   |
|:-------|:-----------------|-------------:|---------------------------:|:---------------|:---------------|:---------------|:---------------|:-----------------|
| ecb    | cutting          |           27 |                        112 | +0.3 (14+/13-) | +0.9 (18+/9-)  | +0.6 (14+/13-) | +0.6 (15+/12-) | +0.0 (15+/11-)   |
| ecb    | hiking           |           16 |                        176 | -0.9 (5+/11-)  | -1.3 (8+/8-)   | -3.0 (7+/8-)   | -1.5 (7+/8-)   | -1.0 (8+/8-)     |
| ecb    | hold_after_cuts  |           25 |                         63 | -0.3 (13+/12-) | +1.0 (15+/10-) | +1.6 (14+/11-) | +0.2 (12+/13-) | +0.3 (12+/13-)   |
| ecb    | hold_after_hikes |           10 |                         65 | +0.7 (7+/3-)   | +2.1 (6+/4-)   | +3.2 (6+/4-)   | +1.1 (6+/4-)   | +3.8 (8+/2-)     |
| fed    | cutting          |           25 |                        128 | +0.5 (15+/10-) | +1.0 (13+/12-) | +1.5 (12+/13-) | +1.9 (13+/12-) | +1.4 (15+/10-)   |
| fed    | hiking           |           21 |                        131 | +0.1 (9+/12-)  | +0.2 (11+/9-)  | +1.2 (9+/11-)  | +1.6 (8+/12-)  | -0.6 (9+/12-)    |
| fed    | hold_after_cuts  |           18 |                         86 | +0.5 (9+/9-)   | +1.6 (12+/6-)  | +1.7 (11+/7-)  | +2.5 (10+/7-)  | -1.1 (8+/10-)    |
| fed    | hold_after_hikes |           10 |                         75 | +0.4 (5+/5-)   | +1.7 (7+/3-)   | +1.8 (6+/4-)   | -1.0 (4+/6-)   | +2.7 (6+/4-)     |

**Joint states (Fed x ECB; hiking / hold / cutting), 1999-2026:**

| bank      | state / event           |   n episodes |   median length (sessions) | +1m          | +3m          | +6m          | +12m         | over the spell   |
|:----------|:------------------------|-------------:|---------------------------:|:-------------|:-------------|:-------------|:-------------|:-----------------|
| fed x ecb | fed_cutting|ecb_cutting |            7 |                         86 | -1.4 (2+/5-) | +0.8 (5+/2-) | +2.9 (4+/3-) | +6.4 (6+/1-) | +1.4 (4+/2-)     |
| fed x ecb | fed_cutting|ecb_hiking  |            3 |                         23 | +0.1 (1+/2-) | -4.7 (1+/2-) | -3.4 (1+/2-) | -6.0 (1+/2-) | -2.8 (1+/2-)     |
| fed x ecb | fed_cutting|ecb_hold    |            9 |                         34 | -0.7 (2+/7-) | +2.4 (6+/3-) | +4.4 (6+/3-) | +6.1 (7+/2-) | +1.0 (5+/4-)     |
| fed x ecb | fed_hiking|ecb_cutting  |            2 |                         56 | +2.6 (2+/0-) | +3.5 (2+/0-) | +1.2 (1+/1-) | -3.4 (0+/2-) | +4.7 (2+/0-)     |
| fed x ecb | fed_hiking|ecb_hiking   |            4 |                        230 | -0.7 (1+/3-) | -2.7 (1+/2-) | +0.5 (2+/1-) | -0.7 (2+/1-) | -1.8 (2+/2-)     |
| fed x ecb | fed_hiking|ecb_hold     |            5 |                        216 | +0.1 (2+/3-) | -0.2 (3+/2-) | -0.4 (2+/3-) | -2.0 (1+/4-) | -1.5 (1+/4-)     |
| fed x ecb | fed_hold|ecb_cutting    |           12 |                         86 | -0.0 (5+/7-) | +1.1 (8+/4-) | +1.2 (7+/5-) | -2.0 (6+/6-) | +0.1 (7+/5-)     |
| fed x ecb | fed_hold|ecb_hiking     |            6 |                         72 | -0.3 (2+/4-) | -1.4 (3+/3-) | -2.3 (2+/3-) | +0.5 (2+/3-) | +1.0 (2+/4-)     |
| fed x ecb | fed_hold|ecb_hold       |           16 |                         88 | +0.1 (8+/8-) | +0.6 (9+/7-) | -0.1 (7+/9-) | -1.3 (7+/8-) | -0.6 (4+/12-)    |

**Joint states (Fed x ECB; hiking / hold / cutting), 1975-2026:**

| bank      | state / event           |   n episodes |   median length (sessions) | +1m            | +3m           | +6m            | +12m           | over the spell   |
|:----------|:------------------------|-------------:|---------------------------:|:---------------|:--------------|:---------------|:---------------|:-----------------|
| fed x ecb | fed_cutting|ecb_cutting |           21 |                         81 | +0.0 (9+/12-)  | +0.6 (12+/9-) | +1.2 (10+/11-) | +2.5 (11+/10-) | -0.4 (9+/11-)    |
| fed x ecb | fed_cutting|ecb_hiking  |           14 |                         54 | +1.4 (11+/3-)  | -0.1 (6+/8-)  | +0.4 (7+/7-)   | +1.9 (7+/7-)   | +0.9 (8+/6-)     |
| fed x ecb | fed_cutting|ecb_hold    |           19 |                         31 | +0.5 (11+/8-)  | +3.1 (15+/4-) | +4.3 (13+/6-)  | +5.8 (13+/6-)  | +1.7 (14+/5-)    |
| fed x ecb | fed_hiking|ecb_cutting  |           13 |                         81 | +1.1 (6+/7-)   | +1.0 (7+/6-)  | +0.8 (7+/6-)   | +1.7 (7+/6-)   | +1.5 (6+/7-)     |
| fed x ecb | fed_hiking|ecb_hiking   |           14 |                         56 | -1.7 (4+/10-)  | -1.8 (6+/7-)  | -1.6 (6+/7-)   | -1.5 (6+/7-)   | -2.9 (6+/8-)     |
| fed x ecb | fed_hiking|ecb_hold     |           14 |                         71 | -0.2 (7+/7-)   | +0.9 (7+/7-)  | +2.4 (8+/6-)   | -1.7 (5+/9-)   | +0.7 (7+/7-)     |
| fed x ecb | fed_hold|ecb_cutting    |           21 |                         78 | -0.0 (10+/11-) | +0.3 (13+/8-) | -0.4 (9+/12-)  | -2.8 (9+/12-)  | -0.5 (12+/9-)    |
| fed x ecb | fed_hold|ecb_hiking     |            9 |                         69 | -0.4 (3+/6-)   | +0.7 (6+/3-)  | +0.9 (5+/3-)   | -0.9 (3+/5-)   | +1.5 (4+/5-)     |
| fed x ecb | fed_hold|ecb_hold       |           23 |                         73 | +0.5 (13+/10-) | +1.2 (14+/9-) | +0.5 (12+/11-) | -0.2 (11+/11-) | +0.2 (9+/14-)    |

**Policy divergence, 1999-2026** (widening / narrowing of the policy-rate gap, and who is tightening relative to the other):

| bank      | state / event         |   n episodes |   median length (sessions) | +1m            | +3m            | +6m            | +12m           | over the spell   |
|:----------|:----------------------|-------------:|---------------------------:|:---------------|:---------------|:---------------|:---------------|:-----------------|
| fed x ecb | narrowing|ecb_tighter |            8 |                         83 | -0.6 (2+/6-)   | +0.5 (5+/3-)   | +2.5 (4+/3-)   | +4.7 (5+/2-)   | +2.5 (5+/3-)     |
| fed x ecb | narrowing|fed_tighter |            8 |                         87 | +0.2 (3+/5-)   | +2.1 (6+/2-)   | +3.5 (6+/2-)   | -1.3 (4+/4-)   | +2.8 (6+/2-)     |
| fed x ecb | parallel|same         |           27 |                        103 | -0.4 (11+/16-) | +0.3 (15+/11-) | +0.8 (13+/13-) | +0.9 (15+/10-) | -0.3 (10+/16-)   |
| fed x ecb | widening|ecb_tighter  |            6 |                         22 | -0.6 (2+/4-)   | +4.3 (4+/2-)   | +4.8 (5+/1-)   | +3.2 (3+/3-)   | -2.3 (1+/5-)     |
| fed x ecb | widening|fed_tighter  |            9 |                        150 | -0.3 (4+/5-)   | -0.6 (5+/4-)   | -3.1 (3+/6-)   | -3.4 (3+/6-)   | -2.1 (4+/5-)     |

**Policy divergence, 1975-2026** (widening / narrowing of the policy-rate gap, and who is tightening relative to the other):

| bank      | state / event         |   n episodes |   median length (sessions) | +1m            | +3m            | +6m            | +12m           | over the spell   |
|:----------|:----------------------|-------------:|---------------------------:|:---------------|:---------------|:---------------|:---------------|:-----------------|
| fed x ecb | narrowing|ecb_tighter |           25 |                         45 | +0.8 (16+/9-)  | +1.7 (17+/8-)  | +2.5 (15+/9-)  | +4.8 (15+/9-)  | +2.5 (17+/8-)    |
| fed x ecb | narrowing|fed_tighter |            9 |                         87 | +0.1 (3+/6-)   | +2.0 (7+/2-)   | +2.7 (6+/3-)   | -1.8 (4+/5-)   | +3.0 (7+/2-)     |
| fed x ecb | parallel|same         |           58 |                         71 | -0.2 (26+/32-) | +0.3 (32+/25-) | +0.3 (28+/29-) | +0.5 (28+/28-) | -0.8 (24+/33-)   |
| fed x ecb | widening|ecb_tighter  |           10 |                         33 | -0.7 (3+/7-)   | +2.4 (6+/4-)   | +2.8 (8+/2-)   | +2.0 (6+/4-)   | -0.6 (3+/7-)     |
| fed x ecb | widening|fed_tighter  |           26 |                         86 | +0.1 (12+/14-) | +0.3 (14+/12-) | -1.6 (9+/17-)  | -1.8 (11+/15-) | -0.4 (13+/13-)   |

**Drift of EUR/USD while each joint state lasted** (annualised %, t from daily returns; the t-statistic treats days as independent and still finds nothing above 2 in 1999-2026):

| kind       | state                   | era       |   sessions |   years |   ann_drift_pct |   t_daily_naive |   share_up_days |
|:-----------|:------------------------|:----------|-----------:|--------:|----------------:|----------------:|----------------:|
| joint      | fed_cutting|ecb_cutting | 1975-2026 |       1735 |    6.88 |           -1.16 |           -0.28 |            0.49 |
| joint      | fed_cutting|ecb_hiking  | 1975-2026 |       1128 |    4.48 |            2.70 |            0.48 |            0.51 |
| joint      | fed_cutting|ecb_hold    | 1975-2026 |       1161 |    4.61 |            6.91 |            1.49 |            0.52 |
| joint      | fed_hiking|ecb_cutting  | 1975-2026 |       1070 |    4.25 |            4.54 |            0.97 |            0.49 |
| joint      | fed_hiking|ecb_hiking   | 1975-2026 |       1593 |    6.32 |           -6.43 |           -1.62 |            0.47 |
| joint      | fed_hiking|ecb_hold     | 1975-2026 |       1651 |    6.55 |            1.40 |            0.40 |            0.51 |
| joint      | fed_hold|ecb_cutting    | 1975-2026 |       1641 |    6.51 |           -1.68 |           -0.49 |            0.49 |
| joint      | fed_hold|ecb_hiking     | 1975-2026 |        737 |    2.92 |            4.47 |            0.80 |            0.52 |
| joint      | fed_hold|ecb_hold       | 1975-2026 |       2531 |   10.04 |            0.51 |            0.18 |            0.51 |
| joint      | fed_cutting|ecb_cutting | 1999-2026 |        733 |    2.91 |            3.35 |            0.50 |            0.49 |
| joint      | fed_cutting|ecb_hiking  | 1999-2026 |         77 |    0.31 |          -27.18 |           -1.51 |            0.42 |
| joint      | fed_cutting|ecb_hold    | 1999-2026 |        669 |    2.65 |            0.27 |            0.05 |            0.49 |
| joint      | fed_hiking|ecb_cutting  | 1999-2026 |        113 |    0.45 |           20.80 |            1.62 |            0.50 |
| joint      | fed_hiking|ecb_hiking   | 1999-2026 |        846 |    3.36 |           -2.18 |           -0.44 |            0.49 |
| joint      | fed_hiking|ecb_hold     | 1999-2026 |       1093 |    4.34 |           -1.68 |           -0.44 |            0.50 |
| joint      | fed_hold|ecb_cutting    | 1999-2026 |       1011 |    4.01 |            0.36 |            0.08 |            0.50 |
| joint      | fed_hold|ecb_hiking     | 1999-2026 |        586 |    2.33 |            2.53 |            0.40 |            0.52 |
| joint      | fed_hold|ecb_hold       | 1999-2026 |       2094 |    8.31 |           -1.21 |           -0.39 |            0.50 |
| divergence | narrowing|ecb_tighter   | 1975-2026 |       1791 |    7.11 |            8.90 |            2.35 |            0.52 |
| divergence | narrowing|fed_tighter   | 1975-2026 |       1204 |    4.78 |            5.73 |            1.36 |            0.51 |
| divergence | parallel|same           | 1975-2026 |       5859 |   23.25 |           -1.87 |           -0.91 |            0.49 |
| divergence | widening|ecb_tighter    | 1975-2026 |       1235 |    4.90 |           -1.28 |           -0.25 |            0.52 |
| divergence | widening|fed_tighter    | 1975-2026 |       3158 |   12.53 |           -0.78 |           -0.31 |            0.49 |
| divergence | narrowing|ecb_tighter   | 1999-2026 |        921 |    3.65 |            3.30 |            0.80 |            0.50 |
| divergence | narrowing|fed_tighter   | 1999-2026 |        734 |    2.91 |            7.57 |            1.46 |            0.51 |
| divergence | parallel|same           | 1999-2026 |       3673 |   14.58 |           -0.52 |           -0.21 |            0.50 |
| divergence | widening|ecb_tighter    | 1999-2026 |        411 |    1.63 |           -8.44 |           -0.96 |            0.50 |
| divergence | widening|fed_tighter    | 1999-2026 |       1483 |    5.88 |           -3.15 |           -0.96 |            0.49 |

## 3. Is there a tradeable signal the market has not priced?

**The ten candidates (2010-2026 coverage)**; definitions and priors in the module docstring.

| candidate      | type   | declared vote form                   |   long % |   short % |   silent % |   sign changes / year |
|:---------------|:-------|:-------------------------------------|---------:|----------:|-----------:|----------------------:|
| gap_rel        | dense  | agreement rule AND signal agrees     |       28 |        72 |          0 |                  8.00 |
| gap_rel_strong | sparse | agreement rule UNLESS signal opposes |       11 |        38 |         51 |                 12.40 |
| gap_fed        | dense  | agreement rule AND signal agrees     |       17 |        83 |          0 |                  1.70 |
| gap_ecb        | dense  | agreement rule AND signal agrees     |       68 |        32 |          0 |                  6.50 |
| model_rel      | dense  | agreement rule AND signal agrees     |       38 |        62 |          0 |                  6.60 |
| mkt_rel        | dense  | agreement rule AND signal agrees     |       67 |        33 |          0 |                  2.70 |
| phase_rel      | sparse | agreement rule UNLESS signal opposes |       13 |        35 |         53 |                  2.10 |
| turn63         | sparse | agreement rule UNLESS signal opposes |        4 |         6 |         90 |                  0.80 |
| fed_phase      | sparse | agreement rule UNLESS signal opposes |       12 |        26 |         62 |                  1.00 |
| ecb_phase      | sparse | agreement rule UNLESS signal opposes |       15 |        25 |         60 |                  1.20 |

**Reconciliation of the agreement rule with arm N** (2010-26):

|   h | mode       |   n_here |   acc_here |   n_selective_code |   acc_selective_code |   n_published |   acc_published |
|----:|:-----------|---------:|-----------:|-------------------:|---------------------:|--------------:|----------------:|
|  21 | weekly     |      387 |      0.594 |                387 |                0.594 |           387 |           0.594 |
|  42 | weekly     |      383 |      0.648 |                383 |                0.648 |           383 |           0.648 |
|  63 | weekly     |      383 |      0.666 |                383 |                0.666 |           383 |           0.666 |
|  21 | nonoverlap |      156 |      0.590 |                156 |                0.590 |           156 |           0.590 |
|  42 | nonoverlap |       89 |      0.607 |                 89 |                0.607 |            89 |           0.610 |
|  63 | nonoverlap |       61 |      0.721 |                 61 |                0.721 |            61 |           0.720 |

### 3.1 Standalone accuracy (direction of the next 21 / 42 / 63 sessions), % [95 % interval] n (decisions a year)

*NON-OVERLAPPING decisions (Wilson interval)*

| candidate      |   h | 2010-26                   | 2016-26                   | 2023-26                  | 2004-09                  |
|:---------------|----:|:--------------------------|:--------------------------|:-------------------------|:-------------------------|
| gap_rel        |  21 | 50 [44-57] n=208 (12.4/y) | 51 [43-59] n=133 (12.4/y) | 51 [37-65] n=47 (12.5/y) | 60 [41-77] n=25 (4.2/y)  |
| gap_rel        |  42 | 50 [41-59] n=104 (6.2/y)  | 50 [38-62] n=66 (6.2/y)   | 48 [29-67] n=23 (6.2/y)  | 62 [36-82] n=13 (2.2/y)  |
| gap_rel        |  63 | 52 [41-64] n=69 (4.2/y)   | 50 [36-64] n=44 (4.2/y)   | 40 [20-64] n=15 (4.2/y)  | 89 [57-98] n=9 (1.5/y)   |
| gap_rel_strong |  21 | 53 [45-61] n=132 (7.9/y)  | 51 [40-61] n=81 (7.5/y)   | 39 [22-59] n=23 (6.1/y)  | 86 [49-97] n=7 (1.2/y)   |
| gap_rel_strong |  42 | 58 [47-68] n=76 (4.6/y)   | 62 [47-74] n=47 (4.4/y)   | 62 [36-82] n=13 (3.5/y)  | 100 [51-100] n=4 (0.7/y) |
| gap_rel_strong |  63 | 57 [44-69] n=56 (3.4/y)   | 62 [45-76] n=34 (3.2/y)   | 60 [31-83] n=10 (2.8/y)  | 100 [44-100] n=3 (0.5/y) |
| gap_fed        |  21 | 55 [48-61] n=208 (12.4/y) | 53 [44-61] n=133 (12.4/y) | 53 [39-67] n=47 (12.5/y) | 51 [40-62] n=75 (12.5/y) |
| gap_fed        |  42 | 57 [47-66] n=104 (6.2/y)  | 55 [43-66] n=66 (6.2/y)   | 52 [33-71] n=23 (6.2/y)  | 50 [35-65] n=38 (6.3/y)  |
| gap_fed        |  63 | 51 [39-62] n=69 (4.2/y)   | 45 [32-60] n=44 (4.2/y)   | 33 [15-58] n=15 (4.2/y)  | 60 [41-77] n=25 (4.2/y)  |
| gap_ecb        |  21 | 45 [39-52] n=208 (12.4/y) | 48 [40-57] n=133 (12.4/y) | 47 [33-61] n=47 (12.5/y) | 44 [27-63] n=25 (4.2/y)  |
| gap_ecb        |  42 | 38 [30-48] n=104 (6.2/y)  | 36 [26-48] n=66 (6.2/y)   | 43 [26-63] n=23 (6.2/y)  | 38 [18-64] n=13 (2.2/y)  |
| gap_ecb        |  63 | 46 [35-58] n=69 (4.2/y)   | 45 [32-60] n=44 (4.2/y)   | 53 [30-75] n=15 (4.2/y)  | 56 [27-81] n=9 (1.5/y)   |
| model_rel      |  21 | 52 [45-59] n=208 (12.4/y) | 53 [45-62] n=133 (12.4/y) | 51 [37-65] n=47 (12.5/y) | 61 [50-72] n=75 (12.5/y) |
| model_rel      |  42 | 54 [44-63] n=104 (6.2/y)  | 55 [43-66] n=66 (6.2/y)   | 48 [29-67] n=23 (6.2/y)  | 58 [42-72] n=38 (6.3/y)  |
| model_rel      |  63 | 55 [43-66] n=69 (4.2/y)   | 57 [42-70] n=44 (4.2/y)   | 60 [36-80] n=15 (4.2/y)  | 72 [52-86] n=25 (4.2/y)  |
| mkt_rel        |  21 | 54 [48-61] n=208 (12.4/y) | 52 [43-60] n=133 (12.4/y) | 49 [35-63] n=47 (12.5/y) | 56 [37-73] n=25 (4.2/y)  |
| mkt_rel        |  42 | 56 [46-65] n=104 (6.2/y)  | 55 [43-66] n=66 (6.2/y)   | 52 [33-71] n=23 (6.2/y)  | 62 [36-82] n=13 (2.2/y)  |
| mkt_rel        |  63 | 61 [49-72] n=69 (4.2/y)   | 61 [47-74] n=44 (4.2/y)   | 67 [42-85] n=15 (4.2/y)  | 44 [19-73] n=9 (1.5/y)   |
| phase_rel      |  21 | 50 [41-60] n=109 (6.5/y)  | 49 [37-60] n=72 (6.7/y)   | 43 [26-63] n=23 (6.1/y)  | 51 [37-65] n=47 (7.8/y)  |
| phase_rel      |  42 | 49 [37-62] n=59 (3.5/y)   | 53 [37-68] n=38 (3.6/y)   | 33 [14-61] n=12 (3.3/y)  | 58 [39-76] n=24 (4.0/y)  |
| phase_rel      |  63 | 43 [29-58] n=42 (2.5/y)   | 52 [34-69] n=27 (2.5/y)   | 33 [12-65] n=9 (2.5/y)   | 62 [39-82] n=16 (2.7/y)  |
| turn63         |  21 | 43 [24-63] n=21 (1.3/y)   | 43 [21-67] n=14 (1.3/y)   | 33 [10-70] n=6 (1.6/y)   | 50 [19-81] n=6 (1.0/y)   |
| turn63         |  42 | 36 [16-61] n=14 (0.8/y)   | 33 [12-65] n=9 (0.8/y)    | 0 [0-49] n=4 (1.1/y)     | 50 [15-85] n=4 (0.7/y)   |
| turn63         |  63 | 57 [25-84] n=7 (0.4/y)    | 75 [30-95] n=4 (0.4/y)    | 50 [9-91] n=2 (0.6/y)    | 50 [9-91] n=2 (0.3/y)    |
| fed_phase      |  21 | 49 [38-59] n=82 (4.9/y)   | 49 [39-60] n=81 (7.5/y)   | 44 [28-63] n=27 (7.2/y)  | 52 [38-66] n=48 (8.0/y)  |
| fed_phase      |  42 | 51 [37-65] n=43 (2.6/y)   | 52 [38-67] n=42 (3.9/y)   | 43 [21-67] n=14 (3.8/y)  | 48 [30-67] n=25 (4.2/y)  |
| fed_phase      |  63 | 48 [31-66] n=29 (1.7/y)   | 50 [33-67] n=28 (2.6/y)   | 33 [12-65] n=9 (2.5/y)   | 41 [22-64] n=17 (2.8/y)  |
| ecb_phase      |  21 | 51 [41-61] n=90 (5.4/y)   | 49 [36-62] n=53 (4.9/y)   | 43 [28-59] n=35 (9.3/y)  | 45 [30-60] n=38 (6.3/y)  |
| ecb_phase      |  42 | 44 [31-58] n=48 (2.9/y)   | 44 [28-63] n=27 (2.5/y)   | 39 [20-61] n=18 (4.9/y)  | 50 [30-70] n=20 (3.3/y)  |
| ecb_phase      |  63 | 36 [22-53] n=33 (2.0/y)   | 44 [25-66] n=18 (1.7/y)   | 58 [32-81] n=12 (3.3/y)  | 77 [50-92] n=13 (2.2/y)  |

*weekly decisions (Wilson with the conservative effective n of arm N)*

| candidate      |   h | 2010-26                   | 2016-26                   | 2023-26                   | 2004-09                   |
|:---------------|----:|:--------------------------|:--------------------------|:--------------------------|:--------------------------|
| gap_rel        |  21 | 49 [42-56] n=870 (52.0/y) | 52 [44-61] n=559 (52.0/y) | 49 [35-63] n=195 (52.2/y) | 53 [34-71] n=104 (17.4/y) |
| gap_rel        |  42 | 51 [41-60] n=866 (52.0/y) | 55 [43-67] n=555 (52.0/y) | 51 [32-70] n=191 (52.2/y) | 65 [38-85] n=104 (17.4/y) |
| gap_rel        |  63 | 51 [39-62] n=862 (52.0/y) | 56 [42-70] n=551 (52.0/y) | 49 [26-72] n=187 (52.2/y) | 67 [35-89] n=104 (17.4/y) |
| gap_rel_strong |  21 | 51 [41-61] n=425 (25.4/y) | 55 [42-67] n=251 (23.4/y) | 40 [19-66] n=57 (15.3/y)  | 90 [45-99] n=20 (3.3/y)   |
| gap_rel_strong |  42 | 56 [42-69] n=425 (25.5/y) | 64 [46-79] n=251 (23.5/y) | 61 [28-87] n=57 (15.6/y)  | 100 [27-100] n=20 (3.3/y) |
| gap_rel_strong |  63 | 55 [39-70] n=425 (25.6/y) | 66 [44-82] n=251 (23.7/y) | 56 [20-87] n=57 (15.9/y)  | 100 [21-100] n=20 (3.3/y) |
| gap_fed        |  21 | 52 [45-59] n=870 (52.0/y) | 51 [42-59] n=559 (52.0/y) | 47 [33-61] n=195 (52.2/y) | 53 [41-64] n=312 (52.1/y) |
| gap_fed        |  42 | 53 [43-62] n=866 (52.0/y) | 53 [41-65] n=555 (52.0/y) | 49 [30-68] n=191 (52.2/y) | 55 [40-70] n=312 (52.1/y) |
| gap_fed        |  63 | 53 [41-64] n=862 (52.0/y) | 53 [39-67] n=551 (52.0/y) | 45 [23-69] n=187 (52.2/y) | 55 [36-72] n=312 (52.1/y) |
| gap_ecb        |  21 | 45 [39-52] n=870 (52.0/y) | 47 [39-56] n=559 (52.0/y) | 48 [34-62] n=195 (52.2/y) | 48 [30-67] n=104 (17.4/y) |
| gap_ecb        |  42 | 44 [35-53] n=866 (52.0/y) | 45 [34-57] n=555 (52.0/y) | 46 [28-66] n=191 (52.2/y) | 41 [19-67] n=104 (17.4/y) |
| gap_ecb        |  63 | 45 [33-56] n=862 (52.0/y) | 47 [33-62] n=551 (52.0/y) | 49 [27-72] n=187 (52.2/y) | 45 [19-75] n=104 (17.4/y) |
| model_rel      |  21 | 50 [43-56] n=870 (52.0/y) | 52 [44-61] n=559 (52.0/y) | 48 [35-62] n=195 (52.2/y) | 62 [51-72] n=312 (52.1/y) |
| model_rel      |  42 | 50 [41-60] n=866 (52.0/y) | 55 [43-67] n=555 (52.0/y) | 48 [29-67] n=191 (52.2/y) | 66 [50-79] n=312 (52.1/y) |
| model_rel      |  63 | 51 [39-62] n=862 (52.0/y) | 58 [44-72] n=551 (52.0/y) | 52 [29-75] n=187 (52.2/y) | 72 [52-86] n=312 (52.1/y) |
| mkt_rel        |  21 | 53 [46-59] n=870 (52.0/y) | 51 [43-60] n=559 (52.0/y) | 52 [38-65] n=195 (52.2/y) | 52 [33-70] n=104 (17.4/y) |
| mkt_rel        |  42 | 53 [44-63] n=866 (52.0/y) | 50 [39-62] n=555 (52.0/y) | 52 [33-71] n=191 (52.2/y) | 59 [33-81] n=104 (17.4/y) |
| mkt_rel        |  63 | 53 [41-64] n=862 (52.0/y) | 51 [36-65] n=551 (52.0/y) | 53 [30-75] n=187 (52.2/y) | 55 [25-81] n=104 (17.4/y) |
| phase_rel      |  21 | 48 [39-58] n=411 (24.6/y) | 48 [36-60] n=273 (25.4/y) | 39 [21-61] n=84 (22.5/y)  | 52 [38-66] n=196 (32.7/y) |
| phase_rel      |  42 | 52 [38-65] n=410 (24.6/y) | 56 [39-71] n=272 (25.5/y) | 42 [18-71] n=83 (22.7/y)  | 54 [34-72] n=196 (32.7/y) |
| phase_rel      |  63 | 48 [32-64] n=406 (24.5/y) | 53 [33-72] n=268 (25.3/y) | 42 [14-75] n=79 (22.0/y)  | 59 [35-79] n=196 (32.7/y) |
| turn63         |  21 | 40 [22-61] n=88 (5.3/y)   | 37 [18-62] n=62 (5.8/y)   | 24 [6-63] n=25 (6.7/y)    | 60 [25-87] n=25 (4.2/y)   |
| turn63         |  42 | 47 [22-73] n=88 (5.3/y)   | 48 [20-78] n=62 (5.8/y)   | 36 [7-81] n=25 (6.8/y)    | 52 [13-88] n=25 (4.2/y)   |
| turn63         |  63 | 44 [16-76] n=84 (5.1/y)   | 50 [16-84] n=58 (5.5/y)   | 43 [6-89] n=21 (5.9/y)    | 48 [9-90] n=25 (4.2/y)    |
| fed_phase      |  21 | 50 [39-61] n=329 (19.7/y) | 50 [39-61] n=327 (30.4/y) | 50 [32-68] n=109 (29.2/y) | 49 [36-63] n=198 (33.1/y) |
| fed_phase      |  42 | 56 [41-71] n=326 (19.6/y) | 57 [41-71] n=324 (30.4/y) | 55 [30-78] n=106 (29.0/y) | 54 [34-72] n=198 (33.1/y) |
| fed_phase      |  63 | 48 [31-67] n=326 (19.7/y) | 49 [31-67] n=324 (30.6/y) | 43 [18-73] n=106 (29.6/y) | 49 [27-72] n=198 (33.1/y) |
| ecb_phase      |  21 | 47 [36-57] n=345 (20.6/y) | 45 [32-59] n=207 (19.3/y) | 44 [29-61] n=139 (37.2/y) | 51 [36-66] n=156 (26.0/y) |
| ecb_phase      |  42 | 45 [30-60] n=341 (20.5/y) | 45 [28-64] n=203 (19.0/y) | 41 [21-65] n=135 (36.9/y) | 48 [28-69] n=156 (26.0/y) |
| ecb_phase      |  63 | 47 [30-65] n=337 (20.3/y) | 53 [31-75] n=199 (18.8/y) | 50 [24-76] n=131 (36.6/y) | 60 [33-81] n=156 (26.0/y) |

### 3.2 As an extra vote on the agreement rule (non-overlapping decisions)

(a) vote rule in its declared form against the agreement rule alone:

| rule                  |   h | 2010-26                  | 2016-26                 | 2023-26                 | 2006-09                 |
|:----------------------|----:|:-------------------------|:------------------------|:------------------------|:------------------------|
| AGREEMENT RULE alone  |  21 | 59 [51-66] n=156 (9.3/y) | 57 [47-67] n=96 (8.9/y) | 60 [44-74] n=35 (9.3/y) | 58 [42-73] n=36 (9.0/y) |
| AGREEMENT RULE alone  |  42 | 61 [50-70] n=89 (5.3/y)  | 59 [46-71] n=56 (5.2/y) | 45 [26-66] n=20 (5.4/y) | 50 [31-69] n=22 (5.5/y) |
| AGREEMENT RULE alone  |  63 | 72 [60-82] n=61 (3.7/y)  | 71 [55-83] n=38 (3.6/y) | 50 [27-73] n=14 (3.9/y) | 80 [55-93] n=15 (3.8/y) |
| gap_rel (agrees)      |  21 | 62 [50-72] n=78 (4.7/y)  | 62 [48-75] n=48 (4.5/y) | 50 [25-75] n=12 (3.2/y) | 83 [55-95] n=12 (3.0/y) |
| gap_rel (agrees)      |  42 | 61 [47-74] n=49 (2.9/y)  | 67 [49-81] n=30 (2.8/y) | 62 [31-86] n=8 (2.2/y)  | 88 [53-98] n=8 (2.0/y)  |
| gap_rel (agrees)      |  63 | 65 [49-78] n=37 (2.2/y)  | 73 [52-87] n=22 (2.1/y) | 50 [19-81] n=6 (1.7/y)  | 67 [30-90] n=6 (1.5/y)  |
| gap_rel_strong (veto) |  21 | 57 [49-66] n=120 (7.2/y) | 58 [46-68] n=73 (6.8/y) | 54 [35-71] n=26 (6.9/y) | 60 [44-74] n=35 (8.8/y) |
| gap_rel_strong (veto) |  42 | 61 [50-72] n=72 (4.3/y)  | 64 [50-77] n=45 (4.2/y) | 47 [26-69] n=17 (4.6/y) | 55 [35-73] n=22 (5.5/y) |
| gap_rel_strong (veto) |  63 | 70 [56-80] n=53 (3.2/y)  | 72 [55-84] n=32 (3.0/y) | 45 [21-72] n=11 (3.1/y) | 80 [55-93] n=15 (3.8/y) |
| gap_fed (agrees)      |  21 | 62 [52-72] n=88 (5.3/y)  | 59 [46-71] n=54 (5.0/y) | 53 [32-73] n=19 (5.0/y) | 59 [36-78] n=17 (4.3/y) |
| gap_fed (agrees)      |  42 | 65 [52-77] n=52 (3.1/y)  | 66 [48-80] n=32 (3.0/y) | 55 [28-79] n=11 (3.0/y) | 75 [47-91] n=12 (3.0/y) |
| gap_fed (agrees)      |  63 | 72 [57-84] n=40 (2.4/y)  | 75 [55-88] n=24 (2.3/y) | 56 [27-81] n=9 (2.5/y)  | 50 [22-78] n=8 (2.0/y)  |
| gap_ecb (agrees)      |  21 | 54 [43-64] n=80 (4.8/y)  | 55 [40-69] n=42 (3.9/y) | 64 [39-84] n=14 (3.7/y) | 73 [43-90] n=11 (2.8/y) |
| gap_ecb (agrees)      |  42 | 58 [44-71] n=50 (3.0/y)  | 54 [36-70] n=28 (2.6/y) | 30 [11-60] n=10 (2.7/y) | 71 [36-92] n=7 (1.8/y)  |
| gap_ecb (agrees)      |  63 | 69 [54-81] n=39 (2.3/y)  | 68 [47-84] n=22 (2.1/y) | 50 [22-78] n=8 (2.2/y)  | 80 [38-96] n=5 (1.3/y)  |
| model_rel (agrees)    |  21 | 58 [47-67] n=92 (5.5/y)  | 64 [51-75] n=58 (5.4/y) | 72 [49-88] n=18 (4.8/y) | 71 [50-86] n=21 (5.3/y) |
| model_rel (agrees)    |  42 | 61 [48-73] n=54 (3.2/y)  | 68 [51-81] n=34 (3.2/y) | 55 [28-79] n=11 (3.0/y) | 73 [48-89] n=15 (3.8/y) |
| model_rel (agrees)    |  63 | 78 [62-88] n=40 (2.4/y)  | 79 [60-91] n=24 (2.3/y) | 50 [22-78] n=8 (2.2/y)  | 82 [52-95] n=11 (2.8/y) |
| mkt_rel (agrees)      |  21 | 60 [50-69] n=92 (5.5/y)  | 61 [48-72] n=56 (5.2/y) | 71 [47-87] n=17 (4.5/y) | 86 [49-97] n=7 (1.8/y)  |
| mkt_rel (agrees)      |  42 | 70 [57-81] n=54 (3.2/y)  | 70 [53-83] n=33 (3.1/y) | 45 [21-72] n=11 (3.0/y) | 80 [38-96] n=5 (1.3/y)  |
| mkt_rel (agrees)      |  63 | 71 [56-82] n=41 (2.5/y)  | 72 [52-86] n=25 (2.4/y) | 56 [27-81] n=9 (2.5/y)  | 67 [21-94] n=3 (0.8/y)  |
| phase_rel (veto)      |  21 | 54 [46-63] n=129 (7.7/y) | 51 [40-62] n=78 (7.2/y) | 46 [30-64] n=28 (7.4/y) | 62 [43-79] n=24 (6.0/y) |
| phase_rel (veto)      |  42 | 58 [47-69] n=72 (4.3/y)  | 57 [42-70] n=44 (4.1/y) | 38 [18-61] n=16 (4.3/y) | 60 [36-80] n=15 (3.8/y) |
| phase_rel (veto)      |  63 | 67 [54-78] n=52 (3.1/y)  | 68 [50-81] n=31 (2.9/y) | 36 [15-65] n=11 (3.1/y) | 77 [50-92] n=13 (3.3/y) |
| turn63 (veto)         |  21 | 57 [49-65] n=152 (9.1/y) | 54 [44-64] n=92 (8.6/y) | 61 [44-75] n=33 (8.8/y) | 58 [42-73] n=36 (9.0/y) |
| turn63 (veto)         |  42 | 60 [50-70] n=86 (5.2/y)  | 58 [45-71] n=53 (5.0/y) | 50 [29-71] n=18 (4.9/y) | 50 [31-69] n=22 (5.5/y) |
| turn63 (veto)         |  63 | 70 [57-80] n=60 (3.6/y)  | 68 [51-80] n=37 (3.5/y) | 46 [23-71] n=13 (3.6/y) | 80 [55-93] n=15 (3.8/y) |
| fed_phase (veto)      |  21 | 57 [48-65] n=134 (8.0/y) | 53 [41-64] n=74 (6.9/y) | 62 [43-78] n=26 (6.9/y) | 60 [39-78] n=20 (5.0/y) |
| fed_phase (veto)      |  42 | 63 [52-73] n=76 (4.6/y)  | 63 [48-76] n=43 (4.0/y) | 53 [30-75] n=15 (4.1/y) | 46 [23-71] n=13 (3.3/y) |
| fed_phase (veto)      |  63 | 71 [58-82] n=52 (3.1/y)  | 69 [51-83] n=29 (2.7/y) | 50 [24-76] n=10 (2.8/y) | 67 [35-88] n=9 (2.3/y)  |
| ecb_phase (veto)      |  21 | 58 [50-66] n=129 (7.7/y) | 58 [47-68] n=78 (7.2/y) | 62 [43-79] n=24 (6.4/y) | 59 [41-75] n=27 (6.8/y) |
| ecb_phase (veto)      |  42 | 62 [51-72] n=74 (4.4/y)  | 63 [49-75] n=46 (4.3/y) | 40 [20-64] n=15 (4.1/y) | 58 [36-77] n=19 (4.8/y) |
| ecb_phase (veto)      |  63 | 75 [62-85] n=53 (3.2/y)  | 81 [65-91] n=32 (3.0/y) | 60 [31-83] n=10 (2.8/y) | 71 [45-88] n=14 (3.5/y) |

The other form for the sparse signals (reported, never selectable; note the decisions a year):

| rule                                           |   h | 2010-26                 | 2016-26                 | 2023-26                  | 2006-09                  |
|:-----------------------------------------------|----:|:------------------------|:------------------------|:-------------------------|:-------------------------|
| gap_rel_strong (agrees; NOT the declared form) |  21 | 62 [47-74] n=47 (2.8/y) | 71 [51-85] n=24 (2.2/y) | 0 [0-79] n=1 (0.3/y)     | 100 [51-100] n=4 (1.0/y) |
| gap_rel_strong (agrees; NOT the declared form) |  42 | 73 [56-86] n=30 (1.8/y) | 76 [53-90] n=17 (1.6/y) | 100 [21-100] n=1 (0.3/y) | 100 [44-100] n=3 (0.8/y) |
| gap_rel_strong (agrees; NOT the declared form) |  63 | 80 [61-91] n=25 (1.5/y) | 86 [60-96] n=14 (1.3/y) | 100 [21-100] n=1 (0.3/y) | 100 [34-100] n=2 (0.5/y) |
| phase_rel (agrees; NOT the declared form)      |  21 | 53 [40-66] n=51 (3.0/y) | 56 [39-72] n=32 (3.0/y) | 56 [27-81] n=9 (2.4/y)   | 57 [25-84] n=7 (1.8/y)   |
| phase_rel (agrees; NOT the declared form)      |  42 | 65 [47-79] n=31 (1.9/y) | 74 [51-88] n=19 (1.8/y) | 67 [30-90] n=6 (1.6/y)   | 60 [23-88] n=5 (1.3/y)   |
| phase_rel (agrees; NOT the declared form)      |  63 | 58 [39-76] n=24 (1.4/y) | 64 [39-84] n=14 (1.3/y) | 50 [15-85] n=4 (1.1/y)   | 75 [30-95] n=4 (1.0/y)   |
| turn63 (agrees; NOT the declared form)         |  21 | 31 [13-58] n=13 (0.8/y) | 17 [3-56] n=6 (0.6/y)   | 0 [0-66] n=2 (0.5/y)     | 100 [21-100] n=1 (0.3/y) |
| turn63 (agrees; NOT the declared form)         |  42 | 44 [19-73] n=9 (0.5/y)  | 50 [15-85] n=4 (0.4/y)  | 50 [9-91] n=2 (0.5/y)    | 100 [21-100] n=1 (0.3/y) |
| turn63 (agrees; NOT the declared form)         |  63 | 33 [10-70] n=6 (0.4/y)  | 33 [6-79] n=3 (0.3/y)   | 0 [0-79] n=1 (0.3/y)     | 100 [21-100] n=1 (0.3/y) |
| fed_phase (agrees; NOT the declared form)      |  21 | 51 [36-67] n=37 (2.2/y) | 50 [34-66] n=36 (3.3/y) | 36 [15-65] n=11 (2.9/y)  | 67 [21-94] n=3 (0.8/y)   |
| fed_phase (agrees; NOT the declared form)      |  42 | 52 [32-72] n=21 (1.3/y) | 55 [34-74] n=20 (1.9/y) | 33 [10-70] n=6 (1.6/y)   | 67 [21-94] n=3 (0.8/y)   |
| fed_phase (agrees; NOT the declared form)      |  63 | 44 [23-67] n=16 (1.0/y) | 47 [25-70] n=15 (1.4/y) | 20 [4-62] n=5 (1.4/y)    | 67 [21-94] n=3 (0.8/y)   |
| ecb_phase (agrees; NOT the declared form)      |  21 | 56 [40-70] n=36 (2.1/y) | 65 [41-83] n=17 (1.6/y) | 58 [32-81] n=12 (3.2/y)  | 61 [39-80] n=18 (4.5/y)  |
| ecb_phase (agrees; NOT the declared form)      |  42 | 50 [31-69] n=22 (1.3/y) | 50 [24-76] n=10 (0.9/y) | 38 [14-69] n=8 (2.2/y)   | 62 [36-82] n=13 (3.3/y)  |
| ecb_phase (agrees; NOT the declared form)      |  63 | 56 [34-75] n=18 (1.1/y) | 62 [31-86] n=8 (0.8/y)  | 50 [19-81] n=6 (1.7/y)   | 78 [45-94] n=9 (2.3/y)   |

(b) calls the signal makes when the three old signals do NOT agree (does it extend coverage?):

| candidate      |   h | 2010-26                   | 2016-26                   | 2023-26                  | 2006-09                  |
|:---------------|----:|:--------------------------|:--------------------------|:-------------------------|:-------------------------|
| gap_rel        |  21 | 47 [40-55] n=170 (10.1/y) | 48 [39-57] n=109 (10.1/y) | 42 [28-58] n=38 (10.1/y) | 57 [37-74] n=23 (5.8/y)  |
| gap_rel        |  42 | 47 [37-57] n=93 (5.6/y)   | 52 [39-64] n=60 (5.6/y)   | 48 [28-68] n=21 (5.7/y)  | 58 [32-81] n=12 (3.0/y)  |
| gap_rel        |  63 | 50 [38-62] n=64 (3.9/y)   | 59 [43-72] n=41 (3.9/y)   | 43 [21-67] n=14 (3.9/y)  | 89 [57-98] n=9 (2.3/y)   |
| gap_rel_strong |  21 | 49 [40-59] n=97 (5.8/y)   | 51 [39-63] n=61 (5.7/y)   | 50 [28-72] n=16 (4.3/y)  | 83 [44-97] n=6 (1.5/y)   |
| gap_rel_strong |  42 | 53 [41-65] n=64 (3.8/y)   | 57 [42-71] n=40 (3.7/y)   | 50 [24-76] n=10 (2.7/y)  | 100 [51-100] n=4 (1.0/y) |
| gap_rel_strong |  63 | 57 [42-70] n=46 (2.8/y)   | 66 [47-80] n=29 (2.7/y)   | 62 [31-86] n=8 (2.2/y)   | 100 [44-100] n=3 (0.8/y) |
| gap_fed        |  21 | 55 [47-62] n=170 (10.1/y) | 54 [45-63] n=109 (10.1/y) | 50 [35-65] n=38 (10.1/y) | 51 [37-65] n=47 (11.8/y) |
| gap_fed        |  42 | 49 [40-59] n=93 (5.6/y)   | 48 [36-61] n=60 (5.6/y)   | 43 [24-63] n=21 (5.7/y)  | 58 [39-76] n=24 (6.0/y)  |
| gap_fed        |  63 | 53 [41-65] n=64 (3.9/y)   | 59 [43-72] n=41 (3.9/y)   | 57 [33-79] n=14 (3.9/y)  | 41 [22-64] n=17 (4.3/y)  |
| gap_ecb        |  21 | 41 [34-49] n=170 (10.1/y) | 42 [33-52] n=109 (10.1/y) | 47 [32-63] n=38 (10.1/y) | 39 [22-59] n=23 (5.8/y)  |
| gap_ecb        |  42 | 48 [38-58] n=93 (5.6/y)   | 53 [41-65] n=60 (5.6/y)   | 57 [37-76] n=21 (5.7/y)  | 25 [9-53] n=12 (3.0/y)   |
| gap_ecb        |  63 | 50 [38-62] n=64 (3.9/y)   | 46 [32-61] n=41 (3.9/y)   | 43 [21-67] n=14 (3.9/y)  | 56 [27-81] n=9 (2.3/y)   |
| model_rel      |  21 | 49 [42-57] n=170 (10.1/y) | 54 [45-63] n=109 (10.1/y) | 50 [35-65] n=38 (10.1/y) | 66 [52-78] n=47 (11.8/y) |
| model_rel      |  42 | 46 [36-56] n=93 (5.6/y)   | 52 [39-64] n=60 (5.6/y)   | 43 [24-63] n=21 (5.7/y)  | 75 [55-88] n=24 (6.0/y)  |
| model_rel      |  63 | 53 [41-65] n=64 (3.9/y)   | 63 [48-76] n=41 (3.9/y)   | 57 [33-79] n=14 (3.9/y)  | 82 [59-94] n=17 (4.3/y)  |
| mkt_rel        |  21 | 52 [45-60] n=170 (10.1/y) | 51 [42-61] n=109 (10.1/y) | 53 [37-68] n=38 (10.1/y) | 61 [41-78] n=23 (5.8/y)  |
| mkt_rel        |  42 | 51 [41-60] n=93 (5.6/y)   | 47 [35-59] n=60 (5.6/y)   | 48 [28-68] n=21 (5.7/y)  | 75 [47-91] n=12 (3.0/y)  |
| mkt_rel        |  63 | 58 [46-69] n=64 (3.9/y)   | 51 [36-66] n=41 (3.9/y)   | 50 [27-73] n=14 (3.9/y)  | 44 [19-73] n=9 (2.3/y)   |
| phase_rel      |  21 | 51 [41-61] n=88 (5.3/y)   | 50 [38-62] n=60 (5.6/y)   | 35 [18-57] n=20 (5.3/y)  | 57 [39-73] n=28 (7.0/y)  |
| phase_rel      |  42 | 43 [31-57] n=51 (3.1/y)   | 45 [30-62] n=33 (3.1/y)   | 36 [15-65] n=11 (3.0/y)  | 53 [30-75] n=15 (3.8/y)  |
| phase_rel      |  63 | 35 [22-51] n=37 (2.2/y)   | 46 [28-65] n=24 (2.3/y)   | 25 [7-59] n=8 (2.2/y)    | 60 [31-83] n=10 (2.5/y)  |
| turn63         |  21 | 35 [18-57] n=20 (1.2/y)   | 36 [16-61] n=14 (1.3/y)   | 17 [3-56] n=6 (1.6/y)    | 67 [21-94] n=3 (0.8/y)   |
| turn63         |  42 | 36 [16-61] n=14 (0.8/y)   | 33 [12-65] n=9 (0.8/y)    | 0 [0-49] n=4 (1.1/y)     | 50 [9-91] n=2 (0.5/y)    |
| turn63         |  63 | 57 [25-84] n=7 (0.4/y)    | 75 [30-95] n=4 (0.4/y)    | 50 [9-91] n=2 (0.6/y)    | 100 [21-100] n=1 (0.3/y) |
| fed_phase      |  21 | 56 [44-67] n=66 (3.9/y)   | 57 [45-68] n=65 (6.0/y)   | 62 [41-79] n=21 (5.6/y)  | 57 [39-73] n=28 (7.0/y)  |
| fed_phase      |  42 | 55 [40-70] n=38 (2.3/y)   | 57 [41-71] n=37 (3.5/y)   | 54 [29-77] n=13 (3.5/y)  | 43 [21-67] n=14 (3.5/y)  |
| fed_phase      |  63 | 54 [36-70] n=28 (1.7/y)   | 56 [37-72] n=27 (2.5/y)   | 50 [24-76] n=10 (2.8/y)  | 36 [15-65] n=11 (2.8/y)  |
| ecb_phase      |  21 | 44 [33-56] n=70 (4.2/y)   | 38 [25-53] n=42 (3.9/y)   | 32 [18-51] n=28 (7.4/y)  | 49 [33-64] n=35 (8.8/y)  |
| ecb_phase      |  42 | 36 [23-51] n=42 (2.5/y)   | 33 [18-53] n=24 (2.2/y)   | 29 [13-53] n=17 (4.6/y)  | 44 [25-66] n=18 (4.5/y)  |
| ecb_phase      |  63 | 30 [17-48] n=30 (1.8/y)   | 41 [22-64] n=17 (1.6/y)   | 45 [21-72] n=11 (3.1/y)  | 77 [50-92] n=13 (3.3/y)  |

(c) paired difference on the weekly grid (circular block bootstrap, block 2h/5 weeks, 2000 draws):

| signal         |   h | period   | weekly accuracy, vote minus agreement rule (points) [95 % block bootstrap]   | kept minus removed decisions   |
|:---------------|----:|:---------|:-----------------------------------------------------------------------------|:-------------------------------|
| gap_rel        |  21 | 2010-26  | +2.3 [-5.7, +10.4]                                                           | +4.2 [-9.9, +18.5]             |
| gap_rel        |  21 | 2016-26  | +6.8 [-3.1, +16.1]                                                           | +11.6 [-5.0, +27.8]            |
| gap_rel        |  42 | 2010-26  | +4.7 [-5.3, +13.7]                                                           | +8.3 [-8.8, +25.0]             |
| gap_rel        |  42 | 2016-26  | +6.9 [-5.8, +17.8]                                                           | +11.7 [-8.9, +31.3]            |
| gap_rel        |  63 | 2010-26  | +4.1 [-5.9, +12.4]                                                           | +7.2 [-10.2, +22.8]            |
| gap_rel        |  63 | 2016-26  | +6.3 [-7.9, +17.0]                                                           | +10.5 [-11.7, +29.7]           |
| gap_rel_strong |  21 | 2010-26  | -0.4 [-4.8, +3.8]                                                            | -1.6 [-16.5, +13.9]            |
| gap_rel_strong |  21 | 2016-26  | +1.6 [-3.6, +6.8]                                                            | +6.3 [-14.8, +25.0]            |
| gap_rel_strong |  42 | 2010-26  | +2.0 [-2.4, +6.8]                                                            | +7.2 [-8.1, +23.0]             |
| gap_rel_strong |  42 | 2016-26  | +2.6 [-2.3, +7.6]                                                            | +10.0 [-9.6, +28.6]            |
| gap_rel_strong |  63 | 2010-26  | +2.8 [-2.1, +8.2]                                                            | +9.7 [-7.6, +26.4]             |
| gap_rel_strong |  63 | 2016-26  | +4.4 [-1.2, +10.7]                                                           | +17.2 [-5.2, +36.9]            |
| gap_fed        |  21 | 2010-26  | +2.2 [-4.4, +8.8]                                                            | +4.8 [-9.2, +19.7]             |
| gap_fed        |  21 | 2016-26  | -1.0 [-9.9, +7.9]                                                            | -2.0 [-19.0, +15.8]            |
| gap_fed        |  42 | 2010-26  | +4.5 [-3.4, +11.7]                                                           | +9.8 [-7.2, +27.4]             |
| gap_fed        |  42 | 2016-26  | +0.4 [-11.4, +10.2]                                                          | +0.7 [-19.8, +20.9]            |
| gap_fed        |  63 | 2010-26  | +3.6 [-5.3, +11.4]                                                           | +7.9 [-10.5, +25.4]            |
| gap_fed        |  63 | 2016-26  | +0.0 [-13.0, +11.0]                                                          | +0.0 [-23.5, +22.8]            |
| gap_ecb        |  21 | 2010-26  | -5.5 [-14.2, +2.7]                                                           | -9.2 [-22.3, +4.8]             |
| gap_ecb        |  21 | 2016-26  | +1.3 [-10.5, +11.6]                                                          | +2.1 [-16.3, +19.1]            |
| gap_ecb        |  42 | 2010-26  | -9.8 [-20.9, +1.3]                                                           | -16.4 [-33.5, +2.5]            |
| gap_ecb        |  42 | 2016-26  | -1.9 [-17.3, +11.7]                                                          | -3.1 [-26.1, +19.4]            |
| gap_ecb        |  63 | 2010-26  | -5.8 [-18.9, +5.5]                                                           | -9.7 [-29.6, +9.3]             |
| gap_ecb        |  63 | 2016-26  | +4.0 [-13.0, +16.2]                                                          | +6.6 [-19.6, +28.0]            |
| model_rel      |  21 | 2010-26  | +1.7 [-4.8, +8.1]                                                            | +3.5 [-9.5, +17.9]             |
| model_rel      |  21 | 2016-26  | +3.2 [-4.8, +11.3]                                                           | +7.2 [-9.5, +25.6]             |
| model_rel      |  42 | 2010-26  | +0.8 [-7.6, +7.9]                                                            | +1.6 [-13.9, +17.5]            |
| model_rel      |  42 | 2016-26  | +1.0 [-8.3, +9.0]                                                            | +2.3 [-17.2, +21.7]            |
| model_rel      |  63 | 2010-26  | +2.9 [-5.4, +10.4]                                                           | +6.1 [-10.7, +23.1]            |
| model_rel      |  63 | 2016-26  | +5.4 [-5.4, +14.3]                                                           | +12.4 [-11.8, +34.3]           |
| mkt_rel        |  21 | 2010-26  | +1.2 [-5.2, +7.3]                                                            | +2.8 [-11.8, +17.8]            |
| mkt_rel        |  21 | 2016-26  | +0.2 [-7.9, +8.2]                                                            | +0.6 [-18.6, +20.4]            |
| mkt_rel        |  42 | 2010-26  | -1.0 [-8.7, +6.2]                                                            | -2.2 [-18.3, +15.4]            |
| mkt_rel        |  42 | 2016-26  | -2.9 [-12.9, +5.9]                                                           | -7.1 [-27.9, +15.5]            |
| mkt_rel        |  63 | 2010-26  | -0.5 [-8.7, +6.7]                                                            | -1.2 [-18.1, +17.3]            |
| mkt_rel        |  63 | 2016-26  | -1.0 [-12.2, +8.4]                                                           | -2.4 [-26.7, +23.4]            |
| phase_rel      |  21 | 2010-26  | +0.6 [-2.4, +3.7]                                                            | +3.5 [-12.7, +21.5]            |
| phase_rel      |  21 | 2016-26  | +1.0 [-3.2, +5.4]                                                            | +5.2 [-16.0, +27.4]            |
| phase_rel      |  42 | 2010-26  | +0.3 [-3.3, +4.0]                                                            | +1.8 [-16.9, +26.0]            |
| phase_rel      |  42 | 2016-26  | +1.7 [-3.5, +6.7]                                                            | +8.7 [-15.8, +40.4]            |
| phase_rel      |  63 | 2010-26  | -1.5 [-6.8, +2.9]                                                            | -8.5 [-31.7, +21.2]            |
| phase_rel      |  63 | 2016-26  | +1.1 [-5.2, +6.9]                                                            | +5.6 [-21.7, +45.6]            |
| turn63         |  21 | 2010-26  | +0.7 [-0.1, +1.8]                                                            | +23.7 [-6.4, +61.1]            |
| turn63         |  21 | 2016-26  | +1.0 [-0.2, +2.7]                                                            | +21.8 [-6.6, +58.7]            |
| turn63         |  42 | 2010-26  | +0.3 [-1.2, +1.8]                                                            | +10.5 [-39.1, +67.4]           |
| turn63         |  42 | 2016-26  | +0.4 [-2.2, +2.7]                                                            | +9.1 [-40.5, +69.3]            |
| turn63         |  63 | 2010-26  | -0.5 [-1.9, +0.8]                                                            | -15.7 [-42.0, +67.2]           |
| turn63         |  63 | 2016-26  | -0.7 [-4.0, +1.4]                                                            | -15.6 [-46.5, +73.7]           |
| fed_phase      |  21 | 2010-26  | -2.0 [-5.2, +0.7]                                                            | -14.0 [-32.5, +5.4]            |
| fed_phase      |  21 | 2016-26  | -4.3 [-10.0, +0.4]                                                           | -18.5 [-37.7, +1.7]            |
| fed_phase      |  42 | 2010-26  | -0.5 [-4.2, +2.8]                                                            | -3.6 [-25.5, +22.8]            |
| fed_phase      |  42 | 2016-26  | -1.4 [-7.7, +3.9]                                                            | -6.1 [-30.4, +20.7]            |
| fed_phase      |  63 | 2010-26  | -3.0 [-7.7, +0.2]                                                            | -20.3 [-36.8, +3.1]            |
| fed_phase      |  63 | 2016-26  | -5.2 [-14.0, +0.6]                                                           | -22.2 [-42.7, +4.0]            |
| ecb_phase      |  21 | 2010-26  | +0.5 [-2.7, +3.8]                                                            | +2.8 [-14.7, +22.2]            |
| ecb_phase      |  21 | 2016-26  | +0.8 [-4.1, +6.0]                                                            | +4.0 [-21.3, +28.7]            |
| ecb_phase      |  42 | 2010-26  | +1.8 [-1.8, +5.8]                                                            | +10.5 [-11.8, +32.2]           |
| ecb_phase      |  42 | 2016-26  | +4.2 [-1.0, +10.4]                                                           | +21.7 [-5.6, +48.5]            |
| ecb_phase      |  63 | 2010-26  | +0.6 [-3.6, +4.5]                                                            | +3.6 [-20.0, +26.8]            |
| ecb_phase      |  63 | 2016-26  | +4.6 [-0.4, +9.7]                                                            | +23.7 [-3.0, +49.3]            |

### 3.3 The Round 5 success test and the timing placebo

Gain = non-overlapping accuracy of the vote rule minus the agreement rule, in points. The bar: gain >= 3 at 21 and 42 sessions in 2010-26 and 2016-26, at least 6 non-overlapping 21-session decisions a year, 2023-26 not worse, and the signal shifted by +63 and +126 sessions keeps at most half of the gain. `*` = final by the declared rule (best 2010-15 vote accuracy at 21 sessions among eligible candidates).

| candidate      | form   | gain 21s 2010-26   | gain 42s 2010-26   | gain 21s 2016-26   | gain 42s 2016-26   | gain 21s 2023-26   | gain 42s 2023-26   | dec/y 21s (2010-26 / 2016-26)   | placebo +63: gain 21s / 42s (2010-26; 2016-26)   | placebo +126: gain 21s / 42s (2010-26; 2016-26)   | >= 3 pts x4   | >= 6 / y   | 2023-26 not worse   | placebo loses half   | BAR MET   | 2010-15 vote acc 21s (selection)   |
|:---------------|:-------|:-------------------|:-------------------|:-------------------|:-------------------|:-------------------|:-------------------|:--------------------------------|:-------------------------------------------------|:--------------------------------------------------|:--------------|:-----------|:--------------------|:---------------------|:----------|:-----------------------------------|
| gap_rel        | agrees | +2.6               | +0.6               | +5.2               | +7.7               | -10.0              | +17.5              | 4.7 / 4.5                       | +6.1 / +1.6; +11.7 / +10.5                       | +1.9 / +1.6; +7.1 / +11.3                         | no            | no         | no                  | no                   | no        | 60 (not eligible)                  |
| gap_rel_strong | veto   | -1.5               | +0.4               | +0.2               | +5.5               | -6.2               | +2.1               | 7.2 / 6.8                       | +3.5 / +1.5; +7.3 / +5.1                         | -0.2 / -1.0; +4.0 / +2.3                          | no            | yes        | no                  | no                   | no        | 57                                 |
| gap_fed        | agrees | +3.5               | +4.7               | +2.0               | +6.7               | -7.4               | +9.5               | 5.3 / 5.0                       | +5.2 / +2.5; +7.1 / +5.9                         | +3.9 / +1.6; +7.1 / +6.8                          | no            | no         | no                  | no                   | no        | 68 (not eligible)                  |
| gap_ecb        | agrees | -5.2               | -2.7               | -2.5               | -5.4               | +4.3               | -15.0              | 4.8 / 3.9                       | -8.3 / -4.2; -4.9 / +0.3                         | -12.2 / +0.2; -4.0 / -1.8                         | no            | no         | no                  | no                   | no        | 53                                 |
| model_rel      | agrees | -1.4               | +0.4               | +6.5               | +8.7               | +12.2              | +9.5               | 5.5 / 5.4                       | +0.8 / -4.1; +12.9 / +5.9                        | +0.8 / -0.3; +10.0 / +8.7                         | no            | no         | yes                 | no                   | no        | 47 (not eligible)                  |
| mkt_rel        | agrees | +0.8               | +9.7               | +3.4               | +10.8              | +10.6              | +0.5               | 5.5 / 5.2                       | -1.2 / +6.6; +2.7 / +6.7                         | -4.1 / +4.6; -0.4 / +5.6                          | no            | no         | yes                 | no                   | no        | 58                                 |
| phase_rel      | veto   | -4.7               | -2.3               | -6.0               | -2.1               | -13.6              | -7.5               | 7.7 / 7.2                       | -4.1 / -0.4; -3.4 / +1.9                         | -2.2 / +2.3; -2.0 / +1.1                          | no            | yes        | no                  | no                   | no        | 59 *                               |
| turn63         | veto   | -1.7               | -0.2               | -2.9               | -0.4               | +0.6               | +5.0               | 9.1 / 8.6                       | -1.4 / -0.9; +0.8 / +1.1                         | -2.7 / +1.0; -0.3 / +2.2                          | no            | yes        | yes                 | no                   | no        | 62 (not eligible)                  |
| fed_phase      | veto   | -2.3               | +2.5               | -4.6               | +3.9               | +1.5               | +8.3               | 8.0 / 6.9                       | -1.3 / +2.5; -2.7 / +3.9                         | +0.0 / +3.4; -0.3 / +5.5                          | no            | yes        | yes                 | no                   | no        | 62 (not eligible)                  |
| ecb_phase      | veto   | -0.8               | +1.5               | +0.4               | +4.1               | +2.5               | -5.0               | 7.7 / 7.2                       | +0.4 / +1.5; +3.7 / +4.9                         | -1.3 / +6.0; -0.5 / +7.0                          | no            | yes        | no                  | no                   | no        | 59                                 |

**Final by the declared rule: `phase_rel`** (selected by the declared rule). Delivered stream = its standalone daily sign.

### 3.4 Protocol table (standalone daily sign of each candidate, 1.2 pips, net Sharpe / t) and the incremental test

| variant                    | kind                              | final   | 2010-2026    | 2016-2026    | 2023-2026    | 2010-2015    | active   |   deflated-Sharpe p (n=10) |
|:---------------------------|:----------------------------------|:--------|:-------------|:-------------|:-------------|:-------------|:---------|---------------------------:|
| gap_rel                    | candidate (standalone daily sign) | False   | +0.02 (+0.1) | -0.19 (-0.6) | -0.29 (-0.6) | +0.30 (+0.7) | 100 %    |                       0.93 |
| gap_rel_strong             | candidate (standalone daily sign) | False   | +0.11 (+0.5) | +0.14 (+0.5) | -0.18 (-0.4) | +0.09 (+0.2) | 49 %     |                       0.86 |
| gap_fed                    | candidate (standalone daily sign) | False   | +0.18 (+0.7) | -0.02 (-0.1) | -0.25 (-0.5) | +0.44 (+1.1) | 100 %    |                       0.80 |
| gap_ecb                    | candidate (standalone daily sign) | False   | -0.40 (-1.7) | -0.10 (-0.3) | -0.37 (-0.7) | -0.81 (-2.0) | 100 %    |                       1.00 |
| model_rel                  | candidate (standalone daily sign) | False   | +0.04 (+0.2) | +0.08 (+0.3) | +0.03 (+0.1) | -0.02 (-0.1) | 100 %    |                       0.92 |
| mkt_rel                    | candidate (standalone daily sign) | False   | +0.30 (+1.3) | +0.33 (+1.1) | +0.11 (+0.2) | +0.27 (+0.7) | 100 %    |                       0.63 |
| phase_rel                  | candidate (standalone daily sign) | True    | +0.01 (+0.0) | -0.10 (-0.3) | -0.40 (-0.8) | +0.17 (+0.4) | 47 %     |                       0.94 |
| turn63                     | candidate (standalone daily sign) | False   | +0.08 (+0.3) | +0.01 (+0.0) | -0.29 (-0.6) | +0.17 (+0.4) | 10 %     |                       0.89 |
| fed_phase                  | candidate (standalone daily sign) | False   | -0.03 (-0.1) | -0.04 (-0.1) | +0.14 (+0.3) | -0.02 (-0.0) | 38 %     |                       0.96 |
| ecb_phase                  | candidate (standalone daily sign) | False   | -0.02 (-0.1) | -0.15 (-0.5) | -0.39 (-0.8) | +0.17 (+0.4) | 40 %     |                       0.95 |
| phase_rel_cost0.6          | cost_sensitivity                  | False   | +0.01 (+0.0) | -0.10 (-0.3) | -0.39 (-0.8) | +0.17 (+0.4) | 47 %     |                       0.94 |
| book21_agree3              | weekly-tranche book (information) | False   | +0.52 (+2.2) | +0.51 (+1.7) | +0.43 (+0.8) | +0.56 (+1.4) | 73 %     |                       0.28 |
| book21_vote_veto_phase_rel | weekly-tranche book (information) | False   | +0.49 (+2.0) | +0.52 (+1.7) | +0.43 (+0.9) | +0.48 (+1.2) | 60 %     |                       0.32 |

Hit rate of the delivered daily stream (active sessions):

| period   |   active_sessions |   share_net_positive |   share_correct_sign |
|:---------|------------------:|---------------------:|---------------------:|
| 2010-26  |              2062 |                0.496 |                0.496 |
| 2016-26  |              1372 |                0.485 |                0.485 |
| 2023-26  |               418 |                0.469 |                0.469 |

Incremental test (`meta.combine(..., 'EW')`, `report_combo`):

| combo                     | period    |   sharpe |     t |
|:--------------------------|:----------|---------:|------:|
| weak_signals+regime_trend | 2010-2026 |    0.563 | 2.347 |
| weak_signals+regime_trend | 2016-2026 |    0.636 | 2.128 |
| weak_signals+regime_trend | 2023-2026 |    0.356 | 0.708 |
| +policy_cycle             | 2010-2026 |    0.451 | 1.877 |
| +policy_cycle             | 2016-2026 |    0.443 | 1.482 |
| +policy_cycle             | 2023-2026 |    0.147 | 0.294 |

Daily-P&L correlation of the delivered stream with `weak_signals` +0.02, with `regime_trend` -0.02.

## 4. Leak checks

(1) and (2) for the exchange-rate side: average over the ten candidates, 21 sessions, 2010-26 (standalone weekly accuracy; non-overlapping accuracy of the declared vote rule; the agreement rule on the same labels). No signal is fitted to an exchange rate, so the shuffle must give a coin and does. Shifting the signals INTO THE FUTURE does not help either: the signals contain no price, so there is nothing for a look-ahead to exploit, and making them 1-21 sessions staler changes nothing, which is the same message as the timing placebo: what little they show is regime, not timing.

| check                      |   standalone_weekly_2010-26 |   vote_nonoverlap_2010-26 |   agreement rule itself |
|:---------------------------|----------------------------:|--------------------------:|------------------------:|
| fx_labels_shuffled_0       |                       0.503 |                     0.538 |                   0.541 |
| fx_labels_shuffled_1       |                       0.498 |                     0.542 |                   0.554 |
| fx_labels_shuffled_2       |                       0.500 |                     0.529 |                   0.529 |
| baseline                   |                       0.485 |                     0.579 |                   0.590 |
| signal_stale_plus1         |                       0.488 |                     0.577 |                   0.590 |
| signal_stale_plus5         |                       0.487 |                     0.589 |                   0.590 |
| signal_stale_plus21        |                       0.499 |                     0.577 |                   0.590 |
| signal_from_future_minus21 |                       0.491 |                     0.573 |                   0.590 |
| signal_from_future_minus63 |                       0.520 |                     0.578 |                   0.590 |

The same for the final signal `phase_rel`:

| check                      |   h |   standalone_weekly_2010-26 |   vote_nonoverlap_2010-26 |   agree3_nonoverlap_2010-26 |
|:---------------------------|----:|----------------------------:|--------------------------:|----------------------------:|
| fx_labels_shuffled_0       |  21 |                       0.529 |                     0.585 |                       0.541 |
| fx_labels_shuffled_0       |  42 |                       0.476 |                     0.534 |                       0.489 |
| fx_labels_shuffled_1       |  21 |                       0.500 |                     0.485 |                       0.554 |
| fx_labels_shuffled_1       |  42 |                       0.478 |                     0.452 |                       0.489 |
| fx_labels_shuffled_2       |  21 |                       0.498 |                     0.485 |                       0.529 |
| fx_labels_shuffled_2       |  42 |                       0.502 |                     0.493 |                       0.456 |
| baseline                   |  21 |                       0.484 |                     0.543 |                       0.590 |
| baseline                   |  42 |                       0.517 |                     0.583 |                       0.607 |
| signal_stale_plus1         |  21 |                       0.488 |                     0.531 |                       0.590 |
| signal_stale_plus1         |  42 |                       0.523 |                     0.549 |                       0.607 |
| signal_stale_plus5         |  21 |                       0.491 |                     0.578 |                       0.590 |
| signal_stale_plus5         |  42 |                       0.531 |                     0.556 |                       0.607 |
| signal_stale_plus21        |  21 |                       0.511 |                     0.547 |                       0.590 |
| signal_stale_plus21        |  42 |                       0.538 |                     0.597 |                       0.607 |
| signal_from_future_minus21 |  21 |                       0.496 |                     0.552 |                       0.590 |
| signal_from_future_minus21 |  42 |                       0.482 |                     0.627 |                       0.607 |
| signal_from_future_minus63 |  21 |                       0.542 |                     0.587 |                       0.590 |
| signal_from_future_minus63 |  42 |                       0.520 |                     0.630 |                       0.607 |

(1) and (2) for the reaction functions (ordered logit, accuracy on all out-of-sample decisions): policy labels shuffled inside every training window; every publication lag 365 days longer; every publication lag 182 days SHORTER (a deliberate look-ahead: the Fed's 3- and 6-month targets gain 5-7 points, the meeting target and the ECB do not, i.e. what limits these models is the instability of the relation, not the timeliness of the data); the model without the NFCI (revision risk: no difference).

| bank   | target   | period    |   baseline |   policy_labels_shuffled_in_training |   features_365_days_staler |   lookahead_control_features_from_182_days_ahead |   without_nfci |
|:-------|:---------|:----------|-----------:|-------------------------------------:|---------------------------:|-------------------------------------------------:|---------------:|
| fed    | next     | 1996-2026 |      0.710 |                                0.579 |                      0.698 |                                            0.702 |          0.694 |
| fed    | m3       | 1990-2026 |      0.478 |                                0.353 |                      0.465 |                                            0.544 |          0.487 |
| fed    | m6       | 1990-2026 |      0.452 |                                0.248 |                      0.351 |                                            0.500 |          0.452 |
| ecb    | next     | 2004-2026 |      0.797 |                                0.749 |                      0.797 |                                            0.767 |          0.797 |
| ecb    | m3       | 2004-2026 |      0.657 |                                0.469 |                      0.605 |                                            0.561 |          0.657 |
| ecb    | m6       | 2004-2026 |      0.448 |                                0.340 |                      0.437 |                                            0.455 |          0.448 |

(4) Truncation test: `policy_state` rebuilt from raw data cut at three dates; every numeric column of every row up to the cut is compared with the full-history table (phases, model probabilities, priced path, gaps).

| cut        |   rows_compared |   max_abs_diff_numeric |   cells_nan_mismatch |   phase_mismatch |
|:-----------|----------------:|-----------------------:|---------------------:|-----------------:|
| 2012-06-29 |            8223 |               7.11e-15 |                    0 |                0 |
| 2019-03-29 |           10687 |               0.00e+00 |                    0 |                0 |
| 2024-09-30 |           12699 |               7.11e-15 |                    0 |                0 |

(3) Top features: see the coefficient table in section 1. The reaction functions never see an exchange rate; the FX signals are fixed-sign rules, so no feature can be an FX label in disguise.

## 5. Variant count, caveats

* **Exchange-rate candidates: 10** (limit 12), each with one declared vote form; the other vote form of the five sparse signals is tabulated and not selectable (strict count 15). Not candidates: the timing placebo (20 shifted copies), 3 label shuffles, 5 staleness / look-ahead shifts, one 0.6-pip re-costing.
* Reaction functions (no exchange rate involved): 2 banks x 3 targets x (ordered logit, Taylor-type rule) + 2 x 2 market / combined models, one Bundesbank line, and the diagnostics table added after the first run (4 feature-block variants and 2 penalties per bank and target; nothing was adopted from it: the declared model is the one used everywhere).
* Added after the first run and labelled as such: the diagnostics table, the 'departs from persistence' table, and a fix that keeps pre-2003 turning points out of the first 63 sessions of `turn63` (2003 is outside every evaluated period). Candidates, signals, selection rule and success test are exactly as declared in the module docstring before the first result.
* The 2026 policy history in the mirrors (ECB hikes of 2026-06 and 2026-09, Fed hike of 2026-09) is taken as given.
* The market-priced path is a 2-year yield minus the policy rate. It mixes a term premium and two years of expectations; proper pricing (OIS / futures strips) is not reachable from here (see arm H). That limits the 'economy vs priced' test.
