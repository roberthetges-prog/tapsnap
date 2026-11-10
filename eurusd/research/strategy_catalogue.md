# EUR/USD practitioner strategy catalogue

Compiled 2026-11-10 from ~95 web searches (search-engine summaries; direct page fetches and GitHub API reads were blocked by the session network policy, so some tables referenced by sources could not be read and are flagged). Companion machine-readable file: `strategies.json`.

**Reading guide.** Every entry has exact entry/exit/stop/target rules; where the source only gave a vague description the rules are a *reconstruction* (flagged). `Claimed performance` is quoted as reported, never adjusted or verified. Evidence quality scale: `rigorous backtest` (peer-reviewed or out-of-sample with disclosed method) > `vendor backtest` (tool/broker/course seller) > `forum anecdote` > `textbook description, no stats`. Pip = 0.0001.

**Entry count: 102** -- Session / time-of-day: 19, Breakout / trend: 18, Mean reversion: 15, Volatility: 6, Price action: 12, Calendar / seasonality / events: 10, Fundamental / intermarket: 12, Microstructure: 2, Systematic / ML / vendor suites: 8.

**Evidence mix:** forum anecdote: 31, textbook description, no stats: 29, vendor backtest: 23, rigorous backtest: 19.

## Headline findings

1. **Every textbook EUR/USD system published with a 10-year, cost-aware test lost money 2016-2026** (Backtrex: London breakout PF 0.87 / 36.3% / 1,230 trades; MACD+RSI H1 PF 0.80 / -53%; Turtle 20/10 D1 PF 0.94; Connors RSI(2) D1 PF 0.78 / 54.7% win). The pair's decade buy-and-hold was +0.1%; it spent most of the period in a 1.03-1.25 band, which punishes both breakout and trend systems while costs eat the mean-reversion ones.
2. **The only EUR/USD edges with peer-reviewed support are intraday seasonal flows**: USD strengthens into the 16:00 London fix and reverses after (Krohn-Mueller-Whelan, JF 2024); EUR/USD tends to fall in European hours and rise in US hours (Breedon-Ranaldo); the dollar drifts in the direction of the expected Fed move in the two days before FOMC (Karnaukh); momentum on abnormal days and reversal the next day (Caporale-Plastun). All are small per event and must be checked against spread.
3. **Candle/pattern/ICT claims are either coin flips when tested mechanically or come from sellers**: bearish engulfing 50.9/49.1; order blocks indistinguishable from placebo levels; Fibonacci retracement depths explained by chance; Judas swing/PO3 50.0% on 4,841 gold days; ICT killzone FVG on GBP/USD 33.9% win, PF 0.80. Vendor pages for the same ideas quote 60-72% win rates on 32-198 'setups' with no method.
4. **Mean reversion is real at 1-minute horizons and in multi-day streaks** (tastyfx: fading 3-day >1% streaks wins 59% on EUR/USD; Quantified Strategies daily system 53.3% / +0.06% per trade), but the per-trade edge is a few pips, i.e. the same order as the spread on a standard account and 5-10x the raw ECN spread.
5. **Useful hard numbers for a prediction model**: daily range 60-90 pips (53-60 recently, 87 in 2023, 74 in 2020); two intraday vol peaks (07:00 GMT ~28 pips/h, 13:00-15:00 GMT ~34 pips/h); the day's high/low is set in the 09:00-12:00 ET window ~20% of the time each (1.6x random); R1/S1 reached on 43%/45% of days, R2/S2 on 20%/21%; days close above the open 50.4%; December +1.24% average (65% positive), May -0.62%; NFP first-hour median range 47 pips vs 13 normally; ECB first hour ~19 pips.


## 1. Session / time-of-day

### S01. London open breakout (Asian range breakout), classic
- **Timeframes:** M15, H1  |  **Session filter:** London open window only (07:00-10:00 UTC)  |  **Evidence:** vendor backtest
- **Entry:** Define Asian range = high/low from 00:00 to 07:00 UTC (variants: 00:00-06:00 UTC, 23:00-06:00). After 07:00 UTC, enter long on first close (or stop order) above the range high; short on first close below the range low. One trade per day; cancel untriggered side once one fills. Backtrex implementation: H1 bars, breakout of Asian range after London open, 2016-10-02 to 2026-10-01.
- **Exit:** Fixed SL/TP or close at a time cutoff (commonly 12:00 UTC or NY close) if neither is hit.
- **Stop:** Backtrex: fixed 35 pips. Common retail variants: opposite side of the Asian range, or range midpoint.  |  **Target:** Backtrex: fixed 70 pips (2:1). Variants: 1x range height projected from breakout, or trailing.
- **Parameters (defaults):** `{"range_start_utc": "00:00", "range_end_utc": "07:00", "entry_window_utc": "07:00-10:00", "sl_pips": 35, "tp_pips": 70, "max_trades_per_day": 1}`
- **Claimed performance (as reported):** Backtrex (vendor backtest, EUR/USD H1, 2016-10-02 to 2026-10-01): 1,230 trades, 36.3% winners, profit factor 0.87, total return -28.0%, CAGR -3.2%, max drawdown -31.4%, only 3 of 11 calendar years positive (none by more than 2.5%); buy-and-hold +0.1%. Same vendor on GBP/USD M15: PF 0.72, total return -60.0%, CAGR -8.8% over 10 years.
- **Notes:** The most-cited intraday EUR/USD strategy and the clearest negative result found. Backtrex notes >100 trades/year makes costs decisive. A gold (XAUUSD) 3.7-year MQL5 study of the same idea exists but is not EUR/USD. Range window definitions differ by source; treat the window as a parameter to sweep.
- **Sources:** <https://backtrex.com/en/backtests/london-breakout-eur-usd>; <https://backtrex.com/en/backtests/london-breakout-gbp-usd>; <https://forums.babypips.com/t/london-breakout-strategy-1h-timeframe-modified/326993>; <https://www.mql5.com/en/blogs/post/777540>

### S02. Statistical London breakout (babypips thread variant)  *(rules reconstructed)*
- **Timeframes:** M15, M30  |  **Session filter:** London open  |  **Evidence:** forum anecdote
- **Entry:** Reconstruction of the long-running babypips 'Statistical London Breakout' thread: measure the range from 00:00 to 07:00 GMT (some posters use 02:00-07:00 ex-Sydney noise); place buy stop a few pips above the high and sell stop a few pips below the low at 07:00-08:00 GMT; skip the day if the Asian range exceeds ~50% of the 14-day ADR (breakout 'already happened').
- **Exit:** Close at 12:00 GMT or when TP/SL is hit; cancel the other pending order on fill.
- **Stop:** Opposite side of the range or ~20-30 pips, whichever is smaller (thread varies).  |  **Target:** Range height (1:1) or 1/2 of 14-day ADR.
- **Parameters (defaults):** `{"range_window_gmt": "00:00-07:00", "buffer_pips": 3, "max_range_pct_of_ADR": 50, "time_exit_gmt": "12:00"}`
- **Claimed performance (as reported):** none found
- **Notes:** No verifiable aggregate statistics in the thread excerpts found; one poster reports avoiding EURUSD/EURGBP because they move before London open. Treat the range-width filter as the one idea worth testing on top of S01.
- **Sources:** <https://forums.babypips.com/t/statistical-london-breakout-strategy/46146>; <https://forums.babypips.com/t/london-breakout-strategy-1h-timeframe-modified/326993?page=10>

### S03. 'London Ripper' Tokyo-box breakout (TradingView open-source script)  *(rules reconstructed)*
- **Timeframes:** M5, M15, M30  |  **Session filter:** London open  |  **Evidence:** textbook description, no stats
- **Entry:** Script defines the Asia box as 05:00-06:55 GMT (last two hours before London), and enters on the first decisive break of the box when London liquidity arrives (first bar closing outside the box after 07:00 GMT).
- **Exit:** Script-defined SL/TP (not visible in search excerpts); author recommends charts <= 30 min.
- **Stop:** Not confirmed from excerpts; typical: opposite box edge.  |  **Target:** Not confirmed from excerpts.
- **Parameters (defaults):** `{"box_window_gmt": "05:00-06:55", "default_risk_per_trade_pct": 5}`
- **Claimed performance (as reported):** none found
- **Notes:** Included because it is a concrete, narrow-window version of the London breakout (2-hour pre-London box) distinct from the full Asian range. The script warns London news spikes blow through stops.
- **Sources:** <https://www.tradingview.com/script/5DjyzjBd-LONDON-RIPPER-Breakout-Daytrade-EURUSD/>

### S04. Frankfurt open trap / 07:00 GMT fake move fade  *(rules reconstructed)*
- **Timeframes:** M5, M15, H1  |  **Session filter:** 07:00-09:00 GMT  |  **Evidence:** forum anecdote
- **Entry:** If the 07:00 GMT (Frankfurt open) hourly candle breaks the Asian range high (low) and price closes back inside the range by the close of the 08:00 GMT candle (the 08:00 candle engulfs the 07:00 candle), sell (buy) on re-entry into the range. Skip if a high-impact release is scheduled 07:00-08:00 GMT.
- **Exit:** Target the opposite side of the Asian range; time-stop at 12:00 GMT.
- **Stop:** Beyond the 07:00 spike extreme (+3-5 pips).  |  **Target:** Opposite Asian range boundary (or 1:1.5 R).
- **Parameters (defaults):** `{"trap_hour_gmt": "07:00", "confirm_hour_gmt": "08:00", "buffer_pips": 3}`
- **Claimed performance (as reported):** none found
- **Notes:** No statistics found. Essentially the same hypothesis as the ICT Judas swing (S07) with a fixed 07:00 GMT trigger. Should be tested jointly with S01: if S01 loses because early breakouts fail, S04 should show the mirror image.
- **Sources:** <https://fxnx.com/en/blog/london-breakout-strategy-how-outsmart-frankfurt-trap>; <https://takeprofitapp.com/en/learn/ict-judas-swing-explained>; <https://www.dailyfx.com/forex/education/trading_tips/chart_of_the_day/2015/05/21/FX-Reversals-EURUSD-False-Breakout.html>

### S05. New York open reversal (fade the London move at the NY open)  *(rules reconstructed)*
- **Timeframes:** M15, H1  |  **Session filter:** NY open window  |  **Evidence:** textbook description, no stats
- **Entry:** Reconstruction: measure the London-session move from 07:00 GMT to 12:30 GMT. If price is at/through a higher-timeframe level (prior day high/low, H4 swing) at the 12:30-13:30 GMT window and prints a rejection candle (pin bar/engulfing) on M15, enter against the London direction.
- **Exit:** Target the London session midpoint or VWAP of the day; close by 16:00 GMT (London fix) at the latest.
- **Stop:** Beyond the NY-open extreme + 5 pips.  |  **Target:** 50% retracement of the London range (first target), London open price (second).
- **Parameters (defaults):** `{"window_gmt": "12:30-14:00", "min_london_move_pips": 40}`
- **Claimed performance (as reported):** none found
- **Notes:** Related: Breedon & Ranaldo's finding that EUR/USD depreciates in European hours and appreciates in US hours (S18) gives a directional prior: NY-open reversals of a London EUR sell-off should be the stronger half of this setup. No numbers found for the setup itself.
- **Sources:** <https://www.whselfinvest.de/en-de/trading-platform/free-trading-strategies/tradingsystem/93-london-reversal-system>; <https://www.tradingview.com/ideas/londonsession>

### S06. London close reversal scalp (16:00 London / 11:00 ET)  *(rules reconstructed)*
- **Timeframes:** M5, M15  |  **Session filter:** London close window  |  **Evidence:** forum anecdote
- **Entry:** Between 11:00 and 12:30 ET (16:00-17:30 London), fade the day's dominant direction after a last push to a new session extreme that fails to close beyond it on M5/M15 (position squaring at the London close).
- **Exit:** Fixed ~10 pip target per the TradingView source; or close by 13:00 ET.
- **Stop:** Beyond session extreme (+5 pips) or 10-15 pips.  |  **Target:** 10 pips (source) or 1:1.
- **Parameters (defaults):** `{"window_et": "11:00-12:30", "tp_pips": 10, "sl_pips": 12}`
- **Claimed performance (as reported):** none found
- **Notes:** Academic support for a reversal around the 4pm London fix exists (Krohn-Mueller-Whelan, S14) but for a USD portfolio, not an EUR/USD scalp; 10-pip targets are below many retail spreads+slippage during the fix.
- **Sources:** <https://br.tradingview.com/chart/EURUSD/uH2ugvS5-WHAT-IS-THE-BEST-PAIR-TO-TRADE-LONDON-CLOSE/>; <https://papriceaction.blogspot.com/p/london-close-tactic.html>

### S07. ICT Judas swing (London killzone sweep of the Asian range)
- **Timeframes:** M5, M15  |  **Session filter:** London killzone  |  **Evidence:** vendor backtest
- **Entry:** Killzone 02:00-05:00 ET (07:00-10:00 UTC). Price sweeps the Asian session high (low) by a few pips and closes back inside the range (M5/M15 close), ideally with a displacement candle and a fair value gap; enter short (long) on the retrace into the FVG/order block in the direction of the daily bias (prior-day direction or HTF structure).
- **Exit:** Target the opposite side of the Asian range, then the prior day's low/high.
- **Stop:** Above/below the sweep wick (+2-5 pips).  |  **Target:** 1:2 minimum; opposite liquidity pool.
- **Parameters (defaults):** `{"killzone_et": "02:00-05:00", "sweep_min_pips": 3, "rr_min": 2}`
- **Claimed performance (as reported):** Take Profit app (vendor): 198 setups, 138 'successful reversals' (69.7%), avg R:R 1:1.8, PF 2.45, '250 trading days 2024-2025', no rules or methodology published. MQL5 blog (18 years of GOLD, not EUR/USD): Judas-swing rest-of-day reversal 50.0% of 4,841 days, i.e. coin flip without filters. Another page claims London killzone forms the definitive daily high/low 58-64% of the time (unsourced).
- **Notes:** Vendor win rates (70%) conflict with the only large-sample test (gold, 50%). The daily-bias filter is the untested ingredient; both sources say unfiltered sweeps have no edge.
- **Sources:** <https://takeprofitapp.com/en/learn/ict-judas-swing-explained>; <https://www.mql5.com/en/blogs/post/778873>; <https://www.luxalgo.com/library/concept/judas-swing.md>; <https://backtrex.com/en/blog/london-kill-zone-ict-times-strategy>

### S08. ICT killzone + fair value gap (NY AM killzone)
- **Timeframes:** M15  |  **Session filter:** NY AM killzone  |  **Evidence:** vendor backtest
- **Entry:** Backtrex implementation (GBP/USD, M15): in the NY AM killzone (07:00-10:00 ET) wait for a 3-candle fair value gap (candle1 high < candle3 low for bullish); enter on the retrace into the gap in the direction of the displacement.
- **Exit:** Fixed SL/TP.
- **Stop:** Beyond the gap/candle extreme.  |  **Target:** Next liquidity level or fixed 1:2.
- **Parameters (defaults):** `{"killzone_et": "07:00-10:00", "rr": 2}`
- **Claimed performance (as reported):** Backtrex (vendor backtest, GBP/USD M15, 2016-10-02 to 2026-10-01): 1,009 trades, win rate 33.89%, PF 0.80, total -30% (~-3.5%/yr), max DD -33.5%, longest losing streak 14; buy-and-hold +2%. No EUR/USD run published.
- **Notes:** Negative result on the sister pair. EUR/USD likely similar or worse (lower volatility, more range days). FVG definition is mechanical and easy to replicate.
- **Sources:** <https://backtrex.com/en/backtests/ict-kill-zone-fvg-gbp-usd>; <https://backtrex.com/en/blog/fair-value-gap-trading-strategy>

### S09. ICT Silver Bullet (10:00-11:00 ET FVG entry)
- **Timeframes:** M1, M5  |  **Session filter:** 10:00-11:00 ET  |  **Evidence:** vendor backtest
- **Entry:** Between 10:00 and 11:00 ET only: after a liquidity sweep (prior session high/low or equal highs/lows), enter on the first M1-M5 fair value gap formed by the displacement away from the swept level, in the direction of the displacement.
- **Exit:** Target the next liquidity pool (session high/low, prior day high/low).
- **Stop:** Below/above the sweep extreme.  |  **Target:** Minimum 1:2; close all by 11:00-11:30 ET.
- **Parameters (defaults):** `{"window_et": "10:00-11:00", "timeframe": "M5", "rr_min": 2}`
- **Claimed performance (as reported):** Take Profit app (vendor): EURUSD M5, 2024-2025, 134 setups, 81 wins (60.4%), avg R:R 1:2.3, PF 2.81 (ranked below NAS100 and gold). Offbeat Forex mechanical bot test (not EURUSD-only, one year): 29.6% win rate, PF 0.81; discretionary EURUSD M15 version 40.4% win rate. LuxAlgo claims 70-80% 'when conditions are respected', no data.
- **Notes:** Claims span 30% to 80% win rate depending on who is selling what. A mechanical definition (sweep + FVG in a one-hour window) is testable; expect the 10-11 ET window itself (post-US-open vol) to carry most of any effect.
- **Sources:** <https://takeprofitapp.com/en/learn/ict-silver-bullet-strategy>; <https://offbeatforex.com/is-ict-strategy-profitable/>; <https://www.luxalgo.com/library/concept/silver-bullet/>; <https://backtrex.com/en/blog/ict-silver-bullet-strategy-trading-guide>

