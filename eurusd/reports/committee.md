# The committee: 100 analysts vote on EUR/USD direction

Code `src/eurusd/committee.py`, test `experiments/70_committee.py`, results `experiments/results/arms/committee_*`.
Design, majority classes and keep bar were written into the module before the first run (2026-11-17). One design, no tuning.

## Verdict against the declared bar: **FAIL**

|   h | era     |   committee clear+strong |   agreement rule |   gain pts |   calls/yr |   63-stale copy | >=3 pts   | >=6/yr   | stale loses half   |
|----:|:--------|-------------------------:|-----------------:|-----------:|-----------:|----------------:|:----------|:---------|:-------------------|
|  21 | 2010-26 |                     59.6 |             58.3 |        1.3 |        6.6 |            57.1 | False     | True     | False              |
|  21 | 2016-26 |                     56.3 |             58   |       -1.7 |        6.3 |            56.1 | False     | True     | False              |
|  42 | 2010-26 |                     63.8 |             63.3 |        0.6 |        2.7 |            59   | False     | False    | False              |
|  42 | 2016-26 |                     59.8 |             62   |       -2.1 |        2.7 |            58.6 | False     | False    | False              |

## What a majority was worth (walk-forward, out of sample)

`n_indep` = independent calls (calls on one non-overlapping grid, averaged over all grid phases); `lo`-`hi` = 95 % Wilson range on that count; `share_of_days` = how often the committee was in that class.

### Horizon 21 sessions

| cls          | era     |   n_days |   n_indep |   acc |   lo |   hi |   per_year |   share_of_days |
|:-------------|:--------|---------:|----------:|------:|-----:|-----:|-----------:|----------------:|
| split        | 2010-26 |      510 |      24.3 |  53.7 | 35.1 | 72.1 |        1.4 |            11.7 |
| split        | 2016-26 |      342 |      16.3 |  55   | 33.2 | 76.9 |        1.5 |            12.2 |
| split        | 2023-26 |      116 |       5.5 |  62.1 | 18.8 | 81.2 |        1.4 |            11.8 |
| lean         | 2010-26 |     1364 |      65   |  57.8 | 46.3 | 69.6 |        3.8 |            31.3 |
| lean         | 2016-26 |      920 |      43.8 |  57.5 | 42.2 | 70.3 |        4   |            32.9 |
| lean         | 2023-26 |      272 |      13   |  54   | 29.1 | 76.8 |        3.2 |            27.8 |
| clear        | 2010-26 |     1635 |      77.9 |  60.6 | 49.2 | 70.4 |        4.6 |            37.6 |
| clear        | 2016-26 |      996 |      47.4 |  57.6 | 43.3 | 70.5 |        4.3 |            35.6 |
| clear        | 2023-26 |      342 |      16.3 |  48.8 | 28   | 72   |        4.1 |            34.9 |
| strong       | 2010-26 |      722 |      34.4 |  57.3 | 42.2 | 73.6 |        2   |            16.6 |
| strong       | 2016-26 |      467 |      22.2 |  53.3 | 34.7 | 73.1 |        2   |            16.7 |
| strong       | 2023-26 |      221 |      10.5 |  42.5 | 15.2 | 64.6 |        2.6 |            22.6 |
| clear+strong | 2010-26 |     2357 |     112.2 |  59.6 | 50.6 | 68.4 |        6.6 |            54.2 |
| clear+strong | 2016-26 |     1463 |      69.7 |  56.3 | 44.1 | 66.8 |        6.3 |            52.3 |
| clear+strong | 2023-26 |      563 |      26.8 |  46.4 | 27.6 | 62.7 |        6.7 |            57.5 |
| any majority | 2010-26 |     4231 |     201.5 |  58.3 | 51.8 | 65.3 |       11.9 |            97.2 |
| any majority | 2016-26 |     2725 |     129.8 |  56.5 | 47.6 | 64.4 |       11.8 |            97.5 |
| any majority | 2023-26 |      951 |      45.3 |  50.5 | 37   | 65   |       11.3 |            97.1 |

### Horizon 42 sessions

