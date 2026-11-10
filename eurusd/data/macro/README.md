# Macro / positioning / calendar / intermarket data for EUR/USD

Everything here is produced by `eurusd/src/eurusd/macro_fetch.py` (run `python -I eurusd/src/eurusd/macro_fetch.py all`,
or one of `ecb | yahoo | mirrors | cftc | calendar`; `--offline` rebuilds from `eurusd/data/raw/` without network).
All files are plain CSV. Dates are ISO (`YYYY-MM-DD`, `YYYY-MM` for monthly); timestamps are UTC with a `Z` suffix.
Built 2026-11-10. Raw downloads live in `eurusd/data/raw/` (CFTC zips are git-ignored, ~43 MB, re-fetched on demand).

Network notes (2026-11-10, via the policy proxy): reachable: `data-api.ecb.europa.eu`, `www.cftc.gov` (Python
`requests` only; curl gets a Cloudflare challenge), `raw.githubusercontent.com`, `nfs.faireconomy.media`,
`en.wikipedia.org`, `query1/2.finance.yahoo.com` (rate-limited, HTTP 429 all afternoon). Blocked (CONNECT 403):
`fred.stlouisfed.org`, `stooq.com`, `www.federalreserve.gov`, `www.ecb.europa.eu`, `www.cmegroup.com`,
`www.bls.gov`, `www.bea.gov`, `publicreporting.cftc.gov`, `data.bis.org` (www.bis.org redirects there).

## 1. ECB Data Portal (official, fresh)

Source: `https://data-api.ecb.europa.eu/service/data/<FLOW>/<KEY>?format=csvdata`. Keys verified to return data.

| file | rows | range | content / keys |
|---|---|---|---|
| `ecb_policy_rates.csv` | 10176 | 1999-01-01..2026-11-10 (daily, incl. weekends) | `deposit_facility_rate` (FM.D.U2.EUR.4F.KR.DFR.LEV), `main_refinancing_rate` = fixed-rate MRO (FM...MRR_FR.LEV) with the 2000-06..2008-10 minimum-bid rate (FM...MRR_MBR.LEV) filled in, `marginal_lending_rate` (FM...MLFR.LEV). Percent. Level changes on the effective date, not the announcement date. |
| `ea_aaa_yield_curve.csv` | 5670 | 2004-09-06..2026-11-09 (business days) | Euro area AAA government spot rates, Svensson fit: `aaa_spot_3m/1y/2y/5y/10y/30y` (YC.B.U2.EUR.4F.G_N_A.SV_C_YM.SR_*). Percent. |
| `ea_hicp.csv` | 360 | 1996-01..2025-12 (monthly) | `hicp_yoy` (ICP.M.U2.N.000000.4.ANR), `hicp_core_yoy` ex energy & food (ICP.M.U2.N.XEF000.4.ANR), `hicp_index` 2015=100. **Stale: the ECB ICP flow stops at 2025-12 for both the U2 and I9 reference areas** (euro-area composition changed 2026-01); use `fred_CP0000EZ19M086NEST.csv` (index to 2026-09) and diff it for 2026 y/y. The full-range ANR request 504s at the ECB; the script uses `startPeriod=1990-01`. |
| `ea_unemployment.csv` | 321 | 2000-01..2026-09 | Euro area unemployment rate, SA, 15-74 (LFSI.M.I9.S.UNEHRT.TOTAL0.15_74.T). Percent. |
| `ea_overnight_rates.csv` | 7132 | 1999-01-04..2026-11-09 | `eonia` (EON.D.EONIA_TO.RATE, discontinued 2021-12-31) and `estr` (EST.B.EU000A2X2A25.WT, from 2019-10-01). Percent. |

EUR/USD ECB reference rate is deliberately not here (fetched by the price-data pipeline).

## 2. US / intermarket daily series via FRED mirrors on GitHub (FRED itself is unreachable)

`fred_<SERIES>.csv`, columns `date,value`. `fred_mirror_catalog.csv` lists every series with description, frequency,
mirror URL, rows and first/last date. Mirrors (all checked 2026-11-10):

