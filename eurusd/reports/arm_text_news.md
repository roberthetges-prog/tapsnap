# Arm Z - text_news: central-bank tone, news sentiment, uncertainty and policy surprises as a 1-3 month vote (round 7)

Code `src/eurusd/arms/text_news.py` (`run(cost_pips=1.2)`; `PYTHONPATH=src python -m eurusd.arms.text_news` fetches (cached, resumable), scores the
texts, runs everything incl. leak checks and writes this report in about 8 minutes on one core; `... text_news report` rebuilds this file from the saved
tables). Outputs in `experiments/results/arms/`: `text_news_positions.parquet` (daily stream of the final rule: `pos`, `fwd_bp`, `net_bp`),
`text_news_report.csv` (protocol table, 12 candidates + the agreement-rule book, `variant`, `final`), `text_news_votes.csv` (every signal x rule x horizon x
mode x period cell, incl. placebo, orthogonalised, re-dated and other-era rows), `text_news_paired.csv`, `text_news_bar.csv`, `text_news_candidates.csv`,
`text_news_incremental.csv`, `text_news_leakchecks.csv`, `text_news_doc_counts.csv`, `text_news_signals.parquet`, log `logs/text_news.log`. Series for the
weekly outlook in `data/macro/`: **`text_news_tone_daily.csv`** (calendar-daily Fed, ECB and relative tone, document counts, z-scores, 1- and 3-month
changes), `text_news_signals_daily.csv` (the 12 signals on the session grid), `text_news_docs.csv` (one row per scored document, no text),
`text_news_sentiment_daily.csv`, `text_news_epu_monthly.csv`, `text_news_epu_us_daily.csv`, `text_news_gpr_daily.csv`, `text_news_jk_shocks.csv`,
`text_news_sources.csv`. Raw downloads (BIS zips, FOMC CSV, ECB copy, live BIS pages) are in `data/raw/text_news/` (git-ignored).

The dictionary, the 12 signals with their signs, the lags, the evaluation and the selection rule were written into the module docstring before any
accuracy number existed. Nothing was changed afterwards: three bugs found on the way were all in data handling and were fixed before the first
evaluation or without reference to it (one-word sentences skipped by the scorer; BIS pages that carry only an abstract, where the speech is now read
from the PDF; duplicate speeches between the bulk file and the live listing).

## Verdict

**The Round 5 bar is NOT met by any of the 12 candidates. Text and news add no vote to the agreement rule.** The largest class of information the
project had never touched turns out to be new (it is nearly uncorrelated with everything we hold) and uninformative about EUR/USD one to three months
ahead.

1. **Central-bank tone - the measurement works, the forecast does not.** The frozen dictionary gives a tone series with face validity (Fed: low in
   2001, 2008-09, 2020, high in 2005-06, 2017-18, 2022-23; ECB: high in 2005-08 and 2022, low in 2013-16; table in section 1) and the ECB series built
   from the BIS selection correlates 0.91 with the same score on the ECB's own complete speech file. As a predictor:
   * *Level of the relative tone* (`tone_rel_lvl`): right 55 / 57 / 51 % at 21 / 42 / 63 sessions (non-overlapping, n = 207 / 103 / 69, 2010-26),
     49 / 55 / 45 % since 2016, 46 / 45 / 33 % since 2023. All of it is 2010-15 (64 / 61 / 60 %, n = 75 / 38 / 25): the signal says "Fed more hawkish than
     its own norm, relative to the ECB" on 77 % of sessions, i.e. it was a standing short-euro position through the 2014-15 fall. Made 63 or 126 sessions
     stale it scores the same (54 / 53 % at 21 sessions): a regime bet, not information.
   * *Changes in the relative tone* over one and three months (`tone_rel_d1m`, `tone_rel_d3m`), the form the "communication moves pricing before the
     turn" idea needed: 49 / 46 / 52 % and 50 / 47 / 58 % (2010-26), 48 / 55 / 50 % and 49 / 43 / 55 % since 2016. Chance.
   * Dated by the BIS posting date instead of the speech date (median 3 days later) the numbers are the same within noise.
2. **US news sentiment** (SF Fed index, copy to 2025-05): 48 / 52 / 50 % (level), 48 / 48 / 39 % (1-month change). Nothing; and it cannot run live from the
   copy.
3. **Uncertainty.** Europe-minus-US policy uncertainty rising: 51 / 48 / 48 %. Geopolitical risk rising: 47 / 57 / 49 % (it was 59 / 66 / 56 % in 2004-09
   and did not carry over). US trade-policy uncertainty with the sign taken from the training window: **41 / 40 / 48 %** - the sign that fitted the past
   was wrong afterwards (the fitted orientation flipped in 2011, 2013, 2023 and 2026): there is no stable relation to learn.
4. **Policy surprises (the owner's rate-cycle idea in its market-surprise form).** Cumulated Fed-minus-ECB *pure policy* shocks: 46 / 54 / 50 % over three
   months, 47 / 49 / 53 % over six (2010-26), 30-35 % at 21 sessions in 2023-26, and as an extra vote they LOWER the agreement rule by 7 points at 21
   sessions. Consistent with arm T: what the central bank does, even the part the market did not expect, is in the price within days.
   The *information* shocks over six months (`jk_cbi_6m`) are the one lead of the arm: 55 / 55 / 56 % standalone in 2010-26, 60 / 61 / 66 % since 2016
   (n = 123 / 61 / 41); as an extra vote +6.3 / +4.3 points in 2010-26 (65 % n=95, 65 % n=60), +13.4 / +12.1 in 2016-26 (71 % n=58, 71 % n=38), not worse in
   2023-26. It does not pass, and it should not be believed yet: (i) 5.7 and 5.4 decisions a year where the bar needs 6; (ii) the placebo keeps more than
   half of the gain in two of eight cells (2016-26: +7.2 of +13.4 when 126 sessions stale at 21 sessions, +6.8 of +12.1 when 63 stale at 42); (iii) it was
   45 / 45 / 40 % standalone in 2010-15 (n = 75 / 38 / 25) and 51 / 55 / 52 % in 2004-09, so the whole effect is 2016-25; (iv) removing the five controls takes
   the 2010-26 21-session gain from +7 to +2 points; (v) it is the best of 12 candidates, its prior was written down as WEAK before the results (the opposite
   sign was called "as respectable"), and it ranks 7th of 12 on the declared selection statistic; the paired bootstrap gives p = 0.17 (2010-26) and 0.02
   (2016-26) at 21 sessions before any allowance for 12 candidates; (vi) the ECB shock file lags by months, so the signal has been undefined since
   2025-12-29 and cannot vote today. A lead for a forward test once the authors update the ECB file, nothing more.
5. **Final by the declared rule: `tone_rel_lvl`, and it fails every component of the bar.** AND rule against the agreement rule, non-overlapping:
   57 % (n=101) vs 59 % at 21 sessions and 66 % (n=62) vs 61 % at 42 in 2010-26 (-1.5 / +5.5 points); -2.1 / +5.0 in 2016-26; -8.0 / +1.7 in 2023-26;
   6.0 and 5.4 decisions a year; the 42-session gain is fully kept by the stale signal (+4.9 / +6.6 in 2010-26, +7.7 / +10.8 in 2016-26). Hit rate of its weekly
   decisions (correct sign = positive net P&L to within one decision): 61 % (n=246) / 56 % (n=135) / 48 % (n=50) for 2010-26 / 2016-26 / 2023-26. Daily book:
   net Sharpe 0.49 / 0.38 / 0.01 (t 2.0 / 1.3 / 0.0; deflated-Sharpe p 0.35 for 12 candidates) against 0.52 / 0.51 / 0.43 for the agreement-rule book it is a
   subset of (daily P&L correlation 0.84). Three-way combination 0.60 / 0.63 / 0.28 against 0.56 / 0.64 / 0.36 for the two live streams: worse where it
   matters. The Round 3 bar fails as well.
6. **Round 7 controls: the signals are new, they are not price in disguise - and that does not help.** Trailing 1- and 3-month returns explain 0-7 % of
   any signal's variance, all five controls 1-13 % (highest: the policy-surprise sums, which load on positioning and the spread trend, as the scoping note
   expected). Standalone accuracy after orthogonalising stays within a few points of the raw number for every signal (section 6). Being uncorrelated with
   what we have is necessary, not sufficient.
7. **Leak checks pass** (section 10): permuted labels put every standalone rule at chance; a 21-session look-ahead does not improve anything materially;
   the row of five dates rebuilt from raw data truncated at that date is identical for all 12 signals.

