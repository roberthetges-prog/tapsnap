# Risk report  2026-11-10 21:00 UTC

Last bar 2026-11-10 20:00 UTC (source: yahoo), price 1.11657

## Volatility
HAR 1-day vol 37 bp (5.9% annualised); realized 22d 5.9%; ATR14 71 pips; ADR14 72 pips

## Book
Equity 9,993.04 | open P&L +0.00 | peak 10,000.00 | open risk at stops 112.68 (1.13%)

|   id | strategy       | side   |   lots |   entry |    stop |   stop_dist_pips |   stop_dist_adr |   pnl |   risk_at_stop | exit                |
|-----:|:---------------|:-------|-------:|--------:|--------:|-----------------:|----------------:|------:|---------------:|:--------------------|
|    2 | macro_exposure | short  |   0.09 | 1.11657 | 1.12909 |            125.2 |            1.75 |     0 |         112.68 | rebalance on signal |

## Limits (kill switches)
- daily_loss: -0.0007 vs limit -0.02 -> ok
- monthly_loss: -0.0007 vs limit -0.05 -> ok
- drawdown: -0.0007 vs limit -0.1 -> ok
- open_risk: +0.0113 vs limit 0.015 -> ok
- consecutive_losses: +1.0000 vs limit 8 -> ok
- data_age_hours: +0.0000 vs limit 30 -> ok

Trading halted: **False**

## Value at risk (99%, 1 day)
- Parametric (HAR vol): VaR 77.30, ES 88.56, net exposure -9,000 USD
- Historical simulation (6771 days, stop-aware): VaR 135.22, ES 135.22, worst day -135.22
- Monte Carlo 1 month per exposure unit: median +0.10%, 5th pct -1.33%, 95th pct +1.97%, P(loss) 41%, median max DD -0.59%, P(breach 10% DD) 0.0%
- Monte Carlo 1 year per exposure unit: median +1.88%, 5th pct -3.68%, 95th pct +7.76%, P(loss) 29%, median max DD -2.84%, P(breach 10% DD) 0.1%

## Stress tests (open book replayed through the episode's path, stops honoured, gaps fill at the gap)
| scenario                           |   episode_move_bp |   book_pnl |   pct_equity |   positions_stopped |
|:-----------------------------------|------------------:|-----------:|-------------:|--------------------:|
| SNB floor removal 2015-01-15       |              -122 |     122.63 |       0.0123 |                   0 |
| FOMC 2015-03-18 (120 pips/min)     |               215 |    -112.68 |      -0.0113 |                   1 |
| ECB 2015-12-03 (168 pips/min)      |               353 |    -112.68 |      -0.0113 |                   1 |
| Brexit night 2016-06-23/24         |              -294 |     294.98 |       0.0295 |                   0 |
| US election night 2016-11-08/09    |                 2 |    -112.68 |      -0.0113 |                   1 |
| COVID dash for cash 2020-03-09..20 |              -587 |    -112.68 |      -0.0113 |                   1 |
| Ukraine invasion 2022-02-24        |              -101 |     101.07 |       0.0101 |                   0 |
| Dollar surge Sep 2022 (10 days)    |              -572 |     574.88 |       0.0575 |                   0 |
| Tariff weekend gap 2025-02-02      |              -112 |     112.28 |       0.0112 |                   0 |
| synthetic gap +1 ADR (72 pips)     |                64 |     -64.52 |      -0.0065 |                   0 |
| synthetic gap -1 ADR (72 pips)     |               -64 |      64.52 |       0.0065 |                   0 |
| synthetic gap +2 ADR (143 pips)    |               128 |    -129.04 |      -0.0129 |                   1 |
| synthetic gap -2 ADR (143 pips)    |              -128 |     129.04 |       0.0129 |                   0 |
| synthetic gap +3 ADR (215 pips)    |               193 |    -193.55 |      -0.0194 |                   1 |
| synthetic gap -3 ADR (215 pips)    |              -193 |     193.55 |       0.0194 |                   0 |

## High-impact events, next 72h
| time                      | event            |   hours_ahead |
|:--------------------------|:-----------------|--------------:|
| 2026-11-13 13:30:00+00:00 | USD Core PPI m/m |          64.5 |
| 2026-11-13 13:30:00+00:00 | USD BLS PPI      |          64.5 |
| 2026-11-13 13:30:00+00:00 | US PPI           |          64.5 |
| 2026-11-13 13:30:00+00:00 | USD PPI m/m      |          64.5 |

## Component health (live trades vs validation record)
|                |   validation_mean_r |   validation_sd_r |   live_trades | live_mean_r   | z   | alert   |   consecutive_losses | unit                                    |
|:---------------|--------------------:|------------------:|--------------:|:--------------|:----|:--------|---------------------:|:----------------------------------------|
| macro_exposure |            0.582505 |           16.4118 |             0 |               |     | False   |                    0 | bp per session per unit (OOS 2010-2026) |
