"""Builds reports/arm_swing.md from the CSVs written by `python -m eurusd.arms.swing full` (tables and the numbers in
the text are read from the result files; the reading of them is the author's)."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from eurusd.arms import swing as S  # noqa: E402

R = ROOT / "experiments/results/arms"
ERAS = ["2006-2026", "2006-2015", "2010-2026", "2016-2026", "2023-2026"]


def md(df, floatfmt=None):
    if floatfmt is None:          # pre-formatted cells: print them as they are
        return df.astype(object).where(df.notna(), "").to_markdown(index=False, disable_numparse=True)
    return df.to_markdown(index=False, floatfmt=floatfmt)


def pct(x, d=1):
    return "" if pd.isna(x) else f"{100 * x:.{d}f}"


ts = pd.read_csv(R / "swing_trade_stats.csv")
acc = pd.read_csv(R / "swing_accuracy.csv")
rep = pd.read_csv(R / "swing_report.csv")
cal = pd.read_csv(R / "swing_calibration.csv")
pred = pd.read_csv(R / "swing_predictors.csv")
abl = pd.read_csv(R / "swing_ablation.csv")
pre = pd.read_csv(R / "swing_pre1999_trade_stats.csv")
prea = pd.read_csv(R / "swing_pre1999_accuracy.csv")
inc = pd.read_csv(R / "swing_incremental.csv").iloc[0]
leak = pd.read_csv(R / "swing_leakchecks.csv")
live = pd.read_csv(R / "swing_live_benchmark.csv")
hr = pd.read_csv(R / "swing_hitrates.csv")
lc = pd.read_csv(R / "swing_label_corr.csv")
wts = pd.read_csv(R / "swing_weights.csv")
trades = pd.read_csv(R / "swing_trades.csv")
final = rep.loc[rep.final, "variant"].iloc[0]
cand = ts[ts.group == "candidate"]
sens = ts[ts.group == "sensitivity"]
P = S.load_prices()
factor = S.weekly_atr(P).attrs.get("close_only_factor", float("nan"))
_h10 = S._ms("fred_DEXUSEU.csv").loc["1999-01-04":"2002-12-31"]
n_ecb = int((~P.loc[P.src == "h10", "cdate"].isin(_h10.index)).sum())
src = P.groupby("src").agg(sessions=("close", "size"), first=("cdate", "min"), last=("cdate", "max")).reset_index()


def trade_row(d):
    return {"trades": int(d.n_trades), "per yr": round(d.trades_per_year, 1), "long %": pct(d.get("share_long")), "closed in profit %": pct(d.get("win_share")),
            "direction right at horizon %": pct(d.get("dir_acc")), "Wilson 95 %": f"{pct(d.get('dir_acc_lo'))}-{pct(d.get('dir_acc_hi'))}" if d.n_trades else "",
            "avg win pips": round(d.get("avg_win_pips", np.nan), 0), "avg loss pips": round(d.get("avg_loss_pips", np.nan), 0),
            "expectancy pips": round(d.get("expectancy_pips", np.nan), 1), "of which carry": round(d.get("carry_pips", np.nan), 1),
            "expectancy R": round(d.get("expectancy_R", np.nan), 3), "hold sessions": round(d.get("avg_hold_sessions", np.nan), 1),
            "stopped %": pct(d.get("stop_share")), "max DD (R)": round(d.get("max_dd_R", np.nan), 1), "Sharpe monthly P&L": round(d.sharpe_monthly, 2)}


out = []
w = out.append

# ---------------------------------------------------------------- tables
t_src = src.assign(first=src["first"].dt.date, last=src["last"].dt.date)
t_src["what"] = t_src.src.map({"synth_dem": "synthetic euro = 1.95583 / DEM-per-USD; DEM daily = DKK daily (H.10) x monthly DEM/DKK; close only; ROBUSTNESS SAMPLE",
                               "h10": f"Fed H.10 noon-NY USD per EUR (ECB reference rate on the {n_ecb} weekdays without an H.10 quote); close only",
                               "histdata": "feature-store NY-close sessions (HistData H1), true session open/high/low"})
t_src = t_src.sort_values("first")

pt = pred.copy()
ptab = pd.DataFrame({"predictor": pt.predictor, "fam": pt.family, "prior (sign on the raw quantity, reason)": pt.prior, "definition": pt.definition, "first value": pt.first_value})
for tgt in ("h21", "h42"):
    for lab, short in (("1999-2026", "99-26"), ("2006-2026", "06-26"), ("2016-2026", "16-26"), ("1980-1998 (synthetic DEM)", "80-98 DEM")):
        ptab[f"{tgt[1:]}s {short}"] = pt[f"acc_{tgt}_{lab}"].map(lambda v: pct(v))

a0 = acc[acc.era.isin(["2006-2026", "2010-2026", "2016-2026", "2023-2026"])]


def acc_table(clock):
    rows = []
    for (fc, tg), g in a0[a0.clock == clock].groupby(["forecaster", "target"], sort=False):
        for thr in (0.5, 0.55, 0.6):
            r = {"model": fc, "target": tg, "P >=": thr}
            for era in ("2006-2026", "2010-2026", "2016-2026", "2023-2026"):
                x = g[(g.thr == thr) & (g.era == era)]
                if len(x):
                    x = x.iloc[0]
                    r[era] = f"{pct(x.acc)} ({int(x.n_acted)})" if x.n_acted else "- (0)"
                    if era == "2006-2026":
                        r["95 % interval 06-26"] = f"{pct(x.ci_lo)}-{pct(x.ci_hi)}" if x.n_acted >= 5 else ""
                        r["independent bets 06-26"] = int(x.n_independent)
            rows.append(r)
    return pd.DataFrame(rows)


brier = acc[(acc.thr == 0.5) & (acc.era == "2006-2026")][["forecaster", "target", "clock", "brier", "naive_majority"]]
brier_t = brier.pivot_table(index=["forecaster", "target"], columns="clock", values="brier", sort=False).round(4).reset_index()

c0 = cal[(cal.target == "h21") & cal.era.isin(["2006-2026", "2016-2026"]) & (cal.n > 0)]
cal_t = c0[c0.model == "S"][["clock", "era", "bin", "n", "n_independent", "mean_predicted", "realised", "wilson_lo", "wilson_hi"]].copy()
for c in ("mean_predicted", "realised", "wilson_lo", "wilson_hi"):
    cal_t[c] = cal_t[c].map(pct)
cal_t = cal_t.rename(columns={"mean_predicted": "predicted %", "realised": "realised %", "wilson_lo": "lo", "wilson_hi": "hi (Wilson, treats rows as independent)"})

c15 = cand[cand.era == "2006-2015"]
sel_t = pd.DataFrame([{"candidate": r.variant, **{k: v for k, v in trade_row(r).items() if k in ("trades", "per yr", "direction right at horizon %", "Wilson 95 %", "expectancy pips", "Sharpe monthly P&L")},
                       "eligible (>= 8/yr and exp > 0)": "yes" if (r.trades_per_year >= 8 and r.expectancy_pips > 0) else "no",
                       "fallback (>= 4/yr and exp > 0)": "yes" if (r.trades_per_year >= 4 and r.expectancy_pips > 0) else "no"} for _, r in c15.iterrows()])
allc = []
for v, g in cand.groupby("variant", sort=False):
    r = {"candidate": v}
    for era in ERAS:
        x = g[g.era == era].iloc[0]
        r[f"{era}"] = f"{pct(x.get('dir_acc'))} / {x.expectancy_pips:+.0f} / {x.sharpe_monthly:+.2f} ({int(x.n_trades)})" if x.n_trades else "- (0)"
    allc.append(r)
allc = pd.DataFrame(allc)

fin_t = pd.DataFrame([{"era": r.era, **trade_row(r)} for _, r in cand[cand.variant == final].iterrows()])
sens_names = {"p50_always": "P > 0.50 (always act, 12 a year)", "p55": "P >= 0.55 (= the flagged rule)", "p60": "P >= 0.60 (the owner's threshold)", "p65": "P >= 0.65", "p70": "P >= 0.70",
              "stop2": "stop 2 x weekly ATR", "trail3": "trailing stop 3 x ATR", "nostop": "no stop",
              "barrier2_tb": "symmetric 2-ATR barrier (target and stop), 2-month limit, tb forecaster", "h42": "42-session forecaster, exit after 2 months",
              "cost0.6": "0.6 pips per round trip", "swap_markup0.75": "retail swap mark-up 0.75 % p.a. against the holder", "no_carry": "carry ignored (as all earlier arms did)",
              "entry_delay1": "entry one session late"}
srows = []
for nm, lab in sens_names.items():
    for era in ("2006-2026", "2016-2026", "2023-2026"):
        x = sens[(sens.variant == f"{final}|{nm}") & (sens.era == era)].iloc[0]
        srows.append({"sensitivity": lab, "era": era, **{k: v for k, v in trade_row(x).items() if k in ("trades", "per yr", "closed in profit %", "direction right at horizon %", "Wilson 95 %", "avg win pips", "avg loss pips", "expectancy pips", "expectancy R", "hold sessions", "stopped %", "max DD (R)", "Sharpe monthly P&L")}})
sens_t = pd.DataFrame(srows)

f12 = rep[(rep.variant == final) & (rep.cost_pips == 1.2)]
f06 = rep[(rep.variant == final) & (rep.cost_pips == 0.6)].set_index("period")
yr_t = f12[["period", "n", "sharpe", "t", "mean_bp", "sum_bp", "active_frac"]].copy()
yr_t["sharpe_0.6pip"] = yr_t.period.map(f06["sharpe"])
agg = rep[(rep.cost_pips == 1.2) & rep.period.str.contains("-")].pivot_table(index="variant", columns="period", values="sharpe", sort=False)[["2006-2026", "2006-2015", "2010-2026", "2016-2026", "2023-2026"]].round(2).reset_index()
dsr = f12[f12.period == "2010-2026"].deflated_sharpe_p.iloc[0]

live_t = pd.DataFrame([{"benchmark": r.variant, "era": r.era, **{k: v for k, v in trade_row(r).items() if k in ("trades", "per yr", "closed in profit %", "direction right at horizon %", "Wilson 95 %", "expectancy pips", "of which carry", "max DD (R)", "Sharpe monthly P&L")}} for _, r in live.iterrows()])

ab = abl.copy()
ab["ablation"] = ab.ablation.str.replace("(always in the market)", "(acts whenever its training slope b > 0)", regex=False)
ab_rows = []
for nm, g in ab.groupby("ablation", sort=False):
    r = {"run": nm}
    for era in ("2006-2026", "2010-2026", "2016-2026", "2023-2026"):
        x = g[g.era == era].iloc[0]
        r[era] = f"{pct(x.dir_acc)} / {x.expectancy_pips:+.0f} / {x.sharpe_monthly:+.2f} ({int(x.n_trades)})" if x.n_trades else "- (0)"
    ab_rows.append(r)
ab_t = pd.DataFrame(ab_rows)

pre_t = pd.DataFrame([{"candidate": r.variant, "era": r.era, **{k: v for k, v in trade_row(r).items() if k in ("trades", "per yr", "direction right at horizon %", "Wilson 95 %", "expectancy pips", "Sharpe monthly P&L")}}
                      for _, r in pre.iterrows() if r.n_trades > 0 and r.era == "1982-1998"])
prea_t = prea[prea.thr.isin([0.5, 0.55, 0.6])][["forecaster", "clock", "thr", "n_decisions", "n_acted", "acc", "ci_lo", "ci_hi", "naive_majority", "n_independent"]].copy()
for c in ("acc", "ci_lo", "ci_hi", "naive_majority"):
    prea_t[c] = prea_t[c].map(pct)

lk = leak.copy()
lk_rows = []
for nm, g in lk.groupby("check", sort=False):
    for era in ("2006-2026", "2016-2026"):
        x = g[g.era == era]
        if not len(x):
            continue
        x = x.iloc[0]
        lk_rows.append({"check": nm, "era": era, "decisions / trades": round(x.n_trades, 1), "direction right %": pct(x.dir_acc), "expectancy pips": "" if pd.isna(x.expectancy_pips) else round(x.expectancy_pips, 1),
                        "Sharpe monthly": "" if pd.isna(x.sharpe_monthly) else round(x.sharpe_monthly, 2),
                        "sd across seeds (acc / Sharpe)": "" if pd.isna(x.get("acc_sd_across_seeds")) else (f"{x.acc_sd_across_seeds:.3f} / " + ("-" if pd.isna(x.get("sharpe_sd_across_seeds")) else f"{x.sharpe_sd_across_seeds:.2f}"))})
lk_t = pd.DataFrame(lk_rows)
lc_t = lc.sort_values("corr_fwd_h21", key=np.abs, ascending=False).head(10).round(3)

wT = wts[wts.model == "T"].drop(columns=["model", "C"]).set_index("test_year")
bT = wT.pop("b")
top = wT.mean().sort_values(ascending=False).head(10).index.tolist()
w_t = wT.loc[[2006, 2008, 2010, 2013, 2016, 2019, 2022, 2026], top].round(2).reset_index()
w_t["test_year"] = w_t["test_year"].astype(int).astype(str)
b_t = wts.pivot_table(index="test_year", columns="model", values="b")[["S", "T", "L"]].round(2).reset_index()
b_t["test_year"] = b_t["test_year"].astype(int).astype(str)
TM = lambda thr: int(g(acc, forecaster="T", target="h21", clock="M", era="2006-2026", thr=thr).n_acted)  # noqa: E731
LM = lambda thr: int(g(acc, forecaster="L", target="h21", clock="M", era="2006-2026", thr=thr).n_acted)  # noqa: E731
p60 = cand[(cand.variant == "S_M_p60")].set_index("era")
r60 = rep[(rep.variant == "S_M_p60") & (rep.cost_pips == 1.2)].set_index("period")

hr_t = hr.copy()
for c in ("session_net_positive", "session_sign_correct"):
    hr_t[c] = hr_t[c].map(pct)
fin = cand[cand.variant == final].set_index("era")
r4 = pd.DataFrame([{"era": e, "decisions (trades)": int(fin.loc[e].n_trades), "net P&L > 0 %": pct(fin.loc[e].win_share), "correct sign before costs %": pct(fin.loc[e].dir_acc),
                    "active sessions": int(hr.set_index("era").loc[e].n_active_sessions), "sessions net > 0 %": hr_t.set_index("era").loc[e].session_net_positive,
                    "sessions sign correct %": hr_t.set_index("era").loc[e].session_sign_correct} for e in ("2010-2026", "2016-2026", "2023-2026")])


def g(df, **kw):
    x = df
    for k, v in kw.items():
        x = x[x[k] == v]
    return x.iloc[0]


SM = lambda era, thr: g(acc, forecaster="S", target="h21", clock="M", era=era, thr=thr)  # noqa: E731
SW = lambda era, thr: g(acc, forecaster="S", target="h21", clock="W", era=era, thr=thr)  # noqa: E731
sv = lambda nm, era: sens[(sens.variant == f"{final}|{nm}") & (sens.era == era)].iloc[0]  # noqa: E731
lv = lambda v, era: live[(live.variant == v) & (live.era == era)].iloc[0]  # noqa: E731

# ---------------------------------------------------------------- text
w(f"""# Arm O — swing: EUR/USD position trading designed for the multi-week horizon

