# Arm DA `bots_experience`: does more experience make the vote better?

Code `src/eurusd/arms/bots_experience.py` (design, bar and controls in its docstring before any outcome was computed, 2026-11-17). Results `experiments/results/arms/bots_experience_*.csv`.

## Verdict

**NOT ADOPTED. None of the three expanded trainings meets the declared bar** (at least +2 points over the EUR/USD-only bots at both 21 and 63 sessions in 2018-26, not worse in 2010-17, bootstrap interval excluding zero at one horizon).

| training                    |   gain_21_2018_26 |   gain_63_2018_26 |   gain_21_2010_17 |   gain_63_2010_17 | two_points_at_both   | not_worse_2010_17   | interval_excludes_zero_at_one   | ADOPTED   |
|:----------------------------|------------------:|------------------:|------------------:|------------------:|:---------------------|:--------------------|:--------------------------------|:----------|
| (b) + mark era 1987-98      |               0.1 |               0.2 |              -0.4 |               0.1 | False                | False               | False                           | False     |
| (c) + six other pairs 1999+ |              -8.3 |              -9.2 |              -7.4 |              -4.9 | False                | False               | True                            | False     |
| (d) all pairs 1987+         |              -6.8 |             -11   |              -5.4 |              -3.7 | False                | False               | True                            | False     |

Gains are accuracy points of the 100-bot majority on EUR/USD against baseline (a).

## What happened, plainly

* **More years (b): nothing.** Adding the Deutsche Mark era changes the vote by +0.1 / +0.2 points at 21 / 63 sessions in 2018-26 (intervals -1.1 .. +1.4 and -1.7 .. +2.2). Two reasons: 72 of the 100 bots have a 5- or 10-year memory and cannot see 1987-98 at all, and the 28 that can are, if anything, slightly worse with it (their own majority -1.4 / -1.9 points in 2018-26, intervals include zero). They keep trusting the same columns (positioning 24 % of what they keep, against 26 %).
* **More markets (c) and both (d): worse, not better.** The pooled bots' majority is 8.3 / 9.2 points (c) and 6.8 / 11.0 points (d) LESS accurate than the EUR/USD-only bots in 2018-26, and 7.4 / 4.9 and 5.4 / 3.7 points less in 2010-17. At 21 sessions the paired interval is entirely below zero in both halves; at 63 sessions it is wide and includes zero in 2018-26. The pooled vote on EUR/USD is 45.0 / 46.5 % in 2010-26, which is not distinguishable from 50 % (37.9-51.6 and 34.6-58.1).
* **Why pooling hurts here.** The bots do what the brief hoped: with seven markets they stop trusting positioning (26 % of kept columns under (a), 5 % under (c)), because it does not generalise. But they replace it with the global columns that every pair shares on the same date (US curve, VIX, equity, oil: 18 % to 37 %), where seven pairs moving together look like seven confirmations of one accident, and the bots agree with each other more (correlation of being right 0.22 to 0.28; share of single bots above 50 %: 65 % to 24 %). What they dropped was the only thing that had worked on EUR/USD in this sample; what they picked up did not carry forward.
* **The pooled vote works nowhere convincingly.** On the six other pairs it scores 48-52 % at 21 sessions in 2010-26 (every interval includes 50); the best cells (NZD 56 % at 63 sessions, CAD / AUD / NZD 54-56 % in 2018-26) are 6 pairs x 2 horizons x 2 eras read after the fact and none excludes 50 %.
* **The cost of the smaller evidence set is nil.** The same 100 bots on the 31 generic columns score 52.9 / 53.9 % at 21 / 63 sessions (2010-26) against 52.0 / 53.2 % for the product's bots on 74 EUR-specific columns; scored on the product's own closes 52.5 / 53.3 %. Neither is distinguishable from the other or from a coin.

## Anything suspicious

* **The noise floor is about 4 points.** On outcomes with no structure at all (sign-flipped returns) the same harness scores 50-54 % at 21 sessions. The baseline's 52.9 % sits inside that band. So the honest reading of the -8 points is "pooling is certainly not better, and probably worse", not "pooling predicts the wrong way".
* **The declared shuffle control came out at 46-49 %, not 50 %.** A permutation keeps the path's total change, which makes the past of a shuffled path slightly anti-informative about its future. The added sign-flip control has no such constraint and centres on 50-54 %. Both are reported.
* **The baseline's edge in 2018-26 (54.8 / 59.1 %) is where all of the candidates' deficit comes from**, and it rests on positioning columns chosen by bots on EUR/USD 2003-22, the one effect the research log says has no out-of-time support. A pooled learner that refuses it is arguably the more honest learner; it is still the less accurate one on this sample.
* **Docstring fact corrected after the run**: AUD positioning is usable from 1993-01, not 1988 (too few reports before); the roster has 28 all-history bots. Neither touches a candidate.
* **Evidence gaps that limit "more years / more markets"**: no 3-month interbank series for CHF before 1999-07 or JPY before 2002-04 (columns neutral there); NZD positioning has holes of up to 3.6 years in 2000-05; VIX starts 1990 and the Fed-meeting file 1989-07; the pre-1999 euro is a synthetic price via the Danish krone; the GBP rate series stops at 2026-01 on FRED (column neutral from 2026-05). US equity is the NASDAQ Composite because it is the only daily index here that spans 1971-2026.
* **Global columns have one sign for seven pairs.** Risk-off lifts the yen and franc and sinks the Australian dollar; a pooled bot with no pair identifier (as declared) can only learn the average. A design with pair groups might pool better; it was not declared and not run.
* The truncation control covers one fold (2018) for all four trainings at 21 and 63 sessions: 0 of 24,900 votes differ in each.

## The table: majority vote on EUR/USD, walk-forward, out of sample

`n_indep` = independent votes (sessions / horizon); `lo`-`hi` = Wilson 95 %; `diff` = accuracy minus baseline (a) on the same sessions, with a paired block-bootstrap 95 % interval. 5 sessions is reported, not judged.

### 21 sessions

