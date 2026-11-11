"""Arm V "divergence_g10": PRE-REGISTERED REPLICATION ACROSS CURRENCIES of the round-5 policy-divergence lead.

Lead being tested (reports/arm_regime_dependence.md, family-wise p 0.11, i.e. NOT a result): on EUR/USD the slow signals
pay almost only while the ECB-Fed policy gap is WIDER than six months earlier (positioning sign: Sharpe 1.34 on WIDER
sessions vs 0.12 elsewhere; 2y-spread trend 0.95 vs 0.10; agreement rule right 64 % / 70 % at 21 / 42 sessions vs
51 % / 49 %). Story: when two central banks are actively diverging, capital follows the rate differential and trends
persist; when they converge nothing does. Two earlier EUR-only findings (positioning trend, residual order flow) failed
on other currencies, so the mechanism is tested here with a rule that needs no EUR-specific input.

STEP 0 - FROZEN DEFINITIONS. Everything from here to the line "END OF FROZEN PART" was written BEFORE any strategy
result of this arm was computed. Only data AVAILABILITY had been inspected (first / last date and missing months of each
series, FRED reachability). Nothing below was changed after the first run; additions made later are listed after that
line and labelled as such.

Currencies c in {EUR, GBP, JPY, CHF, AUD, CAD, NZD, SEK, NOK}, each against USD. The test is IDENTICAL for all nine;
EUR is the reference (the pair the lead was found on), the eight others are the replication sample.

DATA
* Short rates r_c, r_US: OECD 3-month interbank rates from FRED, monthly averages in percent:
  IR3TIB01{EZ,GB,JP,CH,AU,CA,NZ,SE,NO,US}M156N (data/macro/fred_<series>.csv; SE and NO fetched by `fetch_missing`).
  The euro-area series stops at 2026-01; it is extended with IR3TIB01DEM156N (Germany), which is the same number since
  1999 (3-month Euribor; equality on the overlap is asserted). No other splice. Every series is put on a complete
  monthly grid and a missing month (inside a series or after its last observation) is filled with the previous value
  for at most 3 months; beyond that the differential is undefined, the currency is flat and leaves the basket.
  This monthly short rate is the PRIMARY and ONLY rate measure for all nine currencies including EUR (daily 2y yields
  exist in the repo for EUR and USD only and are not used, so that the test is the same everywhere).
* Publication lag: the observation of month m is stamped A(m) = last calendar day of m + 30 days; a session dated D uses
  the latest m with A(m) <= D - 1 calendar day (the feature-store `_align_lagged` convention on top of the 30 days).
* Prices: Federal Reserve H.10 noon New York rates from FRED (DEXUSEU, DEXUSUK, DEXJPUS, DEXSZUS, DEXUSAL, DEXCAUS,
  DEXUSNZ, DEXSDUS, DEXNOUS), converted to USD per unit of foreign currency ("foreign currency vs USD"). One row per
  H.10 date; frames start 1990-01-02 (EUR: 1999-01-04).
* Returns: fwd_spot(D) = 1e4 * ln(P[D+1] / P[D]) in bp. Carry of a long foreign-currency position per session =
  (r_c - r_US) * 100 / 252 bp, using the same lagged monthly differential as the signal. PRIMARY P&L = spot + carry
  (the rule trades rate differentials); the spot-only version is reported next to it.
* Volatility: rv_21d_bp = sqrt(mean of the last 21 squared daily log returns) in bp (as arm F).

RULE (no fitted parameter except the training-median volatility)
  d_c(m)   = r_c(m) - r_US(m)
  (b) gap  = |d_c(m)|;  WIDER if gap(m) > gap(m-6) (+1e-9), NARROWER if smaller, SAME if equal.
      COMPLEMENT = NARROWER or SAME. All streams exist only where d_c(m), d_c(m-3) and d_c(m-6) exist.
  (c) RATE-DIFFERENTIAL TREND: s(m) = sign(d_c(m) - d_c(m-3))  (+1 = long the foreign currency: its relative rate rose).
      Vol scale v(D) = clip(median_train(rv_21d_bp) / rv_21d_bp(D), 0, 1.5), median over the rows whose label is known
      before 1 January of the test year (`eurusd.wf.walk_forward`, test years 2000..2026, min_train_years=1 because the
      EUR H.10 series starts in 1999). MONTHLY REBALANCED: on the first session on which a new monthly observation is
      in use (and on the first walk-forward session) pos = s(m) * v(D); it is held unchanged until the next one.
  (d) GATED: pos of (c) while the class of month m is WIDER, 0 otherwise.
  (e) COMPLEMENT: pos of (c) while the class is NARROWER or SAME, 0 otherwise.   (c) = (d) + (e) before costs.
  Exactly these three streams, each with and without carry = 6 streams. No window is tuned. The one alternative
  (6-month change of d_c for the signal, gap against 12 months earlier for the class) is run ONCE and reported only as
  a labelled robustness line; it cannot enter the verdict.
* Costs: `cost_pips` (1.2) pips of the conventional pair per unit turnover through `wf.pnl_from_positions`: EURUSD,
  GBPUSD, AUDUSD, NZDUSD, USDCHF, USDCAD (pip 1e-4), USDJPY (pip 0.01). For USDSEK and USDNOK 1.2 pips is 0.1 bp, not a
  real spread, so the headline charges 25 x (30 pips, about 3 bp), exactly as arm F did for USDMXN; the literal
  1.2-pip version and a 2x-cost version are reported as sensitivities.

STATISTICS
* Stream Sharpe / t: `wf._agg` on the daily net bp of the stream, all sessions on which the class is defined (flat
  sessions count as zero), 252 a year. Periods by session year: 2000-26, 2010-26, 2016-26, 2023-26.
* On-session Sharpe (the statistic of the arm S lead, "1.34 on WIDER sessions vs 0.12 elsewhere"): Sharpe of the
  UNGATED stream's net P&L over the sessions of the class only.
* Share of time WIDER: WIDER sessions / sessions with a defined class.
* Directional accuracy at h = 21 / 42 / 63 sessions on NON-OVERLAPPING decisions: greedy stream (decide on the first
  session on which the signal is non-zero and the class holds, skip h sessions, repeat; stream started at the first
  session of 2000; a decision belongs to the period of its date); hit = sign(s) x h-session SPOT log return > 0; Wilson
  interval per currency. Basket accuracy = decisions of the eight currencies pooled (they are cross-correlated, so
  the pooled count overstates the information; no interval is claimed for it).
* BASKET: equal weight of the eight non-EUR currencies: basket net bp on a date = mean of the currencies' net bp over
  the currencies whose class is defined on that date (a currency flat because of the gate counts as zero; a currency
  without rate data is left out).

STEP 1 (EUR/USD reproduction, descriptive): (a) the monthly-interbank class against arm S's daily-policy-rate class
  `div_change` (deposit rate vs fed funds target, 182 calendar days) on the feature-store sessions 2006-26: share WIDER
  under each, share of sessions with the same class (WIDER vs not); (b) arm S's own table (`regime_tables`: positioning
  sign, 2y-spread trend, agreement rule; on-session Sharpe inside / outside WIDER, non-overlapping accuracy at 21 / 42
  sessions) recomputed with the monthly class in place of the policy-rate class; (c) the frozen rule on EUR/USD.

STEP 3 - PRE-REGISTERED VERDICT, primary P&L (spot + carry, net of the headline costs), eight-currency ex-EUR basket.
  The divergence mechanism REPLICATES iff ALL of:
  (i)   the basket GATED-WIDER stream has Sharpe > 0 in 2000-26 AND in 2010-26, and its t-statistic over 2000-26
        (the pooled t: one basket stream, so cross-correlation is respected) is >= 2;
  (ii)  the on-session Sharpe of WIDER minus that of the COMPLEMENT (2000-26) is positive in at least 6 of the 8
        non-EUR currencies;
  (iii) rotation placebo: every currency's daily class series (WIDER / complement) is rotated circularly inside its
        own defined span by the SAME k sessions, k uniform in [252, shortest span - 252], 500 draws (seed 7), positions
        and costs recomputed; statistic G = Sharpe(basket WIDER stream) - Sharpe(basket COMPLEMENT stream), 2000-26.
        Passes if the share of draws with G_rot >= G_observed is <= 5 %.
  Otherwise it FAILS. Secondary, reported but not in the verdict: the same placebo for the mean over the eight
  currencies of the on-session Sharpe gap; everything for 2010-26; the spot-only streams.

STEP 4 - ONLY IF STEP 3 SAYS REPLICATES: EUR/USD "agreement rule gated by WIDER" (arm S's code) and "rate-differential
  trend gated by WIDER" on the feature-store grid, Round 5 extra-vote and incremental tests, recommendation on the
  engine's primary rule. If Step 3 fails, Step 4 is NOT run and the report says that the WIDER lead is likely a third
  EUR-specific artefact.

LEAK CHECKS on the basket (ungated, WIDER, complement; with carry): (1) forward returns shuffled in time (5 seeds)
  -> Sharpe ~ 0; class labels shuffled i.i.d. by month (20 seeds) -> the WIDER-minus-complement gap vanishes on
  average; (2) rate data lagged one more month (A(m) + 30 days), and, as the Round 5/6 stale placebo, 3 and 6 more
  months; (3) look-ahead control: rate data stamped 61, 91 and 122 days EARLY (the month's average known at the start
  of its own month, one month before, two months before) - reported so that a timing leak would be visible.

DELIVERABLES: experiments/results/arms/divergence_g10_positions.parquet = EUR/USD daily stream of the gated rule (d)
  on the feature-store grid (store `rv_21d_bp`, `fwd_1d`, `close`; default walk-forward years 2010-26; `pos`, `fwd_bp`,
  `net_bp` spot-only net of costs so that it stacks like every other arm, plus `carry_bp`, `net_bp_carry`,
  `pos_ungated`, `wider`); divergence_g10_report.csv (per currency + basket, every stream and period);
  divergence_g10_basket.parquet (daily basket and per-currency streams); reports/arm_divergence_g10.md.
Trial count: 6 frozen streams (3 x with / without carry) + 1 labelled robustness line.

END OF FROZEN PART
-------------------------------------------------------------------------------------------------------------------
ADDED AFTER THE FIRST RUN (labelled ADDED in the report; none of it enters the verdict, no frozen definition changed):
  * `added_diagnostics`: (A) the three streams by era (2000-09, 2006-26 = the window of the EUR lead, 2010-26, 2010-15,
    2016-26);
    (B) carry alignment: share of sessions on which the position of rule (c) has the sign of the rate differential,
    inside WIDER and inside the complement, and the split of the gated basket's P&L into spot and carry;
    (C) benchmark, not a candidate: the plain carry trade sign(d_c) with the same vol scale and monthly rebalance, its
    correlation with the gated stream and the gated stream's alpha on it; (D) the verdict statistics with the literal
    1.2-pip cost for USDSEK / USDNOK, and the headline placebo with 5,000 draws (Monte-Carlo error of the 500-draw p);
  * leak check (1): the shuffled-return check uses 40 seeds instead of 5 (the first five seeds averaged -0.21, which
    is a 5-seed accident: 40 seeds average -0.07 with s.d. 0.19);
  * the stream table of the delivered EUR/USD feature-store positions.
"""
from __future__ import annotations

import io
import math
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.wf import _agg, pnl_from_positions, walk_forward  # noqa: E402

MACRO = ROOT / "data" / "macro"
DATA = ROOT / "data" / "processed" / "features_daily.parquet"
OUT = ROOT / "experiments" / "results" / "arms"
REPORTS = ROOT / "reports"
ARM = "divergence_g10"

