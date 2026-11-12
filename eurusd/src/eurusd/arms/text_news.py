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
            texts.append(_strip_html(t[max(i, 0): j if j > 0 else len(t)]))
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
    seen = set()
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
            seen.add((r["inst"], _norm_title(r["title"])))
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
        if inst not in ("FED", "ECB") or key in seen or not isinstance(r["text"], str) or len(r["text"]) < 500:
            continue
        seen.add(key)
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
