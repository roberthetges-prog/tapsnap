"""Arm Z ("text_news"): text and news as an EXTRA VOTE for multi-week EUR/USD direction (round 7).

EVERYTHING IN THIS DOCSTRING AND THE CONSTANTS BELOW (dictionary, signals, signs, lags, evaluation, selection rule)
WAS WRITTEN BEFORE ANY ACCURACY NUMBER WAS COMPUTED. Known at that point: which hosts answer, file formats, date
ranges and the number of documents per institution. No tone score had been compared with any return.

Idea: text and news are the only large class of information the project has never used. reports/arm_policy_cycle.md
found that EUR/USD moves BEFORE policy turns; what moves pricing before a turn is communication. Four small families,
each candidate one fixed, signed signal (positive = vote for long EUR/USD, negative = short, zero / missing = no vote).

DATA (all fetched 2026-11-11/12; raw copies in data/raw/text_news/, which is git-ignored; cleaned series in data/macro/)
  FOMC statements and minutes   https://raw.githubusercontent.com/vtasca/fed-statement-scraping/master/communications.csv
                                third-party scrape of federalreserve.gov, 2000-02 .. 2026-10; column `Release Date` is
                                used (minutes come out 3 weeks after the meeting, 5-7 weeks before 2005).
  BIS central bankers' speeches https://www.bis.org/pages/download-central-bankers-speeches/speeches-{1996..2026}.zip
                                (20,726 speeches of all central banks; bulk build of 2026-08-23 ends 2026-06-22) plus the
                                live listing https://www.bis.org/speeches/central-bank?organisation[]=... for the months
                                after the bulk build (Fed and ECB speakers only). `date` = date of the speech (interview:
                                date of publication); the URL / slug carries the BIS posting date (median 1-5 days later).
  ECB speeches copy             https://media.githubusercontent.com/media/Moritz-Pfeifer/CentralBankRoBERTa/main/Data/ECB/all_ECB_speeches.csv
                                copy of the ECB's own file, 1997-02 .. 2023-02. CROSS-CHECK ONLY (monthly ECB tone from
                                the BIS selection against the ECB's complete file); it does not enter any signal.
  SF Fed Daily News Sentiment   https://raw.githubusercontent.com/wattyven/VIX-study/main/sentiment/news_sentiment_data.csv
                                third-party copy, one vintage, 1980-01 .. 2025-05-18. UNDEFINED after the copy ends
                                (www.frbsf.org is blocked). The index is re-estimated, so history is not real-time.
  Economic Policy Uncertainty   FRED USEPUINDXD (US, daily), EUEPUINDXM (Europe, monthly), EPUTRADE (US trade policy,
                                monthly), EPUMONETARY (cached, not used as a candidate). Monthly indices are revised.
  Geopolitical Risk, daily      https://raw.githubusercontent.com/iacoviel/iacoviel.github.io/master/gpr_files/data_gpr_daily_recent.xls
  Jarocinski-Karadi shocks      https://raw.githubusercontent.com/marekjarocinski/jkshocks_update_fed/main/shocks_fed_jk_t.csv (1990 .. 2026-09)
                                https://raw.githubusercontent.com/marekjarocinski/jkshocks_update_ecb/main/shocks_ecb_mpd_me_d.csv (1999 .. 2025-10)
                                columns MP_median / CBI_median (median-rotation decomposition of the surprise into a pure
                                policy shock and a central-bank information shock), in percentage points.
PUBLICATION LAGS (on the session grid the closing calendar date is c; `_align_lagged(., c, k)` uses stamps <= c - k days)
  texts                 dated by publication date d, used from the next session: k = 1.
  JK shocks             announcement date d, k = 1. (The files are updated a few times a year; the surprise itself is
                        observable on the day. Undefined 60 days after the last row of either file.)
  SF Fed sentiment      daily value, published weekly: k = 7; switched off when the newest usable stamp is > 10 days old.
  GPR daily             published with about a week's delay: k = 7; same staleness rule.
  US daily EPU          monthly mean of complete months only, treated like the monthly European index.
  monthly EPU (Europe)  reference month m usable from month-end + 30 days (+1); categorical EPU (trade): + 45 days;
                        switched off when the newest usable observation became available more than 75 days ago.

FAMILY 1 - CENTRAL-BANK TONE: THE DICTIONARY (constant TONE_DICT below, frozen before results)
  Construction principle: Apel & Blix Grimaldi (2012), "The information content of central bank minutes", Sveriges
  Riksbank Working Paper 261 (journal version: "How informative are central bank minutes?", Review of Economics 65(1),
  2014): count directional words standing next to a small set of topic nouns (inflation, prices, wages, growth, ...),
  hawkish when the direction is "up", dovish when "down", and form the net index (hawk - dove) / (hawk + dove).
  Extended, as in the later policy-stance word lists (Bennani & Neuenkirch 2017, Applied Economics 49; Tadle 2022,
  Journal of Economics and Business 118), with outright stance terms (restrictive, vigilance, accommodative, ...), an
  inverted "slack" group (unemployment up = dovish) and a negation rule. HONEST NOTE: the papers' own word lists could
  not be downloaded from this sandbox (archive.riksbank.se is blocked), so the English lists below are THIS ARM'S OWN,
  written from the published principle and frozen here; they are not a verbatim copy of a published dictionary.
  Scoring of one document:
    * lower-case; multi-word expressions in TONE_DICT["phrases"] are merged into one token; text is cut into sentences
      at . ; : ! ? and line breaks; British spellings of dictionary words are mapped to the American ones.
    * (A) topic x direction: for every topic token, the NEAREST direction word within 4 tokens in the same sentence
      (the preceding one wins a tie) gives one hit: up = hawkish, down = dovish; reversed for the slack group; reversed
      again when a negator stands within 3 tokens before the direction word.
    * (B) outright stance terms: one hawkish / dovish hit each; the policy-conditioned ones (tighten..., ease...) count
      only with a policy word within 4 tokens; a dovish noun preceded within 4 tokens by a "removal" word is hawkish
      ("removal of accommodation"); a negator within 3 tokens before the term flips it ("less restrictive").
    * document tone = (H - D) / (H + D); documents with fewer than MIN_HITS = 5 hits carry no tone (non-monetary speeches).
  Institution of a speech: the FIRST central bank named in the BIS description is the speaker's (title precedes venue).
    Fed = "Federal Reserve" (Board and Reserve Banks); ECB = "European Central Bank" / "ECB" / "European Monetary
    Institute", excluding descriptions that name the Supervisory Board without the Executive Board (bank supervisors).
  Aggregation: Fed documents = FOMC statements + FOMC minutes + Fed speeches; ECB documents = ECB speeches (the BIS
    archive carries the ECB press-conference statements as speeches of the President). tone_W(d) = equal-weighted
    mean of the document tones published in the W calendar days up to d, W = 30 (needs >= 2 documents) and 90 (>= 4);
    z_W = (tone_W - expanding mean) / expanding sd of the institution's own daily tone_W history (>= 1,095 days), so
    each bank is measured against its own habitual language; relative tone rel_W = zFed_W - zECB_W.
THE 12 CANDIDATE SIGNALS (positive = long EUR/USD) AND THEIR PRIORS
  1 CENTRAL-BANK TONE - prior: the Fed sounding more hawkish relative to the ECB => EUR/USD down
    1 tone_rel_lvl   -(rel_90)                               level of the relative tone (already a z-score difference)
    2 tone_rel_d1m   -(rel_30(d) - rel_30(d - 30 days))      1-month change (two adjacent 30-day windows)
    3 tone_rel_d3m   -(rel_90(d) - rel_90(d - 90 days))      3-month change (two adjacent 90-day windows)
  2 NEWS SENTIMENT (US economic news; no euro counterpart) - prior: improving US sentiment => USD up => EUR/USD down
    4 news_lvl       -(S - expanding mean of S since 1980)   level against its own history
    5 news_d1m       -(S(d) - S(d - 30 days))                1-month change
    Undefined from 2025-06 (copy ends 2025-05-18).
  3 UNCERTAINTY - the log's "dollar safe haven when stress rises" prior was right 41 % of the time, so:
    6 epu_rel_d3m    -(3-month change of log(Europe EPU / US EPU)), monthly; prior: uncertainty rising in Europe
                      relative to the US => EUR/USD down (relative, not a safe-haven prior).
    7 tpu_d3m        o x (3-month change of log(US trade-policy uncertainty)), monthly; NO prior: the orientation o for
                      test year Y is the sign of the covariance between the raw change and the 21-session forward
                      return over rows whose label is known before Y-01-01 (expanding training window). Undefined
                      before 2010.
    8 gpr_d3m        -(log MA30(GPR)(d) - log MA30(GPR)(d - 90 days)); prior: geopolitical risk rising => EUR/USD down
                      (Europe-centred shocks and safe-haven demand; WEAK prior, flagged as such before results).
  4 POLICY SURPRISES (the owner's rate-cycle idea in its market-surprise form)
    prior: Fed tightening surprises minus ECB ones, cumulated => EUR/USD down
    9 jk_mp_3m       -(sum of Fed MP_median over the last 91 days - sum of ECB MP_median over the last 91 days)
   10 jk_mp_6m       same over 182 days
   11 jk_cbi_3m      same with the information shocks CBI_median, 91 days. WEAK prior (same sign as policy: relative
                      rates up => currency up); the opposite story (good US news => risk-on => dollar down) is as
                      respectable.
   12 jk_cbi_6m      same over 182 days
    Raw percentage points, no rescaling. Undefined 60 days after the last row of either file (ECB file ends 2025-10-30).

EVALUATION (HOWTO_ARMS.md rounds 5 and 7; helpers and conventions of eurusd.arms.selective, as arms Q, R, T used them)
  0 Reconciliation: the agreement rule is rebuilt with selective.house_score_wf and must reproduce arm N's
    56 / 59 / 61 / 72 % non-overlapping (n = 291 / 156 / 89 / 61), 2010-26.
  1 Standalone: direction = sign(signal); accuracy at 21 / 42 / 63 sessions on weekly decisions and on the greedy
    non-overlapping stream (plain Wilson interval), 2010-26 / 2016-26 / 2023-26; decisions per year next to it.
    Other era (round 6): the same standalone rule on 2004-09, which no selection touches.
  2 Extra vote. (a) AND rule: the agreement rule speaks AND sign(signal) equals its direction - against the agreement
    rule alone, with decisions per year; (b) OUTSIDE: direction = sign(signal) on the sessions where the three old
    signals do NOT agree; (c) paired differences on the weekly grid with a circular block bootstrap (block 2h/5 weeks,
    2000 draws): acc(AND) - acc(agreement rule on the sessions where the signal exists), and acc(agreement calls the
    signal confirms) - acc(agreement calls it contradicts).
  3 Daily stream: weekly tranches of the final AND rule held 21 sessions (selective.book_time_exit, 1.2 pips per unit
    turnover); protocol table; meta.combine(["weak_signals","regime_trend","text_news"], "EW") against the two-way
    combination; daily P&L correlations.
  4 Timing placebo: the signal made 63 and 126 sessions staler; AND rule and standalone accuracy re-evaluated.
  5 Round 7 controls: correlation of each signal with cot_z52, d_spread2y_20, the walk-forward house score and the
    trailing 21- and 63-session EUR/USD return (2010-26); accuracy after ORTHOGONALISING: for test year Y an OLS of the
    signal on the controls is fitted on rows dated before Y-01-01 and the fitted part b'(x - mean_train(x)) is
    removed (the signal keeps its own zero point). Two sets: "price" (ret_21d, ret_63d) and "all" (price + cot_z52 +
    d_spread2y_20 + house score; the house score enters from 2013, when three walk-forward years of it exist).
    Standalone and AND-rule accuracy of sign(residual) are reported next to the raw ones.
  SELECTION RULE (the one arms Q, R, T used): final = the candidate whose AND rule has the highest LOWER Wilson bound of
    the 2010-2015 non-overlapping 21-session accuracy among candidates with at least 6 non-overlapping 21-session
    decisions a year in 2010-2015. If no candidate has 6 a year there is NO final rule; the stream written to disk is
    then the highest lower bound among all candidates, flagged as failing the decisions requirement.
  SUCCESS BAR (round 5): the AND rule beats the agreement rule by >= 3 accuracy points at 21 AND 42 sessions on
    non-overlapping decisions in BOTH 2010-26 and 2016-26 with at least 6 decisions a year, is not worse in 2023-26, and
    the placebo loses at least half of the gain. Known in advance (arm R): the agreement rule itself makes 9.3 (21
    sessions) and 5.3 (42 sessions) non-overlapping decisions a year, so no AND rule can have 6 a year at 42 sessions;
    the count is judged on the 21-session stream and the 42-session count is printed next to every number.
  Leak checks: (1) labels permuted (300 draws) -> rules at chance; (2) the signal shifted FORWARD in time (-21 sessions,
    look-ahead) and +1 / +5 / +21 staler; a truncation test (raw data cut at five dates as a user would have held them,
    the row of that date must be unchanged); the tone signals re-dated by the BIS POSTING date (stricter dating);
    (3) what each signal is correlated with, including the forward label.
Variant count for deflation: 12 candidate signals = 12 AND rules. Nothing else is selected from. The orthogonalised,
  shifted and re-dated versions are controls of those 12, not candidates.

CHANGED AFTER THE DOCSTRING WAS WRITTEN (data handling only; dictionary, signals, signs and rules untouched):
  * scorer: one-token sentences were skipped (found with hand-written test sentences, before any document was scored);
  * live BIS pages that carry only an abstract: the speech text is read from the page's PDF (pdftotext);
  * a speech present in both the bulk file and the live listing is kept once (same institution and title within 45 days).
  The last two were found by reading the document table, the duplicates after a first full run; the non-overlapping
  results were unchanged by that fix (it touches eight speeches of April-June 2026).
"""
from __future__ import annotations

import csv
import html
import io
import math
import re
import subprocess
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.arms import selective as SL  # noqa: E402
from eurusd.featstore import _align_lagged  # noqa: E402
from eurusd.wf import report  # noqa: E402

