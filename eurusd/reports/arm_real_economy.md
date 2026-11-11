# Arm R: real economy (`real_economy`) - energy terms of trade, growth leading indicators and US real yields as an extra vote

Code `src/eurusd/arms/real_economy.py` (`run(cost_pips=1.2)`; `python -I src/eurusd/arms/real_economy.py` fetches (cached), runs
everything in about 20 seconds once the data are cached and rebuilds this file; `... real_economy.py report` rebuilds the file only). Results in
`experiments/results/arms/`: `real_economy_positions.parquet` (daily stream of the final extra-vote rule: `pos`, `fwd_bp`, `net_bp`),
`real_economy_report.csv` (protocol table of the 12 candidates, `variant`, `final`, plus the agreement rule as reference and the 0.6-pip
run), `real_economy_votes.csv` (every signal x rule x horizon x decision mode x period: n, decisions per year, accuracy, Wilson
interval, net bp), `real_economy_paired.csv`, `real_economy_bar.csv`, `real_economy_candidates.csv`, `real_economy_leakchecks.csv`,
`real_economy_incremental.csv`, `real_economy_signals.parquet`, `real_economy_data_catalogue.csv`, log `logs/real_economy.log`.
The docstring of the module (signals, signs, lags, evaluation, selection rule) was written before the first accuracy number.

## Verdict
1. **The round-5 success bar is NOT met - not by the rule the declared selection picks, and not by any of the other 11.**
   The pick is `cli_d6m_diff` (agreement rule AND the euro-area-minus-US 6-month change of the OECD leading indicator agrees).
   Non-overlapping decisions, against the agreement rule alone:
   * 21 sessions: 60 % [49-69] n=87 vs 59 % n=156 in 2010-26 (**+0.8 points**), 60 % n=45 vs 57 % n=96 in 2016-26 (**+2.7**),
     50 % n=10 vs 60 % n=35 in 2023-26 (**-10**). 5.2 / 4.2 decisions a year (bar: 6).
   * 42 sessions: 65 % n=51 vs 61 % n=89 (+4.0), 63 % n=27 vs 59 % n=56 (+4.0), 50 % n=6 vs 45 % n=20; 3.1 / 2.5 decisions a year.
   * 63 sessions: 68 % n=40 vs 72 % n=61 (-4.6), 62 % n=21 vs 71 % n=38 (-9.1).
   Bar components: gain of 3 points at 21 AND 42 sessions in both periods - no (21 sessions fails twice); 6 decisions a year - no;
   not worse in 2023-26 - no (21 sessions); placebo loses half the gain - yes, but there is no gain to lose. In its own selection
   period (2010-15) the AND rule is at 59.5 % (n=42) and the agreement rule alone at 61.7 % (n=60): the pick "wins" a contest in which
   every entrant is below the benchmark. The runner-up (`gasratio_d3m`, lower bound 44.4 % against 44.5 %) is at -1.4 / -0.8 points.
   The pick also rests on revised (not real-time) OECD data and has no value after May 2024 (FRED froze the series, the OECD API is
   blocked here).
2. **A fourth vote from these three families does not sharpen the agreement rule.** Across the 12 candidates the non-overlapping gain
   over the agreement rule is negative for 11 of 12 at 21 sessions in 2010-26 (median -3.8 points, range -10.1 .. +0.8), about zero at
   42 sessions (median +1.5, range -5.1 .. +8.2 on 37-76 decisions) and negative for all 12 at 63 sessions (-1.9 .. -13.0). No candidate
   reaches +3 at 21 sessions in 2010-26, and none has +3 at both 21 and 42 sessions in both periods. The AND rules make 3.5-7.1
   non-overlapping decisions a year at 21 sessions and 2.2-4.6 at 42. On the weekly grid, paired with the agreement rule on the same
   sessions, no difference at 21 sessions excludes zero in 2010-26 or 2016-26 for any candidate. Calls that the new vote CONTRADICTS are
   right about as often as calls it confirms (46-61 % against 49-60 % at 21 sessions, non-overlapping, 2010-26): the vote does not sort.
3. **Standalone, at 1-3 months, only 6-month Brent carries anything, and it is arm O's finding, not timely information.**
   `brent_usd_d126` (sign adopted from arm O, not re-fitted): 55 % [48-61] n=208 / 57 % [47-66] n=104 / 68 % [56-78] n=69 at
   21 / 42 / 63 sessions non-overlapping in 2010-26 (weekly 56 / 56 / 58, n=869); 2016-26 55 / 61 / 73 (n=133 / 66 / 44), weekly
   58 / 59 / 60; 2023-26 47 / 61 / 80 (n=47 / 23 / 15), weekly 53 / 50 / 52. That reproduces arm O's 55-58 %. But the same signal made
   63 sessions STALER scores 59 % at 21 sessions (fresh 56 %) and 59 % at 63 (fresh 58 %): it is a slow regime bet (the 2014-16 and
   2020-22 oil cycles), not information that has to be fresh. In EUR terms it is weaker (53 / 53 / 64; weekly 53 / 53 / 55).
   Everything else is at chance:
   * Europe-vs-US gas, monthly (`gasratio_d3m`): 52 / 53 / 49 (n=208 / 104 / 69). Daily TTF / Henry Hub (`ttf_hh_d63`, 2018-26 only):
     57 % [48-66] n=108 / 59 % [46-71] n=54 / 47 % [32-63] n=36, weekly 55 / 60 / 59 (n=452) - one gas shock, intervals contain 50.
   * Euro-area trade balance momentum: 56 / 53 / 59 non-overlapping, 52 / 51 / 51 weekly.
   * Growth: CLI differential 52 / 48 / 48; sentiment level differential 44 / 42 / 46; sentiment 3-month change 45 / 50 / 51.
   * US real yields as CHANGES: `tips_d21` 50 / 47 / 48, `tips_d63` 46 / 53 / 52 (weekly 46-49: if anything wrongly signed, as arm O
     found for levels); 5y5y breakeven 51 / 41 / 48.
4. **Coverage extension (calls when the three old signals do not agree): no.** 42-58 % at 21 sessions in 2010-26 and 2016-26; only `brent_usd_d126` is
   above 53 % with any consistency (55 % [47-62] n=170 / 56 % n=93 / 56 % n=64; weekly 55 / 56 / 56, n=482), and its 63-session-stale
   version does 58 / 59 / 57.
5. **Daily stream and incremental test: fails.** The final rule as a weekly-tranche book: net Sharpe 0.47 / 0.35 / -0.19
   (2010-26 / 2016-26 / 2023-26) at 1.2 pips against 0.52 / 0.51 / 0.43 for the agreement rule itself; three-way EW 0.62 against
   two-way 0.64 on 2016-26 (0.26 against 0.36 on 2023-26). Daily P&L correlation 0.98 with the agreement-rule book on active days,
   0.78 with `regime_trend`. It is a thinned copy of the existing stream.
6. **Two leads, neither a result.** (i) Daily TTF / Henry Hub as a confirmation: on WEEKLY decisions the AND rule is 63 / 74 / 75 %
   (n=123 / 119 / 119) against 56 / 62 / 65 % for the agreement rule on the same 2018-26 sessions, paired difference
   +7 [-1,+14] / +12 [+3,+21] / +10 [+3,+17] points, and it fades when the signal is made stale (55 / 57 at 21 sessions). The
   non-overlapping stream does NOT confirm it (53 / 62 / 67 % on 59 / 37 / 27 decisions against 58 / 61 / 69 %), the history is 8.8
   years with one gas shock, it has no 2010-15 record so the declared rule could not pick it, and 12 of the 108 paired intervals
   exclude zero where about 5 would by chance (8 positive, 4 negative, heavily overlapping cells). Worth a forward look, nothing more.
   (ii) US real-yield changes are wrongly signed as a vote: when `tips_d21` contradicts the agreement rule the rule is right more
   often (2016-26, 42 sessions: confirmed minus contradicted -20 points [-34,-5]). I did not flip the sign: that would be fitting it.

## 1. Data: sources, spans, publication lags
| file                                               | source                                         |   rows | first      | last       | lag used                       |
|:---------------------------------------------------|:-----------------------------------------------|-------:|:-----------|:-----------|:-------------------------------|
| data/macro/real_economy_fred_DFII10.csv            | FRED DFII10                                    |   5968 | 2003-01-02 | 2026-11-09 | 1 calendar day                 |
| data/macro/real_economy_fred_T5YIFR.csv            | FRED T5YIFR                                    |   5969 | 2003-01-02 | 2026-11-10 | 1 calendar day                 |
| data/macro/real_economy_fred_DHHNGSP.csv           | FRED DHHNGSP                                   |   5722 | 1997-01-07 | 2026-11-03 | monthly mean, month-end + 45 d |
| data/macro/real_economy_fred_PNGASEUUSDM.csv       | FRED PNGASEUUSDM                               |    417 | 1992-01-01 | 2026-09-01 | month-end + 45 d               |
| data/macro/real_economy_fred_UMCSENT.csv           | FRED UMCSENT                                   |    677 | 1952-11-01 | 2026-09-01 | month-end + 10 d               |
| data/macro/real_economy_fred_USALOLITONOSTSAM.csv  | FRED USALOLITONOSTSAM                          |    829 | 1955-01-01 | 2024-01-01 | month-end + 45 d               |
| data/macro/real_economy_fred_EA19LOLITONOSTSAM.csv | FRED EA19LOLITONOSTSAM                         |    684 | 1965-12-01 | 2022-11-01 | month-end + 45 d               |
| data/macro/real_economy_fred_DEULOLITONOSTSAM.csv  | FRED DEULOLITONOSTSAM                          |    757 | 1961-01-01 | 2024-01-01 | month-end + 45 d               |
| data/macro/real_economy_fred_FRALOLITONOSTSAM.csv  | FRED FRALOLITONOSTSAM                          |    687 | 1966-11-01 | 2024-01-01 | month-end + 45 d               |
| data/macro/real_economy_fred_ITALOLITONOSTSAM.csv  | FRED ITALOLITONOSTSAM                          |    746 | 1961-12-01 | 2024-01-01 | month-end + 45 d               |
| data/processed/cross/real_economy_ttf_D1.parquet   | Yahoo TTF=F                                    |   2278 | 2017-10-23 | 2026-11-11 | 1 calendar day                 |
| data/processed/cross/real_economy_ng_D1.parquet    | Yahoo NG=F                                     |   6581 | 2000-08-30 | 2026-11-11 | 1 calendar day                 |
| data/macro/real_economy_ecb_esi.csv                | ECB RTD/M.S0.S.Y_ESIND.F                       |    560 | 1980-01    | 2026-08    | month-end + 10 d               |
| data/macro/real_economy_ecb_trade_x.csv            | ECB TRD/M.I10.Y.X.TTT.J10.4.VAL                |    296 | 2002-01    | 2026-08    | month-end + 50 d               |
| data/macro/real_economy_ecb_trade_m.csv            | ECB TRD/M.I10.Y.M.TTT.J10.4.VAL                |    296 | 2002-01    | 2026-08    | month-end + 50 d               |
| data/macro/datahub_brent_daily.csv                 | datahub oil-prices (EIA Brent spot), repo file |   9122 | 1987-05-20 | 2026-11-03 | 1 calendar day                 |