| training                    | era     |   acc |   n_indep |   lo |   hi |   diff |   diff_lo |   diff_hi |
|:----------------------------|:--------|------:|----------:|-----:|-----:|-------:|----------:|----------:|
| (a) EUR/USD 1999+           | 2010-26 |  52.9 |     195.9 | 46.1 | 59.9 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           | 2016-26 |  55   |     124.9 | 46.5 | 63.6 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           | 2023-26 |  51.4 |      44.4 | 37.9 | 66.2 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           | 2010-17 |  50.9 |      93.6 | 41.1 | 60.9 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           | 2018-26 |  54.8 |     102.3 | 45.2 | 64.2 |    0   |     nan   |     nan   |
| (b) + mark era 1987-98      | 2010-26 |  52.8 |     196.5 | 46.1 | 59.9 |   -0.1 |      -1.8 |       1.4 |
| (b) + mark era 1987-98      | 2016-26 |  55.4 |     125.8 | 46.8 | 63.9 |    0.3 |      -2.1 |       2.5 |
| (b) + mark era 1987-98      | 2023-26 |  51.7 |      44.4 | 37.9 | 66.2 |    0.2 |      -1.3 |       1.8 |
| (b) + mark era 1987-98      | 2010-17 |  50.3 |      93.8 | 40.1 | 59.9 |   -0.4 |      -3.6 |       2.4 |
| (b) + mark era 1987-98      | 2018-26 |  55   |     102.7 | 44.8 | 63.7 |    0.1 |      -1.1 |       1.4 |
| (c) + six other pairs 1999+ | 2010-26 |  45   |     196.7 | 37.9 | 51.6 |   -7.8 |     -12.3 |      -3.6 |
| (c) + six other pairs 1999+ | 2016-26 |  44.7 |     125.6 | 36.1 | 53.2 |  -10.5 |     -16.7 |      -4.6 |
| (c) + six other pairs 1999+ | 2023-26 |  49.9 |      44.3 | 35.8 | 64.2 |   -1.4 |      -8.4 |       4.1 |
| (c) + six other pairs 1999+ | 2010-17 |  43.6 |      94   | 34   | 53.7 |   -7.4 |     -13.2 |      -2.1 |
| (c) + six other pairs 1999+ | 2018-26 |  46.2 |     102.7 | 36.3 | 55.2 |   -8.3 |     -15.4 |      -2   |
| (d) all pairs 1987+         | 2010-26 |  46.4 |     196.7 | 39.4 | 53.2 |   -6.1 |     -10.4 |      -2   |
| (d) all pairs 1987+         | 2016-26 |  46.5 |     125.5 | 37.6 | 54.7 |   -8   |     -14.2 |      -2.3 |
| (d) all pairs 1987+         | 2023-26 |  51.2 |      44.5 | 37.9 | 66.2 |   -0.2 |      -7.4 |       5.6 |
| (d) all pairs 1987+         | 2010-17 |  45.2 |      94.1 | 36   | 55.8 |   -5.4 |     -10.7 |      -0.5 |
| (d) all pairs 1987+         | 2018-26 |  47.6 |     102.6 | 38.2 | 57.1 |   -6.8 |     -13.8 |      -0.5 |

### 63 sessions

| training                    | era     |   acc |   n_indep |   lo |   hi |   diff |   diff_lo |   diff_hi |
|:----------------------------|:--------|------:|----------:|-----:|-----:|-------:|----------:|----------:|
| (a) EUR/USD 1999+           | 2010-26 |  53.9 |      65   | 41.9 | 65.4 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           | 2016-26 |  57.1 |      41.2 | 43.4 | 72.2 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           | 2023-26 |  55.9 |      14   | 32.6 | 78.6 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           | 2010-17 |  48.3 |      31.4 | 32   | 65.2 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           | 2018-26 |  59.1 |      33.6 | 42.2 | 73.6 |    0   |     nan   |     nan   |
| (b) + mark era 1987-98      | 2010-26 |  54   |      65.1 | 41.9 | 65.4 |    0.1 |      -1.1 |       1.4 |
| (b) + mark era 1987-98      | 2016-26 |  57.6 |      41.2 | 43.4 | 72.2 |    0.5 |      -1.3 |       2.4 |
| (b) + mark era 1987-98      | 2023-26 |  55.4 |      14   | 32.6 | 78.6 |   -0.1 |      -3.8 |       3.5 |
| (b) + mark era 1987-98      | 2010-17 |  48.3 |      31.4 | 32   | 65.2 |    0.1 |      -1.5 |       1.6 |
| (b) + mark era 1987-98      | 2018-26 |  59.3 |      33.7 | 42.2 | 73.6 |    0.2 |      -1.7 |       2.2 |
| (c) + six other pairs 1999+ | 2010-26 |  46.5 |      65.3 | 34.6 | 58.1 |   -7.1 |     -14.5 |      -0.7 |
| (c) + six other pairs 1999+ | 2016-26 |  45.8 |      41.4 | 32.1 | 61.3 |  -11   |     -22.2 |      -0.9 |
| (c) + six other pairs 1999+ | 2023-26 |  51   |      14.2 | 26.8 | 73.2 |   -5.2 |     -22.6 |       8.2 |
| (c) + six other pairs 1999+ | 2010-17 |  43.1 |      31.6 | 28.2 | 60.7 |   -4.9 |     -11.6 |       0.2 |
| (c) + six other pairs 1999+ | 2018-26 |  49.7 |      33.6 | 34.1 | 65.9 |   -9.2 |     -22.9 |       2.8 |
| (d) all pairs 1987+         | 2010-26 |  46.1 |      65   | 34.6 | 58.1 |   -7.5 |     -15.4 |      -0.8 |
| (d) all pairs 1987+         | 2016-26 |  45.2 |      41.2 | 32.1 | 61.3 |  -11.6 |     -23.6 |      -1.1 |
| (d) all pairs 1987+         | 2023-26 |  49.4 |      14.1 | 26.8 | 73.2 |   -6.7 |     -24.2 |       6.7 |
| (d) all pairs 1987+         | 2010-17 |  44   |      31.4 | 29.2 | 62.2 |   -3.7 |      -8.6 |      -0.3 |
| (d) all pairs 1987+         | 2018-26 |  48   |      33.6 | 31.5 | 63.3 |  -11   |     -25.6 |       1.7 |

### 5 sessions