MACRO = ROOT / "data" / "macro"
RAW = ROOT / "data" / "raw" / "text_news"
RES = ROOT / "experiments" / "results" / "arms"
ARM = "text_news"
N_ARMS = 12
HORIZONS = (21, 42, 63)
SEL_H = 21
MIN_DEC_PER_YEAR = 6.0
PLACEBO_SHIFTS = (63, 126)
STALE_M, STALE_D = 75, 10
LAG = {"text": 1, "jk": 1, "news": 7, "gpr": 7, "epu": 30, "epu_cat": 45}
JK_STALE = 60
MIN_HITS = 5
MIN_DOCS = {30: 2, 90: 4}
Z_MIN_DAYS = 1095

URLS = {
    "fomc": "https://raw.githubusercontent.com/vtasca/fed-statement-scraping/master/communications.csv",
    "ecb_copy": "https://media.githubusercontent.com/media/Moritz-Pfeifer/CentralBankRoBERTa/main/Data/ECB/all_ECB_speeches.csv",
    "bis": "https://www.bis.org/pages/download-central-bankers-speeches/speeches-{y}.zip",
    "bis_list": "https://www.bis.org/speeches/central-bank",
    "sffed": "https://raw.githubusercontent.com/wattyven/VIX-study/main/sentiment/news_sentiment_data.csv",
    "gpr": "https://raw.githubusercontent.com/iacoviel/iacoviel.github.io/master/gpr_files/data_gpr_daily_recent.xls",
    "jk_fed": "https://raw.githubusercontent.com/marekjarocinski/jkshocks_update_fed/main/shocks_fed_jk_t.csv",
    "jk_ecb": "https://raw.githubusercontent.com/marekjarocinski/jkshocks_update_ecb/main/shocks_ecb_mpd_me_d.csv",
    "fred": "https://fred.stlouisfed.org/graph/fredgraph.csv?id={sid}",
}
FRED_IDS = ("USEPUINDXD", "EUEPUINDXM", "EPUTRADE", "EPUMONETARY")
BIS_YEARS = tuple(range(1996, 2027))
BIS_ORGS = ("European Central Bank", "Board of Governors of the Federal Reserve System", "Federal Reserve Bank of Atlanta",
            "Federal Reserve Bank of Boston", "Federal Reserve Bank of Chicago", "Federal Reserve Bank of Cleveland",
            "Federal Reserve Bank of Dallas", "Federal Reserve Bank of Kansas City", "Federal Reserve Bank of Minneapolis",
            "Federal Reserve Bank of New York", "Federal Reserve Bank of Philadelphia", "Federal Reserve Bank of Richmond",
            "Federal Reserve Bank of San Francisco", "Federal Reserve Bank of St Louis")

# ================================================================ THE DICTIONARY (frozen before any result)
TONE_DICT = {
    # multi-word expressions -> one token (regex on lower-cased text, \s+ between words)
    "phrases": (
        (r"rate\s+(?:increase|hike|rise)s?", "rate_hike"),
        (r"rate\s+(?:cut|reduction|decrease)s?", "rate_cut"),
        (r"(?:key\s+)?(?:ecb\s+)?interest\s+rates?", "interest_rate"),
        (r"policy\s+rates?", "policy_rate"),
        (r"(?:federal\s+)?funds\s+rate", "funds_rate"),
        (r"target\s+range", "target_range"),
        (r"deposit\s+(?:facility\s+)?rate", "deposit_rate"),
        (r"(?:main\s+)?refinancing\s+rate", "refi_rate"),
        (r"(?:inflationary|inflation|price|cost|wage)\s+pressures?", "price_pressures"),
        (r"(?:consumer|energy|oil|commodity|import|food|core)\s+prices?", "goods_prices"),
        (r"(?:unit\s+)?labou?r\s+costs?", "labor_costs"),
        (r"labou?r\s+markets?", "labor_market"),
        (r"(?:resource|capacity)\s+utili[sz]ation", "resource_utilization"),
        (r"spare\s+capacity", "spare_capacity"),
        (r"second[\s-]+round\s+effects?", "second_round_effects"),
        (r"wage[\s-]+price\s+spirals?", "wage_price_spiral"),
        (r"quantitative\s+easing", "quantitative_easing"),
        (r"(?:asset\s+)?purchase\s+program(?:me)?s?", "asset_purchases"),
        (r"asset\s+purchases?", "asset_purchases"),
        (r"(?:zero|effective)\s+lower\s+bound", "lower_bound"),
    ),
    # (A) topic nouns: +1 = "up is hawkish", -1 = "up is dovish" (slack group)
    "topics_up_hawkish": ("inflation", "price_pressures", "goods_prices", "wages", "labor_costs",                    # prices
                          "growth", "activity", "demand", "economy", "output", "expansion", "recovery", "employment",  # activity
                          "spending", "consumption", "investment", "labor_market", "production", "hiring", "resource_utilization",
                          "interest_rate", "policy_rate", "funds_rate", "target_range", "deposit_rate", "refi_rate"),  # policy rates
    "topics_up_dovish": ("unemployment", "joblessness", "spare_capacity"),
    "up": ("high", "higher", "rise", "rises", "rising", "rose", "risen", "increase", "increases", "increased", "increasing",
           "raise", "raises", "raised", "raising", "hike", "hikes", "hiked", "hiking", "lift", "lifted", "lifting",
           "strong", "stronger", "strengthen", "strengthens", "strengthened", "strengthening", "robust", "solid", "elevated",
           "accelerate", "accelerates", "accelerated", "accelerating", "acceleration", "upward", "upside", "pickup", "faster",
           "rapid", "rapidly", "buoyant", "surge", "surged", "surging", "firm", "firmer", "firming", "tight", "tighter",
           "tightening", "tightened", "heightened", "mounting", "boom", "booming", "above"),
    "down": ("low", "lower", "fall", "falls", "falling", "fell", "fallen", "decline", "declines", "declined", "declining",
             "decrease", "decreases", "decreased", "decreasing", "cut", "cuts", "cutting", "reduce", "reduces", "reduced",
             "reducing", "reduction", "reductions", "weak", "weaker", "weaken", "weakens", "weakened", "weakening", "weakness",
             "subdued", "sluggish", "slow", "slower", "slowed", "slowing", "slowdown", "moderated", "moderating", "moderation",
             "soft", "softer", "soften", "softened", "softening", "muted", "downward", "downside", "decelerate", "decelerated",
             "decelerating", "deceleration", "contract", "contracted", "contracting", "contraction", "depressed", "anemic",
             "below", "dampen", "dampened", "dampening", "ease", "eased", "easing"),
    # (B) outright stance terms
    "hawkish": ("overheating", "overheat", "overheated", "vigilance", "vigilant", "restrictive", "restrictiveness", "rate_hike",
                "second_round_effects", "wage_price_spiral", "normalization", "normalize", "normalizing", "taper", "tapering",
                "hawkish"),
    "dovish": ("accommodative", "accommodation", "stimulus", "stimulative", "stimulate", "stimulating", "slack", "rate_cut",
               "patient", "patience", "disinflation", "disinflationary", "deflation", "deflationary", "recession",
               "recessionary", "downturn", "headwinds", "asset_purchases", "quantitative_easing", "lower_bound", "dovish"),
    "hawkish_if_policy": ("tighten", "tightens", "tightened", "tightening", "tighter", "firming"),
    "dovish_if_policy": ("ease", "eases", "eased", "easing", "loosen", "loosening", "looser", "loose"),
    "policy_words": ("policy", "monetary", "stance", "cycle"),
    "reversible_dovish": ("accommodative", "accommodation", "stimulus", "slack", "asset_purchases", "quantitative_easing"),
    "reversers": ("remove", "removes", "removed", "removing", "removal", "withdraw", "withdraws", "withdrawing", "withdrawal",
                  "withdrawn", "reduce", "reduces", "reduced", "reducing", "reduction", "diminish", "diminished", "diminishing",
                  "absorb", "absorbed", "unwind", "unwinding", "end", "ended", "ending", "taper", "tapering", "exit"),
    "negators": ("not", "no", "never", "nor", "neither", "without", "hardly", "less"),   # and any token ending in n't
    "british": {"labour": "labor", "normalisation": "normalization", "normalise": "normalize", "normalising": "normalizing",
                "anaemic": "anemic", "programme": "program"},
    "window_topic": 4, "window_negation": 3, "window_policy": 4, "window_reverser": 4,
}

_PHRASE_RE = re.compile("|".join(f"(?P<p{i}>\\b{p}\\b)" for i, (p, _) in enumerate(TONE_DICT["phrases"])))
_PHRASE_TOK = {f"p{i}": t for i, (_, t) in enumerate(TONE_DICT["phrases"])}
_SENT_RE = re.compile(r"[.;:!?\n\r]+")
_TOK_RE = re.compile(r"[a-z_]+(?:'t)?")
_TOPIC = {**{w: 1 for w in TONE_DICT["topics_up_hawkish"]}, **{w: -1 for w in TONE_DICT["topics_up_dovish"]}}
_MOD = {**{w: 1 for w in TONE_DICT["up"]}, **{w: -1 for w in TONE_DICT["down"]}}
_BH, _BD = frozenset(TONE_DICT["hawkish"]), frozenset(TONE_DICT["dovish"])
_BHP, _BDP = frozenset(TONE_DICT["hawkish_if_policy"]), frozenset(TONE_DICT["dovish_if_policy"])
_POL, _REVB, _REV = frozenset(TONE_DICT["policy_words"]), frozenset(TONE_DICT["reversible_dovish"]), frozenset(TONE_DICT["reversers"])
_NEG = frozenset(TONE_DICT["negators"])
_BRIT = TONE_DICT["british"]
_ANY = frozenset(_TOPIC) | _BH | _BD | _BHP | _BDP


def _negated(toks: list, j: int) -> bool:
    for w in toks[max(0, j - TONE_DICT["window_negation"]):j]:
        if w in _NEG or w.endswith("n't"):
            return True
    return False


def score_text(text: str) -> tuple[int, int, int]:
    """(hawkish hits, dovish hits, tokens) of one document under TONE_DICT."""
    if not isinstance(text, str) or not text:
        return 0, 0, 0
    t = text.lower().replace("’", "'")
    t = _PHRASE_RE.sub(lambda m: " " + _PHRASE_TOK[m.lastgroup] + " ", t)
    H = D = n_tok = 0
    wt, wp, wr = TONE_DICT["window_topic"], TONE_DICT["window_policy"], TONE_DICT["window_reverser"]
    for sent in _SENT_RE.split(t):
        toks = [_BRIT.get(w, w) for w in _TOK_RE.findall(sent)]
        n = len(toks)
        n_tok += n
        if n < 1:
            continue
        for i, w in enumerate(toks):
            if w not in _ANY:
                continue
            pol = 0
            tp = _TOPIC.get(w)
            if tp is not None:                                   # (A) nearest direction word within the window
                for d in range(1, wt + 1):
                    j = i - d
                    if j >= 0 and toks[j] in _MOD:
                        pol = _MOD[toks[j]] * tp * (-1 if _negated(toks, j) else 1)
                        break
                    j = i + d
                    if j < n and toks[j] in _MOD:
                        pol = _MOD[toks[j]] * tp * (-1 if _negated(toks, j) else 1)
                        break
            elif w in _BH:
                pol = -1 if _negated(toks, i) else 1
            elif w in _BD:
                if w in _REVB and any(x in _REV for x in toks[max(0, i - wr):i]):
                    pol = 1
                else:
                    pol = 1 if _negated(toks, i) else -1
            if pol == 0 and (w in _BHP or w in _BDP):            # policy-conditioned stance verbs
                lo, hi = max(0, i - wp), min(n, i + wp + 1)
                if any(toks[k] in _POL for k in range(lo, hi) if k != i):
                    pol = 1 if w in _BHP else -1
                    if _negated(toks, i):
                        pol = -pol
            if pol > 0:
                H += 1
            elif pol < 0:
                D += 1
    return H, D, n_tok


