"""Fundamental / positioning / intermarket hypotheses on daily data (F01-F12, C10, H24-H27, H31-H32).
Positions are formed at the NY close of day t using data stamped <= t-1 (one extra day of lag for
publication delay) and held over day t+1. Output: reports/hypotheses_fundamental.md
"""
import sys
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import numpy as np, pandas as pd
from eurusd import features as F
from eurusd.evaluate import SPLITS

D = "/home/user/tapsnap/eurusd/data/"
h1 = pd.read_parquet(D + "processed/EURUSD_H1.parquet").loc["2003":]
d = F.daily_ohlc(h1, 22)
d = d[(d["n"] >= 10) & (d.index.dayofweek != 5)]
d.index = d.index.tz_convert(None).normalize()  # calendar date of the day start (NY-close day labelled by start)
d.index = d.index + pd.Timedelta(days=1)        # label by the closing date
px = d["close"]
r_next = (np.log(px).shift(-1) - np.log(px)) * 1e4   # return of the NEXT day
COST_BP = 1.2 * 1e-4 / 1.15 * 1e4

def csv(name, col="value"):
    s = pd.read_csv(D + "macro/" + name, parse_dates=["date" if "date" in open(D + "macro/" + name).readline() else "report_date"])
    s = s.set_index(s.columns[0])
    return s[col] if col in s.columns else s