| training                    | era     |   acc |   n_indep |   lo |   hi |   diff |   diff_lo |   diff_hi |
|:----------------------------|:--------|------:|----------:|-----:|-----:|-------:|----------:|----------:|
| (a) EUR/USD 1999+           | 2010-26 |  49.1 |     822.6 | 45.7 | 52.5 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           | 2016-26 |  48.8 |     529.4 | 44.7 | 53.2 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           | 2023-26 |  49   |     188   | 41.9 | 56   |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           | 2010-17 |  47.9 |     391.4 | 42.9 | 52.8 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           | 2018-26 |  50.1 |     431.2 | 45.4 | 54.8 |    0   |     nan   |     nan   |
| (b) + mark era 1987-98      | 2010-26 |  49.1 |     825.4 | 45.7 | 52.5 |   -0.1 |      -0.9 |       0.6 |
| (b) + mark era 1987-98      | 2016-26 |  49   |     529.6 | 44.8 | 53.3 |    0   |      -0.9 |       0.9 |
| (b) + mark era 1987-98      | 2023-26 |  49.2 |     188.6 | 42.2 | 56.3 |   -0.1 |      -1.1 |       0.6 |
| (b) + mark era 1987-98      | 2010-17 |  48   |     393.8 | 43.1 | 52.9 |    0.1 |      -1.2 |       1.3 |
| (b) + mark era 1987-98      | 2018-26 |  50   |     431.6 | 45.3 | 54.7 |   -0.3 |      -1.1 |       0.4 |
| (c) + six other pairs 1999+ | 2010-26 |  47.6 |     828.6 | 44.3 | 51.1 |   -1.3 |      -3.8 |       1.3 |
| (c) + six other pairs 1999+ | 2016-26 |  47.5 |     530.2 | 43.3 | 51.8 |   -1.3 |      -4.8 |       2.6 |
| (c) + six other pairs 1999+ | 2023-26 |  50.8 |     189.2 | 43.7 | 57.8 |    1.5 |      -4.7 |       8.7 |
| (c) + six other pairs 1999+ | 2010-17 |  47.6 |     393.6 | 42.6 | 52.4 |    0.2 |      -2.5 |       3   |
| (c) + six other pairs 1999+ | 2018-26 |  47.6 |     435   | 42.9 | 52.3 |   -2.6 |      -6.5 |       1.5 |
| (d) all pairs 1987+         | 2010-26 |  47.4 |     829.2 | 44   | 50.8 |   -1.6 |      -4.1 |       0.9 |
| (d) all pairs 1987+         | 2016-26 |  47.1 |     530.8 | 42.9 | 51.3 |   -1.9 |      -5.3 |       2   |
| (d) all pairs 1987+         | 2023-26 |  50.5 |     189   | 43.2 | 57.3 |    1.3 |      -4.9 |       8.1 |
| (d) all pairs 1987+         | 2010-17 |  47.2 |     395   | 42.2 | 52   |   -0.6 |      -3.3 |       2.1 |
| (d) all pairs 1987+         | 2018-26 |  47.6 |     434.2 | 43   | 52.4 |   -2.6 |      -6.5 |       1.4 |

## Bots that can actually see the extra years

A bot with a 5- or 10-year memory never sees 1987-98 from a 2010+ fold, so for those 72 bots (b) = (a) and (d) = (c) by construction (checked: largest difference in any P(up) 0.0e+00). Only the 28 all-history bots can use the mark era; their own majority:

| training                    |   h | era     |   acc |   n_indep |   lo |   hi |   diff |   diff_lo |   diff_hi |
|:----------------------------|----:|:--------|------:|----------:|-----:|-----:|-------:|----------:|----------:|
| (a) EUR/USD 1999+           |  21 | 2010-26 |  54.7 |     194.7 | 47.9 | 61.7 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           |  21 | 2016-26 |  55.1 |     126.1 | 46.8 | 63.9 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           |  21 | 2023-26 |  46.6 |      44   | 33.8 | 62.1 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           |  21 | 2010-17 |  56.7 |      92.1 | 46.3 | 66.2 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           |  21 | 2018-26 |  52.9 |     102.6 | 42.9 | 61.8 |    0   |     nan   |     nan   |
| (b) + mark era 1987-98      |  21 | 2010-26 |  53.3 |     194.7 | 46.3 | 60.2 |   -1.1 |      -3.7 |       1.8 |
| (b) + mark era 1987-98      |  21 | 2016-26 |  53.5 |     125.6 | 44.5 | 61.7 |   -1.5 |      -4   |       0.8 |
| (b) + mark era 1987-98      |  21 | 2023-26 |  47   |      44.2 | 33.8 | 62.1 |    0.9 |      -1.3 |       3.6 |
| (b) + mark era 1987-98      |  21 | 2010-17 |  55.4 |      92.3 | 45.3 | 65.2 |   -0.7 |      -5   |       4.6 |
| (b) + mark era 1987-98      |  21 | 2018-26 |  51.4 |     102.4 | 42.4 | 61.4 |   -1.4 |      -4.4 |       1.2 |
| (c) + six other pairs 1999+ |  21 | 2010-26 |  44.8 |     191.3 | 38.1 | 52.1 |   -9.1 |     -15.2 |      -3.3 |
| (c) + six other pairs 1999+ |  21 | 2016-26 |  44.1 |     120.2 | 35.6 | 53.1 |  -10.3 |     -17.1 |      -3.5 |
| (c) + six other pairs 1999+ |  21 | 2023-26 |  45   |      42.8 | 30.4 | 58.9 |   -0.9 |     -11.8 |      11.1 |
| (c) + six other pairs 1999+ |  21 | 2010-17 |  46.8 |      93.5 | 37.5 | 57.4 |   -9   |     -18.4 |      -0.5 |
| (c) + six other pairs 1999+ |  21 | 2018-26 |  42.9 |      97.8 | 33.5 | 52.7 |   -9.1 |     -16.8 |      -1.6 |
| (d) all pairs 1987+         |  21 | 2010-26 |  46.1 |     190.2 | 39.4 | 53.4 |   -8.2 |     -14.7 |      -2   |
| (d) all pairs 1987+         |  21 | 2016-26 |  46.5 |     120.4 | 38   | 55.6 |   -8.9 |     -16.9 |      -1.4 |
| (d) all pairs 1987+         |  21 | 2023-26 |  48.8 |      42.7 | 34.6 | 63.2 |    1.6 |     -11.2 |      13.6 |
| (d) all pairs 1987+         |  21 | 2010-17 |  47   |      92.4 | 36.9 | 56.9 |   -8.4 |     -18.5 |       0.1 |
| (d) all pairs 1987+         |  21 | 2018-26 |  45.3 |      97.8 | 35.4 | 54.8 |   -8   |     -16.8 |       0.2 |
| (a) EUR/USD 1999+           |  63 | 2010-26 |  50.5 |      64.3 | 38.1 | 61.9 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           |  63 | 2016-26 |  53.9 |      41   | 38.7 | 67.9 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           |  63 | 2023-26 |  50.8 |      14.1 | 26.8 | 73.2 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           |  63 | 2010-17 |  47.7 |      31.2 | 32   | 65.2 |    0   |     nan   |     nan   |
| (a) EUR/USD 1999+           |  63 | 2018-26 |  53.1 |      33.1 | 38   | 70.2 |    0   |     nan   |     nan   |
| (b) + mark era 1987-98      |  63 | 2010-26 |  49.6 |      63.5 | 38.1 | 61.9 |   -0.6 |      -3.8 |       2.2 |
| (b) + mark era 1987-98      |  63 | 2016-26 |  51.9 |      40   | 37.5 | 67.1 |   -1.4 |      -6.3 |       2.8 |
| (b) + mark era 1987-98      |  63 | 2023-26 |  50.5 |      13.5 | 26.8 | 73.2 |    0   |      -5   |       4.7 |
| (b) + mark era 1987-98      |  63 | 2010-17 |  48.8 |      31.4 | 32   | 65.2 |    0.6 |      -1.2 |       2.3 |
| (b) + mark era 1987-98      |  63 | 2018-26 |  50.4 |      32.1 | 33.6 | 66.4 |   -1.9 |      -8   |       3.4 |
| (c) + six other pairs 1999+ |  63 | 2010-26 |  46.6 |      61.8 | 34.9 | 59   |   -4.3 |     -11.7 |       2   |
| (c) + six other pairs 1999+ |  63 | 2016-26 |  46.2 |      38.3 | 32.5 | 62.7 |   -7.8 |     -19.6 |       2.1 |
| (c) + six other pairs 1999+ |  63 | 2023-26 |  56.7 |      13.2 | 29.1 | 76.8 |    5.3 |      -7.5 |      15.9 |
| (c) + six other pairs 1999+ |  63 | 2010-17 |  49.5 |      31   | 32   | 65.2 |    1   |      -2.5 |       4.8 |
| (c) + six other pairs 1999+ |  63 | 2018-26 |  43.6 |      30.7 | 26.4 | 59.2 |   -9.7 |     -24   |       2.3 |
| (d) all pairs 1987+         |  63 | 2010-26 |  46.1 |      62.5 | 34.3 | 58.2 |   -4.6 |     -13.8 |       3.6 |
| (d) all pairs 1987+         |  63 | 2016-26 |  44.3 |      39.1 | 29.3 | 59   |   -9.3 |     -23.6 |       3.6 |
| (d) all pairs 1987+         |  63 | 2023-26 |  52.4 |      13.3 | 29.1 | 76.8 |    3   |     -17.8 |      19.5 |
| (d) all pairs 1987+         |  63 | 2010-17 |  50.2 |      31.2 | 34.8 | 68   |    1.6 |      -1.5 |       5   |
| (d) all pairs 1987+         |  63 | 2018-26 |  42   |      31.3 | 26.4 | 59.2 |  -10.9 |     -28.8 |       4.6 |