Code `src/eurusd/arms/swing.py` (`run(cost_pips=1.2)`; `PYTHONPATH=src python -m eurusd.arms.swing full` writes
everything in about seven minutes on one core, `fetch` re-downloads the FRED series this arm added, `leak` re-runs the
leak checks; `experiments/61_swing_report.py` rebuilds this file from the CSVs). Results in `experiments/results/arms/`:
`swing_positions.parquet` (daily stream of the flagged rule: `pos`, `fwd_bp`, `net_bp` after costs and carry, plus
`gross_bp`, `carry_bp`), `swing_trades.csv` (one row per trade), `swing_report.csv` (harness table, all 12 candidates,
`variant` and `final` columns), `swing_trade_stats.csv` (candidates and sensitivities by era), `swing_accuracy.csv`,
`swing_calibration.csv`, `swing_predictors.csv`, `swing_probabilities.parquet` (walk-forward P(up) of the nine
forecasters), `swing_weights.csv`, `swing_ablation.csv`, `swing_live_benchmark.csv`, `swing_pre1999_*.csv`,
`swing_incremental.csv`, `swing_leakchecks.csv`, `swing_label_corr.csv`, `swing_hitrates.csv`,
`swing_trades_all_candidates.csv`. Logs `experiments/results/arms/logs/swing*.log`. This report is generated from those
files.