| cls          | era     |   n_days |   n_indep |   acc |   lo |   hi |   per_year |   share_of_days |
|:-------------|:--------|---------:|----------:|------:|-----:|-----:|-----------:|----------------:|
| split        | 2010-26 |      585 |      13.9 |  54.9 | 32.6 | 78.6 |        0.8 |            13.5 |
| split        | 2016-26 |      430 |      10.2 |  53   | 23.7 | 76.3 |        0.9 |            15.5 |
| split        | 2023-26 |      103 |       2.5 |  53.4 |  9.5 | 90.5 |        0.6 |            10.8 |
| lean         | 2010-26 |     1569 |      37.4 |  55.7 | 40.9 | 71.3 |        2.2 |            36.2 |
| lean         | 2016-26 |     1008 |      24   |  57.2 | 38.8 | 75.5 |        2.2 |            36.3 |
| lean         | 2023-26 |      303 |       7.2 |  44.6 | 15.8 | 75   |        1.8 |            31.6 |
| clear        | 2010-26 |     1463 |      34.8 |  63.7 | 46.3 | 76.8 |        2   |            33.8 |
| clear        | 2016-26 |      897 |      21.4 |  61   | 40.9 | 79.2 |        1.9 |            32.3 |
| clear        | 2023-26 |      341 |       8.1 |  47.8 | 21.5 | 78.5 |        2   |            35.6 |
| strong       | 2010-26 |      492 |      11.7 |  64.2 | 39.1 | 86.2 |        0.7 |            11.4 |
| strong       | 2016-26 |      350 |       8.3 |  56.9 | 30.6 | 86.3 |        0.8 |            12.6 |
| strong       | 2023-26 |      192 |       4.6 |  37.5 | 11.8 | 76.9 |        1.1 |            20   |
| clear+strong | 2010-26 |     1955 |      46.5 |  63.8 | 49.5 | 76   |        2.7 |            45.1 |
| clear+strong | 2016-26 |     1247 |      29.7 |  59.8 | 42.3 | 75.4 |        2.7 |            44.9 |
| clear+strong | 2023-26 |      533 |      12.7 |  44.1 | 23.2 | 70.9 |        3.2 |            55.6 |
| any majority | 2010-26 |     4109 |      97.8 |  59.5 | 49.3 | 68.4 |        5.8 |            94.9 |
| any majority | 2016-26 |     2685 |      63.9 |  57.8 | 45.6 | 69.1 |        5.8 |            96.8 |
| any majority | 2023-26 |      939 |      22.4 |  45.3 | 26.9 | 65.3 |        5.6 |            98   |

### Horizon 63 sessions