* `mfenickfau/econ-dashboards` (`data/<S>.csv`, repo pushed 2026-11-06; daily series end 2026-11-04/05, monthly end 2026-09/10):
  DGS2, DGS10, DGS30, T10Y2Y, T10Y3M, FEDFUNDS, DTWEXBGS, CPIAUCSL, CPILFESL, PCEPI, PCEPILFE, PAYEMS, UNRATE, ICSA,
  CES0500000003, JTSJOL, INDPRO, RSAFS, HOUST, GDPC1, M2SL, BOPGSTB, MORTGAGE30US, VIXCLS, SP500 (FRED's 10-year window
  only, from 2016-11), NASDAQCOM, GASREGW, PPIACO, SAHMREALTIME, CP0000EZ19M086NEST (EA HICP index), LRHUTTTTDEM156S (DE unemployment).
* `cool1990/invest-dashboard_v1` (`data/series/<S>.csv`, pushed 2026-11-10, **2022-01 onward only**): EFFR, SOFR, IORB,
  T10YIE, DFII10, BAMLH0A0HYM2, WALCL, RRPONTSYD, WRESBAL, STLFSI4, ANFCI.
* `maybern-tripp-smith/fedjev-bench` (`data/raw/fred/<S>.csv`, pushed 2026-09-21, data to 2026-09): NFCI, DFEDTAR
  (single target to 2008-12-15), DFEDTARL/DFEDTARU (target range from 2008-12-16).

Caveats: these are third-party copies; values were spot-checked for plausibility only (e.g. DGS10 4.90 on 2026-11-04,
FEDFUNDS 3.88 for 2026-10). No 2-year *yield* history beyond DGS2 exists on Yahoo; see section 3 for ZT=F.

## 3. Yahoo Finance (daily OHLCV, hourly for six symbols)

`yahoo_<symbol>_daily.csv` (`date,open,high,low,close,volume`; `date` is the exchange-local session date) and
`yahoo_<symbol>_1h.csv` (`datetime_utc,...`, last 730 days). Symbols: ^IRX ^FVX ^TNX ^TYX DX-Y.NYB 6E=F ZT=F GC=F CL=F
^GSPC ^VIX ^STOXX50E ^GDAXI EURJPY=X EURGBP=X GBPUSD=X USDJPY=X USDCHF=X AUDUSD=X EURCHF=X BTC-USD; hourly: DX-Y.NYB
6E=F ^GSPC GC=F EURGBP=X USDJPY=X. `ZT=F` is the CME 2-year T-note *futures* price, not a yield (no reliable Yahoo
2y-yield symbol; use `fred_DGS2.csv`). Yahoo FX `=X` daily bars are poor-quality (open often equals previous close).
Per-symbol outcome is written to `yahoo_status.json`. **Status at build time: see the bottom of this file.**

## 4. datahub.io (`datasets/*` GitHub org) extras

`datahub_*.csv`; raw URLs are `raw.githubusercontent.com/datasets/<repo>/master/data/<file>` (the `main` ref 404s).

| file | rows | range | content |
|---|---|---|---|
| `datahub_brent_daily.csv` / `datahub_wti_daily.csv` | 9122 / 9537 | 1987/1986..2026-11-03 | EIA spot $/bbl (`date,price`) |
| `datahub_vix_daily.csv` | 9278 | 1990-01-02..2026-09-22 | VIX OHLC (stale 7 weeks; `fred_VIXCLS` is current) |
| `datahub_gold_monthly.csv` | 2326 | 1833-01..2026-10 | gold $/oz monthly avg |
| `datahub_euribor_1w/3m/12m.csv` | 334/334/154 | 1999..2026-10-01 | Euribor, monthly observations |
| `datahub_us10y_monthly.csv` | 882 | 1953-04..2026-09 | US 10y monthly (Fed H.15) |
| `datahub_cpi_us.csv` | 1364 | 1913-01..2026-09 | US CPI index and m/m inflation |
| `datahub_fx_fed_h10_daily.csv` | 14570 | 1971-01-04..2026-11-06 | Fed H.10 noon NY rates, all converted by datahub to foreign units per USD (`eur_per_usd`, `gbp_per_usd`, `aud_per_usd`, `jpy_per_usd`, `chf_per_usd`, `cad_per_usd`; EUR/USD = 1/eur_per_usd) |

## 5. CFTC Commitments of Traders, CME EURO FX futures (contract code 099741)

