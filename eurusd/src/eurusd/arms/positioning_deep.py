"""Arm G ("positioning_deep"): does the STRUCTURE of the CFTC data add to the crude positioning rule?

The only positioning rule used so far is sign(52-week z-score of legacy non-commercial net / open interest) x vol
scale (arms/regime_trend.py `cot_uncond`; live component D). This arm tests whether the richer structure of the
Commitments-of-Traders reports improves on it. Every signal is a daily EUR/USD position in [-1, 1], built from weekly
report rows that become usable at report date + 6 days (and then pass through the feature store's one-calendar-day
lag, exactly as `featstore.py` does for cot_z52), multiplied by the live vol scale clip(median_train(rv_21d_bp) /
rv_21d_bp, 0, 1.5) and clipped to [-1, 1]. The only quantity fitted is the vol target (training-window median, yearly
expanding walk-forward via eurusd.wf). All signal definitions, thresholds and directions below are fixed a priori.

DATA (weekly, `data/macro/cot_eurofx_deep.csv`, built by `build_deep()` from the raw CFTC zips):
  legacy futures-only 1999-01..: non-commercial / commercial / non-reportable long & short, spreading, open interest,
      trader counts (non-commercial long / short, total), top-4 / top-8 net and gross concentration ratios.
  TFF 2006-06..: dealer / asset manager / leveraged funds / other reportable / non-reportable long & short, trader counts
      per group, concentration. 2010-07.. is the project's existing file; 2006-06..2010-07 comes from the CFTC history
      file fin_fut_txt_2006_2016.zip (new raw data, same source, identical to the existing file on the 337-week overlap).
  A TFF-based signal is LIVE from the first test year with >= 5 calendar years of TFF history before it: 2012.
  Legacy-based signals are live from 2010 (the first walk-forward test year).

NOTATION  x/OI = net (or gross) position as a fraction of open interest; zW(x) = (x - mean_W) / std_W over the trailing
W weekly reports; dK(x) = change over K reports.

BASELINE (not a candidate): `base_nc_z52` = sign(z52(non-commercial net / OI)).

THE 12 CANDIDATES (declared before any result was computed):
  theme 1, who is informed (TFF)
    am_z52         sign(z52(asset-manager net / OI))
    lev_z52        sign(z52(leveraged-funds net / OI))
    am_lev_agree   (sign(z52 AM) + sign(z52 LEV)) / 2      -> flat when the two groups disagree
  theme 2, flows vs levels (legacy non-commercial)
    flow_combo     mean of sign(d1), sign(d4), sign(d13) of net / OI
    flow_build13   1[d13(long/OI) > 0] - 1[d13(short/OI) > 0]   (new longs vs new shorts)
    flow_cover13   1[d13(short/OI) < 0] - 1[d13(long/OI) < 0]   (short covering vs long liquidation)
  theme 3, crowding / extremes (legacy non-commercial z52)
    ext_flat       baseline, but flat when |z52| > 2
    ext_fade       baseline, but reversed when |z52| > 2
  theme 4, open-interest dynamics
    oi_conviction  baseline, only while open interest is higher than 13 reports ago (d13 log OI > 0), else flat
  theme 5, trader counts
    breadth_z52    sign(z52((nL - nS) / (nL + nS))), nL / nS = number of non-commercial traders long / short
  theme 7, positioning x price divergence
    div_follow_pos sign(d13 net/OI) when it differs from the sign of the EUR/USD change over the same 13 report weeks
                   (speculators adding against the price move), else flat
  composite
    deep_combo     equal-weight mean of base_nc_z52, am_z52, lev_z52, sign(d13 net/OI), breadth_z52 (those that are live)

DIAGNOSTICS (never eligible for selection; they only describe): the other TFF groups (dealer fade, other reportables,
non-reportables), legacy commercial fade and non-reportables, AM-minus-LEV disagreement, single flow horizons, gross
long / short level z-scores, complements of the gated candidates, top-4 concentration, baseline split by agreement
with the 6-month price trend, z-score windows 26/52/104/156 (robustness table, theme 6), publication-lag table,
P&L of the baseline by |z52| bucket (extremes analysis).

NOTE ADDED AFTER THE FIRST RUN (definitions above were not changed): flow_build13 and flow_cover13 are algebraically
the same series, (sign d13(long/OI) - sign d13(short/OI)) / 2, because d13 is never exactly zero - a definition error.
So 12 candidates were declared but only 11 are distinct. The intended split (is a net inflow driven by the long leg
or by the short leg?) is reported as post-hoc diagnostics `diag_posthoc_build13` / `diag_posthoc_cover13`
(sign(d13 net) attributed to "building" when the leg that grew dominates, to "covering / liquidation" when the leg
that shrank dominates); they are not eligible for selection.

SELECTION RULE (declared before results): the final variant is the candidate with the highest 2010-2015 walk-forward
NET Sharpe at 1.2 pips of its stream as delivered (zero position where it is not live, which penalises the shorter
TFF history by roughly sqrt(live years / 6)). Its full record is then reported and it is JUDGED on 2016-2026 against
the baseline, standalone and in the three-way combination test (eurusd.arms.meta). Nothing is chosen on 2016-2026.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.wf import walk_forward, pnl_from_positions, report, _agg  # noqa: E402
from eurusd.featstore import _align_lagged  # noqa: E402

FEATURES = ROOT / "data/processed/features_daily.parquet"
MACRO = ROOT / "data/macro"
RAW_CFTC = ROOT / "data/raw/cftc"
RES = ROOT / "experiments/results/arms"
DEEP = MACRO / "cot_eurofx_deep.csv"
ARM = "positioning_deep"
EUROFX_CODE = "099741"
TFF_HIST = "fin_fut_txt_2006_2016.zip"
TFF_HIST_URL = "https://www.cftc.gov/files/dea/history/" + TFF_HIST
PUB_LAG_DAYS = 6          # report Tuesday -> published Friday 15:30 ET -> usable from the following Monday
VOL_CAP = 1.5
EXTREME_Z = 2.0
TFF_LIVE_YEAR = 2012      # first test year with >= 5 calendar years of TFF history (TFF starts 2006-06-13)
LEGACY_LIVE_YEAR = 2010
PERIODS = ("2010-2026", "2016-2026", "2023-2026", "2010-2015", "2016-2022")

CANDIDATES = ["am_z52", "lev_z52", "am_lev_agree", "flow_combo", "flow_build13", "flow_cover13", "ext_flat", "ext_fade",
              "oi_conviction", "breadth_z52", "div_follow_pos", "deep_combo"]
BASELINE = "base_nc_z52"


# ----------------------------------------------------------------------------- weekly data
def _read_zip(p: Path) -> pd.DataFrame:
    with zipfile.ZipFile(p) as z:
        names = [n for n in z.namelist() if n.lower().endswith(".txt")]
        with z.open(names[0]) as fh:
            df = pd.read_csv(fh, dtype=str, low_memory=False, encoding="latin-1")
    df.columns = [c.strip() for c in df.columns]
    return df


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.astype(str).str.strip().str.replace(",", ""), errors="coerce")


def _fetch_tff_history() -> Path | None:
    p = RAW_CFTC / TFF_HIST
    if p.exists() and p.stat().st_size > 1000:
        return p
    try:
        import requests
        r = requests.get(TFF_HIST_URL, headers={"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"}, timeout=60)
        if r.content[:2] == b"PK":
            RAW_CFTC.mkdir(parents=True, exist_ok=True)
            p.write_bytes(r.content)
            return p
    except Exception as e:   # offline: fall back to the 2010+ yearly files
        print("  TFF 2006-2016 history not available:", repr(e)[:120])
    return None


def build_deep(force: bool = False) -> pd.DataFrame:
    """Weekly EURO FX rows with the full structure (legacy 1999+, TFF 2006+). Cached in data/macro/cot_eurofx_deep.csv."""
    if DEEP.exists() and not force:
        return pd.read_csv(DEEP, parse_dates=["report_date"]).set_index("report_date")
    # --- TFF
    files = sorted(RAW_CFTC.glob("fut_fin_txt_*.zip"))
    hist = _fetch_tff_history()
    frames = []
    for p in ([hist] if hist else []) + files:       # yearly files last: they win on duplicated dates
        df = _read_zip(p)
        df = df[df["CFTC_Contract_Market_Code"].str.strip() == EUROFX_CODE].copy()
        dc = [c for c in df.columns if c.startswith("Report_Date")]
        rd = df[dc[0]]
        for c in dc[1:]:
            rd = rd.combine_first(df[c])
        rd = rd.str.strip()
        iso = rd.str.match(r"^\d{4}-\d{2}-\d{2}$").all()   # the 2006-2016 history file uses "MM/DD/YYYY 12:00:00 AM"
        df["report_date"] = pd.to_datetime(rd, format="%Y-%m-%d" if iso else "%m/%d/%Y %I:%M:%S %p")
        frames.append(df)
    t = pd.concat(frames, ignore_index=True).drop_duplicates("report_date", keep="last").sort_values("report_date").set_index("report_date")
    tcols = {"Open_Interest_All": "tff_oi", "Traders_Tot_All": "tff_traders_total",
             "Conc_Net_LE_4_TDR_Long_All": "tff_conc4_net_long", "Conc_Net_LE_4_TDR_Short_All": "tff_conc4_net_short"}
    for raw, g in (("Dealer", "dealer"), ("Asset_Mgr", "am"), ("Lev_Money", "lev"), ("Other_Rept", "other")):
        tcols[f"{raw}_Positions_Long_All"] = f"{g}_long"
        tcols[f"{raw}_Positions_Short_All"] = f"{g}_short"
        tcols[f"{raw}_Positions_Spread_All"] = f"{g}_spread"
        tcols[f"Traders_{raw}_Long_All"] = f"{g}_n_long"
        tcols[f"Traders_{raw}_Short_All"] = f"{g}_n_short"
    tcols["NonRept_Positions_Long_All"] = "tnr_long"
    tcols["NonRept_Positions_Short_All"] = "tnr_short"
    T = pd.DataFrame({b: _num(t[a]) for a, b in tcols.items()}, index=t.index)
    # --- legacy
    leg = []
    for p in sorted(RAW_CFTC.glob("deacot*.zip")):
        df = _read_zip(p)
        code_col = next(c for c in df.columns if "Contract Market Code" in c)
        leg.append(df[df[code_col].astype(str).str.strip() == EUROFX_CODE])
    l = pd.concat(leg, ignore_index=True)
    norm = {c: "".join(c.lower().split()) for c in l.columns}

    def col(name: str) -> str:
        key = "".join(name.lower().split())
        return next(c for c, n in norm.items() if n.startswith(key))

    date_col = next(c for c in l.columns if "YYYY-MM-DD" in c)
    lcols = {"Open Interest (All)": "oi", "Noncommercial Positions-Long (All)": "nc_long", "Noncommercial Positions-Short (All)": "nc_short",
             "Noncommercial Positions-Spreading (All)": "nc_spread", "Commercial Positions-Long (All)": "comm_long",
             "Commercial Positions-Short (All)": "comm_short", "Nonreportable Positions-Long (All)": "nr_long",
             "Nonreportable Positions-Short (All)": "nr_short", "Traders-Total (All)": "traders_total",
             "Traders-Noncommercial-Long (All)": "nc_n_long", "Traders-Noncommercial-Short (All)": "nc_n_short",
             "Traders-Commercial-Long (All)": "comm_n_long", "Traders-Commercial-Short (All)": "comm_n_short",
             "Concentration-Net LT =4 TDR-Long (All)": "conc4_net_long", "Concentration-Net LT =4 TDR-Short (All)": "conc4_net_short",
             "Concentration-Gross LT =4 TDR-Long (All)": "conc4_gross_long", "Concentration-Gross LT =4 TDR-Short (All)": "conc4_gross_short"}
    L = pd.DataFrame({b: _num(l[col(a)]).values for a, b in lcols.items()}, index=pd.to_datetime(l[date_col].str.strip()))
    L.index.name = "report_date"
    L = L[~L.index.duplicated(keep="last")].sort_index()
    W = L.join(T, how="left")
    W.to_csv(DEEP)
    return W


def weekly_close(X: pd.DataFrame, dates: pd.DatetimeIndex) -> pd.Series:
    """EUR/USD NY close of the session that closes on each report date (last close on or before it)."""
    c = pd.Series(X["close"].values, index=pd.DatetimeIndex(X["close_time"].dt.tz_convert("UTC").dt.normalize().dt.tz_localize(None)))
    c = c[~c.index.duplicated(keep="last")]
    return c.reindex(c.index.union(dates)).sort_index().ffill().reindex(dates)


def _z(x: pd.Series, w: int) -> pd.Series:
    return (x - x.rolling(w).mean()) / x.rolling(w).std()


def weekly_signals(W: pd.DataFrame, px: pd.Series) -> tuple[pd.DataFrame, pd.DataFrame]:
    """All raw weekly signals in [-1, 1], indexed by report date, plus a frame of the underlying weekly state variables.
    Uses only rows <= the report date (rolling / diff on the weekly rows)."""
    S, V = {}, {}
    oi = W["oi"]
    nc = (W.nc_long - W.nc_short) / oi
    ncL, ncS = W.nc_long / oi, W.nc_short / oi
    z52 = _z(nc, 52)
    V["nc_net"] = nc; V["nc_z52"] = z52
    sg = np.sign
    S["base_nc_z52"] = sg(z52)
    # theme 1: groups (TFF)
    toi = W["tff_oi"]
    grp = {"am": (W.am_long - W.am_short) / toi, "lev": (W.lev_long - W.lev_short) / toi, "dealer": (W.dealer_long - W.dealer_short) / toi,
           "other": (W.other_long - W.other_short) / toi, "tnr": (W.tnr_long - W.tnr_short) / toi}
    for g, x in grp.items():
        V[f"{g}_net"] = x; V[f"{g}_z52"] = _z(x, 52)
    S["am_z52"] = sg(V["am_z52"]); S["lev_z52"] = sg(V["lev_z52"])
    S["am_lev_agree"] = (S["am_z52"] + S["lev_z52"]) / 2
    S["diag_dealer_fade_z52"] = -sg(V["dealer_z52"])
    S["diag_other_z52"] = sg(V["other_z52"]); S["diag_tff_nonrept_z52"] = sg(V["tnr_z52"])
    S["diag_am_minus_lev"] = (S["am_z52"] - S["lev_z52"]) / 2            # follow AM against LEV when they disagree
    S["diag_comm_fade_z52"] = -sg(_z((W.comm_long - W.comm_short) / oi, 52))
    S["diag_nonrept_z52"] = sg(_z((W.nr_long - W.nr_short) / oi, 52))
    # theme 2: flows
    for k in (1, 4, 13):
        S[f"diag_flow_d{k}"] = sg(nc.diff(k))
        S[f"diag_am_flow_d{k}"] = sg(grp["am"].diff(k)); S[f"diag_lev_flow_d{k}"] = sg(grp["lev"].diff(k))
    S["flow_combo"] = (S["diag_flow_d1"] + S["diag_flow_d4"] + S["diag_flow_d13"]) / 3
    dL, dS = ncL.diff(13), ncS.diff(13)
    nan13 = dL.isna() | dS.isna()
    S["flow_build13"] = ((dL > 0).astype(float) - (dS > 0).astype(float)).where(~nan13)
    S["flow_cover13"] = ((dS < 0).astype(float) - (dL < 0).astype(float)).where(~nan13)
    f13n = sg(nc.diff(13)); long_led = dL.abs() > dS.abs()
    building = ((f13n > 0) & long_led) | ((f13n < 0) & ~long_led)     # new longs / new shorts dominate the net flow
    S["diag_posthoc_build13"] = f13n.where(building, 0.0).where(~nan13)
    S["diag_posthoc_cover13"] = f13n.where(~building, 0.0).where(~nan13)
    S["diag_long_z52"] = sg(_z(ncL, 52)); S["diag_short_fade_z52"] = -sg(_z(ncS, 52))
    S["diag_long_flow_d13"] = sg(dL); S["diag_short_flow_d13"] = -sg(dS)
    # theme 3: extremes
    ext = z52.abs() > EXTREME_Z
    S["ext_flat"] = sg(z52).where(~ext, 0.0).where(z52.notna())
    S["ext_fade"] = sg(z52).where(~ext, -sg(z52)).where(z52.notna())
    S["diag_ext_only"] = sg(z52).where(ext, 0.0).where(z52.notna())    # the part of the baseline held at |z| > 2
    # theme 4: open interest
    doi = np.log(oi).diff(13)
    V["d13_log_oi"] = doi
    S["oi_conviction"] = sg(z52).where(doi > 0, 0.0).where(z52.notna() & doi.notna())
    S["diag_oi_falling"] = sg(z52).where(doi <= 0, 0.0).where(z52.notna() & doi.notna())
    S["diag_flow13_oi_rising"] = sg(nc.diff(13)).where(doi > 0, 0.0).where(doi.notna())
    # theme 5: trader counts / concentration
    br = (W.nc_n_long - W.nc_n_short) / (W.nc_n_long + W.nc_n_short)
    V["breadth"] = br; V["breadth_z52"] = _z(br, 52)
    S["breadth_z52"] = sg(V["breadth_z52"])
    conc = W.conc4_net_long - W.conc4_net_short
    V["conc4_net"] = conc
    S["diag_conc4_net_z52"] = sg(_z(conc, 52))
    S["diag_am_breadth_z52"] = sg(_z((W.am_n_long - W.am_n_short) / (W.am_n_long + W.am_n_short), 52))
    S["diag_lev_breadth_z52"] = sg(_z((W.lev_n_long - W.lev_n_short) / (W.lev_n_long + W.lev_n_short), 52))
    # theme 7: positioning x price divergence (price change over the same 13 report weeks)
    dp = np.log(px).diff(13)
    f13 = sg(nc.diff(13)); p13 = sg(dp)
    V["d13_px"] = dp
    ok = f13.notna() & p13.notna()
    S["div_follow_pos"] = f13.where(f13 != p13, 0.0).where(ok)
    S["diag_flow13_confirmed"] = f13.where(f13 == p13, 0.0).where(ok)
    # baseline split by agreement with the 26-week price change (is the COT edge more than a trend proxy?)
    p26 = sg(np.log(px).diff(26))
    S["diag_base_with_trend26"] = sg(z52).where(sg(z52) == p26, 0.0).where(z52.notna() & p26.notna())
    S["diag_base_against_trend26"] = sg(z52).where(sg(z52) != p26, 0.0).where(z52.notna() & p26.notna())
    # composite (mean over the live components; TFF parts are masked to their live years in `daily_signal`)
    # theme 6: z-window robustness
    for w in (26, 104, 156):
        S[f"rob_nc_z{w}"] = sg(_z(nc, w)); S[f"rob_am_z{w}"] = sg(_z(grp["am"], w)); S[f"rob_lev_z{w}"] = sg(_z(grp["lev"], w))
        S[f"rob_breadth_z{w}"] = sg(_z(br, w))
    return pd.DataFrame(S), pd.DataFrame(V)


TFF_BASED = {"am_z52", "lev_z52", "am_lev_agree", "diag_dealer_fade_z52", "diag_other_z52", "diag_tff_nonrept_z52", "diag_am_minus_lev",
             "diag_am_breadth_z52", "diag_lev_breadth_z52"} | {f"diag_{g}_flow_d{k}" for g in ("am", "lev") for k in (1, 4, 13)} | \
            {f"rob_{g}_z{w}" for g in ("am", "lev") for w in (26, 104, 156)}
COMBO_PARTS = ["base_nc_z52", "am_z52", "lev_z52", "diag_flow_d13", "breadth_z52"]


def live_year(name: str) -> int:
    return TFF_LIVE_YEAR if name in TFF_BASED else LEGACY_LIVE_YEAR


def align_daily(sw: pd.DataFrame, X: pd.DataFrame, lag_days: int = PUB_LAG_DAYS, shift_sessions: int = 0) -> pd.DataFrame:
    """Weekly rows -> daily sessions: stamp at report date + lag_days, then the feature store's one-calendar-day lag
    relative to the session's closing date. shift_sessions > 0 delays further (stale), < 0 leads (deliberate leak test)."""
    s = sw.copy()
    s.index = s.index + pd.Timedelta(days=lag_days)
    cdate = pd.DatetimeIndex(X["close_time"].dt.tz_convert("UTC").dt.normalize().dt.tz_localize(None))
    out = pd.DataFrame({c: _align_lagged(s[c], cdate, 1).values for c in s.columns}, index=X.index)
    return out.shift(shift_sessions) if shift_sessions else out