| cls          | era     |   n_days |   n_indep |   acc |   lo |   hi |   per_year |   share_of_days |
|:-------------|:--------|---------:|----------:|------:|-----:|-----:|-----------:|----------------:|
| split        | 2010-26 |      674 |      10.7 |  53.7 | 28   | 78.7 |        0.6 |            15.6 |
| split        | 2016-26 |      463 |       7.3 |  55.7 | 25   | 84.2 |        0.7 |            16.8 |
| split        | 2023-26 |      121 |       1.9 |  47.9 |  9.5 | 90.5 |        0.5 |            12.9 |
| lean         | 2010-26 |     1471 |      23.3 |  64.2 | 44.9 | 81.2 |        1.4 |            34.1 |
| lean         | 2016-26 |     1009 |      16   |  64.5 | 38.6 | 81.5 |        1.5 |            36.6 |
| lean         | 2023-26 |      331 |       5.3 |  63.1 | 23.1 | 88.2 |        1.3 |            35.3 |
| clear        | 2010-26 |     1328 |      21.1 |  63.2 | 40.9 | 79.2 |        1.2 |            30.8 |
| clear        | 2016-26 |      751 |      11.9 |  62.7 | 32   | 80.7 |        1.1 |            27.3 |
| clear        | 2023-26 |      274 |       4.3 |  45.3 | 15   | 85   |        1.1 |            29.2 |
| strong       | 2010-26 |      638 |      10.1 |  67.9 | 39.7 | 89.2 |        0.6 |            14.8 |
| strong       | 2016-26 |      431 |       6.8 |  67.7 | 35.9 | 91.8 |        0.6 |            15.6 |
| strong       | 2023-26 |      196 |       3.1 |  38.8 |  6.1 | 79.2 |        0.8 |            20.9 |
| clear+strong | 2010-26 |     1966 |      31.2 |  64.7 | 46.9 | 78.9 |        1.8 |            45.6 |
| clear+strong | 2016-26 |     1182 |      18.8 |  64.6 | 41   | 80.9 |        1.7 |            42.9 |
| clear+strong | 2023-26 |      470 |       7.5 |  42.6 | 15.8 | 75   |        1.9 |            50.2 |
| any majority | 2010-26 |     4111 |      65.3 |  62.7 | 50.9 | 73.8 |        3.8 |            95.4 |
| any majority | 2016-26 |     2654 |      42.1 |  63   | 49.2 | 77   |        3.8 |            96.4 |
| any majority | 2023-26 |      922 |      14.6 |  50.7 | 24.8 | 69.9 |        3.7 |            98.4 |

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
| committee stale 63  |  21 | clear+strong | 2010-26 |     111.7 |  57.1 | 47.9 | 65.9 |
| committee stale 63  |  21 | clear+strong | 2016-26 |      68.4 |  56.1 | 44.1 | 67.1 |
| committee stale 63  |  21 | clear+strong | 2023-26 |      25.6 |  49.7 | 32.1 | 67.9 |
| committee stale 63  |  21 | any majority | 2010-26 |     201.5 |  54.5 | 47.8 | 61.5 |
| committee stale 63  |  21 | any majority | 2016-26 |     129.8 |  53.2 | 44.5 | 61.4 |
| committee stale 63  |  21 | any majority | 2023-26 |      45.3 |  48.8 | 35   | 63   |
| committee stale 63  |  42 | clear+strong | 2010-26 |      46.1 |  59   | 44.3 | 71.7 |
| committee stale 63  |  42 | clear+strong | 2016-26 |      28.8 |  58.6 | 40.7 | 74.5 |
| committee stale 63  |  42 | clear+strong | 2023-26 |      12.1 |  46.6 | 25.4 | 74.6 |
| committee stale 63  |  42 | any majority | 2010-26 |      97.5 |  55.5 | 45.2 | 64.6 |
| committee stale 63  |  42 | any majority | 2016-26 |      63.9 |  55.8 | 44.1 | 67.7 |
| committee stale 63  |  42 | any majority | 2023-26 |      22.4 |  45.6 | 26.9 | 65.3 |
| committee stale 63  |  63 | clear+strong | 2010-26 |      31   |  57.7 | 40.8 | 73.6 |
| committee stale 63  |  63 | clear+strong | 2016-26 |      18.2 |  63.9 | 43.7 | 83.7 |
| committee stale 63  |  63 | clear+strong | 2023-26 |       6.9 |  51.7 | 25   | 84.2 |
| committee stale 63  |  63 | any majority | 2010-26 |      65.2 |  55.6 | 43.3 | 66.8 |
| committee stale 63  |  63 | any majority | 2016-26 |      42.1 |  58.2 | 42.2 | 70.9 |
| committee stale 63  |  63 | any majority | 2023-26 |      14.6 |  48.9 | 24.8 | 69.9 |
| committee stale 126 |  21 | clear+strong | 2010-26 |     110.5 |  51.5 | 42.2 | 60.4 |
| committee stale 126 |  21 | clear+strong | 2016-26 |      66   |  51.9 | 39.7 | 63.2 |
| committee stale 126 |  21 | clear+strong | 2023-26 |      25.4 |  52.6 | 33.5 | 70   |
| committee stale 126 |  21 | any majority | 2010-26 |     201.5 |  48.9 | 42.4 | 56.1 |
| committee stale 126 |  21 | any majority | 2016-26 |     129.6 |  48.7 | 40   | 57   |
| committee stale 126 |  21 | any majority | 2023-26 |      45.3 |  49.1 | 35   | 63   |
| committee stale 126 |  42 | clear+strong | 2010-26 |      44.9 |  51.2 | 37   | 65   |
| committee stale 126 |  42 | clear+strong | 2016-26 |      27.5 |  51.1 | 34   | 69.3 |
| committee stale 126 |  42 | clear+strong | 2023-26 |      11.7 |  45.8 | 19.3 | 68   |
| committee stale 126 |  42 | any majority | 2010-26 |      97   |  53.3 | 43.7 | 63.2 |
| committee stale 126 |  42 | any majority | 2016-26 |      63.9 |  53.3 | 41.1 | 64.8 |
| committee stale 126 |  42 | any majority | 2023-26 |      22.4 |  45.5 | 26.9 | 65.3 |
| committee stale 126 |  63 | clear+strong | 2010-26 |      30.6 |  50.6 | 32   | 65.2 |
| committee stale 126 |  63 | clear+strong | 2016-26 |      17.6 |  54   | 33.7 | 75.4 |
| committee stale 126 |  63 | clear+strong | 2023-26 |       7   |  46.4 | 15.8 | 75   |
| committee stale 126 |  63 | any majority | 2010-26 |      65.3 |  52.4 | 40.4 | 64   |
| committee stale 126 |  63 | any majority | 2016-26 |      42.1 |  54.3 | 39.9 | 68.8 |
| committee stale 126 |  63 | any majority | 2023-26 |      14.6 |  45.6 | 24.8 | 69.9 |

