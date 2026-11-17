# The vote: 100 bots, direction and levels

Code `src/eurusd/bots.py` (design declared in its docstring before the first run, 2026-11-17), test `experiments/72_bots.py`, results `experiments/results/arms/bots_*`.

**Weights: the equal vote stays** (track record minus equal, every vote: +3.7 / -1.3 points at 21 sessions in 2010-17 / 2018-26, +1.8 / -1.9 at 63).
**Levels: see table** against the declared test (each level holds within 4 points of 80 % in every era).

## What a vote was worth (equal weights, walk-forward, out of sample)

`n_indep` = independent votes (sessions divided by the horizon); `lo`-`hi` = 95 % range; `share_of_days` = how often the vote was in that class.

### 5 sessions

| cls           | era     |   n_indep |   acc |   lo |   hi |   per_year |   share_of_days |
|:--------------|:--------|----------:|------:|-----:|-----:|-----------:|----------------:|
| thin          | 2010-26 |     294.4 |  51.3 | 45.7 | 57   |       17.3 |            33.7 |
| thin          | 2016-26 |     201.2 |  49.1 | 42.4 | 56.1 |       18.3 |            35.8 |
| thin          | 2023-26 |      46   |  45.7 | 32.2 | 59.8 |       11.5 |            23.1 |
| fair          | 2010-26 |     270.6 |  48.3 | 42.5 | 54.3 |       15.9 |            31   |
| fair          | 2016-26 |     193.6 |  49.9 | 43   | 57   |       17.6 |            34.4 |
| fair          | 2023-26 |      70   |  52.6 | 41.3 | 64.1 |       17.5 |            35.2 |
| wide          | 2010-26 |     197.4 |  50.1 | 43.3 | 57.2 |       11.6 |            22.6 |
| wide          | 2016-26 |     142.6 |  45.3 | 37.5 | 53.6 |       13   |            25.4 |
| wide          | 2023-26 |      76.6 |  46.7 | 36   | 57.8 |       19.2 |            38.5 |
| very wide     | 2010-26 |      93.6 |  53.6 | 43.2 | 63   |        5.5 |            10.7 |
| very wide     | 2016-26 |      12.8 |  57.8 | 29.1 | 76.8 |        1.2 |             2.3 |
| very wide     | 2023-26 |       3.8 |  42.1 | 15   | 85   |        1   |             1.9 |
| fair or wider | 2010-26 |     561.6 |  49.8 | 45.7 | 53.9 |       33   |            64.3 |
| fair or wider | 2016-26 |     349   |  48.3 | 43.2 | 53.7 |       31.7 |            62.1 |
| fair or wider | 2023-26 |     150.4 |  49.3 | 41.4 | 57.3 |       37.6 |            75.6 |
| every vote    | 2010-26 |     856   |  50.3 | 47   | 53.7 |       50.4 |            98   |
| every vote    | 2016-26 |     550.2 |  48.6 | 44.4 | 52.7 |       50   |            97.8 |
| every vote    | 2023-26 |     196.4 |  48.5 | 41.6 | 55.4 |       49.1 |            98.7 |

### 21 sessions