## One bot at a time, and how alike the bots are (EUR/USD, 2010-26)

`corr_right` = mean correlation between two bots of being right; `corr_votes` = of their votes; `mean_majority_pct` = average size of the majority.

| training                    |   h | bots        |   median |   q25 |   q75 |   worst |   best |   share_above_50 |   corr_right |   corr_votes |   mean_majority_pct |
|:----------------------------|----:|:------------|---------:|------:|------:|--------:|-------:|-----------------:|-------------:|-------------:|--------------------:|
| (a) EUR/USD 1999+           |   5 | all 100     |     49.8 |  48.7 |  50.4 |    46.9 |   52.5 |             42   |        0.177 |        0.173 |              67.886 |
| (a) EUR/USD 1999+           |   5 | all-history |     50.1 |  48.6 |  50.4 |    47.7 |   51.9 |             53.6 |        0.269 |        0.26  |              73.642 |
| (b) + mark era 1987-98      |   5 | all 100     |     49.7 |  48.7 |  50.4 |    46.9 |   52.5 |             35   |        0.167 |        0.162 |              67.268 |
| (b) + mark era 1987-98      |   5 | all-history |     49.7 |  48.6 |  50.2 |    47.5 |   52.2 |             28.6 |        0.27  |        0.25  |              73.567 |
| (c) + six other pairs 1999+ |   5 | all 100     |     49.1 |  48.5 |  50   |    46.3 |   52.2 |             24   |        0.254 |        0.247 |              71.968 |
| (c) + six other pairs 1999+ |   5 | all-history |     48.9 |  48.4 |  49.2 |    47.4 |   51.7 |             14.3 |        0.257 |        0.2   |              72.503 |
| (d) all pairs 1987+         |   5 | all 100     |     49.5 |  48.8 |  50   |    46.3 |   52.2 |             26   |        0.236 |        0.23  |              71.157 |
| (d) all pairs 1987+         |   5 | all-history |     49.5 |  48.8 |  49.6 |    47.2 |   51.9 |             21.4 |        0.204 |        0.17  |              69.672 |
| (a) EUR/USD 1999+           |  21 | all 100     |     51.7 |  49.1 |  53.8 |    45   |   59.3 |             65   |        0.223 |        0.226 |              70.203 |
| (a) EUR/USD 1999+           |  21 | all-history |     53.3 |  51.3 |  54.3 |    47.5 |   58   |             78.6 |        0.323 |        0.331 |              76.206 |
| (b) + mark era 1987-98      |  21 | all 100     |     50.8 |  49.1 |  53.1 |    45   |   59.3 |             65   |        0.207 |        0.211 |              69.479 |
| (b) + mark era 1987-98      |  21 | all-history |     51.1 |  50.2 |  52.9 |    47   |   55.8 |             78.6 |        0.331 |        0.328 |              76.397 |
| (c) + six other pairs 1999+ |  21 | all 100     |     48.3 |  47.1 |  49.8 |    44.7 |   53   |             24   |        0.284 |        0.288 |              72.887 |
| (c) + six other pairs 1999+ |  21 | all-history |     47.3 |  46.1 |  48.4 |    45   |   49.8 |              0   |        0.257 |        0.243 |              72.626 |
| (d) all pairs 1987+         |  21 | all 100     |     48.6 |  47.2 |  50.3 |    44.7 |   53   |             28   |        0.272 |        0.272 |              72.455 |
| (d) all pairs 1987+         |  21 | all-history |     48   |  46.1 |  49.2 |    44.9 |   52.4 |             14.3 |        0.23  |        0.197 |              71.301 |
| (a) EUR/USD 1999+           |  63 | all 100     |     51   |  47.6 |  55.1 |    41.5 |   62.2 |             60   |        0.231 |        0.231 |              70.719 |
| (a) EUR/USD 1999+           |  63 | all-history |     50.1 |  46.8 |  53   |    42.3 |   57.1 |             50   |        0.339 |        0.266 |              76.491 |
| (b) + mark era 1987-98      |  63 | all 100     |     50.9 |  48   |  54.4 |    41.5 |   62.2 |             60   |        0.227 |        0.227 |              70.652 |
| (b) + mark era 1987-98      |  63 | all-history |     49.7 |  47.8 |  51   |    43   |   55.2 |             50   |        0.3   |        0.222 |              75.109 |
| (c) + six other pairs 1999+ |  63 | all 100     |     48.9 |  46.5 |  50.9 |    42.1 |   57.1 |             37   |        0.283 |        0.277 |              73     |
| (c) + six other pairs 1999+ |  63 | all-history |     48   |  46.1 |  48.8 |    43.2 |   51.6 |             14.3 |        0.277 |        0.186 |              71.881 |
| (d) all pairs 1987+         |  63 | all 100     |     49   |  46.8 |  51.1 |    40.2 |   57.1 |             38   |        0.278 |        0.275 |              73.061 |
| (d) all pairs 1987+         |  63 | all-history |     47.8 |  46.4 |  49.1 |    40.2 |   54.3 |             17.9 |        0.247 |        0.196 |              71.828 |

## What the bots chose to trust: share of kept columns by family