## Verdict
**The arm fails, cleanly.** The declared selection rule finds no eligible rule: none of the 12 candidates has both
>= 8 (or the fallback >= 4) trades a year and a positive net expectancy in 2006-2015. `{final}` is flagged `final`
only so that a stream exists for the lead's incremental test; it is not a recommendation.

1. **A calibrated 60 % call on the next month's direction practically does not exist.** With probabilities calibrated
   honestly in the training window, the transparent scorecard reaches P >= 0.60 on {int(SM('2006-2026', 0.6).n_acted)} of {int(SM('2006-2026', 0.5).n_decisions)} month-ends in
   2006-2026 ({sv('p60', '2006-2026').trades_per_year:.1f} a year); those calls were right {pct(SM('2006-2026', 0.6).acc)} % of the time (Wilson {pct(SM('2006-2026', 0.6).ci_lo)}-{pct(SM('2006-2026', 0.6).ci_hi)}).
   P >= 0.65 happened {int(SM('2006-2026', 0.65).n_acted)} times, P >= 0.70 never. The t-stat combination and the logistic model, whose probabilities are
   calibrated on inner out-of-sample scores, reach 0.55 on {TM(0.55)} and {LM(0.55)} month-ends and 0.60 on {TM(0.6)} and {LM(0.6)}; their hit rates
   there ({pct(g(acc, forecaster='T', target='h21', clock='M', era='2006-2026', thr=0.55).acc, 0)} % for T at 0.55, {pct(g(acc, forecaster='L', target='h21', clock='M', era='2006-2026', thr=0.55).acc, 0)} % and {pct(g(acc, forecaster='L', target='h21', clock='M', era='2006-2026', thr=0.6).acc, 0)} % for L at 0.55 and 0.60) are all inside the noise.
