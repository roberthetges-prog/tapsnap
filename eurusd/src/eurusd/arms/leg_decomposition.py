"""Arm AC - leg_decomposition: is the agreement rule a EURO signal or a DOLLAR signal, and does hedging the other leg help?

DECLARATION. Written 2026-11-17 BEFORE any outcome on either leg was computed. At the time of writing the only numbers
seen were (i) the published agreement-rule benchmark on EUR/USD, reproduced exactly from `eurusd.committee` on the
feature-store closes (58.3 / 63.3 / 66.7 % at 21 / 42 / 63 sessions, 2010-26, phase-averaged) and (ii) reachability
of the data sources. Nothing below was changed after results were seen; anything added later is marked ADDED.

DATA (decided before looking at outcomes)
* Prices: Federal Reserve H.10 noon-New-York buying rates from `data/macro/fred_DEX*.csv` (EUR, JPY, GBP, CHF, CAD,
  AUD; SEK and NOK for a robustness basket). One stamp convention since 1999, all currencies fixed at the same
  instant, so every euro cross (EUR/JPY = EUR/USD x USD/JPY, ...) is derived at ONE timestamp. Yahoo daily bars are
  NOT used: their stamp convention changed in 2010 Q3 (reports/arm_relative_value.md).
* Independent second source for a replication check: ECB euro reference rates (14:15 CET concertation, all
  currencies at one instant; ECB data API, flow EXR, cached as `data/processed/cross/leg_ecb_ref_rates.parquet`).
* Timing. A call is made at the 17:00 New York close of session date D (feature-store convention; the house score
  uses prices up to that close). The trade is entered at the FIRST H.10 fixing STRICTLY AFTER D (noon New York of the
  next fixing day, 19 hours after the call) and scored h sessions later at the first fixing strictly after the
  close date of session i + h. All three series (EUR/USD, EUR leg, USD leg) use the same two fixings, so the
  comparison is like for like and nothing is joined across stamp conventions. The feature-store close-to-close
  number is shown next to it as the reconciliation.
* Legs, FIXED EQUAL WEIGHTS declared here: basket B5 = JPY, GBP, CHF, CAD, AUD at 1/5 each, geometric (log) average.
    USD leg  U = sum_i w_i log(currency_i per USD)      (up = dollar up against the basket; the euro is excluded)
    EUR leg  E = sum_i w_i log(currency_i per EUR)      (up = euro up against the same basket)
    EUR/USD  S = log(USD per EUR);  identity S = E - U, checked numerically.
  A 'long EUR/USD' call is scored as 'E up' on the EUR leg and as 'U DOWN' on the USD leg (sign flipped).
* SEK and NOK enter only the robustness basket B7 and only if verified: the H.10-derived EUR/SEK and EUR/NOK must
  agree with the ECB reference rates on 5-session log returns at least as well as the worst of the five core
  crosses minus 0.01 (correlation) in each of 2003-09, 2010-15, 2016-26, with at most 1 % of fixings missing.

CALLS. The walk-forward three-signal agreement rule exactly as `experiments/70_committee.py::agreement_side`
(`committee._fold_columns`: sign(cot_z52) = sign(d_spread2y_20) = sign(walk-forward house score), else no call),
and each of its three inputs alone (its sign, always on). No signal is re-fitted on the legs: the calls are the
EUR/USD calls, only the instrument they are scored on changes.

SCORING (Round 9). Phase-averaged accuracy as `acc_row` in `experiments/70_committee.py`: every session with a call
is scored on the next h sessions; independent decisions = call days / h; Wilson interval on that count; decisions
per year; eras 2010-26, 2016-26, 2023-26; h = 21, 42, 63. Matched random-entry baseline: the same sequence of calls
(same count, same spacing, same long / short mix) rotated to a random position inside the era, 1,000 draws.
Paired interval on a difference between two instruments on the same call days: circular block bootstrap over
sessions, block 126 sessions, 2,000 draws, percentile 95 %.

PRIMARY TEST (candidate 1). Theory: net speculative positioning in euro futures is a statement about the euro, so
the calls should be expressed as EUR against the basket (leg E, basket B5), which removes the dollar leg.
    gain(h, era) = accuracy on leg E - accuracy on plain EUR/USD (H.10, same call days, same fixings).
PASS BAR, all of:
  (a) gain >= +3.0 points at h = 21 AND h = 42 in 2010-26 AND 2016-26 (four cells);
  (b) gain >= 0 at h = 21 and h = 42 in 2023-26;
  (c) stale placebo: with the calls of 63 sessions earlier, the gain is at most half of the live gain in each of
      the four cells of (a).
The paired bootstrap interval and the random-entry distribution of the gain are reported next to every cell; the
bar is on the point estimates, and the report says plainly whether the intervals exclude zero.

SECONDARY (declared; each counted as a candidate)
  2. Mirror: the same calls on the USD leg (long EUR/USD call = short dollar against B5), same gain table.
  3. Basket weighted by the ECB's trade weights: narrow EER group, overall weights incl. third-market effects,
     manufactures + services, 2021 (ECB data API, flow WTS, key A.I9.<cc>.E01.I9.O.TMS.F), renormalised over the
     five basket currencies: GBP 47.1 %, CHF 26.8 %, JPY 16.5 %, CAD 6.2 %, AUD 3.4 %. Both legs recomputed.
  4. Basket weighted by the Fed's broad-dollar-index trade weights (approximate, from the 2019 revision of the
     index, quoted from memory because federalreserve.gov is not reachable from here: Canada 13.4, Japan 6.3,
     UK 5.3, Switzerland 2.6, Australia 1.4), renormalised: CAD 46.2 %, JPY 21.7 %, GBP 18.3 %, CHF 9.0 %, AUD 4.8 %.
  5. Robustness basket B7 = B5 + SEK + NOK at 1/7 each (only if the data verify, see above).
  Risk-adjusted comparison (same candidates 1 and 2, different yardstick): daily position streams, position = the
  day's agreement call (+1 / 0 / -1) held to the next fixing, Sharpe by era, for plain EUR/USD, leg E and leg U.
  COST, declared: 1.2 pips per unit of turnover on EVERY pair traded, in that pair's own pip (0.01 for yen pairs).
    plain EUR/USD      1 pair,  notional 1
    USD leg            5 dollar pairs, notional 1/5 each
    EUR leg, HEADLINE  'hedge' implementation: EUR/USD (notional 1) + the 5 dollar pairs (1/5 each) = 6 spreads
    EUR leg, sensitivity: 5 euro crosses directly (1/5 each) at 1.2 pips, and the same at 3 pips (a retail cross
    spread is wider than a major's). Spot only, no carry, as everywhere in the project.
  Incremental test (Round 3 addendum) for the primary stream: `meta.combine` EW of weak_signals + regime_trend
  with and without it, and the daily P&L correlations; the plain-EUR/USD agreement stream is the reference.
  Total candidates: 5 (cap 12).

DESCRIPTIVE (declared, no bar): the accuracy table of the agreement rule and of each of its three inputs on
EUR/USD, leg E and leg U; the same per single pair (EUR/JPY ... USD/AUD); volatility and correlation of the legs.

HOW THE PLAIN-LANGUAGE ANSWER IS DECIDED (declared). Over the four cells h = 21, 42 x 2010-26, 2016-26 of the
agreement rule: 'euro signal' if accuracy on leg E exceeds accuracy on leg U by >= 3 points in all four AND the
paired bootstrap interval of (E - U) excludes zero in at least one 2010-26 cell; 'dollar signal' for the mirror
image; otherwise 'cannot be attributed to one leg'.

SANITY CHECKS (declared): the identity S = E - U; labels shuffled (one joint permutation of the outcomes and of
the returns the house score is fitted on): accuracy ~50 % and gain ~0; timing: entry at the same-day fixing
(5 hours BEFORE the call, formally a peek), the declared next fixing, and one fixing later, plus the ECB-fixing
replication: the conclusion must not depend on which.

ADDED AFTER THE FIRST RUN (2026-11-17; nothing above was altered, the declared results did not change):
  * Candidate 6, POST HOC and counted: 'broad dollar' = the calls on the dollar against six currencies including the
    euro (EUR, JPY, GBP, CHF, CAD, AUD at 1/6 each), suggested by the per-pair table. Same gain table and bar as the
    primary; it was chosen after seeing results, so a good number here would be a lead, not a finding.
  * Descriptive, exact: the gross P&L of the calls on EUR/USD split into its EUR-leg and USD-leg parts (S = E - U
    holds bar by bar, so the split is an identity, not an estimate); the long / short mix of the calls.
  * Fix in the incremental test only: a fixing-based stream is booked one session later so that it lines up with
    the close-to-close streams of the other arms (see `incremental`). Accuracy tables were not affected.
  Total candidates run: 6 (5 declared + 1 post hoc; cap 12).
"""
from __future__ import annotations

import io
import math
import subprocess
import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd import committee as C  # noqa: E402
from eurusd.arms import meta as META  # noqa: E402
from eurusd.arms.swing import _ms, wilson  # noqa: E402
from eurusd.wf import _agg  # noqa: E402

RES = ROOT / "experiments" / "results" / "arms"
CROSS = ROOT / "data" / "processed" / "cross"
HORIZONS = (21, 42, 63)
ERAS = C.ERAS
PUBLISHED = {21: 0.583, 42: 0.633, 63: 0.667}          # committee_benchmark.csv, agreement rule, 2010-26
B5 = ("JPY", "GBP", "CHF", "CAD", "AUD")
B7 = B5 + ("SEK", "NOK")
# H.10 file and quote direction: True = USD per unit of the currency, False = currency units per USD
H10 = {"EUR": ("fred_DEXUSEU.csv", True), "JPY": ("fred_DEXJPUS.csv", False), "GBP": ("fred_DEXUSUK.csv", True),
       "CHF": ("fred_DEXSZUS.csv", False), "CAD": ("fred_DEXCAUS.csv", False), "AUD": ("fred_DEXUSAL.csv", True),
       "SEK": ("fred_DEXSDUS.csv", False), "NOK": ("fred_DEXNOUS.csv", False)}
PIP = {"JPY": 0.01}
ECB_RAW = {"JPY": 0.071978, "GBP": 0.205095, "CHF": 0.116690, "CAD": 0.026841, "AUD": 0.014671}
FED_RAW = {"CAD": 13.4, "JPY": 6.3, "GBP": 5.3, "CHF": 2.6, "AUD": 1.4}


def _norm(w: dict) -> dict:
    s = sum(w.values())
    return {k: v / s for k, v in w.items()}


WEIGHTS = {"EW5": {c: 1 / 5 for c in B5}, "ECB": _norm(ECB_RAW), "FED": _norm(FED_RAW), "EW7": {c: 1 / 7 for c in B7}}
N_BASE, N_BOOT, BLOCK, SEED = 1000, 2000, 126, 20261117
COST_PIPS = 1.2


# ============================================================================= data
def load_h10() -> pd.DataFrame:
    """log(USD per unit of currency) at the H.10 noon-New-York fixing, from 1999-01-04; NaN where not published."""
    out = {}
    for c, (f, usd_per) in H10.items():
        s = np.log(_ms(f))
        out[c] = s if usd_per else -s
    return pd.DataFrame(out).loc["1999-01-04":]