| cls           | era     |   n_indep |   acc |   lo |   hi |   per_year |   share_of_days |
|:--------------|:--------|----------:|------:|-----:|-----:|-----------:|----------------:|
| thin          | 2010-26 |      75.1 |  51.5 | 40.9 | 62.9 |        4.4 |            36.2 |
| thin          | 2016-26 |      50.4 |  50   | 36.6 | 63.4 |        4.6 |            37.9 |
| thin          | 2023-26 |       9.8 |  50.2 | 23.7 | 76.3 |        2.4 |            20.9 |
| fair          | 2010-26 |      56.4 |  49.7 | 37.3 | 62.7 |        3.3 |            27.2 |
| fair          | 2016-26 |      39.1 |  53.3 | 38.6 | 68.4 |        3.6 |            29.4 |
| fair          | 2023-26 |      14.8 |  54.2 | 30.1 | 75.2 |        3.7 |            31.7 |
| wide          | 2010-26 |      48.8 |  53.6 | 39.4 | 66.3 |        2.9 |            23.5 |
| wide          | 2016-26 |      30.3 |  49.5 | 33.2 | 66.8 |        2.8 |            22.8 |
| wide          | 2023-26 |      15.4 |  42.7 | 24.8 | 69.9 |        3.8 |            33   |
| very wide     | 2010-26 |      21.9 |  55.9 | 34.7 | 73.1 |        1.3 |            10.6 |
| very wide     | 2016-26 |       9.9 |  41.8 | 16.8 | 68.7 |        0.9 |             7.4 |
| very wide     | 2023-26 |       5.9 |  34.7 |  9.7 | 70   |        1.5 |            12.7 |
| fair or wider | 2010-26 |     127   |  52.3 | 43.3 | 60.5 |        7.5 |            61.3 |
| fair or wider | 2016-26 |      79.3 |  50.4 | 39.8 | 61.4 |        7.2 |            59.6 |
| fair or wider | 2023-26 |      36   |  46.1 | 32   | 63   |        9   |            77.3 |
| every vote    | 2010-26 |     202.1 |  52   | 45.1 | 58.8 |       11.9 |            97.5 |
| every vote    | 2016-26 |     129.8 |  50.3 | 41.5 | 58.5 |       11.8 |            97.5 |
| every vote    | 2023-26 |      45.8 |  47   | 34.1 | 61.9 |       11.5 |            98.3 |

### 63 sessions

| cls           | era     |   n_indep |   acc |   lo |   hi |   per_year |   share_of_days |
|:--------------|:--------|----------:|------:|-----:|-----:|-----------:|----------------:|
| thin          | 2010-26 |      20.8 |  51.9 | 32.4 | 71.7 |        1.2 |            30.5 |
| thin          | 2016-26 |      18.4 |  57.5 | 38.6 | 79.7 |        1.7 |            42.1 |
| thin          | 2023-26 |       4.7 |  68.5 | 23.1 | 88.2 |        1.2 |            31.5 |
| fair          | 2010-26 |      19.6 |  49.2 | 29.9 | 70.1 |        1.2 |            28.6 |
| fair          | 2016-26 |      14.2 |  56.3 | 32.6 | 78.6 |        1.3 |            32.4 |
| fair          | 2023-26 |       3.8 |  51.5 | 15   | 85   |        0.9 |            25.3 |
| wide          | 2010-26 |      14.2 |  59.2 | 32.6 | 78.6 |        0.8 |            20.8 |
| wide          | 2016-26 |       6.7 |  58.1 | 25   | 84.2 |        0.6 |            15.3 |
| wide          | 2023-26 |       3.6 |  58.8 | 15   | 85   |        0.9 |            24.3 |
| very wide     | 2010-26 |      12.5 |  55.1 | 29.1 | 76.8 |        0.7 |            18.3 |
| very wide     | 2016-26 |       3.3 |  43.6 |  6.1 | 79.2 |        0.3 |             7.7 |
| very wide     | 2023-26 |       2.7 |  37.4 |  6.1 | 79.2 |        0.7 |            18.2 |
| fair or wider | 2010-26 |      46.3 |  53.9 | 40.2 | 67.8 |        2.7 |            67.7 |
| fair or wider | 2016-26 |      24.2 |  55   | 35.1 | 72.1 |        2.2 |            55.3 |
| fair or wider | 2023-26 |      10.1 |  50.3 | 23.7 | 76.3 |        2.5 |            67.9 |
| every vote    | 2010-26 |      67.1 |  53.2 | 41.9 | 65.1 |        3.9 |            98.1 |
| every vote    | 2016-26 |      42.6 |  56.1 | 41.1 | 69.6 |        3.9 |            97.4 |
| every vote    | 2023-26 |      14.8 |  56.1 | 30.1 | 75.2 |        3.7 |            99.4 |

## Is the count a probability? Share of sessions that went UP, by number of UP votes (2010-26)