**What to keep.** `data/macro/text_news_tone_daily.csv` as a CONTEXT panel for the weekly outlook ("how hawkish does each bank sound against its own
history"), never as a vote. Current reading in section 11. `jk_cbi_6m` as a named control in the paper forward test if and when the ECB shock file is
current. Variants tried: 12 (deflate by 12; none survives without deflation either).

## 1. Data: sources, spans, publication lags
| series                                                      |   rows | first      | last       | lag used                       | fetched    | file                                     |
|:------------------------------------------------------------|-------:|:-----------|:-----------|:-------------------------------|:-----------|:-----------------------------------------|
| FED fomc_statement (fomc_csv)                               |    227 | 2000-02-02 | 2026-10-28 | release date + 1 d             | 2026-11-11 | data/macro/text_news_docs.csv            |
| FED fomc_minutes (fomc_csv)                                 |    244 | 2000-03-23 | 2026-10-07 | release date + 1 d             | 2026-11-11 | data/macro/text_news_docs.csv            |
| FED speech (bis_bulk)                                       |   2486 | 1996-12-19 | 2026-06-22 | speech date + 1 d              | 2026-11-11 | data/macro/text_news_docs.csv            |
| ECB speech (bis_bulk)                                       |   2643 | 1997-02-07 | 2026-06-22 | speech date + 1 d              | 2026-11-11 | data/macro/text_news_docs.csv            |
| FED speech (bis_live)                                       |     26 | 2026-06-24 | 2026-10-14 | speech date + 1 d              | 2026-11-12 | data/macro/text_news_docs.csv            |
| ECB speech (bis_live)                                       |     28 | 2026-06-30 | 2026-11-05 | speech date + 1 d              | 2026-11-12 | data/macro/text_news_docs.csv            |
| ECB_COPY speech (ecb_copy)                                  |   2603 | 1997-02-07 | 2023-02-16 | cross-check only               | 2026-11-11 | data/macro/text_news_docs.csv            |
| SF Fed Daily News Sentiment (third-party copy, one vintage) |  16556 | 1980-01-01 | 2025-05-18 | 7 d                            | 2026-11-11 | data/macro/text_news_sentiment_daily.csv |
| FRED USEPUINDXD                                             |  15289 | 1985-01-01 | 2026-11-10 | monthly mean, month-end + 30 d | 2026-11-11 | data/macro/text_news_epu_us_daily.csv    |
| FRED EUEPUINDXM                                             |    478 | 1987-01-01 | 2026-10-01 | month-end + 30 d               | 2026-11-11 | data/macro/text_news_epu_monthly.csv     |
| FRED EPUTRADE                                               |    501 | 1985-01-01 | 2026-09-01 | month-end + 45 d               | 2026-11-11 | data/macro/text_news_epu_monthly.csv     |
| FRED EPUMONETARY                                            |    501 | 1985-01-01 | 2026-09-01 | not used as a candidate        | 2026-11-11 | data/macro/text_news_epu_monthly.csv     |
| Geopolitical Risk index, daily (Caldara-Iacoviello)         |  15281 | 1985-01-01 | 2026-11-02 | 7 d                            | 2026-11-11 | data/macro/text_news_gpr_daily.csv       |
| Jarocinski-Karadi shocks, FED                               |    334 | 1990-02-08 | 2026-09-16 | announcement date + 1 d        | 2026-11-11 | data/macro/text_news_jk_shocks.csv       |
| Jarocinski-Karadi shocks, ECB                               |    312 | 1999-01-07 | 2025-10-30 | announcement date + 1 d        | 2026-11-11 | data/macro/text_news_jk_shocks.csv       |

URLs: `https://raw.githubusercontent.com/vtasca/fed-statement-scraping/master/communications.csv`; `https://www.bis.org/pages/download-central-bankers-speeches/speeches-{y}.zip`; `https://www.bis.org/speeches/central-bank`; `https://media.githubusercontent.com/media/Moritz-Pfeifer/CentralBankRoBERTa/main/Data/ECB/all_ECB_speeches.csv`; `https://raw.githubusercontent.com/wattyven/VIX-study/main/sentiment/news_sentiment_data.csv`; `https://fred.stlouisfed.org/graph/fredgraph.csv?id=USEPUINDXD`; `https://fred.stlouisfed.org/graph/fredgraph.csv?id=EUEPUINDXM`; `https://fred.stlouisfed.org/graph/fredgraph.csv?id=EPUTRADE`; `https://fred.stlouisfed.org/graph/fredgraph.csv?id=EPUMONETARY`; `https://raw.githubusercontent.com/iacoviel/iacoviel.github.io/master/gpr_files/data_gpr_daily_recent.xls`; `https://raw.githubusercontent.com/marekjarocinski/jkshocks_update_fed/main/shocks_fed_jk_t.csv`; `https://raw.githubusercontent.com/marekjarocinski/jkshocks_update_ecb/main/shocks_ecb_mpd_me_d.csv`

All files fetched 2026-11-11 / 12. Third-party copies (FOMC scrape, ECB speeches copy, SF Fed copy) are research-only. Cross-checks that were possible from
this sandbox: the ECB tone from the BIS selection against the ECB's complete file (below); FOMC release dates are internally consistent (statements on the
meeting day, minutes 21 days later from 2005 and 37-50 days later before, as the Fed's practice was); the BIS URL of every bulk speech carries the posting
date, which gives the delay table below. Not possible: comparing the SF Fed copy with the official file (www.frbsf.org blocked) or the FOMC scrape with
www.federalreserve.gov (blocked).

Gaps and pitfalls:
* **BIS coverage is a selection.** ECB: 30-60 speeches a year to 2006, 90-170 in 2007-20, 60-75 since 2021; Fed (incl. FOMC texts): 60-80 documents a
  year to 2003, 75-135 since. Of the ECB press-conference statements the archive holds 7-13 a year in 2004-21 but only 4-7 a year since 2022. The bulk file (build of 2026-08-23) ends with speeches of 2026-06-22; later Fed and
  ECB speeches come from the BIS listing pages (`bis_live`: HTML text, or the PDF where the page has only an abstract), which reach 2026-11-05 for the ECB
  and 2026-10-14 for the Fed. www.bis.org cuts long transfers: the fetch resumes until every zip passes its CRC test.
* **Only about two thirds of the speeches carry a tone** (at least 5 dictionary hits); the rest are about payments, supervision, digital money etc. and
  are ignored. 156 of 227 FOMC statements pass (the short ones of 2000-08 and some recent ones have fewer than 5 hits); all 244 minutes do.
* **The 30-day relative tone is undefined on 20 % of sessions** (fewer than two scored documents of one bank in the window: August, blackout periods,
  the thin early ECB years); the 90-day tone on 1 %.
* **SF Fed sentiment**: one vintage of a re-estimated index (not real-time), ends 2025-05-18: both news signals are undefined from 2025-06.
* **EPU**: the monthly indices are revised and rescaled (current vintage used); Europe is monthly only, so the relative signal is monthly with a 30-day lag.
* **JK shocks**: the first principal component is scaled on the full sample (units, not signs); the ECB file ends 2025-10-30, so all four surprise
  signals are undefined from 2025-12-29 (60 days after the last row).

**Documents per institution per year** (all documents, then those with at least 5 dictionary hits = the ones that enter the tone; mean tone of the year)

|   year |   ECB speech (BIS) |   ECB speech (ECB copy) |   Fed FOMC minutes |   Fed FOMC statement |   Fed speech |   Fed all |   Fed scored |   ECB (BIS) scored |   Fed mean tone |   ECB mean tone |
|-------:|-------------------:|------------------------:|-------------------:|---------------------:|-------------:|----------:|-------------:|-------------------:|----------------:|----------------:|
|   1996 |                  0 |                       0 |                  0 |                    0 |            1 |         1 |            0 |                  0 |          nan    |          nan    |
|   1997 |                  2 |                      19 |                  0 |                    0 |           59 |        59 |           26 |                  2 |            0.1  |            0.3  |
|   1998 |                 10 |                      46 |                  0 |                    0 |           50 |        50 |           20 |                  6 |            0.04 |           -0.37 |
|   1999 |                 46 |                     105 |                  0 |                    0 |           47 |        47 |           17 |                 36 |            0.07 |            0.07 |
|   2000 |                 45 |                      74 |                  7 |                    8 |           47 |        62 |           37 |                 34 |            0.37 |            0.52 |
|   2001 |                 37 |                      73 |                 13 |                   11 |           51 |        75 |           43 |                 25 |           -0.14 |            0.07 |
|   2002 |                 40 |                      66 |                  8 |                    8 |           59 |        75 |           39 |                 28 |           -0.06 |            0.04 |
|   2003 |                 31 |                      71 |                 13 |                    8 |           58 |        79 |           51 |                 23 |           -0.21 |           -0.25 |
|   2004 |                 60 |                     104 |                  8 |                    8 |          105 |       121 |           87 |                 40 |            0.04 |            0.08 |
|   2005 |                 51 |                      91 |                  8 |                    8 |          100 |       116 |           78 |                 39 |            0.09 |            0.32 |
|   2006 |                 59 |                     105 |                  8 |                    8 |           90 |       106 |           59 |                 50 |            0.22 |            0.42 |
|   2007 |                 88 |                     127 |                 10 |                   10 |           98 |       118 |           76 |                 62 |           -0.03 |            0.29 |
|   2008 |                150 |                     142 |                 15 |                   11 |           94 |       120 |           77 |                 85 |           -0.23 |            0.15 |
|   2009 |                129 |                     119 |                 11 |                    8 |           81 |       100 |           73 |                 84 |           -0.51 |           -0.5  |
|   2010 |                120 |                     129 |                 10 |                    9 |          106 |       125 |           83 |                 69 |           -0.29 |           -0.22 |
|   2011 |                139 |                     136 |                  9 |                    8 |          118 |       135 |           98 |                 89 |           -0.25 |           -0.13 |
|   2012 |                104 |                     104 |                  9 |                    8 |           82 |        99 |           81 |                 61 |           -0.36 |           -0.24 |
|   2013 |                153 |                     140 |                  9 |                    8 |           88 |       105 |           71 |                 90 |           -0.36 |           -0.44 |
|   2014 |                131 |                     107 |                  9 |                    8 |          116 |       133 |           92 |                 99 |           -0.25 |           -0.48 |
|   2015 |                140 |                     108 |                  8 |                    8 |           98 |       114 |           72 |                105 |           -0.21 |           -0.47 |
|   2016 |                148 |                     113 |                  8 |                    8 |           81 |        97 |           70 |                112 |           -0.24 |           -0.38 |
|   2017 |                172 |                     150 |                  8 |                    8 |           91 |       107 |           69 |                116 |            0.03 |           -0.33 |
|   2018 |                136 |                     114 |                  8 |                    8 |           74 |        90 |           55 |                 93 |            0.29 |           -0.13 |
|   2019 |                143 |                     107 |                  9 |                    9 |          109 |       127 |           77 |                 93 |           -0.19 |           -0.42 |
|   2020 |                108 |                      82 |                  9 |                   10 |           84 |       103 |           64 |                 76 |           -0.4  |           -0.48 |
|   2021 |                 62 |                      83 |                  8 |                    8 |           74 |        90 |           63 |                 43 |           -0.02 |           -0.2  |
|   2022 |                 74 |                      82 |                  8 |                    8 |           61 |        77 |           53 |                 50 |            0.43 |            0.28 |
|   2023 |                 73 |                       6 |                  8 |                    8 |          103 |       119 |           77 |                 54 |            0.23 |            0.12 |
|   2024 |                 72 |                       0 |                  8 |                    8 |          110 |       126 |           74 |                 55 |            0.02 |           -0.01 |
|   2025 |                 73 |                       0 |                  9 |                    8 |          112 |       129 |           88 |                 40 |            0.01 |           -0.06 |
|   2026 |                 75 |                       0 |                  6 |                    7 |           65 |        78 |           44 |                 39 |            0.34 |            0.27 |

**ECB cross-check.** The same scorer on the ECB's own complete speech file (copy, 1999-01 .. 2023-02; 2538 speeches) against the BIS selection (2373 ECB speeches in the same span): monthly mean tone correlates 0.91 over 276 common months (0.91 from 2010; quarterly 0.95); mean tone -0.097 (BIS) against -0.127 (copy). The BIS selection is therefore a fair sample of what the ECB said; the copy does not enter any signal.

**BIS posting delay** (posting date in the URL minus speech date): Fed speeches median 3 days (90th percentile 11), ECB median 3 (90th percentile 9). The signals date a speech by its own date (the central bank publishes the text itself on the day); section 9 repeats the tone tests dated by the BIS posting date.

## 2. The tone dictionary (frozen in `TONE_DICT` before any result)
**Citation and honesty note.** Construction principle: Apel & Blix Grimaldi (2012), "The information content of central bank minutes", Sveriges Riksbank
Working Paper 261 (journal version: "How informative are central bank minutes?", Review of Economics 65(1), 2014) - directional words next to a small set
of topic nouns, net index (hawk - dove) / (hawk + dove) - extended with outright stance terms in the manner of Bennani & Neuenkirch (2017, Applied
Economics 49) and Tadle (2022, Journal of Economics and Business 118), an inverted slack group and a negation rule. The papers' own word lists could not be
downloaded here (archive.riksbank.se is outside the allowed hosts), so **the English lists below are this arm's own, written from the published principle;
they are not a verbatim copy of a published dictionary.** They were frozen before any return was looked at and were not touched afterwards: the tone score
failed as a predictor and was left as it failed.

Scoring: lower-case; merge the multi-word expressions; cut into sentences; (A) every topic noun takes the NEAREST direction word within 4 tokens in its
sentence (the preceding one wins a tie): up = hawkish, down = dovish, reversed for the slack group, reversed again by a negator within 3 tokens before the
direction word; (B) each outright term is one hit, the policy-conditioned verbs only with a policy word within 4 tokens, a dovish noun after a removal word
is hawkish, a negator flips; document tone = (H - D) / (H + D) for documents with at least 5 hits. Institution tone = equal-weighted mean of the document
tones of the last 30 (>= 2 documents) or 90 (>= 4) calendar days; z-score against the bank's own expanding history (>= 1,095 days); relative tone = z(Fed) -
z(ECB). Fed = FOMC statements + minutes + speeches of Board members and Reserve Bank presidents; ECB = speeches of Executive Board members (incl. the
press-conference statements BIS carries), excluding speakers named only as Supervisory Board.

| part | entries |
|---|---|
| multi-word expressions merged into one token | `rate\s+(?:increase\|hike\|rise)s?` -> rate_hike; `rate\s+(?:cut\|reduction\|decrease)s?` -> rate_cut; `(?:key\s+)?(?:ecb\s+)?interest\s+rates?` -> interest_rate; `policy\s+rates?` -> policy_rate; `(?:federal\s+)?funds\s+rate` -> funds_rate; `target\s+range` -> target_range; `deposit\s+(?:facility\s+)?rate` -> deposit_rate; `(?:main\s+)?refinancing\s+rate` -> refi_rate; `(?:inflationary\|inflation\|price\|cost\|wage)\s+pressures?` -> price_pressures; `(?:consumer\|energy\|oil\|commodity\|import\|food\|core)\s+prices?` -> goods_prices; `(?:unit\s+)?labou?r\s+costs?` -> labor_costs; `labou?r\s+markets?` -> labor_market; `(?:resource\|capacity)\s+utili[sz]ation` -> resource_utilization; `spare\s+capacity` -> spare_capacity; `second[\s-]+round\s+effects?` -> second_round_effects; `wage[\s-]+price\s+spirals?` -> wage_price_spiral; `quantitative\s+easing` -> quantitative_easing; `(?:asset\s+)?purchase\s+program(?:me)?s?` -> asset_purchases; `asset\s+purchases?` -> asset_purchases; `(?:zero\|effective)\s+lower\s+bound` -> lower_bound |
| (A) topic nouns, up = hawkish | inflation, price_pressures, goods_prices, wages, labor_costs, growth, activity, demand, economy, output, expansion, recovery, employment, spending, consumption, investment, labor_market, production, hiring, resource_utilization, interest_rate, policy_rate, funds_rate, target_range, deposit_rate, refi_rate |
| (A) topic nouns, up = dovish (slack group) | unemployment, joblessness, spare_capacity |
| (A) direction words: up | high, higher, rise, rises, rising, rose, risen, increase, increases, increased, increasing, raise, raises, raised, raising, hike, hikes, hiked, hiking, lift, lifted, lifting, strong, stronger, strengthen, strengthens, strengthened, strengthening, robust, solid, elevated, accelerate, accelerates, accelerated, accelerating, acceleration, upward, upside, pickup, faster, rapid, rapidly, buoyant, surge, surged, surging, firm, firmer, firming, tight, tighter, tightening, tightened, heightened, mounting, boom, booming, above |
| (A) direction words: down | low, lower, fall, falls, falling, fell, fallen, decline, declines, declined, declining, decrease, decreases, decreased, decreasing, cut, cuts, cutting, reduce, reduces, reduced, reducing, reduction, reductions, weak, weaker, weaken, weakens, weakened, weakening, weakness, subdued, sluggish, slow, slower, slowed, slowing, slowdown, moderated, moderating, moderation, soft, softer, soften, softened, softening, muted, downward, downside, decelerate, decelerated, decelerating, deceleration, contract, contracted, contracting, contraction, depressed, anemic, below, dampen, dampened, dampening, ease, eased, easing |
| (B) outright hawkish terms | overheating, overheat, overheated, vigilance, vigilant, restrictive, restrictiveness, rate_hike, second_round_effects, wage_price_spiral, normalization, normalize, normalizing, taper, tapering, hawkish |
| (B) outright dovish terms | accommodative, accommodation, stimulus, stimulative, stimulate, stimulating, slack, rate_cut, patient, patience, disinflation, disinflationary, deflation, deflationary, recession, recessionary, downturn, headwinds, asset_purchases, quantitative_easing, lower_bound, dovish |
| (B) hawkish only with a policy word within 4 tokens | tighten, tightens, tightened, tightening, tighter, firming |
| (B) dovish only with a policy word within 4 tokens | ease, eases, eased, easing, loosen, loosening, looser, loose |
| policy words | policy, monetary, stance, cycle |
| dovish nouns that turn hawkish after a removal word (within 4 tokens before) | accommodative, accommodation, stimulus, slack, asset_purchases, quantitative_easing |
| removal words | remove, removes, removed, removing, removal, withdraw, withdraws, withdrawing, withdrawal, withdrawn, reduce, reduces, reduced, reducing, reduction, diminish, diminished, diminishing, absorb, absorbed, unwind, unwinding, end, ended, ending, taper, tapering, exit |
| negators (within 3 tokens before; flip the hit) | not, no, never, nor, neither, without, hardly, less, any token ending in n't |
| British -> American | labour -> labor, normalisation -> normalization, normalise -> normalize, normalising -> normalizing, anaemic -> anemic, programme -> program |
| windows | topic-direction 4 tokens, negation 3, policy word 4, removal word 4; a document needs 5 hits to carry a tone |

## 3. The 12 candidate signals and their priors (fixed before any result)
| signal       | family        | prior (sign on the raw quantity)                                               | first value   | last value   | defined 2010-26   | long share   |   sign flips / yr |
|:-------------|:--------------|:-------------------------------------------------------------------------------|:--------------|:-------------|:------------------|:-------------|------------------:|
| tone_rel_lvl | 1 tone        | - Fed tone above its own norm relative to the ECB (90-day windows) = dollar up | 2003-01-01    | 2026-11-05   | 99 %              | 23 %         |               4.1 |
| tone_rel_d1m | 1 tone        | - relative tone (30-day windows) rising over a month = dollar up               | 2003-01-01    | 2026-11-05   | 80 %              | 46 %         |              17.7 |
| tone_rel_d3m | 1 tone        | - relative tone (90-day windows) rising over three months = dollar up          | 2003-01-01    | 2026-11-05   | 99 %              | 51 %         |              10   |
| news_lvl     | 2 news        | - US news sentiment above its own history = dollar up (copy ends 2025-05)      | 2003-01-01    | 2025-06-03   | 92 %              | 56 %         |               6.6 |
| news_d1m     | 2 news        | - US news sentiment improving over a month = dollar up (copy ends 2025-05)     | 2003-01-01    | 2025-06-03   | 92 %              | 47 %         |              23.2 |
| epu_rel_d3m  | 3 uncertainty | - Europe-minus-US policy uncertainty rising over three months = euro down      | 2003-01-01    | 2026-11-05   | 100 %             | 49 %         |               4.3 |
| tpu_d3m      | 3 uncertainty | sign from the training window: 3-month change of US trade-policy uncertainty   | 2010-01-03    | 2026-11-05   | 100 %             | 50 %         |               4.5 |
| gpr_d3m      | 3 uncertainty | - geopolitical risk rising over three months = euro down (weak prior)          | 2003-01-01    | 2026-11-05   | 100 %             | 49 %         |              10.5 |
| jk_mp_3m     | 4 surprises   | - Fed-minus-ECB pure policy surprises cumulated over 3 months = dollar up      | 2003-01-01    | 2025-12-29   | 95 %              | 63 %         |               4.6 |
| jk_mp_6m     | 4 surprises   | - same over 6 months                                                           | 2003-01-01    | 2025-12-29   | 95 %              | 63 %         |               3.5 |
| jk_cbi_3m    | 4 surprises   | - Fed-minus-ECB information surprises over 3 months = dollar up (weak prior)   | 2003-01-01    | 2025-12-29   | 95 %              | 43 %         |               4.6 |
| jk_cbi_6m    | 4 surprises   | - same over 6 months                                                           | 2003-01-01    | 2025-12-29   | 95 %              | 45 %         |               3.3 |

A positive value is a vote for long EUR/USD. `long share` and `sign flips` describe 2010-26. The priors were declared as written in the module docstring;
two were flagged WEAK in advance (`gpr_d3m`, the two `jk_cbi_*`) and one has no prior at all (`tpu_d3m`: orientation = sign of the training-window
covariance with the 21-session forward return, refitted each year; fitted orientations: + in 2010, - in 2011-12, + in 2013-22, - in 2023-25, + in 2026).
EPUMONETARY (US monetary-policy uncertainty) is cached but was not made a candidate: no prior on its sign for the exchange rate and the budget was 12.

## 4. Reconciliation of the agreement rule
The agreement rule (sign of `cot_z52`, of `d_spread2y_20` and of the walk-forward house score all equal) rebuilt with `selective.house_score_wf` and the
selective evaluation helpers. Every cell is identical to arm N's report.

| decisions   | period   | arm N report (10 / 21 / 42 / 63 s)        | rebuilt here                              | identical   | decisions / yr            |
|:------------|:---------|:------------------------------------------|:------------------------------------------|:------------|:--------------------------|
| nonoverlap  | 2010-26  | 56 n=291 / 59 n=156 / 61 n=89 / 72 n=61   | 56 n=291 / 59 n=156 / 61 n=89 / 72 n=61   | True        | 17.3 / 9.3 / 5.3 / 3.7    |
| nonoverlap  | 2016-26  | 53 n=178 / 57 n=96 / 59 n=56 / 71 n=38    | 53 n=178 / 57 n=96 / 59 n=56 / 71 n=38    | True        | 16.5 / 8.9 / 5.2 / 3.6    |
| nonoverlap  | 2023-26  | 54 n=63 / 60 n=35 / 45 n=20 / 50 n=14     | 54 n=63 / 60 n=35 / 45 n=20 / 50 n=14     | True        | 16.6 / 9.3 / 5.4 / 3.9    |
| weekly      | 2010-26  | 57 n=390 / 59 n=387 / 65 n=383 / 67 n=383 | 57 n=390 / 59 n=387 / 65 n=383 / 67 n=383 | True        | 23.2 / 23.1 / 23.0 / 23.1 |
| weekly      | 2016-26  | 55 n=246 / 57 n=243 / 63 n=239 / 67 n=239 | 55 n=246 / 57 n=243 / 63 n=239 / 67 n=239 | True        | 22.8 / 22.6 / 22.4 / 22.6 |
| weekly      | 2023-26  | 57 n=80 / 55 n=77 / 47 n=73 / 53 n=73     | 57 n=80 / 55 n=77 / 47 n=73 / 53 n=73     | True        | 21.1 / 20.6 / 19.9 / 20.4 |

## 5. Standalone accuracy of each signal (direction = sign of the oriented signal)
Direction = sign of the oriented signal on every session where it is defined (and the house score exists, i.e. 2010+). Non-overlapping = greedy sequential
stream, plain Wilson interval. A no-skill caller sits at 50-52 % in these periods (base rate of up-moves 47-51 %).

*2010-26* (accuracy % [Wilson 95 %] n (decisions / year))

| signal       | non-overlapping 21 s      | non-overlapping 42 s     | non-overlapping 63 s    | weekly 21 s   | weekly 42 s   | weekly 63 s   |
|:-------------|:--------------------------|:-------------------------|:------------------------|:--------------|:--------------|:--------------|
| tone_rel_lvl | 55 [48-61] n=207 (12.4/y) | 57 [48-66] n=103 (6.2/y) | 51 [39-62] n=69 (4.2/y) | 53 n=864      | 55 n=861      | 54 n=857      |
| tone_rel_d1m | 49 [42-56] n=192 (11.5/y) | 46 [37-56] n=97 (5.8/y)  | 52 [40-64] n=67 (4.0/y) | 49 n=705      | 48 n=705      | 49 n=705      |
| tone_rel_d3m | 50 [44-57] n=206 (12.3/y) | 47 [37-56] n=103 (6.2/y) | 58 [46-69] n=69 (4.2/y) | 49 n=860      | 49 n=857      | 52 n=853      |
| news_lvl     | 48 [41-55] n=191 (11.4/y) | 52 [42-62] n=96 (5.8/y)  | 50 [38-62] n=64 (3.9/y) | 50 n=800      | 49 n=800      | 51 n=800      |
| news_d1m     | 48 [41-55] n=190 (11.3/y) | 48 [38-58] n=96 (5.8/y)  | 39 [28-51] n=64 (3.9/y) | 49 n=771      | 51 n=771      | 50 n=771      |
| epu_rel_d3m  | 51 [45-58] n=208 (12.4/y) | 48 [39-58] n=104 (6.2/y) | 48 [36-59] n=69 (4.2/y) | 49 n=870      | 48 n=866      | 53 n=862      |
| tpu_d3m      | 41 [35-48] n=208 (12.4/y) | 40 [31-50] n=104 (6.2/y) | 48 [36-59] n=69 (4.2/y) | 46 n=870      | 44 n=866      | 47 n=862      |
| gpr_d3m      | 47 [40-53] n=208 (12.4/y) | 57 [47-66] n=104 (6.2/y) | 49 [38-61] n=69 (4.2/y) | 50 n=870      | 52 n=866      | 54 n=862      |
| jk_mp_3m     | 46 [40-53] n=198 (11.8/y) | 54 [44-63] n=99 (5.9/y)  | 50 [38-62] n=66 (4.0/y) | 47 n=830      | 50 n=830      | 50 n=830      |
| jk_mp_6m     | 47 [40-54] n=198 (11.8/y) | 49 [40-59] n=99 (5.9/y)  | 53 [41-65] n=66 (4.0/y) | 52 n=830      | 52 n=830      | 50 n=830      |
| jk_cbi_3m    | 55 [48-61] n=198 (11.8/y) | 53 [43-62] n=99 (5.9/y)  | 48 [37-60] n=66 (4.0/y) | 54 n=830      | 55 n=830      | 58 n=830      |
| jk_cbi_6m    | 55 [48-61] n=198 (11.8/y) | 55 [45-64] n=99 (5.9/y)  | 56 [44-67] n=66 (4.0/y) | 55 n=830      | 54 n=830      | 56 n=830      |

*2016-26* (accuracy % [Wilson 95 %] n (decisions / year))

| signal       | non-overlapping 21 s      | non-overlapping 42 s    | non-overlapping 63 s    | weekly 21 s   | weekly 42 s   | weekly 63 s   |
|:-------------|:--------------------------|:------------------------|:------------------------|:--------------|:--------------|:--------------|
| tone_rel_lvl | 49 [41-58] n=132 (12.3/y) | 55 [43-67] n=65 (6.1/y) | 45 [32-60] n=44 (4.2/y) | 50 n=553      | 53 n=550      | 53 n=546      |
| tone_rel_d1m | 48 [39-57] n=119 (11.1/y) | 55 [42-67] n=60 (5.6/y) | 50 [36-64] n=42 (4.0/y) | 47 n=423      | 50 n=423      | 51 n=423      |
| tone_rel_d3m | 49 [40-57] n=131 (12.2/y) | 43 [32-55] n=65 (6.1/y) | 55 [40-68] n=44 (4.2/y) | 47 n=549      | 48 n=546      | 51 n=542      |
| news_lvl     | 46 [37-55] n=116 (10.8/y) | 50 [38-62] n=58 (5.4/y) | 49 [34-64] n=39 (3.7/y) | 48 n=489      | 47 n=489      | 50 n=489      |
| news_d1m     | 51 [42-60] n=116 (10.8/y) | 49 [37-62] n=59 (5.5/y) | 36 [23-52] n=39 (3.7/y) | 51 n=477      | 54 n=477      | 52 n=477      |
| epu_rel_d3m  | 51 [43-59] n=133 (12.4/y) | 45 [34-57] n=66 (6.2/y) | 52 [38-66] n=44 (4.2/y) | 48 n=559      | 50 n=555      | 56 n=551      |
| tpu_d3m      | 41 [33-49] n=133 (12.4/y) | 39 [29-51] n=66 (6.2/y) | 48 [34-62] n=44 (4.2/y) | 46 n=559      | 44 n=555      | 47 n=551      |
| gpr_d3m      | 46 [38-54] n=133 (12.4/y) | 56 [44-67] n=66 (6.2/y) | 52 [38-66] n=44 (4.2/y) | 53 n=559      | 54 n=555      | 54 n=551      |
| jk_mp_3m     | 45 [36-54] n=123 (11.4/y) | 51 [39-63] n=61 (5.7/y) | 41 [28-57] n=41 (3.9/y) | 44 n=519      | 47 n=519      | 45 n=519      |
| jk_mp_6m     | 43 [35-52] n=123 (11.4/y) | 46 [34-58] n=61 (5.7/y) | 46 [32-61] n=41 (3.9/y) | 49 n=519      | 48 n=519      | 44 n=519      |
| jk_cbi_3m    | 54 [45-62] n=123 (11.4/y) | 52 [40-64] n=61 (5.7/y) | 49 [34-64] n=41 (3.9/y) | 55 n=519      | 56 n=519      | 60 n=519      |
| jk_cbi_6m    | 60 [51-68] n=123 (11.4/y) | 61 [48-72] n=61 (5.7/y) | 66 [51-78] n=41 (3.9/y) | 61 n=519      | 61 n=519      | 63 n=519      |

*2023-26* (accuracy % [Wilson 95 %] n (decisions / year))

| signal       | non-overlapping 21 s     | non-overlapping 42 s    | non-overlapping 63 s    | weekly 21 s   | weekly 42 s   | weekly 63 s   |
|:-------------|:-------------------------|:------------------------|:------------------------|:--------------|:--------------|:--------------|
| tone_rel_lvl | 46 [32-60] n=46 (12.2/y) | 45 [27-65] n=22 (6.0/y) | 33 [15-58] n=15 (4.2/y) | 48 n=194      | 47 n=191      | 40 n=187      |
| tone_rel_d1m | 51 [36-66] n=39 (10.4/y) | 65 [43-82] n=20 (5.4/y) | 71 [45-88] n=14 (3.9/y) | 53 n=132      | 58 n=132      | 62 n=132      |
| tone_rel_d3m | 53 [39-67] n=47 (12.5/y) | 35 [19-55] n=23 (6.2/y) | 60 [36-80] n=15 (4.2/y) | 52 n=194      | 48 n=191      | 49 n=187      |
| news_lvl     | 47 [30-64] n=30 (8.0/y)  | 67 [42-85] n=15 (4.1/y) | 60 [31-83] n=10 (2.8/y) | 54 n=125      | 48 n=125      | 56 n=125      |
| news_d1m     | 66 [47-80] n=29 (7.7/y)  | 53 [30-75] n=15 (4.1/y) | 60 [31-83] n=10 (2.8/y) | 59 n=122      | 68 n=122      | 64 n=122      |
| epu_rel_d3m  | 55 [41-69] n=47 (12.5/y) | 43 [26-63] n=23 (6.2/y) | 47 [25-70] n=15 (4.2/y) | 48 n=195      | 48 n=191      | 55 n=187      |
| tpu_d3m      | 53 [39-67] n=47 (12.5/y) | 52 [33-71] n=23 (6.2/y) | 60 [36-80] n=15 (4.2/y) | 51 n=195      | 46 n=191      | 50 n=187      |
| gpr_d3m      | 40 [28-55] n=47 (12.5/y) | 48 [29-67] n=23 (6.2/y) | 40 [20-64] n=15 (4.2/y) | 51 n=195      | 53 n=191      | 54 n=187      |
| jk_mp_3m     | 35 [22-51] n=37 (9.8/y)  | 28 [12-51] n=18 (4.9/y) | 33 [14-61] n=12 (3.3/y) | 36 n=155      | 40 n=155      | 43 n=155      |
| jk_mp_6m     | 30 [17-46] n=37 (9.8/y)  | 33 [16-56] n=18 (4.9/y) | 42 [19-68] n=12 (3.3/y) | 38 n=155      | 38 n=155      | 37 n=155      |
| jk_cbi_3m    | 51 [36-67] n=37 (9.8/y)  | 44 [25-66] n=18 (4.9/y) | 67 [39-86] n=12 (3.3/y) | 52 n=155      | 59 n=155      | 63 n=155      |
| jk_cbi_6m    | 54 [38-69] n=37 (9.8/y)  | 61 [39-80] n=18 (4.9/y) | 83 [55-95] n=12 (3.3/y) | 63 n=155      | 63 n=155      | 63 n=155      |

*Other era, 2004-09* (never a test year; the same fixed rule; `tpu_d3m` has no orientation before 2010)

| signal       | non-overlapping 21 s   | non-overlapping 42 s   | non-overlapping 63 s   | weekly 21 s   | weekly 42 s   | weekly 63 s   |
|:-------------|:-----------------------|:-----------------------|:-----------------------|:--------------|:--------------|:--------------|
| tone_rel_lvl | 52 [41-63] n=75        | 61 [45-74] n=38        | 60 [41-77] n=25        | 60 n=309      | 62 n=309      | 64 n=309      |
| tone_rel_d1m | 48 [37-60] n=66        | 44 [29-61] n=34        | 38 [21-57] n=24        | 46 n=230      | 47 n=230      | 50 n=230      |
| tone_rel_d3m | 55 [44-66] n=74        | 55 [40-70] n=38        | 40 [23-59] n=25        | 55 n=301      | 52 n=301      | 54 n=301      |
| news_lvl     | 52 [41-63] n=75        | 53 [37-68] n=38        | 52 [33-70] n=25        | 52 n=312      | 53 n=312      | 47 n=312      |
| news_d1m     | 46 [35-57] n=74        | 58 [42-72] n=38        | 52 [33-70] n=25        | 49 n=302      | 54 n=302      | 51 n=302      |
| epu_rel_d3m  | 55 [43-65] n=75        | 58 [42-72] n=38        | 48 [30-67] n=25        | 51 n=312      | 54 n=312      | 55 n=312      |
| tpu_d3m      | -                      | -                      | -                      | -             | -             | -             |
| gpr_d3m      | 59 [47-69] n=75        | 66 [50-79] n=38        | 56 [37-73] n=25        | 54 n=312      | 57 n=312      | 55 n=312      |
| jk_mp_3m     | 49 [38-60] n=75        | 50 [35-65] n=38        | 56 [37-73] n=25        | 53 n=312      | 51 n=312      | 50 n=312      |
| jk_mp_6m     | 51 [40-62] n=75        | 50 [35-65] n=38        | 52 [33-70] n=25        | 54 n=312      | 55 n=312      | 52 n=312      |
| jk_cbi_3m    | 53 [42-64] n=75        | 45 [30-60] n=38        | 40 [23-59] n=25        | 51 n=312      | 48 n=312      | 44 n=312      |
| jk_cbi_6m    | 51 [40-62] n=75        | 55 [40-70] n=38        | 52 [33-70] n=25        | 54 n=312      | 56 n=312      | 59 n=312      |

## 6. Round 7 controls: is it new information or the recent price move restated?
Round 7 asks whether a new signal merely restates the agreement inputs or the recent price move. Controls: `cot_z52`, `d_spread2y_20`, the walk-forward
house score, and EUR/USD's trailing 21- and 63-session returns. Orthogonalised signal = the signal minus the part an OLS fitted on rows before the test year
attributes to the controls (the signal keeps its own zero point; the house score enters from 2013; `tpu_d3m` has residuals from 2013 only, hence its
smaller n).

**Correlations, 2010-26** (daily sessions; `r2` = share of the signal's variance explained in-sample by the trailing returns / by all five controls; `sign_agree` = share of sessions on which the signal's vote equals the old vote; `corr_fwd` = correlation with the forward 21- / 63-session return)

| signal       |   corr_cot_z52 |   corr_d_spread2y_20 |   corr_house |   corr_ret_21d |   corr_ret_63d |   r2_price_controls |   r2_all_controls |   sign_agree_cot |   sign_agree_spr |   sign_agree_house |   corr_fwd21 |   corr_fwd63 |
|:-------------|---------------:|---------------------:|-------------:|---------------:|---------------:|--------------------:|------------------:|-----------------:|-----------------:|-------------------:|-------------:|-------------:|
| tone_rel_lvl |           0.21 |                 0.14 |         0.17 |           0.12 |           0.22 |                0.05 |              0.07 |             0.55 |             0.57 |               0.58 |         0.11 |         0.19 |
| tone_rel_d1m |          -0.01 |                 0.06 |         0.07 |           0.11 |          -0.03 |                0.03 |              0.03 |             0.49 |             0.51 |               0.54 |         0.03 |        -0.03 |
| tone_rel_d3m |           0.01 |                 0.12 |         0.11 |           0    |           0.03 |                0    |              0.02 |             0.5  |             0.52 |               0.5  |         0.04 |         0.08 |
| news_lvl     |           0.18 |                 0.11 |         0.11 |           0.04 |           0.07 |                0    |              0.04 |             0.57 |             0.53 |               0.54 |         0.07 |         0.1  |
| news_d1m     |           0.07 |                 0.14 |         0.05 |          -0.06 |          -0.03 |                0    |              0.05 |             0.49 |             0.5  |               0.51 |        -0.01 |         0.05 |
| epu_rel_d3m  |           0.23 |                 0.05 |         0.14 |           0.09 |           0.26 |                0.07 |              0.09 |             0.52 |             0.53 |               0.52 |         0.03 |         0.07 |
| tpu_d3m      |           0.06 |                 0.01 |         0.07 |          -0.06 |          -0.11 |                0.01 |              0.04 |             0.54 |             0.49 |               0.53 |        -0.08 |        -0.13 |
| gpr_d3m      |           0.02 |                 0.06 |         0.08 |           0.02 |           0.04 |                0    |              0.01 |             0.5  |             0.51 |               0.5  |        -0    |         0    |
| jk_mp_3m     |           0.24 |                 0.24 |         0.16 |           0.09 |           0.11 |                0.01 |              0.11 |             0.54 |             0.55 |               0.55 |        -0.02 |         0.1  |
| jk_mp_6m     |           0.33 |                 0.18 |         0.22 |           0.14 |           0.15 |                0.03 |              0.13 |             0.59 |             0.54 |               0.59 |         0.05 |         0.1  |
| jk_cbi_3m    |           0.15 |                 0.06 |         0.03 |           0.05 |           0.13 |                0.02 |              0.03 |             0.56 |             0.53 |               0.52 |         0.11 |         0.2  |
| jk_cbi_6m    |           0.07 |                 0.09 |        -0.05 |           0.11 |           0.24 |                0.06 |              0.09 |             0.54 |             0.53 |               0.48 |         0.06 |         0.09 |

**Standalone accuracy after orthogonalising, non-overlapping decisions, 2010-26** (raw signal / residual on trailing returns / residual on all five controls)

| signal       | 21 s raw / ex-price / ex-all   | 42 s raw / ex-price / ex-all   | 63 s raw / ex-price / ex-all   |
|:-------------|:-------------------------------|:-------------------------------|:-------------------------------|
| tone_rel_lvl | 55 n=207 / 54 n=207 / 52 n=207 | 57 n=103 / 58 n=103 / 57 n=103 | 51 n=69 / 51 n=69 / 51 n=69    |
| tone_rel_d1m | 49 n=192 / 49 n=192 / 48 n=192 | 46 n=97 / 46 n=97 / 44 n=97    | 52 n=67 / 52 n=67 / 51 n=67    |
| tone_rel_d3m | 50 n=206 / 49 n=206 / 52 n=206 | 47 n=103 / 45 n=103 / 47 n=103 | 58 n=69 / 55 n=69 / 58 n=69    |
| news_lvl     | 48 n=191 / 49 n=191 / 52 n=191 | 52 n=96 / 52 n=96 / 54 n=96    | 50 n=64 / 50 n=64 / 56 n=64    |
| news_d1m     | 48 n=190 / 51 n=191 / 49 n=191 | 48 n=96 / 44 n=96 / 45 n=96    | 39 n=64 / 45 n=64 / 44 n=64    |
| epu_rel_d3m  | 51 n=208 / 50 n=208 / 50 n=208 | 48 n=104 / 47 n=104 / 45 n=104 | 48 n=69 / 48 n=69 / 45 n=69    |
| tpu_d3m      | 41 n=208 / 44 n=171 / 43 n=171 | 40 n=104 / 39 n=85 / 38 n=85   | 48 n=69 / 53 n=57 / 47 n=57    |
| gpr_d3m      | 47 n=208 / 47 n=208 / 48 n=208 | 57 n=104 / 57 n=104 / 57 n=104 | 49 n=69 / 49 n=69 / 55 n=69    |
| jk_mp_3m     | 46 n=198 / 44 n=198 / 48 n=198 | 54 n=99 / 51 n=99 / 51 n=99    | 50 n=66 / 47 n=66 / 48 n=66    |
| jk_mp_6m     | 47 n=198 / 44 n=198 / 46 n=198 | 49 n=99 / 48 n=99 / 46 n=99    | 53 n=66 / 52 n=66 / 45 n=66    |
| jk_cbi_3m    | 55 n=198 / 56 n=198 / 53 n=198 | 53 n=99 / 54 n=99 / 52 n=99    | 48 n=66 / 48 n=66 / 45 n=66    |
| jk_cbi_6m    | 55 n=198 / 56 n=198 / 54 n=198 | 55 n=99 / 54 n=99 / 60 n=99    | 56 n=66 / 58 n=66 / 53 n=66    |

**Standalone accuracy after orthogonalising, non-overlapping decisions, 2016-26** (raw signal / residual on trailing returns / residual on all five controls)

| signal       | 21 s raw / ex-price / ex-all   | 42 s raw / ex-price / ex-all   | 63 s raw / ex-price / ex-all   |
|:-------------|:-------------------------------|:-------------------------------|:-------------------------------|
| tone_rel_lvl | 49 n=132 / 48 n=132 / 45 n=132 | 55 n=65 / 57 n=65 / 55 n=65    | 45 n=44 / 45 n=44 / 45 n=44    |
| tone_rel_d1m | 48 n=119 / 47 n=119 / 45 n=119 | 55 n=60 / 55 n=60 / 48 n=60    | 50 n=42 / 50 n=42 / 45 n=42    |
| tone_rel_d3m | 49 n=131 / 48 n=131 / 50 n=131 | 43 n=65 / 42 n=65 / 42 n=65    | 55 n=44 / 52 n=44 / 59 n=44    |
| news_lvl     | 46 n=116 / 46 n=116 / 49 n=116 | 50 n=58 / 52 n=58 / 53 n=58    | 49 n=39 / 49 n=39 / 54 n=39    |
| news_d1m     | 51 n=116 / 51 n=116 / 49 n=116 | 49 n=59 / 47 n=58 / 48 n=58    | 36 n=39 / 41 n=39 / 38 n=39    |
| epu_rel_d3m  | 51 n=133 / 50 n=133 / 52 n=133 | 45 n=66 / 45 n=66 / 47 n=66    | 52 n=44 / 52 n=44 / 50 n=44    |
| tpu_d3m      | 41 n=133 / 43 n=134 / 41 n=134 | 39 n=66 / 39 n=66 / 38 n=66    | 48 n=44 / 57 n=44 / 50 n=44    |
| gpr_d3m      | 46 n=133 / 46 n=133 / 47 n=133 | 56 n=66 / 56 n=66 / 53 n=66    | 52 n=44 / 52 n=44 / 57 n=44    |
| jk_mp_3m     | 45 n=123 / 43 n=123 / 46 n=123 | 51 n=61 / 48 n=61 / 46 n=61    | 41 n=41 / 41 n=41 / 39 n=41    |
| jk_mp_6m     | 43 n=123 / 41 n=123 / 42 n=123 | 46 n=61 / 46 n=61 / 38 n=61    | 46 n=41 / 46 n=41 / 34 n=41    |
| jk_cbi_3m    | 54 n=123 / 54 n=123 / 50 n=123 | 52 n=61 / 52 n=61 / 48 n=61    | 49 n=41 / 46 n=41 / 41 n=41    |
| jk_cbi_6m    | 60 n=123 / 62 n=123 / 59 n=123 | 61 n=61 / 59 n=61 / 66 n=61    | 66 n=41 / 66 n=41 / 61 n=41    |

**AND-rule gain over the agreement rule on the same span, in points: raw / ex-price / ex-all** (non-overlapping; n = decisions of the AND rule)

| signal       | 2010-26, 21 s                        | 2010-26, 42 s                     | 2016-26, 21 s                       | 2016-26, 42 s                        |
|:-------------|:-------------------------------------|:----------------------------------|:------------------------------------|:-------------------------------------|
| tone_rel_lvl | -2 (n=101) / +0 (n=100) / -6 (n=90)  | +5 (n=62) / +9 (n=60) / +7 (n=55) | -2 (n=58) / -0 (n=58) / -9 (n=52)   | +5 (n=36) / +10 (n=35) / +7 (n=32)   |
| tone_rel_d1m | -1 (n=99) / -3 (n=100) / -1 (n=101)  | -1 (n=70) / -1 (n=70) / -4 (n=70) | -3 (n=62) / -5 (n=62) / -4 (n=61)   | -0 (n=43) / -3 (n=43) / -7 (n=41)    |
| tone_rel_d3m | -4 (n=100) / -5 (n=97) / -6 (n=103)  | -2 (n=61) / -1 (n=60) / +0 (n=65) | -7 (n=55) / -8 (n=54) / -7 (n=57)   | -4 (n=34) / -4 (n=34) / +1 (n=38)    |
| news_lvl     | +2 (n=101) / +1 (n=105) / +1 (n=105) | +1 (n=62) / +0 (n=66) / +1 (n=65) | +5 (n=65) / +2 (n=65) / +5 (n=65)   | -3 (n=40) / +0 (n=41) / -3 (n=40)    |
| news_d1m     | -4 (n=95) / -4 (n=101) / -6 (n=92)   | +1 (n=62) / +4 (n=64) / +5 (n=61) | -2 (n=57) / -1 (n=61) / -4 (n=52)   | +6 (n=36) / +9 (n=37) / +12 (n=34)   |
| epu_rel_d3m  | -2 (n=97) / -3 (n=95) / -6 (n=93)    | -1 (n=65) / -3 (n=64) / -2 (n=61) | +1 (n=60) / -1 (n=59) / -6 (n=55)   | +2 (n=41) / -1 (n=40) / +1 (n=37)    |
| tpu_d3m      | -8 (n=100) / -7 (n=80) / -3 (n=79)   | -3 (n=66) / -1 (n=55) / +2 (n=56) | -8 (n=61) / -7 (n=60) / -2 (n=58)   | +4 (n=41) / +4 (n=40) / +6 (n=40)    |
| gpr_d3m      | -4 (n=94) / -5 (n=95) / -2 (n=100)   | +6 (n=66) / +8 (n=66) / +2 (n=70) | +1 (n=58) / -1 (n=59) / -2 (n=60)   | +9 (n=41) / +12 (n=41) / +4 (n=43)   |
| jk_mp_3m     | -7 (n=99) / -7 (n=94) / -12 (n=92)   | +3 (n=64) / +5 (n=62) / +1 (n=61) | -10 (n=57) / -9 (n=54) / -16 (n=50) | +3 (n=37) / +3 (n=35) / +1 (n=33)    |
| jk_mp_6m     | -6 (n=103) / -5 (n=101) / -7 (n=75)  | +1 (n=64) / +1 (n=63) / -1 (n=48) | -2 (n=58) / -5 (n=55) / -11 (n=36)  | -7 (n=38) / -7 (n=36) / -7 (n=23)    |
| jk_cbi_3m    | +4 (n=98) / +4 (n=100) / +1 (n=97)   | +2 (n=65) / +2 (n=66) / +4 (n=64) | +9 (n=56) / +7 (n=56) / +5 (n=53)   | +9 (n=38) / +9 (n=38) / +7 (n=36)    |
| jk_cbi_6m    | +7 (n=95) / +8 (n=97) / +2 (n=109)   | +4 (n=60) / +6 (n=61) / +5 (n=68) | +15 (n=58) / +16 (n=59) / +8 (n=66) | +11 (n=38) / +11 (n=38) / +12 (n=42) |

## 7. As an extra vote on the agreement rule
(a) AND rule = the agreement rule speaks and the new signal votes the same way. The gain is against the agreement rule alone on all its decisions; the
count of decisions per year is printed next to every accuracy, and the agreement rule itself has only 9.3 (21 sessions) and 5.3 (42 sessions) a year.
(b) OUTSIDE = sessions on which the three old signals do not agree; the new signal alone gives the direction. (c) Paired bootstrap on the weekly grid.
No signal extends coverage: outside the agreement every candidate is within its interval of 50 % in 2010-26 (best: `jk_cbi_3m` 57 % at 21 sessions, 50 % at
42).

**(a) AND rule, non-overlapping decisions, 2010-26** (accuracy % [Wilson] n (decisions / year), then the gain in points over the agreement rule)

| signal               | 21 s                          | 42 s                         | 63 s                          |
|:---------------------|:------------------------------|:-----------------------------|:------------------------------|
| agreement rule alone | 59 [51-66] n=156 (9.3/y)      | 61 [50-70] n=89 (5.3/y)      | 72 [60-82] n=61 (3.7/y)       |
| tone_rel_lvl         | 57 [48-67] n=101 (6.0/y) -1.5 | 66 [54-77] n=62 (3.7/y) +5.5 | 78 [64-88] n=46 (2.8/y) +6.1  |
| tone_rel_d1m         | 57 [47-66] n=99 (5.9/y) -2.4  | 61 [50-72] n=70 (4.2/y) +0.8 | 67 [53-78] n=51 (3.1/y) -5.5  |
| tone_rel_d3m         | 54 [44-63] n=100 (6.0/y) -5.0 | 59 [46-70] n=61 (3.7/y) -1.7 | 64 [50-77] n=45 (2.7/y) -7.7  |
| news_lvl             | 59 [50-68] n=101 (6.0/y) +0.4 | 61 [49-72] n=62 (3.7/y) +0.6 | 68 [53-80] n=44 (2.7/y) -3.9  |
| news_d1m             | 53 [43-62] n=95 (5.7/y) -6.3  | 61 [49-72] n=62 (3.7/y) +0.6 | 62 [48-75] n=48 (2.9/y) -9.6  |
| epu_rel_d3m          | 57 [47-66] n=97 (5.8/y) -2.3  | 60 [48-71] n=65 (3.9/y) -0.7 | 70 [56-81] n=50 (3.0/y) -2.1  |
| tpu_d3m              | 51 [41-61] n=100 (6.0/y) -8.0 | 58 [46-69] n=66 (4.0/y) -3.1 | 67 [53-79] n=46 (2.8/y) -4.7  |
| gpr_d3m              | 55 [45-65] n=94 (5.6/y) -3.7  | 67 [55-77] n=66 (4.0/y) +6.0 | 73 [59-84] n=45 (2.7/y) +1.2  |
| jk_mp_3m             | 52 [42-61] n=99 (5.9/y) -7.5  | 64 [52-75] n=64 (3.8/y) +3.4 | 67 [52-79] n=45 (2.7/y) -5.5  |
| jk_mp_6m             | 52 [43-62] n=103 (6.1/y) -6.5 | 62 [50-73] n=64 (3.8/y) +1.8 | 63 [49-75] n=46 (2.8/y) -9.1  |
| jk_cbi_3m            | 62 [52-71] n=98 (5.8/y) +3.3  | 63 [51-74] n=65 (3.9/y) +2.4 | 60 [46-73] n=48 (2.9/y) -11.7 |
| jk_cbi_6m            | 65 [55-74] n=95 (5.7/y) +6.3  | 65 [52-76] n=60 (3.6/y) +4.3 | 80 [66-89] n=45 (2.7/y) +7.9  |

**(a) AND rule, non-overlapping decisions, 2016-26** (accuracy % [Wilson] n (decisions / year), then the gain in points over the agreement rule)

| signal               | 21 s                          | 42 s                          | 63 s                          |
|:---------------------|:------------------------------|:------------------------------|:------------------------------|
| agreement rule alone | 57 [47-67] n=96 (8.9/y)       | 59 [46-71] n=56 (5.2/y)       | 71 [55-83] n=38 (3.6/y)       |
| tone_rel_lvl         | 55 [42-67] n=58 (5.4/y) -2.1  | 64 [48-78] n=36 (3.4/y) +5.0  | 78 [59-89] n=27 (2.5/y) +6.7  |
| tone_rel_d1m         | 55 [43-67] n=62 (5.8/y) -2.5  | 65 [50-78] n=43 (4.0/y) +6.2  | 68 [50-81] n=31 (2.9/y) -3.3  |
| tone_rel_d3m         | 49 [36-62] n=55 (5.1/y) -8.2  | 56 [39-71] n=34 (3.2/y) -3.0  | 52 [33-70] n=25 (2.4/y) -19.1 |
| news_lvl             | 58 [46-70] n=65 (6.0/y) +1.2  | 55 [40-69] n=40 (3.7/y) -3.9  | 65 [46-81] n=26 (2.5/y) -5.7  |
| news_d1m             | 53 [40-65] n=57 (5.3/y) -4.7  | 67 [50-80] n=36 (3.4/y) +7.7  | 63 [44-78] n=27 (2.5/y) -8.1  |
| epu_rel_d3m          | 58 [46-70] n=60 (5.6/y) +1.0  | 61 [46-74] n=41 (3.8/y) +2.0  | 70 [52-83] n=30 (2.8/y) -1.1  |
| tpu_d3m              | 49 [37-61] n=61 (5.7/y) -8.1  | 63 [48-76] n=41 (3.8/y) +4.5  | 69 [51-83] n=29 (2.7/y) -2.1  |
| gpr_d3m              | 59 [46-70] n=58 (5.4/y) +1.3  | 68 [53-80] n=41 (3.8/y) +9.4  | 78 [59-89] n=27 (2.5/y) +6.7  |
| jk_mp_3m             | 46 [33-58] n=57 (5.3/y) -11.7 | 62 [46-76] n=37 (3.5/y) +3.2  | 59 [41-75] n=27 (2.5/y) -11.8 |
| jk_mp_6m             | 53 [41-66] n=58 (5.4/y) -3.8  | 53 [37-68] n=38 (3.6/y) -6.3  | 54 [36-70] n=28 (2.6/y) -17.5 |
| jk_cbi_3m            | 64 [51-76] n=56 (5.2/y) +7.0  | 68 [53-81] n=38 (3.6/y) +9.5  | 67 [48-81] n=27 (2.5/y) -4.4  |
| jk_cbi_6m            | 71 [58-81] n=58 (5.4/y) +13.4 | 71 [55-83] n=38 (3.6/y) +12.1 | 82 [64-92] n=28 (2.6/y) +11.1 |

**(a) AND rule, non-overlapping decisions, 2023-26** (accuracy % [Wilson] n (decisions / year), then the gain in points over the agreement rule)

| signal               | 21 s                          | 42 s                          | 63 s                          |
|:---------------------|:------------------------------|:------------------------------|:------------------------------|
| agreement rule alone | 60 [44-74] n=35 (9.3/y)       | 45 [26-66] n=20 (5.4/y)       | 50 [27-73] n=14 (3.9/y)       |
| tone_rel_lvl         | 52 [33-70] n=25 (6.6/y) -8.0  | 47 [25-70] n=15 (4.1/y) +1.7  | 55 [28-79] n=11 (3.1/y) +4.5  |
| tone_rel_d1m         | 61 [39-80] n=18 (4.8/y) +1.1  | 57 [33-79] n=14 (3.8/y) +12.1 | 80 [49-94] n=10 (2.8/y) +30.0 |
| tone_rel_d3m         | 54 [35-71] n=26 (6.9/y) -6.2  | 53 [30-75] n=15 (4.1/y) +8.3  | 45 [21-72] n=11 (3.1/y) -4.5  |
| news_lvl             | 63 [41-81] n=19 (5.0/y) +3.2  | 27 [10-57] n=11 (3.0/y) -17.7 | 62 [31-86] n=8 (2.2/y) +12.5  |
| news_d1m             | 57 [33-79] n=14 (3.7/y) -2.9  | 75 [41-93] n=8 (2.2/y) +30.0  | 71 [36-92] n=7 (1.9/y) +21.4  |
| epu_rel_d3m          | 65 [45-81] n=23 (6.1/y) +5.2  | 67 [42-85] n=15 (4.1/y) +21.7 | 58 [32-81] n=12 (3.3/y) +8.3  |
| tpu_d3m              | 50 [32-68] n=26 (6.9/y) -10.0 | 60 [36-80] n=15 (4.1/y) +15.0 | 58 [32-81] n=12 (3.3/y) +8.3  |
| gpr_d3m              | 58 [36-77] n=19 (5.0/y) -2.1  | 54 [29-77] n=13 (3.5/y) +8.8  | 75 [41-93] n=8 (2.2/y) +25.0  |
| jk_mp_3m             | 33 [16-56] n=18 (4.8/y) -26.7 | 55 [28-79] n=11 (3.0/y) +9.5  | 62 [31-86] n=8 (2.2/y) +12.5  |
| jk_mp_6m             | 38 [18-61] n=16 (4.3/y) -22.5 | 30 [11-60] n=10 (2.7/y) -15.0 | 38 [14-69] n=8 (2.2/y) -12.5  |
| jk_cbi_3m            | 67 [42-85] n=15 (4.0/y) +6.7  | 80 [49-94] n=10 (2.7/y) +35.0 | 50 [22-78] n=8 (2.2/y) +0.0   |
| jk_cbi_6m            | 75 [51-90] n=16 (4.3/y) +15.0 | 55 [28-79] n=11 (3.0/y) +9.5  | 67 [35-88] n=9 (2.5/y) +16.7  |

**Agreement calls the signal confirms vs contradicts, weekly decisions, 2010-26**

| signal       | 21 s: same span / confirmed / contradicted   | 42 s: same span / confirmed / contradicted   | 63 s: same span / confirmed / contradicted   |
|:-------------|:---------------------------------------------|:---------------------------------------------|:---------------------------------------------|
| tone_rel_lvl | 59 n=383 / 61 n=246 / 55 n=137               | 64 n=380 / 68 n=243 / 58 n=137               | 66 n=380 / 70 n=243 / 59 n=137               |
| tone_rel_d1m | 61 n=306 / 61 n=155 / 62 n=151               | 64 n=306 / 63 n=155 / 66 n=151               | 66 n=306 / 64 n=155 / 68 n=151               |
| tone_rel_d3m | 59 n=381 / 59 n=201 / 59 n=180               | 65 n=378 / 62 n=198 / 68 n=180               | 66 n=378 / 68 n=198 / 65 n=180               |
| news_lvl     | 59 n=353 / 61 n=203 / 57 n=150               | 66 n=353 / 64 n=203 / 70 n=150               | 68 n=353 / 67 n=203 / 69 n=150               |
| news_d1m     | 59 n=337 / 63 n=167 / 55 n=170               | 66 n=337 / 69 n=167 / 62 n=170               | 68 n=337 / 74 n=167 / 62 n=170               |
| epu_rel_d3m  | 59 n=387 / 59 n=205 / 60 n=182               | 65 n=383 / 63 n=204 / 66 n=179               | 67 n=383 / 68 n=204 / 65 n=179               |
| tpu_d3m      | 59 n=387 / 56 n=206 / 63 n=181               | 65 n=383 / 59 n=202 / 71 n=181               | 67 n=383 / 63 n=202 / 70 n=181               |
| gpr_d3m      | 59 n=387 / 57 n=202 / 62 n=185               | 65 n=383 / 64 n=202 / 65 n=181               | 67 n=383 / 67 n=202 / 66 n=181               |
| jk_mp_3m     | 59 n=369 / 56 n=218 / 64 n=151               | 66 n=369 / 65 n=218 / 67 n=151               | 67 n=369 / 68 n=218 / 66 n=151               |
| jk_mp_6m     | 59 n=369 / 59 n=239 / 59 n=130               | 66 n=369 / 65 n=239 / 67 n=130               | 67 n=369 / 64 n=239 / 72 n=130               |
| jk_cbi_3m    | 59 n=369 / 62 n=213 / 55 n=156               | 66 n=369 / 67 n=213 / 64 n=156               | 67 n=369 / 70 n=213 / 63 n=156               |
| jk_cbi_6m    | 59 n=369 / 62 n=211 / 55 n=158               | 66 n=369 / 66 n=211 / 65 n=158               | 67 n=369 / 70 n=211 / 63 n=158               |

**Agreement calls the signal confirms vs contradicts, weekly decisions, 2016-26**

| signal       | 21 s: same span / confirmed / contradicted   | 42 s: same span / confirmed / contradicted   | 63 s: same span / confirmed / contradicted   |
|:-------------|:---------------------------------------------|:---------------------------------------------|:---------------------------------------------|
| tone_rel_lvl | 56 n=239 / 56 n=135 / 57 n=104               | 63 n=236 / 67 n=132 / 58 n=104               | 67 n=236 / 71 n=132 / 61 n=104               |
| tone_rel_d1m | 62 n=178 / 57 n=91 / 67 n=87                 | 63 n=178 / 62 n=91 / 64 n=87                 | 67 n=178 / 64 n=91 / 71 n=87                 |
| tone_rel_d3m | 57 n=237 / 55 n=108 / 58 n=129               | 63 n=234 / 60 n=105 / 65 n=129               | 67 n=234 / 71 n=105 / 63 n=129               |
| news_lvl     | 56 n=209 / 56 n=129 / 57 n=80                | 66 n=209 / 60 n=129 / 74 n=80                | 70 n=209 / 68 n=129 / 72 n=80                |
| news_d1m     | 56 n=202 / 63 n=101 / 50 n=101               | 65 n=202 / 71 n=101 / 59 n=101               | 70 n=202 / 77 n=101 / 62 n=101               |
| epu_rel_d3m  | 57 n=243 / 59 n=131 / 55 n=112               | 63 n=239 / 65 n=130 / 61 n=109               | 67 n=239 / 75 n=130 / 58 n=109               |
| tpu_d3m      | 57 n=243 / 55 n=131 / 60 n=112               | 63 n=239 / 59 n=127 / 68 n=112               | 67 n=239 / 66 n=127 / 68 n=112               |
| gpr_d3m      | 57 n=243 / 55 n=133 / 60 n=110               | 63 n=239 / 62 n=133 / 65 n=106               | 67 n=239 / 65 n=133 / 70 n=106               |
| jk_mp_3m     | 56 n=225 / 50 n=129 / 65 n=96                | 64 n=225 / 64 n=129 / 66 n=96                | 68 n=225 / 67 n=129 / 68 n=96                |
| jk_mp_6m     | 56 n=225 / 56 n=141 / 57 n=84                | 64 n=225 / 65 n=141 / 63 n=84                | 68 n=225 / 63 n=141 / 75 n=84                |
| jk_cbi_3m    | 56 n=225 / 64 n=119 / 48 n=106               | 64 n=225 / 65 n=119 / 64 n=106               | 68 n=225 / 71 n=119 / 63 n=106               |
| jk_cbi_6m    | 56 n=225 / 64 n=129 / 46 n=96                | 64 n=225 / 67 n=129 / 60 n=96                | 68 n=225 / 76 n=129 / 56 n=96                |

**(b) OUTSIDE the agreement (the three old signals disagree; direction = the new signal), non-overlapping, 2010-26**

| signal       | 21 s                      | 42 s                    | 63 s                    |
|:-------------|:--------------------------|:------------------------|:------------------------|
| tone_rel_lvl | 55 [48-63] n=170 (10.1/y) | 53 [43-63] n=92 (5.5/y) | 56 [44-68] n=64 (3.9/y) |
| tone_rel_d1m | 51 [44-59] n=156 (9.3/y)  | 50 [40-60] n=84 (5.0/y) | 48 [36-60] n=61 (3.7/y) |
| tone_rel_d3m | 53 [45-60] n=169 (10.1/y) | 55 [45-65] n=92 (5.5/y) | 45 [34-57] n=64 (3.9/y) |
| news_lvl     | 47 [39-55] n=155 (9.2/y)  | 45 [35-56] n=86 (5.2/y) | 47 [35-59] n=60 (3.6/y) |
| news_d1m     | 48 [41-56] n=155 (9.2/y)  | 49 [39-60] n=85 (5.1/y) | 43 [32-56] n=60 (3.6/y) |
| epu_rel_d3m  | 46 [39-54] n=170 (10.1/y) | 44 [34-54] n=93 (5.6/y) | 53 [41-65] n=64 (3.9/y) |
| tpu_d3m      | 39 [32-47] n=170 (10.1/y) | 41 [31-51] n=93 (5.6/y) | 44 [32-56] n=64 (3.9/y) |
| gpr_d3m      | 43 [36-50] n=170 (10.1/y) | 46 [36-56] n=93 (5.6/y) | 48 [37-60] n=64 (3.9/y) |
| jk_mp_3m     | 47 [40-55] n=161 (9.6/y)  | 52 [42-62] n=88 (5.3/y) | 48 [36-60] n=61 (3.7/y) |
| jk_mp_6m     | 53 [46-61] n=161 (9.6/y)  | 55 [44-65] n=88 (5.3/y) | 51 [39-63] n=61 (3.7/y) |
| jk_cbi_3m    | 57 [49-64] n=161 (9.6/y)  | 50 [40-60] n=88 (5.3/y) | 54 [42-66] n=61 (3.7/y) |
| jk_cbi_6m    | 55 [47-62] n=161 (9.6/y)  | 53 [43-63] n=88 (5.3/y) | 49 [37-61] n=61 (3.7/y) |

**(b) OUTSIDE the agreement (the three old signals disagree; direction = the new signal), non-overlapping, 2016-26**

| signal       | 21 s                      | 42 s                    | 63 s                    |
|:-------------|:--------------------------|:------------------------|:------------------------|
| tone_rel_lvl | 50 [41-60] n=109 (10.1/y) | 51 [38-63] n=59 (5.5/y) | 54 [39-68] n=41 (3.9/y) |
| tone_rel_d1m | 52 [42-62] n=96 (8.9/y)   | 53 [40-66] n=51 (4.8/y) | 53 [37-68] n=38 (3.6/y) |
| tone_rel_d3m | 52 [43-61] n=108 (10.0/y) | 56 [43-68] n=59 (5.5/y) | 44 [30-59] n=41 (3.9/y) |
| news_lvl     | 47 [37-57] n=94 (8.7/y)   | 43 [31-57] n=53 (5.0/y) | 46 [31-62] n=37 (3.5/y) |
| news_d1m     | 52 [42-62] n=94 (8.7/y)   | 54 [41-67] n=52 (4.9/y) | 41 [26-57] n=37 (3.5/y) |
| epu_rel_d3m  | 47 [38-56] n=109 (10.1/y) | 50 [38-62] n=60 (5.6/y) | 61 [46-74] n=41 (3.9/y) |
| tpu_d3m      | 33 [25-42] n=109 (10.1/y) | 43 [32-56] n=60 (5.6/y) | 39 [26-54] n=41 (3.9/y) |
| gpr_d3m      | 45 [36-54] n=109 (10.1/y) | 47 [35-59] n=60 (5.6/y) | 41 [28-57] n=41 (3.9/y) |
| jk_mp_3m     | 44 [35-54] n=100 (9.3/y)  | 49 [36-62] n=55 (5.1/y) | 37 [23-53] n=38 (3.6/y) |
| jk_mp_6m     | 50 [40-60] n=100 (9.3/y)  | 47 [35-60] n=55 (5.1/y) | 37 [23-53] n=38 (3.6/y) |
| jk_cbi_3m    | 51 [41-61] n=100 (9.3/y)  | 53 [40-65] n=55 (5.1/y) | 63 [47-77] n=38 (3.6/y) |
| jk_cbi_6m    | 58 [48-67] n=100 (9.3/y)  | 58 [45-70] n=55 (5.1/y) | 58 [42-72] n=38 (3.6/y) |

**(b) OUTSIDE the agreement (the three old signals disagree; direction = the new signal), non-overlapping, 2023-26**

| signal       | 21 s                     | 42 s                    | 63 s                    |
|:-------------|:-------------------------|:------------------------|:------------------------|
| tone_rel_lvl | 47 [32-63] n=38 (10.1/y) | 48 [28-68] n=21 (5.7/y) | 36 [16-61] n=14 (3.9/y) |
| tone_rel_d1m | 55 [38-72] n=29 (7.7/y)  | 69 [44-86] n=16 (4.3/y) | 69 [42-87] n=13 (3.6/y) |
| tone_rel_d3m | 58 [42-72] n=38 (10.1/y) | 52 [32-72] n=21 (5.7/y) | 21 [8-48] n=14 (3.9/y)  |
| news_lvl     | 39 [22-59] n=23 (6.1/y)  | 50 [27-73] n=14 (3.8/y) | 40 [17-69] n=10 (2.8/y) |
| news_d1m     | 57 [37-74] n=23 (6.1/y)  | 64 [39-84] n=14 (3.8/y) | 70 [40-89] n=10 (2.8/y) |
| epu_rel_d3m  | 53 [37-68] n=38 (10.1/y) | 57 [37-76] n=21 (5.7/y) | 64 [39-84] n=14 (3.9/y) |
| tpu_d3m      | 39 [26-55] n=38 (10.1/y) | 38 [21-59] n=21 (5.7/y) | 36 [16-61] n=14 (3.9/y) |
| gpr_d3m      | 45 [30-60] n=38 (10.1/y) | 43 [24-63] n=21 (5.7/y) | 29 [12-55] n=14 (3.9/y) |
| jk_mp_3m     | 41 [26-59] n=29 (7.7/y)  | 38 [18-61] n=16 (4.3/y) | 36 [15-65] n=11 (3.1/y) |
| jk_mp_6m     | 38 [23-56] n=29 (7.7/y)  | 31 [14-56] n=16 (4.3/y) | 45 [21-72] n=11 (3.1/y) |
| jk_cbi_3m    | 48 [31-66] n=29 (7.7/y)  | 44 [23-67] n=16 (4.3/y) | 64 [35-85] n=11 (3.1/y) |
| jk_cbi_6m    | 59 [41-74] n=29 (7.7/y)  | 56 [33-77] n=16 (4.3/y) | 45 [21-72] n=11 (3.1/y) |

**(c) Paired differences on the weekly grid, circular block bootstrap** (points [95 % interval], p = share of draws <= 0)

| signal       | period   | 21 s: AND - same span   | 21 s: confirmed - contradicted     | 42 s: AND - same span   | 42 s: confirmed - contradicted     |
|:-------------|:---------|:------------------------|:-----------------------------------|:------------------------|:-----------------------------------|
| tone_rel_lvl | 2010-26  | +2.4 [-2, +7] p=0.18    | +6.6 [-7, +20] p=0.18 (n 246/137)  | +3.8 [-2, +9] p=0.09    | +10.6 [-6, +27] p=0.09 (n 243/137) |
| tone_rel_lvl | 2016-26  | -0.2 [-9, +7] p=0.52    | -0.4 [-18, +15] p=0.52 (n 135/104) | +4.0 [-6, +12] p=0.22   | +9.0 [-12, +28] p=0.22 (n 132/104) |
| tone_rel_d1m | 2010-26  | -0.8 [-6, +4] p=0.62    | -1.6 [-12, +9] p=0.62 (n 155/151)  | -1.5 [-7, +4] p=0.69    | -3.0 [-14, +7] p=0.69 (n 155/151)  |
| tone_rel_d1m | 2016-26  | -4.7 [-11, +2] p=0.90   | -9.5 [-23, +5] p=0.90 (n 91/87)    | -1.4 [-9, +6] p=0.64    | -2.8 [-18, +13] p=0.64 (n 91/87)   |
| tone_rel_d3m | 2010-26  | -0.3 [-7, +6] p=0.54    | -0.7 [-14, +12] p=0.54 (n 201/180) | -2.9 [-10, +4] p=0.77   | -6.2 [-21, +9] p=0.77 (n 198/180)  |
| tone_rel_d3m | 2016-26  | -1.9 [-12, +7] p=0.66   | -3.5 [-21, +14] p=0.66 (n 108/129) | -2.8 [-14, +7] p=0.71   | -5.1 [-25, +13] p=0.71 (n 105/129) |
| news_lvl     | 2010-26  | +1.4 [-5, +8] p=0.32    | +3.3 [-11, +19] p=0.32 (n 203/150) | -2.7 [-10, +4] p=0.77   | -6.5 [-23, +10] p=0.77 (n 203/150) |
| news_lvl     | 2016-26  | -0.6 [-8, +7] p=0.56    | -1.7 [-20, +19] p=0.56 (n 129/80)  | -5.1 [-14, +4] p=0.86   | -13.3 [-34, +11] p=0.86 (n 129/80) |
| news_d1m     | 2010-26  | +3.8 [-2, +10] p=0.12   | +7.6 [-5, +19] p=0.12 (n 167/170)  | +3.9 [-3, +10] p=0.13   | +7.7 [-6, +21] p=0.13 (n 167/170)  |
| news_d1m     | 2016-26  | +6.9 [-1, +15] p=0.04   | +13.9 [-2, +29] p=0.04 (n 101/101) | +5.9 [-3, +14] p=0.07   | +11.9 [-5, +29] p=0.07 (n 101/101) |
| epu_rel_d3m  | 2010-26  | -0.4 [-7, +6] p=0.55    | -0.9 [-15, +13] p=0.55 (n 205/182) | -1.5 [-9, +5] p=0.68    | -3.2 [-18, +11] p=0.68 (n 204/179) |
| epu_rel_d3m  | 2016-26  | +1.6 [-7, +10] p=0.35   | +3.4 [-15, +21] p=0.35 (n 131/112) | +2.2 [-6, +11] p=0.32   | +4.8 [-14, +22] p=0.32 (n 130/109) |
| tpu_d3m      | 2010-26  | -3.1 [-9, +3] p=0.84    | -6.7 [-20, +7] p=0.84 (n 206/181)  | -5.8 [-12, +1] p=0.96   | -12.4 [-26, +2] p=0.96 (n 202/181) |
| tpu_d3m      | 2016-26  | -2.2 [-10, +6] p=0.71   | -4.9 [-22, +13] p=0.71 (n 131/112) | -4.1 [-13, +5] p=0.81   | -8.8 [-27, +10] p=0.81 (n 127/112) |
| gpr_d3m      | 2010-26  | -2.0 [-8, +4] p=0.72    | -4.2 [-17, +9] p=0.72 (n 202/185)  | -0.4 [-7, +6] p=0.53    | -0.8 [-15, +14] p=0.53 (n 202/181) |
| gpr_d3m      | 2016-26  | -2.3 [-10, +6] p=0.69   | -5.1 [-22, +13] p=0.69 (n 133/110) | -1.5 [-10, +7] p=0.60   | -3.4 [-22, +16] p=0.60 (n 133/106) |
| jk_mp_3m     | 2010-26  | -3.1 [-9, +2] p=0.86    | -7.6 [-21, +6] p=0.86 (n 218/151)  | -0.9 [-8, +6] p=0.58    | -2.2 [-19, +15] p=0.58 (n 218/151) |
| jk_mp_3m     | 2016-26  | -6.1 [-15, +1] p=0.95   | -14.2 [-32, +3] p=0.95 (n 129/96)  | -0.9 [-11, +8] p=0.58   | -2.1 [-25, +20] p=0.58 (n 129/96)  |
| jk_mp_6m     | 2010-26  | -0.1 [-6, +6] p=0.51    | -0.2 [-17, +16] p=0.51 (n 239/130) | -0.7 [-7, +6] p=0.59    | -2.1 [-19, +17] p=0.59 (n 239/130) |
| jk_mp_6m     | 2016-26  | -0.4 [-9, +7] p=0.56    | -1.1 [-23, +19] p=0.56 (n 141/84)  | +0.8 [-8, +10] p=0.46   | +2.2 [-22, +27] p=0.46 (n 141/84)  |
| jk_cbi_3m    | 2010-26  | +2.9 [-3, +9] p=0.16    | +6.8 [-7, +20] p=0.16 (n 213/156)  | +1.1 [-6, +7] p=0.38    | +2.6 [-13, +17] p=0.38 (n 213/156) |
| jk_cbi_3m    | 2016-26  | +7.4 [-0, +16] p=0.03   | +15.8 [-0, +32] p=0.03 (n 119/106) | +0.3 [-10, +10] p=0.47  | +0.6 [-21, +21] p=0.47 (n 119/106) |
| jk_cbi_6m    | 2010-26  | +3.0 [-3, +9] p=0.17    | +7.0 [-7, +21] p=0.17 (n 211/158)  | +0.3 [-7, +8] p=0.47    | +0.7 [-15, +18] p=0.47 (n 211/158) |
| jk_cbi_6m    | 2016-26  | +7.9 [+0, +16] p=0.02   | +18.5 [+1, +35] p=0.02 (n 129/96)  | +3.0 [-6, +12] p=0.25   | +7.0 [-13, +29] p=0.25 (n 129/96)  |

## 8. Selection by the declared rule, the Round 5 bar and the timing placebo
Declared rule: highest LOWER Wilson bound of the AND rule's 2010-15 non-overlapping 21-session accuracy among candidates with at least 6 such decisions a
year in 2010-15. All 12 are eligible; the lower bounds are 0.35-0.46, i.e. the rule separates nothing: the three tone signals, `news_lvl` and the two
3-month surprise sums are within 0.02 of each other.

| signal       |   n_2010-15 |   dec_per_year_2010-15 |   accuracy_2010-15 |   lo_2010-15 |   hi_2010-15 | eligible   | final   |
|:-------------|------------:|-----------------------:|-------------------:|-------------:|-------------:|:-----------|:--------|
| tone_rel_lvl |          43 |                  7.181 |              0.605 |        0.456 |        0.736 | True       | True    |
| tone_rel_d1m |          37 |                  6.179 |              0.595 |        0.435 |        0.737 | True       | False   |
| tone_rel_d3m |          45 |                  7.515 |              0.6   |        0.455 |        0.73  | True       | False   |
| news_lvl     |          36 |                  6.012 |              0.611 |        0.449 |        0.752 | True       | False   |
| news_d1m     |          38 |                  6.346 |              0.526 |        0.373 |        0.675 | True       | False   |
| epu_rel_d3m  |          37 |                  6.179 |              0.541 |        0.384 |        0.69  | True       | False   |
| tpu_d3m      |          39 |                  6.513 |              0.538 |        0.386 |        0.684 | True       | False   |
| gpr_d3m      |          36 |                  6.012 |              0.5   |        0.345 |        0.655 | True       | False   |
| jk_mp_3m     |          42 |                  7.014 |              0.595 |        0.445 |        0.73  | True       | False   |
| jk_mp_6m     |          45 |                  7.515 |              0.511 |        0.37  |        0.65  | True       | False   |
| jk_cbi_3m    |          42 |                  7.014 |              0.595 |        0.445 |        0.73  | True       | False   |
| jk_cbi_6m    |          37 |                  6.179 |              0.568 |        0.409 |        0.713 | True       | False   |

Final: **`tone_rel_lvl`** - selected by the declared rule.

**The bar, cell by cell, for the final** (non-overlapping decisions)

|   horizon | period   | agreement rule   | AND tone_rel_lvl         |   gain (pts) | placebo +63: acc n, gain   | placebo +126: acc n, gain   |
|----------:|:---------|:-----------------|:-------------------------|-------------:|:---------------------------|:----------------------------|
|        21 | 2010-26  | 59 n=156 (9.3/y) | 57 [48-67] n=101 (6.0/y) |         -1.5 | 58 n=100, -1.0             | 58 n=93, -0.9               |
|        21 | 2016-26  | 57 n=96 (8.9/y)  | 55 [42-67] n=58 (5.4/y)  |         -2.1 | 51 n=57, -6.4              | 57 n=54, +0.1               |
|        21 | 2023-26  | 60 n=35 (9.3/y)  | 52 [33-70] n=25 (6.6/y)  |         -8   | 32 n=19, -28.4             | 56 n=18, -4.4               |
|        42 | 2010-26  | 61 n=89 (5.3/y)  | 66 [54-77] n=62 (3.7/y)  |          5.5 | 66 n=61, +4.9              | 67 n=58, +6.6               |
|        42 | 2016-26  | 59 n=56 (5.2/y)  | 64 [48-78] n=36 (3.4/y)  |          5   | 67 n=36, +7.7              | 70 n=33, +10.8              |
|        42 | 2023-26  | 45 n=20 (5.4/y)  | 47 [25-70] n=15 (4.1/y)  |          1.7 | 42 n=12, -3.3              | 58 n=12, +13.3              |
|        63 | 2010-26  | 72 n=61 (3.7/y)  | 78 [64-88] n=46 (2.8/y)  |          6.1 | 76 n=46, +4.0              | 79 n=42, +6.4               |
|        63 | 2016-26  | 71 n=38 (3.6/y)  | 78 [59-89] n=27 (2.5/y)  |          6.7 | 74 n=27, +3.0              | 76 n=25, +4.9               |
|        63 | 2023-26  | 50 n=14 (3.9/y)  | 55 [28-79] n=11 (3.1/y)  |          4.5 | 44 n=9, -5.6               | 56 n=9, +5.6                |

Bar components: gain_ok = False, count21_ok = False, count42_ok = False, not_worse_2023 = False, placebo_ok = False, met = False, met_strict_42_count = False

**The same verdict for every candidate** (so that the selection rule cannot hide a better one)

| signal       | gain_ok   | count21_ok   | count42_ok   | not_worse_2023   | placebo_ok   | met   | met_strict_42_count   |
|:-------------|:----------|:-------------|:-------------|:-----------------|:-------------|:------|:----------------------|
| tone_rel_lvl | False     | False        | False        | False            | False        | False | False                 |
| tone_rel_d1m | False     | False        | False        | True             | False        | False | False                 |
| tone_rel_d3m | False     | False        | False        | False            | False        | False | False                 |
| news_lvl     | False     | True         | False        | False            | False        | False | False                 |
| news_d1m     | False     | False        | False        | False            | False        | False | False                 |
| epu_rel_d3m  | False     | False        | False        | True             | False        | False | False                 |
| tpu_d3m      | False     | False        | False        | False            | False        | False | False                 |
| gpr_d3m      | False     | False        | False        | False            | False        | False | False                 |
| jk_mp_3m     | False     | False        | False        | False            | False        | False | False                 |
| jk_mp_6m     | False     | False        | False        | False            | False        | False | False                 |
| jk_cbi_3m    | False     | False        | False        | True             | False        | False | False                 |
| jk_cbi_6m    | True      | False        | False        | True             | False        | False | False                 |

**Timing placebo, all candidates: gain of the AND rule over the agreement rule in points, with the live signal and with the signal 63 / 126 sessions stale**

| signal       | 2010-26 21 s: live / +63 / +126   | 2010-26 42 s: live / +63 / +126   | 2016-26 21 s: live / +63 / +126   | 2016-26 42 s: live / +63 / +126   |
|:-------------|:----------------------------------|:----------------------------------|:----------------------------------|:----------------------------------|
| tone_rel_lvl | -2 / -1 / -1                      | +5 / +5 / +7                      | -2 / -6 / +0                      | +5 / +8 / +11                     |
| tone_rel_d1m | -2 / -6 / -2                      | +1 / +3 / -1                      | -2 / -9 / -5                      | +6 / -1 / -4                      |
| tone_rel_d3m | -5 / -3 / -8                      | -2 / +4 / -5                      | -8 / -6 / -11                     | -3 / +1 / -3                      |
| news_lvl     | +0 / -1 / -7                      | +1 / +6 / -2                      | +1 / +2 / -7                      | -4 / +7 / -3                      |
| news_d1m     | -6 / -2 / +3                      | +1 / +2 / +5                      | -5 / -0 / +2                      | +8 / +10 / +5                     |
| epu_rel_d3m  | -2 / +4 / -5                      | -1 / +10 / +3                     | +1 / +4 / -4                      | +2 / +9 / +7                      |
| tpu_d3m      | -8 / -6 / -5                      | -3 / -5 / -0                      | -8 / -7 / -5                      | +4 / -16 / -3                     |
| gpr_d3m      | -4 / -4 / -3                      | +6 / -3 / -1                      | +1 / -6 / -5                      | +9 / -4 / -9                      |
| jk_mp_3m     | -7 / -8 / -9                      | +3 / +1 / -3                      | -12 / -6 / -6                     | +3 / -5 / -4                      |
| jk_mp_6m     | -7 / -11 / -10                    | +2 / -1 / -4                      | -4 / -13 / -7                     | -6 / -0 / +0                      |
| jk_cbi_3m    | +3 / +4 / +2                      | +2 / +5 / -1                      | +7 / +9 / +5                      | +9 / +8 / +1                      |
| jk_cbi_6m    | +6 / -1 / +2                      | +4 / -1 / -6                      | +13 / +5 / +7                     | +12 / +7 / -6                     |

**Standalone accuracy when stale, non-overlapping, 2010-26**

| signal       | standalone 21 s: live / +63 / +126   | standalone 63 s: live / +63 / +126   |
|:-------------|:-------------------------------------|:-------------------------------------|
| tone_rel_lvl | 55 n=207 / 54 n=207 / 53 n=207       | 51 n=69 / 42 n=69 / 48 n=69          |
| tone_rel_d1m | 49 n=192 / 45 n=194 / 46 n=194       | 52 n=67 / 37 n=67 / 55 n=67          |
| tone_rel_d3m | 50 n=206 / 51 n=206 / 51 n=206       | 58 n=69 / 46 n=69 / 57 n=69          |
| news_lvl     | 48 n=191 / 56 n=194 / 48 n=197       | 50 n=64 / 54 n=65 / 48 n=66          |
| news_d1m     | 48 n=190 / 51 n=193 / 55 n=196       | 39 n=64 / 48 n=65 / 42 n=66          |
| epu_rel_d3m  | 51 n=208 / 55 n=208 / 46 n=208       | 48 n=69 / 64 n=69 / 45 n=69          |
| tpu_d3m      | 41 n=208 / 47 n=205 / 48 n=202       | 48 n=69 / 44 n=68 / 52 n=67          |
| gpr_d3m      | 47 n=208 / 55 n=208 / 49 n=208       | 49 n=69 / 65 n=69 / 48 n=69          |
| jk_mp_3m     | 46 n=198 / 49 n=201 / 52 n=204       | 50 n=66 / 45 n=67 / 56 n=68          |
| jk_mp_6m     | 47 n=198 / 49 n=201 / 52 n=204       | 53 n=66 / 48 n=67 / 53 n=68          |
| jk_cbi_3m    | 55 n=198 / 52 n=201 / 51 n=204       | 48 n=66 / 55 n=67 / 50 n=68          |
| jk_cbi_6m    | 55 n=198 / 47 n=201 / 50 n=204       | 56 n=66 / 52 n=67 / 47 n=68          |

Reading: a gain that survives when the signal is 3-6 months old is a regime, not information. `tone_rel_lvl` (the final), `news_d1m`, `epu_rel_d3m` and
`jk_cbi_3m` keep or increase their "gain" when stale. `jk_cbi_6m` loses all of it in 2010-26 and about half in 2016-26, which is why it is called a lead in
the verdict and why it still fails the placebo test; `gpr_d3m` loses its 42-session gain when stale but has none at 21 sessions.

## 9. Daily stream of the final rule, incremental test
Weekly tranches of each AND rule held 21 sessions (|position| <= 1), `wf.pnl_from_positions` at 1.2 pips per unit turnover, 2010-26. The final rule's book is
a subset of the agreement-rule book and inherits its record; it does not beat it.

**Net Sharpe of every candidate's AND-rule book (1.2 pips), and the agreement-rule book as reference**

| variant                  |   2010-2026 |   2016-2026 |   2023-2026 |   2010-2015 |
|:-------------------------|------------:|------------:|------------:|------------:|
| and_tone_rel_lvl         |        0.49 |        0.38 |        0.01 |        0.65 |
| and_tone_rel_d1m         |        0.47 |        0.27 |        1.11 |        0.72 |
| and_tone_rel_d3m         |        0.41 |        0.3  |        0.31 |        0.56 |
| and_news_lvl             |        0.4  |        0.3  |        0.66 |        0.54 |
| and_news_d1m             |        0.44 |        0.52 |        0.86 |        0.34 |
| and_epu_rel_d3m          |        0.37 |        0.45 |        0.18 |        0.28 |
| and_tpu_d3m              |        0.3  |        0.29 |        0.64 |        0.33 |
| and_gpr_d3m              |        0.23 |        0.24 |        0.24 |        0.23 |
| and_jk_mp_3m             |        0.26 |        0.21 |       -0.04 |        0.34 |
| and_jk_mp_6m             |        0.33 |        0.29 |       -0.16 |        0.4  |
| and_jk_cbi_3m            |        0.5  |        0.65 |        0.71 |        0.39 |
| and_jk_cbi_6m            |        0.55 |        0.71 |        0.66 |        0.41 |
| agree3_reference         |        0.52 |        0.51 |        0.43 |        0.56 |
| and_tone_rel_lvl_cost0.6 |        0.5  |        0.39 |        0.02 |        0.65 |

**Final rule by year** (weekly decisions held 21 sessions)

|   year |   decisions |   long_share |   accuracy |   net_win_rate |   gross_bp |   net_bp |   avg_hold |   agree3_decisions |   agree3_accuracy |   book_sharpe |
|-------:|------------:|-------------:|-----------:|---------------:|-----------:|---------:|-----------:|-------------------:|------------------:|--------------:|
|   2010 |          31 |        0.387 |      0.613 |          0.581 |     86.034 |   84.242 |         21 |                 31 |             0.613 |         0.774 |
|   2011 |          22 |        0.636 |      0.682 |          0.682 |    105.779 |  104.054 |         21 |                 33 |             0.636 |         0.89  |
|   2012 |          19 |        0.368 |      0.579 |          0.579 |    -20.365 |  -22.204 |         21 |                 28 |             0.607 |        -0.155 |
|   2013 |           3 |        1     |      0.667 |          0.667 |    -77.367 |  -79.161 |         21 |                  7 |             0.429 |        -0.48  |
|   2014 |          21 |        0     |      0.857 |          0.857 |    111.814 |  110.004 |         21 |                 24 |             0.75  |         1.553 |
|   2015 |          15 |        0     |      0.667 |          0.667 |    152.879 |  150.739 |         21 |                 21 |             0.619 |         0.889 |
|   2016 |           7 |        0     |      0.571 |          0.571 |    -43.549 |  -45.726 |         21 |                 24 |             0.583 |        -0.436 |
|   2017 |           2 |        1     |      0     |          0     |   -180.202 | -182.438 |         21 |                 19 |             0.684 |        -1.101 |
|   2018 |          21 |        0     |      0.619 |          0.619 |     52.929 |   50.853 |         21 |                 21 |             0.619 |         0.622 |
|   2019 |           4 |        0.75  |      0.25  |          0.25  |    -36.167 |  -38.317 |         21 |                 12 |             0.5   |        -0.376 |
|   2020 |           7 |        1     |      0.857 |          0.857 |    161.915 |  159.81  |         21 |                 25 |             0.52  |         1.458 |
|   2021 |          26 |        0.077 |      0.577 |          0.577 |     40.058 |   38.003 |         21 |                 34 |             0.441 |         0.719 |
|   2022 |          18 |        0     |      0.722 |          0.722 |    142.402 |  140.142 |         21 |                 31 |             0.742 |         1.284 |
|   2023 |           8 |        0.375 |      0.25  |          0.25  |    -96.614 |  -98.859 |         21 |                 17 |             0.353 |        -0.749 |
|   2024 |          20 |        0.15  |      0.5   |          0.5   |     29.703 |   27.476 |         21 |                 23 |             0.522 |         0.416 |
|   2025 |           7 |        1     |      0.429 |          0.429 |    -28.682 |  -30.742 |         21 |                 19 |             0.632 |        -0.429 |
|   2026 |          15 |        0.2   |      0.6   |          0.6   |     35.338 |   33.269 |         21 |                 18 |             0.667 |         0.527 |

**Incremental test (meta.combine EW)**

| combo                                                      | period    |    n |   sharpe |     t |   mean_bp |
|:-----------------------------------------------------------|:----------|-----:|---------:|------:|----------:|
| two-way weak_signals + regime_trend                        | 2010-2026 | 4373 |    0.563 | 2.347 |     0.583 |
| two-way weak_signals + regime_trend                        | 2016-2026 | 2817 |    0.636 | 2.128 |     0.738 |
| two-way weak_signals + regime_trend                        | 2023-2026 | 1000 |    0.356 | 0.708 |     0.42  |
| three-way + text_news                                      | 2010-2026 | 4373 |    0.599 | 2.495 |     0.533 |
| three-way + text_news                                      | 2016-2026 | 2817 |    0.629 | 2.103 |     0.624 |
| three-way + text_news                                      | 2023-2026 | 1000 |    0.283 | 0.563 |     0.286 |
| three-way + selective (agreement rule book, for reference) | 2010-2026 | 4373 |    0.57  | 2.376 |     0.545 |
| three-way + selective (agreement rule book, for reference) | 2016-2026 | 2817 |    0.641 | 2.143 |     0.691 |
| three-way + selective (agreement rule book, for reference) | 2023-2026 | 1000 |    0.405 | 0.807 |     0.446 |

**Daily P&L correlation of the final stream with the live streams**

| other           |   corr_all_days |   corr_active_days |   corr_2016-26 |
|:----------------|----------------:|-------------------:|---------------:|
| weak_signals    |           0.331 |              0.446 |          0.391 |
| regime_trend    |           0.505 |              0.724 |          0.465 |
| selective_daily |           0.841 |              0.965 |          0.752 |

## 10. Leak checks
(1) With the labels permuted every rule sits at chance (shuffled mean 49-52 %). The AND rules beat the shuffle only because they inherit the agreement
rule's skill. No standalone rule beats it at 21 sessions (p 0.07-0.77); `tone_rel_lvl` standalone is just above the shuffled 95th percentile at 42 and 63
sessions on the weekly grid (55 % against 54-55 %; p 0.03-0.05), which is its 2010-15 regime effect. (2) Shifting the signal 21 sessions FORWARD in time (look-ahead)
does not produce a result the live signal lacks; shifting it 1 / 5 / 21 sessions back barely moves the slow level and leaves the change signals at chance.
(2b) The truncation test rebuilds all 12 signals from raw data cut at the date (documents published up to the day before, monthly indices by their lag,
shocks up to the day before) and reproduces the stored row exactly on all five dates. (2c) Re-dating every speech by the day BIS posted it (stricter than
the declared speech date + 1) changes nothing systematically. (3) The correlation table is in section 6: the largest correlations with the forward
return are 0.11 at 21 sessions and 0.19-0.20 at 63 (`tone_rel_lvl`, `jk_cbi_3m`); nothing is a label in disguise.

**(1) Labels permuted (300 draws), weekly decisions 2010-26**

| signal       | rule       |   h |   n_weekly |   real_acc |   shuffled_mean |   shuffled_p05 |   shuffled_p95 |   p_shuffled_ge_real |
|:-------------|:-----------|----:|-----------:|-----------:|----------------:|---------------:|---------------:|---------------------:|
| tone_rel_lvl | and        |  21 |        246 |      0.614 |           0.511 |          0.455 |          0.569 |                0.003 |
| tone_rel_lvl | standalone |  21 |        864 |      0.534 |           0.514 |          0.488 |          0.541 |                0.123 |
| tone_rel_d3m | and        |  21 |        201 |      0.587 |           0.504 |          0.448 |          0.572 |                0.01  |
| tone_rel_d3m | standalone |  21 |        860 |      0.49  |           0.5   |          0.472 |          0.53  |                0.74  |
| jk_mp_6m     | and        |  21 |        239 |      0.59  |           0.497 |          0.444 |          0.548 |                0.003 |
| jk_mp_6m     | standalone |  21 |        830 |      0.517 |           0.493 |          0.466 |          0.519 |                0.067 |
| tone_rel_lvl | and        |  42 |        243 |      0.683 |           0.512 |          0.465 |          0.56  |                0     |
| tone_rel_lvl | standalone |  42 |        861 |      0.547 |           0.515 |          0.485 |          0.545 |                0.033 |
| tone_rel_d3m | and        |  42 |        198 |      0.616 |           0.499 |          0.439 |          0.556 |                0     |
| tone_rel_d3m | standalone |  42 |        857 |      0.494 |           0.499 |          0.47  |          0.527 |                0.617 |
| jk_mp_6m     | and        |  42 |        239 |      0.649 |           0.496 |          0.444 |          0.552 |                0     |
| jk_mp_6m     | standalone |  42 |        830 |      0.519 |           0.491 |          0.465 |          0.52  |                0.053 |
| tone_rel_lvl | and        |  63 |        243 |      0.704 |           0.513 |          0.461 |          0.564 |                0     |
| tone_rel_lvl | standalone |  63 |        857 |      0.545 |           0.517 |          0.49  |          0.544 |                0.047 |
| tone_rel_d3m | and        |  63 |        198 |      0.677 |           0.508 |          0.444 |          0.566 |                0     |
| tone_rel_d3m | standalone |  63 |        853 |      0.518 |           0.501 |          0.475 |          0.528 |                0.18  |
| jk_mp_6m     | and        |  63 |        239 |      0.644 |           0.497 |          0.444 |          0.548 |                0     |
| jk_mp_6m     | standalone |  63 |        830 |      0.495 |           0.491 |          0.461 |          0.522 |                0.433 |

**(2) Signal shifted in time, non-overlapping 2010-26, 21 / 42 sessions**

| signal       | rule       | look-ahead -21      | live                | +1                  | +5                  | +21                 |
|:-------------|:-----------|:--------------------|:--------------------|:--------------------|:--------------------|:--------------------|
| tone_rel_lvl | and        | 60 n=101 / 67 n=60  | 57 n=101 / 66 n=62  | 58 n=101 / 68 n=63  | 57 n=105 / 65 n=65  | 58 n=102 / 66 n=61  |
| tone_rel_lvl | standalone | 56 n=207 / 61 n=104 | 55 n=207 / 57 n=103 | 54 n=207 / 57 n=103 | 56 n=207 / 59 n=103 | 54 n=207 / 61 n=104 |
| tone_rel_d1m | and        | 57 n=102 / 67 n=67  | 57 n=99 / 61 n=70   | 54 n=97 / 58 n=69   | 59 n=98 / 61 n=71   | 56 n=100 / 62 n=71  |
| tone_rel_d1m | standalone | 52 n=192 / 53 n=97  | 49 n=192 / 46 n=97  | 51 n=192 / 45 n=97  | 46 n=192 / 44 n=97  | 42 n=193 / 51 n=98  |
| tone_rel_d3m | and        | 60 n=96 / 56 n=59   | 54 n=100 / 59 n=61  | 55 n=100 / 59 n=61  | 55 n=95 / 61 n=59   | 53 n=95 / 65 n=63   |
| tone_rel_d3m | standalone | 45 n=206 / 44 n=103 | 50 n=206 / 47 n=103 | 51 n=206 / 50 n=103 | 52 n=206 / 48 n=103 | 49 n=206 / 51 n=103 |
| jk_mp_6m     | and        | 56 n=98 / 69 n=61   | 52 n=103 / 62 n=64  | 51 n=103 / 62 n=64  | 53 n=102 / 59 n=64  | 50 n=103 / 61 n=62  |
| jk_mp_6m     | standalone | 54 n=197 / 53 n=99  | 47 n=198 / 49 n=99  | 47 n=198 / 51 n=99  | 48 n=198 / 48 n=99  | 51 n=199 / 50 n=100 |

**(2b) Truncation test** (raw data cut as a user would have held them on that date; the row must be identical)

| asof       |   signals_defined |   rows_equal |   of |   max_abs_diff | mismatch   |
|:-----------|------------------:|-------------:|-----:|---------------:|:-----------|
| 2012-06-29 |                12 |           12 |   12 |              0 |            |
| 2016-11-15 |                12 |           12 |   12 |              0 |            |
| 2020-03-16 |                12 |           12 |   12 |              0 |            |
| 2022-09-30 |                12 |           12 |   12 |              0 |            |
| 2025-02-14 |                12 |           12 |   12 |              0 |            |

**(2c) Tone signals re-dated by the BIS posting date** (non-overlapping)

| signal       | period   | standalone 21 s: speech date / BIS posting date   | standalone 42 s: speech date / BIS posting date   | standalone 63 s: speech date / BIS posting date   | AND 21 s: speech date / posting date   | AND 42 s: speech date / posting date   |
|:-------------|:---------|:--------------------------------------------------|:--------------------------------------------------|:--------------------------------------------------|:---------------------------------------|:---------------------------------------|
| tone_rel_lvl | 2010-26  | 55 n=207 / 56 n=207                               | 57 n=103 / 56 n=103                               | 51 n=69 / 49 n=69                                 | 57 n=101 / 54 n=100                    | 66 n=62 / 62 n=60                      |
| tone_rel_lvl | 2016-26  | 49 n=132 / 52 n=132                               | 55 n=65 / 51 n=65                                 | 45 n=44 / 45 n=44                                 | 55 n=58 / 52 n=58                      | 64 n=36 / 57 n=35                      |
| tone_rel_d1m | 2010-26  | 49 n=192 / 51 n=192                               | 46 n=97 / 45 n=97                                 | 52 n=67 / 54 n=67                                 | 57 n=99 / 61 n=98                      | 61 n=70 / 65 n=68                      |
| tone_rel_d1m | 2016-26  | 48 n=119 / 50 n=119                               | 55 n=60 / 45 n=60                                 | 50 n=42 / 48 n=42                                 | 55 n=62 / 63 n=59                      | 65 n=43 / 70 n=40                      |
| tone_rel_d3m | 2010-26  | 50 n=206 / 52 n=207                               | 47 n=103 / 55 n=103                               | 58 n=69 / 58 n=69                                 | 54 n=100 / 50 n=98                     | 59 n=61 / 65 n=60                      |
| tone_rel_d3m | 2016-26  | 49 n=131 / 50 n=132                               | 43 n=65 / 55 n=65                                 | 55 n=44 / 55 n=44                                 | 49 n=55 / 49 n=53                      | 56 n=34 / 64 n=33                      |

## 11. The current reading
From `data/macro/text_news_tone_daily.csv` (row d = documents published up to and including d). **Context, not a vote** - the tests above give this reading
no predictive value. As of the last rows: the Fed's 90-day tone is unusually hawkish against its own history (10 scored documents, the latest being the
September minutes and a speech of 8 October; the October statement has fewer than 5 hits), the ECB's mildly so (13 scored documents to 5 November), so the
RELATIVE tone is about +1.5 z (Fed more hawkish relative to the ECB) and about 1.4 higher than three months before; the 30-day comparison is undefined after
5 November because BIS has posted no monetary Fed speech since mid-October. Under the declared prior that is a vote for a LOWER EUR/USD from the level and
the 3-month change, and a marginal vote the other way from the 1-month change. The news-sentiment and policy-surprise signals are undefined today (copies
end 2025-05 and 2025-10).