|   h | family        |   (a) EUR/USD 1999+ |   (b) + mark era 1987-98 |   (c) + six other pairs 1999+ |   (d) all pairs 1987+ |   share_of_the_31_columns |
|----:|:--------------|--------------------:|-------------------------:|------------------------------:|----------------------:|--------------------------:|
|   5 | Fed meetings  |                17.9 |                     17.3 |                          20.3 |                  18.3 |                      16.1 |
|   5 | dollar factor |                 6.6 |                      6.4 |                           7.9 |                   7.7 |                       6.5 |
|   5 | global        |                19.2 |                     20.9 |                          33.8 |                  32.4 |                      29   |
|   5 | own price     |                25.8 |                     27.3 |                          22.7 |                  25.7 |                      25.8 |
|   5 | positioning   |                19.9 |                     17.9 |                           6.7 |                   6.1 |                       9.7 |
|   5 | seasonality   |                 0.8 |                      0.8 |                           0.7 |                   0.6 |                       3.2 |
|   5 | short rates   |                 9.8 |                      9.4 |                           8   |                   9.2 |                       9.7 |
|  21 | Fed meetings  |                13.8 |                     14.7 |                          21.3 |                  20.3 |                      16.1 |
|  21 | dollar factor |                 5.9 |                      5.3 |                           5.3 |                   6.1 |                       6.5 |
|  21 | global        |                18.3 |                     20.2 |                          36.7 |                  36   |                      29   |
|  21 | own price     |                25.2 |                     25.7 |                          22.3 |                  23.2 |                      25.8 |
|  21 | positioning   |                25.8 |                     24.3 |                           4.6 |                   3.9 |                       9.7 |
|  21 | seasonality   |                 1.2 |                      1.5 |                           0.8 |                   0.9 |                       3.2 |
|  21 | short rates   |                 9.8 |                      8.3 |                           9.1 |                   9.7 |                       9.7 |
|  63 | Fed meetings  |                13.7 |                     15.7 |                          18.7 |                  18.4 |                      16.1 |
|  63 | dollar factor |                 3.8 |                      2.2 |                           4.4 |                   3.4 |                       6.5 |
|  63 | global        |                20.7 |                     25.2 |                          32.7 |                  34.7 |                      29   |
|  63 | own price     |                24.9 |                     21.7 |                          25.5 |                  23.7 |                      25.8 |
|  63 | positioning   |                24.4 |                     22.8 |                           5.3 |                   5.5 |                       9.7 |
|  63 | seasonality   |                 2   |                      2.1 |                           3.5 |                   4   |                       3.2 |
|  63 | short rates   |                10.5 |                     10.2 |                           9.9 |                  10.3 |                       9.7 |

Single columns kept most often (share of all kept slots, %, 21 sessions):

| col          |   (a) EUR/USD 1999+ |   (b) + mark era 1987-98 |   (c) + six other pairs 1999+ |   (d) all pairs 1987+ |
|:-------------|--------------------:|-------------------------:|------------------------------:|----------------------:|
| pos_z52      |                12.5 |                     11   |                           1.7 |                   1.4 |
| pos_z156     |                11.5 |                     12.1 |                           2.5 |                   2.2 |
| brk126       |                 7.3 |                      7.3 |                           2.8 |                   3   |
| fed_fx       |                 6.4 |                      6   |                           7   |                   7.4 |
| dist5y       |                 5.9 |                      5.7 |                           7.8 |                   7.7 |
| rd_lvl       |                 5.3 |                      4   |                           5.4 |                   5.6 |
| oil_r21      |                 3.8 |                      4.3 |                           5.8 |                   6.4 |
| mom126       |                 3.7 |                      2.8 |                           1.1 |                   1   |
| usdx21       |                 3.1 |                      2.7 |                           2.9 |                   3.3 |
| us_curve     |                 2.9 |                      1.8 |                           6.4 |                   6   |
| usdx63       |                 2.8 |                      2.6 |                           2.4 |                   2.8 |
| gold_r3      |                 2.8 |                      2.2 |                           4.4 |                   3.1 |
| rd_d3        |                 2.7 |                      2.6 |                           1.6 |                   2.1 |
| mom252       |                 2.7 |                      2.8 |                           3.2 |                   3.6 |
| fed_latest   |                 2.5 |                      3.8 |                           2.9 |                   3.8 |
| fed_priced   |                 2.3 |                      2.2 |                           4.7 |                   3.9 |
| stretch20    |                 2.2 |                      2.5 |                           1.8 |                   2   |
| vix_lvl      |                 2.1 |                      2   |                           5.3 |                   4.2 |
| eq_r21       |                 2   |                      2.6 |                           2.7 |                   2.9 |
| pos_d4       |                 1.9 |                      1.2 |                           0.4 |                   0.3 |
| rd_d6        |                 1.8 |                      1.8 |                           2   |                   2   |
| oil_r63      |                 1.7 |                      2.6 |                           3.8 |                   4.2 |
| mom21        |                 1.5 |                      1.8 |                           1.5 |                   1.4 |
| eq_r63       |                 1.5 |                      3.3 |                           5.3 |                   7.2 |
| fed_surprise |                 1.4 |                      1.5 |                           2.9 |                   2.7 |
| fed_cycle    |                 1.2 |                      1.3 |                           3.8 |                   2.5 |
| ma_state     |                 1.2 |                      1.9 |                           1.5 |                   1.4 |
| seas_month   |                 1.2 |                      1.5 |                           0.8 |                   0.9 |
| us2y_d20n    |                 1   |                      1   |                           2   |                   1.7 |
| mom63        |                 0.8 |                      0.9 |                           2.5 |                   3   |
| vix_d5       |                 0.5 |                      0.5 |                           0.9 |                   0.5 |

## The pooled (c) bots scored on every pair

The same pooled model; each pair's rows standardised on its own history. `always_up` = share of sessions the currency rose.