def daily_signal(D: pd.DataFrame, name: str) -> pd.Series:
    """Raw daily signal in [-1, 1] with the live-year mask applied (0 before the variant is live)."""
    yr = D.index.year
    if name == "deep_combo":
        parts = pd.concat([D[p].where(yr >= live_year(p)) for p in COMBO_PARTS], axis=1)
        return parts.mean(axis=1).fillna(0.0)
    return D[name].where(yr >= live_year(name)).fillna(0.0)


def positions(X: pd.DataFrame, sig: pd.Series, verbose: bool = False) -> pd.Series:
    """Yearly expanding walk-forward: the vol target is the training-window median of rv_21d_bp (the live rule)."""
    df = X[["rv_21d_bp"]].assign(sig=sig)

    def fit(train):
        return float(train["rv_21d_bp"].median())

    def predict(target, test):
        vs = (target / test["rv_21d_bp"]).clip(0, VOL_CAP).fillna(0.0)
        return (test["sig"] * vs).clip(-1, 1).fillna(0.0)

    return walk_forward(df, fit, predict, label_end=X["label_end_1d"], verbose=verbose).fillna(0.0)


def evaluate(X: pd.DataFrame, pos: pd.Series, name: str, n_arms: int, costs=(1.2, 0.6), fwd: pd.Series | None = None) -> pd.DataFrame:
    out = []
    for cp in costs:
        pnl = pnl_from_positions(pos, X["fwd_1d"] if fwd is None else fwd, X["close"], cost_pips=cp)
        t = report(pnl, periods_per_year=252, name=ARM, n_arms=n_arms)
        t.insert(1, "variant", name)
        t.insert(2, "cost_pips", cp)
        out.append(t)
    return pd.concat(out, ignore_index=True)