|   h | up_votes   |   went_up |   sessions |   n_indep |
|----:|:-----------|----------:|-----------:|----------:|
|   5 | 0-19       |      48.6 |         37 |       7.4 |
|   5 | 20-29      |      53.3 |        522 |     104.4 |
|   5 | 30-39      |      50.3 |        870 |     174   |
|   5 | 40-49      |      44.3 |        929 |     185.8 |
|   5 | 50-59      |      43.5 |        722 |     144.4 |
|   5 | 60-69      |      44.8 |        471 |      94.2 |
|   5 | 70-79      |      55.2 |        400 |      80   |
|   5 | 80-100     |      53.7 |        415 |      83   |
|  21 | 0-19       |      55.8 |        156 |       7.4 |
|  21 | 20-29      |      49.9 |        401 |      19.1 |
|  21 | 30-39      |      46.5 |        780 |      37.1 |
|  21 | 40-49      |      42.4 |       1027 |      48.9 |
|  21 | 50-59      |      44.9 |        750 |      35.7 |
|  21 | 60-69      |      36.8 |        372 |      17.7 |
|  21 | 70-79      |      56.9 |        578 |      27.5 |
|  21 | 80-100     |      62.5 |        285 |      13.6 |
|  63 | 0-19       |      56.6 |        189 |       3   |
|  63 | 20-29      |      35.3 |        312 |       5   |
|  63 | 30-39      |      38.9 |        491 |       7.8 |
|  63 | 40-49      |      42.8 |        635 |      10.1 |
|  63 | 50-59      |      46.6 |        804 |      12.8 |
|  63 | 60-69      |      42   |        734 |      11.7 |
|  63 | 70-79      |      55   |        565 |       9   |
|  63 | 80-100     |      59.1 |        579 |       9.2 |

## Levels: how often they held

`lower_held` = the period's lowest price stayed above the lower level; `upper_held` = the highest stayed below the upper level; target 80 % each.