### S10. ICT Power of Three (accumulation-manipulation-distribution) daily model
- **Timeframes:** M15, H1, D1  |  **Session filter:** full-day model  |  **Evidence:** textbook description, no stats
- **Entry:** Asian session (17:00-23:00 ET or 00:00-07:00 UTC) = accumulation range; London (02:00-05:00 ET) = manipulation (false move against the day's eventual direction); NY (07:00-10:00 ET) = distribution. Rule: after London sweeps one side of the Asian range and reverses back through the daily open, trade in the direction of the reversal, targeting expansion through the other side of the range during NY.
- **Exit:** Close at NY lunch (12:00 ET) or at the opposite-side liquidity target.
- **Stop:** Beyond the manipulation extreme.  |  **Target:** Opposite side of Asian range, then prior day high/low.
- **Parameters (defaults):** `{"accumulation_utc": "00:00-07:00", "manipulation_et": "02:00-05:00", "distribution_et": "07:00-10:00"}`
- **Claimed performance (as reported):** MQL5 blog test on 18 years of gold (not EUR/USD): unfiltered PO3/Judas patterns near 50% ('coin flip', 4,841 days); author suggests killzone, HTF direction and key-level filters. No EUR/USD statistics found.
- **Notes:** Equivalent to 'daily open mean reversion + continuation' framed as narrative; the testable statistic is: P(day's close is on the opposite side of the open from the London-session extreme). See fact F-18.
- **Sources:** <https://www.mql5.com/en/blogs/post/771729>; <https://www.mql5.com/en/blogs/post/778873>; <https://backtrex.com/en/blog/ict-power-of-three-amd-strategy>; <https://fxopen.com/blog/en/what-is-ict-po3-and-how-do-traders-use-it/>

### S11. Asian session range fade (Tokyo mean reversion)  *(rules reconstructed)*
- **Timeframes:** M5, M15  |  **Session filter:** Asian session  |  **Evidence:** forum anecdote
- **Entry:** From 00:00 to 06:00 UTC (variants 22:00-02:00 UTC), after the range from 22:00 UTC is at least 15 pips but under 40 pips, sell at the range high / buy at the range low when price touches it with RSI(14, M5) > 70 / < 30, targeting the range midpoint.
- **Exit:** Range midpoint or 06:00 UTC time stop (before Frankfurt/London).
- **Stop:** 8-12 pips beyond the range edge.  |  **Target:** Range midpoint (typically 10-20 pips).
- **Parameters (defaults):** `{"window_utc": "00:00-06:00", "min_range_pips": 15, "max_range_pips": 40, "sl_pips": 10, "rsi_len": 14, "rsi_ob": 70, "rsi_os": 30}`
- **Claimed performance (as reported):** Blog (no verification): EUR/USD stays within 30-50 pips of the 22:00 UTC open on ~70-80% of days; projected 65-75% win rate with average winner 15-20 pips vs loser 20-25 pips, expectancy +1 to +5 pips/trade. Another blog gives a Tokyo-only window average of 14 pips range. Spread in Asia on raw accounts 0.3-0.8 pips.
- **Notes:** Thin expectancy after spread; the real content is the base rate that the Asian range is small, which is better used as a filter for S01/S07 than as a strategy.
- **Sources:** <https://tradingonmt5.pages.dev/eurusd-asia-mean-reversion.html>; <https://asiatradingguide-com.pages.dev/artigos/asian-session-london-overlap-trading-strategies-2026>; <https://gomarkets.com/en-eu/articles/5-traps-traders-face-during-the-asian-session-and-how-to-navigate-them>

### S12. Asian/overnight range width as a regime filter  *(rules reconstructed)*
- **Timeframes:** H1, D1  |  **Session filter:** computed at 07:00 UTC  |  **Evidence:** forum anecdote
- **Entry:** Not a stand-alone strategy. Compute R_asia = Asian range (00:00-07:00 UTC) / ADR(14). Rule used by multiple sources: take breakout trades (S01) only when R_asia < 0.5; take fade/reversal trades (S07, S11) when R_asia > 0.6 ('the move already happened').
- **Exit:** Per host strategy.
- **Stop:** Per host strategy.  |  **Target:** Per host strategy.
- **Parameters (defaults):** `{"adr_len": 14, "breakout_max_ratio": 0.5, "fade_min_ratio": 0.6}`
- **Claimed performance (as reported):** none found
- **Notes:** No published test. Cheap to test and directly addresses why S01 loses.
- **Sources:** <https://forums.babypips.com/t/statistical-london-breakout-strategy/46146>; <https://www.mql5.com/en/blogs/post/774527>

### S13. Opening range breakout (first 30/60 minutes of London)
- **Timeframes:** M5, M15  |  **Session filter:** London first hour  |  **Evidence:** forum anecdote
- **Entry:** FXStreet 2014 rule set: take the range of the half hour before the London open (07:30-08:00 London time; some use 08:00-08:30 or 08:00-09:00 London) and buy/sell a break of that range +/- 10 pips (or +/- 1/10 of the daily ATR).
- **Exit:** Fixed target or close at 12:00 London.
- **Stop:** Opposite side of the opening range.  |  **Target:** 1x or 2x the opening range; ORB statistics scripts also track retest and extension targets.
- **Parameters (defaults):** `{"or_window_london": "08:00-08:30", "buffer_pips": 10, "buffer_alt": "0.1*ATR(14,D1)", "time_exit_london": "12:00"}`
- **Claimed performance (as reported):** Informal Scribd study (EURUSD 2001-2011, 2-3am ET window): a move beyond 30% of ADR in the first 30 minutes was followed by continuation to >=100% of ADR with a stated 98% significance; unreviewed. Edgeful (3-month sample, cited by TradeThatSwing): the London 3am-8am ET range is broken 95.45% of the time, 70% one side only, 26% both sides, 5% neither.
- **Notes:** The 95% 'London range gets broken' statistic says little (the London range is a subset of the day). The 30%-of-ADR early-move continuation claim is the testable one.
- **Sources:** <https://www.scribd.com/document/65690331/ephyquantarticle1>; <https://www.fxstreet.com/analysis/indices-insider/2014/04/23/07>; <https://tradethatswing.com/eurusd-daily-volatility-and-price-movement-tendencies/>; <https://in.tradingview.com/script/NCTr00I4-Opening-Range-Breakout-Statistics-ORB-kronos/>

### S14. 4pm London fix intraday pattern (USD rises into fixes, reverses after)
- **Timeframes:** M5, H1  |  **Session filter:** around 16:00 London (WM/Reuters)  |  **Evidence:** rigorous backtest
- **Entry:** Krohn, Mueller & Whelan (J. Finance 2024, 5-min data 1999-2019, 9 G10 pairs incl. EUR): USD appreciates in the hours before the Tokyo, Frankfurt(ECB 14:15 CET) and London 16:00 fixes and depreciates afterwards (W-shaped 24h pattern). Strategy: short EUR/USD from ~13:00 London to 16:00 London; long EUR/USD from 16:00 London to ~20:00 London (reverse after fix).
- **Exit:** Time-based: exit at the fix / 4 hours after.
- **Stop:** None in the academic version; practical 0.5 x ADR.  |  **Target:** Time exit.
- **Parameters (defaults):** `{"pre_fix_window_london": "13:00-16:00", "post_fix_window_london": "16:00-20:00"}`
- **Claimed performance (as reported):** Paper: 30-40% of daily volume executes in the 3 hours before and 1 hour after the London fix; pattern not driven by stale quotes; magnitudes are for a dollar portfolio, EUR/USD-specific pip sizes not extracted. The Full FX month-end case studies show 10-20 pip spikes/reversals within the 5-minute WM window on some month-ends and nothing on others.
- **Notes:** Best-documented intraday seasonality in FX. Returns are small per day and must beat spread; the paper attributes it to dealer hedging of client fix orders. Month-end amplifies it (S15).
- **Sources:** <https://econpapers.repec.org/RePEc:bla:jfinan:v:79:y:2024:i:1:p:541-578>; <https://www.bankofcanada.ca/2021/10/staff-working-paper-2021-48/>; <https://www.bis.org/events/221213_bis_bdi_ecb_exchange_rates/mueller.pdf>; <https://thefullfx.com/what-happened-at-the-month-end-fix-39/>

### S15. Month-end fix flows (rebalancing into the last-business-day 16:00 London fix)  *(rules reconstructed)*
- **Timeframes:** H1, D1  |  **Session filter:** last business day of month  |  **Evidence:** forum anecdote
- **Entry:** Reconstruction of sell-side practice: on the last business day of the month, estimate rebalancing direction from the month's relative equity performance (if US equities outperformed European equities in the month, foreign managers sell USD to rebalance -> expect EUR/USD bid into the 16:00 London fix, and vice versa). Enter 2-3 hours before the fix in that direction; exit at the fix; optionally fade after the fix.
- **Exit:** Flat at 16:00 London; optional reverse position held to NY close.
- **Stop:** 0.3-0.5 x ADR.  |  **Target:** Time exit at the fix.
- **Parameters (defaults):** `{"signal": "sign(MSCI US m/m return - MSCI Europe m/m return)", "entry_london": "13:00", "exit_london": "16:00"}`
- **Claimed performance (as reported):** No aggregate statistics found. The Full FX publishes monthly case studies: e.g., a January month-end where EUR/USD rose ~20 points in the 5 minutes before the window and fell ~12 pips within 2 minutes after; other months (July, Nov 2025) showed no reversal and lighter-than-expected flows.
- **Notes:** Bank 'month-end model' signals are routinely published by Citi/Barclays desks but no public hit-rate exists. Testable with daily data: sign of EUR/USD 13:00-16:00 London move on last business day vs relative equity returns.
- **Sources:** <https://thefullfx.com/what-happened-at-the-month-end-fix-39/>; <https://www.cityindex.com/en-uk/news-and-analysis/us-dollar-selling-and-eurusd-buying-into-month-end/>; <https://www.forexlive.com/technical-analysis/!/dollar-moves-back-higherfixing-and-stocks-to-blame-20150827>

### S16. Sunday/weekend gap fill
- **Timeframes:** H1, D1  |  **Session filter:** Sunday open  |  **Evidence:** forum anecdote
- **Entry:** If the Sunday 22:00 UTC (Monday Asia) open differs from Friday's 21:00/22:00 UTC close by more than X pips, trade toward Friday's close (short a gap-up, long a gap-down). Filter by gap size relative to ATR.
- **Exit:** Friday close (gap filled) or time stop Wednesday London (DailyForex finding).
- **Stop:** 1x gap size beyond the open (or 0.5 x ATR(14)).  |  **Target:** Friday close.
- **Parameters (defaults):** `{"min_gap_pips": 10, "max_gap_atr_ratio": 0.5, "time_stop": "Wednesday 08:00 London"}`
- **Claimed performance (as reported):** DailyForex (EUR/USD 2001-2020): 204 gaps; all size buckets were 'more likely than not' filled by Wednesday London. ForexFactory post: EUR/USD gaps filled 66.15% (period unstated; GBP/USD 72.18% for 2002-2010). fxnx (500 Sunday opens, EUR/USD+GBP/USD+USD/JPY, methodology undisclosed): gaps < 0.50x daily ATR filled within 48h 88.4% (EUR/USD); gaps > 0.75x ATR filled within 24h only 28.2%, within the week 41.9%. EarnForex: average weekly gap ~70% of Friday's open-close range; no correlation between gap size and surrounding ranges. MQL5 forum anecdote: 98% of gaps over 18 months filled 'at some point'.
- **Notes:** Fill rates of 65-90% are consistent across sources but are mostly 'eventually filled' numbers; small gaps are also only a few pips, so after spread the edge is thin. Large (news) gaps fill much less often.
- **Sources:** <https://www.dailyforex.com/forex-articles/2020/06/forex-gap-trading/144786>; <https://www.forexfactory.com/thread/post/6522850>; <https://fxnx.com/en/blog/forex-weekend-gap-size-500-sunday-opens-their-fill-rates>; <https://earnforex.com/guides/forex-weekly-gap-statistics>; <https://www.poundsterlinglive.com/eurusd/6708-eur-usd-increased-chance-of-gap-being-filled>

### S17. RSI range-trading restricted to 14:00-06:00 ET (DailyFX time-of-day study)
- **Timeframes:** M15, H1  |  **Session filter:** Asian + late-NY hours only  |  **Evidence:** vendor backtest
- **Entry:** DailyFX/FXCM 2011-2015 study: a simple RSI(14) range strategy (buy when RSI crosses up through 30, sell when it crosses down through 70) was unprofitable on EUR/USD 24h over 10 years but produced a rising equity curve when trades were only opened between 14:00 ET and 06:00 ET (i.e., outside London/NY overlap).
- **Exit:** Opposite RSI signal or fixed target.
- **Stop:** Not specified in excerpts; FXCM recommended >= 1:1 reward:risk.  |  **Target:** Not specified.
- **Parameters (defaults):** `{"rsi_len": 14, "os": 30, "ob": 70, "allowed_hours_et": "14:00-06:00"}`
- **Claimed performance (as reported):** Qualitative: 'results not good' 24h; positive equity curve with time filter for EUR/USD and USD/CHF, 'fairly well' GBP/USD, no positive curve for USD/JPY, AUD/USD, NZD/USD over 6 years. A separate FXCM traits study: EUR/USD retail trades were profitable 59% of the time but average loss > average gain. No win rate for the filtered strategy found.
- **Notes:** Broker research; still one of the few published hour-of-day conditional results for EUR/USD mean reversion.
- **Sources:** <https://dailyfx.com/forex/technical/article/special_report/2011/12/12/When_is_the_Best_Time_of_Day_to_Trade_Forex.html>; <https://www.fxcm.com/eu/insights/top-5-traits-of-successful-traders/>; <https://www.dailyfx.com/forex/technical/article/special_report/2012/07/21/Improving_Profitability_with_Intraday_Seasonality.html>

### S18. Local-trading-hours depreciation (Breedon & Ranaldo): short EUR in European hours, long in US hours
- **Timeframes:** H1  |  **Session filter:** full-day  |  **Evidence:** rigorous backtest
- **Entry:** Breedon & Ranaldo (SNB WP 2011-04; 10 years of high-frequency data): currencies depreciate during their own local trading hours. Strategy: sell EUR/USD at the European open (07:00-08:00 London), cover at ~13:00 London; buy EUR/USD at the US open (13:00-14:00 London) and close at the NY close.
- **Exit:** Time-based.
- **Stop:** None in paper.  |  **Target:** Time exit.
- **Parameters (defaults):** `{"short_window_london": "08:00-13:00", "long_window_london": "13:00-21:00"}`
- **Claimed performance (as reported):** Authors state the pattern yields a 'simple, profitable trading strategy' for EUR/USD and appears in order flow (local participants net buy foreign currency in their hours); magnitudes not extracted from excerpts.
- **Notes:** Consistent with S14 (fix-related USD demand). Easy to replicate on hourly data; must be re-checked post-2011.
- **Sources:** <https://www.snb.ch/en/publications/research/working-papers/2011/working_paper_2011_04>; <https://econpapers.repec.org/RePEc:qmw:qmwecw:694>; <https://swlb1.aeaweb.org/conference/2009/retrieve.php?pdfid=301>

### S19. Liquidity sweep reversal with killzone filter (Backtrex 5-year test)
- **Timeframes:** H1, M15  |  **Session filter:** killzones  |  **Evidence:** vendor backtest
- **Entry:** Backtrex rules: identify equal highs/lows (liquidity) on H1; a sweep = price exceeds the level by >= 3 pips and the candle closes back inside; all conditions evaluated on the previous confirmed candle; only take setups inside ICT killzones (London 02:00-05:00 ET, NY 07:00-10:00 ET); enter at next open against the sweep.
- **Exit:** Fixed R multiple.
- **Stop:** Beyond the sweep extreme.  |  **Target:** Next liquidity level or fixed 1:2.
- **Parameters (defaults):** `{"sweep_min_pips": 3, "liquidity_tf": "H1", "killzones_et": ["02:00-05:00", "07:00-10:00"]}`
- **Claimed performance (as reported):** Backtrex blog (vendor, 2019-2024, 'OHLC tick-faithful'): EURUSD H1 win rate 52.8%, PF 1.63; XAUUSD 53.7%, PF 1.75; combined 1,247 trades, PF 1.68, win 53.2%. Internal inconsistencies: per-instrument trade counts quoted elsewhere on the page (1,743 and 1,504, and '74 trades' in another excerpt) do not reconcile with 1,247.
- **Notes:** Only positive vendor ICT result found and it comes from a blog post (marketing) rather than the vendor's 'backtests' section, whose published EUR/USD and GBP/USD ICT runs all lose. Treat PF 1.6 as an upper bound.
- **Sources:** <https://backtrex.com/en/blog/liquidity-sweep-strategy-backtest-results>; <https://backtrex.com/en/blog/new-york-killzone-ict-liquidity-sweep-strategy-guide>; <https://backtrex.com/en/blog/ict-turtle-soup-reversal-strategy>


## 2. Breakout / trend

### T01. Turtle System 1 / Donchian 20-10 on daily bars
- **Timeframes:** D1, H4  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** Buy stop at the highest high of the last 20 days; sell stop at the lowest low of the last 20 days (original Turtle rule skips the signal if the previous S1 trade was a winner).
- **Exit:** Long: close below the 10-day low; short: close above the 10-day high.
- **Stop:** 2 x N where N = 20-day ATR (original); Backtrex stop not confirmed.  |  **Target:** None (trailing channel exit).
- **Parameters (defaults):** `{"entry_len": 20, "exit_len": 10, "atr_len": 20, "stop_atr_mult": 2, "units": "risk 1% per N"}`
- **Claimed performance (as reported):** Backtrex (vendor, EUR/USD D1, 2016-10-02 to 2026-10-01): 80 trades, PF 0.94, total -2.7%, max DD -14.6%; buy-and-hold +0.1%; one search summary quoted 40% win rate (unconfirmed). Take Profit app (vendor, EURUSD H4 20/10, '250 trading days' 2024-2025): 84 setups, 50.0% win rate, avg R:R 1:3.4, PF 2.15. MQL5 default-setting run on EURUSD H4 (2026): PF 0.88-0.89. 10-pair 2015-2024 blog: 20-period Donchian average win rate 38%, avg win 2.8x avg loss (not EUR/USD-specific).
- **Notes:** Decade result is essentially zero after costs: EUR/USD spent 2016-2026 in a 1.03-1.25 band. The one positive number (PF 2.15) is a one-year vendor sample that includes the 2025 trend.
- **Sources:** <https://backtrex.com/en/backtests/turtle-trading-eur-usd>; <https://takeprofitapp.com/pl/learn/donchian-channels-trading>; <https://www.mql5.com/en/blogs/post/773712>; <https://en.wikipedia.org/wiki/Donchian_channel>; <https://tradingwithrayner.com/turtle-trading-rules>

### T02. Turtle System 2 / Donchian 55-20
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Enter on a 55-day high (low) breakout, no skip rule.
- **Exit:** 20-day opposite breakout.
- **Stop:** 2 x ATR(20).  |  **Target:** None.
- **Parameters (defaults):** `{"entry_len": 55, "exit_len": 20, "stop_atr_mult": 2}`
- **Claimed performance (as reported):** none found
- **Notes:** No EUR/USD decade-long result found. Expect ~2-4 trades/year; the 2014-15 and 2022 and 2025 trends are the only large winners in the last decade.
- **Sources:** <https://en.wikipedia.org/wiki/Donchian_channel>; <https://therighttrader.com/learn/indicator-strategies/donchian-channels-and-adx-strategy>

### T03. Golden/death cross: SMA50 x SMA200 (daily)
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Long when SMA(50) closes above SMA(200); short when it closes below.
- **Exit:** Opposite cross.
- **Stop:** None (or 3 x ATR(14)).  |  **Target:** None.
- **Parameters (defaults):** `{"fast": 50, "slow": 200, "type": "SMA (EMA variant common)"}`
- **Claimed performance (as reported):** No decade-long EUR/USD result found. TradesViz community SMA-cross test: 27 trades, PF 0.60, max DD -2.94% (period unstated). Forextester daily 3-month test (2021) with 36 trades was loss-making and internally inconsistent. Golden-cross Pine scripts quoting PF 2-3 are on NFLX/AAPL/NVDA, not FX.
- **Notes:** Most common lengths cited for EUR/USD by retail sources: 50/200 (daily), 20/50 EMA (H4/H1), 10/20 SMA (daily), 7/14 (Dukascopy contest example, M1/H1), 9/21 EMA (intraday).
- **Sources:** <https://www.tradesviz.com/shared/backtests/6fb14389-9523-4fa0-8157-992f2cf45333/>; <https://forextester.com/blog/ma-crossover-strategy>; <https://www.luxalgo.com/blog/2-moving-average-crossover-strategies-explained/>

### T04. EMA 20/50 crossover with price filter (H4/H1)
- **Timeframes:** H1, H4  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Long when EMA(20) > EMA(50) and price closes above EMA(20) after a pullback to it; short mirrored. Dukascopy contest sample: MA(7) x MA(14) on M1/H1 with TP 10 / SL 20 pips.
- **Exit:** Opposite cross, or fixed TP/SL.
- **Stop:** Below the pullback swing low or 1.5 x ATR(14).  |  **Target:** 2 x risk, or trail with EMA(50).
- **Parameters (defaults):** `{"fast": 20, "slow": 50, "atr_len": 14, "sl_atr": 1.5, "rr": 2}`
- **Claimed performance (as reported):** none found
- **Notes:** Ubiquitous; no credible EUR/USD stat found. Backtrex's MACD+RSI H1 result (T05) is the closest proxy for 'fast indicator crossover on H1' and it is strongly negative.
- **Sources:** <https://www.dukascopy.com/swiss/english/forex/jforex/forum/viewtopic.php?p=15097>; <https://forextester.com/blog/ema-rsi-strategy>; <https://www.tradingview.com/script/Is0LQdiz-Smoothed-Heikin-Ashi-Trend-on-Chart-TraderHalai-BACKTEST>

### T05. MACD(12,26,9) signal cross, with RSI filter (Backtrex) or alone
- **Timeframes:** H1, D1  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** Backtrex H1: long when MACD line crosses above signal and RSI(14) > 50; short mirrored. Plain: MACD line crosses signal line.
- **Exit:** Fixed SL/TP (Backtrex) or opposite cross.
- **Stop:** Backtrex: 45 pips.  |  **Target:** Backtrex: 90 pips.
- **Parameters (defaults):** `{"fast": 12, "slow": 26, "signal": 9, "rsi_len": 14, "sl_pips": 45, "tp_pips": 90}`
- **Claimed performance (as reported):** Backtrex (vendor, EUR/USD H1, 2016-10-02 to 2026-10-01): 1,977 trades, PF 0.80, total -53.4%, max DD -56.7%; buy-and-hold ~flat. TradesViz daily 12/26/9 long-only with stops: PF 1.34 on 13 trades (instrument unconfirmed). Liberated Stock Trader on DJIA daily: 3% 'success rate' (not FX).
- **Notes:** Backtrex's explanation: H1 signals fire constantly inside ranges while the pair went nowhere for a decade.
- **Sources:** <https://backtrex.com/en/backtests/macd-rsi-eur-usd>; <https://www.tradesviz.com/shared/backtests/e9c97fb3-1d4b-448d-83ad-32f876b77f1c/>; <https://liberatedstocktrader.com/?p=24867>

### T06. ADX(14) > 25 trend filter on any trend entry
- **Timeframes:** H1, H4, D1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Take trend-following entries (T01-T05) only when ADX(14) > 25 and +DI/-DI agree with direction; stand aside when ADX < 20. Variant: ADXR smoothed.
- **Exit:** Host strategy; some exit when ADX turns down from > 40.
- **Stop:** Host strategy.  |  **Target:** Host strategy.
- **Parameters (defaults):** `{"adx_len": 14, "trend_threshold": 25, "no_trade_threshold": 20}`
- **Claimed performance (as reported):** Babypips HLHB system (EUR/USD H1, 2016-2017): adding ADX(14) raised win rate and average pips per win but reduced total pips vs the unfiltered version; author suspected it filtered out real trends. A marketing page shows -$7.23 net on an ADX EURUSD hourly strategy. No rigorous result.
- **Notes:** Standard filter; the only public EUR/USD evidence is mixed.
- **Sources:** <https://www.babypips.com/trading/forex-hlhb-system-20170212>; <https://www.babypips.com/trading/forex-hlhb-system-20170219>; <https://www.mql5.com/en/articles/22754>

### T07. Ichimoku (9/26/52) Kumo breakout / Chikou cross
- **Timeframes:** D1, H4  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** Long when price closes above the Kumo, Tenkan > Kijun, and Chikou span is above price 26 bars ago; short mirrored. EarnForex EA variant: entry on Chikou span crossing price.
- **Exit:** Tenkan/Kijun cross against position or close back inside the cloud.
- **Stop:** Below Kijun-sen or cloud bottom.  |  **Target:** None (trend exit).
- **Parameters (defaults):** `{"tenkan": 9, "kijun": 26, "senkou_b": 52, "displacement": 26}`
- **Claimed performance (as reported):** EarnForex Ichimoku Chikou Cross EA, EUR/USD D1 2001-2013: net profit $6,696 on $10,000 (+67%), max relative DD 8.08%; the same EA on 2013-01-01 to 2022-04-14 'complete account wipeout'. Babypips forum claim: 30,341 pips over 5 years on D1 with no SL/TP (unverified). MQL5 signal 'Tochi Flow EURUSD only': PF 239.86 on 247 trades but 66.02% equity drawdown (grid-style).
- **Notes:** Clear regime dependence: profitable in the trending 2001-2013 era, wiped out 2013-2022.
- **Sources:** <https://www.earnforex.com/metatrader-expert-advisors/Ichimoku-Chikou-Cross>; <https://forums.babypips.com/t/ichimoku-kinko-hyo-methodology-used-on-school-of-pipsology/49727>; <https://www.mql5.com/en/signals/2346630>

### T08. Bollinger/Keltner squeeze (TTM squeeze) breakout
- **Timeframes:** H1, H4, D1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Squeeze on when Bollinger(20, 2.0) upper/lower are inside Keltner(20, 1.5 x ATR(20)). Enter on the first bar where the bands move back outside the Keltner channel, in the direction of momentum (close - midpoint of (highest high + lowest low)/2 and SMA, linear-regression slope) or the direction of the breakout candle.
- **Exit:** Momentum histogram turns toward zero, or opposite band touch.
- **Stop:** Opposite Keltner band or 1.5 x ATR.  |  **Target:** 2 x ATR or band walk exit.
- **Parameters (defaults):** `{"bb_len": 20, "bb_mult": 2.0, "kc_len": 20, "kc_mult": 1.5, "atr_len": 20}`
- **Claimed performance (as reported):** none found
- **Notes:** No EUR/USD performance numbers found anywhere. John Carter never published a win rate; different Keltner formulas make vendor results non-comparable.
- **Sources:** <https://www.luxalgo.com/library/concept/ttm-squeeze.md>; <https://medium.com/superalgos/a-quantitative-study-of-the-bollinger-bands-squeeze-strategy-9f47143f33fb>; <https://therighttrader.com/pt/learn/indicators/ttm-squeeze>

### T09. Inside-bar (inside day) breakout
- **Timeframes:** D1, H4  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Inside day = today's high < yesterday's high and today's low > yesterday's low. Place buy stop at mother-bar high + 2 pips and sell stop at mother-bar low - 2 pips for the next session; cancel the other on fill.
- **Exit:** Fixed R or close after N days.
- **Stop:** Opposite side of the inside bar (tight) or of the mother bar (wide).  |  **Target:** 1x mother-bar range, or 2R.
- **Parameters (defaults):** `{"buffer_pips": 2, "stop": "inside bar opposite side", "target_R": 2, "hold_days_max": 5}`
- **Claimed performance (as reported):** Currency Trader (Chris Peters) study, 7 pairs incl. EUR/USD, daily, Jan 1993-Sep 2008: 4,174 inside days (avg 596 per pair, ~3/month/pair); inside days were followed by positive (upward-biased) moves over the following week; per-day averages roughly 0.1-0.3% (table garbled in available copy). Forum study (EUR/USD daily since 2003): average inside-bar range 82.7 pips vs ~117 pips average day; average range of the day after an inside bar 124 pips. MQL5 post: EUR/USD M15 was the only inside-bar setup stable in both back and forward test (no figures).
- **Notes:** The range-expansion-after-contraction fact (124 vs 82.7 pips) is the useful bit; direction is not predicted.
- **Sources:** <https://www.scribd.com/document/496411061/CurrencyTrader1108s4>; <https://www.forexpeacearmy.com/community/threads/eur-usd-study.13340/latest>; <https://www.mql5.com/en/blogs/post/771362>; <https://www.edgeful.com/blog/posts/inside-bars-report>

### T10. NR7 / ID-NR4 range-contraction breakout (Crabel)
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** NR7: today's high-low range is the narrowest of the last 7 days. Next day, buy stop at today's high + buffer, sell stop at today's low - buffer (ID/NR4: inside day that is also the narrowest of 4).
- **Exit:** Close of the breakout day (Crabel's original) or trailing.
- **Stop:** Opposite side of the NR7 bar.  |  **Target:** End of day or 1x ADR(10).
- **Parameters (defaults):** `{"lookback": 7, "buffer_pips": 2, "exit": "breakout-day close"}`
- **Claimed performance (as reported):** none found
- **Notes:** No EUR/USD NR7 statistics found. Overlaps T09; the 2023 minimum daily range of 28 pips (Aug) shows how small NR days can get.
- **Sources:** <https://tradingsetupsreview.com/inside-daynr4>; <https://www.marketinout.com/stock-screener/nr7-inside-day/europe?view=charts>

### T11. Supertrend (10, 3) trend following
- **Timeframes:** H1, H4, D1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Long when close crosses above the Supertrend line (ATR(10) x 3 band flip); short when it crosses below.
- **Exit:** Opposite flip.
- **Stop:** The Supertrend line itself (trailing).  |  **Target:** None.
- **Parameters (defaults):** `{"atr_len": 10, "mult": 3.0}`
- **Claimed performance (as reported):** HackerNoon multi-year test of TradingView's Supertrend strategy on NZDUSD (not EUR/USD): M15/H1/H4 all lost, PF 0.80-0.86; D1 the only positive line with 3 trades making 88% of profit. No EUR/USD figures.
- **Notes:** Expect the same profile on EUR/USD: whipsaw losses intraday, a few big daily winners.
- **Sources:** <https://hackernoon.com/the-truth-about-tradingviews-supertrend-strategy-after-67-years-of-backtesting>; <https://www.mql5.com/en/blogs/post/759888>; <https://forextester.com/blog/supertrend-indicator/>

### T12. Parabolic SAR (0.02, 0.2) flip
- **Timeframes:** M30, D1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Long when price closes above the SAR dots (SAR flips below price); short when it flips above.
- **Exit:** Next flip.
- **Stop:** SAR value (trailing).  |  **Target:** None.
- **Parameters (defaults):** `{"af_start": 0.02, "af_step": 0.02, "af_max": 0.2}`
- **Claimed performance (as reported):** EA31337 gist: SAR on EURUSD M30, one month, PF 0.59. DEV Community 'AI-evolved' SAR on EURUSD D1: +150% in-sample over 2,680 candles, 336 trades, max DD 7.4%, PF 2.3 (an earlier draft said 2.62), self-described experiment, in-sample only.
- **Notes:** Nothing credible. Useful only as a trailing-stop mechanism.
- **Sources:** <https://gist.github.com/EA31337-Tester/a3bdfd7893207e24d1a6f664e71ddfac>; <https://dev.to/howiprompt/how-our-ai-agents-evolved-parabolicsar-on-eurusd-to-150-backtested-1-evolutions-2c0l>; <https://www.mql5.com/en/forum/177353/page2>

### T13. Heikin-Ashi trend continuation with EMA filter
- **Timeframes:** H1, H4  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Long after two consecutive bullish Heikin-Ashi candles with no lower wick while price is above EMA(100) (MQL5 variant) or EMA(20) > EMA(50) (TradingView variant); short mirrored.
- **Exit:** First opposite-colour HA candle with a wick, or EMA cross.
- **Stop:** Below the last HA swing low / 1.5 x ATR.  |  **Target:** Trail.
- **Parameters (defaults):** `{"ema_filter": 100, "confirm_candles": 2}`
- **Claimed performance (as reported):** none found
- **Notes:** MQL5 EUR/USD M30 test (Jan 2022-Jul 2023) reported no figures. No stats found.
- **Sources:** <https://www.mql5.com/en/forum/450268>; <https://www.tradingview.com/script/Is0LQdiz-Smoothed-Heikin-Ashi-Trend-on-Chart-TraderHalai-BACKTEST>; <https://www.prorealcode.com/prorealtime-trading-strategies/heikin-ashi-during-trend>

### T14. ATR trailing stop / Chandelier exit as the exit engine
- **Timeframes:** H1, H4, D1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Not an entry. Chandelier exit: long stop = highest high(22) - 3 x ATR(22); short stop = lowest low(22) + 3 x ATR(22). Generic ATR trail: stop = close - k x ATR(14), k in [1.5, 3], ratcheted only in the trade's favour.
- **Exit:** Stop hit.
- **Stop:** As above.  |  **Target:** None.
- **Parameters (defaults):** `{"chandelier_len": 22, "chandelier_mult": 3.0, "atr_len": 14, "k_range": [1.5, 3.0]}`
- **Claimed performance (as reported):** No EUR/USD comparison of multipliers found; a student grid search (daily EURUSD, ATR mult 0.75-1.5, R:R 1.5-3) reported underperformance attributed to timeframe, figures not shown.
- **Notes:** Parameter sweep is cheap; this is an exit module for T01/T03/T11.
- **Sources:** <https://tamaraabu4-cell.github.io/quant-study-notes/projects/turtle-soup.html>; <https://in.tradingview.com/script/U4hsXLAF-ATR-1-5-FX-Stop-Loss>; <https://fr.tradingview.com/script/KO7Qe4Xb-Strategy-Validation-Framework-Standardised-ATR-Exits-1-Ris/>

### T15. Larry Williams volatility breakout: open +/- k x previous range
- **Timeframes:** M5, D1  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** At the day's open: buy stop = open + k x (previous day high - low); sell stop = open - k x (previous range). WHS default k = 0.25, 5-minute chart. Variant: use yesterday's true range or 3-day average range.
- **Exit:** Close at 21:59 (WHS time filter) if neither stop nor target hit; one trade per day.
- **Stop:** 2 x the breakout band (WHS default) or opposite band.  |  **Target:** 2 x the breakout band.
- **Parameters (defaults):** `{"k": 0.25, "range_lookback": 1, "sl_mult": 2, "tp_mult": 2, "time_exit": "21:59 platform time"}`
- **Claimed performance (as reported):** WHS (broker marketing): 'backtests over several years show variable but never negative profits' (no figures published). MQL5 forum opinion: EUR/USD lacks the volatility for this, GBP/USD better. ProRealCode: ATR 'doesn't change much for EURUSD' explaining weak volatility-system results. RogueQuant 15-market 2014-2024 test did not clearly report EURUSD.
- **Notes:** Daily-open-anchored cousin of S01; k and the 'open' definition (00:00 UTC vs 22:00 UTC vs London open) are the key parameters.
- **Sources:** <https://whselfinvest.com/en-be/trading-platform/free-trading-strategies/tradingsystem/56-volatility-break-out-larry-williams-free>; <https://www.mql5.com/en/forum/173441/page7>; <https://prorealcode.com/prorealtime-trading-strategies/eurusd-volatilitybreakout-strategy/?pnum=3>; <https://roguequant.substack.com/p/i-backtested-larry-williams-trading>

### T16. Previous day high/low breakout (continuation)
- **Timeframes:** H1, M15  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** Buy stop at previous day's high + buffer, sell stop at previous day's low - buffer, active during London/NY; Backtrex GBP/USD H1 implementation.
- **Exit:** Fixed SL/TP or end-of-day.
- **Stop:** Fixed pips or midpoint of prior day.  |  **Target:** Fixed pips, 1-2x risk.
- **Parameters (defaults):** `{"buffer_pips": 2, "session": "07:00-17:00 London"}`
- **Claimed performance (as reported):** Backtrex (vendor, GBP/USD H1, 2016-2026): listed as losing money; win rate/PF not visible in search excerpts. No EUR/USD run found. MQL5 forum pivot study (EUR/USD 2003-2010): daily high exceeded R1 43.1%, R2 20.4%, R3 6.3%; low below S1 45.3%, S2 21.5%, S3 6.6% (pivot-based, not PDH/PDL).
- **Notes:** Probability of taking out PDH or PDL for EUR/USD specifically was not found; see facts section for the pivot-level proxies. Edgeful sells this exact report.
- **Sources:** <https://backtrex.com/en/backtests/previous-day-high-low-breakout-gbp-usd>; <https://www.edgeful.com/blog/posts/previous-days-range-report>; <https://mql5.com/en/forum/2724>

### T17. Time-series momentum (12-month, 1-month, 3-month lookbacks)
- **Timeframes:** D1, MN  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** At month end (or daily with monthly rebalance): long EUR/USD if the trailing 12-month return (excess of carry) > 0, short if < 0; variants use 1-, 3-, 12-month signals equally weighted (Hurst-Ooi-Pedersen) and scale position to 10-40% annualized vol target.
- **Exit:** Signal flip at rebalance.
- **Stop:** None (vol scaling).  |  **Target:** None.
- **Parameters (defaults):** `{"lookbacks_months": [1, 3, 12], "vol_target": 0.1, "rebalance": "monthly", "skip_month": false}`
- **Claimed performance (as reported):** EPAT walk-forward study (7 majors, 2003-2025, out-of-sample): only USD/JPY (Sharpe 0.78) and EUR/USD (Sharpe ~0.54) cleared a 0.5 Sharpe bar using time-series momentum; best equal-weight portfolio CAGR 1.24%, Sharpe 0.43, max DD -8.25%. Hurst-Ooi-Pedersen (1880-2016, 67 assets): 1/3/12-month TSMOM positive in every decade; a skip month hurts. Quantpedia cross-sectional 12m FX momentum: Sharpe 0.3, max DD -45.87%. Krohn et al.: G10 momentum profits accrue mostly overnight.
- **Notes:** Low Sharpe but the only trend approach with out-of-sample academic support on EUR/USD; signal is slow (a few flips per year).
- **Sources:** <https://www.quantinsti.com/articles/trend-following-strategies-major-currency-markets-epat-project/>; <https://quantpedia.com/strategies/currency-momentum-factor>; <https://www.cxoadvisory.com/momentum-investing/trend-following-with-intrinsic-momentum-over-the-very-long-run>; <https://acfr.aut.ac.nz/__data/assets/pdf_file/0007/190753/Krohn_Mueller_Whelan_Jun2018_FXPremiaAroundTheClock.pdf>

### T18. Fractal breakout intraday (ProRealCode EUR/USD H1 system)  *(rules reconstructed)*
- **Timeframes:** H1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Williams fractal (5-bar) high/low on H1; buy stop above the most recent up-fractal, sell stop below the most recent down-fractal, London/NY hours only (community system, many iterations in thread).
- **Exit:** Fixed TP/SL plus time exit.
- **Stop:** Opposite fractal or fixed ~30 pips.  |  **Target:** Fixed ~40-60 pips or trailing.
- **Parameters (defaults):** `{"fractal_len": 5, "hours": "08:00-20:00 CET"}`
- **Claimed performance (as reported):** none found
- **Notes:** 20+ page forum thread with screenshots only; no reproducible stats extracted.
- **Sources:** <https://www.prorealcode.com/reply/32837>; <https://www.prorealcode.com/topic/fractal-breakout-intraday-strategy-eurusd-1h/page/20/>


## 3. Mean reversion

### M01. Connors RSI(2) on daily bars
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** Long when close > SMA(200) and RSI(2) < 5 (StockCharts/Backtrex) or < 10 (common variant); short when close < SMA(200) and RSI(2) > 95 (or > 90). Entry at close.
- **Exit:** Close > SMA(5) for longs (close < SMA(5) for shorts); Backtrex also exits if price crosses the 200-day SMA.
- **Stop:** None in original.  |  **Target:** SMA(5) exit.
- **Parameters (defaults):** `{"rsi_len": 2, "long_threshold": 5, "short_threshold": 95, "trend_sma": 200, "exit_sma": 5}`
- **Claimed performance (as reported):** Backtrex (vendor, EUR/USD D1, 2016-10-02 to 2026-10-01): 75 trades, 54.7% winners, PF 0.78, total -4.5%, max DD -6.6%; average loss 0.62% > average win 0.41%. Vendor's explanation: indices supply mean reversion plus upward drift, EUR/USD has only weak mean reversion and no drift. TradingView 80-symbol 2007-2014 community test: 58.4% wins, +32,552 pips, no costs/out-of-sample.
- **Notes:** Clean negative result on EUR/USD; high win rate, negative expectancy.
- **Sources:** <https://backtrex.com/en/backtests/connors-rsi-2-eur-usd>; <https://chartschool.stockcharts.com/table-of-contents/trading-strategies-and-models/trading-strategies/rsi-2>; <https://www.mql5.com/en/articles/17636>; <https://it.tradingview.com/scripts/rsi-2/page-7>

### M02. RSI(14) 30/70 extremes (daily or H4)
- **Timeframes:** H4, D1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Long when RSI(14) crosses back above 30; short when it crosses back below 70. Variants add divergence or require a candle confirmation.
- **Exit:** RSI(14) reaches 50 (or the opposite band), or fixed R.
- **Stop:** Recent swing beyond the extreme, or 1.5 x ATR(14).  |  **Target:** RSI 50 / middle Bollinger band.
- **Parameters (defaults):** `{"rsi_len": 14, "os": 30, "ob": 70}`
- **Claimed performance (as reported):** none found
- **Notes:** No EUR/USD daily win rate found. The only conditional result is DailyFX's hour-of-day filter (S17).
- **Sources:** <https://dailyfx.com/forex/technical/article/special_report/2011/12/12/When_is_the_Best_Time_of_Day_to_Trade_Forex.html>; <https://www.babypips.com/school/what-is-the-most-profitable-indicator.html>

### M03. Bollinger band (20, 2) fade to the middle band
- **Timeframes:** H1, D1, M1  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** Long when close < lower band (20, 2.0) and (optionally) RSI(14) < 30; short when close > upper band and RSI > 70. NautilusTrader tutorial: BBMeanReversion with RSI filter on 1-minute bars.
- **Exit:** Close crosses the 20-period SMA (middle band).
- **Stop:** 1 x band width beyond entry, or 2 x ATR(14).  |  **Target:** Middle band.
- **Parameters (defaults):** `{"len": 20, "mult": 2.0, "rsi_filter": [30, 70]}`
- **Claimed performance (as reported):** AvaTrade 'demo backtest' (no dates/timeframe): 120 trades, 56% win rate, PF 1.45. cTrader bot listings: 56-61% win rates, PF 1.2+ on ~100 trades (sales pages). NautilusTrader Dec-2025 1-minute example: no win rate; notes 'mean reversion without a regime filter pays the spread on every cycle' and the month trended. QuantConnect snippet: 6% win rate, negative (settings unknown).
- **Notes:** Nothing above 'vendor demo' quality. The ProRealCode EUR/USD 1H thread's 'too good to be true' results used spread 0.8.
- **Sources:** <https://www.avatrade.com/education/technical-analysis-indicators-strategies/bollinger-bands-trading-strategies>; <https://nautilustrader.io/docs/latest/tutorials/fx_mean_reversion_ax/>; <https://www.prorealcode.com/topic/mean-reversion-trading-system-eur-usd-1h>; <https://ctrader.com/products/2304>

### M04. Z-score of price vs SMA(20) (+/-2 sigma fade)
- **Timeframes:** M5, H1, D1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** z = (close - SMA(20)) / stdev(20). Long when z crosses below -2 and then back above -2 (re-entry); short when z crosses above +2 and back below.
- **Exit:** z crosses 0.
- **Stop:** z beyond +/-3, or 2 x ATR.  |  **Target:** z = 0.
- **Parameters (defaults):** `{"len": 20, "entry_z": 2.0, "exit_z": 0.0, "stop_z": 3.0}`
- **Claimed performance (as reported):** Community scripts claim '68% win rate on 1-5 min' (unverified). Backtrex guide gives generic targets (max DD < 15-20% over 3 years, Sharpe > 0.8) rather than results. Cautionary example cited everywhere: 2014-15 EUR/USD 1.40->1.05 decline repeatedly stopped out z-score faders.
- **Notes:** Mathematically the same trade as M03. Academic support for intraday mean reversion in EUR/USD exists (Wisniewska 2014 1-min; Middleton et al. 2021) but not at the daily horizon.
- **Sources:** <https://it.tradingview.com/script/IlUJulqm-Z-Score-Mean-Reversion-EURUSD>; <https://backtrex.com/en/blog/mean-reversion-strategy-backtesting-guide>; <https://www.mql5.com/en/articles/24652>

### M05. Classic (floor) pivot point bounce/break
- **Timeframes:** M15, H1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** PP = (H + L + C)/3; R1 = 2PP - L; S1 = 2PP - H; R2 = PP + (H - L); S2 = PP - (H - L); R3 = H + 2(PP - L); S3 = L - 2(H - PP), using the prior day's 00:00-24:00 UTC (or NY-close) bar. Bounce rule: buy at S1 (sell at R1) on a rejection candle when the day opened between S1 and R1; breakout rule: buy a close above R1 targeting R2.
- **Exit:** PP (for bounces) / next level (for breaks); end of day.
- **Stop:** Halfway to the next level (e.g., below S2 for an S1 long: 0.5 x (S1 - S2)).  |  **Target:** PP for bounces; R2/S2 for breaks.
- **Parameters (defaults):** `{"pivot_type": "classic", "day_boundary": "00:00 UTC"}`
- **Claimed performance (as reported):** MQL5 forum study (EUR/USD, 1,965 days, Jan 2003-Nov 2010): high exceeded PP 87.38% / low below PP 85.90% of days; high reached R1 43.10%, R2 20.41%, R3 6.26%; low reached S1 45.34%, S2 21.48%, S3 6.56%. Conditional: when the open was below PP, lows reached S1 50.42% vs 36.20% when the open was above PP.
- **Notes:** These touch frequencies imply R1/S1 are hit on fewer than half of days, which argues for fading R1/S1 rather than buying breaks of them; data is 15 years old.
- **Sources:** <https://mql5.com/en/forum/2724>; <https://www.babypips.com/learn/forex/other-pivot-point-calculation-methods>; <https://capital.com/en-au/learn/trading-strategies/pivot-point-trading>

### M06. Fibonacci pivot points
- **Timeframes:** M15, H1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** PP = (H + L + C)/3; R1 = PP + 0.382 x (H - L); R2 = PP + 0.618 x (H - L); R3 = PP + 1.000 x (H - L); S1 = PP - 0.382 x (H - L); S2 = PP - 0.618 x (H - L); S3 = PP - 1.000 x (H - L). Same bounce/break rules as M05.
- **Exit:** As M05.
- **Stop:** As M05.  |  **Target:** As M05.
- **Parameters (defaults):** `{"ratios": [0.382, 0.618, 1.0]}`
- **Claimed performance (as reported):** none found
- **Notes:** No EUR/USD hit-rate statistics found for this variant.
- **Sources:** <https://www.babypips.com/learn/forex/other-pivot-point-calculation-methods>; <https://www.luxalgo.com/library/concept/fibonacci-pivots.md>

### M07. Camarilla pivots (H3/L3 fade, H4/L4 breakout)
- **Timeframes:** M15, H1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Range = H - L of prior day. H1 = C + Range x 0.0916 (=1.1/12); H2 = C + Range x 0.183 (1.1/6); H3 = C + Range x 0.275 (1.1/4); H4 = C + Range x 0.55 (1.1/2); H5 = (H/L) x C (some vendors); L1..L4 mirrored below C (L3 = C - Range x 0.275, L4 = C - Range x 0.55). Rule: sell at H3 / buy at L3 (expect reversion) with stop beyond H4/L4; if H4/L4 breaks, go with the breakout.
- **Exit:** Fade: target the opposite inner level (L3 from H3) or C. Break: target H5/L5 or 1x range.
- **Stop:** Fade: just beyond H4/L4. Break: back inside H3/L3.  |  **Target:** As exit.
- **Parameters (defaults):** `{"multipliers": {"L1/H1": 0.0916, "L2/H2": 0.183, "L3/H3": 0.275, "L4/H4": 0.55}}`
- **Claimed performance (as reported):** none found
- **Notes:** Sources agree on 1.1/12, 1.1/6, 1.1/4, 1.1/2 multipliers; one source quotes H4 = C + 1.5 x range which is a different convention. No EUR/USD statistics.
- **Sources:** <https://www.babypips.com/learn/forex/other-pivot-point-calculation-methods>; <https://www.strike.money/?p=5102>; <https://in.tradingview.com/scripts/camarillapivot/>

### M08. Woodie pivots
- **Timeframes:** M15, H1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** PP = (H + L + 2C)/4 (some platforms use the current session's open instead of C: (H + L + 2O)/4); R1 = 2PP - L; R2 = PP + (H - L); S1 = 2PP - H; S2 = PP - (H - L). Same rules as M05.
- **Exit:** As M05.
- **Stop:** As M05.  |  **Target:** As M05.
- **Parameters (defaults):** `{"close_weight": 2}`
- **Claimed performance (as reported):** none found
- **Notes:** No statistics.
- **Sources:** <https://www.luxalgo.com/library/concept/woodie-pivots.md>; <https://www.babypips.com/learn/forex/other-pivot-point-calculation-methods>

### M09. Round-number (x.xx00 / x.xx50) reaction and breakout acceleration
- **Timeframes:** M5, M15, H1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Osler (J. Finance 2003, bank order data): take-profit orders cluster exactly on round numbers (00), stop-loss orders cluster just beyond them (buy stops just above, sell stops just below). Rules: (a) fade the first touch of a 00/50 level from a trend (expect reversal); (b) if price closes > 10-15 pips through a 00 level, go with the break (stop cascade). Lallouache & Abergel (EBS EUR/USD order book): volume clusters at round prices, which then act as barriers.
- **Exit:** (a) 20-30 pips or next 50-level; (b) next 00 level.
- **Stop:** (a) 15 pips beyond the level; (b) back below the level.  |  **Target:** As exit.
- **Parameters (defaults):** `{"levels": ["00", "50"], "break_confirm_pips": 12, "fade_stop_pips": 15}`
- **Claimed performance (as reported):** Qualitative academic evidence only (reversal at round numbers; acceleration after breaks). A TradingView post claims ~40% reversal at a level in a given hourly window (unpublished backtest). No EUR/USD hit-rate study found.
- **Notes:** Evidence is for the mechanism, not for a tradable rule's expectancy. Easy to test: conditional 30-min forward return after first touch of a 00 level vs random levels.
- **Sources:** <https://ideas.repec.org/a/bla/jfinan/v58y2003i5p1791-1819.html>; <https://ar5iv.arxiv.org/html/1307.5440>; <https://tradeciety.com/the-order-clustering-effect-around-round-numbers>; <https://icmaif.soc.uoc.gr/Year/8conf/docs/Osler-Price%20Cascades-03-03.doc>

### M10. Previous-day high/low fade ('turtle soup' / failed breakout)
- **Timeframes:** M15, H1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Price trades beyond the prior day's high (low) by 3-10 pips and the M15/H1 candle closes back inside the prior day's range; enter short (long) at the next open with the swept extreme as the stop (Warrior_EA research definition; Connors-Raschke turtle soup uses 20-day highs).
- **Exit:** Prior day's midpoint or opposite extreme; time stop end of day.
- **Stop:** Beyond the sweep extreme + 2 pips.  |  **Target:** Midpoint of prior day range (1st), opposite side (2nd).
- **Parameters (defaults):** `{"sweep_min_pips": 3, "sweep_max_pips": 15, "confirm_tf": "M15"}`
- **Claimed performance (as reported):** No EUR/USD-specific published statistics; Backtrex's liquidity-sweep test (S19) is the nearest (52.8% / PF 1.63, vendor). Vendor material: sweeps typically extend 10-25 pips beyond the level (unmeasured).
- **Notes:** Mirror of T16; the two should be tested together (if PDH breaks continue, T16 wins; if they fail, M10 wins).
- **Sources:** <https://forge.mql5.io/animatedread/Warrior_EA/src/branch/main/research/test_liquidity.py>; <https://backtrex.com/en/blog/ict-turtle-soup-reversal-strategy>; <https://dailypriceaction.com/blog/liquidity-sweep-reversals/>

### M11. Weekly-open mean reversion  *(rules reconstructed)*
- **Timeframes:** H1, H4  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Reference = Sunday 22:00 UTC open. If by Tuesday/Wednesday price is > 1 x ADR(14) from the weekly open, fade toward the weekly open; alternatively buy the first H4 close back through the weekly open after a failed move.
- **Exit:** Weekly open touch or Friday 15:00 London.
- **Stop:** 1 x ADR beyond entry.  |  **Target:** Weekly open.
- **Parameters (defaults):** `{"distance_adr": 1.0, "time_stop": "Friday 15:00 London"}`
- **Claimed performance (as reported):** A self-labelled proprietary page reports a 199-week EUR/USD weekly-open study with 49.7% long win rate (unverifiable). No other statistics found.
- **Notes:** Base rate for 'price returns to the weekly open during the week' not found; must be computed.
- **Sources:** <https://kalaya-research-portal.pages.dev/EURUSD/position>; <https://www.tastyfx.com/news/mean-reversion-in-forex-trading-230712/>

### M12. Daily-open mean reversion (return to the daily open)  *(rules reconstructed)*
- **Timeframes:** M15, H1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Reference = 00:00 UTC (or 22:00 UTC / 17:00 NY) open. After the London session moves >= 0.5 x ADR away from the open without a pullback, fade toward the open in the NY session (variant of S05/S10).
- **Exit:** Daily open or NY close.
- **Stop:** 0.5 x ADR beyond the session extreme.  |  **Target:** Daily open.
- **Parameters (defaults):** `{"open_def": "00:00 UTC", "min_excursion_adr": 0.5}`
- **Claimed performance (as reported):** No study measuring how often EUR/USD revisits its daily open was found. NumXL (EUR/USD daily 2010-2012): open-to-close returns indistinguishable from zero, near-Gaussian. ForexFactory: EUR/USD closed above its open 50.42% of days since inception (1,666 of 3,304; 36 unchanged).
- **Notes:** Key statistic to compute in-house: P(price trades back through the daily open after an excursion of x ADR).
- **Sources:** <https://support.numxl.com/hc/en-us/articles/360032493932-Predict-This>; <https://www.forexfactory.com/thread/post/6036885>; <https://www.edgeful.com/blog/posts/gap-fill-report>

### M13. Fade multi-day directional streaks (tastyfx 3-day streak study)
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** After three consecutive daily closes in the same direction with cumulative move > 1% (tastyfx threshold; they also define a 0.5% day as 'outsized'), enter against the streak at the third close.
- **Exit:** Next day's close (one-day hold) or 2-3 days.
- **Stop:** None in study; practical 1 x ATR.  |  **Target:** Time exit.
- **Parameters (defaults):** `{"streak_days": 3, "min_cum_move_pct": 1.0, "hold_days": 1}`
- **Claimed performance (as reported):** tastyfx (broker, ~6 years of daily closes, major USD pairs): fading 3-day streaks > 1% had win rates > 50% on all majors, EUR/USD highest at 59%; momentum entries underperformed. Sample size, period, costs not disclosed.
- **Notes:** Consistent with the academic next-day contrarian finding (M14); cheap to verify on 20+ years.
- **Sources:** <https://prod.wsprod.tastyfx.com/news/fading-multi-day-dollar-moves-a-quantitative-case-for-mean-reversion>; <https://www.tastyfx.com/news/trading-fx-volatility-shocks-fade-or-follow/>

### M14. Abnormal-day momentum then next-day contrarian (Caporale-Plastun)
- **Timeframes:** H1, D1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Caporale & Plastun (J. Econ. Studies 2020; EURUSD, USDJPY, USDCAD, AUDUSD, EURJPY; 2008-2018 daily and intraday): define an abnormal day as a daily return beyond mean +/- 2 sigma (rolling). On the abnormal day, price continues in the direction of the abnormal move (intraday momentum: enter in the direction once the day is flagged abnormal, exit at close). Next day: price moves against the abnormal day (contrarian: enter at close against the abnormal day, exit next close).
- **Exit:** Close of the same day (momentum leg) / next close (contrarian leg).
- **Stop:** None in paper.  |  **Target:** Time exit.
- **Parameters (defaults):** `{"abnormal_sigma": 2, "window_days": 20}`
- **Claimed performance (as reported):** Paper reports 'strong momentum effect on days with abnormal price changes' and opposite-direction moves the following day; a 2019 Brunel working paper finds the contrarian-after-overreaction strategy 'does not generate profits in FOREX and commodities, but in some cases it does'. A 2014 CESifo paper (EURUSD/USDJPY/GBPCHF) found larger contrarian moves after abnormal days than after normal days. 1994-2019 seven-pair frequency study says abnormal returns 'can be the basis of profitable strategies'. Exact EURUSD returns not extracted.
- **Notes:** Closest thing to a peer-reviewed EUR/USD daily rule; profitability after costs is contested by the authors themselves.
- **Sources:** <https://ideas.repec.org/a/eme/jespps/jes-11-2019-0503.html>; <https://www.brunel.ac.uk/economics-finance-and-accounting/research/pdf/1909-Mar-GMC-Overreactions-and-trading-strategies.pdf>; <https://cesifo.org/DocDL/cesifo1_wp5066.pdf>; <https://cesifo.org/DocDL/cesifo1_wp8196.pdf>

### M15. Quantified Strategies EUR/USD pair strategy (daily)
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** Rules not fully visible in excerpts (page sells the code); page compares 1-day vs 2-day holding periods, implying a short-term mean-reversion entry on daily bars.
- **Exit:** Time exit after 1 (or 2) days.
- **Stop:** None reported.  |  **Target:** Time exit.
- **Parameters (defaults):** `{"hold_days": 1}`
- **Claimed performance (as reported):** Quantified Strategies (vendor, EUR/USD daily): 713 trades, 53.30% win rate, average win 0.53%, average loss -0.47%, CAGR 1.85%, time in market 13.29% (the page text's '53% per trade' is a typo). Implied expectancy ~0.06%/trade (own calculation).
- **Notes:** Positive but tiny edge, before spread (0.06% ~ 6-7 pips at 1.10; a 1-pip round trip is ~15% of it). Their GBP/USD mean-reversion sibling: 315 trades, 1.4% average gain (period unstated).
- **Sources:** <https://www.quantifiedstrategies.com/eurusd-pair-trading-strategy/>; <https://www.quantifiedstrategies.com/?p=1198321>; <https://quantifiedstrategies.substack.com/p/gbpusd-forex-strategy-python-code>


## 4. Volatility

### V01. ATR-based stop/target sizing module
- **Timeframes:** M15, H1, H4, D1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Not an entry. SL = entry -/+ a x ATR(14); TP = entry +/- b x ATR(14); common pairs (a,b) = (1.5, 3), (2, 2), (1, 2); position size = risk% x equity / (a x ATR x pip value). Chandelier: 3 x ATR(22) from highest high.
- **Exit:** SL/TP.
- **Stop:** a x ATR.  |  **Target:** b x ATR.
- **Parameters (defaults):** `{"atr_len": 14, "a": 1.5, "b": 3.0, "risk_pct": 1.0}`
- **Claimed performance (as reported):** none found
- **Notes:** Reference ATR(14, D1) values found: ~102 pips (Dec 2022), 69 pips (2019, with 180-day ATR 57), 87 pips average daily range (2023), 60 pips 10-week average (mid-2026). No EUR/USD multiplier comparison published.
- **Sources:** <https://www.fxstreet.com/education/atr-indicator-explained-201703301902>; <https://in.tradingview.com/script/U4hsXLAF-ATR-1-5-FX-Stop-Loss>; <https://www.vestinda.com/academy/atr-backtesting-strategies-explore-proven-techniques-for-precision-analysis>

### V02. Range contraction -> expansion (ATR percentile / NR-day) filter  *(rules reconstructed)*
- **Timeframes:** D1, H4  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Trade breakouts (S01, T09, T10, T15) only when ATR(5)/ATR(20) < 0.8 or yesterday's range is in the bottom 20% of the last 50 days; trade fades (M03, M04) only when ATR(5)/ATR(20) > 1.2.
- **Exit:** Host strategy.
- **Stop:** Host strategy.  |  **Target:** Host strategy.
- **Parameters (defaults):** `{"short_atr": 5, "long_atr": 20, "contraction_ratio": 0.8, "expansion_ratio": 1.2}`
- **Claimed performance (as reported):** Supporting fact only: EUR/USD day after an inside bar averaged 124 pips vs 82.7-pip inside bar and ~117-pip average day (forum study since 2003).
- **Notes:** Direction-agnostic; the expansion fact is well established, the profitability of trading it is not.
- **Sources:** <https://www.forexpeacearmy.com/community/threads/eur-usd-study.13340/latest>; <https://www.luxalgo.com/blog/inside-bar-breakouts-tight-risk-big-reward/>

### V03. GARCH / Markov-switching volatility regime filter
- **Timeframes:** H1, H4, D1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Fit GARCH(1,1) or MS-GARCH (3 regimes) on EUR/USD log returns; forecast next-period variance; trade trend systems only in the mid-vol regime, mean reversion in the low-vol regime, stand aside (or widen stops) in the high-vol regime. Entropy filter: suppress trades when regime probability entropy is high.
- **Exit:** Host strategy.
- **Stop:** Host strategy; scaled by forecast sigma.  |  **Target:** Host strategy.
- **Parameters (defaults):** `{"model": "GJR-GARCH(1,1) or MS-GARCH(3)", "data": "1-min mid resampled to H1/H4/D1, 2015-2025"}`
- **Claimed performance (as reported):** arXiv 2606.06190 (2026 preprint, EUR/USD 2015-2025): MS-GARCH beats GARCH on out-of-sample volatility forecasting; smoothed Spearman IC 0.5371 vs 0.5264; regime classification certainty 'moderate'; no trading P&L. Robot Wealth ARIMA+GARCH forex test: direction forecasts not clearly profitable after costs.
- **Notes:** Volatility is forecastable; direction is not. Use as a filter/position sizer, not a signal.
- **Sources:** <https://arxiv.org/abs/2606.06190>; <https://robotwealth.com/fitting-time-series-models-to-the-forex-market-are-arimagarch-predictions-profitable>; <https://www.mql5.com/en/articles/22438>

### V04. Implied-volatility / VIX regime filter
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Use EUR/USD 1-month implied vol (or VIX as a risk proxy): when 1M IV < 6 (2024-25 lows 4.9-5.5), expect range days -> favour fades and pivot bounces; when 1M IV > 9 (2022-23 levels, 9.4-11), favour breakouts and widen ATR stops. VIX > 30: EUR/USD-S&P correlation regime shifts (see F-facts).
- **Exit:** Host strategy.
- **Stop:** Host strategy.  |  **Target:** Host strategy.
- **Parameters (defaults):** `{"iv_low": 6.0, "iv_high": 9.0, "vix_stress": 30}`
- **Claimed performance (as reported):** No EUR/USD strategy test with a VIX/IV filter found. IV reference points (Tickmill/ING/Commerzbank 2024-2025): 1M IV 11.0 (Jan 2025) -> 9.0 (Feb) -> 6.5; 7.8 on 21 Jan 2025 from 9.4 peak; 8.35 (Sep 2025) from 9.8; 3M IV 6.47% (3 Oct 2025, lowest since Nov 2024); 1M realised 4.8% vs traded 6.5% (Nov 2025); 1M IV 5.2% 'lowest since before the energy crisis' (undated, ~2024); 1M IV 5.45 vs 2-yr low 4.9 late Mar, 7.1 mid-Apr, realised 4.3 (~2024).
- **Notes:** Level table is useful for regime labelling in backtests.
- **Sources:** <https://www.tickmill.com/blog/fx-options-insights-210125>; <https://www.tickmill.com/blog/fx-options-insights-19925>; <https://www.fxstreet.com/news/eur-holding-up-ing-202511190827>; <https://www.vtmarkets.com/?p=33252>

### V05. NFP straddle (pending orders both sides)
- **Timeframes:** M1, M5  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** At 08:25 ET on NFP Friday (first Friday, 08:30 ET release), place buy stop at pre-release 15-minute high + 5-10 pips and sell stop at low - 5-10 pips (sources quote 12, 15-20, 25-30 pip offsets from mid); cancel the other on fill (OCO).
- **Exit:** Fixed TP or time exit at 09:30 ET; many sources advise exiting within 30 minutes.
- **Stop:** Opposite pending order level (15-30 pips).  |  **Target:** 30-50 pips or trail.
- **Parameters (defaults):** `{"offset_pips": 12, "sl_pips": 20, "tp_pips": 40, "time_exit_et": "09:30"}`
- **Claimed performance (as reported):** FXStreet NFP stress test (2026, six releases): EUR/USD first-hour range median 47.1 pips vs 13.1 pips on a normal weekday hour (3.6x); individual first-hour ranges 21.4, 52.3, 74.4, 53.2, 41.8, 32.3 pips. FXStreet 2018: average 28 pips in the 15 minutes after release and 49 pips over 4 hours (five releases); another 2018 sample: 34-37 pips/15 min, 50-63 pips/4h. FXStreet 2021: almost all pairs return to pre-release levels within an hour. FXStreet 2015: surprises under +/-25K rarely move EUR/USD > 40 pips. Spread widening to 5-10 pips (up to 25 pips) and slippage reported. A blog's 1,000-run Monte Carlo of a 12-pip-offset straddle reflects its own assumptions; thenexttrade quotes 50-60% win rate 'but slippage hurts' (unsourced).
- **Notes:** Median first-hour range of ~47 pips against 20-40 pips of spread+slippage+offset makes the straddle marginal; the 'returns to pre-release level within an hour' finding supports a post-spike fade (V06) instead.
- **Sources:** <https://www.fxstreet.com/analysis/nfp-stress-test-six-payrolls-releases-measured-in-daily-loss-limits-202611050906>; <https://www.fxstreet.com/analysis/how-to-trade-the-us-nfp-with-eur-usd-201808021440>; <https://fxstreet.com/analysis/nfp-cheat-sheet-three-last-minute-things-to-consider-when-trading-the-event-202106041115>; <https://forex.com/ie/trading-academy/courses/advanced-strategies/the-non-farm-payrolls-v-shaped-reversal>; <https://alphatradecircle.pages.dev/blog/prop-firm-news-trading-straddles>

### V06. Post-announcement fade (NFP/CPI V-reversal)  *(rules reconstructed)*
- **Timeframes:** M1, M5  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** FOREX.com 'NFP V-shaped reversal': wait for the initial spike (first 5-10 minutes), then enter against it when a M5 candle closes back toward the pre-release level, targeting the pre-release price. CPI analogue at 08:30 ET.
- **Exit:** Pre-release level or 60 minutes after release.
- **Stop:** Beyond the spike extreme.  |  **Target:** Pre-release price.
- **Parameters (defaults):** `{"wait_minutes": 10, "max_hold_minutes": 60}`
- **Claimed performance (as reported):** FOREX.com single example: EUR/USD fell ~30 pips in 10 minutes then rallied > 60 pips above entry. FXStreet 2021: pairs typically back at pre-release levels within an hour. US CPI (FXStreet 2018 samples): EUR/USD moved 34-37 pips in 15 minutes and 50-63 pips over 4 hours on average; Dec 2022 CPI: 1.0555 -> 1.0648 (+93 pips) immediately.
- **Notes:** Contradicts the straddle (V05): both cannot be right on the same release; the base rate of 'spike reverses within 60 min' is the number to compute.
- **Sources:** <https://forex.com/ie/trading-academy/courses/advanced-strategies/the-non-farm-payrolls-v-shaped-reversal>; <https://www.fxstreet.com/analysis/how-to-trade-the-us-inflation-data-with-eur-usd-201807111106>; <https://www.fxstreet.com/news/eur-usd-soars-as-us-cpi-comes-in-below-expectations-202212131348>


## 5. Price action

### P01. Pin bar (hammer/shooting star) reversal
- **Timeframes:** H4, D1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** TradingHeroes 'Trending Pin Bar' (EUR/USD H4): tail >= 2/3 of candle, body in the top/bottom third, pin bar forms in the direction of the H4 trend (above/below EMA); enter at the close or on a 50% retrace of the pin.
- **Exit:** Next major support/resistance.
- **Stop:** ~5 pips beyond the pin-bar tail.  |  **Target:** Next S/R level (variable R).
- **Parameters (defaults):** `{"tail_ratio": 0.667, "sl_buffer_pips": 5}`
- **Claimed performance (as reported):** TradingHeroes Forex Tester run (EUR/USD H4): 78% win rate, 446.13% compounded return (period, trade count, costs not given; author warns of backtest limits). Same author on a pin-bar + RSI variant: 'mediocre' return despite a good win rate. 'EBP daily bias strategy 88% proven win rate' video claim (unverified).
- **Notes:** Discretionary S/R targets make this non-reproducible; code a fixed-R version.
- **Sources:** <https://www.tradingheroes.com/?p=15765>; <https://www.tradingheroes.com/?p=10805>; <https://recapio.com/digest/the-most-profitable-daily-bias-strategy-ebp-88-proven-win-rate-by-omar-agag>

### P02. Engulfing candle reversal
- **Timeframes:** H1, H4, D1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Bearish engulfing: candle opens above and closes below the prior candle's body (strict: full range). Enter at the close of the engulfing bar, counter to the prior move.
- **Exit:** 2R or opposite signal.
- **Stop:** Beyond the engulfing candle's extreme.  |  **Target:** 2R.
- **Parameters (defaults):** `{"strict_range": false, "rr": 2}`
- **Claimed performance (as reported):** ForexOp MetaTrader detector test on EUR/USD: after a bearish engulfing, next move up 50.9% / down 49.1% (coin flip). DailyFX 2023 'Mystery of bearish engulfings' reached a similar sceptical conclusion. Video claims of 80%+ win rates are unverified.
- **Notes:** The one systematic test says no edge on EUR/USD.
- **Sources:** <https://forexop.com/strategy/engulfing-candle-trade/>; <https://www.dailyfx.com/analysis/the-mystery-of-bearish-engulfings-do-they-reliably-predict-forex-price-reversals-20230528.html>

### P03. Outside bar (engulfing range) momentum
- **Timeframes:** H1, H4, D1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** DailyForex test: outside bar = high > prior high and low < prior low; enter in the direction of the outside bar's close on the next bar open; filter: only in the direction of a longer-term trend.
- **Exit:** Fixed R / N bars.
- **Stop:** Opposite side of the outside bar.  |  **Target:** 1-2R.
- **Parameters (defaults):** `{"filter": "trend direction"}`
- **Claimed performance (as reported):** DailyForex backtest (EUR/USD, GBP/USD, USD/JPY; D1/H4/H1): only USD/JPY had positive expectancy > 50% of trades; EUR/USD 'slightly profitable'; a trend filter 'improved EUR/USD results significantly' (figures not shown).
- **Notes:** Weak positive, undated (2013).
- **Sources:** <https://www.dailyforex.com/forex-articles/2013/12/outside-bar-trading-strategy-in-momentum-trading/27094>

### P04. Double top / double bottom
- **Timeframes:** H4, D1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Two peaks within ~0.5 x ATR of each other separated by a trough; enter short on a close below the trough (neckline); mirror for bottoms. Measured move target = pattern height.
- **Exit:** Target or stop.
- **Stop:** Above the second peak.  |  **Target:** Pattern height projected from the neckline.
- **Parameters (defaults):** `{"peak_tolerance_atr": 0.5, "min_bars_between": 5}`
- **Claimed performance (as reported):** Bulkowski (mostly US stocks; forex sample 1991-2005 not broken out): double top 'success rate >= break-even 73%, average decline 14%' per one summary; another summary cites a 65% failure rate for double tops; no EUR/USD numbers.
- **Notes:** Secondary Bulkowski figures contradict each other; stock-derived anyway.
- **Sources:** <https://thepatternsite.com/ppEEDT.html>; <https://www.thepatternsite.com/id84.html>; <https://mytradingskills.com/?p=2321>

### P05. Head and shoulders
- **Timeframes:** H4, D1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Three peaks with the middle highest; short on a close below the neckline; target = head-to-neckline distance.
- **Exit:** Target or stop.
- **Stop:** Above the right shoulder.  |  **Target:** Measured move.
- **Parameters (defaults):** `{"shoulder_symmetry_tolerance": 0.3}`
- **Claimed performance (as reported):** Bulkowski secondary citations: H&S top break-even failure rate 19% (bull market) / 5% (bear); '93% success' (38,500 patterns) and '81% see a >= 5% move' quoted by course sites; inverse H&S 83%. Not EUR/USD. FOREX.com notes 'busted' EUR/USD H&S patterns.
- **Notes:** No FX-specific statistics; pattern detection is itself discretionary.
- **Sources:** <https://research.titanfx.com/technical-analysis/candlestick-chart/head-and-shoulders-top-bottom>; <https://www.liberatedstocktrader.com/chart-patterns-reliable-profitable/>; <https://www.forex.com/en-us/market-analysis/latest-research/eurusd-busted-bearish-headandshoulders-becomes-bullish-headandshoulders/>

### P06. Flags / pennants (continuation)
- **Timeframes:** M15, H1, H4  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Impulse (pole) of >= 1.5 x ATR followed by a 5-20 bar counter-trend channel retracing < 50% of the pole; enter on a close out of the channel in the pole's direction.
- **Exit:** Pole length projected from the breakout.
- **Stop:** Opposite side of the flag.  |  **Target:** 1x pole.
- **Parameters (defaults):** `{"pole_min_atr": 1.5, "max_retrace": 0.5, "flag_bars": [5, 20]}`
- **Claimed performance (as reported):** none found
- **Notes:** No EUR/USD statistics found.
- **Sources:** <https://tradingcenter.org/index.php/learn/chart-patterns>; <https://www.tradingpedia.com/day-trading-academy/positioning-within-trading-channels>

### P07. Harmonic patterns (Gartley / Bat / Butterfly / Crab)
- **Timeframes:** H1, H4  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** XABCD legs with Fibonacci ratios: Gartley B = 0.618 XA, D = 0.786 XA; Bat B = 0.382-0.5 XA, D = 0.886 XA; Butterfly B = 0.786 XA, D = 1.27-1.618 XA; Crab D = 1.618 XA. Enter at D (potential reversal zone) against the CD leg.
- **Exit:** Targets at 0.382 and 0.618 retracement of AD.
- **Stop:** Beyond X (Gartley/Bat) or beyond the 1.618 extension (Butterfly).  |  **Target:** T1 = 0.382 AD, T2 = 0.618 AD.
- **Parameters (defaults):** `{"tolerance": 0.03}`
- **Claimed performance (as reported):** Take Profit app (vendor): EURUSD H4 Gartley 32 valid patterns, 23 wins (71.9%), avg R:R 1:2.6, PF 3.31. TradingView user: Gartley+Bat+Cypher 68.6% win rate on EURUSD since 2016 (no method). ES futures 2020-2024 independent-style test: Butterfly 58.6% (29 trades), Crab 42.9% / PF 0.43. Carney (2007) cited: 60-65% reach first target. HKUST student project tested four patterns across stocks/forex/crypto (EUR/USD figures not retrieved).
- **Notes:** Win rates of 60-70% to the first (0.382) target are roughly what a random entry with a close target and far stop produces; no evidence of edge.
- **Sources:** <https://takeprofitapp.com/en/learn/gartley-pattern-trading>; <https://in.tradingview.com/chart/EURUSD/MZSdHs7Y-I-ve-done-backtesting-Harmonic-Pattern-on-EURUSD-60/>; <https://cse.hkust.edu.hk/~rossiter/independent_studies_projects/trading_harmonic_patterns/trading_harmonic_patterns.pdf>; <https://anupshindedotcom.pages.dev/harmonic-patterns-backtested/>

### P08. Fibonacci retracement entries (38.2 / 50 / 61.8)
- **Timeframes:** H1, H4, D1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** After an impulse swing, buy the pullback at 38.2%, 50% or 61.8% retracement with a rejection candle; stop below 78.6%; target the swing high (100%) and 127.2%/161.8% extensions.
- **Exit:** Extensions.
- **Stop:** Below 78.6% (or below swing origin).  |  **Target:** 100%, 127.2%, 161.8%.
- **Parameters (defaults):** `{"levels": [0.382, 0.5, 0.618], "stop_level": 0.786, "targets": [1.0, 1.272, 1.618]}`
- **Claimed performance (as reported):** ForexOp (1-minute data, G10 vs USD incl. EUR/USD, Oct 2003-May 2016): retracement depths landing near Fibonacci levels are explained by chance (with four levels between 23.6% and 61.8% a retrace lands near one by construction). Reddit multi-asset 61.8% backtest (50 FX pairs incl. EURUSD, 1m-1d): 'not profitable' (anecdotal).
- **Notes:** The only quantitative test found says Fibonacci levels are not special; 50% retracement of the prior day's range is still a sensible generic target.
- **Sources:** <https://forexop.com/strategy/fibonacci-fact-or-fiction/>; <https://www.forex.com/en-us/news-and-analysis/fibonacci-in-financial-markets/>; <https://reddit.sentinel-team.org/posts/1pn9xhn/snapshots/2025-12-16T04%3A42%3A12.068155Z>

### P09. Supply/demand zones (rally-base-drop, drop-base-rally)
- **Timeframes:** H1, H4  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Identify a base (<= 3 small candles) followed by an impulsive departure (>= 2 x ATR); mark the base's range as the zone; enter on the first return to the zone with a limit at its proximal edge.
- **Exit:** 2-3R or opposite zone.
- **Stop:** Beyond the distal edge of the zone + buffer.  |  **Target:** Opposite zone / 3R.
- **Parameters (defaults):** `{"max_base_candles": 3, "departure_atr": 2, "rr": 3}`
- **Claimed performance (as reported):** none found
- **Notes:** Search found no backtest statistics at all for supply/demand zones on EUR/USD.
- **Sources:** <https://www.luxalgo.com/blog/inside-bar-breakouts-tight-risk-big-reward/>; <https://backtrex.com/en/blog/what-is-smart-money-concepts-trading>

### P10. Order blocks (last opposite candle before displacement)
- **Timeframes:** M15, H1, H4  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Bullish OB = last bearish candle before an impulsive up-move that breaks structure; enter long on the first retrace into the OB's range (open-to-low or full candle); bearish mirrored.
- **Exit:** Next liquidity level or 2R.
- **Stop:** Below the OB low.  |  **Target:** 1:2 minimum.
- **Parameters (defaults):** `{"displacement_atr": 1.5, "zone": "open-to-low of OB candle"}`
- **Claimed performance (as reported):** TradingView placebo study (OB vs matched random levels): no tested configuration showed a reliable difference between real order blocks and placebo levels. DEV Community Pine v5 OB+FVG strategy (1H): EURUSD PF 1.18, max DD -6.1%, 184 trades after adding filters (earlier version 35% win rate). Backtrex GBP/USD order-block backtest exists (result not captured; the vendor's ICT backtests all lose). TradingView 'EURUSD 4H 69% win rate, 12.75R' on 13 trades with acknowledged look-ahead bias.
- **Notes:** Placebo comparison is the right methodology and found nothing; PF ~1.2 after filter-fitting is consistent with no edge.
- **Sources:** <https://de.tradingview.com/script/yFmy3VBi-Order-Block-OB-Statistics-Real-Win-Rate-vs-Random-Levels/>; <https://dev.to/isabelle_dubuis_d858453d7/ict-order-block-fvg-strategy-in-pine-script-v5-backtest-results-full-code-l5c>; <https://backtrex.com/en/backtests/order-block-gbp-usd>; <https://my.tradingview.com/chart/EURUSD/NMjYOOqi-EURUSD-4H-backtest-69-Win-rate-12-75-R>

### P11. Fair value gap (imbalance) retrace entry
- **Timeframes:** M5, M15, H1  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** Bullish FVG: candle1.high < candle3.low (three-candle gap). Enter long with a limit at the top (or 50% 'consequent encroachment') of the gap on the first retrace; bearish mirrored. Usually combined with a killzone (S08) or a sweep (S09).
- **Exit:** Next swing high/low or 2R.
- **Stop:** Below the gap (candle1 high for bullish) + buffer.  |  **Target:** 1:2.
- **Parameters (defaults):** `{"entry_level": "gap top or 50%", "rr": 2}`
- **Claimed performance (as reported):** See S08 (GBP/USD M15 killzone FVG: 33.89% win, PF 0.80, 1,009 trades, 2016-2026, vendor). Forextester FVG article gives no numbers.
- **Notes:** Mechanically well-defined, which is why it can be shown to lose.
- **Sources:** <https://backtrex.com/en/blog/fair-value-gap-trading-strategy>; <https://backtrex.com/en/backtests/ict-kill-zone-fvg-gbp-usd>; <https://forextester.com/blog/fair-value-gap/>

### P12. Wyckoff spring / upthrust (false break of a trading range)
- **Timeframes:** M30, H4  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** After >= 20 bars of range, price breaks the range low on expanding volume (tick volume) and closes back inside within 1-3 bars (spring); buy the close back inside; upthrust mirrored.
- **Exit:** Range top (spring) / range bottom (upthrust); or 2R.
- **Stop:** Below the spring low.  |  **Target:** Opposite range boundary.
- **Parameters (defaults):** `{"min_range_bars": 20, "reclaim_bars": 3}`
- **Claimed performance (as reported):** Take Profit app (vendor, VSA page): EURUSD Spring 32 setups, 22 wins (68.8%), R:R 1:2.3, PF 5.06; no data/period/method. MQL5 article automates spring/upthrust detection on EURUSD, no results shown. TradingView 4H '69% / 13 trades' (too small).
- **Notes:** Same hypothesis as M10/S19 (failed breakout reversal) with a range-length precondition.
- **Sources:** <https://takeprofitapp.com/en/learn/volume-spread-analysis-vsa>; <https://www.mql5.com/en/articles/22628>; <https://doc.stocksharp.com/en/api-examples/0107_Upthrust_Reversal>


## 6. Calendar / seasonality / events

### C01. Day-of-week: short Monday, long Friday
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Seasonax (2000-Feb 2018): EUR/USD average annualised return -1.90% on Mondays, +1.73% on Fridays. Rule: short at Monday open (Sunday 22:00 UTC) to Monday close; long Friday open to Friday close. Popovic & Durovic (hourly EUR/USD, Jan 2004-Jan 2014, ANOVA): day x hour interaction anomalies exist; strongest on Fridays with trades at 00:00 and 03:00.
- **Exit:** Same-day close.
- **Stop:** None (seasonal study).  |  **Target:** Time exit.
- **Parameters (defaults):** `{"short_day": "Monday", "long_day": "Friday"}`
- **Claimed performance (as reported):** Seasonax: -1.90% annualised (Mon), +1.73% annualised (Fri), 2000-2018, no significance tests, in-sample. Bush & Stephens (JBEF 2016): Monday effect in EUR/USD varies with EUR strength/weakness across six sub-periods; a sister paper found no Monday effect 1999-2004 or 2005-2009 and a significant one 2010-2012 for three pairs. TradingView 'no secret profit day in EURUSD' post found nothing. ForexFactory 2017 YTD: Monday the most likely up day, Friday second.
- **Notes:** Annualised 1.7-1.9% per weekday is a few pips per day: real but not tradeable after spread unless combined with another signal; the effect is regime-dependent.
- **Sources:** <https://www.seasonax.com/market-efficiency-the-euro-is-looking-forward-to-the-weekend>; <https://ideas.repec.org/a/eee/beexfi/v10y2016icp72-74.html>; <https://ideas.repec.org/a/taf/applec/v46y2014i32p3968-3979.html>; <https://www.tradingview.com/chart/EURUSD/Zda9xaUn-Is-there-a-secret-profit-day-in-EURUSD/>

### C02. Hour-of-day extremes and the time the daily high/low is set
- **Timeframes:** H1  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** DailyFX (EUR/USD 2005-2009): the 18:00 ET hour (Asian open) set the day's high 8% / low 6% of days (random = 4.17%/hour); the 03:00-05:00 ET window (European open) set the high 12% / low 11% (random 8.33%); the 09:00-12:00 ET window (US open + data) set the high 20% / low 21% (random 12.5%). Rule: place stops beyond, and expect extremes during, these windows; avoid initiating mean-reversion trades at 09:00-12:00 ET.
- **Exit:** n/a (filter).
- **Stop:** n/a  |  **Target:** n/a
- **Parameters (defaults):** `{"extreme_windows_et": ["18:00", "03:00-05:00", "09:00-12:00"]}`
- **Claimed performance (as reported):** As stated; the full hour-by-hour table is an image not retrieved. QuantHedge (14 years): the three hours from NY open to London close are the most volatile, then London open to Tokyo close (figures not retrieved). TradingView seasonality study: ATR peaks ~28 pips/hour near 07:00 GMT and ~34 pips/hour 13:00-15:00 GMT.
- **Notes:** Combined with S14/S18 this gives a full intraday map: volatility 07:00-10:00 and 13:00-16:00 GMT, extremes most often in the US morning.
- **Sources:** <https://www.dailyfx.com/forex/technical/article/special_report/2012/07/21/Improving_Profitability_with_Intraday_Seasonality.html>; <https://quanthedge.substack.com/p/eurusd-profile-a-statistical-view>; <https://my.tradingview.com/chart/EURUSD/O5OLT3x1-Seasonality-Intra-day-Trading-System>

### C03. Monthly seasonality (December long, May short)
- **Timeframes:** MN  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** Long EUR/USD from the last trading day of November to the last trading day of December; short for May. Vendors (StoneX/FOREX.com) publish monthly notes using 50+ years of DEM/EUR data.
- **Exit:** Month end.
- **Stop:** None.  |  **Target:** Time exit.
- **Parameters (defaults):** `{"long_months": ["December"], "short_months": ["May"]}`
- **Claimed performance (as reported):** TickerLeague (1971-2026): December best month, average +1.24%, positive in 65% of years. StoneX: May average -0.62%, June +0.52% over 50+ years. StoneX Sep-2026 note implies August is seasonally weak (EUR/USD 'bucked its seasonal weakness' with +0.7%). FactorResearch 'January effect': 76% of years 1972-2025 set the annual high or low in January; only 37.5% (3 of 8) in the last 8 years.
- **Notes:** December effect is plausibly year-end USD funding/rebalancing; the January high/low effect is a 'range-setting' not a direction.
- **Sources:** <https://tickerleague.com/forex/eurusd/seasonality>; <https://www.stonex.com/en-gb/news-and-analysis/forex-seasonality-september-2026-can-eur-usd-extend-its-gains-to-three-straight-months/>; <https://www.forex.com/en-us/news-and-analysis/forex-seasonality-june-2026-will-eur-usd-rally-back-toward-1-18/>; <https://www.peterlbrandt.com/wp-content/uploads/2026/03/January-Effect_for-2026.pdf>; <https://www.nasdaq.com/articles/eurusd-january-effect-fact-or-fiction-2016-01-05>

### C04. Turn-of-month / first trading day of month  *(rules reconstructed)*
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** CXO window: from the close 5 trading days before the last trading day of the month to the close 4 trading days after. Hypothesis for EUR/USD: USD weakens into/after month end (equity rebalancing, corporate flows). Rule: long EUR/USD from T-1 close to T+1 close (month end = T).
- **Exit:** T+1 (or T+4) close.
- **Stop:** None.  |  **Target:** Time exit.
- **Parameters (defaults):** `{"window": "T-1 to T+1"}`
- **Claimed performance (as reported):** No EUR/USD-specific study found. Related: Indian-rupee study found turn-of-month returns significantly lower (USD/INR, JPY/INR). CXO results paywalled.
- **Notes:** Compute from daily data; combine with S15.
- **Sources:** <https://www.cxoadvisory.com/?p=43042>; <https://www.emeraldinsight.com/insight/content/doi/10.1108/IJMF-05-2014-0068/full/html>; <https://www.fxempire.com/education/article/fx-seasonality-what-still-works-and-what-doesnt-in-2026-1545003>

### C05. Friday afternoon position-squaring reversal  *(rules reconstructed)*
- **Timeframes:** H1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** If EUR/USD has moved >= 1% over Mon-Thu in one direction, fade that direction from Friday 13:00 London to the Friday close (profit-taking into the weekend).
- **Exit:** Friday 21:00 UTC.
- **Stop:** 0.5 x ADR.  |  **Target:** Time exit.
- **Parameters (defaults):** `{"min_weekly_move_pct": 1.0, "entry_london": "13:00"}`
- **Claimed performance (as reported):** Anecdotal only (FXStreet/FXEmpire/ForexLive commentary on Friday profit-taking after 4-5 day streaks). Seasonax Friday strength (C01) argues for a long bias on Fridays regardless. FXStreet 2015 tip: 'why some strategies are so effective except on Fridays' (no data).
- **Notes:** Overlaps M13 (streak fade); test Friday as a conditioning variable in M13.
- **Sources:** <https://www.fxstreet.com/news/eur-usd-recovers-with-profit-taking-in-the-dollar-bull-run-at-the-end-of-the-week-202411151156>; <https://www.forexlive.com/news/!/profit-taking-not-fundamentals-driving-euro-toward-the-close-20150123>; <https://www.fxstreet.com/amp/education/your-daily-educational-tip-201504090000>

### C06. Holiday-week behaviour (Thanksgiving, Christmas/New Year)
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Hypotheses from commentary: (a) narrow ranges and continuation of the pre-holiday trend (Lien); (b) occasional outsized moves on thin liquidity ('Thanksgiving breakouts'). Rule for a test: measure ADR and trend continuation for the US Thanksgiving week and 24 Dec-2 Jan vs matched weeks.
- **Exit:** n/a
- **Stop:** n/a  |  **Target:** n/a
- **Parameters (defaults):** `{"holiday_windows": ["US Thanksgiving week", "Dec 24-Jan 2"]}`
- **Claimed performance (as reported):** Anecdotes: 1M implied vol fell 9.6% -> 7.4% into a Thanksgiving (GlobalCapital); EUR/USD hit a 1-month high on Thanksgiving 2017 and an 11-month low Thanksgiving week 2016 (Lien); Dec 2024 final day ~30-pip range; Dec 2025 'calm 1.1750-1.18'.
- **Notes:** No statistics; useful mainly as a 'do not trade breakouts' filter.
- **Sources:** <https://uk.investing.com/analysis/fx-and-the-possibility-of-thanksgiving-breakouts-200434665>; <https://www.globalcapital.com/article/28mssnrew086objo4qxho/derivatives/euro-dollar-vols-drift-down-for-thanksgiving>; <https://www.fxstreet.com/news/eur-usd-stays-in-tight-range-amid-thin-trading-volume-in-holiday-shortened-week-202412270743>

### C07. Pre-FOMC dollar drift (two days before the decision)
- **Timeframes:** D1, H1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Karnaukh ('The Dollar Ahead of FOMC Target Rate Changes'): over the two days before a scheduled FOMC decision, the USD rises when fed funds futures imply a hike and falls when they imply a cut. Rule: if futures-implied change < 0 (cut expected) go long EUR/USD at the close two days before; if > 0 go short; exit at the 14:00 ET announcement.
- **Exit:** At the announcement.
- **Stop:** None in paper.  |  **Target:** Time exit.
- **Parameters (defaults):** `{"signal": "sign of futures-implied rate change", "window": "T-2 close to T 14:00 ET"}`
- **Claimed performance (as reported):** Macrosynergy summary of Karnaukh: USD -32 bp before expected cuts, +20 bp before expected hikes over the two-day window; stronger when FX implied vol is high; no rise in realised vol/illiquidity pre-FOMC. Mueller, Tahbaz-Salehi & Vedolin: USD excess returns significantly larger on FOMC days (pre- and post-announcement components), larger for high-rate-differential currencies. Borisenko & Pozdeev: the pre-decision drift is common to most currencies before their own central bank's cuts and 'the dollar drift ... averages to zero across specifications' (robustness contested). Lucca-Moench equity drift is not found for other macro releases.
- **Notes:** Eight events per year; the EUR/USD-only estimate is not isolated in the sources.
- **Sources:** <https://acfr.aut.ac.nz/__data/assets/pdf_file/0019/190315/DollarAheadFOMC_NinaKarnaukh.pdf>; <https://macrosynergy.com/?p=41075>; <https://conference.nber.org/conf_papers/f64395/f64395.pdf>; <https://acfr.aut.ac.nz/__data/assets/pdf_file/0011/105500/90345-Borisenko-and-Pozdeev,-Monetary-Policy-and-Currency-Returns-the-Foresight-Saga.pdf>

### C08. FOMC day statement spike / press-conference reversal  *(rules reconstructed)*
- **Timeframes:** M5, H1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Hypothesis: the 14:00 ET statement sets an initial direction that the 14:30 ET press conference often reverses. Rule to test: fade the 14:00-14:30 move at 14:35 if it exceeds 0.4% and the move is retracing; else follow it.
- **Exit:** NY close.
- **Stop:** Beyond the 14:00-14:30 extreme.  |  **Target:** Pre-statement level.
- **Parameters (defaults):** `{"spike_threshold_pct": 0.4}`
- **Claimed performance (as reported):** Anecdotes only: Sep 2025 EUR/USD spiked on the statement then closed -0.5% after Powell; Sep 2023 fell ~80 pips post-FOMC; Jan 2019 +50 pips in seconds; Jun 2026 -60 pips in minutes without reversal. No base rate found.
- **Notes:** ~16 events in two years; needs 10+ years of 1-minute data to say anything.
- **Sources:** <https://www.marketpulse.com/markets/eurusd-technical-euro-bullish-trend-intact-despite-12-sell-off-after-fomc/>; <https://www.fxstreet.com/analysis/eur-usd-forecast-sharp-reversal-after-fed-leaves-the-euro-vulnerable-202309202026>; <https://www.fxstreet.com/news/euro-folds-as-the-fed-trades-cuts-for-hikes-202606171818>

### C09. ECB decision / press conference reaction
- **Timeframes:** M5, M15  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Decision 14:15 CET (13:15 London), press conference 14:45 CET. Hypothesis: the statement move is small and the press conference carries the larger move; trade the press-conference break of the 14:15-14:45 range.
- **Exit:** 16:00 London fix or 1:2.
- **Stop:** Opposite side of the 14:15-14:45 range.  |  **Target:** 1x range or 1:2.
- **Parameters (defaults):** `{"range_window_cet": "14:15-14:45"}`
- **Claimed performance (as reported):** FundedFast tool: average 19.3 pips in the first 60 minutes over the last 9 ECB decisions (methodology unclear). Examples: +72 pips in the first half hour of a Draghi speech (2018); ~100-pip post-ECB rally that fizzled (2020); ~50-pip loss during a 2026 Lagarde conference; 5-day average vol 40 pips before decisions (2026 note).
- **Notes:** Average 60-minute move of ~19 pips is small relative to NFP (~47 pips).
- **Sources:** <https://fundedfast.com/tools/event-reactions/ecb>; <https://www.babypips.com/news/headline-why-eurusd-fell-after-the-ecb-opened-the-door-to-a-september-hike2026-07-24>; <https://www.fxstreet.com/news/eur-usd-declines-following-ecbs-decision-lagardes-press-conference-202401251502>

### C10. Fed-vs-ECB policy divergence trade (2-year swap spread momentum)
- **Timeframes:** D1, W1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Track the EUR-USD 2-year swap (or OIS) differential. Go long EUR/USD when the differential has widened in EUR's favour by >= 20 bp over 4 weeks; short when it narrows by >= 20 bp; or regress and trade residuals (see F01).
- **Exit:** Differential momentum flips.
- **Stop:** 2 x weekly ATR.  |  **Target:** None.
- **Parameters (defaults):** `{"spread_change_bp": 20, "lookback_weeks": 4}`
- **Claimed performance (as reported):** ING (Mar 2025): 2y swap gap -145 bp -> short-term fair value 1.067. ING (May 2026): gap widened 20 bp from -80 to -100 bp in a week, removing EUR support. ING 2023: regression coefficient on the 2y swap spread 'very close to zero' in that period. BNP (daily data since 2019): correlation of EUR/USD level with 1y differential 66%, 2y 62%, 10y only 5%. Centralbank.watch claims the Fed-minus-ECB policy rate tracks the EUR/USD level better than any single variable over 1-3 years (unverified).
- **Notes:** The relationship is strong in levels in some years and absent in others (2023, 2025-26 when growth/tariffs dominated); use rolling-window estimation.
- **Sources:** <https://think.ing.com/articles/fx-daily-dont-rush-to-pick-the-eur-usd-top>; <https://think.ing.com/articles/eur-usd-real-interest-rates-still-important/>; <https://economic-research.bnpparibas.com/html/en-US/multiple-factors-underpinning-renewed-strength-euro-against-dollar-4/17/2023,48485>; <https://centralbank.watch/compare/currency-pair-deep-dives/eur-usd/>


## 7. Fundamental / intermarket

### F01. 2-year yield (swap) differential regression fair value
- **Timeframes:** D1, W1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Fit EUR/USD_t = a + b x (DE2y - US2y)_t [+ c x terms-of-trade] on a rolling 1-year window of daily data; residual z = (spot - fitted)/sigma_resid. Go long when z < -1.5, short when z > +1.5; exit at z = 0.
- **Exit:** Residual crosses zero.
- **Stop:** z beyond +/-2.5.  |  **Target:** z = 0.
- **Parameters (defaults):** `{"window_days": 250, "entry_z": 1.5, "stop_z": 2.5, "regressor": "DE-US 2y swap, optionally relative terms of trade"}`
- **Claimed performance (as reported):** MNI/Citi short-term fair value model (2y swap differential + relative terms of trade, 1-year window): R^2 87%. An academic-style daily-change regression on 2y and 10y US/German yields explained only ~5% of daily EUR/USD fluctuations (2y US yield the largest term). BNP: level correlation since 2019: 1y 66%, 2y 62%, 10y 5%. Bond Vigilantes: capital-key-weighted euro-area yield better than Bund; relationship 'breaking down more recently' but useful over long horizons.
- **Notes:** Levels R^2 is high; daily-change R^2 is tiny. A residual mean-reversion trade is the standard sell-side use; coefficients drift so no fixed beta.
- **Sources:** <https://marketnews.com/eur-usd-cheap-to-short-term-fair-value-but-risks-still-loom>; <https://economic-research.bnpparibas.com/html/en-US/multiple-factors-underpinning-renewed-strength-euro-against-dollar-4/17/2023,48485>; <https://bondvigilantes.com/?p=16105>; <https://think.ing.com/downloads/pdf/article/heres-why-eur-usd-is-not-trading-higher-on-the-fed-repricing>

### F02. Real rate differential (2y real swap / 10y TIPS-Bund)
- **Timeframes:** W1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Real 2y differential = (US 2y swap - US 2y inflation swap) - (EUR 2y swap - EUR 2y inflation swap). Trade the residual of EUR/USD vs this spread as in F01.
- **Exit:** As F01.
- **Stop:** As F01.  |  **Target:** As F01.
- **Parameters (defaults):** `{"tenor": "2y", "window": "rolling 2y"}`
- **Claimed performance (as reported):** ING (Mar 2026): scatter of EUR/USD vs 2y real swap differential described as a 'stable relationship'; argues real, not nominal, spreads matter. BNP (Jan 2021): since 2011 the correlation between the real 10y TIPS-Bund differential and EUR/USD was positive, i.e. the wrong sign for the capital-flow model. BNP 2024: Bund yields moving less than Treasuries than history predicts.
- **Notes:** Sign instability at the 10y tenor; the 2y real spread is the one practitioners use.
- **Sources:** <https://think.ing.com/articles/eur-usd-real-interest-rates-still-important/>; <https://economic-research.bnpparibas.com/pdf/en-US/surprising-weakening-dollar-could-change-1/22/2021,40727>; <https://economic-research.bnpparibas.com/html/en-US/US-versus-Eurozone-inflation-divergence-causes-monetary-desynchronization-lowers-bond-market-correlation-4/22/2024,49528>

### F03. DXY relationship (EUR is 57.6% of DXY)
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Not a signal on its own (near-identity). Use: trade EUR/USD when DXY breaks a technical level EUR/USD has not yet confirmed (lead/lag of a few minutes at most); or use DXY ex-EUR (JPY, GBP, CAD, SEK, CHF basket) as a USD-strength filter.
- **Exit:** n/a
- **Stop:** n/a  |  **Target:** n/a
- **Parameters (defaults):** `{"eur_weight_in_dxy": 0.576}`
- **Claimed performance (as reported):** Convextrade: daily-return correlation EUR/USD vs broad trade-weighted USD index -0.820 (2024), -0.905 (2025). FXStreet '+90% correlation' is a level comparison.
- **Notes:** Mechanical; little independent information.
- **Sources:** <https://convextrade.com/compare/eurusd-vs-dxy/correlation>; <https://www.fxstreet.com/analysis/eur-usd-vs-dxy-averages-1-to-10-years-202404221036>

### F04. Risk sentiment (S&P 500) correlation regime
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Compute 60-day rolling correlation of EUR/USD and S&P 500 daily returns. Risk-on regime (corr > +0.3): trade EUR/USD in the direction of equity momentum; USD-safe-haven regime. In 2024-25 the sign flipped (USD and S&P rose together), so the rule must be regime-conditional.
- **Exit:** Regime change.
- **Stop:** n/a  |  **Target:** n/a
- **Parameters (defaults):** `{"corr_window": 60, "threshold": 0.3}`
- **Claimed performance (as reported):** FXStreet: USD-S&P correlation predominantly negative 2022-2024; 20- and 60-day rolling correlations briefly positive in 2023; from early 2024 USD and S&P 500 'rising nearly in sync'. Investing.com (Jun 2025): 120-day EUR-S&P correlation chart flagged as 'most important macro chart' (values not retrieved).
- **Notes:** Correlation sign is unstable; only useful with regime detection.
- **Sources:** <https://www.fxstreet.com/analysis/sp-500-vs-eur-usd-unpacking-the-2024-2025-shift-202504281941>; <https://ng.investing.com/analysis/eurosp-500-correlation-raises-red-flags-for-us-dollar-stability-209521>; <https://macrohive.com/fx-short-valuation/what-is-our-eur-usd-correlation-cheat-sheet-telling-us>

### F05. Gold and oil as EUR/USD proxies
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Gold: positive but weak correlation; oil: unstable. Use at most as a confirmation filter (e.g., gold up > 1% on the day supports USD weakness).
- **Exit:** n/a
- **Stop:** n/a  |  **Target:** n/a
- **Claimed performance (as reported):** Convextrade EUR/USD vs spot gold yearly Pearson (daily returns): +0.418 (2023), +0.288 (2024), +0.362 (2025); 1-year +0.39. Gold vs DXY latest -0.50. Oil: 'long-run correlation fairly high but net below zero over this period' (broker page); FXStreet 2026: oil shifted to negative correlation with USD.
- **Notes:** Too weak to trade on.
- **Sources:** <https://convextrade.com/compare/dexuseu-vs-gold/correlation>; <https://www.fxstreet.com/analysis/five-market-relationships-traders-rely-on-which-ones-still-work-202609091047>; <https://www.earnforex.com/forex-course/intermarket-correlations/>

### F06. Bund-Treasury 10-year spread
- **Timeframes:** W1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Same residual approach as F01 using the 10y DE-US spread.
- **Exit:** As F01.
- **Stop:** As F01.  |  **Target:** As F01.
- **Parameters (defaults):** `{"tenor": "10y"}`
- **Claimed performance (as reported):** BNP: correlation of EUR/USD level with the 10y differential only ~5% (daily data since 2019) vs 62-66% for 1-2y. Bond Vigilantes: 2y gap works better than 10y; ECB QE depressed Bund yields.
- **Notes:** Dominated by the front end; keep for completeness.
- **Sources:** <https://economic-research.bnpparibas.com/html/en-US/multiple-factors-underpinning-renewed-strength-euro-against-dollar-4/17/2023,48485>; <https://bondvigilantes.com/?p=16105>

### F07. PPP / BEER long-run valuation anchor
- **Timeframes:** MN  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Fair value from OECD PPP (or ING's BEER: terms of trade, productivity, current account, government spending). Rule: multi-month bias long when spot is > 15% below PPP and the 12-month trend turns up; never as a timing signal.
- **Exit:** Spot within 5% of fair value.
- **Stop:** None.  |  **Target:** Fair value.
- **Parameters (defaults):** `{"undervaluation_threshold_pct": 15}`
- **Claimed performance (as reported):** OECD PPP: fair value ~$1.38 (2019, euro ~22% undervalued, cheap for five years); 1.4060 with spot 15% undervalued (MNI, 2020). ING BEER: ~9-10% overvalued in real terms in 2022 (fair value near parity); ~5% undervalued late 2024. SocGen 2017 fair value note exists. No 2024-25 OECD PPP figure retrieved.
- **Notes:** Meese-Rogoff: macro models do not beat a random walk at < 1-year horizons; PPP works, if at all, over 3-5 years.
- **Sources:** <https://www.fxstreet.com/analysis/great-graphic-euros-oecd-ppp-201906131134>; <https://mnimarkets.com/eurusd-spot-rate-vs-purchasing-power-parity>; <https://think.ing.com/articles/eur-usd-not-as-cheap-as-it-looks>; <https://think.ing.com/articles/g10-fx-valuation-round-up>

### F08. Taylor-rule fundamentals model (Molodtsova-Papell)
- **Timeframes:** MN  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Forecast the monthly change in EUR/USD from the difference in Taylor-rule implied rates: i* - i = a + 1.5 x (pi_EA - pi_US) + 0.5 x (gap_EA - gap_US) [+ smoothing, real exchange rate term]; go long EUR when the model's predicted change > 0 (sign-based, monthly).
- **Exit:** Monthly re-estimate.
- **Stop:** None.  |  **Target:** Time exit.
- **Parameters (defaults):** `{"inflation_coef": 1.5, "gap_coef": 0.5, "horizon": "1 month"}`
- **Claimed performance (as reported):** Molodtsova & Papell (JIE 2009): short-horizon out-of-sample predictability for 11 of 12 USD pairs post-Bretton Woods, beating interest-rate, PPP and monetary models. Molodtsova, Nikolsko-Rzhevskyy & Papell ('Taylor rules and the euro', real-time 1999-2007): predictability only for specifications without the real exchange rate; persists through the crisis (2012). Ince, Molodtsova & Papell (2016, 1973-2014): strong evidence for Taylor-rule fundamentals vs random walk; Ince & Molodtsova real-time 15-country study: does not beat a random walk in some specifications.
- **Notes:** Statistical predictability (Clark-West tests) is not the same as tradeable Sharpe; monthly frequency.
- **Sources:** <https://econpapers.repec.org/RePEc:eee:inecon:v:77:y:2009:i:2:p:167-180>; <https://www.appstate.edu/~molodtsovat/Taylor_Euro.pdf>; <https://projects.nber.org/confer/2012/ISOM12/Molodtsova_Papell.pdf>; <https://academicnewsletter.sufe.edu.cn/info/299294>

### F09. Carry (EUR/USD interest differential) with time-of-day split
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Hold the higher-yielding leg (short EUR/USD when US rates > EUR rates, as 2022-2025). Krohn-Mueller-Whelan: carry returns are earned intraday (US hours) and are ~zero overnight; momentum returns are earned overnight.
- **Exit:** Differential sign flip.
- **Stop:** Vol-scaled.  |  **Target:** None.
- **Parameters (defaults):** `{"signal": "sign(US 3m - EUR 3m)"}`
- **Claimed performance (as reported):** Krohn et al. ('UIP in high frequency'): during the overnight period carry risk premia are essentially zero; the carry portfolio appreciates significantly during the day. No EUR/USD-only carry Sharpe retrieved; EUR/USD is a low-carry pair (differential ~2% in 2025).
- **Notes:** Implication for intraday systems: USD-positive drift during US hours when USD is the high-yielder.
- **Sources:** <https://jbs.cam.ac.uk/wp-content/uploads/2024/11/uncovered-interest-parity-in-high-frequency.pdf>; <https://acfr.aut.ac.nz/__data/assets/pdf_file/0007/190753/Krohn_Mueller_Whelan_Jun2018_FXPremiaAroundTheClock.pdf>; <https://quantpedia.com/fx-carry-value-momentum-strategies-over-their-200-year-history/>

### F10. COT positioning extremes (CME Euro FX 099741) as contrarian signal  *(rules reconstructed)*
- **Timeframes:** W1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** Compute the 3-year percentile (or z-score) of large-speculator net EUR futures position (COT, Tuesday data released Friday). Contrarian: short EUR/USD when net long is in the top 5% and the weekly change turns negative; long when net short is in the bottom 5% and the change turns positive.
- **Exit:** Percentile returns to 50%, or 8 weeks.
- **Stop:** 3% adverse move.  |  **Target:** Percentile 50%.
- **Parameters (defaults):** `{"lookback_years": 3, "extreme_pct": 5, "require_turn": true}`
- **Claimed performance (as reported):** No hit-rate study found. FXStreet (Oct 2026): euro positioning at a '343-report extreme' pointing to a medium-term floor. StoneX/FOREX.com notes: net long most bullish since Jul 2023 (early 2026); Jan 2025 'tentative signs of reversal'; 2017 Schaeffer's event study suggested weaker euro a year after large-spec extremes (no table). Commentary consistently treats extremes as 'late' signals.
- **Notes:** Weekly data, ~5-10 signals a decade; needs the full CFTC history to evaluate.
- **Sources:** <https://www.fxstreet.com/analysis/euro-positioning-reaches-343-report-extreme-as-cot-data-points-toward-a-potential-medium-term-floor-202610041903>; <https://forex.com/en/news-and-analysis/tentative-signs-of-reversals-for-eurusd-commodity-fx-cot-report-2025-01-14>; <https://www.schaeffersresearch.com/content/bgs/2017/09/25/signal-suggests-short-term-gains-long-term-pain-for-euro>

### F11. Retail client sentiment (IG/OANDA) contrarian
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** forum anecdote
- **Entry:** IG: fade the retail crowd when % net-long is extreme (e.g., > 65% net long -> bearish; < 35% -> bullish) and the week-on-week change confirms (crowd getting more one-sided).
- **Exit:** Sentiment back to 45-55%.
- **Stop:** 1.5 x ATR(14, D1).  |  **Target:** n/a
- **Parameters (defaults):** `{"long_extreme_pct": 65, "short_extreme_pct": 35}`
- **Claimed performance (as reported):** No published hit rate. IG snapshots: 29% net long (Aug 2020), 69% net long read as bearish (Oct 2023), 47.85% net long / 1.09 short-long ratio (May 2024). DailyFX (IG Group) 2024: 'contrarian signals aren't foolproof'. FXCM traits study: retail EUR/USD trades won 59% of the time but lost money on average.
- **Notes:** Broker-published, non-reproducible history; retail is structurally net long in downtrends because they fade, so the 'signal' is largely trend.
- **Sources:** <https://www.ig.com/uk/news-and-trade-ideas/euro-may-rise-as-retail-eur-usd-upside-exposure-fades-200930>; <https://www.ig.com/en-ch/news-and-trade-ideas/euro-faces-six-weeks-of-losses-as-retail-traders-persistently-re-230823>; <https://www.dailyfx.com/analysis/forex-usd-dollar-outlook-sentiment-analysis-eur-usd-gbp-usd-usd-chf-20240409.html>

### F12. Option risk reversals (25-delta) as a directional signal
- **Timeframes:** D1, W1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Trade in the direction of the 1-month 25d risk-reversal skew (EUR calls over puts = bullish) or fade extremes.
- **Exit:** n/a
- **Stop:** n/a  |  **Target:** n/a
- **Parameters (defaults):** `{"tenor": "1M", "delta": 25}`
- **Claimed performance (as reported):** GlobalCapital/Derivia Granger-causality tests of 1y 25d risk reversals vs spot: 'risk reversals cause spot' strongly rejected for all currencies except EUR/JPY; risk reversals react to spot. Practitioner view: skew measures positioning, not physical probability.
- **Notes:** Negative result; keep only as a positioning gauge.
- **Sources:** <https://www.globalcapital.com/article/28mwtvkodfvd096o6jzeo/derivatives/risk-reversals-their-relationship-with-spot>; <https://www.mql5.com/en/blogs/post/777056>; <https://www.risk.net/our-take/7961941/turn-of-the-skew-fx-options-dealers-balance-fragile-market>


## 8. Microstructure

### B01. London range vs New York: 'London sets the range, NY breaks it' statistic
- **Timeframes:** H1  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** Statistic: the London 03:00-08:00 ET range is broken during the rest of the day 95.45% of the time (70% one side only, 26% both sides, 5% neither; Edgeful, 3-month sample). Trading use: after 08:00 ET, place stop orders at the London high/low expecting at least one break; fade the second break if both sides break (26%).
- **Exit:** End of NY.
- **Stop:** Midpoint of the London range.  |  **Target:** 1x London range.
- **Parameters (defaults):** `{"london_window_et": "03:00-08:00"}`
- **Claimed performance (as reported):** As stated (short sample). Average daily range in the same source: 60 pips (10-week average, mid-2026), 53 pips (5-week).
- **Notes:** A 95% break rate is close to what a random walk gives for a 5-hour sub-range of a 24-hour day; the 26% 'both sides' number is the one with information.
- **Sources:** <https://tradethatswing.com/eurusd-daily-volatility-and-price-movement-tendencies/>; <https://www.edgeful.com/blog/posts/market-session-breakout-report>

### B02. Order-book imbalance on CME 6E futures (short-horizon)
- **Timeframes:** tick, M1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Imbalance = (bid depth - ask depth)/(bid + ask) at top N levels; trade when |imbalance| > threshold for next-k-tick direction (GitHub research project; results not accessible from this session).
- **Exit:** k ticks / seconds.
- **Stop:** 1-2 ticks.  |  **Target:** 1 tick.
- **Parameters (defaults):** `{"levels": 5, "threshold": 0.3}`
- **Claimed performance (as reported):** none found
- **Notes:** Needs depth data; outside the scope of a retail spot-data project but listed because it is one of the few genuinely documented short-horizon edges in FX literature (cost-aware).
- **Sources:** <https://github.com/olegvart/eurusd-futures-order-book-imbalance>; <https://www.cmegroup.com/markets/fx/g10/euro-fx.html>


## 9. Systematic / ML / vendor suites

### Q01. Backtrex EUR/USD backtest suite (vendor negative results)
- **Timeframes:** H1, D1  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** Four published EUR/USD runs, 2016-10-02 to 2026-10-01: London breakout (H1, SL 35 / TP 70), MACD+RSI (H1, SL 45 / TP 90), Turtle 20/10 (D1), Connors RSI(2) (D1, RSI < 5, exit SMA5 or below SMA200).
- **Exit:** See individual entries S01, T05, T01, M01.
- **Stop:** See entries.  |  **Target:** See entries.
- **Claimed performance (as reported):** London breakout: 1,230 trades, 36.3%, PF 0.87, -28.0%, DD -31.4%. MACD+RSI: 1,977 trades, PF 0.80, -53.4%, DD -56.7%. Turtle: 80 trades, PF 0.94, -2.7%, DD -14.6%. RSI(2): 75 trades, 54.7%, PF 0.78, -4.5%, DD -6.6%. Buy-and-hold over the decade: +0.1%. Sister pair GBP/USD: London breakout M15 PF 0.72 / -60%; ICT killzone FVG M15 33.89% / PF 0.80 / 1,009 trades / DD -33.5%; PDH/PDL breakout H1 loses (figures not captured); order block (figures not captured).
- **Notes:** Every textbook strategy the vendor tested on EUR/USD lost over 2016-2026. Vendor sells the tool, but the direction of the results is consistent with independent evidence (coin-flip candle patterns, placebo order blocks).
- **Sources:** <https://backtrex.com/en/backtests>; <https://backtrex.com/en/backtests/london-breakout-eur-usd>; <https://backtrex.com/en/backtests/macd-rsi-eur-usd>; <https://backtrex.com/en/backtests/turtle-trading-eur-usd>; <https://backtrex.com/en/backtests/connors-rsi-2-eur-usd>; <https://backtrex.com/en/backtests/ict-kill-zone-fvg-gbp-usd>

### Q02. Dukascopy JForex strategy contest (rules and sample strategy)
- **Timeframes:** M1, H1  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Contest sample (official): MA(7) crosses MA(14) on EURUSD (M1 or H1 variants), TP 10 pips, SL 20 pips, demo account USD 100,000; strategies fully scripted in JForex, no external files, winners must publish source. A 'MaBreak_Contest' MA-breakout file and a Bollinger-band breakout entry (allegedly copied from a prior winner) circulate on the forum.
- **Exit:** TP/SL.
- **Stop:** 20 pips.  |  **Target:** 10 pips.
- **Parameters (defaults):** `{"fast": 7, "slow": 14, "tp_pips": 10, "sl_pips": 20}`
- **Claimed performance (as reported):** Monthly ranking on four criteria (400 points, 'performance' up to 100); no winner statistics retrieved.
- **Notes:** Winning contest strategies are typically high-leverage, short-window demo results; not evidence of edge.
- **Sources:** <https://www.dukascopy.com/swiss/english/forex/jforex/forum/viewtopic.php?p=15097>; <https://www.dukascopy.com/swiss/english/forex/jforex/forum/download/file.php?id=823>; <https://www.dukascopy.com/swiss/english/forex/jforex/forum/viewtopic.php?p=64747>

### Q03. MQL5 Market EA claims (grid/martingale/scalper audit)
- **Timeframes:** M5, M15  |  **Session filter:** none  |  **Evidence:** vendor backtest
- **Entry:** n/a (meta-entry). Audit findings on best-selling EURUSD EAs.
- **Exit:** n/a
- **Stop:** n/a  |  **Target:** n/a
- **Claimed performance (as reported):** MQL5 blog audit of 10 best-selling scalping/martingale EAs: only 3 of 10 disclosed grid/martingale logic; one shipped with stop-loss disabled by default. A EURUSD grid EA: PF 2.32 but 45.13% max equity DD (Jan 2023-Jun 2026). Buyer flag: 75.91% max deposit load. 'Nova FI' free EA claim: 63% win rate EURUSD M15 (set file, unverified). 'MSX AI scalper' EURUSD M15 tester report Aug 2026 (vendor). Blog summary: 'the backtest won, the account lost'.
- **Notes:** Any EURUSD EA with PF > 2 and DD < 10% over 10 years in a vendor report should be presumed to use grid/martingale or tick-data curve fitting.
- **Sources:** <https://www.mql5.com/en/blogs/post/777027>; <https://www.mql5.com/en/blogs/post/776786>; <https://www.mql5.com/en/blogs/post/768748>; <https://www.mql5.com/en/blogs/post/776182>; <https://www.mql5.com/en/articles/21833>

### Q04. Hour-of-day x day-of-week anomaly strategy (Popovic & Durovic)
- **Timeframes:** H1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Applied Economics 46(32) 2014, hourly EUR/USD Jan 2004-Jan 2014 (Swiss market data), ANOVA of mean returns by day, hour and day x hour: significant interaction anomalies; the strongest 'arbitrage' on Fridays using trades at 00:00 and 03:00 the same day (direction not extracted from abstract).
- **Exit:** Hour-based.
- **Stop:** None.  |  **Target:** Time exit.
- **Parameters (defaults):** `{"day": "Friday", "hours": ["00:00", "03:00"]}`
- **Claimed performance (as reported):** Statistical significance reported; economic magnitude and post-2014 persistence unknown.
- **Notes:** Replicable with hourly data; combine with C01 and S18.
- **Sources:** <https://ideas.repec.org/a/taf/applec/v46y2014i32p3968-3979.html>; <https://econbiz.de/Record/intraweek-and-intraday-trade-anomalies-evidence-from-forex-market-popovi-sa%C5%A1a/10010971380>

### Q05. EPAT walk-forward trend-following study (7 majors, 2003-2025)
- **Timeframes:** D1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Time-series momentum and other trend rules tested walk-forward (in/out-of-sample) on 7 USD majors with crisis-window checks (incl. 2011 euro debt crisis).
- **Exit:** Signal-based.
- **Stop:** n/a  |  **Target:** n/a
- **Claimed performance (as reported):** Only 2 of 7 pairs cleared a 0.5 Sharpe bar out-of-sample: USD/JPY 0.78 and EUR/USD ~0.54 (time-series momentum); best equal-weight portfolio CAGR 1.24%, Sharpe 0.43, max DD -8.25%.
- **Notes:** Low but positive; duplicate of T17 from the evidence side.
- **Sources:** <https://www.quantinsti.com/articles/trend-following-strategies-major-currency-markets-epat-project/>; <https://www.quantinsti.com/articles/trend-following-strategies-major-currency-markets/>

### Q06. LSTM / neural-network direction prediction
- **Timeframes:** H1, D1  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Train LSTM on OHLC + technical (+ macro) features to predict next-bar direction; trade the sign when predicted probability > 0.55.
- **Exit:** Next bar.
- **Stop:** n/a  |  **Target:** n/a
- **Parameters (defaults):** `{"features": "technical + macro", "threshold": 0.55}`
- **Claimed performance (as reported):** Yildirim, Toroslu & Fiore (Financial Innovation 2021): hybrid LSTM on EUR/USD with technical and macro inputs 'significantly improved prediction accuracy' (no random-walk benchmark in excerpt). Frontiers 2025 monthly study: LSTM beats MLP/RF on R^2 (no directional/RW comparison). BSc thesis repo 'eurusd-lstm-garch-trading' asks whether LSTM+GARCH pays its own costs ('honest answer', content not accessible). Vontobel: 'the random walk remains the baseline to beat, and too often it is not beaten at all' (Meese-Rogoff 1983). Robot Wealth ARIMA+GARCH: not clearly profitable after costs. cond-mat/0304469: daily FX Hurst > 0.5 but EUR 'closest to Gaussian, least correlated'.
- **Notes:** Published 'accuracy' numbers are almost always in-sample or lack a cost-adjusted random-walk benchmark; the few honest write-ups find ~50-53% directional accuracy, which does not cover spread at hourly/daily frequency.
- **Sources:** <https://link.springer.com/doi/10.1186/s40854-020-00220-2>; <https://www.frontiersin.org/articles/10.3389/fams.2025.1654093>; <https://github.com/francisco-carcano/eurusd-lstm-garch-trading>; <https://am.vontobel.com/fr/insights/machine-learning-in-fx-learning-the-unlearnable>; <https://robotwealth.com/fitting-time-series-models-to-the-forex-market-are-arimagarch-predictions-profitable>

### Q07. Intraday mean-reversion regime evidence (academic)
- **Timeframes:** M1, M5  |  **Session filter:** none  |  **Evidence:** rigorous backtest
- **Entry:** Not a strategy: evidence base for M03/M04. Wisniewska (2014, 1-min EUR/USD): intraday mean reversion present, ADF rejects unit root at 1-min horizon. Middleton, Dodd & Rijavec (arXiv 2109.08242): EUR/USD high-frequency 'net style' is mean-reverting, more so than daily US stocks. Zeman & Marsik (2013): random-walk tests at 5-min/H1/H4/D1 (results not extracted).
- **Exit:** n/a
- **Stop:** n/a  |  **Target:** n/a
- **Claimed performance (as reported):** Statistical, no P&L.
- **Notes:** Mean reversion at 1-minute horizons is largely bid-ask bounce; the tradeable horizon after spread is the open question.
- **Sources:** <https://reference-global.com/article/10.1515/foli-2015-0014>; <https://pdf.arxiv.org/pdf/2109.08242>; <https://ideas.repec.org/a/mup/actaun/actaun_2013061072965.html>

### Q08. Quantheus 45 EUR/USD M5 hypotheses (IS/OOS prop-trading study)
- **Timeframes:** M5  |  **Session filter:** none  |  **Evidence:** textbook description, no stats
- **Entry:** Public GitHub repo claiming systematic in-sample/out-of-sample testing of 45 EURUSD M5 strategies for prop-firm rules; contents not accessible from this session (API access blocked).
- **Exit:** n/a
- **Stop:** n/a  |  **Target:** n/a
- **Claimed performance (as reported):** none found
- **Notes:** Listed as a lead for the next pass (also: 'Euro Macromechanica' M5 model 2003-Aug 2025 with SHA-256/GPG-signed results; 'fx-structural-momentum-bot' candle-range-theory EA).
- **Sources:** <https://github.com/Quantheus/EURUSD_45Hypotheses_Research>; <https://github.com/euro-macromechanica-backtest/results>; <https://github.com/YannVladimir/fx-structural-momentum-bot>


## EUR/USD behaviour facts

Every numeric statistic found, with its data period and source. Quality column says what kind of source it is; nothing here was recomputed.

| # | Statistic | Value(s) | Data period | Source | Quality |
|---|---|---|---|---|---|
| F-1 | Average daily range (high-low), 2020 | 74 pips (same article also says 70); max daily range 332 pips on 19 Mar 2020 | 2020 | <https://www.forex.in.rs/how-many-pips-does-eurusd-move-daily> | retail blog, internally inconsistent |
| F-2 | Average daily range, 2021 | 44 pips listed for EUR/USD in a majors table (pair average 54); method unstated | 2021 | <https://www.forex.in.rs/how-many-pips-does-eurusd-move-daily> | retail blog, looks low |
| F-3 | Average daily range, 2023 | 87 pips; max 243 pips (15 Mar 2023); min 28 pips (Aug 2023) | 2023 | <https://www.forex.in.rs/how-many-pips-does-eurusd-move-daily> | retail blog |
| F-4 | Average daily range, 'several years' | 75 pips | undated | <https://www.forex.in.rs/how-many-pips-does-eurusd-move-daily> | retail blog |
| F-5 | Average daily range, recent | 60 pips (10-week avg), 53 pips (5-week avg); 'most of the last 5 years above 60, occasionally above 110' | mid-2026 | <https://tradethatswing.com/eurusd-daily-volatility-and-price-movement-tendencies/> | blog, computed from data |
| F-6 | ATR(14) daily reference points | ~102 pips (Dec 2022, 'above 100 = volatile'); 69 pips vs 180-day ATR 57 (2019); 78 pips on an undated tool page | 2019-2022 | <https://fxstreet.com/analysis/eur-usd-effective-bullish-domination-continues-202212190844> | analyst notes |
| F-7 | Daily range typical band | 60-100 pips (FXPro); 50-80 pips (TradeTheDay) | undated | <https://fxpro.com/trading/forex/eurusd> | broker pages |
| F-8 | Annual high-low range | 2019: 691 pips; 2020: 1,637 pips; 2023: 828 pips (2nd-lowest since 1999); 2023 'dominant trend' -828 pips with sub-trends +692/-414; 2024 high 1.1214 (25 Sep) low 1.0334 (22 Nov), avg 1.0821 | 2019-2024 | <https://investinglive.com/technical-analysis/!/eurusd-has-an-above-average-trading-range-for-2020-after-non-trending-2019-20201228> | ForexLive/CityIndex/PoundSterlingLive |
| F-9 | All-time range | High 1.599, low 0.827 (1994-2016 daily series, 5,930 days) | 1994-2016 | <https://www.fxstreet.com/education/the-most-detailed-historical-analysis-of-eurusd-201701130858> | FXStreet/ColibriTrader |
| F-10 | Monthly range examples | 258 pips (Jul 2016), 468 (Jun 2016), 352 (Aug 2016), 398 (Oct 2016); Q1 2024 ~300-pip range; 700-pip range over 18 months to mid-2024 | 2016, 2024 | <https://www.fxstreet.com/analysis/eur-usd-v-dxy-monthly-levels-ranges-targets-201611070501> | analyst notes |
| F-11 | Weekly range examples | 100+ pip weeks in 4 of 7 weeks (May 2024); 136-pip week (2022); ~60-pip week late Dec 2024 | 2022-2024 | <https://fxstreet.com/analysis/fed-interest-rate-move-contains-the-power-to-significantly-move-currency-prices-202405231251> | analyst notes |
| F-12 | Hourly volatility profile | Two peaks: ~28 pips max ATR near 07:00 GMT and ~34 pips 13:00-15:00 GMT (TradingView seasonality study, years unstated); EarnForex: first vol area in early European hours, peak when US opens with Europe still active; QuantHedge (14 yrs): NY open-to-London close is the most volatile 3 hours, then London open-to-Tokyo close; 06:00-08:00 UTC widest spreads/lowest volume (TitanFX) | various | <https://my.tradingview.com/chart/EURUSD/O5OLT3x1-Seasonality-Intra-day-Trading-System> | mixed quality |
| F-13 | Per-hour session ranges | London ~10 pips/hour (Babypips); Asia 15-25 pips/hour rising to 30-50 around London open (guide); one lesson table claims 114 pips for the London session (method unknown); NY 'about 71 pips' historical reference | undated | <https://babypips.com/learn/forex/london-session> | education pages, not comparable |
| F-14 | Which hour sets the daily high/low | 18:00 ET hour: high 8% / low 6% of days (random 4.17%); 03:00-05:00 ET: high 12% / low 11% (random 8.33%); 09:00-12:00 ET: high 20% / low 21% (random 12.5%) | 2005-2009 | <https://www.dailyfx.com/forex/technical/article/special_report/2012/07/21/Improving_Profitability_with_Intraday_Seasonality.html> | DailyFX, 5-year sample |
| F-15 | London range broken later in the day | 95.45% of days (70% one side, 26% both sides, 5% neither), London = 03:00-08:00 ET | 3-month sample, 2026 | <https://tradethatswing.com/eurusd-daily-volatility-and-price-movement-tendencies/> | Edgeful via blog, short sample |
| F-16 | Asian range size | EUR/USD within 30-50 pips of the 22:00 UTC open on ~70-80% of days (blog); Tokyo-only window averages ~14 pips (blog) | undated | <https://tradingonmt5.pages.dev/eurusd-asia-mean-reversion.html> | low quality |
| F-17 | Share of days closing above open | 50.42% (1,666 up, 1,602 down, 36 unchanged of 3,304 days 'since inception'); distribution bell-shaped with heavy tails | ~1999-2012 | <https://www.forexfactory.com/thread/post/6036885> | forum computation |
| F-18 | Open-to-close daily return | Mean not significantly different from zero, symmetric, near-Gaussian tails (NumXL, Mar 2010-Apr 2012) | 2010-2012 | <https://support.numxl.com/hc/en-us/articles/360032493932-Predict-This> | vendor tutorial |
| F-19 | Daily pivot touch frequencies | High > PP 87.38%, low < PP 85.90%; high >= R1 43.10%, R2 20.41%, R3 6.26%; low <= S1 45.34%, S2 21.48%, S3 6.56% (1,965 days); low <= S1 50.42% when open < PP vs 36.20% when open > PP | Jan 2003-Nov 2010 | <https://mql5.com/en/forum/2724> | forum study, old data |
| F-20 | Probability of taking out previous day high/low | Not found for EUR/USD; pivot proxies above; Edgeful sells a 'previous day's range' report | n/a | <https://www.edgeful.com/blog/posts/previous-days-range-report> | gap in evidence |
| F-21 | Inside days | 4,174 inside days across 7 pairs Jan 1993-Sep 2008 (avg 596/pair, ~3/month); followed by upward-biased moves the next week. EUR/USD daily since 2003: inside-bar avg range 82.7 pips vs ~117 avg day; day after inside bar avg 124 pips | 1993-2008; 2003- | <https://www.scribd.com/document/496411061/CurrencyTrader1108s4> | magazine study + forum |
| F-22 | Engulfing candle follow-through | After a bearish engulfing on EUR/USD: up 50.9% / down 49.1% | undated | <https://forexop.com/strategy/engulfing-candle-trade/> | blog test |
| F-23 | Fibonacci retracement levels | Retracement depths near 23.6/38.2/50/61.8% explained by chance (G10 vs USD, 1-min data Oct 2003-May 2016) | 2003-2016 | <https://forexop.com/strategy/fibonacci-fact-or-fiction/> | blog test |
| F-24 | Day-of-week returns | Monday -1.90% annualised, Friday +1.73% annualised (2000-Feb 2018, Seasonax); Monday effect present 2010-2012 but not 1999-2009 (Bush & Stephens sister paper); Friday 00:00/03:00 anomalies 2004-2014 (Popovic & Durovic) | 2000-2018 | <https://www.seasonax.com/market-efficiency-the-euro-is-looking-forward-to-the-weekend> | vendor + academic |
| F-25 | Monthly seasonality | December +1.24% avg, positive 65% of years (1971-2026); May -0.62%, June +0.52% (50+ yrs, StoneX); August seasonally weak (implied) | 1971-2026 | <https://tickerleague.com/forex/eurusd/seasonality> | vendor seasonality |
| F-26 | January effect | Annual high or low set in January in 76% of years 1972-2025; only 3 of 8 (37.5%) in the last 8 years | 1972-2025 | <https://www.peterlbrandt.com/wp-content/uploads/2026/03/January-Effect_for-2026.pdf> | FactorResearch note |
| F-27 | Streak reversal | Fading 3-day streaks with >1% cumulative move: win rate 59% on EUR/USD (highest of majors), ~6 years of daily data | ~2019-2025 | <https://prod.wsprod.tastyfx.com/news/fading-multi-day-dollar-moves-a-quantitative-case-for-mean-reversion> | broker backtest, no details |
| F-28 | Abnormal-day behaviour | Momentum within the abnormal day, reversal the next day (EURUSD and 4 others, 2008-2018); profitability contested | 2008-2018 | <https://ideas.repec.org/a/eme/jespps/jes-11-2019-0503.html> | peer-reviewed |
| F-29 | Autocorrelation / Hurst | Daily returns: essentially zero autocorrelation; Hurst ~0.5 at daily-weekly horizons, ~0.33 at long horizons (blog, 1985-2023); 10-second returns H ~0.5 (arXiv 1906.07834); older multi-currency study: daily H > 0.5 with EUR 'closest to Gaussian'; intraday 1-min: mean-reverting (Wisniewska 2014; Middleton et al. 2021) | various | <https://pdf.arxiv.org/pdf/2109.08242> | academic + blog |
| F-30 | Intraday return seasonality (academic) | USD appreciates into Tokyo/Frankfurt/London fixes and depreciates after (W-shape; 5-min data 1999-2019, 9 currencies); 30-40% of daily volume in the 3h before + 1h after the London fix; EUR/USD depreciates in European hours, appreciates in US hours (Breedon-Ranaldo, 10 yrs HF data); carry earned intraday, momentum earned overnight | 1999-2019 | <https://econpapers.repec.org/RePEc:bla:jfinan:v:79:y:2024:i:1:p:541-578> | peer-reviewed |
| F-31 | Pre-FOMC drift | USD -32 bp before expected cuts, +20 bp before expected hikes over the 2 days pre-decision; no realised-vol increase pre-FOMC | ~1994-2015 | <https://macrosynergy.com/?p=41075> | academic via summary |
| F-32 | NFP first-hour range | Median 47.1 pips vs 13.1 pips normal weekday hour (3.6x); six releases: 21.4, 52.3, 74.4, 53.2, 41.8, 32.3 pips | 2026 | <https://www.fxstreet.com/analysis/nfp-stress-test-six-payrolls-releases-measured-in-daily-loss-limits-202611050906> | FXStreet |
| F-33 | NFP 15-min / 4-hour moves | 28 pips / 49 pips (five releases, Aug 2018); 34-37 pips / 50-63 pips (other 2018 samples); surprises < +/-25K rarely > 40 pips (2015); most pairs back to pre-release levels within an hour (2021) | 2015-2021 | <https://www.fxstreet.com/analysis/how-to-trade-the-us-nfp-with-eur-usd-201808021440> | FXStreet |
| F-34 | US CPI reaction | 34-37 pips in 15 min, 50-63 pips in 4h (2018 samples); Dec 2022: 1.0555 -> 1.0648 immediately (+93 pips), >1% on the day; 2019 example: +24 pips in 5 min, 37 pips total | 2018-2022 | <https://www.fxstreet.com/analysis/how-to-trade-the-us-inflation-data-with-eur-usd-201807111106> | FXStreet |
| F-35 | ECB decision reaction | Average 19.3 pips in the first 60 minutes over 9 decisions (FundedFast); single events 50-100 pips | 2024-2026 | <https://fundedfast.com/tools/event-reactions/ecb> | vendor tool |
| F-36 | FOMC day examples | +50 pips in seconds (Jan 2019); ~-80 pips (Sep 2023); statement spike then -0.5% close (17 Sep 2025); -60 pips in minutes (Jun 2026) | 2019-2026 | <https://www.marketpulse.com/markets/eurusd-technical-euro-bullish-trend-intact-despite-12-sell-off-after-fomc/> | anecdotes |
| F-37 | Month-end fix behaviour | Case studies: ~+20 pts in 5 min before the WM window then -12 pips within 2 min after (a January); sharp spike and reversal after ~1 min (another month); no reversal at some month-ends (July; Nov 2025 fix = Siren rate exactly); estimated 'savings' $0-675 per million | 2023-2025 | <https://thefullfx.com/what-happened-at-the-month-end-fix-39/> | The Full FX case studies |
| F-38 | Weekend gap fill rates | 66.15% (ForexFactory, period unstated); 70-75% within days (guide); all 204 gaps 2001-2020 'more likely than not' filled by Wednesday London (DailyForex); gaps < 0.5x ATR filled within 48h 88.4%, gaps > 0.75x ATR filled within 24h 28.2% / within week 41.9% (fxnx, 500 Sunday opens, method undisclosed); avg weekly gap ~70% of Friday's open-close range (EarnForex); '98% filled at some point' over 18 months (MQL5 forum) | 2001-2025 | <https://www.dailyforex.com/forex-articles/2020/06/forex-gap-trading/144786> | mixed |
| F-39 | Spreads | ECN/raw London session 0.0-0.2 pips (Pepperstone avg 0.1; IC Markets 0.1 + $3.50/side; Exness 0.07); 200-broker ECN average 0.17 pips; standard accounts 0.8-1.6 pips; Asia 0.3-0.8 pips raw; rollover spikes 1-3 pips for 1-3 minutes; NFP widening to 5-10 pips, up to 25 | 2024-2026 | <https://www.compareforexbrokers.com/our-methodology/forex-fees/tightest-spreads> | broker comparison sites |
| F-40 | Implied / realised volatility | 1M IV: 11.0 (Jan 2025) -> 9.0 (Feb) -> 6.5 (lowest since Sep 2024); 7.8 on 21 Jan 2025 from 9.4 peak; 8.35 (Sep 2025) from 9.8; 3M IV 6.47% (3 Oct 2025, lowest since Nov 2024); 1M realised 4.8% vs traded 6.5% (Nov 2025); 1M IV 5.2% 'lowest since before the energy crisis' (undated); 1M IV 5.45 vs 2-yr low 4.9 late Mar / 7.1 mid-Apr, realised 4.3 (~2024); 1-week realised < 7.0 (Jul 2025); 1M IV 9.6 -> 7.4 into a Thanksgiving | 2024-2025 | <https://www.tickmill.com/blog/fx-options-insights-210125> | options desks |
| F-41 | Correlations (daily returns) | EUR/USD vs broad USD index: -0.820 (2024), -0.905 (2025); vs gold: +0.418 (2023), +0.288 (2024), +0.362 (2025), 1-yr +0.39; gold vs DXY -0.50 (latest); USD vs S&P mostly negative 2022-24, briefly positive 2023, rising together early 2024; oil-USD shifted negative (2026) | 2023-2026 | <https://convextrade.com/compare/eurusd-vs-dxy/correlation> | data site + commentary |
| F-42 | Yield-differential explanatory power | Level correlation with EUR/USD since 2019 (daily): 1y differential 66%, 2y 62%, 10y 5% (BNP); 2y+terms-of-trade model R^2 87% on 1-yr window (MNI/Citi); daily-change regression on 2y/10y yields R^2 ~5%; ING 2023: 2y swap coefficient ~0; 2y swap gap -145 bp -> FV 1.067 (Mar 2025); -80 -> -100 bp in a week (May 2026) | 2019-2026 | <https://economic-research.bnpparibas.com/html/en-US/multiple-factors-underpinning-renewed-strength-euro-against-dollar-4/17/2023,48485> | bank research |
| F-43 | Valuation | OECD PPP fair value ~$1.38 (2019; euro ~22% undervalued, cheap 5 yrs); 1.4060 with spot 15% undervalued (2020); ING BEER: ~9-10% overvalued 2022 (FV near parity), ~5% undervalued late 2024 | 2019-2024 | <https://www.fxstreet.com/analysis/great-graphic-euros-oecd-ppp-201906131134> | bank/OECD |
| F-44 | Retail positioning snapshots (IG) | 29% net long (Aug 2020); ~69% net long (Oct 2023); 47.85% net long, 1.09 short:long (May 2024); FXCM: retail EUR/USD trades profitable 59% of the time but net losing | 2020-2024 | <https://www.ig.com/en-ch/news-and-trade-ideas/euro-faces-six-weeks-of-losses-as-retail-traders-persistently-re-230823> | broker |
| F-45 | COT | Large-spec EUR net long most bullish since Jul 2023 (early 2026); '343-report extreme' (Oct 2026); CME Euro FX code 099741 | 2023-2026 | <https://www.fxstreet.com/analysis/euro-positioning-reaches-343-report-extreme-as-cot-data-points-toward-a-potential-medium-term-floor-202610041903> | commentary |
| F-46 | Round numbers | Take-profit orders cluster on 00 levels, stop-loss orders just beyond them (bank order data, Osler 2003); EBS EUR/USD order-book volume clusters at round prices and acts as barriers (Lallouache & Abergel) | 2003; 2013 | <https://ideas.repec.org/a/bla/jfinan/v58y2003i5p1791-1819.html> | peer-reviewed |
| F-47 | Trend-following Sharpe | Time-series momentum EUR/USD out-of-sample Sharpe ~0.54 (2003-2025, EPAT); cross-sectional 12m FX momentum Sharpe 0.3, max DD -45.87% (Quantpedia) | 2003-2025 | <https://www.quantinsti.com/articles/trend-following-strategies-major-currency-markets-epat-project/> | student/vendor research |
| F-48 | Decade buy-and-hold | EUR/USD +0.1% from 2 Oct 2016 to 1 Oct 2026 (Backtrex); GBP/USD +2% | 2016-2026 | <https://backtrex.com/en/backtests/london-breakout-eur-usd> | vendor |

## Gaps: statistics that were searched for and NOT found

- Year-by-year average daily range table for 2015-2019, 2021-2022, 2024, 2025 (only 2020, 2023 and 'recent' values exist publicly; compute from OHLC).
- Probability that EUR/USD takes out the previous day's high or low (only pivot-level proxies from 2003-2010).
- How often price returns to the daily open / weekly open (no study; one unverifiable 49.7% weekly-open figure).
- Which session sets the daily high/low as a share of days (only the 2005-2009 DailyFX hour windows).
- Per-session average ranges (QuantHedge computed them for 14 years but the numbers were not in the retrievable text).
- Hour-by-hour pip table (EarnForex and Investing.com publish them as images/tools only).
- Next-day continuation vs reversal after a large single-day move (only the 3-day-streak broker study and the academic abnormal-day papers).
- Any hit rate for COT extremes, retail sentiment extremes, month-end fix direction, turn-of-month, Friday afternoon or holiday effects on EUR/USD.
- RSI(14) 30/70, Bollinger squeeze, Heikin-Ashi, supply/demand, flags, NR7 and ATR-multiplier comparisons: no EUR/USD backtest numbers anywhere.
- Backtrex figures for the GBP/USD previous-day-high/low and order-block tests (pages exist, numbers not in search excerpts).
- Contents of the GitHub repos (Quantheus 45 M5 hypotheses, LSTM+GARCH thesis, Euro Macromechanica M5 results): API access blocked.


## Formulas referenced

- Classic pivots: PP=(H+L+C)/3; R1=2PP-L; S1=2PP-H; R2=PP+(H-L); S2=PP-(H-L); R3=H+2(PP-L); S3=L-2(H-PP).
- Fibonacci pivots: PP=(H+L+C)/3; R1/S1=PP+/-0.382(H-L); R2/S2=PP+/-0.618(H-L); R3/S3=PP+/-1.000(H-L).
- Woodie: PP=(H+L+2C)/4 (platform variant (H+L+2O)/4); R1=2PP-L; S1=2PP-H; R2=PP+(H-L); S2=PP-(H-L).
- Camarilla: Hn/Ln = C +/- (H-L) x {0.0916, 0.183, 0.275, 0.55} for n=1..4 (=1.1/12, 1.1/6, 1.1/4, 1.1/2); some vendors quote H4 = C + 1.5(H-L).
- ATR(14) Wilder: ATR_t = (13 x ATR_{t-1} + TR_t)/14, TR = max(H-L, |H-C_prev|, |L-C_prev|).
- Chandelier exit: long stop = HH(22) - 3 x ATR(22); short stop = LL(22) + 3 x ATR(22).
- Larry Williams volatility breakout: buy stop = Open + k x (H_prev - L_prev), k=0.25 default.
- Z-score: z = (C - SMA(20)) / stdev(20); fade at +/-2, exit at 0.
- Connors RSI(2): long if C > SMA(200) and RSI(2) < 5 (or 10); exit C > SMA(5).
- Fair value gap (bullish): high[2] < low[0] over three consecutive candles; zone = [high[2], low[0]].
- 2y differential fair value: EURUSD = a + b x (DE2y - US2y) [+ c x rel. terms of trade], rolling 250-day OLS; trade residual z-score.
- Taylor-rule differential: i*_EA - i*_US = 1.5 x (pi_EA - pi_US) + 0.5 x (gap_EA - gap_US) (+ real exchange rate term optional).
- Risk reversal: RR25 = IV(25d call) - IV(25d put); Granger tests say spot leads RR, not the reverse.
