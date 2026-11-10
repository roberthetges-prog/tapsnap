"""Battery of EUR/USD behaviour statistics on our own data, split by period.
Output: reports/behaviour_stats.md
Returns are log returns in basis points (1 bp = 0.01 % ~ 1.1 pips at 1.10).
"""
import sys
sys.path.insert(0, "/home/user/tapsnap/eurusd/src")
import numpy as np, pandas as pd
from eurusd import features as F
from eurusd.evaluate import SPLITS

h1 = pd.read_parquet("/home/user/tapsnap/eurusd/data/processed/EURUSD_H1.parquet")
m15 = pd.read_parquet("/home/user/tapsnap/eurusd/data/processed/EURUSD_M15.parquet")
out = []
P = lambda s: out.append(s)

def tstat(x):
    x = pd.Series(x).dropna()
    return x.mean() / x.std(ddof=1) * np.sqrt(len(x)) if len(x) > 2 and x.std() > 0 else np.nan

def per_split(fn, name):
    rows = {}
    for k, (a, b) in SPLITS.items():
        rows[k] = fn(h1.loc[a:b])
    df = pd.concat(rows, axis=1)
    P(f"\n### {name}\n\n" + df.round(2).to_markdown() + "\n")

r_h = np.log(h1.close).diff() * 1e4
r_h.name = "r"

# 1. hour of day
def hod(s):
    r = np.log(s.close).diff() * 1e4
    g = r.groupby(s.index.hour)
    return pd.DataFrame({"mean_bp": g.mean(), "t": g.apply(tstat), "range_pips": ((s.high - s.low) / 1e-4).groupby(s.index.hour).mean()})
per_split(hod, "Hour of day (UTC): mean hourly log return (bp), t-stat, mean range (pips)")

# 2. daily bars with NY-close day boundary (22:00 UTC)
d = F.daily_ohlc(h1, 22)
d = d[d["n"] >= 10]
rd = np.log(d.close).diff() * 1e4
rd.name = "r"

def dow(s):
    g = s.groupby(s.index.dayofweek)
    return pd.DataFrame({"mean_bp": g.mean(), "t": g.apply(tstat), "n": g.size()}).rename(index={0: "Mon(day ending Mon 22:00)", 1: "Tue", 2: "Wed", 3: "Thu", 4: "Fri", 6: "Sun(part)"})
rows = {k: dow(rd.loc[a:b]) for k, (a, b) in SPLITS.items()}
P("\n### Day of week (NY-close days)\n\n" + pd.concat(rows, axis=1).round(2).to_markdown() + "\n")

def month(s):
    g = s.groupby(s.index.month)
    return pd.DataFrame({"mean_bp": g.mean(), "t": g.apply(tstat), "n": g.size()})
rows = {k: month(rd.loc[a:b]) for k, (a, b) in SPLITS.items()}
P("\n### Month of year (daily mean bp)\n\n" + pd.concat(rows, axis=1).round(2).to_markdown() + "\n")

# turn of month: trading-day index relative to month end
tdm = rd.to_frame()
tdm["ym"] = tdm.index.to_period("M")
tdm["pos_from_start"] = tdm.groupby("ym").cumcount() + 1
tdm["pos_from_end"] = tdm.groupby("ym")["r"].transform("size") - tdm["pos_from_start"]  # 0 = last day
def tom(s):
    lab = np.where(s["pos_from_end"] <= 2, "last3", np.where(s["pos_from_start"] <= 3, "first3", "mid"))
    g = s["r"].groupby(lab)
    return pd.DataFrame({"mean_bp": g.mean(), "t": g.apply(tstat), "n": g.size()})
rows = {k: tom(tdm.loc[a:b]) for k, (a, b) in SPLITS.items()}
P("\n### Turn of month (last 3 / first 3 trading days)\n\n" + pd.concat(rows, axis=1).round(2).to_markdown() + "\n")

# 3. London 4pm fix (16:00 London = 16:00 UTC winter / 15:00 UTC summer). Use M15 and London local time.
m = m15.copy()
lon = m.index.tz_convert("Europe/London")
m["lt"] = lon.hour * 60 + lon.minute
rm = np.log(m.close).diff() * 1e4
def fixwin(s_idx):
    sub = m.loc[s_idx]
    rr = rm.loc[s_idx]
    bins = {"15:00-15:45": (15 * 60, 15 * 60 + 45), "15:45-16:00 (into fix)": (15 * 60 + 45, 16 * 60), "16:00-16:15 (after fix)": (16 * 60, 16 * 60 + 15), "16:15-17:00": (16 * 60 + 15, 17 * 60)}
    res = {}
    for k, (a, b) in bins.items():
        # bar labelled t covers (t, t+15]; use the close-to-close return of bars whose END time is in (a, b]
        endm = sub["lt"] + 15
        mask = (endm > a) & (endm <= b)
        x = rr[mask].groupby(rr[mask].index.floor("D")).sum()
        res[k] = {"mean_bp": x.mean(), "t": tstat(x), "n": len(x)}
    return pd.DataFrame(res).T