|   h | kind                                                | era     |   sessions |   n_indep |   lower_held |   upper_held |   both_held |   avg_width_pct |   worst_year_lower |   worst_year_upper |
|----:|:----------------------------------------------------|:--------|-----------:|----------:|-------------:|-------------:|------------:|----------------:|-------------------:|-------------------:|
|   5 | bots                                                | 2010-26 |       4368 |     873.6 |         79.1 |         80.7 |        60.3 |            2.83 |               70.9 |               69.2 |
|   5 | bots                                                | 2016-26 |       2812 |     562.4 |         80.5 |         79.4 |        60.6 |            2.52 |               72.7 |               69.2 |
|   5 | bots                                                | 2023-26 |        995 |     199   |         81.7 |         80.6 |        62.5 |            2.4  |               74.5 |               77.7 |
|   5 | no volatility scaling                               | 2010-26 |       4368 |     873.6 |         86.4 |         86.1 |        73   |            3.29 |               65.4 |               72.3 |
|   5 | no volatility scaling                               | 2016-26 |       2812 |     562.4 |         90.5 |         87.9 |        78.7 |            3.18 |               71.9 |               73.8 |
|   5 | no volatility scaling                               | 2023-26 |        995 |     199   |         91   |         89.3 |        80.3 |            3.05 |               89.8 |               81.5 |
|   5 | bots | volatility above its median                  | 2010-26 |       2184 |     436.8 |         81.3 |         83.2 |        65.1 |            3.56 |              nan   |              nan   |
|   5 | no volatility scaling | volatility above its median | 2010-26 |       2184 |     436.8 |         80   |         80   |        60.8 |            3.34 |              nan   |              nan   |
|   5 | bots | volatility below its median                  | 2010-26 |       2184 |     436.8 |         77   |         78.2 |        55.6 |            2.1  |              nan   |              nan   |
|   5 | no volatility scaling | volatility below its median | 2010-26 |       2184 |     436.8 |         92.9 |         92.1 |        85.2 |            3.24 |              nan   |              nan   |
|  21 | bots                                                | 2010-26 |       4352 |     207.2 |         78   |         82.1 |        60.8 |            5.84 |               58.1 |               62.5 |
|  21 | bots                                                | 2016-26 |       2796 |     133.1 |         80.3 |         79.9 |        61.2 |            5.16 |               66.2 |               62.5 |
|  21 | bots                                                | 2023-26 |        979 |      46.6 |         81.8 |         77   |        59.1 |            4.93 |               70   |               67.8 |
|  21 | no volatility scaling                               | 2010-26 |       4352 |     207.2 |         84.5 |         87   |        71.6 |            6.63 |               59.2 |               73.5 |
|  21 | no volatility scaling                               | 2016-26 |       2796 |     133.1 |         89.6 |         88.1 |        77.9 |            6.43 |               60   |               73.5 |
|  21 | no volatility scaling                               | 2023-26 |        979 |      46.6 |         91.6 |         87.6 |        79.3 |            6.17 |               85.5 |               76.9 |
|  21 | bots | volatility above its median                  | 2010-26 |       2176 |     103.6 |         81.5 |         85.9 |        67.5 |            7.36 |              nan   |              nan   |
|  21 | no volatility scaling | volatility above its median | 2010-26 |       2176 |     103.6 |         78.4 |         82.9 |        61.4 |            6.72 |              nan   |              nan   |
|  21 | bots | volatility below its median                  | 2010-26 |       2176 |     103.6 |         74.4 |         78.4 |        54   |            4.32 |              nan   |              nan   |
|  21 | no volatility scaling | volatility below its median | 2010-26 |       2176 |     103.6 |         90.5 |         91.1 |        81.8 |            6.53 |              nan   |              nan   |
|  63 | bots                                                | 2010-26 |       4310 |      68.4 |         78   |         82.3 |        61.5 |           10.61 |               33.3 |               39.2 |
|  63 | bots                                                | 2016-26 |       2754 |      43.7 |         81.8 |         77   |        60.7 |            9.29 |               52.7 |               39.2 |
|  63 | bots                                                | 2023-26 |        937 |      14.9 |         89.1 |         73.6 |        63.8 |            8.96 |               77   |               59.2 |
|  63 | no volatility scaling                               | 2010-26 |       4310 |      68.4 |         83   |         89.6 |        72.6 |           12.5  |               47.7 |               63.3 |
|  63 | no volatility scaling                               | 2016-26 |       2754 |      43.7 |         90.3 |         89.5 |        79.8 |           11.98 |               50   |               63.3 |
|  63 | no volatility scaling                               | 2023-26 |        937 |      14.9 |         93   |         91.8 |        84.7 |           11.36 |               78.2 |               71.9 |
|  63 | bots | volatility above its median                  | 2010-26 |       2155 |      34.2 |         80.4 |         87.4 |        67.7 |           13.4  |              nan   |              nan   |
|  63 | no volatility scaling | volatility above its median | 2010-26 |       2155 |      34.2 |         75.5 |         84.3 |        59.9 |           12.72 |              nan   |              nan   |
|  63 | bots | volatility below its median                  | 2010-26 |       2155 |      34.2 |         75.5 |         77.1 |        55.2 |            7.82 |              nan   |              nan   |
|  63 | no volatility scaling | volatility below its median | 2010-26 |       2155 |      34.2 |         90.4 |         94.9 |        85.3 |           12.29 |              nan   |              nan   |

## Equal vote against track-record weights

