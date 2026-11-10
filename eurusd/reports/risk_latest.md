# Risk report  2026-11-10 21:00 UTC

Last bar 2026-11-10 20:00 UTC (source: yahoo), price 1.11657

## Volatility
HAR 1-day vol 37 bp (5.9% annualised); realized 22d 5.9%; ATR14 71 pips; ADR14 72 pips

## Book
Equity 10,000.00 | open P&L -5.96 | peak 10,000.00 | open risk at stops 45.20 (0.45%)

|   id | strategy   | side   |   lots |   entry |    stop |   stop_dist_pips |   stop_dist_adr |   pnl |   risk_at_stop | exit                      |
|-----:|:-----------|:-------|-------:|--------:|--------:|-----------------:|----------------:|------:|---------------:|:--------------------------|
|    1 | cot_trend  | short  |   0.04 | 1.11508 | 1.12638 |             98.1 |            1.37 | -5.96 |           45.2 | 2026-11-13T22:00:00+00:00 |

## Limits (kill switches)
- daily_loss: -0.0006 vs limit -0.02 -> ok
- monthly_loss: -0.0006 vs limit -0.05 -> ok
- drawdown: -0.0006 vs limit -0.1 -> ok
- open_risk: +0.0045 vs limit 0.015 -> ok
- consecutive_losses: +0.0000 vs limit 8 -> ok
- data_age_hours: +0.0000 vs limit 30 -> ok

Trading halted: **False**

## Value at risk (99%, 1 day)
- Parametric (HAR vol): VaR 34.36, ES 39.36, net exposure -4,000 USD
- Historical simulation (6771 days, stop-aware): VaR 47.09, ES 47.09, worst day -47.09
- Monte Carlo strategy mix 1 month at 0.50% risk/trade: median +0.22%, 5th pct -1.61%, 95th pct +2.20%, P(loss) 43%, median max DD -0.93%, P(breach 10% DD) 0.0%
- Monte Carlo strategy mix 1 year at 0.50% risk/trade: median +2.63%, 5th pct -4.03%, 95th pct +9.76%, P(loss) 27%, median max DD -3.41%, P(breach 10% DD) 0.3%

## Stress tests (open book replayed through the episode's path, stops honoured, gaps fill at the gap)
| scenario                           |   episode_move_bp |   book_pnl |   pct_equity |   positions_stopped |
|:-----------------------------------|------------------:|-----------:|-------------:|--------------------:|
| SNB floor removal 2015-01-15       |              -122 |      54.5  |       0.0055 |                   0 |
| FOMC 2015-03-18 (120 pips/min)     |               215 |     -39.24 |      -0.0039 |                   1 |
| ECB 2015-12-03 (168 pips/min)      |               353 |     -39.24 |      -0.0039 |                   1 |
| Brexit night 2016-06-23/24         |              -294 |     131.1  |       0.0131 |                   0 |
| US election night 2016-11-08/09    |                 2 |     -39.24 |      -0.0039 |                   1 |
| COVID dash for cash 2020-03-09..20 |              -587 |     -39.24 |      -0.0039 |                   1 |
| Ukraine invasion 2022-02-24        |              -101 |      44.92 |       0.0045 |                   0 |
| Dollar surge Sep 2022 (10 days)    |              -572 |     255.5  |       0.0256 |                   0 |
| Tariff weekend gap 2025-02-02      |              -112 |      49.9  |       0.005  |                   0 |
| synthetic gap +1 ADR (72 pips)     |                64 |     -28.67 |      -0.0029 |                   0 |
| synthetic gap -1 ADR (72 pips)     |               -64 |      28.67 |       0.0029 |                   0 |
| synthetic gap +2 ADR (143 pips)    |               128 |     -57.35 |      -0.0057 |                   1 |
| synthetic gap -2 ADR (143 pips)    |              -128 |      57.35 |       0.0057 |                   0 |
| synthetic gap +3 ADR (215 pips)    |               193 |     -86.02 |      -0.0086 |                   1 |
| synthetic gap -3 ADR (215 pips)    |              -193 |      86.02 |       0.0086 |                   0 |

## High-impact events, next 72h
| time                      | event            |   hours_ahead |
|:--------------------------|:-----------------|--------------:|
| 2026-11-13 13:30:00+00:00 | USD Core PPI m/m |          64.5 |
| 2026-11-13 13:30:00+00:00 | USD BLS PPI      |          64.5 |
| 2026-11-13 13:30:00+00:00 | US PPI           |          64.5 |
| 2026-11-13 13:30:00+00:00 | USD PPI m/m      |          64.5 |

## Component health (live trades vs validation record)
|               |   validation_mean_r |   validation_sd_r |   live_trades | live_mean_r   | z   | alert   |   consecutive_losses |
|:--------------|--------------------:|------------------:|--------------:|:--------------|:----|:--------|---------------------:|
| london_short  |          0.00691195 |          0.37621  |             0 |               |     | False   |                    0 |
| fomc_day_long |          0.0820862  |          0.559283 |             0 |               |     | False   |                    0 |
| cot_trend     |          0.0475539  |          0.710114 |             0 |               |     | False   |                    0 |