def tstat(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan

rows = []
def record(hyp, name, pos, note=""):
    """pos: daily position in [-1,1] indexed by date (formed at close of that date), applied to r_next.
    Costs charged on position changes (turnover)."""
    pos = pos.reindex(px.index).ffill(limit=5)
    pnl = pos * r_next
    turn = pos.diff().abs().fillna(0)
    net = pnl - turn * COST_BP
    for period, (a, b) in SPLITS.items():
        x = pnl.loc[a:b].dropna(); nx = net.loc[a:b].dropna()
        act = (pos.loc[a:b].abs() > 0).mean()
        rows.append(dict(hyp=hyp, test=name, period=period, n=len(x), mean_bp_per_day=x.mean(), t=tstat(x),
                         net_mean_bp=nx.mean(), t_net=tstat(nx), ann_sharpe_net=(nx.mean() / nx.std() * np.sqrt(252)) if nx.std() > 0 else np.nan,
                         pct_days_active=act, note=note))

us2 = csv("fred_DGS2.csv"); us10 = csv("fred_DGS10.csv")
ea = pd.read_csv(D + "macro/ea_aaa_yield_curve.csv", parse_dates=["date"]).set_index("date")
ea2, ea10 = ea["aaa_spot_2y"], ea["aaa_spot_10y"]
idx = px.index
spread2 = (ea2.reindex(idx, method="ffill") - us2.reindex(idx, method="ffill")).shift(1)   # lag 1 day for publication
spread10 = (ea10.reindex(idx, method="ffill") - us10.reindex(idx, method="ffill")).shift(1)
lp = np.log(px)

# F01 / H26: rolling OLS fair value on 2y spread, residual z-score mean reversion
def rolling_resid_z(y, x, win=250):
    out = pd.Series(np.nan, index=y.index)
    yv, xv = y.values, x.values
    for t in range(win, len(y)):
        ys, xs = yv[t - win:t], xv[t - win:t]
        ok = ~np.isnan(ys) & ~np.isnan(xs)
        if ok.sum() < win * 0.8 or np.isnan(xv[t]) or np.isnan(yv[t]): continue
        b, a = np.polyfit(xs[ok], ys[ok], 1)
        res = ys[ok] - (a + b * xs[ok])
        out.iloc[t] = (yv[t] - (a + b * xv[t])) / res.std()
    return out
z = rolling_resid_z(lp, spread2)
record("F01", "2y-spread fair value: position = -clip(z,-2,2)/2 (mean reversion), 250d OLS", (-z.clip(-2, 2) / 2))
record("F01", "2y-spread fair value: enter when |z|>1.5 against residual, hold while |z|>0.5", (-np.sign(z)).where(z.abs() > 1.5).where(z.abs() > 0.5).ffill().where(z.abs() > 0.5, 0.0).fillna(0.0))
record("F01", "2y-spread fair value MOMENTUM: position = +sign(z) (test opposite sign)", np.sign(z))
# C10 / F06 / H26: spread momentum (change over k days)
for k in (5, 20, 60):
    record("C10", f"2y spread change over {k}d: long EUR/USD if EA-US 2y spread rose", np.sign(spread2 - spread2.shift(k)))
    record("F06", f"10y spread change over {k}d: long EUR/USD if EA-US 10y spread rose", np.sign(spread10 - spread10.shift(k)))
record("H26", "daily 2y spread change (t-1): long if spread rose yesterday", np.sign(spread2.diff()))
# F09 / H24 carry: long the higher-yielding side
record("F09", "carry: long EUR/USD if EA 2y > US 2y else short", np.sign(spread2))
record("F09", "carry on 3m: EA 3m AAA vs US 13w (FRED DTB3 absent -> use 2y as proxy; duplicate)", np.sign(spread2), note="same as above")
# F03/F04: SPX risk regime and DXY
spx = csv("fred_SP500.csv").reindex(idx, method="ffill")
vix = csv("fred_VIXCLS.csv").reindex(idx, method="ffill")
spx_r = np.log(spx).diff().shift(1)
corr60 = lp.diff().rolling(60).corr(spx_r)
record("F04", "risk regime: position = sign(60d corr(EURUSD,SPX)) x sign(SPX return t-1)", np.sign(corr60) * np.sign(spx_r))
record("F04", "SPX momentum 20d (t-1) -> long EUR/USD", np.sign(spx_r.rolling(20).sum()))
record("V04", "VIX regime: long EUR/USD when VIX(t-1) < 20, short when > 30", pd.Series(np.where(vix.shift(1) < 20, 1.0, np.where(vix.shift(1) > 30, -1.0, 0.0)), index=idx))
# F10 / H31 / H32 COT positioning
tff = pd.read_csv(D + "macro/cot_eurofx_tff.csv", parse_dates=["report_date"]).set_index("report_date")
leg = pd.read_csv(D + "macro/cot_eurofx_legacy.csv", parse_dates=["report_date"]).set_index("report_date")
print("legacy cols:", list(leg.columns)[:12])
net_lev = (tff["lev_funds_long"] - tff["lev_funds_short"]) / tff["open_interest"]
nc_cols = [c for c in leg.columns if "noncomm" in c.lower() or "non_comm" in c.lower()]
net_nc = ((leg[nc_cols[0]] - leg[nc_cols[1]]) / leg["open_interest"]) if len(nc_cols) >= 2 else None
def cot_signal(net, win=52):
    zz = (net - net.rolling(win).mean()) / net.rolling(win).std()
    # report released Friday for Tuesday positions: available from the following Monday -> shift index by 6 days
    zz.index = zz.index + pd.Timedelta(days=6)
    return zz.reindex(idx, method="ffill")
for name, net in (("leveraged funds (TFF, 2010+)", net_lev), ("non-commercial (legacy, 1999+)", net_nc)):
    if net is None: continue
    zz = cot_signal(net)
    record("F10", f"COT {name}: contrarian when |z52|>1.5", (-np.sign(zz)).where(zz.abs() > 1.5, 0.0))
    record("H32", f"COT {name}: momentum, sign of 4-week change in net", np.sign(cot_signal(net.diff(4), 1)) if False else np.sign((net.diff(4)).pipe(lambda s: s.set_axis(s.index + pd.Timedelta(days=6))).reindex(idx, method="ffill")))
    record("H31", f"COT {name}: follow the crowd, sign of z52", np.sign(zz))
# F07/H29 PPP anchor (monthly, HICP vs CPI) - long-run only; test 5-year z of real exchange rate
cpi = csv("fred_CPIAUCSL.csv"); hicp = pd.read_csv(D + "macro/ea_hicp.csv")
print("hicp cols:", list(hicp.columns))

out = pd.DataFrame(rows)
out.to_csv("/home/user/tapsnap/eurusd/experiments/results/hypotheses_fundamental.csv", index=False)
piv = out.pivot_table(index=["hyp", "test"], columns="period", values=["n", "mean_bp_per_day", "t", "t_net", "ann_sharpe_net"], sort=False).reindex(columns=["train", "validate", "holdout"], level=1)
open("/home/user/tapsnap/eurusd/reports/hypotheses_fundamental.md", "w").write("# Fundamental / positioning hypotheses (daily positions, bp per day; cost 1.2 pips per unit turnover)\n\n" + piv.round(2).to_markdown())
pd.set_option("display.width", 250); pd.set_option("display.max_rows", 200)
print(piv.round(2).to_string())