VOL_CAP = 1.5
SIG_K, GAP_K = 3, 6            # frozen windows (months)
LAG_DAYS = 30                  # publication lag after month end
FFILL_MONTHS = 3
WF_YEARS = list(range(2000, 2027))
HS = (21, 42, 63)
PERIODS = (("2000-26", 2000, 2026), ("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026))
PLACEBO_REPS, PLACEBO_SEED = 500, 7

CCY = {
    "eur": dict(h10="DEXUSEU", inv=False, pip=1e-4, conv_inv=False, cost_mult=1.0, rate="IR3TIB01EZM156N", pair="EURUSD"),
    "gbp": dict(h10="DEXUSUK", inv=False, pip=1e-4, conv_inv=False, cost_mult=1.0, rate="IR3TIB01GBM156N", pair="GBPUSD"),
    "jpy": dict(h10="DEXJPUS", inv=True, pip=1e-2, conv_inv=True, cost_mult=1.0, rate="IR3TIB01JPM156N", pair="USDJPY"),
    "chf": dict(h10="DEXSZUS", inv=True, pip=1e-4, conv_inv=True, cost_mult=1.0, rate="IR3TIB01CHM156N", pair="USDCHF"),
    "aud": dict(h10="DEXUSAL", inv=False, pip=1e-4, conv_inv=False, cost_mult=1.0, rate="IR3TIB01AUM156N", pair="AUDUSD"),
    "cad": dict(h10="DEXCAUS", inv=True, pip=1e-4, conv_inv=True, cost_mult=1.0, rate="IR3TIB01CAM156N", pair="USDCAD"),
    "nzd": dict(h10="DEXUSNZ", inv=False, pip=1e-4, conv_inv=False, cost_mult=1.0, rate="IR3TIB01NZM156N", pair="NZDUSD"),
    "sek": dict(h10="DEXSDUS", inv=True, pip=1e-4, conv_inv=True, cost_mult=25.0, rate="IR3TIB01SEM156N", pair="USDSEK"),
    "nok": dict(h10="DEXNOUS", inv=True, pip=1e-4, conv_inv=True, cost_mult=25.0, rate="IR3TIB01NOM156N", pair="USDNOK"),
}
ALL9 = list(CCY)
OTHERS8 = ALL9[1:]
US_RATE = "IR3TIB01USM156N"
EZ_EXT = "IR3TIB01DEM156N"


# ============================================================================= data
def _fred(series: str) -> pd.DataFrame:
    """FRED answers curl (HTTP/1.1) through the session proxy but not python-requests (as in arm F)."""
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series}"
    txt = subprocess.run(["curl", "-sS", "-f", "-m", "120", "--http1.1", url], capture_output=True, text=True, check=True).stdout
    if not txt.startswith("observation_date"):
        raise RuntimeError(f"unexpected FRED payload for {series}: {txt[:60]!r}")
    d = pd.read_csv(io.StringIO(txt))
    d.columns = ["date", "value"]
    d["value"] = pd.to_numeric(d["value"], errors="coerce")
    return d.dropna().reset_index(drop=True)


def fetch_missing(verbose: bool = True) -> None:
    """Fetch the series arm F did not save (SEK and NOK prices and rates); existing files are never overwritten."""
    need = [m["h10"] for m in CCY.values()] + [m["rate"] for m in CCY.values()] + [US_RATE, EZ_EXT]
    for s in need:
        p = MACRO / f"fred_{s}.csv"
        if p.exists():
            continue
        d = _fred(s)
        d.to_csv(p, index=False)
        if verbose:
            print(f"  fred {s}: {len(d)} rows {d.date.iloc[0]}..{d.date.iloc[-1]}", flush=True)
        time.sleep(0.5)


def _series(name: str) -> pd.Series:
    return pd.read_csv(MACRO / f"fred_{name}.csv", parse_dates=["date"]).set_index("date")["value"].astype(float).dropna()


def load_rates() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Monthly panel (index = month start) of the ten 3-month rates on a complete grid, forward-filled <= 3 months.
    Returns (panel, info) where info lists first / last raw observation and the months that were filled."""
    raw = {c: _series(m["rate"]) for c, m in CCY.items()}
    raw["us"] = _series(US_RATE)
    de = _series(EZ_EXT)
    ez = raw["eur"]
    ov = pd.concat([ez, de], axis=1, keys=["ez", "de"], sort=True).loc["1999-01":].dropna()
    assert len(ov) > 300 and float((ov.ez - ov.de).abs().max()) < 0.02, "EZ and DE 3-month rates differ on the overlap"
    ez_last = ez.index[-1]
    raw["eur"] = pd.concat([ez, de[de.index > ez_last]])
    last = max(s.index[-1] for s in raw.values())
    grid = pd.date_range("1990-01-01", last, freq="MS")
    info = []
    R = {}
    for c, s in raw.items():
        g = s.reindex(grid)
        f = g.ffill(limit=FFILL_MONTHS)
        filled = f.notna() & g.isna() & (grid >= s.index[0])
        R[c] = f
        info.append({"ccy": c, "series": US_RATE if c == "us" else CCY[c]["rate"], "first": s.index[0].strftime("%Y-%m"),
                     "last": s.index[-1].strftime("%Y-%m"), "filled_months": ", ".join(grid[filled].strftime("%Y-%m")),
                     "ez_extended_from": (ez_last + pd.offsets.MonthBegin(1)).strftime("%Y-%m") if c == "eur" else ""})
    return pd.DataFrame(R), pd.DataFrame(info)


def monthly_state(R: pd.DataFrame, ccy: str, sig_k: int = SIG_K, gap_k: int = GAP_K) -> pd.DataFrame:
    d = R[ccy] - R["us"]
    gap = d.abs()
    chg = gap - gap.shift(gap_k)
    st = pd.DataFrame({"d": d, "sig": np.sign(d - d.shift(sig_k)), "chg": chg})
    st["defined"] = d.notna() & d.shift(sig_k).notna() & d.shift(gap_k).notna()
    st["wider"] = st["defined"] & (chg > 1e-9)
    st["cls"] = np.where(~st["defined"], None, np.where(chg > 1e-9, "WIDER", np.where(chg < -1e-9, "NARROWER", "SAME")))
    return st


def align_month(st: pd.DataFrame, dates: pd.DatetimeIndex, shift_days: int = 0) -> np.ndarray:
    """Index of the latest month usable on each date: A(m) = month end + 30 days (+ shift_days) <= date - 1 day."""
    avail = (st.index + pd.offsets.MonthEnd(0) + pd.Timedelta(days=LAG_DAYS + shift_days)).values
    return np.searchsorted(avail, (pd.DatetimeIndex(dates) - pd.Timedelta(days=1)).values, side="right") - 1


def load_px(ccy: str) -> pd.Series:
    m = CCY[ccy]
    s = _series(m["h10"])
    s = s[s > 0]
    p = 1.0 / s if m["inv"] else s
    return p.loc["1990-01-01":]


def currency_frame(ccy: str, R: pd.DataFrame, sig_k: int = SIG_K, gap_k: int = GAP_K, shift_days: int = 0,
                   literal_cost: bool = False) -> pd.DataFrame:
    """One row per H.10 date D (17:00 UTC ~ noon New York): decision with rate data usable at D, earning D -> D+1."""
    p = load_px(ccy)
    dates = pd.DatetimeIndex(p.index)
    idx = (dates + pd.Timedelta(hours=17)).tz_localize("UTC")
    lp = np.log(p.values)
    df = pd.DataFrame(index=idx)
    df["px"] = p.values
    df["fwd_spot"] = np.r_[np.diff(lp), np.nan] * 1e4
    df["label_end"] = idx[1:].append(pd.DatetimeIndex([idx[-1] + pd.Timedelta(days=3)]))
    r = pd.Series(np.r_[np.nan, np.diff(lp)], index=idx)
    df["rv_21d_bp"] = np.sqrt((r ** 2).rolling(21).mean()) * 1e4
    st = monthly_state(R, ccy, sig_k, gap_k)
    j = align_month(st, dates, shift_days)
    ok = j >= 0
    jj = np.clip(j, 0, len(st) - 1)
    df["j"] = j
    df["d"] = np.where(ok, st["d"].values[jj], np.nan)
    df["sig"] = np.where(ok, st["sig"].values[jj], np.nan)
    df["defined"] = ok & st["defined"].values[jj]
    df["wider"] = ok & st["wider"].values[jj]
    df["carry_bp"] = np.nan_to_num(df["d"].values) * 100.0 / 252.0
    m = CCY[ccy]
    conv = 1.0 / df["px"] if m["conv_inv"] else df["px"]
    df["cost_px"] = conv * (1e-4 / m["pip"]) / (1.0 if literal_cost else m["cost_mult"])
    for h in HS:
        f = np.full(len(lp), np.nan)
        f[:len(lp) - h] = (lp[h:] - lp[:-h]) * 1e4
        df[f"F{h}"] = f
    # vol scale, walk-forward; monthly rebalanced position of rule (c)
    v = walk_forward(df, lambda tr: float(tr["rv_21d_bp"].median()),
                     lambda med, te: (med / te["rv_21d_bp"]).clip(0, VOL_CAP),
                     label_end=df["label_end"], years=WF_YEARS, min_train_years=1, verbose=False)
    df["v"] = v
    df["pos"] = hold_monthly(df["sig"].where(df["defined"], 0.0).fillna(0.0) * v, df["j"].values, v.notna().values)
    df["oos"] = df["defined"].values & v.notna().values & df["fwd_spot"].notna().values
    return df


def hold_monthly(target: pd.Series, j: np.ndarray, live: np.ndarray) -> pd.Series:
    """Take `target` on rebalance sessions (first session of a new usable month, first live session) and hold it."""
    reb = np.r_[True, j[1:] != j[:-1]] & live
    first_live = live & ~np.r_[False, live[:-1]]
    reb |= first_live
    return target.where(reb).ffill().where(live, 0.0).fillna(0.0)


# ============================================================================= streams and statistics
def streams(df: pd.DataFrame, cost_pips: float, carry: bool = True, fwd: np.ndarray | None = None,
            wider: np.ndarray | None = None) -> pd.DataFrame:
    """Daily net bp of (c) ungated, (d) WIDER, (e) complement on the sessions where the class is defined (OOS)."""
    f = pd.Series((df["fwd_spot"].values + (df["carry_bp"].values if carry else 0.0)) if fwd is None else fwd, index=df.index)
    w = df["wider"].values if wider is None else wider
    oos = df["oos"].values
    out = pd.DataFrame(index=df.index)
    for name, mask in (("ungated", np.ones(len(df), bool)), ("wider", w), ("complement", df["defined"].values & ~w)):
        pos = pd.Series(np.where(mask & oos, df["pos"].values, 0.0), index=df.index)
        pn = pnl_from_positions(pos, f, df["cost_px"], cost_pips=cost_pips)
        out[f"pos_{name}"] = pos
        out[f"net_{name}"] = pn["net_bp"]
    out["is_wider"] = w
    return out[oos]


def sr(x: pd.Series | np.ndarray) -> tuple[float, float, int]:
    r = _agg(pd.Series(np.asarray(x, dtype=float)), 252)
    return (r["sharpe"], r["t"], r["n"]) if r["n"] >= 10 else (np.nan, np.nan, r["n"])


def wilson(k: float, n: float, z: float = 1.959964) -> tuple[float, float]:
    if n <= 0:
        return np.nan, np.nan
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(max(p * (1 - p) / n + z * z / (4 * n * n), 0.0)) / den
    return mid - half, mid + half


def greedy_idx(speak: np.ndarray, h: int) -> np.ndarray:
    out, i, n = [], 0, len(speak)
    while i < n:
        if speak[i]:
            out.append(i)
            i += h
        else:
            i += 1
    return np.asarray(out, dtype=int)


def accuracy_cells(df: pd.DataFrame) -> pd.DataFrame:
    """Non-overlapping decisions per class and horizon: one row per decision (ccy-level frame)."""
    year = df.index.year.values
    s = np.sign(df["pos"].values)
    rows = []
    for cls, mask in (("ungated", df["defined"].values), ("wider", df["wider"].values), ("complement", df["defined"].values & ~df["wider"].values)):
        for h in HS:
            F = df[f"F{h}"].values
            speak = (s != 0) & mask & df["oos"].values & np.isfinite(F) & (year >= 2000)
            idx = greedy_idx(speak, h)
            g = s[idx] * F[idx]
            rows.append(pd.DataFrame({"stream": cls, "h": h, "year": year[idx], "hit": (g > 0).astype(float), "gross_bp": g}))
    return pd.concat(rows, ignore_index=True)


def stat_rows(name: str, S: pd.DataFrame, acc: pd.DataFrame | None, carry: bool, group: str) -> list[dict]:
    """Per period: stream Sharpe / t of the three streams, on-session Sharpe, share WIDER, accuracy."""
    rows = []
    yr = S.index.year
    for lab, a, b in PERIODS:
        m = (yr >= a) & (yr <= b)
        if m.sum() < 60:
            continue
        w = S["is_wider"].values[m] if "is_wider" in S else None
        base = {"name": name, "group": group, "carry": carry, "period": lab, "sessions": int(m.sum()),
                "first": str(S.index[m][0].date()), "last": str(S.index[m][-1].date())}
        if w is not None:
            base["share_wider"] = float(w.mean())
            u = S["net_ungated"].values[m]
            base["onsession_sharpe_wider"], base["onsession_t_wider"], _ = sr(u[w])
            base["onsession_sharpe_complement"], base["onsession_t_complement"], _ = sr(u[~w])
            base["onsession_gap"] = base["onsession_sharpe_wider"] - base["onsession_sharpe_complement"]
        elif "share_wider" in S:
            base["share_wider"] = float(S["share_wider"].values[m].mean())
        for st in ("ungated", "wider", "complement"):
            r = dict(base)
            r["stream"] = st
            r["sharpe"], r["t"], r["n"] = sr(S[f"net_{st}"].values[m])
            r["mean_bp"] = float(np.nanmean(S[f"net_{st}"].values[m]))
            r["active_frac"] = float((S[f"pos_{st}"].values[m] != 0).mean()) if f"pos_{st}" in S else np.nan
            if acc is not None:
                for h in HS:
                    q = acc[(acc.stream == st) & (acc.h == h) & (acc.year >= a) & (acc.year <= b)]
                    n = len(q)
                    k = float(q.hit.sum())
                    lo, hi = wilson(k, n)
                    r[f"acc{h}"] = k / n if n else np.nan
                    r[f"n{h}"] = n
                    r[f"lo{h}"], r[f"hi{h}"] = lo, hi
                    r[f"gross_bp{h}"] = float(q.gross_bp.mean()) if n else np.nan
            rows.append(r)
    return rows


def basket_streams(SS: dict, members: list[str]) -> pd.DataFrame:
    """Equal weight over the members whose class is defined on the date."""
    out = {}
    for st in ("ungated", "wider", "complement"):
        out[f"net_{st}"] = pd.DataFrame({c: SS[c][f"net_{st}"] for c in members}).mean(axis=1, skipna=True)
        out[f"pos_{st}"] = pd.DataFrame({c: SS[c][f"pos_{st}"].abs() for c in members}).mean(axis=1, skipna=True)
    out["share_wider"] = pd.DataFrame({c: SS[c]["is_wider"].astype(float) for c in members}).mean(axis=1, skipna=True)
    out["n_ccy"] = pd.DataFrame({c: SS[c]["net_ungated"] for c in members}).notna().sum(axis=1)
    return pd.DataFrame(out).sort_index()


def study(R: pd.DataFrame, cost_pips: float, sig_k: int = SIG_K, gap_k: int = GAP_K, shift_days: int = 0,
          literal_cost: bool = False, with_acc: bool = True, tag: str = "frozen") -> dict:
    frames = {c: currency_frame(c, R, sig_k, gap_k, shift_days, literal_cost) for c in ALL9}
    rows, SSc = [], {}
    for carry in (True, False):
        SS = {c: streams(frames[c], cost_pips, carry) for c in ALL9}
        SSc[carry] = SS
        accs = {c: accuracy_cells(frames[c]) for c in ALL9} if with_acc else {c: None for c in ALL9}
        for c in ALL9:
            rows += stat_rows(c, SS[c], accs[c], carry, "currency")
        B = basket_streams(SS, OTHERS8)
        SSc[(carry, "basket8")] = B
        acc_b = pd.concat([accs[c] for c in OTHERS8], ignore_index=True) if with_acc else None
        rows += stat_rows("basket8_ex_eur", B, acc_b, carry, "basket")
        B9 = basket_streams(SS, ALL9)
        rows += stat_rows("basket9_incl_eur", B9, None, carry, "basket")
    rep = pd.DataFrame(rows)
    rep.insert(0, "variant", tag)
    return {"frames": frames, "streams": SSc, "report": rep}


# ============================================================================= rotation placebo
def _matrices(frames: dict, members: list[str], carry: bool = True):
    """Union-calendar arrays (T x K): ungated pos, fwd, cost bp, class, oos mask."""
    idx = sorted(set().union(*[set(frames[c].index[frames[c]["oos"].values]) for c in members]))
    idx = pd.DatetimeIndex(idx)
    T, K = len(idx), len(members)
    pos = np.zeros((T, K)); fwd = np.zeros((T, K)); cost = np.zeros((T, K)); w = np.zeros((T, K), bool); oos = np.zeros((T, K), bool)
    for k, c in enumerate(members):
        f = frames[c][frames[c]["oos"].values]
        loc = idx.get_indexer(f.index)
        pos[loc, k] = f["pos"].values
        fwd[loc, k] = f["fwd_spot"].values + (f["carry_bp"].values if carry else 0.0)
        cost[loc, k] = 1.0 / f["cost_px"].values
        w[loc, k] = f["wider"].values
        oos[loc, k] = True
    return idx, pos, fwd, cost, w, oos


def _gap_stats(idx, pos, fwd, cost, w, oos, cost_pips: float, a: int, b: int) -> dict:
    """Basket Sharpe gap (WIDER stream - complement stream) and mean per-currency on-session gap, years a..b."""
    yr = idx.year.values
    m = (yr >= a) & (yr <= b)
    out = {}
    nets = {}
    for name, mask in (("w", w & oos), ("c", ~w & oos)):
        p = np.where(mask, pos, 0.0)
        to = np.abs(np.diff(p, axis=0, prepend=0.0))
        net = p * fwd - to * cost * cost_pips
        net = np.where(oos, net, np.nan)
        nets[name] = net
        bk = np.nanmean(net[m], axis=1)
        bk = bk[np.isfinite(bk)]
        out[f"sr_{name}"] = bk.mean() / bk.std(ddof=1) * math.sqrt(252)
        out[f"t_{name}"] = bk.mean() / bk.std(ddof=1) * math.sqrt(len(bk))
    out["gap"] = out["sr_w"] - out["sr_c"]
    # on-session gap per currency from the ungated stream
    to = np.abs(np.diff(pos, axis=0, prepend=0.0))
    un = pos * fwd - to * cost * cost_pips
    gaps = []
    for k in range(pos.shape[1]):
        mk = m & oos[:, k]
        xi, xo = un[mk & w[:, k], k], un[mk & ~w[:, k], k]
        if len(xi) > 20 and len(xo) > 20 and xi.std() > 0 and xo.std() > 0:
            gaps.append(xi.mean() / xi.std(ddof=1) * math.sqrt(252) - xo.mean() / xo.std(ddof=1) * math.sqrt(252))
        else:
            gaps.append(np.nan)
    out["onsession_gaps"] = np.array(gaps)
    out["mean_onsession_gap"] = float(np.nanmean(gaps))
    out["n_pos"] = int(np.nansum(np.array(gaps) > 0))
    return out


def rotation_placebo(frames: dict, cost_pips: float, members: list[str] = OTHERS8, carry: bool = True,
                     reps: int = PLACEBO_REPS, seed: int = PLACEBO_SEED) -> dict:
    idx, pos, fwd, cost, w, oos = _matrices(frames, members, carry)
    spans = [np.flatnonzero(oos[:, k]) for k in range(len(members))]
    shortest = min(len(s) for s in spans)
    rng = np.random.default_rng(seed)
    obs = {lab: _gap_stats(idx, pos, fwd, cost, w, oos, cost_pips, a, b) for lab, a, b in PERIODS[:2]}
    draws = {lab: [] for lab, _, _ in PERIODS[:2]}
    for _ in range(reps):
        k = int(rng.integers(252, shortest - 252))
        wr = np.zeros_like(w)
        for i, s in enumerate(spans):
            wr[s, i] = np.roll(w[s, i], k)
        for lab, a, b in PERIODS[:2]:
            g = _gap_stats(idx, pos, fwd, cost, wr, oos, cost_pips, a, b)
            draws[lab].append((g["gap"], g["mean_onsession_gap"], g["n_pos"], g["sr_w"], g["t_w"]))
    rows = []
    for lab, _, _ in PERIODS[:2]:
        D = np.array(draws[lab], dtype=float)
        o = obs[lab]
        rows.append({"period": lab, "reps": reps, "shortest_span_sessions": shortest,
                     "basket_sr_wider": o["sr_w"], "basket_t_wider": o["t_w"], "basket_sr_complement": o["sr_c"], "basket_t_complement": o["t_c"],
                     "basket_gap": o["gap"], "placebo_gap_mean": float(D[:, 0].mean()), "placebo_gap_sd": float(D[:, 0].std(ddof=1)),
                     "placebo_gap_q95": float(np.quantile(D[:, 0], 0.95)), "p_basket_gap": float((D[:, 0] >= o["gap"] - 1e-12).mean()),
                     "mean_onsession_gap": o["mean_onsession_gap"], "placebo_onsession_mean": float(D[:, 1].mean()),
                     "placebo_onsession_q95": float(np.quantile(D[:, 1], 0.95)),
                     "p_mean_onsession_gap": float((D[:, 1] >= o["mean_onsession_gap"] - 1e-12).mean()),
                     "n_ccy_gap_positive": o["n_pos"], "p_n_positive": float((D[:, 2] >= o["n_pos"]).mean()),
                     "placebo_sr_wider_mean": float(D[:, 3].mean()), "p_sr_wider": float((D[:, 3] >= o["sr_w"] - 1e-12).mean()),
                     **{f"onsession_gap_{c}": float(g) for c, g in zip(members, o["onsession_gaps"])}})
    return {"table": pd.DataFrame(rows), "draws": draws, "obs": obs}


# ============================================================================= verdict
def verdict(rep: pd.DataFrame, plc: pd.DataFrame) -> dict:
    q = rep[(rep.variant == "frozen") & rep.carry & (rep.name == "basket8_ex_eur") & (rep.stream == "wider")].set_index("period")
    c1 = bool(q.loc["2000-26", "sharpe"] > 0 and q.loc["2010-26", "sharpe"] > 0 and q.loc["2000-26", "t"] >= 2.0)
    g = rep[(rep.variant == "frozen") & rep.carry & (rep.group == "currency") & (rep.stream == "wider") & (rep.period == "2000-26")
            & rep.name.isin(OTHERS8)].set_index("name")["onsession_gap"]
    npos = int((g > 0).sum())
    c2 = npos >= 6
    p = float(plc.set_index("period").loc["2000-26", "p_basket_gap"])
    c3 = p <= 0.05
    return {"i": c1, "ii": c2, "iii": c3, "replicates": bool(c1 and c2 and c3),
            "sr_wider_2000": float(q.loc["2000-26", "sharpe"]), "t_wider_2000": float(q.loc["2000-26", "t"]),
            "sr_wider_2010": float(q.loc["2010-26", "sharpe"]), "t_wider_2010": float(q.loc["2010-26", "t"]),
            "n_positive": npos, "gaps": g.to_dict(), "placebo_p": p}


# ============================================================================= leak checks
def _basket_line(R, cost_pips, label, **kw) -> dict:
    S = study(R, cost_pips, with_acc=False, tag=label, **kw)
    B = S["streams"][(True, "basket8")]
    row = {"check": label}
    for lab, a, b in PERIODS[:2]:
        m = (B.index.year >= a) & (B.index.year <= b)
        for st in ("ungated", "wider", "complement"):
            row[f"sr_{st}_{lab}"], row[f"t_{st}_{lab}"], _ = sr(B[f"net_{st}"].values[m])
        row[f"gap_{lab}"] = row[f"sr_wider_{lab}"] - row[f"sr_complement_{lab}"]
    return row


def leak_checks(R: pd.DataFrame, frames: dict, cost_pips: float) -> pd.DataFrame:
    rows = [_basket_line(R, cost_pips, "as run (frozen rule, basket of 8, spot + carry)")]
    # (1a) forward returns shuffled in time (per currency, inside its own OOS rows); 40 seeds (5 in the first run)
    sh = []
    for seed in range(40):
        SS = {}
        for i, c in enumerate(OTHERS8):
            f = frames[c]
            fw = (f["fwd_spot"].values + f["carry_bp"].values).copy()
            o = np.flatnonzero(f["oos"].values)
            fw[o] = fw[o][np.random.default_rng(1000 * seed + i).permutation(len(o))]
            SS[c] = streams(f, cost_pips, True, fwd=fw)
        B = basket_streams(SS, OTHERS8)
        row = {}
        for lab, a, b in PERIODS[:2]:
            m = (B.index.year >= a) & (B.index.year <= b)
            for st in ("ungated", "wider", "complement"):
                row[f"sr_{st}_{lab}"], row[f"t_{st}_{lab}"], _ = sr(B[f"net_{st}"].values[m])
            row[f"gap_{lab}"] = row[f"sr_wider_{lab}"] - row[f"sr_complement_{lab}"]
        sh.append(row)
    A0 = pd.DataFrame(sh)
    rows.append({"check": "(1) forward returns shuffled, mean of 40 seeds", **A0.mean().to_dict()})
    rows.append({"check": "(1) forward returns shuffled, sd of 40 seeds", **A0.std(ddof=1).to_dict()})
    rows.append({"check": "(1) forward returns shuffled, mean of the first 5 seeds (first run)", **A0.iloc[:5].mean().to_dict()})
    # (1b) class labels shuffled i.i.d. by month
    acc = []
    for seed in range(20):
        SS = {}
        for i, c in enumerate(OTHERS8):
            f = frames[c]
            j = f["j"].values
            months = np.unique(j[f["defined"].values])
            lab_m = pd.Series(f["wider"].values[f["defined"].values]).groupby(j[f["defined"].values]).first().reindex(months).values
            perm = np.random.default_rng(5000 + 100 * seed + i).permutation(len(months))
            mp = dict(zip(months, lab_m[perm]))
            wsh = np.array([bool(mp.get(x, False)) for x in j]) & f["defined"].values
            SS[c] = streams(f, cost_pips, True, wider=wsh)
        B = basket_streams(SS, OTHERS8)
        row = {}
        for lab, a, b in PERIODS[:2]:
            m = (B.index.year >= a) & (B.index.year <= b)
            for st in ("ungated", "wider", "complement"):
                row[f"sr_{st}_{lab}"], row[f"t_{st}_{lab}"], _ = sr(B[f"net_{st}"].values[m])
            row[f"gap_{lab}"] = row[f"sr_wider_{lab}"] - row[f"sr_complement_{lab}"]
        acc.append(row)
    A = pd.DataFrame(acc)
    rows.append({"check": "(1) class labels shuffled by month, mean of 20 seeds", **A.mean().to_dict()})
    rows.append({"check": "(1) class labels shuffled by month, sd of 20 seeds", **A.std(ddof=1).to_dict()})
    # (2) staler rate data
    for extra, lab in ((30, "(2) rate data lagged +1 month (month end + 60 d)"), (91, "(2) stale placebo: rate data lagged +3 months"),
                       (182, "(2) stale placebo: rate data lagged +6 months")):
        rows.append(_basket_line(R, cost_pips, lab, shift_days=extra))
    # (3) look-ahead controls
    for early, lab in ((-30, "(3) look-ahead: no publication lag (stamped at month end)"),
                       (-61, "(3) look-ahead: month average known at the start of its own month"),
                       (-91, "(3) look-ahead: known one month before the month starts"),
                       (-122, "(3) look-ahead: known two months before the month starts")):
        rows.append(_basket_line(R, cost_pips, lab, shift_days=early))
    return pd.DataFrame(rows)


# ============================================================================= EUR/USD on the feature-store grid
def eurusd_store(R: pd.DataFrame, cost_pips: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    """The gated rule (d) on the feature-store sessions (deliverable stream) + the daily class series for step 1."""
    X = pd.read_parquet(DATA)
    cdate = pd.DatetimeIndex(X["close_time"].dt.tz_convert("UTC").dt.normalize().dt.tz_localize(None))
    st = monthly_state(R, "eur")
    j = align_month(st, cdate)
    jj = np.clip(j, 0, len(st) - 1)
    ok = j >= 0
    defined = ok & st["defined"].values[jj]
    wider = ok & st["wider"].values[jj]
    cls = np.where(defined, st["cls"].values[jj], None)
    sig = np.where(defined, st["sig"].values[jj], 0.0)
    d = np.where(ok, st["d"].values[jj], np.nan)
    v = walk_forward(X, lambda tr: float(tr["rv_21d_bp"].median()), lambda med, te: (med / te["rv_21d_bp"]).clip(0, VOL_CAP),
                     label_end=X["label_end_1d"], verbose=False)
    pos_u = hold_monthly(pd.Series(sig, index=X.index) * v, j, v.notna().values)
    pos = pos_u.where(wider, 0.0)
    carry = np.nan_to_num(d) * 100.0 / 252.0
    pn = pnl_from_positions(pos, X["fwd_1d"], X["close"], cost_pips=cost_pips)
    pc = pnl_from_positions(pos, X["fwd_1d"] + carry, X["close"], cost_pips=cost_pips)
    out = pd.DataFrame({"pos": pos, "fwd_bp": X["fwd_1d"], "net_bp": pn["net_bp"], "carry_bp": carry, "net_bp_carry": pc["net_bp"],
                        "pos_ungated": pos_u, "wider": wider, "cls": cls})
    for name, p in (("ungated", pos_u), ("complement", pos_u.where(defined & ~wider, 0.0))):
        out[f"net_bp_{name}"] = pnl_from_positions(p, X["fwd_1d"], X["close"], cost_pips=cost_pips)["net_bp"]
        out[f"net_bp_{name}_carry"] = pnl_from_positions(p, X["fwd_1d"] + carry, X["close"], cost_pips=cost_pips)["net_bp"]
    cl = pd.DataFrame({"cls_monthly": cls, "wider_monthly": wider, "defined_monthly": defined}, index=X.index)
    return out[out.index.year >= 2010], cl


def eur_reproduction(R: pd.DataFrame, cost_pips: float) -> dict:
    """Step 1 (a) + (b): arm S's policy-rate class vs the monthly-interbank class, and arm S's own table under both."""
    from eurusd.arms import regime_dependence as RD
    P = RD.load_panel(cost_pips)
    D = P.extra["D"]
    Rg = RD.build_regimes(D)
    _, cl = eurusd_store(R, cost_pips)
    assert cl.index.equals(D.index)
    pol = Rg["div_change"].values
    mon = cl["cls_monthly"].values
    yr = D.index.year.values
    conc = []
    for lab, a, b in (("2006-26", 2006, 2026), ("2006-15", 2006, 2015), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026)):
        m = (yr >= a) & (yr <= b) & pd.notna(pol) & pd.notna(mon)
        pw, mw = pol[m] == "WIDER", mon[m] == "WIDER"
        conc.append({"period": lab, "sessions": int(m.sum()), "share_wider_policy": float(pw.mean()), "share_same_policy": float((pol[m] == "SAME").mean()),
                     "share_wider_monthly": float(mw.mean()), "same_class": float((pw == mw).mean()),
                     "wider_policy_also_monthly": float(mw[pw].mean()) if pw.any() else np.nan,
                     "wider_monthly_also_policy": float(pw[mw].mean()) if mw.any() else np.nan,
                     "phi": float(np.corrcoef(pw, mw)[0, 1])})
    R2 = Rg.copy()
    R2["div_change"] = mon
    comps = ("cot", "spread", "house", "agree3")
    T1 = RD.regime_tables(P, Rg, comps=comps)
    T2 = RD.regime_tables(P, R2, comps=comps)
    keep = ["component", "period", "sessions", "share_of_defined", "sharpe_in", "t_in", "sharpe_out", "N21_in_acc", "N21_in_n", "N21_out_acc",
            "N21_out_n", "N42_in_acc", "N42_in_n", "N42_out_acc", "N42_out_n"]
    t1 = T1[(T1.regime == "div_change") & (T1["class"] == "WIDER")][keep].assign(label="policy rates, daily (arm S)")
    t2 = T2[(T2.regime == "div_change") & (T2["class"] == "WIDER")][keep].assign(label="3m interbank, monthly (this arm)")
    return {"concordance": pd.DataFrame(conc), "table": pd.concat([t1, t2], ignore_index=True)}


# ============================================================================= ADDED AFTER THE FIRST RUN (diagnostics)
ERAS = (("2000-26", 2000, 2026), ("2000-09", 2000, 2009), ("2006-26", 2006, 2026), ("2010-26", 2010, 2026), ("2010-15", 2010, 2015),
        ("2016-26", 2016, 2026))


def added_diagnostics(R: pd.DataFrame, main: dict, cost_pips: float) -> dict:
    frames = main["frames"]
    out = {}
    # (A) eras
    rows = []
    for carry in (True, False):
        for name, S in (("basket8_ex_eur", main["streams"][(carry, "basket8")]), ("eur", main["streams"][carry]["eur"])):
            for lab, a, b in ERAS:
                m = (S.index.year >= a) & (S.index.year <= b)
                r = {"name": name, "carry": carry, "period": lab}
                for st in ("ungated", "wider", "complement"):
                    r[f"sr_{st}"], r[f"t_{st}"], _ = sr(S[f"net_{st}"].values[m])
                r["gap"] = r["sr_wider"] - r["sr_complement"]
                rows.append(r)
    out["eras"] = pd.DataFrame(rows)
    # (B) carry alignment and spot / carry split
    rows, parts = [], {k: {} for k in ("w_spot", "w_carry", "c_spot", "c_carry")}
    for c in ALL9:
        f = frames[c][frames[c]["oos"].values]
        al = np.sign(f["pos"].values) == np.sign(f["d"].values)
        w = f["wider"].values
        act = f["pos"].values != 0
        rows.append({"ccy": c, "aligned_with_carry_wider": float(al[w & act].mean()), "aligned_with_carry_complement": float(al[~w & act].mean()),
                     "mean_abs_diff_pct": float(f["d"].abs().mean()), "share_wider": float(w.mean())})
        parts["w_spot"][c] = pd.Series(np.where(w, f["pos"].values, 0.0) * f["fwd_spot"].values, index=f.index)
        parts["w_carry"][c] = pd.Series(np.where(w, f["pos"].values, 0.0) * f["carry_bp"].values, index=f.index)
        parts["c_spot"][c] = pd.Series(np.where(~w, f["pos"].values, 0.0) * f["fwd_spot"].values, index=f.index)
        parts["c_carry"][c] = pd.Series(np.where(~w, f["pos"].values, 0.0) * f["carry_bp"].values, index=f.index)
    out["alignment"] = pd.DataFrame(rows)
    rows = []
    bk = {k: pd.DataFrame({c: v[c] for c in OTHERS8}).mean(axis=1, skipna=True) for k, v in parts.items()}
    for lab, a, b in ERAS:
        r = {"period": lab}
        for k, x in bk.items():
            r[f"{k}_bp_per_year"] = float(x[(x.index.year >= a) & (x.index.year <= b)].mean() * 252)
        rows.append(r)
    out["split"] = pd.DataFrame(rows)
    # (C) plain carry benchmark (not a candidate)
    SSb = {}
    for c in OTHERS8:
        f = frames[c].copy()
        f["pos"] = hold_monthly(pd.Series(np.sign(f["d"].values), index=f.index).where(f["defined"], 0.0).fillna(0.0) * f["v"], f["j"].values, f["v"].notna().values)
        SSb[c] = streams(f, cost_pips, True)
    Bc = basket_streams(SSb, OTHERS8)
    Bg = main["streams"][(True, "basket8")]
    rows = []
    for lab, a, b in ERAS:
        m = (Bc.index.year >= a) & (Bc.index.year <= b)
        x, y = Bc["net_ungated"].values[m], Bg["net_wider"].reindex(Bc.index).values[m]
        ok = np.isfinite(x) & np.isfinite(y)
        x, y = x[ok], y[ok]
        A_ = np.c_[np.ones(len(x)), x]
        beta, *_ = np.linalg.lstsq(A_, y, rcond=None)
        res = y - A_ @ beta
        se = math.sqrt(res.var(ddof=2) * np.linalg.inv(A_.T @ A_)[0, 0])
        s1, t1, _ = sr(x)
        rows.append({"period": lab, "carry_benchmark_sr": s1, "carry_benchmark_t": t1, "corr_with_gated_wider": float(np.corrcoef(x, y)[0, 1]),
                     "beta": float(beta[1]), "alpha_bp_per_year": float(beta[0] * 252), "alpha_t": float(beta[0] / se)})
    out["carry_benchmark"] = pd.DataFrame(rows)
    # (D) literal 1.2-pip cost for SEK / NOK: verdict statistics; headline placebo with 5,000 draws
    lit = study(R, cost_pips, literal_cost=True, with_acc=False, tag="frozen")
    pl = rotation_placebo(lit["frames"], cost_pips)
    out["verdict_literal_cost"] = verdict(lit["report"], pl["table"])
    out["placebo_literal_cost"] = pl["table"]
    out["placebo_5000"] = rotation_placebo(frames, cost_pips, reps=5000, seed=11)["table"]
    return out


def eur_store_table(eur_pos: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for lab, a, b in (("2010-26", 2010, 2026), ("2016-26", 2016, 2026), ("2023-26", 2023, 2026)):
        m = (eur_pos.index.year >= a) & (eur_pos.index.year <= b)
        r = {"period": lab, "share_wider": float(eur_pos["wider"].values[m].mean())}
        for name, col in (("gated_spot", "net_bp"), ("gated_carry", "net_bp_carry"), ("ungated_spot", "net_bp_ungated"), ("ungated_carry", "net_bp_ungated_carry"),
                          ("complement_spot", "net_bp_complement"), ("complement_carry", "net_bp_complement_carry")):
            r[f"sr_{name}"], r[f"t_{name}"], _ = sr(eur_pos[col].values[m])
        rows.append(r)
    return pd.DataFrame(rows)


# ============================================================================= report (tables generated; prose written after the results)
def _md(df: pd.DataFrame) -> str:
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for _, r in df.iterrows():
        out.append("| " + " | ".join(str(r[c]) for c in cols) + " |")
    return "\n".join(out)


def _s(x, d=2):
    return "-" if x is None or not np.isfinite(x) else f"{x:+.{d}f}"


def _pc(x):
    return "-" if x is None or not np.isfinite(x) else f"{100 * x:.0f}"


def _main_table(rep: pd.DataFrame, carry: bool, names: list[str], periods=None, acc: bool = True) -> pd.DataFrame:
    q = rep[(rep.variant == "frozen") & (rep.carry == carry)]
    rows = []
    for n in names:
        for lab, _, _ in PERIODS:
            if periods and lab not in periods:
                continue
            g = q[(q.name == n) & (q.period == lab)].set_index("stream")
            if g.empty:
                continue
            u, w, c = g.loc["ungated"], g.loc["wider"], g.loc["complement"]
            r = {"currency": n.upper() if len(n) == 3 else n, "period": lab,
                 "(c) ungated SR (t)": f"{_s(u.sharpe)} ({_s(u.t, 1)})", "(d) WIDER SR (t)": f"{_s(w.sharpe)} ({_s(w.t, 1)})",
                 "complement SR (t)": f"{_s(c.sharpe)} ({_s(c.t, 1)})",
                 "on-session SR WIDER / compl.": f"{_s(w.get('onsession_sharpe_wider', np.nan))} / {_s(w.get('onsession_sharpe_complement', np.nan))}",
                 "% WIDER": _pc(w.share_wider)}
            if acc and "acc21" in g and np.isfinite(w.get("n21", np.nan)):
                r["WIDER acc 21 / 42 / 63 (n)"] = f"{_pc(w.acc21)} / {_pc(w.acc42)} / {_pc(w.acc63)} ({int(w.n21)} / {int(w.n42)} / {int(w.n63)})"
                r["compl. acc 21 / 42 / 63 (n)"] = f"{_pc(c.acc21)} / {_pc(c.acc42)} / {_pc(c.acc63)} ({int(c.n21)} / {int(c.n42)} / {int(c.n63)})"
                r["ungated acc 21 / 42 / 63"] = f"{_pc(u.acc21)} / {_pc(u.acc42)} / {_pc(u.acc63)}"
            rows.append(r)
    return pd.DataFrame(rows).fillna("-")


def write_report(res: dict) -> Path:
    rep, V, cp = res["report"], res["verdict"], res["cost_pips"]
    plc = res["placebo"].set_index("period")
    pls = res["placebo_spot"].set_index("period")
    ple = res["placebo_eur"].set_index("period")
    plr = res["placebo_rob"].set_index("period")
    dg = res["diag"]
    p5k = dg["placebo_5000"].set_index("period")
    pll = dg["placebo_literal_cost"].set_index("period")
    VL = dg["verdict_literal_cost"]
    lk = res["leak"].set_index("check")
    conc = res["repro"]["concordance"].set_index("period")
    T = res["repro"]["table"]
    eras = dg["eras"]
    frames = res["frames"]
    q = rep[(rep.variant == "frozen")]

    def cell(name, period, stream, col="sharpe", carry=True, variant="frozen"):
        g = rep[(rep.variant == variant) & (rep.carry == carry) & (rep.name == name) & (rep.period == period) & (rep.stream == stream)]
        return float(g[col].iloc[0])

    def era(name, period, col, carry=True):
        return float(eras[(eras.name == name) & (eras.carry == carry) & (eras.period == period)][col].iloc[0])

    B = lambda per, st, col="sharpe", carry=True: cell("basket8_ex_eur", per, st, col, carry)   # noqa: E731
    E = lambda per, st, col="sharpe", carry=True: cell("eur", per, st, col, carry)              # noqa: E731
    gaps = V["gaps"]
    word = "REPLICATES" if V["replicates"] else "FAILS"
    # ---------------- data table
    info = res["info"].set_index("ccy")
    drows = []
    for c in ALL9:
        f = frames[c]
        o = f[f["oos"].values]
        drows.append({"currency": c.upper(), "pair (H.10 series)": f"{CCY[c]['pair']} ({CCY[c]['h10']})", "rate series": info.loc[c, "series"],
                      "rate span": f"{info.loc[c, 'first']} .. {info.loc[c, 'last']}", "months filled (<= 3)": info.loc[c, "filled_months"] or "-",
                      "streams run": f"{o.index[0].date()} .. {o.index[-1].date()}", "sessions": len(o),
                      "cost, bp per unit turnover": f"{(cp / o['cost_px']).mean():.1f}",
                      "turnover of (c), units / year": f"{o['pos'].diff().abs().sum() / (len(o) / 252):.1f}"})
    data_tbl = pd.DataFrame(drows)
    # ---------------- EUR arm S table
    names = {"cot": "positioning sign", "spread": "2y-spread trend", "house": "house score", "agree3": "AGREEMENT RULE"}
    trows = []
    for comp in ("cot", "spread", "house", "agree3"):
        for per in ("2006-26", "2006-15", "2016-26"):
            a = T[(T.component == comp) & (T.period == per) & T.label.str.startswith("policy")].iloc[0]
            b = T[(T.component == comp) & (T.period == per) & T.label.str.startswith("3m")].iloc[0]
            trows.append({"signal": names[comp], "period": per,
                          "arm S class: SR in / out": f"{_s(a.sharpe_in)} / {_s(a.sharpe_out)}",
                          "monthly class: SR in / out": f"{_s(b.sharpe_in)} / {_s(b.sharpe_out)}",
                          "arm S class: acc 21 in / out (n)": f"{_pc(a.N21_in_acc)} / {_pc(a.N21_out_acc)} ({int(a.N21_in_n)} / {int(a.N21_out_n)})",
                          "monthly class: acc 21 in / out (n)": f"{_pc(b.N21_in_acc)} / {_pc(b.N21_out_acc)} ({int(b.N21_in_n)} / {int(b.N21_out_n)})",
                          "arm S class: acc 42 in / out": f"{_pc(a.N42_in_acc)} / {_pc(a.N42_out_acc)}",
                          "monthly class: acc 42 in / out": f"{_pc(b.N42_in_acc)} / {_pc(b.N42_out_acc)}"})
    arm_s_tbl = pd.DataFrame(trows)
    crow = []
    for per in conc.index:
        r = conc.loc[per]
        crow.append({"period": per, "sessions": int(r.sessions), "% WIDER, policy rates (arm S)": _pc(r.share_wider_policy), "% SAME, policy rates": _pc(r.share_same_policy),
                     "% WIDER, 3m interbank monthly": _pc(r.share_wider_monthly), "% sessions same class (WIDER vs not)": _pc(r.same_class),
                     "arm S WIDER also WIDER here": _pc(r.wider_policy_also_monthly), "WIDER here also arm S WIDER": _pc(r.wider_monthly_also_policy),
                     "phi": f"{r.phi:.2f}"})
    conc_tbl = pd.DataFrame(crow)
    # ---------------- placebo table
    prow = []
    for lab, P_ in (("basket of 8, spot + carry (VERDICT)", plc), ("ADDED: same, 5,000 draws", p5k), ("ADDED: same, literal 1.2 pips for SEK / NOK", pll),
                    ("basket of 8, spot only", pls), ("EUR alone, spot + carry", ple), ("ROBUSTNESS LINE 6m change / 12m gap, basket of 8", plr)):
        for per in ("2000-26", "2010-26"):
            r = P_.loc[per]
            prow.append({"sample": lab, "period": per, "WIDER stream SR (t)": f"{_s(r.basket_sr_wider)} ({_s(r.basket_t_wider, 2)})",
                         "complement SR": _s(r.basket_sr_complement), "gap G": _s(r.basket_gap),
                         "placebo G mean / 95th pct": f"{_s(r.placebo_gap_mean)} / {_s(r.placebo_gap_q95)}", "p(G_rot >= G)": f"{r.p_basket_gap:.3f}",
                         "mean on-session gap (p)": f"{_s(r.mean_onsession_gap)} ({r.p_mean_onsession_gap:.3f})",
                         "currencies with gap > 0 (p)": f"{int(r.n_ccy_gap_positive)} ({r.p_n_positive:.2f})"})
    plc_tbl = pd.DataFrame(prow)
    # ---------------- leak table
    lrow = []
    for chk in lk.index:
        r = lk.loc[chk]
        lrow.append({"check": chk, "ungated 2000-26 / 2010-26": f"{_s(r['sr_ungated_2000-26'])} / {_s(r['sr_ungated_2010-26'])}",
                     "WIDER": f"{_s(r['sr_wider_2000-26'])} / {_s(r['sr_wider_2010-26'])}",
                     "complement": f"{_s(r['sr_complement_2000-26'])} / {_s(r['sr_complement_2010-26'])}",
                     "gap WIDER - complement": f"{_s(r['gap_2000-26'])} / {_s(r['gap_2010-26'])}"})
    leak_tbl = pd.DataFrame(lrow)
    # ---------------- added tables
    erow = []
    for _, r in eras.iterrows():
        erow.append({"sample": "basket of 8" if r["name"].startswith("basket") else "EUR", "P&L": "spot + carry" if r.carry else "spot only", "period": r.period,
                     "ungated SR (t)": f"{_s(r.sr_ungated)} ({_s(r.t_ungated, 1)})", "WIDER SR (t)": f"{_s(r.sr_wider)} ({_s(r.t_wider, 1)})",
                     "complement SR (t)": f"{_s(r.sr_complement)} ({_s(r.t_complement, 1)})", "gap": _s(r.gap)})
    era_tbl = pd.DataFrame(erow)
    al = dg["alignment"]
    al_tbl = pd.DataFrame([{"currency": r.ccy.upper(), "position has the sign of the rate differential: WIDER sessions": _pc(r.aligned_with_carry_wider) + " %",
                            "complement sessions": _pc(r.aligned_with_carry_complement) + " %", "mean abs(r_c - r_US), %": f"{r.mean_abs_diff_pct:.2f}"} for _, r in al.iterrows()])
    sp = dg["split"]
    sp_tbl = pd.DataFrame([{"period": r.period, "WIDER stream: spot bp / year": f"{r.w_spot_bp_per_year:+.0f}", "WIDER stream: carry bp / year": f"{r.w_carry_bp_per_year:+.0f}",
                            "complement: spot bp / year": f"{r.c_spot_bp_per_year:+.0f}", "complement: carry bp / year": f"{r.c_carry_bp_per_year:+.0f}"} for _, r in sp.iterrows()])
    cb = dg["carry_benchmark"]
    cb_tbl = pd.DataFrame([{"period": r.period, "plain carry basket SR (t)": f"{_s(r.carry_benchmark_sr)} ({_s(r.carry_benchmark_t, 1)})",
                            "corr. with the gated WIDER basket": f"{r.corr_with_gated_wider:.2f}", "alpha of the gated basket on carry, bp / year (t)": f"{r.alpha_bp_per_year:+.0f} ({_s(r.alpha_t, 1)})"}
                           for _, r in cb.iterrows()])
    es = res["eur_store"].set_index("period")
    es_tbl = pd.DataFrame([{"period": per, "% WIDER": _pc(es.loc[per, "share_wider"]),
                            "gated (d), spot = `net_bp`": f"{_s(es.loc[per, 'sr_gated_spot'])} ({_s(es.loc[per, 't_gated_spot'], 1)})",
                            "gated (d), spot + carry": f"{_s(es.loc[per, 'sr_gated_carry'])} ({_s(es.loc[per, 't_gated_carry'], 1)})",
                            "ungated (c), spot": f"{_s(es.loc[per, 'sr_ungated_spot'])} ({_s(es.loc[per, 't_ungated_spot'], 1)})",
                            "complement, spot": f"{_s(es.loc[per, 'sr_complement_spot'])} ({_s(es.loc[per, 't_complement_spot'], 1)})"} for per in es.index])
    sens = []
    for v in [x for x in rep.variant.unique() if x != "frozen"]:
        for n in ("basket8_ex_eur", "eur"):
            r = {"variant": v, "sample": "basket of 8" if n.startswith("basket") else "EUR"}
            for per in ("2000-26", "2010-26", "2016-26", "2023-26"):
                r[per + " ungated / WIDER / compl."] = " / ".join(_s(cell(n, per, st, "sharpe", True, v)) for st in ("ungated", "wider", "complement"))
            sens.append(r)
    sens_tbl = pd.DataFrame(sens)
    cur = res["eur_pos"]
    last_cls = cur["cls"].iloc[-1]
    npos10 = int(plc.loc["2010-26", "n_ccy_gap_positive"])
    aT = T[(T.component == "agree3") & (T.period == "2006-26")]
    aS, aM = aT[aT.label.str.startswith("policy")].iloc[0], aT[aT.label.str.startswith("3m")].iloc[0]
    cT = T[(T.component == "cot") & (T.period == "2006-26")]
    cS, cM = cT[cT.label.str.startswith("policy")].iloc[0], cT[cT.label.str.startswith("3m")].iloc[0]
    sT = T[(T.component == "spread") & (T.period == "2006-26")]
    sS, sM = sT[sT.label.str.startswith("policy")].iloc[0], sT[sT.label.str.startswith("3m")].iloc[0]
    a16 = T[(T.component == "agree3") & (T.period == "2016-26") & T.label.str.startswith("3m")].iloc[0]
    a06 = T[(T.component == "agree3") & (T.period == "2006-15") & T.label.str.startswith("3m")].iloc[0]
    acc = lambda per, st, h: cell("basket8_ex_eur", per, st, f"acc{h}")   # noqa: E731
    qq = q[q.carry & (q.group == "currency") & q.period.isin(["2000-26", "2010-26"])]
    wl = []
    for h in HS:
        for _, r in qq[(qq[f"lo{h}"] > 0.5) | (qq[f"hi{h}"] < 0.5)].iterrows():
            wl.append(f"{r['name'].upper()} {r['stream']} at {h} sessions in {r['period']}: {_pc(r[f'acc{h}'])} %, n={int(r[f'n{h}'])}")
    nwil, wil_txt = len(wl), "; ".join(wl)
    txt = f"""# Arm V: divergence across G10 (`divergence_g10`) - pre-registered replication of the WIDER lead on nine currencies

Code `src/eurusd/arms/divergence_g10.py` (`run(cost_pips=1.2)`, about 70 seconds, rewrites this file). Results in
`experiments/results/arms/`: `divergence_g10_positions.parquet` (EUR/USD daily stream of the gated rule on the feature-store grid:
`pos`, `fwd_bp`, `net_bp` spot-only, plus `carry_bp`, `net_bp_carry`, `pos_ungated`, `wider`, `cls`), `divergence_g10_report.csv`
(every currency, basket, stream, period; columns `variant`, `carry`, `final`), `divergence_g10_basket.parquet` (daily basket and
per-currency streams), `divergence_g10_tables.csv` (placebo, leak checks, EUR reproduction, added diagnostics), log
`logs/divergence_g10.log`. The frozen definitions and the verdict rule are in the module docstring and were written before any
result; only data availability had been looked at. What was added after the first run is marked ADDED and is outside the verdict.

## Verdict: {word}
**The divergence mechanism does not replicate. By the pre-registered rule it fails, narrowly on paper and clearly in substance.**

| criterion (eight-currency basket ex EUR, spot + carry, net) | required | observed | |
|---|---|---|---|
| (i) gated-WIDER stream: Sharpe > 0 in 2000-26 and 2010-26, pooled t (2000-26) >= 2 | t >= 2.00 | Sharpe {_s(V['sr_wider_2000'])} / {_s(V['sr_wider_2010'])}, t **{V['t_wider_2000']:.2f}** (2010-26: t {V['t_wider_2010']:.2f}) | {'pass' if V['i'] else '**fail**'} |
| (ii) on-session Sharpe WIDER minus complement > 0, 2000-26 | >= 6 of 8 | **{V['n_positive']} of 8** ({', '.join(f"{c.upper()} {_s(g)}" for c, g in gaps.items())}) | {'pass' if V['ii'] else '**fail**'} |
| (iii) rotation placebo, 500 draws: share of draws with a basket gap at least as large | <= 0.050 | gap {_s(plc.loc['2000-26', 'basket_gap'])}, p = **{V['placebo_p']:.3f}** | {'pass' if V['iii'] else '**fail**'} |

1. **A near miss in the full sample.** (i) misses by 0.02 of a t-statistic and (iii) by 0.006 of a p-value. ADDED checks of how
   fragile that is: with 5,000 placebo draws p = {p5k.loc['2000-26', 'p_basket_gap']:.3f}; with the literal 1.2-pip cost for USDSEK / USDNOK (I had
   declared 30 pips for those two before the run, see below) t = {VL['t_wider_2000']:.2f} and p = {VL['placebo_p']:.3f}, so (i) would pass and (iii) would
   still fail. The labelled 6 / 12-month robustness line reads t {plr.loc['2000-26', 'basket_t_wider']:.2f} and p {plr.loc['2000-26', 'p_basket_gap']:.3f} (it cannot enter the verdict). Under either
   cost convention the verdict is FAILS; nobody should read 1.98 against 2.00 as a refutation by itself.
2. **What decides it is where the number comes from: 2000-09, reversed in 2010-15, weak since.** Basket gated-WIDER Sharpe {_s(era('basket8_ex_eur', '2000-09', 'sr_wider'))}
   (t {_s(era('basket8_ex_eur', '2000-09', 't_wider'), 1)}) in 2000-09 and {_s(B('2010-26', 'wider'))} (t {_s(B('2010-26', 'wider', 't'), 1)}) in 2010-26, {_s(B('2016-26', 'wider'))} in 2016-26,
   {_s(B('2023-26', 'wider'))} in 2023-26. In 2010-26 the WIDER-minus-complement gap is {_s(plc.loc['2010-26', 'basket_gap'])} with placebo p {plc.loc['2010-26', 'p_basket_gap']:.2f} and positive in
   {npos10} of 8 currencies. In the window of the EUR lead itself (2006-26, ADDED) the basket shows {_s(era('basket8_ex_eur', '2006-26', 'sr_wider'))} (t {_s(era('basket8_ex_eur', '2006-26', 't_wider'), 1)})
   inside WIDER against {_s(era('basket8_ex_eur', '2006-26', 'sr_complement'))} outside. 2016-26 is the one stretch after 2009 with the right sign ({_s(B('2016-26', 'wider'))}, t {_s(B('2016-26', 'wider', 't'), 1)},
   against {_s(B('2016-26', 'complement'))} outside; spot only {_s(B('2016-26', 'wider', carry=False))} against {_s(B('2016-26', 'complement', carry=False))}), far from significant, and 2010-15 has the opposite sign ({_s(era('basket8_ex_eur', '2010-15', 'sr_wider'))} inside, {_s(era('basket8_ex_eur', '2010-15', 'sr_complement'))} outside). Nothing
   outside EUR supports the lead at conventional levels in the years it was found on.
3. **And it is carry, not persistence of trends.** A rate differential that is getting wider is, most of the time, moving away from
   zero, so "long the currency whose relative rate rose" is then "long the high yielder": on WIDER sessions the position has the
   sign of the differential {_pc(al.aligned_with_carry_wider.min())}-{_pc(al.aligned_with_carry_wider.max())} % of the time, on complement sessions {_pc(al.aligned_with_carry_complement.min())}-{_pc(al.aligned_with_carry_complement.max())} %
   (ADDED). The gate therefore sorts the same rule into "earn carry" and "pay carry". Spot only, the basket is {_s(B('2000-26', 'wider', carry=False))}
   (t {_s(B('2000-26', 'wider', 't', False), 1)}) inside WIDER against {_s(B('2000-26', 'complement', carry=False))} outside, gap {_s(pls.loc['2000-26', 'basket_gap'])}, placebo p {pls.loc['2000-26', 'p_basket_gap']:.2f}; in 2010-26 {_s(B('2010-26', 'wider', carry=False))}
   against {_s(B('2010-26', 'complement', carry=False))}. The plain carry trade with the same vol scale earned {_s(cb.carry_benchmark_sr.iloc[1])} in 2000-09 and {_s(cb.carry_benchmark_sr.iloc[3])} in 2010-26; the gated
   stream is {cb.corr_with_gated_wider.iloc[0]:.2f} correlated with it and its alpha on it has t {_s(cb.alpha_t.iloc[0], 1)} (2000-26) and {_s(cb.alpha_t.iloc[3], 1)} (2010-26).
4. **Stale placebo.** With the rate data six months older the gap is still {_s(lk.loc['(2) stale placebo: rate data lagged +6 months', 'gap_2000-26'])} (live {_s(plc.loc['2000-26', 'basket_gap'])}); by the house rule a
   slow signal that scores the same when stale is a regime bet (here: the carry regime before 2008), not timing information.
5. **EUR/USD itself does not show it under these definitions.** Frozen rule on EUR/USD: gated {_s(E('2000-26', 'wider'))} against complement
   {_s(E('2000-26', 'complement'))} (2000-26), {_s(E('2010-26', 'wider'))} against {_s(E('2010-26', 'complement'))} (2010-26); spot only {_s(E('2000-26', 'wider', carry=False))} against {_s(E('2000-26', 'complement', carry=False))}; placebo p {ple.loc['2000-26', 'p_basket_gap']:.2f}.
   More important, arm S's own signals lose most of their concentration when the class is built from monthly 3-month interbank
   rates instead of daily policy rates (2006-26): positioning {_s(cM.sharpe_in)} inside / {_s(cM.sharpe_out)} outside (arm S: {_s(cS.sharpe_in)} / {_s(cS.sharpe_out)}), 2y-spread
   trend {_s(sM.sharpe_in)} / {_s(sM.sharpe_out)} (arm S: {_s(sS.sharpe_in)} / {_s(sS.sharpe_out)}), agreement rule Sharpe {_s(aM.sharpe_in)} / {_s(aM.sharpe_out)} (arm S: {_s(aS.sharpe_in)} / {_s(aS.sharpe_out)}) and accuracy
   {_pc(aM.N21_in_acc)} % / {_pc(aM.N42_in_acc)} % inside against {_pc(aM.N21_out_acc)} % / {_pc(aM.N42_out_acc)} % outside (arm S: {_pc(aS.N21_in_acc)} / {_pc(aS.N42_in_acc)} against {_pc(aS.N21_out_acc)} / {_pc(aS.N42_out_acc)}). The two classes
   agree on {_pc(conc.loc['2006-26', 'same_class'])} % of sessions ({_pc(conc.loc['2006-15', 'same_class'])} % in 2006-15, {_pc(conc.loc['2016-26', 'same_class'])} % in 2016-26). Where they agree (2016-26) the agreement rule keeps its
   concentration ({_s(a16.sharpe_in)} inside, {_s(a16.sharpe_out)} outside); in 2006-15 it reverses ({_s(a06.sharpe_in)} inside, {_s(a06.sharpe_out)} outside).

**Plain statement required by the brief: the WIDER lead is likely a third EUR-specific artefact** (after the positioning trend
and residual order flow), and on EUR/USD it is also specific to one way of measuring the policy gap. Step 4 was not run.

**What it means for the engine.** (i) Do not gate the engine on WIDER and do not make "rate-differential trend gated by WIDER" a
rule: on EUR/USD it is {_s(es.loc['2010-26', 'sr_gated_spot'])} / {_s(es.loc['2016-26', 'sr_gated_spot'])} / {_s(es.loc['2023-26', 'sr_gated_spot'])} (2010-26 / 2016-26 / 2023-26, feature-store grid, spot), far below the bar.
(ii) Keep the unconditional agreement rule as the primary rule, at the planning level arm S gave (Sharpe 0.3-0.5). (iii) The paper
scenario `agreement_wider` can keep running because it costs nothing, but it should be read as a scenario whose prior is now
"probably chance"; showing the policy-gap direction next to a call remains harmless context. (iv) No currency outside EUR is a
candidate either: the only positive pocket is SEK ({_s(cell('sek', '2010-26', 'wider'))} gated in 2010-26, t {_s(cell('sek', '2010-26', 'wider', 't'), 1)}), one of eight, not selected for in advance.
Monthly class of EUR/USD on the last session ({cur.index[-1].date()}): {last_cls}.

## Frozen definitions (module docstring, written before any result)
* Currencies EUR, GBP, JPY, CHF, AUD, CAD, NZD, SEK, NOK against USD; identical test for all; EUR is the reference, the other
  eight are the replication sample.
* `d_c(m) = r_c(m) - r_US(m)`, monthly 3-month interbank rates (FRED `IR3TIB01xxM156N`). An observation of month m is usable from
  month end + 30 days, plus one calendar day. Missing months are filled with the previous value for at most three months.
* Policy gap `|d_c|`: WIDER if larger than six months earlier, NARROWER if smaller, SAME if equal; complement = NARROWER or SAME.
* (c) rate-differential trend: `sign(d_c(m) - d_c(m-3))` (+1 = long the foreign currency), position = sign x
  clip(training-median rv_21d / rv_21d, 0, 1.5), set on the first session a new month is usable and held (monthly rebalanced);
  walk-forward through `eurusd.wf.walk_forward`, test years 2000-2026 (the vol median is the only fitted number).
* (d) gated: (c) on WIDER sessions, flat otherwise; complement: (c) on NARROWER / SAME sessions. With and without carry
  ((r_c - r_US) x 100 / 252 bp per session on the position) = 6 streams. Primary P&L = spot + carry.
* Prices: Fed H.10 noon rates from FRED, in "foreign currency vs USD" direction. Cost {cp} pips of the conventional pair per unit
  turnover; **declared deviation from the brief:** USDSEK and USDNOK are charged 30 pips (about 3-4 bp) because 1.2 pips of a
  10-kroner rate is 0.1 bp, as arm F did for USDMXN; the literal version is in the sensitivity table and in the verdict section.
* Stream Sharpe / t: daily net bp over all sessions with a defined class (flat sessions zero). On-session Sharpe (the statistic
  of the arm S lead): the ungated stream on the sessions of the class. Accuracy: sign(s) x h-session spot return > 0 on greedy
  non-overlapping decisions. Basket: equal weight of the currencies with a defined class on the day.
* Verdict rule, placebo design (same rotation offset for all currencies, at least a year, 500 draws, seed 7) and leak checks as in
  the table above and in section 5. Windows 3 and 6 months were not varied; the 6 / 12 alternative is one labelled line.
* Trials: 6 frozen streams + 1 robustness line. Sensitivities (2x cost, literal cost) change no definition.

## 1. Data, spans, lags
{_md(data_tbl)}

* US rate: `IR3TIB01USM156N`, {info.loc['us', 'first']} .. {info.loc['us', 'last']}, one missing month ({info.loc['us', 'filled_months']}) filled with the previous value.
* Euro area: `IR3TIB01EZM156N` ends 2026-01 on FRED; from {info.loc['eur', 'ez_extended_from']} it is continued with `IR3TIB01DEM156N` (Germany), which is the
  same 3-month Euribor (difference below 0.02 points in every month since 1999, asserted). GBP: the FRED series ends 2026-01,
  is carried three months and GBP leaves the basket on {frames['gbp'][frames['gbp']['oos'].values].index[-1].date()}. JPY starts 2002-04, CHF 1999-07 (first sessions in the table).
* New files this arm fetched from FRED (`fredgraph.csv`, curl --http1.1): `fred_DEXSDUS.csv`, `fred_DEXNOUS.csv` (H.10, 1971 ..
  2026-11-06), `fred_IR3TIB01SEM156N.csv` (1982-01 .. 2026-09), `fred_IR3TIB01NOM156N.csv` (1979-01 .. 2026-09). Publication lag
  used for every rate series: month end + 30 days (+1 day). H.10 prices: the price of the decision day (noon New York).
* Daily 2y yields exist in the repo only for EUR and USD and were not used, so the measure is the same for all nine.
* EUR H.10 starts 1999-01-04, so its vol target for 2000-03 rests on 1-4 years; the others have ten years before 2000.

## 2. Step 1 - EUR/USD reproduction with the monthly definitions
(a) The class itself, feature-store sessions:

{_md(conc_tbl)}

Policy rates move in steps and sit still for long stretches (SAME on {_pc(conc.loc['2006-26', 'share_same_policy'])} % of sessions, {_pc(conc.loc['2006-15', 'share_same_policy'])} % in 2006-15); a monthly average of
interbank rates is never exactly unchanged and in 2007-12 it also carries the Libor / Euribor credit premium, which is not policy.
Nearly every arm S WIDER session after 2016 is also WIDER here ({_pc(conc.loc['2016-26', 'wider_policy_also_monthly'])} %), but the monthly class adds as many sessions again.

(b) Arm S's own table (`regime_dependence.regime_tables`, daily-sign streams, feature-store grid, spot, 1.2 pips) with the two
classes; "in" = WIDER sessions, "out" = the other sessions with a defined class:

{_md(arm_s_tbl)}

The first column pair reproduces arm S exactly (positioning 1.34 / 0.12, spread trend 0.95 / 0.10, agreement rule 64 % / 70 %
against 51 % / 49 %). With the monthly class the 2006-26 contrast shrinks to a fraction for positioning, vanishes for the spread
trend and reverses in Sharpe for the agreement rule; the distance is entirely 2006-15, where the two classes agree on only
{_pc(conc.loc['2006-15', 'same_class'])} % of sessions. So the monthly-rate version is NOT close to arm S's version before 2016 and close after it.

(c) The frozen rule on EUR/USD (H.10 grid) is the EUR row of the next table. ADDED: the same rule on the feature-store grid
(the delivered positions file; store volatility, walk-forward 2010-26; Sharpe (t)):

{_md(es_tbl)}

## 3. Step 2 - per currency and basket (frozen rule, spot + carry, net; Sharpe with t in brackets)
{_md(_main_table(rep, True, ALL9 + ['basket8_ex_eur']))}

Basket accuracy pools the eight currencies' decisions (cross-correlated; no interval claimed). Pooled non-overlapping accuracy
inside WIDER is {_pc(acc('2000-26', 'wider', 21))} / {_pc(acc('2000-26', 'wider', 42))} / {_pc(acc('2000-26', 'wider', 63))} % at 21 / 42 / 63 sessions against {_pc(acc('2000-26', 'complement', 21))} / {_pc(acc('2000-26', 'complement', 42))} / {_pc(acc('2000-26', 'complement', 63))} % outside (2000-26) and {_pc(acc('2010-26', 'wider', 21))} / {_pc(acc('2010-26', 'wider', 42))} / {_pc(acc('2010-26', 'wider', 63))} %
against {_pc(acc('2010-26', 'complement', 21))} / {_pc(acc('2010-26', 'complement', 42))} / {_pc(acc('2010-26', 'complement', 63))} % in 2010-26: a coin in both classes. Per currency the Wilson intervals (in the csv) are about +-8 points
at 21 sessions; of the 162 currency x stream x horizon cells of 2000-26 and 2010-26, {nwil} exclude 50 % ({wil_txt}),
which is what chance gives.

Spot only (no carry in the P&L):

{_md(_main_table(rep, False, ALL9 + ['basket8_ex_eur'], periods=('2000-26', '2010-26'), acc=False))}

Basket including EUR (9 currencies, spot + carry): gated {_s(cell('basket9_incl_eur', '2000-26', 'wider'))} (t {_s(cell('basket9_incl_eur', '2000-26', 'wider', 't'), 1)}) / {_s(cell('basket9_incl_eur', '2010-26', 'wider'))} / {_s(cell('basket9_incl_eur', '2016-26', 'wider'))} / {_s(cell('basket9_incl_eur', '2023-26', 'wider'))}.

Sensitivities and the single robustness line (basket of 8 and EUR, spot + carry, Sharpe):

{_md(sens_tbl)}

The 6-month-change / 12-month-gap line gives the same picture (basket gated {_s(plr.loc['2000-26', 'basket_sr_wider'])}, t {plr.loc['2000-26', 'basket_t_wider']:.2f}, in 2000-26; {_s(plr.loc['2010-26', 'basket_sr_wider'])} in 2010-26
with a gap of {_s(plr.loc['2010-26', 'basket_gap'])}). It is not eligible and was not used.

## 4. Step 3 - rotation placebo and the verdict
{_md(plc_tbl)}

G = Sharpe of the basket WIDER stream minus Sharpe of the basket complement stream. Rotating the class series against the
positions leaves the unconditional Sharpe of the rule in place and asks only whether the TIMING of the WIDER label matters.
Verdict by the frozen rule: (i) {'pass' if V['i'] else 'fail'}, (ii) {'pass' if V['ii'] else 'fail'}, (iii) {'pass' if V['iii'] else 'fail'} -> **{word}**.

ADDED after the first run (outside the verdict) - eras:

{_md(era_tbl)}

ADDED - is the gate a carry sort? Share of active sessions on which the position of rule (c) has the sign of `r_c - r_US`:

{_md(al_tbl)}

ADDED - spot and carry parts of the two basket streams (gross bp a year, before costs):

{_md(sp_tbl)}

ADDED - benchmark, not a candidate: plain carry `sign(r_c - r_US)` with the same vol scale and monthly rebalance, basket of 8:

{_md(cb_tbl)}

In 2000-09 the WIDER stream earned more than carry alone (spot {sp.w_spot_bp_per_year.iloc[1]:+.0f} bp a year next to {sp.w_carry_bp_per_year.iloc[1]:+.0f} of carry; alpha on the carry
basket t {_s(cb.alpha_t.iloc[1], 1)}): that decade was the one-way dollar decline with rate differentials widening in favour of AUD, NZD, SEK and GBP.
Since 2010 the spot part is {sp.w_spot_bp_per_year.iloc[3]:+.0f} bp a year and only the carry accrual ({sp.w_carry_bp_per_year.iloc[3]:+.0f}) is left.

## 5. Leak checks (basket of 8, spot + carry; Sharpe 2000-26 / 2010-26)
{_md(leak_tbl)}

* (1) Shuffled forward returns: about zero (the small negative mean is costs plus the 0.19 s.d. of a 27-year Sharpe; the first
  run's five seeds happened to average -0.21 and I extended the check to 40). Class labels shuffled by month: the gap goes to
  {_s(lk.loc['(1) class labels shuffled by month, mean of 20 seeds', 'gap_2000-26'])} +- {lk.loc['(1) class labels shuffled by month, sd of 20 seeds', 'gap_2000-26']:.2f} (real {_s(plc.loc['2000-26', 'basket_gap'])}), i.e. it vanishes; 2 s.d. of that shuffle is the size of the real gap.
* (2) One more month of lag changes nothing in the gap; three more months remove it, six more months bring three quarters of
  it back. A gap that returns when the data are half a year old is a slow state (carry regime), not information.
* (3) Look-ahead control: removing the publication lag changes nothing ({_s(lk.loc['(3) look-ahead: no publication lag (stamped at month end)', 'sr_ungated_2000-26'])} against {_s(lk.loc['as run (frozen rule, basket of 8, spot + carry)', 'sr_ungated_2000-26'])} ungated), so the result does not sit on the
  edge of the lag; knowing the month's average one and two months early gives {_s(lk.loc['(3) look-ahead: known one month before the month starts', 'sr_ungated_2000-26'])} and {_s(lk.loc['(3) look-ahead: known two months before the month starts', 'sr_ungated_2000-26'])} (t 3.8 and 5.1): the harness exposes
  foresight, and rate differentials and currencies move together within the quarter, which is why the honest lag leaves little.
* Inputs: monthly interbank rates (lagged), H.10 prices, trailing realised volatility. No forward return enters a signal or a
  class. Current-vintage OECD rates (monthly averages are not revised in any way that matters).

## Caveats
* This arm tests the MECHANISM with a rate-differential trend rule; it cannot test the agreement rule on other currencies (no
  house score or validated positioning signal exists there). A failure of the mechanism does not prove the EUR pattern is
  chance, but together with section 2 (the pattern depends on how the gap is measured) nothing independent now supports it.
* Three-month interbank rates are not policy rates: in 2007-12 and March 2020 they carry credit and liquidity premia. Policy
  rates for nine central banks were not in the repo; the brief fixed the interbank rate as the primary measure for all.
* The verdict was a near miss on two thresholds; the reading above rests on the era split and the carry decomposition, both
  ADDED after the first run and therefore descriptive. The pre-registered answer is FAILS either way.
* H.10 is a noon New York fix. The basket weights currencies equally in position units, not in risk units. 2026 runs to 6 November.
"""
    path = REPORTS / f"arm_{ARM}.md"
    path.write_text(txt)
    return path


# ============================================================================= driver
def run(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    """Returns (EUR/USD gated positions Series, report DataFrame); `run_all` also returns every table."""
    pos, rep, _ = run_all(cost_pips, write, verbose)
    return pos, rep


def run_all(cost_pips: float = 1.2, write: bool = True, verbose: bool = True):
    fetch_missing(verbose)
    R, info = load_rates()
    main = study(R, cost_pips)
    rep = main["report"]
    frames = main["frames"]
    plc = rotation_placebo(frames, cost_pips)
    plc_spot = rotation_placebo(frames, cost_pips, carry=False)
    plc_eur = rotation_placebo(frames, cost_pips, members=["eur"])
    V = verdict(rep, plc["table"])
    # sensitivities (labelled; not in the verdict)
    sens = [study(R, cost_pips, sig_k=6, gap_k=12, with_acc=False, tag="ROBUSTNESS 6m change / 12m gap")["report"],
            study(R, 2 * cost_pips, with_acc=False, tag="sensitivity 2x cost")["report"],
            study(R, cost_pips, literal_cost=True, with_acc=False, tag="sensitivity literal 1.2 pips SEK NOK")["report"]]
    rob = study(R, cost_pips, sig_k=6, gap_k=12, with_acc=False, tag="rob")
    plc_rob = rotation_placebo(rob["frames"], cost_pips)
    rep_all = pd.concat([rep] + sens, ignore_index=True)
    rep_all["final"] = (rep_all.variant == "frozen") & (rep_all.name == "eur") & (rep_all.stream == "wider") & rep_all.carry
    lk = leak_checks(R, frames, cost_pips)
    eur_pos, _ = eurusd_store(R, cost_pips)
    repro = eur_reproduction(R, cost_pips)
    diag = added_diagnostics(R, main, cost_pips)
    est = eur_store_table(eur_pos)
    res = {"diag": diag, "eur_store": est, "info": info, "report": rep_all, "placebo": plc["table"], "placebo_spot": plc_spot["table"], "placebo_eur": plc_eur["table"],
           "placebo_rob": plc_rob["table"], "verdict": V, "leak": lk, "eur_pos": eur_pos, "repro": repro, "frames": frames,
           "streams": main["streams"], "cost_pips": cost_pips, "placebo_draws": plc["draws"]}
    if write:
        OUT.mkdir(parents=True, exist_ok=True)
        eur_pos.to_parquet(OUT / f"{ARM}_positions.parquet")
        rep_all.to_csv(OUT / f"{ARM}_report.csv", index=False)
        B = main["streams"][(True, "basket8")].copy()
        Bs = main["streams"][(False, "basket8")]
        bk = pd.DataFrame({"net_bp": B["net_wider"], "pos": B["pos_wider"], "net_ungated": B["net_ungated"], "net_complement": B["net_complement"],
                           "net_wider_spot": Bs["net_wider"], "net_ungated_spot": Bs["net_ungated"], "net_complement_spot": Bs["net_complement"],
                           "share_wider": B["share_wider"], "n_ccy": B["n_ccy"]})
        for c in ALL9:
            s = main["streams"][True][c]
            bk[f"net_wider_{c}"] = s["net_wider"]; bk[f"net_ungated_{c}"] = s["net_ungated"]
            bk[f"pos_ungated_{c}"] = s["pos_ungated"]; bk[f"wider_{c}"] = s["is_wider"].astype(float)
        bk.to_parquet(OUT / f"{ARM}_basket.parquet")
        extra = pd.concat([plc["table"].assign(table="placebo basket8, spot + carry (verdict)"),
                           plc_spot["table"].assign(table="placebo basket8, spot only"),
                           plc_eur["table"].assign(table="placebo EUR alone, spot + carry"),
                           plc_rob["table"].assign(table="placebo basket8, ROBUSTNESS 6m / 12m"),
                           lk.assign(table="leak"), repro["concordance"].assign(table="eur_concordance"),
                           repro["table"].assign(table="eur_arm_s_table"), info.assign(table="rate_data"),
                           diag["eras"].assign(table="ADDED eras"), diag["alignment"].assign(table="ADDED carry alignment"),
                           diag["split"].assign(table="ADDED spot / carry split of the basket"),
                           diag["carry_benchmark"].assign(table="ADDED plain carry benchmark"),
                           diag["placebo_literal_cost"].assign(table="ADDED placebo basket8, literal 1.2 pips SEK NOK"),
                           diag["placebo_5000"].assign(table="ADDED placebo basket8, 5000 draws"),
                           pd.DataFrame([{k: v for k, v in diag["verdict_literal_cost"].items() if k != "gaps"}]).assign(table="ADDED verdict, literal cost"),
                           pd.DataFrame([{k: v for k, v in V.items() if k != "gaps"}]).assign(table="verdict"),
                           est.assign(table="ADDED EUR/USD feature-store stream")], ignore_index=True)
        extra.to_csv(OUT / f"{ARM}_tables.csv", index=False)
        write_report(res)
    if verbose:
        _print(res)
    return eur_pos["pos"], rep_all, res


def _print(res: dict) -> None:
    pd.set_option("display.width", 260, "display.max_rows", 500, "display.max_columns", 60)
    rep = res["report"]
    print(res["info"].to_string())
    q = rep[(rep.variant == "frozen")]
    for carry in (True, False):
        g = q[q.carry == carry]
        pv = g.pivot_table(index=["name", "period"], columns="stream", values=["sharpe", "t"], sort=False)
        ex = g[g.stream == "wider"].set_index(["name", "period"])[["share_wider", "onsession_sharpe_wider", "onsession_sharpe_complement", "onsession_gap"]]
        print(f"\n== frozen rule, carry={carry}")
        print(pd.concat([pv, ex], axis=1).round(2).to_string())
    a = q[q.carry & q.stream.isin(["wider", "complement", "ungated"])]
    cols = ["name", "period", "stream"] + [f"{k}{h}" for h in HS for k in ("acc", "n")]
    print("\n== accuracy, non-overlapping\n", a[cols].round(3).to_string())
    for k in ("placebo", "placebo_spot", "placebo_eur", "placebo_rob"):
        print(f"\n== {k}\n", res[k].round(3).T.to_string())
    print("\n== verdict\n", res["verdict"])
    print("\n== leak\n", res["leak"].round(2).to_string())
    print("\n== EUR concordance\n", res["repro"]["concordance"].round(3).to_string())
    print("\n== EUR arm S table\n", res["repro"]["table"].round(3).to_string())
    for k, v in res["diag"].items():
        print(f"\n== ADDED {k}\n", v.round(3).T.to_string() if isinstance(v, pd.DataFrame) and "placebo" in k else (v.round(3).to_string() if isinstance(v, pd.DataFrame) else v))
    print("\n== EUR/USD feature-store stream\n", res["eur_store"].round(2).T.to_string())
    for v in rep.variant.unique():
        if v == "frozen":
            continue
        g = rep[(rep.variant == v) & rep.carry & (rep.name.isin(["basket8_ex_eur", "eur"]))]
        print(f"\n== {v}\n", g.pivot_table(index=["name", "period"], columns="stream", values=["sharpe", "t"], sort=False).round(2).to_string())


if __name__ == "__main__":
    run()