| series      | last defined on   |   value |
|:------------|:------------------|--------:|
| fed_tone_30 | 2026-11-05        |   0.635 |
| fed_tone_90 | 2026-11-06        |   0.587 |
| ecb_tone_30 | 2026-11-06        |   0.262 |
| ecb_tone_90 | 2026-11-06        |   0.24  |
| fed_z_30    | 2026-11-05        |   2.331 |
| fed_z_90    | 2026-11-06        |   2.46  |
| ecb_z_30    | 2026-11-06        |   0.995 |
| ecb_z_90    | 2026-11-06        |   0.955 |
| rel_30      | 2026-11-05        |   1.26  |
| rel_90      | 2026-11-06        |   1.505 |
| rel_d1m     | 2026-11-05        |  -0.187 |
| rel_d3m     | 2026-11-06        |   1.353 |

Last scored document: Fed 2026-10-08, ECB 2026-11-05. Signals on the last session of the store (2026-11-05): `tone_rel_lvl` -1.505, `tone_rel_d1m` +0.187, `tone_rel_d3m` -1.353, `news_lvl` n/a, `news_d1m` n/a, `epu_rel_d3m` -0.184, `tpu_d3m` -0.296, `gpr_d3m` -0.120, `jk_mp_3m` n/a, `jk_mp_6m` n/a, `jk_cbi_3m` n/a, `jk_cbi_6m` n/a.