def kind_of(name: str) -> str:
    if name == BASELINE:
        return "baseline"
    if name in CANDIDATES:
        return "candidate"
    return "robustness" if name.startswith("rob_") else "diagnostic"


def load():
    X = pd.read_parquet(FEATURES)
    W = build_deep()
    px = weekly_close(X, W.index)
    SW, VW = weekly_signals(W, px)
    return X, W, SW, VW


def all_names(SW: pd.DataFrame) -> list[str]:
    return [BASELINE] + CANDIDATES + [c for c in SW.columns if c.startswith("diag_")] + [c for c in SW.columns if c.startswith("rob_")]


def select_final(rep: pd.DataFrame) -> str:
    """Declared rule: best 2010-2015 net Sharpe at 1.2 pips among the 12 candidates."""
    sel = rep[(rep.period == "2010-2015") & (rep.cost_pips == 1.2) & (rep.kind == "candidate")]
    return sel.sort_values("sharpe", ascending=False).iloc[0]["variant"]


def run_all(X, SW, lag_days: int = PUB_LAG_DAYS, shift_sessions: int = 0, names=None, fwd=None, costs=(1.2, 0.6)):
    D = align_daily(SW, X, lag_days, shift_sessions)
    names = names or all_names(SW)
    pos, tabs = {}, []
    for n in names:
        pos[n] = positions(X, daily_signal(D, n))
        t = evaluate(X, pos[n], n, n_arms=len(CANDIDATES), costs=costs, fwd=fwd)
        t["kind"] = kind_of(n)
        t["live_from"] = TFF_LIVE_YEAR if (n in TFF_BASED) else LEGACY_LIVE_YEAR
        tabs.append(t)
    return pd.DataFrame(pos), pd.concat(tabs, ignore_index=True)