* **Lags.** Daily market series: stamp d is used from the session whose NY-close date is >= d + 1 calendar day
  (`featstore._align_lagged(..., 1)`, the convention of every earlier arm). Monthly series: reference month m is used from
  month-end(m) + LAG days, plus the same one day. LAG = 45 d for the OECD leading indicators (published about six weeks after
  the month) and for the IMF European gas price (IMF publishes in the first half of m+1, FRED later); 50 d for euro-area trade
  (Eurostat releases around day 15-18 of m+2); 10 d for the Commission's Economic Sentiment Indicator (released on the
  next-to-last working day of m, a few times in the first week of m+1) and for the final Michigan sentiment (last or
  next-to-last Friday of m). A monthly signal gives no vote once its newest usable observation is more than 75 days old; a daily
  one once its newest stamp is more than 10 days old.
* **TTF history is short.** Yahoo `TTF=F` starts 2017-10-23; with a 63-session change the signal exists from 2018-01-22, i.e. for
  52 % of 2010-26 and not at all in the 2010-15 selection window. The long-history stand-in is the IMF monthly European gas price
  (FRED `PNGASEUUSDM`, USD/MMBtu: TTF in recent years, border prices before) against the monthly mean of the Henry Hub spot
  (FRED `DHHNGSP`, months with at least 15 quotes; FRED's file is thin before 2007, so the ratio signal starts 2007-09).
* **Conversions.** Brent in EUR = Brent (USD) / previous-session EUR/USD close; TTF in USD/MMBtu = EUR/MWh x previous-session
  EUR/USD / 3.412. The gas ratios are in a common currency. Signals built this way contain the lagged EUR/USD return by
  construction; `brent_usd_d126` is the currency-free control (correlations in section 9).
* **Vintage.** Every monthly series is the CURRENT vintage. The OECD CLI is revised materially (the trend is re-estimated every
  month), the trade balance moderately, sentiment hardly. ALFRED (real-time vintages) is refused by the proxy, so this look-ahead
  could not be removed or measured. It favours the CLI signal, which is the one the selection rule picked; it failed anyway.
* **OECD CLI stops.** FRED froze the OECD series at 2024-01 (`EA19LOLITONOSTSAM` at 2022-11; after that the 6-month change of the
  DEU/FRA/ITA mean is used). `sdmx.oecd.org` answers 403 through the proxy, so `cli_d6m_diff` has no value after 2024-05-30.
* **Euro-area real yields: not built.** An AAA yield minus TRAILING HICP is not an expectation; its 1-3 month change is the nominal
  change plus base effects, and arm O found the trailing-inflation real differential wrongly signed (43-48 %). Family C is US-only.
* **Not reachable (proxy 403):** `sdmx.oecd.org`, `ec.europa.eu` (Eurostat, DG ECFIN), `api.db.nomics.world`, `alfred.stlouisfed.org`,
  `www.eia.gov`. Reachable: `fred.stlouisfed.org` with `curl --http1.1`, the Yahoo chart API with a browser User-Agent, the ECB data
  API. The ESI comes from the ECB flow `RTD` (the ECB `SUR` flow only has quarterly items); it ends 2026-08 there. US ISM: not free, skipped.
* **A bug caught before any result:** Yahoo daily bars are stamped at midnight exchange time (04:00 or 05:00 UTC). Converting with
  the current `gmtoffset` put every summer bar one day EARLY (a one-day look-ahead on TTF and NG). The fetch converts with the
  exchange time zone; the cached parquet files carry the trading date.

## 2. The 12 candidate signals and their priors (fixed before any result)
| signal         | fam   | prior (sign on the raw quantity)                                                    | first value   | last value   | defined 2010-26   | long share   |   sign flips / yr |
|:---------------|:------|:------------------------------------------------------------------------------------|:--------------|:-------------|:------------------|:-------------|------------------:|
| brent_eur_d63  | A     | - dearer oil (EUR terms, 3 months) worsens euro-area terms of trade                 | 2003-04-01    | 2026-11-05   | 100 %             | 48 %         |              14.9 |
| brent_eur_d126 | A     | - same, 6 months                                                                    | 2003-06-29    | 2026-11-05   | 100 %             | 47 %         |              11.5 |
| brent_usd_d126 | A     | - same in USD: arm O's `oil_d126`, sign adopted from its table                      | 2003-06-26    | 2026-11-05   | 100 %             | 49 %         |              10   |
| gasratio_d3m   | A     | - Europe/US gas price ratio up (monthly, 3 months) = euro-area terms of trade worse | 2007-09-16    | 2026-11-05   | 100 %             | 49 %         |               2.9 |
| ttf_hh_d63     | A     | - same, daily TTF / Henry Hub futures, 2018+ only                                   | 2018-01-22    | 2026-11-05   | 52 %              | 45 %         |               9.6 |
| ea_tb_mom      | A     | + improving euro-area goods trade balance                                           | 2003-01-01    | 2026-11-05   | 100 %             | 50 %         |               2.1 |
| cli_d6m_diff   | B     | + euro-area minus US 6-month change of the OECD leading indicator (ends mid-2024)   | 2003-01-01    | 2024-05-30   | 86 %              | 40 %         |               1.1 |
| sent_lvl_diff  | B     | + euro-area ESI minus US Michigan sentiment, expanding z-scores                     | 2003-01-01    | 2026-11-05   | 100 %             | 81 %         |               1.4 |
| sent_d3m_diff  | B     | + 3-month change of the same differential                                           | 2003-01-01    | 2026-11-05   | 100 %             | 50 %         |               3.9 |
| tips_d21       | C     | - US 10y real yield up over 1 month = dollar up                                     | 2003-02-02    | 2026-11-05   | 100 %             | 51 %         |              31.6 |
| tips_d63       | C     | - same over 3 months                                                                | 2003-04-01    | 2026-11-05   | 100 %             | 50 %         |              17.7 |
| bei_d63        | C     | + US 5y5y breakeven up over 3 months = dollar down (weak prior)                     | 2003-04-01    | 2026-11-05   | 100 %             | 50 %         |              27.4 |

* Positive value = vote for long EUR/USD. No fitting, no thresholds, no sign learned from the data; the vote is the sign.
* Oil: arm O's table has `oil_d126` = -(126-session log change of Brent) with the prior "dearer oil worsens euro-area terms of
  trade" and 55-58 %. That sign is adopted for all three Brent signals and for the gas signals; it was not re-fitted.
* `bei_d63` has a weak prior (the opposite story is as respectable); `sent_lvl_diff` is long 81 % of the time because Michigan
  sentiment has sat below its own history since 2008 far more than the ESI has: by construction a regime bet.

## 3. Reconciliation of the agreement rule
Rebuilt with `selective.load_data`, `make_ctx`, `build_targets` and `house_score_wf` (walk-forward house score), agreement =
sign(cot_z52) = sign(d_spread2y_20) = sign(house score), evaluated with `selective.weekly_idx` / `seq_idx` / `cell_stats`. Every
accuracy and every n equals arm N's report; the weekly-tranche book of the 21-session rule has net Sharpe 0.52 / 0.51 / 0.43, also
identical. The agreement rule itself makes 9.3 non-overlapping decisions a year at 21 sessions and 5.3 at 42, so "at least 6 a year"
cannot hold at 42 sessions for ANY rule that only removes calls; the count is judged at 21 sessions and printed everywhere.

| decisions   | period   | arm N report (10 / 21 / 42 / 63 s)        | rebuilt here                              | identical   | decisions / yr            |
|:------------|:---------|:------------------------------------------|:------------------------------------------|:------------|:--------------------------|
| nonoverlap  | 2010-26  | 56 n=291 / 59 n=156 / 61 n=89 / 72 n=61   | 56 n=291 / 59 n=156 / 61 n=89 / 72 n=61   | True        | 17.3 / 9.3 / 5.3 / 3.7    |
| nonoverlap  | 2016-26  | 53 n=178 / 57 n=96 / 59 n=56 / 71 n=38    | 53 n=178 / 57 n=96 / 59 n=56 / 71 n=38    | True        | 16.5 / 8.9 / 5.2 / 3.6    |
| nonoverlap  | 2023-26  | 54 n=63 / 60 n=35 / 45 n=20 / 50 n=14     | 54 n=63 / 60 n=35 / 45 n=20 / 50 n=14     | True        | 16.6 / 9.3 / 5.4 / 3.9    |
| weekly      | 2010-26  | 57 n=390 / 59 n=387 / 65 n=383 / 67 n=383 | 57 n=390 / 59 n=387 / 65 n=383 / 67 n=383 | True        | 23.2 / 23.1 / 23.0 / 23.1 |
| weekly      | 2016-26  | 55 n=246 / 57 n=243 / 63 n=239 / 67 n=239 | 55 n=246 / 57 n=243 / 63 n=239 / 67 n=239 | True        | 22.8 / 22.6 / 22.4 / 22.6 |
| weekly      | 2023-26  | 57 n=80 / 55 n=77 / 47 n=73 / 53 n=73     | 57 n=80 / 55 n=77 / 47 n=73 / 53 n=73     | True        | 21.1 / 20.6 / 19.9 / 20.4 |

## 4. Standalone accuracy of each signal (direction = sign of the oriented signal)
One decision whenever the signal is non-zero: weekly grid (every 5th session, overlapping holds; no interval shown because the
overlap makes a plain one meaningless) and the greedy non-overlapping stream (plain Wilson 95 %). The up-base rate is 48-52 % in every
period, so 50 % is the mark to beat. `ttf_hh_d63` exists from 2018 only (its 2010-26 and 2016-26 rows are the same 8.8 years);
`cli_d6m_diff` ends in May 2024.

*2010-26* (accuracy % [Wilson 95 %] n)

| signal         | non-overlapping 21 s   | non-overlapping 42 s   | non-overlapping 63 s   | weekly 21 s   | weekly 42 s   | weekly 63 s   |
|:---------------|:-----------------------|:-----------------------|:-----------------------|:--------------|:--------------|:--------------|
| brent_eur_d63  | 48 [41-55] n=208       | 51 [41-60] n=104       | 58 [46-69] n=69        | 51 n=870      | 55 n=866      | 53 n=862      |
| brent_eur_d126 | 53 [47-60] n=208       | 53 [43-62] n=104       | 64 [52-74] n=69        | 53 n=870      | 53 n=866      | 55 n=862      |
| brent_usd_d126 | 55 [48-61] n=208       | 57 [47-66] n=104       | 68 [56-78] n=69        | 56 n=869      | 56 n=865      | 58 n=861      |
| gasratio_d3m   | 52 [46-59] n=208       | 53 [43-62] n=104       | 49 [38-61] n=69        | 53 n=870      | 51 n=866      | 49 n=862      |
| ttf_hh_d63     | 57 [48-66] n=108       | 59 [46-71] n=54        | 47 [32-63] n=36        | 55 n=452      | 60 n=448      | 59 n=444      |
| ea_tb_mom      | 56 [49-62] n=208       | 53 [43-62] n=104       | 59 [48-70] n=69        | 52 n=870      | 51 n=866      | 51 n=862      |
| cli_d6m_diff   | 52 [45-59] n=179       | 48 [38-58] n=90        | 48 [36-61] n=60        | 54 n=748      | 52 n=748      | 50 n=748      |
| sent_lvl_diff  | 44 [38-51] n=208       | 42 [33-52] n=104       | 46 [35-58] n=69        | 48 n=870      | 45 n=866      | 47 n=862      |
| sent_d3m_diff  | 45 [39-52] n=208       | 50 [41-59] n=104       | 51 [39-62] n=69        | 50 n=870      | 49 n=866      | 48 n=862      |
| tips_d21       | 50 [43-57] n=207       | 47 [38-57] n=104       | 48 [36-59] n=69        | 49 n=847      | 46 n=843      | 47 n=839      |
| tips_d63       | 46 [40-53] n=207       | 53 [43-62] n=104       | 52 [41-64] n=69        | 47 n=858      | 47 n=854      | 49 n=850      |
| bei_d63        | 51 [44-57] n=207       | 41 [32-51] n=104       | 48 [36-59] n=69        | 48 n=851      | 49 n=847      | 51 n=844      |

*2016-26* (accuracy % [Wilson 95 %] n)

| signal         | non-overlapping 21 s   | non-overlapping 42 s   | non-overlapping 63 s   | weekly 21 s   | weekly 42 s   | weekly 63 s   |
|:---------------|:-----------------------|:-----------------------|:-----------------------|:--------------|:--------------|:--------------|
| brent_eur_d63  | 48 [40-57] n=133       | 53 [41-65] n=66        | 57 [42-70] n=44        | 56 n=559      | 60 n=555      | 59 n=551      |
| brent_eur_d126 | 54 [46-62] n=133       | 61 [49-71] n=66        | 70 [56-82] n=44        | 56 n=559      | 58 n=555      | 60 n=551      |
| brent_usd_d126 | 55 [46-63] n=133       | 61 [49-71] n=66        | 73 [58-84] n=44        | 58 n=558      | 59 n=554      | 60 n=550      |
| gasratio_d3m   | 48 [40-57] n=133       | 50 [38-62] n=66        | 50 [36-64] n=44        | 51 n=559      | 49 n=555      | 49 n=551      |
| ttf_hh_d63     | 57 [48-66] n=108       | 59 [46-71] n=54        | 47 [32-63] n=36        | 55 n=452      | 60 n=448      | 59 n=444      |
| ea_tb_mom      | 53 [45-62] n=133       | 56 [44-67] n=66        | 64 [49-76] n=44        | 53 n=559      | 54 n=555      | 55 n=551      |
| cli_d6m_diff   | 52 [42-61] n=104       | 48 [35-61] n=52        | 46 [30-62] n=35        | 52 n=437      | 49 n=437      | 47 n=437      |
| sent_lvl_diff  | 47 [39-56] n=133       | 44 [33-56] n=66        | 52 [38-66] n=44        | 51 n=559      | 46 n=555      | 49 n=551      |
| sent_d3m_diff  | 48 [40-57] n=133       | 50 [38-62] n=66        | 57 [42-70] n=44        | 51 n=559      | 49 n=555      | 46 n=551      |
| tips_d21       | 48 [39-56] n=132       | 42 [31-54] n=66        | 45 [32-60] n=44        | 49 n=546      | 43 n=542      | 46 n=538      |
| tips_d63       | 47 [39-55] n=132       | 53 [41-65] n=66        | 57 [42-70] n=44        | 46 n=549      | 47 n=545      | 49 n=541      |
| bei_d63        | 49 [41-57] n=133       | 40 [29-52] n=67        | 45 [32-60] n=44        | 47 n=544      | 46 n=540      | 50 n=537      |

*2023-26* (accuracy % [Wilson 95 %] n)

| signal         | non-overlapping 21 s   | non-overlapping 42 s   | non-overlapping 63 s   | weekly 21 s   | weekly 42 s   | weekly 63 s   |
|:---------------|:-----------------------|:-----------------------|:-----------------------|:--------------|:--------------|:--------------|
| brent_eur_d63  | 45 [31-59] n=47        | 52 [33-71] n=23        | 53 [30-75] n=15        | 53 n=195      | 51 n=191      | 45 n=187      |
| brent_eur_d126 | 45 [31-59] n=47        | 57 [37-74] n=23        | 73 [48-89] n=15        | 52 n=195      | 48 n=191      | 50 n=187      |
| brent_usd_d126 | 47 [33-61] n=47        | 61 [41-78] n=23        | 80 [55-93] n=15        | 53 n=195      | 50 n=191      | 52 n=187      |
| gasratio_d3m   | 57 [43-70] n=47        | 57 [37-74] n=23        | 53 [30-75] n=15        | 57 n=195      | 55 n=191      | 57 n=187      |
| ttf_hh_d63     | 52 [38-66] n=46        | 74 [54-87] n=23        | 47 [25-70] n=15        | 53 n=195      | 61 n=191      | 60 n=187      |
| ea_tb_mom      | 53 [39-67] n=47        | 48 [29-67] n=23        | 67 [42-85] n=15        | 54 n=195      | 51 n=191      | 61 n=187      |
| cli_d6m_diff   | 44 [25-66] n=18        | 44 [19-73] n=9         | 33 [10-70] n=6         | 55 n=73       | 48 n=73       | 40 n=73       |
| sent_lvl_diff  | 51 [37-65] n=47        | 52 [33-71] n=23        | 67 [42-85] n=15        | 52 n=195      | 52 n=191      | 53 n=187      |
| sent_d3m_diff  | 51 [37-65] n=47        | 57 [37-74] n=23        | 60 [36-80] n=15        | 55 n=195      | 58 n=191      | 47 n=187      |
| tips_d21       | 46 [32-60] n=46        | 35 [19-55] n=23        | 53 [30-75] n=15        | 49 n=191      | 43 n=187      | 49 n=183      |
| tips_d63       | 52 [38-66] n=46        | 57 [37-74] n=23        | 47 [25-70] n=15        | 49 n=192      | 46 n=188      | 47 n=184      |
| bei_d63        | 50 [36-64] n=46        | 39 [22-59] n=23        | 47 [25-70] n=15        | 44 n=188      | 48 n=184      | 50 n=181      |

## 5. As an extra vote
(a) AND rule = the agreement rule speaks and the sign of the new signal equals its direction. (b) OUTSIDE = direction of the new
signal on sessions where the three old signals do not agree. (c) paired differences on the weekly grid with a circular block
bootstrap (block 2h/5 weeks, 2000 draws, the same blocks for both rules); the baseline in (c) is the agreement rule restricted to
the sessions where the signal exists, so a signal with a short history is compared like for like. The gains printed in (a) are
against the agreement rule on the WHOLE period, which is what the bar asks for.

**(a) AND rule, non-overlapping decisions, 2010-26** (accuracy % [Wilson] n (decisions / year), then the gain in points over the agreement rule)

| signal               | 21 s                          | 42 s                         | 63 s                          |
|:---------------------|:------------------------------|:-----------------------------|:------------------------------|
| agreement rule alone | 59 [51-66] n=156 (9.3/y)      | 61 [50-70] n=89 (5.3/y)      | 72 [60-82] n=61 (3.7/y)       |
| brent_eur_d63        | 54 [45-62] n=119 (7.1/y) -5.2 | 63 [52-73] n=73 (4.4/y) +2.3 | 66 [52-78] n=50 (3.0/y) -6.1  |
| brent_eur_d126       | 56 [47-65] n=117 (7.0/y) -2.6 | 59 [48-70] n=71 (4.3/y) -1.5 | 65 [51-76] n=51 (3.1/y) -7.4  |
| brent_usd_d126       | 55 [46-64] n=105 (6.3/y) -3.7 | 67 [55-77] n=64 (3.8/y) +6.5 | 70 [56-81] n=47 (2.8/y) -1.9  |
| gasratio_d3m         | 58 [48-67] n=106 (6.3/y) -1.4 | 62 [50-73] n=66 (4.0/y) +1.4 | 59 [45-72] n=49 (3.0/y) -12.9 |
| ttf_hh_d63           | 53 [40-65] n=59 (3.5/y) -6.4  | 62 [46-76] n=37 (2.2/y) +1.5 | 67 [48-81] n=27 (1.6/y) -5.5  |
| ea_tb_mom            | 55 [45-65] n=98 (5.8/y) -3.9  | 69 [56-79] n=61 (3.7/y) +8.2 | 59 [44-72] n=44 (2.7/y) -13.0 |
| cli_d6m_diff         | 60 [49-69] n=87 (5.2/y) +0.8  | 65 [51-76] n=51 (3.1/y) +4.0 | 68 [52-80] n=40 (2.4/y) -4.6  |
| sent_lvl_diff        | 57 [45-68] n=72 (4.3/y) -2.0  | 58 [43-71] n=45 (2.7/y) -2.9 | 70 [54-83] n=37 (2.2/y) -1.9  |
| sent_d3m_diff        | 49 [39-59] n=92 (5.5/y) -10.1 | 56 [43-67] n=63 (3.8/y) -5.1 | 70 [56-81] n=47 (2.8/y) -1.9  |
| tips_d21             | 58 [49-66] n=119 (7.1/y) -1.0 | 63 [52-73] n=76 (4.6/y) +2.5 | 66 [53-77] n=53 (3.2/y) -6.1  |
| tips_d63             | 51 [42-60] n=112 (6.7/y) -8.1 | 62 [50-73] n=66 (4.0/y) +1.4 | 59 [45-72] n=49 (3.0/y) -12.9 |
| bei_d63              | 50 [41-60] n=103 (6.1/y) -8.5 | 62 [49-72] n=65 (3.9/y) +0.9 | 68 [54-79] n=50 (3.0/y) -4.1  |

**(a) AND rule, non-overlapping decisions, 2016-26** (accuracy % [Wilson] n (decisions / year), then the gain in points over the agreement rule)

| signal               | 21 s                         | 42 s                         | 63 s                          |
|:---------------------|:-----------------------------|:-----------------------------|:------------------------------|
| agreement rule alone | 57 [47-67] n=96 (8.9/y)      | 59 [46-71] n=56 (5.2/y)      | 71 [55-83] n=38 (3.6/y)       |
| brent_eur_d63        | 58 [47-69] n=77 (7.2/y) +1.1 | 67 [53-78] n=48 (4.5/y) +7.7 | 69 [51-82] n=32 (3.0/y) -2.3  |
| brent_eur_d126       | 58 [47-69] n=77 (7.2/y) +1.1 | 57 [43-70] n=47 (4.4/y) -1.5 | 64 [47-78] n=33 (3.1/y) -7.4  |
| brent_usd_d126       | 57 [45-67] n=74 (6.9/y) -0.5 | 62 [48-75] n=45 (4.2/y) +3.3 | 66 [48-80] n=32 (3.0/y) -5.4  |
| gasratio_d3m         | 56 [44-68] n=62 (5.8/y) -0.8 | 62 [46-75] n=39 (3.7/y) +2.6 | 62 [44-77] n=29 (2.7/y) -9.0  |
| ttf_hh_d63           | 53 [40-65] n=59 (5.5/y) -4.7 | 62 [46-76] n=37 (3.5/y) +3.2 | 67 [48-81] n=27 (2.5/y) -4.4  |
| ea_tb_mom            | 55 [43-66] n=66 (6.1/y) -2.7 | 68 [53-80] n=41 (3.8/y) +9.4 | 62 [44-77] n=29 (2.7/y) -9.0  |
| cli_d6m_diff         | 60 [45-73] n=45 (4.2/y) +2.7 | 63 [44-78] n=27 (2.5/y) +4.0 | 62 [41-79] n=21 (2.0/y) -9.1  |
| sent_lvl_diff        | 62 [48-75] n=45 (4.2/y) +4.9 | 57 [39-73] n=30 (2.8/y) -2.3 | 75 [55-88] n=24 (2.3/y) +3.9  |
| sent_d3m_diff        | 50 [37-63] n=54 (5.0/y) -7.3 | 58 [42-72] n=38 (3.6/y) -1.0 | 71 [53-85] n=28 (2.6/y) +0.4  |
| tips_d21             | 61 [50-71] n=77 (7.2/y) +3.7 | 63 [49-75] n=49 (4.6/y) +4.3 | 56 [39-71] n=34 (3.2/y) -15.2 |
| tips_d63             | 51 [40-62] n=75 (7.0/y) -6.6 | 64 [49-76] n=44 (4.1/y) +4.7 | 53 [36-70] n=30 (2.8/y) -17.7 |
| bei_d63              | 48 [36-60] n=63 (5.9/y) -9.7 | 57 [42-71] n=40 (3.7/y) -1.4 | 66 [47-80] n=29 (2.7/y) -5.5  |

**(a) AND rule, non-overlapping decisions, 2023-26** (accuracy % [Wilson] n (decisions / year), then the gain in points over the agreement rule)

| signal               | 21 s                          | 42 s                          | 63 s                          |
|:---------------------|:------------------------------|:------------------------------|:------------------------------|
| agreement rule alone | 60 [44-74] n=35 (9.3/y)       | 45 [26-66] n=20 (5.4/y)       | 50 [27-73] n=14 (3.9/y)       |
| brent_eur_d63        | 54 [36-70] n=28 (7.4/y) -6.4  | 56 [33-77] n=16 (4.3/y) +11.2 | 45 [21-72] n=11 (3.1/y) -4.5  |
| brent_eur_d126       | 52 [34-69] n=29 (7.7/y) -8.3  | 37 [19-59] n=19 (5.2/y) -8.2  | 42 [19-68] n=12 (3.3/y) -8.3  |
| brent_usd_d126       | 46 [29-65] n=26 (6.9/y) -13.8 | 41 [22-64] n=17 (4.6/y) -3.8  | 45 [21-72] n=11 (3.1/y) -4.5  |
| gasratio_d3m         | 60 [41-77] n=25 (6.6/y) +0.0  | 62 [36-82] n=13 (3.5/y) +16.5 | 55 [28-79] n=11 (3.1/y) +4.5  |
| ttf_hh_d63           | 46 [28-65] n=24 (6.4/y) -14.2 | 47 [25-70] n=15 (4.1/y) +1.7  | 60 [31-83] n=10 (2.8/y) +10.0 |
| ea_tb_mom            | 58 [39-76] n=24 (6.4/y) -1.7  | 62 [39-82] n=16 (4.3/y) +17.5 | 64 [35-85] n=11 (3.1/y) +13.6 |
| cli_d6m_diff         | 50 [24-76] n=10 (2.7/y) -10.0 | 50 [19-81] n=6 (1.6/y) +5.0   | 20 [4-62] n=5 (1.4/y) -30.0   |
| sent_lvl_diff        | 71 [47-87] n=17 (4.5/y) +10.6 | 45 [21-72] n=11 (3.0/y) +0.5  | 56 [27-81] n=9 (2.5/y) +5.6   |
| sent_d3m_diff        | 48 [29-67] n=23 (6.1/y) -12.2 | 60 [36-80] n=15 (4.1/y) +15.0 | 60 [31-83] n=10 (2.8/y) +10.0 |
| tips_d21             | 50 [33-67] n=30 (8.0/y) -10.0 | 47 [27-68] n=19 (5.2/y) +2.4  | 33 [14-61] n=12 (3.3/y) -16.7 |
| tips_d63             | 48 [31-66] n=29 (7.7/y) -11.7 | 56 [33-77] n=16 (4.3/y) +11.2 | 45 [21-72] n=11 (3.1/y) -4.5  |
| bei_d63              | 38 [21-59] n=21 (5.6/y) -21.9 | 58 [32-81] n=12 (3.3/y) +13.3 | 33 [12-65] n=9 (2.5/y) -16.7  |

**(a') weekly decisions, 2010-26**: the agreement rule on the sessions where the signal exists / calls the signal confirms (= AND rule) / calls it contradicts

| signal         | 21 s: same span / confirmed / contradicted   | 42 s: same span / confirmed / contradicted   | 63 s: same span / confirmed / contradicted   |
|:---------------|:---------------------------------------------|:---------------------------------------------|:---------------------------------------------|
| brent_eur_d63  | 59 n=387 / 59 n=248 / 60 n=139               | 65 n=383 / 70 n=244 / 56 n=139               | 67 n=383 / 70 n=244 / 60 n=139               |
| brent_eur_d126 | 59 n=387 / 61 n=259 / 56 n=128               | 65 n=383 / 64 n=256 / 65 n=127               | 67 n=383 / 68 n=256 / 64 n=127               |
| brent_usd_d126 | 59 n=387 / 65 n=234 / 52 n=153               | 65 n=383 / 68 n=231 / 60 n=152               | 67 n=383 / 71 n=231 / 59 n=152               |
| gasratio_d3m   | 59 n=387 / 61 n=248 / 56 n=139               | 65 n=383 / 67 n=245 / 62 n=138               | 67 n=383 / 64 n=245 / 71 n=138               |
| ttf_hh_d63     | 56 n=200 / 63 n=123 / 45 n=77                | 62 n=196 / 74 n=119 / 44 n=77                | 65 n=196 / 75 n=119 / 49 n=77                |
| ea_tb_mom      | 59 n=387 / 65 n=207 / 53 n=180               | 65 n=383 / 65 n=203 / 65 n=180               | 67 n=383 / 67 n=203 / 66 n=180               |
| cli_d6m_diff   | 58 n=337 / 60 n=210 / 56 n=127               | 66 n=337 / 64 n=210 / 69 n=127               | 68 n=337 / 65 n=210 / 73 n=127               |
| sent_lvl_diff  | 59 n=387 / 57 n=152 / 61 n=235               | 65 n=383 / 55 n=152 / 71 n=231               | 67 n=383 / 57 n=152 / 73 n=231               |
| sent_d3m_diff  | 59 n=387 / 60 n=187 / 59 n=200               | 65 n=383 / 64 n=183 / 66 n=200               | 67 n=383 / 60 n=183 / 72 n=200               |
| tips_d21       | 60 n=376 / 57 n=235 / 63 n=141               | 65 n=372 / 61 n=231 / 70 n=141               | 66 n=372 / 65 n=231 / 69 n=141               |
| tips_d63       | 59 n=379 / 56 n=236 / 66 n=143               | 65 n=375 / 61 n=232 / 71 n=143               | 67 n=375 / 65 n=232 / 70 n=143               |
| bei_d63        | 59 n=379 / 56 n=174 / 61 n=205               | 65 n=375 / 62 n=174 / 67 n=201               | 66 n=375 / 67 n=174 / 66 n=201               |

**(a') weekly decisions, 2016-26**: the agreement rule on the sessions where the signal exists / calls the signal confirms (= AND rule) / calls it contradicts

| signal         | 21 s: same span / confirmed / contradicted   | 42 s: same span / confirmed / contradicted   | 63 s: same span / confirmed / contradicted   |
|:---------------|:---------------------------------------------|:---------------------------------------------|:---------------------------------------------|
| brent_eur_d63  | 57 n=243 / 61 n=168 / 48 n=75                | 63 n=239 / 71 n=164 / 45 n=75                | 67 n=239 / 73 n=164 / 53 n=75                |
| brent_eur_d126 | 57 n=243 / 61 n=180 / 46 n=63                | 63 n=239 / 67 n=177 / 52 n=62                | 67 n=239 / 71 n=177 / 55 n=62                |
| brent_usd_d126 | 57 n=243 / 61 n=172 / 48 n=71                | 63 n=239 / 67 n=169 / 53 n=70                | 67 n=239 / 71 n=169 / 57 n=70                |
| gasratio_d3m   | 57 n=243 / 61 n=145 / 52 n=98                | 63 n=239 / 69 n=142 / 55 n=97                | 67 n=239 / 66 n=142 / 68 n=97                |
| ttf_hh_d63     | 56 n=200 / 63 n=123 / 45 n=77                | 62 n=196 / 74 n=119 / 44 n=77                | 65 n=196 / 75 n=119 / 49 n=77                |
| ea_tb_mom      | 57 n=243 / 62 n=151 / 49 n=92                | 63 n=239 / 65 n=147 / 60 n=92                | 67 n=239 / 70 n=147 / 62 n=92                |
| cli_d6m_diff   | 55 n=193 / 56 n=108 / 54 n=85                | 65 n=193 / 61 n=108 / 69 n=85                | 70 n=193 / 63 n=108 / 79 n=85                |
| sent_lvl_diff  | 57 n=243 / 57 n=92 / 58 n=151                | 63 n=239 / 52 n=92 / 70 n=147                | 67 n=239 / 58 n=92 / 73 n=147                |
| sent_d3m_diff  | 57 n=243 / 59 n=101 / 56 n=142               | 63 n=239 / 66 n=97 / 61 n=142                | 67 n=239 / 60 n=97 / 72 n=142                |
| tips_d21       | 57 n=237 / 55 n=160 / 62 n=77                | 64 n=233 / 57 n=156 / 77 n=77                | 67 n=233 / 62 n=156 / 75 n=77                |
| tips_d63       | 57 n=237 / 53 n=169 / 69 n=68                | 64 n=233 / 59 n=165 / 76 n=68                | 67 n=233 / 65 n=165 / 72 n=68                |
| bei_d63        | 56 n=239 / 53 n=99 / 59 n=140                | 63 n=235 / 59 n=99 / 67 n=136                | 67 n=235 / 68 n=99 / 66 n=136                |

**(b) calls of the signal when the three old signals do NOT agree, 2010-26**

| signal         | non-overlapping 21 s      | non-overlapping 42 s    | non-overlapping 63 s    | weekly 21 s   | weekly 42 s   | weekly 63 s   |
|:---------------|:--------------------------|:------------------------|:------------------------|:--------------|:--------------|:--------------|
| brent_eur_d63  | 51 [43-58] n=170 (10.1/y) | 47 [37-57] n=93 (5.6/y) | 53 [41-65] n=64 (3.9/y) | 51 n=483      | 51 n=483      | 49 n=479      |
| brent_eur_d126 | 55 [48-63] n=170 (10.1/y) | 54 [44-64] n=93 (5.6/y) | 55 [43-66] n=64 (3.9/y) | 51 n=483      | 52 n=483      | 54 n=479      |
| brent_usd_d126 | 55 [48-63] n=170 (10.1/y) | 56 [46-66] n=93 (5.6/y) | 56 [44-68] n=64 (3.9/y) | 55 n=482      | 56 n=482      | 56 n=478      |
| gasratio_d3m   | 55 [48-63] n=170 (10.1/y) | 53 [43-63] n=93 (5.6/y) | 48 [37-60] n=64 (3.9/y) | 52 n=483      | 47 n=483      | 47 n=479      |
| ttf_hh_d63     | 51 [41-61] n=86 (5.1/y)   | 49 [36-63] n=49 (2.9/y) | 48 [33-65] n=33 (2.0/y) | 51 n=252      | 54 n=252      | 54 n=248      |
| ea_tb_mom      | 51 [44-59] n=170 (10.1/y) | 54 [44-64] n=93 (5.6/y) | 55 [43-66] n=64 (3.9/y) | 49 n=483      | 51 n=483      | 50 n=479      |
| cli_d6m_diff   | 54 [46-62] n=145 (8.7/y)  | 54 [43-64] n=80 (4.8/y) | 48 [36-61] n=56 (3.4/y) | 54 n=411      | 52 n=411      | 50 n=411      |
| sent_lvl_diff  | 42 [35-50] n=170 (10.1/y) | 42 [32-52] n=93 (5.6/y) | 52 [40-63] n=64 (3.9/y) | 49 n=483      | 50 n=483      | 54 n=479      |
| sent_d3m_diff  | 48 [40-55] n=170 (10.1/y) | 49 [40-59] n=93 (5.6/y) | 47 [35-59] n=64 (3.9/y) | 50 n=483      | 50 n=483      | 52 n=479      |
| tips_d21       | 48 [41-55] n=169 (10.1/y) | 58 [47-67] n=92 (5.5/y) | 45 [34-57] n=64 (3.9/y) | 48 n=471      | 43 n=471      | 44 n=467      |
| tips_d63       | 46 [39-53] n=170 (10.1/y) | 51 [41-60] n=93 (5.6/y) | 47 [35-59] n=64 (3.9/y) | 47 n=479      | 46 n=479      | 48 n=475      |
| bei_d63        | 44 [37-52] n=170 (10.1/y) | 47 [37-57] n=93 (5.6/y) | 48 [37-60] n=64 (3.9/y) | 49 n=472      | 52 n=472      | 53 n=469      |

**(b) calls of the signal when the three old signals do NOT agree, 2016-26**

| signal         | non-overlapping 21 s      | non-overlapping 42 s    | non-overlapping 63 s    | weekly 21 s   | weekly 42 s   | weekly 63 s   |
|:---------------|:--------------------------|:------------------------|:------------------------|:--------------|:--------------|:--------------|
| brent_eur_d63  | 56 [47-65] n=109 (10.1/y) | 48 [36-61] n=60 (5.6/y) | 59 [43-72] n=41 (3.9/y) | 53 n=316      | 56 n=316      | 54 n=312      |
| brent_eur_d126 | 58 [48-67] n=109 (10.1/y) | 52 [39-64] n=60 (5.6/y) | 56 [41-70] n=41 (3.9/y) | 54 n=316      | 55 n=316      | 57 n=312      |
| brent_usd_d126 | 57 [48-66] n=109 (10.1/y) | 52 [39-64] n=60 (5.6/y) | 56 [41-70] n=41 (3.9/y) | 57 n=315      | 57 n=315      | 58 n=311      |
| gasratio_d3m   | 52 [43-61] n=109 (10.1/y) | 47 [35-59] n=60 (5.6/y) | 54 [39-68] n=41 (3.9/y) | 48 n=316      | 42 n=316      | 46 n=312      |
| ttf_hh_d63     | 51 [41-61] n=86 (8.0/y)   | 49 [36-63] n=49 (4.6/y) | 48 [33-65] n=33 (3.1/y) | 51 n=252      | 54 n=252      | 54 n=248      |
| ea_tb_mom      | 53 [44-62] n=109 (10.1/y) | 57 [44-68] n=60 (5.6/y) | 61 [46-74] n=41 (3.9/y) | 48 n=316      | 52 n=316      | 53 n=312      |
| cli_d6m_diff   | 51 [41-62] n=84 (7.8/y)   | 51 [37-65] n=47 (4.4/y) | 39 [25-56] n=33 (3.1/y) | 52 n=244      | 51 n=244      | 50 n=244      |
| sent_lvl_diff  | 46 [37-55] n=109 (10.1/y) | 40 [29-53] n=60 (5.6/y) | 56 [41-70] n=41 (3.9/y) | 53 n=316      | 51 n=316      | 56 n=312      |
| sent_d3m_diff  | 50 [41-60] n=109 (10.1/y) | 50 [38-62] n=60 (5.6/y) | 51 [36-66] n=41 (3.9/y) | 51 n=316      | 49 n=316      | 51 n=312      |
| tips_d21       | 49 [40-58] n=108 (10.0/y) | 47 [35-60] n=59 (5.5/y) | 49 [34-64] n=41 (3.9/y) | 49 n=309      | 41 n=309      | 43 n=305      |
| tips_d63       | 46 [37-55] n=109 (10.1/y) | 50 [38-62] n=60 (5.6/y) | 44 [30-59] n=41 (3.9/y) | 46 n=312      | 46 n=312      | 45 n=308      |
| bei_d63        | 45 [36-54] n=109 (10.1/y) | 47 [35-59] n=60 (5.6/y) | 49 [34-64] n=41 (3.9/y) | 47 n=305      | 48 n=305      | 51 n=302      |

**(b) calls of the signal when the three old signals do NOT agree, 2023-26**

| signal         | non-overlapping 21 s     | non-overlapping 42 s    | non-overlapping 63 s    | weekly 21 s   | weekly 42 s   | weekly 63 s   |
|:---------------|:-------------------------|:------------------------|:------------------------|:--------------|:--------------|:--------------|
| brent_eur_d63  | 53 [37-68] n=38 (10.1/y) | 43 [24-63] n=21 (5.7/y) | 43 [21-67] n=14 (3.9/y) | 55 n=118      | 53 n=118      | 48 n=114      |
| brent_eur_d126 | 53 [37-68] n=38 (10.1/y) | 38 [21-59] n=21 (5.7/y) | 57 [33-79] n=14 (3.9/y) | 55 n=118      | 53 n=118      | 51 n=114      |
| brent_usd_d126 | 53 [37-68] n=38 (10.1/y) | 43 [24-63] n=21 (5.7/y) | 57 [33-79] n=14 (3.9/y) | 58 n=118      | 58 n=118      | 55 n=114      |
| gasratio_d3m   | 61 [45-74] n=38 (10.1/y) | 62 [41-79] n=21 (5.7/y) | 79 [52-92] n=14 (3.9/y) | 55 n=118      | 48 n=118      | 55 n=114      |
| ttf_hh_d63     | 53 [37-68] n=38 (10.1/y) | 48 [28-68] n=21 (5.7/y) | 50 [27-73] n=14 (3.9/y) | 50 n=118      | 58 n=118      | 63 n=114      |
| ea_tb_mom      | 50 [35-65] n=38 (10.1/y) | 52 [32-72] n=21 (5.7/y) | 64 [39-84] n=14 (3.9/y) | 43 n=118      | 47 n=118      | 54 n=114      |
| cli_d6m_diff   | 54 [29-77] n=13 (3.5/y)  | 38 [14-69] n=8 (2.2/y)  | 17 [3-56] n=6 (1.7/y)   | 59 n=46       | 50 n=46       | 41 n=46       |
| sent_lvl_diff  | 53 [37-68] n=38 (10.1/y) | 48 [28-68] n=21 (5.7/y) | 50 [27-73] n=14 (3.9/y) | 57 n=118      | 60 n=118      | 56 n=114      |
| sent_d3m_diff  | 58 [42-72] n=38 (10.1/y) | 57 [37-76] n=21 (5.7/y) | 50 [27-73] n=14 (3.9/y) | 60 n=118      | 55 n=118      | 47 n=114      |
| tips_d21       | 46 [31-62] n=37 (9.8/y)  | 70 [48-85] n=20 (5.4/y) | 64 [39-84] n=14 (3.9/y) | 52 n=116      | 46 n=116      | 47 n=112      |
| tips_d63       | 50 [35-65] n=38 (10.1/y) | 57 [37-76] n=21 (5.7/y) | 29 [12-55] n=14 (3.9/y) | 49 n=116      | 53 n=116      | 41 n=112      |
| bei_d63        | 42 [28-58] n=38 (10.1/y) | 57 [37-76] n=21 (5.7/y) | 36 [16-61] n=14 (3.9/y) | 40 n=111      | 48 n=111      | 50 n=108      |

**(c) paired difference, weekly grid: accuracy(AND rule) - accuracy(agreement rule on the same sessions), points [bootstrap 95 %]**

| signal         | 2010-26 21 s   | 2010-26 42 s   | 2010-26 63 s   | 2016-26 21 s   | 2016-26 42 s   | 2016-26 63 s   | 2023-26 21 s   | 2023-26 42 s   | 2023-26 63 s   |
|:---------------|:---------------|:---------------|:---------------|:---------------|:---------------|:---------------|:---------------|:---------------|:---------------|
| brent_eur_d63  | -0 [-6,+5]     | +5 [-1,+10]    | +4 [-2,+9]     | +4 [-2,+10]    | +8 [+2,+15]    | +6 [-1,+12]    | -1 [-12,+11]   | -1 [-17,+12]   | -8 [-23,+3]    |
| brent_eur_d126 | +2 [-4,+7]     | -0 [-6,+5]     | +1 [-5,+6]     | +4 [-1,+10]    | +4 [-2,+11]    | +4 [-3,+10]    | -4 [-14,+5]    | -6 [-20,+5]    | -2 [-20,+7]    |
| brent_usd_d126 | +5 [-1,+11]    | +3 [-3,+9]     | +5 [-2,+11]    | +4 [-2,+10]    | +4 [-2,+11]    | +4 [-4,+10]    | -4 [-16,+6]    | -9 [-27,+4]    | -3 [-27,+8]    |
| gasratio_d3m   | +2 [-4,+7]     | +2 [-4,+8]     | -2 [-9,+4]     | +3 [-4,+10]    | +6 [-3,+15]    | -1 [-10,+7]    | +7 [-5,+21]    | +15 [+3,+34]   | +8 [-6,+24]    |
| ttf_hh_d63     | +7 [-1,+14]    | +12 [+3,+21]   | +10 [+3,+17]   | +7 [-0,+14]    | +12 [+3,+20]   | +10 [+3,+17]   | +8 [-6,+24]    | +15 [-3,+34]   | +5 [-8,+22]    |
| ea_tb_mom      | +5 [-1,+11]    | -0 [-8,+7]     | +0 [-9,+8]     | +5 [-1,+12]    | +2 [-8,+10]    | +3 [-8,+12]    | +20 [+7,+35]   | +9 [-15,+27]   | +22 [+5,+33]   |
| cli_d6m_diff   | +2 [-4,+7]     | -2 [-9,+4]     | -3 [-11,+4]    | +1 [-8,+8]     | -4 [-14,+5]    | -7 [-18,+3]    | +5 [-5,+23]    | +4 [-3,+17]    | -9 [-27,+3]    |
| sent_lvl_diff  | -3 [-12,+6]    | -10 [-22,+0]   | -10 [-22,+1]   | -1 [-12,+10]   | -11 [-25,+2]   | -9 [-25,+6]    | -5 [-23,+15]   | -10 [-32,+7]   | -1 [-23,+23]   |
| sent_d3m_diff  | +0 [-6,+7]     | -1 [-8,+6]     | -6 [-15,+1]    | +2 [-10,+12]   | +3 [-7,+12]    | -7 [-18,+3]    | -2 [-16,+11]   | +11 [-1,+25]   | -3 [-16,+12]   |
| tips_d21       | -2 [-7,+2]     | -3 [-8,+2]     | -2 [-7,+4]     | -2 [-8,+3]     | -6 [-12,-1]    | -4 [-11,+1]    | -6 [-13,-0]    | -6 [-16,-0]    | +1 [-6,+7]     |
| tips_d63       | -4 [-9,+1]     | -4 [-11,+3]    | -2 [-9,+4]     | -5 [-10,+0]    | -5 [-12,+1]    | -2 [-8,+4]     | -2 [-8,+3]     | -7 [-14,-2]    | +2 [-6,+10]    |
| bei_d63        | -3 [-9,+5]     | -3 [-10,+5]    | +0 [-8,+9]     | -4 [-13,+6]    | -5 [-14,+4]    | +1 [-9,+11]    | +3 [-18,+23]   | -4 [-23,+18]   | +0 [-19,+26]   |

**(c') accuracy(agreement calls the signal confirms) - accuracy(agreement calls it contradicts), points [bootstrap 95 %]**

| signal         | 2010-26 21 s   | 2010-26 42 s   | 2010-26 63 s   | 2016-26 21 s   | 2016-26 42 s   | 2016-26 63 s   | 2023-26 21 s   | 2023-26 42 s   | 2023-26 63 s   |
|:---------------|:---------------|:---------------|:---------------|:---------------|:---------------|:---------------|:---------------|:---------------|:---------------|
| brent_eur_d63  | -0 [-15,+14]   | +14 [-1,+28]   | +10 [-5,+25]   | +13 [-5,+31]   | +26 [+6,+45]   | +20 [-2,+39]   | -2 [-33,+37]   | -2 [-39,+41]   | -22 [-51,+11]  |
| brent_eur_d126 | +5 [-11,+20]   | -1 [-18,+17]   | +4 [-13,+22]   | +15 [-5,+35]   | +16 [-8,+41]   | +16 [-9,+44]   | -14 [-50,+28]  | -22 [-62,+24]  | -6 [-48,+44]   |
| brent_usd_d126 | +13 [-2,+27]   | +8 [-8,+24]    | +12 [-5,+30]   | +13 [-6,+33]   | +15 [-7,+38]   | +14 [-11,+40]  | -12 [-43,+27]  | -27 [-63,+16]  | -11 [-55,+37]  |
| gasratio_d3m   | +5 [-10,+20]   | +5 [-12,+23]   | -7 [-24,+11]   | +9 [-9,+25]    | +14 [-7,+35]   | -2 [-24,+18]   | +18 [-15,+46]  | +37 [+11,+63]  | +20 [-19,+53]  |
| ttf_hh_d63     | +17 [-1,+36]   | +30 [+9,+51]   | +25 [+8,+41]   | +17 [-1,+36]   | +30 [+8,+50]   | +25 [+8,+41]   | +17 [-12,+47]  | +29 [-6,+63]   | +10 [-16,+40]  |
| ea_tb_mom      | +11 [-1,+25]   | -0 [-16,+16]   | +1 [-18,+19]   | +13 [-4,+31]   | +6 [-17,+28]   | +8 [-17,+34]   | +43 [+17,+66]  | +18 [-23,+56]  | +43 [+8,+66]   |
| cli_d6m_diff   | +4 [-10,+18]   | -4 [-20,+13]   | -8 [-25,+12]   | +1 [-16,+20]   | -8 [-27,+13]   | -16 [-37,+8]   | +21 [-28,+64]  | +17 [-18,+53]  | -40 [-80,+44]  |
| sent_lvl_diff  | -5 [-19,+10]   | -17 [-34,+0]   | -17 [-34,+1]   | -1 [-18,+16]   | -18 [-38,+3]   | -15 [-37,+10]  | -9 [-42,+32]   | -20 [-56,+19]  | -2 [-44,+44]   |
| sent_d3m_diff  | +1 [-12,+14]   | -2 [-16,+12]   | -12 [-28,+1]   | +4 [-16,+21]   | +5 [-11,+20]   | -12 [-30,+5]   | -6 [-36,+27]   | +25 [-2,+49]   | -8 [-39,+24]   |
| tips_d21       | -6 [-18,+6]    | -9 [-22,+5]    | -4 [-19,+10]   | -7 [-23,+9]    | -20 [-34,-5]   | -13 [-31,+4]   | -26 [-53,-3]   | -29 [-54,-1]   | +3 [-34,+30]   |
| tips_d63       | -10 [-22,+3]   | -10 [-27,+7]   | -5 [-23,+12]   | -16 [-34,+1]   | -18 [-37,+2]   | -7 [-25,+15]   | -15 [-56,+23]  | -45 [-75,-17]  | +13 [-43,+49]  |
| bei_d63        | -5 [-17,+8]    | -5 [-19,+8]    | +0 [-16,+16]   | -7 [-23,+9]    | -8 [-24,+7]    | +2 [-15,+18]   | +5 [-25,+34]   | -7 [-34,+25]   | +1 [-30,+35]   |

Of the 108 paired intervals in (c), 12 exclude zero (8 positive, 4 negative); about 5 would by chance.

## 6. Selection by the declared rule and the record of the pick
Declared rule: highest LOWER Wilson bound of the 2010-2015 non-overlapping 21-session accuracy of the AND rule, among candidates with
at least 6 such decisions a year in 2010-2015. For reference the agreement rule alone in 2010-15: 61.7 % [49.0-72.9], n=60, 10.0 a
year - higher than every AND rule in the table.

| signal         |   n_2010-15 |   dec_per_year_2010-15 |   accuracy_2010-15 |   lo_2010-15 |   hi_2010-15 | eligible   | final   |
|:---------------|------------:|-----------------------:|-------------------:|-------------:|-------------:|:-----------|:--------|
| brent_eur_d63  |          42 |                    7   |               45.2 |         31.2 |         60.1 | True       | False   |
| brent_eur_d126 |          40 |                    6.7 |               52.5 |         37.5 |         67.1 | True       | False   |
| brent_usd_d126 |          31 |                    5.2 |               51.6 |         34.8 |         68   | False      | False   |
| gasratio_d3m   |          44 |                    7.3 |               59.1 |         44.4 |         72.3 | True       | False   |
| ttf_hh_d63     |           0 |                    0   |              nan   |        nan   |        nan   | False      | False   |
| ea_tb_mom      |          32 |                    5.3 |               56.2 |         39.3 |         71.8 | False      | False   |
| cli_d6m_diff   |          42 |                    7   |               59.5 |         44.5 |         73   | True       | True    |
| sent_lvl_diff  |          27 |                    4.5 |               48.1 |         30.7 |         66   | False      | False   |
| sent_d3m_diff  |          38 |                    6.3 |               47.4 |         32.5 |         62.7 | True       | False   |
| tips_d21       |          42 |                    7   |               52.4 |         37.7 |         66.6 | True       | False   |
| tips_d63       |          37 |                    6.2 |               51.4 |         35.9 |         66.6 | True       | False   |
| bei_d63        |          40 |                    6.7 |               55   |         39.8 |         69.3 | True       | False   |

**Final: `cli_d6m_diff`** (selected by the declared rule). Round-5 bar, cell by cell (non-overlapping decisions):

|   h | period   | agreement rule   | AND rule                |   gain pts | placebo +63     | placebo +126    |
|----:|:---------|:-----------------|:------------------------|-----------:|:----------------|:----------------|
|  21 | 2010-26  | 59 n=156 (9.3/y) | 60 [49-69] n=87 (5.2/y) |        0.8 | 51 n=79 (-8.3)  | 49 n=67 (-9.7)  |
|  21 | 2016-26  | 57 n=96 (8.9/y)  | 60 [45-73] n=45 (4.2/y) |        2.7 | 48 n=44 (-9.6)  | 49 n=43 (-8.5)  |
|  21 | 2023-26  | 60 n=35 (9.3/y)  | 50 [24-76] n=10 (2.7/y) |      -10   | 33 n=9 (-26.7)  | 56 n=9 (-4.4)   |
|  42 | 2010-26  | 61 n=89 (5.3/y)  | 65 [51-76] n=51 (3.1/y) |        4   | 55 n=47 (-5.4)  | 42 n=43 (-18.8) |
|  42 | 2016-26  | 59 n=56 (5.2/y)  | 63 [44-78] n=27 (2.5/y) |        4   | 52 n=27 (-7.1)  | 45 n=29 (-14.1) |
|  42 | 2023-26  | 45 n=20 (5.4/y)  | 50 [19-81] n=6 (1.6/y)  |        5   | 0 n=5 (-45.0)   | 50 n=6 (+5.0)   |
|  63 | 2010-26  | 72 n=61 (3.7/y)  | 68 [52-80] n=40 (2.4/y) |       -4.6 | 61 n=36 (-11.0) | 61 n=33 (-11.5) |
|  63 | 2016-26  | 71 n=38 (3.6/y)  | 62 [41-79] n=21 (2.0/y) |       -9.1 | 57 n=21 (-13.9) | 67 n=21 (-4.4)  |
|  63 | 2023-26  | 50 n=14 (3.9/y)  | 20 [4-62] n=5 (1.4/y)   |      -30   | 40 n=5 (-10.0)  | 75 n=4 (+25.0)  |

Bar components: gain_ok = False, count21_ok = False, count42_ok = False, not_worse_2023 = False, placebo_ok = True, met = False, met_strict_42_count = False

Hit rates of the final rule at 21 sessions (round-4 format; weekly interval = Wilson with Newey-West effective n):

| decisions   | period   |   n |   per year |   correct sign before costs % | interval   |   positive net P&L % |   net bp / decision |   avg win bp |   avg loss bp |   long share % |
|:------------|:---------|----:|-----------:|------------------------------:|:-----------|---------------------:|--------------------:|-------------:|--------------:|---------------:|
| weekly      | 2010-26  | 210 |       12.5 |                          60   | 50-70      |                 59.5 |                61.7 |          210 |          -156 |             34 |
| weekly      | 2016-26  | 108 |       10.1 |                          55.6 | 41-69      |                 55.6 |                39.6 |          163 |          -115 |             37 |
| weekly      | 2023-26  |  21 |        5.6 |                          38.1 | 15-68      |                 38.1 |               -26.7 |          172 |          -149 |             29 |
| nonoverlap  | 2010-26  |  87 |        5.2 |                          59.8 | 49-69      |                 59.8 |                65.6 |          219 |          -162 |             39 |
| nonoverlap  | 2016-26  |  45 |        4.2 |                          60   | 45-73      |                 60   |                40.8 |          152 |          -127 |             40 |
| nonoverlap  | 2023-26  |  10 |        2.7 |                          50   | 24-76      |                 50   |               -29.5 |          137 |          -196 |             30 |

Per year (weekly decisions by decision date; the agreement rule next to it):

|   year |   decisions |   long_share |   accuracy |   net_win_rate |   gross_bp |   net_bp |   avg_hold |   agree3_decisions |   agree3_accuracy |   book_sharpe |
|-------:|------------:|-------------:|-----------:|---------------:|-----------:|---------:|-----------:|-------------------:|------------------:|--------------:|
|   2010 |          26 |         0.35 |       0.65 |           0.62 |      83.86 |    82.07 |         21 |                 31 |              0.61 |          0.66 |
|   2011 |          28 |         0.39 |       0.71 |           0.71 |     158.38 |   156.64 |         21 |                 33 |              0.64 |          1.4  |
|   2012 |          19 |         0    |       0.47 |           0.47 |     -25.39 |   -27.26 |         21 |                 28 |              0.61 |         -0.22 |
|   2013 |           2 |         1    |       0    |           0    |     -66.43 |   -68.2  |         21 |                  7 |              0.43 |         -0.34 |
|   2014 |          15 |         0.2  |       0.8  |           0.8  |     108.21 |   106.38 |         21 |                 24 |              0.75 |          1.13 |
|   2015 |          12 |         0.5  |       0.67 |           0.67 |     103.65 |   101.53 |         21 |                 21 |              0.62 |          0.59 |
|   2016 |          20 |         0.6  |       0.65 |           0.65 |      53.06 |    50.89 |         21 |                 24 |              0.58 |          0.65 |
|   2017 |           6 |         1    |       1    |           1    |     226.53 |   224.45 |         21 |                 19 |              0.68 |          1.31 |
|   2018 |          21 |         0    |       0.62 |           0.62 |      52.93 |    50.85 |         21 |                 21 |              0.62 |          0.62 |
|   2019 |           8 |         1    |       0.38 |           0.38 |     -23.77 |   -25.94 |         21 |                 12 |              0.5  |         -0.22 |
|   2020 |           6 |         1    |       0.33 |           0.33 |      26.23 |    24.24 |         21 |                 25 |              0.52 |          0.83 |
|   2021 |          12 |         0.17 |       0.33 |           0.33 |     -51.06 |   -53.07 |         21 |                 34 |              0.44 |         -0.9  |
|   2022 |          14 |         0    |       0.79 |           0.79 |     152.65 |   150.35 |         21 |                 31 |              0.74 |          1.22 |
|   2023 |          11 |         0.55 |       0.45 |           0.45 |     -15.58 |   -17.82 |         21 |                 17 |              0.35 |         -0.15 |
|   2024 |          10 |         0    |       0.3  |           0.3  |     -34.2  |   -36.43 |         21 |                 23 |              0.52 |         -0.49 |

The same bar applied to every candidate (none was selected from this table; it shows that the verdict does not hinge on the pick):

| signal         | gain_ok   | count21_ok   | count42_ok   | not_worse_2023   | placebo_ok   | met   | met_strict_42_count   |
|:---------------|:----------|:-------------|:-------------|:-----------------|:-------------|:------|:----------------------|
| brent_eur_d63  | False     | True         | False        | False            | False        | False | False                 |
| brent_eur_d126 | False     | True         | False        | False            | False        | False | False                 |
| brent_usd_d126 | False     | True         | False        | False            | False        | False | False                 |
| gasratio_d3m   | False     | False        | False        | True             | False        | False | False                 |
| ttf_hh_d63     | False     | False        | False        | False            | False        | False | False                 |
| ea_tb_mom      | False     | False        | False        | False            | False        | False | False                 |
| cli_d6m_diff   | False     | False        | False        | False            | True         | False | False                 |
| sent_lvl_diff  | False     | False        | False        | True             | False        | False | False                 |
| sent_d3m_diff  | False     | False        | False        | False            | False        | False | False                 |
| tips_d21       | False     | True         | False        | False            | False        | False | False                 |
| tips_d63       | False     | True         | False        | False            | False        | False | False                 |
| bei_d63        | False     | False        | False        | False            | False        | False | False                 |

## 7. Timing placebo (signal made 63 / 126 sessions staler)
The signal is shifted by +63 and +126 sessions (staler) and the rule re-evaluated. A vote that helps as much when it is three or six
months old is a regime bet. Reading: the pick (`cli_d6m_diff`) loses everything when stale, but its fresh gain is +0.8 / +2.7 points
at 21 sessions, i.e. nothing. The Brent signals do NOT pass: their AND-rule and standalone numbers are as good or better 63 sessions
stale (`brent_usd_d126` AND rule, weekly 21 sessions: 65 % fresh, 65 % at +63; standalone 56 % fresh, 59 % at +63). `ea_tb_mom`'s +8
points at 42 sessions falls to +0.4 / -0.3 when stale, but it is -3.9 at 21 sessions and -13.0 at 63 on 44-98 decisions: noise around zero.
The look-ahead column (-21: the signal as it will be 21 sessions later) shows the test has power where information exists:
`tips_d21` goes from 49 % to 60 %, because real yields and EUR/USD move together within the month and not afterwards.

AND rule, gain in points over the agreement rule, non-overlapping decisions:

| signal         | 2010-26 21 s: gain fresh / +63 / +126   | 2010-26 42 s: gain fresh / +63 / +126   | 2016-26 21 s: gain fresh / +63 / +126   | 2016-26 42 s: gain fresh / +63 / +126   |
|:---------------|:----------------------------------------|:----------------------------------------|:----------------------------------------|:----------------------------------------|
| brent_eur_d63  | -5.2 / -2.0 / +3.1                      | +2.3 / +4.5 / +2.7                      | +1.1 / -0.3 / +2.1                      | +7.7 / +5.5 / +3.3                      |
| brent_eur_d126 | -2.6 / +7.1 / +0.3                      | -1.5 / +10.3 / +1.0                     | +1.1 / +8.0 / -1.1                      | -1.5 / +12.2 / +4.1                     |
| brent_usd_d126 | -3.7 / +4.7 / -0.5                      | +6.5 / +7.4 / +2.3                      | -0.5 / +8.5 / +1.4                      | +3.3 / +12.8 / +4.1                     |
| gasratio_d3m   | -1.4 / -4.1 / -9.5                      | +1.4 / -4.2 / +3.4                      | -0.8 / -1.6 / -5.9                      | +2.6 / -2.5 / +5.4                      |
| ttf_hh_d63     | -6.4 / -7.3 / -6.6                      | +1.5 / -1.2 / -0.7                      | -4.7 / -5.6 / -4.9                      | +3.2 / +0.5 / +1.1                      |
| ea_tb_mom      | -3.9 / -7.3 / -4.7                      | +8.2 / +0.4 / -0.3                      | -2.7 / -6.4 / -1.3                      | +9.4 / +3.9 / +3.6                      |
| cli_d6m_diff   | +0.8 / -8.3 / -9.7                      | +4.0 / -5.4 / -18.8                     | +2.7 / -9.6 / -8.5                      | +4.0 / -7.1 / -14.1                     |
| sent_lvl_diff  | -2.0 / -1.6 / -3.1                      | -2.9 / -5.1 / -8.4                      | +4.9 / +9.4 / +1.2                      | -2.3 / -7.2 / -12.5                     |
| sent_d3m_diff  | -10.1 / +2.8 / -8.4                     | -5.1 / -0.3 / -7.2                      | -7.3 / +4.7 / -7.3                      | -1.0 / -0.9 / -4.6                      |
| tips_d21       | -1.0 / -6.8 / -5.5                      | +2.5 / +2.8 / +1.5                      | +3.7 / -6.6 / -3.8                      | +4.3 / +4.1 / +2.8                      |
| tips_d63       | -8.1 / -11.5 / -10.0                    | +1.4 / -0.7 / +0.3                      | -6.6 / -12.5 / -11.1                    | +4.7 / +2.4 / -0.4                      |
| bei_d63        | -8.5 / -4.2 / -3.6                      | +0.9 / -1.9 / -1.0                      | -9.7 / -0.8 / +1.0                      | -1.4 / -2.5 / +0.0                      |

Weekly decisions, 2010-26, accuracy % as the signal is shifted in time:

| signal         | standalone 21 s: -21 (look-ahead) / fresh / +1 / +5 / +21 / +63 / +126   | standalone 63 s: -21 (look-ahead) / fresh / +1 / +5 / +21 / +63 / +126   | AND 21 s: fresh / +63 / +126   | outside 21 s: fresh / +63 / +126   |
|:---------------|:-------------------------------------------------------------------------|:-------------------------------------------------------------------------|:-------------------------------|:-----------------------------------|
| brent_eur_d63  | 55 / 51 / 52 / 52 / 52 / 53 / 54                                         | 56 / 53 / 52 / 52 / 51 / 55 / 55                                         | 59 / 61 / 61                   | 51 / 51 / 55                       |
| brent_eur_d126 | 54 / 53 / 53 / 53 / 53 / 58 / 52                                         | 55 / 55 / 56 / 56 / 57 / 59 / 53                                         | 61 / 64 / 56                   | 51 / 58 / 55                       |
| brent_usd_d126 | 53 / 56 / 56 / 57 / 55 / 59 / 52                                         | 56 / 58 / 59 / 58 / 59 / 59 / 53                                         | 65 / 65 / 56                   | 55 / 58 / 55                       |
| gasratio_d3m   | 55 / 53 / 53 / 52 / 48 / 50 / 50                                         | 53 / 49 / 49 / 48 / 48 / 54 / 55                                         | 61 / 54 / 56                   | 52 / 54 / 52                       |
| ttf_hh_d63     | 51 / 55 / 53 / 56 / 56 / 48 / 56                                         | 59 / 59 / 58 / 58 / 54 / 61 / 52                                         | 63 / 55 / 57                   | 51 / 47 / 59                       |
| ea_tb_mom      | 53 / 52 / 53 / 53 / 51 / 49 / 51                                         | 54 / 51 / 51 / 51 / 49 / 50 / 49                                         | 65 / 58 / 67                   | 49 / 49 / 47                       |
| cli_d6m_diff   | 56 / 54 / 54 / 53 / 49 / 46 / 42                                         | 55 / 50 / 50 / 49 / 46 / 42 / 40                                         | 60 / 52 / 49                   | 54 / 47 / 42                       |
| sent_lvl_diff  | 49 / 48 / 48 / 47 / 46 / 47 / 47                                         | 46 / 47 / 48 / 47 / 47 / 44 / 45                                         | 57 / 56 / 55                   | 49 / 49 / 50                       |
| sent_d3m_diff  | 53 / 50 / 50 / 49 / 49 / 49 / 46                                         | 51 / 48 / 48 / 48 / 47 / 44 / 48                                         | 60 / 57 / 54                   | 50 / 51 / 48                       |
| tips_d21       | 60 / 49 / 48 / 47 / 51 / 50 / 46                                         | 54 / 47 / 48 / 46 / 49 / 48 / 46                                         | 57 / 55 / 53                   | 48 / 53 / 48                       |
| tips_d63       | 53 / 47 / 47 / 48 / 48 / 47 / 48                                         | 49 / 49 / 49 / 48 / 47 / 46 / 45                                         | 56 / 54 / 57                   | 47 / 49 / 47                       |
| bei_d63        | 50 / 48 / 46 / 47 / 49 / 49 / 49                                         | 52 / 51 / 49 / 52 / 50 / 51 / 48                                         | 56 / 57 / 63                   | 49 / 49 / 47                       |

## 8. Daily stream and incremental test
Each AND rule as a book of weekly tranches held 21 sessions (`selective.book_time_exit`: weight 1/5 per tranche, turnover netted,
1.2 pips per unit turnover), net Sharpe by period; `agree3_reference` is the agreement rule through the same code (arm N: 0.52 / 0.51 /
0.43). Deflated-Sharpe p for 12 candidates. The final stream misses the round-3 bar as well (2023-26 negative, three-way below two-way).
Some AND books have a higher Sharpe than the reference in 2016-26 (`brent_eur_d63` 0.76, `brent_usd_d126` 0.68); with twelve thinned
copies of a 0.51 stream that is expected, none was selected, and their 2010-15 and placebo records (above) do not support them.

| variant                  |   2010-2015 |   2010-2026 |   2016-2026 |   2023-2026 |   t 2010-26 |   deflated p |   active | final   |
|:-------------------------|------------:|------------:|------------:|------------:|------------:|-------------:|---------:|:--------|
| and_brent_eur_d63        |        0.13 |        0.5  |        0.76 |        0.4  |        2.07 |         0.34 |     0.52 | False   |
| and_brent_eur_d126       |        0.19 |        0.46 |        0.66 |        0.25 |        1.91 |         0.4  |     0.52 | False   |
| and_brent_usd_d126       |        0.57 |        0.64 |        0.68 |        0.3  |        2.65 |         0.16 |     0.49 | False   |
| and_gasratio_d3m         |        0.26 |        0.4  |        0.56 |        0.68 |        1.67 |         0.5  |     0.5  | False   |
| and_ttf_hh_d63           |        0    |        0.49 |        0.61 |        0.73 |        2.05 |         0.34 |     0.24 | False   |
| and_ea_tb_mom            |        0.19 |        0.46 |        0.6  |        0.96 |        1.9  |         0.4  |     0.43 | False   |
| and_cli_d6m_diff         |        0.64 |        0.47 |        0.35 |       -0.19 |        1.96 |         0.38 |     0.41 | True    |
| and_sent_lvl_diff        |        0.15 |        0.2  |        0.26 |        0.2  |        0.84 |         0.8  |     0.32 | False   |
| and_sent_d3m_diff        |        0.19 |        0.32 |        0.49 |        0.38 |        1.33 |         0.63 |     0.42 | False   |
| and_tips_d21             |        0.44 |        0.38 |        0.33 |        0.14 |        1.57 |         0.54 |     0.54 | False   |
| and_tips_d63             |        0.32 |        0.35 |        0.38 |        0.24 |        1.46 |         0.58 |     0.51 | False   |
| and_bei_d63              |        0.31 |        0.2  |        0.11 |        0.19 |        0.84 |         0.8  |     0.41 | False   |
| and_cli_d6m_diff_cost0.6 |        0.64 |        0.48 |        0.35 |       -0.18 |        1.99 |         0.37 |     0.41 | False   |
| agree3_reference         |        0.56 |        0.52 |        0.51 |        0.43 |        2.17 |         0.31 |     0.73 | False   |

Incremental test (EW, walk-forward weights, `meta.combine` / `report_combo`):

| combo                                                      | period    |    n |   sharpe |     t |   mean_bp |   sum_bp |   deflated_sharpe_p |
|:-----------------------------------------------------------|:----------|-----:|---------:|------:|----------:|---------:|--------------------:|
| two-way weak_signals + regime_trend                        | 2010-2026 | 4373 |    0.563 | 2.347 |     0.583 | 2547.29  |               0.249 |
| two-way weak_signals + regime_trend                        | 2016-2026 | 2817 |    0.636 | 2.128 |     0.738 | 2078.3   |             nan     |
| two-way weak_signals + regime_trend                        | 2023-2026 | 1000 |    0.356 | 0.708 |     0.42  |  420.283 |             nan     |
| three-way + real_economy                                   | 2010-2026 | 4373 |    0.567 | 2.363 |     0.486 | 2127.35  |               0.245 |
| three-way + real_economy                                   | 2016-2026 | 2817 |    0.616 | 2.06  |     0.59  | 1662.35  |             nan     |
| three-way + real_economy                                   | 2023-2026 | 1000 |    0.26  | 0.518 |     0.238 |  237.695 |             nan     |
| three-way + selective (agreement rule book, for reference) | 2010-2026 | 4373 |    0.57  | 2.376 |     0.545 | 2382.12  |               0.239 |
| three-way + selective (agreement rule book, for reference) | 2016-2026 | 2817 |    0.641 | 2.143 |     0.691 | 1947.75  |             nan     |
| three-way + selective (agreement rule book, for reference) | 2023-2026 | 1000 |    0.405 | 0.807 |     0.446 |  445.876 |             nan     |

Daily net P&L correlation of the final stream:

| other           |   corr_all_days |   corr_active_days |   corr_2016-26 |
|:----------------|----------------:|-------------------:|---------------:|
| weak_signals    |            0.34 |               0.48 |           0.34 |
| regime_trend    |            0.52 |               0.78 |           0.47 |
| selective_daily |            0.81 |               0.98 |           0.67 |

## 9. Leak checks
* (1) Permuted labels: every rule falls to 50-51 % (5-95 % band 45-57 %).
* (2) Shifted features. One period staler (+1) changes nothing for 3-6-month signals (table in section 7: within a point), so
  "collapses when shifted by one" cannot apply to slow votes; the round-5 placebo (+63 / +126) is the meaningful version and is in
  section 7. The look-ahead control (-21) raises `tips_d21` from 49 to 60 %, the CLI from 54 to 56 %, `gasratio_d3m` from 53 to 55 % and
  `brent_eur_d63` from 51 to 55 % (its EUR conversion then contains the future EUR/USD return), and does not help `brent_usd_d126`
  (56 -> 53): the test sees look-ahead where there is some, and the honest signals do not have it.
* (2b) Truncation: raw data cut at five dates under the declared lags reproduce the stored signal row exactly (12 of 12 each time),
  so no value uses an observation that would not yet have been published (revisions aside, see section 1).
* (3) No signal is a label in disguise: correlation with the forward 21-session return is between -0.07 and +0.13, with the forward
  63-session return between -0.13 and +0.14. Several are correlated with PAST EUR/USD returns (with the
  126-session return: `cli_d6m_diff` +0.27, `ea_tb_mom` +0.24, `brent_usd_d126` -0.21; with the 63-session return: `gasratio_d3m`
  +0.22, `tips_d63` +0.21; with the 21-session return: `tips_d21` +0.22): part of what they vote is price momentum, which rounds
  1-4 found to be worthless here. Their signs agree with each old vote 40-61 % of the time.

(1) labels permuted (300 draws, weekly decisions, 2010-26):

| signal         | rule       |   h |   n_weekly |   real_acc |   shuffled_mean |   shuffled_p05 |   shuffled_p95 |   p_shuffled_ge_real |
|:---------------|:-----------|----:|-----------:|-----------:|----------------:|---------------:|---------------:|---------------------:|
| cli_d6m_diff   | and        |  21 |        210 |      0.6   |           0.507 |          0.452 |          0.567 |                0.003 |
| cli_d6m_diff   | standalone |  21 |        748 |      0.539 |           0.504 |          0.475 |          0.532 |                0.03  |
| brent_usd_d126 | and        |  21 |        234 |      0.645 |           0.503 |          0.449 |          0.551 |                0     |
| brent_usd_d126 | standalone |  21 |        869 |      0.562 |           0.499 |          0.474 |          0.525 |                0     |
| cli_d6m_diff   | and        |  42 |        210 |      0.643 |           0.511 |          0.452 |          0.567 |                0     |
| cli_d6m_diff   | standalone |  42 |        748 |      0.521 |           0.505 |          0.475 |          0.533 |                0.22  |
| brent_usd_d126 | and        |  42 |        231 |      0.68  |           0.502 |          0.446 |          0.558 |                0     |
| brent_usd_d126 | standalone |  42 |        865 |      0.563 |           0.5   |          0.473 |          0.525 |                0     |
| cli_d6m_diff   | and        |  63 |        210 |      0.652 |           0.512 |          0.452 |          0.572 |                0     |
| cli_d6m_diff   | standalone |  63 |        748 |      0.504 |           0.505 |          0.477 |          0.535 |                0.533 |
| brent_usd_d126 | and        |  63 |        231 |      0.714 |           0.505 |          0.455 |          0.558 |                0     |
| brent_usd_d126 | standalone |  63 |        861 |      0.577 |           0.5   |          0.476 |          0.531 |                0     |

(2b) truncation test (raw data cut at the date under the declared lags; the 12 signal values of that session must be unchanged):

| asof       |   signals_defined |   rows_equal |   of |   max_abs_diff | mismatch   |
|:-----------|------------------:|-------------:|-----:|---------------:|:-----------|
| 2012-06-29 |                11 |           12 |   12 |              0 |            |
| 2016-11-15 |                11 |           12 |   12 |              0 |            |
| 2020-03-16 |                12 |           12 |   12 |              0 |            |
| 2022-09-30 |                12 |           12 |   12 |              0 |            |
| 2025-02-14 |                11 |           12 |   12 |              0 |            |

(3) what each signal is correlated with (2010-26; correlations of the signal VALUE, agreement shares of its SIGN):

| signal         |   corr_ret_21d |   corr_ret_63d |   corr_ret_126d |   sign_agree_cot |   sign_agree_spr |   sign_agree_house |   corr_fwd21 |   corr_fwd63 |
|:---------------|---------------:|---------------:|----------------:|-----------------:|-----------------:|-------------------:|-------------:|-------------:|
| brent_eur_d63  |          0.026 |          0.001 |          -0.031 |            0.558 |            0.573 |              0.59  |       -0.005 |        0.064 |
| brent_eur_d126 |          0.072 |          0.058 |           0.01  |            0.574 |            0.584 |              0.601 |        0.052 |        0.138 |
| brent_usd_d126 |         -0.015 |         -0.101 |          -0.212 |            0.514 |            0.567 |              0.599 |        0.045 |        0.128 |
| gasratio_d3m   |          0.083 |          0.215 |           0.124 |            0.614 |            0.538 |              0.564 |       -0.032 |       -0.055 |
| ttf_hh_d63     |          0.134 |          0.031 |          -0.017 |            0.541 |            0.55  |              0.59  |        0.132 |        0.129 |
| ea_tb_mom      |          0.094 |          0.127 |           0.237 |            0.559 |            0.486 |              0.501 |        0.076 |        0.063 |
| cli_d6m_diff   |          0.109 |          0.218 |           0.265 |            0.613 |            0.516 |              0.542 |        0.072 |        0.041 |
| sent_lvl_diff  |         -0.06  |         -0     |           0.012 |            0.474 |            0.429 |              0.401 |       -0.073 |       -0.126 |
| sent_d3m_diff  |          0.03  |          0.205 |           0.168 |            0.518 |            0.485 |              0.461 |       -0.04  |       -0.051 |
| tips_d21       |          0.221 |          0.165 |           0.078 |            0.503 |            0.617 |              0.559 |       -0.044 |       -0.062 |
| tips_d63       |          0.068 |          0.205 |           0.131 |            0.515 |            0.585 |              0.546 |       -0.063 |       -0.078 |
| bei_d63        |          0.019 |          0.159 |           0.211 |            0.535 |            0.431 |              0.457 |       -0.059 |       -0.025 |

## 10. Variants, caveats, what is worth keeping
* **Variant count: 12** candidate signals = 12 AND rules, one selection rule, one final. Not selected from: the standalone, outside,
  contradicted and shifted versions of the same 12 signals. The module was run in full five times: the first run, then re-runs that
  added diagnostics only (the outside-agreement placebo rows, the per-year table, this report); signals, candidates, the selection and
  every number of the first run are unchanged.
* Non-overlapping and weekly numbers disagree for several AND rules (`ttf_hh_d63` against its same-span baseline: weekly
  +7 / +12 / +10 points, non-overlapping -5 / +1 / -2; `brent_usd_d126` at 21 sessions: weekly +5, non-overlapping -3.7). The weekly
  grid counts one directional episode five to thirteen times; the non-overlapping stream is the one the bar is written on, and it
  says no.
* The 2023-26 cells have 5-30 non-overlapping decisions each; nothing can be read from them in either direction.
* What I would keep: (1) the cached data set (TTF, Henry Hub, TIPS and breakevens from 2003, ESI from 1980, euro-area trade from 2002)
  for later arms; (2) the negative result that real-yield and breakeven CHANGES, the CLI and sentiment differentials, trade-balance
  momentum and the monthly gas ratio do not predict 1-3 month EUR/USD direction (45-54 % on weekly decisions), which closes families
  B and C and most of A;
  (3) 6-month Brent as a known 55-58 % slow regime variable that adds nothing to the agreement rule; (4) TTF / Henry Hub as a
  forward-test note only.