Raw: `https://www.cftc.gov/files/dea/history/fut_fin_txt_YYYY.zip` (TFF, 2010-2026) and `deacotYYYY.zip` (legacy
futures-only, 1999-2026), stored under `eurusd/data/raw/cftc/`, parsed only. Report date = Tuesday position date;
published the following Friday 15:30 ET (3-day lag matters for backtests).

* `cot_eurofx_tff.csv` (851 weekly rows, 2010-07-20..2026-11-03): `open_interest`, long/short for `dealer`, `asset_mgr`,
  `lev_funds`, `other_rept`, `nonrept`, `traders_total`, plus `<group>_net` and `<group>_net_pct_oi` (net / OI * 100).
* `cot_eurofx_legacy.csv` (1453 weekly rows, 1999-01-05..2026-11-03): `noncomm_long/short/spread`, `comm_long/short`,
  `nonrept_long/short`, nets and net-%-OI. The 1999..mid-2000 files name the contract "EURO FX - INTERNATIONAL MONETARY
  MARKET"; same code. Open interest matches the TFF file week for week on the overlap (851/851).

Contract = EUR 125,000; positive net = long EUR vs USD. E-mini and EUR cross-rate contracts excluded.

## 6. Economic calendar

### `events.csv` (70,332 rows, 1989..2027) and `events_high_eur_usd.csv` (High-impact USD/EUR rows with a time)
Columns: `datetime_utc, currency, event, impact, actual, forecast, previous, source, has_time`. `has_time=False` rows
are all-day/tentative items stamped 00:00Z on their calendar date. `source` codes:

| code | rows | what / timezone handling | quality |
|---|---|---|---|
| `ff_archive_2010_2023` | 65,276 | ForexFactory calendar 2010-01..2023-12 with actual/forecast/previous, mirror `spoluan/forex-factory-scraper` (`datasets/forex_factory_calendar_<year>.csv`, master, pushed 2024-08). Scraped in a fixed UTC+8 display zone: NFP shows 8:30pm (US summer) / 9:30pm (US winter) = 12:30/13:30Z, FOMC statements convert to 18:00/19:00Z (18:15/19:15Z pre-2013, 16:30Z for 2011-12 press-conference meetings), ECB to 11:45/12:45Z - all consistent, so `datetime_utc = displayed - 8h`. Years 2009 and 2024+ not in the mirror. | good |
| `ff_2025q4_snapshot` | 126 | ForexFactory Oct-Dec 2025 (CryptoPrism-io export of 2025-11-08, IST display zone converted). Mostly without actuals. | ok |
| `ff_2026_fxdesk_lowq` | 3,129 | ForexFactory Jan-Sep 2026 incl. actuals, mirror `datpro12345/fx-desk`. Display zone assumed UTC+7 (NFP/ECB rows convert correctly to 13:30Z/13:15Z) but FOMC/CPI rows do not, so **treat times as +/- hours; dates and values are fine**. | low (times) |
| `ff_2026_cwt` | 107 | ForexFactory Apr-Oct 7 2026, high-impact USD subset with actuals (`Gourav232003/cwt-macro-pipeline` raw JSON, America/New_York). | good |
| `ff_live_thisweek` | 105 | `https://nfs.faireconomy.media/ff_calendar_thisweek.json` fetched 2026-11-10 (week of Nov 8-14 2026; ISO timestamps with offset). `nextweek`/`lastweek` returned 404. Raw JSON kept in `data/raw/ff/`. | good |
| `fomc_decisions:*`, `ecb_decisions:*`, `us_bls_releases:*` | ~1,500 | the verified lists below, appended so one file covers everything (`actual` = fed funds target / DFR after meeting where known) | see below |

Coverage gaps: 2009, 2024-01..2025-09, 2025-12-03..2025-12-31 and 2026-10-08..2026-11-07 have no ForexFactory rows
(structured central-bank / BLS rows still cover those periods).

### `fomc_decisions.csv` (329 rows, 1989-07-07..2027-12-08)
`date, statement_utc, time_quality, scheduled, has_sep, status, chair, fed_funds_target, discount_rate, votes,
in_hillenbrand_meeting_list, in_wikipedia_actions_table, note`.
* `time_quality=verified:*` (140 dates, 2008-12..2026-03): release time taken from the Fed statement / press-conference
  page by F. Pinna (`francescopinna03/Monetary_surprises_and_volatility`, `Raw/Certification/fomc_calendar_verified.csv`,
  repo pushed 2026-11-10). Includes 12:30 ET releases for the 2011-2013 press-conference meetings.