def run(cost_pips: float = 1.2, save: bool = True, verbose: bool = True):
    """Run baseline + 12 candidates + diagnostics, apply the declared rule, save the deliverables.
    Returns (positions of the final variant, report of all variants)."""
    X, W, SW, VW = load()
    P, rep = run_all(X, SW)
    final = select_final(rep)
    rep["final"] = rep["variant"] == final
    rep["n_candidates"] = len(CANDIDATES)
    rep["n_variants"] = rep["variant"].nunique()
    pos = P[final]
    out = pd.DataFrame({"pos": pos, "fwd_bp": X["fwd_1d"],
                        "net_bp": pnl_from_positions(pos, X["fwd_1d"], X["close"], cost_pips=cost_pips)["net_bp"]})
    out = out[out.index.year >= 2010]
    if save:
        RES.mkdir(parents=True, exist_ok=True)
        out.to_parquet(RES / f"{ARM}_positions.parquet")
        rep.to_csv(RES / f"{ARM}_report.csv", index=False)
        P[P.index.year >= 2010].to_parquet(RES / f"{ARM}_all_positions.parquet")
    if verbose:
        r = rep[rep.cost_pips == cost_pips].pivot(index="variant", columns="period", values="sharpe")
        tt = rep[rep.cost_pips == cost_pips].pivot(index="variant", columns="period", values="t")
        for n in P.columns:
            print(f"{kind_of(n)[:4]} {n:28s} 10-15 {r.loc[n,'2010-2015']:+.2f} | 10-26 {r.loc[n,'2010-2026']:+.2f} (t {tt.loc[n,'2010-2026']:+.2f}) | "
                  f"16-26 {r.loc[n,'2016-2026']:+.2f} (t {tt.loc[n,'2016-2026']:+.2f}) | 23-26 {r.loc[n,'2023-2026']:+.2f}")
        print("FINAL:", final)
    return out["pos"], rep