# ================================================================ cached fetch
def _curl(url: str, dest: Path, tries: int = 25, is_zip: bool = False, params: dict | None = None) -> None:
    """Resumable download (www.bis.org cuts long transfers); a zip must pass its CRC test."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    part = dest.with_suffix(dest.suffix + ".part")
    err = ""
    for k in range(tries):
        cmd = ["curl", "--http1.1", "-sS", "-L", "-m", "600", "-o", str(part), "-w", "%{http_code}"]
        if part.exists() and params is None:
            cmd += ["-C", "-"]
        if params:
            cmd += ["-G"]
            for a, b in params.items():
                cmd += ["--data-urlencode", f"{a}={b}"]
        r = subprocess.run(cmd + [url], capture_output=True, text=True)
        code = r.stdout.strip()[-3:]
        ok = r.returncode == 0 and code in ("200", "206") and part.exists() and part.stat().st_size > 50
        if ok and is_zip:
            try:
                ok = zipfile.ZipFile(part).testzip() is None
            except zipfile.BadZipFile:
                ok = False
        if ok:
            part.replace(dest)
            return
        if code in ("403", "404", "407", "416"):
            part.unlink(missing_ok=True)
            if code != "416":
                raise RuntimeError(f"fetch refused: {url}: http {code}")
        err = f"http {code} rc {r.returncode} {r.stderr.strip()[:160]}"
        time.sleep(min(2 * (k + 1), 15))
    raise RuntimeError(f"fetch failed: {url}: {err}")


def _strip_html(t: str) -> str:
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<svg.*?</svg>", " ", t, flags=re.S)
    return re.sub(r"[ \t\r\f\v]+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


_MONTHS = {m: i + 1 for i, m in enumerate(("january", "february", "march", "april", "may", "june", "july", "august", "september",
                                           "october", "november", "december"))}


def _last_date(desc: str):
    m = re.findall(r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})", desc)
    if not m:
        return pd.NaT
    d, mo, y = m[-1]
    try:
        return pd.Timestamp(int(y), _MONTHS[mo.lower()], int(d))
    except ValueError:
        return pd.NaT


def fetch_bis_live(since: str, refresh: bool = False, verbose: bool = True) -> pd.DataFrame:
    """Fed and ECB speeches posted on www.bis.org after the bulk build (listing filtered by organisation)."""
    out = RAW / "bis_live" / "speeches_live.csv"
    if out.exists() and not refresh:
        return pd.read_csv(out)
    rows = []
    for org in BIS_ORGS:
        page = 0
        while True:
            dest = RAW / "bis_live" / "lists" / f"{re.sub('[^a-z]+', '_', org.lower())}_{page}.htm"
            try:
                _curl(URLS["bis_list"], dest, tries=6, params={"organisation[]": org, "start_date": since, "page": page})
            except RuntimeError as e:
                if verbose:
                    print(f"  BIS live listing failed for {org} page {page}: {e}", flush=True)
                break
            t = dest.read_text(encoding="utf-8", errors="replace")
            cards = re.findall(r'<a href="(/speeches/[^"]+)" class="card-link">.*?card-date fs-sm">([^<]*)</span>.*?card-heading">(.*?)</h5>.*?'
                               r'card-description">(.*?)</div>', t, flags=re.S)
            for href, pdate, title, desc in cards:
                rows.append({"url": "https://www.bis.org" + href, "post_date": pd.to_datetime(pdate.strip(), format="%d %b %Y"),
                             "title": html.unescape(re.sub(r"<[^>]+>", "", title)).strip(), "description": html.unescape(re.sub(r"<[^>]+>", "", desc)).strip()})
            m = re.search(r"Displaying\s+\d+-(\d+)\s+of\s+(\d+)", t)
            if not cards or not m or int(m.group(1)) >= int(m.group(2)):
                break
            page += 1
            time.sleep(0.3)
    L = pd.DataFrame(rows).drop_duplicates("url") if rows else pd.DataFrame(columns=["url", "post_date", "title", "description"])
    texts = []
    for u in L["url"]:
        dest = RAW / "bis_live" / "pages" / (u.rsplit("/", 1)[1] + ".htm")
        try:
            if not dest.exists():
                _curl(u, dest, tries=6)
                time.sleep(0.3)
            t = dest.read_text(encoding="utf-8", errors="replace")
            i = t.find("block--system-main")
            j = t.find("The views expressed in this speech")
            txt = _strip_html(t[max(i, 0): j if j > 0 else len(t)])
            if len(txt) < 5000 and (u + ".pdf") in t:           # the page carries an abstract only: the speech is the PDF
                pdf = dest.with_suffix(".pdf")
                if not pdf.exists():
                    _curl(u + ".pdf", pdf, tries=8)
                    time.sleep(0.3)
                r = subprocess.run(["pdftotext", "-q", str(pdf), "-"], capture_output=True, text=True)
                if r.returncode == 0 and len(r.stdout) > len(txt):
                    txt = r.stdout
            texts.append(txt)
        except RuntimeError:
            texts.append("")
    L["text"] = texts
    L["date"] = [(_last_date(d) if pd.notna(_last_date(d)) else p) for d, p in zip(L["description"], L["post_date"])]
    L["date"] = np.minimum(pd.to_datetime(L["date"]), pd.to_datetime(L["post_date"]))
    L.to_csv(out, index=False)
    return L


_CB_RE = re.compile(r"Fed(?:eral|\.)\s+Res(?:erve|\.)|European Central Bank|\bECB\b|European Monetary Institute|Bank of [A-Z]|Bundesbank|Banque de France|"
                    r"Banca d'Italia|Bank for International Settlements|\bBIS\b|Reserve Bank|Riksbank|Riskbank|Norges Bank|National Bank|Nationalbank|"
                    r"Central Bank|central bank of|Monetary Authority|Bangko Sentral|Banco |Nederlandsche Bank|Netherlands Bank|Nemzeti Bank|Bank Negara|"
                    r"Bank Indonesia|People's Bank|Bank Al-Maghrib|Banque |Monetary Agency|Bank of the|Narodowy|Banka|Sedlabanki|Eesti Pank|"
                    r"Latvijas|Lietuvos|Suomen Pankki|Bank Markazi|Financial Services Authority|Financial Supervisory|BANK OF JAPAN")


def institution(desc: str) -> str:
    """The first central bank named in the BIS description is the speaker's."""
    d = re.sub(r"\s+", " ", desc or "")
    m = _CB_RE.search(d)
    if not m:
        return "none"
    g = m.group(0)
    if g.startswith("Fed"):
        return "FED"
    if g in ("European Central Bank", "ECB", "European Monetary Institute"):
        return "other" if ("Supervisory Board" in d and "Executive Board" not in d) else "ECB"
    return "other"


def _norm_title(t: str) -> str:
    t = re.sub(r"^[^:]{3,60}:\s*", "", str(t))
    return re.sub(r"[^a-z0-9]+", "", t.lower())[:60]


def build_docs(refresh: bool = False, verbose: bool = True) -> pd.DataFrame:
    """Per-document tone scores (no text) for every Fed / ECB document: data/macro/text_news_docs.csv."""
    out = MACRO / f"{ARM}_docs.csv"
    if out.exists() and not refresh:
        return pd.read_csv(out, parse_dates=["date", "post_date"])
    csv.field_size_limit(10 ** 9)
    rows = []
    # ---- FOMC statements and minutes
    f = pd.read_csv(RAW / "fomc" / "communications.csv")
    f = f[f["Type"].isin(["Statement", "Minute"]) & f["Text"].notna()]
    for _, r in f.iterrows():
        h, d, n = score_text(r["Text"])
        rows.append({"inst": "FED", "kind": "fomc_statement" if r["Type"] == "Statement" else "fomc_minutes", "source": "fomc_csv",
                     "date": pd.Timestamp(r["Release Date"]), "post_date": pd.Timestamp(r["Release Date"]), "title": f"FOMC {r['Type']} of {r['Date']}",
                     "n_tokens": n, "hawk": h, "dove": d})
    if verbose:
        print(f"  scored {len(rows)} FOMC documents", flush=True)
    # ---- BIS bulk archive
    seen: dict = {}                                    # (institution, normalised title) -> dates already held
    n_all, bulk_last = 0, pd.Timestamp("1990-01-01")
    for y in BIS_YEARS:
        z = zipfile.ZipFile(RAW / "bis" / f"speeches-{y}.zip")
        b = pd.read_csv(z.open(z.namelist()[0]))
        n_all += len(b)
        b = b.drop_duplicates("url")
        b["inst"] = b["description"].fillna("").map(institution)
        date = (pd.to_datetime(b["date"]) + pd.Timedelta(hours=3)).dt.normalize()      # 22:00 / 23:00 stamps are CET midnights
        post = pd.to_datetime(b["url"].str.extract(r"/r(\d{6})")[0], format="%y%m%d", errors="coerce")
        post = post.fillna(date)
        date = date.where((post - date).dt.days >= -3, post)                            # a date after the posting date is a data error
        bulk_last = max(bulk_last, date.max())
        b["date"], b["post_date"] = date, post
        for _, r in b[b["inst"].isin(["FED", "ECB"])].iterrows():
            h, d, n = score_text(r["text"])
            seen.setdefault((r["inst"], _norm_title(r["title"])), []).append(r["date"])
            rows.append({"inst": r["inst"], "kind": "speech", "source": "bis_bulk", "date": r["date"], "post_date": r["post_date"],
                         "title": str(r["title"])[:120], "n_tokens": n, "hawk": h, "dove": d})
    if verbose:
        print(f"  BIS bulk: {n_all} speeches of all central banks, last speech date {bulk_last.date()}; {len(rows)} documents so far", flush=True)
    # ---- BIS live listing after the bulk build
    try:
        L = fetch_bis_live(str((bulk_last - pd.Timedelta(days=60)).date()), refresh=False, verbose=verbose)
    except Exception as e:  # noqa: BLE001  (live continuation is optional)
        print(f"  BIS live continuation unavailable: {e}", flush=True)
        L = pd.DataFrame()
    n_live = 0
    for _, r in L.iterrows():
        inst = institution(str(r["description"]))
        key = (inst, _norm_title(r["title"]))
        dup = any(abs((pd.Timestamp(r["date"]) - d0).days) <= 45 for d0 in seen.get(key, []))   # same title within 45 days = the bulk copy
        if inst not in ("FED", "ECB") or dup or not isinstance(r["text"], str) or len(r["text"]) < 500:
            continue
        seen.setdefault(key, []).append(pd.Timestamp(r["date"]))
        h, d, n = score_text(r["text"])
        rows.append({"inst": inst, "kind": "speech", "source": "bis_live", "date": pd.Timestamp(r["date"]), "post_date": pd.Timestamp(r["post_date"]),
                     "title": str(r["title"])[:120], "n_tokens": n, "hawk": h, "dove": d})
        n_live += 1
    if verbose:
        print(f"  BIS live listing: {n_live} further Fed / ECB speeches", flush=True)
    # ---- ECB copy (cross-check only)
    e = pd.read_csv(RAW / "ecb_copy" / "all_ECB_speeches.csv", sep="|", engine="python", quoting=csv.QUOTE_NONE, on_bad_lines="skip")
    e = e[e["contents"].notna()]
    for _, r in e.iterrows():
        h, d, n = score_text(r["contents"])
        dt = pd.to_datetime(r["date"], errors="coerce")
        if pd.isna(dt):
            continue
        rows.append({"inst": "ECB_COPY", "kind": "speech", "source": "ecb_copy", "date": dt, "post_date": dt, "title": str(r["title"])[:120],
                     "n_tokens": n, "hawk": h, "dove": d})
    X = pd.DataFrame(rows)
    X["hits"] = X["hawk"] + X["dove"]
    X["tone"] = np.where(X["hits"] >= MIN_HITS, (X["hawk"] - X["dove"]) / X["hits"].clip(lower=1), np.nan)
    X = X.sort_values(["date", "inst", "kind"]).reset_index(drop=True)
    X.to_csv(out, index=False)
    return X


def fetch_all(refresh: bool = False, verbose: bool = True) -> pd.DataFrame:
    """Downloads every raw file once (data/raw/text_news/, resumable), scores the texts and writes the cleaned series
    data/macro/text_news_*.csv. Returns the source catalogue (also written to data/macro/text_news_sources.csv)."""
    jobs = [(URLS["fomc"], RAW / "fomc" / "communications.csv", False), (URLS["ecb_copy"], RAW / "ecb_copy" / "all_ECB_speeches.csv", False),
            (URLS["sffed"], RAW / "sffed" / "news_sentiment_data.csv", False), (URLS["gpr"], RAW / "gpr" / "data_gpr_daily_recent.xls", False),
            (URLS["jk_fed"], RAW / "jk" / "shocks_fed_jk_t.csv", False), (URLS["jk_ecb"], RAW / "jk" / "shocks_ecb_mpd_me_d.csv", False)]
    jobs += [(URLS["fred"].format(sid=s), RAW / "fred" / f"{s}.csv", False) for s in FRED_IDS]
    jobs += [(URLS["bis"].format(y=y), RAW / "bis" / f"speeches-{y}.zip", True) for y in BIS_YEARS]
    for url, dest, is_zip in jobs:
        if refresh or not dest.exists():
            _curl(url, dest, is_zip=is_zip)
            time.sleep(0.5)
    fetched = lambda p: time.strftime("%Y-%m-%d", time.gmtime(p.stat().st_mtime))
    cat = []
    # ---- texts
    docs = build_docs(refresh=refresh, verbose=verbose)
    for inst, kind, src, url, lag in (("FED", "fomc_statement", "fomc_csv", URLS["fomc"], "release date + 1 d"),
                                      ("FED", "fomc_minutes", "fomc_csv", URLS["fomc"], "release date + 1 d"),
                                      ("FED", "speech", "bis_bulk", URLS["bis"], "speech date + 1 d"), ("ECB", "speech", "bis_bulk", URLS["bis"], "speech date + 1 d"),
                                      ("FED", "speech", "bis_live", URLS["bis_list"], "speech date + 1 d"), ("ECB", "speech", "bis_live", URLS["bis_list"], "speech date + 1 d"),
                                      ("ECB_COPY", "speech", "ecb_copy", URLS["ecb_copy"], "cross-check only")):
        d = docs[(docs.inst == inst) & (docs.kind == kind) & (docs.source == src)]
        if len(d):
            raw = {"fomc_csv": RAW / "fomc" / "communications.csv", "bis_bulk": RAW / "bis" / "speeches-2026.zip", "bis_live": RAW / "bis_live" / "speeches_live.csv",
                   "ecb_copy": RAW / "ecb_copy" / "all_ECB_speeches.csv"}[src]
            cat.append({"file": f"data/macro/{ARM}_docs.csv", "series": f"{inst} {kind} ({src})", "url": url, "fetched": fetched(raw), "rows": len(d),
                        "first": str(d.date.min().date()), "last": str(d.date.max().date()), "lag used": lag})
    # ---- SF Fed news sentiment
    s = pd.read_csv(RAW / "sffed" / "news_sentiment_data.csv")
    s.columns = ["date", "sentiment"]
    s.to_csv(MACRO / f"{ARM}_sentiment_daily.csv", index=False)
    cat.append({"file": f"data/macro/{ARM}_sentiment_daily.csv", "series": "SF Fed Daily News Sentiment (third-party copy, one vintage)", "url": URLS["sffed"],
                "fetched": fetched(RAW / "sffed" / "news_sentiment_data.csv"), "rows": len(s), "first": s.date.iloc[0], "last": s.date.iloc[-1], "lag used": "7 d"})
    # ---- EPU
    fr = {}
    for sid in FRED_IDS:
        d = pd.read_csv(RAW / "fred" / f"{sid}.csv")
        d.columns = ["date", "value"]
        d["value"] = pd.to_numeric(d["value"], errors="coerce")
        fr[sid] = d.dropna()
        cat.append({"file": f"data/macro/{ARM}_epu_{'us_daily' if sid == 'USEPUINDXD' else 'monthly'}.csv", "series": f"FRED {sid}", "url": URLS["fred"].format(sid=sid),
                    "fetched": fetched(RAW / "fred" / f"{sid}.csv"), "rows": len(d), "first": d.date.iloc[0], "last": d.date.iloc[-1],
                    "lag used": {"USEPUINDXD": "monthly mean, month-end + 30 d", "EUEPUINDXM": "month-end + 30 d", "EPUTRADE": "month-end + 45 d",
                                 "EPUMONETARY": "not used as a candidate"}[sid]})
    fr["USEPUINDXD"].to_csv(MACRO / f"{ARM}_epu_us_daily.csv", index=False)
    m = pd.DataFrame({k: v.assign(month=lambda x: x.date.str[:7]).set_index("month")["value"] for k, v in fr.items() if k != "USEPUINDXD"})
    m.index.name = "month"
    m.to_csv(MACRO / f"{ARM}_epu_monthly.csv")
    # ---- GPR
    g = pd.read_excel(RAW / "gpr" / "data_gpr_daily_recent.xls")[["date", "GPRD", "GPRD_ACT", "GPRD_THREAT"]].dropna(subset=["GPRD"])
    g["date"] = pd.to_datetime(g["date"]).dt.strftime("%Y-%m-%d")
    g.to_csv(MACRO / f"{ARM}_gpr_daily.csv", index=False)
    cat.append({"file": f"data/macro/{ARM}_gpr_daily.csv", "series": "Geopolitical Risk index, daily (Caldara-Iacoviello)", "url": URLS["gpr"],
                "fetched": fetched(RAW / "gpr" / "data_gpr_daily_recent.xls"), "rows": len(g), "first": g.date.iloc[0], "last": g.date.iloc[-1], "lag used": "7 d"})
    # ---- JK shocks
    a = pd.read_csv(RAW / "jk" / "shocks_fed_jk_t.csv")
    a["date"] = pd.to_datetime(a["start"]).dt.strftime("%Y-%m-%d")
    b = pd.read_csv(RAW / "jk" / "shocks_ecb_mpd_me_d.csv")
    b["date"] = pd.to_datetime(b["date"]).dt.strftime("%Y-%m-%d")
    j = pd.concat([a.assign(bank="FED")[["bank", "date", "pc1", "MP_median", "CBI_median", "MP_pm", "CBI_pm"]],
                   b.assign(bank="ECB")[["bank", "date", "pc1", "MP_median", "CBI_median", "MP_pm", "CBI_pm"]]], ignore_index=True)
    j.to_csv(MACRO / f"{ARM}_jk_shocks.csv", index=False)
    for bank, key in (("FED", "jk_fed"), ("ECB", "jk_ecb")):
        d = j[j.bank == bank]
        cat.append({"file": f"data/macro/{ARM}_jk_shocks.csv", "series": f"Jarocinski-Karadi shocks, {bank}", "url": URLS[key],
                    "fetched": fetched(RAW / "jk" / ("shocks_fed_jk_t.csv" if bank == "FED" else "shocks_ecb_mpd_me_d.csv")), "rows": len(d),
                    "first": d.date.iloc[0], "last": d.date.iloc[-1], "lag used": "announcement date + 1 d"})
    cat = pd.DataFrame(cat)
    cat.to_csv(MACRO / f"{ARM}_sources.csv", index=False)
    if verbose:
        print(cat.drop(columns=["url"]).to_string(index=False), flush=True)
    return cat