* `rule:14:00ET(gcmbo)` (2017..2026-12, `Vrushabh43/GC-MBO-ML` events_fomc.csv built from the Fed calendar pages) and
  `rule:14:15ET` / `rule:14:00ET`: date from the merged lists, time by rule (14:15 ET before March 2013, 14:00 ET after).
  Intermeeting/emergency actions (e.g. 2001-01-03, 2020-03-15 which was really 17:00 ET) carry rule times - check `note`.
* Dates: Hillenbrand (2021) scheduled-meeting list 1989-2024 (`yildirimalper/yildirim-masters-thesis` fed_mpd.csv),
  `fedjev-bench` meetings 2011-2026-09 (scheduled/SEP/chair flags), `aansensei/macro-event-lab` seed 2021-2027
  (`status=tentative` for future meetings), and the Wikipedia "History of FOMC actions" table 2000-02..2026-10
  (target, discount rate, votes; raw HTML in `data/raw/wikipedia/`). `scheduled=False` rows are conference calls /
  unscheduled actions.

### `ecb_decisions.csv` (321 rows, 1999-03-04..2026-12-17)
`date, decision_utc, press_conference_utc, time_quality, in_ecb_decision_list_1999_2024, dfr_after, mrr_after`.
* `verified(pinna)` 2000-01..2012-12 (press release and press conference times from ecb.europa.eu pages, 358 phases) and
  `registry(pinna)` 2013-01..2026-03-19 (same author's event registry) - both already reflect the July 2022 move of the
  decision from 13:45 to 14:15 CET and the press conference from 14:30 to 14:45 CET.
* 1999 and 2026-04..2026-12: dates from the 1999-2024 decision list (`ecb_mpd.csv`, gathered from ecb.europa.eu) and, for
  2026, from the ForexFactory 2026 rows (Apr 30, Jun 11, Jul 23, Sep 10 confirmed) plus Oct 29 and Dec 17 from the ECB's
  published 2026 schedule **as remembered, not verified online** (ecb.europa.eu is blocked). Times by rule.
* `dfr_after`/`mrr_after`: level of the deposit / main refinancing rate 7 days after the meeting, from `ecb_policy_rates.csv`.
  Rows before 2001 include the twice-monthly meetings that did not all carry decisions.

### `us_bls_releases.csv` (618 rows, 2010-01-08..2026-12-15)
`release_utc, release (Employment Situation | CPI | PPI), source, time_quality`.
* `verified(bls schedule archive)` 2017-01..2026-12: taken from archived bls.gov schedule pages (web.archive.org) by
  `Vrushabh43/GC-MBO-ML` (`data/calendar/events_bls.csv`). All at 08:30 ET = 12:30/13:30Z. 2026 dates were fetched from
  the schedule as published mid-2026; shutdown-related postponements after that are not reflected.
* `ff-archive(unverified)` 2010-01..2016-12: the "Non-Farm Employment Change", "CPI m/m", "PPI m/m" USD rows of the
  ForexFactory archive above (converted from UTC+8). These are observed dates, not the first-Friday rule, so they do
  capture the irregular releases (e.g. 2013-10-22 NFP after the shutdown).
No official US CPI/NFP list before 2010 was reachable; bls.gov and bea.gov are blocked.

## 7. What was tried and failed / not available
* FRED, stooq, Dukascopy, Fed, ECB website, CME, BLS, BEA, BIS data portal, CFTC Socrata API: blocked by the proxy policy.
* ECB HICP (ICP flow) is stale at 2025-12 (see section 1). `EST` and `ICP` full-range requests intermittently 504.
* Yahoo Finance answered HTTP 429 "Edge: Too Many Requests" to every request from this host between 17:55 and 18:30
  UTC on 2026-11-10 (no browser UA spoofing was attempted). The script retries with backoff; see status below.
* EA-MPD (Altavilla et al. ECB surprise dataset) is only on ecb.europa.eu; no GitHub mirror found.
* ForexFactory `nextweek`/`lastweek` feeds returned 404 on 2026-11-10.
* The `datasets/employment-us`, `gdp-us`, `investor-flow-of-funds-us` repos are stale (2018-2025) and were not kept.

## Yahoo status at build time
(filled in by the final run; also machine-readable in `yahoo_status.json`)