# ----------------------------------------------------------------------------- analysis beyond the standard table
SHUTDOWNS = (("2013-10-01", "2013-11-12", "2013-11-25"), ("2018-12-18", "2019-02-26", "2019-03-11"),
             ("2025-09-30", "2025-12-30", "2026-01-26"))   # (first late report, last late report, approx. catch-up date)


def _sr(x: pd.Series, a: int, b: int) -> tuple[float, float]:
    r = _agg(x[(x.index.year >= a) & (x.index.year <= b)], 252)
    return r["sharpe"], r["t"]


def _net(X, pos, cost=1.2, fwd=None):
    return pnl_from_positions(pos, X["fwd_1d"] if fwd is None else fwd, X["close"], cost_pips=cost)["net_bp"]


def extremes_table(X, VW) -> pd.DataFrame:
    """P&L of following sign(z52) by |z52| bucket (vol-scaled baseline positions, gross of costs; bucket days only)."""
    D = align_daily(VW[["nc_z52"]], X)
    z = D["nc_z52"]
    pos = positions(X, np.sign(z).fillna(0.0))
    g = pos * X["fwd_1d"]
    rows = []
    bins = [(0, 0.5), (0.5, 1), (1, 1.5), (1.5, 2), (2, 9), (2.5, 9)]
    for lab, a, b in (("2003-2026 (incl. pre-2010, descriptive)", 2003, 2026), ("2010-2026", 2010, 2026), ("2016-2026", 2016, 2026)):
        m0 = (X.index.year >= a) & (X.index.year <= b) & z.notna() & X["fwd_1d"].notna()
        for lo, hi in bins:
            for side, ms in (("both", True), ("long (z>0)", z > 0), ("short (z<0)", z < 0)):
                if side != "both" and lo < 2:
                    continue
                m = m0 & (z.abs() > lo) & (z.abs() <= hi) & ms
                x = g[m]
                n = int(m.sum())
                rows.append({"period": lab, "abs_z": f"{lo}-{hi if hi < 9 else 'inf'}", "side": side, "days": n, "share": n / max(int(m0.sum()), 1),
                             "mean_bp": x.mean() if n else np.nan, "sharpe_on_bucket_days": x.mean() / x.std() * np.sqrt(252) if n > 20 else np.nan,
                             "t": x.mean() / x.std() * np.sqrt(n) if n > 20 else np.nan,
                             "episodes": int((m & ~m.shift(1, fill_value=False)).sum())})
    return pd.DataFrame(rows)


