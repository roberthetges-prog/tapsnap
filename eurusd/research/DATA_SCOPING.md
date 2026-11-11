# Data scoping: information the project has never had

Checked 2026-11-11 from the sandbox. Nothing was backtested and no bulk history was stored in the repository. Machine-readable version: `research/data_sources.json` (same content, one object per source).

## Findings

1. **A 23-year daily EUR/USD risk-reversal history is reachable today.** A GitHub copy of the Bloomberg 1-month 25-delta series runs 2003-10-02 to 2026-07-29 (5,874 rows). Together with at-the-money implied vols (2000-01 to 2022-02), EVZ on FRED (2007-11 to 2025-03) and CFTC options-only positioning (combined minus futures-only, files from 1995), an options arm can start now. None of these has a free live feed after mid-2026: EVZ was discontinued in March 2025 and the copies are static.
2. **Four hosts are open that the project had recorded as blocked or had never tried:** `fred.stlouisfed.org` (plain `curl --http1.1`; a browser user-agent is refused), `www.bis.org` (30 years of central-bank speeches as CSV), `storage.googleapis.com` (all GDELT raw files) and `api.stlouisfed.org` (real-time vintages, needs a free key).
3. **All of the top 8 by the requested formula can be backtested without any allowlist change.** Two of them need a host for live use afterwards (`www.frbsf.org`; `www.cmegroup.com` or `cdn.cboe.com`).
4. **What does not exist for free with 10+ years:** OTC option strikes and expiries (DTCC keeps one year), CME option open interest by strike (current day only), retail broker positioning (current values only; OANDA reportedly withdrew its endpoints in 2024), CLS flow (paid), fixed-horizon fed funds / OIS curves (Yahoo drops expired contracts; ECB OIS data start 2017).
5. **Prior evidence is not encouraging for two candidates.** A public study of JPY risk reversals found they react to returns rather than lead them, and a public test of FOMC statement text found no gain for 20-day EUR/USD direction. Both are scored with reduced plausibility.

## Ranking (expected value = independence x history x plausibility / effort)

Scales are 1-5; history is scored on verified length unless marked `claimed`. The formula rewards cheap, long series, so several low-plausibility items rank high simply because they cost nothing to try.

| # | Source | Indep. | Hist. | Plaus. | Effort | EV | Reachable today | History seen |
|---|---|---|---|---|---|---|---|---|
| 1 | EUR/USD 1-month 25-delta risk reversal (Bloomberg BGN), GitHub copy (`rr25_eurusd_github`) | 3 | 5 | 3 | 1 | **45.0** | yes | 2003-10-02 .. 2026-07-29, 5,874 EUR/USD rows, 150-262 rows a year, longest gap 13 days |
| 2 | Fed H.4.1 memo items: securities held in custody for foreign official accounts; foreign repo pool; swap lines (`fred_h41_foreign_custody`) | 4 | 5 | 2 | 1 | **40.0** | yes | 2002-12-18 .. 2026-11-04, 1,247 weeks each |
| 3 | Economic Policy Uncertainty and news-based trackers (FRED copies) (`epu_fred`) | 4 | 5 | 2 | 1 | **40.0** | yes | USEPUINDXD 1985-01-01 .. 2026-11-10 |
| 4 | CFTC options-only positioning in Euro FX (combined report minus futures-only) (`cftc_options_delta`) | 2.5 | 5 | 3 | 1 | **37.5** | yes | Legacy combined: Euro FX 1999-01-05 .. 2016-12-27 (939 weeks) in deahistfo_1995_2016.zip, th... |
| 5 | Geopolitical Risk index, daily (Caldara-Iacoviello), authors' GitHub (`gpr_github`) | 4.5 | 5 | 1.5 | 1 | **33.8** | yes | 1985-01-01 .. 2026-11-02 (15,281 rows) |
| 6 | Jarocinski-Karadi high-frequency policy and information shocks (Fed, ECB) (`jk_policy_shocks`) | 3 | 5 | 2 | 1 | **30.0** | yes | Fed 1990-02-08 .. 2026-09-16 |
| 7 | Euro area balance of payments: monthly portfolio and direct investment flows (ECB flow BPS) (`ecb_bps_portfolio_flows`) | 4 | 5 | 1.5 | 1 | **30.0** | yes | BPS.M.N.I10.W1.S1.S1.T.N.FA.P.F._Z.EUR._T.M.N.ALL: 1999-04 .. 2026-08 (329 months) |
| 8 | San Francisco Fed Daily News Sentiment Index (`sf_fed_news_sentiment`) | 4 | 5 | 2 | 1.5 | **26.7** | yes | 1980-01-01 .. 2025-05-18 in a GitHub copy |
| 9 | EUR/USD implied volatility: Bloomberg ATM 1M/3M/1Y copy + CBOE EVZ on FRED (`atm_iv_eurusd`) | 3 | 5 | 2.5 | 1.5 | **25.0** | yes | ATM vols 2000-01-25 .. 2022-02-22 (5,761 rows) |
| 10 | ECB Survey of Professional Forecasters: expected USD per EUR, policy rate, oil (`ecb_spf_fx_assumption`) | 4 | 3 | 2 | 1 | **24.0** | yes | SPF.Q.U2.ASSU.USD.P3M.Q.AVG: target periods 2002-Q1 .. 2026-Q4 (100 rows) |
| 11 | US Treasury International Capital (TIC) monthly (`us_tic`) | 4 | 5 (claimed) | 2 | 2 | **20.0** | no | none (host blocked) |
| 12 | Central-bank text: BIS speeches archive, FOMC statements and minutes, ECB speeches (`central_bank_text`) | 5 | 5 | 2 | 2.5 | **20.0** | yes | BIS: yearly zips 1996 .. 2026 plus speeches.zip (129.5 MB, last modified 2026-08-23) |
| 13 | sentix investor survey: EUR-USD sentiment (1 month) and strategic bias (6 months) (`sentix_fx_sentiment`) | 5 | 5 (claimed) | 3 | 4 | **18.8** | no | none (host blocked) |
| 14 | ECB Euro Area Monetary Policy event-study Database (EA-MPD) (`ecb_ea_mpd`) | 3 | 5 (claimed) | 2 | 2 | **15.0** | no | none (host blocked) |

Ranks 9-14 are shown because they are close to the cut. Central-bank text (`central_bank_text`) is the most independent source of all and is reachable today; it ranks lower only because tone scoring is real work.

### Suggested research arms from the top of the list

* **Options arm (start now):** risk-reversal level, change and extremes; implied-minus-realised variance from the ATM vols / EVZ and the project's own minute data; CFTC option-delta positioning by trader group.
* **Official and portfolio flow arm (start now):** weekly change in foreign official custody holdings and the foreign repo pool; ECB monthly portfolio flows with the 7-week lag applied.
* **Uncertainty and news arm (start now):** US-minus-Europe policy uncertainty, monetary-policy and trade uncertainty, geopolitical risk, SF Fed news sentiment (to 2025-05 from the copy).
* **Policy-surprise and text arm (start now, more work):** cumulated Fed-minus-ECB high-frequency shocks; hawkish-minus-dovish tone gap from BIS speeches and FOMC text, with the scoring rule frozen first.

Each arm adds trials to the deflation count; with about 480 already spent, one or two pre-declared variants per source is the affordable budget.

## Hosts

### Reachable today (verified by a successful request)

| Host | Used for |
|---|---|
| `raw.githubusercontent.com` | GitHub copies: risk reversal, ATM vols, policy shocks, GPR, FOMC text, SF Fed copy |
| `media.githubusercontent.com` | GitHub large files (ECB speeches copy, 52 MB) |
| `fred.stlouisfed.org` | EVZ, EPU family, H.4.1 custody, term premia (curl --http1.1, default user-agent only) |
| `api.stlouisfed.org` | ALFRED vintages once a free API key exists |
| `data-api.ecb.europa.eu` | BPS portfolio flows, SPF, OIS money-market statistics, TARGET balances |
| `www.cftc.gov` | futures-and-options-combined history |
| `www.bis.org` | central bankers' speeches bulk files and RSS |
| `storage.googleapis.com` | GDELT raw files (bucket data.gdeltproject.org) |
| `query1.finance.yahoo.com` | 6E volume, live fed funds contracts, FXE |