# ================================================================ raw series -> signals
SIGNALS = (  # name, family, prior
    ("tone_rel_lvl", "1 tone", "- Fed tone above its own norm relative to the ECB (90-day windows) = dollar up"),
    ("tone_rel_d1m", "1 tone", "- relative tone (30-day windows) rising over a month = dollar up"),
    ("tone_rel_d3m", "1 tone", "- relative tone (90-day windows) rising over three months = dollar up"),
    ("news_lvl", "2 news", "- US news sentiment above its own history = dollar up (copy ends 2025-05)"),
    ("news_d1m", "2 news", "- US news sentiment improving over a month = dollar up (copy ends 2025-05)"),
    ("epu_rel_d3m", "3 uncertainty", "- Europe-minus-US policy uncertainty rising over three months = euro down"),
    ("tpu_d3m", "3 uncertainty", "sign from the training window: 3-month change of US trade-policy uncertainty"),
    ("gpr_d3m", "3 uncertainty", "- geopolitical risk rising over three months = euro down (weak prior)"),
    ("jk_mp_3m", "4 surprises", "- Fed-minus-ECB pure policy surprises cumulated over 3 months = dollar up"),
    ("jk_mp_6m", "4 surprises", "- same over 6 months"),
    ("jk_cbi_3m", "4 surprises", "- Fed-minus-ECB information surprises over 3 months = dollar up (weak prior)"),
    ("jk_cbi_6m", "4 surprises", "- same over 6 months"),
)
NAMES = [s[0] for s in SIGNALS]
TONE_NAMES = NAMES[:3]
CTRL_PRICE = ("ret_21d", "ret_63d")
CTRL_ALL = ("ret_21d", "ret_63d", "cot_z52", "d_spread2y_20", "house")
CAL0 = "1997-01-01"


def load_raw() -> dict:
    R = {"docs": pd.read_csv(MACRO / f"{ARM}_docs.csv", parse_dates=["date", "post_date"])}
    s = pd.read_csv(MACRO / f"{ARM}_sentiment_daily.csv", parse_dates=["date"]).set_index("date")["sentiment"].astype(float)
    R["news"] = s[~s.index.duplicated()].sort_index()
    u = pd.read_csv(MACRO / f"{ARM}_epu_us_daily.csv", parse_dates=["date"]).set_index("date")["value"].astype(float)
    R["epu_us_d"] = u.sort_index()
    m = pd.read_csv(MACRO / f"{ARM}_epu_monthly.csv")
    m.index = pd.PeriodIndex(m.pop("month"), freq="M")
    R["epu_m"] = m.sort_index()
    g = pd.read_csv(MACRO / f"{ARM}_gpr_daily.csv", parse_dates=["date"]).set_index("date")["GPRD"].astype(float)
    R["gpr"] = g.sort_index()
    R["jk"] = pd.read_csv(MACRO / f"{ARM}_jk_shocks.csv", parse_dates=["date"])
    return R


def truncate_raw(R: dict, asof: pd.Timestamp, date_col: str = "date") -> dict:
    """The raw data as a user would have held it on calendar date `asof` under the declared lags. Leak check only."""
    d1 = pd.Timedelta(days=1)
    out = {"docs": R["docs"][R["docs"][date_col] + d1 * LAG["text"] <= asof],
           "news": R["news"][R["news"].index + d1 * LAG["news"] <= asof],
           "gpr": R["gpr"][R["gpr"].index + d1 * LAG["gpr"] <= asof],
           "epu_us_d": R["epu_us_d"][R["epu_us_d"].index + d1 <= asof],
           "jk": R["jk"][R["jk"]["date"] + d1 * LAG["jk"] <= asof]}
    m = R["epu_m"].copy()
    me = m.index.to_timestamp(how="end").normalize()
    for c in m.columns:
        lag = LAG["epu"] if c == "EUEPUINDXM" else LAG["epu_cat"]
        m.loc[np.asarray(me + d1 * lag > asof), c] = np.nan
    out["epu_m"] = m
    return out


def tone_panel(docs: pd.DataFrame, end, date_col: str = "date") -> pd.DataFrame:
    """Calendar-daily Fed, ECB and relative tone. Row d uses documents dated <= d (usable from the next session)."""
    days = pd.date_range(CAL0, pd.Timestamp(end).normalize(), freq="D")
    P = pd.DataFrame(index=days)
    P.index.name = "date"
    for inst, key in (("FED", "fed"), ("ECB", "ecb")):
        d = docs[(docs["inst"] == inst) & docs["tone"].notna()]
        g = d.groupby(d[date_col].dt.normalize())["tone"]
        sm = g.sum().reindex(days, fill_value=0.0)
        ct = g.size().reindex(days, fill_value=0).astype(float)
        for W in (30, 90):
            n = ct.rolling(W, min_periods=1).sum()
            tone = (sm.rolling(W, min_periods=1).sum() / n.where(n > 0)).where(n >= MIN_DOCS[W])
            P[f"{key}_tone_{W}"], P[f"{key}_n_{W}"] = tone, n
            P[f"{key}_z_{W}"] = (tone - tone.expanding(min_periods=Z_MIN_DAYS).mean()) / tone.expanding(min_periods=Z_MIN_DAYS).std()
    for W in (30, 90):
        P[f"rel_{W}"] = P[f"fed_z_{W}"] - P[f"ecb_z_{W}"]
    P["rel_d1m"] = P["rel_30"] - P["rel_30"].shift(30)
    P["rel_d3m"] = P["rel_90"] - P["rel_90"].shift(90)
    return P


def _monthly_on_grid(s: pd.Series, lag_days: int, cdate: pd.DatetimeIndex) -> np.ndarray:
    """Monthly statistic (PeriodIndex) on the session grid: usable from month-end + lag_days (+ 1 day), switched off
    when the newest usable observation became available more than STALE_M days ago."""
    s = s.dropna()
    if s.empty:
        return np.full(len(cdate), np.nan)
    av = s.index.to_timestamp(how="end").normalize() + pd.Timedelta(days=lag_days)
    v = _align_lagged(pd.Series(s.values, index=av), cdate, 1).values
    stamp = _align_lagged(pd.Series(av.values.astype("datetime64[ns]").astype("int64").astype(float), index=av), cdate, 1).values
    age = (cdate.values.astype("datetime64[ns]").astype("int64") - stamp) / 86400e9
    return np.where(age <= STALE_M + 1, v, np.nan)


def _orient_wf(raw: np.ndarray, D: pd.DataFrame) -> np.ndarray:
    """Orientation of a signal without a prior: for test year Y the sign of the covariance between the raw signal and
    the 21-session forward log return over rows whose label is known before Y-01-01."""
    lc = np.log(D["close"].values)
    n = len(lc)
    f = np.full(n, np.nan)
    f[: n - 21] = lc[21:] - lc[: n - 21]
    ct = D["close_time"].values.astype("datetime64[ns]").astype(np.int64)
    end = np.full(n, SL.NAT, dtype=np.int64)
    end[: n - 21] = ct[21:]
    yr = D.index.year.values
    o = np.full(n, np.nan)
    for Y in SL.YEARS:
        start = pd.Timestamp(f"{Y}-01-01", tz="UTC").value
        tr = (end != SL.NAT) & (end < start) & np.isfinite(raw) & np.isfinite(f)
        if tr.sum() >= 250:
            o[yr == Y] = np.sign(np.mean((raw[tr] - raw[tr].mean()) * (f[tr] - f[tr].mean())))
    return o


def build_signals(D: pd.DataFrame, R: dict | None = None, date_col: str = "date", want_panel: bool = False):
    """The 12 oriented signals on the session grid of the feature store (positive = long EUR/USD)."""
    R = load_raw() if R is None else R
    cdate = pd.DatetimeIndex(pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None))
    days = pd.date_range(CAL0, cdate[-1], freq="D")
    at = lambda s, k: s.reindex(cdate - pd.Timedelta(days=k)).values          # calendar-daily series, value of day c - k
    S = pd.DataFrame(index=D.index)
    # ---- 1 tone
    P = tone_panel(R["docs"], cdate[-1], date_col)
    S["tone_rel_lvl"] = -at(P["rel_90"], LAG["text"])
    S["tone_rel_d1m"] = -at(P["rel_d1m"], LAG["text"])
    S["tone_rel_d3m"] = -at(P["rel_d3m"], LAG["text"])
    # ---- 2 news sentiment (expanding mean over the published observations; calendar fill of at most STALE_D days)
    nw = R["news"]
    lvl = (nw - nw.expanding(min_periods=1825).mean()).reindex(days).ffill(limit=STALE_D)
    cal = nw.reindex(days).ffill(limit=STALE_D)
    S["news_lvl"] = -at(lvl, LAG["news"])
    S["news_d1m"] = -at(cal - cal.shift(30), LAG["news"])
    # ---- 3 uncertainty
    us = R["epu_us_d"]
    per = pd.PeriodIndex(us.index, freq="M")
    us_m = us.groupby(per).mean()[us.groupby(per).size() >= 25]                # complete months only
    M = R["epu_m"]
    ratio = (np.log(M["EUEPUINDXM"]) - np.log(us_m)).dropna()
    if len(ratio):
        ratio = ratio.reindex(pd.period_range(ratio.index[0], ratio.index[-1], freq="M"))
    S["epu_rel_d3m"] = -_monthly_on_grid(ratio.diff(3), LAG["epu"], cdate)
    tp = np.log(M["EPUTRADE"].dropna())
    if len(tp):
        tp = tp.reindex(pd.period_range(tp.index[0], tp.index[-1], freq="M"))
    raw_tpu = _monthly_on_grid(tp.diff(3), LAG["epu_cat"], cdate)
    orient = _orient_wf(raw_tpu, D)
    S["tpu_d3m"] = orient * raw_tpu
    g = R["gpr"].reindex(days)
    ma = np.log(g.rolling(30, min_periods=20).mean())
    S["gpr_d3m"] = -at(ma - ma.shift(90), LAG["gpr"])
    # ---- 4 policy surprises
    jk = R["jk"]
    for col, tag in (("MP_median", "mp"), ("CBI_median", "cbi")):
        cum = {}
        for bank in ("FED", "ECB"):
            b = jk[jk["bank"] == bank]
            if b.empty:
                cum[bank] = {W: pd.Series(np.nan, index=days) for W in (91, 182)}
                continue
            x = b.groupby("date")[col].sum().reindex(days, fill_value=0.0)
            live = (days >= b["date"].min()) & (days <= b["date"].max() + pd.Timedelta(days=JK_STALE))
            cum[bank] = {W: x.rolling(W, min_periods=W).sum().where((days >= b["date"].min() + pd.Timedelta(days=W)) & live) for W in (91, 182)}
        for W, nm in ((91, "3m"), (182, "6m")):
            S[f"jk_{tag}_{nm}"] = -at(cum["FED"][W] - cum["ECB"][W], LAG["jk"])
    S = S[NAMES].replace([np.inf, -np.inf], np.nan)
    if want_panel:
        return S, P, pd.Series(orient, index=D.index, name="tpu_orientation")
    return S


def orthogonalise(S: pd.DataFrame, X: pd.DataFrame) -> pd.DataFrame:
    """Walk-forward residual of each signal on the controls: for test year Y the OLS (with intercept) is fitted on rows
    dated before Y-01-01 and b'(x - mean_train(x)) is removed, so the signal keeps its own zero point. A control with
    fewer than 750 training rows (the house score before 2013) is left out for that year."""
    yr = S.index.year.values
    out = pd.DataFrame(np.nan, index=S.index, columns=S.columns)
    for nm in S.columns:
        s = S[nm].values
        for Y in SL.YEARS:
            te = yr == Y
            pre = yr < Y
            cols = [c for c in X.columns if (pre & np.isfinite(X[c].values) & np.isfinite(s)).sum() >= 750]
            if not cols:
                continue
            Xv = X[cols].values
            tr = pre & np.isfinite(s) & np.isfinite(Xv).all(axis=1)
            if tr.sum() < 750:
                continue
            mu = Xv[tr].mean(axis=0)
            A = np.column_stack([np.ones(tr.sum()), Xv[tr] - mu])
            b = np.linalg.lstsq(A, s[tr], rcond=None)[0][1:]
            ok = te & np.isfinite(Xv).all(axis=1)
            out.loc[ok, nm] = s[ok] - (Xv[ok] - mu) @ b
    return out