2. **The probability does not sort the outcomes.** Scorecard, month-ends 2006-2026: stated {' / '.join(pct(v, 0) for v in cal[(cal.model == 'S') & (cal.clock == 'M') & (cal.target == 'h21') & (cal.era == '2006-2026') & (cal.n > 5)].mean_predicted.head(5))} %,
   realised {' / '.join(pct(v, 0) for v in cal[(cal.model == 'S') & (cal.clock == 'M') & (cal.target == 'h21') & (cal.era == '2006-2026') & (cal.n > 5)].realised.head(5))} %. Brier score {SM('2006-2026', 0.5).brier:.3f} against 0.250 for "always 50 %".
3. **Best honest multi-week direction accuracy of the purpose-built system: {pct(SM('2006-2026', 0.5).acc)} %** (scorecard, every month-end,
   {int(SM('2006-2026', 0.5).n_acted)} non-overlapping decisions 2006-2026, Wilson {pct(SM('2006-2026', 0.5).ci_lo)}-{pct(SM('2006-2026', 0.5).ci_hi)}, naive {pct(SM('2006-2026', 0.5).naive_majority)}); {pct(SM('2010-2026', 0.5).acc)} % in 2010-26, {pct(SM('2016-2026', 0.5).acc)} % in
   2016-26, {pct(SM('2023-2026', 0.5).acc)} % in 2023-26. The interval contains 50 %. Traded every month with a 3-ATR stop, after 1.2 pips and
   carry: {sv('p50_always', '2006-2026').expectancy_pips:+.0f} pips a trade, monthly-P&L Sharpe {sv('p50_always', '2006-2026').sharpe_monthly:.2f} (2006-26), {sv('p50_always', '2016-2026').sharpe_monthly:.2f} (2016-26), {sv('p50_always', '2023-2026').sharpe_monthly:.2f} (2023-26).
4. **Designing for the horizon did not beat the existing exposure held for a month.** The sign of the live daily
   combination read at month-ends and run through the same trade simulator (benchmark, not a candidate, and selected on
   this very period by rounds 1-2): {pct(lv('live_exposure_sign_M', '2010-2026').dir_acc)} % right in 2010-26 ({int(lv('live_exposure_sign_M', '2010-2026').n_trades)} trades, Wilson {pct(lv('live_exposure_sign_M', '2010-2026').dir_acc_lo)}-{pct(lv('live_exposure_sign_M', '2010-2026').dir_acc_hi)}), {lv('live_exposure_sign_M', '2010-2026').expectancy_pips:+.0f} pips a trade,
   Sharpe {lv('live_exposure_sign_M', '2010-2026').sharpe_monthly:.2f}; 2016-26 {pct(lv('live_exposure_sign_M', '2016-2026').dir_acc)} % / {lv('live_exposure_sign_M', '2016-2026').sharpe_monthly:.2f}; 2023-26 {pct(lv('live_exposure_sign_M', '2023-2026').dir_acc)} % / {lv('live_exposure_sign_M', '2023-2026').sharpe_monthly:.2f}. The scorecard on the same window: {pct(SM('2010-2026', 0.5).acc)} %.
5. **What carries the little there is**: speculative positioning (alone {pct(g(abl, ablation='only POS (always in the market)', era='2006-2026').dir_acc)} % at month-ends 2006-26) and US-vs-euro-area
   equity momentum, i.e. the two house signals already live, plus 6-month oil since 2016. Rate levels, real rates, PPP,
   the 5-year average, curve slope, carry and (after 1998) trend are at 50 % or wrongly signed. Nothing new was found.
6. Incremental test: three-way {inc['SR3_2016-2026']:.2f} vs two-way {inc['SR2_2016-2026']:.2f} on 2016-26 (noise), {inc['SR3_2023-2026']:.2f} vs {inc['SR2_2023-2026']:.2f} on 2023-26 (worse).
   Standalone harness Sharpe of the flagged stream {g(f12, period='2010-2026').sharpe:.2f} / {g(f12, period='2016-2026').sharpe:.2f} / {g(f12, period='2023-2026').sharpe:.2f}: the round-3 bar is missed (2023-26 negative).

## 1. Data and spans
Price (continuous daily frame, {len(P):,} sessions):

{md(t_src[['src', 'first', 'last', 'sessions', 'what']])}

* Weekly ATR = mean true range of the last {S.ATR_WEEKS} weekly bars. Before 2003 only closes exist, so the close-only weekly
  range is scaled by {factor:.3f} (ratio of true to close-only weekly range in 2003-2005, i.e. before the first test year).
  All test-period trades (2006+) use true session highs and lows for stops.
* Pre-1999 sample: FRED no longer serves the daily DEM series (`DEXGEUS` returns 404) and the repo's H.10 file has no
  DEM column, so the daily path is DKK/USD (H.10 daily) times the monthly-average DEM/DKK cross (FRED `EXGEUS` /
  `EXDNUS`), interpolated. Its monthly averages match `EXGEUS` to 0.1 % (sd of the log error 0.0011); applied to
  1999-2001, where the euro itself is known, the 21-session returns of the same construction are 0.995 correlated with
  the real ones and the daily returns 0.91. Good for a 21-session robustness test, not for anything daily.
* Repo series used with their lags: US 2y / 10y (`fred_DGS2`, `fred_DGS10`), `fred_T10Y3M`, Fed target (`fred_DFEDTAR`,
  `DFEDTARL/U`), ECB MRO, EONIA / euro short-term rate, AAA curve, VIX (`fred_VIXCLS`), DAX and S&P closes, Brent
  (`datahub_brent_daily`, an EIA spot price, treated as a market price): one calendar day. US CPI, HICP: 60 days from
  the month stamp. US 3-month interbank (`fred_IR3TIB01USM156N`): 45 days. CFTC legacy report: report date + 6 days,
  then one day.
* Main-sample walk-forward: training from 1999, test years 2006-2026 (7 training years for the first test year). The
  pre-1999 path is never used to fit anything in the main sample; it only gives the 5-year average and the PPP mean a
  history, so those two exist from 1999 instead of 2004.

New raw data (all `data/macro/`, fetched with curl from `fred.stlouisfed.org/graph/fredgraph.csv`):