| weights      |   h | era     |   n_indep |   acc |   lo |   hi |
|:-------------|----:|:--------|----------:|------:|-----:|-----:|
| equal        |   5 | 2010-26 |     856   |  50.3 | 47   | 53.7 |
| equal        |   5 | 2016-26 |     550.2 |  48.6 | 44.4 | 52.7 |
| equal        |   5 | 2023-26 |     196.4 |  48.5 | 41.6 | 55.4 |
| equal        |   5 | 2010-17 |     407.2 |  51.8 | 47   | 56.7 |
| equal        |   5 | 2018-26 |     448.8 |  49   | 44.4 | 53.6 |
| track record |   5 | 2010-26 |     873.2 |  50.7 | 47.4 | 54.1 |
| track record |   5 | 2016-26 |     562.2 |  49.5 | 45.4 | 53.6 |
| track record |   5 | 2023-26 |     198.8 |  49   | 41.9 | 55.6 |
| track record |   5 | 2010-17 |     414.6 |  51.9 | 47   | 56.6 |
| track record |   5 | 2018-26 |     458.6 |  49.6 | 45.1 | 54.2 |
| equal        |  21 | 2010-26 |     202.1 |  52   | 45.1 | 58.8 |
| equal        |  21 | 2016-26 |     129.8 |  50.3 | 41.5 | 58.5 |
| equal        |  21 | 2023-26 |      45.8 |  47   | 34.1 | 61.9 |
| equal        |  21 | 2010-17 |      96.5 |  52.3 | 42.2 | 61.8 |
| equal        |  21 | 2018-26 |     105.7 |  51.7 | 42.5 | 61.2 |
| track record |  21 | 2010-26 |     207.1 |  53   | 46.3 | 59.8 |
| track record |  21 | 2016-26 |     133   |  51.1 | 42.7 | 59.5 |
| track record |  21 | 2023-26 |      46.6 |  46.3 | 33.3 | 60.8 |
| track record |  21 | 2010-17 |      98.7 |  56   | 45.7 | 65   |
| track record |  21 | 2018-26 |     108.4 |  50.4 | 41.6 | 60.2 |
| equal        |  63 | 2010-26 |      67.1 |  53.2 | 41.9 | 65.1 |
| equal        |  63 | 2016-26 |      42.6 |  56.1 | 41.1 | 69.6 |
| equal        |  63 | 2023-26 |      14.8 |  56.1 | 30.1 | 75.2 |
| equal        |  63 | 2010-17 |      32.4 |  51.3 | 36.4 | 69.1 |
| equal        |  63 | 2018-26 |      34.8 |  55   | 38.2 | 69.5 |
| track record |  63 | 2010-26 |      68.4 |  53.1 | 41.2 | 64.3 |
| track record |  63 | 2016-26 |      43.7 |  55   | 40.1 | 68.3 |
| track record |  63 | 2023-26 |      14.9 |  54.7 | 30.1 | 75.2 |
| track record |  63 | 2010-17 |      32.9 |  53.1 | 35.2 | 67.5 |
| track record |  63 | 2018-26 |      35.5 |  53.1 | 38.2 | 69.5 |

## Stale vote, always-up, the agreement rule, and the bots one by one