# ================================================================ evaluation helpers (as arms Q / R / T)
def old_votes(ctx: SL.Ctx) -> dict:
    hs = SL.house_score_wf(ctx)
    sg = np.sign(hs)
    cot, spr = np.sign(ctx.G["cot_z52"].values), np.sign(ctx.G["d_spread2y_20"].values)
    base = np.isfinite(hs) & (sg != 0)
    return {"hs": hs, "sg": sg, "cot": cot, "spr": spr, "base": base, "agree": base & (cot == sg) & (spr == sg)}


def eval_rule(ctx: SL.Ctx, T: dict, speak: np.ndarray, dirs: np.ndarray, tag: dict, horizons=HORIZONS, keep: dict | None = None) -> list[dict]:
    rows = []
    for h in horizons:
        t = T[f"sign{h}"]
        valid = np.isfinite(t.long)
        for mode in ("weekly", "nonoverlap"):
            idx = SL.weekly_idx(speak, valid) if mode == "weekly" else SL.seq_idx(speak, valid, t.hold)
            dec = SL.decision_frame(ctx, t, idx, dirs, None)
            if keep is not None:
                keep[(h, mode)] = dec
            for r in SL.cell_stats(ctx, t, dec, speak, mode):
                rows.append({**tag, "h": h, "mode": mode, **r})
    return rows


def era_rows(ctx: SL.Ctx, T: dict, has: np.ndarray, dirs: np.ndarray, nm: str, a: int = 2004, b: int = 2009) -> list[dict]:
    """Standalone accuracy in an era the walk-forward never tests (no house score there, so no extra-vote test)."""
    rows = []
    era = (ctx.year >= a) & (ctx.year <= b)
    for h in HORIZONS:
        t = T[f"sign{h}"]
        valid = np.isfinite(t.long)
        for mode in ("weekly", "nonoverlap"):
            idx = SL.weekly_idx(has & era, valid) if mode == "weekly" else SL.seq_idx(has & era, valid, t.hold)
            r = {"signal": nm, "rule": "standalone_era", "h": h, "mode": mode, "period": f"{a}-{str(b)[2:]}", "n": len(idx)}
            if len(idx):
                hit = np.where(dirs[idx] > 0, t.long[idx], t.short[idx]) > 0
                lo, hi = SL.wilson(float(hit.mean()), float(len(idx)))
                r.update({"accuracy": float(hit.mean()), "lo": lo, "hi": hi, "dec_per_year": len(idx) / (b - a + 1),
                          "share_long": float((dirs[idx] > 0).mean())})
            rows.append(r)
    return rows


def paired_boot(ctx: SL.Ctx, t: SL.Target, sa: np.ndarray, da: np.ndarray, sb: np.ndarray, db: np.ndarray, a: int, b: int,
                reps: int = 2000, seed: int = 7) -> dict:
    """acc(rule A) - acc(rule B) on the weekly grid of years a..b; both rules resampled with the SAME circular blocks."""
    valid = np.isfinite(t.long)
    g = np.arange(0, len(valid), SL.STEP)
    g = g[valid[g]]
    g = g[(ctx.year[g] >= a) & (ctx.year[g] <= b)]
    out = {"n_a": 0, "n_b": 0, "acc_a": np.nan, "acc_b": np.nan, "diff": np.nan, "lo": np.nan, "hi": np.nan, "p_le0": np.nan}
    if len(g) < 40:
        return out
    xa, xb = sa[g].astype(float), sb[g].astype(float)
    ha = xa * (np.where(da[g] > 0, t.long[g], t.short[g]) > 0)
    hb = xb * (np.where(db[g] > 0, t.long[g], t.short[g]) > 0)
    out.update({"n_a": int(xa.sum()), "n_b": int(xb.sum())})
    if xa.sum() < 5 or xb.sum() < 5:
        return out
    out.update({"acc_a": float(ha.sum() / xa.sum()), "acc_b": float(hb.sum() / xb.sum())})
    out["diff"] = out["acc_a"] - out["acc_b"]
    block = max(2, int(math.ceil(2 * t.h / SL.STEP)))
    Tn = len(g)
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(Tn / block))
    starts = rng.integers(0, Tn, size=(reps, nb))
    idx = ((starts[:, :, None] + np.arange(block)[None, None, :]) % Tn).reshape(reps, -1)[:, :Tn]
    na, nbb = xa[idx].sum(1), xb[idx].sum(1)
    ok = (na > 0) & (nbb > 0)
    d = ha[idx].sum(1)[ok] / na[ok] - hb[idx].sum(1)[ok] / nbb[ok]
    out.update({"lo": float(np.quantile(d, 0.025)), "hi": float(np.quantile(d, 0.975)), "p_le0": float((d <= 0).mean())})
    return out


def _cell(V: pd.DataFrame, **kw) -> pd.Series | None:
    m = np.ones(len(V), bool)
    for k, v in kw.items():
        m &= (V[k] == v).values
    x = V[m]
    return x.iloc[0] if len(x) else None


# ================================================================ main
def compute(cost_pips: float = 1.2, verbose: bool = True) -> dict:
    cat = fetch_all(verbose=verbose)
    D = SL.load_data()
    ctx = SL.make_ctx(D, cost_pips)
    T = SL.build_targets(D)
    R = load_raw()
    S, panel, orient = build_signals(D, R, want_panel=True)
    S_post = build_signals(D, R, date_col="post_date")[TONE_NAMES]
    O = old_votes(ctx)
    sg, agree = O["sg"], O["agree"]
    X = pd.DataFrame({"ret_21d": D["ret_21d"].values, "ret_63d": D["ret_63d"].values, "cot_z52": D["cot_z52"].values,
                      "d_spread2y_20": D["d_spread2y_20"].values, "house": O["hs"]}, index=D.index)
    S_op = orthogonalise(S, X[list(CTRL_PRICE)])
    S_oa = orthogonalise(S, X[list(CTRL_ALL)])
    rows, decs = [], {}
    keep = {}
    rows += eval_rule(ctx, T, agree, sg, {"signal": "-", "rule": "agree3"}, horizons=(10, 21, 42, 63), keep=keep)
    decs["agree3"] = keep
    P = [(lab, a, b) for lab, a, b in SL.PERIODS if lab != "2010-15"]
    paired = []

    def votes(s: np.ndarray):
        ss = np.sign(s)
        return ss, np.isfinite(s) & (ss != 0)

    for nm in NAMES:
        ss, has = votes(S[nm].values)
        rows += eval_rule(ctx, T, has & O["base"], ss, {"signal": nm, "rule": "standalone"})
        rows += era_rows(ctx, T, has, ss, nm)
        keep = {}
        sp_and = agree & has & (ss == sg)
        rows += eval_rule(ctx, T, sp_and, sg, {"signal": nm, "rule": "and"}, keep=keep)
        decs[nm] = keep
        rows += eval_rule(ctx, T, agree & has & (ss == -sg), sg, {"signal": nm, "rule": "agree3_contradicted"})
        rows += eval_rule(ctx, T, agree & has, sg, {"signal": nm, "rule": "agree3_same_span"})
        rows += eval_rule(ctx, T, O["base"] & ~agree & has, ss, {"signal": nm, "rule": "outside"})
        for k in PLACEBO_SHIFTS + (1, 5, 21, -21):                 # staler (+) and look-ahead (-) versions
            sks, hk = votes(S[nm].shift(k).values)
            rows += eval_rule(ctx, T, agree & hk & (sks == sg), sg, {"signal": nm, "rule": f"and_shift{k:+d}"})
            rows += eval_rule(ctx, T, hk & O["base"], sks, {"signal": nm, "rule": f"standalone_shift{k:+d}"})
            if k in PLACEBO_SHIFTS:
                rows += eval_rule(ctx, T, O["base"] & ~agree & hk, sks, {"signal": nm, "rule": f"outside_shift{k:+d}"})
        for lab, So in (("ortho_price", S_op), ("ortho_all", S_oa)):   # round-7 control
            so, ho = votes(So[nm].values)
            rows += eval_rule(ctx, T, ho & O["base"], so, {"signal": nm, "rule": f"standalone_{lab}"})
            rows += eval_rule(ctx, T, agree & ho & (so == sg), sg, {"signal": nm, "rule": f"and_{lab}"})
            rows += eval_rule(ctx, T, agree & ho, sg, {"signal": nm, "rule": f"agree3_same_span_{lab}"})
        if nm in TONE_NAMES:                                           # stricter dating: BIS posting date
            sp_, hp = votes(S_post[nm].values)
            rows += eval_rule(ctx, T, hp & O["base"], sp_, {"signal": nm, "rule": "standalone_postdate"})
            rows += eval_rule(ctx, T, agree & hp & (sp_ == sg), sg, {"signal": nm, "rule": "and_postdate"})
        for h in HORIZONS:
            t = T[f"sign{h}"]
            for lab, a, b in P:
                r1 = paired_boot(ctx, t, sp_and, sg, agree & has, sg, a, b)
                r2 = paired_boot(ctx, t, sp_and, sg, agree & has & (ss == -sg), sg, a, b)
                paired.append({"signal": nm, "h": h, "period": lab, "n_and": r1["n_a"], "n_agree_same_span": r1["n_b"], "acc_and": r1["acc_a"],
                               "acc_agree_same_span": r1["acc_b"], "diff": r1["diff"], "diff_lo": r1["lo"], "diff_hi": r1["hi"], "p_le0": r1["p_le0"],
                               "n_contradicted": r2["n_b"], "acc_contradicted": r2["acc_b"], "split": r2["diff"], "split_lo": r2["lo"], "split_hi": r2["hi"],
                               "split_p_le0": r2["p_le0"]})
        if verbose:
            print(f"  signal {nm}: done", flush=True)
    V = pd.DataFrame(rows)
    return {"cat": cat, "D": D, "ctx": ctx, "T": T, "R": R, "S": S, "S_post": S_post, "S_op": S_op, "S_oa": S_oa, "X": X, "panel": panel, "orient": orient,
            "O": O, "V": V, "paired": pd.DataFrame(paired), "decs": decs}


def select_final(V: pd.DataFrame) -> tuple[pd.DataFrame, str, str]:
    rows = []
    for nm in NAMES:
        c = _cell(V, signal=nm, rule="and", h=SEL_H, mode="nonoverlap", period="2010-15")
        rows.append({"signal": nm, "n_2010-15": int(c["n"]), "dec_per_year_2010-15": c.get("dec_per_year", np.nan), "accuracy_2010-15": c.get("accuracy", np.nan),
                     "lo_2010-15": c.get("lo", np.nan), "hi_2010-15": c.get("hi", np.nan)})
    Sx = pd.DataFrame(rows)
    Sx["eligible"] = Sx["dec_per_year_2010-15"] >= MIN_DEC_PER_YEAR
    el = Sx[Sx["eligible"] & Sx["lo_2010-15"].notna()]
    if len(el):
        final, status = el.sort_values("lo_2010-15", ascending=False)["signal"].iloc[0], "selected by the declared rule"
    else:
        pool = Sx[Sx["lo_2010-15"].notna()]
        final = pool.sort_values("lo_2010-15", ascending=False)["signal"].iloc[0]
        status = "NO candidate has 6 decisions a year in 2010-15 - nominal stream only (fails the declared rule)"
    Sx["final"] = Sx["signal"] == final
    return Sx, final, status


def bar_table(V: pd.DataFrame, nm: str, rule: str = "and") -> pd.DataFrame:
    """The round-5 success bar, cell by cell, for one candidate's AND rule (non-overlapping decisions)."""
    rows = []
    for h in (21, 42, 63):
        for lab in ("2010-26", "2016-26", "2023-26"):
            a = _cell(V, signal=nm, rule=rule, h=h, mode="nonoverlap", period=lab)
            b = _cell(V, signal="-", rule="agree3", h=h, mode="nonoverlap", period=lab)
            r = {"h": h, "period": lab, "agree3_acc": b["accuracy"], "agree3_n": int(b["n"]), "agree3_per_year": b["dec_per_year"],
                 "and_acc": a.get("accuracy", np.nan), "and_lo": a.get("lo", np.nan), "and_hi": a.get("hi", np.nan), "and_n": int(a["n"]),
                 "and_per_year": a.get("dec_per_year", np.nan)}
            r["gain_pts"] = 100 * (r["and_acc"] - r["agree3_acc"])
            for k in PLACEBO_SHIFTS:
                p = _cell(V, signal=nm, rule=f"and_shift{k:+d}", h=h, mode="nonoverlap", period=lab)
                r[f"placebo{k}_acc"] = p.get("accuracy", np.nan)
                r[f"placebo{k}_n"] = int(p["n"])
                r[f"placebo{k}_gain_pts"] = 100 * (r[f"placebo{k}_acc"] - r["agree3_acc"])
            rows.append(r)
    return pd.DataFrame(rows)


def bar_verdict(B: pd.DataFrame) -> dict:
    g = lambda h, lab, c: float(B[(B.h == h) & (B.period == lab)][c].iloc[0])
    v = {}
    v["gain_ok"] = all(g(h, lab, "gain_pts") >= 3.0 for h in (21, 42) for lab in ("2010-26", "2016-26"))
    v["count21_ok"] = all(g(21, lab, "and_per_year") >= MIN_DEC_PER_YEAR for lab in ("2010-26", "2016-26"))
    v["count42_ok"] = all(g(42, lab, "and_per_year") >= MIN_DEC_PER_YEAR for lab in ("2010-26", "2016-26"))
    v["not_worse_2023"] = all(g(h, "2023-26", "gain_pts") >= 0 for h in (21, 42))
    pl = []
    for h in (21, 42):
        for lab in ("2010-26", "2016-26"):
            gain = g(h, lab, "gain_pts")
            pl.append(all(g(h, lab, f"placebo{k}_gain_pts") <= 0.5 * gain for k in PLACEBO_SHIFTS) if gain > 0 else False)
    v["placebo_ok"] = all(pl)
    v["met"] = bool(v["gain_ok"] and v["count21_ok"] and v["not_worse_2023"] and v["placebo_ok"])
    v["met_strict_42_count"] = bool(v["met"] and v["count42_ok"])
    return v