| file | content | range | lag used |
|---|---|---|---|
| `fred_DEXDNUS.csv` | DKK per USD, daily H.10 | 1971-01-04 .. 2026-11-06 | price of the day (pre-1999 path only) |
| `fred_EXGEUS.csv`, `fred_EXDNUS.csv` | DEM and DKK per USD, monthly averages | 1971-01 .. 2001-12 / 2026-10 | used as a level bridge, pre-1999 only |
| `fred_IRLTLT01DEM156N.csv` | German 10-year yield, monthly average | 1956-05 .. 2026-09 | 45 days from the month stamp; euro-area 10y before 2004-09 |
| `fred_IR3TIB01DEM156N.csv` | German 3-month interbank, monthly | 1960-01 .. 2026-09 | 45 days; short rate before 1999 and 3m rate before 2004-09 |
| `fred_DEUCPIALLMINMEI.csv` | German CPI | 1955-01 .. 2025-03 | 60 days; spliced to the HICP index before 1996 |

Not obtained: S&P 500 before 2003 and the VIX term structure (VIX3M). Both need Yahoo; Yahoo answered HTTP 429 to a
plain request and the retry with a browser User-Agent was blocked by this session's permission layer, which I did not
work around. Consequence: `eqrel63` starts in
2003-04 (repo `spx_D1`, `gdaxi_D1`) and "VIX term" is replaced by the VIX level against its own 1-year median.

Which predictor exists over which span is the `first value` column of the next table (first weekly decision with a
value). In short: price-based, 10-year, short-rate, slope (10y-3m), carry, seasonality from 1975; valuation from 1980;
oil from 1987; VIX from 1991; positioning from 2000 (z52) / 2002 (z156); equities from 2003; everything that needs a
euro-area 2-year yield from 2004-09. The fitted models may use a predictor only once it has {S.MIN_ROWS_PRED} weekly training rows.

## 2. Predictors, priors (fixed before any result) and single-predictor accuracy
Every predictor is oriented so that a positive value means "long EUR/USD" under the stated prior. The accuracy columns
are the share of weekly decisions on which the sign of the oriented predictor equals the sign of the next 21- / 42-session
return. No fitting is involved, so these are honest for the textbook priors; for the priors marked HOUSE the sign was
observed by rounds 1-2 on 2003-2026 and the 1999-2026 columns are in-sample for the sign. Weekly windows overlap: the
number of independent 21-session bets is about 345 for 1999-2026, 258 for 2006-2026, 133 for 2016-2026 and 236 for
1980-1998, so one standard error is about 2.7 / 3.1 / 4.3 / 3.3 points (half of that again for 42 sessions).

{md(ptab)}

Reading it:
* Above 55 % at 21 sessions in 2006-2026: `cot_z52`, `cot_z156` and `eqrel63` (all HOUSE signs, positioning and
  equity momentum are already in the live exposure), nothing else. `oil_d126` and `rd2_d126` are at 54-55 %, `seas`
  at 53 %.
* **Trend at position-trading speed**: 52-53 % over 2006-2026 and 49-51 % over 2016-2026, against 53-57 % in the
  DEM era. Monthly holding does not rescue it; the round-2 finding stands. 12-month momentum is at 49 %.
* **Rate differential levels and carry**: 47-50 % in 2006-2026. **Real-rate differential levels are wrongly signed**
  (42-44 %): the currency with the higher real yield fell.
* **Valuation**: PPP gap 49 % at 21 sessions and 45 % at 42; 5-year average 52 %. As the prior said, a 3-5 year
  half-life is invisible at one or two months.
* **Curve slope (Ang-Chen)**: 48 %. **Positioning extremes, contrarian**: 46 % at 21 and 39 % at 42 sessions on only
  ~50 independent bets, i.e. fading extreme positioning was wrong; following it was right.
* **Month-of-year effect learned from the past** (`seas_month`): 46 % and 39 %, worse than a coin. The December/May
  rule (`seas`) is the only calendar effect with a positive record and it has no economic story.

## 3. Models, decision clocks, probabilities
Targets on a decision close: sign of the next 21-session return (`h21`), of the next 42-session return (`h42`), and a
symmetric triple barrier at 2 x weekly ATR within 42 sessions (`tb`; no touch = sign of the 42-session return).
Models, fitted on weekly decision rows whose label is known before the test year (`eurusd.wf.walk_forward`, expanding,
test years 2006-2026):
* **S** scorecard: sign votes, mean within family, mean across the 11 families. No fitted number in the score.
* **T** house combination: weights proportional to the positive part of each predictor's training t-stat.
* **L** ridge logistic regression, penalty chosen by inner time-ordered CV.
* Probability P(up) = sigmoid(b x score), no intercept, b >= 0 fitted in the training window: on the training scores
  for S (the score has no fitted part), on inner walk-forward out-of-sample scores for T and L.

Calibration slope b by test year (0 means "the training window gives no out-of-sample evidence that the score predicts",
and the model then says 50 % all year):

{md(b_t, floatfmt='.2f')}

T is silent from 2007 to 2014 and barely speaks afterwards; that is the honest calibration at work, not a bug: its
in-sample t-stats do not survive the inner walk-forward. The t-stat weights themselves (largest ten, selected years)
settle on positioning, equity momentum and the 2-year spread change, the same things the daily arm found (blank =
the predictor does not yet have 156 weekly training rows):

{md(w_t)}

### Model comparison: direction accuracy, % (number of decisions acted on)
Month-end clock, non-overlapping (h21 scored on the return to the next month-end; h42 and tb on every other month-end).
Interval = Wilson 95 %.

{md(acc_table('M'))}

Weekly clock, overlapping horizons. Interval = circular block bootstrap (blocks of 9 weeks for 21 sessions, 17 weeks for
42); "independent bets" = number of acted decisions whose horizon windows do not overlap.

{md(acc_table('W'))}

* At "always act" every model is at 52-56 % on the 21-session target, with intervals that contain 50 %.
* Raising the threshold does not raise accuracy in any stable way. The one eye-catching cell, S weekly at P >= 0.60
  ({pct(SW('2006-2026', 0.6).acc)} % on {int(SW('2006-2026', 0.6).n_acted)} weekly decisions, {pct(SW('2016-2026', 0.6).acc)} % in 2016-26), is {int(SW('2006-2026', 0.6).n_independent)} independent bets, block-bootstrap interval {pct(SW('2006-2026', 0.6).ci_lo)}-{pct(SW('2006-2026', 0.6).ci_hi)},
  and the same threshold was {pct(SW('2006-2015', 0.6).acc)} % in 2006-2015; the two bands just below it (0.55-0.60) realised 44-47 %.