| pair   |   h | era     |   acc |   n_indep |   lo |   hi |   always_up |   median_bot |
|:-------|----:|:--------|------:|----------:|-----:|-----:|------------:|-------------:|
| eur    |  21 | 2010-26 |  45   |     196.7 | 37.9 | 51.6 |        47.3 |         48.3 |
| eur    |  21 | 2018-26 |  46.2 |     102.7 | 36.3 | 55.2 |        46.2 |         49.6 |
| gbp    |  21 | 2010-26 |  48.4 |     196.4 | 41.6 | 55.4 |        50.7 |         49.8 |
| gbp    |  21 | 2018-26 |  48.1 |     102.1 | 38.6 | 57.6 |        49.9 |         49.3 |
| jpy    |  21 | 2010-26 |  48.2 |     196.6 | 41.3 | 55.2 |        45.7 |         48.9 |
| jpy    |  21 | 2018-26 |  48.7 |     102.9 | 39.1 | 58.1 |        41.8 |         50.5 |
| chf    |  21 | 2010-26 |  49.6 |     196.6 | 42.8 | 56.7 |        51.9 |         49.5 |
| chf    |  21 | 2018-26 |  49.6 |     103   | 40.1 | 59   |        50.9 |         48.7 |
| cad    |  21 | 2010-26 |  50.6 |     196.7 | 43.8 | 57.7 |        48.2 |         49.6 |
| cad    |  21 | 2018-26 |  55.9 |     103.3 | 46.7 | 65.5 |        48   |         51.9 |
| aud    |  21 | 2010-26 |  51.7 |     196.8 | 44.8 | 58.7 |        49.1 |         49   |
| aud    |  21 | 2018-26 |  54.1 |     102.6 | 44.8 | 63.7 |        48.9 |         50.3 |
| nzd    |  21 | 2010-26 |  51.8 |     196.6 | 44.8 | 58.7 |        48.6 |         50.9 |
| nzd    |  21 | 2018-26 |  54.7 |     102.6 | 44.8 | 63.7 |        46.8 |         52   |
| eur    |  63 | 2010-26 |  46.5 |      65.3 | 34.6 | 58.1 |        46.5 |         48.9 |
| eur    |  63 | 2018-26 |  49.7 |      33.6 | 34.1 | 65.9 |        42.1 |         50.1 |
| gbp    |  63 | 2010-26 |  45.3 |      65.1 | 33.2 | 56.7 |        51   |         48.3 |
| gbp    |  63 | 2018-26 |  47.1 |      33.5 | 31.5 | 63.3 |        50.9 |         48.8 |
| jpy    |  63 | 2010-26 |  49.7 |      64.7 | 37.5 | 61.1 |        43.3 |         48.3 |
| jpy    |  63 | 2018-26 |  52.2 |      33.2 | 35.2 | 67.5 |        37.4 |         49.8 |
| chf    |  63 | 2010-26 |  48   |      64.8 | 36   | 59.6 |        53.9 |         50.5 |
| chf    |  63 | 2018-26 |  45.6 |      33.5 | 29.8 | 62   |        53.7 |         47.8 |
| cad    |  63 | 2010-26 |  47.3 |      65.3 | 36   | 59.6 |        43.5 |         48.4 |
| cad    |  63 | 2018-26 |  54.8 |      33.6 | 36.7 | 68.5 |        45.1 |         52.4 |
| aud    |  63 | 2010-26 |  50.8 |      64.8 | 38.9 | 62.5 |        47.6 |         48.8 |
| aud    |  63 | 2018-26 |  55.4 |      33.2 | 38   | 70.2 |        45.9 |         50.2 |
| nzd    |  63 | 2010-26 |  56.4 |      65.2 | 44.8 | 68.2 |        48.9 |         53.8 |
| nzd    |  63 | 2018-26 |  60.5 |      33.6 | 42.2 | 73.6 |        41.4 |         53.6 |

## Generic evidence against the product's own bots