def controls_table(res: dict) -> pd.DataFrame:
    """Round 7: what each signal is correlated with (2010-26, sessions where it is defined)."""
    D, S, X, O = res["D"], res["S"], res["X"], res["O"]
    y = D.index.year.values >= 2010
    rows = []
    for nm in NAMES:
        s = S[nm]
        r = {"signal": nm, "first_value": str(s.first_valid_index())[:10], "last_value": str(s.last_valid_index())[:10],
             "defined_2010-26": float(s[y].notna().mean()), "share_long_2010-26": float((s[y] > 0).sum() / max(s[y].notna().sum(), 1)),
             "sign_flips_per_year": float((np.sign(s[y]).diff().abs() > 0).sum() / (y.sum() / 252))}
        for c in CTRL_ALL:
            r[f"corr_{c}"] = float(s[y].corr(X[c][y]))
        for c, v in (("cot", O["cot"]), ("spr", O["spr"]), ("house", O["sg"])):
            ok = y & np.isfinite(s.values) & np.isfinite(v) & (v != 0) & (np.sign(s.values) != 0)
            r[f"sign_agree_{c}"] = float((np.sign(s.values[ok]) == v[ok]).mean()) if ok.sum() else np.nan
        ok = y & np.isfinite(s.values) & np.isfinite(X[list(CTRL_ALL)].values).all(axis=1)
        if ok.sum() > 200:
            A = np.column_stack([np.ones(ok.sum()), X[list(CTRL_ALL)].values[ok]])
            e = s.values[ok] - A @ np.linalg.lstsq(A, s.values[ok], rcond=None)[0]
            r["r2_all_controls"] = float(1 - e.var() / s.values[ok].var())
            A = A[:, :3]
            e = s.values[ok] - A @ np.linalg.lstsq(A, s.values[ok], rcond=None)[0]
            r["r2_price_controls"] = float(1 - e.var() / s.values[ok].var())
        for h in (21, 63):
            f = pd.Series(res["T"][f"sign{h}"].long, index=D.index)
            r[f"corr_fwd{h}"] = float(s[y].corr(f[y]))
        rows.append(r)
    return pd.DataFrame(rows)


def leak_checks(res: dict, final: str, reps: int = 300) -> dict:
    ctx, T, S, O, D, R = res["ctx"], res["T"], res["S"], res["O"], res["D"], res["R"]
    sg, agree = O["sg"], O["agree"]
    out = {}
    # (1) permuted labels
    rng = np.random.default_rng(3)
    rows = []
    for h in HORIZONS:
        t = T[f"sign{h}"]
        valid = np.isfinite(t.long) & (ctx.year >= 2010)
        vi = np.where(valid)[0]
        g = np.arange(0, len(valid), SL.STEP)
        g = g[valid[g]]
        for nm in dict.fromkeys([final, "tone_rel_d3m", "jk_mp_6m"]):
            s = np.sign(S[nm].values)
            has = np.isfinite(S[nm].values) & (s != 0)
            for rule, sp, dr in (("and", agree & has & (s == sg), sg), ("standalone", has & O["base"], s)):
                gi = g[sp[g]]
                if len(gi) < 5:
                    continue
                real = float((np.where(dr[gi] > 0, t.long[gi], t.short[gi]) > 0).mean())
                acc = []
                for _ in range(reps):
                    perm = np.arange(len(valid))
                    perm[vi] = rng.permutation(vi)
                    L = t.long[perm]
                    acc.append(float((np.where(dr[gi] > 0, L[gi], -L[gi]) > 0).mean()))
                acc = np.array(acc)
                rows.append({"signal": nm, "rule": rule, "h": h, "n_weekly": len(gi), "real_acc": real, "shuffled_mean": acc.mean(),
                             "shuffled_p05": np.quantile(acc, 0.05), "shuffled_p95": np.quantile(acc, 0.95), "p_shuffled_ge_real": float((acc >= real).mean())})
    out["shuffle"] = pd.DataFrame(rows)
    # (2b) truncation test: the row of date T0 built from raw data cut at T0 must equal the full build
    rows = []
    cdate = pd.DatetimeIndex(pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").normalize().tz_localize(None))
    for d0 in ("2012-06-29", "2016-11-15", "2020-03-16", "2022-09-30", "2025-02-14"):
        i = int(np.searchsorted(cdate.values, np.datetime64(d0), side="right") - 1)
        St = build_signals(D.iloc[: i + 1], truncate_raw(R, cdate[i]))
        a, b = S.iloc[i].values.astype(float), St.iloc[i].values.astype(float)
        same = np.isclose(a, b, rtol=1e-9, atol=1e-12, equal_nan=True)
        rows.append({"asof": str(cdate[i].date()), "signals_defined": int(np.isfinite(a).sum()), "rows_equal": int(same.sum()), "of": len(a),
                     "max_abs_diff": float(np.nanmax(np.abs(a - b))) if np.isfinite(a - b).any() else 0.0, "mismatch": ",".join(np.array(NAMES)[~same])})
    out["truncation"] = pd.DataFrame(rows)
    out["features"] = controls_table(res)
    return out


def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True) -> tuple[pd.Series, pd.DataFrame]:
    """Arm entry point: (daily positions of the final AND rule, protocol report). Writes the deliverables."""
    pos, rep, _ = run_full(cost_pips, write, verbose)
    return pos, rep


def doc_counts(docs: pd.DataFrame) -> pd.DataFrame:
    d = docs.copy()
    d["year"] = d["date"].dt.year
    d["grp"] = np.where(d.inst == "FED", "Fed " + d.kind.str.replace("fomc_", "FOMC "), np.where(d.inst == "ECB", "ECB speech (BIS)", "ECB speech (ECB copy)"))
    n = d.pivot_table(index="year", columns="grp", values="hits", aggfunc="size", fill_value=0)
    sc = d[d.tone.notna()].pivot_table(index="year", columns="grp", values="hits", aggfunc="size", fill_value=0)
    out = n.copy()
    out["Fed all"] = n[[c for c in n.columns if c.startswith("Fed")]].sum(axis=1)
    out["Fed scored"] = sc[[c for c in sc.columns if c.startswith("Fed")]].sum(axis=1)
    out["ECB (BIS) scored"] = sc.get("ECB speech (BIS)", 0)
    tn = d[d.tone.notna()].groupby(["year", "inst"])["tone"].mean().unstack()
    out["Fed mean tone"], out["ECB mean tone"] = tn.get("FED"), tn.get("ECB")
    return out.reset_index()


def ecb_crosscheck(docs: pd.DataFrame) -> dict:
    """Monthly ECB tone from the BIS selection against the same score on the ECB's own complete file (copy to 2023-02)."""
    d = docs[docs.tone.notna()].copy()
    d["m"] = d["date"].dt.to_period("M")
    a = d[d.inst == "ECB"].groupby("m")["tone"].mean()
    b = d[d.inst == "ECB_COPY"].groupby("m")["tone"].mean()
    j = pd.concat([a, b], axis=1, keys=["bis", "copy"]).dropna()
    j = j[j.index >= "1999-01"]
    q = j.groupby(j.index.asfreq("Q")).mean()
    return {"months": len(j), "corr_monthly": float(j["bis"].corr(j["copy"])), "corr_quarterly": float(q["bis"].corr(q["copy"])),
            "corr_monthly_2010on": float(j[j.index >= "2010-01"]["bis"].corr(j[j.index >= "2010-01"]["copy"])),
            "mean_bis": float(j["bis"].mean()), "mean_copy": float(j["copy"].mean()),
            "n_bis": int(((docs.inst == "ECB") & (docs.date <= "2023-02-28") & (docs.date >= "1999-01-01")).sum()),
            "n_copy": int(((docs.inst == "ECB_COPY") & (docs.date >= "1999-01-01")).sum())}