def lag_table(X, SW, names) -> pd.DataFrame:
    rows = []
    for lab, lag, sh in (("lead 10 sessions (next week's report: look-ahead)", PUB_LAG_DAYS, -10), ("lead 5 (report Tuesday itself: not yet published)", PUB_LAG_DAYS, -5),
                         ("lead 2 (Friday close after publication: earliest legitimate)", PUB_LAG_DAYS, -2), ("as run (report + 6d, + 1d store lag)", PUB_LAG_DAYS, 0),
                         ("lag 1 session", PUB_LAG_DAYS, 1), ("lag 5 sessions", PUB_LAG_DAYS, 5), ("lag 10 sessions", PUB_LAG_DAYS, 10), ("lag 20 sessions", PUB_LAG_DAYS, 20)):
        D = align_daily(SW, X, lag, sh)
        for n in names:
            x = _net(X, positions(X, daily_signal(D, n)))
            rows.append({"shift": lab, "variant": n, "sr_2010_2026": _sr(x, 2010, 2026)[0], "sr_2016_2026": _sr(x, 2016, 2026)[0], "sr_2023_2026": _sr(x, 2023, 2026)[0]})
    return pd.DataFrame(rows)


def shutdown_check(X, SW, names) -> pd.DataFrame:
    """Reports dated inside US government shutdowns were published weeks late; delay them to an approximate catch-up date."""
    s = SW.copy()
    stamp = pd.Series(s.index + pd.Timedelta(days=PUB_LAG_DAYS), index=s.index)
    for a, b, c in SHUTDOWNS:
        m = (s.index >= a) & (s.index <= b)
        stamp[m] = np.maximum(stamp[m].values, np.datetime64(c))
    s.index = pd.DatetimeIndex(stamp.values)
    s = s[~s.index.duplicated(keep="last")].sort_index()
    cdate = pd.DatetimeIndex(X["close_time"].dt.tz_convert("UTC").dt.normalize().dt.tz_localize(None))
    D = pd.DataFrame({c: _align_lagged(s[c], cdate, 1).values for c in s.columns}, index=X.index)
    rows = []
    for n in names:
        x = _net(X, positions(X, daily_signal(D, n)))
        rows.append({"variant": n, "sr_2010_2026": _sr(x, 2010, 2026)[0], "sr_2016_2026": _sr(x, 2016, 2026)[0], "sr_2023_2026": _sr(x, 2023, 2026)[0]})
    return pd.DataFrame(rows)