## Does the committee add to the three-signal agreement rule?

|   h | era     | case                                              |   n_indep |   acc |    lo |    hi |   per_year |
|----:|:--------|:--------------------------------------------------|----------:|------:|------:|------:|-----------:|
|  21 | 2010-26 | rule calls, committee clear majority the same way |      63.2 |  59.6 |  48   |  71.5 |        3.7 |
|  21 | 2010-26 | rule calls, committee no clear majority           |      26.8 |  55.2 |  37.3 |  72.4 |        1.6 |
|  21 | 2010-26 | rule calls, committee clear majority AGAINST      |       0.7 |  60   |   0   |  79.3 |        0   |
|  21 | 2010-26 | rule silent, committee clear majority             |      48.3 |  60   |  46.3 |  73   |        2.8 |
|  21 | 2016-26 | rule calls, committee clear majority the same way |      37.1 |  59.8 |  43.5 |  73.7 |        3.4 |
|  21 | 2016-26 | rule calls, committee no clear majority           |      19.2 |  54.2 |  31.7 |  72.7 |        1.7 |
|  21 | 2016-26 | rule calls, committee clear majority AGAINST      |       0.7 |  64.3 |   0   |  79.3 |        0.1 |
|  21 | 2016-26 | rule silent, committee clear majority             |      31.9 |  52.5 |  36.4 |  69.1 |        2.9 |
|  21 | 2023-26 | rule calls, committee clear majority the same way |      14.6 |  51.1 |  24.8 |  69.9 |        3.7 |
|  21 | 2023-26 | rule calls, committee no clear majority           |       4.8 |  60.4 |  23.1 |  88.2 |        1.2 |
|  21 | 2023-26 | rule calls, committee clear majority AGAINST      |       0   | 100   |   0   |  79.3 |        0   |
|  21 | 2023-26 | rule silent, committee clear majority             |      12.1 |  40.8 |  19.3 |  68   |        3   |
|  42 | 2010-26 | rule calls, committee clear majority the same way |      27.8 |  64.2 |  45.8 |  79.3 |        1.6 |
|  42 | 2010-26 | rule calls, committee no clear majority           |      16.9 |  61.3 |  36   |  78.4 |        1   |
|  42 | 2010-26 | rule calls, committee clear majority AGAINST      |       0.2 |  88.9 |   0   |  79.3 |        0   |
|  42 | 2010-26 | rule silent, committee clear majority             |      18.6 |  63.8 |  41   |  80.9 |        1.1 |
|  42 | 2016-26 | rule calls, committee clear majority the same way |      16.6 |  63.2 |  36   |  78.4 |        1.5 |
|  42 | 2016-26 | rule calls, committee no clear majority           |      11.2 |  59.7 |  35.4 |  84.8 |        1   |
|  42 | 2016-26 | rule calls, committee clear majority AGAINST      |       0.2 |  87.5 |   0   |  79.3 |        0   |
|  42 | 2016-26 | rule silent, committee clear majority             |      12.9 |  56.2 |  29.1 |  76.8 |        1.2 |
|  42 | 2023-26 | rule calls, committee clear majority the same way |       6   |  42.9 |  18.8 |  81.2 |        1.5 |
|  42 | 2023-26 | rule calls, committee no clear majority           |       3.3 |  55.8 |  20.8 |  93.9 |        0.8 |
|  42 | 2023-26 | rule calls, committee clear majority AGAINST      |       0   | nan   | nan   | nan   |        0   |
|  42 | 2023-26 | rule silent, committee clear majority             |       6.7 |  45.2 |  15.8 |  75   |        1.7 |
|  63 | 2010-26 | rule calls, committee clear majority the same way |      19.7 |  67.3 |  43.3 |  81.9 |        1.2 |
|  63 | 2010-26 | rule calls, committee no clear majority           |      10.1 |  66.1 |  39.7 |  89.2 |        0.6 |
|  63 | 2010-26 | rule calls, committee clear majority AGAINST      |       0.1 |  14.3 |   0   |  79.3 |        0   |
|  63 | 2010-26 | rule silent, committee clear majority             |      11.4 |  60.1 |  35.4 |  84.8 |        0.7 |
|  63 | 2016-26 | rule calls, committee clear majority the same way |      11.3 |  69.7 |  43.4 |  90.3 |        1   |
|  63 | 2016-26 | rule calls, committee no clear majority           |       7.2 |  63.6 |  35.9 |  91.8 |        0.7 |
|  63 | 2016-26 | rule calls, committee clear majority AGAINST      |       0.1 |  14.3 |   0   |  79.3 |        0   |
|  63 | 2016-26 | rule silent, committee clear majority             |       7.3 |  56.4 |  25   |  84.2 |        0.7 |
|  63 | 2023-26 | rule calls, committee clear majority the same way |       4   |  46.5 |  15   |  85   |        1   |
|  63 | 2023-26 | rule calls, committee no clear majority           |       2.1 |  61.7 |   9.5 |  90.5 |        0.5 |
|  63 | 2023-26 | rule calls, committee clear majority AGAINST      |       0   | nan   | nan   | nan   |        0   |
|  63 | 2023-26 | rule silent, committee clear majority             |       3.4 |  38   |   6.1 |  79.2 |        0.9 |