def run_full(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Builds the signals, evaluates the 12 candidates as rounds 5 and 7 prescribe, applies the declared selection rule
    and writes the deliverables. Returns (daily positions, protocol report, every intermediate table)."""
    res = compute(cost_pips, verbose=verbose)
    ctx, T, V, D = res["ctx"], res["T"], res["V"], res["D"]
    Sx, final, status = select_final(V)
    res["selection"], res["final"], res["final_status"] = Sx, final, status
    res["bar"] = bar_table(V, final)
    res["bar_verdict"] = bar_verdict(res["bar"])
    res["bar_all"] = pd.concat([bar_table(V, nm).assign(signal=nm) for nm in NAMES], ignore_index=True)
    res["bar_verdict_all"] = pd.DataFrame([{"signal": nm, **bar_verdict(bar_table(V, nm))} for nm in NAMES])
    reps, streams = [], {}

    def book(dec, cp):
        cx = ctx if cp == cost_pips else SL.make_ctx(D, cp)
        b = SL.book_time_exit(cx, dec, SEL_H, cp)
        return b[b.index.year >= 2010]

    for nm in NAMES + ["agree3"]:
        dec = res["decs"][nm][(SEL_H, "weekly")]
        streams[nm] = book(dec, cost_pips)
        tb = report(streams[nm], periods_per_year=252, name=ARM, n_arms=N_ARMS)
        tb.insert(1, "variant", f"and_{nm}" if nm != "agree3" else "agree3_reference")
        tb["final"] = nm == final
        tb["kind"] = "candidate" if nm != "agree3" else "reference"
        tb["cost_pips"] = cost_pips
        reps.append(tb)
    tb = report(book(res["decs"][final][(SEL_H, "weekly")], 0.6), periods_per_year=252, name=ARM, n_arms=N_ARMS)
    tb.insert(1, "variant", f"and_{final}_cost0.6"); tb["final"] = False; tb["kind"] = "cost_sensitivity"; tb["cost_pips"] = 0.6
    reps.append(tb)
    rep = pd.concat(reps, ignore_index=True)
    daily = streams[final].copy()
    daily["fwd_bp"] = D["fwd_1d"].reindex(daily.index)
    daily = daily[["pos", "fwd_bp", "net_bp"]]
    res["report"], res["streams"], res["daily"] = rep, streams, daily
    by = SL.by_year(res["decs"][final][(SEL_H, "weekly")])
    ref = SL.by_year(res["decs"]["agree3"][(SEL_H, "weekly")]).set_index("year")
    by["agree3_decisions"] = by["year"].map(ref["decisions"])
    by["agree3_accuracy"] = by["year"].map(ref["accuracy"])
    yr = rep[(rep["variant"] == f"and_{final}") & rep["period"].str.fullmatch(r"\d{4}")]
    by["book_sharpe"] = by["year"].map(pd.Series(yr["sharpe"].values, index=yr["period"].astype(int).values))
    res["by_year"] = by
    res["leak"] = leak_checks(res, final)
    docs = res["R"]["docs"]
    res["doc_counts"] = doc_counts(docs)
    res["ecb_check"] = ecb_crosscheck(docs)
    lagd = (docs["post_date"] - docs["date"]).dt.days
    res["post_lag"] = {k: {"median": float(lagd[(docs.inst == k) & (docs.kind == "speech")].median()), "p90": float(lagd[(docs.inst == k) & (docs.kind == "speech")].quantile(0.9))}
                       for k in ("FED", "ECB")}
    # the tone series for the weekly outlook
    P = res["panel"]
    tone = P[P.index >= "2000-01-01"].round(4)
    cur = {}
    lastdoc = {k: docs[(docs.inst == k) & docs.tone.notna()]["date"].max() for k in ("FED", "ECB")}
    for c in ("fed_tone_30", "fed_tone_90", "ecb_tone_30", "ecb_tone_90", "fed_z_30", "fed_z_90", "ecb_z_30", "ecb_z_90", "rel_30", "rel_90", "rel_d1m", "rel_d3m"):
        x = P[c].dropna()
        cur[c] = {"date": str(x.index[-1].date()), "value": float(x.iloc[-1])} if len(x) else None
    cur["last_scored_doc"] = {k: str(v.date()) for k, v in lastdoc.items()}
    cur["panel_last_row"] = {c: (None if pd.isna(P[c].iloc[-1]) else float(P[c].iloc[-1])) for c in P.columns}
    cur["panel_last_date"] = str(P.index[-1].date())
    cur["signals_last_row"] = {nm: (None if pd.isna(res["S"][nm].iloc[-1]) else float(res["S"][nm].iloc[-1])) for nm in NAMES}
    cur["signals_last_session"] = str(D.index[-1])
    res["current"] = cur
    if write:
        RES.mkdir(parents=True, exist_ok=True)
        (RES / "logs").mkdir(exist_ok=True)
        daily.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        V.insert(0, "arm", ARM) if "arm" not in V else None
        V["final"] = (V["signal"] == final) & (V["rule"] == "and")
        V.to_csv(RES / f"{ARM}_votes.csv", index=False)
        res["paired"].to_csv(RES / f"{ARM}_paired.csv", index=False)
        Sx.to_csv(RES / f"{ARM}_candidates.csv", index=False)
        res["bar_all"].to_csv(RES / f"{ARM}_bar.csv", index=False)
        res["S"].to_parquet(RES / f"{ARM}_signals.parquet")
        res["cat"].to_csv(RES / f"{ARM}_data_catalogue.csv", index=False)
        res["doc_counts"].to_csv(RES / f"{ARM}_doc_counts.csv", index=False)
        pd.concat([v.assign(check=k) for k, v in res["leak"].items()], ignore_index=True).to_csv(RES / f"{ARM}_leakchecks.csv", index=False)
        tone.to_csv(MACRO / f"{ARM}_tone_daily.csv")
        sd = res["S"].copy()
        sd.insert(0, "close_date", pd.DatetimeIndex(D["close_time"]).tz_convert("UTC").strftime("%Y-%m-%d"))
        sd["tpu_orientation"] = res["orient"].values
        sd.round(5).to_csv(MACRO / f"{ARM}_signals_daily.csv")
        res["incremental"], res["corr"] = incremental(streams, final)
        res["incremental"].to_csv(RES / f"{ARM}_incremental.csv", index=False)
        keep = ("V", "paired", "selection", "final", "final_status", "bar", "bar_verdict", "bar_all", "bar_verdict_all", "report", "by_year", "leak",
                "doc_counts", "ecb_check", "post_lag", "current", "incremental", "corr", "cat")
        pd.to_pickle({k: res[k] for k in keep if k in res}, RES / "logs" / f"{ARM}_tables.pkl")
    return daily["pos"], rep, res


def incremental(streams: dict, final: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    from eurusd.arms import meta
    rows = []
    for lab, arms in (("two-way weak_signals + regime_trend", ["weak_signals", "regime_trend"]),
                      (f"three-way + {ARM}", ["weak_signals", "regime_trend", ARM]),
                      ("three-way + selective (agreement rule book, for reference)", ["weak_signals", "regime_trend", "selective_daily"])):
        if "selective_daily" in arms and not (RES / "selective_daily_positions.parquet").exists():
            continue
        pnl, _ = meta.combine(arms, "EW")
        tb = meta.report_combo(pnl, lab, N_ARMS)
        rows.append(tb[tb.period.isin(["2010-2026", "2016-2026", "2023-2026"])])
    inc = pd.concat(rows, ignore_index=True)
    me = meta.load_arm_daily(ARM)
    cr = []
    for other in ("weak_signals", "regime_trend", "selective_daily"):
        o = meta.load_arm_daily(other)
        if len(o) < 100:
            continue
        j = pd.concat([me, o], axis=1, keys=["me", "o"]).fillna(0.0)
        j = j[j.index.year >= 2010]
        act = j[j["me"] != 0]
        cr.append({"other": other, "corr_all_days": float(j["me"].corr(j["o"])), "corr_active_days": float(act["me"].corr(act["o"])),
                   "corr_2016-26": float(j[j.index.year >= 2016]["me"].corr(j[j.index.year >= 2016]["o"]))})
    return inc, pd.DataFrame(cr)


# ================================================================ report (python -m eurusd.arms.text_news report)
def _fmt(c, ci: bool = True, py: bool = False) -> str:
    if c is None or not c["n"] or not np.isfinite(c.get("accuracy", np.nan)):
        return "-"
    s = f"{100 * c['accuracy']:.0f}"
    if ci:
        s += f" [{100 * c['lo']:.0f}-{100 * c['hi']:.0f}]"
    s += f" n={int(c['n'])}"
    if py:
        s += f" ({c['dec_per_year']:.1f}/y)"
    return s


def _grid(V: pd.DataFrame, rule: str, mode: str, period: str, sigs, ci=True, py=False, hs=HORIZONS, gain_vs: pd.DataFrame | None = None) -> pd.DataFrame:
    rows = []
    for nm in sigs:
        r = {"signal": nm}
        for h in hs:
            c = _cell(V, signal=nm, rule=rule, h=h, mode=mode, period=period)
            txt = _fmt(c, ci, py)
            if gain_vs is not None and c is not None and c["n"] and np.isfinite(c.get("accuracy", np.nan)):
                b = _cell(gain_vs, h=h, mode=mode, period=period)
                txt += f" {100 * (c['accuracy'] - b['accuracy']):+.1f}"
            r[f"{h} s"] = txt
        rows.append(r)
    return pd.DataFrame(rows)


def _dict_md() -> str:
    d = TONE_DICT
    L = ["| part | entries |", "|---|---|",
         "| multi-word expressions merged into one token | " + "; ".join(f"`{p}` -> {t}" for p, t in d["phrases"]).replace("|", "\\|") + " |",
         "| (A) topic nouns, up = hawkish | " + ", ".join(d["topics_up_hawkish"]) + " |",
         "| (A) topic nouns, up = dovish (slack group) | " + ", ".join(d["topics_up_dovish"]) + " |",
         "| (A) direction words: up | " + ", ".join(d["up"]) + " |",
         "| (A) direction words: down | " + ", ".join(d["down"]) + " |",
         "| (B) outright hawkish terms | " + ", ".join(d["hawkish"]) + " |",
         "| (B) outright dovish terms | " + ", ".join(d["dovish"]) + " |",
         "| (B) hawkish only with a policy word within 4 tokens | " + ", ".join(d["hawkish_if_policy"]) + " |",
         "| (B) dovish only with a policy word within 4 tokens | " + ", ".join(d["dovish_if_policy"]) + " |",
         "| policy words | " + ", ".join(d["policy_words"]) + " |",
         "| dovish nouns that turn hawkish after a removal word (within 4 tokens before) | " + ", ".join(d["reversible_dovish"]) + " |",
         "| removal words | " + ", ".join(d["reversers"]) + " |",
         "| negators (within 3 tokens before; flip the hit) | " + ", ".join(d["negators"]) + ", any token ending in n't |",
         "| British -> American | " + ", ".join(f"{a} -> {b}" for a, b in d["british"].items()) + " |",
         f"| windows | topic-direction {d['window_topic']} tokens, negation {d['window_negation']}, policy word {d['window_policy']}, removal word {d['window_reverser']}; "
         f"a document needs {MIN_HITS} hits to carry a tone |"]
    return "\n".join(L)


def write_report(path: Path | None = None) -> str:
    r = pd.read_pickle(RES / "logs" / f"{ARM}_tables.pkl")
    V, P, final = r["V"], r["paired"], r["final"]
    A = V[(V.signal == "-") & (V.rule == "agree3")]
    md = [VERDICT_MD.strip(), ""]
    # ---- 1 data
    cat = r["cat"].copy()
    md += ["## 1. Data: sources, spans, publication lags", cat[["series", "rows", "first", "last", "lag used", "fetched", "file"]].to_markdown(index=False), "",
           "URLs: " + "; ".join(f"`{u}`" for u in dict.fromkeys(cat["url"])), "", DATA_MD.strip(), ""]
    dc = r["doc_counts"].copy()
    for c in dc.columns:
        if c not in ("Fed mean tone", "ECB mean tone"):
            dc[c] = dc[c].fillna(0).astype(int)
    md += ["**Documents per institution per year** (all documents, then those with at least 5 dictionary hits = the ones that enter the tone; mean tone of the year)", "",
           dc.round(2).to_markdown(index=False), ""]
    e, pl = r["ecb_check"], r["post_lag"]
    md += [f"**ECB cross-check.** The same scorer on the ECB's own complete speech file (copy, 1999-01 .. 2023-02; {e['n_copy']} speeches) against the BIS selection "
           f"({e['n_bis']} ECB speeches in the same span): monthly mean tone correlates {e['corr_monthly']:.2f} over {e['months']} common months "
           f"({e['corr_monthly_2010on']:.2f} from 2010; quarterly {e['corr_quarterly']:.2f}); mean tone {e['mean_bis']:+.3f} (BIS) against {e['mean_copy']:+.3f} (copy). "
           "The BIS selection is therefore a fair sample of what the ECB said; the copy does not enter any signal.", "",
           f"**BIS posting delay** (posting date in the URL minus speech date): Fed speeches median {pl['FED']['median']:.0f} days (90th percentile {pl['FED']['p90']:.0f}), "
           f"ECB median {pl['ECB']['median']:.0f} (90th percentile {pl['ECB']['p90']:.0f}). The signals date a speech by its own date (the central bank publishes the text "
           "itself on the day); section 9 repeats the tone tests dated by the BIS posting date.", ""]
    # ---- 2 dictionary
    md += ["## 2. The tone dictionary (frozen in `TONE_DICT` before any result)", DICT_MD.strip(), "", _dict_md(), ""]
    # ---- 3 signals
    F = r["leak"]["features"].set_index("signal")
    rows = []
    for nm, fam, prior in SIGNALS:
        f = F.loc[nm]
        rows.append({"signal": nm, "family": fam, "prior (sign on the raw quantity)": prior, "first value": f["first_value"], "last value": f["last_value"],
                     "defined 2010-26": f"{100 * f['defined_2010-26']:.0f} %", "long share": f"{100 * f['share_long_2010-26']:.0f} %",
                     "sign flips / yr": f"{f['sign_flips_per_year']:.1f}"})
    md += ["## 3. The 12 candidate signals and their priors (fixed before any result)", pd.DataFrame(rows).to_markdown(index=False), "", PRIORS_MD.strip(), ""]
    # ---- 4 reconciliation
    rows = []
    armN = {("nonoverlap", "2010-26"): "56 n=291 / 59 n=156 / 61 n=89 / 72 n=61", ("nonoverlap", "2016-26"): "53 n=178 / 57 n=96 / 59 n=56 / 71 n=38",
            ("nonoverlap", "2023-26"): "54 n=63 / 60 n=35 / 45 n=20 / 50 n=14", ("weekly", "2010-26"): "57 n=390 / 59 n=387 / 65 n=383 / 67 n=383",
            ("weekly", "2016-26"): "55 n=246 / 57 n=243 / 63 n=239 / 67 n=239", ("weekly", "2023-26"): "57 n=80 / 55 n=77 / 47 n=73 / 53 n=73"}
    for (mode, per), ref in armN.items():
        mine = " / ".join(_fmt(_cell(A, h=h, mode=mode, period=per), ci=False) for h in (10, 21, 42, 63))
        dy = " / ".join(f"{_cell(A, h=h, mode=mode, period=per)['dec_per_year']:.1f}" for h in (10, 21, 42, 63))
        rows.append({"decisions": mode, "period": per, "arm N report (10 / 21 / 42 / 63 s)": ref, "rebuilt here": mine, "identical": ref == mine, "decisions / yr": dy})
    md += ["## 4. Reconciliation of the agreement rule", RECON_MD.strip(), "", pd.DataFrame(rows).to_markdown(index=False), ""]
    # ---- 5 standalone
    md += ["## 5. Standalone accuracy of each signal (direction = sign of the oriented signal)", STANDALONE_MD.strip(), ""]
    for per in ("2010-26", "2016-26", "2023-26"):
        a = _grid(V, "standalone", "nonoverlap", per, NAMES, py=True).rename(columns={f"{h} s": f"non-overlapping {h} s" for h in HORIZONS})
        b = _grid(V, "standalone", "weekly", per, NAMES, ci=False).rename(columns={f"{h} s": f"weekly {h} s" for h in HORIZONS})
        md += [f"*{per}* (accuracy % [Wilson 95 %] n (decisions / year))", "", a.merge(b, on="signal").to_markdown(index=False), ""]
    E = V[V.rule == "standalone_era"]
    rows = []
    for nm in NAMES:
        x = {"signal": nm}
        for h in HORIZONS:
            x[f"non-overlapping {h} s"] = _fmt(_cell(E, signal=nm, h=h, mode="nonoverlap"))
        for h in HORIZONS:
            x[f"weekly {h} s"] = _fmt(_cell(E, signal=nm, h=h, mode="weekly"), ci=False)
        rows.append(x)
    md += ["*Other era, 2004-09* (never a test year; the same fixed rule; `tpu_d3m` has no orientation before 2010)", "", pd.DataFrame(rows).to_markdown(index=False), ""]
    # ---- 6 round-7 controls
    f = r["leak"]["features"]
    c1 = f[["signal", "corr_cot_z52", "corr_d_spread2y_20", "corr_house", "corr_ret_21d", "corr_ret_63d", "r2_price_controls", "r2_all_controls",
            "sign_agree_cot", "sign_agree_spr", "sign_agree_house", "corr_fwd21", "corr_fwd63"]].copy()
    md += ["## 6. Round 7 controls: is it new information or the recent price move restated?", CONTROLS_MD.strip(), "",
           "**Correlations, 2010-26** (daily sessions; `r2` = share of the signal's variance explained in-sample by the trailing returns / by all five controls; "
           "`sign_agree` = share of sessions on which the signal's vote equals the old vote; `corr_fwd` = correlation with the forward 21- / 63-session return)", "",
           c1.round(2).to_markdown(index=False), ""]
    for per in ("2010-26", "2016-26"):
        rows = []
        for nm in NAMES:
            x = {"signal": nm}
            for h in (21, 42, 63):
                x[f"{h} s raw / ex-price / ex-all"] = " / ".join(_fmt(_cell(V, signal=nm, rule=rl, h=h, mode="nonoverlap", period=per), ci=False)
                                                                for rl in ("standalone", "standalone_ortho_price", "standalone_ortho_all"))
            rows.append(x)
        md += [f"**Standalone accuracy after orthogonalising, non-overlapping decisions, {per}** (raw signal / residual on trailing returns / residual on all five controls)", "",
               pd.DataFrame(rows).to_markdown(index=False), ""]
    rows = []
    for nm in NAMES:
        x = {"signal": nm}
        for per in ("2010-26", "2016-26"):
            for h in (21, 42):
                parts = []
                for rl, bs in (("and", "agree3_same_span"), ("and_ortho_price", "agree3_same_span_ortho_price"), ("and_ortho_all", "agree3_same_span_ortho_all")):
                    a_, b_ = _cell(V, signal=nm, rule=rl, h=h, mode="nonoverlap", period=per), _cell(V, signal=nm, rule=bs, h=h, mode="nonoverlap", period=per)
                    ok = a_ is not None and b_ is not None and a_["n"] and b_["n"]
                    parts.append(f"{100 * (a_['accuracy'] - b_['accuracy']):+.0f} (n={int(a_['n'])})" if ok else "-")
                x[f"{per}, {h} s"] = " / ".join(parts)
        rows.append(x)
    md += ["**AND-rule gain over the agreement rule on the same span, in points: raw / ex-price / ex-all** (non-overlapping; n = decisions of the AND rule)", "",
           pd.DataFrame(rows).to_markdown(index=False), ""]
    # ---- 7 extra vote
    md += ["## 7. As an extra vote on the agreement rule", EXTRA_MD.strip(), ""]
    for per in ("2010-26", "2016-26", "2023-26"):
        base = pd.DataFrame([{"signal": "agreement rule alone", **{f"{h} s": _fmt(_cell(A, h=h, mode="nonoverlap", period=per), py=True) for h in HORIZONS}}])
        a = _grid(V, "and", "nonoverlap", per, NAMES, py=True, gain_vs=A)
        md += [f"**(a) AND rule, non-overlapping decisions, {per}** (accuracy % [Wilson] n (decisions / year), then the gain in points over the agreement rule)", "",
               pd.concat([base, a], ignore_index=True).to_markdown(index=False), ""]
    for per in ("2010-26", "2016-26"):
        rows = []
        for nm in NAMES:
            x = {"signal": nm}
            for h in HORIZONS:
                x[f"{h} s: same span / confirmed / contradicted"] = " / ".join(_fmt(_cell(V, signal=nm, rule=rl, h=h, mode="weekly", period=per), ci=False)
                                                                              for rl in ("agree3_same_span", "and", "agree3_contradicted"))
            rows.append(x)
        md += [f"**Agreement calls the signal confirms vs contradicts, weekly decisions, {per}**", "", pd.DataFrame(rows).to_markdown(index=False), ""]
    for per in ("2010-26", "2016-26", "2023-26"):
        a = _grid(V, "outside", "nonoverlap", per, NAMES, py=True)
        md += [f"**(b) OUTSIDE the agreement (the three old signals disagree; direction = the new signal), non-overlapping, {per}**", "", a.to_markdown(index=False), ""]
    rows = []
    for nm in NAMES:
        for per in ("2010-26", "2016-26"):
            x = {"signal": nm, "period": per}
            for h in (21, 42):
                p = P[(P.signal == nm) & (P.h == h) & (P.period == per)].iloc[0]
                x[f"{h} s: AND - same span"] = f"{100 * p['diff']:+.1f} [{100 * p['diff_lo']:+.0f}, {100 * p['diff_hi']:+.0f}] p={p['p_le0']:.2f}" if np.isfinite(p["diff"]) else "-"
                x[f"{h} s: confirmed - contradicted"] = (f"{100 * p['split']:+.1f} [{100 * p['split_lo']:+.0f}, {100 * p['split_hi']:+.0f}] p={p['split_p_le0']:.2f} "
                                                         f"(n {int(p['n_and'])}/{int(p['n_contradicted'])})") if np.isfinite(p["split"]) else "-"
            rows.append(x)
    md += ["**(c) Paired differences on the weekly grid, circular block bootstrap** (points [95 % interval], p = share of draws <= 0)", "", pd.DataFrame(rows).to_markdown(index=False), ""]
    # ---- 8 selection, bar, placebo
    md += ["## 8. Selection by the declared rule, the Round 5 bar and the timing placebo", SELECT_MD.strip(), "", r["selection"].round(3).to_markdown(index=False), "",
           f"Final: **`{final}`** - {r['final_status']}.", ""]
    B = r["bar"].copy()
    bt = pd.DataFrame({"horizon": B.h, "period": B.period, "agreement rule": [f"{100 * a:.0f} n={n} ({p:.1f}/y)" for a, n, p in zip(B.agree3_acc, B.agree3_n, B.agree3_per_year)],
                       f"AND {final}": [f"{100 * a:.0f} [{100 * lo:.0f}-{100 * hi:.0f}] n={n} ({p:.1f}/y)" if n else "-" for a, lo, hi, n, p in zip(B.and_acc, B.and_lo, B.and_hi, B.and_n, B.and_per_year)],
                       "gain (pts)": B.gain_pts.round(1), "placebo +63: acc n, gain": [f"{100 * a:.0f} n={n}, {g:+.1f}" if n else "-" for a, n, g in zip(B.placebo63_acc, B.placebo63_n, B.placebo63_gain_pts)],
                       "placebo +126: acc n, gain": [f"{100 * a:.0f} n={n}, {g:+.1f}" if n else "-" for a, n, g in zip(B.placebo126_acc, B.placebo126_n, B.placebo126_gain_pts)]})
    md += ["**The bar, cell by cell, for the final** (non-overlapping decisions)", "", bt.to_markdown(index=False), "", "Bar components: " +
           ", ".join(f"{k} = {v}" for k, v in r["bar_verdict"].items()), "",
           "**The same verdict for every candidate** (so that the selection rule cannot hide a better one)", "", r["bar_verdict_all"].to_markdown(index=False), ""]
    BA = r["bar_all"]
    rows = []
    for nm in NAMES:
        x = {"signal": nm}
        for per in ("2010-26", "2016-26"):
            for h in (21, 42):
                b = BA[(BA.signal == nm) & (BA.h == h) & (BA.period == per)].iloc[0]
                x[f"{per} {h} s: live / +63 / +126"] = f"{b.gain_pts:+.0f} / {b.placebo63_gain_pts:+.0f} / {b.placebo126_gain_pts:+.0f}"
        rows.append(x)
    md += ["**Timing placebo, all candidates: gain of the AND rule over the agreement rule in points, with the live signal and with the signal 63 / 126 sessions stale**", "",
           pd.DataFrame(rows).to_markdown(index=False), ""]
    rows = []
    for nm in NAMES:
        x = {"signal": nm}
        for h in (21, 63):
            x[f"standalone {h} s: live / +63 / +126"] = " / ".join(_fmt(_cell(V, signal=nm, rule=rl, h=h, mode="nonoverlap", period="2010-26"), ci=False)
                                                                   for rl in ("standalone", "standalone_shift+63", "standalone_shift+126"))
        rows.append(x)
    md += ["**Standalone accuracy when stale, non-overlapping, 2010-26**", "", pd.DataFrame(rows).to_markdown(index=False), "", PLACEBO_MD.strip(), ""]
    # ---- 9 stream
    rep = r["report"]
    agg = rep[rep.period.isin(["2010-2026", "2016-2026", "2023-2026", "2010-2015"])]
    piv = agg.pivot_table(index="variant", columns="period", values="sharpe", sort=False).round(2).reset_index()
    md += ["## 9. Daily stream of the final rule, incremental test", STREAM_MD.strip(), "", "**Net Sharpe of every candidate's AND-rule book (1.2 pips), and the agreement-rule book as reference**", "",
           piv.to_markdown(index=False), "", "**Final rule by year** (weekly decisions held 21 sessions)", "", r["by_year"].round(3).to_markdown(index=False), ""]
    if "incremental" in r:
        md += ["**Incremental test (meta.combine EW)**", "", r["incremental"][["combo", "period", "n", "sharpe", "t", "mean_bp"]].round(3).to_markdown(index=False), "",
               "**Daily P&L correlation of the final stream with the live streams**", "", r["corr"].round(3).to_markdown(index=False), ""]
    # ---- 10 leak checks
    L = r["leak"]
    md += ["## 10. Leak checks", LEAK_MD.strip(), "", "**(1) Labels permuted (300 draws), weekly decisions 2010-26**", "", L["shuffle"].round(3).to_markdown(index=False), ""]
    rows = []
    for nm in dict.fromkeys([final] + TONE_NAMES + ["jk_mp_6m"]):
        for rule in ("and", "standalone"):
            x = {"signal": nm, "rule": rule}
            for k, lab in ((-21, "look-ahead -21"), (0, "live"), (1, "+1"), (5, "+5"), (21, "+21")):
                rl = rule if k == 0 else f"{rule}_shift{k:+d}"
                x[lab] = " / ".join(_fmt(_cell(V, signal=nm, rule=rl, h=h, mode="nonoverlap", period="2010-26"), ci=False) for h in (21, 42))
            rows.append(x)
    md += ["**(2) Signal shifted in time, non-overlapping 2010-26, 21 / 42 sessions**", "", pd.DataFrame(rows).to_markdown(index=False), "",
           "**(2b) Truncation test** (raw data cut as a user would have held them on that date; the row must be identical)", "", L["truncation"].to_markdown(index=False), ""]
    rows = []
    for nm in TONE_NAMES:
        for per in ("2010-26", "2016-26"):
            x = {"signal": nm, "period": per}
            for h in (21, 42, 63):
                x[f"standalone {h} s: speech date / BIS posting date"] = " / ".join(_fmt(_cell(V, signal=nm, rule=rl, h=h, mode="nonoverlap", period=per), ci=False)
                                                                                   for rl in ("standalone", "standalone_postdate"))
            for h in (21, 42):
                x[f"AND {h} s: speech date / posting date"] = " / ".join(_fmt(_cell(V, signal=nm, rule=rl, h=h, mode="nonoverlap", period=per), ci=False)
                                                                        for rl in ("and", "and_postdate"))
            rows.append(x)
    md += ["**(2c) Tone signals re-dated by the BIS posting date** (non-overlapping)", "", pd.DataFrame(rows).to_markdown(index=False), ""]
    # ---- 11 current reading
    cur = r["current"]
    rows = [{"series": k, "last defined on": v["date"], "value": round(v["value"], 3)} for k, v in cur.items() if isinstance(v, dict) and "date" in v]
    md += ["## 11. The current reading", CURRENT_MD.strip(), "", pd.DataFrame(rows).to_markdown(index=False), "",
           f"Last scored document: Fed {cur['last_scored_doc']['FED']}, ECB {cur['last_scored_doc']['ECB']}. Signals on the last session of the store ({cur['signals_last_session'][:10]}): " +
           ", ".join(f"`{k}` {'n/a' if v is None else format(v, '+.3f')}" for k, v in cur["signals_last_row"].items()) + ".", ""]
    md += [TAIL_MD.strip(), ""]
    txt = "\n".join(md)
    (path or ROOT / "reports" / f"arm_{ARM}.md").write_text(txt)
    return txt


VERDICT_MD = r"""
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
"""

DATA_MD = r"""
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
"""

DICT_MD = r"""
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
"""

PRIORS_MD = r"""
A positive value is a vote for long EUR/USD. `long share` and `sign flips` describe 2010-26. The priors were declared as written in the module docstring;
two were flagged WEAK in advance (`gpr_d3m`, the two `jk_cbi_*`) and one has no prior at all (`tpu_d3m`: orientation = sign of the training-window
covariance with the 21-session forward return, refitted each year; fitted orientations: + in 2010, - in 2011-12, + in 2013-22, - in 2023-25, + in 2026).
EPUMONETARY (US monetary-policy uncertainty) is cached but was not made a candidate: no prior on its sign for the exchange rate and the budget was 12.
"""

RECON_MD = r"""
The agreement rule (sign of `cot_z52`, of `d_spread2y_20` and of the walk-forward house score all equal) rebuilt with `selective.house_score_wf` and the
selective evaluation helpers. Every cell is identical to arm N's report.
"""

STANDALONE_MD = r"""
Direction = sign of the oriented signal on every session where it is defined (and the house score exists, i.e. 2010+). Non-overlapping = greedy sequential
stream, plain Wilson interval. A no-skill caller sits at 50-52 % in these periods (base rate of up-moves 47-51 %).
"""

CONTROLS_MD = r"""
Round 7 asks whether a new signal merely restates the agreement inputs or the recent price move. Controls: `cot_z52`, `d_spread2y_20`, the walk-forward
house score, and EUR/USD's trailing 21- and 63-session returns. Orthogonalised signal = the signal minus the part an OLS fitted on rows before the test year
attributes to the controls (the signal keeps its own zero point; the house score enters from 2013; `tpu_d3m` has residuals from 2013 only, hence its
smaller n).
"""

EXTRA_MD = r"""
(a) AND rule = the agreement rule speaks and the new signal votes the same way. The gain is against the agreement rule alone on all its decisions; the
count of decisions per year is printed next to every accuracy, and the agreement rule itself has only 9.3 (21 sessions) and 5.3 (42 sessions) a year.
(b) OUTSIDE = sessions on which the three old signals do not agree; the new signal alone gives the direction. (c) Paired bootstrap on the weekly grid.
No signal extends coverage: outside the agreement every candidate is within its interval of 50 % in 2010-26 (best: `jk_cbi_3m` 57 % at 21 sessions, 50 % at
42).
"""

SELECT_MD = r"""
Declared rule: highest LOWER Wilson bound of the AND rule's 2010-15 non-overlapping 21-session accuracy among candidates with at least 6 such decisions a
year in 2010-15. All 12 are eligible; the lower bounds are 0.35-0.46, i.e. the rule separates nothing: the three tone signals, `news_lvl` and the two
3-month surprise sums are within 0.02 of each other.
"""

PLACEBO_MD = r"""
Reading: a gain that survives when the signal is 3-6 months old is a regime, not information. `tone_rel_lvl` (the final), `news_d1m`, `epu_rel_d3m` and
`jk_cbi_3m` keep or increase their "gain" when stale. `jk_cbi_6m` loses all of it in 2010-26 and about half in 2016-26, which is why it is called a lead in
the verdict and why it still fails the placebo test; `gpr_d3m` loses its 42-session gain when stale but has none at 21 sessions.
"""

STREAM_MD = r"""
Weekly tranches of each AND rule held 21 sessions (|position| <= 1), `wf.pnl_from_positions` at 1.2 pips per unit turnover, 2010-26. The final rule's book is
a subset of the agreement-rule book and inherits its record; it does not beat it.
"""

LEAK_MD = r"""
(1) With the labels permuted every rule sits at chance (shuffled mean 49-52 %). The AND rules beat the shuffle only because they inherit the agreement
rule's skill. No standalone rule beats it at 21 sessions (p 0.07-0.77); `tone_rel_lvl` standalone is just above the shuffled 95th percentile at 42 and 63
sessions on the weekly grid (55 % against 54-55 %; p 0.03-0.05), which is its 2010-15 regime effect. (2) Shifting the signal 21 sessions FORWARD in time (look-ahead)
does not produce a result the live signal lacks; shifting it 1 / 5 / 21 sessions back barely moves the slow level and leaves the change signals at chance.
(2b) The truncation test rebuilds all 12 signals from raw data cut at the date (documents published up to the day before, monthly indices by their lag,
shocks up to the day before) and reproduces the stored row exactly on all five dates. (2c) Re-dating every speech by the day BIS posted it (stricter than
the declared speech date + 1) changes nothing systematically. (3) The correlation table is in section 6: the largest correlations with the forward
return are 0.11 at 21 sessions and 0.19-0.20 at 63 (`tone_rel_lvl`, `jk_cbi_3m`); nothing is a label in disguise.
"""

CURRENT_MD = r"""
From `data/macro/text_news_tone_daily.csv` (row d = documents published up to and including d). **Context, not a vote** - the tests above give this reading
no predictive value. As of the last rows: the Fed's 90-day tone is unusually hawkish against its own history (10 scored documents, the latest being the
September minutes and a speech of 8 October; the October statement has fewer than 5 hits), the ECB's mildly so (13 scored documents to 5 November), so the
RELATIVE tone is about +1.5 z (Fed more hawkish relative to the ECB) and about 1.4 higher than three months before; the 30-day comparison is undefined after
5 November because BIS has posted no monetary Fed speech since mid-October. Under the declared prior that is a vote for a LOWER EUR/USD from the level and
the 3-month change, and a marginal vote the other way from the 1-month change. The news-sentiment and policy-surprise signals are undefined today (copies
end 2025-05 and 2025-10).
"""

TAIL_MD = r"""
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
"""


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "report":
        write_report()
        print(f"report written: reports/arm_{ARM}.md")
    else:
        pos, rep, res = run_full()
        print(res["selection"].round(3).to_string(index=False))
        print("final:", res["final"], "|", res["final_status"])
        print(res["bar"].round(3).to_string(index=False))
        print(res["bar_verdict"])
        write_report()