* The 42-session and barrier targets are not reliably easier than the 21-session one (the 61.5 % of T on h42 is 52
  month-ends, interval 48-74, and its weekly twin is at 51 %).
* Brier score 2006-2026 (0.2500 = always 50 %):

{md(brier_t, floatfmt='.4f')}

### Probability calibration (scorecard, 21 sessions)
{md(cal_t)}

A calibrated forecaster would show realised rising with predicted. It does not: the 57.5-60 % band realised 42-44 %
and the 50-52.5 % band 56-57 %. The stated probabilities are not usable for sizing or for a "P >= 60 %" trigger.

## 4. The trade as a position trader would run it
Entry at the decision close when flat and max(P, 1-P) >= threshold; initial stop 3 x weekly ATR, checked on session
highs and lows, gap filled at the open; time exit at the next month-end close (M) or four weekly closes later (W); a
trade that ends on time may be renewed on the same close. Costs: 1.2 pips per round trip, plus overnight carry on every
night held = (EUR overnight rate (EONIA, then the euro short-term rate) - Fed funds target midpoint) x days / 360 x
side. R = net pips / (3 x weekly ATR at entry). The daily stream charges the harness cost (1.2 pips per unit of
turnover, i.e. 2.4 a round trip) plus the same carry, and reconciles with the trade list to the basis point.

### The 12 candidates on the selection window 2006-2015
{md(sel_t)}

**Selection: no candidate is eligible, under the rule or under the fallback.** By the pre-declared last resort the best
lower Wilson bound, `{final}`, is flagged `final`. It lost money on the selection window.

All candidates, all eras: direction right % / expectancy pips / monthly-P&L Sharpe (trades):

{md(allc)}

Harness Sharpe of the 12 daily streams (net, 1.2 pips per unit turnover plus carry, 252 periods):

{md(agg, floatfmt='.2f')}

The only candidate that is positive in each of the five reporting windows is `S_M_p60`, the owner's threshold on the scorecard: {int(p60.loc['2006-2026'].n_trades)} trades in
21 years ({int(round(p60.loc['2006-2026'].n_trades * p60.loc['2006-2026'].share_long))} long), harness Sharpe {r60.loc['2006-2026'].sharpe:.2f} / {r60.loc['2010-2026'].sharpe:.2f} / {r60.loc['2016-2026'].sharpe:.2f} / {r60.loc['2023-2026'].sharpe:.2f} for 2006-26 / 2010-26 / 2016-26 / 2023-26, deflated-Sharpe p
{r60.loc['2010-2026'].deflated_sharpe_p:.2f} with 12 candidates. It traded {p60.loc['2006-2015'].trades_per_year:.1f} times a year on the selection window, so it is not eligible, its direction
accuracy is {pct(p60.loc['2006-2026'].dir_acc)} % (Wilson {pct(p60.loc['2006-2026'].dir_acc_lo)}-{pct(p60.loc['2006-2026'].dir_acc_hi)}), and it is the same short-EUR-with-carry exposure as the rule below.

### The flagged rule `{final}` (scorecard, month-end, P >= 0.55, stop 3 x ATR)
{md(fin_t)}

Per year, harness table (deflated-Sharpe p for 2010-2026 with 12 candidates = {dsr:.2f}):

{md(yr_t, floatfmt='.3f')}

Round-4 hit rates of the flagged rule:

{md(r4)}

What this record is: {pct(fin.loc['2016-2026'].share_long, 0)} % of the 2016-2026 trades are long, i.e. the scorecard at P >= 0.55 is a short-EUR position
that collects the dollar's rate advantage ({fin.loc['2016-2026'].carry_pips:.0f} of the {fin.loc['2016-2026'].expectancy_pips:.0f} pips a trade are carry) and happened to be on the right
side of 2018-2022. It lost every year from 2006 to 2011 and again in 2024-2025. That is one macro regime, not timing skill.

### Sensitivities of the flagged rule (reported, never selectable)
{md(sens_t)}

* **Carry matters at this horizon**: ignoring it changes the 2006-2026 expectancy from {fin.loc['2006-2026'].expectancy_pips:+.0f} to {sv('no_carry', '2006-2026').expectancy_pips:+.0f} pips a trade
  (about {fin.loc['2006-2026'].carry_pips:.0f} pips per month-long trade, in favour of dollar longs for most of the sample); a retail swap mark-up of
  0.75 % p.a. takes about {fin.loc['2006-2026'].expectancy_pips - sv('swap_markup0.75', '2006-2026').expectancy_pips:.0f} pips a trade back. The 1.2-pip spread is irrelevant ({sv('cost0.6', '2006-2026').expectancy_pips - fin.loc['2006-2026'].expectancy_pips:+.1f} pips at 0.6).
* Stops: a 3-ATR stop is hit on {pct(fin.loc['2006-2026'].stop_share, 0)} % of trades and changes nothing; 2 ATR is hit on {pct(sv('stop2', '2006-2026').stop_share, 0)} % and is slightly better
  here, no stop slightly better again in 2016-26: no evidence that the stop adds or costs anything. Trailing: no effect.
* The barrier version and the 42-session version trade about twice a year and look like the base rule; both lose
  2023-26.
* P >= 0.60: {int(sv('p60', '2006-2026').n_trades)} trades in 21 years, {sv('p60', '2006-2026').expectancy_pips:+.0f} pips each, Sharpe {sv('p60', '2006-2026').sharpe_monthly:.2f}; t of the trade mean about 1.9, from {int(sv('p60', '2006-2026').n_trades)} trades of which
  {int(sv('p60', '2016-2026').n_trades)} fall in 2016-26 and all of those are short. I would not read anything into it.

## 5. Benchmark: the live exposure held as a position (not a candidate)
Sign of 0.5 x weak_signals + 0.5 x regime_trend (both walk-forward from 2010) read at the decision close and run through
the same simulator (3-ATR stop, 1.2 pips, carry):

{md(live_t)}

This is the best multi-week record in the repository and it is not mine. Two cautions: it was selected by rounds 1-2
out of ~430 variants on exactly this period, so it is flattered in a way the prior-signed scorecard is not; and it is
at 49-50 % with a negative or flat expectancy in 2023-26, like everything else here.