## 12. Variant count, replication, what was not done
* **Variants: 12** candidate signals = 12 AND rules, all reported above; one final by the declared rule. The orthogonalised, shifted, re-dated and other-era
  rows are controls of those 12 and were never selected from.
* **Replication (round 6).** Other era: the standalone table for 2004-09 in section 5 (no test year, no selection). The only signal with a 2010-26 record,
  `jk_cbi_6m`, is at 51 / 55 / 52 % there and at 45 / 45 / 40 % in 2010-15. Other pairs: not run. The shock series exist for the Fed and the ECB only, and a
  relative tone for other pairs (Fed against the Bank of England, Bank of Japan, ... from the same BIS archive) would replicate a signal that has already
  failed on the pair it was designed for.
* **Not done:** a language-model tone score (the brief asked for a transparent fixed dictionary; a second scorer after seeing these results would be
  tuning); Fed-only and ECB-only tone as separate candidates (budget of 12); intraday reaction to individual speeches (arm E found event reactions
  unprofitable).
* **Hosts that would improve the data:** `www.frbsf.org` (live news sentiment), `www.federalreserve.gov` and `www.ecb.europa.eu` (official texts on the day,
  complete ECB press conferences, the EA-MPD file behind the ECB shocks), `archive.riksbank.se` (the original Apel-Blix Grimaldi word list).