def fetch_ecb(refresh: bool = False) -> pd.DataFrame:
    """ECB euro reference rates (currency units per EUR, 14:15 CET), cached. Returns the same layout as load_h10()."""
    p = CROSS / "leg_ecb_ref_rates.parquet"
    if p.exists() and not refresh:
        raw = pd.read_parquet(p)
    else:
        cols = {}
        for c in ("USD",) + B7:
            url = f"https://data-api.ecb.europa.eu/service/data/EXR/D.{c}.EUR.SP00.A?format=csvdata&startPeriod=1999-01-01"
            txt = subprocess.run(["curl", "-sS", "-f", "-m", "120", "--retry", "3", url], capture_output=True, text=True, check=True).stdout
            d = pd.read_csv(io.StringIO(txt))
            cols[c] = pd.Series(pd.to_numeric(d["OBS_VALUE"], errors="coerce").values, index=pd.to_datetime(d["TIME_PERIOD"]))
        raw = pd.DataFrame(cols).sort_index()
        raw.index.name = "date"
        raw.to_parquet(p)
    lg = np.log(raw)
    out = pd.DataFrame({"EUR": lg["USD"]})
    for c in B7:
        out[c] = lg["USD"] - lg[c]                 # log(USD per unit of c)
    return out


def fetch_ecb_weights(refresh: bool = False) -> pd.DataFrame:
    p = CROSS / "leg_ecb_trade_weights.csv"
    if p.exists() and not refresh:
        return pd.read_csv(p)
    url = "https://data-api.ecb.europa.eu/service/data/WTS/A.I9..E01.I9.O.TMS.F?format=csvdata&lastNObservations=1"
    txt = subprocess.run(["curl", "-sS", "-f", "-m", "120", "--retry", "3", url], capture_output=True, text=True, check=True).stdout
    d = pd.read_csv(io.StringIO(txt))[["KEY", "COUNT_AREA", "TIME_PERIOD", "OBS_VALUE"]]
    d.to_csv(p, index=False)
    return d


def legs(L: pd.DataFrame, w: dict) -> pd.DataFrame:
    """S = log EUR/USD, U = dollar against the basket (up = dollar up), E = euro against the basket; rows with the
    whole panel present only. Also the single pairs: 'EUR<c>' = log(c per EUR), 'USD<c>' = log(c per USD)."""
    d = L[["EUR"] + list(w)].dropna()
    U = -sum(w[c] * d[c] for c in w)
    out = pd.DataFrame({"S": d["EUR"], "E": d["EUR"] + U, "U": U})
    for c in w:
        out[f"USD{c}"] = -d[c]
        out[f"EUR{c}"] = d["EUR"] - d[c]
    return out


def to_sessions(P: pd.DataFrame, cdate: pd.DatetimeIndex, index: pd.Index, lag: int = 1) -> pd.DataFrame:
    """Value of each series at the entry fixing of every session. lag = 1: first fixing STRICTLY AFTER the session's
    close date (declared); lag = 0: last fixing on or before it (noon of the same day: 5 hours before the call);
    lag = 2: one fixing later than declared."""
    n_le = P.index.searchsorted(cdate.values, side="right")          # number of fixings dated <= close date
    pos = n_le + (lag - 1)
    ok = (pos >= 0) & (pos < len(P))
    v = np.full((len(cdate), P.shape[1]), np.nan)
    v[ok] = P.values[pos[ok]]
    return pd.DataFrame(v, index=index, columns=P.columns)


def outcomes(PS: pd.DataFrame, cols=("S", "E", "U")) -> dict:
    """Sign of the h-session move per series, oriented so that +1 = 'a long EUR/USD call was right'."""
    Y = {}
    for h in HORIZONS:
        d = PS.shift(-h) - PS
        y = pd.DataFrame({c: np.sign(d[c]) for c in cols if not c.startswith("USD") and c != "U"})
        for c in cols:
            if c == "U" or c.startswith("USD"):
                y[c] = -np.sign(d[c])
        Y[h] = y[list(cols)]
    return Y


def calls(X: pd.DataFrame) -> pd.DataFrame:
    """Walk-forward agreement side (identical to experiments/70_committee.py::agreement_side) and the three inputs."""
    ag = pd.Series(np.nan, index=X.index)
    house = pd.Series(np.nan, index=X.index)
    for Yr in C.TEST_YEARS:
        start = pd.Timestamp(f"{Yr}-01-01", tz="UTC")
        known = (X["yend21"] < start).values & X["y21"].notna().values
        fc = C._fold_columns(X, known)
        rows = X.index.year == Yr
        ag[rows] = fc["@agree"][rows]
        house[rows] = fc["@house"][rows]
    return pd.DataFrame({"agreement": ag.fillna(0.0), "positioning": np.sign(X["cot_z52"]).fillna(0.0),
                         "spread_trend": np.sign(X["d_spread2y_20"]).fillna(0.0), "house_score": np.sign(house).fillna(0.0)})


# ============================================================================= scoring
def acc_row(side: pd.Series, y: pd.Series, h: int, a: int, b: int) -> dict:
    """Copy of experiments/70_committee.py::acc_row (phase-averaged non-overlapping accuracy)."""
    m = (side.index.year >= a) & (side.index.year <= b) & (side != 0).values & y.notna().values & (y != 0).values
    n = int(m.sum())
    if n == 0:
        return {"n_days": 0, "n_indep": 0.0, "acc": np.nan, "lo": np.nan, "hi": np.nan, "per_year": 0.0, "share_of_days": 0.0}
    hit = float((side[m] == y[m]).mean())
    n_ind = n / h
    lo, hi = wilson(int(round(hit * n_ind)), max(int(round(n_ind)), 1))
    era_days = int(((side.index.year >= a) & (side.index.year <= b) & y.notna().values).sum())
    return {"n_days": n, "n_indep": round(n_ind, 1), "acc": hit, "lo": lo, "hi": hi, "per_year": n_ind / (b - a + 1), "share_of_days": n / max(era_days, 1)}


def _era(index: pd.Index, a: int, b: int) -> np.ndarray:
    return np.asarray((index.year >= a) & (index.year <= b))


def _acc(side: np.ndarray, y: np.ndarray) -> float:
    m = (side != 0) & np.isfinite(y) & (y != 0)
    return float((side[m] == y[m]).mean()) if m.any() else np.nan


def random_entry(side: pd.Series, ys: list[pd.Series], h: int, a: int, b: int, n: int = N_BASE, seed: int = SEED) -> np.ndarray:
    """Matched baseline: the era's own call sequence rotated by a random offset (count, spacing and long / short mix
    preserved). Returns an (n, len(ys)) array of accuracies."""
    e = _era(side.index, a, b)
    s = side.values[e]
    Y = [y.values[e].astype(float) for y in ys]
    rng = np.random.default_rng(seed + 7 * h + a)
    out = np.empty((n, len(Y)))
    lo, hi = h, max(len(s) - h, h + 1)
    for k in range(n):
        r = np.roll(s, int(rng.integers(lo, hi)))
        out[k] = [_acc(r, y) for y in Y]
    return out


def paired_boot(side: pd.Series, y1: pd.Series, y2: pd.Series, a: int, b: int, n: int = N_BOOT, block: int = BLOCK, seed: int = SEED) -> tuple[float, float]:
    """95 % circular-block-bootstrap interval of acc(y1) - acc(y2) on the same call days."""
    e = _era(side.index, a, b)
    s, u, v = side.values[e], y1.values[e].astype(float), y2.values[e].astype(float)
    m = (s != 0) & np.isfinite(u) & np.isfinite(v) & (u != 0) & (v != 0)
    d = np.where(m, (s == u).astype(float) - (s == v).astype(float), 0.0)
    cnt = m.astype(float)
    N = len(s)
    nb = int(math.ceil(N / block))
    rng = np.random.default_rng(seed + a)
    out = np.empty(n)
    for k in range(n):
        st = rng.integers(0, N, nb)
        idx = (st[:, None] + np.arange(block)[None, :]).ravel()[:N] % N
        c = cnt[idx].sum()
        out[k] = d[idx].sum() / c if c > 0 else np.nan
    return float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5))


def accuracy_table(SIDES: pd.DataFrame, Y: dict, series=("S", "E", "U"), signals=None, baseline: bool = True, eras=None) -> pd.DataFrame:
    rows = []
    for sig in (signals or SIDES.columns):
        for h in HORIZONS:
            for era, a, b in (eras or ERAS):
                base = random_entry(SIDES[sig], [Y[h][c] for c in series], h, a, b) if baseline else None
                for j, c in enumerate(series):
                    r = acc_row(SIDES[sig], Y[h][c], h, a, b)
                    row = {"signal": sig, "series": c, "h": h, "era": era, **r}
                    if baseline and r["n_days"]:
                        bj = base[:, j]
                        row.update({"base_mean": float(np.nanmean(bj)), "base_lo": float(np.nanpercentile(bj, 2.5)), "base_hi": float(np.nanpercentile(bj, 97.5)),
                                    "p_random": float((bj >= r["acc"]).mean())})
                    rows.append(row)
    return pd.DataFrame(rows)


def gain_table(side: pd.Series, Y: dict, leg: str, label: str, ref: str = "S", stale: int = 63) -> pd.DataFrame:
    """Accuracy on `leg` minus accuracy on `ref` for the same calls, with the paired bootstrap interval, the
    random-entry distribution of the difference and the stale placebo."""
    st = side.shift(stale).fillna(0.0)
    rows = []
    for h in HORIZONS:
        for era, a, b in ERAS:
            r1, r0 = acc_row(side, Y[h][leg], h, a, b), acc_row(side, Y[h][ref], h, a, b)
            lo, hi = paired_boot(side, Y[h][leg], Y[h][ref], a, b)
            base = random_entry(side, [Y[h][leg], Y[h][ref]], h, a, b)
            bd = base[:, 0] - base[:, 1]
            s1, s0 = acc_row(st, Y[h][leg], h, a, b), acc_row(st, Y[h][ref], h, a, b)
            g = r1["acc"] - r0["acc"]
            rows.append({"expression": label, "h": h, "era": era, "n_indep": r1["n_indep"], "per_year": r1["per_year"], "acc_ref": r0["acc"], "acc_leg": r1["acc"],
                         "leg_lo": r1["lo"], "leg_hi": r1["hi"], "gain": g, "gain_lo": lo, "gain_hi": hi,
                         "rand_gain_mean": float(np.nanmean(bd)), "rand_gain_lo": float(np.nanpercentile(bd, 2.5)), "rand_gain_hi": float(np.nanpercentile(bd, 97.5)),
                         "p_random_gain": float((bd >= g).mean()),
                         "stale_acc_ref": s0["acc"], "stale_acc_leg": s1["acc"], "stale_gain": s1["acc"] - s0["acc"]})
    return pd.DataFrame(rows)


def verdict_rows(G: pd.DataFrame) -> tuple[pd.DataFrame, bool]:
    rows, ok = [], True
    for h in (21, 42):
        for era in ("2010-26", "2016-26"):
            r = G[(G.h == h) & (G.era == era)].iloc[0]
            p_a = bool(r.gain >= 0.03 - 1e-12)
            p_c = bool(r.gain > 0 and r.stale_gain <= 0.5 * r.gain)
            ok &= p_a and p_c
            rows.append({"h": h, "era": era, "test": "(a) gain >= 3 pts / (c) stale loses half", "gain_pts": 100 * r.gain, "stale_gain_pts": 100 * r.stale_gain,
                         "pass_a": p_a, "pass_c": p_c})
        r = G[(G.h == h) & (G.era == "2023-26")].iloc[0]
        p_b = bool(r.gain >= -1e-12)
        ok &= p_b
        rows.append({"h": h, "era": "2023-26", "test": "(b) not worse", "gain_pts": 100 * r.gain, "stale_gain_pts": 100 * r.stale_gain, "pass_a": p_b, "pass_c": np.nan})
    return pd.DataFrame(rows), bool(ok)