### To allow, smallest useful set first (exact hostnames)

| Order | Host | Unlocks |
|---|---|---|
| 1 | `www.frbsf.org` | live SF Fed news sentiment (top-8 item; the GitHub copy stops 2025-05-18) |
| 2 | `www.cmegroup.com` | CVOL EUVL and skew = only free live continuation of the risk reversal / implied vol; daily bulletin (6E option open interest) |
| 3 | `cdn.cboe.com` | FXE option chain for an own implied-vol and skew series going forward |
| 4 | `www.ecb.europa.eu` | official all_ECB_speeches.csv (weekly), EA-MPD event database, policy statements |
| 5 | `www.federalreserve.gov` | official FOMC statements, minutes, speeches, H.4.1 detail |
| 6 | `ticdata.treasury.gov` | TIC monthly flows |
| 7 | `www.sentix.de` | EUR-USD investor sentiment (needs a registered login as well) |
| 8 | `api.gdeltproject.org` | GDELT timelines without the 170 GB raw route |
| 9 | `www.atlantafed.org` | GDPNow history, Market Probability Tracker |
| 10 | `www.mof.go.jp` | Japan weekly securities flows |
| 11 | `download.zew.de` | ZEW monthly tables with dollar/euro expectations |
| 12 | `www.newyorkfed.org` | NY Fed nowcast, market surveys |
| 13 | `pddata.dtcc.com` | OTC FX option trades (one year of history only) |
| 14 | `trends.google.com` | Google Trends |
| 15 | `content.guardianapis.com` | Guardian article API |
| 16 | `api.fiscaldata.treasury.gov` | Treasury auction results |
| 17 | `data.snb.ch` | SNB sight deposits |
| 18 | `data.imf.org` | COFER |

The first three are what the top-8 items need to keep running after a backtest. Hosts 4-7 open the next tier (official text, TIC, sentix). The rest are optional. Not a host change: a free FRED API key for `api.stlouisfed.org`, and a sentix login.

Every host in the table above returned a proxy refusal (CONNECT 403) today; the full list of hosts confirmed blocked is in the JSON (`hosts_confirmed_blocked_today`). `stooq.com` answers but serves a JavaScript challenge.

## Full source table

### 1 FX options

#### EUR/USD 1-month 25-delta risk reversal (Bloomberg BGN), GitHub copy

`rr25_eurusd_github` · rank 1 · EV 45.0 (independence 3, history 5 verified, plausibility 3, effort 1)

* **Measures:** Implied vol of 25-delta EUR calls minus EUR puts, 1 month; also USD/JPY and EUR/JPY.
* **Why it could matter over weeks:** Price of crash insurance = where option buyers pay up for protection. Level/extremes proxy hedging demand and skew risk premium; changes show whether real-money hedgers lean with or against spot.
* **Frequency / lag:** daily / same day (market quote)
* **History verified:** 2003-10-02 .. 2026-07-29, 5,874 EUR/USD rows, 150-262 rows a year, longest gap 13 days. *How:* Downloaded the file (302 kB) and parsed it; values plausible (-2.86 on 2008-10-24, -2.26 on 2015-01-16).
* **Cost:** free copy of paid data (Bloomberg)
* **URL pattern:** `https://raw.githubusercontent.com/GerardWu100/geographic-equity-rotation/main/data/RiskReversalData_Clean.csv`
* **Hosts:** `raw.githubusercontent.com` · reachable today: yes
* **Format / size:** CSV, 0.3 MB
* **GitHub copy:** `https://raw.githubusercontent.com/GerardWu100/geographic-equity-rotation/main/data/RiskReversalData_Clean.csv` · range seen 2003-10-02 .. 2026-07-29
* **Pitfalls:** Third-party redistribution of Bloomberg data: research use only, licence is not ours; one tenor only (1M), no butterfly; quote time unknown (assume NY close, lag one day); copy ends 2026-07-29 and may never update. A sibling study on JPY carry (AleMazza04-NoScroll/carry-unwind-signals) found risk reversals REACT to returns rather than lead them: expect a contemporaneous, not predictive, relation.
* **Independence from positioning / 2y-spread trend / macro score:** Moderate: correlated with recent spot return and with speculative positioning, but it is an options-market price the project has never seen.
* **Live continuation:** No free live feed. Options: CME CVOL skew (www.cmegroup.com), or own skew from the FXE chain (cdn.cboe.com).

#### EUR/USD implied volatility: Bloomberg ATM 1M/3M/1Y copy + CBOE EVZ on FRED

`atm_iv_eurusd` · rank 9 · EV 25.0 (independence 3, history 5 verified, plausibility 2.5, effort 1.5)

* **Measures:** At-the-money implied vol 1M/3M/1Y (GitHub copy) and EVZ, the 30-day implied vol of FXE options.
* **Why it could matter over weeks:** Implied minus realised variance (variance risk premium) is a documented predictor of dollar returns at 1-4 months (Londono & Zhou 2017); term-structure slope marks stress regimes.
* **Frequency / lag:** daily / same day; FRED copy next day
* **History verified:** ATM vols 2000-01-25 .. 2022-02-22 (5,761 rows); EVZCLS 2007-11-01 .. 2025-03-11. *How:* Downloaded both; level correlation V1M vs EVZ 0.991 on 3,596 common days.
* **Cost:** free
* **URL pattern:** `https://raw.githubusercontent.com/frederikbachdk/FXVolTrading/master/data/EURUSD.csv ; https://fred.stlouisfed.org/graph/fredgraph.csv?id=EVZCLS`
* **Hosts:** `raw.githubusercontent.com`, `fred.stlouisfed.org` · reachable today: yes
* **Format / size:** CSV, 0.29 MB + 0.07 MB
* **GitHub copy:** `https://raw.githubusercontent.com/frederikbachdk/FXVolTrading/master/data/EURUSD.csv` · range seen 2000-01-25 .. 2022-02-22
* **Pitfalls:** EVZ was decommissioned: last value 2025-03-11 on FRED (and, per NavyBlueCheese/fx-vrp, on CBOE). Splice of two sources ends 2025-03; nothing free after that. GitHub copy is redistributed Bloomberg data.
* **Independence from positioning / 2y-spread trend / macro score:** Low-moderate for direction: the project already forecasts range/volatility well; the new part is the implied-minus-realised gap.
* **Live continuation:** Needs CME CVOL (www.cmegroup.com) or own model-free vol from FXE chain (cdn.cboe.com).

#### CFTC options-only positioning in Euro FX (combined report minus futures-only)

`cftc_options_delta` · rank 4 · EV 37.5 (independence 2.5, history 5 verified, plausibility 3, effort 1)