## 6. Which predictors carry it (leave one family out / one family alone; diagnostic)
Direction right % / expectancy pips / monthly Sharpe (trades). "drop X" = the flagged rule without family X; "only X" =
a one-family scorecard that acts whenever its training-window slope is positive.

{md(ab_t)}

Positioning alone is the strongest family by a distance (59-60 % and +43 to +52 pips a trade in every window, flat in
2023-26) and removing it costs the scorecard most accuracy; oil alone is positive but weaker; trend alone is at
+3 pips a trade. The scorecard is better without the rate-level and carry families. Valuation never acts (its training
slope is never positive). Since the family signs were not all textbook (POS, EQ and SEAS are house signs), the families that work are
exactly the ones this project had already mined.

## 7. Pre-1999 robustness sample (synthetic DEM euro, 1975-1998, close only; test years 1982-1998)
Same pipeline, same candidates, predictors that exist before 1999 only (no positioning, no equities, no 2-year yields).
Carry = German minus US 3-month interbank. Never used for any choice.

Forecast accuracy (h21):

{md(prea_t)}

Trades (candidates with at least one trade):

{md(pre_t)}

* The prior-signed scorecard is at chance here too ({pct(g(prea, forecaster='S', clock='M', thr=0.5).acc)} % at month-ends) and never reaches P >= 0.55.
* The t-stat combination does better in the DEM era ({pct(g(prea, forecaster='T', clock='W', thr=0.5).acc)} % weekly, interval {pct(g(prea, forecaster='T', clock='W', thr=0.5).ci_lo)}-{pct(g(prea, forecaster='T', clock='W', thr=0.5).ci_hi)}), consistent with the
  single-predictor table, where trend and the 6-month change of the 10-year (real) differential are at 55-58 % in that
  era; almost all of it is 1982-1989 (`T_W_p55` Sharpe {g(pre, variant='T_W_p55', era='1982-1989').sharpe_monthly:.2f}, then {g(pre, variant='T_W_p55', era='1990-1998').sharpe_monthly:.2f} in 1990-98).
  It is the well-known trend era of the dollar, and the same model in the euro era is at {pct(g(acc, forecaster='T', target='h21', clock='W', era='2006-2026', thr=0.5).acc)} %.
* Month-ends: T is at {pct(g(prea, forecaster='T', clock='M', thr=0.5).acc)} % against a naive majority of {pct(g(prea, forecaster='T', clock='M', thr=0.5).naive_majority)} %, and its P >= 0.60 calls ({int(g(prea, forecaster='T', clock='M', thr=0.6).n_acted)} month-ends) were right {pct(g(prea, forecaster='T', clock='M', thr=0.6).acc)} % of
  the time: here too a higher stated probability did not mean a higher hit rate.
* So the older sample does not support any of the textbook predictors as a stable multi-week signal either.

## 8. Incremental test (round-3 addendum)
`meta.combine([...], "EW")` + `report_combo`, daily net P&L, 2010 onward (combination starts 2013):

| | 2010-2026 | 2013-2026 | 2016-2026 | 2023-2026 |
|---|---|---|---|---|
| EW(weak_signals, regime_trend) Sharpe (t) | {inc['SR2_2010-2026']:.2f} ({inc['t2_2010-2026']:.2f}) | {inc['SR2_2013-2026']:.2f} ({inc['t2_2013-2026']:.2f}) | {inc['SR2_2016-2026']:.2f} ({inc['t2_2016-2026']:.2f}) | {inc['SR2_2023-2026']:.2f} ({inc['t2_2023-2026']:.2f}) |
| EW(weak_signals, regime_trend, swing) | {inc['SR3_2010-2026']:.2f} ({inc['t3_2010-2026']:.2f}) | {inc['SR3_2013-2026']:.2f} ({inc['t3_2013-2026']:.2f}) | {inc['SR3_2016-2026']:.2f} ({inc['t3_2016-2026']:.2f}) | {inc['SR3_2023-2026']:.2f} ({inc['t3_2023-2026']:.2f}) |

Daily P&L correlation of the swing stream with weak_signals {inc.corr_weak_signals:.2f}, with regime_trend {inc.corr_regime_trend:.2f}, with their
combination {inc.corr_two_way:.2f}. Alpha of the swing stream on the two survivors: {inc['alpha_bp_2010-2026']:+.2f} bp a day (t {inc['alpha_t_2010-2026']:.2f}) 2010-26,
{inc['alpha_bp_2016-2026']:+.2f} (t {inc['alpha_t_2016-2026']:.2f}) 2016-26, {inc['alpha_bp_2023-2026']:+.2f} (t {inc['alpha_t_2023-2026']:.2f}) 2023-26. The combiner admits the stream in {int(inc.years_in_combo)} of the 14 years.
**Round-3 bar: failed.** Standalone 2016-2026 is {g(f12, period='2016-2026').sharpe:.2f} (> 0.3) and the three-way edges the two-way by {inc['SR3_2016-2026'] - inc['SR2_2016-2026']:+.2f} on
2016-26, but 2023-2026 is {g(f12, period='2023-2026').sharpe:.2f}, the alpha t-stats are below 1, and the rule was not selectable in the first place.

## 9. Leak checks
{md(lk_t)}

1. **Shuffled labels** (targets permuted among decision rows, used for fitting and scoring, 20 seeds): {pct(g(leak, check='shuffled_labels_weekly_accuracy_thr0.5 (pooled over seeds)').dir_acc)} % at
   "always act"; the calibrator then issues a P >= 0.55 call on {g(leak, check='shuffled_labels_weekly_accuracy_thr0.55 (pooled over seeds)').n_trades:.0f} weekly decisions per run instead of ~370 and none
   at 0.60. **Permuted price path** (daily bars from 1999 re-ordered at random, the whole pipeline including the trade
   simulation, 20 seeds): {pct(g(leak, check='permuted_price_path_always_in_market (pooled over seeds)').dir_acc)} % and Sharpe {g(leak, check='permuted_price_path_always_in_market (pooled over seeds)').sharpe_monthly:+.2f} (sd {g(leak, check='permuted_price_path_always_in_market (pooled over seeds)').sharpe_sd_across_seeds:.2f}) when always in the market; at P >= 0.55 only ~9 trades a
   run, Sharpe {g(leak, check='permuted_price_path_full_pipeline (accuracy pooled over seeds)').sharpe_monthly:+.2f} (sd {g(leak, check='permuted_price_path_full_pipeline (accuracy pooled over seeds)').sharpe_sd_across_seeds:.2f}). The {pct(g(leak, check='permuted_price_path_full_pipeline (accuracy pooled over seeds)').dir_acc, 0)} % pooled accuracy of those few trades is 1.5 standard errors below 50 across
   seeds and has a mechanical cause: a permutation keeps the total 1999-2026 return, so whatever drift the training
   window had is taken back in the test window. Note that the null Sharpe has a standard deviation of about 0.2 over
   21 years: the flagged rule's 0.02 (2006-26) and 0.28 (2010-26) sit inside it.