## Null: the same machine on labels shifted by years (nothing to find)

|   shift |   h |   n_indep |   acc |   lo |   hi |
|--------:|----:|----------:|------:|-----:|-----:|
|    1500 |  21 |      95.6 |  47.7 | 38.2 | 57.8 |
|    1500 |  42 |      47.7 |  42.7 | 28.8 | 55.7 |
|    2500 |  21 |      40   |  52.1 | 37.5 | 67.1 |
|    2500 |  42 |      26.5 |  55.7 | 38.9 | 74.5 |
|    3500 |  21 |      75   |  57.5 | 46.1 | 67.9 |
|    3500 |  42 |      34   |  53.3 | 36.7 | 68.5 |

## Look-ahead control

View columns from a frame cut at 2018-12-31 against the full frame, last 250 sessions: 0 of 48 columns differ.

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
| rev252:E     | VAL      | HOUSE    |      22.1 |  44.1 | 26.9 | 65.3 |            10.7 |
| rd10_lvl:E   | RL       | textbook |      33.8 |  42.7 | 26.4 | 57.8 |            16.3 |
| pol_d63:E    | CB       | textbook |      19.4 |  42.5 | 23.1 | 63.7 |             9.4 |
| pol_d126:E   | CB       | textbook |      23.2 |  42.3 | 25.6 | 63.2 |            11.2 |
| rd2_lvl:D    | RL       | textbook |      26.7 |  41.1 | 24.5 | 59.3 |            12.9 |
| fair_value:D | VAL      | HOUSE    |      28.5 |  41   | 26.5 | 60.9 |            13.7 |
| ppp:E        | VAL      | textbook |      10.3 |  38.7 | 16.8 | 68.7 |             5   |
| oil63:E      | XA       | textbook |      31.2 |  38.5 | 23.7 | 56.2 |            15.1 |
| rd10_d126:E  | RC       | textbook |      10.7 |  37.9 | 15.2 | 64.6 |             5.1 |
| spx20:E      | RISK     | textbook |      11.6 |  32.8 | 13.8 | 60.9 |             5.6 |