| what                                                                                                                                  |   h | era     |   n_indep |   acc |    lo |    hi |
|:--------------------------------------------------------------------------------------------------------------------------------------|----:|:--------|----------:|------:|------:|------:|
| vote of 63 sessions ago (every vote)                                                                                                  |   5 | 2010-26 |     856   |  49   |  45.6 |  52.3 |
| vote of 63 sessions ago (fair or wider)                                                                                               |   5 | 2010-26 |     561.6 |  49.7 |  45.5 |  53.8 |
| always up                                                                                                                             |   5 | 2010-26 |     873.2 |  48.4 |  45.2 |  51.8 |
| vote of 63 sessions ago (every vote)                                                                                                  |   5 | 2016-26 |     549.2 |  49.3 |  45.2 |  53.5 |
| vote of 63 sessions ago (fair or wider)                                                                                               |   5 | 2016-26 |     340   |  50.9 |  45.6 |  56.2 |
| always up                                                                                                                             |   5 | 2016-26 |     562.2 |  49.2 |  45   |  53.2 |
| vote of 63 sessions ago (every vote)                                                                                                  |   5 | 2023-26 |     196.4 |  49.6 |  42.6 |  56.4 |
| vote of 63 sessions ago (fair or wider)                                                                                               |   5 | 2023-26 |     143.6 |  50.8 |  42.6 |  58.7 |
| always up                                                                                                                             |   5 | 2023-26 |     198.8 |  49.1 |  42.4 |  56.1 |
| single bots: median accuracy 50.0 %, best 54.1 %, worst 46.6 %, share above 50 %: 50 %; mean correlation between two bots' votes 0.13 |   5 | 2010-26 |     nan   |  50   | nan   | nan   |
| vote of 63 sessions ago (every vote)                                                                                                  |  21 | 2010-26 |     202.1 |  50.2 |  43.2 |  56.8 |
| vote of 63 sessions ago (fair or wider)                                                                                               |  21 | 2010-26 |     127.2 |  51.3 |  42.6 |  59.7 |
| always up                                                                                                                             |  21 | 2010-26 |     207.1 |  47.5 |  40.7 |  54.1 |
| vote of 63 sessions ago (every vote)                                                                                                  |  21 | 2016-26 |     129.6 |  47.9 |  39.3 |  56.2 |
| vote of 63 sessions ago (fair or wider)                                                                                               |  21 | 2016-26 |      77.3 |  51.4 |  41   |  62.7 |
| always up                                                                                                                             |  21 | 2016-26 |     133   |  49   |  40.5 |  57.3 |
| vote of 63 sessions ago (every vote)                                                                                                  |  21 | 2023-26 |      45.8 |  49.1 |  34.1 |  61.9 |
| vote of 63 sessions ago (fair or wider)                                                                                               |  21 | 2023-26 |      35.3 |  48   |  33   |  64.4 |
| always up                                                                                                                             |  21 | 2023-26 |      46.6 |  50.9 |  37.2 |  64.7 |
| single bots: median accuracy 50.9 %, best 60.6 %, worst 43.6 %, share above 50 %: 62 %; mean correlation between two bots' votes 0.13 |  21 | 2010-26 |     nan   |  50.9 | nan   | nan   |
| vote of 63 sessions ago (every vote)                                                                                                  |  63 | 2010-26 |      67.1 |  50   |  39.1 |  62.3 |
| vote of 63 sessions ago (fair or wider)                                                                                               |  63 | 2010-26 |      46.2 |  48.6 |  34.1 |  61.9 |
| always up                                                                                                                             |  63 | 2010-26 |      68.4 |  46.8 |  35.7 |  58.8 |
| vote of 63 sessions ago (every vote)                                                                                                  |  63 | 2016-26 |      42.6 |  51.6 |  36.8 |  65.4 |
| vote of 63 sessions ago (fair or wider)                                                                                               |  63 | 2016-26 |      24.2 |  50.6 |  31.4 |  68.6 |
| always up                                                                                                                             |  63 | 2016-26 |      43.7 |  46.5 |  31.7 |  59.9 |
| vote of 63 sessions ago (every vote)                                                                                                  |  63 | 2023-26 |      14.7 |  50.8 |  24.8 |  69.9 |
| vote of 63 sessions ago (fair or wider)                                                                                               |  63 | 2023-26 |       9.8 |  49.8 |  23.7 |  76.3 |
| always up                                                                                                                             |  63 | 2023-26 |      14.9 |  54   |  30.1 |  75.2 |
| single bots: median accuracy 52.1 %, best 62.4 %, worst 41.7 %, share above 50 %: 64 %; mean correlation between two bots' votes 0.17 |  63 | 2010-26 |     nan   |  52.1 | nan   | nan   |
| three-signal agreement rule                                                                                                           |   5 | 2010-26 |     384   |  56.2 |  51.3 |  61.1 |
| three-signal agreement rule                                                                                                           |   5 | 2016-26 |     242   |  55.1 |  48.7 |  61.1 |
| three-signal agreement rule                                                                                                           |   5 | 2023-26 |      84.4 |  56.2 |  45.3 |  66.1 |
| three-signal agreement rule                                                                                                           |  21 | 2010-26 |      90.8 |  58.3 |  48   |  67.8 |
| three-signal agreement rule                                                                                                           |  21 | 2016-26 |      57   |  58   |  45   |  69.8 |
| three-signal agreement rule                                                                                                           |  21 | 2023-26 |      19.5 |  53.5 |  31.7 |  72.7 |
| three-signal agreement rule                                                                                                           |  63 | 2010-26 |      29.9 |  66.7 |  48.8 |  80.8 |
| three-signal agreement rule                                                                                                           |  63 | 2016-26 |      18.7 |  67   |  41   |  80.9 |
| three-signal agreement rule                                                                                                           |  63 | 2023-26 |       6.1 |  51.7 |  18.8 |  81.2 |