2. **Features lagged** by 1 / 4 / 13 extra weeks: {' / '.join(pct(g(leak, check=c, era='2006-2026').dir_acc) for c in ('features_lag_plus1week', 'features_lag_plus4weeks', 'features_lag_plus13weeks'))} % and the number of P >= 0.55 calls falls from {int(g(leak, check='final (reference)', era='2006-2026').n_trades)}
   to {' / '.join(str(int(g(leak, check=c, era='2006-2026').n_trades)) for c in ('features_lag_plus1week', 'features_lag_plus4weeks', 'features_lag_plus13weeks'))}, because the in-sample calibration slope shrinks. With a reference this close to zero "collapse" is
   not a meaningful word; what the test shows is that nothing improves with stale inputs. **Look-ahead control**: the
   full scorecard fed with predictors from 21 sessions ahead rises to {pct(g(leak, check='features_from_21sessions_AHEAD_lookahead_control', era='2006-2026').dir_acc)} % only, because the trend family's leak is
   offset by the valuation family, which votes against a price that has risen. The trend family alone makes the harness's
   sensitivity plain (and in 2016-26 the full scorecard does jump, to {pct(g(leak, check='features_from_21sessions_AHEAD_lookahead_control', era='2016-2026').dir_acc)} % and Sharpe {g(leak, check='features_from_21sessions_AHEAD_lookahead_control', era='2016-2026').sharpe_monthly:.2f}): {pct(g(leak, check='control_trend_family_only_honest', era='2006-2026').dir_acc)} % honest, {pct(g(leak, check='control_trend_family_only_21sessions_AHEAD', era='2006-2026').dir_acc)} % and Sharpe {g(leak, check='control_trend_family_only_21sessions_AHEAD', era='2006-2026').sharpe_monthly:.2f} with features from 21 sessions ahead.
3. **Label in disguise**: largest correlations of an oriented predictor with the forward 21-session return on weekly rows:

{md(lc_t, floatfmt='.3f')}

   Nothing above 0.2; the negative entries are the wrongly-signed real-rate and slope priors. `seas_month` is the only
   predictor built from labels and it uses prior calendar years only. `seas` looks forward on the calendar, not on
   prices.
4. The trade list and the daily stream reconcile (sum of side x log(exit / entry) = sum of the stream's gross P&L, to
   0.02 bp; carry to 0.3 %). A stop trade and a time-exit trade were checked by hand against the session bars.
5. Entry one session late: {sv('entry_delay1', '2006-2026').expectancy_pips:+.0f} pips a trade against {fin.loc['2006-2026'].expectancy_pips:+.0f}; no dependence on the exact entry close.

## 10. Variant count, caveats
* **Candidates: 12** (3 models x 2 clocks x 2 thresholds), the cap. Forecasters behind them: 9 (3 models x 3 targets), of
  which the candidates use 3. Reported but not selectable: 14 sensitivity runs of the flagged rule, 2 live-exposure
  benchmarks, 22 ablation runs, 12 candidate replays on the pre-1999 sample, 33 single-predictor rows, and 47 leak-check
  runs (5 feature shifts, 2 trend-only controls, 20 label shuffles, 20 permuted paths). The candidate set, the models
  and the selection rule were not touched after the first result. Added after results were seen, all outside the
  candidate set: the live-exposure benchmark, the trend-only look-ahead control, the always-in-the-market version of
  the permuted-path null and the pooling of null accuracies over seeds; two reporting bugs were fixed (a read-only
  array in the label shuffle, time-zone stamps in the trade file).
* Departures from the brief, all forced: (a) daily DEM is not in the H.10 file and not on FRED any more, hence the
  DKK bridge; (b) no Yahoo, hence no S&P before 2003 and no VIX term structure; (c) the 42-session and barrier trades
  cannot reach 8 trades a year with one position at a time, so they were run as sensitivities, not candidates.
* The early test years lean on thin training data (1999-2005; 2-year yields and equities enter the fitted models in
  2007-2008). The scorecard's calibration slope for 2006 came from 7 years and produced confident, wrong short calls
  through 2006 (probabilities up to 0.68). That is what a short history does and it is part of the honest record.
* The monthly sample is small by nature: 246 non-overlapping decisions in 21 years. A true 55 % accuracy has a standard
  error of 3.2 points on that sample, so 54 % cannot be told from 50 % or from 58 %. More history was the point of the
  pre-1999 sample, and there the prior-signed scorecard is at 49 %.
* Suspicious-looking and explained: T and L make no calls in 2007-2014 (b = 0, see section 3); "only VAL" never trades
  (same reason); {pct(1 - fin.loc['2006-2026'].share_long, 0)} % of the flagged rule's trades are short because the rate-level, real-rate and carry families have voted
  dollar for most of 2006-2026.

## What this means for the product
* Do not attach "P >= 60 %" to a monthly EUR/USD direction call from this information set. The honest number is about
  54-59 % when always acting, with a 95 % interval of roughly +-6-7 points, and about 50 % since 2023.
* The horizon effect in the scoreboard (52 / 55 / 58 %) is the same slow positioning-and-equity signal read over a
  longer window, not additional predictability that a purpose-built monthly model can harvest.
* If the position-trading product is run anyway, the least bad expression in this repository is the existing live
  exposure read at month-ends (section 5), with the carry accounted for (about 13 pips a month for or against the
  position at the 2006-2026 average rate gap; it has been ignored so far), and with the planning Sharpe the research
  log already gives for it (0.25-0.45), not the 0.6 of its in-sample-selected record.
""")

(ROOT / "reports" / "arm_swing.md").write_text("\n".join(out))
print("written", len("\n".join(out).splitlines()), "lines")
