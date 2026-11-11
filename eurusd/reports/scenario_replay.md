# Scenario replay 2010-2026 through the live paper engine

Net bp per unit, 1.2 pips per unit turnover (London control: 1.2 pips per round trip). Signals refitted every session on prior data only.
`P(120d SR<0)` = share of all rolling 120-session windows in which the scenario's Sharpe was negative, i.e. how often the six-month DISPOSE rule would have fired.
`P(PROMOTE vs base)` = share of windows in which the PROMOTE? rule would have fired.

| scenario            | role       |   SR_2010_26 |   SR_2016_26 |   SR_2023_26 |   last120_bp |   last120_SR |   P(120d SR<0) |   median_120d_SR |   p10_120d_SR |   p90_120d_SR |   P(PROMOTE vs base) |   bp_per_yr |   max_dd_bp |
|:--------------------|:-----------|-------------:|-------------:|-------------:|-------------:|-------------:|---------------:|-----------------:|--------------:|--------------:|---------------------:|------------:|------------:|
| base_no_stop        | variant    |         0.82 |         0.74 |         0.36 |       502.36 |         2.14 |           0.33 |             0.62 |         -1.01 |          2.5  |                 0.03 |      487.52 |    -1033.09 |
| base_tight_stop     | variant    |         0.78 |         0.65 |         0.17 |       426.85 |         1.92 |           0.34 |             0.61 |         -1.09 |          2.34 |                 0.05 |      453.25 |     -979.79 |
| base                | primary    |         0.76 |         0.7  |         0.37 |       448.06 |         1.98 |           0.32 |             0.61 |         -1.21 |          2.48 |               nan    |      447.89 |    -1203.44 |
| base_daily          | variant    |         0.76 |         0.58 |         0.19 |       482.42 |         2.21 |           0.33 |             0.63 |         -1.17 |          2.46 |                 0.11 |      438.97 |     -925.92 |
| round1_combo        | challenger |         0.72 |         0.8  |         0.43 |       405.75 |         2.41 |           0.33 |             0.89 |         -1.62 |          2.45 |                 0.24 |      302.19 |    -1088.04 |
| positioning_only    | challenger |         0.63 |         0.53 |         0.23 |       461.3  |         1.82 |           0.35 |             0.55 |         -1.07 |          2.39 |                 0.1  |      536.3  |    -1780.42 |
| london_short        | control    |         0.6  |         0.51 |        -0.08 |       130.55 |         1.03 |           0.34 |             0.53 |         -1.17 |          2.32 |                 0.24 |      274.9  |     -871.83 |
| weak_signals_sign   | challenger |         0.56 |         0.41 |         0.02 |       325.66 |         2.12 |           0.39 |             0.37 |         -1.39 |          2.3  |                 0.18 |      304.09 |    -1509.7  |
| weak_signals_linear | challenger |         0.54 |         0.44 |         0.37 |       297.28 |         2.14 |           0.39 |             0.41 |         -1.54 |          2.11 |                 0.17 |      261.52 |    -1839.95 |
| always_short        | benchmark  |         0.18 |        -0.03 |        -0.15 |       410.26 |         1.82 |           0.46 |             0.17 |         -1.69 |          1.89 |                 0.16 |      148.43 |    -2267.94 |
| trend_3m            | control    |         0.09 |        -0.1  |        -0.38 |      -444.92 |        -1.31 |           0.5  |            -0.02 |         -1.94 |          1.81 |                 0.12 |       78.84 |    -3721.49 |
| always_long         | benchmark  |        -0.18 |         0.03 |         0.15 |      -410.26 |        -1.82 |           0.54 |            -0.17 |         -1.89 |          1.69 |                 0.11 |     -148.53 |    -4352.87 |