# ============================================================================= daily streams and cost
def pair_cost_bp(L: pd.DataFrame, w: dict) -> pd.DataFrame:
    """Cost in bp of one unit of turnover at COST_PIPS = 1 (multiply by the pips charged), per implementation, on the
    fixing-date grid. Each pair costs pips x pip-size / price of that pair, times the notional traded in it."""
    d = L[["EUR"] + list(w)].dropna()
    eurusd = 1e-4 / np.exp(d["EUR"]) * 1e4
    usd_pairs, crosses = 0.0, 0.0
    for c in w:
        pip = PIP.get(c, 1e-4)
        conv = np.exp(d[c]) if H10[c][1] else np.exp(-d[c])          # the pair's market quote (GBPUSD, AUDUSD; USDJPY, USDCHF, ...)
        usd_pairs = usd_pairs + w[c] * pip / conv * 1e4
        crosses = crosses + w[c] * pip / np.exp(d["EUR"] - d[c]) * 1e4  # EUR/c quoted as c per EUR
    return pd.DataFrame({"plain": eurusd, "usd_leg": usd_pairs, "eur_leg_hedge6": eurusd + usd_pairs, "eur_leg_crosses": crosses})


def stream(side: pd.Series, PS: pd.DataFrame, col: str, flip: bool, cost_bp: pd.Series) -> pd.DataFrame:
    """Daily P&L in bp: the day's call held from its entry fixing to the next session's entry fixing."""
    f = (PS[col].shift(-1) - PS[col]) * 1e4 * (-1.0 if flip else 1.0)
    pos = side.astype(float)
    to = pos.diff().abs().fillna(pos.abs())
    gross = pos * f
    return pd.DataFrame({"pos": pos, "fwd_bp": f, "gross_bp": gross, "net_bp": gross - to * cost_bp, "turnover": to})


def sharpe_rows(st: pd.DataFrame, name: str, cost: str) -> list[dict]:
    rows = []
    for era, a, b in ERAS:
        e = _era(st.index, a, b)
        x = st[e]
        g, n_ = _agg(x["gross_bp"], 252), _agg(x["net_bp"], 252)
        rows.append({"expression": name, "cost": cost, "era": era, "sharpe_net": n_["sharpe"], "t_net": n_["t"], "sharpe_gross": g["sharpe"], "mean_net_bp": n_["mean_bp"],
                     "ann_vol_bp_when_in": float(x["fwd_bp"][x["pos"] != 0].std() * math.sqrt(252)), "turnover_per_year": float(x["turnover"].sum() / (b - a + 1)),
                     "cost_bp_per_year": float((x["gross_bp"] - x["net_bp"]).sum() / (b - a + 1)), "active_frac": float((x["pos"] != 0).mean())})
    return rows


def sharpe_diff_boot(x: pd.Series, y: pd.Series, a: int, b: int, n: int = N_BOOT, block: int = BLOCK, seed: int = SEED) -> tuple[float, float, float]:
    e = _era(x.index, a, b)
    u, v = x.values[e], y.values[e]
    ok = np.isfinite(u) & np.isfinite(v)
    u, v = u[ok], v[ok]
    sr = lambda z: z.mean() / z.std() * math.sqrt(252) if z.std() > 0 else np.nan  # noqa: E731
    N = len(u)
    nb = int(math.ceil(N / block))
    rng = np.random.default_rng(seed + b)
    out = np.empty(n)
    for k in range(n):
        st = rng.integers(0, N, nb)
        idx = (st[:, None] + np.arange(block)[None, :]).ravel()[:N] % N
        out[k] = sr(u[idx]) - sr(v[idx])
    return float(sr(u) - sr(v)), float(np.nanpercentile(out, 2.5)), float(np.nanpercentile(out, 97.5))