* **Measures:** Delta-equivalent option positions by trader group = futures-and-options-combined minus futures-only.
* **Why it could matter over weeks:** Splits speculative positioning into outright futures and option exposure; option exposure of leveraged funds and asset managers is a positioning view the project has not used (only futures-only columns are in cot_eurofx_deep.csv).
* **Frequency / lag:** weekly (Tuesday) / 3 days (Friday 15:30 ET)
* **History verified:** Legacy combined: Euro FX 1999-01-05 .. 2016-12-27 (939 weeks) in deahistfo_1995_2016.zip, then yearly files to deahistfo2026.zip; by-trader-type (TFF) combined: 551 Euro FX weeks in fin_com_txt_2006_2016.zip, then yearly com_fin_txt_{YYYY}.zip; current week FinComWk.txt dated 2026-11-03. *How:* Downloaded and parsed both multi-year archives (19.3 MB, 3.2 MB); HTTP 200 on the 2026 files; compared FinComWk.txt with FinFutWk.txt for 2026-11-03: open interest 1,031,931 vs 876,122, leveraged-fund longs 90,652 vs 119,238.
* **Cost:** free
* **URL pattern:** `https://www.cftc.gov/files/dea/history/deahistfo_1995_2016.zip ; .../deahistfo{YYYY}.zip ; .../fin_com_txt_2006_2016.zip ; .../com_fin_txt_{YYYY}.zip ; https://www.cftc.gov/dea/newcot/FinComWk.txt`
* **Hosts:** `www.cftc.gov` · reachable today: yes
* **Format / size:** zipped CSV, ~45 MB in total
* **GitHub copy:** none found
* **Pitfalls:** Delta-weighted aggregate only: no strikes, expiries or put/call split. Same Tuesday snapshot and Friday release as the positioning already used. The project README says curl sometimes gets a Cloudflare challenge from cftc.gov; a browser user-agent worked today.
* **Independence from positioning / 2y-spread trend / macro score:** Low-moderate: same reporting population as the live positioning stream.

#### CME CVOL for Euro FX (EUVL): implied vol, skew, up/down variance

`cme_cvol` · rank 30 · EV 4.5 (independence 3, history 2 claimed, plausibility 3, effort 4)

* **Measures:** Model-free 30-day implied vol and skew from CME 6E options.
* **Why it could matter over weeks:** Exchange-traded equivalent of the risk reversal, and the only candidate live feed for one.
* **Frequency / lag:** daily / end of day
* **History verified:** none. *How:* www.cmegroup.com is blocked; documentation found by search only.
* **Claimed, not verified:** Launch material (2020) promised two years of back-history; a 2026-08-17 CME notice quotes EUVL 5.345. Start date of the public series not established.
* **Cost:** end-of-day values on the website free; full history via CME DataMine (paid)
* **URL pattern:** `https://www.cmegroup.com/market-data/cme-group-benchmark-administration/cme-volatility-indexes.html (JSON endpoint behind the chart not verified)`
* **Hosts:** `www.cmegroup.com` · reachable today: no
* **Format / size:** CSV/JSON, small
* **GitHub copy:** none found
* **Pitfalls:** Website is bot-protected; free look-back window unknown; licence restricts redistribution.
* **Independence from positioning / 2y-spread trend / macro score:** Moderate (same information as the risk reversal).

#### CME Daily Bulletin: 6E option volume, open interest by strike, put/call

`cme_daily_bulletin` · rank 36 · EV 1.8 (independence 3, history 1 none, plausibility 3, effort 5)

* **Measures:** Per-strike open interest and volume for Euro FX options (sections 31/32/39) and the FX summary (01B).
* **Why it could matter over weeks:** Put/call open-interest ratios and large open-interest strikes (pinning into expiry).
* **Frequency / lag:** daily / next morning
* **History verified:** none. *How:* Host blocked; CME documentation says files are 'top day only' and overwritten daily.
* **Claimed, not verified:** CME states volume/open-interest history exists from 1972 in DataMine.
* **Cost:** current day free; history paid (DataMine)
* **URL pattern:** `https://www.cmegroup.com/daily_bulletin/current/Section31_Foreign_Exchange_Call_Options.pdf ; .../Section32_Foreign_Exchange_Put_Options.pdf ; .../Section01B_Summary_Volume_And_Open_Interest_FX_Futures_And_Options.pdf`
* **Hosts:** `www.cmegroup.com` · reachable today: no
* **Format / size:** PDF, ~1 MB a day
* **GitHub copy:** none found
* **Pitfalls:** No free history: only forward collection from the day the host opens; PDF parsing.
* **Independence from positioning / 2y-spread trend / macro score:** Moderate.

#### DTCC swap data repository: public OTC FX option trades (large expiries)

`dtcc_sdr_fx_options` · rank 35 · EV 2.0 (independence 4, history 1 claimed, plausibility 2, effort 4)

* **Measures:** Trade-level OTC FX options reported under CFTC rules: notional, strike, expiry, option type.
* **Why it could matter over weeks:** The only public source for OTC strikes and expiries (NY-cut expiry maps).
* **Frequency / lag:** intraday / daily cumulative files / same day
* **History verified:** none. *How:* Host blocked; DTCC help pages found by search.
* **Claimed, not verified:** DTCC help: cumulative slice reports are kept 366 days (data from 2023-12-29); older data on request.
* **Cost:** free
* **URL pattern:** `https://pddata.dtcc.com/ppd/cftcdashboard (per-day zip per asset class; URL pattern not confirmed)`
* **Hosts:** `pddata.dtcc.com` · reachable today: no
* **Format / size:** zipped CSV, tens of MB a day
* **GitHub copy:** none found
* **Pitfalls:** About one year of free history: far below the 10-year bar; notionals capped; US-reported trades only. NY-cut expiry lists otherwise exist only as news commentary, not as a dataset.
* **Independence from positioning / 2y-spread trend / macro score:** High, but untestable on history.

#### CBOE delayed option chain for FXE (forward collection only)

`cboe_fxe_chain` · rank 34 · EV 2.5 (independence 3, history 1 none, plausibility 2.5, effort 3)

* **Measures:** Full FXE option chain snapshot (bids, asks, implied vols, open interest).
* **Why it could matter over weeks:** Lets the project compute its own implied vol and 25-delta skew going forward.
* **Frequency / lag:** snapshot (15-minute delayed) / none
* **History verified:** none. *How:* Host blocked; URL documented in NavyBlueCheese/fx-vrp.
* **Cost:** free
* **URL pattern:** `https://cdn.cboe.com/api/global/delayed_quotes/options/FXE.json ; https://cdn.cboe.com/api/global/us_indices/daily_prices/EVZ_History.csv`
* **Hosts:** `cdn.cboe.com` · reachable today: no
* **Format / size:** JSON, <1 MB a snapshot
* **GitHub copy:** none found
* **Pitfalls:** No history at all; FXE options are thin (244 contracts in July 2026 per the fx-vrp note).
* **Independence from positioning / 2y-spread trend / macro score:** Moderate.

### 2 Policy paths

#### Jarocinski-Karadi high-frequency policy and information shocks (Fed, ECB)

`jk_policy_shocks` · rank 6 · EV 30.0 (independence 3, history 5 verified, plausibility 2, effort 1)

