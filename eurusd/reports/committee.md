# The committee: 110 analysts (100 + a Fed desk of 10) vote on EUR/USD direction

Code `src/eurusd/committee.py`, test `experiments/70_committee.py`, results `experiments/results/arms/committee_*`.
Design, majority classes and keep bar were written into the module before the first run (2026-11-17). Trial 1: 100 analysts. Trial 2 (same day, owner's request): a Fed-meeting school of 10 analysts added, nothing else changed.

## Verdict against the declared bar: **FAIL**

|   h | era     |   committee clear+strong |   agreement rule |   gain pts |   calls/yr |   63-stale copy | >=3 pts   | >=6/yr   | stale loses half   |
|----:|:--------|-------------------------:|-----------------:|-----------:|-----------:|----------------:|:----------|:---------|:-------------------|
|  21 | 2010-26 |                     59   |             58.3 |        0.7 |        6.5 |            57.2 | False     | True     | False              |
|  21 | 2016-26 |                     55.8 |             58   |       -2.1 |        6.3 |            56.2 | False     | True     | False              |
|  42 | 2010-26 |                     63.1 |             63.3 |       -0.2 |        2.6 |            59.9 | False     | False    | False              |
|  42 | 2016-26 |                     59.1 |             62   |       -2.9 |        2.6 |            60   | False     | False    | False              |

## Effect of the Fed desk (clear or strong majority, with and without the 10 Fed analysts)

| who              |   h | era     |   n_indep |   acc |   lo |   hi |   per_year |
|:-----------------|----:|:--------|----------:|------:|-----:|-----:|-----------:|
| with Fed desk    |  21 | 2010-26 |     111   |  59   | 50.2 | 68.1 |        6.5 |
| with Fed desk    |  21 | 2016-26 |      69   |  55.8 | 44.8 | 67.6 |        6.3 |
| with Fed desk    |  21 | 2023-26 |      26.4 |  45   | 28.8 | 64.5 |        6.6 |
| with Fed desk    |  42 | 2010-26 |      44.6 |  63.1 | 47.6 | 74.9 |        2.6 |
| with Fed desk    |  42 | 2016-26 |      28.6 |  59.1 | 40.7 | 74.5 |        2.6 |
| with Fed desk    |  42 | 2023-26 |      11.7 |  42.9 | 19.3 | 68   |        2.9 |
| with Fed desk    |  63 | 2010-26 |      30.6 |  63.6 | 43.8 | 76.3 |        1.8 |
| with Fed desk    |  63 | 2016-26 |      18.7 |  63.8 | 41   | 80.9 |        1.7 |
| with Fed desk    |  63 | 2023-26 |       7.3 |  41.1 | 15.8 | 75   |        1.8 |
| without Fed desk |  21 | 2010-26 |     112.2 |  59.6 | 50.6 | 68.4 |        6.6 |
| without Fed desk |  21 | 2016-26 |      69.7 |  56.3 | 44.1 | 66.8 |        6.3 |
| without Fed desk |  21 | 2023-26 |      26.8 |  46.4 | 27.6 | 62.7 |        6.7 |
| without Fed desk |  42 | 2010-26 |      46.5 |  63.8 | 49.5 | 76   |        2.7 |
| without Fed desk |  42 | 2016-26 |      29.7 |  59.8 | 42.3 | 75.4 |        2.7 |
| without Fed desk |  42 | 2023-26 |      12.7 |  44.1 | 23.2 | 70.9 |        3.2 |
| without Fed desk |  63 | 2010-26 |      31.2 |  64.7 | 46.9 | 78.9 |        1.8 |
| without Fed desk |  63 | 2016-26 |      18.8 |  64.6 | 41   | 80.9 |        1.7 |
| without Fed desk |  63 | 2023-26 |       7.5 |  42.6 | 15.8 | 75   |        1.9 |

## The Fed desk on its own (majority of the Fed analysts with a view)

| who                          |   h | era     |   n_indep |   acc |   lo |   hi |   share_of_days |
|:-----------------------------|----:|:--------|----------:|------:|-----:|-----:|----------------:|
| Fed desk majority (any size) |  21 | 2010-26 |      59   |  42.5 | 30.6 | 55.1 |            28.5 |
| Fed desk majority (any size) |  21 | 2016-26 |      33.5 |  41.9 | 26.4 | 57.8 |            25.2 |
| Fed desk majority (any size) |  21 | 2023-26 |       8.9 |  40.9 | 18.9 | 73.3 |            19   |
| Fed desk majority (any size) |  42 | 2010-26 |      71.5 |  43.8 | 32.3 | 54.6 |            69.4 |
| Fed desk majority (any size) |  42 | 2016-26 |      34.5 |  40.5 | 25.6 | 56.4 |            52.3 |
| Fed desk majority (any size) |  42 | 2023-26 |      14.6 |  47.5 | 24.8 | 69.9 |            64.2 |
| Fed desk majority (any size) |  63 | 2010-26 |      55.5 |  49.4 | 35.7 | 61   |            81.2 |
| Fed desk majority (any size) |  63 | 2016-26 |      34.3 |  51.5 | 36.7 | 68.5 |            78.4 |
| Fed desk majority (any size) |  63 | 2023-26 |      12.5 |  56.5 | 32   | 80.7 |            84   |

## The ten Fed analysts one by one, 2010-26

| analyst        |   h |   n_indep |   acc |    lo |    hi |   share_of_days |
|:---------------|----:|----------:|------:|------:|------:|----------------:|
| fed_latest:D   |  21 |       0   | nan   | nan   | nan   |             0   |
| fed_latest:E   |  21 |       0   | nan   | nan   | nan   |             0   |
| fed_cycle:D    |  21 |      12.4 |  37.7 |  19.3 |  68   |             6   |
| fed_cycle:E    |  21 |       0   | nan   | nan   | nan   |             0   |
| fed_surprise:D |  21 |       3.6 |  26.7 |   4.6 |  69.9 |             1.7 |
| fed_surprise:E |  21 |       0   | nan   | nan   | nan   |             0   |
| fed_fx:D       |  21 |       0   | nan   | nan   | nan   |             0   |
| fed_fx:E       |  21 |       0   | nan   | nan   | nan   |             0   |
| fed_priced:D   |  21 |       8.9 |  40.9 |  18.9 |  73.3 |             4.3 |
| fed_priced:E   |  21 |      37   |  46.5 |  31   |  61.6 |            17.9 |
| fed_latest:D   |  42 |      11.2 |  37.7 |  15.2 |  64.6 |            10.9 |
| fed_latest:E   |  42 |       0   | nan   | nan   | nan   |             0   |
| fed_cycle:D    |  42 |      65.9 |  44   |  32.6 |  55.9 |            63.9 |
| fed_cycle:E    |  42 |       0   | nan   | nan   | nan   |             0   |
| fed_surprise:D |  42 |       1   |  20   |   0   |  79.3 |             0.9 |
| fed_surprise:E |  42 |       0   | nan   | nan   | nan   |             0   |
| fed_fx:D       |  42 |       0   | nan   | nan   | nan   |             0   |
| fed_fx:E       |  42 |       4.3 |  60.3 |  30.1 |  95.4 |             4.1 |
| fed_priced:D   |  42 |       5.4 |  30.7 |  11.8 |  76.9 |             5.3 |
| fed_priced:E   |  42 |       0   | nan   | nan   | nan   |             0   |
| fed_latest:D   |  63 |       4.7 |  11.5 |   3.6 |  62.4 |             6.8 |
| fed_latest:E   |  63 |       0   | nan   | nan   | nan   |             0   |
| fed_cycle:D    |  63 |      32.9 |  46.1 |  29.8 |  62   |            48.1 |
| fed_cycle:E    |  63 |       0   | nan   | nan   | nan   |             0   |
| fed_surprise:D |  63 |       0   | nan   | nan   | nan   |             0   |
| fed_surprise:E |  63 |       0   | nan   | nan   | nan   |             0   |
| fed_fx:D       |  63 |       0   | nan   | nan   | nan   |             0   |
| fed_fx:E       |  63 |       0   | nan   | nan   | nan   |             0   |
| fed_priced:D   |  63 |      26.3 |  54.4 |  35.5 |  71.2 |            38.4 |
| fed_priced:E   |  63 |      16.2 |  53.8 |  33.2 |  76.9 |            23.7 |

## What a majority was worth (walk-forward, out of sample)

`n_indep` = independent calls (calls on one non-overlapping grid, averaged over all grid phases); `lo`-`hi` = 95 % Wilson range on that count; `share_of_days` = how often the committee was in that class.

### Horizon 21 sessions

| cls          | era     |   n_days |   n_indep |   acc |   lo |   hi |   per_year |   share_of_days |
|:-------------|:--------|---------:|----------:|------:|-----:|-----:|-----------:|----------------:|
| split        | 2010-26 |      529 |      25.2 |  55.2 | 37.1 | 73.3 |        1.5 |            12.2 |
| split        | 2016-26 |      365 |      17.4 |  56.2 | 36   | 78.4 |        1.6 |            13.1 |
| split        | 2023-26 |      124 |       5.9 |  62.9 | 30   | 90.3 |        1.5 |            12.7 |
| lean         | 2010-26 |     1369 |      65.2 |  58.7 | 46.3 | 69.6 |        3.8 |            31.5 |
| lean         | 2016-26 |      911 |      43.4 |  57.8 | 43.3 | 71.6 |        3.9 |            32.6 |
| lean         | 2023-26 |      273 |      13   |  55.7 | 29.1 | 76.8 |        3.2 |            27.9 |
| clear        | 2010-26 |     1616 |      77   |  59.7 | 48.6 | 70   |        4.5 |            37.1 |
| clear        | 2016-26 |      987 |      47   |  56.8 | 43.3 | 70.5 |        4.3 |            35.3 |
| clear        | 2023-26 |      338 |      16.1 |  46.2 | 23.1 | 66.8 |        4   |            34.5 |
| strong       | 2010-26 |      715 |      34   |  57.6 | 42.2 | 73.6 |        2   |            16.4 |
| strong       | 2016-26 |      462 |      22   |  53.7 | 34.7 | 73.1 |        2   |            16.5 |
| strong       | 2023-26 |      217 |      10.3 |  43.3 | 16.8 | 68.7 |        2.6 |            22.2 |
| clear+strong | 2010-26 |     2331 |     111   |  59   | 50.2 | 68.1 |        6.5 |            53.6 |
| clear+strong | 2016-26 |     1449 |      69   |  55.8 | 44.8 | 67.6 |        6.3 |            51.8 |
| clear+strong | 2023-26 |      555 |      26.4 |  45   | 28.8 | 64.5 |        6.6 |            56.7 |
| any majority | 2010-26 |     4229 |     201.4 |  58.4 | 51.8 | 65.3 |       11.8 |            97.2 |
| any majority | 2016-26 |     2725 |     129.8 |  56.6 | 47.6 | 64.4 |       11.8 |            97.5 |
| any majority | 2023-26 |      952 |      45.3 |  50.4 | 37   | 65   |       11.3 |            97.2 |

### Horizon 42 sessions

| cls          | era     |   n_days |   n_indep |   acc |   lo |   hi |   per_year |   share_of_days |
|:-------------|:--------|---------:|----------:|------:|-----:|-----:|-----------:|----------------:|
| split        | 2010-26 |      611 |      14.5 |  51.6 | 30.1 | 75.2 |        0.9 |            14.1 |
| split        | 2016-26 |      424 |      10.1 |  51.7 | 23.7 | 76.3 |        0.9 |            15.3 |
| split        | 2023-26 |      104 |       2.5 |  52.9 |  9.5 | 90.5 |        0.6 |            10.9 |
| lean         | 2010-26 |     1681 |      40   |  57.4 | 42.2 | 71.5 |        2.4 |            38.8 |
| lean         | 2016-26 |     1061 |      25.3 |  56.6 | 37.1 | 73.3 |        2.3 |            38.2 |
| lean         | 2023-26 |      343 |       8.2 |  46.4 | 21.5 | 78.5 |        2   |            35.8 |
| clear        | 2010-26 |     1449 |      34.5 |  63.6 | 47.9 | 78.5 |        2   |            33.5 |
| clear        | 2016-26 |      905 |      21.5 |  60.2 | 38.7 | 76.7 |        2   |            32.6 |
| clear        | 2023-26 |      336 |       8   |  47.9 | 21.5 | 78.5 |        2   |            35.1 |
| strong       | 2010-26 |      425 |      10.1 |  61.2 | 31.3 | 83.2 |        0.6 |             9.8 |
| strong       | 2016-26 |      297 |       7.1 |  55.6 | 25   | 84.2 |        0.6 |            10.7 |
| strong       | 2023-26 |      156 |       3.7 |  32.1 |  4.6 | 69.9 |        0.9 |            16.3 |
| clear+strong | 2010-26 |     1874 |      44.6 |  63.1 | 47.6 | 74.9 |        2.6 |            43.3 |
| clear+strong | 2016-26 |     1202 |      28.6 |  59.1 | 40.7 | 74.5 |        2.6 |            43.3 |
| clear+strong | 2023-26 |      492 |      11.7 |  42.9 | 19.3 | 68   |        2.9 |            51.4 |
| any majority | 2010-26 |     4166 |      99.2 |  59.1 | 49.7 | 68.7 |        5.8 |            96.2 |
| any majority | 2016-26 |     2687 |      64   |  56.9 | 44.1 | 67.7 |        5.8 |            96.8 |
| any majority | 2023-26 |      939 |      22.4 |  45.3 | 26.9 | 65.3 |        5.6 |            98   |

### Horizon 63 sessions

| cls          | era     |   n_days |   n_indep |   acc |   lo |   hi |   per_year |   share_of_days |
|:-------------|:--------|---------:|----------:|------:|-----:|-----:|-----------:|----------------:|
| split        | 2010-26 |      710 |      11.3 |  56.8 | 28   | 78.7 |        0.7 |            16.5 |
| split        | 2016-26 |      475 |       7.5 |  57.7 | 21.5 | 78.5 |        0.7 |            17.2 |
| split        | 2023-26 |      124 |       2   |  60.5 |  9.5 | 90.5 |        0.5 |            13.2 |
| lean         | 2010-26 |     1501 |      23.8 |  64.4 | 42.7 | 78.8 |        1.4 |            34.8 |
| lean         | 2016-26 |     1009 |      16   |  63.7 | 38.6 | 81.5 |        1.5 |            36.6 |
| lean         | 2023-26 |      334 |       5.3 |  60.8 | 23.1 | 88.2 |        1.3 |            35.6 |
| clear        | 2010-26 |     1395 |      22.1 |  61.1 | 43   | 80.3 |        1.3 |            32.4 |
| clear        | 2016-26 |      809 |      12.8 |  59.3 | 35.5 | 82.3 |        1.2 |            29.4 |
| clear        | 2023-26 |      313 |       5   |  39   | 11.8 | 76.9 |        1.2 |            33.4 |
| strong       | 2010-26 |      532 |       8.4 |  69.9 | 40.9 | 92.9 |        0.5 |            12.3 |
| strong       | 2016-26 |      371 |       5.9 |  73.6 | 30   | 90.3 |        0.5 |            13.5 |
| strong       | 2023-26 |      144 |       2.3 |  45.8 |  9.5 | 90.5 |        0.6 |            15.4 |
| clear+strong | 2010-26 |     1927 |      30.6 |  63.6 | 43.8 | 76.3 |        1.8 |            44.7 |
| clear+strong | 2016-26 |     1180 |      18.7 |  63.8 | 41   | 80.9 |        1.7 |            42.8 |
| clear+strong | 2023-26 |      457 |       7.3 |  41.1 | 15.8 | 75   |        1.8 |            48.8 |
| any majority | 2010-26 |     4138 |      65.7 |  62.7 | 50.1 | 72.9 |        3.9 |            96   |
| any majority | 2016-26 |     2664 |      42.3 |  62.7 | 49.2 | 77   |        3.8 |            96.7 |
| any majority | 2023-26 |      915 |      14.5 |  50.9 | 24.8 | 69.9 |        3.6 |            97.7 |

## Benchmarks on the same folds

| who            |   h | era     |   n_indep |   acc |   lo |   hi |   per_year |   share_of_days |
|:---------------|----:|:--------|----------:|------:|-----:|-----:|-----------:|----------------:|
| agreement rule |  21 | 2010-26 |      90.8 |  58.3 | 48   | 67.8 |        5.3 |            43.8 |
| always long    |  21 | 2010-26 |     207.1 |  47.5 | 40.7 | 54.1 |       12.2 |            99.9 |
| agreement rule |  21 | 2016-26 |      57   |  58   | 45   | 69.8 |        5.2 |            42.8 |
| always long    |  21 | 2016-26 |     133   |  49   | 40.5 | 57.3 |       12.1 |            99.9 |
| agreement rule |  21 | 2023-26 |      19.5 |  53.5 | 31.7 | 72.7 |        4.9 |            41.8 |
| always long    |  21 | 2023-26 |      46.6 |  50.9 | 37.2 | 64.7 |       11.6 |            99.9 |
| agreement rule |  42 | 2010-26 |      44.9 |  63.3 | 47.6 | 74.9 |        2.6 |            43.5 |
| always long    |  42 | 2010-26 |     103.1 |  47.1 | 38.2 | 57.1 |        6.1 |           100   |
| agreement rule |  42 | 2016-26 |      28   |  62   | 42.4 | 76.4 |        2.5 |            42.5 |
| always long    |  42 | 2016-26 |      66.1 |  46.9 | 35.4 | 58.8 |        6   |           100   |
| agreement rule |  42 | 2023-26 |       9.3 |  47.4 | 18.9 | 73.3 |        2.3 |            40.7 |
| always long    |  42 | 2023-26 |      22.8 |  51.5 | 33   | 70.8 |        5.7 |           100   |
| agreement rule |  63 | 2010-26 |      29.9 |  66.7 | 48.8 | 80.8 |        1.8 |            43.7 |
| always long    |  63 | 2010-26 |      68.4 |  46.8 | 35.7 | 58.8 |        4   |           100   |
| agreement rule |  63 | 2016-26 |      18.7 |  67   | 41   | 80.9 |        1.7 |            42.7 |
| always long    |  63 | 2016-26 |      43.7 |  46.5 | 31.7 | 59.9 |        4   |           100   |
| agreement rule |  63 | 2023-26 |       6.1 |  51.7 | 18.8 | 81.2 |        1.5 |            41.3 |
| always long    |  63 | 2023-26 |      14.9 |  54   | 30.1 | 75.2 |        3.7 |           100   |

## Stale copies (the vote of 63 / 126 sessions ago, scored on today's outcome)

| who                 |   h | cls          | era     |   n_indep |   acc |   lo |   hi |
|:--------------------|----:|:-------------|:--------|----------:|------:|-----:|-----:|
| committee stale 63  |  21 | clear+strong | 2010-26 |     110.4 |  57.2 | 47.9 | 66.1 |
| committee stale 63  |  21 | clear+strong | 2016-26 |      67.7 |  56.2 | 44.1 | 67.1 |
| committee stale 63  |  21 | clear+strong | 2023-26 |      25.2 |  49.7 | 33.5 | 70   |
| committee stale 63  |  21 | any majority | 2010-26 |     201.4 |  54.3 | 47.3 | 61   |
| committee stale 63  |  21 | any majority | 2016-26 |     129.8 |  52.9 | 44.5 | 61.4 |
| committee stale 63  |  21 | any majority | 2023-26 |      45.3 |  48.6 | 35   | 63   |
| committee stale 63  |  42 | clear+strong | 2010-26 |      44.3 |  59.9 | 46.6 | 74.3 |
| committee stale 63  |  42 | clear+strong | 2016-26 |      27.7 |  60   | 42.4 | 76.4 |
| committee stale 63  |  42 | clear+strong | 2023-26 |      11.1 |  46.8 | 21.3 | 72   |
| committee stale 63  |  42 | any majority | 2010-26 |      99   |  54.3 | 44.8 | 64   |
| committee stale 63  |  42 | any majority | 2016-26 |      64   |  54.6 | 42.6 | 66.3 |
| committee stale 63  |  42 | any majority | 2023-26 |      22.4 |  45   | 26.9 | 65.3 |
| committee stale 63  |  63 | clear+strong | 2010-26 |      30.3 |  57.9 | 42.3 | 75.4 |
| committee stale 63  |  63 | clear+strong | 2016-26 |      18.1 |  64.7 | 43.7 | 83.7 |
| committee stale 63  |  63 | clear+strong | 2023-26 |       6.7 |  53   | 25   | 84.2 |
| committee stale 63  |  63 | any majority | 2010-26 |      65.7 |  55.6 | 42.6 | 66   |
| committee stale 63  |  63 | any majority | 2016-26 |      42.3 |  58.3 | 44.5 | 73   |
| committee stale 63  |  63 | any majority | 2023-26 |      14.5 |  49.4 | 24.8 | 69.9 |
| committee stale 126 |  21 | clear+strong | 2010-26 |     109.4 |  51.9 | 43   | 61.4 |
| committee stale 126 |  21 | clear+strong | 2016-26 |      65.3 |  52.2 | 40.4 | 64   |
| committee stale 126 |  21 | clear+strong | 2023-26 |      25   |  53.4 | 33.5 | 70   |
| committee stale 126 |  21 | any majority | 2010-26 |     201.4 |  49.1 | 42.4 | 56.1 |
| committee stale 126 |  21 | any majority | 2016-26 |     129.6 |  48.5 | 40   | 57   |
| committee stale 126 |  21 | any majority | 2023-26 |      45.3 |  49.4 | 35   | 63   |
| committee stale 126 |  42 | clear+strong | 2010-26 |      43.1 |  50.7 | 36.8 | 65.4 |
| committee stale 126 |  42 | clear+strong | 2016-26 |      26.5 |  50.9 | 35.5 | 71.2 |
| committee stale 126 |  42 | clear+strong | 2023-26 |      10.7 |  47.8 | 21.3 | 72   |
| committee stale 126 |  42 | any majority | 2010-26 |      98.7 |  53.3 | 43.8 | 63   |
| committee stale 126 |  42 | any majority | 2016-26 |      63.9 |  53.4 | 41.1 | 64.8 |
| committee stale 126 |  42 | any majority | 2023-26 |      22.4 |  46   | 26.9 | 65.3 |
| committee stale 126 |  63 | clear+strong | 2010-26 |      29.9 |  49.5 | 33.2 | 66.8 |
| committee stale 126 |  63 | clear+strong | 2016-26 |      17.6 |  52.4 | 29   | 71   |
| committee stale 126 |  63 | clear+strong | 2023-26 |       6.8 |  44.8 | 15.8 | 75   |
| committee stale 126 |  63 | any majority | 2010-26 |      65.6 |  52.3 | 39.7 | 63.2 |
| committee stale 126 |  63 | any majority | 2016-26 |      42.3 |  54   | 39.9 | 68.8 |
| committee stale 126 |  63 | any majority | 2023-26 |      14.5 |  44.7 | 19.8 | 64.3 |

## Does the committee add to the three-signal agreement rule?

|   h | era     | case                                              |   n_indep |   acc |    lo |    hi |   per_year |
|----:|:--------|:--------------------------------------------------|----------:|------:|------:|------:|-----------:|
|  21 | 2010-26 | rule calls, committee clear majority the same way |      62.5 |  59   |  47.3 |  71   |        3.7 |
|  21 | 2010-26 | rule calls, committee no clear majority           |      27.5 |  56.6 |  39.1 |  73.5 |        1.6 |
|  21 | 2010-26 | rule calls, committee clear majority AGAINST      |       0.8 |  62.5 |   0   |  79.3 |        0   |
|  21 | 2010-26 | rule silent, committee clear majority             |      47.8 |  59.4 |  44.3 |  71.2 |        2.8 |
|  21 | 2016-26 | rule calls, committee clear majority the same way |      37   |  59.7 |  43.5 |  73.7 |        3.4 |
|  21 | 2016-26 | rule calls, committee no clear majority           |      19.3 |  54.3 |  31.7 |  72.7 |        1.8 |
|  21 | 2016-26 | rule calls, committee clear majority AGAINST      |       0.7 |  66.7 |   0   |  79.3 |        0.1 |
|  21 | 2016-26 | rule silent, committee clear majority             |      31.3 |  51.8 |  34.8 |  68   |        2.8 |
|  21 | 2023-26 | rule calls, committee clear majority the same way |      14.5 |  50.8 |  24.8 |  69.9 |        3.6 |
|  21 | 2023-26 | rule calls, committee no clear majority           |       4.9 |  61.2 |  23.1 |  88.2 |        1.2 |
|  21 | 2023-26 | rule calls, committee clear majority AGAINST      |       0   | 100   |   0   |  79.3 |        0   |
|  21 | 2023-26 | rule silent, committee clear majority             |      11.9 |  38.2 |  19.3 |  68   |        3   |
|  42 | 2010-26 | rule calls, committee clear majority the same way |      27.2 |  63.3 |  44.2 |  78.5 |        1.6 |
|  42 | 2010-26 | rule calls, committee no clear majority           |      17.6 |  62.9 |  38.6 |  79.7 |        1   |
|  42 | 2010-26 | rule calls, committee clear majority AGAINST      |       0.1 | 100   |   0   |  79.3 |        0   |
|  42 | 2010-26 | rule silent, committee clear majority             |      17.3 |  63.2 |  41.3 |  82.7 |        1   |
|  42 | 2016-26 | rule calls, committee clear majority the same way |      16.6 |  62.5 |  36   |  78.4 |        1.5 |
|  42 | 2016-26 | rule calls, committee no clear majority           |      11.3 |  60.8 |  35.4 |  84.8 |        1   |
|  42 | 2016-26 | rule calls, committee clear majority AGAINST      |       0.1 | 100   |   0   |  79.3 |        0   |
|  42 | 2016-26 | rule silent, committee clear majority             |      11.9 |  54.9 |  32   |  80.7 |        1.1 |
|  42 | 2023-26 | rule calls, committee clear majority the same way |       5.9 |  42.1 |   9.7 |  70   |        1.5 |
|  42 | 2023-26 | rule calls, committee no clear majority           |       3.4 |  56.6 |  20.8 |  93.9 |        0.9 |
|  42 | 2023-26 | rule calls, committee clear majority AGAINST      |       0   | nan   | nan   | nan   |        0   |
|  42 | 2023-26 | rule silent, committee clear majority             |       5.8 |  43.7 |  18.8 |  81.2 |        1.5 |
|  63 | 2010-26 | rule calls, committee clear majority the same way |      19.4 |  66.1 |  46   |  84.6 |        1.1 |
|  63 | 2010-26 | rule calls, committee no clear majority           |      10.4 |  68   |  39.7 |  89.2 |        0.6 |
|  63 | 2010-26 | rule calls, committee clear majority AGAINST      |       0.1 |  25   |   0   |  79.3 |        0   |
|  63 | 2010-26 | rule silent, committee clear majority             |      11.1 |  59.1 |  35.4 |  84.8 |        0.7 |
|  63 | 2016-26 | rule calls, committee clear majority the same way |      11.3 |  68.4 |  43.4 |  90.3 |        1   |
|  63 | 2016-26 | rule calls, committee no clear majority           |       7.3 |  65.2 |  35.9 |  91.8 |        0.7 |
|  63 | 2016-26 | rule calls, committee clear majority AGAINST      |       0   |   0   |   0   |  79.3 |        0   |
|  63 | 2016-26 | rule silent, committee clear majority             |       7.4 |  56.6 |  25   |  84.2 |        0.7 |
|  63 | 2023-26 | rule calls, committee clear majority the same way |       4.1 |  44.2 |  15   |  85   |        1   |
|  63 | 2023-26 | rule calls, committee no clear majority           |       2   |  66.9 |   9.5 |  90.5 |        0.5 |
|  63 | 2023-26 | rule calls, committee clear majority AGAINST      |       0   | nan   | nan   | nan   |        0   |
|  63 | 2023-26 | rule silent, committee clear majority             |       3.1 |  37.1 |   6.1 |  79.2 |        0.8 |

## Null: the same machine on labels shifted by years (nothing to find)

|   shift |   h |   n_indep |   acc |   lo |   hi |
|--------:|----:|----------:|------:|-----:|-----:|
|    1500 |  21 |      89.4 |  47.8 | 38.2 | 58.5 |
|    1500 |  42 |      45.3 |  43   | 30.9 | 58.8 |
|    2500 |  21 |      50.7 |  52.2 | 37.7 | 64.1 |
|    2500 |  42 |      32.2 |  50.3 | 33.6 | 66.4 |
|    3500 |  21 |      76.6 |  55.7 | 44.7 | 66.4 |
|    3500 |  42 |      36.3 |  55.3 | 39.6 | 70.5 |

## Look-ahead control

View columns from a frame cut at 2018-12-31 against the full frame, last 250 sessions: 0 of 53 columns differ.

## League table of the analysts, 1 month, 2010-26 (only analysts with at least 10 independent calls)

| analyst      | school   | prior    |   n_indep |   acc |   lo |   hi |   share_of_days |
|:-------------|:---------|:---------|----------:|------:|-----:|-----:|----------------:|
| labour:E     | ECO      | textbook |      41.7 |  60.1 | 44.5 | 73   |            20.1 |
| cot_z52:E    | POS      | HOUSE    |     186.2 |  58.6 | 51.4 | 65.4 |            89.8 |
| cot_z52:D    | POS      | HOUSE    |     194.6 |  58.6 | 51.4 | 65.1 |            93.9 |
| agreement:D  | GEN      | HOUSE    |      83.8 |  58.2 | 47.7 | 68.3 |            40.4 |
| agreement:E  | GEN      | HOUSE    |      79   |  58   | 47.2 | 68.5 |            38.1 |
| eqrel:D      | RISK     | HOUSE    |     180.4 |  57.7 | 50.5 | 64.8 |            87.1 |
| infl_gap:E   | ECO      | textbook |     195   |  57.7 | 50.4 | 64.2 |            94.1 |
| eqrel:E      | RISK     | HOUSE    |     151.1 |  57.6 | 49.6 | 65.2 |            72.9 |
| infl_gap:D   | ECO      | textbook |     198.9 |  57.6 | 50.3 | 64   |            96   |
| pol_lvl:E    | CB       | textbook |      25.1 |  57.4 | 37.1 | 73.3 |            12.1 |
| rrd2_lvl:E   | RL       | textbook |     102.1 |  57.2 | 47.2 | 66.1 |            49.3 |
| rrd10_lvl:E  | RL       | textbook |     120.3 |  56.9 | 47.7 | 65.2 |            58.1 |
| season:D     | GEN      | HOUSE    |      61.9 |  56   | 44.1 | 68.1 |            29.9 |
| cot_z156:D   | POS      | HOUSE    |     187.4 |  56   | 49   | 63.1 |            90.4 |
| cot_z156:E   | POS      | HOUSE    |     175.8 |  55.9 | 48.3 | 62.8 |            84.8 |
| scorecard:D  | GEN      | textbook |     171.5 |  55.8 | 48.6 | 63.4 |            82.7 |
| cot_lev:E    | POS      | follow   |     136.7 |  55.3 | 47.1 | 63.5 |            65.9 |
| cot_lev:D    | POS      | follow   |     136.7 |  55.3 | 47.1 | 63.5 |            65.9 |
| house:D      | GEN      | HOUSE    |     186.6 |  55.1 | 47.9 | 62   |            90.1 |
| rd2_d126:E   | RC       | textbook |      35.1 |  54.9 | 38.2 | 69.5 |            17   |
| house:E      | GEN      | HOUSE    |     175.2 |  54.5 | 46.9 | 61.5 |            84.6 |
| infl_d126:E  | ECO      | textbook |     134.1 |  54.4 | 46   | 62.7 |            64.7 |
| scorecard:E  | GEN      | textbook |      66.5 |  53.6 | 41.9 | 65.1 |            32.1 |
| infl_d126:D  | ECO      | textbook |     183   |  53.4 | 46.3 | 60.6 |            88.3 |
| rd2_d126:D   | RC       | textbook |     155.6 |  53.2 | 45.4 | 60.9 |            75.1 |
| rd2_d63:D    | RC       | textbook |     156.4 |  53.2 | 45.4 | 60.9 |            75.5 |
| fed_dir:D    | CB       | textbook |      33.8 |  53   | 36.7 | 68.5 |            16.3 |
| slope2:E     | XA       | textbook |      33.8 |  52.9 | 36.7 | 68.5 |            16.3 |
| cot_d4:D     | POS      | follow   |     109.4 |  52.6 | 43.9 | 62.3 |            52.8 |
| labour:D     | ECO      | textbook |     101.9 |  52.5 | 42.4 | 61.4 |            49.1 |
| mom126:D     | TR       | textbook |     132.5 |  52.4 | 43.5 | 60.2 |            63.9 |
| sma50_200:D  | TR       | textbook |     207.1 |  52.3 | 45.4 | 58.9 |            99.9 |
| brk126:D     | TR       | textbook |     207.1 |  52.1 | 45.4 | 58.9 |            99.9 |
| usd20:D      | XA       | HOUSE    |     147.4 |  51.6 | 43.7 | 59.6 |            71.1 |
| rd10_lvl:D   | RL       | textbook |     183.2 |  51.6 | 44.7 | 59   |            88.4 |
| rd2_d63:E    | RC       | textbook |      54   |  51.3 | 38.9 | 64.6 |            26.1 |
| carry:E      | RL       | textbook |      48.6 |  51.3 | 37.5 | 64.4 |            23.4 |
| mom21:D      | TR       | textbook |      99.1 |  51.3 | 41.8 | 61.1 |            47.8 |
| mom63:D      | TR       | textbook |      85.1 |  51.2 | 41.3 | 62.1 |            41.1 |
| vix_d5:D     | RISK     | textbook |      14.7 |  51.1 | 30.1 | 75.2 |             7.1 |
| sahm:E       | ECO      | textbook |      71.2 |  50.9 | 39.3 | 62   |            34.4 |
| carry:D      | RL       | textbook |     148.7 |  50.2 | 42.4 | 58.3 |            71.8 |
| sp2_d20:D    | RC       | HOUSE    |      80   |  50.1 | 39.3 | 60.7 |            38.6 |
| brk126:E     | TR       | textbook |      61.7 |  49.7 | 37.9 | 62.1 |            29.8 |
| pol_lvl:D    | CB       | textbook |     138   |  49.6 | 41.1 | 57.5 |            66.6 |
| mom126:E     | TR       | textbook |      69.5 |  49.6 | 37.2 | 60   |            33.5 |
| month:D      | GEN      | learned  |      44.2 |  49.5 | 35.8 | 64.2 |            21.3 |
| sahm:D       | ECO      | textbook |      94.4 |  49.2 | 39.1 | 58.9 |            45.6 |
| sma50_200:E  | TR       | textbook |      74   |  48.7 | 37.6 | 59.8 |            35.7 |
| fair_value:E | VAL      | HOUSE    |      63.5 |  48.6 | 37.3 | 61.2 |            30.6 |
| vix:D        | RISK     | textbook |     100.8 |  48.6 | 39   | 58.1 |            48.6 |
| slope3m:E    | XA       | textbook |      58.8 |  47.9 | 35.3 | 60   |            28.4 |
| slope3m:D    | XA       | textbook |     148   |  47.9 | 40.1 | 56   |            71.4 |
| spx20:D      | RISK     | textbook |     144.4 |  47.3 | 39.2 | 55.3 |            69.7 |
| gold20:D     | RISK     | textbook |     115.9 |  46.8 | 37.7 | 55.6 |            55.9 |
| fed_priced:E | FED      | textbook |      37   |  46.5 | 31   | 61.6 |            17.9 |
| rev252:E     | VAL      | HOUSE    |      22.1 |  44.1 | 26.9 | 65.3 |            10.7 |
| rd10_lvl:E   | RL       | textbook |      33.8 |  42.7 | 26.4 | 57.8 |            16.3 |
| pol_d63:E    | CB       | textbook |      19.4 |  42.5 | 23.1 | 63.7 |             9.4 |
| pol_d126:E   | CB       | textbook |      23.2 |  42.3 | 25.6 | 63.2 |            11.2 |
| rd2_lvl:D    | RL       | textbook |      26.7 |  41.1 | 24.5 | 59.3 |            12.9 |
| fair_value:D | VAL      | HOUSE    |      28.5 |  41   | 26.5 | 60.9 |            13.7 |
| ppp:E        | VAL      | textbook |      10.3 |  38.7 | 16.8 | 68.7 |             5   |
| oil63:E      | XA       | textbook |      31.2 |  38.5 | 23.7 | 56.2 |            15.1 |
| rd10_d126:E  | RC       | textbook |      10.7 |  37.9 | 15.2 | 64.6 |             5.1 |
| fed_cycle:D  | FED      | textbook |      12.4 |  37.7 | 19.3 | 68   |             6   |
| spx20:E      | RISK     | textbook |      11.6 |  32.8 | 13.8 | 60.9 |             5.6 |