rows = {k: fixwin(slice(a, b)) for k, (a, b) in SPLITS.items()}
P("\n### London 4pm WM/R fix windows (London local time), daily sum of 15-min returns\n\n" + pd.concat(rows, axis=1).round(2).to_markdown() + "\n")
# month-end fix: last business day of month
me = m[(m["lt"] >= 15 * 60 + 45) & (m["lt"] < 16 * 60)]
x = rm.loc[me.index].groupby(me.index.floor("D")).sum()
last_bd = x.index.to_period("M").to_timestamp(how="end").normalize()
is_me = pd.Series(x.index.tz_localize(None).normalize(), index=x.index).groupby(x.index.to_period("M")).transform("max").values == x.index.tz_localize(None).normalize().values
P(f"\n### Month-end day into-fix return (15:45-16:00 London): mean {x[is_me].mean():.2f} bp, t={tstat(x[is_me]):.2f}, n={is_me.sum()}; other days mean {x[~is_me].mean():.2f} bp\n")

# 4. Range / continuation facts (NY-close days)
d["rng"] = (d.high - d.low) / 1e-4
d["ret"] = (d.close - d.open) / 1e-4
d["prev_high_broken"] = d.high > d.high.shift(1)
d["prev_low_broken"] = d.low < d.low.shift(1)
d["both"] = d.prev_high_broken & d.prev_low_broken
d["ret_next"] = d["ret"].shift(-1)
def facts(s):
    big = s["ret"].abs() > s["rng"].rolling(20).mean()
    return pd.Series({
        "avg_daily_range_pips": s.rng.mean(),
        "median_daily_range_pips": s.rng.median(),
        "P(prev high broken)": s.prev_high_broken.mean(),
        "P(prev low broken)": s.prev_low_broken.mean(),
        "P(both broken)": s.both.mean(),
        "P(neither broken, inside day)": (~s.prev_high_broken & ~s.prev_low_broken).mean(),
        "P(close>open)": (s.ret > 0).mean(),
        "corr(ret, next ret)": s.ret.corr(s.ret_next),
        "next-day mean after big up day (pips)": s.ret_next[big & (s.ret > 0)].mean(),
        "next-day mean after big down day (pips)": s.ret_next[big & (s.ret < 0)].mean(),
        "n_days": len(s),
    })
rows = {k: facts(d.loc[a:b]) for k, (a, b) in SPLITS.items()}
P("\n### Daily range and continuation facts\n\n" + pd.concat(rows, axis=1).round(3).to_markdown() + "\n")

# 5. per-year ADR
adr = d.groupby(d.index.year)["rng"].mean().round(1)
P("\n### Average daily range (pips) by year\n\n" + adr.to_frame("ADR_pips").T.to_markdown() + "\n")

# 6. Session returns: Asia (22-07), London (07-13), overlap (13-16), NY pm (16-21) ; and cross-session correlations
def sess(s):
    r = np.log(s.close).diff() * 1e4
    h = s.index.hour
    lab = np.select([(h >= 22) | (h < 7), (h >= 7) & (h < 13), (h >= 13) & (h < 16), (h >= 16) & (h < 21)], ["asia", "london", "overlap", "ny_pm"], "other")
    day = (s.index - pd.Timedelta(hours=22)).floor("D")
    piv = r.groupby([day, lab]).sum().unstack()
    piv = piv.drop(columns=[c for c in piv.columns if c == "other"], errors="ignore").dropna()
    stats = pd.DataFrame({"mean_bp": piv.mean(), "t": piv.apply(tstat), "sd": piv.std()})
    stats.loc["corr(asia,london)", "mean_bp"] = piv["asia"].corr(piv["london"])
    stats.loc["corr(london,overlap)", "mean_bp"] = piv["london"].corr(piv["overlap"])
    stats.loc["corr(london,ny_pm)", "mean_bp"] = piv["london"].corr(piv["ny_pm"])
    stats.loc["corr(overlap,ny_pm)", "mean_bp"] = piv["overlap"].corr(piv["ny_pm"])
    stats.loc["corr(asia+london, overlap+ny)", "mean_bp"] = (piv["asia"] + piv["london"]).corr(piv["overlap"] + piv["ny_pm"])
    return stats
per_split(sess, "Session returns (UTC windows) and cross-session correlations")

# 7. Hourly return autocorrelation structure
def acf(s):
    r = np.log(s.close).diff().dropna()
    return pd.Series({f"lag{k}": r.autocorr(k) for k in (1, 2, 3, 6, 12, 24)})
per_split(acf, "Hourly log-return autocorrelation")

open("/home/user/tapsnap/eurusd/reports/behaviour_stats.md", "w").write("# EUR/USD behaviour statistics (own data, HistData M1 -> H1/M15, bid)\n\nPeriods: " + ", ".join(f"{k}={a}..{b}" for k, (a, b) in SPLITS.items()) + "\n" + "\n".join(out))
print("\n".join(out)[:6000])