def shuffle_check(X, SW, n_seeds: int = 20) -> pd.DataFrame:
    """Permute fwd_1d over all rows and re-run baseline + candidates + the selection rule."""
    D = align_daily(SW, X)
    P = {n: positions(X, daily_signal(D, n)) for n in [BASELINE] + CANDIDATES}
    rows = []
    ok = X["fwd_1d"].notna().values
    for seed in range(n_seeds):
        rng = np.random.default_rng(seed)
        v = X["fwd_1d"].to_numpy(copy=True)
        v[ok] = rng.permutation(v[ok])
        f = pd.Series(v, index=X.index)
        nets = {n: _net(X, p, fwd=f) for n, p in P.items()}
        sel = max(CANDIDATES, key=lambda n: _sr(nets[n], 2010, 2015)[0])
        rows.append({"seed": seed, "selected": sel, "final_sr_2010_2015": _sr(nets[sel], 2010, 2015)[0], "final_sr_2010_2026": _sr(nets[sel], 2010, 2026)[0],
                     "final_sr_2016_2026": _sr(nets[sel], 2016, 2026)[0], "baseline_sr_2010_2026": _sr(nets[BASELINE], 2010, 2026)[0],
                     "baseline_sr_2016_2026": _sr(nets[BASELINE], 2016, 2026)[0]})
    return pd.DataFrame(rows)


def vs_baseline(X, P: pd.DataFrame, names) -> pd.DataFrame:
    """Each stream against the crude rule on 2016-2026: P&L correlation, paired difference, residual alpha."""
    b = _net(X, P[BASELINE])
    m = (X.index.year >= 2016) & b.notna()
    rows = []
    for n in names:
        x = _net(X, P[n])
        xb, bb = x[m], b[m]
        d = xb - bb
        beta = np.cov(xb, bb)[0, 1] / bb.var()
        res = xb - beta * bb
        ew = 25 * xb / xb.std() + 25 * bb / bb.std()
        rows.append({"variant": n, "kind": kind_of(n), "corr_pnl_2016_2026": xb.corr(bb), "corr_pos_2016_2026": P[n][m].corr(P[BASELINE][m]),
                     "sr_2016_2026": _sr(x, 2016, 2026)[0], "diff_vs_base_t": d.mean() / d.std() * np.sqrt(len(d)) if d.std() > 0 else 0.0,
                     "beta_to_base": beta, "resid_alpha_bp": res.mean(), "resid_alpha_t": res.mean() / res.std() * np.sqrt(len(res)) if res.std() > 0 else 0.0,
                     "ew_with_base_sr_2016_2026": ew.mean() / ew.std() * np.sqrt(252)})
    return pd.DataFrame(rows)