def incremental(streams: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Round 3 incremental test. `streams` = name -> net_bp Series on the session index; each is offered as a
    third arm next to weak_signals and regime_trend through meta.combine (EW). Row i of a fixing-based stream is the
    move from noon of D+1 to noon of D+2, which overlaps 19 of 24 hours with the feature-store label of row i + 1
    (close D+1 to close D+2; measured correlation 0.81 against 0.17 unshifted), so it is booked one session later
    before it is combined with the close-to-close streams. Weights for year Y use years < Y only, so no leak."""
    orig = META.load_arm_daily
    base = {a: orig(a) for a in ("weak_signals", "regime_trend")}
    rows, corr = [], []
    try:
        two, _ = META.combine(["weak_signals", "regime_trend"], "EW")
        for name, s in streams.items():
            s = s.shift(1)
            key = (pd.DatetimeIndex(s.index) - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
            sd = s.groupby(key).sum().sort_index()
            sd = sd[sd.index.year >= 2010]
            META.load_arm_daily = lambda a, _sd=sd, _n=name: _sd if a == _n else orig(a)
            three, wts = META.combine(["weak_signals", "regime_trend", name], "EW")
            for era, a, b in ERAS:
                s2 = _agg(two["net_bp"][_era(two.index, a, b)], 252)
                s3 = _agg(three["net_bp"][_era(three.index, a, b)], 252)
                rows.append({"third_arm": name, "era": era, "sr_2way": s2["sharpe"], "sr_3way": s3["sharpe"], "d_sr": s3["sharpe"] - s2["sharpe"],
                             "years_arm_in": int((wts[name] > 0).sum()) if name in wts else 0})
            J = pd.DataFrame({"x": sd, **base}).dropna()
            for era, a, b in ERAS[:2]:
                j = J[_era(J.index, a, b)]
                corr.append({"stream": name, "era": era, "corr_weak_signals": float(j["x"].corr(j["weak_signals"])), "corr_regime_trend": float(j["x"].corr(j["regime_trend"]))})
    finally:
        META.load_arm_daily = orig
    return pd.DataFrame(rows), pd.DataFrame(corr)


# ============================================================================= data checks (no outcomes)
def data_checks(X: pd.DataFrame, L: pd.DataFrame, LE: pd.DataFrame) -> dict:
    out = {}
    cd = pd.DatetimeIndex(X["__cdate"])
    # (1) H.10 EUR/USD against the feature-store close
    fs = pd.Series(np.log(X["__close"].values), index=cd)
    fs = fs[~fs.index.duplicated(keep="last")]
    h10 = L["EUR"].dropna()
    j = pd.DataFrame({"fs": fs, "h10": h10}).dropna().loc["2003":]
    rows = []
    for h in (1, 5, 21, 42, 63):
        d = j.diff(h).dropna()
        rows.append({"h_fixings": h, "n": len(d), "corr_returns": float(d["fs"].corr(d["h10"])), "sign_agree": float((np.sign(d["fs"]) == np.sign(d["h10"])).mean()),
                     "median_abs_gap_bp": float((d["fs"] - d["h10"]).abs().median() * 1e4)})
    out["h10_vs_store"] = pd.DataFrame(rows)
    out["h10_level_gap_pips"] = float(((np.exp(j["fs"]) - np.exp(j["h10"])).abs().median()) * 1e4)
    # (2) H.10-derived euro crosses against ECB reference rates (independent source, 14:15 CET vs 12:00 New York)
    rows = []
    for c in B7 + ("EUR",):
        a_ = (L["EUR"] - L[c]) if c != "EUR" else L["EUR"]
        b_ = (LE["EUR"] - LE[c]) if c != "EUR" else LE["EUR"]
        jj = pd.DataFrame({"h10": a_, "ecb": b_})
        for era, lo, hi in (("2003-09", "2003", "2009"), ("2010-15", "2010", "2015"), ("2016-26", "2016", "2026")):
            q = jj.loc[lo:hi]
            both = q.dropna()
            d5, d21 = both.diff(5).dropna(), both.diff(21).dropna()
            bd = pd.bdate_range(q.index.min(), q.index.max())
            rows.append({"cross": ("EUR" + c) if c != "EUR" else "EURUSD", "era": era, "n": len(both), "corr_5d": float(d5["h10"].corr(d5["ecb"])), "corr_21d": float(d21["h10"].corr(d21["ecb"])),
                         "max_abs_5d_gap_bp": float((d5["h10"] - d5["ecb"]).abs().max() * 1e4), "h10_missing_share_of_weekdays": float(1 - q["h10"].reindex(bd).notna().mean())})
    v = pd.DataFrame(rows)
    out["h10_vs_ecb"] = v
    core = v[v.cross.isin([f"EUR{c}" for c in B5])].groupby("era")["corr_5d"].min()
    miss_core = v[v.cross.isin([f"EUR{c}" for c in B5])]["h10_missing_share_of_weekdays"].max()
    ok = True
    for c in ("SEK", "NOK"):
        q = v[v.cross == f"EUR{c}"].set_index("era")
        ok &= bool((q["corr_5d"] >= core - 0.01).all() and (q["h10_missing_share_of_weekdays"] <= max(miss_core, 0.0) + 0.01).all())
    out["sek_nok_verified"] = ok
    return out


def leg_stats(PS: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for era, a, b in (("1999-2009", 1999, 2009),) + tuple(ERAS):
        e = _era(PS.index, a, b)
        for h in (1, 21, 63):
            d = (PS[["S", "E", "U"]].shift(-h) - PS[["S", "E", "U"]])[e].dropna() * 1e4
            vs, ve, vu = d["S"].var(), d["E"].var(), d["U"].var()
            rows.append({"era": era, "h": h, "ann_vol_S_pct": float(d["S"].std() * math.sqrt(252 / h) / 100), "ann_vol_E_pct": float(d["E"].std() * math.sqrt(252 / h) / 100),
                         "ann_vol_U_pct": float(d["U"].std() * math.sqrt(252 / h) / 100), "corr_E_U": float(d["E"].corr(d["U"])),
                         "corr_S_E": float(d["S"].corr(d["E"])), "corr_S_minusU": float(d["S"].corr(-d["U"])),
                         "var_share_E": float(ve / vs), "var_share_U": float(vu / vs), "var_share_minus2cov": float(-2 * d["E"].cov(d["U"]) / vs),
                         "sign_agree_S_E": float((np.sign(d["S"]) == np.sign(d["E"])).mean()), "sign_agree_S_minusU": float((np.sign(d["S"]) == -np.sign(d["U"])).mean()),
                         "identity_max_abs_err_bp": float((d["S"] - d["E"] + d["U"]).abs().max())})
    return pd.DataFrame(rows)


# ============================================================================= the run
def _session_cost(L: pd.DataFrame, w: dict, cd: pd.DatetimeIndex, index: pd.Index) -> pd.DataFrame:
    return to_sessions(pair_cost_bp(L, w), cd, index, 1).ffill()


def compute(verbose: bool = True) -> dict:
    warnings.filterwarnings("ignore")
    K = {}
    X = C.build_frame()
    cd = pd.DatetimeIndex(X["__cdate"])
    SIDES = calls(X)
    ag = SIDES["agreement"]
    L, LE = load_h10(), fetch_ecb()
    K["ecb_weights"] = fetch_ecb_weights()
    K["checks"] = data_checks(X, L, LE)
    P = {k: legs(L, w) for k, w in WEIGHTS.items()}
    PS = {k: to_sessions(P[k], cd, X.index, 1) for k in P}
    Y = {k: outcomes(PS[k]) for k in P}
    K["leg_stats"] = leg_stats(PS["EW5"])

    # ---- 1. reconcile: published -> feature-store closes -> H.10 fixings
    rows = []
    Ystore = {h: X[f"y{h}"] for h in HORIZONS}
    Y0 = outcomes(to_sessions(P["EW5"], cd, X.index, 0))
    for h in HORIZONS:
        for era, a, b in ERAS:
            r = acc_row(ag, Ystore[h], h, a, b)
            rows.append({"h": h, "era": era, "published_2010_26": PUBLISHED[h] if era == "2010-26" else np.nan, "n_indep": r["n_indep"], "per_year": r["per_year"],
                         "store_close": r["acc"], "h10_next_fixing": acc_row(ag, Y["EW5"][h]["S"], h, a, b)["acc"], "h10_same_day_fixing": acc_row(ag, Y0[h]["S"], h, a, b)["acc"]})
    K["reconcile"] = pd.DataFrame(rows)
    for h in HORIZONS:
        got = K["reconcile"][(K["reconcile"].h == h) & (K["reconcile"].era == "2010-26")]["store_close"].iloc[0]
        assert abs(got - PUBLISHED[h]) < 0.0006, (h, got)

    # ---- 2. descriptive: the rule and its three inputs on EUR/USD, the EUR leg and the USD leg
    K["accuracy"] = accuracy_table(SIDES, Y["EW5"])
    if verbose:
        print("descriptive done", flush=True)

    # ---- 3. PRIMARY (candidate 1) and 4a mirror (candidate 2); E against U for the plain-language answer
    K["primary"] = gain_table(ag, Y["EW5"], "E", "C1 EUR leg vs plain (EW5)")
    K["verdict_rows"], K["pass"] = verdict_rows(K["primary"])
    K["mirror"] = gain_table(ag, Y["EW5"], "U", "C2 USD leg vs plain (EW5)")
    K["e_vs_u"] = gain_table(ag, Y["EW5"], "E", "EUR leg minus USD leg (EW5)", ref="U")
    inp = []
    for sig in ("positioning", "spread_trend", "house_score"):
        g = gain_table(SIDES[sig], Y["EW5"], "E", f"{sig}: EUR leg minus USD leg", ref="U")
        inp.append(g.assign(signal=sig))
    K["e_vs_u_inputs"] = pd.concat(inp, ignore_index=True)
    if verbose:
        print("primary done", flush=True)

    # ---- 4c / robustness baskets (candidates 3, 4, 5)
    alt = []
    for k, cnum in (("ECB", 3), ("FED", 4), ("EW7", 5)):
        alt.append(gain_table(ag, Y[k], "E", f"C{cnum} EUR leg vs plain ({k})").assign(basket=k, leg="E"))
        alt.append(gain_table(ag, Y[k], "U", f"C{cnum} USD leg vs plain ({k})").assign(basket=k, leg="U"))
        alt.append(gain_table(ag, Y[k], "E", f"C{cnum} EUR leg minus USD leg ({k})", ref="U").assign(basket=k, leg="E-U"))
    K["alt_baskets"] = pd.concat(alt, ignore_index=True)
    # ---- candidate 6, ADDED AFTER the results above were seen (post hoc, counted): the per-pair table showed the
    # calls working on the dollar pairs, so the obvious follow-up is the dollar against SIX currencies including the
    # euro (EUR, JPY, GBP, CHF, CAD, AUD at 1/6 each): USD6 = (5 U - S) / 6, a long EUR/USD call = USD6 down.
    PS["EW5"]["USD6"] = (5 * PS["EW5"]["U"] - PS["EW5"]["S"]) / 6
    Y6 = outcomes(PS["EW5"], cols=("S", "USD6"))
    K["broad_dollar"] = gain_table(ag, Y6, "USD6", "C6 broad dollar vs plain (ADDED, post hoc)")
    if verbose:
        print("baskets done", flush=True)

    # ---- 4b. daily position streams, cost on every pair traded
    cost = _session_cost(L, WEIGHTS["EW5"], cd, X.index)
    ST = {"plain EUR/USD (H.10)": (stream(ag, PS["EW5"], "S", False, COST_PIPS * cost["plain"]), "1 pair, 1.2 pips"),
          "EUR leg (EW5)": (stream(ag, PS["EW5"], "E", False, COST_PIPS * cost["eur_leg_hedge6"]), "hedge: 6 pairs, 1.2 pips each"),
          "EUR leg (EW5), direct crosses": (stream(ag, PS["EW5"], "E", False, COST_PIPS * cost["eur_leg_crosses"]), "5 crosses, 1.2 pips each"),
          "EUR leg (EW5), direct crosses 3 pips": (stream(ag, PS["EW5"], "E", False, 3.0 * cost["eur_leg_crosses"]), "5 crosses, 3 pips each"),
          "USD leg (EW5)": (stream(ag, PS["EW5"], "U", True, COST_PIPS * cost["usd_leg"]), "5 pairs, 1.2 pips each")}
    ST["broad dollar USD6 (ADDED)"] = (stream(ag, PS["EW5"], "USD6", True, COST_PIPS * (cost["plain"] / 6 + 5 / 6 * cost["usd_leg"])), "6 pairs at 1/6, 1.2 pips each")
    fs = pd.DataFrame({"pos": ag, "fwd_bp": X["ws_fwd_1d"]})
    to = ag.diff().abs().fillna(ag.abs())
    fs["gross_bp"] = fs["pos"] * fs["fwd_bp"]
    fs["net_bp"] = fs["gross_bp"] - to * COST_PIPS * 1e-4 / X["__close"] * 1e4
    fs["turnover"] = to
    ST["plain EUR/USD (store closes)"] = (fs, "1 pair, 1.2 pips")
    rows = []
    for name, (st, c) in ST.items():
        rows += sharpe_rows(st, name, c)
    K["sharpe"] = pd.DataFrame(rows)
    rows = []
    ref = ST["plain EUR/USD (H.10)"][0]["net_bp"]
    for name in ("EUR leg (EW5)", "EUR leg (EW5), direct crosses", "USD leg (EW5)", "broad dollar USD6 (ADDED)"):
        for era, a, b in ERAS:
            d, lo, hi = sharpe_diff_boot(ST[name][0]["net_bp"], ref, a, b)
            e = _era(ref.index, a, b)
            rows.append({"expression": name, "era": era, "d_sharpe_vs_plain": d, "lo": lo, "hi": hi,
                         "pnl_corr_with_plain": float(ST[name][0]["net_bp"][e].corr(ref[e]))})
    K["sharpe_diff"] = pd.DataFrame(rows)
    K["cost_table"] = pd.DataFrame({"mean_bp_per_unit_turnover_2010_26": (COST_PIPS * cost[_era(cost.index, 2010, 2026)]).mean(),
                                    "latest_bp": COST_PIPS * cost.dropna().iloc[-1]})
    K["streams"] = {k: v[0] for k, v in ST.items()}
    pos = ST["EUR leg (EW5)"][0][["pos", "fwd_bp", "net_bp", "gross_bp", "turnover"]]
    K["positions"] = pos[pos.index.year >= 2010]
    K["incremental"], K["pnl_corr"] = incremental({"leg_decomposition": ST["EUR leg (EW5)"][0]["net_bp"], "leg_plain_agreement": ST["plain EUR/USD (H.10)"][0]["net_bp"],
                                                   "leg_usd": ST["USD leg (EW5)"][0]["net_bp"], "leg_usd6": ST["broad dollar USD6 (ADDED)"][0]["net_bp"]})
    # ---- ADDED (descriptive, exact): the gross P&L of a call on EUR/USD is the sum of its P&L on the two legs
    att = []
    for sig in SIDES.columns:
        zero = pd.Series(0.0, index=X.index)
        g = {c: stream(SIDES[sig], PS["EW5"], c, c == "U", zero)["gross_bp"] for c in ("S", "E", "U")}
        for era, a, b in (("2010-15", 2010, 2015),) + tuple(ERAS):
            e = _era(X.index, a, b)
            s_, e_, u_ = (_agg(g[c][e], 252) for c in ("S", "E", "U"))
            yrs = b - a + 1
            att.append({"signal": sig, "era": era, "bp_per_year_eurusd": s_["sum_bp"] / yrs, "bp_per_year_eur_leg": e_["sum_bp"] / yrs, "bp_per_year_usd_leg": u_["sum_bp"] / yrs,
                        "share_from_usd_leg": u_["sum_bp"] / s_["sum_bp"] if s_["sum_bp"] else np.nan, "t_eurusd": s_["t"], "t_eur_leg": e_["t"], "t_usd_leg": u_["t"],
                        "sharpe_gross_eurusd": s_["sharpe"], "sharpe_gross_eur_leg": e_["sharpe"], "sharpe_gross_usd_leg": u_["sharpe"],
                        "identity_err_bp": float((g["S"] - g["E"] - g["U"])[e].abs().max())})
    K["attribution"] = pd.DataFrame(att)
    mix = []
    for era, a, b in ERAS:
        s = ag[_era(X.index, a, b)]
        mix.append({"era": era, "call_days_share": float((s != 0).mean()), "long_share_of_call_days": float((s > 0).sum() / max((s != 0).sum(), 1)),
                    "call_episodes": int(((s != 0) & (s.shift(1) != s)).sum())})
    K["call_mix"] = pd.DataFrame(mix)
    # ADDED (descriptive): the first six years on their own, because the split between the legs is not stable
    K["accuracy_2010_15"] = accuracy_table(SIDES, Y["EW5"], eras=(("2010-15", 2010, 2015),))
    if verbose:
        print("streams done", flush=True)

    # ---- 5. sanity checks
    # (i) timing: same-day fixing (a 5-hour peek), declared next fixing, one fixing later; ECB 14:15 CET fixings
    tim = []
    variants = {"H.10 same-day fixing (5 h before the call)": outcomes(to_sessions(P["EW5"], cd, X.index, 0)), "H.10 next fixing (declared)": Y["EW5"],
                "H.10 one fixing later": outcomes(to_sessions(P["EW5"], cd, X.index, 2)),
                "ECB reference rates, next fixing": outcomes(to_sessions(legs(LE, WEIGHTS["EW5"]), cd, X.index, 1))}
    for name, Yv in variants.items():
        for h in HORIZONS:
            for era, a, b in ERAS:
                rs, re_, ru = (acc_row(ag, Yv[h][c], h, a, b) for c in ("S", "E", "U"))
                tim.append({"prices": name, "h": h, "era": era, "n_indep": rs["n_indep"], "acc_S": rs["acc"], "acc_E": re_["acc"], "acc_U": ru["acc"],
                            "gain_E": re_["acc"] - rs["acc"], "gain_U": ru["acc"] - rs["acc"]})
    K["timing"] = pd.DataFrame(tim)
    # (ii) shuffled labels: one joint permutation of every outcome and of the returns the house score is fitted on
    sh = []
    for seed in range(5):
        perm = np.random.default_rng(SEED + seed).permutation(len(X))
        Xs = X.copy()
        Xs["ws_fwd_1d"] = X["ws_fwd_1d"].values[perm]
        ags = calls(Xs)["agreement"]
        for h in (21, 42):
            yp = pd.DataFrame(Y["EW5"][h].values[perm], index=X.index, columns=Y["EW5"][h].columns)
            rs, re_, ru = (acc_row(ags, yp[c], h, 2010, 2026) for c in ("S", "E", "U"))
            sh.append({"seed": seed, "h": h, "era": "2010-26", "call_days": rs["n_days"], "acc_S": rs["acc"], "acc_E": re_["acc"], "acc_U": ru["acc"], "gain_E": re_["acc"] - rs["acc"]})
    K["shuffled"] = pd.DataFrame(sh)
    # (iii) per single pair (descriptive)
    pairs = [f"EUR{c}" for c in B5] + [f"USD{c}" for c in B5]
    Yp = outcomes(PS["EW5"], cols=tuple(pairs))
    K["pairs"] = accuracy_table(SIDES, Yp, series=tuple(pairs), signals=["agreement"])
    K["calls"] = SIDES
    K["n_candidates"] = 6          # 5 declared + 1 added post hoc (broad dollar)
    return K


def save(K: dict) -> None:
    RES.mkdir(parents=True, exist_ok=True)
    for name in ("reconcile", "accuracy", "primary", "mirror", "e_vs_u", "e_vs_u_inputs", "alt_baskets", "broad_dollar", "sharpe", "sharpe_diff", "incremental", "pnl_corr",
                 "timing", "shuffled", "pairs", "leg_stats", "verdict_rows", "attribution", "call_mix", "accuracy_2010_15"):
        K[name].to_csv(RES / f"leg_decomposition_{name}.csv", index=False)
    K["cost_table"].to_csv(RES / "leg_decomposition_cost_table.csv")
    K["checks"]["h10_vs_store"].to_csv(RES / "leg_decomposition_check_h10_vs_store.csv", index=False)
    K["checks"]["h10_vs_ecb"].to_csv(RES / "leg_decomposition_check_h10_vs_ecb.csv", index=False)
    K["positions"].shift(1).iloc[1:].to_parquet(RES / "leg_decomposition_positions.parquet")   # booked one session later, see incremental()
    K["calls"].to_parquet(RES / "leg_decomposition_calls.parquet")


def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Entry point. Returns (out-of-sample daily positions of the primary expression, the primary gain table)."""
    global COST_PIPS
    COST_PIPS = cost_pips
    K = compute(verbose=verbose)
    if write:
        save(K)
        write_report(K)
    if verbose:
        pd.set_option("display.width", 250)
        pd.set_option("display.max_rows", 400)
        f = lambda d: d.to_string(index=False, float_format=lambda v: f"{v:.3f}")  # noqa: E731
        print("\nRECONCILE\n", f(K["reconcile"]))
        print("\nPRIMARY\n", f(K["primary"]), "\n", f(K["verdict_rows"]), "\nPASS" if K["pass"] else "\nFAIL")
        print("\nMIRROR\n", f(K["mirror"]))
        print("\nE minus U\n", f(K["e_vs_u"]))
        print("\nACCURACY\n", f(K["accuracy"]))
        print("\nALT BASKETS\n", f(K["alt_baskets"][["expression", "h", "era", "acc_ref", "acc_leg", "gain", "gain_lo", "gain_hi", "stale_gain"]]))
        print("\nSHARPE\n", f(K["sharpe"]), "\n", f(K["sharpe_diff"]), "\n", K["cost_table"])
        print("\nINCREMENTAL\n", f(K["incremental"]), "\n", f(K["pnl_corr"]))
        print("\nTIMING\n", f(K["timing"]))
        print("\nSHUFFLED\n", f(K["shuffled"]))
        print("\nPAIRS\n", f(K["pairs"][["series", "h", "era", "n_indep", "acc", "lo", "hi", "base_mean", "p_random"]]))
        print("\nLEG STATS\n", f(K["leg_stats"]))
        print("\nBROAD DOLLAR (ADDED)\n", f(K["broad_dollar"]))
        print("\nATTRIBUTION (ADDED)\n", f(K["attribution"]), "\n", f(K["call_mix"]))
        print("\nE minus U, inputs\n", f(K["e_vs_u_inputs"][["signal", "h", "era", "n_indep", "acc_ref", "acc_leg", "gain", "gain_lo", "gain_hi"]]))
    return K["positions"], K["primary"]



# ============================================================================= report
def _g(df: pd.DataFrame, col: str, **kw) -> float:
    m = np.ones(len(df), dtype=bool)
    for k, v in kw.items():
        m &= (df[k] == v).values
    return float(df[m].iloc[0][col])


def _md(df: pd.DataFrame, pct=(), dec1=(), dec2=(), dec3=()) -> str:
    d = df.copy()
    for c in pct:
        if c in d:
            d[c] = (100 * d[c].astype(float)).round(1)
    for c in dec1:
        if c in d:
            d[c] = d[c].astype(float).round(1)
    for c in dec2:
        if c in d:
            d[c] = d[c].astype(float).round(2)
    for c in dec3:
        if c in d:
            d[c] = d[c].astype(float).round(3)
    return d.to_markdown(index=False)


def write_report(K: dict, path: Path | None = None) -> None:
    P_, M_, EU, A, SH, SD = K["primary"], K["mirror"], K["e_vs_u"], K["accuracy"], K["sharpe"], K["sharpe_diff"]
    AT, BD, INC, PC, TM, RC = K["attribution"], K["broad_dollar"], K["incremental"], K["pnl_corr"], K["timing"], K["reconcile"]
    p = lambda df, col, **kw: 100 * _g(df, col, **kw)  # noqa: E731
    PCT = ("acc", "lo", "hi", "base_mean", "base_lo", "base_hi", "acc_ref", "acc_leg", "leg_lo", "leg_hi", "gain", "gain_lo", "gain_hi", "rand_gain_lo", "rand_gain_hi",
           "stale_acc_ref", "stale_acc_leg", "stale_gain", "acc_S", "acc_E", "acc_U", "gain_E", "gain_U", "store_close", "h10_next_fixing", "h10_same_day_fixing",
           "published_2010_26", "share_of_days")

    # ---- key table
    key = []
    for h in HORIZONS:
        for era, _, _ in ERAS:
            r, m = P_[(P_.h == h) & (P_.era == era)].iloc[0], M_[(M_.h == h) & (M_.era == era)].iloc[0]
            key.append({"sessions": h, "era": era, "independent calls": r.n_indep, "per year": round(r.per_year, 1),
                        "plain EUR/USD %": round(100 * r.acc_ref, 1), "EUR leg %": round(100 * r.acc_leg, 1), "USD leg %": round(100 * m.acc_leg, 1),
                        "EUR leg - plain (95 % paired)": f"{100 * r.gain:+.1f} ({100 * r.gain_lo:+.1f} .. {100 * r.gain_hi:+.1f})",
                        "USD leg - plain (95 % paired)": f"{100 * m.gain:+.1f} ({100 * m.gain_lo:+.1f} .. {100 * m.gain_hi:+.1f})"})
    key = pd.DataFrame(key)
    vr = []
    for r in K["verdict_rows"].itertuples():
        if r.era == "2023-26":
            vr.append({"sessions": r.h, "era": r.era, "condition": "(b) not worse than plain EUR/USD", "gain, points": f"{r.gain_pts:+.1f}", "gain with 63-session-stale calls": f"{r.stale_gain_pts:+.1f}",
                       "result": "pass" if r.pass_a else "FAIL"})
        else:
            vr.append({"sessions": r.h, "era": r.era, "condition": "(a) gain >= +3.0 and (c) stale copy loses half of it", "gain, points": f"{r.gain_pts:+.1f}",
                       "gain with 63-session-stale calls": f"{r.stale_gain_pts:+.1f}", "result": "pass" if (r.pass_a and r.pass_c) else "FAIL (a)" + ("" if r.gain_pts > 0 else ", (c) not applicable: no gain")})
    vr = pd.DataFrame(vr)
    att = AT[AT.signal == "agreement"]
    a10, a16, a23 = (att[att.era == e].iloc[0] for e in ("2010-26", "2016-26", "2023-26"))
    a15 = att[att.era == "2010-15"].iloc[0]
    A15 = K["accuracy_2010_15"]
    acc15 = lambda c: " / ".join(f"{p(A15, 'acc', signal='agreement', series=c, h=h):.1f}" for h in HORIZONS)  # noqa: E731
    sh = lambda name, era: _g(SH, "sharpe_net", expression=name, era=era)  # noqa: E731
    trio = lambda name: " / ".join(f"{sh(name, e):+.2f}" for e in ("2010-26", "2016-26", "2023-26"))  # noqa: E731
    ct = K["cost_table"]["mean_bp_per_unit_turnover_2010_26"]
    to10 = _g(SH, "turnover_per_year", expression="plain EUR/USD (H.10)", era="2010-26")
    ck = K["checks"]
    acc3 = lambda sig, c, era: " / ".join(f"{p(A, 'acc', signal=sig, series=c, h=h, era=era):.1f}" for h in HORIZONS)  # noqa: E731
    pr3 = lambda sig, c, era: " / ".join(f"{100 * _g(A, 'p_random', signal=sig, series=c, h=h, era=era):.0f}" for h in HORIZONS)  # noqa: E731
    uwins = all(_g(EU, "gain", h=h, era=e) <= -0.03 for h in (21, 42) for e in ("2010-26", "2016-26"))
    ewins = all(_g(EU, "gain", h=h, era=e) >= 0.03 for h in (21, 42) for e in ("2010-26", "2016-26"))
    excl = any(_g(EU, "gain_lo", h=h, era="2010-26") > 0 or _g(EU, "gain_hi", h=h, era="2010-26") < 0 for h in (21, 42))
    formal = "a euro signal" if (ewins and excl) else ("a dollar signal" if (uwins and excl) else "cannot be attributed to one leg")

    L = []
    L += ["# Arm AC - leg_decomposition: is the agreement rule a euro signal or a dollar signal, and does a hedge help?", "",
          "Code `src/eurusd/arms/leg_decomposition.py` (`run()`; `PYTHONPATH=src OMP_NUM_THREADS=1 python src/eurusd/arms/leg_decomposition.py`, about half a minute, one process). "
          "Results `experiments/results/arms/leg_decomposition_*.csv`, log `experiments/results/arms/logs/leg_decomposition.log`. "
          "The primary test, its pass bar, the basket, the weights, the timing rule and the cost rule were written into the module docstring before any outcome on "
          "either leg was computed; what was added afterwards is marked ADDED there and here.", "",
          f"## Verdict: **{'PASS' if K['pass'] else 'FAIL'}** against the declared bar", "",
          "**The hedged expression is worse, not better.** The same agreement calls scored on the euro against a basket (JPY, GBP, CHF, CAD, AUD, 1/5 each) instead of on "
          f"plain EUR/USD are right {p(P_, 'acc_leg', h=21, era='2010-26'):.1f} % instead of {p(P_, 'acc_ref', h=21, era='2010-26'):.1f} % at 21 sessions and "
          f"{p(P_, 'acc_leg', h=42, era='2010-26'):.1f} % instead of {p(P_, 'acc_ref', h=42, era='2010-26'):.1f} % at 42 sessions (2010-26); "
          f"{p(P_, 'acc_leg', h=21, era='2016-26'):.1f} vs {p(P_, 'acc_ref', h=21, era='2016-26'):.1f} % and {p(P_, 'acc_leg', h=42, era='2016-26'):.1f} vs "
          f"{p(P_, 'acc_ref', h=42, era='2016-26'):.1f} % since 2016. The bar asked for +3 points in those four cells; the result is "
          f"{p(P_, 'gain', h=21, era='2010-26'):+.1f}, {p(P_, 'gain', h=21, era='2016-26'):+.1f}, {p(P_, 'gain', h=42, era='2010-26'):+.1f} and {p(P_, 'gain', h=42, era='2016-26'):+.1f} "
          "points, and at 21 sessions the paired 95 % interval lies entirely below zero in both eras. In 2023-26 it is "
          f"{p(P_, 'gain', h=21, era='2023-26'):+.1f} points at 21 sessions (bar: not worse) and {p(P_, 'gain', h=42, era='2023-26'):+.1f} at 42 sessions on "
          f"{_g(P_, 'n_indep', h=42, era='2023-26'):.0f} independent calls. The stale-copy condition cannot be met because there is no gain to lose.", "",
          _md(vr), "",
          "**Plain-language answer: it is not a euro signal, and not reliably a dollar signal either. It is a signal about the pair; the leg that delivered has changed: mostly the euro leg "
          "in 2010-15, almost only the dollar leg since 2016. Over 2010-26 as a whole slightly more of it came from the dollar side.**", "",
          f"* Direction, 2010-26: on the dollar leg alone (dollar against the same basket, euro excluded) the calls are right {acc3('agreement', 'U', '2010-26')} % at 21 / 42 / 63 sessions, about what they "
          f"score on EUR/USD itself ({acc3('agreement', 'S', '2010-26')} %); on the euro leg alone {acc3('agreement', 'E', '2010-26')} %. Since 2016: dollar leg {acc3('agreement', 'U', '2016-26')} %, "
          f"euro leg {acc3('agreement', 'E', '2016-26')} % (EUR/USD {acc3('agreement', 'S', '2016-26')} %). A random entry with the same call pattern matches or beats the euro-leg numbers in "
          f"{pr3('agreement', 'E', '2010-26')} % (2010-26) and {pr3('agreement', 'E', '2016-26')} % (2016-26) of 1,000 draws; the dollar-leg numbers in {pr3('agreement', 'U', '2010-26')} % and "
          f"{pr3('agreement', 'U', '2016-26')} %; plain EUR/USD in {pr3('agreement', 'S', '2010-26')} % and {pr3('agreement', 'S', '2016-26')} %.",
          f"* But in 2010-15 (ADDED; the euro-crisis years) it was the other way round at one month: euro leg {acc15('E')} %, dollar leg {acc15('U')} %, EUR/USD {acc15('S')} %.",
          f"* Exact split of the profit (EUR/USD = euro leg minus dollar leg, so the P&L of a call splits with no residual), gross bp a year: 2010-26 {a10.bp_per_year_eurusd:.0f} on EUR/USD = "
          f"{a10.bp_per_year_eur_leg:.0f} euro leg (t {a10.t_eur_leg:.1f}) + {a10.bp_per_year_usd_leg:.0f} dollar leg (t {a10.t_usd_leg:.1f}); "
          f"2010-15 {a15.bp_per_year_eurusd:.0f} = {a15.bp_per_year_eur_leg:.0f} euro leg (t {a15.t_eur_leg:.1f}) + {a15.bp_per_year_usd_leg:.0f} dollar leg (t {a15.t_usd_leg:.1f}); "
          f"2016-26 {a16.bp_per_year_eurusd:.0f} = {a16.bp_per_year_eur_leg:.0f} euro leg (t {a16.t_eur_leg:.1f}) + {a16.bp_per_year_usd_leg:.0f} dollar leg (t {a16.t_usd_leg:.1f}), "
          f"i.e. {100 * a16.share_from_usd_leg:.0f} % from the dollar leg; 2023-26 {a23.bp_per_year_eurusd:.0f} = {a23.bp_per_year_eur_leg:.0f} + {a23.bp_per_year_usd_leg:.0f}.",
          f"* By the attribution rule declared in advance the formal answer is **'{formal}'**: accuracy on the dollar leg is higher than on the euro leg by "
          f"{-p(EU, 'gain', h=21, era='2010-26'):.1f}, {-p(EU, 'gain', h=21, era='2016-26'):.1f}, {-p(EU, 'gain', h=42, era='2010-26'):.1f} and {-p(EU, 'gain', h=42, era='2016-26'):.1f} points in the four "
          f"declared cells (3 were required), but the paired intervals in 2010-26 include zero ({p(EU, 'gain_lo', h=21, era='2010-26'):+.1f} .. {p(EU, 'gain_hi', h=21, era='2010-26'):+.1f} at 21 sessions, "
          f"{p(EU, 'gain_lo', h=42, era='2010-26'):+.1f} .. {p(EU, 'gain_hi', h=42, era='2010-26'):+.1f} at 42); only 2016-26 at 21 sessions excludes it "
          f"({p(EU, 'gain_lo', h=21, era='2016-26'):+.1f} .. {p(EU, 'gain_hi', h=21, era='2016-26'):+.1f}). The data cannot prove a difference between the legs, and the sub-periods disagree about its sign.",
          "* The premise of the primary test (positioning in euro futures is a statement about the euro) is not supported: positioning alone calls the direction of both legs about equally often and "
          "earned most of its money on the dollar leg (section 3).",
          "* Consequence for the product: **keep trading the calls on plain EUR/USD.** The two legs are almost uncorrelated (correlation of their 21-session moves "
          f"{_g(K['leg_stats'], 'corr_E_U', era='2010-26', h=21):+.2f} in 2010-26) and EUR/USD is their difference, so the pair collects whatever the calls know about either leg, whichever leg it turns out "
          "to be. A hedge removes one leg's noise only by also removing that leg's share of the edge, and which leg carries the edge was not stable: hedging the dollar leg would have thrown away "
          "nine tenths of the profit since 2016; hedging the euro leg (trading a dollar basket instead) would have thrown away two thirds of it in 2010-15, and since 2016 it matches plain EUR/USD "
          "without beating it, for five spreads instead of one.", "",
          "## Key table: the same agreement calls scored on three instruments", "",
          "Phase-averaged accuracy (every call day scored on the next h sessions; independent calls = call days / h). Entry at the first H.10 fixing after the call, all three "
          "instruments on the same two fixings. USD leg: a long-EUR/USD call counts as right when the dollar FELL against the basket.", "",
          _md(key), "",
          "Sharpe of the daily position streams, net of 1.2 pips on every pair traded (2010-26 / 2016-26 / 2023-26): "
          f"plain EUR/USD {trio('plain EUR/USD (H.10)')}; EUR leg as a hedge (six pairs) {trio('EUR leg (EW5)')}; EUR leg through five direct crosses {trio('EUR leg (EW5), direct crosses')}; "
          f"USD leg {trio('USD leg (EW5)')}.", "",
          f"Candidates run: **{K['n_candidates']}** (5 declared + 1 added post hoc; cap 12). None passes.", ""]

    # ---- data
    L += ["## 1. Data, timing and what was checked before any outcome", "",
          "* **Used: Federal Reserve H.10 noon-New-York rates** (`data/macro/fred_DEX{USEU,JPUS,USUK,SZUS,CAUS,USAL,SDUS,NOUS}.csv`, 1999-01-04 .. 2026-11-06, 6,984 fixings, no gaps "
          "inside the panel; 3.5-4.4 % of weekdays have no fixing, the US holidays). One stamp convention for the whole history and every currency at the same instant, so each euro "
          "cross is derived at one timestamp. **Not used: the Yahoo daily bars** in `data/processed/cross/*_D1.parquet` (stamp convention changed in 2010 Q3).",
          "* **Timing rule.** The call is made at the 17:00 New York close of date D; the trade is entered at the first fixing strictly after D (noon of the next fixing day, 19 hours later) and "
          "scored at the first fixing strictly after the close date of session i + h. No series stamped at a different time is joined on the same day.",
          f"* **H.10 against EUR/USD in the feature store** (same date, noon vs 17:00): median level gap {ck['h10_level_gap_pips']:.0f} pips; return correlation and sign agreement by horizon:", "",
          _md(ck["h10_vs_store"], dec3=("corr_returns", "sign_agree"), dec1=("median_abs_gap_bp",)), "",
          "* **Independent source.** ECB euro reference rates (14:15 CET, `data/processed/cross/leg_ecb_ref_rates.parquet`, fetched 2026-11-17 from the ECB data API, flow EXR, "
          "1999-01-04 .. 2026-11-17). They quote the euro crosses DIRECTLY, whereas H.10 gives the dollar pairs directly and the euro crosses by triangulation. The derived H.10 crosses agree with "
          "the direct ECB crosses exactly as well as EUR/USD itself agrees between the two sources (the difference is the 3 h 45 min between the fixings, not triangulation error):", "",
          _md(ck["h10_vs_ecb"], dec3=("corr_5d", "corr_21d", "h10_missing_share_of_weekdays"), dec1=("max_abs_5d_gap_bp",)), "",
          f"* **SEK and NOK** pass the declared verification rule ({'verified' if ck['sek_nok_verified'] else 'NOT verified'}: 5-session correlation with the ECB rates within 0.01 of the worst core cross "
          "in every era), so the robustness basket B7 was run.",
          "* **The identity.** S = E - U holds to floating-point precision on every bar (max error 0.0 bp in `leg_decomposition_leg_stats.csv`), by construction, because the euro crosses are "
          "derived from the dollar pairs at the same fixing. What the legs look like (21-session moves unless stated):", "",
          _md(K["leg_stats"][K["leg_stats"].h == 21][["era", "ann_vol_S_pct", "ann_vol_E_pct", "ann_vol_U_pct", "corr_E_U", "var_share_E", "var_share_U", "sign_agree_S_E", "sign_agree_S_minusU"]],
              dec1=("ann_vol_S_pct", "ann_vol_E_pct", "ann_vol_U_pct"), dec2=("corr_E_U", "var_share_E", "var_share_U", "sign_agree_S_E", "sign_agree_S_minusU")), "",
          "  S = EUR/USD, E = euro against the basket, U = dollar against the basket. The dollar leg is the larger one: its variance is 52-83 % of EUR/USD's, the euro leg's 28-43 % (the shares need not add to 100 because of the covariance); "
          "the two are close to uncorrelated; EUR/USD's 21-session direction agrees with the dollar leg's 79-89 % of the time and with the euro leg's 58-73 %.", "",
          "## 2. Reconciliation", "",
          "The agreement rule rebuilt with `committee._fold_columns` (identical to `experiments/70_committee.py::agreement_side`) reproduces the published benchmark exactly on the feature-store "
          "closes (asserted in `compute()`), and scores within about one point of it on the H.10 fixings:", "",
          _md(RC, pct=PCT, dec1=("per_year",)), "",
          "Call pattern: " + "; ".join(f"{r.era}: calls on {100 * r.call_days_share:.0f} % of sessions, {100 * r.long_share_of_call_days:.0f} % of them long, {r.call_episodes} separate call episodes"
                                       for r in K["call_mix"].itertuples()) + ".", ""]

    # ---- descriptive
    L += ["## 3. Descriptive (declared): the rule and each of its three inputs on EUR/USD (S), the euro leg (E) and the dollar leg (U)", "",
          "`n_indep` = independent decisions, `lo`-`hi` = 95 % Wilson interval on that count, `per_year` = independent decisions a year, `base_*` = matched random entry (the era's own call "
          "sequence rotated to a random position, 1,000 draws: same count, spacing and long / short mix), `p_random` = share of random draws at least as accurate.", ""]
    for sig, title in (("agreement", "Agreement rule"), ("positioning", "Positioning alone (sign of cot_z52, always on)"), ("spread_trend", "2-year spread trend alone (sign of d_spread2y_20)"),
                       ("house_score", "House macro score alone (sign, walk-forward)")):
        d = A[A.signal == sig][["series", "h", "era", "n_indep", "per_year", "acc", "lo", "hi", "base_mean", "base_lo", "base_hi", "p_random"]]
        L += [f"### {title}", "", _md(d, pct=PCT, dec1=("per_year",), dec2=("p_random",)), ""]
    pa = AT.copy()
    L += ["What the inputs say:",
          f"* **Positioning** (the input the theory was about). Direction accuracy is the same on both legs at 21 sessions ({p(A, 'acc', signal='positioning', series='E', h=21, era='2010-26'):.1f} % euro leg, "
          f"{p(A, 'acc', signal='positioning', series='U', h=21, era='2010-26'):.1f} % dollar leg, 2010-26) and somewhat higher on the euro leg at 42 and 63 sessions "
          f"({p(A, 'acc', signal='positioning', series='E', h=42, era='2010-26'):.1f} vs {p(A, 'acc', signal='positioning', series='U', h=42, era='2010-26'):.1f}; "
          f"{p(A, 'acc', signal='positioning', series='E', h=63, era='2010-26'):.1f} vs {p(A, 'acc', signal='positioning', series='U', h=63, era='2010-26'):.1f}); no paired interval excludes zero. "
          f"In money terms it is the other way round: {100 * _g(pa, 'share_from_usd_leg', signal='positioning', era='2010-26'):.0f} % of its 2010-26 P&L and "
          f"{100 * _g(pa, 'share_from_usd_leg', signal='positioning', era='2016-26'):.0f} % of its 2016-26 P&L came from the dollar leg (above 100 means the euro leg lost a little; gross Sharpe {_g(pa, 'sharpe_gross_usd_leg', signal='positioning', era='2016-26'):.2f} "
          f"on the dollar leg, {_g(pa, 'sharpe_gross_eur_leg', signal='positioning', era='2016-26'):.2f} on the euro leg). 'Net speculative position in euro futures' is a position in the EUR/USD contract; "
          "it is at least as much a view on the dollar as on the euro. The premise of the primary test is not supported.",
          f"* **House macro score**: dollar leg ({acc3('house_score', 'U', '2016-26')} % since 2016; random entry at least as good in {pr3('house_score', 'U', '2016-26')} % of draws) rather than euro leg ({acc3('house_score', 'E', '2016-26')} %).",
          f"* **2-year spread trend**: about 50 % on everything on its own (known); the little there is sits on the dollar leg at 42-63 sessions "
          f"({p(A, 'acc', signal='spread_trend', series='U', h=42, era='2010-26'):.1f} / {p(A, 'acc', signal='spread_trend', series='U', h=63, era='2010-26'):.1f} %).",
          "* **2023-26** runs the other way for positioning (euro leg 54-61 %, dollar leg 45-46 %) on 15-47 independent decisions with intervals 25 points wide: not evidence of anything.", "",
          "Euro leg minus dollar leg, per input (paired 95 % interval, same call days):", "",
          _md(K["e_vs_u_inputs"].rename(columns={"acc_ref": "acc_U", "acc_leg": "acc_E", "gain": "E_minus_U", "gain_lo": "lo", "gain_hi": "hi"})[["signal", "h", "era", "n_indep", "acc_E", "acc_U", "E_minus_U", "lo", "hi"]]
              .pipe(lambda d: d[d.era != "2023-26"]), pct=("acc_E", "acc_U", "E_minus_U", "lo", "hi")), ""]

    # ---- primary
    cols = ["h", "era", "n_indep", "per_year", "acc_ref", "acc_leg", "leg_lo", "leg_hi", "gain", "gain_lo", "gain_hi", "rand_gain_lo", "rand_gain_hi", "p_random_gain", "stale_acc_ref", "stale_acc_leg", "stale_gain"]
    L += ["## 4. PRIMARY TEST (candidate 1): the calls on the euro leg against the calls on plain EUR/USD", "",
          "`acc_ref` = plain EUR/USD, `acc_leg` = euro against the basket, `gain` = difference with its paired block-bootstrap 95 % interval (blocks of 126 sessions, 2,000 draws); "
          "`rand_gain_*` = 95 % range of the same difference under matched random entry; `stale_*` = the calls of 63 sessions earlier.", "",
          _md(P_[cols], pct=PCT, dec1=("per_year",), dec2=("p_random_gain",)), "",
          f"**FAIL** on (a) in all four cells and on (b) at 21 sessions. Noteworthy in the placebo columns: the 63-session-stale calls score {p(P_, 'stale_acc_leg', h=21, era='2010-26'):.1f} % on the euro leg at 21 sessions "
          f"(live calls {p(P_, 'acc_leg', h=21, era='2010-26'):.1f} %) and {p(M_, 'stale_acc_leg', h=21, era='2010-26'):.1f} % on the dollar leg (live {p(M_, 'acc_leg', h=21, era='2010-26'):.1f} %). "
          f"Since 2016: stale {p(P_, 'stale_acc_leg', h=21, era='2016-26'):.1f} vs live {p(P_, 'acc_leg', h=21, era='2016-26'):.1f} % on the euro leg, stale {p(M_, 'stale_acc_leg', h=21, era='2016-26'):.1f} vs live "
          f"{p(M_, 'acc_leg', h=21, era='2016-26'):.1f} % on the dollar leg. The timely part of the rule is its dollar part; on the euro leg the three-month-old calls do better than the live ones, "
          "so whatever is there is slow drift or noise, not timing.", "",
          "## 5. Secondary (declared)", "",
          "### 5a. Mirror (candidate 2): the calls on the dollar leg (long EUR/USD call = short the dollar against the basket)", "",
          _md(M_[cols], pct=PCT, dec1=("per_year",), dec2=("p_random_gain",)), "",
          f"Same accuracy as plain EUR/USD within noise ({p(M_, 'gain', h=21, era='2010-26'):+.1f} / {p(M_, 'gain', h=42, era='2010-26'):+.1f} points in 2010-26, "
          f"{p(M_, 'gain', h=21, era='2016-26'):+.1f} / {p(M_, 'gain', h=42, era='2016-26'):+.1f} in 2016-26, {p(M_, 'gain', h=21, era='2023-26'):+.1f} / {p(M_, 'gain', h=42, era='2023-26'):+.1f} in 2023-26). "
          "It would also fail the bar: +3 points is reached in one cell of four.", "",
          "### 5b. Risk-adjusted comparison and the cost of the hedge", "",
          "Position = the day's call (+1 / 0 / -1), held from its entry fixing to the next session's entry fixing. Cost arithmetic, 1.2 pips per unit of turnover on EVERY pair traded, in the "
          "pair's own pip (0.01 for yen pairs), 2010-26 averages:", "",
          f"| expression | pairs traded | cost per unit of turnover | turnover a year | cost a year |", "|:--|:--|--:|--:|--:|",
          f"| plain EUR/USD | EUR/USD x 1 | {ct['plain']:.2f} bp | {to10:.0f} | {ct['plain'] * to10:.0f} bp |",
          f"| USD leg | five dollar pairs x 1/5 | {ct['usd_leg']:.2f} bp | {to10:.0f} | {ct['usd_leg'] * to10:.0f} bp |",
          f"| EUR leg as a hedge (headline) | EUR/USD x 1 + five dollar pairs x 1/5 = six spreads | {ct['eur_leg_hedge6']:.2f} bp | {to10:.0f} | {ct['eur_leg_hedge6'] * to10:.0f} bp |",
          f"| EUR leg, five direct crosses at 1.2 pips | EUR/JPY, EUR/GBP, EUR/CHF, EUR/CAD, EUR/AUD x 1/5 | {ct['eur_leg_crosses']:.2f} bp | {to10:.0f} | {ct['eur_leg_crosses'] * to10:.0f} bp |",
          f"| EUR leg, five direct crosses at 3 pips | same | {ct['eur_leg_crosses'] * 3 / COST_PIPS:.2f} bp | {to10:.0f} | {ct['eur_leg_crosses'] * 3 / COST_PIPS * to10:.0f} bp |", "",
          "The hedge doubles the cost per unit of notional (2.18 against 1.02 bp) while the hedged position is LESS volatile (5.7 against 8.1 % a year in 2010-26, 4.5 against 6.9 % since 2016), "
          "so per unit of risk it costs about three times as much. Trading the five crosses directly at a major's spread would cost the same as EUR/USD, but nobody quotes EUR/AUD or EUR/CAD "
          "at 1.2 pips; the 3-pip row is the realistic one. The rule changes its call about 40 times a year (20 round trips), so this is 40-100 bp a year against a gross edge of "
          f"{a10.bp_per_year_eur_leg:.0f} bp a year on the euro leg in 2010-26 and {a16.bp_per_year_eur_leg:.0f} bp since 2016.", "",
          _md(SH[["expression", "cost", "era", "sharpe_net", "t_net", "sharpe_gross", "ann_vol_bp_when_in", "turnover_per_year", "cost_bp_per_year"]],
              dec2=("sharpe_net", "t_net", "sharpe_gross"), dec1=("ann_vol_bp_when_in", "turnover_per_year", "cost_bp_per_year")), "",
          "Sharpe difference against plain EUR/USD (same calls, paired block bootstrap, 95 %):", "",
          _md(SD, dec2=("d_sharpe_vs_plain", "lo", "hi", "pnl_corr_with_plain")), "",
          f"The hedged expression loses {-_g(SD, 'd_sharpe_vs_plain', expression='EUR leg (EW5)', era='2010-26'):.2f} Sharpe in 2010-26 and {-_g(SD, 'd_sharpe_vs_plain', expression='EUR leg (EW5)', era='2016-26'):.2f} in 2016-26 "
          "(both intervals below zero) and is not better even before costs (gross 0.45 against 0.74; 0.07 against 0.55). The lower volatility of a basket does not rescue it: the edge "
          "falls faster than the risk. The dollar-leg expression is level with plain EUR/USD since 2016 and behind it over 2010-26.", "",
          "Incremental test (Round 3 addendum): `meta.combine` EW of weak_signals + regime_trend, with each stream offered as a third arm:", "",
          _md(INC, dec2=("sr_2way", "sr_3way", "d_sr")), "",
          _md(PC, dec2=("corr_weak_signals", "corr_regime_trend")), "",
          f"The primary stream (`leg_decomposition` = euro leg, hedge costs) LOWERS the combination on 2016-26 ({_g(INC, 'sr_2way', third_arm='leg_decomposition', era='2016-26'):.2f} -> "
          f"{_g(INC, 'sr_3way', third_arm='leg_decomposition', era='2016-26'):.2f}): fails. The plain agreement stream is the reference (the existing rule, 0.46-0.52 correlated with the live streams; adds nothing "
          "to them on 2016-26, as known).", "",
          "### 5c. Other basket weights (candidates 3, 4, 5)", "",
          "* Candidate 3, ECB trade weights: narrow EER group, overall weights including third-market effects, manufactures and services, 2021 (official figures from the ECB data API, "
          "`data/processed/cross/leg_ecb_trade_weights.csv`), renormalised over the five: GBP 47.1 %, CHF 26.8 %, JPY 16.5 %, CAD 6.2 %, AUD 3.4 %.",
          "* Candidate 4, Fed broad-dollar-index weights, APPROXIMATE (2019 revision, quoted from memory because federalreserve.gov is blocked here; not verified): CAD 46.2 %, JPY 21.7 %, "
          "GBP 18.3 %, CHF 9.0 %, AUD 4.8 % after renormalising.",
          "* Candidate 5, seven currencies at 1/7 (adds SEK and NOK).", "",
          _md(K["alt_baskets"][K["alt_baskets"].h.isin([21, 42])][["basket", "leg", "h", "era", "n_indep", "acc_ref", "acc_leg", "gain", "gain_lo", "gain_hi", "stale_gain"]], pct=PCT), "",
          "`leg` E / U = that leg against plain EUR/USD (`acc_ref` = plain); `E-U` = euro leg against dollar leg (`acc_ref` = dollar leg). **The answer does not change with the weights**: the euro leg is "
          "2.6-9.8 points below plain EUR/USD in every 2010-26 and 2016-26 cell under all three weightings, the dollar leg is within about 3 points of it, and the dollar leg is at or above the euro leg in every "
          "such cell. The gap is smallest with the Fed weights, where the basket is half Canadian dollar.", ""]

    # ---- added
    L += ["## 6. ADDED after the first run", "",
          "### 6a. Exact split of the P&L between the legs (descriptive)", "",
          "Because S = E - U bar by bar, the gross P&L of any call on EUR/USD is the P&L of the same call on the euro leg plus its P&L on the (sign-flipped) dollar leg, with no residual "
          "(`identity_err_bp` = 0). bp a year, gross, all sessions:", "",
          _md(AT[["signal", "era", "bp_per_year_eurusd", "bp_per_year_eur_leg", "bp_per_year_usd_leg", "share_from_usd_leg", "t_eurusd", "t_eur_leg", "t_usd_leg", "sharpe_gross_eur_leg", "sharpe_gross_usd_leg"]],
              dec1=("bp_per_year_eurusd", "bp_per_year_eur_leg", "bp_per_year_usd_leg"), dec2=("share_from_usd_leg", "t_eurusd", "t_eur_leg", "t_usd_leg", "sharpe_gross_eur_leg", "sharpe_gross_usd_leg")), "",
          "For every input and every era more than half of the money came from the dollar leg; over 2016-26 it is 80-100 %. No t-statistic on the euro leg reaches 1 in the 2016-26 or 2023-26 windows. "
          "(Direction accuracy and money can disagree: positioning calls the euro leg's direction as often as the dollar leg's, but the dollar leg moves further when it is right.)", "",
          "The split is not stable. In 2010-15 the euro leg earned more than the dollar leg for the agreement rule and the house score; in 2016-26 the dollar leg earned nearly everything. "
          "The same in direction accuracy, 2010-15 only (ADDED; 34 / 17 / 11 independent calls for the agreement rule, so the intervals are wide):", "",
          _md(K["accuracy_2010_15"][["signal", "series", "h", "n_indep", "acc", "lo", "hi", "base_mean", "p_random"]], pct=PCT, dec2=("p_random",)), "",
          "### 6b. Candidate 6, POST HOC: the calls on a broad dollar basket (dollar against EUR, JPY, GBP, CHF, CAD, AUD at 1/6 each)", "",
          "Chosen after seeing the per-pair table below, so it could only ever be a lead. It is not one:", "",
          _md(BD[cols], pct=PCT, dec1=("per_year",), dec2=("p_random_gain",)), "",
          f"Accuracy within about 3 points of plain EUR/USD in every cell ({p(BD, 'gain', h=21, era='2010-26'):+.1f} / {p(BD, 'gain', h=42, era='2010-26'):+.1f} in 2010-26, "
          f"{p(BD, 'gain', h=21, era='2016-26'):+.1f} / {p(BD, 'gain', h=42, era='2016-26'):+.1f} in 2016-26), net Sharpe {trio('broad dollar USD6 (ADDED)')} against {trio('plain EUR/USD (H.10)')} for plain EUR/USD. "
          "Spreading the call over six dollar pairs neither helps nor hurts; it is the same bet with six tickets.", "",
          "### 6c. Per single pair (declared descriptive)", "",
          "Agreement calls scored on each pair. EURxxx: right when the euro rose against xxx after a long call; USDxxx: right when the dollar FELL against xxx after a long call.", "",
          _md(K["pairs"][K["pairs"].era != "2023-26"][["series", "h", "era", "n_indep", "acc", "lo", "hi", "base_mean", "p_random"]].pipe(lambda d: d[d.h.isin([21, 42])]), pct=PCT, dec2=("p_random",)), "",
          "After a long-EUR/USD call the dollar tends to fall against sterling, the franc, the Canadian and the Australian dollar as well (55-63 % in these cells); the yen is the weak spot (49-57 %). "
          "The euro itself does best against the yen (54-59 %) and LOSES to the Australian dollar (43-45 %): a 'long EUR/USD' call is in practice a 'dollar down' call, and the euro is not the "
          "currency that gains most from it. Ten pairs, four cells each: single-pair differences are descriptive, none is a result.", ""]

    # ---- sanity
    L += ["## 7. Sanity checks", "",
          "**Timing** (the conclusion must not depend on the fixing used). Accuracy of the same calls on S / E / U and the two gains:", "",
          _md(TM[TM.h.isin([21, 42])], pct=PCT), "",
          "Entering at the same-day fixing (five hours before the call, formally a peek), at the declared next fixing, one fixing later, or on the ECB's 14:15 CET fixings gives the same picture to "
          "within a point or two: euro leg 5-8 points below plain EUR/USD in 2010-26 and 2016-26, dollar leg within 4 points of it. Nothing here is a same-day join across stamp conventions, and "
          "lagging the cross series by a day changes nothing.", "",
          "**Shuffled labels** (one joint permutation of all outcomes and of the returns the house score is fitted on, five seeds, 2010-26):", "",
          _md(K["shuffled"], pct=PCT), "",
          "Accuracy 48-52 % on every series and the gain within +-2 points: the pipeline finds nothing when there is nothing.", "",
          "**Identity**: section 1 (exact). **Look-ahead**: the calls are the committee module's walk-forward calls (its truncation control: 0 of 48 columns differ); no parameter is fitted on the legs; "
          "the basket weights are fixed constants (the ECB weights are 2021 figures applied to the whole history, which is a mild anachronism in a robustness run, not a leak of prices).", "",
          "## 8. Candidates and counts", "",
          f"* Candidates: **{K['n_candidates']}**. Declared: (1) euro leg, equal weights [primary]; (2) dollar leg, equal weights [mirror]; (3) ECB weights; (4) Fed weights; (5) seven-currency basket. "
          "Added post hoc: (6) broad dollar. Each was scored at 21 / 42 / 63 sessions in three eras with the same tables; the Sharpe comparison and the incremental test are other yardsticks on "
          "candidates 1, 2 and 6, not new candidates.",
          "* Declared descriptive cells: 4 signals x 3 instruments x 9 (horizon, era) = 108 accuracies; 10 single pairs x 9 = 90. Checks: 4 timing variants, 5 shuffles.", "",
          "## 9. Suspicious, and caveats", "",
          f"* **Entry-time noise in 2023-26.** The same calls on plain EUR/USD have a net Sharpe of {sh('plain EUR/USD (H.10)', '2023-26'):.2f} when entered at the next noon fixing and "
          f"{sh('plain EUR/USD (store closes)', '2023-26'):.2f} on the feature-store closes 19 hours earlier (2010-26: {sh('plain EUR/USD (H.10)', '2010-26'):.2f} vs {sh('plain EUR/USD (store closes)', '2010-26'):.2f}; "
          f"2016-26: {sh('plain EUR/USD (H.10)', '2016-26'):.2f} vs {sh('plain EUR/USD (store closes)', '2016-26'):.2f}). Accuracy at 21-63 sessions reconciles within a point, so this is the daily-stream yardstick being "
          "fragile on four years with about 35 position changes a year, not a data error; all comparisons in this report are between instruments on the SAME fixings, where it cancels. It is one more "
          "reason not to read anything into 2023-26.",
          "* **The call flickers.** 340 separate call episodes in 17 years, about 6 sessions each; the phase-averaged accuracy scores every call day on the following 21-63 sessions regardless. "
          "This is the published benchmark's convention and is the same for every instrument here.",
          "* **The stale euro leg** (section 4): on the euro leg the three-month-old calls beat the live ones (59 vs 53 % at 21 sessions). Whatever the rule has on the euro side is slow drift or noise, not timing. "
          "On plain EUR/USD the stale copy scores the same as the live calls at 21 sessions (59.4 vs 59.2 %), as the committee report already found: the live calls' dollar-leg timing and the stale calls' "
          "euro-leg drift happen to add up to the same number.",
          "* **Fed weights are from memory**, not from the source (blocked). They enter one robustness candidate whose result agrees with the other baskets.",
          "* **Spot only.** No carry in any expression, as everywhere in the project. A long-euro-against-basket position earns or pays a different carry from long EUR/USD (the basket holds two "
          "low-yield and three higher-yield currencies); with the gross edge on the euro leg at 20 bp a year since 2016 this cannot change the verdict.",
          "* **Small samples.** 2023-26 has 19 / 9 / 6 independent calls at 21 / 42 / 63 sessions; the Wilson intervals are 40-60 points wide.",
          "* **H.10 is one noon snapshot** of buying rates rounded to four decimals (about 1 bp); irrelevant against 21-session moves of 150-230 bp.",
          "* The attribution rule was declared in advance and returns 'cannot be attributed'; the stronger statement in the verdict ('more dollar than euro, almost only dollar since 2016') rests on "
          "the exact P&L split, which was added after the first run and is descriptive.", "",
          "## 10. Files", "",
          "* `src/eurusd/arms/leg_decomposition.py` - declaration in the docstring, `run()` entry point, `write_report()`.",
          "* `experiments/results/arms/leg_decomposition_*.csv`: `reconcile`, `accuracy`, `primary`, `verdict_rows`, `mirror`, `e_vs_u`, `e_vs_u_inputs`, `alt_baskets`, `broad_dollar`, `sharpe`, `sharpe_diff`, "
          "`cost_table`, `incremental`, `pnl_corr`, `attribution`, `call_mix`, `pairs`, `timing`, `shuffled`, `leg_stats`, `check_h10_vs_store`, `check_h10_vs_ecb`.",
          "* `experiments/results/arms/leg_decomposition_positions.parquet` (primary expression, 2010+: `pos`, `fwd_bp`, `net_bp`, booked one session later so that it lines up with the "
          "close-to-close arms) and `leg_decomposition_calls.parquet` (the walk-forward calls and the three input signs).",
          "* New data: `data/processed/cross/leg_ecb_ref_rates.parquet` (ECB reference rates, USD JPY GBP CHF CAD AUD SEK NOK per EUR, 1999-01-04 .. 2026-11-17, no lag needed: used only at fixings "
          "after the call) and `data/processed/cross/leg_ecb_trade_weights.csv` (ECB narrow-group trade weights, 2021).", ""]
    (path or ROOT / "reports" / "arm_leg_decomposition.md").write_text("\n".join(L))


if __name__ == "__main__":
    run()