* **Measures:** Surprise in OIS / fed funds futures in the minutes around each FOMC and ECB announcement, split into 'policy' and 'central-bank information' shocks.
* **Why it could matter over weeks:** Measures what the market did NOT expect, which the calendar actual-vs-forecast data cannot. Relative cumulated surprises are a candidate for post-announcement drift over weeks.
* **Frequency / lag:** per meeting (8 a year each) and monthly / same day in principle; these files are updated a few times a year
* **History verified:** Fed 1990-02-08 .. 2026-09-16; ECB 1999-01-07 .. 2025-10-30. *How:* Downloaded and read first/last rows.
* **Cost:** free (authors' repository)
* **URL pattern:** `https://raw.githubusercontent.com/marekjarocinski/jkshocks_update_fed/main/shocks_fed_jk_t.csv ; https://raw.githubusercontent.com/marekjarocinski/jkshocks_update_ecb/main/shocks_ecb_mpd_me_d.csv`
* **Hosts:** `raw.githubusercontent.com` · reachable today: yes
* **Format / size:** CSV, 25 kB each
* **GitHub copy:** `https://raw.githubusercontent.com/marekjarocinski/jkshocks_update_ecb/main/shocks_ecb_mpd_me_d.csv` · range seen 1999-01-07 .. 2025-10-30 (ECB); 1990-02-08 .. 2026-09-16 (Fed)
* **Pitfalls:** Only ~16 events a year: small samples. Scaling of pc1 uses the full sample (mild look-ahead in units, not in sign). ECB file lags by months. The log already found event reactions and policy-cycle turns unprofitable.
* **Independence from positioning / 2y-spread trend / macro score:** Moderate: related to the 2y-spread trend, which absorbs the same surprises within days.

#### ECB Euro Area Monetary Policy event-study Database (EA-MPD)

`ecb_ea_mpd` · rank 14 · EV 15.0 (independence 3, history 5 claimed, plausibility 2, effort 2)

* **Measures:** Intraday changes in OIS, yields, equities and exchange rates in the press-release and press-conference windows.
* **Why it could matter over weeks:** Raw input of the ECB shock series above, including the EUR/USD move itself and the OIS curve by maturity.
* **Frequency / lag:** per ECB meeting / updated after meetings
* **History verified:** none (host blocked). *How:* URL is quoted in the README of marekjarocinski/jkshocks_update_ecb; no GitHub copy of the xlsx found.
* **Claimed, not verified:** From 1999 per the authors.
* **Cost:** free
* **URL pattern:** `https://www.ecb.europa.eu/pub/pdf/annex/Dataset_EA-MPD.xlsx`
* **Hosts:** `www.ecb.europa.eu` · reachable today: no
* **Format / size:** XLSX, ~1 MB
* **GitHub copy:** none found
* **Pitfalls:** Events only; same caveats as the shock series.
* **Independence from positioning / 2y-spread trend / macro score:** Moderate.

#### Fed funds and SOFR futures by contract month on Yahoo

`yahoo_fed_funds_contracts` · rank 33 · EV 3.0 (independence 1.5, history 1 verified, plausibility 2, effort 1)

* **Measures:** Settlement prices of individual contract months.
* **Why it could matter over weeks:** Would give the priced policy path at fixed horizons.
* **Frequency / lag:** daily / same day
* **History verified:** Only contracts still listed: ZQZ26.CBT from 2021-12-31, ZQZ27.CBT from 2022-12-30; ZQZ25/ZQZ20/ZQZ15 return 404. Front continuation ZQ=F 2000-09-01 .. today. SR3Z26.CME has 75 non-empty closes.. *How:* Chart API with period1=0, interval=1d.
* **Cost:** free
* **URL pattern:** `https://query1.finance.yahoo.com/v8/finance/chart/ZQZ26.CBT?period1=0&period2=1900000000&interval=1d`
* **Hosts:** `query1.finance.yahoo.com` · reachable today: yes
* **Format / size:** JSON, small
* **GitHub copy:** none found
* **Pitfalls:** Expired contracts are gone, so no fixed-horizon (e.g. 6- or 12-month-ahead) history can be built before 2022; SOFR contract data are mostly empty. Rate expectations were already tested (round 3).
* **Independence from positioning / 2y-spread trend / macro score:** Low: the 2y spread already carries the priced path.

#### ECB money-market statistics: euro OIS rates (flows EMMS, MMSR)

`ecb_ois_money_market` · rank 24 · EV 6.0 (independence 1.5, history 2 verified, plausibility 2, effort 1)

* **Measures:** Traded OIS rates by maturity bucket; '1-year OIS in 2 years' monthly.
* **Why it could matter over weeks:** Euro-side priced policy path without sovereign-credit noise.
* **Frequency / lag:** daily buckets; monthly forwards / weeks to months
* **History verified:** EMMS daily buckets 2017-01-03 .. 2025-12-31 (2,302 rows); monthly 1y-in-2y OIS 2010-01 .. 2025-12; MMSR per maintenance period 2017-03-14 .. 2026-09-15 (77 rows). *How:* Queried the API, read first/last periods.
* **Cost:** free
* **URL pattern:** `https://data-api.ecb.europa.eu/service/data/EMMS/B.U2._X._Z.S122.S1ZV._Z.O._X.WR._X.GB._Z._Z.EUR._Z._Z.OIS._Z?format=csvdata`
* **Hosts:** `data-api.ecb.europa.eu` · reachable today: yes
* **Format / size:** CSV, small
* **GitHub copy:** none found
* **Pitfalls:** Under 10 years daily; daily series stops at 2025-12-31; published with a long delay: unusable live.
* **Independence from positioning / 2y-spread trend / macro score:** Low.

#### Atlanta Fed Market Probability Tracker

`atlanta_fed_mpt` · rank 28 · EV 5.0 (independence 2.5, history 2 claimed, plausibility 2, effort 2)

* **Measures:** Option-implied probability distribution of the 3-month SOFR path.
* **Why it could matter over weeks:** Adds the distribution (skew, tail weight) around the priced Fed path.
* **Frequency / lag:** daily / 1 day
* **History verified:** none (host blocked). *How:* Search confirms a 'MPT Historical Data' download; start date not found.
* **Claimed, not verified:** Start date unknown.
* **Cost:** free
* **URL pattern:** `https://www.atlantafed.org/cenfis/market-probability-tracker (historical data link)`
* **Hosts:** `www.atlantafed.org` · reachable today: no
* **Format / size:** XLSX/CSV, small
* **GitHub copy:** none found
* **Pitfalls:** US side only; methodology switched from fed funds to SOFR options; history probably under 10 years.
* **Independence from positioning / 2y-spread trend / macro score:** Low-moderate.

#### Kim-Wright term premia (FRED THREEFYTP2 / THREEFYTP10)

`fred_term_premia` · rank 18 · EV 11.2 (independence 1.5, history 5 verified, plausibility 1.5, effort 1)

* **Measures:** Model split of US yields into expected short rates and term premium.
* **Why it could matter over weeks:** Separates the 'expected policy path' part of the 2y/10y yield from the premium part.
* **Frequency / lag:** daily / about one week
* **History verified:** 1990-01-02 .. 2026-11-06 (9,614 rows each). *How:* Downloaded from FRED.
* **Cost:** free
* **URL pattern:** `https://fred.stlouisfed.org/graph/fredgraph.csv?id=THREEFYTP2`
* **Hosts:** `fred.stlouisfed.org` · reachable today: yes
* **Format / size:** CSV, 0.2 MB
* **GitHub copy:** none found
* **Pitfalls:** US only; model re-estimated, so history is revised; rate-based signals already exhausted.
* **Independence from positioning / 2y-spread trend / macro score:** Low.

#### ECB Survey of Professional Forecasters: expected USD per EUR, policy rate, oil

`ecb_spf_fx_assumption` · rank 10 · EV 24.0 (independence 4, history 3 verified, plausibility 2, effort 1)

* **Measures:** Mean (and dispersion) of forecasters' assumed EUR/USD 3 to 12 months ahead, plus MRO-rate assumptions.
* **Why it could matter over weeks:** Direct survey expectation of the exchange rate; expected change and disagreement are information of a kind the project has never used.
* **Frequency / lag:** quarterly / about 3-4 weeks after the survey
* **History verified:** SPF.Q.U2.ASSU.USD.P3M.Q.AVG: target periods 2002-Q1 .. 2026-Q4 (100 rows); P12M 2002-Q4 .. 2027-Q3. *How:* Queried the API.
* **Cost:** free
* **URL pattern:** `https://data-api.ecb.europa.eu/service/data/SPF/Q.U2.ASSU.USD.P3M+P12M.Q.AVG?format=csvdata`
* **Hosts:** `data-api.ecb.europa.eu` · reachable today: yes
* **Format / size:** CSV, small
* **GitHub copy:** none found
* **Pitfalls:** Quarterly: ~96 observations, low power. TIME_PERIOD is the target quarter, not the survey date: map each row back to its survey round and publication date before use. Survey FX forecasts are known to follow spot.
* **Independence from positioning / 2y-spread trend / macro score:** High in kind, low in frequency.

### 3 Flows and positioning

#### Fed H.4.1 memo items: securities held in custody for foreign official accounts; foreign repo pool; swap lines

`fred_h41_foreign_custody` · rank 2 · EV 40.0 (independence 4, history 5 verified, plausibility 2, effort 1)

* **Measures:** Treasuries and agencies held at the NY Fed for foreign central banks (WMTSECL1, WSEFINTL1), foreign official reverse repos (WLRRAFOIAL), central-bank liquidity swaps (SWPT).
* **Why it could matter over weeks:** Weekly footprint of reserve managers: dollar accumulation and liquidation by foreign central banks (intervention, reserve recycling into euros). Not in the project's H.4.1 file (walcl, wresbal, rrp only).
* **Frequency / lag:** weekly (Wednesday level) / 1 day (Thursday 16:30 ET)
* **History verified:** 2002-12-18 .. 2026-11-04, 1,247 weeks each. *How:* Downloaded four series from FRED.
* **Cost:** free
* **URL pattern:** `https://fred.stlouisfed.org/graph/fredgraph.csv?id=WMTSECL1 (also WSEFINTL1, WLRRAFOIAL, SWPT, WFCDA)`
* **Hosts:** `fred.stlouisfed.org` · reachable today: yes
* **Format / size:** CSV, 30 kB each
* **GitHub copy:** none found
* **Pitfalls:** Covers only reserves custodied at the Fed (share has changed over time); face value; mixes all currencies' reserve managers. FRED answers curl only with the default user-agent and --http1.1 (a browser user-agent is refused).
* **Independence from positioning / 2y-spread trend / macro score:** High: official-sector flow, unrelated to speculative futures positioning.

#### Euro area balance of payments: monthly portfolio and direct investment flows (ECB flow BPS)

`ecb_bps_portfolio_flows` · rank 7 · EV 30.0 (independence 4, history 5 verified, plausibility 1.5, effort 1)

* **Measures:** Net purchases of euro-area equities and debt by non-residents and of foreign securities by residents.
* **Why it could matter over weeks:** Cross-border portfolio flows are the textbook medium-term driver of EUR/USD (equity inflows 2017, bond outflows under QE).
* **Frequency / lag:** monthly / about 7 weeks (August 2026 was the latest month on 2026-11-11)
* **History verified:** BPS.M.N.I10.W1.S1.S1.T.N.FA.P.F._Z.EUR._T.M.N.ALL: 1999-04 .. 2026-08 (329 months); equity/debt, asset/liability splits verified for area I9 2013-01 .. 2025-12. *How:* Queried the API.
* **Cost:** free
* **URL pattern:** `https://data-api.ecb.europa.eu/service/data/BPS/M.N.I10.W1.S1.S1.T.N.FA.P.F._Z.EUR._T.M.N.ALL?format=csvdata`
* **Hosts:** `data-api.ecb.europa.eu` · reachable today: yes
* **Format / size:** CSV, small
* **GitHub copy:** none found
* **Pitfalls:** Heavily revised and no vintages in this flow; area code changed (I8 to 2022-12 in flow BP6, I9 to 2025-12, I10 current); the 7-week lag must be applied; splits by instrument are shorter than the net series.
* **Independence from positioning / 2y-spread trend / macro score:** High.

#### US Treasury International Capital (TIC) monthly

`us_tic` · rank 11 · EV 20.0 (independence 4, history 5 claimed, plausibility 2, effort 2)

* **Measures:** Foreign net purchases of US long-term securities by country and holder type; major foreign holders.
* **Why it could matter over weeks:** Dollar-side counterpart of the ECB flows; official vs private demand for dollar assets.
* **Frequency / lag:** monthly / about 6 weeks
* **History verified:** none (host blocked). *How:* File names confirmed by search (slt_table3.txt, slt_table5, mfhhis01.txt).
* **Claimed, not verified:** Decades of history per Treasury archives.
* **Cost:** free
* **URL pattern:** `https://ticdata.treasury.gov/resource-center/data-chart-center/tic/Documents/slt_table3.txt (also slt_table1, slt_table5.html, snetus.csv)`
* **Hosts:** `ticdata.treasury.gov` · reachable today: no
* **Format / size:** TXT/CSV, <5 MB
* **GitHub copy:** none found
* **Pitfalls:** Format changed in 2023 (S and SLT forms merged); custodial bias by country; revisions.
* **Independence from positioning / 2y-spread trend / macro score:** High.

#### Japan MoF weekly international transactions in securities

`japan_mof_weekly` · rank 15 · EV 15.0 (independence 4, history 5 claimed, plausibility 1.5, effort 2)

* **Measures:** Japanese residents' net purchases of foreign bonds and equities; foreigners' purchases of Japanese assets.
* **Why it could matter over weeks:** Japanese life insurers and pension funds are large buyers of euro-area and US bonds.
* **Frequency / lag:** weekly / about 1 week
* **History verified:** none (host blocked). *How:* CEIC lists the weekly series from 2005 (third party).
* **Claimed, not verified:** Weekly from 2005.
* **Cost:** free
* **URL pattern:** `https://www.mof.go.jp/english/policy/international_policy/reference/itn_transactions_in_securities/week.csv (not confirmed)`
* **Hosts:** `www.mof.go.jp` · reachable today: no
* **Format / size:** CSV, small
* **GitHub copy:** none found
* **Pitfalls:** No currency split: euro share unknown; affects JPY crosses first.
* **Independence from positioning / 2y-spread trend / macro score:** High, but indirect.

#### Retail broker positioning (OANDA, IG, Myfxbook, Dukascopy SWFX)

`retail_sentiment` · rank 32 · EV 3.3 (independence 4, history 1 none, plausibility 2.5, effort 3)

* **Measures:** Share of retail accounts long vs short EUR/USD.
* **Why it could matter over weeks:** Contrarian indicator with a published track record at brokers.
* **Frequency / lag:** intraday / none
* **History verified:** none. *How:* No GitHub repository with stored history found (only scrapers). A trading blog reports OANDA removed its order-book and position-book endpoints in September 2024.
* **Claimed, not verified:** Dukascopy shows some history in a web widget.
* **Cost:** free with account
* **URL pattern:** `https://www.myfxbook.com/api/get-community-outlook.json?session=... ; https://api.ig.com/gateway/deal/clientsentiment/EURUSD ; https://freeserv.dukascopy.com/2.0/ (widget)`
* **Hosts:** `www.myfxbook.com`, `api.ig.com`, `freeserv.dukascopy.com` · reachable today: no
* **Format / size:** JSON, small
* **GitHub copy:** none found
* **Pitfalls:** Current values only: no usable history, so forward collection for years before any test; terms of use.
* **Independence from positioning / 2y-spread trend / macro score:** High, untestable.

#### CLS FX spot flow by participant type

`cls_fx_flow` · rank 20 · EV 10.5 (independence 5, history 3 claimed, plausibility 3.5, effort 5)

* **Measures:** Hourly buy/sell volume of banks, funds, corporates, non-bank financials.
* **Why it could matter over weeks:** The best-documented flow predictor in the literature (Ranaldo & Somogyi).
* **Frequency / lag:** hourly / next business day
* **History verified:** none. *How:* Search only.
* **Claimed, not verified:** Hourly data from about 2012; intraday from 2017-09.
* **Cost:** paid (CLS Market Data; no public price list)
* **URL pattern:** `vendor delivery`
* **Hosts:** `(vendor)` · reachable today: no
* **Format / size:** CSV
* **GitHub copy:** none found
* **Pitfalls:** Commercial licence.
* **Independence from positioning / 2y-spread trend / macro score:** High.

#### CME 6E front-contract volume and FXE ETF price/volume (Yahoo)

`yahoo_6e_volume_fxe` · rank 16 · EV 15.0 (independence 2, history 5 verified, plausibility 1.5, effort 1)

* **Measures:** Daily futures volume (no open interest) and ETF dollar volume.
* **Why it could matter over weeks:** Activity/attention proxy.
* **Frequency / lag:** daily / same day
* **History verified:** 6E=F 2000-09-12 .. 2026-11-11 (5,825 days with volume); FXE 2005-12-12 .. 2026-11-11. *How:* Chart API.
* **Claimed, not verified:** FXE shares-outstanding history: no source located.
* **Cost:** free
* **URL pattern:** `https://query1.finance.yahoo.com/v8/finance/chart/6E=F?period1=0&period2=1900000000&interval=1d`
* **Hosts:** `query1.finance.yahoo.com` · reachable today: yes
* **Format / size:** JSON
* **GitHub copy:** none found
* **Pitfalls:** Front contract only (roll artefacts); no daily open interest; FXE is a small fund.
* **Independence from positioning / 2y-spread trend / macro score:** Low: volume mostly tracks volatility.

#### Reserve data: IMF COFER, SNB sight deposits, ECB TARGET balances and FX interventions

`imf_cofer_snb` · rank 25 · EV 6.0 (independence 3, history 4 verified, plausibility 1, effort 2)

* **Measures:** Currency composition of world reserves (quarterly); SNB sight deposits (weekly intervention proxy); TARGET balances (monthly); ECB interventions (daily).
* **Why it could matter over weeks:** Reserve diversification and intra-euro capital flight.
* **Frequency / lag:** weekly to quarterly / 1 week to 3 months
* **History verified:** ECB TARGET (TGB) 2008-05 .. 2026-09; ECB interventions (FXI) 2000-09-01 .. 2026-06-30 with five non-zero days (four in 2000, one in 2011). *How:* ECB API queried; IMF and SNB hosts blocked.
* **Claimed, not verified:** COFER quarterly from 1999; SNB weekly.
* **Cost:** free
* **URL pattern:** `https://data-api.ecb.europa.eu/service/data/TGB/M.DE.N.A094T.U2.EUR.E?format=csvdata ; https://data.snb.ch/ ; https://data.imf.org/`
* **Hosts:** `data-api.ecb.europa.eu`, `data.snb.ch`, `data.imf.org` · reachable today: no
* **Format / size:** CSV
* **GitHub copy:** none found
* **Pitfalls:** COFER is quarterly with a 3-month lag; SNB data speak to EUR/CHF; ECB interventions are five days in 26 years.
* **Independence from positioning / 2y-spread trend / macro score:** Moderate, low relevance at a multi-week horizon.

### 4 News and text

#### Economic Policy Uncertainty and news-based trackers (FRED copies)

`epu_fred` · rank 3 · EV 40.0 (independence 4, history 5 verified, plausibility 2, effort 1)

* **Measures:** Newspaper-count indices: US daily EPU; Europe, Germany, Italy, UK monthly; US monetary-policy and trade-policy uncertainty; equity-market-volatility trackers by topic (incl. exchange rates).
* **Why it could matter over weeks:** Relative policy uncertainty US vs Europe is a risk-premium driver independent of rates and positioning.
* **Frequency / lag:** daily (US), monthly (others) / 1 day (US daily); about 1 month (monthly)
* **History verified:** USEPUINDXD 1985-01-01 .. 2026-11-10; EUEPUINDXM 1987-01 .. 2026-10; DEEPUINDXM 1993-01 .. 2026-10; EPUMONETARY and EPUTRADE 1985-01 .. 2026-09; EMVEXRATES 1985-01 .. 2026-10; WLEMUINDXD 1985 .. 2026-11-10. *How:* Downloaded each from FRED.
* **Cost:** free
* **URL pattern:** `https://fred.stlouisfed.org/graph/fredgraph.csv?id=USEPUINDXD (EUEPUINDXM, DEEPUINDXM, ITEPUINDXM, UKEPUINDXM, EPUMONETARY, EPUTRADE, EMVEXRATES, EMVMONETARYPOL, WLEMUINDXD)`
* **Hosts:** `fred.stlouisfed.org` · reachable today: yes
* **Format / size:** CSV, <0.3 MB each
* **GitHub copy:** none found
* **Pitfalls:** Monthly indices are revised and rescaled; no daily European index exists; France series absent on FRED.
* **Independence from positioning / 2y-spread trend / macro score:** High: built from newspaper text.

#### Geopolitical Risk index, daily (Caldara-Iacoviello), authors' GitHub

`gpr_github` · rank 5 · EV 33.8 (independence 4.5, history 5 verified, plausibility 1.5, effort 1)

* **Measures:** Share of newspaper articles about geopolitical threats and acts.
* **Why it could matter over weeks:** Safe-haven demand for dollars; Europe-centred shocks (Ukraine, energy) hit the euro.
* **Frequency / lag:** daily / about 1 week
* **History verified:** 1985-01-01 .. 2026-11-02 (15,281 rows). *How:* Downloaded the xls and read first/last rows.
* **Cost:** free
* **URL pattern:** `https://raw.githubusercontent.com/iacoviel/iacoviel.github.io/master/gpr_files/data_gpr_daily_recent.xls`
* **Hosts:** `raw.githubusercontent.com` · reachable today: yes
* **Format / size:** XLS, 3.3 MB (needs xlrd)
* **GitHub copy:** `https://raw.githubusercontent.com/iacoviel/iacoviel.github.io/master/gpr_files/data_gpr_daily_recent.xls` · range seen 1985-01-01 .. 2026-11-02
* **Pitfalls:** The log's own test of 'dollar as safe haven when stress is high and rising' was right 41 % of the time.
* **Independence from positioning / 2y-spread trend / macro score:** High.

#### San Francisco Fed Daily News Sentiment Index

`sf_fed_news_sentiment` · rank 8 · EV 26.7 (independence 4, history 5 verified, plausibility 2, effort 1.5)

* **Measures:** Sentiment of economics-related US newspaper articles.
* **Why it could matter over weeks:** High-frequency read of US growth sentiment ahead of the data.
* **Frequency / lag:** daily, published weekly / up to 1 week
* **History verified:** 1980-01-01 .. 2025-05-18 in a GitHub copy. *How:* Downloaded the copy (289 kB).
* **Claimed, not verified:** Official file is current (page showed an update of 2026-07-20 in search results).
* **Cost:** free
* **URL pattern:** `https://raw.githubusercontent.com/wattyven/VIX-study/main/sentiment/news_sentiment_data.csv (copy) ; official: https://www.frbsf.org/wp-content/uploads/news_sentiment_data.xlsx (not fetched)`
* **Hosts:** `raw.githubusercontent.com` · reachable today: yes
* **Format / size:** XLSX/CSV, 0.4 MB
* **GitHub copy:** `https://raw.githubusercontent.com/wattyven/VIX-study/main/sentiment/news_sentiment_data.csv` · range seen 1980-01-01 .. 2025-05-18
* **Pitfalls:** US only, no euro counterpart; the index is re-estimated so history changes between vintages; the copy is 18 months stale.
* **Independence from positioning / 2y-spread trend / macro score:** High.
* **Live continuation:** Live values need www.frbsf.org.

#### Central-bank text: BIS speeches archive, FOMC statements and minutes, ECB speeches

`central_bank_text` · rank 12 · EV 20.0 (independence 5, history 5 verified, plausibility 2, effort 2.5)

* **Measures:** Full text of central bankers' speeches (all central banks), FOMC statements and minutes, ECB speeches.
* **Why it could matter over weeks:** A hawkish-minus-dovish tone gap between Fed and ECB speakers is a direct, forward-looking version of the 'policy gap is widening' regime that is the log's one surviving lead.
* **Frequency / lag:** per speech (several a week) / 0-3 days
* **History verified:** BIS: yearly zips 1996 .. 2026 plus speeches.zip (129.5 MB, last modified 2026-08-23); the 2026 file holds 360 speeches dated 2026-01-08 .. 2026-06-22; RSS feed lists items dated 2026-11-10. FOMC: statements 2000-02-02 .. 2026-10-28 (227), minutes to 2026-09-16 (244). ECB copy: 1997-02-07 .. 2023-02-27 (2,661).. *How:* Downloaded the BIS 2026 zip (2 MB) and read the CSV; HEAD requests returned 200 for 1996 (66 kB), 2005, 2015, 2025 and the full zip, whose contents were not opened; downloaded the FOMC CSV (12 MB) and the ECB copy (52 MB).
* **Cost:** free
* **URL pattern:** `https://www.bis.org/pages/download-central-bankers-speeches/speeches-{YYYY}.zip ; https://www.bis.org/doclist/cbspeeches.rss ; https://raw.githubusercontent.com/vtasca/fed-statement-scraping/master/communications.csv ; https://media.githubusercontent.com/media/Moritz-Pfeifer/CentralBankRoBERTa/main/Data/ECB/all_ECB_speeches.csv ; official ECB file https://www.ecb.europa.eu/press/key/shared/data/all_ECB_speeches.csv (blocked)`
* **Hosts:** `www.bis.org`, `raw.githubusercontent.com`, `media.githubusercontent.com` · reachable today: yes
* **Format / size:** CSV in zip: 130 MB (BIS), 12 MB (FOMC), 52 MB (ECB copy)
* **GitHub copy:** `https://raw.githubusercontent.com/vtasca/fed-statement-scraping/master/communications.csv` · range seen 2000-02-02 .. 2026-10-28 (FOMC); ECB copy 1997-02-07 .. 2023-02-27
* **Pitfalls:** Needs a tone-scoring step (dictionary or language model) that must be fixed before looking at returns. BIS bulk file is rebuilt only every few months (use the RSS feed between builds) and carries the speech date, not the posting time. BIS covers a selection of speeches. One public test (Mingju-Zhang-CBS/financial-text-validation) found FOMC statement text added nothing to 20-day EUR/USD direction.
* **Independence from positioning / 2y-spread trend / macro score:** Highest of all candidates.

#### GDELT raw files through Google Cloud Storage

`gdelt_gcs` · rank 27 · EV 5.6 (independence 5, history 3 verified, plausibility 1.5, effort 4)

* **Measures:** Events (who did what to whom, with tone) and the Global Knowledge Graph (themes, organisations, tone per article).
* **Why it could matter over weeks:** Volume and tone of world news on the euro, ECB, Fed, sovereign stress.
* **Frequency / lag:** daily (v1), 15 minutes (v2) / same day
* **History verified:** Events: yearly/monthly files 1979 .. 2013-03 (7.7 GB) and daily 2013-04-01 .. 2026-11-10 (4,950 files, 45.2 GB); GKG v1 daily 2013-04-01 .. 2026-11-10 (170.2 GB; counts files 21.1 GB); v2 from 2015-02-18, latest file 2026-11-11 23:30. *How:* Read the bucket's own filesizes manifests and the v2 master list; HEAD on sample files.
* **Cost:** free
* **URL pattern:** `https://storage.googleapis.com/data.gdeltproject.org/gkg/{YYYYMMDD}.gkg.csv.zip ; .../events/{YYYYMMDD}.export.CSV.zip ; .../gdeltv2/masterfilelist.txt`
* **Hosts:** `storage.googleapis.com` · reachable today: yes
* **Format / size:** zipped TSV; 45 GB (events) or 170 GB (GKG) for the full history
* **GitHub copy:** none found
* **Pitfalls:** Very large: must be streamed and filtered, not stored. Source mix changes over time (tone drifts); article-level tone history starts 2013, under the BigQuery route it would be easier but bq has no credentials.
* **Independence from positioning / 2y-spread trend / macro score:** High.

#### GDELT DOC 2.0 API (ready-made tone and volume timelines)

`gdelt_doc_api` · rank 23 · EV 7.5 (independence 5, history 2 claimed, plausibility 1.5, effort 2)

* **Measures:** Daily tone / article-count series for any query.
* **Why it could matter over weeks:** Same as above without the 170 GB.
* **Frequency / lag:** daily / same day
* **History verified:** none (host blocked). *How:* Search only.
* **Claimed, not verified:** Start of the searchable window not confirmed (sources disagree: 3 months, 1 year, or from 2017).
* **Cost:** free
* **URL pattern:** `https://api.gdeltproject.org/api/v2/doc/doc?query=%22european%20central%20bank%22&mode=timelinetone&format=csv&startdatetime=YYYYMMDDHHMMSS&enddatetime=YYYYMMDDHHMMSS`
* **Hosts:** `api.gdeltproject.org` · reachable today: no
* **Format / size:** CSV, small
* **GitHub copy:** none found
* **Pitfalls:** One request per 5 seconds; history at best 2017 onward.
* **Independence from positioning / 2y-spread trend / macro score:** High.

#### Google Trends, Guardian / New York Times article APIs, Wikipedia page views

`news_apis_trends` · rank 21 · EV 10.0 (independence 4, history 5 claimed, plausibility 1.5, effort 3)

* **Measures:** Search interest and article counts/text for chosen terms.
* **Why it could matter over weeks:** Attention to 'euro crisis', 'ECB', 'Fed' as a crowding or risk signal; own text index back to 1999.
* **Frequency / lag:** daily to weekly / 1-3 days
* **History verified:** none (hosts blocked). *How:* Not verified.
* **Claimed, not verified:** Google Trends from 2004; Guardian archive from 1999; Wikipedia page views from 2015-07.
* **Cost:** free (API keys for Guardian and NYT)
* **URL pattern:** `https://trends.google.com/trends/api/widgetdata/multiline (unofficial) ; https://content.guardianapis.com/search?q=...&from-date=...&api-key=KEY ; https://api.nytimes.com/svc/search/v2/articlesearch.json ; https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/...`
* **Hosts:** `trends.google.com`, `content.guardianapis.com`, `api.nytimes.com`, `wikimedia.org` · reachable today: no
* **Format / size:** JSON
* **GitHub copy:** none found
* **Pitfalls:** Google Trends is sampled and re-normalised on every pull (history is not stable) and the unofficial API is rate-limited; article APIs need keys and have daily quotas.
* **Independence from positioning / 2y-spread trend / macro score:** High.

### 5 Vintages and nowcasts

#### ALFRED real-time vintages through the FRED API

`alfred_vintages_api` · rank 17 · EV 13.3 (independence 2, history 5 claimed, plausibility 2, effort 1.5)

* **Measures:** Every published vintage of US (and some euro-area) macro series, including the GDPNow series.
* **Why it could matter over weeks:** Removes revision look-ahead from the macro score; gives the day-by-day GDPNow path.
* **Frequency / lag:** as released / none
* **History verified:** Host answers: HTTP 400 'api_key is not set' (so it is reachable); no data pulled. *How:* curl to api.stlouisfed.org; separately confirmed that fredgraph.csv ignores vintage_date.
* **Claimed, not verified:** Vintages back to the 1990s for major series.
* **Cost:** free (registration for an API key)
* **URL pattern:** `https://api.stlouisfed.org/fred/series/observations?series_id=PAYEMS&realtime_start=YYYY-MM-DD&realtime_end=YYYY-MM-DD&file_type=json&api_key=KEY`
* **Hosts:** `api.stlouisfed.org` · reachable today: yes
* **Format / size:** JSON
* **GitHub copy:** none found
* **Pitfalls:** Needs the owner to register a free key (a secret, not a host change). alfred.stlouisfed.org itself is blocked.
* **Independence from positioning / 2y-spread trend / macro score:** Low: a hygiene fix for existing inputs rather than new information.

#### GDPNow full history, NY Fed Staff Nowcast, Philadelphia Fed ADS index and real-time data set

`nowcasts` · rank 31 · EV 4.5 (independence 2, history 3 claimed, plausibility 1.5, effort 2)

* **Measures:** Daily/weekly model nowcasts of US GDP and business conditions.
* **Why it could matter over weeks:** Growth differential in real time.
* **Frequency / lag:** daily to weekly / same day
* **History verified:** FRED GDPNOW holds only one value per quarter: 2011-Q3 .. 2026-Q4 (62 rows); WEI weekly 2008-01-05 .. 2026-10-31. *How:* Downloaded from FRED; other hosts blocked.
* **Claimed, not verified:** GDPNow from 2011/2014; NY Fed nowcast from 2016.
* **Cost:** free
* **URL pattern:** `https://www.atlantafed.org/-/media/documents/cqer/researchcq/gdpnow/GDPTrackingModelDataAndForecasts.xlsx ; https://www.newyorkfed.org/research/policy/nowcast ; https://www.philadelphiafed.org/surveys-and-data/real-time-data-research/`
* **Hosts:** `www.atlantafed.org`, `www.newyorkfed.org`, `www.philadelphiafed.org` · reachable today: no
* **Format / size:** XLSX
* **GitHub copy:** none found
* **Pitfalls:** US only (no free euro-area nowcast history); growth indicators already failed as a vote (round 5).
* **Independence from positioning / 2y-spread trend / macro score:** Low.

#### Flash PMI, ZEW, Ifo, Sentix headline releases with forecasts (already held)

`calendar_surveys_in_hand` · rank 26 · EV 6.0 (independence 1, history 4 verified, plausibility 1.5, effort 1)

* **Measures:** Actual, forecast and previous for each release, time-stamped.
* **Why it could matter over weeks:** First-release values without revision.
* **Frequency / lag:** monthly / none
* **History verified:** In data/macro/events.csv: flash manufacturing PMI 2010-01-21 .. 2026-09-23 (984 rows), ZEW from 2010-01-19, Ifo from 2010-01-26, Sentix from 2010-01-04. *How:* Counted rows in the project file.
* **Cost:** free
* **URL pattern:** `(local) data/macro/events.csv`
* **Hosts:** none · reachable today: yes
* **Format / size:** CSV
* **GitHub copy:** none found
* **Pitfalls:** Nothing to acquire: the paid S&P Global archive would add sub-indices only.
* **Independence from positioning / 2y-spread trend / macro score:** None (already used).

#### Citi Economic Surprise Index, US (GitHub copy)

`citi_surprise_copy` · rank 19 · EV 11.2 (independence 1.5, history 5 verified, plausibility 1.5, effort 1)

* **Measures:** Daily surprise index.
* **Why it could matter over weeks:** Benchmark for the project's own surprise index.
* **Frequency / lag:** daily / same day
* **History verified:** 2005-01-03 .. 2025-05-09. *How:* Downloaded (134 kB).
* **Cost:** free copy of paid data
* **URL pattern:** `https://raw.githubusercontent.com/Pj-354/Python-Notebooks--Mine-/main/Dispersion/GARCH%20MIDAS/Citi%20Suprise%20Economic%20Index%202005-2025.csv`
* **Hosts:** `raw.githubusercontent.com` · reachable today: yes
* **Format / size:** CSV, 0.13 MB
* **GitHub copy:** `https://raw.githubusercontent.com/Pj-354/Python-Notebooks--Mine-/main/Dispersion/GARCH%20MIDAS/Citi%20Suprise%20Economic%20Index%202005-2025.csv` · range seen 2005-01-03 .. 2025-05-09
* **Pitfalls:** US only, no euro series; stale; macro surprises already failed (round 3).
* **Independence from positioning / 2y-spread trend / macro score:** Low.

### 7 Other

#### sentix investor survey: EUR-USD sentiment (1 month) and strategic bias (6 months)

`sentix_fx_sentiment` · rank 13 · EV 18.8 (independence 5, history 5 claimed, plausibility 3, effort 4)

* **Measures:** Weekly survey of several thousand investors on the expected direction of EUR/USD.
* **Why it could matter over weeks:** The only long-running sentiment survey aimed at EUR/USD itself; short-term sentiment is contrarian, the 6-month 'strategic bias' is said by the provider to lead.
* **Frequency / lag:** weekly (Friday-Saturday poll) / Sunday/Monday
* **History verified:** none (host blocked). *How:* sentix pages found by search name the EUR-USD series (code SNTXEUN6) and weekly polling since 2001.
* **Claimed, not verified:** Weekly since 2001.
* **Cost:** free delayed data with registration; licence for timely data
* **URL pattern:** `https://www.sentix.de/index.php/en/ (data section after login)`
* **Hosts:** `www.sentix.de` · reachable today: no
* **Format / size:** CSV/XLS, small
* **GitHub copy:** none found
* **Pitfalls:** Login and manual export; licence terms for systematic use must be read; free series may be delayed.
* **Independence from positioning / 2y-spread trend / macro score:** High: neither futures positioning nor rates.

#### ZEW Financial Market Survey: share expecting the dollar to rise vs the euro

`zew_fx_expectations` · rank 29 · EV 5.0 (independence 5, history 2 claimed, plausibility 2, effort 4)

* **Measures:** Monthly balance of ~300 analysts on the 6-month dollar/euro direction.
* **Why it could matter over weeks:** Second survey of FX expectations.
* **Frequency / lag:** monthly / release day
* **History verified:** none (host blocked). *How:* Monthly result tables found by search for 2023-09 .. 2026-07.
* **Claimed, not verified:** Survey began December 1991; long series on request for researchers.
* **Cost:** free PDFs; research data set on request
* **URL pattern:** `https://download.zew.de/e_{MM}_{YYYY}_Tabelle.pdf`
* **Hosts:** `download.zew.de` · reachable today: no
* **Format / size:** PDF, one a month
* **GitHub copy:** none found
* **Pitfalls:** PDF scraping; long history only by request.
* **Independence from positioning / 2y-spread trend / macro score:** High.

#### US Treasury auction results (indirect bidders) and ICI weekly fund flows

`us_treasury_auctions_ici` · rank 22 · EV 9.0 (independence 4, history 3 claimed, plausibility 1.5, effort 2)

* **Measures:** Share of auctions taken by indirect (largely foreign) bidders; US fund flows into world equity and bond funds.
* **Why it could matter over weeks:** Foreign demand for dollar assets at higher frequency than TIC.
* **Frequency / lag:** per auction / weekly / same day / 1 week
* **History verified:** none (hosts blocked). *How:* Not verified.
* **Claimed, not verified:** Bidder data from about 2008; ICI weekly from 2007.
* **Cost:** free
* **URL pattern:** `https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v1/accounting/od/auctions_query ; https://www.ici.org/research/stats/flows`
* **Hosts:** `api.fiscaldata.treasury.gov`, `www.ici.org` · reachable today: no
* **Format / size:** JSON/XLS
* **GitHub copy:** none found
* **Pitfalls:** Indirect link to EUR/USD.
* **Independence from positioning / 2y-spread trend / macro score:** High.

## Checked and set aside

* **Risk reversals elsewhere:** no ECB Data Portal series, no replication package and no other GitHub copy with EUR/USD history was found; other hits are config files or studies that withhold the Bloomberg data.
* **CME FedWatch history:** GitHub trackers store only recent snapshots; history is a paid CME API.
* **ECB FX interventions (flow FXI):** reachable, daily 2000-09-01 to 2026-06-30, with five non-zero days (four in 2000, one in 2011).
* **Eurostat, OECD, DBnomics, Bundesbank, BIS data portal:** still blocked; nothing there is needed for the top of this list.
* **Hugging Face, Zenodo, Harvard Dataverse, Kaggle, archive.org:** blocked, so academic replication packages could only be searched on GitHub.
* **GDELT on BigQuery:** `bq` has no credentials in this sandbox.