def incremental(X, P: pd.DataFrame, final: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Three-way combination test of the round-3 addendum, plus replacement and placebo (a copy of the crude rule)."""
    from eurusd.arms import meta
    orig = meta.load_arm_daily
    extra = {}

    def patched(name):
        return extra[name] if name in extra else orig(name)

    def stream(n):
        d = pd.DataFrame({"net_bp": _net(X, P[n])})
        d = d[d.index.year >= 2010]
        key = (d.index - pd.Timedelta(hours=22)).floor("D") + pd.Timedelta(hours=22)
        return d["net_bp"].groupby(key).sum().sort_index()

    meta.load_arm_daily = patched
    try:
        rows = []

        def add(label, arms):
            pnl, w = meta.combine(arms, "EW")
            r = meta.report_combo(pnl, label, 3).set_index("period")
            rows.append({"combo": label, **{f"sr_{p}": r.loc[p, "sharpe"] for p in ("2010-2026", "2013-2026", "2016-2026", "2023-2026")},
                         "t_2016-2026": r.loc["2016-2026", "t"]})

        add("two-way: weak_signals + regime_trend", ["weak_signals", "regime_trend"])
        add(f"three-way: + positioning_deep ({final})", ["weak_signals", "regime_trend", ARM])
        add(f"replacement: weak_signals + positioning_deep ({final})", ["weak_signals", ARM])
        extra["_base"] = stream(BASELINE)
        add("placebo three-way: + a copy of the crude rule (base_nc_z52)", ["weak_signals", "regime_trend", "_base"])
        for n in CANDIDATES:
            extra["_c"] = stream(n)
            add(f"[info] three-way with {n}", ["weak_signals", "regime_trend", "_c"])
            add(f"[info] replacement with {n}", ["weak_signals", "_c"])
        ws, rt = orig("weak_signals"), orig("regime_trend")
        cr = []
        for n in [final, BASELINE, "deep_combo", "am_lev_agree", "div_follow_pos"]:
            df = pd.DataFrame({"x": stream(n), "weak_signals": ws, "regime_trend": rt}).fillna(0.0)
            for lab, a in (("2010-2026", 2010), ("2016-2026", 2016)):
                d = df[df.index.year >= a]
                A = np.column_stack([np.ones(len(d)), d["weak_signals"], d["regime_trend"]])
                coef = np.linalg.lstsq(A, d["x"].values, rcond=None)[0]
                res = d["x"].values - A[:, 1:] @ coef[1:]
                cr.append({"stream": n, "period": lab, "corr_weak_signals": d["x"].corr(d["weak_signals"]), "corr_regime_trend": d["x"].corr(d["regime_trend"]),
                           "alpha_bp_vs_both": res.mean(), "alpha_t_vs_both": res.mean() / res.std() * np.sqrt(len(res))})
    finally:
        meta.load_arm_daily = orig
    return pd.DataFrame(rows), pd.DataFrame(cr)


def flow_price_table(W: pd.DataFrame, px: pd.Series) -> pd.DataFrame:
    """Descriptive (weekly, in-sample): do a group's weekly flows follow, accompany or lead the EUR/USD return?
    r(t) = log return over the report week ending at report date t; flow(t) = change of net/OI over the same week."""
    r = np.log(px).diff()
    oi, toi = W["oi"], W["tff_oi"]
    nets = {"non-commercial (legacy)": (W.nc_long - W.nc_short) / oi, "commercial (legacy)": (W.comm_long - W.comm_short) / oi,
            "non-reportable": (W.nr_long - W.nr_short) / oi, "asset managers": (W.am_long - W.am_short) / toi,
            "leveraged funds": (W.lev_long - W.lev_short) / toi, "dealers": (W.dealer_long - W.dealer_short) / toi,
            "other reportables": (W.other_long - W.other_short) / toi}
    rows = []
    for lab, a in (("2006-06..2026", "2006-06-13"), ("2016..2026", "2016-01-01")):
        for g, x in nets.items():
            f = x.diff()
            m = (W.index >= a) & f.notna() & r.notna()
            rows.append({"period": lab, "group": g, "n_weeks": int(m.sum()),
                         "corr_flow_prev_week_ret": f[m].corr(r.shift(1)[m]), "corr_flow_same_week_ret": f[m].corr(r[m]),
                         "corr_flow_next_week_ret": f[m].corr(r.shift(-1)[m]), "corr_flow_week_after_next_ret (tradable)": f[m].corr(r.shift(-2)[m]),
                         "corr_level_z52_next_13w_ret": _z(x, 52)[m].corr((np.log(px).shift(-14) - np.log(px).shift(-1))[m])})
    return pd.DataFrame(rows)


def analysis(verbose: bool = True) -> dict:
    """Everything in the report beyond the standard table. Needs run() to have saved the final positions first."""
    X, W, SW, VW = load()
    rep = pd.read_csv(RES / f"{ARM}_report.csv")
    final = rep.loc[rep.final, "variant"].iloc[0]
    P, _ = run_all(X, SW, costs=(1.2,))
    out = {}
    out["extremes"] = extremes_table(X, VW)
    out["flow_price"] = flow_price_table(W, weekly_close(X, W.index))
    probe = [BASELINE, final, "deep_combo", "am_lev_agree", "diag_flow_d1"]
    out["lags"] = lag_table(X, SW, probe)
    out["shutdown"] = shutdown_check(X, SW, [BASELINE, final, "deep_combo"])
    out["shuffle"] = shuffle_check(X, SW)
    out["vs_baseline"] = vs_baseline(X, P, [n for n in P.columns if not n.startswith("rob_")])
    out["combos"], out["corr"] = incremental(X, P, final)
    D = align_daily(SW, X)
    m = X.index.year >= 2010
    out["label_corr"] = pd.DataFrame([{"variant": n, "corr_signal_fwd_1d": daily_signal(D, n)[m].corr(X["fwd_1d"][m]),
                                       "corr_signal_ret_1d_same_day": daily_signal(D, n)[m].corr(X["fwd_1d"].shift(1)[m]),
                                       "turnover_per_year": P[n][m].diff().abs().sum() / (m.sum() / 252)} for n in [BASELINE] + CANDIDATES])
    for k, v in out.items():
        v.to_csv(RES / f"{ARM}_{k}.csv", index=False)
        if verbose:
            print(f"\n== {k}\n{v.round(3).to_string()}")
    return out


if __name__ == "__main__":
    run()
    analysis()