| what                                                      |   h | era     |   n_indep |   acc |   lo |   hi |   diff |   diff_lo |   diff_hi |
|:----------------------------------------------------------|----:|:--------|----------:|------:|-----:|-----:|-------:|----------:|----------:|
| product bots (74 EUR-specific columns), product closes    |   5 | 2010-26 |     856   |  50.3 | 47   | 53.7 |  nan   |     nan   |     nan   |
| generic baseline (a), same votes scored on product closes |   5 | 2010-26 |     825.2 |  49   | 45.7 | 52.5 |   -1.3 |      -3.9 |       0.9 |
| generic baseline (a), H.10 fixings (this arm's scoring)   |   5 | 2010-26 |     822.6 |  49.1 | 45.7 | 52.5 |  nan   |     nan   |     nan   |
| product bots (74 EUR-specific columns), product closes    |   5 | 2016-26 |     550.2 |  48.6 | 44.4 | 52.7 |  nan   |     nan   |     nan   |
| generic baseline (a), same votes scored on product closes |   5 | 2016-26 |     531.4 |  49.3 | 45.1 | 53.6 |    0.8 |      -1.8 |       3.1 |
| generic baseline (a), H.10 fixings (this arm's scoring)   |   5 | 2016-26 |     529.4 |  48.8 | 44.7 | 53.2 |  nan   |     nan   |     nan   |
| product bots (74 EUR-specific columns), product closes    |   5 | 2023-26 |     196.4 |  48.5 | 41.6 | 55.4 |  nan   |     nan   |     nan   |
| generic baseline (a), same votes scored on product closes |   5 | 2023-26 |     189   |  49.5 | 42.7 | 56.8 |    1.7 |      -0.6 |       4.2 |
| generic baseline (a), H.10 fixings (this arm's scoring)   |   5 | 2023-26 |     188   |  49   | 41.9 | 56   |  nan   |     nan   |     nan   |
| product bots (74 EUR-specific columns), product closes    |  21 | 2010-26 |     202.1 |  52   | 45.1 | 58.8 |  nan   |     nan   |     nan   |
| generic baseline (a), same votes scored on product closes |  21 | 2010-26 |     195.9 |  52.5 | 45.6 | 59.4 |    0.7 |      -3.6 |       4.9 |
| generic baseline (a), H.10 fixings (this arm's scoring)   |  21 | 2010-26 |     195.9 |  52.9 | 46.1 | 59.9 |  nan   |     nan   |     nan   |
| product bots (74 EUR-specific columns), product closes    |  21 | 2016-26 |     129.8 |  50.3 | 41.5 | 58.5 |  nan   |     nan   |     nan   |
| generic baseline (a), same votes scored on product closes |  21 | 2016-26 |     124.9 |  55.3 | 46.5 | 63.6 |    5.2 |       0.2 |      10.3 |
| generic baseline (a), H.10 fixings (this arm's scoring)   |  21 | 2016-26 |     124.9 |  55   | 46.5 | 63.6 |  nan   |     nan   |     nan   |
| product bots (74 EUR-specific columns), product closes    |  21 | 2023-26 |      45.8 |  47   | 34.1 | 61.9 |  nan   |     nan   |     nan   |
| generic baseline (a), same votes scored on product closes |  21 | 2023-26 |      44.3 |  51.6 | 37.9 | 66.2 |    4.7 |      -0.1 |      10.6 |
| generic baseline (a), H.10 fixings (this arm's scoring)   |  21 | 2023-26 |      44.4 |  51.4 | 37.9 | 66.2 |  nan   |     nan   |     nan   |
| product bots (74 EUR-specific columns), product closes    |  63 | 2010-26 |      67.1 |  53.2 | 41.9 | 65.1 |  nan   |     nan   |     nan   |
| generic baseline (a), same votes scored on product closes |  63 | 2010-26 |      65.1 |  53.3 | 41.9 | 65.4 |    0.5 |      -4.1 |       5.5 |
| generic baseline (a), H.10 fixings (this arm's scoring)   |  63 | 2010-26 |      65   |  53.9 | 41.9 | 65.4 |  nan   |     nan   |     nan   |
| product bots (74 EUR-specific columns), product closes    |  63 | 2016-26 |      42.6 |  56.1 | 41.1 | 69.6 |  nan   |     nan   |     nan   |
| generic baseline (a), same votes scored on product closes |  63 | 2016-26 |      41.3 |  56.7 | 41   | 70.1 |    0.9 |      -6.6 |       8.9 |
| generic baseline (a), H.10 fixings (this arm's scoring)   |  63 | 2016-26 |      41.2 |  57.1 | 43.4 | 72.2 |  nan   |     nan   |     nan   |
| product bots (74 EUR-specific columns), product closes    |  63 | 2023-26 |      14.8 |  56.1 | 30.1 | 75.2 |  nan   |     nan   |     nan   |
| generic baseline (a), same votes scored on product closes |  63 | 2023-26 |      14.1 |  55.6 | 32.6 | 78.6 |   -0.5 |      -6.9 |       7   |
| generic baseline (a), H.10 fixings (this arm's scoring)   |  63 | 2023-26 |      14   |  55.9 | 32.6 | 78.6 |  nan   |     nan   |     nan   |

## Controls

| control                                       |   h | era     |   sessions |   n_indep |   acc |    lo |    hi | note                                                                              |
|:----------------------------------------------|----:|:--------|-----------:|----------:|------:|------:|------:|:----------------------------------------------------------------------------------|
| look-ahead column on every desk, training (a) |  21 | 2010-26 |       4187 |     199.4 |  99.9 |  98.1 | 100   | 100 % of bot-years kept it; median bot 99.1 %                                     |
| shuffled outcomes, seed 1, training (a)       |  21 | 2010-26 |       4127 |     196.5 |  47.1 |  40.4 |  54.2 | always-up on the same shuffled path 50.9 %; median bot 48.6 %                     |
| shuffled outcomes, seed 1, training (c)       |  21 | 2010-26 |       4121 |     196.2 |  45.8 |  39.1 |  52.9 | always-up on the same shuffled path 50.9 %; median bot 47.7 %                     |
| shuffled outcomes, seed 2, training (a)       |  21 | 2010-26 |       4124 |     196.4 |  46.7 |  40.1 |  53.9 | always-up on the same shuffled path 47.4 %; median bot 48.6 %                     |
| shuffled outcomes, seed 3, training (a)       |  21 | 2010-26 |       4141 |     197.2 |  48.9 |  41.8 |  55.7 | always-up on the same shuffled path 50.6 %; median bot 50.5 %                     |
| truncation at 2018-12-31, training (a)        |  21 | 2018    |        249 |     nan   | nan   | nan   | nan   | max |difference in P(up)| 0.00e+00; votes that differ 0 of 24900; rows 249 vs 249 |
| truncation at 2018-12-31, training (a)        |  63 | 2018    |        249 |     nan   | nan   | nan   | nan   | max |difference in P(up)| 0.00e+00; votes that differ 0 of 24900; rows 249 vs 249 |
| truncation at 2018-12-31, training (b)        |  21 | 2018    |        249 |     nan   | nan   | nan   | nan   | max |difference in P(up)| 0.00e+00; votes that differ 0 of 24900; rows 249 vs 249 |
| truncation at 2018-12-31, training (b)        |  63 | 2018    |        249 |     nan   | nan   | nan   | nan   | max |difference in P(up)| 0.00e+00; votes that differ 0 of 24900; rows 249 vs 249 |
| truncation at 2018-12-31, training (c)        |  21 | 2018    |        249 |     nan   | nan   | nan   | nan   | max |difference in P(up)| 0.00e+00; votes that differ 0 of 24900; rows 249 vs 249 |
| truncation at 2018-12-31, training (c)        |  63 | 2018    |        249 |     nan   | nan   | nan   | nan   | max |difference in P(up)| 0.00e+00; votes that differ 0 of 24900; rows 249 vs 249 |
| truncation at 2018-12-31, training (d)        |  21 | 2018    |        249 |     nan   | nan   | nan   | nan   | max |difference in P(up)| 0.00e+00; votes that differ 0 of 24900; rows 249 vs 249 |
| truncation at 2018-12-31, training (d)        |  63 | 2018    |        249 |     nan   | nan   | nan   | nan   | max |difference in P(up)| 0.00e+00; votes that differ 0 of 24900; rows 249 vs 249 |

Reconciliation: with one pair the pooled fold reproduces `bots.run_bot` bot for bot (largest difference in P(up) 0.0e+00 over 12 fold checks of 100 bots; same kept columns for every bot).
Pooling leak rule: 816 (training, horizon, year, pair) cells; training rows dated in or after the test year: 0; every training outcome fix is before 1 January of the test year (asserted for every bot and fold; table `bots_experience_pool_leak_check.csv`).

## Post-hoc checks (added after the declared run was read; descriptive)

Outcomes rebuilt from daily returns with random signs (no structure left, no fixed total): what the harness scores on pure noise.

| control                                                        |   h | era     |   sessions |   n_indep |   acc |   lo |   hi | note                                |
|:---------------------------------------------------------------|----:|:--------|-----------:|----------:|------:|-----:|-----:|:------------------------------------|
| outcomes from sign-flipped daily returns, seed 1, training (a) |  21 | 2010-26 |       4153 |     197.8 |  54.1 | 47.1 | 60.8 | always-up 50.5 %; median bot 51.9 % |
| outcomes from sign-flipped daily returns, seed 1, training (c) |  21 | 2010-26 |       4126 |     196.5 |  50   | 43.1 | 56.9 | always-up 50.5 %; median bot 51.2 % |
| outcomes from sign-flipped daily returns, seed 2, training (a) |  21 | 2010-26 |       4149 |     197.6 |  50.4 | 43.6 | 57.4 | always-up 50.0 %; median bot 49.6 % |
| outcomes from sign-flipped daily returns, seed 2, training (c) |  21 | 2010-26 |       4101 |     195.3 |  49.5 | 42.8 | 56.7 | always-up 50.0 %; median bot 49.4 % |
| outcomes from sign-flipped daily returns, seed 3, training (a) |  21 | 2010-26 |       4176 |     198.9 |  54.4 | 47.3 | 61   | always-up 54.8 %; median bot 53.4 % |
| outcomes from sign-flipped daily returns, seed 3, training (c) |  21 | 2010-26 |       4162 |     198.2 |  53.6 | 46.6 | 60.3 | always-up 54.8 %; median bot 52.4 % |

Vote direction on EUR/USD, 2010-26 (`up_share` = share of sessions the majority voted UP; `went_up` = share that rose):

| training                    |   h |   up_share |   went_up |   acc_when_up |   acc_when_down |   same_side_as_a |
|:----------------------------|----:|-----------:|----------:|--------------:|----------------:|-----------------:|
| (a) EUR/USD 1999+           |  21 |       45.8 |      47.4 |          50.3 |            55.1 |            100   |
| (b) + mark era 1987-98      |  21 |       49.9 |      47.4 |          50.1 |            55.4 |             93.9 |
| (c) + six other pairs 1999+ |  21 |       51.6 |      47.4 |          42.6 |            47.5 |             71.6 |
| (d) all pairs 1987+         |  21 |       52.2 |      47.3 |          44   |            49   |             72.3 |
| (a) EUR/USD 1999+           |  63 |       59   |      46.3 |          50.1 |            59.3 |            100   |
| (b) + mark era 1987-98      |  63 |       58.7 |      46.2 |          50.1 |            59.4 |             95.7 |
| (c) + six other pairs 1999+ |  63 |       52.9 |      46.5 |          43.4 |            50   |             79.3 |
| (d) all pairs 1987+         |  63 |       54.6 |      46.2 |          43   |            49.8 |             79.4 |

## Training rows

| training                    | eur        | gbp        | jpy        | chf        | cad        | aud        | nzd        |
|:----------------------------|:-----------|:-----------|:-----------|:-----------|:-----------|:-----------|:-----------|
| (a) EUR/USD 1999+           | 1999-01-04 |            |            |            |            |            |            |
| (b) + mark era 1987-98      | 1987-02-17 |            |            |            |            |            |            |
| (c) + six other pairs 1999+ | 1999-01-04 | 1999-01-04 | 1999-01-04 | 1999-01-04 | 1999-01-04 | 1999-01-04 | 1999-01-04 |
| (d) all pairs 1987+         | 1987-02-17 | 1987-02-17 | 1987-02-17 | 1987-02-17 | 1987-02-17 | 1993-01-04 | 1999-01-04 |

## Which column exists from when (first date; share of sessions present before / after 1999)

| column       | eur        | gbp        | jpy        | chf        | cad        | aud        | nzd        |
|:-------------|:-----------|:-----------|:-----------|:-----------|:-----------|:-----------|:-----------|
| pos_z52      | 1987-02-17 | 1987-02-17 | 1987-02-17 | 1987-02-17 | 1987-02-17 | 1993-01-04 | 2000-01-04 |
| pos_z156     | 1989-02-14 | 1989-02-14 | 1989-02-14 | 1989-02-14 | 1989-02-14 | 1993-07-20 | 2006-10-03 |
| pos_d4       | 1986-03-14 | 1986-03-14 | 1986-03-14 | 1986-03-14 | 1986-03-14 | 1987-09-14 | 1999-02-09 |
| rd_lvl       | 1986-01-02 | 1986-01-02 | 2002-05-16 | 1999-08-16 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| rd_d3        | 1986-01-02 | 1986-01-02 | 2002-08-15 | 1999-11-15 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| rd_d6        | 1986-01-02 | 1986-01-02 | 2002-11-15 | 2000-02-15 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| mom21        | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| mom63        | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| mom126       | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| mom252       | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| ma_state     | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| brk126       | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| dist5y       | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| stretch20    | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| usdx21       | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| usdx63       | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| vix_lvl      | 1990-01-03 | 1990-01-03 | 1990-01-03 | 1990-01-03 | 1990-01-03 | 1990-01-03 | 1990-01-03 |
| vix_d5       | 1990-01-10 | 1990-01-10 | 1990-01-10 | 1990-01-10 | 1990-01-10 | 1990-01-10 | 1990-01-10 |
| eq_r21       | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| eq_r63       | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| oil_r21      | 1986-02-04 | 1986-02-04 | 1986-02-04 | 1986-02-04 | 1986-02-04 | 1986-02-04 | 1986-02-04 |
| oil_r63      | 1986-04-04 | 1986-04-04 | 1986-04-04 | 1986-04-04 | 1986-04-04 | 1986-04-04 | 1986-04-04 |
| gold_r3      | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| us_curve     | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| us2y_d20n    | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| fed_latest   | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 |
| fed_cycle    | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 |
| fed_surprise | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 |
| fed_priced   | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |
| fed_fx       | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 | 1989-07-10 |
| seas_month   | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 | 1986-01-02 |

Share of 1987-98 sessions on which the column is present:

| column       |   eur |   gbp |   jpy |   chf |   cad |   aud |   nzd |
|:-------------|------:|------:|------:|------:|------:|------:|------:|
| pos_z52      | 0.997 | 0.997 | 0.997 | 0.997 | 0.997 | 0.503 | 0     |
| pos_z156     | 0.829 | 0.829 | 0.829 | 0.829 | 0.829 | 0.458 | 0     |
| pos_d4       | 1     | 1     | 1     | 1     | 1     | 0.705 | 0     |
| rd_lvl       | 1     | 1     | 0     | 0     | 1     | 1     | 1     |
| rd_d3        | 1     | 1     | 0     | 0     | 1     | 1     | 1     |
| rd_d6        | 1     | 1     | 0     | 0     | 1     | 1     | 1     |
| mom21        | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| mom63        | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| mom126       | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| mom252       | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| ma_state     | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| brk126       | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| dist5y       | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| stretch20    | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| usdx21       | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| usdx63       | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| vix_lvl      | 0.755 | 0.755 | 0.755 | 0.755 | 0.755 | 0.755 | 0.755 |
| vix_d5       | 0.753 | 0.753 | 0.753 | 0.753 | 0.753 | 0.753 | 0.753 |
| eq_r21       | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| eq_r63       | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| oil_r21      | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| oil_r63      | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| gold_r3      | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| us_curve     | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| us2y_d20n    | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| fed_latest   | 0.796 | 0.796 | 0.796 | 0.796 | 0.796 | 0.796 | 0.796 |
| fed_cycle    | 0.796 | 0.796 | 0.796 | 0.796 | 0.796 | 0.796 | 0.796 |
| fed_surprise | 0.796 | 0.796 | 0.796 | 0.796 | 0.796 | 0.796 | 0.796 |
| fed_priced   | 1     | 1     | 1     | 1     | 1     | 1     | 1     |
| fed_fx       | 0.796 | 0.796 | 0.796 | 0.796 | 0.796 | 0.796 | 0.796 |
| seas_month   | 1     | 1     | 1     | 1     | 1     | 1     | 1     |



## Answer to the owner's question

The bots' experience can be expanded, and it was: the same 100 bots were given the Deutsche Mark years back to 1987 and six other dollar pairs, on evidence that exists for all of them. It does not make the vote better: twelve more years change nothing (+0.1 / +0.2 points), and six more markets make the EUR/USD vote about 8 points worse, because the bots then drop positioning (the one thing that had worked on EUR/USD) for patterns shared by all pairs that did not carry forward. Nothing is adopted; the vote stays a coin flip of about 52-53 %, and the reason is the lack of information in public evidence, not a lack of experience.
